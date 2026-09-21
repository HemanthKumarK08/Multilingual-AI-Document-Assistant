"""
Unit Tests for Citation Extraction and Validation (Phase 5)
"""

import pytest
from app.services.rag.citation_formatter import extract_cited_source_indices, resolve_citations
from app.services.rag.models import SourceCitation


class TestCitationFormatterUnit:
    def test_extract_cited_source_indices(self):
        text = "According to policy, 75% attendance is required [Source 1] and condonation is up to 10% [2]."
        indices = extract_cited_source_indices(text)
        assert indices == [1, 2]

    def test_resolve_citations_matching(self):
        sources = [
            SourceCitation(
                source_id="Source 1",
                chunk_id="c1",
                doc_id="d1",
                filename="f1.pdf",
                page_number=1,
            ),
            SourceCitation(
                source_id="Source 2",
                chunk_id="c2",
                doc_id="d2",
                filename="f2.pdf",
                page_number=2,
            ),
        ]

        text = "Minimum attendance is 75% [Source 1]."
        resolved, warnings = resolve_citations(text, sources)

        assert len(resolved) == 1
        assert resolved[0].chunk_id == "c1"
        assert resolved[0].page_number == 1
        assert len(warnings) == 0

    def test_resolve_citations_unknown_index(self):
        sources = [
            SourceCitation(
                source_id="Source 1",
                chunk_id="c1",
                doc_id="d1",
                filename="f1.pdf",
                page_number=1,
            )
        ]

        text = "Claim referencing unknown source [Source 5]."
        resolved, warnings = resolve_citations(text, sources)

        assert len(warnings) > 0
        assert any("Source 5" in w for w in warnings)
