"""Loader for plain-text prose: Markdown (``.md``) and prose ``.txt`` files.

Prose is already natural language, so unlike the code/data-card loaders there is no
synthesized header -- ``text`` is simply the file contents read verbatim as UTF-8.
``source_type`` is resolved by :func:`bios667_rag.metadata.classify_source_type`,
which treats ``.md``/prose ``.txt`` by role (mostly ``"lecture"``, or ``"syllabus"``
by filename).

This module owns ``.md`` (registered at import). It is also the prose destination for
``.txt`` files: :func:`bios667_rag.loaders.dispatch.load` sniffs each ``.txt`` with
``looks_like_data`` and routes tabular files to the data-card loader and the rest
here. ``.txt`` is therefore NOT registered statically -- its destination is dynamic.
"""

from pathlib import Path

from ..metadata import classify_source_type
from .base import RawDoc
from .dispatch import register


def prose_loader(path: str) -> RawDoc | None:
    """Load a plain-text prose file into a :class:`RawDoc`, or ``None`` if empty.

    Reads ``path`` as UTF-8 (best-effort) and stores the contents verbatim in
    ``text``. Empty or whitespace-only content returns ``None``, consistent with the
    single-meaning loader contract (callers treat ``None`` as "skip this path").
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not text.strip():
        return None

    return RawDoc(
        text=text,
        source_path=path,
        source_type=classify_source_type(path),
    )


register(".md", loader=prose_loader)
