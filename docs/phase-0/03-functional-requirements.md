# Functional Requirements Specification

This document details the functional capabilities of the **Multilingual AI Document Assistant with Big Data Analytics**. Requirements are prioritized using the **MoSCoW** convention:
- **Must Have (M):** Mandatory for the initial Minimum Viable Product (MVP).
- **Should Have (S):** High priority for the primary academic demonstration.
- **Could Have (C):** Optional enhancement if time and resources permit.
- **Future Scope (F):** Documented architecture extension, deferred past core delivery.

---

## 1. Document Management Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-DOC-001** | **Multi-Format Upload:** The system shall accept digital documents in PDF (`.pdf`), Microsoft Word (`.docx`), and Plain Text (`.txt`) formats via an administrative interface. | **Must Have** |
| **FR-DOC-002** | **File Validation & Safety:** The system shall validate file size (max 15 MB per file), file extension, and MIME type, rejecting unsupported, corrupt, or password-protected files with descriptive error messages. | **Must Have** |
| **FR-DOC-003** | **Document Categorization:** The system shall require the administrator to assign uploaded documents to an institutional category (e.g., *Academic Regulations, Examination, Scholarships, Hostel, Placements, General Notices*). | **Must Have** |
| **FR-DOC-004** | **Document Deduplication:** The system shall compute a cryptographic hash (SHA-256) of uploaded files to detect and reject or warn against duplicate document uploads. | **Should Have** |
| **FR-DOC-005** | **Ingestion Status Tracking:** The system shall maintain and display real-time/granular ingestion states for each document (*Uploaded, Extracting, Chunking, Embedding, Indexed, Failed*). | **Must Have** |
| **FR-DOC-006** | **Document Deactivation & Deletion:** The system shall allow administrators to soft-deactivate or delete a document, immediately removing its associated chunks from the active vector search index. | **Must Have** |
| **FR-DOC-007** | **Document Inventory Listing:** The system shall display a table of all uploaded documents including title, category, upload timestamp, page count, chunk count, and active status. | **Must Have** |
| **FR-DOC-008** | **Scanned PDF OCR Extraction:** The system shall detect scanned image-only PDFs and attempt Optical Character Recognition (OCR via Tesseract/easyOCR). | **Could Have** |

---

## 2. Text Processing & Chunking Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-TXT-001** | **Structure-Aware Text Extraction:** The system shall extract text from digital PDFs while preserving logical page numbers, line breaks, and paragraph boundaries. | **Must Have** |
| **FR-TXT-002** | **Text Normalization:** The system shall clean extracted text by stripping non-printable artifacts, excessive whitespace, and non-standard line breaks while preserving punctuation and Indic Unicode code points. | **Must Have** |
| **FR-TXT-003** | **Page-Aware Chunking:** The system shall segment documents using a recursive character or sentence-aware sliding window (e.g., 500–700 characters with 100-character overlap) while embedding immutable metadata (`doc_id`, `doc_title`, `category`, `page_number`, `chunk_index`) in every chunk. | **Must Have** |
| **FR-TXT-004** | **Language Detection for Ingested Text:** The system shall identify the dominant language of uploaded documents (English, Kannada, Telugu, Hindi) and store it in document metadata. | **Should Have** |
| **FR-TXT-005** | **Table-Aware Extraction:** The system shall detect simple tabular structures in PDFs/DOCX and format them as Markdown or linearized text to prevent semantic disruption during chunking. | **Could Have** |

---### 3. Search and Retrieval Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-RET-001** | **Multilingual Dense Vectorization:** The system shall convert user queries into dense vector embeddings using a pre-trained multilingual embedding model (`intfloat/multilingual-e5-small` / `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`). | **Must Have** |
| **FR-RET-002** | **Semantic Vector Search:** The system shall execute approximate nearest neighbor (ANN) or exact cosine similarity search over indexed chunks to retrieve the Top-$K$ ($K=3$ to $5$) most relevant chunks. | **Must Have** |
| **FR-RET-003** | **Staged Multilingual Retrieval:** The system shall support cross-lingual semantic matching in a phased rollout: (1) English, (2) Hindi, (3) Kannada, (4) Telugu (Staged/Evaluation), and (5) Romanized/Code-Mixed input (Kanglish/Hinglish). | **Must Have (EN/HI/KN), Should Have (TE/Code-Mixed)** |
| **FR-RET-004** | **Relevance Thresholding & Evidence Gating:** The system shall compute similarity confidence scores; if the top chunk similarity falls below an empirical threshold ($\tau$), the retrieval step shall trigger a deterministic information-not-found flow. | **Must Have** |
| **FR-RET-005** | **Category-Filtered Retrieval:** The system shall allow users to optionally restrict semantic search to specific document categories (e.g., "Search only within Hostel Rules"). | **Should Have** |
| **FR-RET-006** | **Index Lifecycle & Deduplication:** The vector store shall support automated document hash checking, document chunk deletion by `doc_id`, soft-deactivation filtering, and full index rebuild from SQLite metadata. | **Must Have** |

---

