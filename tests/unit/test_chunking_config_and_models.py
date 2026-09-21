"""
Unit tests for Chunking Configuration, Models, Validator, and Serialization.
"""

import json
import pytest
from pydantic import ValidationError

from app.services.chunking.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MINIMUM_CHUNK_SIZE,
)
from app.services.chunking.exceptions import (
    ChunkValidationError,
    InvalidChunkConfigError,
    SourceCoverageError,
)
from app.services.chunking.models import (
    ChunkedDocumentArtifact,
    ChunkingConfig,
    DocumentChunk,
)
from app.services.chunking.serialization import (
    deserialize_chunked_artifact,
    serialize_chunked_artifact,
)
from app.services.chunking.validator import ChunkValidator


class TestChunkingConfig:
    def test_default_config(self):
        config = ChunkingConfig()
        assert config.chunk_size == 600
        assert config.chunk_overlap == 100
        assert config.minimum_chunk_size == 1
        assert len(config.separators) > 0

    def test_custom_valid_config(self):
        config = ChunkingConfig(
            chunk_size=500,
            chunk_overlap=50,
            minimum_chunk_size=5,
        )
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.minimum_chunk_size == 5

    def test_zero_overlap_allowed(self):
        config = ChunkingConfig(chunk_size=600, chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_invalid_chunk_size_too_small(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=0)

    def test_invalid_chunk_size_negative(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=-100)

    def test_invalid_chunk_size_too_large(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=5000)

    def test_invalid_overlap_greater_than_chunk_size(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=500, chunk_overlap=600)

    def test_invalid_overlap_equal_to_chunk_size(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=500, chunk_overlap=500)

    def test_invalid_overlap_negative(self):
        with pytest.raises((ValidationError, InvalidChunkConfigError)):
            ChunkingConfig(chunk_size=500, chunk_overlap=-10)


class TestDocumentChunkModel:
    def test_valid_document_chunk(self):
        chunk = DocumentChunk(
            chunk_id="DOC-ACAD-001:p1:c0",
            doc_id="DOC-ACAD-001",
            file_hash_sha256="a" * 64,
            filename="test.pdf",
            category="academic",
            language="en",
            script="Latin",
            page_number=1,
            section_title="Introduction",
            heading_level=1,
            chunk_index=0,
            text_content="This is sample text content for testing chunk model.",
            text_length=52,
            source_start_offset=0,
            source_end_offset=52,
            source_unit_index=0,
            parser_name="pypdf",
            parser_version="5.3.0",
            version="1.0",
            extraction_notes=[],
        )
        assert chunk.chunk_id == "DOC-ACAD-001:p1:c0"
        assert chunk.text_length == 52
        assert chunk.page_number == 1
        assert chunk.chunk_index == 0

    def test_chunk_text_length_mismatch_fails_validation(self):
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id="DOC-ACAD-001:p1:c0",
                doc_id="DOC-ACAD-001",
                file_hash_sha256="a" * 64,
                filename="test.pdf",
                category="academic",
                language="en",
                script="Latin",
                page_number=1,
                section_title="Introduction",
                heading_level=1,
                chunk_index=0,
                text_content="Hello world",
                text_length=999,  # Mismatch
                source_start_offset=0,
                source_end_offset=11,
                source_unit_index=0,
                parser_name="pypdf",
                parser_version="5.3.0",
                version="1.0",
            )

    def test_negative_offset_fails_validation(self):
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id="DOC-ACAD-001:p1:c0",
                doc_id="DOC-ACAD-001",
                file_hash_sha256="a" * 64,
                filename="test.pdf",
                category="academic",
                language="en",
                script="Latin",
                page_number=1,
                section_title=None,
                heading_level=None,
                chunk_index=0,
                text_content="Hello",
                text_length=5,
                source_start_offset=-1,
                source_end_offset=4,
                source_unit_index=0,
                parser_name="pypdf",
                parser_version="5.3.0",
                version="1.0",
            )


