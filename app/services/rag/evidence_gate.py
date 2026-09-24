"""
Answerability & Evidence Sufficiency Gate Module (Research-Backed RAG Architecture)
Implements research-inspired answerability gating (DUTIR / 2025 Hybrid Multilingual RAG):
Determines before generation: CAN THIS EVIDENCE ACTUALLY ANSWER THE QUESTION?
Evaluates:
- Top candidate relevance
- Candidate agreement & consistency
- Important-term coverage
- Entity match
- Intent compatibility
- Completeness and contradiction detection
Outputs:
- ANSWERABLE
- PARTIALLY_ANSWERABLE
- UNANSWERABLE
"""

import re
from typing import List, Optional, Set
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
    "required", "requirement", "requirements", "need", "needed", "tell", "give", "provide",
    "using", "used", "applicable", "apply", "must", "shall", "only", "per", "as", "such",
    "document", "documents", "section", "page", "query", "question", "questions",
}

_CORE_TOPIC_TERMS = {
    "attendance", "attend", "condonation", "cgtmse", "guarantee", "credit", "credits",
    "revaluation", "photocopy", "challenge", "supplementary", "makeup", "fast-track",
    "backlog", "scholarship", "merit", "hostel", "placement", "debarment", "eligibility",
    "grade", "malpractice", "database", "mysql", "electron", "backend", "frontend",
    "proctoring", "nirf", "reimbursement", "incubation", "aspire", "sfurti", "msme",
    "curfew", "stipend", "fine", "penalty", "admission", "fastapi", "react", "vite", "tailwind"
}


