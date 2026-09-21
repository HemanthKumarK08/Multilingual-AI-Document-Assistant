"""
Embedding Provider Protocol Definition (Phase 4)
Defines the abstract interface for embedding model implementations.
"""

from typing import Protocol, List, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for pluggable embedding models."""

    @property
    def model_name(self) -> str:
        """Name or path of the embedding model."""
        ...

    @property
    def dimension(self) -> int:
        """Expected dimensional size of generated embeddings."""
        ...

    @property
    def device(self) -> str:
        """Hardware device on which inference is performed (e.g. 'cpu')."""
        ...

    @property
    def max_length(self) -> int:
        """Maximum supported sequence token length."""
        ...

    @property
    def normalize(self) -> bool:
        """Whether embeddings are L2-normalized upon generation."""
        ...

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of document passage texts.
        Automatically applies passage-level prefixing (e.g. 'passage: ').
        
        Args:
            texts: List of document text strings.
            
        Returns:
            List of float vectors, each of length `dimension`.
        """
        ...

    def embed_query(self, text: str) -> List[float]:
        """
        Generates a dense vector embedding for a single search query text.
        Automatically applies query-level prefixing (e.g. 'query: ').
        
        Args:
            text: Query text string.
            
        Returns:
            Float vector of length `dimension`.
        """
        ...
