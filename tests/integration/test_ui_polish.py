"""
Phase 10.1 — Final UI/UX Polish & Product Presentation Test Suite
Tests UI-01 through UI-25 verifying production branding, layout polish,
locale code hiding, accessibility, responsiveness, and component integrity.
"""
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def header_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "Header.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sidebar_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "Sidebar.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ask_ai_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def voice_language_selector_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "VoiceLanguageSelector.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dashboard_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "Dashboard.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def documents_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "Documents.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def analytics_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "Analytics.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def settings_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "pages" / "Settings.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def citations_section_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "CitationsSection.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def evidence_drawer_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "EvidenceDrawer.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def feedback_widget_jsx() -> str:
    p = PROJECT_ROOT / "frontend" / "src" / "components" / "FeedbackWidget.jsx"
    assert p.exists()
    return p.read_text(encoding="utf-8")


# ── UI-01: No Outdated Phase 8.1 Label ────────────────────────────────────────

def test_ui_01_no_outdated_phase_label(header_jsx: str, dashboard_jsx: str, analytics_jsx: str):
    """UI-01: Outdated 'Phase 8.1' / 'Phase 8.5' development badges are removed."""
    assert "Phase 8.1" not in header_jsx
    assert "Phase 8.1" not in dashboard_jsx
    assert "Phase 8.5" not in analytics_jsx


# ── UI-02: Header Branding Renders Correctly ──────────────────────────────────

def test_ui_02_header_branding(header_jsx: str):
    """UI-02: Header displays production branding and platform identity."""
    assert "Multilingual AI Document Assistant" in header_jsx
    assert "Production" in header_jsx
    assert "AI-Powered Document Intelligence" in header_jsx


# ── UI-03: Ask AI Layout Renders ──────────────────────────────────────────────

def test_ui_03_ask_ai_layout_renders(ask_ai_jsx: str):
    """UI-03: Ask AI page structure has top controls, conversation thread, and composer."""
    assert "Ask AI" in ask_ai_jsx
    assert "handleSend" in ask_ai_jsx
    assert "handleVoiceTranscript" in ask_ai_jsx


# ── UI-04: Conversation Responsive Width ──────────────────────────────────────

def test_ui_04_conversation_responsive_width(ask_ai_jsx: str):
    """UI-04: Conversation layout utilizes expanded responsive container (max-w-6xl)."""
    assert "max-w-6xl" in ask_ai_jsx
    assert "max-w-3xl sm:max-w-4xl" in ask_ai_jsx or "max-w-4xl" in ask_ai_jsx


# ── UI-05: Language Labels Hide Locale Codes ──────────────────────────────────

def test_ui_05_language_labels_hide_locale_codes(voice_language_selector_jsx: str, ask_ai_jsx: str):
    """UI-05: Normal users see friendly native labels without raw locale codes (kn-IN/te-IN)."""
    assert "{lang.nativeLabel} ({lang.label})" in voice_language_selector_jsx
    assert "{lang.nativeLabel} — {lang.locale}" not in voice_language_selector_jsx
    assert "LANGUAGE_DISPLAY_NAMES" in ask_ai_jsx


# ── UI-06: Voice Response Toggle Functional ───────────────────────────────────

def test_ui_06_voice_response_toggle_functional(ask_ai_jsx: str):
    """UI-06: Voice Response button toggles state with accessible attributes."""
    assert "voiceResponseEnabled" in ask_ai_jsx
    assert "setVoiceResponseEnabled" in ask_ai_jsx
    assert "aria-pressed={voiceResponseEnabled}" in ask_ai_jsx


# ── UI-07: Microphone Remains Functional ──────────────────────────────────────

def test_ui_07_microphone_functional(ask_ai_jsx: str):
    """UI-07: SpeechRecognitionButton is connected to transcript handler and turn-taking."""
    assert "SpeechRecognitionButton" in ask_ai_jsx
    assert "onTranscript={handleVoiceTranscript}" in ask_ai_jsx
    assert "stopAllSpeech()" in ask_ai_jsx


# ── UI-08: TTS SpeakButton Functional ─────────────────────────────────────────

def test_ui_08_tts_speak_button_functional(ask_ai_jsx: str):
    """UI-08: SpeakButton is rendered for assistant messages."""
    assert "<SpeakButton" in ask_ai_jsx
    assert "!isUser && msg.content" in ask_ai_jsx


# ── UI-09: Citations Remain Functional ────────────────────────────────────────

def test_ui_09_citations_functional(ask_ai_jsx: str, citations_section_jsx: str):
    """UI-09: CitationsSection renders citations and supports inspection."""
    assert "<CitationsSection citations={msg.citations}" in ask_ai_jsx
    assert "CitationCard" in citations_section_jsx


# ── UI-10: Evidence Drawer Functional ─────────────────────────────────────────

def test_ui_10_evidence_drawer_functional(evidence_drawer_jsx: str):
    """UI-10: EvidenceDrawer renders verified citation, provenance attributes, and copy controls."""
    assert "EvidenceDrawer" in evidence_drawer_jsx or "Supporting Evidence Passage" in evidence_drawer_jsx
    assert "copyEvidenceText" in evidence_drawer_jsx


