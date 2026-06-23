"""Tests for the code loader (``.sas`` / ``.r``).

Pins the NL-header construction (leading comment + detected procedures/functions),
its placement at the top of ``text`` (so the chunker can rely on it), role-based
``source_type`` classification, and registration so dispatch ``load`` reaches it.
"""

from bios667_rag.loaders.code import code_loader
from bios667_rag.loaders.dispatch import load

_SAS = (
    "/* Six cities random intercept */\n"
    "proc sort data=six; by id; run;\n"
    "proc mixed data=six;\n"
    "  class id;\n"
    "  model fev = age;\n"
    "  random intercept / subject=id;\n"
    "run;\n"
)

_R = (
    "# Fit LME model\n"
    "library(lme4)\n"
    "f <- function(d) lmer(y ~ x, d)\n"
)


def test_sas_source_type(tmp_path):
    f = tmp_path / "6city_demo.sas"
    f.write_text(_SAS)
    rd = code_loader(str(f))
    assert rd is not None
    assert rd.source_type == "sas"


def test_sas_nl_header_has_proc_and_comment(tmp_path):
    f = tmp_path / "6city_demo.sas"
    f.write_text(_SAS)
    rd = code_loader(str(f))
    header = rd.native_metadata["nl_header"]
    assert "mixed" in header  # procedure detected
    assert "sort" in header  # second procedure detected
    assert "six cities" in header.lower()  # leading comment referenced


def test_sas_text_starts_with_header_and_contains_code(tmp_path):
    f = tmp_path / "6city_demo.sas"
    f.write_text(_SAS)
    rd = code_loader(str(f))
    header = rd.native_metadata["nl_header"]
    assert rd.text.startswith(header)
    assert "proc mixed" in rd.text  # raw code preserved verbatim


def test_r_source_type_and_header(tmp_path):
    f = tmp_path / "fit.r"
    f.write_text(_R)
    rd = code_loader(str(f))
    assert rd is not None
    assert rd.source_type == "rcode"
    header = rd.native_metadata["nl_header"]
    # header mentions the library or function or comment
    assert ("lme4" in header) or ("function" in header.lower()) or (
        "fit lme" in header.lower()
    )
    assert rd.text.startswith(header)
    assert "lmer(y ~ x, d)" in rd.text


def test_r_header_detects_function_name(tmp_path):
    f = tmp_path / "fit.r"
    f.write_text(_R)
    rd = code_loader(str(f))
    header = rd.native_metadata["nl_header"]
    assert "Functions/libraries: f" in header  # top-level function name detected
    assert "lme4" in header  # library detected


def test_dispatch_load_reaches_sas_loader(tmp_path):
    f = tmp_path / "6city_demo.sas"
    f.write_text(_SAS)
    rd = load(str(f))
    assert rd is not None
    assert rd.source_type == "sas"
    assert "mixed" in rd.native_metadata["nl_header"]


def test_dispatch_load_reaches_r_loader(tmp_path):
    f = tmp_path / "fit.r"
    f.write_text(_R)
    rd = load(str(f))
    assert rd is not None
    assert rd.source_type == "rcode"


def test_sas_no_comment_no_proc_still_returns_rawdoc(tmp_path):
    f = tmp_path / "plain.sas"
    f.write_text("data x;\n  set y;\nrun;\n")
    rd = code_loader(str(f))
    assert rd is not None
    assert rd.source_type == "sas"
    header = rd.native_metadata["nl_header"]
    assert "SAS" in header  # minimal header still present
    assert rd.text.startswith(header)
    assert "data x;" in rd.text


def test_r_no_comment_no_function_still_returns_rawdoc(tmp_path):
    f = tmp_path / "plain.r"
    f.write_text("x <- 1\nprint(x)\n")
    rd = code_loader(str(f))
    assert rd is not None
    assert rd.source_type == "rcode"
    header = rd.native_metadata["nl_header"]
    assert "R" in header
    assert rd.text.startswith(header)
    assert "print(x)" in rd.text
