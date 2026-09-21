"""
Query Log Reference Model Definition
Stores lightweight query telemetry references and feedback in SQLite, linking to raw JSONL telemetry files.
"""

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Float, DateTime, Index
from app.db.base import Base, TimestampMixin

class QueryLogReference(Base, TimestampMixin):
    __tablename__ = "query_log_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    telemetry_source: Mapped[str] = mapped_column(
        String(50),
        default="REAL_APPLICATION",
        index=True,
        nullable=False
    )  # "REAL_APPLICATION", "SYNTHETIC_SIMULATION", "EVALUATION_BENCHMARK", "ERROR_DIAGNOSTIC"
    detected_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    top_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    user_feedback: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 = positive, -1 = negative
    telemetry_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_telem_src_time", "telemetry_source", "timestamp"),
        Index("idx_telem_lang_cat", "detected_language", "category"),
    )

    def __repr__(self) -> str:
        return f"<QueryLogReference(query_id='{self.query_id}', src='{self.telemetry_source}', lang='{self.detected_language}', fallback={self.is_fallback})>"
