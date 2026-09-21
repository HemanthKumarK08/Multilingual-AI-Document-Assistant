import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Cpu, Activity, Clock, Globe } from 'lucide-react';

const LANGUAGE_LABELS = {
  en: 'English (en)',
  hi: 'हिन्दी / Hindi (hi)',
  kn: 'ಕನ್ನಡ / Kannada (kn)',
  te: 'తెలుగు / Telugu (te)',
};

export default function TechnicalDetailsPanel({ msg }) {
  const [open, setOpen] = useState(false);

  if (!msg) return null;

  const langLabel = LANGUAGE_LABELS[msg.detected_language] || msg.detected_language || 'English (en)';

  return (
    <div className="pt-2 text-[11px] border-t border-surface-border/40">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-gray-400 hover:text-gray-200 font-mono transition py-0.5"
      >
        <Terminal size={12} className="text-brand-400" />
        <span>Technical details</span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <div className="mt-2 p-3 rounded-xl bg-surface-base/80 border border-surface-border/60 font-mono text-[10px] space-y-1.5 text-gray-300 animate-fadeIn">
          <div className="flex justify-between">
            <span className="text-gray-500">Query ID:</span>
            <span className="text-gray-200 select-all">{msg.query_id || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Detected Language:</span>
            <span className="text-indigo-300">{langLabel}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">RAG Answer Mode:</span>
            <span className={msg.is_fallback ? 'text-amber-400' : 'text-emerald-400'}>
              {msg.is_fallback ? 'Fallback / Insufficient Evidence' : 'Grounded in Documents'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Retrieval Latency:</span>
            <span>{msg.retrieval_latency_ms ? `${Math.round(msg.retrieval_latency_ms)} ms` : 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Generation Latency:</span>
            <span>{msg.generation_latency_ms ? `${Math.round(msg.generation_latency_ms)} ms` : 'N/A'}</span>
          </div>
          <div className="flex justify-between border-t border-surface-border/40 pt-1">
            <span className="text-gray-400 font-bold">Total Execution Latency:</span>
            <span className="text-brand-400 font-bold">
              {msg.total_latency_ms ? `${Math.round(msg.total_latency_ms)} ms` : 'N/A'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
