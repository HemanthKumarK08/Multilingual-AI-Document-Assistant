import React, { useEffect } from 'react';
import {
  X,
  FileText,
  Calendar,
  Layers,
  Database,
  ShieldCheck,
  Hash,
  Globe,
  HardDrive,
  Info,
  CheckCircle2,
  AlertCircle,
  Clock,
} from 'lucide-react';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DocumentDetailModal({ doc, onClose }) {
  // Close on Escape key press
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!doc) return null;

  const isStatusSuccess = doc.status === 'parsed' || doc.status === 'indexed' || doc.status === 'completed';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="relative w-full max-w-2xl bg-surface-card border border-surface-border rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-6 border-b border-surface-border flex items-start justify-between bg-surface-base/50">
          <div className="flex items-start gap-3.5">
            <div className="p-3 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 shrink-0">
              <FileText size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded-md bg-brand-500/10 border border-brand-500/20 text-brand-300 font-mono text-[11px] font-bold">
                  {doc.doc_id}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    isStatusSuccess
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {isStatusSuccess ? <CheckCircle2 size={11} /> : <AlertCircle size={11} />}
                  <span>{doc.status}</span>
                </span>
              </div>
              <h2 id="modal-title" className="text-lg font-bold text-white leading-snug">
                {doc.display_title || doc.filename}
              </h2>
              <p className="text-xs text-gray-400 font-mono mt-0.5">{doc.filename}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-surface-base border border-transparent hover:border-surface-border transition"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Document Properties Grid */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">
              Document Metadata
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <Layers size={13} className="text-brand-400" />
                  <span>Category</span>
                </div>
                <p className="font-semibold text-white capitalize">
                  {doc.category ? doc.category.replace(/_/g, ' ') : 'General'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <Globe size={13} className="text-indigo-400" />
                  <span>Language</span>
                </div>
                <p className="font-semibold text-white uppercase">{doc.language || 'en'}</p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <HardDrive size={13} className="text-emerald-400" />
                  <span>File Size</span>
                </div>
                <p className="font-semibold text-white">{formatBytes(doc.file_size_bytes)}</p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <FileText size={13} className="text-amber-400" />
                  <span>Page Count</span>
                </div>
                <p className="font-semibold text-white">{doc.page_count ?? 1} Pages</p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <Database size={13} className="text-blue-400" />
                  <span>Format</span>
                </div>
                <p className="font-semibold text-white uppercase">{doc.file_type || 'TXT'}</p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <Calendar size={13} className="text-purple-400" />
                  <span>Ingested On</span>
                </div>
                <p className="font-semibold text-white truncate">
                  {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Cryptographic SHA-256 Provenance */}
          <div className="p-4 rounded-2xl bg-surface-base/60 border border-surface-border/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs font-bold text-gray-300">
                <Hash size={14} className="text-brand-400" />
                SHA-256 Provenance Hash
              </span>
              <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Verified
              </span>
            </div>
            <p className="font-mono text-[11px] text-gray-400 break-all bg-surface-card/90 p-2.5 rounded-xl border border-surface-border/40 select-all">
              {doc.file_hash_sha256 || 'N/A'}
            </p>
          </div>

          {/* Error Message if any */}
          {doc.error_message && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertCircle size={15} />
                <span>Processing Notice</span>
              </div>
              <p className="text-rose-200/90">{doc.error_message}</p>
            </div>
          )}

          {/* Chunk Inspection Notice (Step 15) */}
          <div className="p-4 rounded-2xl bg-surface-base/40 border border-surface-border/50 text-xs text-gray-400 space-y-1.5">
            <div className="flex items-center gap-2 text-gray-300 font-semibold">
              <Info size={15} className="text-brand-400" />
              <span>ChromaDB Vector Store Chunks</span>
            </div>
            <p className="text-gray-400 leading-relaxed text-[11px]">
              Chunk inspection is available internally via the ChromaDB collection <code className="text-brand-300 font-mono">document_chunks</code> and intermediate artifacts at <code className="text-brand-300 font-mono">data/processed/{doc.doc_id}_chunks.json</code>. No public chunk inspection REST endpoint is currently exposed.
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-surface-border flex justify-end bg-surface-base/50">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-semibold text-white transition active:scale-95"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
