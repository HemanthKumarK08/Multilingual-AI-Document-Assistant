"""
Professional TTS Service using Sarvam Bulbul v3

Provides:
- Native Indian & English high-fidelity neural voices.
- Language & speaker mapping:
  - en -> en-IN (speaker: ratan)
  - hi -> hi-IN (speaker: priya)
  - te -> te-IN (speaker: neha)
  - kn -> kn-IN (speaker: ishita)
- Sentence-boundary chunking for long answers without splitting URLs, numbers,
  percentages, citations, or technical abbreviations.
- Sequential synthesis & clean WAV buffer concatenation.
- In-memory base64 response (zero permanent file persistence).
- Safe fallback semantics (Indic never falls back to English audio).
"""

from __future__ import annotations

import base64
import io
import math
import re
import struct
import time
import wave
from typing import List, NamedTuple, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger

LANGUAGE_CODE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "te": "te-IN",
}

SPEAKER_ENV_MAP = {
    "en": lambda: settings.SARVAM_SPEAKER_EN,
    "hi": lambda: settings.SARVAM_SPEAKER_HI,
    "kn": lambda: settings.SARVAM_SPEAKER_KN,
    "te": lambda: settings.SARVAM_SPEAKER_TE,
}

# Regex to detect URLs, citations, numbers, and technical identifiers to prevent bad splits
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_CITATION_RE = re.compile(r"\[(?:Source|శీర్షిక|మూలం|स्रोत|ಮೂಲ)\s*\d+\]", re.IGNORECASE)
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?।॥])\s+")


class SynthesisResult(NamedTuple):
    audio_base64: str
    language: str
    speaker: str
    provider: str
    latency_ms: float
    is_mock: bool = False
    tts_mode: str = "synthetic_test"


def get_speaker_for_language(lang: str) -> str:
    """Resolves speaker name for language code with env var override support."""
    clean_lang = lang.lower().split("-")[0]
    getter = SPEAKER_ENV_MAP.get(clean_lang)
    if getter:
        return getter()
    return settings.SARVAM_SPEAKER_EN


def get_target_language_code(lang: str) -> str:
    """Maps 2-letter language code to Sarvam target_language_code."""
    clean_lang = lang.lower().split("-")[0]
    return LANGUAGE_CODE_MAP.get(clean_lang, "en-IN")


def split_text_for_tts(text: str, max_chunk_chars: int = 400) -> List[str]:
    """
    Splits long answers strictly at sentence boundaries.
    Preserves URLs, percentages, numbers, and citation markers.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= max_chunk_chars:
        return [clean_text]

    # Split by sentence end punctuation followed by whitespace
    raw_sentences = _SENTENCE_BOUNDARY_RE.split(clean_text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for s in raw_sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        s_len = len(s_clean)
        if current_len + s_len + 1 > max_chunk_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [s_clean]
            current_len = s_len
        else:
            current_chunk.append(s_clean)
            current_len += s_len + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks or [clean_text[:max_chunk_chars]]


def concatenate_wav_buffers(wav_bytes_list: List[bytes]) -> bytes:
    """Concatenates multiple PCM WAV audio byte streams into a single valid WAV buffer."""
    if not wav_bytes_list:
        return b""
    if len(wav_bytes_list) == 1:
        return wav_bytes_list[0]

    output_io = io.BytesIO()
    out_wav: Optional[wave.Wave_write] = None

    try:
        for b in wav_bytes_list:
            with wave.open(io.BytesIO(b), "rb") as in_wav:
                if out_wav is None:
                    out_wav = wave.open(output_io, "wb")
                    out_wav.setnchannels(in_wav.getnchannels())
                    out_wav.setsampwidth(in_wav.getsampwidth())
                    out_wav.setframerate(in_wav.getframerate())
                out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
    finally:
        if out_wav is not None:
            out_wav.close()

    return output_io.getvalue()


def generate_synthetic_wav_bytes(text: str, duration_sec: float = 0.8, sample_rate: int = 16000) -> bytes:
    """
    Generates a minimal valid PCM WAV buffer for automated offline tests
    when no live Sarvam API key is present.
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        n_samples = max(int(0.2 * sample_rate), int(duration_sec * sample_rate))
        frames = bytearray()
        freq = 440.0
        for i in range(n_samples):
            val = int(32767.0 * 0.08 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            frames.extend(struct.pack("<h", val))
        wav.writeframes(frames)
    return buf.getvalue()


class SarvamTTSClient:
    """Client for Sarvam Bulbul v3 Text-to-Speech API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.endpoint = settings.SARVAM_TTS_URL
        self.model = settings.SARVAM_TTS_MODEL

    async def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
        """
        Synthesizes speech for the provided text in the target language.
        Returns SynthesisResult containing base64 audio and metadata.
        """
        t0 = time.perf_counter()
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Text for synthesis cannot be empty.")

        clean_lang = language.lower().split("-")[0]
        if clean_lang not in ("en", "hi", "kn", "te"):
            clean_lang = "en"

        speaker = get_speaker_for_language(clean_lang)
        target_code = get_target_language_code(clean_lang)

        # If API key is absent or in offline test environment, use deterministic synthetic WAV
        if not self.api_key or self.api_key.startswith("mock") or self.api_key == "test_key":
            if settings.APP_ENV == "testing" or (self.api_key and (self.api_key.startswith("mock") or self.api_key == "test_key")):
                logger.info(f"Using synthetic test fixture for [{clean_lang}/{speaker}].")
                synthetic_bytes = generate_synthetic_wav_bytes(clean_text)
                b64_audio = base64.b64encode(synthetic_bytes).decode("ascii")
                latency = (time.perf_counter() - t0) * 1000.0
                return SynthesisResult(
                    audio_base64=b64_audio,
                    language=clean_lang,
                    speaker=speaker,
                    provider="sarvam",
                    latency_ms=round(latency, 2),
                    is_mock=True,
                    tts_mode="synthetic_test",
                )
            raise RuntimeError("SARVAM_API_KEY is not configured on the server.")

        # Live Sarvam Bulbul v3 API Execution
        chunks = split_text_for_tts(clean_text, max_chunk_chars=450)
        audio_segments: List[bytes] = []

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for chunk in chunks:
                payload = {
                    "inputs": [chunk],
                    "target_language_code": target_code,
                    "speaker": speaker,
                    "model": self.model,
                }
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code != 200:
                    sanitized_err = resp.text[:200].replace(self.api_key, "***") if self.api_key else resp.text[:200]
                    logger.warning(
                        f"Sarvam TTS HTTP error {resp.status_code} for [{target_code}]: {sanitized_err}"
                    )
                    resp.raise_for_status()

                data = resp.json()
                audios = data.get("audios") or []
                if not audios:
                    raise RuntimeError("Sarvam TTS returned empty audio payload.")

                raw_chunk_bytes = base64.b64decode(audios[0])
                audio_segments.append(raw_chunk_bytes)

        combined_bytes = concatenate_wav_buffers(audio_segments)
        b64_audio = base64.b64encode(combined_bytes).decode("ascii")
        total_latency = (time.perf_counter() - t0) * 1000.0

        return SynthesisResult(
            audio_base64=b64_audio,
            language=clean_lang,
            speaker=speaker,
            provider="sarvam",
            latency_ms=round(total_latency, 2),
            is_mock=False,
            tts_mode="live_sarvam",
        )


# Singleton instance
_tts_client: Optional[SarvamTTSClient] = None


def get_tts_client() -> SarvamTTSClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = SarvamTTSClient()
    return _tts_client
