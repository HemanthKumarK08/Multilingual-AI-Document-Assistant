import re
from typing import List, Optional
from app.core.config import settings
from app.services.rag.constants import (
    REASON_EMPTY_CONTEXT,
    REASON_LOW_RELEVANCE,
    REASON_MISSING_METADATA,
    REASON_NO_CANDIDATES,
)
from app.services.rag.models import EvidenceGateResult
from app.services.retrieval.lexical_retriever import tokenize
from app.services.retrieval.models import CandidateChunk, RetrievalResult

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(prior|previous)\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?(rules|documentation|system)", re.I),
    re.compile(r"system\s+(override|prompt)", re.I),
    re.compile(r"admin\s+access\s+granted", re.I),
]

_GENERIC_STOPWORDS = {
    "what", "is", "the", "in", "for", "to", "of", "and", "a", "an", "on", "are",
    "how", "do", "does", "did", "explain", "about", "which", "where", "can", "be",
    "who", "whom", "whose", "when", "why", "won", "was", "were", "been", "have", "has",
    "policy", "guidelines", "rules", "system", "campus", "college", "details",
    "student", "students", "faculty", "staff", "university", "department",
}


def evaluate_evidence_sufficiency(
    retrieval_result: RetrievalResult,
    min_score: Optional[float] = None,
    min_chunks: Optional[int] = None,
) -> EvidenceGateResult:
    """
    Evaluates whether retrieved candidates meet the strict evidence criteria for grounded answering.
    """
    threshold = min_score if min_score is not None else settings.RAG_MIN_EVIDENCE_SCORE
    required_chunks = min_chunks if min_chunks is not None else settings.RAG_MIN_EVIDENCE_CHUNKS
    
    query_text = retrieval_result.query.normalized_query
    warnings: List[str] = list(retrieval_result.warnings)

    # 1. Check for prompt injection in query
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(query_text):
            return EvidenceGateResult(
                is_sufficient=False,
                reason="PROMPT_INJECTION_DETECTED",
                selected_candidates=[],
                minimum_score=threshold,
                observed_best_score=0.0,
                warnings=["Query matched prompt-injection security pattern."],
            )

    candidates = retrieval_result.candidates

    # 2. Check if candidates exist
    if not candidates:
        return EvidenceGateResult(
            is_sufficient=False,
            reason=REASON_NO_CANDIDATES,
            selected_candidates=[],
            minimum_score=threshold,
            observed_best_score=0.0,
            warnings=warnings,
        )

    # 3. Check scores and filter candidates meeting minimum relevance threshold
    qualifying_candidates: List[CandidateChunk] = []
    best_score = 0.0

    # Extract informative query tokens
    q_tokens = set(tokenize(query_text)) - _GENERIC_STOPWORDS

    for cand in candidates:
        effective_score = cand.rerank_score or cand.hybrid_score or cand.dense_score or cand.lexical_score or 0.0
        if effective_score > best_score:
            best_score = effective_score
        
        # Check text validity
        if not cand.text_content or not cand.text_content.strip():
            warnings.append(f"Candidate {cand.chunk_id} has empty text content.")
            continue

        # Check metadata validity
        if not cand.doc_id or not cand.filename or cand.page_number < 1:
            warnings.append(f"Candidate {cand.chunk_id} missing critical metadata attributes.")
            continue

        if effective_score >= threshold:
            qualifying_candidates.append(cand)

    # 4. Check if candidates have meaningful content overlap when specific keywords were queried in Latin script
    is_latin_query = retrieval_result.query.script == "Latin"
    if is_latin_query and qualifying_candidates and q_tokens:
        all_context_tokens = set()
        for cand in qualifying_candidates:
            all_context_tokens.update(tokenize(cand.text_content))
            all_context_tokens.update(tokenize(cand.section_title))
        
        # If query has substantial domain tokens (e.g. cryogenics, saturn, pet unicorn), evaluate coverage
        matched_tokens = q_tokens.intersection(all_context_tokens)
        overlap_ratio = len(matched_tokens) / len(q_tokens) if q_tokens else 0.0

        if not matched_tokens and len(q_tokens) >= 1:
            return EvidenceGateResult(
                is_sufficient=False,
                reason=REASON_LOW_RELEVANCE,
                selected_candidates=[],
                minimum_score=threshold,
                observed_best_score=round(best_score, 4),
                warnings=warnings + ["No informative query keywords were present in retrieved context."],
            )
        elif len(q_tokens) >= 3 and len(matched_tokens) < 2 and overlap_ratio < 0.30:
            return EvidenceGateResult(
                is_sufficient=False,
                reason=REASON_LOW_RELEVANCE,
                selected_candidates=[],
                minimum_score=threshold,
                observed_best_score=round(best_score, 4),
                warnings=warnings + ["Low keyword overlap between query and retrieved candidates."],
            )

    # 5. Check if qualifying candidates meet min_chunks
    if len(qualifying_candidates) < required_chunks:
        return EvidenceGateResult(
            is_sufficient=False,
            reason=REASON_LOW_RELEVANCE if best_score < threshold else REASON_EMPTY_CONTEXT,
            selected_candidates=[],
            minimum_score=threshold,
            observed_best_score=round(best_score, 4),
            warnings=warnings,
        )

    return EvidenceGateResult(
        is_sufficient=True,
        reason=None,
        selected_candidates=qualifying_candidates,
        minimum_score=threshold,
        observed_best_score=round(best_score, 4),
        warnings=warnings,
    )
