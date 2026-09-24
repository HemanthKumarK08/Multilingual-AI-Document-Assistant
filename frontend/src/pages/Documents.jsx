import React, { useState, useEffect } from 'react';
import {
  Files,
  Search,
  Filter,
  RefreshCw,
  FileText,
  Eye,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  HardDrive,
  Globe,
  SlidersHorizontal,
  AlertTriangle,
  Loader2,
  X
} from 'lucide-react';
import { apiService } from '../services/api';
import DocumentUploadZone from '../components/DocumentUploadZone';
import DocumentDetailModal from '../components/DocumentDetailModal';

const CATEGORY_TABS = [
  { id: 'all', label: 'All Categories' },
  { id: 'academic_regulations', label: 'Academic Regulations' },
  { id: 'examination_guidelines', label: 'Examination' },
  { id: 'attendance', label: 'Attendance' },
  { id: 'scholarships', label: 'Scholarships' },
  { id: 'hostel', label: 'Hostel' },
  { id: 'placements', label: 'Placements' },
];

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  // Modal states
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [successNotice, setSuccessNotice] = useState(null);

  async function loadDocuments(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const data = await apiService.getDocuments();
      setDocuments(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Failed to load institutional documents');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  // Handle Document Deletion
  async function handleConfirmDelete() {
    if (!documentToDelete) return;
    setIsDeleting(true);
    setDeleteError(null);

    try {
      const resp = await apiService.deleteDocument(documentToDelete.doc_id);
      
      // Update local state and remove deleted document
      setDocuments((prev) => prev.filter((d) => d.doc_id !== documentToDelete.doc_id));
      
      // Close viewer modal if currently viewing this deleted doc
      if (selectedDoc?.doc_id === documentToDelete.doc_id) {
        setSelectedDoc(null);
      }

      setSuccessNotice(
        resp.message || `Document '${documentToDelete.display_title || documentToDelete.filename}' was successfully removed.`
      );
      
      // Auto-dismiss toast
      setTimeout(() => {
        setSuccessNotice(null);
      }, 5000);

      setDocumentToDelete(null);
    } catch (err) {
      console.error("Deletion failed:", err);
      setDeleteError(err.message || 'Failed to delete document and associated vectors.');
    } finally {
      setIsDeleting(false);
    }
  }

  // Client-side filtering across loaded documents
  const filteredDocuments = documents.filter((doc) => {
    const matchesCategory =
      selectedCategory === 'all' || doc.category === selectedCategory;

    const q = searchQuery.toLowerCase().trim();
    if (!q) return matchesCategory;

    const matchesSearch =
      (doc.display_title && doc.display_title.toLowerCase().includes(q)) ||
      (doc.doc_id && doc.doc_id.toLowerCase().includes(q)) ||
      (doc.filename && doc.filename.toLowerCase().includes(q)) ||
      (doc.category && doc.category.toLowerCase().includes(q)) ||
      (doc.language && doc.language.toLowerCase().includes(q));

    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto pb-12">
      {/* Toast / Notification Banner */}
      {successNotice && (
        <div className="p-4 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 flex items-center justify-between gap-3 shadow-lg animate-fadeIn">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
            <span>{successNotice}</span>
          </div>
          <button
            onClick={() => setSuccessNotice(null)}
            className="text-emerald-400 hover:text-white p-1 rounded-lg transition"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-brand-400 mb-1">
            <Files size={14} />
            <span>Document Repository</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Documents
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
            Manage, inspect, and safely index your institutional knowledge base for RAG retrieval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-surface-card border border-surface-border text-xs font-semibold text-gray-300">
            <span className="text-brand-400 font-bold">{documents.length}</span> Documents Registered
          </div>

          <button
            onClick={() => loadDocuments(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-surface-card hover:bg-surface-card/80 border border-surface-border text-xs font-medium text-gray-200 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Upload Zone Component */}
      <section className="space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400">
          Upload & Ingest New Document
        </h2>
        <DocumentUploadZone onUploadSuccess={() => loadDocuments(true)} />
      </section>

      {/* Filter and Search Bar */}
      <section className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, doc ID, category, or language..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white placeholder-gray-500 text-xs focus:outline-none focus:border-brand-500 transition shadow-inner"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white text-xs font-medium"
              >
                Clear
              </button>
            )}
          </div>

          {/* Results Summary Counter */}
          <div className="text-xs text-gray-400 flex items-center gap-2">
            <span>Showing <strong className="text-white">{filteredDocuments.length}</strong> of {documents.length} records</span>
          </div>
        </div>

        {/* Category Pills Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORY_TABS.map((tab) => {
            const isActive = selectedCategory === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedCategory(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                    : 'bg-surface-card hover:bg-surface-card/80 text-gray-400 hover:text-white border border-surface-border'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Documents Table / Card List */}
      <section className="space-y-4">
        {loading ? (
          /* Loading Skeleton */
          <div className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4 shadow-xl">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="h-16 rounded-xl bg-surface-base/60 animate-pulse flex items-center justify-between px-4"
              >
                <div className="space-y-2 w-1/3">
                  <div className="h-4 bg-gray-700/60 rounded w-3/4" />
                  <div className="h-3 bg-gray-800/80 rounded w-1/2" />
                </div>
                <div className="h-4 bg-gray-800/80 rounded w-20" />
                <div className="h-4 bg-gray-800/80 rounded w-24" />
              </div>
            ))}
          </div>
        ) : error ? (
          /* Error State */
          <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-center space-y-3">
            <AlertCircle size={28} className="mx-auto text-rose-400" />
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-rose-200">Unable to load document repository</h3>
              <p className="text-xs text-rose-300/80 max-w-md mx-auto">{error}</p>
            </div>
            <button
              onClick={() => loadDocuments(false)}
              className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition"
            >
              Try Again
            </button>
          </div>
        ) : filteredDocuments.length === 0 ? (
          /* Empty State */
          <div className="bg-surface-card border border-surface-border rounded-3xl p-10 text-center space-y-4 shadow-xl">
            <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center">
              <FileText size={32} />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h3 className="text-base font-bold text-white">
                {searchQuery || selectedCategory !== 'all'
                  ? 'No matching documents found'
                  : 'No indexed documents yet'}
              </h3>
              <p className="text-xs text-gray-400">
                {searchQuery || selectedCategory !== 'all'
                  ? 'Try adjusting your search terms or selecting a different category filter.'
                  : 'Upload your first PDF, DOCX, TXT, or Markdown document above to begin building your searchable knowledge base.'}
              </p>
            </div>
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                }}
                className="px-4 py-2 rounded-xl bg-surface-base border border-surface-border text-xs font-semibold text-gray-300 hover:text-white transition"
              >
                Reset Filters
              </button>
            )}
          </div>
        ) : (
          /* Document Table (Responsive for Desktop & Tablet) */
          <div className="bg-surface-card border border-surface-border rounded-2xl shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-base/40 text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                    <th className="py-3.5 px-4 sm:px-6">Document</th>
                    <th className="py-3.5 px-4 hidden md:table-cell">Category</th>
                    <th className="py-3.5 px-4 hidden sm:table-cell">Language</th>
                    <th className="py-3.5 px-4 hidden lg:table-cell">Size & Pages</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border text-xs">
                  {filteredDocuments.map((doc) => {
                    const isSuccess =
                      doc.status === 'parsed' ||
                      doc.status === 'indexed' ||
                      doc.status === 'completed';

                    return (
                      <tr
                        key={doc.doc_id}
                        onClick={() => setSelectedDoc(doc)}
                        className="hover:bg-surface-base/40 cursor-pointer transition group"
                      >
                        {/* Title & Doc ID */}
                        <td className="py-3.5 px-4 sm:px-6">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 shrink-0 group-hover:scale-105 transition">
                              <FileText size={18} />
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-white group-hover:text-brand-300 transition truncate max-w-xs sm:max-w-md">
                                {doc.display_title || doc.filename}
                              </p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className="font-mono text-[10px] text-gray-400">
                                  {doc.doc_id}
                                </span>
                                <span className="px-1.5 py-0.2 rounded text-[10px] uppercase font-bold bg-surface-base border border-surface-border/80 text-gray-300">
                                  {doc.file_type || 'TXT'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Category */}
                        <td className="py-3.5 px-4 hidden md:table-cell">
                          <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-surface-base border border-surface-border text-gray-300 capitalize">
                            {doc.category ? doc.category.replace(/_/g, ' ') : 'General'}
                          </span>
                        </td>

                        {/* Language */}
                        <td className="py-3.5 px-4 hidden sm:table-cell">
                          <div className="flex items-center gap-1.5 text-gray-300">
                            <Globe size={13} className="text-indigo-400" />
                            <span className="uppercase font-medium">{doc.language || 'en'}</span>
                          </div>
                        </td>

                        {/* Size & Pages */}
                        <td className="py-3.5 px-4 hidden lg:table-cell text-gray-400">
                          <span>{formatBytes(doc.file_size_bytes)}</span>
                          <span className="mx-1.5">•</span>
                          <span>{doc.page_count ?? 1} p</span>
                        </td>

                        {/* Status Badge */}
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold capitalize ${
                              isSuccess
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isSuccess ? 'bg-emerald-400' : 'bg-rose-400'
                              }`}
                            />
                            <span>{doc.status}</span>
                          </span>
                        </td>

                        {/* Actions: [ 👁 View ] [ 🗑 Delete ] */}
                        <td className="py-3.5 px-4 text-right">
                          <div className="inline-flex items-center gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedDoc(doc);
                              }}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-base hover:bg-brand-600 hover:text-white border border-surface-border text-xs font-semibold text-gray-300 transition shadow-sm active:scale-95"
                              title="View Document & Metadata"
                            >
                              <Eye size={13} />
                              <span>View</span>
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setDocumentToDelete(doc);
                              }}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-base hover:bg-rose-600 hover:text-white border border-surface-border hover:border-rose-500 text-xs font-semibold text-rose-400 transition shadow-sm active:scale-95"
                              title="Delete Document"
                            >
                              <Trash2 size={13} />
                              <span>Delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Document Viewer Modal */}
      {selectedDoc && (
        <DocumentDetailModal
          doc={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onDeleteRequested={(docToDelete) => setDocumentToDelete(docToDelete)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {documentToDelete && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
        >
          <div
            className="relative w-full max-w-md bg-surface-card border border-rose-500/30 rounded-3xl shadow-2xl overflow-hidden p-6 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 shrink-0">
                <AlertTriangle size={24} />
              </div>
              <div className="space-y-1">
                <h3 id="delete-dialog-title" className="text-base font-bold text-white">
                  Delete Document?
                </h3>
                <p className="text-xs font-semibold text-gray-200 truncate max-w-xs">
                  {documentToDelete.display_title || documentToDelete.filename}
                </p>
                <p className="text-[10px] font-mono text-gray-400">
                  ID: {documentToDelete.doc_id}
                </p>
              </div>
            </div>

            <p className="text-xs text-gray-300 leading-relaxed bg-surface-base/80 p-3.5 rounded-2xl border border-surface-border">
              You are about to permanently remove: <strong className="text-white">{documentToDelete.display_title || documentToDelete.filename}</strong>.<br />
              This will remove the document record, uploaded file, processed artifacts, and indexed vectors. This action cannot be undone.
            </p>

            {deleteError && (
              <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
                <AlertCircle size={15} className="text-rose-400 shrink-0 mt-0.5" />
                <span>{deleteError}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setDocumentToDelete(null);
                  setDeleteError(null);
                }}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl bg-surface-base hover:bg-surface-card border border-surface-border text-xs font-semibold text-gray-300 hover:text-white transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 border border-rose-500 text-xs font-semibold text-white transition shadow-lg shadow-rose-600/20 disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <Loader2 size={13} className="animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 size={13} />
                    <span>Delete Document</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
