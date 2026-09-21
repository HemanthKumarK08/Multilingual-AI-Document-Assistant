"""
Integration Tests for Grounding and Citation Consistency (Phase 5)
"""

import pytest
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.llm_provider import MockLLMProvider
from app.services.retrieval.coordinator import RetrievalCoordinator


class TestGroundingValidationIntegration:
    def test_mock_hallucinated_citation_detection(self):
        # LLM returns hallucinated [Source 99] not present in context
        bad_llm = MockLLMProvider(canned_response="This fact is from [Source 99].")
        coord = RAGCoordinator(
            retrieval_coordinator=RetrievalCoordinator(),
            llm_provider=bad_llm,
        )

        answer = coord.answer("What is the attendance requirement?")
        # The warning should capture that Source 99 was not in context
        assert any("Source 99" in w for w in answer.warnings)
