"""Tests for the corpus walker, ``plan`` preview, and the sha256 ingest manifest.

CRITICAL: every test builds its fake corpus under ``tmp_path``. NONE of these tests
may walk a real directory -- the walker is exercised only against throwaway trees so
it can never ascend into personal/clinical/financial files in the surrounding repo.
"""

from pathlib import Path

from bios667_rag import corpus_index


def _build_corpus(root: Path) -> None:
    """Create a small fake corpus tree mixing admitted, unmapped, and excluded files."""
    (root / "lectures").mkdir()
    (root / "homework").mkdir()
    (root / "data").mkdir()

    # Admitted files (5): qmd x3, csv, sas.
    (root / "lectures" / "BIOS667_L08.qmd").write_text("# Lecture 8\n")
    (root / "homework" / "HW3.qmd").write_text("# HW3\n")
    (root / "homework" / "HW3_solution.qmd").write_text("# HW3 solution\n")
    (root / "data" / "dental.csv").write_text("id,age\n1,5\n")
    (root / "6city.sas").write_text("proc print; run;\n")

    # Unmapped (.png) -- admitted-set miss, should be reported as unindexed.
    (root / "notes.png").write_bytes(b"\x89PNG\r\n")

    # Excluded: under a .venv tree.
    venv = root / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "foo.qmd").write_text("# venv noise\n")

    # Excluded: under a *_cache tree.
    cache = root / "something_cache"
    cache.mkdir()
    (cache / "x.qmd").write_text("# cache noise\n")

    # Excluded: a Quarto render-artifact dir (name ends in ``_files``).
    artifact = root / "BIOS667_L08_files"
    artifact.mkdir()
    (artifact / "figure.qmd").write_text("# render artifact\n")

    # Excluded: a Dropbox conflicted-copy file.
    (root / "L05 (conflicted copy).qmd").write_text("# conflicted\n")


# --- walk ---------------------------------------------------------------------


def test_walk_admits_mapped_excludes_unmapped_and_excluded(tmp_path):
    _build_corpus(tmp_path)
    admitted = corpus_index.walk([str(tmp_path)])
    names = sorted(p.name for p in admitted)

    assert names == [
        "6city.sas",
        "BIOS667_L08.qmd",
        "HW3.qmd",
        "HW3_solution.qmd",
        "dental.csv",
    ]
    # No unmapped, no excluded-tree, no conflicted-copy file slipped in.
    joined = " ".join(str(p) for p in admitted)
    assert "notes.png" not in joined
    assert ".venv" not in joined
    assert "something_cache" not in joined
    assert "_files" not in joined
    assert "conflicted copy" not in joined


def test_walk_excludes_quarto_files_artifact_dir(tmp_path):
    """Regression: Quarto ``*_files`` render-artifact dirs must be pruned.

    The corpus is full of dirs like ``BIOS667_L08_files`` holding render artifacts.
    Their name ends in ``_files`` (it is never literally ``_files``), so exclusion
    must match the ``_files`` SUFFIX, not an exact ``_files`` component.
    """
    artifact = tmp_path / "BIOS667_L08_files"
    artifact.mkdir()
    # An admitted-extension file living inside the artifact dir -- must NOT be indexed.
    (artifact / "figure.qmd").write_text("# render artifact\n")
    # A legitimate sibling that MUST be indexed, proving we excluded the dir not the ext.
    (tmp_path / "BIOS667_L08.qmd").write_text("# real lecture\n")

    admitted = corpus_index.walk([str(tmp_path)])
    names = sorted(p.name for p in admitted)

    assert names == ["BIOS667_L08.qmd"]
    assert all("_files" not in str(p) for p in admitted)


def test_walk_returns_sorted_paths(tmp_path):
    _build_corpus(tmp_path)
    admitted = corpus_index.walk([str(tmp_path)])
    assert admitted == sorted(admitted)


def test_walk_admitted_extensions_derive_from_dispatch(tmp_path):
    """The admitted set must include every dispatch-registered extension plus .txt."""
    from bios667_rag.loaders import LOADERS

    for ext in LOADERS:
        (tmp_path / f"file{ext}").write_text("id,age\n1,5\ncontent here\n")
    (tmp_path / "prose.txt").write_text("English prose sentences here.\n")
    (tmp_path / "skip.zzz").write_text("unmapped\n")

    admitted = {p.suffix.lower() for p in corpus_index.walk([str(tmp_path)])}
    assert set(LOADERS.keys()) <= admitted
    assert ".txt" in admitted
    assert ".zzz" not in admitted


