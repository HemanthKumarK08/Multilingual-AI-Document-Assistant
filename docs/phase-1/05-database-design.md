# Relational Database Design & Schema Specification

**Database Engine:** SQLite 3 (via SQLAlchemy 2.0 Async + `aiosqlite`)  
**Storage Location:** [`data/app.db`](file:///Users/hemanthkumark/College/BIT/AI:Ml/data/app.db)  
**Seeding Script:** [`scripts/seed_database.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/scripts/seed_database.py)  

---

## 1. Entity-Relationship Diagram (Logical Schema)

```
       +------------------------------------+
       |              documents             |
       +------------------------------------+
       | PK  id                 Integer     |
       | UQ  doc_id             String(64)  |<---------+
       |     filename           String(255) |          |
       |     display_title      String(255) |          |
       | IX  category           String(100) |          |
       |     description        Text        |          |
       |     language           String(10)  |          |
       |     file_type          String(20)  |          |
       |     file_size_bytes    Integer     |          |
       | UQ  file_hash_sha256   String(64)  |          |
       |     storage_path       String(500) |          |
       |     page_count         Integer     |          |
       |     chunk_count        Integer     |          |
       |     version            String(20)  |          |
       | IX  status             String(30)  |          |
       | IX  is_active          Boolean     |          |
       |     error_message      Text        |          |
       |     created_at         DateTime    |          |
       |     updated_at         DateTime    |          |
       +------------------------------------+          |
                         │                             | (Foreign Key)
                         │ 1:N                         |
                         ▼                             |
       +------------------------------------+          |
       |      document_processing_jobs      |          |
       +------------------------------------+          |
       | PK  id                 Integer     |          |
       | UQ  job_id             String(64)  |          |
       | FK  doc_id             String(64)  |----------+
       |     job_type           String(50)  |
       | IX  status             String(30)  |
       |     started_at         DateTime    |
       |     completed_at       DateTime    |
       |     error_message      Text        |
       |     job_metadata       Text (JSON) |
       |     created_at         DateTime    |
       |     updated_at         DateTime    |
       +------------------------------------+

       +------------------------------------+       +------------------------------------+
       |               users                |       |        query_log_references        |
       +------------------------------------+       +------------------------------------+
       | PK  id                 Integer     |       | PK  id                 Integer     |
       | UQ  user_id            String(64)  |       | UQ  query_id           String(64)  |
       | UQ  username           String(100) |       | IX  session_id         String(64)  |
       |     role               String(50)  |       | IX  timestamp          DateTime    |
       |     password_hash      String(255) |       | IX  telemetry_source   String(50)  |
       |     is_active          Boolean     |       |     detected_language  String(10)  |
       |     created_at         DateTime    |       | IX  category           String(100) |
       |     updated_at         DateTime    |       |     top_similarity     Float       |
       +------------------------------------+       | IX  is_fallback        Boolean     |
                                                    |     user_feedback      Integer     |
                                                    |     file_path          String(500) |
                                                    |     created_at         DateTime    |
                                                    |     updated_at         DateTime    |
                                                    +------------------------------------+
```

---

## 2. Table Specifications & Indexing Strategy

### 2.1 Table: `documents`
- **Purpose:** Primary catalog of all uploaded institutional regulatory files.
- **Deduplication:** Enforced by unique constraint and index on `file_hash_sha256`.
- **Soft Deletion:** `is_active` boolean allows immediate exclusion of documents from queries without deleting historical telemetry logs.
- **Composite Indexes:**
  - `idx_doc_cat_active` on `(category, is_active)`
  - `idx_doc_status_active` on `(status, is_active)`

### 2.2 Table: `document_processing_jobs`
- **Purpose:** Tracks asynchronous background processing pipelines (text extraction, chunking, vector embedding, index rebuild).
- **Foreign Key:** `doc_id` references `documents.doc_id` with `ON DELETE CASCADE`.

### 2.3 Table: `users`
- **Purpose:** Administrator credentials and authorization roles.
- **Security:** Plaintext passwords are never stored; PBKDF2-HMAC-SHA256 salted hashes with 100,000 iterations are stored in `password_hash`.

### 2.4 Table: `query_log_references`
- **Purpose:** Lightweight relational index of user interaction events. Full telemetry payloads remain in partitioned JSONL files for high-throughput PySpark processing.
- **Data Provenance:** Tagged with `telemetry_source` (`REAL_APPLICATION`, `SYNTHETIC_SIMULATION`, `EVALUATION_BENCHMARK`, `ERROR_DIAGNOSTIC`).

---

## 3. Database Initialization & Seeding Command

To initialize the schema and populate baseline metadata:
```bash
.venv/bin/python scripts/seed_database.py
```
