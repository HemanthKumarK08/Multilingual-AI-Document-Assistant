import React from "react";
import { X, Loader2 } from "lucide-react";

/**
 * VoiceListeningIndicator Component (Phase 9.2 / updated Phase 9.3)
 * Lightweight visual feedback: animated CSS waveform bars, elapsed timer,
 * interim transcript preview, language label, and a cancel button.
 * Respects prefers-reduced-motion.
 *
 * @param {boolean}  props.isStarting      - Microphone initializing
 * @param {boolean}  props.isListening     - Actively capturing voice
 * @param {boolean}  props.isProcessing    - Finalizing speech recognition
 * @param {string}   props.interimText     - Live unfinalized recognized speech
 * @param {string}   props.locale          - BCP-47 locale (e.g. "en-US")
 * @param {string}   props.languageLabel   - Human-readable name (e.g. "English", "ಕನ್ನಡ")
 * @param {number}   props.elapsedSeconds  - Elapsed listening time in seconds
 * @param {Function} props.onCancel        - Abort voice input callback
 */
export default function VoiceListeningIndicator({
  isStarting = false,
  isListening = false,
  isProcessing = false,
  interimText = "",
  locale = "en-US",
  languageLabel = "English",
  elapsedSeconds = 0,
  onCancel,
}) {
  if (!isStarting && !isListening && !isProcessing) {
    return null;
  }

  // Format elapsed seconds as MM:SS
  const mins = Math.floor(elapsedSeconds / 60);
  const secs = elapsedSeconds % 60;
  const timeStr =
    String(mins).padStart(2, "0") + ":" + String(secs).padStart(2, "0");

  // Status text shown to the user
  const statusText = isProcessing
    ? "Processing speech..."
    : isStarting
    ? "Starting microphone..."
    : `Listening in ${languageLabel}...`;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={statusText}
      className="absolute bottom-full mb-2 right-0 z-30 max-w-sm sm:max-w-md w-auto p-2.5 sm:p-3 rounded-2xl bg-surface-card/95 backdrop-blur-md border border-rose-500/40 text-xs shadow-2xl animate-fadeIn flex flex-col gap-2"
    >
      {/* Top Row: Status icon + text + waveform */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {isProcessing ? (
            <Loader2 size={15} className="animate-spin text-amber-400 shrink-0" />
          ) : isStarting ? (
            <Loader2 size={15} className="animate-spin text-indigo-400 shrink-0" />
          ) : (
            <div className="relative flex items-center justify-center">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping absolute motion-reduce:hidden" />
              <span className="w-2 h-2 rounded-full bg-rose-500 relative shrink-0" />
            </div>
          )}

          <span className="font-semibold text-white text-[11px] sm:text-xs">
            {statusText}
          </span>

          {/* CSS-only animated waveform bars — pure CSS animations, zero raw audio */}
          {isListening && (
            <div
              className="flex items-center gap-0.5 h-4 px-1 select-none"
              aria-hidden="true"
              title="Voice Activity Indicator"
            >
              <span className="w-0.5 h-2 bg-rose-400 rounded-full animate-pulse motion-reduce:animate-none" />
              <span className="w-0.5 h-3.5 bg-rose-500 rounded-full animate-pulse motion-reduce:animate-none [animation-delay:150ms]" />
              <span className="w-0.5 h-4 bg-rose-400 rounded-full animate-pulse motion-reduce:animate-none [animation-delay:300ms]" />
              <span className="w-0.5 h-2.5 bg-rose-500 rounded-full animate-pulse motion-reduce:animate-none [animation-delay:450ms]" />
              <span className="w-0.5 h-3.5 bg-rose-400 rounded-full animate-pulse motion-reduce:animate-none [animation-delay:200ms]" />
              <span className="w-0.5 h-1.5 bg-rose-500 rounded-full animate-pulse motion-reduce:animate-none [animation-delay:350ms]" />
            </div>
          )}
        </div>

        {/* Timer, Language pill, Cancel */}
        <div className="flex items-center gap-1.5 shrink-0">
          {isListening && (
            <span className="text-[10px] font-mono text-gray-400 bg-surface-base px-1.5 py-0.5 rounded border border-surface-border">
              {timeStr}
            </span>
          )}

          {/* Language label pill — human-readable, not raw locale */}
          <span
            className="text-[10px] font-semibold text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20 max-w-[80px] truncate"
            title={locale}
          >
            {languageLabel}
          </span>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              aria-label="Cancel voice input"
              title="Cancel voice input (Esc)"
              className="px-2 py-0.5 rounded-lg bg-surface-base hover:bg-rose-500/20 text-gray-300 hover:text-rose-300 border border-surface-border text-[10px] font-medium transition flex items-center gap-1 active:scale-95"
            >
              <X size={11} />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>

      {/* Interim Transcript Live Preview */}
      {interimText && (
        <div className="px-2.5 py-1.5 rounded-xl bg-surface-base/80 border border-surface-border text-gray-300 italic text-[11px] leading-relaxed max-h-20 overflow-y-auto">
          &ldquo;{interimText}&rdquo;
        </div>
      )}
    </div>
  );
}
