import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip
} from 'recharts';
import { Globe2 } from 'lucide-react';

const LANG_CONFIG = {
  en: { color: '#38bdf8', label: 'English', native: 'English' },
  hi: { color: '#fb923c', label: 'Hindi', native: 'हिन्दी' },
  kn: { color: '#a855f7', label: 'Kannada', native: 'ಕನ್ನಡ' },
  te: { color: '#34d399', label: 'Telugu', native: 'తెలుగు' },
  code_mixed: { color: '#f43f5e', label: 'Code-Mixed', native: 'Mixed' },
  other: { color: '#94a3b8', label: 'Other', native: 'Other' }
};

const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900/95 border border-slate-750 rounded-xl p-3 shadow-xl backdrop-blur-md text-xs">
        <div className="flex items-center gap-2 mb-1.5 border-b border-slate-800 pb-1">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: data.color }}></span>
          <span className="font-bold text-slate-200">{data.name}</span>
          <span className="text-slate-400 font-normal">({data.native})</span>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between gap-4">
            <span className="text-slate-400">Queries:</span>
            <span className="font-mono font-bold text-slate-100">{data.value.toLocaleString()}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-slate-400">Share:</span>
            <span className="font-mono font-bold text-indigo-400">{data.percentage.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function MultilingualUsagePanel({ languages, languagePerf }) {
  const langList = Array.isArray(languagePerf?.languages) 
    ? languagePerf.languages 
    : (Array.isArray(languages?.distribution) ? languages.distribution : []);
  
  const totalQueries = langList.reduce((acc, curr) => acc + (curr.query_count ?? curr.total_queries ?? 0), 0);

  const pieData = langList.map(item => {
    const code = (item.language || '').toLowerCase();
    const cfg = LANG_CONFIG[code] || LANG_CONFIG.other;
    const queryCount = item.query_count ?? item.total_queries ?? 0;
    const share = item.percentage ?? item.query_share_pct ?? (totalQueries > 0 ? (queryCount / totalQueries) * 100 : 0);
    return {
      name: item.label || item.language_name || cfg.label,
      native: cfg.native,
      code: code,
      value: queryCount,
      percentage: share,
      color: cfg.color
    };
  });

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Globe2 className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Language Usage</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Breakdown of questions asked across supported Indic languages and English
          </p>
        </div>
        <div className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700 self-start sm:self-auto">
          {pieData.filter(d => d.value > 0).length} Languages Active
        </div>
      </div>

      {totalQueries === 0 ? (
        <div className="py-10 text-center text-slate-500 text-xs">
          No language query activity recorded yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Donut Chart */}
          <div className="lg:col-span-5 h-56 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Clean Horizontal Language Share Rows */}
          <div className="lg:col-span-7 space-y-3">
            {pieData.map(lang => (
              <div
                key={lang.code}
                className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: lang.color }} />
                    <span className="text-sm font-semibold text-slate-200">{lang.name}</span>
                    <span className="text-xs text-slate-400">({lang.native})</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-bold font-mono text-slate-100">{lang.value.toLocaleString()}</span>
                    <span className="text-xs font-semibold text-slate-400">({lang.percentage.toFixed(1)}%)</span>
                  </div>
                </div>

                {/* Visual Progress Bar */}
                <div className="w-full bg-slate-800/60 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.max(lang.value > 0 ? 3 : 0, lang.percentage))}%`,
                      backgroundColor: lang.color
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
