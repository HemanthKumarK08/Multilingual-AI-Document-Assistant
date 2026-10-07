import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { Calendar, TrendingUp } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 border border-slate-750 rounded-xl p-3 shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-200 mb-1.5 border-b border-slate-800 pb-1 flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          {label}
        </p>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Queries:</span>
          <span className="font-mono font-bold text-indigo-300">
            {typeof payload[0].value === 'number' ? payload[0].value.toLocaleString() : payload[0].value}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

export default function UserActivityTrendsChart({ timeseries }) {
  const dailyData = timeseries?.daily_trends || timeseries?.daily_trend || [];

  const chartData = useMemo(() => {
    const arr = Array.isArray(dailyData) ? dailyData : [];
    return arr.map(d => ({
      date: d.date,
      queries: d.queries ?? (d.query_count || 0)
    }));
  }, [dailyData]);

  const totalPeriodQueries = chartData.reduce((acc, curr) => acc + curr.queries, 0);

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Query Activity</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Daily query volume tracked across operational partitions
          </p>
        </div>
        <div className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700 self-start sm:self-auto">
          {totalPeriodQueries.toLocaleString()} Total Queries in Period
        </div>
      </div>

      <div className="h-60 w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs">
            No temporal activity recorded for the selected dataset.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorQueriesOnly" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="queries"
                name="Queries"
                stroke="#6366f1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorQueriesOnly)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
