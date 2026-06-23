"""Tests for the prose loader (``.md`` and prose ``.txt``).

``prose_loader`` reads a plain-text file verbatim as UTF-8, sets ``text`` to the
file contents and ``source_type`` via ``classify_source_type``. Empty/whitespace
content yields ``None`` (the single-meaning loader contract).
"""

from bios667_rag.loaders.base import RawDoc
from bios667_rag.loaders.prose import prose_loader
from bios667_rag.metadata import SOURCE_TYPES


def test_md_file_loads_prose(tmp_path):
    f = tmp_path / "notes.md"
    prose = "# Heading\n\nThis is some markdown prose about longitudinal data.\n"
    f.write_text(prose)

    doc = prose_loader(str(f))

    assert isinstance(doc, RawDoc)
    assert "markdown prose about longitudinal data" in doc.text
    assert doc.text == prose
    assert doc.source_path == str(f)
    assert doc.source_type in SOURCE_TYPES


def test_prose_txt_loads_via_prose_loader(tmp_path):
    f = tmp_path / "readme.txt"
    prose = "These are English sentences. They describe the dataset in words.\n"
    f.write_text(prose)

    doc = prose_loader(str(f))

    assert isinstance(doc, RawDoc)
    assert doc.text == prose
    assert doc.source_type in SOURCE_TYPES


def test_empty_prose_returns_none(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("")
    assert prose_loader(str(f)) is None


def test_whitespace_only_prose_returns_none(tmp_path):
    f = tmp_path / "blank.md"
    f.write_text("   \n\t  \n")
    assert prose_loader(str(f)) is None
