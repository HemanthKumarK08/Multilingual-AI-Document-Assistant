"""
Vector Store Coordinator Module (Phase 4)
Orchestrates embedding generation, persistent ChromaDB indexing, stale-record reconciliation,
and batch indexing reports.
"""

import json
import time
import uuid
import pathlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set

from app.core.config import settings
from app.core.logging import logger
from app.services.chunking.models import ChunkedDocumentArtifact
from app.services.chunking.serialization import deserialize_chunked_artifact
from app.services.embeddings.coordinator import EmbeddingCoordinator
from app.services.embeddings.models import EmbeddingConfig
from app.services.vector_store.models import VectorStoreConfig, IndexRunReport
from app.services.vector_store.chroma_client import get_persistent_chroma_client
from app.services.vector_store.collection import get_or_create_collection
from app.services.vector_store.indexing import (
    upsert_embedded_chunks,
    detect_stale_records,
    remove_stale_records,
)
from app.services.vector_store.validation import validate_vector_index


class VectorStoreCoordinator:
    """Coordinates document chunk embedding and persistent ChromaDB indexing."""

    def __init__(
        self,
        vector_config: Optional[VectorStoreConfig] = None,
        embedding_coordinator: Optional[EmbeddingCoordinator] = None,
    ):
        self.vector_config = vector_config or VectorStoreConfig(
            persist_directory=settings.VECTOR_STORE_PERSIST_DIRECTORY,
            collection_name=settings.VECTOR_STORE_COLLECTION_NAME,
            distance_metric=settings.VECTOR_STORE_DISTANCE_METRIC,
            index_version=settings.VECTOR_INDEX_VERSION,
        )
        self.embedding_coordinator = embedding_coordinator or EmbeddingCoordinator()
        self._client = None

    def get_client(self):
        """Returns the persistent ChromaDB client."""
        if self._client is None:
            self._client = get_persistent_chroma_client(self.vector_config.persist_directory)
        return self._client

    def get_collection(self, rebuild: bool = False):
        """Returns the active persistent collection."""
        client = self.get_client()
        return get_or_create_collection(
            client=client,
            config=self.vector_config,
            embedding_model_name=self.embedding_coordinator.provider.model_name,
            dimension=self.embedding_coordinator.provider.dimension,
            rebuild=rebuild,
        )

    def index_document_artifact(
        self,
        artifact: ChunkedDocumentArtifact,
        collection=None,
    ) -> tuple[int, int, int]:
        """
        Generates embeddings for a chunked document artifact and indexes them into ChromaDB.
        
        Returns:
            Tuple of (inserted_count, updated_count, skipped_count).
        """
        col = collection or self.get_collection()
        embedded_chunks = self.embedding_coordinator.embed_document_artifact(artifact)
        return upsert_embedded_chunks(col, embedded_chunks)

    def index_corpus(
        self,
        input_dir: Optional[pathlib.Path] = None,
        rebuild: bool = False,
        remove_stale: bool = False,
    ) -> IndexRunReport:
        """
        Discovers all *_chunks.json in data/processed/, embeds them, and upserts into ChromaDB.
        Produces data/vector_store/index_report.json.
        """
        start_time = time.time()
        in_dir = (input_dir or (settings.DATA_DIRECTORY / "processed")).resolve()
        persist_dir = pathlib.Path(self.vector_config.persist_directory).resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)

        collection = self.get_collection(rebuild=rebuild)
        chunk_files = sorted(in_dir.glob("*_chunks.json"))

        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        successful_docs = 0
        failed_docs = 0
        total_chunks_discovered = 0
        total_chunks_embedded = 0
        total_chunks_indexed = 0
        total_chunks_updated = 0
        total_chunks_skipped = 0
        total_chunks_failed = 0
        all_expected_chunk_ids: Set[str] = set()

        errors: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # 1. Process documents
        for c_file in chunk_files:
            try:
                artifact = deserialize_chunked_artifact(c_file)
                total_chunks_discovered += len(artifact.chunks)
                for chk in artifact.chunks:
                    all_expected_chunk_ids.add(chk.chunk_id)

                embedded_chunks = self.embedding_coordinator.embed_document_artifact(artifact)
                total_chunks_embedded += len(embedded_chunks)

                inserted, updated, skipped = upsert_embedded_chunks(collection, embedded_chunks)
                total_chunks_indexed += inserted
                total_chunks_updated += updated
                total_chunks_skipped += skipped
                successful_docs += 1

            except Exception as e:
                failed_docs += 1
                logger.error(f"Failed to index {c_file.name}: {str(e)}")
                errors.append({
                    "file": c_file.name,
                    "status": "failed",
                    "error": str(e),
                })

        # 2. Stale Record Detection & Optional Removal
        stale_report = detect_stale_records(collection, all_expected_chunk_ids)
        stale_detected = stale_report.stale_count
        stale_removed = 0

        if stale_detected > 0:
            warnings.append(f"Detected {stale_detected} stale records in collection.")
            if remove_stale:
                stale_removed = remove_stale_records(collection, stale_report.stale_chunk_ids)
                logger.info(f"Removed {stale_removed} stale records.")

        # 3. Validation
        validation_info = validate_vector_index(
            collection=collection,
            expected_dim=self.embedding_coordinator.provider.dimension,
            expected_model=self.embedding_coordinator.provider.model_name,
        )

        total_elapsed = round(time.time() - start_time, 3)
        completed_at = datetime.now(timezone.utc).isoformat()

        report = IndexRunReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            input_directory=str(in_dir),
            persist_directory=str(persist_dir),
            collection_name=self.vector_config.collection_name,
            embedding_model_name=self.embedding_coordinator.provider.model_name,
            embedding_dimension=self.embedding_coordinator.provider.dimension,
            embedding_device=self.embedding_coordinator.provider.device,
            embedding_batch_size=self.embedding_coordinator.config.batch_size,
            embedding_normalized=self.embedding_coordinator.provider.normalize,
            documents_discovered=len(chunk_files),
            documents_succeeded=successful_docs,
            documents_failed=failed_docs,
            chunks_discovered=total_chunks_discovered,
            chunks_embedded=total_chunks_embedded,
            chunks_indexed=total_chunks_indexed,
            chunks_updated=total_chunks_updated,
            chunks_skipped=total_chunks_skipped,
            chunks_failed=total_chunks_failed,
            stale_records_detected=stale_detected,
            stale_records_removed=stale_removed,
            embedding_elapsed_seconds=total_elapsed,  # Total encompasses embedding & index
            indexing_elapsed_seconds=total_elapsed,
            total_elapsed_seconds=total_elapsed,
            validation_status=validation_info.get("status", "unknown"),
            warnings=warnings,
            errors=errors,
        )

        report_file = persist_dir / "index_report.json"
        report_file.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(
            f"Indexing run complete: {successful_docs}/{len(chunk_files)} docs -> "
            f"{total_chunks_indexed} added, {total_chunks_updated} updated, {total_chunks_skipped} skipped in {total_elapsed}s."
        )

        return report

    def verify_index(self) -> Dict[str, Any]:
        """Validates the persistent index and returns diagnostic metrics."""
        collection = self.get_collection()
        return validate_vector_index(
            collection=collection,
            expected_dim=self.embedding_coordinator.provider.dimension,
            expected_model=self.embedding_coordinator.provider.model_name,
        )
