"""
ChromaDB Metadata Serialization and Adaptation Module (Phase 4)
"""

import json
from typing import Dict, Any
from app.services.embeddings.models import EmbeddedChunk
from app.services.vector_store.exceptions import MetadataSerializationError


def serialize_chunk_metadata(chunk: EmbeddedChunk) -> Dict[str, Any]:
    """
    Serializes all 20 provenance attributes and embedding configuration into
    ChromaDB-compatible scalar metadata (str, int, float, bool).
    Lists (such as extraction_notes) are serialized to JSON strings.
    """
    try:
        notes_json = json.dumps(chunk.extraction_notes, ensure_ascii=False) if chunk.extraction_notes else "[]"
        
        return {
            "chunk_id": str(chunk.chunk_id),
            "doc_id": str(chunk.doc_id),
            "file_hash_sha256": str(chunk.file_hash_sha256),
            "filename": str(chunk.filename),
            "category": str(chunk.category or "general"),
            "language": str(chunk.language),
            "script": str(chunk.script),
            "page_number": int(chunk.page_number),
            "section_title": str(chunk.section_title or "Introduction / Overview"),
            "heading_level": int(chunk.heading_level or 1),
            "chunk_index": int(chunk.chunk_index),
            "text_length": int(chunk.text_length),
            "source_start_offset": int(chunk.source_start_offset),
            "source_end_offset": int(chunk.source_end_offset),
            "source_unit_index": int(chunk.source_unit_index),
            "parser_name": str(chunk.parser_name),
            "parser_version": str(chunk.parser_version),
            "version": str(chunk.version),
            "extraction_notes": notes_json,
            "embedding_model_name": str(chunk.embedding_model_name),
            "embedding_dimension": int(chunk.embedding_dimension),
            "embedding_device": str(chunk.embedding_device),
            "embedding_normalized": bool(chunk.embedding_normalized),
            "vector_index_version": int(chunk.vector_index_version),
        }
    except Exception as e:
        raise MetadataSerializationError(f"Failed to serialize metadata for chunk {chunk.chunk_id}: {str(e)}") from e


def deserialize_chunk_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserializes ChromaDB metadata, unescaping JSON lists back to Python lists.
    """
    output = dict(metadata)
    if "extraction_notes" in output and isinstance(output["extraction_notes"], str):
        try:
            output["extraction_notes"] = json.loads(output["extraction_notes"])
        except Exception:
            output["extraction_notes"] = [output["extraction_notes"]]
    return output
