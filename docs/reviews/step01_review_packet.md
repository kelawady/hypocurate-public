# Build step 1 — review packet for the second model

Date: 2026-10-04. Branch: `step-01-sources`. Code reviewed: commit `37f4ac8` (this packet is added in the next commit and changes no code).

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

You are reviewing build step 1 of HypoCurate (PRD Section 15): freezing the two data sources and building the controlled duplicate extract. Your review is advice; the test suite is the gate. Please return a dated findings file; each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

The fixed reviewer checklist (`docs/reviews/checklist.md`, PRD 13.2) does not exist yet. Until it does, these are the minimum questions from PRD 13.2:

- Can any role reach outcome values it should not see?
- Can anything change after the lock?
- Are records ever dropped or overwritten in the store?
- Do the eligibility rules match Section 5.3?
- Are the statistics what the plan states?
- Are there untested paths?
- Are secrets or keys exposed?

For this step the most relevant are: whether the frozen files are really protected against change; whether the duplicate extract and its expected answers match PRD 5.3; whether the answer file is truly out of the pipeline's reach; and untested paths.

## Contents

1. Step summary
2. Files added or changed in this step
3. Code, scripts and tests (full text)
4. Manifest
5. Controlled duplicate extract and its README
6. Answer file
7. Test output

## 1. Step summary

Full text of `docs/reviews/step01_summary.md`.

### `docs/reviews/step01_summary.md`

SHA-256 `7f27528b1e04020f0a4e3671ed1a31629df64e057ddfac606a724bcb496dd32b`, 8163 bytes.

````markdown
# Build step 1 — summary for review

Date: 2026-10-04. Branch: `step-01-sources`. PRD Section 15, step 1: "Sources frozen. Store copies of the MPEA dataset and the Texas A&M dataset with their fingerprints. Build the controlled duplicate extract."

The suite is the gate; this summary is for the second-model review (PRD 13.2).

## What was built

| Path | What it is |
|---|---|
| `data/sources/mpea/MPEA_dataset.csv`, `LICENSE` | MPEA dataset (Borg et al. 2020, Sci. Data 7:430), byte-for-byte from `CitrineInformatics/MPEA_dataset` at commit `d31e2510…` (2022-08-03, head of master). Apache-2.0, confirmed from the repository's LICENSE (the PRD said "to be confirmed"). |
| `data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx` | Texas A&M FCC dataset, the lab's raw spreadsheet: the source of record. |
| `data/sources/tamu_fcc/inputs.csv` | The authors' CSV of the same 94 rows, which adds computed descriptors. Kept as a verified view, on the owner's decision to freeze both. |
| `data/sources/tamu_fcc/LICENSE` | MIT. |
| `data/manifest.json` | For every frozen file: SHA-256, size, role, origin URL pinned to a commit, retrieval date (2026-10-04), licence, citation. For Texas A&M also the DOI 10.5281/zenodo.22798856, tag v1.1.0 / commit `11390ee5…`, the Zenodo archive's MD5 and the archive member path of each file. |
| `data/controlled_duplicates/extract.csv`, `README.md` | The controlled duplicate extract: 12 records in the MPEA column layout (see below). |
| `tests/fixtures/controlled_duplicates_truth.csv` | The expected answer for each extract row. |
| `hypocurate/sources/manifest.py` | `sha256_file`, `load_manifest`, `verify`. Will be reused for source versions in step 4. |
| `scripts/build_controlled_duplicates.py` | Deterministic builder of the extract and answer file. |
| `scripts/fetch_sources.py` | Manual tool: downloads every frozen file again from its pinned origin (and, with `--zenodo`, the Zenodo archive) and compares it with the manifest. Never overwrites. Not part of the suite, so the suite does not need the network. |
| `.gitattributes` | Marks `data/**` and `tests/fixtures/**` as `-text`, so git never converts line endings and a checkout on another machine keeps the fingerprinted bytes. |
| `pyproject.toml`, `README.md` | Package metadata (pandas, openpyxl; pytest for dev) and how to run the suite. |

Not built, as instructed: Docker, database, web, CI workflow, agents.

