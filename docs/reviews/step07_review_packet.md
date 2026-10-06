# Build step 7 — review packet for the second model

Date: 2026-10-06. Branch: `step-07-statistics`. Code reviewed: commit `d3da7c4` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success (1,104 passed, runtime image OK), https://github.com/kelawady/hypocurate/actions/runs/37398444475.

Generated from the files on disk by a script, so every file below is quoted exactly. Lock-file hash lines are left out.

## How to use this packet

This is the first review of build step 7 (PRD Section 15), as the owner scoped it: the statistics module, the two validity checks, data sufficiency, the verdict and per-run calibration. There is no agent, no model call, no screen and no plot. **Three changes are safeguard changes and need your review before the merge:** the access-layer change (the code roles `statistics` and `gap_facts`, the field `frozen_analysis_data`), migration 0004, and the estimated calibration (a departure from PRD 5.10).

The summary (section 1) states the owner's decisions, the model, every result state (what is stored and what is withheld), the calibration method exactly, the reference numbers with the path that produces each, every test changed, the mutation checks and the decisions made while building. Your review is advice; the test suite is the gate. Please return a dated findings file with each finding, its severity and the evidence.

Please check in particular:
- **The estimated calibration** (`calibration.py`, `henderson_iii`): is the method correct and honestly described? Can it influence inclusion, the outcome or the verdict?
- **Statistics' and the gap facts' inputs** (`allowlist.py`, `fields.frozen_analysis_data`): can either reach anything beyond its list?
- **Below the minimums** (decision 1): does anything stored carry a number computed from outcome values?
- **Migration 0004** (section 6): does it enforce the withheld rule, labels and calibration rules completely? Safe with the previous release's code?
- **The copy path** (`completion.py`): does it only copy?
- **The statistics** (`statistics.py`): are they what the plan states? Are the tolerances justified?
- **Overclaims**: is any statement stronger than the code supports?

## Contents

1. Step summary
2. Reviewer checklist
3. CLAUDE.md
4. Core rules: PRD Sections 3.1, 4, 5.6 to 5.10
5. New package code (full text)
6. Migration 0004 (full text)
7. Other code changes (diffs against `main`)
8. The assumptions register (diff)
9. Tests: new files (full text)
10. Tests: changed files (diffs)
11. README (diff)
12. Mutation checks (script and output)
13. Suite output

## Files added, modified or deleted since `main` (`3aee798`, the step 6 live record)

```
M	README.md
M	hypocurate/access/allowlist.py
M	hypocurate/access/fields.py
M	hypocurate/access/layer.py
M	hypocurate/access/vocabulary.py
M	hypocurate/assumptions.json
A	hypocurate/db/migrations/versions/0004_statistics_results.py
M	hypocurate/db/models.py
A	hypocurate/pipeline/analysis.py
A	hypocurate/pipeline/calibration.py
M	hypocurate/pipeline/checkpoints.py
A	hypocurate/pipeline/completion.py
M	hypocurate/pipeline/plan.py
M	hypocurate/pipeline/profile.py
A	hypocurate/pipeline/results.py
A	hypocurate/pipeline/statistics.py
M	hypocurate/pipeline/writes.py
M	pyproject.toml
M	requirements-dev.lock
M	requirements.lock
M	scripts/check_runtime_image.py
M	tests/access_world.py
A	tests/generator.py
M	tests/model_builder.py
A	tests/reference_stats.py
A	tests/stats_world.py
M	tests/test_access_code_roles.py
A	tests/test_access_statistics.py
A	tests/test_analysis_stage.py
M	tests/test_assumptions.py
A	tests/test_calibration.py
A	tests/test_completion.py
M	tests/test_data_model.py
A	tests/test_generated_fixed_set.py
A	tests/test_migrations_step7.py
A	tests/test_permutation_stats.py
A	tests/test_reference_numbers.py
A	tests/test_statistics.py
```


## 1. Step summary

### `docs/reviews/step07_summary.md`

```markdown
# Build step 7 — summary for review

Date: 2026-10-06. Branch: `step-07-statistics`, code at `d3da7c4`; GitHub Actions on it: success (1,104 passed, runtime image OK), https://github.com/kelawady/hypocurate/actions/runs/37398444475. **Status: built, the whole suite passes (1,104 tests, locally and in the test image); not yet reviewed by the second model; not merged.** PRD Section 15, step 7, as the owner scoped it: the statistics module, the validity checks, data sufficiency, the verdict and per-run calibration.

The suite is the gate. This summary is for the second model, which uses `docs/reviews/checklist.md`; the packet is `docs/reviews/step07_review_packet.md`. **Three changes are safeguard changes and need the review before the merge** (CLAUDE.md, "How we work" item 5; the owner approved them subject to it): the access-layer change (two code roles and one field), migration 0004, and the estimated calibration (a departure from PRD 5.10).

**Not built, as instructed:** agents, model calls, screens, plots, live source registration. Also not built: the gap report text (step 8, the Analyst explains the stored gap facts) and the workbook (step 10). No change to `render.yaml`, `.github/workflows/`, the Dockerfile or Compose. Dependencies changed: numpy and scipy in the runtime lock; statsmodels in the development lock only.

## The owner's decisions (2026-10-05)

From the step 7 brief:
- The one supported model (CLAUDE.md rule 6). The two validity checks can never be waived; check 1 without check 2 gives the coefficient only.
- Fixed minimums 30 / 5 / 10 / 10; "use what is available" waives the threshold only and labels the result exploratory.
- **New:** a fixed-minimum run that falls short holds the counts against each minimum and the records found, for a plot in step 10, and nothing computed from the outcome values. Label "data found; not enough to test".
- Verdict: supported when the one-sided p is strictly below 0.05; "supported under the stated model", "in the sources searched".
- **New:** calibration is reported both ways (fixed numbers of PRD 5.10, and scatter and per-paper shift estimated by code from the frozen residuals); the method is fixed at the rules lock; a flag, never a gate.
- Smallest effect a query setting, default 150 MPa·µm^0.5; the power report is information only.
- Marked test runs labelled "test run: includes constructed data" in every stored result and excluded from every aggregate.
- Every sensitivity set analysed with the same code as the primary set; sensitivity results never change the verdict.
- Statistics reads only the frozen set through the access layer and never decides inclusion; results are a pure function of the frozen set and the locked plan (permutation test); software correctness against an independent reference implementation on the test side; the reference numbers reproduced with justified tolerances.

From planning (one question at a time):
1. **Below the minimums, run-wide.** Under the fixed option, if the pooled fit misses any minimum, every analysis of the run (pooled, per source, sensitivity) holds counts and records only, even where check 2 fails. The coefficient-only rule applies only to analyses whose numbers are shown. (Otherwise a one-source run would show its coefficient through its per-source result.)
2. **Four per-source labels**, from the locked test and the sign only: "not enough data" (no p-value); "agrees" (same decision as pooled and same sign); "conflicts" (opposite sign); "same direction, different decision" (same sign, different decision). Descriptive only.
3. Migration 0004 widens the label constraint for the fourth label.
4. **Estimated calibration: Henderson's method III**; not estimable means "unavailable" with the reason (section "Calibration").
5. **Estimated power** = the effect-world share of the fixed calibration (uses no outcome value), shown also below the minimums.
6. **Store now, copy later:** step 7 stores the decision; a function copies it onto the run; "partly sufficient" is not set by step 7.
7. **Per-fit alloy rule:** each fit uses only alloys with two or more distinct grain sizes among its own records.
8. **Tolerances, two tiers** (section "Reference numbers"), replacing the register's ±1.
9. **Gap facts as data only** (counts against each minimum, minimums missed, records lacking which fields, the kind of "nothing found" per source); no report text; the Analyst may only explain them. The workbook goes to step 10.
10. Remaining defaults accepted: numpy/scipy runtime, statsmodels development only; the seed from the freeze fingerprint; the code role `statistics` with `frozen_analysis_data`; the `calibration` part of the plan; migration 0004's contents.

Owner's additions before the build:
11. **The copy function only copies.** It refuses if the stored decision is missing or belongs to a different freeze fingerprint.
12. **The minimums are counted on the records actually used in a fit**, not on the whole frozen set.
13. **When the estimated paper shift is set to zero, the stored result says so.**
14. **A permutation test** of record ids and insertion order.
15. **Evidence level 1 to 6**, stored with each run's statistics result, derived by one tested function from the result state, never by an agent: 6 sufficient with a verdict; 5 exploratory; 4 coefficient only; 3 below the minimums under the fixed option; 2 coefficient cannot be fitted; 1 no dataset frozen. Descriptive; a marked run keeps its level beside its label. Stored in the decision and as `run.evidence_level` (0004). A partly sufficient original question keeps the level of its own pooled result state.
16. `test_reference_numbers.py` states the path that produces each reference result, with Texas A&M alone and MPEA alone shown three ways each.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/pipeline/statistics.py` | The model, the two validity checks, the minimums, the verdict, the per-source labels, the result state and the evidence level. Pure. |
| `hypocurate/pipeline/calibration.py` | Both calibration methods, method III, the exact interval, the flag and the seed. Pure. |
| `hypocurate/pipeline/analysis.py` | The analysis stage: reads through the Statistics and gap-facts access objects, `analyse` (pure), the gap facts, the write. |
| `hypocurate/pipeline/completion.py` | `copy_decision`: copies the stored decision onto the run, unchanged. |
| `hypocurate/pipeline/results.py` | `REAL_RUN`, the one condition that leaves marked runs out of aggregates; three queries that use it. |
| `hypocurate/pipeline/plan.py`, `profile.py` | The plan's `calibration` part, its validation, and one named constant per default (profile version 2). |
| `hypocurate/pipeline/writes.py`, `checkpoints.py` | New refusal codes; `TEST_RUN_LABEL` (from the model); the freeze's "no dataset frozen" row carries the label on a marked run. |
| `hypocurate/access/allowlist.py`, `fields.py`, `layer.py`, `vocabulary.py` | The code roles `statistics` and `gap_facts`, the field `frozen_analysis_data`, the denial `not_frozen`, the calibration vocabularies. |
| `hypocurate/db/migrations/versions/0004_statistics_results.py`, `models.py` | Migration 0004 (section "Migration 0004"). |
| `hypocurate/assumptions.json` | The register (section "Assumptions register"). |
| `pyproject.toml`, `requirements.lock`, `requirements-dev.lock` | numpy, scipy (runtime: scipy 1.18.1 added; numpy 2.5.3 was already there through pandas); statsmodels 0.15.0 and its dependencies (development only). |
| `scripts/check_runtime_image.py`, `README.md` | The image must contain the new modules and 0004; a README section. |
| `tests/reference_stats.py`, `tests/generator.py`, `tests/stats_world.py` | The independent reference implementation (statsmodels), the data generator and its fixed set, a helper for small pipeline runs. |

## The model and the test

