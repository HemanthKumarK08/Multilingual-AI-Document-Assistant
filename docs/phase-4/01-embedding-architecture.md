# Phase 4 — Embedding and Vector Store Architecture

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Components:** `app.services.embeddings`, `app.services.vector_store`  
**WBS Stages:** Stage 6 (Embedding Generation) & Stage 7 (Vector Store Indexing)

---

## 1. System Architecture Overview

Phase 4 establishes the vector ingestion backbone of the architecture. It ingests the canonical, validated Phase 3 chunk artifacts (`data/processed/{doc_id}_chunks.json`), converts them into 384-dimensional dense semantic vectors using `intfloat/multilingual-e5-small`, and stores them along with their complete provenance metadata in a persistent ChromaDB instance.

```
+-------------------------------------------------------------------------------+
|                       PHASE 3 CHUNKED ARTIFACTS                               |
|                 data/processed/{doc_id}_chunks.json                           |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                         EMBEDDING SUBSYSTEM                                   |
|                                                                               |
|  1. EmbeddingCoordinator (app/services/embeddings/coordinator.py)             |
|     - Loads Phase 3 chunks and orchestrates batch processing                  |
|                                                                               |
|  2. SentenceTransformerEmbeddingProvider                                      |
|     (app/services/embeddings/sentence_transformer.py)                        |
|     - Uses intfloat/multilingual-e5-small on CPU                              |
|     - Automatically applies 'passage: ' prefix for document chunks            |
|     - Generates L2-normalized 384-dimensional dense vectors                   |
|                                                                               |
|  3. Validation (app/services/embeddings/validation.py)                        |
|     - Verifies 384 dimensions and absence of NaN / Infinite float values      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                       VECTOR STORE SUBSYSTEM                                  |
|                                                                               |
|  4. ChromaClientFactory (app/services/vector_store/chroma_client.py)          |
|     - PersistentClient at data/vector_store/                                  |
|                                                                               |
|  5. CollectionManager (app/services/vector_store/collection.py)               |
|     - HNSW index with cosine distance metric                                  |
|     - Validates embedding model and dimension compatibility                   |
|                                                                               |
|  6. Idempotent Indexer (app/services/vector_store/indexing.py)                |
|     - Deterministic chunk_id keys ({doc_id}:p{page}:c{idx})                   |
|     - Compares SHA-256 hashes to skip unchanged and update changed records    |
|     - Stale record detection and optional deletion                            |
|                                                                               |
|  7. Metadata Serializer (app/services/vector_store/metadata.py)               |
|     - Formats all 20 provenance attributes into ChromaDB scalar metadata      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                     PERSISTENT VECTOR STORE & REPORTS                         |
|                 data/vector_store/ (ChromaDB SQLite + HNSW)                   |
|                 data/vector_store/index_report.json                           |
|                 data/embeddings/embedding_report.json                         |
+-------------------------------------------------------------------------------+
```

---

## 2. Package Structure & Module Responsibilities

### Embedding Subsystem (`app/services/embeddings/`)
- `constants.py`: Model name, dimension (`384`), prefixes (`passage: `, `query: `), batch defaults (`8`).
- `exceptions.py`: Typed hierarchy (`EmbeddingError`, `ModelLoadError`, `DimensionMismatchError`, `InvalidInputError`).
- `models.py`: Pydantic models for `EmbeddingConfig`, `EmbeddedChunk`, `EmbeddingBatchResult`, `EmbeddingRunReport`.
- `provider.py`: Abstract `EmbeddingProvider` Protocol definition.
- `sentence_transformer.py`: `SentenceTransformerEmbeddingProvider` implementing lazy loading and E5 prefixes.
- `batching.py`: Fixed-batch generator and order-preserving batch embedding runner.
- `validation.py`: Strict vector shape, dimension, and numerical validity checks.
- `coordinator.py`: High-level coordinator for chunk artifact embedding and batch reporting.

### Vector Store Subsystem (`app/services/vector_store/`)
- `constants.py`: Collection name (`document_chunks`), distance metric (`cosine`), default paths.
- `exceptions.py`: Typed hierarchy (`VectorStoreError`, `CollectionCompatibilityError`, `IndexingError`).
- `models.py`: Pydantic models for `VectorStoreConfig`, `VectorRecord`, `IndexStats`, `IndexRunReport`.
- `chroma_client.py`: Persistent ChromaDB client builder with telemetry disabled.
- `collection.py`: Collection lifecycle, HNSW cosine space configuration, and compatibility checker.
- `indexing.py`: Idempotent upserting, hash-change detection, and stale-record reconciliation.
- `metadata.py`: Serialization of 20 provenance attributes into ChromaDB primitive scalars.
- `validation.py`: Vector index audit checking record count, vector dimension, and text retrievability.
- `coordinator.py`: `VectorStoreCoordinator` orchestrating embedding, indexing, and report output.
