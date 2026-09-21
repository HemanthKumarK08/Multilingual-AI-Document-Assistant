"""
Unit Tests for Deterministic Heuristic Reranker (Phase 5)
"""

import pytest
from app.services.retrieval.models import CandidateChunk, ProcessedQuery
from app.services.retrieval.reranker import heuristic_rerank


class TestRerankerUnit:
    def test_reranker_phrase_match_and_term_coverage(self):
        pq = ProcessedQuery(
            raw_query="minimum attendance percentage",
            normalized_query="minimum attendance percentage",
        )

        candidates = [
            CandidateChunk(
                chunk_id="c_general",
                doc_id="d1",
                filename="f1.pdf",
                text_content="General guidelines regarding student conduct and library rules.",
                section_title="General Rules",
                hybrid_score=0.75,
            ),
            CandidateChunk(
                chunk_id="c_exact",
                doc_id="d2",
                filename="f2.pdf",
                text_content="The minimum attendance percentage required in each course is 75%.",
                section_title="Attendance Policy",
                hybrid_score=0.70,
            ),
        ]

        reranked = heuristic_rerank(pq, candidates)

        assert len(reranked) == 2
        # c_exact should get coverage bonus, exact phrase match bonus, and section title bonus
        assert reranked[0].chunk_id == "c_exact"
        assert reranked[0].rank == 1
        assert reranked[0].rerank_score > reranked[1].rerank_score

    def test_reranker_preserves_provenance(self):
        pq = ProcessedQuery(raw_query="test", normalized_query="test")
        cand = CandidateChunk(
            chunk_id="c1",
            doc_id="d1",
            filename="f1.pdf",
            page_number=3,
            section_title="Section A",
            file_hash_sha256="abc123hash",
            text_content="This is a test content with sufficient length.",
            hybrid_score=0.5,
        )

        reranked = heuristic_rerank(pq, [cand])
        assert len(reranked) == 1
        assert reranked[0].page_number == 3
        assert reranked[0].file_hash_sha256 == "abc123hash"
        assert reranked[0].section_title == "Section A"
