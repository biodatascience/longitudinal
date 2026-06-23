"""Tests for the PDF loader (Task 2.5).

``pdf_loader`` extracts text via PyMuPDF (reusing :mod:`bios667_rag.extract`),
concatenates pages into ``text``, records ``n_pages``, and flags sparse/empty
PDFs as ``scanned``. OCR is genuinely optional: if ``pytesseract`` cannot be
imported OR the ``tesseract`` binary is missing, the loader must NOT crash --
it returns the (possibly empty) RawDoc with ``ocr_attempted=False``.

Fixtures are built on the fly with PyMuPDF (``fitz``) so the tests carry no
binary blobs and run anywhere ``fitz`` is installed.
"""

import fitz
import pytest

from bios667_rag.loaders import load
from bios667_rag.loaders.pdf import pdf_loader
from bios667_rag.metadata import SOURCE_TYPES


def _make_text_pdf(path, sentence):
    """Create a single-page PDF containing ``sentence`` as real text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), sentence)
    doc.save(str(path))
    doc.close()


def _make_blank_pdf(path):
    """Create a single-page PDF with NO extractable text (just a drawn rect)."""
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(100, 100, 200, 200))
    doc.save(str(path))
    doc.close()


def test_text_pdf_extracts_sentence(tmp_path):
    sentence = "Random intercept model for six cities"
    f = tmp_path / "notes.pdf"
    _make_text_pdf(f, sentence)

    rd = pdf_loader(str(f))

    assert rd is not None
    assert sentence in rd.text
    assert rd.native_metadata["scanned"] is False
    assert rd.native_metadata["n_pages"] == 1
    assert rd.source_type in SOURCE_TYPES


def test_text_pdf_does_not_attempt_ocr(tmp_path):
    f = tmp_path / "notes.pdf"
    _make_text_pdf(f, "Linear mixed effects estimation")

    rd = pdf_loader(str(f))

    # A normal text PDF is never scanned and never triggers OCR.
    assert rd.native_metadata["scanned"] is False
    assert rd.native_metadata.get("ocr_attempted", False) is False


def test_scanned_pdf_flagged_and_does_not_crash(tmp_path):
    """An empty/text-free PDF is flagged ``scanned`` regardless of OCR availability."""
    f = tmp_path / "scan.pdf"
    _make_blank_pdf(f)

    rd = pdf_loader(str(f))

    assert rd is not None
    assert rd.native_metadata["scanned"] is True
    assert rd.native_metadata["n_pages"] == 1
    # ocr_attempted must be present and boolean whatever the environment did.
    assert isinstance(rd.native_metadata["ocr_attempted"], bool)


def test_scanned_pdf_graceful_when_pytesseract_unavailable(tmp_path, monkeypatch):
    """Simulate ``import pytesseract`` failing: loader returns, ocr_attempted False."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("simulated: pytesseract not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    f = tmp_path / "scan.pdf"
    _make_blank_pdf(f)

    rd = pdf_loader(str(f))

    assert rd is not None
    assert rd.native_metadata["scanned"] is True
    assert rd.native_metadata["ocr_attempted"] is False
    # Sparse text is kept as-is (a string, possibly empty) -- never crash.
    assert isinstance(rd.text, str)


def test_dispatch_load_returns_rawdoc_for_text_pdf(tmp_path):
    """Dispatch integration: binary PDF routes through ``load`` to ``pdf_loader``."""
    sentence = "Generalized estimating equations working correlation"
    f = tmp_path / "deck.pdf"
    _make_text_pdf(f, sentence)

    rd = load(str(f))

    assert rd is not None
    assert sentence in rd.text
    assert rd.native_metadata["n_pages"] == 1
