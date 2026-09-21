"""
Grounded RAG Pipeline Coordinator Module
"""

import time
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.rag.answer_generator import generate_grounded_answer
from app.services.rag.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    REASON_PROVIDER_UNAVAILABLE,
)
from app.services.rag.context_builder import build_context_package
from app.services.rag.evidence_gate import evaluate_evidence_sufficiency
from app.services.rag.fallback import create_fallback_answer
from app.services.rag.llm_provider import LLMProvider, get_llm_provider
from app.services.rag.models import GroundedAnswer
from app.services.rag.validation import validate_grounded_answer
from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.models import RetrievalFilter, RetrievalResult


class RAGCoordinator:
    """
    Orchestrates the complete evidence-grounded RAG answering pipeline:
    Query -> Retrieval -> Evidence Gating -> Context Building -> Grounded LLM Generation -> Citation Validation -> Grounded Answer.
    """

    def __init__(
        self,
        retrieval_coordinator: Optional[RetrievalCoordinator] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.retrieval_coordinator = retrieval_coordinator or RetrievalCoordinator()
        self.llm_provider = llm_provider or get_llm_provider()

    def answer(
        self,
        query: str,
        language: Optional[str] = None,
        filters: Optional[RetrievalFilter] = None,
        max_context_chunks: Optional[int] = None,
        min_evidence_score: Optional[float] = None,
    ) -> GroundedAnswer:
        """
        Executes end-to-end Grounded RAG query answering.
        """
        start_time = time.perf_counter()

        # 1. Retrieval Stage
        retrieval_result: RetrievalResult = self.retrieval_coordinator.retrieve(
            raw_query=query,
            language=language,
            filters=filters,
        )

        query_id = retrieval_result.query.query_id
        response_lang = retrieval_result.query.language if retrieval_result.query.language != "und" else "en"

        # 2. Evidence Sufficiency Gating
        gate_result = evaluate_evidence_sufficiency(
            retrieval_result=retrieval_result,
            min_score=min_evidence_score or settings.RAG_MIN_EVIDENCE_SCORE,
            min_chunks=settings.RAG_MIN_EVIDENCE_CHUNKS,
        )

        if not gate_result.is_sufficient:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return create_fallback_answer(
                query_id=query_id,
                reason=gate_result.reason or "INSUFFICIENT_EVIDENCE",
                response_language=response_lang,
                retrieval_id=retrieval_result.retrieval_id,
                warnings=gate_result.warnings,
                latency_ms=elapsed_ms,
            )

        # 3. Context Construction
        context = build_context_package(
            candidates=gate_result.selected_candidates,
            max_chunks=max_context_chunks or settings.RETRIEVAL_MAX_CONTEXT_CHUNKS,
            max_characters=settings.RETRIEVAL_MAX_CONTEXT_CHARACTERS,
        )

        # 4. LLM Generation
        try:
            answer_text, citations, gen_warnings = generate_grounded_answer(
                query_text=retrieval_result.query.normalized_query,
                context=context,
                target_language=response_lang,
                llm_provider=self.llm_provider,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            )
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return create_fallback_answer(
                query_id=query_id,
                reason=REASON_PROVIDER_UNAVAILABLE,
                response_language=response_lang,
                retrieval_id=retrieval_result.retrieval_id,
                warnings=[f"Provider error: {str(e)}"],
                latency_ms=elapsed_ms,
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Check if fallback was returned by generator
        if answer_text == settings.RAG_FALLBACK_MESSAGE:
            return create_fallback_answer(
                query_id=query_id,
                reason="MODEL_FALLBACK_TRIGGERED",
                response_language=response_lang,
                retrieval_id=retrieval_result.retrieval_id,
                warnings=gen_warnings,
                latency_ms=elapsed_ms,
            )

        # Determine qualitative confidence label
        best_score = gate_result.observed_best_score
        if best_score >= 0.70:
            confidence = CONFIDENCE_HIGH
        elif best_score >= 0.50:
            confidence = CONFIDENCE_MEDIUM
        else:
            confidence = CONFIDENCE_LOW

        answer_obj = GroundedAnswer(
            query_id=query_id,
            answer_text=answer_text,
            response_language=response_lang,
            grounded=True,
            fallback_used=False,
            fallback_reason=None,
            retrieval_id=retrieval_result.retrieval_id,
            sources=citations,
            confidence_label=confidence,
            warnings=gen_warnings,
            latency_ms=round(elapsed_ms, 2),
        )

        # 5. Answer Grounding Validation
        is_valid, val_errors = validate_grounded_answer(answer_obj, context)
        if not is_valid:
            answer_obj.warnings.extend(val_errors)

        return answer_obj
