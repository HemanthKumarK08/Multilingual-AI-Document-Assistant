# Multilingual AI Document Assistant with Big Data Analytics

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4.24-orange.svg)](https://www.trychroma.com/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.3-E25A1C.svg)](https://spark.apache.org/)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-Bulbul_v3-blueviolet.svg)](https://www.sarvam.ai/)
[![Test Suite](https://img.shields.io/badge/Tests-599%20Passing-brightgreen.svg)]()

> **MCA Project — Department of Master of Computer Applications, Bangalore Institute of Technology (BIT)**  
> **Author:** Hemanth Kumar K  
> An enterprise-grade, privacy-first Multilingual Document Assistant combining dense-lexical hybrid Retrieval-Augmented Generation (RAG), resilient multilingual answer generation, Sarvam Bulbul v3 neural voice synthesis, and Apache Spark Lakehouse analytics.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Supported Languages](#-supported-languages)
- [System Architecture](#-system-architecture)
- [End-to-End Workflow](#-end-to-end-workflow)
- [Multilingual RAG Pipeline](#-multilingual-rag-pipeline)
- [Multilingual Resilience & Generation Cascade](#-multilingual-resilience--generation-cascade)
- [Document Ingestion & Chunking](#-document-ingestion--chunking)
- [Grounded Answer Generation & Citations](#-grounded-answer-generation--citations)
- [Voice Interaction & Speech Recognition](#-voice-interaction--speech-recognition)
- [Sarvam Bulbul v3 Text-to-Speech](#-sarvam-bulbul-v3-text-to-speech)
- [Big Data Analytics & PySpark Engine](#-big-data-analytics--pyspark-engine)
- [Privacy & Security Architecture](#-privacy--security-architecture)
- [Technology Stack](#-technology-stack)
- [Project Directory Layout](#-project-directory-layout)
- [Requirements & Prerequisites](#-requirements--prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Configuration](#-environment-configuration)
- [Quick Start](#-quick-start)
- [Frontend User Interface](#-frontend-user-interface)
- [API Reference](#-api-reference)
- [Testing & Verification](#-testing--verification)
- [Troubleshooting](#-troubleshooting)
- [Academic Project Metadata](#-academic-project-metadata)

---

## 🌟 Overview

Institutional knowledge across universities, government organizations, and enterprises is frequently locked in dense PDFs, DOCX files, and unstructured circulars. Accessing this information is particularly challenging for multilingual populations who query in regional languages (such as Hindi, Kannada, or Telugu) or code-mixed dialects.

The **Multilingual AI Document Assistant** resolves this through an end-to-end grounded RAG architecture with:
1. **Hybrid Multi-Pass Retrieval:** Dense multilingual embeddings (`intfloat/multilingual-e5-small`) combined with BM25 lexical indexing and Reciprocal Rank Fusion (RRF).
2. **Resilient Multilingual Answer Generation:** A 3-level cascade preventing language unavailability through direct generation, secondary fallback, and grounded English intermediate translation.
3. **High-Fidelity Neural Speech Synthesis:** Server-side Sarvam Bulbul v3 TTS integration mapping Indian language responses to native regional speakers.
4. **Lakehouse Telemetry & PySpark Analytics:** Privacy-filtered, zero-raw-query telemetry processed into partitioned Parquet files and analyzed via Apache Spark.

---

## 🚀 Key Features

- **Multilingual Query Processing:** Full native script support and transliteration handling for English, Hindi (हिन्दी), Kannada (ಕನ್ನಡ), and Telugu (తెలుగు).
- **Hybrid Dense-Lexical Search:** ChromaDB vector store + BM25 keyword index fused via Reciprocal Rank Fusion ($k=60$) with heuristic reranking.
- **Strict Evidence Gating & Citations:** Eliminates hallucinations. Out-of-domain queries return explicit `INSUFFICIENT_EVIDENCE` indicators without fabricating answers. Every factual sentence carries verifiable `[Source N]` citations.
- **Multi-Level Generation Cascade:** Gracefully handles provider rate limits (HTTP 429) or generation failures via primary LLM (Gemini), secondary LLM (Groq), and grounded translation fallback.
- **Sarvam Bulbul v3 Neural Voice:** Generates studio-grade WAV speech audio mapped to native language speakers (`ratan`, `priya`, `ishita`, `neha`).
- **Interactive Single-Page Application (SPA):** React 18, Vite, and Tailwind CSS web interface featuring chat history, PDF viewers, voice query mode, evidence drawers, and real-time analytics dashboards.
- **Big Data Analytics via PySpark:** Batch processing pipeline computing query latency trends, language distribution, retrieval precision, and error rates from partitioned Parquet datasets.
- **Privacy & Security First:** Zero raw user queries or document text logged to telemetry; backend-only secrets management; SQLite metadata persistence.

---

## 🌐 Supported Languages

The application provides authoritative language detection, explicit target-language overrides, and Unicode script validation:

| Language | Code | Native Script | Unicode Block | Default TTS Voice | TTS Locale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **English** | `en` | Latin | `U+0020–U+007F` | `ratan` | `en-IN` |
| **Hindi** | `hi` | Devanagari (हिन्दी) | `U+0900–U+097F` | `priya` | `hi-IN` |
| **Kannada** | `kn` | Kannada (ಕನ್ನಡ) | `U+0C80–U+0CFF` | `ishita` | `kn-IN` |
| **Telugu** | `te` | Telugu (తెలుగు) | `U+0C00–U+0C7F` | `neha` | `te-IN` |

---

## 🏛 System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    React 18 SPA (Vite)                 │
                               │  - Ask AI (Chat)     - Document Viewer - Audio Player │
                               │  - Web Speech STT    - Analytics Charts - Settings UI  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ HTTP / REST (/api/v1)
                                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                  FastAPI Application Gateway                                            │
├──────────────────────────┬───────────────────────────────┬──────────────────────────────┬──────────────────────────────┤
│      Document Routes     │           QA Routes           │          TTS Routes          │       Analytics Routes       │
│  /api/v1/documents/*     │      /api/v1/qa/query         │   /api/v1/tts/synthesize     │    /api/v1/analytics/*       │
└────────────┬─────────────┴───────────────┬───────────────┴──────────────┬───────────────┴──────────────┬───────────────┘
             │                             │                              │                              │
             ▼                             ▼                              ▼                              ▼
 ┌───────────────────────┐   ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
 │   Document Ingestion  │   │  Hybrid Multilingual RAG  │  │  Sarvam Bulbul v3 Engine  │  │    Telemetry & Lakehouse  │
 │ - PyMuPDF / docx      │   │ - Query Translation       │  │ - Bulbul v3 REST API      │  │ - Privacy Redaction Filter│
 │ - Recursive Chunker   │   │ - ChromaDB Dense (e5)     │  │ - Native Speaker Mapping  │  │ - JSONL Buffer Streams    │
 │ - SQLite DB Metadata  │   │ - BM25 Lexical Search     │  │ - Base64 WAV Streaming    │  │ - Partitioned Parquet Lake│
 │ - ChromaDB Embedder   │   │ - RRF Fusion + Reranker   │  │ - Synthetic Test Fallback │  │ - Apache Spark Batch Jobs │
 └───────────────────────┘   │ - 3-Level Resilience LLM  │  └───────────────────────────┘  └───────────────────────────┘
                             └───────────────────────────┘
```

---

## 🔄 End-to-End Workflow

```
1. User Query (Text or Voice)
       │
       ▼
2. Language Resolution (Explicit Target or Auto-Detected Query Language)
       │
       ▼
3. Multi-Query Processing & Expansion (Transliteration & Keyword Variants)
       │
       ▼
4. Parallel Hybrid Retrieval
       ├─► Dense Vector Search (ChromaDB + multilingual-e5-small) -> Top 12 Chunks
       └─► Lexical Search (In-Memory BM25 with Indic Tokenizer)   -> Top 12 Chunks
       │
       ▼
5. Reciprocal Rank Fusion (RRF k=60) & Heuristic Score Boosting
       │
       ▼
6. Evidence Selection & Grounding Gate (Check Evidence Threshold >= 0.35)
       ├─► Below Threshold: Return INSUFFICIENT_EVIDENCE
       └─► Above Threshold: Build Numbered Evidence Context [Source 1..N]
       │
       ▼
7. Resilient Answer Generation Cascade
       ├─► Level 1: Primary Multilingual LLM (Gemini 3.6/3.8 Flash)
       ├─► Level 2: Secondary Multilingual LLM (Groq LLaMA/Qwen)
       └─► Level 3: Grounded English Intermediate -> Target Script Translation
       │
       ▼
8. Positive Unicode Script Validation (Devanagari, Kannada, Telugu, Latin)
       │
       ▼
9. Final Grounded Response returned to Frontend with Citations & Latency KPIs
       │
       ▼
10. Optional Voice Synthesis via Sarvam Bulbul v3 (Matching Native Speaker)
       │
       ▼
11. Privacy-Filtered Telemetry written to Parquet Data Lake for PySpark Analytics
```

---

## 🔍 Multilingual RAG Pipeline

### 1. Multilingual Embeddings & Vector Store
- **Embedding Model:** `intfloat/multilingual-e5-small` (384-dimensional dense vectors).
- **Query Prefixing:** Follows the asymmetric e5 embedding convention: queries are prefixed with `query: ` and chunk passages with `passage: `.
- **Vector Database:** ChromaDB with persistent storage in `./data/vector_store`.

### 2. Lexical Inverted Index (BM25)
- In-memory BM25 implementation tokenizing text across whitespace, punctuation, and Unicode word boundaries for Indic and Latin scripts.
- Automatically synchronized with ChromaDB on document ingestion, update, or deletion.

### 3. Reciprocal Rank Fusion (RRF) & Reranking
Dense and lexical candidate lists are fused using reciprocal rank scoring:
$$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{60 + r_{\text{dense}}(d)} + \frac{w_{\text{lexical}}}{60 + r_{\text{lexical}}(d)}$$
Where $w_{\text{dense}} = 0.70$ and $w_{\text{lexical}} = 0.30$. Candidate chunks undergo heuristic reranking based on exact phrase matches, term coverage, and document priority.

---

## 🛡 Multilingual Resilience & Generation Cascade

To ensure users never receive a generic `LANGUAGE_UNAVAILABLE` error when a provider encounters rate limits or script degradation, [`app/services/rag/coordinator.py`](file:///Users/hemanthkumark/College/BIT/Ml/app/services/rag/coordinator.py) implements a 3-level recovery cascade:

```
                  Retrieved Grounded Evidence Context
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ Level 1: Direct Primary Generation (Gemini)      │
         └────────────────────────┬─────────────────────────┘
                                  │ (fails / HTTP 429 / non-Indic script)
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ Level 2: Direct Secondary Generation (Groq)      │
         └────────────────────────┬─────────────────────────┘
                                  │ (fails / non-Indic script)
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ Level 3: Grounded Intermediate English Gen       │
         │          ↓                                       │
         │          Strict Target Translation Prompt        │
         │          ↓                                       │
         │          Unicode Script Validation & Retry       │
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ Final Grounded Answer with Authoritative Lang    │
         │ response_state = "GROUNDED"                      │
         │ generation_path = "direct" | "fallback_translate"│
         └──────────────────────────────────────────────────┘
```

### Strict Translation Rules
When Level 3 is engaged, translation operates under strict constraints:
- **No Independent Answering:** Translates only the grounded intermediate text.
- **Citation Preservation:** Verbatim preservation of `[Source 1]`, `[Source 2]` citations.
- **Entity Preservation:** Numeric values (e.g. `75%`), dates, names, URLs, and technical terms remain intact.
- **Script Enforcement:** Strictly outputs native Unicode characters (`U+0900–U+097F` for Hindi, `U+0C80–U+0CFF` for Kannada, `U+0C00–U+0C7F` for Telugu).

---

## 📄 Document Ingestion & Chunking

### Supported Document Types
- **PDF Documents (`.pdf`):** Extracted via PyMuPDF (`fitz`) with page-level tracking.
- **Word Documents (`.docx`):** Parsed via `python-docx` preserving headings, paragraphs, and tables.
- **Plain Text (`.txt`):** UTF-8 / UTF-16 encoded text files.

### Recursive Character Chunker
- Target Chunk Size: 500 characters with 100-character sliding overlap.
- Splits hierarchically across double newlines (`\n\n`), single newlines (`\n`), sentence boundaries (`.`, `|`, `?`, `!`, `।`), and whitespace.
- Preserves full provenance metadata: `document_id`, `filename`, `page_number`, `chunk_index`, and `file_hash_sha256`.

---

## 🎯 Grounded Answer Generation & Citations

- **Strict Grounding Prompt:** LLMs are explicitly instructed to answer using *only* provided evidence blocks.
- **Citation Badges:** Every claim is linked to source citations (e.g. `[Source 1]`), which the frontend renders as interactive badges. Clicking an evidence badge opens the **Evidence Drawer** showing the exact source snippet, similarity score, document ID, and page number.
- **Out-of-Domain (OOD) Protection:** If the highest retrieval score is below `RAG_MIN_EVIDENCE_SCORE` ($0.35$), the system halts generation and outputs a localized insufficient-evidence response without hallucinating.

---

## 🎙 Voice Interaction & Speech Recognition

The frontend integrates browser-native **Web Speech API** for hands-free voice search:
- **Voice Query Recognition:** Live speech-to-text supporting English (`en-IN`), Hindi (`hi-IN`), Kannada (`kn-IN`), and Telugu (`te-IN`).
- **Voice Response (Auto-Speak Mode):** When enabled, incoming RAG responses are automatically spoken aloud in the matching regional language.
- **Manual Audio Controls:** Individual `Speak` / `Stop` buttons on each chat message allow on-demand playback.

---

## 🔊 Sarvam Bulbul v3 Text-to-Speech

High-quality regional voice synthesis is powered by the **Sarvam Bulbul v3** neural TTS API:

- **Server-Side Proxy:** Client requests `/api/v1/tts/synthesize`; the backend uses the securely stored `SARVAM_API_KEY` to query `https://api.sarvam.ai/text-to-speech`.
- **WAV Audio Streaming:** Audio is synthesized at 16,000 Hz / 24,000 Hz and returned as base64-encoded WAV payloads for instant browser playback.
- **Native Speaker Mapping:**
  - `en` $\rightarrow$ `en-IN` / **`ratan`**
  - `hi` $\rightarrow$ `hi-IN` / **`priya`**
  - `kn` $\rightarrow$ `kn-IN` / **`ishita`**
  - `te` $\rightarrow$ `te-IN` / **`neha`**
- **Test Mode Fallback:** When running offline tests without an API key, the system produces synthetic WAV audio for headless validation (`tts_mode = "synthetic_test"`).

---

## 📊 Big Data Analytics & PySpark Engine

The application includes an Apache Spark batch analytics lakehouse:

```
Application Telemetry Event (JSONL)
                │
                ▼
      Privacy Redaction Filter
(Removes raw queries, auth headers, PII)
                │
                ▼
  Validated Telemetry Stream (JSONL)
                │
                ▼
 Partitioned Parquet Lakehouse (PyArrow)
 data/telemetry/parquet/year=YYYY/month=MM/
                │
                ▼
      Apache Spark Batch Jobs
   (PySpark 3.5.3 in local[*] mode)
                │
                ▼
 Precomputed Analytics Summary KPIs & Metrics
 (data/telemetry/analytics/*.json)
                │
                ▼
  FastAPI Analytics API & React Dashboards
```

### Precomputed Analytics Metrics
1. **Summary KPIs:** Total queries, unique sessions, average latency, grounded response rate, fallback rate.
2. **Language Distribution:** Volume and percentage breakdown across `en`, `hi`, `kn`, `te`.
3. **Retrieval Performance:** Mean similarity scores, top-k candidate distributions, dense vs lexical win rates.
4. **Hourly Query Volume:** Peak usage intervals and daily throughput trends.
5. **RAG Reliability:** Fallback category distributions (`INSUFFICIENT_EVIDENCE`, `EMPTY_CONTEXT`).

---

## 🔒 Privacy & Security Architecture

- **Backend-Only Secrets:** `GEMINI_API_KEY`, `GROQ_API_KEY`, and `SARVAM_API_KEY` are strictly loaded in server memory via Pydantic Settings and never exposed to client-side code.
- **Zero-Raw-Query Telemetry:** Telemetry logs contain *only* token counts, character lengths, language identifiers, latency metrics, and anonymized session UUIDs. User query text and document content are never written to telemetry files.
- **Role-Based Admin Authentication:** JWT-based token authentication for sensitive document administration endpoints.

---

## 💻 Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI | `>=0.110.0` | Async REST API & OpenAPI docs |
| **ASGI Server** | Uvicorn | `>=0.28.0` | High-performance asynchronous HTTP server |
| **Relational Database** | SQLite / aiosqlite | `>=0.20.0` | Asynchronous metadata and document tracking |
| **ORM & Data Mapping**| SQLAlchemy | `>=2.0.28` | Database schema models and async sessions |
| **Vector Store** | ChromaDB | `>=0.4.24` | Persistent dense vector indexing |
| **Embedding Model** | Sentence-Transformers | `>=2.5.0` | `intfloat/multilingual-e5-small` (384-dim) |
| **Lexical Indexing** | In-Memory BM25 | Native | Token-level lexical matching |
| **Deep Learning** | PyTorch | `>=2.2.0` | CPU/MPS tensor operations for embeddings |
| **Big Data Engine** | Apache Spark (PySpark)| `3.5.3` | Large-scale telemetry analytics |
| **Columnar Data Lake**| PyArrow / Parquet | `>=17.0.0` | Partitioned columnar storage |
| **Speech Synthesis** | Sarvam Bulbul v3 | API | Regional Indian language neural TTS |
| **Frontend SPA** | React | `18.3.1` | Single Page Application UI |
| **Frontend Bundler** | Vite | `6.0.3` | Modern frontend build tooling |
| **CSS Styling** | Tailwind CSS | `3.4.16` | Utility-first responsive design |
| **Data Visualization**| Recharts | `3.10.1` | Interactive analytics charts |
| **Icons** | Lucide React | `0.468.0` | UI iconography |

---

## 📁 Project Directory Layout

```text
.
├── run_project.command       # One-click macOS project launcher
├── stop_project.command      # Clean service termination script
├── check_project.sh          # System health check & diagnostics
├── requirements.txt          # Root Python dependencies file
├── pyproject.toml            # Project packaging & pytest configuration
├── .env.example              # Environment variable template
├── app/                      # FastAPI Backend Application
│   ├── api/routes/           # API routes (health, documents, qa, tts, analytics, admin)
│   ├── core/                 # Config (Pydantic), logging, security, landing page
│   ├── db/                   # SQLAlchemy async engine, session, and ORM models
│   ├── schemas/              # Pydantic request/response data contracts
│   └── services/             # Core RAG, retrieval, embeddings, chunking, telemetry, TTS
├── frontend/                 # React 18 / Vite / Tailwind SPA
│   ├── src/
│   │   ├── components/       # Chat, citations, evidence drawer, voice, analytics
│   │   ├── pages/            # Dashboard, AskAI, Documents, Analytics, Settings
│   │   ├── services/         # Axios API clients
│   │   └── App.jsx           # Main router and layout
│   ├── package.json          # Frontend dependency definitions
│   └── vite.config.js        # Vite bundler configuration
├── data/
│   ├── app.db                # SQLite application database
│   ├── raw/                  # Uploaded source documents (PDF, DOCX, TXT)
│   ├── processed/            # Chunk artifacts and parsed JSONs
│   ├── vector_store/         # ChromaDB persistent collection
│   └── telemetry/            # JSONL streams, Parquet data lake, analytics JSONs
├── docs/                     # Architectural documentation and phase reports
├── scripts/                  # Batch ingestion, Lakehouse export, PySpark runner
└── tests/                    # 599 automated unit and integration tests
    ├── unit/                 # Unit tests (parsers, chunkers, telemetry, security)
    └── integration/          # Integration tests (RAG, Sarvam TTS, retrieval, resilience)
```

---

## 📋 Requirements & Prerequisites

- **Operating System:** macOS (Apple Silicon / Intel), Linux, or Windows (WSL2).
- **Python:** Python `3.10` or `3.11` (Python `3.11` recommended).
- **Node.js:** Node.js `>= 18.0.0` and `npm` (for frontend building).
- **Java Runtime:** Java 17 LTS (Required for PySpark analytics; e.g., `brew install openjdk@17`).

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` and configure your API keys:

```bash
cp .env.example .env
```

### Configuration Parameters

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | String | `development` | Environment mode (`development`, `production`) |
| `APP_PORT` | Integer | `8000` | HTTP service port |
| `DATABASE_URL` | String | `sqlite+aiosqlite:///./data/app.db` | Async SQLite database URI |
| `VECTOR_STORE_PATH` | String | `./data/vector_store` | ChromaDB persistence folder |
| `EMBEDDING_MODEL_NAME` | String | `intfloat/multilingual-e5-small` | Hugging Face embedding model |
| `LLM_PRIMARY_PROVIDER` | String | `gemini` | Primary LLM (`gemini`, `groq`, `ollama`, `mock`) |
| `LLM_FALLBACK_PROVIDER`| String | `groq` | Secondary LLM fallback provider |
| `GEMINI_API_KEY` | Secret | `""` | Google Gemini API Key |
| `GROQ_API_KEY` | Secret | `""` | Groq API Key |
| `SARVAM_API_KEY` | Secret | `""` | Sarvam AI API Key for Bulbul v3 TTS |
| `TELEMETRY_ENABLED` | Boolean | `true` | Enables JSONL privacy telemetry logging |
| `SPARK_MASTER` | String | `local[*]` | PySpark execution cluster master |

---

## ⚡ Quick Start

### Option 1 — One-Click Launcher (macOS)
Double-click `run_project.command` in Finder or run:
```bash
./run_project.command
```
**The launcher automatically:**
1. Validates Python 3.11 and sets up `.venv`.
2. Builds the frontend application via Vite.
3. Cleans up any stale processes on port 8000.
4. Pre-warms embedding models, ChromaDB, and BM25 indexes.
5. Launches the backend server and opens `http://localhost:8000/` in your default browser.

### Option 2 — Manual Terminal Startup

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build frontend
cd frontend && npm install && npm run build && cd ..

# 4. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Stopping the Application
```bash
./stop_project.command
```

---

## 🖥 Frontend User Interface

- **Ask AI (`/`):** Full conversational interface with query language auto-detection, explicit language dropdowns, microphone input, clickable citation badges, and Sarvam audio playback.
- **Documents (`/documents`):** Ingest new PDF/DOCX files, inspect page counts and chunk distributions, preview source documents, or delete obsolete files.
- **Analytics (`/analytics`):** Real-time KPI summary cards, interactive query volume charts, language distribution pie charts, and RAG reliability panels.
- **Settings (`/settings`):** Configure active LLM providers, temperature, similarity thresholds, and inspect vector store health.

---

## 📡 API Reference

### Health
- `GET /health` — Application health check.
- `GET /health/ready` — Readiness check verifying database and vector store connectivity.

### Question Answering & RAG
- `POST /api/v1/qa/query` — Submit a multilingual query.
  ```json
  {
    "query_text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?",
    "target_language": "kn"
  }
  ```
- `POST /api/v1/qa/feedback` — Submit user feedback (+1 / -1) for an answer.

### Text-to-Speech
- `POST /api/v1/tts/synthesize` — Synthesize neural speech via Sarvam Bulbul v3.
  ```json
  {
    "text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ 75% ಹಾಜರಾತಿ ಕಡ್ಡಾಯವಾಗಿದೆ.",
    "language": "kn"
  }
  ```

### Documents
- `POST /api/v1/documents/upload` — Multipart file upload and automatic RAG ingestion.
- `GET /api/v1/documents` — List all registered institutional documents.
- `GET /api/v1/documents/{doc_id}` — Retrieve detailed document metadata.
- `GET /api/v1/documents/{doc_id}/chunks` — Inspect extracted chunk passages.
- `DELETE /api/v1/documents/{doc_id}` — Delete document and evict vectors from ChromaDB/BM25.

### Analytics
- `GET /api/v1/analytics/health` — Check analytics lakehouse status.
- `GET /api/v1/analytics/summary` — Retrieve high-level summary KPIs.
- `GET /api/v1/analytics/metrics/{metric_name}` — Retrieve granular metric series.
- `POST /api/v1/analytics/run-spark-pipeline` — Trigger an on-demand PySpark batch run.

---

## 🧪 Testing & Verification

The repository contains **599 automated tests** verifying all layers of the system:

```bash
# Run the complete test suite
.venv/bin/pytest tests/ -v

# Run multilingual resilience tests
.venv/bin/pytest tests/integration/test_multilingual_resilience.py -v

# Run Sarvam TTS integration tests
.venv/bin/pytest tests/integration/test_sarvam_tts.py -v

# Run system health diagnostics
./check_project.sh
```

---

## 🛠 Troubleshooting

- **Port 8000 already in use:** Execute `./stop_project.command` to automatically kill stale Uvicorn workers, or run `lsof -ti :8000 | xargs kill -9`.
- **PySpark Java Missing:** Install Java 17 LTS (`brew install openjdk@17`). The launcher automatically configures `JAVA_HOME`.
- **Gemini Rate Limits (HTTP 429):** The built-in resilience cascade automatically catches 429 errors and delegates generation to Groq or the translation cascade without disrupting user queries.

---

## 🎓 Academic Project Information

- **Institution:** Bangalore Institute of Technology (BIT), Bengaluru
- **Department:** Master of Computer Applications (MCA)
- **Project Title:** Multilingual AI Document Assistant with Big Data Analytics
- **Candidate:** Hemanth Kumar K (1BI23MC041)
- **Academic Year:** 2024–2026
