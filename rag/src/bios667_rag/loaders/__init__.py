"""Format loaders for the course corpus.

Exposes the ``RawDoc`` value object plus the dispatch ``load`` entry point and the
``LOADERS``/``register`` registry mechanism that later tasks populate with concrete
per-format loaders.
"""

from .base import RawDoc
from .dispatch import LOADERS, load, register

# Import concrete loaders for their import-time ``register`` side effects so that
# ``load`` can dispatch to them. Each loader module registers its extensions on import.
from . import quarto  # noqa: F401  (side-effect import: registers .qmd/.rmd)
from . import code  # noqa: F401  (side-effect import: registers .sas/.r)
from . import data_card  # noqa: F401  (side-effect import: registers .dat/.csv)
from . import pdf  # noqa: F401  (side-effect import: registers .pdf)
from . import office  # noqa: F401  (side-effect import: registers .docx/.pptx)
from . import latex  # noqa: F401  (side-effect import: registers .tex)
from . import prose  # noqa: F401  (side-effect import: registers .md; .txt routed in load)

__all__ = ["RawDoc", "LOADERS", "load", "register"]
