"""Loader for SAS (``.sas``) and R (``.r``) source code.

The embedding model (``all-MiniLM-L6-v2``) is trained on prose and embeds raw code
poorly, so a query like "random intercept example" retrieves a ``proc mixed`` file
badly when only the raw code is indexed. To fix this we synthesize a short
natural-language ``nl_header`` from the file's leading comment block and its detected
procedure/function names, e.g.::

    SAS program. Procedures: sort, mixed. Six cities random intercept

The header is stored in ``native_metadata["nl_header"]`` AND prepended to ``text``
(``text == nl_header + "\\n\\n" + raw_code``). This dual placement is deliberate:

* exposing it as metadata lets the chunker (Task 3.1) prepend it per-chunk if needed;
* placing it at the TOP of ``text`` makes retrieval work even before chunking.

Because the header is already the first thing in ``text``, the chunker MUST NOT
prepend it a second time for code RawDocs -- it is already there.

The raw code body is kept verbatim (never executed or stripped). ``source_type`` is
resolved by :func:`bios667_rag.metadata.classify_source_type` (``.sas`` -> ``"sas"``,
``.r`` -> ``"rcode"``).
"""

import re
from pathlib import Path

from ..metadata import classify_source_type
from .base import RawDoc
from .dispatch import register

# SAS procedure invocations: ``proc <name>``. Captures the procedure name.
_SAS_PROC_RE = re.compile(r"\bproc\s+(\w+)", re.IGNORECASE)

# R top-level function definitions: ``name <- function(`` (or ``=`` assignment).
_R_FUNC_RE = re.compile(r"^\s*([A-Za-z.][\w.]*)\s*(?:<-|=)\s*function\b", re.MULTILINE)

# R ``library(pkg)`` / ``require(pkg)`` calls. Captures the package name.
_R_LIB_RE = re.compile(r"\b(?:library|require)\s*\(\s*([\w.]+)", re.IGNORECASE)


def _leading_comment_sas(code: str) -> str:
    """Extract the leading SAS comment text (``/* ... */`` or ``* ... ;`` at top)."""
    stripped = code.lstrip()
    # Block comment /* ... */
    if stripped.startswith("/*"):
        end = stripped.find("*/")
        if end != -1:
            return stripped[2:end].strip()
    # Star-statement comment: ``* text ;`` (only when it opens the file).
    if stripped.startswith("*"):
        end = stripped.find(";")
        if end != -1:
            return stripped[1:end].strip()
    return ""


def _leading_comment_r(code: str) -> str:
    """Extract the contiguous leading block of R ``#`` comment lines at the top."""
    lines = []
    for line in code.splitlines():
        s = line.strip()
        if s == "":
            # Allow blank lines only before any comment has started.
            if lines:
                break
            continue
        if s.startswith("#"):
            lines.append(s.lstrip("#").strip())
        else:
            break
    return " ".join(t for t in lines if t).strip()


def _dedupe(names: list[str]) -> list[str]:
    """Return ``names`` with duplicates removed, preserving first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _build_nl_header(code: str, is_sas: bool) -> str:
    """Build the natural-language retrieval header for a code file.

    Combines the language label, detected procedure/function/library names, and the
    leading comment text into a short (~1-2 line) prose string.
    """
    if is_sas:
        lang = "SAS"
        names = _dedupe(_SAS_PROC_RE.findall(code))
        names_label = "Procedures"
        comment = _leading_comment_sas(code)
    else:
        lang = "R"
        funcs = _dedupe(_R_FUNC_RE.findall(code))
        libs = _dedupe(_R_LIB_RE.findall(code))
        names = _dedupe(funcs + libs)
        names_label = "Functions/libraries"
        comment = _leading_comment_r(code)

    parts = [f"{lang} program."]
    if names:
        parts.append(f"{names_label}: {', '.join(names)}.")
    if comment:
        parts.append(comment)
    return " ".join(parts)


def code_loader(path: str) -> RawDoc | None:
    """Load a ``.sas``/``.r`` file into a :class:`RawDoc`, or ``None`` if empty.

    ``native_metadata["nl_header"]`` holds the synthesized natural-language header and
    ``text`` is ``nl_header + "\\n\\n" + raw_code`` (header at the top, raw code
    verbatim below). See the module docstring for why the header is duplicated into
    ``text`` and the contract this implies for the chunker.
    """
    try:
        code = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not code.strip():
        return None

    source_type = classify_source_type(path)
    is_sas = source_type == "sas"

    nl_header = _build_nl_header(code, is_sas)
    text = nl_header + "\n\n" + code

    return RawDoc(
        text=text,
        source_path=path,
        source_type=source_type,
        native_metadata={"nl_header": nl_header},
    )


register(".sas", ".r", loader=code_loader)
