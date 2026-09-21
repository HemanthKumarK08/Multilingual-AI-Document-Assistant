"""
Integration Tests for AI Chat & Multilingual RAG QA (Phase 8.3)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_ask_ai_page_html():
    """Verify GET /ask returns the HTML application shell for web browsers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/ask", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_qa_query_english_attendance():
    """Verify POST /api/v1/qa/query executes English query and returns expected contract."""
    payload = {
        "query_text": "What is the minimum attendance percentage required?",
        "target_language": "en",
        "category": "attendance"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "answer_text" in res
    assert "is_fallback" in res
    assert "citations" in res
    assert "total_latency_ms" in res
    assert res["detected_language"] == "en"

@pytest.mark.asyncio
async def test_qa_query_kannada():
    """Verify POST /api/v1/qa/query processes Kannada Unicode query."""
    payload = {
        "query_text": "ಹಾಜರಾತಿ ನಿಯಮಗಳು ಯಾವುವು?",
        "target_language": "kn",
        "category": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "answer_text" in res
    assert res["detected_language"] == "kn"

@pytest.mark.asyncio
async def test_qa_query_hindi():
    """Verify POST /api/v1/qa/query processes Hindi Unicode query."""
    payload = {
        "query_text": "उपस्थिति के क्या नियम हैं?",
        "target_language": "hi",
        "category": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "answer_text" in res
    assert res["detected_language"] == "hi"

@pytest.mark.asyncio
async def test_qa_query_telugu():
    """Verify POST /api/v1/qa/query processes Telugu Unicode query."""
    payload = {
        "query_text": "హాజరు నిబంధనలు ఏమిటి?",
        "target_language": "te",
        "category": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "answer_text" in res
    assert res["detected_language"] == "te"

@pytest.mark.asyncio
async def test_qa_query_code_mixed_romanized():
    """Verify POST /api/v1/qa/query processes Romanized / code-mixed query."""
    payload = {
        "query_text": "minimum attendance eshtu percentage irbeku for exam?",
        "target_language": "en",
        "category": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "query_id" in res
    assert "answer_text" in res

@pytest.mark.asyncio
async def test_qa_query_validation_too_short():
    """Verify query validation rejects queries with fewer than 2 characters."""
    payload = {
        "query_text": "a",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 422  # Unprocessable Entity validation error

@pytest.mark.asyncio
async def test_qa_feedback_submission():
    """Verify POST /api/v1/qa/feedback records thumbs up/down feedback."""
    payload = {
        "query_id": "test-query-id-12345",
        "feedback": 1,
        "comment": "Accurate grounded answer"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/feedback", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "recorded"
    assert res["feedback"] == 1

