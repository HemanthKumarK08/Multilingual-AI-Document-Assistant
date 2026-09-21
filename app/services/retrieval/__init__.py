"""
Retrieval Subsystem Package (Phase 5)
"""

from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.exceptions import (
    DenseRetrievalError,
    FilterError,
    HybridFusionError,
    LexicalRetrievalError,
    QueryValidationError,
    RerankingError,
    RetrievalError,
)
from app.services.retrieval.hybrid import fuse_hybrid_scores
from app.services.retrieval.lexical_retriever import InMemoryBM25Index, LexicalRetriever
from app.services.retrieval.models import (
    CandidateChunk,
    ProcessedQuery,
    RetrievalFilter,
    RetrievalResult,
)
from app.services.retrieval.query_processing import normalize_query_text, process_query
from app.services.retrieval.reranker import heuristic_rerank

__all__ = [
    "RetrievalCoordinator",
    "DenseRetriever",
    "LexicalRetriever",
    "InMemoryBM25Index",
    "fuse_hybrid_scores",
    "heuristic_rerank",
    "normalize_query_text",
    "process_query",
    "CandidateChunk",
    "ProcessedQuery",
    "RetrievalFilter",
    "RetrievalResult",
    "RetrievalError",
    "QueryValidationError",
    "DenseRetrievalError",
    "LexicalRetrievalError",
    "HybridFusionError",
    "RerankingError",
    "FilterError",
]
