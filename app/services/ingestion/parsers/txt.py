"""
Plain Text and Markdown Document Parser
Handles UTF-8, UTF-8 BOM, Markdown headings, and logical paragraph blocks.
"""

import pathlib
import re
from typing import Dict, Any, Optional, List
from app.services.ingestion.parsers.base import BaseParser
from app.services.ingestion.models import (
    ParsedDocument,
    ExtractedPage,
    ExtractedBlock,
    ExtractionWarning,
)
from app.services.ingestion.exceptions import (
    FileNotFoundIngestionError,
    CorruptedFileError,
    ParserExecutionError,
)
from app.services.ingestion.normalization import normalize_text, clean_heading_text
from app.services.ingestion.language import detect_script_and_language

_MARKDOWN_HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.+)$")
_NUMBERED_HEADING_REGEX = re.compile(r"^(?:(?:Section|Chapter|Article|Clause)\s+\d+|(?:\d+\.)+\d*)\s+(.+)$", re.IGNORECASE)

class TxtParser(BaseParser):
    """Plain text and Markdown document parser."""

    @property
    def parser_name(self) -> str:
        return "TxtParser"

    @property
    def parser_version(self) -> str:
        return "1.0.0 (utf8-stream)"

    @property
    def supported_extensions(self) -> set[str]:
        return {".txt", ".md"}

    def parse(
        self,
        file_path: str | pathlib.Path,
        doc_id: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ParsedDocument:
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundIngestionError(f"Text file not found: {path}")

        warnings: List[ExtractionWarning] = []

        try:
            raw_bytes = path.read_bytes()
        except Exception as e:
            raise CorruptedFileError(f"Failed to read file {path}: {str(e)}")

        if len(raw_bytes) == 0:
            warnings.append(
                ExtractionWarning(
                    warning_code="EMPTY_FILE",
                    message="File is empty (0 bytes).",
                    severity="warning",
                )
            )
            text = ""
        else:
            # Check and strip UTF-8 BOM if present
            if raw_bytes.startswith(b"\xef\xbb\xbf"):
                raw_bytes = raw_bytes[3:]
                warnings.append(
                    ExtractionWarning(
                        warning_code="BOM_STRIPPED",
                        message="UTF-8 Byte Order Mark (BOM) was detected and stripped.",
                        severity="info",
                    )
                )

            # Attempt UTF-8 decoding
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError as ude:
                warnings.append(
                    ExtractionWarning(
                        warning_code="UTF8_DECODE_FALLBACK",
                        message=f"UTF-8 decode failed ({str(ude)}); falling back to latin-1 encoding.",
                        severity="warning",
                    )
                )
                text = raw_bytes.decode("latin-1", errors="replace")

        # Parse structural blocks and headings
        blocks: List[ExtractedBlock] = []
        sections: List[Dict[str, Any]] = []
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_heading = "Introduction / Overview"
        current_heading_level = 1

        for para in raw_paragraphs:
            is_heading = False
            heading_level = None

            # 1. Check for Markdown # heading
            md_match = _MARKDOWN_HEADING_REGEX.match(para)
            if md_match:
                is_heading = True
                heading_level = len(md_match.group(1))
                current_heading = clean_heading_text(md_match.group(2))
                current_heading_level = heading_level
                sections.append({
                    "title": current_heading,
                    "level": current_heading_level,
                    "page": 1
                })
            else:
                # 2. Check for single line numbered heading
                lines = para.split("\n")
                if len(lines) == 1 and len(para) < 100:
                    num_match = _NUMBERED_HEADING_REGEX.match(para)
                    if num_match:
                        is_heading = True
                        current_heading = clean_heading_text(para)
                        current_heading_level = 2
                        sections.append({
                            "title": current_heading,
                            "level": current_heading_level,
                            "page": 1
                        })

            blocks.append(
                ExtractedBlock(
                    block_type="heading" if is_heading else "paragraph",
                    text=para,
                    heading_level=heading_level if is_heading else None,
                    section_title=current_heading,
                )
            )

        full_normalized_text = normalize_text(text)
        lang_res = detect_script_and_language(full_normalized_text)

        # Represent as 1 logical page
        page_1 = ExtractedPage(
            page_number=1,
            text=text,
            blocks=blocks,
            warnings=[w.message for w in warnings],
        )

        return ParsedDocument(
            doc_id=doc_id,
            filename=path.name,
            file_type=path.suffix.lstrip(".").lower() or "txt",
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            page_count=1,
            raw_text=text,
            normalized_text=full_normalized_text,
            pages=[page_1],
            sections=sections,
            detected_language=lang_res.language,
            detected_script=lang_res.script,
            language_confidence=lang_res.confidence,
            warnings=warnings,
            metadata=metadata or {},
        )
