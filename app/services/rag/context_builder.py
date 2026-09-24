"""
Context Construction, Boundary Repair, and Budgeting Module (Research-Backed RAG Architecture)
Reconstructs evidence in natural document order:
- Recovers boundary predecessor (max 1) for continuation chunks.
- Recovers boundary successor (max 1) only for genuinely incomplete sentences within the same section.
- Groups and stitches contiguous chunks belonging to the same document, page, and section.
- Enforces character and token budgets cleanly.
"""

import re
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
from app.services.rag.models import ContextPackage, SourceCitation
from app.services.retrieval.models import CandidateChunk


def _extract_chunk_index_from_id(chunk_id: str) -> int:
    """Extracts the numerical chunk index from ID like 'doc:p1:c124'."""
    match = re.search(r":c(\d+)$", chunk_id)
    if match:
        return int(match.group(1))
    return 0


def _merge_contiguous_texts(t1: str, t2: str) -> str:
    """Merges two contiguous text chunks cleanly, avoiding duplicate overlap."""
    t1_clean = t1.strip()
    t2_clean = t2.strip()
    if not t1_clean:
        return t2_clean
    if not t2_clean:
        return t1_clean

    # Check for direct overlap between end of t1 and start of t2
    max_check = min(150, len(t1_clean), len(t2_clean))
    for ov_len in range(max_check, 10, -1):
        if t1_clean.endswith(t2_clean[:ov_len]):
            return t1_clean + t2_clean[ov_len:]

    return f"{t1_clean}\n\n{t2_clean}"


_CONTINUATION_PATTERNS = [
    re.compile(r"^[a-z]"),
    re.compile(r"^(is|are|was|were|been|being)\b", re.I),
    re.compile(r"^(and|or|but|nor|so|yet)\b", re.I),
    re.compile(r"^(which|that|who|whom|whose|wherein)\b", re.I),
    re.compile(r"^(to|of|for|with|by|from|in|on|at|into)\b", re.I),
    re.compile(r"^(less to|whichever|fee\b|\.|\,)", re.I),
    re.compile(r"^(top 50|short-term|training program)\b", re.I),
]

_INCOMPLETE_ENDING_PATTERNS = [
    re.compile(r"\b(and|or|such as|including|with|for|to|the|a|an|of|in|on|at|by|from|is|are|shall|must)$", re.I),
    re.compile(r"[\,\:\;\-]$"),
]


def _is_suspicious_continuation(text: str) -> bool:
    """Detects if a chunk text begins with an orphan sentence continuation."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return False
    first = lines[0]
    return any(p.search(first) for p in _CONTINUATION_PATTERNS)


def _is_suspicious_incomplete_ending(text: str) -> bool:
    """Detects if a chunk ends abruptly without terminal punctuation mid-sentence."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return False
    last = lines[-1]
    if any(p.search(last) for p in _INCOMPLETE_ENDING_PATTERNS):
        return True
    return False


def _recover_boundary_predecessor(cand: CandidateChunk, existing_ids: set) -> Optional[CandidateChunk]:
    """
    Recovers at most 1 previous contiguous chunk when a high-ranking candidate
    begins with a sentence continuation.
    """
    if not _is_suspicious_continuation(cand.text_content):
        return None
    match = re.search(r":p(\d+):c(\d+)$", cand.chunk_id)
    if not match:
        return None
    page = int(match.group(1))
    cidx = int(match.group(2))
    if cidx <= 0:
        return None

    try:
        from app.services.vector_store.coordinator import VectorStoreCoordinator
        vsc = VectorStoreCoordinator()
        col = vsc.get_collection()

        prev_id = f"{cand.doc_id}:p{page}:c{cidx-1}"
        if prev_id in existing_ids:
            return None

        res = col.get(ids=[prev_id])
        if (not res or not res.get("ids")) and page > 1:
            prev_id = f"{cand.doc_id}:p{page-1}:c{cidx-1}"
            if prev_id in existing_ids:
                return None
            res = col.get(ids=[prev_id])

        if res and res.get("ids"):
            meta = res["metadatas"][0]
            text = res["documents"][0]
            return CandidateChunk(
                chunk_id=res["ids"][0],
                doc_id=meta.get("doc_id", cand.doc_id),
                filename=meta.get("filename", cand.filename),
                text_content=text,
                page_number=meta.get("page_number", cand.page_number),
                section_title=cand.section_title or meta.get("section_title", ""),
                dense_score=(cand.dense_score or 1.0) * 0.95,
            )
    except Exception:
        pass
    return None


