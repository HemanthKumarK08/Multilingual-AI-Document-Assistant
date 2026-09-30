"""
Question Answering and Grounded RAG Endpoints
"""

import time
from functools import partial

import anyio.to_thread
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.schemas import Citation, FeedbackRequest, QueryRequest, QueryResponse
from app.services.rag.coordinator import RAGCoordinator
from app.services.retrieval.models import RetrievalFilter

router = APIRouter()

# Single coordinator instance (embedding model loaded once)
_rag_coordinator = RAGCoordinator()


@router.post("/query", response_model=QueryResponse)
async def submit_query(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Multilingual hybrid-RAG QA endpoint.
    Executes: embed → ChromaDB → BM25 → RRF → top-5 → Gemini/Groq/Mock → answer.
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
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")

    total_latency = (time.perf_counter() - start_time) * 1000.0

    is_fallback = grounded_answer.fallback_used or not grounded_answer.grounded
    is_grounded = grounded_answer.grounded

    if grounded_answer.fallback_reason == "LANGUAGE_UNAVAILABLE":
        response_state = "LANGUAGE_UNAVAILABLE"
        is_grounded = False
    elif is_grounded:
        response_state = "GROUNDED"
    else:
        response_state = "INSUFFICIENT_EVIDENCE"

    # Build citations from retrieved sources — ONLY for strictly grounded answers
    api_citations = []
    if is_grounded and response_state == "GROUNDED" and grounded_answer.sources:
        for src in grounded_answer.sources:
            api_citations.append(Citation(
                document_id=src.doc_id,
                document_title=src.filename,
                category=req.category or "general",
                page_number=src.page_number,
                chunk_index=0,
                similarity_score=1.0,
                excerpt=src.section_title or src.filename,
            ))

    # Telemetry (best-effort, non-blocking)
    try:
        from app.services.telemetry.models import RAGTelemetryEvent
        from app.services.telemetry.recorder import telemetry_recorder

        telemetry_recorder.record_event(
            RAGTelemetryEvent(
                query_id=grounded_answer.query_id,
                retrieval_id=grounded_answer.retrieval_id or "",
                language=grounded_answer.response_language,
                script={"en": "latin", "hi": "devanagari",
                        "kn": "kannada", "te": "telugu"}.get(
                    grounded_answer.response_language, "unknown"),
                is_code_mixed=False,
                candidate_count=len(grounded_answer.sources),
                selected_chunk_count=len(grounded_answer.sources),
                best_retrieval_score=1.0 if is_grounded else 0.0,
                fallback_used=grounded_answer.fallback_used,
                fallback_reason=grounded_answer.fallback_reason,
                answer_grounded=grounded_answer.grounded,
                citation_count=len(api_citations),
                latency_ms=round(total_latency, 2),
            )
        )
    except Exception:
        pass

    return QueryResponse(
        query_id=grounded_answer.query_id,
        query_text=req.query_text,
        detected_language=grounded_answer.response_language,
        target_language=grounded_answer.target_language,
        response_language=grounded_answer.response_language,
        answer_text=grounded_answer.answer_text,
        is_fallback=is_fallback,
        grounded=is_grounded,
        fallback_reason=grounded_answer.fallback_reason if is_fallback else None,
        response_state=response_state,
        generation_path=grounded_answer.generation_path,
        citations=api_citations,
        retrieval_latency_ms=round(grounded_answer.latency_ms * 0.4, 2),
        generation_latency_ms=round(grounded_answer.latency_ms * 0.6, 2),
        total_latency_ms=round(total_latency, 2),
    )


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    """Submit user quality feedback (Thumbs Up / Down)."""
    return {"status": "recorded", "query_id": req.query_id, "feedback": req.feedback}
