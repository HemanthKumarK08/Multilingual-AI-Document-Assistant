"""
Candidate Relevance & Deterministic Reranker Module (Research-Backed RAG Architecture)
Implements research-inspired candidate relevance evaluation:
Calculates dense_score, lexical_score, rrf_score, entity_match, important_term_coverage,
query_intent_match, and document_scope_match.
Prevents generic words (like "required", "student", "rules") from dominating topical matching.
"""

import re
from typing import List, Optional, Set
from app.services.retrieval.lexical_retriever import tokenize
from app.services.retrieval.models import CandidateChunk, ProcessedQuery

_GENERIC_MODIFIERS = {
    'what', 'is', 'the', 'in', 'for', 'to', 'of', 'and', 'a', 'an', 'on', 'are',
    'how', 'do', 'does', 'did', 'explain', 'about', 'which', 'where', 'can', 'be',
    'who', 'whom', 'whose', 'when', 'why', 'won', 'was', 'were', 'been', 'have', 'has',
    'tell', 'me', 'used', 'with', 'from', 'at', 'by', 'use', 'using', 'mentioned',
    'any', 'some', 'give', 'detail', 'details', 'system', 'platform', 'student',
    'students', 'faculty', 'shall', 'must', 'only', 'per', 'as', 'such', 'required',
    'requirement', 'requirements', 'need', 'needed', 'rules', 'rule', 'guidelines',
    'guideline', 'policy', 'applicable', 'apply', 'instruction', 'instructions', 'procedure',
    'course', 'courses', 'registered', 'registered courses'
}

_CORE_DOMAIN_TERMS = {
    'database', 'mysql', 'backend', 'frontend', 'technology', 'technologies', 'stack',
    'proctoring', 'security', 'desktop', 'electron', 'services', 'attendance',
    'condonation', 'credit', 'credits', 'revaluation', 'photocopy', 'challenge',
    'supplementary', 'makeup', 'fast-track', 'backlog', 'scholarship', 'merit',
    'hostel', 'placement', 'debarment', 'eligibility', 'grade', 'malpractice',
    'express', 'jwt', 'rbac', 'cloudflare', 'gemini', 'openai', 'html5', 'css3',
    'javascript', 'python', 'vision', 'proctor', 'cgtmse', 'guarantee', 'scheme',
    'msme', 'website', 'portal', 'url', 'nirf', 'fee', 'fees', 'curfew', 'deposit',
    'caution', 'stipend', 'shortage', '75%', '65%', '88', 'distinction', 'cgpa'
}


def stem_term(t: str) -> str:
    """Simple inflection normalizer for matching plurals and verb forms."""
    if t.endswith('ies') and len(t) > 4:
        return t[:-3] + 'y'
    if t.endswith('es') and len(t) > 3:
        return t[:-2]
    if t.endswith('s') and not t.endswith('ss') and len(t) > 2:
        return t[:-1]
    return t


