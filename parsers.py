import os
from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Abstract Base Class defining the interface for document parsers."""
    
    @abstractmethod
    def extract_text(self, source: str) -> str:
        """
        Extract plain text from the source.
        For text parsers, source is the raw message string.
        For file parsers, source is the local path to the downloaded file.
        """
        pass


class TextParser(BaseParser):
    """Parser for raw text messages."""
    
    def extract_text(self, source: str) -> str:
        return source


class PDFParser(BaseParser):
    """Parser for extracting text from PDF files using pypdf."""
    
    def extract_text(self, source: str) -> str:
        if not os.path.exists(source):
            raise FileNotFoundError(f"PDF file not found at: {source}")
            
        from pypdf import PdfReader
        
        reader = PdfReader(source)
        text_content = []
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
                
        return "\n".join(text_content).strip()


class ParserFactory:
    """Factory to register and resolve document parsers, following Open-Closed Principle."""
    
    _parsers = {}
    
    @classmethod
    def register_parser(cls, file_type: str, parser_class):
        """Register a new parser for a file type without changing the factory logic."""
        cls._parsers[file_type.lower()] = parser_class
        
    @classmethod
    def get_parser(cls, source_type: str) -> BaseParser:
        """Resolve and return the correct parser instance."""
        source_type = source_type.lower().strip()
        parser_class = cls._parsers.get(source_type)
        if not parser_class:
            raise ValueError(f"No parser registered for source type: '{source_type}'")
        return parser_class()

# Register default parsers
ParserFactory.register_parser("text", TextParser)
ParserFactory.register_parser("pdf", PDFParser)
