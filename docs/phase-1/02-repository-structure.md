# Repository Structure Specification

This document details the directory organization, module responsibilities, and file locations for the project.

```text
/Users/hemanthkumark/College/BIT/AI:Ml/
├── app/                                 # Core FastAPI Backend Application
│   ├── __init__.py
│   ├── main.py                          # Application lifespan, CORS, and routing entrypoint
│   ├── core/                            # Central configuration, logging, and security
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic Settings and environment validation
│   │   ├── logging.py                   # Centralized logging setup
│   │   └── security.py                  # PBKDF2 hashing & HMAC session tokens
│   ├── api/                             # REST API Endpoints
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py              # Aggregated API router
│   │       ├── health.py                # System health check & diagnostics
│   │       ├── documents.py             # Document metadata & listing endpoints
│   │       ├── qa.py                    # Public student QA & feedback endpoints
│   │       ├── analytics.py             # PySpark analytics summary endpoint
│   │       └── admin.py                 # Administrator authentication
│   ├── db/                              # Relational Database Layer (SQLite / aiosqlite)
│   │   ├── __init__.py
│   │   ├── base.py                      # DeclarativeBase and TimestampMixin
│   │   ├── session.py                   # Async database engine & session maker
│   │   └── models/                      # SQLAlchemy Data Entities
│   │       ├── __init__.py
│   │       ├── document.py              # Document model
│   │       ├── job.py                   # DocumentProcessingJob model
│   │       ├── user.py                  # User / Admin model
│   │       └── telemetry_ref.py         # QueryLogReference model
│   ├── services/                        # Business Logic Service Modules
│   │   ├── __init__.py
│   │   ├── documents/                   # Document metadata service
│   │   ├── ingestion/                   # PDF/DOCX extraction & chunking (Phase 2)
│   │   ├── retrieval/                   # ChromaDB vector search (Phase 2)
│   │   ├── rag/                         # Context-grounded LLM synthesis (Phase 3)
│   │   ├── language/                    # Language detection & transliteration (Phase 3)
│   │   ├── telemetry/                   # Asynchronous JSONL event logger (Phase 4)
│   │   └── analytics/                   # PySpark batch aggregation ETL (Phase 4)
│   ├── schemas/                         # Pydantic Request & Response Models
│   │   └── __init__.py
│   └── utils/                           # Shared utility helpers
│       └── __init__.py
├── scripts/                             # Operational & Verification Scripts
│   ├── verify_environment.py            # Environment prerequisite verification script
│   ├── seed_database.py                 # SQLite database initializer and seeder
│   ├── validate_corpus.py               # Corpus manifest and checksum validator
│   └── generate_initial_corpus.py       # Corpus synthesis utility
├── data/                                # Persistent Application Data Directories
│   ├── raw/                             # Ingested institutional regulatory files
│   │   ├── academic_regulations/
│   │   ├── examination_guidelines/
│   │   ├── attendance/
│   │   ├── scholarships/
│   │   ├── hostel/
│   │   ├── placements/
│   │   └── corpus_manifest.json         # Authoritative document catalog with SHA-256 hashes
│   ├── processed/                       # Chunked and normalized text extracts
│   ├── evaluation/                      # Golden benchmark dataset and documentation
│   │   ├── eval_dataset.json            # 60 benchmark Q&A pairs
│   │   └── README.md
│   ├── telemetry/                       # Partitioned JSON Lines telemetry logs
│   ├── vector_store/                    # ChromaDB persistent SQLite & Parquet vectors
│   └── app.db                           # Local SQLite relational database file
├── docs/                                # Project Documentation Suites
│   ├── phase-0/                         # Phase 0 Discovery, Scope & Feasibility specifications
│   └── phase-1/                         # Phase 1 Architecture, Database & Corpus documentation
├── tests/                               # Automated Test Suite (Pytest)
│   ├── __init__.py
│   ├── unit/                            # Unit tests for config, security, models
│   │   ├── test_config.py
│   │   ├── test_security.py
│   │   └── test_db_models.py
│   └── integration/                     # Integration tests for FastAPI endpoints
│       └── test_api.py
├── requirements/                        # Layered Dependency Requirements
│   ├── base.txt                         # Core FastAPI & SQLite dependencies
│   ├── dev.txt                          # Testing & QA dependencies
│   └── optional.txt                     # Future ML, Chroma, and PySpark dependencies
├── .env.example                         # Environment configuration template
├── .gitignore                           # Comprehensive git exclusion rules
├── pyproject.toml                       # Python package configuration
└── README.md                            # Project overview & quickstart
```
