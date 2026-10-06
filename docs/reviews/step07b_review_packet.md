# Build step 7b — review packet

Date: 2026-10-06. Branch: `step-07b-group-and-influence`, from `main` at `0f31698`. Code reviewed: commit `c5f74f0`. Generated from the files on disk by a script, so every diff and output below is quoted exactly. Left out: no frozen data changed (the extract is byte-identical); the register diff is given in full.

## How to use this packet

The owner applied two decisions (records without a group decided at inclusion; a sensitivity set without the most influential paper). Both touch safeguards. Please review against `docs/reviews/checklist.md` and answer the questions at the end of the summary (section 1). Section 2 is the code diff; 3 the new test file; 4 the test diffs; 5 the register and answer-file diffs; 6 the reference comparison (before/after, its script and output); 7 the mutation checks; 8 the tests that failed on the code before; 9 the suite output.

## 1. The summary

# Build step 7b — summary for review

Date: 2026-10-06. Branch: `step-07b-group-and-influence` (from `main` at `0f31698`). **Status: built (code at `c5f74f0`), the whole suite passes (1,186 locally, 1,186 in the test image; GitHub Actions success, runtime image OK: https://github.com/kelawady/hypocurate/actions/runs/37474428306); pushed; not merged** (owner's instruction: "full suite, summary, review packet, push, and stop. Do not merge."). A small step between 7 and 8, applying two owner decisions of 2026-10-06. **Both touch safeguards** (an eligibility rule, the freeze check's invariants, the sensitivity sets), so they need the second model's review before any merge (CLAUDE.md, "How we work" item 5). The review packet is `docs/reviews/step07b_review_packet.md`; the checklist is `docs/reviews/checklist.md`.

**Not changed:** no migration (below), no change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose or dependencies. No agent, no model call, no screen. No PRD document is changed; corrections are listed at the end.

## The owner's decisions (2026-10-06)

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

1. **Second-model review** of this step (both changes are safeguard changes), then the owner's decision on merging.
2. **Owner:** approve or not the new set's values as reference numbers (they are pinned in `test_reference_numbers.py` as "reported, not yet approved").
3. **Owner, before step 8:** `curator_tabular_sources` (unchanged).
4. Step 8 waits for the owner's go.

## Questions for the reviewer

1. Is rule 5's position right, and can a record without a group still reach any fit (any set, any plan) or push out a grouped twin?
2. Is invariant (7) at the freeze independent of rule 5, as claimed?
3. Can the choice of the removed paper depend on an outcome value, a database id or an order? Is the tie-break stable?
4. Does the new set differ from primary in exactly one respect, and is "no cascade through the grain-size rule" the right reading of that?
5. Is any claim stronger than the code supports?

## 2. Code diff (`main...HEAD`, package and README)

```diff
diff --git a/README.md b/README.md
index 67d15e6..5324b1d 100644
--- a/README.md
+++ b/README.md
@@ -155,6 +155,8 @@ checkpoints.freeze_dataset(engine, run_id)  # counts and fingerprint; or "no dat
 
 - **The plan** follows `PLAN_SCHEMA` exactly and holds every plan setting that affects eligibility or grouping. The default and reference plans take each value from the domain profile (`profile.py`); decision code reads those settings only from the locked plan. Some policies are fixed in code for every plan (listed in `eligibility.py` and register entry `fixed_policies_in_code`), among them the rules no plan can change for the primary set (`primary_set_invariants`).
 - **Checks and Inclusion read through their own access objects** (`dispatch.bind_code`). Inclusion receives no outcome value.
+- **A record without a group** (a paper-grouped record without a DOI) is stored and shown but not eligible: rule 5, `group_unknown`, judged under each set's grouping; no group is invented, and the freeze refuses a primary set holding one (step 7b).
+- **Nine sensitivity sets**, each one named change from the primary set. The ninth, `without_most_influential_paper`, leaves out the paper with the largest share of slope information, chosen from grain sizes, alloys and groups only (step 7b).
 - **Every write** takes `hc_write_lock(p_run => …)` in `run_transaction`, re-checks by id what it read, and logs any refusal (`audit_log`, `detail.result` "rejected").
 - **Constructed test data** (the controlled extract) enter only a run marked `{"constructed_test_data": true}` in `experiment_flags` at dispatch.
 
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index 640e3f4..163852f 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -59,18 +59,19 @@ FLAG_KINDS = frozenset({"exact_duplicate", "possible_duplicate", "values_disagre
                         "scope_not_confirmed", "invalid_value", "model_recalled"})
 # Step 6 additions (owner, 2026-10-05): the category "several candidates" (an ambiguous match
 # group), the rules "missing_value", "identity_unresolved" and "conflict_unresolved", and the
-# sensitivity keys "no_exclusions" and "conflicts_survivor_value".
+# sensitivity keys "no_exclusions" and "conflicts_survivor_value". Step 7b (owner, 2026-10-06): the
+# rules "group_unknown" and "most_influential_paper", the key "without_most_influential_paper".
 FLAG_CATEGORIES = frozenset({"identical values", "differ beyond tolerance", "within tolerance",
                              "outside scope", "scope not confirmed", "physically impossible",
                              "several candidates"})
 ELIGIBILITY_RULES = frozenset({"in_scope", "out_of_scope", "scope_not_confirmed", "invalid_value",
                                "duplicate_counted_once", "model_recalled", "single_grain_size",
                                "excluded_by_rule", "missing_value", "identity_unresolved",
-                               "conflict_unresolved"})
+                               "conflict_unresolved", "group_unknown", "most_influential_paper"})
 SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                               "source_only_assignments", "possible_duplicates_separate",
                               "scope_not_confirmed_included", "removal_after_lock", "no_exclusions",
-                              "conflicts_survivor_value"})
+                              "conflicts_survivor_value", "without_most_influential_paper"})
 ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS
 
 
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index df4c260..0134528 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -142,7 +142,8 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
         # The result check (owner, 2026-10-06): the primary set itself against every invariant.
         run_flags = conn.execute(text("SELECT experiment_flags FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
         broken = el.primary_set_problems(set(members[el.PRIMARY]), by_id, flags,
-                                         isinstance(run_flags, dict) and run_flags.get(CONSTRUCTED_MARK) is True)
+                                         isinstance(run_flags, dict) and run_flags.get(CONSTRUCTED_MARK) is True,
+                                         grouping=el.settings(plan).grouping)
         if broken:
             raise Refused("freeze_dataset", "invariant_broken", "; ".join(broken))
         stored = dict(conn.execute(text("SELECT record_id, rule FROM run_record WHERE run_id = :r"),
@@ -151,6 +152,8 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
             raise Refused("freeze_dataset", "changed_since_read",
                           "the stored decisions are not what the locked rules produce")
         record = {"fingerprint": fp, "counts": counts, "frozen": bool(members[el.PRIMARY])}
+        if el.INFLUENCE_KEY in sets:  # step 7b: which paper the set leaves out (group key, share, ties)
+            record["most_influential"] = el.most_influential(plan, by_id, members[el.PRIMARY])
         code_stage(conn, run_id, "dataset_freeze", {"plan": data["plan"]["fingerprint"]}, record)
         if members[el.PRIMARY]:
             conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 146a321..5347434 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -23,21 +23,29 @@ Each record gets one rule code, the first that applies (owner, 2026-10-05):
 3. `out_of_scope`: a known value outside the scope (test type; reported temperature outside
    the room-temperature range, or a band outside the scope; microstructure, or phase class).
 4. `missing_value`: composition, predictor or outcome without an accepted value.
-5. `scope_not_confirmed`: a scope value missing, or held with a status the plan does not accept.
-6. `excluded_by_rule`: an exclusion rule from the menu (for example grain size below 0.1 µm).
-7. Identity, among records that passed 1–6, per flag the plan maps:
+5. `group_unknown`: the record has no group under the set's grouping (a paper-grouped record
+   without a DOI; a batch-grouped record without a batch). No group is invented (owner,
+   2026-10-06, step 7b; register 'records_without_group'). After rules 1-4, so that a record out of
+   scope or missing a value keeps that more basic reason; before identity, so that a record without
+   a group is never chosen as a survivor and never pushes out its grouped twin; before the
+   grain-size count, so that alloys are counted on records that can be analysed.
+6. `scope_not_confirmed`: a scope value missing, or held with a status the plan does not accept.
+7. `excluded_by_rule`: an exclusion rule from the menu (for example grain size below 0.1 µm).
+8. Identity, among records that passed 1–7, per flag the plan maps:
    `identity_unresolved` (every record of an ambiguous group), `conflict_unresolved` (every
    record of a group whose values disagree), `duplicate_counted_once` (every record but the
    survivor of an exact or possible duplicate group).
-8. `single_grain_size`: the alloy (same-alloy rule) has fewer than the plan's distinct grain
-   sizes among records that passed 1–7, so duplicates are resolved before grain sizes are
+9. `single_grain_size`: the alloy (same-alloy rule) has fewer than the plan's distinct grain
+   sizes among records that passed 1–8, so duplicates are resolved before grain sizes are
    counted (owner, 2026-10-05).
-9. `in_scope`: eligible.
+10. `in_scope`: eligible.
 
 **Sensitivity sets** (register 'sensitivity_one_change'): each differs from the primary set in
 exactly one named respect; every other rule applies unchanged. `SENSITIVITY_CHANGES` lists
 the change of each key. The variation each key applies is fixed by the key (its name in the
-vocabulary), not by a number in the plan.
+vocabulary), not by a number in the plan. The set 'without_most_influential_paper' (step 7b) is the
+primary set minus every record of the paper holding the largest share of slope information
+(`most_influential`); its records get `most_influential_paper` in that set only.
 """
 from __future__ import annotations
 
@@ -46,9 +54,16 @@ from collections import defaultdict
 from dataclasses import dataclass, replace
 from typing import Any, Iterable, Mapping
 
+from hypocurate.pipeline import statistics
 from hypocurate.sources.normalize import same_alloy_key
 
 PRIMARY = "primary"
+# Rule 5 (owner, 2026-10-06; register 'records_without_group').
+NO_GROUP_RULE = "group_unknown"
+# The sensitivity set without the most influential paper, and the rule its removed records get in
+# that set (owner, 2026-10-06; register 'most_influential_paper_set').
+INFLUENCE_KEY = "without_most_influential_paper"
+INFLUENCE_RULE = "most_influential_paper"
 # Sprint 1 supports one model (CLAUDE.md rule 6): its outcome is yield strength. Plan validation
 # refuses any other (re-check finding 2b; register 'supported_outcomes').
 SUPPORTED_OUTCOMES = ("yield_strength",)
@@ -119,6 +134,8 @@ SENSITIVITY_CHANGES = {
     "possible_duplicates_separate": "records of unresolved or possible duplicate groups count as separate "
                                     "measurements",
     "conflicts_survivor_value": "conflict groups are counted once by the survivor rule",
+    INFLUENCE_KEY: "the records of the most influential paper (the largest share of slope information, from "
+                   "grain sizes, alloys and groups only) are removed",
 }
 
 
@@ -188,6 +205,8 @@ def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
                                               for k, c, rule in base.flag_rules))
     if key == "conflicts_survivor_value":
         return base  # its one change is `conflict_survivor`, set above
+    if key == INFLUENCE_KEY:
+        return base  # its one change is applied to the primary set's decisions (`decide`)
     raise KeyError(f"no change is defined for the analysis {key!r}")
 
 
@@ -231,6 +250,11 @@ def _missing(rec: Mapping, st: Settings) -> bool:
         rec["values"].get(st.predictor) is None
 
 
+def has_group(rec: Mapping, st: Settings) -> bool:
+    """Rule 5: does the record have a group under the set's grouping (`group`)?"""
+    return group(rec, st) is not None
+
+
 def _excluded(rec: Mapping, st: Settings) -> bool:
     for items in st.exclusions:
         e = dict(items)
@@ -286,7 +310,7 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
         if flag_rule(f, st) == "invalid_value":
             for rid in f["records"]:
                 rules.setdefault(rid, "invalid_value")
-    for r in records.values():  # 3-6
+    for r in records.values():  # 3-7
         if r["id"] in rules:
             continue
         sc = scope(r, st)
@@ -294,12 +318,14 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
             rules[r["id"]] = "out_of_scope"
         elif _missing(r, st):
             rules[r["id"]] = "missing_value"
+        elif not has_group(r, st):
+            rules[r["id"]] = NO_GROUP_RULE
         elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
             rules[r["id"]] = "scope_not_confirmed"
         elif _excluded(r, st):
             rules[r["id"]] = "excluded_by_rule"
-    _identity(records, flags, rules, st)
-    sizes: dict[str, set] = defaultdict(set)  # 8
+    _identity(records, flags, rules, st)  # 8
+    sizes: dict[str, set] = defaultdict(set)  # 9
     for r in records.values():
         if r["id"] not in rules:
             sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
@@ -307,9 +333,53 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
         if r["id"] not in rules:
             rules[r["id"]] = ("single_grain_size" if len(sizes[alloy(r, st.decimals)]) < st.min_grain_sizes
                               else "in_scope")
+    if key == INFLUENCE_KEY:  # the set's one change, on the primary decisions above
+        for i in most_influential(plan, records, members(rules))["records"]:
+            rules[i] = INFLUENCE_RULE
     return rules
 
 
+def most_influential(plan: Mapping[str, Any], records: Mapping[int, Mapping], ids: Iterable[int]) -> dict:
+    """The paper (the group under the primary grouping) holding the largest share of slope
+    information among the primary set's records `ids` (owner, 2026-10-06; register
+    'most_influential_paper_set'). I_g comes from `statistics.slope_information`: grain sizes, alloys
+    (the plan's same-alloy rule) and groups only; the records carry no outcome value. Shares within
+    `statistics.RELATIVE_ZERO` of the largest are tied; a tie is broken by each tied paper's earliest
+    record under (the plan's survivor source order, the lowest row in the source file, the stable
+    identity: source-version fingerprint, origin key, item index), never a database id or an order.
+    Without any slope information nothing is removed (reason 'no_slope_information')."""
+    st = settings(plan)
+    # A primary record without a group exists only if rule 5 was bypassed; it is no paper's, and the
+    # freeze's invariant (7) refuses such a primary set.
+    chosen = [records[i] for i in ids if group(records[i], st) is not None]
+    items = [(f"{r['version_fingerprint']}|{r['origin']}|{r['item_index']}", alloy(r, st.decimals), group(r, st),
+              r["values"][st.predictor]) for r in chosen]
+    info = statistics.slope_information(items, plan["variables"]["predictor"]["transformation"])
+    total = sum(info.values())
+    if not total > 0:
+        return {"group": None, "share": None, "tied": [], "records": [], "n_records": 0, "n_alloys": 0,
+                "reason": "no_slope_information"}
+    top = max(info.values())
+    tied = sorted(g for g, v in info.items() if v >= top - statistics.RELATIVE_ZERO * top)
+
+    def earliest(g: str) -> tuple:
+        return min(influence_tie_key(r, st) for r in chosen if group(r, st) == g)
+
+    pick = min(tied, key=earliest)
+    removed = sorted(r["id"] for r in chosen if group(r, st) == pick)
+    return {"group": pick, "share": info[pick] / total, "tied": tied, "records": removed,
+            "n_records": len(removed), "n_alloys": len({alloy(records[i], st.decimals) for i in removed}),
+            "reason": None}
+
+
+def influence_tie_key(rec: Mapping, st: Settings) -> tuple:
+    """The tie-break of `most_influential` for one record (owner, 2026-10-06): the plan's survivor
+    source order, the row in the source file, then the stable identity."""
+    order = st.survivor_order.index(rec["source"]) if rec["source"] in st.survivor_order else len(st.survivor_order)
+    return (order, rec["row"] if rec["row"] is not None else math.inf, rec["version_fingerprint"], rec["origin"],
+            rec["item_index"])
+
+
 class MissingSetFlags(ValueError):
     """A sensitivity set needs its own matching flags and the Checks result lacks them."""
 
@@ -338,14 +408,16 @@ def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | No
 
 
 def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: Iterable[Mapping],
-                         marked: bool) -> list[str]:
+                         marked: bool, *, grouping: Mapping[str, str]) -> list[str]:
     """The result check of the freeze (owner, 2026-10-06; register 'primary_set_invariants'): what
     in the primary set itself breaks an invariant, whatever the plan said. `flags` are the Checks
     flags, including every retained pairwise exact or conflict result (two-record flags inside
     mixed groups), so exact and conflict pairs are checked pair by pair, never through a group's
     label (confirmation, 2026-10-06); identity and validity are independent of the plan's grouping
     and outcome. `records` gives
-    each member's kind and source; `marked` is the run's test mark. Empty if nothing."""
+    each member's kind, source, paper and batch; `marked` is the run's test mark; `grouping` is the
+    primary set's grouping (source -> unit), for invariant (7), no record without a group (step 7b,
+    owner 2026-10-06), checked with `group_in` itself, not through rule 5. Empty if nothing."""
     from hypocurate.sources.versions import SOURCES
     out = []
     flags = list(flags)
@@ -376,6 +448,9 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
     constructed = sorted(i for i in members if getattr(SOURCES.get(records[i]["source"]), "constructed", False))
     if constructed and not marked:
         out.append(f"constructed records in a run not marked as a test: {constructed}")
+    ungrouped = sorted(i for i in members if group_in(records[i], grouping) is None)
+    if ungrouped:
+        out.append(f"records without a group: {ungrouped}")
     return out
 
 
@@ -464,7 +539,12 @@ def members(rules: Mapping[int, str]) -> list[int]:
 
 def group(rec: Mapping, st: Settings) -> str | None:
     """The record's independent group under the set's grouping (PRD 5.7)."""
-    unit = st.grouping.get(rec["source"])
+    return group_in(rec, st.grouping)
+
+
+def group_in(rec: Mapping, grouping: Mapping[str, str]) -> str | None:
+    """The record's group under a grouping (source -> unit), or None: no group is invented."""
+    unit = grouping.get(rec["source"])
     if unit == "paper":
         return f"paper:{rec['paper']}" if rec["paper"] else None
     if unit == "dataset":
diff --git a/hypocurate/pipeline/inclusion.py b/hypocurate/pipeline/inclusion.py
index faab423..d3a14aa 100644
--- a/hypocurate/pipeline/inclusion.py
+++ b/hypocurate/pipeline/inclusion.py
@@ -61,7 +61,10 @@ def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
         code_stage(conn, run_id, "inclusion", {"plan": data["plan"]["fingerprint"], "records": len(read_ids),
                                                "flags": len(read_flags)},
                    {"rules": totals, "differences_from_primary": differences,
-                    "changes": {k: el.SENSITIVITY_CHANGES[k] for k in sets if k != el.PRIMARY}})
+                    "changes": {k: el.SENSITIVITY_CHANGES[k] for k in sets if k != el.PRIMARY},
+                    **({"most_influential": el.most_influential(plan, {r["id"]: r for r in records},
+                                                                el.members(primary))}
+                       if el.INFLUENCE_KEY in sets else {})})
         return sets
 
     return write(engine, run_id, "inclusion", "decide", body)
diff --git a/hypocurate/pipeline/profile.py b/hypocurate/pipeline/profile.py
index f21387d..b5e8c80 100644
--- a/hypocurate/pipeline/profile.py
+++ b/hypocurate/pipeline/profile.py
@@ -77,10 +77,12 @@ SMALLEST_EFFECT = 150.0
 
 # --- Sensitivity analyses (owner, 2026-10-05; register 'sensitivity_one_change') ---------
 # Each differs from the primary set in exactly one named respect; descriptive only, never
-# changes the verdict, no adjustment for there being eight.
+# changes the verdict, no adjustment for there being nine. The ninth, without the most influential
+# paper, added by the owner on 2026-10-06 (step 7b; register 'most_influential_paper_set').
 SENSITIVITY_ANALYSES = ("no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                         "source_only_assignments", "scope_not_confirmed_included",
-                        "possible_duplicates_separate", "conflicts_survivor_value")
+                        "possible_duplicates_separate", "conflicts_survivor_value",
+                        "without_most_influential_paper")
 
 # --- Tags (PRD 5.5; register 'tag_starting_lists'; seeded by migration 0002) -------------
 TAG_STARTING_LISTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index 6040dad..cf3d864 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -208,10 +208,10 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
     informative: set = set()
     effective, largest = 0.0, None
     if used:
-        deviation = demeaned(x, alloy, len(used_alloys))
+        deviation, info = _information(x, alloy, len(used_alloys),
+                                       np.array([group_index[o.group] for o in used]), len(groups))
         contrast = np.abs(deviation)
         informative = {o.group for o, c in zip(used, contrast) if c > RELATIVE_ZERO * float(np.abs(x).max())}
-        info = np.bincount(np.array([group_index[o.group] for o in used]), deviation ** 2, len(groups))
         total = float(info.sum())
         if total > 0:
             effective, largest = total ** 2 / float(info @ info), float(info.max()) / total
@@ -225,6 +225,40 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
         effective_papers=effective, largest_paper_share=largest)
 
 
+def _information(x: np.ndarray, alloy: np.ndarray, n_alloys: int, group: np.ndarray, n_groups: int) -> tuple:
+    """The within-alloy deviations of the transformed grain size, and I_g per group index: the
+    group's sum of squared deviations (register 'effective_papers'). No outcome is used."""
+    deviation = demeaned(x, alloy, n_alloys)
+    return deviation, np.bincount(group, deviation ** 2, n_groups)
+
+
+def slope_information(items: Iterable[tuple], transformation: str) -> dict[str, float]:
+    """{group: I_g} for records given as (stable identity, alloy, group, grain size in µm): the same
+    computation as `design` (identity order, alloys with two or more distinct transformed grain sizes,
+    stable centring), from grain sizes, alloys and groups only, never an outcome. Used by `design` for
+    the effective number of papers and by Inclusion to choose the paper of the sensitivity set
+    'without_most_influential_paper' (step 7b; register 'most_influential_paper_set')."""
+    rows = sorted(items, key=lambda t: t[0])
+    transform = TRANSFORMATIONS[transformation]
+    values: dict[str, list] = {}
+    for _, alloy, _, d in rows:
+        if not (math.isfinite(d) and d > 0):
+            raise StatisticsError("a record has no finite positive grain size")
+        values.setdefault(alloy, []).append(transform(d))
+    used_alloys = sorted(a for a, v in values.items() if has_contrast(v))
+    keep = set(used_alloys)
+    used = [t for t in rows if t[1] in keep]
+    groups = sorted({t[2] for t in used})
+    if not used:
+        return {}
+    alloy_index = {a: i for i, a in enumerate(used_alloys)}
+    group_index = {g: i for i, g in enumerate(groups)}
+    _, info = _information(np.array([transform(t[3]) for t in used], dtype=float),
+                           np.array([alloy_index[t[1]] for t in used], dtype=int), len(used_alloys),
+                           np.array([group_index[t[2]] for t in used], dtype=int), len(groups))
+    return {g: float(info[i]) for g, i in group_index.items()}
+
+
 def has_contrast(values: list) -> bool:
     """At least two distinct transformed grain sizes: the full range exceeds the numerical zero
     (relative to the largest value). Adding a value can never remove a contrast (re-check finding 4)."""
```

## 3. New test file `tests/test_influential_paper.py`

```python
"""Step 7b (owner, 2026-10-06): the sensitivity set "without the most influential paper"; register
'most_influential_paper_set'.

The set is the primary set minus every record of the paper (the group under the primary grouping)
that holds the largest share of slope information, I_g = the group's sum of squared within-alloy
deviations of the transformed grain size (register 'effective_papers'). The paper is chosen by code at
Inclusion, from grain sizes, alloys and groups only: Inclusion receives no outcome value. Ties (shares
within the numerical zero of the largest) are broken by each tied paper's earliest record under the
plan's survivor source order, then the lowest row in the source file, then the stable identity. The
set differs from primary in exactly this one respect; it is descriptive and never changes the verdict.
"""
from __future__ import annotations

import copy
import math
from collections import defaultdict

import numpy as np
import pytest

import generator as g
from hypocurate.pipeline import analysis
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.plan import default_plan
from test_eligibility import cond, decide

PLAN = default_plan(1)
KEY = "without_most_influential_paper"
CO, CN = {"Co": 50.0, "Ni": 50.0}, {"Co": 40.0, "Ni": 60.0}


def information_test_side(rows):
    """I_g from (alloy, group, grain size), written independently of the package: alloys with two
    or more distinct grain sizes, x = d^-1/2, deviations from the alloy's mean x."""
    by_alloy = defaultdict(list)
    for alloy, group, d in rows:
        by_alloy[alloy].append((group, d ** -0.5))
    info = defaultdict(float)
    for members in by_alloy.values():
        xs = [x for _, x in members]
        if max(xs) - min(xs) <= 1e-10 * max(xs):
            continue
        mean = sum(xs) / len(xs)
        for group, x in members:
            info[group] += (x - mean) ** 2
    return dict(info)


def _records():
    """Three papers on two alloys: p1 has the widest grain-size range."""
    return [cond(1, comp=CO, gs=1.0, paper="p1"), cond(2, comp=CO, gs=100.0, paper="p1"),
            cond(3, comp=CO, gs=10.0, paper="p2"), cond(4, comp=CO, gs=12.0, paper="p2"),
            cond(5, comp=CN, gs=5.0, paper="p3"), cond(6, comp=CN, gs=6.0, paper="p3")]


def test_the_slope_information_is_the_owners_formula():
    """`statistics.slope_information` against the independent computation."""
    recs = _records()
    got = st.slope_information([(f"id{r['id']}", el.alloy(r, 1), f"paper:{r['paper']}", r["values"]["grain_size"])
                                for r in recs], "inverse_square_root")
    expected = information_test_side([(el.alloy(r, 1), f"paper:{r['paper']}", r["values"]["grain_size"]) for r in recs])
    assert got.keys() == expected.keys()
    for k in got:
        assert got[k] == pytest.approx(expected[k], rel=1e-12)


def test_the_design_uses_the_same_slope_information():
    """The effective number of papers and the largest share stored with every result come from the
    same function (one place), on generated data with several papers."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    obs = analysis.observations(data["records"], g.plan(), "primary")
    d = st.design(obs, "inverse_square_root")
    info = st.slope_information([(o.identity, o.alloy, o.group, o.grain_size) for o in obs], "inverse_square_root")
    values = np.array(list(info.values()))
    assert d.effective_papers == pytest.approx(values.sum() ** 2 / (values @ values), rel=1e-12)
    assert d.largest_paper_share == pytest.approx(values.max() / values.sum(), rel=1e-12)


def test_the_set_is_primary_minus_the_paper_with_the_largest_share():
    records = _records()
    primary = decide(records)
    assert set(primary.values()) == {"in_scope"}
    rules = decide(records, key=KEY)
    assert rules == {1: "most_influential_paper", 2: "most_influential_paper", 3: "in_scope", 4: "in_scope",
                     5: "in_scope", 6: "in_scope"}
    info = information_test_side([(el.alloy(r, 1), r["paper"], r["values"]["grain_size"]) for r in records])
    assert max(info, key=info.get) == "p1"
    chosen = el.most_influential(PLAN, {r["id"]: r for r in records}, sorted(primary))
    assert chosen["group"] == "paper:" + "p1" and chosen["records"] == [1, 2]
    assert chosen["share"] == pytest.approx(info["p1"] / sum(info.values()), rel=1e-12)
    assert chosen["tied"] == ["paper:p1"]


def test_it_differs_from_primary_in_exactly_this_one_respect():
    """Every record keeps its primary rule except the chosen paper's records, which are not in the
    set (rule `most_influential_paper`); no other rule is applied again."""
    records = [*_records(), cond(7, comp=CO, gs=10.0, doi=False), cond(8, test_type="compression"),
               cond(9, comp={"Fe": 50.0, "Ni": 50.0}, gs=3.0, paper="p4")]
    primary, other = decide(records), decide(records, key=KEY)
    differing = {i for i in primary if primary[i] != other[i]}
    assert differing == {1, 2} and {other[i] for i in differing} == {"most_influential_paper"}
    assert primary[9] == "single_grain_size" and other[9] == "single_grain_size"


def test_only_primary_members_count():
    """A record outside the primary set does not count toward its paper's share: here the widest
    range belongs to a compression test (out of scope), so its paper is not chosen."""
    records = [cond(1, comp=CO, gs=1.0, paper="p1", test_type="compression"), cond(2, comp=CO, gs=100.0, paper="p1"),
               cond(3, comp=CO, gs=10.0, paper="p2"), cond(4, comp=CO, gs=40.0, paper="p2")]
    assert decide(records, key=KEY) == {1: "out_of_scope", 2: "in_scope", 3: "most_influential_paper",
                                        4: "most_influential_paper"}


def _tie(ids, rows, sources=("mpea", "mpea")):
    """Two papers on two alloys with identical designs: equal shares."""
    (a1, a2), (b1, b2) = ids
    return [cond(a1, sources[0], comp=CO, gs=10.0, paper="pa", row=rows[0]),
            cond(a2, sources[0], comp=CO, gs=40.0, paper="pa", row=rows[0] + 1),
            cond(b1, sources[1], comp=CN, gs=10.0, paper="pb", row=rows[1]),
            cond(b2, sources[1], comp=CN, gs=40.0, paper="pb", row=rows[1] + 1)]


def _chosen(records):
    return el.most_influential(PLAN, {r["id"]: r for r in records}, sorted(r["id"] for r in records))


@pytest.mark.parametrize("ids", [((1, 2), (3, 4)), ((3, 4), (1, 2)), ((10, 2), (7, 1))])
def test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order(ids):
    """Equal shares: the paper whose earliest record has the lowest row in the source file (here
    'pb', rows 3-4, before 'pa', rows 50-51), whatever the database ids or the order of records."""
    records = _tie(ids, rows=(50, 3))
    for order in (records, records[::-1], records[1::2] + records[::2]):
        chosen = _chosen(order)
        assert chosen["group"] == "paper:pb" and chosen["tied"] == ["paper:pa", "paper:pb"]
        assert chosen["share"] == pytest.approx(0.5)


def test_a_tie_follows_the_survivor_source_order_before_the_row():
    """The plan's survivor source order comes first: an MPEA paper at row 50 beats an extract paper
    at row 3 (MPEA is first in the order)."""
    chosen = _chosen(_tie(((1, 2), (3, 4)), rows=(50, 3), sources=("mpea", "controlled_duplicates")))
    assert chosen["group"] == "paper:pa"


def test_without_any_slope_information_nothing_is_removed():
    """Grain sizes equal after the transformation: the set equals primary, and the choice says why."""
    records = [cond(1, gs=9.0), cond(2, gs=9.000000000000002)]
    assert decide(records) == {1: "in_scope", 2: "in_scope"}
    assert decide(records, key=KEY) == decide(records)
    chosen = _chosen(records)
    assert chosen["group"] is None and chosen["records"] == [] and chosen["reason"] == "no_slope_information"
    # Transformed values that differ by a few units in the last place (not exactly equal) are still no
    # contrast: the alloy rule of `statistics.has_contrast` applies before any information is counted.
    near = [cond(1, gs=9.0), cond(2, gs=9.000000000000004)]
    assert 9.0 ** -0.5 != 9.000000000000004 ** -0.5
    assert st.slope_information([(f"id{r['id']}", el.alloy(r, 1), "paper:p1", r["values"]["grain_size"])
                                 for r in near], "inverse_square_root") == {}
    assert _chosen(near)["reason"] == "no_slope_information"


def test_the_choice_uses_no_outcome_value():
    """The records Inclusion receives carry no outcome value; the choice is the same when every
    outcome field is absent, and when made-up outcome values are added (they are not read)."""
    records = _records()
    assert all("yield_strength" not in r["values"] for r in records)
    planted = copy.deepcopy(records)
    for n, r in enumerate(planted):
        r["values"]["yield_strength"] = 1e6 * (-1) ** n
        r["outcome"] = -r["values"]["yield_strength"]
    assert _chosen(planted) == _chosen(records)
    assert decide(planted, key=KEY) == decide(records, key=KEY)


def test_the_change_is_named_and_in_the_default_plan():
    assert KEY in PLAN["sensitivity_analyses"] and KEY in el.SENSITIVITY_CHANGES
    assert "most influential" in el.SENSITIVITY_CHANGES[KEY]
    assert not el.needs_own_flags(PLAN, KEY)  # it changes no matching setting: primary's flags apply


def test_the_numerical_zero_decides_ties():
    """Shares within RELATIVE_ZERO of the largest are tied (the register's numerical zero)."""
    records = _tie(((1, 2), (3, 4)), rows=(50, 3))
    records[1]["values"]["grain_size"] = 40.0 * (1 + 1e-14)
    chosen = _chosen(records)
    assert chosen["tied"] == ["paper:pa", "paper:pb"] and chosen["group"] == "paper:pb"
    records[1]["values"]["grain_size"] = 41.0
    assert _chosen(records)["tied"] == ["paper:pa"]
    assert math.isclose(st.RELATIVE_ZERO, 1e-10)
```

## 4. Test diffs (`main...HEAD`)

```diff
diff --git a/tests/test_analysis_stage.py b/tests/test_analysis_stage.py
index f171123..0b00430 100644
--- a/tests/test_analysis_stage.py
+++ b/tests/test_analysis_stage.py
@@ -16,6 +16,7 @@ from sqlalchemy.exc import IntegrityError
 import pipeline_world as pw
 from hypocurate.db.engine import make_engine
 from hypocurate.pipeline import analysis, completion, results
+from hypocurate.pipeline.plan import reference_plan
 from hypocurate.pipeline.writes import TEST_RUN_LABEL, Refused
 from pipeline_fixtures import frozen_run
 from stats_world import audit_codes, rows_of, run_on, small_rows, val
@@ -46,6 +47,19 @@ def calibration_rows(engine, rid):
     return rows_of(engine, "SELECT * FROM calibration_result WHERE run_id = :r ORDER BY id", r=rid)
 
 
+INFLUENCE = "without_most_influential_paper"
+
+
+def calibration_reasons(engine, rid, influence: bool) -> set:
+    """(status, reason) of the calibration rows of the set without the most influential paper
+    (`influence`), or of every other analysis (step 7b: that set is analysed on its own records, so
+    its validity checks can fail where the others pass)."""
+    return {(c.status, c.reason) for c in rows_of(
+        engine, "SELECT c.status, c.reason, a.key FROM calibration_result c JOIN analysis_result ar "
+                "ON ar.id = c.analysis_result_id JOIN analysis_set a ON a.id = ar.analysis_set_id "
+                "WHERE c.run_id = :r", r=rid) if (c.key == INFLUENCE) == influence}
+
+
 # --- sufficient with a verdict (the reference run) ------------------------------------------------
 
 def test_every_analysis_is_stored_with_both_calibrations(reference):
@@ -56,7 +70,7 @@ def test_every_analysis_is_stored_with_both_calibrations(reference):
         ("sensitivity", k, None) for k in ("no_exclusions", "tension_and_compression", "six_batches_as_groups",
                                            "same_alloy_1_at_pct", "source_only_assignments",
                                            "scope_not_confirmed_included", "possible_duplicates_separate",
-                                           "conflicts_survivor_value")]
+                                           "conflicts_survivor_value", "without_most_influential_paper")]
     assert all(r.withheld is False and r.test_run_label is None and r.n_records_not_used == 0 for r in rows)
     cal = calibration_rows(engine, rid)
     assert len(cal) == 2 * len(rows)
@@ -138,7 +152,10 @@ def test_below_the_minimums_every_analysis_holds_counts_and_records_only(engine)
     assert pooled["checks"]["inference_valid"] and pooled["estimated_power"] is not None  # no outcome used
     for r in result_rows(engine, rid):
         assert r.withheld and r.estimate is None and r.std_error is None and r.p_value is None
-    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "below_minimums")}
+    assert calibration_reasons(engine, rid, influence=False) == {("unavailable", "below_minimums")}
+    # Step 7b: without the most influential paper (here the papers cross the alloys) one alloy is left,
+    # so that set's check 2 fails and its validity reason takes precedence (decision 5 of step 7).
+    assert calibration_reasons(engine, rid, influence=True) == {("unavailable", "insufficient_groups")}
     # Nothing computed from outcomes anywhere in what is stored: the real outcomes can be anything.
     facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
     assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]
@@ -165,7 +182,8 @@ def test_use_what_is_available_gives_an_exploratory_verdict_on_the_same_data(eng
     assert out["decision"]["verdict"] in ("supported", "not_supported") and out["decision"]["label"] == "exploratory"
     pooled = result_rows(engine, rid)[0]
     assert not pooled.withheld and not pooled.minimums_met and pooled.p_value is not None
-    assert {c.method: c.status for c in calibration_rows(engine, rid)}["fixed"] == "computed"
+    assert {c.method: c.status for c in calibration_rows(engine, rid) if c.analysis_result_id == pooled.id}[
+        "fixed"] == "computed"
     completion.copy_decision(engine, rid)
     assert rows_of(engine, "SELECT outcome, exploratory, evidence_level FROM run WHERE id = :r", r=rid) == [
         ("sufficient", True, 5)]
@@ -178,7 +196,9 @@ def test_use_what_is_available_with_one_group_gives_the_coefficient_only(engine)
     assert (out["decision"]["state"], out["decision"]["evidence_level"]) == ("coefficient_only", 4)
     assert pooled["estimate"] is not None and pooled["std_error"] is None and pooled["p_value"] is None
     assert out["decision"]["verdict"] is None
-    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}
+    assert calibration_reasons(engine, rid, influence=False) == {("unavailable", "insufficient_groups")}
+    # Step 7b: removing the one paper leaves no record: no coefficient for that set.
+    assert calibration_reasons(engine, rid, influence=True) == {("unavailable", "coefficient_not_fitted")}
 
 
 def test_the_fixed_option_with_one_group_withholds_even_the_coefficient(engine):
@@ -186,7 +206,8 @@ def test_the_fixed_option_with_one_group_withholds_even_the_coefficient(engine):
     rid = run_on(engine, small_rows(3, papers=1))
     out = analysis.run_statistics(engine, rid)
     assert out["decision"]["evidence_level"] == 3 and out["analyses"][0]["estimate"] is None
-    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}
+    assert calibration_reasons(engine, rid, influence=False) == {("unavailable", "insufficient_groups")}
+    assert calibration_reasons(engine, rid, influence=True) == {("unavailable", "coefficient_not_fitted")}  # step 7b
 
 
 # --- no dataset frozen ------------------------------------------------------------------------------
@@ -234,13 +255,11 @@ def test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_
     analysis.run_statistics(engine, real)
     assert TEST_RUN_LABEL == LABEL
     assert out["test_run_label"] == LABEL and out["decision"]["evidence_level"] == 6  # keeps its level
-    # The extract's two records without a paper enter only 'possible_duplicates_separate': that descriptive
-    # analysis is not analysed (no group invented), and nothing is stored for it; the others are.
-    assert out["not_analysed"] == [{"analysis": "sensitivity:possible_duplicates_separate", "scope": "sensitivity",
-                                    "set": "possible_duplicates_separate", "source": None,
-                                    "reason": "records_without_group", "n_records_without_group": 2,
-                                    "n_records_in_set": out["not_analysed"][0]["n_records_in_set"]}]
-    assert "possible_duplicates_separate" not in {r.set_key for r in result_rows(engine, marked)}
+    # Step 7b (owner, 2026-10-06): the extract's two records without a paper are not eligible at
+    # inclusion (`group_unknown`), in every set, so every analysis is analysed and the statistics'
+    # backstop is never reached; before, 'possible_duplicates_separate' was not analysed.
+    assert out["not_analysed"] == []
+    assert "possible_duplicates_separate" in {r.set_key for r in result_rows(engine, marked)}
     assert {r.test_run_label for r in result_rows(engine, marked)} == {LABEL}
     assert {c.test_run_label for c in calibration_rows(engine, marked)} == {LABEL}
     assert rows_of(engine, "SELECT output->>'test_run_label' FROM stage_result WHERE run_id = :r "
@@ -510,3 +529,26 @@ def test_the_database_refuses_a_p_value_without_its_description_and_quantities(e
     with pytest.raises(IntegrityError, match="ck_analysis_result_p_value_description"):
         _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, p_value_description="exact p-value")
     _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1)
+
+
+def test_the_statistics_backstop_is_not_reached_in_a_normal_run(engine):
+    """Step 7b (owner, 2026-10-06; register 'records_without_group'): records without a group are decided
+    at inclusion, so a normal run never reaches the statistics' refusal (kept as a backstop, tested in
+    test_statistics.py). The marked run with the extract, whose rows 5-6 have no DOI: those two records
+    are `group_unknown` and in no set; every analysis is analysed; no `records_without_group` refusal is
+    logged."""
+    pw.registered(engine, ("mpea", "controlled_duplicates"))
+    rid = pw.through_freeze(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    out = analysis.run_statistics(engine, rid)
+    assert out["not_analysed"] == []
+    rules = dict(rows_of(engine, "SELECT r.source_item_key, rr.rule FROM run_record rr JOIN record r "
+                                 "ON r.id = rr.record_id WHERE rr.run_id = :r AND r.source_item_key LIKE 'extract%'",
+                         r=rid))
+    assert (rules["extract.csv:row:4"], rules["extract.csv:row:5"]) == ("group_unknown", "group_unknown")
+    in_sets = val(engine, "SELECT count(*) FROM analysis_set_record asr JOIN analysis_set a ON a.id = "
+                          "asr.analysis_set_id JOIN record r ON r.id = asr.record_id WHERE a.run_id = :r AND "
+                          "r.source_item_key IN ('extract.csv:row:4', 'extract.csv:row:5')", r=rid)
+    assert in_sets == 0
+    assert val(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r AND detail->>'code' = "
+                       "'records_without_group'", r=rid) == 0
+    assert len(out["analyses"]) == 3 + len(reference_plan(1)["sensitivity_analyses"])
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 31f1f07..65287b5 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -58,9 +58,9 @@ def test_every_category_has_entries_and_keys_are_unique():
 # Step 6 completed same_alloy_rule, sufficiency_options, controlled_extract_disabled and
 # assigned_value_statuses, and added constructed_test_runs (its label and exclusion: steps 7, 10).
 # Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
-# grain_size_transformation_at_analysis and reference_numbers; records_without_group is open, with
-# the code failing closed until the owner decides.
-PARTLY = {"constructed_test_runs", "records_without_group"}
+# grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
+# the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
+PARTLY = {"constructed_test_runs"}
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -127,10 +127,16 @@ def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review
     """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)
     and added the possible-duplicate case and the rule for several candidates in step 6 planning.
     Step 6 recorded two new open decisions for the owner (steps 7 and 8). Step 7: the owner decided
-    the first; a new one (records without a group) is open before step 8."""
-    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["curator_tabular_sources", "records_without_group"]
+    the first; a new one (records without a group) was open before step 8, and the owner decided it in
+    step 7b (2026-10-06)."""
+    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["curator_tabular_sources"]
     assert {e["key"]: e["pending"]["before_step"] for e in REGISTER if e["state"] == "open"} == {
-        "curator_tabular_sources": 8, "records_without_group": 8}
+        "curator_tabular_sources": 8}
+    grouped = BY_KEY["records_without_group"]
+    assert grouped["state"] == "in_force" and grouped["decided"] == {"by": OWNER, "date": "2026-10-06"}
+    assert "pending" not in grouped and grouped["applied"]["status"] == "yes"
+    assert grouped["history"][-1]["value"].startswith("open decision: Open: what a fit does with a frozen record")
+    assert "'group_unknown', rule 5" in grouped["statement"] and "No group is ever invented" in grouped["statement"]
     below = BY_KEY["below_minimum_display"]
     assert below["state"] == "in_force" and below["decided"] == {"by": OWNER, "date": "2026-10-05"}
     assert "not even a coefficient" in " ".join(below["notes"]) and below["history"][-1]["value"].startswith("open")
@@ -235,7 +241,9 @@ def test_the_step_6_decisions_carry_the_owners_wording():
     assert "CLAUDE.md rule 4" in conflicts["reason"] and "PRD 5.3" in conflicts["reason"]
     one = BY_KEY["sensitivity_one_change"]
     assert "exactly one named respect" in one["statement"] and "never change the verdict" in one["statement"]
-    assert "no adjustment is made for there being eight" in one["statement"]
+    # Step 7b (owner, 2026-10-06): a ninth set; the eight-set wording is kept in the history.
+    assert "no adjustment is made for there being nine" in one["statement"]
+    assert "no adjustment is made for there being eight" in one["history"][-1]["value"]
     assert "discretionary removals" in " ".join(one["notes"])
     access = BY_KEY["code_role_access"]["statement"]
     assert "Inclusion receives no outcome value" in access and "Not claimed: that outcomes play no part at all" in access
@@ -247,9 +255,13 @@ def test_the_step_6_decisions_carry_the_owners_wording():
     for key in ("sensitivity_one_change", "code_role_access", "constructed_test_runs", "record_extraction_provenance",
                 "eligibility_rule_order", "conflicts_not_pooled", "freeze_counts"):
         e = BY_KEY[key]
-        # conflicts_not_pooled was made a fixed rule by the owner on 2026-10-06.
-        date = "2026-10-06" if key == "conflicts_not_pooled" else "2026-10-05"
+        # conflicts_not_pooled was made a fixed rule by the owner on 2026-10-06; step 7b (owner, 2026-10-06)
+        # reworded sensitivity_one_change and eligibility_rule_order, each with its 2026-10-05 wording in history.
+        changed = ("conflicts_not_pooled", "sensitivity_one_change", "eligibility_rule_order")
+        date = "2026-10-06" if key in changed else "2026-10-05"
         assert e["decided"] == {"by": OWNER, "date": date} and e["expert_review"]["status"] == "not_reviewed"
+        if key in changed[1:]:
+            assert e["history"][-1]["from"] == "2026-10-05"
 
 
 def test_the_approved_reference_numbers_keep_the_earlier_values_in_their_history():
@@ -467,11 +479,10 @@ def test_open_decisions_are_shown_first_when_there_are_any():
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
     assert headings == HEADINGS
     first = re.split(r"<h2>", html)[1]
-    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["curator_tabular_sources", "records_without_group",
-                                                             "an_open_question"]
+    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["curator_tabular_sources", "an_open_question"]
     assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
-    assert first.count("Not decided (owner, before step 8)") == 2
-    assert "3 open decisions</strong>" in html
+    assert first.count("Not decided (owner, before step 8)") == 1  # records_without_group decided in step 7b
+    assert "2 open decisions</strong>" in html
     second = re.split(r"<h2>", html)[2]
     assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
     assert "pending: second-model technical review, before step 8" in second
@@ -482,9 +493,9 @@ def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
     summary = " ".join(re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1).split())
     count = {s: sum(e["state"] == s for e in REGISTER) for s in a.STATES}
     n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
-    assert count == {"in_force": len(REGISTER) - 3, "open": 2, "direction_approved": 1}
+    assert count == {"in_force": len(REGISTER) - 2, "open": 1, "direction_approved": 1}
     assert f"{len(REGISTER)} entries: {count['in_force']} in force" in summary
-    assert "2 open decisions</strong>" in summary
+    assert "1 open decision</strong>" in summary
     assert "1 direction approved, pending technical review</strong>" in summary
     assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
     assert html.index('id="summary"') < html.index("<h2>")
diff --git a/tests/test_conflict_policy.py b/tests/test_conflict_policy.py
index 466db55..c3dd84f 100644
--- a/tests/test_conflict_policy.py
+++ b/tests/test_conflict_policy.py
@@ -57,8 +57,10 @@ SHAPES = {
 def _chain(shape="only through B"):
     (ya, da, ra), (yb, db, rb), (yc, dc, rc), expected = SHAPES[shape]
     plan = survivor_plan(PLAN)
+    # Step 7b: C (no DOI in one shape) is grouped by dataset so that it keeps a group; identity is
+    # unchanged (Checks' paper identity never reads the grouping).
     plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
-                                 {"source": "controlled_duplicates", "unit": "paper"}]
+                                 {"source": "controlled_duplicates", "unit": "dataset"}]
     full = [rec(1, "mpea", ys=ya, doi=da, reference=ra), rec(2, "tamu_fcc", ys=yb, doi=db, reference=rb),
             rec(3, "controlled_duplicates", ys=yc, doi=dc, reference=rc),
             rec(4, "mpea", gs=40.0, ys=300.0, doi=da, reference=ra)]
@@ -89,9 +91,9 @@ def test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group(no_va
     plan, records, flags, _ = _chain(shape)
     recs = {r["id"]: r for r in records}
     for member in (1, 2, 3):  # A alone (only exact-linked to the conflict), B alone, C alone
-        problems = el.primary_set_problems({member, 4}, recs, flags, True)
+        problems = el.primary_set_problems({member, 4}, recs, flags, True, grouping=el.settings(plan).grouping)
         assert any("conflict" in p for p in problems), member
-    assert el.primary_set_problems({4}, recs, flags, True) == []
+    assert el.primary_set_problems({4}, recs, flags, True, grouping=el.settings(plan).grouping) == []
 
 
 # --- through the real pipeline: the controlled extract's conflicting rows 7-8 --------------------------
diff --git a/tests/test_controlled_duplicates.py b/tests/test_controlled_duplicates.py
index b11a895..30ab97f 100644
--- a/tests/test_controlled_duplicates.py
+++ b/tests/test_controlled_duplicates.py
@@ -16,7 +16,7 @@ TRUTH = FIXTURES / "truth.csv"
 # Step 6 (owner, 2026-10-05): the restored survivor wording and decision C (rows 7-8 are a conflict).
 # Owner, 2026-10-06: rows 15-16 describe the reference plan with its test-type rule (tension only),
 # their explanation included (after the step 6 review).
-TRUTH_SHA256 = "e6e859cd127b26cad233fac11f68c09eeb29dc2e4457ea68cba530ef2355025b"
+TRUTH_SHA256 = "0503f2b8e890c9d2c474beadfdd2f72f006b9cf817cd16495f494ac881242f9c"
 # The frozen source files: fingerprint-pinned, and not written by us, so they
 # cannot hold our answers. Everything else under data/ is scanned.
 FROZEN_SOURCE_FILES = {
@@ -287,7 +287,9 @@ def test_tension_only_handling_differs_only_for_compression_rows():
 EXPECTED = {
     "exact_duplicate_verbatim": ("exact_duplicate", "counted once", "none"),
     "exact_duplicate_renamed_alloy": ("exact_duplicate", "counted once", "none"),
-    "possible_duplicate_unknown_paper": ("possible_duplicate", "counted once", "both counted separately"),
+    # Step 7b (owner, 2026-10-06): no paper reference, so no group: not eligible in any set.
+    "possible_duplicate_unknown_paper": ("possible_duplicate", "not eligible: no group (paper reference missing)",
+                                         "none"),
     # Decision C (owner, 2026-10-05; corrects PRD 5.3, which contradicted CLAUDE.md rule 4).
     "conflict_value_differs": ("conflict", "neither enters: conflict unresolved",
                                "counted once in conflicts_survivor_value"),
@@ -319,6 +321,8 @@ def test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed():
     for t in rows:
         assert t["prd_5_3_class"] == "Possible duplicate that cannot be resolved"
         assert "Flagged as a possible duplicate, kept, not removed." in t["explanation"]
+        assert "no group is invented (owner, 2026-10-06)" in t["explanation"]  # step 7b
+        assert t["survivor_reason"].endswith("not eligible in any case (no group: the paper reference is missing)")
 
 
 # --- which record survives in the primary analysis (owner's rule, 2026-10-04) ------
diff --git a/tests/test_controlled_duplicates_handling.py b/tests/test_controlled_duplicates_handling.py
index cd6e78e..eaf4a43 100644
--- a/tests/test_controlled_duplicates_handling.py
+++ b/tests/test_controlled_duplicates_handling.py
@@ -71,6 +71,7 @@ def test_the_primary_handling_and_the_survivor_are_the_answer_files(run, t):
         "not eligible under a room-temperature plan": ("in_scope", "out_of_scope"),
         "not eligible: scope not confirmed": ("in_scope", "scope_not_confirmed"),
         "not eligible: excluded by the test-type rule (tension only)": ("in_scope", "out_of_scope"),
+        "not eligible: no group (paper reference missing)": ("in_scope", "group_unknown"),  # step 7b
     }[primary]
     assert (rules[mpea_id], rules[extract_id]) == expected
     if t["survivor_in_primary"].startswith("MPEA row"):
@@ -98,8 +99,13 @@ def test_the_sensitivity_handling_is_the_answer_files(run, t):
         assert sensitivity == "none"
         for key, rules in run["rules"].items():  # no set treats this pair differently from primary
             if key not in ("tension_and_compression", "source_only_assignments"):
-                assert (rules[mpea_id], rules[extract_id]) == \
-                    (run["rules"]["primary"][mpea_id], run["rules"]["primary"][extract_id]), key
+                expected = [run["rules"]["primary"][mpea_id], run["rules"]["primary"][extract_id]]
+                if key == "without_most_influential_paper":
+                    # Step 7b: that set removes one whole paper's primary members, whatever their duplicate
+                    # handling; it changes nothing else.
+                    expected = ["most_influential_paper" if r == "in_scope" and got == "most_influential_paper" else r
+                                for r, got in zip(expected, (rules[mpea_id], rules[extract_id]))]
+                assert [rules[mpea_id], rules[extract_id]] == expected, key
 
 
 def test_rows_15_and_16_enter_together_when_compression_is_permitted(run):
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index e14af31..a61cb12 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -58,6 +58,16 @@ def decide(records, flags=(), plan=PLAN, key=el.PRIMARY):
     return el.decide(plan, records, list(flags), key)
 
 
+def grouped_by_dataset(*sources, plan=PLAN):
+    """A plan grouping `sources` by dataset (step 7b): their records keep a group without a DOI, so a
+    test of identity or the survivor rule can use a record without a DOI. Grouping never changes
+    identity: Checks' paper identity reads the DOI and reference only (step 6 re-check, finding 2a)."""
+    plan = copy.deepcopy(plan)
+    plan["rules"]["grouping"] = [{"source": g["source"], "unit": "dataset" if g["source"] in sources else g["unit"]}
+                                 for g in plan["rules"]["grouping"]]
+    return plan
+
+
 # --- one rule per record, the first that applies ---------------------------------------------
 
 def test_each_rule_on_its_own():
@@ -125,9 +135,12 @@ def test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule():
                                                                               doi=False)]
     flags = [flag("exact_duplicate", "identical values", 1, 3, fid=1),
              flag("possible_duplicate", "identical values", 2, 4, fid=2)]
-    assert decide(records, flags) == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once",
-                                      4: "duplicate_counted_once"}
-    sep = decide(records, flags, key="possible_duplicates_separate")
+    # Step 7b: grouped by paper, record 4 (no DOI) has no group: rule 5, before identity.
+    assert decide(records, flags)[4] == "group_unknown"
+    plan = grouped_by_dataset("controlled_duplicates")
+    assert decide(records, flags, plan) == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once",
+                                            4: "duplicate_counted_once"}
+    sep = decide(records, flags, plan, key="possible_duplicates_separate")
     assert sep == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once", 4: "in_scope"}
 
 
@@ -136,16 +149,20 @@ def test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carri
     MPEA record does not: rule 1 keeps the extract record."""
     records = [cond(1, "mpea", gs=10.0, doi=False), cond(2, "controlled_duplicates", gs=10.0, doi=True),
                cond(3, "controlled_duplicates", gs=40.0)]
-    got = decide(records, [flag("possible_duplicate", "identical values", 1, 2)])
+    possible = [flag("possible_duplicate", "identical values", 1, 2)]
+    assert decide(records, possible)[1] == "group_unknown"  # step 7b: no DOI, grouped by paper
+    got = decide(records, possible, grouped_by_dataset("mpea"))
     assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}
 
 
 def test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order():
     records = [cond(1, "controlled_duplicates", gs=10.0, doi=False), cond(2, "tamu_fcc", gs=10.0, doi=False),
                cond(3, "tamu_fcc", gs=40.0, doi=False)]
-    got = decide(records, [flag("exact_duplicate", "identical values", 1, 2)])
+    assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)])[1] == "group_unknown"  # step 7b
+    plan = grouped_by_dataset("controlled_duplicates")
+    got = decide(records, [flag("exact_duplicate", "identical values", 1, 2)], plan)
     assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}
-    reordered = copy.deepcopy(PLAN)
+    reordered = copy.deepcopy(plan)
     reordered["rules"]["survivor_source_order"] = ["controlled_duplicates", "mpea", "tamu_fcc"]
     assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)], reordered)[1] == "in_scope"
 
@@ -205,7 +222,8 @@ def test_an_ambiguous_group_keeps_its_conflict_in_every_set():
     (`flags.raise_flags`), and the resulting sets are checked, not only the labels."""
     from test_flags import rec
     plan = copy.deepcopy(PLAN)
-    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "controlled_duplicates", "unit": "paper"},
+    # Step 7b: B (no DOI) is grouped by dataset so that it keeps a group; identity is unchanged.
+    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "controlled_duplicates", "unit": "dataset"},
                                  {"source": "tamu_fcc", "unit": "paper"}]
     full = [rec(1, "mpea", ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
             rec(3, "tamu_fcc", ys=440.0), rec(4, "mpea", gs=40.0, ys=300.0)]
@@ -412,3 +430,63 @@ def test_counts_known_at_the_freeze():
         {"n_records": 4, "n_alloys": 2, "n_alloys_two_grain_sizes": 2, "n_groups": 2, "resid_df": 1}
     assert got["check1_inputs_met"] and got["check2_inputs_met"] and not got["minimums_met"]
     assert got["minimums"] == {"records": False, "alloys": False, "groups": False, "resid_df": False}
+
+
+# --- Step 7b: a record without a group (owner, 2026-10-06; register 'records_without_group') -------
+
+def test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule():
+    """A literature record whose paper is not known (no DOI) has no group under paper grouping: it
+    gets a decision of its own, `group_unknown`, and is in no set. No group is invented."""
+    records = [*pair(1, 10.0), *pair(3, 10.0, doi=False, comp={"Co": 40.0, "Ni": 60.0})]
+    for key in (el.PRIMARY, *PLAN["sensitivity_analyses"]):
+        rules = decide(records, key=key)
+        assert (rules[3], rules[4]) == ("group_unknown", "group_unknown"), key
+        assert set(rules) == {1, 2, 3, 4}  # every stored record has its decision
+
+
+@pytest.mark.parametrize("record, expected", [
+    (dict(doi=False, kind="model_recalled"), "model_recalled"),
+    (dict(doi=False, test_type="compression"), "out_of_scope"),
+    (dict(doi=False, gs=None), "missing_value"),
+    (dict(doi=False, temp=None), "group_unknown"),     # scope not confirmed comes after it
+    (dict(doi=False, gs=0.05), "group_unknown"),        # excluded by a rule comes after it
+    (dict(doi=True, temp=None), "scope_not_confirmed"),
+])
+def test_group_unknown_is_rule_5_after_missing_value(record, expected):
+    """Owner, 2026-10-06: rule 5, after missing value and before scope not confirmed, the menu
+    exclusions, identity and the grain-size count."""
+    assert decide([cond(5, **record), *pair(1, 10.0)])[5] == expected
+
+
+def test_a_record_without_a_group_is_never_a_survivor():
+    """Before identity: a record without a group can never be chosen as the survivor of its
+    duplicate group and push out its grouped twin (the measurement would be lost). Here the plan's
+    source order would prefer the extract record, which has no DOI and so no group; the Texas A&M
+    record (grouped by dataset) survives, in primary and in every set."""
+    plan = copy.deepcopy(PLAN)
+    plan["rules"]["survivor_source_order"] = ["controlled_duplicates", "mpea", "tamu_fcc"]
+    tamu = dict(source="tamu_fcc", doi=False, batch="b1")
+    records = [cond(1, **tamu), cond(2, gs=40.0, **tamu), cond(3, "controlled_duplicates", doi=False)]
+    possible = flag("possible_duplicate", "within tolerance", 1, 3)
+    for key in (el.PRIMARY, *plan["sensitivity_analyses"]):
+        rules = decide(records, [possible], plan, key)
+        # In the set without the most influential paper the one group (the dataset) is the one removed.
+        kept = "most_influential_paper" if key == el.INFLUENCE_KEY else "in_scope"
+        assert (rules[1], rules[2], rules[3]) == (kept, kept, "group_unknown"), key
+
+
+def test_the_group_is_judged_under_each_sets_own_grouping():
+    """Texas A&M is grouped by dataset in primary and by batch in 'six_batches_as_groups': a record
+    without a batch has a group in primary and none in that set (the same `group` function)."""
+    tamu = dict(source="tamu_fcc", doi=False)
+    records = [cond(1, batch="b1", **tamu), cond(2, gs=40.0, batch="b1", **tamu),
+               cond(3, gs=20.0, batch=None, **tamu)]
+    assert decide(records) == {1: "in_scope", 2: "in_scope", 3: "in_scope"}
+    assert decide(records, key="six_batches_as_groups") == {1: "in_scope", 2: "in_scope", 3: "group_unknown"}
+
+
+def test_alloys_are_counted_on_records_with_a_group():
+    """Before the grain-size count (rule 9): a grain size held only by a record without a group does
+    not make its alloy eligible."""
+    records = [cond(1, gs=10.0), cond(2, gs=40.0, doi=False)]
+    assert decide(records) == {1: "single_grain_size", 2: "group_unknown"}
diff --git a/tests/test_freeze_invariants.py b/tests/test_freeze_invariants.py
index 41f9d4a..eb18ea0 100644
--- a/tests/test_freeze_invariants.py
+++ b/tests/test_freeze_invariants.py
@@ -8,7 +8,8 @@ kind and source:
 - no member carries an invalid-value flag;
 - no member belongs to an unresolved-identity group;
 - no member is model-recalled;
-- no member comes from a constructed source in a run not marked as a test.
+- no member comes from a constructed source in a run not marked as a test;
+- no member lacks a group under the primary grouping (step 7b, owner 2026-10-06).
 A freeze that fails any of them is refused and logged.
 
 Each end-to-end case uses a plan deliberately built to slip past settings validation: the
@@ -29,13 +30,16 @@ from hypocurate.pipeline.writes import Refused
 
 # --- the check itself, item by item ---------------------------------------------------------------
 
-def rec(i, source="mpea", kind="measured"):
-    return {"id": i, "source": source, "kind": kind}
+def rec(i, source="mpea", kind="measured", paper="p"):
+    return {"id": i, "source": source, "kind": kind, "paper": paper, "batch": None}
+
+
+GROUPING = {"mpea": "paper", "tamu_fcc": "dataset", "controlled_duplicates": "paper"}
 
 
 def problems(members, flags=(), records=None, marked=False):
     records = records or {i: rec(i) for i in members}
-    return eligibility.primary_set_problems(set(members), records, list(flags), marked)
+    return eligibility.primary_set_problems(set(members), records, list(flags), marked, grouping=GROUPING)
 
 
 def flag(kind, category, *ids):
@@ -53,6 +57,7 @@ def flag(kind, category, *ids):
     ("a model-recalled record", {1}, [], {1: rec(1, kind="model_recalled")}, False, "model-recalled"),
     ("a constructed record in an unmarked run", {1}, [], {1: rec(1, source="controlled_duplicates")}, False,
      "constructed"),
+    ("a record without a group", {1}, [], {1: rec(1, paper=None)}, False, "without a group"),
 ])
 def test_each_invariant_is_checked_on_the_primary_set(case, members, flags, records, marked, expected):
     got = problems(members, flags, records, marked)
@@ -178,6 +183,22 @@ def test_a_constructed_record_in_an_unmarked_run_is_refused_at_the_freeze(db, mo
     _refused(db, rid, "constructed")
 
 
+def test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze(db, monkeypatch):
+    """Step 7b (owner, 2026-10-06): invariant (7). The eligibility rule `group_unknown` switched off,
+    and the plan counting possible duplicates both (a choice the plan may make): the extract
+    records of answer rows 5-6, which have no DOI and so no group, would enter primary. The check on
+    the result finds them, from the primary grouping, and the freeze refuses."""
+    monkeypatch.setattr(eligibility, "has_group", lambda rec, st: True)
+    content = _rule(_extract_run(db), "possible_duplicate", None, "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "without a group")
+
+
+def test_a_texas_am_record_is_not_without_a_group():
+    """Grouped by dataset, a Texas A&M record has its group without a DOI; the check reads the plan's
+    grouping, not the DOI."""
+    assert problems({1}, [], {1: rec(1, source="tamu_fcc", paper=None)}) == []
+
+
 def test_a_valid_plan_freezes(db):
     """The reference plan on MPEA and the extract (marked) passes the check."""
     content = _extract_run(db)
diff --git a/tests/test_order_independence.py b/tests/test_order_independence.py
index 0940f89..df9f4ae 100644
--- a/tests/test_order_independence.py
+++ b/tests/test_order_independence.py
@@ -27,9 +27,12 @@ from hypocurate.sources.record import AdapterResult
 from test_eligibility import PLAN, cond
 from test_flags import rec
 
+# Step 7b: C (the extract record, no DOI) is grouped by dataset so that it keeps a group; identity is
+# unchanged (Checks' paper identity reads the DOI and reference only, never the grouping).
 GROUPING = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
-            {"source": "controlled_duplicates", "unit": "paper"}]
+            {"source": "controlled_duplicates", "unit": "dataset"}]
 D = "10.1016/j.test.2026.042"
+GROUPS = {g["source"]: g["unit"] for g in GROUPING}
 
 
 def plan_counting_possible_both():
@@ -66,7 +69,8 @@ def _decide_abc(plan, ids: dict, order: list):
     members = {k: el.members(r) for k, r in sets.items()}
     fp = checkpoints.freeze_fingerprint("p" * 64, by_id, members, sets, {})
     return ({k: {name[i]: r for i, r in rules.items()} for k, rules in sets.items()}, fp,
-            el.primary_set_problems(set(members["primary"]), by_id, flags, True))
+            el.primary_set_problems(set(members["primary"]), by_id, flags, True,
+                                    grouping=el.settings(plan).grouping))
 
 
 def test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order():
@@ -102,15 +106,15 @@ def test_a_chain_touching_a_conflict_enters_with_none_of_its_records():
 def test_the_freeze_check_allows_at_most_one_record_per_chain():
     """A and C in the primary set, B out: no single exact pair is wholly inside, but A and C are
     the same measurement through B."""
-    recs = {i: {"id": i, "source": "mpea", "kind": "measured"} for i in (1, 2, 3)}
+    recs = {i: {"id": i, "source": "mpea", "kind": "measured", "paper": "p", "batch": None} for i in (1, 2, 3)}
     flags = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
              {"id": 2, "kind": "exact_duplicate", "category": "identical values", "records": [2, 3]}]
-    problems = el.primary_set_problems({1, 3}, recs, flags, True)
+    problems = el.primary_set_problems({1, 3}, recs, flags, True, grouping=GROUPS)
     assert len(problems) == 1 and "exact duplicate" in problems[0]
-    assert el.primary_set_problems({1}, recs, flags, True) == []
+    assert el.primary_set_problems({1}, recs, flags, True, grouping=GROUPS) == []
     conflict = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
                 {"id": 2, "kind": "values_disagree", "category": "differ beyond tolerance", "records": [2, 3]}]
-    assert any("conflict" in p for p in el.primary_set_problems({1, 3}, recs, conflict, True))
+    assert any("conflict" in p for p in el.primary_set_problems({1, 3}, recs, conflict, True, grouping=GROUPS))
 
 
 # --- through the real pipeline ------------------------------------------------------------------
@@ -171,6 +175,9 @@ def test_permuted_ids_and_insertion_order_give_the_same_frozen_result(db, monkey
     results = [_permuted_run(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
     first = results[0]
     assert len(first[0]) > 1000 and first[1]["primary"]
+    # Step 7b: the set without the most influential paper is among those compared, and it removes a paper.
+    assert first[1]["without_most_influential_paper"] and \
+        first[1]["without_most_influential_paper"] != first[1]["primary"]
     for other in results[1:]:
         assert other[0] == first[0]  # every record's decision
         assert other[1] == first[1]  # the primary set and every sensitivity set
diff --git a/tests/test_permutation_stats.py b/tests/test_permutation_stats.py
index 52dafe1..973e54b 100644
--- a/tests/test_permutation_stats.py
+++ b/tests/test_permutation_stats.py
@@ -73,6 +73,8 @@ def test_permuted_ids_and_insertion_order_give_identical_results(db, monkeypatch
     results = [_permuted_analysis(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
     first = results[0]
     assert first[0]["analyses"][0]["estimate"] is not None and len(first[2]) == 2 * len(first[1])
+    # Step 7b: the set without the most influential paper is analysed and compared too.
+    assert "sensitivity:without_most_influential_paper" in {e["analysis"] for e in first[0]["analyses"]}
     for other in results[1:]:
         assert other[0] == first[0]  # the record of statistical significance and the decision, seeds included
         assert other[1] == first[1]  # every analysis result
diff --git a/tests/test_plan.py b/tests/test_plan.py
index 5aac794..000a1ba 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -40,7 +40,7 @@ def test_the_reference_plan_is_the_default_plan_under_the_owners_decisions():
     assert ref["sensitivity_analyses"] == [
         "no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
         "source_only_assignments", "scope_not_confirmed_included", "possible_duplicates_separate",
-        "conflicts_survivor_value"]
+        "conflicts_survivor_value", "without_most_influential_paper"]  # the ninth: owner, 2026-10-06 (step 7b)
     assert ref["eligibility_rules"] == [
         {"flag_kind": "invalid_value", "rule": "invalid_value"},
         {"flag_kind": "exact_duplicate", "rule": "duplicate_counted_once"},
diff --git a/tests/test_reference_numbers.py b/tests/test_reference_numbers.py
index b5246ad..a6533a8 100644
--- a/tests/test_reference_numbers.py
+++ b/tests/test_reference_numbers.py
@@ -217,3 +217,67 @@ def test_every_reference_result_matches_the_reference_implementation(runs, key):
     for mine, theirs in ((got["estimate"], expected["k"]), (got["std_error"], expected["se"]),
                          (got["p_value"], expected["p"])):
         assert (mine is None and theirs is None) or math.isclose(mine, theirs, rel_tol=1e-9)
+
+
+# --- step 7b: the set without the most influential paper (owner, 2026-10-06) ------------------------
+
+INFLUENCE = "sensitivity:without_most_influential_paper"
+
+
+def _information_by_group(rows):
+    """Test-side I_g (pandas; register 'effective_papers'), independent of the package."""
+    f = rs.frame(rows)
+    dev = f["x"] - f.groupby("alloy")["x"].transform("mean")
+    return (dev ** 2).groupby(f["group"]).sum()
+
+
+def test_the_set_without_the_most_influential_paper(runs):
+    """The paper removed is the one test-side pandas finds with the largest I_g on the pooled set
+    (no tie on these data); the set is the primary set minus exactly its records; its result matches
+    the independent implementations; it is descriptive and leaves the decision as the pooled result
+    alone gives it."""
+    from hypocurate.pipeline import statistics as st
+    ref = runs["reference"]
+    data = ref["data"]
+    info = _information_by_group(_rows(data, "primary")).sort_values(ascending=False)
+    assert info.iloc[0] > info.iloc[1] * (1 + 1e-6)  # a clear maximum: the tie-break is not used here
+    removed = info.index[0]
+    assert info.iloc[0] / info.sum() == pytest.approx(ref["analyses"]["pooled"]["counts"]["largest_paper_share"],
+                                                       rel=1e-12)
+    by_id = {r["id"]: r for r in data["records"]}
+    group_of = lambda r: "dataset:tamu_fcc" if r["source"] == "tamu_fcc" else f"paper:{r['paper']}"  # noqa: E731
+    assert set(data["sets"]["without_most_influential_paper"]) == {
+        i for i in data["sets"]["primary"] if group_of(by_id[i]) != removed}
+    got = ref["analyses"][INFLUENCE]
+    rows = _rows(data, "without_most_influential_paper")
+    decimal = rs.fit_informative(rows)
+    assert got["counts"]["n_groups_informative"] == decimal["groups_informative"]
+    assert got["df"] == decimal["df"]
+    for mine, theirs in ((got["estimate"], decimal["k"]), (got["std_error"], decimal["se"]),
+                         (got["p_value"], decimal["p"])):
+        assert math.isclose(mine, theirs, rel_tol=1e-9)
+    effective, share = rs.effective_papers(rows)
+    assert math.isclose(got["counts"]["effective_papers"], effective, rel_tol=1e-9)
+    assert math.isclose(got["counts"]["largest_paper_share"], share, rel_tol=1e-9)
+    assert got["label"] is None and "verdict" not in got
+    pooled = ref["analyses"]["pooled"]
+    assert ref["out"]["decision"] == st.decision(pooled, reference_plan(1), ref["out"]["freeze_fingerprint"])
+
+
+# Step 7b values on the reference data, as reported to the owner (2026-10-06); not yet approved as
+# reference numbers. Records, alloys, groups, residual df, k, standard error, p-value (as stated).
+INFLUENCE_REPORTED = (89, 22, 19, 66, "393.5", "90.5", "1.9e-4")
+
+
+def test_the_set_without_the_most_influential_paper_as_reported(runs):
+    ref = runs["reference"]
+    got = ref["analyses"][INFLUENCE]
+    check_approved(got, INFLUENCE_REPORTED)
+    c = got["counts"]
+    assert (c["n_groups_informative"], got["df"]) == (19, 18)
+    assert within(c["effective_papers"], "3.24") and within(c["largest_paper_share"], "0.521")
+    pooled = ref["analyses"]["pooled"]["counts"]
+    removed = set(ref["data"]["sets"]["primary"]) - set(ref["data"]["sets"]["without_most_influential_paper"])
+    by_id = {r["id"]: r for r in ref["data"]["records"]}
+    assert len(removed) == 8 and len({same_alloy_key(by_id[i]["composition"], 1) for i in removed}) == 1
+    assert pooled["n_records"] - len(removed) == c["n_records"]
diff --git a/tests/test_reference_sets.py b/tests/test_reference_sets.py
index 317e847..90eb8d4 100644
--- a/tests/test_reference_sets.py
+++ b/tests/test_reference_sets.py
@@ -127,6 +127,8 @@ def _direct(key, run, i):
         "scope_not_confirmed_included": primary == "scope_not_confirmed",
         "possible_duplicates_separate": in_flag("possible_duplicate"),
         "conflicts_survivor_value": in_flag("values_disagree"),
+        # Step 7b: the records of the removed paper (checked to be one whole paper below).
+        el.INFLUENCE_KEY: run["rules"][el.INFLUENCE_KEY][i] == el.INFLUENCE_RULE,
     }[key]
 
 
@@ -153,6 +155,14 @@ def _check_one_change(run):
                 # decisions change for records regrouped by the set's own flags (direct, above).
                 assert {primary[i], other[i]} <= {"in_scope", "single_grain_size", "duplicate_counted_once"}
         assert run["sets"][key] == {i for i, r in other.items() if r == "in_scope"}
+        if key == el.INFLUENCE_KEY:
+            # Step 7b: exactly the primary members of one paper (primary grouping) leave; nothing cascades.
+            assert differing == direct and {primary[i] for i in differing} == {"in_scope"}
+            st = el.settings(plan)
+            removed_groups = {el.group(run["conditions"][i], st) for i in differing}
+            assert len(removed_groups) == 1
+            assert differing == {i for i in run["sets"]["primary"]
+                                 if el.group(run["conditions"][i], st) in removed_groups}
         differing_total[key] = len(differing)
     return differing_total
 
@@ -162,7 +172,8 @@ def test_each_sensitivity_set_differs_from_primary_only_by_its_named_change(refe
     differing = _check_one_change(reference)
     assert differing["six_batches_as_groups"] == 0
     assert reference["sets"]["six_batches_as_groups"] == reference["sets"]["primary"]
-    for key in ("tension_and_compression", "source_only_assignments", "scope_not_confirmed_included"):
+    for key in ("tension_and_compression", "source_only_assignments", "scope_not_confirmed_included",
+                "without_most_influential_paper"):
         assert differing[key] > 0, key
 
 
@@ -170,6 +181,11 @@ def test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_a
     """The same, on a marked run with the controlled extract, where possible duplicates and
     conflicts exist."""
     differing = _check_one_change(with_extract)
-    for key in ("possible_duplicates_separate", "conflicts_survivor_value", "scope_not_confirmed_included"):
+    for key in ("conflicts_survivor_value", "scope_not_confirmed_included", "without_most_influential_paper"):
         assert differing[key] > 0, key
+    # Step 7b (owner, 2026-10-06): the extract's only possible duplicates with an eligible twin (rows 5-6)
+    # have no DOI, so no group: rule 5 excludes them in every set, before identity, and this set now
+    # equals primary here. Counting possible duplicates separately is still exercised where both records
+    # have a group (test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule).
+    assert differing["possible_duplicates_separate"] == 0
     assert set(el.SENSITIVITY_CHANGES) == set(reference_plan(1)["sensitivity_analyses"])
```

## 5. Register and answer-file diffs

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index ce85b57..3f25fc9 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -236,7 +236,7 @@
     "key": "fixed_minimums",
     "name": "Fixed minimums for data sufficiency",
     "state": "in_force",
-    "statement": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent informative papers (entry 'informative_groups') and 10 residual degrees of freedom, counted on the records a fit uses. All four must be met.",
+    "statement": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent informative papers (entry 'informative_groups') and 10 residual degrees of freedom, counted on the records a fit uses. All four must be met. The paper minimum stays a count of informative papers, not the effective number of papers (entry 'effective_papers'); final for sprint 1 (owner, 2026-10-06).",
     "value": {
       "text": "30 records; 5 alloys; 10 papers; 10 residual degrees of freedom",
       "unit": null
@@ -290,6 +290,12 @@
         "from": "2026-10-05",
         "to": "2026-10-06",
         "note": "The paper minimum counts informative papers only (owner, 2026-10-06)."
+      },
+      {
+        "value": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent informative papers (entry 'informative_groups') and 10 residual degrees of freedom, counted on the records a fit uses. All four must be met.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Step 7b (owner, 2026-10-06): recorded as final for sprint 1; the values are unchanged."
       }
     ],
     "notes": [
@@ -4296,7 +4302,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -4337,11 +4343,13 @@
             "conflict_unresolved",
             "duplicate_counted_once",
             "excluded_by_rule",
+            "group_unknown",
             "identity_unresolved",
             "in_scope",
             "invalid_value",
             "missing_value",
             "model_recalled",
+            "most_influential_paper",
             "out_of_scope",
             "scope_not_confirmed",
             "single_grain_size"
@@ -4358,7 +4366,8 @@
             "scope_not_confirmed_included",
             "six_batches_as_groups",
             "source_only_assignments",
-            "tension_and_compression"
+            "tension_and_compression",
+            "without_most_influential_paper"
           ]
         },
         {
@@ -4426,6 +4435,12 @@
         "from": "2026-10-05",
         "to": "2026-10-05",
         "note": "Step 7 (owner, 2026-10-05)."
+      },
+      {
+        "value": "eligibility rules without 'group_unknown' and 'most_influential_paper'; sensitivity keys without 'without_most_influential_paper'",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 7b additions approved by the owner on 2026-10-06."
       }
     ],
     "notes": [],