def heuristic_rerank(
    query: ProcessedQuery,
    candidates: List[CandidateChunk],
    top_k: Optional[int] = None,
) -> List[CandidateChunk]:
    """
    Applies multi-dimensional candidate relevance evaluation:
    - Entity Match
    - Core Informative Term Coverage (excluding generic modifiers)
    - Intent Compatibility Match (Numerical, URL/Where-to, Policy, Definition)
    - Section / Document Scope Match
    - Boundary Continuity & Content Quality
    """
    if not candidates:
        return []

    q_text = query.normalized_query.lower()
    raw_q_tokens = tokenize(query.normalized_query.lower())
    
    # 1. Distinguish between core topic tokens and generic modifiers
    core_q_tokens = [t for t in raw_q_tokens if t not in _GENERIC_MODIFIERS]
    if not core_q_tokens:
        core_q_tokens = raw_q_tokens

    core_q_stems = {stem_term(t) for t in core_q_tokens} | set(core_q_tokens)
    all_q_stems = {stem_term(t) for t in raw_q_tokens} | set(raw_q_tokens)
    total_core = max(1, len(core_q_tokens))

    # 2. Query Entities & Numbers
    q_entities = {e.lower() for e in (query.entities or [])}
    q_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", query.normalized_query))
    q_intent = query.query_intent

    reranked: List[CandidateChunk] = []

    for cand in candidates:
        cand_copy = cand.model_copy(deep=True)
        base_rrf = cand_copy.rrf_score or cand_copy.hybrid_score or cand_copy.dense_score or cand_copy.lexical_score or 0.0

        chunk_text_raw = cand_copy.text_content
        chunk_text_lower = chunk_text_raw.lower()
        chunk_tokens = set(tokenize(chunk_text_lower))
        chunk_stems = {stem_term(t) for t in chunk_tokens} | chunk_tokens

        sec_title = (cand_copy.section_title or "").lower()
        sec_tokens = set(tokenize(sec_title))
        sec_stems = {stem_term(t) for t in sec_tokens} | sec_tokens

        # A. Core Important Term Coverage
        matched_core = core_q_stems.intersection(chunk_stems)
        term_cov = len(matched_core) / total_core
        cand_copy.important_term_coverage = round(term_cov, 4)

        # B. Entity Match
        matched_entities = [ent for ent in q_entities if ent in chunk_text_lower or ent in sec_title]
        entity_score = (len(matched_entities) / max(1, len(q_entities))) if q_entities else 0.0
        cand_copy.entity_match = round(entity_score, 4)

        # C. Query Intent Compatibility Match
        intent_match = 0.0
        if q_intent == "NUMERICAL":
            chunk_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", chunk_text_raw))
            if q_numbers and q_numbers.intersection(chunk_nums):
                intent_match += 0.35
            elif bool(re.search(r"\b\d+(?:\.\d+)?%?\b", chunk_text_raw)):
                intent_match += 0.20
            if any(k in sec_title or k in chunk_text_lower for k in ["fee", "attendance", "credits", "limit", "amount", "concession"]):
                intent_match += 0.15

        elif q_intent == "WHERE_TO":
            if "http" in chunk_text_lower or "www." in chunk_text_lower:
                intent_match += 0.40
            if "how to apply" in sec_title or "official" in chunk_text_lower or "portal" in chunk_text_lower or "website" in chunk_text_lower:
                intent_match += 0.25

        elif q_intent == "HOW_TO":
            if "how to apply" in sec_title or "procedure" in sec_title or "process" in sec_title:
                intent_match += 0.35
            if any(step in chunk_text_lower for step in ["step", "apply through", "submission", "portal"]):
                intent_match += 0.20

        elif q_intent == "POLICY":
            if any(p in sec_title for p in ["policy", "regulations", "rules", "attendance", "hostel", "discipline", "curfew", "malpractice"]):
                intent_match += 0.30

        cand_copy.query_intent_match = round(intent_match, 4)

        # D. Document & Section Scope Match
        scope_score = 0.0
        if core_q_stems.intersection(sec_stems):
            scope_score += 0.30
        if any(k in all_q_stems for k in ['technology', 'stack', 'database', 'backend', 'frontend', 'mysql']) and 'technology stack' in sec_title:
            scope_score += 0.35
        cand_copy.document_scope_match = round(scope_score, 4)

        # Core Domain Specific Term Boost
        domain_term_boost = 0.0
        matched_domain_terms = set(core_q_tokens).intersection(_CORE_DOMAIN_TERMS).intersection(chunk_tokens)
        if matched_domain_terms:
            domain_term_boost = 0.25

        # E. Generic word collision protection:
        # If query has core topic terms (like attendance, cgtmse, revaluation, nirf, database),
        # but chunk only matched generic words (like "required", "student") with ZERO core topic overlap,
        # penalize heavily so "Students are required to use black ballpoint pen" NEVER outranks the policy!
        generic_only_penalty = 0.0
        has_core_q_terms = any(t in _CORE_DOMAIN_TERMS for t in core_q_tokens)
        if has_core_q_terms and not matched_core and not matched_entities:
            generic_only_penalty = 0.60

        # Exact phrase match bonus
        phrase_bonus = 0.20 if (len(q_text) > 4 and q_text in chunk_text_lower) else 0.0

        # Fragment/Short text penalty
        short_penalty = 0.20 if len(chunk_text_raw.strip()) < 80 else (0.05 if len(chunk_text_raw.strip()) < 120 else 0.0)

        # Compute combined relevance score
        combined_score = (
            (base_rrf * 0.40)
            + (term_cov * 0.40)
            + (entity_score * 0.25)
            + (intent_match * 0.20)
            + (scope_score * 0.15)
            + domain_term_boost
            + phrase_bonus
            - generic_only_penalty
            - short_penalty
        )

        cand_copy.rerank_score = round(combined_score, 4)
        reranked.append(cand_copy)

    # Sort descending by rerank_score, break ties deterministically
    reranked.sort(
        key=lambda x: (
            x.rerank_score or 0.0,
            x.rrf_score or 0.0,
            x.dense_score or 0.0,
            x.chunk_id
        ),
        reverse=True
    )

    # Normalize display rerank score to [0.0, 1.0] and re-assign rank indices
    for idx, cand in enumerate(reranked, start=1):
        cand.rank = idx
        cand.rerank_score = round(max(0.0, min(1.0, cand.rerank_score or 0.0)), 4)

    if top_k is not None and top_k > 0:
        return reranked[:top_k]
    return reranked
