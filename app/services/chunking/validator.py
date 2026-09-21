"""
Chunk Validator Module
Validates chunk schema completeness, ID uniqueness, index continuity, and source text coverage.
"""

import re
from typing import List, Optional, Dict
from app.services.chunking.models import DocumentChunk, ChunkingConfig
from app.services.chunking.exceptions import ChunkValidationError, SourceCoverageError


class ChunkValidator:
    """Validates structural correctness and data integrity of generated document chunks."""

    @staticmethod
    def validate_chunks(
        chunks: List[DocumentChunk],
        config: Optional[ChunkingConfig] = None,
        source_text: Optional[str] = None
    ) -> bool:
        """
        Executes a comprehensive validation suite against a list of DocumentChunks.
        
        Raises:
            ChunkValidationError if any structural constraint is violated.
            SourceCoverageError if source coverage check fails.
        """
        if not chunks:
            # Empty chunks is valid only if source_text is empty
            if source_text and source_text.strip():
                raise ChunkValidationError("Chunker returned 0 chunks for non-empty source text.")
            return True

        seen_ids = set()
        expected_index = 0

        for chunk in chunks:
            # 1. Non-empty text validation
            if not chunk.text_content or not chunk.text_content.strip():
                raise ChunkValidationError(f"Chunk {chunk.chunk_id} contains empty or whitespace-only text.")

            # 2. Text length consistency
            actual_len = len(chunk.text_content)
            if chunk.text_length != actual_len:
                raise ChunkValidationError(
                    f"Chunk {chunk.chunk_id} declared length ({chunk.text_length}) != actual length ({actual_len})."
                )

            # 3. Stable ID pattern check: {doc_id}:p{page_number}:c{chunk_index}
            expected_pattern = rf"^{re.escape(chunk.doc_id)}:p{chunk.page_number}:c{chunk.chunk_index}$"
            if not re.match(expected_pattern, chunk.chunk_id):
                raise ChunkValidationError(
                    f"Chunk ID '{chunk.chunk_id}' violates format '{chunk.doc_id}:p{chunk.page_number}:c{chunk.chunk_index}'."
                )

            # 4. Unique chunk IDs
            if chunk.chunk_id in seen_ids:
                raise ChunkValidationError(f"Duplicate chunk ID detected: {chunk.chunk_id}")
            seen_ids.add(chunk.chunk_id)

            # 5. Sequential chunk indexing
            if chunk.chunk_index != expected_index:
                raise ChunkValidationError(
                    f"Chunk index continuity break: expected {expected_index}, got {chunk.chunk_index} on {chunk.chunk_id}."
                )
            expected_index += 1

            # 6. Page number validity
            if chunk.page_number < 1:
                raise ChunkValidationError(f"Invalid page number {chunk.page_number} on chunk {chunk.chunk_id}.")

            # 7. Offset validity
            if chunk.source_start_offset > chunk.source_end_offset:
                raise ChunkValidationError(
                    f"Invalid offsets ({chunk.source_start_offset} > {chunk.source_end_offset}) on {chunk.chunk_id}."
                )

        # 8. Source Coverage Validation
        if source_text and source_text.strip():
            ChunkValidator._verify_coverage(chunks, source_text)

        return True

    def validate_document_chunks(
        self,
        chunks: List[DocumentChunk],
        doc_id: str,
        config: Optional[ChunkingConfig] = None,
        source_text_map: Optional[Dict[int, str]] = None,
    ) -> bool:
        """
        Instance method version of validate_chunks supporting source_text_map.
        """
        if not chunks:
            raise ChunkValidationError(f"No chunks provided for document {doc_id}")

        combined_source = ""
        if source_text_map:
            combined_source = " ".join(source_text_map.values())

        return self.validate_chunks(chunks=chunks, config=config, source_text=combined_source)

    @staticmethod
    def _verify_coverage(chunks: List[DocumentChunk], source_text: str) -> None:
        """
        Verifies that meaningful content from source text is present across emitted chunks.
        """
        # Tokenize meaningful words from source text
        source_words = [w for w in re.findall(r"\w+", source_text.lower()) if len(w) > 2]
        if not source_words:
            return

        combined_chunk_text = " ".join(c.text_content.lower() for c in chunks)
        
        # Check sample tokens (first, middle, last)
        sample_indices = [0, len(source_words) // 2, len(source_words) - 1]
        for idx in sample_indices:
            word = source_words[idx]
            if word not in combined_chunk_text:
                raise SourceCoverageError(
                    f"Source word '{word}' from source index {idx} was not found in generated chunks."
                )
