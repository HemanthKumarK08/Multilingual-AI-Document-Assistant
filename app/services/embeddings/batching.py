"""
Batch Processing Utilities for Embedding Generation (Phase 4)
"""

from typing import List, TypeVar, Generator
import time
from app.services.embeddings.provider import EmbeddingProvider
from app.services.embeddings.models import EmbeddingBatchResult
from app.services.embeddings.exceptions import InvalidInputError, EmbeddingValidationError

T = TypeVar("T")


def chunk_list(items: List[T], batch_size: int) -> Generator[List[T], None, None]:
    """Yields consecutive batches of size `batch_size` from `items`."""
    if batch_size < 1:
        raise InvalidInputError(f"batch_size must be >= 1, got {batch_size}")
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def embed_texts_in_batches(
    provider: EmbeddingProvider,
    texts: List[str],
    batch_size: int | None = None,
) -> EmbeddingBatchResult:
    """
    Embeds a collection of document texts in sequential batches using the provider.
    Guarantees strict input-to-output order preservation.
    """
    if not texts:
        return EmbeddingBatchResult(
            total_texts=0,
            dimension=provider.dimension,
            embeddings=[],
            elapsed_seconds=0.0,
        )

    b_size = batch_size or getattr(provider, "batch_size", 8)
    all_embeddings: List[List[float]] = []
    start_time = time.time()

    for batch in chunk_list(texts, b_size):
        batch_vecs = provider.embed_documents(batch)
        if len(batch_vecs) != len(batch):
            raise EmbeddingValidationError(
                f"Provider returned {len(batch_vecs)} embeddings for batch of {len(batch)} texts."
            )
        all_embeddings.extend(batch_vecs)

    elapsed = time.time() - start_time

    return EmbeddingBatchResult(
        total_texts=len(texts),
        dimension=provider.dimension,
        embeddings=all_embeddings,
        elapsed_seconds=elapsed,
    )
