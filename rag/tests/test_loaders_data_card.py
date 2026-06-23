"""Tests for the data-card loader (``.dat`` / ``.csv``) and ``looks_like_data``.

The whole point of a data card is that we do NOT embed raw data rows (privacy +
the fact that a wall of numbers embeds terribly). Instead the loader builds a
compact natural-language DESCRIPTION -- filename, delimiter, dimensions, column
names, inferred dtypes, and AT MOST the first 3 rows as examples -- so a query
like "six cities FEV1 dataset" can find the file by its description.

The most load-bearing test pins the no-raw-rows guarantee: a UNIQUE sentinel value
placed only in row 8 (well past ``head(3)``) must NOT appear in ``rd.text``.

``looks_like_data`` is a pure delimiter/numeric sniffer used by the ``.txt``
dispatch (Task 2.8) to route data-vs-prose; it is tested standalone here.
"""

from bios667_rag.loaders.data_card import data_card_loader, looks_like_data
from bios667_rag.loaders.dispatch import load

# Header + 12 data rows. The sentinel (id=9999, distance=42424242) lives ONLY in
# row 8 (index 7), well past head(3), so we can assert it never leaks into text.
_CSV = (
    "id,age,distance,sex\n"
    "1,8,21.0,F\n"
    "2,8,20.0,M\n"
    "3,8,21.5,F\n"
    "4,10,22.0,M\n"
    "5,10,23.0,F\n"
    "6,10,24.5,M\n"
    "7,12,25.0,F\n"
    "9999,12,42424242,M\n"  # row 8: UNIQUE sentinel, must NOT leak
    "9,12,26.0,F\n"
    "10,14,27.5,M\n"
    "11,14,28.0,F\n"
    "12,14,29.0,M\n"
)

_SENTINEL_ID = "9999"
_SENTINEL_DISTANCE = "42424242"

_DAT = (
    "1.0 2.0 3.0\n"
    "4.0 5.0 6.0\n"
    "7.0 8.0 9.0\n"
    "10.0 11.0 12.0\n"
)

_PROSE = (
    "Longitudinal data analysis studies repeated measurements over time.\n"
    "The six cities study followed children and recorded their lung function.\n"
    "This paragraph contains no consistent delimiter and is mostly words.\n"
)


def _write(tmp_path, name, content):
    f = tmp_path / name
    f.write_text(content)
    return str(f)


def test_looks_like_data_true_for_csv(tmp_path):
    p = _write(tmp_path, "dental.csv", _CSV)
    assert looks_like_data(p) is True


def test_looks_like_data_true_for_whitespace_dat(tmp_path):
    p = _write(tmp_path, "rat.dat", _DAT)
    assert looks_like_data(p) is True


def test_looks_like_data_false_for_prose(tmp_path):
    p = _write(tmp_path, "notes.txt", _PROSE)
    assert looks_like_data(p) is False


def test_csv_source_type(tmp_path):
    p = _write(tmp_path, "dental.csv", _CSV)
    rd = data_card_loader(p)
    assert rd is not None
    assert rd.source_type == "data_card"


def test_csv_text_has_columns_dims_and_delimiter(tmp_path):
    p = _write(tmp_path, "dental.csv", _CSV)
    rd = data_card_loader(p)
    # all column names present
    for col in ("id", "age", "distance", "sex"):
        assert col in rd.text
    # dimensions present
    assert "12" in rd.text  # n_rows
    assert "4" in rd.text  # n_cols
    # filename referenced
    assert "dental.csv" in rd.text


def test_csv_no_raw_rows_beyond_head3_leak(tmp_path):
    """CRITICAL: data rows past head(3) must never appear in the card text."""
    p = _write(tmp_path, "dental.csv", _CSV)
    rd = data_card_loader(p)
    # The sentinel lives only in row 8 -- it must NOT leak.
    assert _SENTINEL_ID not in rd.text
    assert _SENTINEL_DISTANCE not in rd.text
    # At most 3 example data rows: a later data row (row 4, id=4 distance 22.0)
    # must also be absent.
    assert "22.0" not in rd.text  # row 4's distance
    # And head(3) examples ARE present.
    assert "21.0" in rd.text  # row 1's distance


def test_csv_native_metadata(tmp_path):
    p = _write(tmp_path, "dental.csv", _CSV)
    rd = data_card_loader(p)
    assert rd.native_metadata["n_rows"] == 12
    assert rd.native_metadata["n_cols"] == 4
    assert rd.native_metadata["columns"] == ["id", "age", "distance", "sex"]
    assert "delimiter" in rd.native_metadata


def test_dat_loads_as_data_card(tmp_path):
    p = _write(tmp_path, "rat.dat", _DAT)
    rd = data_card_loader(p)
    assert rd is not None
    assert rd.source_type == "data_card"
    assert rd.native_metadata["n_rows"] == 4
    assert rd.native_metadata["n_cols"] == 3


def test_dispatch_load_reaches_data_card_loader(tmp_path):
    p = _write(tmp_path, "dental.csv", _CSV)
    rd = load(p)
    assert rd is not None
    assert rd.source_type == "data_card"
    assert rd.native_metadata["n_cols"] == 4


# Ragged rows: no consistent delimiter yields a >=2-col grid, so _sniff_delimiter
# falls back to the _WHITESPACE sentinel and re-splitting leaves ragged rows.
_RAGGED = (
    "alpha beta gamma\n"
    "one two\n"
    "x y z w\n"
)

# Single column: every line splits into exactly one field under every delimiter.
_SINGLE_COL = (
    "alpha\n"
    "beta\n"
    "gamma\n"
)


def test_data_card_loader_returns_none_for_ragged_rows(tmp_path):
    p = _write(tmp_path, "ragged.dat", _RAGGED)
    assert data_card_loader(p) is None


def test_data_card_loader_returns_none_for_single_column(tmp_path):
    p = _write(tmp_path, "single.dat", _SINGLE_COL)
    assert data_card_loader(p) is None
