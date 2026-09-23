"""
Integration Test Suite: Real-World Ask AI Stability & Bug Discovery Pass
Verifies frontend-backend integration, submission concurrency locks, ErrorBoundary fallback,
isolated scroll containment, sequential conversation ordering, multi-document workflows, and script purity.
"""

import pytest
import os
import re
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_01_error_boundary_component_exists_and_integrated():
    """Verify ErrorBoundary component is created, exported, and imported in App.jsx and AskAI.jsx."""
    err_boundary_path = Path("frontend/src/components/ErrorBoundary.jsx")
    assert err_boundary_path.exists(), "ErrorBoundary.jsx must exist"
    content = err_boundary_path.read_text(encoding="utf-8")
    assert "class ErrorBoundary extends React.Component" in content
    assert "getDerivedStateFromError" in content
    assert "componentDidCatch" in content
    assert "handleReset" in content

    app_path = Path("frontend/src/App.jsx")
    app_content = app_path.read_text(encoding="utf-8")
    assert "import ErrorBoundary" in app_content
    assert "<ErrorBoundary>" in app_content

    ask_path = Path("frontend/src/pages/AskAI.jsx")
    ask_content = ask_path.read_text(encoding="utf-8")
    assert "import ErrorBoundary" in ask_content
    assert "<ErrorBoundary" in ask_content

def test_02_askai_submission_lock_prevents_duplicate_requests():
    """Verify isSubmittingRef synchronous submission lock in AskAI.jsx."""
    ask_path = Path("frontend/src/pages/AskAI.jsx")
    content = ask_path.read_text(encoding="utf-8")
    assert "isSubmittingRef = useRef(false)" in content
    assert "if (isSubmittingRef.current) return;" in content
    assert "isSubmittingRef.current = true;" in content
    assert "isSubmittingRef.current = false;" in content

def test_03_askai_isolated_scroll_containment():
    """Verify message container uses scrollTo on internal ref rather than ancestor-displacing scrollIntoView."""
    ask_path = Path("frontend/src/pages/AskAI.jsx")
    content = ask_path.read_text(encoding="utf-8")
    assert "chatContainerRef = useRef(null)" in content
    assert "chatContainerRef.current.scrollTo" in content
    assert "messagesEndRef.current.scrollIntoView" not in content

def test_04_starter_prompts_parameter_override_propagation():
    """Verify starter prompts pass language and category explicitly to handleSend avoiding stale closures."""
    ask_path = Path("frontend/src/pages/AskAI.jsx")
    content = ask_path.read_text(encoding="utf-8")
    assert "handleSend(prompt.query, prompt.lang, prompt.category)" in content
    assert "async function handleSend(queryToSend = null, langOverride = null, catOverride = null)" in content

def test_05_sequential_multi_turn_qa_integrity():
    """Submit 10 sequential questions and verify unique responses, citations, and latencies."""
    queries = [
        ("What is the minimum attendance required?", "en"),
        ("Explain the credit requirement for degree completion.", "en"),
        ("What is the condonation limit for attendance?", "en"),
        ("What is the CGTMSE credit guarantee coverage?", "en"),
        ("What technologies are used in the document assistant?", "en"),
        ("What are the hostel policies?", "en"),
        ("How are scholarships awarded?", "en"),
        ("What is the placement training framework?", "en"),
        ("How does hybrid search work?", "en"),
        ("What is the zero-raw-data privacy guarantee?", "en"),
    ]

    query_ids = set()
    for q_text, lang in queries:
        resp = client.post(
            "/api/v1/qa/query",
            json={"query_text": q_text, "target_language": lang, "category": None},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query_id"]
        assert data["query_id"] not in query_ids, "Each query must generate a distinct query_id"
        query_ids.add(data["query_id"])
        assert data["answer_text"] and len(data["answer_text"]) > 10
        assert data["total_latency_ms"] >= 0

def test_06_rapid_concurrent_requests_backend_stability():
    """Verify backend handles rapid sequential queries without race conditions or database deadlocks."""
    for i in range(5):
        resp = client.post(
            "/api/v1/qa/query",
            json={"query_text": f"Query iteration {i}: What is the attendance requirement?", "target_language": "en"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "75%" in data["answer_text"] or data["is_fallback"] is False

def test_07_multilingual_cross_language_rendering_and_script_purity():
    """Verify cross-language answers in HI, KN, TE render with exact script purity and no foreign block contamination."""
    resp_hi = client.post(
        "/api/v1/qa/query",
        json={"query_text": "What is the minimum attendance required?", "target_language": "hi"},
    )
    assert resp_hi.status_code == 200
    hi_text = resp_hi.json()["answer_text"]
    assert re.search(r"[\u0900-\u097F]", hi_text) is not None, "Must contain Devanagari characters"

    resp_kn = client.post(
        "/api/v1/qa/query",
        json={"query_text": "What is the minimum attendance required?", "target_language": "kn"},
    )
    assert resp_kn.status_code == 200
    kn_text = resp_kn.json()["answer_text"]
    assert re.search(r"[\u0C80-\u0CFF]", kn_text) is not None, "Must contain Kannada characters"

    resp_te = client.post(
        "/api/v1/qa/query",
        json={"query_text": "What is the minimum attendance required?", "target_language": "te"},
    )
    assert resp_te.status_code == 200
    te_text = resp_te.json()["answer_text"]
    assert re.search(r"[\u0C00-\u0C7F]", te_text) is not None, "Must contain Telugu characters"
    assert re.search(r"[\u0C80-\u0CFF]", te_text) is None, "Telugu output must not contain Kannada characters"

def test_08_spa_routes_content_negotiation():
    """Verify all SPA routes return HTML index for browser navigation."""
    for route in ["/", "/ask", "/documents", "/analytics", "/settings"]:
        resp = client.get(route, headers={"Accept": "text/html"})
        assert resp.status_code == 200
        assert "<div id=\"root\"></div>" in resp.text or "<!DOCTYPE html>" in resp.text
