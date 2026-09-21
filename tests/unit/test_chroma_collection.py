"""
Unit tests for persistent ChromaDB client and collection compatibility.
"""

import pytest
from app.services.vector_store.chroma_client import get_persistent_chroma_client
from app.services.vector_store.collection import get_or_create_collection
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.exceptions import CollectionCompatibilityError


class TestChromaCollection:
    def test_persistent_client_and_collection_lifecycle(self, tmp_path):
        client = get_persistent_chroma_client(tmp_path / "chroma_test")
        config = VectorStoreConfig(
            persist_directory=str(tmp_path / "chroma_test"),
            collection_name="test_chunks",
            distance_metric="cosine",
        )

        # 1. Create collection
        col = get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-small",
            dimension=384,
        )
        assert col.name == "test_chunks"
        assert col.count() == 0

        # 2. Reconnect to existing collection
        col2 = get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-small",
            dimension=384,
        )
        assert col2.name == "test_chunks"

    def test_collection_dimension_mismatch_raises_error(self, tmp_path):
        client = get_persistent_chroma_client(tmp_path / "chroma_dim_test")
        config = VectorStoreConfig(
            persist_directory=str(tmp_path / "chroma_dim_test"),
            collection_name="dim_chunks",
        )

        # Create with dim 384
        get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-small",
            dimension=384,
        )

        # Try to connect with dim 768
        with pytest.raises(CollectionCompatibilityError):
            get_or_create_collection(
                client=client,
                config=config,
                embedding_model_name="intfloat/multilingual-e5-small",
                dimension=768,
            )

    def test_rebuild_resets_collection(self, tmp_path):
        client = get_persistent_chroma_client(tmp_path / "chroma_rebuild_test")
        config = VectorStoreConfig(
            persist_directory=str(tmp_path / "chroma_rebuild_test"),
            collection_name="rebuild_chunks",
        )

        # Create collection
        get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-small",
            dimension=384,
        )

        # Rebuild with new dimension succeeds because old collection is dropped
        rebuilt = get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-large",
            dimension=1024,
            rebuild=True,
        )
        assert rebuilt.metadata["embedding_dimension"] == 1024
