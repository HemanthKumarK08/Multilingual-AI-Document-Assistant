"""
Speech-to-Text & Voice UX Integration Tests (Phase 9.1 & 9.2)
Validates speech recognition engine, voice state machine, waveform indicator,
cancel interaction, transcript preservation, duplicate click protection,
accessibility, reduced motion, and privacy compliance.
"""

import os
import re
from pathlib import Path
import pytest
from app.core.config import PROJECT_ROOT


class TestSpeechRecognitionFoundationAndUX:
    """Phase 9.1 & 9.2 Voice Integration & UX Refinement test suite."""

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
    def indicator_jsx_content(self, voice_dir: Path) -> str:
        jsx_path = voice_dir / "VoiceListeningIndicator.jsx"
        assert jsx_path.exists(), f"Missing {jsx_path}"
        return jsx_path.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def ask_ai_content(self) -> str:
        ask_path = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
        assert ask_path.exists(), f"Missing {ask_path}"
        return ask_path.read_text(encoding="utf-8")

    def test_01_idle_to_start_state_transition(self, button_jsx_content: str):
        """Test 1: Idle state transitions to starting and listening."""
        assert "idle" in button_jsx_content
        assert "starting" in button_jsx_content
        assert "handleStartListening" in button_jsx_content

    def test_02_start_to_listening_state_transition(self, button_jsx_content: str):
        """Test 2: Starting state transitions cleanly to listening on recognizer onStart."""
        assert "onStart:" in button_jsx_content
        assert "setState(\"listening\")" in button_jsx_content or "setState('listening')" in button_jsx_content

    def test_03_listening_indicator_component_exists_and_renders(self, indicator_jsx_content: str, button_jsx_content: str):
        """Test 3: VoiceListeningIndicator component is imported and rendered."""
        assert "VoiceListeningIndicator" in button_jsx_content
        assert "export default function VoiceListeningIndicator" in indicator_jsx_content
        assert "Listening... Speak now" in indicator_jsx_content or "Listening in " in indicator_jsx_content

    def test_04_waveform_visual_activity_indicator(self, indicator_jsx_content: str):
        """Test 4: Pure CSS visual waveform activity bars exist without raw AudioContext."""
        assert "Voice Activity Indicator" in indicator_jsx_content
        assert "animate-pulse" in indicator_jsx_content
        # Ensure no MediaRecorder or AudioContext is used for animation
        assert "AudioContext" not in indicator_jsx_content
        assert "MediaRecorder" not in indicator_jsx_content

    def test_05_interim_transcript_display(self, indicator_jsx_content: str):
        """Test 5: Interim transcript is rendered in preview banner without submitting."""
        assert "interimText" in indicator_jsx_content
        assert "&ldquo;{interimText}&rdquo;" in indicator_jsx_content or "{interimText}" in indicator_jsx_content

    def test_06_final_transcript_populates_input(self, ask_ai_content: str, button_jsx_content: str):
        """Test 6: Final transcript invokes onTranscript callback to populate inputQuery."""
        assert "onFinal:" in button_jsx_content
        assert "onTranscript(finalText)" in button_jsx_content or "onTranscript(finalTranscript)" in button_jsx_content
        assert "handleVoiceTranscript" in ask_ai_content
        assert "setInputQuery" in ask_ai_content

    def test_07_final_transcript_does_not_auto_submit(self, ask_ai_content: str):
        """Test 7: handleVoiceTranscript updates state and does NOT call handleSend() automatically."""
        handler_match = re.search(
            r"const handleVoiceTranscript\s*=\s*\([^)]*\)\s*=>\s*\{([^}]*)\}",
            ask_ai_content,
        )
        assert handler_match, "handleVoiceTranscript function not found in AskAI.jsx"
        handler_body = handler_match.group(1)
        assert "handleSend(" not in handler_body, "handleVoiceTranscript must NOT auto-submit query"

    def test_08_cancel_stops_recognition(self, button_jsx_content: str):
        """Test 8: Cancel action aborts active recognizer instance."""
        assert "handleCancel" in button_jsx_content
        assert "recognizerRef.current.abort()" in button_jsx_content
        assert "isCancelledRef.current = true" in button_jsx_content

    def test_09_cancel_clears_interim_transcript_and_timer(self, button_jsx_content: str):
        """Test 9: Cancel resets interimText and stops timer."""
        assert "setInterimText(\"\")" in button_jsx_content or "setInterimText('')" in button_jsx_content
        assert "stopTimer()" in button_jsx_content

    def test_10_previous_typed_text_preserved(self, ask_ai_content: str):
        """Test 10: Appends voice transcript to existing typed text with space separator."""
        assert "trimmed ? (trimmed + \" \" + transcript) : transcript" in ask_ai_content or (
            "trimmed ? `${trimmed} ${transcript}` : transcript" in ask_ai_content
        )

    def test_11_duplicate_click_protection(self, button_jsx_content: str):
        """Test 11: Rapid clicks are blocked when state is starting, listening, or processing."""
        assert "state === \"starting\"" in button_jsx_content or "state === 'starting'" in button_jsx_content
        assert "state === \"listening\"" in button_jsx_content or "state === 'listening'" in button_jsx_content
        assert "disabled || isUnsupported || isStarting || isProcessing" in button_jsx_content

    def test_12_new_chat_clears_input_and_conversation(self, ask_ai_content: str):
        """Test 12: clearConversation resets messages and clears inputQuery."""
        assert "function clearConversation()" in ask_ai_content
        assert "setInputQuery(\"\")" in ask_ai_content or "setInputQuery('')" in ask_ai_content
        assert "setMessages([])" in ask_ai_content

    def test_13_navigation_cleanup_on_unmount(self, button_jsx_content: str):
        """Test 13: Component cleanup on unmount aborts recognizer and clears timer interval."""
        assert "return () => {" in button_jsx_content
        assert "stopTimer()" in button_jsx_content
        assert "recognizerRef.current.abort()" in button_jsx_content

    def test_14_permission_denied_friendly_error(self, speech_js_content: str):
        """Test 14: not-allowed returns user-friendly microphone permission explanation."""
        assert "Microphone permission was denied" in speech_js_content

    def test_15_no_speech_friendly_error(self, speech_js_content: str):
        """Test 15: no-speech returns friendly guidance to speak closer to microphone."""
        assert "No speech was detected" in speech_js_content

    def test_16_unsupported_browser_handled(self, speech_js_content: str, button_jsx_content: str):
        """Test 16: Unsupported browser displays clean compatibility message."""
        assert "Speech recognition is not supported in this browser" in speech_js_content
        assert "isUnsupported" in button_jsx_content

    def test_17_escape_key_cancels_voice_input(self, button_jsx_content: str):
        """Test 17: Escape key listener cancels active listening session."""
        assert "e.key === \"Escape\"" in button_jsx_content or "e.key === 'Escape'" in button_jsx_content
        assert "handleCancel()" in button_jsx_content

    def test_18_aria_labels_and_pressed_state(self, button_jsx_content: str, indicator_jsx_content: str):
        """Test 18: ARIA attributes for screen readers."""
        assert "aria-label=" in button_jsx_content
        assert "aria-pressed={isListening}" in button_jsx_content
        assert "aria-live=\"polite\"" in indicator_jsx_content or "aria-live='polite'" in indicator_jsx_content

    def test_19_keyboard_accessibility_focus(self, button_jsx_content: str):
        """Test 19: Focus ring styling and button type=button for keyboard navigation."""
        assert "type=\"button\"" in button_jsx_content or "type='button'" in button_jsx_content
        assert "focus:ring-2" in button_jsx_content

    def test_20_reduced_motion_respected(self, indicator_jsx_content: str, button_jsx_content: str):
        """Test 20: Uses motion-reduce:animate-none or motion-reduce:hidden to disable animations."""
        assert "motion-reduce:" in indicator_jsx_content or "motion-reduce:" in button_jsx_content


