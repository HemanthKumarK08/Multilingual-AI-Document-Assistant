"""
Grounded RAG Pipeline Data Models
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.services.retrieval.models import CandidateChunk


class SourceCitation(BaseModel):
    """Structured provenance citation mapping directly to indexed corpus evidence."""
    source_id: str
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    section_title: str = ""
    source_start_offset: int = 0
    source_end_offset: int = 0
    file_hash_sha256: str = ""


class EvidenceGateResult(BaseModel):
    """Outcome of the pre-generation evidence sufficiency evaluation."""
    is_sufficient: bool
    reason: Optional[str] = None
    selected_candidates: List[CandidateChunk] = Field(default_factory=list)
    minimum_score: float = 0.35
    observed_best_score: float = 0.0
    warnings: List[str] = Field(default_factory=list)


class ContextPackage(BaseModel):
    """Structured and prompt-serialized context bundle with character budget tracking."""
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    selected_chunks: List[CandidateChunk] = Field(default_factory=list)
    serialized_context: str
    total_characters: int = 0
    truncated: bool = False
    sources: List[SourceCitation] = Field(default_factory=list)


class GroundedAnswer(BaseModel):
    """Complete grounded answer object with strict source provenance."""
    answer_id: str = Field(default_factory=lambda: str(uuid4()))
    query_id: str
    answer_text: str
    response_language: str = "en"
    grounded: bool = True
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    retrieval_id: Optional[str] = None
    sources: List[SourceCitation] = Field(default_factory=list)
    confidence_label: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: float = 0.0