@@ -4479,9 +4494,9 @@
     "key": "eligibility_rule_order",
     "name": "One eligibility rule per record, in a fixed order",
     "state": "in_force",
-    "statement": "Every record gets one rule, the first that applies: model-recalled; invalid value; out of scope; missing value; scope not confirmed; excluded by a rule; identity (ambiguous group, conflict, or not the survivor of a duplicate group); fewer than two grain sizes for its alloy; otherwise eligible. Duplicates are resolved before grain sizes are counted.",
+    "statement": "Every record gets one rule, the first that applies: model-recalled; invalid value; out of scope; missing value; no group under the set's grouping; scope not confirmed; excluded by a rule; identity (ambiguous group, conflict, or not the survivor of a duplicate group); fewer than two grain sizes for its alloy; otherwise eligible. Duplicates are resolved before grain sizes are counted. In the set without the most influential paper, that paper's primary members get 'most_influential_paper' (entry 'most_influential_paper_set').",
     "value": {
-      "text": "model_recalled, invalid_value, out_of_scope, missing_value, scope_not_confirmed, excluded_by_rule, identity, single_grain_size, in_scope",
+      "text": "model_recalled, invalid_value, out_of_scope, missing_value, group_unknown, scope_not_confirmed, excluded_by_rule, identity, single_grain_size, in_scope",
       "unit": null
     },
     "category": "data_handling",
