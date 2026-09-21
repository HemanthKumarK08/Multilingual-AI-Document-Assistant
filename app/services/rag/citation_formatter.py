"""
Source Citation Formatting and Extraction Module
"""

import re
from typing import Dict, List, Set, Tuple
from app.services.rag.models import SourceCitation

_CITATION_PATTERN = re.compile(r"\[(?:Source\s*)?(\d+)\]", re.IGNORECASE)


def extract_cited_source_indices(text: str) -> List[int]:
    """Extracts integer source indices from text markers like [Source 1] or [1]."""
    if not text:
        return []
    matches = _CITATION_PATTERN.findall(text)
    indices: List[int] = []
    for m in matches:
        try:
            val = int(m)
            if val not in indices:
                indices.append(val)
        except ValueError:
            continue
    return indices


def resolve_citations(
    answer_text: str,
    available_sources: List[SourceCitation],
) -> Tuple[List[SourceCitation], List[str]]:
    """
    Resolves citation markers in the generated answer against available context sources.
    
    Returns:
        Tuple of (valid_resolved_citations, warnings).
    """
    warnings: List[str] = []
    if not available_sources:
        return [], ["No context sources were available for citation."]

    source_map: Dict[int, SourceCitation] = {}
    for idx, src in enumerate(available_sources, start=1):
        source_map[idx] = src

    cited_indices = extract_cited_source_indices(answer_text)
    
    resolved: List[SourceCitation] = []
    seen_chunk_ids: Set[str] = set()

    for idx in cited_indices:
        if idx in source_map:
            src = source_map[idx]
            if src.chunk_id not in seen_chunk_ids:
                resolved.append(src)
                seen_chunk_ids.add(src.chunk_id)
        else:
            warnings.append(f"Answer cited [Source {idx}], which was not in the provided context.")

    # If the answer contains substantive text but no explicit citation markers at all,
    # associate with all supplied context sources as an explicit fallback attribution.
    if not resolved and not cited_indices and answer_text.strip():
        resolved = list(available_sources)
        warnings.append("Answer lacked explicit citation markers; attached all context sources.")

    return resolved, warnings
