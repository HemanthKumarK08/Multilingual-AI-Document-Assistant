"""
Unit Tests for Context Construction and Budgeting (Phase 5)
"""

import pytest
from app.services.rag.context_builder import build_context_package
from app.services.retrieval.models import CandidateChunk


class TestContextBuilderUnit:
    def test_build_context_package_structure(self):
        cands = [
            CandidateChunk(
                chunk_id="doc_0001_p01_c01",
                doc_id="doc_0001",
                filename="attendance.pdf",
                page_number=1,
                section_title="1.1 Minimum Attendance",
                text_content="Students must maintain 75% attendance.",
            ),
            CandidateChunk(
                chunk_id="doc_0001_p02_c01",
                doc_id="doc_0001",
                filename="attendance.pdf",
                page_number=2,
                section_title="1.2 Condonation",
                text_content="Medical condonation is available up to 10%.",
            ),
        ]

        pkg = build_context_package(cands, max_chunks=5, max_characters=1000)

        assert len(pkg.selected_chunks) == 2
        assert len(pkg.sources) == 2
        assert "[Source 1]" in pkg.serialized_context
        assert "[Source 2]" in pkg.serialized_context
        assert "attendance.pdf" in pkg.serialized_context
        assert "Page: 1" in pkg.serialized_context
        assert pkg.truncated is False

    def test_character_budget_limit(self):
        long_cand = CandidateChunk(
            chunk_id="c_long",
            doc_id="d_long",
            filename="long.pdf",
            page_number=1,
            text_content="A" * 500,
        )
        cands = [long_cand, long_cand]

        pkg = build_context_package(cands, max_chunks=5, max_characters=300)
        assert pkg.total_characters <= 600
        assert pkg.truncated is True
