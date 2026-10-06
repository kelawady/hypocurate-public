# Build step 7 — summary for review

Date: 2026-10-06. Branch: `step-07-statistics`. **Status (updated 2026-10-06 after the owner's second decision, informative papers in the factor and the degrees of freedom; 1,138 tests; code at `496644e`, GitHub Actions success: https://github.com/kelawady/hypocurate/actions/runs/37415861832): reviewed by the second model (ChatGPT, 2026-10-06: "not safe to merge", four findings and smaller points); the owner accepted all of them with a decision on informative papers; fixed (code at `fb5fd62`; GitHub Actions success, 1,131 passed, runtime image OK: https://github.com/kelawady/hypocurate/actions/runs/37403929929), each fix with tests that failed on the code before it; the whole suite passes (1,131 tests). Not merged; awaiting the re-check.** The first build was `d3da7c4` (1,104 tests; GitHub run https://github.com/kelawady/hypocurate/actions/runs/37398444475). The review is `docs/reviews/step07_review_chatgpt.md` (verbatim); the fixes are in section "Second-model review and fixes" and in `docs/reviews/step07_fix_packet.md`. **This summary describes the state after the fixes.** PRD Section 15, step 7, as the owner scoped it: the statistics module, the validity checks, data sufficiency, the verdict and per-run calibration.

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

## Second-model review and fixes (ChatGPT, 2026-10-06)

**Owner's decision (2026-10-06):** the minimum of 10 independent papers counts only informative papers: papers whose records help estimate the slope (non-zero grain-size variation after removing each alloy's average). Uninformative papers are kept and listed but not counted. The same count is used for validity check 2 (at least 2). Register entry `informative_groups`.

