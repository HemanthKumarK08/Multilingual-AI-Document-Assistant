"""
Embedding Coordinator Module (Phase 4)
Orchestrates embedding generation across Phase 3 chunk artifacts and generates batch reports.
"""

import json
import time
import uuid
import pathlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.chunking.models import ChunkedDocumentArtifact, DocumentChunk
from app.services.chunking.serialization import deserialize_chunked_artifact
from app.services.embeddings.models import (
    EmbeddingConfig,
    EmbeddedChunk,
    EmbeddingRunReport,
)
from app.services.embeddings.provider import EmbeddingProvider
from app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
from app.services.embeddings.batching import embed_texts_in_batches
from app.services.embeddings.validation import validate_batch_embeddings
from app.services.embeddings.exceptions import EmbeddingError, InvalidInputError


class EmbeddingCoordinator:
    """Coordinates batch embedding generation for document chunks."""

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        provider: Optional[EmbeddingProvider] = None,
    ):
        self.config = config or EmbeddingConfig(
            model_name=settings.EMBEDDING_MODEL_NAME,
            dimension=settings.EMBEDDING_DIMENSION,
            device=settings.EMBEDDING_DEVICE,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            max_length=settings.EMBEDDING_MAX_LENGTH,
            normalize=settings.EMBEDDING_NORMALIZE,
            model_cache_dir=settings.EMBEDDING_MODEL_CACHE_DIR,
        )
        self.provider = provider or SentenceTransformerEmbeddingProvider(self.config)

    def embed_document_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> List[EmbeddedChunk]:
        """
        Generates dense embeddings for a list of DocumentChunk instances.
        
        Args:
            chunks: List of Phase 3 DocumentChunk models.
            
        Returns:
            List of EmbeddedChunk models pairing metadata with dense vectors.
        """
        if not chunks:
            return []

        texts = [c.text_content for c in chunks]
        batch_result = embed_texts_in_batches(self.provider, texts, self.config.batch_size)
        
        # Validate output shape and values
        validate_batch_embeddings(batch_result.embeddings, len(chunks), self.config.dimension)

        embedded_chunks: List[EmbeddedChunk] = []
        for chunk, vec in zip(chunks, batch_result.embeddings):
            embedded = EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                file_hash_sha256=chunk.file_hash_sha256,
                filename=chunk.filename,
                category=chunk.category,
                language=chunk.language,
                script=chunk.script,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                heading_level=chunk.heading_level,
                chunk_index=chunk.chunk_index,
                text_content=chunk.text_content,
                text_length=chunk.text_length,
                source_start_offset=chunk.source_start_offset,
                source_end_offset=chunk.source_end_offset,
                source_unit_index=chunk.source_unit_index,
                parser_name=chunk.parser_name,
                parser_version=chunk.parser_version,
                version=chunk.version,
                extraction_notes=chunk.extraction_notes,
                embedding=vec,
                embedding_model_name=self.provider.model_name,
                embedding_dimension=self.provider.dimension,
                embedding_device=self.provider.device,
                embedding_normalized=self.provider.normalize,
                vector_index_version=settings.VECTOR_INDEX_VERSION,
            )
            embedded_chunks.append(embedded)

        return embedded_chunks

    def embed_document_artifact(
        self,
        artifact: ChunkedDocumentArtifact,
    ) -> List[EmbeddedChunk]:
        """Embeds all chunks contained in a ChunkedDocumentArtifact."""
        return self.embed_document_chunks(artifact.chunks)

    def embed_document_file(
        self,
        file_path: str | pathlib.Path,
    ) -> List[EmbeddedChunk]:
        """Loads a Phase 3 chunk artifact file and embeds its chunks."""
        artifact = deserialize_chunked_artifact(file_path)
        return self.embed_document_artifact(artifact)

    def embed_corpus(
        self,
        input_dir: Optional[pathlib.Path] = None,
        output_dir: Optional[pathlib.Path] = None,
        save_artifacts: bool = False,
    ) -> EmbeddingRunReport:
        """
        Discovers all *_chunks.json in data/processed/, generates embeddings,
        and produces data/embeddings/embedding_report.json.
        """
        start_time = time.time()
        in_dir = (input_dir or (settings.DATA_DIRECTORY / "processed")).resolve()
        out_dir = (output_dir or (settings.DATA_DIRECTORY / "embeddings")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        chunk_files = sorted(in_dir.glob("*_chunks.json"))
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        doc_summaries: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        successful_docs = 0
        failed_docs = 0
        total_chunks_discovered = 0
        total_chunks_embedded = 0
        total_chunks_failed = 0

        for c_file in chunk_files:
            file_start = time.time()
            try:
                artifact = deserialize_chunked_artifact(c_file)
                doc_id = artifact.source_document.get("doc_id", c_file.stem.replace("_chunks", ""))
                total_chunks_discovered += len(artifact.chunks)

                embedded_chunks = self.embed_document_artifact(artifact)
                total_chunks_embedded += len(embedded_chunks)
                successful_docs += 1

                if save_artifacts:
                    art_file = out_dir / f"{doc_id}_embeddings.json"
                    art_data = {
                        "doc_id": doc_id,
                        "embedding_model": self.provider.model_name,
                        "dimension": self.provider.dimension,
                        "total_chunks": len(embedded_chunks),
                        "chunks": [ec.model_dump() for ec in embedded_chunks],
                    }
                    art_file.write_text(json.dumps(art_data, indent=2, ensure_ascii=False), encoding="utf-8")

                doc_summaries.append({
                    "doc_id": doc_id,
                    "status": "success",
                    "chunk_count": len(embedded_chunks),
                    "duration_ms": round((time.time() - file_start) * 1000, 2),
                })
            except Exception as e:
                failed_docs += 1
                logger.error(f"Failed to embed {c_file.name}: {str(e)}")
                errors.append({
                    "file": c_file.name,
                    "status": "failed",
                    "error": str(e),
                })

        total_elapsed = round(time.time() - start_time, 3)
        completed_at = datetime.now(timezone.utc).isoformat()

        report = EmbeddingRunReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            embedding_model_name=self.provider.model_name,
            embedding_dimension=self.provider.dimension,
            embedding_device=self.provider.device,
            embedding_batch_size=self.config.batch_size,
            embedding_normalized=self.provider.normalize,
            documents_discovered=len(chunk_files),
            documents_succeeded=successful_docs,
            documents_failed=failed_docs,
            chunks_discovered=total_chunks_discovered,
            chunks_embedded=total_chunks_embedded,
            chunks_failed=total_chunks_failed,
            total_elapsed_seconds=total_elapsed,
            document_summaries=doc_summaries,
            errors=errors,
        )

        report_file = out_dir / "embedding_report.json"
        report_file.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Embedding run complete: {successful_docs}/{len(chunk_files)} docs -> {total_chunks_embedded} chunks in {total_elapsed}s")

        return report
