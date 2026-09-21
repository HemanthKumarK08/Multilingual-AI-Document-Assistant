"""
Document Model Definition
Stores metadata, ingestion status, checksums, and storage paths for institutional circulars.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Text, Index
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.job import DocumentProcessingJob

class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    display_title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "pdf", "docx", "txt"
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded",
        index=True,
        nullable=False
    )  # "uploaded", "extracting", "chunked", "indexed", "failed"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    jobs: Mapped[List["DocumentProcessingJob"]] = relationship(
        "DocumentProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_doc_cat_active", "category", "is_active"),
        Index("idx_doc_status_active", "status", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Document(doc_id='{self.doc_id}', title='{self.display_title}', category='{self.category}', active={self.is_active})>"
