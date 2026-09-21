# Development Roadmap & 17-Stage Work Breakdown Structure

This document defines the sequential development lifecycle, stage dependencies, milestones, and formal exit criteria for the **Multilingual AI Document Assistant with Big Data Analytics**.

---

## 1. 17-Stage Comprehensive Implementation Lifecycle

```
[Phase 0: Discovery, Scope & Feasibility] (COMPLETED)
                     │
                     ▼
STAGE 1: Architecture, Contracts & Environment Setup
STAGE 2: SQLite Relational Database Foundation & Schemas
STAGE 3: Document Upload Ingestion & Validation Pipeline
STAGE 4: Structure-Preserving Text Extraction (PDF/DOCX/TXT)
STAGE 5: Page-Aware Chunking & Metadata Preservation
STAGE 6: Dense Multilingual Embedding Generation (E5-Small)
STAGE 7: ChromaDB Vector Indexing & Cross-Lingual Search
STAGE 8: Context-Grounded RAG Generation Engine
STAGE 9: Deterministic Citation Attribution & Negative Fallback
STAGE 10: Multilingual & Code-Mixed Processing (EN -> HI -> KN -> TE -> Romanized)
STAGE 11: Categorized Telemetry Event Logging (JSONL Engine)
STAGE 12: Apache Spark (PySpark) Batch ETL & Aggregations
STAGE 13: Admin Analytics Dashboard & Visual KPI Rendering
STAGE 14: Automated Evaluation Harness & Benchmarking
STAGE 15: Security Hardening & Input Sanitization
STAGE 16: Local Deployment Packaging & Configuration Hardening
STAGE 17: Academic Documentation, Thesis Report & Defense Audit
```

---

## 2. Detailed Work Breakdown Structure (Stages 1 to 17)

| Stage ID | Stage Title | Core Technical Deliverables | Exit / Verification Criteria |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Architecture & Environment Setup** | Define API contracts, directory scaffolding, Python 3.10+ virtual env, PyTorch CPU, Java 11/17 runtime validation script (`verify_environment.py`). | `verify_environment.py` passes all checks with 0 errors. |
| **Stage 2** | **Database Foundation** | SQLite schema setup (`documents`, `chunks_metadata`, `telemetry_cache`, `admin_users`) using SQLAlchemy/aiosqlite. | CRUD unit tests pass for document tracking. |
| **Stage 3** | **Document Upload & Ingestion** | Multipart upload endpoint, file size validation (15 MB), SHA-256 deduplication, category assignment. | Uploads validated and stored with UUID filenames. |
| **Stage 4** | **Text Extraction Engine** | PyMuPDF page-by-page extraction for PDFs, `python-docx` for Word docs, UTF-8 text normalizer. | Extracts text with 100% page boundary retention. |
| **Stage 5** | **Page-Aware Chunking** | Recursive character sliding-window chunker (500–700 chars, 100 overlap) embedding `doc_id`, `page_number`, `chunk_index`. | Verified metadata attached to every generated chunk. |
| **Stage 6** | **Dense Embedding Pipeline** | Integration of `intfloat/multilingual-e5-small` CPU vectorizer with query/passage task prefix formatting. | Generates normalized 384-dim embeddings on CPU. |
| **Stage 7** | **Vector Store Indexing & Search** | Persistent ChromaDB collection (`institutional_documents_v1`), cosine similarity search, soft-deactivation filtering. | ANN search returns relevant chunks in $\le 150\text{ ms}$. |
| **Stage 8** | **Grounded RAG Generation** | Decoupled `LLMProvider` (Gemini Flash default, Ollama fallback), evidence-gated system prompts forbidding ungrounded claims. | Synthesizes answers strictly using retrieved context. |
| **Stage 9** | **Citations & Negative Fallback** | Deterministic citation parser `[Doc, Page]`, similarity threshold gating ($\tau$), explicit *"Information Not Found"* fallback. | 100% rejection on unanswerable negative queries. |
| **Stage 10** | **Multilingual & Code-Mixed QA**| Staged rollout: (1) English, (2) Hindi, (3) Kannada, (4) Telugu (Evaluation), (5) Romanized Kanglish/Hinglish subword matching. | Multi-language QA operational with localized text. |
| **Stage 11** | **Categorized Telemetry Logging**| Asynchronous JSONL event logger capturing `REAL_APPLICATION`, `SYNTHETIC_SIMULATION`, `EVALUATION`, and `ERROR` events. | Logs written without blocking FastAPI async loop. |
| **Stage 12** | **PySpark Big Data Analytics** | Distributed PySpark aggregation job computing language share, knowledge gaps, top circulars, and latency percentiles. | Spark job processes 50,000 events in $\le 12\text{ s}$ in `local[*]`. |
| **Stage 13** | **Admin Analytics Dashboard** | Web dashboard rendering Chart.js graphs from cached Spark outputs with explicit synthetic/real data filters. | Dashboard loads in $<5\text{ ms}$ with live charts. |
| **Stage 14** | **Automated Evaluation Harness**| `run_evaluation_benchmark.py` running 60 golden test queries, computing HitRate@K, MRR@K, Faithfulness, and Latency. | Generates verifiable LaTeX/Markdown report tables. |
| **Stage 15** | **Security Hardening** | Admin authentication (PBKDF2 session tokens), path traversal protection, input sanitization against prompt injection. | Security audit passes with zero token leaks. |
| **Stage 16** | **Deployment Packaging** | `.env.example`, launch scripts (`start_server.sh`, `run_analytics.sh`), local offline mode verification. | Clean one-command startup on fresh machine. |
| **Stage 17** | **Documentation & Defense Audit** | Complete MCA Project Report / Thesis (Chapters 1–7), user manuals, demonstration test scripts, slide deck. | Peer review and academic guide approval. |

---

## 3. Critical Stage Dependencies

```
[Stage 1: Env & Scaffolding] ──► [Stage 2: Database] ──► [Stage 3: Ingestion]
                                                               │
                                                               ▼
[Stage 6: Embeddings] ◄── [Stage 5: Chunking] ◄── [Stage 4: Extraction]
       │
       ▼
[Stage 7: Vector Store] ──► [Stage 8: RAG Engine] ──► [Stage 9: Citations & Fallback]
                                                            │
                                                            ▼
[Stage 12: PySpark ETL] ◄── [Stage 11: Telemetry] ◄── [Stage 10: Multilingual]
       │
       ▼
[Stage 13: Dashboard] ──► [Stage 14: Evaluation] ──► [Stage 15: Security]
                                                            │
                                                            ▼
                              [Stage 16: Deployment] ──► [Stage 17: Thesis & Audit]
```

> [!NOTE]
> Completion of Stage 17 establishes the baseline project defense package. Maintenance, logging inspection, and incremental document updates remain an active lifecycle process during institutional deployment.
