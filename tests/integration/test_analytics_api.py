"""
Integration tests for Analytics API endpoints (app/api/routes/analytics.py)
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_analytics_health(client):
    response = client.get("/analytics/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "analytics_precomputed" in data
    assert "parquet_lake_present" in data


def test_analytics_endpoints_with_data(client):
    endpoints = [
        "/analytics/summary",
        "/analytics/volume",
        "/analytics/languages",
        "/analytics/retrieval",
        "/analytics/rag",
        "/analytics/errors",
        "/analytics/timeseries",
    ]

    for ep in endpoints:
        response = client.get(ep)
        assert response.status_code == 200, f"Endpoint {ep} failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict)
        assert "data_available" in data or "source_record_count" in data or "status" in data
