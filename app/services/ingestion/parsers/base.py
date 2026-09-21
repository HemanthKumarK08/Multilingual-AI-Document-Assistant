"""
Base Document Parser Abstract Interface
"""

import abc
import pathlib
from typing import Dict, Any, Optional
from app.services.ingestion.models import ParsedDocument

class BaseParser(abc.ABC):
    """
    Abstract base class for all file parsers.
    Stateless and independent of database or HTTP layers.
    """
    
    @property
    @abc.abstractmethod
    def parser_name(self) -> str:
        """Name of the parser implementation."""
        pass

    @property
    @abc.abstractmethod
    def parser_version(self) -> str:
        """Semantic version of the parser."""
        pass

    @property
    @abc.abstractmethod
    def supported_extensions(self) -> set[str]:
        """Set of file extensions handled by this parser (lowercase, e.g. {'.pdf'})."""
        pass

    @abc.abstractmethod
    def parse(
        self,
        file_path: str | pathlib.Path,
        doc_id: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ParsedDocument:
        """
        Parses a file from disk and returns a structured ParsedDocument representation.
        
        Args:
            file_path: Target path to file.
            doc_id: Stable identifier for the document.
            category: Institutional category.
            metadata: Optional additional metadata dictionary.
            
        Returns:
            ParsedDocument with extracted pages, sections, normalized text, and warnings.
        """
        pass
