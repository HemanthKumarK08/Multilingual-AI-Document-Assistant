"""
Constants and Configuration Defaults for Page-Aware Chunking Pipeline
"""

# Default Chunking Hyperparameters
DEFAULT_CHUNK_SIZE = 600       # Target character length (within approved 500-700 range)
DEFAULT_CHUNK_OVERLAP = 100    # Overlap character length
DEFAULT_MINIMUM_CHUNK_SIZE = 1 # Minimum acceptable chunk character length
MIN_CHUNK_SIZE = 1             # Alias for backward compatibility
MAX_CHUNK_SIZE = 2000          # Upper safety ceiling for configuration validation
MAX_CHUNK_SIZE_LIMIT = 2000    # Alias for safety ceiling
CHUNK_ID_DELIMITER = ":"       # Delimiter for structured chunk IDs (e.g. DOC-001:p1:c0)

# Natural Separator Hierarchy for Recursive Splitting
# Evaluates from coarse-grained paragraph boundaries down to fine-grained character cuts
DEFAULT_SEPARATORS = [
    "\n\n",   # Multi-paragraph breaks
    "\n",     # Single line breaks
    ". ",     # Sentence boundary (period + space)
    "? ",     # Question boundary
    "! ",     # Exclamation boundary
    "; ",     # Semicolon clause boundary
    ", ",     # Comma phrase boundary
    " ",      # Word boundary
    "",       # Character-level fallback
]