@@ -4492,7 +4507,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -4509,7 +4524,14 @@
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Every record gets one rule, the first that applies: model-recalled; invalid value; out of scope; missing value; scope not confirmed; excluded by a rule; identity (ambiguous group, conflict, or not the survivor of a duplicate group); fewer than two grain sizes for its alloy; otherwise eligible. Duplicates are resolved before grain sizes are counted.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 7b (owner, 2026-10-06): rule 5, 'group_unknown', added after missing value."
+      }
+    ],
     "notes": [
       "Confirmation (2026-10-06): within the identity rule, definite relationships (exact duplicates, conflicts) are applied before the plan's possible-duplicate choice, which then applies to what remains.",
       "Confirmation round 2 (2026-10-06): the identity rule decides whole groups, never flag by flag: records linked by a chain of exact pairs are one measurement (one survivor); a chain touching a definite conflict follows the plan's conflict rule as one group; then the possible-duplicate choice per connected possible group. No decision depends on record ids, flag ids or insertion order."
@@ -4524,7 +4546,9 @@
       "tests/test_order_independence.py::test_a_chain_touching_a_conflict_enters_with_none_of_its_records",
       "tests/test_order_independence.py::test_permuted_ids_and_insertion_order_give_the_same_frozen_result",
       "tests/test_order_independence.py::test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order",
-      "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule"
+      "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule",
+      "tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value",
+      "tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor"
     ]
   },
   {
@@ -4595,9 +4619,9 @@
     "key": "sensitivity_one_change",
     "name": "Each sensitivity analysis changes one thing",
     "state": "in_force",
-    "statement": "Each sensitivity set differs from the primary set in exactly one named respect, and every other rule applies unchanged. The reference and default plans name eight: no exclusions; tension and compression together; six batches for Texas A&M; the same-alloy rule at 1 at.%; source-only values; scope not confirmed included; possible duplicates separate; conflicts by the survivor value. Sensitivity results are descriptive, never change the verdict, and no adjustment is made for there being eight.",
+    "statement": "Each sensitivity set differs from the primary set in exactly one named respect, and every other rule applies unchanged. The reference and default plans name nine: no exclusions; tension and compression together; six batches for Texas A&M; the same-alloy rule at 1 at.%; source-only values; scope not confirmed included; possible duplicates separate; conflicts by the survivor value; without the most influential paper. Sensitivity results are descriptive, never change the verdict, and no adjustment is made for there being nine.",
     "value": {
-      "text": "eight sets, one change each",
+      "text": "nine sets, one change each",
       "unit": null
     },
     "category": "statistical",
@@ -4608,7 +4632,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -4628,7 +4652,14 @@
       ],
       "note": "What each key changes is fixed by the key itself, not by a number in the plan."
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Each sensitivity set differs from the primary set in exactly one named respect, and every other rule applies unchanged. The reference and default plans name eight: no exclusions; tension and compression together; six batches for Texas A&M; the same-alloy rule at 1 at.%; source-only values; scope not confirmed included; possible duplicates separate; conflicts by the survivor value. Sensitivity results are descriptive, never change the verdict, and no adjustment is made for there being eight.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Eight sets until step 7b (owner, 2026-10-06), which added 'without_most_influential_paper'."
+      }
+    ],
     "notes": [
       "The reference script's 'discretionary removals' analysis (PRD 10: 438 ± 67 with four records removed) is not carried over: its records were chosen after seeing outcomes, so it cannot be named in a plan locked before the data (owner, 2026-10-05).",
       "Related: 'no_multiplicity_adjustment'.",
@@ -4639,7 +4670,8 @@
       "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change",
       "tests/test_reference_sets.py::test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts",
       "tests/test_sensitivity_matching.py::test_the_coarser_same_alloy_rule_recomputes_the_duplicates",
-      "tests/test_sensitivity_matching.py::test_the_one_change_rule_holds_with_recomputed_matching_flags"
+      "tests/test_sensitivity_matching.py::test_the_one_change_rule_holds_with_recomputed_matching_flags",
+      "tests/test_influential_paper.py::test_it_differs_from_primary_in_exactly_this_one_respect"
     ]
   },
   {
@@ -5009,9 +5041,9 @@
     "key": "primary_set_invariants",
     "name": "What no plan can ever do to the primary set",
     "state": "in_force",
-    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) No record connected to a definite conflict ever enters, under any plan: not both records, not one. That includes a record linked by exact duplicates to a record in conflict (the whole connected group stays out). A survivor's value is counted only in the sensitivity analysis 'conflicts_survivor_value'. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The one plan choice that remains: possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
+    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) No record connected to a definite conflict ever enters, under any plan: not both records, not one. That includes a record linked by exact duplicates to a record in conflict (the whole connected group stays out). A survivor's value is counted only in the sensitivity analysis 'conflicts_survivor_value'. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. (7) A record without a group under the plan's grouping never enters (no group is invented; entry 'records_without_group'). A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze; (7) by the eligibility rule 'group_unknown'. The one plan choice that remains: possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (7), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind, source and, for (7), group under the plan's grouping, and refuses the freeze, logging the refusal, if any fails.",
     "value": {
-      "text": "six things no plan can do",
+      "text": "seven things no plan can do",
       "unit": null
     },
     "category": "data_handling",
