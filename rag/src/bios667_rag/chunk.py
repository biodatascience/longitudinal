"""Semantic chunking for the course corpus.

``semantic_chunk`` is the original textbook section-based chunker (kept intact for
the textbook indexer). ``chunk_document`` is the generalized per-``source_type``
dispatcher (Task 3.1): it routes a :class:`~bios667_rag.loaders.base.RawDoc` to a
chunking strategy keyed on its ``source_type`` (one of the 11
:data:`~bios667_rag.metadata.SOURCE_TYPES`) and returns ``(text, chunk_type)`` tuples.
"""

import re
from dataclasses import dataclass

from .loaders.base import RawDoc


@dataclass
class Chunk:
    """A semantic chunk of text."""
    text: str
    chapter_num: int
    section_path: str
    page_start: int
    page_end: int
    chunk_type: str = "content"


def estimate_tokens(text: str) -> int:
    """Rough token estimate (words * 1.3)."""
    return int(len(text.split()) * 1.3)


def semantic_chunk(
    text: str,
    chapter_num: int,
    max_tokens: int = 600,
    page_start: int = 1,
) -> list[Chunk]:
    """Split text into semantic chunks by section."""
    chunks = []
    section_pattern = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+(.+?)(?=\n|$)", re.MULTILINE)

    sections = []
    for match in section_pattern.finditer(text):
        sections.append({
            "number": match.group(1),
            "title": match.group(2).strip(),
            "start": match.start(),
        })

    if not sections:
        if text.strip():
            chunks.append(Chunk(
                text=text.strip(), chapter_num=chapter_num,
                section_path=f"{chapter_num}.0",
                page_start=page_start, page_end=page_start,
            ))
        return chunks

    for i, section in enumerate(sections):
        start = section["start"]
        end = sections[i + 1]["start"] if i + 1 < len(sections) else len(text)
        section_text = text[start:end].strip()

        if estimate_tokens(section_text) <= max_tokens:
            chunks.append(Chunk(
                text=section_text, chapter_num=chapter_num,
                section_path=section["number"],
                page_start=page_start, page_end=page_start,
            ))
        else:
            paragraphs = re.split(r"\n\s*\n", section_text)
            current_chunk = []
            current_tokens = 0

            for para in paragraphs:
                para_tokens = estimate_tokens(para)

                if current_tokens + para_tokens > max_tokens and current_chunk:
                    chunks.append(Chunk(
                        text="\n\n".join(current_chunk), chapter_num=chapter_num,
                        section_path=section["number"],
                        page_start=page_start, page_end=page_start,
                    ))
                    current_chunk = [para]
                    current_tokens = para_tokens
                else:
                    current_chunk.append(para)
                    current_tokens += para_tokens

            if current_chunk:
                chunks.append(Chunk(
                    text="\n\n".join(current_chunk), chapter_num=chapter_num,
                    section_path=section["number"],
                    page_start=page_start, page_end=page_start,
                ))

    return chunks


# --------------------------------------------------------------------------- #
# Task 3.1: per-source_type chunking dispatch.
# --------------------------------------------------------------------------- #

# source_type groups (keys are the 11 SOURCE_TYPES, never loader names).
_PROSE_TYPES = frozenset(
    {"textbook", "lecture", "handout", "slides", "syllabus"}
)
_PROBLEM_TYPES = frozenset({"hw", "hw_solution", "quiz"})
_CODE_TYPES = frozenset({"sas", "rcode"})
# "data_card" is handled on its own (single chunk).

# A heading line for prose splitting. Matches, in order:
#   * numbered sections: ``8.1 Title`` / ``8.1.2 Title``
#   * markdown headings:  ``## Title`` / ``### Title``
#   * \section-style:     ``\section{Title}`` / ``\subsection*{Title}``
#   * slide separators:   ``--- Slide N ---``
_HEADING_RE = re.compile(
    r"^(?:"
    r"\d+\.\d+(?:\.\d+)?\s+\S"          # numbered section
    r"|#{1,6}\s+\S"                      # markdown ## / ###
    r"|\\(?:sub)*section\*?\s*\{"        # \section{...}, \subsection{...}
    r"|---\s*Slide\s+\d+\s*---"          # --- Slide N ---
    r")",
    re.MULTILINE | re.IGNORECASE,
)

# A problem boundary: a line opening with ``1.``, ``Q1)``, ``2)``, etc.
_PROBLEM_RE = re.compile(r"^\s*Q?\d+[.)]", re.MULTILINE | re.IGNORECASE)


def _resolve_source_type(raw_doc: RawDoc, meta=None) -> str | None:
    """Return the dispatch ``source_type`` from the RawDoc (preferred) or meta."""
    st = getattr(raw_doc, "source_type", None)
    if not st and meta is not None:
        st = getattr(meta, "source_type", None)
    return st


