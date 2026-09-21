"""
Typed Exceptions for Chunking Pipeline
"""

class ChunkingError(Exception):
    """Base exception for all chunking-related errors."""
    def __init__(self, message: str, doc_id: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.doc_id = doc_id
        self.details = details or {}

class InvalidChunkConfigError(ChunkingError):
    """Raised when chunk_size or chunk_overlap configuration parameters are invalid."""
    pass

class ChunkValidationError(ChunkingError):
    """Raised when generated chunks fail structural or metadata validation checks."""
    pass

class SourceCoverageError(ChunkingError):
    """Raised when generated chunks fail source text reconstruction or coverage validation."""
    pass

class ArtifactNotFoundError(ChunkingError):
    """Raised when source parsed artifact cannot be discovered on disk."""
    pass
