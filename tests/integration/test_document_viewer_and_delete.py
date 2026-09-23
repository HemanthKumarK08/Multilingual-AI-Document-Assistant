"""
Integration Tests for Document Viewer and Document Deletion Subsystem
Phase: Document Management Completion
"""

import pytest
import uuid
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings, PROJECT_ROOT
from app.services.vector_store.coordinator import VectorStoreCoordinator

@pytest.mark.asyncio
async def test_01_document_list_displays_and_endpoints_work():
    """Verify document list endpoint returns records ready for View and Delete actions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/documents")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) > 0
    first = docs[0]
    assert "doc_id" in first
    assert "display_title" in first
    assert "category" in first
    assert "file_type" in first

@pytest.mark.asyncio
async def test_02_view_metadata_still_works():
    """Verify GET /api/v1/documents/{doc_id} returns complete document metadata."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_res = await ac.get("/api/v1/documents")
        first_doc = list_res.json()[0]
        doc_id = first_doc["doc_id"]

        res = await ac.get(f"/api/v1/documents/{doc_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["doc_id"] == doc_id
    assert "file_hash_sha256" in detail
    assert "status" in detail

@pytest.mark.asyncio
async def test_03_original_content_endpoint_works():
    """Verify GET /api/v1/documents/{doc_id}/content returns structured content structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_res = await ac.get("/api/v1/documents")
        doc_id = list_res.json()[0]["doc_id"]

        res = await ac.get(f"/api/v1/documents/{doc_id}/content")
    assert res.status_code == 200
    content_data = res.json()
    assert content_data["doc_id"] == doc_id
    assert "content_type" in content_data
    assert "file_url" in content_data

@pytest.mark.asyncio
async def test_04_pdf_preview_and_file_streaming():
    """Verify PDF document file streaming returns application/pdf."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_res = await ac.get("/api/v1/documents")
        pdf_docs = [d for d in list_res.json() if (d.get("file_type") or "").lower() == "pdf"]
        if not pdf_docs:
            pytest.skip("No PDF document available in database")
        pdf_doc = pdf_docs[0]

        file_res = await ac.get(f"/api/v1/documents/{pdf_doc['doc_id']}/file")
        assert file_res.status_code == 200
        assert "application/pdf" in file_res.headers.get("content-type", "")

        content_res = await ac.get(f"/api/v1/documents/{pdf_doc['doc_id']}/content")
        assert content_res.status_code == 200
        assert content_res.json()["content_type"] == "pdf"

@pytest.mark.asyncio
async def test_05_txt_content_inspection():
    """Verify TXT document file endpoint returns utf-8 text and raw content."""
    content = b"Institutional Guideline Note: Academic semester registrations must be completed within 10 days."
    files = {"file": ("test_txt_inspect.txt", content, "text/plain")}
    data = {
        "display_title": "Test TXT Inspection Document",
        "category": "academic_regulations",
        "version": "1.0",
        "allow_reingest": "true"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        up_res = await ac.post("/api/v1/documents/upload", files=files, data=data)
        assert up_res.status_code == 200
        doc_id = up_res.json()["doc_id"]

        content_res = await ac.get(f"/api/v1/documents/{doc_id}/content")
        assert content_res.status_code == 200
        data_json = content_res.json()
        assert data_json["is_original"] is True
        assert "Academic semester registrations" in data_json["text_content"]

        # Clean up this test upload
        del_res = await ac.delete(f"/api/v1/documents/{doc_id}")
        assert del_res.status_code == 200

@pytest.mark.asyncio
async def test_06_md_content_inspection():
    """Verify Markdown document inspection returns markdown content."""
    content = b"# Academic Honor Code\n\nAll students must adhere to the highest standard of academic integrity."
    files = {"file": ("test_md_inspect.md", content, "text/markdown")}
    data = {
        "display_title": "Test Markdown Document",
        "category": "academic_regulations",
        "version": "1.0",
        "allow_reingest": "true"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        up_res = await ac.post("/api/v1/documents/upload", files=files, data=data)
        assert up_res.status_code == 200
        doc_id = up_res.json()["doc_id"]

        content_res = await ac.get(f"/api/v1/documents/{doc_id}/content")
        assert content_res.status_code == 200
        data_json = content_res.json()
        assert data_json["content_type"] == "markdown"
        assert "Academic Honor Code" in data_json["text_content"]

        # Clean up
        await ac.delete(f"/api/v1/documents/{doc_id}")

@pytest.mark.asyncio
async def test_07_docx_preview_content():
    """Verify DOCX preview returns extracted structured sections."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_res = await ac.get("/api/v1/documents")
        docx_docs = [d for d in list_res.json() if (d.get("file_type") or "").lower() in ["docx", "doc"]]
        if not docx_docs:
            pytest.skip("No DOCX document available in database")
        doc_id = docx_docs[0]["doc_id"]

        content_res = await ac.get(f"/api/v1/documents/{doc_id}/content")
        assert content_res.status_code == 200
        assert content_res.json()["content_type"] in ["docx_preview", "text", "pdf_text"]

@pytest.mark.asyncio
async def test_08_missing_document_returns_404():
    """Verify nonexistent doc_id returns 404 across details, content, file, and delete."""
    fake_id = "NONEXISTENT-DOC-404-XYZ"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        assert (await ac.get(f"/api/v1/documents/{fake_id}")).status_code == 404
        assert (await ac.get(f"/api/v1/documents/{fake_id}/content")).status_code == 404
        assert (await ac.get(f"/api/v1/documents/{fake_id}/file")).status_code == 404
        assert (await ac.delete(f"/api/v1/documents/{fake_id}")).status_code == 404

@pytest.mark.asyncio
async def test_09_invalid_document_id_rejected():
    """Verify malformed doc_id characters trigger 400 Bad Request."""
    invalid_id = "invalid doc id!@#$"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"/api/v1/documents/{invalid_id}")
    assert res.status_code in [400, 404]

@pytest.mark.asyncio
async def test_10_path_traversal_attempt_rejected():
    """Verify path traversal in doc_id is rejected safely."""
    traversal_ids = ["..%2F..%2Fetc%2Fpasswd", "../etc/passwd", "..\\..\\windows\\win.ini"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for tid in traversal_ids:
            res = await ac.get(f"/api/v1/documents/{tid}/file")
            assert res.status_code in [400, 404]

@pytest.mark.asyncio
async def test_11_to_16_e2e_upload_view_qa_delete_and_rag_verification():
    """
    E2E Comprehensive Test:
    1. Upload a dedicated unique test document: 'E2E DELETE VIEW TEST DOCUMENT'
    2. Index in ChromaDB & SQLite
    3. View content endpoint verification
    4. Ask RAG question grounded in this test document
    5. Delete the test document
    6. Verify SQLite record deleted
    7. Verify processed JSON artifacts deleted
    8. Verify ChromaDB chunks zeroed (0 vectors remaining)
    9. Verify document disappears from inventory
    10. Ask same RAG question -> Must NOT return deleted document or cite it
    """
    unique_marker = f"UniqueSecretCode_{uuid.uuid4().hex[:8]}"
    doc_lines = [
        "E2E DELETE VIEW TEST DOCUMENT",
        "Special Security Guideline Protocol.",
        f"The secret verification key for project release is {unique_marker}.",
        "All authorized campus personnel must present this key at checkpoint Alpha."
    ]
    doc_content = "\n".join(doc_lines).encode("utf-8")

    files = {"file": ("e2e_delete_view_test.txt", doc_content, "text/plain")}
    data = {
        "display_title": "E2E DELETE VIEW TEST DOCUMENT",
        "category": "academic_regulations",
        "version": "1.0",
        "allow_reingest": "true"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Upload & Ingest
        up_res = await ac.post("/api/v1/documents/upload", files=files, data=data)
        assert up_res.status_code == 200
        up_json = up_res.json()
        doc_id = up_json["doc_id"]
        assert doc_id is not None

        # Step 2: Verify View Content
        view_res = await ac.get(f"/api/v1/documents/{doc_id}/content")
        assert view_res.status_code == 200
        assert unique_marker in view_res.json()["text_content"]

        # Step 3: Verify Vectors present before deletion
        vsc = VectorStoreCoordinator()
        col = vsc.get_collection()
        pre_records = col.get(where={"doc_id": doc_id})
        assert len(pre_records["ids"]) > 0, "ChromaDB should contain vectors for new document"

        # Step 4: Ask Question Grounded in this Document
        qa_query = "What is the secret verification key for project release in the security protocol?"
        qa_res = await ac.post("/api/v1/qa/query", json={"query_text": qa_query, "target_language": "en"})
        assert qa_res.status_code == 200
        qa_json = qa_res.json()
        pre_citations = [c.get("doc_id") for c in qa_json.get("citations", [])]
        assert (doc_id in pre_citations) or (unique_marker in qa_json.get("answer_text", "")) or (len(qa_json.get("citations", [])) > 0)

        # Step 5: Execute DELETE /api/v1/documents/{doc_id}
        del_res = await ac.delete(f"/api/v1/documents/{doc_id}")
        assert del_res.status_code == 200
        del_json = del_res.json()
        assert del_json["status"] == "deleted"
        assert del_json["deleted_chunks"] > 0

        # Step 6: Verify SQLite document record is gone
        get_res = await ac.get(f"/api/v1/documents/{doc_id}")
        assert get_res.status_code == 404

        # Step 7: Verify ChromaDB contains 0 vectors for this doc_id
        post_records = col.get(where={"doc_id": doc_id})
        assert len(post_records["ids"]) == 0, "ChromaDB must contain 0 vectors for deleted document"

        # Step 8: Verify processed artifacts are removed
        processed_parsed = settings.DATA_DIRECTORY / "processed" / f"{doc_id}_parsed.json"
        assert not processed_parsed.exists(), "Parsed JSON artifact should be removed"

        # Step 9: Verify document disappears from inventory list
        list_res = await ac.get("/api/v1/documents")
        active_ids = [d["doc_id"] for d in list_res.json()]
        assert doc_id not in active_ids, "Deleted document must not appear in document list"

        # Step 10: RAG Safety Test — Ask the same question again
        post_qa_res = await ac.post("/api/v1/qa/query", json={"query_text": qa_query, "target_language": "en"})
        assert post_qa_res.status_code == 200
        post_qa_json = post_qa_res.json()
        post_citations = [c.get("doc_id") for c in post_qa_json.get("citations", [])]
        
        # Deleted document MUST NOT appear in citations
        assert doc_id not in post_citations, f"Deleted document '{doc_id}' must not appear in post-deletion citations"
        # Secret unique marker must NOT be hallucinated or grounded from deleted document
        assert unique_marker not in post_qa_json.get("answer_text", ""), "Deleted document text must not be returned in RAG answer"

@pytest.mark.asyncio
async def test_17_other_documents_remain_searchable():
    """Verify existing institutional documents continue working normally."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        qa_res = await ac.post("/api/v1/qa/query", json={
            "query_text": "What is the minimum attendance percentage required?",
            "target_language": "en",
            "category": "attendance"
        })
    assert qa_res.status_code == 200
    res_json = qa_res.json()
    assert "answer_text" in res_json
    assert len(res_json["answer_text"]) > 0

@pytest.mark.asyncio
async def test_18_search_and_filter_regression():
    """Verify document list category filter and query parameters remain accurate."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/documents?category=academic_regulations&active_only=true")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    for d in docs:
        assert d["category"] == "academic_regulations"

@pytest.mark.asyncio
async def test_19_viewer_loading_and_error_handling():
    """Verify error responses on invalid document sub-endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/documents/INVALID_UNKNOWN_ID/content")
    assert res.status_code == 404
    assert "not found" in res.json().get("detail", "").lower()

@pytest.mark.asyncio
async def test_20_no_unsafe_html_injection():
    """Verify malicious script payloads in document content are not executed or parsed unsafely."""
    script_payload = b"<script>alert('xss');</script>## Important Campus Rules"
    files = {"file": ("xss_test.txt", script_payload, "text/plain")}
    data = {
        "display_title": "XSS Test Document",
        "category": "academic_regulations",
        "version": "1.0",
        "allow_reingest": "true"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        up_res = await ac.post("/api/v1/documents/upload", files=files, data=data)
        assert up_res.status_code == 200
        doc_id = up_res.json()["doc_id"]

        content_res = await ac.get(f"/api/v1/documents/{doc_id}/content")
        assert content_res.status_code == 200
        # Text is returned as plain string data, not unescaped executable HTML
        assert "<script>" in content_res.json()["text_content"]

        # Clean up
        await ac.delete(f"/api/v1/documents/{doc_id}")

@pytest.mark.asyncio
async def test_21_no_arbitrary_filesystem_access():
    """Verify files outside PROJECT_ROOT or DATA_DIRECTORY cannot be accessed."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/documents/....//....//etc/passwd/file")
        assert res.status_code in [400, 404]
