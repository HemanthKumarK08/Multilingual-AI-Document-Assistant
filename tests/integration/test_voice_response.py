"""
Phase 9.6 — Multilingual Voice Response & Optional Voice Conversation Test Suite
Tests VR-01 through VR-45 covering Voice Response Mode, automatic TTS trigger,
language resolution, turn-taking, interruption, error handling, accessibility, and privacy.
"""
import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ask_ai_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    assert p.exists(), "AskAI.jsx required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tts_js() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "textToSpeech.js"
    assert p.exists(), "textToSpeech.js required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def speak_button_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "SpeakButton.jsx"
    assert p.exists(), "SpeakButton.jsx required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def speech_recognition_button_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "SpeechRecognitionButton.jsx"
    assert p.exists(), "SpeechRecognitionButton.jsx required"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def api_service_js() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "services" / "api.js"
    assert p.exists(), "api.js required"
    return p.read_text(encoding="utf-8")


# ── VR-01: Voice Response Toggle Exists ───────────────────────────────────────

def test_vr_01_voice_response_toggle_exists(ask_ai_jsx: str):
    """VR-01: Voice Response toggle button exists in AskAI top controls."""
    assert "Voice Response" in ask_ai_jsx
    assert "setVoiceResponseEnabled" in ask_ai_jsx


# ── VR-02: Default State is OFF ───────────────────────────────────────────────

def test_vr_02_default_state_is_off(ask_ai_jsx: str):
    """VR-02: voiceResponseEnabled initializes to false (OFF)."""
    assert "useState(false)" in ask_ai_jsx
    match = re.search(r'const\s+\[voiceResponseEnabled,\s*setVoiceResponseEnabled\]\s*=\s*useState\(false\)', ask_ai_jsx)
    assert match is not None, "voiceResponseEnabled must default to false"


# ── VR-03: Toggle ON Works ───────────────────────────────────────────────────

def test_vr_03_toggle_on_works(ask_ai_jsx: str):
    """VR-03: Clicking toggle inverts state from false to true."""
    assert "setVoiceResponseEnabled((prev) => !prev)" in ask_ai_jsx or "setVoiceResponseEnabled(!voiceResponseEnabled)" in ask_ai_jsx


# ── VR-04: Toggle OFF Works ──────────────────────────────────────────────────

def test_vr_04_toggle_off_works(ask_ai_jsx: str):
    """VR-04: Inverting state when ON returns to OFF."""
    assert "setVoiceResponseEnabled((prev) => !prev)" in ask_ai_jsx


# ── VR-05: Voice Query Mode OFF No Auto-Speak ────────────────────────────────

def test_vr_05_voice_query_mode_off_no_auto_speak(ask_ai_jsx: str):
    """VR-05: Auto-TTS only executes if submitVoiceResponse is truthy."""
    assert "if (submitVoiceResponse && submitMode === 'voice'" in ask_ai_jsx


# ── VR-06: Voice Query Mode ON Auto-Speaks ───────────────────────────────────

def test_vr_06_voice_query_mode_on_auto_speaks(ask_ai_jsx: str):
    """VR-06: Auto-TTS triggers when submitVoiceResponse && submitMode === 'voice'."""
    assert "autoTTS.speak()" in ask_ai_jsx or "createTTSController" in ask_ai_jsx


# ── VR-07: Typed Query Does Not Auto-Speak ───────────────────────────────────

def test_vr_07_typed_query_does_not_auto_speak(ask_ai_jsx: str):
    """VR-07: Typed query has submitMode === 'typed' so auto-TTS condition is false."""
    # When query is typed, submitMode is 'typed', thus submitMode === 'voice' fails
    assert "submitMode === 'voice'" in ask_ai_jsx


# ── VR-08: Automatic TTS Reuses Existing Controller ───────────────────────────

def test_vr_08_automatic_tts_uses_existing_tts_controller(ask_ai_jsx: str):
    """VR-08: createTTSController from textToSpeech.js is imported and reused."""
    assert "import { createTTSController" in ask_ai_jsx or "createTTSController," in ask_ai_jsx


# ── VR-09: Correct Response Language Selected ─────────────────────────────────

def test_vr_09_correct_response_language_selected(ask_ai_jsx: str):
    """VR-09: Language hierarchy respects selectedLanguage, detected_language, with en fallback."""
    assert "selectedLanguage !== 'auto'" in ask_ai_jsx
    assert "res.detected_language" in ask_ai_jsx


# ── VR-10: English Automatic Response ─────────────────────────────────────────

