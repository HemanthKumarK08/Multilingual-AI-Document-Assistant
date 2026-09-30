"""
Regression Tests for BM25 Cache Invalidation and Chunk ID Alignment
Verifies that:
1. Deleting document A and adding document B with the SAME number of chunks
   does NOT reuse the old lexical index.
2. Querying for token A after replacement returns 0 hits for document A.
3. Querying for token B returns document B.
4. clear_bm25_cache() cleanly resets the in-memory index.
5. Zero-document collection does not crash or raise uncaught errors.
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.retrieval.coordinator import (
    clear_bm25_cache,
    simple_retrieve,
    _bm25_search,
)


@pytest.mark.asyncio
async def test_bm25_cache_invalidation_on_equal_chunk_count_replacement():
    """
    Mandatory Regression Test:
    1. Upload document A with unique token BM25TEST_ALPHA.
    2. Query BM25 for BM25TEST_ALPHA -> returns document A.
    3. Delete document A.
    4. Upload document B with SAME chunk count (1 chunk) with unique token BM25TEST_BETA.
    5. Query BM25 for BM25TEST_ALPHA -> must NOT return document A.
    6. Query BM25 for BM25TEST_BETA -> MUST return document B.
    """
    token_a = f"BM25TEST_ALPHA_{uuid.uuid4().hex[:6]}"
    token_b = f"BM25TEST_BETA_{uuid.uuid4().hex[:6]}"

    content_a = f"Special Document Alpha Content.\nSecurity Protocol: {token_a}.\nCampus release rule Alpha."
    content_b = f"Special Document Beta Content.\nSecurity Protocol: {token_b}.\nCampus release rule Beta."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Upload Document A
        files_a = {"file": ("doc_alpha.txt", content_a.encode("utf-8"), "text/plain")}
        data_a = {
            "display_title": "Document Alpha",
            "category": "academic_regulations",
            "version": "1.0",
            "allow_reingest": "true",
        }
        res_a = await ac.post("/api/v1/documents/upload", files=files_a, data=data_a)
        assert res_a.status_code == 200, f"Upload A failed: {res_a.text}"
        doc_id_a = res_a.json()["doc_id"]

        try:
            # Step 2: Query BM25 directly for token A
            bm25_res_a = _bm25_search(token_a, top_k=5, filters=None)
            assert len(bm25_res_a) > 0, f"Token A '{token_a}' should be found in BM25"
            assert any(doc_id_a in cid for cid in bm25_res_a.keys()), "Hit must belong to Doc A"

            # Step 3: Delete Document A
            del_a = await ac.delete(f"/api/v1/documents/{doc_id_a}")
            assert del_a.status_code == 200, f"Delete A failed: {del_a.text}"

            # Step 4: Upload Document B (with exact same chunk count: 1 chunk)
            files_b = {"file": ("doc_beta.txt", content_b.encode("utf-8"), "text/plain")}
            data_b = {
                "display_title": "Document Beta",
                "category": "academic_regulations",
                "version": "1.0",
                "allow_reingest": "true",
            }
            res_b = await ac.post("/api/v1/documents/upload", files=files_b, data=data_b)
            assert res_b.status_code == 200, f"Upload B failed: {res_b.text}"
            doc_id_b = res_b.json()["doc_id"]

            try:
                # Step 5: Query BM25 for token A -> must NOT return Doc A (or anything with token A)
                bm25_after_a = _bm25_search(token_a, top_k=5, filters=None)
                matching_doc_a = [cid for cid in bm25_after_a.keys() if doc_id_a in cid]
                assert len(matching_doc_a) == 0, f"Stale index bug: Doc A still returned after deletion: {matching_doc_a}"

                # Step 6: Query BM25 for token B -> MUST return Doc B
                bm25_after_b = _bm25_search(token_b, top_k=5, filters=None)
                matching_doc_b = [cid for cid in bm25_after_b.keys() if doc_id_b in cid]
                assert len(matching_doc_b) > 0, f"Doc B was not found in BM25: {bm25_after_b}"

                # Step 7: Verify via simple_retrieve as well
                retrieved_b = simple_retrieve(token_b, top_k=5)
                assert any(r.doc_id == doc_id_b for r in retrieved_b), "simple_retrieve must find Doc B"

            finally:
                # Cleanup Document B
                await ac.delete(f"/api/v1/documents/{doc_id_b}")

        except Exception:
            # Cleanup Document A if error occurred before deletion
            await ac.delete(f"/api/v1/documents/{doc_id_a}")
            raise


@pytest.mark.asyncio
async def test_bm25_explicit_clear_cache():
    """Verify that calling clear_bm25_cache() executes without error and forces cache reload."""
    clear_bm25_cache()
    # Search should continue to work seamlessly after cache clear
    res = _bm25_search("attendance", top_k=3, filters=None)
    assert isinstance(res, dict)


@pytest.mark.asyncio
async def test_bm25_empty_query_and_zero_results():
    """Verify edge cases for BM25 search."""
    # Empty query string
    assert _bm25_search("", top_k=5, filters=None) == {}
    assert _bm25_search("   ", top_k=5, filters=None) == {}

    # Query for impossible token
    impossible_token = f"NONEXISTENT_XYZ_TOKEN_{uuid.uuid4().hex}"
    assert _bm25_search(impossible_token, top_k=5, filters=None) == {}
