# Build step 4 — review packet for the second model

Date: 2026-10-05. Branch: `step-04-adapters`. Code reviewed: commit `cb0f814` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success, 445 passed, https://github.com/kelawady/hypocurate/actions/runs/37256382423.

Generated from the files on disk by a script, so every file below is quoted exactly. The frozen data files are not reproduced; they are unchanged since step 1 (their fingerprints are in `data/manifest.json` and pinned by the step 1 tests).

## How to use this packet

You are reviewing build step 4 of HypoCurate (PRD Section 15): sources and harmonization. It includes:
- the three frozen sources registered as sealed source versions (MPEA, Texas A&M, the controlled duplicate extract);
- one adapter per source, returning records in a common record format;
- a read-only "test connection" that returns sample records, and its command line;
- a retry helper for every write path.

Not in this step: the access layer, agents, eligibility or duplicate decisions, statistics, screens, storing records, any migration.

Your review is advice; the test suite is the gate. Please return a dated findings file. Each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

Use the fixed checklist in section 2, answering each item yes, no or not applicable to this change, with a reason for every "no". For this step the most relevant items are:
- **Stored is not analysed**: does an adapter ever drop, overwrite or silently correct a record, or decide eligibility?
- **Who decides**: is any decision made in the adapters rather than by later code under the locked plan?
- **Data and tests**: are the frozen sources read exactly, and are the tests meaningful?
- **Secrets**: does anything print the database URL?

