# Phase 2.4 — Deduplication & Processing Job Lifecycle

## 1. Cryptographic File Deduplication Policy

To prevent storage bloat and redundant vector embedding computation, every file submitted for ingestion undergoes streaming SHA-256 hash calculation before parsing.

### 1.1 Hashing Specification:
- **Module:** [`app/services/ingestion/hashing.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/app/services/ingestion/hashing.py)
- **Buffer Size:** 64 KB streaming buffer (`DEFAULT_CHUNK_SIZE = 65536`)
- **Format:** 64-character lowercase hexadecimal digest
- **Database Constraint:** `documents.file_hash_sha256` is defined with `unique=True` and `index=True`.

### 1.2 Deduplication Workflow:
1. When `IngestionCoordinator.ingest_document()` is invoked, it computes the SHA-256 hash from raw source bytes.
2. Queries the SQLite database: `SELECT * FROM documents WHERE file_hash_sha256 = :hash`.
3. If a match is found with a different `doc_id`:
   - If `allow_reingest=False` (default): Immediately halts and returns `IngestionResult(status="duplicate", is_duplicate=True, details={"duplicate_of": existing_doc_id})`.
   - If `allow_reingest=True`: Updates the existing document record and reprocesses.

---

## 2. Processing Job State Machine

All asynchronous processing activities are tracked in the relational `document_processing_jobs` table via SQLAlchemy:

```
                  ┌───────────────┐
                  │    PENDING    │ (Job registered in queue)
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │    RUNNING    │ (Parser executing / text normalizing)
                  └───────┬───────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
  ┌───────────────┐               ┌───────────────┐
  │   COMPLETED   │               │    FAILED     │
  └───────────────┘               └───────────────┘
  (Metadata & JSON                 (Error recorded,
   artifact saved)                  DB rolled back)
```

### 2.1 State Attributes & Transitions:

| Field | Description | Running State | Completed State | Failed State |
| :--- | :--- | :---: | :---: | :---: |
| `job_id` | Unique identifier (`job_ingest_{doc_id}_{timestamp}`) | Set | Retained | Retained |
| `doc_id` | Foreign key referencing `documents.doc_id` | Set | Retained | Retained |
| `job_type` | Job classification (`ingestion`) | `ingestion` | `ingestion` | `ingestion` |
| `status` | State enumeration | `running` | `completed` | `failed` |
| `started_at` | UTC timestamp of job launch | `datetime.now(timezone.utc)` | Retained | Retained |
| `completed_at`| UTC timestamp of job termination | `None` | Set | Set |
| `error_message`| Error message or exception details | `None` | `None` | Set |
| `job_metadata` | JSON string with parser metrics | File info | Parser, char count, warnings | Partial metadata |

---

## 3. Transaction Rollback & Atomicity Guarantee

To eliminate corrupted or half-ingested documents:
1. If parser execution fails or an unhandled exception occurs, the coordinator catches the error, sets `job.status = "failed"`, `job.error_message = str(e)`, and updates `doc_record.status = "failed"`.
2. Emits an explicit `await db.commit()` for the failure record, ensuring administrators have complete visibility into what failed and why.
3. No intermediate or partial chunk artifacts are written to `data/processed/` when a failure occurs.
