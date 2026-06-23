"""Tests for the loader dispatch registry and the ``RawDoc`` dataclass.

The dispatch ``load`` returns ``None`` with EXACTLY ONE meaning: "no loader claims
this path" -- whether the extension is unmapped, the file is empty/whitespace-only,
or the file is unreadable/undecodable. These tests pin that single-meaning contract
plus registry dispatch, and keep the registry test-isolated via a fixture.
"""

import pytest

from bios667_rag.loaders import LOADERS, RawDoc, load
from bios667_rag.loaders.dispatch import register


@pytest.fixture
def clean_registry():
    """Snapshot/restore ``LOADERS`` so a test's dummy registration cannot leak."""
    saved = dict(LOADERS)
    try:
        yield
    finally:
        LOADERS.clear()
        LOADERS.update(saved)


def test_rawdoc_default_native_metadata_is_empty_dict():
    doc = RawDoc(text="x", source_path="p", source_type="lecture")
    assert doc.native_metadata == {}
    # Each instance gets its own dict (default_factory, not a shared mutable default).
    other = RawDoc(text="y", source_path="q", source_type="hw")
    assert other.native_metadata is not doc.native_metadata


def test_unmapped_extension_returns_none(tmp_path):
    """Registry-miss branch: valid UTF-8 text but no loader claims the extension."""
    f = tmp_path / "fig.zzz"
    f.write_text("valid utf-8 content")
    assert load(str(f)) is None


def test_undecodable_bytes_returns_none(tmp_path, clean_registry):
    """Distinct branch: a mapped-looking file whose bytes are not valid UTF-8.

    Covered as its own test because undecodable/unreadable is a different reason
    ``load`` returns ``None`` than an unmapped extension.

    We register a ``.png`` loader that returns a sentinel ``RawDoc``, then assert
    ``load`` still returns ``None``. Because the UTF-8 decode check runs *before*
    the registry lookup, the dummy loader is never reached -- proving the ``None``
    came from the ``UnicodeDecodeError`` branch and NOT from an unmapped extension.
    This keeps the test robust if someone later removes the pre-read decode check.
    """
    f = tmp_path / "fig.png"
    f.write_bytes(b"\x89PNG\r\n")

    sentinel = RawDoc(text="loaded", source_path=str(f), source_type="lecture")
    register(".png", loader=lambda path: sentinel)

    assert load(str(f)) is None


def test_empty_file_returns_none(tmp_path):
    f = tmp_path / "empty.qmd"
    f.write_text("")
    assert load(str(f)) is None


def test_whitespace_only_file_returns_none(tmp_path):
    f = tmp_path / "blank.qmd"
    f.write_text("   \n\t  \n")
    assert load(str(f)) is None


def test_registry_dispatch_calls_registered_loader(tmp_path, clean_registry):
    f = tmp_path / "thing.foo"
    f.write_text("real content")

    sentinel = RawDoc(text="loaded", source_path=str(f), source_type="lecture")

    def dummy_loader(path: str) -> RawDoc:
        return sentinel

    register(".foo", loader=dummy_loader)
    assert load(str(f)) is sentinel


def test_dummy_registration_does_not_leak(tmp_path):
    """Outside the clean_registry fixture, ``.foo`` must still be unmapped."""
    f = tmp_path / "thing.foo"
    f.write_text("real content")
    assert load(str(f)) is None


def test_prose_txt_routes_to_prose_not_data_card(tmp_path):
    """A prose ``.txt`` (English sentences, not tabular) routes to prose_loader."""
    f = tmp_path / "notes.txt"
    prose = "These are English sentences. They describe a longitudinal study in words.\n"
    f.write_text(prose)

    doc = load(str(f))
    assert doc is not None
    assert doc.source_type != "data_card"
    assert doc.text == prose


def test_tabular_txt_routes_to_data_card(tmp_path):
    """A tabular ``.txt`` routes to data_card_loader via looks_like_data."""
    f = tmp_path / "table.txt"
    f.write_text("id,age\n1,5\n2,6\n3,7\n4,8")

    doc = load(str(f))
    assert doc is not None
    assert doc.source_type == "data_card"


def test_empty_txt_returns_none(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    assert load(str(f)) is None


def test_md_routes_to_loader(tmp_path):
    """A ``.md`` file dispatches to the registered prose loader."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nSome prose content here.\n")

    doc = load(str(f))
    assert doc is not None
    assert "Some prose content here" in doc.text