def test_walk_handles_multiple_roots(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "one.qmd").write_text("x\n")
    (b / "two.csv").write_text("id\n1\n")
    admitted = corpus_index.walk([str(a), str(b)])
    assert sorted(p.name for p in admitted) == ["one.qmd", "two.csv"]


def test_walk_dedupes_nested_roots(tmp_path):
    """Nested roots must not double-walk a file (realpath de-duplication, Fix 1).

    The real corpus has two nested default roots (``.../BIOS667`` contains
    ``.../BIOS667/new``); a file under the inner root would otherwise be walked twice.
    """
    a = tmp_path / "a"
    b = a / "b"
    b.mkdir(parents=True)
    (b / "deep.qmd").write_text("# nested\n")

    admitted = corpus_index.walk([str(a), str(b)])
    matches = [p for p in admitted if p.name == "deep.qmd"]
    assert len(matches) == 1, f"file double-walked across nested roots: {matches}"


# --- exclusions (Fix 3) -------------------------------------------------------


def test_walk_excludes_tooling_meta_and_student_repos_and_sas_pdfs(tmp_path):
    """Curation excludes: docs/, rag/, *_note.md, meta files, student repos, SAS PDFs.

    A legitimate lecture and a book/ FLW PDF must survive; everything in the
    curation-exclude categories must be dropped.
    """
    # --- things that MUST be excluded ---
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("# design doc\n")

    (tmp_path / "rag").mkdir()
    (tmp_path / "rag" / "src.qmd").write_text("# rag package file\n")

    (tmp_path / "foo_note.md").write_text("# a note\n")
    (tmp_path / "CLAUDE.md").write_text("# claude config\n")
    (tmp_path / "AGENTS.md").write_text("# agents\n")
    (tmp_path / "CLAUDE_md_improvements.md").write_text("# meta\n")
    (tmp_path / "REVIEW_CROSS_REFERENCE.md").write_text("# meta\n")
    (tmp_path / "COURSE_MATERIALS_AUDIT.md").write_text("# meta\n")
    (tmp_path / "L05_AUDIT.md").write_text("# audit\n")
    (tmp_path / "LECTURE_TIMING_PLAN.md").write_text("# timing\n")
    (tmp_path / "STUDENT_REVIEW_summary.md").write_text("# student review\n")

    repos_cloned = tmp_path / "repos_cloned" / "g1"
    repos_cloned.mkdir(parents=True)
    (repos_cloned / "a.qmd").write_text("# cloned student work\n")

    repos = tmp_path / "repos" / "g2"
    repos.mkdir(parents=True)
    (repos / "b.qmd").write_text("# student repo\n")

    (tmp_path / "6city04sas.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "6city06_sas.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "output_SAS.pdf").write_bytes(b"%PDF-1.4")

    # --- things that MUST survive ---
    (tmp_path / "lectures").mkdir()
    (tmp_path / "lectures" / "BIOS667_L08.qmd").write_text("# real lecture\n")

    (tmp_path / "book").mkdir()
    flw = (
        tmp_path / "book"
        / "Applied Longitudinal Analysis - 2011 - Fitzmaurice - "
          "Linear Mixed Effects Models.pdf"
    )
    flw.write_bytes(b"%PDF-1.4")

    # A .sas SOURCE file (not a pdf) must NOT be excluded by the SAS-pdf rule.
    (tmp_path / "6city04.sas").write_text("proc print; run;\n")

    # A reference-paper PDF (kept) -- not a 6city/sas output pdf.
    (tmp_path / "Diggle_1994_longitudinal.pdf").write_bytes(b"%PDF-1.4")

    admitted = corpus_index.walk([str(tmp_path)])
    names = sorted(p.name for p in admitted)
    joined = " ".join(str(p) for p in admitted)

    # Survivors present.
    assert "BIOS667_L08.qmd" in names
    assert any("Fitzmaurice" in n for n in names)
    assert "6city04.sas" in names
    assert "Diggle_1994_longitudinal.pdf" in names

    # Tooling / meta excluded.
    assert "/docs/" not in joined and "docs/x.md" not in joined
    assert "/rag/" not in joined
    assert "foo_note.md" not in joined
    assert "CLAUDE.md" not in joined
    assert "AGENTS.md" not in joined
    assert "CLAUDE_md_improvements.md" not in joined
    assert "REVIEW_CROSS_REFERENCE.md" not in joined
    assert "COURSE_MATERIALS_AUDIT.md" not in joined
    assert "L05_AUDIT.md" not in joined
    assert "LECTURE_TIMING_PLAN.md" not in joined
    assert "STUDENT_REVIEW_summary.md" not in joined

    # Student repos excluded.
    assert "repos_cloned" not in joined
    assert "/repos/" not in joined

    # SAS-output PDFs excluded.
    assert "6city04sas.pdf" not in joined
    assert "6city06_sas.pdf" not in joined
    assert "output_SAS.pdf" not in joined


