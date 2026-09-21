"""
Context Construction and Budgeting Module
"""

from typing import List, Optional
from app.core.config import settings
from app.services.rag.models import ContextPackage, SourceCitation
from app.services.retrieval.models import CandidateChunk

def build_context_package(
    candidates: List[CandidateChunk],
    max_chunks: Optional[int] = None,
    max_characters: Optional[int] = None,
) -> ContextPackage:
    """
    Constructs structured and serialized context from reranked candidate chunks,
    respecting strict chunk count and character budget constraints.
    """
    limit_chunks = max_chunks or settings.RETRIEVAL_MAX_CONTEXT_CHUNKS
    limit_chars = max_characters or settings.RETRIEVAL_MAX_CONTEXT_CHARACTERS

    selected_chunks: List[CandidateChunk] = []
    sources: List[SourceCitation] = []
    context_blocks: List[str] = []
    current_char_count = 0
    is_truncated = False

    for idx, cand in enumerate(candidates[:limit_chunks], start=1):
        source_id = f"Source {idx}"
        
        # Build block
        block = (
            f"[{source_id}]\n"
            f"Document: {cand.filename}\n"
            f"Page: {cand.page_number}\n"
            f"Section: {cand.section_title or 'General'}\n"
            f"Chunk ID: {cand.chunk_id}\n"
            f"Content:\n"
            f"{cand.text_content.strip()}\n"
        )
        
        block_len = len(block)
        if current_char_count + block_len > limit_chars:
            if not selected_chunks:
                # If even first chunk exceeds, take portion of it safely
                allowed_len = max(100, limit_chars - 200)
                truncated_text = cand.text_content.strip()[:allowed_len]
                block = (
                    f"[{source_id}]\n"
                    f"Document: {cand.filename}\n"
                    f"Page: {cand.page_number}\n"
                    f"Section: {cand.section_title or 'General'}\n"
                    f"Chunk ID: {cand.chunk_id}\n"
                    f"Content:\n"
                    f"{truncated_text}...\n"
                )
                selected_chunks.append(cand)
                sources.append(
                    SourceCitation(
                        source_id=source_id,
                        chunk_id=cand.chunk_id,
                        doc_id=cand.doc_id,
                        filename=cand.filename,
                        page_number=cand.page_number,
                        section_title=cand.section_title,
                        source_start_offset=cand.source_start_offset,
                        source_end_offset=cand.source_end_offset,
                        file_hash_sha256=cand.file_hash_sha256,
                    )
                )
                context_blocks.append(block)
                current_char_count += len(block)
            is_truncated = True
            break

        selected_chunks.append(cand)
        sources.append(
            SourceCitation(
                source_id=source_id,
                chunk_id=cand.chunk_id,
                doc_id=cand.doc_id,
                filename=cand.filename,
                page_number=cand.page_number,
                section_title=cand.section_title,
                source_start_offset=cand.source_start_offset,
                source_end_offset=cand.source_end_offset,
                file_hash_sha256=cand.file_hash_sha256,
            )
        )
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
