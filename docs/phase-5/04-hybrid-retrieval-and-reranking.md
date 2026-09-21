# Phase 5 — Hybrid Retrieval and Deterministic Reranking

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 5 — Retrieval, Reranking, and Grounded RAG Pipeline  
**WBS Stage:** WBS Stage 8 (Retrieval Engine)  
**Date:** 2026-09-12  

---

## 1. Hybrid Score Fusion Strategy

Combining dense vector retrieval and lexical keyword retrieval overcomes vector search limitations on exact numerical constants, proper nouns, and policy clause numbers.

### 1.1. Score Combination
1. **Candidate Union:** Dense candidates ($N_{\text{dense}} \le 12$) and lexical candidates ($N_{\text{lexical}} \le 12$) are combined.
2. **Deduplication by `chunk_id`:** Merges dense and lexical scores into a single unified candidate record.
3. **Linear Fusion Formula:**
   $$\text{hybrid\_score} = \frac{0.70 \cdot s_{\text{dense}} + 0.30 \cdot s_{\text{lexical}}}{0.70 + 0.30}$$

---

## 2. Deterministic Heuristic Reranker

The heuristic reranker refines the top candidate ordering based on lexical term coverage and structural document signals without adding heavy cross-encoder overhead on CPU:

### 2.1. Feature Adjustments
1. **Query Term Coverage Bonus:**
   $$\Delta_{\text{coverage}} = \min\left(0.10, 0.10 \times \frac{|\text{matched\_query\_tokens}|}{|\text{unique\_query\_tokens}|}\right)$$
2. **Exact Query Phrase Match Bonus:**
   $$\Delta_{\text{phrase}} = 0.10 \quad \text{if full query substring exists in chunk text}$$
3. **Section Title Overlap Bonus:**
   $$\Delta_{\text{section}} = 0.05 \quad \text{if query tokens match section heading}$$
4. **Short Content Penalty:**
   $$\Delta_{\text{penalty}} = -0.05 \quad \text{if text length} < 30 \text{ characters}$$

$$\text{rerank\_score} = \max(0.0, \min(1.0, \text{hybrid\_score} + \Delta_{\text{coverage}} + \Delta_{\text{phrase}} + \Delta_{\text{section}} - \Delta_{\text{penalty}}))$$

### 2.2. Deterministic Tie-Breaking
Candidates are sorted by:
`(-rerank_score, -hybrid_score, chunk_id)`
This guarantees 100% reproducible retrieval ranking across identical repeated queries.