`statistics.py`, for each analysis:
1. **The fit's records.** Sort by stable identity (source-version fingerprint, origin key, item index). Keep alloys with at least two distinct grain sizes among this analysis's records (`MODEL_MIN_GRAIN_SIZES = 2`); count the others as "not used in this fit".
2. **The estimate.** x = d^-1/2 (the plan's transformation); remove each alloy's mean from x and y; k = Σ x̃ỹ / Σ x̃². The same as OLS with one intercept per alloy.
3. **The standard error.** Per group g, s_g = Σ_{i∈g} x̃_i e_i with e = ỹ − k x̃; V = Σ s_g² / (Σ x̃²)² × G/(G−1) × (N−1)/(N−K), K = alloys + 1 (statsmodels' default cluster correction).
4. **The test.** t = k / √V; p = P(T > t), T ~ t(G − 1); "supported" exactly when p < α (the plan's, 0.05).
5. **Validity checks.** Check 1: at least one alloy with two distinct grain sizes. Check 2: N − alloys − 1 ≥ 1 and G ≥ 2. Check 1 only: k alone.
6. **Minimums,** on the fit's counts: records, alloys (each with two or more grain sizes), groups, residual df.
7. **Groups** come from the same function Inclusion and the freeze counts use (`eligibility.group`, the set's own grouping), and alloys from `eligibility.alloy` (the set's same-alloy rule).

## Result states

The pooled analysis decides; per-source and sensitivity results go through the same function and only describe. Precedence: no dataset frozen; below the minimums (fixed option); not fitted; coefficient only; exploratory; sufficient.

| State (level) | Inputs that lead to it | Stored | Withheld |
|---|---|---|---|
| Sufficient with a verdict (6) | Validity checks pass; minimums met (either option) | Counts, both checks, minimums, k, SE, t, df, p, α, estimated power, both calibrations; decision: outcome sufficient, verdict "supported" (p < α) or "not supported" "under the stated model, in the sources searched", not exploratory | — |
| Exploratory (5) | "Use what is available", checks pass, a minimum missed | As above, `exploratory` true, label "exploratory" | — |
| Coefficient only (4) | Check 1 passes, check 2 fails, and the minimums do not withhold (use what is available, or a plan whose own minimums are met) | Counts, checks, k only; calibration "unavailable: insufficient groups"; outcome insufficient | SE, p, verdict, power, calibration |
| Below the minimums, fixed option (3) | Fixed option and the pooled fit misses any minimum, whether check 2 passes or fails | Run-wide: every analysis holds its counts against each minimum, the minimums missed and the records found (stable identities); label "data found; not enough to test"; estimated power where check 2 passes (no outcome used); calibration "unavailable: below minimums" (or the validity reason if a check fails); gap facts; outcome insufficient | Everything computed from outcomes, in every analysis: k, SE, t, p, verdict, estimated calibration |
| Not fitted (2) | Check 1 fails and the minimums do not withhold. The pooled set of a frozen run always has an alloy with two grain sizes (eligibility rule 8), so this is reachable only in the pure function and in per-source or sensitivity analyses | Counts; calibration "unavailable: coefficient not fitted" | k and everything after it |
| No dataset frozen (1) | No eligible record | Decision (no freeze fingerprint); gap facts; the run-level calibration row "unavailable: no dataset frozen" written at the freeze | Everything else |
| Marked test run (any level) | Any state, on a run with `constructed_test_data` | The same, plus "test run: includes constructed data" on every analysis and calibration row (the database checks: present exactly when the run is marked) and in the `statistics` and `gap_facts` stage results; keeps its level | Left out of every aggregate through `results.REAL_RUN` |

Calibration rows per analysis: `fixed` and `estimated`, each "computed" or "unavailable" with one reason: `coefficient_not_fitted`, `insufficient_groups`, `below_minimums`, or, for the estimated method only, `scatter_not_estimable` / `shift_not_estimable`.

## Calibration (the safeguard change for review)

**What is estimated, and how (the estimated method).** For each analysis whose numbers are shown and whose inference is valid, from that analysis's own frozen records, after the freeze (Henderson's method III, closed form, no optimizer, no random step):
1. Fit the locked model (alloy intercepts and k × x): residual sum of squares RSS_R, rank r_R.
2. Fit it with one intercept per group added: RSS_F, rank r_F.
3. σe² = RSS_F / (N − r_F). Not estimable when N ≤ r_F, or RSS_F is zero (nothing to simulate).
4. σu² = max(0, (RSS_R − RSS_F − (r_F − r_R) σe²) / tr(Z′M_R Z)), with Z the group membership matrix and M_R = I − P_R. Not estimable when the trace is zero (to a relative 1e-9 × N): the groups are entirely explained by alloys and grain sizes, for example every paper studying its own alloys.
5. A negative σu² estimate is set to zero; the stored assumptions say `shift_truncated_at_zero: true` and keep the value before truncation, with RSS_R, RSS_F, both ranks and the trace.

**The simulation (both methods).** The design is kept (the fit's records, alloys, groups, grain sizes). Outcomes are replaced by k_true × x + u_g + e_i, with u_g ~ N(0, σu²) and e_i ~ N(0, σe²); the alloy baselines are zero (the alloy intercepts absorb any baseline exactly). Two worlds, 2,000 simulations each: k_true = 0, then the smallest effect. One generator per method and analysis, seeded with the first 63 bits of SHA-256("freeze fingerprint|analysis|method"); each world draws its shifts (simulations × groups) and then its errors (simulations × records). Each share has an exact (Clopper-Pearson) 95% interval. The flag is "over-confident" when the no-effect interval lies wholly above α, "under-confident" when wholly below.

**What it does not do.**
- It never changes inclusion, the outcome or the verdict. Tested by forcing every calibration to "over-confident" and comparing everything else.
- It does not say how trustworthy the real result is, and does not check extraction or inclusion (PRD 5.10).
- It departs from PRD 5.10, which fixes the noise in advance and never estimates it from the real outcomes. The estimate uses the frozen outcomes after the freeze, when the statistics code sees them anyway, and can change no decision. Whether a calibration based on the data's own noise is a fair description of the test's behaviour is the question for the reviewer.

**On the reference run** (fixed: 60 / 40 MPa; estimated by method III):

| Analysis | Fixed: no-effect significant of 2,000 (95% interval), effect detected, flag | Estimated: σe, σu; no-effect (interval), effect, flag |
|---|---|---|
| Pooled | 157 (6.7% to 9.1%), 2,000, over-confident | 156.2, 22.1; 151 (6.4% to 8.8%), 1,944, over-confident |
| MPEA alone (per source) | 166 (7.1% to 9.6%), 2,000, over-confident | 170.0, 0.0 (truncated; σu² was −1,610); 161 (6.9% to 9.3%), 1,922, over-confident |
| Texas A&M alone (per source) | unavailable: insufficient groups | unavailable: insufficient groups |

Every sensitivity set: over-confident under both methods (no-effect 6.3% to 9.7%). These are findings, not a gate.

**Finding: PRD 5.10's 7.2% (6.1% to 8.4%) is not reproduced.** On the step 6 sets, the reference script's own loop (`docs/reference/calibration_example.py`, run test-side on the same design) gives 8.6% with seed 1 on the earlier 98-record set. Long runs give about 7.8% (pooled) and 8.0% (98 records), with 40,000 simulations in the package and 20,000 in the script's loop, which agree. The PRD's figure probably comes from an earlier design. The conclusion stands: the specified grouped test is somewhat over-confident on data shaped like this. The real residual scatter (about 156 MPa) is much larger than the illustrative 60 MPa.

## The access-layer change (for review)

- **Code role `statistics`:** at the analysis stage only (a dataset frozen, the run running), exactly `plan` and `frozen_analysis_data`.
  - The field returns the freeze fingerprint, the outcome field's name, the frozen sets (vocabulary keys, record ids), and, for records in any frozen set and only those: id, source, stable identity, composition, the paper and the batch as hashes, grain size and the plan's outcome value.
  - It never returns values as reported, free text, records outside the frozen sets, or another run's data.
  - The reader itself refuses a run with no snapshot (`not_frozen`), behind the stage list.
- **Code role `gap_facts`:** at the analysis stage and when a run closed without a freeze. It receives `plan`, `decisions`, `stored_record_counts` and `coverage`, and no outcome value (the planted-value search finds none).
- **No agent role gains a field.** Both code roles are bound by `dispatch.bind_code`; every bind and read is logged.
- **Guaranteed and tested:** Statistics receives no record outside the frozen sets, and the gap facts receive no outcome value.
- **Not claimed:** anything beyond the threat model. Statistics is trusted code and sees the frozen outcomes by design.
- **Statistics never decides inclusion.** It uses each set as frozen. An import scan shows statistics, calibration and analysis import no inclusion, checks, extraction or checkpoint code, and the analysis stage writes no decision, set or record. The database already refuses any change to a frozen set.

## Migration 0004 (for review)

| Change | Why | Previous release's code |
|---|---|---|
| `analysis_result.withheld`, computed by the insert trigger (pooled: fixed option and minimums not met; any other row: the pooled row's, which must be written first); a caller's value must agree; the three "iff check" CHECKs keep their names with "AND NOT withheld" | Decision 1, enforced by the database | Writes no analysis result |
| `analysis_result.n_records_not_used`; the trigger checks n_records + n_records_not_used = the set's records | Decision 7 (the fit's counts) | — |
| `test_run_label` on both result tables, present exactly when the run is marked (trigger) | The owner's labelling rule | Its run-level "no dataset frozen" row needs no label on an unmarked run; a marked run's would be refused (none exist live) |
| Label CHECK gains `same_direction_different_decision`; a label only on per-source rows; power only where check 2 passes | Decisions 2 and 3 | — |
| `calibration_result.method` ('fixed' or 'estimated', present exactly on analysis rows); unique index (run, analysis, method); reasons `below_minimums`, `scatter_not_estimable`, `shift_not_estimable`; trigger: computed only where check 2 passes and not withheld; there, the fixed method must be computed and the estimated one computed or naming why the noise cannot be estimated; other reasons must match the checks and the withheld state | Both ways, decision 4 | — |
| `run.evidence_level` 1 to 6, with a CHECK tying it to the outcome, verdict and exploratory label | Addition 15 | Never completes a run |

Every check of 0001's two trigger functions is kept unchanged except the record count, which now accounts for unused records (tested textually). The downgrade refuses while any row uses what 0004 adds (tested), then restores 0001's functions verbatim (tested against the installed function source) and the old constraints and index. Up, down, up gives the same schema; a failed upgrade changes nothing. **The database does not require `evidence_level` on a completed run** (only that it agrees when present); the copy path always writes it.

## The copy path

`completion.copy_decision(engine, run_id)`, in one locked transaction:
- reads the latest done "statistics" stage result;
- refuses (logged) `decision_missing`, or `decision_not_current` when its freeze fingerprint is not the run's (a run with no freeze needs a decision with none, and vice versa);
- writes outcome, verdict, exploratory and evidence level, and completes the run;
- computes nothing. Tested: a stored decision that disagrees with the statistics is copied as stored, and the database refuses a stored "sufficient" for a withheld run.

The orchestrator (steps 8 and 9) calls it after the Analyst.

## Reference numbers

The two tiers of tolerance:
1. **Against the approved, rounded numbers:** half a unit in the last digit stated. k and its SE are stated to 0.1, so ±0.05; a p-value stated to two figures must round to them; counts are exact. Tighter than the earlier ±1.
2. **Against the independent reference implementation** on the same frozen data: relative 1e-9. Both compute the same closed-form quantities in double precision; observed differences are below 1e-13 relative, and any change of method (correction, df, grouping) moves the numbers by far more.

| Result | Path (`tests/test_reference_numbers.py`) | Package value (full precision) | Approved | Level |
|---|---|---|---|---|
| Pooled | reference run, pooled analysis | 97 / 22 / 20 / 74; k = 424.878909890; SE 64.381043484; p = 1.28715e-6 | 424.9 ± 64.4, p ≈ 1.3e-6 | 6 |
| MPEA alone (1) | reference run, per-source analysis | 76 / 13 / 19 / 62; k = 424.054423082; SE 62.216037758; p = 1.10760e-6; "agrees" | 424.1 ± 62.2, p ≈ 1.1e-6 | run 6 |
| MPEA alone (2) | MPEA-only run, use what is available | same numbers; minimums met: verdict "supported", not exploratory | — | 6 |
| MPEA alone (3) | MPEA-only run, fixed minimums | same numbers; verdict "supported" | — | 6 |
| Texas A&M alone (1) | reference run, per-source analysis | 21 / 9 / 1 / 11; k = 1173.341867347; no SE, no p; "not enough data" | ≈ 1173 (step 6 table 1173.3) | run 6 |
| Texas A&M alone (2) | Texas A&M-only run, use what is available | k = 1173.34 only; no verdict | — | 4 |
| Texas A&M alone (3) | Texas A&M-only run, fixed minimums | withheld: records 21/30, alloys 9/5, groups 1/10, df 11/10; 21 records found; no coefficient | — | 3 |
| Eight sensitivity sets | reference run, sensitivity analyses | each equals the step 6 table (e.g. tension and compression 428.024 ± 63.511, p = 7.398e-7; six batches 424.879 ± 64.229, p = 7.511e-7; scope not confirmed included 432.350 ± 64.861, p = 6.724e-7) | step 6 table | — |

The freeze fingerprint of the reference run changed from step 6 (`93c44b22…`) to `3ec87f58…`. The plan now has a `calibration` part and profile version 2, so the plan's fingerprint changed, and the freeze fingerprint includes it. It is not a reference number.

## Tests

**New: 195 tests, all passing.**

| File | Tests | What they cover |
|---|---|---|
| `test_statistics.py` | 48 | The model; the correction formula; one-sided; strict p < α; the per-fit alloy rule and minimums on the fit; both validity checks; order and id independence (pure); no group invented; the four labels; every state and level; the level never feeds back; wording; the plan's calibration part; no inclusion code imported; no reference number in package code |
| `test_generated_fixed_set.py` | 34 | Ten generated datasets × two options: package against statsmodels (1e-9); stored states, levels, verdicts and simulated counts; validity cases under both options; the generator |
| `test_calibration.py` | 24 | Vectorized test against one statsmodels fit per simulation; the documented draw order; the exact interval against scipy's; the flag; the seed; method III against an independent computation; recovery of known noise; truncation recorded; not estimable (shift, scatter); fixed against estimated; never changes the decision; power needs no outcome |
| `test_analysis_stage.py` | 27 | What is stored per state through the database; refusals (second run, before the freeze); withheld run-wide; exploratory; coefficient only; level 1 and gap facts; marked runs labelled and out of aggregates; the database's own refusals (withheld, unused records, labels, power, calibration, evidence level) |
| `test_completion.py` | 7 | Copies unchanged; refuses missing or another freeze; never recomputes; stage checks; the database checks the copy |
| `test_access_statistics.py` | 16 | The lists; no other stage; Statistics' complete input; only frozen records; gap facts without outcome values (planted-value search); the reader's own refusal |
| `test_reference_numbers.py` | 27 | Each path above, both tiers |
| `test_permutation_stats.py` | 2 | Ids and insertion order permuted three ways, on the reference data and the controlled extract: identical results, calibrations (seeds included), decision and gap facts |
| `test_migrations_step7.py` | 8 | Head; 0001's functions kept verbatim; every check kept; up, down, up; failed upgrade; downgrade refused while used |

**Changed: none removed.**
- `tests/access_world.py` (helper): the narrower question's original run uses "use what is available". Its run stores a coefficient, which decision 1 forbids under the fixed option below the minimums; it still holds the other run's value as its coefficient.
- `tests/model_builder.py` (helper): `result()` computes the withheld state as the database does and leaves out the numbers of a withheld result.
- `test_data_model.py`:
  - The calibration insert template names a method ('fixed' on analysis rows).
  - `test_coefficient_only_completes_as_insufficient_without_a_verdict` and `test_the_validity_checks_cannot_be_waived` run under "use what is available", so that the result is not withheld and each original constraint is still the one that refuses. The fixed-option case is tested in `test_analysis_stage.py`.
  - `test_calibration_unavailable_states_a_matching_reason` writes the pooled row first, which 0004 requires.
- `test_access_code_roles.py`: the code-role list has four roles. The step 6 tests that iterate code roles now iterate Inclusion and Checks by name (`STEP6_ROLES`).
- `test_assumptions.py`: the pinned states move with the decisions:
  - `OWNER_DECISIONS` statuses, and `PARTLY` (now `constructed_test_runs` and `records_without_group`);
  - the open entries (`curator_tabular_sources`, `records_without_group`, both before step 8);
  - `calibration_noise_levels`: new wording, with the earlier wording checked in its history; pending before step 8;
  - `reference_numbers`: applied "yes";
  - the "Not yet" example now uses `spending_caps`.

## Mutation checks

Each safeguard was switched off in a scratch copy of the package (`PYTHONPATH` to the copy, `data/` linked, run from outside the repository, the import checked). Each mutation was run against the tests that should catch it. A control run with no change passes.

| Mutation | Result |
|---|---|
| m01: never withhold below the minimums | 12 failed, 124 passed, 26 errors |
| m02: supported at p ≤ α | 1 failed, 107 passed |
| m03: no small-sample correction | 46 failed, 89 passed |
| m04: alloy rule: one grain size enough | 5 failed, 69 passed, 34 errors |
| m05: no sort by stable identity | 17 failed, 93 passed |
| m06: t df = residual df instead of groups − 1 | 30 failed, 105 passed |
| m07: two-sided p | 33 failed, 102 passed |
| m08: coefficient computed although withheld | 8 failed, 127 passed |
| m09: opposite sign not 'conflicts' | 2 failed, 46 passed |
| m10: exploratory state ignored | 3 failed, 108 passed |
| m11: copy without the fingerprint check | 2 failed, 5 passed |
| m12: copy recomputes the verdict | 1 failed, 6 passed |
| m13: frozen data returns every record | 1 failed, 15 passed |
| m14: Statistics allowed at curation | 2 failed, 14 passed |
| m15: gap facts get records_full | 2 failed, 14 passed |
| m16: truncation not recorded | 1 failed, 23 passed |
| m17: fixed method uses estimated noise | 14 failed, 46 passed |
| m18: flag inverted | 1 failed, 23 passed |
| m19: seed ignores the method | 2 failed, 22 passed |
| m20: trigger: withheld mismatch accepted | 1 failed, 26 passed |
| m21: trigger: test label not checked | 1 failed, 26 passed |
| m22: label not written | 2 failed, 25 passed |
| m23: pooled set with ungrouped record skipped, not refused | 1 failed, 47 passed |
| m24: REAL_RUN does not filter | 1 failed, 26 passed |
| m25: second analysis allowed | 1 failed, 26 passed |

Every mutation is caught (25 of 25). "Errors" are module fixtures that fail because the mutated code produces results the database refuses or the reference cannot match; they count as caught. Full output in the packet.

## Assumptions register

108 entries (was 100): 105 in force, 2 open, 1 direction approved; 104 applied "yes", 2 "partly", 2 "not yet". Every entry decided in step 7 is by the owner on 2026-10-05, not reviewed by an expert.

- **New:**
  - `calibration_both_ways`, `smallest_effect`, `evidence_level_scale`, `per_source_labels`, `fit_alloy_rule`, `copy_decision_only_copies`, `results_pure_function`;
  - `records_without_group`: **open**, owner, before step 8; the code fails closed until then.
- **Decided:** `below_minimum_display` (open → in force; the open wording kept in history).
- **Reworded, with the earlier wording in history:**
  - `calibration_noise_levels`: the exact method III. It stays "direction approved", pending the second-model review, now before step 8, and is applied "yes";
  - `reference_test_tolerance` (the two tiers);
  - `code_role_access` (the two code roles);
  - `code_vocabularies` (the calibration and estimation methods);
  - `plan_named_parts` (the `calibration` part).
- **Moved to "yes":** `model_form`, `shared_coefficient`, `exponent_fixed`, `baseline_per_alloy`, `ols_alloy_intercepts`, `equal_row_weights`, `cluster_robust_se` (with the exact formula in a note), `few_groups_approximate`, `one_sided_test`, `p_threshold_comparison`, `no_multiplicity_adjustment`, `pooled_gives_verdict`, `association_not_causation`, `selection_and_missingness`, `mean_grain_size_only`, `measurement_error_not_propagated`, `papers_independent`, `tamu_grouping_unit`, `grain_size_transformation_at_analysis`, `validity_checks`, `fixed_minimums`, `calibration_simulation` (with the 7.2% finding), `normal_errors_in_calibration`, `calibration_error_model`, `reference_numbers`.
- **Still partly applied:** `constructed_test_runs`. Done: the labels and `REAL_RUN`. Pending: the screens, step 10.

## Decisions I made while building (for the owner and the reviewer)

1. **Records without a group** (now the open register entry `records_without_group`). The marked run with the controlled extract puts two extract records without a DOI into `possible_duplicates_separate`. A clustered standard error needs every record in a group, and the register says no group is invented. Code fails closed:
   - if the pooled set has such a record, the analysis stage refuses (logged, `records_without_group`);
   - a per-source or sensitivity analysis with such a record is listed under `not_analysed` with the count, and nothing is stored for it.
   
   No record of the reference sets lacks a group. **Owner's decision needed** before step 8.
2. **The gap facts read through their own code role** (`gap_facts`), not the Statistics role. That keeps Statistics' list exactly as approved, and the gap facts can be shown to read no outcome value.
3. **Real results by a code condition, not a database view** (`results.REAL_RUN`). A view would have changed the schema tests of step 3; the condition is one named place.
4. **The evidence level is not required by the database** on a completed run. Only agreement is checked, so that the step 3 to 6 helpers that complete runs directly keep working. The copy path always writes it.
5. **The calibration reason when a run is withheld and a check fails** is the validity reason (`coefficient_not_fitted`, `insufficient_groups`), not `below_minimums`. The trigger enforces this precedence.
6. **Label edge rules:** pooled without a decision, or a coefficient of exactly zero, gives "not enough data".
7. **A zero standard error** gives p = 0 when k > 0 and 1 otherwise, and stores no t (JSON cannot hold infinity).

## PRD corrections and clarifications (for the next PRD update)

1. 5.7 "Reference test" and 13.1: the reference numbers and tolerance are the approved ones (CLAUDE.md, register `reference_numbers`, `reference_test_tolerance`), not 427 ± 61 / 428 ± 64 with ±1.
2. 5.8 "Checked against the sprint data": 97 / 22 / 20 / 74 pooled and 76 / 13 / 19 for MPEA (tension only).
3. 5.10: calibration is reported both ways (owner, 2026-10-05); the estimated method is method III (register `calibration_noise_levels`). The first-result figures (7.2%, 9.2%) are not reproduced on the current sets (about 7.8% to 8.3% for the fixed method); replace them.
4. 5.8: under the fixed option, a run below the minimums is withheld run-wide (decision 1); estimated power is the fixed calibration's effect share (decision 5).
5. 7 (analysis_result.label): the four labels and their rules (`per_source_labels`).
6. 7 (run): `evidence_level` 1 to 6.
7. 15, step 7: the gap report text moves to step 8 (the Analyst explains the stored gap facts and may not produce its own), the workbook and the plot to step 10.
8. 5.7: the per-fit alloy rule; the minimums are counted on each fit's records.
9. 3.1 / 5.4: "partly sufficient" reaches the run through a step 8 path; step 7's copy function only copies.

## Open items

1. **Second-model review** of the three safeguard changes, then the owner's sign-off. `calibration_noise_levels` moves to "in force" after it.
2. **Owner:** `records_without_group` (before step 8); `curator_tabular_sources` (before step 8, from step 6).
3. **Step 8:** the Analyst explains the stored record and gap facts only; the orchestrator calls `copy_decision` after the Analyst; how "partly sufficient" reaches the run.
4. **Step 10:** the plot from the stored records found (below the minimums: raw data, no fitted line); the label and `REAL_RUN` on every screen and list; the workbook.
5. **Carried:** the step 5 and step 6 open items for steps 8 to 10; live registration of sources (owner).

## Questions for the reviewer

1. Is the estimated calibration (method III, truncation recorded, unavailable when not estimable) a sound and honestly described departure from PRD 5.10, and can it influence any decision?
2. Can Statistics or the gap facts reach anything beyond their lists: a record outside the frozen sets, a value as reported, another run's data, or (gap facts) an outcome value?
3. Does migration 0004 enforce the withheld rule, the labels and the calibration rules completely, and is it safe with the previous release's code and on the live database?
4. Under the fixed option below the minimums, does anything stored (results, calibration, stage outputs, gap facts) carry a number computed from outcome values?
5. Are the two tolerance tiers justified, and does every reference result come from the stated path?
6. Is any claim stronger than the code supports?
```


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


## 3. CLAUDE.md

### `CLAUDE.md`

```markdown
# HypoCurate — instructions for Claude Code

Version: 2026-10-04 v1. Owner: Khalid El-Awady.

## What this is

HypoCurate takes a scientific hypothesis in words (first domain: grain-size strengthening in metal alloys), searches registered data sources, and ends in one of three outcomes stated for the sources searched: **sufficient** (a test and a verdict), **partly sufficient** (no verdict on the original question; a narrower question is a separate linked record), or **insufficient** (a gap report, never a forced verdict).

The full specification is `docs/PRD_sprint1.md`. Read the relevant section before you write code. If this file and the PRD disagree, stop and ask.

## How we work

1. **One build step at a time.** The build order is PRD Section 15. Do not start a step until the owner says so. Do not build ahead.
2. **Plan first.** For each step, propose a plan and wait for approval before changing files.
3. **Tests are the gate.** Every step adds tests to the regression suite. A step is finished only when the whole suite passes. Never weaken, skip or delete a test to make it pass; never widen a tolerance. If a test seems wrong, stop and ask.
4. **End of each step:** write a short summary in `docs/reviews/` (what was built, which tests were added, what is open) so a second model (ChatGPT) can review it. Its review is advice; the tests decide.
5. **Any change to a safeguard** (access layer, checkpoints, validity checks, eligibility rules) needs the owner's approval and a second-model review, even if small.
6. **Ask one question at a time**, in plain English, with options and a recommendation.
7. **Deferred ideas go in the backlog** (PRD Section 18). Do not build them.
8. Small commits with clear messages. Never commit to `main` anything that fails the suite.
9. **Any change to `.github/workflows/` needs the owner's explicit review**, even if the workflow tests pass. A workflow test cannot stop its own job from being skipped (for example by a job-level condition), and Render counts a skipped check as passed.
10. **A change to `render.yaml` takes effect at push, before the checks pass**, and redeploys the code already running (Render's Blueprint sync; seen on the step 3 merge, 2026-10-05). So any setting that depends on new code goes in a later merge than that code, and every `render.yaml` change needs the owner's explicit review, like workflow changes.

11. **Assumptions register.** Any new assumption or changed default is entered in `hypocurate/assumptions.json` in the same merge, with its reason, who decided it and when, and its earlier value in the history. The page /assumptions is generated from that file only.
12. **One named place per default.** Code reads a default from one named setting (a module constant, a source definition, a plan default or a database constraint), never from a literal scattered through the code. A register entry applied in code ("yes" or "partly") names that setting; `tests/test_assumptions.py` fails if it does not exist or holds a different value. That is a reference and value check only: it does not show that the entry's wording matches what the code does. Behaviour is covered by the regression tests the entry names, and the register test checks only that they exist.

## Rules the code must never break

1. **Code decides; agents advise.** Inclusion of records, flags, the choice of test, data sufficiency and the verdict are computed by code. No language model output may set them.
2. **Access contract (PRD Section 4).** Every agent reads data only through the access layer, which holds an allow-list of fields per role and stage. Anything else raises `AccessDenied` and is written to the audit log. Tests check a role's *complete* input, including a planted-value test.
   - Planner: fills template parameters; sees counts only, never outcome values.
   - Curator: extraction only; is not told the direction of the claim; has no say over inclusion.
   - Critic: classifies flags from sources and metadata; is told the kind of flag, not the numbers; never sees outcomes.
   - Analyst: explains results that code has already computed.
   - Commentator: outside the decision path; a different model; optional. Its numbers are checked against the run record; label: "numbers checked against the run record".
3. **Two checkpoints (PRD 5.6).** *Rules lock* before curation: the model, scope, exclusion rules and data-sufficiency option are fixed. *Dataset freeze* before analysis: the record set is fixed and fingerprinted. Nothing changes after its checkpoint, by agent or by person. Later removals are sensitivity analyses only and never change the verdict.
4. **Stored is not analysed (PRD 5.3).** Every record found is kept. Eligibility for the test is a separate decision by code under the locked rules. Conflicting records are preserved, not automatically pooled.
5. **Two validity checks that can never be waived (PRD 5.7).** (1) Can a coefficient be fitted? (2) Is inference valid (at least 1 residual degree of freedom and at least 2 independent groups)? If 1 passes and 2 fails: report the coefficient only, with no uncertainty, no p-value and no verdict.
6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction; one-sided test of k > 0 at 0.05 against a t distribution with (groups − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
7. **Data sufficiency is a query parameter fixed at rules lock (PRD 5.8).** Default: fixed minimum (30 records, 5 alloys with at least 2 grain sizes, 10 independent papers, 10 residual degrees of freedom). "Use what is available" waives the threshold only, never the validity checks, and labels the result exploratory.
8. **A narrower question is a separate record**, linked to the original. The original gets no verdict.
9. **Three kinds of "nothing found" stay distinct:** a reported negative result, missing evidence, and a failed search.
10. **Model-recalled data are never pooled** and never count toward a verdict.
11. **Per-run calibration (PRD 5.10) is a flag, not a gate.** When inference cannot run, show "calibration unavailable" with the reason. Software correctness (pass/fail against an independent reference) is separate from calibration (a reported finding).
12. **Every model call is recorded** with tokens and actual cost (`model_call`). Spending caps: $2 per run, $50 per month.
13. **Wording:** outcomes are always stated "in the sources searched". Never write that data "do not exist".
14. **Nothing a model controls ever receives SQL, a database connection or a file path.** Agents get data only as text built from an access object that the trusted dispatcher (`hypocurate.access.dispatch.bind`) bound to a run, role, stage and source. No code gives an agent a tool that runs SQL, opens files or executes code.

## Threat model (owner, 2026-10-05)

The access layer and its tests guard against **our own code** leaking data to a model. In sprint 1 agents are language models that return text only: they never execute code and never receive SQL or file tools. Only trusted, reviewed code runs, and a trusted dispatcher binds each agent call to a run, role, stage and source. The access layer is not a boundary against hostile code running in the same process, and the file guard is a tripwire against accidental file access, not a sandbox. The only construction-level guarantee about answer material is that the deployed image contains no `tests/` or `docs/`. Agents that execute code are in the backlog, with operating-system isolation as a precondition. Do not claim more than this anywhere.

## Environment

- Development happens in a GitHub Codespace. Nothing lives on the owner's laptop. The site runs on Render: pushing to `main` on GitHub deploys it.
- Stack: Python, FastAPI + Jinja + HTMX, one background worker (same code as the command line), PostgreSQL + Alembic, DSPy + litellm, statsmodels/scipy, Docker from day one (`Dockerfile`, `docker-compose.yml`, `render.yaml`).
- Repository layout: PRD Section 6.1.
- **Secrets** (API keys, database URL, login password) live in `.env` locally and in Render environment variables. Never commit them, print them, or put them in tests. Keep `.env.example` with names only.
- Do not create Render services or anything else that costs money without asking first.

## Reference material in `docs/`

- `PRD_sprint1.md` — the specification (PDF copy alongside).
- `HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf` — background and research questions.
- `glossary.json` — the 41 explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
- `mockup_screens/` — the nine target screens.
- `reference/worked_example.py`, `reference/calibration_example.py` — the scripts that produced the reference numbers. They contain file paths from another machine; treat them as a statement of method, not as code to import.

## Reference numbers (fixed-plan test, PRD 14.1a)

Under the owner's decisions of 2026-10-05 (tension only; Texas A&M room temperature and single-phase FCC assigned by decision); recomputed test-side in step 6 and approved by the owner on 2026-10-06 (register entry `reference_numbers`, which keeps the earlier values in its history). Pooled: 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6. First source alone (MPEA): 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6. Each "±" is one standard error (cluster-robust, by group), not a confidence interval. Second source alone (Texas A&M): 21 records, 9 alloys, coefficient ≈ 1173, one group, no uncertainty, no verdict. The statistics module (step 7) must reproduce these independently; the step 6 values come from a test-side script, not from package code.
```


## 4. Core rules (from `docs/PRD_sprint1.md`)

```markdown
## 3.1 The three outcomes

| **Outcome** | **What the system returns** |
|---|---|
| Sufficient | A verdict from the pooled test, per-source results, sensitivity analyses and a curated dataset. |
| Partly sufficient | No verdict on the original question. A narrower question is stored as a separate, labelled record linked to the original, with its own locked plan and verdict. A gap report says what is missing for the original. |
| Insufficient in the sources searched | No verdict. A gap report listing missing fields, the shortfall against the required sample size, the sources searched and not searched, and the kind of "nothing found". |

Every result lists the sources searched and the sources not searched. A field missing from one dataset shows a gap in that dataset, not that the measurement was never made.

The three kinds of "nothing found" are: a **reported negative result** (the measurement was made and showed no effect), **missing evidence** (no one has reported the measurement in the sources searched), and a **failed search** (the system could not reach or read a source).

## 5.6 Two checkpoints: the rules lock and the dataset freeze

| **Checkpoint** | **When** | **What it fixes** |
|---|---|---|
| Rules lock | After the Planner, before curation | The plan: model parameters, scope, exclusion rules, eligibility rules, data-sufficiency option, sensitivity analyses. Stored with a fingerprint and a time. |
| Dataset freeze | After inclusion, checks and the Critic, before analysis | The analysis dataset: exactly which records enter the primary analysis and each sensitivity analysis. Stored with a fingerprint and a time. |

- Between the two checkpoints the set of records changes only by applying the locked rules. No agent and no person can add or remove a record by choice.

- After the dataset freeze nothing changes. Outcome values become visible to the statistics code and the Analyst only after it.

- A removal proposed after the rules lock, by an agent or a person, is recorded and appears only in a labelled sensitivity analysis.

- If no records are eligible, no dataset is frozen and no test is run; the run ends as insufficient.

## 5.7 The supported statistical model

Sprint 1 supports one model. The Planner fills in its parameters; it does not choose a test freely. The list of supported models is built so that more can be added later.

| **Element** | **Specification** |
|---|---|
| Formula | Yield strength = a baseline for each alloy + k × (grain size in µm)^-½. One baseline (intercept) per alloy; one shared coefficient k. |
| Fitting | Ordinary least squares. |
| Uncertainty | Standard error of k with records grouped by source paper (cluster-robust, with the small-sample correction). Each source states its grouping unit: the paper for literature data; for a single-laboratory dataset without per-record papers, the whole dataset is one group unless the adapter defines a unit such as a batch. |
| Hypotheses and reference distribution | Null: k ≤ 0. Alternative: k \> 0. One-sided test; threshold 0.05 unless the plan sets another. The statistic is judged against a t distribution with (number of groups − 1) degrees of freedom. |
| Validity check 1: can a coefficient be fitted? | At least one alloy measured at two distinct grain sizes. If not, nothing is fitted. |
| Validity check 2: is the inference valid? | Residual degrees of freedom (records − alloys − 1) of at least 1, and at least 2 independent groups; these are the hard floor below which no uncertainty can be computed. If check 1 passes and check 2 fails, the coefficient is reported alone: no uncertainty, no p-value, no verdict. |
| Which alloys can be used | Only alloys measured at two or more distinct grain sizes within the plan's scope. Others are kept in the store and marked not eligible. |
| Allowed exclusion rules | From the menu in Section 5.2 only. |
| Per-source results | The same model fitted on each source alone; descriptive. |
| Sensitivity analyses | The same model on the alternative record sets defined by the plan. |

- **The validity checks cannot be waived.** They are separate from data sufficiency (Section 5.8) and apply to the pooled test, to each per-source result and to each sensitivity analysis. One alloy at two grain sizes gives a slope but no way to estimate its uncertainty, and a source that is a single group has no computable grouped uncertainty.

- **Code decides; the Analyst explains.** Code determines whether the data are sufficient and what the statistical decision is. The Analyst never computes or changes a result.

- **Reference test.** The result k = 427 ± 61 is tested with a fixed plan and a fixed copy of the source, with numerical tolerances (for example ±1 on k and on its uncertainty). With 20 papers the p-value is about 6×10⁻⁷. The live Planner is tested separately; a statistics regression must not depend on a model producing the same plan again.

## 5.8 How much data is enough

This is a parameter of the query, chosen before dispatch and fixed at the rules lock. Changing it requires a new version of the query. It is applied after the two validity checks of Section 5.7, which no option can waive.

| **Option** | **What the user sets** | **How sufficiency is decided** |
|---|---|---|
| Fixed minimum (default in sprint 1) | Minimum records, alloys measured at two or more grain sizes, independent papers, and residual degrees of freedom. Starting values: 30, 5, 10 and 10. | Simple counts. All four must be met. |
| Power-based | Significance threshold, power wanted, smallest effect worth detecting, expected scatter, and an assumed similarity of records within a paper. | Code computes, from the grain sizes found, an estimated power under the stated assumptions. Not used as the gate in sprint 1 until the calculation has been specified and reviewed. |
| Use what is available | Nothing. | Any data that pass the validity checks are tested. The result is labelled "exploratory". |

- **Why fixed minimums are the default.** The power calculation needs an assumption about how alike the records within one paper are, as well as the grain-size spread and the expected scatter. Until that calculation is written down and reviewed, it should not decide whether a test runs.

- **Checked against the sprint data.** Pooled (98 records, 22 alloys, 21 groups, 75 residual degrees of freedom): met. MPEA alone (77, 13, 20): met. Texas A&M alone (21 records, 9 alloys, 1 group): not met, and it also fails validity check 2.

- **Estimated power.** The power figure may be computed and shown for information under any option. It is always labelled "estimated power under the stated assumptions", never "power achieved".

- The power check uses only the predictor (grain sizes), never the outcome, so it can be done at the dataset freeze, before any outcome is visible. The same calculation can tell the gap report roughly how much more data are needed.

- **Exploratory** waives the sufficiency threshold only. It does not waive either validity check.

- The starting values are to be confirmed with Prof. El-Awady.

## 5.9 Record of statistical significance, and commentary

Every run output contains two things that speak to how far the result can be trusted.

- **Record of statistical significance (written by code).** The estimate and its uncertainty; the test, p-value and threshold; the numbers of records, alloys and sources used; the outcome of the two validity checks; the degrees of freedom and number of groups; the data-sufficiency option and whether it was met; the estimated power under the stated assumptions, where computed; the per-source results; and the sensitivity results.

- **Commentary (written by the Commentator).** A fifth role, outside the decision path. After the verdict is final it reads the query and the complete output and comments on the result, in particular on the limits of its statistical significance.

- The Commentator uses a different model from the pipeline by default. It works from a fixed checklist: few papers; hidden causes in observational data; effect size against significance; several sources compared at once; the assumptions behind the power calculation; the limits of the scope; and what would strengthen the result.

- It may quote only numbers that are in the run record. Code checks every number in the commentary against the record and shows the result as "numbers checked against the run record: all match" or lists those that do not. This checks numerical consistency only. It does not verify the interpretation, and the label must never suggest that the commentary as a whole has been verified.

- **Optional in sprint 1.** The Commentator is built last and is not part of the required acceptance criteria. It is switched on once criteria 14.1 to 14.4 pass.

- It cannot change the plan, the records, the verdict or the outcome. Its text is labelled as model commentary, not evidence and not the verdict.

- If the commentary call fails, the run still completes and shows "commentary unavailable".

- The pipeline that produces the result still has four agents. The Commentator runs the same way in the later single-agent comparison.

## 5.10 Calibration on generated data

For every real run in which inference is valid, after the dataset freeze, code checks the behaviour of the test on simulated outcomes with that run's data structure, under stated assumptions. It needs no materials knowledge, uses no real outcome values and makes no model calls.

1.  Keep the structure of the frozen dataset: the same records, alloys, groups and grain sizes.

2.  Replace the outcomes with generated ones: a baseline per alloy, a shift per group, scatter per record, and a chosen true effect.

3.  Run the locked test on the generated data. Repeat many times (default 2,000) in each of two simulated worlds.

4.  **A simulated world with no effect** (true k = 0): record the share of simulations in which the test is significant.

5.  **A simulated world with the smallest effect that matters:** record the share in which the effect is detected.

6.  Report each share with a 95% confidence interval (exact binomial), because it comes from a finite number of simulations.

- **What it does and does not say.** It describes test behaviour on simulated outcomes with this data structure, under the stated assumptions. It does not say how trustworthy the real result is, and it does not check the real data for errors in extraction or inclusion.

- **Assumptions.** The scatter, the size of the shift between groups, and the smallest effect that matters come from the domain profile and are fixed at the rules lock. They are never estimated from the real outcomes, which would break the blinding. Every result is shown with its assumptions.

- **When it is unavailable.** Calibration is not attempted when inference cannot run. The run then shows "calibration unavailable" with the reason: no dataset frozen; a coefficient cannot be fitted; or insufficient independent groups (for example a single-group source). The same applies to each per-source and sensitivity analysis.

- **Flag, not gate.** When the interval for the no-effect share excludes the significance threshold, the run shows a flag: "the method is over-confident (or under-confident) on this data structure under the stated assumptions". The calibration does not change the outcome or the verdict in sprint 1.

- **Why a simulation.** It uses the real grouping of records by paper directly, which a power formula has to assume. It is the intended basis for the power-based option of Section 5.8 once reviewed.

- **First result, on the sprint data** (scatter 60 MPa, group shift 40 MPa, 2,000 simulations; illustrative assumptions). Pooled dataset, no effect: significant in 7.2% (95% interval 6.1% to 8.4%) against a nominal 5%. MPEA dataset alone, no effect: 9.2% (8.0% to 10.6%). Effect of 150: detected in 2,000 of 2,000 simulations (at least 99.8%). Under these assumptions the specified grouped test is somewhat over-confident on data shaped like this.

- It is deterministic for a given seed, which is stored with the run.

# 4. Access contract

What each role can see is fixed in code, by role and by stage. There is no general unlock at either checkpoint. Roles that can add or remove records never see outcome values. Every read goes through the data-access layer and is written to an audit log.

| **Role** | **Can see** | **Cannot do or see** |
|---|---|---|
| Planner (agent) | The claim in words; record counts by field | Outcome values, at any stage |
| Curator, extraction (agent) | The source it is reading; the list of fields to extract | The direction of the claim; any say over which records are included |
| Inclusion (code) | The locked rules; record fields | Discretion: rules are applied exactly as written |
| Checks (code) | All values | Judgment: it only raises flags |
| Critic (agent) | Sources, metadata, and the kind of each flag raised by code | Outcome values, including the numbers behind a flag; choosing between conflicting values |
| Analyst (agent) | Results and outcome values, after the dataset freeze | Changing the plan, the records, or the verdict that code computed |
| Commentator (agent) | The query and the complete output, after the verdict is final | Changing anything; using numbers that are not in the run record |

**Allowed fields, not blocked fields.** Each role has a written list of the fields it may receive, kept in code next to the access layer. Anything not on the list is withheld. Removing the outcome column alone is not enough: outcome values can also leak through the numbers stored with a flag, through values as originally reported, through nested fields, and through explanatory text passed between stages.

**Implementation requirement.** Each agent role receives a data-access object built for that role and stage. A call that the role is not allowed to make raises an AccessDenied error and writes a row to the audit log. A flag passed to the Critic carries its kind, the record identifiers, the metadata and a category (for example "differ beyond tolerance" or "identical values"), never the numbers compared. The contract can be relaxed only by an explicit experiment flag on the run, which is recorded and shown in the run viewer.

**Testing requirement.** Access is tested on everything a role receives: the prompt text, every tool response and any text handed over from an earlier stage. The test data contain distinctive planted outcome values, and the tests fail if any of them appears anywhere in the input of the Planner or the Critic.
```


## 5. New package code (full text)

### `hypocurate/pipeline/statistics.py`

```python
"""The supported statistical model, its two validity checks, data sufficiency and the verdict
(PRD 5.7, 5.8; CLAUDE.md rules 5 to 7; build step 7). Pure functions: no database, no model.

**The one model** (CLAUDE.md rule 6; register 'model_form'): yield strength = a baseline per
alloy + k × (grain size in µm)^-1/2. Ordinary least squares with one intercept per alloy and one
shared coefficient k, computed by removing each alloy's mean from the predictor and the outcome
(the same estimate as fitting the alloy intercepts; Frisch-Waugh-Lovell). Its standard error is
cluster-robust, grouped by each source's grouping unit, with the small-sample correction
G/(G-1) × (N-1)/(N-K), K = alloys + 1 (statsmodels' default for clustered errors; register
'cluster_robust_se'). The test is one-sided, k > 0, against a t distribution with G - 1 degrees of
freedom, at the plan's threshold; "supported" exactly when p < alpha (register
'p_threshold_comparison').

**Which records a fit uses** (owner, 2026-10-05, decision 7): only alloys with at least
`MODEL_MIN_GRAIN_SIZES` distinct grain sizes among the analysis's own records. This is the model's
own condition, applied to grain sizes only; the frozen set is not changed and the others are
reported as "not used in this fit". **The minimums are counted on the records the fit uses**
(owner, 2026-10-05).

**The two validity checks** can never be waived (CLAUDE.md rule 5): (1) a coefficient can be fitted
when at least one alloy has two distinct grain sizes; (2) inference is valid with at least 1
residual degree of freedom (records - alloys - 1) and at least 2 independent groups. Check 1 only:
the coefficient alone, no uncertainty, no p-value, no verdict.

**Below the minimums under the fixed option** (owner, 2026-10-05, decision 1): when the pooled fit
misses any minimum, every analysis of the run is withheld: counts against each minimum, which were
missed, and the records found; nothing computed from outcome values. Label
"data found; not enough to test".

**Results are a pure function of the frozen set and the locked plan.** Records are sorted by their
stable identity (source-version fingerprint, origin key, item index) before any arithmetic, and
alloys and groups are indexed by their sorted keys, so record ids and insertion order cannot change
a number.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy import stats

# The model's own alloy condition (CLAUDE.md rule 6; PRD 5.7 "which alloys can be used").
MODEL_MIN_GRAIN_SIZES = 2
# The predictor's transformation, by the locked plan's code (register
# 'grain_size_transformation_at_analysis').
TRANSFORMATIONS = MappingProxyType({"inverse_square_root": lambda d: d ** -0.5})

# Wording (CLAUDE.md rule 13: outcomes are stated "in the sources searched").
VERDICT_WORDING = MappingProxyType({
    "supported": "supported under the stated model, in the sources searched",
    "not_supported": "not supported under the stated model, in the sources searched",
})
OUTCOME_WORDING = MappingProxyType({
    "sufficient": "sufficient in the sources searched",
    "insufficient": "insufficient in the sources searched",
})
BELOW_MINIMUMS_LABEL = "data found; not enough to test"
EXPLORATORY_LABEL = "exploratory"
POWER_LABEL = "estimated power under the stated assumptions"

# The evidence level (owner, 2026-10-05; register 'evidence_level_scale'): descriptive only, derived
# by `evidence_level` from the result state, never by an agent; it never affects the outcome or the
# verdict. A partly sufficient original question keeps the level of its own pooled result state.
EVIDENCE_LEVELS = MappingProxyType({
    6: "sufficient with a verdict",
    5: "use what is available with a minimum missed (exploratory)",
    4: "inference invalid: coefficient only",
    3: "below the minimums under the fixed option",
    2: "coefficient cannot be fitted",
    1: "no dataset frozen",
})
STATE_LEVELS = MappingProxyType({"sufficient": 6, "exploratory": 5, "coefficient_only": 4, "below_minimums": 3,
                                 "not_fitted": 2, "no_dataset_frozen": 1})

# The per-source labels (owner, 2026-10-05, decision 2): descriptive only, never the verdict.
LABELS = ("agrees", "conflicts", "same_direction_different_decision", "not_enough_data")


class StatisticsError(ValueError):
    """The data cannot be analysed as specified (for example a record without a group)."""


@dataclass(frozen=True)
class Observation:
    identity: str  # stable identity: the sort key, never a database id
    alloy: str
    group: str
    grain_size: float  # µm
    outcome: float


@dataclass(frozen=True)
class Design:
    """The records one fit uses, in identity order, with alloys and groups indexed by sorted key."""
    x: np.ndarray  # transformed predictor
    y: np.ndarray
    alloy: np.ndarray  # alloy index per record
    group: np.ndarray  # group index per record
    n_alloys: int
    n_groups: int
    n_records_in_set: int
    n_alloys_not_used: int

    @property
    def n(self) -> int:
        return int(self.x.size)

    @property
    def resid_df(self) -> int:
        return self.n - self.n_alloys - 1

    @property
    def coefficient_fitted(self) -> bool:  # validity check 1
        return self.n_alloys >= 1

    @property
    def inference_valid(self) -> bool:  # validity check 2
        return self.coefficient_fitted and self.resid_df >= 1 and self.n_groups >= 2


def design(observations: Iterable[Observation], transformation: str) -> Design:
    """The fit's records: alloys with at least two distinct grain sizes among these records."""
    obs = sorted(observations, key=lambda o: o.identity)
    if len({o.identity for o in obs}) != len(obs):
        raise StatisticsError("two records share one stable identity")
    sizes: dict[str, set] = {}
    for o in obs:
        if not (math.isfinite(o.grain_size) and o.grain_size > 0 and math.isfinite(o.outcome)):
            raise StatisticsError("a record in a frozen set has no finite positive grain size or finite outcome")
        sizes.setdefault(o.alloy, set()).add(o.grain_size)
    used_alloys = sorted(a for a, s in sizes.items() if len(s) >= MODEL_MIN_GRAIN_SIZES)
    keep = set(used_alloys)
    used = [o for o in obs if o.alloy in keep]
    groups = sorted({o.group for o in used})
    alloy_index = {a: i for i, a in enumerate(used_alloys)}
    group_index = {g: i for i, g in enumerate(groups)}
    transform = TRANSFORMATIONS[transformation]
    return Design(
        x=np.array([transform(o.grain_size) for o in used], dtype=float),
        y=np.array([o.outcome for o in used], dtype=float),
        alloy=np.array([alloy_index[o.alloy] for o in used], dtype=int),
        group=np.array([group_index[o.group] for o in used], dtype=int),
        n_alloys=len(used_alloys), n_groups=len(groups), n_records_in_set=len(obs),
        n_alloys_not_used=len(sizes) - len(used_alloys))


def demeaned(values: np.ndarray, alloy: np.ndarray, n_alloys: int) -> np.ndarray:
    """Each value minus its alloy's mean (works on the last axis, for one or many outcome rows)."""
    counts = np.bincount(alloy, minlength=n_alloys).astype(float)
    if values.ndim == 1:
        return values - (np.bincount(alloy, values, n_alloys) / counts)[alloy]
    indicator = np.zeros((alloy.size, n_alloys))
    indicator[np.arange(alloy.size), alloy] = 1.0
    return values - ((values @ indicator) / counts)[:, alloy]


def small_sample_factor(n: int, n_alloys: int, n_groups: int) -> float:
    """G/(G-1) × (N-1)/(N-K), K = alloys + 1 (register 'cluster_robust_se')."""
    return (n_groups / (n_groups - 1)) * ((n - 1) / (n - n_alloys - 1))


def one_sided_p(t: float, df: int) -> float:
    """P(T > t) for T ~ t(df). A zero standard error gives p = 0 when k > 0, else 1."""
    if math.isinf(t):
        return 0.0 if t > 0 else 1.0
    return float(stats.t.sf(t, df))


@dataclass(frozen=True)
class Fit:
    estimate: float
    std_error: float | None
    t: float | None
    df: int | None
    p_value: float | None


def fit(d: Design) -> Fit | None:
    """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
    if not d.coefficient_fitted:
        return None
    xd = demeaned(d.x, d.alloy, d.n_alloys)
    yd = demeaned(d.y, d.alloy, d.n_alloys)
    sxx = float(xd @ xd)
    k = float(xd @ yd) / sxx
    if not d.inference_valid:
        return Fit(k, None, None, None, None)
    e = yd - k * xd
    scores = np.bincount(d.group, xd * e, d.n_groups)
    variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
    se = math.sqrt(variance)
    t = k / se if se > 0 else (math.inf if k > 0 else -math.inf)
    df = d.n_groups - 1
    return Fit(k, se, t, df, one_sided_p(t, df))


def minimums(d: Design, sufficiency: Mapping) -> dict:
    """Each count of the fit against its minimum (PRD 5.8)."""
    counts = {"records": d.n, "alloys": d.n_alloys, "groups": d.n_groups, "resid_df": d.resid_df}
    keys = {"records": "min_records", "alloys": "min_alloys", "groups": "min_groups", "resid_df": "min_resid_df"}
    return {name: {"count": counts[name], "minimum": sufficiency[keys[name]],
                   "met": counts[name] >= sufficiency[keys[name]]} for name in counts}


def significant(p_value: float | None, alpha: float) -> bool | None:
    return None if p_value is None else p_value < alpha


def label(per_source: Mapping, pooled: Mapping, alpha: float) -> str:
    """The four per-source labels (owner, 2026-10-05): from the locked test and the sign only."""
    if per_source.get("p_value") is None or pooled.get("p_value") is None:
        return "not_enough_data"
    a, b = per_source["estimate"], pooled["estimate"]
    if a == 0 or b == 0:
        return "not_enough_data"
    if (a > 0) != (b > 0):
        return "conflicts"
    if significant(per_source["p_value"], alpha) == significant(pooled["p_value"], alpha):
        return "agrees"
    return "same_direction_different_decision"


def result_state(pooled: Mapping | None, option: str) -> str:
    """The run's result state from its pooled result. Precedence: no dataset frozen; below the
    minimums under the fixed option (decision 1 withholds run-wide); coefficient cannot be fitted;
    inference invalid; exploratory; sufficient."""
    if pooled is None:
        return "no_dataset_frozen"
    if pooled["withheld"]:
        return "below_minimums"
    if not pooled["checks"]["coefficient_fitted"]:
        return "not_fitted"
    if not pooled["checks"]["inference_valid"]:
        return "coefficient_only"
    if option == "use_available" and not pooled["minimums_met"]:
        return "exploratory"
    return "sufficient"


def evidence_level(state: str) -> int:
    """The evidence level of a result state (register 'evidence_level_scale')."""
    return STATE_LEVELS[state]


def decision(pooled: Mapping | None, plan: Mapping, freeze_fingerprint: str | None) -> dict:
    """The stored decision: outcome, verdict, exploratory, evidence level, with the freeze it
    belongs to. Copied onto the run later, unchanged (`completion.py`)."""
    option = plan["sufficiency"]["option"]
    state = result_state(pooled, option)
    verdict = None
    if state in ("sufficient", "exploratory"):
        verdict = "supported" if significant(pooled["p_value"], plan["model"]["alpha"]) else "not_supported"
    outcome = "sufficient" if verdict else "insufficient"
    return {"freeze_fingerprint": freeze_fingerprint, "state": state, "outcome": outcome,
            "outcome_wording": OUTCOME_WORDING[outcome], "verdict": verdict,
            "verdict_wording": VERDICT_WORDING[verdict] if verdict else None,
            "exploratory": state == "exploratory", "evidence_level": evidence_level(state),
            "evidence_level_wording": EVIDENCE_LEVELS[evidence_level(state)],
            "label": BELOW_MINIMUMS_LABEL if state == "below_minimums" else
            EXPLORATORY_LABEL if state == "exploratory" else None}


def analysis_entry(d: Design, plan: Mapping, withheld: bool) -> dict:
    """One analysis: counts, checks, minimums, and (unless withheld) the numbers from outcomes."""
    m = minimums(d, plan["sufficiency"])
    entry = {
        "counts": {"n_records_in_set": d.n_records_in_set, "n_records": d.n,
                   "n_records_not_used": d.n_records_in_set - d.n, "n_alloys": d.n_alloys,
                   "n_alloys_not_used": d.n_alloys_not_used, "n_groups": d.n_groups, "resid_df": d.resid_df},
        "checks": {"coefficient_fitted": d.coefficient_fitted, "inference_valid": d.inference_valid},
        "minimums": m, "minimums_met": all(v["met"] for v in m.values()), "withheld": withheld,
        "estimate": None, "std_error": None, "t": None, "df": None, "p_value": None,
        "alpha": plan["model"]["alpha"], "significant": None,
    }
    if withheld:
        return entry
    f = fit(d)
    if f is not None:
        t = f.t if f.t is None or math.isfinite(f.t) else None  # a zero standard error: no finite t to store
        entry.update(estimate=f.estimate, std_error=f.std_error, t=t, df=f.df, p_value=f.p_value,
                     significant=significant(f.p_value, plan["model"]["alpha"]))
    return entry


def pooled_withheld(pooled_design: Design, plan: Mapping) -> bool:
    """Decision 1: under the fixed option, the pooled fit missing any minimum withholds the run."""
    m = minimums(pooled_design, plan["sufficiency"])
    return plan["sufficiency"]["option"] == "fixed_minimum" and not all(v["met"] for v in m.values())


def analyses_of(plan: Mapping, sets: Mapping[str, Sequence[int]], sources: Mapping[int, str]) -> list[tuple]:
    """(analysis key, scope, set key, source) for the pooled result, each source within the primary
    set (key order), and each sensitivity set the plan names (in the plan's order)."""
    out = [("pooled", "pooled", "primary", None)]
    for source in sorted({sources[i] for i in sets["primary"]}):
        out.append((f"per_source:{source}", "per_source", "primary", source))
    for key in plan["sensitivity_analyses"]:
        out.append((f"sensitivity:{key}", "sensitivity", key, None))
    return out
```

### `hypocurate/pipeline/calibration.py`

```python
"""Per-run calibration on generated data (PRD 5.10; CLAUDE.md rule 11; build step 7). Pure functions.

**A flag, never a gate.** It describes how the locked test behaves on simulated outcomes with
this analysis's structure (the records the fit uses, their alloys, groups and grain sizes), under
stated assumptions. It does not say how trustworthy the real result is and never changes the
outcome, the verdict or inclusion.

**Reported both ways** (owner, 2026-10-05; register 'calibration_both_ways'), each method fixed at
the rules lock by the plan's `calibration` part; no person or agent chooses a value:

- **fixed**: the scatter per record and the shift per group from the plan (PRD 5.10's
  illustrative 60 and 40 MPa by default). It uses no outcome value.
- **estimated**: the scatter σe and the per-group shift σu estimated by code from this analysis's
  frozen records with Henderson's method III (register 'calibration_noise_levels'). This departs
  from PRD 5.10, which fixes them in advance; it is a safeguard change reviewed by a second model.
  1. Fit the locked model (alloy intercepts and k × x): residual sum of squares RSS_R, rank r_R.
  2. Fit it with one intercept per group added: RSS_F, rank r_F.
  3. σe² = RSS_F / (N - r_F). Not estimable when N <= r_F, or when RSS_F is zero (a perfect fit
     gives no scatter to simulate).
  4. σu² = max(0, (RSS_R - RSS_F - (r_F - r_R) σe²) / tr(Z'M_R Z)), where Z is the group
     membership matrix and M_R = I - P_R removes what the locked model explains. Not estimable
     when the trace is zero (the groups are entirely explained by alloys and grain sizes). A
     negative estimate set to zero is recorded (`shift_truncated_at_zero`, with the value before
     truncation).
  An analysis whose scatter or shift cannot be estimated gets "unavailable" with the reason for
  this method; the fixed method is still reported.

**The simulation** (register 'calibration_simulation', 'calibration_error_model',
'normal_errors_in_calibration'): the design is kept; outcomes are replaced by k_true × x + u_g + e_i
with u_g ~ N(0, σu²) per group and e_i ~ N(0, σe²) per record, independent (the alloy baselines are
zero: the alloy intercepts absorb any baseline exactly). In each of two worlds (k_true = 0, and
k_true = the smallest effect) the locked test is run `n_simulations` times; each world draws its
shifts (simulations × groups), then its errors (simulations × records), from one generator seeded
as below, the no-effect world first. Each share has an exact (Clopper-Pearson) 95% interval. The
flag: over-confident when the interval for the no-effect share lies wholly above alpha,
under-confident when wholly below.

**The seed** is the first 63 bits of SHA-256 of "freeze fingerprint|analysis|method", stored with
the result; draws are assigned to records in stable-identity order (`statistics.design`), so ids
and insertion order cannot change a share.

**Estimated power** (owner, 2026-10-05, decision 5) is the effect world's share of the fixed
method, labelled "estimated power under the stated assumptions". It uses no outcome value.
"""
from __future__ import annotations

import hashlib
import math
from typing import Mapping

import numpy as np
from scipy import stats

from hypocurate.pipeline.statistics import Design, demeaned, small_sample_factor

CONFIDENCE = 0.95
FLAG_WORDING = {
    "over_confident": "the method is over-confident on this data structure under the stated assumptions",
    "under_confident": "the method is under-confident on this data structure under the stated assumptions",
    "none": None,
}
# Relative tolerances of the estimator's linear algebra (numerical zero).
TRACE_TOLERANCE = 1e-9


def seed(freeze_fingerprint: str, analysis: str, method: str) -> int:
    digest = hashlib.sha256(f"{freeze_fingerprint}|{analysis}|{method}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") >> 1


def exact_interval(successes: int, n: int, confidence: float = CONFIDENCE) -> tuple[float, float]:
    """Clopper-Pearson interval for a binomial share."""
    tail = (1 - confidence) / 2
    low = 0.0 if successes == 0 else float(stats.beta.ppf(tail, successes, n - successes + 1))
    high = 1.0 if successes == n else float(stats.beta.ppf(1 - tail, successes + 1, n - successes))
    return low, high


def confidence_flag(low: float, high: float, alpha: float) -> str:
    if low > alpha:
        return "over_confident"
    if high < alpha:
        return "under_confident"
    return "none"


def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
    """How many rows of `outcomes` (simulations × records) the locked test finds significant:
    the same estimator, standard error, correction and one-sided t test as `statistics.fit`."""
    xd = demeaned(d.x, d.alloy, d.n_alloys)
    sxx = float(xd @ xd)
    yd = demeaned(outcomes, d.alloy, d.n_alloys)
    k = yd @ xd / sxx
    e = yd - k[:, None] * xd[None, :]
    groups = np.zeros((d.n, d.n_groups))
    groups[np.arange(d.n), d.group] = 1.0
    scores = (e * xd[None, :]) @ groups
    variance = (scores ** 2).sum(axis=1) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(variance > 0, k / np.sqrt(variance), np.where(k > 0, np.inf, -np.inf))
    p = stats.t.sf(t, d.n_groups - 1)
    return int(np.count_nonzero(p < alpha))


def simulate(d: Design, scatter: float, shift: float, smallest_effect: float, n_simulations: int,
             alpha: float, seed_value: int) -> dict:
    """Both worlds; shares, intervals and the flag."""
    rng = np.random.default_rng(seed_value)
    out = {}
    for world, k_true in (("null", 0.0), ("effect", smallest_effect)):
        shifts = rng.normal(0.0, shift, size=(n_simulations, d.n_groups))
        errors = rng.normal(0.0, scatter, size=(n_simulations, d.n))
        outcomes = k_true * d.x[None, :] + shifts[:, d.group] + errors
        hits = significant_count(d, outcomes, alpha)
        low, high = exact_interval(hits, n_simulations)
        out[world] = {"significant": hits, "share": hits / n_simulations, "ci_low": low, "ci_high": high}
    out["confidence_flag"] = confidence_flag(out["null"]["ci_low"], out["null"]["ci_high"], alpha)
    return out


def _rss_and_rank(matrix: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    coef, *_ = np.linalg.lstsq(matrix, y, rcond=None)
    residual = y - matrix @ coef
    return float(residual @ residual), int(np.linalg.matrix_rank(matrix))


def henderson_iii(d: Design) -> dict:
    """σe² and σu² from the analysis's own records (method III), or the reason they cannot be
    estimated. Every intermediate quantity is returned for the record."""
    n = d.n
    alloys = np.zeros((n, d.n_alloys))
    alloys[np.arange(n), d.alloy] = 1.0
    groups = np.zeros((n, d.n_groups))
    groups[np.arange(n), d.group] = 1.0
    reduced = np.column_stack([alloys, d.x])
    full = np.column_stack([alloys, groups, d.x])
    rss_r, rank_r = _rss_and_rank(reduced, d.y)
    rss_f, rank_f = _rss_and_rank(full, d.y)
    q, _ = np.linalg.qr(reduced)
    residual_groups = groups - q @ (q.T @ groups)
    trace = float((residual_groups ** 2).sum())
    out = {"estimation": "henderson_iii", "rss_reduced": rss_r, "rank_reduced": rank_r, "rss_full": rss_f,
           "rank_full": rank_f, "trace": trace, "n_records": n}
    if n <= rank_f or not rss_f > 0:
        return {**out, "reason": "scatter_not_estimable"}
    scatter_sq = rss_f / (n - rank_f)
    out["scatter_squared"] = scatter_sq
    if trace <= TRACE_TOLERANCE * n:
        return {**out, "reason": "shift_not_estimable"}
    shift_sq_raw = (rss_r - rss_f - (rank_f - rank_r) * scatter_sq) / trace
    return {**out, "reason": None, "shift_squared_untruncated": shift_sq_raw,
            "shift_truncated_at_zero": shift_sq_raw < 0, "scatter": math.sqrt(scatter_sq),
            "shift": math.sqrt(max(0.0, shift_sq_raw))}


def calibrate(d: Design, calibration: Mapping, alpha: float, freeze_fingerprint: str, analysis: str,
              method: str) -> dict:
    """One method's calibration of one analysis whose inference is valid: 'computed' with its
    numbers, or (estimated only) 'unavailable' with the reason the noise cannot be estimated."""
    assumptions = {"method": method, "smallest_effect": calibration["smallest_effect"],
                   "n_simulations": calibration["n_simulations"], "alpha": alpha, "errors": "normal",
                   "design": "fixed: the fit's records, alloys, groups and grain sizes"}
    if method == "fixed":
        scatter, shift = calibration["scatter"], calibration["shift"]
        assumptions.update(scatter=scatter, shift=shift, source="the locked plan")
    else:
        estimate = henderson_iii(d)
        if estimate["reason"]:
            return {"status": "unavailable", "reason": estimate["reason"], "estimation": estimate}
        scatter, shift = estimate["scatter"], estimate["shift"]
        assumptions.update(scatter=scatter, shift=shift, source="estimated from the frozen records",
                           estimation="henderson_iii",
                           shift_truncated_at_zero=estimate["shift_truncated_at_zero"],
                           shift_squared_untruncated=estimate["shift_squared_untruncated"],
                           scatter_squared=estimate["scatter_squared"], rss_reduced=estimate["rss_reduced"],
                           rss_full=estimate["rss_full"], rank_reduced=estimate["rank_reduced"],
                           rank_full=estimate["rank_full"], trace=estimate["trace"])
    seed_value = seed(freeze_fingerprint, analysis, method)
    sims = simulate(d, scatter, shift, calibration["smallest_effect"], calibration["n_simulations"], alpha,
                    seed_value)
    return {"status": "computed", "reason": None, "assumptions": assumptions, "seed": seed_value,
            "n_simulations": calibration["n_simulations"], "null": sims["null"], "effect": sims["effect"],
            "confidence_flag": sims["confidence_flag"], "flag_wording": FLAG_WORDING[sims["confidence_flag"]]}
```

### `hypocurate/pipeline/analysis.py`

```python
"""The analysis stage (PRD 5.7 to 5.10; build step 7): the statistics on the frozen sets, the
record of statistical significance, per-run calibration, the gap facts and the stored decision.

**Reads.** Statistics reads only through its access object (`dispatch.bind_code(…, "statistics")`),
which returns the frozen sets and, for their records only, what the model needs
(`frozen_analysis_data`), and only once the dataset is frozen. It never decides inclusion: every
set is used as frozen; the one rule it applies inside a fit is the model's own (alloys with two or
more distinct grain sizes among the analysis's records), reported as "not used in this fit". The
gap facts read through their own access object (`gap_facts`), which carries no outcome value.

**Computation** is a pure function of the frozen data and the locked plan (`analyse`): the same
inputs give the same numbers whatever the record ids or order. Every analysis (pooled, each source
within the primary set, each sensitivity set) goes through the same function. Per-source and
sensitivity results are descriptive and never change the verdict (register 'pooled_gives_verdict',
'sensitivity_one_change'); no adjustment is made for there being several.

**Writes.** One transaction under the run's lock (`writes.write`): the run must be at the
analysis stage (or closed without a freeze), with no result yet; the freeze fingerprint read must
be the run's. It writes `analysis_result` (pooled first), `calibration_result` (both methods per
analysis), and two code stage results: "statistics" (the record of statistical significance, PRD
5.9, and the decision) and "gap_facts" (data only; no report text). A marked run's rows and stage
results carry "test run: includes constructed data". The run itself is not completed here: the
decision is copied onto the run later by `completion.copy_decision`, unchanged.
"""
from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.dispatch import bind_code
from hypocurate.access.errors import AccessDenied
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import calibration as cal
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.binding import record_identity
from hypocurate.pipeline.writes import TEST_RUN_LABEL, Refused, code_stage, log_refusal, marked, write
from hypocurate.sources.record import VALUE_STATUSES

ROLE = "statistics"


# --- Pure: from the frozen data and the locked plan ----------------------------------------------

class RecordsWithoutGroup(st.StatisticsError):
    """Records of a frozen set have no group (a paper not known): no group is invented (register
    'paper_grouping_by_doi'). The pooled analysis refuses; any other analysis is not analysed."""

    def __init__(self, n: int):
        self.n = n
        super().__init__("records_without_group")


def observations(records: list[Mapping], plan: Mapping, set_key: str) -> list[st.Observation]:
    """The records of one analysis as observations: alloy and group by the set's own settings
    (the same functions as Inclusion and the freeze counts), the stable identity as the sort key."""
    settings = el.settings(plan, set_key)
    without_group = sum(el.group(r, settings) is None for r in records)
    if without_group:
        raise RecordsWithoutGroup(without_group)
    out = []
    for r in records:
        group = el.group(r, settings)
        alloy = el.alloy(r, settings.decimals)
        if alloy is None or r["grain_size"] is None or r["outcome"] is None:
            raise st.StatisticsError("a record in a frozen set lacks its composition, grain size or outcome")
        out.append(st.Observation(record_identity(r["version_fingerprint"], r["origin"], r["item_index"]),
                                  alloy, group, r["grain_size"], r["outcome"]))
    return out


def _unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason}


def analyse(plan: Mapping, data: Mapping) -> dict:
    """Every analysis of the run, its calibrations, and the decision (the record of statistical
    significance). `data` is `frozen_analysis_data`."""
    by_id = {r["id"]: r for r in data["records"]}
    sources = {i: r["source"] for i, r in by_id.items()}
    transformation = plan["variables"]["predictor"]["transformation"]
    alpha = plan["model"]["alpha"]
    fp = data["freeze_fingerprint"]
    designs, entries, not_analysed = {}, [], []
    for key, scope, set_key, source in st.analyses_of(plan, data["sets"], sources):
        ids = [i for i in data["sets"][set_key] if source is None or sources[i] == source]
        try:
            designs[key] = st.design(observations([by_id[i] for i in ids], plan, set_key), transformation)
        except RecordsWithoutGroup as missing:
            if scope == "pooled":
                raise
            # A descriptive analysis only: it is reported as not analysed, with the count (owner's
            # decision open; step 7 summary). Fail closed: no group is invented, nothing stored for it.
            not_analysed.append({"analysis": key, "scope": scope, "set": set_key, "source": source,
                                 "reason": "records_without_group", "n_records_without_group": missing.n,
                                 "n_records_in_set": len(ids)})
            continue
        entries.append({"analysis": key, "scope": scope, "set": set_key, "source": source})
    withheld = st.pooled_withheld(designs["pooled"], plan)
    for entry in entries:
        d = designs[entry["analysis"]]
        entry.update(st.analysis_entry(d, plan, withheld))
        if withheld:
            ids = [i for i in data["sets"][entry["set"]] if entry["source"] is None or sources[i] == entry["source"]]
            entry["records_found"] = sorted(record_identity(by_id[i]["version_fingerprint"], by_id[i]["origin"],
                                                            by_id[i]["item_index"]) for i in ids)
            entry["label_text"] = st.BELOW_MINIMUMS_LABEL
    pooled = entries[0]
    for entry in entries:
        entry["label"] = st.label(entry, pooled, alpha) if entry["scope"] == "per_source" else None
        d = designs[entry["analysis"]]
        entry["estimated_power"], entry["power_label"] = None, None
        if not d.inference_valid:
            reason = "coefficient_not_fitted" if not d.coefficient_fitted else "insufficient_groups"
            entry["calibration"] = {"fixed": _unavailable(reason), "estimated": _unavailable(reason)}
            continue
        # The fixed method uses no outcome value: its effect world is the estimated power, shown
        # even below the minimums (owner, decision 5).
        fixed = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "fixed")
        entry["estimated_power"], entry["power_label"] = fixed["effect"]["share"], st.POWER_LABEL
        if withheld:
            entry["calibration"] = {"fixed": _unavailable("below_minimums"),
                                    "estimated": _unavailable("below_minimums")}
        else:
            entry["calibration"] = {"fixed": fixed, "estimated": cal.calibrate(d, plan["calibration"], alpha, fp,
                                                                                entry["analysis"], "estimated")}
    return {"freeze_fingerprint": fp, "model": plan["model"]["name"],
            "test": "one-sided t test of k > 0 against t with (groups - 1) degrees of freedom; "
                    "cluster-robust standard error by group with the small-sample correction",
            "alpha": alpha, "sufficiency_option": plan["sufficiency"]["option"], "withheld": withheld,
            "analyses": entries, "not_analysed": not_analysed, "decision": st.decision(pooled, plan, fp)}


def gap_facts(gap: Mapping, minimums: Mapping | None) -> dict:
    """The facts a gap report needs, as data only (owner, 2026-10-05): counts against each minimum
    and which were missed, how many records lacked which fields, the eligibility rules applied, and
    the kind of "nothing found" per source. No report text; no outcome value."""
    fields = gap["plan"]["content"].get("fields_to_extract", [])
    lacking = {}
    for source in gap["stored_record_counts"]:
        by_status = source.get("by_status", {})
        lacking[source["source"]] = {f: sum(n for status, n in by_status.get(f, {}).items()
                                            if status not in VALUE_STATUSES) for f in fields}
    rules: dict[str, int] = {}
    for d in gap["decisions"]["records"]:
        rules[d["rule"]] = rules.get(d["rule"], 0) + 1
    return {"minimums": minimums, "minimums_missed": sorted(k for k, v in (minimums or {}).items() if not v["met"]),
            "records_lacking_fields": lacking, "eligibility_rules": dict(sorted(rules.items())),
            "sources": [{"source": s["source"], "search_status": s["search_status"], "nothing_found": s["nothing_found"]}
                        for s in gap["coverage"]["sources"]]}


def empty_minimums(plan: Mapping) -> dict:
    """The minimums against a run with no record to analyse (no dataset frozen)."""
    d = st.design([], plan["variables"]["predictor"]["transformation"])
    return st.minimums(d, plan["sufficiency"])


# --- Reads and the write ---------------------------------------------------------------------------

def _read(engine: Engine, run_id: int, role: str) -> tuple[dict, str]:
    try:
        access = bind_code(engine, run_id, role)
    except AccessDenied as denied:
        log_refusal(engine, run_id, ROLE, "run_statistics", "stage_mismatch", denied.code)
        raise Refused("run_statistics", "stage_mismatch", denied.code) from None
    return role_input(access), access.context.stage


_RESULT = text(
    "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, resid_df, "
    "check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, estimated_power, label, withheld, "
    "n_records_not_used, test_run_label) VALUES (:r, :scope, :set, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, "
    ":p, :pw, :lab, :wh, :nu, :tl) RETURNING id")
_CALIBRATION = text(
    "INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, n_simulations, "
    "seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, confidence_flag, "
    "test_run_label) VALUES (:r, :a, :m, :st, :re, :asm, :ns, :seed, :ns_sh, :ns_lo, :ns_hi, :ef_sh, :ef_lo, "
    ":ef_hi, :flag, :tl)").bindparams(bindparam("asm", type_=JSONB(none_as_null=True)))


def _calibration_row(run_id: int, result_id: int, method: str, c: Mapping, label: str | None) -> dict:
    computed = c["status"] == "computed"
    pick = lambda world, k: c[world][k] if computed else None  # noqa: E731
    return dict(r=run_id, a=result_id, m=method, st=c["status"], re=c.get("reason"),
                asm=c["assumptions"] if computed else None, ns=c["n_simulations"] if computed else None,
                seed=c["seed"] if computed else None, ns_sh=pick("null", "share"), ns_lo=pick("null", "ci_low"),
                ns_hi=pick("null", "ci_high"), ef_sh=pick("effect", "share"), ef_lo=pick("effect", "ci_low"),
                ef_hi=pick("effect", "ci_high"), flag=c["confidence_flag"] if computed else None, tl=label)


def run_statistics(engine: Engine, run_id: int) -> dict:
    """The analysis stage of a run whose dataset is frozen, or the closing record of a run with no
    dataset frozen. Returns the stored "statistics" output."""
    gap, stage = _read(engine, run_id, "gap_facts")
    plan = gap["plan"]["content"]
    if stage == "analysis":
        data, _ = _read(engine, run_id, ROLE)
        try:
            record = analyse(data["plan"]["content"], data["frozen_analysis_data"])
        except st.StatisticsError as error:
            code = "records_without_group" if str(error) == "records_without_group" else "changed_since_read"
            log_refusal(engine, run_id, ROLE, "run_statistics", code, str(error))
            raise Refused("run_statistics", code, str(error)) from None
        pooled = record["analyses"][0]
        facts = gap_facts(gap, pooled["minimums"])
        plan_fp, fp = data["plan"]["fingerprint"], record["freeze_fingerprint"]
    else:
        record = {"freeze_fingerprint": None, "analyses": [], "not_analysed": [], "withheld": False,
                  "decision": st.decision(None, plan, None), "no_dataset_frozen": True}
        facts = gap_facts(gap, empty_minimums(plan))
        plan_fp, fp = gap["plan"]["fingerprint"], None

    def body(conn: Connection, now_stage: str):
        if now_stage != stage:
            raise Refused("run_statistics", "stage_mismatch")
        done = conn.execute(text("SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'statistics') "
                                 "OR EXISTS (SELECT 1 FROM analysis_result WHERE run_id = :r)"),
                            dict(r=run_id)).scalar_one()
        if done:
            raise Refused("run_statistics", "already_done")
        snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                dict(r=run_id)).scalar_one_or_none()
        if snapshot != fp:
            raise Refused("run_statistics", "changed_since_read")
        label = TEST_RUN_LABEL if marked(conn, run_id) else None
        sets = dict(conn.execute(text("SELECT key, id FROM analysis_set WHERE run_id = :r"), dict(r=run_id)).all())
        source_ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
        for e in record["analyses"]:
            c = e["counts"]
            rid = conn.execute(_RESULT, dict(
                r=run_id, scope=e["scope"], set=sets[e["set"]], src=source_ids[e["source"]] if e["source"] else None,
                n=c["n_records"], a=c["n_alloys"], g=c["n_groups"], df=c["resid_df"],
                c1=e["checks"]["coefficient_fitted"], c2=e["checks"]["inference_valid"], mm=e["minimums_met"],
                est=e["estimate"], se=e["std_error"], p=e["p_value"], pw=e["estimated_power"], lab=e["label"],
                wh=e["withheld"], nu=c["n_records_not_used"], tl=label)).scalar_one()
            for method in ("fixed", "estimated"):
                conn.execute(_CALIBRATION, _calibration_row(run_id, rid, method, e["calibration"][method], label))
        output = {**record, "test_run_label": label}
        code_stage(conn, run_id, "statistics", {"plan": plan_fp, "freeze": fp}, output)
        code_stage(conn, run_id, "gap_facts", {"plan": plan_fp, "freeze": fp}, {**facts, "test_run_label": label})
        return output

    return write(engine, run_id, ROLE, "run_statistics", body)


def stored_record(engine: Engine, run_id: int) -> dict[str, Any] | None:
    """The stored "statistics" output of a run (tests and the copy path)."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' "
                                 "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
```

### `hypocurate/pipeline/completion.py`

```python
"""Copying the stored decision onto the run (build step 7; owner, 2026-10-05).

`copy_decision` **only copies**. It writes the decision stored by the analysis stage (outcome,
verdict, exploratory label and evidence level, in the "statistics" stage result) onto the run and
completes it, unchanged; it computes nothing. It refuses, and logs the refusal, when the stored
decision is missing (`decision_missing`) or belongs to a different freeze fingerprint than the
run's (`decision_not_current`; a run with no dataset frozen has a decision with no fingerprint,
and a run with a freeze must have the decision of that freeze).

The orchestrator (steps 8 and 9) calls it after the Analyst. "Partly sufficient" is not set here:
how it reaches the run is a step 8 decision (proposal: its own stored code decision, copied by the
same fingerprint-checked path). The database checks the copy again (run CHECKs and the
`hc_run_update` trigger: a sufficient outcome needs one pooled result that passed both validity
checks and, under the fixed option, the minimums met; the evidence level must agree with the
outcome, verdict and exploratory label).
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline.writes import Refused, write

ROLE = "completion"


def copy_decision(engine: Engine, run_id: int) -> dict:
    """Completes the run with its stored decision; returns the decision copied."""

    def body(conn: Connection, stage: str):
        if stage not in ("analysis", "closed_without_freeze"):
            raise Refused("copy_decision", "stage_mismatch")
        output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' "
                                   "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
        decision = output.get("decision") if isinstance(output, dict) else None
        if not isinstance(decision, dict):
            raise Refused("copy_decision", "decision_missing")
        snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                dict(r=run_id)).scalar_one_or_none()
        if decision.get("freeze_fingerprint") != snapshot:
            raise Refused("copy_decision", "decision_not_current")
        conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
                          "exploratory = :x, evidence_level = :e WHERE id = :r"),
                     dict(o=decision["outcome"], v=decision["verdict"], x=decision["exploratory"],
                          e=decision["evidence_level"], r=run_id))
        return decision

    return write(engine, run_id, ROLE, "copy_decision", body)
