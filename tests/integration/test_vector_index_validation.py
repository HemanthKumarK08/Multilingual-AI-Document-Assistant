"""
Integration tests for Vector Store indexing, persistence across restarts, and validation.
"""

import pathlib
import pytest

from app.services.chunking.serialization import deserialize_chunked_artifact
from app.services.embeddings.coordinator import EmbeddingCoordinator
from app.services.vector_store.coordinator import VectorStoreCoordinator
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.chroma_client import get_persistent_chroma_client

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class TestVectorIndexValidationIntegration:
    @pytest.fixture
    def vector_coordinator(self, tmp_path):
        vec_config = VectorStoreConfig(
            persist_directory=str(tmp_path / "chroma_integration"),
            collection_name="integration_chunks",
            distance_metric="cosine",
        )
        return VectorStoreCoordinator(vector_config=vec_config)

    def test_end_to_end_indexing_and_persistence(self, vector_coordinator, tmp_path):
        artifact_path = PROCESSED_DIR / "DOC-ACAD-001_chunks.json"
        if not artifact_path.exists():
            pytest.skip(f"Chunk artifact {artifact_path} not found")

        artifact = deserialize_chunked_artifact(artifact_path)
        ins, upd, skp = vector_coordinator.index_document_artifact(artifact)

        assert ins == len(artifact.chunks)
        assert upd == 0
        assert skp == 0

        # Verify collection count
        collection = vector_coordinator.get_collection()
        assert collection.count() == len(artifact.chunks)

        # Verify validation suite
        val_res = vector_coordinator.verify_index()
        assert val_res["status"] == "valid"
        assert val_res["total_records"] == len(artifact.chunks)
        assert val_res["dimension"] == 384

        # Test persistence across a fresh client instantiation
        fresh_client = get_persistent_chroma_client(tmp_path / "chroma_integration")
        fresh_col = fresh_client.get_collection(name="integration_chunks")
        assert fresh_col.count() == len(artifact.chunks)

    def test_idempotent_reindexing(self, vector_coordinator):
        artifact_path = PROCESSED_DIR / "DOC-ACAD-001_chunks.json"
        if not artifact_path.exists():
            pytest.skip(f"Chunk artifact {artifact_path} not found")

        artifact = deserialize_chunked_artifact(artifact_path)
        # First index
        vector_coordinator.index_document_artifact(artifact)
        
        # Second index -> all should be skipped
        ins2, upd2, skp2 = vector_coordinator.index_document_artifact(artifact)
        assert ins2 == 0
        assert upd2 == 0
        assert skp2 == len(artifact.chunks)
