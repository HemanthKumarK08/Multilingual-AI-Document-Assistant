"""
Document Processing Job Model Definition
Tracks asynchronous lifecycle stages (extraction, chunking, embedding, indexing, rebuild).
"""

from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.document import Document

class DocumentProcessingJob(Base, TimestampMixin):
    __tablename__ = "document_processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    doc_id: Mapped[str] = mapped_column(String(64), ForeignKey("documents.doc_id", ondelete="CASCADE"), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "extraction", "embedding", "indexing", "rebuild"
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        index=True,
        nullable=False
    )  # "pending", "running", "completed", "failed"
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string for extra metrics

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="jobs")

    __table_args__ = (
        Index("idx_job_doc_status", "doc_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<DocumentProcessingJob(job_id='{self.job_id}', doc_id='{self.doc_id}', status='{self.status}')>"
