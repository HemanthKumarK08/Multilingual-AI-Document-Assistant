"""
Unit tests for EmbeddingConfig and VectorStoreConfig models and validation.
"""

import pytest
from pydantic import ValidationError

from app.services.embeddings.models import EmbeddingConfig
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.exceptions import VectorStoreError


class TestEmbeddingConfig:
    def test_default_config(self):
        config = EmbeddingConfig()
        assert config.model_name == "intfloat/multilingual-e5-small"
        assert config.dimension == 384
        assert config.device == "cpu"
        assert config.batch_size == 8
        assert config.max_length == 512
        assert config.normalize is True

    def test_custom_valid_config(self):
        config = EmbeddingConfig(
            model_name="custom/model",
            dimension=768,
            device="cpu",
            batch_size=16,
            max_length=256,
            normalize=False,
        )
        assert config.model_name == "custom/model"
        assert config.dimension == 768
        assert config.batch_size == 16
        assert config.normalize is False

    def test_invalid_batch_size_zero(self):
        with pytest.raises(ValidationError):
            EmbeddingConfig(batch_size=0)

    def test_invalid_batch_size_negative(self):
        with pytest.raises(ValidationError):
            EmbeddingConfig(batch_size=-5)

    def test_invalid_batch_size_too_large(self):
        with pytest.raises(ValidationError):
            EmbeddingConfig(batch_size=1000)

    def test_invalid_dimension_zero(self):
        with pytest.raises(ValidationError):
            EmbeddingConfig(dimension=0)


class TestVectorStoreConfig:
    def test_default_config(self):
        config = VectorStoreConfig()
        assert config.collection_name == "document_chunks"
        assert config.distance_metric == "cosine"
        assert config.persist_directory == "data/vector_store"
        assert config.index_version == 1

    def test_custom_valid_config(self):
        config = VectorStoreConfig(
            collection_name="custom_chunks",
            distance_metric="l2",
            persist_directory="tmp/test_chroma",
            index_version=2,
        )
        assert config.collection_name == "custom_chunks"
        assert config.distance_metric == "l2"
        assert config.index_version == 2

    def test_invalid_distance_metric(self):
        with pytest.raises(VectorStoreError):
            VectorStoreConfig(distance_metric="manhattan_invalid")
