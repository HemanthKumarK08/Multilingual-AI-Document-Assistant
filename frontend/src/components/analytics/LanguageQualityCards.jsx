import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  ShieldCheck,
  Zap,
  Globe2,
  FileCheck,
  AlertTriangle,
  Server
} from 'lucide-react';

const LANG_THEMES = {
  en: {
    border: 'border-sky-500/30 hover:border-sky-500/50',
    headerBg: 'bg-sky-500/10 text-sky-300',
    accent: 'text-sky-400',
    bar: 'bg-sky-500'
  },
  hi: {
    border: 'border-orange-500/30 hover:border-orange-500/50',
    headerBg: 'bg-orange-500/10 text-orange-300',
    accent: 'text-orange-400',
    bar: 'bg-orange-500'
  },
  kn: {
    border: 'border-purple-500/30 hover:border-purple-500/50',
    headerBg: 'bg-purple-500/10 text-purple-300',
    accent: 'text-purple-400',
    bar: 'bg-purple-500'
  },
  te: {
    border: 'border-emerald-500/30 hover:border-emerald-500/50',
    headerBg: 'bg-emerald-500/10 text-emerald-300',
    accent: 'text-emerald-400',
    bar: 'bg-emerald-500'
  }
};

export default function LanguageQualityCards({ languagePerf }) {
  const [expandedLang, setExpandedLang] = useState('kn'); // default Kannada expanded

  const languages = languagePerf?.languages || [];

  const toggleExpand = (code) => {
    setExpandedLang(prev => (prev === code ? null : code));
  };

  return (
    <div className="bg-slate-850/80 border border-slate-750/70 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-bold text-slate-100">Language Quality & System Deep-Dives</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Expandable diagnostics covering retrieval depth, LLM inference, script purity, and gating reliability
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {languages.map((item) => {
          const theme = LANG_THEMES[item.language] || LANG_THEMES.en;
          const isExpanded = expandedLang === item.language;

          return (
            <div
              key={item.language}
              className={`rounded-xl border bg-slate-900/60 transition-all duration-200 ${theme.border} overflow-hidden`}
            >
              {/* Card Header / Summary */}
              <div
                onClick={() => toggleExpand(item.language)}
                className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${theme.headerBg}`}>
                    <Globe2 className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-slate-200 text-sm">{item.label || item.language}</h3>
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {item.language}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {item.query_count?.toLocaleString()} queries ({item.percentage?.toFixed(1)}% volume)
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right hidden sm:block">
                    <span className="text-xs font-semibold text-emerald-400 block">
                      {item.grounded_rate != null ? `${item.grounded_rate.toFixed(0)}% Grounded` : 'N/A'}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {item.avg_latency_ms != null ? `${Math.round(item.avg_latency_ms)} ms` : 'N/A'}
                    </span>
                  </div>
                  <button className="text-slate-400 hover:text-slate-200 p-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Core Metric Bar */}
              <div className="grid grid-cols-4 border-t border-b border-slate-800 bg-slate-950/40 text-center py-2 px-3 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Grounded</span>
                  <span className="font-bold text-emerald-400">
                    {item.grounded_rate != null ? `${item.grounded_rate.toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Citation</span>
                  <span className="font-bold text-teal-400">
                    {item.citation_validity_rate != null ? `${item.citation_validity_rate.toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Fallback</span>
                  <span className="font-bold text-rose-400">
                    {item.fallback_rate != null ? `${item.fallback_rate.toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">P95 Latency</span>
                  <span className="font-bold text-slate-300">
                    {item.p95_latency_ms != null ? `${Math.round(item.p95_latency_ms)} ms` : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Expanded Diagnostic Details */}
              {isExpanded && (
                <div className="p-4 bg-slate-900/90 border-t border-slate-800 space-y-3.5 text-xs animate-in fade-in duration-150">
                  {/* Retrieval Section */}
                  <div>
                    <h4 className="font-semibold text-slate-300 text-[11px] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-sky-400" />
                      Retrieval Performance
                    </h4>
                    <div className="grid grid-cols-2 gap-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                      <div>
                        <span className="text-slate-400 text-[11px]">Avg Retrieved Chunks:</span>
                        <p className="font-mono font-semibold text-slate-200">
                          {item.avg_retrieved_chunks != null ? item.avg_retrieved_chunks.toFixed(1) : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px]">Avg Candidates:</span>
                        <p className="font-mono font-semibold text-slate-200">
                          {item.avg_candidates != null ? item.avg_candidates.toFixed(1) : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px]">Retrieval Latency:</span>
                        <p className="font-mono font-semibold text-slate-200">
                          {item.avg_retrieval_latency_ms != null ? `${item.avg_retrieval_latency_ms.toFixed(1)} ms` : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px]">Reranking Latency:</span>
                        <p className="font-mono font-semibold text-slate-200">
                          {item.avg_reranking_latency_ms != null ? `${item.avg_reranking_latency_ms.toFixed(1)} ms` : 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Generation & Provider Distribution */}
                  <div>
                    <h4 className="font-semibold text-slate-300 text-[11px] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Server className="w-3.5 h-3.5 text-indigo-400" />
                      Generation & Provider Distribution
                    </h4>
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 space-y-2">
                      <div className="flex justify-between items-center text-[11px]">
                        <span className="text-slate-400">Avg Generation Latency:</span>
                        <span className="font-mono font-semibold text-slate-200">
                          {item.avg_generation_latency_ms != null ? `${item.avg_generation_latency_ms.toFixed(1)} ms` : 'N/A'}
                        </span>
                      </div>
                      {item.provider_distribution && (
                        <div className="pt-1.5 border-t border-slate-800">
                          <span className="text-slate-400 text-[10px] block mb-1">Provider Executions:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {Object.entries(item.provider_distribution).map(([prov, count]) => (
                              <span
                                key={prov}
                                className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-300"
                              >
                                {prov}: <strong className="text-indigo-300">{count}</strong>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Script Breakdown */}
                  {item.script_distribution && (
                    <div>
                      <h4 className="font-semibold text-slate-300 text-[11px] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Script Purity & Encoding
                      </h4>
                      <div className="flex flex-wrap gap-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                        {Object.entries(item.script_distribution).map(([script, count]) => (
                          <div key={script} className="flex items-center gap-2">
                            <span className="text-slate-400 capitalize">{script}:</span>
                            <span className="font-mono font-semibold text-emerald-400">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
