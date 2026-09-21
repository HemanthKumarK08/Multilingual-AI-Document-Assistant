"""
Unit tests for EmbeddingProvider interface, text preparation, and vector validation.
"""

import pytest
from app.services.embeddings.constants import PASSAGE_PREFIX, QUERY_PREFIX
from app.services.embeddings.exceptions import (
    DimensionMismatchError,
    EmbeddingValidationError,
    InvalidInputError,
)
from app.services.embeddings.models import EmbeddingConfig
from app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
from app.services.embeddings.validation import validate_batch_embeddings, validate_vector


class DummyEmbeddingProvider:
    """Deterministic test double for fast unit tests without full model downloads."""
    def __init__(self, dimension: int = 384):
        self._dim = dimension
        self.model_name = "test/dummy-e5"
        self.device = "cpu"
        self.max_length = 512
        self.normalize = True
        self.batch_size = 8

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        for t in texts:
            if not t or not t.strip():
                raise InvalidInputError("Empty text")
        # Return deterministic unit vectors
        return [[1.0 / (self._dim ** 0.5)] * self._dim for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise InvalidInputError("Empty query")
        return [1.0 / (self._dim ** 0.5)] * self._dim


class TestEmbeddingProviderUnit:
    def test_text_preparation_passage_and_query_prefix(self):
        provider = SentenceTransformerEmbeddingProvider(
            EmbeddingConfig(model_name="intfloat/multilingual-e5-small")
        )
        prep_doc = provider._prepare_text("Academic regulations text", PASSAGE_PREFIX)
        assert prep_doc == "passage: Academic regulations text"

        prep_query = provider._prepare_text("What is minimum CGPA?", QUERY_PREFIX)
        assert prep_query == "query: What is minimum CGPA?"

        # Already prefixed should not duplicate prefix
        assert provider._prepare_text("passage: Already prefixed", PASSAGE_PREFIX) == "passage: Already prefixed"

    def test_empty_text_rejection(self):
        provider = SentenceTransformerEmbeddingProvider()
        with pytest.raises(InvalidInputError):
            provider._prepare_text("", PASSAGE_PREFIX)
        with pytest.raises(InvalidInputError):
            provider._prepare_text("   \n\t ", PASSAGE_PREFIX)

    def test_vector_validation_success(self):
        valid_vec = [0.1] * 384
        validate_vector(valid_vec, expected_dim=384)

    def test_vector_validation_dimension_mismatch(self):
        short_vec = [0.1] * 128
        with pytest.raises(DimensionMismatchError):
            validate_vector(short_vec, expected_dim=384)

    def test_vector_validation_nan_rejection(self):
        nan_vec = [0.1] * 383 + [float("nan")]
        with pytest.raises(EmbeddingValidationError):
            validate_vector(nan_vec, expected_dim=384)

    def test_vector_validation_inf_rejection(self):
        inf_vec = [0.1] * 383 + [float("inf")]
        with pytest.raises(EmbeddingValidationError):
            validate_vector(inf_vec, expected_dim=384)

    def test_dummy_provider_multilingual_texts(self):
        dummy = DummyEmbeddingProvider(dimension=384)
        texts = [
            "English academic policy text.",
            "बैंगलोर इंस्टीट्यूट ऑफ टेक्नोलॉजी में आपका स्वागत है।",
            "ಬೆಂಗಳೂರು ಇನ್‌ಸ್ಟಿಟ್ಯೂಟ್ ಆಫ್ ಟೆಕ್ನಾಲಜಿ ಗ್ರಂಥಾಲಯ ನಿಯಮಗಳು.",
            "బెంగళూరు ఇన్స్టిట్యూట్ ఆఫ్ టెక్నాలజీ పరీక్షల నిబంధనలు.",
            "BIT college mein admission schedule check karo.",
        ]
        embeddings = dummy.embed_documents(texts)
        assert len(embeddings) == len(texts)
        validate_batch_embeddings(embeddings, expected_count=5, expected_dim=384)
