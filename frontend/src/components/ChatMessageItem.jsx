import React from 'react';
import {
  Sparkles,
  ShieldCheck,
  Info,
  Globe,
  AlertCircle,
  Copy,
  Check,
  User,
  Mic,
} from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import CitationsSection from './CitationsSection';
import TechnicalDetailsPanel from './TechnicalDetailsPanel';
import FeedbackWidget from './FeedbackWidget';
import SpeakButton from './voice/SpeakButton';

const DEFAULT_TTS_LOCALE_MAP = {
  en: 'en-US',
  hi: 'hi-IN',
  kn: 'kn-IN',
  te: 'te-IN',
};

const DEFAULT_LANGUAGE_DISPLAY_NAMES = {
  en: 'English',
  hi: 'हिन्दी',
  kn: 'ಕನ್ನಡ',
  te: 'తెలుగు',
};

/**
 * Authoritative Response State Derivation
 * Maps backend payload metadata to clear, mutually exclusive UI states:
 * - GROUNDED: True grounded answer supported by retrieved evidence with valid citations.
 * - LANGUAGE_UNAVAILABLE: Multilingual generation provider unavailable for requested Indic language.
 * - INSUFFICIENT_EVIDENCE: Out-of-domain or insufficient corpus evidence.
 * - ERROR: System or network exception.
 */
export function deriveResponseState(msg) {
  if (msg.is_error || msg.response_state === 'ERROR') {
    return 'ERROR';
  }
  if (msg.response_state === 'LANGUAGE_UNAVAILABLE') {
    return 'LANGUAGE_UNAVAILABLE';
  }
  if (msg.response_state === 'INSUFFICIENT_EVIDENCE') {
    return 'INSUFFICIENT_EVIDENCE';
  }
  if (msg.response_state === 'GROUNDED') {
    return (Array.isArray(msg.citations) && msg.citations.length > 0 && !msg.is_fallback)
      ? 'GROUNDED'
      : 'INSUFFICIENT_EVIDENCE';
  }

  // Fallback heuristics for legacy or unannotated payloads
  const content = msg.content || msg.answer_text || '';
  const isLangUnavail = (
    msg.fallback_reason === 'MISSING_TARGET_SCRIPT' ||
    msg.fallback_reason === 'LANGUAGE_UNAVAILABLE' ||
    msg.fallback_reason === 'UNAVAILABLE_LANGUAGE' ||
    content.includes('सेवा वर्तमान में अनुपलब्ध') ||
    content.includes('ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ') ||
    content.includes('సేవ ప్రస్తుతం అందుబాటులో లేదు')
  );

  if (isLangUnavail) {
    return 'LANGUAGE_UNAVAILABLE';
  }

  if (msg.is_fallback || msg.grounded === false) {
    return 'INSUFFICIENT_EVIDENCE';
  }

  if (Array.isArray(msg.citations) && msg.citations.length > 0) {
    return 'GROUNDED';
  }

  return 'INSUFFICIENT_EVIDENCE';
}

/**
 * ChatMessageItem Component
 * Memoized individual chat message item providing honest response states,
 * clear visual hierarchy, and compact padding without empty vertical space.
 */
