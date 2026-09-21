# Phase 5 — Citations and Information-Not-Found Behavior

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 5 — Retrieval, Reranking, and Grounded RAG Pipeline  
**WBS Stage:** WBS Stage 9 (Grounded RAG and Answer Construction)  
**Date:** 2026-09-12  

---

## 1. Provenance Citation Contract

Every claim made by the assistant is linked directly to a verifiable chunk in the institutional knowledge base.

### 1.1. Citation Extraction & Mapping (`citation_formatter.py`)
- Regex pattern `\[(?:Source\s*)?(\d+)\]` extracts cited source indices from generated text.
- Maps indices (e.g. `[Source 1]`) to actual `SourceCitation` objects containing:
  - `chunk_id`
  - `doc_id`
  - `filename`
  - `page_number`
  - `section_title`
  - `file_hash_sha256`
- **Fabrication Prevention:** If the LLM returns an unknown source index (e.g., `[Source 99]`), the citation validator flags an error and refuses to attach unverified metadata.

---

## 2. Deterministic Information-Not-Found Fallback

When evidence is missing, inconclusive, or below quality thresholds, the pipeline returns a deterministic fallback response:

```text
Information Not Found in the provided documents.
```

### 2.1. Fallback Trigger Conditions
| Scenario | Fallback Reason Code | Resulting Response |
|---|---|---|
| No candidates returned by retrieval | `NO_CANDIDATES` | Fallback message, 0 citations |
| Best retrieval score below 0.35 | `LOW_RELEVANCE` | Fallback message, 0 citations |
| Query matched prompt injection | `PROMPT_INJECTION_DETECTED` | Fallback message, 0 citations |
| Informative keywords not in context | `LOW_RELEVANCE` | Fallback message, 0 citations |
| LLM Provider error / timeout | `PROVIDER_UNAVAILABLE` | Fallback message, 0 citations |
| Model declares insufficient evidence | `MODEL_FALLBACK_TRIGGERED` | Fallback message, 0 citations |

### 2.2. Guarantees
- **No Hallucinated Citations:** Fallback responses never include citations.
- **`grounded = False`:** Explicit flag for downstream UI/API handling.
