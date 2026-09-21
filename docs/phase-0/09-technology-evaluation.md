# Technology Evaluation and Architectural Selection

This document provides an objective, resource-aware comparative analysis of technology candidates for each layer of the **Multilingual AI Document Assistant with Big Data Analytics**.

---

## 1. Frontend Framework Evaluation

| Candidate | Advantages | Disadvantages / Resource Impact | Recommendation & Justification |
| :--- | :--- | :--- | :--- |
| **Vanilla HTML5 + Modern CSS + JavaScript** | • Zero build step or npm overhead.<br>• Instant page load, ultra-low RAM footprint.<br>• Clean glassmorphic UI with full native control. | • Manual DOM manipulation for complex state. | **Recommended for Version 1 Core**: Eliminates build-tool complexity and runs seamlessly in any browser without consuming laptop RAM. |
| **React (Vite + Tailwind)** | • Component-based architecture.<br>• Rich ecosystem of charting libraries (Recharts/Chart.js). | • Requires Node.js runtime and build toolchain.<br>• Heavier memory footprint during development. | **Alternative for Phase 4+**: Suitable if dedicated SPA with complex state management is prioritized later. |
| **Streamlit** | • Extremely fast Python-only prototyping.<br>• Built-in widget ecosystem. | • Re-runs entire script on every user click, creating poor latency for RAG.<br>• Limited customization for bilingual chat + source drawers. | **Rejected**: Inadequate responsiveness and layout flexibility for a polished student/admin portal. |

---

## 2. Backend Web Framework Evaluation

| Candidate | Advantages | Disadvantages | Recommendation & Justification |
| :--- | :--- | :--- | :--- |
| **FastAPI (Python 3.10+)** | • High-performance asynchronous execution (ASGI).<br>• Automatic OpenAPI/Swagger documentation.<br>• Native Pydantic data validation and typing.<br>• Direct Python integration with PySpark, Chroma, and Transformers. | • Requires async understanding for streaming endpoints. | **Recommended (Primary Backend)**: Standard industry choice for modern AI/ML backends with typed request/response contracts. |
| **Flask** | • Minimalist and lightweight.<br>• Simple routing model. | • Synchronous by default; lacks built-in Pydantic validation and auto-documentation. | **Rejected**: Slower throughput and requires boilerplate for validation. |
| **Django** | • Full-featured ORM and admin suite. | • Excessive overhead, heavy boilerplate, and monolithic architecture unsuitable for a micro-RAG service. | **Rejected**: Overengineered for this project scope. |

---

## 3. Application Database Evaluation

| Candidate | Advantages | Disadvantages | Recommendation & Justification |
| :--- | :--- | :--- | :--- |
| **SQLite (via SQLAlchemy / aiosqlite)** | • Zero-configuration, zero-daemon serverless engine.<br>• Built into Python standard library.<br>• File-based persistence with negligible RAM usage. | • Not designed for high-concurrency multi-node writes. | **Recommended**: Ideal for local laptop development and single-server institutional deployments. Easily stores document metadata, user feedback, and cached Spark aggregations. |
| **PostgreSQL** | • Enterprise-grade ACID compliance, concurrent writes.<br>• Supports `pgvector` extension. | • Requires running a separate system daemon, consuming 150–300 MB background RAM and complex setup on student laptops. | **Rejected for V1**: Adds unnecessary operational overhead without tangible academic benefit at V1 scale. |
| **MySQL** | • Widely taught in university curricula. | • Lacks native vector capabilities; requires separate background service. | **Rejected**: Unnecessary daemon overhead. |

---

## 4. Vector Database & Indexing Layer Evaluation

