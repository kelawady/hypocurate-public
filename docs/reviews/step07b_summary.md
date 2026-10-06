# Build step 7b — summary for review

> **Update (2026-10-06): the owner decided to merge step 7b**, on the second model's "safe to merge" (`docs/reviews/step07b_review_chatgpt.md`, verbatim), and approved the new sensitivity set's reference numbers as reported. Two small changes and a recorded deferral came first (section "Second-model review and the owner's decisions"). The set is now displayed **"without the group with the largest share of slope information"**; the internal key `without_most_influential_paper` and rule `most_influential_paper` are unchanged. Where this summary says "the most influential paper" below, read that display name.

Date: 2026-10-06. Branch: `step-07b-group-and-influence` (from `main` at `0f31698`). **Status: built (code at `c5f74f0`), the whole suite passes (1,186 locally, 1,186 in the test image; GitHub Actions success, runtime image OK: https://github.com/kelawady/hypocurate/actions/runs/37474428306); pushed; not merged** (owner's instruction: "full suite, summary, review packet, push, and stop. Do not merge."). A small step between 7 and 8, applying two owner decisions of 2026-10-06. **Both touch safeguards** (an eligibility rule, the freeze check's invariants, the sensitivity sets), so they need the second model's review before any merge (CLAUDE.md, "How we work" item 5). The review packet is `docs/reviews/step07b_review_packet.md`; the checklist is `docs/reviews/checklist.md`.

**Not changed:** no migration (below), no change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose or dependencies. No agent, no model call, no screen. No PRD document is changed; corrections are listed at the end.

## Second-model review and the owner's decisions (2026-10-06)

**The review** (ChatGPT, `docs/reviews/step07b_review_chatgpt.md`, verbatim): no serious defect or merge blocker; rule 5's position, invariant (7)'s independence, the new set's determinism, outcome blindness and single change, the shared information calculation, and the answer-file changes confirmed. Three non-blocking points. **"Safe to merge."** The reviewer states it did not rerun the database suite, the reference comparison or the 1,186-test suite.

**The owner's decisions:**
1. **Merge step 7b** ("This is my decision, on ChatGPT's 'safe to merge'"), after two small changes on the branch, the full suite and a green run.
2. **The new set's reference numbers are approved as reported:** 89 records, 22 alloys, 19 groups, 66 residual df, k = 393.5 ± 90.5 (one standard error), p ≈ 1.9e-4. They are now in `APPROVED` in `test_reference_numbers.py` (checked by `test_each_sensitivity_set` and against statsmodels by `test_every_reference_result_matches_the_reference_implementation`), and in the register (`reference_numbers`, field `sensitivity`; note in `most_influential_paper_set`).
3. **Review point 2, the display:** the set is displayed "without the group with the largest share of slope information", stating whether the removed group is a paper, a dataset or a batch; the internal key stays. `eligibility.INFLUENCE_DISPLAY_NAME`; `most_influential` now returns `unit` ('paper', 'dataset' or 'batch', the group key's prefix) and `display`, e.g. "without the group with the largest share of slope information (the removed group is a paper)", recorded in the Inclusion stage result and the freeze record. The register says that this is **the largest share of within-alloy grain-size contrast, not necessarily the group whose removal changes the slope most** (`most_influential_paper_set` reworded, earlier wording in its history; `SENSITIVITY_CHANGES` says the same). On the reference data the removed group is a paper.
4. **Review point 3, the test:** `test_the_sensitivity_handling_is_the_answer_files` now derives the expected removed records independently of the result being checked. `expected_removed(run)` computes I_g in plain Python from the primary members' conditions (no outcome), with the reference plan's grouping and same-alloy rule, and no package code; it requires a clear maximum. A new test, `test_the_set_without_the_largest_share_removes_the_independently_derived_records`, checks the whole set against it. Mutations m07 (smallest share) and m08 (most records) run against this file alone: 4 and 7 failures.
5. **Review point 1, deferred (not done now):** an analysis-specific simulation seed and about 10,000 simulations, before the final evaluation. In the backlog below and in the notes of `calibration_simulation`, `results_pure_function` and `most_influential_paper_set`.

**Tests added for these changes:** `test_the_display_states_whether_the_removed_group_is_a_paper_a_dataset_or_a_batch` (3 cases), `test_the_set_without_the_largest_share_removes_the_independently_derived_records`; the new set's case is added to the two parametrized reference tests by its entry in `APPROVED`. **Changed:** `test_the_change_is_named_and_in_the_default_plan` (the new description); `test_the_set_without_the_most_influential_paper_as_reported` renamed `…_as_approved` (it reads `APPROVED`); the "none" branch of `test_the_sensitivity_handling_is_the_answer_files` (above).

## Backlog (deferred; PRD Section 18)

1. **An analysis-specific simulation seed** (review point 1). Today the seed is SHA-256 of the run's freeze fingerprint, the analysis and the method. So adding an unrelated set (as here) changes every analysis's draws, although their data and settings are identical. Derive it from a fingerprint of the analysis's own stable records and design, the simulation settings and the calibration method; keep the run fingerprint for provenance. The set's name alone is not enough.
2. **About 10,000 simulations** per world. At an 8% rejection rate, 2,000 give a 95% Monte Carlo margin of about ±1.2 points, about ±0.5 with 10,000. With 2,000, the before/after table in this summary is consistent with simulation noise but does not prove noise is the only explanation.
Both before the final evaluation (owner, 2026-10-06).

## The owner's decisions in the brief (2026-10-06)

From the brief:
1. **Records without a paper reference are decided at inclusion.** Such a record is stored and shown but is not eligible for the primary set, with its own recorded reason. The statistics never receive one; their existing refusal stays as a backstop, and a test shows it is no longer reached in normal runs. The open register entry `records_without_group` is resolved. No group is ever invented.
2. **A new sensitivity set, "without the most influential paper":** the primary set minus every record of the paper holding the largest share of slope information. The paper is chosen by code from grain sizes and alloys only, never from outcome values, with a stable tie-break from source evidence. It differs from the primary set in exactly this one respect, is descriptive only, and never changes the verdict.
3. **The minimum of 10 informative papers stays a count; final for sprint 1** (recorded in `fixed_minimums`).
4. Every setting from one named place, in the register in the same merge; results identical under permuted record ids and order; reference numbers recomputed and reported plainly.

From planning (one question at a time):
- **Q1, the rule's place:** rule 5, `group_unknown`, after `missing_value` (4) and before `scope_not_confirmed`. The answer file's rows 5–6 change (two cells each; below).
- **Q2, the freeze:** yes, a seventh invariant: the freeze refuses a primary set holding a record without a group.
- **Q3, the tie-break:** each tied paper's earliest record under (the plan's survivor source order, the lowest row in the source file, the stable identity).

At approval, two additions to the report: the simulated figures before and after, side by side, for the pooled set and MPEA alone under both calibrations; and the removed paper's reference, records and alloys beside the new set's numbers. Both are in section "Reference numbers".

## Migration: none

`run_record.rule` is free text (CHECK `length(rule) > 0`); `analysis_set.key` and `plan.sensitivity_analysis_keys` have a format check only (`^[a-z0-9_]+$`); migration 0004's triggers name no sensitivity key. The new codes are in the Python vocabularies (`access/vocabulary.py`) and the register (`code_vocabularies`).

## 1. Records without a group (rule 5, `group_unknown`)

**What a "group" is here.** `eligibility.group` (unchanged, now through `group_in`): a source grouped by paper gives `paper:<hash of the DOI>`, or none when the record carries no DOI; a source grouped by batch gives the batch, or none; a source grouped by dataset always has its group. So a Texas A&M record (grouped by dataset) never lacks one; an MPEA or extract record without a DOI does.

**The order** (`eligibility.decide`, register `eligibility_rule_order`):

| # | Rule | |
|---|---|---|
| 1 | `model_recalled` | |
| 2 | `invalid_value` | |
| 3 | `out_of_scope` | |
| 4 | `missing_value` | |
| **5** | **`group_unknown`** | **new** |
| 6 | `scope_not_confirmed` | was 5 |
| 7 | `excluded_by_rule` | was 6 |
| 8 | identity (`identity_unresolved`, `conflict_unresolved`, `duplicate_counted_once`) | was 7 |
| 9 | `single_grain_size` | was 8 |
| 10 | `in_scope` | was 9 |

**Why there:**
- after 1–4, so that a record out of scope or missing a value keeps that more basic reason;
- **before identity**, so that a record without a group is never chosen as a survivor and never pushes out its grouped twin (the measurement would be lost; tested with a plan whose source order prefers the ungrouped record);
- before the grain-size count, so that alloys are counted on records that can be analysed;
- before the scope and exclusion rules that sensitivity sets relax, so that the reason is the same in every set.

**Per set:** judged under each set's own grouping (`has_group(rec, st)`), by the same function the statistics use. Only `six_batches_as_groups` changes a grouping: a Texas A&M record without a batch would be `group_unknown` there only. No reference record lacks a batch.

**The freeze (owner, Q2):** `primary_set_problems` gains invariant (7), "records without a group", computed with `group_in` and the plan's grouping, **not** through rule 5's `has_group`, so switching off the rule does not switch off the check (mutation m06). The freeze refuses (`invariant_broken`, logged). Its signature gains a required keyword `grouping`.

**The backstop:** `analysis.RecordsWithoutGroup` is unchanged (pooled refuses; a descriptive analysis is reported as not analysed). `test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one` still reaches it directly; the new `test_the_statistics_backstop_is_not_reached_in_a_normal_run` shows that a marked run with the extract (rows 5–6 have no DOI) analyses every set, `not_analysed` is empty, and no `records_without_group` refusal is logged.

**Effect on the controlled extract (answer file rows 5–6).** The extract record (DOI, year, title blanked) was "counted once" in primary and counted separately in `possible_duplicates_separate`. Now it is `group_unknown` in every set; its MPEA twin still enters. The answer file (`truth.csv`, regenerated by its builder; the extract itself is unchanged, `8e11979a…`) changes in two cells per row and in the survivor reason and explanation:

| Column | Before | After |
|---|---|---|
| `primary_analysis` | counted once | not eligible: no group (paper reference missing) |
| `sensitivity_analysis` | both counted separately | none |
| `survivor_reason` | rule 1: only the MPEA record carries the original paper reference (DOI) | the same; this record is not eligible in any case (no group: the paper reference is missing) |
| `explanation` | … Flagged as a possible duplicate, kept, not removed. | the same, plus: without a paper reference it has no group …; no group is invented (owner, 2026-10-06) |

The pinned fingerprint changes from `e6e859cd…` to `0503f2b8…`.

**A consequence on the extract run:** `possible_duplicates_separate` now equals primary there (its only possible duplicates with an eligible twin were rows 5–6). Counting possible duplicates separately is still exercised where both records have a group (`test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule`, with the extract grouped by dataset; and the pipeline test in `test_mixed_groups.py`, which uses a Texas A&M workbook).

## 2. The set "without the most influential paper"

**Key** `without_most_influential_paper` (`eligibility.INFLUENCE_KEY`), in the default and reference plans as the ninth sensitivity set (`profile.SENSITIVITY_ANALYSES`). **Rule** for the removed records in that set: `most_influential_paper` (`eligibility.INFLUENCE_RULE`).

**How the paper is chosen** (`eligibility.most_influential`, called by Inclusion and by the freeze):
1. On the primary set's members, I_g per group (the primary grouping): the group's sum of squared within-alloy deviations of the transformed grain size, by **`statistics.slope_information`**. That is the same function `statistics.design` now uses for the effective number of papers and the largest share (one place; `test_the_design_uses_the_same_slope_information`). Alloys with two or more distinct transformed grain sizes; identity order; stable centring.
2. Inputs: stable identity, alloy (the plan's same-alloy rule), group, grain size. **No outcome value**: Inclusion's access object (`record_conditions`) carries none (the step 6 planted-value test), and the test `test_the_choice_uses_no_outcome_value` plants outcome values in the records and shows they are not read.
3. The largest share; shares within `statistics.RELATIVE_ZERO` (1e-10) of the largest are tied.
4. A tie is broken by each tied paper's earliest record under `influence_tie_key`: the plan's survivor source order, then the lowest row in the source file, then the stable identity (source-version fingerprint, origin key, item index). Never a database id or an order.
5. Without any slope information (possible only with grain sizes equal after the transformation) nothing is removed, reason `no_slope_information`, and the set equals primary.

**Exactly one change.** The set is the primary set's decisions with the chosen paper's members set to `most_influential_paper`: no rule is applied again. In particular, an alloy left with one grain size is **not** re-decided as `single_grain_size`; the fit's own alloy rule reports it as "not used in this fit", as in every set (mutation m13 adds such a cascade and is caught). `test_reference_sets._check_one_change` checks, on the reference run and the extract run, that the differing records are exactly the primary members of one group.

**Where the choice is recorded:** the Inclusion stage result and the freeze record carry `most_influential`: the group key (a hash), its share, the tied groups, the removed record ids, and their records and alloys counts. The ids are informational (like the existing "differences from primary"); the freeze fingerprint covers the set by stable identity.

**Descriptive only.** Analysed by the same code as every set; its result has no label and no verdict, and the run's decision equals the decision computed from the pooled result alone (`test_the_set_without_the_most_influential_paper`). No multiplicity adjustment.

## Reference numbers

**Plainly: no approved number changed.** Recomputed on the reference run (both sources, reference plan, fixed minimums) and compared with the same run on `main` (`0f31698`). For every analysis that existed before (pooled, both per-source, the eight earlier sensitivity sets), counts, informative papers, effective number, largest share, k, standard error, p-value, df, label and inference reason are **bit-identical** (exact equality, not within a tolerance). The decision is identical. `tests/test_reference_numbers.py` passes unchanged for every approved value.

**What did change, and why:** the plan gains a ninth sensitivity set, so the plan's fingerprint changes. That changes the freeze fingerprint (`3ec87f58…` → `52207f25…`), and with it the calibration seeds (SHA-256 of fingerprint, analysis, method). So the simulated figures are new draws. Neither is a reference number.

**Simulated figures, before → after** (2,000 simulations each; 95% exact intervals; z is the difference over its standard error for two independent shares):

| Analysis | Calibration | Quantity | Before (`main`) | After (branch) | Difference |
|---|---|---|---|---|---|
| Pooled | fixed (60 / 40 MPa) | false-positive share | 7.85% [6.71, 9.12] | 7.25% [6.15, 8.48] | −0.60 pts (z −0.72) |
| Pooled | fixed | detection rate | 100.00% [99.82, 100.00] | 100.00% [99.82, 100.00] | 0 |
| Pooled | estimated (method III) | false-positive share | 7.55% [6.43, 8.80] | 8.85% [7.64, 10.18] | +1.30 pts (z +1.50) |
| Pooled | estimated | detection rate | 97.20% [96.38, 97.88] | 97.75% [97.00, 98.35] | +0.55 pts (z +1.11) |
| MPEA alone | fixed | false-positive share | 8.30% [7.13, 9.60] | 9.95% [8.67, 11.35] | +1.65 pts (z +1.81) |
| MPEA alone | fixed | detection rate | 100.00% [99.82, 100.00] | 100.00% [99.82, 100.00] | 0 |
| MPEA alone | estimated | false-positive share | 8.05% [6.89, 9.33] | 8.00% [6.85, 9.28] | −0.05 pts (z −0.06) |
| MPEA alone | estimated | detection rate | 96.10% [95.16, 96.91] | 95.95% [94.99, 96.77] | −0.15 pts (z −0.24) |

"MPEA alone" is the reference run's per-source analysis for MPEA. The estimated noise itself (scatter and shift) comes from the frozen residuals, which are unchanged; only the random draws differ.

All differences are within simulation noise: the largest is 1.65 points (z = 1.81, MPEA alone, fixed calibration, no-effect share), and every flag is unchanged ("over-confident").

**The new set on the reference data:**

**The removed paper:** DOI `10.1007/s11661-019-05231-y`, reference as stored: "Effect of Annealing Temperature on Microstructure and Mechanical Properties of a Severe Cold-Rolled FeCoCrNiMn High-Entropy Alloy". **8 records, 1 alloy** (equiatomic CoCrFeMnNi, which other papers also measure, so the alloy stays in the set). Its share of slope information is 38.67%: it is the pooled result's "largest paper share", and a clear maximum (no tie; the tie-break was not used). An MPEA paper.

| | Pooled (approved) | Without the most influential paper |
|---|---|---|
| Records / alloys / groups / residual df | 97 / 22 / 20 / 74 | 89 / 22 / 19 / 66 (none "not used in this fit") |
| k (MPa·µm^½) | 424.9 | **393.5** |
| One standard error (cluster-robust, by group; not a confidence interval) | 64.4 | **90.5** |
| p (approximate, nominal, one-sided cluster-robust p-value under the locked method) | 1.3e-6 | **1.9e-4** |
| Informative papers | 20 | **19** (all) |
| Effective number of papers (a concentration diagnostic, not a number of independent papers) | 3.94 | **3.24** |
| Largest single paper's share | 38.7% | **52.1%** |
| t degrees of freedom | 19 | **18** |
| Calibration, fixed: false-positive share; detection | 7.25%; 100% | 7.50% [6.38, 8.74]; 99.95% |
| Calibration, estimated: false-positive share; detection | 8.85%; 97.75% | 7.90% [6.76, 9.17]; 87.40% |

Full precision: k = 393.50438134761, SE = 90.487111236234, p = 1.9348509448671e-4, effective 3.2411963217867, largest share 0.52100731612193. Both validity checks pass and the minimums are met. Like every sensitivity result, it is descriptive and has no verdict. Read with the same caution as the pooled result: removing the paper leaves the slope information still concentrated (another paper now holds 52.1%), and the calibration is "over-confident" under both methods.

The values are checked against the independent implementations (`test_the_set_without_the_most_influential_paper`: the removed paper chosen by test-side pandas, k, SE and p by the 60-digit decimal sandwich at relative 1e-9, the effective number and share by test-side pandas). They are pinned as reported (`test_the_set_without_the_most_influential_paper_as_reported`), not as approved reference numbers.

## Tests

**New: 29 tests** (1,186 in all, was 1,157). The whole suite passes: locally 1,186 passed (355 s), in the rebuilt test image 1,186 passed (384 s), on GitHub Actions 1,186 passed (run 37474428306).

| File | New tests | What they cover |
|---|---|---|
| `test_eligibility.py` | 10 | `group_unknown`: stored with its own rule in every set; its place (6 cases: model-recalled, out of scope and missing value come first; scope not confirmed and the menu exclusion come after); never a survivor (a plan whose source order prefers the ungrouped record); judged under each set's grouping; alloys counted on grouped records |
| `test_freeze_invariants.py` | 3 | Invariant (7) on the checker; end to end with rule 5 switched off and a plan counting possible duplicates both (the extract's rows 5–6 would enter): the freeze refuses and logs; a Texas A&M record (dataset grouping) is not "without a group" |
| `test_analysis_stage.py` | 1 | The backstop is not reached in a normal run (above) |
| `test_influential_paper.py` (new) | 13 | `slope_information` against an independent computation; `design` uses it; the set is primary minus the top paper; exactly one change (no cascade); only primary members count; ties: lowest row whatever the ids or order (3 id sets × 3 orders), source order before row, the numerical zero decides ties; no slope information (exactly equal and a few ulps apart): nothing removed; outcome values planted and not read; the key named and in the default plan |
| `test_reference_numbers.py` | 2 | The new set on the reference data (above) |

**Failed on the code before:** every new and changed test file of the branch was run against `main`'s package (`0f31698`; packet, section 8): 55 failed, 280 passed. Of the 29 new tests, **25 failed**. The 4 that passed are guard cases of `test_group_unknown_is_rule_5_after_missing_value` (model-recalled, out of scope, missing value, and scope not confirmed for a record with a DOI): they pin what must not change. Read with care: on `main`, the checker-level cases of `test_freeze_invariants.py` (including the six earlier invariants and `test_a_texas_am_record_is_not_without_a_group`) fail on the new required `grouping` argument, a signature change, not behaviour. The end-to-end test `test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze` fails on `main` because nothing refuses the record.

**Changed tests, none removed or weakened** (each because the owner's decision changes its premise; what it tested is still tested):
- **Records without a DOI used as vehicles for identity or the survivor rule** now have no group under paper grouping. Each test gives that record's source a dataset grouping in its test plan, so it keeps a group. Grouping never changes identity: Checks' paper identity reads the DOI and reference only (step 6 re-check, finding 2a). Each also gains an assertion that under paper grouping the record is `group_unknown`. The tests:
  - `test_eligibility.py`: `test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule`, `test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi`, `test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order`, `test_an_ambiguous_group_keeps_its_conflict_in_every_set` (with a helper `grouped_by_dataset`);
  - `test_order_independence.py` (the reviewer's A-B-C chain: C, the extract record without a DOI);
  - `test_conflict_policy.py` (the chain's C).
- **`primary_set_problems` takes a required `grouping`:** its callers in `test_freeze_invariants.py`, `test_order_independence.py` and `test_conflict_policy.py` pass it; their record dicts carry `paper` and `batch`.
- **The answer file (rows 5–6):**
  - `test_controlled_duplicates.py`: the pinned fingerprint, `EXPECTED` for the case, and two new assertions on the explanation and the survivor reason;
  - `test_controlled_duplicates_handling.py`: the new primary handling maps to (`in_scope`, `group_unknown`). In the "none" branch, the set without the most influential paper may remove a primary member of the removed paper, and nothing else may differ.
- **Nine sets:** `test_plan.py` (the reference plan's list); `test_analysis_stage.py::test_every_analysis_is_stored_with_both_calibrations` (the stored list). Four small-design tests in `test_analysis_stage.py` asserted one calibration reason for every analysis of the run. In those designs the papers cross the alloys, so the new set has one alloy left (`insufficient_groups`) or no record (`coefficient_not_fitted`). The run-wide claims now apply to every other analysis, and each test pins the new set's own reason (helper `calibration_reasons`); the exploratory test reads the pooled row's calibration.
- **The marked run:** `test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates` asserted that `possible_duplicates_separate` was not analysed (records without a group); now it asserts that every set is analysed.
- **`test_reference_sets.py`:** `_check_one_change` knows the new key (exactly the primary members of one group differ); the extract run's `possible_duplicates_separate` now equals primary (asserted as 0, with the reason; its change is exercised in the unit test above).
- **`test_permutation_stats.py`, `test_order_independence.py`:** each asserts that the new set is among the results compared.
- **`test_assumptions.py`:** `records_without_group` in force (its open wording in history); one open entry; the page and summary counts; "nine" sets with "eight" in history; `sensitivity_one_change` and `eligibility_rule_order` decided on 2026-10-06 with their 2026-10-05 wording in history; `PARTLY` loses `records_without_group`.

## Mutation checks

Each safeguard was changed in a scratch copy of the package (`data/` linked, `PYTHONPATH` to the copy, run from outside the repository, the import checked), one at a time, against the named tests. The control (no change) passes: 179 passed. Final run on the final tests (packet, section 7):

| Mutation | Result |
|---|---|
| m01: rule 5 removed | 14 failed, 99 passed |
| m02: rule 5 after the menu exclusions | 2 failed, 60 passed |
| m03: rule 5 after identity (a survivor may lack a group) | 1 failed |
| m04: rule 5 judged under the primary grouping in every set | 1 failed, 61 passed |
| m05: freeze invariant (7) off | 2 failed, 16 passed |
| m06: invariant (7) computed through rule 5's `has_group` (switched off with it) | 1 failed, 17 passed |
| m07: the paper with the smallest share | 5 failed, 37 passed |
| m08: the paper with the most records, not the most information | 4 failed, 38 passed |
| m09: tie-break by database id | 2 failed, 11 passed |
| m10: tie-break without the source order | 1 failed, 12 passed |
| m11: ties by exact equality, not the numerical zero | 1 failed, 12 passed |
| m12: the choice counts records outside the primary set | 2 failed, 11 passed |
| m13: removal cascades through the grain-size rule | 1 failed, 18 passed |
| m14: slope information without the alloy contrast rule | 1 failed, 12 passed |
| m15: nothing removed (the set equals primary) | 7 failed, 41 passed |

All 15 are caught. **m14 survived at first:** the only no-contrast test used 9.0 and 9.000000000000002 µm, whose transforms are exactly equal, so the deviations were exactly zero with or without the rule. A case a few units in the last place apart (9.0 and 9.000000000000004 µm: transforms differ by 5.6e-17) was added to `test_without_any_slope_information_nothing_is_removed`, and m14 is now caught. All 15 were then re-run on the final tests (the table above).

## Assumptions register

114 entries (was 113): 112 in force, 1 open (`curator_tabular_sources`), 1 direction approved; 111 applied "yes", 1 "partly" (`constructed_test_runs`), 2 "not yet". Every change is by the owner on 2026-10-06, not reviewed by an expert; earlier wording is in each entry's history.
- **Decided:** `records_without_group`: open → in force, applied "yes" (settings `eligibility.NO_GROUP_RULE` = "group_unknown", `has_group`, `primary_set_problems`, `analysis.RecordsWithoutGroup`); its open wording in history.
- **New:** `most_influential_paper_set` (settings `INFLUENCE_KEY`, `INFLUENCE_RULE`, `most_influential`, `influence_tie_key`, `statistics.slope_information`, `statistics.RELATIVE_ZERO` = 1e-10, `profile.SENSITIVITY_ANALYSES`).
- **Reworded (history kept):** `eligibility_rule_order` (rule 5), `sensitivity_one_change` (nine sets), `primary_set_invariants` (point 7), `fixed_minimums` (the paper minimum stays a count, final for sprint 1).
- **Lists:** `code_vocabularies` (two rules, one key).
- **Note:** `effective_papers` (I_g also chooses the removed paper; the minimum stays a count).

The register test checks that each named setting exists and, where stated, holds the value. It does not show that an entry's wording matches what the code does; the named regression tests cover the behaviour (CLAUDE.md, item 12).

## Commits

One code commit, `c5f74f0`: the two decisions share `eligibility.py`, the register and several test files, and could not be split without interactive staging. This summary and the packet are in the next commit and change no code.

## What this step does not do

- It does not change the statistical method, the verdict rule, the minimums or the validity checks.
- The new set's paper is chosen from the primary set's structure only. It does not say whether that paper's values are wrong, and the set is not a robustness test of the verdict: it is a single descriptive analysis.
- The tie-break has not occurred on real data (on the reference data the largest share is a clear maximum).
- A record without a group is excluded, never re-grouped: a source whose records lack DOIs, grouped by paper, contributes nothing. Grouping such a source by dataset is a plan choice (its grouping setting), not made here.

## PRD corrections and clarifications (for the next PRD update)

1. **PRD 5.3 (rule order):** a record without a group under the plan's grouping (no DOI under paper grouping) is not eligible, rule 5 `group_unknown`, after missing value and before scope not confirmed; no group is invented.
2. **PRD 5.3 / 14.1 (controlled extract rows 5–6):** "possible duplicate: counted once; sensitivity both counted separately" → "not eligible: no group (paper reference missing)"; sensitivity none.
3. **PRD 5.6 / 5.7 (sensitivity analyses):** nine named sets; the ninth is "without the most influential paper" (largest share of slope information, from structure only; tie-break by source order, row, identity).
4. **PRD 5.8:** the paper minimum is a count of informative papers, final for sprint 1.
5. **Primary-set invariants:** seven (no record without a group), checked at the freeze.

## Open items

1. ~~Second-model review, then the owner's decision on merging.~~ Done: "safe to merge"; the owner decided to merge (2026-10-06).
2. ~~Owner: approve or not the new set's values.~~ Approved as reported (2026-10-06).
2a. **Backlog, before the final evaluation:** an analysis-specific simulation seed; about 10,000 simulations (section "Backlog").
3. **Owner, before step 8:** `curator_tabular_sources` (unchanged).
4. Step 8 waits for the owner's go.

## Questions for the reviewer

1. Is rule 5's position right, and can a record without a group still reach any fit (any set, any plan) or push out a grouped twin?
2. Is invariant (7) at the freeze independent of rule 5, as claimed?
3. Can the choice of the removed paper depend on an outcome value, a database id or an order? Is the tie-break stable?
4. Does the new set differ from primary in exactly one respect, and is "no cascade through the grain-size rule" the right reading of that?
5. Is any claim stronger than the code supports?
