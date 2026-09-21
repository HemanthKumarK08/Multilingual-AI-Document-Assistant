# Document and Dataset Strategy

## 1. Document Types and Ingestion Scope

The document repository for development, testing, and evaluation will comprise structured institutional regulatory documents across multiple domains.

### 1.1 In-Scope Formats for Version 1
- **Digital PDFs (`.pdf`):** Searchable, machine-generated PDFs containing standard text, headings, bullet points, and basic single-tier tables.
- **Microsoft Word Documents (`.docx`):** Institutional circulars and syllabus specifications.
- **Plain Text Files (`.txt`):** Administrative notices and policy excerpts.

### 1.2 Out-of-Scope / Deferred Formats
- **Scanned Image PDFs (without text layer):** Deferred to Phase 6 (requires heavy OCR pipeline with potential Tesseract latency bottlenecks).
- **Complex Multi-Page Financial Spreadsheets (`.xlsx`):** Ingestion restricted to text extracts.
- **Encrypted / Password-Protected Files:** Strictly rejected during validation with informative error banners.

---

## 2. Institutional Document Collection Composition

To provide a comprehensive benchmark without violating private data policies, the project uses a hybrid corpus of **Public University Bylaws** (e.g., VTU, AICTE, UGC guidelines) and **Realistic Synthetic Institutional Circulars**.

| Document Category | Example Document Titles | Typical Page Range | Primary Content |
| :--- | :--- | :---: | :--- |
| **Academic Regulations** | *Academic_Regulations_2024_2025.pdf*, *Attendance_Condonation_Rules.pdf* | 10 – 35 | Grading system, minimum credits, detention rules, attendance thresholds (75% rule, medical exemptions). |
| **Examination Guidelines** | *Examination_Code_of_Conduct.pdf*, *Revaluation_and_MakeUp_Exam_Bylaws.pdf* | 8 – 20 | Hall ticket rules, malpractice penalties, revaluation procedures, backlog clearance schedules. |
| **Scholarships & Financial Aid**| *Post_Matric_Scholarship_Notice.pdf*, *Institutional_Fee_Concession_Policy.pdf* | 4 – 10 | Eligibility income limits, portal registration steps, required certificates, renewal criteria. |
| **Hostel & Campus Life** | *Hostel_Rules_and_Discipline_Manual.pdf*, *Anti_Ragging_Policy_2024.pdf* | 6 – 15 | Curfew timings, mess fee structure, guest policy, grievance redressal, disciplinary actions. |
| **Training & Placements** | *Placement_Policy_and_Eligibility_2024.pdf*, *Internship_Guidelines_Manual.pdf* | 5 – 12 | One-offer policy, minimum CGPA criteria, attendance requirement during placement drives. |
| **General Administrative** | *Fee_Refund_Policy_on_Cancellation.pdf*, *Library_Borrowing_and_Fine_Rules.pdf* | 3 – 8 | Admission withdrawal timelines, refund percentages, security deposit return procedures. |

### Target Corpus Volume:
- **Development & Unit Testing:** 5 core documents ($\approx 50\text{ pages}$, $\approx 350\text{ chunks}$).
- **Integration & Benchmark Evaluation:** 20–30 comprehensive documents ($\approx 250\text{ pages}$, $\approx 2,000\text{ chunks}$).
- **Big Data Analytics Demonstration:** 10,000 to 100,000 synthetic interaction log records generated against the active corpus.

---

## 3. Document Metadata Schema

Every uploaded document and its derived chunks must conform to the following metadata structure:

```json
{
  "doc_id": "doc_8f7b2c1a-9e3d-4c5b-a1b2-c3d4e5f6a7b8",
  "filename": "Academic_Regulations_2024.pdf",
  "category": "Academic Regulations",
  "file_size_bytes": 1428500,
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "uploaded_at": "2026-09-12T10:30:00Z",
  "page_count": 28,
  "chunk_count": 142,
  "language": "en",
  "is_active": true
}
```

### Chunk-Level Metadata (Embedded in Vector Store):
```json
{
  "chunk_id": "chunk_doc_8f7b2c1a_p04_c02",
  "doc_id": "doc_8f7b2c1a-9e3d-4c5b-a1b2-c3d4e5f6a7b8",
  "doc_title": "Academic Regulations 2024-2025",
  "category": "Academic Regulations",
  "page_number": 4,
  "chunk_index": 2,
  "char_length": 620,
  "text_content": "4.2 Attendance Shortage and Condonation: A student must maintain a minimum of 75% attendance in each course..."
}
```

---

## 4. Vector Store Lifecycle & Index Management

To ensure reliable, predictable vector persistence and index health across application restarts and document updates:

| Lifecycle Phase | Architectural Specification | Implementation Mechanism |
| :--- | :--- | :--- |
| **Storage Location** | `./data/vector_store/chroma/` | Persistent directory-backed ChromaDB SQLite & Parquet store. |
| **Collection Naming** | `institutional_documents_v1` | Explicit collection versioning to isolate model changes. |
| **Embedding Model** | `intfloat/multilingual-e5-small` | 384-dimensional dense vectors with normalized cosine similarity. |
| **Document ID Schema** | `doc_<sha256_prefix>_<timestamp>` | Globally unique, deterministic document identifier. |
| **Chunk ID Schema** | `chunk_<doc_id>_p<page>_c<idx>` | Hierarchical chunk ID embedding document, page, and chunk index. |
| **Duplicate Ingestion**| SHA-256 Hash Comparison | Uploads check `file_hash_sha256` against SQLite registry; duplicates rejected with HTTP 409. |
| **Soft Deactivation** | Metadata Filtering | Query vector filter `{ "is_active": { "$eq": true } }` ignores disabled policies. |
| **Hard Deletion** | Collection Purge | `collection.delete(where={"doc_id": doc_id})` permanently purges orphan chunks. |
| **Index Rebuild** | Batch Re-indexing CLI | `scripts/rebuild_vector_index.py` reads active documents from SQLite and regenerates vectors from scratch. |
| **Model Migration** | Versioned Migration | If embedding model changes, new collection (`..._v2`) is created; old vectors are never mixed. |
| **Backup & Restore** | File-System Snapshots | Archiving `./data/vector_store/` + `./data/app.db` restores complete operational state. |

---

## 5. Evaluation Q&A Dataset Design (Golden Benchmark)

To scientifically evaluate RAG precision, a curated benchmark of **60 Grounded Test Questions** will be authored:

- **20 In-Domain English Queries:** Explicit policy questions with clear single-page answers.
- **10 In-Domain Hindi Queries:** Cross-lingual queries (Devanagari script) mapping to English regulations.
- **10 In-Domain Kannada Queries:** Cross-lingual queries (Kannada script) mapping to English regulations.
- **10 In-Domain Telugu Queries:** Cross-lingual queries (Telugu script) mapping to English regulations (Staged evaluation).
- **5 Code-Mixed Queries:** Romanized Kanglish / Hinglish / Tenglish queries.
- **5 Negative / Out-of-Corpus Queries:** Questions about unmentioned topics to verify deterministic fallback behavior.

---

## 6. Privacy, Copyright, and Ethics

1. **Non-Confidential Data:** No private student records (marks, grades, disciplinary files containing student names or personal identifiers) will be ingested.
2. **Synthetic Data for Private Clauses:** Any document modeled on real institutions will have personal names, specific phone numbers, and identifying email addresses anonymized.
3. **Public Policy Attribution:** Public university guidelines are used strictly under academic fair use for educational research.