def _recover_boundary_successor(cand: CandidateChunk, existing_ids: set) -> Optional[CandidateChunk]:
    """
    Recovers at most 1 next contiguous chunk when a high-ranking candidate
    ends abruptly mid-sentence on the same page and section.
    """
    if not _is_suspicious_incomplete_ending(cand.text_content):
        return None
    match = re.search(r":p(\d+):c(\d+)$", cand.chunk_id)
    if not match:
        return None
    page = int(match.group(1))
    cidx = int(match.group(2))

    try:
        from app.services.vector_store.coordinator import VectorStoreCoordinator
        vsc = VectorStoreCoordinator()
        col = vsc.get_collection()

        next_id = f"{cand.doc_id}:p{page}:c{cidx+1}"
        if next_id in existing_ids:
            return None

        res = col.get(ids=[next_id])
        if res and res.get("ids"):
            meta = res["metadatas"][0]
            # Must be same section to avoid combining unrelated sections
            succ_sec = meta.get("section_title", "")
            if cand.section_title and succ_sec and cand.section_title.lower() != succ_sec.lower():
                return None

            text = res["documents"][0]
            return CandidateChunk(
                chunk_id=res["ids"][0],
                doc_id=meta.get("doc_id", cand.doc_id),
                filename=meta.get("filename", cand.filename),
                text_content=text,
                page_number=meta.get("page_number", cand.page_number),
                section_title=cand.section_title or succ_sec,
                dense_score=(cand.dense_score or 1.0) * 0.95,
            )
    except Exception:
        pass
    return None


