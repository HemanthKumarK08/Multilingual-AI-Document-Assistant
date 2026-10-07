import React from 'react';
import { Layers } from 'lucide-react';

export default function CodeMixedAnalysisPanel({ codeMixed }) {
  const romanizedCount = codeMixed?.romanized_count ?? 0;
  const codeMixedCount = codeMixed?.total_code_mixed_queries ?? codeMixed?.code_mixed_count ?? 0;
  const cmShare = codeMixed?.code_mixed_share_pct ?? codeMixed?.code_mixed_percentage ?? 0;
  const totalAnalyzed = codeMixed?.total_queries_analyzed ?? 0;

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-rose-400" />
          <h2 className="text-lg font-bold text-slate-100">Romanized & Code-Mixed Usage</h2>
        </div>
        <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-300">
          {cmShare.toFixed(1)}% Share
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        User queries written in Roman script transliterations or bilingual code-mixed patterns
      </p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Romanized Queries</span>
          <span className="text-2xl font-black font-mono text-indigo-300">
            {romanizedCount.toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">Indic in Latin script</span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Code-Mixed Queries</span>
          <span className="text-2xl font-black font-mono text-rose-300">
            {codeMixedCount.toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">Mixed vocabulary</span>
        </div>
      </div>

      <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-3 text-xs text-slate-400 mt-auto">
        <div className="flex justify-between items-center">
          <span>Total Multilingual Queries Analyzed:</span>
          <span className="font-mono font-bold text-slate-200">{totalAnalyzed.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
