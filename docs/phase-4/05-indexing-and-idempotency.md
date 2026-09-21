# Phase 4 — Indexing and Idempotency Policy

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.vector_store.indexing`

---

## 1. Idempotent Upsert Strategy

Running the indexing pipeline repeatedly against the same corpus must be strictly idempotent:

1. **New Chunks:** If `chunk_id` does not exist in the collection $\rightarrow$ `collection.add(...)`.
2. **Unchanged Existing Chunks:** If `chunk_id` exists and its indexed `file_hash_sha256` matches the current chunk's hash $\rightarrow$ **Skipped** (no redundant write or re-indexing).
3. **Modified Chunks:** If `chunk_id` exists but its source content or `file_hash_sha256` has changed $\rightarrow$ `collection.update(...)`.

---

## 2. Stale Record Detection & Controlled Reconciliation

When documents are deleted or re-chunked with fewer chunks, orphaned records may remain in the index:

1. **Detection:**
   - The indexer collects all existing IDs from the ChromaDB collection: $S_{\text{existing}}$.
   - The indexer collects all canonical chunk IDs from the current corpus: $S_{\text{corpus}}$.
   - Stale IDs are computed as: $S_{\text{stale}} = S_{\text{existing}} \setminus S_{\text{corpus}}$.
2. **Controlled Removal:**
   - By default, stale records are reported as warnings without destructive deletions.
   - When `--remove-stale` is explicitly specified, `collection.delete(ids=S_{stale})` safely purges only confirmed orphaned chunks.
