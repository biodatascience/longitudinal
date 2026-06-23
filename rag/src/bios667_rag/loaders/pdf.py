"""Loader for ``.pdf`` files with scanned-PDF detection and optional OCR fallback.

Most course PDFs (lecture exports, handouts, the textbook scan) carry a real text
layer, so we extract it with PyMuPDF via :func:`bios667_rag.extract.extract_pdf_text`
(reused rather than reinvented) and concatenate the per-page text into ``text``.

Some PDFs are image-only scans with no text layer. We detect that heuristically: a
PDF whose extracted text averages fewer than :data:`_MIN_CHARS_PER_PAGE` characters
per page (or is essentially empty) is flagged ``native_metadata["scanned"] = True``.

OCR is GENUINELY OPTIONAL. We only attempt it for scanned PDFs, and only via a lazy
``import pytesseract`` guarded by try/except. If ``pytesseract`` is not importable OR
the underlying ``tesseract`` binary is missing (or OCR otherwise raises), we degrade
gracefully: keep whatever sparse text we extracted, set ``ocr_attempted = False``, and
STILL return the ``RawDoc`` (the orchestrator logs scanned/un-OCR'd files later). When
OCR succeeds it augments ``text`` and sets ``ocr_attempted = True``.

``native_metadata`` keys set by this loader:

* ``n_pages`` -- page count (int).
* ``scanned`` -- bool; True when the text layer is sparse/absent.
* ``ocr_attempted`` -- bool; only meaningful (and only present) for scanned PDFs.

``source_type`` is resolved by :func:`bios667_rag.metadata.classify_source_type`.
"""

from pathlib import Path

import fitz  # PyMuPDF

from ..extract import extract_pdf_text
from ..metadata import classify_source_type
from .base import RawDoc
from .dispatch import register

# Sparse-text heuristic: average chars/page below this flags the PDF as scanned.
# The operative signal is "near-zero": an image-only scan yields ~0 chars/page
# (PyMuPDF returns "" when there is no text layer), whereas ANY real text layer --
# even a one-line page -- yields tens of chars. A low floor (not a "full page worth"
# threshold like 100) avoids misclassifying genuinely-sparse-but-text PDFs (e.g. a
# title slide) as scanned while still catching text-free scans.
_MIN_CHARS_PER_PAGE = 10


def _ocr_pages(pdf_path: Path) -> str | None:
    """OCR every page of ``pdf_path`` and return the concatenated text.

    Returns ``None`` if OCR cannot run for ANY reason -- ``pytesseract`` not
    importable, the ``tesseract`` binary missing, or any rendering/OCR error. The
    caller treats ``None`` as "OCR not attempted/failed" and degrades gracefully.
    """
    try:
        import pytesseract  # lazy: optional dependency, may be absent
        from PIL import Image  # Pillow ships with pytesseract; guard regardless
    except ImportError:
        return None

    try:
        import io

        doc = fitz.open(pdf_path)
        try:
            chunks: list[str] = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                chunks.append(pytesseract.image_to_string(img))
        finally:
            doc.close()
        return "\n".join(chunks)
    except Exception:
        # TesseractNotFoundError (binary missing) and any render/OCR failure land
        # here. Never propagate: a scanned PDF we cannot OCR is still returned.
        return None


def pdf_loader(path: str) -> RawDoc | None:
    """Load a ``.pdf`` file into a :class:`RawDoc`, or ``None`` if unreadable.

    See the module docstring for the scanned-detection heuristic and the optional,
    crash-free OCR fallback contract.
    """
    pdf_path = Path(path)

    try:
        pages = extract_pdf_text(pdf_path)
    except Exception:
        # Corrupt/unparseable PDF: dispatch contract -> None means "skip this path".
        return None

    n_pages = len(pages)
    text = "".join(p["text"] for p in pages)

    native_metadata: dict = {"n_pages": n_pages}

    avg_chars = (len(text) / n_pages) if n_pages else 0
    scanned = avg_chars < _MIN_CHARS_PER_PAGE
    native_metadata["scanned"] = scanned

    if scanned:
        ocr_text = _ocr_pages(pdf_path)
        if ocr_text is not None:
            native_metadata["ocr_attempted"] = True
            # Augment whatever sparse text we had with the OCR output.
            text = (text + "\n" + ocr_text) if text.strip() else ocr_text
        else:
            native_metadata["ocr_attempted"] = False

    return RawDoc(
        text=text,
        source_path=path,
        source_type=classify_source_type(path),
        native_metadata=native_metadata,
    )


register(".pdf", loader=pdf_loader)
