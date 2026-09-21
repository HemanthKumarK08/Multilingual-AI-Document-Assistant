"""
Retrieval Pipeline Coordinator Module (Phase 6)
Coordinates multi-stage, multi-variant hybrid retrieval workflow:
Query Processing -> Query Expansion & Transliteration -> Multi-Variant Dense & Lexical Retrieval
-> Priority-Weighted Candidate Fusion -> Deterministic Heuristic Reranking -> Validation.
"""

import time
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.hybrid import fuse_hybrid_scores
from app.services.retrieval.lexical_retriever import LexicalRetriever
from app.services.retrieval.models import (
    CandidateChunk,
    ProcessedQuery,
    QueryVariant,
    RetrievalFilter,
    RetrievalResult,
)
from app.services.retrieval.query_expansion import expand_query
from app.services.retrieval.query_processing import process_query
from app.services.retrieval.reranker import heuristic_rerank
from app.services.retrieval.validation import validate_retrieval_result


class RetrievalCoordinator:
    """
    Coordinates the full multi-stage, multi-variant retrieval workflow.
    """

    def __init__(
        self,
        dense_retriever: Optional[DenseRetriever] = None,
        lexical_retriever: Optional[LexicalRetriever] = None,
    ):
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.lexical_retriever = lexical_retriever or (
            LexicalRetriever() if settings.RETRIEVAL_ENABLE_LEXICAL else None
        )

    def retrieve(
        self,
        raw_query: str,
        language: Optional[str] = None,
        filters: Optional[RetrievalFilter] = None,
        dense_top_k: Optional[int] = None,
        lexical_top_k: Optional[int] = None,
        final_top_k: Optional[int] = None,
        dense_weight: Optional[float] = None,
        lexical_weight: Optional[float] = None,
        enable_reranking: Optional[bool] = None,
        enable_query_expansion: Optional[bool] = None,
    ) -> RetrievalResult:
        """
        Executes end-to-end multi-variant hybrid retrieval for a user query.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        # 1. Query Processing & Normalization
        query: ProcessedQuery = process_query(raw_query, explicit_language=language)

        d_k = dense_top_k or settings.RETRIEVAL_DENSE_TOP_K
        l_k = lexical_top_k or settings.RETRIEVAL_LEXICAL_TOP_K
        f_k = final_top_k or settings.RETRIEVAL_FINAL_TOP_K
        d_weight = dense_weight if dense_weight is not None else settings.RETRIEVAL_DENSE_WEIGHT
        l_weight = lexical_weight if lexical_weight is not None else settings.RETRIEVAL_LEXICAL_WEIGHT
        rerank = enable_reranking if enable_reranking is not None else settings.RETRIEVAL_ENABLE_RERANKING
        expansion_active = (
            enable_query_expansion
            if enable_query_expansion is not None
            else settings.RETRIEVAL_ENABLE_QUERY_EXPANSION
        )

        # 2. Safe Query Expansion & Transliteration
        if expansion_active:
            variants = expand_query(
                processed_query=query,
                max_variants=settings.RETRIEVAL_MAX_QUERY_VARIANTS,
                enable_expansion=True,
                enable_transliteration=settings.RETRIEVAL_ENABLE_TRANSLITERATION,
            )
        else:
            variants = [
                QueryVariant(
                    variant_text=query.normalized_query,
                    variant_type="original",
                    weight=1.0,
                    language=query.language,
                )
            ]

        query.query_variants = variants
        if any(v.variant_type in ("transliteration", "indic_translation") for v in variants):
            query.is_transliterated = True

        # 3. Multi-Variant Dense and Lexical Retrieval
        merged_candidates: Dict[str, CandidateChunk] = {}
        total_found = 0

        for var_idx, variant in enumerate(variants):
            is_primary = var_idx == 0
            var_query = (
                query
                if is_primary
                else ProcessedQuery(
                    raw_query=variant.variant_text,
                    normalized_query=variant.variant_text,
                    language=variant.language,
                    script="Latin",
                )
            )

            v_d_k = d_k if is_primary else min(8, d_k)
            v_l_k = l_k if is_primary else min(8, l_k)
            weight = variant.weight

            # Dense Retrieval for variant
            try:
                dense_res = self.dense_retriever.retrieve(
                    query=var_query,
                    top_k=v_d_k,
                    filters=filters,
                    min_score=settings.RETRIEVAL_MIN_SCORE,
                )
                total_found += len(dense_res)
            except Exception as e:
                logger.warning(f"Dense retrieval error for variant '{variant.variant_text}': {e}")
                warnings.append(f"Dense retrieval error: {str(e)}")
                dense_res = []

            # Lexical Retrieval for variant
            lexical_res: List[CandidateChunk] = []
            if self.lexical_retriever and settings.RETRIEVAL_ENABLE_LEXICAL:
                try:
                    lexical_res = self.lexical_retriever.retrieve(
                        query=var_query,
                        top_k=v_l_k,
                        filters=filters,
                        min_score=settings.RETRIEVAL_MIN_SCORE,
                    )
                    total_found += len(lexical_res)
                except Exception as e:
                    logger.warning(f"Lexical retrieval error for variant '{variant.variant_text}': {e}")
                    warnings.append(f"Lexical retrieval error: {str(e)}")
                    lexical_res = []

            # Merge Dense Candidates
            for cand in dense_res:
                weighted_score = (cand.dense_score or 0.0) * weight
                cid = cand.chunk_id
                if cid not in merged_candidates:
                    cand_copy = cand.model_copy()
                    cand_copy.dense_score = weighted_score
                    cand_copy.query_variant_sources = [variant.variant_type]
                    merged_candidates[cid] = cand_copy
                else:
                    existing = merged_candidates[cid]
                    if weighted_score > (existing.dense_score or 0.0):
                        existing.dense_score = weighted_score
                    if variant.variant_type not in existing.query_variant_sources:
                        existing.query_variant_sources.append(variant.variant_type)
                    for m in cand.retrieval_methods:
                        if m not in existing.retrieval_methods:
                            existing.retrieval_methods.append(m)

            # Merge Lexical Candidates
            for cand in lexical_res:
                weighted_score = (cand.lexical_score or 0.0) * weight
                cid = cand.chunk_id
                if cid not in merged_candidates:
                    cand_copy = cand.model_copy()
                    cand_copy.lexical_score = weighted_score
                    cand_copy.query_variant_sources = [variant.variant_type]
                    merged_candidates[cid] = cand_copy
                else:
                    existing = merged_candidates[cid]
                    if weighted_score > (existing.lexical_score or 0.0):
                        existing.lexical_score = weighted_score
                    if variant.variant_type not in existing.query_variant_sources:
                        existing.query_variant_sources.append(variant.variant_type)
                    for m in cand.retrieval_methods:
                        if m not in existing.retrieval_methods:
                            existing.retrieval_methods.append(m)

        # 4. Hybrid Score Computation
        unique_candidates = list(merged_candidates.values())
        for cand in unique_candidates:
            d_s = cand.dense_score or 0.0
            l_s = cand.lexical_score or 0.0
            cand.hybrid_score = round(d_weight * d_s + l_weight * l_s, 4)

        # Sort by hybrid score descending
        unique_candidates.sort(key=lambda c: (c.hybrid_score or 0.0), reverse=True)

        # Cap intermediate candidate pool before reranking (max 30)
        candidate_pool = unique_candidates[:30]

        # 5. Deterministic Heuristic Reranking
        if rerank and candidate_pool:
            ranked_candidates = heuristic_rerank(
                query=query,
                candidates=candidate_pool,
                top_k=f_k,
            )
        else:
            ranked_candidates = candidate_pool[:f_k]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        result = RetrievalResult(
            query=query,
            candidates=ranked_candidates,
            total_candidates_found=total_found,
            selected_candidates_count=len(ranked_candidates),
            query_variant_count=len(variants),
            latency_ms=round(elapsed_ms, 2),
            filters_applied=filters,
            warnings=warnings,
        )

        valid, validation_errors = validate_retrieval_result(result)
        if not valid:
            result.warnings.extend(validation_errors)

        return result
