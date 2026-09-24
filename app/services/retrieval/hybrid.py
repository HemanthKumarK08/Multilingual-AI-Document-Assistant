"""
Multi-Query Reciprocal Rank Fusion (RRF) & Hybrid Score Fusion Module
Implements research-standard Reciprocal Rank Fusion:
RRF_score(d) = sum_{v in variants} sum_{m in {dense, bm25}} (w_v * w_m) / (k + rank_m(d))
with k = 60.
Also provides deterministic linear weighted score fusion for direct two-way combination.
"""

from typing import Dict, List, Optional, Tuple
from app.services.retrieval.constants import DEFAULT_DENSE_WEIGHT, DEFAULT_LEXICAL_WEIGHT
from app.services.retrieval.deduplication import deduplicate_candidates
from app.services.retrieval.models import CandidateChunk, QueryVariant

RRF_K_CONSTANT = 60.0


def reciprocal_rank_fusion(
    ranked_lists: List[Tuple[List[CandidateChunk], float, str]],
    k: float = RRF_K_CONSTANT,
    top_k: Optional[int] = 20,
) -> List[CandidateChunk]:
    """
    Fuses multiple ranked lists using Reciprocal Rank Fusion (RRF).
    
    Args:
        ranked_lists: List of (candidate_list, weight, method_name).
        k: Smoothing constant (default 60).
        top_k: Max candidate chunks to return (default 20).
        
    Returns:
        Deduplicated list of CandidateChunks with calculated `rrf_score` and `hybrid_score`.
    """
    if not ranked_lists:
        return []

    chunk_map: Dict[str, CandidateChunk] = {}
    rrf_scores: Dict[str, float] = {}

    for candidates, weight, method in ranked_lists:
        for rank, cand in enumerate(candidates, start=1):
            cid = cand.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = cand.model_copy(deep=True)
                chunk_map[cid].retrieval_methods = [method]
                rrf_scores[cid] = 0.0
            else:
                existing = chunk_map[cid]
                if method not in existing.retrieval_methods:
                    existing.retrieval_methods.append(method)
                if cand.dense_score is not None:
                    if existing.dense_score is None or cand.dense_score > existing.dense_score:
                        existing.dense_score = cand.dense_score
                if cand.lexical_score is not None:
                    if existing.lexical_score is None or cand.lexical_score > existing.lexical_score:
                        existing.lexical_score = cand.lexical_score
                for src in cand.query_variant_sources:
                    if src not in existing.query_variant_sources:
                        existing.query_variant_sources.append(src)

            # Accumulate weighted RRF score
            rrf_scores[cid] += weight / (k + rank)

    # Normalize RRF scores to [0.0, 1.0] relative to highest observed score
    max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
    if max_rrf <= 0:
        max_rrf = 1.0

    fused_candidates: List[CandidateChunk] = []
    for cid, cand in chunk_map.items():
        raw_rrf = rrf_scores[cid]
        normalized_rrf = round(raw_rrf / max_rrf, 4)
        cand.rrf_score = normalized_rrf
        cand.hybrid_score = normalized_rrf
        fused_candidates.append(cand)

    # Sort descending by rrf_score, then tie-break deterministically by chunk_id
    fused_candidates.sort(
        key=lambda c: (c.rrf_score or 0.0, c.dense_score or 0.0, c.lexical_score or 0.0, c.chunk_id),
        reverse=True
    )

    for idx, cand in enumerate(fused_candidates, start=1):
        cand.rank = idx

    if top_k is not None and top_k > 0:
        return fused_candidates[:top_k]
    return fused_candidates


def fuse_hybrid_scores(
    dense_candidates: List[CandidateChunk],
    lexical_candidates: List[CandidateChunk],
    dense_weight: float = DEFAULT_DENSE_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    top_k: Optional[int] = None,
) -> List[CandidateChunk]:
    """
    Fuses dense and lexical candidates using weighted linear score combination.
    """
    all_candidates = list(dense_candidates) + list(lexical_candidates)
    deduped = deduplicate_candidates(all_candidates)
    
    total_weight = dense_weight + lexical_weight
    if total_weight <= 0:
        total_weight = 1.0
        dense_weight = 0.7
        lexical_weight = 0.3

    for cand in deduped:
        d_score = cand.dense_score if cand.dense_score is not None else 0.0
        l_score = cand.lexical_score if cand.lexical_score is not None else 0.0
        h_score = (dense_weight * d_score + lexical_weight * l_score) / total_weight
        cand.hybrid_score = round(max(0.0, min(1.0, h_score)), 4)

    deduped.sort(key=lambda x: (x.hybrid_score or 0.0, -len(x.text_content), x.chunk_id), reverse=True)

    for rank_idx, cand in enumerate(deduped, start=1):
        cand.rank = rank_idx

    if top_k is not None and top_k > 0:
        return deduped[:top_k]
    return deduped
