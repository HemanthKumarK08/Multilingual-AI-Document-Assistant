"""
Typed Exception Hierarchy for Persistent Vector Store Subsystem (Phase 4)
"""


class VectorStoreError(Exception):
    """Base exception for all vector store errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CollectionCompatibilityError(VectorStoreError):
    """Raised when an existing vector collection has incompatible metadata/dimensions."""
    pass


class StaleRecordError(VectorStoreError):
    """Raised when stale or orphaned records violate indexing integrity."""
    pass


class IndexingError(VectorStoreError):
    """Raised when upsert or index operation fails."""
    pass


class MetadataSerializationError(VectorStoreError):
    """Raised when chunk metadata cannot be formatted for ChromaDB."""
    pass
