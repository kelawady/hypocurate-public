# Build step 4 — summary for review

Date: 2026-10-05. Branch: `step-04-adapters`. **Status: first review received (ChatGPT, 2026-10-05: five findings and one test weakness, all accepted by the owner); fixes done, suite passing; awaiting the re-check.** PRD Section 15, step 4: "Sources and harmonization. The CSV adapter, both sources, the common record format, and source versions."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`. It describes the state **after** the fixes for the first review. The findings and their fixes are listed in "Review findings and fixes"; the review text is in `docs/reviews/step04_review_chatgpt.md`, and the fix diffs are in `docs/reviews/step04_fix_packet.md`.

The owner approved the plan on 2026-10-05 after three questions (below), with one addition: a report on test temperature and test type in the MPEA reference records (section "Owner's addition").

**Not built, as instructed:** the access layer, any agent, eligibility or duplicate decisions, statistics, screens. No migration, no `render.yaml` change, no workflow change. Records are **not stored**: a `record` row needs an extraction run after its rules lock (step 3 rule), so storing waits for steps 6 and 8. The sources are **not registered on the live database**: that needs the owner (open item 1).

## What was built

| Path | What it is |
|---|---|
| `hypocurate/db/retry.py` | `run_transaction(engine, fn)`: runs `fn(conn)` in one transaction; on SQLSTATE `40P01` or `40001` reruns the whole transaction (at most 5 attempts); any other error is raised unchanged. |
| `hypocurate/sources/versions.py` | `files_digest` and `version_identity` (Python copies of `hc_files_digest` and `hc_version_identity`); the three source definitions (`SOURCES`); `safe_path_within`; `register`; `load_sealed_version`; `latest_sealed_version_id`. |
| `hypocurate/sources/record.py` | The common record format: `CommonRecord`, `Value`, `Reported`, `Group`, `Citation`, `AdapterResult`, `AdapterError`. |
| `hypocurate/sources/normalize.py` | Number parsing; formula → atomic % (numerically safe); percentage columns → atomic %; the display label for an alloy; the paper grouping key from a DOI. |
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
  - **The group key is derived from the DOI** (review finding 1; `normalize.doi_group_key`): surrounding whitespace trimmed; one `https://doi.org/`, `http://dx.doi.org/` or `doi:` wrapper removed (case-insensitive); ASCII A–Z case-folded, nothing else (no Unicode normalization). Key `doi:<normalized>`. `paper_doi` and the reported text keep the DOI exactly as in the file.
  - **Effect on the frozen files:** 8 of MPEA's 265 DOI strings change form (the leading space, and 7 with capital letters such as `10.4028/www.scientific.net/MSF.849.76`), but 265 DOI strings still give 265 keys: no group merges or splits (tested). The 77 reference records keep their 20 papers (tested, by key and by DOI as reported). None of the extract's DOIs change.
  - In the frozen MPEA file the DOI and `IDENTIFIER: Reference ID` are one-to-one (265 each, tested).
  - A blank DOI gives `group.key = None` with the reason "no DOI in the source: paper unknown". The Reference ID is never used in its place, and no group is invented. This applies to extract rows 5–6, where both are blank.
  - Extract rows 9–10 have a blank Reference ID and a constructed DOI, which is their group.
  - The DOI is kept exactly as reported. One MPEA DOI has a leading space (`" 10.1038/ncomms10602"`): `paper_doi` keeps it, and its group key is `doi:10.1038/ncomms10602`.
- **Texas A&M: the dataset**, one group `dataset:10.5281/zenodo.22798856` (grouping unit `dataset`).
  - `paper_reference` is the dataset citation; `paper_doi` is empty, because the record has no per-record paper (PRD 10).
  - The batch (`Iteration`: CBA 23, CBC 21, BBA 18, CBB 15, BBB 9, BBC 8) is kept as reported.
  - **The grouping unit is an open decision for the owner (PRD 17, decision 9).** The adapter refuses any other unit, so a version sealed with grouping unit `batch` fails until the owner decides and the adapter is changed.

