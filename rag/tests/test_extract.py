# rag/tests/test_extract.py
from pathlib import Path
import pytest
from bios667_rag.extract import extract_pdf_text, detect_structure

BOOK_DIR = Path("/home/naimrashid/Dropbox/UNC_bios_line/BIOS667/new/book")

@pytest.mark.skipif(not BOOK_DIR.exists(), reason="Book directory not found")
def test_extract_pdf_text():
    pdf_path = BOOK_DIR / "Applied Longitudinal Analysis - 2011 - Fitzmaurice - Front Matter.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF not found")

    pages = extract_pdf_text(pdf_path)

    assert len(pages) > 0
    assert all("text" in page for page in pages)
    assert all("page_num" in page for page in pages)