class TestChunkValidator:
    def _create_sample_chunk(self, doc_id="DOC-001", page=1, chunk_idx=0, text="Sample text", start=0, end=11):
        return DocumentChunk(
            chunk_id=f"{doc_id}:p{page}:c{chunk_idx}",
            doc_id=doc_id,
            file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            filename="doc.pdf",
            category="general",
            language="en",
            script="Latin",
            page_number=page,
            section_title="Overview",
            heading_level=1,
            chunk_index=chunk_idx,
            text_content=text,
            text_length=len(text),
            source_start_offset=start,
            source_end_offset=end,
            source_unit_index=0,
            parser_name="pypdf",
            parser_version="5.3.0",
            version="1.0",
        )

    def test_validate_valid_chunks(self):
        validator = ChunkValidator()
        config = ChunkingConfig()
        chunks = [
            self._create_sample_chunk(chunk_idx=0, text="First chunk content", start=0, end=19),
            self._create_sample_chunk(chunk_idx=1, text="Second chunk content", start=19, end=39),
        ]
        validator.validate_document_chunks(
            chunks=chunks,
            doc_id="DOC-001",
            config=config,
            source_text_map={1: "First chunk content Second chunk content"},
        )

    def test_validate_empty_chunks_list_rejected(self):
        validator = ChunkValidator()
        config = ChunkingConfig()
        with pytest.raises(ChunkValidationError):
            validator.validate_document_chunks([], doc_id="DOC-001", config=config)

    def test_validate_non_sequential_index_rejected(self):
        validator = ChunkValidator()
        config = ChunkingConfig()
        chunks = [
            self._create_sample_chunk(chunk_idx=0),
            self._create_sample_chunk(chunk_idx=2),  # Skipped 1
        ]
        with pytest.raises(ChunkValidationError):
            validator.validate_document_chunks(chunks, doc_id="DOC-001", config=config)

    def test_validate_duplicate_chunk_id_rejected(self):
        validator = ChunkValidator()
        config = ChunkingConfig()
        c1 = self._create_sample_chunk(chunk_idx=0)
        c2 = self._create_sample_chunk(chunk_idx=1)
        c2.chunk_id = c1.chunk_id  # Force duplicate ID
        with pytest.raises(ChunkValidationError):
            validator.validate_document_chunks([c1, c2], doc_id="DOC-001", config=config)


class TestSerialization:
    def test_serialization_roundtrip(self, tmp_path):
        config = ChunkingConfig()
        chunk = DocumentChunk(
            chunk_id="DOC-TEST:p1:c0",
            doc_id="DOC-TEST",
            file_hash_sha256="abc12345",
            filename="sample.txt",
            category="circular",
            language="en",
            script="Latin",
            page_number=1,
            section_title="Circular Notice",
            heading_level=2,
            chunk_index=0,
            text_content="Official circular text content.",
            text_length=31,
            source_start_offset=0,
            source_end_offset=31,
            source_unit_index=0,
            parser_name="txt_parser",
            parser_version="1.0.0",
            version="1.0",
        )
        artifact = ChunkedDocumentArtifact(
            chunking_config=config,
            source_document={
                "doc_id": "DOC-TEST",
                "file_hash_sha256": "abc12345",
                "filename": "sample.txt",
                "category": "circular",
                "language": "en",
                "script": "Latin",
                "parser_name": "txt_parser",
                "parser_version": "1.0.0",
                "version": "1.0",
            },
            chunks=[chunk],
            total_chunks=1,
            total_source_characters=31,
            total_chunk_characters=31,
        )

        out_file = tmp_path / "DOC-TEST_chunks.json"
        serialize_chunked_artifact(artifact, out_file)

        assert out_file.exists()
        deserialized = deserialize_chunked_artifact(out_file)
        assert deserialized.source_document["doc_id"] == "DOC-TEST"
        assert len(deserialized.chunks) == 1
        assert deserialized.chunks[0].chunk_id == "DOC-TEST:p1:c0"
        assert deserialized.chunks[0].text_content == "Official circular text content."
