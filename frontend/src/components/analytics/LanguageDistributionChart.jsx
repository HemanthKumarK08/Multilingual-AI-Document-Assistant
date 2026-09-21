import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Globe2, Sparkles, Languages, AlertCircle } from 'lucide-react';

const LANGUAGE_META = {
  en: { name: 'English', native: 'English', color: '#6366f1' },
  hi: { name: 'Hindi', native: 'हिन्दी', color: '#f59e0b' },
  kn: { name: 'Kannada', native: 'ಕನ್ನಡ', color: '#10b981' },
  te: { name: 'Telugu', native: 'తెలుగు', color: '#06b6d4' },
  ta: { name: 'Tamil', native: 'தமிழ்', color: '#ec4899' },
  mr: { name: 'Marathi', native: 'मराठी', color: '#8b5cf6' },
};

const SCRIPT_COLORS = {
  latin: '#6366f1',
  devanagari: '#f59e0b',
  kannada: '#10b981',
  telugu: '#06b6d4',
};

export default function LanguageDistributionChart({ languages, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-surface-card border border-surface-border animate-pulse space-y-4 h-80">
        <div className="h-4 w-40 bg-surface-border rounded"></div>
        <div className="h-56 bg-surface-base/50 rounded-xl"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl bg-surface-card border border-surface-border flex flex-col justify-center items-center text-center h-80 space-y-3">
        <AlertCircle size={24} className="text-red-400" />
        <p className="text-sm text-red-400">Failed to load language metrics: {error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1.5 text-xs rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 font-medium transition"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  const langDist = languages?.language_distribution || {};
  const pieData = Object.keys(langDist).map((code) => {
    const meta = LANGUAGE_META[code] || { name: code.toUpperCase(), native: code, color: '#94a3b8' };
    const item = langDist[code];
    return {
      code,
      name: meta.name,
      native: meta.native,
      value: item.percentage || 0,
      count: item.count || 0,
      color: meta.color,
      avgLatency: item.avg_latency_ms || 0,
      fallbackRate: item.fallback_rate || 0,
    };
  }).sort((a, b) => b.value - a.value);

  const scripts = languages?.script_distribution || {};
  const totalQueries = languages?.total_queries_analyzed || 350;
  const codeMixedPct = languages?.code_mixed_percentage || 0;
  const codeMixedCount = languages?.code_mixed_queries_count || 0;

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe2 size={16} className="text-cyan-400" />
            <h3 className="text-base font-semibold text-white">Multilingual Distribution</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-medium">
            {pieData.length} Languages
          </span>
        </div>
        <p className="text-xs text-gray-400 mt-0.5">
          Query share by detected natural language and script
        </p>
      </div>

      {/* Screen Reader Summary */}
      <div className="sr-only">
        Language distribution: {pieData.map(d => `${d.name}: ${d.value.toFixed(1)}% (${d.count} queries)`).join(', ')}.
        Code-mixed queries: {codeMixedPct}% ({codeMixedCount} queries).
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
        {/* Donut Chart */}
        <div className="h-52 w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                paddingAngle={4}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="#171717" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name, item) => [`${value.toFixed(1)}% (${item.payload.count} queries)`, name]}
                contentStyle={{
                  backgroundColor: '#171717',
                  borderColor: '#262626',
                  borderRadius: '0.75rem',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Centered Stat */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-lg font-bold text-white">{totalQueries}</span>
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">Queries</span>
          </div>
        </div>

        {/* Legend List & Stats */}
        <div className="space-y-2">
          {pieData.map((item) => (
            <div key={item.code} className="flex items-center justify-between text-xs p-1.5 rounded-lg hover:bg-surface-base/50 transition">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="font-medium text-white">{item.name}</span>
                <span className="text-[11px] text-gray-400">({item.native})</span>
              </div>
              <div className="text-right">
                <span className="font-semibold text-gray-200">{item.value.toFixed(1)}%</span>
                <span className="text-[10px] text-gray-400 ml-1.5">({item.count})</span>
              </div>
            </div>
          ))}

          {/* Code-Mixed Badge */}
          <div className="mt-3 pt-3 border-t border-surface-border/60 flex items-center justify-between text-xs bg-brand-500/5 p-2 rounded-xl border border-brand-500/10">
            <div className="flex items-center gap-1.5 text-brand-300 font-medium">
              <Sparkles size={13} className="text-brand-400" />
              <span>Code-Mixed Queries</span>
            </div>
            <span className="font-bold text-brand-200">{codeMixedPct.toFixed(1)}% ({codeMixedCount})</span>
          </div>
        </div>
      </div>
    </div>
  );
}
