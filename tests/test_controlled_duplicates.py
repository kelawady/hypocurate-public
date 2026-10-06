"""Step 1: the controlled duplicate extract (PRD Sections 5.3, 10 and 14.1)."""
import csv
import importlib.util
import re
from collections import Counter

import pytest

from hypocurate.sources.manifest import REPO_ROOT, load_manifest, sha256_file

MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
EXTRACT = REPO_ROOT / "data/controlled_duplicates/extract.csv"
FIXTURES = REPO_ROOT / "tests/fixtures/controlled_duplicates"
TRUTH = FIXTURES / "truth.csv"
# Pinned here, outside data/, so the answer file cannot change without changing a test.
# Step 6 (owner, 2026-10-05): the restored survivor wording and decision C (rows 7-8 are a conflict).
# Owner, 2026-10-06: rows 15-16 describe the reference plan with its test-type rule (tension only),
# their explanation included (after the step 6 review).
TRUTH_SHA256 = "0503f2b8e890c9d2c474beadfdd2f72f006b9cf817cd16495f494ac881242f9c"
# The frozen source files: fingerprint-pinned, and not written by us, so they
# cannot hold our answers. Everything else under data/ is scanned.
FROZEN_SOURCE_FILES = {
    "data/sources/mpea/MPEA_dataset.csv",
    "data/sources/mpea/LICENSE",
    "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
    "data/sources/tamu_fcc/inputs.csv",
    "data/sources/tamu_fcc/LICENSE",
}

_spec = importlib.util.spec_from_file_location("builder", FIXTURES / "build.py")
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


# --- no answer material under data/ or the package -----------------------------------
# A convention checked by content, not an access guarantee: enforcement is the
# approved-input-file list of the access layer (step 5).

def test_answer_material_is_not_under_data_or_the_package():
    for root in ("data", "hypocurate"):
        assert not list((REPO_ROOT / root).rglob("*truth*"))
        assert not list((REPO_ROOT / root).rglob("build*.py"))


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=\.)\s+", text) if len(s.strip()) > 30]


def _row_specific_markers():
    """Answer material tied to particular extract rows."""
    markers = {"extract_row", "mpea_row", "survivor_in_primary", "truth.csv", "fixtures/controlled_duplicates"}
    for t in TRUTH_ROWS:
        markers |= {t["case"], t["explanation"], t["survivor_in_primary"]}
        markers |= set(_sentences(t["explanation"]))
    return markers


def _generic_outcome_markers():
    """Outcome vocabulary: forbidden under data/, allowed in the package (step 6 uses it)."""
    markers = {"exact_duplicate", "possible_duplicate", "not_duplicate",
               "counted once", "both enter", "both counted separately"}
    markers |= {c for c in builder.TRUTH_COLUMNS if "_" in c}
    for t in TRUTH_ROWS:
        markers |= {t["prd_5_3_class"], t["survivor_reason"], t["survivor_rule"]}
        markers |= {t[c] for c in ("primary_analysis", "sensitivity_analysis") if " " in t[c]}
    return markers


def _scanned_files(root):
    for path in sorted((REPO_ROOT / root).rglob("*")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if path.is_file() and rel not in FROZEN_SOURCE_FILES and "__pycache__" not in path.parts:
            yield rel, path.read_text(encoding="utf-8").lower()


def test_no_expected_outcomes_under_data():
    markers = {m.lower() for m in _row_specific_markers() | _generic_outcome_markers()}
    scanned = 0
    for rel, text in _scanned_files("data"):
        scanned += 1
        found = sorted(m for m in markers if m in text)
        assert not found, f"{rel} contains expected-outcome material: {found}"
    assert scanned >= 3  # manifest, extract, README


def test_no_row_answers_under_package():
    markers = {m.lower() for m in _row_specific_markers()}
    scanned = 0
    for rel, text in _scanned_files("hypocurate"):
        scanned += 1
        found = sorted(m for m in markers if m in text)
        assert not found, f"{rel} contains row-specific answer material: {found}"
    assert scanned >= 3


def _strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)
    elif isinstance(obj, str):
        yield obj


def test_manifest_points_to_nothing_holding_answers():
    for s in _strings(load_manifest()):
        assert "tests/" not in s and "scripts/" not in s and "fixtures" not in s, s


def test_extract_carries_no_answer_columns():
    assert EXTRACT_HEADER == MPEA_HEADER


# --- content matches the stated construction ---------------------------------------

def test_one_answer_per_extract_row():
    assert len(EXTRACT_ROWS) == len(TRUTH_ROWS) == 16
    assert [int(t["extract_row"]) for t in TRUTH_ROWS] == list(range(1, 17))


