"""
Phase 9.5 — Text-to-Speech Test Suite
Tests the textToSpeech.js utility and SpeakButton.jsx component via static analysis.
Real-browser TTS is tested manually (browser-native API not testable in headless pytest).
"""
import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tts_js() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "textToSpeech.js"
    assert p.exists(), "textToSpeech.js not found — Phase 9.5 utility required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def speak_button_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "SpeakButton.jsx"
    assert p.exists(), "SpeakButton.jsx not found — Phase 9.5 component required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ask_ai_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


# ── TTS-01: Feature Detection ─────────────────────────────────────────────────

def test_tts_01_feature_detection(tts_js: str):
    """TTS-01: isTTSSupported() checks both speechSynthesis and SpeechSynthesisUtterance."""
    assert "isTTSSupported" in tts_js
    assert "speechSynthesis" in tts_js
    assert "SpeechSynthesisUtterance" in tts_js
    assert "typeof window" in tts_js


# ── TTS-02: Speak button on assistant messages ────────────────────────────────

def test_tts_02_speak_button_on_assistant_messages(ask_ai_jsx: str):
    """TTS-02: SpeakButton is rendered only for assistant (non-user) messages."""
    assert "SpeakButton" in ask_ai_jsx
    assert "!isUser && msg.content" in ask_ai_jsx


# ── TTS-03: No speak button on user messages ──────────────────────────────────

def test_tts_03_no_speak_button_on_user_messages(ask_ai_jsx: str):
    """TTS-03: SpeakButton is inside a !isUser guard (never appears on user bubbles)."""
    speak_match = re.search(r'\{!isUser[^}]*msg\.content.*?<SpeakButton', ask_ai_jsx, re.DOTALL)
    assert speak_match, "SpeakButton must be inside a !isUser guard"


# ── TTS-04: Speak invokes SpeechSynthesis ────────────────────────────────────

def test_tts_04_speak_invokes_speech_synthesis(tts_js: str, speak_button_jsx: str):
    """TTS-04: speak() calls synth.speak(utterance) via the TTS controller."""
    assert "synth.speak(" in tts_js
    assert "createTTSController" in speak_button_jsx


# ── TTS-05: No automatic speech after AI response ────────────────────────────

def test_tts_05_no_auto_speak(ask_ai_jsx: str, speak_button_jsx: str):
    """TTS-05: TTS is not invoked automatically when a response arrives."""
    assert "autoPlay" not in speak_button_jsx
    assert "autoplay" not in speak_button_jsx.lower()
    assert "ctrl.speak()" not in ask_ai_jsx


# ── TTS-06: Speaking state is displayed ──────────────────────────────────────

def test_tts_06_speaking_state_displayed(speak_button_jsx: str):
    """TTS-06: 'speaking' state is tracked and reflected in the UI."""
    assert "'speaking'" in speak_button_jsx
    assert "isSpeaking" in speak_button_jsx
    assert "Stop reading" in speak_button_jsx


# ── TTS-07: Speech completion returns to idle ─────────────────────────────────

def test_tts_07_speech_completion_returns_to_idle(tts_js: str):
    """TTS-07: u.onend transitions state back to idle via onEnd callback."""
    assert "onEnd" in tts_js
    assert "u.onend" in tts_js


# ── TTS-08: Stop cancels speech ──────────────────────────────────────────────

def test_tts_08_stop_cancels_speech(tts_js: str, speak_button_jsx: str):
    """TTS-08: stop() calls synth.cancel() and controller exposes handleStop."""
    assert "synth.cancel()" in tts_js
    assert "handleStop" in speak_button_jsx
    assert "Stop reading" in speak_button_jsx


# ── TTS-09: Pause works ───────────────────────────────────────────────────────

def test_tts_09_pause_works(tts_js: str, speak_button_jsx: str):
    """TTS-09: pause() calls synth.pause() and Pause button renders while speaking."""
    assert "synth.pause()" in tts_js
    assert "handlePause" in speak_button_jsx
    assert "Pause reading" in speak_button_jsx


# ── TTS-10: Resume works ──────────────────────────────────────────────────────