| Finding | Fix | Tests (failed on the code before the fix unless marked) |
|---|---|---|
| **1 (high).** An unestimable clustered uncertainty gave "supported" with p = 0: the reviewer's design (five alloys × six records, grain sizes 16, 16/9, 4, 4, 4, 4; only the first paper varies within alloys) gave k = 400, SE = 0, p = 0, level 6; its null simulation rejected 50.5% | Informative papers (the owner's decision): a paper counts when one of its records differs from its alloy's average transformed grain size by more than the numerical zero; check 2 and the paper minimum count these. Inference also needs a clustered SE that is finite and above a scale-aware numerical zero (`RELATIVE_ZERO` = 1e-10 of sqrt(Σỹ²/Σx̃²)); otherwise the coefficient alone, with `inference_reason` "insufficient_groups" or "uncertainty_not_estimable". Every simulated fit gets the same checks (no inference, never significant). The database: `n_groups_informative`, `inference_reason`, check 2's constraint an implication on the informative count, the trigger's minimum on the informative count | `test_the_reviewers_design_never_gives_a_verdict` (both options: fixed → withheld, level 3; use what is available → k = 400 only, level 4); `test_a_paper_is_informative_when_its_records_vary_after_removing_the_alloy_average`; `test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only`; `test_the_simulations_apply_the_same_check_to_each_simulated_fit`; `test_the_reviewers_design_through_the_database`; `test_the_database_counts_informative_groups_for_check_2_and_the_minimum`; `test_the_database_takes_an_uncertainty_that_cannot_be_estimated`. Guards (passed before; they stop the fix from overshooting): `test_small_real_noise_keeps_the_uncertainty_estimable`, `test_the_uncertainty_check_is_scale_aware` |
| **2 (medium).** The result trigger bounded the alloy count by the display label (rounded to 0.1 at.%) while the plan may round finer: Fe50.01Ni49.99 and Fe50.04Ni49.96 (both "Fe50Ni50") were refused under 0.01 at.% | The bound is removed (n_records ≥ 2 × n_alloys remains) | `test_two_alloys_with_one_display_label_are_stored` (end to end, three grain sizes each, `same_alloy_decimals` = 2: refused with "n_alloys cannot exceed…" before); `test_the_display_label_no_longer_bounds_the_alloy_count` (changed from a case of `test_stored_counts_must_be_consistent`, below) |
| **3 (medium).** 9.0 and 9.000000000000002 µm transform to one value: both checks passed, then `fit` raised ZeroDivisionError, which bypassed the stage's error handling | An alloy counts only when its transformed grain sizes differ by more than the numerical zero (`distinct_values`); `fit` refuses a zero predictor variation or a non-finite coefficient as a `StatisticsError`; the stage turns **any** exception into a logged refusal (`statistics_failed`, with the error's type and text) | `test_grain_sizes_equal_after_transformation_never_raise` (level 2, no exception); `test_nearly_equal_transformed_grain_sizes_are_not_distinct`; `test_an_unexpected_error_in_the_statistics_is_a_logged_refusal` (a ZeroDivisionError escaped before) |
| **4 (medium).** A perfect fit (RSS ≈ 9.3e-25) was taken for real scatter (≈ 2e-13 MPa) and calibrated | Scatter not estimable when RSS_F ≤ RELATIVE_ZERO² × Σỹ² (the outcome's spread within alloys) | `test_an_exact_fit_has_no_estimable_scatter`; guard (passed before): `test_small_real_noise_gives_an_estimable_scatter` (σ = 0.01 MPa is estimated) |
| Smaller: what the intervals cover | Every calibration carries `interval_note`; the estimated one: "Monte Carlo (simulation) uncertainty only, not uncertainty in the estimated scatter and shift … a diagnostic … not independent validation" | `test_every_estimated_calibration_states_what_its_intervals_cover` |
| Smaller: detection rates both ways | `detection` per analysis: fixed and estimated, each with its false-positive share and the noise used; `estimated_power` (fixed) and `estimated_power_estimated_noise` stored; the estimated one withheld below the minimums (the database refuses it on a withheld result); `detection_note`: detection rates of the nominal 5% test, not power for a test shown to keep 5% | `test_detection_rates_are_reported_both_ways_with_the_false_positive_shares`; `test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld`; `test_the_estimated_detection_rate_is_never_stored_for_a_withheld_result` |
| Smaller: a zero coefficient's own reason | `label_reason`: "no_p_value", "pooled_without_decision" or "zero_coefficient", present exactly with "not enough data" (stored and checked by the database) | `test_a_zero_coefficient_has_its_own_reason` (5 cases); `test_a_label_reason_is_stored_exactly_with_not_enough_data` |
| Smaller: evidence level required | `ck_run_evidence_level_iff_completed`: present exactly on a completed run | `test_a_completed_run_needs_its_evidence_level` |
| Smaller: records without a group | Unchanged: fails closed; the decision stays open (register note added) | — |

**Owner's second decision (2026-10-06):** the standard error's small-sample factor and the t distribution's degrees of freedom count informative papers only, the same count as validity check 2, in the real fits and in every simulated fit; CLAUDE.md rule 6 now reads "(informative papers − 1) degrees of freedom" (approved by the owner). Register entry `informative_groups_in_inference`; `cluster_robust_se` and `one_sided_test` reworded (earlier wording in history).

| Change | Tests (failed on the code before the change unless marked) |
|---|---|
| `fit`: the clustered variance sums the scores of informative groups only; factor G/(G−1) × (N−1)/(N−K) and df G − 1 with G the informative groups. `significant_count` (every simulated fit): the same | `tests/test_informative_inference.py`: on a design with 3 informative and 6 uninformative papers, `test_the_factor_and_degrees_of_freedom_count_informative_papers_only` (df 2, not 8; k, SE and p equal an **independent explicit sandwich** written test-side with numpy, `reference_stats.fit_informative`); `test_the_result_is_more_cautious_than_counting_every_paper` (against statsmodels with all nine clusters: same k, SE larger by exactly √(4/3), fewer df, larger p); `test_every_simulated_fit_counts_informative_papers_only` (200 simulated fits decided exactly as the independent sandwich: 50 significant; the old code gave 125). Regressions (passed before): `test_the_design_has_three_informative_and_six_uninformative_papers`; `test_where_every_paper_is_informative_nothing_changes` (three generated designs: statsmodels and the independent sandwich both agree with the package to 1e-9) |

The test-side statsmodels comparison is kept for designs where every paper is informative (the fixed set and the reference numbers); the independent sandwich covers the other case. **Reference numbers: still identical.** The reference run's full output (counts, k, SE, p, labels, reasons, simulated counts under both calibrations, detection rates, decision) is byte-identical to the previous round, because every paper of every reference set is informative. Mutations: switching the factor, the df, the simulated factor or the simulated df back to all groups is caught (4 of 5). Putting the uninformative groups' scores back into the sum survives; it is an equivalent mutation, since an uninformative group's records sit within the numerical zero of their alloy's average, so its score is zero (at most about 1e-20 of the variance), below any testable tolerance. The exclusion is kept because it states the rule exactly.

**What the fixes do not do.**
- A withheld analysis is judged on its counts only (no outcome is used, so no standard error is computed); its check 2 can only fail on the counts.
- The numerical zero (1e-10 relative) is not a scientific threshold: rounding residue is about 1e-16 of the scale, and the guards show that noise of 0.001 MPa on hundreds of MPa is still estimable.

**Reference numbers after the fixes: none changed.** Recomputed on the reference run (pooled, both per-source results, all eight sensitivity sets): every coefficient, standard error and p-value is bit-identical, every simulated count under both calibrations is identical, and the freeze fingerprint is unchanged (`3ec87f58…`). **The group count stays 20, and all 20 groups are informative**: every paper in the pooled set has at least one record whose transformed grain size differs from its alloy's average. That is true of each MPEA paper (19 of 19) and of the Texas A&M dataset (1 of 1); every sensitivity set's groups are all informative too. The paper minimum is therefore still met (20 ≥ 10) and check 2 still passes. The estimated-noise detection rates, now reported: pooled 97.2% (fixed 100%), MPEA 96.1% (fixed 100%).

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
1. **The fit's records.** Sort by stable identity (source-version fingerprint, origin key, item index). Keep alloys with at least two grain sizes among this analysis's records that are distinct after the transformation by more than the numerical zero (`MODEL_MIN_GRAIN_SIZES = 2`); count the others as "not used in this fit". Mark each group informative when one of its records differs from its alloy's average transformed grain size by more than the numerical zero; list the uninformative ones.
2. **The estimate.** x = d^-1/2 (the plan's transformation); remove each alloy's mean from x and y; k = Σ x̃ỹ / Σ x̃². The same as OLS with one intercept per alloy.
3. **The standard error.** Per group g, s_g = Σ_{i∈g} x̃_i e_i with e = ỹ − k x̃; V = Σ s_g² / (Σ x̃²)² × G/(G−1) × (N−1)/(N−K), K = alloys + 1, the sum and G over informative groups (statsmodels' cluster correction when every group is informative).
4. **The test.** t = k / √V; p = P(T > t), T ~ t(G − 1) with G the informative groups; "supported" exactly when p < α (the plan's, 0.05).
5. **Validity checks.** Check 1: at least one alloy with two distinct grain sizes. Check 2: N − alloys − 1 ≥ 1, at least 2 informative groups, and an SE that is finite and above RELATIVE_ZERO × sqrt(Σỹ²/Σx̃²). Check 1 only: k alone, with the reason (`insufficient_groups` or `uncertainty_not_estimable`).
6. **Minimums,** on the fit's counts: records, alloys (each with two or more grain sizes), informative groups, residual df.
7. **Groups** come from the same function Inclusion and the freeze counts use (`eligibility.group`, the set's own grouping), and alloys from `eligibility.alloy` (the set's same-alloy rule).

## Result states

The pooled analysis decides; per-source and sensitivity results go through the same function and only describe. Precedence: no dataset frozen; below the minimums (fixed option); not fitted; coefficient only; exploratory; sufficient.

| State (level) | Inputs that lead to it | Stored | Withheld |
|---|---|---|---|
| Sufficient with a verdict (6) | Validity checks pass; minimums met (either option) | Counts, both checks, minimums, k, SE, t, df, p, α, estimated power, both calibrations; decision: outcome sufficient, verdict "supported" (p < α) or "not supported" "under the stated model, in the sources searched", not exploratory | — |
| Exploratory (5) | "Use what is available", checks pass, a minimum missed | As above, `exploratory` true, label "exploratory" | — |
| Coefficient only (4) | Check 1 passes, check 2 fails (fewer than 2 informative groups, no residual df, or an unestimable SE), and the minimums do not withhold (use what is available, or a plan whose own minimums are met) | Counts (all and informative groups, the uninformative ones listed), checks, k only, the reason; calibration "unavailable" with that reason; outcome insufficient | SE, p, verdict, power, calibration |
| Below the minimums, fixed option (3) | Fixed option and the pooled fit misses any minimum, whether check 2 passes or fails | Run-wide: every analysis holds its counts against each minimum, the minimums missed and the records found (stable identities); label "data found; not enough to test"; estimated power where check 2 passes (no outcome used); calibration "unavailable: below minimums" (or the validity reason if a check fails); gap facts; outcome insufficient | Everything computed from outcomes, in every analysis: k, SE, t, p, verdict, estimated calibration |
| Not fitted (2) | Check 1 fails and the minimums do not withhold. The pooled set of a frozen run always has an alloy with two grain sizes (eligibility rule 8), so this is reachable only in the pure function and in per-source or sensitivity analyses | Counts; calibration "unavailable: coefficient not fitted" | k and everything after it |
| No dataset frozen (1) | No eligible record | Decision (no freeze fingerprint); gap facts; the run-level calibration row "unavailable: no dataset frozen" written at the freeze | Everything else |
| Marked test run (any level) | Any state, on a run with `constructed_test_data` | The same, plus "test run: includes constructed data" on every analysis and calibration row (the database checks: present exactly when the run is marked) and in the `statistics` and `gap_facts` stage results; keeps its level | Left out of every aggregate through `results.REAL_RUN` |

Calibration rows per analysis: `fixed` and `estimated`, each "computed" or "unavailable" with one reason: `coefficient_not_fitted`, `insufficient_groups`, `uncertainty_not_estimable` (the result's inference reason), `below_minimums`, or, for the estimated method only, `scatter_not_estimable` / `shift_not_estimable`. Every computed calibration states what its intervals cover (`interval_note`).

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


**Review round (2026-10-06): 34 new tests** (1,138 in all; 7 of them in `tests/test_informative_inference.py` for the owner's second decision): `tests/test_statistics_boundaries.py` (19) and eight database tests in `test_analysis_stage.py` (7) and `test_completion.py` (1). Changed, none removed:
- `test_data_model.py`: the case `(4, 2, 2, "cannot exceed the distinct alloys")` of `test_stored_counts_must_be_consistent` became `test_the_display_label_no_longer_bounds_the_alloy_count` (the bound is removed on the reviewer's finding 2; the new test checks such a result is stored); raw inserts give `n_groups_informative`; raw completions give an evidence level (one test's completion uses level 6 so that the verdict constraint is still the one that refuses).
- `test_concurrency.py`: the completion statement gives an evidence level.
- `test_migrations_step7.py`: `test_the_new_result_function_keeps_every_check_of_0001` lists three changed checks (record count, display-label bound removed, minimum on informative groups).
- `test_statistics.py`, `test_calibration.py`: `Design.inference_valid` is now `counts_allow_inference` (counts alone no longer decide check 2); the fake calibration in `test_calibration_never_changes_the_outcome_or_the_verdict` carries noise values (the detection report reads them).
- `test_assumptions.py`: `fixed_minimums` is decided on 2026-10-06 (the informative-paper wording), with the 2026-10-05 wording checked in its history.
- Helpers: `model_builder.result()` takes `informative` (default: every group); `model_builder.complete()` gives an evidence level consistent with the outcome; the access world's original run gives its informative count; `stats_world.run_on` takes plan `rules`.

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


**Review round (2026-10-06):** 13 mutations of the fixes, each caught:

| Mutation | Result |
|---|---|
| f01: every group counted as informative | 4 failed, 49 passed |
| f02: no numerical-zero check on the SE | 1 failed, 18 passed |
| f03: simulations without the validity check | 1 failed, 18 passed |
| f04: raw grain sizes distinct (not transformed) | 1 failed, 18 passed |
| f05: any positive residual is scatter | 1 failed, 18 passed |
| f06: only StatisticsError caught | 1 failed, 33 passed |
| f07: trigger: paper minimum on all groups | 2 failed, 40 passed |
| f08: database: check 2 on all groups | 2 failed, 32 passed |
| f10: zero coefficient without its reason | 2 failed, 17 passed |
| f11: estimated detection rate not withheld | 1 failed, 18 passed |
| f12: no interval note on the estimated method | 1 failed, 18 passed |
| f13: evidence level not required | 1 failed, 7 passed |
| f09: trigger: display-label bound put back | 2 failed, 185 passed |

f09's first attempt broke the SQL through shell quoting and tested nothing; it was re-run correctly (output in the fix packet). The first round's 25 mutations were not re-run on the fixed code.

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


**Review round (2026-10-06): 111 entries** (with the owner's second decision: `informative_groups_in_inference`; `cluster_robust_se`, `one_sided_test` reworded). New: `informative_groups` (the owner's decision), `numerical_zero`. Reworded, with the earlier wording in history: `validity_checks`, `fixed_minimums`, `per_source_labels` (reasons), `smallest_effect` (detection both ways), `fit_alloy_rule` (transformed distinctness). Notes: `calibration_noise_levels` (interval note, perfect fit), `calibration_simulation` (checks in each simulated fit), `evidence_level_scale` (required), `records_without_group` (the reviewer's question).

## Decisions I made while building (for the owner and the reviewer)

1. **Records without a group** (now the open register entry `records_without_group`). The marked run with the controlled extract puts two extract records without a DOI into `possible_duplicates_separate`. A clustered standard error needs every record in a group, and the register says no group is invented. Code fails closed:
   - if the pooled set has such a record, the analysis stage refuses (logged, `records_without_group`);
   - a per-source or sensitivity analysis with such a record is listed under `not_analysed` with the count, and nothing is stored for it.
   
   No record of the reference sets lacks a group. **Owner's decision needed** before step 8.
2. **The gap facts read through their own code role** (`gap_facts`), not the Statistics role. That keeps Statistics' list exactly as approved, and the gap facts can be shown to read no outcome value.
3. **Real results by a code condition, not a database view** (`results.REAL_RUN`). A view would have changed the schema tests of step 3; the condition is one named place.
4. ~~The evidence level is not required by the database on a completed run.~~ Superseded by the review: it is required (`ck_run_evidence_level_iff_completed`); the test helpers that complete runs directly now give one.
5. **The calibration reason when a run is withheld and a check fails** is the validity reason (`coefficient_not_fitted`, `insufficient_groups`), not `below_minimums`. The trigger enforces this precedence.
6. **Label edge rules:** pooled without a decision, or a coefficient of exactly zero, gives "not enough data", now with its reason (`label_reason`).
7. ~~A zero standard error gives p = 0 when k > 0.~~ Superseded by the review (finding 1): an SE at or below the numerical zero gives no inference (coefficient only).

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

1. **Second-model re-check** of the fixes (the review was 2026-10-06), then the owner's sign-off. `calibration_noise_levels` moves to "in force" after it.
2. **Owner:** `records_without_group` (before step 8; the reviewer asks whether a permitted coefficient-only result should stay available when grouping is missing); `curator_tabular_sources` (before step 8, from step 6).
3. **Step 8:** the Analyst explains the stored record and gap facts only; the orchestrator calls `copy_decision` after the Analyst; how "partly sufficient" reaches the run.
4. **Step 10:** the plot from the stored records found (below the minimums: raw data, no fitted line); the label and `REAL_RUN` on every screen and list; the workbook.
5. **Carried:** the step 5 and step 6 open items for steps 8 to 10; live registration of sources (owner).

## Questions for the re-check

0. Is counting informative papers in the small-sample factor and the degrees of freedom (the owner's second decision) implemented consistently in the real fits and every simulated fit, and is the independent sandwich a fair check of it?
1. Are the four findings closed: can any design still give a verdict, a p-value or a standard error without at least two informative papers and an estimable uncertainty, in a real fit or a simulated one?
2. Is "informative paper" implemented as the owner defined it, and is the numerical zero (1e-10 of the natural scale) applied consistently and never acting as a scientific threshold?
3. Does migration 0004, as changed, enforce check 2, the reasons and the evidence level completely, and is the downgrade still exact?
4. Is anything new computed from outcome values below the minimums (detection rates, reasons, notes)?
5. Is any claim stronger than the code supports?

## Questions for the first review (answered in its text)

1. Is the estimated calibration (method III, truncation recorded, unavailable when not estimable) a sound and honestly described departure from PRD 5.10, and can it influence any decision?
2. Can Statistics or the gap facts reach anything beyond their lists: a record outside the frozen sets, a value as reported, another run's data, or (gap facts) an outcome value?
3. Does migration 0004 enforce the withheld rule, the labels and the calibration rules completely, and is it safe with the previous release's code and on the live database?
4. Under the fixed option below the minimums, does anything stored (results, calibration, stage outputs, gap facts) carry a number computed from outcome values?
5. Are the two tolerance tiers justified, and does every reference result come from the stated path?
6. Is any claim stronger than the code supports?
