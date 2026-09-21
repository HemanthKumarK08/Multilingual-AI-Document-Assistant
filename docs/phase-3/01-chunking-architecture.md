# Phase 3 — Chunking Pipeline Architecture

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.chunking`  
**Architecture Style:** Stateless, CPU-only, Pipeline Coordinator

---

## 1. Architectural Overview

The Phase 3 chunking pipeline operates as an intermediate transformation layer situated strictly between Phase 2 document parsing and Phase 4 vector embedding generation.

```
+-------------------------------------------------------------------------------+
|                       PHASE 2 PARSED ARTIFACT                                 |
|                 data/processed/{doc_id}_parsed.json                           |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                             CHUNKING PIPELINE                                 |
|                                                                               |
|  1. ChunkingCoordinator (app/services/chunking/coordinator.py)                |
|     - Loads canonical ParsedDocument and resolves manifest metadata           |
|                                                                               |
|  2. PageAwareBoundaryManager (app/services/chunking/boundaries.py)            |
|     - Iterates page by page (1-indexed)                                       |
|     - Clusters blocks by section heading context                              |
|                                                                               |
|  3. RecursiveCharacterChunker (app/services/chunking/recursive.py)            |
|     - Hierarchical natural separator splitting                                |
|     - Sliding window overlap backtracking (default: 100 chars)                |
|     - Exact character offset tracking [start_offset, end_offset)              |
|                                                                               |
|  4. ChunkValidator (app/services/chunking/validator.py)                       |
|     - Strict provenance field validation (20 attributes)                      |
|     - Regex stable ID validation: {doc_id}:p{page}:c{chunk_index}             |
|     - Source token coverage verification                                      |
|                                                                               |
|  5. Serialization (app/services/chunking/serialization.py)                    |
|     - Atomic temporary file replacement                                       |
|     - Deterministic UTF-8 JSON encoding                                       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                       PHASE 3 CHUNKED ARTIFACTS                               |
|                 data/processed/{doc_id}_chunks.json                           |
|                 data/processed/corpus_chunking_report.json                    |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Responsibilities

| Module | File Path | Primary Responsibilities |
| :--- | :--- | :--- |
| `constants` | `app/services/chunking/constants.py` | Defines default chunk size (`600`), overlap (`100`), min size (`1`), max ceiling (`2000`), natural separator hierarchy. |
| `exceptions` | `app/services/chunking/exceptions.py` | Defines typed exceptions: `ChunkingError`, `InvalidChunkConfigError`, `ChunkValidationError`, `SourceCoverageError`, `ArtifactNotFoundError`. |
| `models` | `app/services/chunking/models.py` | Pydantic DTOs for `ChunkingConfig`, `DocumentChunk` (20 provenance fields), `ChunkedDocumentArtifact`, `ChunkingReport`. |
| `recursive` | `app/services/chunking/recursive.py` | Pure, stateless recursive character chunker with natural boundary splitting and sliding-window overlap. |
| `boundaries` | `app/services/chunking/boundaries.py` | Manages 1-indexed page boundaries and structural section groupings. |
| `validator` | `app/services/chunking/validator.py` | Comprehensive verification of structural integrity, ID syntax, sequence continuity, and source coverage. |
| `serialization` | `app/services/chunking/serialization.py` | Atomic UTF-8 JSON writing via temporary file replacement. |
| `coordinator` | `app/services/chunking/coordinator.py` | High-level orchestrator for single-document and batch corpus chunking runs. |

---

## 3. Database & API Policy

### Database Decision
In Phase 3, chunk data is strictly persisted as canonical JSON artifacts under `data/processed/{doc_id}_chunks.json`. Database table modifications for individual chunks are deferred to Phase 4 (ChromaDB vector indexing) to avoid creating premature relational tables that duplicate vector store metadata. The `Document` table in SQLite retains an updated `chunk_count` metric for synchronization.

### API Policy
No public HTTP endpoints or web interfaces are introduced in Phase 3. The pipeline is consumed via the internal service layer (`ChunkingCoordinator`) and the command-line corpus runner (`scripts/chunk_corpus.py`).
