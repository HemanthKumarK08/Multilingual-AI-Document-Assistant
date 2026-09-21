"""
Integration tests for Frontend Shell, SPA Routes, and Static Asset Delivery (Phase 8.1)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_frontend_root_html():
    """Verify GET / returns the HTML application shell for web browsers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Multilingual AI Document Assistant" in response.text or "<div id=\"root\">" in response.text

@pytest.mark.asyncio
async def test_frontend_root_json_negotiation():
    """Verify GET / returns JSON metadata when requested by programmatic clients."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert data["status"] == "online"
    assert "app_name" in data

@pytest.mark.asyncio
async def test_frontend_spa_routes_return_html():
    """Verify client-side SPA routes (/documents, /ask, /analytics, /settings) return the application shell."""
    spa_routes = ["/documents", "/ask", "/analytics", "/settings"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for route in spa_routes:
            response = await ac.get(route, headers={"Accept": "text/html"})
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert "<!doctype html>" in response.text.lower() or "<html" in response.text.lower()

@pytest.mark.asyncio
async def test_api_v1_endpoints_remain_intact():
    """Verify that backend REST APIs remain functional under /api/v1 prefix."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Health endpoint
        r_health = await ac.get("/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "ok"

        # Analytics Health endpoint
        r_analytics = await ac.get("/api/v1/analytics/health")
        assert r_analytics.status_code == 200
        assert r_analytics.json()["status"] == "healthy"

        # Documents endpoint
        r_docs = await ac.get("/api/v1/documents")
        assert r_docs.status_code == 200
        assert isinstance(r_docs.json(), list)

