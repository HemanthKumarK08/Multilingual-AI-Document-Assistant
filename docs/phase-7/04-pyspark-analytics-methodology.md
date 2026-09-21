# Phase 7 — PySpark Batch Analytics Methodology

## 1. Objective & Design Principles

The PySpark analytics pipeline aggregates partitioned Parquet datasets into deterministic, structured JSON metrics. It runs purely locally on CPU in `local[*]` mode with zero external cluster or distributed storage requirements.

---

## 2. Resource & Runtime Optimization (Apple Silicon Mac)

| Setting | Value | Rationale |
|---|---|---|
| `spark.master` | `local[*]` | Utilizes local Apple Silicon CPU cores without network overhead |
| `spark.sql.shuffle.partitions` | `4` | Prevents unnecessary shuffle partition explosion on small/medium datasets |
| `spark.driver.memory` | `2g` | Fits safely within 16 GB unified memory headroom |
| `spark.driver.maxResultSize` | `1g` | Prevents memory exhaust during driver collection |
| `JAVA_HOME` | `/opt/homebrew/opt/openjdk@17` | Standard Java 17 LTS runtime |
| `SPARK_HOME` | `/tmp/aiml_pyspark_home` | POSIX symlink workaround preventing classpath separator colons |

---

## 3. Analytical Computations & Metric Formulations

### A. Volume Analytics
- `total_events`: Count of all records across all partitions.
- `total_queries`: Count of `event_type = 'query_completed'`.
- `events_by_type`: Aggregation grouping by `event_type`.
- `events_per_day`: Aggregation grouping by partition `date`.
- `events_per_hour`: Aggregation grouping by UTC `hour`.

### B. Language Analytics
- `query_count`: Count of queries grouped by `language`.
- `query_percentage`: $\frac{\text{queries for language } L}{\text{total query events}} \times 100$.
- `script_distribution`: Aggregation grouping by `script`.
- `code_mixed_count` & `code_mixed_percentage`: Indicator for Romanized queries.
- `language_fallback_rate`: $\frac{\text{fallback queries for language } L}{\text{total queries for language } L} \times 100$.
- `language_avg_latency_ms`: Mean of `total_latency_ms` grouped by language.

### C. Retrieval Analytics
- `average_retrieval_latency_ms`: Mean of `retrieval_latency_ms`.
- `p50_retrieval_latency_ms` & `p95_retrieval_latency_ms`: PySpark `percentile_approx(retrieval_latency_ms, array(0.5, 0.95))`.
- `average_candidate_count`: Mean of initial candidate chunks fetched.
- `average_retrieved_chunk_count`: Mean of chunks passed to reranker.
- `average_reranking_latency_ms`: Mean reranker execution duration.

### D. RAG & Generation Analytics
- `average_generation_latency_ms`: Mean LLM response latency.
- `average_total_latency_ms` & `p95_total_latency_ms`: End-to-end latency percentiles.
- `grounded_answer_rate_pct`: $\frac{\text{grounded answers}}{\text{total queries}} \times 100$.
- `citation_validity_rate_pct`: $\frac{\text{queries with valid citations}}{\text{total queries}} \times 100$.
- `average_citation_count`: Mean number of validated citations.
- `provider_usage`: Distribution across `gemini`, `ollama`, and `mock`.

### E. Reliability Analytics
- `total_errors`: Count of events where `error = true` or `event_type = 'error'`.
- `error_rate_pct`: $\frac{\text{total errors}}{\text{total events}} \times 100$.
- `fallback_rate_pct`: $\frac{\text{fallback queries}}{\text{total queries}} \times 100$.
- `errors_by_category`: Aggregated by `error_type`.

### F. Time-Series Trends
- Daily & hourly trends tracking query volume, mean/P95 latency, fallback rate, error rate, and grounding rate over time.

---

## 4. Execution Command
```bash
python scripts/run_spark_analytics.py \
  --parquet data/telemetry/parquet \
  --output data/telemetry/analytics
```
