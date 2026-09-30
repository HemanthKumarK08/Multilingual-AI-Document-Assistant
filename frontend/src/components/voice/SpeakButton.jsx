import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Volume2, VolumeX, Pause, Play, Loader2 } from 'lucide-react';
import {
  createTTSController,
  isTTSSupported,
  isVoiceAvailableForLocale,
  getTTSUnavailableMessage,
  stopAllSpeech,
} from './textToSpeech';

/**
 * SpeakButton Component (Multilingual Quality Repair)
 * Renders a compact TTS control for a single AI answer.
 *
 * Guarantees:
 * - Checks voice availability specifically for requested locale.
 * - For Indic languages without a native browser voice, gracefully shows
 *   a localized unavailable message and PREVENTS fallback to English voice.
 * - Deterministic single-answer playback with pause/resume/stop.
 *
 * @param {string}  props.text           - The AI answer text (Markdown OK, stripped for speech)
 * @param {string}  [props.locale]       - BCP-47 locale for voice selection (e.g. "en-US", "hi-IN", "te-IN")
 * @param {boolean} [props.disabled]     - External disable flag
 * @param {string}  [props.className]    - Additional CSS classes
 */
export default function SpeakButton({
  text,
  locale = 'en-US',
  disabled = false,
  className = '',
}) {
  const supported = isTTSSupported();

  // state: 'idle' | 'starting' | 'speaking' | 'paused' | 'error'
  const [ttsState, setTtsState] = useState('idle');
  const [errorMsg, setErrorMsg] = useState(null);
  const [voiceAvailable, setVoiceAvailable] = useState(() => isVoiceAvailableForLocale(locale));

  const controllerRef = useRef(null);
  const isMountedRef = useRef(true);

  // Sync voice availability when voices load or locale changes
  useEffect(() => {
    isMountedRef.current = true;
    const checkAvailability = () => {
      if (isMountedRef.current) {
        setVoiceAvailable(isVoiceAvailableForLocale(locale));
      }
    };

    checkAvailability();

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.addEventListener('voiceschanged', checkAvailability);
      return () => {
        isMountedRef.current = false;
        window.speechSynthesis.removeEventListener('voiceschanged', checkAvailability);
        stopAllSpeech();
        controllerRef.current = null;
      };
    }

    return () => {
      isMountedRef.current = false;
      stopAllSpeech();
      controllerRef.current = null;
    };
  }, [locale]);

  const safeSetState = useCallback((newState) => {
    if (isMountedRef.current) setTtsState(newState);
  }, []);

  const buildController = useCallback(() => {
    return createTTSController({
      text,
      locale,
      onStart: () => safeSetState('speaking'),
      onEnd: () => safeSetState('idle'),
      onPause: () => safeSetState('paused'),
      onResume: () => safeSetState('speaking'),
      onError: (msg) => {
        if (isMountedRef.current) {
          setErrorMsg(msg);
          safeSetState('error');
        }
      },
    });
  }, [text, locale, safeSetState]);

  const langPrefix = (locale || '').toLowerCase().split('-')[0];
  const isBackendSupported = ['en', 'hi', 'kn', 'te'].includes(langPrefix);
  const effectiveAvailable = isBackendSupported || voiceAvailable;

  const handleSpeak = useCallback(() => {
    if (!supported || disabled || !effectiveAvailable || ttsState === 'starting') return;

    // Stop any other answer that may be speaking
    stopAllSpeech();

    setErrorMsg(null);
    safeSetState('starting');

    const ctrl = buildController();
    controllerRef.current = ctrl;
    ctrl.speak();
  }, [supported, disabled, effectiveAvailable, ttsState, buildController, safeSetState]);

  const handleStop = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.stop();
    } else {
      stopAllSpeech();
    }
    safeSetState('idle');
  }, [safeSetState]);

  const handlePause = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.pause();
    }
  }, []);

  const handleResume = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.resume();
    }
  }, []);

  const handleDismissError = useCallback(() => {
    setErrorMsg(null);
    safeSetState('idle');
  }, [safeSetState]);

  if (!supported) {
    return (
      <div
        className={'inline-flex items-center gap-1.5 text-[11px] text-gray-600 ' + className}
        title="Text-to-Speech is not available in this browser"
      >
        <VolumeX size={14} className="text-gray-600" />
        <span className="hidden sm:inline">TTS unavailable</span>
      </div>
    );
  }

  // Graceful degradation when no compatible voice exists in backend or browser for this language
  if (!effectiveAvailable) {
    const unavailMsg = getTTSUnavailableMessage(locale);
    const shortLabel = unavailMsg.split('(')[0].trim();
    return (
      <div
        className={'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg text-[10px] font-medium text-amber-300/80 bg-amber-500/10 border border-amber-500/20 select-none ' + className}
        title={unavailMsg}
      >
        <VolumeX size={12} className="text-amber-400 shrink-0" />
        <span className="truncate max-w-[260px] sm:max-w-xs">{shortLabel}</span>
      </div>
    );
  }

  const isIdle = ttsState === 'idle' || ttsState === 'error';
  const isStarting = ttsState === 'starting';
  const isSpeaking = ttsState === 'speaking';
  const isPaused = ttsState === 'paused';

  return (
    <div className={'relative inline-flex items-center gap-1 ' + className}>
      {/* Primary speak/stop/resume button */}
      {isIdle && (
        <button
          type="button"
          onClick={handleSpeak}
          disabled={disabled || !text}
          aria-label="Read answer aloud"
          aria-pressed={false}
          title="Read answer aloud"
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium text-gray-400 hover:text-indigo-300 hover:bg-indigo-500/10 border border-transparent hover:border-indigo-500/20 transition disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500/50 active:scale-95"
        >
          <Volume2 size={13} />
          <span>Speak</span>
        </button>
      )}

      {isStarting && (
        <button
          type="button"
          disabled
          aria-label="Starting speech"
          aria-busy={true}
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium text-amber-400 border border-amber-500/20 bg-amber-500/10 cursor-wait"
        >
          <Loader2 size={13} className="animate-spin" />
          <span>Starting...</span>
        </button>
      )}

      {isSpeaking && (
        <>
          {/* Pause button */}
          <button
            type="button"
            onClick={handlePause}
            aria-label="Pause reading"
            aria-pressed={false}
            title="Pause reading"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 transition focus:outline-none focus:ring-2 focus:ring-indigo-500/50 active:scale-95 motion-reduce:animate-none"
          >
            <Pause size={13} />
            <span className="hidden sm:inline">Pause</span>
          </button>
          {/* Stop button */}
          <button
            type="button"
            onClick={handleStop}
            aria-label="Stop reading"
            aria-pressed={true}
            title="Stop reading"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition focus:outline-none focus:ring-2 focus:ring-rose-500/50 active:scale-95"
          >
            <VolumeX size={13} />
            <span className="hidden sm:inline">Stop</span>
          </button>
        </>
      )}

      {isPaused && (
        <>
          {/* Resume button */}
          <button
            type="button"
            onClick={handleResume}
            aria-label="Resume reading"
            aria-pressed={false}
            title="Resume reading"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-emerald-400 hover:text-white bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 transition focus:outline-none focus:ring-2 focus:ring-emerald-500/50 active:scale-95"
          >
            <Play size={13} />
            <span className="hidden sm:inline">Resume</span>
          </button>
          {/* Stop button */}
          <button
            type="button"
            onClick={handleStop}
            aria-label="Stop reading"
            aria-pressed={false}
            title="Stop reading"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition focus:outline-none focus:ring-2 focus:ring-rose-500/50 active:scale-95"
          >
            <VolumeX size={13} />
            <span className="hidden sm:inline">Stop</span>
          </button>
        </>
      )}

      {/* Dismissible error badge */}
      {ttsState === 'error' && errorMsg && (
        <button
          type="button"
          onClick={handleDismissError}
          aria-label="Dismiss TTS error"
          title={errorMsg}
          className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition focus:outline-none focus:ring-2 focus:ring-rose-500/50"
        >
          <VolumeX size={13} />
          <span className="hidden sm:inline max-w-[140px] truncate">Speech error</span>
        </button>
      )}

      {/* Accessible live region for screen readers */}
      <span
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {isSpeaking ? 'Reading answer aloud' : isPaused ? 'Reading paused' : ''}
      </span>
    </div>
  );
}
