# Build step 1 — summary for review

Date: 2026-10-04. Branch: `step-01-sources`. **Status: signed off by the owner, 2026-10-04.** PRD Section 15, step 1: "Sources frozen. Store copies of the MPEA dataset and the Texas A&M dataset with their fingerprints. Build the controlled duplicate extract."

The suite is the gate; this summary is for the second-model review (PRD 13.2). It describes the state **after** the fixes for the first review and the re-check. Both are listed below.

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
| `docs/reviews/checklist.md` | The reviewer's checklist (PRD 13.2). Approved by the owner as a working draft; may be amended after its first use in step 2. |

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
| 15–16 | **other test type** | tension → compression | not a duplicate (known different, not a possible duplicate). Under the reference plan (no test-type rule): within scope, distinct measurements, both enter. Under a tension-only plan: excluded by the test-type rule | no pair |

**Survivor rule (owner's decision, 2026-10-04, refining PRD 5.3):**
1. Prefer the record that comes directly from the original paper. This is detected by the original paper's DOI on the record.
2. If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

## Review findings and fixes (first review, ChatGPT, 2026-10-04)

The owner accepted all four findings. The review text is in `docs/reviews/step01_review_chatgpt.md`.

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
   - **What this does and does not establish:** keeping answer material under `tests/` is a **convention, checked by content tests, not an access guarantee**. Until the access layer is built, pipeline code with repository access could still open files under `tests/`. It could also open the review documents in `docs/reviews/`, which contain the answers too (this summary and the packets among them).
   - **Requirement recorded for step 5:** the access layer must give pipeline code an **explicit list of approved input files** (`data/sources/**` and the extract). `tests/` and `docs/reviews/` must be outside that list.
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

## Re-check (ChatGPT, 2026-10-04) and corrections

The re-check text is in `docs/reviews/step01_recheck_chatgpt.md`. Its verdict on each finding:

| Finding | Re-check status |
|---|---|
| 1 | partly closed |
| 2 | closed |
| 3 | partly closed |
| 4 | closed for this review, with owner approval still pending |

The reviewer named one blocker: a contradictory fixture label. Correcting it, the reviewer said, leaves no remaining step-1 blocker.

Corrections:
1. **Rows 15–16 contradiction.** The answer file labelled them "Incompatible measurements: outside the plan's scope" while stating that both enter under the reference plan.
   - Under the reference plan they are now labelled "Within scope under the reference plan: distinct measurements, not duplicates".
   - A new answer-file column, `handling_under_tension_only_plan`, gives the expected handling under a tension-only plan: excluded by the test-type rule. For every other row it reads "same as under the reference plan".
   - Two new tests check that no row is labelled out of scope while entering the analysis, and that the tension-only handling differs only for rows 15–16.
   - The reference plan is not changed.
2. **Answer isolation wording.** This summary, the fixtures README and the builder no longer describe isolation as guaranteed by directory placement. It is a convention until the step 5 access layer enforces an approved list of input files, and the review documents must be outside that list too (finding 1 above).
3. **Survivor rule wording.** Rule 1 now reads "the record that comes directly from the original paper", detected by the original paper's DOI on the record. This is in the answer file, the fixtures README and this summary.
4. **Two open items** were added for step 6 (items 2 and 3 below).

## Tests (93, all passing)

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

`tests/test_controlled_duplicates.py` (69):
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
- test-type rows are compression copies of tension records, within scope under the reference plan, and excluded under a tension-only plan;
- no row is labelled out of scope while entering the analysis;
- the tension-only handling differs only for the compression rows;
- the expected handling per case follows PRD 5.3;
- the survivor is stated per the owner's rule for every row.

### Suite result
```
$ .venv/bin/pytest -q
...........................................................................................
93 passed in 0.66s
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
2. **Step 6: permitted test types (owner decision pending).** The reference plan must state its permitted test types explicitly before eligibility is implemented. Its 77 MPEA records include one compression test (MPEA row 139, doi 10.1016/j.jallcom.2014.12.157, CoCrFeMnNi, 350 µm, 230 MPa). Membership in that result set must not itself define the rule. The reference plan is **not** changed now. Extract rows 15–16 give the expected handling both ways.
3. **Step 6: a non-MPEA survivor.** The behavioural tests for duplicate handling need a pair in which a source other than MPEA survives. In every pair of the current extract the MPEA record survives.
4. **Step 5 requirement:** the access layer gives pipeline code an explicit list of approved input files. `tests/` and `docs/reviews/` must be outside it (finding 1).
5. `docs/reviews/checklist.md` was approved as a working draft on 2026-10-04 and may be amended after its first use in step 2.
6. The suite does not yet run on GitHub (step 2).
7. Dependency versions are minimums, not a lock file. Revisit when the Docker image is built in step 2.