| Candidate | Advantages | Disadvantages | Recommendation & Justification |
| :--- | :--- | :--- | :--- |
| **ChromaDB** | • Native Python embedded mode (no background service).<br>• Built-in metadata filtering (`category == 'Hostel'`).<br>• Direct SQLite persistence on disk.<br>• Rich documentation and active ecosystem. | • Can experience performance degradation if index exceeds 500,000 vectors (not an issue for 5k–10k chunks). | **Recommended (Primary Vector Store)**: Perfect match for student laptop deployment. Zero external daemon, persists to directory, supports metadata filtering. |
| **FAISS (Facebook AI Similarity Search)** | • Blazing fast C++ similarity search.<br>• Ultra-low memory footprint. | • Requires manual metadata indexing/mapping wrapper; lacks built-in document persistence schema. | **Alternative (Backup Vector Engine)**: Useful if extreme vector search benchmarking is requested. |
| **Qdrant / Milvus (Standalone Server)** | • Production distributed clustering, enterprise features. | • Requires Docker containers and dedicated server memory (1 GB+ RAM). | **Rejected**: Incompatible with lightweight student laptop constraint. |

---

## 5. Multilingual Embedding Model Evaluation

| Candidate | Model Size & RAM | CPU Latency (per chunk) | Indic & Code-Mixed Support | Recommendation & Justification |
| :--- | :---: | :---: | :---: | :--- |
| **`intfloat/multilingual-e5-small`** | $\approx 470\text{ MB}$ | $\approx 50–70\text{ ms}$ | High cross-lingual semantic alignment across 100+ languages including Kannada, Telugu, Hindi. | **Recommended (Primary Model)**: Exceptional balance of accuracy, small memory footprint, and low CPU inference latency. |
| **`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`** | $\approx 1.1\text{ GB}$ | $\approx 150–200\text{ ms}$ | Very High semantic accuracy. | **Alternative (High Accuracy Mode)**: Usable if 16 GB RAM is available on host machine. |
| **`ai4bharat/indic-bert`** | $\approx 500\text{ MB}$ | $\approx 100\text{ ms}$ | Strong on native scripts, weaker on Romanized code-mixed text. | **Rejected as primary**: E5-small provides superior cross-lingual English-Indic transfer. |

---

## 6. Large Language Model (LLM) Generation & Configuration Strategy

To prevent vendor lock-in, eliminate hardcoded model names, and ensure resilience against API rate-limiting or offline defense conditions, the LLM layer is designed behind an abstract polymorphic provider interface (`LLMProvider`):

