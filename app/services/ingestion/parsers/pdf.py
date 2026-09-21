"""
PyMuPDF (fitz) PDF Document Parser
Extracts text page-by-page preserving 1-indexed page numbers, structural headings, and tables.
"""

import fitz  # PyMuPDF
import pathlib
import re
from typing import Dict, Any, Optional, List
from app.services.ingestion.parsers.base import BaseParser
from app.services.ingestion.models import (
    ParsedDocument,
    ExtractedPage,
    ExtractedBlock,
    ExtractedTable,
    ExtractionWarning,
)
from app.services.ingestion.exceptions import (
    FileNotFoundIngestionError,
    CorruptedFileError,
    ParserExecutionError,
)
from app.services.ingestion.normalization import normalize_text, clean_heading_text
from app.services.ingestion.language import detect_script_and_language

_HEADING_REGEX = re.compile(
    r"^(?:(?:Section|Chapter|Article|Clause|Part)\s+\d+|(?:\d+\.)+\d*|[A-Z][A-Z\s\-_:]{3,60}$)",
    re.IGNORECASE,
)

class PyMuPDFParser(BaseParser):
    """PDF parser implementation using PyMuPDF (fitz)."""

    @property
    def parser_name(self) -> str:
        return "PyMuPDFParser"

    @property
    def parser_version(self) -> str:
        return f"1.0.0 (fitz-{fitz.__version__})"

    @property
    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    def parse(
        self,
        file_path: str | pathlib.Path,
        doc_id: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ParsedDocument:
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundIngestionError(f"PDF file not found: {path}")

        try:
            doc = fitz.open(path)
        except Exception as e:
            raise CorruptedFileError(f"Failed to open PDF file {path}: {str(e)}")

        pages: List[ExtractedPage] = []
        warnings: List[ExtractionWarning] = []
        raw_text_parts: List[str] = []
        sections: List[Dict[str, Any]] = []

        current_heading = "Introduction / Overview"
        current_heading_level = 1

        try:
            page_count = len(doc)
            if page_count == 0:
                warnings.append(
                    ExtractionWarning(
                        warning_code="EMPTY_DOCUMENT",
                        message="PDF document contains 0 pages.",
                        severity="warning",
                    )
                )

            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1  # 1-indexed
                page_blocks: List[ExtractedBlock] = []
                page_warnings: List[str] = []

                # 1. Extract tables if table finder is supported
                tables_on_page: List[ExtractedTable] = []
                try:
                    tabs = page.find_tables()
                    if tabs and tabs.tables:
                        for tab in tabs.tables:
                            extracted_df = tab.extract()
                            if extracted_df and len(extracted_df) > 0:
                                headers = [str(c or "") for c in extracted_df[0]]
                                rows = [[str(c or "") for c in r] for r in extracted_df[1:]]
                                t_model = ExtractedTable(headers=headers, rows=rows)
                                tables_on_page.append(t_model)
                                page_blocks.append(
                                    ExtractedBlock(
                                        block_type="table",
                                        text=t_model.to_formatted_text(),
                                        section_title=current_heading,
                                        heading_level=current_heading_level,
                                        table_data=t_model,
                                    )
                                )
                except Exception:
                    # Non-fatal if table discovery is not applicable
                    pass

                # 2. Extract text blocks
                # get_text("blocks") returns (x0, y0, x1, y1, text, block_no, block_type)
                try:
                    raw_blocks = page.get_text("blocks")
                except Exception as e:
                    page_warnings.append(f"Block extraction failed: {str(e)}")
                    raw_blocks = []

                page_text_accum = []
                for blk in raw_blocks:
                    if len(blk) >= 5 and isinstance(blk[4], str):
                        blk_text = blk[4].strip()
                        if not blk_text:
                            continue

                        # Check if block looks like a heading
                        is_heading = False
                        lines = [l.strip() for l in blk_text.split("\n") if l.strip()]
                        if len(lines) == 1 and len(lines[0]) < 80:
                            line = lines[0]
                            if _HEADING_REGEX.match(line) or (line.isupper() and len(line) > 4):
                                is_heading = True
                                current_heading = clean_heading_text(line)
                                current_heading_level = 2 if re.match(r"^\d+\.\d+", line) else 1
                                sections.append({
                                    "title": current_heading,
                                    "level": current_heading_level,
                                    "page": page_num
                                })

                        block_obj = ExtractedBlock(
                            block_type="heading" if is_heading else "paragraph",
                            text=blk_text,
                            heading_level=current_heading_level if is_heading else None,
                            section_title=current_heading,
                        )
                        page_blocks.append(block_obj)
                        page_text_accum.append(blk_text)

                page_raw_text = "\n\n".join(page_text_accum)
                
                # Check for empty / scanned image page
                if len(page_raw_text.strip()) < 15 and not tables_on_page:
                    warn_msg = f"Page {page_num} has no extractable text (OCR may be required)."
                    page_warnings.append(warn_msg)
                    warnings.append(
                        ExtractionWarning(
                            warning_code="OCR_REQUIRED_OR_TEXT_NOT_EXTRACTABLE",
                            message=warn_msg,
                            page_number=page_num,
                        )
                    )

                pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=page_raw_text,
                        blocks=page_blocks,
                        warnings=page_warnings,
                    )
                )
                raw_text_parts.append(page_raw_text)

        except Exception as e:
            raise ParserExecutionError(f"Error during PDF parsing of {path}: {str(e)}")
        finally:
            doc.close()

        full_raw_text = "\n\n".join(raw_text_parts)
        full_normalized_text = normalize_text(full_raw_text)

        # Detect script and language
        lang_res = detect_script_and_language(full_normalized_text)

        return ParsedDocument(
            doc_id=doc_id,
            filename=path.name,
            file_type="pdf",
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            page_count=len(pages),
            raw_text=full_raw_text,
            normalized_text=full_normalized_text,
            pages=pages,
            sections=sections,
            detected_language=lang_res.language,
            detected_script=lang_res.script,
            language_confidence=lang_res.confidence,
            warnings=warnings,
            metadata=metadata or {},
        )