## The common record format

One `CommonRecord` per data row, mirroring the `record` table: `source_key`, `version_fingerprint`, `source_item_key` (origin key), `item_index`, `kind`, `alloy` (a display label), `paper_reference`, `paper_doi`, `group`, `harmonized`, `reported`. **It has no field for eligibility, flags, duplicates or survivors, and states no alloy identity** (tested).

- **`reported`:** every column, keyed by its header exactly as in the file. Each entry holds the cell text exactly as in the file (`""` when blank; for the spreadsheet, numbers in their shortest exact form) and the unit the header states.
- **`harmonized`:** the same 17 fields for every source, each with a fixed unit (`HARMONIZED_FIELDS`).
  - Each value has a status: `converted`, `not_reported` (blank, or "the source has no column for this field"), `not_convertible` (with the reason; the text stays in `reported`) or `assigned`.
  - `assigned` requires a `Citation` (document, location, exact quote), and a `Reported` entry cannot carry one. Both are enforced by the dataclasses and tested.
- **Origin keys:** `<file>:row:<n>`, n the 0-based data row, the same for both layouts.
  - MPEA's numbering is the one step 1 used.
  - The Texas A&M sheet is named `GS_MasterTable_Iterations ` (with a trailing space); it is matched verbatim and left out of the key.
