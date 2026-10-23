# Sprint 2 evidence-assembly pilot: final report

Prepared 23 October 2026 for the owner and the review-week reviewer. The specification is PRD v1.2 (`docs/sprint2/HypoCurate_Sprint2_PRD_2026-10-22_v1.2.pdf`). The day-by-day record is `docs/sprint2/daily/2026-10-22.md` and `docs/sprint2/daily/2026-10-23.md` (sections 1 to 20). The merge packet, after two ChatGPT review rounds, is `docs/reviews/sprint2_pilot_merge_packet.md`. The H2 section (section 7) was added last, after the owner's manual fetch of 19 papers.

## 1. Outcome in one paragraph

The pilot is **merged** (`ded0e2f`, tag `pilot-merge-1`) and **live** on migration 0010.
- **The evidence:** 10 papers were extracted (Claude Sonnet 5.5, prompt v4), reconciled and reviewed by the owner. The evidence was frozen (S2, events hash e13de3b7…) and sealed as the "extracted (pilot)" source. That source and all the evidence rows are loaded into the live database (pilot version fingerprint abe38724…, 40 snapshot hashes re-checked on load).
- **The three H1 runs on the live site:**
  - MPEA only, 424.05 ± 62.22, which reproduces the Sprint 1 anchor;
  - extracted only under "use what is available": insufficient, no test;
  - augmented pool: 77 records, 419.73 ± 62.31.

  An independent calculation agrees with the augmented pool's estimate.
- **What the extracted source added:** of 48 extracted observations, 5 met the acceptance matrix. Four are re-reports of MPEA records, counted once. One is a new record that enters the pool.
- **Why most did not:** the largest reason is yield strengths shown only in figures, a result about the sources searched, not a loss.

## 2. Requirements against their acceptance conditions

| R | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Migration 0010, additive, tested downgrade | **Met** | 18 additive tables; `tests/test_migrations_step0010.py` (33 test functions); up-down-up restores the full 0009 catalog; downgrade refused while 0010 holds data; the six reference dumps byte-identical to main at the release code; the Sprint 1 fixed-plan run reproduces 97/22/20/74, 424.9 ± 64.4 |
| R2 | Reach for every paper behind MPEA's FCC grain-size records | **Met** | 28 papers and 107 records. Open copy listed: 9 papers (31 records). Downloaded by program: 3 (11). Fetched by hand: 8 (28). Parsed: 10 (32). Every lookup and fetch is in `search_log`. Figures are stated with the source configuration (`pilot_access_method`) |
| R3 | Paper choice (owner) | **Met** | the owner's choices of 2026-10-22/23 (daily report 2026-10-22) |
| R4 | The Extractor interface with a second implementation | **Met** | `pipeline/extraction/interface.py`; the fixture extractor; provenance checks; S0 frozen with its hash in the same transaction |
| R5 | The Reconciler | **Met, with a recorded deviation** | It runs per document before the runs, not "in the run" (`pilot_reconciler_placement`, matching Design 3.9). 119 mappings with quotes and code's checks; owner review sheets v1 and v2 |
| R6 | Evidence states and the acceptance matrix | **Met** | `pipeline/evidence.py`; `tests/test_evidence.py`, including PRD R6's condition (one disputed link removes exactly that record and keeps it in the gap count); a mutation dropping the freeze invariant is caught |
| R7 | Annotation template and scoring script | **Met, with stated limits** | `hypocurate scoring tables` regenerates both P6 tables (S0 and S2, same rows and columns, per paper and pooled) from the database and the annotation file alone (`pilot_s2_scoring`). The scorer matches on R-identity, applies the register's tolerances, and has the five self-checks. **Limits:** one extractor method (the Opus second method was never run) and one annotator (AI-assisted), so the per-method and per-annotator splits each have one value |
| R8 | The owner's first-pass annotation | **Met, with a recorded deviation** | `annotation_KE_v1`, 25 rows on 4 papers. It was **AI-assisted (Codex, for KE)**: not a blind human key, and its minutes are not owner time (`pilot_annotation_ke_v1`). Discrepancies are listed in the scorer's pairs |
| R9 | The three H1 conditions on the live site | **Met** | live runs 9, 10, 11; `tests/pilot_independent.py` agrees on runs 9 and 11 (to better than 1e-12) |
| R10 | Auditor findings and the repair trace | **Met** | 40 findings, each with a consequence (`auditor_finding`). Repair 1 (Wu et al. 2014, published version): attempted, gap not closed. Repair 2 (Otto et al. 2013, the primary source for cited observation 124): its grain sizes (4.4 and 155 µm) carry page provenance naming document 12. Both fetches are in `search_log` with author and time |
| R11 | H2 evidence inventory | **Met, with the scope the owner set** | Page `/pilot/h2` and workbook. Status "inventory; analysis deferred to a versioned protocol". Selection reproduces the PRD's anchor (131 records, 20 papers). **The extraction and reconciliation of the 19 fetched papers are reported locally** (section 7): 22 records recovered with provenance, grain-size type and state, and the causes counted. The live page shows no paper read (post-pilot item 9) |
| R12 | Workbook provenance columns | **Met** | five columns and the "Extracted evidence by state" sheet on pilot runs; Sprint 1 workbooks unchanged |
| R13 | Pipeline view | **Cut** by the owner (post-pilot list item 8) | — |
| R14 | The results-note generator | **Replaced** by the owner's cut | The note's tables come from the scorer and saved queries (`documents costs`, `documents reach`, `documents h2-inventory`); the owner writes the prose |
| R15 | Costs | **Met** | `documents costs`, from `model_call`, `stage_result` and `owner_time_log` (section 6) |

