"""
Retrieval Pipeline Coordinator Module (Research-Backed RAG Architecture)
Coordinates multi-stage, multi-variant hybrid retrieval workflow:
Query Processing -> Query Rewriting (max 3 variants) -> Multi-Variant Dense & Lexical Retrieval (top-20 each)
-> Multi-Query Reciprocal Rank Fusion (RRF, k=60) -> Candidate Relevance Stage -> Validation.
"""

import time
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.hybrid import reciprocal_rank_fusion
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
    Coordinates multi-query dense + BM25 retrieval and Reciprocal Rank Fusion (RRF).
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
        target_language: Optional[str] = None,
        filters: Optional[RetrievalFilter] = None,
        dense_top_k: Optional[int] = 20,
        lexical_top_k: Optional[int] = 20,
        final_top_k: Optional[int] = 20,
        dense_weight: Optional[float] = None,
        lexical_weight: Optional[float] = None,
        enable_reranking: Optional[bool] = None,
        enable_query_expansion: Optional[bool] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RetrievalResult:
        """
        Executes end-to-end multi-variant hybrid retrieval for a user query.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        # 1. Query Processing, Normalization & Intent Understanding
        query: ProcessedQuery = process_query(
            raw_query=raw_query,
            explicit_language=language,
            target_language=target_language,
            conversation_history=conversation_history,
        )

        d_k = dense_top_k or 20
        l_k = lexical_top_k or 20
        f_k = final_top_k or 20
        d_weight = dense_weight if dense_weight is not None else settings.RETRIEVAL_DENSE_WEIGHT
        l_weight = lexical_weight if lexical_weight is not None else settings.RETRIEVAL_LEXICAL_WEIGHT
        rerank = enable_reranking if enable_reranking is not None else settings.RETRIEVAL_ENABLE_RERANKING
        expansion_active = (
            enable_query_expansion
            if enable_query_expansion is not None
            else settings.RETRIEVAL_ENABLE_QUERY_EXPANSION
        )

        # 2. Safe Query Rewriting (max 3 variants)
        if expansion_active:
            variants = expand_query(
                processed_query=query,
                max_variants=3,
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
        ranked_lists_for_rrf: List[Tuple[List[CandidateChunk], float, str]] = []
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

            # Variant weighting
            var_weight = variant.weight

            # Dense Retrieval for variant (top 20)
            try:
                dense_res = self.dense_retriever.retrieve(
                    query=var_query,
                    top_k=d_k,
                    filters=filters,
                    min_score=settings.RETRIEVAL_MIN_SCORE,
                )
                for c in dense_res:
                    if variant.variant_type not in c.query_variant_sources:
                        c.query_variant_sources.append(variant.variant_type)
                total_found += len(dense_res)
                if dense_res:
                    ranked_lists_for_rrf.append((dense_res, var_weight, f"dense_{variant.variant_type}"))
            except Exception as e:
                logger.warning(f"Dense retrieval error for variant '{variant.variant_text}': {e}")
                warnings.append(f"Dense retrieval error: {str(e)}")

            # Lexical Retrieval for variant (top 20)
            if self.lexical_retriever and settings.RETRIEVAL_ENABLE_LEXICAL:
                try:
                    lexical_res = self.lexical_retriever.retrieve(
                        query=var_query,
                        top_k=l_k,
                        filters=filters,
                        min_score=settings.RETRIEVAL_MIN_SCORE,
                    )
                    for c in lexical_res:
                        if variant.variant_type not in c.query_variant_sources:
                            c.query_variant_sources.append(variant.variant_type)
                    total_found += len(lexical_res)
                    if lexical_res:
                        ranked_lists_for_rrf.append((lexical_res, var_weight, f"lexical_{variant.variant_type}"))
                except Exception as e:
                    logger.warning(f"Lexical retrieval error for variant '{variant.variant_text}': {e}")
                    warnings.append(f"Lexical retrieval error: {str(e)}")

        # 4. Multi-Query Reciprocal Rank Fusion (RRF, k=60)
        fused_pool = reciprocal_rank_fusion(
            ranked_lists=ranked_lists_for_rrf,
            k=60.0,
            top_k=20,  # Max 20 candidates in pool
        )

        # 5. Candidate Relevance & Heuristic Reranking
        if rerank and fused_pool:
            ranked_candidates = heuristic_rerank(
                query=query,
                candidates=fused_pool,
                top_k=f_k,
            )
        else:
            ranked_candidates = fused_pool[:f_k]

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