### Origin checks done once at freeze time
- Zenodo archive MD5 `dad706f3a6db0b96166f43c82a721bc8` matches the Zenodo record. The xlsx, csv and LICENSE inside it are byte-identical to the GitHub files at tag v1.1.0.
- `scripts/fetch_sources.py --zenodo` output on 2026-10-04: all 5 GitHub files OK, Zenodo archive OK, all 3 archive members OK. "ALL MATCH".

### Controlled duplicate extract
Each row is one listed MPEA row, copied unchanged or with listed columns changed. All 12 source rows are among the 77 records eligible under the reference plan, from 8 papers.

| Rows | Case | Change | Expected (PRD 5.3) |
|---|---|---|---|
| 1–2 | exact duplicate, verbatim | none: byte-identical line | duplicate; kept; counted once |
| 3–4 | exact duplicate, renamed alloy | formula `CoCrFeMnNi`, `Co4Cr1Ni4` (same atomic %) | duplicate; kept; counted once |
| 5–6 | paper unknown | reference ID, DOI, year, title blanked | **flagged as possible duplicate, kept, not removed**; counted once in primary; both counted in sensitivity |
| 7–8 | same paper, alloy, grain size; value differs | YS × 1.3 | not a duplicate; both enter |
| 9–10 | same alloy, grain size, value; other paper | DOI → constructed `10.5555/hypocurate-test-000n` | not a duplicate; both enter |
| 11–12 | same except test temperature | 25 → −196 °C | not a duplicate; out of scope for a room-temperature plan |

Every row of the answer file has `kept_in_store = yes` and `removed_from_store = no` (stored is not analysed).

