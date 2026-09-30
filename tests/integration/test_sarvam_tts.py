"""
Integration tests for Provider-backed Neural TTS (Sarvam Bulbul v3).
Verifies:
- Endpoint POST /api/v1/tts/synthesize
- Language mappings (en -> en-IN, hi -> hi-IN, te -> te-IN, kn -> kn-IN)
- Speaker selection (ratan, priya, neha, ishita)
- Exact sentences test matrix (English, Hindi, Telugu, Kannada)
- Sentence boundary splitting for long answers
- Security (no API key exposure)
- Independent voice selection per turn
"""

import base64
import wave
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.tts.sarvam import split_text_for_tts, get_tts_client, SarvamTTSClient
from app.core.config import settings

client = TestClient(app)


# ── Section L Test Matrix: Exact Sentences ───────────────────────────────────

TEST_MATRIX = [
    {
        "language": "en",
        "text": "The minimum attendance required is 75 percent.",
        "expected_speaker": settings.SARVAM_SPEAKER_EN,  # ratan
        "expected_lang_code": "en",
    },
    {
        "language": "hi",
        "text": "परीक्षा में शामिल होने के लिए न्यूनतम उपस्थिति 75 प्रतिशत होनी चाहिए।",
        "expected_speaker": settings.SARVAM_SPEAKER_HI,  # priya
        "expected_lang_code": "hi",
    },
    {
        "language": "te",
        "text": "పరీక్షకు హాజరు కావడానికి కనీసం 75 శాతం హాజరు ఉండాలి.",
        "expected_speaker": settings.SARVAM_SPEAKER_TE,  # neha
        "expected_lang_code": "te",
    },
    {
        "language": "kn",
        "text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ 75 ಶೇಕಡಾ ಹಾಜರಾತಿ ಇರಬೇಕು.",
        "expected_speaker": settings.SARVAM_SPEAKER_KN,  # ishita
        "expected_lang_code": "kn",
    },
]


@pytest.mark.parametrize("case", TEST_MATRIX)
def test_tts_matrix_exact_sentences(case):
    """Test synthesis for each language in the test matrix."""
    response = client.post(
        "/api/v1/tts/synthesize",
        json={"text": case["text"], "language": case["language"]},
    )
    assert response.status_code == 200, f"Failed for {case['language']}: {response.text}"
    data = response.json()

    assert data["provider"] == "sarvam"
    assert data["language"] == case["expected_lang_code"]
    assert data["voice"] == case["expected_speaker"]
    assert "audio" in data and len(data["audio"]) > 0

    # Verify base64 audio decodes to valid WAV
    audio_bytes = base64.b64decode(data["audio"])
    assert len(audio_bytes) > 44  # WAV header is 44 bytes
    assert audio_bytes[:4] == b"RIFF"
    assert audio_bytes[8:12] == b"WAVE"

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() in (16000, 22050, 24000)
        assert wav_file.getnframes() > 0


def test_tts_turn_independence():
    """Verify that turns in sequence each select their exact voice and do not leak or reuse."""
    turns = ["en", "hi", "te", "kn", "en"]
    expected_voices = [
        settings.SARVAM_SPEAKER_EN,
        settings.SARVAM_SPEAKER_HI,
        settings.SARVAM_SPEAKER_TE,
        settings.SARVAM_SPEAKER_KN,
        settings.SARVAM_SPEAKER_EN,
    ]

    for lang, expected_voice in zip(turns, expected_voices):
        resp = client.post(
            "/api/v1/tts/synthesize",
            json={"text": "Test speech utterance.", "language": lang},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == lang
        assert data["voice"] == expected_voice


def test_tts_long_answer_sentence_splitting():
    """Section K: Verify that answers exceeding max characters are split only at sentence boundaries."""
    long_text = (
        "IntelliExam requires a minimum score of 75.5 percent for eligibility. "
        "Visit https://example.com/api/v1/docs for more details on project DOC-1234. "
        "The model achieves 98.2 percent accuracy on test sets."
    )
    chunks = split_text_for_tts(long_text, max_chunk_chars=80)
    assert len(chunks) >= 2
    # Check that URLs and percentages are preserved without awkward splitting
    combined = " ".join(chunks)
    assert "75.5 percent" in combined
    assert "https://example.com/api/v1/docs" in combined
    assert "DOC-1234" in combined


def test_tts_security_no_api_key_leak():
    """Verify that SARVAM_API_KEY is never in the response JSON or headers."""
    resp = client.post(
        "/api/v1/tts/synthesize",
        json={"text": "Security test", "language": "en"},
    )
    assert resp.status_code == 200
    body_str = resp.text
    if settings.SARVAM_API_KEY:
        assert settings.SARVAM_API_KEY not in body_str
        for header, value in resp.headers.items():
            assert settings.SARVAM_API_KEY not in value
    assert "api-subscription-key" not in body_str
    assert "api_key" not in body_str
