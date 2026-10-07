import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { BarChart3, Clock, ShieldCheck, Zap } from 'lucide-react';

const CustomChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 border border-slate-700/80 rounded-lg p-3 shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-200 mb-2 border-b border-slate-700/60 pb-1">
          {label}
        </p>
        <div className="space-y-1">
          {payload.map((entry, index) => (
            <div key={`item-${index}`} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5" style={{ color: entry.color }}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></span>
                {entry.name}:
              </span>
              <span className="font-mono font-semibold text-slate-200">
                {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
                {entry.unit ? ` ${entry.unit}` : ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export default function LanguagePerformanceCharts({ languagePerf }) {
  const rawList = languagePerf?.languages || [];

  const chartData = rawList.map(item => ({
    name: item.label || item.language,
    code: item.language.toUpperCase(),
    grounded: item.grounded_rate != null ? Number(item.grounded_rate.toFixed(1)) : 0,
    citation: item.citation_validity_rate != null ? Number(item.citation_validity_rate.toFixed(1)) : 0,
    fallback: item.fallback_rate != null ? Number(item.fallback_rate.toFixed(1)) : 0,
    avgLatency: item.avg_latency_ms != null ? Math.round(item.avg_latency_ms) : 0,
    p95Latency: item.p95_latency_ms != null ? Math.round(item.p95_latency_ms) : 0,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Chart 1: Quality & Reliability Comparison */}
      <div className="bg-slate-850/80 border border-slate-750/70 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-100">Quality & Reliability by Language (%)</h3>
            <p className="text-[11px] text-slate-400">Grounded Rate vs Citation Validity vs Fallback Rate</p>
          </div>
        </div>

        <div className="h-64 w-full">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No language data available.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip content={<CustomChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} iconType="circle" />
                <Bar dataKey="grounded" name="Grounded %" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="citation" name="Citation Validity %" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fallback" name="Fallback %" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Chart 2: Latency Profile Comparison */}
      <div className="bg-slate-850/80 border border-slate-750/70 rounded-2xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-sky-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-100">Response Latency Profile by Language (ms)</h3>
            <p className="text-[11px] text-slate-400">Mean End-to-End Latency vs 95th Percentile Tail Latency</p>
          </div>
        </div>

        <div className="h-64 w-full">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No latency data available.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} iconType="circle" />
                <Bar dataKey="avgLatency" name="Avg Latency (ms)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="p95Latency" name="P95 Latency (ms)" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
