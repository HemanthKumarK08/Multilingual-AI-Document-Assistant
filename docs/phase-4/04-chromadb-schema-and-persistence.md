# Phase 4 — ChromaDB Schema and Persistence

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.vector_store.chroma_client`, `app.services.vector_store.collection`

---

## 1. Storage Backend & Persistence Configuration

- **Storage Location:** `data/vector_store/` (configured via `VECTOR_STORE_PERSIST_DIRECTORY`).
- **Engine:** ChromaDB `PersistentClient` utilizing embedded SQLite for catalog metadata and an HNSW graph for approximate nearest neighbor (ANN) vector indexing.
- **Client Configuration:**
  - `anonymized_telemetry=False` (Strict privacy compliance).
  - `allow_reset=True` (Enables clean re-indexing and test teardowns).

---

## 2. Collection Schema & HNSW Parameters

- **Collection Name:** `document_chunks` (configured via `VECTOR_STORE_COLLECTION_NAME`).
- **Distance Metric:** `cosine` (`hnsw:space: "cosine"`).
- **Collection-Level Metadata:**
  ```json
  {
    "hnsw:space": "cosine",
    "embedding_model_name": "intfloat/multilingual-e5-small",
    "embedding_dimension": 384,
    "index_version": 1
  }
  ```

---

## 3. Record Structure in ChromaDB

Each indexed record consists of:
1. **`id` (`str`):** Stable deterministic chunk identifier (e.g. `DOC-ACAD-001:p1:c0`).
2. **`embedding` (`List[float]`):** 384-dimensional dense vector.
3. **`document` (`str`):** Full `text_content` of the chunk for instant retrieval context in Phase 5.
4. **`metadata` (`Dict[str, Union[str, int, float, bool]]`):**
   - Flattened scalar metadata containing all 20 provenance attributes.
   - `extraction_notes` is stored as a serialized JSON string array (`"[]"`).
