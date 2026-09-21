"""Chunking service package for the Multilingual AI Document Assistant."""

from app.services.chunking.boundaries import PageAwareBoundaryManager
from app.services.chunking.constants import (
    CHUNK_ID_DELIMITER,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MINIMUM_CHUNK_SIZE,
    DEFAULT_SEPARATORS,
    MAX_CHUNK_SIZE,
)
from app.services.chunking.coordinator import ChunkingCoordinator
from app.services.chunking.exceptions import (
    ArtifactNotFoundError,
    ChunkingError,
    ChunkValidationError,
    InvalidChunkConfigError,
    SourceCoverageError,
)
from app.services.chunking.models import (
    ChunkedDocumentArtifact,
    ChunkingConfig,
    ChunkingReport,
    DocumentChunk,
    DocumentChunkSummary,
)
from app.services.chunking.recursive import RecursiveCharacterChunker
from app.services.chunking.serialization import (
    deserialize_chunked_artifact,
    serialize_chunked_artifact,
)
from app.services.chunking.validator import ChunkValidator

__all__ = [
    "CHUNK_ID_DELIMITER",
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_MINIMUM_CHUNK_SIZE",
    "DEFAULT_SEPARATORS",
    "MAX_CHUNK_SIZE",
    "ArtifactNotFoundError",
    "ChunkValidationError",
    "ChunkedDocumentArtifact",
    "ChunkingConfig",
    "ChunkingCoordinator",
    "ChunkingError",
    "ChunkingReport",
    "DocumentChunk",
    "DocumentChunkSummary",
    "InvalidChunkConfigError",
    "PageAwareBoundaryManager",
    "RecursiveCharacterChunker",
    "SourceCoverageError",
    "deserialize_chunked_artifact",
    "serialize_chunked_artifact",
    "ChunkValidator",
]
