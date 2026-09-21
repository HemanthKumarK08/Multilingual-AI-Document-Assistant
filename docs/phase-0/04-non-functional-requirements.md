# Non-Functional Requirements Specification

This document defines the quality attributes, operational limits, performance benchmarks, and architectural constraints for the **Multilingual AI Document Assistant with Big Data Analytics**.

---

## 1. Performance Requirements (Proposed Targets)

> [!NOTE]
> All latency and throughput metrics listed below represent **proposed design targets** derived from preliminary baseline benchmarks on a 4-core to 8-core CPU student laptop. Final verified values will be measured and documented during Phase 5 empirical benchmarking.

| ID | Pipeline Stage / Metric | Proposed Target (p50) | Proposed Target (p95) | Testing Methodology & Conditions |
| :--- | :--- | :---: | :---: | :--- |
| **NFR-PERF-01a** | **Query Preprocessing & Language Tagging** | $\le 20\text{ ms}$ | $\le 50\text{ ms}$ | Unicode normalization, script detection, and task prefix formatting. |
| **NFR-PERF-01b** | **Query Dense Embedding Generation** | $\le 60\text{ ms}$ | $\le 120\text{ ms}$ | CPU forward pass using `intfloat/multilingual-e5-small` on single query. |
| **NFR-PERF-01c** | **Vector Similarity Search (ChromaDB)** | $\le 50\text{ ms}$ | $\le 150\text{ ms}$ | Approximate Nearest Neighbor / Cosine search over 5,000 indexed chunks. |
| **NFR-PERF-01d** | **Context Formatting & Prompt Assembly** | $\le 10\text{ ms}$ | $\le 25\text{ ms}$ | Extraction thresholding ($\tau$), metadata deduplication, and system prompt formatting. |
| **NFR-PERF-01e** | **LLM Response Generation (Hosted API)** | $\le 1.5\text{ s}$ | $\le 3.0\text{ s}$ | Network roundtrip + token generation using Google Gemini 1.5 Flash / Groq. |
| **NFR-PERF-01f** | **LLM Response Generation (Local CPU Ollama)**| $\le 6.0\text{ s}$ | $\le 10.0\text{ s}$ | 4-bit quantized local model inference (Llama-3.2-3B) on CPU. |
| **NFR-PERF-02a** | **Total End-to-End Response Latency (API Mode)**| $\le 2.0\text{ s}$ | $\le 3.5\text{ s}$ | Complete request-response lifecycle from query submit to UI render. |
| **NFR-PERF-02b** | **Total End-to-End Latency (Local CPU Mode)** | $\le 7.0\text{ s}$ | $\le 12.0\text{ s}$ | Offline local CPU inference mode lifecycle. |
| **NFR-PERF-03** | **Document Ingestion Throughput** | $\ge 2.0\text{ pages/s}$ | $\ge 1.0\text{ pages/s}$ | PyMuPDF text extraction, chunking, and embedding generation. |
| **NFR-PERF-04** | **PySpark Batch Telemetry Execution** | $\le 12.0\text{ s}$ | $\le 20.0\text{ s}$ | Full distributed batch aggregation on 50,000 JSONL records in `local[*]`. |

---

## 2. Scalability Requirements

| ID | Parameter | Target Limit | Description |
| :--- | :--- | :--- | :--- |
| **NFR-SCAL-01** | **Vector Store Capacity** | Up to $10,000\text{ chunks}$ ($\approx 500\text{ document pages}$) | Must operate seamlessly in embedded/local vector storage without memory overflow. |
| **NFR-SCAL-02** | **Telemetry Log Handling** | Scales to $>500,000\text{ log events}$ | PySpark job must process partitioned JSON Lines logs without single-node memory saturation. |
| **NFR-SCAL-03** | **Document Collection Scaling** | Up to $100\text{ distinct institutional files}$ | System must maintain constant retrieval latency regardless of file count distribution. |

---

## 3. Reliability & Fault Tolerance Requirements

