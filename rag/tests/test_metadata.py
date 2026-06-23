"""Tests for the metadata schema (SourceType, ChunkMeta, make_chunk_id)."""

import pytest

from bios667_rag.metadata import (
    SOURCE_TYPES,
    ChunkMeta,
    classify_source_type,
    flw_textbook_chapters,
    make_chunk_id,
    map_chapters,
)


def test_chunk_id_stable_and_separated():
    cid = make_chunk_id("a/b.sas", 3)
    assert len(cid) == 40 and cid == make_chunk_id("a/b.sas", 3)
    assert make_chunk_id("foo", 10) != make_chunk_id("foo1", 0)


def test_chunkmeta_chroma_roundtrip():
    m = ChunkMeta(chunk_id="x", source_type="lecture", source_path="p.qmd",
                  title="L8", chapters=[1, 10, 11], topic_tags=["lme"],
                  year=2025, dataset_refs=["sixcities"], is_solution=False,
                  chunk_type="content")
    d = m.to_chroma()
    assert all(not isinstance(v, (list, dict)) for v in d.values())  # chroma needs scalars
    back = ChunkMeta.from_chroma(d)
    assert back.chapters == [1, 10, 11]      # parses back to list[int], no substring corruption
    assert back.topic_tags == ["lme"] and back.dataset_refs == ["sixcities"]
    # empty lists round-trip cleanly:
    empty = ChunkMeta.from_chroma(ChunkMeta(chunk_id="y", source_type="data_card",
            source_path="d.csv", title="d", chapters=[], topic_tags=[], year=None,
            dataset_refs=[], is_solution=False, chunk_type="card").to_chroma())
    assert empty.chapters == [] and empty.dataset_refs == []
    assert empty.year is None                # -1 sentinel restores to None


@pytest.mark.parametrize(
    "path, front_matter, expected",
    [
        # role beats format: a revealjs lecture deck is a lecture, not slides
        ("lectures/BIOS667_L08_LME.qmd", {"format": "revealjs"}, "lecture"),
        # root-level lecture deck recognized by BIOS667_L\d+ filename pattern
        ("BIOS667_L08_LME.qmd", {"format": "revealjs"}, "lecture"),
        # standalone pptx is slides
        ("slides/ADAPT Biannual Slide Deck.pptx", None, "slides"),
        # path-signal documents
        ("handouts/GEE_Complete_Guide.qmd", None, "handout"),
        ("homework/HW3_solution.qmd", None, "hw_solution"),
        ("homework/HW3.qmd", None, "hw"),
        ("quizzes/Quiz2.qmd", None, "quiz"),
        # code / data extensions
        ("6city01a.sas", None, "sas"),
        ("analysis.r", None, "rcode"),
        # .rmd is a document, NOT rcode; path signal handout wins
        ("handouts/report.rmd", None, "handout"),
        # data extensions
        ("foo.dat", None, "data_card"),
        ("data/dental.csv", None, "data_card"),
        # syllabus by filename (highest priority)
        ("BIOS_667_2025_syllabus.docx", None, "syllabus"),
        # tex handout by path signal
        ("handouts/L04_handout_ch4.tex", None, "handout"),
        # real FLW textbook PDF under book/ -> textbook (not lecture catch-all)
        (
            "book/Applied Longitudinal Analysis - 2011 - Fitzmaurice - "
            "Linear Mixed Effects Models.pdf",
            None,
            "textbook",
        ),
        # a Fitzmaurice-named file anywhere -> textbook
        ("reference/Fitzmaurice_2011_ch5.pdf", None, "textbook"),
        # "applied longitudinal analysis" in filename (case-insensitive) -> textbook
        ("misc/Applied Longitudinal Analysis excerpt.pdf", None, "textbook"),
        # design docs whose path contains the word "textbook" must NOT be textbook
        # (the loose path rule was removed); with no other signal -> catch-all lecture
        ("docs/plans/2025-01-16-textbook-rag-design.md", None, "lecture"),
        # unknown doc with no path signal -> catch-all default
        ("random_notes.qmd", None, "lecture"),
    ],
)
def test_classify_source_type(path, front_matter, expected):
    result = classify_source_type(path, front_matter)
    assert result == expected
    assert result in SOURCE_TYPES


