"""
Typed Exceptions for Document Ingestion Pipeline
"""

class IngestionError(Exception):
    """Base exception for all ingestion-related failures."""
    def __init__(self, message: str, doc_id: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.doc_id = doc_id
        self.details = details or {}

class FileNotFoundIngestionError(IngestionError):
    """Raised when source file does not exist on disk."""
    pass

class UnsupportedFileTypeError(IngestionError):
    """Raised when file extension or MIME type is not supported."""
    pass

class FileSizeExceededError(IngestionError):
    """Raised when file size exceeds maximum permitted threshold."""
    pass

class EmptyFileError(IngestionError):
    """Raised when file is 0 bytes or has no readable content."""
    pass

class CorruptedFileError(IngestionError):
    """Raised when file binary is malformed or unreadable."""
    pass

class DuplicateDocumentError(IngestionError):
    """Raised when a document with identical SHA-256 hash already exists."""
    def __init__(self, message: str, existing_doc_id: str, sha256_hash: str):
        super().__init__(message, doc_id=existing_doc_id, details={"sha256": sha256_hash})
        self.existing_doc_id = existing_doc_id
        self.sha256_hash = sha256_hash

class ParserExecutionError(IngestionError):
    """Raised when parser fails to extract structure or content."""
    pass

class DatabasePersistenceError(IngestionError):
    """Raised when saving metadata or job status to SQLite fails."""
    pass
