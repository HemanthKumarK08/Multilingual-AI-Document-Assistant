"""
Page-Aware and Section-Aware Boundary Manager (Phase 3)
Coordinates boundary-respecting text chunking across document pages and structural sections.
"""

from typing import List, Dict, Any, Optional
from app.services.chunking.models import DocumentChunk, ChunkingConfig
from app.services.chunking.recursive import RecursiveCharacterChunker
from app.services.ingestion.models import ParsedDocument


class PageAwareBoundaryManager:
    """
    Orchestrates page-level and section-level chunk boundaries.
    Guarantees that chunks never cross physical/logical page boundaries without attribution.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self.chunker = RecursiveCharacterChunker(self.config)

    def chunk_document(
        self,
        parsed_doc: ParsedDocument,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Extracts chunks from a ParsedDocument, strictly preserving page numbers and section context.
        
        Args:
            parsed_doc: The canonical ParsedDocument intermediate representation from Phase 2.
            doc_metadata: Optional dictionary with file_hash_sha256, category, version, etc.
            
        Returns:
            List of DocumentChunk instances in document-global sequential order.
        """
        metadata = doc_metadata or {}
        doc_id = parsed_doc.doc_id
        file_hash = (
            metadata.get("file_hash_sha256")
            or metadata.get("checksum_sha256")
            or parsed_doc.metadata.get("file_hash_sha256")
            or "unknown_hash"
        )
        category = metadata.get("category", parsed_doc.metadata.get("category", "general"))
        doc_version = metadata.get("version", parsed_doc.metadata.get("version", "1.0"))
        
        chunks: List[DocumentChunk] = []
        global_chunk_index = 0

        # If pages list is empty, fallback to normalized_text on page 1
        pages_to_process = parsed_doc.pages
        if not pages_to_process and parsed_doc.normalized_text:
            raw_chunks = self.chunker.split_text_with_offsets(parsed_doc.normalized_text)
            for chunk_text, start_off, end_off in raw_chunks:
                chunk_obj = DocumentChunk(
                    chunk_id=f"{doc_id}:p1:c{global_chunk_index}",
                    doc_id=doc_id,
                    file_hash_sha256=file_hash,
                    filename=parsed_doc.filename,
                    category=category,
                    language=parsed_doc.detected_language,
                    script=parsed_doc.detected_script,
                    page_number=1,
                    section_title="Introduction / Overview",
                    heading_level=1,
                    chunk_index=global_chunk_index,
                    text_content=chunk_text,
                    text_length=len(chunk_text),
                    source_start_offset=start_off,
                    source_end_offset=end_off,
                    source_unit_index=0,
                    parser_name=parsed_doc.parser_name,
                    parser_version=parsed_doc.parser_version,
                    version=doc_version,
                    extraction_notes=[w.message if hasattr(w, "message") else str(w) for w in parsed_doc.warnings]
                )
                chunks.append(chunk_obj)
                global_chunk_index += 1
            return chunks

        # Iterate page by page
        for page_idx, page in enumerate(pages_to_process):
            page_num = page.page_number
            page_warnings = [w.message if hasattr(w, "message") else str(w) for w in page.warnings]
            
            # If page has blocks, chunk section-by-section
            if page.blocks:
                # Group consecutive blocks sharing the same section title
                section_groups: List[Dict[str, Any]] = []
                current_group: Dict[str, Any] = {
                    "section_title": page.blocks[0].section_title or "Introduction / Overview",
                    "heading_level": page.blocks[0].heading_level or 1,
                    "texts": []
                }

                for block in page.blocks:
                    block_sec = block.section_title or current_group["section_title"]
                    block_lvl = block.heading_level or current_group["heading_level"]

                    if block_sec != current_group["section_title"] and current_group["texts"]:
                        section_groups.append(current_group)
                        current_group = {
                            "section_title": block_sec,
                            "heading_level": block_lvl,
                            "texts": []
                        }

                    if block.text and block.text.strip():
                        current_group["texts"].append(block.text)

                if current_group["texts"]:
                    section_groups.append(current_group)

                # Merge short / fragmentary section groups into neighboring content on the same page
                merged_groups: List[Dict[str, Any]] = []
                for grp in section_groups:
                    grp_text = "\n\n".join(grp["texts"]).strip()
                    if not grp_text:
                        continue
                    # If this group is very short (< 40 chars) and previous group exists on same page
                    if merged_groups and len(grp_text) < 40 and grp.get("heading_level", 2) > 1:
                        merged_groups[-1]["texts"].extend(grp["texts"])
                    else:
                        merged_groups.append(grp)

                # Secondary pass: if leading or trailing group on page is tiny (< 30 chars), merge with neighbor
                final_groups: List[Dict[str, Any]] = []
                for grp in merged_groups:
                    grp_text = "\n\n".join(grp["texts"]).strip()
                    if not grp_text:
                        continue
                    if len(grp_text) < 30 and final_groups:
                        final_groups[-1]["texts"].extend(grp["texts"])
                    else:
                        final_groups.append(grp)

                # Chunk each section group independently
                for grp in final_groups:
                    sec_text = "\n\n".join(grp["texts"]).strip()
                    if not sec_text:
                        continue

                    raw_chunks = self.chunker.split_text_with_offsets(sec_text)
                    # Merge any trailing micro-chunk (< 30 chars) into previous chunk if within budget
                    processed_chunks = []
                    for c_text, start_off, end_off in raw_chunks:
                        if processed_chunks and len(c_text) < 30 and (len(processed_chunks[-1][0]) + len(c_text) + 2 <= self.config.chunk_size):
                            prev_text, prev_start, _ = processed_chunks[-1]
                            processed_chunks[-1] = (f"{prev_text}\n\n{c_text}", prev_start, end_off)
                        else:
                            processed_chunks.append((c_text, start_off, end_off))

                    for chunk_text, start_off, end_off in processed_chunks:
                        chunk_obj = DocumentChunk(
                            chunk_id=f"{doc_id}:p{page_num}:c{global_chunk_index}",
                            doc_id=doc_id,
                            file_hash_sha256=file_hash,
                            filename=parsed_doc.filename,
                            category=category,
                            language=parsed_doc.detected_language,
                            script=parsed_doc.detected_script,
                            page_number=page_num,
                            section_title=grp["section_title"],
                            heading_level=grp["heading_level"],
                            chunk_index=global_chunk_index,
                            text_content=chunk_text,
                            text_length=len(chunk_text),
                            source_start_offset=start_off,
                            source_end_offset=end_off,
                            source_unit_index=page_idx,
                            parser_name=parsed_doc.parser_name,
                            parser_version=parsed_doc.parser_version,
                            version=doc_version,
                            extraction_notes=page_warnings
                        )
                        chunks.append(chunk_obj)
                        global_chunk_index += 1

            else:
                # Page has no blocks; chunk raw page text directly
                page_text = page.text.strip()
                if page_text:
                    raw_chunks = self.chunker.split_text_with_offsets(page_text)
                    for chunk_text, start_off, end_off in raw_chunks:
                        chunk_obj = DocumentChunk(
                            chunk_id=f"{doc_id}:p{page_num}:c{global_chunk_index}",
                            doc_id=doc_id,
                            file_hash_sha256=file_hash,
                            filename=parsed_doc.filename,
                            category=category,
                            language=parsed_doc.detected_language,
                            script=parsed_doc.detected_script,
                            page_number=page_num,
                            section_title="Introduction / Overview",
                            heading_level=1,
                            chunk_index=global_chunk_index,
                            text_content=chunk_text,
                            text_length=len(chunk_text),
                            source_start_offset=start_off,
                            source_end_offset=end_off,
                            source_unit_index=page_idx,
                            parser_name=parsed_doc.parser_name,
                            parser_version=parsed_doc.parser_version,
                            version=doc_version,
                            extraction_notes=page_warnings
                        )
                        chunks.append(chunk_obj)
                        global_chunk_index += 1

        return chunks
