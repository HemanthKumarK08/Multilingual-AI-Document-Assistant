# Configuration & Secrets Management Specification

**Status:** IMPLEMENTED & AUDITED  
**Module Reference:** [`app/core/config.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/app/core/config.py)  
**Template File:** [`.env.example`](file:///Users/hemanthkumark/College/BIT/AI:Ml/.env.example)  

---

## 1. Security Principles & Secret Isolation

1. **Zero Hardcoded Secrets:** All secret keys, API credentials, and database connection strings are loaded exclusively via environment variables or a local `.env` file.
2. **Git Exclusion:** `.env` is explicitly ignored in `.gitignore`, preventing accidental commits of private credentials.
3. **Secret Masking:** In Pydantic model representation (`repr=False`), sensitive attributes (`GEMINI_API_KEY`, `GROQ_API_KEY`, `ADMIN_TOKEN_SECRET`, `ADMIN_DEFAULT_PASSWORD`) are omitted from logs and debug dumps.
4. **Safe Local Defaults:** Non-sensitive defaults allow the development environment to initialize immediately without configuration friction.

---

## 2. Configuration Parameter Schema

| Parameter Name | Data Type | Default Value | Description & Sensitivity |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `str` | `"Multilingual AI Document Assistant"` | Display title of the application. |
| `APP_ENV` | `str` | `"development"` | Environment (`development`, `testing`, `production`). |
| `APP_DEBUG` | `bool` | `false` | Enables SQLAlchemy SQL echo and verbose debug logs. |
| `APP_HOST` | `str` | `"0.0.0.0"` | Network interface for FastAPI Uvicorn listener. |
| `APP_PORT` | `int` | `8000` | HTTP port for web server. |
| `DATABASE_URL` | `str` | `"sqlite+aiosqlite:///./data/app.db"` | Async SQLite database connection string. |
| `VECTOR_STORE_PATH` | `str` | `"./data/vector_store/chroma"` | Directory location for ChromaDB vector files. |
| `VECTOR_COLLECTION_NAME` | `str` | `"institutional_documents_v1"` | Active Chroma collection identifier. |
| `EMBEDDING_MODEL_NAME` | `str` | `"intfloat/multilingual-e5-small"` | HuggingFace embedding model ID. |
| `EMBEDDING_DIMENSION` | `int` | `384` | Embedding vector dimensionality. |
| `SIMILARITY_THRESHOLD` | `float` | `0.65` | Cosine similarity gating threshold ($\tau$) for RAG context. |
| `LLM_PRIMARY_PROVIDER` | `str` | `"gemini"` | Primary generative backend (`gemini`, `groq`, `ollama`). |
| `LLM_FALLBACK_PROVIDER`| `str` | `"ollama"` | Fallback generative engine on rate-limit / offline. |
| `LLM_MODEL_NAME` | `str` | `"gemini-1.5-flash"` | Target generative model checkpoint. |
| `GEMINI_API_KEY` | `str` | `""` (**Sensitive**) | Google AI Studio free-tier API Key. |
| `ADMIN_TOKEN_SECRET` | `str` | `"dev-insecure-secret..."` (**Sensitive**)| HMAC-SHA256 session token signing key. |
| `ADMIN_TOKEN_EXPIRY_MINUTES`| `int`| `480` (8 Hours) | Session validity lifetime before requiring re-login. |
| `TELEMETRY_DIRECTORY` | `str` | `"./data/telemetry"` | Directory destination for JSONL telemetry events. |
| `SPARK_MASTER` | `str` | `"local[*]"` | Apache Spark execution master. |

---

## 3. How to Configure for Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. (Optional) Add your Google Gemini API key to enable hosted LLM generation:
   ```env
   GEMINI_API_KEY=AIzaSy...your_key_here
   ```
3. If running offline, set `LLM_PRIMARY_PROVIDER=ollama` and ensure the Ollama daemon is running locally on port 11434.
