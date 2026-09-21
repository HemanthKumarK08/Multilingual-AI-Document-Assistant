"""
Constants and Defaults for Multilingual Embedding Subsystem (Phase 4)
"""

# Default Model Specifications
DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
DEFAULT_EMBEDDING_DIMENSION = 384
DEFAULT_EMBEDDING_DEVICE = "cpu"
DEFAULT_EMBEDDING_BATCH_SIZE = 8
DEFAULT_EMBEDDING_MAX_LENGTH = 512
DEFAULT_EMBEDDING_NORMALIZE = True

# E5 Model Prefix Requirements
PASSAGE_PREFIX = "passage: "   # Required prefix for indexing document chunks
QUERY_PREFIX = "query: "       # Required prefix for retrieval queries

# Safety Limits
MAX_BATCH_SIZE_LIMIT = 256
MIN_BATCH_SIZE = 1
MIN_DIMENSION = 1
MAX_DIMENSION = 4096
