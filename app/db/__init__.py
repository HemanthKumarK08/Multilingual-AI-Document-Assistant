"""
Database Package
Provides session maker, base declarative class, and model references.
"""

from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal, get_db, init_db, close_db
from app.db.models import (
    Document,
    DocumentProcessingJob,
    User,
    QueryLogReference,
)

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "close_db",
    "Document",
    "DocumentProcessingJob",
    "User",
    "QueryLogReference",
]
