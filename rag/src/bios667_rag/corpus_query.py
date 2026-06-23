"""Query layer for the course corpus (Task 5.1): ``CorpusQuery.search_all``.

The corpus is a ChromaDB ``bios667_corpus`` collection whose per-record metadata is in
:meth:`ChunkMeta.to_chroma` form -- in particular ``chapters`` is a comma-joined string
(e.g. ``"8"`` or ``"1,10,11"``).

Chapter filtering MUST be exact int-membership, NOT a substring/native ``where`` match:
a chroma ``$eq``/substring on the stored string ``"1,10,11"`` would let ``chapter=1``
falsely match ``"10"``/``"11"``. So this layer applies the cheap scalar filters
(``source_type``, ``year``) natively via chroma ``where`` (over-fetching), then parses
each candidate's ``chapters`` with :meth:`ChunkMeta.from_chroma` and keeps only records
where ``chapter in chapters`` before truncating to ``top_k``.
"""

import math
from pathlib import Path
from typing import Optional, Union

import chromadb
from chromadb.config import Settings

from .metadata import ChunkMeta

_COLLECTION_NAME = "bios667_corpus"

# Course lecture ``_chN_`` numbering aligns with FLW textbook chapters for ch1-16, but
# DIVERGES for ch17+: the course resequenced late topics (L18=Transition models,
# L19=Advanced Missing data) whereas FLW ch18 is Missing-Data/Multiple-Imputation and
# ch19 is Smoothing/Semiparametric. So sync results are reliable only for ch1-16; for
# any chapter >=17 we attach this caveat to the report. (Task 5.3 known limitation.)
_CH_DIVERGENCE_THRESHOLD = 17
_CH_DIVERGENCE_CAVEAT = (
    "Course lecture _chN_ numbering aligns with FLW textbook chapters for ch1-16 but "
    "DIVERGES for ch17+: the course resequenced late topics (L18=Transition models, "
    "L19=Advanced Missing data) vs FLW ch18=Missing-Data/Multiple-Imputation and "
    "ch19=Smoothing/Semiparametric. Sync results for chapters >=17 may be unreliable."
)

# How many candidate records to over-fetch from chroma when pulling lecture/textbook
# chunks by (source_type, chapter) for the sync report. Same rationale as ``search_all``:
# the exact int-membership chapter filter happens in Python after the native filter.
_SYNC_FETCH_CAP = 2000

# The knowledge graph lives at ``store_dir/"graph.db"`` (matching ``corpus_index.build``),
# with its vector sidecar under ``store_dir/"chroma"``.
_GRAPH_DB_NAME = "graph.db"
_GRAPH_CHROMA_SUBDIR = "chroma"

# Materials a user might open and adapt: problem/code units, not lecture/textbook prose.
_DEFAULT_EXAMPLE_TYPES = ["hw", "hw_solution", "sas", "rcode", "handout"]

# How many candidates to pull from chroma before the in-Python chapter filter. We
# over-fetch so the chapter filter (which chroma cannot do exactly) still leaves enough
# rows to satisfy ``top_k``.
def _overfetch(top_k: int) -> int:
    return max(top_k * 10, 100)


