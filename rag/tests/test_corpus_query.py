"""Tests for the ``search_all`` core of the corpus query layer (Task 5.1).

CRITICAL test-safety: every test seeds its OWN temp ``bios667_corpus`` collection
under ``tmp_path`` with a tiny deterministic FAKE embedder. NO test touches the real
``rag/data/chroma`` store or downloads a model. The query layer must work against a
fresh seeded collection.

The single most important correctness property exercised here is EXACT int-membership
chapter filtering: a record whose ``chapters`` serialize to ``"1,10,11"`` must match
``chapter=1`` while a record whose ``chapters`` are ``[10]`` must NOT (no substring
false-match of "1" inside "10").
"""

import hashlib

import chromadb
from chromadb.config import Settings

from bios667_rag.corpus_query import CorpusQuery
from bios667_rag.metadata import ChunkMeta
from bios667_rag.storage import KnowledgeStore


class _FakeEmbedder:
    """Deterministic stand-in for ``Embedder``: fixed 4-dim vector seeded from text.

    Identical text -> identical vector. Mirrors the fake used in test_corpus_index so
    seeding records and embedding the query use the same vector space.
    """

    def __init__(self):
        self.calls = []

    def _vec(self, text: str) -> list[float]:
        h = hashlib.sha1(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h[:4]]

    def embed(self, texts):
        self.calls.append(list(texts))
        return [self._vec(t) for t in texts]

    def embed_single(self, text: str) -> list[float]:
        return self.embed([text])[0]


# Six seed records with known source_types / chapters. Each ``text`` is distinct so the
# fake embedder gives each a distinct vector.
_SEEDS = [
    # (chunk_id, source_type, source_path, title, chapters, text)
    ("c_lec8", "lecture", "lectures/BIOS667_L08.qmd", "Lecture 8 LME", [8],
     "Lecture 8 covers linear mixed effects models and random intercepts."),
    ("c_tb8", "textbook", "book/flw_ch8.md", "FLW Ch8", [8],
     "Textbook chapter 8 develops the linear mixed effects model."),
    ("c_tb10", "textbook", "book/flw_ch10.md", "FLW Ch10", [10],
     "Textbook chapter 10 covers residual analyses and diagnostics."),
    ("c_tb1_10_11", "textbook", "book/flw_ch1_10_11.md", "FLW Ch1/10/11", [1, 10, 11],
     "Textbook spanning chapters 1, 10 and 11 on longitudinal data overview."),
    ("c_sas", "sas", "analysis.sas", "SAS analysis", [],
     "SAS proc mixed code with random slopes for the dental data."),
    ("c_hw8", "hw", "homework/HW3.qmd", "Homework 3", [8],
     "Homework 3 problem about fitting a random intercept model."),
    ("c_rcode", "rcode", "code/random_slopes.R", "R random slopes", [8],
     "R lmer code fitting a random slopes model to longitudinal data."),
    ("c_dcard_dental", "data_card", "data/dental.txt", "Dental data card", [],
     "Data card for the dental growth dataset with distance over age."),
    ("c_dcard_six", "data_card", "data/sixcities.txt", "Six Cities data card", [],
     "Data card for the six cities respiratory dataset on smoking and FEV."),
]


def _seed_collection(store_dir, embedder):
    """Seed a temp ``bios667_corpus`` collection from ``_SEEDS`` and return store_dir."""
    client = chromadb.PersistentClient(
        path=str(store_dir / "chroma"),
        settings=Settings(anonymized_telemetry=False),
    )
    coll = client.get_or_create_collection(
        name="bios667_corpus", metadata={"hnsw:space": "cosine"}
    )
    ids, embeddings, documents, metadatas = [], [], [], []
    for chunk_id, src_type, src_path, title, chapters, text in _SEEDS:
        meta = ChunkMeta(
            chunk_id=chunk_id,
            source_type=src_type,
            source_path=src_path,
            title=title,
            chapters=chapters,
            topic_tags=[],
            year=2026,
            dataset_refs=[],
            is_solution=False,
            chunk_type="prose",
        )
        ids.append(chunk_id)
        embeddings.append(embedder.embed_single(text))
        documents.append(text)
        metadatas.append(meta.to_chroma())
    coll.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return store_dir