## Changes from the approved plan
1. **Answer file under `tests/fixtures/`, not `data/`** (owner's instruction). For the same reason the builder lives in `scripts/`, not in the `hypocurate` package, so no runtime code contains the answers. Nothing under `data/` or `hypocurate/` names the answer file, and a test enforces this. The first run of that test caught the data README naming the path. The README was fixed; the test was not changed.
2. **Unknown-paper case** states "Flagged as a possible duplicate, kept, not removed" (owner's instruction), and a test checks it.
3. Manifest at `data/manifest.json` (not `data/sources/manifest.json`), because it also covers the extract.

## Tests added (55, all passing)

`tests/test_frozen_sources.py` (16):
- each of the 6 manifest files matches its SHA-256 and size;
- `verify` reports nothing on the real files and reports a single altered byte in a copy;
- both sources are in the manifest with origin, commit-pinned URLs, retrieval date and licence;
- licence texts are Apache-2.0 and MIT;
- the Texas A&M origin is the Zenodo DOI and v1.1.0;
- **MPEA: 1,545 records, 237 with grain size**;
- **Texas A&M: 94 samples, 82 compositions**, exactly 1 without yield strength (BBA09), grain size present for all;
- the CSV view equals the spreadsheet on composition, grain size, YS, HV, their SDs and processing.

`tests/test_controlled_duplicates.py` (39):
- rebuilding gives byte-identical extract and answer file;
- the extract's fingerprint is in the manifest; the answer file's fingerprint is pinned in the test;
- the answer file is not reachable from `data/` or the package; the extract has no answer columns;
- 12 rows, 2 per case;
- each row differs from its MPEA source in exactly the stated columns;
- source rows are in reference scope and span 8 papers;
- verbatim rows are byte-identical lines;
- renamed alloys have the same composition;
- constructed DOIs do not occur in MPEA;
- changed values are as stated;
- expected handling per case follows PRD 5.3.

### Suite result
```
$ .venv/bin/pytest -q
.......................................................                  [100%]
55 passed in 0.56s
```
Tamper check (scratch copy of the repository, one byte of `tamu_fcc/inputs.csv` flipped): `test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/inputs.csv]` and `test_verify_reports_no_problems` fail; 2 failed, 53 passed. Not committed.

Environment: Codespace, Python 3.14.2, pandas 3.0.6, openpyxl 3.1.5, pytest 9.1.1, in `.venv` (gitignored).

## Checked but not yet tested (later steps)
At freeze time, using the method of `docs/reference/worked_example.py` on the frozen files (scratch script, not committed), the results match the PRD:
- MPEA alone: 77 records, 13 alloys, 20 papers; k = 427.2 ± 61.4; p = 6.2e-7.
- Texas A&M alone: 21 eligible records, 9 alloys, 72 not eligible; k ≈ 1173.
- Pooled: 98 records, 22 alloys, 21 groups, 75 residual df; k = 428.0 ± 63.5.

The eligibility counts and reference numbers become tests in steps 6–7, not now.

The 77 eligible MPEA records contain no exact duplicates of each other. The file's 32 internally duplicated rows are all out of scope, so "counted once" does not disturb the reference numbers. Two natural groups share paper, alloy and grain size with different values (MPEA rows 752–754 and 1033–1034). Duplicate detection must not merge them.

## Open items
1. **Pooled p-value.** PRD 5.7/10 and CLAUDE.md state pooled p ≈ 8e-7; recomputation gives 7.4e-7 (statsmodels 0.15.0), while k and its SE match. To be settled before the step 7 reference test (owner agreed).
2. `docs/reviews/checklist.md` (PRD 13.2) does not exist yet; the reviewer's fixed checklist should be added before or with this review.
3. The suite does not yet run on GitHub (step 2).
4. Dependency versions are minimums, not a lock file; revisit when the Docker image is built in step 2.

## Questions for the reviewer
- Are the six duplicate cases sufficient for PRD 14.1 "Duplicates", or is a case missing (for example a possible duplicate where only the test type differs)?
- Is keeping both the raw spreadsheet and the authors' derived CSV a risk for step 4, given that the CSV also carries computed descriptors?
````

## 2. Files added or changed in this step

`git diff --name-status main..37f4ac8` (A = added, M = modified).

| Status | Path | In this packet |
|---|---|---|
| A | `.gitattributes` | section 3 |
| M | `README.md` | section 3 |
| A | `data/controlled_duplicates/README.md` | section 5 |
| A | `data/controlled_duplicates/extract.csv` | section 5 |
| A | `data/manifest.json` | section 4 |
| A | `data/sources/mpea/LICENSE` | not included: frozen licence text (fingerprint in the manifest, section 4) |
| A | `data/sources/mpea/MPEA_dataset.csv` | not included: frozen source data (fingerprint in the manifest, section 4) |
| A | `data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx` | not included: frozen source data (fingerprint in the manifest, section 4) |
| A | `data/sources/tamu_fcc/LICENSE` | not included: frozen licence text (fingerprint in the manifest, section 4) |
| A | `data/sources/tamu_fcc/inputs.csv` | not included: frozen source data (fingerprint in the manifest, section 4) |
| A | `docs/reviews/step01_summary.md` | section 1 |
| A | `hypocurate/__init__.py` | section 3 |
| A | `hypocurate/sources/__init__.py` | section 3 |
| A | `hypocurate/sources/manifest.py` | section 3 |
| A | `pyproject.toml` | section 3 |
| A | `scripts/build_controlled_duplicates.py` | section 3 |
| A | `scripts/fetch_sources.py` | section 3 |
| A | `tests/fixtures/controlled_duplicates_truth.csv` | section 6 |
| A | `tests/test_controlled_duplicates.py` | section 3 |
| A | `tests/test_frozen_sources.py` | section 3 |

## 3. Code, scripts and tests (full text)

Package, then scripts, then tests, then configuration and the repository README.

### `hypocurate/__init__.py`

SHA-256 `850b2f626a6c503d0b25cd24054712f174994c228613fe6616e0692099398198`, 79 bytes.

````python
"""HypoCurate: tests a hypothesis in words against registered data sources."""
````

### `hypocurate/sources/__init__.py`

SHA-256 `9987596ccdd1a24b7b0dde1ac8d36d826a8549014d98ed21ebafab77f7ddf167`, 86 bytes.

````python
"""Data sources: frozen copies, their fingerprints and (from step 4) the adapters."""
````

### `hypocurate/sources/manifest.py`

SHA-256 `6a94e50bc527d94dc9c814dde5a3211f6ba265aa11c4fd9cf119cc2df5b06ca1`, 2019 bytes.

````python
"""Fingerprints of the frozen files (PRD Sections 10 and 15, step 1).

`data/manifest.json` records, for every frozen file, its SHA-256, its size, its
licence and its exact origin. `verify` compares the files on disk against it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data" / "manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class FileEntry:
    group: str  # "sources/<id>" or "controlled_duplicates"
    path: str  # relative to the repository root
    sha256: str
    bytes: int


def file_entries(manifest: dict) -> list[FileEntry]:
    entries = []
    for source_id, source in manifest["sources"].items():
        for f in source["files"]:
            entries.append(FileEntry(f"sources/{source_id}", f["path"], f["sha256"], f["bytes"]))
    for f in manifest["controlled_duplicates"]["files"]:
        entries.append(FileEntry("controlled_duplicates", f["path"], f["sha256"], f["bytes"]))
    return entries


def verify(manifest: dict, root: Path = REPO_ROOT) -> list[str]:
    """Return one message per mismatch; an empty list means every file matches."""
    problems = []
    for e in file_entries(manifest):
        p = root / e.path
        if not p.is_file():
            problems.append(f"{e.path}: missing")
            continue
        size = p.stat().st_size
        if size != e.bytes:
            problems.append(f"{e.path}: size {size} != {e.bytes}")
        digest = sha256_file(p)
        if digest != e.sha256:
            problems.append(f"{e.path}: sha256 {digest} != {e.sha256}")
    return problems
````

### `scripts/build_controlled_duplicates.py`

SHA-256 `f0319ce499a4a98859e974d34488c792a49e93da391613d7280467640dfeda63`, 8435 bytes.

````python
"""Build the controlled duplicate extract (PRD Sections 5.3, 10 and 14.1).

The two sprint sources share no measurements, so duplicate handling is tested on
a small extract built from the frozen MPEA dataset that overlaps it in a known
way. Every row of the extract is derived from one listed MPEA row, so the truth
is known by construction.

Outputs:
  data/controlled_duplicates/extract.csv          the extract, in the MPEA column layout
  tests/fixtures/controlled_duplicates_truth.csv  the expected answer per row

The answer file lives under tests/, outside data/ and outside the hypocurate
package, so no part of the pipeline (and so no agent) can read it. This script
is not part of the package for the same reason.

The build is deterministic: running it again on the frozen MPEA file gives the
same bytes, and a test checks that.

    python scripts/build_controlled_duplicates.py
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MPEA_PATH = REPO_ROOT / "data" / "sources" / "mpea" / "MPEA_dataset.csv"
EXTRACT_PATH = REPO_ROOT / "data" / "controlled_duplicates" / "extract.csv"
TRUTH_PATH = REPO_ROOT / "tests" / "fixtures" / "controlled_duplicates_truth.csv"

# MPEA column positions used below (header names in the frozen file).
REF_ID = 0  # IDENTIFIER: Reference ID (one value per paper)
FORMULA = 1  # FORMULA
TEMPERATURE = 10  # PROPERTY: Test temperature ($^\circ$C)
YS = 11  # PROPERTY: YS (MPa)
DOI = 20  # REFERENCE: doi
YEAR = 21  # REFERENCE: year
TITLE = 22  # REFERENCE: title

TEST_DOI_PREFIX = "10.5555/hypocurate-test-"  # 10.5555 is a test prefix; never a real paper here
CONSTRUCTED_TITLE = "Constructed record: HypoCurate controlled duplicate extract (not a real paper)"

KEPT = "yes"
NOT_REMOVED = "no"

# Each case: the PRD 5.3 class it exercises and the expected handling.
CASES = {
    "exact_duplicate_verbatim": dict(
        duplicate_status="exact_duplicate",
        prd_class="Exact duplicate: the same measurement reported by two sources",
        primary_analysis="counted once",
        sensitivity_analysis="none",
        explanation="Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions.",
    ),
    "exact_duplicate_renamed_alloy": dict(
        duplicate_status="exact_duplicate",
        prd_class="Exact duplicate: the same measurement reported by two sources",
        primary_analysis="counted once",
        sensitivity_analysis="none",
        explanation="Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition.",
    ),
    "possible_duplicate_unknown_paper": dict(
        duplicate_status="possible_duplicate",
        prd_class="Possible duplicate that cannot be resolved",
        primary_analysis="counted once",
        sensitivity_analysis="both counted separately",
        explanation="Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed.",
    ),
    "not_duplicate_value_differs": dict(
        duplicate_status="not_duplicate",
        prd_class="Comparable specimens and conditions; the values truly differ",
        primary_analysis="both enter",
        sensitivity_analysis="none",
        explanation="Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate.",
    ),
    "not_duplicate_other_paper": dict(
        duplicate_status="not_duplicate",
        prd_class="Comparable specimens and conditions; the values truly differ",
        primary_analysis="both enter",
        sensitivity_analysis="none",
        explanation="Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper.",
    ),
    "not_duplicate_other_temperature": dict(
        duplicate_status="not_duplicate",
        prd_class="Incompatible measurements: outside the plan's scope",
        primary_analysis="not eligible under a room-temperature plan",
        sensitivity_analysis="none",
        explanation="Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate.",
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
            c["explanation"],
        ]))
    return "".join(extract), "".join(truth)


def main() -> None:
    extract, truth = build()
    EXTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXTRACT_PATH.write_text(extract, encoding="utf-8", newline="")
    TRUTH_PATH.write_text(truth, encoding="utf-8", newline="")
    print(f"wrote {EXTRACT_PATH.relative_to(REPO_ROOT)} and {TRUTH_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
````

### `scripts/fetch_sources.py`

SHA-256 `e3a37d5edbed8e44c7cf71e87fd6ea90bda9a53e915af65d6cb22e636b0a9a0f`, 2992 bytes.

````python
"""Download the frozen source files again from their pinned origins and check them.

A manual tool, not part of the test suite (the suite must not depend on the
network). It never overwrites the frozen copies: it only reports whether each
origin still serves the exact bytes recorded in data/manifest.json.

    python scripts/fetch_sources.py            # check each file at its pinned GitHub URL
    python scripts/fetch_sources.py --zenodo   # also download the Zenodo archive (about 49 MB)
                                               # and check its MD5 and the files inside it

Exit status 0 means every check passed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hypocurate.sources.manifest import load_manifest  # noqa: E402


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "hypocurate-fetch-sources"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def check(label: str, data: bytes, sha256: str, size: int) -> bool:
    digest = hashlib.sha256(data).hexdigest()
    ok = digest == sha256 and len(data) == size
    print(f"{'OK  ' if ok else 'FAIL'} {label}  sha256={digest}  bytes={len(data)}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zenodo", action="store_true", help="also check the Zenodo archive")
    args = parser.parse_args()

    manifest = load_manifest()
    ok = True
    for source_id, source in manifest["sources"].items():
        for f in source["files"]:
            try:
                data = fetch(f["origin_url"])
            except Exception as e:  # report and carry on: a failed fetch is not a match
                print(f"FAIL {source_id}: {f['path']}  could not fetch: {e}")
                ok = False
                continue
            ok &= check(f"{source_id}: {f['path']} <- {f['origin_url']}", data, f["sha256"], f["bytes"])

    if args.zenodo:
        source = manifest["sources"]["tamu_fcc"]
        z = source["zenodo_archive"]
        archive = fetch(z["url"])
        md5 = hashlib.md5(archive).hexdigest()
        archive_ok = md5 == z["md5"] and len(archive) == z["bytes"]
        print(f"{'OK  ' if archive_ok else 'FAIL'} tamu_fcc: Zenodo archive md5={md5} bytes={len(archive)}")
        ok &= archive_ok
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            for f in source["files"]:
                member = z["member_prefix"] + f["archive_member"]
                ok &= check(f"tamu_fcc: {f['path']} <- Zenodo {member}", zf.read(member), f["sha256"], f["bytes"])

    print("ALL MATCH" if ok else "MISMATCH: do not substitute another source; report it")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
````

### `tests/test_frozen_sources.py`

SHA-256 `cd63a275f81f9bcade5dd20f9c4378e896ee88764a86bfc186031b57973d0491`, 4665 bytes.

````python
"""Step 1: the two sources are frozen, fingerprinted and as the PRD describes (Section 10)."""
import pandas as pd
import pytest

from hypocurate.sources.manifest import REPO_ROOT, file_entries, load_manifest, sha256_file, verify

MANIFEST = load_manifest()
MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
TAMU_XLSX = REPO_ROOT / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
TAMU_CSV = REPO_ROOT / "data/sources/tamu_fcc/inputs.csv"
ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]


# --- fingerprints -------------------------------------------------------------

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

### `tests/test_controlled_duplicates.py`

SHA-256 `b67700d3273d750b9f83379bdab75a383490af115ebc78aaeb5f569c2eec0cfa`, 7990 bytes.

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
````

### `pyproject.toml`

SHA-256 `d2ce8e41b7f4a493dbdc50f1fca13707d12b1de10b1702aea62b3ff6fa1cafa8`, 485 bytes.

````toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "hypocurate"
version = "0.1.0"
description = "Tests a scientific hypothesis in words against registered data sources."
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.2",
    "openpyxl>=3.1",
]

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.setuptools.packages.find]
include = ["hypocurate*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
````

### `.gitattributes`

SHA-256 `69a748dff37fdb7a5f5387735d99059d4269e8cc70436d1ec2e86ab7f3827c50`, 115 bytes.

````text
# Frozen data: never convert line endings (fingerprints are of exact bytes).
data/** -text
tests/fixtures/** -text
````

### `README.md`

SHA-256 `a3b8b02eb5102593b58a20b04713435a251fdcf3a59cc23b8469b52b08bc7854`, 1418 bytes.

````markdown
# hypocurate

HypoCurate takes a scientific hypothesis in words, searches registered data sources, and reports whether the data in the sources searched are sufficient, partly sufficient or insufficient to test it. The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md); the rules for working on the code are in [CLAUDE.md](CLAUDE.md).

## Status

Build step 1 of 12 (PRD Section 15): the two data sources are frozen with their fingerprints, and the controlled duplicate extract is built. Docker, the database, the website and the agents come in later steps.

## Run the test suite (in the Codespace)

```
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Data

| Path | What it is |
|---|---|
| `data/manifest.json` | Fingerprint (SHA-256), size, licence, origin and retrieval date of every frozen file |
| `data/sources/mpea/` | MPEA dataset (Borg et al. 2020), Apache-2.0 |
| `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT |
| `data/controlled_duplicates/` | Constructed extract for testing duplicate detection; see its README |

To check that the origins still serve the same bytes (needs network; never overwrites the frozen copies):

```
.venv/bin/python scripts/fetch_sources.py            # pinned GitHub files
.venv/bin/python scripts/fetch_sources.py --zenodo   # also the Zenodo archive (about 49 MB)
```
````

## 4. Manifest

### `data/manifest.json`

SHA-256 `8b209b387eebfc3c301b4dd473c6cc4a73abb31a6d1230c4ff57e0c4c0afea98`, 4621 bytes.

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
    "built_by": "scripts/build_controlled_duplicates.py",
    "built_from": "data/sources/mpea/MPEA_dataset.csv",
    "built": "2026-10-04",
    "files": [
      {
        "path": "data/controlled_duplicates/extract.csv",
        "role": "extract",
        "sha256": "6aa33a6276c7fb77fad21fac34c684949b58b4e50ae3d55d8df1e4e533637926",
        "bytes": 2993
      }
    ]
  }
}
````

## 5. Controlled duplicate extract and its README

### `data/controlled_duplicates/README.md`

SHA-256 `c034687be89d5694569fd8490a92bb0c470954f768cd8f60754d851c07631d11`, 2167 bytes.

````markdown
# Controlled duplicate extract

**Constructed test data.** These 12 records are built from the frozen MPEA dataset (`data/sources/mpea/MPEA_dataset.csv`) by `scripts/build_controlled_duplicates.py`. They exist only to test duplicate detection (PRD Sections 5.3, 10 and 14.1). They are never pooled into a real analysis or a reference run.

The two sprint sources share no measurements, so this extract overlaps the MPEA dataset in a known way. The truth is known by construction.

## Format

The same columns as the MPEA dataset, with the header copied verbatim. Each row is one MPEA record, either copied unchanged or with the listed columns changed.

## The cases

All source rows are among the records eligible under the reference plan, from eight papers.

| Rows | Case | What was changed | Duplicate? |
|---|---|---|---|
| 1–2 | Exact duplicate, verbatim | nothing (byte-for-byte copy) | yes |
| 3–4 | Exact duplicate, renamed alloy | formula written differently (`CoCrFeMnNi`, `Co4Cr1Ni4`); same composition in atomic percent | yes |
| 5–6 | Paper unknown | reference ID, DOI, year and title blanked | possible: flagged, kept, not removed |
| 7–8 | Same paper, alloy and grain size; value differs | yield strength × 1.3 | no |
| 9–10 | Same alloy, grain size and value; other paper | DOI set to a constructed `10.5555/hypocurate-test-…` reference | no |
| 11–12 | Same everything except test temperature | 25 °C → −196 °C | no (conditions differ) |

Two records count as duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions (PRD 5.3). Matching alloy and grain size alone is not enough.

## Where the answers are

The expected result for each row is kept with the tests, outside `data/` and outside the `hypocurate` package, so no part of the pipeline can read it. Nothing under `data/` names its location; a test checks that.

## Rebuilding

```
python scripts/build_controlled_duplicates.py
```

This writes the same bytes every time. A test checks that rebuilding gives exactly the committed extract and answer file, and the extract's fingerprint is in `data/manifest.json`.
````

### `data/controlled_duplicates/extract.csv`

SHA-256 `6aa33a6276c7fb77fad21fac34c684949b58b4e50ae3d55d8df1e4e533637926`, 2993 bytes.

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
````

## 6. Answer file

Kept under `tests/fixtures/`, outside `data/` and the `hypocurate` package, so no part of the pipeline can read it.

### `tests/fixtures/controlled_duplicates_truth.csv`

SHA-256 `b5742da9c5118f52c78d62325b02164033a422e0e5a602212363abf40a3692a6`, 4438 bytes.

````csv
extract_row,case,mpea_row,mpea_reference_id,mpea_doi,changed_columns,duplicate_status,prd_5_3_class,kept_in_store,removed_from_store,primary_analysis,sensitivity_analysis,explanation
1,exact_duplicate_verbatim,1315,252,10.1007/s11661-019-05231-y,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,"Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
2,exact_duplicate_verbatim,812,144,10.1016/j.ijplas.2018.10.005,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,"Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
3,exact_duplicate_renamed_alloy,1316,252,10.1007/s11661-019-05231-y,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,"Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
4,exact_duplicate_renamed_alloy,1007,208,10.1016/j.actamat.2019.04.017,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,"Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,"Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,"Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
7,not_duplicate_value_differs,1278,248,10.1016/j.msea.2019.138039,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,"Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
8,not_duplicate_value_differs,986,204,10.1016/j.intermet.2019.106477,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,"Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
9,not_duplicate_other_paper,1035,211,10.1016/j.msea.2019.04.025,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,"Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
10,not_duplicate_other_paper,764,98,10.1016/j.actamat.2018.12.015,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,"Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
11,not_duplicate_other_temperature,1313,252,10.1007/s11661-019-05231-y,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,"Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
12,not_duplicate_other_temperature,1086,221,10.1016/j.msea.2018.12.077,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,"Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
````

## 7. Test output

`.venv/bin/pytest -v` on commit `37f4ac8`, Python 3.14.2, in the Codespace.

````text
============================= test session starts ==============================
platform linux -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- /workspaces/hypocurate/.venv/bin/python3
rootdir: /workspaces/hypocurate
configfile: pyproject.toml
testpaths: tests
collecting ... collected 55 items

tests/test_controlled_duplicates.py::test_rebuild_gives_identical_bytes PASSED [  1%]
tests/test_controlled_duplicates.py::test_extract_fingerprint_is_in_the_manifest PASSED [  3%]
tests/test_controlled_duplicates.py::test_truth_fingerprint PASSED       [  5%]
tests/test_controlled_duplicates.py::test_answer_file_is_not_under_data_or_the_package PASSED [  7%]
tests/test_controlled_duplicates.py::test_no_package_code_or_data_refers_to_the_answer_file PASSED [  9%]
tests/test_controlled_duplicates.py::test_extract_carries_no_answer_columns PASSED [ 10%]
tests/test_controlled_duplicates.py::test_one_answer_per_extract_row PASSED [ 12%]
tests/test_controlled_duplicates.py::test_every_case_is_present_twice PASSED [ 14%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row1-exact_duplicate_verbatim] PASSED [ 16%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row2-exact_duplicate_verbatim] PASSED [ 18%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row3-exact_duplicate_renamed_alloy] PASSED [ 20%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row4-exact_duplicate_renamed_alloy] PASSED [ 21%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row5-possible_duplicate_unknown_paper] PASSED [ 23%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row6-possible_duplicate_unknown_paper] PASSED [ 25%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row7-not_duplicate_value_differs] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row8-not_duplicate_value_differs] PASSED [ 29%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row9-not_duplicate_other_paper] PASSED [ 30%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row10-not_duplicate_other_paper] PASSED [ 32%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row11-not_duplicate_other_temperature] PASSED [ 34%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row12-not_duplicate_other_temperature] PASSED [ 36%]
tests/test_controlled_duplicates.py::test_source_rows_are_in_reference_scope PASSED [ 38%]
tests/test_controlled_duplicates.py::test_verbatim_duplicates_are_byte_identical_lines PASSED [ 40%]
tests/test_controlled_duplicates.py::test_renamed_alloys_have_the_same_composition PASSED [ 41%]
tests/test_controlled_duplicates.py::test_unknown_paper_rows_have_no_reference PASSED [ 43%]
tests/test_controlled_duplicates.py::test_other_paper_rows_use_constructed_dois_not_found_in_mpea PASSED [ 45%]
tests/test_controlled_duplicates.py::test_changed_values_are_as_stated PASSED [ 47%]
tests/test_controlled_duplicates.py::test_expected_handling[row1-exact_duplicate_verbatim] PASSED [ 49%]
tests/test_controlled_duplicates.py::test_expected_handling[row2-exact_duplicate_verbatim] PASSED [ 50%]
tests/test_controlled_duplicates.py::test_expected_handling[row3-exact_duplicate_renamed_alloy] PASSED [ 52%]
tests/test_controlled_duplicates.py::test_expected_handling[row4-exact_duplicate_renamed_alloy] PASSED [ 54%]
tests/test_controlled_duplicates.py::test_expected_handling[row5-possible_duplicate_unknown_paper] PASSED [ 56%]
tests/test_controlled_duplicates.py::test_expected_handling[row6-possible_duplicate_unknown_paper] PASSED [ 58%]
tests/test_controlled_duplicates.py::test_expected_handling[row7-not_duplicate_value_differs] PASSED [ 60%]
tests/test_controlled_duplicates.py::test_expected_handling[row8-not_duplicate_value_differs] PASSED [ 61%]
tests/test_controlled_duplicates.py::test_expected_handling[row9-not_duplicate_other_paper] PASSED [ 63%]
tests/test_controlled_duplicates.py::test_expected_handling[row10-not_duplicate_other_paper] PASSED [ 65%]
tests/test_controlled_duplicates.py::test_expected_handling[row11-not_duplicate_other_temperature] PASSED [ 67%]
tests/test_controlled_duplicates.py::test_expected_handling[row12-not_duplicate_other_temperature] PASSED [ 69%]
tests/test_controlled_duplicates.py::test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed PASSED [ 70%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/MPEA_dataset.csv] PASSED [ 72%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/LICENSE] PASSED [ 74%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 76%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/inputs.csv] PASSED [ 78%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/LICENSE] PASSED [ 80%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/controlled_duplicates/extract.csv] PASSED [ 81%]
tests/test_frozen_sources.py::test_verify_reports_no_problems PASSED     [ 83%]
tests/test_frozen_sources.py::test_verify_detects_a_changed_byte PASSED  [ 85%]
tests/test_frozen_sources.py::test_both_sources_are_in_the_manifest PASSED [ 87%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[mpea] PASSED [ 89%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[tamu_fcc] PASSED [ 90%]
tests/test_frozen_sources.py::test_licence_texts_match_the_manifest PASSED [ 92%]
tests/test_frozen_sources.py::test_tamu_origin_is_the_zenodo_record PASSED [ 94%]
tests/test_frozen_sources.py::test_mpea_counts PASSED                    [ 96%]
tests/test_frozen_sources.py::test_tamu_counts PASSED                    [ 98%]
tests/test_frozen_sources.py::test_tamu_csv_view_agrees_with_the_spreadsheet PASSED [100%]

============================== 55 passed in 0.63s ==============================
````