def test_tts_10_resume_works(tts_js: str, speak_button_jsx: str):
    """TTS-10: resume() calls synth.resume() and Resume button renders when paused."""
    assert "synth.resume()" in tts_js
    assert "handleResume" in speak_button_jsx
    assert "Resume reading" in speak_button_jsx


# ── TTS-11: Single active speech session ─────────────────────────────────────

def test_tts_11_single_active_speech_session(tts_js: str, speak_button_jsx: str):
    """TTS-11: stopAllSpeech is called before new speak to prevent simultaneous audio."""
    assert "stopAllSpeech" in speak_button_jsx
    assert "stopAllSpeech" in tts_js


# ── TTS-12: Starting Answer B stops Answer A ─────────────────────────────────

def test_tts_12_starting_b_stops_a(tts_js: str):
    """TTS-12: synth.cancel() is called in speak() when synth.speaking or synth.pending."""
    assert "synth.speaking" in tts_js
    assert "synth.pending" in tts_js
    assert "synth.cancel()" in tts_js


# ── TTS-13: Rapid click protection ───────────────────────────────────────────

def test_tts_13_rapid_click_protection(speak_button_jsx: str):
    """TTS-13: 'starting' state disables the Speak button to prevent duplicate sessions."""
    assert "ttsState === 'starting'" in speak_button_jsx or "isStarting" in speak_button_jsx
    assert "Starting..." in speak_button_jsx


# ── TTS-14: Speak → Stop → Speak works ───────────────────────────────────────

def test_tts_14_speak_stop_speak(speak_button_jsx: str):
    """TTS-14: After stop(), state returns to idle and Speak button re-renders."""
    assert "safeSetState('idle')" in speak_button_jsx
    assert "isIdle" in speak_button_jsx


# ── TTS-15: Speak again after completion ──────────────────────────────────────

def test_tts_15_speak_again_after_completion(tts_js: str, speak_button_jsx: str):
    """TTS-15: onEnd → idle; idle state shows Speak button again."""
    assert "'idle'" in speak_button_jsx
    assert "onEnd" in tts_js


# ── TTS-16: New Chat stops TTS ───────────────────────────────────────────────

def test_tts_16_new_chat_stops_tts(ask_ai_jsx: str):
    """TTS-16: clearConversation() calls stopAllSpeech() before clearing messages."""
    assert "stopAllSpeech()" in ask_ai_jsx
    assert "setMessages([])" in ask_ai_jsx


# ── TTS-17: Navigation/unmount stops TTS ─────────────────────────────────────

def test_tts_17_unmount_stops_tts(speak_button_jsx: str):
    """TTS-17: useEffect cleanup calls stopAllSpeech on SpeakButton unmount."""
    assert "stopAllSpeech()" in speak_button_jsx
    assert "return () =>" in speak_button_jsx
    assert "isMountedRef.current = false" in speak_button_jsx


# ── TTS-18: Markdown stripped for speech ─────────────────────────────────────

def test_tts_18_markdown_converted_to_speech_text(tts_js: str):
    """TTS-18: markdownToSpeechText() strips #, **, *, `, [Source N], [Doc-*]."""
    assert "markdownToSpeechText" in tts_js
    assert "#{1,6}" in tts_js
    assert r"\*\*" in tts_js
    assert "Source" in tts_js


# ── TTS-19: Citation metadata not spoken ──────────────────────────────────────

def test_tts_19_citation_metadata_not_spoken(tts_js: str):
    """TTS-19: [Source N] and [Doc-*] markers are stripped from spoken text."""
    assert r"\[Source\s*\d+\]" in tts_js or "Source" in tts_js
    assert "Doc-" in tts_js


# ── TTS-20: Fallback answer can be spoken ────────────────────────────────────

def test_tts_20_fallback_answer_can_be_spoken(ask_ai_jsx: str):
    """TTS-20: SpeakButton renders for ALL assistant messages — no is_fallback gate."""
    speak_block = re.search(r'\{!isUser && msg\.content(.*?)<SpeakButton', ask_ai_jsx, re.DOTALL)
    assert speak_block, "SpeakButton must depend only on msg.content"
    assert "is_fallback" not in speak_block.group(1)


