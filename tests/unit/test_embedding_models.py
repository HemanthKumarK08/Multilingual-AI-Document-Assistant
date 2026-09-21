"""
Unit tests for EmbeddedChunk, VectorRecord, and Report models.
"""

import pytest
from app.services.embeddings.models import EmbeddedChunk, EmbeddingBatchResult, EmbeddingRunReport
from app.services.vector_store.models import VectorRecord, IndexStats, StaleRecordReport


class TestEmbeddingModels:
    def test_valid_embedded_chunk(self):
        chunk = EmbeddedChunk(
            chunk_id="DOC-001:p1:c0",
            doc_id="DOC-001",
            file_hash_sha256="a" * 64,
            filename="sample.txt",
            category="academic",
            language="en",
            script="Latin",
            page_number=1,
            section_title="Intro",
            heading_level=1,
            chunk_index=0,
            text_content="Sample text content for embedding test.",
            text_length=40,
            source_start_offset=0,
            source_end_offset=40,
            source_unit_index=0,
            parser_name="txt_parser",
            parser_version="1.0.0",
            version="1.0",
            extraction_notes=[],
            embedding=[0.1] * 384,
            embedding_model_name="intfloat/multilingual-e5-small",
            embedding_dimension=384,
            embedding_device="cpu",
            embedding_normalized=True,
        )
        assert chunk.chunk_id == "DOC-001:p1:c0"
        assert len(chunk.embedding) == 384
        assert chunk.embedding_dimension == 384

    def test_embedding_batch_result(self):
        res = EmbeddingBatchResult(
            total_texts=2,
            dimension=384,
            embeddings=[[0.1] * 384, [0.2] * 384],
            elapsed_seconds=0.05,
        )
        assert res.total_texts == 2
        assert len(res.embeddings) == 2

    def test_stale_record_report(self):
        rep = StaleRecordReport(
            total_existing_in_collection=10,
            total_expected_in_corpus=8,
            stale_count=2,
            stale_chunk_ids=["DOC-001:p1:c8", "DOC-001:p1:c9"],
            missing_count=0,
            missing_chunk_ids=[],
        )
        assert rep.stale_count == 2
        assert len(rep.stale_chunk_ids) == 2
