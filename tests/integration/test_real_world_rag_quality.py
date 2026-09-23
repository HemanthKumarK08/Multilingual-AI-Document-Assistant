"""
Integration Tests: Real-World MSME RAG Quality, URL Preservation & CGTMSE Grounding
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

CGTMSE_URL = "https://www.cgtmse.in"
MSME_DOC_ID = "DOC-UP-MSMESCHEMEBOOKLE-3692EB"

@pytest.mark.asyncio
async def test_cgtmse_website_query_original_english():
    """Verify original real-world English question preserves https://www.cgtmse.in and MLI instructions."""
    payload = {
        "query_text": "in which website credit guarantee scheme can be applied",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["is_fallback"] is False
    assert CGTMSE_URL in res["answer_text"]
    assert "MLIs" in res["answer_text"] or "Banks" in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_natural_english_website_query():
    """Verify natural English website question retrieves Page 10 and includes exact URL."""
    payload = {
        "query_text": "Which website can I use to apply for the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_where_to_apply_query():
    """Verify application-location query identifies MLIs (Banks/NBFCs) and guidelines URL."""
    payload = {
        "query_text": "Where can I apply for the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "MLIs" in res["answer_text"] or "Banks" in res["answer_text"]
    assert CGTMSE_URL in res["answer_text"]

@pytest.mark.asyncio
async def test_cgtmse_how_to_apply_query():
    """Verify how-to-apply query retrieves section on Page 10."""
    payload = {
        "query_text": "How can I apply for the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "MLIs" in res["answer_text"] or "Banks" in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_objective_query_disambiguation():
    """Verify objective question routes to Page 9 objective and does not confuse with application steps."""
    payload = {
        "query_text": "What is the objective of the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["is_fallback"] is False
    assert any(c.get("page_number") in [9, 10] for c in res.get("citations", []))
    assert "credit facility" in res["answer_text"].lower() or "micro" in res["answer_text"].lower() or "collateral" in res["answer_text"].lower()

@pytest.mark.asyncio
async def test_cgtmse_hindi_website_query():
    """Verify Hindi query retrieves CGTMSE Page 10 and includes https://www.cgtmse.in."""
    payload = {
        "query_text": "क्रेडिट गारंटी योजना के लिए किस वेबसाइट पर आवेदन करें?",
        "target_language": "hi"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_kannada_website_query():
    """Verify Kannada query retrieves CGTMSE Page 10 and includes https://www.cgtmse.in."""
    payload = {
        "query_text": "ಕ್ರೆಡಿಟ್ ಗ್ಯಾರಂಟಿ ಯೋಜನೆಗೆ ಯಾವ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು?",
        "target_language": "kn"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_telugu_website_query():
    """Verify Telugu query retrieves CGTMSE Page 10 and includes https://www.cgtmse.in."""
    payload = {
        "query_text": "క్రెడిట్ గ్యారెంటీ పథకం కోసం ఏ వెబ్‌సైట్‌లో దరఖాస్తు చేసుకోవాలి?",
        "target_language": "te"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_romanized_kannada_code_mixed():
    """Verify Romanized Kannada query preserves CGTMSE URL."""
    payload = {
        "query_text": "credit guarantee scheme ge apply madoke yav website?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_romanized_hindi_code_mixed():
    """Verify Romanized Hindi query preserves CGTMSE URL."""
    payload = {
        "query_text": "credit guarantee scheme ke liye kaunsi website par apply kare?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert CGTMSE_URL in res["answer_text"]
    assert any(c.get("page_number") == 10 for c in res.get("citations", []))

@pytest.mark.asyncio
async def test_cgtmse_url_preservation_strict():
    """Strict assertion that the exact URL https://www.cgtmse.in is retained in answer payload."""
    payload = {
        "query_text": "What is the official website for the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "https://www.cgtmse.in" in res["answer_text"]
    assert "cgtmse" in res["answer_text"].lower()

@pytest.mark.asyncio
async def test_cgtmse_no_fabricated_urls():
    """Assert that no hallucinated or invented URLs are present in response."""
    payload = {
        "query_text": "in which website credit guarantee scheme can be applied",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    ans = res["answer_text"]
    assert "cgtmse.gov.in" not in ans
    assert "applycgtmse.com" not in ans
    assert "msme-apply.in" not in ans

@pytest.mark.asyncio
async def test_cgtmse_citation_page_grounding():
    """Assert citation is linked to Page 10 chunk containing How to apply."""
    payload = {
        "query_text": "Where should I apply for the Credit Guarantee Scheme?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    citations = res.get("citations", [])
    assert len(citations) > 0
    p10_citations = [c for c in citations if c.get("page_number") == 10]
    assert len(p10_citations) > 0

@pytest.mark.asyncio
async def test_cgtmse_application_vs_website_distinction():
    """Assert answer distinguishes applying through MLIs while providing URL for detailed guidelines."""
    payload = {
        "query_text": "in which website credit guarantee scheme can be applied",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/qa/query", json=payload)
    assert response.status_code == 200
    res = response.json()
    ans = res["answer_text"]
    assert "MLIs" in ans or "Banks" in ans
    assert CGTMSE_URL in ans
