"""
Unit Tests for Retrieval Data Models and Filters (Phase 5)
"""

import pytest
from app.services.retrieval.exceptions import FilterError
from app.services.retrieval.filters import build_chroma_filter, validate_filter
from app.services.retrieval.models import CandidateChunk, ProcessedQuery, RetrievalFilter, RetrievalResult
from app.services.retrieval.validation import validate_candidate_chunk, validate_retrieval_result


class TestRetrievalModelsUnit:
    def test_retrieval_filter_single_clause(self):
        rf = RetrievalFilter(doc_id="DOC-ATTN-001")
        clause = rf.to_chroma_where()
        assert clause == {"doc_id": {"$eq": "DOC-ATTN-001"}}

    def test_retrieval_filter_multiple_clauses(self):
        rf = RetrievalFilter(doc_id="DOC-ATTN-001", category="academic", page_number=2)
        clause = rf.to_chroma_where()
        assert "$and" in clause
        assert len(clause["$and"]) == 3

    def test_invalid_filter_page_number_raises(self):
        rf = RetrievalFilter(page_number=0)
        with pytest.raises(FilterError):
            validate_filter(rf)

    def test_candidate_chunk_validation(self):
        valid_chunk = CandidateChunk(
            chunk_id="chunk_001",
            doc_id="doc_001",
            text_content="Sample text",
            filename="sample.pdf",
            page_number=1,
            dense_score=0.85,
        )
        is_valid, errors = validate_candidate_chunk(valid_chunk)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_candidate_chunk_detected(self):
        invalid_chunk = CandidateChunk(
            chunk_id="",
            doc_id="",
            text_content="",
            filename="",
            page_number=-1,
            dense_score=1.5,
        )
        is_valid, errors = validate_candidate_chunk(invalid_chunk)
        assert is_valid is False
        assert len(errors) >= 4