Beyond the checklist, please look at:
- the digest and identity code in `versions.py` against the database's definitions (summary, "Requirements carried from step 3");
- the locking and retry on the registration path (owner's question 1);
- how assigned values are kept distinguishable from reported ones (`record.py`, `tamu_fcc.py`);
- the "Questions for the reviewer" at the end of the summary.

## Contents

1. Step summary
2. Reviewer checklist
3. Application code: write retry and source versions
4. Application code: record format, normalizers and adapters
5. Application code: test connection and command line
6. Tests
7. Image check and README
8. Test output

## Files added, modified or deleted since `main` (step 3 live record)

```
M	README.md
M	hypocurate/cli.py
A	hypocurate/db/retry.py
A	hypocurate/sources/adapters/__init__.py
A	hypocurate/sources/adapters/mpea_layout.py
A	hypocurate/sources/adapters/tamu_fcc.py
A	hypocurate/sources/connection.py
A	hypocurate/sources/normalize.py
A	hypocurate/sources/record.py
A	hypocurate/sources/versions.py
M	scripts/check_runtime_image.py
A	tests/source_helpers.py
A	tests/test_adapter_extract.py
A	tests/test_adapter_mpea.py
A	tests/test_adapter_tamu.py
A	tests/test_reference_counts_from_adapters.py
A	tests/test_source_connection.py
A	tests/test_source_versions.py
A	tests/test_write_retry.py
```

Also added in the next commit: `docs/reviews/step04_summary.md` and this packet.

## 1. Step summary

### `docs/reviews/step04_summary.md`

````markdown
# Build step 4 — summary for review

Date: 2026-10-05. Branch: `step-04-adapters`. **Status: built, suite passing; awaiting the second-model review.** PRD Section 15, step 4: "Sources and harmonization. The CSV adapter, both sources, the common record format, and source versions."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`.

The owner approved the plan on 2026-10-05 after three questions (below), with one addition: a report on test temperature and test type in the MPEA reference records (section "Owner's addition").

**Not built, as instructed:** the access layer, any agent, eligibility or duplicate decisions, statistics, screens. No migration, no `render.yaml` change, no workflow change. Records are **not stored**: a `record` row needs an extraction run after its rules lock (step 3 rule), so storing waits for steps 6 and 8. The sources are **not registered on the live database**: that needs the owner (open item 1).

## What was built

| Path | What it is |
|---|---|
| `hypocurate/db/retry.py` | `run_transaction(engine, fn)`: runs `fn(conn)` in one transaction; on SQLSTATE `40P01` or `40001` reruns the whole transaction (at most 5 attempts); any other error is raised unchanged. |
| `hypocurate/sources/versions.py` | `files_digest` and `version_identity` (Python copies of `hc_files_digest` and `hc_version_identity`); the three source definitions (`SOURCES`); `safe_path_within`; `register`; `load_sealed_version`; `latest_sealed_version_id`. |
| `hypocurate/sources/record.py` | The common record format: `CommonRecord`, `Value`, `Reported`, `Group`, `Citation`, `AdapterResult`, `AdapterError`. |
| `hypocurate/sources/normalize.py` | Number parsing; formula → atomic %; percentage columns → atomic %; the canonical alloy label. |
| `hypocurate/sources/adapters/mpea_layout.py` | Adapter for the MPEA column layout: the MPEA dataset and the controlled duplicate extract. |
| `hypocurate/sources/adapters/tamu_fcc.py` | Adapter for the Texas A&M spreadsheet. |
| `hypocurate/sources/adapters/__init__.py` | `ADAPTERS` (source key → adapter) and `read(version)`. |
| `hypocurate/sources/connection.py` | `test_connection(engine, key, n)`: "test connection and show sample records" (PRD 9.6). |
| `hypocurate/cli.py` | `hypocurate sources register [keys…]`, `hypocurate sources test <key> [-n N]`. |
| `scripts/check_runtime_image.py` | `REQUIRED` gains the adapter modules and the three data files. |
| `README.md` | Status line; a "Sources and adapters" section. |

## The owner's decisions (2026-10-05)

1. **Locking for source registration (question 1).** `hc_write_lock` covers runs and hypothesis versions only, and rejects a call that names neither. Registering a source writes neither (only `source`, `source_version`, `source_file`), so `hc_write_lock` does not apply. **Decision: lock the source row.**
   - `register` runs in `run_transaction`.
   - Inside it: `INSERT … ON CONFLICT (key) DO NOTHING`, then `SELECT … FROM source WHERE key = :key FOR UPDATE`, then the version, its files and the seal, all in that one transaction.
   - No migration.
2. **Grain-size transformation (question 2).** PRD 10 says harmonization covers "the grain-size transformation the plan asks for", but no plan exists before step 6. **Decision: later, from the plan.** Adapters give grain size in µm only. The transformation the locked plan names is applied by code when the analysis dataset is built (steps 6/7).
3. **Texas A&M test temperature and test type (questions 3 and 3b).** **Decision:** assign a value only on an explicit statement in the source, quoted with its location; otherwise leave it not reported and tell the owner. Assigned values must stay distinguishable from reported ones everywhere they are stored or shown. The search and its result are in the next section.

## Texas A&M: what the source states, and what the adapter assigns

Searched: every text file of `ArroyaveLab/2026-mulukutla-hall-petch` at the pinned commit `11390ee516c1a17cacdde318b40d5d6889d4007f`: `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/reproducing.md`, `docs/validation_protocol.md`, `results/*.txt`, `paper/main.tex` and `paper/supplementary.tex`. The two paper files, as fetched on 2026-10-05, have SHA-256:
- `paper/main.tex`: `81fb864c1463573adbfc2272c79287c2c71649e7a6e3024ca927bb221836038e`;
- `paper/supplementary.tex`: `8dfe9731af618937c6686da5d63b8e0decc220c591e1831060cd10d447461317`.

They are not part of the frozen data. The citations name the file and line at the pinned commit.

| Field | Status in every record | Passage (verbatim) |
|---|---|---|
| Test type | `assigned`: `tension` | `paper/main.tex` line 177 ("Alloy Synthesis and characterization", in the paragraph that opens "Overall, both campaigns used the same high level production route"): "Quasistatic tensile testing was used to determine 0.2\% offset YS, while Vickers indentation tests provided the HV." Also `paper/supplementary.tex` line 65: "quasistatic tensile and Vickers indentation measurements supplied YS and HV." |
| Phase class | `assigned`: `FCC` | `paper/main.tex` line 173: "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system." |
| Composition unit | `converted`, at.%, with a citation because the column headers state no unit | `paper/main.tex` line 399: "Al is not included in the 15\% statement because it spans only 0--4~at.\% and has a much wider interval." (The spreadsheet's Al column runs 0–4.) |
| Test temperature and its band | `not_reported`: "no per-record temperature; the source states no test temperature for its own measurements (owner decides; step 4 summary)" | none (below) |
| Microstructure | `not_reported`: "the source does not state the phases present per record" | The paper says "FCC alloy conditions", not "single-phase". |

**The temperature passages, for a domain expert** (owner's request: verbatim, with file and line):

- `paper/supplementary.tex` line 439, the caption of Supplementary Table S12:

  > \caption{Literature context for the fitted constant Hall--Petch slope, ordered by $k_{\mathrm{HP}}$. All values are room temperature and, except where noted, are fitted to tensile yield strength. Coefficients obtained by converting hardness to strength are excluded, because that conversion depends on the work-hardening response rather than on a fixed factor; this also excludes survey values for pure metals that pool indentation and tensile data in a single fit~\cite{Cordero2016}. Otto et al.\ report $k_{\mathrm{HP}}$ for CoCrFeMnNi falling from 538 at 77~K to 127 at 1073~K, so comparison across studies is meaningful only at matched test temperature. $^{\ddagger}$Fitted to compression data. The two Al$_{0.3}$ alloys remain single-phase FCC by selected-area diffraction; their large coefficients are attributed to coherency strain from nanometre-scale Ni--Al clusters rather than to precipitates~\cite{Jagetia2021}.}

- `paper/supplementary.tex` line 451, the row of that table for this dataset:

  > This work, Family~3 M3 & 766 & 14.7--212 & shared fitted slope \\

- **Main paper (`paper/main.tex`): no methods statement on test temperature.** Its only room-temperature mention is line 397, and it concerns literature values:

  > Reported room-temperature values for concentrated FCC alloys span 265 to 1244~MPa$\cdot\mu$m$^{1/2}$ with a median of 770~\cite{Yoshida2017,Otto2013,Yoshida2019acta,SchneiderCrFeNi2021,LiKHP2024,Jagetia2021}, so the fitted slope is close to the middle of the published set.

  Its other temperature mentions are recrystallization temperatures (lines 175, 188) and Otto et al.'s 77–1073 K (line 397).
- The caption states the temperature of a fitted slope listed in a comparison table, not the test conditions of the 94 records. The methods are deferred to "Ref. Mulukutla2026BRAVE" (the BB campaign) and to a future campaign publication (CB). Neither is in the repository.

**Consequence (open decision for step 6; it gates PRD 14.1a).** With the temperature not reported, a room-temperature scope rule makes all 94 Texas A&M records "scope not confirmed". The 21 eligible Texas A&M records, and with them the pooled reference result (98 records, k = 428 ± 64), depend on the owner's decision. The owner's step 6 requirement (the scope rule accepts the room-temperature band, with a test that the 21 records stay eligible under the reference plan) applies once the band is assigned on an accepted source. The same applies to the microstructure if the scope requires single-phase FCC.

## How each adapter assigns the paper (grouping) identity

- **MPEA and the controlled extract: the DOI** (`REFERENCE: doi`), as in the reference script (`pd.factorize(f.doi)`).
  - Group key `doi:<DOI as reported>`.
  - In the frozen MPEA file the DOI and `IDENTIFIER: Reference ID` are one-to-one (265 each, tested).
  - A blank DOI gives `group.key = None` with the reason "no DOI in the source: paper unknown". The Reference ID is never used in its place, and no group is invented. This applies to extract rows 5–6, where both are blank.
  - Extract rows 9–10 have a blank Reference ID and a constructed DOI, which is their group.
  - The DOI is kept exactly as reported. One MPEA DOI has a leading space (`" 10.1038/ncomms10602"`); removing it would not merge any groups (265 distinct either way), but it is not removed.
- **Texas A&M: the dataset**, one group `dataset:10.5281/zenodo.22798856` (grouping unit `dataset`).
  - `paper_reference` is the dataset citation; `paper_doi` is empty, because the record has no per-record paper (PRD 10).
  - The batch (`Iteration`: CBA 23, CBC 21, BBA 18, CBB 15, BBB 9, BBC 8) is kept as reported.
  - **The grouping unit is an open decision for the owner (PRD 17, decision 9).** The adapter refuses any other unit, so a version sealed with grouping unit `batch` fails until the owner decides and the adapter is changed.

## The common record format

One `CommonRecord` per data row, mirroring the `record` table: `source_key`, `version_fingerprint`, `source_item_key` (origin key), `item_index`, `kind`, `alloy`, `paper_reference`, `paper_doi`, `group`, `harmonized`, `reported`. **It has no field for eligibility, flags, duplicates or survivors** (tested).

- **`reported`:** every column, keyed by its header exactly as in the file. Each entry holds the cell text exactly as in the file (`""` when blank; for the spreadsheet, numbers in their shortest exact form) and the unit the header states.
- **`harmonized`:** the same 17 fields for every source, each with a fixed unit (`HARMONIZED_FIELDS`).
  - Each value has a status: `converted`, `not_reported` (blank, or "the source has no column for this field"), `not_convertible` (with the reason; the text stays in `reported`) or `assigned`.
  - `assigned` requires a `Citation` (document, location, exact quote), and a `Reported` entry cannot carry one. Both are enforced by the dataclasses and tested.
- **Origin keys:** `<file>:row:<n>`, n the 0-based data row, the same for both layouts.
  - MPEA's numbering is the one step 1 used.
  - The Texas A&M sheet is named `GS_MasterTable_Iterations ` (with a trailing space); it is matched verbatim and left out of the key.
- **Units:** MPEA's headers state µm, MPa, HV and °C; the Texas A&M headers state µm, MPa, HV, °C, h and % reduction. Values are converted unchanged.
- **Alloy naming:** the composition in atomic % is kept at full precision. The label follows the reference script: elements in alphabetical order, each rounded to 0.1 at.%. `CoCrFeMnNi` and `Co1 Cr1 Fe1 Mn1 Ni1` give the same alloy (tested).
- **What is never done:** no rescaling of percentages that do not sum to 100 (marked instead), no row dropped, no physical judgment (a negative grain size is converted as reported; flagging it is step 6's job).
  - An entirely blank row is listed in `blank_rows`, not made a record. The frozen files have none.
  - A row with the wrong number of fields is kept, with every harmonized value `not_convertible` and the reason.

## Requirements carried from step 3, and how they are met

| Requirement | How |
|---|---|
| Compute each source-version digest and identity exactly as the database does | `files_digest` and `version_identity` in `versions.py`. Tests compare them with `hc_files_digest` and `hc_version_identity` on a scratch database: four file sets, including bytewise sort cases (upper case before lower; `-` `.` `/` `_`), and all 36 combinations of the settings. Registration seals with the Python identity, so the database's own check is the cross-check, and it also compares the database's digest with the Python one. |
| Seal every version before use | `register` seals in the same transaction as the insert. `load_sealed_version` refuses an unsealed version, and re-checks each file's SHA-256 and the digest and identity against the stored seal. Every adapter calls `version.verify()` before parsing, so altered bytes or changed settings are refused before any record is made. |
| Every write path calls `hc_write_lock` first and retries on deadlock or serialization failure | The only write path in this step is registration. It writes no run or hypothesis version, so it locks the source row first instead (question 1), and it runs in `run_transaction`, which retries on `40P01` and `40001`. "Test connection" is read-only (`SET TRANSACTION READ ONLY`, tested). |
| Before any stored path is written to disk, check it stays inside its directory | Nothing in this step writes a stored file to disk: adapters read bytes from the database or memory. `safe_path_within` is in place for that later step. It is used now for every path registration *reads* from `data/`, and is tested with `a/../../outside.csv`, `../outside.csv`, absolute paths, the empty path and a symlink pointing out. Stored paths are also checked against the database's safe pattern before the database sees them. |

## Owner's addition: test temperature and test type in the MPEA reference records

Information for the owner's step 6 decision. No rule was changed. Computed test-side from the adapter output: the reference filter in `tests/test_reference_counts_from_adapters.py`, with the counting script kept in the scratchpad.

| Set | Temperature reported | Blank | Distinct values (count) | Test type |
|---|---|---|---|---|
| The 77 reference records | 77 | 0 | 25.0 °C (77) | `T` 76, `C` 1 |
| All 237 rows with a grain size | 223 | 14 | −196.0 (2), 20.0 (1), 24.0 (1), 25.0 (219) | `T` 161, `C` 60, blank 16 |

- **None of the 77 lacks a reported temperature.** So a strict rule (reported room temperature only) selects the same 77 records, and the MPEA-alone result under it is the reference result itself (427 ± 61, 20 papers). No separate computation was needed.
- The reference script's scope is `d['T'].between(20, 25)`, which is False for a blank temperature, so a blank-temperature row would have been excluded. In this data the case never arises: of the 92 MPEA rows with microstructure FCC, a grain size and a yield strength, none has a blank temperature.
- The one compression record among the 77 is `MPEA_dataset.csv:row:139` (`Co20Cr20Fe20Mn20Ni20`, doi 10.1016/j.jallcom.2014.12.157): the "permitted test types" item already open for step 6.

## Reference counts reproduced from the adapters' output

`tests/test_reference_counts_from_adapters.py` applies a **test-side** copy of the reference script's scope and rules. It is not package code and not an eligibility rule.

| | Records | Alloys | Groups |
|---|---|---|---|
| MPEA | 77 (the same row keys as the reference script run with pandas on the raw file) | — | 20 papers |
| Texas A&M (grain size and yield strength; temperature ignored, see above) | 21 | 9 | 1 |
| Pooled | 98 | 22 | 21 |

These match the reference numbers in CLAUDE.md (98 records, 22 alloys, 21 groups).

## Tests (445, all passing; 70 new; no existing test changed)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data tests/test_login.py tests/test_login_throttle.py tests/test_data_model.py tests/test_concurrency.py tests/test_migrations.py` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_write_retry.py` | 5 | Both SQLSTATEs rerun the whole transaction (the first attempt's insert is rolled back); other errors are not retried; it gives up after the last attempt; a real deadlock between two transactions is retried and both complete. |
| `tests/test_source_versions.py` | 20 | Digest and identity equal the database's. Unsafe stored paths are refused before the database. All three sources registered and sealed, with stored bytes equal to disk and settings copied; registering again adds nothing. A concurrent registration **waits on the source lock** and leaves one version (new source, and existing source with a new version). Two registrations at once leave one version. A changed file is refused and nothing is written; changed interpretation settings are refused. Paths stay inside their directory. Unsealed versions are refused. A loaded version reads exactly like the files on disk. Changed settings on a loaded version are refused. |
| `tests/test_adapter_mpea.py` | 16 | 1,545 records, one per row, origin keys in order. Every reported text equals the file's cell. Common fields and units. Numbers converted unchanged. 237 grain sizes. Nothing unconvertible in the frozen file. Test-type codes. No value assigned. Alloy names equal the reference naming. Paper identity is the DOI (265 groups, one-to-one with the Reference ID). The format has no decision fields. **Planted rows:** a non-numeric grain size, an unknown element, a blank formula, a negative grain size, a temperature with text, an unknown test type, a blank DOI, a blank line, an extra field, NaN, a zero amount; each record kept and marked. Another layout or encoding is refused, another grouping unit is refused, altered bytes are refused before parsing, and text is kept exactly as reported. |
| `tests/test_adapter_extract.py` | 5 | 16 records. Each equals its MPEA source row except where a listed column changed (the answer file is read on the test side only). A renamed formula gives the same alloy. Unknown paper is marked, never invented. A constructed DOI is its own paper. |
| `tests/test_adapter_tamu.py` | 13 | 94 records, every value as reported, BBA09's yield strength `not_reported` and the record kept. One group (the dataset), batches kept. Assigned values carry their passage. Assigned and reported stay distinguishable. Temperature not reported. Composition in at.% with 82 distinct compositions and 82 labels. Agrees with the authors' `inputs.csv`. **Planted rows:** a non-numeric percentage, a sum of 99, a blank yield strength, a formula cell, a blank row, an extra column, a negative grain size, a number stored as text. Another layout is refused; the `batch` grouping unit is refused until the owner decides. |
| `tests/test_reference_counts_from_adapters.py` | 4 | As in the table above. |
| `tests/test_source_connection.py` | 7 | Sample records in the common format for each source, with no row count changing in seven tables. Assigned values shown with their citation. A sealed version is needed. The transaction is read-only (a write slipped in is refused by PostgreSQL). The command line: register, register again, test, unknown source. |
| `tests/source_helpers.py` | — | Builds `SealedVersion` objects with a correct digest and identity for adapter tests that need no database. |

### The safeguard tests fail when the safeguard is removed

Each mechanism was removed in a scratch copy of the repository (not committed). The copy was then discarded.

| Removed | Result |
|---|---|
| The `FOR UPDATE` on the source row | At first the two concurrency tests **still passed**, because the source row was new and `INSERT … ON CONFLICT` already made the second transaction wait. I added `test_the_source_lock_serializes_a_new_version_of_an_existing_source` (the source row exists, the version does not). With the lock removed, that test fails; with it, all three pass. |
| `version.verify()` in both adapters | The two altered-version tests fail. |
| Retrying (`RETRYABLE_SQLSTATES` empty) | 4 of 5 retry tests fail; the "other errors are not retried" test passes, as it should. |
| Path containment in `safe_path_within` | The two path tests fail. |
| The sealed check in `load_sealed_version` alone | The unsealed test still passes, because `verify()` checks sealing again. With both checks removed, it fails. |
| The DOI stripped of spaces | 2 MPEA tests fail. |
| A Texas A&M temperature of 25 °C set as `converted` | `test_temperature_is_not_reported` fails. |

### Tests removed or replaced

None.

### Suite results

```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, `docker compose up -d db`)
445 passed in 61.76s
$ docker compose run --rm test           (the test image, rebuilt)
445 passed in 62.80s
$ python scripts/check_runtime_image.py <runtime image /app>
runtime image OK
```

GitHub Actions, commit `cb0f814` (last code change): success; "Run the suite in the test image": 445 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37256382423

The runtime image also imports the adapters and reads all three sources' files from `data/`.

## Deviations from the approved plan

1. **The Texas A&M origin key has no sheet name** (`<file>:row:<n>`, not `<file>:<sheet>:row:<n>`). The sheet name ends with a space, which would put a trailing space inside every key. The adapter reads only that sheet, matched verbatim.
2. **Phase class `FCC` is assigned** for Texas A&M, and the composition's at.% unit carries a citation. The plan named only test type and temperature. Both rest on explicit passages (quoted above), under the owner's rule for assigned values. The microstructure is left not reported, because the source does not say "single-phase".
3. **Text is kept exactly as reported** (the DOI with a leading space). The first draft stripped surrounding spaces; that would have been a silent change, so it was removed before commit.
4. **An extra concurrency test** (existing source, new version), added after the removal check showed that the first two did not depend on the source-row lock.
5. **Adapters refuse a grouping unit they do not support**, and list entirely blank rows instead of making records of them. The plan implied both without stating them.

## PRD corrections and clarifications for the next PRD update

1. **PRD 10 (grain-size transformation):** harmonization gives grain size in µm; the transformation the locked plan names is applied by code when the analysis dataset is built (owner, question 2).
2. **PRD 10 (Texas A&M):** "no temperature column (room-temperature tensile tests, per its paper)" overstates the source. The repository states tensile tests explicitly, but no test temperature for its own measurements (above). The temperature is not reported until the owner decides.
3. **PRD 10 (Texas A&M):** "82 single-phase FCC compositions": the source says "94 FCC alloy conditions", not single-phase.
4. **PRD 9.6 and 15 ("the CSV adapter"):** sprint 1 has one adapter per registered source. A generic uploaded-table adapter for any CSV registered through the form is not built; it belongs with the step 10 screens.
5. **PRD 4 (Curator) and tabular sources:** for tables, extraction is done by the adapter, which is code. How the Curator relates to tabular sources is a step 8 question.
6. **PRD 10 (alloy naming):** two compositions are the same alloy when their 0.1 at.% labels match (the reference script's rule); the full-precision composition is kept beside the label.
7. **Step 3 locking protocol:** `hc_write_lock` covers runs and hypothesis versions. Source registration locks the source row instead (owner, question 1).
8. **PRD 7 (`source`):** the controlled duplicate extract is registered as a source with `enabled = false`. No database rule prevents choosing a disabled source.

## Open items

1. **Registering on the live database (owner).** Not done in this step. When the owner agrees: `hypocurate sources register` in the Render Shell of one service. No `render.yaml` change is needed, and no setting depends on it.
2. **Texas A&M test temperature (owner; gates PRD 14.1a in step 6).** See "Consequence" above. If the band is assigned on an accepted source, step 6's scope rule must accept the room-temperature band, with a test that the 21 Texas A&M records stay eligible under the reference plan. The same question applies to the microstructure if the scope requires single-phase FCC.
3. **Texas A&M grouping unit (owner, PRD 17 decision 9).** One group now; the batch is kept as reported. A `batch` version is refused by the adapter until decided.
4. **Step 5 (access layer):** adapters read source bytes from the sealed version in the database, not from disk. The approved input list should name the sealed source versions, and `tests/` and `docs/reviews/` stay outside it, as before.
5. **Step 6:**
   - a guard so that the controlled extract (constructed data) cannot enter a real analysis;
   - permitted test types (MPEA row 139, compression, is among the 77);
   - duplicate matching uses `alloy` (the 0.1 at.% label) together with paper, grain size, value and test conditions.
6. **Step 6/8:** store the records (the format mirrors the `record` table), from inside an extraction run after the rules lock, through `hc_write_lock(p_run => …)` and `run_transaction`.
7. **Carried from step 3, unchanged:** step 7 and step 9 requirements; the lock-contention note; a transaction writing to more than one run needs an ordering rule.

## Questions for the reviewer

1. Is locking the source row an adequate substitute for `hc_write_lock` on the registration path, given that the database also locks the version row on file insert and at sealing?
2. Is the status vocabulary (`converted`, `not_reported`, `not_convertible`, `assigned` with citation) enough to keep assigned values distinguishable from reported ones once records are stored as JSON in step 6?
3. Is anything in the adapters a decision rather than a conversion (for example the 0.1 at.% alloy label, or listing blank rows instead of making records)?
````

## 2. Reviewer checklist

### `docs/reviews/checklist.md`

```markdown
# Second-model review checklist

**Status: approved by the owner as a working draft, 2026-10-04.** Drafted from PRD Section 13.2 and the rules in `CLAUDE.md`. This is the fixed checklist given to the reviewer at every review. It may be amended after its first use in step 2; any amendment needs the owner's approval.

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
- [ ] Pipeline code reads input files only from an explicit list of approved files. Are `tests/` and `docs/reviews/`, which hold expected answers, outside that list? Directory placement alone is a convention, not enforcement.
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
  1. the record that comes directly from the original paper (detected by its DOI);
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
```

## 3. Application code: write retry and source versions

### `hypocurate/db/retry.py`

```python
"""Retry a whole transaction on deadlock or serialization failure (step 3, open item 3).

Every write path from step 4 on runs inside `run_transaction`. The function `fn`
receives a connection inside a fresh transaction and does all its work there: its
first statement takes the locks the protocol asks for (`hc_write_lock` for runs and
hypothesis versions; the source row for source registration). If PostgreSQL aborts
the transaction with SQLSTATE 40P01 (deadlock) or 40001 (serialization failure),
everything it wrote is rolled back, so `fn` is simply run again from the start.
Any other error is raised unchanged.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from sqlalchemy import Connection, Engine
from sqlalchemy.exc import DBAPIError

T = TypeVar("T")

RETRYABLE_SQLSTATES = frozenset({"40P01", "40001"})


def sqlstate(error: BaseException) -> str | None:
    """The SQLSTATE of a database error, or None."""
    orig = getattr(error, "orig", None)
    return getattr(orig, "sqlstate", None)


def run_transaction(engine: Engine, fn: Callable[[Connection], T], attempts: int = 5,
                    backoff: float = 0.05) -> T:
    """Runs `fn(conn)` in one transaction and commits; retries the whole transaction
    on 40P01 / 40001, at most `attempts` times in all."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            with engine.begin() as conn:
                return fn(conn)
        except DBAPIError as error:
            if sqlstate(error) not in RETRYABLE_SQLSTATES or attempt == attempts:
                raise
            time.sleep(backoff * attempt)
    raise AssertionError("unreachable")
```

### `hypocurate/sources/versions.py`

```python
"""Registered sources and their sealed versions (PRD Sections 7 and 10; step 4).

Three sources are registered from the frozen files of step 1: the MPEA dataset, the
Texas A&M FCC dataset and the controlled duplicate extract. Each becomes a
`source_version` holding the data files its adapter reads, sealed once (step 3).

The digest and identity are computed here exactly as the database computes them
(`hc_files_digest`, `hc_version_identity` in migration 0001), and the database checks
them again at sealing.

Locking (owner, 2026-10-05, step 4 question 1): `hc_write_lock` covers runs and
hypothesis versions only, and source registration writes neither. Registration
therefore locks the source row first (`SELECT … FOR UPDATE`, after an
`INSERT … ON CONFLICT DO NOTHING` for a new source), then writes the version, its files
and the seal in the same transaction, retried on 40P01 / 40001 (`run_transaction`).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.db.retry import run_transaction
from hypocurate.sources.manifest import REPO_ROOT, load_manifest

DATA_DIR = REPO_ROOT / "data"
MAX_FILE_BYTES = 5 * 1024 * 1024  # the source_file CHECK (owner decision, 2026-10-04)
# The source_file path CHECK, in Python, so an unsafe path is refused before the database sees it.
SAFE_STORED_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)")


class RegistrationError(Exception):
    """A source cannot be registered as defined (changed file, changed settings, unsafe path)."""


class UnsealedVersion(Exception):
    """A source version that is not sealed, or whose stored bytes do not match its seal."""


# --- Digest and identity (the database's definitions, step 3 item 10) ---------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_digest(files: Mapping[str, bytes]) -> str:
    """SHA-256 of one line "<sha256>  <path>\\n" per file, sorted by path bytewise
    (the database sorts with COLLATE "C"). The same as `hc_files_digest`."""
    for path in files:
        if not SAFE_STORED_PATH.fullmatch(path):
            raise RegistrationError(f"unsafe stored path {path!r}")
    listing = "".join(f"{sha256_hex(files[p])}  {p}\n" for p in sorted(files, key=lambda p: p.encode()))
    return sha256_hex(listing.encode("utf-8"))


def version_identity(digest: str, source_type: str, data_kind: str, grouping_unit: str) -> str:
    """SHA-256 of four lines, each "<name> <value>\\n". The same as `hc_version_identity`."""
    return sha256_hex((f"files {digest}\nsource_type {source_type}\n"
                       f"data_kind {data_kind}\ngrouping_unit {grouping_unit}\n").encode("utf-8"))


# --- Paths --------------------------------------------------------------------------

def safe_path_within(directory: Path, relative: str) -> Path:
    """The path `relative` inside `directory`, after resolving `..` and symbolic links.
    Raises RegistrationError if it is absolute, empty, or leaves the directory.
    Every path read from the manifest goes through this, and so must any stored path
    before it is written to disk (step 3, open item 4)."""
    if not relative or Path(relative).is_absolute() or relative.startswith(("/", "\\")):
        raise RegistrationError(f"path {relative!r} must be relative")
    base = directory.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base):
        raise RegistrationError(f"path {relative!r} leaves {directory}")
    return target


# --- The three sources --------------------------------------------------------------

@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    source_type: str
    data_kind: str
    grouping_unit: str
    licence: str
    address: str | None
    properties_covered: tuple[str, ...]
    enabled: bool
    directory: str  # relative to data/
    data_files: tuple[str, ...]  # file names inside `directory`, as stored
    version_label: str
    manifest_section: tuple[str, ...]  # where its files are listed in data/manifest.json


SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
    "mpea": SourceDefinition(
        key="mpea", name="MPEA dataset (Borg et al. 2020)", source_type="uploaded_table",
        data_kind="measured", grouping_unit="paper", licence="Apache-2.0",
        address="https://github.com/CitrineInformatics/MPEA_dataset",
        properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
        enabled=True, directory="sources/mpea", data_files=("MPEA_dataset.csv",),
        version_label="commit d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e",
        manifest_section=("sources", "mpea")),
    "tamu_fcc": SourceDefinition(
        key="tamu_fcc", name="Texas A&M FCC dataset (Mulukutla et al. 2026)", source_type="uploaded_table",
        data_kind="measured",
        # PRD 17, open decision 9: one group in sprint 1; batches later if the owner agrees.
        grouping_unit="dataset", licence="MIT",
        address="https://doi.org/10.5281/zenodo.22798856",
        properties_covered=("yield_strength", "hardness", "grain_size"),
        enabled=True, directory="sources/tamu_fcc",
        # The spreadsheet is the source of record (step 1); only files the adapter reads are stored.
        data_files=("Grain_Size_Summary_v3.xlsx",),
        version_label="v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f",
        manifest_section=("sources", "tamu_fcc")),
    "controlled_duplicates": SourceDefinition(
        key="controlled_duplicates",
        name="Controlled duplicate extract (constructed test data; never pooled into a real analysis)",
        source_type="uploaded_table", data_kind="measured", grouping_unit="paper",
        licence="Apache-2.0 (derived from the MPEA dataset)", address=None,
        properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
        # Off by default: constructed data. A real guard against choosing it is step 6's.
        enabled=False, directory="controlled_duplicates", data_files=("extract.csv",),
        version_label="built 2026-10-04 from the MPEA dataset",
        manifest_section=("controlled_duplicates",)),
})


def _manifest_files(definition: SourceDefinition, manifest: dict) -> tuple[dict, str]:
    section = manifest
    for part in definition.manifest_section:
        section = section[part]
    obtained = section.get("retrieved") or section.get("built")
    return {f["path"]: f for f in section["files"]}, obtained


def read_definition_files(definition: SourceDefinition, data_dir: Path = DATA_DIR,
                          manifest: dict | None = None) -> tuple[dict[str, bytes], date]:
    """Reads a source's data files from disk, checks each against its manifest entry
    (SHA-256 and size) and returns {stored path: bytes} and the date obtained."""
    manifest = manifest if manifest is not None else load_manifest(data_dir / "manifest.json")
    listed, obtained = _manifest_files(definition, manifest)
    source_dir = safe_path_within(data_dir, definition.directory)
    files: dict[str, bytes] = {}
    for name in definition.data_files:
        if not SAFE_STORED_PATH.fullmatch(name):
            raise RegistrationError(f"unsafe stored path {name!r}")
        path = safe_path_within(source_dir, name)
        manifest_path = f"data/{definition.directory}/{name}"
        entry = listed.get(manifest_path)
        if entry is None:
            raise RegistrationError(f"{manifest_path} is not in the manifest")
        content = path.read_bytes()
        if len(content) != entry["bytes"] or sha256_hex(content) != entry["sha256"]:
            raise RegistrationError(f"{manifest_path} does not match its manifest fingerprint")
        if len(content) > MAX_FILE_BYTES:
            raise RegistrationError(f"{manifest_path} is larger than 5 MiB")
        files[name] = content
    return files, date.fromisoformat(obtained)


# --- Registration -------------------------------------------------------------------

@dataclass(frozen=True)
class Registered:
    key: str
    source_id: int
    version_id: int
    label: str
    files_digest: str
    fingerprint: str
    created: bool  # False: an identical sealed version already existed


INTERPRETATION = ("source_type", "data_kind", "grouping_unit")


def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes], obtained: date) -> Registered:
    digest = files_digest(files)
    identity = version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)
    conn.execute(text(
        "INSERT INTO source (key, name, source_type, address, licence, data_kind, adapter_status, enabled, "
        "grouping_unit, properties_covered) VALUES (:key, :name, :type, :address, :licence, :kind, "
        "'available', :enabled, :unit, :props) ON CONFLICT (key) DO NOTHING"),
        dict(key=d.key, name=d.name, type=d.source_type, address=d.address, licence=d.licence,
             kind=d.data_kind, enabled=d.enabled, unit=d.grouping_unit, props=list(d.properties_covered)))
    # The lock: every registration of this source waits here until the other commits.
    row = conn.execute(text(
        "SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = :key FOR UPDATE"),
        dict(key=d.key)).one()
    stored = dict(zip(INTERPRETATION, row[1:]))
    expected = {k: getattr(d, k) for k in INTERPRETATION}
    if stored != expected:
        raise RegistrationError(
            f"source {d.key!r} is registered with {stored}, but the code defines {expected}; "
            "a change of interpretation settings is not made silently")
    source_id = row[0]
    existing = conn.execute(text(
        "SELECT id, label, files_digest FROM source_version "
        "WHERE source_id = :s AND fingerprint = :fp AND sealed_at IS NOT NULL"),
        dict(s=source_id, fp=identity)).one_or_none()
    if existing is not None:
        return Registered(d.key, source_id, existing[0], existing[1], existing[2], identity, created=False)
    version_id = conn.execute(text(
        "INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, :l, :o) RETURNING id"),
        dict(s=source_id, l=d.version_label, o=obtained)).scalar_one()
    for path in sorted(files):
        conn.execute(text(
            "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)"),
            dict(v=version_id, p=path, h=sha256_hex(files[path]), c=files[path]))
    sealed = conn.execute(text(
        "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v "
        "RETURNING files_digest, fingerprint"), dict(v=version_id, fp=identity)).one()
    if sealed[0] != digest or sealed[1] != identity:
        raise RegistrationError("the database's files digest differs from the one computed here")
    return Registered(d.key, source_id, version_id, d.version_label, digest, identity, created=True)


def register(engine: Engine, key: str, data_dir: Path = DATA_DIR, manifest: dict | None = None) -> Registered:
    """Registers source `key` and seals its version, or returns the identical sealed
    version if it is already registered. One transaction, retried on 40P01 / 40001."""
    if key not in SOURCES:
        raise RegistrationError(f"unknown source {key!r}; known: {', '.join(SOURCES)}")
    d = SOURCES[key]
    files, obtained = read_definition_files(d, data_dir, manifest)
    return run_transaction(engine, lambda conn: _register_in(conn, d, files, obtained))


# --- Loading a sealed version for an adapter ----------------------------------------

@dataclass(frozen=True)
class SealedVersion:
    """A sealed source version with its file bytes, as an adapter receives it."""
    id: int
    source_key: str
    label: str
    source_type: str
    data_kind: str
    grouping_unit: str
    sealed_at: datetime | None
    files_digest: str
    fingerprint: str
    files: Mapping[str, bytes]

    def __post_init__(self):
        object.__setattr__(self, "files", MappingProxyType(dict(self.files)))

    def verify(self) -> None:
        """Raises UnsealedVersion unless the version is sealed and its bytes give exactly
        its stored files digest and identity. Every adapter calls this before parsing."""
        if self.sealed_at is None:
            raise UnsealedVersion(f"source version {self.id} is not sealed")
        if files_digest(self.files) != self.files_digest:
            raise UnsealedVersion(f"source version {self.id}: files do not match the sealed files digest")
        if version_identity(self.files_digest, self.source_type, self.data_kind,
                            self.grouping_unit) != self.fingerprint:
            raise UnsealedVersion(f"source version {self.id}: settings do not match the sealed identity")


def load_sealed_version(conn: Connection, version_id: int) -> SealedVersion:
    """Loads a version and its files. Refuses an unsealed version, and checks each file's
    bytes against its stored SHA-256 and the whole against the seal."""
    row = conn.execute(text(
        "SELECT sv.id, s.key, sv.label, sv.source_type, sv.data_kind, sv.grouping_unit, sv.sealed_at, "
        "sv.files_digest, sv.fingerprint FROM source_version sv JOIN source s ON s.id = sv.source_id "
        "WHERE sv.id = :v"), dict(v=version_id)).one_or_none()
    if row is None:
        raise UnsealedVersion(f"no source version {version_id}")
    if row.sealed_at is None:
        raise UnsealedVersion(f"source version {version_id} is not sealed")
    files = {}
    for path, sha, content in conn.execute(text(
            "SELECT path, sha256, content FROM source_file WHERE source_version_id = :v"), dict(v=version_id)):
        content = bytes(content)
        if sha256_hex(content) != sha:
            raise UnsealedVersion(f"source version {version_id}: {path} does not match its SHA-256")
        files[path] = content
    version = SealedVersion(row.id, row.key, row.label, row.source_type, row.data_kind, row.grouping_unit,
                            row.sealed_at, row.files_digest, row.fingerprint, files)
    version.verify()
    return version


def latest_sealed_version_id(conn: Connection, key: str) -> int:
    """The most recently sealed version of source `key`."""
    vid = conn.execute(text(
        "SELECT sv.id FROM source_version sv JOIN source s ON s.id = sv.source_id "
        "WHERE s.key = :k AND sv.sealed_at IS NOT NULL ORDER BY sv.sealed_at DESC, sv.id DESC LIMIT 1"),
        dict(k=key)).scalar_one_or_none()
    if vid is None:
        raise UnsealedVersion(f"source {key!r} has no sealed version")
    return vid
```

## 4. Application code: record format, normalizers and adapters

### `hypocurate/sources/record.py`

```python
"""The common record format every source adapter returns (PRD Section 10; step 4).

One `CommonRecord` per observation, mirroring the `record` table (step 3) so that a
later step can store it unchanged: its origin (`source_item_key`, `item_index`), the
kind of data, the alloy, the paper and its grouping identity, the harmonized values
and the values as reported.

An adapter converts and reports. The format therefore has no field for eligibility,
flags, duplicates or survivors: those are decided by code under the locked plan
(steps 6 and 7). Every harmonized value carries its status:

- `converted`: read from the source and converted (possibly unchanged) to the unit shown;
- `not_reported`: blank in the source, or the source has no such column (the reason says which);
- `not_convertible`: present in the source but could not be converted; the reason says why,
  and the text as reported is kept in `reported`;
- `assigned`: not in the data file, set by the adapter from the source's own documentation.
  It always carries a `Citation` (file, location and the exact passage), so an assigned
  value can never be mistaken for a reported one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

STATUSES = ("converted", "not_reported", "not_convertible", "assigned")

# The harmonized fields, the same for every adapter, with their units (None: no unit).
# A source without a column for a field reports it as `not_reported`.
HARMONIZED_FIELDS: Mapping[str, str | None] = MappingProxyType({
    "composition": "at.%",
    "grain_size": "µm",
    "grain_size_sd": "µm",
    "yield_strength": "MPa",
    "yield_strength_sd": "MPa",
    "ultimate_tensile_strength": "MPa",
    "hardness": "HV",
    "hardness_sd": "HV",
    "test_type": None,
    "test_temperature": "°C",
    "test_temperature_band": None,
    "phase_class": None,
    "microstructure": None,
    "processing_method": None,
    "cold_work": "% reduction",
    "recrystallization_temperature": "°C",
    "holding_time": "h",
})

TEST_TYPES = ("tension", "compression")


@dataclass(frozen=True)
class Citation:
    """Where an assigned value (or a unit not stated in the data file) comes from."""
    document: str  # e.g. "ArroyaveLab/2026-mulukutla-hall-petch@11390ee paper/main.tex"
    location: str  # e.g. "line 177"
    quote: str  # the exact passage

    def __post_init__(self):
        for name in ("document", "location", "quote"):
            if not getattr(self, name).strip():
                raise ValueError(f"a citation needs a {name}")

    def to_json(self) -> dict:
        return {"document": self.document, "location": self.location, "quote": self.quote}


@dataclass(frozen=True)
class Value:
    """One harmonized value with its unit and status."""
    value: Any
    unit: str | None
    status: str
    reason: str | None = None
    citation: Citation | None = None

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}")
        if self.status in ("converted", "assigned") and self.value is None:
            raise ValueError(f"a {self.status} value needs a value")
        if self.status in ("not_reported", "not_convertible"):
            if self.value is not None:
                raise ValueError(f"a {self.status} value has no value")
            if not self.reason:
                raise ValueError(f"a {self.status} value needs a reason")
        if self.status == "assigned" and self.citation is None:
            raise ValueError("an assigned value needs a citation")
        if self.citation is not None and self.status not in ("assigned", "converted"):
            raise ValueError("only an assigned value, or a converted value whose unit is documented "
                             "outside the data file, carries a citation")
        if isinstance(self.value, dict):
            object.__setattr__(self, "value", MappingProxyType(dict(self.value)))

    def to_json(self) -> dict:
        out = {"value": dict(self.value) if isinstance(self.value, Mapping) else self.value,
               "unit": self.unit, "status": self.status}
        if self.reason is not None:
            out["reason"] = self.reason
        if self.citation is not None:
            out["citation"] = self.citation.to_json()
        return out


@dataclass(frozen=True)
class Reported:
    """A value exactly as the source gives it: the column header and the cell text."""
    column: str
    text: str  # "" for a blank cell
    unit: str | None  # the unit the source states for this column, or None

    def to_json(self) -> dict:
        return {"column": self.column, "text": self.text, "unit": self.unit}


@dataclass(frozen=True)
class Group:
    """The grouping (independence) identity used for cluster-robust errors (PRD 5.7)."""
    unit: str  # the version's grouping unit: "paper" or "dataset"
    key: str | None
    reason: str | None = None  # why there is no key

    def __post_init__(self):
        if (self.key is None) == (self.reason is None):
            raise ValueError("a group has either a key or the reason it has none")

    def to_json(self) -> dict:
        return {"unit": self.unit, "key": self.key, "reason": self.reason}


@dataclass(frozen=True)
class CommonRecord:
    source_key: str
    version_fingerprint: str
    source_item_key: str  # stable origin key within the source version
    item_index: int
    kind: str  # the version's kind of data
    alloy: str | None  # canonical label from the composition; None if not convertible
    paper_reference: str | None
    paper_doi: str | None
    group: Group
    harmonized: Mapping[str, Value] = field(default_factory=dict)
    reported: Mapping[str, Reported] = field(default_factory=dict)

    def __post_init__(self):
        if not self.source_item_key:
            raise ValueError("a record needs its origin key")
        if set(self.harmonized) != set(HARMONIZED_FIELDS):
            raise ValueError(f"harmonized fields differ from the common set: "
                             f"{sorted(set(self.harmonized) ^ set(HARMONIZED_FIELDS))}")
        for name, v in self.harmonized.items():
            if v.unit != HARMONIZED_FIELDS[name]:
                raise ValueError(f"{name}: unit {v.unit!r}, expected {HARMONIZED_FIELDS[name]!r}")
        object.__setattr__(self, "harmonized", MappingProxyType(dict(self.harmonized)))
        object.__setattr__(self, "reported", MappingProxyType(dict(self.reported)))

    def to_json(self) -> dict:
        return {
            "source_key": self.source_key,
            "version_fingerprint": self.version_fingerprint,
            "source_item_key": self.source_item_key,
            "item_index": self.item_index,
            "kind": self.kind,
            "alloy": self.alloy,
            "paper_reference": self.paper_reference,
            "paper_doi": self.paper_doi,
            "group": self.group.to_json(),
            "harmonized": {k: v.to_json() for k, v in self.harmonized.items()},
            "reported": {k: r.to_json() for k, r in self.reported.items()},
        }


@dataclass(frozen=True)
class AdapterResult:
    """What an adapter read: one record per data row, in file order, and the data rows
    that were entirely blank (listed, never silently skipped)."""
    records: tuple[CommonRecord, ...]
    blank_rows: tuple[int, ...] = ()


class AdapterError(Exception):
    """The file as a whole cannot be read by this adapter (wrong layout, wrong encoding,
    an unsealed or altered version). Raised before any record is returned."""
```

### `hypocurate/sources/normalize.py`

```python
"""Unit and alloy-name normalizers shared by the adapters (PRD Sections 6.1 and 10).

Each function converts and reports. It never rescales, rounds away or corrects a value
silently: anything it cannot convert comes back as a `not_convertible` (or
`not_reported`) `Value` with the reason, and the adapter keeps the text as reported.
Physical plausibility (for example a negative grain size) is not judged here: that is
the job of the code checks under the locked plan (step 6).
"""
from __future__ import annotations

import math
import re

from hypocurate.sources.record import Value

# The 118 element symbols, to catch a formula that parses but names no element.
ELEMENTS = frozenset("""
H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge
As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm
Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U
Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og
""".split())

_FORMULA = re.compile(r"(?:\s*[A-Z][a-z]?\s*(?:\d+(?:\.\d*)?|\.\d+)?)+\s*")
_TERM = re.compile(r"([A-Z][a-z]?)\s*(\d+(?:\.\d*)?|\.\d+)?")

# Sum of percentage columns accepted as 100 (floating-point representation only).
PERCENT_SUM_TOLERANCE = 1e-6


def number(text: str, unit: str | None, blank_reason: str = "blank in the source") -> Value:
    """A number as reported, in the unit the source states. Blank → not reported;
    anything that is not a finite decimal number → not convertible, with the reason."""
    t = text.strip()
    if t == "":
        return Value(None, unit, "not_reported", blank_reason)
    try:
        x = float(t)
    except ValueError:
        return Value(None, unit, "not_convertible", f"not a number: {text!r}")
    if not math.isfinite(x):
        return Value(None, unit, "not_convertible", f"not a finite number: {text!r}")
    return Value(x, unit, "converted")


def formula_to_atomic_percent(formula: str) -> tuple[dict[str, float] | None, str | None]:
    """A formula string ("Al0.25 Co1 Fe1 Ni1", "CoCrFeMnNi") → atomic percent per element,
    full precision. A missing amount means 1. Returns (composition, None) or (None, reason)."""
    if formula.strip() == "":
        return None, "blank in the source"
    if not _FORMULA.fullmatch(formula):
        return None, f"formula does not parse: {formula!r}"
    amounts: dict[str, float] = {}
    for symbol, amount in _TERM.findall(formula):
        if symbol not in ELEMENTS:
            return None, f"unknown element symbol {symbol!r} in {formula!r}"
        a = float(amount) if amount else 1.0
        if a <= 0:
            return None, f"amount {amount!r} of {symbol} is not positive in {formula!r}"
        amounts[symbol] = amounts.get(symbol, 0.0) + a
    total = sum(amounts.values())
    return {e: 100.0 * a / total for e, a in amounts.items()}, None


def percent_columns_to_atomic_percent(columns: dict[str, float | None]
                                      ) -> tuple[dict[str, float] | None, str | None]:
    """Columns of atomic percentages, one per element → atomic percent per element.
    Elements at 0 are absent from the alloy. A blank column, a negative value or a sum
    other than 100 is reported, never rescaled."""
    for symbol in columns:
        if symbol not in ELEMENTS:
            return None, f"unknown element symbol {symbol!r}"
    blank = [e for e, v in columns.items() if v is None]
    if blank:
        return None, f"blank percentage for {', '.join(blank)}"
    negative = [e for e, v in columns.items() if v < 0]
    if negative:
        return None, f"negative percentage for {', '.join(negative)}"
    total = sum(columns.values())
    if abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
        return None, f"percentages sum to {total:g}, not 100"
    return {e: float(v) for e, v in columns.items() if v > 0}, None


def alloy_label(composition: dict[str, float]) -> str:
    """The canonical alloy name: elements in alphabetical order, each with its atomic
    percent rounded to 0.1 (the reference script's naming, `docs/reference/worked_example.py`).
    The full-precision composition is kept beside it in the record."""
    return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))
```

### `hypocurate/sources/adapters/__init__.py`

```python
"""One adapter per registered source (PRD 6.1, 10). Each takes a sealed source version
and returns its records in the common record format (`hypocurate.sources.record`).
An adapter converts and reports: it never decides eligibility, never drops a record and
never corrects a value silently."""
from __future__ import annotations

from typing import Callable, Mapping
from types import MappingProxyType

from hypocurate.sources.adapters import mpea_layout, tamu_fcc
from hypocurate.sources.record import AdapterError, AdapterResult
from hypocurate.sources.versions import SealedVersion

ADAPTERS: Mapping[str, Callable[[SealedVersion], AdapterResult]] = MappingProxyType({
    "mpea": mpea_layout.read,
    "controlled_duplicates": mpea_layout.read,
    "tamu_fcc": tamu_fcc.read,
})


def read(version: SealedVersion) -> AdapterResult:
    """Reads a sealed version with its source's adapter."""
    adapter = ADAPTERS.get(version.source_key)
    if adapter is None:
        raise AdapterError(f"no adapter for source {version.source_key!r}")
    return adapter(version)
```

### `hypocurate/sources/adapters/mpea_layout.py`

```python
"""Adapter for the MPEA column layout (Borg et al. 2020): the MPEA dataset itself and the
controlled duplicate extract, which copies its header verbatim (step 1).

- One record per data row, in file order; no row is dropped. An entirely blank line is
  listed in `blank_rows`, not turned into a record.
- Origin key: `<file>:row:<n>`, n the 0-based data row (the row numbering used in
  step 1). One record per row, so `item_index` is 0.
- Every column is kept as reported text, with the unit its header states.
- **Paper identity (grouping): the DOI** (`REFERENCE: doi`), as in the reference script.
  In the frozen MPEA file it is one-to-one with `IDENTIFIER: Reference ID`. A blank DOI
  gives a record whose group is unknown, with the reason; the Reference ID is never used
  in its place, and no group is invented.
- Units are those of the headers (µm, MPa, HV, °C); values are converted unchanged.
- Text values (DOI, title, categories) are kept exactly as reported, surrounding spaces
  included; only a whitespace-only cell counts as blank.
"""
from __future__ import annotations

import csv
import io

from hypocurate.sources import normalize as n
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, CommonRecord,
                                       Group, Reported, Value)
from hypocurate.sources.versions import SealedVersion

HEADER = (
    "IDENTIFIER: Reference ID", "FORMULA", "PROPERTY: Microstructure", "PROPERTY: Processing method",
    "PROPERTY: BCC/FCC/other", "PROPERTY: grain size ($\\mu$m)", "PROPERTY: Exp. Density (g/cm$^3$)",
    "PROPERTY: Calculated Density (g/cm$^3$)", "PROPERTY: HV", "PROPERTY: Type of test",
    "PROPERTY: Test temperature ($^\\circ$C)", "PROPERTY: YS (MPa)", "PROPERTY: UTS (MPa)",
    "PROPERTY: Elongation (%)", "PROPERTY: Elongation plastic (%)", "PROPERTY: Exp. Young modulus (GPa)",
    "PROPERTY: Calculated Young modulus (GPa)", "PROPERTY: O content (wppm)", "PROPERTY: N content (wppm)",
    "PROPERTY: C content (wppm)", "REFERENCE: doi", "REFERENCE: year", "REFERENCE: title",
)

# The unit each column's header states (None: none stated, or text).
UNITS = {
    "PROPERTY: grain size ($\\mu$m)": "µm", "PROPERTY: Exp. Density (g/cm$^3$)": "g/cm³",
    "PROPERTY: Calculated Density (g/cm$^3$)": "g/cm³", "PROPERTY: HV": "HV",
    "PROPERTY: Test temperature ($^\\circ$C)": "°C", "PROPERTY: YS (MPa)": "MPa", "PROPERTY: UTS (MPa)": "MPa",
    "PROPERTY: Elongation (%)": "%", "PROPERTY: Elongation plastic (%)": "%",
    "PROPERTY: Exp. Young modulus (GPa)": "GPa", "PROPERTY: Calculated Young modulus (GPa)": "GPa",
    "PROPERTY: O content (wppm)": "wppm", "PROPERTY: N content (wppm)": "wppm",
    "PROPERTY: C content (wppm)": "wppm",
}

TEST_TYPE_CODES = {"T": "tension", "C": "compression"}

NO_COLUMN = "the source has no column for this field"


def _text(value: str) -> Value:
    """A categorical value, kept verbatim."""
    if value.strip() == "":
        return Value(None, None, "not_reported", "blank in the source")
    return Value(value, None, "converted")


def _harmonize(cells: dict[str, str]) -> tuple[dict[str, Value], str | None]:
    h: dict[str, Value] = {}
    composition, reason = n.formula_to_atomic_percent(cells["FORMULA"])
    if composition is None:
        status = "not_reported" if cells["FORMULA"].strip() == "" else "not_convertible"
        h["composition"] = Value(None, "at.%", status, reason)
        alloy = None
    else:
        h["composition"] = Value(composition, "at.%", "converted")
        alloy = n.alloy_label(composition)
    h["grain_size"] = n.number(cells["PROPERTY: grain size ($\\mu$m)"], "µm")
    h["yield_strength"] = n.number(cells["PROPERTY: YS (MPa)"], "MPa")
    h["ultimate_tensile_strength"] = n.number(cells["PROPERTY: UTS (MPa)"], "MPa")
    h["hardness"] = n.number(cells["PROPERTY: HV"], "HV")
    h["test_temperature"] = n.number(cells["PROPERTY: Test temperature ($^\\circ$C)"], "°C")
    h["test_temperature_band"] = Value(None, None, "not_reported",
                                       "the source reports a temperature in °C, not a band")
    code = cells["PROPERTY: Type of test"]
    if code.strip() == "":
        h["test_type"] = Value(None, None, "not_reported", "blank in the source")
    elif code.strip() in TEST_TYPE_CODES:
        h["test_type"] = Value(TEST_TYPE_CODES[code.strip()], None, "converted")
    else:
        h["test_type"] = Value(None, None, "not_convertible", f"unknown test type code {code!r}")
    h["phase_class"] = _text(cells["PROPERTY: BCC/FCC/other"])
    h["microstructure"] = _text(cells["PROPERTY: Microstructure"])
    h["processing_method"] = _text(cells["PROPERTY: Processing method"])
    for name in ("grain_size_sd", "yield_strength_sd", "hardness_sd", "cold_work",
                 "recrystallization_temperature", "holding_time"):
        h[name] = Value(None, HARMONIZED_FIELDS[name], "not_reported", NO_COLUMN)
    return h, alloy


def read(version: SealedVersion) -> AdapterResult:
    version.verify()
    if version.grouping_unit != "paper":
        raise AdapterError(f"the MPEA-layout adapter groups by paper; version {version.id} "
                           f"has grouping unit {version.grouping_unit!r}")
    if len(version.files) != 1:
        raise AdapterError(f"expected one CSV file, found {sorted(version.files)}")
    (path, content), = version.files.items()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AdapterError(f"{path} is not UTF-8: {error}") from None
    rows = csv.reader(io.StringIO(decoded, newline=""))
    header = tuple(next(rows, ()))
    if header != HEADER:
        raise AdapterError(f"{path}: the header is not the MPEA layout")
    records, blank = [], []
    for i, fields in enumerate(rows):
        if not fields or all(f.strip() == "" for f in fields):
            blank.append(i)
            continue
        records.append(_record(version, path, i, fields))
    return AdapterResult(tuple(records), tuple(blank))


def _record(version: SealedVersion, path: str, i: int, fields: list[str]) -> CommonRecord:
    key = f"{path}:row:{i}"
    reported = {}
    for name, value in zip(HEADER, fields):
        reported[name] = Reported(name, value, UNITS.get(name))
    for extra, value in enumerate(fields[len(HEADER):], start=len(HEADER) + 1):
        reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", value, None)
    if len(fields) != len(HEADER):
        reason = f"the row has {len(fields)} fields, the header {len(HEADER)}"
        harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
        return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None, None, None,
                            Group("paper", None, reason), harmonized, reported)
    cells = dict(zip(HEADER, fields))
    harmonized, alloy = _harmonize(cells)
    # Kept exactly as reported (one MPEA DOI has a leading space); only a whitespace-only
    # cell counts as blank.
    doi = cells["REFERENCE: doi"] if cells["REFERENCE: doi"].strip() else None
    title = cells["REFERENCE: title"] if cells["REFERENCE: title"].strip() else None
    group = Group("paper", f"doi:{doi}") if doi else Group("paper", None, "no DOI in the source: paper unknown")
    return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy, title, doi,
                        group, harmonized, reported)
```

### `hypocurate/sources/adapters/tamu_fcc.py`

```python
"""Adapter for the Texas A&M FCC dataset (Mulukutla et al. 2026), read from its
spreadsheet, the source of record (step 1).

- One record per data row of the workbook's one sheet, `GS_MasterTable_Iterations `
  (the name ends with a space in the file), in sheet order; no row is dropped. An
  entirely blank row is listed in `blank_rows`.
- Origin key: `<file>:row:<n>`, n the 0-based data row of that sheet (the adapter reads
  only that sheet). `item_index` is 0.
- Every column is kept as reported: the header and the cell value as text (numbers in
  their shortest exact form), with the unit the header states.
- Composition: eight columns of atomic percentages (Al … V). The headers state no unit;
  the unit is documented in the paper (citation on the value). A sum other than 100 is
  marked, never rescaled.
- **Paper identity (grouping): the dataset.** The dataset is the source, with no
  per-record paper (PRD 10), so every record has the one group `dataset:<DOI>`. The
  batch (`Iteration`, six values) is kept as reported. **The grouping unit is an open
  decision for the owner (PRD 17, decision 9):** one group in sprint 1; batches only if
  the owner agrees they are independent enough. This adapter refuses any other unit.
- Values not in the file are set only where the source's own documentation states them,
  as `assigned` with the exact passage (owner, 2026-10-05, step 4 question 3):
  test type `tension`, phase class `FCC`. **Test temperature is not assigned**: the
  repository states no test temperature for these measurements (step 4 summary), so the
  temperature and its band are `not_reported`, and the owner decides later.
"""
from __future__ import annotations

import io
import math
import zipfile

import openpyxl

from hypocurate.sources import normalize as n
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation,
                                       CommonRecord, Group, Reported, Value)
from hypocurate.sources.versions import SealedVersion

SHEET = "GS_MasterTable_Iterations "  # verbatim: the sheet name ends with a space
HEADER = (
    "Iteration", "Alloy Name", "Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V", "Hardness, HV", "SD, HV",
    "YS (MPa)", "SD, YS", "Cold Work (%Reduction)", "Recrystallization Temp(℃)", "Holding time (h)",
    "Grain Size(µm)", "SD, Grain Size(µm)",
)
ELEMENT_COLUMNS = ("Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V")
# Units the headers state. "SD, YS" states none; an SD has the unit of its quantity.
UNITS = {
    "Hardness, HV": "HV", "SD, HV": "HV", "YS (MPa)": "MPa", "Cold Work (%Reduction)": "% reduction",
    "Recrystallization Temp(℃)": "°C", "Holding time (h)": "h", "Grain Size(µm)": "µm",
    "SD, Grain Size(µm)": "µm",
}

DATASET_DOI = "10.5281/zenodo.22798856"
DATASET_REFERENCE = ("Mulukutla, M. et al. (2026). Revisiting Hall-Petch strengthening in FCC "
                     "multi-principal element alloys: data and analysis pipeline (v1.1.0). Zenodo. "
                     "doi:10.5281/zenodo.22798856")

_REPO = "ArroyaveLab/2026-mulukutla-hall-petch@11390ee516c1a17cacdde318b40d5d6889d4007f"
TEST_TYPE_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 177 (Dataset and descriptors, Alloy Synthesis and characterization)",
    "Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
    "tests provided the HV.")
PHASE_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 173 (Dataset and descriptors, Alloy Synthesis and characterization)",
    "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.")
COMPOSITION_UNIT_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 399 (Results, Family 3)",
    "Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider "
    "interval.")

TEMPERATURE_NOT_REPORTED = ("no per-record temperature; the source states no test temperature for its "
                            "own measurements (owner decides; step 4 summary)")
NO_COLUMN = "the source has no column for this field"


def reported_text(value) -> str:
    """A cell value as text: "" for an empty cell, numbers in their shortest exact form."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _number(value, unit: str | None) -> Value:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Value(None, unit, "not_reported", "blank in the source")
    if isinstance(value, bool):
        return Value(None, unit, "not_convertible", f"not a number: {value!r}")
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            return Value(None, unit, "not_convertible", f"not a finite number: {value!r}")
        return Value(float(value), unit, "converted")
    return n.number(str(value), unit)


def _composition(cells: dict) -> tuple[Value, str | None]:
    columns: dict[str, float | None] = {}
    for symbol in ELEMENT_COLUMNS:
        v = _number(cells[symbol], "at.%")
        if v.status == "not_convertible":
            return Value(None, "at.%", "not_convertible", f"{symbol}: {v.reason}"), None
        columns[symbol] = v.value
    composition, reason = n.percent_columns_to_atomic_percent(columns)
    if composition is None:
        return Value(None, "at.%", "not_convertible", reason), None
    return Value(composition, "at.%", "converted", citation=COMPOSITION_UNIT_CITATION), n.alloy_label(composition)


def _harmonize(cells: dict) -> tuple[dict[str, Value], str | None]:
    h: dict[str, Value] = {}
    h["composition"], alloy = _composition(cells)
    h["grain_size"] = _number(cells["Grain Size(µm)"], "µm")
    h["grain_size_sd"] = _number(cells["SD, Grain Size(µm)"], "µm")
    h["yield_strength"] = _number(cells["YS (MPa)"], "MPa")
    h["yield_strength_sd"] = _number(cells["SD, YS"], "MPa")
    h["hardness"] = _number(cells["Hardness, HV"], "HV")
    h["hardness_sd"] = _number(cells["SD, HV"], "HV")
    h["cold_work"] = _number(cells["Cold Work (%Reduction)"], "% reduction")
    h["recrystallization_temperature"] = _number(cells["Recrystallization Temp(℃)"], "°C")
    h["holding_time"] = _number(cells["Holding time (h)"], "h")
    h["test_type"] = Value("tension", None, "assigned", citation=TEST_TYPE_CITATION)
    h["phase_class"] = Value("FCC", None, "assigned", citation=PHASE_CITATION)
    h["test_temperature"] = Value(None, "°C", "not_reported", TEMPERATURE_NOT_REPORTED)
    h["test_temperature_band"] = Value(None, None, "not_reported", TEMPERATURE_NOT_REPORTED)
    h["microstructure"] = Value(None, None, "not_reported",
                                "the source does not state the phases present per record")
    h["processing_method"] = Value(None, None, "not_reported",
                                   "the source gives processing parameters (cold work, recrystallization "
                                   "temperature, holding time), not a processing-method category")
    h["ultimate_tensile_strength"] = Value(None, "MPa", "not_reported", NO_COLUMN)
    assert set(h) == set(HARMONIZED_FIELDS)
    return h, alloy


def read(version: SealedVersion) -> AdapterResult:
    version.verify()
    if version.grouping_unit != "dataset":
        raise AdapterError(f"the Texas A&M adapter supports the grouping unit 'dataset' only "
                           f"(PRD 17, decision 9); version {version.id} has {version.grouping_unit!r}")
    if len(version.files) != 1:
        raise AdapterError(f"expected one spreadsheet, found {sorted(version.files)}")
    (path, content), = version.files.items()
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False)
    except (zipfile.BadZipFile, OSError, ValueError, KeyError) as error:
        raise AdapterError(f"{path} is not a readable spreadsheet: {error}") from None
    if SHEET not in workbook.sheetnames:
        raise AdapterError(f"{path} has no sheet {SHEET!r}")
    rows = workbook[SHEET].iter_rows(values_only=True)
    header = list(next(rows, ()))
    while header and header[-1] is None:  # empty cells past the last header (a wider data row)
        header.pop()
    if tuple(header) != HEADER:
        raise AdapterError(f"{path}: the header of {SHEET!r} is not the Texas A&M layout")
    records, blank = [], []
    for i, values in enumerate(rows):
        if all(v is None or (isinstance(v, str) and v.strip() == "") for v in values):
            blank.append(i)
            continue
        records.append(_record(version, path, i, values))
    workbook.close()
    return AdapterResult(tuple(records), tuple(blank))


def _record(version: SealedVersion, path: str, i: int, values: tuple) -> CommonRecord:
    key = f"{path}:row:{i}"
    reported = {name: Reported(name, reported_text(v), UNITS.get(name)) for name, v in zip(HEADER, values)}
    for extra, v in enumerate(values[len(HEADER):], start=len(HEADER) + 1):
        if v is not None:
            reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", reported_text(v), None)
    group = Group("dataset", f"dataset:{DATASET_DOI}")
    formulas = [name for name, v in zip(HEADER, values) if isinstance(v, str) and v.startswith("=")]
    if formulas:
        reason = f"cells hold formulas, not values: {', '.join(formulas)}"
        harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
        return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None,
                            DATASET_REFERENCE, None, group, harmonized, reported)
    harmonized, alloy = _harmonize(dict(zip(HEADER, values)))
    return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy,
                        DATASET_REFERENCE, None, group, harmonized, reported)
```

## 5. Application code: test connection and command line

### `hypocurate/sources/connection.py`

```python
"""'Test connection and show sample records' (PRD 9.6; step 4).

Loads the latest sealed version of a source, reads it with its adapter, and returns the
first few records in the common record format, with counts. It only reads: the
transaction is READ ONLY, so it cannot write to the database."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sqlalchemy import Engine, text

from hypocurate.sources import adapters
from hypocurate.sources.record import CommonRecord
from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version


@dataclass(frozen=True)
class ConnectionReport:
    source_key: str
    version_id: int
    version_label: str
    fingerprint: str
    records_read: int
    blank_rows: int
    status_counts: dict[str, int]  # harmonized values by status, over all records read
    sample: tuple[CommonRecord, ...]

    def to_json(self) -> dict:
        return {
            "source_key": self.source_key, "version_id": self.version_id, "version_label": self.version_label,
            "fingerprint": self.fingerprint, "records_read": self.records_read, "blank_rows": self.blank_rows,
            "status_counts": self.status_counts, "sample": [r.to_json() for r in self.sample],
        }


def test_connection(engine: Engine, key: str, n: int = 5) -> ConnectionReport:
    if n < 1:
        raise ValueError("n must be at least 1")
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        version = load_sealed_version(conn, latest_sealed_version_id(conn, key))
        conn.rollback()
    result = adapters.read(version)
    counts = Counter(v.status for r in result.records for v in r.harmonized.values())
    return ConnectionReport(key, version.id, version.label, version.fingerprint, len(result.records),
                            len(result.blank_rows), dict(sorted(counts.items())), result.records[:n])


test_connection.__test__ = False  # a function, not a pytest test
```

### `hypocurate/cli.py`

```python
"""The command-line entry point (PRD Section 12). Step 2: `version` and `check-db`.
Step 4: `sources register` and `sources test`."""
from __future__ import annotations

import argparse
import json
import sys

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypocurate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="print the deployed version")
    sub.add_parser("check-db", help="check that the database answers")
    sources = sub.add_parser("sources", help="register the frozen sources; test a connection")
    sources_sub = sources.add_subparsers(dest="sources_command", required=True)
    register = sources_sub.add_parser("register", help="register and seal the frozen sources")
    register.add_argument("keys", nargs="*", help="source keys (default: all)")
    test = sources_sub.add_parser("test", help="read a source and show sample records")
    test.add_argument("key")
    test.add_argument("-n", type=int, default=5, help="number of sample records (default 5)")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    if args.command == "version":
        print(settings.version)
        return 0
    engine = make_engine(settings.database_url)
    if args.command == "check-db":
        reachable = database_reachable(engine)
        print("database reachable" if reachable else "database NOT reachable")
        return 0 if reachable else 1
    return _sources(args, engine)


def _sources(args, engine) -> int:
    from hypocurate.sources.connection import test_connection
    from hypocurate.sources.record import AdapterError
    from hypocurate.sources.versions import SOURCES, RegistrationError, UnsealedVersion, register

    try:
        if args.sources_command == "register":
            for key in args.keys or list(SOURCES):
                r = register(engine, key)
                state = "registered and sealed" if r.created else "already registered"
                print(f"{r.key}: {state}; version {r.version_id} ({r.label}); fingerprint {r.fingerprint}")
            return 0
        report = test_connection(engine, args.key, args.n)
        # Assigned values carry status "assigned" and their citation in this output.
        print(json.dumps(report.to_json(), indent=2, ensure_ascii=False))
        return 0
    except (RegistrationError, UnsealedVersion, AdapterError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## 6. Tests

### `tests/source_helpers.py`

```python
"""Builds `SealedVersion` objects for adapter tests without a database. The real path
(`load_sealed_version`) is tested in test_source_versions.py; these objects carry a
correct digest and identity, so `verify()` passes exactly as for a loaded version."""
from __future__ import annotations

from datetime import datetime, timezone

from hypocurate.sources.versions import (SOURCES, SealedVersion, files_digest, read_definition_files,
                                         version_identity)


def sealed(key: str, files: dict[str, bytes], grouping_unit: str | None = None, version_id: int = 1) -> SealedVersion:
    d = SOURCES[key]
    unit = grouping_unit or d.grouping_unit
    digest = files_digest(files)
    return SealedVersion(version_id, key, d.version_label, d.source_type, d.data_kind, unit,
                         datetime.now(timezone.utc), digest,
                         version_identity(digest, d.source_type, d.data_kind, unit), files)


def sealed_from_disk(key: str) -> SealedVersion:
    files, _ = read_definition_files(SOURCES[key])
    return sealed(key, files)
```

### `tests/test_write_retry.py`

```python
"""Step 4: `run_transaction` retries the whole transaction on deadlock (40P01) or
serialization failure (40001), and on nothing else (step 3, open item 3)."""
import threading

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from hypocurate.db.retry import run_transaction, sqlstate


class _Orig(Exception):
    def __init__(self, state):
        super().__init__(state)
        self.sqlstate = state


def failure(state):
    return OperationalError("SELECT 1", {}, _Orig(state))


def add_source(conn, key):
    conn.execute(text(
        "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
        "VALUES (:k, :k, 'uploaded_table', 'test', 'measured', 'available', true, 'paper')"), dict(k=key))


@pytest.mark.parametrize("state", ["40P01", "40001"])
def test_a_retryable_failure_reruns_the_whole_transaction(db, state):
    calls = []

    def fn(conn):
        calls.append(1)
        add_source(conn, "retry")  # would violate the unique key if the first attempt had stayed
        if len(calls) == 1:
            raise failure(state)
        return "done"

    assert run_transaction(db, fn, backoff=0) == "done"
    assert len(calls) == 2
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM source WHERE key = 'retry'")).scalar() == 1


def test_other_errors_are_not_retried(db):
    calls = []

    def fn(conn):
        calls.append(1)
        add_source(conn, "dup")
        add_source(conn, "dup")

    with pytest.raises(IntegrityError) as error:
        run_transaction(db, fn, backoff=0)
    assert sqlstate(error.value) == "23505" and len(calls) == 1
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM source")).scalar() == 0


def test_it_gives_up_after_the_last_attempt(db):
    calls = []

    def fn(conn):
        calls.append(1)
        raise failure("40P01")

    with pytest.raises(OperationalError):
        run_transaction(db, fn, attempts=3, backoff=0)
    assert len(calls) == 3


def test_a_real_deadlock_is_retried_to_completion(db):
    """Two transactions lock two source rows in opposite orders. PostgreSQL aborts one
    with 40P01; run_transaction runs it again, and both complete."""
    with db.begin() as conn:
        add_source(conn, "a")
        add_source(conn, "b")
    barrier = threading.Barrier(2)
    attempts = {"ab": 0, "ba": 0}
    results, errors = [], []

    def worker(first, second, name):
        def fn(conn):
            attempts[name] += 1
            conn.execute(text("SELECT 1 FROM source WHERE key = :k FOR UPDATE"), dict(k=first))
            if attempts[name] == 1:
                barrier.wait(10)
            conn.execute(text("SELECT 1 FROM source WHERE key = :k FOR UPDATE"), dict(k=second))
            return name
        try:
            results.append(run_transaction(db, fn, backoff=0.01))
        except Exception as error:  # reported below
            errors.append(error)

    threads = [threading.Thread(target=worker, args=("a", "b", "ab")),
               threading.Thread(target=worker, args=("b", "a", "ba"))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert errors == []
    assert sorted(results) == ["ab", "ba"]
    assert sorted(attempts.values()) == [1, 2]
```

### `tests/test_source_versions.py`

```python
"""Step 4: registering the three sources as sealed versions (step 3 requirements).

- The files digest and identity computed in Python equal the database's.
- Every version is sealed before use; an unsealed or altered version is refused.
- Registration locks the source row first (owner, step 4 question 1) and is retried
  on deadlock; registering twice, or at the same time, leaves one version.
- Every manifest path read stays inside its directory (step 3, open item 4)."""
import dataclasses
import json
import shutil
import threading
import time
from pathlib import Path

import pytest
from sqlalchemy import text

from hypocurate.sources import adapters
from hypocurate.sources.manifest import load_manifest
from hypocurate.sources.versions import (SOURCES, RegistrationError, UnsealedVersion, _register_in, files_digest,
                                         latest_sealed_version_id, load_sealed_version, read_definition_files,
                                         register, safe_path_within, sha256_hex, version_identity)

REPO = Path(__file__).resolve().parents[1]


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def val(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def add_unsealed(engine, key, files, unit="paper"):
    with engine.begin() as conn:
        sid = conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES (:k, :k, 'uploaded_table', 'test', 'measured', 'available', true, :u) RETURNING id"),
            dict(k=key, u=unit)).scalar_one()
        vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) "
                                "VALUES (:s, 'v', '2026-10-05') RETURNING id"), dict(s=sid)).scalar_one()
        for path, content in files.items():
            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) "
                              "VALUES (:v, :p, :h, :c)"), dict(v=vid, p=path, h=sha256_hex(content), c=content))
    return vid


# --- The database's definitions ------------------------------------------------------

FILE_SETS = [
    {"a.csv": b"1"},
    {"b.csv": b"x", "B.csv": b"y", "a.csv": b"z"},             # bytewise: upper case first
    {"a-b.csv": b"1", "a.b.csv": b"2", "a/b.csv": b"3", "a_b.csv": b"4", "aB.xlsx": b"5"},
    {"dir/z.csv": b"", "dir/A.xlsx": b"\x00\xff"},
]


@pytest.mark.parametrize("files", FILE_SETS)
def test_files_digest_equals_the_databases(db, files):
    vid = add_unsealed(db, "digest_test", files)
    assert val(db, "SELECT hc_files_digest(:v)", v=vid) == files_digest(files)


def test_version_identity_equals_the_databases(db):
    digest = files_digest({"a.csv": b"1"})
    for source_type in ("uploaded_table", "web_interface", "paper_search", "model_recall"):
        for kind in ("measured", "computed", "model_recalled"):
            for unit in ("paper", "dataset", "batch"):
                assert val(db, "SELECT hc_version_identity(:d, :t, :k, :u)", d=digest, t=source_type, k=kind,
                           u=unit) == version_identity(digest, source_type, kind, unit)


def test_an_unsafe_stored_path_is_refused_before_the_database():
    for path in ("a\n.csv", "../a.csv", "/a.csv", "a.txt", ".a.csv", "a b.csv"):
        with pytest.raises(RegistrationError, match="unsafe"):
            files_digest({path: b"1"})


# --- Registration --------------------------------------------------------------------

def test_registering_seals_every_source(db):
    for key, d in SOURCES.items():
        r = register(db, key)
        assert r.created
        files, obtained = read_definition_files(d)
        assert r.files_digest == files_digest(files)
        assert r.fingerprint == version_identity(r.files_digest, d.source_type, d.data_kind, d.grouping_unit)
        (sealed_at, digest, fp, label, on, stype, kind, unit), = rows(db, (
            "SELECT sealed_at, files_digest, fingerprint, label, obtained_on, source_type, data_kind, grouping_unit "
            "FROM source_version WHERE id = :v"), v=r.version_id)
        assert sealed_at is not None and (digest, fp, label) == (r.files_digest, r.fingerprint, d.version_label)
        assert (on, stype, kind, unit) == (obtained, d.source_type, d.data_kind, d.grouping_unit)
        stored = {p: bytes(c) for p, c in rows(db, "SELECT path, content FROM source_file WHERE source_version_id = :v",
                                                v=r.version_id)}
        assert stored == files
        (enabled, status), = rows(db, "SELECT enabled, adapter_status FROM source WHERE key = :k", k=key)
        assert (enabled, status) == (d.enabled, "available")
    stored_paths = {p for (p,) in rows(db, "SELECT path FROM source_file")}
    assert stored_paths == {"MPEA_dataset.csv", "Grain_Size_Summary_v3.xlsx", "extract.csv"}
    assert val(db, "SELECT enabled FROM source WHERE key = 'controlled_duplicates'") is False


def test_registering_again_adds_nothing(db):
    first = {k: register(db, k) for k in SOURCES}
    counts = [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")]
    again = {k: register(db, k) for k in SOURCES}
    assert counts == [3, 3, 3]
    assert [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")] == counts
    assert all(not r.created and r.version_id == first[k].version_id and r.fingerprint == first[k].fingerprint
               for k, r in again.items())


def waiting_on_a_lock(engine) -> int:
    return val(engine, "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                       "AND wait_event_type = 'Lock' AND state = 'active'")


def test_concurrent_registration_waits_on_the_source_lock_and_leaves_one_version(db):
    d = SOURCES["mpea"]
    files, obtained = read_definition_files(d)
    outcome = {}

    def second():
        try:
            outcome["result"] = register(db, "mpea")
        except Exception as error:  # reported below
            outcome["result"] = error

    with db.connect() as a:
        tx = a.begin()
        first = _register_in(a, d, files, obtained)  # holds the source row lock, uncommitted
        thread = threading.Thread(target=second)
        thread.start()
        deadline = time.monotonic() + 10
        while waiting_on_a_lock(db) == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert thread.is_alive() and waiting_on_a_lock(db) == 1, "the second registration should wait"
        tx.commit()
    thread.join(30)
    result = outcome["result"]
    assert not isinstance(result, Exception), result
    assert first.created and not result.created and result.version_id == first.version_id
    assert val(db, "SELECT count(*) FROM source_version") == 1


def test_the_source_lock_serializes_a_new_version_of_an_existing_source(db):
    """The source row exists, but its version does not (a second version later, or a
    registration that failed before sealing). Without the source-row lock both writers
    would insert a version and the second would fail at sealing on the unique identity."""
    d = SOURCES["mpea"]
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES ('mpea', 'x', :t, 'x', :k, 'available', true, :u)"),
            dict(t=d.source_type, k=d.data_kind, u=d.grouping_unit))
    test_concurrent_registration_waits_on_the_source_lock_and_leaves_one_version(db)


def test_two_registrations_at_once_leave_one_version(db):
    barrier = threading.Barrier(2)
    results = []

    def go():
        barrier.wait()
        results.append(register(db, "tamu_fcc"))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert sorted(r.created for r in results) == [False, True]
    assert len({r.version_id for r in results}) == 1
    assert val(db, "SELECT count(*) FROM source_version") == 1


@pytest.fixture
def data_copy(tmp_path):
    """A copy of data/ to alter, with the original manifest."""
    copy = tmp_path / "data"
    shutil.copytree(REPO / "data", copy)
    return copy


def test_a_changed_file_is_refused_and_nothing_is_written(db, data_copy):
    path = data_copy / "sources/mpea/MPEA_dataset.csv"
    content = bytearray(path.read_bytes())
    content[-2] ^= 1
    path.write_bytes(bytes(content))
    with pytest.raises(RegistrationError, match="does not match its manifest fingerprint"):
        register(db, "mpea", data_dir=data_copy)
    assert val(db, "SELECT count(*) FROM source") == 0


def test_changed_interpretation_settings_are_refused(db):
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES ('tamu_fcc', 'x', 'uploaded_table', 'MIT', 'measured', 'available', true, 'batch')"))
    with pytest.raises(RegistrationError, match="not made silently"):
        register(db, "tamu_fcc")
    assert val(db, "SELECT count(*) FROM source_version") == 0
    assert val(db, "SELECT grouping_unit FROM source WHERE key = 'tamu_fcc'") == "batch"


def test_an_unknown_source_is_refused(db):
    with pytest.raises(RegistrationError, match="unknown source"):
        register(db, "nope")


# --- Paths ---------------------------------------------------------------------------

def test_paths_must_stay_inside_their_directory(tmp_path):
    base = tmp_path / "base"
    (base / "a").mkdir(parents=True)
    (tmp_path / "outside.csv").write_text("x")
    assert safe_path_within(base, "a/../b.csv") == (base / "b.csv").resolve()
    for bad in ("a/../../outside.csv", "../outside.csv", "/etc/passwd", str(tmp_path / "outside.csv"), ""):
        with pytest.raises(RegistrationError):
            safe_path_within(base, bad)
    (base / "link.csv").symlink_to(tmp_path / "outside.csv")
    with pytest.raises(RegistrationError, match="leaves"):
        safe_path_within(base, "link.csv")


def test_a_definition_pointing_outside_data_is_refused(data_copy):
    escaping = dataclasses.replace(SOURCES["mpea"], directory="../../tests")
    with pytest.raises(RegistrationError, match="leaves"):
        read_definition_files(escaping, data_dir=data_copy)
    via_name = dataclasses.replace(SOURCES["mpea"], data_files=("../tamu_fcc/inputs.csv",))
    with pytest.raises(RegistrationError):
        read_definition_files(via_name, data_dir=data_copy)


def test_a_file_missing_from_the_manifest_is_refused(data_copy):
    manifest = load_manifest(data_copy / "manifest.json")
    manifest["sources"]["mpea"]["files"] = []
    with pytest.raises(RegistrationError, match="not in the manifest"):
        read_definition_files(SOURCES["mpea"], data_dir=data_copy, manifest=manifest)


# --- Sealed before use ---------------------------------------------------------------

def test_an_unsealed_version_is_refused(db):
    vid = add_unsealed(db, "unsealed", {"a.csv": b"1"})
    with db.connect() as conn:
        with pytest.raises(UnsealedVersion, match="not sealed"):
            load_sealed_version(conn, vid)
        with pytest.raises(UnsealedVersion, match="no sealed version"):
            latest_sealed_version_id(conn, "unsealed")
        with pytest.raises(UnsealedVersion, match="no source version"):
            load_sealed_version(conn, vid + 1000)


def test_a_loaded_version_reads_like_the_files_on_disk(db):
    from source_helpers import sealed_from_disk
    for key in SOURCES:
        r = register(db, key)
        with db.connect() as conn:
            assert latest_sealed_version_id(conn, key) == r.version_id
            version = load_sealed_version(conn, r.version_id)
        assert (version.files_digest, version.fingerprint) == (r.files_digest, r.fingerprint)
        from_db = [x.to_json() for x in adapters.read(version).records]
        from_disk = [x.to_json() for x in adapters.read(sealed_from_disk(key)).records]
        assert json.dumps(from_db) == json.dumps(from_disk)


def test_changed_settings_on_a_loaded_version_are_refused(db):
    r = register(db, "tamu_fcc")
    with db.connect() as conn:
        version = load_sealed_version(conn, r.version_id)
    with pytest.raises(UnsealedVersion, match="sealed identity"):
        adapters.read(dataclasses.replace(version, grouping_unit="batch"))
```

### `tests/test_adapter_mpea.py`

```python
"""Step 4: the MPEA-layout adapter on the frozen MPEA dataset, and on planted rows.

An adapter converts and reports: one record per row, nothing dropped, every value as
reported kept with its unit, anything unconvertible kept and marked with the reason."""
import csv
import dataclasses
import io
import re
from collections import Counter
from pathlib import Path

import pytest

from hypocurate.sources import adapters
from hypocurate.sources.adapters import mpea_layout
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, CommonRecord
from hypocurate.sources.versions import UnsealedVersion
from source_helpers import sealed, sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
MPEA_CSV = REPO / "data/sources/mpea/MPEA_dataset.csv"
GS = "PROPERTY: grain size ($\\mu$m)"


@pytest.fixture(scope="module")
def version():
    return sealed_from_disk("mpea")


@pytest.fixture(scope="module")
def result(version):
    return adapters.read(version)


@pytest.fixture(scope="module")
def rows():
    with open(MPEA_CSV, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))[1:]


def test_one_record_per_row_none_dropped(result, rows):
    assert len(rows) == 1545
    assert len(result.records) == 1545
    assert result.blank_rows == ()
    assert [r.source_item_key for r in result.records] == [f"MPEA_dataset.csv:row:{i}" for i in range(1545)]
    assert all(r.item_index == 0 for r in result.records)


def test_every_value_is_kept_as_reported_with_its_unit(result, rows):
    for record, row in zip(result.records, rows):
        assert list(record.reported) == list(mpea_layout.HEADER)
        assert [r.text for r in record.reported.values()] == row
        assert all(r.column == name for name, r in record.reported.items())
    first = result.records[0].reported
    assert first[GS].unit == "µm"
    assert first["PROPERTY: YS (MPa)"].unit == "MPa"
    assert first["PROPERTY: Test temperature ($^\\circ$C)"].unit == "°C"
    assert first["FORMULA"].unit is None


def test_every_record_has_the_common_fields_with_their_units(result):
    for r in result.records:
        assert set(r.harmonized) == set(HARMONIZED_FIELDS)
        assert all(v.unit == HARMONIZED_FIELDS[k] for k, v in r.harmonized.items())
        assert r.kind == "measured"
        assert r.source_key == "mpea"


def test_numbers_are_converted_unchanged(result, rows):
    for record, row in zip(result.records, rows):
        for field, col in (("grain_size", 5), ("hardness", 8), ("test_temperature", 10),
                           ("yield_strength", 11), ("ultimate_tensile_strength", 12)):
            v = record.harmonized[field]
            if row[col] == "":
                assert (v.status, v.reason) == ("not_reported", "blank in the source")
            else:
                assert (v.status, v.value) == ("converted", float(row[col]))


def test_grain_size_counts(result):
    statuses = Counter(r.harmonized["grain_size"].status for r in result.records)
    assert statuses == {"converted": 237, "not_reported": 1308}


def test_nothing_in_the_frozen_file_is_unconvertible(result):
    assert not [(r.source_item_key, k) for r in result.records for k, v in r.harmonized.items()
                if v.status == "not_convertible"]


def test_test_type_codes(result):
    assert Counter(r.harmonized["test_type"].value or r.harmonized["test_type"].status
                   for r in result.records) == {"compression": 792, "tension": 358, "not_reported": 395}


def test_no_value_is_assigned(result):
    assert not [r for r in result.records for v in r.harmonized.values()
                if v.status == "assigned" or v.citation is not None]


def _reference_norm(f):
    """The reference script's alloy naming (docs/reference/worked_example.py), copied."""
    comp = {}
    for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
        comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
    s = sum(comp.values())
    return ''.join(f"{e}{round(100 * v / s, 1):g}" for e, v in sorted(comp.items()))


def test_alloy_names_follow_the_reference_naming(result, rows):
    for record, row in zip(result.records, rows):
        assert record.alloy == _reference_norm(row[1])
        assert sum(record.harmonized["composition"].value.values()) == pytest.approx(100)


def test_paper_identity_is_the_doi(result, rows):
    for record, row in zip(result.records, rows):
        assert record.paper_doi == row[20]
        assert record.group.unit == "paper"
        assert record.group.key == f"doi:{row[20]}"
        assert record.paper_reference == (row[22] or None)
    assert len({r.group.key for r in result.records}) == 265
    # In the frozen file the DOI and the Reference ID are one-to-one.
    assert len({(row[0], row[20]) for row in rows}) == len({row[20] for row in rows}) == len({row[0] for row in rows})


def test_the_record_format_has_no_decision_fields():
    names = {f.name for f in dataclasses.fields(CommonRecord)}
    assert names == {"source_key", "version_fingerprint", "source_item_key", "item_index", "kind", "alloy",
                     "paper_reference", "paper_doi", "group", "harmonized", "reported"}


# --- Planted rows --------------------------------------------------------------------

def planted(lines: list[str]) -> bytes:
    header = MPEA_CSV.read_bytes().split(b"\n", 1)[0].decode("utf-8")
    return ("\n".join([header] + lines) + "\n").encode("utf-8")


GOOD = "1,Co1 Cr1 Ni1,FCC,CAST,FCC,50.0,,8.0,,T,25.0,300.0,,,,,,,,,10.1/x,2020,A paper"


def _row(**changes):
    fields = next(csv.reader([GOOD]))
    for col, value in changes.items():
        fields[int(col[1:])] = value
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(fields)
    return buf.getvalue()


def test_planted_values_are_kept_and_marked():
    lines = [
        GOOD,
        _row(c5="abc"),              # 1: grain size not a number
        _row(c1="Xx1 Co1"),          # 2: unknown element
        _row(c1=""),                 # 3: no formula
        _row(c5="-5"),               # 4: negative grain size: converted as reported, not judged here
        _row(c10="25 C"),            # 5: temperature with text
        _row(c9="X"),                # 6: unknown test type
        _row(c20=""),                # 7: no DOI
        "",                          # 8: blank line
        GOOD + ",extra",             # 9: an extra field
        _row(c11="nan"),             # 10: not finite
        _row(c1="Co1 Cr0 Ni1"),      # 11: zero amount
    ]
    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(lines)}))
    by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
    assert result.blank_rows == (8,)
    assert sorted(by_row) == [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11]

    def h(i, field):
        return by_row[i].harmonized[field]

    assert h(0, "grain_size").value == 50.0 and by_row[0].alloy == "Co33.3Cr33.3Ni33.3"
    assert (h(1, "grain_size").status, h(1, "grain_size").reason) == ("not_convertible", "not a number: 'abc'")
    assert by_row[1].reported[GS].text == "abc"
    assert h(2, "composition").status == "not_convertible" and "unknown element symbol 'Xx'" in h(2, "composition").reason
    assert by_row[2].alloy is None and by_row[2].reported["FORMULA"].text == "Xx1 Co1"
    assert h(3, "composition").status == "not_reported" and by_row[3].alloy is None
    assert (h(4, "grain_size").status, h(4, "grain_size").value) == ("converted", -5.0)
    assert h(5, "test_temperature").status == "not_convertible"
    assert by_row[5].reported["PROPERTY: Test temperature ($^\\circ$C)"].text == "25 C"
    assert h(6, "test_type").status == "not_convertible" and "'X'" in h(6, "test_type").reason
    assert by_row[7].group.key is None and by_row[7].group.reason == "no DOI in the source: paper unknown"
    assert by_row[7].paper_doi is None
    assert all(v.status == "not_convertible" for v in by_row[9].harmonized.values())
    assert by_row[9].reported["(column 24, no header)"].text == "extra"
    assert by_row[9].group.key is None
    assert h(10, "yield_strength").status == "not_convertible"
    assert h(11, "composition").status == "not_convertible" and "not positive" in h(11, "composition").reason


def test_a_file_in_another_layout_is_refused():
    with pytest.raises(AdapterError, match="header"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"a,b\n1,2\n"}))
    with pytest.raises(AdapterError, match="UTF-8"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"\xff\xfe\x00"}))


def test_another_grouping_unit_is_refused():
    with pytest.raises(AdapterError, match="groups by paper"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([GOOD])}, grouping_unit="dataset"))


def test_altered_bytes_are_refused_before_parsing(version):
    tampered = dataclasses.replace(version, files={"MPEA_dataset.csv": planted([GOOD])})
    with pytest.raises(UnsealedVersion, match="files digest"):
        adapters.read(tampered)
    with pytest.raises(UnsealedVersion, match="not sealed"):
        adapters.read(dataclasses.replace(version, sealed_at=None))


def test_text_is_kept_exactly_as_reported(result, rows):
    """One MPEA DOI has a leading space; the adapter keeps it (no silent correction)."""
    spaced = [r for r in result.records if r.paper_doi and r.paper_doi != r.paper_doi.strip()]
    assert [r.paper_doi for r in spaced] == [" 10.1038/ncomms10602"]
    assert spaced[0].group.key == "doi: 10.1038/ncomms10602"
```

### `tests/test_adapter_extract.py`

```python
"""Step 4: the controlled duplicate extract, read by the MPEA-layout adapter.

Each extract row is an MPEA row copied unchanged or with listed columns changed (step 1).
The adapter must give the same harmonized values for both, except where a listed column
changed. The answer file is read here, on the test side only; the adapter never sees it.
Duplicate handling itself is step 6."""
import csv
from pathlib import Path

import pytest

from hypocurate.sources import adapters
from source_helpers import sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
TRUTH = REPO / "tests/fixtures/controlled_duplicates/truth.csv"

# Which harmonized fields (and record attributes) each changed column feeds.
FEEDS = {
    "FORMULA": {"composition"},
    "PROPERTY: YS (MPa)": {"yield_strength"},
    "PROPERTY: Test temperature ($^\\circ$C)": {"test_temperature"},
    "PROPERTY: Type of test": {"test_type"},
    "IDENTIFIER: Reference ID": set(),
    "REFERENCE: doi": {"paper_doi", "group"},
    "REFERENCE: year": set(),
    "REFERENCE: title": {"paper_reference"},
}


@pytest.fixture(scope="module")
def extract():
    return adapters.read(sealed_from_disk("controlled_duplicates")).records


@pytest.fixture(scope="module")
def mpea():
    return adapters.read(sealed_from_disk("mpea")).records


@pytest.fixture(scope="module")
def truth():
    with open(TRUTH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_sixteen_records_with_origin_keys(extract):
    assert [r.source_item_key for r in extract] == [f"extract.csv:row:{i}" for i in range(16)]
    assert all(r.source_key == "controlled_duplicates" and r.kind == "measured" for r in extract)


def test_each_record_equals_its_mpea_row_except_the_changed_columns(extract, mpea, truth):
    assert len(truth) == 16
    for t, record in zip(truth, extract):
        source = mpea[int(t["mpea_row"])]
        changed = [c for c in t["changed_columns"].split("; ") if c]
        changed_fields = set().union(*(FEEDS[c] for c in changed)) if changed else set()
        for name, value in record.harmonized.items():
            if name in changed_fields:
                continue
            assert value == source.harmonized[name], (t["extract_row"], name)
        for attr in ("paper_doi", "paper_reference", "group"):
            if attr not in changed_fields:
                assert getattr(record, attr) == getattr(source, attr), (t["extract_row"], attr)
        if "FORMULA" not in changed:
            assert record.alloy == source.alloy
        for column, rep in record.reported.items():
            if column not in changed:
                assert rep == source.reported[column], (t["extract_row"], column)
            else:
                assert rep.text != source.reported[column].text


def test_a_renamed_formula_gives_the_same_alloy(extract, mpea, truth):
    renamed = [(t, r) for t, r in zip(truth, extract) if t["changed_columns"] == "FORMULA"]
    assert len(renamed) == 2
    for t, record in renamed:
        source = mpea[int(t["mpea_row"])]
        assert record.reported["FORMULA"].text != source.reported["FORMULA"].text
        assert record.alloy == source.alloy
        a, b = record.harmonized["composition"].value, source.harmonized["composition"].value
        assert a.keys() == b.keys() and all(a[e] == pytest.approx(b[e], abs=1e-9) for e in a)


def test_paper_unknown_is_marked_never_invented(extract, truth):
    blank = [r for t, r in zip(truth, extract) if "REFERENCE: doi" in t["changed_columns"]
             and r.reported["REFERENCE: doi"].text == ""]
    assert len(blank) == 2
    for r in blank:
        assert r.paper_doi is None and r.group.key is None
        assert r.group.reason == "no DOI in the source: paper unknown"


def test_a_constructed_doi_is_its_own_paper(extract):
    constructed = [r for r in extract if (r.paper_doi or "").startswith("10.5555/hypocurate-test-")]
    assert [r.group.key for r in constructed] == ["doi:10.5555/hypocurate-test-0001",
                                                  "doi:10.5555/hypocurate-test-0002"]
    # Their Reference ID is blank; the DOI alone identifies the paper.
    assert all(r.reported["IDENTIFIER: Reference ID"].text == "" for r in constructed)
```

### `tests/test_adapter_tamu.py`

```python
"""Step 4: the Texas A&M adapter on the frozen spreadsheet, and on planted rows.

Assigned values (owner, step 4 question 3) are set only where the source's own paper
states them, always with the passage, and stay distinguishable from reported values.
The test temperature is not stated, so it is not reported."""
import csv
import dataclasses
import io
import json
from collections import Counter
from pathlib import Path

import openpyxl
import pytest

from hypocurate.sources import adapters
from hypocurate.sources.adapters import tamu_fcc
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, Reported
from source_helpers import sealed, sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
XLSX = REPO / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
INPUTS = REPO / "data/sources/tamu_fcc/inputs.csv"
FILE = "Grain_Size_Summary_v3.xlsx"


@pytest.fixture(scope="module")
def records():
    result = adapters.read(sealed_from_disk("tamu_fcc"))
    assert result.blank_rows == ()
    return result.records


@pytest.fixture(scope="module")
def sheet_rows():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    rows = list(wb[tamu_fcc.SHEET].iter_rows(values_only=True))
    wb.close()
    return rows[1:]


def test_one_record_per_sample_none_dropped(records, sheet_rows):
    assert len(sheet_rows) == len(records) == 94
    assert [r.source_item_key for r in records] == [f"{FILE}:row:{i}" for i in range(94)]
    assert all(r.source_key == "tamu_fcc" and r.kind == "measured" and r.item_index == 0 for r in records)


def test_every_value_is_kept_as_reported(records, sheet_rows):
    for record, row in zip(records, sheet_rows):
        assert list(record.reported) == list(tamu_fcc.HEADER)
        assert [r.text for r in record.reported.values()] == [tamu_fcc.reported_text(v) for v in row]
    units = records[0].reported
    assert (units["Grain Size(µm)"].unit, units["YS (MPa)"].unit, units["Hardness, HV"].unit) == ("µm", "MPa", "HV")
    assert units["Al"].unit is None  # the header states none; the paper does (citation on the value)


def test_the_sample_without_yield_strength_is_kept(records):
    missing = [r for r in records if r.harmonized["yield_strength"].status != "converted"]
    assert [r.reported["Alloy Name"].text for r in missing] == ["BBA09"]
    assert missing[0].harmonized["yield_strength"].reason == "blank in the source"
    assert missing[0].harmonized["grain_size"].status == "converted"


def test_one_group_the_dataset(records):
    assert {r.group.key for r in records} == {"dataset:10.5281/zenodo.22798856"}
    assert {r.group.unit for r in records} == {"dataset"}
    assert {r.paper_reference for r in records} == {tamu_fcc.DATASET_REFERENCE}
    assert {r.paper_doi for r in records} == {None}
    # The batch is kept as reported, for the owner's grouping decision (PRD 17, decision 9).
    assert Counter(r.reported["Iteration"].text for r in records) == {
        "CBA": 23, "CBC": 21, "BBA": 18, "CBB": 15, "BBB": 9, "BBC": 8}


def test_assigned_values_carry_their_passage(records):
    for r in records:
        t, p = r.harmonized["test_type"], r.harmonized["phase_class"]
        assert (t.value, t.status, t.citation) == ("tension", "assigned", tamu_fcc.TEST_TYPE_CITATION)
        assert (p.value, p.status, p.citation) == ("FCC", "assigned", tamu_fcc.PHASE_CITATION)
        assert "Quasistatic tensile testing" in t.citation.quote and t.citation.location.startswith("line 177")
        assert "94 FCC alloy conditions" in p.citation.quote
        out = r.to_json()["harmonized"]
        assert out["test_type"]["status"] == "assigned" and out["test_type"]["citation"]["quote"]
    assigned = {k for r in records for k, v in r.harmonized.items() if v.status == "assigned"}
    assert assigned == {"test_type", "phase_class"}


def test_assigned_and_reported_stay_distinguishable(records):
    for r in records:
        for v in r.harmonized.values():
            assert (v.status == "assigned") <= (v.citation is not None)
        assert all(isinstance(rep, Reported) and not hasattr(rep, "citation") for rep in r.reported.values())
        assert "tension" not in {rep.text for rep in r.reported.values()}


def test_temperature_is_not_reported(records):
    for r in records:
        for name in ("test_temperature", "test_temperature_band"):
            v = r.harmonized[name]
            assert (v.status, v.value) == ("not_reported", None)
            assert "states no test temperature" in v.reason


def test_composition_in_atomic_percent(records):
    for r in records:
        c = r.harmonized["composition"]
        assert c.status == "converted" and c.citation == tamu_fcc.COMPOSITION_UNIT_CITATION
        assert sum(c.value.values()) == pytest.approx(100, abs=1e-9)
        for e in tamu_fcc.ELEMENT_COLUMNS:
            assert c.value.get(e, 0.0) == float(r.reported[e].text)
    # 82 distinct compositions (PRD 10), and the naming keeps them distinct.
    assert len({tuple(sorted(r.harmonized["composition"].value.items())) for r in records}) == 82
    assert len({r.alloy for r in records}) == 82


def test_agrees_with_the_authors_csv_view(records):
    with open(INPUTS, encoding="utf-8", newline="") as f:
        view = {row["Alloy"]: row for row in csv.DictReader(f)}
    assert len(view) == 94
    for r in records:
        row = view[r.reported["Alloy Name"].text]
        h = r.harmonized
        assert h["grain_size"].value == pytest.approx(float(row["GrainSize"]))
        assert h["hardness"].value == pytest.approx(float(row["HV"]))
        if row["YS"]:
            assert h["yield_strength"].value == pytest.approx(float(row["YS"]))
        else:
            assert h["yield_strength"].status == "not_reported"
        for e in tamu_fcc.ELEMENT_COLUMNS:
            assert h["composition"].value.get(e, 0.0) == pytest.approx(float(row[e]))


# --- Planted rows --------------------------------------------------------------------

def workbook(rows, sheet=tamu_fcc.SHEET, header=tamu_fcc.HEADER) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(list(header))
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


GOOD = ["BBA", "X01", 4, 8, 4, 4, 16, 12, 48, 4, 140.2, 3.8, 284.2, 34.3, 60, 950, 0.5, 23, 13]


def _row(**changes):
    row = list(GOOD)
    for col, value in changes.items():
        row[int(col[1:])] = value
    return row


def test_planted_values_are_kept_and_marked():
    rows = [
        GOOD,
        _row(c4="abc"),           # 1: a percentage that is not a number
        _row(c8=47),              # 2: percentages sum to 99
        _row(c12=None),           # 3: blank yield strength
        _row(c17="=1+1"),         # 4: a formula, not a value
        [None] * 19,              # 5: blank row
        GOOD + ["extra"],         # 6: an extra column
        _row(c17=-5),             # 7: negative grain size: converted as reported, not judged here
        _row(c17="12.5"),         # 8: a number stored as text
    ]
    result = tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook(rows)}))
    by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
    assert result.blank_rows == (5,)
    assert sorted(by_row) == [0, 1, 2, 3, 4, 6, 7, 8]

    def h(i, field):
        return by_row[i].harmonized[field]

    assert by_row[0].alloy == "Al4Co8Cr4Cu4Fe16Mn12Ni48V4"
    assert h(1, "composition").status == "not_convertible" and h(1, "composition").reason == "Cr: not a number: 'abc'"
    assert by_row[1].alloy is None and by_row[1].reported["Cr"].text == "abc"
    assert h(2, "composition").reason == "percentages sum to 99, not 100"
    assert h(3, "yield_strength").status == "not_reported"
    assert all(v.status == "not_convertible" for v in by_row[4].harmonized.values())
    assert by_row[4].reported["Grain Size(µm)"].text == "=1+1"
    assert by_row[6].reported["(column 20, no header)"].text == "extra"
    assert (h(7, "grain_size").status, h(7, "grain_size").value) == ("converted", -5.0)
    assert (h(8, "grain_size").status, h(8, "grain_size").value) == ("converted", 12.5)


def test_another_layout_is_refused():
    with pytest.raises(AdapterError, match="no sheet"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], sheet="Other")}))
    with pytest.raises(AdapterError, match="header"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], header=("a",) * 19)}))
    with pytest.raises(AdapterError, match="not a readable spreadsheet"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: b"not a spreadsheet"}))


def test_the_batch_grouping_unit_is_refused_until_the_owner_decides():
    with pytest.raises(AdapterError, match="decision 9"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD])}, grouping_unit="batch"))


def test_records_serialize_to_json(records):
    out = json.loads(json.dumps(records[0].to_json()))
    assert set(out["harmonized"]) == set(HARMONIZED_FIELDS)
    assert out["group"] == {"unit": "dataset", "key": "dataset:10.5281/zenodo.22798856", "reason": None}
```

### `tests/test_reference_counts_from_adapters.py`

```python
"""Step 4: the adapters' output reproduces the reference counts (PRD 10, 14.1a).

The filter below is a copy of the reference script's scope and rules
(`docs/reference/worked_example.py`), written here on the test side to check the
harmonization. It is not package code: eligibility is decided by code under the locked
plan in step 6, and these counts are not a rule.

The Texas A&M count ignores temperature: the source states no test temperature for its
own measurements (step 4 question 3), and how a room-temperature scope treats it is the
owner's step 6 decision."""
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

from hypocurate.sources import adapters
from source_helpers import sealed_from_disk

REPO = Path(__file__).resolve().parents[1]


def value(record, field):
    v = record.harmonized[field]
    return v.value if v.status in ("converted", "assigned") else None


def at_least_two_grain_sizes(records):
    sizes = defaultdict(set)
    for r in records:
        sizes[r.alloy].add(value(r, "grain_size"))
    return [r for r in records if len(sizes[r.alloy]) >= 2]


def mpea_reference_set(records):
    """Scope: microstructure FCC, test temperature 20–25 °C; grain size and yield strength
    present; alloys with at least two distinct grain sizes; grain size at least 0.1 µm."""
    scoped = [r for r in records if value(r, "microstructure") == "FCC"
              and value(r, "test_temperature") is not None and 20 <= value(r, "test_temperature") <= 25
              and value(r, "grain_size") is not None and value(r, "yield_strength") is not None]
    return [r for r in at_least_two_grain_sizes(scoped) if value(r, "grain_size") >= 0.1]


def tamu_reference_set(records):
    present = [r for r in records if value(r, "grain_size") is not None and value(r, "yield_strength") is not None]
    return at_least_two_grain_sizes(present)


@pytest.fixture(scope="module")
def mpea():
    return adapters.read(sealed_from_disk("mpea")).records


@pytest.fixture(scope="module")
def tamu():
    return adapters.read(sealed_from_disk("tamu_fcc")).records


def test_mpea_77_records_from_20_papers(mpea):
    chosen = mpea_reference_set(mpea)
    assert len(chosen) == 77
    assert len({r.group.key for r in chosen}) == 20


def test_mpea_rows_are_those_of_the_reference_script(mpea):
    """The same rows as the reference script run on the raw file with pandas."""
    d = pd.read_csv(REPO / "data/sources/mpea/MPEA_dataset.csv")
    d.columns = ['ref', 'formula', 'micro', 'proc', 'phase', 'gs', 'rho_exp', 'rho_calc', 'HV', 'test', 'T', 'YS',
                 'UTS', 'el', 'elp', 'E_exp', 'E_calc', 'O', 'N', 'Cwt', 'doi', 'year', 'title']

    def norm(f):
        comp = {}
        for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
            comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
        s = sum(comp.values())
        return ''.join(f"{e}{round(100 * v / s, 1):g}" for e, v in sorted(comp.items()))

    d['comp'] = d.formula.map(norm)
    scope = (d.micro == 'FCC') & d['T'].between(20, 25)
    s = d[scope & d.gs.notna() & d.YS.notna()].copy()
    g = s.groupby('comp').gs.nunique()
    s = s[s.comp.isin(g[g >= 2].index)]
    plan = s[s.gs >= 0.1]
    assert len(plan) == 77 and plan.doi.nunique() == 20
    assert [f"MPEA_dataset.csv:row:{i}" for i in plan.index] == [r.source_item_key for r in mpea_reference_set(mpea)]


def test_tamu_21_records_from_9_alloys(tamu):
    chosen = tamu_reference_set(tamu)
    assert len(chosen) == 21
    assert len({r.alloy for r in chosen}) == 9
    assert len({r.group.key for r in chosen}) == 1


def test_pooled_98_records_22_alloys(mpea, tamu):
    pooled = mpea_reference_set(mpea) + tamu_reference_set(tamu)
    assert len(pooled) == 98
    assert len({r.alloy for r in pooled}) == 22
    assert len({r.group.key for r in pooled}) == 21
```

### `tests/test_source_connection.py`

```python
"""Step 4: 'test connection and show sample records' (PRD 9.6), and the command line."""
import json

import pytest
from sqlalchemy import text

from hypocurate import cli
from hypocurate.sources import connection
from hypocurate.sources.record import HARMONIZED_FIELDS
from hypocurate.sources.versions import SOURCES, UnsealedVersion, register

TABLES = ("source", "source_version", "source_file", "record", "audit_log", "run", "hypothesis")


def counts(engine):
    with engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABLES}


@pytest.fixture
def registered(db):
    for key in SOURCES:
        register(db, key)
    return db


@pytest.mark.parametrize("key,total", [("mpea", 1545), ("tamu_fcc", 94), ("controlled_duplicates", 16)])
def test_it_returns_sample_records_in_the_common_format(registered, key, total):
    before = counts(registered)
    report = connection.test_connection(registered, key, n=3)
    assert counts(registered) == before
    assert report.source_key == key and report.records_read == total and report.blank_rows == 0
    assert len(report.sample) == 3
    assert [r.source_item_key.rsplit(":", 1)[1] for r in report.sample] == ["0", "1", "2"]
    assert all(set(r.harmonized) == set(HARMONIZED_FIELDS) for r in report.sample)
    assert all(r.version_fingerprint == report.fingerprint for r in report.sample)
    assert sum(report.status_counts.values()) == total * len(HARMONIZED_FIELDS)
    json.dumps(report.to_json())


def test_assigned_values_are_shown_with_their_citation(registered):
    report = connection.test_connection(registered, "tamu_fcc", n=1).to_json()
    test_type = report["sample"][0]["harmonized"]["test_type"]
    assert test_type["status"] == "assigned" and "Quasistatic tensile testing" in test_type["citation"]["quote"]
    assert report["status_counts"]["assigned"] == 94 * 2


def test_it_needs_a_sealed_version(db):
    with pytest.raises(UnsealedVersion, match="no sealed version"):
        connection.test_connection(db, "mpea")


def test_the_transaction_is_read_only(registered, monkeypatch):
    """A write slipped into the read would be refused by PostgreSQL."""
    original = connection.load_sealed_version

    def writing_loader(conn, vid):
        conn.execute(text("UPDATE source SET enabled = enabled"))
        return original(conn, vid)

    monkeypatch.setattr(connection, "load_sealed_version", writing_loader)
    with pytest.raises(Exception, match="read-only transaction"):
        connection.test_connection(registered, "mpea")


def test_the_command_line(db, migrated_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.delenv("HYPOCURATE_ENV", raising=False)
    assert cli.main(["sources", "register"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in out] == list(SOURCES)
    assert all("registered and sealed" in line for line in out)
    assert cli.main(["sources", "register", "mpea"]) == 0
    assert "already registered" in capsys.readouterr().out
    assert cli.main(["sources", "test", "tamu_fcc", "-n", "2"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["records_read"] == 94 and len(shown["sample"]) == 2
    assert shown["sample"][0]["harmonized"]["test_type"]["status"] == "assigned"
    assert cli.main(["sources", "register", "nope"]) == 1
    assert "unknown source" in capsys.readouterr().err
```

## 7. Image check and README

### `scripts/check_runtime_image.py`

```python
"""Check the contents of the deployed image (second-model review of step 2, finding 1).

Usage: python scripts/check_runtime_image.py <dir>
where <dir> is the image's /app copied out with `docker cp`. Run from the
repository (the test image in CI), because the answer markers come from the
step 1 tests, which are never in the deployed image.

The image must hold exactly the package, the frozen data and the runtime lock:
no tests/, no docs/, no answer file, no builder, no review document, and no
answer material in any file. Exit status 1 and one line per problem otherwise.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOP_LEVEL = {"hypocurate", "data", "requirements.lock"}
REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.json", "requirements.lock",
            # Step 3: Render's pre-deploy command migrates from inside the deployed image.
            "hypocurate/db/migrate.py", "hypocurate/db/migrations/env.py",
            "hypocurate/db/migrations/versions/0001_data_model.py",
            # Step 4: the sources are registered and read from inside the deployed image.
            "hypocurate/sources/versions.py", "hypocurate/sources/adapters/__init__.py",
            "data/sources/mpea/MPEA_dataset.csv", "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
            "data/controlled_duplicates/extract.csv"]
FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")


def _answer_markers():
    spec = importlib.util.spec_from_file_location("step1_tests", REPO / "tests/test_controlled_duplicates.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    row = {m.lower() for m in tests._row_specific_markers()}
    generic = {m.lower() for m in tests._generic_outcome_markers()}
    return row, generic, tests.FROZEN_SOURCE_FILES


def problems(root: Path) -> list[str]:
    root = Path(root)
    found = []
    top = {p.name for p in root.iterdir()}
    if top != TOP_LEVEL:
        found.append(f"top level is {sorted(top)}, expected {sorted(TOP_LEVEL)}")
    found += [f"missing {r}" for r in REQUIRED if not (root / r).is_file()]

    row, generic, frozen = _answer_markers()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        if FORBIDDEN_DIRS & set(parts if path.is_dir() else parts[:-1]):
            found.append(f"forbidden directory: {rel}")
            continue
        if not path.is_file():
            continue
        if FORBIDDEN_NAMES.match(path.name):
            found.append(f"forbidden file: {rel}")
        if rel in frozen:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        # Row-specific answers are forbidden everywhere; the outcome vocabulary only
        # under data/ (the package uses it from step 6), as in the step 1 tests.
        markers = row | generic if rel.startswith("data/") else row
        hits = sorted(m for m in markers if m in text)
        if hits:
            found.append(f"answer material in {rel}: {hits[:3]}")
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    found = problems(Path(argv[1]))
    for line in found:
        print(line)
    print("runtime image OK" if not found else f"{len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

### `README.md`

````markdown
# hypocurate

[![tests](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml/badge.svg)](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml)

HypoCurate takes a scientific hypothesis in words, searches registered data sources, and reports whether the data in the sources searched are sufficient, partly sufficient or insufficient to test it. The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md); the rules for working on the code are in [CLAUDE.md](CLAUDE.md).

## Status

Build step 4 of 12 (PRD Section 15): sources and harmonization. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), plus the three sources registered as sealed versions, one adapter per source and "test connection" (step 4). The access layer, the pipeline and the screens come in later steps.

## Set up secrets (once)

```
cp .env.example .env     # then fill in every value; .env is never committed
```

`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`.

## Start the system locally

```
docker compose up --build         # database, web (http://localhost:8000) and worker
```

`/health` needs no login; every other page asks for the shared password. Compose publishes the web service on 127.0.0.1 only, because locally it is plain HTTP. Each service gets only the variables it needs; the worker never sees the login password or the session secret.

In this Codespace, Docker has a leftover firewall rule that blocks traffic between containers. After every Codespace restart, run once:

```
sudo iptables-legacy -I DOCKER-USER -j ACCEPT
```

## Sessions and the login

- A session is a signed cookie holding only `{"signed_in": true}`. It lasts 12 hours. There is no server-side session record.
- **To revoke access, rotate `SESSION_SECRET` together with the password.** Changing the password alone does not end existing sessions. On Render: set a new `HYPOCURATE_PASSWORD` and a new `SESSION_SECRET` on the web service, then redeploy. Every existing session ends.
- Logout clears the cookie in that browser only. A copied cookie keeps working until it expires or the secret is rotated. This is a known limitation of cookie-only sessions, stated in `tests/test_login.py`.
- Failed logins are counted. Every attempt is still checked against the password, and the correct password is never refused by the count, so nobody can lock the owner out. After 5 wrong attempts within 15 minutes, further wrong attempts receive 429 instead of 401 until the window passes. That is all the count does.
- The protection against guessing is a random password of at least 24 characters, generated as above. The configuration enforces the length, not the randomness.

## Run the test suite

The suite needs PostgreSQL; the database tests fail (they never skip) when it is not reachable.

In the same image as the deployed services (this is what GitHub runs at every push):

```
docker compose run --rm test
```

Or in the Codespace's virtual environment:

```
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-dev.lock
.venv/bin/pip install --no-deps -e .
docker compose up -d db
set -a; . ./.env; set +a
.venv/bin/pytest
```

## Dependencies

Direct dependencies are listed in `pyproject.toml`. The exact versions, with hashes, are in `requirements.lock` (runtime) and `requirements-dev.lock` (runtime plus test tools). To change a dependency: edit `pyproject.toml`, then regenerate both locks with pip-tools:

```
.venv/bin/pip install pip-tools
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe -o requirements.lock pyproject.toml
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe --extra dev -o requirements-dev.lock pyproject.toml
```

## Deployment

`render.yaml` describes the Render web service, worker and PostgreSQL database. Render deploys a commit on `main` only after its GitHub checks pass (`autoDeployTrigger: checksPass`).

## Database migrations

The tables are created and changed only by Alembic migrations in `hypocurate/db/migrations/`. The tables and the rules the database enforces are described in `hypocurate/db/models.py`.

```
python -m hypocurate.db.migrate upgrade              # to the latest revision
python -m hypocurate.db.migrate current              # the database's revision
python -m hypocurate.db.migrate downgrade <revision> # drops tables and their data
```

- **On deploy.** Both Render services run `python -m hypocurate.db.migrate upgrade` as their pre-deploy command. It runs after the image is built and before the new version starts. An advisory lock makes the second service wait, after which it finds the schema at the latest revision. `/health` shows the database's revision and whether it is the latest. Locally, `docker compose up` runs the same command in a one-off `migrate` service before web and worker start.
- **If a migration fails.** The whole upgrade is one transaction, so PostgreSQL undoes all of it: no table and no revision change. The command exits non-zero, Render fails the deploy, and the previous version keeps running. Every migration must therefore stay inside that transaction (no `CREATE INDEX CONCURRENTLY`, no `autocommit_block`); a test checks this.
- **Every migration keeps working with the previous release's code** (add first, remove in a later release). Reverting a merge on `main` then deploys the old code safely on the newer schema.
- **Rolling back:**
  1. Preferred: a new migration that undoes the change, deployed the normal way.
  2. Code only: revert the merge on `main`.
  3. Schema: the owner runs `python -m hypocurate.db.migrate downgrade <revision> --confirm-data-loss` in the Render Shell of a service. **This drops tables and their data**; in production it refuses without the flag. Before it, check the backups: Render's point-in-time recovery reaches back 3 days on the Hobby workspace and restores into a *new* database, which costs money.
- **What the database enforces, and its limits.**
  - Triggers and CHECK constraints refuse, among others: editing a locked plan; changing a frozen dataset; freezing a primary set that leaves out an eligible record; updating or deleting a record; extracting before the rules lock; any curation once a run has ended; adding files to a sealed source version; and a verdict on a run that is not sufficient. A refusal raises an error starting `hypocurate:`.
  - **Locking protocol (all write paths, from step 4 on).** The lock order is version, then run, then the run's child rows.
    - Every transaction that will write to a run or its child rows first calls `SELECT hc_write_lock(p_run => <run id>)`.
    - Every transaction that will change a hypothesis version's chosen sources, submit it or dispatch it first calls `SELECT hc_write_lock(p_version => <version id>)`.
    - Paths that follow the protocol cannot deadlock with each other.
    - The triggers also lock the run (or version) before checking its state, which makes the checks race-free. They do not by themselves establish the lock order: an UPDATE of a child row locks that row before its trigger asks for the run lock. A path that skips the protocol can deadlock.
    - **On a reported deadlock (SQLSTATE `40P01`) or serialization failure (`40001`), retry the whole transaction.** PostgreSQL aborts one transaction and writes nothing from it.
    - A transaction holding a run's lock makes every other writer to that run wait, so keep such transactions short.
  - **After a run ends.** On a completed run only the commentary, the Commentator's stage and model calls, and artifacts may still be written; on a failed run only the audit log.
  - **Validity checks.** The CHECKs on `analysis_result` are necessary conditions on the stored counts, not the full validity rules of PRD 5.7. Those, and the agreement of the verdict with the pooled result, are computed and tested in step 7.
  - The triggers stop the application and ordinary edits. The database owner can still drop a trigger, so they are not tamper-proof; the fingerprints are the cross-check.
- **Tests never touch the database at `DATABASE_URL`.** They create scratch databases (`hypocurate_t_…`, from a template migrated once per session) and drop them afterwards. The database user must be allowed to create databases (the local and CI containers' user is).

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

## Sources and adapters

The three sources (`mpea`, `tamu_fcc`, `controlled_duplicates`) are defined in `hypocurate/sources/versions.py`. Registering one stores the data files its adapter reads as a `source_version` and seals it. The files digest and identity are computed as the database computes them, and the database checks them again.

```
hypocurate sources register              # all three; registering again changes nothing
hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common record format, as JSON
```

- Registration reads only paths inside `data/` (checked after resolving `..` and links), and refuses a file whose SHA-256 differs from `data/manifest.json`, or a source already registered with different interpretation settings.
- Registration writes no run or hypothesis version, so `hc_write_lock` does not apply. It locks the source row first (`SELECT … FOR UPDATE`) and runs in `run_transaction` (`hypocurate/db/retry.py`), which retries the whole transaction on `40P01` and `40001`.
- An adapter reads a **sealed** version (`load_sealed_version` re-checks every file's bytes against the seal) and returns one record per data row in the format of `hypocurate/sources/record.py`. Every value is kept as reported, with its unit. Every harmonized value has a status: `converted`, `not_reported`, `not_convertible` (with the reason) or `assigned` (with the passage of the source's documentation that states it). Adapters never decide eligibility and never drop or correct a record.
- "Test connection" runs in a read-only transaction.
- The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
- Not yet run on the live database: registering there is a later step and needs the owner.
````

## 8. Test output

```
$ .venv/bin/pytest -v   (the 70 new tests below; the whole suite's last line at the end)
tests/test_adapter_extract.py::test_sixteen_records_with_origin_keys PASSED [  0%]
tests/test_adapter_extract.py::test_each_record_equals_its_mpea_row_except_the_changed_columns PASSED [  0%]
tests/test_adapter_extract.py::test_a_renamed_formula_gives_the_same_alloy PASSED [  0%]
tests/test_adapter_extract.py::test_paper_unknown_is_marked_never_invented PASSED [  0%]
tests/test_adapter_extract.py::test_a_constructed_doi_is_its_own_paper PASSED [  1%]
tests/test_adapter_mpea.py::test_one_record_per_row_none_dropped PASSED  [  1%]
tests/test_adapter_mpea.py::test_every_value_is_kept_as_reported_with_its_unit PASSED [  1%]
tests/test_adapter_mpea.py::test_every_record_has_the_common_fields_with_their_units PASSED [  1%]
tests/test_adapter_mpea.py::test_numbers_are_converted_unchanged PASSED  [  2%]
tests/test_adapter_mpea.py::test_grain_size_counts PASSED                [  2%]
tests/test_adapter_mpea.py::test_nothing_in_the_frozen_file_is_unconvertible PASSED [  2%]
tests/test_adapter_mpea.py::test_test_type_codes PASSED                  [  2%]
tests/test_adapter_mpea.py::test_no_value_is_assigned PASSED             [  2%]
tests/test_adapter_mpea.py::test_alloy_names_follow_the_reference_naming PASSED [  3%]
tests/test_adapter_mpea.py::test_paper_identity_is_the_doi PASSED        [  3%]
tests/test_adapter_mpea.py::test_the_record_format_has_no_decision_fields PASSED [  3%]
tests/test_adapter_mpea.py::test_planted_values_are_kept_and_marked PASSED [  3%]
tests/test_adapter_mpea.py::test_a_file_in_another_layout_is_refused PASSED [  4%]
tests/test_adapter_mpea.py::test_another_grouping_unit_is_refused PASSED [  4%]
tests/test_adapter_mpea.py::test_altered_bytes_are_refused_before_parsing PASSED [  4%]
tests/test_adapter_mpea.py::test_text_is_kept_exactly_as_reported PASSED [  4%]
tests/test_adapter_tamu.py::test_one_record_per_sample_none_dropped PASSED [  4%]
tests/test_adapter_tamu.py::test_every_value_is_kept_as_reported PASSED  [  5%]
tests/test_adapter_tamu.py::test_the_sample_without_yield_strength_is_kept PASSED [  5%]
tests/test_adapter_tamu.py::test_one_group_the_dataset PASSED            [  5%]
tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage PASSED [  5%]
tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable PASSED [  6%]
tests/test_adapter_tamu.py::test_temperature_is_not_reported PASSED      [  6%]
tests/test_adapter_tamu.py::test_composition_in_atomic_percent PASSED    [  6%]
tests/test_adapter_tamu.py::test_agrees_with_the_authors_csv_view PASSED [  6%]
tests/test_adapter_tamu.py::test_planted_values_are_kept_and_marked PASSED [  6%]
tests/test_adapter_tamu.py::test_another_layout_is_refused PASSED        [  7%]
tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides PASSED [  7%]
tests/test_adapter_tamu.py::test_records_serialize_to_json PASSED        [  7%]
tests/test_reference_counts_from_adapters.py::test_mpea_77_records_from_20_papers PASSED [ 84%]
tests/test_reference_counts_from_adapters.py::test_mpea_rows_are_those_of_the_reference_script PASSED [ 84%]
tests/test_reference_counts_from_adapters.py::test_tamu_21_records_from_9_alloys PASSED [ 85%]
tests/test_reference_counts_from_adapters.py::test_pooled_98_records_22_alloys PASSED [ 85%]
tests/test_source_connection.py::test_it_returns_sample_records_in_the_common_format[mpea-1545] PASSED [ 93%]
tests/test_source_connection.py::test_it_returns_sample_records_in_the_common_format[tamu_fcc-94] PASSED [ 93%]
tests/test_source_connection.py::test_it_returns_sample_records_in_the_common_format[controlled_duplicates-16] PASSED [ 93%]
tests/test_source_connection.py::test_assigned_values_are_shown_with_their_citation PASSED [ 93%]
tests/test_source_connection.py::test_it_needs_a_sealed_version PASSED   [ 93%]
tests/test_source_connection.py::test_the_transaction_is_read_only PASSED [ 94%]
tests/test_source_connection.py::test_the_command_line PASSED            [ 94%]
tests/test_source_versions.py::test_files_digest_equals_the_databases[files0] PASSED [ 94%]
tests/test_source_versions.py::test_files_digest_equals_the_databases[files1] PASSED [ 94%]
tests/test_source_versions.py::test_files_digest_equals_the_databases[files2] PASSED [ 95%]
tests/test_source_versions.py::test_files_digest_equals_the_databases[files3] PASSED [ 95%]
tests/test_source_versions.py::test_version_identity_equals_the_databases PASSED [ 95%]
tests/test_source_versions.py::test_an_unsafe_stored_path_is_refused_before_the_database PASSED [ 95%]
tests/test_source_versions.py::test_registering_seals_every_source PASSED [ 95%]
tests/test_source_versions.py::test_registering_again_adds_nothing PASSED [ 96%]
tests/test_source_versions.py::test_concurrent_registration_waits_on_the_source_lock_and_leaves_one_version PASSED [ 96%]
tests/test_source_versions.py::test_the_source_lock_serializes_a_new_version_of_an_existing_source PASSED [ 96%]
tests/test_source_versions.py::test_two_registrations_at_once_leave_one_version PASSED [ 96%]
tests/test_source_versions.py::test_a_changed_file_is_refused_and_nothing_is_written PASSED [ 97%]
tests/test_source_versions.py::test_changed_interpretation_settings_are_refused PASSED [ 97%]
tests/test_source_versions.py::test_an_unknown_source_is_refused PASSED  [ 97%]
tests/test_source_versions.py::test_paths_must_stay_inside_their_directory PASSED [ 97%]
tests/test_source_versions.py::test_a_definition_pointing_outside_data_is_refused PASSED [ 97%]
tests/test_source_versions.py::test_a_file_missing_from_the_manifest_is_refused PASSED [ 98%]
tests/test_source_versions.py::test_an_unsealed_version_is_refused PASSED [ 98%]
tests/test_source_versions.py::test_a_loaded_version_reads_like_the_files_on_disk PASSED [ 98%]
tests/test_source_versions.py::test_changed_settings_on_a_loaded_version_are_refused PASSED [ 98%]
tests/test_write_retry.py::test_a_retryable_failure_reruns_the_whole_transaction[40P01] PASSED [ 99%]
tests/test_write_retry.py::test_a_retryable_failure_reruns_the_whole_transaction[40001] PASSED [ 99%]
tests/test_write_retry.py::test_other_errors_are_not_retried PASSED      [ 99%]
tests/test_write_retry.py::test_it_gives_up_after_the_last_attempt PASSED [ 99%]
tests/test_write_retry.py::test_a_real_deadlock_is_retried_to_completion PASSED [100%]
======================== 445 passed in 62.09s (0:01:02) ========================
```
