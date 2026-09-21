"""
Integration Tests for Grounded RAG Pipeline (Phase 5)
"""

import pytest
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.llm_provider import MockLLMProvider
from app.services.retrieval.coordinator import RetrievalCoordinator


@pytest.fixture(scope="module")
def rag_coordinator():
    ret_coord = RetrievalCoordinator()
    mock_llm = MockLLMProvider(
        canned_response="The minimum required attendance is 75% for all registered courses [Source 1]."
    )
    return RAGCoordinator(retrieval_coordinator=ret_coord, llm_provider=mock_llm)


class TestRAGPipelineIntegration:

    def test_in_domain_grounded_answer(self, rag_coordinator):
        answer = rag_coordinator.answer("What is the minimum attendance requirement in each course?")

        assert answer.grounded is True
        assert answer.fallback_used is False
        assert "75%" in answer.answer_text
        assert len(answer.sources) > 0
        assert answer.sources[0].page_number >= 1

    def test_out_of_domain_deterministic_fallback(self, rag_coordinator):
        answer = rag_coordinator.answer("How do quantum entanglement computers simulate interstellar black holes?")

        assert answer.grounded is False
        assert answer.fallback_used is True
        assert answer.answer_text == "Information Not Found in the provided documents."
        assert len(answer.sources) == 0
