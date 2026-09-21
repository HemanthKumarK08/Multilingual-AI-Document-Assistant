import React, { useEffect, useState } from 'react';
import { Server, Database, BrainCircuit, BarChart2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { apiService } from '../services/api';

export default function SystemStatus() {
  const [health, setHealth] = useState(null);
  const [analyticsHealth, setAnalyticsHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function fetchStatus() {
    setLoading(true);
    setError(null);
    try {
      const [hData, aData] = await Promise.all([
        apiService.getHealth().catch((err) => ({ status: 'error', error: err.message })),
        apiService.getAnalyticsHealth().catch((err) => ({ status: 'error', error: err.message })),
      ]);
      setHealth(hData);
      setAnalyticsHealth(aData);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStatus();
  }, []);

  const isBackendOk = health?.status === 'ok';
  const isDbOk = health?.database_status === 'connected';
  const isAiOk = health?.vector_store_configured === true;
  const isAnalyticsOk = analyticsHealth?.status === 'healthy' || analyticsHealth?.analytics_precomputed === true;

  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-5 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-surface-border pb-3">
        <div className="flex items-center gap-2">
          <Server size={18} className="text-brand-400" />
          <h2 className="text-sm font-bold text-white tracking-wide uppercase">
            System Live Diagnostics
          </h2>
        </div>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium text-gray-400 hover:text-white bg-surface-base/60 border border-surface-border hover:border-brand-500/30 transition disabled:opacity-50"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error ? (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle size={16} />
          <span>Backend unreachable: {error}. Ensure project backend is running.</span>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* 1. Backend */}
          <div className="p-3 rounded-xl bg-surface-base/50 border border-surface-border/60 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-[11px] text-gray-400 font-medium">Backend API</p>
              <p className="text-xs font-bold text-white">FastAPI</p>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendOk ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-rose-500'
                }`}
              />
              <span className={`text-xs font-semibold ${isBackendOk ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isBackendOk ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>

          {/* 2. Database */}
          <div className="p-3 rounded-xl bg-surface-base/50 border border-surface-border/60 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-[11px] text-gray-400 font-medium">Database</p>
              <p className="text-xs font-bold text-white">SQLite</p>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isDbOk ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-rose-500'
                }`}
              />
              <span className={`text-xs font-semibold ${isDbOk ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isDbOk ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* 3. AI / RAG Vector Store */}
          <div className="p-3 rounded-xl bg-surface-base/50 border border-surface-border/60 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-[11px] text-gray-400 font-medium">AI / Vector</p>
              <p className="text-xs font-bold text-white">ChromaDB</p>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isAiOk ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-rose-500'
                }`}
              />
              <span className={`text-xs font-semibold ${isAiOk ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isAiOk ? 'Ready' : 'Not Ready'}
              </span>
            </div>
          </div>

          {/* 4. Big Data Analytics */}
          <div className="p-3 rounded-xl bg-surface-base/50 border border-surface-border/60 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-[11px] text-gray-400 font-medium">Analytics</p>
              <p className="text-xs font-bold text-white">PySpark Lake</p>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isAnalyticsOk ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-amber-400'
                }`}
              />
              <span className={`text-xs font-semibold ${isAnalyticsOk ? 'text-emerald-400' : 'text-amber-400'}`}>
                {isAnalyticsOk ? 'Available' : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