- **Units:** MPEA's headers state µm, MPa, HV and °C; the Texas A&M headers state µm, MPa, HV, °C, h and % reduction. Values are converted unchanged.
- **Alloy: full-precision composition; the label is for display only** (review finding 2). Every record carries the composition in atomic % at full precision. `alloy` is a display label in the reference script's style (elements in alphabetical order, each rounded to 0.1 at.%). **Equal labels do not mean the same alloy**: Fe50.01Ni49.99 and Fe50.04Ni49.96 both read `Fe50Ni50`, and the adapter reports their compositions as different (tested). When two compositions count as the same alloy is a plan and domain-profile setting, defined in step 6 with a tolerance the owner approves. The reference numbers (98 records, 22 alloys) were computed with 0.1 at.% rounding, which stays the current default pending that approval. `CoCrFeMnNi` and `Co1 Cr1 Fe1 Mn1 Ni1` give the same composition (tested).
- **Composition parsing is numerically safe** (review finding 5): every amount must be finite; the calculation scales by the largest amount before summing (`math.fsum`), so large finite amounts do not overflow; an amount that underflows to zero, a ratio too extreme to represent, or any non-finite result is `not_convertible` with the reason. Percentage columns must be finite too.
- **Strict CSV parsing** (review finding 3, with the owner's addition): a quoting error (unterminated or malformed quote) or a row with the wrong number of fields refuses the **whole file** with an `AdapterError` naming the file, the line(s) and the reason, for example `MPEA_dataset.csv: line 4: expected 23 fields, found 21; the file is refused`, or `MPEA_dataset.csv: line 3: the record starting on this line cannot be parsed (unexpected end of data, detected at line 5); the file is refused`. No partial extraction is returned. A legitimate quoted field may span lines. The frozen MPEA file and the extract parse under strict mode (no multi-line fields). **Limitation:** a stray quote that happens to leave exactly 23 fields in every row is valid CSV and cannot be detected by syntax alone.
- **Spreadsheet formulas** (review finding 4): a formula cell makes only the field it feeds `not_convertible` (a formula in any element column: the composition); every other value, the cited assignments and the deliberately not-reported temperature are unchanged. The frozen spreadsheet has no formulas.
- **What is never done:** no rescaling of percentages that do not sum to 100 (marked instead), no row dropped, no physical judgment (a negative grain size is converted as reported; flagging it is step 6's job).
  - An entirely blank row is listed in `blank_rows`, not made a record. The frozen files have none.

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

These match the reference numbers in CLAUDE.md (98 records, 22 alloys, 21 groups). Alloys are counted here by the 0.1 at.% label, as the reference script did (the current default pending the owner's approval, finding 2); groups by the derived key (finding 1).

## Review findings and fixes (first review, ChatGPT, 2026-10-05)

The review's verdict: registration, sealing, digests, locking, retries and paths are sound; five findings and one test weakness. The owner accepted all six, with instructions for each (below), and approved the fix plan with one addition (finding 3: the error names the file, the line and the reason). One commit per item:

1. **Paper groups used the raw DOI text, so formatting differences split one paper** (`30b95c0`). The group key is now derived from the DOI (trim; remove a URL or `doi:` wrapper; ASCII case-fold only); `paper_doi` and the reported text are unchanged. The tests that required raw grouping are replaced. Frozen data: 8 DOI strings change form, no group merges or splits (265 → 265); the 77 reference records keep their 20 papers.
2. **Rounded alloy labels were promoted into scientific identity** (`8a58a58`). The label is for display only; every statement that equal labels mean the same alloy is removed from code, README and this summary. The same-alloy rule is a step 6 plan setting with an owner-approved tolerance; the reference numbers used 0.1 at.% rounding, the current default pending approval. New test: Fe50.01Ni49.99 and Fe50.04Ni49.96 share a label, not a composition.
3. **Malformed CSV quoting could silently absorb later records** (`028617e`). Strict parsing; a quoting error or a wrong field count refuses the whole file with an `AdapterError` naming the file, line(s) and reason (owner's addition). The frozen MPEA file and the extract parse under strict mode, so no relaxation was needed. Tested: unterminated quotes (at the end, and swallowing later rows), a malformed quote, wrong field counts with the line, a legitimate multi-line field.
4. **One spreadsheet formula made unrelated fields unavailable** (`f0efe89`). A formula now affects only the field it feeds; the existing test is corrected, not extended.
5. **Formula normalization could emit non-finite compositions** (`d2de2d8`). Finite amounts only, scaling by the largest amount before an `fsum`, refusal of unrepresentable ratios and of any non-finite result; tests in `tests/test_normalize.py`.
6. **Test weakness: the spreadsheet "reported values preserved" test used the production formatter** (`f569d2b`). A new test compares cells with strings written out by hand from the file's XML.

README updated in `4aad3a2`.

The review's other checks found no problem: ordinary unit conversions, assigned values on ordinary rows, registration and sealing, path containment, answer isolation and scope. The reviewer could not retrieve the pinned paper, so the citations were checked against the packet, not the publication; the fetched files' SHA-256 are listed above.

## Tests (467, all passing; 92 new in step 4; no test from an earlier step changed)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data tests/test_login.py tests/test_login_throttle.py tests/test_data_model.py tests/test_concurrency.py tests/test_migrations.py` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_write_retry.py` | 5 | Both SQLSTATEs rerun the whole transaction (the first attempt's insert is rolled back); other errors are not retried; it gives up after the last attempt; a real deadlock between two transactions is retried and both complete. |
| `tests/test_source_versions.py` | 20 | Digest and identity equal the database's. Unsafe stored paths are refused before the database. All three sources registered and sealed, with stored bytes equal to disk and settings copied; registering again adds nothing. A concurrent registration **waits on the source lock** and leaves one version (new source, and existing source with a new version). Two registrations at once leave one version. A changed file is refused and nothing is written; changed interpretation settings are refused. Paths stay inside their directory. Unsealed versions are refused. A loaded version reads exactly like the files on disk. Changed settings on a loaded version are refused. |
| `tests/test_adapter_mpea.py` | 32 | 1,545 records, one per row, origin keys in order. Every reported text equals the file's cell. Common fields and units. Numbers converted unchanged. 237 grain sizes. Nothing unconvertible in the frozen file. Test-type codes. No value assigned. Display labels follow the reference naming. Paper identity is the DOI, group key derived (expected keys written out independently; 265 groups, one-to-one with the Reference ID; 8 DOI strings change form, no group merges). The format has no decision fields. **Planted rows:** a non-numeric grain size, an unknown element, a blank formula, a negative grain size, a temperature with text, an unknown test type, a blank DOI, a blank line, NaN, a zero amount; each record kept and marked. Another layout or encoding is refused, another grouping unit is refused, altered bytes are refused before parsing, text is kept exactly as reported. **Finding 1:** seven spellings of one DOI give one group, with the DOI kept as reported; ASCII-only case folding. **Finding 2:** compositions differing below the rounding step share a label but not a composition. **Finding 3:** unterminated quote at the end, unterminated quote swallowing later rows (start and detection lines), malformed quote, wrong field counts (24 and 21) with the line, a legitimate multi-line field, a multi-line record's line range; each refusal message starts with the file and line. |
| `tests/test_normalize.py` (new) | 5 | **Finding 5:** a coefficient too large to represent; large finite coefficients normalized without overflow; a ratio too extreme or an amount too small to represent; every converted composition finite and summing to 100; non-finite percentages refused. |
| `tests/test_adapter_extract.py` | 5 | 16 records. Each equals its MPEA source row except where a listed column changed (the answer file is read on the test side only). A renamed formula gives the same composition. Unknown paper is marked, never invented. A constructed DOI is its own paper. |
| `tests/test_adapter_tamu.py` | 14 | 94 records, every value as reported, **and a few cells of BBA01, BBA02 and BBA09 checked against strings written out by hand from the file's XML** (test weakness), BBA09's yield strength `not_reported` and the record kept. One group (the dataset), batches kept. Assigned values carry their passage. Assigned and reported stay distinguishable. Temperature not reported. Composition in at.% with 82 distinct compositions and 82 labels. Agrees with the authors' `inputs.csv`. **Planted rows:** a non-numeric percentage, a sum of 99, a blank yield strength, a formula in the grain-size SD (**finding 4:** only that field is affected; every other value, the assignments and the not-reported temperature equal those of the ordinary row), a formula in an element column (the composition only), a blank row, an extra column, a negative grain size, a number stored as text. Another layout is refused; the `batch` grouping unit is refused until the owner decides. |
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

**After the review fixes**, each new test was run against the code from before its fix, in a scratch copy:

| Restored | Result |
|---|---|
| The MPEA adapter before fixes 1 and 3 | 16 of 32 MPEA tests fail |
| The raw DOI as group key (fix 1 only) | 9 tests fail (MPEA and reference counts) |
| The permissive CSV reader (fix 3 only) | 3 tests fail; the wrong-field-count tests still pass, because the field-count check refuses those files independently |
| The Texas A&M adapter before fix 4 | the corrected planted test fails |
| `normalize.py` before fix 5 | all 5 normalization tests fail |
| A formatter regression (floats printed with two decimals) | the new hand-written-strings test fails; the old test, which used the adapter's own formatter, still passes, which is the weakness the review named |

### Tests removed or replaced (none weakened)

Review round:
- **Finding 1, raw grouping protected the bug:**
  - `test_paper_identity_is_the_doi` expected the group key `doi:<raw cell>`; it now expects the derived key, written out independently (`"doi:" + row.strip().lower()`, valid because the frozen DOIs have no wrapper), and also checks that 8 DOI strings change form while 265 groups stay 265.
  - `test_text_is_kept_exactly_as_reported` expected the key `doi: 10.1038/ncomms10602` (with the space); it now expects `doi:10.1038/ncomms10602` and still checks that the DOI and its reported text keep the space.
- **Finding 2:** `test_alloy_names_follow_the_reference_naming` is renamed `test_display_labels_follow_the_reference_naming` (assertion unchanged: the label is the reference naming, for display). `test_a_renamed_formula_gives_the_same_alloy` is renamed `test_a_renamed_formula_gives_the_same_composition` and no longer asserts equal labels; it compares the full compositions, as before.
- **Finding 3:** in `test_planted_values_are_kept_and_marked`, the planted row with an extra field (formerly expected kept, every value `not_convertible`) is replaced by an ordinary row, because such a file is now refused as a whole; that refusal is tested in `test_a_wrong_field_count_refuses_the_file_and_names_the_line`. The header-refusal assertion now also checks `line 1`.
- **Finding 4:** in the Texas A&M `test_planted_values_are_kept_and_marked`, the formula row expected all 17 fields `not_convertible`; it now has its formula in the grain-size SD and expects only that field affected (corrected, as the review asked).

### Suite results

```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, `docker compose up -d db`)
467 passed in 62.52s
$ docker compose run --rm test           (the test image, rebuilt)
467 passed in 63.37s
```

GitHub Actions, commit `4aad3a2` (after the review fixes): success; "Run the suite in the test image": 467 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37257783194

First round, commit `cb0f814`: success, 445 passed, runtime image OK. https://github.com/kelawady/hypocurate/actions/runs/37256382423

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
6. **PRD 10 (alloy naming)** (review finding 2): the adapter gives the full-precision composition in atomic % and a label for display only. When two compositions count as the same alloy is a plan and domain-profile setting, defined in step 6 with a tolerance the owner approves. The reference numbers were computed with 0.1 at.% rounding (the reference script's rule), the current default pending that approval.
7. **Step 3 locking protocol:** `hc_write_lock` covers runs and hypothesis versions. Source registration locks the source row instead (owner, question 1).
8. **PRD 7 (`source`):** the controlled duplicate extract is registered as a source with `enabled = false`. No database rule prevents choosing a disabled source.
9. **PRD 10 (paper identity)** (review finding 1): a paper's group key is derived from its DOI by conservative normalization (trim, remove a URL or `doi:` wrapper, ASCII case-fold); the DOI as reported is kept.
10. **PRD 10 (malformed files)** (review finding 3): an adapter refuses a file it cannot parse strictly, naming the file, line and reason; it never returns a partial extraction.

## Open items

1. **Registering on the live database (owner).** Not done in this step. When the owner agrees: `hypocurate sources register` in the Render Shell of one service. No `render.yaml` change is needed, and no setting depends on it.
2. **Texas A&M test temperature (owner; gates PRD 14.1a in step 6).** See "Consequence" above. If the band is assigned on an accepted source, step 6's scope rule must accept the room-temperature band, with a test that the 21 Texas A&M records stay eligible under the reference plan. The same question applies to the microstructure if the scope requires single-phase FCC.
3. **Texas A&M grouping unit (owner, PRD 17 decision 9).** One group now; the batch is kept as reported. A `batch` version is refused by the adapter until decided.
4. **Step 5 (access layer):** adapters read source bytes from the sealed version in the database, not from disk. The approved input list should name the sealed source versions, and `tests/` and `docs/reviews/` stay outside it, as before.
5. **Step 6:**
   - a guard so that the controlled extract (constructed data) cannot enter a real analysis;
   - permitted test types (MPEA row 139, compression, is among the 77);
   - **the same-alloy rule** (review finding 2): a plan and domain-profile setting with a tolerance the owner approves, applied to the full-precision composition, before any model grouping or duplicate matching uses alloys. The 0.1 at.% rounding of the reference numbers is the current default pending approval. The display label is never used for it;
   - duplicate matching uses the paper's derived group key, the composition under that rule, grain size, value and test conditions.
6. **Step 6/8:** store the records (the format mirrors the `record` table), from inside an extraction run after the rules lock, through `hc_write_lock(p_run => …)` and `run_transaction`.
7. **Carried from step 3, unchanged:** step 7 and step 9 requirements; the lock-contention note; a transaction writing to more than one run needs an ordering rule.

## Questions for the reviewer

1. Is locking the source row an adequate substitute for `hc_write_lock` on the registration path, given that the database also locks the version row on file insert and at sealing?
2. Is the status vocabulary (`converted`, `not_reported`, `not_convertible`, `assigned` with citation) enough to keep assigned values distinguishable from reported ones once records are stored as JSON in step 6?
3. Is anything in the adapters still a decision rather than a conversion (for example listing blank rows instead of making records)?
4. Is the DOI normalization conservative enough (one wrapper removed, ASCII case-fold only), and is refusing a whole file on one malformed row the right trade-off?