def test_walk_excludes_stale_repo_course_clone(tmp_path):
    """A stale ``repo/`` course-clone subtree is pruned; legit ``lectures/`` survives.

    ``.../BIOS667/repo`` is an Aug-Oct 2025 git clone of the course that duplicates
    the canonical ``new/`` materials (textbook PDFs, older-version lectures, data).
    Any path with a ``repo`` path component must be excluded (same exact-component
    mechanism as ``repos``/``repos_cloned``), while a legitimate ``lectures/`` file
    must NOT be.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "x.qmd").write_text("# stale course-clone lecture\n")

    (tmp_path / "lectures").mkdir()
    (tmp_path / "lectures" / "BIOS667_L08.qmd").write_text("# real lecture\n")

    admitted = corpus_index.walk([str(tmp_path)])
    joined = " ".join(str(p) for p in admitted)
    names = sorted(p.name for p in admitted)

    assert "/repo/" not in joined
    assert "x.qmd" not in names
    assert "BIOS667_L08.qmd" in names


def test_walk_excludes_whole_book_pdf_keeps_per_chapter(tmp_path):
    """The redundant whole-book FLW PDF is excluded; per-chapter PDFs survive.

    ``book/`` holds one per-chapter PDF each named ``...Fitzmaurice - <Topic>.pdf`` plus
    a single whole-book blob ``Applied Longitudinal Analysis - 2011 - Fitzmaurice.pdf``
    (entire textbook as one untagged file, chapters=[]) that duplicates them. The
    exact-basename exclusion must drop ONLY the whole-book file.
    """
    book = tmp_path / "book"
    book.mkdir()
    whole = book / "Applied Longitudinal Analysis - 2011 - Fitzmaurice.pdf"
    whole.write_bytes(b"%PDF-1.4")
    per_chapter = (
        book
        / "Applied Longitudinal Analysis - 2011 - Fitzmaurice - "
          "Linear Mixed Effects Models.pdf"
    )
    per_chapter.write_bytes(b"%PDF-1.4")

    admitted = corpus_index.walk([str(tmp_path)])
    names = sorted(p.name for p in admitted)

    # Whole-book file excluded.
    assert "Applied Longitudinal Analysis - 2011 - Fitzmaurice.pdf" not in names
    # Per-chapter file survives.
    assert (
        "Applied Longitudinal Analysis - 2011 - Fitzmaurice - "
        "Linear Mixed Effects Models.pdf"
    ) in names


# --- plan ---------------------------------------------------------------------


def test_plan_reports_counts_total_and_unindexed(tmp_path):
    _build_corpus(tmp_path)
    report = corpus_index.plan([str(tmp_path)])

    assert report["total_admitted"] == 5

    counts = report["counts_by_source_type"]
    assert counts.get("lecture", 0) >= 1
    assert counts.get("hw", 0) >= 1
    assert counts.get("hw_solution", 0) >= 1
    assert counts.get("sas", 0) >= 1
    assert counts.get("data_card", 0) >= 1

    unindexed_names = " ".join(str(p) for p in report["unindexed"])
    assert "notes.png" in unindexed_names


def test_plan_scanned_pdfs_is_a_count(tmp_path):
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "a.qmd").write_text("x\n")
    report = corpus_index.plan([str(tmp_path)])
    assert isinstance(report["scanned_pdfs"], int)
    assert report["scanned_pdfs"] == 1


# --- manifest -----------------------------------------------------------------


def test_manifest_path_is_under_store_dir(tmp_path):
    p = corpus_index.manifest_path(str(tmp_path))
    assert Path(p).name == "ingest_manifest.json"
    assert str(tmp_path) in str(p)


def test_load_manifest_missing_returns_empty(tmp_path):
    assert corpus_index.load_manifest(str(tmp_path / "nope.json")) == {}


def test_is_changed_lifecycle(tmp_path):
    f = tmp_path / "f.qmd"
    f.write_text("original content\n")
    mpath = corpus_index.manifest_path(str(tmp_path))

    manifest = corpus_index.load_manifest(mpath)
    # New file: changed.
    assert corpus_index.is_changed(str(f), manifest) is True

    corpus_index.update_manifest(manifest, str(f))
    corpus_index.save_manifest(manifest, mpath)
    reloaded = corpus_index.load_manifest(mpath)

    # Recorded + unchanged content: not changed.
    assert corpus_index.is_changed(str(f), reloaded) is False

    # Modify content -> sha differs -> changed.
    f.write_text("DIFFERENT content now\n")
    assert corpus_index.is_changed(str(f), reloaded) is True


def test_file_sha256_changes_with_content(tmp_path):
    f = tmp_path / "f.qmd"
    f.write_text("aaa")
    h1 = corpus_index.file_sha256(str(f))
    f.write_text("bbb")
    h2 = corpus_index.file_sha256(str(f))
    assert h1 != h2
    assert len(h1) == 64  # sha256 hex digest length


# --- build pipeline -----------------------------------------------------------
#
# CRITICAL test-safety: every build() test writes ONLY into a tmp store_dir and
# walks ONLY a tmp_path corpus. The real 839MB corpus and real rag/data store are
# never touched. We use a tiny deterministic FAKE embedder (records call order,
# returns fixed-dim vectors) so tests are fast and offline -- no model download.


class _FakeEmbedder:
    """Deterministic stand-in for ``Embedder``: records call order, fixed vectors.

    ``embed(list[str]) -> list[list[float]]`` returns a 4-dim vector per text whose
    components are seeded from a stable hash of the text, so identical text -> identical
    vector (needed for the nearest-textbook-chunk vote to be deterministic). Each call's
    input texts are appended to ``self.calls`` so a test can assert ordering.
    """

    def __init__(self):
        self.calls = []

    def _vec(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.sha1(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h[:4]]

    def embed(self, texts):
        self.calls.append(list(texts))
        return [self._vec(t) for t in texts]


def _build_index_corpus(root: Path) -> None:
    """Fixture corpus for build(): textbook x2, hw (no ch signal), data_card, sas."""
    tb = root / "book"
    tb.mkdir()
    # Two textbook-classified files (under ``book/``; ``_ch5_`` -> chapter 5). They are
    # textbook by the ``/book/`` path signal (the loose "textbook"-in-path rule was
    # removed), so their basenames need no Fitzmaurice marker.
    (tb / "flw_ch5_intro.md").write_text(
        "# Chapter 5 Response Profiles\n\n"
        "We model the mean response over time using a saturated profile.\n"
    )
    (tb / "flw_ch5_methods.md").write_text(
        "# Chapter 5 Methods\n\n"
        "The dental growth study illustrates response profile analysis over time.\n"
    )

    # A homework qmd with NO chapter signal -- chapters must be INFERRED via the
    # textbook vote (its prose echoes the textbook so the nearest record is ch 5).
    hw = root / "homework"
    hw.mkdir()
    (hw / "HW2.qmd").write_text(
        "# Homework 2\n\n"
        "1. Fit a response profile model to the dental growth study data over time.\n"
    )

    # A data_card under data/.
    data = root / "data"
    data.mkdir()
    (data / "dental.csv").write_text("id,age,distance\n1,8,21.0\n1,10,20.0\n2,8,21.5\n")

    # A SAS file mentioning the dental dataset by stem -> material--uses-->dental edge.
    (root / "analysis.sas").write_text(
        "/* analysis of dental data */\nproc mixed data=dental; run;\n"
    )


def _open_corpus_collection(store_dir: Path):
    """Open the bios667_corpus chroma collection at ``store_dir`` for assertions."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(store_dir / "chroma"),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name="bios667_corpus", metadata={"hnsw:space": "cosine"}
    )