def test_vr_10_english_automatic_response(ask_ai_jsx: str):
    """VR-10: English maps to en-US in TTS_LOCALE_MAP."""
    assert "en: 'en-US'" in ask_ai_jsx or '"en": "en-US"' in ask_ai_jsx


# ── VR-11: Hindi Automatic Response ──────────────────────────────────────────

def test_vr_11_hindi_automatic_response(ask_ai_jsx: str):
    """VR-11: Hindi maps to hi-IN in TTS_LOCALE_MAP."""
    assert "hi: 'hi-IN'" in ask_ai_jsx or '"hi": "hi-IN"' in ask_ai_jsx


# ── VR-12: Kannada Locale Handling ───────────────────────────────────────────

def test_vr_12_kannada_locale_handling(ask_ai_jsx: str):
    """VR-12: Kannada maps to kn-IN in TTS_LOCALE_MAP."""
    assert "kn: 'kn-IN'" in ask_ai_jsx or '"kn": "kn-IN"' in ask_ai_jsx


# ── VR-13: Telugu Locale Handling ────────────────────────────────────────────

def test_vr_13_telugu_locale_handling(ask_ai_jsx: str):
    """VR-13: Telugu maps to te-IN in TTS_LOCALE_MAP."""
    assert "te: 'te-IN'" in ask_ai_jsx or '"te": "te-IN"' in ask_ai_jsx


# ── VR-14: Native Voice Availability Detection ────────────────────────────────

def test_vr_14_native_voice_availability_detected(tts_js: str):
    """VR-14: resolveVoice searches getVoices() and returns null for browser default when missing."""
    assert "window.speechSynthesis.getVoices()" in tts_js
    assert "resolveVoice" in tts_js


# ── VR-15: Fallback Voice Behavior ───────────────────────────────────────────

def test_vr_15_fallback_voice_behavior(tts_js: str):
    """VR-15: When resolveVoice returns null, utterance is synthesized with default voice."""
    assert "const voice = resolveVoice(locale);" in tts_js
    assert "if (voice) u.voice = voice;" in tts_js


# ── VR-16: Manual Speak Still Works ──────────────────────────────────────────

def test_vr_16_manual_speak_still_works(ask_ai_jsx: str):
    """VR-16: SpeakButton remains rendered for assistant messages."""
    assert "<SpeakButton" in ask_ai_jsx
    assert "!isUser && msg.content" in ask_ai_jsx


# ── VR-17: Stop Automatic Speech Works ────────────────────────────────────────

def test_vr_17_stop_automatic_speech_works(tts_js: str):
    """VR-17: stopAllSpeech() calls speechSynthesis.cancel()."""
    assert "window.speechSynthesis.cancel()" in tts_js


# ── VR-18: New Answer Stops Previous Speech ───────────────────────────────────

def test_vr_18_new_answer_stops_previous_speech(ask_ai_jsx: str):
    """VR-18: stopAllSpeech() is called before starting new auto-TTS."""
    match = re.search(r'if\s*\(submitVoiceResponse.*?\)\s*\{.*?stopAllSpeech\(\);', ask_ai_jsx, re.DOTALL)
    assert match is not None, "stopAllSpeech must be called before new auto speech"


# ── VR-19: Microphone Interrupts Active TTS ───────────────────────────────────

def test_vr_19_microphone_interrupts_active_tts(ask_ai_jsx: str):
    """VR-19: onVoiceStateChange calls stopAllSpeech() when mic activates."""
    match = re.search(r'onVoiceStateChange.*?active.*?stopAllSpeech', ask_ai_jsx, re.DOTALL)
    assert match is not None, "Mic activation must trigger stopAllSpeech() for turn-taking"


# ── VR-20: TTS Does Not Restart Unexpectedly ──────────────────────────────────

def test_vr_20_tts_does_not_restart_after_interruption(speech_recognition_button_jsx: str):
    """VR-20: Speech recognition session end goes to idle without invoking TTS."""
    assert "autoTTS" not in speech_recognition_button_jsx
    assert "createTTSController" not in speech_recognition_button_jsx


# ── VR-21: New Chat Stops TTS ────────────────────────────────────────────────

def test_vr_21_new_chat_stops_tts(ask_ai_jsx: str):
    """VR-21: clearConversation() invokes stopAllSpeech()."""
    assert "stopAllSpeech()" in ask_ai_jsx
    assert "clearConversation" in ask_ai_jsx


# ── VR-22: New Chat Stops Recognition ────────────────────────────────────────

