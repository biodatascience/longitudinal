"""Corpus walker, ``--plan`` preview, and the sha256 ingest manifest.

This module is deliberately cheap: it WALKS corpus roots, decides which files are
*admittable* (their extension is claimed by the loader dispatch registry), classifies
each admitted file by PATH only, and tracks per-file sha256 in a JSON manifest so a
later ingest can skip unchanged files. It performs NO embedding and NO chunking -- it
loads no file contents beyond hashing for the manifest. Those steps live downstream.

Safety: the walker only descends into the roots it is given and hard-excludes build
artifacts, virtualenvs, caches, the RAG data store, and Dropbox "conflicted copy"
files. Callers pass explicit roots; nothing here discovers roots on its own.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from .chunk import chunk_document
from .loaders import LOADERS, load
from .loaders.dispatch import BINARY_EXTS
from .metadata import (
    ChunkMeta,
    classify_source_type,
    make_chunk_id,
    map_chapters,
)

# Path substrings (and one filename substring) that exclude a file or directory from
# the walk. Directory names are matched as exact path components; ``*_cache`` and
# ``*_files`` match any directory whose name ends in that suffix (e.g. Quarto's
# ``BIOS667_L08_files`` render-artifact dirs). ``conflicted copy`` matches Dropbox
# conflict files anywhere in the filename.
_EXCLUDE_DIR_SUBSTRINGS = (".venv", ".git", ".quarto")
_EXCLUDE_DIR_SUFFIXES = ("_cache", "_files")
_EXCLUDE_PATH_SUBSTRINGS = ("rag/data",)
_EXCLUDE_NAME_SUBSTRINGS = ("conflicted copy",)

# --- curation excludes (Task 4.3a) -------------------------------------------
# Directory components that exclude any path under them: our own tooling/meta
# (``docs/`` design docs, the ``rag/`` package dir itself), cloned student
# repositories (``repos``/``repos_cloned``), and the stale ``repo/`` course-clone
# (an Aug-Oct 2025 git snapshot of the course that duplicates the canonical ``new/``
# materials -- redundant textbook PDFs, older lecture .qmd, and data). Matched as
# exact path components (case-insensitive) so subtrees are pruned whole.
_EXCLUDE_DIR_COMPONENTS = ("docs", "rag", "repo", "repos", "repos_cloned")

# Exact filenames (case-insensitive) we never index. Two kinds:
#  * Meta files we author ourselves (CLAUDE.md, audits, plans).
#  * The redundant WHOLE-BOOK FLW PDF. ``book/`` holds one per-chapter PDF each named
#    ``Applied Longitudinal Analysis - 2011 - Fitzmaurice - <Topic>.pdf`` (a " - " AFTER
#    "Fitzmaurice"); the whole-book file ``Applied Longitudinal Analysis - 2011 -
#    Fitzmaurice.pdf`` ends right after "Fitzmaurice" and duplicates all of them as one
#    untagged blob (chapters=[]). Excluding the exact basename drops only the whole-book
#    file -- the per-chapter PDFs have distinct basenames and survive.
_EXCLUDE_EXACT_NAMES = frozenset(
    n.lower()
    for n in (
        "CLAUDE.md",
        "AGENTS.md",
        "CLAUDE_md_improvements.md",
        "REVIEW_CROSS_REFERENCE.md",
        "LECTURE_TIMING_PLAN.md",
        "COURSE_MATERIALS_AUDIT.md",
        "Applied Longitudinal Analysis - 2011 - Fitzmaurice.pdf",
    )
)

# Basename glob patterns (case-insensitive) for tooling/meta and SAS-output PDFs.
# ``*_note.md`` is our scratch notes; ``*_AUDIT.md`` / ``STUDENT_REVIEW*.md`` are
# review meta. ``6city*.pdf`` and ``*sas*.pdf`` are SAS-output PDFs (NOT the FLW
# book PDFs, which carry neither token, and NOT ``.sas`` source files).
_EXCLUDE_NAME_GLOBS = (
    "*_note.md",
    "*_audit.md",
    "student_review*.md",
    "6city*.pdf",
    "*sas*.pdf",
)

# Manifest filename written under the store directory.
_MANIFEST_NAME = "ingest_manifest.json"


def admitted_extensions() -> set[str]:
    """Extensions admitted by the walker, derived from the dispatch registry.

    Built from ``dispatch.LOADERS`` keys (every concrete loader's extensions),
    ``BINARY_EXTS`` (defensive: in case a binary ext is ever known to dispatch but not
    yet in ``LOADERS``), and ``.txt`` (handled dynamically inside ``dispatch.load`` and
    therefore absent from the static registry). Deriving from dispatch -- rather than
    hardcoding a parallel list -- keeps the admitted set in sync as loaders are added.
    """
    return set(LOADERS.keys()) | set(BINARY_EXTS) | {".txt"}


def _is_excluded(path: Path) -> bool:
    """True if ``path`` lies under an excluded dir, store, or is a conflicted copy.

    Beyond the build-artifact / store / conflicted-copy rules, this also applies the
    Task-4.3a curation excludes: our own tooling/meta directories (``docs/``, the
    ``rag/`` package dir) and files (``CLAUDE.md``, ``*_note.md``, ``*_AUDIT.md``,
    ``STUDENT_REVIEW*.md``, etc.), cloned student repos (``repos``/``repos_cloned``),
    and SAS-output PDFs (``6city*.pdf`` / ``*sas*.pdf``). Reference-paper PDFs and the
    FLW book PDFs are intentionally NOT matched by the SAS-pdf rule.
    """
    import fnmatch

    parts = [part.lower() for part in path.parts]

    for part in parts:
        if part in _EXCLUDE_DIR_SUBSTRINGS:
            return True
        if part.endswith(_EXCLUDE_DIR_SUFFIXES):
            return True
        # Curation: tooling/meta dirs and student-repo dirs (exact-component match).
        if part in _EXCLUDE_DIR_COMPONENTS:
            return True

    posix = path.as_posix().lower()
    for sub in _EXCLUDE_PATH_SUBSTRINGS:
        if sub in posix:
            return True

    name = path.name.lower()
    for sub in _EXCLUDE_NAME_SUBSTRINGS:
        if sub in name:
            return True

    # Curation: exact meta filenames and basename globs (case-insensitive).
    if name in _EXCLUDE_EXACT_NAMES:
        return True
    for pattern in _EXCLUDE_NAME_GLOBS:
        if fnmatch.fnmatch(name, pattern):
            return True

    return False


def _iter_files(roots: list[str], excludes: set[str] | None = None):
    """Yield every non-excluded file under ``roots`` (one shared walk + filter).

    This is the single home for the walk's exclusion logic: it prunes excluded
    directories in place so ``os.walk`` never descends into them, and skips excluded
    files, honoring both the built-in hard-exclusion rules (:func:`_is_excluded`) and
    any extra path-substring ``excludes``. It performs NO extension admission -- callers
    (:func:`walk`, :func:`plan`) decide what to do with each yielded file based on its
    suffix. The walk never ascends above a given root.
    """
    extra = {e.lower() for e in excludes} if excludes else set()

    def _extra_excluded(path: Path) -> bool:
        return bool(extra) and any(x in path.as_posix().lower() for x in extra)

    # Realpath de-duplication (Fix 1): the default corpus roots are NESTED
    # (``.../BIOS667`` contains ``.../BIOS667/new``), so a file under the inner root
    # would otherwise be walked once per containing root. Track the resolved realpath
    # of every yielded file and emit each at most once.
    seen: set[str] = set()

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(Path(root)):
            d = Path(dirpath)

            # Prune excluded directories in place so os.walk does not descend.
            dirnames[:] = [
                name
                for name in dirnames
                if not _is_excluded(d / name) and not _extra_excluded(d / name)
            ]

            for fname in filenames:
                f = d / fname
                if _is_excluded(f) or _extra_excluded(f):
                    continue
                real = os.path.realpath(f)
                if real in seen:
                    continue
                seen.add(real)
                yield f


def walk(roots: list[str], excludes: set[str] | None = None) -> list[Path]:
    """Recursively walk ``roots``; return sorted admitted file Paths.

    A file is ADMITTED only when its (lowercased) extension is in
    :func:`admitted_extensions`. Files/directories matching the hard exclusion rules
    (``.venv``, ``*_files``, ``*_cache``, ``.git``, ``rag/data``, ``.quarto``,
    "conflicted copy" filenames) are skipped, and excluded directories are pruned so the
    walk never descends into them. ``excludes`` adds extra path-substring exclusions on
    top of the built-in rules. The walk never ascends above a given root.
    """
    admitted_exts = admitted_extensions()
    results = [
        f for f in _iter_files(roots, excludes=excludes)
        if f.suffix.lower() in admitted_exts
    ]
    return sorted(results)


def plan(roots: list[str], excludes: set[str] | None = None) -> dict:
    """Build a cheap, no-load preview report for the ``--plan`` CLI gate.

    Walks the roots, classifies each admitted file by PATH only (via
    :func:`classify_source_type`), and tallies a report. This preview performs NO
    embedding, NO chunking, and loads no file contents. Keys:

    * ``counts_by_source_type``: ``{source_type: count}`` over admitted files.
    * ``total_admitted``: number of admitted files.
    * ``unindexed``: admitted-set *misses* -- files whose extension is NOT mapped
      (i.e. what the walk skipped), as a sample list. This is the visibility hook for
      "what got left out". The walk itself already drops these; here we re-scan to
      surface them, while still honoring exclusion rules.
    * ``scanned_pdfs``: count of ``.pdf`` files admitted. NOTE: this is a plain PDF
      *count*, not true scanned-vs-text detection -- distinguishing image-only
      (scanned) PDFs requires actually loading them, which this cheap preview avoids.
    """
    admitted = walk(roots, excludes=excludes)

    counts: dict[str, int] = {}
    scanned_pdfs = 0
    for path in admitted:
        st = classify_source_type(str(path))
        counts[st] = counts.get(st, 0) + 1
        if path.suffix.lower() == ".pdf":
            scanned_pdfs += 1

    # Re-scan for admitted-set MISSES (unmapped extensions) so the plan can report what
    # was skipped. Reusing _iter_files keeps the exclusion rules identical to the walk.
    admitted_exts = admitted_extensions()
    unindexed = [
        f for f in _iter_files(roots, excludes=excludes)
        if f.suffix.lower() not in admitted_exts
    ]

    return {
        "counts_by_source_type": counts,
        "total_admitted": len(admitted),
        "unindexed": sorted(unindexed),
        "scanned_pdfs": scanned_pdfs,
    }


# --- manifest -----------------------------------------------------------------


def manifest_path(store_dir: str) -> str:
    """Return ``<store_dir>/ingest_manifest.json``."""
    return str(Path(store_dir) / _MANIFEST_NAME)


def load_manifest(path: str) -> dict:
    """Load the manifest JSON; return ``{}`` if the file is missing or unreadable."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def file_sha256(path: str) -> str:
    """Return the hex sha256 digest of ``path`` (streamed, constant memory)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_changed(path: str, manifest: dict) -> bool:
    """True if ``path`` is absent from ``manifest`` or its sha256 differs from record."""
    key = str(path)
    entry = manifest.get(key)
    if not entry or "sha256" not in entry:
        return True
    return file_sha256(path) != entry["sha256"]


def update_manifest(manifest: dict, path: str) -> None:
    """Record ``path``'s current sha256 and mtime into ``manifest`` (in place)."""
    p = Path(path)
    manifest[str(path)] = {
        "sha256": file_sha256(path),
        "mtime": p.stat().st_mtime,
    }


def save_manifest(manifest: dict, path: str) -> None:
    """Write ``manifest`` to ``path`` as pretty JSON, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)


# --- build pipeline -----------------------------------------------------------
#
# build() is the indexing core: walk -> (textbook-first) load/chunk/embed -> add to the
# ``bios667_corpus`` ChromaDB collection, plus a small SQLite knowledge graph for
# ``material --uses--> dataset`` edges. It is incremental by default via the sha256
# manifest, and re-embeds everything under ``rebuild=True``.

# Sub-paths of the store directory (kept next to the existing textbook store layout).
_CHROMA_SUBDIR = "chroma"
_GRAPH_DB_NAME = "graph.db"
_CORPUS_COLLECTION = "bios667_corpus"
_LOG_NAME = "corpus_index_log.json"

# A 4-digit year (19xx/20xx) appearing as its own path/name token, e.g. ``.../2024/``
# or ``HW_2023.qmd``. Used as a best-effort ``year`` for ChunkMeta.
_YEAR_RE = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")


def _parse_year(path: str) -> int | None:
    """Best-effort 4-digit year from the path, else ``None``."""
    m = _YEAR_RE.search(path.replace("\\", "/"))
    return int(m.group(0)) if m else None


def _relative_source_path(path: Path, roots: list[str]) -> str:
    """Return ``path`` relative to the first root it lives under, else its full str."""
    for root in roots:
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def _open_corpus_collection(store_dir: str):
    """Open (or create) the ``bios667_corpus`` ChromaDB collection under ``store_dir``."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(Path(store_dir) / _CHROMA_SUBDIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=_CORPUS_COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def _textbook_first_key(path: Path) -> tuple[int, str]:
    """Sort key putting textbook-classified files first (0), then everything else (1).

    The empty-``chapters`` fallback vote queries already-indexed textbook records, so
    every textbook file MUST be processed before any non-textbook file. We sort by
    PATH-classification here (cheap, no load); the per-file loop re-checks the loaded
    RawDoc's source_type as the authoritative signal.
    """
    is_textbook = classify_source_type(str(path)) == "textbook"
    return (0 if is_textbook else 1, str(path))


def _infer_chapters_from_textbook_vote(collection, embedder, first_chunk_text):
    """Vote the nearest already-indexed textbook chunk's chapters for ``first_chunk_text``.

    Embeds the doc's first chunk and queries ``collection`` filtered to
    ``source_type=textbook`` for the single nearest record, returning its parsed
    ``chapters`` list. Best-effort: returns ``[]`` if no textbook records exist yet or
    on any query error.
    """
    if not first_chunk_text:
        return []
    try:
        vec = embedder.embed([first_chunk_text])[0]
        res = collection.query(
            query_embeddings=[vec],
            n_results=1,
            where={"source_type": "textbook"},
            include=["metadatas"],
        )
    except Exception:
        return []
    metas = res.get("metadatas") or []
    if not metas or not metas[0]:
        return []
    try:
        return ChunkMeta.from_chroma(metas[0][0]).chapters
    except Exception:
        return []


def _dataset_stem(data_card_path: Path) -> str:
    """Dataset name for a data_card file: its filename stem, lowercased (e.g. ``dental``)."""
    return data_card_path.stem.lower()


def build(
    roots,
    store_dir,
    *,
    incremental: bool = True,
    embedder=None,
    rebuild: bool = False,
) -> dict:
    """Walk ``roots``, load/chunk/embed admitted files, index into ``bios667_corpus``.

    Textbook-first invariant: files classifying as ``textbook`` are processed before
    all others, because non-textbook files with no chapter signal resolve their
    chapters via a nearest-textbook-chunk vote against already-indexed records.

    Incremental by default (sha256 manifest short-circuits unchanged files);
    ``rebuild=True`` ignores the manifest and re-embeds everything. ``embedder`` may be
    a real :class:`~bios667_rag.embed.Embedder` or any object exposing
    ``embed(list[str]) -> list[list[float]]`` (a fake keeps tests fast); when ``None`` a
    real ``Embedder`` is constructed lazily.

    Side effects under ``store_dir``: the ChromaDB ``bios667_corpus`` collection, a
    SQLite knowledge graph (``graph.db``) carrying dataset nodes and
    ``material --uses--> dataset`` edges, an updated ``ingest_manifest.json``, and a
    ``corpus_index_log.json`` of counts. Returns the log dict.

    Dataset-edge limitation (intentionally simple): dataset names are derived from the
    data_card filenames seen during THIS build, and a ``uses`` edge is added when a
    non-data_card material's text contains that dataset stem (case-insensitive). It does
    not consult a global dataset registry, will not match datasets whose only data_card
    lives outside the walked roots, and uses naive substring matching.
    """
    from .storage import KnowledgeStore

    roots = list(roots)
    store_path = Path(store_dir)
    store_path.mkdir(parents=True, exist_ok=True)

    if embedder is None:
        from .embed import Embedder

        embedder = Embedder()

    collection = _open_corpus_collection(store_dir)
    graph = KnowledgeStore(
        db_path=store_path / _GRAPH_DB_NAME,
        chromadb_path=store_path / _CHROMA_SUBDIR,
    )

    mpath = manifest_path(store_dir)
    manifest = load_manifest(mpath)

    files = sorted(walk(roots), key=_textbook_first_key)

    log = {
        "files_processed": 0,
        "chunks_added": 0,
        "by_source_type": {},
        "skipped_unchanged": 0,
        "unindexed": 0,
    }

    # Dataset registry built as we go: stem -> dataset node id. Because the file list is
    # sorted textbook-first then by path, data_card files are not guaranteed to precede
    # the materials that reference them. We therefore record edges to dataset *stems* and
    # also ensure a node exists for any stem referenced; data_card files upgrade the node
    # with its data-card content/path when encountered.
    known_datasets: set[str] = set()

    # Data_card stem set: computed ONCE here (one classify pass over the file list) rather
    # than recomputed inside the per-file loop, so the cost is O(files) not O(files^2).
    data_card_stems = sorted({
        _dataset_stem(p) for p in files
        if classify_source_type(str(p)) == "data_card"
    })

    def _ensure_dataset_node(stem: str) -> str:
        node_id = f"dataset_{stem}"
        if stem not in known_datasets:
            graph.add_node(node_id=node_id, node_type="dataset", name=stem)
            known_datasets.add(stem)
        return node_id

    for path in files:
        spath = str(path)

        if incremental and not rebuild and not is_changed(spath, manifest):
            log["skipped_unchanged"] += 1
            continue

        raw_doc = load(spath)
        if raw_doc is None:
            log["unindexed"] += 1
            continue

        source_type = raw_doc.source_type
        front_matter = (raw_doc.native_metadata or {}).get("front_matter")
        chapters = map_chapters(spath, front_matter)

        chunks = chunk_document(raw_doc)
        if not chunks:
            # Nothing to index, but the file is accounted for (manifest updated below).
            update_manifest(manifest, spath)
            log["files_processed"] += 1
            log["by_source_type"][source_type] = (
                log["by_source_type"].get(source_type, 0) + 1
            )
            continue

        # Empty-chapters fallback vote (non-textbook only): the nearest already-indexed
        # textbook chunk decides. Textbook-first ordering guarantees those exist by now.
        if not chapters and source_type != "textbook":
            chapters = _infer_chapters_from_textbook_vote(
                collection, embedder, chunks[0][0]
            )

        rel_path = _relative_source_path(path, roots)
        title = (raw_doc.native_metadata or {}).get("title") or path.name
        year = _parse_year(spath)

        # Dataset edges. data_card -> register a dataset node named by its stem. Other
        # materials -> add a uses edge for any known dataset stem mentioned in the text.
        dataset_refs: list[str] = []
        if source_type == "data_card":
            stem = _dataset_stem(path)
            _ensure_dataset_node(stem)
            dataset_refs = [stem]
        else:
            text_lower = raw_doc.text.lower()
            for stem in data_card_stems:
                if stem and re.search(rf"\b{re.escape(stem)}\b", text_lower):
                    node_id = _ensure_dataset_node(stem)
                    material_id = f"material_{make_chunk_id(spath, 0)}"
                    if not graph.get_node(material_id):
                        graph.add_node(
                            node_id=material_id,
                            node_type="material",
                            name=rel_path,
                        )
                    graph.add_edge(material_id, node_id, "uses")
                    dataset_refs.append(stem)

        ids = []
        documents = []
        metadatas = []
        for i, (text, chunk_type) in enumerate(chunks):
            meta = ChunkMeta(
                chunk_id=make_chunk_id(spath, i),
                source_type=source_type,
                source_path=rel_path,
                title=str(title),
                chapters=chapters,
                topic_tags=[],
                year=year,
                dataset_refs=dataset_refs,
                is_solution=(source_type == "hw_solution"),
                chunk_type=chunk_type,
            )
            ids.append(meta.chunk_id)
            documents.append(text)
            metadatas.append(meta.to_chroma())

        embeddings = embedder.embed(documents)
        # upsert (not add): a ``--rebuild`` re-embeds files whose chunk_ids already exist,
        # so we must overwrite-by-id rather than rely on add()'s warn-and-update behavior,
        # which varies across chromadb versions. upsert dedupes by id => no duplicates.
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        update_manifest(manifest, spath)
        log["files_processed"] += 1
        log["chunks_added"] += len(chunks)
        log["by_source_type"][source_type] = (
            log["by_source_type"].get(source_type, 0) + 1
        )

    save_manifest(manifest, mpath)
    graph.close()

    log_path = store_path / _LOG_NAME
    with log_path.open("w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2, sort_keys=True)

    return log


# --- CLI ----------------------------------------------------------------------

# Default corpus root for the ``bios667-index-corpus`` console script. A SINGLE
# level-up root: ``.../BIOS667`` already contains ``.../BIOS667/new``, so listing both
# (as before) double-walked the nested subtree. The realpath-dedup in ``_iter_files``
# is the safety net, but one root is cleaner. ``--roots`` still overrides.
_DEFAULT_ROOTS = [
    "/home/naimrashid/Dropbox/UNC_bios_line/BIOS667",
]
_DEFAULT_STORE_DIR = str(Path(__file__).resolve().parents[2] / "data")


def main(argv=None) -> int:
    """``bios667-index-corpus`` entry point: ``--plan`` preview, default/incremental
    build, or ``--rebuild`` full re-embed. There is intentionally NO ``--full`` flag."""
    parser = argparse.ArgumentParser(
        prog="bios667-index-corpus",
        description="Index the BIOS667 course corpus into the bios667_corpus store.",
    )
    parser.add_argument(
        "--roots", nargs="+", default=None,
        help="Corpus roots to walk (default: the BIOS667 new + parent dirs).",
    )
    parser.add_argument(
        "--store-dir", default=_DEFAULT_STORE_DIR,
        help="Store directory for the chroma collection, graph, manifest, and log.",
    )
    parser.add_argument(
        "--plan", action="store_true",
        help="Preview only: counts by source_type, total, unindexed sample. No embedding.",
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Re-embed everything, ignoring the incremental manifest.",
    )
    args = parser.parse_args(argv)

    roots = args.roots if args.roots else _DEFAULT_ROOTS

    if args.plan:
        report = plan(roots)
        print(f"Total admitted: {report['total_admitted']}")
        print("Counts by source_type:")
        for st, n in sorted(report["counts_by_source_type"].items()):
            print(f"  {st}: {n}")
        unindexed = report["unindexed"]
        print(f"Unindexed (unmapped) files: {len(unindexed)}")
        for p in unindexed[:10]:
            print(f"  {p}")
        if len(unindexed) > 10:
            print(f"  ... and {len(unindexed) - 10} more")
        return 0

    log = build(roots, args.store_dir, incremental=True, rebuild=args.rebuild)
    print(json.dumps(log, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