```

### `hypocurate/pipeline/results.py`

```python
"""Real results only (build step 7; owner, 2026-10-05; register 'constructed_test_runs').

A run marked as a test with constructed data (`run.experiment_flags.constructed_test_data`) keeps
its results, each labelled "test run: includes constructed data", and is left out of every
aggregate, count or list of real results. Every such query goes through `REAL_RUN`, the one
named condition; the screens of step 10 must use it.
"""
from __future__ import annotations

from sqlalchemy import Connection, text

# The one named condition: a run that is not marked as a test (`r` is the run table's alias).
REAL_RUN = "NOT coalesce(r.experiment_flags->>'constructed_test_data' = 'true', false)"


def real_runs(conn: Connection) -> list:
    """Completed runs that are not marked as a test: id, outcome, verdict, exploratory, level."""
    return conn.execute(text(f"SELECT r.id, r.outcome, r.verdict, r.exploratory, r.evidence_level FROM run r "
                             f"WHERE r.status = 'completed' AND {REAL_RUN} ORDER BY r.id")).all()


def real_outcome_counts(conn: Connection) -> dict:
    """Completed real runs per outcome (an aggregate: marked runs never count)."""
    return dict(conn.execute(text(f"SELECT r.outcome, count(*) FROM run r WHERE r.status = 'completed' "
                                  f"AND {REAL_RUN} GROUP BY r.outcome")).all())


def real_analysis_results(conn: Connection) -> list:
    """Analysis results of runs that are not marked as a test."""
    return conn.execute(text(f"SELECT ar.* FROM analysis_result ar JOIN run r ON r.id = ar.run_id "
                             f"WHERE {REAL_RUN} ORDER BY ar.id")).all()
```


## 6. Migration 0004 (full text)

### `hypocurate/db/migrations/versions/0004_statistics_results.py`

```python
"""Step 7 results: the withheld state, the records a fit does not use, the test-run label, both
calibration methods, the fourth per-source label and the run's evidence level (build step 7).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05

Approved by the owner on 2026-10-05, subject to the second-model review before merging. Additive:
0001 to 0003 are untouched; the two trigger functions replaced here keep every check of 0001.

analysis_result:
- `withheld` (owner, decision 1): under the fixed option, when the pooled fit misses a minimum,
  every analysis of the run holds counts only. **The database computes it**: the insert trigger
  derives it from the plan and the pooled result (for the pooled row: fixed option and minimums
  not met; for any other row: the run's pooled row, which must exist first). A caller's value
  must agree; a missing value is filled in. Estimate, standard error and p-value are present
  exactly when their check passed **and the row is not withheld** (the three CHECKs of 0001 keep
  their names, with "AND NOT withheld" added).
- `n_records_not_used` (decision 7): records of the set the fit does not use (alloys with fewer
  than two distinct grain sizes within this analysis). The trigger now checks
  n_records + n_records_not_used = the records of the set used; the stored counts are the fit's.
- `test_run_label`: "test run: includes constructed data" exactly when the run is marked.
- The label CHECK gains `same_direction_different_decision` (decision 2/3); a label only on a
  per-source row; an estimated power only where inference is valid.

calibration_result:
- `method` ('fixed' or 'estimated'): present exactly on rows of an analysis; the one run-level
  row ("no dataset frozen") has none. The unique index becomes (run, analysis, method).
- Reasons gain `below_minimums`, `scatter_not_estimable`, `shift_not_estimable`.
- `test_run_label`, as above.
- The insert trigger: computed only where inference is valid and the result is not withheld;
  where it is, the fixed method must be computed and the estimated one is computed or names why
  the noise cannot be estimated; every other reason must match the validity checks and the
  withheld state.

run:
- `evidence_level` 1 to 6 (owner, 2026-10-05; register 'evidence_level_scale'). Written only by
  the copy path (`pipeline/completion.py`); when present it must agree with the outcome: 6 = a
  verdict and not exploratory, 5 = a verdict and exploratory, 1 to 4 = no verdict; present only
  with an outcome. **The database does not require it** on a completed run.

Marked runs are left out of every aggregate by `pipeline/results.py` (`real_runs`), in code, not by
a view (register 'constructed_test_runs').

Works with the previous release's code: that code writes no analysis or calibration result
except the run-level "no dataset frozen" row, which keeps its shape (an unmarked run needs no
label), and never completes a run.

Downgrade refuses while any row uses what 0004 adds (a withheld result, an unused record, a test
label, an estimated calibration, a new reason or label, an evidence level), then restores 0001's
functions, constraints and index exactly.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
transaction (no CONCURRENTLY, no autocommit_block); it keeps working with the previous release's
code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

TEST_RUN_LABEL = "test run: includes constructed data"
MARKED = "coalesce((SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = NEW.run_id) = 'true', false)"

# 0001's functions, verbatim (restored by the downgrade).
ANALYSIS_RESULT_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        RETURN NEW;
    END $$
    """

CALIBRATION_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF (NEW.status = 'computed') <> a.check2_passed THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid');
        END IF;
        IF NEW.reason = 'coefficient_not_fitted' AND a.check1_passed
           OR NEW.reason = 'insufficient_groups' AND NOT (a.check1_passed AND NOT a.check2_passed) THEN
            PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
        END IF;
        RETURN NEW;
    END $$
    """

ANALYSIS_RESULT_INSERT_0004 = """
    CREATE OR REPLACE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int; pooled analysis_result; computed boolean;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records + NEW.n_records_not_used <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used, less those the fit does not use');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        -- Step 7, decision 1: withheld run-wide when the pooled fit misses a minimum under the fixed option.
        IF NEW.scope = 'pooled' THEN
            computed := p.sufficiency_option = 'fixed_minimum' AND NOT NEW.minimums_met;
        ELSE
            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.run_id AND scope = 'pooled';
            IF NOT FOUND THEN
                PERFORM hc_reject('the pooled result is written before any other result of the run');
            END IF;
            computed := pooled.withheld;
        END IF;
        IF NEW.withheld IS NULL THEN
            NEW.withheld := computed;
        ELSIF NEW.withheld <> computed THEN
            PERFORM hc_reject('withheld must equal: the fixed option and the pooled minimums not met');
        END IF;
        IF (NEW.test_run_label IS NOT NULL) <> """ + MARKED + """ THEN
            PERFORM hc_reject('a result carries the test-run label exactly when its run is marked as a test');
        END IF;
        RETURN NEW;
    END $$
    """

CALIBRATION_INSERT_0004 = """
    CREATE OR REPLACE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result; expected text;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF (NEW.test_run_label IS NOT NULL) <> """ + MARKED + """ THEN
            PERFORM hc_reject('a result carries the test-run label exactly when its run is marked as a test');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF NEW.status = 'computed' AND NOT (a.check2_passed AND NOT a.withheld) THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid and the result is not withheld');
        END IF;
        IF NEW.status = 'unavailable' AND a.check2_passed AND NOT a.withheld
           AND NOT (NEW.method = 'estimated' AND NEW.reason IN ('scatter_not_estimable', 'shift_not_estimable')) THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid and the result is not withheld '
                              '(the estimated method may name why the noise cannot be estimated)');
        END IF;
        IF NEW.status = 'unavailable' AND NOT (a.check2_passed AND NOT a.withheld) THEN
            expected := CASE WHEN NOT a.check1_passed THEN 'coefficient_not_fitted'
                             WHEN NOT a.check2_passed THEN 'insufficient_groups'
                             ELSE 'below_minimums' END;
            IF NEW.reason IS NOT NULL AND NEW.reason <> expected THEN  -- a missing reason: the CHECK refuses it
                PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """

NEW_LABELS = "('agrees', 'conflicts', 'not_enough_data', 'same_direction_different_decision')"
OLD_LABELS = "('agrees', 'conflicts', 'not_enough_data')"
NEW_REASONS = ("('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups', 'below_minimums', "
               "'scatter_not_estimable', 'shift_not_estimable')")
OLD_REASONS = "('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')"

EVIDENCE_LEVEL = ("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
                  "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                  "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))")

IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM analysis_result WHERE withheld OR n_records_not_used <> 0
                   OR test_run_label IS NOT NULL OR label = 'same_direction_different_decision')
           OR EXISTS (SELECT 1 FROM calibration_result WHERE method = 'estimated' OR test_run_label IS NOT NULL
                      OR reason IN ('below_minimums', 'scatter_not_estimable', 'shift_not_estimable'))
           OR EXISTS (SELECT 1 FROM run WHERE evidence_level IS NOT NULL) THEN
            RAISE EXCEPTION USING MESSAGE = 'hypocurate: 0004 cannot be downgraded while step 7 results use it',
                                  ERRCODE = 'check_violation';
        END IF;
    END $$
    """


def upgrade() -> None:
    # analysis_result
    op.add_column('analysis_result', sa.Column('withheld', sa.Boolean(), nullable=True))
    op.execute("UPDATE analysis_result SET withheld = false")
    op.create_check_constraint(op.f('ck_analysis_result_withheld_set'), 'analysis_result', 'withheld IS NOT NULL')
    op.add_column('analysis_result', sa.Column('n_records_not_used', sa.Integer(), server_default=sa.text('0'),
                                               nullable=False))
    op.create_check_constraint(op.f('ck_analysis_result_not_used_not_negative'), 'analysis_result',
                               'n_records_not_used >= 0')
    op.add_column('analysis_result', sa.Column('test_run_label', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_analysis_result_test_run_label'), 'analysis_result',
                               f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'")
    for name, expr in (("estimate_iff_check1", "(check1_passed AND NOT withheld) = (estimate IS NOT NULL)"),
                       ("std_error_iff_check2", "(check2_passed AND NOT withheld) = (std_error IS NOT NULL)"),
                       ("p_value_iff_check2", "(check2_passed AND NOT withheld) = (p_value IS NOT NULL)"),
                       ("label", f"label IS NULL OR label IN {NEW_LABELS}")):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
        op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
    op.create_check_constraint(op.f('ck_analysis_result_label_per_source_only'), 'analysis_result',
                               "label IS NULL OR scope = 'per_source'")
    op.create_check_constraint(op.f('ck_analysis_result_power_needs_check2'), 'analysis_result',
                               'estimated_power IS NULL OR check2_passed')
    op.execute(ANALYSIS_RESULT_INSERT_0004)
    # calibration_result
    op.add_column('calibration_result', sa.Column('method', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_calibration_result_method'), 'calibration_result',
                               "method IS NULL OR method IN ('fixed', 'estimated')")
    op.create_check_constraint(op.f('ck_calibration_result_method_iff_analysis'), 'calibration_result',
                               '(method IS NULL) = (analysis_result_id IS NULL)')
    op.add_column('calibration_result', sa.Column('test_run_label', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_calibration_result_test_run_label'), 'calibration_result',
                               f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'")
    op.drop_constraint(op.f('ck_calibration_result_reason'), 'calibration_result', type_='check')
    op.create_check_constraint(op.f('ck_calibration_result_reason'), 'calibration_result',
                               f"reason IS NULL OR reason IN {NEW_REASONS}")
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id', 'method'],
                    unique=True, postgresql_nulls_not_distinct=True)
    op.execute(CALIBRATION_INSERT_0004)
    # run
    op.add_column('run', sa.Column('evidence_level', sa.SmallInteger(), nullable=True))
    op.create_check_constraint(op.f('ck_run_evidence_level'), 'run', EVIDENCE_LEVEL)


def downgrade() -> None:
    op.execute(IN_USE)
    op.drop_constraint(op.f('ck_run_evidence_level'), 'run', type_='check')
    op.drop_column('run', 'evidence_level')
    op.execute(CALIBRATION_INSERT_0001)
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id'],
                    unique=True, postgresql_nulls_not_distinct=True)
    op.drop_constraint(op.f('ck_calibration_result_reason'), 'calibration_result', type_='check')
    op.create_check_constraint(op.f('ck_calibration_result_reason'), 'calibration_result',
                               f"reason IS NULL OR reason IN {OLD_REASONS}")
    for name in ('test_run_label', 'method_iff_analysis', 'method'):
        op.drop_constraint(op.f(f'ck_calibration_result_{name}'), 'calibration_result', type_='check')
    op.drop_column('calibration_result', 'test_run_label')
    op.drop_column('calibration_result', 'method')
    op.execute(ANALYSIS_RESULT_INSERT_0001)
    for name in ('power_needs_check2', 'label_per_source_only'):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
    for name, expr in (("estimate_iff_check1", "check1_passed = (estimate IS NOT NULL)"),
                       ("std_error_iff_check2", "check2_passed = (std_error IS NOT NULL)"),
                       ("p_value_iff_check2", "check2_passed = (p_value IS NOT NULL)"),
                       ("label", f"label IS NULL OR label IN {OLD_LABELS}")):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
        op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
    for name in ('test_run_label', 'not_used_not_negative', 'withheld_set'):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
    op.drop_column('analysis_result', 'test_run_label')
    op.drop_column('analysis_result', 'n_records_not_used')
    op.drop_column('analysis_result', 'withheld')
```


## 7. Other code changes (diffs against `main`)

### `hypocurate/access/allowlist.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index d812f41..5ae91e5 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -36,7 +36,7 @@ from __future__ import annotations
 from types import MappingProxyType
 from typing import Mapping
 
-from hypocurate.access.vocabulary import (CATEGORY_FIELDS, ELIGIBILITY_RULES, FLAG_CATEGORIES, FLAG_KINDS,
+from hypocurate.access.vocabulary import (CALIBRATION_METHODS, CATEGORY_FIELDS, ELIGIBILITY_RULES, ESTIMATION_METHODS, FLAG_CATEGORIES, FLAG_KINDS,
                                           GROUPING_UNITS, PHASE_CLASSES, PROCESSING_METHODS, PROFILE_NAMES,
                                           SENSITIVITY_KEYS, SINGLE_PHASE, SOURCE_KEYS, TEMPERATURE_BANDS, TEST_TYPES,
                                           VALUE_STATUSES)
@@ -44,8 +44,9 @@ from hypocurate.access.vocabulary import (CATEGORY_FIELDS, ELIGIBILITY_RULES, FL
 ROLES = ("planner", "curator", "critic", "analyst", "commentator")
 # The code roles of PRD 4 (step 6, owner 2026-10-05): Inclusion and Checks are code, not
 # agents. They read through access objects too, bound by `dispatch.bind_code`, so their reads
-# are logged. No agent setting can bind as one of them.
-CODE_ROLES = ("inclusion", "checks")
+# are logged. No agent setting can bind as one of them. Step 7 (owner, 2026-10-05; a safeguard
+# change, reviewed by a second model): Statistics and the gap facts.
+CODE_ROLES = ("inclusion", "checks", "statistics", "gap_facts")
 ALL_ROLES = ROLES + CODE_ROLES
 
 # none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
@@ -102,6 +103,12 @@ FIELDS = MappingProxyType({
                          "field's status, grain size and test temperature, and the category values from their "
                          "vocabularies. No outcome value, no value as reported, no free text.",
     "outcome": "The run's status, outcome, verdict and exploratory label.",
+    "frozen_analysis_data": "For Statistics (code; step 7), once the dataset is frozen: the freeze's "
+                            "fingerprint; the frozen sets (keys from the vocabulary, record ids); and per "
+                            "record in any frozen set, and only those: id, source, stable identity "
+                            "(source-version fingerprint, origin key, item index), composition, the paper "
+                            "(from the DOI) and the batch as hashes, grain size, and the plan's outcome value. "
+                            "No record outside the frozen sets, no value as reported, no free text.",
 })
 
 _ANALYSIS = frozenset({"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full",
@@ -141,6 +148,13 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
 CODE_ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
     "inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind", "set_flags"})}),
     "checks": MappingProxyType({"curation": frozenset({"plan", "records_full"})}),
+    # Step 7 (owner, 2026-10-05): Statistics reads only the frozen set, after the freeze, and
+    # never decides inclusion. The gap facts read no outcome value: counts, decisions, coverage.
+    "statistics": MappingProxyType({"analysis": frozenset({"plan", "frozen_analysis_data"})}),
+    "gap_facts": MappingProxyType({
+        "analysis": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
+        "closed_without_freeze": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
+    }),
 })
 
 
@@ -219,6 +233,9 @@ PLAN_SCHEMA = MappingProxyType({
               "room_temperature_min": "number", "room_temperature_max": "number", "single_phase": SINGLE_PHASE,
               "accepted_value_statuses": ("list", VALUE_STATUSES),
               "grouping": ("list", {"source": SOURCE_KEYS, "unit": GROUPING_UNITS})},
+    # Step 7 (owner, 2026-10-05): the calibration is fixed at the rules lock, both methods.
+    "calibration": {"methods": ("list", CALIBRATION_METHODS), "n_simulations": "integer", "scatter": "number",
+                    "shift": "number", "estimation": ESTIMATION_METHODS, "smallest_effect": "number"},
 })
 POWER_SCHEMA = MappingProxyType({"method": POWER_METHODS, "within_paper_similarity": "number",
                                  "smallest_effect": "number", "scatter": "number"})
```

### `hypocurate/access/fields.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index b148d6d..2866d6f 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -500,6 +500,47 @@ def outcome(conn: Connection, ctx: Context) -> dict:
     return {"status": row.status, "outcome": row.outcome, "verdict": row.verdict, "exploratory": row.exploratory}
 
 
+def frozen_analysis_data(conn: Connection, ctx: Context) -> dict:
+    """For Statistics (code; step 7): the frozen sets and, for their records only, what the model
+    needs. The outcome value is the locked plan's outcome field (sprint 1: yield strength), through
+    `_number` (a value status and a finite number, else None). Refused without a freeze."""
+    snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
+                            dict(r=ctx.run_id)).scalar_one_or_none()
+    if snapshot is None:
+        raise Refused("not_frozen")
+    content = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=ctx.run_id)).scalar_one()
+    outcome_field = (project(content, PLAN_SCHEMA) or {}).get("variables", {}).get("outcome", {}).get("field")
+    sets: dict[str, list[int]] = {}
+    for key, record_id in _rows(conn, "SELECT a.key, asr.record_id FROM analysis_set a "
+                                      "LEFT JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
+                                      "WHERE a.run_id = :r ORDER BY a.key, asr.record_id", r=ctx.run_id):
+        key = vocab.code(key, vocab.ANALYSIS_SET_KEYS)
+        sets.setdefault(key, [])
+        if record_id is not None:
+            sets[key].append(record_id)
+    members = {i for ids in sets.values() for i in ids}
+    records = []
+    for r in _stored_records(conn, ctx):
+        if r.id not in members:
+            continue
+        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
+        reported = r.reported if isinstance(r.reported, Mapping) else {}
+        batch_column = BATCH_COLUMNS.get(r.source)
+        batch = reported.get(batch_column, {}).get("text") if batch_column else None
+        doi = r.paper_doi if isinstance(r.paper_doi, str) and r.paper_doi.strip() else None
+        records.append({
+            "id": r.id, "source": r.source,
+            "version_fingerprint": r.version_fingerprint, "origin": r.source_item_key, "item_index": r.item_index,
+            "composition": _composition(h.get("composition")),
+            "paper": identity_hash(doi_group_key(doi)) if doi else None,
+            "batch": identity_hash(batch) if isinstance(batch, str) and batch.strip() else None,
+            "grain_size": _number(h.get("grain_size")),
+            "outcome": _number(h.get(outcome_field)) if outcome_field in OUTCOME_FIELDS else None,
+        })
+    return {"freeze_fingerprint": snapshot, "outcome_field": outcome_field if outcome_field in OUTCOME_FIELDS
+            else None, "sets": sets, "records": records}
+
+
 READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
     "record_counts": record_counts, "plan_fields_to_extract": plan_fields_to_extract,
@@ -508,4 +549,5 @@ READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
     "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
     "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions, "set_flags": set_flags,
+    "frozen_analysis_data": frozen_analysis_data,
 }
