# Phase 1.6 — Golden Evaluation Benchmark Design

## 1. Executive Summary

This document details the design, schema, language distribution, query typology, and evaluation methodology of the **Golden Evaluation Benchmark** (`data/evaluation/eval_dataset.json`) created during Phase 1.6.

The benchmark contains **60 meticulously designed queries** mapped directly to evidence within the Phase 1.5 document corpus. It establishes an immutable ground-truth dataset for evaluating:
1. Retrieval Recall and Precision (Hit Rate@K, MRR@K, nDCG@K).
2. Answer Groundedness and Context Precision (Ragas Faithfulness).
3. Deterministic Out-of-Domain Refusal (Hallucination-risk mitigation).
4. Cross-lingual Query-to-Evidence Alignment across English, Hindi, Kannada, Telugu, and Romanized/Code-mixed inputs.

---

## 2. Benchmark Architecture and Taxonomy

### 2.1 Dataset Composition

```text
Total Queries: 60
├── Answerable Queries (In-Domain): 55 queries (91.7%)
│   ├── English (en):             20 queries (33.3%)
│   ├── Hindi (hi):               10 queries (16.7%)
│   ├── Kannada (kn):             10 queries (16.7%)
│   ├── Telugu (te):              10 queries (16.7%)
│   └── Code-Mixed / Hinglish:     5 queries (8.3%)
└── Unanswerable Queries (Out-of-Domain): 5 queries (8.3%)
    └── Intentionally fabricated / external institutional queries
```

### 2.2 Question Typology Distribution

The benchmark assesses multiple dimensions of reasoning and retrieval complexity:

| Question Type | Count | Description | Target Evaluation Metric |
| :--- | :---: | :--- | :--- |
| `fact_lookup` | 26 | Direct single-fact lookups (e.g. minimum attendance percentage, curfew time) | Recall@3, Precision@1, Exact Match |
| `multi_constraint` | 14 | Queries requiring cross-clause reasoning (e.g. attendance waiver conditions combined with CGPA) | Reranking nDCG@5, Context Precision |
| `cross_lingual_retrieval` | 10 | Non-English queries matching English or vernacular source documents | Multilingual Embedding Cosine Alignment, Cross-lingual MRR |
| `code_mixed_retrieval` | 5 | Romanized / Hinglish queries (e.g. "Attendance kam hone par kya fine lagta hai?") | Subword Tokenization Robustness, Semantic Hit Rate |
| `out_of_domain` | 5 | Queries regarding non-existent policies (e.g. campus pet policy, drone flying) | Negative Rejection Rate, Fallback Adherence (100%) |

---

## 3. Benchmark Schema Specification

The dataset is formatted in JSON according to the following strict schema in [`data/evaluation/eval_dataset.json`](file:///Users/hemanthkumark/College/BIT/AI:Ml/data/evaluation/eval_dataset.json):

```json
{
  "question_id": "string (unique identifier, e.g., EVAL-001, EVAL-UNANSWERABLE-001)",
  "question": "string (the user query)",
  "language": "string (ISO 639-1 code or dialect code: en, hi, kn, te, en-hi-mixed)",
  "input_type": "string (text | voice_transcription)",
  "category": "string (one of the 6 institutional categories or out_of_domain)",
  "difficulty": "string (easy | medium | hard)",
  "question_type": "string (fact_lookup | multi_constraint | cross_lingual_retrieval | code_mixed_retrieval | out_of_domain)",
  "answer_available": "boolean (true if answer is present in the corpus, false otherwise)",
  "expected_answer": "string | null (concise ground-truth reference answer)",
  "acceptable_answer_points": [
    "string (bulleted key factual assertions that must be present in the response)"
  ],
  "source_documents": [
    {
      "document_id": "string (matching valid document_id in corpus manifest)",
      "page_or_section": "string (specific section or paragraph reference)",
      "evidence_summary": "string (verbatim or condensed factual excerpt proving the answer)"
    }
  ]
}
```

---

## 4. Evaluation Methodology and Usage Guidelines

### 4.1 Phase 4 Retrieval Evaluation
Future automated retrieval evaluation scripts will consume `eval_dataset.json` as follows:
1. Pass `question` to the retrieval pipeline (Dense Chroma vector search + Sparse BM25 + Hybrid RRF).
2. Inspect top-$k$ returned document chunks ($k \in \{1, 3, 5, 10\}$).
3. Check if chunk's `document_id` and `section` match any entry in `source_documents`.
4. Calculate:
   - **Hit Rate@K** $= \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{target doc in top-}k)$
   - **MRR@K (Mean Reciprocal Rank)** $= \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_q}$
   - **nDCG@K** (Normalized Discounted Cumulative Gain)

### 4.2 Phase 5 Answer Generation & Groundedness Evaluation
When the LLM generation layer is connected in Phase 5:
1. The model will be provided the retrieved context and user `question`.
2. For `answer_available: true`:
   - Evaluate whether all `acceptable_answer_points` are semantically covered.
   - Run **Ragas Faithfulness** scoring to ensure no ungrounded claims are introduced.
   - Verify citation metadata matches `source_documents.document_id`.
3. For `answer_available: false` (Out-of-Domain):
   - Verify that the model returns the standard fallback message ("I cannot find relevant information in the provided institutional documents...") with 0 hallucinated facts.

---

## 5. Dataset Validation and Integrity

The benchmark has been audited against the physical corpus:
- **100% Referential Integrity:** Every `document_id` referenced in `source_documents` exists in `data/raw/corpus_manifest.json` and has a verified SHA-256 hash.
- **Evidence Verification:** Every evidence excerpt corresponds to active text within the designated document file.
- **Controlled Out-of-Domain Distribution:** Exactly 5 out-of-domain queries exist with `expected_answer: null` and `source_documents: []` to guarantee deterministic rejection testing.
