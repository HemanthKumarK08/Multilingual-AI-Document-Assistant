"""
Validation Functions for Generated Vector Embeddings (Phase 4)
"""

from typing import List
import math
from app.services.embeddings.exceptions import (
    DimensionMismatchError,
    EmbeddingValidationError,
)


def validate_vector(vector: List[float], expected_dim: int, index: int | None = None) -> None:
    """Validates that a vector has the correct dimension and finite float values."""
    if len(vector) != expected_dim:
        idx_str = f" at index {index}" if index is not None else ""
        raise DimensionMismatchError(
            f"Embedding vector{idx_str} has dimension {len(vector)}, expected {expected_dim}."
        )

    for i, val in enumerate(vector):
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            idx_str = f" at index {index}" if index is not None else ""
            raise EmbeddingValidationError(
                f"Embedding vector{idx_str} contains invalid numeric value at element {i}: {val}"
            )


def validate_batch_embeddings(
    vectors: List[List[float]],
    expected_count: int,
    expected_dim: int,
) -> None:
    """Validates an entire batch of vectors against shape and numerical constraints."""
    if len(vectors) != expected_count:
        raise EmbeddingValidationError(
            f"Output vector count ({len(vectors)}) != expected count ({expected_count})."
        )

    for idx, vec in enumerate(vectors):
        validate_vector(vec, expected_dim, index=idx)
