"""
Integration Tests for Retrieval Pipeline with Real Vector Store and Lexical Index (Phase 5)
"""

import pytest
from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.models import RetrievalFilter


@pytest.fixture(scope="module")
def coordinator():
    return RetrievalCoordinator()


class TestRetrievalPipelineIntegration:

    def test_english_query_retrieval(self, coordinator):
        result = coordinator.retrieve(
            raw_query="What is the minimum attendance requirement in each course?",
            final_top_k=3,
        )

        assert result.query.language in ["en", "und"]
        assert len(result.candidates) > 0
        assert result.total_candidates_found > 0
        assert result.latency_ms > 0

        top_cand = result.candidates[0]
        assert top_cand.chunk_id is not None
        assert top_cand.page_number >= 1
        assert top_cand.filename != ""

    def test_hindi_multilingual_query_retrieval(self, coordinator):
        result = coordinator.retrieve(
            raw_query="कक्षा में न्यूनतम उपस्थिति की आवश्यकता क्या है?",
            language="hi",
            final_top_k=3,
        )

        assert result.query.script == "Devanagari"
        assert len(result.candidates) > 0

    def test_kannada_multilingual_query_retrieval(self, coordinator):
        result = coordinator.retrieve(
            raw_query="ಹಾಜರಾತಿ ನಿಯಮಗಳು ಯಾವುವು?",
            language="kn",
            final_top_k=3,
        )

        assert result.query.script == "Kannada"
        assert len(result.candidates) > 0

    def test_telugu_multilingual_query_retrieval(self, coordinator):
        result = coordinator.retrieve(
            raw_query="హాజరు నిబంధనలు ఏమిటి?",
            language="te",
            final_top_k=3,
        )

        assert result.query.script == "Telugu"
        assert len(result.candidates) > 0

    def test_deterministic_repeated_query_ordering(self, coordinator):
        q = "What is the fee payment deadline?"
        r1 = coordinator.retrieve(raw_query=q, final_top_k=5)
        r2 = coordinator.retrieve(raw_query=q, final_top_k=5)

        assert len(r1.candidates) == len(r2.candidates)
        for c1, c2 in zip(r1.candidates, r2.candidates):
            assert c1.chunk_id == c2.chunk_id
            assert c1.rank == c2.rank
