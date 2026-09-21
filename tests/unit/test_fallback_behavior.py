"""
Unit Tests for Deterministic Fallback Behavior (Phase 5)
"""

import pytest
from app.services.rag.fallback import create_fallback_answer


class TestFallbackBehaviorUnit:
    def test_create_fallback_answer_properties(self):
        answer = create_fallback_answer(
            query_id="q_123",
            reason="NO_CANDIDATES",
            response_language="en",
        )

        assert answer.query_id == "q_123"
        assert answer.answer_text == "Information Not Found in the provided documents."
        assert answer.grounded is False
        assert answer.fallback_used is True
        assert answer.fallback_reason == "NO_CANDIDATES"
        assert len(answer.sources) == 0
