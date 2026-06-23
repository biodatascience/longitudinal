"""Data-card loader for tabular files (``.dat`` / ``.csv``) plus a pure
``looks_like_data`` sniffer.

We deliberately do NOT embed raw data rows. Two reasons: privacy (course data may
carry identifiers) and signal -- a wall of numbers embeds terribly, so a query like
"six cities FEV1 dataset" would never retrieve a file indexed as raw rows. Instead
we synthesize a compact natural-language DESCRIPTION (a "data card"): filename,
detected delimiter, dimensions, column names, inferred per-column dtypes, and AT
MOST the first 3 rows as concrete examples. That description is what gets embedded.

Two public functions:

* :func:`looks_like_data` -- a PURE helper (no ``RawDoc``). It reads the first ~20
  lines, sniffs a single consistent delimiter, and returns ``True`` iff the rows
  have >= 2 columns AND are numeric-dominant. Task 2.8 calls this on ``.txt`` files
  to decide data-vs-prose routing, so it must be importable and standalone.
* :func:`data_card_loader` -- builds the ``RawDoc`` card. It is only ever invoked on
  files already known to be tabular (dispatch guarantees this for ``.txt``;
  ``.dat``/``.csv`` route here directly via the registry).

``source_type`` is always ``"data_card"``: this loader is only ever invoked on files
already known to be tabular, so it pins the role directly rather than deriving it from
the path (which cannot sniff a tabular ``.txt``).
"""

from pathlib import Path

from .base import RawDoc
from .dispatch import register

# How many leading lines to sample when sniffing the delimiter / numeric dominance.
_SNIFF_LINES = 20

# Number of example data rows allowed in the card. NEVER raise this without
# revisiting the privacy guarantee in the module docstring -- the whole point of a
# card is that bulk rows do not leak into the embedded text.
_HEAD_N = 3

# Candidate delimiters, tried in priority order. Whitespace is the fallback: a run
# of spaces/tabs (handled specially via ``str.split()`` with no argument).
_COMMA = ","
_TAB = "\t"
_WHITESPACE = None  # sentinel: split on arbitrary runs of whitespace