def test_build_indexes_records_and_writes_log(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    fake = _FakeEmbedder()
    log = corpus_index.build([str(corpus)], str(store), embedder=fake)

    coll = _open_corpus_collection(store)
    assert coll.count() > 0

    # Log written with sane counts.
    log_file = store / "corpus_index_log.json"
    assert log_file.exists()
    import json

    on_disk = json.loads(log_file.read_text())
    assert on_disk["files_processed"] >= 5
    assert on_disk["chunks_added"] >= 5
    assert on_disk["by_source_type"].get("textbook", 0) >= 2
    assert log == on_disk


def test_build_textbook_first_ordering(tmp_path):
    """Textbook files MUST embed before the hw file.

    Verified two independent ways: (1) the fake embedder's recorded call order has the
    first textbook embed strictly before the first hw embed; (2) the hw's inferred
    chapters == [5], which is ONLY possible if textbook records were already indexed
    when the hw's empty-chapters vote ran.
    """
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    fake = _FakeEmbedder()
    corpus_index.build([str(corpus)], str(store), embedder=fake)

    # (1) call-order check: flatten recorded texts, find first textbook vs first hw.
    flat = [t for call in fake.calls for t in call]

    def _first_idx(pred):
        for i, t in enumerate(flat):
            if pred(t):
                return i
        return None

    # The hw preamble ("# Homework 2") is dropped by the problem chunker, so we match
    # the problem body text that survives into the embedded chunk.
    tb_idx = _first_idx(lambda t: "Response Profiles" in t or "Chapter 5" in t)
    hw_idx = _first_idx(lambda t: "Fit a response profile model" in t)
    assert tb_idx is not None and hw_idx is not None
    assert tb_idx < hw_idx, "textbook must be embedded before homework"

    # (2) inferred-chapters check: the hw chunk's chapters must be [5] (voted).
    coll = _open_corpus_collection(store)
    got = coll.get(where={"source_type": "hw"}, include=["metadatas"])
    assert got["metadatas"], "hw record should exist"
    chapters = {m["chapters"] for m in got["metadatas"]}
    assert "5" in chapters, f"hw chapters should be inferred as 5, got {chapters}"


def test_build_creates_material_uses_dataset_edge(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    fake = _FakeEmbedder()
    corpus_index.build([str(corpus)], str(store), embedder=fake)

    from bios667_rag.storage import KnowledgeStore

    ks = KnowledgeStore(
        db_path=store / "graph.db", chromadb_path=store / "chroma"
    )
    # Edge is stored material--uses-->dataset; querying from the dataset node
    # relies on get_related's bidirectional traversal (matches source_id OR target_id).
    related = ks.get_related("dataset_dental", relationship="uses")
    ks.close()
    # The .sas material that mentions ``dental`` should have a uses edge to the dataset,
    # and the related material node's name must point back at analysis.sas.
    assert related, "expected at least one material--uses-->dental edge"
    assert any(
        r and "analysis.sas" in (r.get("name") or "") for r in related
    ), f"expected a uses edge from analysis.sas, got {[r.get('name') for r in related]}"


def test_build_incremental_short_circuit_and_single_change(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    log1 = corpus_index.build([str(corpus)], str(store), embedder=_FakeEmbedder())
    assert log1["files_processed"] >= 5

    # Second build, no changes: manifest short-circuit -> 0 files processed.
    log2 = corpus_index.build([str(corpus)], str(store), embedder=_FakeEmbedder())
    assert log2["files_processed"] == 0

    # Touch exactly one file's content -> only that one reprocesses.
    (corpus / "homework" / "HW2.qmd").write_text(
        "# Homework 2 (revised)\n\n1. Refit the dental response profile over time.\n"
    )
    log3 = corpus_index.build([str(corpus)], str(store), embedder=_FakeEmbedder())
    assert log3["files_processed"] == 1


def test_build_rebuild_reprocesses_all(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    corpus_index.build([str(corpus)], str(store), embedder=_FakeEmbedder())
    # No changes, but rebuild=True ignores the manifest and reprocesses everything.
    log = corpus_index.build(
        [str(corpus)], str(store), embedder=_FakeEmbedder(), rebuild=True
    )
    assert log["files_processed"] >= 5


def test_build_rebuild_has_no_duplicate_chunk_ids(tmp_path):
    """A --rebuild re-embeds every file; upsert must overwrite by id, not duplicate.

    This is a direct check that the build uses id-deduping (upsert) rather than add():
    after a build + rebuild over an unchanged corpus, every chunk_id in the collection
    must appear exactly once.
    """
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _build_index_corpus(corpus)
    store = tmp_path / "store"

    corpus_index.build([str(corpus)], str(store), embedder=_FakeEmbedder())
    coll = _open_corpus_collection(store)
    count_after_first = coll.count()

    # Rebuild over the same (unchanged) corpus re-embeds everything by the same ids.
    corpus_index.build(
        [str(corpus)], str(store), embedder=_FakeEmbedder(), rebuild=True
    )

    coll = _open_corpus_collection(store)
    ids = coll.get(include=[])["ids"]
    assert len(ids) == len(set(ids)), "rebuild produced duplicate chunk_ids"
    # And the count is unchanged: upsert overwrote in place rather than appending.
    assert coll.count() == count_after_first
