# Golden Evaluation Benchmark Dataset Specification

## 1. Dataset Purpose & Role

This benchmark dataset (`eval_dataset.json`) provides a standardized, verifiable test suite for quantitatively measuring:
1. **Information Retrieval Quality:** HitRate@K, Mean Reciprocal Rank (MRR@K), and Context Relevance.
2. **Cross-Lingual Retrieval Parity:** Evaluating how accurately regional (Hindi, Kannada, Telugu) and Code-Mixed queries fetch English source documents.
3. **Generation Faithfulness:** Measuring whether synthesized answers are strictly grounded in retrieved citations.
4. **Deterministic Negative Rejection:** Verifying that out-of-corpus queries deterministically return *"Information Not Found"* without fabricating policies.

---

## 2. Dataset Distribution Summary

| Language / Modality | Query Type | Count | Answerable? | Target Documents |
| :--- | :--- | :---: | :---: | :--- |
| **English (`en`)** | Direct Fact Lookup & Constraints | 20 | Yes (100%) | `DOC-ACAD-*`, `DOC-EXAM-*`, `DOC-ATTN-*`, `DOC-SCHOL-*`, `DOC-HOST-*`, `DOC-PLACE-*` |
| **Hindi (`hi`)** | Cross-Lingual Factual QA | 10 | Yes (100%) | English regulatory files (Cross-Lingual Dense Search) |
| **Kannada (`kn`)** | Cross-Lingual Factual QA | 10 | Yes (100%) | English regulatory files (Cross-Lingual Dense Search) |
| **Telugu (`te`)** | Cross-Lingual Factual QA | 10 | Yes (100%) | English regulatory files (Staged Stage 14 Benchmarking) |
| **Code-Mixed** | Romanized Kanglish / Hinglish / Tenglish | 5 | Yes (100%) | English regulatory files (Subword Tokenization) |
| **Negative / Out-of-Corpus** | Unanswerable Distractor Queries | 5 | **No (0%)** | `null` (Tests deterministic negative fallback) |
| **TOTAL BENCHMARK QUERIES** | — | **60** | **55 Yes / 5 No** | **24 Indexed Institutional Documents** |

---

## 3. JSON Schema Specification

```json
{
  "question_id": "Q-EN-001",
  "question": "What is the minimum attendance percentage required in each course?",
  "language": "en",
  "input_type": "text",
  "expected_answer": "A student must maintain a minimum of 75% attendance in each registered course.",
  "acceptable_answer_points": [
    "Minimum attendance requirement is 75%",
    "Applies to individual theory and practical courses"
  ],
  "source_documents": [
    {
      "document_id": "DOC-ATTN-001",
      "page": 1,
      "evidence_summary": "Clause 1.1 states minimum 75% attendance requirement."
    }
  ],
  "question_type": "fact_lookup",
  "category": "attendance",
  "answer_available": true,
  "difficulty": "easy"
}
```

---

## 4. Usage in Automated Evaluation (Stage 14)

The evaluation harness (`scripts/run_evaluation_benchmark.py`) iterates over all 60 queries:
- For `answer_available == true`: Verifies that `expected_doc_id` appears in the Top-$K$ retrieved chunks and checks whether generated answers contain key points from `acceptable_answer_points`.
- For `answer_available == false`: Verifies that similarity scores fall below threshold $\tau$ and the system outputs the deterministic fallback message without hallucinations.