@@ -5050,9 +5082,12 @@
         },
         {
           "ref": "python:hypocurate.pipeline.eligibility:primary_set_problems"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:has_group"
         }
       ],
-      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…], tests/test_conflict_policy.py (the reviewer's chain, through the pipeline and at the freeze); (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused. The result check at the freeze: test_each_invariant_is_checked_on_the_primary_set (all six) and the end-to-end tests in tests/test_freeze_invariants.py."
+      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…], tests/test_conflict_policy.py (the reviewer's chain, through the pipeline and at the freeze); (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused. The result check at the freeze: test_each_invariant_is_checked_on_the_primary_set (all six) and the end-to-end tests in tests/test_freeze_invariants.py. (7) test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule, test_each_invariant_is_checked_on_the_primary_set[a record without a group…], test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze."
     },
     "history": [
       {
@@ -5066,6 +5101,12 @@
         "from": "2026-10-06",
         "to": "2026-10-06",
         "note": "Before the third confirmation: point (2) let a plan choose the survivor's value counted once, and the freeze check refused only more than one record of a conflict group."
+      },
+      {
+        "value": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) No record connected to a definite conflict ever enters, under any plan: not both records, not one. That includes a record linked by exact duplicates to a record in conflict (the whole connected group stays out). A survivor's value is counted only in the sensitivity analysis 'conflicts_survivor_value'. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The one plan choice that remains: possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Six invariants until step 7b (owner, 2026-10-06): point (7) added."
       }
     ],
     "notes": [
@@ -5099,7 +5140,9 @@
       "tests/test_mixed_groups.py::test_the_pipeline_never_admits_the_exact_duplicate_twice",
       "tests/test_order_independence.py::test_the_freeze_check_allows_at_most_one_record_per_chain",
       "tests/test_plan.py::test_invalid_plans_are_refused",
-      "tests/test_plan.py::test_the_plan_choices_that_remain"
+      "tests/test_plan.py::test_the_plan_choices_that_remain",
+      "tests/test_freeze_invariants.py::test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze",
+      "tests/test_eligibility.py::test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule"
     ]
   },
   {
@@ -5668,42 +5711,67 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "open decision: Open: what a fit does with a frozen record that has no group (a literature record whose paper is not known). Until decided, code fails closed and invents no group: the pooled analysis refuses the analysis stage (logged, 'records_without_group'); a per-source or sensitivity analysis is reported as not analysed, with the count, and nothing is stored for it.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Open from the step 7 build; decided by the owner in step 7b."
+      }
+    ],
     "notes": [
-      "Second-model review (2026-10-06): failing closed is safe; keep the explicit skipped-analysis record and invent no singleton papers. Still open: whether a permitted coefficient-only result should remain available when grouping is missing."
+      "Second-model review (2026-10-06): failing closed is safe; keep the explicit skipped-analysis record and invent no singleton papers. Still open: whether a permitted coefficient-only result should remain available when grouping is missing.",
+      "Step 7b (owner, 2026-10-06): decided at inclusion; the reviewer's question (a coefficient-only result when grouping is missing) no longer arises, since such a record never reaches a fit."
     ],
     "key": "records_without_group",
     "name": "Records without a group in a fit",
