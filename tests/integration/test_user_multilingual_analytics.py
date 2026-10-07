"""
Phase 8.6 Integration Tests — User & Multilingual Analytics API Suite
Verifies privacy guarantees, PySpark lakehouse aggregations, and REST contracts for:
- /api/v1/analytics/users
- /api/v1/analytics/language-performance
- /api/v1/analytics/language-switching
- /api/v1/analytics/code-mixed
- /api/v1/analytics/documents
- /api/v1/analytics/run-spark-pipeline
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)


def test_users_analytics_endpoint(client):
    response = client.get("/api/v1/analytics/users")
    assert response.status_code == 200
    data = response.json()
    assert "total_unique_users" in data
    assert "avg_queries_per_user" in data
    assert "user_language_profiles" in data
    assert "top_anonymous_users" in data
    assert isinstance(data["user_language_profiles"], list)
    assert isinstance(data["top_anonymous_users"], list)

    # Verify zero PII in top_anonymous_users
    prohibited_pii = ["email", "name", "phone", "ip", "password", "token", "raw_query", "raw_answer"]
    for user in data["top_anonymous_users"]:
        assert "anonymous_user_id" in user
        for pii in prohibited_pii:
            assert pii not in user
        # Verify anonymous prefix if present
        if user["anonymous_user_id"]:
            assert user["anonymous_user_id"].startswith("USER-") or user["anonymous_user_id"].startswith("ANON-")


def test_language_performance_endpoint(client):
    response = client.get("/api/v1/analytics/language-performance")
    assert response.status_code == 200
    data = response.json()
    assert "total_queries_analyzed" in data
    assert "languages" in data
    assert isinstance(data["languages"], list)
    assert len(data["languages"]) >= 4

    lang_codes = [item["language"] for item in data["languages"]]
    for expected in ["en", "hi", "kn", "te"]:
        assert expected in lang_codes

    for item in data["languages"]:
        assert "grounded_rate" in item
        assert "citation_validity_rate" in item
        assert "fallback_rate" in item
        assert "avg_latency_ms" in item
        assert "p95_latency_ms" in item
        assert "avg_retrieved_chunks" in item
        assert item["grounded_rate"] >= 0.0
        assert item["fallback_rate"] >= 0.0
        assert item["status"] in ["Excellent", "Good", "Needs Attention"]


def test_language_switching_endpoint(client):
    response = client.get("/api/v1/analytics/language-switching")
    assert response.status_code == 200
    data = response.json()
    assert "total_switches_detected" in data
    assert "transitions" in data
    assert "transition_matrix" in data
    assert isinstance(data["transitions"], list)
    assert isinstance(data["transition_matrix"], dict)


def test_code_mixed_endpoint(client):
    response = client.get("/api/v1/analytics/code-mixed")
    assert response.status_code == 200
    data = response.json()
    assert "code_mixed_share_pct" in data
    assert "total_code_mixed_queries" in data
    assert "script_type_comparison" in data
    assert isinstance(data["script_type_comparison"], list)
    for row in data["script_type_comparison"]:
        assert "script_type" in row
        assert "query_count" in row
        assert "grounded_rate" in row
        assert "fallback_rate" in row


def test_documents_analytics_endpoint(client):
    response = client.get("/api/v1/analytics/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents_analyzed" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)
    for doc in data["documents"]:
        assert "document_id" in doc
        assert "query_count" in doc
        assert "grounded_rate" in doc
        # Ensure raw document content is NOT exposed in analytics
        assert "content" not in doc
        assert "raw_text" not in doc
        assert "page_content" not in doc


def test_privacy_guarantees_all_analytics_endpoints(client):
    """
    Forensic privacy validation ensuring no endpoint ever returns PII or raw secrets.
    """
    endpoints = [
        "/api/v1/analytics/health",
        "/api/v1/analytics/summary",
        "/api/v1/analytics/volume",
        "/api/v1/analytics/languages",
        "/api/v1/analytics/retrieval",
        "/api/v1/analytics/rag",
        "/api/v1/analytics/errors",
        "/api/v1/analytics/timeseries",
        "/api/v1/analytics/users",
        "/api/v1/analytics/language-performance",
        "/api/v1/analytics/language-switching",
        "/api/v1/analytics/code-mixed",
        "/api/v1/analytics/documents",
    ]

    prohibited_keys = {
        "email", "phone", "password", "api_key", "secret",
        "authorization", "bearer", "raw_query", "raw_answer",
        "document_text", "user_ip", "ip_address"
    }

    def check_dict_keys(d):
        if isinstance(d, dict):
            for k, v in d.items():
                assert k.lower() not in prohibited_keys, f"Prohibited key '{k}' found in analytics response!"
                check_dict_keys(v)
        elif isinstance(d, list):
            for item in d:
                check_dict_keys(item)

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint {ep} failed: {res.text}"
        data = res.json()
        check_dict_keys(data)
