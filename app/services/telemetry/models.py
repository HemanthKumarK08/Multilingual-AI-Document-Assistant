"""
Telemetry Event Models (Phase 7)
Defines strongly typed, privacy-preserving event models for Retrieval, Grounded RAG, and Error tracking.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.services.telemetry.schema import SCHEMA_VERSION


def _get_utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get_utc_hour() -> int:
    return datetime.now(timezone.utc).hour


class RetrievalTelemetryEvent(BaseModel):
    """Safe, privacy-preserving telemetry event for retrieval requests."""
    schema_version: str = SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "retrieval_completed"
    timestamp: str = Field(default_factory=_get_utc_now_iso)
    date: str = Field(default_factory=_get_utc_date)
    hour: int = Field(default_factory=_get_utc_hour)
    query_id: str
    retrieval_id: str
    language: str
    script: str
    is_code_mixed: bool = False
    candidate_count: int = 0
    selected_chunk_count: int = 0
    best_retrieval_score: float = 0.0
    latency_ms: float = 0.0
    error_type: Optional[str] = None


class RAGTelemetryEvent(BaseModel):
    """Safe, privacy-preserving telemetry event for Grounded RAG requests."""
    schema_version: str = SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "rag_response"
    timestamp: str = Field(default_factory=_get_utc_now_iso)
    date: str = Field(default_factory=_get_utc_date)
    hour: int = Field(default_factory=_get_utc_hour)
    query_id: str
    retrieval_id: Optional[str] = None
    language: str
    script: str
    is_code_mixed: bool = False
    candidate_count: int = 0
    selected_chunk_count: int = 0
    best_retrieval_score: float = 0.0
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    answer_grounded: bool = True
    citation_count: int = 0
    latency_ms: float = 0.0
    error_type: Optional[str] = None


class UnifiedQueryTelemetryEvent(BaseModel):
    """
    Unified end-to-end query completion telemetry event (Phase 7 primary analytics model).
    Contains all operational, retrieval, and generation dimensions without storing any raw text.
    """
    schema_version: str = SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "query_completed"
    timestamp: str = Field(default_factory=_get_utc_now_iso)
    date: str = Field(default_factory=_get_utc_date)
    hour: int = Field(default_factory=_get_utc_hour)
    request_id_hash: str = Field(default_factory=lambda: str(uuid4())[:16])
    query_id: str
    retrieval_id: Optional[str] = None
    language: str = "en"
    script: str = "latin"
    query_type: str = "cross_lingual_fact"
    is_code_mixed: bool = False
    variant_count: int = 1
    candidate_count: int = 0
    retrieved_chunk_count: int = 0
    best_retrieval_score: float = 0.0
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    provider: str = "mock"
    answer_mode: str = "grounded"
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    citation_count: int = 0
    citation_valid: bool = True
    grounded: bool = True
    error: bool = False
    error_type: Optional[str] = None


class ErrorTelemetryEvent(BaseModel):
    """Telemetry event for application or pipeline errors."""
    schema_version: str = SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = "error"
    timestamp: str = Field(default_factory=_get_utc_now_iso)
    date: str = Field(default_factory=_get_utc_date)
    hour: int = Field(default_factory=_get_utc_hour)
    error_category: str
    error_code: str
    component: str
    latency_ms: float = 0.0
    language: Optional[str] = None
