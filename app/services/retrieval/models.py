"""
Retrieval Subsystem Data Models
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

class QueryVariant(BaseModel):
    """An expanded or transliterated variant of a user query."""
    variant_text: str
    variant_type: Literal["original", "synonym", "transliteration", "indic_translation", "expanded"] = "original"
    weight: float = 1.0
    language: str = "en"
    source_terms: List[str] = Field(default_factory=list)

class ProcessedQuery(BaseModel):
    """Normalized and analyzed user query."""
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    raw_query: str
    normalized_query: str
    language: str = "und"
    script: str = "Unknown"
    language_source: Literal["explicit", "detected", "default"] = "detected"
    is_code_mixed: bool = False
    is_romanized: bool = False
    is_transliterated: bool = False
    script_distribution: Dict[str, float] = Field(default_factory=dict)
    query_variants: List[QueryVariant] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RetrievalFilter(BaseModel):
    """Metadata filter parameters supported by vector store and retrieval."""
    doc_id: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    script: Optional[str] = None
    page_number: Optional[int] = None
    filename: Optional[str] = None

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Converts filter to ChromaDB where clause."""
        clauses = []
        if self.doc_id:
            clauses.append({"doc_id": {"$eq": self.doc_id}})
        if self.category:
            clauses.append({"category": {"$eq": self.category}})
        if self.language:
            clauses.append({"language": {"$eq": self.language}})
        if self.script:
            clauses.append({"script": {"$eq": self.script}})
        if self.page_number is not None:
            clauses.append({"page_number": {"$eq": self.page_number}})
        if self.filename:
            clauses.append({"filename": {"$eq": self.filename}})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

class CandidateChunk(BaseModel):
    """A retrieved chunk candidate with provenance and ranking scores."""
    chunk_id: str
    doc_id: str
    text_content: str
    filename: str
    category: str = "general"
    language: str = "und"
    script: str = "Unknown"
    page_number: int = 1
    section_title: str = ""
    heading_level: int = 0
    source_start_offset: int = 0
    source_end_offset: int = 0
    file_hash_sha256: str = ""
    
    # Retrieval Scores
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rerank_score: Optional[float] = None
    
    # Provenance
    retrieval_methods: List[str] = Field(default_factory=list)
    query_variant_sources: List[str] = Field(default_factory=list)
    rank: int = 0

class RetrievalResult(BaseModel):
    """Aggregate result from the retrieval engine."""
    retrieval_id: str = Field(default_factory=lambda: str(uuid4()))
    query: ProcessedQuery
    candidates: List[CandidateChunk] = Field(default_factory=list)
    total_candidates_found: int = 0
    selected_candidates_count: int = 0
    query_variant_count: int = 1
    latency_ms: float = 0.0
    filters_applied: Optional[RetrievalFilter] = None
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