-    "state": "open",
-    "statement": "Open: what a fit does with a frozen record that has no group (a literature record whose paper is not known). Until decided, code fails closed and invents no group: the pooled analysis refuses the analysis stage (logged, 'records_without_group'); a per-source or sensitivity analysis is reported as not analysed, with the count, and nothing is stored for it.",
-    "value": null,
-    "decided": null,
+    "state": "in_force",
+    "statement": "A record with no group under a set's grouping (a paper-grouped record without a DOI, so its paper is not known; a batch-grouped record without a batch) is stored and shown but is not eligible: Inclusion gives it its own rule, 'group_unknown', rule 5 in the order (after missing value, before scope not confirmed, the menu exclusions, identity and the grain-size count), judged in each set under that set's own grouping. No group is ever invented. The dataset freeze also refuses a primary set holding such a record (entry 'primary_set_invariants', point 7). The statistics therefore never receive one in normal runs; their refusal (pooled refuses, a descriptive analysis is reported as not analysed) is kept as a backstop.",
+    "value": {
+      "text": "not eligible at inclusion, rule 'group_unknown' (rule 5); no group invented",
+      "unit": null
+    },
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
     "category": "statistical",
-    "affects": "Sensitivity sets that admit records without a paper (in sprint 1 only the controlled extract's, in 'possible_duplicates_separate' of a marked run); no record in the reference sets lacks a group.",
-    "reason": "A clustered standard error needs every record in a group; register 'paper_grouping_by_doi' says no group is invented.",
+    "affects": "Eligibility in every set; the extract's records without a paper (answer rows 5-6) are not eligible in any set. No record of the reference sets lacks a group, so no reference number changes.",
+    "reason": "A clustered standard error needs every record in a group; register 'paper_grouping_by_doi' says no group is invented. Deciding it at inclusion keeps the record visible with a stated reason and keeps every analysis computable.",
     "evidence": [
-      "Found while building step 7 (2026-10-06): the marked run's 'possible_duplicates_separate' set holds two extract records without a DOI."
+      "Found while building step 7 (2026-10-06): the marked run's 'possible_duplicates_separate' set holds two extract records without a DOI.",
+      "Owner's decision, 2026-10-06 (step 7b brief)."
     ],
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:NO_GROUP_RULE",
+          "equals": "group_unknown"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:has_group"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:primary_set_problems"
+        },
         {
           "ref": "python:hypocurate.pipeline.analysis:RecordsWithoutGroup"
         }
       ],
