"""Extension -> loader registry and the ``load`` entry point.

A loader is a callable ``(path: str) -> RawDoc | None`` registered against one or
more file extensions. Later tasks (2.2-2.8) populate :data:`LOADERS` with concrete
format loaders; this module only provides the registry and dispatch.
"""

from collections.abc import Callable
from pathlib import Path

from .base import RawDoc

# Extension (lowercase, dot-prefixed e.g. ``.qmd``) -> loader callable. Populated by
# later tasks via :func:`register`. A loader returns a ``RawDoc`` or ``None``.
LOADERS: dict[str, Callable[[str], RawDoc | None]] = {}

# Binary loader extensions (e.g. ``.pdf``). Their files are NOT UTF-8 text, so the
# whole-file UTF-8 decode pre-read in :func:`load` would wrongly reject them. For
# these we skip the decode pre-read and only guard against an empty (0-byte) file;
# the loader itself owns parse/validity (returning ``None`` to reject a file). An
# unregistered binary extension is unaffected: it still hits the decode pre-read and
# is rejected like any other undecodable file.
BINARY_EXTS: frozenset[str] = frozenset({".pdf", ".docx", ".pptx"})


def register(*extensions: str, loader: Callable[[str], RawDoc | None]) -> None:
    """Register ``loader`` for one or more file ``extensions``.

    Extensions are normalized to lowercase and dot-prefixed (``"qmd"`` and ``".QMD"``
    both register as ``".qmd"``).
    """
    for ext in extensions:
        key = ext.lower()
        if not key.startswith("."):
            key = "." + key
        LOADERS[key] = loader


def load(path: str) -> RawDoc | None:
    """Load one source file into a :class:`RawDoc`, or return ``None``.

    From the caller's perspective ``None`` has EXACTLY ONE meaning: "skip this
    path (log it as unindexed)." That single caller-facing meaning covers all of:

    * the file is empty (0 bytes) or whitespace-only,
    * the file is unreadable or its bytes are undecodable as UTF-8 text,
    * no loader is registered for the file's extension (UNMAPPED),
    * a loader *is* registered for the extension but returns ``None`` for this
      specific file (i.e. "I claim this extension but reject this file" -- e.g. a
      corrupt or unparseable document); ``load`` propagates that ``None`` as-is.

    Callers must treat ``None`` uniformly as "skip this path"; they cannot and must
    not distinguish empty from unreadable from unmapped from loader-rejected.
    """
    p = Path(path)
    suffix = p.suffix.lower()

    # Empty / whitespace-only / unreadable / undecodable -> None (single meaning).
    # Binary loader extensions (``.pdf``) skip the UTF-8 decode pre-read -- their
    # bytes are not text -- but still get the empty-file (0-byte) guard.
    # TODO: avoid double file read once loaders exist -- this pre-read decode check
    # reads the whole file, then the registered loader reads it again.
    try:
        if p.stat().st_size == 0:
            return None
        if suffix not in BINARY_EXTS and not p.read_text(encoding="utf-8").strip():
            return None
    except (OSError, UnicodeDecodeError):
        return None

    # .txt has a DYNAMIC destination, so it is not in the static registry: sniff the
    # file and route tabular content to the data-card loader, prose to the prose
    # loader. Imported lazily to avoid an import cycle (both loader modules import
    # from this module). The empty/whitespace guard above already handled the None
    # case, so a non-None return here is a genuine loader result.
    if suffix == ".txt":
        from .data_card import data_card_loader, looks_like_data
        from .prose import prose_loader

        if looks_like_data(path):
            return data_card_loader(path)
        return prose_loader(path)

    loader = LOADERS.get(suffix)
    if loader is None:
        return None
    return loader(path)
