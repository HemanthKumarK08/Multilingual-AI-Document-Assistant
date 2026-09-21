"""
Deterministic Heuristic Reranker Module
"""

import re
from typing import List, Optional
from app.services.retrieval.lexical_retriever import tokenize
from app.services.retrieval.models import CandidateChunk, ProcessedQuery

_STOPWORDS = {
    'what', 'is', 'the', 'in', 'for', 'to', 'of', 'and', 'a', 'an', 'on', 'are',
    'how', 'do', 'does', 'explain', 'about', 'which', 'where', 'can', 'be',
    'tell', 'me', 'used', 'with', 'from', 'at', 'by', 'use', 'using', 'mentioned',
    'any', 'some', 'give', 'detail', 'details', 'system', 'platform'
}

_DOMAIN_KEYWORDS = {
    'database', 'mysql', 'backend', 'frontend', 'technology', 'technologies', 'stack',
    'proctoring', 'security', 'desktop', 'electron', 'services', 'attendance',
    'condonation', 'credit', 'credits', 'revaluation', 'photocopy', 'challenge',
    'supplementary', 'makeup', 'fast-track', 'backlog', 'scholarship', 'merit',
    'hostel', 'placement', 'debarment', 'eligibility', 'grade', 'malpractice',
    'express', 'jwt', 'rbac', 'cloudflare', 'gemini', 'openai', 'html5', 'css3',
    'javascript', 'python', 'vision', 'proctor'
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
    Applies deterministic heuristic reranking combining hybrid retrieval scores,
    exact query phrase matches, informative query term coverage, section title overlap,
    and stability tie-breaks.
    
    Preserves all provenance attributes and metadata intact.
    """
    if not candidates:
        return []

    q_text = query.normalized_query.lower()
    raw_q_tokens = tokenize(query.normalized_query.lower())
    info_q_tokens = [t for t in raw_q_tokens if t not in _STOPWORDS]
    q_tokens = set(info_q_tokens) if info_q_tokens else set(raw_q_tokens)
    
    key_q_tokens = {t for t in q_tokens if t not in {'intelliexam', 'exam', 'ai', 'document', 'documents'}}
    if not key_q_tokens:
        key_q_tokens = q_tokens
        
    q_stems = {stem_term(t) for t in q_tokens} | q_tokens
    key_q_stems = {stem_term(t) for t in key_q_tokens} | key_q_tokens
    total_key = max(1, len(key_q_tokens))
    total_all = max(1, len(q_tokens))

    reranked: List[CandidateChunk] = []

    for cand in candidates:
        cand_copy = cand.model_copy(deep=True)
        base_score = cand_copy.hybrid_score or cand_copy.dense_score or cand_copy.lexical_score or 0.0
        
        chunk_text_lower = cand_copy.text_content.lower()
        chunk_tokens = set(tokenize(chunk_text_lower))
        chunk_stems = {stem_term(t) for t in chunk_tokens} | chunk_tokens
        
        sec_tokens = set(tokenize(cand_copy.section_title.lower()))
        sec_stems = {stem_term(t) for t in sec_tokens} | sec_tokens

        # 1. Informative key term coverage bonus
        matched_key = key_q_stems.intersection(chunk_stems)
        key_coverage = len(matched_key) / total_key

        # 2. General informative term coverage
        matched_all = q_stems.intersection(chunk_stems)
        all_coverage = len(matched_all) / total_all
        
        # 3. Domain keyword bonus
        domain_overlap = q_stems.intersection(_DOMAIN_KEYWORDS)
        matched_domain = domain_overlap.intersection(chunk_stems)
        domain_bonus = 0.25 * len(matched_domain)

        # 4. Section title relevance bonus
        sec_key_overlap = key_q_stems.intersection(sec_stems)
        sec_bonus = 0.30 if sec_key_overlap else (0.10 if q_stems.intersection(sec_stems) else 0.0)

        # 5. Exact phrase match bonus
        phrase_bonus = 0.20 if (len(q_text) > 4 and q_text in chunk_text_lower) else 0.0

        # 6. Technology stack specific bonus
        if ('technology' in q_stems or 'stack' in q_stems or 'tech' in q_stems) and 'technology stack' in cand_copy.section_title.lower():
            sec_bonus += 0.30

        # 7. Short content penalty
        short_penalty = 0.05 if len(cand_copy.text_content.strip()) < 30 else 0.0

        # Combine into un-clamped score for sorting
        computed_score = base_score + (key_coverage * 0.50) + (all_coverage * 0.10) + domain_bonus + sec_bonus + phrase_bonus - short_penalty
        cand_copy.rerank_score = round(computed_score, 4)
        
        reranked.append(cand_copy)

    # Deterministic sorting: highest rerank_score, then highest base score, then alphabetical chunk_id
    reranked.sort(
        key=lambda x: (
            x.rerank_score or 0.0,
            x.hybrid_score or x.dense_score or 0.0,
            x.chunk_id
        ),
        reverse=True
    )

    # Re-assign rank indices and normalize display score to [0.0, 1.0]
    for idx, cand in enumerate(reranked, start=1):
        cand.rank = idx
        cand.rerank_score = round(max(0.0, min(1.0, cand.rerank_score or 0.0)), 4)

    if top_k is not None and top_k > 0:
        return reranked[:top_k]
    return reranked
