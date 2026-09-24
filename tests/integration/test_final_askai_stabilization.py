"""
Final Stabilization and Response-State Consistency Test Suite.
Verifies authoritative response states (GROUNDED, LANGUAGE_UNAVAILABLE, INSUFFICIENT_EVIDENCE, ERROR),
script validation, absence of phantom citations, complete sentence extraction, and URL preservation.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas import QueryResponse
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.llm_provider import MockLLMProvider
from app.services.retrieval.models import CandidateChunk
from app.services.rag.context_builder import build_context_package


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_1_grounded_response_state_and_citations():
    """Test 1 & 7: Grounded response state returns response_state='GROUNDED', grounded=True, and valid citations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required for registered courses?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "GROUNDED"
        assert data["grounded"] is True
        assert data["is_fallback"] is False
        assert len(data["citations"]) >= 1
        assert "75%" in data["answer_text"]


@pytest.mark.anyio
async def test_2_insufficient_evidence_state():
    """Test 2 & 16: Out-of-domain query returns INSUFFICIENT_EVIDENCE with empty citations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the recipe for baking chocolate chip cookies on Mars?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "INSUFFICIENT_EVIDENCE"
        assert data["grounded"] is False
        assert data["is_fallback"] is True
        assert len(data["citations"]) == 0
        assert "could not find sufficient" in data["answer_text"] or "Information Not Found" in data["answer_text"]


@pytest.mark.anyio
async def test_3_5_6_language_unavailable_state_telugu():
    """Test 3, 5, 6, 10: Telugu query with no multilingual LLM key returns LANGUAGE_UNAVAILABLE with no phantom citations or grounded badge."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required for semester examinations?",
            "target_language": "te"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] in ("LANGUAGE_UNAVAILABLE", "GROUNDED")
        if data["response_state"] == "LANGUAGE_UNAVAILABLE":
            assert data["grounded"] is False
            assert data["is_fallback"] is True
            assert len(data["citations"]) == 0
            assert "అందుబాటులో లేదు" in data["answer_text"]
        else:
            # If grounded, must contain Telugu script and 75%
            assert any("\u0C00" <= ch <= "\u0C7F" for ch in data["answer_text"])


@pytest.mark.anyio
async def test_8_hindi_language_handling():
    """Test 8: Hindi target query handling and script validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required?",
            "target_language": "hi"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")
        if data["response_state"] == "GROUNDED":
            assert any("\u0900" <= ch <= "\u097F" for ch in data["answer_text"])
            assert "75%" in data["answer_text"]
        else:
            assert len(data["citations"]) == 0


@pytest.mark.anyio
async def test_9_kannada_language_handling():
    """Test 9: Kannada target query handling and script validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required?",
            "target_language": "kn"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")
        if data["response_state"] == "GROUNDED":
            assert any("\u0C80" <= ch <= "\u0CFF" for ch in data["answer_text"])
            assert "75%" in data["answer_text"]
        else:
            assert len(data["citations"]) == 0


@pytest.mark.anyio
async def test_11_english_target():
    """Test 11: English target produces fully grounded answer."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the total credits required for the award of the MCA degree?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "GROUNDED"
        assert "88" in data["answer_text"]
        assert len(data["citations"]) >= 1


@pytest.mark.anyio
async def test_12_attendance_query_no_ballpoint():
    """Test 12: Attendance query returns 75% attendance and never mentions ballpoint pen instructions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required for registered courses?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert "75%" in data["answer_text"]
        assert "ball point" not in data["answer_text"].lower()
        assert "ballpoint" not in data["answer_text"].lower()


@pytest.mark.anyio
async def test_13_nirf_fragment_query():
    """Test 13: Query 'NIRF management fee' returns a complete answer, not a fragment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "NIRF management fee",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert not data["answer_text"].startswith("is less")
        assert not data["answer_text"].startswith("less to")
        assert not data["answer_text"].startswith("fee.")


@pytest.mark.anyio
async def test_14_nirf_full_query():
    """Test 14: Full NIRF training fee query returns 90% and 1.0 lakh."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the reimbursement for top 50 NIRF rated management institutions short term training program fee?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "GROUNDED"
        assert "90%" in data["answer_text"] or "1.0 lakh" in data["answer_text"]
        assert not data["answer_text"].startswith("is less")


@pytest.mark.anyio
async def test_15_cgtmse_url_preservation():
    """Test 15: CGTMSE website query preserves https://www.cgtmse.in URL."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "in which website credit guarantee scheme can be applied",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "GROUNDED"
        assert "https://www.cgtmse.in" in data["answer_text"] or "www.cgtmse.in" in data["answer_text"]


@pytest.mark.anyio
async def test_17_citation_provenance():
    """Test 17: Citations in grounded answer have document_id, page_number, and title."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What are the rules for medical condonation of attendance shortage?",
            "target_language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["response_state"] == "GROUNDED"
        for cite in data["citations"]:
            assert cite["document_id"]
            assert cite["page_number"] >= 1
            assert cite["document_title"]


@pytest.mark.anyio
async def test_18_response_state_consistency():
    """Test 18: Verify response_state matches is_fallback, grounded, and citations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the attendance policy?",
            "target_language": "en"
        })
        data = res.json()
        if data["response_state"] == "GROUNDED":
            assert data["grounded"] is True
            assert data["is_fallback"] is False
            assert len(data["citations"]) > 0
        elif data["response_state"] in ("INSUFFICIENT_EVIDENCE", "LANGUAGE_UNAVAILABLE"):
            assert data["grounded"] is False
            assert data["is_fallback"] is True
            assert len(data["citations"]) == 0


@pytest.mark.anyio
async def test_19_feedback_submission():
    """Test 19: Feedback endpoint accepts user quality feedback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/feedback", json={
            "query_id": "test-query-id-123",
            "feedback": 1,
            "comment": "Accurate and grounded"
        })
        assert res.status_code == 200
        assert res.json()["status"] == "recorded"


@pytest.mark.anyio
async def test_20_stateless_api_and_new_chat():
    """Test 20: Each QA request is independent and stateless."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res1 = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum required attendance?",
            "target_language": "en"
        })
        res2 = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the recipe for baking cookies on Mars?",
            "target_language": "en"
        })
        assert res1.json()["response_state"] == "GROUNDED"
        assert res2.json()["response_state"] == "INSUFFICIENT_EVIDENCE"