```

### `hypocurate/access/layer.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index 6774f63..f255781 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -70,8 +70,8 @@ LOG = logging.getLogger("hypocurate.access")
 
 # Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
 DENIALS = {
-    "unknown_role": "the role is not one of the five agent roles or the two code roles",
-    "not_a_code_role": "only the code roles Inclusion and Checks are bound without an agent setting",
+    "unknown_role": "the role is not one of the five agent roles or the code roles",
+    "not_a_code_role": "only the code roles (Inclusion, Checks, Statistics, gap facts) are bound without an agent setting",
     "unknown_stage": "the stage is not one of the access stages",
     "stage_mismatch": "the run is no longer at the stage this access was bound to",
     "not_on_list": "the field is not on the role's list at the run's stage",
@@ -82,6 +82,7 @@ DENIALS = {
     "empty_list": "the role has no field at this stage",
     "checks_not_done": "no completed Checks result for this run",
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
+    "not_frozen": "no dataset is frozen for this run",
 }
 FAILURES = ("unknown_run", "lock_timeout", "reader_error", "database_error", "file_guard")
 FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
```

### `hypocurate/access/vocabulary.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index ffeb18e..640e3f4 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -81,6 +81,10 @@ GROUPING_UNITS = frozenset({"paper", "dataset", "batch"})
 VALUE_STATUSES = frozenset({"converted", "assigned_from_source", "assigned_by_decision"})
 PROFILE_NAMES = frozenset({"grain_size_strengthening"})
 SINGLE_PHASE = frozenset({"required", "not_required"})
+# Step 7 (owner, 2026-10-05): the calibration methods and the estimation method of the
+# 'estimated' calibration (register 'calibration_both_ways', 'calibration_noise_levels').
+CALIBRATION_METHODS = frozenset({"fixed", "estimated"})
+ESTIMATION_METHODS = frozenset({"henderson_iii"})
 
 
 def code(value: Any, vocabulary: frozenset[str]) -> str:
```

### `hypocurate/pipeline/plan.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index f301d87..ebaa8b1 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -8,7 +8,9 @@ and content that the sprint-1 template does not support.
 
 Every plan setting that affects which records are eligible or how they are grouped is in the
 plan (`rules`, `scope`, `exclusion_rules`, `eligibility_rules`, `sufficiency`), and the
-plan records the domain profile its defaults came from (`profile`). The default and the
+plan records the domain profile its defaults came from (`profile`). Step 7 adds the calibration,
+fixed at the lock (`calibration`: both methods, the number of simulations, the fixed scatter and
+shift, the estimation method and the smallest effect). The default and the
 reference plans are built from the domain profile (`hypocurate.pipeline.profile`), its one
 named place for each default. Plans are fixed inputs in step 6; the Planner (step 8) fills the
 same template.
@@ -32,7 +34,7 @@ from hypocurate.pipeline import profile as p
 from hypocurate.pipeline.eligibility import SUPPORTED_OUTCOMES, fixed_rule_problems
 
 PARTS = ("hypothesis_version", "variables", "scope", "model", "sufficiency", "fields_to_extract", "exclusion_rules",
-         "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules")
+         "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules", "calibration")
 RULES = ("same_alloy_decimals", "duplicate_tolerance", "survivor_source_order", "min_grain_sizes",
          "room_temperature_min", "room_temperature_max", "single_phase", "accepted_value_statuses", "grouping")
 # What each eligibility-rule code does when the plan names it for a flag (PRD 5.3).
@@ -77,6 +79,9 @@ def default_plan(hypothesis_version_id: int) -> dict:
                   "single_phase": p.SINGLE_PHASE,
                   "accepted_value_statuses": list(p.ACCEPTED_VALUE_STATUSES),
                   "grouping": [{"source": s, "unit": u} for s, u in p.GROUPING.items()]},
+        "calibration": {"methods": list(p.CALIBRATION_METHODS), "n_simulations": p.CALIBRATION_SIMULATIONS,
+                        "scatter": float(p.CALIBRATION_SCATTER_MPA), "shift": float(p.CALIBRATION_SHIFT_MPA),
+                        "estimation": p.CALIBRATION_ESTIMATION, "smallest_effect": float(p.SMALLEST_EFFECT)},
     }
 
 
@@ -165,6 +170,16 @@ def _check_template(c: dict) -> None:
     problems = fixed_rule_problems(c["eligibility_rules"])
     if problems:
         raise PlanError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
+    cal = c["calibration"]
+    # Step 7 (owner, 2026-10-05): calibration is reported both ways, each method fixed here.
+    if set(cal) != {"methods", "n_simulations", "scatter", "shift", "estimation", "smallest_effect"} or \
+            cal["methods"] != ["fixed", "estimated"] or not 1 <= cal["n_simulations"] <= 100_000 or \
+            not (math.isfinite(cal["scatter"]) and cal["scatter"] > 0) or \
+            not (math.isfinite(cal["shift"]) and cal["shift"] >= 0) or \
+            not (math.isfinite(cal["smallest_effect"]) and cal["smallest_effect"] > 0):
+        raise PlanError("the calibration names both methods (fixed, estimated), a number of simulations, a "
+                        "positive scatter, a shift of zero or more, its estimation method and a positive "
+                        "smallest effect")
     keys = c["sensitivity_analyses"]
     if len(set(keys)) != len(keys) or not set(keys) <= SENSITIVITY_KEYS - {"removal_after_lock"}:
         raise PlanError("sensitivity analyses are named once each, from the vocabulary")
```

### `hypocurate/pipeline/profile.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/pipeline/profile.py b/hypocurate/pipeline/profile.py
index d738330..f21387d 100644
--- a/hypocurate/pipeline/profile.py
+++ b/hypocurate/pipeline/profile.py
@@ -19,7 +19,7 @@ from typing import Mapping
 from hypocurate.sources.normalize import SAME_ALLOY_DECIMALS
 
 PROFILE_NAME = "grain_size_strengthening"
-PROFILE_VERSION = 1
+PROFILE_VERSION = 2  # 2: the calibration defaults (step 7)
 
 # --- Variables and the supported model (PRD 5.7) ---------------------------------------
 OUTCOME = ("yield_strength", "MPa")
@@ -61,6 +61,20 @@ GROUPING = MappingProxyType({"mpea": "paper", "tamu_fcc": "dataset", "controlled
 SUFFICIENCY_OPTION = "fixed_minimum"
 FIXED_MINIMUMS = MappingProxyType({"min_records": 30, "min_alloys": 5, "min_groups": 10, "min_resid_df": 10})
 
+# --- Calibration on generated data (PRD 5.10; owner, 2026-10-05; step 7) ----------------
+# Reported both ways, each method fixed at the rules lock (register 'calibration_both_ways'):
+# 'fixed' uses the scatter and per-paper shift below (PRD 5.10's illustrative values, register
+# 'calibration_simulation'); 'estimated' estimates them by code from the frozen residuals with
+# Henderson's method III (register 'calibration_noise_levels'). A flag, never a gate.
+CALIBRATION_METHODS = ("fixed", "estimated")
+CALIBRATION_SIMULATIONS = 2000  # per simulated world
+CALIBRATION_SCATTER_MPA = 60.0  # per record, fixed method
+CALIBRATION_SHIFT_MPA = 40.0  # per group (paper), fixed method
+CALIBRATION_ESTIMATION = "henderson_iii"
+# The smallest effect that matters (register 'smallest_effect'): a query setting, in MPa·µm^0.5.
+# The effect world of the calibration and the estimated power use it.
+SMALLEST_EFFECT = 150.0
+
 # --- Sensitivity analyses (owner, 2026-10-05; register 'sensitivity_one_change') ---------
 # Each differs from the primary set in exactly one named respect; descriptive only, never
 # changes the verdict, no adjustment for there being eight.
```

### `hypocurate/pipeline/writes.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index a00bfd4..0a5a044 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -38,13 +38,14 @@ from sqlalchemy.exc import DBAPIError, IntegrityError
 
 from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
 from hypocurate.access.stage import actual_stage
+from hypocurate.db.models import TEST_RUN_LABEL  # noqa: F401 (re-exported for the write paths)
 from hypocurate.db.retry import run_transaction
 from hypocurate.pipeline.binding import binding, record_identity  # noqa: F401 (shared with the access layer)
 
 LOG = logging.getLogger("hypocurate.pipeline")
 LOCK_TIMEOUT_MS = ACCESS_LOCK_TIMEOUT_MS
 # The roles under which the pipeline's own writes are logged.
-WRITE_ROLES = ("extraction", "checks", "inclusion", "checkpoint")
+WRITE_ROLES = ("extraction", "checks", "inclusion", "checkpoint", "statistics", "completion")
 CODES = {
     "stage_mismatch": "the run is not at the stage this step needs",
     "changed_since_read": "the run's records, flags or decisions changed after they were read",
@@ -59,8 +60,20 @@ CODES = {
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
     "set_flags_missing": "the completed Checks result lacks the flags a sensitivity set needs",
     "invariant_broken": "the primary set breaks a rule no plan can change (register 'primary_set_invariants')",
+    # Step 7.
+    "records_without_group": "a record in a frozen set has no group, so the grouped uncertainty cannot be computed",
+    "decision_missing": "no stored decision for this run",
+    "decision_not_current": "the stored decision belongs to a different freeze than the run's",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
+# Step 7 (owner, 2026-10-05; register 'constructed_test_runs'): TEST_RUN_LABEL, on every stored
+# result of a marked run, comes from one named place, the database model, whose CHECKs use it.
+
+
+def marked(conn: Connection, run_id: int) -> bool:
+    """Is the run marked as a test with constructed data?"""
+    flags = conn.execute(text("SELECT experiment_flags FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
+    return isinstance(flags, dict) and flags.get(CONSTRUCTED_MARK) is True
 
 
 class Refused(Exception):
```

### `hypocurate/pipeline/checkpoints.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index 98c0f57..df4c260 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -33,7 +33,8 @@ from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
 from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
-from hypocurate.pipeline.writes import (CONSTRUCTED_MARK, Refused, code_stage, constructed_unmarked, decide_sets,
+from hypocurate.pipeline.writes import (CONSTRUCTED_MARK, TEST_RUN_LABEL, Refused, code_stage, constructed_unmarked,
+                                        decide_sets, marked,
                                         flag_index,
                                         inclusion_input, log_refusal,
                                         record_identity, record_ids, require_checks_cover, run_record_sources,
@@ -155,8 +156,10 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
             conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
                          dict(r=run_id, fp=fp, n=len(members[el.PRIMARY])))
         else:
-            conn.execute(text("INSERT INTO calibration_result (run_id, status, reason) "
-                              "VALUES (:r, 'unavailable', 'no_dataset_frozen')"), dict(r=run_id))
+            # Step 7 (migration 0004): the row of a marked run carries the test-run label.
+            conn.execute(text("INSERT INTO calibration_result (run_id, status, reason, test_run_label) "
+                              "VALUES (:r, 'unavailable', 'no_dataset_frozen', :l)"),
+                         dict(r=run_id, l=TEST_RUN_LABEL if marked(conn, run_id) else None))
         return record
 
     return write(engine, run_id, "checkpoint", "freeze_dataset", body)
```

### `hypocurate/db/models.py` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 67cd3d3..db297fa 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -27,7 +27,10 @@ retry the whole transaction.
 
 What the CHECKs on `analysis_result` establish (review finding 5): necessary
 conditions on the stored counts only. The full validity rules of PRD 5.7 and the
-agreement of the verdict with the pooled result are computed and tested in step 7.
+agreement of the verdict with the pooled result are computed and tested in step 7
+(`pipeline/statistics.py`). Migration 0004 (step 7) adds the withheld state, computed by the
+insert trigger, the records a fit does not use, the test-run label, both calibration methods,
+the fourth per-source label and the run's evidence level.
 """
 from __future__ import annotations
 
@@ -50,6 +53,7 @@ from sqlalchemy import (
     LargeBinary,
     MetaData,
     Sequence,
+    SmallInteger,
     Numeric,
     Text,
     UniqueConstraint,
@@ -319,6 +323,8 @@ class Run(Base):
     outcome: Mapped[str | None] = mapped_column(Text)
     verdict: Mapped[str | None] = mapped_column(Text)
     exploratory: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
+    # Step 7 (migration 0004; register 'evidence_level_scale'): 1 to 6, written only by the copy path.
+    evidence_level: Mapped[int | None] = mapped_column(SmallInteger)
     failure_reason: Mapped[str | None] = mapped_column(Text)
     agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
     fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
@@ -337,6 +343,9 @@ class Run(Base):
             "(verdict IS NOT NULL) = (status = 'completed' AND outcome IS NOT DISTINCT FROM 'sufficient')",
             name="verdict_iff_sufficient"),
         CheckConstraint("NOT exploratory OR verdict IS NOT NULL", name="exploratory_needs_verdict"),
+        CheckConstraint("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
+                        "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
+                        "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))", name="evidence_level"),
         CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
         CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
         CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
@@ -624,7 +633,8 @@ class FlagRecord(Base):
 # --- Results -------------------------------------------------------------------
 
 SCOPES = ("pooled", "per_source", "sensitivity")
-LABELS = ("agrees", "conflicts", "not_enough_data")
+LABELS = ("agrees", "conflicts", "not_enough_data", "same_direction_different_decision")  # 4th: step 7
+TEST_RUN_LABEL = "test run: includes constructed data"
 
 
 class AnalysisResult(Base):
@@ -653,6 +663,11 @@ class AnalysisResult(Base):
     estimated_power: Mapped[float | None] = mapped_column(Double)
     label: Mapped[str | None] = mapped_column(Text)
     created_at: Mapped[datetime] = created()
+    # Step 7 (migration 0004): withheld below the fixed minimums (computed by the insert trigger);
+    # records of the set the fit does not use; the test-run label.
+    withheld: Mapped[bool | None] = mapped_column(Boolean)
+    n_records_not_used: Mapped[int] = mapped_column(Integer, server_default=sql("0"))
+    test_run_label: Mapped[str | None] = mapped_column(Text)
     __table_args__ = (
         ForeignKeyConstraint(["analysis_set_id", "run_id"], ["analysis_set.id", "analysis_set.run_id"],
                              name="fk_analysis_result_analysis_set"),
@@ -671,16 +686,23 @@ class AnalysisResult(Base):
         CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_consistent"),
         CheckConstraint("check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)",
                         name="check2_consistent"),
-        CheckConstraint("check1_passed = (estimate IS NOT NULL)", name="estimate_iff_check1"),
-        CheckConstraint("check2_passed = (std_error IS NOT NULL)", name="std_error_iff_check2"),
-        CheckConstraint("check2_passed = (p_value IS NOT NULL)", name="p_value_iff_check2"),
+        CheckConstraint("(check1_passed AND NOT withheld) = (estimate IS NOT NULL)", name="estimate_iff_check1"),
+        CheckConstraint("(check2_passed AND NOT withheld) = (std_error IS NOT NULL)", name="std_error_iff_check2"),
+        CheckConstraint("(check2_passed AND NOT withheld) = (p_value IS NOT NULL)", name="p_value_iff_check2"),
+        CheckConstraint("withheld IS NOT NULL", name="withheld_set"),
+        CheckConstraint("n_records_not_used >= 0", name="not_used_not_negative"),
+        CheckConstraint(f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'", name="test_run_label"),
+        CheckConstraint("label IS NULL OR scope = 'per_source'", name="label_per_source_only"),
+        CheckConstraint("estimated_power IS NULL OR check2_passed", name="power_needs_check2"),
         CheckConstraint("std_error IS NULL OR std_error >= 0", name="std_error_not_negative"),
         CheckConstraint("p_value IS NULL OR p_value BETWEEN 0 AND 1", name="p_value_range"),
         CheckConstraint("estimated_power IS NULL OR estimated_power BETWEEN 0 AND 1", name="power_range"),
     )
 
 
-CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups")
+CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups",
+                       "below_minimums", "scatter_not_estimable", "shift_not_estimable")  # last three: step 7
+CALIBRATION_METHODS = ("fixed", "estimated")
 CALIBRATION_NUMBERS = ("assumptions", "n_simulations", "seed", "null_share", "null_ci_low", "null_ci_high",
                        "effect_share", "effect_ci_low", "effect_ci_high", "confidence_flag")
 
@@ -704,11 +726,17 @@ class CalibrationResult(Base):
     effect_ci_high: Mapped[float | None] = mapped_column(Double)
     confidence_flag: Mapped[str | None] = mapped_column(Text)
     created_at: Mapped[datetime] = created()
+    # Step 7 (migration 0004): both methods per analysis; the test-run label.
+    method: Mapped[str | None] = mapped_column(Text)
+    test_run_label: Mapped[str | None] = mapped_column(Text)
     __table_args__ = (
         ForeignKeyConstraint(["analysis_result_id", "run_id"], ["analysis_result.id", "analysis_result.run_id"],
                              name="fk_calibration_result_analysis_result"),
-        Index("uq_calibration_result_scope", "run_id", "analysis_result_id",
+        Index("uq_calibration_result_scope", "run_id", "analysis_result_id", "method",
               unique=True, postgresql_nulls_not_distinct=True),
+        CheckConstraint("method IS NULL OR " + one_of("method", CALIBRATION_METHODS), name="method"),
+        CheckConstraint("(method IS NULL) = (analysis_result_id IS NULL)", name="method_iff_analysis"),
+        CheckConstraint(f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'", name="test_run_label"),
         CheckConstraint(one_of("status", ("computed", "unavailable")), name="status"),
         CheckConstraint(f"reason IS NULL OR {one_of('reason', CALIBRATION_REASONS)}", name="reason"),
         CheckConstraint("confidence_flag IS NULL OR "
```

### `scripts/check_runtime_image.py` (diff against `main`, `3aee798`)

```diff
diff --git a/scripts/check_runtime_image.py b/scripts/check_runtime_image.py
index 654730d..29e929f 100644
--- a/scripts/check_runtime_image.py
+++ b/scripts/check_runtime_image.py
@@ -39,7 +39,11 @@ REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.jso
             "hypocurate/db/migrations/versions/0003_record_extraction.py",
             "hypocurate/pipeline/profile.py", "hypocurate/pipeline/plan.py", "hypocurate/pipeline/checkpoints.py",
             "hypocurate/pipeline/extract.py", "hypocurate/pipeline/flags.py", "hypocurate/pipeline/checks.py",
-            "hypocurate/pipeline/eligibility.py", "hypocurate/pipeline/inclusion.py", "hypocurate/pipeline/writes.py"]
+            "hypocurate/pipeline/eligibility.py", "hypocurate/pipeline/inclusion.py", "hypocurate/pipeline/writes.py",
+            # Step 7: the statistics, the calibration, the analysis stage, the copy path, migration 0004.
+            "hypocurate/pipeline/statistics.py", "hypocurate/pipeline/calibration.py",
+            "hypocurate/pipeline/analysis.py", "hypocurate/pipeline/completion.py", "hypocurate/pipeline/results.py",
+            "hypocurate/db/migrations/versions/0004_statistics_results.py"]
 FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
 FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")
```

### `pyproject.toml` (diff against `main`, `3aee798`)

```diff
diff --git a/pyproject.toml b/pyproject.toml
index f2e0cfc..558ef77 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -20,10 +20,14 @@ dependencies = [
     "sqlalchemy>=2.0",
     "psycopg[binary]>=3.2",
     "alembic>=1.16",
+    # Step 7: the statistics module (numpy linear algebra, scipy t and binomial distributions).
+    "numpy>=2.0",
+    "scipy>=1.14",
 ]
 
 [project.optional-dependencies]
-dev = ["pytest>=8", "httpx2>=2.13", "pyyaml>=6"]
+# statsmodels: the independent reference implementation of the statistics, test side only (step 7).
+dev = ["pytest>=8", "httpx2>=2.13", "pyyaml>=6", "statsmodels>=0.14"]
 
 [project.scripts]
 hypocurate = "hypocurate.cli:main"
```

### `requirements.lock` (diff against `main`, `3aee798`)

```diff
diff --git a/requirements.lock b/requirements.lock
index e421a42..edfacfc 100644
--- a/requirements.lock
+++ b/requirements.lock
@@ -274,7 +274,10 @@ numpy==2.5.3 \
-    # via pandas
+    # via
+    #   hypocurate (pyproject.toml)
+    #   pandas
+    #   scipy
 openpyxl==3.1.5 \
@@ -549,6 +552,69 @@ python-multipart==0.0.32 \
     # via hypocurate (pyproject.toml)
+scipy==1.18.1 \
+    # via hypocurate (pyproject.toml)
 six==1.17.0 \
```

### `requirements-dev.lock` (diff against `main`, `3aee798`)

```diff
diff --git a/requirements-dev.lock b/requirements-dev.lock
index 77e642e..d4dae17 100644
--- a/requirements-dev.lock
+++ b/requirements-dev.lock
@@ -34,6 +34,10 @@ fastapi==0.142.2 \
     # via hypocurate (pyproject.toml)
+formulaic==1.2.2 \
+    # via statsmodels
 h11==0.16.0 \
@@ -58,6 +62,10 @@ iniconfig==2.3.0 \
     # via pytest
+interface-meta==2.0.1 \
+    # via formulaic
 itsdangerous==2.2.0 \
@@ -225,6 +233,10 @@ markupsafe==3.0.4 \
     # via
     #   jinja2
     #   mako
+narwhals==2.26.0 \
+    # via formulaic
 numpy==2.5.3 \
@@ -292,7 +304,13 @@ numpy==2.5.3 \
-    # via pandas
+    # via
+    #   formulaic
+    #   hypocurate (pyproject.toml)
+    #   pandas
+    #   patsy
+    #   scipy
+    #   statsmodels
 openpyxl==3.1.5 \
@@ -304,7 +322,10 @@ opentelemetry-api==1.45.0 \
 packaging==26.3 \
-    # via pytest
+    # via
+    #   patsy
+    #   pytest
+    #   statsmodels
 pandas==3.0.6 \
@@ -364,7 +385,14 @@ pandas==3.0.6 \
-    # via hypocurate (pyproject.toml)
+    # via
+    #   formulaic
+    #   hypocurate (pyproject.toml)
+    #   statsmodels
+patsy==1.0.3 \
+    # via statsmodels
 pluggy==1.6.0 \
@@ -658,6 +686,72 @@ pyyaml==6.0.3 \
     # via hypocurate (pyproject.toml)
+scipy==1.18.1 \
+    # via
+    #   formulaic
+    #   hypocurate (pyproject.toml)
+    #   statsmodels
 six==1.17.0 \
@@ -742,6 +836,63 @@ starlette==1.7.0 \
     # via fastapi
+statsmodels==0.15.0 \
+    # via hypocurate (pyproject.toml)
 truststore==0.10.4 \
@@ -755,6 +906,7 @@ typing-extensions==4.16.0 \
     #   alembic
     #   anyio
     #   fastapi
+    #   formulaic
     #   opentelemetry-api
     #   pydantic
     #   pydantic-core
@@ -770,3 +922,106 @@ uvicorn==0.54.0 \
     # via hypocurate (pyproject.toml)
+wrapt==2.5.0 \
+    # via formulaic
```


## 8. The assumptions register (diff)

### `hypocurate/assumptions.json` (diff against `main`, `3aee798`)

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 0021e09..210528c 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -137,7 +137,7 @@
     },
     "sensitivity": "Six batches as six groups.",
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit",
@@ -148,9 +148,6 @@
           "equals": "dataset"
         }
       ],
-      "done": "The adapter gives every record one group (the dataset) and refuses any other grouping unit; the plan states the grouping per source, and the sensitivity set 'six_batches_as_groups' groups the Texas A&M records by batch (step 6).",
-      "pending": "Using the groups in inference (step 7).",
-      "step": 7,
       "note": null
     },
     "history": [
@@ -169,6 +166,8 @@
       "tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides",
       "tests/test_checkpoints.py::test_the_lock_refuses_settings_that_leave_out_a_chosen_source",
       "tests/test_eligibility.py::test_grouping_is_read_from_the_locked_plan",
+      "tests/test_reference_numbers.py::test_each_sensitivity_set",
+      "tests/test_reference_numbers.py::test_texas_am_alone_1_per_source_in_the_pooled_run",
       "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
   },
@@ -259,7 +258,7 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.pipeline.profile:FIXED_MINIMUMS",
@@ -272,11 +271,11 @@
         },
         {
           "ref": "sql:hc_run_update"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:minimums"
         }
       ],
-      "done": "The four minimums are each plan's default (step 6); the database checks that 'minimums met' agrees with them; the freeze records the counts and whether they are met, as information.",
-      "pending": "The fixed-minimum check that decides the outcome, computed by code (step 7).",
-      "step": 7,
       "note": null
     },
     "history": [
@@ -287,13 +286,17 @@
         "note": "PRD 5.8."
       }
     ],
-    "notes": [],
+    "notes": [
+      "Step 7 (owner, 2026-10-05): the minimums are counted on the records a fit actually uses, not on the whole frozen set."
+    ],
     "tests": [
+      "tests/test_analysis_stage.py::test_below_the_minimums_every_analysis_holds_counts_and_records_only",
       "tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met",
       "tests/test_data_model.py::test_minimums_met_must_agree_with_the_plan",
       "tests/test_eligibility.py::test_counts_known_at_the_freeze",
       "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions",
-      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze",
+      "tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes"
     ]
   },
   {
@@ -441,10 +444,10 @@
     "key": "calibration_noise_levels",
     "name": "Calibration assumptions",
     "state": "direction_approved",
-    "statement": "The scatter per record and the shift per paper used in the calibration simulation are estimated by code from the frozen dataset's residuals after the dataset freeze. The estimation method is fixed at the rules lock and applied by code; no person or agent chooses the values. The smallest effect that matters is a query setting.",
+    "statement": "For the 'estimated' calibration, the scatter per record (σe) and the shift per group (σu) are estimated by code from each analysis's frozen records with Henderson's method III, fixed at the rules lock: fit the locked model (RSS_R, rank r_R) and the same model with one intercept per group (RSS_F, rank r_F); σe² = RSS_F / (N - r_F); σu² = max(0, (RSS_R - RSS_F - (r_F - r_R) σe²) / tr(Z'M_R Z)). A negative estimate set to zero is recorded with its value before truncation. Not estimable (N <= r_F, RSS_F zero, or the trace zero): the estimated calibration of that analysis is 'unavailable' with the reason, and the fixed one is still reported. No person or agent chooses a value. A flag, never a gate.",
     "value": {
-      "text": "scatter and per-paper shift estimated from the frozen residuals; smallest effect default 150",
-      "unit": "MPa·µm^0.5"
+      "text": "Henderson's method III from the frozen records; unavailable when not estimable",
+      "unit": "MPa"
     },
     "category": "statistical",
     "affects": "The calibration shares shown with the report (a flag, never a gate).",
@@ -463,8 +466,16 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:CALIBRATION_ESTIMATION",
+          "equals": "henderson_iii"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.calibration:henderson_iii"
+        }
+      ],
       "note": null
     },
     "history": [
@@ -473,17 +484,29 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "PRD 5.10 and 17, decision 10."
+      },
+      {
+        "value": "The scatter per record and the shift per paper used in the calibration simulation are estimated by code from the frozen dataset's residuals after the dataset freeze. The estimation method is fixed at the rules lock and applied by code; no person or agent chooses the values. The smallest effect that matters is a query setting.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Direction approved before step 7; replaced by the owner's step 7 decision (both ways)."
       }
     ],
     "notes": [
       "Conflicts with PRD 5.10, which says these assumptions are fixed at the rules lock and never estimated from the real outcomes.",
       "This is a safeguard change: it needs a second-model review in step 7 before it is applied.",
-      "Alternative to compare in that review: report calibration both ways, with data-derived noise levels and with the fixed defaults."
+      "Built in step 7 and awaiting the second-model review before the merge (owner, 2026-10-05). It departs from PRD 5.10, which fixes the noise levels in advance and never estimates them from the real outcomes: the estimate uses the frozen outcomes after the freeze, and can change no decision."
+    ],
+    "tests": [
+      "tests/test_calibration.py::test_a_negative_shift_estimate_is_set_to_zero_and_the_result_says_so",
+      "tests/test_calibration.py::test_a_shift_explained_by_the_alloys_cannot_be_estimated",
+      "tests/test_calibration.py::test_method_iii_matches_an_independent_computation",
+      "tests/test_calibration.py::test_method_iii_recovers_known_noise_levels_on_a_large_generated_dataset",
+      "tests/test_calibration.py::test_the_scatter_cannot_be_estimated_without_residual_freedom_in_the_full_model"
     ],
-    "tests": [],
     "pending": {
       "by": "second-model technical review",
-      "before_step": 7
+      "before_step": 8
     }
   },
   {
@@ -625,15 +648,22 @@
     },
     "sensitivity": "Per-source estimates.",
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:fit"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [
       "The two sources' separate estimates differ: about 427 (MPEA) and about 1173 (Texas A&M)."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_reference_numbers.py::test_pooled",
+      "tests/test_statistics.py::test_the_fit_matches_the_reference_on_a_hand_made_dataset"
+    ]
   },
   {
     "key": "exponent_fixed",
@@ -661,13 +691,23 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:TRANSFORMATION",
+          "equals": "inverse_square_root"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:TRANSFORMATIONS"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_statistics.py::test_the_model_is_the_one_supported_model"
+    ]
   },
   {
     "key": "model_form",
@@ -695,13 +735,25 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:MODEL",
+          "equals": "hall_petch_alloy_intercepts"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:TRANSFORMATIONS"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation",
+      "tests/test_statistics.py::test_the_fit_matches_the_reference_on_a_hand_made_dataset",
+      "tests/test_statistics.py::test_the_model_is_the_one_supported_model"
+    ]
   },
   {
     "key": "baseline_per_alloy",
@@ -729,15 +781,22 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:demeaned"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [
       "Omitted factors that vary with grain size within an alloy can bias k; see entry 'association_not_causation'."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation",
+      "tests/test_statistics.py::test_the_fit_matches_the_reference_on_a_hand_made_dataset"
+    ]
   },
   {
     "key": "association_not_causation",
@@ -766,11 +825,18 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:VERDICT_WORDING.supported",
+          "equals": "supported under the stated model, in the sources searched"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_statistics.py::test_the_wording_is_scoped_to_the_sources_searched"
+    ],
     "history": [],
     "notes": [
       "For step 10: the run screen's verdict wording must say 'supported under the stated model' and never imply proof of cause."
@@ -844,15 +910,21 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
-      "note": "The adapters keep the reported grain-size SD where a source has one."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.access.fields:frozen_analysis_data"
+        }
+      ],
+      "note": "The adapters keep the reported grain-size SD where a source has one; Statistics does not receive it."
     },
     "history": [],
     "notes": [
       "Added in step 4b while writing the entries the owner listed."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_access_statistics.py::test_the_complete_input_of_statistics"
+    ]
   },
   {
     "key": "measurement_error_not_propagated",
@@ -881,11 +953,17 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:fit"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation"
+    ],
     "history": [],
     "notes": []
   },
@@ -1468,13 +1546,23 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:fit"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:demeaned"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation",
+      "tests/test_statistics.py::test_the_fit_matches_the_reference_on_a_hand_made_dataset"
+    ]
   },
   {
     "key": "equal_row_weights",
@@ -1503,11 +1591,17 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:fit"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation"
+    ],
     "history": [],
     "notes": []
   },
@@ -1537,15 +1631,23 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:small_sample_factor"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [
-      "The reference numbers used statsmodels' default cluster correction; step 7 states the exact formula."
+      "The reference numbers used statsmodels' default cluster correction; step 7 states the exact formula.",
+      "Step 7: the exact formula is G/(G-1) × (N-1)/(N-K), K = alloys + 1, statsmodels' default for clustered errors (statistics.small_sample_factor)."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation",
+      "tests/test_statistics.py::test_the_small_sample_correction_is_statsmodels_default"
+    ]
   },
   {
     "key": "few_groups_approximate",
@@ -1574,11 +1676,20 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:small_sample_factor"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:one_sided_p"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_statistics.py::test_the_small_sample_correction_is_statsmodels_default"
+    ],
     "history": [],
     "notes": []
   },
@@ -1608,22 +1719,23 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.versions:SOURCES.mpea.grouping_unit",
           "equals": "paper"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:group"
         }
       ],
-      "done": "Each MPEA record's group is its paper (the source's grouping unit is 'paper').",
-      "pending": "Independence is assumed, not established; the groups are first used in inference in step 7.",
-      "step": 7,
-      "note": null
+      "note": "Independence is assumed, not established."
     },
     "history": [],
     "notes": [],
     "tests": [
-      "tests/test_adapter_mpea.py::test_paper_identity_is_the_doi"
+      "tests/test_adapter_mpea.py::test_paper_identity_is_the_doi",
+      "tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation"
     ]
   },
   {
@@ -1652,13 +1764,24 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:one_sided_p"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:ALPHA",
+          "equals": 0.05
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_statistics.py::test_a_zero_standard_error_gives_a_defined_p_value",
+      "tests/test_statistics.py::test_the_test_is_one_sided"
+    ]
   },
   {
     "key": "p_threshold_comparison",
@@ -1686,13 +1809,19 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:significant"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_statistics.py::test_supported_exactly_when_p_is_strictly_below_alpha"
+    ]
   },
   {
     "key": "no_multiplicity_adjustment",
@@ -1721,11 +1850,17 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:significant"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_reference_numbers.py::test_each_sensitivity_set"
+    ],
     "history": [],
     "notes": []
   },
@@ -1755,26 +1890,30 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "sql:ck_analysis_result_check1_consistent"
         },
         {
           "ref": "sql:ck_analysis_result_check2_consistent"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:MODEL_MIN_GRAIN_SIZES",
+          "equals": 2
         }
       ],
-      "done": "The database checks necessary conditions on stored counts (check 1 needs an alloy; check 2 needs a residual degree of freedom and two groups).",
-      "pending": "The full rules computed by code from the frozen dataset (two distinct grain sizes; exact alloy and group counts).",
-      "step": 7,
       "note": null
     },
     "history": [],
     "notes": [],
     "tests": [
-      "tests/test_data_model.py::test_the_validity_checks_cannot_be_waived",
+      "tests/test_analysis_stage.py::test_use_what_is_available_with_one_group_gives_the_coefficient_only",
       "tests/test_data_model.py::test_check_one_failing_means_no_estimate",
-      "tests/test_data_model.py::test_stored_counts_must_be_consistent"
+      "tests/test_data_model.py::test_stored_counts_must_be_consistent",
+      "tests/test_data_model.py::test_the_validity_checks_cannot_be_waived",
+      "tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option",
+      "tests/test_statistics.py::test_the_two_validity_checks"
     ]
   },
   {
@@ -1897,13 +2036,24 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:decision"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:result_state"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_calibration.py::test_calibration_never_changes_the_outcome_or_the_verdict",
+      "tests/test_reference_numbers.py::test_each_sensitivity_set",
+      "tests/test_reference_numbers.py::test_mpea_alone_1_per_source_in_the_pooled_run"
+    ]
   },
   {
     "key": "selection_and_missingness",
@@ -1932,11 +2082,18 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:OUTCOME_WORDING.sufficient",
+          "equals": "sufficient in the sources searched"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_statistics.py::test_the_wording_is_scoped_to_the_sources_searched"
+    ],
     "history": [],
     "notes": []
   },
@@ -1966,13 +2123,39 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:CALIBRATION_SIMULATIONS",
+          "equals": 2000
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:CALIBRATION_SCATTER_MPA",
+          "equals": 60.0
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:CALIBRATION_SHIFT_MPA",
+          "equals": 40.0
+        },
+        {
+          "ref": "python:hypocurate.pipeline.calibration:exact_interval"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.calibration:seed"
+        }
+      ],
       "note": null
     },
     "history": [],
-    "notes": [],
-    "tests": []
+    "notes": [
+      "Step 7 finding (reported, not gated): on the sets frozen in step 6 the fixed method gives about 7.8% significant no-effect results for the pooled set and 8.0% for the earlier 98-record set over long runs (40,000 simulations), and the reference script's own loop gives the same; PRD 5.10's 7.2% (6.1% to 8.4%) is not reproduced."
+    ],
+    "tests": [
+      "tests/test_calibration.py::test_each_world_draws_shifts_then_errors_from_one_seeded_generator",
+      "tests/test_calibration.py::test_the_interval_is_the_exact_binomial_interval",
+      "tests/test_calibration.py::test_the_seed_is_fixed_by_the_freeze_the_analysis_and_the_method",
+      "tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values"
+    ]
   },
   {
     "key": "normal_errors_in_calibration",
@@ -2000,15 +2183,21 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.calibration:simulate"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [
       "The full error model is entry 'calibration_error_model'."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_calibration.py::test_each_world_draws_shifts_then_errors_from_one_seeded_generator"
+    ]
   },
   {
     "key": "calibration_error_model",
@@ -2037,11 +2226,18 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.calibration:simulate"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_calibration.py::test_each_world_draws_shifts_then_errors_from_one_seeded_generator",
+      "tests/test_calibration.py::test_the_simulation_runs_the_locked_test_exactly_as_the_reference_implementation"
+    ],
     "history": [],
     "notes": []
   },
@@ -2049,9 +2245,9 @@
     "key": "reference_test_tolerance",
     "name": "Reference-test tolerance",
     "state": "in_force",
-    "statement": "The fixed-plan reference test passes when k and its uncertainty are within ±1 of the reference values.",
+    "statement": "Two tiers. Against the approved reference numbers, which are rounded: half a unit in the last digit stated (k and its standard error stated to 0.1, so ±0.05; a p-value stated to two significant figures must round to them); counts exact. Against the independent reference implementation on the same frozen data: relative 1e-9.",
     "value": {
-      "text": "±1 on k and on its uncertainty",
+      "text": "±0.05 on k and SE; p within its rounding; 1e-9 relative against the reference implementation",
       "unit": "MPa·µm^0.5"
     },
     "category": "statistical",
@@ -2061,8 +2257,8 @@
       "PRD 5.7."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -2071,15 +2267,30 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "file:tests/test_reference_numbers.py:half a unit in the last digit"
+        }
+      ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "The fixed-plan reference test passes when k and its uncertainty are within ±1 of the reference values.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 7 (owner, 2026-10-05)."
+      }
+    ],
     "notes": [
-      "The reference values are recomputed before step 7 (decision 'permitted_test_types')."
+      "Tighter than the earlier ±1, which the PRD set before the numbers were recomputed; approved by the owner on 2026-10-05."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation",
+      "tests/test_reference_numbers.py::test_half_a_unit_in_the_last_digit",
+      "tests/test_reference_numbers.py::test_pooled"
+    ]
   },
   {
     "key": "paper_grouping_by_doi",
@@ -2714,22 +2925,23 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.record:HARMONIZED_FIELDS.grain_size",
           "equals": "µm"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:TRANSFORMATIONS"
         }
       ],