## 4. Answer Generation & RAG Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-GEN-001** | **Context-Grounded Answering:** The system shall supply retrieved document chunks to the LLM with strict system prompt instructions forbidding the use of external parametric knowledge or ungrounded extrapolation. | **Must Have** |
| **FR-GEN-002** | **Deterministic Fallback on Missing Data:** When retrieved chunks do not contain sufficient evidence or when similarity falls below threshold, the system shall return a clear, deterministic fallback response: *"The requested information is not available in the uploaded institutional documents."* | **Must Have** |
| **FR-GEN-003** | **Granular Source Attribution & Citations:** Every generated response with factual content shall explicitly cite the source document name, category, and exact page number(s) where the evidence appears. | **Must Have** |
| **FR-GEN-004** | **Multilingual Response Synthesis:** The system shall generate responses in the language requested by the user (English, Hindi, Kannada in MVP; Telugu in staged expansion), strictly grounded in the retrieved English source text. | **Must Have** |
| **FR-GEN-005** | **Source Chunk Excerpt Display:** The user interface shall provide an expandable citation drawer allowing users to read the exact raw text chunks used to synthesize the answer. | **Must Have** |
| **FR-GEN-006** | **Configurable LLM Provider Interface:** The LLM generator backend shall be decoupled via configuration (`.env`), supporting Hosted APIs (Gemini 1.5 Flash, Groq) and local offline inference (Ollama). | **Must Have** |

---

## 5. Voice Interaction Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-VOI-001** | **Browser-Based Speech-to-Text (STT):** The system shall support speech input capture using Web Speech API for English and Hindi queries. | **Could Have (Phase 6)** |
| **FR-VOI-002** | **Audio Query Recording & Ingestion:** The system shall allow microphone audio capture, converting spoken input into text prior to vector retrieval. | **Could Have (Phase 6)** |
| **FR-VOI-003** | **Text-to-Speech (TTS) Response Audio:** The system shall synthesize and play audio versions of generated text responses using standard browser synthesis. | **Could Have (Phase 6)** |
| **FR-VOI-004** | **Regional Dialect & Code-Mixed STT:** Real-time speech recognition for mixed Kannada-English / Telugu-English spoken vernaculars. | **Future Scope** |

---

## 6. Big Data & Analytics Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-ANA-001** | **Categorized Telemetry Event Logging:** The system shall log interaction events into 4 distinct categories (`REAL_APPLICATION`, `SYNTHETIC_SIMULATION`, `EVALUATION_BENCHMARK`, `ERROR_DIAGNOSTIC`), storing `query_id`, `timestamp`, `telemetry_source`, `raw_query_text`, `detected_language`, `category`, `top_similarity_score`, `retrieval_latency_ms`, `llm_latency_ms`, `is_fallback`, `user_feedback`. | **Must Have** |
| **FR-ANA-002** | **Document Processing Telemetry:** The system shall record document lifecycle events: `doc_id`, `filename`, `file_size_bytes`, `page_count`, `chunk_count`, `extraction_time_ms`, `embedding_time_ms`, `status`. | **Must Have** |
| **FR-ANA-003** | **PySpark Batch Aggregation Engine:** The system shall execute PySpark data processing jobs in `local[*]` mode to ingest partitioned JSONL logs and compute institutional intelligence metrics. | **Must Have** |
| **FR-ANA-004** | **Language & Intent Distribution Analytics:** The PySpark job shall aggregate query volume segmented by language (English, Hindi, Kannada, Telugu, Code-Mixed) and document category over time windows. | **Must Have** |
| **FR-ANA-005** | **Knowledge Gap & Unanswered Query Clustering:** The PySpark job shall aggregate queries resulting in "Information Not Found" fallbacks or low similarity scores, identifying missing policy areas. | **Must Have** |
| **FR-ANA-006** | **Latency & Performance Profiling:** The PySpark job shall compute p50, p90, and p95 latency percentiles for vector search and generation across load conditions. | **Should Have** |
| **FR-ANA-007** | **Interactive Analytics Dashboard with Data Provenance:** The administrative interface shall visualize PySpark aggregate metrics using charts and summary tables, with clear labels distinguishing real usage from synthetic simulation data. | **Must Have** |

---

## 7. Administration and Security Requirements

| Requirement ID | Description | Priority |
| :--- | :--- | :---: |
| **FR-SEC-001** | **Administrator Authentication:** The system shall secure admin routes (`/admin/*`, upload, index rebuild, analytics trigger) using HTTP Basic Auth or Bearer session tokens backed by PBKDF2 password hashing. | **Must Have** |
| **FR-SEC-002** | **Public Student Access Boundary:** The student QA interface shall remain publicly accessible (read-only) without requiring user registration or credential storage. | **Must Have** |
| **FR-SEC-003** | **Input Sanitization:** The system shall sanitize all text query inputs to mitigate prompt injection attacks and formatting exploits. | **Must Have** |
| **FR-SEC-004** | **Secure Local File Storage:** Uploaded files shall be stored in an isolated, non-executable directory with sanitized unique UUID filenames to prevent path traversal. | **Must Have** |
| **FR-SEC-005** | **API Key & Secret Masking:** All external LLM credentials and database configurations shall be loaded strictly via environment variables (`.env`), never exposed in client payloads or git commits. | **Must Have** |
