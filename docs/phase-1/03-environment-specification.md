# Environment Specification & Verification Report

**Date of Audit:** September 2026  
**Host Operating System:** macOS (Darwin 25.6.0 arm64 — Apple Silicon)  
**Python Runtime:** Python 3.11.15 (Target 3.10/3.11 fully satisfied)  
**Virtual Environment Path:** `/Users/hemanthkumark/College/BIT/AI:Ml/.venv`  

---

## 1. System Runtime & Tool Inventory

| Tool / Runtime | Installed Version | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Python** | `3.11.15` (CPython 64-bit) | **PASS** | Optimal version for PyTorch CPU, ChromaDB, and PySpark 3.5. |
| **pip** | `26.2.1` | **PASS** | Modern package manager within `.venv`. |
| **Git** | `2.54.0` (Apple Git-157) | **PASS** | Initialized repository with comprehensive `.gitignore`. |
| **Java Runtime** | OpenJDK `25.0.1+8-LTS` (Temurin) | **PASS** | Ready for local Apache Spark batch execution. |
| **Disk Storage** | 76.8 GB free of 228.3 GB SSD | **PASS** | Far exceeds the $\ge 15\text{ GB}$ requirement. |
| **Compute Arch** | ARM64 / Apple Silicon (Metal MPS) | **PASS** | Fully capable of fast local CPU/MPS embedding execution. |

---

## 2. Core Dependency Status (Phase 1 Baseline)

| Package | Installed Version | Purpose |
| :--- | :---: | :--- |
| `fastapi` | `0.111.1` | High-performance async ASGI web framework. |
| `uvicorn` | `0.29.0` | ASGI production server worker. |
| `pydantic` | `2.13.5` | Data validation and type enforcement. |
| `pydantic-settings` | `2.15.0` | Environment variable parsing and validation. |
| `sqlalchemy` | `2.0.52` | Relational ORM and database abstraction. |
| `aiosqlite` | `0.20.0` | Asynchronous SQLite driver for non-blocking I/O. |
| `greenlet` | `3.5.5` | Concurrency engine for SQLAlchemy async context. |
| `pymupdf` (`fitz`) | `1.24.14` | Fast C-based PDF text extraction engine. |
| `python-docx` | `1.1.2` | Native Microsoft Word document extraction. |
| `pytest` | `8.4.2` | Automated unit and integration test runner. |
| `pytest-asyncio` | `0.23.8` | Async test fixtures and event loop management. |
| `httpx` | `0.27.2` | Async HTTP client for integration test requests. |

---

## 3. Dependency Tiers & Planned Rollout Schedule

Dependencies are partitioned into distinct tiers to maintain lightweight, reproducible environments:

1. **Tier 1: Core Verified Baseline (`requirements/base.txt` & `requirements/dev.txt`)**
   - *Status:* Installed and verified in active `.venv`.
   - *Packages:* `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `aiosqlite`, `greenlet`, `pymupdf`, `python-docx`, `pytest`, `pytest-asyncio`, `httpx`.
2. **Tier 2: Java & JVM Runtime**
   - *Status:* OpenJDK 25.0.1 LTS installed and verified via `JAVA_HOME`.
   - *Purpose:* Prerequisite for Apache Spark (PySpark) execution in Phase 7.
3. **Tier 3: Intentionally Deferred ML & Big Data Packages (`requirements/optional.txt`)**
   - *Status:* Specified but intentionally not installed during Phase 1 to prevent premature downloads and heavy memory usage.
   - *Packages & Rollout Schedule:*
     - `torch`, `transformers`, `sentence-transformers` -> Phase 4 (Embeddings & Vector Store)
     - `chromadb` -> Phase 4 (Vector Store Indexing)
     - `google-genai` -> Phase 5 (RAG Generation)
     - `pyspark` -> Phase 7 (Big Data Telemetry Analytics)

---

## 4. Virtual Environment Setup & Path Notes

> [!NOTE]
> The standard virtual-environment creation command encountered a path/tooling compatibility issue in the current workspace. The environment was successfully created using an alternative supported method (`virtualenv -p python3.11 .venv`). All Python, pip, and pytest invocations cleanly resolve to the active virtual environment at `/Users/hemanthkumark/College/BIT/AI:Ml/.venv`.


## 5. Verification Execution Output

Environment verification executed via `scripts/verify_environment.py`:
```text
======================================================================
 MULTILINGUAL AI DOCUMENT ASSISTANT — ENVIRONMENT VERIFICATION
======================================================================
[1] SYSTEM & RUNTIME PREREQUISITES
  [PASS] Python 3.11.15 (Target 3.10/3.11 satisfied)
  [PASS] Active virtualenv at /Users/hemanthkumark/College/BIT/AI:Ml/.venv
  [PASS] git available (git version 2.54.0 (Apple Git-157))
  [PASS] Java runtime available: openjdk version "25.0.1" 2025-10-21 LTS
  [PASS] 76.8 GB free of 228.3 GB disk space (Sufficient)

[2] HARDWARE SPECS & COMPUTE ACCELERATION
  [PASS] CPU Architecture: arm64 (arm)
  [OPTIONAL] PyTorch not installed yet (CPU execution is default for Phase 2)

[3] CORE APPLICATION & DATABASE PACKAGES (PHASE 1 BASELINE)
  [PASS] FastAPI, Uvicorn, Pydantic, SQLAlchemy, aiosqlite, PyMuPDF, python-docx, pytest, httpx

[5] PROJECT STORAGE & DIRECTORY PERMISSIONS
  [PASS] data/raw, data/processed, data/evaluation, data/telemetry, data/vector_store, logs
======================================================================
VERIFICATION PASSED: Environment is ready for Phase 1 execution.
======================================================================
```
