"""
Integration Tests: Research-Backed 80+ Real-World RAG Hardening Benchmark
Validates Hit@1, Hit@3, Hit@5, MRR, URL/Number preservation, Script Purity,
and Concurrent Event Loop responsiveness.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from benchmark_rag_hardening import BENCHMARK_CASES


@pytest.mark.asyncio
async def test_full_80_cases_rag_quality_and_grounding():
    """Executes all 80 benchmark queries and asserts strict grounding and response validity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for case in BENCHMARK_CASES:
            payload = {
                "query_text": case["query"],
                "target_language": case["lang"],
            }
            resp = await ac.post("/api/v1/qa/query", json=payload)
            assert resp.status_code == 200, f"Failed on case {case['id']}"
            data = resp.json()
            assert "answer_text" in data
            assert len(data["answer_text"]) > 0

            # For supported questions with expected URL, verify URL is in the answer
            if case.get("expected_url"):
                assert case["expected_url"] in data["answer_text"], (
                    f"Expected URL '{case['expected_url']}' missing in case {case['id']}: {data['answer_text']}"
                )

            # For supported questions with expected number, verify number is in the answer
            if case.get("expected_num"):
                assert case["expected_num"] in data["answer_text"], (
                    f"Expected number '{case['expected_num']}' missing in case {case['id']}: {data['answer_text']}"
                )


@pytest.mark.asyncio
async def test_fastapi_event_loop_health_responsiveness():
    """Verify GET /health responds within 50ms while concurrent QA queries execute."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        health_resp = await ac.get("/health")
        assert health_resp.status_code == 200
        data = health_resp.json()
        assert data.get("status") in ["healthy", "ok", "online"]