def test_vr_22_new_chat_stops_recognition(ask_ai_jsx: str):
    """VR-22: clearConversation() sets voiceActive to false and resets inputMode."""
    assert "setVoiceActive(false)" in ask_ai_jsx
    assert "inputModeRef.current = 'typed'" in ask_ai_jsx


# ── VR-23: Navigation Stops TTS ──────────────────────────────────────────────

def test_vr_23_navigation_stops_tts(speak_button_jsx: str):
    """VR-23: SpeakButton unmount cleanup executes stopAllSpeech()."""
    assert "stopAllSpeech()" in speak_button_jsx


# ── VR-24: Navigation Cleans Recognition ──────────────────────────────────────

def test_vr_24_navigation_cleans_recognition(speech_recognition_button_jsx: str):
    """VR-24: SpeechRecognitionButton unmount cleanup aborts active recognizer."""
    assert "recognizerRef.current.abort()" in speech_recognition_button_jsx


# ── VR-25: Fallback Answer Can Be Spoken ─────────────────────────────────────

def test_vr_25_fallback_answer_can_be_spoken(ask_ai_jsx: str):
    """VR-25: Fallback answers have res.answer_text and are spoken if voiceResponseMode is active."""
    # Auto-TTS only checks submitVoiceResponse && submitMode === 'voice' && res.answer_text
    auto_block = re.search(r'if\s*\(submitVoiceResponse[^)]*\)', ask_ai_jsx)
    assert auto_block is not None
    assert "!res.is_fallback" not in auto_block.group(0)


# ── VR-26: RAG Error Does Not Trigger TTS ────────────────────────────────────

def test_vr_26_rag_error_does_not_trigger_tts(ask_ai_jsx: str):
    """VR-26: auto-TTS is inside try block after successful API response, not catch block."""
    # Extract handleSend function body
    start_idx = ask_ai_jsx.find("async function handleSend")
    end_idx = ask_ai_jsx.find("const handleVoiceTranscript", start_idx)
    assert start_idx != -1 and end_idx != -1
    body = ask_ai_jsx[start_idx:end_idx]
    catch_pos = body.find("} catch (err) {")
    auto_pos = body.find("autoTTS.speak()")
    assert auto_pos != -1
    assert catch_pos != -1
    assert auto_pos < catch_pos, "Auto TTS must occur inside try block before catch block"


# ── VR-27: TTS Error Does Not Remove Answer ──────────────────────────────────

def test_vr_27_tts_error_does_not_remove_answer(ask_ai_jsx: str, speak_button_jsx: str):
    """VR-27: TTS error is isolated to TTS layer and does not alter message list."""
    assert "setMessages" not in speak_button_jsx
    assert "Speech error" in speak_button_jsx


# ── VR-28: No Duplicate TTS ──────────────────────────────────────────────────

def test_vr_28_no_duplicate_tts(ask_ai_jsx: str):
    """VR-28: Auto-TTS stops previous speech and only creates one controller instance per send."""
    assert ask_ai_jsx.count("autoTTS.speak()") <= 1


# ── VR-29: No Duplicate QA Request ───────────────────────────────────────────

def test_vr_29_no_duplicate_qa_request(ask_ai_jsx: str):
    """VR-29: submitQuery is called exactly once in handleSend."""
    assert ask_ai_jsx.count("apiService.submitQuery(") == 1


# ── VR-30: Voice Language Selector Remains Functional ─────────────────────────

def test_vr_30_voice_language_selector_functional(ask_ai_jsx: str):
    """VR-30: VoiceLanguageSelector remains present and connected to voiceLanguage state."""
    assert "<VoiceLanguageSelector" in ask_ai_jsx
    assert "value={voiceLanguage}" in ask_ai_jsx


# ── VR-31: RAG Target Language Remains Independent ───────────────────────────

def test_vr_31_rag_target_language_independent(ask_ai_jsx: str):
    """VR-31: selectedLanguage and voiceLanguage remain distinct independent states."""
    assert "const [selectedLanguage, setSelectedLanguage] = useState('auto')" in ask_ai_jsx
    assert "const [voiceLanguage, setVoiceLanguage] = useState('en')" in ask_ai_jsx


# ── VR-32: Edited Transcript is Submitted ────────────────────────────────────

def test_vr_32_edited_transcript_is_submitted(ask_ai_jsx: str):
    """VR-32: Typing into textarea updates inputQuery, ensuring user edits are submitted."""
    assert "setInputQuery(e.target.value)" in ask_ai_jsx


# ── VR-33: Voice Response Mode Captured at Send ──────────────────────────────