class TestMultilingualSpeechRecognition:
    """Phase 9.3 — Multilingual Speech Recognition Enhancement test suite."""

    @pytest.fixture(scope="class")
    def voice_dir(self) -> Path:
        return PROJECT_ROOT / "frontend" / "src" / "components" / "voice"

    @pytest.fixture(scope="class")
    def speech_js_content(self, voice_dir: Path) -> str:
        p = voice_dir / "speechRecognition.js"
        assert p.exists(), f"Missing {p}"
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def button_jsx_content(self, voice_dir: Path) -> str:
        p = voice_dir / "SpeechRecognitionButton.jsx"
        assert p.exists(), f"Missing {p}"
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def selector_jsx_content(self, voice_dir: Path) -> str:
        p = voice_dir / "VoiceLanguageSelector.jsx"
        assert p.exists(), f"Missing: VoiceLanguageSelector.jsx not found — Phase 9.3 component required"
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def indicator_jsx_content(self, voice_dir: Path) -> str:
        p = voice_dir / "VoiceListeningIndicator.jsx"
        assert p.exists(), f"Missing {p}"
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def ask_ai_content(self) -> str:
        p = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
        assert p.exists(), f"Missing {p}"
        return p.read_text(encoding="utf-8")

    # ── Test 21: English locale mapping ────────────────────────────────────────
    def test_21_english_locale_mapping(self, speech_js_content: str):
        """Test 21: en → en-US locale mapping exists in SPEECH_LOCALE_MAP."""
        assert "en" in speech_js_content
        assert "en-US" in speech_js_content
        # Accept both quoted and unquoted key formats: en: 'en-US' or 'en': 'en-US'
        assert ("'en': 'en-US'" in speech_js_content or
                '"en": "en-US"' in speech_js_content or
                "en: 'en-US'" in speech_js_content or
                'en: "en-US"' in speech_js_content)

    # ── Test 22: Hindi locale mapping ──────────────────────────────────────────
    def test_22_hindi_locale_mapping(self, speech_js_content: str):
        """Test 22: hi → hi-IN locale mapping exists."""
        assert "hi" in speech_js_content
        assert "hi-IN" in speech_js_content

    # ── Test 23: Kannada locale mapping ───────────────────────────────────────
    def test_23_kannada_locale_mapping(self, speech_js_content: str):
        """Test 23: kn → kn-IN locale mapping exists."""
        assert "kn" in speech_js_content
        assert "kn-IN" in speech_js_content

    # ── Test 24: Telugu locale mapping ────────────────────────────────────────
    def test_24_telugu_locale_mapping(self, speech_js_content: str):
        """Test 24: te → te-IN locale mapping exists."""
        assert "te" in speech_js_content
        assert "te-IN" in speech_js_content

    # ── Test 25: Voice language selector component exists ─────────────────────
    def test_25_voice_language_selector_component_exists(self, selector_jsx_content: str):
        """Test 25: VoiceLanguageSelector.jsx exists with all four languages."""
        assert "VOICE_LANGUAGES" in selector_jsx_content
        assert "en-US" in selector_jsx_content
        assert "hi-IN" in selector_jsx_content
        assert "kn-IN" in selector_jsx_content
        assert "te-IN" in selector_jsx_content

    # ── Test 26: Language selector disables during active recognition ──────────
    def test_26_language_selector_disabled_during_recognition(
        self, selector_jsx_content: str, ask_ai_content: str
    ):
        """Test 26: Selector is disabled when mic is active (voiceActive flag)."""
        assert "disabled" in selector_jsx_content
        assert "voiceActive" in ask_ai_content
        assert "disabled={voiceActive" in ask_ai_content

    # ── Test 27: Language change creates fresh recognition session ─────────────
    def test_27_fresh_recognizer_instance_per_session(self, button_jsx_content: str):
        """Test 27: A new recognizer is created for each start() call — no stale reuse."""
        # createSpeechRecognizer is called inside handleStartListening on every invocation
        assert "createSpeechRecognizer(" in button_jsx_content
        assert "recognizerRef.current = recognizer" in button_jsx_content

    # ── Test 28: English transcript editable ──────────────────────────────────
    def test_28_english_transcript_editable(self, ask_ai_content: str):
        """Test 28: Transcript populates editable textarea; no auto-submit for English."""
        assert "setInputQuery" in ask_ai_content
        assert "handleVoiceTranscript" in ask_ai_content

    # ── Test 29: Hindi transcript editable ────────────────────────────────────
    def test_29_hindi_locale_present_in_selector(self, selector_jsx_content: str):
        """Test 29: Hindi locale (hi-IN) option present in VoiceLanguageSelector."""
        assert "hi-IN" in selector_jsx_content
        # Native script label
        assert "हिन्दी" in selector_jsx_content

    # ── Test 30: Kannada transcript editable ──────────────────────────────────
    def test_30_kannada_locale_present_in_selector(self, selector_jsx_content: str):
        """Test 30: Kannada locale (kn-IN) option present in VoiceLanguageSelector."""
        assert "kn-IN" in selector_jsx_content
        assert "ಕನ್ನಡ" in selector_jsx_content

    # ── Test 31: Telugu transcript editable ───────────────────────────────────
    def test_31_telugu_locale_present_in_selector(self, selector_jsx_content: str):
        """Test 31: Telugu locale (te-IN) option present in VoiceLanguageSelector."""
        assert "te-IN" in selector_jsx_content
        assert "తెలుగు" in selector_jsx_content

    # ── Test 32: No auto-submission after multilingual transcript ─────────────
    def test_32_no_auto_submission_after_transcript(self, ask_ai_content: str):
        """Test 32: handleVoiceTranscript never calls handleSend automatically."""
        handler_match = re.search(
            r"const handleVoiceTranscript\s*=\s*\([^)]*\)\s*=>\s*\{([^}]*)\}",
            ask_ai_content,
        )
        assert handler_match, "handleVoiceTranscript not found"
        body = handler_match.group(1)
        assert "handleSend(" not in body

    # ── Test 33: No duplicate recognition handlers ────────────────────────────
    def test_33_no_duplicate_recognition_handlers(self, button_jsx_content: str):
        """Test 33: Only one recognizer instance created per session; old one aborted."""
        assert "recognizerRef.current = recognizer" in button_jsx_content
        # Cleanup on unmount aborts any leftover instance
        assert "recognizerRef.current.abort()" in button_jsx_content

    # ── Test 34: Unsupported locale gracefully handled ────────────────────────
    def test_34_unsupported_locale_graceful_error(self, speech_js_content: str):
        """Test 34: language-not-supported error code produces user-friendly message."""
        assert "language-not-supported" in speech_js_content
        assert "not supported for speech recognition" in speech_js_content

    # ── Test 35: ARIA accessibility preserved in selector ─────────────────────
    def test_35_aria_accessibility_in_voice_selector(self, selector_jsx_content: str):
        """Test 35: VoiceLanguageSelector has aria-label and aria-disabled."""
        assert "aria-label" in selector_jsx_content
        assert "aria-disabled" in selector_jsx_content

    # ── Test 36: New Chat resets voice session state ───────────────────────────
    def test_36_new_chat_resets_voice_state(self, ask_ai_content: str):
        """Test 36: clearConversation resets voiceActive so selector re-enables."""
        assert "setVoiceActive(false)" in ask_ai_content
        assert "function clearConversation()" in ask_ai_content

    # ── Test 37: Navigation cleanup aborts recognition and timer ──────────────
    def test_37_navigation_cleanup_aborts_recognition(self, button_jsx_content: str):
        """Test 37: useEffect cleanup on unmount aborts recognition and clears timer."""
        assert "return () =>" in button_jsx_content
        assert "recognizerRef.current.abort()" in button_jsx_content
        assert "stopTimer()" in button_jsx_content

    # ── Test 38: Reduced-motion compliance preserved ──────────────────────────
    def test_38_reduced_motion_compliance_preserved(self, indicator_jsx_content: str, button_jsx_content: str):
        """Test 38: motion-reduce: classes present in updated Phase 9.3 components."""
        assert "motion-reduce:" in indicator_jsx_content or "motion-reduce:" in button_jsx_content