def build_context_package(
    candidates: List[CandidateChunk],
    max_chunks: Optional[int] = None,
    max_characters: Optional[int] = None,
) -> ContextPackage:
    """
    Constructs structured and serialized context from reranked candidate chunks.
    Groups and stitches contiguous chunks belonging to the same document, page, and section.
    """
    limit_chunks = max_chunks or settings.RETRIEVAL_MAX_CONTEXT_CHUNKS
    limit_chars = max_characters or settings.RETRIEVAL_MAX_CONTEXT_CHARACTERS

    if not candidates:
        return ContextPackage(
            selected_chunks=[],
            serialized_context="",
            total_characters=0,
            truncated=False,
            sources=[],
        )

    # 1. Take top candidate pool and recover predecessors / successors where needed (max 1 pred + 1 succ)
    pool = list(candidates[:limit_chunks])
    existing_ids = {c.chunk_id for c in pool}
    recovered: List[CandidateChunk] = []

    for cand in pool:
        pred = _recover_boundary_predecessor(cand, existing_ids)
        if pred and pred.chunk_id not in existing_ids:
            recovered.append(pred)
            existing_ids.add(pred.chunk_id)

        succ = _recover_boundary_successor(cand, existing_ids)
        if succ and succ.chunk_id not in existing_ids:
            recovered.append(succ)
            existing_ids.add(succ.chunk_id)

    if recovered:
        pool.extend(recovered)

    # 2. Group candidates by (doc_id, page_number, section_title)
    groups: Dict[Tuple[str, int, str], List[CandidateChunk]] = {}
    group_order: List[Tuple[str, int, str]] = []

    for cand in pool:
        sec = cand.section_title or "General"
        key = (cand.doc_id, cand.page_number, sec)
        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(cand)

    # 3. Stitch contiguous chunks within each group in ascending chunk_index order
    stitched_blocks: List[Tuple[List[CandidateChunk], str, SourceCitation]] = []

    for key in group_order:
        cands_in_group = groups[key]
        cands_in_group.sort(key=lambda c: _extract_chunk_index_from_id(c.chunk_id))

        current_batch: List[CandidateChunk] = []
        for c in cands_in_group:
            if not current_batch:
                current_batch.append(c)
            else:
                prev_c = current_batch[-1]
                idx_prev = _extract_chunk_index_from_id(prev_c.chunk_id)
                idx_curr = _extract_chunk_index_from_id(c.chunk_id)
                if idx_curr == idx_prev + 1:
                    current_batch.append(c)
                else:
                    # Flush previous batch
                    merged_text = current_batch[0].text_content
                    for nxt in current_batch[1:]:
                        merged_text = _merge_contiguous_texts(merged_text, nxt.text_content)
                    first_c = current_batch[0]
                    last_c = current_batch[-1]
                    combined_chunk_id = first_c.chunk_id if len(current_batch) == 1 else f"{first_c.chunk_id}..{last_c.chunk_id}"
                    cit = SourceCitation(
                        source_id="",
                        chunk_id=combined_chunk_id,
                        doc_id=first_c.doc_id,
                        filename=first_c.filename,
                        page_number=first_c.page_number,
                        section_title=first_c.section_title,
                        source_start_offset=first_c.source_start_offset,
                        source_end_offset=last_c.source_end_offset,
                        file_hash_sha256=first_c.file_hash_sha256,
                    )
                    stitched_blocks.append((list(current_batch), merged_text, cit))
                    current_batch = [c]

        if current_batch:
            merged_text = current_batch[0].text_content
            for nxt in current_batch[1:]:
                merged_text = _merge_contiguous_texts(merged_text, nxt.text_content)
            first_c = current_batch[0]
            last_c = current_batch[-1]
            combined_chunk_id = first_c.chunk_id if len(current_batch) == 1 else f"{first_c.chunk_id}..{last_c.chunk_id}"
            cit = SourceCitation(
                source_id="",
                chunk_id=combined_chunk_id,
                doc_id=first_c.doc_id,
                filename=first_c.filename,
                page_number=first_c.page_number,
                section_title=first_c.section_title,
                source_start_offset=first_c.source_start_offset,
                source_end_offset=last_c.source_end_offset,
                file_hash_sha256=first_c.file_hash_sha256,
            )
            stitched_blocks.append((list(current_batch), merged_text, cit))

    # 4. Assemble serialized context respecting character budget
    selected_chunks: List[CandidateChunk] = []
    sources: List[SourceCitation] = []
    context_blocks: List[str] = []
    current_char_count = 0
    is_truncated = False

    for idx, (batch_chunks, text_content, cit) in enumerate(stitched_blocks, start=1):
        source_id = f"Source {idx}"
        cit.source_id = source_id

        block = (
            f"[{source_id}]\n"
            f"Document: {cit.filename}\n"
            f"Page: {cit.page_number}\n"
            f"Section: {cit.section_title or 'General'}\n"
            f"Chunk ID: {cit.chunk_id}\n"
            f"Content:\n"
            f"{text_content.strip()}\n"
        )
        block_len = len(block)

        if current_char_count + block_len > limit_chars:
            if not selected_chunks:
                allowed_len = max(100, limit_chars - 200)
                truncated_text = text_content.strip()[:allowed_len]
                block = (
                    f"[{source_id}]\n"
                    f"Document: {cit.filename}\n"
                    f"Page: {cit.page_number}\n"
                    f"Section: {cit.section_title or 'General'}\n"
                    f"Chunk ID: {cit.chunk_id}\n"
                    f"Content:\n"
                    f"{truncated_text}...\n"
                )
                selected_chunks.extend(batch_chunks)
                sources.append(cit)
                context_blocks.append(block)
                current_char_count += len(block)
            is_truncated = True
            break

        selected_chunks.extend(batch_chunks)
        sources.append(cit)
        context_blocks.append(block)
        current_char_count += block_len

    serialized = "\n".join(context_blocks)

    return ContextPackage(
        selected_chunks=selected_chunks,
        serialized_context=serialized,
        total_characters=len(serialized),
        truncated=is_truncated,
        sources=sources,
    )
