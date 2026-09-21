"""
Deterministic Indexing and Idempotency Subsystem (Phase 4)
Handles upsert operations, hash checking, stale record detection, and controlled removal.
"""

from typing import List, Dict, Any, Tuple, Set, Optional
from app.core.logging import logger
from app.services.embeddings.models import EmbeddedChunk
from app.services.vector_store.metadata import serialize_chunk_metadata
from app.services.vector_store.models import StaleRecordReport
from app.services.vector_store.exceptions import IndexingError


def upsert_embedded_chunks(
    collection,
    chunks: List[EmbeddedChunk],
) -> Tuple[int, int, int]:
    """
    Idempotently upserts a list of EmbeddedChunks into the ChromaDB collection.
    
    Args:
        collection: chromadb.Collection instance.
        chunks: List of EmbeddedChunk models.
        
    Returns:
        Tuple of (inserted_count, updated_count, skipped_count).
    """
    if not chunks:
        return 0, 0, 0

    chunk_ids = [c.chunk_id for c in chunks]
    
    try:
        # Check existing records in batch
        existing = collection.get(ids=chunk_ids, include=["metadatas"])
        existing_id_set = set(existing["ids"]) if existing and "ids" in existing else set()
        existing_meta_map: Dict[str, Dict[str, Any]] = {}
        
        if existing and "metadatas" in existing and existing["metadatas"]:
            for eid, emeta in zip(existing["ids"], existing["metadatas"]):
                existing_meta_map[eid] = emeta or {}

        to_insert_ids: List[str] = []
        to_insert_embeddings: List[List[float]] = []
        to_insert_documents: List[str] = []
        to_insert_metadatas: List[Dict[str, Any]] = []

        to_update_ids: List[str] = []
        to_update_embeddings: List[List[float]] = []
        to_update_documents: List[str] = []
        to_update_metadatas: List[Dict[str, Any]] = []

        skipped_count = 0

        for chunk in chunks:
            meta = serialize_chunk_metadata(chunk)
            
            if chunk.chunk_id not in existing_id_set:
                to_insert_ids.append(chunk.chunk_id)
                to_insert_embeddings.append(chunk.embedding)
                to_insert_documents.append(chunk.text_content)
                to_insert_metadatas.append(meta)
            else:
                # Record exists; check if content or hash changed
                ex_meta = existing_meta_map.get(chunk.chunk_id, {})
                ex_hash = ex_meta.get("file_hash_sha256")
                
                if ex_hash == chunk.file_hash_sha256:
                    skipped_count += 1
                else:
                    to_update_ids.append(chunk.chunk_id)
                    to_update_embeddings.append(chunk.embedding)
                    to_update_documents.append(chunk.text_content)
                    to_update_metadatas.append(meta)

        # Perform insertions
        if to_insert_ids:
            collection.add(
                ids=to_insert_ids,
                embeddings=to_insert_embeddings,
                documents=to_insert_documents,
                metadatas=to_insert_metadatas,
            )

        # Perform updates
        if to_update_ids:
            collection.update(
                ids=to_update_ids,
                embeddings=to_update_embeddings,
                documents=to_update_documents,
                metadatas=to_update_metadatas,
            )

        return len(to_insert_ids), len(to_update_ids), skipped_count

    except Exception as e:
        logger.error(f"Failed to upsert chunks into ChromaDB: {str(e)}")
        raise IndexingError(f"Failed to upsert chunks into ChromaDB: {str(e)}") from e


def detect_stale_records(
    collection,
    expected_chunk_ids: Set[str],
) -> StaleRecordReport:
    """
    Compares the ChromaDB collection against the expected canonical corpus chunk IDs.
    """
    all_collection_records = collection.get(include=[])
    existing_ids = set(all_collection_records.get("ids", []))

    stale_ids = sorted(list(existing_ids - expected_chunk_ids))
    missing_ids = sorted(list(expected_chunk_ids - existing_ids))

    return StaleRecordReport(
        total_existing_in_collection=len(existing_ids),
        total_expected_in_corpus=len(expected_chunk_ids),
        stale_count=len(stale_ids),
        stale_chunk_ids=stale_ids,
        missing_count=len(missing_ids),
        missing_chunk_ids=missing_ids,
    )


def remove_stale_records(
    collection,
    stale_chunk_ids: List[str],
) -> int:
    """
    Controlled deletion of confirmed stale chunk IDs from ChromaDB.
    """
    if not stale_chunk_ids:
        return 0

    try:
        collection.delete(ids=stale_chunk_ids)
        logger.info(f"Removed {len(stale_chunk_ids)} stale records from ChromaDB collection.")
        return len(stale_chunk_ids)
    except Exception as e:
        logger.error(f"Failed to remove stale records: {str(e)}")
        raise IndexingError(f"Failed to remove stale records: {str(e)}") from e
