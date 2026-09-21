"""
Unit Tests for Evidence Sufficiency Gate (Phase 5)
"""

import pytest
from app.services.rag.constants import REASON_LOW_RELEVANCE, REASON_NO_CANDIDATES
from app.services.rag.evidence_gate import evaluate_evidence_sufficiency
from app.services.retrieval.models import CandidateChunk, ProcessedQuery, RetrievalResult


class TestEvidenceGateUnit:
    def test_empty_candidates_rejection(self):
        pq = ProcessedQuery(raw_query="query", normalized_query="query")
        rr = RetrievalResult(query=pq, candidates=[])

        gate_res = evaluate_evidence_sufficiency(rr, min_score=0.35)
        assert gate_res.is_sufficient is False
        assert gate_res.reason == REASON_NO_CANDIDATES
        assert len(gate_res.selected_candidates) == 0

    def test_low_score_rejection(self):
        pq = ProcessedQuery(raw_query="query", normalized_query="query")
        cand = CandidateChunk(
            chunk_id="c1",
            doc_id="d1",
            filename="f1.pdf",
            text_content="Sample text content for low score test.",
            page_number=1,
            rerank_score=0.20,
        )
        rr = RetrievalResult(query=pq, candidates=[cand])

        gate_res = evaluate_evidence_sufficiency(rr, min_score=0.35)
        assert gate_res.is_sufficient is False
        assert gate_res.reason == REASON_LOW_RELEVANCE
        assert gate_res.observed_best_score == pytest.approx(0.20, rel=1e-2)

    def test_sufficient_candidate_acceptance(self):
        pq = ProcessedQuery(raw_query="query", normalized_query="query")
        cand = CandidateChunk(
            chunk_id="c1",
            doc_id="d1",
            filename="f1.pdf",
            text_content="Valid evidence content.",
            page_number=1,
            rerank_score=0.65,
        )
        rr = RetrievalResult(query=pq, candidates=[cand])

        gate_res = evaluate_evidence_sufficiency(rr, min_score=0.35)
        assert gate_res.is_sufficient is True
        assert gate_res.reason is None
        assert len(gate_res.selected_candidates) == 1
