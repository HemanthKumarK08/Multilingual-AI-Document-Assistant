/**
 * Speech Recognition Utility Module (Phase 9.1 & Reliability Hardening)
 * Provides browser capability detection, language locale mapping,
 * error humanization, continuous recognition support, and a robust SpeechRecognition wrapper.
 */

// Language code to SpeechRecognition BCP-47 locale mapping
export const SPEECH_LOCALE_MAP = {
  en: "en-US",
  "en-US": "en-US",
  hi: "hi-IN",
  "hi-IN": "hi-IN",
  kn: "kn-IN",
  "kn-IN": "kn-IN",
  te: "te-IN",
  "te-IN": "te-IN",
  auto: "en-US", // Default recognition locale for auto-detection
};

/**
 * Resolves application language code to standard BCP-47 locale.
 * @param {string} langCode - Language code ('en', 'hi', 'kn', 'te', 'auto', etc.)
 * @returns {string} BCP-47 locale string (e.g. 'en-US', 'hi-IN')
 */
export function mapLanguageToSpeechLocale(langCode) {
  if (!langCode) return "en-US";
  const normalized = langCode.trim().toLowerCase();
  return SPEECH_LOCALE_MAP[normalized] || SPEECH_LOCALE_MAP[langCode] || "en-US";
}

/**
 * Returns the native SpeechRecognition constructor if supported by the browser.
 * @returns {typeof SpeechRecognition | null}
 */
export function getSpeechRecognitionClass() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

/**
 * Checks if Speech Recognition is supported in the current environment.
 * @returns {boolean}
 */
export function isSpeechRecognitionSupported() {
  return getSpeechRecognitionClass() !== null;
}

/**
 * Maps technical SpeechRecognition error codes to user-friendly messages.
 * @param {string} errorCode - Error code from SpeechRecognitionErrorEvent
 * @returns {string} Human-readable error message
 */
export function humanizeSpeechError(errorCode) {
  switch (errorCode) {
    case "not-allowed":
      return "Microphone permission was denied. Please allow microphone access in your browser settings.";
    case "service-not-allowed":
      return "Speech recognition service was denied by browser or system policy.";
    case "no-speech":
      return "No speech was detected. Please try speaking closer to the microphone.";
    case "audio-capture":
      return "No microphone was found or could be accessed. Please check your audio input device.";
    case "network":
      return "Speech recognition network service is currently unavailable. Please check your connection.";
    case "aborted":
      return "Speech input was stopped.";
    case "language-not-supported":
      return "The selected language is not supported for speech recognition in this browser.";
    case "unsupported":
      return "Speech recognition is not supported in this browser. Please use Google Chrome or a supported browser.";
    default:
      return "Speech recognition encountered an unexpected error. Please try again.";
  }
}

/**
 * Creates and configures a SpeechRecognition instance with continuous stream support.
 * 
 * @param {Object} options
 * @param {string} [options.language='en-US'] - Language locale
 * @param {boolean} [options.continuous=true] - Continuous streaming mode
 * @param {Function} [options.onStart] - Called when recognition starts
 * @param {Function} [options.onInterim] - Called with interim transcript (text)
 * @param {Function} [options.onFinal] - Called with final transcript (text)
 * @param {Function} [options.onError] - Called with humanized error string and error code
 * @param {Function} [options.onEnd] - Called when recognition session ends
 * @returns {{ start: Function, stop: Function, abort: Function, isSupported: boolean }}
 */
export function createSpeechRecognizer({
  language = "en-US",
  continuous = true,
  onStart = () => {},
  onInterim = () => {},
  onFinal = () => {},
  onError = () => {},
  onEnd = () => {},
} = {}) {
  const SpeechClass = getSpeechRecognitionClass();

  if (!SpeechClass) {
    return {
      start: () => onError(humanizeSpeechError("unsupported"), "unsupported"),
      stop: () => {},
      abort: () => {},
      isSupported: false,
    };
  }

  let recognition = null;
  let hasReceivedFinal = false;

  try {
    recognition = new SpeechClass();
    recognition.continuous = continuous;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = mapLanguageToSpeechLocale(language);

    recognition.onstart = () => {
      hasReceivedFinal = false;
      onStart();
    };

    recognition.onresult = (event) => {
      let interim = "";
      let finalTranscript = "";

      for (let i = 0; i < event.results.length; ++i) {
        const res = event.results[i];
        const transcript = res[0]?.transcript || "";
        if (res.isFinal) {
          finalTranscript += transcript + " ";
        } else {
          interim += transcript;
        }
      }

      finalTranscript = finalTranscript.trim();
      interim = interim.trim();

      if (interim && onInterim) {
        onInterim(interim);
      }

      if (finalTranscript) {
        hasReceivedFinal = true;
        onFinal(finalTranscript);
      }
    };

    recognition.onerror = (event) => {
      const msg = humanizeSpeechError(event.error);
      onError(msg, event.error);
    };

    recognition.onend = () => {
      onEnd({ hasReceivedFinal });
    };

    return {
      start: () => {
        try {
          recognition.lang = mapLanguageToSpeechLocale(language);
          recognition.start();
        } catch (err) {
          if (err.name !== "InvalidStateError") {
            onError(humanizeSpeechError("audio-capture"), "audio-capture");
          }
        }
      },
      stop: () => {
        try {
          recognition.stop();
        } catch (e) {
          // Ignore state errors on stop
        }
      },
      abort: () => {
        try {
          recognition.abort();
        } catch (e) {
          // Ignore on abort
        }
      },
      isSupported: true,
    };
  } catch (err) {
    return {
      start: () => onError(humanizeSpeechError("unknown"), "unknown"),
      stop: () => {},
      abort: () => {},
      isSupported: false,
    };
  }
}
