"""
Pydantic Data Models for Persistent Vector Store (Phase 4)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator

from app.services.vector_store.constants import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_DISTANCE_METRIC,
    DEFAULT_PERSIST_DIRECTORY,
    DEFAULT_VECTOR_INDEX_VERSION,
    SUPPORTED_DISTANCE_METRICS,
)
from app.services.vector_store.exceptions import VectorStoreError


class VectorStoreConfig(BaseModel):
    """Configuration hyperparameters for ChromaDB vector store."""
    persist_directory: str = Field(default=DEFAULT_PERSIST_DIRECTORY)
    collection_name: str = Field(default=DEFAULT_COLLECTION_NAME, min_length=1)
    distance_metric: str = Field(default=DEFAULT_DISTANCE_METRIC)
    index_version: int = Field(default=DEFAULT_VECTOR_INDEX_VERSION, ge=1)

    @model_validator(mode="after")
    def validate_distance_metric(self) -> "VectorStoreConfig":
        if self.distance_metric.lower() not in SUPPORTED_DISTANCE_METRICS:
            raise VectorStoreError(
                f"Unsupported distance metric '{self.distance_metric}'. Supported: {SUPPORTED_DISTANCE_METRICS}"
            )
        return self


class VectorRecord(BaseModel):
    """Container for an indexed chunk vector and its retrieval metadata in ChromaDB."""
    id: str = Field(description="Deterministic chunk_id: {doc_id}:p{page}:c{idx}")
    embedding: List[float] = Field(description="Dense embedding vector")
    document: str = Field(description="Exact chunk text_content for retrieval context")
    metadata: Dict[str, Any] = Field(description="Flat provenance metadata dictionary")


class IndexStats(BaseModel):
    """Current statistics of the persistent vector collection."""
    collection_name: str
    persist_directory: str
    total_records: int
    dimension: int
    distance_metric: str
    index_version: int
    embedding_model_name: str


class StaleRecordReport(BaseModel):
    """Diagnostics for stale or orphaned vectors in ChromaDB."""
    total_existing_in_collection: int
    total_expected_in_corpus: int
    stale_count: int
    stale_chunk_ids: List[str] = Field(default_factory=list)
    missing_count: int
    missing_chunk_ids: List[str] = Field(default_factory=list)


class IndexRunReport(BaseModel):
    """Machine-readable summary report for a batch indexing execution."""
    run_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_directory: str
    persist_directory: str
    collection_name: str
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
    chunks_indexed: int
    chunks_updated: int
    chunks_skipped: int
    chunks_failed: int
    stale_records_detected: int
    stale_records_removed: int
    embedding_elapsed_seconds: float
    indexing_elapsed_seconds: float
    total_elapsed_seconds: float
    validation_status: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
