"""Tests for the LaTeX loader (``.tex``).

Pins preamble stripping (drop everything before ``\\begin{document}``), line-comment
removal with ``\\%`` literal-percent preservation, heading text survival
(``\\section{...}`` -> readable heading line), role-based ``source_type``, and that the
loader is registered so dispatch ``load`` reaches it.
"""

from bios667_rag.loaders.dispatch import load
from bios667_rag.loaders.latex import latex_loader

_TEX_WITH_PREAMBLE = (
    "\\documentclass{article}\n"
    "\\usepackage{amsmath}\n"
    "\\begin{document}\n"
    "% this is a comment\n"
    "\\section{Covariance Models}\n"
    "Compound symmetry assumes equal correlation.\n"
    "We need 50\\% power for this study.\n"
    "\\end{document}\n"
)


def test_tex_preamble_stripped_and_headings_kept(tmp_path):
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "cov.tex"
    f.write_text(_TEX_WITH_PREAMBLE)

    rd = latex_loader(str(f))
    assert rd is not None
    # Heading text survives for chunking/retrieval.
    assert "Covariance Models" in rd.text
    # Body prose survives.
    assert "Compound symmetry assumes" in rd.text
    # Preamble dropped.
    assert "\\documentclass" not in rd.text
    assert "amsmath" not in rd.text
    # Comment text removed.
    assert "this is a comment" not in rd.text


def test_tex_source_type_role_based(tmp_path):
    """A ``.tex`` under ``handouts/`` classifies as ``handout``."""
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "cov.tex"
    f.write_text(_TEX_WITH_PREAMBLE)

    rd = latex_loader(str(f))
    assert rd.source_type == "handout"


def test_tex_escaped_percent_preserved(tmp_path):
    """``\\%`` is a literal percent, NOT a comment start, so the line survives."""
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "cov.tex"
    f.write_text(_TEX_WITH_PREAMBLE)

    rd = latex_loader(str(f))
    # We unescape ``\\%`` to a literal ``%`` in the output.
    assert "50% power" in rd.text


def test_tex_double_backslash_then_comment(tmp_path):
    """``\\\\`` is a line break (literal ``\\\\``); a following ``%`` starts a comment.

    The leading backslash must not pair with the second backslash's ``%`` and be
    mistaken for an escaped percent. ``50\\\\% rest`` -> ``50\\\\`` with the comment
    dropped (the ``%`` after the line break is a real comment marker).
    """
    f = tmp_path / "lb.tex"
    f.write_text(
        "\\begin{document}\n"
        "Row one\\\\% trailing comment after line break\n"
        "Row two.\n"
        "\\end{document}\n"
    )

    rd = latex_loader(str(f))
    assert rd is not None
    # The literal line break survives.
    assert "Row one\\\\" in rd.text
    # The comment after the line break is removed.
    assert "trailing comment" not in rd.text
    # The escaped-percent path was not wrongly taken (no literal percent emitted).
    assert "%" not in rd.text
    assert "Row two." in rd.text


def test_tex_no_begin_document_keeps_whole_file(tmp_path):
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "snippet.tex"
    f.write_text(
        "\\section{Intro}\n"
        "% drop me\n"
        "Just a fragment of body prose.\n"
    )

    rd = latex_loader(str(f))
    assert rd is not None
    assert "Intro" in rd.text
    assert "Just a fragment of body prose." in rd.text
    assert "drop me" not in rd.text


def test_tex_subsection_headings_readable(tmp_path):
    f = tmp_path / "h.tex"
    f.write_text(
        "\\begin{document}\n"
        "\\subsection{Random Effects}\n"
        "\\subsubsection{Variance Components}\n"
        "Body.\n"
        "\\end{document}\n"
    )

    rd = latex_loader(str(f))
    assert "Random Effects" in rd.text
    assert "Variance Components" in rd.text


def test_tex_empty_after_stripping_returns_none(tmp_path):
    f = tmp_path / "empty.tex"
    f.write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "% only a comment\n"
        "\\end{document}\n"
    )

    rd = latex_loader(str(f))
    assert rd is None


def test_dispatch_load_routes_tex(tmp_path):
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "cov.tex"
    f.write_text(_TEX_WITH_PREAMBLE)

    rd = load(str(f))
    assert rd is not None
    assert rd.source_type == "handout"
    assert "Covariance Models" in rd.text
