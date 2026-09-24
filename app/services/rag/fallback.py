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
    Constructs a deterministic Information-Not-Found or localized unavailable response.
    Guarantees no fabricated answers or citations when evidence or language capability is insufficient.
    """
    if custom_message:
        msg = custom_message
    elif reason == "MISSING_TARGET_SCRIPT":
        if response_language == "hi":
            msg = "अनुरोधित भाषा (हिन्दी) में उत्तर देने के लिए बहुभाषी मॉडल सेवा वर्तमान में अनुपलब्ध है।"
        elif response_language == "kn":
            msg = "ವಿನಂತಿಸಿದ ಭಾಷೆಯಲ್ಲಿ (ಕನ್ನಡ) ಉತ್ತರಿಸಲು ಬಹುಭಾಷಾ ಮಾದರಿ ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ."
        elif response_language == "te":
            msg = "అభ్యర్థించిన భాషలో (తెలుగు) సమాధానం ఇవ్వడానికి బహుభాషా మోడల్ సేవ ప్రస్తుతం అందుబాటులో లేదు."
        else:
            msg = settings.RAG_FALLBACK_MESSAGE
    else:
        msg = settings.RAG_FALLBACK_MESSAGE

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

