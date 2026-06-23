"""Tests for the Quarto/RMarkdown loader (``.qmd`` / ``.rmd``).

Pins front-matter parsing (including the no-front-matter case), code-fence
preservation in ``text``, role-based ``source_type`` classification, and that the
loader is registered so dispatch ``load`` reaches it.
"""

from bios667_rag.loaders.dispatch import load
from bios667_rag.loaders.quarto import quarto_loader

_QMD_WITH_FM = (
    "---\n"
    'title: "L8 LME"\n'
    "format: revealjs\n"
    "---\n"
    "\n"
    "## Intro\n"
    "Some prose.\n"
    "\n"
    "```{r}\n"
    "lmer(y~x)\n"
    "```\n"
)


def test_qmd_front_matter_parsed(tmp_path):
    d = tmp_path / "lectures"
    d.mkdir()
    f = d / "BIOS667_L08.qmd"
    f.write_text(_QMD_WITH_FM)

    rd = quarto_loader(str(f))
    assert rd is not None
    assert rd.native_metadata["front_matter"]["title"] == "L8 LME"
    assert rd.native_metadata["front_matter"]["format"] == "revealjs"


def test_qmd_title_extracted(tmp_path):
    d = tmp_path / "lectures"
    d.mkdir()
    f = d / "BIOS667_L08.qmd"
    f.write_text(_QMD_WITH_FM)

    rd = quarto_loader(str(f))
    assert rd.native_metadata["title"] == "L8 LME"


def test_qmd_role_based_source_type_is_lecture(tmp_path):
    """A revealjs lecture deck classifies as ``lecture``, NOT ``slides``."""
    d = tmp_path / "lectures"
    d.mkdir()
    f = d / "BIOS667_L08.qmd"
    f.write_text(_QMD_WITH_FM)

    rd = quarto_loader(str(f))
    assert rd.source_type == "lecture"


def test_qmd_body_preserves_prose_and_code_fences(tmp_path):
    d = tmp_path / "lectures"
    d.mkdir()
    f = d / "BIOS667_L08.qmd"
    f.write_text(_QMD_WITH_FM)

    rd = quarto_loader(str(f))
    assert "## Intro" in rd.text
    assert "lmer(y~x)" in rd.text
    # Front-matter block stripped entirely: neither the `---` fences nor any
    # front-matter key (e.g. `title:`/`format:`) leaks into the body, and the
    # body begins at the first prose line.
    assert "---" not in rd.text
    assert "title:" not in rd.text
    assert "format: revealjs" not in rd.text
    assert rd.text.lstrip().startswith("## Intro")


def test_rmd_under_handouts_is_handout(tmp_path):
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "guide.rmd"
    f.write_text("---\ntitle: \"Guide\"\n---\n\nBody text here.\n")

    rd = quarto_loader(str(f))
    assert rd is not None
    assert rd.source_type == "handout"


def test_qmd_no_front_matter(tmp_path):
    f = tmp_path / "notes.qmd"
    body = "## Just a body\n\nNo front matter at all.\n"
    f.write_text(body)

    rd = quarto_loader(str(f))
    assert rd is not None
    assert rd.native_metadata["front_matter"] == {}
    assert rd.text == body


def test_dispatch_load_routes_qmd(tmp_path):
    d = tmp_path / "lectures"
    d.mkdir()
    f = d / "BIOS667_L08.qmd"
    f.write_text(_QMD_WITH_FM)

    rd = load(str(f))
    assert rd is not None
    assert rd.source_type == "lecture"
    assert rd.native_metadata["front_matter"]["title"] == "L8 LME"


def test_dispatch_load_routes_rmd(tmp_path):
    """The ``.rmd`` extension is registered too, so ``load`` reaches the loader."""
    d = tmp_path / "handouts"
    d.mkdir()
    f = d / "guide.rmd"
    f.write_text('---\ntitle: "Guide"\n---\n\nBody text here.\n')

    rd = load(str(f))
    assert rd is not None
    assert rd.source_type == "handout"
    assert rd.native_metadata["front_matter"]["title"] == "Guide"
