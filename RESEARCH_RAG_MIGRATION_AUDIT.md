# Research RAG Migration Audit

## Architectural Baseline vs Research Papers

This audit evaluates the current RAG architecture of the **Multilingual AI Document Assistant with Big Data Analytics** against three reference research papers:
1. **DUTIR at SemEval-2026 Task 8**: *"A Hybrid Retrieval and Faithfulness-Guarded Framework for Multi-Turn RAG"* (Query rewriting → hybrid dense + BM25 retrieval → RRF → answerability/confidence gating → generation → post-generation faithfulness guard).
2. **Ranaldi, Haddow & Birch, EACL 2026**: *"Multilingual Retrieval-Augmented Generation for Knowledge-Intensive Question Answering Task"* (CrossRAG: retrieved evidence → common-language evidence representation → answer generation → target-language response).
3. **Hybrid Retrieval-Augmented Generation for Robust Multilingual Document Question Answering (2025)**: (Semantic query expansion → multi-query retrieval → RRF → strict grounding → abstention when evidence is insufficient).

---

## Component Audit Matrix

| CURRENT COMPONENT | RESEARCH COMPONENT | CAN REUSE? | MUST CHANGE? | REASON |
| :--- | :--- | :---: | :---: | :--- |
| **Embedding Provider** (`sentence_transformer.py` / `multilingual-e5-small`) | Dense Vector Retriever | **YES** | **NO** | `intfloat/multilingual-e5-small` (384-dim, asymmetric `query:` / `passage:` prefixes) provides solid cross-lingual dense retrieval capabilities across Latin and Indic scripts. |
| **BM25 Lexical Retriever** (`lexical_retriever.py`) | Sparse Lexical Retriever | **YES** | **NO** | Robertson-Spärck Jones IDF with Unicode-aware tokenization correctly handles numbers, URLs, and Indic script lexemes with shared in-memory index caching. |
| **Score Fusion** (`hybrid.py`) | Multi-Query Reciprocal Rank Fusion (RRF) | **NO** | **YES** | Current `hybrid.py` applies a linear weighted combination on a single query. Research specifies true standard RRF: $RRF(d) = \sum_{q} \sum_{m \in \{dense, bm25\}} \frac{w_q \cdot w_m}{k + r_m(d)}$ with $k=60$ over multi-query variant runs. |
| **Query Understanding & Intent** (`query_processing.py`) | Deterministic Query Understanding Layer | **PARTIAL** | **YES** | Needs structured output with explicit intent categories (`FACTUAL`, `DEFINITION`, `HOW_TO`, `WHERE_TO`, `NUMERICAL`, `POLICY`, `COMPARISON`, `LIST`, `OUT_OF_DOMAIN`, `AMBIGUOUS`), entity extraction, and important term identification. |
| **Query Rewriter & Expansion** (`query_expansion.py`) | Controlled Query Variant Rewriter | **PARTIAL** | **YES** | Current system can produce up to 4 variants with hardcoded dictionary mappings. Must be bounded to $\le 3$ distinct variants (normalized, lexical-expanded, multilingual/transliterated) without slowing down QA. |
| **Multi-Turn Context Rewriter** (None) | Lightweight Conversational Dependency Rewriter | **NO** | **YES** | DUTIR architecture specifies lightweight multi-turn query rewriting using the last $\le 3$ session turns to resolve pronominal/contextual references without an extra database. |
| **Candidate Relevance Reranker** (`reranker.py`) | Research-Inspired Candidate Relevance Stage | **PARTIAL** | **YES** | Must ensure generic words (like "required", "student") never cause unrelated instructions (like black-ballpoint rules) to outrank specific topic chunks (like attendance or fees). |
| **Evidence Sufficiency Gate** (`evidence_gate.py`) | Answerability / Confidence Gate | **PARTIAL** | **YES** | Must upgrade from a single threshold/keyword check to a multi-factor answerability assessment returning `ANSWERABLE`, `PARTIALLY_ANSWERABLE`, or `UNANSWERABLE`. |
| **Context Builder & Stitcher** (`context_builder.py`) | Natural Document Order & Boundary Reconstruction | **YES** | **PARTIAL** | Keep predecessor boundary recovery and add safe successor recovery (max 1 pred + 1 succ), ensuring section and document boundaries are never crossed. |
| **Multilingual Evidence Normalization** (Ad-hoc) | CrossRAG Evidence Normalization | **NO** | **YES** | When cross-lingual generation is required (e.g. English source → Indic target), normalize evidence for the generator while preserving URLs, numbers, percentages, and organization names. |
| **LLM Inference Provider** (`llm_provider.py`) | Multilingual Grounded Generator | **PARTIAL** | **YES** | Remove dictionary-based mock Indic translation. Enforce honest priority: Gemini Multilingual API → Ollama local model → Controlled `LANGUAGE_UNAVAILABLE`. |
| **Mock LLM Fallback** (`llm_provider.py`) | Test/CI Extractive Provider | **PARTIAL** | **YES** | Mock provider must strictly serve deterministic unit tests and CI. For arbitrary Indic target generation without canned fixtures, it must return `LANGUAGE_UNAVAILABLE`. |
| **Post-Generation Faithfulness Guard** (`answer_guard.py`) | DUTIR Post-Generation Faithfulness Guard | **PARTIAL** | **YES** | Add structured evaluation returning `PASS` or `REJECT(reason)` across script purity, citation validity, number mismatch, URL preservation, and fragment detection. |
| **Response State Machine** (`routes/qa.py`, `ChatMessageItem.jsx`) | Authoritative Response State Model | **YES** | **NO** | Already enforces `GROUNDED`, `PARTIAL`, `INSUFFICIENT_EVIDENCE`, `LANGUAGE_UNAVAILABLE`, `ERROR` cleanly between backend and frontend. |
| **ChromaDB Vector Store** (`vector_store/`) | Chunk Vector Index (490 chunks) | **YES** | **NO** | Existing collection `document_chunks` contains properly chunked and metadata-indexed passages. |
| **SQLite Application Database** (`app.db`) | Document & Chunk Metadata Store | **YES** | **NO** | Retains relational integrity, document hashes, and status. |
| **Frontend Stack** (React, Vite, Tailwind) | Chat UI & Response Presentation | **YES** | **NO** | UI layout, badges, TTS, citations, and telemetry viewers work effectively. |

---

## Key Principles & Guardrails for Implementation

1. **Keep the Core Stack**: Retain FastAPI, SQLite, ChromaDB, `multilingual-e5-small`, BM25, React, Vite, Tailwind, PySpark. No new heavy databases or microservices.
2. **Honest Multilingual Policy**: If no capable multilingual generative model is active, return `LANGUAGE_UNAVAILABLE` rather than fabricating Indic translations.
3. **Controlled Query Variants**: Maximum 3 query variants per request to preserve low latency ($P50 < 300\text{ms}$ for retrieval).
4. **True RRF Fusion**: Execute Dense (top-20) + BM25 (top-20) per variant, fusing via Reciprocal Rank Fusion ($k=60$) into a top-20 candidate pool.
5. **No Fake Claims**: Report real measured benchmark numbers across 100 test cases and verify visually in real Chrome.
