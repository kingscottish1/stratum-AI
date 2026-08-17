"""
PDF text extraction (pypdf). Supports multi-page documents and basic layout.
"""
from pathlib import Path
from typing import Union

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


class PDFParser:
    def __init__(self):
        if PdfReader is None:
            raise RuntimeError("pypdf not installed")

    def extract_text(self, source: Union[str, Path, bytes]) -> str:
        """Extract all text from a PDF file path or raw bytes."""
        if isinstance(source, (str, Path)):
            reader = PdfReader(str(source))
        else:
            reader = PdfReader(__import__("io").BytesIO(source))

        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001 - keep going on bad pages
                pages.append("")
        return "\n\n".join(p for p in pages if p.strip())

    def page_count(self, source: Union[str, Path, bytes]) -> int:
        if isinstance(source, (str, Path)):
            return len(PdfReader(str(source)).pages)
        return len(PdfReader(__import__("io").BytesIO(source)).pages)
