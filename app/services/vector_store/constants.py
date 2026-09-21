"""
Constants and Defaults for Persistent Vector Store (Phase 4)
"""

DEFAULT_COLLECTION_NAME = "document_chunks"
DEFAULT_DISTANCE_METRIC = "cosine"
DEFAULT_PERSIST_DIRECTORY = "data/vector_store"
DEFAULT_VECTOR_INDEX_VERSION = 1

# Supported Distance Metrics for ChromaDB HNSW Index
SUPPORTED_DISTANCE_METRICS = ["cosine", "l2", "ip"]
