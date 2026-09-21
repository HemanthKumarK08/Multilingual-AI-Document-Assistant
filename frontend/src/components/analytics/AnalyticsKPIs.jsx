import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, FileCheck2, Clock, Sparkles, AlertCircle } from 'lucide-react';

export default function AnalyticsKPIs({ summary, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="p-4 rounded-xl bg-surface-card/60 border border-surface-border animate-pulse space-y-2">
            <div className="h-3 w-16 bg-surface-border rounded"></div>
            <div className="h-7 w-20 bg-surface-border rounded"></div>
            <div className="h-2.5 w-12 bg-surface-border rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <AlertCircle size={16} />
          <span>Failed to load summary KPIs: {error}</span>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-2.5 py-1 text-xs rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 font-medium transition"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!summary) return null;

  const kpis = [
    {
      label: 'Total Events',
      value: summary.source_record_count?.toLocaleString() || summary.total_queries?.toLocaleString() || '0',
      sublabel: 'Telemetry records',
      icon: Activity,
      color: 'text-brand-400',
      bg: 'bg-brand-500/10',
      border: 'border-brand-500/20',
    },
    {
      label: 'Grounded Rate',
      value: summary.grounded_answer_rate != null ? `${summary.grounded_answer_rate.toFixed(1)}%` : 'N/A',
      sublabel: 'Supported by docs',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
    },
    {
      label: 'Fallback Rate',
      value: summary.fallback_rate != null ? `${summary.fallback_rate.toFixed(1)}%` : 'N/A',
      sublabel: 'Insufficient evidence',
      icon: AlertTriangle,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
    },
    {
      label: 'Citation Validity',
      value: summary.citation_validity_rate != null ? `${summary.citation_validity_rate.toFixed(1)}%` : 'N/A',
      sublabel: 'Verified provenance',
      icon: FileCheck2,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
    },
    {
      label: 'Avg Total Latency',
      value: summary.avg_total_latency_ms != null ? `${summary.avg_total_latency_ms.toFixed(0)} ms` : 'N/A',
      sublabel: summary.p95_total_latency_ms != null ? `P95: ${summary.p95_total_latency_ms.toFixed(0)} ms` : 'End-to-end',
      icon: Clock,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
    },
    {
      label: 'Code-Mixed Share',
      value: summary.code_mixed_query_share != null ? `${summary.code_mixed_query_share.toFixed(1)}%` : 'N/A',
      sublabel: `${summary.languages_active || 4} active languages`,
      icon: Sparkles,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            className="p-4 rounded-xl bg-surface-card border border-surface-border shadow-sm flex flex-col justify-between hover:border-surface-border/80 transition group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">
                {kpi.label}
              </span>
              <div className={`p-1.5 rounded-lg ${kpi.bg} ${kpi.border} border ${kpi.color}`}>
                <Icon size={14} />
              </div>
            </div>
            <div>
              <div className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {kpi.value}
              </div>
              <div className="text-[11px] text-gray-400 mt-0.5 truncate">
                {kpi.sublabel}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