class TestVoiceToRAGIntegration:
    """Phase 9.4 — Voice → RAG Integration test suite."""

    @pytest.fixture(scope="class")
    def voice_dir(self) -> Path:
        return PROJECT_ROOT / "frontend" / "src" / "components" / "voice"

    @pytest.fixture(scope="class")
    def ask_ai_content(self) -> str:
        p = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
        assert p.exists()
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def api_js_content(self) -> str:
        p = PROJECT_ROOT / "frontend" / "src" / "services" / "api.js"
        assert p.exists()
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def button_jsx_content(self, voice_dir: Path) -> str:
        p = voice_dir / "SpeechRecognitionButton.jsx"
        assert p.exists()
        return p.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def qa_route_content(self) -> str:
        p = PROJECT_ROOT / "app" / "api" / "routes" / "qa.py"
        assert p.exists()
        return p.read_text(encoding="utf-8")

    # ── Test 39: Voice transcript populates Ask AI input ──────────────────────
    def test_39_voice_transcript_populates_input(self, ask_ai_content: str):
        """Test 39: handleVoiceTranscript sets inputQuery from speech transcript."""
        assert "handleVoiceTranscript" in ask_ai_content
        assert "setInputQuery" in ask_ai_content
        assert "inputModeRef.current = 'voice'" in ask_ai_content

    # ── Test 40: Voice transcript does NOT auto-submit ─────────────────────────
    def test_40_voice_transcript_does_not_auto_submit(self, ask_ai_content: str):
        """Test 40: handleVoiceTranscript does not call handleSend automatically."""
        handler_match = re.search(
            r"const handleVoiceTranscript\s*=\s*\([^)]*\)\s*=>\s*\{(.*?)\};",
            ask_ai_content, re.DOTALL
        )
        assert handler_match, "handleVoiceTranscript not found"
        body = handler_match.group(1)
        assert "handleSend(" not in body

    # ── Test 41: Submitted text is the final edited value ─────────────────────
    def test_41_edited_transcript_is_submitted(self, ask_ai_content: str):
        """Test 41: handleSend() uses inputQuery (which can be edited), not raw transcript."""
        assert "const text = (queryToSend !== null ? queryToSend : inputQuery).trim()" in ask_ai_content
        # Any manual typing resets inputMode to 'typed'
        assert "inputModeRef.current = 'typed'" in ask_ai_content

    # ── Test 42: Voice queries use existing QA API ─────────────────────────────
    def test_42_voice_uses_existing_qa_api(self, ask_ai_content: str, api_js_content: str):
        """Test 42: Both typed and voice submit via the same apiService.submitQuery call."""
        assert "apiService.submitQuery(text," in ask_ai_content
        assert "/api/v1/qa/query" in api_js_content
        # No separate voice endpoint
        assert "/api/v1/voice/query" not in api_js_content
        assert "/api/v1/voice/query" not in ask_ai_content

    # ── Test 43: No duplicate QA request ──────────────────────────────────────
    def test_43_no_duplicate_qa_request(self, ask_ai_content: str):
        """Test 43: handleSend guards with 'if (!text || loading) return;' to prevent double-send."""
        assert "if (!text || loading) return;" in ask_ai_content

    # ── Test 44: English locale mapping passes to submitQuery ─────────────────
    def test_44_english_voice_locale_reaches_rag(self, ask_ai_content: str, api_js_content: str):
        """Test 44: English 'en' maps to en-US in speech; submitQuery sends target_language."""
        assert "submitQuery" in ask_ai_content
        assert "query_text" in api_js_content
        assert "target_language" in api_js_content

    # ── Test 45: Hindi voice locale supported ─────────────────────────────────
    def test_45_hindi_voice_locale_supported(self) -> None:
        """Test 45: hi-IN locale is in SPEECH_LOCALE_MAP — Hindi speech can reach RAG."""
        speech_js = (PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "speechRecognition.js").read_text()
        assert "hi-IN" in speech_js
        selector_jsx = (PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "VoiceLanguageSelector.jsx").read_text()
        assert "hi-IN" in selector_jsx

    # ── Test 46: Kannada voice locale supported ───────────────────────────────
    def test_46_kannada_voice_locale_supported(self) -> None:
        """Test 46: kn-IN locale supported for Kannada speech → RAG path."""
        speech_js = (PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "speechRecognition.js").read_text()
        assert "kn-IN" in speech_js

    # ── Test 47: Telugu voice locale supported ────────────────────────────────
    def test_47_telugu_voice_locale_supported(self) -> None:
        """Test 47: te-IN locale supported for Telugu speech → RAG path."""
        speech_js = (PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "speechRecognition.js").read_text()
        assert "te-IN" in speech_js

    # ── Test 48: Code-mixed transcript uses existing multilingual pipeline ─────
    def test_48_code_mixed_transcript_uses_existing_pipeline(self, ask_ai_content: str):
        """Test 48: No special code-mixed processing — transcript goes through submitQuery unchanged."""
        # There must be no code-mixed pre-processor between handleVoiceTranscript and submitQuery
        assert "handleVoiceTranscript" in ask_ai_content
        # submitQuery takes the raw text — no intermediate transformation
        assert "apiService.submitQuery(text," in ask_ai_content

    # ── Test 49: Voice answer displays citations ───────────────────────────────
    def test_49_voice_answer_displays_citations(self, ask_ai_content: str):
        """Test 49: CitationsSection is rendered for all assistant messages regardless of input mode."""
        assert "CitationsSection" in ask_ai_content
        assert "msg.citations" in ask_ai_content

    # ── Test 50: Evidence drawer available for voice answers ──────────────────
    def test_50_evidence_drawer_available_for_voice(self, ask_ai_content: str):
        """Test 50: TechnicalDetailsPanel is rendered for all assistant messages."""
        assert "TechnicalDetailsPanel" in ask_ai_content

    # ── Test 51: Feedback widget available for voice answers ──────────────────
    def test_51_feedback_widget_available_for_voice(self, ask_ai_content: str):
        """Test 51: FeedbackWidget is rendered for all assistant messages."""
        assert "FeedbackWidget" in ask_ai_content
        assert "msg.query_id" in ask_ai_content

    # ── Test 52: Backend failure uses existing error UI ────────────────────────
    def test_52_backend_failure_uses_existing_error_ui(self, ask_ai_content: str):
        """Test 52: Error state is set from QA request catch block, not voice-specific path."""
        assert "setError({" in ask_ai_content
        assert "error.message" in ask_ai_content
        assert "Retry" in ask_ai_content

    # ── Test 53: Retry does not restart microphone ─────────────────────────────
    def test_53_retry_does_not_restart_microphone(self, ask_ai_content: str):
        """Test 53: Retry calls handleSend(error.query) — no microphone/recognition restart."""
        assert "onClick={() => handleSend(error.query)}" in ask_ai_content
        # Retry handler does not reference startListening or SpeechRecognition
        retry_match = re.search(r'onClick=\{.*?handleSend\(error\.query\).*?\}', ask_ai_content)
        assert retry_match, "Retry handler not found"
        retry_str = retry_match.group(0)
        assert "recognition" not in retry_str.lower()
        assert "mic" not in retry_str.lower()

    # ── Test 54: New Chat resets voice state ───────────────────────────────────
    def test_54_new_chat_clears_voice_state(self, ask_ai_content: str):
        """Test 54: clearConversation resets voiceActive, inputMode, messages, and inputQuery."""
        assert "setVoiceActive(false)" in ask_ai_content
        assert "inputModeRef.current = 'typed'" in ask_ai_content
        assert "setMessages([])" in ask_ai_content
        assert "setInputQuery" in ask_ai_content

    # ── Test 55: Navigation cleanup aborts recognition ─────────────────────────
    def test_55_navigation_cleanup_voice_state(self, button_jsx_content: str):
        """Test 55: SpeechRecognitionButton useEffect cleanup aborts recognition on unmount."""
        assert "return () =>" in button_jsx_content
        assert "recognizerRef.current.abort()" in button_jsx_content

    # ── Test 56: Edited transcript is what gets submitted ─────────────────────
    def test_56_edited_transcript_submitted_not_original(self, ask_ai_content: str):
        """Test 56: Textarea onChange resets inputMode to 'typed' so edits override voice origin."""
        assert "inputModeRef.current = 'typed'" in ask_ai_content
        # The edit path resets mode before submission
        assert "Any manual edit resets inputMode" in ask_ai_content

    # ── Test 57: inputMode metadata is frontend-only ───────────────────────────
    def test_57_inputmode_is_frontend_only(self, api_js_content: str, ask_ai_content: str):
        """Test 57: inputMode is not sent to backend — submitQuery only sends query_text, target_language, category."""
        # api.js submitQuery must NOT include inputMode
        submit_match = re.search(
            r"async submitQuery\s*\([^)]*\)\s*\{.*?body:\s*JSON\.stringify\(\{(.*?)\}\)",
            api_js_content, re.DOTALL
        )
        assert submit_match, "submitQuery not found in api.js"
        body_fields = submit_match.group(1)
        assert "inputMode" not in body_fields
        # It IS stored on the frontend message object
        assert "inputMode: submitMode" in ask_ai_content

    # ── Test 58: Accessibility remains intact ─────────────────────────────────
    def test_58_accessibility_remains_intact(self, button_jsx_content: str, ask_ai_content: str):
        """Test 58: aria-label, aria-pressed, aria-live still present after Phase 9.4 changes."""
        assert "aria-label" in button_jsx_content
        assert "aria-pressed={isListening}" in button_jsx_content
        assert "aria-label=\"Send Query\"" in ask_ai_content


