import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  BotMessageSquare,
  Send,
  User,
  Sparkles,
  RotateCcw,
  Copy,
  Check,
  Globe,
  Layers,
  FileText,
  AlertCircle,
  ShieldCheck,
  Info,
  Loader2,
  Mic,
  Volume2,
} from 'lucide-react';
import { apiService } from '../services/api';
import MarkdownRenderer from '../components/MarkdownRenderer';
import CitationsSection from '../components/CitationsSection';
import TechnicalDetailsPanel from '../components/TechnicalDetailsPanel';
import FeedbackWidget from '../components/FeedbackWidget';
import SpeechRecognitionButton from '../components/voice/SpeechRecognitionButton';
import SpeakButton from '../components/voice/SpeakButton';
import { createTTSController, stopAllSpeech } from '../components/voice/textToSpeech';
import VoiceLanguageSelector, { getVoiceLanguageLabel } from '../components/voice/VoiceLanguageSelector';
import ErrorBoundary from '../components/ErrorBoundary';

export const LANGUAGE_DISPLAY_NAMES = {
  en: 'English',
  hi: 'हिन्दी',
  kn: 'ಕನ್ನಡ',
  te: 'తెలుగు',
};

const LANGUAGES = [
  { code: 'auto', label: 'Auto Detect' },
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
];

const CATEGORIES = [
  { value: 'all', label: 'All Documents' },
  { value: 'academic_regulations', label: 'Academic Regulations' },
  { value: 'examination_guidelines', label: 'Examination Guidelines' },
  { value: 'attendance', label: 'Attendance Policies' },
  { value: 'scholarships', label: 'Scholarships & Aid' },
  { value: 'hostel', label: 'Hostel & Housing' },
  { value: 'placements', label: 'Placements & Internships' },
];

const STARTER_PROMPTS = [
  {
    title: 'Attendance Policy',
    query: 'What is the minimum attendance required for semester examinations?',
    category: 'attendance',
    lang: 'en',
  },
  {
    title: 'Academic Regulations',
    query: 'Explain the credit framework and grading system for undergraduate programs.',
    category: 'academic_regulations',
    lang: 'en',
  },
  {
    title: 'ಹಾಜರಾತಿ ನಿಯಮಗಳು',
    query: 'ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಎಷ್ಟು ಶೇಕಡಾ ಹಾಜರಾತಿ ಬೇಕು?',
    category: 'attendance',
    lang: 'kn',
  },
  {
    title: 'उपस्थिति नियम',
    query: 'सेमेस्टर परीक्षा के लिए कितनी उपस्थिति अनिवार्य है?',
    category: 'attendance',
    lang: 'hi',
  },
];

// Map RAG language codes to BCP-47 TTS locales
const TTS_LOCALE_MAP = {
  en: 'en-US',
  hi: 'hi-IN',
  kn: 'kn-IN',
  te: 'te-IN',
};

/**
 * Authoritative Response State Derivation
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
 * Memoized Chat Message Item
 * Renders honest response states, prominent answer typography, and zero phantom citations.
 */
