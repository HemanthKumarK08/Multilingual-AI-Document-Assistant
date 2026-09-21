"""
Deterministic JSON Serialization Module for Chunked Artifacts
"""

import json
import pathlib
from app.services.chunking.models import ChunkedDocumentArtifact


def serialize_chunked_artifact(
    artifact: ChunkedDocumentArtifact,
    output_path: str | pathlib.Path
) -> pathlib.Path:
    """
    Serializes a ChunkedDocumentArtifact to a deterministic UTF-8 JSON file.
    Uses atomic temporary file write and replacement to prevent partial file corruption.
    
    Args:
        artifact: ChunkedDocumentArtifact to serialize.
        output_path: Target filesystem path (e.g. data/processed/{doc_id}_chunks.json).
        
    Returns:
        pathlib.Path of the written artifact.
    """
    path = pathlib.Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    json_str = json.dumps(
        artifact.model_dump(),
        ensure_ascii=False,
        indent=2
    )

    # Atomic write via temporary file in same directory
    temp_file = path.parent / f".{path.name}.tmp"
    try:
        temp_file.write_text(json_str, encoding="utf-8")
        temp_file.replace(path)
    except Exception:
        if temp_file.exists():
            temp_file.unlink()
        raise

    return path


def deserialize_chunked_artifact(file_path: str | pathlib.Path) -> ChunkedDocumentArtifact:
    """Loads and deserializes a ChunkedDocumentArtifact from JSON."""
    path = pathlib.Path(file_path).resolve()
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    return ChunkedDocumentArtifact.model_validate(data)


# Alias for backward compatibility
load_chunked_artifact = deserialize_chunked_artifact
