"""
Chunking Coordinator Module (Phase 3)
Orchestrates document chunking, validation, artifact persistence, and batch corpus reporting.
"""

import json
import time
import pathlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.services.ingestion.models import ParsedDocument
from app.services.chunking.models import (
    ChunkingConfig,
    DocumentChunk,
    ChunkedDocumentArtifact,
    ChunkingReport,
    DocumentChunkSummary,
)
from app.services.chunking.boundaries import PageAwareBoundaryManager
from app.services.chunking.validator import ChunkValidator
from app.services.chunking.serialization import serialize_chunked_artifact
from app.services.chunking.exceptions import ChunkingError, ArtifactNotFoundError
from app.db.models.document import Document


class ChunkingCoordinator:
    """Coordinates page-aware and section-aware document chunking."""

    def __init__(
        self,
        config: Optional[ChunkingConfig] = None,
        output_dir: Optional[pathlib.Path] = None,
    ):
        self.config = config or ChunkingConfig()
        self.output_dir = output_dir or (settings.DATA_DIRECTORY / "processed")
        self.boundary_manager = PageAwareBoundaryManager(self.config)
        self.validator = ChunkValidator()

    def chunk_parsed_document(
        self,
        parsed_doc: ParsedDocument,
        doc_metadata: Optional[Dict[str, Any]] = None,
        save_artifact: bool = True
    ) -> ChunkedDocumentArtifact:
        """
        Chunks a ParsedDocument, validates chunk consistency, and optionally saves the JSON artifact.
        
        Args:
            parsed_doc: Canonical ParsedDocument instance from Phase 2.
            doc_metadata: Supplementary metadata dictionary (category, file_hash_sha256, version).
            save_artifact: If True, serializes output to data/processed/{doc_id}_chunks.json.
            
        Returns:
            Validated ChunkedDocumentArtifact.
        """
        meta = doc_metadata or {}
        doc_id = parsed_doc.doc_id

        # 1. Generate chunks using page and section boundary manager
        chunks = self.boundary_manager.chunk_document(parsed_doc, meta)

        # 2. Validate generated chunks
        self.validator.validate_chunks(chunks, self.config, source_text=parsed_doc.normalized_text)

        # 3. Assemble ChunkedDocumentArtifact
        total_src_chars = len(parsed_doc.normalized_text)
        total_chk_chars = sum(c.text_length for c in chunks)
        now_utc = datetime.now(timezone.utc).isoformat()

        file_hash = (
            meta.get("file_hash_sha256")
            or meta.get("checksum_sha256")
            or parsed_doc.metadata.get("file_hash_sha256")
            or "unknown_hash"
        )
        source_doc_info = {
            "doc_id": doc_id,
            "filename": parsed_doc.filename,
            "file_type": parsed_doc.file_type,
            "file_hash_sha256": file_hash,
            "category": meta.get("category", parsed_doc.metadata.get("category", "general")),
            "language": parsed_doc.detected_language,
            "script": parsed_doc.detected_script,
            "page_count": parsed_doc.page_count,
            "parser_name": parsed_doc.parser_name,
            "parser_version": parsed_doc.parser_version,
            "version": meta.get("version", parsed_doc.metadata.get("version", "1.0")),
        }

        artifact = ChunkedDocumentArtifact(
            schema_version="1.0",
            chunking_config=self.config,
            source_document=source_doc_info,
            total_chunks=len(chunks),
            total_source_characters=total_src_chars,
            total_chunk_characters=total_chk_chars,
            chunks=chunks,
            created_at=now_utc
        )

        # 4. Serialize to disk if requested
        if save_artifact:
            out_path = self.output_dir / f"{doc_id}_chunks.json"
            serialize_chunked_artifact(artifact, out_path)
            logger.info(f"Saved chunk artifact for {doc_id} -> {out_path} ({len(chunks)} chunks)")

        return artifact

    def chunk_parsed_file(
        self,
        parsed_file_path: str | pathlib.Path,
        doc_metadata: Optional[Dict[str, Any]] = None,
        save_artifact: bool = True
    ) -> ChunkedDocumentArtifact:
        """Loads a parsed JSON artifact from disk and chunks it."""
        path = pathlib.Path(parsed_file_path).resolve()
        if not path.exists():
            raise ArtifactNotFoundError(f"Parsed artifact file not found: {path}")

        content = path.read_text(encoding="utf-8")
        parsed_doc_data = json.loads(content)
        parsed_doc = ParsedDocument.model_validate(parsed_doc_data)

        return self.chunk_parsed_document(parsed_doc, doc_metadata, save_artifact)

    # Alias for convenient API compatibility
    chunk_document_artifact = chunk_parsed_file

    async def update_database_chunk_count(
        self,
        db: AsyncSession,
        doc_id: str,
        chunk_count: int
    ) -> None:
        """Updates chunk_count on the Document record in SQLite."""
        stmt = select(Document).where(Document.doc_id == doc_id)
        result = await db.execute(stmt)
        doc_record = result.scalar_one_or_none()
        if doc_record:
            doc_record.chunk_count = chunk_count
            await db.commit()

    def chunk_all_processed_documents(
        self,
        processed_dir: Optional[pathlib.Path] = None,
        manifest_path: Optional[pathlib.Path] = None,
        input_dir: Optional[pathlib.Path] = None,
    ) -> ChunkingReport:
        """
        Discovers all *_parsed.json files in data/processed/, chunks them, and writes corpus_chunking_report.json.
        """
        start_time = time.time()
        target_input = input_dir or processed_dir or self.output_dir
        p_dir = target_input.resolve()
        m_path = (manifest_path or (settings.DATA_DIRECTORY / "raw" / "corpus_manifest.json")).resolve()

        manifest_map: Dict[str, Dict[str, Any]] = {}
        if m_path.exists():
            manifest_items = json.loads(m_path.read_text(encoding="utf-8"))
            for item in manifest_items:
                manifest_map[item["document_id"]] = item

        parsed_files = sorted(p_dir.glob("*_parsed.json"))
        doc_summaries: List[DocumentChunkSummary] = []
        successful = 0
        failed = 0
        total_chunks = 0
        total_source_chars = 0
        total_chunk_chars = 0
        all_chunk_lengths: List[int] = []

        for p_file in parsed_files:
            file_start = time.time()
            try:
                parsed_data = json.loads(p_file.read_text(encoding="utf-8"))
                doc_id = parsed_data.get("doc_id", p_file.stem.replace("_parsed", ""))
                meta = manifest_map.get(doc_id, {})

                parsed_doc = ParsedDocument.model_validate(parsed_data)
                artifact = self.chunk_parsed_document(parsed_doc, meta, save_artifact=True)

                doc_chunk_count = len(artifact.chunks)
                doc_src_chars = len(parsed_doc.normalized_text)
                doc_chk_chars = sum(c.text_length for c in artifact.chunks)
                chunk_lengths = [c.text_length for c in artifact.chunks]
                avg_len = round(sum(chunk_lengths) / len(chunk_lengths), 2) if chunk_lengths else 0.0
                min_len = min(chunk_lengths) if chunk_lengths else 0
                max_len = max(chunk_lengths) if chunk_lengths else 0

                successful += 1
                total_chunks += doc_chunk_count
                total_source_chars += doc_src_chars
                total_chunk_chars += doc_chk_chars
                all_chunk_lengths.extend(chunk_lengths)

                doc_summaries.append(
                    DocumentChunkSummary(
                        doc_id=doc_id,
                        status="success",
                        category=meta.get("category", parsed_doc.metadata.get("category", "general")),
                        language=parsed_doc.detected_language,
                        script=parsed_doc.detected_script,
                        page_count=parsed_doc.page_count,
                        chunk_count=doc_chunk_count,
                        source_character_count=doc_src_chars,
                        chunk_character_count=doc_chk_chars,
                        avg_chunk_length=avg_len,
                        min_chunk_length=min_len,
                        max_chunk_length=max_len,
                        duration_ms=round((time.time() - file_start) * 1000, 2),
                        artifact_path=str(self.output_dir / f"{doc_id}_chunks.json")
                    )
                )
            except Exception as e:
                failed += 1
                logger.error(f"Failed to chunk {p_file.name}: {str(e)}")
                doc_summaries.append(
                    DocumentChunkSummary(
                        doc_id=p_file.stem.replace("_parsed", ""),
                        status="failed",
                        error_message=str(e),
                        duration_ms=round((time.time() - file_start) * 1000, 2),
                    )
                )

        total_duration = round(time.time() - start_time, 3)
        avg_chunk_len = round(sum(all_chunk_lengths) / len(all_chunk_lengths), 2) if all_chunk_lengths else 0.0

        report = ChunkingReport(
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
            total_discovered_documents=len(parsed_files),
            total_successful=successful,
            total_failed=failed,
            total_chunks_generated=total_chunks,
            total_source_characters=total_source_chars,
            total_chunk_characters=total_chunk_chars,
            overall_avg_chunk_length=avg_chunk_len,
            total_duration_seconds=total_duration,
            documents=doc_summaries,
        )

        report_file = self.output_dir / "corpus_chunking_report.json"
        report_file.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Corpus chunking complete: {successful}/{len(parsed_files)} docs -> {total_chunks} chunks in {total_duration}s")

        return report

    # Alias for convenient API compatibility
    chunk_corpus = chunk_all_processed_documents


# Global default chunking coordinator instance
default_chunking_coordinator = ChunkingCoordinator()