def _read_lines(path: str, limit: int | None = None) -> list[str]:
    """Return non-empty, stripped text lines from ``path`` (up to ``limit``)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if s:
            lines.append(s)
            if limit is not None and len(lines) >= limit:
                break
    return lines


def _split(line: str, delimiter: str | None) -> list[str]:
    """Split ``line`` on ``delimiter`` (``None`` => arbitrary whitespace runs)."""
    if delimiter is _WHITESPACE:
        return line.split()
    return [c.strip() for c in line.split(delimiter)]


def _is_number(cell: str) -> bool:
    """True iff ``cell`` parses as a float (covers ints, decimals, sci-notation)."""
    if cell == "":
        return False
    try:
        float(cell)
        return True
    except ValueError:
        return False


def _sniff_delimiter(lines: list[str]) -> str | None:
    """Pick the delimiter that splits the sampled lines into a consistent, >=2-column
    grid, or return ``None`` if none does.

    A delimiter is "consistent" when every sampled line splits into the SAME number
    of fields and that count is >= 2. Comma and tab are preferred over whitespace
    (whitespace also matches comma/tab-free numeric tables, so it is the fallback).

    Returns the chosen delimiter: ``","``, ``"\\t"``, or the ``_WHITESPACE`` sentinel
    (``None``) for whitespace. NOTE: the ``_WHITESPACE`` sentinel and the
    no-consistent-grid case BOTH return ``None``, so the return value alone cannot
    distinguish them. Callers must re-split on the result and inspect the resulting
    grid (consistent column count >= 2) to confirm an actual table; both
    :func:`looks_like_data` and :func:`data_card_loader` do exactly this.
    """
    if not lines:
        return None
    for delim in (_COMMA, _TAB, _WHITESPACE):
        counts = {len(_split(line, delim)) for line in lines}
        if len(counts) == 1:
            (ncols,) = tuple(counts)
            if ncols >= 2:
                return delim
    return None


def looks_like_data(path: str) -> bool:
    """Return ``True`` iff ``path`` looks like a numeric-dominant tabular file.

    Pure helper (no ``RawDoc``). Reads the first ~20 non-empty lines, sniffs a single
    consistent delimiter, and returns ``True`` only when the grid has >= 2 columns AND
    is numeric-dominant: most cells across the sampled DATA rows (a leading header row,
    if present, is excluded) parse as numbers. Prose -- inconsistent field counts or
    mostly non-numeric cells -- returns ``False``.
    """
    lines = _read_lines(path, limit=_SNIFF_LINES)
    if len(lines) < 2:
        return False

    delim = _sniff_delimiter(lines)
    # _sniff_delimiter returns the _WHITESPACE sentinel (None) BOTH for a whitespace
    # table and for "no consistent delimiter found". Re-derive the column grid to
    # disambiguate: a real table has a consistent count >= 2; prose collapses to <2
    # or ragged counts.
    rows = [_split(line, delim) for line in lines]
    ncols = len(rows[0])
    if ncols < 2 or any(len(r) != ncols for r in rows):
        return False

    # Exclude a leading header row (all-non-numeric) from the numeric-dominance vote
    # so a numeric table with string column names still counts as data.
    data_rows = rows
    if rows and not any(_is_number(c) for c in rows[0]):
        data_rows = rows[1:]
    if not data_rows:
        return False

    total = sum(len(r) for r in data_rows)
    numeric = sum(_is_number(c) for r in data_rows for c in r)
    return total > 0 and numeric >= 0.6 * total


def _delimiter_name(delim: str | None) -> str:
    """Human-readable delimiter label for the card text."""
    if delim == _COMMA:
        return "comma"
    if delim == _TAB:
        return "tab"
    return "whitespace"


def _infer_dtype(values: list[str]) -> str:
    """Infer a coarse column dtype from sampled string ``values``.

    ``integer`` if every value is an integer literal, ``numeric`` if every value
    parses as a float (but not all integers), else ``categorical``.
    """
    vals = [v for v in values if v != ""]
    if not vals:
        return "categorical"
    if all(_is_number(v) for v in vals):
        if all(_is_int_literal(v) for v in vals):
            return "integer"
        return "numeric"
    return "categorical"


def _is_int_literal(cell: str) -> bool:
    """True iff ``cell`` is an integer literal (no decimal point / exponent)."""
    try:
        int(cell)
        return True
    except ValueError:
        return False


def data_card_loader(path: str) -> RawDoc | None:
    """Load a tabular file into a compact data-card :class:`RawDoc`, or ``None``.

    Builds a natural-language description (filename, delimiter, dimensions, column
    names, per-column dtypes, and AT MOST the first 3 data rows). Raw rows beyond
    ``head(3)`` are NEVER written into ``text`` -- see the module docstring.
    """
    lines = _read_lines(path)
    if not lines:
        return None

    delim = _sniff_delimiter(lines)
    rows = [_split(line, delim) for line in lines]

    # Guard against non-tabular input. _sniff_delimiter returns the _WHITESPACE
    # sentinel (None) BOTH for a whitespace table and for "no consistent delimiter
    # found", so re-splitting can leave a ragged or single-column grid. A card built
    # from such rows would be meaningless (and could misalign column<->value pairs),
    # so return None -- consistent with the empty-file None above and the loader
    # contract (callers treat None as "not loadable here").
    ncols = len(rows[0])
    if ncols < 2 or any(len(r) != ncols for r in rows):
        return None

    # Detect a header: a leading row with no numeric cells gives the column names.
    has_header = bool(rows) and not any(_is_number(c) for c in rows[0])
    if has_header:
        columns = rows[0]
        data_rows = rows[1:]
    else:
        columns = [f"V{i + 1}" for i in range(ncols)]
        data_rows = rows

    n_rows = len(data_rows)
    n_cols = len(columns)

    # Per-column dtypes inferred from the data rows.
    dtypes = []
    for j in range(n_cols):
        col_vals = [r[j] for r in data_rows if j < len(r)]
        dtypes.append(_infer_dtype(col_vals))

    delim_name = _delimiter_name(delim)
    filename = Path(path).name

    # Only the first _HEAD_N data rows become examples. Bulk rows never appear.
    examples = data_rows[:_HEAD_N]

    col_lines = [
        f"  - {name} ({dtype})" for name, dtype in zip(columns, dtypes)
    ]
    example_lines = [
        "  " + ", ".join(
            f"{name}={val}" for name, val in zip(columns, row)
        )
        for row in examples
    ]

    text = (
        f"Data file: {filename}\n"
        f"Delimiter: {delim_name}\n"
        f"Dimensions: {n_rows} rows x {n_cols} columns\n"
        f"Columns ({n_cols}):\n"
        + "\n".join(col_lines)
        + f"\nExample rows (first {len(examples)} of {n_rows}):\n"
        + "\n".join(example_lines)
    )

    # This loader is invoked ONLY on files already known to be tabular: ``.dat``/
    # ``.csv`` route here directly (classify_source_type -> "data_card") and ``.txt``
    # arrives only after dispatch's ``looks_like_data`` sniff. So the card's role is
    # always "data_card". We pin it directly rather than via classify_source_type,
    # which is path-only and would mis-classify a tabular ``.txt`` as the default
    # "lecture" (it has no way to sniff the content).
    return RawDoc(
        text=text,
        source_path=path,
        source_type="data_card",
        native_metadata={
            "columns": columns,
            "n_rows": n_rows,
            "n_cols": n_cols,
            "delimiter": delim_name,
            "dtypes": dtypes,
        },
    )


register(".dat", ".csv", loader=data_card_loader)
