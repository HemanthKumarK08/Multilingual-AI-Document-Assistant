"""
Integration tests for FastAPI endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "app_name" in data

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_status"] == "connected"

@pytest.mark.asyncio
async def test_list_documents():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1

@pytest.mark.asyncio
async def test_admin_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Valid login with default seeded credentials
        response = await ac.post("/admin/login", json={"username": "admin", "password": "admin_password_change_me"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_admin_login_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/admin/login", json={"username": "admin", "password": "wrong_password"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_ingest_document_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/documents/ingest",
            json={
                "file_path": "data/raw/academic_regulations/DOC-ACAD-001.txt",
                "doc_id": "DOC-ACAD-001",
                "display_title": "Autonomous Academic Regulations",
                "category": "academic_regulations",
                "version": "1.0",
                "allow_reingest": True
            }
        )
    assert response.status_code == 200

    data = response.json()
    assert data["doc_id"] == "DOC-ACAD-001"
    assert data["status"] == "parsed"
    assert data["character_count"] > 100

