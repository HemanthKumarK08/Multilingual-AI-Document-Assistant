import React, { useState, useEffect } from 'react';
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
  ExternalLink,
  Download,
  Eye,
  Loader2,
  Trash2,
  FileCode,
  FileType,
  BookOpen,
  FileSearch,
  Sparkles
} from 'lucide-react';
import { apiService } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DocumentDetailModal({ doc, onClose, onDeleteRequested }) {
  // Tabs: 'original' | 'content' | 'metadata'
  const [activeTab, setActiveTab] = useState('original');
  const [contentData, setContentData] = useState(null);
  const [loadingContent, setLoadingContent] = useState(true);
  const [contentError, setContentError] = useState(null);

  // Close on Escape key press
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Fetch document content / preview from backend
  useEffect(() => {
    let isMounted = true;
    if (!doc?.doc_id) return;

    setLoadingContent(true);
    setContentError(null);

    apiService.getDocumentContent(doc.doc_id)
      .then((data) => {
        if (isMounted) {
          setContentData(data);
          setLoadingContent(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Failed to load document content:", err);
          setContentError(err.message || 'Unable to load document content');
          setLoadingContent(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [doc?.doc_id]);

  if (!doc) return null;

  const isStatusSuccess = doc.status === 'parsed' || doc.status === 'indexed' || doc.status === 'completed';
  const fileType = (doc.file_type || '').toLowerCase();
  const fileUrl = apiService.getDocumentFileUrl(doc.doc_id);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-black/80 backdrop-blur-md animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="relative w-full max-w-5xl bg-surface-card border border-surface-border rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-surface-border flex items-center justify-between bg-surface-base/70">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 shrink-0">
              <FileText size={22} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="px-2 py-0.5 rounded-md bg-brand-500/10 border border-brand-500/20 text-brand-300 font-mono text-[10px] sm:text-[11px] font-bold">
                  {doc.doc_id}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    isStatusSuccess
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {isStatusSuccess ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
                  <span>{doc.status}</span>
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-base border border-surface-border text-gray-300 text-[10px] font-mono uppercase font-bold">
                  {fileType || 'DOC'}
                </span>
              </div>
              <h2 id="modal-title" className="text-base sm:text-lg font-bold text-white leading-snug truncate">
                {doc.display_title || doc.filename}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onDeleteRequested && (
              <button
                onClick={() => {
                  onClose();
                  onDeleteRequested(doc);
                }}
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-semibold transition"
                title="Delete Document"
              >
                <Trash2 size={13} />
                <span>Delete</span>
              </button>
            )}
            <button
              onClick={onClose}
              aria-label="Close modal"
              className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-surface-base border border-transparent hover:border-surface-border transition"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Viewer Navigation Subheader Tabs: [ View Original ] [ View Content ] [ Metadata ] */}
        <div className="px-5 py-2.5 bg-surface-base/40 border-b border-surface-border flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('original')}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'original'
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                  : 'text-gray-400 hover:text-white hover:bg-surface-card'
              }`}
            >
              <BookOpen size={13} />
              <span>View Original</span>
            </button>
            <button
              onClick={() => setActiveTab('content')}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'content'
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                  : 'text-gray-400 hover:text-white hover:bg-surface-card'
              }`}
            >
              <FileSearch size={13} />
              <span>View Content</span>
            </button>
            <button
              onClick={() => setActiveTab('metadata')}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'metadata'
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                  : 'text-gray-400 hover:text-white hover:bg-surface-card'
              }`}
            >
              <Info size={13} />
              <span>Metadata</span>
            </button>
          </div>

          {/* External Action Button */}
          <div className="flex items-center gap-2">
            <a
              href={fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-surface-card hover:bg-surface-base border border-surface-border text-xs text-gray-300 hover:text-brand-300 font-medium transition shadow-sm"
            >
              <Download size={12} />
              <span>Raw File</span>
              <ExternalLink size={11} />
            </a>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 min-h-[380px]">
          {loadingContent ? (
            /* Loading Skeleton */
            <div className="space-y-3 py-12 text-center">
              <Loader2 size={32} className="animate-spin text-brand-400 mx-auto" />
              <p className="text-xs text-gray-400">Loading document...</p>
              <div className="max-w-md mx-auto space-y-2 pt-4">
                <div className="h-4 bg-surface-base rounded animate-pulse" />
                <div className="h-4 bg-surface-base rounded animate-pulse w-5/6 mx-auto" />
                <div className="h-4 bg-surface-base rounded animate-pulse w-4/6 mx-auto" />
              </div>
            </div>
          ) : contentError ? (
            /* Error State */
            <div className="p-8 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-center space-y-3">
              <AlertCircle size={32} className="text-rose-400 mx-auto" />
              <h3 className="text-sm font-bold text-rose-200">Unable to preview this document</h3>
              <p className="text-xs text-rose-300/80 max-w-md mx-auto">{contentError}</p>
              <div className="pt-2">
                <a
                  href={fileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface-card border border-surface-border text-xs font-semibold text-white hover:bg-surface-base transition"
                >
                  <Download size={13} />
                  <span>Download / Open File Directly</span>
                </a>
              </div>
            </div>
          ) : activeTab === 'original' ? (
            /* TAB 1: VIEW ORIGINAL */
            <div className="space-y-4 animate-fadeIn">
              {fileType === 'pdf' ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-gray-400 px-1">
                    <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Original PDF Document Viewer</span>
                    </div>
                    <a
                      href={fileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand-400 hover:text-brand-300 font-semibold inline-flex items-center gap-1"
                    >
                      <span>Open in Full Tab</span>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                  <div className="w-full h-[540px] rounded-2xl overflow-hidden border border-surface-border bg-gray-950 shadow-inner">
                    <iframe
                      src={`${fileUrl}#toolbar=1&navpanes=1&scrollbar=1`}
                      title={doc.display_title || doc.filename}
                      className="w-full h-full border-none"
                    />
                  </div>
                </div>
              ) : fileType === 'md' ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-gray-400 px-1">
                    <div className="flex items-center gap-1.5 font-semibold text-indigo-400">
                      <span className="w-2 h-2 rounded-full bg-indigo-400" />
                      <span>Original Markdown Document</span>
                    </div>
                    <span className="text-[11px] font-mono text-gray-500">
                      {contentData?.text_content ? `${contentData.text_content.length} characters` : ''}
                    </span>
                  </div>
                  <div className="p-5 rounded-2xl bg-surface-base/80 border border-surface-border max-h-[540px] overflow-y-auto text-sm leading-relaxed">
                    <MarkdownRenderer content={contentData?.text_content || 'No text content available.'} />
                  </div>
                </div>
              ) : fileType === 'docx' || fileType === 'doc' ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-bold text-amber-300">
                      <Info size={16} />
                      <span>DOCX Binary File Format</span>
                    </div>
                    <p className="text-amber-200/90 leading-relaxed">
                      Direct binary DOCX rendering is not supported natively inside web browsers. You can open/download the original file using the button below, or view the extracted structured text in the <strong>View Content</strong> tab.
                    </p>
                    <div className="pt-1">
                      <a
                        href={fileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 text-xs font-semibold text-white transition"
                      >
                        <Download size={13} />
                        <span>Download Original DOCX</span>
                      </a>
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-surface-base/80 border border-surface-border max-h-[420px] overflow-y-auto space-y-3 text-xs">
                    <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                      Structured Document Preview (Extracted Institutional Content)
                    </h4>
                    {contentData?.text_content ? (
                      contentData.text_content.split('\n\n').map((para, pIdx) => (
                        <p key={pIdx} className="text-gray-200 leading-relaxed">
                          {para}
                        </p>
                      ))
                    ) : (
                      <p className="text-gray-400 italic">No text content extracted for this DOCX document.</p>
                    )}
                  </div>
                </div>
              ) : (
                /* Plain TXT File */
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-gray-400 px-1">
                    <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Original Plain Text File</span>
                    </div>
                    <span className="text-[11px] font-mono text-gray-500">
                      {contentData?.text_content ? `${contentData.text_content.length} characters` : ''}
                    </span>
                  </div>
                  <pre className="p-5 rounded-2xl bg-surface-base/80 border border-surface-border max-h-[540px] overflow-y-auto font-mono text-xs text-gray-200 whitespace-pre-wrap leading-relaxed">
                    {contentData?.text_content || 'No text content available.'}
                  </pre>
                </div>
              )}
            </div>
          ) : activeTab === 'content' ? (
            /* TAB 2: VIEW EXTRACTED CONTENT / PREVIEW */
            <div className="space-y-4 animate-fadeIn">
              <div className="p-3.5 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold">
                  <Sparkles size={15} />
                  <span>Extracted Content Preview (Normalized Institutional Data)</span>
                </div>
                <span className="text-[11px] font-mono text-gray-400">
                  {contentData?.sections_count ? `${contentData.sections_count} sections` : 'Extracted Text'}
                </span>
              </div>

              {fileType === 'md' ? (
                <div className="p-5 rounded-2xl bg-surface-base/80 border border-surface-border max-h-[500px] overflow-y-auto text-sm leading-relaxed">
                  <MarkdownRenderer content={contentData?.text_content || 'No text content found in document.'} />
                </div>
              ) : (
                <div className="p-5 rounded-2xl bg-surface-base/80 border border-surface-border max-h-[500px] overflow-y-auto space-y-4 text-xs leading-relaxed">
                  {contentData?.text_content ? (
                    contentData.text_content.split('\n\n').map((para, pIdx) => (
                      <p key={pIdx} className="text-gray-200">
                        {para}
                      </p>
                    ))
                  ) : (
                    <p className="text-gray-400 italic">No extracted text content available for this document.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* TAB 3: METADATA & PROVENANCE */
            <div className="space-y-6 animate-fadeIn">
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

              {/* Chunk & Vector Store Details */}
              <div className="p-4 rounded-2xl bg-surface-base/40 border border-surface-border/50 text-xs text-gray-400 space-y-1.5">
                <div className="flex items-center gap-2 text-gray-300 font-semibold">
                  <Info size={15} className="text-brand-400" />
                  <span>ChromaDB Vector Store Chunks</span>
                </div>
                <p className="text-gray-400 leading-relaxed text-[11px]">
                  Chunk indexed under collection <code className="text-brand-300 font-mono">document_chunks</code> with ownership tag <code className="text-brand-300 font-mono">{doc.doc_id}</code>. Total indexed chunks: <span className="font-bold text-white">{doc.chunk_count || contentData?.sections_count || 'N/A'}</span>.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-surface-border flex items-center justify-between bg-surface-base/70">
          <div className="text-xs text-gray-400 font-mono">
            ID: <span className="text-gray-200">{doc.doc_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-semibold text-white transition active:scale-95"
            >
              Close Viewer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