def test_every_case_is_present_twice():
    assert Counter(t["case"] for t in TRUTH_ROWS) == {
        "exact_duplicate_verbatim": 2,
        "exact_duplicate_renamed_alloy": 2,
        "possible_duplicate_unknown_paper": 2,
        "conflict_value_differs": 2,
        "not_duplicate_other_paper": 2,
        "not_duplicate_other_temperature": 2,
        "missing_test_condition": 2,
        "not_duplicate_other_test_type": 2,
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
        if t["case"] == "conflict_value_differs":
            assert float(row[ys]) == pytest.approx(1.3 * float(src[ys]), abs=0.05)
        if t["case"] == "not_duplicate_other_temperature":
            assert float(row[temp]) == -196.0


def test_missing_test_condition_rows_keep_their_paper():
    """Distinct from the missing-paper case: the paper is known, the test temperature is not."""
    temp = COL["PROPERTY: Test temperature ($^\\circ$C)"]
    rows = [t for t in TRUTH_ROWS if t["case"] == "missing_test_condition"]
    assert len(rows) == 2
    for t in rows:
        src, row = MPEA_ROWS[int(t["mpea_row"])], EXTRACT_ROWS[int(t["extract_row"]) - 1]
        assert row[temp] == "" and src[temp] != ""
        assert row[COL["REFERENCE: doi"]] == src[COL["REFERENCE: doi"]] != ""
        assert t["prd_5_3_class"] == "Difference explained by missing metadata: scope cannot be confirmed"


def test_other_test_type_rows_are_compression_copies_of_tension_records():
    tt = COL["PROPERTY: Type of test"]
    rows = [t for t in TRUTH_ROWS if t["case"] == "not_duplicate_other_test_type"]
    assert len(rows) == 2
    for t in rows:
        src, row = MPEA_ROWS[int(t["mpea_row"])], EXTRACT_ROWS[int(t["extract_row"]) - 1]
        assert (src[tt], row[tt]) == ("T", "C")
        assert t["duplicate_status"] == "not_duplicate"  # known different, not a possible duplicate
        # The reference plan accepts tension only (owner, 2026-10-05): the compression copy is out of scope.
        assert t["prd_5_3_class"] == "Incompatible measurements: outside the plan's scope (test-type rule: tension only)"
        assert t["primary_analysis"] == "not eligible: excluded by the test-type rule (tension only)"
        assert "accepts tension tests only, so this record is out of scope" in t["explanation"]
        assert "sets no test-type rule" not in t["explanation"]
        # Under a tension-only plan the compression record is out of scope.
        assert t["handling_under_tension_only_plan"] == (
            "excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements')")


def test_no_row_is_labelled_out_of_scope_while_entering_the_analysis():
    """A row's PRD 5.3 class and its primary handling must describe the same plan."""
    for t in TRUTH_ROWS:
        if t["prd_5_3_class"].startswith("Incompatible measurements"):
            assert t["primary_analysis"].startswith("not eligible"), t["extract_row"]


def test_tension_only_handling_differs_only_for_compression_rows():
    for t in TRUTH_ROWS:
        if t["case"] != "not_duplicate_other_test_type":
            assert t["handling_under_tension_only_plan"] == "same as under the reference plan"


# --- the expected answers follow PRD 5.3 ------------------------------------------

EXPECTED = {
    "exact_duplicate_verbatim": ("exact_duplicate", "counted once", "none"),
    "exact_duplicate_renamed_alloy": ("exact_duplicate", "counted once", "none"),
    # Step 7b (owner, 2026-10-06): no paper reference, so no group: not eligible in any set.
    "possible_duplicate_unknown_paper": ("possible_duplicate", "not eligible: no group (paper reference missing)",
                                         "none"),
    # Decision C (owner, 2026-10-05; corrects PRD 5.3, which contradicted CLAUDE.md rule 4).
    "conflict_value_differs": ("conflict", "neither enters: conflict unresolved",
                               "counted once in conflicts_survivor_value"),
    "not_duplicate_other_paper": ("not_duplicate", "both enter", "none"),
    "not_duplicate_other_temperature": ("not_duplicate", "not eligible under a room-temperature plan", "none"),
    "missing_test_condition": ("possible_duplicate", "not eligible: scope not confirmed", "included"),
    "not_duplicate_other_test_type": (
        "not_duplicate", "not eligible: excluded by the test-type rule (tension only)", "none"),
}

SURVIVOR_RULE = (
    "1) prefer the record that carries the original paper reference (DOI); "
    "2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; "
    "3) within one source, the lowest row number"
)


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
        assert "no group is invented (owner, 2026-10-06)" in t["explanation"]  # step 7b
        assert t["survivor_reason"].endswith("not eligible in any case (no group: the paper reference is missing)")


# --- which record survives in the primary analysis (owner's rule, 2026-10-04) ------

@pytest.mark.parametrize("t", TRUTH_ROWS, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_survivor_is_stated(t):
    assert t["survivor_rule"] == SURVIVOR_RULE
    if t["duplicate_status"] in ("exact_duplicate", "possible_duplicate"):
        # Every pair in the extract: the MPEA record survives.
        assert t["survivor_in_primary"] == f"MPEA row {t['mpea_row']}"
        src = MPEA_ROWS[int(t["mpea_row"])]
        row = EXTRACT_ROWS[int(t["extract_row"]) - 1]
        doi = COL["REFERENCE: doi"]
        if row[doi] == "":
            assert t["survivor_reason"].startswith("rule 1:")  # only the MPEA record carries the paper's DOI
        else:
            assert row[doi] == src[doi]
            assert t["survivor_reason"].startswith("rule 2:")  # both carry it; MPEA is first in order
    elif t["duplicate_status"] == "conflict":
        # Decision C: neither enters the primary analysis; the sensitivity analysis counts the
        # pair once by the survivor rule (both carry the paper's DOI; MPEA is first in order).
        assert t["survivor_in_primary"] == "none: neither enters the primary analysis"
        assert "conflicts_survivor_value" in t["survivor_reason"] and "rule 2:" in t["survivor_reason"]
    else:
        assert t["survivor_in_primary"] == "no pair: both kept"
