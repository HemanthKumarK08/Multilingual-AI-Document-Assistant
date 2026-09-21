"""
Cryptographic Hashing Utilities for Document Deduplication
"""

import hashlib
import pathlib
from app.services.ingestion.exceptions import FileNotFoundIngestionError, IngestionError

DEFAULT_CHUNK_SIZE = 65536  # 64 KB streaming buffer

def compute_file_sha256(file_path: str | pathlib.Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """
    Computes a deterministic lowercase hexadecimal SHA-256 hash of a file using streaming reads.
    
    Args:
        file_path: Path to the target file on disk.
        chunk_size: Byte buffer size for chunked reading.
        
    Returns:
        64-character lowercase hexadecimal SHA-256 string.
    """
    path = pathlib.Path(file_path)
    if not path.exists():
        raise FileNotFoundIngestionError(f"File not found for hash calculation: {path}")
    if not path.is_file():
        raise IngestionError(f"Path is not a regular file: {path}")

    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest().lower()
    except Exception as e:
        raise IngestionError(f"Failed to compute SHA-256 hash for {path}: {str(e)}")

def compute_bytes_sha256(data: bytes) -> str:
    """
    Computes a deterministic lowercase hexadecimal SHA-256 hash from in-memory bytes.
    """
    return hashlib.sha256(data).hexdigest().lower()
