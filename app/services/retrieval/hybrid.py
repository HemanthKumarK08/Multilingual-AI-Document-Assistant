"""
Hybrid Retrieval Score Fusion Module
"""

from typing import List, Optional
from app.services.retrieval.constants import DEFAULT_DENSE_WEIGHT, DEFAULT_LEXICAL_WEIGHT
from app.services.retrieval.deduplication import deduplicate_candidates
from app.services.retrieval.models import CandidateChunk

def fuse_hybrid_scores(
    dense_candidates: List[CandidateChunk],
    lexical_candidates: List[CandidateChunk],
    dense_weight: float = DEFAULT_DENSE_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    top_k: Optional[int] = None,
) -> List[CandidateChunk]:
    """
    Fuses dense and lexical candidates using weighted linear score combination.
    
    Formula:
        hybrid_score = (dense_weight * dense_score + lexical_weight * lexical_score) / (dense_weight + lexical_weight)
        
    Candidate deduplication is performed by chunk_id. Ties broken deterministically by chunk_id.
    """
    # Combine candidate lists
    all_candidates = list(dense_candidates) + list(lexical_candidates)
    
    # Deduplicate and merge components
    deduped = deduplicate_candidates(all_candidates)
    
    total_weight = dense_weight + lexical_weight
    if total_weight <= 0:
        total_weight = 1.0
        dense_weight = 0.7
        lexical_weight = 0.3

    for cand in deduped:
        d_score = cand.dense_score if cand.dense_score is not None else 0.0
        l_score = cand.lexical_score if cand.lexical_score is not None else 0.0
        
        # Linear weighted score
        h_score = (dense_weight * d_score + lexical_weight * l_score) / total_weight
        cand.hybrid_score = round(max(0.0, min(1.0, h_score)), 4)

    # Sort descending by hybrid_score, break ties deterministically with chunk_id
    deduped.sort(key=lambda x: (x.hybrid_score or 0.0, -len(x.text_content), x.chunk_id), reverse=True)

    # Re-assign ranks
    for rank_idx, cand in enumerate(deduped, start=1):
        cand.rank = rank_idx

    if top_k is not None and top_k > 0:
        return deduped[:top_k]
    return deduped