class CorpusQuery:
    """Search the ``bios667_corpus`` ChromaDB collection with provenance-rich results.

    ``embedder`` is injectable (any object with ``embed_single(str) -> list[float]``,
    or ``embed(list[str]) -> list[list[float]]``) so tests can pass a deterministic fake
    and avoid a model download. If omitted, a real :class:`Embedder` is constructed
    lazily on first use.

    ``store_dir`` is the store directory; the chroma persistent client opens at
    ``store_dir/"chroma"`` (matching how the corpus is built/indexed). ``client`` may be
    passed directly to point at an already-open client (tests/smoke checks).
    """

    def __init__(
        self,
        store_dir: Optional[Union[str, Path]] = None,
        embedder=None,
        client=None,
        graph=None,
        graph_db_path: Optional[Union[str, Path]] = None,
    ):
        self._embedder = embedder
        self._store_dir = Path(store_dir) if store_dir is not None else None
        # Graph store used by ``find_datasets`` to walk ``material --uses--> dataset``
        # edges. May be injected directly (``graph``), opened lazily from an explicit
        # ``graph_db_path``, or (default) opened from ``store_dir/"graph.db"``.
        self._graph = graph
        self._graph_db_path = Path(graph_db_path) if graph_db_path is not None else None
        if client is not None:
            self._client = client
        elif store_dir is not None:
            # Resolve the chroma persist dir robustly so BOTH the store dir
            # (".../data", which contains chroma/) and the chroma dir itself
            # (".../data/chroma", which contains chroma.sqlite3) work. Passing the
            # chroma dir used to silently open an empty auto-created collection at
            # ".../data/chroma/chroma" and return no results; this prevents that.
            sd = Path(store_dir)
            if (sd / "chroma.sqlite3").exists():
                chroma_path = sd                # sd IS the chroma persist dir
            elif (sd / "chroma" / "chroma.sqlite3").exists():
                chroma_path = sd / "chroma"     # sd is the store dir
            else:
                chroma_path = sd / "chroma"  # fresh store: build will create it here
            self._client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            raise ValueError("CorpusQuery requires either store_dir or client")
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    # -- embedder ---------------------------------------------------------------

    def _embed_query(self, query: str) -> list[float]:
        if self._embedder is None:
            from .embed import Embedder

            self._embedder = Embedder()
        emb = self._embedder
        if hasattr(emb, "embed_single"):
            return emb.embed_single(query)
        return emb.embed([query])[0]

    # -- where filter -----------------------------------------------------------

    @staticmethod
    def _build_where(
        source_type: Optional[Union[str, list[str]]],
        year: Optional[int],
    ) -> Optional[dict]:
        """Build a native chroma ``where`` for the scalar-comparable filters.

        ``source_type`` is a scalar ``$eq`` for a single value, or ``$in`` for a list.
        ``year`` is a scalar ``$eq`` (only non-``None`` years are filtered here).
        ``chapter`` is deliberately NOT included -- it is filtered in Python for exact
        int-membership. Multiple clauses are combined under ``$and``.
        """
        clauses: list[dict] = []
        if source_type is not None:
            if isinstance(source_type, (list, tuple, set)):
                clauses.append({"source_type": {"$in": list(source_type)}})
            else:
                clauses.append({"source_type": {"$eq": source_type}})
        if year is not None:
            clauses.append({"year": {"$eq": year}})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    # -- search -----------------------------------------------------------------

    def search_all(
        self,
        query: str,
        source_type: Optional[Union[str, list[str]]] = None,
        chapter: Optional[int] = None,
        year: Optional[int] = None,
        top_k: int = 8,
    ) -> list[dict]:
        """Semantic search over the corpus with optional metadata filters.

        Returns up to ``top_k`` dicts ordered best-first (lowest chroma distance), each:
        ``{text, source_path, source_type, title, chapters, score, distance}`` where
        ``score`` is a similarity ``1 - distance`` (higher is better; the raw
        ``distance`` is also included for transparency).

        ``source_type`` and ``year`` are applied as native chroma ``where`` filters
        (``source_type`` accepts a single value -> ``$eq`` or a list -> ``$in``).
        ``chapter`` is applied in Python as exact int-membership over the parsed
        ``chapters`` list (no substring false-match).
        """
        query_embedding = self._embed_query(query)
        where = self._build_where(source_type, year)

        # Clamp the over-fetch to the collection size: chroma raises if
        # ``n_results`` exceeds the number of stored records on some versions.
        n_results = min(_overfetch(top_k), self._collection.count())
        if n_results == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        out: list[dict] = []
        ids = results.get("ids") or [[]]
        if not ids or not ids[0]:
            return out

        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        distances = results["distances"][0]

        for i in range(len(ids[0])):
            meta_raw = metadatas[i]
            meta = ChunkMeta.from_chroma(meta_raw)

            # Exact int-membership chapter filter (NOT substring): keep only records
            # whose parsed chapters list contains the requested chapter.
            if chapter is not None and chapter not in meta.chapters:
                continue

            distance = distances[i]
            out.append({
                "text": documents[i],
                "source_path": meta.source_path,
                "source_type": meta.source_type,
                "title": meta.title,
                "chapters": meta.chapters,
                "score": 1 - distance,
                "distance": distance,
            })
            if len(out) >= top_k:
                break

        return out

    # -- find_examples ----------------------------------------------------------

    def find_examples(
        self,
        topic: str,
        material_types: Optional[list[str]] = None,
        top_k: int = 8,
    ) -> list[dict]:
        """Find adaptable example materials (homework/code/handouts) on ``topic``.

        A thin wrapper over :meth:`search_all` restricted to material source types --
        by default ``hw``, ``hw_solution``, ``sas``, ``rcode``, ``handout`` -- so it
        returns whole problem/code units the user can open and adapt, NOT lecture or
        textbook prose. Each result is a ``search_all`` dict (so it carries
        ``source_path`` for opening the file).
        """
        if material_types is None:
            material_types = list(_DEFAULT_EXAMPLE_TYPES)
        return self.search_all(topic, source_type=material_types, top_k=top_k)

    # -- find_datasets ----------------------------------------------------------

    def _resolve_graph(self, graph=None, graph_db_path=None):
        """Resolve the graph store to use, preferring (in order) the call-level
        ``graph``/``graph_db_path`` overrides, then the instance graph, then a lazily
        opened store from the instance ``graph_db_path`` / ``store_dir/"graph.db"``.
        Returns ``None`` if no graph location is available.
        """
        if graph is not None:
            return graph
        if graph_db_path is not None:
            return self._open_graph(Path(graph_db_path))
        if self._graph is not None:
            return self._graph
        if self._graph_db_path is not None:
            return self._open_graph(self._graph_db_path)
        if self._store_dir is not None:
            db = self._store_dir / _GRAPH_DB_NAME
            if db.exists():
                return self._open_graph(db)
        return None

    @staticmethod
    def _open_graph(db_path: Path):
        from .storage import KnowledgeStore

        return KnowledgeStore(
            db_path=db_path,
            chromadb_path=db_path.parent / _GRAPH_CHROMA_SUBDIR,
        )

    def find_datasets(
        self,
        query: str,
        top_k: int = 8,
        graph=None,
        graph_db_path: Optional[Union[str, Path]] = None,
    ) -> list[dict]:
        """Find dataset cards matching ``query`` and the materials that USE each one.

        Searches ``data_card`` records via :meth:`search_all`, then for each card walks
        the knowledge graph's ``material --uses--> dataset`` edges to list the materials
        that use that dataset. The dataset node id is ``dataset_<stem>`` where ``stem``
        is the data_card filename stem, lowercased (matching ``corpus_index.build``).

        Returns a list of ``{"dataset_card": <search_all dict>, "used_by": [<paths>]}``.
        ``used_by`` is each related material node's ``name`` (its source path), or ``[]``
        when the dataset has no ``uses`` edges (or no graph is available).
        """
        cards = self.search_all(query, source_type="data_card", top_k=top_k)
        graph_store = self._resolve_graph(graph=graph, graph_db_path=graph_db_path)

        out: list[dict] = []
        for card in cards:
            used_by: list[str] = []
            if graph_store is not None:
                stem = Path(card["source_path"]).stem.lower()
                dataset_id = f"dataset_{stem}"
                related = graph_store.get_related(dataset_id, relationship="uses")
                seen: set[str] = set()
                for node in related:
                    # ``get_related`` LEFT-JOINs nodes; the dataset's own row may appear
                    # with a NULL node (self side). Keep only material nodes.
                    if not node or node.get("id") is None:
                        continue
                    if node.get("type") != "material":
                        continue
                    label = node.get("name") or node["id"]
                    if label not in seen:
                        seen.add(label)
                        used_by.append(label)
            out.append({"dataset_card": card, "used_by": used_by})
        return out

    # -- check_lecture_sync (Task 5.3) ------------------------------------------

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        """Cosine distance ``1 - cos(a, b)`` matching chroma's ``hnsw:space=cosine``.

        Returns ``1.0`` for a degenerate (zero-norm) vector so it never spuriously
        "covers" a concept.
        """
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return 1.0
        return 1.0 - dot / (na * nb)

    def _get_by(self, where: dict) -> list[dict]:
        """Fetch records via ``collection.get`` (embeddings + docs + metadata).

        Returns a list of per-record dicts ``{id, embedding, document, meta}`` where
        ``meta`` is a parsed :class:`ChunkMeta`. ``embedding`` may be ``None`` if the
        record has no stored embedding.
        """
        got = self._collection.get(
            where=where,
            include=["embeddings", "documents", "metadatas"],
            limit=_SYNC_FETCH_CAP,
        )
        ids = got.get("ids") or []
        embeddings = got.get("embeddings")
        documents = got.get("documents") or []
        metadatas = got.get("metadatas") or []
        out: list[dict] = []
        for i in range(len(ids)):
            emb = None
            # chroma may return embeddings as a numpy array; index defensively.
            if embeddings is not None and len(embeddings) > i and embeddings[i] is not None:
                emb = list(embeddings[i])
            out.append({
                "id": ids[i],
                "embedding": emb,
                "document": documents[i] if i < len(documents) else "",
                "meta": ChunkMeta.from_chroma(metadatas[i]),
            })
        return out

    def _records_for_chapters(self, source_type: str, chapters: list[int]) -> list[dict]:
        """All ``source_type`` records whose parsed chapters intersect ``chapters``.

        Native chroma ``where`` filters on ``source_type`` (cheap scalar); the exact
        int-membership chapter test is done in Python (no substring false-match, as in
        ``search_all``).
        """
        chap_set = set(chapters)
        recs = self._get_by({"source_type": {"$eq": source_type}})
        return [r for r in recs if chap_set & set(r["meta"].chapters)]

    def _ensure_embedding(self, rec: dict) -> list[float]:
        """Return a record's stored embedding, or embed its text on the fly."""
        if rec["embedding"] is not None:
            return rec["embedding"]
        return self._embed_query(rec["document"] or "")

    @staticmethod
    def _cite(rec: dict) -> dict:
        """A compact citation: source_path + a text snippet (first ~300 chars)."""
        text = rec["document"] or ""
        snippet = text if len(text) <= 300 else text[:300] + "..."
        meta = rec["meta"]
        return {
            "source_path": meta.source_path,
            "title": meta.title,
            "chapters": meta.chapters,
            "text": snippet,
        }

    def check_lecture_sync(
        self,
        lecture: Union[int, str],
        distance_threshold: float = 0.6,
        mismatch_threshold: float = 0.45,
    ) -> dict:
        """Surface candidate textbook-coverage GAPS for a lecture -- it does NOT judge.

        For each FLW textbook chunk ("concept") in the resolved chapter(s), this finds
        the NEAREST lecture chunk by cosine distance and bins it:

        * ``covered`` -- nearest distance ``<= distance_threshold``. The concept appears
          to be addressed by some lecture chunk (recorded with its match + distance).
        * ``possible_mismatches`` -- a SUBSET of covered whose nearest distance falls in
          the loose band ``(mismatch_threshold, distance_threshold]``: close enough to
          count as covered, but loosely enough to flag for a human to eyeball. These are
          ALSO included in ``covered`` (the band is advisory, not a third exclusive bin).
        * ``gaps`` -- nearest distance ``> distance_threshold`` (or there are no lecture
          chunks at all). The textbook concept has no close lecture match.

        IMPORTANT: this tool SURFACES candidates for human review; it does NOT
        auto-judge correctness. A "gap" means "no lecture chunk is semantically near
        this textbook chunk", which is a prompt to look, not a verdict that the topic is
        missing (paraphrase, different emphasis, or chunk granularity can all lower
        similarity). Likewise "covered" is a similarity signal, not a proof of fidelity.

        ``lecture`` is resolved in this order:
        1. ``int`` -> ``chapters=[lecture]``; lecture_chunks = all ``lecture`` records
           whose chapters contain it.
        2. path-like (``.qmd``/``.rmd`` that exists) -> ``load`` the file, classify +
           ``map_chapters`` for the chapters; lecture_chunks = collection records whose
           stored ``source_path`` matches the file (exact, else by basename).
        3. else (topic string) -> ``search_all(lecture, source_type="lecture")``;
           chapters = union of the hits' chapters; lecture_chunks = those hits.

        Distances are computed from STORED embeddings where available (fetched via
        ``collection.get(include=["embeddings", ...])``); a chunk lacking a stored
        embedding is embedded on the fly via the injected Embedder.

        Returns ``{lecture, chapters, n_textbook_concepts, n_lecture_chunks, covered,
        gaps, possible_mismatches, caveat}``. ``caveat`` is the course/FLW ch17+
        divergence note when any resolved chapter is >=17, else ``None``. Each
        covered/gap entry carries citations (``source_path`` + text snippet).
        """
        chapters, lecture_recs, resolved_descr = self._resolve_lecture(lecture)

        # Textbook "concepts" = textbook chunks in these chapters.
        textbook_recs = self._records_for_chapters("textbook", chapters)

        # Embeddings for the lecture chunks (stored, else embedded on the fly).
        lecture_embs = [(r, self._ensure_embedding(r)) for r in lecture_recs]

        covered: list[dict] = []
        gaps: list[dict] = []
        possible_mismatches: list[dict] = []

        for tb in textbook_recs:
            tb_emb = self._ensure_embedding(tb)
            best_rec = None
            best_dist = None
            for lec_rec, lec_emb in lecture_embs:
                d = self._cosine_distance(tb_emb, lec_emb)
                if best_dist is None or d < best_dist:
                    best_dist = d
                    best_rec = lec_rec

            if best_dist is not None and best_dist <= distance_threshold:
                entry = {
                    "textbook": self._cite(tb),
                    "lecture": self._cite(best_rec),
                    "distance": best_dist,
                }
                covered.append(entry)
                if best_dist > mismatch_threshold:
                    possible_mismatches.append(entry)
            else:
                # No lecture chunks at all -> best_dist is None -> a gap with distance 1.
                gaps.append({
                    "textbook": self._cite(tb),
                    "distance": best_dist if best_dist is not None else 1.0,
                })

        caveat = (
            _CH_DIVERGENCE_CAVEAT
            if any(c >= _CH_DIVERGENCE_THRESHOLD for c in chapters)
            else None
        )

        return {
            "lecture": resolved_descr,
            "chapters": chapters,
            "n_textbook_concepts": len(textbook_recs),
            "n_lecture_chunks": len(lecture_recs),
            "covered": covered,
            "gaps": gaps,
            "possible_mismatches": possible_mismatches,
            "caveat": caveat,
        }

    def _resolve_lecture(self, lecture):
        """Resolve ``lecture`` -> ``(chapters, lecture_recs, descr)``. See the three
        cases documented on :meth:`check_lecture_sync`."""
        # 1. int -> single chapter; lecture chunks are lecture records in that chapter.
        if isinstance(lecture, int) and not isinstance(lecture, bool):
            chapters = [lecture]
            recs = self._records_for_chapters("lecture", chapters)
            return chapters, recs, f"chapter {lecture}"

        # 2. path-like: a .qmd/.rmd file that exists on disk.
        if isinstance(lecture, str):
            p = Path(lecture)
            if p.suffix.lower() in (".qmd", ".rmd") and p.exists():
                return self._resolve_lecture_path(lecture)

            # 3. topic string -> lecture hits.
            hits = self.search_all(lecture, source_type="lecture", top_k=10)
            chapter_set: set[int] = set()
            for h in hits:
                chapter_set.update(h.get("chapters") or [])
            chapters = sorted(chapter_set)
            # Re-fetch full records (with embeddings) for the hit source_paths so we can
            # use stored embeddings and consistent citation shape.
            recs = self._lecture_recs_for_paths({h["source_path"] for h in hits})
            return chapters, recs, f"topic:{lecture}"

        raise TypeError(f"unsupported lecture spec: {lecture!r}")

    def _resolve_lecture_path(self, path: str):
        """Resolve a lecture .qmd/.rmd path -> ``(chapters, lecture_recs, descr)``."""
        from .loaders.dispatch import load
        from .metadata import map_chapters

        raw = load(path)
        front = raw.native_metadata if raw is not None else None
        chapters = map_chapters(path, front_matter=front)

        # Lecture chunks for this file: match stored source_path exactly, else basename.
        recs = self._lecture_recs_for_paths({path})
        if not recs:
            base = Path(path).name
            all_lec = self._get_by({"source_type": {"$eq": "lecture"}})
            recs = [r for r in all_lec if Path(r["meta"].source_path).name == base]
        return chapters, recs, f"file:{path}"

    def _lecture_recs_for_paths(self, paths: set[str]) -> list[dict]:
        """Fetch lecture records whose stored ``source_path`` is in ``paths``.

        Tries each exact path via ``collection.get(where=...)``; collects de-duplicated
        records (with embeddings) for the sync computation.
        """
        out: list[dict] = []
        seen: set[str] = set()
        for path in paths:
            recs = self._get_by({
                "$and": [
                    {"source_type": {"$eq": "lecture"}},
                    {"source_path": {"$eq": path}},
                ]
            })
            for r in recs:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    out.append(r)
        return out
