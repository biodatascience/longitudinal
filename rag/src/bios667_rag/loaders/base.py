"""The ``RawDoc`` value object produced by every format loader.

A loader's job is to read one source file and return a ``RawDoc`` carrying the raw
extracted ``text`` plus provenance (``source_path``, ``source_type``) and any
format-native metadata (e.g. YAML front matter) it parsed out. Downstream chunking
and ``ChunkMeta`` construction consume ``RawDoc`` instances, not raw files.
"""

from dataclasses import dataclass, field


@dataclass
class RawDoc:
    """Raw extracted text for one source file, before chunking.

    ``native_metadata`` holds format-native key/values a loader parsed (e.g. Quarto
    YAML front matter); it defaults to an empty dict via ``field(default_factory)``
    so each instance owns its own dict rather than sharing a mutable default.
    """

    text: str
    source_path: str
    source_type: str
    native_metadata: dict = field(default_factory=dict)
