"""
Schemas for Text-to-Speech Endpoints
"""

from typing import Optional
from pydantic import BaseModel, Field

class TTSSynthesizeRequest(BaseModel):
    """Request model for professional neural speech synthesis."""
    text: str = Field(..., min_length=1, description="Text to synthesize into speech.")
    language: str = Field(default="en", description="Target language code: en, hi, kn, te.")

class TTSSynthesizeResponse(BaseModel):
    """Response model containing synthesized base64 audio and metadata."""
    audio: str = Field(..., description="Base64-encoded WAV audio data.")
    language: str = Field(..., description="Language code of synthesized speech.")
    provider: str = Field(default="sarvam", description="TTS provider name.")
    model: str = Field(default="bulbul:v3", description="TTS model name.")
    voice: str = Field(..., description="Selected neural speaker voice.")
    speaker: str = Field(..., description="Selected neural speaker voice alias.")
    tts_mode: str = Field(default="live_sarvam", description="'live_sarvam' or 'synthetic_test'")
    latency_ms: Optional[float] = Field(default=None, description="Synthesis latency in milliseconds.")
    fallback_allowed: bool = Field(default=False, description="Whether browser speechSynthesis fallback is permitted (English only).")


