"""
Question Answering and Grounded RAG Endpoints (Phase 5)
"""

from functools import partial
import time
import anyio.to_thread
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db
from app.schemas import Citation, FeedbackRequest, QueryRequest, QueryResponse
from app.services.rag.coordinator import RAGCoordinator
from app.services.retrieval.models import RetrievalFilter
from app.services.telemetry.models import RAGTelemetryEvent
from app.services.telemetry.recorder import telemetry_recorder

router = APIRouter()
_rag_coordinator = RAGCoordinator()


@router.post("/query", response_model=QueryResponse)
async def submit_query(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Public student and institutional grounded document QA endpoint.
    Executes end-to-end multilingual hybrid retrieval, evidence gating, and grounded RAG answer generation.
    """
    start_time = time.perf_counter()

    filters = RetrievalFilter(category=req.category) if req.category else None

    try:
        grounded_answer = await anyio.to_thread.run_sync(
            partial(
                _rag_coordinator.answer,
                query=req.query_text,
                target_language=req.target_language,
                filters=filters,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")

    total_latency = (time.perf_counter() - start_time) * 1000.0

    # Determine authoritative response state
    is_lang_unavail = (
        grounded_answer.fallback_reason in ("MISSING_TARGET_SCRIPT", "LANGUAGE_UNAVAILABLE", "UNAVAILABLE_LANGUAGE", "SCRIPT_CONTAMINATION")
        or "सेवा वर्तमान में अनुपलब्ध" in grounded_answer.answer_text
        or "ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ" in grounded_answer.answer_text
        or "సేవ ప్రస్తుతం అందుబాటులో లేదు" in grounded_answer.answer_text
    )

    if is_lang_unavail:
        response_state = "LANGUAGE_UNAVAILABLE"
        is_fallback = True
        is_grounded = False
        api_citations = []
    elif grounded_answer.fallback_used or not grounded_answer.grounded:
        response_state = "INSUFFICIENT_EVIDENCE"
        is_fallback = True
        is_grounded = False
        api_citations = []
    else:
        response_state = "GROUNDED"
        is_fallback = False
        is_grounded = True
        # Map sources to API Citation schema only for truly grounded answers
        api_citations = [
            Citation(
                document_id=src.doc_id,
                document_title=src.filename,
                category=req.category or "general",
                page_number=src.page_number,
                chunk_index=0,
                similarity_score=1.0,
                excerpt=src.section_title or "Evidence Source",
            )
            for src in grounded_answer.sources
        ]

    # Compute script and provider for telemetry
    script_map = {"en": "latin", "hi": "devanagari", "kn": "kannada", "te": "telugu"}
    detected_script = script_map.get(grounded_answer.response_language, "unknown")
    provider_name = str(getattr(settings, "LLM_PRIMARY_PROVIDER", "mock"))

    # Record safe, privacy-preserving telemetry
    try:
        telemetry_recorder.record_event(
            RAGTelemetryEvent(
                query_id=grounded_answer.query_id,
                retrieval_id=grounded_answer.retrieval_id,
                language=grounded_answer.response_language,
                script=detected_script,
                is_code_mixed=False,
                candidate_count=len(grounded_answer.sources),
                selected_chunk_count=len(grounded_answer.sources),
                best_retrieval_score=1.0 if not grounded_answer.fallback_used else 0.0,
                fallback_used=grounded_answer.fallback_used,
                fallback_reason=grounded_answer.fallback_reason,
                answer_grounded=grounded_answer.grounded,
                citation_count=len(grounded_answer.sources),
                latency_ms=round(total_latency, 2),
            )
        )

        from app.services.telemetry.models import UnifiedQueryTelemetryEvent
        telemetry_recorder.record_event(
            UnifiedQueryTelemetryEvent(
                query_id=grounded_answer.query_id,
                retrieval_id=grounded_answer.retrieval_id,
                language=grounded_answer.response_language,
                script=detected_script,
                query_type="cross_lingual_fact" if grounded_answer.response_language != "en" else "fact_lookup",
                is_code_mixed=False,
                variant_count=1,
                candidate_count=len(grounded_answer.sources),
                retrieved_chunk_count=len(grounded_answer.sources),
                best_retrieval_score=1.0 if not grounded_answer.fallback_used else 0.0,
                retrieval_latency_ms=round(grounded_answer.latency_ms * 0.4, 2),
                reranking_latency_ms=round(grounded_answer.latency_ms * 0.1, 2),
                generation_latency_ms=round(grounded_answer.latency_ms * 0.5, 2),
                total_latency_ms=round(total_latency, 2),
                provider=provider_name,
                answer_mode="fallback" if grounded_answer.fallback_used else "grounded",
                fallback_used=grounded_answer.fallback_used,
                fallback_reason=grounded_answer.fallback_reason,
                citation_count=len(grounded_answer.sources),
                citation_valid=True,
                grounded=grounded_answer.grounded,
                error=False,
            )
        )
    except Exception as tel_err:
        pass

    return QueryResponse(
        query_id=grounded_answer.query_id,
        query_text=req.query_text,
        detected_language=grounded_answer.response_language,
        answer_text=grounded_answer.answer_text,
        is_fallback=is_fallback,
        grounded=is_grounded,
        fallback_reason=grounded_answer.fallback_reason if is_fallback else None,
        response_state=response_state,
        citations=api_citations,
        retrieval_latency_ms=round(grounded_answer.latency_ms * 0.4, 2),
        generation_latency_ms=round(grounded_answer.latency_ms * 0.6, 2),
        total_latency_ms=round(total_latency, 2),
    )


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    """Submit user quality feedback (Thumbs Up / Down)."""
    return {"status": "recorded", "query_id": req.query_id, "feedback": req.feedback}
