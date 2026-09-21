"""
Unit tests for PageAwareBoundaryManager testing page isolation, section context retention,
and provenance propagation.
"""

import pytest

from app.services.chunking.boundaries import PageAwareBoundaryManager
from app.services.chunking.models import ChunkingConfig
from app.services.ingestion.models import ExtractedBlock, ExtractedPage, ParsedDocument


class TestPageAwareBoundaryManager:
    @pytest.fixture
    def sample_parsed_doc(self):
        page1 = ExtractedPage(
            page_number=1,
            text="Introduction Section\nWelcome to the official handbook.\nThis handbook covers academic regulations, code of conduct, and grading policies.",
            blocks=[
                ExtractedBlock(
                    block_type="heading",
                    text="Introduction Section\nWelcome to the official handbook.",
                    section_title="Introduction Section",
                    heading_level=1,
                ),
                ExtractedBlock(
                    block_type="paragraph",
                    text="This handbook covers academic regulations, code of conduct, and grading policies.",
                    section_title="Introduction Section",
                    heading_level=1,
                ),
            ],
            warnings=[],
        )

        page2 = ExtractedPage(
            page_number=2,
            text="Fee Regulations\nTuition fees must be paid per semester.\nLate fee penalties apply after the deadline of 30th September.",
            blocks=[
                ExtractedBlock(
                    block_type="heading",
                    text="Fee Regulations\nTuition fees must be paid per semester.",
                    section_title="Fee Regulations",
                    heading_level=2,
                ),
                ExtractedBlock(
                    block_type="paragraph",
                    text="Late fee penalties apply after the deadline of 30th September.",
                    section_title="Fee Regulations",
                    heading_level=2,
                ),
            ],
            warnings=[],
        )

        raw_txt = page1.text + "\n" + page2.text
        return ParsedDocument(
            doc_id="DOC-TEST-001",
            filename="handbook.pdf",
            file_type="pdf",
            parser_name="pypdf",
            parser_version="5.3.0",
            page_count=2,
            raw_text=raw_txt,
            normalized_text=raw_txt,
            pages=[page1, page2],
            sections=[],
            detected_language="en",
            detected_script="Latin",
            language_confidence=1.0,
            warnings=[],
            metadata={"file_hash_sha256": "1234567890abcdef" * 4, "category": "handbook", "version": "1.0"},
        )

    def test_page_boundaries_strictly_preserved(self, sample_parsed_doc):
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, minimum_chunk_size=1)
        manager = PageAwareBoundaryManager(config=config)
        chunks = manager.chunk_document(sample_parsed_doc)

        assert len(chunks) > 0

        # Check page numbers
        page1_chunks = [c for c in chunks if c.page_number == 1]
        page2_chunks = [c for c in chunks if c.page_number == 2]

        assert len(page1_chunks) > 0
        assert len(page2_chunks) > 0
        assert len(page1_chunks) + len(page2_chunks) == len(chunks)

        # Check chunk indices are sequential document-global 0..N-1
        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_index == idx
            assert chunk.chunk_id == f"DOC-TEST-001:p{chunk.page_number}:c{idx}"

    def test_section_title_propagation(self, sample_parsed_doc):
        config = ChunkingConfig(chunk_size=150, chunk_overlap=20, minimum_chunk_size=1)
        manager = PageAwareBoundaryManager(config=config)
        chunks = manager.chunk_document(sample_parsed_doc)

        for chunk in chunks:
            if chunk.page_number == 1:
                assert chunk.section_title == "Introduction Section"
                assert chunk.heading_level == 1
            elif chunk.page_number == 2:
                assert chunk.section_title == "Fee Regulations"
                assert chunk.heading_level == 2

    def test_provenance_fields_populated(self, sample_parsed_doc):
        config = ChunkingConfig(chunk_size=600, chunk_overlap=100)
        manager = PageAwareBoundaryManager(config=config)
        chunks = manager.chunk_document(sample_parsed_doc)

        for chunk in chunks:
            assert chunk.doc_id == "DOC-TEST-001"
            assert chunk.file_hash_sha256 == "1234567890abcdef" * 4
            assert chunk.filename == "handbook.pdf"
            assert chunk.category == "handbook"
            assert chunk.language == "en"
            assert chunk.script == "Latin"
            assert chunk.parser_name == "pypdf"
            assert chunk.parser_version == "5.3.0"
            assert chunk.version == "1.0"
            assert chunk.text_length == len(chunk.text_content)
            assert chunk.source_start_offset >= 0
            assert chunk.source_end_offset > chunk.source_start_offset
