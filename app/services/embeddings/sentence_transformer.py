"""
SentenceTransformer Embedding Provider Implementation (Phase 4)
Supports multilingual-e5-small with E5 query/passage prefixing, CPU-first inference, and normalization.
"""

from typing import List, Optional
import math
from app.core.logging import logger
from app.services.embeddings.constants import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_DEVICE,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MAX_LENGTH,
    DEFAULT_EMBEDDING_NORMALIZE,
    PASSAGE_PREFIX,
    QUERY_PREFIX,
)
from app.services.embeddings.exceptions import (
    ModelLoadError,
    DimensionMismatchError,
    InvalidInputError,
    EmbeddingValidationError,
)
from app.services.embeddings.models import EmbeddingConfig


# Global singleton cache for loaded SentenceTransformer model instances
_GLOBAL_MODEL_CACHE = {}


class SentenceTransformerEmbeddingProvider:
    """
    Sentence Transformers wrapper implementing the EmbeddingProvider protocol.
    Supports lazy loading, shared process-level model cache, and E5-specific prefix conventions.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._model = None

    @property
    def model_name(self) -> str:
        return self.config.model_name

    @property
    def dimension(self) -> int:
        return self.config.dimension

    @property
    def device(self) -> str:
        return self.config.device

    @property
    def max_length(self) -> int:
        return self.config.max_length

    @property
    def normalize(self) -> bool:
        return self.config.normalize

    @property
    def batch_size(self) -> int:
        return self.config.batch_size

    def _get_model(self):
        """Lazy loader for the SentenceTransformer model instance using shared global cache."""
        cache_key = (self.model_name, self.device, str(self.config.model_cache_dir or ""))
        if cache_key in _GLOBAL_MODEL_CACHE:
            self._model = _GLOBAL_MODEL_CACHE[cache_key]
            return self._model

        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(
                    f"Loading embedding model [{self.model_name}] on device [{self.device}]..."
                )
                model_inst = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=self.config.model_cache_dir,
                )
                # Set max sequence length
                if hasattr(model_inst, "max_seq_length"):
                    model_inst.max_seq_length = self.max_length
                logger.info(f"Model [{self.model_name}] successfully loaded (dimension={self.dimension}).")
                _GLOBAL_MODEL_CACHE[cache_key] = model_inst
                self._model = model_inst
            except Exception as e:
                logger.error(f"Failed to load embedding model {self.model_name}: {str(e)}")
                raise ModelLoadError(f"Failed to load embedding model {self.model_name}: {str(e)}") from e
        return self._model

    def _prepare_text(self, text: str, prefix: str) -> str:
        """Applies prefixing and validates text."""
        if not text or not text.strip():
            raise InvalidInputError("Cannot embed empty or whitespace-only text.")
        
        cleaned = text.strip()
        # If text does not already start with prefix, prepend it (e.g. for E5 models)
        if "e5" in self.model_name.lower():
            if not cleaned.startswith(PASSAGE_PREFIX) and not cleaned.startswith(QUERY_PREFIX):
                return f"{prefix}{cleaned}"
        return cleaned

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of document chunks, applying 'passage: ' prefix for E5.
        """
        if not texts:
            return []

        prepared_texts = [self._prepare_text(t, PASSAGE_PREFIX) for t in texts]
        model = self._get_model()

        try:
            embeddings_tensor = model.encode(
                prepared_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
            )
        except Exception as e:
            raise EmbeddingValidationError(f"Inference failed during document embedding: {str(e)}") from e

        results: List[List[float]] = []
        for i, vec in enumerate(embeddings_tensor):
            vec_list = [float(v) for v in vec]
            
            # Check dimension
            if len(vec_list) != self.dimension:
                raise DimensionMismatchError(
                    f"Generated embedding dimension ({len(vec_list)}) does not match expected ({self.dimension})"
                )
            
            # Check for NaN or infinite values
            for val in vec_list:
                if math.isnan(val) or math.isinf(val):
                    raise EmbeddingValidationError(f"Invalid numeric value (NaN/inf) in embedding vector for text index {i}")
            
            results.append(vec_list)

        return results

    def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single query string, applying 'query: ' prefix for E5.
        """
        prepared_query = self._prepare_text(text, QUERY_PREFIX)
        model = self._get_model()

        try:
            vec = model.encode(
                prepared_query,
                show_progress_bar=False,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
            )
        except Exception as e:
            raise EmbeddingValidationError(f"Inference failed during query embedding: {str(e)}") from e

        vec_list = [float(v) for v in vec]
        if len(vec_list) != self.dimension:
            raise DimensionMismatchError(
                f"Generated query embedding dimension ({len(vec_list)}) does not match expected ({self.dimension})"
            )

        for val in vec_list:
            if math.isnan(val) or math.isinf(val):
                raise EmbeddingValidationError("Invalid numeric value (NaN/inf) in query embedding vector")

        return vec_list
