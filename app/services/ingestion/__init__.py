"""
Document Ingestion Service Package
"""

from app.services.ingestion.coordinator import IngestionCoordinator, default_ingestion_coordinator
from app.services.ingestion.models import ParsedDocument, ExtractedPage, ExtractedBlock, ExtractedTable, IngestionResult
from app.services.ingestion.hashing import compute_file_sha256, compute_bytes_sha256
from app.services.ingestion.normalization import normalize_text, clean_heading_text
from app.services.ingestion.language import detect_script_and_language
from app.services.ingestion.exceptions import IngestionError, DuplicateDocumentError

__all__ = [
    "IngestionCoordinator",
    "default_ingestion_coordinator",
    "ParsedDocument",
    "ExtractedPage",
    "ExtractedBlock",
    "ExtractedTable",
    "IngestionResult",
    "compute_file_sha256",
    "compute_bytes_sha256",
    "normalize_text",
    "clean_heading_text",
    "detect_script_and_language",
    "IngestionError",
    "DuplicateDocumentError",
]