-      "done": "Fail closed: pooled refuses; a descriptive analysis is reported as not analysed with the count.",
-      "pending": "The owner's decision.",
-      "step": 8,
-      "note": null
+      "note": "The order: owner, 2026-10-06 (step 7b, question 1). Before identity, so that a record without a group is never chosen as a survivor and never pushes out its grouped twin."
     },
     "tests": [
-      "tests/test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one",
-      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates"
-    ],
-    "pending": {
-      "by": "owner",
-      "before_step": 8
-    }
+      "tests/test_eligibility.py::test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule",
+      "tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value",
+      "tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor",
+      "tests/test_eligibility.py::test_the_group_is_judged_under_each_sets_own_grouping",
+      "tests/test_eligibility.py::test_alloys_are_counted_on_records_with_a_group",
+      "tests/test_freeze_invariants.py::test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze",
+      "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
+      "tests/test_analysis_stage.py::test_the_statistics_backstop_is_not_reached_in_a_normal_run",
+      "tests/test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one"
+    ]
   },
   {
     "sensitivity": null,
@@ -5945,7 +6013,8 @@
     ],
     "history": [],
     "notes": [
-      "Second-model confirmation (2026-10-06): a measure of how concentrated the within-alloy predictor contrast is; not an estimate of independent sample size; passing the floor of 2 does not establish reliable inference, and it supplies no replacement degrees of freedom."
+      "Second-model confirmation (2026-10-06): a measure of how concentrated the within-alloy predictor contrast is; not an estimate of independent sample size; passing the floor of 2 does not establish reliable inference, and it supplies no replacement degrees of freedom.",
+      "Step 7b (owner, 2026-10-06): I_g also chooses the paper left out of the sensitivity set 'without_most_influential_paper' (entry 'most_influential_paper_set'), through the same function ('statistics.slope_information'). The paper minimum stays a count (entry 'fixed_minimums')."
     ]
   },
   {
@@ -5993,5 +6062,77 @@
     ],
     "history": [],
     "notes": []
+  },
+  {
+    "key": "most_influential_paper_set",
+    "name": "Sensitivity set without the most influential paper",
+    "state": "in_force",
+    "statement": "The sensitivity set 'without_most_influential_paper' is the primary set minus every record of the paper (the group under the plan's grouping) holding the largest share of slope information, I_g / Σ I_g, with I_g the paper's sum of squared within-alloy deviations of the transformed grain size (entry 'effective_papers'), computed on the primary set's records. The paper is chosen by code at Inclusion from grain sizes, alloys and groups only, never from outcome values (Inclusion receives none). Shares within the numerical zero (RELATIVE_ZERO, 1e-10) of the largest are tied; a tie is broken by each tied paper's earliest record under the plan's survivor source order, then the lowest row in the source file, then the stable identity (source-version fingerprint, origin key, item index), never a database id or an order. The removed records get the rule 'most_influential_paper' in that set only; it differs from the primary set in exactly this one respect (alloys left with one grain size are the fit's own 'not used in this fit', as in every set). Without any slope information nothing is removed. Descriptive only; it never changes the verdict.",
+    "value": {
+      "text": "primary minus the paper with the largest share of slope information",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "One more sensitivity analysis in every run whose plan names it (the default and reference plans). The plan's fingerprint, so the freeze fingerprint and the calibration seeds of every run, change.",
+    "reason": "The pooled result's largest paper share (38.7% on the reference data) shows the evidence is concentrated; this set shows the result without that paper.",
+    "evidence": [
+      "Owner's decision, 2026-10-06 (step 7b brief); tie-break: step 7b planning, question 3."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:INFLUENCE_KEY",
+          "equals": "without_most_influential_paper"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:INFLUENCE_RULE",
+          "equals": "most_influential_paper"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:most_influential"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:influence_tie_key"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:slope_information"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:RELATIVE_ZERO",
+          "equals": 1e-10
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:SENSITIVITY_ANALYSES"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_influential_paper.py::test_the_slope_information_is_the_owners_formula",
+      "tests/test_influential_paper.py::test_the_design_uses_the_same_slope_information",
+      "tests/test_influential_paper.py::test_the_set_is_primary_minus_the_paper_with_the_largest_share",
+      "tests/test_influential_paper.py::test_it_differs_from_primary_in_exactly_this_one_respect",
+      "tests/test_influential_paper.py::test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order",
+      "tests/test_influential_paper.py::test_a_tie_follows_the_survivor_source_order_before_the_row",
+      "tests/test_influential_paper.py::test_the_choice_uses_no_outcome_value",
+      "tests/test_influential_paper.py::test_without_any_slope_information_nothing_is_removed",
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change",
+      "tests/test_reference_numbers.py::test_the_set_without_the_most_influential_paper"
+    ],
+    "history": [],
+    "notes": [
+      "Like every sensitivity set: descriptive, never changes the verdict, no multiplicity adjustment (entries 'sensitivity_one_change', 'no_multiplicity_adjustment')."
+    ]
   }
 ]
diff --git a/tests/fixtures/controlled_duplicates/build.py b/tests/fixtures/controlled_duplicates/build.py
index 6f950c7..cc13a4b 100644
--- a/tests/fixtures/controlled_duplicates/build.py
+++ b/tests/fixtures/controlled_duplicates/build.py
@@ -103,13 +103,15 @@ CASES = {
         pair=BOTH_CARRY_PAPER,
         explanation="Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition.",
     ),
