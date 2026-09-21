# Multilingual Evaluation Methodology and Benchmark Results

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 6 — Multilingual and Code-Mixed Processing Optimization  
**Module:** `scripts/evaluate_retrieval.py`  

---

## 1. Evaluation Methodology

The Phase 6 evaluation harness assesses retrieval performance across all 60 golden benchmark questions in `data/evaluation/eval_dataset.json` (55 in-domain queries and 5 out-of-domain unanswerable queries).

### Multi-Tier Candidate Matching
To evaluate cross-lingual retrieval rigorously without relying solely on literal Indic-token matching against English documents, candidates are evaluated against three objective ground-truth criteria:
1. **Document ID Match:** Candidate `doc_id` matches the golden `source_documents` requirement (e.g. `DOC-ATTN-001`, `DOC-HOST-001`).
2. **Chunk ID Match:** Candidate `chunk_id` matches the primary golden chunk identifier.
3. **Acceptable Answer Points Keyword Overlap:** Candidate text contains essential factual terms defined in the benchmark ground truth.

---

## 2. Reconciled Retrieval Benchmark Results

### 2.1. Overall Comparison (N=55 In-Domain Queries)

| Metric | Phase 5 Reported Baseline | Corrected Phase 5 Baseline | Phase 6 Multi-Variant Pipeline | Improvement vs Corrected Baseline |
|---|---:|---:|---:|---:|
| **Hit Rate @ 1** | 56.36% (31/55) | 89.09% (49/55) | **94.55%** (52/55) | **+5.46% absolute** (+6.13% rel) |
| **Hit Rate @ 3** | 67.27% (37/55) | 100.00% (55/55) | **100.00%** (55/55) | **0.00%** |
| **Hit Rate @ 5** | 67.27% (37/55) | 100.00% (55/55) | **100.00%** (55/55) | **0.00%** |
| **Mean Reciprocal Rank (MRR)** | 0.6152 | 0.9394 | **0.9636** | **+0.0242 absolute** |

---

## 3. Disjoint In-Domain Category Partition (N=55)

| Category / Partition | Total In-Domain | Hit @ 1 | Hit @ 5 | Hit Rate @ 1 | Hit Rate @ 5 | MRR |
|---|:---:|:---:|:---:|---:|---:|---:|
| **English (In-Domain)** | 20 | 20 | 20 | 100.00% | 100.00% | 1.0000 |
| **Hindi Native Script (Devanagari)** | 10 | 9 | 10 | 90.00% | 100.00% | 0.9333 |
| **Kannada Native Script (Kannada)** | 10 | 9 | 10 | 90.00% | 100.00% | 0.9333 |
| **Telugu Native Script (Telugu)** | 10 | 10 | 10 | 100.00% | 100.00% | 1.0000 |
| **Romanized / Code-Mixed (Latin)** | 5 | 4 | 5 | 80.00% | 100.00% | 0.8667 |
| **Total In-Domain** | **55** | **52** | **55** | **94.55%** | **100.00%** | **0.9636** |
| **Out-of-Domain (Fallback Evaluated)** | **5** | N/A | N/A | N/A | N/A | N/A |
| **Total Benchmark Dataset** | **60** | — | — | — | — | — |

---

## 4. Controlled 5-Stage Ablation Study

Executed using `python scripts/evaluate_retrieval.py --ablation` on the exact 55 in-domain benchmark dataset:

| Configuration | Benchmark | Hit Rate@1 | Hit Rate@5 | MRR | Avg Variants | Warm Latency |
|---|---:|---:|---:|---:|---:|---:|
| **1. Baseline (Phase 5 - No Expansion)** | 55 | 89.09% | 100.00% | 0.9394 | 1.00 | ~7.6 ms |
| **2. Baseline + Script Normalization** | 55 | 89.09% | 100.00% | 0.9394 | 1.00 | ~7.7 ms |
| **3. Baseline + Domain Query Expansion** | 55 | 89.09% | 100.00% | 0.9394 | 1.00 | ~8.0 ms |
| **4. Baseline + Transliteration Variants** | 55 | 94.55% | 100.00% | 0.9636 | 2.98 | ~21.6 ms |
| **5. Full Phase 6 Multi-Variant Pipeline** | **55** | **94.55%** | **100.00%** | **0.9636** | **2.98** | **~24.5 ms** |

### Key Findings
- Adding transliteration and cross-lingual query variants increased top-rank accuracy (Hit Rate@1) from 89.09% to **94.55%**, with MRR reaching **0.9636**.
- Hit Rate@5 reached **100.00%** (55/55) across all in-domain cross-lingual queries.
- Warm latency remains ~24.5 ms on CPU, well within the 100 ms budget constraint.

