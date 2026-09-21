# Query-Variant Retrieval Fusion and Ranking

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 6 — Multilingual and Code-Mixed Processing Optimization  
**Module:** `app/services/retrieval/coordinator.py`  

---

## 1. Overview

In Phase 6, the `RetrievalCoordinator` coordinates multi-variant retrieval across both dense (ChromaDB) and sparse (in-memory BM25) search engines, merging retrieved chunk candidates with priority weighting.

```text
User Query
    │
    ▼
[Query Processing] ──► [Query Expansion & Transliteration]
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      [Variant 1 (Original)]       [Variants 2-4 (Expanded)]
              │                           │
       Dense + BM25                Dense + BM25
              │                           │
              └─────────────┬─────────────┘
                            ▼
           [Priority-Weighted Candidate Fusion]
                   (Grouped by chunk_id)
                            │
                            ▼
              [Deterministic Heuristic Reranker]
                            │
                            ▼
              [Final Top-K Candidate Chunks]
```

---

## 2. Priority-Weighted Candidate Fusion Algorithm

1. **Multi-Variant Execution:** For each variant $v \in V$ with weight $w_v \in [0.75, 1.0]$:
   - Dense retrieval queries ChromaDB for top $k_d$ candidates ($k_d = 12$ for primary, $k_d = 8$ for variants).
   - Lexical retrieval queries BM25 index for top $k_l$ candidates ($k_l = 12$ for primary, $k_l = 8$ for variants).
2. **Keyed Deduplication by Chunk ID:**
   - Candidate chunks are keyed uniquely by `chunk_id`.
   - Adjusted dense score: $s_d(c, v) = \text{cand.dense\_score} \times w_v$
   - Adjusted lexical score: $s_l(c, v) = \text{cand.lexical\_score} \times w_v$
   - If a chunk is retrieved across multiple variants, the maximum weighted score is preserved:
     $$S_d(c) = \max_{v} \left( s_d(c, v) \right), \quad S_l(c) = \max_{v} \left( s_l(c, v) \right)$$
3. **Hybrid Score Calculation:**
   $$\text{hybrid\_score}(c) = (0.70 \times S_d(c)) + (0.30 \times S_l(c))$$
4. **Candidate Capping:** The candidate pool is sorted and capped at 30 chunks prior to reranking.
5. **Deterministic Heuristic Reranking:** Applies phrase boost ($+0.12$), term coverage boost ($+0.08$), and section title match ($+0.05$) based on the user's primary query.
6. **Top-K Selection:** Selects the top $K=5$ candidates.

---

## 3. Provenance and Metadata Invariance

During multi-variant candidate fusion:
- `chunk_id`, `doc_id`, `filename`, `page_number`, `source_start_offset`, `source_end_offset`, and `file_hash_sha256` are strictly preserved from the Phase 4 vector index.
- Candidate provenance records `query_variant_sources` (e.g. `["original", "indic_translation"]`) for transparency and diagnostic auditing.
- No synthetic text or translation artifacts are injected into chunk text bodies.
