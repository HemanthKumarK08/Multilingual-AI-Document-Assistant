# Evaluation Strategy & Benchmarking Framework

This document defines the quantitative metrics, benchmark datasets, evaluation protocols, and automated testing harnesses used to scientifically measure the performance of the **Multilingual AI Document Assistant with Big Data Analytics**.

---

## 1. Information Retrieval (IR) Evaluation Metrics

Retrieval quality measures the system's ability to fetch the exact ground-truth document chunk containing the answer from among thousands of indexed chunks.

| Metric | Formula / Definition | Target Benchmark | Academic Purpose |
| :--- | :--- | :---: | :--- |
| **Hit Rate @ K** ($K=3, 5$) | $\text{HitRate@}K = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \mathbb{I}(\text{ground\_truth\_chunk} \in \text{Top-}K)$ | $\ge 85\%$ (@ $K=5$) | Verifies whether the correct policy clause is included in the LLM context window. |
| **Mean Reciprocal Rank (MRR@K)** | $\text{MRR@}K = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \frac{1}{\text{rank}_q}$ | $\ge 0.70$ | Measures how high the relevant chunk is ranked in the retrieved candidate list. |
| **Context Relevance** | Ratio of retrieved text characters directly pertinent to the query vs total context characters. | $\ge 70\%$ | Prevents bloated context windows that confuse the generation model. |
| **Cross-Lingual Retrieval Parity** | $\frac{\text{HitRate@5}(\text{Indic Queries})}{\text{HitRate@5}(\text{English Queries})}$ | $\ge 0.80$ | Quantifies how effectively Kannada/Telugu/Hindi queries retrieve English documents compared to native English queries. |

---

## 2. Generation & RAG Quality Metrics

Generation quality evaluates whether the synthesized response is factually grounded in the retrieved chunks, minimizes hallucination risk, and accurately cites official sources.

| Evaluation Criterion | Measurement Protocol | Proposed Target Score |
| :--- | :--- | :---: |
| **Faithfulness / Grounding** | Proportion of factual claims in the answer that are strictly supported by cited source chunks (verified via LLM-as-a-Judge / heuristic fact verification). | $\ge 95\%$ |
| **Citation Accuracy** | Verification that the cited `[Document Name, Page Number]` matches the actual location of the evidence in the source PDF. | $\ge 98\%$ |
| **Negative Rejection Rate (Negative Queries)** | Frequency with which out-of-domain or unanswerable questions correctly trigger *"Information Not Found"* without fabricating policies. | $100\%$ |
| **Answer Completeness** | Degree to which all sub-parts of the user query are addressed based on available context. | $\ge 90\%$ |
| **Linguistic Naturalness (Indic)** | Human review / qualitative rating (1–5 scale) for Kannada, Hindi, and Telugu responses. | $\ge 4.0 / 5.0$ |

---

## 3. System Performance & Computational Profiling (Proposed Targets)

| Performance Dimension | Benchmark Method | Proposed Target (Laptop Baseline) |
| :--- | :--- | :---: |
| **Query Preprocessing Latency** | Timer probe on normalization and script detection. | $\text{p50} \le 20\text{ ms} \text{ / } \text{p95} \le 50\text{ ms}$ |
| **Embedding Generation Latency** | Timer probe on CPU forward pass (`multilingual-e5-small`). | $\text{p50} \le 60\text{ ms} \text{ / } \text{p95} \le 120\text{ ms}$ |
| **Vector Search Latency (ChromaDB)**| Timer probe on cosine similarity retrieval over 5,000 chunks. | $\text{p50} \le 50\text{ ms} \text{ / } \text{p95} \le 150\text{ ms}$ |
| **LLM Generation Latency (API)** | Timer probe on external API response (Gemini Flash). | $\text{p50} \le 1.5\text{ s} \text{ / } \text{p95} \le 3.0\text{ s}$ |
| **End-to-End Latency (API Mode)** | Total roundtrip time from request dispatch to UI render. | $\text{p50} \le 2.0\text{ s} \text{ / } \text{p95} \le 3.5\text{ s}$ |
| **Document Ingestion Throughput** | Text extraction + embedding throughput on 20-page PDF. | $\ge 2.0\text{ pages/sec}$ |
| **PySpark ETL Execution Time** | Runtime of full aggregation job on 50,000 JSONL log events. | $\le 12.0\text{ s}$ |
| **Peak Application RAM Footprint** | Monitored via `psutil` during combined RAG query + PySpark job. | $\le 4.5\text{ GB}$ |

---

## 4. Benchmark Golden Dataset Structure (`eval_dataset.json`)

```json
[
  {
    "query_id": "eval_q01",
    "language": "en",
    "query_text": "What is the minimum attendance required to appear for semester end exams?",
    "category": "Academic Regulations",
    "expected_doc_id": "doc_academic_regulations_2024",
    "expected_page": 4,
    "expected_chunk_snippet": "A student must maintain a minimum of 75% attendance in each registered course...",
    "expected_answer_keywords": ["75%", "attendance", "semester end", "condonation"],
    "is_answerable": true
  },
  {
    "query_id": "eval_q12",
    "language": "kn",
    "query_text": "ಹಾಸ್ಟೆಲ್ ಮರು-ಪ್ರವೇಶಕ್ಕೆ ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?",
    "category": "Hostel & Campus Life",
    "expected_doc_id": "doc_hostel_rules_2024",
    "expected_page": 2,
    "expected_chunk_snippet": "Hostel re-admission requires an overall academic attendance of not less than 75%...",
    "expected_answer_keywords": ["75%", "ಹಾಜರಾತಿ", "ಹಾಸ್ಟೆಲ್"],
    "is_answerable": true
  },
  {
    "query_id": "eval_q55",
    "language": "en",
    "query_text": "What is the hostel mess menu on Sunday for Marine Engineering students?",
    "category": "Hostel & Campus Life",
    "expected_doc_id": null,
    "expected_page": null,
    "expected_chunk_snippet": null,
    "expected_answer_keywords": ["not available", "not found"],
    "is_answerable": false
  }
]
```

---

## 5. Automated Evaluation Harness Implementation Plan

An offline evaluation script (`scripts/run_evaluation_benchmark.py`) will automate testing:
1. Iterates through all test queries in `eval_dataset.json`.
2. Sends queries through the retrieval pipeline and records Top-$K$ retrieved chunks.
3. Computes automated HitRate@K, MRR@K, and Latency.
4. Passes retrieved context to the generation layer and validates citation accuracy and negative rejection.
5. Exports a comprehensive Markdown/LaTeX evaluation table suitable for inclusion directly in the MCA academic project report and defense presentation.