def _chunk_prose(text: str) -> list[tuple[str, str]]:
    """Heading-aware ~600-token chunks with ~80-token overlap.

    Splits ``text`` at heading lines (numbered, markdown, ``\\section``, or slide
    separators), then packs sections into ~600-token windows, carrying a ~80-token
    tail overlap into the next window so context is not lost across chunk boundaries.
    """
    max_tokens = 600
    overlap_tokens = 80

    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        sections = [text.strip()] if text.strip() else []
    else:
        sections = []
        # Preamble before the first heading, if any.
        head = text[: matches[0].start()].strip()
        if head:
            sections.append(head)
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            seg = text[start:end].strip()
            if seg:
                sections.append(seg)

    chunks: list[tuple[str, str]] = []
    current: list[str] = []
    current_tokens = 0

    def _flush() -> list[str]:
        """Emit the current window and return the overlap tail (list of words)."""
        if not current:
            return []
        chunk_text = "\n\n".join(current)
        chunks.append((chunk_text, "content"))
        words = chunk_text.split()
        # ~80-token tail; tokens ~= words * 1.3, so take ~80/1.3 words.
        n_words = int(overlap_tokens / 1.3)
        return words[-n_words:] if n_words else []

    for sec in sections:
        sec_tokens = estimate_tokens(sec)
        if current and current_tokens + sec_tokens > max_tokens:
            tail = _flush()
            current = []
            current_tokens = 0
            if tail:
                overlap = " ".join(tail)
                current.append(overlap)
                current_tokens += estimate_tokens(overlap)
        current.append(sec)
        current_tokens += sec_tokens

    if current:
        chunks.append(("\n\n".join(current), "content"))

    if not chunks and text.strip():
        chunks.append((text.strip(), "content"))
    return chunks


def _chunk_problems(text: str) -> list[tuple[str, str]]:
    """Split on question boundaries so each chunk is one self-contained problem."""
    starts = [m.start() for m in _PROBLEM_RE.finditer(text)]
    if not starts:
        return [(text.strip(), "problem")] if text.strip() else []

    chunks: list[tuple[str, str]] = []
    # Any preamble before the first problem boundary (instructions, honor-code
    # text, etc.) is intentionally dropped: we start iterating at the first
    # boundary, so only the problem units themselves are emitted.
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        seg = text[start:end].strip()
        if seg:
            chunks.append((seg, "problem"))
    return chunks


def _chunk_code(text: str, nl_header: str) -> list[tuple[str, str]]:
    """Split code on ``proc``/function boundaries, prepending the NL header per chunk.

    The code RawDoc already has ``nl_header`` at the TOP of ``text`` (see
    ``loaders/code.py``). We strip that single leading copy, split the remaining body
    on boundaries, then prepend the header to EACH chunk so every chunk is
    independently retrievable.

    Unlike ``_chunk_problems``, which drops preamble, ``_chunk_code`` folds
    preamble into the first chunk; a whitespace-only RawDoc yields no
    chunks (the ``text.strip()`` guard on the fallback prevents an empty chunk
    from polluting the index).
    """
    body = text
    if nl_header and body.startswith(nl_header):
        body = body[len(nl_header):].lstrip("\n")

    # Boundary: ``proc <name>`` (SAS) or ``name <- function`` / ``name = function`` (R).
    boundary_re = re.compile(
        r"(?=^\s*proc\b|^\s*[A-Za-z.][\w.]*\s*(?:<-|=)\s*function\b)",
        re.MULTILINE | re.IGNORECASE,
    )
    starts = [m.start() for m in boundary_re.finditer(body)]

    segments: list[str] = []
    if not starts:
        if body.strip():
            segments = [body.strip()]
    else:
        # Preamble before the first boundary (comments/setup) rides with first chunk.
        head = body[: starts[0]].strip()
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else len(body)
            seg = body[start:end].strip()
            if not seg:
                continue
            if i == 0 and head:
                seg = head + "\n" + seg
            segments.append(seg)
        if not segments and head:
            segments = [head]

    chunks: list[tuple[str, str]] = []
    for seg in segments:
        chunk_text = (nl_header + "\n\n" + seg) if nl_header else seg
        chunks.append((chunk_text, "code"))
    if not chunks and body.strip():
        # Fall back to the whole text (header already at top) as one chunk.
        # Gate on the stripped BODY (post-header) so a non-empty nl_header with a
        # whitespace-only body yields no header-only junk chunk.
        chunks.append((text.strip(), "code"))
    return chunks


def chunk_document(raw_doc: RawDoc, meta=None) -> list[tuple[str, str]]:
    """Chunk a :class:`RawDoc` by its ``source_type``, returning ``(text, chunk_type)``.

    Dispatch keys are :data:`~bios667_rag.metadata.SOURCE_TYPES` members only:

    * prose (``textbook``/``lecture``/``handout``/``slides``/``syllabus``):
      heading-aware ~600-token chunks with ~80-token overlap -> ``"content"``.
    * problems (``hw``/``hw_solution``/``quiz``): one chunk per problem -> ``"problem"``.
    * code (``sas``/``rcode``): split on ``proc``/function, NL header per chunk
      -> ``"code"``.
    * ``data_card``: a single chunk -> ``"card"``.

    ``source_type`` is taken from ``raw_doc.source_type`` (preferred) or ``meta``.
    """
    source_type = _resolve_source_type(raw_doc, meta)
    text = raw_doc.text

    if source_type in _PROBLEM_TYPES:
        return _chunk_problems(text)
    if source_type in _CODE_TYPES:
        nl_header = (raw_doc.native_metadata or {}).get("nl_header", "")
        return _chunk_code(text, nl_header)
    if source_type == "data_card":
        return [(text.strip(), "card")] if text.strip() else []

    # Prose types (textbook/lecture/handout/slides/syllabus), plus any
    # unknown/unset source_type: prose is the safest, most retrievable default.
    return _chunk_prose(text)
