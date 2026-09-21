# Multilingual AI Document Assistant with Big Data Analytics

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-orange.svg)](https://www.trychroma.com/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.3-E25A1C.svg)](https://spark.apache.org/)
[![Status](https://img.shields.io/badge/Phase%207-Completed%20%26%20Audited-brightgreen.svg)]()

> **MCA Major Project — Bangalore Institute of Technology (BIT)**  
> An NLP, Retrieval-Augmented Generation (RAG), and Apache Spark Big Data system for intelligent document retrieval and multilingual institutional knowledge analytics.

---

## 🚀 Quick Start

### Option 1 — One Click (Recommended on macOS)

Simply **double-click** the launcher in Finder or execute:
```bash
./run_project.command
```

**What the one-click launcher does automatically:**
1. Detects project root and validates Python 3.11.
2. Creates or verifies the virtual environment (`.venv`).
3. Installs and updates all required dependencies.
4. Prepares `.env` with safe local defaults if missing.
5. Cleans up any stale processes occupying port `8000`.
6. Launches the FastAPI backend with database and ChromaDB initialization.
7. Waits for health checks to pass (`http://localhost:8000/health`).
8. **Automatically opens the interactive application in your default web browser (`http://localhost:8000/docs`).**
9. Streams live server logs and cleanly shuts down child processes on `Ctrl+C`.

---

### Option 2 — Terminal (Manual Startup)

1. **Activate Virtual Environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Application Server:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access in Browser:**
   - **Interactive API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Alternative ReDoc UI:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - **System Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)
   - **Analytics Health Endpoint:** [http://localhost:8000/api/v1/analytics/health](http://localhost:8000/api/v1/analytics/health)

---

## 🛑 How to Stop the Application

Double-click or run:
```bash
./stop_project.command
```
*(Or press `Ctrl+C` in the terminal window running `run_project.command`)*

This cleanly terminates all background workers and frees port `8000` while preserving database state and ChromaDB vector embeddings.

---

## 🩺 Project Health Check & Diagnostics

To run an automated health check verifying all environment dependencies, databases, vector stores, Parquet data lakes, analytics outputs, and test suites:
```bash
./check_project.sh
```

---

## 🧪 Running Tests

The test suite contains **197 automated unit and integration tests** covering all phases (Phase 0 through Phase 7):
```bash
# Run all tests
.venv/bin/pytest tests/ -v

# Run with concise summary
.venv/bin/pytest tests/ -q
```

---

## 📊 Running Big Data PySpark Analytics Pipeline

To ingest raw telemetry, export to the Parquet data lake, and execute local PySpark batch analytics:

```bash
# 1. Ingest & validate raw JSONL telemetry streams
python scripts/ingest_telemetry.py

# 2. Export validated telemetry to partitioned Parquet Data Lake
python scripts/export_telemetry_parquet.py

# 3. Run PySpark Batch Analytics
python scripts/run_spark_analytics.py

# 4. Run automated Zero-Raw-Data Privacy Audit
python scripts/audit_telemetry_privacy.py --telemetry data/telemetry
```

---

## ⚙️ Configuration & Environment Variables

Key configuration parameters (stored in `.env` or overridden by environment variables):

| Variable | Default Value | Description |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | Application bind host |
| `APP_PORT` | `8000` | Application HTTP port |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/app.db` | Async SQLite database path |
| `VECTOR_STORE_PATH` | `./data/vector_store` | ChromaDB persistence path |
| `EMBEDDING_MODEL_NAME` | `intfloat/multilingual-e5-small` | Multilingual embedding model (384 dim) |
| `LLM_PRIMARY_PROVIDER` | `gemini` | Primary generation engine (`gemini`, `groq`, `ollama`, `mock`) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key (optional for cloud generation) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama instance for 100% offline generation |
| `SPARK_MASTER` | `local[*]` | PySpark execution mode |
| `SPARK_SHUFFLE_PARTITIONS`| `4` | Local PySpark shuffle partitions for Apple Silicon |

---

## 🗂️ Project Directory Layout

```text
.
├── run_project.command       # One-click macOS project launcher
├── stop_project.command      # Project shutdown script
├── check_project.sh          # Comprehensive system diagnostics script
├── requirements.txt          # Master Python requirements file
├── pyproject.toml            # Project configuration and dependency metadata
├── .env.example              # Environment variables template
├── app/                      # Application core (Modular Monolith)
│   ├── api/routes/           # FastAPI routers (health, documents, qa, analytics, admin)
│   ├── core/                 # Configuration (Pydantic Settings), logging, security
│   ├── db/                   # SQLAlchemy async models, database engine, migrations
│   ├── schemas/              # Pydantic request/response data contracts
│   └── services/             # Ingestion, chunking, embeddings, vector_store, retrieval, rag, telemetry
├── data/
│   ├── app.db                # SQLite institutional relational database
│   ├── raw/                  # Initial institutional source documents (PDF, DOCX, TXT)
│   ├── processed/            # Parsed JSONs and page-aware chunk artifacts
│   ├── vector_store/         # ChromaDB persistent collection (document_chunks)
│   └── telemetry/            # Privacy-safe JSONL streams, partitioned Parquet lake, and analytics JSONs
├── docs/                     # Comprehensive Phase 0 to Phase 7 engineering documentation
├── scripts/                  # Batch ingestion, Parquet lake export, PySpark analytics & privacy audit
└── tests/                    # 197 automated unit and integration tests
```

---

## 💡 Troubleshooting

* **Port 8000 in use:** Run `./stop_project.command` to automatically kill stale processes, or check active PIDs using `lsof -i :8000`.
* **PySpark Java Error:** Ensure Java 17 LTS is installed via Homebrew (`brew install openjdk@17`). `run_project.command` automatically configures `JAVA_HOME=/opt/homebrew/opt/openjdk@17`.
* **Gemini API Key:** If running without a Gemini API key, the system automatically falls back to deterministic grounded evidence gating and offline fallback mechanisms. To enable live Gemini generation, add your free key to `.env`: `GEMINI_API_KEY="your_api_key"`.
