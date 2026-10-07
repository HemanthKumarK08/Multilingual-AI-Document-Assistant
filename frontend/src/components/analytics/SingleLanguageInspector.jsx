import React, { useState } from 'react';
import {
  Globe2,
  Search,
  Database,
  Cpu,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Zap,
  Users
} from 'lucide-react';

export default function SingleLanguageInspector({ languagePerf, codeMixed }) {
  const languages = languagePerf?.languages || [];
  const [selectedLangCode, setSelectedLangCode] = useState(languages[0]?.language || 'kn');

  const selectedData = languages.find(l => l.language === selectedLangCode) || languages[0];

  if (!selectedData) {
    return null;
  }

  return (
    <div className="bg-slate-850/80 border border-slate-750/70 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
      {/* Header & Language Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-750">
        <div>
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-sky-400" />
            <h2 className="text-lg font-bold text-slate-100">Deep Single-Language Inspector</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluate end-to-end RAG retrieval, generation, grounding, and script handling for any specific language
          </p>
        </div>

        {/* Dropdown Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="lang-select" className="text-xs font-medium text-slate-400">
            Select Language:
          </label>
          <select
            id="lang-select"
            value={selectedLangCode}
            onChange={(e) => setSelectedLangCode(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs font-semibold rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
          >
            {languages.map((l) => (
              <option key={l.language} value={l.language}>
                {l.label || l.language} ({l.query_count?.toLocaleString()} queries)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Language Overview Grid */}
      <div className="space-y-6">
        {/* Section A: Overview Bar */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Globe2 className="w-4 h-4 text-indigo-400" />
              Language Overview: {selectedData.label || selectedData.language}
            </h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {selectedData.percentage?.toFixed(1)}% of total system volume
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Total Queries</span>
              <span className="text-lg font-bold font-mono text-slate-100 mt-0.5 block">
                {selectedData.query_count?.toLocaleString() || 0}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Unique Users</span>
              <span className="text-lg font-bold font-mono text-sky-400 mt-0.5 block">
                {selectedData.unique_users ?? 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Avg Queries / User</span>
              <span className="text-lg font-bold font-mono text-amber-400 mt-0.5 block">
                {selectedData.avg_queries_per_user != null ? selectedData.avg_queries_per_user.toFixed(1) : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Grounded Rate</span>
              <span className="text-lg font-bold font-mono text-emerald-400 mt-0.5 block">
                {selectedData.grounded_rate != null ? `${selectedData.grounded_rate.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Citation Validity</span>
              <span className="text-lg font-bold font-mono text-teal-400 mt-0.5 block">
                {selectedData.citation_validity_rate != null ? `${selectedData.citation_validity_rate.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Fallback Rate</span>
              <span className="text-lg font-bold font-mono text-rose-400 mt-0.5 block">
                {selectedData.fallback_rate != null ? `${selectedData.fallback_rate.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Avg Latency</span>
              <span className="text-lg font-bold font-mono text-slate-200 mt-0.5 block">
                {selectedData.avg_latency_ms != null ? `${Math.round(selectedData.avg_latency_ms)} ms` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Section B: 3 Pillars (Retrieval, Generation, Language Handling) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Pillar 1: Retrieval */}
          <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs uppercase tracking-wider pb-2 border-b border-slate-800">
              <Database className="w-4 h-4" />
              1. Retrieval Quality
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Avg Retrieved Chunks:</span>
                <span className="font-mono font-bold text-slate-200">{selectedData.avg_retrieved_chunks?.toFixed(1) || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Avg Candidate Pool:</span>
                <span className="font-mono font-bold text-slate-200">{selectedData.avg_candidates?.toFixed(1) || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Avg Best Match Score:</span>
                <span className="font-mono font-bold text-emerald-400">{selectedData.avg_best_score?.toFixed(4) || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Retrieval Latency:</span>
                <span className="font-mono font-bold text-slate-200">{selectedData.avg_retrieval_latency_ms?.toFixed(1) || 'N/A'} ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Reranking Latency:</span>
                <span className="font-mono font-bold text-slate-200">{selectedData.avg_reranking_latency_ms?.toFixed(1) || 'N/A'} ms</span>
              </div>
            </div>
          </div>

          {/* Pillar 2: Generation */}
          <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider pb-2 border-b border-slate-800">
              <Cpu className="w-4 h-4" />
              2. Generation & Providers
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Generation Latency:</span>
                <span className="font-mono font-bold text-slate-200">{selectedData.avg_generation_latency_ms?.toFixed(1) || 'N/A'} ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">P95 End-to-End Latency:</span>
                <span className="font-mono font-bold text-amber-400">{selectedData.p95_latency_ms ? `${Math.round(selectedData.p95_latency_ms)} ms` : 'N/A'}</span>
              </div>
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-slate-400 text-[11px] block mb-1.5 font-medium">Provider Cascade Breakdown:</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedData.provider_distribution && Object.entries(selectedData.provider_distribution).map(([prov, cnt]) => (
                    <span
                      key={prov}
                      className="px-2 py-0.5 rounded bg-slate-800 text-[11px] font-mono text-slate-300 border border-slate-700"
                    >
                      {prov}: <strong className="text-indigo-300">{cnt}</strong>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Pillar 3: Language Handling */}
          <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider pb-2 border-b border-slate-800">
              <Layers className="w-4 h-4" />
              3. Script & Linguistic Handling
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Native Script Distribution:</span>
                <span className="font-mono font-bold text-emerald-400">
                  {selectedData.script_distribution
                    ? Object.entries(selectedData.script_distribution)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(', ')
                    : 'Standard'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Primary Script Purity:</span>
                <span className="font-mono font-bold text-teal-400">
                  {selectedData.script_distribution
                    ? `${(
                        (Math.max(...Object.values(selectedData.script_distribution)) /
                          (selectedData.query_count || 1)) *
                        100
                      ).toFixed(1)}%`
                    : '100%'}
                </span>
              </div>
              <div className="pt-2 border-t border-slate-800/80">
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Queries are normalized through the multilingual canonicalizer, ensuring high-recall hybrid BM25 + Dense vector matching regardless of diacritics.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
