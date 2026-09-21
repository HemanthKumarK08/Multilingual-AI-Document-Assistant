# Phase 7 — Analytics API Specification

## 1. Overview

The Analytics API exposes precomputed big-data telemetry metrics via FastAPI endpoints. The design guarantees zero runtime compute overhead during HTTP request handling by serving deterministic JSON metrics generated during batch PySpark execution.

---

## 2. Endpoint Catalog

All routes are prefixed under `/api/analytics`:

| Endpoint | Method | Response Structure | Purpose |
|---|---|---|---|
| `/api/analytics/health` | `GET` | Status, manifest presence, last generated timestamp | Telemetry subsystem status |
| `/api/analytics/summary` | `GET` | High-level volume, latency, grounding, and fallback KPIs | Executive overview dashboard |
| `/api/analytics/volume` | `GET` | Total events, daily and hourly distributions | Ingestion & usage volume trends |
| `/api/analytics/languages` | `GET` | Language and script query distributions, code-mixed rates | Multilingual performance |
| `/api/analytics/retrieval` | `GET` | Latency percentiles, candidate counts, reranking timings | Search & retrieval performance |
| `/api/analytics/rag` | `GET` | Generation latencies, grounding rates, citation stats | RAG quality & provider metrics |
| `/api/analytics/errors` | `GET` | Error counts, error rates, and failure categories | Reliability & system health |
| `/api/analytics/timeseries`| `GET` | Multi-day/hourly metric trends | Time-series visualization |

---

## 3. Response Contracts & Error Handling

When analytics have not yet been generated (e.g. fresh installation or pipeline reset), endpoints return HTTP 200 with standard fallback envelopes:
```json
{
  "status": "pending_generation",
  "message": "Analytics batch job has not run yet. Execute scripts/run_spark_analytics.py to generate metrics."
}
```

When manifest and metrics files are present, responses include deterministic payloads accompanied by manifest metadata (`generated_at_utc`, `source_record_count`, `privacy_status`).