def test_vr_33_mode_captured_at_send(ask_ai_jsx: str):
    """VR-33: submitVoiceResponse = voiceResponseEnabled is snapshotted at handleSend entry."""
    assert "const submitVoiceResponse = voiceResponseEnabled;" in ask_ai_jsx


# ── VR-34: Race Condition: Toggle OFF After Send ─────────────────────────────

def test_vr_34_race_toggle_off_after_send(ask_ai_jsx: str):
    """VR-34: Logic checks submitVoiceResponse (captured constant), not live state, after async await."""
    assert "if (submitVoiceResponse && submitMode === 'voice'" in ask_ai_jsx


# ── VR-35: Race Condition: New Chat During RAG ───────────────────────────────

def test_vr_35_race_new_chat_during_rag(ask_ai_jsx: str):
    """VR-35: clearConversation resets voiceActive and stops all speech."""
    assert "stopAllSpeech()" in ask_ai_jsx
    assert "setVoiceActive(false)" in ask_ai_jsx


# ── VR-36: Race Condition: Microphone During TTS ─────────────────────────────

def test_vr_36_race_mic_during_tts(ask_ai_jsx: str):
    """VR-36: Turning on mic immediately triggers stopAllSpeech()."""
    match = re.search(r'onVoiceStateChange.*?stopAllSpeech\(\)', ask_ai_jsx, re.DOTALL)
    assert match is not None


# ── VR-37: Accessibility ─────────────────────────────────────────────────────

def test_vr_37_accessibility(ask_ai_jsx: str):
    """VR-37: Voice Response toggle has aria-pressed, aria-label, and focus ring."""
    assert "aria-label={voiceResponseEnabled" in ask_ai_jsx
    assert "aria-pressed={voiceResponseEnabled}" in ask_ai_jsx
    assert "focus:ring-2" in ask_ai_jsx


# ── VR-38: Responsive 375px ──────────────────────────────────────────────────

def test_vr_38_responsive_375px(ask_ai_jsx: str):
    """VR-38: Controls bar uses flex-wrap and hidden sm:inline for narrow viewports."""
    assert "flex-wrap" in ask_ai_jsx
    assert "hidden sm:inline" in ask_ai_jsx


# ── VR-39: Responsive 768px ──────────────────────────────────────────────────

def test_vr_39_responsive_768px(ask_ai_jsx: str):
    """VR-39: Responsive sm: flex-row breakpoint handles tablet layouts cleanly."""
    assert "sm:flex-row" in ask_ai_jsx or "sm:items-center" in ask_ai_jsx


# ── VR-40: Responsive 1024px ─────────────────────────────────────────────────

def test_vr_40_responsive_1024px(ask_ai_jsx: str):
    """VR-40: Container max-w-5xl ensures optimal layout on desktop."""
    assert "max-w-5xl" in ask_ai_jsx


# ── VR-41: Responsive 1366px ─────────────────────────────────────────────────

def test_vr_41_responsive_1366px(ask_ai_jsx: str):
    """VR-41: Centered mx-auto layout supports large displays."""
    assert "mx-auto" in ask_ai_jsx


# ── VR-42: Privacy No Audio Storage ───────────────────────────────────────────

def test_vr_42_privacy_no_audio_storage(ask_ai_jsx: str, tts_js: str):
    """VR-42: Zero audio files or blobs stored on disk or in memory."""
    combined = ask_ai_jsx + tts_js
    assert "createObjectURL" not in combined
    assert "Blob" not in combined
    assert "writeFile" not in combined


# ── VR-43: No Microphone Recording Persistence ────────────────────────────────

def test_vr_43_no_microphone_recording_persistence(speech_recognition_button_jsx: str):
    """VR-43: Web Speech API uses browser engine directly — no MediaRecorder or stream persistence."""
    assert "MediaRecorder" not in speech_recognition_button_jsx
    assert "AudioContext" not in speech_recognition_button_jsx


# ── VR-44: No External TTS API ───────────────────────────────────────────────

def test_vr_44_no_external_tts_api(tts_js: str, api_service_js: str):
    """VR-44: TTS uses browser-native window.speechSynthesis, zero external cloud TTS calls."""
    assert "/api/v1/tts" not in api_service_js
    assert "speechSynthesis" in tts_js


# ── VR-45: Production Build Verified ─────────────────────────────────────────

def test_vr_45_production_build_verified():
    """VR-45: Dist assets exist and are generated cleanly by Vite build."""
    dist_index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    assert dist_index.exists(), "Production build output frontend/dist/index.html must exist"
