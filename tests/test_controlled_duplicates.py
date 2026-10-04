"""Step 1: the controlled duplicate extract (PRD Sections 5.3, 10 and 14.1)."""
import csv
import importlib.util
import re
from collections import Counter

import pytest

from hypocurate.sources.manifest import REPO_ROOT, load_manifest, sha256_file

MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
EXTRACT = REPO_ROOT / "data/controlled_duplicates/extract.csv"
TRUTH = REPO_ROOT / "tests/fixtures/controlled_duplicates_truth.csv"
# Pinned here, outside data/, so the answer file cannot change without changing a test.
TRUTH_SHA256 = "b5742da9c5118f52c78d62325b02164033a422e0e5a602212363abf40a3692a6"

_spec = importlib.util.spec_from_file_location("builder", REPO_ROOT / "scripts/build_controlled_duplicates.py")
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


MPEA_HEADER, MPEA_ROWS = read_csv(MPEA_CSV)
EXTRACT_HEADER, EXTRACT_ROWS = read_csv(EXTRACT)
with open(TRUTH, newline="", encoding="utf-8") as _f:
    TRUTH_ROWS = list(csv.DictReader(_f))
COL = {name: i for i, name in enumerate(MPEA_HEADER)}


def composition(formula):
    """Atomic percent by element; the same arithmetic as docs/reference/worked_example.py."""
    comp = {}
    for el, n in re.findall(r"([A-Z][a-z]?)([0-9.]*)", formula):
        comp[el] = comp.get(el, 0) + (float(n) if n else 1.0)
    total = sum(comp.values())
    return {el: round(100 * v / total, 1) for el, v in comp.items()}


# --- reproducible and fingerprinted ---------------------------------------------

def test_rebuild_gives_identical_bytes():
    extract, truth = builder.build(MPEA_CSV)
    assert extract == EXTRACT.read_text(encoding="utf-8")
    assert truth == TRUTH.read_text(encoding="utf-8")


def test_extract_fingerprint_is_in_the_manifest():
    files = load_manifest()["controlled_duplicates"]["files"]
    assert [f["path"] for f in files] == ["data/controlled_duplicates/extract.csv"]
    assert sha256_file(EXTRACT) == files[0]["sha256"]


def test_truth_fingerprint():
    assert sha256_file(TRUTH) == TRUTH_SHA256


# --- the answer file is out of the pipeline's reach --------------------------------

def test_answer_file_is_not_under_data_or_the_package():
    assert not list((REPO_ROOT / "data").rglob("*truth*"))
    assert not list((REPO_ROOT / "hypocurate").rglob("*truth*"))


def test_no_package_code_or_data_refers_to_the_answer_file():
    for path in list((REPO_ROOT / "hypocurate").rglob("*.py")) + list((REPO_ROOT / "data").rglob("*")):
        if path.is_file() and path.suffix in {".py", ".json", ".csv", ".md"}:
            assert "controlled_duplicates_truth" not in path.read_text(encoding="utf-8"), path


def test_extract_carries_no_answer_columns():
    assert EXTRACT_HEADER == MPEA_HEADER


# --- content matches the stated construction ---------------------------------------

def test_one_answer_per_extract_row():
    assert len(EXTRACT_ROWS) == len(TRUTH_ROWS) == 12
    assert [int(t["extract_row"]) for t in TRUTH_ROWS] == list(range(1, 13))


def test_every_case_is_present_twice():
    assert Counter(t["case"] for t in TRUTH_ROWS) == {
        "exact_duplicate_verbatim": 2,
        "exact_duplicate_renamed_alloy": 2,
        "possible_duplicate_unknown_paper": 2,
        "not_duplicate_value_differs": 2,
        "not_duplicate_other_paper": 2,
        "not_duplicate_other_temperature": 2,
    }


