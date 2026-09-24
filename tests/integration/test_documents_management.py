"""
Integration Tests for Document Management & Ingestion (Phase 8.2)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_documents_list():
    """Verify GET /api/v1/documents returns list of registered documents."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1

    first_doc = docs[0]
    assert "doc_id" in first_doc
    assert "display_title" in first_doc
    assert "category" in first_doc
    assert "file_hash_sha256" in first_doc
    assert "status" in first_doc

@pytest.mark.asyncio
async def test_get_documents_with_category_filter():
    """Verify category filtering works on /api/v1/documents."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents?category=academic_regulations")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) > 0
    for d in docs:
        assert d["category"] == "academic_regulations"

@pytest.mark.asyncio
async def test_get_document_by_id():
    """Verify GET /api/v1/documents/{doc_id} returns detailed document record."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Fetch list to get a valid doc_id
        list_res = await ac.get("/api/v1/documents")
        valid_doc_id = list_res.json()[0]["doc_id"]

        response = await ac.get(f"/api/v1/documents/{valid_doc_id}")
    assert response.status_code == 200
    doc = response.json()
    assert doc["doc_id"] == valid_doc_id
    assert "filename" in doc
    assert "page_count" in doc

@pytest.mark.asyncio
async def test_get_document_by_id_not_found():
    """Verify 404 is returned for nonexistent doc_id."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/documents/NONEXISTENT-DOC-999")
    assert response.status_code == 404
    assert "not found" in response.json().get("detail", "").lower()

@pytest.mark.asyncio
async def test_upload_supported_txt_document():
    """Verify real document upload and ingestion via POST /api/v1/documents/upload."""
    file_content = (
        b"Multilingual AI Document Assistant Institutional Policy Document.\n"
        b"Section 1: Academic Regulations.\n"
        b"Students must maintain minimum 75% attendance in each semester."
    )
    files = {"file": ("test_policy_doc.txt", file_content, "text/plain")}
    data = {
        "display_title": "Test Institutional Policy 2026",
        "category": "academic_regulations",
        "version": "1.0",
        "allow_reingest": "true"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert "doc_id" in res
    assert res["status"] in ["parsed", "indexed", "completed"]
    assert res["page_count"] >= 1
    assert res["category"] == "academic_regulations"

@pytest.mark.asyncio
async def test_upload_unsupported_file_format_rejected():
    """Verify rejection of unsupported file extensions (e.g. .exe)."""
    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}
    data = {"category": "academic_regulations"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 400
    assert "unsupported file format" in response.json().get("detail", "").lower()

@pytest.mark.asyncio
async def test_upload_empty_file_rejected():
    """Verify rejection of 0-byte empty files."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    data = {"category": "academic_regulations"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 400
    assert "empty" in response.json().get("detail", "").lower()

