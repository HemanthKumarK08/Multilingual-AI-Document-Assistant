import React, { useState } from 'react';
import {
  FileText,
  Copy,
  Check,
  ExternalLink,
  BookOpen,
  Layers,
  Sparkles,
} from 'lucide-react';

export default function CitationCard({ citation, onInspect }) {
  const [copied, setCopied] = useState(false);

  if (!citation) return null;

  function copyCitation(e) {
    e.stopPropagation();
    const title = citation.document_title || citation.document_id || 'Institutional Document';
    const page = citation.page_number ? `, Page ${citation.page_number}` : '';
    const citeStr = `${title}${page}`;
    navigator.clipboard.writeText(citeStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const scorePercent =
    citation.similarity_score !== undefined && citation.similarity_score !== null
      ? Math.round(citation.similarity_score * 100)
      : null;

  return (
    <div
      onClick={() => onInspect(citation)}
      className="p-3.5 rounded-2xl bg-surface-base/80 hover:bg-surface-base border border-surface-border/80 hover:border-indigo-500/40 transition cursor-pointer group shadow-sm space-y-2.5"
    >
      {/* Top Title & Badges */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0 group-hover:scale-105 transition">
            <FileText size={15} />
          </div>
          <p className="font-bold text-xs text-white group-hover:text-indigo-300 transition truncate">
            {citation.document_title || citation.document_id}
          </p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {citation.page_number && (
            <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold text-[10px]">
              Page {citation.page_number}
            </span>
          )}
          {scorePercent !== null && (
            <span
              className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[10px]"
              title="Retrieval Similarity Score"
            >
              {scorePercent}% match
            </span>
          )}
        </div>
      </div>

      {/* Excerpt Snippet */}
      {citation.excerpt && (
        <p className="text-[11px] text-gray-300 italic bg-surface-card/60 p-2.5 rounded-xl border border-surface-border/40 line-clamp-2 leading-relaxed">
          "{citation.excerpt}"
        </p>
      )}

      {/* Footer Details & Action */}
      <div className="flex items-center justify-between pt-1 text-[10px] text-gray-400">
        <span className="capitalize text-gray-400">
          {citation.category ? citation.category.replace(/_/g, ' ') : 'Institutional Policy'}
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={copyCitation}
            className="text-gray-400 hover:text-white p-1 rounded transition"
            title="Copy Citation"
          >
            {copied ? (
              <Check size={12} className="text-emerald-400" />
            ) : (
              <Copy size={12} />
            )}
          </button>
          <span className="text-indigo-400 group-hover:text-indigo-300 font-semibold flex items-center gap-1">
            <span>View Evidence</span>
            <BookOpen size={11} />
          </span>
        </div>
      </div>
    </div>
  );
}