## 3. The PRD's acceptance criteria (Section 6)

| # | Criterion | Status |
|---|---|---|
| 1 | Reproducible scoring | **Met.** One command (`hypocurate scoring tables`) regenerates the S0 and S2 tables from the database and the annotation file, with the register's tolerances and rules, on each paper's standing S0. |
| 2 | Traceable values and links | **Met.** Each of the 5 accepted records has provenance for its grain size, its yield strength and its link, resolving to a page with a table row, sentence or passage. The workbook shows them. |
| 3 | Correct re-report handling | **Met.** On live, Sprint 1's checks flagged the two actamat.2018.12.012 re-reports as possible duplicates, each counted once with MPEA surviving. New observations: 1, reported separately (pending adjudication in the note). |
| 4 | The acceptance matrix holds | **Met.** The freeze invariant, its negative tests, its re-check on bundle load, and a mutation test. |
| 5 | The repair trace exists | **Met, with one limit.** It is in `search_log` and in the database (provenance names document 12). The workbook shows the repaired observations by state on its "Extracted evidence by state" sheet; they are not in a run's records because their yield strengths are figure-only. |
| 6 | Validity preserved | **Met.** The extracted-only run under "use what is available" ended insufficient with no coefficient, no uncertainty and no verdict. The validity checks were not waived. |
| 7 | H2 inventoried honestly | **Met.** The causes are separated (not obtained, not parsed, read with no observation, no grain size stated) and stated against the source configuration; the grain-size type of every recovered record is recorded (D27's two types, with the wording as written); no "absent"; no analysis. |
| 8 | Sprint 1 intact | **Met.** The whole suite is green (2,600 locally; GitHub suite step 43 min 25 s at the merge). The dumps are byte-identical at the release code. Every safeguard touch has a test (packet sections 9–13). |
| 9 | The package is complete | **Not fully.** See section 8 for what is open. |

## 4. P6, recovery metrics: S0 and S2 side by side

**Generated by** `hypocurate scoring tables` (full tables: `docs/sprint2/p6_tables_2026-10-23.md` and `.csv`).
- Both snapshots have the same rows and the same columns, on each paper's standing S0.
- The annotation is `annotation_KE_v1` (AI-assisted, Codex for KE; 4 papers).
- The method is the pilot Extractor, Claude Sonnet 5.5, prompt v4.
- S2 is S0 less the observations disputed at the freeze, with grain-size and yield-strength corrections applied (`pilot_s2_scoring`).

**Pooled:**

| Table | Snapshot | Denominator | Matched | Recall or recovery | Own predictions | Strict precision | Matched to the compilation | Not in the compilation (pending) |
|---|---|---|---|---|---|---|---|---|
| vs annotation | **S0** | 25 | 23 | **0.920** | 25 | **0.920** | — | — |
| vs annotation | **S2** | 25 | 12 | **0.480** | 12 | **1.000** | — | — |
| vs compilation | **S0** | 10 (15 set aside as figure-only or range) | 4 | **0.400** | 45 | 0.311 | 4 | 31 |
| vs compilation | **S2** | 10 (15 set aside) | 2 | **0.200** | 22 | 0.273 | 2 | 16 |

**Reading:**
- **What S2 drops:** every observation the owner's review disputed. Many of those matched the annotation in S0: all ten Wu et al. observations matched as "figure only" claims, but their links were rejected, because a figure-only value cannot be linked.
- **So recall falls and precision rises:** S2 recall against the annotation falls from 0.92 to 0.48, and its precision rises to 1.000. This is what "corrected performance" measures under this definition.
- **The definition is the builder's and is registered.** The owner may change it.

The per-paper rows are in the generated file.

## 5. P7, the H1 runs on the live site

| Live run | Condition | Result |
|---|---|---|
| 8 | V1: MPEA only, reference before the bundle | 76 / 13 / 19 / 62, k = 424.05442308188793 ± 62.21603775763127, p ≈ 1.1e-6; sufficient, supported |
| 9 | **H1 "MPEA only"** (V3, after the bundle) | identical to run 8 |
| 10 | **H1 "extracted only", use what is available** (V4) | insufficient, evidence level 1, missing evidence ("extracted_pilot: 5 records found") |
| 11 | **H1 "augmented pool"** (V5) | **77 / 13 / 20 / 63, k = 419.73474127880974 ± 62.309086460668425**, p ≈ 9.7e-7; sufficient, supported |

- **The independent check:** on run 11 it gives 419.7347412788101 ± 62.309086460669214, which agrees.
- **What the extracted source contributed:**
  - observation 121 (FeCoNiCr alloy A, 289.7 µm, 165 MPa, actamat.2015.08.076) enters the pool;
  - two re-reports were caught by Sprint 1's duplicate flags;
  - the other accepted records are out by scope: no test temperature stated (actamat.2018.12.012), or no accepted phase mapping (actamat.2015.08.076 P1, P2).
- **A reasoning error in the Analyst's text on run 11:** "the extracted source added no usable records". In fact it added one: 77 against 76. It misread the per-source line. The text is labelled as not verified, and code's statement is correct. No check catches such a misreading.

**The extracted evidence by state** (48 observations on the 10 standing S0s):

| State | Count | Detail |
|---|---|---|
| Accepted | 5 | 4 re-reports, 1 new |
| Proposed | 17 | figure-only yield strength 10; grain size flagged ambiguous 5; a range 1; figure-only grain size 1 |
| Disputed | 26 | a finding disputes it 8; a link or mapping disputed 18 |

## 6. P9, costs and time (from stored rows)

- **Document model calls** (development database, all iterations: prompts v1–v4, two repairs):
  - Extractor: 67 calls, $4.90.
  - Reconciler: 10 calls, $0.78.
  - Total **$5.68** over 77 calls, 3 failed (no cost).
  - Per paper: daily report 2026-10-23 section 13.
- **H2 document model calls** (19 papers, v4, H2 v1): extractor $2.52, Reconciler $1.23, total **$3.75** of the declared $8. Per paper: section 7.
- **All document model calls in the pilot: $9.44.**
- **Live runs:** run 8 $0.048; run 10 $0.055; run 11 $0.051; run 9 about $0.05 (unconfirmed when read). About **$0.20**.
- **Owner time:**
  - The time log: review sheet v2, 1 min; the repair fetches, 1 + 1 min.
  - Sheet v1: 3 min (the owner's stated total).
  - **AI time, separate:** the AI-assisted annotation (Codex), and the AI reviewer of sheet v1 (ChatGPT, 10.7 min).
- **Wall time:** stage times come from `stage_result`. Document call times come from the development database: on live, loaded calls carry the load's time (post-pilot item 2).
- **CI time:** the GitHub suite step was 43 min 25 s at the merge, against the 60-minute job limit.

## 7. P7 / R11, the H2 inventory (local, for the note)

**H2:** grain refinement in BCC high-entropy alloys at 800 °C and above; tension and compression both recorded. The qualifying grain size is either type, recorded per record (D27).
- **Status:** inventory; analysis deferred to a versioned protocol. No analysis ran.
- **Scope:** for the pilot the inventory is local, for the note (owner, 2026-10-23). The live `/pilot/h2` page shows the counts by cause with no paper read; an additive H2 bundle is post-pilot item 9.
- **Generated by:** `hypocurate documents h2-inventory --out docs/sprint2/h2_inventory_2026-10-23.xlsx`.

**The corpus** (`pilot_h2_budget`; owner, 2026-10-23): the 20 papers behind the compilation's 131 BCC records at ≥ 800 °C (none has a grain size).
- The owner fetched **19** by hand: 7 had an open copy listed but refused to the program (access method `none`), and 12 came through institutional access (`institutional_credential`).
- The paper not obtained under the configured sources is `10.1007/s40195-019-00921-3` (3 records).
- **Processing:** all 19 were parsed (Docling; two have no tables) and the row-split rule applied (one paper changed). Each was extracted on prompt v4 with the specification H2 v1 (Claude Sonnet 5.5), and reconciled against MPEA.

**Counts by cause:**

| Cause | Count |
|---|---|
| Compilation records lacking a grain size | 131 of 131 |
| Papers not obtained under the configured sources (no open copy listed) | 1 |
| Papers not parsed | 0 |
| **Papers read, no observation returned (no grain size with a yield strength found)** | **10** |
| Observations read with no grain size stated as a number | 26 |
| Observations read with no yield strength stated as a number | 0 |

**Records recovered** (grain size and yield strength both stated as numbers, with provenance):
- **22, all from two papers:** 10.1007/s11837-014-1066-0 (12) and 10.1016/j.intermet.2011.01.004 (10).
- **All are as-processed grain sizes in compression tests;** none is a grain size at or after the test temperature.
- **All 22 are in state `proposed`.** The owner has not reviewed them, and none is accepted.
- **The compilation lacks their grain sizes:** the Reconciler proposes 22 same-observation mappings, matching them to compilation records whose yield strengths at ≥ 800 °C carry no grain size. These papers state as-processed grain sizes for those records.

**Observations by state and grain-size type:**

| State | As-processed | At or after the test temperature |
|---|---|---|
| Proposed | 43 | 5 |

Every observation keeps the Extractor's own wording of its type beside the type code read.

**Per paper, with cost:**

| Paper | Access | Compilation records | Observations | Recovered (as-processed / at or after) | Same-observation proposals | Extractor $ | Reconciler $ |
|---|---|---|---|---|---|---|---|
| 10.1016/j.actamat.2019.06.032 | none | 30 | 0 | 0 (0 / 0) | 0 | 0.145 | 0.101 |
| 10.3390/e21010015 | none | 17 | 0 | 0 (0 / 0) | 0 | 0.120 | 0.067 |
| 10.1007/s11837-014-1066-0 | institutional_credential | 10 | 12 | 12 (12 / 0) | 12 | 0.260 | 0.106 |
| 10.1016/j.intermet.2011.01.004 | institutional_credential | 10 | 13 | 10 (10 / 0) | 10 | 0.204 | 0.080 |
| 10.1007/s11661-017-4386-1 | none | 9 | 0 | 0 (0 / 0) | 0 | 0.104 | 0.055 |
| 10.1016/j.actamat.2019.06.006 | none | 7 | 1 | 0 (0 / 0) | 0 | 0.193 | 0.108 |
| 10.1016/j.intermet.2015.03.013 | institutional_credential | 6 | 0 | 0 (0 / 0) | 0 | 0.084 | 0.044 |
| 10.1016/j.intermet.2017.01.007 | institutional_credential | 6 | 0 | 0 (0 / 0) | 0 | 0.061 | 0.033 |
| 10.1007/s11661-005-0218-9 | institutional_credential | 4 | 0 | 0 (0 / 0) | 0 | 0.079 | 0.047 |
| 10.1007/s12598-019-01310-6 | institutional_credential | 4 | 2 | 0 (0 / 0) | 2 | 0.093 | 0.048 |
| 10.1016/j.jallcom.2015.08.224 | institutional_credential | 4 | 8 | 0 (0 / 0) | 8 | 0.271 | 0.128 |
| 10.1016/j.msea.2012.12.018 | institutional_credential | 4 | 2 | 0 (0 / 0) | 2 | 0.220 | 0.078 |
| 10.1007/s10853-012-6260-2 | institutional_credential | 3 | 5 | 0 (0 / 0) | 3 | 0.152 | 0.067 |
| 10.1007/s40195-019-00921-3 | not obtained | 3 | 0 | 0 (0 / 0) | 0 | 0.000 | 0.000 |
| 10.1016/j.jallcom.2015.11.050 | none | 3 | 3 | 0 (0 / 0) | 3 | 0.134 | 0.073 |
| 10.1016/j.jallcom.2019.05.322 | none | 3 | 0 | 0 (0 / 0) | 0 | 0.157 | 0.066 |
| 10.1016/j.matdes.2015.05.019 | institutional_credential | 3 | 0 | 0 (0 / 0) | 0 | 0.071 | 0.036 |
| 10.1016/j.jallcom.2016.10.014 | institutional_credential | 2 | 0 | 0 (0 / 0) | 0 | 0.090 | 0.049 |
| 10.1016/j.matlet.2014.11.162 | institutional_credential | 2 | 2 | 0 (0 / 0) | 2 | 0.071 | 0.037 |
| 10.1007/s10853-019-03567-9 | none | 1 | 0 | 0 (0 / 0) | 0 | 0.011 | 0.012 |
| **Total** | 7 none, 12 institutional, 1 not obtained | **131** | **48** | **22 (22 / 0)** | 42 | **2.522** | **1.232** |

**Cost:** all H2 model calls cost **$3.75**, within the declared $8 budget (extractor $2.52, Reconciler $1.23). No stop rule fired.

**Read honestly:**
- In the sources searched, 10 of the 19 papers read report yield strengths at ≥ 800 °C with no grain size we could pair with them. 26 further observations have no grain size stated as a number.
- Where the papers do state one (2 papers, 22 records), it is the as-processed grain size.
- This is not a statement that grain sizes "do not exist": it is what these sources, as fetched and parsed, state.

## 8. Open items

1. **The results note prose** (P10), the owner's.
2. **The full second-model review of the whole branch** (review week; the owner's merge condition (d)).
3. **The post-pilot list** (`docs/sprint2/post_pilot_list.md`):
   - S1 lineage test;
   - import time against execution time;
   - an end-to-end disagreeing re-report;
   - the error reason on failed calls (needs a `model_call` column);
   - the survivor default for digitized compilation values;
   - cumulative per-document cost enforcement;
   - R13;
   - the additive H2 bundle.

## 9. Release artifacts (merge review C5)

| | |
|---|---|
| Merge commit | `ded0e2f7a8f66e8b1052f42ebe868f06926df9aa` (tag `pilot-merge-1`); parents `eb78ec0` (tag `pre-pilot-merge`) and `1888f3f`; tree `9beda799…`, identical to the tested commit |
| Whole suite | 2,600 passed at the tree (local, 50 min 40 s); GitHub run 39993817271 green (suite step 43 min 25 s) |
| Reference dumps at the release code, byte-identical to main | `fixed_plan` 5c5b27e9…, `narrower` b172fd48…, `partly_original` 31f30687…, `planner_bcc` d9f86be9…, `planner_fcc` 83cc064c…, `reference` 4797b3c1… (raw files in `~/hc-work/sprint2/refdump/release/`) |
| Pilot source version | fingerprint abe38724eb9e3a741359e21b4e967d09be0d1c52e561fb9dd4fef99ab1ff53b1; S2 events hash e13de3b7…; bundle SHA-256 b104cf31… |
| Live backups | B1 (0009, SHA-256 dd241ba3…), B2 (0010 before the bundle, SHA-256 3a0cb409…), in `~/hc-work/`. Revert after the bundle is by restore (packet section 7) |
| Register | 217 entries, 48 of them the pilot's |
