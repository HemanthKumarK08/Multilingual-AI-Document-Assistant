"""
Document Ingestion Coordinator
Orchestrates file validation, SHA-256 deduplication, parser execution,
job lifecycle tracking, and database synchronization.
"""

import json
import time
import pathlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.db.models.document import Document
from app.db.models.job import DocumentProcessingJob
from app.services.ingestion.constants import (
    MAX_FILE_SIZE_BYTES,
    IngestionStatus,
    JobStatus,
    JobType,
)
from app.services.ingestion.exceptions import (
    IngestionError,
    FileNotFoundIngestionError,
    FileSizeExceededError,
    EmptyFileError,
    DuplicateDocumentError,
    ParserExecutionError,
)
from app.services.ingestion.hashing import compute_file_sha256
from app.services.ingestion.parsers.registry import default_parser_registry, ParserRegistry
from app.services.ingestion.models import ParsedDocument, IngestionResult

class IngestionCoordinator:
    """
    Coordinates the document ingestion pipeline.
    Ensures safe transaction management, job state transitions, and file deduplication.
    """

    def __init__(self, parser_registry: Optional[ParserRegistry] = None):
        self.registry = parser_registry or default_parser_registry

    async def ingest_document(
        self,
        db: AsyncSession,
        file_path: str | pathlib.Path,
        doc_id: str,
        display_title: Optional[str] = None,
        category: str = "general",
        version: str = "1.0",
        allow_reingest: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        """
        Executes end-to-end ingestion on a target file.
        
        Args:
            db: Async SQLAlchemy database session.
            file_path: Absolute or relative path to the document file.
            doc_id: Stable document identifier (e.g. DOC-ACAD-001).
            display_title: Human-readable title for the document.
            category: Institutional policy category.
            version: Document policy version.
            allow_reingest: If True, allows updating an existing document with the same hash.
            metadata: Optional extra metadata dictionary.
            
        Returns:
            IngestionResult containing processing details, hash, status, and warnings.
        """
        start_time = time.time()
        path = pathlib.Path(file_path).resolve()
        job_id = f"job_ingest_{doc_id}_{int(start_time)}"
        now_utc = datetime.now(timezone.utc)

        # 1. File existence, size, and extension validation
        if not path.exists():
            raise FileNotFoundIngestionError(f"Target file not found at: {path}", doc_id=doc_id)
        if not path.is_file():
            raise IngestionError(f"Target path is not a regular file: {path}", doc_id=doc_id)

        file_size = path.stat().st_size
        if file_size == 0:
            raise EmptyFileError(f"File {path.name} is 0 bytes (empty).", doc_id=doc_id)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise FileSizeExceededError(
                f"File size {file_size} bytes exceeds max permitted limit of {MAX_FILE_SIZE_BYTES} bytes.",
                doc_id=doc_id
            )

        # Ensure parser is registered for file extension upfront
        parser = self.registry.get_parser_for_file(path)

        # 2. Compute SHA-256 hash
        sha256_hash = compute_file_sha256(path)
        logger.info(f"Initiating ingestion for {doc_id} ({path.name}) | SHA-256: {sha256_hash[:12]}...")


        # 3. Check for duplicates in database
        stmt_hash = select(Document).where(Document.file_hash_sha256 == sha256_hash)
        res_hash = await db.execute(stmt_hash)
        existing_by_hash = res_hash.scalar_one_or_none()

        if existing_by_hash and existing_by_hash.doc_id != doc_id and not allow_reingest:
            logger.warning(f"Duplicate detected: File {path.name} has identical hash to {existing_by_hash.doc_id}")
            return IngestionResult(
                doc_id=doc_id,
                status=IngestionStatus.DUPLICATE.value,
                job_id=job_id,
                file_hash_sha256=sha256_hash,
                filename=path.name,
                storage_path=str(path),
                category=category,
                language=existing_by_hash.language,
                detected_script="unknown",
                page_count=existing_by_hash.page_count,
                character_count=0,
                warnings=[f"Duplicate of existing document ID: {existing_by_hash.doc_id}"],
                processed_at=now_utc.isoformat(),
                duration_ms=round((time.time() - start_time) * 1000, 2),
                is_duplicate=True,
                details={"duplicate_of": existing_by_hash.doc_id}
            )

        # 4. Check if Document record exists, or prepare new one
        stmt_doc = select(Document).where(Document.doc_id == doc_id)
        res_doc = await db.execute(stmt_doc)
        doc_record = res_doc.scalar_one_or_none()

        if not doc_record:
            doc_record = Document(
                doc_id=doc_id,
                filename=path.name,
                display_title=display_title or path.stem.replace("-", " ").replace("_", " ").title(),
                category=category,
                language="unknown",
                file_type=path.suffix.lstrip(".").lower() or "txt",
                file_size_bytes=file_size,
                file_hash_sha256=sha256_hash,
                storage_path=str(path),
                version=version,
                status=IngestionStatus.PROCESSING.value,
                is_active=True
            )
            db.add(doc_record)
            await db.flush()
        else:
            doc_record.status = IngestionStatus.PROCESSING.value
            doc_record.file_hash_sha256 = sha256_hash
            doc_record.file_size_bytes = file_size
            doc_record.storage_path = str(path)
            await db.flush()

        # 5. Create processing job record
        job_record = DocumentProcessingJob(
            job_id=job_id,
            doc_id=doc_id,
            job_type=JobType.INGESTION.value,
            status=JobStatus.RUNNING.value,
            started_at=now_utc,
            job_metadata=json.dumps({"filename": path.name, "size": file_size, "category": category})
        )
        db.add(job_record)
        await db.flush()

        # 6. Execute parsing
        try:
            parsed_doc = parser.parse(
                file_path=path,
                doc_id=doc_id,
                category=category,
                metadata=metadata
            )
        except Exception as parse_err:

            logger.error(f"Parser execution failed for {doc_id}: {str(parse_err)}")
            job_record.status = JobStatus.FAILED.value
            job_record.completed_at = datetime.now(timezone.utc)
            job_record.error_message = str(parse_err)
            doc_record.status = IngestionStatus.FAILED.value
            doc_record.error_message = str(parse_err)
            await db.commit()
            raise ParserExecutionError(f"Parsing failed for {doc_id}: {str(parse_err)}", doc_id=doc_id)

        # 7. Update document record with extracted metadata
        doc_record.page_count = parsed_doc.page_count
        doc_record.language = parsed_doc.detected_language
        doc_record.status = IngestionStatus.PARSED.value
        doc_record.error_message = None

        # 8. Save structured intermediate artifact in data/processed/
        processed_dir = settings.DATA_DIRECTORY / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = processed_dir / f"{doc_id}_parsed.json"
        
        try:
            artifact_path.write_text(
                json.dumps(parsed_doc.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as io_err:
            logger.warning(f"Could not persist processed JSON artifact for {doc_id}: {str(io_err)}")

        # 9. Mark processing job as completed
        completed_utc = datetime.now(timezone.utc)
        job_record.status = JobStatus.COMPLETED.value
        job_record.completed_at = completed_utc
        job_record.job_metadata = json.dumps({
            "parser": parsed_doc.parser_name,
            "version": parsed_doc.parser_version,
            "page_count": parsed_doc.page_count,
            "char_count": len(parsed_doc.normalized_text),
            "language": parsed_doc.detected_language,
            "script": parsed_doc.detected_script,
            "warnings": [w.model_dump() for w in parsed_doc.warnings]
        })

        # 10. Commit transaction
        await db.commit()

        duration = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"Successfully ingested {doc_id} | Pages: {parsed_doc.page_count} | "
            f"Chars: {len(parsed_doc.normalized_text)} | Lang: {parsed_doc.detected_language} | "
            f"Time: {duration} ms"
        )

        return IngestionResult(
            doc_id=doc_id,
            status=IngestionStatus.PARSED.value,
            job_id=job_id,
            file_hash_sha256=sha256_hash,
            filename=path.name,
            storage_path=str(path),
            category=category,
            language=parsed_doc.detected_language,
            detected_script=parsed_doc.detected_script,
            page_count=parsed_doc.page_count,
            character_count=len(parsed_doc.normalized_text),
            warnings=[w.message for w in parsed_doc.warnings],
            processed_at=completed_utc.isoformat(),
            duration_ms=duration,
            is_duplicate=False,
            details={
                "parser_name": parsed_doc.parser_name,
                "sections_count": len(parsed_doc.sections),
                "artifact_path": str(artifact_path)
            }
        )

# Default global coordinator instance
default_ingestion_coordinator = IngestionCoordinator()
