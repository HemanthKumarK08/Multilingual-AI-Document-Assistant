import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Layers,
  ArrowRight,
  Loader2,
  FileType,
} from 'lucide-react';
import { apiService } from '../services/api';

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md'];
const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

const CATEGORIES = [
  { value: 'academic_regulations', label: 'Academic Regulations' },
  { value: 'examination_guidelines', label: 'Examination Guidelines' },
  { value: 'attendance', label: 'Attendance Policies' },
  { value: 'scholarships', label: 'Scholarships & Aid' },
  { value: 'hostel', label: 'Hostel & Residential' },
  { value: 'placements', label: 'Placements & Internships' },
];

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DocumentUploadZone({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [displayTitle, setDisplayTitle] = useState('');
  const [category, setCategory] = useState('academic_regulations');
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  function validateFile(file) {
    if (!file) return 'No file selected.';
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format '${ext}'. Please upload a PDF, DOCX, TXT, or MD document.`;
    }
    if (file.size === 0) {
      return 'Selected file is empty (0 bytes).';
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File size (${formatBytes(file.size)}) exceeds the maximum allowed limit of 15 MB.`;
    }
    return null;
  }

  function handleFileSelection(file) {
    setSuccessMessage(null);
    setErrorMessage(null);

    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setDisplayTitle(file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '));
  }

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }

  function handleInputChange(e) {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  }

  async function handleUpload() {
    if (!selectedFile) return;

    setUploading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await apiService.uploadDocument(
        selectedFile,
        displayTitle.trim() || selectedFile.name,
        category,
        '1.0',
        true
      );

      setSuccessMessage({
        title: 'Document Ingested Successfully',
        docId: res.doc_id,
        filename: selectedFile.name,
        pages: res.page_count ?? 1,
        language: res.language || 'en',
      });

      // Clear selection
      setSelectedFile(null);
      setDisplayTitle('');
      if (fileInputRef.current) fileInputRef.current.value = '';

      // Trigger list refresh
      if (onUploadSuccess) {
        onUploadSuccess(res);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Document ingestion failed. Please verify the document format.');
    } finally {
      setUploading(false);
    }
  }

  function clearSelection() {
    setSelectedFile(null);
    setDisplayTitle('');
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  return (
    <div className="space-y-4">
      {/* Upload Drop Zone Card */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative rounded-3xl border-2 border-dashed p-6 sm:p-8 text-center transition-all duration-200 ${
          dragActive
            ? 'border-brand-500 bg-brand-500/10 scale-[1.01]'
            : 'border-surface-border bg-surface-card hover:border-brand-500/40 hover:bg-surface-card/90'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.doc,.txt,.md"
          onChange={handleInputChange}
          className="hidden"
          id="document-file-input"
          disabled={uploading}
        />

        {!selectedFile ? (
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center shadow-lg shadow-brand-500/10">
              <UploadCloud size={28} />
            </div>

            <div className="space-y-1.5 max-w-md mx-auto">
              <h3 className="text-base font-bold text-white">
                Drag and drop your document here
              </h3>
              <p className="text-xs text-gray-400">
                Support institutional files up to 15 MB in PDF, DOCX, TXT, or Markdown formats
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <label
                htmlFor="document-file-input"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs sm:text-sm cursor-pointer transition shadow-md shadow-brand-600/30 active:scale-95"
              >
                <FileType size={16} />
                <span>Browse Files</span>
              </label>
              <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                <span className="px-2 py-0.5 rounded bg-surface-base border border-surface-border font-mono">PDF</span>
                <span className="px-2 py-0.5 rounded bg-surface-base border border-surface-border font-mono">DOCX</span>
                <span className="px-2 py-0.5 rounded bg-surface-base border border-surface-border font-mono">TXT</span>
                <span className="px-2 py-0.5 rounded bg-surface-base border border-surface-border font-mono">MD</span>
              </div>
            </div>
          </div>
        ) : (
          /* Selected File Pre-Upload Form */
          <div className="max-w-xl mx-auto space-y-5 text-left animate-fadeIn">
            <div className="p-4 rounded-2xl bg-surface-base/80 border border-surface-border flex items-center justify-between">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 shrink-0">
                  <FileText size={22} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm font-bold text-white truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-[11px] text-gray-400 font-mono">
                    {formatBytes(selectedFile.size)} • {selectedFile.name.split('.').pop().toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={clearSelection}
                disabled={uploading}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-surface-card transition disabled:opacity-50"
                title="Remove file"
              >
                <X size={18} />
              </button>
            </div>

            {/* Ingestion Options */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <label className="block text-gray-300 font-medium">Display Title</label>
                <input
                  type="text"
                  value={displayTitle}
                  onChange={(e) => setDisplayTitle(e.target.value)}
                  placeholder="Document Title"
                  disabled={uploading}
                  className="w-full px-3 py-2 rounded-xl bg-surface-base border border-surface-border text-white text-xs focus:outline-none focus:border-brand-500 disabled:opacity-50"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-gray-300 font-medium">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={uploading}
                  className="w-full px-3 py-2 rounded-xl bg-surface-base border border-surface-border text-white text-xs focus:outline-none focus:border-brand-500 disabled:opacity-50"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={clearSelection}
                disabled={uploading}
                className="px-4 py-2 rounded-xl bg-surface-base hover:bg-surface-base/80 border border-surface-border text-xs font-medium text-gray-300 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs transition shadow-md shadow-brand-600/30 disabled:opacity-60"
              >
                {uploading ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Ingesting & Parsing...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud size={14} />
                    <span>Upload & Ingest Document</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-start justify-between gap-3 animate-fadeIn">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <p className="font-bold text-emerald-300">{successMessage.title}</p>
              <p className="text-emerald-200/80">
                <span className="font-mono text-white font-semibold">{successMessage.filename}</span> registered under ID{' '}
                <span className="font-mono text-emerald-400 font-bold">{successMessage.docId}</span> ({successMessage.pages} pages, language: {successMessage.language}).
              </p>
            </div>
          </div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-400 hover:text-emerald-200 p-1"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start justify-between gap-3 animate-fadeIn">
          <div className="flex items-start gap-2.5">
            <AlertCircle size={18} className="text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <p className="font-bold text-rose-300">Ingestion Error</p>
              <p className="text-rose-200/90">{errorMessage}</p>
            </div>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-rose-200 p-1"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
