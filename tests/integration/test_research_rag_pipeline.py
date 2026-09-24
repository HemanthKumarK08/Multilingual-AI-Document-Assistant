"""
Research-Backed RAG Architecture Integration & Benchmark Suite (100 Cases)
Validates all Section S Critical Failure Tests and Section R Benchmark Cases:
1. 'NIRF management fee' returns complete answer without fragments.
2. 'What is the minimum attendance required for registered courses?' retrieves attendance chunk and never black ballpoint pen.
3. 'in which website credit guarantee scheme can be applied' preserves https://www.cgtmse.in.
4. Cross-lingual generation produces native Indic scripts or honest LANGUAGE_UNAVAILABLE.
5. AnswerGuard rejects English-only answers when target is Indic.
6. Nonsense / Out-of-Domain queries trigger deterministic abstention.
7. Numerical and URL questions preserve numbers and URLs faithfully.
8. Context reconstruction repairs boundary continuations (c123 -> c124).
9. Generic keyword overlap ('required', 'students') is prevented from dominating.
"""

import json
import os
import re
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.models import ContextPackage, GroundedAnswer, SourceCitation
from app.services.rag.answer_guard import answer_guard
from app.services.retrieval.models import CandidateChunk


@pytest.fixture(scope="module")
def benchmark_data():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "research_rag_benchmark.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_critical_failure_01_nirf_management_fee_no_fragment():
    """Critical Test 1: 'NIRF management fee' must return full answer without fragments."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "NIRF management fee",
            "target_language": "en"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["response_state"] == "GROUNDED"
    ans = data["answer_text"]
    assert not ans.startswith("is less")
    assert not ans.startswith("less to")
    assert not ans.startswith("fee.")
    assert "90%" in ans or "10,000" in ans or "1.0 lakh" in ans


@pytest.mark.asyncio
async def test_critical_failure_02_attendance_no_ballpoint_pen():
    """Critical Test 2: 'What is the minimum attendance required for registered courses?' must not retrieve ballpoint pen."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required for registered courses?",
            "target_language": "en"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["response_state"] == "GROUNDED"
    ans = data["answer_text"]
    assert "75%" in ans
    assert "ballpoint" not in ans.lower()
    assert "ball point" not in ans.lower()
    assert "pen" not in ans.lower()


