"""
Global Pytest Configuration and LLM Mocking Fixture
Separates deterministic offline regression testing from external live LLM API calls.
"""

import pytest
from app.services.rag.llm_provider import MockLLMProvider
import app.api.routes.qa as qa_route


@pytest.fixture(autouse=True)
def configure_test_llm_provider(request):
    """
    Ensure deterministic offline execution for standard regression tests.
    Tests marked with @pytest.mark.live_llm execute against live LLM providers.
    All other tests use the deterministic offline MockLLMProvider to prevent
    rate-limiting (HTTP 429) failures during automated regression runs.
    """
    if "live_llm" in request.keywords:
        yield
    else:
        orig = qa_route._rag_coordinator.llm_provider
        qa_route._rag_coordinator.llm_provider = MockLLMProvider()
        yield
        qa_route._rag_coordinator.llm_provider = orig