+    # Owner, 2026-10-06 (step 7b): a record without a paper reference has no group, so it is not
+    # eligible (rule 'group_unknown', before identity), in the primary set and in every sensitivity set.
     "possible_duplicate_unknown_paper": dict(
         duplicate_status="possible_duplicate",
         prd_class="Possible duplicate that cannot be resolved",
-        primary_analysis="counted once",
-        sensitivity_analysis="both counted separately",
-        pair=ONLY_MPEA_CARRIES_PAPER,
-        explanation="Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed.",
+        primary_analysis="not eligible: no group (paper reference missing)",
+        sensitivity_analysis="none",
+        pair=ONLY_MPEA_CARRIES_PAPER + "; this record is not eligible in any case (no group: the paper reference is missing)",
+        explanation="Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed. Without a paper reference it has no group for the paper-grouped uncertainty, so it is not eligible in the primary analysis or in any sensitivity analysis; no group is invented (owner, 2026-10-06).",
     ),
     "missing_test_condition": dict(
         duplicate_status="possible_duplicate",
diff --git a/tests/fixtures/controlled_duplicates/truth.csv b/tests/fixtures/controlled_duplicates/truth.csv
index 47cccc7..d4e53e7 100644
--- a/tests/fixtures/controlled_duplicates/truth.csv
+++ b/tests/fixtures/controlled_duplicates/truth.csv
@@ -3,8 +3,8 @@ extract_row,case,mpea_row,mpea_reference_id,mpea_doi,changed_columns,duplicate_s
 2,exact_duplicate_verbatim,812,144,10.1016/j.ijplas.2018.10.005,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 812,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
 3,exact_duplicate_renamed_alloy,1316,252,10.1007/s11661-019-05231-y,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1316,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
 4,exact_duplicate_renamed_alloy,1007,208,10.1016/j.actamat.2019.04.017,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1007,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
-5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 998,rule 1: only the MPEA record carries the original paper reference (DOI),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
-6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 1085,rule 1: only the MPEA record carries the original paper reference (DOI),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
+5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,not eligible: no group (paper reference missing),none,same as under the reference plan,MPEA row 998,rule 1: only the MPEA record carries the original paper reference (DOI); this record is not eligible in any case (no group: the paper reference is missing),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed. Without a paper reference it has no group for the paper-grouped uncertainty, so it is not eligible in the primary analysis or in any sensitivity analysis; no group is invented (owner, 2026-10-06)."
+6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,not eligible: no group (paper reference missing),none,same as under the reference plan,MPEA row 1085,rule 1: only the MPEA record carries the original paper reference (DOI); this record is not eligible in any case (no group: the paper reference is missing),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed. Without a paper reference it has no group for the paper-grouped uncertainty, so it is not eligible in the primary analysis or in any sensitivity analysis; no group is invented (owner, 2026-10-06)."
 7,conflict_value_differs,1278,248,10.1016/j.msea.2019.138039,PROPERTY: YS (MPa),conflict,Conflicting reports of the same measurement: the values differ beyond the tolerance,yes,no,neither enters: conflict unresolved,counted once in conflicts_survivor_value,same as under the reference plan,none: neither enters the primary analysis,conflict: the values differ beyond the tolerance and code does not choose between them; in the sensitivity analysis 'conflicts_survivor_value' the pair is counted once by the survivor rule: rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions reported by two sources, but yield strength is 30% higher: conflicting reports of the same measurement. Both are kept and flagged, and neither enters the primary analysis (owner, 2026-10-05). Matching alloy and grain size alone would not make them the same measurement."
 8,conflict_value_differs,986,204,10.1016/j.intermet.2019.106477,PROPERTY: YS (MPa),conflict,Conflicting reports of the same measurement: the values differ beyond the tolerance,yes,no,neither enters: conflict unresolved,counted once in conflicts_survivor_value,same as under the reference plan,none: neither enters the primary analysis,conflict: the values differ beyond the tolerance and code does not choose between them; in the sensitivity analysis 'conflicts_survivor_value' the pair is counted once by the survivor rule: rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions reported by two sources, but yield strength is 30% higher: conflicting reports of the same measurement. Both are kept and flagged, and neither enters the primary analysis (owner, 2026-10-05). Matching alloy and grain size alone would not make them the same measurement."
 9,not_duplicate_other_paper,1035,211,10.1016/j.msea.2019.04.025,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
```

The register edits were made by this script:

```python
"""Step 7b register edits (owner, 2026-10-06). Earlier wording goes to each entry's history."""
import json
from pathlib import Path

PATH = Path("/workspaces/hypocurate/hypocurate/assumptions.json")
entries = json.loads(PATH.read_text(encoding="utf-8"))
by = {e["key"]: e for e in entries}
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-06"}
DAY = "2026-10-06"


def reword(e, statement, note, start):
    e["history"].append({"value": e["statement"], "from": start, "to": DAY, "note": note})
    e["statement"] = statement
    e["decided"] = dict(OWNER)


# 1. records_without_group: open -> in force.
e = by["records_without_group"]
old = e["statement"]
e.update(state="in_force", decided=dict(OWNER), value={
    "text": "not eligible at inclusion, rule 'group_unknown' (rule 5); no group invented", "unit": None})
e.pop("pending")
e["statement"] = (
    "A record with no group under a set's grouping (a paper-grouped record without a DOI, so its paper is not "
    "known; a batch-grouped record without a batch) is stored and shown but is not eligible: Inclusion gives it "
    "its own rule, 'group_unknown', rule 5 in the order (after missing value, before scope not confirmed, the "
    "menu exclusions, identity and the grain-size count), judged in each set under that set's own grouping. No "
    "group is ever invented. The dataset freeze also refuses a primary set holding such a record (entry "
    "'primary_set_invariants', point 7). The statistics therefore never receive one in normal runs; their "
    "refusal (pooled refuses, a descriptive analysis is reported as not analysed) is kept as a backstop.")
e["affects"] = ("Eligibility in every set; the extract's records without a paper (answer rows 5-6) are not eligible "
                "in any set. No record of the reference sets lacks a group, so no reference number changes.")
e["reason"] = ("A clustered standard error needs every record in a group; register 'paper_grouping_by_doi' says "
               "no group is invented. Deciding it at inclusion keeps the record visible with a stated reason and "
               "keeps every analysis computable.")
e["evidence"].append("Owner's decision, 2026-10-06 (step 7b brief).")
e["history"].append({"value": "open decision: " + old, "from": DAY, "to": DAY,
                     "note": "Open from the step 7 build; decided by the owner in step 7b."})
e["applied"] = {"status": "yes", "settings": [
    {"ref": "python:hypocurate.pipeline.eligibility:NO_GROUP_RULE", "equals": "group_unknown"},
    {"ref": "python:hypocurate.pipeline.eligibility:has_group"},
    {"ref": "python:hypocurate.pipeline.eligibility:primary_set_problems"},
    {"ref": "python:hypocurate.pipeline.analysis:RecordsWithoutGroup"}],
    "note": "The order: owner, 2026-10-06 (step 7b, question 1). Before identity, so that a record without a group is "
            "never chosen as a survivor and never pushes out its grouped twin."}
e["notes"].append("Step 7b (owner, 2026-10-06): decided at inclusion; the reviewer's question (a coefficient-only "
                  "result when grouping is missing) no longer arises, since such a record never reaches a fit.")
e["tests"] = [
    "tests/test_eligibility.py::test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule",
    "tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value",
    "tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor",
    "tests/test_eligibility.py::test_the_group_is_judged_under_each_sets_own_grouping",
    "tests/test_eligibility.py::test_alloys_are_counted_on_records_with_a_group",
    "tests/test_freeze_invariants.py::test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze",
    "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
    "tests/test_analysis_stage.py::test_the_statistics_backstop_is_not_reached_in_a_normal_run",
    "tests/test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one",
]

# 2. eligibility_rule_order.
e = by["eligibility_rule_order"]
reword(e, "Every record gets one rule, the first that applies: model-recalled; invalid value; out of scope; missing "
          "value; no group under the set's grouping; scope not confirmed; excluded by a rule; identity (ambiguous "
          "group, conflict, or not the survivor of a duplicate group); fewer than two grain sizes for its alloy; "
          "otherwise eligible. Duplicates are resolved before grain sizes are counted. In the set without the most "
          "influential paper, that paper's primary members get 'most_influential_paper' (entry "
          "'most_influential_paper_set').",
       "Step 7b (owner, 2026-10-06): rule 5, 'group_unknown', added after missing value.", "2026-10-05")
e["value"]["text"] = ("model_recalled, invalid_value, out_of_scope, missing_value, group_unknown, scope_not_confirmed, "
                      "excluded_by_rule, identity, single_grain_size, in_scope")
e["tests"] += ["tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value",
               "tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor"]

# 3. code_vocabularies: the lists change, the statement does not.
e = by["code_vocabularies"]
e["history"].append({"value": "eligibility rules without 'group_unknown' and 'most_influential_paper'; sensitivity "
                              "keys without 'without_most_influential_paper'",
                     "from": "2026-10-05", "to": DAY, "note": "Step 7b additions approved by the owner on 2026-10-06."})
e["decided"] = dict(OWNER)
for s in e["applied"]["settings"]:
    if s["ref"].endswith(":ELIGIBILITY_RULES"):
        s["equals"] = sorted(s["equals"] + ["group_unknown", "most_influential_paper"])
    if s["ref"].endswith(":SENSITIVITY_KEYS"):
        s["equals"] = sorted(s["equals"] + ["without_most_influential_paper"])

# 4. sensitivity_one_change: nine sets.
e = by["sensitivity_one_change"]
reword(e, "Each sensitivity set differs from the primary set in exactly one named respect, and every other rule "
          "applies unchanged. The reference and default plans name nine: no exclusions; tension and compression "
          "together; six batches for Texas A&M; the same-alloy rule at 1 at.%; source-only values; scope not "
          "confirmed included; possible duplicates separate; conflicts by the survivor value; without the most "
          "influential paper. Sensitivity results are descriptive, never change the verdict, and no adjustment is "
          "made for there being nine.",
       "Eight sets until step 7b (owner, 2026-10-06), which added 'without_most_influential_paper'.", "2026-10-05")
e["value"]["text"] = "nine sets, one change each"
e["tests"] += ["tests/test_influential_paper.py::test_it_differs_from_primary_in_exactly_this_one_respect"]

# 5. primary_set_invariants: point (7).
e = by["primary_set_invariants"]
st = e["statement"]
st = st.replace("(6) A constructed record (the controlled extract) never enters a run that is not marked as a test. ",
                "(6) A constructed record (the controlled extract) never enters a run that is not marked as a test. "
                "(7) A record without a group under the plan's grouping never enters (no group is invented; entry "
                "'records_without_group'). ")
st = st.replace("(6) by code at record storage, inclusion and the freeze.",
                "(6) by code at record storage, inclusion and the freeze; (7) by the eligibility rule 'group_unknown'.")
st = st.replace("checks the primary set against each of (1) to (6)", "checks the primary set against each of (1) to (7)")
st = st.replace("and each record's kind and source, and refuses",
                "and each record's kind, source and, for (7), group under the plan's grouping, and refuses")
assert st.count("(7)") == 4, st
reword(e, st, "Six invariants until step 7b (owner, 2026-10-06): point (7) added.", "2026-10-06")
e["value"]["text"] = "seven things no plan can do"
e["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.eligibility:has_group"})
e["applied"]["note"] += (" (7) test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule, "
                         "test_each_invariant_is_checked_on_the_primary_set[a record without a group…], "
                         "test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze.")
e["tests"] += ["tests/test_freeze_invariants.py::test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze",
               "tests/test_eligibility.py::test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule"]

# 6. fixed_minimums: the paper minimum stays a count, final for sprint 1.
e = by["fixed_minimums"]
reword(e, e["statement"] + " The paper minimum stays a count of informative papers, not the effective number of "
          "papers (entry 'effective_papers'); final for sprint 1 (owner, 2026-10-06).",
       "Step 7b (owner, 2026-10-06): recorded as final for sprint 1; the values are unchanged.", "2026-10-06")

# 7. effective_papers: a note.
by["effective_papers"]["notes"].append(
    "Step 7b (owner, 2026-10-06): I_g also chooses the paper left out of the sensitivity set "
    "'without_most_influential_paper' (entry 'most_influential_paper_set'), through the same function "
    "('statistics.slope_information'). The paper minimum stays a count (entry 'fixed_minimums').")

# 8. New entry.
new = {
    "key": "most_influential_paper_set",
    "name": "Sensitivity set without the most influential paper",
    "state": "in_force",
    "statement": (
        "The sensitivity set 'without_most_influential_paper' is the primary set minus every record of the paper "
        "(the group under the plan's grouping) holding the largest share of slope information, I_g / Σ I_g, with I_g "
        "the paper's sum of squared within-alloy deviations of the transformed grain size (entry 'effective_papers'), "
        "computed on the primary set's records. The paper is chosen by code at Inclusion from grain sizes, alloys and "
        "groups only, never from outcome values (Inclusion receives none). Shares within the numerical zero "
        "(RELATIVE_ZERO, 1e-10) of the largest are tied; a tie is broken by each tied paper's earliest record under "
        "the plan's survivor source order, then the lowest row in the source file, then the stable identity "
        "(source-version fingerprint, origin key, item index), never a database id or an order. The removed records "
        "get the rule 'most_influential_paper' in that set only; it differs from the primary set in exactly this one "
        "respect (alloys left with one grain size are the fit's own 'not used in this fit', as in every set). Without "
        "any slope information nothing is removed. Descriptive only; it never changes the verdict."),
    "value": {"text": "primary minus the paper with the largest share of slope information", "unit": None},
    "category": "statistical",
    "affects": ("One more sensitivity analysis in every run whose plan names it (the default and reference plans). "
                "The plan's fingerprint, so the freeze fingerprint and the calibration seeds of every run, change."),
    "reason": ("The pooled result's largest paper share (38.7% on the reference data) shows the evidence is "
               "concentrated; this set shows the result without that paper."),
    "evidence": ["Owner's decision, 2026-10-06 (step 7b brief); tie-break: step 7b planning, question 3."],
    "decided": dict(OWNER),
    "expert_review": {"status": "not_reviewed", "name": None, "date": None},
    "sensitivity": None,
    "applied": {"status": "yes", "settings": [
        {"ref": "python:hypocurate.pipeline.eligibility:INFLUENCE_KEY", "equals": "without_most_influential_paper"},
        {"ref": "python:hypocurate.pipeline.eligibility:INFLUENCE_RULE", "equals": "most_influential_paper"},
        {"ref": "python:hypocurate.pipeline.eligibility:most_influential"},
        {"ref": "python:hypocurate.pipeline.eligibility:influence_tie_key"},
        {"ref": "python:hypocurate.pipeline.statistics:slope_information"},
        {"ref": "python:hypocurate.pipeline.statistics:RELATIVE_ZERO", "equals": 1e-10},
        {"ref": "python:hypocurate.pipeline.profile:SENSITIVITY_ANALYSES"}], "note": None},
    "tests": [
        "tests/test_influential_paper.py::test_the_slope_information_is_the_owners_formula",
        "tests/test_influential_paper.py::test_the_design_uses_the_same_slope_information",
        "tests/test_influential_paper.py::test_the_set_is_primary_minus_the_paper_with_the_largest_share",
        "tests/test_influential_paper.py::test_it_differs_from_primary_in_exactly_this_one_respect",
        "tests/test_influential_paper.py::test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order",
        "tests/test_influential_paper.py::test_a_tie_follows_the_survivor_source_order_before_the_row",
        "tests/test_influential_paper.py::test_the_choice_uses_no_outcome_value",
        "tests/test_influential_paper.py::test_without_any_slope_information_nothing_is_removed",
        "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change",
        "tests/test_reference_numbers.py::test_the_set_without_the_most_influential_paper",
    ],
    "history": [],
    "notes": ["Like every sensitivity set: descriptive, never changes the verdict, no multiplicity adjustment "
              "(entries 'sensitivity_one_change', 'no_multiplicity_adjustment')."],
}
entries.append(new)
PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(entries))
```

## 6. Reference numbers: before (main) and after

Dump (run once on `main`, once on the branch; it uses the project's conftest as a plugin):

```python
"""Scratch: dump the reference run's full statistics output (step 7b before/after comparison)."""
import json, os
import pipeline_world as pw
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from stats_world import rows_of


def test_dump(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        rid = pw.dispatched_run(engine, sources=("mpea", "tamu_fcc"))
        checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
        extract.store_records(engine, rid)
        checks.run_checks(engine, rid)
        sets = inclusion.decide_run(engine, rid)
        freeze = checkpoints.freeze_dataset(engine, rid)
        out = analysis.run_statistics(engine, rid)
        inc = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid)[0][0]
        recs = rows_of(engine, "SELECT id, 0, paper_doi, paper_reference, harmonized FROM record WHERE extraction_run_id = :r", r=rid)
        json.dump({"stats": out, "freeze": freeze, "inclusion": inc,
                   "records": [[r[0], r[2], r[3], (r[4] or {}).get("composition")] for r in recs]},
                  open(os.environ["DUMP_TO"], "w"), indent=1, default=str, sort_keys=True)
    finally:
        engine.dispose()
        _drop(admin, name)
```

Comparison:

```python
"""Step 7b: the reference run before (main, 0f31698) and after, side by side."""
import json, math, sys
S = sys.argv[1]
b, a = (json.load(open(f"{S}/{n}.json")) for n in ("before", "after"))
A = {e["analysis"]: e for e in a["stats"]["analyses"]}
B = {e["analysis"]: e for e in b["stats"]["analyses"]}
print("freeze fingerprint before", b["freeze"]["fingerprint"][:16], "after", a["freeze"]["fingerprint"][:16])
print("\n1. Every analysis present before: counts, k, SE, p, df, informative, effective, share (exact equality)")
keys = ["n_records", "n_alloys", "n_groups", "n_groups_informative", "resid_df", "effective_papers", "largest_paper_share"]
same = True
for k in B:
    eb, ea = B[k], A[k]
    vb = [eb["counts"][c] for c in keys] + [eb[x] for x in ("estimate", "std_error", "p_value", "df", "label", "inference_reason")]
    va = [ea["counts"][c] for c in keys] + [ea[x] for x in ("estimate", "std_error", "p_value", "df", "label", "inference_reason")]
    print(f"  {k:45s} {'identical' if vb == va else 'DIFFERENT'}")
    same &= vb == va
print("  all identical:", same, "| decision identical:", {k: v for k, v in b["stats"]["decision"].items() if k != "freeze_fingerprint"} ==
      {k: v for k, v in a["stats"]["decision"].items() if k != "freeze_fingerprint"})
print("\n2. Simulated figures (2,000 simulations each), before -> after")
def fmt(c, world):
    w = c[world]
    return f"{w['share']*100:6.2f}% [{w['ci_low']*100:5.2f}, {w['ci_high']*100:5.2f}]"
for k in ("pooled", "per_source:mpea"):
    for m in ("fixed", "estimated"):
        cb, ca = B[k]["calibration"][m], A[k]["calibration"][m]
        for world, label in (("null", "false-positive share"), ("effect", "detection rate")):
            pb, pa = cb[world]["share"], ca[world]["share"]
            n = 2000
            p = (pb + pa) / 2
            sd = math.sqrt(max(p * (1 - p), 1 / n) * 2 / n)   # difference of two independent shares
            z = (pa - pb) / sd
            print(f"  {k:16s} {m:9s} {label:20s} {fmt(cb, world)} -> {fmt(ca, world)}  diff {100*(pa-pb):+5.2f} pts, z = {z:+.2f}")
        print(f"  {'':16s} {m:9s} flag {cb['confidence_flag']} -> {ca['confidence_flag']}; seed changed: {cb['seed'] != ca['seed']}")
print("\n3. The new set")
mi = a["freeze"]["most_influential"]
recs = {r[0]: r for r in a["records"]}
dois = {recs[i][1] for i in mi["records"]}
refs = {recs[i][2] for i in mi["records"]}
print("  removed group", mi["group"], "share", mi["share"], "tied", mi["tied"])
print("  DOI", dois, "reference", refs)
print("  records", mi["n_records"], "alloys", mi["n_alloys"])
from collections import Counter
print("  compositions", Counter(json.dumps(recs[i][3], sort_keys=True)[:120] for i in mi["records"]))
e = A["sensitivity:without_most_influential_paper"]
c = e["counts"]
print(f"  k = {e['estimate']!r}, SE = {e['std_error']!r}, p = {e['p_value']!r}, df = {e['df']}")
print(f"  records {c['n_records']} (in set {c['n_records_in_set']}, not used {c['n_records_not_used']}), alloys {c['n_alloys']} "
      f"(not used {c['n_alloys_not_used']}), groups {c['n_groups']}, informative {c['n_groups_informative']}, resid df {c['resid_df']}")
print(f"  effective {c['effective_papers']!r}, largest share {c['largest_paper_share']!r}, uninformative {e['uninformative_groups']}")
print(f"  inference_reason {e['inference_reason']}, minimums_met {e['minimums_met']}, significant {e['significant']}")
for m in ("fixed", "estimated"):
    cal = e["calibration"][m]
    if cal["status"] == "computed":
        print(f"  calibration {m}: false-positive {fmt(cal, 'null')}, detection {fmt(cal, 'effect')}, flag {cal['confidence_flag']}")
    else:
        print(f"  calibration {m}: {cal}")
