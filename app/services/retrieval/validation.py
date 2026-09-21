"""
Retrieval Result Validation Module
"""

from typing import List, Tuple
from app.services.retrieval.models import CandidateChunk, RetrievalResult

def validate_candidate_chunk(chunk: CandidateChunk) -> Tuple[bool, List[str]]:
    """Validates individual candidate chunk schema and contents."""
    errors = []
    if not chunk.chunk_id or not chunk.chunk_id.strip():
        errors.append("Candidate chunk missing valid chunk_id.")
    if not chunk.doc_id or not chunk.doc_id.strip():
        errors.append("Candidate chunk missing valid doc_id.")
    if not chunk.text_content or not chunk.text_content.strip():
        errors.append(f"Candidate chunk [{chunk.chunk_id}] has empty text content.")
    if chunk.page_number < 1:
        errors.append(f"Candidate chunk [{chunk.chunk_id}] has invalid page_number {chunk.page_number}.")
    
    # Validate score bounds
    for score_name, score_val in [
        ("dense_score", chunk.dense_score),
        ("lexical_score", chunk.lexical_score),
        ("hybrid_score", chunk.hybrid_score),
        ("rerank_score", chunk.rerank_score),
    ]:
        if score_val is not None and not (0.0 <= score_val <= 1.0):
            errors.append(f"Score {score_name}={score_val} out of valid bounds [0.0, 1.0].")

    return len(errors) == 0, errors

def validate_retrieval_result(result: RetrievalResult) -> Tuple[bool, List[str]]:
    """Validates the overall retrieval result object."""
    errors = []
    if not result.query or not result.query.raw_query:
        errors.append("Retrieval result missing valid query.")
    
    for cand in result.candidates:
        valid, cand_errors = validate_candidate_chunk(cand)
        if not valid:
            errors.extend(cand_errors)

    return len(errors) == 0, errors
