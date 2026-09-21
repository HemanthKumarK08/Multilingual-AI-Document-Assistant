import React from 'react';
import { Link } from 'react-router-dom';
import {
  UploadCloud,
  BotMessageSquare,
  BarChart3,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  FileText,
} from 'lucide-react';
import SystemStatus from '../components/SystemStatus';

export default function Dashboard() {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero / Welcome Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-surface-card via-surface-card/90 to-brand-950/40 border border-surface-border p-6 sm:p-8 lg:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
        <div className="max-w-3xl space-y-4 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold">
            <Sparkles size={14} className="text-brand-400" />
            <span>Phase 8.1 Active • Application Shell</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Welcome to Multilingual AI Document Assistant
          </h1>

          <p className="text-sm sm:text-base text-gray-300 leading-relaxed">
            Upload institutional documents, ask citation-grounded questions across multiple languages (English, Hindi, Kannada, Telugu), and explore privacy-preserving telemetry analytics powered by Apache PySpark.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/documents"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition shadow-lg shadow-brand-600/30 active:scale-95"
            >
              <UploadCloud size={18} />
              <span>Upload Document</span>
            </Link>
            <Link
              to="/ask"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-surface-base hover:bg-surface-card border border-surface-border text-white font-medium text-sm transition active:scale-95"
            >
              <BotMessageSquare size={18} className="text-indigo-400" />
              <span>Ask AI</span>
            </Link>
            <Link
              to="/analytics"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-surface-base hover:bg-surface-card border border-surface-border text-white font-medium text-sm transition active:scale-95"
            >
              <BarChart3 size={18} className="text-emerald-400" />
              <span>View Analytics</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Live System Diagnostics */}
      <SystemStatus />

      {/* Quick Action Navigation Cards */}
      <section className="space-y-4">
        <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <span>Quick Actions</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1: Documents */}
          <Link
            to="/documents"
            className="group p-6 rounded-2xl bg-surface-card border border-surface-border hover:border-brand-500/40 hover:bg-surface-card/80 transition duration-200 flex flex-col justify-between space-y-4 shadow-lg"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center group-hover:scale-105 transition">
                <FileText size={24} />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-brand-300 transition">
                Document Repository
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Ingest institutional PDFs, Word documents, and text files with page-aware chunking and multilingual embedding indexing.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-brand-400 group-hover:translate-x-1 transition">
              <span>Manage documents</span>
              <ArrowRight size={14} />
            </div>
          </Link>

          {/* Card 2: Ask AI */}
          <Link
            to="/ask"
            className="group p-6 rounded-2xl bg-surface-card border border-surface-border hover:border-indigo-500/40 hover:bg-surface-card/80 transition duration-200 flex flex-col justify-between space-y-4 shadow-lg"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center group-hover:scale-105 transition">
                <BotMessageSquare size={24} />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition">
                Ask AI Assistant
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Query institutional knowledge with hybrid RAG retrieval, transliteration normalization, and strict citation provenance.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 group-hover:translate-x-1 transition">
              <span>Start conversation</span>
              <ArrowRight size={14} />
            </div>
          </Link>

          {/* Card 3: Big Data Analytics */}
          <Link
            to="/analytics"
            className="group p-6 rounded-2xl bg-surface-card border border-surface-border hover:border-emerald-500/40 hover:bg-surface-card/80 transition duration-200 flex flex-col justify-between space-y-4 shadow-lg"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center group-hover:scale-105 transition">
                <BarChart3 size={24} />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition">
                Big Data Analytics
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Examine batch-aggregated telemetry metrics, language distributions, RAG latencies, and zero-raw-data privacy metrics.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 group-hover:translate-x-1 transition">
              <span>Explore metrics</span>
              <ArrowRight size={14} />
            </div>
          </Link>
        </div>
      </section>

      {/* Core Architecture Capabilities */}
      <section className="bg-surface-card/50 border border-surface-border rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider text-gray-400">
          Platform Architecture & Technology Stack
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1.5">
            <div className="flex items-center gap-2 text-brand-400">
              <Layers size={16} />
              <h4 className="text-xs font-bold text-white">Hybrid Retrieval</h4>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Dense multilingual-e5-small embeddings + Unicode BM25 lexical fusion with heuristic reranking.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1.5">
            <div className="flex items-center gap-2 text-indigo-400">
              <Cpu size={16} />
              <h4 className="text-xs font-bold text-white">Multilingual Core</h4>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Indic script normalization, phonetic transliteration mapping, and query expansion across 4 languages.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1.5">
            <div className="flex items-center gap-2 text-emerald-400">
              <BarChart3 size={16} />
              <h4 className="text-xs font-bold text-white">PySpark Lake</h4>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              JSONL privacy telemetry partitioned into Parquet data lakes with batch analytics jobs.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1.5">
            <div className="flex items-center gap-2 text-amber-400">
              <ShieldCheck size={16} />
              <h4 className="text-xs font-bold text-white">Zero Raw Privacy</h4>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Strict privacy preservation ensuring raw queries, answers, and documents are never logged to telemetry.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
