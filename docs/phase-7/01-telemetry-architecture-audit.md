# Phase 7 — Telemetry Architecture and Contract Audit

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 7 — Privacy-Preserving Telemetry, Parquet Data Lake, PySpark Analytics, and Analytics API  
**Date:** 2026-09-15  
**Status:** AUDITED & APPROVED  

---

## 1. Overview and Current State Assessment

A comprehensive audit of the telemetry emission points and log stores across Phase 5 and Phase 6 was conducted:

### Existing Telemetry Sources
1. **RAG QA Route (`app/api/routes/qa.py`):** Emits `RAGTelemetryEvent` per user query, logging language, latency, candidate count, fallback status, and citations.
2. **Retrieval Coordinator (`app/services/retrieval/coordinator.py`):** Computes per-variant metrics, candidate counts, and hybrid reranking scores.
3. **Telemetry Recorder (`app/services/telemetry/recorder.py`):** Appends raw JSON lines to `data/telemetry/{event_type}.jsonl`.

---

## 2. Privacy Guarantees & Non-Negotiable Boundaries

The current implementation guarantees strict zero-raw-data persistence:
- **No Raw Queries:** User input queries (`raw_query`, `query_text`) are never written to telemetry.
- **No Prompt Payloads:** Grounded system instructions and prompt templates are excluded.
- **No Chunk Passages or Answers:** Document contents, excerpts, and LLM generated responses are never written to disk.
- **No Sensitive Identifiers:** Request IDs are anonymized UUIDs without session or PII linkage.

---

## 3. Identified Gaps for Big Data Analytics

1. **Schema Versioning:** Existing events lacked explicit `schema_version` ("1.0"), `date`, and `hour` partition columns.
2. **Unified Completed Event Model:** Retrieval and generation events were partially decoupled; a consolidated `query_completed` event is required for holistic RAG analytics.
3. **Validation Layer:** Events were dumped without defensive runtime scanning for accidental field injections (e.g. `raw_query`, `api_key`, `token`).
4. **Columnar Parquet Lake:** Telemetry was stored exclusively in flat `.jsonl` files without compression or partition hierarchy.
5. **PySpark Aggregations:** Batch analytics scripts were missing, leaving analytics API routes with placeholder responses.

---

## 4. Phase 7 Architecture Plan

```text
[FastAPI / RAG Pipeline]
          │
          ▼
[TelemetryRecorder & Validator] ──► data/telemetry/raw/
          │
          ▼ (Batch Ingestion CLI: ingest_telemetry.py)
[Validated JSONL] ──► data/telemetry/validated/ (and rejected/)
          │
          ▼ (Parquet Converter: export_telemetry_parquet.py)
[Partitioned Parquet Lake] ──► data/telemetry/parquet/date=YYYY-MM-DD/event_type=.../
          │
          ▼ (PySpark Batch Analytics: run_spark_analytics.py)
[Aggregated JSON Analytics] ──► data/telemetry/analytics/*.json + manifest.json
          │
          ▼
[FastAPI Analytics Endpoints: /api/v1/analytics/*]
```

---

## 5. Backward Compatibility Strategy

- Existing `RetrievalTelemetryEvent` and `RAGTelemetryEvent` models in `app/services/telemetry/models.py` are preserved and extended with `schema_version`, `date`, and `hour` metadata.
- A new unified `UnifiedQueryTelemetryEvent` (`event_type="query_completed"`) is introduced for unified analytics.
- Old JSONL logs without `schema_version` will be safely normalized to version 1.0 during ingestion.
