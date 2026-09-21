"""
Vector Index Validation and Integrity Verification Module (Phase 4)
"""

import math
from typing import Dict, Any, List, Optional
from app.services.vector_store.exceptions import VectorStoreError
from app.services.vector_store.models import IndexStats


def validate_vector_index(
    collection,
    expected_dim: int,
    expected_model: str,
    sample_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validates persistent ChromaDB collection integrity, dimensions, and metadata completeness.
    
    Raises:
        VectorStoreError if any integrity invariant is violated.
    """
    total_count = collection.count()
    if total_count == 0:
        return {
            "status": "empty",
            "total_records": 0,
            "message": "Vector collection is empty.",
        }

    meta = collection.metadata or {}
    collection_dim = meta.get("embedding_dimension")
    if collection_dim is not None and int(collection_dim) != expected_dim:
        raise VectorStoreError(
            f"Collection dimension ({collection_dim}) != expected ({expected_dim})"
        )

    # Fetch sample records to verify embeddings and metadata
    fetch_limit = min(50, total_count)
    sample_data = collection.get(
        ids=sample_ids if sample_ids else None,
        limit=fetch_limit if not sample_ids else None,
        include=["embeddings", "documents", "metadatas"],
    )

    if not sample_data or not sample_data.get("ids"):
        raise VectorStoreError("Failed to fetch sample records from ChromaDB collection.")

    for idx, (cid, emb, doc, md) in enumerate(
        zip(
            sample_data["ids"],
            sample_data["embeddings"],
            sample_data["documents"],
            sample_data["metadatas"],
        )
    ):
        # 1. Check ID format
        if not cid or ":" not in cid:
            raise VectorStoreError(f"Malformed chunk_id in index: '{cid}'")

        # 2. Check embedding dimension and finiteness
        if emb is not None:
            if len(emb) != expected_dim:
                raise VectorStoreError(
                    f"Record {cid} has vector dimension {len(emb)}, expected {expected_dim}."
                )
            for v_idx, val in enumerate(emb):
                if math.isnan(val) or math.isinf(val):
                    raise VectorStoreError(
                        f"Record {cid} contains NaN/inf vector value at component {v_idx}."
                    )

        # 3. Check document text retrievability
        if not doc or not doc.strip():
            raise VectorStoreError(f"Record {cid} has empty document text in vector store.")

        # 4. Check essential metadata
        if not md:
            raise VectorStoreError(f"Record {cid} is missing metadata in ChromaDB.")
        
        required_meta_keys = [
            "chunk_id",
            "doc_id",
            "file_hash_sha256",
            "category",
            "language",
            "script",
            "page_number",
            "chunk_index",
        ]
        for r_key in required_meta_keys:
            if r_key not in md:
                raise VectorStoreError(f"Record {cid} metadata is missing required key '{r_key}'.")

    return {
        "status": "valid",
        "total_records": total_count,
        "sample_checked": len(sample_data["ids"]),
        "dimension": expected_dim,
        "model": expected_model,
    }
