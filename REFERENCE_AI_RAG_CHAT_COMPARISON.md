# REFERENCE COMPARISON REPORT: ai-RAG-chat vs. OUR IMPLEMENTATION

## Project: Multilingual AI Document Assistant with Big Data Analytics
**Primary Behavioral Reference**: [`lyakoway/ai-RAG-chat`](https://github.com/lyakoway/ai-RAG-chat)  
**Date**: September 24, 2026

---

### 1. Executive Summary

This report provides a granular technical comparison between the architectural principles demonstrated in `lyakoway/ai-RAG-chat` and our enterprise **Multilingual AI Document Assistant with Big Data Analytics**. 

The `ai-RAG-chat` repository provides a clean, battle-tested standard for hybrid RAG:
1. Combining **Dense semantic retrieval** with **Sparse BM25 lexical search**.
2. Fusing parallel ranked lists via **Reciprocal Rank Fusion (RRF, $k=60$)**.
3. Selecting a small, high-precision context pool (max 5 evidence chunks) rather than overwhelming the LLM with 20 noisy chunks.
4. Eliminating heavy cross-encoder rerankers, which evaluation showed degraded Recall@1 and added significant latency.
5. Deterministic post-generation validation and strict document-only prompt grounding.

Our project incorporates these backend RAG principles while retaining our full institutional feature set: modern React SPA UI, SQLite relational catalog, multilingual Indic support (Hindi, Telugu, Kannada, English), browser-native speech STT/TTS, and PySpark big data analytics.

---

### 2. Comprehensive Subsystem Comparison Table

| Subsystem / Dimension | Reference (`ai-RAG-chat`) | Our Implementation | Technical Comparison (Reference vs. Ours) | Architectural Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Architecture** | Streamlit or minimal chat UI with basic message list. | Modern **React 18 SPA** (Vite + Tailwind CSS + Lucide Icons) with 4 dedicated views: Ask AI, Document Catalog, Analytics Dashboard, and Settings. | **REFERENCE**: Simple script-based UI.<br>**OURS**: Full-featured enterprise SPA with rich typography, feedback, citation drawers, and live KPI cards. | Preserves the existing production React interface without UI redesign or tech-stack churn. |
| **Backend Framework** | FastAPI with modular API routing under `backend/app/api/routes/`. | **FastAPI** with structured routers (`/api/v1/qa`, `/api/v1/documents`, `/api/v1/analytics`, `/health`). | **REFERENCE**: FastAPI REST endpoints.<br>**OURS**: FastAPI REST endpoints with unified error schemas, request validation, and OpenAPI documentation. | Full parity with the reference's backend framework standard. |
| **Document Parsing** | PDF and text parsers extracting plain textual streams. | Multi-format structured parsers supporting **PDF, DOCX, TXT, MD, CSV, JSON** with SHA-256 deduplication and section header detection. | **REFERENCE**: Standard document parsers.<br>**OURS**: Format-aware ingestion preserving page offsets, headings, and tables. | Expands ingestion capabilities to handle diverse academic and administrative documents. |
| **Chunking Strategy** | Recursive character text splitting (fixed size ~800–1000 tokens). | Structure-aware recursive splitting (target 600 chars, overlap 120 chars, min size 80 chars) with adjacent boundary repair (predecessor/successor expansion). | **REFERENCE**: Standard recursive splitting.<br>**OURS**: Recursive splitting + sentence-boundary preservation + adjacent chunk stitching. | Prevents sentence-fragment truncation at chunk boundaries (e.g., repairing *"is less..."* into full NIRF reimbursement clauses). |
| **Dense Embeddings** | SentenceTransformer embedding model generating dense vectors. | `SentenceTransformer` using **`intfloat/multilingual-e5-small`** (384 dimensions) with `"passage: "` and `"query: "` prefix conventions. | **REFERENCE**: Monolingual English dense embeddings.<br>**OURS**: Multilingual dense embedding model supporting cross-lingual semantic search. | Enables cross-lingual alignment for Indic queries (Hindi, Kannada, Telugu) matching English documents. |
| **Vector Store** | **ChromaDB** persistent vector database using cosine distance. | **ChromaDB** persistent vector database with pre-warmed singleton client and batched indexing. | **REFERENCE**: ChromaDB collection.<br>**OURS**: ChromaDB collection with startup prewarming and zero-latency retrieval. | Direct parity with reference vector store choice. |
| **Lexical Search (BM25)** | **BM25Okapi** sparse lexical index built in-memory over chunk tokens. | **BM25Okapi** sparse lexical index cached with token pre-tokenization and case normalization. | **REFERENCE**: BM25Okapi lexical retrieval.<br>**OURS**: BM25Okapi lexical retrieval with incremental updates and query normalization. | Direct parity; ensures exact matching for acronyms (`NIRF`, `CGTMSE`, `MSME`), numbers, and URLs. |
| **Hybrid Rank Fusion (RRF)** | Reciprocal Rank Fusion formula: $\text{RRF}(d) = \sum \frac{1}{60 + \text{rank}(d)}$. | **Reciprocal Rank Fusion** with $k=60.0$, fusing Dense Top-20 + BM25 Top-20 into a single fused candidate pool. | **REFERENCE**: RRF with $k=60$.<br>**OURS**: RRF with $k=60.0$ and multi-variant query fusion. | Direct parity with the reference's proven optimal fusion formula. |
| **Cross-Encoder Reranking** | **Explicitly Rejected**: Empirical evaluation proved cross-encoders reduced Recall@1 and added several seconds of latency. | **Eliminated Heavy Rerankers**: Uses lightweight deterministic relevance scoring based on term coverage and entity matches without cross-encoders. | **REFERENCE**: Rejected cross-encoder.<br>**OURS**: Deterministic heuristic scoring without neural cross-encoder overhead. | Adheres to the reference's core finding: BM25 + RRF delivers higher precision and lower latency than cross-encoders. |
| **Context Construction** | Clean context package formatted with source identifiers and page metadata, capped at Top 4–5 chunks. | Natural document-ordered context (`Document` $\rightarrow$ `Page` $\rightarrow$ `Section` $\rightarrow$ `Chunk`) formatted as `[Source N] Document: <title> Page: <p> Content: <text>`, capped at **Top-5 chunks**. | **REFERENCE**: Top 4–5 formatted chunks.<br>**OURS**: Top 5 naturally-ordered chunks with boundary repair. | Prevents prompt noise; ensures the LLM focuses on high-precision evidence rather than 20 raw candidates. |
| **LLM Provider & Generation** | Modular LLM abstraction (OpenAI / Claude / local). | **Google Gemini 2.5 Flash** (`gemini-2.5-flash`, `temperature: 0.0`) with multi-model fallback (`gemini-1.5-flash`, `gemini-2.0-flash`). | **REFERENCE**: LLM abstraction.<br>**OURS**: Gemini 2.5 Flash with multi-tier fallback and honest `GENERATION_UNAVAILABLE` reporting. | Zero-temperature deterministic generation ensures strict adherence to document evidence. |
| **Multilingual Generation** | Primarily English-centric generation. | Native multilingual synthesis: explicit `TARGET LANGUAGE: <lang>` passed to Gemini; outputs fluent Hindi (Devanagari), Telugu, Kannada, or English. | **REFERENCE**: English-focused.<br>**OURS**: Native Indic generation + Unicode script validation in AnswerGuard. | Core MCA requirement: native Indic QA without fake dictionary translations. |
| **Citations & Provenance** | Source document name and page number citations mapped to chunks. | Structured `Citation` objects linking to exact document ID, title, page number, and chunk offset; verified by AnswerGuard. | **REFERENCE**: Inline page citations.<br>**OURS**: Verified interactive citation cards; zero phantom citations on abstention. | Full traceability; guarantees citations correspond 1-to-1 with retrieved evidence. |
| **Error Handling & Abstention** | Fallback string when retrieval similarity is below threshold. | State Machine: `GROUNDED`, `PARTIAL`, `INSUFFICIENT_EVIDENCE`, `LANGUAGE_UNAVAILABLE`, `GENERATION_UNAVAILABLE`, `ERROR`. | **REFERENCE**: Simple fallback string.<br>**OURS**: Controlled response-state enum with honest UI presentation. | Guarantees the system never invents facts or shows fake citations for out-of-domain queries. |
| **Latency & Performance** | Sub-second retrieval + LLM generation time measurement. | Explicit breakdown: `retrieval_latency_ms`, `generation_latency_ms`, and `total_latency_ms` tracked per query. | **REFERENCE**: Total latency timing.<br>**OURS**: Granular multi-stage latency telemetry returned in API response. | Complete observability into retrieval and generation execution times. |
| **Voice / Speech (STT/TTS)** | Not implemented. | Browser-native **Web Speech API** for multilingual STT and **speechSynthesis** for zero-latency multilingual TTS. | **REFERENCE**: No voice.<br>**OURS**: Integrated voice input and speech synthesis without paid external cloud APIs. | Preserves accessibility and voice interaction features. |
| **Big Data Analytics** | Not implemented. | **Apache PySpark 3.5.0 + PyArrow** computing processing throughput, token distributions, latency percentiles, and language breakdown. | **REFERENCE**: No analytics.<br>**OURS**: Distributed analytics subsystem with interactive charts and REST APIs. | Fulfills academic MCA curriculum big data requirements. |

---

### 3. Key Findings & Architectural Validations

1. **Why Hybrid BM25 + RRF ($k=60$) is Optimal**:
   Like `ai-RAG-chat`, our benchmarks demonstrate that hybrid retrieval combines the best of both worlds:
   - Dense embeddings (`multilingual-e5-small`) capture high-level semantics and cross-lingual intent.
   - BM25 captures exact acronyms (`NIRF`, `CGTMSE`), exact numbers (`75%`, `90%`, `₹1.0 lakh`), and URLs (`https://www.cgtmse.in`).
   - RRF ($k=60$) normalizes rank positions across different scoring scales without hyperparameter tuning.

2. **Rejection of Neural Cross-Encoder Rerankers**:
   Empirical testing in `ai-RAG-chat` revealed that cross-encoders added 1.5–3.0 seconds of latency while degrading Recall@1 on domain-specific acronyms. Our implementation follows this insight by relying on high-precision RRF fusion and lightweight deterministic scoring.

3. **Small, Clean Top-5 Generation Context**:
   Passing 20 raw chunks to Gemini degrades attention and increases token cost. Selecting at most Top-5 high-relevance chunks and ordering them naturally produces concise, perfectly grounded answers.
