"""
Grounded RAG Pipeline Package (Phase 5)
"""

from app.services.rag.answer_generator import generate_grounded_answer
from app.services.rag.citation_formatter import extract_cited_source_indices, resolve_citations
from app.services.rag.context_builder import build_context_package
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.evidence_gate import evaluate_evidence_sufficiency
from app.services.rag.exceptions import (
    CitationValidationError,
    ContextConstructionError,
    EvidenceGateError,
    GroundingValidationError,
    LLMProviderError,
    PromptConstructionError,
    RAGError,
)
from app.services.rag.fallback import create_fallback_answer
from app.services.rag.llm_provider import (
    GeminiLLMProvider,
    LLMProvider,
    MockLLMProvider,
    OllamaLLMProvider,
    get_llm_provider,
)
from app.services.rag.models import (
    ContextPackage,
    EvidenceGateResult,
    GroundedAnswer,
    SourceCitation,
)
from app.services.rag.prompt_builder import build_grounded_prompt
from app.services.rag.validation import validate_grounded_answer

__all__ = [
    "RAGCoordinator",
    "evaluate_evidence_sufficiency",
    "build_context_package",
    "build_grounded_prompt",
    "generate_grounded_answer",
    "resolve_citations",
    "extract_cited_source_indices",
    "create_fallback_answer",
    "validate_grounded_answer",
    "get_llm_provider",
    "LLMProvider",
    "MockLLMProvider",
    "GeminiLLMProvider",
    "OllamaLLMProvider",
    "ContextPackage",
    "EvidenceGateResult",
    "GroundedAnswer",
    "SourceCitation",
    "RAGError",
    "EvidenceGateError",
    "ContextConstructionError",
    "PromptConstructionError",
    "LLMProviderError",
    "CitationValidationError",
    "GroundingValidationError",
]
