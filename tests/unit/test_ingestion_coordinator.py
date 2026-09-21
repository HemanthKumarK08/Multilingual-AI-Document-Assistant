"""
Unit and Integration Tests for Ingestion Coordinator
"""

import pytest
import pytest_asyncio
import tempfile
import pathlib
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, event
from app.db.base import Base
from app.db.models.document import Document
from app.db.models.job import DocumentProcessingJob
from app.services.ingestion.coordinator import IngestionCoordinator
from app.services.ingestion.exceptions import (
    FileNotFoundIngestionError,
    EmptyFileError,
    UnsupportedFileTypeError,
)
from app.services.ingestion.constants import IngestionStatus, JobStatus

@pytest_asyncio.fixture
async def test_db_session():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_sessionmaker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with test_sessionmaker() as session:
        yield session

    await test_engine.dispose()

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield pathlib.Path(tmp)

@pytest.mark.asyncio
async def test_coordinator_successful_ingestion(test_db_session: AsyncSession, temp_dir: pathlib.Path):
    coordinator = IngestionCoordinator()
    test_file = temp_dir / "sample_policy.md"
    test_file.write_text("# Autonomous Hostel Policy\n\nCurfew is 9:30 PM for all residential students.", encoding="utf-8")

    result = await coordinator.ingest_document(
        db=test_db_session,
        file_path=test_file,
        doc_id="DOC-COORD-001",
        display_title="Autonomous Hostel Policy",
        category="hostel",
        version="1.0"
    )

    assert result.doc_id == "DOC-COORD-001"
    assert result.status == IngestionStatus.PARSED.value
    assert result.is_duplicate is False
    assert result.page_count == 1
    assert result.character_count > 20
    assert result.language == "en"

    # Verify Document in DB
    stmt_doc = select(Document).where(Document.doc_id == "DOC-COORD-001")
    doc_res = await test_db_session.execute(stmt_doc)
    doc_record = doc_res.scalar_one()
    assert doc_record.status == IngestionStatus.PARSED.value
    assert doc_record.category == "hostel"
    assert doc_record.file_hash_sha256 == result.file_hash_sha256

    # Verify DocumentProcessingJob in DB
    stmt_job = select(DocumentProcessingJob).where(DocumentProcessingJob.doc_id == "DOC-COORD-001")
    job_res = await test_db_session.execute(stmt_job)
    job_record = job_res.scalar_one()
    assert job_record.status == JobStatus.COMPLETED.value
    assert job_record.completed_at is not None

@pytest.mark.asyncio
async def test_coordinator_duplicate_detection(test_db_session: AsyncSession, temp_dir: pathlib.Path):
    coordinator = IngestionCoordinator()
    file1 = temp_dir / "original.md"
    file1.write_text("Identical content for duplicate check in hostel category.", encoding="utf-8")

    # Ingest first document
    res1 = await coordinator.ingest_document(
        db=test_db_session,
        file_path=file1,
        doc_id="DOC-ORIG-001",
        category="hostel"
    )
    assert res1.status == IngestionStatus.PARSED.value
    assert res1.is_duplicate is False

    # Ingest second document with different filename and doc_id but identical bytes
    file2 = temp_dir / "duplicate_copy.md"
    file2.write_text("Identical content for duplicate check in hostel category.", encoding="utf-8")

    res2 = await coordinator.ingest_document(
        db=test_db_session,
        file_path=file2,
        doc_id="DOC-DUP-002",
        category="hostel",
        allow_reingest=False
    )
    assert res2.status == IngestionStatus.DUPLICATE.value
    assert res2.is_duplicate is True
    assert res2.details["duplicate_of"] == "DOC-ORIG-001"

@pytest.mark.asyncio
async def test_coordinator_file_validation_errors(test_db_session: AsyncSession, temp_dir: pathlib.Path):
    coordinator = IngestionCoordinator()

    # 1. Non-existent file
    with pytest.raises(FileNotFoundIngestionError):
        await coordinator.ingest_document(
            db=test_db_session,
            file_path=temp_dir / "non_existent.md",
            doc_id="DOC-ERR-001"
        )

    # 2. Empty file
    empty_file = temp_dir / "empty.txt"
    empty_file.write_bytes(b"")
    with pytest.raises(EmptyFileError):
        await coordinator.ingest_document(
            db=test_db_session,
            file_path=empty_file,
            doc_id="DOC-ERR-002"
        )

    # 3. Unsupported extension
    bad_ext_file = temp_dir / "archive.zip"
    bad_ext_file.write_bytes(b"PK\x03\x04fakezipcontent")
    with pytest.raises(UnsupportedFileTypeError):
        await coordinator.ingest_document(
            db=test_db_session,
            file_path=bad_ext_file,
            doc_id="DOC-ERR-003"
        )
