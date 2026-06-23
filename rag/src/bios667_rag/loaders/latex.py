"""Loader for LaTeX (``.tex``) source documents.

A ``.tex`` file is plain UTF-8 text, but its raw form is noisy for retrieval: the
preamble (``\\documentclass``/``\\usepackage`` etc.) carries no course content, and
line comments add clutter. This loader does a *light* clean-up -- it does NOT attempt
to fully de-TeX the body:

* Strip the preamble: if ``\\begin{document}`` is present, keep only the body after
  it (and drop a trailing ``\\end{document}``). With no ``\\begin{document}`` the whole
  file is kept.
* Strip line comments: remove an unescaped ``%`` to end-of-line, but keep a literal
  ``\\%`` (unescaped to ``%`` in the output).
* Make sectioning commands readable headings: ``\\section{Title}`` (and
  ``\\subsection``/``\\subsubsection``) become a ``# Title`` line so the heading text
  survives for chunking/retrieval. Other commands are left inline as-is.

``source_type`` is resolved by ROLE via
:func:`bios667_rag.metadata.classify_source_type` (e.g. ``handouts/foo.tex`` ->
``"handout"``). Empty after stripping -> ``None``.
"""

import re
from pathlib import Path

from ..metadata import classify_source_type
from .base import RawDoc
from .dispatch import register

# Sectioning command -> readable heading. Captures the (possibly starred) command name
# and its braced title, e.g. ``\section{Covariance Models}`` or ``\subsection*{X}``.
_SECTION_RE = re.compile(r"\\(?:sub){0,2}section\*?\s*\{([^}]*)\}")


def _strip_preamble(content: str) -> str:
    """Drop everything before ``\\begin{document}`` and the trailing ``\\end{document}``.

    If there is no ``\\begin{document}``, return ``content`` unchanged.
    """
    begin = re.search(r"\\begin\{document\}", content)
    if begin is None:
        return content
    body = content[begin.end() :]
    end = re.search(r"\\end\{document\}", body)
    if end is not None:
        body = body[: end.start()]
    return body


def _strip_line_comment(line: str) -> str:
    """Remove an unescaped ``%`` comment to end-of-line; keep ``\\%`` as literal ``%``.

    Scans char-by-char so an escaped percent (preceded by a backslash) is treated as a
    literal percent and unescaped, while the first unescaped ``%`` truncates the line.
    """
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "\\" and i + 1 < n and line[i + 1] == "\\":
            # ``\\`` is a line break, not an escape: emit both backslashes verbatim
            # and consume them as one token so a following ``%`` is a real comment.
            out.append("\\\\")
            i += 2
            continue
        if ch == "\\" and i + 1 < n and line[i + 1] == "%":
            # Escaped percent: emit a literal `%`, consume both chars.
            out.append("%")
            i += 2
            continue
        if ch == "%":
            # Unescaped comment marker: drop the rest of the line.
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _readable_headings(text: str) -> str:
    r"""Turn ``\section{...}``/``\subsection{...}``/``\subsubsection{...}`` into ``# ...``."""
    return _SECTION_RE.sub(lambda m: "# " + m.group(1).strip(), text)


def latex_loader(path: str) -> RawDoc | None:
    """Load a ``.tex`` file into a :class:`RawDoc`, or ``None`` if empty after stripping.

    Strips the preamble and line comments and rewrites sectioning commands as readable
    headings (see the module docstring). The body is otherwise left inline as-is.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not content.strip():
        return None

    body = _strip_preamble(content)
    body = "\n".join(_strip_line_comment(ln) for ln in body.splitlines())
    body = _readable_headings(body)

    if not body.strip():
        return None

    return RawDoc(
        text=body,
        source_path=path,
        source_type=classify_source_type(path),
        native_metadata={},
    )


register(".tex", loader=latex_loader)
