import React from 'react';
import {
  MessageSquare,
  Users,
  ShieldCheck,
  Clock
} from 'lucide-react';

export default function UserExecutiveKPIs({ summary, users, languagePerf }) {
  const totalQueries = summary?.total_queries_analyzed ?? summary?.total_queries ?? 0;
  const totalUsers = users?.total_unique_users ?? summary?.total_users ?? summary?.unique_users_count ?? 0;

  const groundedRateVal = summary?.grounded_answer_rate_pct ?? summary?.grounded_answer_rate;
  const groundedRate = groundedRateVal != null ? `${groundedRateVal.toFixed(1)}%` : '0.0%';

  const latencyRawMs = summary?.avg_total_latency_ms ?? summary?.avg_retrieval_latency_ms ?? 0;
  const avgResponseTime = latencyRawMs > 0 
    ? (latencyRawMs >= 1000 ? `${(latencyRawMs / 1000).toFixed(2)} s` : `${Math.round(latencyRawMs)} ms`)
    : '0.00 s';

  const cards = [
    {
      title: 'Total Queries',
      value: totalQueries.toLocaleString(),
      subtext: 'Processed questions & requests',
      icon: MessageSquare,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10 border-indigo-500/20',
      badge: 'Activity'
    },
    {
      title: 'Anonymous Users',
      value: totalUsers.toLocaleString(),
      subtext: 'Privacy-safe unique sessions',
      icon: Users,
      color: 'text-sky-400',
      bgColor: 'bg-sky-500/10 border-sky-500/20',
      badge: 'Audience'
    },
    {
      title: 'Grounded Answers',
      value: groundedRate,
      subtext: 'Verified against document context',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/20',
      badge: 'Precision'
    },
    {
      title: 'Avg Response Time',
      value: avgResponseTime,
      subtext: 'End-to-end pipeline latency',
      icon: Clock,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/20',
      badge: 'Speed'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-5 rounded-2xl border backdrop-blur-md transition-all duration-200 hover:border-slate-700 bg-slate-900/70 border-slate-800 shadow-sm`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400">{card.title}</span>
              <div className={`p-2 rounded-xl ${card.bgColor} ${card.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 my-1">
              <span className={`text-2xl sm:text-3xl font-black tracking-tight ${card.color}`}>
                {card.value}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 truncate">
              {card.subtext}
            </p>
          </div>
        );
      })}
    </div>
  );
}
