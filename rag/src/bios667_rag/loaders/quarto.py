"""Loader for Quarto (``.qmd``) and RMarkdown (``.rmd``) source documents.

Parses the leading YAML front-matter block (between ``---`` fences) into a dict and
returns the body *after* that block as ``text``, with prose and fenced code blocks
(```` ``` ````) preserved verbatim -- code is NOT executed or stripped. ``source_type``
is resolved by ROLE via :func:`bios667_rag.metadata.classify_source_type`, so a
RevealJS lecture deck classifies as ``"lecture"``, never ``"slides"``.
"""

from pathlib import Path

import yaml

from ..metadata import classify_source_type
from .base import RawDoc
from .dispatch import register


def _split_front_matter(content: str) -> tuple[dict, str]:
    """Return ``(front_matter, body)`` from raw file ``content``.

    Front-matter is the YAML block delimited by a leading ``---`` line and the next
    ``---`` line. If the file does not begin with a ``---`` fence (allowing leading
    blank lines), there is no front-matter: ``({}, content)`` is returned unchanged.
    """
    lines = content.splitlines(keepends=True)

    # Find the first non-blank line; front-matter must open there with a `---` fence.
    first_idx = next((i for i, ln in enumerate(lines) if ln.strip() != ""), None)
    if first_idx is None or lines[first_idx].strip() != "---":
        return {}, content

    # Find the closing `---` fence after the opening one.
    close_idx = next(
        (i for i in range(first_idx + 1, len(lines)) if lines[i].strip() == "---"),
        None,
    )
    if close_idx is None:
        # Unterminated fence: treat whole file as body (no valid front-matter block).
        return {}, content

    fm_text = "".join(lines[first_idx + 1 : close_idx])
    body = "".join(lines[close_idx + 1 :])

    parsed = yaml.safe_load(fm_text) if fm_text.strip() else None
    front_matter = parsed if isinstance(parsed, dict) else {}
    return front_matter, body


def quarto_loader(path: str) -> RawDoc | None:
    """Load a ``.qmd``/``.rmd`` file into a :class:`RawDoc`, or ``None`` if empty.

    ``native_metadata`` carries the parsed ``front_matter`` dict (``{}`` when absent)
    and, when present, the front-matter ``title``. Code fences in the body are kept
    as text.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not content.strip():
        return None

    front_matter, body = _split_front_matter(content)

    native_metadata: dict = {"front_matter": front_matter}
    title = front_matter.get("title")
    if title is not None:
        native_metadata["title"] = title

    return RawDoc(
        text=body,
        source_path=path,
        source_type=classify_source_type(path, front_matter),
        native_metadata=native_metadata,
    )


register(".qmd", ".rmd", loader=quarto_loader)
