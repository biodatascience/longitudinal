# rag/tests/test_chunk.py
import pytest
from bios667_rag.chunk import semantic_chunk, Chunk, chunk_document
from bios667_rag.loaders.base import RawDoc


def test_semantic_chunk_respects_sections():
    text = """
8.1 Introduction

This section introduces random effects models. Random effects capture
correlation within clusters by assuming that observations from the same
cluster share common random deviations from the population mean.

8.2 Model Specification

The linear mixed effects model can be written as Y = Xβ + Zb + ε where
b represents the random effects. This formulation allows for both fixed
population-level effects and random subject-specific deviations.
"""

    chunks = semantic_chunk(text, chapter_num=8, max_tokens=100)

    assert len(chunks) >= 2
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].section_path.startswith("8.1")
    assert chunks[1].section_path.startswith("8.2")


def test_chunk_document_hw_splits_per_problem():
    text = (
        "1. First problem about random intercepts. Fit a model.\n"
        "2. Second problem about GEE. Compare working correlations.\n"
        "3. Third problem about GLMMs. Interpret the attenuation."
    )
    doc = RawDoc(text=text, source_path="homework/HW3.qmd", source_type="hw")

    chunks = chunk_document(doc)

    assert len(chunks) == 3
    assert all(ctype == "problem" for _, ctype in chunks)
    assert "First problem" in chunks[0][0]
    assert "Second problem" not in chunks[0][0]
    assert "Second problem" in chunks[1][0]
    assert "Third problem" in chunks[2][0]


def test_chunk_document_code_each_chunk_carries_nl_header():
    nl_header = "SAS program. Procedures: glm, mixed."
    text = nl_header + "\n\nproc glm; run;\nproc mixed; run;"
    doc = RawDoc(
        text=text,
        source_path="code/example.sas",
        source_type="sas",
        native_metadata={"nl_header": nl_header},
    )

    chunks = chunk_document(doc)

    assert len(chunks) >= 2
    assert all(ctype == "code" for _, ctype in chunks)
    # Every chunk must independently carry the NL header for retrieval.
    assert all("SAS program. Procedures" in ctext for ctext, _ in chunks)


def test_chunk_document_code_whitespace_only_yields_no_chunks():
    # A whitespace-only code RawDoc must not produce an empty chunk that would
    # pollute the index (guards the _chunk_code fallback path).
    doc = RawDoc(
        text="   \n\n  \t\n",
        source_path="code/empty.sas",
        source_type="sas",
        native_metadata={"nl_header": ""},
    )

    chunks = chunk_document(doc)

    assert chunks == []


def test_chunk_document_code_nonempty_header_whitespace_body_yields_no_chunks():
    # A non-empty nl_header with a whitespace-only body must NOT produce a
    # header-only junk chunk: the fallback is gated on the stripped post-header
    # body, not the full text (which would be truthy due to the header).
    nl_header = "SAS program. Procedures: none."
    doc = RawDoc(
        text=nl_header + "\n\n   \n\t\n",
        source_path="code/header_only.sas",
        source_type="sas",
        native_metadata={"nl_header": nl_header},
    )

    chunks = chunk_document(doc)

    assert chunks == []


def test_chunk_document_data_card_single_chunk():
    doc = RawDoc(
        text="Dental dataset. 27 subjects, 4 occasions. Distance in mm.",
        source_path="data/dental.csv",
        source_type="data_card",
    )

    chunks = chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0][1] == "card"


def test_chunk_document_prose_is_heading_aware():
    text = (
        "## Response Profiles\n\n"
        "Response profile analysis treats time as categorical. "
        "It is the most general approach for balanced designs.\n\n"
        "## Hypothesis Testing\n\n"
        "We test for group-by-time interactions using a multivariate "
        "Wald or likelihood ratio test across all occasions."
    )
    doc = RawDoc(
        text=text, source_path="lectures/L05.qmd", source_type="lecture"
    )

    chunks = chunk_document(doc)

    assert len(chunks) >= 1
    assert all(ctype == "content" for _, ctype in chunks)
    joined = "\n".join(ctext for ctext, _ in chunks)
    assert "Response Profiles" in joined
    assert "Hypothesis Testing" in joined
