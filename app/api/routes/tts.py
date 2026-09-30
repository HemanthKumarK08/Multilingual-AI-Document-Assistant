"""
Text-to-Speech Endpoints using Sarvam Bulbul v3
"""

from fastapi import APIRouter, HTTPException, status
from app.core.logging import logger
from app.schemas.tts import TTSSynthesizeRequest, TTSSynthesizeResponse
from app.services.tts.sarvam import get_tts_client, get_speaker_for_language

router = APIRouter()


@router.post("/synthesize", response_model=TTSSynthesizeResponse)
async def synthesize_speech(req: TTSSynthesizeRequest):
    """
    Synthesizes speech using Sarvam Bulbul v3.
    Accepts text and language ('en', 'hi', 'kn', 'te').
    Returns base64-encoded WAV audio data with voice metadata.
    """
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty."
        )

    clean_lang = req.language.lower().split("-")[0]
    if clean_lang not in ("en", "hi", "kn", "te"):
        clean_lang = "en"

    tts_client = get_tts_client()
    expected_speaker = get_speaker_for_language(clean_lang)

    try:
        res = await tts_client.synthesize(text=clean_text, language=clean_lang)
        return TTSSynthesizeResponse(
            audio=res.audio_base64,
            language=res.language,
            provider=res.provider,
            model=tts_client.model,
            voice=res.speaker,
            speaker=res.speaker,
            tts_mode=res.tts_mode,
            latency_ms=res.latency_ms,
            fallback_allowed=(clean_lang == "en"),
        )
    except Exception as e:
        logger.warning(f"Sarvam synthesis failed for language [{clean_lang}]: {e}")
        # Safe fallback semantics per PART N:
        # Indic text must NEVER be spoken by an English browser voice.
        if clean_lang != "en":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice generation is temporarily unavailable."
            )
        # For English, allow optional browser fallback
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice generation is temporarily unavailable."
        )
