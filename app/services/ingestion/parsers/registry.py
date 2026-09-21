"""
Parser Registry for Resolving File Handlers by Extension and MIME Type
"""

import pathlib
from typing import Dict, Type
from app.services.ingestion.parsers.base import BaseParser
from app.services.ingestion.parsers.pdf import PyMuPDFParser
from app.services.ingestion.parsers.docx import DocxParser
from app.services.ingestion.parsers.txt import TxtParser
from app.services.ingestion.exceptions import UnsupportedFileTypeError

class ParserRegistry:
    """Central registry mapping file extensions to parser instances."""

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        # Register default parsers
        self.register_parser(PyMuPDFParser())
        self.register_parser(DocxParser())
        self.register_parser(TxtParser())

    def register_parser(self, parser: BaseParser) -> None:
        """Registers a parser instance for all its supported extensions."""
        for ext in parser.supported_extensions:
            self._parsers[ext.lower()] = parser

    def get_parser_for_file(self, file_path: str | pathlib.Path) -> BaseParser:
        """
        Retrieves the appropriate parser for a given file path based on its extension.
        
        Raises:
            UnsupportedFileTypeError if no parser is registered for the extension.
        """
        path = pathlib.Path(file_path)
        ext = path.suffix.lower()
        if not ext:
            raise UnsupportedFileTypeError(f"File {path.name} has no file extension.")

        parser = self._parsers.get(ext)
        if not parser:
            supported = ", ".join(sorted(self._parsers.keys()))
            raise UnsupportedFileTypeError(
                f"No parser available for extension '{ext}'. Supported extensions: {supported}"
            )
        return parser

# Global default registry instance
default_parser_registry = ParserRegistry()