-      "done": "Records carry grain size in µm only.",
-      "pending": "The transformation the locked plan names (variables.predictor.transformation), applied when the analysis data are built (step 7).",
-      "step": 7,
       "note": null
     },
     "history": [],
     "notes": [],
     "tests": [
-      "tests/test_adapter_mpea.py::test_every_record_has_the_common_fields_with_their_units"
+      "tests/test_adapter_mpea.py::test_every_record_has_the_common_fields_with_their_units",
+      "tests/test_statistics.py::test_the_model_is_the_one_supported_model"
     ]
   },
   {
@@ -3454,7 +3666,7 @@
     "key": "plan_named_parts",
     "name": "The plan's schema",
     "state": "in_force",
-    "statement": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule.",
+    "statement": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule. Step 7 adds the 'calibration' part (both methods, the number of simulations, the fixed scatter and shift, the estimation method and the smallest effect).",
     "value": {
       "text": "PLAN_SCHEMA (nested, named keys and vocabulary leaves)",
       "unit": null
@@ -3500,6 +3712,12 @@
         "from": "2026-10-05",
         "to": "2026-10-05",
         "note": "Step 5 wording; extended by the owner in step 6 planning (2026-10-05)."
+      },
+      {
+        "value": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 7 (owner, 2026-10-05)."
       }
     ],
     "notes": [
@@ -3511,7 +3729,8 @@
       "tests/test_eligibility.py::test_decisions_ignore_the_domain_profile",
       "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
       "tests/test_plan.py::test_invalid_plans_are_refused",
-      "tests/test_plan.py::test_the_default_plan_is_valid_and_is_its_own_projection"
+      "tests/test_plan.py::test_the_default_plan_is_valid_and_is_its_own_projection",
+      "tests/test_statistics.py::test_an_invalid_calibration_part_is_refused_at_the_lock"
     ]
   },
   {
@@ -4011,7 +4230,7 @@
     "key": "code_vocabularies",
     "name": "Vocabularies of codes our own code writes",
     "state": "in_force",
-    "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
+    "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase), and the calibration and estimation methods (step 7) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
     "value": {
       "text": "flag kinds, flag categories, eligibility rules, sensitivity keys, plan rule codes",
       "unit": null
@@ -4125,6 +4344,19 @@
             "not_required",
             "required"
           ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:CALIBRATION_METHODS",
+          "equals": [
+            "estimated",
+            "fixed"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:ESTIMATION_METHODS",
+          "equals": [
+            "henderson_iii"
+          ]
         }
       ],
       "note": null
@@ -4135,6 +4367,12 @@
         "from": "2026-10-05",
         "to": "2026-10-05",
         "note": "Step 5. Step 6 additions approved by the owner on 2026-10-05 (planning, questions 3, 5, 6, 9 and decision C)."
+      },
+      {
+        "value": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 7 (owner, 2026-10-05)."
       }
     ],
     "notes": [],
@@ -4355,7 +4593,7 @@
     "key": "code_role_access",
     "name": "Inclusion and Checks read through access objects",
     "state": "in_force",
-    "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
+    "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds. Step 7 (owner, 2026-10-05; a safeguard change): Statistics binds only at the analysis stage and receives exactly the locked plan and the frozen data (the frozen sets and, for their records only, what the model needs, outcome included); the gap facts bind at the analysis stage and when a run closed without a freeze, and receive no outcome value.",
     "value": {
       "text": "Inclusion: plan, record conditions, flag kinds; Checks: plan, all values",
       "unit": null
@@ -4388,16 +4626,27 @@
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 7 (owner, 2026-10-05)."
+      }
+    ],
     "notes": [
       "Step 6 review, finding 2 (2026-10-06): Inclusion's list gains 'set_flags' (each sensitivity set's matching flags from the completed Checks result: codes and record ids, no numbers)."
     ],
     "tests": [
-      "tests/test_access_code_roles.py::test_the_code_lists_match_the_owners_decision",
-      "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
-      "tests/test_access_code_roles.py::test_only_code_roles_bind_without_an_agent_setting",
       "tests/test_access_code_roles.py::test_an_agent_setting_cannot_bind_as_a_code_role",
       "tests/test_access_code_roles.py::test_code_roles_do_not_bind_at_any_other_stage",
+      "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
+      "tests/test_access_code_roles.py::test_only_code_roles_bind_without_an_agent_setting",
+      "tests/test_access_code_roles.py::test_the_code_lists_match_the_owners_decision",
+      "tests/test_access_statistics.py::test_records_outside_the_frozen_sets_never_reach_statistics",
+      "tests/test_access_statistics.py::test_the_complete_input_of_statistics",
+      "tests/test_access_statistics.py::test_the_gap_facts_receive_no_outcome_value",
+      "tests/test_access_statistics.py::test_the_lists_are_the_owners_decision",
       "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification"
     ]
   },
@@ -4480,10 +4729,17 @@
         {
           "ref": "python:hypocurate.pipeline.writes:CONSTRUCTED_MARK",
           "equals": "constructed_test_data"
+        },
+        {
+          "ref": "python:hypocurate.db.models:TEST_RUN_LABEL",
+          "equals": "test run: includes constructed data"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.results:REAL_RUN"
         }
       ],
-      "done": "The mark and the refusals at storage, inclusion and freeze (step 6).",
-      "pending": "The label wherever a marked run's outcome, verdict or numbers are stored or shown, and the exclusion from aggregates and lists of real results (steps 7 and 10).",
+      "done": "The mark and the refusals at storage, inclusion and freeze (step 6). Step 7: the label on every stored analysis and calibration result and on the statistics and gap-facts stage results of a marked run (checked by the database for result rows), and one named condition that leaves marked runs out of every aggregate (pipeline/results.py, REAL_RUN).",
+      "pending": "The label and the exclusion on every screen and list (step 10).",
       "step": 10,
       "note": "The guard is in code; the database itself does not refuse a constructed record."
     },
@@ -4493,8 +4749,10 @@
       "Step 6 review (2026-10-06), for a later step: a source whose definition is unknown to the code should fail closed (be treated as constructed, or refused), not pass the guard."
     ],
     "tests": [
-      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
-      "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records"
+      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates",
+      "tests/test_analysis_stage.py::test_a_marked_run_with_no_dataset_frozen_is_labelled_too",
+      "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records",
+      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test"
     ]
   },
   {
@@ -4546,16 +4804,22 @@
   {
     "key": "below_minimum_display",
     "name": "What a run below the fixed minimums shows",
-    "state": "open",
-    "statement": "Open: what a run below the fixed minimums may show besides 'insufficient'.",
-    "value": null,
+    "state": "in_force",
+    "statement": "Under the fixed-minimum option, when the pooled fit misses any minimum, every analysis of the run (pooled, per source and sensitivity) is withheld: it holds the counts against each minimum, which minimums were missed and the records found (for a plot drawn in step 10), and no coefficient, no fitted line and nothing else computed from the outcome values; this applies even where check 2 fails, so the coefficient-only rule applies only to results whose numbers are shown. Label: 'data found; not enough to test'. The estimated power, which uses no outcome value, is still shown.",
+    "value": {
+      "text": "counts, minimums missed and records found; nothing from outcomes; run-wide",
+      "unit": null
+    },
     "category": "statistical",
     "affects": "The gap report and the run viewer for runs below the minimums.",
     "reason": "The sufficiency option must not be choosable after seeing an estimate.",
     "evidence": [
       "Owner, step 6 approval (2026-10-05)."
     ],
-    "decided": null,
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
     "expert_review": {
       "status": "not_reviewed",
       "name": null,
@@ -4563,19 +4827,40 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 7,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:BELOW_MINIMUMS_LABEL",
+          "equals": "data found; not enough to test"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:pooled_withheld"
+        },
+        {
+          "ref": "sql:ck_analysis_result_withheld_set"
+        }
+      ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "open decision: Open: what a run below the fixed minimums may show besides 'insufficient'.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Open from step 6 approval; decided by the owner in step 7 planning."
+      }
+    ],
     "notes": [
-      "Owner's starting position: the counts and which minimums were not met, and nothing derived from outcome values, not even a coefficient, so that the sufficiency option cannot be chosen after seeing an estimate."
+      "Owner's starting position: the counts and which minimums were not met, and nothing derived from outcome values, not even a coefficient, so that the sufficiency option cannot be chosen after seeing an estimate.",
+      "The database computes 'withheld' itself (migration 0004) and refuses a number in a withheld result."
     ],
-    "tests": [],
-    "pending": {
-      "by": "owner",
-      "before_step": 7
-    }
+    "tests": [
+      "tests/test_analysis_stage.py::test_below_the_minimums_every_analysis_holds_counts_and_records_only",
+      "tests/test_analysis_stage.py::test_the_database_computes_withheld_and_refuses_a_number_in_a_withheld_result",
+      "tests/test_analysis_stage.py::test_the_fixed_option_with_one_group_withholds_even_the_coefficient",
+      "tests/test_analysis_stage.py::test_withheld_results_do_not_depend_on_the_outcome_values",
+      "tests/test_reference_numbers.py::test_texas_am_alone_3_fixed_minimums_withheld"
+    ]
   },
   {
     "key": "curator_tabular_sources",
@@ -4636,7 +4921,7 @@
     },
     "sensitivity": "The eight sensitivity sets of the reference plan; their recomputed values are in the step 6 summary.",
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "file:CLAUDE.md:Pooled: 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6"
@@ -4645,10 +4930,7 @@
           "ref": "file:CLAUDE.md:First source alone (MPEA): 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6"
         }
       ],
-      "done": "The record counts, alloys, groups and residual degrees of freedom are regression tests on the pipeline's frozen sets (step 6).",
-      "pending": "The coefficients, uncertainties and p-values, reproduced independently by the statistics module and made regression tests (step 7).",
-      "step": 7,
-      "note": "The step 6 values come from a test-side script, not from package code."
+      "note": null
     },
     "history": [
       {
@@ -4662,8 +4944,12 @@
       "Approved by the owner on 2026-10-06; CLAUDE.md 'Reference numbers' updated the same day."
     ],
     "tests": [
-      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139",
-      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
+      "tests/test_reference_numbers.py::test_each_sensitivity_set",
+      "tests/test_reference_numbers.py::test_mpea_alone_1_per_source_in_the_pooled_run",
+      "tests/test_reference_numbers.py::test_pooled",
+      "tests/test_reference_numbers.py::test_texas_am_alone_1_per_source_in_the_pooled_run",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
     ]
   },
   {
@@ -4940,5 +5226,381 @@
     "tests": [
       "tests/test_plan.py::test_invalid_plans_are_refused"
     ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [
+      "A departure from PRD 5.10 (a safeguard change): second-model review before the merge."
+    ],
+    "key": "calibration_both_ways",
+    "name": "Calibration reported both ways",
+    "state": "in_force",
+    "statement": "Per-run calibration is run twice for every analysis whose inference is valid and whose numbers are shown: once with the fixed scatter and per-group shift of the plan (PRD 5.10's 60 and 40 MPa by default), and once with both estimated by code from the frozen records (entry 'calibration_noise_levels'). Both are stored. The methods are fixed at the rules lock in the plan's 'calibration' part. Calibration stays a flag, never a gate.",
+    "value": {
+      "text": "fixed and estimated, both stored",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "The calibration results stored per analysis (two rows: method 'fixed' and 'estimated').",
+    "reason": "Fixed values alone describe the test on illustrative noise; estimated values describe it on noise like this run's. Showing both lets a reader see how much the assumptions matter.",
+    "evidence": [
+      "Owner, step 7 brief (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:CALIBRATION_METHODS",
+          "equals": [
+            "fixed",
+            "estimated"
+          ]
+        },
+        {
+          "ref": "sql:ck_calibration_result_method_iff_analysis"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_analysis_stage.py::test_every_analysis_is_stored_with_both_calibrations",
+      "tests/test_calibration.py::test_the_estimated_method_uses_the_estimates_and_the_fixed_method_the_plan",
+      "tests/test_calibration.py::test_calibration_never_changes_the_outcome_or_the_verdict",
+      "tests/test_statistics.py::test_an_invalid_calibration_part_is_refused_at_the_lock"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "smallest_effect",
+    "name": "Smallest effect of interest",
+    "state": "in_force",
+    "statement": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it, and so does the estimated power, which is the share detected in the fixed method's effect world, labelled 'estimated power under the stated assumptions'. The power is information only and uses no outcome value, so it is shown also below the minimums.",
+    "value": {
+      "text": "150 (default)",
+      "unit": "MPa·µm^0.5"
+    },
+    "category": "statistical",
+    "affects": "The calibration's effect world and the estimated power; never the outcome or the verdict.",
+    "reason": "PRD 5.8 and 5.10; owner, step 7 brief.",
+    "evidence": [
+      "PRD 5.8, 5.10, 17 (decisions 8 and 10); owner, step 7 brief and planning decision 5 (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:SMALLEST_EFFECT",
+          "equals": 150.0
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:POWER_LABEL",
+          "equals": "estimated power under the stated assumptions"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_calibration.py::test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome",
+      "tests/test_statistics.py::test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "evidence_level_scale",
+    "name": "Evidence level",
+    "state": "in_force",
+    "statement": "Every run's statistics result stores an evidence level from 1 to 6, derived by one tested function from the result state, never by an agent: 6 sufficient with a verdict; 5 use what is available with a minimum missed (exploratory); 4 inference invalid, coefficient only; 3 below the minimums under the fixed option; 2 coefficient cannot be fitted; 1 no dataset frozen. Precedence: no freeze; below the minimums (fixed option); not fitted; coefficient only; exploratory; sufficient. Descriptive only; it never affects the outcome or the verdict. A marked test run keeps its level beside its test label. A partly sufficient original question keeps the level of its own pooled result state.",
+    "value": {
+      "text": "1 to 6",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "What is stored and shown with a run; filtering runs by level.",
+    "reason": "A single descriptive scale of how far a run got, computed by code.",
+    "evidence": [
+      "Owner, step 7 (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:EVIDENCE_LEVELS"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:evidence_level"
+        },
+        {
+          "ref": "sql:ck_run_evidence_level"
+        }
+      ],
+      "note": "Copied onto the run by the copy path only; the database checks it agrees with the outcome, verdict and exploratory label but does not require it on a completed run."
+    },
+    "tests": [
+      "tests/test_statistics.py::test_every_result_state_has_its_evidence_level",
+      "tests/test_statistics.py::test_the_evidence_scale_is_the_owners",
+      "tests/test_statistics.py::test_the_level_never_feeds_back_into_the_outcome_or_verdict",
+      "tests/test_analysis_stage.py::test_the_evidence_level_must_agree_with_the_outcome",
+      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "per_source_labels",
+    "name": "Per-source labels",
+    "state": "in_force",
+    "statement": "Each per-source result has one of four labels, from the locked test and the sign only, no new threshold: 'not enough data' (no p-value; also when the pooled result has none, or a coefficient is exactly zero); 'agrees' (the same decision as pooled at the plan's threshold and the same sign); 'conflicts' (the opposite sign from pooled); 'same direction, different decision' (the same sign, a different decision). Descriptive only; never the verdict.",
+    "value": {
+      "text": "agrees; conflicts; same direction, different decision; not enough data",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "The label stored with each per-source result.",
+    "reason": "The PRD names the labels (PRD 7, analysis_result) but does not define them.",
+    "evidence": [
+      "Owner, step 7 planning decisions 2 and 3 (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:LABELS",
+          "equals": [
+            "agrees",
+            "conflicts",
+            "same_direction_different_decision",
+            "not_enough_data"
+          ]
+        },
+        {
+          "ref": "sql:ck_analysis_result_label_per_source_only"
+        }
+      ],
+      "note": "The edge rules for a pooled result without a decision and a zero coefficient are Claude Code's, stated in planning."
+    },
+    "tests": [
+      "tests/test_statistics.py::test_the_four_per_source_labels",
+      "tests/test_reference_numbers.py::test_mpea_alone_1_per_source_in_the_pooled_run",
+      "tests/test_reference_numbers.py::test_texas_am_alone_1_per_source_in_the_pooled_run"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [
+      "No effect on the reference numbers: the two sources share no alloy."
+    ],
+    "key": "fit_alloy_rule",
+    "name": "Which records a fit uses",
+    "state": "in_force",
+    "statement": "Each fit (pooled, per source, sensitivity) uses only alloys with at least two distinct grain sizes among that analysis's own records: the model's own condition, applied by code to grain sizes only. The frozen set is not changed; the records not used are counted and reported as 'not used in this fit'. The stored counts, and the minimums, are the fit's.",
+    "value": {
+      "text": "two or more distinct grain sizes per alloy, within each fit",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Per-source and sensitivity fits where an alloy qualifies only pooled.",
+    "reason": "PRD 5.7 ('which alloys can be used'); the eligibility rule counts grain sizes over the whole primary set.",
+    "evidence": [
+      "Owner, step 7 planning decisions 7 and 12 (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:MODEL_MIN_GRAIN_SIZES",
+          "equals": 2
+        },
+        {
+          "ref": "sql:n_records_not_used"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes",
+      "tests/test_analysis_stage.py::test_the_database_refuses_records_not_accounted_for"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "copy_decision_only_copies",
+    "name": "The decision is copied, not recomputed",
+    "state": "in_force",
+    "statement": "The analysis stage stores the run's decision (outcome, verdict, exploratory label, evidence level) with the freeze fingerprint it belongs to; it does not complete the run. A separate function copies the stored decision onto the run, unchanged, and completes it; it refuses, and logs the refusal, when the decision is missing or belongs to a different freeze. 'Partly sufficient' is not set by it (a step 8 decision).",
+    "value": {
+      "text": "store, then copy unchanged",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "How a run's outcome reaches the run row (orchestration in steps 8 and 9).",
+    "reason": "The Analyst runs after the statistics, and 'partly sufficient' needs the Planner's narrower question.",
+    "evidence": [
+      "Owner, step 7 planning decision 6 and addition 11 (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.completion:copy_decision"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_completion.py::test_the_decision_is_copied_unchanged",
+      "tests/test_completion.py::test_it_refuses_a_missing_decision_and_logs_it",
+      "tests/test_completion.py::test_it_refuses_a_decision_of_another_freeze_and_logs_it",
+      "tests/test_completion.py::test_it_copies_what_is_stored_and_never_recomputes",
+      "tests/test_completion.py::test_the_database_checks_the_copy_again"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "results_pure_function",
+    "name": "Results are a pure function of the frozen set and the plan",
+    "state": "in_force",
+    "statement": "The statistics read only the frozen sets (through the Statistics access object) and the locked plan. Records are sorted by stable identity before any arithmetic, and seeds come from the freeze fingerprint, the analysis and the method, so the same data give the same numbers whatever the record ids or insertion order.",
+    "value": {
+      "text": "identity order; seed from the freeze",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Reproducibility of every result.",
+    "reason": "PRD 13.1; owner, step 7 brief.",
+    "evidence": [
+      "Owner, step 7 brief (2026-10-05)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
+    },
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:design"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.calibration:seed"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_permutation_stats.py::test_permuted_ids_and_insertion_order_give_identical_results",
+      "tests/test_statistics.py::test_results_do_not_depend_on_record_order_or_ids"
+    ]
+  },
+  {
+    "sensitivity": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "history": [],
+    "notes": [],
+    "key": "records_without_group",
+    "name": "Records without a group in a fit",
+    "state": "open",
+    "statement": "Open: what a fit does with a frozen record that has no group (a literature record whose paper is not known). Until decided, code fails closed and invents no group: the pooled analysis refuses the analysis stage (logged, 'records_without_group'); a per-source or sensitivity analysis is reported as not analysed, with the count, and nothing is stored for it.",
+    "value": null,
+    "decided": null,
+    "category": "statistical",
+    "affects": "Sensitivity sets that admit records without a paper (in sprint 1 only the controlled extract's, in 'possible_duplicates_separate' of a marked run); no record in the reference sets lacks a group.",
+    "reason": "A clustered standard error needs every record in a group; register 'paper_grouping_by_doi' says no group is invented.",
+    "evidence": [
+      "Found while building step 7 (2026-10-06): the marked run's 'possible_duplicates_separate' set holds two extract records without a DOI."
+    ],
+    "applied": {
+      "status": "partly",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.analysis:RecordsWithoutGroup"
+        }
+      ],
+      "done": "Fail closed: pooled refuses; a descriptive analysis is reported as not analysed with the count.",
+      "pending": "The owner's decision.",
+      "step": 8,
+      "note": null
+    },
+    "tests": [
+      "tests/test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one",
+      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates"
+    ],
+    "pending": {
+      "by": "owner",
+      "before_step": 8
+    }
   }
 ]
```


## 9. Tests: new files (full text)

### `tests/reference_stats.py`

```python
"""The independent reference implementation of the statistics (test side only; step 7).

PRD 13.3, software correctness: the package's coefficient, uncertainty and p-value must match an
independent implementation within numerical tolerance. This one uses statsmodels (a test-only
dependency, not in the deployed image) with explicit dummy variables, as the reference scripts in
`docs/reference/` do: OLS of the outcome on k × d^-1/2 plus one intercept per alloy, statsmodels'
cluster-robust covariance grouped by paper (its default small-sample correction), and a one-sided
p-value against t with (groups - 1) degrees of freedom. It shares no code with
`hypocurate.pipeline.statistics` or `calibration`: the model's alloy rule (two or more distinct
grain sizes) and the sorting are reimplemented here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats


def frame(rows) -> pd.DataFrame:
    """rows: (alloy, group, grain size in µm, outcome). Only alloys with two or more distinct grain sizes."""
    f = pd.DataFrame(list(rows), columns=["alloy", "group", "d", "y"])
    sizes = f.groupby("alloy")["d"].nunique()
    f = f[f["alloy"].isin(sizes[sizes >= 2].index)].copy()
    f["x"] = f["d"] ** -0.5
    return f.reset_index(drop=True)


def fit(rows) -> dict:
    """k, its cluster-robust standard error and the one-sided p-value; counts."""
    f = frame(rows)
    n, alloys, groups = len(f), f["alloy"].nunique(), f["group"].nunique()
    out = {"n": n, "alloys": alloys, "groups": groups, "resid_df": n - alloys - 1}
    if alloys == 0:
        return {**out, "k": None, "se": None, "p": None}
    formula = "y ~ x + C(alloy)" if alloys > 1 else "y ~ x"
    if n - alloys - 1 < 1 or groups < 2:
        return {**out, "k": float(smf.ols(formula, f).fit().params["x"]), "se": None, "p": None}
    m = smf.ols(formula, f).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(f["group"])[0]})
    k, se = float(m.params["x"]), float(m.bse["x"])
    return {**out, "k": k, "se": se, "p": float(stats.t.sf(k / se, groups - 1))}


def henderson_iii(rows) -> dict:
    """Method III by statsmodels' OLS fits and an explicit projection (numpy pinv)."""
    f = frame(rows)
    reduced = smf.ols("y ~ x + C(alloy)", f).fit()
    full = smf.ols("y ~ x + C(alloy) + C(group)", f).fit()
    rss_r, rss_f = float(reduced.ssr), float(full.ssr)
    rank_r, rank_f = int(np.linalg.matrix_rank(reduced.model.exog)), int(np.linalg.matrix_rank(full.model.exog))
    x = reduced.model.exog
    projection = x @ np.linalg.pinv(x)
    z = pd.get_dummies(f["group"]).to_numpy(dtype=float)
    residual = z - projection @ z
    trace = float(np.trace(residual.T @ residual))
    n = len(f)
    scatter_sq = rss_f / (n - rank_f)
    return {"rss_reduced": rss_r, "rss_full": rss_f, "rank_reduced": rank_r, "rank_full": rank_f, "trace": trace,
            "scatter_squared": scatter_sq,
            "shift_squared_untruncated": (rss_r - rss_f - (rank_f - rank_r) * scatter_sq) / trace}


def significant_count(x, alloy, group, outcomes, alpha) -> int:
    """The locked test on each row of `outcomes`, one statsmodels fit per row (explicit dummies)."""
    alloy, group = np.asarray(alloy), np.asarray(group)
    dummies = pd.get_dummies(alloy).to_numpy(dtype=float)
    exog = np.column_stack([x, dummies])  # k first, then one intercept per alloy (no constant)
    g = len(set(group.tolist()))
    hits = 0
    for y in outcomes:
        m = sm.OLS(y, exog).fit(cov_type="cluster", cov_kwds={"groups": group})
        hits += stats.t.sf(m.params[0] / m.bse[0], g - 1) < alpha
    return int(hits)
```

### `tests/generator.py`

```python
"""The data generator (PRD 13.3; build step 7), test side.

It produces datasets from the model the system tests, with every property set by us (number of
alloys and their grain sizes, records per grain size, groups and how records are spread over them,
true effect, scatter, per-group shift), so that results can be scored without materials
knowledge. Alloys have invented compositions of the invented elements "Qa" and "Qb", so that no
model could answer from what it knows about real alloys. Deterministic for a seed.

`frozen_data(spec)` gives the records in the shape the access layer's `frozen_analysis_data`
returns, so the package's pure `analysis.analyse` can run on them without a database; `rows(...)`
gives (alloy, group, grain size, outcome) for the reference implementation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from hypocurate.pipeline.plan import default_plan
from hypocurate.sources.normalize import same_alloy_key


@dataclass(frozen=True)
class Spec:
    name: str
    seed: int
    n_alloys: int
    grain_sizes: tuple  # the distinct grain sizes (µm) of every alloy
    repeats: int  # records per alloy and grain size
    n_groups: int
    k: float
    scatter: float
    shift: float
    groups: str = "spread"  # "spread" (round robin), "one" (a single group), "per_alloy" (nested in alloys)
    single_size_alloys: int = 0  # extra alloys measured at one grain size only
    extra: dict = field(default_factory=dict)


def _group(spec: Spec, a: int, n: int) -> int:
    if spec.groups == "one":
        return 0
    if spec.groups == "per_alloy":
        return a % spec.n_groups
    return n % spec.n_groups


def frozen_data(spec: Spec) -> dict:
    rng = np.random.default_rng(spec.seed)
    shifts = rng.normal(0.0, spec.shift, spec.n_groups)
    records, n = [], 0
    layout = [(a, d) for a in range(spec.n_alloys) for d in spec.grain_sizes]
    layout += [(spec.n_alloys + j, spec.grain_sizes[0]) for j in range(spec.single_size_alloys)]
    for a, d in layout:
        for _ in range(spec.repeats):
            g = _group(spec, a, n)
            y = 250.0 + 40.0 * a + spec.k * d ** -0.5 + shifts[g] + rng.normal(0.0, spec.scatter)
            n += 1
            records.append({"id": n, "source": "mpea", "version_fingerprint": f"gen-{spec.name}",
                            "origin": f"generated:{spec.name}:row:{n}", "item_index": n - 1,
                            "composition": {"Qa": float(10 + a), "Qb": float(90 - a)},
                            "paper": f"paper-{g:03d}", "batch": None, "grain_size": float(d), "outcome": float(y)})
    fp = hashlib.sha256(f"{spec.name}|{spec.seed}".encode()).hexdigest()
    return {"freeze_fingerprint": fp, "outcome_field": "yield_strength", "sets": {"primary": [r["id"] for r in records]},
            "records": records}


def rows(data: dict, ids=None) -> list[tuple]:
    chosen = [r for r in data["records"] if ids is None or r["id"] in set(ids)]
    return [(same_alloy_key(r["composition"]), r["paper"], r["grain_size"], r["outcome"]) for r in chosen]


def plan(option: str = "fixed_minimum", minimums=(30, 5, 10, 10), n_simulations: int = 2000) -> dict:
    """The default plan without sensitivity analyses (generated data have only a primary set)."""
    p = default_plan(1)
    p["sensitivity_analyses"] = []
    p["sufficiency"] = {"option": option, "min_records": minimums[0], "min_alloys": minimums[1],
                        "min_groups": minimums[2], "min_resid_df": minimums[3]}
    p["calibration"]["n_simulations"] = n_simulations
    return p


# The fixed set (PRD 13.3): each dataset with its seed; the expected results are in
# tests/test_generated_fixed_set.py.
FIXED_SET = (
    Spec("effect_many_papers", 101, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=300.0, scatter=40.0, shift=20.0),
    Spec("no_effect_many_papers", 102, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=0.0, scatter=40.0, shift=20.0),
    Spec("negative_effect", 103, n_alloys=6, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=-200.0, scatter=40.0, shift=20.0),
    Spec("large_paper_shifts", 104, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=150.0, scatter=20.0, shift=120.0),
    Spec("small_but_valid", 105, n_alloys=3, grain_sizes=(1.0, 9.0), repeats=2, n_groups=4,
         k=300.0, scatter=30.0, shift=10.0),
    Spec("single_group", 106, n_alloys=6, grain_sizes=(1.0, 4.0, 16.0), repeats=2, n_groups=1,
         k=300.0, scatter=30.0, shift=0.0, groups="one"),
    Spec("one_alloy_two_sizes", 107, n_alloys=1, grain_sizes=(1.0, 9.0), repeats=1, n_groups=2,
         k=300.0, scatter=30.0, shift=0.0),
    Spec("no_alloy_with_two_sizes", 108, n_alloys=0, grain_sizes=(4.0,), repeats=1, n_groups=3,
         k=300.0, scatter=30.0, shift=0.0, single_size_alloys=6),
    Spec("papers_nested_in_alloys", 109, n_alloys=10, grain_sizes=(1.0, 4.0, 16.0), repeats=2, n_groups=10,
         k=300.0, scatter=30.0, shift=30.0, groups="per_alloy"),
    Spec("single_size_alloys_added", 110, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=300.0, scatter=40.0, shift=20.0, single_size_alloys=4),
)
SPECS = {s.name: s for s in FIXED_SET}
```

### `tests/stats_world.py`

```python
"""Step 7 test helper: small runs through the real pipeline (adapters, Checks, Inclusion, the freeze)
from constructed MPEA-layout files, for the analysis stage and the copy path.

`small_rows(alloys, sizes, papers)` builds rows with invented-looking but parseable formulas (each
alloy a different equiatomic composition), every row in scope (FCC, tension, 25 °C).
`run_on(engine, rows, option, mins)` registers the file as source 'mpea', dispatches a run that
chose it, and takes it through the freeze under the reference plan with the given sufficiency
option and minimums.
"""
from __future__ import annotations

from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan

FORMULAS = ("CoCrFeMnNi", "CoCrFeNi", "CoCrNi", "CoFeNi", "CrFeNi", "CoCrMnNi", "CoFeMnNi", "CrFeMnNi",
            "FeMnNi", "CoMnNi", "CoCrFe", "CoNi")


def small_rows(n_alloys: int, sizes=(1.0, 9.0), papers: int = 3, k: float = 300.0, repeats: int = 1,
               base: float = 200.0) -> list[dict]:
    rows, i = [], 0
    for a in range(n_alloys):
        for d in sizes:
            for r in range(repeats):
                noise = ((i * 37) % 11 - 5) * 3.0  # small deterministic scatter
                ys = round(base + 30 * a + k * d ** -0.5 + noise, 1)
                rows.append(pw.mpea_row(FORMULAS[a], d, ys, doi=f"10.1016/j.test.2026.{(i % papers) + 1:03d}"))
                i += 1
    return rows


def plan_for(vid: int, option: str = "fixed_minimum", mins=(30, 5, 10, 10)) -> dict:
    plan = reference_plan(vid)
    plan["sufficiency"] = {"option": option, "min_records": mins[0], "min_alloys": mins[1], "min_groups": mins[2],
                           "min_resid_df": mins[3]}
    return plan


def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True) -> int:
    if register:
        pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
    rid = pw.dispatched_run(engine, sources=("mpea",), marked=marked)
    checkpoints.lock_rules(engine, rid, plan_for(pw.version_of(engine, rid), option, mins))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid


def rows_of(engine, sql: str, **params) -> list:
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def val(engine, sql: str, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def audit_codes(engine, run_id: int, function: str) -> list:
    return [r[0] for r in rows_of(engine, "SELECT detail->>'code' FROM audit_log WHERE run_id = :r AND function = :f "
                                          "AND NOT allowed ORDER BY id", r=run_id, f=function)]
```

### `tests/test_statistics.py`

```python
"""Step 7: the supported model, the validity checks, the minimums, the verdict, the labels and
the evidence level (PRD 5.7 to 5.9; CLAUDE.md rules 5 to 7; owner's decisions of 2026-10-05).
Pure functions, no database."""
from __future__ import annotations

import ast
import math
import random
from pathlib import Path

import numpy as np
import pytest

import generator as g
import reference_stats as rs
from hypocurate.pipeline import analysis, profile
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.plan import PlanError, default_plan, validate

PACKAGE = Path(__file__).resolve().parents[1] / "hypocurate" / "pipeline"


def obs(rows):
    """(identity, alloy, group, grain size, outcome) tuples as observations."""
    return [st.Observation(*r) for r in rows]


def test_the_model_is_the_one_supported_model():
    assert st.MODEL_MIN_GRAIN_SIZES == 2
    assert set(st.TRANSFORMATIONS) == {"inverse_square_root"}
    assert st.TRANSFORMATIONS["inverse_square_root"](4.0) == 0.5
    assert default_plan(1)["model"] == {"name": "hall_petch_alloy_intercepts", "null": "k <= 0",
                                        "alternative": "k > 0", "alpha": 0.05}


def test_the_small_sample_correction_is_statsmodels_default():
    """G/(G-1) × (N-1)/(N-K), K = alloys + 1 (register 'cluster_robust_se')."""
    assert st.small_sample_factor(97, 22, 20) == pytest.approx((20 / 19) * (96 / 74), rel=1e-15)


def test_the_fit_matches_the_reference_on_a_hand_made_dataset():
    rows = [("r1", "A", "p1", 1.0, 500.0), ("r2", "A", "p2", 4.0, 420.0), ("r3", "A", "p3", 16.0, 390.0),
            ("r4", "B", "p1", 1.0, 700.0), ("r5", "B", "p2", 9.0, 600.0), ("r6", "B", "p3", 25.0, 585.0),
            ("r7", "C", "p4", 2.0, 300.0), ("r8", "C", "p4", 8.0, 260.0)]
    f = st.fit(st.design(obs(rows), "inverse_square_root"))
    ref = rs.fit([(a, gr, d, y) for _, a, gr, d, y in rows])
    assert math.isclose(f.estimate, ref["k"], rel_tol=1e-9) and math.isclose(f.std_error, ref["se"], rel_tol=1e-9)
    assert math.isclose(f.p_value, ref["p"], rel_tol=1e-9) and f.df == 3


def test_the_test_is_one_sided():
    """k < 0 gives p > 0.5: a negative slope is never support for k > 0."""
    data = g.frozen_data(g.SPECS["negative_effect"])
    pooled = analysis.analyse(g.plan("use_available"), data)["analyses"][0]
    assert pooled["estimate"] < 0 and pooled["p_value"] > 0.5 and pooled["significant"] is False


def test_supported_exactly_when_p_is_strictly_below_alpha():
    assert st.significant(0.0499999, 0.05) is True
    assert st.significant(0.05, 0.05) is False
    assert st.significant(0.0500001, 0.05) is False
    assert st.significant(None, 0.05) is None
    plan = g.plan("use_available")
    pooled = {"withheld": False, "checks": {"coefficient_fitted": True, "inference_valid": True},
              "minimums_met": True, "p_value": 0.05}
    assert st.decision(pooled, plan, "f")["verdict"] == "not_supported"
    assert st.decision({**pooled, "p_value": 0.049}, plan, "f")["verdict"] == "supported"


def test_a_zero_standard_error_gives_a_defined_p_value():
    assert st.one_sided_p(math.inf, 5) == 0.0 and st.one_sided_p(-math.inf, 5) == 1.0


def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
    """Decision 7: the model's own condition, on grain sizes only; the others are reported as not
    used in this fit, and the counts are the fit's (decision 12)."""
    rows = [("r1", "A", "p1", 1.0, 500.0), ("r2", "A", "p2", 4.0, 420.0), ("r3", "A", "p2", 4.0, 425.0),
            ("r4", "B", "p1", 2.0, 700.0), ("r5", "B", "p3", 2.0, 690.0),  # one distinct size
            ("r6", "C", "p4", 3.0, 300.0)]
    d = st.design(obs(rows), "inverse_square_root")
    assert (d.n, d.n_alloys, d.n_groups, d.n_records_in_set, d.n_alloys_not_used) == (3, 1, 2, 6, 2)
    assert d.resid_df == 1 and d.coefficient_fitted and d.inference_valid
    entry = st.analysis_entry(d, g.plan("use_available", minimums=(3, 1, 2, 1)), withheld=False)
    assert entry["counts"]["n_records_not_used"] == 3
    assert entry["minimums"]["records"] == {"count": 3, "minimum": 3, "met": True}
    assert entry["minimums_met"]
    entry4 = st.analysis_entry(d, g.plan("use_available", minimums=(4, 1, 2, 1)), withheld=False)
    assert not entry4["minimums_met"]  # 6 records in the set, but the fit uses 3


@pytest.mark.parametrize("rows, check1, check2", [
    ([("a", "A", "p1", 1.0, 1.0)], False, False),                                           # one record
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 1.0, 2.0)], False, False),              # one grain size
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0)], True, False),               # resid df 0
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p1", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, False),  # 1 group
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, True),
])
def test_the_two_validity_checks(rows, check1, check2):
    d = st.design(obs(rows), "inverse_square_root")
    assert (d.coefficient_fitted, d.inference_valid) == (check1, check2)
    f = st.fit(d)
    assert (f is not None) == check1
    if check1:
        assert (f.std_error is not None, f.p_value is not None) == (check2, check2)


def test_results_do_not_depend_on_record_order_or_ids():
    """Records are sorted by stable identity before any arithmetic: shuffling gives bit-identical
    numbers."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    plan = g.plan("use_available", n_simulations=200)
    first = analysis.analyse(plan, data)
    rnd = random.Random(7)
    for _ in range(3):
        records = list(data["records"])
        rnd.shuffle(records)
        new_ids = list(range(1000, 1000 + len(records)))
        rnd.shuffle(new_ids)
        remap = {r["id"]: i for r, i in zip(records, new_ids)}
        shuffled = {**data, "records": [{**r, "id": remap[r["id"]]} for r in records],
                    "sets": {"primary": [remap[i] for i in reversed(data["sets"]["primary"])]}}
        assert analysis.analyse(plan, shuffled) == first


def test_two_records_with_one_identity_are_refused():
    rows = [("same", "A", "p1", 1.0, 1.0), ("same", "A", "p2", 4.0, 2.0)]
    with pytest.raises(st.StatisticsError):
        st.design(obs(rows), "inverse_square_root")


def test_a_record_without_a_group_is_refused_never_given_one():
    """Register 'paper_grouping_by_doi': no group is invented. The analysis refuses."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    data["records"][0]["paper"] = None
    with pytest.raises(st.StatisticsError, match="records_without_group"):
        analysis.analyse(g.plan(), data)