```
                                  ┌─────────────────────────────┐
                                  │   Abstract LLMProvider      │
                                  │   + generate_response()     │
                                  │   + health_check()          │
                                  └──────────────┬──────────────┘
                                                 │
                     ┌───────────────────────────┼───────────────────────────┐
                     ▼                           ▼                           ▼
        ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
        │   GeminiProvider        │ │   GroqProvider          │ │   OllamaProvider        │
        │   (Primary Hosted API)  │ │   (Secondary Hosted API)│ │   (Local Offline Fallback│
        │   - Free Tier / High RPM│ │   - Low Latency Llama-3 │ │   - CPU 4-bit Quantized │
        └─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

### 6.1 Configuration Parameters (`.env` / `config.yaml`)
| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| `LLM_PRIMARY_PROVIDER` | `gemini` | Primary LLM engine (`gemini`, `groq`, `ollama`). |
| `LLM_FALLBACK_PROVIDER` | `ollama` | Fallback engine if primary returns HTTP 429/500 or times out. |
| `LLM_MODEL_NAME` | `gemini-1.5-flash` | Specific model checkpoint identifier (configurable without code edits). |
| `GEMINI_API_KEY` | `""` | User-supplied free Google AI Studio API key. |
| `GROQ_API_KEY` | `""` | Optional secondary fast hosted API key. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama daemon endpoint for 100% offline inference. |
| `OLLAMA_MODEL_NAME` | `llama3.2:3b-instruct-q4_K_M` | Small 4-bit quantized model for CPU laptop execution. |
| `LLM_TEMPERATURE` | `0.0` | Zero temperature to minimize generative variance and reduce hallucination risk. |
| `LLM_TIMEOUT_SECONDS` | `15` | Request timeout before triggering fallback or user warning. |

### 6.2 Risk & Limitation Analysis
- **Rate-Limit Risk:** Hosted free-tier APIs enforce request-per-minute (RPM) quotas. The backend implements exponential backoff retry (2 attempts) and caches identical query hashes.
- **Offline Defense Limitation:** If internet connectivity drops during an academic evaluation, switching `LLM_PRIMARY_PROVIDER=ollama` enables 100% offline operation on CPU, with a generation latency trade-off (6–10s on CPU vs 1.5s on API).
- **Multilingual Nuance:** Smaller local models (3B) have lower syntactic fluency in native Kannada/Telugu scripts compared to larger models; Gemini 1.5 Flash provides state-of-the-art multilingual translation fidelity.

---

## 7. Authentication & Security Architecture

| Security Component | Implementation Decision for Version 1 | Rationale & Security Boundary |
| :--- | :--- | :--- |
| **Student / General QA Access** | **Public Anonymous Read-Only** | Low barrier of entry; no credentials required to query or view citations. |
| **Admin Route Protection** | **HTTP Bearer Session Token** | Protects `/admin/*`, upload endpoints, index rebuild, and PySpark triggers. |
| **Password Storage** | **PBKDF2-HMAC-SHA256 (Salted)** | Admin password hashed securely in SQLite `admin_users` table; fallback `ADMIN_SECRET_KEY` in `.env`. |
| **Session Lifetime** | **Ephemeral 8-Hour Expiry** | Cryptographically signed session tokens invalidated on logout or timeout. |
| **Out-of-Scope Auth** | **Enterprise SSO / LDAP / Multi-tenant** | Deferred to prevent bloat; non-essential for single-institution academic deployment. |

---

## 7. Document Extraction Libraries

| Candidate | Formats Supported | Performance & Page-Awareness | Recommendation |
| :--- | :--- | :--- | :--- |
| **PyMuPDF (`fitz`)** | PDF | High-speed C-based text extraction; accurate page-by-page bounding boxes and layout preservation. | **Recommended for PDFs**: 10x faster than pure-Python extractors. |
| **`python-docx`** | DOCX | Native extraction of paragraphs, headings, and tables from Word documents. | **Recommended for Word docs**. |
| **`pdfplumber`** | PDF | Excellent for complex tabular extraction, but 5x slower. | **Secondary tool for tabular pages**. |
| **`pypdf`** | PDF | Basic extraction, often loses whitespace structure in multi-column layouts. | **Rejected**. |

---

## 8. Big Data & Analytics Engine

| Candidate | Processing Model | Suitability for Telemetry & Aggregation | Recommendation |
| :--- | :--- | :--- | :--- |
| **Apache Spark (PySpark 3.5+)** | Distributed memory engine (`local[*]` mode on multi-core CPU). | Fulfills Big Data curriculum requirements; executes Spark SQL, RDD/DataFrame aggregations over large event batches. | **Recommended (Core Big Data Engine)**: Provides rigorous distributed computing demonstration. |
| **Pandas** | Single-threaded in-memory tabular library. | Simple, but does not fulfill Big Data engineering criteria or distributed paradigms. | **Rejected for Big Data pipeline**: Used only for final UI data framing if needed. |

---

## 9. Final Recommended Technology Stack Summary

```
+-------------------------------------------------------------------------------+
| LAYER                 | RECOMMENDED SELECTION          | RESOURCE IMPACT     |
+-------------------------------------------------------------------------------+
| User Interface        | HTML5 / Modern CSS / Vanilla JS| Negligible (<50MB)  |
| Backend Service       | FastAPI (Python 3.10+)         | ~120 MB RAM         |
| Application DB        | SQLite (via SQLAlchemy)        | Negligible (<20MB)  |
| Vector Store          | ChromaDB (Embedded local mode) | ~250 MB RAM         |
| Multilingual Embeddings| intfloat/multilingual-e5-small| ~470 MB (Disk/RAM)  |
| LLM Generator         | Gemini 1.5 Flash API (Hybrid)  | 0 MB local RAM      |
| Document Extraction   | PyMuPDF (fitz) + python-docx   | ~50 MB RAM          |
| Big Data Analytics    | Apache Spark (PySpark Local[*])| ~1.5 - 2.0 GB RAM   |
+-------------------------------------------------------------------------------+
| TOTAL ESTIMATED PEAK RUNTIME RAM FOOTPRINT: ~2.5 - 3.5 GB (Well within 8GB/16GB laptop)|
+-------------------------------------------------------------------------------+
```
