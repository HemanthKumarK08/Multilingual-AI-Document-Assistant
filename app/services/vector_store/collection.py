"""
ChromaDB Collection Management and Compatibility Validation Module (Phase 4)
"""

from typing import Dict, Any, Optional
from app.core.logging import logger
from app.services.vector_store.exceptions import CollectionCompatibilityError, VectorStoreError
from app.services.vector_store.models import VectorStoreConfig


def get_or_create_collection(
    client,
    config: VectorStoreConfig,
    embedding_model_name: str,
    dimension: int,
    rebuild: bool = False,
):
    """
    Retrieves or creates a persistent ChromaDB Collection with validated HNSW metadata.
    
    Args:
        client: chromadb.ClientAPI persistent client.
        config: VectorStoreConfig instance.
        embedding_model_name: Name of embedding model (e.g. intfloat/multilingual-e5-small).
        dimension: Embedding dimension (e.g. 384).
        rebuild: If True, drops existing collection before recreating.
        
    Returns:
        chromadb.Collection instance.
    """
    col_name = config.collection_name
    space = "cosine" if config.distance_metric == "cosine" else config.distance_metric

    if rebuild:
        try:
            client.delete_collection(name=col_name)
            logger.info(f"Rebuild requested: Deleted existing collection [{col_name}].")
        except Exception:
            pass

    collection_metadata = {
        "hnsw:space": space,
        "embedding_model_name": embedding_model_name,
        "embedding_dimension": dimension,
        "index_version": config.index_version,
    }

    try:
        # Check if collection already exists
        existing_collections = [c.name for c in client.list_collections()]
        
        if col_name in existing_collections:
            collection = client.get_collection(name=col_name)
            meta = collection.metadata or {}
            
            # Compatibility checks
            existing_dim = meta.get("embedding_dimension")
            if existing_dim is not None and int(existing_dim) != dimension:
                raise CollectionCompatibilityError(
                    f"Collection [{col_name}] has dimension {existing_dim}, incompatible with model dimension {dimension}."
                )
            
            existing_model = meta.get("embedding_model_name")
            if existing_model is not None and existing_model != embedding_model_name:
                raise CollectionCompatibilityError(
                    f"Collection [{col_name}] was built with model '{existing_model}', incompatible with '{embedding_model_name}'."
                )
            
            logger.info(f"Connected to existing ChromaDB collection [{col_name}] (records={collection.count()}).")
            return collection
        else:
            collection = client.create_collection(
                name=col_name,
                metadata=collection_metadata,
            )
            logger.info(f"Created new persistent ChromaDB collection [{col_name}] (metric={space}, dim={dimension}).")
            return collection

    except CollectionCompatibilityError:
        raise
    except Exception as e:
        logger.error(f"Failed to get/create ChromaDB collection [{col_name}]: {str(e)}")
        raise VectorStoreError(f"Failed to get/create ChromaDB collection [{col_name}]: {str(e)}") from e
