"""
Integration Tests for Advanced Citations & Evidence Provenance (Phase 8.4)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_grounded_answer_citation_structure():
    """Verify that citations returned by the QA pipeline contain all required provenance fields."""
    from app.services.rag.coordinator import RAGCoordinator
    from app.services.rag.llm_provider import MockLLMProvider

    # Use MockLLMProvider to test grounded citation assembly deterministically
    mock_rag = RAGCoordinator(llm_provider=MockLLMProvider())
    answer = mock_rag.answer("What is the minimum attendance requirement?", language="en")

    assert answer.grounded is True
    assert answer.fallback_used is False
    assert len(answer.sources) > 0

    first_source = answer.sources[0]
    assert hasattr(first_source, "doc_id")
    assert hasattr(first_source, "filename")
    assert hasattr(first_source, "page_number")
    assert hasattr(first_source, "section_title")
    assert first_source.page_number >= 1

@pytest.mark.asyncio
async def test_qa_query_response_citation_schema():
    """Verify that POST /api/v1/qa/query serializes Citation objects according to API contract."""
    payload = {
        "query_text": "What are the rules regarding attendance?",
        "target_language": "en",
        "category": "attendance"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "citations" in res
    assert isinstance(res["citations"], list)

    for cite in res["citations"]:
        assert "document_id" in cite
        assert "document_title" in cite
        assert "category" in cite
        assert "page_number" in cite
        assert "chunk_index" in cite
        assert "similarity_score" in cite
        assert "excerpt" in cite
        assert cite["similarity_score"] >= 0.0

@pytest.mark.asyncio
async def test_fallback_has_zero_phantom_citations():
    """Verify that out-of-domain queries return empty citations without phantom sources."""
    payload = {
        "query_text": "Who won the premier league match yesterday in London?",
        "target_language": "en",
        "category": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["is_fallback"] is True
    assert len(res["citations"]) == 0

@pytest.mark.asyncio
async def test_feedback_positive_submission():
    """Verify positive feedback (+1) submission on a valid query_id."""
    payload = {
        "query_id": "eval-provenance-query-001",
        "feedback": 1,
        "comment": "Accurate page and source citation"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/feedback", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "recorded"
    assert res["feedback"] == 1

@pytest.mark.asyncio
async def test_feedback_negative_submission():
    """Verify negative feedback (-1) submission on a valid query_id."""
    payload = {
        "query_id": "eval-provenance-query-002",
        "feedback": -1,
        "comment": "Needs more detail"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/feedback", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "recorded"
    assert res["feedback"] == -1

@pytest.mark.asyncio
async def test_technical_details_timing_metrics():
    """Verify that timing and latency metrics are populated in QA response."""
    payload = {
        "query_text": "attendance requirement",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "retrieval_latency_ms" in res
    assert "generation_latency_ms" in res
    assert "total_latency_ms" in res
    assert res["total_latency_ms"] >= 0.0

