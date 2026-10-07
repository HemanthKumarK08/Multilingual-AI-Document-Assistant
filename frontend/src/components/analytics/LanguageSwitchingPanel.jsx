import React from 'react';
import { Shuffle, ArrowRight } from 'lucide-react';

const LANG_NAMES = {
  en: 'English',
  hi: 'Hindi',
  kn: 'Kannada',
  te: 'Telugu'
};

export default function LanguageSwitchingPanel({ switching }) {
  const transitions = Array.isArray(switching?.transitions) ? switching.transitions : [];
  const totalSwitches = switching?.total_switches_detected || 0;

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Shuffle className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-bold text-slate-100">Language Switching</h2>
        </div>
        <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
          {totalSwitches} Total Switches
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Inter-turn language transitions observed within conversational sessions
      </p>

      {totalSwitches === 0 || transitions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center py-8 text-center text-slate-500 text-xs">
          No language switching recorded yet.
        </div>
      ) : (
        <div className="space-y-2.5 flex-1">
          {transitions.map((item, idx) => {
            const srcLabel = item.source_label || LANG_NAMES[item.source] || item.source;
            const tgtLabel = item.target_label || LANG_NAMES[item.target] || item.target;
            const pct = totalSwitches > 0 ? ((item.count / totalSwitches) * 100).toFixed(0) : 0;
            return (
              <div
                key={idx}
                className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200 text-xs">{srcLabel}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span className="font-semibold text-indigo-300 text-xs">{tgtLabel}</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-mono font-bold text-sm text-slate-100">{item.count}</span>
                  <span className="text-[11px] text-slate-400">({pct}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
