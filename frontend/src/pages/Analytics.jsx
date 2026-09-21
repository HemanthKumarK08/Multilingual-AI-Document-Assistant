import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  RefreshCw,
  Clock,
  ArrowLeft,
  AlertCircle,
  Database,
  Flame,
  CheckCircle2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';

import AnalyticsKPIs from '../components/analytics/AnalyticsKPIs';
import QueryVolumeChart from '../components/analytics/QueryVolumeChart';
import LanguageDistributionChart from '../components/analytics/LanguageDistributionChart';
import RetrievalPerformancePanel from '../components/analytics/RetrievalPerformancePanel';
import RagPerformancePanel from '../components/analytics/RagPerformancePanel';
import ErrorReliabilityPanel from '../components/analytics/ErrorReliabilityPanel';
import PrivacyArchitectureNotice from '../components/analytics/PrivacyArchitectureNotice';

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [globalError, setGlobalError] = useState(null);

  // Endpoint states
  const [data, setData] = useState({
    health: null,
    summary: null,
    volume: null,
    languages: null,
    retrieval: null,
    rag: null,
    errors: null,
    timeseries: null,
  });

  const [errors, setErrors] = useState({
    health: null,
    summary: null,
    volume: null,
    languages: null,
    retrieval: null,
    rag: null,
    errors: null,
    timeseries: null,
  });

  const fetchAnalytics = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setGlobalError(null);

    try {
      const results = await Promise.allSettled([
        apiService.getAnalyticsHealth(),
        apiService.getAnalyticsSummary(),
        apiService.getAnalyticsVolume(),
        apiService.getAnalyticsLanguages(),
        apiService.getAnalyticsRetrieval(),
        apiService.getAnalyticsRag(),
        apiService.getAnalyticsErrors(),
        apiService.getAnalyticsTimeseries(),
      ]);

      const [
        healthRes,
        summaryRes,
        volumeRes,
        languagesRes,
        retrievalRes,
        ragRes,
        errorsRes,
        timeseriesRes,
      ] = results;

      const newData = {
        health: healthRes.status === 'fulfilled' ? healthRes.value : null,
        summary: summaryRes.status === 'fulfilled' ? summaryRes.value : null,
        volume: volumeRes.status === 'fulfilled' ? volumeRes.value : null,
        languages: languagesRes.status === 'fulfilled' ? languagesRes.value : null,
        retrieval: retrievalRes.status === 'fulfilled' ? retrievalRes.value : null,
        rag: ragRes.status === 'fulfilled' ? ragRes.value : null,
        errors: errorsRes.status === 'fulfilled' ? errorsRes.value : null,
        timeseries: timeseriesRes.status === 'fulfilled' ? timeseriesRes.value : null,
      };

      const newErrors = {
        health: healthRes.status === 'rejected' ? healthRes.reason?.message : null,
        summary: summaryRes.status === 'rejected' ? summaryRes.reason?.message : null,
        volume: volumeRes.status === 'rejected' ? volumeRes.reason?.message : null,
        languages: languagesRes.status === 'rejected' ? languagesRes.reason?.message : null,
        retrieval: retrievalRes.status === 'rejected' ? retrievalRes.reason?.message : null,
        rag: ragRes.status === 'rejected' ? ragRes.reason?.message : null,
        errors: errorsRes.status === 'rejected' ? errorsRes.reason?.message : null,
        timeseries: timeseriesRes.status === 'rejected' ? timeseriesRes.reason?.message : null,
      };

      setData(newData);
      setErrors(newErrors);
      setLastRefreshed(new Date());

      // If all endpoints failed
      const allFailed = results.every((r) => r.status === 'rejected');
      if (allFailed) {
        setGlobalError('The analytics service is currently unreachable. Please ensure the backend server is running.');
      }
    } catch (err) {
      setGlobalError(err.message || 'An unexpected error occurred while loading analytics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-brand-400 mb-1">
            <BarChart3 size={14} />
            <span>Big Data Engine • Phase 8.5</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Big Data Analytics Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Privacy-preserving usage, multilingual distributions, and PySpark batch performance insights.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          {lastRefreshed && (
            <span className="text-xs text-gray-400 hidden md:inline-block">
              Refreshed: {lastRefreshed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => fetchAnalytics(true)}
            disabled={loading || refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-medium text-gray-200 hover:text-white transition disabled:opacity-50 shadow-sm"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin text-brand-400' : ''} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Analytics'}</span>
          </button>
          <Link
            to="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-medium text-gray-300 hover:text-white transition shadow-sm"
          >
            <ArrowLeft size={13} />
            <span>Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Global Error Banner */}
      {globalError && (
        <div className="p-5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-red-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-white">Unable to Load Analytics</h3>
              <p className="text-xs text-red-300/90 mt-1">{globalError}</p>
            </div>
          </div>
          <button
            onClick={() => fetchAnalytics(true)}
            className="px-3 py-1.5 text-xs rounded-xl bg-red-500/20 hover:bg-red-500/30 text-white font-medium transition shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Section */}
      <AnalyticsKPIs
        summary={data.summary}
        loading={loading}
        error={errors.summary}
        onRetry={() => fetchAnalytics(true)}
      />

      {/* Primary Visualizations Grid: Query Volume & Multilingual Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <QueryVolumeChart
          timeseries={data.timeseries}
          volume={data.volume}
          loading={loading}
          error={errors.timeseries || errors.volume}
          onRetry={() => fetchAnalytics(true)}
        />
        <LanguageDistributionChart
          languages={data.languages}
          loading={loading}
          error={errors.languages}
          onRetry={() => fetchAnalytics(true)}
        />
      </div>

      {/* Secondary Visualizations Grid: Retrieval & RAG Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <RetrievalPerformancePanel
          retrieval={data.retrieval}
          loading={loading}
          error={errors.retrieval}
          onRetry={() => fetchAnalytics(true)}
        />
        <RagPerformancePanel
          rag={data.rag}
          loading={loading}
          error={errors.rag}
          onRetry={() => fetchAnalytics(true)}
        />
      </div>

      {/* System Errors & Reliability */}
      <ErrorReliabilityPanel
        errors={data.errors}
        loading={loading}
        error={errors.errors}
        onRetry={() => fetchAnalytics(true)}
      />

      {/* Privacy & Big Data Architecture Section */}
      <PrivacyArchitectureNotice
        generatedAt={data.summary?.generated_at_utc}
        recordCount={data.summary?.source_record_count}
      />
    </div>
  );
}