function ChatMessageItem({
  msg,
  index,
  isCopied = false,
  onCopy,
  ttsLocaleMap = DEFAULT_TTS_LOCALE_MAP,
  languageDisplayNames = DEFAULT_LANGUAGE_DISPLAY_NAMES,
}) {
  const isUser = msg.role === 'user';
  const responseState = !isUser ? deriveResponseState(msg) : null;

  const isGrounded = responseState === 'GROUNDED';
  const isLanguageUnavailable = responseState === 'LANGUAGE_UNAVAILABLE';
  const isInsufficientEvidence = responseState === 'INSUFFICIENT_EVIDENCE';
  const isError = responseState === 'ERROR';

  const citationCount = Array.isArray(msg.citations) ? msg.citations.length : 0;
  const langLabel = languageDisplayNames[msg.detected_language] || msg.detected_language || 'English';

  return (
    <div
      className={`flex gap-3 sm:gap-3.5 ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-brand-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20 mt-0.5">
          <Sparkles size={16} />
        </div>
      )}

      <div
        className={`max-w-3xl sm:max-w-4xl rounded-2xl sm:rounded-3xl p-4 sm:p-5 shadow-lg space-y-3 ${
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-surface-card border border-surface-border text-gray-100 rounded-tl-sm'
        }`}
      >
        {/* Assistant Header Status Bar */}
        {!isUser && (
          <div className="flex items-center justify-between border-b border-surface-border/60 pb-2 text-[11px]">
            <div className="flex items-center gap-2 flex-wrap">
              {/* Authoritative State Badge */}
              {isGrounded && (
                <span
                  data-testid="grounded-badge"
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm"
                >
                  <ShieldCheck size={12} />
                  <span>
                    Grounded in {citationCount} {citationCount === 1 ? 'Source' : 'Sources'}
                  </span>
                </span>
              )}

              {isLanguageUnavailable && (
                <span
                  data-testid="language-unavailable-badge"
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm"
                >
                  <Globe size={12} />
                  <span>Language Unavailable</span>
                </span>
              )}

              {isInsufficientEvidence && (
                <span
                  data-testid="insufficient-evidence-badge"
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm"
                >
                  <Info size={12} />
                  <span>Insufficient Evidence</span>
                </span>
              )}

              {isError && (
                <span
                  data-testid="error-badge"
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-sm"
                >
                  <AlertCircle size={12} />
                  <span>System Error</span>
                </span>
              )}

              {/* Language Pill */}
              {msg.detected_language && (
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                  isLanguageUnavailable
                    ? 'text-amber-300 bg-amber-500/10 border-amber-500/20'
                    : 'text-indigo-300 bg-indigo-500/10 border-indigo-500/20'
                }`}>
                  {langLabel}
                </span>
              )}
            </div>

            {onCopy && (
              <button
                type="button"
                onClick={() => onCopy(msg.content, index)}
                className="inline-flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition py-0.5 px-1.5 rounded-md hover:bg-surface-base"
                title="Copy answer"
              >
                {isCopied ? (
                  <>
                    <Check size={12} className="text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            )}
          </div>
        )}

        {/* Fallback Notice Banners */}
        {!isUser && isInsufficientEvidence && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2">
            <Info size={15} className="text-amber-400 shrink-0 mt-0.5" />
            <p className="text-[11px] text-amber-200/90 leading-relaxed">
              I couldn't find sufficient supporting evidence in the indexed institutional documents to answer this question reliably.
            </p>
          </div>
        )}

        {!isUser && isLanguageUnavailable && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2">
            <Globe size={15} className="text-amber-400 shrink-0 mt-0.5" />
            <p className="text-[11px] text-amber-200/90 leading-relaxed">
              Multilingual model inference service is currently unavailable for the requested language. You can switch the Response language to English or configure a multilingual LLM API key.
            </p>
          </div>
        )}

        {/* Primary Answer Content */}
        <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed font-normal text-gray-100">
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <MarkdownRenderer content={msg.content} />
          )}
        </div>

        {/* Citations & Evidence Section — ONLY for strictly grounded answers */}
        {!isUser && isGrounded && msg.citations && msg.citations.length > 0 && (
          <CitationsSection citations={msg.citations} />
        )}

        {/* Technical Details Panel — Collapsed by default */}
        {!isUser && (
          <TechnicalDetailsPanel msg={{
            ...msg,
            response_state: responseState,
          }} />
        )}

        {/* TTS Speak Button — Available on assistant messages */}
        {!isUser && msg.content && (
          <div className="pt-2 border-t border-surface-border/40 flex items-center gap-2">
            <SpeakButton
              text={msg.content}
              locale={ttsLocaleMap[msg.detected_language] || 'en-US'}
            />
          </div>
        )}

        {/* User Quality Feedback Widget */}
        {!isUser && msg.query_id && isGrounded && (
          <FeedbackWidget queryId={msg.query_id} />
        )}

        {/* Message Timestamp */}
        <div className="flex items-center justify-between text-[10px] text-gray-400/80 pt-0.5">
          <span>{msg.timestamp}</span>
        </div>
      </div>

      {isUser && (
        <div className="flex flex-col items-center gap-1">
          <div className="w-8 h-8 rounded-xl bg-surface-card border border-surface-border flex items-center justify-center text-gray-300 shrink-0">
            <User size={16} />
          </div>
          {msg.inputMode === 'voice' && (
            <span
              title="Sent via voice input"
              className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-[10px]"
            >
              <Mic size={10} />
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default React.memo(ChatMessageItem);
