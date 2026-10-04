# Build step 1 — fix packet for the second-model re-check

Date: 2026-10-04. Branch: `step-01-sources`. First review covered commit `735c5ac` (see `docs/reviews/step01_review_packet.md`). Fixes are in commit `eb3da7b`. This packet is added in the next commit and changes no code.

Generated from the files on disk by a script, so every file below is quoted exactly. Frozen source data files are left out: none changed, and the suite checks their fingerprints.

## How to use this packet

The owner accepted all four findings of your first review of step 1. Please check that each fix closes its finding, and look for anything the fixes broke or left untested. Return a dated findings file as before; your review is advice, and the test suite is the gate. The checklist you will use from now on is included as a **draft awaiting owner approval** (section 3); comments on it are welcome.

Your first review's text will be filed as `docs/reviews/step01_review_chatgpt.md`. It is not yet in the repository, because the owner has not yet supplied the text.

| # | Finding (first review) | Where the fix is |
|---|---|---|
| 1 | Answers exposed under `data/`: the extract README listed expected classifications; the manifest pointed to the builder | builder, case table and answer file moved under `tests/fixtures/controlled_duplicates/`; data README neutral; `built_by` removed from the manifest; content tests `test_no_expected_outcomes_under_data`, `test_no_row_answers_under_package` and `test_manifest_points_to_nothing_holding_answers` |
| 2 | Freeze tests can lose coverage | `REQUIRED_FILES` and `MANIFEST_SHA256` pinned in `tests/test_frozen_sources.py` |
| 3 | Extract incomplete: no missing-condition case, no known-different test type, no survivor | extract rows 13–16; answer-file columns `survivor_in_primary`, `survivor_reason`, `survivor_rule`; survivor rule decided by the owner |
| 4 | No `docs/reviews/checklist.md` | drafted from PRD 13.2 and CLAUDE.md |

The step summary (section 1) gives the details, the tamper checks behind each fix, and the open items. It includes an open question for the owner: the reference plan's 77 MPEA records include one compression test, so that plan sets no test-type rule.

## Contents

1. Step summary (updated)
2. Files changed since the first review
3. Changed files (full text): builder, tests, manifest, extract and its README, the answer material, the draft checklist
4. Test output

## 1. Step summary (updated)

### `docs/reviews/step01_summary.md`

SHA-256 `52283619c06080cb789ff8fa3806dd2a162c7ba7f36c6d71a6e3a9e646fb6981`, 12559 bytes.

````markdown
# Build step 1 — summary for review

Date: 2026-10-04. Branch: `step-01-sources`. PRD Section 15, step 1: "Sources frozen. Store copies of the MPEA dataset and the Texas A&M dataset with their fingerprints. Build the controlled duplicate extract."

The suite is the gate; this summary is for the second-model review (PRD 13.2). It describes the state **after** the fixes for the first review. Those fixes are listed in "Review findings and fixes" below.

## What was built

| Path | What it is |
|---|---|
| `data/sources/mpea/MPEA_dataset.csv`, `LICENSE` | MPEA dataset (Borg et al. 2020, Sci. Data 7:430), byte-for-byte from `CitrineInformatics/MPEA_dataset` at commit `d31e2510…` (2022-08-03, head of master). Apache-2.0, confirmed from the repository's LICENSE (the PRD said "to be confirmed"). |
| `data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx` | Texas A&M FCC dataset, the lab's raw spreadsheet: the source of record. |
| `data/sources/tamu_fcc/inputs.csv` | The authors' CSV of the same 94 rows, which adds computed descriptors. Kept as a verified view, on the owner's decision to freeze both. |
| `data/sources/tamu_fcc/LICENSE` | MIT. |
| `data/manifest.json` | For every frozen file: SHA-256, size, role, origin URL pinned to a commit, retrieval date (2026-10-04), licence, citation. For Texas A&M also the DOI 10.5281/zenodo.22798856, tag v1.1.0 / commit `11390ee5…`, the Zenodo archive's MD5 and the archive member path of each file. It points to nothing that holds answers. |
| `data/controlled_duplicates/extract.csv`, `README.md` | The controlled duplicate extract: 16 constructed records in the MPEA column layout. The README states only neutral facts; it holds no case names and no expected outcomes. |
| `tests/fixtures/controlled_duplicates/build.py` | Deterministic builder of the extract and the answer file, with its case table. |
| `tests/fixtures/controlled_duplicates/truth.csv` | The expected answer for each extract row, including which record survives in the primary analysis. |
| `tests/fixtures/controlled_duplicates/README.md` | The per-row case table, the survivor rule and the open question. |
| `hypocurate/sources/manifest.py` | `sha256_file`, `load_manifest`, `verify`. Will be reused for source versions in step 4. |
| `scripts/fetch_sources.py` | Manual tool: downloads every frozen file again from its pinned origin (and, with `--zenodo`, the Zenodo archive) and compares it with the manifest. Never overwrites. Not part of the suite, so the suite does not need the network. |
| `.gitattributes` | Marks `data/**` and `tests/fixtures/**` as `-text`, so git never converts line endings and a checkout on another machine keeps the fingerprinted bytes. |
| `pyproject.toml`, `README.md` | Package metadata (pandas, openpyxl; pytest for dev) and how to run the suite. |
| `docs/reviews/checklist.md` | The reviewer's checklist (PRD 13.2). **Draft, awaiting owner approval.** |

Not built, as instructed: Docker, database, web, CI workflow, agents.

### Origin checks done once at freeze time
- Zenodo archive MD5 `dad706f3a6db0b96166f43c82a721bc8` matches the Zenodo record. The xlsx, csv and LICENSE inside it are byte-identical to the GitHub files at tag v1.1.0.
- `scripts/fetch_sources.py --zenodo` output on 2026-10-04: all 5 GitHub files OK, Zenodo archive OK, all 3 archive members OK. "ALL MATCH".

### Controlled duplicate extract
Each row is one listed MPEA row, copied unchanged or with listed columns changed. All 16 source rows are among the 77 records eligible under the reference plan, from 8 papers. Every row is kept in the store and none is removed.

| Rows | Case | Change | Expected (PRD 5.3) | Survivor in primary |
|---|---|---|---|---|
| 1–2 | exact duplicate, verbatim | none: byte-identical line | duplicate; counted once | MPEA record (rule 2) |
| 3–4 | exact duplicate, renamed alloy | formula `CoCrFeMnNi`, `Co4Cr1Ni4` (same atomic %) | duplicate; counted once | MPEA record (rule 2) |
| 5–6 | paper unknown | reference ID, DOI, year, title blanked | flagged as possible duplicate, kept, not removed; counted once in primary; both in sensitivity | MPEA record (rule 1) |
| 7–8 | same paper, alloy, grain size; value differs | YS × 1.3 | not a duplicate; both enter | no pair |
| 9–10 | same alloy, grain size, value; other paper | DOI → constructed `10.5555/hypocurate-test-000n` | not a duplicate; both enter | no pair |
| 11–12 | same except test temperature | 25 → −196 °C | not a duplicate; out of scope for a room-temperature plan | no pair |
| 13–14 | **missing test condition** | test temperature blanked (paper known) | scope cannot be confirmed; possible duplicate; not in primary; included in sensitivity | MPEA record (rule 2; this record is not eligible anyway) |
| 15–16 | **other test type** | tension → compression | not a duplicate (known different, not a possible duplicate); both enter under the reference plan | no pair |

