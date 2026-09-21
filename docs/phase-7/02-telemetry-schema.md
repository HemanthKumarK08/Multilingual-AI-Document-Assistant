# Phase 7 — Telemetry Schema and Data Contract

## 1. Overview & Purpose

The telemetry subsystem provides privacy-preserving observability and big-data analytics for the Multilingual AI Document Assistant. It records operational metrics, query performance, language distributions, and reliability statistics without ever capturing sensitive user content, prompt templates, raw document text, retrieved passages, or credentials.

---

## 2. Schema Specification (Version 1.0)

### Event Types
- `query_completed`: Full request-level lifecycle event capturing query classification, latencies across stages, grounding state, fallback flags, and citation validity.
- `retrieval_completed`: Granular retrieval stage event capturing dense/lexical candidate counts, fusion metrics, and reranking timings.
- `rag_completed`: Granular generation stage event recording LLM provider, prompt/answer token metrics, grounding verification, and citation stats.
- `fallback_triggered`: Explicit out-of-domain or evidence-gated fallback event with reason categorization.
- `error`: Operational error event recording error category, error type, and stage without sensitive stack traces or inputs.

---

## 3. Data Dictionary

| Field | Type | Required | Description | Privacy Guarantee |
|---|---|---|---|---|
| `schema_version` | String | Yes | Telemetry schema version (default `"1.0"`) | Constant string |
| `event_id` | String | Yes | Unique UUID or random identifier | Ephemeral / Non-reversible |
| `event_type` | String | Yes | Event classification (`query_completed`, etc.) | Enum restricted |
| `timestamp` | String | Yes | ISO-8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Temporal metadata only |
| `date` | String | Yes | Partition date (`YYYY-MM-DD`) | Temporal dimension |
| `hour` | Integer | Yes | UTC hour (0–23) | Temporal dimension |
| `request_id_hash` | String | No | One-way SHA-256 hash or random UUID | Anonymized identifier |
| `query_id` | String | No | Query execution ID | Anonymized identifier |
| `retrieval_id` | String | No | Retrieval execution ID | Anonymized identifier |
| `language` | String | Yes | ISO language code (`en`, `hi`, `kn`, `te`, `und`) | Categorical metadata |
| `script` | String | Yes | Script classification (`latin`, `devanagari`, `kannada`, `telugu`, etc.) | Categorical metadata |
| `query_type` | String | No | Semantic query category (`cross_lingual_fact`, `definition`, etc.) | High-level taxonomy |
| `is_code_mixed` | Boolean | Yes | Flag indicating Romanized/code-mixed Indic query | Binary indicator |
| `variant_count` | Integer | Yes | Number of query expansion variants generated | Count only (no variant text) |
| `candidate_count` | Integer | Yes | Dense/lexical candidates retrieved | Integer count |
| `retrieved_chunk_count` | Integer | Yes | Number of chunks routed to reranker/context | Integer count |
| `selected_chunk_count` | Integer | No | Chunks included in final grounded context | Integer count |
| `best_retrieval_score` | Float | No | Maximum fusion score from reranker | Normalized scalar |
| `retrieval_latency_ms` | Float | Yes | Latency of hybrid retrieval and reranking in ms | Non-negative numeric |
| `reranking_latency_ms` | Float | No | Latency of cross-encoder / heuristic reranking in ms | Non-negative numeric |
| `generation_latency_ms`| Float | No | Latency of LLM response generation in ms | Non-negative numeric |
| `total_latency_ms` | Float | Yes | End-to-end request latency in ms | Non-negative numeric |
| `provider` | String | Yes | LLM provider name (`gemini`, `ollama`, `mock`) | Identifier |
| `answer_mode` | String | Yes | Mode of response (`grounded`, `fallback`, `error`) | High-level status |
| `fallback_used` | Boolean | Yes | Whether deterministic fallback was triggered | Boolean flag |
| `fallback_reason` | String | No | Categorical reason (`no_evidence`, `out_of_domain`, `error`) | Non-sensitive string |
| `citation_count` | Integer | Yes | Number of verified citations in answer | Non-negative integer |
| `citation_valid` | Boolean | Yes | Whether all citations passed provenance checks | Boolean flag |
| `grounded` | Boolean | Yes | Whether output was grounded in source documents | Boolean flag |
| `error` | Boolean | Yes | Whether an error occurred | Boolean flag |
| `error_type` | String | No | Categorical error classification (`Timeout`, `LLMUnavailable`) | High-level category |

---

## 4. Absolute Privacy Prohibitions

The following data elements are strictly prohibited from being persisted in telemetry records:
1. **Raw User Query Text** (`query`, `raw_query`, `query_text`)
2. **Generated Query Variants** (`variants`, `generated_variants`, `expanded_queries`)
3. **Document Contents & Passages** (`content`, `passage`, `document_text`, `chunk_text`)
4. **Generated LLM Answers** (`answer`, `response_text`, `llm_output`)
5. **Prompt Templates & Rendered Prompts** (`prompt`, `system_prompt`, `user_prompt`)
6. **Personally Identifiable Information (PII)**: Real names, email addresses, telephone numbers.
7. **Credentials & Secrets**: API keys, bearer tokens, passwords.
