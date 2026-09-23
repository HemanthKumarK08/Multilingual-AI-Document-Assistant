/**
 * Text-to-Speech Utility Module (Phase 9.5)
 * Wraps browser-native window.speechSynthesis / SpeechSynthesisUtterance.
 * No cloud service, no audio storage, no microphone access required.
 */

// ─── Feature Detection ────────────────────────────────────────────────────────

/**
 * Returns true if the browser supports Web Speech Synthesis.
 * @returns {boolean}
 */
export function isTTSSupported() {
  return (
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    'SpeechSynthesisUtterance' in window
  );
}

// ─── Voice Selection ──────────────────────────────────────────────────────────

/**
 * Attempt to pick the best available voice for the given BCP-47 locale.
 * Resolution order:
 *   1. Exact locale match (e.g. "en-US", "hi-IN", "kn-IN", "te-IN")
 *   2. Language-prefix match (e.g. any "hi" voice for hi-IN)
 *   3. null → browser uses its default voice
 *
 * Supported locales: en-US, hi-IN, kn-IN, te-IN (and any BCP-47 locale the browser recognizes)
 *
 * @param {string} locale - BCP-47 locale string (e.g. "en-US", "hi-IN", "kn-IN", "te-IN")
 * @returns {SpeechSynthesisVoice | null}
 */
export function resolveVoice(locale) {
  if (!isTTSSupported()) return null;

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const lowerLocale = locale.toLowerCase();
  const langPrefix = lowerLocale.split('-')[0];

  // 1. Exact locale match
  const exact = voices.find((v) => v.lang.toLowerCase() === lowerLocale);
  if (exact) return exact;

  // 2. Language-prefix match (e.g. "hi" matches "hi-IN", "hi-TTS", etc.)
  const prefixMatch = voices.find((v) => v.lang.toLowerCase().startsWith(langPrefix));
  if (prefixMatch) return prefixMatch;

  // 3. Fall back to browser default
  return null;
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

  // Remove inline citation markers like [Source 1], [1], [Doc-abc]
  text = text.replace(/\[Source\s*\d+\]/gi, '');
  text = text.replace(/\[\d+\]/g, '');
  text = text.replace(/\[Doc-[^\]]+\]/gi, '');

  // Remove Markdown headings (#, ##, ###)
  text = text.replace(/^#{1,6}\s+/gm, '');

  // Remove bold/italic markers (**text**, *text*, __text__, _text_)
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/__([^_]+)__/g, '$1');
  text = text.replace(/_([^_]+)_/g, '$1');

  // Remove code fences and inline code
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/`([^`]+)`/g, '$1');

  // Remove links [text](url) → text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // Convert unordered list bullets (-, *, •) to sentence-friendly breaks
  text = text.replace(/^[\s]*[-*•]\s+/gm, '');

  // Convert ordered list numbers to plain text
  text = text.replace(/^\d+\.\s+/gm, '');

  // Remove horizontal rules
  text = text.replace(/^[-*_]{3,}$/gm, '');

  // Collapse multiple blank lines into single paragraph breaks
  text = text.replace(/\n{2,}/g, '. ');
  text = text.replace(/\n/g, ' ');

  // Remove excess whitespace
  text = text.replace(/\s{2,}/g, ' ').trim();

  // Ensure text doesn't end with orphaned punctuation artifacts
  text = text.replace(/\.\s*\.\s*\./g, '.');

  return text;
}

// ─── TTS Controller Factory ───────────────────────────────────────────────────

/**
 * Creates a TTS controller instance for a single answer.
 *
 * @param {Object}   options
 * @param {string}   options.text           - Raw answer text (Markdown OK)
 * @param {string}   [options.locale]       - BCP-47 locale (e.g. "en-US")
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

  const synth = window.speechSynthesis;

  // Prepare clean spoken text once
  const spokenText = markdownToSpeechText(text || '');

  let utterance = null;

  const buildUtterance = () => {
    const u = new SpeechSynthesisUtterance(spokenText);
    u.rate = rate;
    u.pitch = pitch;
    u.volume = volume;
    u.lang = locale;

    const voice = resolveVoice(locale);
    if (voice) u.voice = voice;

    u.onstart = () => onStart();
    u.onend = () => onEnd();
    u.onpause = () => onPause();
    u.onresume = () => onResume();
    u.onerror = (e) => {
      // 'interrupted' is not a real error — it means cancel() was called
      if (e.error !== 'interrupted' && e.error !== 'canceled') {
        onError(`Speech error: ${e.error || 'unknown'}`);
      }
    };
    return u;
  };

  return {
    isSupported: true,

    speak() {
      // Cancel any currently active speech before starting
      if (synth.speaking || synth.pending) {
        synth.cancel();
      }
      utterance = buildUtterance();
      // Small delay on some browsers to avoid immediate cancellation race
      setTimeout(() => {
        try {
          synth.speak(utterance);
        } catch (err) {
          onError('Unable to start speech. Please try again.');
        }
      }, 50);
    },

    stop() {
      try {
        synth.cancel();
      } catch (_) {}
      utterance = null;
    },

    pause() {
      try {
        if (synth.speaking && !synth.paused) {
          synth.pause();
        }
      } catch (_) {}
    },

    resume() {
      try {
        if (synth.paused) {
          synth.resume();
        }
      } catch (_) {}
    },
  };
}

/**
 * Stops all currently active speech synthesis immediately.
 * Use this as a global cleanup (New Chat, navigation).
 */
export function stopAllSpeech() {
  if (isTTSSupported()) {
    try {
      window.speechSynthesis.cancel();
    } catch (_) {}
  }
}
