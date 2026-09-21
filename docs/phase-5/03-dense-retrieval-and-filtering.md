# Phase 5 — Dense Retrieval and Metadata Filtering

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 5 — Retrieval, Reranking, and Grounded RAG Pipeline  
**WBS Stage:** WBS Stage 8 (Retrieval Engine)  
**Date:** 2026-09-12  

---

## 1. Dense Semantic Vector Retrieval

Dense retrieval searches for semantically similar chunks across the 384-dimensional vector space stored in ChromaDB.

### 1.1. Cosine Distance to Similarity Formula
ChromaDB uses HNSW with cosine distance $d = 1 - \cos(\mathbf{q}, \mathbf{p}) \in [0, 2]$.  
Because embedding vectors are L2-normalized upon generation, the dense similarity score is bounded:
$$s_{\text{dense}} = \max(0.0, \min(1.0, 1.0 - d))$$

### 1.2. Query Parameters
- `RETRIEVAL_DENSE_TOP_K`: Default `12` candidates.
- `RETRIEVAL_MIN_SCORE`: Minimum score cutoff for candidate inclusion.

---

## 2. Metadata Filtering

Filters allow queries to be scoped to specific documents, categories, languages, or pages.

### 2.1. Supported Filter Schema
| Field | Type | ChromaDB Operator | Description |
|---|---|---|---|
| `doc_id` | `str` | `$eq` | Scopes search to a single document ID |
| `category` | `str` | `$eq` | Filters by institutional category (e.g., `academic`, `hostel`) |
| `language` | `str` | `$eq` | Filters by document language code |
| `script` | `str` | `$eq` | Filters by script type |
| `page_number`| `int` | `$eq` | Scopes to specific physical document page |
| `filename` | `str` | `$eq` | Filters by original source filename |

### 2.2. Safety and Validation
- Multiple filter parameters are combined using ChromaDB's `$and` construct.
- Empty or invalid filters are rejected early via `validate_filter()` without corrupting query execution.
