"""
Unit tests for batching and chunk splitting utilities in embedding pipeline.
"""

import pytest
from app.services.embeddings.batching import chunk_list, embed_texts_in_batches
from app.services.embeddings.exceptions import InvalidInputError
from tests.unit.test_embedding_provider import DummyEmbeddingProvider


class TestEmbeddingBatching:
    def test_chunk_list_splitting(self):
        items = list(range(25))
        batches = list(chunk_list(items, 8))
        assert len(batches) == 4
        assert len(batches[0]) == 8
        assert len(batches[1]) == 8
        assert len(batches[2]) == 8
        assert len(batches[3]) == 1
        assert [x for b in batches for x in b] == items

    def test_chunk_list_invalid_batch_size(self):
        with pytest.raises(InvalidInputError):
            list(chunk_list([1, 2, 3], 0))

    def test_embed_texts_in_batches_order_preservation(self):
        provider = DummyEmbeddingProvider(dimension=64)
        texts = [f"Passage text number {i}" for i in range(20)]
        result = embed_texts_in_batches(provider, texts, batch_size=6)

        assert result.total_texts == 20
        assert result.dimension == 64
        assert len(result.embeddings) == 20

    def test_embed_empty_texts_list(self):
        provider = DummyEmbeddingProvider(dimension=64)
        result = embed_texts_in_batches(provider, [], batch_size=8)
        assert result.total_texts == 0
        assert result.embeddings == []