# --- labels, states, levels -------------------------------------------------------------------

def _r(estimate, p):
    return {"estimate": estimate, "p_value": p}


@pytest.mark.parametrize("per_source, pooled, expected", [
    (_r(400, 1e-5), _r(420, 1e-6), "agrees"),                                   # same sign, both significant
    (_r(30, 0.4), _r(20, 0.3), "agrees"),                                       # same sign, both not
    (_r(-50, 0.9), _r(420, 1e-6), "conflicts"),                                 # opposite sign
    (_r(-50, 0.01), _r(-20, 0.9), "same_direction_different_decision"),         # same sign, different decision
    (_r(-50, 0.9), _r(20, 0.3), "conflicts"),                                   # opposite sign, same decision
    (_r(100, 0.2), _r(420, 1e-6), "same_direction_different_decision"),
    (_r(1173, None), _r(424, 1e-6), "not_enough_data"),                         # no p-value
    (_r(400, 1e-5), _r(424, None), "not_enough_data"),                          # pooled has no decision
    (_r(0.0, 0.5), _r(424, 1e-6), "not_enough_data"),                           # no sign
])
def test_the_four_per_source_labels(per_source, pooled, expected):
    """Owner, 2026-10-05: from the locked test and the sign only; descriptive."""
    assert st.label(per_source, pooled, 0.05) == expected


def _pooled(withheld=False, c1=True, c2=True, met=True, p=0.01):
    return {"withheld": withheld, "checks": {"coefficient_fitted": c1, "inference_valid": c2},
            "minimums_met": met, "p_value": p}


@pytest.mark.parametrize("pooled, option, state, level", [
    (None, "fixed_minimum", "no_dataset_frozen", 1),
    (_pooled(withheld=True, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(withheld=True, c1=False, c2=False, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(withheld=True, c2=False, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(c1=False, c2=False, met=False), "use_available", "not_fitted", 2),
    (_pooled(c2=False, met=False), "use_available", "coefficient_only", 4),
    (_pooled(c2=False, met=True), "fixed_minimum", "coefficient_only", 4),  # a plan whose minimums allow 1 group
    (_pooled(met=False), "use_available", "exploratory", 5),
    (_pooled(met=True), "use_available", "sufficient", 6),
    (_pooled(met=True), "fixed_minimum", "sufficient", 6),
])
def test_every_result_state_has_its_evidence_level(pooled, option, state, level):
    """Owner, 2026-10-05: 6 sufficient with a verdict; 5 exploratory; 4 coefficient only; 3 below the
    minimums under the fixed option; 2 not fitted; 1 no dataset frozen."""
    plan = g.plan(option)
    assert st.result_state(pooled, option) == state
    d = st.decision(pooled, plan, None if pooled is None else "f")
    assert d["evidence_level"] == level == st.evidence_level(state)
    assert (d["verdict"] is not None) == (level >= 5)
    assert d["exploratory"] == (level == 5)
    assert d["outcome"] == ("sufficient" if level >= 5 else "insufficient")
    assert d["evidence_level_wording"] == st.EVIDENCE_LEVELS[level]


def test_the_evidence_scale_is_the_owners():
    assert dict(st.EVIDENCE_LEVELS) == {
        6: "sufficient with a verdict", 5: "use what is available with a minimum missed (exploratory)",
        4: "inference invalid: coefficient only", 3: "below the minimums under the fixed option",
        2: "coefficient cannot be fitted", 1: "no dataset frozen"}
    assert sorted(st.STATE_LEVELS.values()) == [1, 2, 3, 4, 5, 6]


def test_the_wording_is_scoped_to_the_sources_searched():
    """CLAUDE.md rule 13."""
    for text in (*st.VERDICT_WORDING.values(), *st.OUTCOME_WORDING.values()):
        assert text.endswith("in the sources searched")
    assert st.VERDICT_WORDING["supported"] == "supported under the stated model, in the sources searched"
    assert st.BELOW_MINIMUMS_LABEL == "data found; not enough to test"
    assert st.POWER_LABEL == "estimated power under the stated assumptions"


def test_the_level_never_feeds_back_into_the_outcome_or_verdict(monkeypatch):
    """Whatever the level function returns, the outcome and verdict stay the same."""
    plan = g.plan("use_available")
    for pooled in (None, _pooled(), _pooled(met=False), _pooled(c2=False, met=False), _pooled(p=0.5)):
        before = st.decision(pooled, plan, "f")
        monkeypatch.setattr(st, "evidence_level", lambda state: 1)
        after = st.decision(pooled, plan, "f")
        monkeypatch.undo()
        assert {k: after[k] for k in ("outcome", "verdict", "exploratory", "state")} == \
            {k: before[k] for k in ("outcome", "verdict", "exploratory", "state")}


# --- the plan's calibration part --------------------------------------------------------------

def test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting():
    cal = default_plan(1)["calibration"]
    assert cal == {"methods": ["fixed", "estimated"], "n_simulations": profile.CALIBRATION_SIMULATIONS,
                   "scatter": profile.CALIBRATION_SCATTER_MPA, "shift": profile.CALIBRATION_SHIFT_MPA,
                   "estimation": profile.CALIBRATION_ESTIMATION, "smallest_effect": profile.SMALLEST_EFFECT}
    assert (cal["n_simulations"], cal["scatter"], cal["shift"], cal["smallest_effect"]) == (2000, 60.0, 40.0, 150.0)
    validate(default_plan(1))


@pytest.mark.parametrize("change", [
    {"methods": ["fixed"]}, {"methods": ["estimated", "fixed"]}, {"n_simulations": 0}, {"scatter": 0.0},
    {"shift": -1.0}, {"smallest_effect": 0.0}, {"estimation": "reml"}, {"chosen_later": 1},
])
def test_an_invalid_calibration_part_is_refused_at_the_lock(change):
    plan = default_plan(1)
    plan["calibration"] = {**plan["calibration"], **change}
    with pytest.raises(PlanError):
        validate(plan)
    del plan["calibration"]
    with pytest.raises(PlanError):
        validate(plan)


def test_statistics_code_imports_nothing_that_decides_inclusion():
    """Statistics never decides inclusion: the statistics, calibration and analysis modules import
    no inclusion, checks, extraction or checkpoint code, and the analysis stage writes no decision
    or set (only results and stage results)."""
    for name in ("statistics.py", "calibration.py", "analysis.py"):
        tree = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
        imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names} | \
                   {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert not imported & {"inclusion", "checks", "extract", "checkpoints", "hypocurate.pipeline.inclusion",
                               "hypocurate.pipeline.checks", "hypocurate.pipeline.extract",
                               "hypocurate.pipeline.checkpoints"}, name
    source = (PACKAGE / "analysis.py").read_text(encoding="utf-8").upper()
    for table in ("RUN_RECORD", "ANALYSIS_SET_RECORD", "INTO ANALYSIS_SET ", "INTO RECORD", "INTO FLAG"):
        assert f"INSERT INTO {table.replace('INTO ', '')}" not in source and "UPDATE " + table not in source


def test_the_reference_numbers_are_not_in_package_code():
    """The statistics module reproduces the reference numbers independently: none of them is
    written in the package (they live in CLAUDE.md, the register and the tests)."""
    for path in PACKAGE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for number in ("424.9", "64.4", "424.1", "62.2", "1173", "1.3e-6", "1.1e-6"):
            assert number not in text, (path.name, number)
```

### `tests/test_generated_fixed_set.py`

```python
"""Step 7: the fixed set of generated datasets (PRD 13.3), run on every change, no model calls.

Software correctness (pass or fail): on each dataset the package's coefficient, uncertainty and
p-value match the independent reference implementation (`reference_stats`, statsmodels) within a
relative 1e-9; with the fixed seeds, the result state, evidence level, verdict and simulated counts
equal the stored expected values below; one alloy at two grain sizes, and a single-group source,
give a coefficient and no verdict, and "use what is available" bypasses neither check.

Tolerance, justified: both implementations compute the same closed-form quantities in double
precision (about 16 significant digits); differences come only from summation order and the linear
algebra route (observed: below 1e-13 relative). 1e-9 leaves four orders of magnitude for that and
still catches any change in the method (a different correction, df or grouping moves the numbers
by far more than 1e-9).

The simulated counts are stored, not recomputed (PRD 13.3: "with a fixed seed, the simulated
shares equal stored expected values"). They depend on numpy's PCG64 normal generator, pinned by the
lock file. Statistical calibration is a reported finding, not pass or fail: the flags below are
what the method does on these structures, not targets.
"""
from __future__ import annotations

import math

import pytest

import generator as g
import reference_stats as rs
from hypocurate.pipeline import analysis

REL = 1e-9

# (dataset, option): (state, evidence level, verdict, fixed calibration, estimated calibration, power)
# A computed calibration is (no-effect significant of 2,000, effect significant of 2,000, flag);
# otherwise the reason it is unavailable.
EXPECTED = {
    ("effect_many_papers", "fixed_minimum"): ("sufficient", 6, 'supported', (95, 1999, 'none'), (112, 2000, 'none'), 0.9995),
    ("effect_many_papers", "use_available"): ("sufficient", 6, 'supported', (95, 1999, 'none'), (112, 2000, 'none'), 0.9995),
    ("no_effect_many_papers", "fixed_minimum"): ("sufficient", 6, 'not_supported', (99, 2000, 'none'), (103, 2000, 'none'), 1.0),
    ("no_effect_many_papers", "use_available"): ("sufficient", 6, 'not_supported', (99, 2000, 'none'), (103, 2000, 'none'), 1.0),
    ("negative_effect", "fixed_minimum"): ("sufficient", 6, 'not_supported', (105, 1997, 'none'), (82, 2000, 'none'), 0.9985),
    ("negative_effect", "use_available"): ("sufficient", 6, 'not_supported', (105, 1997, 'none'), (82, 2000, 'none'), 0.9985),
    ("large_paper_shifts", "fixed_minimum"): ("sufficient", 6, 'supported', (95, 2000, 'none'), (67, 1888, 'under_confident'), 1.0),
    ("large_paper_shifts", "use_available"): ("sufficient", 6, 'supported', (95, 2000, 'none'), (67, 1888, 'under_confident'), 1.0),
    ("small_but_valid", "fixed_minimum"): ("below_minimums", 3, None, 'below_minimums', 'below_minimums', 0.48),
    ("small_but_valid", "use_available"): ("exploratory", 5, 'supported', (153, 960, 'over_confident'), (160, 1918, 'over_confident'), 0.48),
    ("single_group", "fixed_minimum"): ("below_minimums", 3, None, 'insufficient_groups', 'insufficient_groups', None),
    ("single_group", "use_available"): ("coefficient_only", 4, None, 'insufficient_groups', 'insufficient_groups', None),
    ("one_alloy_two_sizes", "fixed_minimum"): ("below_minimums", 3, None, 'insufficient_groups', 'insufficient_groups', None),
    ("one_alloy_two_sizes", "use_available"): ("coefficient_only", 4, None, 'insufficient_groups', 'insufficient_groups', None),
    ("no_alloy_with_two_sizes", "fixed_minimum"): ("below_minimums", 3, None, 'coefficient_not_fitted', 'coefficient_not_fitted', None),
    ("no_alloy_with_two_sizes", "use_available"): ("not_fitted", 2, None, 'coefficient_not_fitted', 'coefficient_not_fitted', None),
    ("papers_nested_in_alloys", "fixed_minimum"): ("sufficient", 6, 'supported', (88, 2000, 'none'), 'shift_not_estimable', 1.0),
    ("papers_nested_in_alloys", "use_available"): ("sufficient", 6, 'supported', (88, 2000, 'none'), 'shift_not_estimable', 1.0),
    ("single_size_alloys_added", "fixed_minimum"): ("sufficient", 6, 'supported', (112, 1998, 'none'), (128, 2000, 'over_confident'), 0.999),
    ("single_size_alloys_added", "use_available"): ("sufficient", 6, 'supported', (112, 1998, 'none'), (128, 2000, 'over_confident'), 0.999),
}


def close(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=REL, abs_tol=0.0)


@pytest.fixture(scope="module")
def results():
    return {(s.name, option): analysis.analyse(g.plan(option), g.frozen_data(s))
            for s in g.FIXED_SET for option in ("fixed_minimum", "use_available")}


def test_the_fixed_set_covers_every_state_and_both_options():
    assert {k for k in EXPECTED} == {(s.name, o) for s in g.FIXED_SET for o in ("fixed_minimum", "use_available")}
    assert {v[1] for v in EXPECTED.values()} == {2, 3, 4, 5, 6}  # level 1 needs a run with no freeze (DB tests)


@pytest.mark.parametrize("name", [s.name for s in g.FIXED_SET])
def test_coefficient_uncertainty_and_p_match_the_reference_implementation(results, name):
    """Software correctness: the package against statsmodels on the same data (use what is
    available, so nothing is withheld)."""
    data = g.frozen_data(g.SPECS[name])
    pooled = results[(name, "use_available")]["analyses"][0]
    ref = rs.fit(g.rows(data))
    c = pooled["counts"]
    assert (c["n_records"], c["n_alloys"], c["n_groups"], c["resid_df"]) == (ref["n"], ref["alloys"], ref["groups"],
                                                                             ref["resid_df"])
    assert close(pooled["estimate"], ref["k"]) and close(pooled["std_error"], ref["se"])
    assert close(pooled["p_value"], ref["p"])


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values(results, key):
    state, level, verdict, fixed, estimated, power = EXPECTED[key]
    out = results[key]
    pooled = out["analyses"][0]
    assert (out["decision"]["state"], out["decision"]["evidence_level"], out["decision"]["verdict"]) == (
        state, level, verdict)
    for method, expected in (("fixed", fixed), ("estimated", estimated)):
        c = pooled["calibration"][method]
        got = (c["null"]["significant"], c["effect"]["significant"], c["confidence_flag"]) \
            if c["status"] == "computed" else c["reason"]
        assert got == expected, method
    assert pooled["estimated_power"] == power


@pytest.mark.parametrize("option", ["fixed_minimum", "use_available"])
@pytest.mark.parametrize("name", ["one_alloy_two_sizes", "single_group"])
def test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option(results, name, option):
    """PRD 13.1 validity tests: a coefficient (where shown) and no verdict; "use what is available"
    does not bypass either check."""
    out = results[(name, option)]
    pooled = out["analyses"][0]
    assert out["decision"]["verdict"] is None and out["decision"]["outcome"] == "insufficient"
    assert pooled["std_error"] is None and pooled["p_value"] is None
    assert pooled["checks"] == {"coefficient_fitted": True, "inference_valid": False}
    assert (pooled["estimate"] is not None) == (option == "use_available")  # fixed: withheld (decision 1)


def test_the_generator_controls_what_it_says():
    """Generated properties are what the spec sets (alloys, grain sizes, groups, records)."""
    for spec in g.FIXED_SET:
        data = g.frozen_data(spec)
        alloys = {r["composition"]["Qa"] for r in data["records"]}
        assert len(alloys) == spec.n_alloys + spec.single_size_alloys
        assert len(data["records"]) == (spec.n_alloys * len(spec.grain_sizes) + spec.single_size_alloys) * spec.repeats
        assert len({r["paper"] for r in data["records"]}) <= spec.n_groups
        assert g.frozen_data(spec) == data  # deterministic for its seed
    one = g.frozen_data(g.SPECS["single_group"])
    assert len({r["paper"] for r in one["records"]}) == 1
```

### `tests/test_calibration.py`

```python
"""Step 7: per-run calibration, reported both ways (PRD 5.10 as amended by the owner, 2026-10-05;
register 'calibration_both_ways', 'calibration_noise_levels'). A flag, never a gate.

Software correctness here means: the vectorized simulation runs the same test as the reference
implementation on the same generated outcomes; the exact interval is Clopper-Pearson; method III
matches an independent computation; the seed is fixed by the freeze, the analysis and the method;
and nothing in the calibration can change the outcome or the verdict.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

import generator as g
import reference_stats as rs
from hypocurate.pipeline import analysis
from hypocurate.pipeline import calibration as cal
from hypocurate.pipeline import statistics as st


def design_of(name):
    data = g.frozen_data(g.SPECS[name])
    obs = analysis.observations(data["records"], g.plan(), "primary")
    return data, st.design(obs, "inverse_square_root")


def test_the_simulation_runs_the_locked_test_exactly_as_the_reference_implementation():
    """The same generated outcomes (seeded draws) through the vectorized test and through one
    statsmodels fit per simulation: the same number of significant results, in both worlds."""
    _, d = design_of("large_paper_shifts")
    rng = np.random.default_rng(2026)
    for k_true in (0.0, 150.0):
        outcomes = k_true * d.x[None, :] + rng.normal(0, 40, (300, d.n_groups))[:, d.group] + rng.normal(0, 60, (300, d.n))
        assert cal.significant_count(d, outcomes, 0.05) == rs.significant_count(d.x, d.alloy, d.group, outcomes, 0.05)


def test_each_world_draws_shifts_then_errors_from_one_seeded_generator():
    """The documented draw order, reproduced by hand: no-effect world first."""
    _, d = design_of("effect_many_papers")
    out = cal.simulate(d, 60.0, 40.0, 150.0, 250, 0.05, 99)
    rng = np.random.default_rng(99)
    counts = []
    for k_true in (0.0, 150.0):
        shifts = rng.normal(0, 40.0, (250, d.n_groups))
        errors = rng.normal(0, 60.0, (250, d.n))
        counts.append(cal.significant_count(d, k_true * d.x[None, :] + shifts[:, d.group] + errors, 0.05))
    assert (out["null"]["significant"], out["effect"]["significant"]) == tuple(counts)
    assert cal.simulate(d, 60.0, 40.0, 150.0, 250, 0.05, 99) == out  # deterministic for its seed


@pytest.mark.parametrize("hits, n", [(0, 2000), (1, 2000), (144, 2000), (1999, 2000), (2000, 2000), (3, 7)])
def test_the_interval_is_the_exact_binomial_interval(hits, n):
    low, high = cal.exact_interval(hits, n)
    ref = stats.binomtest(hits, n).proportion_ci(confidence_level=0.95, method="exact")
    assert math.isclose(low, ref.low, abs_tol=1e-12) and math.isclose(high, ref.high, abs_tol=1e-12)
    assert low <= hits / n <= high


@pytest.mark.parametrize("low, high, flag", [(0.061, 0.084, "over_confident"), (0.040, 0.061, "none"),
                                             (0.020, 0.049, "under_confident"), (0.05, 0.06, "none"),
                                             (0.04, 0.05, "none")])
def test_the_flag_is_raised_only_when_the_interval_excludes_alpha(low, high, flag):
    assert cal.confidence_flag(low, high, 0.05) == flag


def test_the_seed_is_fixed_by_the_freeze_the_analysis_and_the_method():
    a = cal.seed("f" * 64, "pooled", "fixed")
    assert a == cal.seed("f" * 64, "pooled", "fixed") and 0 <= a < 2 ** 63
    assert len({a, cal.seed("f" * 64, "pooled", "estimated"), cal.seed("f" * 64, "per_source:mpea", "fixed"),
                cal.seed("e" * 64, "pooled", "fixed")}) == 4


# --- method III -----------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["effect_many_papers", "large_paper_shifts", "single_size_alloys_added"])
def test_method_iii_matches_an_independent_computation(name):
    data, d = design_of(name)
    mine = cal.henderson_iii(d)
    ref = rs.henderson_iii(g.rows(data))
    for key in ("rss_reduced", "rss_full", "trace", "scatter_squared", "shift_squared_untruncated"):
        assert math.isclose(mine[key], ref[key], rel_tol=1e-9), key
    assert (mine["rank_reduced"], mine["rank_full"]) == (ref["rank_reduced"], ref["rank_full"])


def test_method_iii_recovers_known_noise_levels_on_a_large_generated_dataset():
    """60 alloys, 60 papers, 1,440 records, σe = 40, σu = 30 (seeded, so deterministic). Tolerance:
    about four standard errors of each estimate at this size (σe² from ~1,300 residual degrees of
    freedom: ±16%; σu² from 60 groups: ±75%), on the standard deviations: ±8% and ±40%."""
    spec = g.Spec("large", 4242, n_alloys=60, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=6, n_groups=60,
                  k=200.0, scatter=40.0, shift=30.0)
    data = g.frozen_data(spec)
    d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
    est = cal.henderson_iii(d)
    assert est["reason"] is None and not est["shift_truncated_at_zero"]
    assert abs(est["scatter"] - 40.0) / 40.0 < 0.08 and abs(est["shift"] - 30.0) / 30.0 < 0.40


def test_a_negative_shift_estimate_is_set_to_zero_and_the_result_says_so():
    """Owner's addition (2026-10-05): the stored result records the truncation and the value before it."""
    spec = g.Spec("no_shift", 77, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0), repeats=2, n_groups=12,
                  k=200.0, scatter=40.0, shift=0.0)
    found = None
    for seed in range(77, 120):  # the first seed whose estimate is negative (no true shift: about half are)
        data = g.frozen_data(g.Spec(**{**spec.__dict__, "seed": seed}))
        d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
        if cal.henderson_iii(d)["shift_squared_untruncated"] < 0:
            found = d
            break
    assert found is not None
    c = cal.calibrate(found, g.plan()["calibration"], 0.05, "f" * 64, "pooled", "estimated")
    assert c["status"] == "computed"
    assert c["assumptions"]["shift_truncated_at_zero"] is True
    assert c["assumptions"]["shift_squared_untruncated"] < 0 and c["assumptions"]["shift"] == 0.0


def test_a_shift_explained_by_the_alloys_cannot_be_estimated():
    """Every paper studies its own alloys: the per-paper shift is absorbed by the alloy intercepts,
    the trace is zero, and the estimated method is unavailable with its reason; the fixed method is
    still computed."""
    data, d = design_of("papers_nested_in_alloys")
    assert cal.henderson_iii(d)["reason"] == "shift_not_estimable"
    out = analysis.analyse(g.plan(n_simulations=100), data)["analyses"][0]["calibration"]
    assert out["estimated"] == {"status": "unavailable", "reason": "shift_not_estimable",
                                "estimation": cal.henderson_iii(d)}
    assert out["fixed"]["status"] == "computed"


def test_the_scatter_cannot_be_estimated_without_residual_freedom_in_the_full_model():
    """N <= rank of the model with group intercepts."""
    rows = [st.Observation(f"r{i}", a, p, d, y) for i, (a, p, d, y) in enumerate(
        [("A", "p1", 1.0, 500.0), ("A", "p2", 4.0, 420.0), ("B", "p1", 1.0, 700.0), ("B", "p3", 4.0, 610.0)])]
    d = st.design(rows, "inverse_square_root")
    assert d.inference_valid
    assert cal.henderson_iii(d)["reason"] == "scatter_not_estimable"


def test_the_estimated_method_uses_the_estimates_and_the_fixed_method_the_plan():
    data, d = design_of("effect_many_papers")
    plan = g.plan(n_simulations=100)
    fixed = cal.calibrate(d, plan["calibration"], 0.05, "f" * 64, "pooled", "fixed")
    est = cal.calibrate(d, plan["calibration"], 0.05, "f" * 64, "pooled", "estimated")
    h = cal.henderson_iii(d)
    assert (fixed["assumptions"]["scatter"], fixed["assumptions"]["shift"]) == (60.0, 40.0)
    assert (est["assumptions"]["scatter"], est["assumptions"]["shift"]) == (h["scatter"], h["shift"])
    assert est["assumptions"]["source"] == "estimated from the frozen records"
    assert fixed["seed"] != est["seed"]
    assert fixed["assumptions"]["smallest_effect"] == est["assumptions"]["smallest_effect"] == 150.0


def test_calibration_never_changes_the_outcome_or_the_verdict(monkeypatch):
    """A flag, never a gate: with every calibration forced to 'over-confident', or failing to
    estimate, the decision and every number from the real outcomes are unchanged."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    plan = g.plan(n_simulations=100)
    before = analysis.analyse(plan, data)

    def forced(*args, **kwargs):
        return {"status": "computed", "reason": None, "assumptions": {}, "seed": 1, "n_simulations": 1,
                "null": {"significant": 1, "share": 1.0, "ci_low": 0.9, "ci_high": 1.0},
                "effect": {"significant": 0, "share": 0.0, "ci_low": 0.0, "ci_high": 0.1},
                "confidence_flag": "over_confident", "flag_wording": "x"}

    monkeypatch.setattr(cal, "calibrate", forced)
    after = analysis.analyse(plan, data)
    assert after["decision"] == before["decision"]
    keep = ("estimate", "std_error", "p_value", "significant", "counts", "checks", "minimums", "label")
    assert [{k: e[k] for k in keep} for e in after["analyses"]] == [{k: e[k] for k in keep} for e in before["analyses"]]


def test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome():
    """Decision 5: shown even below the minimums; the outcomes may be replaced by anything."""
    data = g.frozen_data(g.SPECS["small_but_valid"])
    below = analysis.analyse(g.plan("fixed_minimum", n_simulations=400), data)["analyses"][0]
    shown = analysis.analyse(g.plan("use_available", n_simulations=400), data)["analyses"][0]
    assert below["withheld"] and below["estimate"] is None
    assert below["estimated_power"] == shown["estimated_power"] == shown["calibration"]["fixed"]["effect"]["share"]
    assert below["power_label"] == "estimated power under the stated assumptions"
    scrambled = {**data, "records": [{**r, "outcome": 1.0} for r in data["records"]]}
    assert analysis.analyse(g.plan("fixed_minimum", n_simulations=400), scrambled)["analyses"][0][
        "estimated_power"] == below["estimated_power"]
```

### `tests/test_analysis_stage.py`

```python
"""Step 7: the analysis stage through the database: what is stored in each result state, what is
withheld, the test-run label, the refusals, and the rules the database itself enforces on results
(migration 0004).

Result states (owner, 2026-10-05): sufficient with a verdict (6); exploratory (5); coefficient only
(4); below the minimums under the fixed option (3, withheld run-wide: counts and records only);
coefficient cannot be fitted (2, pure tests only: eligibility rule 8 leaves the primary set no
alloy with fewer than two grain sizes); no dataset frozen (1).
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, completion, results
from hypocurate.pipeline.writes import TEST_RUN_LABEL, Refused
from pipeline_fixtures import frozen_run
from stats_world import audit_codes, rows_of, run_on, small_rows, val

LABEL = "test run: includes constructed data"


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


@pytest.fixture(scope="module")
def reference(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        yield engine, rid, analysis.run_statistics(engine, rid)


def result_rows(engine, rid):
    return rows_of(engine, "SELECT ar.*, a.key AS set_key, s.key AS source_key FROM analysis_result ar "
                           "JOIN analysis_set a ON a.id = ar.analysis_set_id LEFT JOIN source s ON s.id = ar.source_id "
                           "WHERE ar.run_id = :r ORDER BY ar.id", r=rid)


def calibration_rows(engine, rid):
    return rows_of(engine, "SELECT * FROM calibration_result WHERE run_id = :r ORDER BY id", r=rid)


# --- sufficient with a verdict (the reference run) ------------------------------------------------

def test_every_analysis_is_stored_with_both_calibrations(reference):
    engine, rid, out = reference
    rows = result_rows(engine, rid)
    assert [(r.scope, r.set_key, r.source_key) for r in rows] == [
        ("pooled", "primary", None), ("per_source", "primary", "mpea"), ("per_source", "primary", "tamu_fcc")] + [
        ("sensitivity", k, None) for k in ("no_exclusions", "tension_and_compression", "six_batches_as_groups",
                                           "same_alloy_1_at_pct", "source_only_assignments",
                                           "scope_not_confirmed_included", "possible_duplicates_separate",
                                           "conflicts_survivor_value")]
    assert all(r.withheld is False and r.test_run_label is None and r.n_records_not_used == 0 for r in rows)
    cal = calibration_rows(engine, rid)
    assert len(cal) == 2 * len(rows)
    assert {(c.analysis_result_id, c.method) for c in cal} == {(r.id, m) for r in rows for m in ("fixed", "estimated")}
    pooled = rows[0]
    assert (pooled.n_records, pooled.n_alloys, pooled.n_groups, pooled.resid_df, pooled.minimums_met) == (
        97, 22, 20, 74, True)
    assert pooled.label is None and pooled.estimated_power is not None
    tamu = rows[2]
    assert (tamu.check1_passed, tamu.check2_passed, tamu.std_error, tamu.p_value, tamu.label) == (
        True, False, None, None, "not_enough_data")
    assert [(c.status, c.reason) for c in cal if c.analysis_result_id == tamu.id] == [
        ("unavailable", "insufficient_groups")] * 2
    assert rows[1].label == "agrees"


def test_the_record_of_statistical_significance_and_the_decision(reference):
    """PRD 5.9: estimate and uncertainty, test, p-value and threshold, counts, the two checks, df
    and groups, the sufficiency option and whether it was met, estimated power, per-source and
    sensitivity results."""
    engine, rid, out = reference
    stored = analysis.stored_record(engine, rid)
    assert stored == out
    assert stored["decision"] == {
        "freeze_fingerprint": val(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid),
        "state": "sufficient", "outcome": "sufficient", "outcome_wording": "sufficient in the sources searched",
        "verdict": "supported", "verdict_wording": "supported under the stated model, in the sources searched",
        "exploratory": False, "evidence_level": 6, "evidence_level_wording": "sufficient with a verdict",
        "label": None}
    pooled = stored["analyses"][0]
    for key in ("estimate", "std_error", "t", "df", "p_value", "alpha", "counts", "checks", "minimums",
                "minimums_met", "estimated_power", "power_label", "calibration"):
        assert pooled[key] is not None, key
    assert pooled["df"] == 19 and stored["sufficiency_option"] == "fixed_minimum" and stored["test_run_label"] is None


def test_the_run_is_not_completed_by_the_analysis_stage(reference):
    engine, rid, _ = reference
    assert rows_of(engine, "SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("running", None, None, None)]


def test_a_second_analysis_is_refused_and_logged(reference):
    engine, rid, _ = reference
    with pytest.raises(Refused) as refused:
        analysis.run_statistics(engine, rid)
    assert refused.value.code == "already_done"
    assert "already_done" in audit_codes(engine, rid, "run_statistics")


def test_no_analysis_before_the_freeze(engine):
    pw.registered(engine, ("mpea",))
    rid = pw.locked_run(engine, sources=("mpea",))
    with pytest.raises(Refused) as refused:
        analysis.run_statistics(engine, rid)
    assert refused.value.code == "stage_mismatch"
    assert audit_codes(engine, rid, "run_statistics") == ["stage_mismatch"]
    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0


# --- below the minimums under the fixed option: withheld run-wide --------------------------------

def test_below_the_minimums_every_analysis_holds_counts_and_records_only(engine):
    """Decision 1: 3 alloys at two grain sizes, 3 papers: inference is valid, but 6 records < 30."""
    rid = run_on(engine, small_rows(3, papers=3))
    out = analysis.run_statistics(engine, rid)
    assert out["withheld"] and out["decision"]["state"] == "below_minimums"
    assert out["decision"]["evidence_level"] == 3 and out["decision"]["label"] == "data found; not enough to test"
    assert out["decision"]["verdict"] is None and out["decision"]["outcome"] == "insufficient"
    for e in out["analyses"]:
        assert e["withheld"] and (e["estimate"], e["std_error"], e["t"], e["p_value"], e["significant"]) == (
            None, None, None, None, None)
        assert e["label_text"] == "data found; not enough to test"
        assert set(e["minimums"]) == {"records", "alloys", "groups", "resid_df"}
        assert len(e["records_found"]) == e["counts"]["n_records_in_set"]
        assert all(v["status"] == "unavailable" for v in e["calibration"].values())
    pooled = out["analyses"][0]
    assert pooled["minimums"]["records"] == {"count": 6, "minimum": 30, "met": False}
    assert pooled["checks"]["inference_valid"] and pooled["estimated_power"] is not None  # no outcome used
    for r in result_rows(engine, rid):
        assert r.withheld and r.estimate is None and r.std_error is None and r.p_value is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "below_minimums")}
    # Nothing computed from outcomes anywhere in what is stored: the real outcomes can be anything.
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]


def test_withheld_results_do_not_depend_on_the_outcome_values():
    """Below the minimums nothing computed from outcomes is kept: replacing every outcome value
    changes nothing in what would be stored (the power and counts come from structure only)."""
    import generator as g
    data = g.frozen_data(g.SPECS["small_but_valid"])
    plan = g.plan("fixed_minimum", n_simulations=300)
    first = analysis.analyse(plan, data)
    for value in (-5000.0, 0.0, 12345.6):
        other = {**data, "records": [{**r, "outcome": value + i} for i, r in enumerate(data["records"])]}
        assert analysis.analyse(plan, other) == first
    assert first["withheld"]


def test_use_what_is_available_gives_an_exploratory_verdict_on_the_same_data(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    out = analysis.run_statistics(engine, rid)
    assert (out["decision"]["state"], out["decision"]["evidence_level"], out["decision"]["exploratory"]) == (
        "exploratory", 5, True)
    assert out["decision"]["verdict"] in ("supported", "not_supported") and out["decision"]["label"] == "exploratory"
    pooled = result_rows(engine, rid)[0]
    assert not pooled.withheld and not pooled.minimums_met and pooled.p_value is not None
    assert {c.method: c.status for c in calibration_rows(engine, rid)}["fixed"] == "computed"
    completion.copy_decision(engine, rid)
    assert rows_of(engine, "SELECT outcome, exploratory, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("sufficient", True, 5)]


def test_use_what_is_available_with_one_group_gives_the_coefficient_only(engine):
    rid = run_on(engine, small_rows(3, papers=1), option="use_available")
    out = analysis.run_statistics(engine, rid)
    pooled = out["analyses"][0]
    assert (out["decision"]["state"], out["decision"]["evidence_level"]) == ("coefficient_only", 4)
    assert pooled["estimate"] is not None and pooled["std_error"] is None and pooled["p_value"] is None
    assert out["decision"]["verdict"] is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}


def test_the_fixed_option_with_one_group_withholds_even_the_coefficient(engine):
    """Decision 1: below the minimums, the coefficient-only rule does not apply."""
    rid = run_on(engine, small_rows(3, papers=1))
    out = analysis.run_statistics(engine, rid)
    assert out["decision"]["evidence_level"] == 3 and out["analyses"][0]["estimate"] is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}


# --- no dataset frozen ------------------------------------------------------------------------------

def test_a_run_with_no_dataset_frozen_gets_level_one_and_its_gap_facts(engine):
    """Every record out of scope (compression) or without a grain size: no dataset frozen."""
    rows = [pw.mpea_row("CoCrFeNi", 1.0, 400.0, test="C"), pw.mpea_row("CoCrFeNi", 9.0, 300.0, test="C"),
            {**pw.mpea_row("CoCrNi", 1.0, 500.0), "PROPERTY: grain size ($\\mu$m)": ""}]
    rid = run_on(engine, rows)
    out = analysis.run_statistics(engine, rid)
    assert out["decision"] == {**out["decision"], "state": "no_dataset_frozen", "evidence_level": 1,
                               "outcome": "insufficient", "verdict": None, "freeze_fingerprint": None}
    assert out["analyses"] == []
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert facts["records_lacking_fields"]["mpea"]["grain_size"] == 1
    assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]
    assert facts["minimums"]["records"] == {"count": 0, "minimum": 30, "met": False}
    assert facts["eligibility_rules"] == {"missing_value": 1, "out_of_scope": 2}
    assert facts["sources"] == [{"source": "mpea", "search_status": "searched", "nothing_found": None}]
    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
    completion.copy_decision(engine, rid)
    assert rows_of(engine, "SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("completed", "insufficient", None, 1)]


def test_the_gap_facts_hold_no_text_and_no_outcome_value(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    analysis.run_statistics(engine, rid)
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert set(facts) == {"minimums", "minimums_missed", "records_lacking_fields", "eligibility_rules", "sources",
                          "test_run_label"}
    yields = {r[0] for r in rows_of(engine, "SELECT (harmonized->'yield_strength'->>'value') FROM record "
                                            "WHERE extraction_run_id = :r", r=rid)}
    flat = repr(facts)
    assert not any(y in flat for y in yields)


# --- marked test runs ---------------------------------------------------------------------------------

def test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates(engine):
    pw.registered(engine, ("mpea", "tamu_fcc", "controlled_duplicates"))
    marked = pw.through_freeze(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    real = pw.through_freeze(engine, sources=("mpea", "tamu_fcc"))
    out = analysis.run_statistics(engine, marked)
    analysis.run_statistics(engine, real)
    assert TEST_RUN_LABEL == LABEL
    assert out["test_run_label"] == LABEL and out["decision"]["evidence_level"] == 6  # keeps its level
    # The extract's two records without a paper enter only 'possible_duplicates_separate': that descriptive
    # analysis is not analysed (no group invented), and nothing is stored for it; the others are.
    assert out["not_analysed"] == [{"analysis": "sensitivity:possible_duplicates_separate", "scope": "sensitivity",
                                    "set": "possible_duplicates_separate", "source": None,
                                    "reason": "records_without_group", "n_records_without_group": 2,
                                    "n_records_in_set": out["not_analysed"][0]["n_records_in_set"]}]
    assert "possible_duplicates_separate" not in {r.set_key for r in result_rows(engine, marked)}
    assert {r.test_run_label for r in result_rows(engine, marked)} == {LABEL}
    assert {c.test_run_label for c in calibration_rows(engine, marked)} == {LABEL}
    assert rows_of(engine, "SELECT output->>'test_run_label' FROM stage_result WHERE run_id = :r "
                           "AND stage IN ('statistics', 'gap_facts')", r=marked) == [(LABEL,), (LABEL,)]
    assert {r.test_run_label for r in result_rows(engine, real)} == {None}
    for rid in (marked, real):
        completion.copy_decision(engine, rid)
    with engine.connect() as conn:
        assert [r.id for r in results.real_runs(conn)] == [real]
        assert results.real_outcome_counts(conn) == {"sufficient": 1}
        assert {r.run_id for r in results.real_analysis_results(conn)} == {real}
    assert val(engine, "SELECT evidence_level FROM run WHERE id = :r", r=marked) == 6


def test_a_marked_run_with_no_dataset_frozen_is_labelled_too(engine):
    rows = [pw.mpea_row("CoCrFeNi", 1.0, 400.0, test="C")]
    rid = run_on(engine, rows, marked=True)
    assert rows_of(engine, "SELECT test_run_label FROM calibration_result WHERE run_id = :r", r=rid) == [(LABEL,)]
    assert analysis.run_statistics(engine, rid)["test_run_label"] == LABEL


# --- what the database refuses (migration 0004) -------------------------------------------------------

def _insert_result(engine, rid, **over):
    sets = dict(rows_of(engine, "SELECT key, id FROM analysis_set WHERE run_id = :r", r=rid))
    n = val(engine, "SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sets["primary"])
    cols = dict(run_id=rid, scope="pooled", analysis_set_id=sets["primary"], n_records=n, n_alloys=3, n_groups=3,
                resid_df=n - 4, check1_passed=True, check2_passed=True, minimums_met=False, estimate=None,
                std_error=None, p_value=None)
    cols.update(over)
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO analysis_result ({', '.join(cols)}) VALUES "
                          f"({', '.join(':' + c for c in cols)})"), cols)


def test_the_database_computes_withheld_and_refuses_a_number_in_a_withheld_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # fixed option, 6 records: the pooled result is withheld
    with pytest.raises(IntegrityError, match="withheld must equal"):
        _insert_result(engine, rid, withheld=False)
    with pytest.raises(IntegrityError, match="ck_analysis_result_estimate_iff_check1"):
        _insert_result(engine, rid, estimate=300.0)
    with pytest.raises(IntegrityError, match="ck_analysis_result_std_error_iff_check2"):
        _insert_result(engine, rid, std_error=10.0)
    _insert_result(engine, rid)  # withheld filled in by the database
    assert val(engine, "SELECT withheld FROM analysis_result WHERE run_id = :r", r=rid) is True


def test_the_database_refuses_a_per_source_result_before_the_pooled_one(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    src = val(engine, "SELECT id FROM source WHERE key = 'mpea'")
    with pytest.raises(IntegrityError, match="pooled result is written before"):
        _insert_result(engine, rid, scope="per_source", source_id=src)


def test_the_database_refuses_a_label_on_a_pooled_result_and_power_without_inference(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_label_per_source_only"):
        _insert_result(engine, rid, label="agrees", estimate=1.0, std_error=1.0, p_value=0.1)
    with pytest.raises(IntegrityError, match="ck_analysis_result_power_needs_check2"):
        _insert_result(engine, rid, n_groups=1, check2_passed=False, estimate=1.0, estimated_power=0.5)
    with pytest.raises(IntegrityError, match="test-run label exactly when"):
        _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, test_run_label=LABEL)


def test_the_database_refuses_records_not_accounted_for(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="n_records must equal"):
        _insert_result(engine, rid, n_records=5, resid_df=1, estimate=1.0, std_error=1.0, p_value=0.1)
    _insert_result(engine, rid, n_records=4, n_records_not_used=2, n_alloys=2, n_groups=2, resid_df=1,
                   estimate=1.0, std_error=1.0, p_value=0.1)


def test_the_database_refuses_calibration_that_does_not_match_the_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # withheld
    analysis.run_statistics(engine, rid)
    pooled = val(engine, "SELECT id FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
    numbers = ("'{\"scatter\": 60}', 2000, 7, 0.05, 0.04, 0.06, 1.0, 0.99, 1.0, 'none'")
    insert = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, "
              "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, "
              "confidence_flag) VALUES (:r, :a, :m, :st, :re, {n})")
    none = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"
    for method, status, reason, nums, match in (
            ("fixed", "computed", None, numbers, "computed exactly when"),
            ("fixed", "unavailable", "insufficient_groups", none, "must match the validity checks"),
            (None, "unavailable", "below_minimums", none, "ck_calibration_result_method_iff_analysis")):
        with pytest.raises(IntegrityError, match=match):
            with engine.begin() as conn:
                conn.execute(text(insert.format(n=nums)), dict(r=rid, a=pooled, m=method, st=status, re=reason))
    with pytest.raises(IntegrityError, match="uq_calibration_result_scope"):
        with engine.begin() as conn:
            conn.execute(text(insert.format(n=none)), dict(r=rid, a=pooled, m="fixed", st="unavailable",
                                                          re="below_minimums"))


def test_the_database_requires_the_fixed_method_where_inference_is_valid(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1)
    pooled = val(engine, "SELECT id FROM analysis_result WHERE run_id = :r", r=rid)
    insert = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason) "
              "VALUES (:r, :a, :m, 'unavailable', :re)")
    with pytest.raises(IntegrityError, match="computed exactly when"):
        with engine.begin() as conn:
            conn.execute(text(insert), dict(r=rid, a=pooled, m="fixed", re="shift_not_estimable"))
    with engine.begin() as conn:  # the estimated method may name why the noise cannot be estimated
        conn.execute(text(insert), dict(r=rid, a=pooled, m="estimated", re="shift_not_estimable"))


@pytest.mark.parametrize("outcome, verdict, exploratory, level, ok", [
    ("insufficient", None, False, 1, True), ("insufficient", None, False, 4, True),
    ("partly_sufficient", None, False, 3, True), ("insufficient", None, False, 6, False),
    ("insufficient", None, False, 5, False), ("insufficient", None, False, 7, False),
    ("insufficient", None, False, 0, False),
])
def test_the_evidence_level_must_agree_with_the_outcome(engine, outcome, verdict, exploratory, level, ok):
    pw.registered(engine, ("mpea",))
    rid = pw.dispatched_run(engine, sources=("mpea",))
    update = ("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
              "exploratory = :x, evidence_level = :e WHERE id = :r")
    params = dict(o=outcome, v=verdict, x=exploratory, e=level, r=rid)
    if ok:
        with engine.begin() as conn:
            conn.execute(text(update), params)
    else:
        with pytest.raises(IntegrityError, match="ck_run_evidence_level"):
            with engine.begin() as conn:
                conn.execute(text(update), params)
```

### `tests/test_completion.py`

```python
"""Step 7: the function that copies the stored decision onto the run only copies (owner, 2026-10-05).

It refuses, and logs the refusal, when the stored decision is missing or belongs to a different
freeze fingerprint; it computes nothing; the database checks the copy again.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, completion
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.writes import Refused, code_stage
from stats_world import audit_codes, rows_of, run_on, small_rows, val


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def run_row(engine, rid):
    return rows_of(engine, "SELECT status, outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r",
                   r=rid)[0]


def test_the_decision_is_copied_unchanged(engine):
    rid = run_on(engine, small_rows(6, sizes=(1.0, 4.0, 16.0), papers=12, repeats=2), mins=(30, 5, 10, 10))
    stored = analysis.run_statistics(engine, rid)["decision"]
    assert stored["state"] == "sufficient"
    copied = completion.copy_decision(engine, rid)
    assert copied == stored
    assert tuple(run_row(engine, rid)) == ("completed", stored["outcome"], stored["verdict"], stored["exploratory"],
                                           stored["evidence_level"])


def test_it_refuses_a_missing_decision_and_logs_it(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_missing"
    assert audit_codes(engine, rid, "copy_decision") == ["decision_missing"]
    assert run_row(engine, rid).status == "running"


def test_it_refuses_a_decision_of_another_freeze_and_logs_it(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    decision = st.decision(None, {"sufficiency": {"option": "fixed_minimum"}}, "0" * 64)
    with engine.begin() as conn:
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        code_stage(conn, rid, "statistics", {}, {"decision": decision})
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_not_current"
    assert audit_codes(engine, rid, "copy_decision") == ["decision_not_current"]
    assert run_row(engine, rid).status == "running"


def test_a_run_with_a_freeze_refuses_a_decision_without_one(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    with engine.begin() as conn:
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        code_stage(conn, rid, "statistics", {}, {"decision": st.decision(None, {"sufficiency": {
            "option": "fixed_minimum"}}, None)})
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_not_current"


def test_it_copies_what_is_stored_and_never_recomputes(engine, monkeypatch):
    """A stored decision that differs from what the statistics would give (here: 'not supported'
    on data that support the claim) is copied as stored. The copy reads only the stored decision."""
    rid = run_on(engine, small_rows(6, sizes=(1.0, 4.0, 16.0), papers=12, repeats=2))
    real = st.decision

    def altered(pooled, plan, fp):
        return {**real(pooled, plan, fp), "verdict": "not_supported"}

    monkeypatch.setattr(st, "decision", altered)
    stored = analysis.run_statistics(engine, rid)
    monkeypatch.undo()
    assert stored["analyses"][0]["significant"] is True and stored["decision"]["verdict"] == "not_supported"
    completion.copy_decision(engine, rid)
    assert run_row(engine, rid).verdict == "not_supported"


def test_it_refuses_before_the_analysis_stage_and_after_completion(engine):
    pw.registered(engine, ("mpea",))
    rid = pw.locked_run(engine, sources=("mpea",))
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "stage_mismatch"
    done = run_on(engine, small_rows(3, papers=3), register=False)
    analysis.run_statistics(engine, done)
    completion.copy_decision(engine, done)
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, done)
    assert refused.value.code == "stage_mismatch"


def test_the_database_checks_the_copy_again(engine, monkeypatch):
    """A stored decision claiming 'sufficient' for a withheld run is refused by the database
    (hc_run_update: under the fixed option, a sufficient outcome needs the minimums met)."""
    rid = run_on(engine, small_rows(3, papers=3))
    real = st.decision

    def claims_sufficient(pooled, plan, fp):
        return {**real(pooled, plan, fp), "outcome": "sufficient", "verdict": "supported", "evidence_level": 6}

    monkeypatch.setattr(st, "decision", claims_sufficient)
    analysis.run_statistics(engine, rid)
    monkeypatch.undo()
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "rejected_by_database"
    assert run_row(engine, rid).status == "running"
```

### `tests/test_access_statistics.py`

```python
"""Step 7: the code roles Statistics and the gap facts read through access objects (PRD 4; owner,
2026-10-05; a safeguard change, reviewed by a second model).

**Statistics** binds only at the analysis stage (a dataset frozen, the run running) and receives
exactly the locked plan and `frozen_analysis_data`: the frozen sets and, for the records in them
only, what the model needs. It sees outcome values (it must: it fits them), but never those of
records outside the frozen sets, never values as reported, never another run's data.

**The gap facts** bind at the analysis stage and when the run closed without a freeze, and receive
no outcome value (the projected-data search with planted values, as for the Planner and Critic).

**Not claimed:** anything beyond the threat model (CLAUDE.md): the access layer guards against our
own code leaking data; Statistics is trusted code, not a sandboxed reader.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import access_world as aw
from hypocurate.access import AccessDenied, role_input
from hypocurate.access.allowlist import ALLOWED, CODE_ALLOWED, ROLES, allowed
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from pipeline_fixtures import frozen_run
from test_access_projected import leaks

STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")
RECORD_KEYS = {"id", "source", "version_fingerprint", "origin", "item_index", "composition", "paper", "batch",
               "grain_size", "outcome"}


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def audit(engine, run_id, role):
    with engine.connect() as conn:
        return conn.execute(text("SELECT function, allowed, detail FROM audit_log WHERE run_id = :r AND role = :o "
                                 "ORDER BY id"), dict(r=run_id, o=role)).all()


def test_the_lists_are_the_owners_decision():
    assert {s: set(v) for s, v in CODE_ALLOWED["statistics"].items()} == {"analysis": {"plan", "frozen_analysis_data"}}
    assert {s: set(v) for s, v in CODE_ALLOWED["gap_facts"].items()} == {
        "analysis": {"plan", "decisions", "stored_record_counts", "coverage"},
        "closed_without_freeze": {"plan", "decisions", "stored_record_counts", "coverage"}}
    for stage in STAGES:
        if stage != "analysis":
            assert allowed("statistics", stage) == frozenset()
        for role in ROLES:  # no agent ever receives the statistics field
            assert "frozen_analysis_data" not in allowed(role, stage)
    assert not {"records_full", "flags_full", "results", "stage_outputs"} & set().union(*CODE_ALLOWED["gap_facts"].values())


@pytest.mark.parametrize("stage", ["queued", "before_lock", "curation", "closed_without_freeze", "final"])
def test_statistics_binds_at_no_other_stage(engine, stage):
    world = aw.build(engine, stage)
    with pytest.raises(AccessDenied) as denied:
        bind_code(engine, world.run, "statistics")
    assert denied.value.code == "empty_list"
    row = audit(engine, world.run, "statistics")[-1]
    assert (row.function, row.allowed, row.detail["code"]) == ("bind", False, "empty_list")


@pytest.mark.parametrize("stage", ["queued", "before_lock", "curation", "final", "final_without_freeze"])
def test_the_gap_facts_bind_at_no_other_stage(engine, stage):
    world = aw.build(engine, stage)
    with pytest.raises(AccessDenied):
        bind_code(engine, world.run, "gap_facts")


def test_the_complete_input_of_statistics(engine):
    """Exactly the plan and the frozen data; the frozen records with exactly the named keys; the
    world's planted outcome value is there (the positive control: Statistics fits outcomes), the
    other runs' value is not; every read is logged."""
    world = aw.build(engine, "analysis")
    got = role_input(bind_code(engine, world.run, "statistics"))
    assert set(got) == {"plan", "frozen_analysis_data"}
    data = got["frozen_analysis_data"]
    assert set(data) == {"freeze_fingerprint", "outcome_field", "sets", "records"}
    assert data["outcome_field"] == "yield_strength"
    assert {r["id"] for r in data["records"]} == set(world.records) == set(data["sets"]["primary"])
    assert all(set(r) == RECORD_KEYS for r in data["records"])
    assert any(r["outcome"] == aw.PLANTED["yield_strength"] for r in data["records"])
    assert leaks(got, [aw.OTHER]) == []  # nothing from another run
    assert not any(f.startswith(f"{aw.PLANTED['ultimate_tensile_strength']}:") for f in leaks(got, aw.PLANTED.values()))
    rows = audit(engine, world.run, "statistics")
    assert [(r.function, r.allowed) for r in rows][0] == ("bind", True)
    assert sorted((r.function, r.allowed) for r in rows[1:]) == [("frozen_analysis_data", True), ("plan", True)]


def test_records_outside_the_frozen_sets_never_reach_statistics(admin, database_url, template_database):
    """On the reference run: 1,639 records stored, the frozen sets hold 103 distinct records; only
    those are returned, and no value as reported."""
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        data = bind_code(engine, rid, "statistics").get("frozen_analysis_data")
        with engine.connect() as conn:
            members = set(conn.execute(text("SELECT DISTINCT asr.record_id FROM analysis_set_record asr JOIN analysis_set a "
                                            "ON a.id = asr.analysis_set_id WHERE a.run_id = :r"), dict(r=rid)).scalars())
            stored = conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"),
                                  dict(r=rid)).scalar()
            outside = conn.execute(text("SELECT reported FROM record WHERE extraction_run_id = :r AND id <> ALL(:m)"),
                                   dict(r=rid, m=list(members))).scalars().all()
        assert {r["id"] for r in data["records"]} == members and len(members) < stored
        assert all(set(r) == RECORD_KEYS for r in data["records"])
        flat = json.dumps(data)
        assert "reported" not in flat and "harmonized" not in flat
        # Text cells as reported for records outside the sets (titles, raw cells) never appear.
        texts = {c["text"] for rep in outside for c in rep.values() if isinstance(c, dict) and isinstance(c.get("text"), str)
                 and len(c["text"]) > 25}
        assert texts and not any(t in flat for t in texts)