export const ChatMessageItem = React.memo(function ChatMessageItem({
  msg,
  idx,
  copiedIndex,
  copyToClipboard,
}) {
  const isUser = msg.role === 'user';
  const responseState = !isUser ? deriveResponseState(msg) : null;

  const isGrounded = responseState === 'GROUNDED';
  const isLanguageUnavailable = responseState === 'LANGUAGE_UNAVAILABLE';
  const isInsufficientEvidence = responseState === 'INSUFFICIENT_EVIDENCE';
  const isError = responseState === 'ERROR';

  const citationCount = Array.isArray(msg.citations) ? msg.citations.length : 0;
  const langLabel = LANGUAGE_DISPLAY_NAMES[msg.detected_language] || msg.detected_language || 'English';

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

            <button
              onClick={() => copyToClipboard(msg.content, idx)}
              className="inline-flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition py-0.5 px-1.5 rounded-md hover:bg-surface-base"
              title="Copy answer"
            >
              {copiedIndex === idx ? (
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
              locale={TTS_LOCALE_MAP[msg.detected_language] || 'en-US'}
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
});

export default function AskAI() {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [voiceLanguage, setVoiceLanguage] = useState('en');
  const [voiceActive, setVoiceActive] = useState(false);
  const [voiceResponseEnabled, setVoiceResponseEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [docCount, setDocCount] = useState(null);

  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const inputModeRef = useRef('typed');
  const isSubmittingRef = useRef(false);
  const isMountedRef = useRef(true);
  const isNearBottomRef = useRef(true);
  const prevMessageCountRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    async function checkDocs() {
      try {
        const docs = await apiService.getDocuments();
        if (isMountedRef.current) {
          setDocCount(Array.isArray(docs) ? docs.length : 0);
        }
      } catch (err) {
        if (isMountedRef.current) {
          setDocCount(0);
        }
      }
    }
    checkDocs();
    return () => {
      isMountedRef.current = false;
      stopAllSpeech();
    };
  }, []);

  const handleChatScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 120;
  };

  useEffect(() => {
    if (!chatContainerRef.current) return;
    const count = messages.length;
    if (count > prevMessageCountRef.current) {
      const lastMsg = messages[count - 1];
      if (lastMsg?.role === 'user' || isNearBottomRef.current) {
        chatContainerRef.current.scrollTo({
          top: chatContainerRef.current.scrollHeight,
          behavior: 'smooth',
        });
        isNearBottomRef.current = true;
      }
    }
    prevMessageCountRef.current = count;
  }, [messages]);

  async function handleSend(queryToSend = null, langOverride = null, catOverride = null) {
    const text = (queryToSend !== null ? queryToSend : inputQuery).trim();
    if (!text || loading) return;
    if (isSubmittingRef.current) return;

    isSubmittingRef.current = true;
    const submitMode = queryToSend !== null ? 'typed' : inputModeRef.current;
    const submitVoiceResponse = voiceResponseEnabled;
    inputModeRef.current = 'typed';

    setError(null);
    setInputQuery('');

    const userMsgId = 'user-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
    const userMsg = {
      id: userMsgId,
      role: 'user',
      content: text,
      inputMode: submitMode,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const targetLang = langOverride !== null
        ? (langOverride === 'auto' ? null : langOverride)
        : (selectedLanguage === 'auto' ? null : selectedLanguage);

      const categoryFilter = catOverride !== null
        ? (catOverride === 'all' ? null : catOverride)
        : (selectedCategory === 'all' ? null : selectedCategory);

      const res = await apiService.submitQuery(text, targetLang, categoryFilter);

      if (!isMountedRef.current) return;

      const assistantMsgId = 'assistant-' + (res.query_id || Date.now()) + '-' + Math.random().toString(36).substring(2, 7);
      const assistantMsg = {
        id: assistantMsgId,
        role: 'assistant',
        query_id: res.query_id,
        content: res.answer_text,
        is_fallback: res.is_fallback,
        grounded: res.grounded !== undefined ? res.grounded : !res.is_fallback,
        fallback_reason: res.fallback_reason,
        response_state: res.response_state || (
          (res.fallback_reason === 'MISSING_TARGET_SCRIPT' || res.fallback_reason === 'LANGUAGE_UNAVAILABLE' ||
           res.answer_text?.includes('सेवा वर्तमान में अनुपलब्ध') ||
           res.answer_text?.includes('ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ') ||
           res.answer_text?.includes('సేవ ప్రస్తుతం అందుబాటులో లేదు')) ? 'LANGUAGE_UNAVAILABLE' :
          res.is_fallback ? 'INSUFFICIENT_EVIDENCE' : 'GROUNDED'
        ),
        detected_language: res.detected_language,
        citations: res.citations || [],
        total_latency_ms: res.total_latency_ms,
        retrieval_latency_ms: res.retrieval_latency_ms,
        generation_latency_ms: res.generation_latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Automatic TTS only for strictly grounded answers when Voice Response is ON
      const isLanguageUnavailable = assistantMsg.response_state === 'LANGUAGE_UNAVAILABLE';
      const isInsufficientEvidence = assistantMsg.response_state === 'INSUFFICIENT_EVIDENCE';
      if (submitVoiceResponse && submitMode === 'voice' && !isLanguageUnavailable && !isInsufficientEvidence && res.answer_text) {
        stopAllSpeech();
        const langKey = (selectedLanguage !== 'auto' && selectedLanguage) || res.detected_language || 'en';
        const ttsLocale = TTS_LOCALE_MAP[langKey] || TTS_LOCALE_MAP[res.detected_language] || 'en-US';
        const autoTTS = createTTSController({
          text: res.answer_text,
          locale: ttsLocale,
        });
        autoTTS.speak();
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError({
          query: text,
          message: err.message || 'Unable to retrieve answer. Please verify backend service status.',
        });
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        isSubmittingRef.current = false;
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      } else {
        isSubmittingRef.current = false;
      }
    }
  }

  const handleVoiceTranscript = (transcript) => {
    if (!transcript) return;
    inputModeRef.current = 'voice';
    setInputQuery((prev) => {
      const trimmed = prev.trim();
      return trimmed ? (trimmed + " " + transcript) : transcript;
    });
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function clearConversation() {
    setMessages([]);
    setInputQuery('');
    setError(null);
    setVoiceActive(false);
    inputModeRef.current = 'typed';
    isSubmittingRef.current = false;
    isNearBottomRef.current = true;
    prevMessageCountRef.current = 0;
    stopAllSpeech();
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({ top: 0, behavior: 'auto' });
    }
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }

  const copyToClipboard = useCallback((text, idx) => {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  }, []);

  return (
    <ErrorBoundary onReset={clearConversation}>
      <div className="flex flex-col h-[calc(100vh-6.5rem)] max-w-5xl lg:max-w-6xl mx-auto w-full animate-fadeIn">
        {/* Top Controls Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3 mb-3 shrink-0">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-brand-400 mb-0.5">
              <BotMessageSquare size={14} />
              <span>AI Document Intelligence</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
              Ask AI
            </h1>
          </div>

          {/* Filters & Actions */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Response Language Selector */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-card border border-surface-border text-xs" title="RAG Response Language">
              <Globe size={13} className="text-indigo-400 shrink-0" />
              <span className="text-[11px] text-gray-400 font-medium hidden sm:inline">Response:</span>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                aria-label="Response Language"
                className="bg-transparent text-gray-200 text-xs font-medium focus:outline-none cursor-pointer"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code} className="bg-surface-card text-white">
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Document Scope Selector */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-card border border-surface-border text-xs" title="Filter Document Category Scope">
              <Layers size={13} className="text-brand-400 shrink-0" />
              <span className="text-[11px] text-gray-400 font-medium hidden sm:inline">Scope:</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                aria-label="Document Category Scope"
                className="bg-transparent text-gray-200 text-xs font-medium focus:outline-none cursor-pointer max-w-[130px] sm:max-w-none truncate"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value} className="bg-surface-card text-white">
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Voice Response Mode Toggle */}
            <button
              type="button"
              onClick={() => setVoiceResponseEnabled((prev) => !prev)}
              aria-label={voiceResponseEnabled ? 'Voice Response Mode enabled' : 'Voice Response Mode disabled'}
              aria-pressed={voiceResponseEnabled}
              title={voiceResponseEnabled ? 'Voice Response Mode is ON — Spoken queries will be answered with automatic voice speech' : 'Voice Response Mode is OFF — Spoken queries will return text only'}
              className={"inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-500/50 active:scale-95 " + (voiceResponseEnabled ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40 shadow-sm shadow-indigo-500/20" : "bg-surface-card hover:bg-surface-card/80 text-gray-400 hover:text-gray-200 border-surface-border")}
            >
              <Volume2 size={13} className={voiceResponseEnabled ? 'text-indigo-400' : 'text-gray-400'} />
              <span className="hidden sm:inline">Voice Response:</span>
              <span className={voiceResponseEnabled ? 'font-bold text-indigo-300' : 'text-gray-400'}>
                {voiceResponseEnabled ? 'On' : 'Off'}
              </span>
            </button>

            {/* Clear Chat Button */}
            {messages.length > 0 && (
              <button
                onClick={clearConversation}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-medium text-gray-300 hover:text-white transition shadow-sm"
                title="Start New Chat"
              >
                <RotateCcw size={13} />
                <span className="hidden sm:inline">New Chat</span>
              </button>
            )}
          </div>
        </div>

        {/* Main Conversation Thread */}
        <div
          ref={chatContainerRef}
          onScroll={handleChatScroll}
          className="flex-1 overflow-y-auto pr-1 space-y-4 scrollbar-thin min-h-0"
        >
          {docCount === 0 && (
            <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info size={16} className="text-amber-400 shrink-0" />
                <span>No documents currently indexed in knowledge base. Upload documents to enable grounded retrieval.</span>
              </div>
              <a
                href="/documents"
                className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-semibold transition"
              >
                Upload
              </a>
            </div>
          )}

          {messages.length === 0 ? (
            /* Empty Initial State with Starter Cards */
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-5">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600/30 to-brand-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shadow-2xl shadow-indigo-500/10">
                <Sparkles size={28} />
              </div>

              <div className="space-y-1.5 max-w-md">
                <h2 className="text-lg sm:text-xl font-bold text-white">
                  Ask questions about your indexed documents
                </h2>
                <p className="text-xs sm:text-sm text-gray-400 leading-relaxed">
                  Query institutional policies in English, हिन्दी, ಕನ್ನಡ, or తెలుగు with hybrid vector retrieval, transliteration normalization, and citation provenance.
                </p>
              </div>

              {/* Starter Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-3xl pt-1 text-left">
                {STARTER_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setSelectedCategory(prompt.category);
                      setSelectedLanguage(prompt.lang);
                      handleSend(prompt.query, prompt.lang, prompt.category);
                    }}
                    className="p-3.5 rounded-2xl bg-surface-card hover:bg-surface-card/80 border border-surface-border hover:border-indigo-500/40 text-left transition group shadow-md space-y-1"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-indigo-400">
                      <span>{prompt.title}</span>
                      <span className="uppercase text-[10px] text-gray-500">{prompt.lang}</span>
                    </div>
                    <p className="text-xs text-gray-300 group-hover:text-white transition leading-snug">
                      "{prompt.query}"
                    </p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message List */
            messages.map((msg, idx) => (
              <ChatMessageItem
                key={msg.id || idx}
                msg={msg}
                idx={idx}
                copiedIndex={copiedIndex}
                copyToClipboard={copyToClipboard}
              />
            ))
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3 sm:gap-3.5 items-start animate-fadeIn">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-brand-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20 mt-0.5">
                <Sparkles size={16} />
              </div>
              <div className="p-3.5 sm:p-4 rounded-2xl sm:rounded-3xl bg-surface-card border border-surface-border text-xs text-gray-300 flex items-center gap-3 shadow-lg">
                <Loader2 size={16} className="animate-spin text-indigo-400 shrink-0" />
                <div className="space-y-0.5">
                  <p className="font-semibold text-white">Searching indexed documents...</p>
                  <p className="text-[11px] text-gray-400">Executing hybrid retrieval and evidence gating</p>
                </div>
              </div>
            </div>
          )}

          {/* Error Banner with Retry */}
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between gap-3 animate-fadeIn">
              <div className="flex items-center gap-2">
                <Info size={16} className="text-rose-400 shrink-0" />
                <span>{error.message}</span>
              </div>
              {error.query && (
                <button
                  onClick={() => handleSend(error.query)}
                  className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold transition shrink-0"
                >
                  Retry
                </button>
              )}
            </div>
          )}
        </div>

        {/* Input Form Bar */}
        <div className="mt-2.5 pt-2.5 border-t border-surface-border shrink-0">
          <div className="relative rounded-2xl bg-surface-card border border-surface-border focus-within:border-brand-500 transition shadow-xl p-2 flex items-end gap-2">
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputQuery}
              onChange={(e) => {
                // Any manual edit resets inputMode to typed — edited text is always what gets submitted
                inputModeRef.current = 'typed';
                setInputQuery(e.target.value);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents (English, हिन्दी, ಕನ್ನಡ, తెలుగు)..."
              disabled={loading}
              className="flex-1 bg-transparent text-white placeholder-gray-500 text-xs sm:text-sm px-3 py-1.5 focus:outline-none resize-none disabled:opacity-50"
            />

            {/* Voice Language Selector */}
            <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-surface-base/60 border border-surface-border">
              <VoiceLanguageSelector
                value={voiceLanguage}
                onChange={(code) => setVoiceLanguage(code)}
                disabled={voiceActive || loading}
              />
              <SpeechRecognitionButton
                onTranscript={handleVoiceTranscript}
                language={voiceLanguage}
                languageLabel={getVoiceLanguageLabel(voiceLanguage)}
                onVoiceStateChange={(active) => {
                  if (active) {
                    stopAllSpeech();
                  }
                  setVoiceActive(active);
                }}
                disabled={loading}
              />
            </div>

            <button
              onClick={() => handleSend()}
              disabled={!inputQuery.trim() || loading}
              aria-label="Send Query"
              className="p-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:bg-surface-base text-white disabled:text-gray-500 font-semibold transition shadow-md shadow-brand-600/30 disabled:shadow-none active:scale-95 shrink-0"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>

          <div className="flex items-center justify-between px-2 pt-1.5 text-[10px] text-gray-500">
            <span>Press <strong>Enter</strong> to send • <strong>Shift + Enter</strong> for new line</span>
            <span>Zero-Raw-Data Privacy Active</span>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