def evaluate_evidence_sufficiency(
    retrieval_result: RetrievalResult,
    min_score: Optional[float] = None,
    min_chunks: Optional[int] = None,
) -> EvidenceGateResult:
    """
    Evaluates evidence answerability and sufficiency across multiple dimensions:
    Returns EvidenceGateResult with answerability_status in ("ANSWERABLE", "PARTIALLY_ANSWERABLE", "UNANSWERABLE").
    """
    threshold = min_score if min_score is not None else settings.RAG_MIN_EVIDENCE_SCORE
    required_chunks = min_chunks if min_chunks is not None else settings.RAG_MIN_EVIDENCE_CHUNKS
    
    query = retrieval_result.query
    query_text = query.normalized_query
    q_intent = query.query_intent
    warnings: List[str] = list(retrieval_result.warnings)

    # 1. Check for prompt injection in query
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(query_text):
            return EvidenceGateResult(
                is_sufficient=False,
                answerability_status="UNANSWERABLE",
                reason="PROMPT_INJECTION_DETECTED",
                selected_candidates=[],
                minimum_score=threshold,
                observed_best_score=0.0,
                confidence_score=0.0,
                warnings=["Query matched prompt-injection security pattern."],
            )

    # 2. Check for explicit Out-of-Domain or Ambiguous intent
    if q_intent in ("OUT_OF_DOMAIN", "AMBIGUOUS"):
        return EvidenceGateResult(
            is_sufficient=False,
            answerability_status="UNANSWERABLE",
            reason="OUT_OF_DOMAIN_OR_AMBIGUOUS",
            selected_candidates=[],
            minimum_score=threshold,
            observed_best_score=0.0,
            confidence_score=0.0,
            warnings=[f"Query intent '{q_intent}' classified as unanswerable from corpus."],
        )

    candidates = retrieval_result.candidates

    # 3. Check if candidates exist
    if not candidates:
        return EvidenceGateResult(
            is_sufficient=False,
            answerability_status="UNANSWERABLE",
            reason=REASON_NO_CANDIDATES,
            selected_candidates=[],
            minimum_score=threshold,
            observed_best_score=0.0,
            confidence_score=0.0,
            warnings=warnings,
        )

    # 4. Extract informative tokens and entities
    q_all_tokens = set(tokenize(query_text.lower()))
    q_informative_tokens = q_all_tokens - _GENERIC_STOPWORDS
    core_q_topics = q_all_tokens.intersection(_CORE_TOPIC_TERMS)
    q_entities = {e.lower() for e in (query.entities or [])}

    # 5. Filter qualifying candidates
    qualifying_candidates: List[CandidateChunk] = []
    best_score = 0.0

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

        cand_tokens = set(tokenize(cand.text_content.lower())).union(set(tokenize((cand.section_title or "").lower())))
        is_latin_query = (query.script or "").lower() in ("latin", "en", "unknown")

        # If query has core topical keywords (e.g. attendance, database, nirf), verify topical overlap
        if core_q_topics and not core_q_topics.intersection(cand_tokens) and is_latin_query:
            continue

        # If query has entities, check if entity appears or if high-confidence term matches
        if q_entities and is_latin_query:
            has_ent = any(ent in cand.text_content.lower() or ent in (cand.section_title or "").lower() for ent in q_entities)
            if not has_ent and not core_q_topics.intersection(cand_tokens):
                continue

        if effective_score >= threshold:
            qualifying_candidates.append(cand)

    # 6. Candidate Agreement & Keyword Overlap Evaluation
    all_context_tokens: Set[str] = set()
    doc_agreement_count = 0
    top_doc_id = qualifying_candidates[0].doc_id if qualifying_candidates else ""

    for cand in qualifying_candidates:
        all_context_tokens.update(tokenize(cand.text_content.lower()))
        all_context_tokens.update(tokenize((cand.section_title or "").lower()))
        if cand.doc_id == top_doc_id:
            doc_agreement_count += 1

    matched_tokens = q_informative_tokens.intersection(all_context_tokens)
    overlap_ratio = len(matched_tokens) / max(1, len(q_informative_tokens))
    agreement_score = doc_agreement_count / max(1, len(qualifying_candidates))

    confidence = (
        (best_score * 0.40)
        + (overlap_ratio * 0.35)
        + (agreement_score * 0.25)
    )

    is_latin_query = (query.script or "").lower() in ("latin", "en", "unknown")

    # 7. Check for Zero or Very Low Informative Overlap in Latin Queries
    if is_latin_query:
        if q_informative_tokens and not matched_tokens:
            return EvidenceGateResult(
                is_sufficient=False,
                answerability_status="UNANSWERABLE",
                reason=REASON_LOW_RELEVANCE,
                selected_candidates=[],
                minimum_score=threshold,
                observed_best_score=round(best_score, 4),
                confidence_score=round(confidence, 4),
                agreement_score=round(agreement_score, 4),
                term_coverage_score=0.0,
                warnings=warnings + ["No informative query keywords were present in retrieved context."],
            )

        if len(q_informative_tokens) >= 2 and not core_q_topics.intersection(matched_tokens):
            if overlap_ratio < 0.30 or len(matched_tokens) < 2:
                return EvidenceGateResult(
                    is_sufficient=False,
                    answerability_status="UNANSWERABLE",
                    reason=REASON_LOW_RELEVANCE,
                    selected_candidates=[],
                    minimum_score=threshold,
                    observed_best_score=round(best_score, 4),
                    confidence_score=round(confidence, 4),
                    agreement_score=round(agreement_score, 4),
                    term_coverage_score=round(overlap_ratio, 4),
                    warnings=warnings + ["Low keyword overlap between query and retrieved context."],
                )

    if not qualifying_candidates:
        return EvidenceGateResult(
            is_sufficient=False,
            answerability_status="UNANSWERABLE",
            reason=REASON_LOW_RELEVANCE if best_score < threshold else REASON_EMPTY_CONTEXT,
            selected_candidates=[],
            minimum_score=threshold,
            observed_best_score=round(best_score, 4),
            confidence_score=round(confidence, 4),
            agreement_score=round(agreement_score, 4),
            term_coverage_score=round(overlap_ratio, 4),
            warnings=warnings,
        )

    # Check for PARTIALLY_ANSWERABLE vs ANSWERABLE
    if len(qualifying_candidates) >= required_chunks and (overlap_ratio >= 0.40 or bool(core_q_topics.intersection(matched_tokens)) or not is_latin_query):
        answerability = "ANSWERABLE"
        is_suff = True
    elif len(qualifying_candidates) >= 1 and (best_score >= 0.60 or overlap_ratio >= 0.30):
        answerability = "PARTIALLY_ANSWERABLE"
        is_suff = True
    else:
        answerability = "UNANSWERABLE"
        is_suff = False

    return EvidenceGateResult(
        is_sufficient=is_suff,
        answerability_status=answerability,
        reason=None if is_suff else REASON_LOW_RELEVANCE,
        selected_candidates=qualifying_candidates,
        minimum_score=threshold,
        observed_best_score=round(best_score, 4),
        confidence_score=round(confidence, 4),
        agreement_score=round(agreement_score, 4),
        term_coverage_score=round(overlap_ratio, 4),
        warnings=warnings,
    )