def _make_query(tmp_path):
    fake = _FakeEmbedder()
    store_dir = _seed_collection(tmp_path / "store", fake)
    return CorpusQuery(store_dir=store_dir, embedder=fake), fake


def _seed_graph(tmp_path):
    """Seed a temp knowledge graph with a dataset node + a ``uses`` edge.

    Mirrors the real graph: a ``material --uses--> dataset`` edge. The dataset node
    id is ``dataset_<stem>`` (the data_card filename stem, lowercased), matching how
    ``corpus_index.build`` registers dataset nodes. ``dental`` gets one material that
    uses it (``analysis.sas``); ``sixcities`` is left with NO edges so ``used_by`` is [].
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    graph_db = tmp_path / "graph.db"
    store = KnowledgeStore(db_path=graph_db, chromadb_path=tmp_path / "graph_chroma")
    store.add_node(node_id="dataset_dental", node_type="dataset", name="dental")
    store.add_node(node_id="dataset_sixcities", node_type="dataset", name="sixcities")
    store.add_node(node_id="material_sas", node_type="material", name="analysis.sas")
    store.add_edge("material_sas", "dataset_dental", "uses")
    return store, graph_db


def _make_query_with_graph(tmp_path):
    fake = _FakeEmbedder()
    store_dir = _seed_collection(tmp_path / "store", fake)
    store, graph_db = _seed_graph(tmp_path / "graphstore")
    cq = CorpusQuery(store_dir=store_dir, embedder=fake, graph=store)
    return cq, store


def test_chapter_filter_exact_int_membership(tmp_path):
    """chapter=1 returns ONLY the [1,10,11] record; never the [10]-only record.

    This is the critical no-substring-false-match test.
    """
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("longitudinal data", chapter=1, top_k=8)

    paths = {r["source_path"] for r in results}
    assert "book/flw_ch1_10_11.md" in paths, "the [1,10,11] record must match chapter=1"
    assert "book/flw_ch10.md" not in paths, "the [10] record must NOT match chapter=1"
    # Every returned record must genuinely contain chapter 1.
    for r in results:
        assert 1 in r["chapters"], f"record {r['source_path']} lacks chapter 1"


def test_chapter_filter_ten_matches_both_ten_records(tmp_path):
    """chapter=10 matches both the [10] record and the [1,10,11] record."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("diagnostics", chapter=10, top_k=8)
    paths = {r["source_path"] for r in results}
    assert "book/flw_ch10.md" in paths
    assert "book/flw_ch1_10_11.md" in paths
    for r in results:
        assert 10 in r["chapters"]


def test_source_type_single_filter(tmp_path):
    """source_type='textbook' returns only textbook records (scalar $eq path)."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("model", source_type="textbook", top_k=8)
    assert results, "expected some textbook records"
    assert all(r["source_type"] == "textbook" for r in results)
    # All three textbook records present.
    paths = {r["source_path"] for r in results}
    assert paths == {"book/flw_ch8.md", "book/flw_ch10.md", "book/flw_ch1_10_11.md"}


def test_source_type_list_in_filter(tmp_path):
    """source_type=['lecture','hw'] returns lecture+hw records (the $in path)."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("model", source_type=["lecture", "hw"], top_k=8)
    assert results
    types = {r["source_type"] for r in results}
    assert types == {"lecture", "hw"}
    paths = {r["source_path"] for r in results}
    assert paths == {"lectures/BIOS667_L08.qmd", "homework/HW3.qmd"}


def test_top_k_truncates(tmp_path):
    """top_k caps the number of returned results."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("model", top_k=2)
    assert len(results) <= 2


def test_result_dict_has_full_provenance(tmp_path):
    """Each result dict exposes the documented keys with correct provenance."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("model", source_type="lecture", top_k=8)
    assert len(results) == 1
    r = results[0]
    expected_keys = {"text", "source_path", "source_type", "title", "chapters", "score"}
    assert expected_keys <= set(r.keys())
    assert r["source_path"] == "lectures/BIOS667_L08.qmd"
    assert r["source_type"] == "lecture"
    assert r["title"] == "Lecture 8 LME"
    assert r["chapters"] == [8]
    assert isinstance(r["text"], str) and r["text"]
    assert isinstance(r["score"], (int, float))


