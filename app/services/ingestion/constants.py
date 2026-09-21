"""
Constants and Enumerations for Document Ingestion Pipeline
"""

from enum import Enum

# File format definitions
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

MIME_TYPE_MAPPING = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "text/plain": "txt",
    "text/markdown": "md",
}

# Size limits
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB max file upload size

# Ingestion & Job Status Codes
class IngestionStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PARSED = "parsed"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobType(str, Enum):
    INGESTION = "ingestion"
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    REBUILD = "rebuild"

# Supported Language and Script Codes
class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    KANNADA = "kn"
    TELUGU = "te"
    UNKNOWN = "unknown"

class ScriptType(str, Enum):
    LATIN = "latin"
    DEVANAGARI = "devanagari"
    KANNADA = "kannada"
    TELUGU = "telugu"
    MIXED = "mixed"
    UNKNOWN = "unknown"

# Institutional Categories
VALID_CATEGORIES = {
    "academic_regulations",
    "examination_guidelines",
    "attendance",
    "scholarships",
    "hostel",
    "placements",
}
