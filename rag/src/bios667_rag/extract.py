"""PDF text extraction and structure detection."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclass
class TextBlock:
    """A block of text with metadata."""
    text: str
    page_num: int
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool = False


def extract_pdf_text(pdf_path: Path) -> list[dict]:
    """Extract text from PDF with page numbers."""
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({"text": text, "page_num": page_num})

    doc.close()
    return pages


def extract_pdf_blocks(pdf_path: Path) -> list[TextBlock]:
    """Extract text blocks with font metadata for structure detection."""
    doc = fitz.open(pdf_path)
    blocks = []

    for page_num, page in enumerate(doc, start=1):
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            block_text = []
            max_font_size = 0
            is_bold = False

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text.append(span.get("text", ""))
                    font_size = span.get("size", 0)
                    if font_size > max_font_size:
                        max_font_size = font_size
                    if "bold" in span.get("font", "").lower():
                        is_bold = True

            text = " ".join(block_text).strip()
            if text:
                blocks.append(TextBlock(
                    text=text, page_num=page_num,
                    bbox=tuple(block["bbox"]),
                    font_size=max_font_size, is_bold=is_bold,
                ))

    doc.close()
    return blocks


def detect_structure(blocks: list[TextBlock]) -> list[dict]:
    """Detect chapter/section structure from text blocks."""
    font_sizes = [b.font_size for b in blocks if b.font_size > 0]
    if not font_sizes:
        return []

    avg_font_size = sum(font_sizes) / len(font_sizes)
    structure = []

    for block in blocks:
        is_heading = block.font_size > avg_font_size * 1.2 or (
            block.is_bold and block.font_size >= avg_font_size
        )

        chapter_match = re.match(r"^Chapter\s+(\d+)", block.text, re.IGNORECASE)
        section_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s+(.+)", block.text)

        if chapter_match:
            structure.append({
                "type": "chapter", "number": int(chapter_match.group(1)),
                "title": block.text, "page": block.page_num,
            })
        elif section_match and is_heading:
            structure.append({
                "type": "section", "number": section_match.group(1),
                "title": section_match.group(2).strip(), "page": block.page_num,
            })

    return structure
