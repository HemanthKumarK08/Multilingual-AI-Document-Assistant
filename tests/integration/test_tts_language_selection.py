"""
Integration Tests for TTS Language & Voice Selection
Covers requirements 12-19 from PART 21:
  - Telugu, Hindi, Kannada, English locale resolution
  - Wrong-language TTS voice rejected (no English fallback for Indic text)
  - Exact locale preferred over base language
  - Base-language locale accepted when exact dialect absent
  - Previous voice not reused across turns
"""
import json
import subprocess
import pytest
from app.services.language.resolution import TTS_LOCALE_MAP


class TestTTSLocaleResolution:
    """Tests 12-15: Authoritative TTS Locale Mapping."""

    def test_telugu_locale_resolution(self):
        """12. Telugu maps to te-IN."""
        assert TTS_LOCALE_MAP["te"] == "te-IN"

    def test_hindi_locale_resolution(self):
        """13. Hindi maps to hi-IN."""
        assert TTS_LOCALE_MAP["hi"] == "hi-IN"

    def test_kannada_locale_resolution(self):
        """14. Kannada maps to kn-IN."""
        assert TTS_LOCALE_MAP["kn"] == "kn-IN"

    def test_english_locale_resolution(self):
        """15. English maps to en-US."""
        assert TTS_LOCALE_MAP["en"] == "en-US"


class TestTTSVoiceSelectionJS:
    """Tests 16-19: Frontend voice resolution algorithm tested via Node.js execution."""

    @staticmethod
    def _run_tts_js(script_body: str):
        node_script = f"""
        import {{
          resolveVoiceDetailed,
          isVoiceAvailableForLocale,
          getTTSUnavailableMessage,
          TTS_LOCALE_MAP
        }} from './frontend/src/components/voice/textToSpeech.js';

        // Mock window.speechSynthesis
        const mockVoices = [
          {{ name: 'Google US English', lang: 'en-US', default: true }},
          {{ name: 'Google UK English Female', lang: 'en-GB', default: false }},
          {{ name: 'Google हिन्दी', lang: 'hi-IN', default: false }},
          {{ name: 'Rishi (Indian English)', lang: 'en-IN', default: false }}
        ];

        global.window = {{
          speechSynthesis: {{
            getVoices: () => mockVoices,
            speak: () => {{}},
            cancel: () => {{}},
          }},
          SpeechSynthesisUtterance: class {{
            constructor(text) {{ this.text = text; }}
          }}
        }};

        {script_body}
        """
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", node_script],
            capture_output=True,
            text=True,
            cwd="/Users/hemanthkumark/College/BIT/Ml",
        )
        assert proc.returncode == 0, f"Node script error: {proc.stderr}"
        return json.loads(proc.stdout.strip())

    def test_wrong_language_voice_rejected_for_indic(self):
        """16. When only English voices exist, Telugu & Kannada reject English voice."""
        res = self._run_tts_js("""
        const teRes = resolveVoiceDetailed('te-IN');
        const knRes = resolveVoiceDetailed('kn-IN');
        const teAvail = isVoiceAvailableForLocale('te-IN');
        const knAvail = isVoiceAvailableForLocale('kn-IN');
        console.log(JSON.stringify({
          teVoice: teRes.voice,
          teReason: teRes.reason,
          teAvail,
          knVoice: knRes.voice,
          knReason: knRes.reason,
          knAvail,
        }));
        """)
        # Telugu and Kannada MUST NOT pick Google US English or en-IN
        assert res["teVoice"] is None
        assert res["teReason"] == "no_compatible_indic_voice"
        assert res["teAvail"] is False
        assert res["knVoice"] is None
        assert res["knReason"] == "no_compatible_indic_voice"
        assert res["knAvail"] is False

    def test_exact_locale_preferred(self):
        """17. Exact locale match preferred over generic fallback."""
        res = self._run_tts_js("""
        const hiRes = resolveVoiceDetailed('hi-IN');
        console.log(JSON.stringify({
          name: hiRes.voice.name,
          lang: hiRes.voice.lang,
          reason: hiRes.reason
        }));
        """)
        assert res["name"] == "Google हिन्दी"
        assert res["lang"] == "hi-IN"
        assert res["reason"] == "exact_locale_match"

    def test_base_language_accepted_when_dialect_matches(self):
        """18. Base-language prefix matches when regional dialect suffix varies."""
        res = self._run_tts_js("""
        // Add a generic 'te' voice with non-standard locale 'te-Telu'
        global.window.speechSynthesis.getVoices = () => [
          { name: 'Google US English', lang: 'en-US' },
          { name: 'Telugu Base Voice', lang: 'te' }
        ];
        const teRes = resolveVoiceDetailed('te-IN');
        console.log(JSON.stringify({
          name: teRes.voice.name,
          lang: teRes.voice.lang,
          reason: teRes.reason
        }));
        """)
        assert res["name"] == "Telugu Base Voice"
        assert res["reason"] == "base_language_match"

    def test_previous_voice_not_reused_across_turns(self):
        """19. Each turn independently resolves its voice without caching."""
        res = self._run_tts_js("""
        // Turn 1: English
        const turn1 = resolveVoiceDetailed('en-US');
        // Turn 2: Hindi
        const turn2 = resolveVoiceDetailed('hi-IN');
        // Turn 3: Telugu (no native voice)
        const turn3 = resolveVoiceDetailed('te-IN');
        // Turn 4: English
        const turn4 = resolveVoiceDetailed('en-US');

        console.log(JSON.stringify({
          turn1Voice: turn1.voice.name,
          turn2Voice: turn2.voice.name,
          turn3Voice: turn3.voice,
          turn4Voice: turn4.voice.name,
        }));
        """)
        assert res["turn1Voice"] == "Google US English"
        assert res["turn2Voice"] == "Google हिन्दी"
        assert res["turn3Voice"] is None  # Does not carry over Hindi or English!
        assert res["turn4Voice"] == "Google US English"
