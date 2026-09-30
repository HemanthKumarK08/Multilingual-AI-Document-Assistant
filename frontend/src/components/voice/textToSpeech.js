/**
 * Text-to-Speech Utility Module (Multilingual Quality Repair)
 * Primary: Provider-backed neural TTS (Sarvam Bulbul v3 via /api/v1/tts/synthesize)
 * Fallback: Native browser speechSynthesis for English only (never for Indic).
 *
 * Strict Guarantees:
 * 1. Independent resolution per turn (never reuses previous voice across languages).
 * 2. Provider-backed neural voices for all 4 languages:
 *    - en -> en-IN (ratan)
 *    - hi -> hi-IN (priya)
 *    - te -> te-IN (neha)
 *    - kn -> kn-IN (ishita)
 * 3. Never falls back from Indic (Telugu, Kannada, Hindi) to English voices.
 * 4. Graceful unavailable reporting when voice generation is unavailable.
 */

import apiService from '../../services/api.js';

// ─── Constants & Locales ──────────────────────────────────────────────────────

export const TTS_LOCALE_MAP = {
  en: 'en-US',
  hi: 'hi-IN',
  kn: 'kn-IN',
  te: 'te-IN',
};

export const INDIC_LANG_CODES = ['te', 'kn', 'hi'];

// ─── Global Audio Tracker ─────────────────────────────────────────────────────
let activeGlobalAudio = null;

// ─── Feature Detection ────────────────────────────────────────────────────────

/**
 * Returns true if the browser supports Audio playback or Web Speech Synthesis.
 * @returns {boolean}
 */
export function isTTSSupported() {
  return (
    typeof window !== 'undefined' &&
    ('Audio' in window || 'speechSynthesis' in window) &&
    'SpeechSynthesisUtterance' in window
  );
}

// ─── Localized Voice Unavailable Messages ─────────────────────────────────────

/**
 * Returns a friendly localized message when a voice for the requested Indic
 * language is not available in the user's browser/OS.
 *
 * @param {string} locale - BCP-47 locale (e.g. "te-IN", "kn-IN", "hi-IN")
 * @returns {string} Localized message
 */
export function getTTSUnavailableMessage(locale) {
  const lang = (locale || '').toLowerCase().split('-')[0];
  if (lang === 'te') {
    return 'తెలుగు వాయిస్ ఈ బ్రౌజర్లో అందుబాటులో లేదు. (Telugu voice is not available in this browser)';
  }
  if (lang === 'kn') {
    return 'ಕನ್ನಡ ಧ್ವನಿ ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ. (Kannada voice is not available in this browser)';
  }
  if (lang === 'hi') {
    return 'हिन्दी आवाज़ इस ब्राउज़र में उपलब्ध नहीं है। (Hindi voice is not available in this browser)';
  }
  return 'Voice generation is temporarily unavailable.';
}

// ─── Voice Selection (Browser Diagnostic Fallback) ───────────────────────────

/**
 * Detailed voice resolution inspecting browser voices.
 *
 * Priority:
 *   1. Exact locale match (e.g. "hi-IN", "te-IN", "kn-IN", "en-US")
 *   2. Base-language match (e.g. startsWith "te", "kn", "hi", "en")
 *   3. If Indic and no match: returns null with 'no_compatible_indic_voice'
 *      (NEVER silently uses English)
 *   4. If English and no exact match: returns English fallback voice
 *
 * @param {string} locale - BCP-47 locale (e.g. "en-US", "hi-IN", "kn-IN", "te-IN")
 * @returns {{ voice: SpeechSynthesisVoice | null, reason: string, matchingCount: number }}
 */
export function resolveVoiceDetailed(locale) {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    return { voice: null, reason: 'speech_synthesis_unsupported', matchingCount: 0 };
  }

  const voices = window.speechSynthesis.getVoices() || [];
  const lowerLocale = (locale || 'en-US').toLowerCase().replace('_', '-');
  const langPrefix = lowerLocale.split('-')[0];
  const isIndic = INDIC_LANG_CODES.includes(langPrefix);

  const matchingVoices = voices.filter((v) => {
    const vLang = (v.lang || '').toLowerCase().replace('_', '-');
    return vLang === lowerLocale || vLang.startsWith(langPrefix);
  });

  // 1. Exact locale match
  const exact = voices.find((v) => (v.lang || '').toLowerCase().replace('_', '-') === lowerLocale);
  if (exact) {
    return { voice: exact, reason: 'exact_locale_match', matchingCount: matchingVoices.length };
  }

  // 2. Base language prefix match
  const prefixMatch = voices.find((v) => (v.lang || '').toLowerCase().replace('_', '-').startsWith(langPrefix));
  if (prefixMatch) {
    return { voice: prefixMatch, reason: 'base_language_match', matchingCount: matchingVoices.length };
  }

  // 3. For Indic languages, NEVER fall back to English!
  if (isIndic) {
    return { voice: null, reason: 'no_compatible_indic_voice', matchingCount: 0 };
  }

  // 4. For English: pick first English voice or first available
  const enVoice = voices.find((v) => (v.lang || '').toLowerCase().startsWith('en')) || voices[0] || null;
  return {
    voice: enVoice,
    reason: enVoice ? 'english_fallback' : 'no_voice_available',
    matchingCount: matchingVoices.length,
  };
}

