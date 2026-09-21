"""
Unit tests for ChunkingCoordinator covering artifact loading, metadata resolution,
single-document processing, database count updates, and error handling.
"""

import json
import pathlib
import pytest

from app.services.chunking.coordinator import ChunkingCoordinator
from app.services.chunking.exceptions import ArtifactNotFoundError, ChunkValidationError
from app.services.chunking.models import ChunkingConfig
from app.services.ingestion.models import ExtractedBlock, ExtractedPage, ParsedDocument


class TestChunkingCoordinator:
    @pytest.fixture
    def coordinator(self, tmp_path):
        config = ChunkingConfig(chunk_size=500, chunk_overlap=50)
        return ChunkingCoordinator(config=config, output_dir=tmp_path)

    @pytest.fixture
    def sample_parsed_doc(self):
        page = ExtractedPage(
            page_number=1,
            text="Header\nSample paragraph text for coordinator testing.",
            blocks=[
                ExtractedBlock(
                    block_type="paragraph",
                    text="Header\nSample paragraph text for coordinator testing.",
                    section_title="Testing Section",
                    heading_level=1,
                )
            ],
            warnings=[],
        )
        return ParsedDocument(
            doc_id="DOC-COORD-TEST",
            filename="coord_test.txt",
            file_type="txt",
            parser_name="TxtParser",
            parser_version="1.0.0",
            page_count=1,
            raw_text=page.text,
            normalized_text=page.text,
            pages=[page],
            sections=[],
            detected_language="en",
            detected_script="Latin",
            language_confidence=1.0,
            warnings=[],
            metadata={"file_hash_sha256": "abc12345" * 8, "category": "test"},
        )

    def test_chunk_parsed_document_in_memory_and_save(self, coordinator, sample_parsed_doc, tmp_path):
        artifact = coordinator.chunk_parsed_document(sample_parsed_doc, save_artifact=True)
        assert artifact.source_document["doc_id"] == "DOC-COORD-TEST"
        assert artifact.total_chunks == 1
        assert (tmp_path / "DOC-COORD-TEST_chunks.json").exists()

    def test_chunk_parsed_document_without_saving(self, coordinator, sample_parsed_doc, tmp_path):
        artifact = coordinator.chunk_parsed_document(sample_parsed_doc, save_artifact=False)
        assert artifact.source_document["doc_id"] == "DOC-COORD-TEST"
        assert not (tmp_path / "DOC-COORD-TEST_chunks.json").exists()

    def test_chunk_parsed_file_not_found(self, coordinator, tmp_path):
        missing = tmp_path / "non_existent_parsed.json"
        with pytest.raises(ArtifactNotFoundError):
            coordinator.chunk_parsed_file(missing)

    def test_table_marker_preservation(self, coordinator):
        table_text = (
            "[TABLE]\n"
            "Caption: Grading Scale\n"
            "Grade | Marks | Points\n"
            "----------------------\n"
            "O     | >=90% | 10\n"
            "A+    | 80-89%| 9\n"
            "[/TABLE]"
        )
        page = ExtractedPage(
            page_number=1,
            text=table_text,
            blocks=[
                ExtractedBlock(
                    block_type="table",
                    text=table_text,
                    section_title="Grading",
                    heading_level=2,
                )
            ],
            warnings=[],
        )
        doc = ParsedDocument(
            doc_id="DOC-TABLE-TEST",
            filename="table_test.txt",
            file_type="txt",
            parser_name="TxtParser",
            parser_version="1.0.0",
            page_count=1,
            raw_text=table_text,
            normalized_text=table_text,
            pages=[page],
            sections=[],
            detected_language="en",
            detected_script="Latin",
            language_confidence=1.0,
            warnings=[],
            metadata={"file_hash_sha256": "tablehash" * 8, "category": "academic"},
        )

        artifact = coordinator.chunk_parsed_document(doc, save_artifact=False)
        assert len(artifact.chunks) >= 1
        combined = " ".join(c.text_content for c in artifact.chunks)
        assert "[TABLE]" in combined
        assert "[/TABLE]" in combined
