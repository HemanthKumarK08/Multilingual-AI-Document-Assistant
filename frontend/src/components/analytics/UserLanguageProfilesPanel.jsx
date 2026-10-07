import React, { useState } from 'react';
import { Users, UserCheck, Shield, ChevronLeft, ChevronRight, Lock } from 'lucide-react';

export default function UserLanguageProfilesPanel({ users }) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  const profiles = users?.user_language_profiles || [];
  const topUsers = users?.top_anonymous_users || [];
  const totalUsers = users?.total_unique_users || 0;

  const totalPages = Math.max(1, Math.ceil(topUsers.length / pageSize));
  const displayedUsers = topUsers.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="bg-slate-850/80 border border-slate-750/70 rounded-2xl p-5 shadow-lg backdrop-blur-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-sky-400" />
            <h2 className="text-lg font-bold text-slate-100">User Language Preference & Anonymous Activity</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Aggregated bilingual adoption profiles and privacy-safe anonymous session telemetry
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          <Lock className="w-3.5 h-3.5" />
          Zero-PII Compliance Verified
        </div>
      </div>

      {/* Part 1: User Language Preference Breakdown */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-1.5">
          <UserCheck className="w-4 h-4 text-indigo-400" />
          Aggregated User Linguistic Profiles
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {profiles.map((prof, idx) => (
            <div
              key={idx}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 hover:border-slate-700 transition-colors"
            >
              <span className="text-slate-400 text-[11px] font-medium block truncate" title={prof.profile}>
                {prof.profile}
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-lg font-bold text-slate-100 font-mono">{prof.user_count}</span>
                <span className="text-xs font-semibold text-indigo-400 font-mono">
                  {prof.percentage != null ? `${prof.percentage.toFixed(0)}%` : '0%'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Part 2: Anonymous User / Session Telemetry Table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-sky-400" />
            Anonymous User & Session Activity Matrix
          </h3>
          <span className="text-xs text-slate-400">
            Showing {topUsers.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} -{' '}
            {Math.min(currentPage * pageSize, topUsers.length)} of {topUsers.length} users
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-750">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 text-[11px] uppercase font-semibold border-b border-slate-750">
              <tr>
                <th className="py-2.5 px-4">Anonymous User ID</th>
                <th className="py-2.5 px-3 text-right">Queries</th>
                <th className="py-2.5 px-3">Languages Used</th>
                <th className="py-2.5 px-3 text-right">Docs Accessed</th>
                <th className="py-2.5 px-3 text-right">Grounded Rate</th>
                <th className="py-2.5 px-3 text-right">Fallback Rate</th>
                <th className="py-2.5 px-3 text-right">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40">
              {displayedUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500">
                    No anonymous user records found in telemetry store.
                  </td>
                </tr>
              ) : (
                displayedUsers.map((u, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-4 font-mono font-semibold text-sky-300">
                      {u.anonymous_user_id || 'ANON-SESSION'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-100">
                      {u.query_count}
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex flex-wrap gap-1">
                        {u.languages_used && u.languages_used.map(lang => (
                          <span
                            key={lang}
                            className="px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-300 uppercase"
                          >
                            {lang}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                      {u.documents_accessed ?? 1}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-emerald-400">
                      {u.grounded_rate != null ? `${u.grounded_rate.toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-rose-400">
                      {u.fallback_rate != null ? `${u.fallback_rate.toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                      {u.avg_latency_ms != null ? `${Math.round(u.avg_latency_ms)} ms` : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-end gap-2 mt-3 text-xs">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-slate-400 font-mono">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
