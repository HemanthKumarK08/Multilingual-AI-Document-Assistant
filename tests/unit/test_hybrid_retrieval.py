"""
Unit Tests for Candidate Deduplication and Hybrid Score Fusion (Phase 5)
"""

import pytest
from app.services.retrieval.deduplication import deduplicate_candidates
from app.services.retrieval.hybrid import fuse_hybrid_scores
from app.services.retrieval.models import CandidateChunk


class TestHybridRetrievalUnit:
    def test_deduplication_merges_methods_and_scores(self):
        c1_dense = CandidateChunk(
            chunk_id="chunk_1",
            doc_id="doc_1",
            text_content="Content 1",
            filename="file1.pdf",
            dense_score=0.90,
            retrieval_methods=["dense"],
        )
        c1_lexical = CandidateChunk(
            chunk_id="chunk_1",
            doc_id="doc_1",
            text_content="Content 1",
            filename="file1.pdf",
            lexical_score=0.70,
            retrieval_methods=["lexical"],
        )
        c2 = CandidateChunk(
            chunk_id="chunk_2",
            doc_id="doc_2",
            text_content="Content 2",
            filename="file2.pdf",
            dense_score=0.80,
            retrieval_methods=["dense"],
        )

        deduped = deduplicate_candidates([c1_dense, c1_lexical, c2])
        assert len(deduped) == 2

        merged_c1 = next(c for c in deduped if c.chunk_id == "chunk_1")
        assert merged_c1.dense_score == 0.90
        assert merged_c1.lexical_score == 0.70
        assert "dense" in merged_c1.retrieval_methods
        assert "lexical" in merged_c1.retrieval_methods

    def test_fuse_hybrid_scores_weighted(self):
        dense_list = [
            CandidateChunk(
                chunk_id="c1",
                doc_id="d1",
                text_content="A",
                filename="a.pdf",
                dense_score=1.0,
                retrieval_methods=["dense"],
            ),
            CandidateChunk(
                chunk_id="c2",
                doc_id="d2",
                text_content="B",
                filename="b.pdf",
                dense_score=0.5,
                retrieval_methods=["dense"],
            ),
        ]
        lexical_list = [
            CandidateChunk(
                chunk_id="c2",
                doc_id="d2",
                text_content="B",
                filename="b.pdf",
                lexical_score=1.0,
                retrieval_methods=["lexical"],
            ),
            CandidateChunk(
                chunk_id="c3",
                doc_id="d3",
                text_content="C",
                filename="c.pdf",
                lexical_score=0.8,
                retrieval_methods=["lexical"],
            ),
        ]

        # Weights: dense=0.7, lexical=0.3
        # c1: 0.7*1.0 + 0.3*0.0 = 0.70
        # c2: 0.7*0.5 + 0.3*1.0 = 0.35 + 0.30 = 0.65
        # c3: 0.7*0.0 + 0.3*0.8 = 0.24
        fused = fuse_hybrid_scores(dense_list, lexical_list, dense_weight=0.7, lexical_weight=0.3)

        assert len(fused) == 3
        assert fused[0].chunk_id == "c1"
        assert fused[0].hybrid_score == pytest.approx(0.70, rel=1e-2)
        assert fused[1].chunk_id == "c2"
        assert fused[1].hybrid_score == pytest.approx(0.65, rel=1e-2)
        assert fused[2].chunk_id == "c3"
        assert fused[2].hybrid_score == pytest.approx(0.24, rel=1e-2)