@pytest.mark.parametrize("stage", ["analysis", "closed_without_freeze"])
def test_the_gap_facts_receive_no_outcome_value(engine, stage):
    """The projected-data search over the gap facts' complete input finds none of the planted
    outcome values, nor the other runs' value."""
    world = aw.build(engine, stage)
    got = role_input(bind_code(engine, world.run, "gap_facts"))
    assert set(got) == {"plan", "decisions", "stored_record_counts", "coverage"}
    assert leaks(got, list(aw.PLANTED.values()) + [aw.OTHER]) == []


def test_the_reader_itself_refuses_without_a_freeze(engine):
    """A second line behind the stage list (which already allows the field only at the analysis
    stage, where a freeze exists): the reader refuses a run with no snapshot."""
    from hypocurate.access.context import AccessContext
    from hypocurate.access.fields import Refused, frozen_analysis_data
    world = aw.build(engine, "curation")
    with engine.connect() as conn, pytest.raises(Refused) as refused:
        frozen_analysis_data(conn, AccessContext(world.run, "statistics", "analysis"))
    assert refused.value.code == "not_frozen"
```

### `tests/test_reference_numbers.py`

```python
"""Step 7: the statistics module reproduces the approved reference numbers independently (PRD 14.1a,
13.1; CLAUDE.md "Reference numbers"; register 'reference_numbers', 'reference_test_tolerance').

**Which path produces each result.** Every run below goes through the real pipeline (adapters,
Checks, Inclusion, the dataset freeze) under the reference plan, then `analysis.run_statistics`,
which reads the frozen sets through the Statistics access object:

| Reference result | Path |
|---|---|
| Pooled | reference run (MPEA + Texas A&M, fixed minimums): its pooled analysis |
| Eight sensitivity sets | the same reference run: each set's sensitivity analysis |
| MPEA alone (1) | the reference run's per-source analysis for MPEA: full numbers, label "agrees"; run level 6 |
| MPEA alone (2) | a run that chose MPEA only, "use what is available": pooled analysis; it meets every minimum, so full numbers, a verdict, not exploratory; level 6 |
| MPEA alone (3) | a run that chose MPEA only, fixed minimums: pooled analysis; full numbers, a verdict; level 6 |
| Texas A&M alone (1) | the reference run's per-source analysis for Texas A&M: coefficient only (one group), label "not enough data"; run level 6 (from the pooled result) |
| Texas A&M alone (2) | a run that chose Texas A&M only, "use what is available": pooled analysis; coefficient only, no verdict; level 4 |
| Texas A&M alone (3) | a run that chose Texas A&M only, fixed minimums: withheld (21 records < 30, 1 group < 10): counts against each minimum and the 21 records found, no coefficient; level 3 |

**Tolerances, two tiers.**
1. Against the approved numbers, which are rounded: half a unit in the last digit stated. k and
   its standard error are stated to 0.1, so ±0.05; a p-value stated to two significant figures
   must lie in the interval that rounds to them (for 1.3e-6: [1.25e-6, 1.35e-6)). Counts are exact.
   This is tighter than the register's earlier ±1 (replaced with the owner's approval, 2026-10-05).
2. Package against the independent reference implementation (`reference_stats`, statsmodels) on
   the same frozen data: relative 1e-9 (same closed-form quantities in double precision; observed
   differences are below 1e-13).
Each "±" is one standard error (cluster-robust, by group), not a confidence interval.
"""
from __future__ import annotations

import math

import pytest

import pipeline_world as pw
import reference_stats as rs
from conftest import _create, _drop, url_for
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources.normalize import same_alloy_key
from stats_world import rows_of

# Approved values (owner, 2026-10-06; CLAUDE.md and the step 6 summary's table): records, alloys,
# groups, residual df, k, standard error, p-value as stated.
APPROVED = {
    "pooled": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "per_source:mpea": (76, 13, 19, 62, "424.1", "62.2", "1.1e-6"),
    "sensitivity:no_exclusions": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:tension_and_compression": (98, 22, 21, 75, "428.0", "63.5", "7.4e-7"),
    "sensitivity:six_batches_as_groups": (97, 22, 22, 74, "424.9", "64.2", "7.5e-7"),
    "sensitivity:same_alloy_1_at_pct": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:source_only_assignments": (76, 13, 19, 62, "424.1", "62.2", "1.1e-6"),
    "sensitivity:scope_not_confirmed_included": (103, 23, 22, 79, "432.4", "64.9", "6.7e-7"),
    "sensitivity:possible_duplicates_separate": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:conflicts_survivor_value": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
}
TAMU = (21, 9, 1, 11, "1173.3")  # coefficient only (step 6 table; CLAUDE.md: "≈ 1173")


def half_unit(stated: str) -> float:
    """Half a unit in the last digit of a stated number ("424.9" -> 0.05; "1.3e-6" -> 0.05e-6)."""
    mantissa, _, exponent = stated.partition("e")
    decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
    return 0.5 * 10 ** (-decimals) * (10 ** int(exponent) if exponent else 1)


def within(value: float, stated: str) -> bool:
    return abs(value - float(stated)) <= half_unit(stated) * (1 + 1e-12)


def test_half_a_unit_in_the_last_digit():
    assert half_unit("424.9") == pytest.approx(0.05) and half_unit("1173.3") == pytest.approx(0.05)
    assert half_unit("1.3e-6") == pytest.approx(0.05e-6) and half_unit("7.4e-7") == pytest.approx(0.05e-7)
    assert within(424.94, "424.9") and not within(424.96, "424.9")


def _run(engine, sources, option="fixed_minimum"):
    rid = pw.dispatched_run(engine, sources=sources)
    plan = reference_plan(pw.version_of(engine, rid))
    plan["sufficiency"]["option"] = option
    checkpoints.lock_rules(engine, rid, plan)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid


@pytest.fixture(scope="module")
def runs(admin, database_url, template_database):
    """Five runs in one scratch database, each through the freeze and the analysis stage."""
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        out = {}
        for key, sources, option in (("reference", ("mpea", "tamu_fcc"), "fixed_minimum"),
                                     ("mpea_use", ("mpea",), "use_available"), ("mpea_fixed", ("mpea",), "fixed_minimum"),
                                     ("tamu_use", ("tamu_fcc",), "use_available"),
                                     ("tamu_fixed", ("tamu_fcc",), "fixed_minimum")):
            rid = _run(engine, sources, option)
            data = bind_code(engine, rid, "statistics").get("frozen_analysis_data")
            stats_out = analysis.run_statistics(engine, rid)
            completion.copy_decision(engine, rid)
            run = rows_of(engine, "SELECT outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r", r=rid)[0]
            out[key] = {"rid": rid, "data": data, "out": stats_out, "run": run,
                        "analyses": {e["analysis"]: e for e in stats_out["analyses"]}}
        yield out
    finally:
        engine.dispose()
        _drop(admin, name)


def check_approved(entry, approved):
    n, alloys, groups, df, k, se, p = approved
    c = entry["counts"]
    assert (c["n_records"], c["n_alloys"], c["n_groups"], c["resid_df"]) == (n, alloys, groups, df)
    assert within(entry["estimate"], k), (entry["estimate"], k)
    assert within(entry["std_error"], se), (entry["std_error"], se)
    assert within(entry["p_value"], p), (entry["p_value"], p)


# --- tier 1: the approved numbers ----------------------------------------------------------------------

def test_pooled(runs):
    ref = runs["reference"]
    check_approved(ref["analyses"]["pooled"], APPROVED["pooled"])
    assert ref["out"]["decision"]["verdict"] == "supported"
    assert tuple(ref["run"]) == ("sufficient", "supported", False, 6)


@pytest.mark.parametrize("key", [k for k in APPROVED if k.startswith("sensitivity:")])
def test_each_sensitivity_set(runs, key):
    """Sensitivity sets go through the same code as the primary set; they never change the verdict."""
    entry = runs["reference"]["analyses"][key]
    check_approved(entry, APPROVED[key])
    assert entry["label"] is None and "verdict" not in entry


def test_mpea_alone_1_per_source_in_the_pooled_run(runs):
    entry = runs["reference"]["analyses"]["per_source:mpea"]
    check_approved(entry, APPROVED["per_source:mpea"])
    assert entry["label"] == "agrees" and runs["reference"]["run"].evidence_level == 6


@pytest.mark.parametrize("key, option", [("mpea_use", "use_available"), ("mpea_fixed", "fixed_minimum")])
def test_mpea_alone_2_and_3_as_its_own_run(runs, key, option):
    r = runs[key]
    pooled = r["analyses"]["pooled"]
    check_approved(pooled, APPROVED["per_source:mpea"])
    assert pooled["minimums_met"] and not pooled["withheld"]
    assert r["out"]["sufficiency_option"] == option
    assert tuple(r["run"]) == ("sufficient", "supported", False, 6)  # minimums met: not exploratory


def test_texas_am_alone_1_per_source_in_the_pooled_run(runs):
    entry = runs["reference"]["analyses"]["per_source:tamu_fcc"]
    n, alloys, groups, df, k = TAMU
    c = entry["counts"]
    assert (c["n_records"], c["n_alloys"], c["n_groups"], c["resid_df"]) == (n, alloys, groups, df)
    assert within(entry["estimate"], k) and entry["std_error"] is None and entry["p_value"] is None
    assert entry["label"] == "not_enough_data" and runs["reference"]["run"].evidence_level == 6
    assert {m: (c["status"], c["reason"]) for m, c in entry["calibration"].items()} == {
        "fixed": ("unavailable", "insufficient_groups"), "estimated": ("unavailable", "insufficient_groups")}


def test_texas_am_alone_2_use_what_is_available(runs):
    r = runs["tamu_use"]
    pooled = r["analyses"]["pooled"]
    assert within(pooled["estimate"], TAMU[4]) and pooled["std_error"] is None and pooled["p_value"] is None
    assert r["out"]["decision"]["state"] == "coefficient_only"
    assert tuple(r["run"]) == ("insufficient", None, False, 4)


def test_texas_am_alone_3_fixed_minimums_withheld(runs):
    r = runs["tamu_fixed"]
    pooled = r["analyses"]["pooled"]
    assert pooled["withheld"] and pooled["estimate"] is None
    assert pooled["minimums"] == {"records": {"count": 21, "minimum": 30, "met": False},
                                  "alloys": {"count": 9, "minimum": 5, "met": True},
                                  "groups": {"count": 1, "minimum": 10, "met": False},
                                  "resid_df": {"count": 11, "minimum": 10, "met": True}}
    assert len(pooled["records_found"]) == 21 and pooled["label_text"] == "data found; not enough to test"
    assert r["out"]["decision"]["state"] == "below_minimums"
    assert tuple(r["run"]) == ("insufficient", None, False, 3)
    assert all(e["estimate"] is None for e in r["out"]["analyses"])  # run-wide


# --- tier 2: against the independent reference implementation ---------------------------------------

def _rows(data, set_key, source=None):
    """Test-side alloy and group keys, independent of the package's eligibility module."""
    decimals = 0 if set_key == "same_alloy_1_at_pct" else 1
    out = []
    for r in data["records"]:
        if r["id"] not in set(data["sets"][set_key]) or (source and r["source"] != source):
            continue
        if r["source"] == "tamu_fcc":
            group = f"batch:{r['batch']}" if set_key == "six_batches_as_groups" else "dataset:tamu_fcc"
        else:
            group = f"paper:{r['paper']}"
        out.append((same_alloy_key(r["composition"], decimals), group, r["grain_size"], r["outcome"]))
    return out


@pytest.mark.parametrize("key", list(APPROVED) + ["per_source:tamu_fcc"])
def test_every_reference_result_matches_the_reference_implementation(runs, key):
    ref = runs["reference"]
    scope, _, name = key.partition(":")
    set_key = name if scope == "sensitivity" else "primary"
    expected = rs.fit(_rows(ref["data"], set_key, name if scope == "per_source" else None))
    got = ref["analyses"][key]
    assert (got["counts"]["n_records"], got["counts"]["n_alloys"], got["counts"]["n_groups"]) == (
        expected["n"], expected["alloys"], expected["groups"])
    for mine, theirs in ((got["estimate"], expected["k"]), (got["std_error"], expected["se"]),
                         (got["p_value"], expected["p"])):
        assert (mine is None and theirs is None) or math.isclose(mine, theirs, rel_tol=1e-9)
```

### `tests/test_permutation_stats.py`

```python
"""Step 7: results are a pure function of the frozen set and the locked plan (owner, 2026-10-05).

The same data, stored three times with record ids and insertion order permuted (each source's
records shuffled, the sources stored in a shuffled order, unrelated records of another run inserted
first so every id shifts), give identical analysis results, calibration results (seeds included),
stored decision, record of statistical significance and gap facts.
"""
from __future__ import annotations

import random

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources import adapters
from hypocurate.sources.record import AdapterResult

RESULT_COLUMNS = ("scope", "n_records", "n_alloys", "n_groups", "resid_df", "check1_passed", "check2_passed",
                  "minimums_met", "estimate", "std_error", "p_value", "estimated_power", "label", "withheld",
                  "n_records_not_used", "test_run_label")
CALIBRATION_COLUMNS = ("method", "status", "reason", "assumptions", "n_simulations", "seed", "null_share",
                       "null_ci_low", "null_ci_high", "effect_share", "effect_ci_low", "effect_ci_high",
                       "confidence_flag", "test_run_label")


def _permuted_analysis(db, vid, sources, seed, monkeypatch, marked):
    rnd = random.Random(seed)
    real_read = adapters.read

    def shuffled(version):
        result = real_read(version)
        records = list(result.records)
        rnd.shuffle(records)
        return AdapterResult(tuple(records), result.blank_rows)

    with monkeypatch.context() as m:
        m.setattr(extract.adapters, "read", shuffled)
        for _ in range(seed):
            other = pw.run_of_version(db, vid, sources=("tamu_fcc",))
            checkpoints.lock_rules(db, other, reference_plan(vid))
            extract.store_records(db, other)
        rid = pw.run_of_version(db, vid, sources=sources, marked=marked)
        checkpoints.lock_rules(db, rid, reference_plan(vid))
        order = list(sources)
        rnd.shuffle(order)
        for key in order:
            extract.store_source(db, rid, key)
    checks.run_checks(db, rid)
    inclusion.decide_run(db, rid)
    checkpoints.freeze_dataset(db, rid)
    out = analysis.run_statistics(db, rid)
    with db.connect() as conn:
        keyed = {r.id: (r.key, r.source) for r in conn.execute(text(
            "SELECT ar.id, a.key, s.key AS source FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r"), dict(r=rid))}
        rows = {keyed[r.id]: tuple(getattr(r, c) for c in RESULT_COLUMNS) for r in conn.execute(text(
            "SELECT * FROM analysis_result WHERE run_id = :r"), dict(r=rid))}
        cal = {(keyed[r.analysis_result_id], r.method): tuple(getattr(r, c) for c in CALIBRATION_COLUMNS)
               for r in conn.execute(text("SELECT * FROM calibration_result WHERE run_id = :r"), dict(r=rid))}
        facts = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'"),
                             dict(r=rid)).scalar_one()
    return out, rows, cal, facts


@pytest.mark.parametrize("sources, marked", [(("mpea", "tamu_fcc"), False), (("mpea", "controlled_duplicates"), True)],
                         ids=["reference_data", "controlled_extract"])
def test_permuted_ids_and_insertion_order_give_identical_results(db, monkeypatch, sources, marked):
    pw.registered(db, ("mpea", "tamu_fcc", "controlled_duplicates"))
    vid = pw.version_of(db, pw.dispatched_run(db, sources=("tamu_fcc",)))
    results = [_permuted_analysis(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
    first = results[0]
    assert first[0]["analyses"][0]["estimate"] is not None and len(first[2]) == 2 * len(first[1])
    for other in results[1:]:
        assert other[0] == first[0]  # the record of statistical significance and the decision, seeds included
        assert other[1] == first[1]  # every analysis result
        assert other[2] == first[2]  # every calibration result
        assert other[3] == first[3]  # the gap facts
```

### `tests/test_migrations_step7.py`

```python
"""Step 7: migration 0004 (approved by the owner on 2026-10-05, subject to the second-model review).

Additive; 0001 to 0003 untouched; the two replaced trigger functions keep every check of 0001; up,
down, up gives the same schema; the downgrade refuses while step 7 results use what 0004 adds and
restores 0001's functions exactly; a failed upgrade changes nothing. Every test starts from an
empty scratch database, except the one that needs a run."""
from __future__ import annotations

import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis
from test_migrations import assert_schema_is_empty, assert_schema_is_head, snapshot
from test_migrations_step6 import body, columns

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0004 = SCRIPTS.get_revision("0004").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


def function_source(engine, name) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = :n"), dict(n=name)).scalar_one()


def checks_of(function_sql: str) -> list[str]:
    """Each `IF ... END IF;` block of a function body, whitespace normalized."""
    return re.findall(r"IF .*? END IF;", body(function_sql))


def test_0004_is_the_head_and_follows_0003():
    assert migrate.head_revision() == "0004" and M0004.down_revision == "0003"


@pytest.mark.parametrize("name", ["hc_analysis_result_insert", "hc_calibration_insert"])
def test_the_downgrade_keeps_0001s_functions_verbatim(name):
    original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
    kept = M0004.ANALYSIS_RESULT_INSERT_0001 if name == "hc_analysis_result_insert" else M0004.CALIBRATION_INSERT_0001
    assert body(kept) == body(original)


def test_the_new_result_function_keeps_every_check_of_0001():
    """Every check of 0001's function is in 0004's, unchanged, except the record count, which now
    accounts for the records the fit does not use (decision 7)."""
    old, new = checks_of(M0004.ANALYSIS_RESULT_INSERT_0001), body(M0004.ANALYSIS_RESULT_INSERT_0004)
    changed = [c for c in old if c not in new]
    assert changed == ["IF NEW.n_records <> set_count THEN PERFORM hc_reject('n_records must equal the records of "
                       "the set used'); END IF;"]
    assert ("IF NEW.n_records + NEW.n_records_not_used <> set_count THEN PERFORM hc_reject('n_records must equal "
            "the records of the set used, less those the fit does not use'); END IF;") in new


def test_the_new_calibration_function_keeps_the_run_level_rules_of_0001():
    old, new = body(M0004.CALIBRATION_INSERT_0001), body(M0004.CALIBRATION_INSERT_0004)
    for kept in ("IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN PERFORM hc_reject('calibration is "
                 "recorded only while the run is running'); END IF;",
                 "IF NEW.analysis_result_id IS NULL THEN IF hc_is_frozen(NEW.run_id) THEN PERFORM hc_reject('a dataset "
                 "was frozen: calibration is reported per analysis'); END IF; RETURN NEW; END IF;"):
        assert kept in old and kept in new
    # 0001's "computed exactly when inference is valid" is kept, strengthened by "and not withheld".
    assert "calibration is computed exactly when inference is valid" in old
    assert "calibration is computed exactly when inference is valid and the result is not withheld" in new


def test_up_down_up(engine):
    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    first = snapshot(engine)
    assert {"withheld", "n_records_not_used", "test_run_label"} <= columns(engine, "analysis_result")
    assert {"method", "test_run_label"} <= columns(engine, "calibration_result")
    assert "evidence_level" in columns(engine, "run")
    migrate.downgrade(engine, "0003")
    assert migrate.current_revision(engine) == "0003"
    assert not {"withheld", "n_records_not_used", "test_run_label"} & columns(engine, "analysis_result")
    assert not {"method", "test_run_label"} & columns(engine, "calibration_result")
    assert "evidence_level" not in columns(engine, "run")
    for name in ("hc_analysis_result_insert", "hc_calibration_insert"):
        original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
        assert " ".join(function_source(engine, name).split()) == body(original)
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0003")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE run ADD COLUMN evidence_level int"))  # 0004 adds it last
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0003"


def test_the_downgrade_refuses_while_step_7_results_use_0004(db):
    """A run with step 7 results: the downgrade refuses, and nothing changes."""
    import stats_world as sw
    rid = sw.run_on(db, sw.small_rows(3, papers=3))
    analysis.run_statistics(db, rid)  # withheld results and 'below_minimums' calibration rows
    before = snapshot(db)
    with pytest.raises(IntegrityError, match="0004 cannot be downgraded while step 7 results use it"):
        migrate.downgrade(db, "0003")
    assert snapshot(db) == before and migrate.current_revision(db) == "0004"
```


## 10. Tests: changed files (diffs)

### `tests/access_world.py` (diff against `main`, `3aee798`)

```diff
diff --git a/tests/access_world.py b/tests/access_world.py
index 0a781b1..cc2bf5a 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -186,7 +186,9 @@ def original_run(w: World) -> int:
     """A completed 'partly sufficient' run with OTHER in its records, coefficient, stage
     outputs and commentary: the run a narrower question comes from."""
     rid = w.running(sources=("mpea",))
-    w.lock(rid)
+    # Step 7 (owner's decision 1): under the fixed option a run below the minimums stores no
+    # coefficient, so this run, which holds OTHER as its coefficient, uses what is available.
+    w.lock(rid, option="use_available")
     w.search(rid, "mpea")
     recs = store_value_records(w, rid, OTHER)
     primary = w.analysis_set(rid)
```

### `tests/model_builder.py` (diff against `main`, `3aee798`)

```diff
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 5d1ba12..0d6e4da 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -221,12 +221,19 @@ class World:
         check2 = check1 and resid >= 1 and groups >= 2
         if minimums_met is None:
             minimums_met = n >= mins[0] and alloys >= mins[1] and groups >= mins[2] and resid >= mins[3]
