# Phase 3 — Metadata and Provenance Contract

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.chunking.models.DocumentChunk`

---

## 1. Provenance Schema Specification

Every generated chunk contains a comprehensive 20-field provenance record ensuring end-to-end traceability from the final retrieved chunk back to the exact source file, physical page, and character offset.

| # | Field Name | Type | Description | Example Value |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `chunk_id` | `str` | Deterministic stable chunk identifier | `"DOC-ACAD-001:p1:c0"` |
| 2 | `doc_id` | `str` | Canonical institutional document identifier | `"DOC-ACAD-001"` |
| 3 | `file_hash_sha256` | `str` | Cryptographic SHA256 checksum of raw source | `"c33d25bc8e2c17b8..."` |
| 4 | `filename` | `str` | Original file name on disk | `"DOC-ACAD-001.txt"` |
| 5 | `category` | `str` | Institutional document category | `"academic_regulations"` |
| 6 | `language` | `str` | ISO 639-1 language code | `"en"` |
| 7 | `script` | `str` | Detected script family | `"latin"` / `"devanagari"` |
| 8 | `page_number` | `int` | 1-indexed physical or logical page number | `1` |
| 9 | `section_title` | `Optional[str]` | Nearest preceding structural heading | `"Introduction / Overview"` |
| 10 | `heading_level` | `Optional[int]` | Heading hierarchy level (1–6) | `1` |
| 11 | `chunk_index` | `int` | 0-indexed document-global sequential index | `0` |
| 12 | `text_content` | `str` | Exact extracted text content of chunk | `"================..."` |
| 13 | `text_length` | `int` | Actual character length of `text_content` | `300` |
| 14 | `source_start_offset`| `int` | Inclusive start offset in source page unit | `0` |
| 15 | `source_end_offset` | `int` | Exclusive end offset in source page unit | `300` |
| 16 | `source_unit_index` | `int` | 0-indexed sequence of source page unit | `0` |
| 17 | `parser_name` | `str` | Ingestion parser responsible for extraction | `"TxtParser"` |
| 18 | `parser_version` | `str` | Version of the ingestion parser | `"1.0.0 (utf8-stream)"` |
| 19 | `version` | `str` | Document revision version | `"1.0"` |
| 20 | `extraction_notes` | `List[str]` | Warnings or OCR anomalies from parsing | `[]` |

---

## 2. Stable Chunk ID Construction

Chunk IDs follow a strict deterministic format:

$$\text{chunk\_id} = \{\text{doc\_id}\}\text{:p}\{\text{page\_number}\}\text{:c}\{\text{chunk\_index}\}$$

### Guarantees
- **Deterministic:** Reprocessing the same document with identical configuration yields identical chunk IDs.
- **Source-Locatable:** Contains the document ID and 1-indexed page number directly in the primary key.
- **Globally Sequential:** `chunk_index` is 0-indexed and monotonically increases from `0` to $N-1$ across the entire document.
- **Path-Independent:** Does not embed absolute host filesystem paths.

---

## 3. Offset and Page Boundary Conventions

1. **Page Boundaries:** Chunks never span across physical PDF page boundaries or logical DOCX/TXT page units.
2. **Offset Indexing:**
   - `source_start_offset`: Inclusive start index relative to the source page unit text.
   - `source_end_offset`: Exclusive end index relative to the source page unit text.
   - Invariant: `source_end_offset - source_start_offset >= text_length` (accounting for separator trimming or whitespace collapsing).
