"""
Grounded RAG Pipeline Exceptions
"""

class RAGError(Exception):
    """Base exception for all Grounded RAG errors."""
    pass

class EvidenceGateError(RAGError):
    """Raised when evidence verification fails unexpectedly."""
    pass

class ContextConstructionError(RAGError):
    """Raised when context construction fails."""
    pass

class PromptConstructionError(RAGError):
    """Raised when prompt generation fails."""
    pass

class LLMProviderError(RAGError):
    """Raised when LLM provider invocation fails."""
    pass

class CitationValidationError(RAGError):
    """Raised when LLM citations cannot be validated against supplied context."""
    pass

class GroundingValidationError(RAGError):
    """Raised when answer grounding checks fail."""
    pass