def test_combined_source_type_and_chapter(tmp_path):
    """source_type + chapter compose: textbook AND chapter 1 -> only [1,10,11]."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("data", source_type="textbook", chapter=1, top_k=8)
    paths = {r["source_path"] for r in results}
    assert paths == {"book/flw_ch1_10_11.md"}


def test_no_filters_returns_records(tmp_path):
    """With no filters, search returns records across source types."""
    cq, _ = _make_query(tmp_path)
    results = cq.search_all("model", top_k=8)
    assert results
    assert len(results) <= 8


# -- find_examples (Task 5.2) ---------------------------------------------------


def test_find_examples_explicit_material_types(tmp_path):
    """find_examples with material_types=['sas','rcode'] returns ONLY sas/rcode."""
    cq, _ = _make_query(tmp_path)
    results = cq.find_examples("random slopes", material_types=["sas", "rcode"])
    assert results, "expected sas/rcode example records"
    types = {r["source_type"] for r in results}
    assert types <= {"sas", "rcode"}
    paths = {r["source_path"] for r in results}
    assert paths == {"analysis.sas", "code/random_slopes.R"}


def test_find_examples_default_types_exclude_lectures_and_textbook(tmp_path):
    """Default material_types must exclude lecture and textbook records."""
    cq, _ = _make_query(tmp_path)
    results = cq.find_examples("model", top_k=8)
    assert results
    types = {r["source_type"] for r in results}
    assert "lecture" not in types
    assert "textbook" not in types
    # Default set is hw/hw_solution/sas/rcode/handout.
    assert types <= {"hw", "hw_solution", "sas", "rcode", "handout"}
    paths = {r["source_path"] for r in results}
    assert "lectures/BIOS667_L08.qmd" not in paths
    assert "book/flw_ch8.md" not in paths


def test_find_examples_results_carry_source_path(tmp_path):
    """Each example carries source_path so the user can open & adapt it."""
    cq, _ = _make_query(tmp_path)
    results = cq.find_examples("random intercept", material_types=["hw"])
    assert results
    for r in results:
        assert r["source_path"]


# -- find_datasets (Task 5.2) ---------------------------------------------------


def test_find_datasets_walks_uses_edge(tmp_path):
    """find_datasets('dental') returns the dental card with analysis.sas in used_by."""
    cq, _ = _make_query_with_graph(tmp_path)
    results = cq.find_datasets("dental", top_k=8)
    assert results, "expected the dental data_card"
    by_path = {r["dataset_card"]["source_path"]: r for r in results}
    assert "data/dental.txt" in by_path
    dental = by_path["data/dental.txt"]
    assert "analysis.sas" in dental["used_by"]


def test_find_datasets_no_edges_yields_empty_used_by(tmp_path):
    """A dataset with no uses edges returns used_by == []."""
    cq, _ = _make_query_with_graph(tmp_path)
    results = cq.find_datasets("six cities respiratory", top_k=8)
    by_path = {r["dataset_card"]["source_path"]: r for r in results}
    assert "data/sixcities.txt" in by_path
    assert by_path["data/sixcities.txt"]["used_by"] == []


def test_find_datasets_only_returns_data_cards(tmp_path):
    """find_datasets restricts to data_card source_type."""
    cq, _ = _make_query_with_graph(tmp_path)
    results = cq.find_datasets("data", top_k=8)
    assert results
    for r in results:
        assert r["dataset_card"]["source_type"] == "data_card"
        assert "used_by" in r and isinstance(r["used_by"], list)


def test_find_datasets_accepts_graph_db_path(tmp_path):
    """An injectable graph_db_path opens the graph lazily for the call."""
    fake = _FakeEmbedder()
    store_dir = _seed_collection(tmp_path / "store", fake)
    _store, graph_db = _seed_graph(tmp_path / "graphstore")
    cq = CorpusQuery(store_dir=store_dir, embedder=fake)
    results = cq.find_datasets("dental", top_k=8, graph_db_path=graph_db)
    by_path = {r["dataset_card"]["source_path"]: r for r in results}
    assert "analysis.sas" in by_path["data/dental.txt"]["used_by"]


# -- check_lecture_sync (Task 5.3) ----------------------------------------------
#
# These tests use a KEYED embedder so cosine distances between specific texts are
# controllable. Vectors are chosen on the unit circle (2-D) so cosine distance is
# 1 - cos(angle): identical texts -> distance 0; orthogonal -> distance 1.


class _KeyedEmbedder:
    """Deterministic embedder mapping known texts to fixed unit vectors.

    Unknown texts fall back to a sha1-seeded vector (still deterministic). The
    explicit ``_KEYS`` let a test place a textbook concept and a lecture chunk at a
    chosen cosine distance (e.g. identical -> 0, near -> small, far -> ~1).
    """

    # angle in radians for each keyed text; vector = (cos, sin).
    _ANGLES = {
        # ch8 concepts and the lecture chunk that covers ONLY random intercepts.
        "TB random intercepts": 0.0,
        "LEC random intercepts": 0.02,        # near-identical -> tiny distance
        "TB random slopes": 1.4,              # far from the lecture chunk -> a GAP
        # topic-string / generic lecture-prose vectors
        "LEC linear mixed effects": 0.05,
        "TB linear mixed effects concept": 0.06,
        # path-resolution lecture file content + its ch5 textbook concept
        "LEC ch5 response profiles": 0.10,
        "TB ch5 response profiles": 0.11,
        # ch18 (caveat) textbook + lecture
        "TB transition models": 0.30,
        "LEC transition models": 0.31,
    }

    def __init__(self):
        self.calls = []

    def _vec(self, text):
        import math

        if text in self._ANGLES:
            a = self._ANGLES[text]
            return [math.cos(a), math.sin(a)]
        h = hashlib.sha1(text.encode("utf-8")).digest()
        # map to a far-away angle so unknown texts don't accidentally cover concepts.
        a = 2.5 + (h[0] / 255.0)
        return [math.cos(a), math.sin(a)]

    def embed(self, texts):
        self.calls.append(list(texts))
        return [self._vec(t) for t in texts]

    def embed_single(self, text):
        return self.embed([text])[0]


_SYNC_SEEDS = [
    # (chunk_id, source_type, source_path, title, chapters, text)
    # -- chapter 8: 2 textbook concepts, lecture covers ONLY random intercepts --
    ("s_tb8_ri", "textbook", "book/flw_ch8_ri.md", "FLW Ch8 RI", [8],
     "TB random intercepts"),
    ("s_tb8_rs", "textbook", "book/flw_ch8_rs.md", "FLW Ch8 RS", [8],
     "TB random slopes"),
    ("s_lec8_ri", "lecture", "lectures/BIOS667_L08_LME.qmd", "L08 LME", [8],
     "LEC random intercepts"),
    # -- a ch8 lecture chunk + textbook concept for topic-string resolution --
    ("s_lec8_lme", "lecture", "lectures/BIOS667_L08_LME.qmd", "L08 LME", [8],
     "LEC linear mixed effects"),
    ("s_tb8_lme", "textbook", "book/flw_ch8_lme.md", "FLW Ch8 LME", [8],
     "TB linear mixed effects concept"),
    # -- chapter 18 (>=17 caveat band) --
    ("s_tb18", "textbook", "book/flw_ch18.md", "FLW Ch18", [18],
     "TB transition models"),
    ("s_lec18", "lecture", "lectures/BIOS667_L18_Transition.qmd", "L18", [18],
     "LEC transition models"),
]


def _seed_sync_collection(store_dir, embedder, extra_seeds=()):
    client = chromadb.PersistentClient(
        path=str(store_dir / "chroma"),
        settings=Settings(anonymized_telemetry=False),
    )
    coll = client.get_or_create_collection(
        name="bios667_corpus", metadata={"hnsw:space": "cosine"}
    )
    ids, embeddings, documents, metadatas = [], [], [], []
    for chunk_id, src_type, src_path, title, chapters, text in (
        list(_SYNC_SEEDS) + list(extra_seeds)
    ):
        meta = ChunkMeta(
            chunk_id=chunk_id,
            source_type=src_type,
            source_path=src_path,
            title=title,
            chapters=chapters,
            topic_tags=[],
            year=2026,
            dataset_refs=[],
            is_solution=False,
            chunk_type="prose",
        )
        ids.append(chunk_id)
        embeddings.append(embedder.embed_single(text))
        documents.append(text)
        metadatas.append(meta.to_chroma())
    coll.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return store_dir


def _make_sync_query(tmp_path, extra_seeds=()):
    emb = _KeyedEmbedder()
    store_dir = _seed_sync_collection(tmp_path / "store", emb, extra_seeds)
    return CorpusQuery(store_dir=store_dir, embedder=emb), emb


def test_check_lecture_sync_int_detects_gap(tmp_path):
    """check_lecture_sync(8): random-intercepts covered, random-slopes is a gap."""
    cq, _ = _make_sync_query(tmp_path)
    report = cq.check_lecture_sync(8)

    assert report["chapters"] == [8]
    covered_paths = {c["textbook"]["source_path"] for c in report["covered"]}
    gap_paths = {g["textbook"]["source_path"] for g in report["gaps"]}

    assert "book/flw_ch8_ri.md" in covered_paths, "random intercepts should be covered"
    assert "book/flw_ch8_rs.md" in gap_paths, "random slopes should be a gap"

    # Covered entries carry their matched lecture chunk + a distance + citations.
    ri = next(c for c in report["covered"]
              if c["textbook"]["source_path"] == "book/flw_ch8_ri.md")
    assert "lecture" in ri and ri["lecture"]["source_path"]
    assert isinstance(ri["distance"], (int, float))
    assert ri["textbook"]["text"]  # citation snippet present

    # Gap entries carry the textbook concept + a best distance + citation.
    rs = next(g for g in report["gaps"]
              if g["textbook"]["source_path"] == "book/flw_ch8_rs.md")
    assert rs["textbook"]["text"]
    assert isinstance(rs["distance"], (int, float))

    assert report["n_textbook_concepts"] >= 2
    assert report["n_lecture_chunks"] >= 1


def test_check_lecture_sync_topic_string_resolves_chapters(tmp_path):
    """A topic string resolves chapters via lecture hits and returns the report keys."""
    cq, _ = _make_sync_query(tmp_path)
    report = cq.check_lecture_sync("linear mixed effects")
    expected_keys = {
        "lecture", "chapters", "n_textbook_concepts", "n_lecture_chunks",
        "covered", "gaps", "possible_mismatches", "caveat",
    }
    assert expected_keys <= set(report.keys())
    assert 8 in report["chapters"]


def test_check_lecture_sync_path_resolution(tmp_path):
    """A .qmd path resolves chapters from the file and uses that file's chunks."""
    # Write a temp lecture file whose front matter declares chapter 5.
    lec = tmp_path / "BIOS667_L05_ResponseProfiles_ch5.qmd"
    lec.write_text(
        "---\ntitle: Response Profiles\nchapter: 5\n---\n\n"
        "LEC ch5 response profiles\n",
        encoding="utf-8",
    )
    extra = [
        ("s_lec5", "lecture", str(lec), "L05", [5], "LEC ch5 response profiles"),
        ("s_tb5", "textbook", "book/flw_ch5.md", "FLW Ch5", [5],
         "TB ch5 response profiles"),
    ]
    cq, _ = _make_sync_query(tmp_path, extra_seeds=extra)
    report = cq.check_lecture_sync(str(lec))

    assert 5 in report["chapters"]
    # The ch5 textbook concept should be covered by the file's own chunk.
    covered_paths = {c["textbook"]["source_path"] for c in report["covered"]}
    assert "book/flw_ch5.md" in covered_paths
    # The matched lecture chunk must come from the resolved file.
    c5 = next(c for c in report["covered"]
              if c["textbook"]["source_path"] == "book/flw_ch5.md")
    assert c5["lecture"]["source_path"] == str(lec)


def test_check_lecture_sync_ch17plus_caveat(tmp_path):
    """check_lecture_sync(18) includes the course/FLW divergence caveat."""
    cq, _ = _make_sync_query(tmp_path)
    report = cq.check_lecture_sync(18)
    assert report["caveat"], "ch>=17 must carry a divergence caveat"
    assert "diverge" in report["caveat"].lower() or "17" in report["caveat"]


def test_check_lecture_sync_ch16_has_no_caveat(tmp_path):
    """Chapters <=16 are reliable: caveat is falsy (None or empty)."""
    cq, _ = _make_sync_query(tmp_path)
    report = cq.check_lecture_sync(8)
    assert not report["caveat"]
