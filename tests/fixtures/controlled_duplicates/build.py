"""Build the controlled duplicate extract and its answer file (PRD Sections 5.3, 10 and 14.1).

The two sprint sources share no measurements, so duplicate handling is tested on
a small extract built from the frozen MPEA dataset that overlaps it in a known
way. Every row of the extract is derived from one listed MPEA row, so the truth
is known by construction.

Outputs:
  data/controlled_duplicates/extract.csv           the extract, in the MPEA column layout
  tests/fixtures/controlled_duplicates/truth.csv   the expected answer per row

This builder and its case table hold the answers, so they live under tests/,
outside data/ and outside the hypocurate package: no part of the pipeline (and
so no agent) can read them. Nothing under data/ points here.

The build is deterministic: running it again on the frozen MPEA file gives the
same bytes, and a test checks that.

    python tests/fixtures/controlled_duplicates/build.py
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MPEA_PATH = REPO_ROOT / "data" / "sources" / "mpea" / "MPEA_dataset.csv"
EXTRACT_PATH = REPO_ROOT / "data" / "controlled_duplicates" / "extract.csv"
TRUTH_PATH = Path(__file__).resolve().parent / "truth.csv"

# MPEA column positions used below (header names in the frozen file).
REF_ID = 0  # IDENTIFIER: Reference ID (one value per paper)
FORMULA = 1  # FORMULA
TEST_TYPE = 9  # PROPERTY: Type of test (T = tension, C = compression)
TEMPERATURE = 10  # PROPERTY: Test temperature ($^\circ$C)
YS = 11  # PROPERTY: YS (MPa)
DOI = 20  # REFERENCE: doi
YEAR = 21  # REFERENCE: year
TITLE = 22  # REFERENCE: title

TEST_DOI_PREFIX = "10.5555/hypocurate-test-"  # 10.5555 is a test prefix; never a real paper here
CONSTRUCTED_TITLE = "Constructed record: HypoCurate controlled duplicate extract (not a real paper)"

KEPT = "yes"
NOT_REMOVED = "no"

# Owner's decision (2026-10-04): which record of a duplicate pair enters the
# primary analysis. Refines PRD 5.3 "the record from the original paper, or the
# first source in a fixed order if the origin is unknown".
SURVIVOR_RULE = (
    "1) prefer the record that carries the original paper reference (DOI); "
    "2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; "
    "3) within one source, the lowest row number"
)
BOTH_CARRY_PAPER = "rule 2: both records carry the paper reference; MPEA comes first in the fixed source order"
ONLY_MPEA_CARRIES_PAPER = "rule 1: only the MPEA record carries the paper reference"
NO_PAIR = "no pair: both kept"
NOT_SAME_MEASUREMENT = "not the same measurement"

# Each case: the PRD 5.3 class it exercises and the expected handling.
# `pair` says how the survivor is chosen: None when the two records are not the
# same measurement.
CASES = {
    "exact_duplicate_verbatim": dict(
        duplicate_status="exact_duplicate",
        prd_class="Exact duplicate: the same measurement reported by two sources",
        primary_analysis="counted once",
        sensitivity_analysis="none",
        pair=BOTH_CARRY_PAPER,
        explanation="Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions.",
    ),
    "exact_duplicate_renamed_alloy": dict(
        duplicate_status="exact_duplicate",
        prd_class="Exact duplicate: the same measurement reported by two sources",
        primary_analysis="counted once",
        sensitivity_analysis="none",
        pair=BOTH_CARRY_PAPER,
        explanation="Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition.",
    ),
    "possible_duplicate_unknown_paper": dict(
        duplicate_status="possible_duplicate",
        prd_class="Possible duplicate that cannot be resolved",
        primary_analysis="counted once",
        sensitivity_analysis="both counted separately",
        pair=ONLY_MPEA_CARRIES_PAPER,
        explanation="Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed.",
    ),
    "missing_test_condition": dict(
        duplicate_status="possible_duplicate",
        prd_class="Difference explained by missing metadata: scope cannot be confirmed",
        primary_analysis="not eligible: scope not confirmed",
        sensitivity_analysis="included",
        pair=BOTH_CARRY_PAPER + "; this record is not eligible in any case (scope not confirmed)",
        explanation="Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis.",
    ),
    "not_duplicate_value_differs": dict(
        duplicate_status="not_duplicate",
        prd_class="Comparable specimens and conditions; the values truly differ",
        primary_analysis="both enter",
        sensitivity_analysis="none",
        pair=None,
        explanation="Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate.",
    ),
    "not_duplicate_other_paper": dict(
        duplicate_status="not_duplicate",
        prd_class="Comparable specimens and conditions; the values truly differ",
        primary_analysis="both enter",
        sensitivity_analysis="none",
        pair=None,
        explanation="Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper.",
    ),
    "not_duplicate_other_temperature": dict(
        duplicate_status="not_duplicate",
        prd_class="Incompatible measurements: outside the plan's scope",
        primary_analysis="not eligible under a room-temperature plan",
        sensitivity_analysis="none",
        pair=None,
        explanation="Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate.",
    ),
    "not_duplicate_other_test_type": dict(
        duplicate_status="not_duplicate",
        prd_class="Incompatible measurements: outside the plan's scope",
        primary_analysis="both enter under the reference plan (it sets no test-type rule)",
        sensitivity_analysis="none",
        pair=None,
        explanation="Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope.",
    ),
}

# The extract, in order. Rows are 0-based data-row indices in the frozen MPEA
# file (the header is not counted). All are among the records eligible under
# the reference plan (FCC, room temperature, grain size and yield strength
# reported, alloy at two or more grain sizes, grain size >= 0.1 um), spread
# over eight papers, so that a duplicate would matter to the analysis.
#   (case, MPEA row, {column: new value})
SPEC: list[tuple[str, int, dict[int, str]]] = [
    ("exact_duplicate_verbatim", 1315, {}),
    ("exact_duplicate_verbatim", 812, {}),
    ("exact_duplicate_renamed_alloy", 1316, {FORMULA: "CoCrFeMnNi"}),
    ("exact_duplicate_renamed_alloy", 1007, {FORMULA: "Co4Cr1Ni4"}),
    ("possible_duplicate_unknown_paper", 998, {REF_ID: "", DOI: "", YEAR: "", TITLE: ""}),
    ("possible_duplicate_unknown_paper", 1085, {REF_ID: "", DOI: "", YEAR: "", TITLE: ""}),
    ("not_duplicate_value_differs", 1278, {YS: "665.6"}),  # 512.0 x 1.3
    ("not_duplicate_value_differs", 986, {YS: "282.1"}),  # 217.0 x 1.3
    ("not_duplicate_other_paper", 1035, {REF_ID: "", DOI: TEST_DOI_PREFIX + "0001", TITLE: CONSTRUCTED_TITLE}),
    ("not_duplicate_other_paper", 764, {REF_ID: "", DOI: TEST_DOI_PREFIX + "0002", TITLE: CONSTRUCTED_TITLE}),
    ("not_duplicate_other_temperature", 1313, {TEMPERATURE: "-196.0"}),
    ("not_duplicate_other_temperature", 1086, {TEMPERATURE: "-196.0"}),
    ("missing_test_condition", 1036, {TEMPERATURE: ""}),
    ("missing_test_condition", 813, {TEMPERATURE: ""}),
    ("not_duplicate_other_test_type", 1004, {TEST_TYPE: "C"}),
    ("not_duplicate_other_test_type", 765, {TEST_TYPE: "C"}),
]

TRUTH_COLUMNS = [
    "extract_row",  # 1-based data row in extract.csv
    "case",
    "mpea_row",  # 0-based data row in the frozen MPEA file
    "mpea_reference_id",
    "mpea_doi",
    "changed_columns",  # MPEA header names, separated by "; "
    "duplicate_status",  # exact_duplicate | possible_duplicate | not_duplicate
    "prd_5_3_class",
    "kept_in_store",
    "removed_from_store",
    "primary_analysis",
    "sensitivity_analysis",
    "survivor_in_primary",  # which record of a duplicate pair enters the primary analysis
    "survivor_reason",
    "survivor_rule",
    "explanation",
]


def _csv_line(fields: list[str]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(fields)
    return buf.getvalue()


def build(mpea_path: Path = MPEA_PATH) -> tuple[str, str]:
    """Return (extract text, truth text)."""
    text = mpea_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    header_line, data_lines = lines[0], lines[1:]
    header = next(csv.reader([header_line]))

    extract = [header_line + "\n"]
    truth = [_csv_line(TRUTH_COLUMNS)]
    for n, (case, row, changes) in enumerate(SPEC, start=1):
        raw = data_lines[row]
        fields = next(csv.reader([raw]))
        if len(fields) != len(header):
            raise ValueError(f"MPEA row {row} has {len(fields)} fields, expected {len(header)}")
        for col, new in changes.items():
            if fields[col] == new:
                raise ValueError(f"MPEA row {row}: change to column {col} does not change the value")
        if changes:
            out = list(fields)
            for col, new in changes.items():
                out[col] = new
            extract.append(_csv_line(out))
        else:
            extract.append(raw + "\n")  # verbatim
        c = CASES[case]
        if c["pair"] is None:
            survivor, reason = NO_PAIR, NOT_SAME_MEASUREMENT
        else:
            survivor, reason = f"MPEA row {row}", c["pair"]
        truth.append(_csv_line([
            str(n),
            case,
            str(row),
            fields[REF_ID],
            fields[DOI],
            "; ".join(header[col] for col in sorted(changes)),
            c["duplicate_status"],
            c["prd_class"],
            KEPT,
            NOT_REMOVED,
            c["primary_analysis"],
            c["sensitivity_analysis"],
            survivor,
            reason,
            SURVIVOR_RULE,
            c["explanation"],
        ]))
    return "".join(extract), "".join(truth)


def main() -> None:
    extract, truth = build()
    EXTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXTRACT_PATH.write_text(extract, encoding="utf-8", newline="")
    TRUTH_PATH.write_text(truth, encoding="utf-8", newline="")
    print(f"wrote {EXTRACT_PATH.relative_to(REPO_ROOT)} and {TRUTH_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
