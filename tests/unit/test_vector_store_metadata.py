"""
Unit tests for metadata serialization and deserialization in ChromaDB.
"""

import pytest
from app.services.embeddings.models import EmbeddedChunk
from app.services.vector_store.metadata import serialize_chunk_metadata, deserialize_chunk_metadata


class TestVectorStoreMetadata:
    def test_serialize_and_deserialize_chunk_metadata(self):
        chunk = EmbeddedChunk(
            chunk_id="DOC-ACAD-001:p1:c0",
            doc_id="DOC-ACAD-001",
            file_hash_sha256="12345678" * 8,
            filename="DOC-ACAD-001.txt",
            category="academic_regulations",
            language="en",
            script="latin",
            page_number=1,
            section_title="Program Structure",
            heading_level=1,
            chunk_index=0,
            text_content="Credit framework content.",
            text_length=25,
            source_start_offset=0,
            source_end_offset=25,
            source_unit_index=0,
            parser_name="TxtParser",
            parser_version="1.0.0",
            version="1.0",
            extraction_notes=["Note 1", "Note 2"],
            embedding=[0.1] * 384,
            embedding_model_name="intfloat/multilingual-e5-small",
            embedding_dimension=384,
            embedding_device="cpu",
            embedding_normalized=True,
            vector_index_version=1,
        )

        serialized = serialize_chunk_metadata(chunk)

        # All values in serialized metadata must be scalar types (str, int, float, bool)
        for key, val in serialized.items():
            assert isinstance(val, (str, int, float, bool)), f"Non-scalar type for {key}: {type(val)}"

        assert serialized["chunk_id"] == "DOC-ACAD-001:p1:c0"
        assert serialized["page_number"] == 1
        assert serialized["extraction_notes"] == '["Note 1", "Note 2"]'

        deserialized = deserialize_chunk_metadata(serialized)
        assert deserialized["extraction_notes"] == ["Note 1", "Note 2"]
