"""Golden-retrieval regression test (Task 6.1) against the REAL built corpus.

These goldens guard against silent retrieval regressions in the live
``bios667_corpus`` store (data/chroma). Each case is a known query that SHOULD
surface a specific known file: we assert an expected substring appears in some
top-k (k=5) result's ``source_path``. Matching is intentionally generous --
case-insensitive substring, k=5 -- so the goldens are STABLE regression guards,
not brittle exact-rank assertions.

CI/dev machines without the built index must NOT fail: the module is skipped
gracefully when the real chroma store is absent (module-level ``pytestmark``),
and the whole module is tagged ``@pytest.mark.golden`` so it can be selected or
deselected explicitly (``-m golden`` / ``-m 'not golden'``).
"""

from pathlib import Path

import pytest

# The real store lives at <repo>/rag/data/chroma. This file is rag/tests/...,
# so parents[1] is rag/, and rag/data/chroma is the persistent chroma store.
_STORE_DIR = Path(__file__).resolve().parents[1] / "data"
_CHROMA_DIR = _STORE_DIR / "chroma"

# Tag every test golden AND skip the whole module if the real store is absent.
pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not _CHROMA_DIR.exists(),
        reason=(
            "real corpus store not built (rag/data/chroma absent); "
            "golden-retrieval regression tests require the live index"
        ),
    ),
]


# (query, source_type filter or None, list of acceptable path substrings).
# A case passes if ANY listed substring appears (case-insensitive) in ANY of the
# top-5 result source_paths. Grounded in what we KNOW is in the corpus: 838 SAS
# example files (6city*.sas, etc.), 23 per-chapter FLW textbook PDFs, 57 data
# cards, and ~1778 lecture chunks (.qmd).
_GOLDEN_CASES = [
    # SAS example files exist (6city*.sas and many others).
    ("random intercept model", "sas", [".sas"]),
    # Per-chapter FLW textbook PDFs (ch8 = Linear Mixed Effects Models).
    ("linear mixed effects models", "textbook", ["Linear Mixed Effects"]),
    # ch12/13 marginal models / GEE textbook PDFs.
    ("generalized estimating equations", "textbook", ["Marginal", "Generalized Estimating"]),
    # A covariance-structure lecture/material (.qmd).
    ("compound symmetry covariance structure", None, [".qmd"]),
    # Epilepsy example/dataset surfaces somewhere unfiltered.
    ("epilepsy seizure counts", None, ["epilepsy", "seizure"]),
    # The six-cities data card (6city.dat).
    ("6city", "data_card", ["6city"]),
    # Dental growth study material surfaces unfiltered.
    ("dental growth study orthodontic", None, ["dental"]),
    # ch17/18 missing-data textbook PDFs.
    ("multiple imputation missing data dropout", "textbook", ["Missing Data"]),
    # ch6 parametric-curves textbook PDF.
    ("parametric curves modeling the mean", "textbook", ["Parametric Curves"]),
    # ch14/15 GLMM textbook PDFs.
    (
        "generalized linear mixed models random effects",
        "textbook",
        ["Generalized Linear Mixed"],
    ),
]


@pytest.fixture(scope="module")
def corpus():
    """A real CorpusQuery against the built store (one model load per module)."""
    from bios667_rag.corpus_query import CorpusQuery

    return CorpusQuery(store_dir=str(_STORE_DIR))


@pytest.mark.parametrize("query,source_type,expected_subs", _GOLDEN_CASES)
def test_golden_retrieval(corpus, query, source_type, expected_subs):
    """Each golden query must surface an expected file in its top-5 source_paths."""
    results = corpus.search_all(query, source_type=source_type, top_k=5)
    paths = [r["source_path"] for r in results]
    assert paths, f"no results for golden query {query!r} (source_type={source_type})"

    joined = " ".join(paths).lower()
    matched = [sub for sub in expected_subs if sub.lower() in joined]
    assert matched, (
        f"golden query {query!r} (source_type={source_type}) did not surface any of "
        f"{expected_subs} in top-5 source_paths: {paths}"
    )


def test_golden_find_datasets_six_cities_has_used_by(corpus):
    """``find_datasets('6city')`` returns the 6city card with non-empty ``used_by``.

    Exercises the knowledge-graph ``material --uses--> dataset`` edges end-to-end:
    the six-cities data card must be found AND list materials that use it.
    """
    cards = corpus.find_datasets("6city", top_k=5)
    assert cards, "find_datasets('6city') returned no cards"

    six = [
        c for c in cards
        if "6city" in Path(c["dataset_card"]["source_path"]).name.lower()
    ]
    assert six, (
        "find_datasets('6city') did not surface a 6city data card: "
        f"{[c['dataset_card']['source_path'] for c in cards]}"
    )
    assert any(c["used_by"] for c in six), (
        "expected a 6city data card with non-empty used_by; "
        f"got used_by sizes {[len(c['used_by']) for c in six]}"
    )
