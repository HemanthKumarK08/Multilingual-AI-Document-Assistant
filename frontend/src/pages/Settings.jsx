import React from 'react';
import {
  Settings as SettingsIcon,
  Terminal,
  FileCode,
  Activity,
  ExternalLink,
  ShieldCheck,
  Server,
  Code2,
  Layers,
  ArrowLeft,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Settings() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fadeIn">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
            <SettingsIcon size={14} />
            <span>Configuration & Diagnostics</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Settings & Developer Tools
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            System diagnostics, API contracts, and architecture specifications.
          </p>
        </div>
        <Link
          to="/"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-medium text-gray-300 hover:text-white transition"
        >
          <ArrowLeft size={14} />
          <span>Dashboard</span>
        </Link>
      </div>

      {/* Developer API Documentation Links */}
      <div className="rounded-2xl bg-surface-card border border-surface-border p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Terminal size={18} className="text-brand-400" />
          <span>Backend API Specifications</span>
        </h2>
        <p className="text-xs text-gray-400">
          FastAPI provides interactive OpenAPI Swagger documentation and ReDoc specifications out-of-the-box.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="p-4 rounded-xl bg-surface-base/60 hover:bg-surface-base border border-surface-border/60 hover:border-brand-500/40 transition group flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400">
                <Terminal size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-brand-300 transition">
                  Swagger UI
                </p>
                <p className="text-[11px] text-gray-400">Interactive REST documentation (/docs)</p>
              </div>
            </div>
            <ExternalLink size={16} className="text-gray-500 group-hover:text-brand-400 transition" />
          </a>

          <a
            href="/redoc"
            target="_blank"
            rel="noreferrer"
            className="p-4 rounded-xl bg-surface-base/60 hover:bg-surface-base border border-surface-border/60 hover:border-indigo-500/40 transition group flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <FileCode size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-indigo-300 transition">
                  ReDoc API
                </p>
                <p className="text-[11px] text-gray-400">Structured OpenAPI reference (/redoc)</p>
              </div>
            </div>
            <ExternalLink size={16} className="text-gray-500 group-hover:text-indigo-400 transition" />
          </a>
        </div>
      </div>

      {/* System Specifications */}
      <div className="rounded-2xl bg-surface-card border border-surface-border p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Layers size={18} className="text-emerald-400" />
          <span>Architecture Specifications</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-surface-base/50 border border-surface-border/50 space-y-1">
            <span className="text-gray-400 font-medium">Embedding Model</span>
            <p className="text-white font-mono font-semibold">intfloat/multilingual-e5-small (384-dim)</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-base/50 border border-surface-border/50 space-y-1">
            <span className="text-gray-400 font-medium">Vector Store</span>
            <p className="text-white font-mono font-semibold">ChromaDB Persistent (document_chunks)</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-base/50 border border-surface-border/50 space-y-1">
            <span className="text-gray-400 font-medium">Hybrid Fusion</span>
            <p className="text-white font-mono font-semibold">Dense Vector + Unicode BM25 Lexical</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-base/50 border border-surface-border/50 space-y-1">
            <span className="text-gray-400 font-medium">Big Data Engine</span>
            <p className="text-white font-mono font-semibold">Apache PySpark 3.5.3 (Parquet Lake)</p>
          </div>
        </div>
      </div>

      {/* Privacy Policy Guarantee */}
      <div className="rounded-2xl bg-surface-card border border-surface-border p-6 shadow-xl flex items-start gap-4">
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
          <ShieldCheck size={22} />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-white">
            Privacy-by-Design Compliance
          </h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            All system telemetry is strictly privacy-preserving. User query text, prompt templates, generated responses, and document texts are excluded from telemetry payloads. Only token lengths, language codes, latencies, and metadata aggregations are retained for PySpark processing.
          </p>
        </div>
      </div>
    </div>
  );
}
