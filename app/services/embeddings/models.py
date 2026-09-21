"""
Pydantic Data Models for Multilingual Embedding Generation (Phase 4)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator

from app.services.embeddings.constants import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_DEVICE,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MAX_LENGTH,
    DEFAULT_EMBEDDING_NORMALIZE,
    MIN_BATCH_SIZE,
    MAX_BATCH_SIZE_LIMIT,
)
from app.services.embeddings.exceptions import InvalidInputError


class EmbeddingConfig(BaseModel):
    """Configuration hyperparameters for embedding generation."""
    model_name: str = Field(default=DEFAULT_EMBEDDING_MODEL, min_length=1)
    dimension: int = Field(default=DEFAULT_EMBEDDING_DIMENSION, ge=1)
    device: str = Field(default=DEFAULT_EMBEDDING_DEVICE)
    batch_size: int = Field(default=DEFAULT_EMBEDDING_BATCH_SIZE, ge=MIN_BATCH_SIZE, le=MAX_BATCH_SIZE_LIMIT)
    max_length: int = Field(default=DEFAULT_EMBEDDING_MAX_LENGTH, ge=1)
    normalize: bool = Field(default=DEFAULT_EMBEDDING_NORMALIZE)
    model_cache_dir: Optional[str] = None

    @model_validator(mode="after")
    def validate_config(self) -> "EmbeddingConfig":
        if self.batch_size < 1:
            raise InvalidInputError("batch_size must be positive")
        if self.dimension < 1:
            raise InvalidInputError("dimension must be positive")
        return self


class EmbeddedChunk(BaseModel):
    """Standardized representation of a single chunk paired with its embedding vector."""
    chunk_id: str
    doc_id: str
    file_hash_sha256: str
    filename: str
    category: str
    language: str
    script: str
    page_number: int
    section_title: Optional[str] = None
    heading_level: Optional[int] = None
    chunk_index: int
    text_content: str
    text_length: int
    source_start_offset: int
    source_end_offset: int
    source_unit_index: int
    parser_name: str
    parser_version: str
    version: str
    extraction_notes: List[str] = Field(default_factory=list)
    
    # Embedding provenance
    embedding: List[float] = Field(description="Dense vector embedding")
    embedding_model_name: str
    embedding_dimension: int
    embedding_device: str
    embedding_normalized: bool
    vector_index_version: int = 1


class EmbeddingBatchResult(BaseModel):
    """Result of embedding a batch of chunks."""
    total_texts: int
    dimension: int
    embeddings: List[List[float]]
    elapsed_seconds: float


class EmbeddingRunReport(BaseModel):
    """Machine-readable summary report for corpus embedding."""
    run_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    embedding_model_name: str
    embedding_dimension: int
    embedding_device: str
    embedding_batch_size: int
    embedding_normalized: bool
    documents_discovered: int
    documents_succeeded: int
    documents_failed: int
    chunks_discovered: int
    chunks_embedded: int
    chunks_failed: int
    total_elapsed_seconds: float
    document_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
