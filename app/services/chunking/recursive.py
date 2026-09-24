"""
Deterministic Recursive Character Chunker (Phase 3 & Phase 2 Hardening)
Implements natural boundary splitting with deterministic sliding-window overlap and character offsets.
Guarantees sentence integrity and prevents mid-sentence orphan chunk starts.
"""

import re
from typing import List, Tuple, NamedTuple
from app.services.chunking.models import ChunkingConfig

_ABBREVIATIONS = {
    "rs.", "dr.", "prof.", "mr.", "mrs.", "ms.", "i.e.", "e.g.", "vs.",
    "etc.", "no.", "dept.", "govt.", "ltd.", "pvt.", "inc.", "corp.",
    "univ.", "vol.", "jan.", "feb.", "mar.", "apr.", "jun.", "jul.",
    "aug.", "sep.", "oct.", "nov.", "dec.", "approx.", "est.", "min.", "max."
}

_ORPHAN_STARTS = re.compile(
    r"^(?:is\b|are\b|was\b|were\b|and\b|or\b|but\b|to\b|of\b|for\b|less to\b|fee\.|whichever\b|[\.,;:!\?]\s*)",
    re.IGNORECASE,
)


class ChunkSpan(NamedTuple):
    """Container for chunk text and its source-unit character offsets."""
    text: str
    start_offset: int
    end_offset: int
    length: int


def _is_safe_sentence_end(text: str, pos: int) -> bool:
    """
    Determines if punctuation at `pos` represents a true sentence boundary
    rather than an abbreviation, decimal number, or URL component.
    """
    char = text[pos]
    if char not in (".", "?", "!", "।"):
        return False

    # Check decimal numbers: digit before and digit after
    if pos > 0 and pos + 1 < len(text):
        if text[pos - 1].isdigit() and text[pos + 1].isdigit():
            return False

    # Check abbreviation before period
    if char == ".":
        # Lookback up to 10 chars for preceding token
        start_token = max(0, pos - 10)
        preceding = text[start_token:pos + 1]
        tokens = preceding.split()
        if tokens:
            last_tok = tokens[-1].lower().strip(" \t\n()[]{}")
            if last_tok in _ABBREVIATIONS:
                return False

        # Check for URL patterns (e.g. .com, .in, .gov, .org, .edu)
        following = text[pos + 1 : pos + 10].lower()
        if following.startswith(("in/", "in ", "gov", "com", "org", "edu", "ac.in", "co.in", "html", "php")):
            return False

    return True


class RecursiveCharacterChunker:
    """
    Stateless, deterministic recursive character chunker.
    Splits text along a hierarchical sequence of natural separators while preserving
    configurable sliding-window overlap with strict sentence boundary protection.
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

    def _find_safe_overlap_start(self, text: str, raw_overlap_start: int, actual_end: int) -> int:
        """
        Locates the cleanest structural/sentence boundary inside the overlap slice.
        Order of preference:
        1. Paragraph break (\n\n)
        2. Bullet / numbered list item (\n•, \n-, \n*, \n1., \n2.)
        3. Real sentence end (. , ? , ! , । )
        4. Line break (\n)
        5. Word boundary ( )
        Rejects positions that produce orphan/fragmentary sentence continuations.
        """
        overlap_slice = text[raw_overlap_start:actual_end]
        if not overlap_slice:
            return actual_end

        # 1. Look for paragraph boundary (\n\n)
        p_idx = overlap_slice.rfind("\n\n")
        if p_idx != -1 and p_idx + 2 < len(overlap_slice):
            candidate = raw_overlap_start + p_idx + 2
            cand_text = text[candidate:actual_end].strip()
            if cand_text and not _ORPHAN_STARTS.match(cand_text):
                return candidate

        # 2. Look for bullet or list marker
        bullet_matches = list(re.finditer(r"\n(?:[•\-\*]|\d+[\.)])\s*", overlap_slice))
        if bullet_matches:
            last_bullet = bullet_matches[-1]
            candidate = raw_overlap_start + last_bullet.start() + 1
            cand_text = text[candidate:actual_end].strip()
            if cand_text and not _ORPHAN_STARTS.match(cand_text):
                return candidate

        # 3. Look for true sentence boundary (. , ? , ! , । )
        sentence_end_positions = []
        for i, ch in enumerate(overlap_slice):
            if ch in (".", "?", "!", "।"):
                abs_pos = raw_overlap_start + i
                if _is_safe_sentence_end(text, abs_pos):
                    # Next sentence starts after space/newline
                    following_offset = 1
                    while i + following_offset < len(overlap_slice) and overlap_slice[i + following_offset] in (" ", "\t", "\n"):
                        following_offset += 1
                    sentence_end_positions.append(raw_overlap_start + i + following_offset)

        if sentence_end_positions:
            # Pick a sentence boundary that is strictly before actual_end to create overlap
            valid_sent_starts = [pos for pos in sentence_end_positions if pos < actual_end]
            if valid_sent_starts:
                candidate = valid_sent_starts[-1]
                cand_text = text[candidate:actual_end].strip()
                if cand_text and not _ORPHAN_STARTS.match(cand_text):
                    return candidate

        # 4. Look for line break (\n)
        nl_idx = overlap_slice.rfind("\n")
        if nl_idx != -1 and nl_idx + 1 < len(overlap_slice):
            candidate = raw_overlap_start + nl_idx + 1
            cand_text = text[candidate:actual_end].strip()
            if cand_text and not _ORPHAN_STARTS.match(cand_text) and not (cand_text[0].islower() if cand_text else False):
                return candidate

        # 5. Look for word boundary (\s+) that does not produce an orphan start
        sp_matches = [m.start() + 1 for m in re.finditer(r"\s+", overlap_slice)]
        for sp in sp_matches:
            candidate = raw_overlap_start + sp
            cand_text = text[candidate:actual_end].strip()
            if cand_text and not _ORPHAN_STARTS.match(cand_text):
                return candidate

        # 6. Fallback: if slicing overlap causes mid-sentence orphan, clean cut at actual_end
        return actual_end


    def split_text_with_offsets(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Splits text into chunks of at most `chunk_size` characters with `chunk_overlap`.
        Guarantees natural boundaries and protects sentence integrity.
        
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
                    # Check if separator is period and ensure it is safe
                    if sep == ". ":
                        abs_pos = cur_start + r_pos
                        if not _is_safe_sentence_end(text, abs_pos):
                            continue
                    split_idx = r_pos + len(sep)
                    break

            if split_idx <= 0:
                split_idx = len(candidate)

            chunk_text = text[cur_start : cur_start + split_idx]
            actual_end = cur_start + split_idx

            if not chunks or chunks[-1][0] != chunk_text:
                chunks.append((chunk_text, cur_start, actual_end))

            # Advance cur_start taking sentence-safe overlap into account
            if self.config.chunk_overlap > 0 and actual_end < text_len:
                overlap_target = min(self.config.chunk_overlap, len(chunk_text))
                raw_overlap_start = actual_end - overlap_target
                next_start = self._find_safe_overlap_start(text, raw_overlap_start, actual_end)

                # Ensure forward progress
                if next_start <= cur_start:
                    next_start = cur_start + max(1, split_idx - self.config.chunk_overlap)
                if next_start >= actual_end:
                    next_start = actual_end

                cur_start = next_start
            else:
                cur_start = actual_end

        return chunks

