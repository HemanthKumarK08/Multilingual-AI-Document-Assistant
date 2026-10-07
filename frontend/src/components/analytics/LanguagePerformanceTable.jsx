import React, { useState, useMemo } from 'react';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ShieldCheck
} from 'lucide-react';

export default function LanguagePerformanceTable({ languagePerf }) {
  const [sortKey, setSortKey] = useState('queries');
  const [sortDir, setSortDir] = useState('desc'); // 'asc' | 'desc'

  const rawLanguages = Array.isArray(languagePerf?.languages) ? languagePerf.languages : [];

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sortedData = useMemo(() => {
    const list = rawLanguages.map(item => {
      const qCount = item.query_count ?? item.total_queries ?? 0;
      const grounded = item.grounded_rate ?? 0;
      const latencyMs = item.avg_total_latency_ms ?? item.avg_latency_ms ?? 0;
      return {
        code: item.language,
        name: item.label || item.language_name || item.language,
        queries: qCount,
        groundedRate: grounded,
        latencyMs: latencyMs,
        avgResponseStr: latencyMs >= 1000 ? `${(latencyMs / 1000).toFixed(2)} s` : `${Math.round(latencyMs)} ms`
      };
    });

    return list.sort((a, b) => {
      let valA = a[sortKey];
      let valB = b[sortKey];

      if (valA == null) valA = 0;
      if (valB == null) valB = 0;

      if (typeof valA === 'string') {
        return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortDir === 'asc' ? valA - valB : valB - valA;
    });
  }, [rawLanguages, sortKey, sortDir]);

  const renderSortIcon = (key) => {
    if (sortKey !== key) {
      return <ArrowUpDown className="w-3.5 h-3.5 opacity-40 ml-1 inline" />;
    }
    return sortDir === 'asc' ? (
      <ArrowUp className="w-3.5 h-3.5 text-indigo-400 ml-1 inline" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-indigo-400 ml-1 inline" />
    );
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-slate-100">Language Performance</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Answer grounding quality and response speed evaluated across languages
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 text-[11px] uppercase font-semibold border-b border-slate-800">
            <tr>
              <th
                onClick={() => handleSort('name')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200 transition-colors"
              >
                Language {renderSortIcon('name')}
              </th>
              <th
                onClick={() => handleSort('queries')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200 text-right transition-colors"
              >
                Queries {renderSortIcon('queries')}
              </th>
              <th
                onClick={() => handleSort('groundedRate')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200 text-right transition-colors"
              >
                Grounded Rate {renderSortIcon('groundedRate')}
              </th>
              <th
                onClick={() => handleSort('latencyMs')}
                className="py-3 px-4 cursor-pointer hover:text-slate-200 text-right transition-colors"
              >
                Avg Response {renderSortIcon('latencyMs')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 bg-slate-900/40">
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-slate-500">
                  No language performance metrics recorded yet.
                </td>
              </tr>
            ) : (
              sortedData.map((row) => (
                <tr key={row.code} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-200 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-400" />
                    {row.name}
                    <span className="text-[10px] font-mono text-slate-500 uppercase">({row.code})</span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-medium text-slate-100">
                    {row.queries.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-400">
                    {row.groundedRate.toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">
                    {row.avgResponseStr}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
