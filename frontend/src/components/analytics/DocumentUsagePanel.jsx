import React from 'react';
import { FileText } from 'lucide-react';

export default function DocumentUsagePanel({ documents }) {
  const docList = Array.isArray(documents?.documents) ? documents.documents : [];

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-teal-400" />
            <h2 className="text-lg font-bold text-slate-100">Document Usage</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Most frequently referenced documents across institutional QA queries
          </p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 self-start sm:self-auto">
          {docList.length} Documents Indexed
        </span>
      </div>

      {docList.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs">
          No document usage data available yet.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 text-[11px] uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">#</th>
                <th className="py-3 px-4">Document Title / Reference</th>
                <th className="py-3 px-4 text-right">Queries / Uses</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-slate-900/40">
              {docList.map((row, idx) => (
                <tr key={row.document_id || idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-500 w-12">
                    {idx + 1}
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-200">
                    <div className="flex items-center gap-2.5">
                      <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="font-semibold text-slate-100">
                        {row.display_title || row.document_id}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-teal-300">
                    {(row.query_count ?? 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
