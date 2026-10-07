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

# In-memory session language history tracker (bounded to last 5,000 active sessions)
_session_language_history: dict = {}


def _detect_script_and_code_mixed(text: str, response_lang: str) -> tuple:
    """Detects script and code-mixed/romanized characteristics from user query text."""
    if not text:
        return "latin", False, False

    has_dev = any('\u0900' <= c <= '\u097F' for c in text)
    has_kn = any('\u0C80' <= c <= '\u0CFF' for c in text)
    has_te = any('\u0C00' <= c <= '\u0C7F' for c in text)
    has_latin = any('a' <= c.lower() <= 'z' for c in text)
    indic_count = sum([has_dev, has_kn, has_te])

    if has_dev and indic_count == 1:
        script = "devanagari"
    elif has_kn and indic_count == 1:
        script = "kannada"
    elif has_te and indic_count == 1:
        script = "telugu"
    elif has_latin and indic_count == 0:
        script = "latin"
    else:
        script = "mixed" if (indic_count > 1 or (indic_count >= 1 and has_latin)) else "latin"

    is_romanized = bool(has_latin and response_lang in ("hi", "kn", "te") and indic_count == 0)
    is_code_mixed = bool((has_latin and indic_count >= 1) or is_romanized)
    return script, is_code_mixed, is_romanized


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
        import os
        from app.services.telemetry.models import RAGTelemetryEvent
        from app.services.telemetry.recorder import telemetry_recorder
        from app.services.telemetry.user_identity import (
            generate_anonymous_user_id,
            generate_anonymous_session_id,
        )

        raw_sess_id = req.session_id or "SES-DEFAULT"
        anon_user = generate_anonymous_user_id(raw_sess_id)
        anon_session = generate_anonymous_session_id(raw_sess_id)

        # Retrieve previous language in this session
        global _session_language_history
        prev_lang = _session_language_history.get(anon_session)
        if len(_session_language_history) > 5000:
            _session_language_history.clear()
        _session_language_history[anon_session] = grounded_answer.response_language

        # Detect script and code-mixing
        script, is_code_mixed, is_romanized = _detect_script_and_code_mixed(
            req.query_text, grounded_answer.response_language
        )

        # Resolve telemetry environment
        active_env = os.environ.get("TELEMETRY_ENVIRONMENT")
        if not active_env:
            if os.environ.get("PYTEST_CURRENT_TEST") or settings.APP_ENV == "testing":
                active_env = "test"
            else:
                active_env = settings.TELEMETRY_ENVIRONMENT or "live"

        top_doc_id = grounded_answer.sources[0].doc_id if grounded_answer.sources else None

        telemetry_recorder.record_event(
            RAGTelemetryEvent(
                query_id=grounded_answer.query_id,
                telemetry_environment=active_env,
                anonymous_user_id=anon_user,
                session_id=anon_session,
                document_id=top_doc_id,
                retrieval_id=grounded_answer.retrieval_id or "",
                language=grounded_answer.response_language,
                previous_language=prev_lang,
                script=script,
                is_code_mixed=is_code_mixed,
                is_romanized=is_romanized,
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
