"""
Pydantic Data Models for Page-Aware Chunking Pipeline (Phase 3)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator

from app.services.chunking.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_MINIMUM_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
    DEFAULT_SEPARATORS,
)
from app.services.chunking.exceptions import InvalidChunkConfigError


class ChunkingConfig(BaseModel):
    """Configuration hyperparameters for recursive chunker."""
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, ge=10, le=MAX_CHUNK_SIZE)
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, ge=0)
    minimum_chunk_size: int = Field(default=DEFAULT_MINIMUM_CHUNK_SIZE, ge=1)
    separators: List[str] = Field(default_factory=lambda: list(DEFAULT_SEPARATORS))

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise InvalidChunkConfigError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly less than chunk_size ({self.chunk_size})"
            )
        return self


class DocumentChunk(BaseModel):
    """
    Standardized atomic chunk data model preserving full source provenance.
    Contains all 20 required provenance attributes.
    """
    chunk_id: str = Field(description="Deterministic stable ID: {doc_id}:p{page_number}:c{chunk_index}")
    doc_id: str
    file_hash_sha256: str
    filename: str
    category: str
    language: str
    script: str
    page_number: int = Field(ge=1, description="1-indexed physical or logical page number")
    section_title: Optional[str] = None
    heading_level: Optional[int] = None
    chunk_index: int = Field(ge=0, description="0-indexed document-global sequential index")
    text_content: str
    text_length: int
    source_start_offset: int = Field(ge=0, description="Inclusive start character offset in source unit")
    source_end_offset: int = Field(ge=0, description="Exclusive end character offset in source unit")
    source_unit_index: int = Field(ge=0, description="0-indexed source page/unit sequence")
    parser_name: str
    parser_version: str
    version: str
    extraction_notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_text_and_offsets(self) -> "DocumentChunk":
        if self.text_length != len(self.text_content):
            raise ValueError(
                f"text_length ({self.text_length}) must match actual character length ({len(self.text_content)})"
            )
        if self.source_start_offset > self.source_end_offset:
            raise ValueError(
                f"source_start_offset ({self.source_start_offset}) cannot exceed source_end_offset ({self.source_end_offset})"
            )
        return self


class ChunkedDocumentArtifact(BaseModel):
    """Top-level serialized JSON structure for data/processed/{doc_id}_chunks.json."""
    schema_version: str = "1.0"
    chunking_config: ChunkingConfig
    source_document: Dict[str, Any]
    total_chunks: int
    total_source_characters: int = 0
    total_chunk_characters: int = 0
    chunks: List[DocumentChunk]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DocumentChunkSummary(BaseModel):
    """Summary record for a single document within a batch chunking run."""
    doc_id: str
    status: str
    category: str = "general"
    language: str = "en"
    script: str = "Latin"
    page_count: int = 1
    chunk_count: int = 0
    source_character_count: int = 0
    chunk_character_count: int = 0
    avg_chunk_length: float = 0.0
    min_chunk_length: int = 0
    max_chunk_length: int = 0
    duration_ms: float = 0.0
    artifact_path: Optional[str] = None
    error_message: Optional[str] = None


class ChunkingReport(BaseModel):
    """Machine-readable summary report for batch corpus chunking."""
    execution_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_discovered_documents: int
    total_successful: int
    total_failed: int
    total_chunks_generated: int
    total_source_characters: int
    total_chunk_characters: int
    overall_avg_chunk_length: float = 0.0
    total_duration_seconds: float
    documents: List[DocumentChunkSummary]
