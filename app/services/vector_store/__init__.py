"""
Persistent Vector Store Package (Phase 4)
"""

from app.services.vector_store.constants import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_DISTANCE_METRIC,
    DEFAULT_PERSIST_DIRECTORY,
    DEFAULT_VECTOR_INDEX_VERSION,
    SUPPORTED_DISTANCE_METRICS,
)
from app.services.vector_store.exceptions import (
    CollectionCompatibilityError,
    IndexingError,
    MetadataSerializationError,
    StaleRecordError,
    VectorStoreError,
)
from app.services.vector_store.models import (
    IndexRunReport,
    IndexStats,
    StaleRecordReport,
    VectorRecord,
    VectorStoreConfig,
)
from app.services.vector_store.chroma_client import get_persistent_chroma_client
from app.services.vector_store.collection import get_or_create_collection
from app.services.vector_store.indexing import (
    detect_stale_records,
    remove_stale_records,
    upsert_embedded_chunks,
)
from app.services.vector_store.metadata import (
    deserialize_chunk_metadata,
    serialize_chunk_metadata,
)
from app.services.vector_store.validation import validate_vector_index
from app.services.vector_store.coordinator import VectorStoreCoordinator

__all__ = [
    "DEFAULT_COLLECTION_NAME",
    "DEFAULT_DISTANCE_METRIC",
    "DEFAULT_PERSIST_DIRECTORY",
    "DEFAULT_VECTOR_INDEX_VERSION",
    "SUPPORTED_DISTANCE_METRICS",
    "CollectionCompatibilityError",
    "IndexingError",
    "MetadataSerializationError",
    "StaleRecordError",
    "VectorStoreError",
    "IndexRunReport",
    "IndexStats",
    "StaleRecordReport",
    "VectorRecord",
    "VectorStoreConfig",
    "get_persistent_chroma_client",
    "get_or_create_collection",
    "detect_stale_records",
    "remove_stale_records",
    "upsert_embedded_chunks",
    "deserialize_chunk_metadata",
    "serialize_chunk_metadata",
    "validate_vector_index",
    "VectorStoreCoordinator",
]