| ID | Parameter | Requirement |
| :--- | :--- | :--- |
| **NFR-REL-01** | **Graceful Ingestion Failure** | If a single PDF contains corrupt pages, the extraction pipeline must log the error, isolate the failure, and continue processing valid pages without crashing the backend service. |
| **NFR-REL-02** | **API / LLM Fallback Resilience** | If external LLM API experiences network timeout or rate limiting (HTTP 429/500), the backend must retry with exponential backoff (max 2 retries) or display a clean user-friendly notification. |
| **NFR-REL-03** | **Vector Store Index Persistence** | The vector database and document metadata database must be durably persisted to disk after every write operation, preventing index loss upon application restart. |

---

## 4. Maintainability & Code Quality Requirements

| ID | Parameter | Requirement |
| :--- | :--- | :--- |
| **NFR-MAIN-01** | **Modular Decoupling** | Document Ingestion, Vector Search, LLM Generation, and PySpark Analytics must exist as decoupled Python modules with typed dataclass/Pydantic schemas. |
| **NFR-MAIN-02** | **Independent Analytics Execution** | The PySpark analytics pipeline must be executable both as a standalone batch script (`python -m analytics.run_spark_job`) and as a triggerable service from the admin dashboard. |
| **NFR-MAIN-03** | **Clean Configuration Architecture** | All hyperparameters (chunk size, overlap, similarity threshold $\tau$, model names, log paths) must be configurable via `.env` or `config.yaml` without editing source code. |

---

## 5. Usability & Explainability Requirements

| ID | Parameter | Requirement |
| :--- | :--- | :--- |
| **NFR-USE-01** | **Citation Transparency** | Every factual claim in an answer must display an inline or footer citation referencing `[Document Name, Page Number]`. |
| **NFR-USE-02** | **Auditable Source Drawer** | Clicking a citation badge must open a slide-over/modal showing the verbatim raw text chunk retrieved from the document. |
| **NFR-USE-03** | **Linguistic Accessibility** | The UI interface must render native Indic scripts (Kannada, Telugu, Devanagari) cleanly using standard UTF-8 fonts with zero character clipping. |
| **NFR-USE-04** | **Unambiguous Negative Response** | When the system cannot find verified information, it must explicitly state that the answer is absent rather than providing ambiguous hints. |

---

## 6. Security & Privacy Requirements

| ID | Parameter | Requirement |
| :--- | :--- | :--- |
| **NFR-SEC-01** | **Strict Upload Boundary & Sanitization** | Restrict file uploads to `.pdf`, `.docx`, `.txt`. Reject executable payloads, embedded macros, and enforce random UUID naming to prevent path traversal attacks (`../../etc/passwd`). |
| **NFR-SEC-02** | **Admin Access Protection** | Protect document upload and administrative analytics endpoints using a secure bearer token or session passkey. |
| **NFR-SEC-03** | **Local Data Isolation** | Uploaded institutional documents and vector embeddings must remain in local application storage, never submitted to public indexing pools. |

---

## 7. Resource Efficiency & Hardware Portability

| ID | Parameter | Requirement Target |
| :--- | :--- | :--- |
| **NFR-RES-01** | **RAM Footprint (Standard Mode)** | $\le 4.5\text{ GB}$ peak memory consumption running backend, vector store, embedding model, and frontend simultaneously on a student laptop. |
| **NFR-RES-02** | **CPU-Only Execution** | All core embedding, search, and data processing operations must execute efficiently on standard x86_64 / ARM64 multi-core CPUs without requiring a CUDA-compatible GPU. |
| **NFR-RES-03** | **Disk Storage Footprint** | Complete application code, embedding model cache, vector store, and 50 document files must consume $\le 4.0\text{ GB}$ disk space. |

---

## 8. Summary Checklist of Non-Functional Constraints

- [x] Tested against typical student hardware limits (8GB/16GB RAM, no discrete GPU required).
- [x] Measurable latency bounds defined for retrieval, generation, and analytics.
- [x] Zero-data-loss persistence guarantees for SQLite and vector store indexes.
- [x] Full UTF-8 Indic script rendering compliance across all UI components.
