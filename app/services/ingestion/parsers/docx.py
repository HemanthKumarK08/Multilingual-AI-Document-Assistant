"""
python-docx Document Parser
Extracts paragraphs in order, preserving Heading 1/2/3 styles, hierarchy, and tables.
"""

import docx
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

class DocxParser(BaseParser):
    """DOCX parser implementation using python-docx."""

    @property
    def parser_name(self) -> str:
        return "DocxParser"

    @property
    def parser_version(self) -> str:
        return f"1.0.0 (python-docx-{docx.__version__})"

    @property
    def supported_extensions(self) -> set[str]:
        return {".docx", ".doc"}

    def parse(
        self,
        file_path: str | pathlib.Path,
        doc_id: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ParsedDocument:
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundIngestionError(f"DOCX file not found: {path}")

        try:
            doc = docx.Document(path)
        except Exception as e:
            raise CorruptedFileError(f"Failed to open DOCX file {path}: {str(e)}")

        blocks: List[ExtractedBlock] = []
        warnings: List[ExtractionWarning] = []
        raw_text_parts: List[str] = []
        sections: List[Dict[str, Any]] = []

        current_heading = "Introduction / Overview"
        current_heading_level = 1

        try:
            # 1. Process paragraphs
            for para in doc.paragraphs:
                p_text = para.text.strip()
                if not p_text:
                    continue

                style_name = para.style.name.lower() if para.style else ""
                is_heading = False
                heading_level = None

                if "heading 1" in style_name or style_name == "title":
                    is_heading = True
                    heading_level = 1
                elif "heading 2" in style_name:
                    is_heading = True
                    heading_level = 2
                elif "heading 3" in style_name or "heading 4" in style_name:
                    is_heading = True
                    heading_level = 3
                elif re.match(r"^(?:Section|Chapter|\d+\.)", p_text, re.IGNORECASE) and len(p_text) < 80:
                    is_heading = True
                    heading_level = 2 if re.match(r"^\d+\.\d+", p_text) else 1

                if is_heading:
                    current_heading = clean_heading_text(p_text)
                    current_heading_level = heading_level or 1
                    sections.append({
                        "title": current_heading,
                        "level": current_heading_level,
                        "page": 1
                    })

                blocks.append(
                    ExtractedBlock(
                        block_type="heading" if is_heading else "paragraph",
                        text=p_text,
                        heading_level=heading_level if is_heading else None,
                        section_title=current_heading,
                    )
                )
                raw_text_parts.append(p_text)

            # 2. Process tables
            for table in doc.tables:
                table_rows: List[List[str]] = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_rows.append(row_cells)

                if table_rows:
                    headers = table_rows[0]
                    data_rows = table_rows[1:] if len(table_rows) > 1 else []
                    t_model = ExtractedTable(headers=headers, rows=data_rows)
                    t_formatted = t_model.to_formatted_text()
                    blocks.append(
                        ExtractedBlock(
                            block_type="table",
                            text=t_formatted,
                            section_title=current_heading,
                            heading_level=current_heading_level,
                            table_data=t_model,
                        )
                    )
                    raw_text_parts.append(t_formatted)

            if not blocks:
                warnings.append(
                    ExtractionWarning(
                        warning_code="EMPTY_DOCUMENT",
                        message="DOCX document contains no readable text or tables.",
                        severity="warning",
                    )
                )

        except Exception as e:
            raise ParserExecutionError(f"Error during DOCX parsing of {path}: {str(e)}")

        full_raw_text = "\n\n".join(raw_text_parts)
        full_normalized_text = normalize_text(full_raw_text)

        # Non-paginated format: wrap as 1 logical page
        page_1 = ExtractedPage(
            page_number=1,
            text=full_raw_text,
            blocks=blocks,
            warnings=[w.message for w in warnings],
        )

        lang_res = detect_script_and_language(full_normalized_text)

        return ParsedDocument(
            doc_id=doc_id,
            filename=path.name,
            file_type="docx",
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            page_count=1,
            raw_text=full_raw_text,
            normalized_text=full_normalized_text,
            pages=[page_1],
            sections=sections,
            detected_language=lang_res.language,
            detected_script=lang_res.script,
            language_confidence=lang_res.confidence,
            warnings=warnings,
            metadata=metadata or {},
        )
