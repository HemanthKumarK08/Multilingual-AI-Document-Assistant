"""
Document Parsers Package
"""

from app.services.ingestion.parsers.base import BaseParser
from app.services.ingestion.parsers.pdf import PyMuPDFParser
from app.services.ingestion.parsers.docx import DocxParser
from app.services.ingestion.parsers.txt import TxtParser
from app.services.ingestion.parsers.registry import ParserRegistry, default_parser_registry

__all__ = [
    "BaseParser",
    "PyMuPDFParser",
    "DocxParser",
    "TxtParser",
    "ParserRegistry",
    "default_parser_registry",
]