@pytest.mark.parametrize("t", TRUTH_ROWS, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_row_differs_from_its_source_in_exactly_the_stated_columns(t):
    src = MPEA_ROWS[int(t["mpea_row"])]
    row = EXTRACT_ROWS[int(t["extract_row"]) - 1]
    assert src[COL["IDENTIFIER: Reference ID"]] == t["mpea_reference_id"]
    assert src[COL["REFERENCE: doi"]] == t["mpea_doi"]
    changed = {MPEA_HEADER[i] for i, (a, b) in enumerate(zip(src, row)) if a != b}
    stated = set(t["changed_columns"].split("; ")) - {""}
    assert changed == stated


def test_source_rows_are_in_reference_scope():
    """Each source row is FCC, room temperature, with grain size >= 0.1 um and yield strength."""
    for t in TRUTH_ROWS:
        src = MPEA_ROWS[int(t["mpea_row"])]
        assert src[COL["PROPERTY: Microstructure"]] == "FCC"
        assert 20 <= float(src[COL["PROPERTY: Test temperature ($^\\circ$C)"]]) <= 25
        assert float(src[COL["PROPERTY: grain size ($\\mu$m)"]]) >= 0.1
        assert src[COL["PROPERTY: YS (MPa)"]] != ""
    assert len({t["mpea_doi"] for t in TRUTH_ROWS}) == 8


def test_verbatim_duplicates_are_byte_identical_lines():
    mpea_lines = MPEA_CSV.read_text(encoding="utf-8").split("\n")[1:]
    extract_lines = EXTRACT.read_text(encoding="utf-8").split("\n")[1:]
    for t in TRUTH_ROWS:
        if t["case"] == "exact_duplicate_verbatim":
            assert extract_lines[int(t["extract_row"]) - 1] == mpea_lines[int(t["mpea_row"])]


def test_renamed_alloys_have_the_same_composition():
    f = COL["FORMULA"]
    for t in TRUTH_ROWS:
        if t["case"] == "exact_duplicate_renamed_alloy":
            src, row = MPEA_ROWS[int(t["mpea_row"])], EXTRACT_ROWS[int(t["extract_row"]) - 1]
            assert row[f] != src[f]
            assert composition(row[f]) == composition(src[f])


def test_unknown_paper_rows_have_no_reference():
    for t in TRUTH_ROWS:
        if t["case"] == "possible_duplicate_unknown_paper":
            row = EXTRACT_ROWS[int(t["extract_row"]) - 1]
            for name in ("IDENTIFIER: Reference ID", "REFERENCE: doi", "REFERENCE: year", "REFERENCE: title"):
                assert row[COL[name]] == ""


def test_other_paper_rows_use_constructed_dois_not_found_in_mpea():
    real_dois = {r[COL["REFERENCE: doi"]] for r in MPEA_ROWS}
    for t in TRUTH_ROWS:
        if t["case"] == "not_duplicate_other_paper":
            doi = EXTRACT_ROWS[int(t["extract_row"]) - 1][COL["REFERENCE: doi"]]
            assert doi.startswith("10.5555/hypocurate-test-")
            assert doi not in real_dois


def test_changed_values_are_as_stated():
    ys, temp = COL["PROPERTY: YS (MPa)"], COL["PROPERTY: Test temperature ($^\\circ$C)"]
    for t in TRUTH_ROWS:
        src, row = MPEA_ROWS[int(t["mpea_row"])], EXTRACT_ROWS[int(t["extract_row"]) - 1]
        if t["case"] == "not_duplicate_value_differs":
            assert float(row[ys]) == pytest.approx(1.3 * float(src[ys]), abs=0.05)
        if t["case"] == "not_duplicate_other_temperature":
            assert float(row[temp]) == -196.0


# --- the expected answers follow PRD 5.3 ------------------------------------------

EXPECTED = {
    "exact_duplicate_verbatim": ("exact_duplicate", "counted once", "none"),
    "exact_duplicate_renamed_alloy": ("exact_duplicate", "counted once", "none"),
    "possible_duplicate_unknown_paper": ("possible_duplicate", "counted once", "both counted separately"),
    "not_duplicate_value_differs": ("not_duplicate", "both enter", "none"),
    "not_duplicate_other_paper": ("not_duplicate", "both enter", "none"),
    "not_duplicate_other_temperature": ("not_duplicate", "not eligible under a room-temperature plan", "none"),
}


@pytest.mark.parametrize("t", TRUTH_ROWS, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_expected_handling(t):
    status, primary, sensitivity = EXPECTED[t["case"]]
    assert (t["duplicate_status"], t["primary_analysis"], t["sensitivity_analysis"]) == (status, primary, sensitivity)
    # Stored is not analysed: every record is kept and none is removed.
    assert t["kept_in_store"] == "yes"
    assert t["removed_from_store"] == "no"


def test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed():
    rows = [t for t in TRUTH_ROWS if t["case"] == "possible_duplicate_unknown_paper"]
    for t in rows:
        assert t["prd_5_3_class"] == "Possible duplicate that cannot be resolved"
        assert "Flagged as a possible duplicate, kept, not removed." in t["explanation"]
