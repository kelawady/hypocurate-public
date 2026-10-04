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
