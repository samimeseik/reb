"""Text, Markdown, PDF (optional `pypdf`), DOCX (stdlib zip) and image OCR
(optional `pytesseract`, languages ara+tur+eng)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from . import Extraction, FactDraft


def extract(path: Path) -> Extraction:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix == ".docx":
        return _docx(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.count("\n") + 1
    return Extraction(
        provider="documents",
        text=text,
        facts=[
            FactDraft(
                fact=f"Text document with {lines} lines and {len(text)} characters.",
                operation="inventory_document",
                normalized={"lines": lines, "characters": len(text)},
            )
        ],
    )


def _pdf(path: Path) -> Extraction:
    try:
        from pypdf import PdfReader
    except ImportError:
        return Extraction(
            provider="documents",
            limitations=["PDF text not extracted: install the 'pdf' extra (pip install reb-agents[pdf])."],
            facts=[FactDraft(fact="PDF document (text not extracted).", operation="inventory_document")],
        )
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        pages.append(f"[page {i}]\n{page.extract_text() or ''}")
    text = "\n\n".join(pages)
    limitations = []
    if len(re.sub(r"\[page \d+\]|\s", "", text)) < 20:
        limitations.append("PDF has little or no text layer; it may be a scan — OCR the page images.")
    return Extraction(
        provider="documents",
        text=text,
        limitations=limitations,
        facts=[
            FactDraft(
                fact=f"PDF document with {len(reader.pages)} pages.",
                operation="inventory_document",
                normalized={"pages": len(reader.pages)},
                limitations=limitations,
            )
        ],
    )


def _docx(path: Path) -> Extraction:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    paragraphs = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    lines = ["".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S)) for p in paragraphs]
    text = "\n".join(line for line in lines if line.strip())
    return Extraction(
        provider="documents",
        text=text,
        facts=[
            FactDraft(
                fact=f"Word document with {len(lines)} paragraphs.",
                operation="inventory_document",
                normalized={"paragraphs": len(lines)},
            )
        ],
    )


def extract_image(path: Path, language: str | None = None) -> Extraction:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return Extraction(
            provider="ocr",
            limitations=["Image not OCR'd: install the 'ocr' extra and Tesseract with ara/tur data."],
            facts=[FactDraft(fact="Image (no OCR performed).", operation="inventory_image")],
        )
    lang = language or "ara+tur+eng"
    text = pytesseract.image_to_string(Image.open(path), lang=lang)
    return Extraction(
        provider="ocr",
        text=text,
        limitations=["OCR text may contain recognition errors; check numbers against the image."],
        facts=[
            FactDraft(
                fact=f"Image OCR'd with Tesseract ({lang}): {len(text)} characters recognized.",
                operation="ocr_image",
                normalized={"characters": len(text), "ocr_languages": lang},
                limitations=["OCR text may contain recognition errors."],
            )
        ],
    )
