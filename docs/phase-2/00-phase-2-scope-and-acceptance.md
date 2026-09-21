# Phase 2 — Scope, Objectives, and Acceptance Criteria

## 1. Executive Summary

This document defines the architectural boundaries, functional objectives, and acceptance criteria for **Phase 2: Document Ingestion and Preprocessing Pipeline** (encompassing WBS **Stage 3** and **Stage 4**) of the **Multilingual AI Document Assistant with Big Data Analytics**.

Phase 2 establishes the end-to-end ingestion pipeline responsible for reading raw institutional circulars, parsing multi-format documents (`PDF`, `DOCX`, `TXT`, `MD`), extracting structural elements (pages, headings, tables), performing deterministic Unicode normalization, detecting script and language metadata, computing streaming SHA-256 digests for deduplication, and tracking job lifecycles in the SQLite database.

---

## 2. In-Scope vs. Explicitly Out-of-Scope Capabilities

### In-Scope (Phase 2 Responsibilities):
- **Multi-Format Parsers:** Modular parsers for PDF (`PyMuPDF`), DOCX (`python-docx`), and plain text/markdown (`UTF-8`, `UTF-8 BOM`).
- **Structure & Page Preservation:** 1-indexed page boundaries for PDFs, logical paragraph/section boundaries for flowable documents, heading style detection (`Heading 1/2/3`), and table serialization (`[TABLE]...[/TABLE]`).
- **Deterministic Normalization:** Unicode NFC normalization, newline unification (`\r\n` -> `\n`), unsafe control character removal, whitespace collapsing without semantic modification.
- **Script & Language Identification:** CPU-first Unicode range analyzer detecting `devanagari`, `kannada`, `telugu`, `latin`, and `mixed` scripts with language inference (`en`, `hi`, `kn`, `te`).
- **Cryptographic Deduplication:** Streaming SHA-256 calculation to enforce database uniqueness constraints and prevent duplicate ingestion.
- **Job Lifecycle Tracking:** Creation and state management of `DocumentProcessingJob` (`running` -> `completed` / `failed`).
- **Intermediate Artifact Generation:** Saving structured JSON representations of parsed documents in `data/processed/`.
- **FastAPI Ingestion Endpoint:** `POST /api/v1/documents/ingest`.

### Explicitly Out-of-Scope (Deferred to Future Phases):
- **Chunking (Phase 3):** Recursive character chunking, sliding-window chunking, token counting.
- **Embeddings & Vector Store (Phase 4):** Sentence Transformers, PyTorch vectorization, ChromaDB collection indexing.
- **Retrieval & Grounded RAG (Phase 5):** BM25 sparse search, Gemini API / Ollama generation, citation generation.
- **Speech & OCR (Phase 6 / Deferred):** Scanned image OCR, Speech-to-Text, Text-to-Speech.
- **Big Data Analytics (Phase 7):** Apache Spark batch jobs, telemetry aggregation.
- **Web UI (Phase 8):** Dashboard interface and interactive charts.

---

## 3. Acceptance Criteria Checklist

| Criterion | Target Requirement | Status |
| :--- | :--- | :---: |
| **Independent Parsers** | PDF, DOCX, TXT parsers function statelessly and adhere to common `BaseParser` interface | **PASS** |
| **Page Boundaries** | 1-indexed page numbers preserved for multi-page PDFs | **PASS** |
| **Heading Hierarchy** | Heading styles and nearest preceding section context extracted | **PASS** |
| **Table Preservation** | Tables serialized into deterministic bracketed format (`[TABLE]...[/TABLE]`) | **PASS** |
| **Unicode & Script Safety**| Devanagari, Kannada, and Telugu scripts preserved without corruption or stemming | **PASS** |
| **Deduplication** | Streaming SHA-256 rejects duplicate content with distinct filenames | **PASS** |
| **Job State Tracking** | `DocumentProcessingJob` records transition atomically (`running` -> `completed`/`failed`) | **PASS** |
| **Transaction Safety** | Database rollbacks prevent partial document state on parser failures | **PASS** |
| **Corpus Processing** | All 24 documents in `data/raw/` parsed, normalized, and logged with 0 failures | **PASS** |
| **Automated Tests** | 100% test pass rate (34/34 tests passing in `pytest tests/ -v`) | **PASS** |