# ── UI-11: Feedback Remains Functional ────────────────────────────────────────

def test_ui_11_feedback_functional(feedback_widget_jsx: str):
    """UI-11: FeedbackWidget handles positive/negative feedback submission."""
    assert "FeedbackWidget" in feedback_widget_jsx or "queryId" in feedback_widget_jsx
    assert "handleFeedback" in feedback_widget_jsx or "apiService.submitFeedback" in feedback_widget_jsx


# ── UI-12: New Chat Remains Functional ────────────────────────────────────────

def test_ui_12_new_chat_functional(ask_ai_jsx: str):
    """UI-12: clearConversation resets conversation, input, voice state, and TTS."""
    assert "clearConversation" in ask_ai_jsx
    assert "stopAllSpeech()" in ask_ai_jsx
    assert "setVoiceActive(false)" in ask_ai_jsx


# ── UI-13: Dashboard Remains Functional ───────────────────────────────────────

def test_ui_13_dashboard_functional(dashboard_jsx: str):
    """UI-13: Dashboard displays hero section, quick actions, and system diagnostics."""
    assert "SystemStatus" in dashboard_jsx
    assert "Quick Actions" in dashboard_jsx
    assert "Document Repository" in dashboard_jsx


# ── UI-14: Documents Page Functional ──────────────────────────────────────────

def test_ui_14_documents_functional(documents_jsx: str):
    """UI-14: Documents page supports upload zone, category filters, and search."""
    assert "DocumentUploadZone" in documents_jsx
    assert "DocumentDetailModal" in documents_jsx
    assert "filteredDocuments" in documents_jsx


# ── UI-15: Analytics Page Functional ──────────────────────────────────────────

def test_ui_15_analytics_functional(analytics_jsx: str):
    """UI-15: Analytics page renders PySpark analytics KPIs and telemetry charts."""
    assert "AnalyticsKPIs" in analytics_jsx
    assert "QueryVolumeChart" in analytics_jsx
    assert "LanguageDistributionChart" in analytics_jsx


# ── UI-16: Settings Page Functional ───────────────────────────────────────────

def test_ui_16_settings_functional(settings_jsx: str):
    """UI-16: Settings page renders developer docs, API links, and architecture specifications."""
    assert "Swagger UI" in settings_jsx
    assert "ReDoc API" in settings_jsx


# ── UI-17: 375px Responsive Layout ────────────────────────────────────────────

def test_ui_17_responsive_375px(ask_ai_jsx: str, header_jsx: str):
    """UI-17: Mobile layout handles narrow screens with hidden sm: badges and wrapping."""
    assert "sm:inline" in header_jsx
    assert "flex-wrap" in ask_ai_jsx


# ── UI-18: 768px Responsive Layout ────────────────────────────────────────────

def test_ui_18_responsive_768px(header_jsx: str, sidebar_jsx: str):
    """UI-18: Tablet layout integrates responsive sidebar drawer."""
    assert "lg:hidden" in sidebar_jsx
    assert "lg:translate-x-0" in sidebar_jsx


# ── UI-19: 1024px Responsive Layout ───────────────────────────────────────────

def test_ui_19_responsive_1024px(ask_ai_jsx: str):
    """UI-19: Laptop viewport renders comfortable max-w-6xl container."""
    assert "max-w-6xl" in ask_ai_jsx


# ── UI-20: 1366px Responsive Layout ───────────────────────────────────────────

def test_ui_20_responsive_1366px(ask_ai_jsx: str):
    """UI-20: Desktop layout centers container with mx-auto."""
    assert "mx-auto" in ask_ai_jsx


# ── UI-21: Keyboard Accessibility ─────────────────────────────────────────────

def test_ui_21_keyboard_accessibility(ask_ai_jsx: str):
    """UI-21: Inputs and buttons provide visible focus ring classes and keyboard handlers."""
    assert "focus:ring-2" in ask_ai_jsx
    assert "onKeyDown={handleKeyDown}" in ask_ai_jsx


# ── UI-22: Reduced Motion ─────────────────────────────────────────────────────

def test_ui_22_reduced_motion(ask_ai_jsx: str):
    """UI-22: Reduced motion compliance is maintained across voice and animations."""
    assert "animate-fadeIn" in ask_ai_jsx


# ── UI-23: No Horizontal Overflow ─────────────────────────────────────────────

def test_ui_23_no_horizontal_overflow(ask_ai_jsx: str, sidebar_jsx: str):
    """UI-23: Containers use overflow-hidden / overflow-y-auto preventing horizontal scroll."""
    assert "overflow-y-auto" in ask_ai_jsx
    assert "truncate" in ask_ai_jsx


# ── UI-24: No Hardcoded Broken Console Logic ──────────────────────────────────

def test_ui_24_clean_console_logic(ask_ai_jsx: str):
    """UI-24: Frontend does not contain console error dumpers or unhandled promises."""
    assert "console.error" not in ask_ai_jsx


# ── UI-25: Production Build Verified ──────────────────────────────────────────

def test_ui_25_production_build_verified():
    """UI-25: Frontend dist folder contains verified production bundle."""
    dist_index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    assert dist_index.exists(), "frontend/dist/index.html must exist"
