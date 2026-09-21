"""
Integration tests for multilingual embedding pipeline.
Tests embedding generation against actual Phase 3 chunk artifacts.
"""

import pathlib
import pytest

from app.services.chunking.serialization import deserialize_chunked_artifact
from app.services.embeddings.coordinator import EmbeddingCoordinator
from app.services.embeddings.models import EmbeddingConfig

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class TestEmbeddingPipelineIntegration:
    @pytest.fixture
    def embedding_coordinator(self):
        config = EmbeddingConfig(
            model_name="intfloat/multilingual-e5-small",
            dimension=384,
            device="cpu",
            batch_size=8,
            normalize=True,
        )
        return EmbeddingCoordinator(config=config)

    def test_embed_real_chunk_artifact(self, embedding_coordinator):
        artifact_path = PROCESSED_DIR / "DOC-ACAD-001_chunks.json"
        if not artifact_path.exists():
            pytest.skip(f"Chunk artifact {artifact_path} not found")

        artifact = deserialize_chunked_artifact(artifact_path)
        embedded_chunks = embedding_coordinator.embed_document_artifact(artifact)

        assert len(embedded_chunks) == len(artifact.chunks)
        assert len(embedded_chunks) > 0

        first_chunk = embedded_chunks[0]
        assert first_chunk.doc_id == "DOC-ACAD-001"
        assert len(first_chunk.embedding) == 384
        assert first_chunk.embedding_dimension == 384
        assert first_chunk.embedding_model_name == "intfloat/multilingual-e5-small"
        assert first_chunk.embedding_normalized is True
        assert first_chunk.embedding_device == "cpu"
