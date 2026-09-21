"""
Candidate Deduplication Module
"""

from typing import Dict, List
from app.core.logging import logger
from app.services.retrieval.models import CandidateChunk

def deduplicate_candidates(candidates: List[CandidateChunk]) -> List[CandidateChunk]:
    """
    Deduplicates candidates by chunk_id while merging scores and retrieval method provenance.
    Preserves first-seen candidate metadata deterministically.
    """
    if not candidates:
        return []

    merged_map: Dict[str, CandidateChunk] = {}

    for cand in candidates:
        cid = cand.chunk_id
        if cid not in merged_map:
            # Clone candidate
            merged_map[cid] = cand.model_copy(deep=True)
        else:
            existing = merged_map[cid]
            # Merge dense score if not present
            if existing.dense_score is None and cand.dense_score is not None:
                existing.dense_score = cand.dense_score
            elif existing.dense_score is not None and cand.dense_score is not None:
                existing.dense_score = max(existing.dense_score, cand.dense_score)

            # Merge lexical score if not present
            if existing.lexical_score is None and cand.lexical_score is not None:
                existing.lexical_score = cand.lexical_score
            elif existing.lexical_score is not None and cand.lexical_score is not None:
                existing.lexical_score = max(existing.lexical_score, cand.lexical_score)

            # Merge retrieval methods
            for method in cand.retrieval_methods:
                if method not in existing.retrieval_methods:
                    existing.retrieval_methods.append(method)

            # Check for conflicting metadata and log if needed
            if existing.doc_id != cand.doc_id:
                logger.warning(
                    f"Metadata conflict for chunk_id [{cid}]: doc_id '{existing.doc_id}' vs '{cand.doc_id}'. Retaining first."
                )

    return list(merged_map.values())