@pytest.mark.parametrize(
    "path, front_matter, expected",
    [
        # multi-chapter shorthand in filename: _ch5_6 means chapters 5 AND 6
        ("lectures/BIOS667_L05_Foo_ch5_6.qmd", None, [5, 6]),
        # single chapter from filename
        ("lectures/BIOS667_L08_LME_ch8.qmd", None, [8]),
        # explicit front-matter scalar chapter wins
        ("handouts/Guide.qmd", {"chapter": 7}, [7]),
        # explicit front-matter chapters list wins
        ("handouts/Guide.qmd", {"chapters": [11, 12]}, [11, 12]),
        # no signal -> empty list
        ("data/dental.csv", None, []),
        # sorted ascending and de-duplicated (ch6 before ch5 in path)
        ("lectures/L99_ch6_ch5.qmd", None, [5, 6]),
        # two-digit multi-chapter form
        ("lectures/Foo_ch11_12.qmd", None, [11, 12]),
        # empty front-matter list is falsy -> fall through to path inference
        ("lectures/BIOS667_L05_ch5.qmd", {"chapters": []}, [5]),
        # non-empty front-matter list still wins over a path ch-signal
        ("lectures/BIOS667_L05_ch5.qmd", {"chapters": [11, 12]}, [11, 12]),
    ],
)
def test_map_chapters(path, front_matter, expected):
    assert map_chapters(path, front_matter) == expected


_FLW = "Applied Longitudinal Analysis - 2011 - Fitzmaurice - "


@pytest.mark.parametrize(
    "filename, expected",
    [
        # numbered chapters by distinctive title keyword
        (f"{_FLW}Linear Mixed Effects Models.pdf", [8]),
        (f"{_FLW}Estimation and Statistical Inference.pdf", [4]),
        (f"{_FLW}Modeling the Mean  Analyzing Response Profiles.pdf", [5]),
        (f"{_FLW}Modeling the Covariance.pdf", [7]),
        (f"{_FLW}Fixed Effects versus Random Effects Models.pdf", [9]),
        (f"{_FLW}Contrasting Marginal and Mixed Effects Models.pdf", [16]),
        # GLMM approximate methods is ch15, must not collide with plain GLMM (ch14)
        (
            f"{_FLW}Generalized Linear Mixed Effects Models  Approximate Methods of.pdf",
            [15],
        ),
        (f"{_FLW}Generalized Linear Mixed Effects Models.pdf", [14]),
        # the two Marginal Models volumes: intro (12) vs GEE (13)
        (f"{_FLW}Marginal Models  Introduction and Overview.pdf", [12]),
        (f"{_FLW}Marginal Models  Generalized Estimating Equations  GEE.pdf", [13]),
        # front matter and appendices have no numbered chapter
        (f"{_FLW}Front Matter.pdf", []),
        (f"{_FLW}Gentle Introduction to Vectors and Matrices.pdf", []),
        # the whole-book single PDF (no topic suffix) -> no single chapter
        ("Applied Longitudinal Analysis - 2011 - Fitzmaurice.pdf", []),
        # case-insensitive, works on a full path too
        ("book/" + f"{_FLW}LINEAR MIXED EFFECTS MODELS.pdf".upper(), [8]),
        # non-FLW filename -> []
        ("lectures/BIOS667_L08_LME.qmd", []),
    ],
)
def test_flw_textbook_chapters(filename, expected):
    assert flw_textbook_chapters(filename) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        # FLW textbook PDF under book/ with no ch-signal: chapter comes from title map
        (f"book/{_FLW}Linear Mixed Effects Models.pdf", [8]),
        (f"book/{_FLW}Contrasting Marginal and Mixed Effects Models.pdf", [16]),
        # Fitzmaurice-named file anywhere also resolves via the title map
        (f"reference/{_FLW}Estimation and Statistical Inference.pdf", [4]),
        # front matter -> still empty
        (f"book/{_FLW}Front Matter.pdf", []),
    ],
)
def test_map_chapters_flw_textbook(path, expected):
    assert map_chapters(path) == expected