**Survivor rule (owner's decision, 2026-10-04, refining PRD 5.3):**
1. Prefer the record that carries the original paper reference (DOI).
2. If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

## Review findings and fixes (first review, ChatGPT, 2026-10-04)

The owner accepted all four findings. The review text is to be saved as `docs/reviews/step01_review_chatgpt.md`. **That file is not yet committed: the text has not been received.**

1. **Answers exposed under `data/`.** The extract README listed the expected classification per row, and the manifest pointed to the builder, which holds the answers.
   - **Fix:**
     - the builder and its case table moved from `scripts/` to `tests/fixtures/controlled_duplicates/build.py`;
     - the answer file moved to `tests/fixtures/controlled_duplicates/truth.csv`;
     - the data README was cut down to neutral facts;
     - `built_by` was removed from the manifest.
   - **Tests:**
     - `test_no_expected_outcomes_under_data` scans every non-frozen file under `data/` for row-specific answer material and for the generic outcome vocabulary, with markers read from the answer file;
     - `test_no_row_answers_under_package` scans `hypocurate/` for row-specific material only (owner's change: the generic vocabulary is legitimate pipeline language from step 6);
     - `test_manifest_points_to_nothing_holding_answers` checks the manifest.
   - These replace the filename test.
   - **Requirement recorded for step 5:** the access layer must give pipeline code an **explicit list of approved input files** (`data/sources/**` and the extract), so that answer material under `tests/` is unreachable by construction, not by convention.
2. **Freeze tests could lose coverage.**
   - **Fix:**
     - `REQUIRED_FILES` (6 paths) is fixed in the test, and the manifest's file set must equal it;
     - the manifest's own SHA-256 is pinned in the test (`test_manifest_itself_is_unchanged`).
   - Changing a data file and its manifest entry together now fails.
3. **Extract incomplete.**
   - **Fix:** two cases were added:
     - missing test condition (rows 13–14), distinct from missing paper;
     - known-different test type (rows 15–16), not a possible duplicate.
   - Answer-file columns `survivor_in_primary`, `survivor_reason` and `survivor_rule` state which record survives for each duplicate pair.
   - The PRD's survivor rule was ambiguous for these pairs, because both records cite the same paper and no source order is defined. The owner chose the rule above.
4. **Checklist missing.**
   - **Fix:** `docs/reviews/checklist.md` drafted from PRD 13.2 and the CLAUDE.md rules, for owner approval.

**Tamper checks** (scratch copies of the repository, not committed):

| Tampering | Result |
|---|---|
| one byte of `tamu_fcc/inputs.csv` changed **and** its manifest entry updated to match | `test_manifest_itself_is_unchanged` fails |
| an MPEA manifest entry removed | the manifest-fingerprint, required-files and origin tests fail |
| a case name added to the data README | `test_no_expected_outcomes_under_data` fails |
| generic vocabulary added to a package file | passes, as intended |
| `MPEA row 1315` added to a package file | `test_no_row_answers_under_package` fails |

## Tests (91, all passing)

`tests/test_frozen_sources.py` (24):
- the manifest's own fingerprint is pinned;
- the manifest covers exactly the 6 required files, and each is present;
- each manifest file matches its SHA-256 and size;
- `verify` reports nothing on the real files and reports a single altered byte in a copy;
- origin, commit-pinned URLs, retrieval date and licence are recorded for both sources;
- the licence texts are Apache-2.0 and MIT;
- the Texas A&M origin is the Zenodo DOI and v1.1.0;
- **MPEA: 1,545 records, 237 with grain size**;
- **Texas A&M: 94 samples, 82 compositions**, exactly 1 without yield strength (BBA09), and grain size present for all;
- the CSV view equals the spreadsheet on composition, grain size, YS, HV, their SDs and processing.

`tests/test_controlled_duplicates.py` (67):
- rebuilding gives a byte-identical extract and answer file;
- the extract's fingerprint is in the manifest, and the answer file's fingerprint is pinned in the test;
- no answer material is under `data/` or the package (location and content), and the manifest points to nothing holding answers;
- the extract has no answer columns;
- there are 16 rows, 2 per case;
- each row differs from its MPEA source in exactly the stated columns;
- the source rows are in reference scope and span 8 papers;
- verbatim rows are byte-identical lines;
- renamed alloys have the same composition;
- unknown-paper rows have no reference;
- constructed DOIs do not occur in MPEA;
- changed values are as stated;
- missing-condition rows keep their paper;
- test-type rows are compression copies of tension records;
- the expected handling per case follows PRD 5.3;
- the survivor is stated per the owner's rule for every row.

### Suite result
```
$ .venv/bin/pytest -q
...........................................................................................
91 passed in 1.31s
```
Environment: Codespace, Python 3.14.2, pandas 3.0.6, openpyxl 3.1.5, pytest 9.1.1, in `.venv` (gitignored).

## Reference numbers still reproduce
I re-ran the method of `docs/reference/worked_example.py` on the frozen files in the repository after the fixes (a scratch script, not committed). The frozen sources are unchanged, and the extract never enters a reference run.
- MPEA alone: 77 records, 13 alloys, 20 papers; k = 427.2 ± 61.4; p = 6.2e-7.
- Texas A&M alone: 21 eligible records, 9 alloys, 72 not eligible; k ≈ 1173.
- Pooled: 98 records, 22 alloys, 21 groups, 75 residual df; k = 428.0 ± 63.5; p = 7.4e-7.

The eligibility counts and reference numbers become tests in steps 6–7, not now.

The 77 eligible MPEA records contain no exact duplicates of each other. The file's 32 internally duplicated rows are all out of scope, so "counted once" does not disturb the reference numbers. Two natural groups share paper, alloy and grain size with different values (MPEA rows 752–754 and 1033–1034). Duplicate detection must not merge them.

## Open items
1. **Pooled p-value.** PRD 5.7/10 and CLAUDE.md state pooled p ≈ 8e-7. Recomputation gives 7.4e-7 (statsmodels 0.15.0), while k and its SE match. To be settled before the step 7 reference test (owner agreed).
2. **Open question for the owner: compression test in the reference set.** The 77 MPEA records eligible under the reference plan include one compression test (MPEA row 139, doi 10.1016/j.jallcom.2014.12.157, CoCrFeMnNi, 350 µm, 230 MPa). So the reference plan sets no test-type rule. The reference plan is **not** changed. Extract rows 15–16 are stated relative to it.
3. **Step 5 requirement:** the access layer gives pipeline code an explicit list of approved input files (see finding 1).
4. `docs/reviews/checklist.md` awaits owner approval.
5. `docs/reviews/step01_review_chatgpt.md` awaits the review text.
6. The suite does not yet run on GitHub (step 2).
7. Dependency versions are minimums, not a lock file. Revisit when the Docker image is built in step 2.

## Questions for the reviewer
- Do the fixes close the four findings?
- Is the split between the data-content test (all outcome vocabulary) and the package test (row-specific material only) sound?
- Is keeping both the raw spreadsheet and the authors' derived CSV a risk for step 4, given that the CSV also carries computed descriptors?
````

## 2. Files changed since the first review

`git diff --name-status -M 735c5ac..eb3da7b` (A = added, M = modified, R = moved, D = deleted).

| Status | Path | In this packet |
|---|---|---|
| M | `data/controlled_duplicates/README.md` | section 3 |
| M | `data/controlled_duplicates/extract.csv` | section 3 |
| M | `data/manifest.json` | section 3 |
| A | `docs/reviews/checklist.md` | section 3 |
| M | `docs/reviews/step01_summary.md` | section 1 |
| A | `tests/fixtures/controlled_duplicates/README.md` | section 3 |
| R | `scripts/build_controlled_duplicates.py` → `tests/fixtures/controlled_duplicates/build.py` | section 3 |
| A | `tests/fixtures/controlled_duplicates/truth.csv` | section 3 |
| D | `tests/fixtures/controlled_duplicates_truth.csv` | removed: the answer file now lives at `tests/fixtures/controlled_duplicates/truth.csv` (section 3) |
| M | `tests/test_controlled_duplicates.py` | section 3 |
| M | `tests/test_frozen_sources.py` | section 3 |

## 3. Changed files (full text)

Builder, then tests, then data, then the answer material under `tests/fixtures/`, then the draft checklist.

### `tests/fixtures/controlled_duplicates/build.py`

SHA-256 `d7e48dfcf496013a6923ae6ff8671e16c003f2631fae7c714052c8319675ec48`, 11466 bytes.

````python
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
````

### `tests/test_controlled_duplicates.py`

SHA-256 `fb10b67216e9b453199cbd387a0c892f9790ddb74ea3e52aa9270d03a21c6629`, 13283 bytes.

````python
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
TRUTH_SHA256 = "fa70d4fbfed3ad8899b8f2240f45f53fe34e1be5537f268ca7cc55deb0ce5809"
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


# --- the answer file is out of the pipeline's reach --------------------------------

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
        "not_duplicate_value_differs": 2,
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
        if t["case"] == "not_duplicate_value_differs":
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


# --- the expected answers follow PRD 5.3 ------------------------------------------

EXPECTED = {
    "exact_duplicate_verbatim": ("exact_duplicate", "counted once", "none"),
    "exact_duplicate_renamed_alloy": ("exact_duplicate", "counted once", "none"),
    "possible_duplicate_unknown_paper": ("possible_duplicate", "counted once", "both counted separately"),
    "not_duplicate_value_differs": ("not_duplicate", "both enter", "none"),
    "not_duplicate_other_paper": ("not_duplicate", "both enter", "none"),
    "not_duplicate_other_temperature": ("not_duplicate", "not eligible under a room-temperature plan", "none"),
    "missing_test_condition": ("possible_duplicate", "not eligible: scope not confirmed", "included"),
    "not_duplicate_other_test_type": (
        "not_duplicate", "both enter under the reference plan (it sets no test-type rule)", "none"),
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
            assert t["survivor_reason"].startswith("rule 1:")  # only the MPEA record carries the paper
        else:
            assert row[doi] == src[doi]
            assert t["survivor_reason"].startswith("rule 2:")  # both carry it; MPEA is first in order
    else:
        assert t["survivor_in_primary"] == "no pair: both kept"
````

### `tests/test_frozen_sources.py`

SHA-256 `8eada242e1466f1014009bfdf1fed2e3541278f95464d8446b4e3afcc88d7b35`, 5738 bytes.

````python
"""Step 1: the two sources are frozen, fingerprinted and as the PRD describes (Section 10)."""
import pandas as pd
import pytest

from hypocurate.sources.manifest import REPO_ROOT, file_entries, load_manifest, sha256_file, verify

MANIFEST = load_manifest()
MANIFEST_PATH = REPO_ROOT / "data/manifest.json"
# Pinned here, outside data/, so the data and the manifest cannot be changed
# together without changing a test (second-model review of step 1, finding 2).
MANIFEST_SHA256 = "fa25ebee6a7c95d4d05dfe7eec2d388001fe37cd975e027d688b2de70b11f5b8"
# Every file the manifest must cover. Fixed here so that dropping an entry from
# the manifest cannot silently remove its fingerprint check.
REQUIRED_FILES = {
    "data/sources/mpea/MPEA_dataset.csv",
    "data/sources/mpea/LICENSE",
    "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
    "data/sources/tamu_fcc/inputs.csv",
    "data/sources/tamu_fcc/LICENSE",
    "data/controlled_duplicates/extract.csv",
}
MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
TAMU_XLSX = REPO_ROOT / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
TAMU_CSV = REPO_ROOT / "data/sources/tamu_fcc/inputs.csv"
ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]


# --- fingerprints -------------------------------------------------------------

def test_manifest_itself_is_unchanged():
    assert sha256_file(MANIFEST_PATH) == MANIFEST_SHA256


def test_manifest_covers_exactly_the_required_files():
    assert {e.path for e in file_entries(MANIFEST)} == REQUIRED_FILES


@pytest.mark.parametrize("path", sorted(REQUIRED_FILES))
def test_required_file_is_present(path):
    assert (REPO_ROOT / path).is_file()


@pytest.mark.parametrize("entry", file_entries(MANIFEST), ids=lambda e: e.path)
def test_frozen_file_matches_its_fingerprint(entry):
    path = REPO_ROOT / entry.path
    assert path.is_file(), f"{entry.path} is missing"
    assert path.stat().st_size == entry.bytes
    assert sha256_file(path) == entry.sha256


def test_verify_reports_no_problems():
    assert verify(MANIFEST) == []


def test_verify_detects_a_changed_byte(tmp_path):
    """The check itself works: one altered byte in a copy is reported."""
    entry = next(e for e in file_entries(MANIFEST) if e.path.endswith("MPEA_dataset.csv"))
    copy = tmp_path / entry.path
    copy.parent.mkdir(parents=True)
    data = bytearray((REPO_ROOT / entry.path).read_bytes())
    data[1000] ^= 0x01
    copy.write_bytes(bytes(data))
    manifest = {"sources": {"mpea": {"files": [{"path": entry.path, "sha256": entry.sha256, "bytes": entry.bytes}]}},
                "controlled_duplicates": {"files": []}}
    problems = verify(manifest, root=tmp_path)
    assert len(problems) == 1 and "sha256" in problems[0]


def test_both_sources_are_in_the_manifest():
    assert set(MANIFEST["sources"]) == {"mpea", "tamu_fcc"}


@pytest.mark.parametrize("source_id", ["mpea", "tamu_fcc"])
def test_manifest_records_origin_date_and_licence(source_id):
    s = MANIFEST["sources"][source_id]
    for key in ("name", "citation", "licence", "licence_file", "repository", "commit", "retrieved"):
        assert s.get(key), f"{source_id}: {key} missing"
    assert s["retrieved"] == "2026-10-04"
    assert len(s["commit"]) == 40
    for f in s["files"]:
        assert f["origin_url"].startswith("https://")
        assert s["commit"] in f["origin_url"], "origin must be pinned to the recorded commit"
    assert s["licence_file"] in {f["path"] for f in s["files"]}, "licence text must be frozen too"


def test_licence_texts_match_the_manifest():
    mpea = (REPO_ROOT / MANIFEST["sources"]["mpea"]["licence_file"]).read_text(encoding="utf-8")
    tamu = (REPO_ROOT / MANIFEST["sources"]["tamu_fcc"]["licence_file"]).read_text(encoding="utf-8")
    assert MANIFEST["sources"]["mpea"]["licence"] == "Apache-2.0"
    assert "Apache License" in mpea and "Version 2.0" in mpea
    assert MANIFEST["sources"]["tamu_fcc"]["licence"] == "MIT"
    assert tamu.startswith("MIT License")


def test_tamu_origin_is_the_zenodo_record():
    s = MANIFEST["sources"]["tamu_fcc"]
    assert s["doi"] == "10.5281/zenodo.22798856"
    assert s["tag"] == "v1.1.0"
    assert s["repository"] == "https://github.com/ArroyaveLab/2026-mulukutla-hall-petch"
    assert s["zenodo_archive"]["md5"] == "dad706f3a6db0b96166f43c82a721bc8"


# --- record counts stated in the PRD -------------------------------------------

def test_mpea_counts():
    d = pd.read_csv(MPEA_CSV)
    assert len(d) == 1545
    assert d["PROPERTY: grain size ($\\mu$m)"].notna().sum() == 237


def tamu_xlsx():
    return pd.read_excel(TAMU_XLSX)


def test_tamu_counts():
    x = tamu_xlsx()
    assert len(x) == 94  # samples
    assert len(x[ELEMENTS].drop_duplicates()) == 82  # compositions
    assert x["YS (MPa)"].isna().sum() == 1  # one sample has no yield strength
    assert x.loc[x["YS (MPa)"].isna(), "Alloy Name"].tolist() == ["BBA09"]
    assert x["Grain Size(µm)"].notna().all()


def test_tamu_csv_view_agrees_with_the_spreadsheet():
    x, c = tamu_xlsx(), pd.read_csv(TAMU_CSV)
    assert len(c) == len(x)
    assert c["Alloy"].tolist() == x["Alloy Name"].tolist()
    assert c["Iteration"].tolist() == x["Iteration"].tolist()
    pairs = {el: el for el in ELEMENTS} | {
        "GrainSize": "Grain Size(µm)", "SD_GS": "SD, Grain Size(µm)",
        "YS": "YS (MPa)", "SD_YS": "SD, YS", "HV": "Hardness, HV", "SD_HV": "SD, HV",
        "ColdWork": "Cold Work (%Reduction)", "RecrystT": "Recrystallization Temp(℃)",
        "HoldTime": "Holding time (h)",
    }
    for csv_col, xlsx_col in pairs.items():
        pd.testing.assert_series_equal(
            c[csv_col].astype(float), x[xlsx_col].astype(float), check_names=False, obj=csv_col
        )
````

### `data/manifest.json`

SHA-256 `fa25ebee6a7c95d4d05dfe7eec2d388001fe37cd975e027d688b2de70b11f5b8`, 4563 bytes.

````json
{
  "manifest_version": 1,
  "note": "Frozen copies for HypoCurate sprint 1 (PRD Sections 10 and 15, step 1). Any change to a listed file fails the regression suite. Fingerprints are SHA-256 of the file bytes.",
  "sources": {
    "mpea": {
      "name": "MPEA dataset",
      "citation": "Borg, C. K. H. et al. (2020). Expanded dataset of mechanical properties and observed phases of multi-principal element alloys. Scientific Data 7, 430. doi:10.1038/s41597-020-00768-9",
      "kind_of_data": "measured (literature compilation)",
      "licence": "Apache-2.0",
      "licence_file": "data/sources/mpea/LICENSE",
      "repository": "https://github.com/CitrineInformatics/MPEA_dataset",
      "commit": "d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e",
      "commit_date": "2022-08-03",
      "retrieved": "2026-10-04",
      "files": [
        {
          "path": "data/sources/mpea/MPEA_dataset.csv",
          "role": "source data",
          "origin_url": "https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e/MPEA_dataset.csv",
          "sha256": "c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d",
          "bytes": 332126
        },
        {
          "path": "data/sources/mpea/LICENSE",
          "role": "licence text",
          "origin_url": "https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e/LICENSE",
          "sha256": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
          "bytes": 11357
        }
      ]
    },
    "tamu_fcc": {
      "name": "Texas A&M FCC dataset",
      "citation": "Mulukutla, M. et al. (2026). Revisiting Hall-Petch strengthening in FCC multi-principal element alloys: data and analysis pipeline (v1.1.0). Zenodo. doi:10.5281/zenodo.22798856",
      "kind_of_data": "measured (single laboratory)",
      "licence": "MIT",
      "licence_file": "data/sources/tamu_fcc/LICENSE",
      "doi": "10.5281/zenodo.22798856",
      "concept_doi": "10.5281/zenodo.22703332",
      "zenodo_archive": {
        "url": "https://zenodo.org/api/records/22798856/files/ArroyaveLab/2026-mulukutla-hall-petch-v1.1.0.zip/content",
        "name": "ArroyaveLab/2026-mulukutla-hall-petch-v1.1.0.zip",
        "md5": "dad706f3a6db0b96166f43c82a721bc8",
        "bytes": 48838629,
        "member_prefix": "ArroyaveLab-2026-mulukutla-hall-petch-11390ee/"
      },
      "repository": "https://github.com/ArroyaveLab/2026-mulukutla-hall-petch",
      "tag": "v1.1.0",
      "commit": "11390ee516c1a17cacdde318b40d5d6889d4007f",
      "retrieved": "2026-10-04",
      "files": [
        {
          "path": "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
          "role": "source data (source of record)",
          "archive_member": "data/raw/Grain_Size_Summary_v3.xlsx",
          "origin_url": "https://raw.githubusercontent.com/ArroyaveLab/2026-mulukutla-hall-petch/11390ee516c1a17cacdde318b40d5d6889d4007f/data/raw/Grain_Size_Summary_v3.xlsx",
          "sha256": "dea3f117e947ae875de31911fabb08d3d747a055336d17793edb82ad7e88155b",
          "bytes": 22939
        },
        {
          "path": "data/sources/tamu_fcc/inputs.csv",
          "role": "CSV view of the same 94 rows, with computed descriptors added by the authors",
          "archive_member": "data/derived/inputs.csv",
          "origin_url": "https://raw.githubusercontent.com/ArroyaveLab/2026-mulukutla-hall-petch/11390ee516c1a17cacdde318b40d5d6889d4007f/data/derived/inputs.csv",
          "sha256": "e5c087d860c650b9d86ddb54b82e9ddb293f64e767150b739169e27740d835ec",
          "bytes": 32449
        },
        {
          "path": "data/sources/tamu_fcc/LICENSE",
          "role": "licence text",
          "archive_member": "LICENSE",
          "origin_url": "https://raw.githubusercontent.com/ArroyaveLab/2026-mulukutla-hall-petch/11390ee516c1a17cacdde318b40d5d6889d4007f/LICENSE",
          "sha256": "917035f0704dbb979bd157a7f8d814f5e7c32d28aedba41986443298dea5b98b",
          "bytes": 1119
        }
      ]
    }
  },
  "controlled_duplicates": {
    "name": "Controlled duplicate extract",
    "kind_of_data": "constructed test data; never pooled into a real analysis or a reference run",
    "built_from": "data/sources/mpea/MPEA_dataset.csv",
    "built": "2026-10-04",
    "files": [
      {
        "path": "data/controlled_duplicates/extract.csv",
        "role": "extract",
        "sha256": "8e11979a373c74f2bf6d8f39c8c0316164bcc3ac1361a7e325ccb0a36294afee",
        "bytes": 3875
      }
    ]
  }
}
````

### `data/controlled_duplicates/README.md`

SHA-256 `392a84489391fa98c27d5c6be2176ca6358c15d08c11061ded6359c05dae1c83`, 773 bytes.

````markdown
# Controlled duplicate extract

**Constructed test data.** `extract.csv` holds 16 records derived from the frozen MPEA dataset (`data/sources/mpea/MPEA_dataset.csv`). Some overlap MPEA records and some do not. It exists only to test duplicate handling (PRD Sections 5.3, 10 and 14.1). It is never pooled into a real analysis or a reference run.

The two sprint sources share no measurements, so this extract is the only overlap available for testing.

## Format

The same columns as the MPEA dataset, with the header copied verbatim. Records whose paper is not a real publication carry a DOI beginning `10.5555/hypocurate-test-` and say so in their title.

## Fingerprint

The SHA-256 of `extract.csv` is recorded in `data/manifest.json`. A test fails if the file changes.
````

### `data/controlled_duplicates/extract.csv`

SHA-256 `8e11979a373c74f2bf6d8f39c8c0316164bcc3ac1361a7e325ccb0a36294afee`, 3875 bytes.

````csv
IDENTIFIER: Reference ID,FORMULA,PROPERTY: Microstructure,PROPERTY: Processing method,PROPERTY: BCC/FCC/other,PROPERTY: grain size ($\mu$m),PROPERTY: Exp. Density (g/cm$^3$),PROPERTY: Calculated Density (g/cm$^3$),PROPERTY: HV,PROPERTY: Type of test,PROPERTY: Test temperature ($^\circ$C),PROPERTY: YS (MPa),PROPERTY: UTS (MPa),PROPERTY: Elongation (%),PROPERTY: Elongation plastic (%),PROPERTY: Exp. Young modulus (GPa),PROPERTY: Calculated Young modulus (GPa),PROPERTY: O content (wppm),PROPERTY: N content (wppm),PROPERTY: C content (wppm),REFERENCE: doi,REFERENCE: year,REFERENCE: title
252,Co1 Cr1 Fe1 Mn1 Ni1,FCC,WROUGHT,FCC,1.79,,8.0,,T,25.0,729.21,901.74,26.3,,,220,,,,10.1007/s11661-019-05231-y,2019,Effect of Annealing Temperature on Microstructure and Mechanical Properties of a Severe Cold-Rolled FeCoCrNiMn High-Entropy Alloy
144,Co1 Cr0.588 Fe0.176 Mo0.176 Ni1,FCC,WROUGHT,FCC,3.2,,8.6,,T,25.0,649.0,,42.0,,,231,,,,10.1016/j.ijplas.2018.10.005,2019,Strength and ductility of CrFeCoNiMo alloy with hierarchical microstructures
252,CoCrFeMnNi,FCC,WROUGHT,FCC,4.57,,8.0,,T,25.0,494.82,735.6,38.7,,,220,,,,10.1007/s11661-019-05231-y,2019,Effect of Annealing Temperature on Microstructure and Mechanical Properties of a Severe Cold-Rolled FeCoCrNiMn High-Entropy Alloy
208,Co4Cr1Ni4,FCC,WROUGHT,FCC,1.46,,8.7,,T,25.0,387.0,626.0,73.0,,223.0,213,,,,10.1016/j.actamat.2019.04.017,2019,Effect of elemental combination on friction stress and Hall-Petch relationship in face-centered cubic high / medium entropy alloys
,Fe1 Mn1 Ni1,FCC,WROUGHT,FCC,1.75,,8.1,,T,25.0,407.0,536.0,26.0,,182.0,203,,,,,,
,Co0.286 Cr0.429 Fe1 Mn0.143 Ni0.714 V0.286,FCC,WROUGHT,FCC,11.2,,7.9,,T,25.0,312.0,660.0,51.0,,,208,,,,,,
248,Co0.25 Cr0.25 Fe1 Mn1,FCC,WROUGHT,FCC,32.0,,7.7,,T,25.0,665.6,978.0,55.3,,,212,,,,10.1016/j.msea.2019.138039,2019,Development of a large size FCC high-entropy alloy with excellent mechanical properties
204,Co1 Fe1 Ni1,FCC,WROUGHT,FCC,74.0,,8.5,,T,25.0,282.1,498.0,47.0,,,207,,,,10.1016/j.intermet.2019.106477,2019,Effects of heat treatment on the microstructure and properties of cold-forged CoNiFe medium entropy alloy
,Co1 Cr1 Fe1 Mn1 Ni1,FCC,WROUGHT,FCC,10.0,,8.0,,T,25.0,320.0,,59.0,,,220,,,,10.5555/hypocurate-test-0001,2019,Constructed record: HypoCurate controlled duplicate extract (not a real paper)
,Co1 Cr1 Ni1,FCC,WROUGHT,FCC,2.3,,8.3,326.0,T,25.0,597.0,,53.0,,,231,,,,10.5555/hypocurate-test-0002,2019,Constructed record: HypoCurate controlled duplicate extract (not a real paper)
252,Co1 Cr1 Fe1 Mn1 Ni1,FCC,WROUGHT,FCC,0.248,,8.0,,T,-196.0,1241.81,1325.25,4.31,,,220,,,,10.1007/s11661-019-05231-y,2019,Effect of Annealing Temperature on Microstructure and Mechanical Properties of a Severe Cold-Rolled FeCoCrNiMn High-Entropy Alloy
221,Co0.286 Cr0.429 Fe1 Mn0.143 Ni0.714 V0.286,FCC,WROUGHT,FCC,48.2,,7.9,,T,-196.0,240.0,610.0,53.0,,,208,,,,10.1016/j.msea.2018.12.077,2019,Effect of grain size on the tensile behavior of V10Cr15Mn5Fe35Co10Ni25 high entropy alloy
211,Co1 Cr1 Fe1 Mn1 Ni1,FCC,WROUGHT,FCC,20.0,,8.0,,T,,280.0,,62.0,,,220,,,,10.1016/j.msea.2019.04.025,2019,Regulating the strength and ductility of a cold rolled FeCrCoMnNi high-entropy alloy via annealing treatment
144,Co1 Cr0.588 Fe0.176 Mo0.176 Ni1,FCC,WROUGHT,FCC,18.2,,8.6,,T,,439.0,,63.0,,,231,,,,10.1016/j.ijplas.2018.10.005,2019,Strength and ductility of CrFeCoNiMo alloy with hierarchical microstructures
208,Co1 Mn1 Ni1,FCC,WROUGHT,FCC,2.67,,8.4,,C,25.0,267.0,506.0,62.5,,190.0,202,,,,10.1016/j.actamat.2019.04.017,2019,Effect of elemental combination on friction stress and Hall-Petch relationship in face-centered cubic high / medium entropy alloys
98,Co1 Cr1 Ni1,FCC,WROUGHT,FCC,24.0,,8.3,223.0,C,25.0,346.0,,76.0,,,231,,,,10.1016/j.actamat.2018.12.015,2019,Achieving ultra-high strength and ductility in equiatomic CrCoNi with partially recrystallized microstructures
````

### `tests/fixtures/controlled_duplicates/README.md`

SHA-256 `5e67cc7a19d78d391abb9efac8c062350c63baa19da85df19a59ec27f800741a`, 3144 bytes.

````markdown
# Controlled duplicate extract: construction and expected answers

**Test material. Never move any of this under `data/` or into the `hypocurate` package.** The pipeline must not be able to read the expected answers. Tests check that no expected-outcome content exists there.

| File | What it is |
|---|---|
| `build.py` | Builds `data/controlled_duplicates/extract.csv` and `truth.csv` from the frozen MPEA file. Deterministic. |
| `truth.csv` | The expected answer for each extract row. |

## The cases

All 16 source rows are among the records eligible under the reference plan, from eight papers. Two rows per case.

| Rows | Case | What was changed | Duplicate? | Primary analysis | Sensitivity |
|---|---|---|---|---|---|
| 1–2 | `exact_duplicate_verbatim` | nothing (byte-for-byte copy) | yes | counted once | none |
| 3–4 | `exact_duplicate_renamed_alloy` | formula written differently (`CoCrFeMnNi`, `Co4Cr1Ni4`); same atomic % | yes | counted once | none |
| 5–6 | `possible_duplicate_unknown_paper` | reference ID, DOI, year, title blanked | possible: flagged, kept, not removed | counted once | both counted separately |
| 7–8 | `not_duplicate_value_differs` | yield strength × 1.3 | no | both enter | none |
| 9–10 | `not_duplicate_other_paper` | DOI → constructed `10.5555/hypocurate-test-…` | no | both enter | none |
| 11–12 | `not_duplicate_other_temperature` | 25 °C → −196 °C | no (conditions differ) | not eligible under a room-temperature plan | none |
| 13–14 | `missing_test_condition` | test temperature blanked | possible (conditions cannot be confirmed); kept, not removed | not eligible: scope not confirmed | included |
| 15–16 | `not_duplicate_other_test_type` | tension → compression | no (conditions known to differ; not a possible duplicate) | both enter under the reference plan (it sets no test-type rule) | none |

**Missing paper vs missing test condition (PRD 5.3).**
- Rows 5–6: the paper is unknown but the conditions match. This is a possible duplicate that cannot be resolved.
- Rows 13–14: the paper is known but a test condition is missing, so the scope cannot be confirmed. The record stays out of the primary analysis and goes into the sensitivity analysis.

Every row is kept in the store and none is removed.

## Which record survives in the primary analysis

Owner's decision, 2026-10-04, refining PRD 5.3:
1. Prefer the record that carries the original paper reference (DOI).
2. If both or neither do, take the first source in the fixed order: MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

For every duplicate and possible-duplicate row in this extract, the MPEA record survives:
- rows 1–4 and 13–14 by rule 2 (rows 13–14 are not eligible anyway);
- rows 5–6 by rule 1.

`truth.csv` gives the survivor and the reason for each row.

## Open question (owner)

The reference plan's 77 MPEA records include one compression test (MPEA row 139), so the reference plan sets no test-type rule. Rows 15–16 are stated relative to that plan.

## Rebuilding

```
python tests/fixtures/controlled_duplicates/build.py
```
````

### `tests/fixtures/controlled_duplicates/truth.csv`

SHA-256 `fa70d4fbfed3ad8899b8f2240f45f53fe34e1be5537f268ca7cc55deb0ce5809`, 11424 bytes.

````csv
extract_row,case,mpea_row,mpea_reference_id,mpea_doi,changed_columns,duplicate_status,prd_5_3_class,kept_in_store,removed_from_store,primary_analysis,sensitivity_analysis,survivor_in_primary,survivor_reason,survivor_rule,explanation
1,exact_duplicate_verbatim,1315,252,10.1007/s11661-019-05231-y,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,MPEA row 1315,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
2,exact_duplicate_verbatim,812,144,10.1016/j.ijplas.2018.10.005,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,MPEA row 812,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
3,exact_duplicate_renamed_alloy,1316,252,10.1007/s11661-019-05231-y,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,MPEA row 1316,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
4,exact_duplicate_renamed_alloy,1007,208,10.1016/j.actamat.2019.04.017,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,MPEA row 1007,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,MPEA row 998,rule 1: only the MPEA record carries the paper reference,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,MPEA row 1085,rule 1: only the MPEA record carries the paper reference,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
7,not_duplicate_value_differs,1278,248,10.1016/j.msea.2019.138039,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
8,not_duplicate_value_differs,986,204,10.1016/j.intermet.2019.106477,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
9,not_duplicate_other_paper,1035,211,10.1016/j.msea.2019.04.025,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
10,not_duplicate_other_paper,764,98,10.1016/j.actamat.2018.12.015,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
11,not_duplicate_other_temperature,1313,252,10.1007/s11661-019-05231-y,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
12,not_duplicate_other_temperature,1086,221,10.1016/j.msea.2018.12.077,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
13,missing_test_condition,1036,211,10.1016/j.msea.2019.04.025,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,MPEA row 1036,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
14,missing_test_condition,813,144,10.1016/j.ijplas.2018.10.005,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,MPEA row 813,rule 2: both records carry the paper reference; MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
15,not_duplicate_other_test_type,1004,208,10.1016/j.actamat.2019.04.017,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,both enter under the reference plan (it sets no test-type rule),none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
16,not_duplicate_other_test_type,765,98,10.1016/j.actamat.2018.12.015,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,both enter under the reference plan (it sets no test-type rule),none,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
````

### `docs/reviews/checklist.md`

SHA-256 `81ecd9aca38ed36b5c7e94ba814cbaa3d8602b7ec7ad8f9026f3b09d2f288923`, 6114 bytes.

````markdown
# Second-model review checklist

**Status: draft, awaiting owner approval.** Drafted 2026-10-04 from PRD Section 13.2 and the rules in `CLAUDE.md`. Once approved, this is the fixed checklist given to the reviewer at every review.

## When a review is required (PRD 13.2)
- At the end of each build step in PRD Section 15.
- Whenever a change touches a safeguard: the access rules, the plan lock, the inclusion and eligibility rules, or the statistics. Any change to a safeguard also needs the owner's approval, however small.

## What the reviewer is given
1. The changes since the last review: a review packet with the full text of every changed code, test and script file, and the test output.
2. The core rules:
   - the access contract (PRD 4);
   - the plan lock and dataset freeze (PRD 5.6);
   - "stored is not the same as analysed" (PRD 5.3);
   - "a narrower question is a separate record" (PRD 5.4).
3. This checklist.

## Minimum questions (PRD 13.2, verbatim)
1. Can any role reach outcome values it should not see?
2. Can anything change after the lock?
3. Are records ever dropped or overwritten in the store?
4. Do the eligibility rules match Section 5.3?
5. Are the statistics what the plan states?
6. Are there untested paths?
7. Are secrets or keys exposed?

## Rule-by-rule checks
Answer each with yes, no or not applicable to this change. Give a reason for every "no".

**Who decides**
- [ ] Code alone sets inclusion, flags, the choice of test, data sufficiency and the verdict. No language model output can set any of them. (CLAUDE.md rule 1)

**Access contract (PRD 4)**
- [ ] Every agent reads data only through the access layer, using a per-role, per-stage allow-list of fields. Is anything not on the list withheld?
- [ ] A disallowed call raises `AccessDenied` and writes an audit-log row.
- [ ] Outcome values cannot leak through any of these:
  - flag numbers;
  - values as originally reported;
  - nested fields;
  - text handed between stages.
- [ ] The tests cover a role's **complete** input: prompt, every tool response and handed-over text. Do they include the planted-value test for the Planner and the Critic?
- [ ] Pipeline code reads input files only from an explicit list of approved files. Is answer material under `tests/` unreachable by construction?
- [ ] The Curator is not told the direction of the claim.
- [ ] The Critic gets the kind of each flag, never the numbers.

**Checkpoints (PRD 5.6)**
- [ ] Rules lock before curation fixes all of these, with a fingerprint and a time:
  - the model;
  - scope;
  - exclusion rules;
  - eligibility rules;
  - the data-sufficiency option;
  - sensitivity analyses.
- [ ] Dataset freeze before analysis fixes the record sets, with a fingerprint and a time.
- [ ] After each checkpoint, nothing changes, by agent or by person. Is every attempt rejected and logged?
- [ ] A later removal appears only as a labelled sensitivity analysis and never changes the verdict.

**Stored is not analysed (PRD 5.3)**
- [ ] Every record found is kept. Nothing is deleted or overwritten in place.
- [ ] Eligibility is decided by code under the locked rules. Do the defaults match the PRD 5.3 table?
- [ ] Duplicates require all of these: the same original paper, alloy, grain size, value and test conditions. Is matching alloy and grain size alone kept from counting?
- [ ] The survivor of a duplicate pair follows the owner's rule:
  1. paper reference;
  2. then the fixed source order MPEA, Texas A&M, controlled extract;
  3. then the lowest row.
- [ ] Conflicting records are preserved, not automatically pooled.
- [ ] Physical checks never use the relationship under test.
- [ ] Model-recalled data are never pooled and never count toward a verdict.

**Statistics (PRD 5.7, 5.8, 5.10)**
- [ ] Only the one supported model is used:
  - OLS with alloy intercepts;
  - k × d^-1/2;
  - cluster-robust standard errors by paper, with the small-sample correction;
  - a one-sided test of k > 0 at 0.05, against t with (groups − 1) degrees of freedom;
  - only alloys with at least 2 distinct grain sizes.
- [ ] Both validity checks are applied to every analysis and can never be waived:
  1. Can a coefficient be fitted?
  2. Are there at least 1 residual degree of freedom and at least 2 groups?
  
  If check 2 fails, is only the coefficient reported?
- [ ] Data sufficiency is the option fixed at rules lock. Does "use what is available" waive only the threshold, and label the result exploratory?
- [ ] Calibration is a flag, not a gate. Is "calibration unavailable" shown with its reason when inference cannot run?
- [ ] Do the reference numbers still reproduce within the stated tolerances, with no tolerance widened?

**Outcomes and wording**
- [ ] A narrower question is a separate, linked record. Does the original get no verdict? (PRD 5.4)
- [ ] Are the three kinds of "nothing found" kept distinct: reported negative, missing evidence, failed search? (PRD 3.1)
- [ ] Are outcomes stated "in the sources searched"? Is it never claimed that data "do not exist"?

**Cost (PRD 8)**
- [ ] Is every model call recorded with tokens and actual cost (`model_call`)?
- [ ] Are the caps enforced: $2 per run, $50 per month?

**Data and tests**
- [ ] Do frozen files match their pinned fingerprints, with the manifest's own fingerprint and the list of required files pinned in the tests? (PRD 10, 15)
- [ ] Has no test been weakened, skipped or deleted, and no tolerance widened?
- [ ] Are new paths covered by tests?
- [ ] Has nothing been built ahead of the current step, and nothing from the backlog (PRD 18)?

**Secrets**
- [ ] Are there no keys, database URLs or passwords in code, tests, logs or committed files? Does `.env.example` hold names only?

## What comes back (PRD 13.2)
- A dated findings file in `docs/reviews/`.
- Each finding is either accepted, which means a fix plus a regression test, or rejected with a one-line reason in the same file.
- **Authority:** the reviewer advises; the test suite is the gate. A review cannot approve a change that fails the suite. A finding is acted on only after the owner accepts it.
````

## 4. Test output

`.venv/bin/pytest -v` on commit `eb3da7b`, Python 3.14.2, in the Codespace.

````text
============================= test session starts ==============================
platform linux -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- /workspaces/hypocurate/.venv/bin/python3
rootdir: /workspaces/hypocurate
configfile: pyproject.toml
testpaths: tests
collecting ... collected 91 items

tests/test_controlled_duplicates.py::test_rebuild_gives_identical_bytes PASSED [  1%]
tests/test_controlled_duplicates.py::test_extract_fingerprint_is_in_the_manifest PASSED [  2%]
tests/test_controlled_duplicates.py::test_truth_fingerprint PASSED       [  3%]
tests/test_controlled_duplicates.py::test_answer_material_is_not_under_data_or_the_package PASSED [  4%]
tests/test_controlled_duplicates.py::test_no_expected_outcomes_under_data PASSED [  5%]
tests/test_controlled_duplicates.py::test_no_row_answers_under_package PASSED [  6%]
tests/test_controlled_duplicates.py::test_manifest_points_to_nothing_holding_answers PASSED [  7%]
tests/test_controlled_duplicates.py::test_extract_carries_no_answer_columns PASSED [  8%]
tests/test_controlled_duplicates.py::test_one_answer_per_extract_row PASSED [  9%]
tests/test_controlled_duplicates.py::test_every_case_is_present_twice PASSED [ 10%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row1-exact_duplicate_verbatim] PASSED [ 12%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row2-exact_duplicate_verbatim] PASSED [ 13%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row3-exact_duplicate_renamed_alloy] PASSED [ 14%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row4-exact_duplicate_renamed_alloy] PASSED [ 15%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row5-possible_duplicate_unknown_paper] PASSED [ 16%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row6-possible_duplicate_unknown_paper] PASSED [ 17%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row7-not_duplicate_value_differs] PASSED [ 18%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row8-not_duplicate_value_differs] PASSED [ 19%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row9-not_duplicate_other_paper] PASSED [ 20%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row10-not_duplicate_other_paper] PASSED [ 21%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row11-not_duplicate_other_temperature] PASSED [ 23%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row12-not_duplicate_other_temperature] PASSED [ 24%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row13-missing_test_condition] PASSED [ 25%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row14-missing_test_condition] PASSED [ 26%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row15-not_duplicate_other_test_type] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row16-not_duplicate_other_test_type] PASSED [ 28%]
tests/test_controlled_duplicates.py::test_source_rows_are_in_reference_scope PASSED [ 29%]
tests/test_controlled_duplicates.py::test_verbatim_duplicates_are_byte_identical_lines PASSED [ 30%]
tests/test_controlled_duplicates.py::test_renamed_alloys_have_the_same_composition PASSED [ 31%]
tests/test_controlled_duplicates.py::test_unknown_paper_rows_have_no_reference PASSED [ 32%]
tests/test_controlled_duplicates.py::test_other_paper_rows_use_constructed_dois_not_found_in_mpea PASSED [ 34%]
tests/test_controlled_duplicates.py::test_changed_values_are_as_stated PASSED [ 35%]
tests/test_controlled_duplicates.py::test_missing_test_condition_rows_keep_their_paper PASSED [ 36%]
tests/test_controlled_duplicates.py::test_other_test_type_rows_are_compression_copies_of_tension_records PASSED [ 37%]
tests/test_controlled_duplicates.py::test_expected_handling[row1-exact_duplicate_verbatim] PASSED [ 38%]
tests/test_controlled_duplicates.py::test_expected_handling[row2-exact_duplicate_verbatim] PASSED [ 39%]
tests/test_controlled_duplicates.py::test_expected_handling[row3-exact_duplicate_renamed_alloy] PASSED [ 40%]
tests/test_controlled_duplicates.py::test_expected_handling[row4-exact_duplicate_renamed_alloy] PASSED [ 41%]
tests/test_controlled_duplicates.py::test_expected_handling[row5-possible_duplicate_unknown_paper] PASSED [ 42%]
tests/test_controlled_duplicates.py::test_expected_handling[row6-possible_duplicate_unknown_paper] PASSED [ 43%]
tests/test_controlled_duplicates.py::test_expected_handling[row7-not_duplicate_value_differs] PASSED [ 45%]
tests/test_controlled_duplicates.py::test_expected_handling[row8-not_duplicate_value_differs] PASSED [ 46%]
tests/test_controlled_duplicates.py::test_expected_handling[row9-not_duplicate_other_paper] PASSED [ 47%]
tests/test_controlled_duplicates.py::test_expected_handling[row10-not_duplicate_other_paper] PASSED [ 48%]
tests/test_controlled_duplicates.py::test_expected_handling[row11-not_duplicate_other_temperature] PASSED [ 49%]
tests/test_controlled_duplicates.py::test_expected_handling[row12-not_duplicate_other_temperature] PASSED [ 50%]
tests/test_controlled_duplicates.py::test_expected_handling[row13-missing_test_condition] PASSED [ 51%]
tests/test_controlled_duplicates.py::test_expected_handling[row14-missing_test_condition] PASSED [ 52%]
tests/test_controlled_duplicates.py::test_expected_handling[row15-not_duplicate_other_test_type] PASSED [ 53%]
tests/test_controlled_duplicates.py::test_expected_handling[row16-not_duplicate_other_test_type] PASSED [ 54%]
tests/test_controlled_duplicates.py::test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed PASSED [ 56%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row1-exact_duplicate_verbatim] PASSED [ 57%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row2-exact_duplicate_verbatim] PASSED [ 58%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row3-exact_duplicate_renamed_alloy] PASSED [ 59%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row4-exact_duplicate_renamed_alloy] PASSED [ 60%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row5-possible_duplicate_unknown_paper] PASSED [ 61%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row6-possible_duplicate_unknown_paper] PASSED [ 62%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row7-not_duplicate_value_differs] PASSED [ 63%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row8-not_duplicate_value_differs] PASSED [ 64%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row9-not_duplicate_other_paper] PASSED [ 65%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row10-not_duplicate_other_paper] PASSED [ 67%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row11-not_duplicate_other_temperature] PASSED [ 68%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row12-not_duplicate_other_temperature] PASSED [ 69%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row13-missing_test_condition] PASSED [ 70%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row14-missing_test_condition] PASSED [ 71%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row15-not_duplicate_other_test_type] PASSED [ 72%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row16-not_duplicate_other_test_type] PASSED [ 73%]
tests/test_frozen_sources.py::test_manifest_itself_is_unchanged PASSED   [ 74%]
tests/test_frozen_sources.py::test_manifest_covers_exactly_the_required_files PASSED [ 75%]
tests/test_frozen_sources.py::test_required_file_is_present[data/controlled_duplicates/extract.csv] PASSED [ 76%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/LICENSE] PASSED [ 78%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/MPEA_dataset.csv] PASSED [ 79%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 80%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/LICENSE] PASSED [ 81%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/inputs.csv] PASSED [ 82%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/MPEA_dataset.csv] PASSED [ 83%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/LICENSE] PASSED [ 84%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 85%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/inputs.csv] PASSED [ 86%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/LICENSE] PASSED [ 87%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/controlled_duplicates/extract.csv] PASSED [ 89%]
tests/test_frozen_sources.py::test_verify_reports_no_problems PASSED     [ 90%]
tests/test_frozen_sources.py::test_verify_detects_a_changed_byte PASSED  [ 91%]
tests/test_frozen_sources.py::test_both_sources_are_in_the_manifest PASSED [ 92%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[mpea] PASSED [ 93%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[tamu_fcc] PASSED [ 94%]
tests/test_frozen_sources.py::test_licence_texts_match_the_manifest PASSED [ 95%]
tests/test_frozen_sources.py::test_tamu_origin_is_the_zenodo_record PASSED [ 96%]
tests/test_frozen_sources.py::test_mpea_counts PASSED                    [ 97%]
tests/test_frozen_sources.py::test_tamu_counts PASSED                    [ 98%]
tests/test_frozen_sources.py::test_tamu_csv_view_agrees_with_the_spreadsheet PASSED [100%]

============================== 91 passed in 0.67s ==============================
````
