"""
Multilingual Embedding Subsystem Package (Phase 4)
"""

from app.services.embeddings.constants import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_DEVICE,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MAX_LENGTH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_NORMALIZE,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
)
from app.services.embeddings.exceptions import (
    DimensionMismatchError,
    EmbeddingError,
    EmbeddingValidationError,
    InvalidInputError,
    ModelLoadError,
)
from app.services.embeddings.models import (
    EmbeddedChunk,
    EmbeddingBatchResult,
    EmbeddingConfig,
    EmbeddingRunReport,
)
from app.services.embeddings.provider import EmbeddingProvider
from app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
from app.services.embeddings.batching import embed_texts_in_batches
from app.services.embeddings.validation import validate_batch_embeddings, validate_vector
from app.services.embeddings.coordinator import EmbeddingCoordinator

__all__ = [
    "DEFAULT_EMBEDDING_BATCH_SIZE",
    "DEFAULT_EMBEDDING_DEVICE",
    "DEFAULT_EMBEDDING_DIMENSION",
    "DEFAULT_EMBEDDING_MAX_LENGTH",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_EMBEDDING_NORMALIZE",
    "PASSAGE_PREFIX",
    "QUERY_PREFIX",
    "DimensionMismatchError",
    "EmbeddingError",
    "EmbeddingValidationError",
    "InvalidInputError",
    "ModelLoadError",
    "EmbeddedChunk",
    "EmbeddingBatchResult",
    "EmbeddingConfig",
    "EmbeddingRunReport",
    "EmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "embed_texts_in_batches",
    "validate_batch_embeddings",
    "validate_vector",
    "EmbeddingCoordinator",
]
