# Hardware and Storage Feasibility Analysis

## 1. Target Hardware Profile (Student Laptop Baseline)

The system is explicitly engineered to run reliably on a standard student laptop:
- **Processor:** 4-Core to 8-Core modern CPU (Intel Core i5/i7, AMD Ryzen 5/7, or Apple Silicon M1/M2/M3).
- **Installed System RAM:** 8.0 GB (Minimum) / 16.0 GB (Recommended).
- **Discrete GPU:** **Not Required**. (All core pipelines run natively on CPU).
- **Available Disk Storage:** $\ge 15.0\text{ GB}$ free SSD storage.
- **Operating System:** Cross-platform support (macOS, Ubuntu/Debian Linux, Windows 11 with WSL2).

---

## 2. Granular Memory (RAM) Budget Breakdown

| Subsystem / Process | Runtime RAM Footprint | Notes & Optimization Strategy |
| :--- | :---: | :--- |
| **Operating System & Background Apps** | 2.5 – 3.0 GB | Standard baseline OS allocation. |
| **FastAPI Web Service + Uvicorn** | 120 – 180 MB | Lightweight ASGI async worker process. |
| **ChromaDB Vector Store (In-Memory)** | 200 – 350 MB | Holds indexed embeddings and HNSW graph for 5,000 chunks. |
| **Multilingual Embedding Model (`E5-small`)**| 450 – 600 MB | PyTorch CPU memory during vectorization inference. |
| **PySpark JVM Runtime (`local[*]`)** | 1.2 – 1.8 GB | Spark Driver memory during batch analytical aggregation jobs. |
| **Browser UI (Tabs, Charts, Rendering)** | 250 – 400 MB | Standard browser memory usage. |
| **Total Peak Memory Consumption** | **4.7 – 6.3 GB** | **Feasible on an 8 GB RAM laptop** with room to spare. |

---

## 3. Storage Footprint & Disk Allocation Estimates

| Component / Directory | Estimated Disk Space | Location / Management Policy |
| :--- | :---: | :--- |
| **Python Virtual Environment (`.venv`)** | 1.2 – 1.8 GB | PyTorch (CPU-only build), FastAPI, ChromaDB, PySpark. |
| **HuggingFace Embedding Model Cache** | 500 MB – 1.0 GB | Cached under `~/.cache/huggingface/hub/`. Downloaded once. |
| **Institutional Document Repository** | 50 – 100 MB | 30–50 PDF/Word circulars stored in `data/documents/`. |
| **ChromaDB Vector Storage Directory** | 50 – 150 MB | Parquet / SQLite files stored in `data/vector_store/`. |
| **Telemetry Event Logs (`.jsonl`)** | 50 – 200 MB | Partitioned logs for 100,000 queries in `logs/telemetry/`. |
| **PySpark Analytics Parquet & Cache** | 100 – 300 MB | Spark temporary checkpoints and output files in `data/analytics/`. |
| **Total Disk Requirement** | **$\approx 3.0\text{ to }5.5\text{ GB}$** | **Extremely safe on 15 GB+ free disk space.** |

---

## 4. Dual-Mode Deployment Strategy

To accommodate varying hardware capabilities and internet connectivity scenarios, the system supports two operational configurations via `.env`:

```
               ┌─────────────────────────────────────────────────────────────┐
               │                  DUAL OPERATIONAL MODES                     │
               └──────────────────────────────┬──────────────────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
      ┌───────────────────────────┐                       ┌───────────────────────────┐
      │   MODE A: CLOUD-ASSISTED  │                       │   MODE B: 100% OFFLINE    │
      │     HYBRID (RECOMMENDED)  │                       │     LOCAL INFERENCE       │
      ├───────────────────────────┤                       ├───────────────────────────┤
      │ • Embeddings: Local CPU   │                       │ • Embeddings: Local CPU   │
      │ • Vector Store: Local CPU │                       │ • Vector Store: Local CPU │
      │ • LLM: Free Gemini Flash  │                       │ • LLM: Local Ollama Model │
      │ • RAM Required: ~4.5 GB   │                       │ • RAM Required: ~8.5 GB   │
      │ • Internet: Active        │                       │ • Internet: Zero (Airgap) │
      │ • Latency: ~1.5s          │                       │ • Latency: ~7.0s          │
      └───────────────────────────┘                       └───────────────────────────┘
```

---

## 5. Storage-Saving Guardrails & Download Safety

To prevent accidental hard-drive exhaustion or unexpected out-of-memory crashes on student laptops:
1. **CPU-Only PyTorch Wheel:** In the installation instructions, specify CPU-only PyTorch (`pip install torch --index-url https://download.pytorch.org/whl/cpu`), avoiding unnecessary 3–5 GB CUDA binary downloads.
2. **Model Download Guardrails:** Hardcode and verify embedding model identifiers so that arbitrary multi-gigabyte models are not triggered dynamically.
3. **Log File Rotation:** Limit telemetry log file size to 25 MB per segment, archiving or rolling older logs to prevent uncontrolled disk growth.
4. **Spark Garbage Collection Configuration:** Set JVM memory flags (`spark.driver.memory=2g`) to strictly bound Spark heap allocation.
