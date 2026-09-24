"""
Pydantic Schemas for Request & Response Payloads
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# --- Document Schemas ---
class DocumentBase(BaseModel):
    display_title: str
    category: str
    description: Optional[str] = None
    language: str = "en"
    file_type: str = "pdf"
    version: str = "1.0"
    is_active: bool = True

class DocumentCreate(DocumentBase):
    filename: str
    file_size_bytes: int
    file_hash_sha256: str
    storage_path: str
    page_count: int = 1

class DocumentIngestRequest(BaseModel):
    file_path: str = Field(..., description="Path to file on disk relative to project root or absolute")
    doc_id: str = Field(..., description="Stable unique document identifier e.g. DOC-ACAD-001")
    display_title: Optional[str] = None
    category: str = Field(default="general")
    version: str = Field(default="1.0")
    allow_reingest: bool = False


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_id: str
    filename: str
    file_size_bytes: int
    file_hash_sha256: str
    page_count: int
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

# --- QA & RAG Schemas ---
class QueryRequest(BaseModel):
    query_text: str = Field(..., min_length=2, max_length=1000)
    category: Optional[str] = None
    target_language: Optional[str] = None
    session_id: Optional[str] = None

class Citation(BaseModel):
    document_id: str
    document_title: str
    category: str
    page_number: int
    chunk_index: int
    similarity_score: float
    excerpt: str

class QueryResponse(BaseModel):
    query_id: str
    query_text: str
    detected_language: str
    answer_text: str
    is_fallback: bool
    grounded: bool = True
    fallback_reason: Optional[str] = None
    response_state: str = "GROUNDED"
    citations: List[Citation]
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float

# --- Feedback Schema ---
class FeedbackRequest(BaseModel):
    query_id: str
    feedback: int = Field(..., ge=-1, le=1)  # 1 = thumbs up, -1 = thumbs down
    comment: Optional[str] = None

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str

# --- Health Schema ---
class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    database_status: str
    vector_store_configured: bool
    llm_primary_provider: str
