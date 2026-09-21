"""
Unit tests for indexing idempotency, hash change detection, and stale-record handling.
"""

import pytest
from app.services.embeddings.models import EmbeddedChunk
from app.services.vector_store.chroma_client import get_persistent_chroma_client
from app.services.vector_store.collection import get_or_create_collection
from app.services.vector_store.models import VectorStoreConfig
from app.services.vector_store.indexing import (
    upsert_embedded_chunks,
    detect_stale_records,
    remove_stale_records,
)


def _create_sample_embedded_chunk(chunk_id="DOC-001:p1:c0", file_hash="hash1", text="Text 1"):
    return EmbeddedChunk(
        chunk_id=chunk_id,
        doc_id="DOC-001",
        file_hash_sha256=file_hash,
        filename="doc.txt",
        category="general",
        language="en",
        script="latin",
        page_number=1,
        section_title="Intro",
        heading_level=1,
        chunk_index=0,
        text_content=text,
        text_length=len(text),
        source_start_offset=0,
        source_end_offset=len(text),
        source_unit_index=0,
        parser_name="txt",
        parser_version="1.0",
        version="1.0",
        extraction_notes=[],
        embedding=[0.05] * 384,
        embedding_model_name="intfloat/multilingual-e5-small",
        embedding_dimension=384,
        embedding_device="cpu",
        embedding_normalized=True,
    )


class TestIndexingIdempotency:
    @pytest.fixture
    def test_collection(self, tmp_path):
        client = get_persistent_chroma_client(tmp_path / "idempotency_chroma")
        config = VectorStoreConfig(
            persist_directory=str(tmp_path / "idempotency_chroma"),
            collection_name="idempotent_chunks",
        )
        return get_or_create_collection(
            client=client,
            config=config,
            embedding_model_name="intfloat/multilingual-e5-small",
            dimension=384,
        )

    def test_idempotent_repeated_upsert(self, test_collection):
        chunks = [
            _create_sample_embedded_chunk("DOC-001:p1:c0", "hash1", "Text 1"),
            _create_sample_embedded_chunk("DOC-001:p1:c1", "hash1", "Text 2"),
        ]

        # 1. Initial insert
        ins, upd, skp = upsert_embedded_chunks(test_collection, chunks)
        assert ins == 2
        assert upd == 0
        assert skp == 0
        assert test_collection.count() == 2

        # 2. Repeated insert with identical content -> should skip
        ins2, upd2, skp2 = upsert_embedded_chunks(test_collection, chunks)
        assert ins2 == 0
        assert upd2 == 0
        assert skp2 == 2
        assert test_collection.count() == 2

    def test_changed_hash_triggers_update(self, test_collection):
        c1 = _create_sample_embedded_chunk("DOC-001:p1:c0", "hash_old", "Old Text")
        upsert_embedded_chunks(test_collection, [c1])

        # Updated hash
        c1_new = _create_sample_embedded_chunk("DOC-001:p1:c0", "hash_new", "New Updated Text")
        ins, upd, skp = upsert_embedded_chunks(test_collection, [c1_new])
        assert ins == 0
        assert upd == 1
        assert skp == 0
        assert test_collection.count() == 1

        # Check updated document text in ChromaDB
        rec = test_collection.get(ids=["DOC-001:p1:c0"], include=["documents", "metadatas"])
        assert rec["documents"][0] == "New Updated Text"
        assert rec["metadatas"][0]["file_hash_sha256"] == "hash_new"

    def test_stale_record_detection_and_removal(self, test_collection):
        c1 = _create_sample_embedded_chunk("DOC-001:p1:c0")
        c2 = _create_sample_embedded_chunk("DOC-001:p1:c1")
        upsert_embedded_chunks(test_collection, [c1, c2])

        # If corpus now only contains c1, then c2 is stale
        stale_report = detect_stale_records(test_collection, expected_chunk_ids={"DOC-001:p1:c0"})
        assert stale_report.stale_count == 1
        assert stale_report.stale_chunk_ids == ["DOC-001:p1:c1"]

        # Controlled removal
        removed = remove_stale_records(test_collection, stale_report.stale_chunk_ids)
        assert removed == 1
        assert test_collection.count() == 1