/**
 * Returns matching voice or null.
 * @param {string} locale
 * @returns {SpeechSynthesisVoice | null}
 */
export function resolveVoice(locale) {
  return resolveVoiceDetailed(locale).voice;
}

/**
 * Returns true if a compatible native voice exists for the given locale in the browser.
 * @param {string} locale
 * @returns {boolean}
 */
export function isVoiceAvailableForLocale(locale) {
  return resolveVoiceDetailed(locale).voice !== null;
}

/**
 * Returns full snapshot of all available browser voices for diagnostics.
 * @returns {Array<{ name: string, lang: string, localService: boolean, default: boolean }>}
 */
export function getBrowserVoiceInventory() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return [];
  const voices = window.speechSynthesis.getVoices() || [];
  return voices.map((v) => ({
    name: v.name,
    lang: v.lang,
    localService: v.localService,
    default: v.default,
  }));
}

// ─── Markdown → Plain Text Conversion ────────────────────────────────────────

/**
 * Strips Markdown markup and citation noise to produce clean spoken text.
 * Does NOT translate. Does NOT invoke a second LLM.
 *
 * @param {string} markdown - Raw answer string (may include Markdown)
 * @returns {string} Clean text suitable for speech synthesis
 */
export function markdownToSpeechText(markdown) {
  if (!markdown || typeof markdown !== 'string') return '';

  let text = markdown;

  // 1. Strip Markdown headings (# Header, ## Subheader)
  text = text.replace(/#{1,6}\s+/g, '');

  // 2. Strip bold and italic formatting (**bold**, *italic*, __bold__, _italic_)
  text = text.replace(/\*\*(.*?)\*\*/g, '$1');
  text = text.replace(/\*(.*?)\*/g, '$1');
  text = text.replace(/__(.*?)__/g, '$1');
  text = text.replace(/_(.*?)_/g, '$1');

  // 3. Strip inline code (`code`) and code blocks (```code```)
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/`([^`]+)`/g, '$1');

  // 4. Strip citation tags: [Source N], [శీర్షిక N], [మూలం N], [स्रोत N], [ಮೂಲ N], [Doc-*]
  text = text.replace(/\[(?:Source|శీర్షిక|మూలం|स्रोत|ಮೂಲ)\s*\d+\]/gi, '');
  text = text.replace(/\[(?:Doc-[A-Z0-9_\-]+)\]/gi, '');
  text = text.replace(/\[\d+\]/g, '');

  // 5. Convert Markdown links [text](url) -> "text"
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // 6. Convert bullet lists and numbered lists into readable pause boundaries
  text = text.replace(/^\s*[-*+]\s+/gm, '');
  text = text.replace(/^\s*\d+\.\s+/gm, '');

  // 7. Strip blockquote markers (> quote)
  text = text.replace(/^\s*>\s+/gm, '');

  // 8. Normalize excessive whitespace and blank lines
  text = text.replace(/\r\n|\r/g, '\n');
  text = text.replace(/\n{2,}/g, '. ');
  text = text.replace(/\n/g, ' ');
  text = text.replace(/\s{2,}/g, ' ').trim();

  // Ensure text doesn't end with orphaned punctuation artifacts
  text = text.replace(/\.\s*\.\s*\./g, '.');

  return text;
}

// ─── TTS Controller Factory ───────────────────────────────────────────────────

/**
 * Creates a TTS controller instance for a single answer.
 * Integrates Sarvam Bulbul v3 backend neural speech synthesis with graceful fallback.
 *
 * @param {Object}   options
 * @param {string}   options.text           - Raw answer text (Markdown OK)
 * @param {string}   [options.locale="en-US"]- BCP-47 locale (e.g. "en-US", "hi-IN", "te-IN")
 * @param {number}   [options.rate=1.0]     - Speech rate
 * @param {number}   [options.pitch=1.0]    - Speech pitch
 * @param {number}   [options.volume=1.0]   - Speech volume
 * @param {Function} [options.onStart]      - Called when speech begins
 * @param {Function} [options.onEnd]        - Called when speech ends naturally
 * @param {Function} [options.onPause]      - Called when speech is paused
 * @param {Function} [options.onResume]     - Called when speech resumes
 * @param {Function} [options.onError]      - Called with error message string
 * @returns {{ speak, stop, pause, resume, isSupported: boolean }}
 */
export function createTTSController({
  text,
  locale = 'en-US',
  rate = 1.0,
  pitch = 1.0,
  volume = 1.0,
  onStart = () => {},
  onEnd = () => {},
  onPause = () => {},
  onResume = () => {},
  onError = () => {},
} = {}) {
  if (!isTTSSupported()) {
    return {
      speak: () => onError('Text-to-Speech is not supported in this browser.'),
      stop: () => {},
      pause: () => {},
      resume: () => {},
      isSupported: false,
    };
  }

  const spokenText = markdownToSpeechText(text || '');
  const synth = typeof window !== 'undefined' && window.speechSynthesis ? window.speechSynthesis : null;
  let activeAudio = null;
  let utterance = null;

  return {
    isSupported: true,

    speak() {
      // Cancel any currently active speech before starting
      stopAllSpeech();

      const langPrefix = (locale || '').toLowerCase().split('-')[0];
      const isIndic = INDIC_LANG_CODES.includes(langPrefix);
      const voice = resolveVoice(locale);
      const res = resolveVoiceDetailed(locale);

      console.log(
        `[TTS] target_language=${langPrefix} ` +
        `requested_locale=${locale} ` +
        `primary_provider=sarvam ` +
        `available_matching_voices=${res.matchingCount} ` +
        `selected_voice=${res.voice ? res.voice.name : 'NONE'}`
      );

      // 1. Primary Neural TTS via Sarvam Bulbul v3 backend endpoint
      apiService.synthesizeSpeech(spokenText, langPrefix)
        .then((data) => {
          if (data && data.audio) {
            console.log(`[TTS] Playing Sarvam audio (${data.voice}) for [${langPrefix}]`);
            const audioObj = new Audio('data:audio/wav;base64,' + data.audio);
            activeAudio = audioObj;
            activeGlobalAudio = audioObj;

            audioObj.onplay = () => onStart();
            audioObj.onended = () => {
              activeAudio = null;
              if (activeGlobalAudio === audioObj) activeGlobalAudio = null;
              onEnd();
            };
            audioObj.onerror = (e) => {
              console.warn('[TTS] Audio playback error:', e);
              activeAudio = null;
              if (activeGlobalAudio === audioObj) activeGlobalAudio = null;
              onError('Audio playback error');
            };

            audioObj.play().catch((playErr) => {
              console.warn('[TTS] audio.play() error:', playErr);
              activeAudio = null;
              if (activeGlobalAudio === audioObj) activeGlobalAudio = null;
              onError('Audio playback was prevented by the browser.');
            });
            return;
          }
          throw new Error('Empty audio');
        })
        .catch((err) => {
          console.warn(`[TTS] Sarvam TTS unavailable: ${err.message}`);

          // PART N: If Indic, NEVER use English browser voice!
          if (isIndic) {
            onError('Voice generation is temporarily unavailable.');
            return;
          }

          // English optional fallback: browser speechSynthesis
          if (!synth) {
            onError('Voice generation is temporarily unavailable.');
            return;
          }

          if (synth.speaking || synth.pending) {
            synth.cancel();
          }

          const u = new SpeechSynthesisUtterance(spokenText);
          u.rate = rate;
          u.pitch = pitch;
          u.volume = volume;
          u.lang = locale;

          if (voice) u.voice = voice;

          u.onstart = () => onStart();
          u.onend = () => onEnd();
          u.onpause = () => onPause();
          u.onresume = () => onResume();
          u.onerror = (e) => {
            if (e.error !== 'interrupted' && e.error !== 'canceled') {
              onError(`Speech error: ${e.error || 'unknown'}`);
            }
          };
          utterance = u;

          try {
            synth.speak(utterance);
          } catch (speakErr) {
            onError('Speech synthesis failed.');
          }
        });
    },

    stop() {
      if (activeAudio) {
        try {
          activeAudio.pause();
          activeAudio.currentTime = 0;
        } catch (_) {}
        activeAudio = null;
      }
      if (synth) {
        try {
          synth.cancel();
        } catch (_) {}
      }
      utterance = null;
    },

    pause() {
      if (activeAudio && !activeAudio.paused) {
        try {
          activeAudio.pause();
        } catch (_) {}
      }
      if (synth) {
        try {
          if (synth.speaking && !synth.paused) {
            synth.pause();
          }
        } catch (_) {}
      }
    },

    resume() {
      if (activeAudio && activeAudio.paused) {
        try {
          activeAudio.play().catch(() => {});
        } catch (_) {}
      }
      if (synth) {
        try {
          if (synth.paused) {
            synth.resume();
          }
        } catch (_) {}
      }
    },
  };
}

/**
 * Stops all currently active speech synthesis and HTML5 audio playback immediately.
 * Use this as a global cleanup (New Chat, navigation, mode changes).
 */
export function stopAllSpeech() {
  if (activeGlobalAudio) {
    try {
      activeGlobalAudio.pause();
      activeGlobalAudio.currentTime = 0;
    } catch (_) {}
    activeGlobalAudio = null;
  }
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (_) {}
  }
}