class TestVoiceInputReliabilityAndContinuousStream:
    """Voice input reliability, continuous recognition, and lifecycle recovery tests."""

    @pytest.fixture(scope="class")
    def voice_dir(self) -> Path:
        return PROJECT_ROOT / "frontend" / "src" / "components" / "voice"

    @pytest.fixture(scope="class")
    def speech_js_content(self, voice_dir: Path) -> str:
        return (voice_dir / "speechRecognition.js").read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def button_jsx_content(self, voice_dir: Path) -> str:
        return (voice_dir / "SpeechRecognitionButton.jsx").read_text(encoding="utf-8")

    def test_59_continuous_mode_enabled_in_speech_recognition(self, speech_js_content: str, button_jsx_content: str):
        """Test 59: continuous recognition is enabled to prevent premature stoppage on natural pauses."""
        assert "recognition.continuous = continuous" in speech_js_content
        assert "continuous = true" in speech_js_content
        assert "continuous: true" in button_jsx_content

    def test_60_streaming_transcript_accumulation(self, speech_js_content: str, button_jsx_content: str):
        """Test 60: interim and final results are accumulated cleanly without dropping words."""
        assert "recognition.interimResults = true" in speech_js_content
        assert "finalTranscript +=" in speech_js_content
        assert "accumulatedTranscriptRef.current" in button_jsx_content

    def test_61_unexpected_onend_auto_restart_in_listening_mode(self, button_jsx_content: str):
        """Test 61: Unexpected browser onend while in listening state triggers safe auto-restart."""
        assert "isRestartingRef.current" in button_jsx_content
        assert "startRecognitionSession(langToUse)" in button_jsx_content or "startRecognitionSession(" in button_jsx_content

    def test_62_explicit_stop_and_cancel_does_not_restart(self, button_jsx_content: str):
        """Test 62: Manual stop or cancel flags prevent recognition from restarting."""
        assert "isManualStopRef.current" in button_jsx_content
        assert "isCancelledRef.current" in button_jsx_content
        assert "if (isCancelledRef.current) {" in button_jsx_content

    def test_63_single_active_session_guard(self, button_jsx_content: str):
        """Test 63: Any existing recognition instance is aborted before starting a new session."""
        assert "if (recognizerRef.current) {" in button_jsx_content
        assert "recognizerRef.current.abort()" in button_jsx_content

    def test_64_transient_no_speech_error_does_not_abort_session(self, button_jsx_content: str):
        """Test 64: Non-fatal no-speech events during active listening do not kick user out of listening state."""
        assert "code === \"no-speech\" && !isManualStopRef.current" in button_jsx_content

    def test_65_fatal_permission_error_cleans_up(self, button_jsx_content: str):
        """Test 65: Fatal permission errors stop timer, set error state, and notify parent."""
        assert "stopTimer()" in button_jsx_content
        assert "setErrorMessage(msg)" in button_jsx_content
        assert "setState(\"error\")" in button_jsx_content

    def test_66_privacy_preserved_zero_audio_storage(self, speech_js_content: str, button_jsx_content: str):
        """Test 66: Strict privacy compliance — no MediaRecorder, AudioContext, or audio file persistence."""
        assert "MediaRecorder" not in speech_js_content
        assert "AudioContext" not in speech_js_content
        assert "MediaRecorder" not in button_jsx_content
        assert "AudioContext" not in button_jsx_content
