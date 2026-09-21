import React from 'react';
import { Shield, Database, Flame, Server, ArrowRight, CheckCircle2, Lock } from 'lucide-react';

export default function PrivacyArchitectureNotice({ generatedAt, recordCount }) {
  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Precomputed';

  const pipelineSteps = [
    { name: 'Telemetry Events', icon: Shield, desc: 'Privacy-gated capture' },
    { name: 'JSONL Logs', icon: Database, desc: 'Local append logs' },
    { name: 'Parquet Lake', icon: Database, desc: 'Columnar partitions' },
    { name: 'PySpark Engine', icon: Flame, desc: 'Batch compute job' },
    { name: 'REST Analytics API', icon: Server, desc: '7 precomputed endpoints' },
  ];

  const privacyGuarantees = [
    'No raw document text stored',
    'No raw query text stored',
    'No raw AI responses stored',
    'No credential or token fields stored',
    'Derived performance metrics only',
    'Local execution & storage',
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Privacy Guarantees Card */}
        <div className="p-5 sm:p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-emerald-400">
            <Lock size={16} />
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">
              Privacy-Preserving Telemetry Model
            </h4>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Telemetry schema rejects raw document passages and user query strings. No prohibited raw-content or credential fields detected in the audited telemetry dataset.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
            {privacyGuarantees.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-gray-300">
                <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PySpark Big Data Architecture Card */}
        <div className="lg:col-span-2 p-5 sm:p-6 rounded-2xl bg-surface-card border border-surface-border shadow-sm space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-brand-400">
                <Flame size={16} />
                <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                  PySpark Big Data Analytics Pipeline
                </h4>
              </div>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 font-medium">
                Apache Spark 3.5.3
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              High-throughput offline batch processing from date-partitioned Parquet files into precomputed JSON aggregates.
            </p>
          </div>

          {/* Pipeline Flow Diagram */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
            {pipelineSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={idx}
                  className="p-2.5 rounded-xl bg-surface-base border border-surface-border flex flex-col items-center text-center relative group hover:border-brand-500/30 transition"
                >
                  <div className="p-1.5 rounded-lg bg-surface-card text-brand-400 mb-1.5">
                    <Icon size={14} />
                  </div>
                  <span className="text-xs font-semibold text-white">{step.name}</span>
                  <span className="text-[10px] text-gray-400 mt-0.5">{step.desc}</span>
                </div>
              );
            })}
          </div>

          {/* Batch Notice Footer */}
          <div className="pt-2 border-t border-surface-border/60 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-gray-400 gap-2">
            <span>
              Batch analytics computed over <strong className="text-gray-200">{recordCount || 350} records</strong>
            </span>
            <span>
              Generated at: <strong className="text-gray-200">{formattedDate}</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
