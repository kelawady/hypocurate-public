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
