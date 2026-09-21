import React, { useState, useEffect, useRef, useCallback } from "react";
import { Mic, MicOff, AlertCircle, X, Loader2 } from "lucide-react";
import {
  createSpeechRecognizer,
  isSpeechRecognitionSupported,
  mapLanguageToSpeechLocale,
  humanizeSpeechError,
} from "./speechRecognition";

/**
 * SpeechRecognitionButton Component (Phase 9.1)
 * Accessible, responsive microphone button with visual state feedback
 * for browser-native speech-to-text.
 * 
 * @param {Object} props
 * @param {Function} props.onTranscript - Callback receiving recognized final text string
 * @param {Function} [props.onInterimTranscript] - Optional callback for live interim text
 * @param {string} [props.language="en-US"] - Language code or locale ("auto", "en", "hi", "kn", "te")
 * @param {boolean} [props.disabled=false] - Whether the button is disabled
 * @param {string} [props.className=""] - Additional CSS classes
 */
export default function SpeechRecognitionButton({
  onTranscript,
  onInterimTranscript,
  language = "en-US",
  disabled = false,
  className = "",
}) {
  const [supported, setSupported] = useState(true);
  const [state, setState] = useState("idle"); // "idle" | "listening" | "processing" | "error" | "unsupported"
  const [errorMessage, setErrorMessage] = useState(null);
  const [interimText, setInterimText] = useState("");

  const recognizerRef = useRef(null);

  // Check browser capability on mount
  useEffect(() => {
    const isSup = isSpeechRecognitionSupported();
    setSupported(isSup);
    if (!isSup) {
      setState("unsupported");
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognizerRef.current) {
        recognizerRef.current.abort();
      }
    };
  }, []);

  const handleStartListening = useCallback(() => {
    if (disabled || !supported) return;

    setErrorMessage(null);
    setInterimText("");
    setState("listening");

    const recognizer = createSpeechRecognizer({
      language,
      onStart: () => {
        setState("listening");
      },
      onInterim: (text) => {
        setInterimText(text);
        if (onInterimTranscript) {
          onInterimTranscript(text);
        }
      },
      onFinal: (finalText) => {
        setState("idle");
        setInterimText("");
        if (onTranscript && finalText) {
          onTranscript(finalText);
        }
      },
      onError: (msg) => {
        setErrorMessage(msg);
        setState("error");
        setInterimText("");
      },
      onEnd: () => {
        setState((prev) => (prev === "listening" ? "idle" : prev));
        setInterimText("");
      },
    });

    recognizerRef.current = recognizer;
    recognizer.start();
  }, [disabled, supported, language, onTranscript, onInterimTranscript]);

  const handleStopListening = useCallback(() => {
    if (recognizerRef.current) {
      setState("processing");
      recognizerRef.current.stop();
    } else {
      setState("idle");
    }
  }, []);

  const toggleListening = () => {
    if (state === "listening") {
      handleStopListening();
    } else {
      handleStartListening();
    }
  };

  const clearError = (e) => {
    e.stopPropagation();
    setErrorMessage(null);
    setState(supported ? "idle" : "unsupported");
  };

  const isListening = state === "listening";
  const isProcessing = state === "processing";
  const isError = state === "error" && Boolean(errorMessage);
  const isUnsupported = state === "unsupported" || !supported;

  const locale = mapLanguageToSpeechLocale(language);

  const getButtonTitle = () => {
    if (isUnsupported) return "Speech recognition is not supported in this browser";
    if (isListening) return "Listening (" + locale + ")... Click to stop";
    return "Voice Input (" + locale + ")";
  };

  return (
    <div className={"relative inline-flex items-center " + className}>
      {/* Speech Recognition Button */}
      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled || isUnsupported}
        aria-label={isListening ? "Stop voice input" : "Start voice input"}
        aria-pressed={isListening}
        aria-describedby={isError ? "speech-error-msg" : undefined}
        title={getButtonTitle()}
        className={
          "p-3 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center shrink-0 select-none active:scale-95 focus:outline-none focus:ring-2 focus:ring-brand-500/50 " +
          (isListening
            ? "bg-rose-600 text-white shadow-lg shadow-rose-600/40 animate-pulse"
            : isProcessing
            ? "bg-amber-600/20 text-amber-300 border border-amber-500/30"
            : isError
            ? "bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20"
            : isUnsupported
            ? "bg-surface-base text-gray-600 cursor-not-allowed border border-surface-border"
            : "bg-surface-base hover:bg-surface-border/80 text-gray-300 hover:text-white border border-surface-border disabled:opacity-50 disabled:cursor-not-allowed")
        }
      >
        {isProcessing ? (
          <Loader2 size={16} className="animate-spin text-amber-300" />
        ) : isListening ? (
          <Mic size={16} className="text-white animate-bounce" />
        ) : isUnsupported ? (
          <MicOff size={16} className="text-gray-600" />
        ) : (
          <Mic size={16} />
        )}
      </button>

      {/* Live Interim Transcript or Listening Pill */}
      {isListening && (
        <div className="absolute bottom-full mb-2 right-0 sm:right-0 z-30 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-card/95 backdrop-blur-md border border-rose-500/40 text-xs shadow-2xl animate-fadeIn whitespace-nowrap">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <span className="font-medium text-rose-300">
            {interimText ? "\"" + interimText + "\"" : "Listening... Speak now"}
          </span>
          <span className="text-[10px] text-gray-400 font-mono bg-surface-base px-1.5 py-0.5 rounded border border-surface-border">
            {locale}
          </span>
        </div>
      )}

      {/* Error Popup Banner */}
      {isError && (
        <div
          id="speech-error-msg"
          role="alert"
          className="absolute bottom-full mb-2 right-0 z-30 max-w-xs sm:max-w-sm p-3 rounded-2xl bg-surface-card border border-rose-500/30 shadow-2xl text-xs text-rose-300 flex items-start gap-2.5 animate-fadeIn"
        >
          <AlertCircle size={15} className="text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-rose-200 text-[11px]">Speech Recognition Error</p>
            <p className="text-[11px] text-gray-300 mt-0.5 leading-relaxed">{errorMessage}</p>
          </div>
          <button
            type="button"
            onClick={clearError}
            aria-label="Dismiss error"
            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-surface-base transition shrink-0"
          >
            <X size={13} />
          </button>
        </div>
      )}
    </div>
  );
}
