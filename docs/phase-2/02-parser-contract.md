# Phase 2.2 — Multi-Format Parser Contract & Specification

## 1. Abstract Parser Interface (`BaseParser`)

All file format parsers inherit from [`app/services/ingestion/parsers/base.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/app/services/ingestion/parsers/base.py):

```python
class BaseParser(abc.ABC):
    @property
    @abc.abstractmethod
    def parser_name(self) -> str:
        """Name of the parser implementation."""
        pass

    @property
    @abc.abstractmethod
    def parser_version(self) -> str:
        """Semantic version of the parser."""
        pass

    @property
    @abc.abstractmethod
    def supported_extensions(self) -> set[str]:
        """Set of file extensions handled by this parser (e.g. {'.pdf'})."""
        pass

    @abc.abstractmethod
    def parse(
        self,
        file_path: str | pathlib.Path,
        doc_id: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ParsedDocument:
        """Parses a file from disk and returns a structured ParsedDocument."""
        pass
```

---

## 2. Format-Specific Parser Implementations

### 2.1 PyMuPDF PDF Parser (`PyMuPDFParser`)
- **Engine:** PyMuPDF (`fitz` 1.24+)
- **Supported Extensions:** `.pdf`
- **Page Boundary Preservation:** Iterates through `doc` pages and sets `page_number = page.number + 1` (1-indexed).
- **Heading Detection:** Evaluates standalone text blocks matching numbered section patterns (`\d+\.\d+`), uppercase titles, or bold spans.
- **Table Extraction:** Utilizes `page.find_tables()` to detect grid tables, serializing cells to bracketed text (`[TABLE]...[/TABLE]`).
- **Scanned Image Warning:** When page text length is $< 15$ characters and no tables are found, records warning code `OCR_REQUIRED_OR_TEXT_NOT_EXTRACTABLE`.

### 2.2 python-docx Word Parser (`DocxParser`)
- **Engine:** `python-docx`
- **Supported Extensions:** `.docx`, `.doc`
- **Heading Hierarchy:** Inspects paragraph style names (`Heading 1`, `Heading 2`, `Heading 3`, `Title`) and assigns numeric heading levels (1, 2, 3).
- **Table Extraction:** Iterates through document table elements in document order, extracting headers and row values into `ExtractedTable`.
- **Page Model:** Wrapped into 1 logical page with discrete paragraph blocks.

### 2.3 Plain Text & Markdown Parser (`TxtParser`)
- **Engine:** Standard library UTF-8 binary stream parser
- **Supported Extensions:** `.txt`, `.md`
- **BOM Handling:** Automatically detects and strips 3-byte UTF-8 Byte Order Mark (`\xef\xbb\xbf`) with an info warning.
- **Fallback Decoding:** If UTF-8 decoding fails, attempts `latin-1` decoding and logs `UTF8_DECODE_FALLBACK` warning.
- **Heading Detection:** Parses markdown `# `, `## `, `### ` prefix syntax as well as numbered section lines (`1.0`, `Section 2`).

---

## 3. Authoritative Ingestion Metadata Contract (16 Canonical Fields)

The ingestion pipeline guarantees the preservation of **16 canonical metadata fields** across the document lifecycle. These fields are partitioned across database entities and intermediate parsed artifacts as follows:

| Field Index | Field Name | Data Type | Scope & Preservation Target | Description |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `doc_id` | `str` | DB Entity & Parsed Artifact | Stable unique document identifier (e.g. `DOC-ACAD-001`). |
| **2** | `file_hash_sha256` | `str` | DB Entity & Parsed Artifact | Cryptographic SHA-256 digest of original raw file bytes. |
| **3** | `filename` | `str` | DB Entity & Parsed Artifact | Original source file name on disk. |
| **4** | `storage_path` | `str` | DB Entity & Parsed Artifact | Normalized local storage path to source file. |
| **5** | `category` | `str` | DB Entity & Parsed Artifact | Institutional category (`academic_regulations`, etc.). |
| **6** | `language` | `str` | DB Entity & Parsed Artifact | Primary detected language code (`en`, `hi`, `kn`, `te`). |
| **7** | `page_number` | `int` | Block / Page Intermediate Artifact | 1-indexed physical page number (PDF) or logical page (DOCX/TXT). |
| **8** | `section_title` | `str \| null` | Block / Page Intermediate Artifact | Nearest preceding structural heading or section title. |
| **9** | `heading_level` | `int \| null` | Block / Page Intermediate Artifact | Hierarchy level of the heading (e.g., 1, 2, 3). |
| **10** | `text_content` | `str` | Block / Page Intermediate Artifact | Cleaned, normalized UTF-8 text string. |
| **11** | `extraction_notes` | `list[str]` | Block / Page Intermediate Artifact | Warnings or non-fatal extraction notes (e.g., OCR required). |
| **12** | `status` | `str` | DB Entity & Ingestion Result | Processing status (`uploaded`, `parsed`, `failed`). |
| **13** | `processed_at` | `str` (ISO) | DB Entity & Job Record | UTC timestamp of ingestion completion. |
| **14** | `parser_name` | `str` | Parsed Artifact & Job Metadata | Identifier of the parser implementation (`PyMuPDFParser`, etc.). |
| **15** | `parser_version` | `str` | Parsed Artifact & Job Metadata | Engine semantic version string. |
| **16** | `version` | `str` | DB Entity & Manifest | Document policy version string (e.g. `1.0`). |

---

## 4. Intermediate Representation Schema (`ParsedDocument`)


```json
{
  "doc_id": "DOC-ACAD-001",
  "filename": "DOC-ACAD-001.txt",
  "file_type": "txt",
  "parser_name": "TxtParser",
  "parser_version": "1.0.0 (utf8-stream)",
  "page_count": 1,
  "raw_text": "...",
  "normalized_text": "...",
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "blocks": [
        {
          "block_type": "heading",
          "text": "1.0 Autonomous Academic Regulations",
          "heading_level": 1,
          "section_title": "1.0 Autonomous Academic Regulations",
          "table_data": null
        },
        {
          "block_type": "paragraph",
          "text": "These regulations apply to all undergraduate programs...",
          "heading_level": null,
          "section_title": "1.0 Autonomous Academic Regulations",
          "table_data": null
        }
      ],
      "warnings": []
    }
  ],
  "sections": [
    {
      "title": "1.0 Autonomous Academic Regulations",
      "level": 1,
      "page": 1
    }
  ],
  "detected_language": "en",
  "detected_script": "latin",
  "language_confidence": 0.88,
  "warnings": [],
  "metadata": {
    "source_type": "synthetic"
  }
}
```
