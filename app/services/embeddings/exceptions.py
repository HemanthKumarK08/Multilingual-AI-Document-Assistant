"""
Typed Exception Hierarchy for Multilingual Embedding Subsystem
"""


class EmbeddingError(Exception):
    """Base exception for all embedding-related errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ModelLoadError(EmbeddingError):
    """Raised when the embedding model fails to initialize or load weights."""
    pass


class DimensionMismatchError(EmbeddingError):
    """Raised when generated embedding vectors do not match the expected dimension."""
    pass


class InvalidInputError(EmbeddingError):
    """Raised when input texts are invalid (e.g. empty, NaN, or improper batch)."""
    pass


class EmbeddingValidationError(EmbeddingError):
    """Raised when generated vectors fail numeric or shape validation."""
    pass
