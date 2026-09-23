import React from "react";
import { Languages } from "lucide-react";

/**
 * VoiceLanguageSelector Component (Phase 9.3)
 * Dedicated voice-language picker — controls speech recognition locale only.
 * Separate from the RAG response-language selector in the top bar.
 * Disabled during active recognition to prevent mid-session locale changes.
 *
 * @param {string}   props.value       - Language code: "en" | "hi" | "kn" | "te"
 * @param {Function} props.onChange    - Called with the new language code on change
 * @param {boolean}  [props.disabled]  - True when mic is active
 * @param {string}   [props.className] - Extra CSS classes
 */

export const VOICE_LANGUAGES = [
  { code: "en", label: "English",  nativeLabel: "English",  locale: "en-US" },
  { code: "hi", label: "Hindi",    nativeLabel: "हिन्दी",   locale: "hi-IN" },
  { code: "kn", label: "Kannada",  nativeLabel: "ಕನ್ನಡ",   locale: "kn-IN" },
  { code: "te", label: "Telugu",   nativeLabel: "తెలుగు",  locale: "te-IN" },
];

/** Returns the human-readable English label for a language code. */
export function getVoiceLanguageLabel(code) {
  const lang = VOICE_LANGUAGES.find((l) => l.code === code);
  return lang ? lang.label : "English";
}

/** Returns the native-script label for a language code. */
export function getVoiceLanguageNativeLabel(code) {
  const lang = VOICE_LANGUAGES.find((l) => l.code === code);
  return lang ? lang.nativeLabel : "English";
}

export default function VoiceLanguageSelector({
  value = "en",
  onChange,
  disabled = false,
  className = "",
}) {
  const selectedLang = VOICE_LANGUAGES.find((l) => l.code === value) || VOICE_LANGUAGES[0];

  return (
    <div
      className={"flex items-center gap-1.5 " + className}
      title={
        disabled
          ? "Language cannot be changed while microphone is active. Stop or cancel first."
          : "Select voice input language"
      }
    >
      <Languages
        size={13}
        className={disabled ? "text-gray-600 shrink-0" : "text-indigo-400 shrink-0"}
        aria-hidden="true"
      />
      <select
        id="voice-language-selector"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        disabled={disabled}
        aria-label="Voice input language"
        aria-disabled={disabled}
        className={
          "bg-transparent text-xs font-medium focus:outline-none " +
          (disabled
            ? "text-gray-600 cursor-not-allowed opacity-60"
            : "text-gray-200 hover:text-white cursor-pointer")
        }
      >
        {VOICE_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-surface-card text-white">
            {lang.nativeLabel} ({lang.label})
          </option>
        ))}
      </select>
    </div>
  );
}
