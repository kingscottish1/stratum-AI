"""
OCR for scanned documents (Tesseract via pytesseract).

Requires system tesseract binary:
  apt-get install -y tesseract-ocr
"""
import os
import tempfile
from pathlib import Path
from typing import Union

try:
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover
    pytesseract = Image = None


class OCRHandler:
    def __init__(self, tesseract_cmd: str = "tesseract", lang: str = "eng"):
        if pytesseract is None:
            raise RuntimeError("pytesseract/Pillow not installed")
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.lang = lang

    def ocr_image(self, image_path: Union[str, Path]) -> str:
        with Image.open(str(image_path)) as img:
            return pytesseract.image_to_string(img, lang=self.lang)

    def ocr_pdf(self, pdf_path: Union[str, Path], dpi: int = 300) -> str:
        """Render PDF pages to images (requires pdf2image+poppler) then OCR."""
        try:
            from pdf2image import convert_from_path
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pdf2image not installed") from exc

        texts = []
        with tempfile.TemporaryDirectory() as tmp:
            images = convert_from_path(str(pdf_path), dpi=dpi, output_folder=tmp)
            for page in images:
                texts.append(pytesseract.image_to_string(page, lang=self.lang))
        return "\n\n".join(texts)
