"""
Integration Tests for Multilingual Answer Generation & Cross-Language Propagation (Issue A Fix)
Verifies:
1. English -> English
2. Hindi -> Hindi
3. Kannada -> Kannada
4. Telugu -> Telugu
5. English query -> Hindi response
6. English query -> Kannada response
7. English query -> Telugu response
8. Hindi query -> English response
9. Kannada query -> English response
10. Telugu query -> English response
11. Citation preservation in all language combinations
12. Grounding preservation & no fabricated facts
13. Honest fallback behavior in native scripts
"""

import pytest
import re
from httpx import AsyncClient, ASGITransport
from app.main import app

CGTMSE_URL = "https://www.cgtmse.in"

@pytest.mark.asyncio
async def test_01_english_to_english_response():
    """1. English query with English response target."""
    payload = {
        "query_text": "What is the minimum attendance required?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "en"
    assert "75%" in data["answer_text"]
    assert len(data.get("citations", [])) > 0
    assert not re.search(r"[ऀ-౿]", data["answer_text"])

@pytest.mark.asyncio
async def test_02_hindi_to_hindi_response():
    """2. Hindi query with Hindi response target."""
    payload = {
        "query_text": "सेमेस्टर परीक्षा के लिए कितनी उपस्थिति अनिवार्य है?",
        "target_language": "hi"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "hi"
    assert "75%" in data["answer_text"]
    assert "उपस्थिति" in data["answer_text"]
    assert re.search(r"[ऀ-ॿ]", data["answer_text"])

@pytest.mark.asyncio
async def test_03_kannada_to_kannada_response():
    """3. Kannada query with Kannada response target."""
    payload = {
        "query_text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಎಷ್ಟು ಶೇಕಡಾ ಹಾಜರಾತಿ ಬೇಕು?",
        "target_language": "kn"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "kn"
    assert "75%" in data["answer_text"]
    assert "ಹಾಜರಾತಿ" in data["answer_text"]
    assert re.search(r"[ಀ-೿]", data["answer_text"])

@pytest.mark.asyncio
async def test_04_telugu_to_telugu_response():
    """4. Telugu query with Telugu response target."""
    payload = {
        "query_text": "పరీక్షలకు కనీస హాజరు ఎంత శాతం ఉండాలి?",
        "target_language": "te"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "te"
    assert "75%" in data["answer_text"]
    assert "హాజరు" in data["answer_text"]
    assert re.search(r"[ఀ-౿]", data["answer_text"])

@pytest.mark.asyncio
async def test_05_english_query_to_hindi_response():
    """5. English query with explicit Hindi target response language."""
    payload = {
        "query_text": "What is the minimum attendance required?",
        "target_language": "hi"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "hi"
    assert "75%" in data["answer_text"]
    assert "उपस्थिति" in data["answer_text"]
    assert re.search(r"[ऀ-ॿ]", data["answer_text"])

@pytest.mark.asyncio
async def test_06_english_query_to_kannada_response():
    """6. English query with explicit Kannada target response language."""
    payload = {
        "query_text": "What is the minimum attendance required?",
        "target_language": "kn"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "kn"
    assert "75%" in data["answer_text"]
    assert "ಹಾಜರಾತಿ" in data["answer_text"]
    assert re.search(r"[ಀ-೿]", data["answer_text"])

@pytest.mark.asyncio
async def test_07_english_query_to_telugu_response():
    """7. English query with explicit Telugu target response language."""
    payload = {
        "query_text": "What is the minimum attendance required?",
        "target_language": "te"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "te"
    assert "75%" in data["answer_text"]
    assert "హాజరు" in data["answer_text"]
    assert re.search(r"[ఀ-౿]", data["answer_text"])

@pytest.mark.asyncio
async def test_08_hindi_query_to_english_response():
    """8. Hindi query with explicit English target response language."""
    payload = {
        "query_text": "सेमेस्टर परीक्षा के लिए कितनी उपस्थिति अनिवार्य है?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "en"
    assert "75%" in data["answer_text"]
    assert "attendance" in data["answer_text"].lower()
    assert not re.search(r"[ऀ-ॿ]", data["answer_text"])

@pytest.mark.asyncio
async def test_09_kannada_query_to_english_response():
    """9. Kannada query with explicit English target response language."""
    payload = {
        "query_text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಎಷ್ಟು ಶೇಕಡಾ ಹಾಜರಾತಿ ಬೇಕು?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "en"
    assert "75%" in data["answer_text"]
    assert "attendance" in data["answer_text"].lower()
    assert not re.search(r"[ಀ-೿]", data["answer_text"])

@pytest.mark.asyncio
async def test_10_telugu_query_to_english_response():
    """10. Telugu query with explicit English target response language."""
    payload = {
        "query_text": "పరీక్షలకు కనీస హాజరు ఎంత శాతం ఉండాలి?",
        "target_language": "en"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "en"
    assert "75%" in data["answer_text"]
    assert "attendance" in data["answer_text"].lower()
    assert not re.search(r"[ఀ-౿]", data["answer_text"])

@pytest.mark.asyncio
async def test_11_citations_preserved_across_all_target_languages():
    """11. Verified citations attached for English, Hindi, Kannada, Telugu answers."""
    for lang in ["en", "hi", "kn", "te"]:
        payload = {
            "query_text": "in which website credit guarantee scheme can be applied",
            "target_language": lang
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/qa/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data.get("citations", [])) > 0
        assert CGTMSE_URL in data["answer_text"]
        assert any(c.get("page_number") == 10 for c in data.get("citations", []))

@pytest.mark.asyncio
async def test_12_grounding_preservation_and_technical_entities():
    """12. Technical entities (MLIs, URLs, percentages) preserved in native scripts."""
    payload = {
        "query_text": "in which website credit guarantee scheme can be applied",
        "target_language": "hi"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "CGTMSE" in data["answer_text"]
    assert "MLIs" in data["answer_text"]
    assert CGTMSE_URL in data["answer_text"]

@pytest.mark.asyncio
async def test_13_fallback_behavior_in_native_language():
    """13. Unanswerable query returns honest non-hallucinated fallback in target language."""
    payload = {
        "query_text": "What is the submarine cafeteria lunch menu?",
        "target_language": "hi"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert len(data.get("citations", [])) == 0

@pytest.mark.asyncio
async def test_14_telugu_output_script_purity_no_kannada_contamination():
    """14. Validates Telugu generated responses do not contain cross-script Kannada characters."""
    test_queries = [
        ("in which website credit guarantee scheme can be applied", "te"),
        ("What is the minimum attendance required?", "te"),
        ("పరీక్షలకు కనీస హాజరు ఎంత శాతం ఉండాలి?", "te"),
    ]
    kannada_char_regex = re.compile(r"[ಀ-೿]")
    telugu_char_regex = re.compile(r"[ఀ-౿]")

    for query_text, target_lang in test_queries:
        payload = {
            "query_text": query_text,
            "target_language": target_lang
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/v1/qa/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        ans = data["answer_text"]
        # Must contain genuine Telugu characters
        assert telugu_char_regex.search(ans) is not None, f"Expected Telugu script in answer: {ans}"
        # Must NOT contain Kannada script characters
        assert kannada_char_regex.search(ans) is None, f"Cross-script Kannada contamination detected in Telugu answer: {ans}"
        # Specifically verify correct Telugu form అర్హత for CGTMSE
        if "credit guarantee" in query_text:
            assert "అర్హత" in ans, f"Expected proper Telugu అర్హత in answer: {ans}"