# ── TTS-21: TTS error handled gracefully ─────────────────────────────────────

def test_tts_21_tts_error_handled_gracefully(tts_js: str, speak_button_jsx: str):
    """TTS-21: onerror sets error state; UI shows dismissible error badge."""
    assert "u.onerror" in tts_js
    assert "onError(" in tts_js
    assert "'error'" in speak_button_jsx
    assert "Speech error" in speak_button_jsx


# ── TTS-22: Unsupported browser handled ───────────────────────────────────────

def test_tts_22_unsupported_browser_handled(tts_js: str, speak_button_jsx: str):
    """TTS-22: isTTSSupported() === false → SpeakButton shows 'TTS unavailable' message."""
    assert "isTTSSupported" in speak_button_jsx
    assert "TTS unavailable" in speak_button_jsx
    assert "isSupported: false" in tts_js


# ── TTS-23: Hindi locale mapping ─────────────────────────────────────────────

def test_tts_23_hindi_locale_mapping(ask_ai_jsx: str, tts_js: str):
    """TTS-23: Hindi (hi) → hi-IN locale for TTS voice selection."""
    assert "hi: 'hi-IN'" in ask_ai_jsx or '"hi": "hi-IN"' in ask_ai_jsx
    assert "hi-IN" in tts_js


# ── TTS-24: Kannada locale mapping ───────────────────────────────────────────

def test_tts_24_kannada_locale_mapping(ask_ai_jsx: str, tts_js: str):
    """TTS-24: Kannada (kn) → kn-IN locale for TTS voice selection."""
    assert "kn: 'kn-IN'" in ask_ai_jsx or '"kn": "kn-IN"' in ask_ai_jsx
    assert "kn-IN" in tts_js


# ── TTS-25: Telugu locale mapping ────────────────────────────────────────────

def test_tts_25_telugu_locale_mapping(ask_ai_jsx: str, tts_js: str):
    """TTS-25: Telugu (te) → te-IN locale for TTS voice selection."""
    assert "te: 'te-IN'" in ask_ai_jsx or '"te": "te-IN"' in ask_ai_jsx
    assert "te-IN" in tts_js


# ── TTS-26: English locale mapping ───────────────────────────────────────────

def test_tts_26_english_locale_mapping(ask_ai_jsx: str, tts_js: str):
    """TTS-26: English (en) → en-US locale for TTS voice selection."""
    assert "en: 'en-US'" in ask_ai_jsx or '"en": "en-US"' in ask_ai_jsx
    assert "en-US" in tts_js


# ── TTS-27: No microphone permission required ─────────────────────────────────

def test_tts_27_no_microphone_permission_for_tts(tts_js: str, speak_button_jsx: str):
    """TTS-27: TTS module uses no getUserMedia, AudioContext, or MediaRecorder."""
    combined = tts_js + speak_button_jsx
    assert "getUserMedia" not in combined
    assert "MediaRecorder" not in combined
    assert "AudioContext" not in combined


# ── TTS-28: No audio files created ───────────────────────────────────────────

def test_tts_28_no_audio_files_created(tts_js: str, speak_button_jsx: str):
    """TTS-28: No Blob, createObjectURL, or writeFile used in TTS module."""
    combined = tts_js + speak_button_jsx
    assert "createObjectURL" not in combined
    assert "Blob" not in combined
    assert "writeFile" not in combined
    assert "MediaRecorder" not in combined


# ── TTS-29: Keyboard accessibility ───────────────────────────────────────────

def test_tts_29_keyboard_accessibility(speak_button_jsx: str):
    """TTS-29: All TTS buttons have type='button', aria-label, and focus ring styles."""
    assert 'type="button"' in speak_button_jsx
    assert "aria-label" in speak_button_jsx
    assert "focus:ring-2" in speak_button_jsx or "focus:outline-none" in speak_button_jsx


# ── TTS-30: Responsive UI ────────────────────────────────────────────────────

def test_tts_30_responsive_ui(speak_button_jsx: str):
    """TTS-30: Button labels use hidden sm:inline to avoid overflow on narrow screens."""
    assert "hidden sm:inline" in speak_button_jsx
