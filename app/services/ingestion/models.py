"""
Pydantic Data Transfer Objects and Intermediate Representation for Ingestion Pipeline
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExtractedTable(BaseModel):
    """Structured representation of extracted table content."""
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    caption: Optional[str] = None

    def to_formatted_text(self) -> str:
        """Serializes table to deterministic bracketed representation."""
        lines = ["[TABLE]"]
        if self.caption:
            lines.append(f"Caption: {self.caption}")
        if self.headers:
            lines.append(" | ".join(h.strip() for h in self.headers))
            lines.append("-" * max(20, sum(len(h) + 3 for h in self.headers)))
        for row in self.rows:
            lines.append(" | ".join(c.strip() for c in row))
        lines.append("[/TABLE]")
        return "\n".join(lines)

class ExtractedBlock(BaseModel):
    """A logical text block, heading, or table inside a page/document."""
    block_type: str = Field(description="paragraph, heading, table, list_item")
    text: str
    heading_level: Optional[int] = None
    section_title: Optional[str] = None
    table_data: Optional[ExtractedTable] = None

class ExtractedPage(BaseModel):
    """Page-level container preserving 1-indexed page boundaries."""
    page_number: int = Field(ge=1, description="1-indexed physical page number")
    text: str
    blocks: List[ExtractedBlock] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ExtractionWarning(BaseModel):
    """Warning or non-fatal anomaly encountered during parsing."""
    warning_code: str
    message: str
    page_number: Optional[int] = None
    severity: str = "warning"

class ParsedDocument(BaseModel):
    """Complete intermediate representation produced by document parsers."""
    doc_id: str
    filename: str
    file_type: str
    parser_name: str
    parser_version: str
    page_count: int
    raw_text: str
    normalized_text: str
    pages: List[ExtractedPage] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    detected_language: str = "unknown"
    detected_script: str = "unknown"
    language_confidence: float = 0.0
    warnings: List[ExtractionWarning] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionResult(BaseModel):
    """Structured response returned by the IngestionCoordinator."""
    doc_id: str
    status: str
    job_id: str
    file_hash_sha256: str
    filename: str
    storage_path: str
    category: str
    language: str
    detected_script: str
    page_count: int
    character_count: int
    warnings: List[str] = Field(default_factory=list)
    processed_at: str
    duration_ms: float
    is_duplicate: bool = False
    details: Optional[Dict[str, Any]] = None
