import React, { useState, useEffect, useRef, useCallback } from "react";
import { Mic, MicOff, AlertCircle, X, Loader2 } from "lucide-react";
import {
  createSpeechRecognizer,
  isSpeechRecognitionSupported,
  mapLanguageToSpeechLocale,
} from "./speechRecognition";
import VoiceListeningIndicator from "./VoiceListeningIndicator";

/**
 * SpeechRecognitionButton Component (Phase 9.3 & Reliability Hardening)
 * Accessible, responsive microphone button with multilingual locale support,
 * continuous recognition, visual state feedback, waveform activity, elapsed timer,
 * cancellation, and duplicate session protection.
 *
 * Voice State Machine:
 *   IDLE → STARTING → LISTENING → PROCESSING → TRANSCRIPT_READY → IDLE
 *   Any active state → ERROR
 *   Browser check → UNSUPPORTED
 */
export default function SpeechRecognitionButton({
  onTranscript,
  onInterimTranscript,
  language = "en",
  languageLabel = "English",
  onVoiceStateChange,
  disabled = false,
  className = "",
}) {
  const [supported, setSupported] = useState(true);
  const [state, setState] = useState("idle");
  // idle | starting | listening | processing | transcript_ready | error | unsupported
  const [errorMessage, setErrorMessage] = useState(null);
  const [interimText, setInterimText] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const recognizerRef = useRef(null);
  const timerRef = useRef(null);
  const isCancelledRef = useRef(false);
  const isManualStopRef = useRef(false);
  const isRestartingRef = useRef(false);
  const activeLanguageRef = useRef(language);
  const accumulatedTranscriptRef = useRef("");

  // Check browser capability on mount
  useEffect(() => {
    const isSup = isSpeechRecognitionSupported();
    setSupported(isSup);
    if (!isSup) {
      setState("unsupported");
    }
  }, []);

  // — Timer helpers —
  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setElapsedSeconds(0);
    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setElapsedSeconds(0);
  }, []);

  // Cleanup on unmount (navigation away)
  useEffect(() => {
    return () => {
      stopTimer();
      if (recognizerRef.current) {
        recognizerRef.current.abort();
        recognizerRef.current = null;
      }
    };
  }, [stopTimer]);

  const handleCancel = useCallback(() => {
    isCancelledRef.current = true;
    isManualStopRef.current = true;
    stopTimer();
    setInterimText("");
    setErrorMessage(null);
    accumulatedTranscriptRef.current = "";
    if (recognizerRef.current) {
      recognizerRef.current.abort();
      recognizerRef.current = null;
    }
    setState(supported ? "idle" : "unsupported");
    if (onVoiceStateChange) onVoiceStateChange(false);
  }, [stopTimer, supported, onVoiceStateChange]);

  // Global Escape key handler to cancel active voice input
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && (state === "listening" || state === "starting")) {
        e.preventDefault();
        handleCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [state, handleCancel]);

  const startRecognitionSession = useCallback((langToUse) => {
    // Single active instance guard
    if (recognizerRef.current) {
      try {
        recognizerRef.current.abort();
      } catch (e) {}
      recognizerRef.current = null;
    }

    const recognizer = createSpeechRecognizer({
      language: langToUse,
      continuous: true,
      onStart: () => {
        if (!isCancelledRef.current) {
          isRestartingRef.current = false;
          setState("listening");
          if (!timerRef.current) {
            startTimer();
          }
        }
      },
      onInterim: (text) => {
        if (!isCancelledRef.current) {
          setInterimText(text);
          if (onInterimTranscript) {
            onInterimTranscript(text);
          }
        }
      },
      onFinal: (finalText) => {
        if (!isCancelledRef.current && finalText) {
          accumulatedTranscriptRef.current = finalText;
          setInterimText("");
          if (onTranscript) {
            onTranscript(finalText);
          }
        }
      },
      onError: (msg, code) => {
        if (isCancelledRef.current || isManualStopRef.current) return;

        // Non-fatal transient errors (like no-speech pause) in listening mode do not abort user session
        if (code === "no-speech" && !isManualStopRef.current) {
          return;
        }

        stopTimer();
        setErrorMessage(msg);
        setState("error");
        setInterimText("");
        if (onVoiceStateChange) onVoiceStateChange(false);
      },
      onEnd: () => {
        if (isCancelledRef.current) {
          stopTimer();
          setInterimText("");
          return;
        }

        // If user manually stopped, finish smoothly
        if (isManualStopRef.current) {
          stopTimer();
          setInterimText("");
          setState("transcript_ready");
          if (onTranscript && accumulatedTranscriptRef.current) {
            onTranscript(accumulatedTranscriptRef.current);
          }
          setTimeout(() => {
            setState((prev) => {
              if (prev === "transcript_ready") {
                if (onVoiceStateChange) onVoiceStateChange(false);
                return "idle";
              }
              return prev;
            });
          }, 300);
          return;
        }

        // Unexpected browser recognition end while user is still in listening state:
        // Safely auto-restart recognition to keep microphone open without losing text.
        if (!isRestartingRef.current) {
          isRestartingRef.current = true;
          setTimeout(() => {
            if (!isCancelledRef.current && !isManualStopRef.current) {
              try {
                startRecognitionSession(langToUse);
              } catch (e) {
                stopTimer();
                setState("idle");
                if (onVoiceStateChange) onVoiceStateChange(false);
              }
            }
          }, 150);
        }
      },
    });

    recognizerRef.current = recognizer;
    recognizer.start();
  }, [onInterimTranscript, onTranscript, onVoiceStateChange, startTimer, stopTimer]);

  const handleStartListening = useCallback(() => {
    if (
      disabled ||
      !supported ||
      state === "starting" ||
      state === "listening" ||
      state === "processing"
    ) {
      return; // Duplicate click protection
    }

    isCancelledRef.current = false;
    isManualStopRef.current = false;
    isRestartingRef.current = false;
    accumulatedTranscriptRef.current = "";
    setErrorMessage(null);
    setInterimText("");
    setState("starting");
    if (onVoiceStateChange) onVoiceStateChange(true);

    activeLanguageRef.current = language;
    startRecognitionSession(language);
  }, [disabled, supported, state, language, onVoiceStateChange, startRecognitionSession]);

  const handleStopListening = useCallback(() => {
    isManualStopRef.current = true;
    setState("processing");
    if (recognizerRef.current) {
      recognizerRef.current.stop();
    } else {
      stopTimer();
      setState("idle");
      if (onVoiceStateChange) onVoiceStateChange(false);
    }
  }, [stopTimer, onVoiceStateChange]);

  const toggleListening = () => {
    if (state === "listening" || state === "starting") {
      handleStopListening();
    } else if (state === "idle" || state === "error" || state === "transcript_ready") {
      handleStartListening();
    }
  };

  const clearError = (e) => {
    e.stopPropagation();
    setErrorMessage(null);
    setState(supported ? "idle" : "unsupported");
  };

  const isStarting = state === "starting";
  const isListening = state === "listening";
  const isProcessing = state === "processing";
  const isError = state === "error" && Boolean(errorMessage);
  const isUnsupported = state === "unsupported" || !supported;

  const locale = mapLanguageToSpeechLocale(language);

  const getButtonTitle = () => {
    if (isUnsupported) return "Voice input is not supported in this browser";
    if (isStarting) return `Starting microphone (${languageLabel})...`;
    if (isListening) return `Listening in ${languageLabel} (${locale})... Click to finish (or Esc to cancel)`;
    if (isProcessing) return "Processing speech...";
    return `Start voice input in ${languageLabel} (${locale})`;
  };

  return (
    <div className={"relative inline-flex items-center " + className}>
      {/* Microphone Trigger Button */}
      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled || isUnsupported || isStarting || isProcessing}
        aria-label={
          isListening
            ? `Stop voice input (${languageLabel})`
            : isStarting
            ? "Starting microphone"
            : isProcessing
            ? "Processing speech"
            : `Start voice input in ${languageLabel}`
        }
        aria-pressed={isListening}
        aria-busy={isStarting || isProcessing}
        aria-describedby={isError ? "speech-error-msg" : undefined}
        title={getButtonTitle()}
        className={
          "p-3 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center shrink-0 select-none active:scale-95 focus:outline-none focus:ring-2 focus:ring-brand-500/50 " +
          (isListening
            ? "bg-rose-600 text-white shadow-lg shadow-rose-600/40 animate-pulse"
            : isStarting || isProcessing
            ? "bg-amber-600/20 text-amber-300 border border-amber-500/30 cursor-wait"
            : isError
            ? "bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20"
            : isUnsupported
            ? "bg-surface-base text-gray-600 cursor-not-allowed border border-surface-border"
            : "bg-surface-base hover:bg-surface-border/80 text-gray-300 hover:text-white border border-surface-border disabled:opacity-50 disabled:cursor-not-allowed")
        }
      >
        {isStarting || isProcessing ? (
          <Loader2 size={16} className="animate-spin text-amber-300" />
        ) : isListening ? (
          <Mic size={16} className="text-white animate-bounce motion-reduce:animate-none" />
        ) : isUnsupported ? (
          <MicOff size={16} className="text-gray-600" />
        ) : (
          <Mic size={16} />
        )}
      </button>

      {/* Voice Listening & Activity Indicator Overlay */}
      <VoiceListeningIndicator
        isStarting={isStarting}
        isListening={isListening}
        isProcessing={isProcessing}
        interimText={interimText}
        locale={locale}
        languageLabel={languageLabel}
        elapsedSeconds={elapsedSeconds}
        onCancel={handleCancel}
      />

      {/* Dismissible Error Banner */}
      {isError && (
        <div
          id="speech-error-msg"
          role="alert"
          aria-live="polite"
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