+        # Step 7 (migration 0004): a result is withheld (no number from outcomes) when the run uses
+        # the fixed option and its pooled result misses a minimum; the database computes it.
+        option = self.val("SELECT sufficiency_option FROM plan WHERE run_id = :r", r=rid)
+        pooled = self.val("SELECT withheld FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
+        withheld = (option == "fixed_minimum" and not minimums_met) if scope == "pooled" else bool(pooled)
+        check1, check2 = check1 and not withheld, check2 and not withheld  # only for the values below
         return self.val(
             "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, "
             "resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
             "VALUES (:r, :sc, :s, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
             r=rid, sc=scope, s=set_id, src=self.source[source] if source else None, n=n, a=alloys, g=groups,
-            df=resid, c1=check1, c2=check2, mm=minimums_met, est=428.0 if check1 else None,
+            df=resid, c1=alloys >= 1, c2=alloys >= 1 and resid >= 1 and groups >= 2, mm=minimums_met,
+            est=428.0 if check1 else None,
             se=64.0 if check2 else None, p=1e-6 if check2 else None)
 
     def complete(self, rid, outcome, verdict=None, exploratory=False):
```

### `tests/test_data_model.py` (diff against `main`, `3aee798`)

```diff
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index 61af868..a703569 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -239,8 +239,10 @@ def test_sufficient_needs_a_pooled_result_that_passed_both_checks(w):
 
 
 def test_coefficient_only_completes_as_insufficient_without_a_verdict(w):
-    """Check 1 passes, check 2 fails (2 records, 1 alloy: no residual degree of freedom)."""
-    rid, sets, _ = w.frozen(n=2, mins=(1, 1, 1, 1))
+    """Check 1 passes, check 2 fails (2 records, 1 alloy: no residual degree of freedom).
+    Step 7: under "use what is available" (under the fixed option the run misses the residual
+    minimum, so the coefficient is withheld: owner's decision 1, tested in test_statistics_results)."""
+    rid, sets, _ = w.frozen(n=2, mins=(1, 1, 1, 1), option="use_available")
     w.result(rid, sets["primary"], n=2, alloys=1, groups=2)
     assert w.rows("SELECT check1_passed, check2_passed, estimate IS NOT NULL, std_error, p_value "
                   "FROM analysis_result WHERE run_id = :r", r=rid) == [(True, False, True, None, None)]
@@ -892,12 +894,14 @@ def test_results_come_after_the_freeze(w):
     ("resid_df", "5", "ck_analysis_result_resid_df_definition"),
 ])
 def test_the_validity_checks_cannot_be_waived(w, column, value, match):
-    """One group: check 2 fails, so no uncertainty and no p-value can be stored."""
-    rid, sets, _ = w.frozen()
+    """One group: check 2 fails, so no uncertainty and no p-value can be stored. Step 7: under "use
+    what is available", so that the result is not withheld (owner's decision 1) and each constraint
+    is the one that refuses."""
+    rid, sets, _ = w.frozen(option="use_available")
     rid_value = w.result(rid, sets["primary"], groups=1)
     assert w.rows("SELECT check2_passed, std_error, p_value FROM analysis_result WHERE id = :a", a=rid_value) == [
         (False, None, None)]
-    rid2, sets2, _ = w.frozen()
+    rid2, sets2, _ = w.frozen(option="use_available")
     columns = {"run_id": rid2, "scope": "'pooled'", "analysis_set_id": sets2["primary"], "n_records": 4,
                "n_alloys": 1, "n_groups": 1, "resid_df": 2, "check1_passed": "true", "check2_passed": "false",
                "minimums_met": "false", "estimate": 1.0}
@@ -965,9 +969,11 @@ def test_minimums_met_must_agree_with_the_plan(w):
 
 # --- calibration --------------------------------------------------------------------------------------
 
-CALIBRATION = ("INSERT INTO calibration_result (run_id, analysis_result_id, status, reason, assumptions, "
+# Step 7 (migration 0004): a row of an analysis names its method (here 'fixed'); the run-level row none.
+CALIBRATION = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, "
                "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, "
-               "effect_ci_high, confidence_flag) VALUES (:r, :a, :st, :re, {numbers})")
+               "effect_ci_high, confidence_flag) VALUES (:r, :a, CASE WHEN CAST(:a AS bigint) IS NULL THEN NULL "
+               "ELSE 'fixed' END, :st, :re, {numbers})")
 NUMBERS = "'{\"scatter\": 60}', 2000, 7, 0.072, 0.061, 0.084, 1.0, 0.998, 1.0, 'over_confident'"
 NONE = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"
 
@@ -983,6 +989,7 @@ def test_calibration_is_computed_exactly_when_inference_is_valid(w):
 
 def test_calibration_unavailable_states_a_matching_reason(w):
     rid, sets, _ = w.frozen(n=2, per_source={"mpea": 1, "tamu_fcc": 1}, mins=(1, 1, 1, 1))
+    w.result(rid, sets["primary"], n=2, alloys=0, groups=2, mins=(1, 1, 1, 1))  # step 7: the pooled row first
     one_group = w.result(rid, sets["primary"], scope="per_source", source="mpea", n=1, alloys=0, groups=1,
                          mins=(1, 1, 1, 1))
     w.rejected(CALIBRATION.format(numbers=NUMBERS), "computed exactly when", r=rid, a=one_group, st="computed",
```

### `tests/test_access_code_roles.py` (diff against `main`, `3aee798`)

```diff
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index a062940..f9b9eaa 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -44,21 +44,28 @@ def audit(engine, run_id):
                                  "ORDER BY id"), dict(r=run_id)).all()
 
 
+# The two code roles of step 6. Step 7 adds Statistics and the gap facts (test_access_statistics.py).
+STEP6_ROLES = ("inclusion", "checks")
+
+
 def test_the_code_lists_match_the_owners_decision():
-    assert CODE_ROLES == ("inclusion", "checks") and ALL_ROLES == ROLES + CODE_ROLES
+    # Step 7 (owner, 2026-10-05): Statistics and the gap facts added (changed from step 6's two).
+    assert CODE_ROLES == ("inclusion", "checks", "statistics", "gap_facts") and ALL_ROLES == ROLES + CODE_ROLES
     assert not set(CODE_ROLES) & set(ALLOWED)  # the agent table is unchanged
-    assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {"inclusion": {"curation"}, "checks": {"curation"}}
+    assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {
+        "inclusion": {"curation"}, "checks": {"curation"}, "statistics": {"analysis"},
+        "gap_facts": {"analysis", "closed_without_freeze"}}
     # set_flags: step 6 review, finding 2 (each sensitivity set's matching flags, codes and ids only).
     assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind", "set_flags"}
     assert allowed("checks", "curation") == {"plan", "records_full"}
-    for role in CODE_ROLES:
+    for role in STEP6_ROLES:
         for stage in ("none", "before_lock", "analysis", "closed_without_freeze", "final", "final_without_freeze"):
             assert allowed(role, stage) == frozenset()
 
 
 def test_code_roles_bind_at_curation_and_every_bind_is_logged(engine):
     world = aw.build(engine, "curation")
-    for role in CODE_ROLES:
+    for role in STEP6_ROLES:
         access = bind_code(engine, world.run, role)
         assert (access.context.role, access.context.stage, access.context.agent_setting_id) == (role, "curation", None)
     rows = [r for r in audit(engine, world.run) if r.function == "bind" and r.role in CODE_ROLES]
@@ -69,7 +76,7 @@ def test_code_roles_bind_at_curation_and_every_bind_is_logged(engine):
 @pytest.mark.parametrize("stage", ["queued", "before_lock", "analysis", "closed_without_freeze", "final"])
 def test_code_roles_do_not_bind_at_any_other_stage(engine, stage):
     world = aw.build(engine, stage)
-    for role in CODE_ROLES:
+    for role in STEP6_ROLES:
         with pytest.raises(AccessDenied) as denied:
             bind_code(engine, world.run, role)
         assert denied.value.code == "empty_list"
```

### `tests/test_assumptions.py` (diff against `main`, `3aee798`)

```diff
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 7da064f..11f8479 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -33,11 +33,11 @@ OWNER = "owner (Khalid El-Awady)"
 OWNER_DECISIONS = {
     "tamu_test_temperature": ("scientific", "yes", None),
     "permitted_test_types": ("scientific", "yes", None),
-    "tamu_grouping_unit": ("statistical", "partly", 7),  # the adapter's unit and the plan's grouping; inference
+    "tamu_grouping_unit": ("statistical", "yes", None),  # step 7: the groups used in inference
     "same_alloy_rule": ("scientific", "yes", None),
-    "fixed_minimums": ("statistical", "partly", 7),  # plan default and freeze counts; the check deciding outcomes
+    "fixed_minimums": ("statistical", "yes", None),  # step 7: the check deciding the outcome
     "values_disagree_tolerance": ("data_handling", "yes", None),
-    "calibration_noise_levels": ("statistical", "not_yet", 7),
+    "calibration_noise_levels": ("statistical", "yes", None),  # step 7: built, its review pending
     "tag_starting_lists": ("data_handling", "yes", None),
 }
 
@@ -57,9 +57,10 @@ def test_every_category_has_entries_and_keys_are_unique():
 
 # Step 6 completed same_alloy_rule, sufficiency_options, controlled_extract_disabled and
 # assigned_value_statuses, and added constructed_test_runs (its label and exclusion: steps 7, 10).
-PARTLY = {"tamu_grouping_unit", "papers_independent", "validity_checks", "fixed_minimums",
-          "grain_size_transformation_at_analysis", "constructed_test_runs",
-          "reference_numbers"}  # owner, 2026-10-06: coefficients reproduced by the statistics module in step 7
+# Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
+# grain_size_transformation_at_analysis and reference_numbers; records_without_group is open, with
+# the code failing closed until the owner decides.
+PARTLY = {"constructed_test_runs", "records_without_group"}
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -87,10 +88,14 @@ def test_decisions_carry_the_owners_wording():
     assert "min(|a|, |b|)" in BY_KEY["values_disagree_tolerance"]["statement"]
     assert "conflict_pairing_rule" in " ".join(BY_KEY["values_disagree_tolerance"]["notes"])
     calibration = BY_KEY["calibration_noise_levels"]
-    assert "fixed at the rules lock and applied by code" in calibration["statement"]
-    assert "no person or agent chooses the values" in calibration["statement"]
+    # Step 7 (owner, 2026-10-05): reported both ways; the estimation method stated exactly.
+    assert "Henderson's method III" in calibration["statement"] and "fixed at the rules lock" in calibration["statement"]
+    assert "No person or agent chooses a value" in calibration["statement"]
     notes = " ".join(calibration["notes"])
-    assert "PRD 5.10" in notes and "second-model review in step 7" in notes and "both ways" in notes
+    assert "PRD 5.10" in notes and "second-model review" in notes
+    assert "fixed at the rules lock and applied by code" in calibration["history"][-1]["value"]
+    assert "both ways" in calibration["history"][-1]["note"]
+    assert "Both are stored" in BY_KEY["calibration_both_ways"]["statement"]
     assert BY_KEY["p_threshold_comparison"]["value"]["text"] == "p < α (α = 0.05 by default)"
 
 
@@ -116,11 +121,14 @@ def test_the_survivor_rule_has_the_owners_step_1_wording():
 def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review():
     """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)
     and added the possible-duplicate case and the rule for several candidates in step 6 planning.
-    Step 6 recorded two new open decisions for the owner (steps 7 and 8)."""
-    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["below_minimum_display", "curator_tabular_sources"]
+    Step 6 recorded two new open decisions for the owner (steps 7 and 8). Step 7: the owner decided
+    the first; a new one (records without a group) is open before step 8."""
+    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["curator_tabular_sources", "records_without_group"]
     assert {e["key"]: e["pending"]["before_step"] for e in REGISTER if e["state"] == "open"} == {
-        "below_minimum_display": 7, "curator_tabular_sources": 8}
-    assert "not even a coefficient" in " ".join(BY_KEY["below_minimum_display"]["notes"])
+        "curator_tabular_sources": 8, "records_without_group": 8}
+    below = BY_KEY["below_minimum_display"]
+    assert below["state"] == "in_force" and below["decided"] == {"by": OWNER, "date": "2026-10-05"}
+    assert "not even a coefficient" in " ".join(below["notes"]) and below["history"][-1]["value"].startswith("open")
     pairing = BY_KEY["conflict_pairing_rule"]
     assert pairing["state"] == "in_force" and "pending" not in pairing
     assert pairing["decided"] == {"by": OWNER, "date": "2026-10-05"}
@@ -139,7 +147,7 @@ def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review
         "same paper with the same alloy, grain size and test conditions. Rows within one source are always "
         "separate measurements (repeat specimens).")
     assert [e["key"] for e in REGISTER if e["state"] == "direction_approved"] == ["calibration_noise_levels"]
-    assert BY_KEY["calibration_noise_levels"]["pending"] == {"by": "second-model technical review", "before_step": 7}
+    assert BY_KEY["calibration_noise_levels"]["pending"] == {"by": "second-model technical review", "before_step": 8}
 
 
 REVIEW_ADDITIONS = {
@@ -245,7 +253,8 @@ def test_the_approved_reference_numbers_keep_the_earlier_values_in_their_history
     assert e["decided"] == {"by": OWNER, "date": "2026-10-06"} and e["state"] == "in_force"
     assert "k = 424.9 ± 64.4" in e["statement"] and "k = 424.1 ± 62.2" in e["statement"]
     assert "must reproduce them independently" in e["statement"]
-    assert e["applied"]["status"] == "partly" and e["applied"]["step"] == 7
+    # Step 7: reproduced by the statistics module (tests/test_reference_numbers.py).
+    assert e["applied"]["status"] == "yes" and "tests/test_reference_numbers.py::test_pooled" in e["tests"]
     assert "k = 428 ± 64" in e["history"][0]["value"] and "77 records" in e["history"][0]["value"]
     assert "database rule" in " ".join(BY_KEY["constructed_test_runs"]["notes"])
 
@@ -453,14 +462,14 @@ def test_open_decisions_are_shown_first_when_there_are_any():
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
     assert headings == HEADINGS
     first = re.split(r"<h2>", html)[1]
-    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["below_minimum_display", "curator_tabular_sources",
+    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["curator_tabular_sources", "records_without_group",
                                                              "an_open_question"]
     assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
-    assert "Not decided (owner, before step 7)" in first and "Not decided (owner, before step 8)" in first
+    assert first.count("Not decided (owner, before step 8)") == 2
     assert "3 open decisions</strong>" in html
     second = re.split(r"<h2>", html)[2]
     assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
-    assert "pending: second-model technical review, before step 7" in second
+    assert "pending: second-model technical review, before step 8" in second
 
 
 def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
@@ -515,7 +524,7 @@ def test_each_row_expands_to_reason_evidence_history_and_sensitivity():
         assert str(escape(text)) in body, text
     applied = re.search(r'<tbody id="session_length"(.*?)</tbody>', html, re.S).group(1)
     assert "<code>python:hypocurate.web.app:SESSION_MAX_AGE</code>" in applied
-    assert "Not yet: step 7" in re.search(r'<tbody id="exponent_fixed"(.*?)</tbody>', html, re.S).group(1)
+    assert "Not yet: step 9" in re.search(r'<tbody id="spending_caps"(.*?)</tbody>', html, re.S).group(1)
     assert "<code>tests/test_login.py::test_session_expires_after_max_age</code>" in applied
     assert "Named settings (reference and value checks only)" in applied
```


## 11. README (diff)

### `README.md` (diff against `main`, `3aee798`)

````diff
diff --git a/README.md b/README.md
index a11e99c..67d15e6 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,7 @@ HypoCurate takes a scientific hypothesis in words, searches registered data sour
 
 ## Status
 
-Build step 6 of 12 (PRD Section 15): the plan, the two checkpoints, inclusion and checks. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), the access layer with its audit log and the file guard for pipeline processes (step 5), plus the plan model, the rules lock, record storage, the code checks that raise flags, the eligibility decisions and the dataset freeze (step 6). The statistics, the agents and the screens come in later steps.
+Build step 7 of 12 (PRD Section 15): the statistics, the validity checks, data sufficiency, the verdict and per-run calibration. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), the access layer with its audit log and the file guard for pipeline processes (step 5), plus the plan model, the rules lock, record storage, the code checks that raise flags, the eligibility decisions and the dataset freeze (step 6), plus the supported model, the two validity checks, the fixed-minimum check, the verdict, per-run calibration both ways, the record of statistical significance, the gap facts and the copy of the decision onto the run (step 7). The agents, the worker, the screens, the plot and the workbook come in later steps.
 
 ## Set up secrets (once)
 
@@ -158,9 +158,27 @@ checkpoints.freeze_dataset(engine, run_id)  # counts and fingerprint; or "no dat
 - **Every write** takes `hc_write_lock(p_run => …)` in `run_transaction`, re-checks by id what it read, and logs any refusal (`audit_log`, `detail.result` "rejected").
 - **Constructed test data** (the controlled extract) enter only a run marked `{"constructed_test_data": true}` in `experiment_flags` at dispatch.
 
+## Statistics, calibration and the decision
+
+Code in `hypocurate/pipeline/` (step 7; PRD 5.7 to 5.10). No agent, no model call, no screen or plot yet.
+
+```python
+from hypocurate.pipeline import analysis, completion
+analysis.run_statistics(engine, run_id)   # every analysis, both calibrations, the record of significance, gap facts
+completion.copy_decision(engine, run_id)  # copies the stored decision onto the run and completes it (steps 8/9 call it)
+```
+
+- **One model** (`statistics.py`): yield strength = baseline per alloy + k × (grain size in µm)^-1/2, OLS with alloy intercepts, cluster-robust SE by group with statsmodels' small-sample correction, one-sided t test with groups − 1 df; "supported" when p < α. Each fit uses only alloys with two or more distinct grain sizes among its records; the minimums are counted on those records.
+- **The two validity checks** can never be waived. Under the fixed option, a pooled fit that misses any minimum withholds every analysis of the run: counts and records only, "data found; not enough to test". "Use what is available" waives the minimums only and labels the result exploratory.
+- **Calibration** (`calibration.py`) is reported both ways for each analysis whose numbers are shown: with the plan's fixed scatter and shift, and with both estimated from the frozen records (Henderson's method III). A flag, never a gate. The seed comes from the freeze fingerprint, the analysis and the method.
+- **Statistics reads only the frozen sets** through its own access object (`bind_code(…, "statistics")`, analysis stage only); the gap facts read no outcome value. Results are a pure function of the frozen set and the locked plan.
+- **The decision** (outcome, verdict, exploratory, evidence level 1 to 6) is stored in the "statistics" stage result and copied onto the run unchanged; the copy refuses a missing decision or one from another freeze.
+- **Marked test runs** carry "test run: includes constructed data" on every stored result; aggregates use `results.REAL_RUN`.
+- **Software correctness** is checked against an independent statsmodels implementation on the test side (`tests/reference_stats.py`); statsmodels is a development dependency only.
+
 ## Access layer
 
-Every agent reads data only through an access object for one run, role and stage (`hypocurate/access/`; PRD 4). There is no agent yet (step 8). The code roles Inclusion and Checks (step 6) read through access objects too, bound by `dispatch.bind_code` at the curation stage only.
+Every agent reads data only through an access object for one run, role and stage (`hypocurate/access/`; PRD 4). There is no agent yet (step 8). The code roles read through access objects too, bound by `dispatch.bind_code`: Inclusion and Checks (step 6) at the curation stage only; Statistics (step 7) at the analysis stage only; the gap facts (step 7) at the analysis stage and when a run closed without a freeze.
 
 ```python
 from hypocurate.access import bind, role_input
````


## 12. Mutation checks

The harness (`mutate.sh`) copies `hypocurate/` to the scratchpad, links `data/`, applies one replacement, checks that the copy is the package imported, and runs the named tests from outside the repository with `PYTHONPATH` set to the copy. A control run with no change passes.

### `mutate.sh`

```bash
#!/bin/bash
# usage: mutate.sh <name> <file relative to hypocurate/> <python replacement script> <tests...>
set -e
S=/tmp/claude-1000/-workspaces-hypocurate/d40b08e7-9c83-4b0a-8b2e-aa110db4b20f/scratchpad
NAME=$1; FILE=$2; OLD=$3; NEW=$4; shift 4
COPY=$S/mut/$NAME
rm -rf $COPY && mkdir -p $COPY && cp -r /workspaces/hypocurate/hypocurate $COPY/ && ln -s /workspaces/hypocurate/data $COPY/data
find $COPY -name __pycache__ -prune -exec rm -rf {} +
/workspaces/hypocurate/.venv/bin/python - "$COPY/hypocurate/$FILE" "$OLD" "$NEW" <<'PY'
import sys
p, old, new = sys.argv[1:]
s = open(p).read()
assert s.count(old) >= 1, f"pattern not found in {p}: {old!r}"
open(p, "w").write(s.replace(old, new))
PY
cd $S
export DATABASE_URL="$(grep '^DATABASE_URL=' /workspaces/hypocurate/.env | cut -d= -f2-)"
PYTHONPATH=$COPY /workspaces/hypocurate/.venv/bin/python -c "import hypocurate,sys; assert hypocurate.__file__.startswith('$COPY'), hypocurate.__file__"
PYTHONPATH=$COPY /workspaces/hypocurate/.venv/bin/pytest -q -p no:cacheprovider --rootdir=/workspaces/hypocurate "$@" 2>&1 | grep -E "^FAILED|passed|failed|error" | sed "s/^/[$NAME] /" | tail -12
rm -rf $COPY
```

### `mutations.sh`

```bash
#!/bin/bash
M=/tmp/claude-1000/-workspaces-hypocurate/d40b08e7-9c83-4b0a-8b2e-aa110db4b20f/scratchpad/mutate.sh
PURE="/workspaces/hypocurate/tests/test_statistics.py /workspaces/hypocurate/tests/test_generated_fixed_set.py /workspaces/hypocurate/tests/test_calibration.py"
$M m01_never_withheld pipeline/statistics.py 'return plan["sufficiency"]["option"] == "fixed_minimum" and not all(v["met"] for v in m.values())' 'return False' $PURE /workspaces/hypocurate/tests/test_analysis_stage.py /workspaces/hypocurate/tests/test_reference_numbers.py
$M m02_p_at_or_below pipeline/statistics.py 'return None if p_value is None else p_value < alpha' 'return None if p_value is None else p_value <= alpha' $PURE
$M m03_no_correction pipeline/statistics.py 'return (n_groups / (n_groups - 1)) * ((n - 1) / (n - n_alloys - 1))' 'return 1.0' $PURE /workspaces/hypocurate/tests/test_reference_numbers.py
$M m04_alloy_rule_one pipeline/statistics.py 'MODEL_MIN_GRAIN_SIZES = 2' 'MODEL_MIN_GRAIN_SIZES = 1' $PURE
$M m05_no_identity_sort pipeline/statistics.py 'obs = sorted(observations, key=lambda o: o.identity)' 'obs = list(observations)' $PURE /workspaces/hypocurate/tests/test_permutation_stats.py
$M m06_df_groups pipeline/statistics.py 'df = d.n_groups - 1' 'df = d.n - d.n_alloys - 1' $PURE /workspaces/hypocurate/tests/test_reference_numbers.py
$M m07_two_sided pipeline/statistics.py 'return float(stats.t.sf(t, df))' 'return float(2 * stats.t.sf(abs(t), df))' $PURE /workspaces/hypocurate/tests/test_reference_numbers.py
$M m08_coefficient_below_min pipeline/statistics.py '    if withheld:
        return entry
    f = fit(d)' '    f = fit(d)' $PURE /workspaces/hypocurate/tests/test_analysis_stage.py
$M m09_label_sign_ignored pipeline/statistics.py '    if (a > 0) != (b > 0):
        return "conflicts"' '' /workspaces/hypocurate/tests/test_statistics.py
$M m10_exploratory_ignored pipeline/statistics.py '    if option == "use_available" and not pooled["minimums_met"]:
        return "exploratory"' '' /workspaces/hypocurate/tests/test_statistics.py /workspaces/hypocurate/tests/test_generated_fixed_set.py /workspaces/hypocurate/tests/test_analysis_stage.py
$M m11_copy_no_fp_check pipeline/completion.py '        if decision.get("freeze_fingerprint") != snapshot:' '        if False:' /workspaces/hypocurate/tests/test_completion.py
$M m12_copy_recomputes pipeline/completion.py 'o=decision["outcome"], v=decision["verdict"]' 'o=decision["outcome"], v="supported" if decision["outcome"] == "sufficient" else None' /workspaces/hypocurate/tests/test_completion.py
$M m13_frozen_all_records access/fields.py '        if r.id not in members:
            continue' '' /workspaces/hypocurate/tests/test_access_statistics.py
$M m14_statistics_at_curation access/allowlist.py '"statistics": MappingProxyType({"analysis": frozenset({"plan", "frozen_analysis_data"})}),' '"statistics": MappingProxyType({"analysis": frozenset({"plan", "frozen_analysis_data"}), "curation": frozenset({"plan", "frozen_analysis_data"})}),' /workspaces/hypocurate/tests/test_access_statistics.py
$M m15_gap_sees_records access/allowlist.py '"analysis": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),' '"analysis": frozenset({"plan", "decisions", "stored_record_counts", "coverage", "records_full"}),' /workspaces/hypocurate/tests/test_access_statistics.py
$M m16_no_truncation_flag pipeline/calibration.py '"shift_truncated_at_zero": shift_sq_raw < 0,' '"shift_truncated_at_zero": False,' /workspaces/hypocurate/tests/test_calibration.py
$M m17_fixed_uses_estimates pipeline/calibration.py '        scatter, shift = calibration["scatter"], calibration["shift"]' '        scatter, shift = henderson_iii(d).get("scatter", 60.0), henderson_iii(d).get("shift", 40.0)' /workspaces/hypocurate/tests/test_calibration.py /workspaces/hypocurate/tests/test_generated_fixed_set.py
$M m18_flag_inverted pipeline/calibration.py '    if low > alpha:
        return "over_confident"' '    if low > alpha:
        return "under_confident"' /workspaces/hypocurate/tests/test_calibration.py
$M m19_seed_by_id pipeline/calibration.py 'f"{freeze_fingerprint}|{analysis}|{method}"' 'f"{freeze_fingerprint}|{analysis}"' /workspaces/hypocurate/tests/test_calibration.py
$M m20_trigger_no_withheld db/migrations/versions/0004_statistics_results.py "        ELSIF NEW.withheld <> computed THEN
            PERFORM hc_reject('withheld must equal: the fixed option and the pooled minimums not met');
        END IF;" "        END IF;" /workspaces/hypocurate/tests/test_analysis_stage.py
$M m21_trigger_no_label_check db/migrations/versions/0004_statistics_results.py "        IF (NEW.test_run_label IS NOT NULL) <> \"\"\" + MARKED + \"\"\" THEN
            PERFORM hc_reject('a result carries the test-run label exactly when its run is marked as a test');
        END IF;
        RETURN NEW;
    END \$\$
    \"\"\"

CALIBRATION_INSERT_0004" "        RETURN NEW;
    END \$\$
    \"\"\"

CALIBRATION_INSERT_0004" /workspaces/hypocurate/tests/test_analysis_stage.py
$M m22_no_label_written pipeline/analysis.py '        label = TEST_RUN_LABEL if marked(conn, run_id) else None' '        label = None' /workspaces/hypocurate/tests/test_analysis_stage.py
$M m23_pooled_ungrouped_skipped pipeline/analysis.py '            if scope == "pooled":
                raise' '' /workspaces/hypocurate/tests/test_statistics.py
$M m24_real_run_unfiltered pipeline/results.py "REAL_RUN = \"NOT coalesce(r.experiment_flags->>'constructed_test_data' = 'true', false)\"" 'REAL_RUN = "true"' /workspaces/hypocurate/tests/test_analysis_stage.py
$M m25_second_analysis_allowed pipeline/analysis.py '        if done:
            raise Refused("run_statistics", "already_done")' '' /workspaces/hypocurate/tests/test_analysis_stage.py
```

### Output

```
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key10]
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key14]
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key18]
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option[one_alloy_two_sizes-fixed_minimum]
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option[single_group-fixed_minimum]
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_below_the_minimums_every_analysis_holds_counts_and_records_only
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_withheld_results_do_not_depend_on_the_outcome_values
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_fixed_option_with_one_group_withholds_even_the_coefficient
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_gap_facts_hold_no_text_and_no_outcome_value
[m01_never_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_refuses_calibration_that_does_not_match_the_result
[m01_never_withheld] 12 failed, 124 passed, 26 errors in 48.94s
[m02_p_at_or_below] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_supported_exactly_when_p_is_strictly_below_alpha
[m02_p_at_or_below] 1 failed, 107 passed in 7.44s
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_mpea_alone_2_and_3_as_its_own_run[mpea_fixed-fixed_minimum]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[pooled]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[per_source:mpea]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:no_exclusions]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:tension_and_compression]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:six_batches_as_groups]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:same_alloy_1_at_pct]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:source_only_assignments]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:scope_not_confirmed_included]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:possible_duplicates_separate]
[m03_no_correction] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:conflicts_survivor_value]
[m03_no_correction] 46 failed, 89 passed in 45.10s
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
[m04_alloy_rule_one] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_the_model_is_the_one_supported_model
[m04_alloy_rule_one] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes
[m04_alloy_rule_one] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_the_two_validity_checks[rows0-False-False]
[m04_alloy_rule_one] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_the_two_validity_checks[rows1-False-False]
[m04_alloy_rule_one] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_method_iii_matches_an_independent_computation[single_size_alloys_added]
[m04_alloy_rule_one] 5 failed, 69 passed, 34 errors in 9.56s
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key5]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key8]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key9]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key12]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key13]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key16]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key17]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key18]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key19]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_permutation_stats.py::test_permuted_ids_and_insertion_order_give_identical_results[reference_data]
[m05_no_identity_sort] FAILED ../../../../../workspaces/hypocurate/tests/test_permutation_stats.py::test_permuted_ids_and_insertion_order_give_identical_results[controlled_extract]
[m05_no_identity_sort] 17 failed, 93 passed in 65.77s (0:01:05)
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_mpea_alone_2_and_3_as_its_own_run[mpea_fixed-fixed_minimum]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[pooled]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[per_source:mpea]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:no_exclusions]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:tension_and_compression]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:six_batches_as_groups]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:same_alloy_1_at_pct]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:source_only_assignments]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:scope_not_confirmed_included]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:possible_duplicates_separate]
[m06_df_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:conflicts_survivor_value]
[m06_df_groups] 30 failed, 105 passed in 22.06s
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_mpea_alone_2_and_3_as_its_own_run[mpea_fixed-fixed_minimum]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[pooled]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[per_source:mpea]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:no_exclusions]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:tension_and_compression]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:six_batches_as_groups]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:same_alloy_1_at_pct]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:source_only_assignments]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:scope_not_confirmed_included]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:possible_duplicates_separate]
[m07_two_sided] FAILED ../../../../../workspaces/hypocurate/tests/test_reference_numbers.py::test_every_reference_result_matches_the_reference_implementation[sensitivity:conflicts_survivor_value]
[m07_two_sided] 33 failed, 102 passed in 21.12s
[m08_coefficient_below_min]             message = database_message(error)
[m08_coefficient_below_min]         except IntegrityError as error:
[m08_coefficient_below_min]             message = database_message(error)
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option[one_alloy_two_sizes-fixed_minimum]
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option[single_group-fixed_minimum]
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_below_the_minimums_every_analysis_holds_counts_and_records_only
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_withheld_results_do_not_depend_on_the_outcome_values
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_fixed_option_with_one_group_withholds_even_the_coefficient
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_gap_facts_hold_no_text_and_no_outcome_value
[m08_coefficient_below_min] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_refuses_calibration_that_does_not_match_the_result
[m08_coefficient_below_min] 8 failed, 127 passed in 49.86s
[m09_label_sign_ignored] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_the_four_per_source_labels[per_source2-pooled2-conflicts]
[m09_label_sign_ignored] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_the_four_per_source_labels[per_source4-pooled4-conflicts]
[m09_label_sign_ignored] 2 failed, 46 passed in 3.16s
[m10_exploratory_ignored] results = {('effect_many_papers', 'fixed_minimum'): {'freeze_fingerprint': 'babdbfb3c1b502bee37c6710573e92284d46cec4e177e389226b...degrees of freedom; cluster-robust standard error by group with the small-sample correction', 'alpha': 0.05, ...}, ...}
[m10_exploratory_ignored] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_every_result_state_has_its_evidence_level[pooled7-use_available-exploratory-5]
[m10_exploratory_ignored] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key19]
[m10_exploratory_ignored] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_use_what_is_available_gives_an_exploratory_verdict_on_the_same_data
[m10_exploratory_ignored] 3 failed, 108 passed in 38.06s
[m11_copy_no_fp_check] FAILED ../../../../../workspaces/hypocurate/tests/test_completion.py::test_it_refuses_a_decision_of_another_freeze_and_logs_it
[m11_copy_no_fp_check] FAILED ../../../../../workspaces/hypocurate/tests/test_completion.py::test_a_run_with_a_freeze_refuses_a_decision_without_one
[m11_copy_no_fp_check] 2 failed, 5 passed in 15.89s
[m12_copy_recomputes] FAILED ../../../../../workspaces/hypocurate/tests/test_completion.py::test_it_copies_what_is_stored_and_never_recomputes
[m12_copy_recomputes] 1 failed, 6 passed in 18.00s
[m13_frozen_all_records] FAILED ../../../../../workspaces/hypocurate/tests/test_access_statistics.py::test_records_outside_the_frozen_sets_never_reach_statistics
[m13_frozen_all_records] 1 failed, 15 passed in 26.45s
[m14_statistics_at_curation] FAILED ../../../../../workspaces/hypocurate/tests/test_access_statistics.py::test_the_lists_are_the_owners_decision
[m14_statistics_at_curation] FAILED ../../../../../workspaces/hypocurate/tests/test_access_statistics.py::test_statistics_binds_at_no_other_stage[curation]
[m14_statistics_at_curation] 2 failed, 14 passed in 24.95s
[m15_gap_sees_records] FAILED ../../../../../workspaces/hypocurate/tests/test_access_statistics.py::test_the_lists_are_the_owners_decision
[m15_gap_sees_records] FAILED ../../../../../workspaces/hypocurate/tests/test_access_statistics.py::test_the_gap_facts_receive_no_outcome_value[analysis]
[m15_gap_sees_records] 2 failed, 14 passed in 20.75s
[m16_no_truncation_flag] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_a_negative_shift_estimate_is_set_to_zero_and_the_result_says_so
[m16_no_truncation_flag] 1 failed, 23 passed in 6.18s
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key1]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key2]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key3]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key4]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key5]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key8]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key9]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key16]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key17]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key18]
[m17_fixed_uses_estimates] FAILED ../../../../../workspaces/hypocurate/tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values[key19]
[m17_fixed_uses_estimates] 14 failed, 46 passed in 7.53s
[m18_flag_inverted] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_the_flag_is_raised_only_when_the_interval_excludes_alpha[0.061-0.084-over_confident]
[m18_flag_inverted] 1 failed, 23 passed in 4.57s
[m19_seed_by_id] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_the_seed_is_fixed_by_the_freeze_the_analysis_and_the_method
[m19_seed_by_id] FAILED ../../../../../workspaces/hypocurate/tests/test_calibration.py::test_the_estimated_method_uses_the_estimates_and_the_fixed_method_the_plan
[m19_seed_by_id] 2 failed, 22 passed in 5.83s
[m20_trigger_no_withheld] E         Actual message: '(psycopg.errors.CheckViolation) new row for relation "analysis_result" violates check constraint "ck_analysis_result_estimate_iff_check1"\nDETAIL:  Failing row contains (1, 1, pooled, 1, null, 6, 3, 3, 2, t, t, f, null, null, null, null, null, 2026-10-06 00:45:44.458228+00, f, 0, null).\n[SQL: INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, withheld) VALUES (%(run_id)s, %(scope)s, %(analysis_set_id)s, %(n_records)s, %(n_alloys)s, %(n_groups)s, %(resid_df)s, %(check1_passed)s, %(check2_passed)s, %(minimums_met)s, %(estimate)s, %(std_error)s, %(p_value)s, %(withheld)s)]\n[parameters: {\'run_id\': 1, \'scope\': \'pooled\', \'analysis_set_id\': 1, \'n_records\': 6, \'n_alloys\': 3, \'n_groups\': 3, \'resid_df\': 2, \'check1_passed\': True, \'check2_passed\': True, \'minimums_met\': False, \'estimate\': None, \'std_error\': None, \'p_value\': None, \'withheld\': False}]\n(Background on this error at: https://sqlalche.me/e/21/gkpj)'
[m20_trigger_no_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_computes_withheld_and_refuses_a_number_in_a_withheld_result
[m20_trigger_no_withheld] 1 failed, 26 passed in 43.53s
[m21_trigger_no_label_check]             _insert_result(engine, rid, label="agrees", estimate=1.0, std_error=1.0, p_value=0.1)
[m21_trigger_no_label_check]             _insert_result(engine, rid, n_groups=1, check2_passed=False, estimate=1.0, estimated_power=0.5)
[m21_trigger_no_label_check] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_refuses_a_label_on_a_pooled_result_and_power_without_inference
[m21_trigger_no_label_check] 1 failed, 26 passed in 42.51s
[m22_no_label_written]         except IntegrityError as error:
[m22_no_label_written]             message = database_message(error)
[m22_no_label_written] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates
[m22_no_label_written] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_a_marked_run_with_no_dataset_frozen_is_labelled_too
[m22_no_label_written] 2 failed, 25 passed in 43.44s
[m23_pooled_ungrouped_skipped] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics.py::test_a_record_without_a_group_is_refused_never_given_one
[m23_pooled_ungrouped_skipped] 1 failed, 47 passed in 4.30s
[m24_real_run_unfiltered] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates
[m24_real_run_unfiltered] 1 failed, 26 passed in 51.85s
[m25_second_analysis_allowed] reference = (Engine(postgresql+psycopg://hypocurate:***@localhost:5432/hypocurate_t_efb95d15dabb), 1, {'freeze_fingerprint': '3ec8...- 1) degrees of freedom; cluster-robust standard error by group with the small-sample correction', 'alpha': 0.05, ...})
[m25_second_analysis_allowed] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_a_second_analysis_is_refused_and_logged
[m25_second_analysis_allowed] 1 failed, 26 passed in 45.57s
```

## 13. Suite output

```
Local (Codespace):
1104 passed in 352.28s (0:05:52)

Test image (docker compose run --rm test, after docker compose build test):
1104 passed in 579.32s (0:09:39)
```
