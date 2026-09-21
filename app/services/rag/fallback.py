"""
Deterministic Fallback Generation Module
"""

from typing import List, Optional
from app.core.config import settings
from app.services.rag.models import GroundedAnswer

def create_fallback_answer(
    query_id: str,
    reason: str,
    response_language: str = "en",
    retrieval_id: Optional[str] = None,
    custom_message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    latency_ms: float = 0.0,
) -> GroundedAnswer:
    """
    Constructs a deterministic Information-Not-Found response.
    Guarantees no fabricated answers or citations when evidence is insufficient.
    """
    msg = custom_message or settings.RAG_FALLBACK_MESSAGE

    return GroundedAnswer(
        query_id=query_id,
        answer_text=msg,
        response_language=response_language,
        grounded=False,
        fallback_used=True,
        fallback_reason=reason,
        retrieval_id=retrieval_id,
        sources=[],
        confidence_label=None,
        warnings=warnings or [],
        latency_ms=round(latency_ms, 2),
    )
