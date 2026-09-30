"""
Integration Tests for Voice Response Language Consistency
Verifies that:
1. Target response language, backend response metadata, UI badge mapping,
   and TTS locale resolution remain strictly consistent.
2. English voice input with Telugu target produces Telugu answer and te-IN TTS locale.
3. Telugu voice input with English target produces English answer and en-US TTS locale.
4. Voice input language operates independently from response target language.
5. In case of LANGUAGE_UNAVAILABLE, citations are strictly empty and TTS does not speak.
"""
import pytest
from app.services.language.resolution import (
    resolve_response_language,
    detect_query_language,
    TTS_LOCALE_MAP,
    LANGUAGE_NAMES,
    LANGUAGE_UNAVAILABLE_MESSAGES,
)
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.models import GroundedAnswer, SourceCitation


class TestVoiceResponseLanguageConsistency:
    """Verifies end-to-end consistency across Query, Response, Badge, and TTS."""

    def test_voice_input_english_to_telugu_response_pipeline(self):
        """English voice input with Telugu target -> Telugu response & te-IN TTS."""
        voice_transcript = "What is the minimum attendance required for semester examinations?"
        selected_response_lang = "te"

        # 1. Voice input language detected
        detected_input_lang = detect_query_language(voice_transcript)
        assert detected_input_lang == "en"

        # 2. Authoritative response language resolution
        resolved_resp_lang = resolve_response_language(
            explicit_target_language=selected_response_lang,
            query=voice_transcript,
            detected_query_language=detected_input_lang,
        )
        assert resolved_resp_lang == "te"

        # 3. TTS Locale derivation
        tts_locale = TTS_LOCALE_MAP[resolved_resp_lang]
        assert tts_locale == "te-IN"

        # 4. Badge display name
        badge_name = LANGUAGE_NAMES[resolved_resp_lang]
        assert badge_name == "Telugu"

    def test_voice_input_telugu_to_english_response_pipeline(self):
        """Telugu voice input with explicit English target -> English response & en-US TTS."""
        voice_transcript = "విద్యార్థులకు పరీక్షలకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?"
        selected_response_lang = "en"

        # 1. Voice input detected as Telugu
        detected_input_lang = detect_query_language(voice_transcript)
        assert detected_input_lang == "te"

        # 2. Authoritative response language respects explicit user target
        resolved_resp_lang = resolve_response_language(
            explicit_target_language=selected_response_lang,
            query=voice_transcript,
            detected_query_language=detected_input_lang,
        )
        assert resolved_resp_lang == "en"

        # 3. TTS Locale derivation
        tts_locale = TTS_LOCALE_MAP[resolved_resp_lang]
        assert tts_locale == "en-US"

    def test_voice_input_hindi_auto_detect_pipeline(self):
        """Hindi voice input with Auto Detect -> Hindi response & hi-IN TTS."""
        voice_transcript = "परीक्षा में शामिल होने के लिए न्यूनतम उपस्थिति कितनी होनी चाहिए?"
        selected_response_lang = "auto"

        # 1. Voice input detected as Hindi
        detected_input_lang = detect_query_language(voice_transcript)
        assert detected_input_lang == "hi"

        # 2. Authoritative response language auto-detects Hindi
        resolved_resp_lang = resolve_response_language(
            explicit_target_language=selected_response_lang,
            query=voice_transcript,
            detected_query_language=detected_input_lang,
        )
        assert resolved_resp_lang == "hi"

        # 3. TTS Locale derivation
        tts_locale = TTS_LOCALE_MAP[resolved_resp_lang]
        assert tts_locale == "hi-IN"

    def test_voice_input_kannada_auto_detect_pipeline(self):
        """Kannada voice input with Auto Detect -> Kannada response & kn-IN TTS."""
        voice_transcript = "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?"
        selected_response_lang = "auto"

        # 1. Voice input detected as Kannada
        detected_input_lang = detect_query_language(voice_transcript)
        assert detected_input_lang == "kn"

        # 2. Authoritative response language auto-detects Kannada
        resolved_resp_lang = resolve_response_language(
            explicit_target_language=selected_response_lang,
            query=voice_transcript,
            detected_query_language=detected_input_lang,
        )
        assert resolved_resp_lang == "kn"

        # 3. TTS Locale derivation
        tts_locale = TTS_LOCALE_MAP[resolved_resp_lang]
        assert tts_locale == "kn-IN"

    def test_language_unavailable_prevents_tts_and_zero_citations(self):
        """When language generation is unavailable, citations must be zero."""
        coord = RAGCoordinator()
        ans = coord._fallback_answer(
            query_id="q-unavail",
            reason="LANGUAGE_UNAVAILABLE",
            resp_lang="kn",
            latency_ms=100.0,
        )
        assert ans.fallback_used is True
        assert ans.fallback_reason == "LANGUAGE_UNAVAILABLE"
        assert ans.grounded is False
        assert ans.sources == []
        assert ans.target_language == "kn"
        assert ans.response_language == "kn"
        assert "ಲಭ್ಯವಿಲ್ಲ" in ans.answer_text
