"""
Phase 8.5 Integration Tests — Visual Big Data Analytics Dashboard API Contracts
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_analytics_health_endpoint(client):
    response = client.get("/api/v1/analytics/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "ready"]
    assert "parquet_lake_present" in data
    assert "analytics_precomputed" in data
    assert "analytics_directory" in data

def test_analytics_summary_contract(client):
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "source_record_count" in data or "total_queries" in data
    assert "grounded_answer_rate" in data
    assert "fallback_rate" in data
    assert "citation_validity_rate" in data
    assert "avg_total_latency_ms" in data
    assert "code_mixed_query_share" in data
    assert data["grounded_answer_rate"] >= 0.0
    assert data["fallback_rate"] >= 0.0

def test_analytics_volume_contract(client):
    response = client.get("/api/v1/analytics/volume")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data or "query_completed_count" in data
    assert "events_by_date" in data
    assert "events_by_hour" in data
    assert isinstance(data["events_by_date"], dict)

def test_analytics_languages_contract(client):
    response = client.get("/api/v1/analytics/languages")
    assert response.status_code == 200
    data = response.json()
    assert "language_distribution" in data
    assert "script_distribution" in data
    assert "code_mixed_percentage" in data
    assert isinstance(data["language_distribution"], dict)
    for lang, metrics in data["language_distribution"].items():
        assert "percentage" in metrics
        assert "count" in metrics
        assert "avg_latency_ms" in metrics

def test_analytics_retrieval_contract(client):
    response = client.get("/api/v1/analytics/retrieval")
    assert response.status_code == 200
    data = response.json()
    assert "avg_retrieval_latency_ms" in data
    assert "p50_retrieval_latency_ms" in data
    assert "p95_retrieval_latency_ms" in data
    assert "retrieval_by_language" in data
    assert isinstance(data["retrieval_by_language"], dict)

def test_analytics_rag_contract(client):
    response = client.get("/api/v1/analytics/rag")
    assert response.status_code == 200
    data = response.json()
    assert "grounded_answer_rate" in data
    assert "citation_validity_rate" in data
    assert "fallback_answer_rate" in data
    assert "provider_distribution" in data
    assert isinstance(data["provider_distribution"], dict)

def test_analytics_errors_contract(client):
    response = client.get("/api/v1/analytics/errors")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "error_events_count" in data
    assert "overall_error_rate" in data
    assert "fallback_events_count" in data
    assert "fallback_rate" in data

def test_analytics_timeseries_contract(client):
    response = client.get("/api/v1/analytics/timeseries")
    assert response.status_code == 200
    data = response.json()
    assert "daily_trends" in data
    assert "hourly_distribution" in data
    assert isinstance(data["daily_trends"], list)
    for day in data["daily_trends"]:
        assert "date" in day
        assert "queries" in day
        assert "grounded_rate" in day

def test_analytics_cross_metric_consistency(client):
    summary = client.get("/api/v1/analytics/summary").json()
    rag = client.get("/api/v1/analytics/rag").json()
    errors = client.get("/api/v1/analytics/errors").json()
    
    if summary.get("data_available", True):
        # Grounded rate consistency
        assert round(summary["grounded_answer_rate"], 1) == round(rag["grounded_answer_rate"], 1)
        # Fallback rate consistency
        assert round(summary["fallback_rate"], 1) == round(errors["fallback_rate"], 1)
        # Rates sum to ~100%
        assert abs(summary["grounded_answer_rate"] + summary["fallback_rate"] - 100.0) < 0.1
