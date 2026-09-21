"""
Retrieval Subsystem Exceptions
"""

class RetrievalError(Exception):
    """Base exception for all retrieval errors."""
    pass

class QueryValidationError(RetrievalError):
    """Raised when user query is invalid, empty, or unprocessable."""
    pass

class DenseRetrievalError(RetrievalError):
    """Raised when dense ChromaDB query fails or collection is incompatible."""
    pass

class LexicalRetrievalError(RetrievalError):
    """Raised when lexical search fails."""
    pass

class HybridFusionError(RetrievalError):
    """Raised when combining candidate scores fails."""
    pass

class RerankingError(RetrievalError):
    """Raised when candidate reranking fails."""
    pass

class FilterError(RetrievalError):
    """Raised when metadata filter syntax or execution is invalid."""
    pass
