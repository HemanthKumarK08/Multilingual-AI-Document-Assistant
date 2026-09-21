# Phase 7 — Telemetry Privacy & Security Audit

## 1. Zero-Leakage Privacy Policy

The Multilingual AI Document Assistant enforces strict privacy guarantees at every layer of the architecture:
- **No Raw Queries**: User search queries are tokenized or transformed in-memory and never logged to telemetry or analytical files.
- **No Passages**: Text snippets from institutional documents or chunks are excluded from logs.
- **No Prompt/Answer Text**: Generation prompts and raw model answers are omitted from metrics.
- **No Credentials or Personal Data**: User emails, phone numbers, and API tokens are rejected both at ingestion and during audit scans.

---

## 2. Automated Privacy Audit Tool (`scripts/audit_telemetry_privacy.py`)

The auditor performs deep recursive scanning across:
1. Raw JSONL files in `data/telemetry/raw/`
2. Validated JSONL files in `data/telemetry/validated/`
3. Parquet Lake files in `data/telemetry/parquet/`
4. Analytics JSON files in `data/telemetry/analytics/`

### Audit Checkpoints
- **Forbidden Key Scan**: Ensures no key matches prohibited terms (`query`, `raw_query`, `prompt`, `answer`, `passage`, `token`, `password`, `email`, etc.).
- **PII Pattern Regex**: Evaluates all string values against patterns for email addresses, phone numbers, and Bearer / API credential formats.
- **Oversized String Heuristic**: Flags arbitrary free-form strings exceeding 200 characters to prevent accidental prompt payload dumps.
- **Strict Exit Codes**: Returns exit code `0` on clean state and `1` on any detected privacy violation.

### CLI Usage
```bash
python scripts/audit_telemetry_privacy.py --telemetry data/telemetry
```
