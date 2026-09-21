import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { TrendingUp, Clock, AlertCircle } from 'lucide-react';

export default function QueryVolumeChart({ timeseries, volume, loading, error, onRetry }) {
  const [viewMode, setViewMode] = useState('daily'); // 'daily' | 'hourly'

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
        <p className="text-sm text-red-400">Failed to load query volume data: {error}</p>
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

  // Format Daily Trends
  const dailyData = timeseries?.daily_trends?.map((item) => ({
    date: item.date.slice(5), // 'MM-DD'
    fullDate: item.date,
    queries: item.queries || 0,
    grounded: Math.round((item.queries * (item.grounded_rate || 94)) / 100),
    fallback: Math.round((item.queries * (item.fallback_rate || 6)) / 100),
    latency: item.avg_latency_ms || 0,
  })) || [];

  // Format Hourly Distribution
  const hourlyRaw = timeseries?.hourly_distribution || volume?.events_by_hour || {};
  const hourlyData = Object.keys(hourlyRaw)
    .sort((a, b) => parseInt(a) - parseInt(b))
    .map((hour) => ({
      hour: `${hour.padStart(2, '0')}:00`,
      events: hourlyRaw[hour],
    }));

  const totalQueries = dailyData.reduce((acc, curr) => acc + curr.queries, 0);

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-brand-400" />
            <h3 className="text-base font-semibold text-white">Query Volume & Temporal Trends</h3>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">
            {viewMode === 'daily'
              ? `${totalQueries} total queries across active date partitions`
              : 'Diurnal query distribution by operational hour'}
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center bg-surface-base p-1 rounded-xl border border-surface-border text-xs font-medium self-start sm:self-auto">
          <button
            onClick={() => setViewMode('daily')}
            className={`px-3 py-1 rounded-lg transition ${
              viewMode === 'daily'
                ? 'bg-brand-500/20 text-brand-300 font-semibold shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Daily Trend (7d)
          </button>
          <button
            onClick={() => setViewMode('hourly')}
            className={`px-3 py-1 rounded-lg transition ${
              viewMode === 'hourly'
                ? 'bg-brand-500/20 text-brand-300 font-semibold shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Hourly Pattern
          </button>
        </div>
      </div>

      {/* Accessible Description for Screen Readers */}
      <div className="sr-only">
        {viewMode === 'daily'
          ? `Daily query volume chart showing ${dailyData.length} days with total ${totalQueries} queries.`
          : `Hourly query distribution chart covering ${hourlyData.length} active hours.`}
      </div>

      {/* Chart Area */}
      <div className="h-64 sm:h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          {viewMode === 'daily' ? (
            <AreaChart data={dailyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="groundedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="fallbackGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
              <XAxis dataKey="date" stroke="#737373" fontSize={11} tickLine={false} />
              <YAxis stroke="#737373" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#171717',
                  borderColor: '#262626',
                  borderRadius: '0.75rem',
                  color: '#fff',
                  fontSize: '12px',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Area
                type="monotone"
                dataKey="grounded"
                name="Grounded Queries"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#groundedGrad)"
              />
              <Area
                type="monotone"
                dataKey="fallback"
                name="Fallback Queries"
                stroke="#f59e0b"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#fallbackGrad)"
              />
            </AreaChart>
          ) : (
            <BarChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
              <XAxis dataKey="hour" stroke="#737373" fontSize={10} tickLine={false} />
              <YAxis stroke="#737373" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#171717',
                  borderColor: '#262626',
                  borderRadius: '0.75rem',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="events" name="Queries / Events" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
