# Phase 2.1 — Ingestion Pipeline Architecture

## 1. Architectural Overview

The Document Ingestion Pipeline operates as a core subsystem within the modular monolith architecture of the **Multilingual AI Document Assistant**. It decouples file validation, parsing, normalization, language detection, and database state management into testable, single-responsibility components.

```
[Uploaded File / Raw Corpus File]
                │
                ▼
   ┌──────────────────────────┐
   │   IngestionCoordinator   │ ◄── File Existence, Size & Type Validation
   └────────────┬─────────────┘
                │ (Compute Streaming SHA-256)
                ├─────────────────────────────► [Check SQLite Duplicates]
                │                                       │ (Duplicate Detected)
                │                                       ▼
                │                          Return IngestionResult(DUPLICATE)
                │
                ▼ (Unique File Verified)
   ┌──────────────────────────┐
   │ Create Processing Job    │ ◄── DocumentProcessingJob (status: running)
   └────────────┬─────────────┘
                │
                ▼ (Resolve by Extension)
   ┌──────────────────────────┐
   │      ParserRegistry      │
   └────────────┬─────────────┘
                ├──────────────────────┬──────────────────────┐
                ▼                      ▼                      ▼
        ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
        │PyMuPDFParser │       │  DocxParser  │       │  TxtParser   │
        │  (.pdf)      │       │  (.docx)     │       │  (.txt, .md) │
        └───────┬──────┘       └───────┬──────┘       └───────┬──────┘
                │                      │                      │
                └──────────────────────┼──────────────────────┘
                                       │
                                       ▼ (Parsed Intermediate Document)
                        ┌──────────────────────────────┐
                        │    Text Normalization        │ ◄── Unicode NFC, LF unification,
                        │    & Script Detection        │     Devanagari/Kannada/Telugu
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │   Persistence & Artifacts    │
                        ├──────────────────────────────┤
                        │ 1. Update Document (PARSED)  │
                        │ 2. Save JSON to processed/   │
                        │ 3. Update Job (COMPLETED)    │
                        │ 4. Commit DB Transaction     │
                        └──────────────────────────────┘
```

---

## 2. Component Directory Structure

The ingestion subsystem is packaged under `app/services/ingestion/`:

```text
app/services/ingestion/
├── __init__.py           # Public exports (coordinator, models, hashing, normalization)
├── constants.py          # Extensions, MIME types, size thresholds, status enums
├── exceptions.py         # Typed exceptions (IngestionError, DuplicateDocumentError, etc.)
├── models.py             # Pydantic models (ParsedDocument, ExtractedPage, IngestionResult)
├── hashing.py            # Streaming 64 KB SHA-256 hash generator
├── normalization.py      # Unicode NFC, control char removal, whitespace normalization
├── language.py           # Unicode script frequency and language detection
├── coordinator.py        # IngestionCoordinator orchestrating the complete workflow
└── parsers/
    ├── __init__.py       # Parser exports and default registry instance
    ├── base.py           # BaseParser abstract base interface
    ├── pdf.py            # PyMuPDF parser with page, heading, and table extraction
    ├── docx.py           # python-docx parser with heading styles and tables
    ├── txt.py            # Plain text and Markdown parser with UTF-8 BOM handling
    └── registry.py       # ParserRegistry mapping extensions to parser instances
```

---

## 3. Design Principles and Guardrails

1. **Stateless Parsers:** Parsers never execute SQL queries or commit database sessions. They accept file paths and return a rich, validated `ParsedDocument` intermediate representation.
2. **Deterministic Processing:** All hash calculations, Unicode normalizations, and table formatting routines produce bitwise-identical output across repeated invocations.
3. **Graceful Degradation:** Malformed pages or low-confidence language detection trigger structured warnings (`ExtractionWarning`) rather than crashing the batch process.
4. **Zero Heavy ML Overhead:** Uses deterministic Unicode block frequency analysis and standard-library modules without downloading neural models or spawning background worker daemons.
