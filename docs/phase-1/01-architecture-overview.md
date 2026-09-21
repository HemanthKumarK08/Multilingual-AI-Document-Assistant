# Phase 1: Architecture Overview & Subsystem Design

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 1 — Architecture, Environment, Database, and Corpus Foundation  
**Status:** IMPLEMENTED & AUDITED  

---

## 1. High-Level Architectural Layers

The system follows a modular monolithic architecture partitioned into three primary operational tiers:

```
+---------------------------------------------------------------------------------------+
|                                1. PRESENTATION LAYER                                  |
|   - Student Multilingual QA Portal (English, Hindi, Kannada, Telugu, Kanglish)        |
|   - Verifiable Source Citations & Raw Excerpt Inspection Drawer                       |
|   - Admin Document Ingestion, Status Monitor & PySpark Analytics Dashboard            |
+-------------------------------------------+-------------------------------------------+
                                            │ (HTTP / REST JSON)
                                            ▼
+---------------------------------------------------------------------------------------+
|                        2. APPLICATION & BACKEND API (FastAPI)                         |
|   +--------------------------+  +--------------------------+  +---------------------+ |
|   | Document Ingestion &     |  | Multilingual Vector      |  | Context-Grounded    | |
|   | Extraction Service       |  | Retrieval Service        |  | RAG LLM Generator   | |
|   | (PyMuPDF / python-docx)  |  | (Multilingual-E5-Small)  |  | (Gemini / Ollama)   | |
|   +--------------------------+  +--------------------------+  +---------------------+ |
|                │                             │                           │            |
|                ▼                             ▼                           ▼            |
|   +--------------------------+  +--------------------------+  +---------------------+ |
|   | SQLite Relational DB     |  | ChromaDB Vector Store    |  | Categorized JSONL   | |
|   | (Metadata, Jobs, Users)  |  | (Local Persistent HNSW)  |  | Telemetry Logger    | |
|   +--------------------------+  +--------------------------+  +---------------------+ |
+-------------------------------------------+-------------------------------------------+
                                            │ (Batch / Scheduled Execution)
                                            ▼
+---------------------------------------------------------------------------------------+
|                      3. BIG DATA ANALYTICS LAYER (Apache Spark)                       |
|   - PySpark Batch Aggregation Engine (`local[*]`)                                     |
|   - Categorized Event Ingestion (Real App, Synthetic Simulation, Evaluation Runs)     |
|   - Spark SQL Metric Computation: Language Trends, Knowledge Gaps, Latency P95        |
|   - Cached Analytics KPI Summaries consumed instantly by Admin Dashboard              |
+---------------------------------------------------------------------------------------+
```

---

## 2. Subsystem State & Phase Mapping

| Subsystem Component | Phase 1 Foundation State | Full Implementation Phase |
| :--- | :--- | :--- |
| **Relational Database** | **Fully Operational:** SQLite + SQLAlchemy models (`Document`, `DocumentProcessingJob`, `User`, `QueryLogReference`). | Complete in Phase 1 |
| **Environment & Config** | **Fully Operational:** Python 3.11 virtualenv, Pydantic Settings, `verify_environment.py`. | Complete in Phase 1 |
| **Document Corpus** | **Fully Operational:** 24 documents across 6 categories, validated by `validate_corpus.py`. | Complete in Phase 1 |
| **Evaluation Benchmark** | **Fully Operational:** 60 golden Q&A pairs with verified source document mappings. | Complete in Phase 1 |
| **API Web Service** | **Scaffolding Active:** FastAPI with CORS, `/health`, `/documents`, `/admin/login`, `/qa/query`. | Core RAG in Phase 3 |
| **Document Ingestion** | **Scaffolded:** Package structure ready; text extraction active in Phase 2. | Phase 2 |
| **Vector Indexing** | **Configured:** Storage paths and schemas defined; Chroma embedding active in Phase 2. | Phase 2 |
| **Multilingual RAG Engine**| **Contract Defined:** Prompt templates & decoupled `LLMProvider` ready; synthesis in Phase 3. | Phase 3 |
| **Big Data Telemetry** | **Schema Defined:** JSONL event model ready; PySpark batch ETL in Phase 4. | Phase 4 |
| **Analytics Dashboard** | **Contract Defined:** Summary endpoint ready; Chart.js UI in Phase 4. | Phase 4 |

---

## 3. Data Flow Between Components

```
1. Ingestion Flow (Phase 2):
   Admin Upload -> FastAPI Multipart -> SHA-256 Check -> SQLite Record -> PyMuPDF Page Chunker -> Multilingual-E5 Embeddings -> ChromaDB Index

2. Query & QA Flow (Phase 3):
   Student Query -> FastAPI Endpoint -> Language Detection -> E5 Query Vector -> ChromaDB Top-K Search -> Context Prompt Gating -> Gemini/Ollama LLM -> Grounded Response with Citations -> Telemetry JSONL Log

3. Big Data Analytics Flow (Phase 4):
   Telemetry JSONL Logs -> PySpark DataFrame Ingestion -> Spark SQL Aggregations -> summary.json Cache -> Admin Dashboard Render
```
