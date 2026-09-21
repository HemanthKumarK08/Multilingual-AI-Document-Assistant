"""
Unit Tests for Dense Retriever (Phase 5)
"""

from unittest.mock import MagicMock
import pytest
from app.services.retrieval.dense_retriever import DenseRetriever
from app.services.retrieval.models import ProcessedQuery, RetrievalFilter
from app.services.vector_store.models import VectorStoreConfig


class TestDenseRetrieverUnit:
    def test_retrieve_empty_collection(self):
        mock_client = MagicMock()
        mock_col = MagicMock()
        mock_col.count.return_value = 0
        mock_col.metadata = {"embedding_dimension": 384, "embedding_model_name": "dummy"}
        mock_client.list_collections.return_value = [mock_col]
        mock_client.get_collection.return_value = mock_col

        mock_embedder = MagicMock()
        mock_embedder.config.dimension = 384
        mock_embedder.config.model_name = "dummy"
        mock_embedder.embed_query.return_value = [0.1] * 384

        retriever = DenseRetriever(
            embedding_provider=mock_embedder,
            chroma_client=mock_client,
            vector_config=VectorStoreConfig(collection_name="test_col"),
        )
        retriever.collection = mock_col

        pq = ProcessedQuery(raw_query="test", normalized_query="test")
        candidates = retriever.retrieve(pq, top_k=5)
        assert candidates == []

    def test_retrieve_mock_candidates_mapping(self):
        mock_client = MagicMock()
        mock_col = MagicMock()
        mock_col.count.return_value = 2
        mock_col.query.return_value = {
            "ids": [["c1", "c2"]],
            "documents": [["Doc 1 text", "Doc 2 text"]],
            "metadatas": [[
                {"doc_id": "d1", "filename": "f1.pdf", "page_number": 1, "category": "academic"},
                {"doc_id": "d2", "filename": "f2.pdf", "page_number": 2, "category": "hostel"},
            ]],
            "distances": [[0.2, 0.4]],
        }

        mock_embedder = MagicMock()
        mock_embedder.config.dimension = 384
        mock_embedder.config.model_name = "dummy"
        mock_embedder.embed_query.return_value = [0.1] * 384

        retriever = DenseRetriever(
            embedding_provider=mock_embedder,
            chroma_client=mock_client,
            vector_config=VectorStoreConfig(collection_name="test_col"),
        )
        retriever.collection = mock_col

        pq = ProcessedQuery(raw_query="attendance rules", normalized_query="attendance rules")
        candidates = retriever.retrieve(pq, top_k=2)

        assert len(candidates) == 2
        assert candidates[0].chunk_id == "c1"
        assert candidates[0].dense_score == pytest.approx(0.8, rel=1e-2)
        assert candidates[0].rank == 1
        assert candidates[1].chunk_id == "c2"
        assert candidates[1].dense_score == pytest.approx(0.6, rel=1e-2)
        assert candidates[1].rank == 2