@pytest.mark.asyncio
async def test_critical_failure_03_cgtmse_url_preservation():
    """Critical Test 3: 'in which website credit guarantee scheme can be applied' must preserve https://www.cgtmse.in."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "in which website credit guarantee scheme can be applied",
            "target_language": "en"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["response_state"] == "GROUNDED"
    assert "https://www.cgtmse.in" in data["answer_text"]


@pytest.mark.asyncio
async def test_critical_failure_04_cross_lingual_script_or_unavailable():
    """Critical Test 4: English -> Indic targets must produce native Indic script or LANGUAGE_UNAVAILABLE."""
    telugu_regex = re.compile(r"[\u0C00-\u0C7F]")
    kannada_regex = re.compile(r"[\u0C80-\u0CFF]")
    hindi_regex = re.compile(r"[\u0900-\u097F]")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Telugu target
        res_te = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required?",
            "target_language": "te"
        })
        assert res_te.status_code == 200
        d_te = res_te.json()
        assert d_te["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")
        if d_te["response_state"] == "GROUNDED":
            assert telugu_regex.search(d_te["answer_text"]) is not None
            assert kannada_regex.search(d_te["answer_text"]) is None

        # Kannada target
        res_kn = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required?",
            "target_language": "kn"
        })
        assert res_kn.status_code == 200
        d_kn = res_kn.json()
        assert d_kn["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")
        if d_kn["response_state"] == "GROUNDED":
            assert kannada_regex.search(d_kn["answer_text"]) is not None
            assert telugu_regex.search(d_kn["answer_text"]) is None

        # Hindi target
        res_hi = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance required?",
            "target_language": "hi"
        })
        assert res_hi.status_code == 200
        d_hi = res_hi.json()
        assert d_hi["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")
        if d_hi["response_state"] == "GROUNDED":
            assert hindi_regex.search(d_hi["answer_text"]) is not None


def test_critical_failure_05_answer_guard_rejection_of_english_for_indic_target():
    """Critical Test 5: AnswerGuard must reject English-only answer when target is Indic."""
    ctx = ContextPackage(
        selected_chunks=[CandidateChunk(
            chunk_id="c1", doc_id="d1", text_content="Evidence", filename="f.pdf"
        )],
        serialized_context="Evidence",
        total_characters=8,
        sources=[SourceCitation(source_id="Source 1", chunk_id="c1", doc_id="d1", filename="f.pdf", page_number=1)]
    )

    ans_telugu_target = GroundedAnswer(
        query_id="q1",
        answer_text="The minimum attendance required is 75 percent for all students. [Source 1]",
        response_language="te",
        grounded=True,
        sources=[SourceCitation(source_id="Source 1", chunk_id="c1", doc_id="d1", filename="f.pdf", page_number=1)],
    )

    res = answer_guard.verify_and_guard(
        answer=ans_telugu_target,
        context=ctx,
        query_text="What is the attendance?",
        target_language="te"
    )
    assert res.fallback_required is True
    assert res.fallback_reason == "MISSING_TARGET_SCRIPT"


@pytest.mark.asyncio
async def test_critical_failure_06_nonsense_query_abstention():
    """Critical Test 6: Nonsense / Gibberish query must trigger INSUFFICIENT_EVIDENCE abstention."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json={
            "query_text": "asdfghjkl zxcvbnm qwertyuiop",
            "target_language": "en"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["response_state"] == "INSUFFICIENT_EVIDENCE"
    assert data["is_fallback"] is True
    assert len(data.get("citations", [])) == 0


@pytest.mark.asyncio
async def test_critical_failure_07_full_100_cases_benchmark(benchmark_data):
    """Critical Test 7: Executes all 100+ cases from research_rag_benchmark.json and asserts state validity."""
    assert len(benchmark_data) >= 100, f"Expected at least 100 benchmark test cases, found {len(benchmark_data)}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for case in benchmark_data:
            payload = {
                "query_text": case["query"],
                "target_language": case.get("target_language"),
            }
            res = await ac.post("/api/v1/qa/query", json=payload)
            assert res.status_code == 200, f"HTTP failure on case {case['id']}"
            data = res.json()
            assert "response_state" in data
            assert len(data["answer_text"]) > 0

            exp_state = case.get("expected_state")
            if exp_state == "GROUNDED":
                assert data["response_state"] == "GROUNDED", (
                    f"Case {case['id']} expected GROUNDED, got {data['response_state']}: {data['answer_text']}"
                )
                assert len(data.get("citations", [])) > 0
                for kw in case.get("expected_keywords", []):
                    assert kw.lower() in data["answer_text"].lower(), (
                        f"Expected keyword '{kw}' missing in case {case['id']}: {data['answer_text']}"
                    )
            elif exp_state == "INSUFFICIENT_EVIDENCE":
                assert data["response_state"] == "INSUFFICIENT_EVIDENCE", (
                    f"Case {case['id']} expected INSUFFICIENT_EVIDENCE, got {data['response_state']}"
                )
                assert len(data.get("citations", [])) == 0
            elif exp_state == "GROUNDED_OR_LANG_UNAVAIL":
                assert data["response_state"] in ("GROUNDED", "LANGUAGE_UNAVAILABLE")

            # Verify negative keywords if specified
            for nkw in case.get("negative_keywords", []):
                assert nkw.lower() not in data["answer_text"].lower(), (
                    f"Negative keyword '{nkw}' found in case {case['id']}: {data['answer_text']}"
                )
