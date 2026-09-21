"""
Integration tests for Phase 3 Chunking Pipeline.
Tests end-to-end chunking from parsed artifacts across PDF, DOCX, and TXT,
repeated execution determinism, and corpus chunking runner.
"""

import json
import pathlib
import pytest

from app.services.chunking.constants import DEFAULT_CHUNK_SIZE
from app.services.chunking.coordinator import ChunkingCoordinator
from app.services.chunking.exceptions import ArtifactNotFoundError
from app.services.chunking.models import ChunkingConfig
from app.services.chunking.serialization import deserialize_chunked_artifact

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class TestChunkingPipelineIntegration:
    @pytest.fixture
    def coordinator(self, tmp_path):
        config = ChunkingConfig(chunk_size=600, chunk_overlap=100, minimum_chunk_size=1)
        return ChunkingCoordinator(config=config, output_dir=tmp_path)

    def test_chunk_pdf_parsed_artifact(self, coordinator, tmp_path):
        pdf_artifact = PROCESSED_DIR / "DOC-ACAD-001_parsed.json"
        if not pdf_artifact.exists():
            pytest.skip(f"Artifact {pdf_artifact} not found")

        artifact = coordinator.chunk_document_artifact(pdf_artifact)
        assert artifact.source_document["doc_id"] == "DOC-ACAD-001"
        assert artifact.total_chunks > 0
        assert artifact.total_source_characters > 0
        assert len(artifact.chunks) == artifact.total_chunks

        # Check saved file
        saved_file = tmp_path / "DOC-ACAD-001_chunks.json"
        assert saved_file.exists()
        loaded = deserialize_chunked_artifact(saved_file)
        assert loaded.source_document["doc_id"] == "DOC-ACAD-001"
        assert len(loaded.chunks) == artifact.total_chunks

    def test_chunk_docx_parsed_artifact(self, coordinator, tmp_path):
        docx_artifact = PROCESSED_DIR / "DOC-SYLL-001_parsed.json"
        if not docx_artifact.exists():
            pytest.skip(f"Artifact {docx_artifact} not found")

        artifact = coordinator.chunk_document_artifact(docx_artifact)
        assert artifact.source_document["doc_id"] == "DOC-SYLL-001"
        assert artifact.total_chunks > 0
        assert artifact.total_source_characters > 0
        assert len(artifact.chunks) == artifact.total_chunks

    def test_chunk_txt_parsed_artifact(self, coordinator, tmp_path):
        txt_artifact = PROCESSED_DIR / "DOC-CIRC-001_parsed.json"
        if not txt_artifact.exists():
            pytest.skip(f"Artifact {txt_artifact} not found")

        artifact = coordinator.chunk_document_artifact(txt_artifact)
        assert artifact.source_document["doc_id"] == "DOC-CIRC-001"
        assert artifact.total_chunks > 0
        assert artifact.total_source_characters > 0

    def test_repeated_chunking_determinism(self, coordinator, tmp_path):
        pdf_artifact = PROCESSED_DIR / "DOC-ACAD-001_parsed.json"
        if not pdf_artifact.exists():
            pytest.skip(f"Artifact {pdf_artifact} not found")

        art1 = coordinator.chunk_document_artifact(pdf_artifact)
        art2 = coordinator.chunk_document_artifact(pdf_artifact)

        assert art1.total_chunks == art2.total_chunks
        assert art1.total_source_characters == art2.total_source_characters
        assert art1.total_chunk_characters == art2.total_chunk_characters

        for c1, c2 in zip(art1.chunks, art2.chunks):
            assert c1.chunk_id == c2.chunk_id
            assert c1.text_content == c2.text_content
            assert c1.source_start_offset == c2.source_start_offset
            assert c1.source_end_offset == c2.source_end_offset
            assert c1.page_number == c2.page_number
            assert c1.section_title == c2.section_title
            assert c1.heading_level == c2.heading_level

    def test_missing_artifact_raises_error(self, coordinator, tmp_path):
        missing = tmp_path / "NON_EXISTENT_parsed.json"
        with pytest.raises(ArtifactNotFoundError):
            coordinator.chunk_document_artifact(missing)

    def test_corpus_batch_chunking(self, tmp_path):
        config = ChunkingConfig(chunk_size=600, chunk_overlap=100)
        coord = ChunkingCoordinator(config=config, output_dir=tmp_path)
        report = coord.chunk_corpus(input_dir=PROCESSED_DIR)

        assert report.total_discovered_documents >= 24
        assert report.total_successful == report.total_discovered_documents
        assert report.total_failed == 0
        assert report.total_chunks_generated > 0
        assert (tmp_path / "corpus_chunking_report.json").exists()
