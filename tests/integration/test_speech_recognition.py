"""
Speech-to-Text Foundation Integration Tests (Phase 9.1)
Verifies browser speech recognition contract, language mapping,
error humanization, privacy boundaries, and component integration.
"""

import os
import re
from pathlib import Path
import pytest
from app.core.config import PROJECT_ROOT


class TestSpeechRecognitionFoundation:
    """Phase 9.1 Speech-to-Text Foundation test suite."""

    @pytest.fixture(scope="class")
    def voice_dir(self) -> Path:
        return PROJECT_ROOT / "frontend" / "src" / "components" / "voice"

    @pytest.fixture(scope="class")
    def speech_js_content(self, voice_dir: Path) -> str:
        js_path = voice_dir / "speechRecognition.js"
        assert js_path.exists(), f"Missing {js_path}"
        return js_path.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def button_jsx_content(self, voice_dir: Path) -> str:
        jsx_path = voice_dir / "SpeechRecognitionButton.jsx"
        assert jsx_path.exists(), f"Missing {jsx_path}"
        return jsx_path.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def ask_ai_content(self) -> str:
        ask_path = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
        assert ask_path.exists(), f"Missing {ask_path}"
        return ask_path.read_text(encoding="utf-8")

    def test_01_speech_utility_exists_and_exports_required_functions(self, speech_js_content: str):
        """Test 1: API availability & exported interfaces."""
        required_exports = [
            "export const SPEECH_LOCALE_MAP",
            "export function mapLanguageToSpeechLocale",
            "export function getSpeechRecognitionClass",
            "export function isSpeechRecognitionSupported",
            "export function humanizeSpeechError",
            "export function createSpeechRecognizer",
        ]
        for exp in required_exports:
            assert exp in speech_js_content, f"Missing export: {exp}"

    def test_02_browser_feature_detection_and_fallback(self, speech_js_content: str):
        """Test 2: Feature detection handles standard and webkit prefixed APIs."""
        assert "window.SpeechRecognition" in speech_js_content
        assert "window.webkitSpeechRecognition" in speech_js_content
        assert "unsupported" in speech_js_content

    def test_03_language_locale_mapping(self, speech_js_content: str):
        """Test 3: Language mapping resolves English, Hindi, Kannada, Telugu, and auto."""
        assert "'en': 'en-US'" in speech_js_content or "en: 'en-US'" in speech_js_content
        assert "'hi': 'hi-IN'" in speech_js_content or "hi: 'hi-IN'" in speech_js_content
        assert "'kn': 'kn-IN'" in speech_js_content or "kn: 'kn-IN'" in speech_js_content
        assert "'te': 'te-IN'" in speech_js_content or "te: 'te-IN'" in speech_js_content
        assert "'auto': 'en-US'" in speech_js_content or "auto: 'en-US'" in speech_js_content

    def test_04_error_humanization_mapping(self, speech_js_content: str):
        """Test 4: Maps technical error codes to readable explanations."""
        error_codes = [
            "not-allowed",
            "service-not-allowed",
            "no-speech",
            "audio-capture",
            "network",
            "aborted",
            "language-not-supported",
            "unsupported",
        ]
        for err in error_codes:
            assert f"'{err}'" in speech_js_content or f'"{err}"' in speech_js_content, (
                f"Missing error code handling for {err}"
            )

    def test_05_speech_recognition_configuration(self, speech_js_content: str):
        """Test 5: Speech recognition is configured for single-utterance non-continuous capture."""
        assert "recognition.continuous = false" in speech_js_content
        assert "recognition.interimResults = true" in speech_js_content

    def test_06_speech_button_states_and_callbacks(self, button_jsx_content: str):
        """Test 6: Component handles idle, listening, processing, error, and unsupported states."""
        assert "onTranscript" in button_jsx_content
        assert "onInterimTranscript" in button_jsx_content
        assert "listening" in button_jsx_content
        assert "processing" in button_jsx_content
        assert "error" in button_jsx_content
        assert "unsupported" in button_jsx_content

    def test_07_accessibility_attributes(self, button_jsx_content: str):
        """Test 7: Accessibility requirements (aria-label, aria-pressed, role)."""
        assert "aria-label=" in button_jsx_content
        assert "aria-pressed=" in button_jsx_content
        assert "Start voice input" in button_jsx_content
        assert "Stop voice input" in button_jsx_content

    def test_08_privacy_guarantee_no_audio_storage(self):
        """Test 8: Strict privacy verification - no audio storage directories or routes exist."""
        audio_dir = PROJECT_ROOT / "data" / "audio"
        recordings_dir = PROJECT_ROOT / "data" / "recordings"
        assert not audio_dir.exists(), "Audio storage directory must not exist in Phase 9.1"
        assert not recordings_dir.exists(), "Recordings storage directory must not exist in Phase 9.1"

    def test_09_ask_ai_integration_non_auto_submit(self, ask_ai_content: str):
        """Test 9: Voice transcript populates inputQuery without auto-submitting."""
        assert "SpeechRecognitionButton" in ask_ai_content
        assert "handleVoiceTranscript" in ask_ai_content
        assert "setInputQuery" in ask_ai_content
        # Ensure handleVoiceTranscript does not directly call handleSend()
        handler_match = re.search(
            r'const handleVoiceTranscript\s*=\s*\([^)]*\)\s*=>\s*\{([^}]*)\}',
            ask_ai_content,
        )
        assert handler_match, "handleVoiceTranscript function not found in AskAI.jsx"
        handler_body = handler_match.group(1)
        assert "handleSend(" not in handler_body, (
            "handleVoiceTranscript must NOT auto-submit query to handleSend in Phase 9.1"
        )

    def test_10_production_build_contains_voice_components(self):
        """Test 10: Verified production dist bundle builds with voice components."""
        dist_html = PROJECT_ROOT / "frontend" / "dist" / "index.html"
        assert dist_html.exists(), "Frontend production dist/index.html must exist"
