"""
Dense ChromaDB Retriever Module
"""

from typing import List, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
from app.services.retrieval.constants import METHOD_DENSE
from app.services.retrieval.exceptions import DenseRetrievalError
from app.services.retrieval.filters import build_chroma_filter
from app.services.retrieval.models import CandidateChunk, ProcessedQuery, RetrievalFilter
from app.services.vector_store.chroma_client import get_persistent_chroma_client
from app.services.vector_store.collection import get_or_create_collection
from app.services.vector_store.metadata import deserialize_chunk_metadata
from app.services.vector_store.models import VectorStoreConfig


class DenseRetriever:
    """
    Performs dense semantic vector similarity search against the persistent ChromaDB collection.
    """

    def __init__(
        self,
        embedding_provider: Optional[SentenceTransformerEmbeddingProvider] = None,
        chroma_client=None,
        vector_config: Optional[VectorStoreConfig] = None,
    ):
        self.config = vector_config or VectorStoreConfig(
            persist_directory=settings.VECTOR_STORE_PERSIST_DIRECTORY,
            collection_name=settings.VECTOR_STORE_COLLECTION_NAME,
            distance_metric=settings.VECTOR_STORE_DISTANCE_METRIC,
            index_version=settings.VECTOR_INDEX_VERSION,
        )
        self.embedding_provider = embedding_provider or SentenceTransformerEmbeddingProvider()
        self.client = chroma_client or get_persistent_chroma_client(self.config.persist_directory)
        self.collection = get_or_create_collection(
            client=self.client,
            config=self.config,
            embedding_model_name=self.embedding_provider.config.model_name,
            dimension=self.embedding_provider.config.dimension,
        )

    def retrieve(
        self,
        query: ProcessedQuery,
        top_k: int = 12,
        filters: Optional[RetrievalFilter] = None,
        min_score: float = 0.0,
    ) -> List[CandidateChunk]:
        """
        Embeds the query and queries ChromaDB collection.
        
        Args:
            query: Normalized ProcessedQuery.
            top_k: Max candidate chunks to retrieve.
            filters: Optional metadata filters.
            min_score: Minimum similarity score threshold [0.0, 1.0].
            
        Returns:
            List of CandidateChunk instances ranked by dense score.
        """
        if top_k <= 0:
            return []

        try:
            # Generate query embedding (includes "query: " prefix)
            query_vector = self.embedding_provider.embed_query(query.normalized_query)
            query_list = query_vector.tolist() if isinstance(query_vector, np.ndarray) else list(query_vector)

            # Build Chroma filter
            where_clause = build_chroma_filter(filters)

            # Check collection count
            total_items = self.collection.count()
            if total_items == 0:
                logger.warning("DenseRetriever: ChromaDB collection is empty.")
                return []

            actual_n = min(top_k, total_items)
            
            kwargs = {
                "query_embeddings": [query_list],
                "n_results": actual_n,
                "include": ["documents", "metadatas", "distances"],
            }
            if where_clause:
                kwargs["where"] = where_clause

            results = self.collection.query(**kwargs)

            candidates: List[CandidateChunk] = []
            if not results or not results.get("ids") or not results["ids"][0]:
                return candidates

            ids = results["ids"][0]
            raw_docs = results.get("documents")
            docs = raw_docs[0] if (raw_docs and raw_docs[0] is not None) else [""] * len(ids)

            raw_metas = results.get("metadatas")
            metadatas = raw_metas[0] if (raw_metas and raw_metas[0] is not None) else [{}] * len(ids)

            raw_dists = results.get("distances")
            distances = raw_dists[0] if (raw_dists and raw_dists[0] is not None) else [1.0] * len(ids)

            for rank_idx, (chunk_id, doc_text, raw_meta, dist) in enumerate(zip(ids, docs, metadatas, distances), start=1):
                # Convert cosine distance to cosine similarity score: score = 1.0 - distance
                dense_score = max(0.0, min(1.0, 1.0 - float(dist)))
                
                if dense_score < min_score:
                    continue

                meta = deserialize_chunk_metadata(raw_meta)
                
                candidate = CandidateChunk(
                    chunk_id=str(chunk_id),
                    doc_id=str(meta.get("doc_id", "")),
                    text_content=str(doc_text or ""),
                    filename=str(meta.get("filename", "")),
                    category=str(meta.get("category", "general")),
                    language=str(meta.get("language", "und")),
                    script=str(meta.get("script", "Unknown")),
                    page_number=int(meta.get("page_number", 1)),
                    section_title=str(meta.get("section_title", "")),
                    heading_level=int(meta.get("heading_level", 0)),
                    source_start_offset=int(meta.get("source_start_offset", 0)),
                    source_end_offset=int(meta.get("source_end_offset", 0)),
                    file_hash_sha256=str(meta.get("file_hash_sha256", "")),
                    dense_score=round(dense_score, 4),
                    retrieval_methods=[METHOD_DENSE],
                    rank=rank_idx,
                )
                candidates.append(candidate)

            return candidates

        except Exception as e:
            logger.error(f"Dense retrieval query failed: {str(e)}")
            raise DenseRetrievalError(f"Dense retrieval query failed: {str(e)}") from e
