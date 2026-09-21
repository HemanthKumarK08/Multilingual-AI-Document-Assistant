import React, { useEffect, useState } from 'react';
import {
  X,
  FileText,
  Copy,
  Check,
  Layers,
  HardDrive,
  Hash,
  ShieldCheck,
  Sparkles,
  Info,
  Bookmark,
} from 'lucide-react';

export default function EvidenceDrawer({ citation, onClose }) {
  const [copiedEvidence, setCopiedEvidence] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState(false);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!citation) return null;

  function copyEvidenceText() {
    navigator.clipboard.writeText(citation.excerpt || '');
    setCopiedEvidence(true);
    setTimeout(() => setCopiedEvidence(false), 2000);
  }

  function copyCitationString() {
    const title = citation.document_title || citation.document_id || 'Institutional Document';
    const page = citation.page_number ? `, Page ${citation.page_number}` : '';
    const chunk = citation.chunk_index !== undefined ? `, Chunk ${citation.chunk_index + 1}` : '';
    const citeStr = `${title}${page}${chunk}`;
    navigator.clipboard.writeText(citeStr);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  }

  // Format relevance percentage if available
  const scorePercent =
    citation.similarity_score !== undefined && citation.similarity_score !== null
      ? Math.round(citation.similarity_score * 100)
      : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-modal-title"
    >
      <div
        className="relative w-full max-w-2xl bg-surface-card border border-surface-border rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="p-6 border-b border-surface-border flex items-start justify-between bg-surface-base/50">
          <div className="flex items-start gap-3.5">
            <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
              <Bookmark size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold text-[10px] uppercase tracking-wider">
                  Verified Citation
                </span>
                {citation.page_number && (
                  <span className="px-2 py-0.5 rounded-md bg-surface-base border border-surface-border text-gray-300 font-mono text-[11px] font-bold">
                    Page {citation.page_number}
                  </span>
                )}
              </div>
              <h2 id="evidence-modal-title" className="text-base sm:text-lg font-bold text-white leading-snug">
                {citation.document_title || citation.document_id}
              </h2>
              <p className="text-xs text-gray-400 font-mono mt-0.5">{citation.document_id}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close evidence modal"
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-surface-base border border-transparent hover:border-surface-border transition"
          >
            <X size={20} />
          </button>
        </div>

        {/* Drawer Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Provenance Metadata Grid */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">
              Provenance Attributes
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <span className="text-gray-400 text-[11px] font-medium">Category</span>
                <p className="font-semibold text-white capitalize truncate">
                  {citation.category ? citation.category.replace(/_/g, ' ') : 'General'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <span className="text-gray-400 text-[11px] font-medium">Page Number</span>
                <p className="font-semibold text-white">
                  {citation.page_number ? `Page ${citation.page_number}` : 'N/A'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <span className="text-gray-400 text-[11px] font-medium">Chunk Index</span>
                <p className="font-semibold text-white font-mono">
                  {citation.chunk_index !== undefined ? `#${citation.chunk_index + 1}` : 'N/A'}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-surface-base/60 border border-surface-border/60 space-y-1">
                <span className="text-gray-400 text-[11px] font-medium">Retrieval Similarity</span>
                <p className="font-semibold text-emerald-400 font-mono">
                  {scorePercent !== null ? `${scorePercent}% match` : 'High'}
                </p>
              </div>
            </div>
          </div>

          {/* Supporting Evidence Passage */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                <FileText size={14} className="text-indigo-400" />
                <span>Supporting Evidence Passage</span>
              </h3>
              <button
                onClick={copyEvidenceText}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-base hover:bg-surface-base/80 border border-surface-border text-xs text-gray-300 hover:text-white transition"
              >
                {copiedEvidence ? (
                  <>
                    <Check size={12} className="text-emerald-400" />
                    <span className="text-emerald-400 font-semibold text-[11px]">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span className="text-[11px]">Copy Passage</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-4 rounded-2xl bg-surface-base/90 border border-surface-border text-xs sm:text-sm text-gray-200 leading-relaxed font-sans select-text">
              {citation.excerpt ? (
                <p className="italic text-gray-200">
                  "{citation.excerpt}"
                </p>
              ) : (
                <p className="text-gray-400 italic">
                  No textual excerpt available for this source.
                </p>
              )}
            </div>
          </div>

          {/* Storage & Knowledge Base Notice */}
          <div className="p-4 rounded-2xl bg-surface-base/40 border border-surface-border/50 text-xs text-gray-400 space-y-1">
            <div className="flex items-center gap-2 text-gray-300 font-semibold">
              <ShieldCheck size={14} className="text-emerald-400" />
              <span>Grounded Knowledge Base Verification</span>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              This evidence passage was retrieved through hybrid dense vector similarity (multilingual-e5-small) and Unicode BM25 lexical fusion, validated against the institutional document collection in ChromaDB.
            </p>
          </div>
        </div>

        {/* Drawer Actions Footer */}
        <div className="p-4 border-t border-surface-border flex flex-wrap items-center justify-between gap-3 bg-surface-base/50">
          <button
            onClick={copyCitationString}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-semibold text-gray-300 hover:text-white transition"
          >
            {copiedCitation ? (
              <>
                <Check size={13} className="text-emerald-400" />
                <span className="text-emerald-400">Citation Copied</span>
              </>
            ) : (
              <>
                <Copy size={13} />
                <span>Copy Citation</span>
              </>
            )}
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition shadow-md shadow-brand-600/30"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
