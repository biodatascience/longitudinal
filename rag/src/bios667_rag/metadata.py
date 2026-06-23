"""Metadata schema for the course-corpus RAG: source types, chunk IDs, chunk metadata.

``SourceType`` is the single source of truth for valid corpus source types. Note that
loader names like ``latex``/``quarto`` are NOT source types.

ChromaDB metadata values must be scalars (str/int/float/bool). ``ChunkMeta.to_chroma``
serializes the list-valued fields as comma-joined strings and ``from_chroma`` parses
them back, round-tripping exactly so that downstream exact int-membership filtering on
``chapters`` (e.g. ``N in chapters``) works without substring false-matches.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import Literal, get_args

# Single source of truth for valid source types. Used as both a Literal and a frozenset.
SourceType = Literal[
    "textbook",
    "lecture",
    "hw",
    "hw_solution",
    "handout",
    "quiz",
    "slides",
    "author_slides",
    "sas",
    "rcode",
    "data_card",
    "syllabus",
]

# Derived from ``SourceType`` so the two never drift apart (single source of truth).
SOURCE_TYPES: frozenset[str] = frozenset(get_args(SourceType))

# Sentinel stored for ``year=None`` in chroma (chroma needs a scalar). Restored to None.
_YEAR_NONE = -1

# A BIOS667 lecture deck filename, e.g. ``BIOS667_L08_LME.qmd``. Used as a role signal:
# such files are lectures regardless of their RevealJS front-matter format.
_LECTURE_NAME_RE = re.compile(r"BIOS667_L\d+", re.IGNORECASE)

# Matches a chapter signal in a path: ``ch`` + digits, plus any underscore-separated
# trailing digit groups that are the ``_ch5_6`` shorthand (5 AND 6) -- but NOT digit
# groups that themselves carry a ``ch`` prefix, since ``ch5_ch6`` yields two separate
# matches. Group 1 is the leading chapter; group 2 is the trailing ``_6`` shorthand tail
# (possibly several, e.g. ``ch5_6_7``), captured for splitting by the caller.
_CHAPTER_RE = re.compile(r"ch(\d+)((?:_\d+)*)", re.IGNORECASE)

# FLW (2011, 2nd ed.) chapter map for the topic-named book PDFs in ``book/`` (e.g.
# "Applied Longitudinal Analysis - 2011 - Fitzmaurice - Linear Mixed Effects Models.pdf").
# These carry no ``chN`` token, so ``map_chapters`` resolves them by distinctive title
# keyword instead. Chapter numbers follow the authoritative FLW 2nd-edition table of
# contents (verified against the Front Matter PDF) and match the course's lecture
# ``_chN_`` scheme (e.g. "Linear Mixed Effects Models" -> 8, as in L08_ch8).
#
# Ordering is significant: entries are matched top-to-bottom and the FIRST keyword
# substring found wins, so more specific titles MUST precede the shorter titles they
# contain (e.g. the ch15 "Approximate Methods" GLMM volume before the ch14 plain GLMM
# volume; the ch12 "Introduction and Overview" and ch13 "GEE" marginal-model volumes
# before any bare "marginal models" match). Appendices, front matter, and the
# whole-book single PDF have no numbered chapter and resolve to ``[]``.
_FLW_CHAPTER_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("longitudinal and clustered data", 1),
    ("basic concepts", 2),
    ("overview of linear models", 3),
    ("estimation and statistical inference", 4),
    ("analyzing response profiles", 5),
    ("parametric curves", 6),
    ("modeling the covariance", 7),
    # GLMM (ch14/15) titles CONTAIN "linear mixed effects models"; they must be tested
    # before the bare ch8 LME key, and the ch15 "approximate methods" before ch14.
    ("generalized linear mixed effects models  approximate methods", 15),
    ("generalized linear mixed effects models", 14),
    ("linear mixed effects models", 8),
    ("fixed effects versus random effects", 9),
    ("residual analyses and diagnostics", 10),
    ("review of generalized linear models", 11),
    ("marginal models  introduction and overview", 12),
    ("marginal models  introduction", 12),
    ("generalized estimating equations", 13),
    ("approximate methods", 15),
    ("contrasting marginal and mixed effects models", 16),
    ("missing data and dropout  overview", 17),
    ("missing data and dropout  multiple imputation", 18),
    ("smoothing longitudinal data", 19),
    ("semiparametric regression", 19),
    ("sample size and power", 20),
    ("repeated measures", 21),
    ("multilevel models", 22),
)


def flw_textbook_chapters(filename: str) -> list[int]:
    """Return the FLW chapter number(s) for a topic-named Fitzmaurice book PDF.

    The 24 FLW (2011) PDFs in ``book/`` are named by TOPIC, not chapter number, e.g.
    ``Applied Longitudinal Analysis - 2011 - Fitzmaurice - Linear Mixed Effects
    Models.pdf``. This maps such a filename (case-insensitive; a full path is also
    accepted -- only the basename is inspected) to its chapter via distinctive title
    keyword, using the authoritative FLW 2nd-edition table of contents.

    Returns a single-element list for numbered chapters, or ``[]`` for front matter,
    the appendices (Gentle Introduction to Vectors and Matrices, Properties of
    Expectations and Variances, Critical Points...), and the whole-book single PDF
    that has no topic suffix -- none of which is a single numbered chapter.
    """
    name = filename.lower().rsplit("/", 1)[-1]
    for keyword, chapter in _FLW_CHAPTER_KEYWORDS:
        if keyword in name:
            return [chapter]
    return []


def classify_source_type(path: str, front_matter: dict | None = None) -> str:
    """Classify a corpus file into a :data:`SOURCE_TYPES` member by ROLE, not format.

    Critical design rule: every BIOS667 lecture is authored as a RevealJS ``.qmd``
    deck, so ``format: revealjs`` in ``front_matter`` does NOT imply ``slides``.
    Lecture decks classify as ``"lecture"``; ``"slides"`` is reserved for standalone
    ``.pptx`` files only.

    Resolution order (first match wins):

    1. ``syllabus`` in filename -> ``"syllabus"``.
    2. ``.pptx`` extension -> ``"slides"``.
    3. Path/name role signals (apply regardless of extension):
       ``homework/`` -> ``"hw_solution"`` (if ``_solution`` in name) else ``"hw"``;
       ``quizzes/`` -> ``"quiz"``; ``handouts/`` -> ``"handout"``;
       ``lectures/`` or ``BIOS667_L\\d+`` filename -> ``"lecture"``.
    4. Code/data extensions: ``.sas`` -> ``"sas"``; ``.r`` ONLY -> ``"rcode"``
       (``.rmd`` deliberately falls through); ``.dat``/``.csv`` -> ``"data_card"``.
    5. Textbook signal: path contains ``/book/`` OR filename contains
       ``fitzmaurice`` OR ``applied longitudinal analysis`` -> ``"textbook"``.
       (The old loose "any path containing the word ``textbook``" rule was removed
       because it mis-caught our own design docs under ``docs/.../*textbook*``.)
    6. Catch-all default -> ``"lecture"``.

    ``front_matter`` is accepted for interface stability but intentionally does not
    override role signals (see the design rule above).
    """
    p = path.lower()
    name = p.rsplit("/", 1)[-1]
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""

    # 1. Syllabus by filename (highest priority).
    if "syllabus" in name:
        return "syllabus"

    # 2. Standalone slide decks.
    if ext == ".pptx":
        return "slides"

    # 2b. FLW author's official lecture slides (BIO 226), kept under an
    #     ``author_slides/`` dir. Distinct from our own decks and from the book text.
    if "author_slides/" in p or "bio226-slides" in name:
        return "author_slides"

    # 3. Path / name role signals.
    if "homework/" in p:
        return "hw_solution" if "_solution" in name else "hw"
    if "quizzes/" in p:
        return "quiz"
    if "handouts/" in p:
        return "handout"
    if "lectures/" in p or _LECTURE_NAME_RE.search(name):
        return "lecture"

    # 4. Code / data extensions. Note: .rmd is a document, NOT rcode.
    if ext == ".sas":
        return "sas"
    if ext == ".r":
        return "rcode"
    if ext in (".dat", ".csv"):
        return "data_card"

    # 5. Textbook signal: the real FLW book PDFs live under ``book/`` and are named
    #    like "Applied Longitudinal Analysis - 2011 - Fitzmaurice - ...". Detect by the
    #    ``/book/`` directory OR a Fitzmaurice / "applied longitudinal analysis" filename.
    #    (Deliberately NOT triggered by the bare word "textbook" in a path, which would
    #    mis-catch our own design docs.)
    if (
        "/book/" in p
        or p.startswith("book/")
        or "fitzmaurice" in name
        or "applied longitudinal analysis" in name
    ):
        return "textbook"

    # 6. Catch-all default.
    return "lecture"


def map_chapters(
    path: str, front_matter: dict | None = None, text: str | None = None
) -> list[int]:
    """Return the FLW textbook chapter number(s) a file pertains to, sorted & deduped.

    Precedence (first signal wins):

    1. Explicit front-matter: a truthy ``chapters`` (non-empty list of ints) or
       ``chapter`` (non-zero int). A falsy/empty value is treated as unset and falls
       through to path parsing.
    2. Path/filename ``ch<digits>`` signals, including the multi-chapter shorthand
       ``_ch5_6`` (chapters 5 AND 6), ``ch5_ch6``, and ``ch11_12``.
    3. FLW textbook fallback: when there is no ``chN`` token and the file is the
       Fitzmaurice book (path under ``book/`` or a Fitzmaurice/"applied longitudinal
       analysis" filename), resolve the chapter from the topic in the filename via
       :func:`flw_textbook_chapters`. The 24 FLW PDFs are named by topic, not number.
    4. Otherwise ``[]`` -- no guessing here; a later task resolves empties via a
       nearest-textbook-chunk vote.

    ``text`` is reserved for that future nearest-chunk fallback and is currently unused.
    """
    # text is reserved for fallback (nearest-textbook-chunk vote); intentionally unused.
    _ = text

    # 1. Explicit front-matter wins -- but only when truthy. An empty/falsy
    #    ``chapters``/``chapter`` (``[]``, ``None``, ``0``) is treated as "unset" so we
    #    fall through to path parsing rather than suppressing it. (An empty list must
    #    not short-circuit: the nearest-textbook-chunk fallback vote relies on empties.)
    if front_matter:
        if front_matter.get("chapters"):
            return sorted({int(c) for c in front_matter["chapters"]})
        if front_matter.get("chapter"):
            return [int(front_matter["chapter"])]

    # 2. Parse path/filename for ``ch<digits>`` signals (incl. ``_ch5_6`` shorthand).
    chapters: set[int] = set()
    for lead, tail in _CHAPTER_RE.findall(path):
        chapters.add(int(lead))
        # tail is like "_6" or "_6_7"; split out the shorthand continuation chapters.
        for part in tail.split("_"):
            if part:
                chapters.add(int(part))

    if chapters:
        return sorted(chapters)

    # 3. FLW textbook fallback: the topic-named book PDFs carry no ``chN`` token, so
    #    map them by title keyword when the file is recognized as the Fitzmaurice book.
    p = path.lower()
    name = p.rsplit("/", 1)[-1]
    if (
        "/book/" in p
        or p.startswith("book/")
        or "fitzmaurice" in name
        or "applied longitudinal analysis" in name
    ):
        return flw_textbook_chapters(path)

    # 4. Empty list when no signal.
    return []


def make_chunk_id(source_path: str, chunk_index: int) -> str:
    """Return a stable 40-char SHA-1 hex id for a chunk.

    The ``::`` separator prevents collisions like ``("foo", 10)`` vs ``("foo1", 0)``.
    """
    return hashlib.sha1(f"{source_path}::{chunk_index}".encode()).hexdigest()


@dataclass
class ChunkMeta:
    """Metadata for a single corpus chunk."""

    chunk_id: str
    source_type: str
    source_path: str
    title: str
    chapters: list[int]
    topic_tags: list[str]
    year: int | None
    dataset_refs: list[str]
    is_solution: bool
    chunk_type: str

    def to_chroma(self) -> dict:
        """Serialize to a dict of ChromaDB-safe scalars.

        List fields become comma-joined strings (empty list -> ""). ``year=None`` is
        stored as ``-1``. Booleans stay bool.

        Encoding caveat: because list fields (``chapters``, ``topic_tags``,
        ``dataset_refs``) are comma-joined, individual list-element values must not
        contain commas, or ``from_chroma`` will split them incorrectly. No runtime
        guard enforces this.
        """
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "title": self.title,
            "chapters": ",".join(str(c) for c in self.chapters),
            "topic_tags": ",".join(self.topic_tags),
            "year": self.year if self.year is not None else _YEAR_NONE,
            "dataset_refs": ",".join(self.dataset_refs),
            "is_solution": self.is_solution,
            "chunk_type": self.chunk_type,
        }

    @classmethod
    def from_chroma(cls, d: dict) -> "ChunkMeta":
        """Inverse of :meth:`to_chroma`. Empty strings parse to ``[]`` (not ``[""]``)."""
        chapters_raw = d["chapters"]
        chapters = [int(c) for c in chapters_raw.split(",")] if chapters_raw else []

        topic_raw = d["topic_tags"]
        topic_tags = topic_raw.split(",") if topic_raw else []

        datasets_raw = d["dataset_refs"]
        dataset_refs = datasets_raw.split(",") if datasets_raw else []

        year = d["year"]
        year = None if year == _YEAR_NONE else year

        return cls(
            chunk_id=d["chunk_id"],
            source_type=d["source_type"],
            source_path=d["source_path"],
            title=d["title"],
            chapters=chapters,
            topic_tags=topic_tags,
            year=year,
            dataset_refs=dataset_refs,
            is_solution=d["is_solution"],
            chunk_type=d["chunk_type"],
        )
