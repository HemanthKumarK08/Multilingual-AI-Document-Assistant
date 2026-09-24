"""
Persistent ChromaDB Client Factory Module (Phase 4)
"""

import pathlib
from typing import Dict, Any
from app.core.logging import logger
from app.services.vector_store.exceptions import VectorStoreError

_CHROMA_CLIENT_CACHE: Dict[str, Any] = {}


def get_persistent_chroma_client(persist_dir: str | pathlib.Path):
    """
    Creates or returns a persistent ChromaDB Client at the specified directory.
    Uses an in-memory cache to guarantee a single reused client per directory.
    
    Args:
        persist_dir: Target filesystem path for persistent vector storage.
        
    Returns:
        chromadb.ClientAPI persistent client instance.
    """
    path = pathlib.Path(persist_dir).resolve()
    path_key = str(path)
    
    if path_key in _CHROMA_CLIENT_CACHE:
        return _CHROMA_CLIENT_CACHE[path_key]

    path.mkdir(parents=True, exist_ok=True)

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        _CHROMA_CLIENT_CACHE[path_key] = client
        return client
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB PersistentClient at {path}: {str(e)}")
        raise VectorStoreError(f"Failed to initialize ChromaDB PersistentClient at {path}: {str(e)}") from e