```

Output:

```
freeze fingerprint before 3ec87f58975dc9fc after 52207f25f71748cf

1. Every analysis present before: counts, k, SE, p, df, informative, effective, share (exact equality)
  pooled                                        identical
  per_source:mpea                               identical
  per_source:tamu_fcc                           identical
  sensitivity:no_exclusions                     identical
  sensitivity:tension_and_compression           identical
  sensitivity:six_batches_as_groups             identical
  sensitivity:same_alloy_1_at_pct               identical
  sensitivity:source_only_assignments           identical
  sensitivity:scope_not_confirmed_included      identical
  sensitivity:possible_duplicates_separate      identical
  sensitivity:conflicts_survivor_value          identical
  all identical: True | decision identical: True

2. Simulated figures (2,000 simulations each), before -> after
  pooled           fixed     false-positive share   7.85% [ 6.71,  9.12] ->   7.25% [ 6.15,  8.48]  diff -0.60 pts, z = -0.72
  pooled           fixed     detection rate       100.00% [99.82, 100.00] -> 100.00% [99.82, 100.00]  diff +0.00 pts, z = +0.00
                   fixed     flag over_confident -> over_confident; seed changed: True
  pooled           estimated false-positive share   7.55% [ 6.43,  8.80] ->   8.85% [ 7.64, 10.18]  diff +1.30 pts, z = +1.50
  pooled           estimated detection rate        97.20% [96.38, 97.88] ->  97.75% [97.00, 98.35]  diff +0.55 pts, z = +1.11
                   estimated flag over_confident -> over_confident; seed changed: True
  per_source:mpea  fixed     false-positive share   8.30% [ 7.13,  9.60] ->   9.95% [ 8.67, 11.35]  diff +1.65 pts, z = +1.81
  per_source:mpea  fixed     detection rate       100.00% [99.82, 100.00] -> 100.00% [99.82, 100.00]  diff +0.00 pts, z = +0.00
                   fixed     flag over_confident -> over_confident; seed changed: True
  per_source:mpea  estimated false-positive share   8.05% [ 6.89,  9.33] ->   8.00% [ 6.85,  9.28]  diff -0.05 pts, z = -0.06
  per_source:mpea  estimated detection rate        96.10% [95.16, 96.91] ->  95.95% [94.99, 96.77]  diff -0.15 pts, z = -0.24
                   estimated flag over_confident -> over_confident; seed changed: True

3. The new set
  removed group paper:eff935ed572e750b3e2d6fc26fc70fe16ee313149f0bdacf1fd1197d532db890 share 0.38672766820523524 tied ['paper:eff935ed572e750b3e2d6fc26fc70fe16ee313149f0bdacf1fd1197d532db890']
  DOI {'10.1007/s11661-019-05231-y'} reference {'Effect of Annealing Temperature on Microstructure and Mechanical Properties of a Severe Cold-Rolled FeCoCrNiMn High-Entropy Alloy'}
  records 8 alloys 1
  compositions Counter({'{"status": "converted", "unit": "at.%", "value": {"Co": 20.0, "Cr": 20.0, "Fe": 20.0, "Mn": 20.0, "Ni": 20.0}}': 8})
  k = 393.50438134761123, SE = 90.487111236234, p = 0.00019348509448671378, df = 18
  records 89 (in set 89, not used 0), alloys 22 (not used 0), groups 19, informative 19, resid df 66
  effective 3.2411963217867, largest share 0.5210073161219331, uninformative []
  inference_reason None, minimums_met True, significant True
  calibration fixed: false-positive   7.50% [ 6.38,  8.74], detection  99.95% [99.72, 100.00], flag over_confident
  calibration estimated: false-positive   7.90% [ 6.76,  9.17], detection  87.40% [85.87, 88.82], flag over_confident
```

## 7. Mutation checks

Each mutation applied alone to a scratch copy of the package (`data/` linked), `PYTHONPATH` to the copy, run from outside the repository; the import is checked. Control (no change): see the first line of the output.

```python
"""Step 7b mutations: (name, file, old, new, tests). Each is applied alone to a scratch copy."""
E = "hypocurate/pipeline/eligibility.py"
M = [
 ("m01 rule 5 removed", E,
  '''        elif not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE
''', "", "tests/test_eligibility.py tests/test_controlled_duplicates_handling.py tests/test_analysis_stage.py::test_the_statistics_backstop_is_not_reached_in_a_normal_run"),
 ("m02 rule 5 after the menu exclusions", E,
  '''        elif not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE
        elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
            rules[r["id"]] = "scope_not_confirmed"
        elif _excluded(r, st):
            rules[r["id"]] = "excluded_by_rule"''',
  '''        elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
            rules[r["id"]] = "scope_not_confirmed"
        elif _excluded(r, st):
            rules[r["id"]] = "excluded_by_rule"
        elif not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE''', "tests/test_eligibility.py"),
 ("m03 rule 5 after identity (survivor may lack a group)", E,
  ['''        elif not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE
''', '''    _identity(records, flags, rules, st)  # 8
'''], ["", '''    _identity(records, flags, rules, st)  # 8
    for r in records.values():
        if r["id"] not in rules and not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE
'''], "tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor"),
 ("m04 rule 5 judged under the primary grouping in every set", E,
  '''    return group(rec, st) is not None


def _excluded''', '''    return group_in(rec, {**st.grouping, "tamu_fcc": "dataset"}) is not None


def _excluded''', "tests/test_eligibility.py"),
 ("m05 freeze invariant 7 off", E,
  '''    if ungrouped:
        out.append(f"records without a group: {ungrouped}")''', '''    if False:
        out.append(f"records without a group: {ungrouped}")''', "tests/test_freeze_invariants.py"),
 ("m06 freeze invariant 7 through rule 5's has_group (bypassed with it)", E,
  '''    ungrouped = sorted(i for i in members if group_in(records[i], grouping) is None)''',
  '''    ungrouped = sorted(i for i in members if not has_group(records[i], type("S", (), {"grouping": grouping})()))''',
  "tests/test_freeze_invariants.py"),
 ("m07 the paper with the smallest share", E,
  '''    top = max(info.values())''', '''    top = min(info.values())''',
  "tests/test_influential_paper.py tests/test_reference_numbers.py"),
 ("m08 the paper with the most records, not the most information", E,
  '''    top = max(info.values())
    tied = sorted(g for g, v in info.items() if v >= top - statistics.RELATIVE_ZERO * top)''',
  '''    size = {g: sum(group(r, st) == g for r in chosen) for g in info}
    top = max(size.values())
    tied = sorted(g for g in info if size[g] == top)''', "tests/test_influential_paper.py tests/test_reference_numbers.py"),
 ("m09 tie-break by database id", E,
  '''    return (order, rec["row"] if rec["row"] is not None else math.inf, rec["version_fingerprint"], rec["origin"],
            rec["item_index"])''', '''    return (rec["id"],)''', "tests/test_influential_paper.py"),
 ("m10 tie-break without the source order", E,
  '''    return (order, rec["row"] if rec["row"] is not None else math.inf,''',
  '''    return (0, rec["row"] if rec["row"] is not None else math.inf,''', "tests/test_influential_paper.py"),
 ("m11 ties by exact equality, not the numerical zero", E,
  '''if v >= top - statistics.RELATIVE_ZERO * top)''', '''if v == top)''', "tests/test_influential_paper.py"),
 ("m12 the choice counts records outside the primary set", E,
  '''        for i in most_influential(plan, records, members(rules))["records"]:''',
  '''        for i in most_influential(plan, records, [i for i, r in rules.items() if r in ("in_scope", "single_grain_size", "out_of_scope")])["records"]:''',
  "tests/test_influential_paper.py"),
 ("m13 removal cascades through the grain-size rule", E,
  '''        for i in most_influential(plan, records, members(rules))["records"]:
            rules[i] = INFLUENCE_RULE''',
  '''        for i in most_influential(plan, records, members(rules))["records"]:
            rules[i] = INFLUENCE_RULE
        left = defaultdict(set)
        for r in records.values():
            if rules[r["id"]] == "in_scope":
                left[alloy(r, st.decimals)].add(r["values"][st.predictor])
        for r in records.values():
            if rules[r["id"]] == "in_scope" and len(left[alloy(r, st.decimals)]) < st.min_grain_sizes:
                rules[r["id"]] = "single_grain_size"''',
  "tests/test_influential_paper.py tests/test_reference_sets.py"),
 ("m14 slope information without the alloy contrast rule", "hypocurate/pipeline/statistics.py",
  '''    used_alloys = sorted(a for a, v in values.items() if has_contrast(v))
    keep = set(used_alloys)
    used = [t for t in rows if t[1] in keep]''', '''    used_alloys = sorted(values)
    keep = set(used_alloys)
    used = [t for t in rows if t[1] in keep]''', "tests/test_influential_paper.py"),
 ("m15 nothing removed (the set equals primary)", E,
  '''    if key == INFLUENCE_KEY:  # the set's one change, on the primary decisions above''',
  '''    if False:  # the set's one change, on the primary decisions above''',
  "tests/test_influential_paper.py tests/test_reference_sets.py tests/test_reference_numbers.py"),
]
```

```bash
#!/bin/bash
# Usage: mutate.sh <index>   (control run: index -1). Applies one mutation to a fresh scratch copy.
S=/tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad
R=/workspaces/hypocurate
C=$S/copy_$1
rm -rf $C && mkdir -p $C && cp -r $R/hypocurate $C/ && ln -s $R/data $C/data
TESTS=$(cd $R && .venv/bin/python - "$1" "$C" <<'PY'
import sys; sys.path.insert(0, "/tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad")
from mutations import M
i, c = int(sys.argv[1]), sys.argv[2]
if i < 0:
    print(" ".join(sorted({t for m in M for t in m[4].split()}))); sys.exit()
name, f, old, new, tests = M[i]
p = f"{c}/{f}"; s = open(p).read()
for o, n in (zip(old, new) if isinstance(old, list) else [(old, new)]):
    assert s.count(o) == 1, name
    s = s.replace(o, n)
open(p, "w").write(s); print(tests)
PY
)
cd /tmp && set -a && . $R/.env && set +a
echo "import check: $(PYTHONPATH=$C $R/.venv/bin/python -c 'import hypocurate; print(hypocurate.__file__)')"
cd $R/tests/.. && cd /tmp && PYTHONPATH=$C:$R/tests $R/.venv/bin/python -m pytest -q -p no:cacheprovider --rootdir=$R -c $R/pyproject.toml $(for t in $TESTS; do echo $R/$t; done) 2>&1 | tail -1
rm -rf $C
```

Output:

```
== control (no change)
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_-1/hypocurate/__init__.py
179 passed in 53.94s
== m01 rule 5 removed
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_0/hypocurate/__init__.py
14 failed, 99 passed in 10.11s
== m02 rule 5 after the menu exclusions
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_1/hypocurate/__init__.py
2 failed, 60 passed in 1.24s
== m03 rule 5 after identity (survivor may lack a group)
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_2/hypocurate/__init__.py
1 failed in 1.28s
== m04 rule 5 judged under the primary grouping in every set
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_3/hypocurate/__init__.py
1 failed, 61 passed in 1.15s
== m05 freeze invariant 7 off
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_4/hypocurate/__init__.py
2 failed, 16 passed in 19.85s
== m06 freeze invariant 7 through rule 5's has_group (bypassed with it)
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_5/hypocurate/__init__.py
1 failed, 17 passed in 19.53s
== m07 the paper with the smallest share
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_6/hypocurate/__init__.py
5 failed, 37 passed in 15.96s
== m08 the paper with the most records, not the most information
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_7/hypocurate/__init__.py
4 failed, 38 passed in 15.89s
== m09 tie-break by database id
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_8/hypocurate/__init__.py
2 failed, 11 passed in 1.26s
== m10 tie-break without the source order
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_9/hypocurate/__init__.py
1 failed, 12 passed in 1.34s
== m11 ties by exact equality, not the numerical zero
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_10/hypocurate/__init__.py
1 failed, 12 passed in 1.31s
== m12 the choice counts records outside the primary set
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_11/hypocurate/__init__.py
2 failed, 11 passed in 1.41s
== m13 removal cascades through the grain-size rule
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_12/hypocurate/__init__.py
1 failed, 18 passed in 9.98s
== m14 slope information without the alloy contrast rule
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_13/hypocurate/__init__.py
1 failed, 12 passed in 1.40s
== m15 nothing removed (the set equals primary)
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/copy_14/hypocurate/__init__.py
7 failed, 41 passed in 23.62s
```

## 8. The new and changed tests on the code before (`main`'s package)

```
import check: /tmp/claude-1000/-workspaces-hypocurate/cf698fcd-eb20-442c-9bdc-3ae99d1e243d/scratchpad/main_copy/hypocurate/__init__.py
package: main (0f31698); tests: the branch's
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_slope_information_is_the_owners_formula
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_design_uses_the_same_slope_information
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_set_is_primary_minus_the_paper_with_the_largest_share
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_it_differs_from_primary_in_exactly_this_one_respect
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_only_primary_members_count
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order[ids0]
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order[ids1]
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order[ids2]
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_a_tie_follows_the_survivor_source_order_before_the_row
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_without_any_slope_information_nothing_is_removed
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_choice_uses_no_outcome_value
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_change_is_named_and_in_the_default_plan
FAILED ../workspaces/hypocurate/tests/test_influential_paper.py::test_the_numerical_zero_decides_ties
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value[record3-group_unknown]
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_group_unknown_is_rule_5_after_missing_value[record4-group_unknown]
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_a_record_without_a_group_is_never_a_survivor
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_the_group_is_judged_under_each_sets_own_grouping
FAILED ../workspaces/hypocurate/tests/test_eligibility.py::test_alloys_are_counted_on_records_with_a_group
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[exact duplicate counted twice-members0-flags0-None-False-exact duplicate]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[both records of a conflict-members1-flags1-None-False-conflict]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[an invalid value-members2-flags2-None-False-invalid value]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[an unresolved-identity group-members3-flags3-None-False-unresolved identity]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[a model-recalled record-members4-flags4-records4-False-model-recalled]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[a constructed record in an unmarked run-members5-flags5-records5-False-constructed]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set[a record without a group-members6-flags6-records6-False-without a group]
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_what_the_invariants_allow
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze
FAILED ../workspaces/hypocurate/tests/test_freeze_invariants.py::test_a_texas_am_record_is_not_without_a_group
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_every_analysis_is_stored_with_both_calibrations
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_below_the_minimums_every_analysis_holds_counts_and_records_only
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_use_what_is_available_with_one_group_gives_the_coefficient_only
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_fixed_option_with_one_group_withholds_even_the_coefficient
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates
FAILED ../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_statistics_backstop_is_not_reached_in_a_normal_run
FAILED ../workspaces/hypocurate/tests/test_reference_numbers.py::test_the_set_without_the_most_influential_paper
FAILED ../workspaces/hypocurate/tests/test_reference_numbers.py::test_the_set_without_the_most_influential_paper_as_reported
FAILED ../workspaces/hypocurate/tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files[row5-possible_duplicate_unknown_paper]
FAILED ../workspaces/hypocurate/tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files[row6-possible_duplicate_unknown_paper]
FAILED ../workspaces/hypocurate/tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files[row5-possible_duplicate_unknown_paper]
FAILED ../workspaces/hypocurate/tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files[row6-possible_duplicate_unknown_paper]
FAILED ../workspaces/hypocurate/tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change
FAILED ../workspaces/hypocurate/tests/test_reference_sets.py::test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts
FAILED ../workspaces/hypocurate/tests/test_order_independence.py::test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order
FAILED ../workspaces/hypocurate/tests/test_order_independence.py::test_the_freeze_check_allows_at_most_one_record_per_chain
FAILED ../workspaces/hypocurate/tests/test_order_independence.py::test_permuted_ids_and_insertion_order_give_the_same_frozen_result[controlled_extract]
FAILED ../workspaces/hypocurate/tests/test_order_independence.py::test_permuted_ids_and_insertion_order_give_the_same_frozen_result[reference_data]
FAILED ../workspaces/hypocurate/tests/test_conflict_policy.py::test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group[one paper]
FAILED ../workspaces/hypocurate/tests/test_conflict_policy.py::test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group[only through B]
FAILED ../workspaces/hypocurate/tests/test_permutation_stats.py::test_permuted_ids_and_insertion_order_give_identical_results[reference_data]
FAILED ../workspaces/hypocurate/tests/test_permutation_stats.py::test_permuted_ids_and_insertion_order_give_identical_results[controlled_extract]
FAILED ../workspaces/hypocurate/tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions
55 failed, 280 passed in 126.19s (0:02:06)
```

## 9. Suite

```
$ pytest -q   (Codespace, Python 3.14, docker compose up -d db; code at c5f74f0)
1186 passed in 355.41s (0:05:55)
$ docker compose build test && docker compose run --rm test
1186 passed in 383.75s (0:06:23)
GitHub Actions run 37474428306 on c5f74f0: success
runtime image OK
1186 passed in 266.92s (0:04:26)
```
