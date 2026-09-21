import React, { useState } from 'react';
import {
  FileText,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Layers,
} from 'lucide-react';
import CitationCard from './CitationCard';
import EvidenceDrawer from './EvidenceDrawer';

export default function CitationsSection({ citations }) {
  const [expanded, setExpanded] = useState(false);
  const [inspectingCitation, setInspectingCitation] = useState(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="pt-2.5 border-t border-surface-border/60 space-y-2">
      {/* Accordion Toggle Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left py-1 text-xs font-bold text-gray-300 hover:text-white transition group"
      >
        <span className="flex items-center gap-2 text-indigo-300 group-hover:text-indigo-200">
          <FileText size={14} />
          <span>
            Grounded in {citations.length} {citations.length === 1 ? 'Source' : 'Sources'}
          </span>
        </span>
        <div className="flex items-center gap-1 text-[11px] text-gray-400">
          <span>{expanded ? 'Hide' : 'Inspect'}</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {/* Citations List Grid */}
      {expanded && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 animate-fadeIn">
          {citations.map((cite, idx) => (
            <CitationCard
              key={idx}
              citation={cite}
              onInspect={(c) => setInspectingCitation(c)}
            />
          ))}
        </div>
      )}

      {/* Evidence Modal / Drawer */}
      {inspectingCitation && (
        <EvidenceDrawer
          citation={inspectingCitation}
          onClose={() => setInspectingCitation(null)}
        />
      )}
    </div>
  );
}
