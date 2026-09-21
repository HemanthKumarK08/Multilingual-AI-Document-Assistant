"""
Metadata Filtering Utilities for Retrieval
"""

from typing import Any, Dict, Optional
from app.services.retrieval.exceptions import FilterError
from app.services.retrieval.models import RetrievalFilter

# Allowed metadata filter keys
ALLOWED_FILTER_FIELDS = {
    "doc_id",
    "category",
    "language",
    "script",
    "page_number",
    "filename",
}

def validate_filter(filters: Optional[RetrievalFilter]) -> None:
    """Validates filter fields against supported schema."""
    if not filters:
        return
    if filters.page_number is not None and filters.page_number < 1:
        raise FilterError("page_number filter must be a positive integer (>= 1).")

def build_chroma_filter(filters: Optional[RetrievalFilter]) -> Optional[Dict[str, Any]]:
    """Converts a RetrievalFilter model into a ChromaDB compatible query where dict."""
    if not filters:
        return None
    validate_filter(filters)
    return filters.to_chroma_where()
