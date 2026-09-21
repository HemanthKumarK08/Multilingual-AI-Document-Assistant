"""
Deterministic Recursive Character Chunker (Phase 3)
Implements natural boundary splitting with deterministic sliding-window overlap and character offsets.
"""

from typing import List, Tuple, NamedTuple
from app.services.chunking.models import ChunkingConfig


class ChunkSpan(NamedTuple):
    """Container for chunk text and its source-unit character offsets."""
    text: str
    start_offset: int
    end_offset: int
    length: int


class RecursiveCharacterChunker:
    """
    Stateless, deterministic recursive character chunker.
    Splits text along a hierarchical sequence of natural separators while preserving
    configurable sliding-window overlap.
    """

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def chunk_text(self, text: str) -> List[ChunkSpan]:
        """Convenience method returning List[ChunkSpan]."""
        raw_chunks = self.split_text_with_offsets(text)
        return [
            ChunkSpan(
                text=chunk_text,
                start_offset=start_off,
                end_offset=end_off,
                length=len(chunk_text),
            )
            for chunk_text, start_off, end_off in raw_chunks
        ]

    def split_text_with_offsets(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Splits text into chunks of at most `chunk_size` characters with `chunk_overlap`.
        
        Returns:
            List of (chunk_text, start_offset, end_offset) tuples.
            Offsets are 0-indexed relative to input `text` (start: inclusive, end: exclusive).
        """
        if not text or not text.strip():
            return []

        text_len = len(text)

        # Base case: text fits entirely within chunk_size
        if text_len <= self.config.chunk_size:
            return [(text, 0, text_len)]

        chunks: List[Tuple[str, int, int]] = []
        cur_start = 0

        while cur_start < text_len:
            # Candidate slice up to chunk_size
            cur_end = min(cur_start + self.config.chunk_size, text_len)
            
            # If remaining text fits entirely within chunk_size
            if cur_end == text_len:
                chunk_str = text[cur_start:cur_end]
                if not chunks or chunks[-1][0] != chunk_str:
                    chunks.append((chunk_str, cur_start, cur_end))
                break

            # Text slice under consideration
            candidate = text[cur_start:cur_end]

            # Find best natural split point within candidate using separator hierarchy
            split_idx = -1
            for sep in self.config.separators:
                if sep == "":
                    # Character fallback
                    split_idx = len(candidate)
                    break
                
                # Look for separator in the second half of candidate to maximize chunk fullness
                min_search_pos = max(1, len(candidate) // 3)
                r_pos = candidate.rfind(sep, min_search_pos)
                if r_pos != -1:
                    split_idx = r_pos + len(sep)
                    break

            if split_idx <= 0:
                split_idx = len(candidate)

            chunk_text = text[cur_start : cur_start + split_idx]
            actual_end = cur_start + split_idx

            if not chunks or chunks[-1][0] != chunk_text:
                chunks.append((chunk_text, cur_start, actual_end))

            # Advance cur_start taking overlap into account
            if self.config.chunk_overlap > 0 and actual_end < text_len:
                overlap_target = min(self.config.chunk_overlap, len(chunk_text))
                raw_overlap_start = actual_end - overlap_target

                # Try to align overlap start to a natural word boundary
                overlap_slice = text[raw_overlap_start:actual_end]
                space_pos = overlap_slice.find(" ")
                if space_pos != -1 and space_pos < len(overlap_slice) - 1:
                    next_start = raw_overlap_start + space_pos + 1
                else:
                    next_start = raw_overlap_start

                # Ensure forward progress
                if next_start <= cur_start:
                    next_start = cur_start + max(1, split_idx - self.config.chunk_overlap)
                if next_start >= actual_end:
                    next_start = actual_end

                cur_start = next_start
            else:
                cur_start = actual_end

        return chunks
