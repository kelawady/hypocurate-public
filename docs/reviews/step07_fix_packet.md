# Build step 7 — fix packet for the second model's re-check

Date: 2026-10-06. Branch: `step-07-statistics`. Code reviewed: commit `496644e` (this packet and the summary update are added in the next commit and change no code). GitHub Actions on that commit: success (1,138 passed, runtime image OK), https://github.com/kelawady/hypocurate/actions/runs/37415861832.

Generated from the files on disk by a script, so every diff and output below is quoted exactly.

## How to use this packet

Your review of 2026-10-06 (`docs/reviews/step07_review_chatgpt.md`) found four problems and smaller points; the owner accepted all of them and decided that the paper minimum and validity check 2 count only informative papers. **The owner then decided that the standard error's small-sample factor and the t distribution's degrees of freedom count informative papers only too** (commit `496644e`; CLAUDE.md rule 6 reworded with the owner's approval). This packet holds what changed since your review: the fix table, the per-commit diffs, the recomputed reference numbers, the mutation checks and the suite output. The full summary (`docs/reviews/step07_summary.md`) describes the state after the fixes; the first packet (`docs/reviews/step07_review_packet.md`) holds the first build. Your review is advice; the test suite is the gate.

The first three fix commits are by area, not one per finding: the fixes share files, and splitting them per finding would need interactive staging.

Please check in particular the questions at the end.

## 1. The fixes (from the summary)

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


## 2. Commits

```
496644e Step 7: informative papers in the small-sample factor and the degrees of freedom (owner, 2026-10-06)

The clustered variance sums informative groups' scores; G/(G-1) and the t distribution's G - 1 use the
informative count, in the real fits and every simulated fit. CLAUDE.md rule 6 reworded (approved by the
owner). Register: informative_groups_in_inference; cluster_robust_se and one_sided_test reworded.
tests/test_informative_inference.py: 3 of its 7 tests failed before the change (df 8 instead of 2; SE
not larger than the all-papers SE; 125 simulated rejections where the independent sandwich gives 50).
Reference numbers: the reference run's output is byte-identical (every paper is informative).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

69407e8 Step 7: summary after the review fixes, and the fix packet

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

fb5fd62 Step 7 review fixes: assumptions register (informative_groups, numerical_zero; reworded entries)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

ee99d9d Step 7 review fixes: migration 0004 (no display-label bound; informative groups, inference and label reasons, estimated detection rate, evidence level required)

Finding 2 and the database side of finding 1 and the smaller points. 0004 has not run on the live
database (still at 0003), so it is changed in place. The 8 new database tests failed before the fix.
Helpers and raw statements give the informative count and the evidence level; one data-model case
(display-label bound) becomes a test that the bound is gone.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

31d3368 Step 7 review fixes: informative papers, estimable uncertainty, numerical rank and zero; smaller points

Findings 1, 3 and 4 of the second-model review, the owner's decision on informative papers
(2026-10-06), and the smaller points (interval note, detection rates both ways, label reason).
tests/test_statistics_boundaries.py: 17 of its 19 tests failed before the fix; the other two
(small real noise stays estimable; the check is scale-aware) are guards against an overshoot.
test_statistics.py and test_calibration.py: renamed property, and a fake calibration given noise values.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

### Commit `31d3368`

```
31d3368 Step 7 review fixes: informative papers, estimable uncertainty, numerical rank and zero; smaller points

 hypocurate/pipeline/analysis.py     |  46 +++++---
 hypocurate/pipeline/calibration.py  |  48 ++++++--
 hypocurate/pipeline/statistics.py   | 125 +++++++++++++++-----
 hypocurate/pipeline/writes.py       |   1 +
 tests/test_calibration.py           |   5 +-
 tests/test_statistics.py            |   4 +-
 tests/test_statistics_boundaries.py | 219 ++++++++++++++++++++++++++++++++++++
 7 files changed, 391 insertions(+), 57 deletions(-)
```

```diff
diff --git a/hypocurate/pipeline/analysis.py b/hypocurate/pipeline/analysis.py
index 3910c50..bc313b9 100644
--- a/hypocurate/pipeline/analysis.py
+++ b/hypocurate/pipeline/analysis.py
@@ -75,6 +75,15 @@ def _unavailable(reason: str) -> dict:
     return {"status": "unavailable", "reason": reason}
 
 
+def _rates(c: Mapping) -> dict:
+    """The detection rate beside the false-positive share, under one method's assumptions."""
+    if c["status"] != "computed":
+        return {"unavailable": c["reason"]}
+    return {"detection": c["effect"]["share"], "detection_ci": [c["effect"]["ci_low"], c["effect"]["ci_high"]],
+            "false_positive": c["null"]["share"], "false_positive_ci": [c["null"]["ci_low"], c["null"]["ci_high"]],
+            "scatter": c["assumptions"]["scatter"], "shift": c["assumptions"]["shift"]}
+
+
 def analyse(plan: Mapping, data: Mapping) -> dict:
     """Every analysis of the run, its calibrations, and the decision (the record of statistical
     significance). `data` is `frozen_analysis_data`."""
@@ -109,23 +118,31 @@ def analyse(plan: Mapping, data: Mapping) -> dict:
             entry["label_text"] = st.BELOW_MINIMUMS_LABEL
     pooled = entries[0]
     for entry in entries:
-        entry["label"] = st.label(entry, pooled, alpha) if entry["scope"] == "per_source" else None
+        per_source = entry["scope"] == "per_source"
+        entry["label"] = st.label(entry, pooled, alpha) if per_source else None
+        entry["label_reason"] = st.label_reason(entry, pooled) if per_source else None
         d = designs[entry["analysis"]]
-        entry["estimated_power"], entry["power_label"] = None, None
-        if not d.inference_valid:
-            reason = "coefficient_not_fitted" if not d.coefficient_fitted else "insufficient_groups"
+        entry["estimated_power"], entry["estimated_power_estimated_noise"], entry["power_label"] = None, None, None
+        entry["detection"], entry["detection_note"] = None, None
+        if not entry["checks"]["inference_valid"]:
+            reason = entry["inference_reason"]
             entry["calibration"] = {"fixed": _unavailable(reason), "estimated": _unavailable(reason)}
             continue
         # The fixed method uses no outcome value: its effect world is the estimated power, shown
         # even below the minimums (owner, decision 5).
         fixed = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "fixed")
         entry["estimated_power"], entry["power_label"] = fixed["effect"]["share"], st.POWER_LABEL
+        entry["detection_note"] = st.DETECTION_NOTE
         if withheld:
             entry["calibration"] = {"fixed": _unavailable("below_minimums"),
                                     "estimated": _unavailable("below_minimums")}
+            entry["detection"] = {"fixed": _rates(fixed), "estimated": {"withheld": True}}
         else:
-            entry["calibration"] = {"fixed": fixed, "estimated": cal.calibrate(d, plan["calibration"], alpha, fp,
-                                                                                entry["analysis"], "estimated")}
+            estimated = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "estimated")
+            entry["calibration"] = {"fixed": fixed, "estimated": estimated}
+            entry["detection"] = {"fixed": _rates(fixed), "estimated": _rates(estimated)}
+            if estimated["status"] == "computed":
+                entry["estimated_power_estimated_noise"] = estimated["effect"]["share"]
     return {"freeze_fingerprint": fp, "model": plan["model"]["name"],
             "test": "one-sided t test of k > 0 against t with (groups - 1) degrees of freedom; "
                     "cluster-robust standard error by group with the small-sample correction",
@@ -172,8 +189,9 @@ def _read(engine: Engine, run_id: int, role: str) -> tuple[dict, str]:
 _RESULT = text(
     "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, resid_df, "
     "check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, estimated_power, label, withheld, "
-    "n_records_not_used, test_run_label) VALUES (:r, :scope, :set, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, "
-    ":p, :pw, :lab, :wh, :nu, :tl) RETURNING id")
+    "n_records_not_used, test_run_label, n_groups_informative, inference_reason, label_reason, "
+    "estimated_power_estimated_noise) VALUES (:r, :scope, :set, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, "
+    ":p, :pw, :lab, :wh, :nu, :tl, :gi, :ir, :lr, :pe) RETURNING id")
 _CALIBRATION = text(
     "INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, n_simulations, "
     "seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, confidence_flag, "
@@ -200,10 +218,11 @@ def run_statistics(engine: Engine, run_id: int) -> dict:
         data, _ = _read(engine, run_id, ROLE)
         try:
             record = analyse(data["plan"]["content"], data["frozen_analysis_data"])
-        except st.StatisticsError as error:
-            code = "records_without_group" if str(error) == "records_without_group" else "changed_since_read"
-            log_refusal(engine, run_id, ROLE, "run_statistics", code, str(error))
-            raise Refused("run_statistics", code, str(error)) from None
+        except Exception as error:  # review finding 3: nothing bypasses the stage's error handling
+            code = "records_without_group" if isinstance(error, RecordsWithoutGroup) else "statistics_failed"
+            message = f"{type(error).__name__}: {error}"
+            log_refusal(engine, run_id, ROLE, "run_statistics", code, message)
+            raise Refused("run_statistics", code, message) from None
         pooled = record["analyses"][0]
         facts = gap_facts(gap, pooled["minimums"])
         plan_fp, fp = data["plan"]["fingerprint"], record["freeze_fingerprint"]
@@ -235,7 +254,8 @@ def run_statistics(engine: Engine, run_id: int) -> dict:
                 n=c["n_records"], a=c["n_alloys"], g=c["n_groups"], df=c["resid_df"],
                 c1=e["checks"]["coefficient_fitted"], c2=e["checks"]["inference_valid"], mm=e["minimums_met"],
                 est=e["estimate"], se=e["std_error"], p=e["p_value"], pw=e["estimated_power"], lab=e["label"],
-                wh=e["withheld"], nu=c["n_records_not_used"], tl=label)).scalar_one()
+                wh=e["withheld"], nu=c["n_records_not_used"], tl=label, gi=c["n_groups_informative"],
+                ir=e["inference_reason"], lr=e["label_reason"], pe=e["estimated_power_estimated_noise"])).scalar_one()
             for method in ("fixed", "estimated"):
                 conn.execute(_CALIBRATION, _calibration_row(run_id, rid, method, e["calibration"][method], label))
         output = {**record, "test_run_label": label}
diff --git a/hypocurate/pipeline/calibration.py b/hypocurate/pipeline/calibration.py
index 4504f23..aa91b5c 100644
--- a/hypocurate/pipeline/calibration.py
+++ b/hypocurate/pipeline/calibration.py
@@ -15,8 +15,9 @@ the rules lock by the plan's `calibration` part; no person or agent chooses a va
   from PRD 5.10, which fixes them in advance; it is a safeguard change reviewed by a second model.
   1. Fit the locked model (alloy intercepts and k × x): residual sum of squares RSS_R, rank r_R.
   2. Fit it with one intercept per group added: RSS_F, rank r_F.
-  3. σe² = RSS_F / (N - r_F). Not estimable when N <= r_F, or when RSS_F is zero (a perfect fit
-     gives no scatter to simulate).
+  3. σe² = RSS_F / (N - r_F). Not estimable when N <= r_F, or when RSS_F is at most the numerical
+     zero of the outcome's spread within alloys (RSS_F <= RELATIVE_ZERO² × Σ ỹ²): a perfect fit,
+     whose residue is rounding, gives no scatter to simulate (review finding 4).
   4. σu² = max(0, (RSS_R - RSS_F - (r_F - r_R) σe²) / tr(Z'M_R Z)), where Z is the group
      membership matrix and M_R = I - P_R removes what the locked model explains. Not estimable
      when the trace is zero (the groups are entirely explained by alloys and grain sizes). A
@@ -40,7 +41,17 @@ the result; draws are assigned to records in stable-identity order (`statistics.
 and insertion order cannot change a share.
 
 **Estimated power** (owner, 2026-10-05, decision 5) is the effect world's share of the fixed
-method, labelled "estimated power under the stated assumptions". It uses no outcome value.
+method, labelled "estimated power under the stated assumptions". It uses no outcome value. The
+detection rate is reported both ways (review, smaller point), each beside its false-positive share:
+fixed (shown also below the minimums) and estimated (withheld below the minimums). Both are detection
+rates of the nominal 5% test, not power for a test shown to keep false positives at 5%.
+
+**What the intervals cover**: Monte Carlo uncertainty only. For the estimated method they do not
+cover uncertainty in the estimated scatter and shift; it is a diagnostic conditional on the estimate,
+not independent validation (stated with every result, `interval_note`).
+
+**Each simulated fit gets the real fit's validity checks**: a simulated standard error that is not
+finite or not above the numerical zero gives no inference and is not counted as significant.
 """
 from __future__ import annotations
 
@@ -51,7 +62,7 @@ from typing import Mapping
 import numpy as np
 from scipy import stats
 
-from hypocurate.pipeline.statistics import Design, demeaned, small_sample_factor
+from hypocurate.pipeline.statistics import RELATIVE_ZERO, Design, demeaned, small_sample_factor
 
 CONFIDENCE = 0.95
 FLAG_WORDING = {
@@ -61,6 +72,11 @@ FLAG_WORDING = {
 }
 # Relative tolerances of the estimator's linear algebra (numerical zero).
 TRACE_TOLERANCE = 1e-9
+# What the intervals cover (review, smaller point): stated with every calibration.
+INTERVAL_NOTE_FIXED = "The intervals cover Monte Carlo (simulation) uncertainty only."
+INTERVAL_NOTE_ESTIMATED = ("The intervals cover Monte Carlo (simulation) uncertainty only, not uncertainty in the "
+                           "estimated scatter and shift. This is a diagnostic conditional on the estimated noise "
+                           "(a shift truncated at zero biases it), not independent validation.")
 
 
 def seed(freeze_fingerprint: str, analysis: str, method: str) -> int:
@@ -86,7 +102,11 @@ def confidence_flag(low: float, high: float, alpha: float) -> str:
 
 def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
     """How many rows of `outcomes` (simulations × records) the locked test finds significant:
-    the same estimator, standard error, correction and one-sided t test as `statistics.fit`."""
+    the same estimator, standard error, correction, validity checks and one-sided t test as
+    `statistics.fit`. A simulated fit whose standard error is not finite or not above the numerical
+    zero gives no inference, so it is never significant (review finding 1)."""
+    if not d.counts_allow_inference:
+        return 0
     xd = demeaned(d.x, d.alloy, d.n_alloys)
     sxx = float(xd @ xd)
     yd = demeaned(outcomes, d.alloy, d.n_alloys)
@@ -97,9 +117,12 @@ def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
     scores = (e * xd[None, :]) @ groups
     variance = (scores ** 2).sum(axis=1) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
     with np.errstate(divide="ignore", invalid="ignore"):
-        t = np.where(variance > 0, k / np.sqrt(variance), np.where(k > 0, np.inf, -np.inf))
+        se = np.sqrt(variance)
+        scale = np.sqrt((yd ** 2).sum(axis=1) / sxx)
+        valid = np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)
+        t = np.where(valid, k / np.where(valid, se, 1.0), 0.0)
     p = stats.t.sf(t, d.n_groups - 1)
-    return int(np.count_nonzero(p < alpha))
+    return int(np.count_nonzero(valid & (p < alpha)))
 
 
 def simulate(d: Design, scatter: float, shift: float, smallest_effect: float, n_simulations: int,
@@ -139,9 +162,13 @@ def henderson_iii(d: Design) -> dict:
     q, _ = np.linalg.qr(reduced)
     residual_groups = groups - q @ (q.T @ groups)
     trace = float((residual_groups ** 2).sum())
+    within = demeaned(d.y, d.alloy, d.n_alloys)
+    tss_within = float(within @ within)
     out = {"estimation": "henderson_iii", "rss_reduced": rss_r, "rank_reduced": rank_r, "rss_full": rss_f,
-           "rank_full": rank_f, "trace": trace, "n_records": n}
-    if n <= rank_f or not rss_f > 0:
+           "rank_full": rank_f, "trace": trace, "n_records": n, "tss_within_alloys": tss_within}
+    # Review finding 4: a residual at most the numerical zero of the outcome's within-alloy spread is
+    # rounding residue (a perfect fit), not scatter.
+    if n <= rank_f or not (math.isfinite(rss_f) and rss_f > (RELATIVE_ZERO ** 2) * tss_within):
         return {**out, "reason": "scatter_not_estimable"}
     scatter_sq = rss_f / (n - rank_f)
     out["scatter_squared"] = scatter_sq
@@ -159,7 +186,8 @@ def calibrate(d: Design, calibration: Mapping, alpha: float, freeze_fingerprint:
     numbers, or (estimated only) 'unavailable' with the reason the noise cannot be estimated."""
     assumptions = {"method": method, "smallest_effect": calibration["smallest_effect"],
                    "n_simulations": calibration["n_simulations"], "alpha": alpha, "errors": "normal",
-                   "design": "fixed: the fit's records, alloys, groups and grain sizes"}
+                   "design": "fixed: the fit's records, alloys, groups and grain sizes",
+                   "interval_note": INTERVAL_NOTE_FIXED if method == "fixed" else INTERVAL_NOTE_ESTIMATED}
     if method == "fixed":
         scatter, shift = calibration["scatter"], calibration["shift"]
         assumptions.update(scatter=scatter, shift=shift, source="the locked plan")
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index f2d460a..f7234bb 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -12,15 +12,30 @@ freedom, at the plan's threshold; "supported" exactly when p < alpha (register
 'p_threshold_comparison').
 
 **Which records a fit uses** (owner, 2026-10-05, decision 7): only alloys with at least
-`MODEL_MIN_GRAIN_SIZES` distinct grain sizes among the analysis's own records. This is the model's
-own condition, applied to grain sizes only; the frozen set is not changed and the others are
-reported as "not used in this fit". **The minimums are counted on the records the fit uses**
-(owner, 2026-10-05).
+`MODEL_MIN_GRAIN_SIZES` distinct grain sizes among the analysis's own records, distinct after the
+transformation by more than the numerical zero (review finding 3: 9.0 and 9.000000000000002 µm give
+the same d^-1/2). This is the model's own condition, applied to grain sizes only; the frozen set is
+not changed and the others are reported as "not used in this fit". **The minimums are counted on
+the records the fit uses** (owner, 2026-10-05).
+
+**Informative papers** (owner, 2026-10-06; register 'informative_groups'): a group is informative
+when at least one of its records differs from its alloy's average transformed grain size by more
+than the numerical zero, so that the group helps estimate the slope. Uninformative groups stay in
+the fit and are listed, but are not counted for the paper minimum or for validity check 2. The
+standard error's small-sample factor and the t distribution's degrees of freedom still use every
+group of the fit (statsmodels' definition, CLAUDE.md rule 6).
 
 **The two validity checks** can never be waived (CLAUDE.md rule 5): (1) a coefficient can be fitted
 when at least one alloy has two distinct grain sizes; (2) inference is valid with at least 1
-residual degree of freedom (records - alloys - 1) and at least 2 independent groups. Check 1 only:
-the coefficient alone, no uncertainty, no p-value, no verdict.
+residual degree of freedom (records - alloys - 1), at least 2 informative groups, and a clustered
+standard error that is finite and above the scale-aware numerical zero (review finding 1). Check 1
+only: the coefficient alone, no uncertainty, no p-value, no verdict, with the reason.
+
+**Numerical zero** (`RELATIVE_ZERO`, register 'numerical_zero'): a quantity counts as zero when it is
+at most `RELATIVE_ZERO` times its natural scale in the same units: a predictor contrast against the
+largest transformed grain size; a standard error against sqrt(Σ ỹ² / Σ x̃²), the slope scale of the
+data. Rounding residue is about 1e-16 of the scale; any real measurement scatter is many orders above
+1e-10.
 
 **Below the minimums under the fixed option** (owner, 2026-10-05, decision 1): when the pooled fit
 misses any minimum, every analysis of the run is withheld: counts against each minimum, which were
@@ -44,6 +59,8 @@ from scipy import stats
 
 # The model's own alloy condition (CLAUDE.md rule 6; PRD 5.7 "which alloys can be used").
 MODEL_MIN_GRAIN_SIZES = 2
+# A quantity at most this fraction of its natural scale is numerically zero (register 'numerical_zero').
+RELATIVE_ZERO = 1e-10
 # The predictor's transformation, by the locked plan's code (register
 # 'grain_size_transformation_at_analysis').
 TRANSFORMATIONS = MappingProxyType({"inverse_square_root": lambda d: d ** -0.5})
@@ -60,6 +77,12 @@ OUTCOME_WORDING = MappingProxyType({
 BELOW_MINIMUMS_LABEL = "data found; not enough to test"
 EXPLORATORY_LABEL = "exploratory"
 POWER_LABEL = "estimated power under the stated assumptions"
+DETECTION_NOTE = ("detection rates of the nominal 5% test under the stated assumptions (fixed and estimated noise), "
+                  "with its false-positive shares under the same assumptions; not power for a test shown to keep "
+                  "false positives at 5%")
+
+# Why validity check 2 failed (stored with the result; migration 0004).
+INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "uncertainty_not_estimable")
 
 # The evidence level (owner, 2026-10-05; register 'evidence_level_scale'): descriptive only, derived
 # by `evidence_level` from the result state, never by an agent; it never affects the outcome or the
@@ -77,6 +100,8 @@ STATE_LEVELS = MappingProxyType({"sufficient": 6, "exploratory": 5, "coefficient
 
 # The per-source labels (owner, 2026-10-05, decision 2): descriptive only, never the verdict.
 LABELS = ("agrees", "conflicts", "same_direction_different_decision", "not_enough_data")
+# Why a per-source result is "not enough data" (review, smaller point): zero direction is not missing inference.
+LABEL_REASONS = ("no_p_value", "pooled_without_decision", "zero_coefficient")
 
 
 class StatisticsError(ValueError):
@@ -103,6 +128,8 @@ class Design:
     n_groups: int
     n_records_in_set: int
     n_alloys_not_used: int
+    n_groups_informative: int = 0
+    uninformative_groups: tuple = ()
 
     @property
     def n(self) -> int:
@@ -117,8 +144,10 @@ class Design:
         return self.n_alloys >= 1
 
     @property
-    def inference_valid(self) -> bool:  # validity check 2
-        return self.coefficient_fitted and self.resid_df >= 1 and self.n_groups >= 2
+    def counts_allow_inference(self) -> bool:
+        """Validity check 2's counts: a residual degree of freedom and two informative groups. The
+        standard error must also be estimable (`fit`)."""
+        return self.coefficient_fitted and self.resid_df >= 1 and self.n_groups_informative >= 2
 
 
 def design(observations: Iterable[Observation], transformation: str) -> Design:
@@ -126,25 +155,38 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
     obs = sorted(observations, key=lambda o: o.identity)
     if len({o.identity for o in obs}) != len(obs):
         raise StatisticsError("two records share one stable identity")
-    sizes: dict[str, set] = {}
+    transform = TRANSFORMATIONS[transformation]
+    values: dict[str, list] = {}
     for o in obs:
         if not (math.isfinite(o.grain_size) and o.grain_size > 0 and math.isfinite(o.outcome)):
             raise StatisticsError("a record in a frozen set has no finite positive grain size or finite outcome")
-        sizes.setdefault(o.alloy, set()).add(o.grain_size)
-    used_alloys = sorted(a for a, s in sizes.items() if len(s) >= MODEL_MIN_GRAIN_SIZES)
+        values.setdefault(o.alloy, []).append(transform(o.grain_size))
+    used_alloys = sorted(a for a, v in values.items() if distinct_values(v) >= MODEL_MIN_GRAIN_SIZES)
     keep = set(used_alloys)
     used = [o for o in obs if o.alloy in keep]
     groups = sorted({o.group for o in used})
     alloy_index = {a: i for i, a in enumerate(used_alloys)}
     group_index = {g: i for i, g in enumerate(groups)}
-    transform = TRANSFORMATIONS[transformation]
+    x = np.array([transform(o.grain_size) for o in used], dtype=float)
+    alloy = np.array([alloy_index[o.alloy] for o in used], dtype=int)
+    informative: set = set()
+    if used:
+        contrast = np.abs(demeaned(x, alloy, len(used_alloys)))
+        informative = {o.group for o, c in zip(used, contrast) if c > RELATIVE_ZERO * float(np.abs(x).max())}
     return Design(
-        x=np.array([transform(o.grain_size) for o in used], dtype=float),
-        y=np.array([o.outcome for o in used], dtype=float),
-        alloy=np.array([alloy_index[o.alloy] for o in used], dtype=int),
+        x=x, y=np.array([o.outcome for o in used], dtype=float), alloy=alloy,
         group=np.array([group_index[o.group] for o in used], dtype=int),
         n_alloys=len(used_alloys), n_groups=len(groups), n_records_in_set=len(obs),
-        n_alloys_not_used=len(sizes) - len(used_alloys))
+        n_alloys_not_used=len(values) - len(used_alloys), n_groups_informative=len(informative),
+        uninformative_groups=tuple(g for g in groups if g not in informative))
+
+
+def distinct_values(values: list) -> int:
+    """How many values differ from each other by more than the numerical zero (relative to the
+    largest): numerical distinctness of transformed grain sizes (review finding 3)."""
+    ordered = sorted(values)
+    tolerance = RELATIVE_ZERO * max(abs(v) for v in ordered)
+    return 1 + sum(1 for a, b in zip(ordered, ordered[1:]) if b - a > tolerance)
 
 
 def demeaned(values: np.ndarray, alloy: np.ndarray, n_alloys: int) -> np.ndarray:
@@ -176,30 +218,38 @@ class Fit:
     t: float | None
     df: int | None
     p_value: float | None
+    reason: str | None = None  # why there is no inference (INFERENCE_REASONS), or None
 
 
 def fit(d: Design) -> Fit | None:
-    """The coefficient (check 1), and its standard error and one-sided p-value (check 2)."""
+    """The coefficient (check 1), and its standard error and one-sided p-value (check 2): only when
+    the counts allow it and the standard error is finite and above the numerical zero."""
     if not d.coefficient_fitted:
         return None
     xd = demeaned(d.x, d.alloy, d.n_alloys)
     yd = demeaned(d.y, d.alloy, d.n_alloys)
     sxx = float(xd @ xd)
+    if not (math.isfinite(sxx) and sxx > 0):  # excluded by the alloy rule; never divide by it
+        raise StatisticsError("the transformed grain sizes have no variation within any alloy")
     k = float(xd @ yd) / sxx
-    if not d.inference_valid:
-        return Fit(k, None, None, None, None)
+    if not math.isfinite(k):
+        raise StatisticsError("the coefficient is not finite")
+    if not d.counts_allow_inference:
+        return Fit(k, None, None, None, None, "insufficient_groups")
     e = yd - k * xd
     scores = np.bincount(d.group, xd * e, d.n_groups)
     variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
-    se = math.sqrt(variance)
-    t = k / se if se > 0 else (math.inf if k > 0 else -math.inf)
+    se = math.sqrt(variance) if math.isfinite(variance) and variance >= 0 else math.nan
+    if not (math.isfinite(se) and se > RELATIVE_ZERO * math.sqrt(float(yd @ yd) / sxx)):
+        return Fit(k, None, None, None, None, "uncertainty_not_estimable")
+    t = k / se
     df = d.n_groups - 1
     return Fit(k, se, t, df, one_sided_p(t, df))
 
 
 def minimums(d: Design, sufficiency: Mapping) -> dict:
     """Each count of the fit against its minimum (PRD 5.8)."""
-    counts = {"records": d.n, "alloys": d.n_alloys, "groups": d.n_groups, "resid_df": d.resid_df}
+    counts = {"records": d.n, "alloys": d.n_alloys, "groups": d.n_groups_informative, "resid_df": d.resid_df}
     keys = {"records": "min_records", "alloys": "min_alloys", "groups": "min_groups", "resid_df": "min_resid_df"}
     return {name: {"count": counts[name], "minimum": sufficiency[keys[name]],
                    "met": counts[name] >= sufficiency[keys[name]]} for name in counts}
@@ -209,13 +259,22 @@ def significant(p_value: float | None, alpha: float) -> bool | None:
     return None if p_value is None else p_value < alpha
 
 
+def label_reason(per_source: Mapping, pooled: Mapping) -> str | None:
+    """Why a per-source result is "not enough data", or None when it can be compared."""
+    if per_source.get("p_value") is None:
+        return "no_p_value"
+    if pooled.get("p_value") is None:
+        return "pooled_without_decision"
+    if per_source["estimate"] == 0 or pooled["estimate"] == 0:
+        return "zero_coefficient"
+    return None
+
+
 def label(per_source: Mapping, pooled: Mapping, alpha: float) -> str:
     """The four per-source labels (owner, 2026-10-05): from the locked test and the sign only."""
-    if per_source.get("p_value") is None or pooled.get("p_value") is None:
+    if label_reason(per_source, pooled):
         return "not_enough_data"
     a, b = per_source["estimate"], pooled["estimate"]
-    if a == 0 or b == 0:
-        return "not_enough_data"
     if (a > 0) != (b > 0):
         return "conflicts"
     if significant(per_source["p_value"], alpha) == significant(pooled["p_value"], alpha):
@@ -266,11 +325,17 @@ def decision(pooled: Mapping | None, plan: Mapping, freeze_fingerprint: str | No
 def analysis_entry(d: Design, plan: Mapping, withheld: bool) -> dict:
     """One analysis: counts, checks, minimums, and (unless withheld) the numbers from outcomes."""
     m = minimums(d, plan["sufficiency"])
+    counts_reason = None if d.counts_allow_inference else \
+        "coefficient_not_fitted" if not d.coefficient_fitted else "insufficient_groups"
     entry = {
         "counts": {"n_records_in_set": d.n_records_in_set, "n_records": d.n,
                    "n_records_not_used": d.n_records_in_set - d.n, "n_alloys": d.n_alloys,
-                   "n_alloys_not_used": d.n_alloys_not_used, "n_groups": d.n_groups, "resid_df": d.resid_df},
-        "checks": {"coefficient_fitted": d.coefficient_fitted, "inference_valid": d.inference_valid},
+                   "n_alloys_not_used": d.n_alloys_not_used, "n_groups": d.n_groups,
+                   "n_groups_informative": d.n_groups_informative, "resid_df": d.resid_df},
+        "uninformative_groups": list(d.uninformative_groups),
+        # Withheld: judged on the counts only (no outcome is used, so no standard error is computed).
+        "checks": {"coefficient_fitted": d.coefficient_fitted, "inference_valid": d.counts_allow_inference},
+        "inference_reason": counts_reason,
         "minimums": m, "minimums_met": all(v["met"] for v in m.values()), "withheld": withheld,
         "estimate": None, "std_error": None, "t": None, "df": None, "p_value": None,
         "alpha": plan["model"]["alpha"], "significant": None,
@@ -279,9 +344,9 @@ def analysis_entry(d: Design, plan: Mapping, withheld: bool) -> dict:
         return entry
     f = fit(d)
     if f is not None:
-        t = f.t if f.t is None or math.isfinite(f.t) else None  # a zero standard error: no finite t to store
-        entry.update(estimate=f.estimate, std_error=f.std_error, t=t, df=f.df, p_value=f.p_value,
-                     significant=significant(f.p_value, plan["model"]["alpha"]))
+        entry.update(estimate=f.estimate, std_error=f.std_error, t=f.t, df=f.df, p_value=f.p_value,
+                     significant=significant(f.p_value, plan["model"]["alpha"]), inference_reason=f.reason)
+        entry["checks"]["inference_valid"] = f.reason is None
     return entry
 
 
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index 0a5a044..eb15f99 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -62,6 +62,7 @@ CODES = {
     "invariant_broken": "the primary set breaks a rule no plan can change (register 'primary_set_invariants')",
     # Step 7.
     "records_without_group": "a record in a frozen set has no group, so the grouped uncertainty cannot be computed",
+    "statistics_failed": "the statistics could not be computed for this run (the error is in the refusal's message)",
     "decision_missing": "no stored decision for this run",
     "decision_not_current": "the stored decision belongs to a different freeze than the run's",
 }
diff --git a/tests/test_calibration.py b/tests/test_calibration.py
index 1cb0379..bcb77b4 100644
--- a/tests/test_calibration.py
+++ b/tests/test_calibration.py
@@ -133,7 +133,7 @@ def test_the_scatter_cannot_be_estimated_without_residual_freedom_in_the_full_mo
     rows = [st.Observation(f"r{i}", a, p, d, y) for i, (a, p, d, y) in enumerate(
         [("A", "p1", 1.0, 500.0), ("A", "p2", 4.0, 420.0), ("B", "p1", 1.0, 700.0), ("B", "p3", 4.0, 610.0)])]
     d = st.design(rows, "inverse_square_root")
-    assert d.inference_valid
+    assert d.counts_allow_inference
     assert cal.henderson_iii(d)["reason"] == "scatter_not_estimable"
 
 
@@ -158,7 +158,8 @@ def test_calibration_never_changes_the_outcome_or_the_verdict(monkeypatch):
     before = analysis.analyse(plan, data)
 
     def forced(*args, **kwargs):
-        return {"status": "computed", "reason": None, "assumptions": {}, "seed": 1, "n_simulations": 1,
+        return {"status": "computed", "reason": None, "assumptions": {"scatter": 1.0, "shift": 1.0}, "seed": 1,
+                "n_simulations": 1,
                 "null": {"significant": 1, "share": 1.0, "ci_low": 0.9, "ci_high": 1.0},
                 "effect": {"significant": 0, "share": 0.0, "ci_low": 0.0, "ci_high": 0.1},
                 "confidence_flag": "over_confident", "flag_wording": "x"}
diff --git a/tests/test_statistics.py b/tests/test_statistics.py
index 5cf0d4d..43f089f 100644
--- a/tests/test_statistics.py
+++ b/tests/test_statistics.py
@@ -79,7 +79,7 @@ def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
             ("r6", "C", "p4", 3.0, 300.0)]
     d = st.design(obs(rows), "inverse_square_root")
     assert (d.n, d.n_alloys, d.n_groups, d.n_records_in_set, d.n_alloys_not_used) == (3, 1, 2, 6, 2)
-    assert d.resid_df == 1 and d.coefficient_fitted and d.inference_valid
+    assert d.resid_df == 1 and d.coefficient_fitted and d.counts_allow_inference
     entry = st.analysis_entry(d, g.plan("use_available", minimums=(3, 1, 2, 1)), withheld=False)
     assert entry["counts"]["n_records_not_used"] == 3
     assert entry["minimums"]["records"] == {"count": 3, "minimum": 3, "met": True}
@@ -97,7 +97,7 @@ def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
 ])
 def test_the_two_validity_checks(rows, check1, check2):
     d = st.design(obs(rows), "inverse_square_root")
-    assert (d.coefficient_fitted, d.inference_valid) == (check1, check2)
+    assert (d.coefficient_fitted, d.counts_allow_inference) == (check1, check2)  # step 7 review: renamed
     f = st.fit(d)
     assert (f is not None) == check1
     if check1:
diff --git a/tests/test_statistics_boundaries.py b/tests/test_statistics_boundaries.py
new file mode 100644
index 0000000..cf696cc
--- /dev/null
+++ b/tests/test_statistics_boundaries.py
@@ -0,0 +1,219 @@
+"""Step 7 review fixes (ChatGPT, 2026-10-06): the boundaries of validity check 2, numerical rank and
+numerical zero, and the smaller points. Pure functions, no database.
+
+Owner's decision (2026-10-06): the minimum of independent papers, and validity check 2's "at least
+two groups", count only informative papers: papers whose records help estimate the slope (non-zero
+grain-size variation after removing each alloy's average). Uninformative papers are kept and listed
+but not counted. Inference is valid only if the clustered standard error is finite and above a
+scale-aware numerical zero; otherwise the coefficient alone is reported. The simulations apply the
+same checks.
+"""
+from __future__ import annotations
+
+import math
+
+import numpy as np
+import pytest
+
+import generator as g
+from hypocurate.pipeline import analysis
+from hypocurate.pipeline import calibration as cal
+from hypocurate.pipeline import statistics as st
+
+
+def frozen(rows, name="boundary"):
+    """rows: (alloy index, paper, grain size, outcome) as frozen analysis data."""
+    records = [{"id": i + 1, "source": "mpea", "version_fingerprint": f"gen-{name}", "origin": f"b:{name}:{i}",
+                "item_index": i, "composition": {"Qa": float(10 + a), "Qb": float(90 - a)}, "paper": paper,
+                "batch": None, "grain_size": float(d), "outcome": float(y)} for i, (a, paper, d, y) in enumerate(rows)]
+    return {"freeze_fingerprint": "b" * 64, "outcome_field": "yield_strength",
+            "sets": {"primary": [r["id"] for r in records]}, "records": records}
+
+
+def reviewers_design():
+    """ChatGPT's case: five alloys, six records each; within each alloy grain sizes [16, 16/9, 4, 4, 4,
+    4]; the first two records of every alloy from one paper, the other twenty spread over ten papers;
+    outcomes [400, 600, 470, 510, 500, 490] plus an alloy baseline."""
+    sizes = [16.0, 16.0 / 9.0, 4.0, 4.0, 4.0, 4.0]
+    ys = [400.0, 600.0, 470.0, 510.0, 500.0, 490.0]
+    rows, n = [], 0
+    for a in range(5):
+        for j in range(6):
+            paper = "paper-00" if j < 2 else f"paper-{1 + n % 10:02d}"
+            if j >= 2:
+                n += 1
+            rows.append((a, paper, sizes[j], ys[j] + 100.0 * a))
+    return frozen(rows, "reviewer")
+
+
+# --- finding 1: informative papers and an estimable uncertainty -----------------------------------
+
+@pytest.mark.parametrize("option", ["fixed_minimum", "use_available"])
+def test_the_reviewers_design_never_gives_a_verdict(option):
+    out = analysis.analyse(g.plan(option, n_simulations=200), reviewers_design())
+    pooled = out["analyses"][0]
+    assert out["decision"]["verdict"] is None and out["decision"]["outcome"] == "insufficient"
+    assert pooled["counts"]["n_groups"] == 11 and pooled["counts"]["n_groups_informative"] == 1
+    assert pooled["uninformative_groups"] == [f"paper:paper-{i:02d}" for i in range(1, 11)]
+    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "insufficient_groups"
+    assert pooled["std_error"] is None and pooled["p_value"] is None
+    assert pooled["minimums"]["groups"]["count"] == 1
+    if option == "fixed_minimum":  # the paper minimum counts informative papers only: withheld
+        assert out["decision"]["evidence_level"] == 3 and pooled["estimate"] is None
+    else:
+        assert out["decision"]["evidence_level"] == 4 and math.isclose(pooled["estimate"], 400.0, rel_tol=1e-12)
+    assert {c["status"] for c in pooled["calibration"].values()} == {"unavailable"}
+
+
+def test_a_paper_is_informative_when_its_records_vary_after_removing_the_alloy_average():
+    obs = [st.Observation("a", "A", "p1", 1.0, 1.0), st.Observation("b", "A", "p1", 4.0, 2.0),  # p1 varies
+           st.Observation("c", "A", "p2", 9.0, 3.0),                                          # differs from mean
+           st.Observation("d", "B", "p3", 4.0, 1.0), st.Observation("e", "B", "p3", 4.0, 1.5),
+           st.Observation("f", "B", "p4", 1.0, 2.0), st.Observation("g", "B", "p4", 9.0, 2.5)]
+    d = st.design(obs, "inverse_square_root")
+    # Alloy B: x = 0.5, 0.5, 1, 1/3; mean 7/12: p3's records are 1/12 away from it, so p3 is informative.
+    assert (d.n_groups, d.n_groups_informative, d.uninformative_groups) == (4, 4, ())
+    obs2 = obs[:3] + [st.Observation("d", "B", "p3", 4.0, 1.0), st.Observation("f", "B", "p4", 1.0, 2.0),
+                      st.Observation("g", "B", "p4", 16.0 / 9.0, 2.5)]
+    d2 = st.design(obs2, "inverse_square_root")  # B: x = 0.5, 1, 0.75; mean 0.75: p4's mean-valued record...
+    assert d2.n_groups_informative == 4  # ...but p4 also holds x = 1, so it varies; p3 (x = 0.5) differs too
+    obs3 = [st.Observation("a", "A", "p1", 1.0, 1.0), st.Observation("b", "A", "p1", 9.0, 2.0),
+            st.Observation("c", "A", "p2", 1.0 / (2.0 / 3.0) ** 2, 3.0)]  # x = 2/3 = the alloy mean
+    d3 = st.design(obs3, "inverse_square_root")
+    assert (d3.n_groups, d3.n_groups_informative, d3.uninformative_groups) == (2, 1, ("p2",))
+
+
+def test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only():
+    """Two informative papers, residuals zero up to rounding: the standard error is below the
+    scale-aware numerical zero, so no p-value and no verdict."""
+    rows = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5)
+            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    out = analysis.analyse(g.plan("use_available", n_simulations=100), frozen(rows, "exact"))
+    pooled = out["analyses"][0]
+    assert pooled["counts"]["n_groups_informative"] >= 2 and pooled["counts"]["resid_df"] >= 1
+    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "uncertainty_not_estimable"
+    assert math.isclose(pooled["estimate"], 250.0, rel_tol=1e-9) and pooled["std_error"] is None
+    assert out["decision"]["verdict"] is None and out["decision"]["evidence_level"] == 4
+    assert {c["reason"] for c in pooled["calibration"].values()} == {"uncertainty_not_estimable"}
+
+
+def test_small_real_noise_keeps_the_uncertainty_estimable():
+    """The numerical zero is relative and far below any real scatter: noise of 0.001 MPa on values of
+    hundreds of MPa still gives a standard error and a test."""
+    rng = np.random.default_rng(5)
+    rows = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5 + rng.normal(0, 1e-3))
+            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=100), frozen(rows, "noise"))["analyses"][0]
+    assert pooled["checks"]["inference_valid"] is True and pooled["inference_reason"] is None
+    assert 0 < pooled["std_error"] < 1 and pooled["p_value"] < 1e-6
+
+
+def test_the_simulations_apply_the_same_check_to_each_simulated_fit():
+    """A simulated outcome row that fits exactly is never counted as significant."""
+    rows = [(a, f"p{j % 4}", d, 1.0) for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
+    exact = np.vstack([300.0 + 250.0 * d.x, 100.0 + 0.0 * d.x])
+    assert cal.significant_count(d, exact, 0.05) == 0
+
+
+def test_the_uncertainty_check_is_scale_aware():
+    """The same data in other units (×1e6 or ×1e-6) give the same validity decision."""
+    rng = np.random.default_rng(9)
+    base = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5 + rng.normal(0, 5.0))
+            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    for scale in (1e-6, 1.0, 1e6):
+        rows = [(a, p, d, y * scale) for a, p, d, y in base]
+        pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, f"s{scale}"))["analyses"][0]
+        assert pooled["checks"]["inference_valid"] is True, scale
+
+
+# --- finding 3: numerical rank of the transformed design ------------------------------------------
+
+def test_grain_sizes_equal_after_transformation_never_raise():
+    """9.0 and 9.000000000000002 transform to the same value: the alloy has no numerical variation,
+    so no coefficient is fitted, and nothing raises."""
+    assert 9.0 ** -0.5 == 9.000000000000002 ** -0.5
+    rows = [(0, "p1", 9.0, 400.0), (0, "p2", 9.000000000000002, 410.0), (0, "p1", 9.0, 405.0),
+            (0, "p2", 9.000000000000002, 395.0)]
+    out = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, "rank"))
+    pooled = out["analyses"][0]
+    assert pooled["checks"] == {"coefficient_fitted": False, "inference_valid": False}
+    assert pooled["estimate"] is None and pooled["inference_reason"] == "coefficient_not_fitted"
+    assert out["decision"]["evidence_level"] == 2
+
+
+def test_nearly_equal_transformed_grain_sizes_are_not_distinct():
+    rows = [(0, "p1", 9.0, 400.0), (0, "p2", 9.0 * (1 + 1e-13), 410.0), (1, "p1", 1.0, 500.0),
+            (1, "p2", 4.0, 420.0), (1, "p3", 9.0, 401.0)]
+    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
+    assert d.n_alloys == 1 and d.n_alloys_not_used == 1
+
+
+# --- finding 4: a perfect fit has no estimable scatter --------------------------------------------
+
+def test_an_exact_fit_has_no_estimable_scatter():
+    rows = [(a, f"p{(j + a) % 5}", d, 300.0 + 40 * a + 100.0 * d ** -0.5)
+            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
+    est = cal.henderson_iii(d)
+    assert est["rss_full"] < 1e-15 and est["reason"] == "scatter_not_estimable"
+
+
+def test_small_real_noise_gives_an_estimable_scatter():
+    rng = np.random.default_rng(3)
+    rows = [(a, f"p{(j + a) % 5}", d, 300.0 + 40 * a + 100.0 * d ** -0.5 + rng.normal(0, 0.01))
+            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
+    est = cal.henderson_iii(d)
+    assert est["reason"] in (None, "shift_not_estimable") and 0.003 < math.sqrt(est["scatter_squared"]) < 0.03
+
+
+# --- smaller points ----------------------------------------------------------------------------------
+
+def test_every_estimated_calibration_states_what_its_intervals_cover():
+    data = g.frozen_data(g.SPECS["effect_many_papers"])
+    d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
+    est = cal.calibrate(d, g.plan()["calibration"], 0.05, "f" * 64, "pooled", "estimated")
+    note = est["assumptions"]["interval_note"]
+    assert "Monte Carlo" in note and "not uncertainty in the estimated scatter and shift" in note
+    assert "diagnostic" in note and "not independent validation" in note
+    fixed = cal.calibrate(d, g.plan()["calibration"], 0.05, "f" * 64, "pooled", "fixed")
+    assert "Monte Carlo" in fixed["assumptions"]["interval_note"]
+
+
+def test_detection_rates_are_reported_both_ways_with_the_false_positive_shares():
+    data = g.frozen_data(g.SPECS["effect_many_papers"])
+    pooled = analysis.analyse(g.plan("fixed_minimum", n_simulations=300), data)["analyses"][0]
+    rates = pooled["detection"]
+    for method in ("fixed", "estimated"):
+        c = pooled["calibration"][method]
+        assert rates[method] == {"detection": c["effect"]["share"], "detection_ci": [c["effect"]["ci_low"],
+                                                                                    c["effect"]["ci_high"]],
+                                 "false_positive": c["null"]["share"],
+                                 "false_positive_ci": [c["null"]["ci_low"], c["null"]["ci_high"]],
+                                 "scatter": c["assumptions"]["scatter"], "shift": c["assumptions"]["shift"]}
+    assert pooled["estimated_power"] == rates["fixed"]["detection"]
+    assert pooled["estimated_power_estimated_noise"] == rates["estimated"]["detection"]
+    assert "nominal" in pooled["detection_note"] and "not power" in pooled["detection_note"]
+
+
+def test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld():
+    data = g.frozen_data(g.SPECS["small_but_valid"])
+    pooled = analysis.analyse(g.plan("fixed_minimum", n_simulations=300), data)["analyses"][0]
+    assert pooled["withheld"]
+    assert pooled["detection"]["fixed"]["detection"] == pooled["estimated_power"] is not None
+    assert pooled["detection"]["estimated"] == {"withheld": True}
+    assert pooled["estimated_power_estimated_noise"] is None
+
+
+@pytest.mark.parametrize("per_source, pooled, reason", [
+    ({"estimate": 0.0, "p_value": 0.5}, {"estimate": 424.0, "p_value": 1e-6}, "zero_coefficient"),
+    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 0.0, "p_value": 0.5}, "zero_coefficient"),
+    ({"estimate": 1173.0, "p_value": None}, {"estimate": 424.0, "p_value": 1e-6}, "no_p_value"),
+    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 424.0, "p_value": None}, "pooled_without_decision"),
+    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 424.0, "p_value": 1e-6}, None),
+])
+def test_a_zero_coefficient_has_its_own_reason(per_source, pooled, reason):
+    """'Not enough data' keeps its label; the reason says why (zero direction or missing inference)."""
+    assert st.label_reason(per_source, pooled) == reason
+    assert (st.label(per_source, pooled, 0.05) == "not_enough_data") == (reason is not None)
```


### Commit `ee99d9d`

```
ee99d9d Step 7 review fixes: migration 0004 (no display-label bound; informative groups, inference and label reasons, estimated detection rate, evidence level required)

 .../migrations/versions/0004_statistics_results.py | 89 ++++++++++++++++----
 hypocurate/db/models.py                            | 33 +++++++-
 tests/access_world.py                              |  6 +-
 tests/model_builder.py                             | 26 ++++--
 tests/stats_world.py                               |  7 +-
 tests/test_analysis_stage.py                       | 97 ++++++++++++++++++++--
 tests/test_completion.py                           | 11 +++
 tests/test_concurrency.py                          |  3 +-
 tests/test_data_model.py                           | 37 ++++++---
 tests/test_migrations_step7.py                     | 17 +++-
 10 files changed, 270 insertions(+), 56 deletions(-)
```

```diff
diff --git a/hypocurate/db/migrations/versions/0004_statistics_results.py b/hypocurate/db/migrations/versions/0004_statistics_results.py
index 5608f7a..6015532 100644
--- a/hypocurate/db/migrations/versions/0004_statistics_results.py
+++ b/hypocurate/db/migrations/versions/0004_statistics_results.py
@@ -19,6 +19,14 @@ analysis_result:
 - `n_records_not_used` (decision 7): records of the set the fit does not use (alloys with fewer
   than two distinct grain sizes within this analysis). The trigger now checks
   n_records + n_records_not_used = the records of the set used; the stored counts are the fit's.
+  The trigger no longer bounds the alloy count by the display label (review finding 2).
+- `n_groups_informative` (owner, 2026-10-06): the groups that help estimate the slope; the paper
+  minimum and validity check 2 count these. `ck_analysis_result_check2_consistent` becomes an
+  implication (check 2 needs a coefficient, a residual degree of freedom and two informative groups,
+  but can also fail on an unestimable uncertainty), and `inference_reason` states why it failed
+  (derived by the trigger where the counts determine it; 'uncertainty_not_estimable' must be given).
+- `label_reason` (present exactly with "not enough data") and `estimated_power_estimated_noise`
+  (the detection rate under the estimated noise; never on a withheld result).
 - `test_run_label`: "test run: includes constructed data" exactly when the run is marked.
 - The label CHECK gains `same_direction_different_decision` (decision 2/3); a label only on a
   per-source row; an estimated power only where inference is valid.
@@ -26,7 +34,8 @@ analysis_result:
 calibration_result:
 - `method` ('fixed' or 'estimated'): present exactly on rows of an analysis; the one run-level
   row ("no dataset frozen") has none. The unique index becomes (run, analysis, method).
-- Reasons gain `below_minimums`, `scatter_not_estimable`, `shift_not_estimable`.
+- Reasons gain `below_minimums`, `scatter_not_estimable`, `shift_not_estimable`,
+  `uncertainty_not_estimable` (an unavailable reason follows the result's inference reason).
 - `test_run_label`, as above.
 - The insert trigger: computed only where inference is valid and the result is not withheld;
   where it is, the fixed method must be computed and the estimated one is computed or names why
@@ -36,8 +45,8 @@ calibration_result:
 run:
 - `evidence_level` 1 to 6 (owner, 2026-10-05; register 'evidence_level_scale'). Written only by
   the copy path (`pipeline/completion.py`); when present it must agree with the outcome: 6 = a
-  verdict and not exploratory, 5 = a verdict and exploratory, 1 to 4 = no verdict; present only
-  with an outcome. **The database does not require it** on a completed run.
+  verdict and not exploratory, 5 = a verdict and exploratory, 1 to 4 = no verdict; required on
+  every completed run, and only on one (review fixes, 2026-10-06).
 
 Marked runs are left out of every aggregate by `pipeline/results.py` (`real_runs`), in code, not by
 a view (register 'constructed_test_runs').
@@ -130,7 +139,7 @@ CALIBRATION_INSERT_0001 = """
 
 ANALYSIS_RESULT_INSERT_0004 = """
     CREATE OR REPLACE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
-    DECLARE s analysis_set; p plan; set_count int; set_alloys int; pooled analysis_result; computed boolean;
+    DECLARE s analysis_set; p plan; set_count int; pooled analysis_result; computed boolean;
     BEGIN
         IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
             PERFORM hc_reject('analysis results are written only while the run is running');
@@ -145,7 +154,10 @@ ANALYSIS_RESULT_INSERT_0004 = """
         IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
             PERFORM hc_reject('a sensitivity result uses a sensitivity set');
         END IF;
-        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
+        -- Review finding 2: the alloy count is no longer bounded by the display label (record.alloy),
+        -- which is rounded to 0.1 at.% while the plan's same-alloy rule may be finer. The bound
+        -- n_records >= 2 * n_alloys (a CHECK) remains.
+        SELECT count(*) INTO set_count FROM analysis_set_record sr
             JOIN record r ON r.id = sr.record_id
             JOIN source_version sv ON sv.id = r.source_version_id
             WHERE sr.analysis_set_id = NEW.analysis_set_id
@@ -153,14 +165,18 @@ ANALYSIS_RESULT_INSERT_0004 = """
         IF NEW.n_records + NEW.n_records_not_used <> set_count THEN
             PERFORM hc_reject('n_records must equal the records of the set used, less those the fit does not use');
         END IF;
-        IF NEW.n_alloys > set_alloys THEN
-            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
-        END IF;
         SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
+        -- The paper minimum counts informative groups only (owner, 2026-10-06).
         IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
-                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
+                                AND NEW.n_groups_informative >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
             PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
         END IF;
+        -- Why check 2 failed, where the counts determine it; an unestimable uncertainty must be stated.
+        IF NEW.inference_reason IS NULL AND NOT NEW.check2_passed THEN
+            NEW.inference_reason := CASE WHEN NOT NEW.check1_passed THEN 'coefficient_not_fitted'
+                                         WHEN NOT (NEW.resid_df >= 1 AND NEW.n_groups_informative >= 2)
+                                         THEN 'insufficient_groups' END;
+        END IF;
         -- Step 7, decision 1: withheld run-wide when the pooled fit misses a minimum under the fixed option.
         IF NEW.scope = 'pooled' THEN
             computed := p.sufficiency_option = 'fixed_minimum' AND NOT NEW.minimums_met;
@@ -210,7 +226,7 @@ CALIBRATION_INSERT_0004 = """
         END IF;
         IF NEW.status = 'unavailable' AND NOT (a.check2_passed AND NOT a.withheld) THEN
             expected := CASE WHEN NOT a.check1_passed THEN 'coefficient_not_fitted'
-                             WHEN NOT a.check2_passed THEN 'insufficient_groups'
+                             WHEN NOT a.check2_passed THEN a.inference_reason
                              ELSE 'below_minimums' END;
             IF NEW.reason IS NOT NULL AND NEW.reason <> expected THEN  -- a missing reason: the CHECK refuses it
                 PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
@@ -223,20 +239,31 @@ CALIBRATION_INSERT_0004 = """
 NEW_LABELS = "('agrees', 'conflicts', 'not_enough_data', 'same_direction_different_decision')"
 OLD_LABELS = "('agrees', 'conflicts', 'not_enough_data')"
 NEW_REASONS = ("('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups', 'below_minimums', "
-               "'scatter_not_estimable', 'shift_not_estimable')")
+               "'scatter_not_estimable', 'shift_not_estimable', 'uncertainty_not_estimable')")
+INFERENCE_REASONS = "('coefficient_not_fitted', 'insufficient_groups', 'uncertainty_not_estimable')"
+LABEL_REASONS = "('no_p_value', 'pooled_without_decision', 'zero_coefficient')"
+COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"
+INFERENCE_REASON = ("(inference_reason IS NULL) = check2_passed "
+                    "AND (inference_reason IS NOT DISTINCT FROM 'coefficient_not_fitted') = NOT check1_passed "
+                    f"AND (inference_reason IS DISTINCT FROM 'insufficient_groups' OR NOT {COUNTS_ALLOW}) "
+                    f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR {COUNTS_ALLOW})")
 OLD_REASONS = "('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')"
 
 EVIDENCE_LEVEL = ("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
                   "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                   "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))")
+EVIDENCE_LEVEL_REQUIRED = "(evidence_level IS NOT NULL) = (status = 'completed')"
 
 IN_USE = """
     DO $$
     BEGIN
         IF EXISTS (SELECT 1 FROM analysis_result WHERE withheld OR n_records_not_used <> 0
-                   OR test_run_label IS NOT NULL OR label = 'same_direction_different_decision')
+                   OR test_run_label IS NOT NULL OR label = 'same_direction_different_decision'
+                   OR n_groups_informative <> n_groups OR inference_reason = 'uncertainty_not_estimable'
+                   OR label_reason IS NOT NULL OR estimated_power_estimated_noise IS NOT NULL)
            OR EXISTS (SELECT 1 FROM calibration_result WHERE method = 'estimated' OR test_run_label IS NOT NULL
-                      OR reason IN ('below_minimums', 'scatter_not_estimable', 'shift_not_estimable'))
+                      OR reason IN ('below_minimums', 'scatter_not_estimable', 'shift_not_estimable',
+                                    'uncertainty_not_estimable'))
            OR EXISTS (SELECT 1 FROM run WHERE evidence_level IS NOT NULL) THEN
             RAISE EXCEPTION USING MESSAGE = 'hypocurate: 0004 cannot be downgraded while step 7 results use it',
                                   ERRCODE = 'check_violation';
@@ -257,12 +284,33 @@ def upgrade() -> None:
     op.add_column('analysis_result', sa.Column('test_run_label', sa.Text(), nullable=True))
     op.create_check_constraint(op.f('ck_analysis_result_test_run_label'), 'analysis_result',
                                f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'")
+    # Review fixes (2026-10-06): informative groups, the reason inference is missing, the label's reason,
+    # the detection rate under the estimated noise.
+    op.add_column('analysis_result', sa.Column('n_groups_informative', sa.Integer(), nullable=True))
+    op.execute("UPDATE analysis_result SET n_groups_informative = n_groups")  # none on the live database
+    op.alter_column('analysis_result', 'n_groups_informative', nullable=False)
+    op.create_check_constraint(op.f('ck_analysis_result_informative_within_groups'), 'analysis_result',
+                               'n_groups_informative BETWEEN 0 AND n_groups')
+    for column in ('inference_reason', 'label_reason'):
+        op.add_column('analysis_result', sa.Column(column, sa.Text(), nullable=True))
+    op.add_column('analysis_result', sa.Column('estimated_power_estimated_noise', sa.Double(), nullable=True))
+    op.create_check_constraint(op.f('ck_analysis_result_inference_reason_value'), 'analysis_result',
+                               f"inference_reason IS NULL OR inference_reason IN {INFERENCE_REASONS}")
+    op.create_check_constraint(op.f('ck_analysis_result_label_reason_value'), 'analysis_result',
+                               f"label_reason IS NULL OR label_reason IN {LABEL_REASONS}")
+    op.create_check_constraint(op.f('ck_analysis_result_label_reason'), 'analysis_result',
+                               "(label_reason IS NOT NULL) = (label IS NOT DISTINCT FROM 'not_enough_data')")
+    op.create_check_constraint(op.f('ck_analysis_result_power_estimated_noise'), 'analysis_result',
+                               "estimated_power_estimated_noise IS NULL OR (check2_passed AND NOT withheld "
+                               "AND estimated_power_estimated_noise BETWEEN 0 AND 1)")
     for name, expr in (("estimate_iff_check1", "(check1_passed AND NOT withheld) = (estimate IS NOT NULL)"),
                        ("std_error_iff_check2", "(check2_passed AND NOT withheld) = (std_error IS NOT NULL)"),
                        ("p_value_iff_check2", "(check2_passed AND NOT withheld) = (p_value IS NOT NULL)"),
-                       ("label", f"label IS NULL OR label IN {NEW_LABELS}")):
+                       ("label", f"label IS NULL OR label IN {NEW_LABELS}"),
+                       ("check2_consistent", f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW})")):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
         op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
+    op.create_check_constraint(op.f('ck_analysis_result_inference_reason'), 'analysis_result', INFERENCE_REASON)
     op.create_check_constraint(op.f('ck_analysis_result_label_per_source_only'), 'analysis_result',
                                "label IS NULL OR scope = 'per_source'")
     op.create_check_constraint(op.f('ck_analysis_result_power_needs_check2'), 'analysis_result',
@@ -287,10 +335,14 @@ def upgrade() -> None:
     # run
     op.add_column('run', sa.Column('evidence_level', sa.SmallInteger(), nullable=True))
     op.create_check_constraint(op.f('ck_run_evidence_level'), 'run', EVIDENCE_LEVEL)
+    # Review (smaller point): required on every completed run. Needs no completed run to exist
+    # (true on the live database, where no run was ever dispatched); otherwise the upgrade fails whole.
+    op.create_check_constraint(op.f('ck_run_evidence_level_iff_completed'), 'run', EVIDENCE_LEVEL_REQUIRED)
 
 
 def downgrade() -> None:
     op.execute(IN_USE)
+    op.drop_constraint(op.f('ck_run_evidence_level_iff_completed'), 'run', type_='check')
     op.drop_constraint(op.f('ck_run_evidence_level'), 'run', type_='check')
     op.drop_column('run', 'evidence_level')
     op.execute(CALIBRATION_INSERT_0001)
@@ -305,14 +357,19 @@ def downgrade() -> None:
     op.drop_column('calibration_result', 'test_run_label')
     op.drop_column('calibration_result', 'method')
     op.execute(ANALYSIS_RESULT_INSERT_0001)
-    for name in ('power_needs_check2', 'label_per_source_only'):
+    for name in ('power_needs_check2', 'label_per_source_only', 'inference_reason', 'power_estimated_noise',
+                 'label_reason', 'label_reason_value', 'inference_reason_value', 'informative_within_groups'):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
     for name, expr in (("estimate_iff_check1", "check1_passed = (estimate IS NOT NULL)"),
                        ("std_error_iff_check2", "check2_passed = (std_error IS NOT NULL)"),
                        ("p_value_iff_check2", "check2_passed = (p_value IS NOT NULL)"),
-                       ("label", f"label IS NULL OR label IN {OLD_LABELS}")):
+                       ("label", f"label IS NULL OR label IN {OLD_LABELS}"),
+                       ("check2_consistent", "check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)")):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
         op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
+    # After the constraints that name them are restored (a dropped column takes its constraints with it).
+    for column in ('estimated_power_estimated_noise', 'label_reason', 'inference_reason', 'n_groups_informative'):
+        op.drop_column('analysis_result', column)
     for name in ('test_run_label', 'not_used_not_negative', 'withheld_set'):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
     op.drop_column('analysis_result', 'test_run_label')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index db297fa..c456c81 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -323,7 +323,8 @@ class Run(Base):
     outcome: Mapped[str | None] = mapped_column(Text)
     verdict: Mapped[str | None] = mapped_column(Text)
     exploratory: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
-    # Step 7 (migration 0004; register 'evidence_level_scale'): 1 to 6, written only by the copy path.
+    # Step 7 (migration 0004; register 'evidence_level_scale'): 1 to 6, written by the copy path;
+    # required on every completed run.
     evidence_level: Mapped[int | None] = mapped_column(SmallInteger)
     failure_reason: Mapped[str | None] = mapped_column(Text)
     agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
@@ -346,6 +347,7 @@ class Run(Base):
         CheckConstraint("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
                         "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                         "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))", name="evidence_level"),
+        CheckConstraint("(evidence_level IS NOT NULL) = (status = 'completed')", name="evidence_level_iff_completed"),
         CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
         CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
         CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
@@ -635,6 +637,9 @@ class FlagRecord(Base):
 SCOPES = ("pooled", "per_source", "sensitivity")
 LABELS = ("agrees", "conflicts", "not_enough_data", "same_direction_different_decision")  # 4th: step 7
 TEST_RUN_LABEL = "test run: includes constructed data"
+INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "uncertainty_not_estimable")
+LABEL_REASONS = ("no_p_value", "pooled_without_decision", "zero_coefficient")
+COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"
 
 
 class AnalysisResult(Base):
@@ -668,6 +673,13 @@ class AnalysisResult(Base):
     withheld: Mapped[bool | None] = mapped_column(Boolean)
     n_records_not_used: Mapped[int] = mapped_column(Integer, server_default=sql("0"))
     test_run_label: Mapped[str | None] = mapped_column(Text)
+    # Review fixes (2026-10-06): informative groups (the paper minimum and check 2 count these), why
+    # check 2 failed, why a per-source label is "not enough data", the detection rate under the
+    # estimated noise.
+    n_groups_informative: Mapped[int] = mapped_column(Integer)
+    inference_reason: Mapped[str | None] = mapped_column(Text)
+    label_reason: Mapped[str | None] = mapped_column(Text)
+    estimated_power_estimated_noise: Mapped[float | None] = mapped_column(Double)
     __table_args__ = (
         ForeignKeyConstraint(["analysis_set_id", "run_id"], ["analysis_set.id", "analysis_set.run_id"],
                              name="fk_analysis_result_analysis_set"),
@@ -684,8 +696,20 @@ class AnalysisResult(Base):
         CheckConstraint("n_records = 0 OR n_groups >= 1", name="records_have_a_group"),
         CheckConstraint("resid_df = n_records - n_alloys - 1", name="resid_df_definition"),
         CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_consistent"),
-        CheckConstraint("check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)",
-                        name="check2_consistent"),
+        CheckConstraint(f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW})", name="check2_consistent"),
+        CheckConstraint("n_groups_informative BETWEEN 0 AND n_groups", name="informative_within_groups"),
+        CheckConstraint("inference_reason IS NULL OR " + one_of("inference_reason", INFERENCE_REASONS),
+                        name="inference_reason_value"),
+        CheckConstraint("(inference_reason IS NULL) = check2_passed "
+                        "AND (inference_reason IS NOT DISTINCT FROM 'coefficient_not_fitted') = NOT check1_passed "
+                        f"AND (inference_reason IS DISTINCT FROM 'insufficient_groups' OR NOT {COUNTS_ALLOW}) "
+                        f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR {COUNTS_ALLOW})",
+                        name="inference_reason"),
+        CheckConstraint("label_reason IS NULL OR " + one_of("label_reason", LABEL_REASONS), name="label_reason_value"),
+        CheckConstraint("(label_reason IS NOT NULL) = (label IS NOT DISTINCT FROM 'not_enough_data')",
+                        name="label_reason"),
+        CheckConstraint("estimated_power_estimated_noise IS NULL OR (check2_passed AND NOT withheld "
+                        "AND estimated_power_estimated_noise BETWEEN 0 AND 1)", name="power_estimated_noise"),
         CheckConstraint("(check1_passed AND NOT withheld) = (estimate IS NOT NULL)", name="estimate_iff_check1"),
         CheckConstraint("(check2_passed AND NOT withheld) = (std_error IS NOT NULL)", name="std_error_iff_check2"),
         CheckConstraint("(check2_passed AND NOT withheld) = (p_value IS NOT NULL)", name="p_value_iff_check2"),
@@ -701,7 +725,8 @@ class AnalysisResult(Base):
 
 
 CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups",
-                       "below_minimums", "scatter_not_estimable", "shift_not_estimable")  # last three: step 7
+                       "below_minimums", "scatter_not_estimable", "shift_not_estimable",  # step 7
+                       "uncertainty_not_estimable")  # step 7 review fix
 CALIBRATION_METHODS = ("fixed", "estimated")
 CALIBRATION_NUMBERS = ("assumptions", "n_simulations", "seed", "null_share", "null_ci_low", "null_ci_high",
                        "effect_share", "effect_ci_low", "effect_ci_high", "confidence_flag")
diff --git a/tests/access_world.py b/tests/access_world.py
index cc2bf5a..aacff11 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -196,9 +196,9 @@ def original_run(w: World) -> int:
         w.decide(rid, rec)
         w.add(primary, rec)
     w.freeze(rid, len(recs))
-    sql(w, "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
-           "check1_passed, check2_passed, minimums_met, estimate) "
-           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, true, false, false, :e)", r=rid, s=primary, e=OTHER)
+    sql(w, "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
+           "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate) "
+           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, 1, true, false, false, :e)", r=rid, s=primary, e=OTHER)
     stage(w, rid, "analyst", "analyst", f"k = {OTHER}")
     w.complete(rid, "partly_sufficient")
     cid = stage(w, rid, "commentator", "commentator", f"the coefficient {OTHER}")
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 0d6e4da..156a907 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -214,31 +214,39 @@ class World:
         return rid, sets, recs
 
     def result(self, rid, set_id, scope="pooled", n=4, alloys=1, groups=2, source=None, minimums_met=None,
-               mins=(4, 1, 2, 1)):
-        """An analysis result whose fields follow the validity-check definitions."""
+               mins=(4, 1, 2, 1), informative=None):
+        """An analysis result whose fields follow the validity-check definitions. Step 7 review fixes:
+        `informative` groups (default: every group) count for check 2 and the paper minimum."""
+        informative = groups if informative is None else informative
         resid = n - alloys - 1
         check1 = alloys >= 1
-        check2 = check1 and resid >= 1 and groups >= 2
+        check2 = check1 and resid >= 1 and informative >= 2
         if minimums_met is None:
-            minimums_met = n >= mins[0] and alloys >= mins[1] and groups >= mins[2] and resid >= mins[3]
+            minimums_met = n >= mins[0] and alloys >= mins[1] and informative >= mins[2] and resid >= mins[3]
         # Step 7 (migration 0004): a result is withheld (no number from outcomes) when the run uses
         # the fixed option and its pooled result misses a minimum; the database computes it.
         option = self.val("SELECT sufficiency_option FROM plan WHERE run_id = :r", r=rid)
         pooled = self.val("SELECT withheld FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
         withheld = (option == "fixed_minimum" and not minimums_met) if scope == "pooled" else bool(pooled)
+        counts_check2 = check2
         check1, check2 = check1 and not withheld, check2 and not withheld  # only for the values below
         return self.val(
             "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, "
-            "resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
-            "VALUES (:r, :sc, :s, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
+            "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
+            "VALUES (:r, :sc, :s, :src, :n, :a, :g, :gi, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
             r=rid, sc=scope, s=set_id, src=self.source[source] if source else None, n=n, a=alloys, g=groups,
-            df=resid, c1=alloys >= 1, c2=alloys >= 1 and resid >= 1 and groups >= 2, mm=minimums_met,
+            gi=informative, df=resid, c1=alloys >= 1, c2=counts_check2, mm=minimums_met,
             est=428.0 if check1 else None,
             se=64.0 if check2 else None, p=1e-6 if check2 else None)
 
-    def complete(self, rid, outcome, verdict=None, exploratory=False):
+    def complete(self, rid, outcome, verdict=None, exploratory=False, level=None):
+        """Step 7 review fixes: a completed run needs its evidence level. The default is a level
+        consistent with the outcome (6 or 5 with a verdict, else 1); the real one comes from the copy path."""
+        if level is None:
+            level = (5 if exploratory else 6) if verdict else 1
         self.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
-                     "exploratory = :x WHERE id = :r", o=outcome, v=verdict, x=exploratory, r=rid)
+                     "exploratory = :x, evidence_level = :e WHERE id = :r", o=outcome, v=verdict, x=exploratory,
+                     e=level, r=rid)
 
     def fail(self, rid, reason="worker stopped"):
         self.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r",
diff --git a/tests/stats_world.py b/tests/stats_world.py
index 1937bda..7213caa 100644
--- a/tests/stats_world.py
+++ b/tests/stats_world.py
@@ -32,18 +32,19 @@ def small_rows(n_alloys: int, sizes=(1.0, 9.0), papers: int = 3, k: float = 300.
     return rows
 
 
-def plan_for(vid: int, option: str = "fixed_minimum", mins=(30, 5, 10, 10)) -> dict:
+def plan_for(vid: int, option: str = "fixed_minimum", mins=(30, 5, 10, 10), rules=None) -> dict:
     plan = reference_plan(vid)
+    plan["rules"].update(rules or {})
     plan["sufficiency"] = {"option": option, "min_records": mins[0], "min_alloys": mins[1], "min_groups": mins[2],
                            "min_resid_df": mins[3]}
     return plan
 
 
-def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True) -> int:
+def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True, rules=None) -> int:
     if register:
         pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
     rid = pw.dispatched_run(engine, sources=("mpea",), marked=marked)
-    checkpoints.lock_rules(engine, rid, plan_for(pw.version_of(engine, rid), option, mins))
+    checkpoints.lock_rules(engine, rid, plan_for(pw.version_of(engine, rid), option, mins, rules))
     extract.store_records(engine, rid)
     checks.run_checks(engine, rid)
     inclusion.decide_run(engine, rid)
diff --git a/tests/test_analysis_stage.py b/tests/test_analysis_stage.py
index 1bda375..025a14a 100644
--- a/tests/test_analysis_stage.py
+++ b/tests/test_analysis_stage.py
@@ -268,8 +268,8 @@ def _insert_result(engine, rid, **over):
     sets = dict(rows_of(engine, "SELECT key, id FROM analysis_set WHERE run_id = :r", r=rid))
     n = val(engine, "SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sets["primary"])
     cols = dict(run_id=rid, scope="pooled", analysis_set_id=sets["primary"], n_records=n, n_alloys=3, n_groups=3,
-                resid_df=n - 4, check1_passed=True, check2_passed=True, minimums_met=False, estimate=None,
-                std_error=None, p_value=None)
+                n_groups_informative=3, resid_df=n - 4, check1_passed=True, check2_passed=True, minimums_met=False,
+                estimate=None, std_error=None, p_value=None)
     cols.update(over)
     with engine.begin() as conn:
         conn.execute(text(f"INSERT INTO analysis_result ({', '.join(cols)}) VALUES "
@@ -300,7 +300,8 @@ def test_the_database_refuses_a_label_on_a_pooled_result_and_power_without_infer
     with pytest.raises(IntegrityError, match="ck_analysis_result_label_per_source_only"):
         _insert_result(engine, rid, label="agrees", estimate=1.0, std_error=1.0, p_value=0.1)
     with pytest.raises(IntegrityError, match="ck_analysis_result_power_needs_check2"):
-        _insert_result(engine, rid, n_groups=1, check2_passed=False, estimate=1.0, estimated_power=0.5)
+        _insert_result(engine, rid, n_groups=1, n_groups_informative=1, check2_passed=False, estimate=1.0,
+                       estimated_power=0.5)
     with pytest.raises(IntegrityError, match="test-run label exactly when"):
         _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, test_run_label=LABEL)
 
@@ -309,8 +310,8 @@ def test_the_database_refuses_records_not_accounted_for(engine):
     rid = run_on(engine, small_rows(3, papers=3), option="use_available")
     with pytest.raises(IntegrityError, match="n_records must equal"):
         _insert_result(engine, rid, n_records=5, resid_df=1, estimate=1.0, std_error=1.0, p_value=0.1)
-    _insert_result(engine, rid, n_records=4, n_records_not_used=2, n_alloys=2, n_groups=2, resid_df=1,
-                   estimate=1.0, std_error=1.0, p_value=0.1)
+    _insert_result(engine, rid, n_records=4, n_records_not_used=2, n_alloys=2, n_groups=2, n_groups_informative=2,
+                   resid_df=1, estimate=1.0, std_error=1.0, p_value=0.1)
 
 
 def test_the_database_refuses_calibration_that_does_not_match_the_result(engine):
@@ -367,3 +368,89 @@ def test_the_evidence_level_must_agree_with_the_outcome(engine, outcome, verdict
         with pytest.raises(IntegrityError, match="ck_run_evidence_level"):
             with engine.begin() as conn:
                 conn.execute(text(update), params)
+
+
+# --- review fixes (ChatGPT, 2026-10-06) ---------------------------------------------------------------
+
+def test_two_alloys_with_one_display_label_are_stored(engine):
+    """Finding 2: Fe50.01Ni49.99 and Fe50.04Ni49.96 both display as Fe50Ni50. Under a plan rounding
+    compositions to 0.01 at.% they are two alloys, each at three grain sizes; the result must be stored
+    (the trigger no longer bounds the alloy count by the display label)."""
+    rows = [pw.mpea_row(formula, d, ys, doi=f"10.1016/j.test.2026.{p:03d}")
+            for formula, base in (("Fe50.01Ni49.99", 200.0), ("Fe50.04Ni49.96", 260.0))
+            for p, (d, ys) in enumerate(((1.0, base + 300), (4.0, base + 150), (16.0, base + 75)), start=1)]
+    rid = run_on(engine, rows, option="use_available", rules={"same_alloy_decimals": 2})
+    assert {r[0] for r in rows_of(engine, "SELECT alloy FROM record WHERE extraction_run_id = :r", r=rid)} == {"Fe50Ni50"}
+    out = analysis.run_statistics(engine, rid)
+    assert out["analyses"][0]["counts"]["n_alloys"] == 2
+    assert result_rows(engine, rid)[0].n_alloys == 2
+
+
+def test_an_unexpected_error_in_the_statistics_is_a_logged_refusal(engine, monkeypatch):
+    """Finding 3: no exception may bypass the stage's error handling."""
+    from hypocurate.pipeline import statistics as st
+    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
+
+    def broken(d):
+        raise ZeroDivisionError("float division by zero")
+
+    monkeypatch.setattr(st, "fit", broken)
+    with pytest.raises(Refused) as refused:
+        analysis.run_statistics(engine, rid)
+    assert refused.value.code == "statistics_failed"
+    assert audit_codes(engine, rid, "run_statistics") == ["statistics_failed"]
+    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
+
+
+def test_the_reviewers_design_through_the_database(engine):
+    """Finding 1 end to end: eleven papers, one informative; use what is available gives the
+    coefficient only and the database stores the informative count and the reason."""
+    rows = []
+    # The reviewer's structure with grain sizes written exactly in the file: x = d^-1/2 = 0.2, 0.8 and
+    # four times 0.5, the alloy average (16/9 µm cannot be written exactly in a CSV cell).
+    sizes, ys = (25.0, 1.5625, 4.0, 4.0, 4.0, 4.0), (400.0, 600.0, 470.0, 510.0, 500.0, 490.0)
+    n = 0
+    from stats_world import FORMULAS
+    for a in range(5):
+        for j in range(6):
+            paper = 0 if j < 2 else 1 + n % 10
+            n += j >= 2
+            rows.append(pw.mpea_row(FORMULAS[a], sizes[j], ys[j] + 100 * a,
+                                    doi=f"10.1016/j.test.2026.{paper:03d}"))
+    rid = run_on(engine, rows, option="use_available")
+    out = analysis.run_statistics(engine, rid)
+    assert out["decision"]["verdict"] is None and out["decision"]["evidence_level"] == 4
+    r = result_rows(engine, rid)[0]
+    assert (r.n_groups, r.n_groups_informative, r.check2_passed, r.inference_reason) == (11, 1, False,
+                                                                                         "insufficient_groups")
+    assert r.estimate is not None and r.std_error is None and r.p_value is None
+
+
+def test_the_database_counts_informative_groups_for_check_2_and_the_minimum(engine):
+    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
+    with pytest.raises(IntegrityError, match="ck_analysis_result_check2_consistent"):
+        _insert_result(engine, rid, n_groups=3, n_groups_informative=1, estimate=1.0, std_error=1.0, p_value=0.1)
+    _insert_result(engine, rid, n_groups=3, n_groups_informative=1, check2_passed=False, estimate=1.0)
+    assert rows_of(engine, "SELECT inference_reason FROM analysis_result WHERE run_id = :r", r=rid) == [
+        ("insufficient_groups",)]
+
+
+def test_the_database_takes_an_uncertainty_that_cannot_be_estimated(engine):
+    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
+    with pytest.raises(IntegrityError, match="ck_analysis_result_inference_reason"):
+        _insert_result(engine, rid, check2_passed=False, estimate=1.0, inference_reason="insufficient_groups")
+    _insert_result(engine, rid, check2_passed=False, estimate=1.0, inference_reason="uncertainty_not_estimable")
+
+
+def test_the_estimated_detection_rate_is_never_stored_for_a_withheld_result(engine):
+    rid = run_on(engine, small_rows(3, papers=3))  # fixed option: withheld
+    with pytest.raises(IntegrityError, match="ck_analysis_result_power_estimated_noise"):
+        _insert_result(engine, rid, estimated_power=0.5, estimated_power_estimated_noise=0.4)
+    _insert_result(engine, rid, estimated_power=0.5)
+
+
+def test_a_label_reason_is_stored_exactly_with_not_enough_data(engine):
+    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
+    analysis.run_statistics(engine, rid)
+    per_source = [r for r in result_rows(engine, rid) if r.scope == "per_source"]
+    assert all((r.label == "not_enough_data") == (r.label_reason is not None) for r in per_source)
diff --git a/tests/test_completion.py b/tests/test_completion.py
index 866199a..75ea12f 100644
--- a/tests/test_completion.py
+++ b/tests/test_completion.py
@@ -118,3 +118,14 @@ def test_the_database_checks_the_copy_again(engine, monkeypatch):
         completion.copy_decision(engine, rid)
     assert refused.value.code == "rejected_by_database"
     assert run_row(engine, rid).status == "running"
+
+
+def test_a_completed_run_needs_its_evidence_level(engine):
+    """Review (smaller point): the evidence level is required on every completed run."""
+    from sqlalchemy.exc import IntegrityError
+    pw.registered(engine, ("mpea",))
+    rid = pw.dispatched_run(engine, sources=("mpea",))
+    with pytest.raises(IntegrityError, match="ck_run_evidence_level_iff_completed"):
+        with engine.begin() as conn:
+            conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' "
+                              "WHERE id = :r"), dict(r=rid))
diff --git a/tests/test_concurrency.py b/tests/test_concurrency.py
index 5153584..4b668ab 100644
--- a/tests/test_concurrency.py
+++ b/tests/test_concurrency.py
@@ -155,7 +155,8 @@ def test_start_first_then_dispatch_metadata_is_rejected(w):
 
 # --- a child write against completion ----------------------------------------------------------------------
 
-COMPLETE = "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r"
+COMPLETE = ("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient', evidence_level = 1 "
+            "WHERE id = :r")  # step 7: a completed run needs its evidence level
 
 
 def test_flag_first_then_completion_waits(w):
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index a703569..db7527b 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -149,7 +149,7 @@ def test_narrower_question_links_only_to_a_partly_sufficient_run(w):
 def test_a_partly_sufficient_run_has_no_verdict(w):
     rid = w.running()
     w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
-               "verdict = 'supported' WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)
+               "verdict = 'supported', evidence_level = 6 WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)
 
 
 def test_narrower_question_has_the_original_domain(w):
@@ -184,7 +184,8 @@ def test_a_run_starts_queued(w):
 
 
 @pytest.mark.parametrize("sql", [
-    "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r",
+    "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient', evidence_level = 1 "
+    "WHERE id = :r",
     "UPDATE run SET status = 'queued' WHERE id = :r",
 ])
 def test_run_status_moves_only_forward(w, sql):
@@ -773,8 +774,9 @@ def test_a_record_extracted_after_the_freeze_cannot_slip_in_after_the_run_ends(w
     w.result(rid, sets["primary"])
     w.complete(rid, "sufficient", "supported")
     for sql in ["INSERT INTO analysis_set (run_id, key) VALUES (:r, 'extra')",
-                "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
-                "check1_passed, check2_passed, minimums_met) VALUES (:r, 'sensitivity', :s, 0, 0, 0, -1, false, false, false)"]:
+                "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
+                "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met) "
+                "VALUES (:r, 'sensitivity', :s, 0, 0, 0, 0, -1, false, false, false)"]:
         w.rejected(sql, "only while the run is running", r=rid, s=sets["primary"])
 
 
@@ -903,7 +905,8 @@ def test_the_validity_checks_cannot_be_waived(w, column, value, match):
         (False, None, None)]
     rid2, sets2, _ = w.frozen(option="use_available")
     columns = {"run_id": rid2, "scope": "'pooled'", "analysis_set_id": sets2["primary"], "n_records": 4,
-               "n_alloys": 1, "n_groups": 1, "resid_df": 2, "check1_passed": "true", "check2_passed": "false",
+               "n_alloys": 1, "n_groups": 1, "n_groups_informative": 1, "resid_df": 2, "check1_passed": "true",
+               "check2_passed": "false",
                "minimums_met": "false", "estimate": 1.0}
     columns[column] = value
     w.rejected(f"INSERT INTO analysis_result ({', '.join(columns)}) VALUES ({', '.join(map(str, columns.values()))})",
@@ -912,9 +915,10 @@ def test_the_validity_checks_cannot_be_waived(w, column, value, match):
 
 def test_check_one_failing_means_no_estimate(w):
     rid, sets, _ = w.frozen(n=1, mins=(1, 1, 1, 1))
-    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
-               "check1_passed, check2_passed, minimums_met, estimate) VALUES (:r, 'pooled', :s, 1, 0, 1, 0, false, "
-               "false, false, 5.0)", "ck_analysis_result_estimate_iff_check1", r=rid, s=sets["primary"])
+    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
+               "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate) "
+               "VALUES (:r, 'pooled', :s, 1, 0, 1, 1, 0, false, false, false, 5.0)",
+               "ck_analysis_result_estimate_iff_check1", r=rid, s=sets["primary"])
     w.result(rid, sets["primary"], n=1, alloys=0, groups=1, mins=(1, 1, 1, 1))
 
 
@@ -922,7 +926,6 @@ def test_check_one_failing_means_no_estimate(w):
     (1, 1, 1, "ck_analysis_result_two_records_per_alloy"),  # one record cannot show two grain sizes
     (4, 1, 5, "ck_analysis_result_groups_within_records"),
     (4, 0, 0, "ck_analysis_result_records_have_a_group"),
-    (4, 2, 2, "cannot exceed the distinct alloys"),         # the set has one alloy
 ])
 def test_stored_counts_must_be_consistent(w, n, alloys, groups, match):
     """Review finding 5: necessary conditions on the stored counts. The full validity
@@ -932,6 +935,18 @@ def test_stored_counts_must_be_consistent(w, n, alloys, groups, match):
         w.result(rid, sets["primary"], n=n, alloys=alloys, groups=groups, mins=(1, 1, 1, 1))
 
 
+def test_the_display_label_no_longer_bounds_the_alloy_count(w):
+    """Step 7 review, finding 2 (changed from the case "(4, 2, 2): cannot exceed the distinct alloys"
+    of test_stored_counts_must_be_consistent): the trigger no longer bounds the alloy count by the
+    display label, which is rounded to 0.1 at.% while the plan's same-alloy rule may be finer. Two
+    alloys in a set whose records share one label are stored; two records per alloy remain required."""
+    rid, sets, _ = w.frozen(n=4, mins=(1, 1, 1, 1))
+    assert w.val("SELECT count(DISTINCT r.alloy) FROM analysis_set_record sr JOIN record r ON r.id = sr.record_id "
+                 "WHERE sr.analysis_set_id = :s", s=sets["primary"]) == 1
+    w.result(rid, sets["primary"], n=4, alloys=2, groups=2, mins=(1, 1, 1, 1))
+    assert w.val("SELECT n_alloys FROM analysis_result WHERE run_id = :r", r=rid) == 2
+
+
 def test_one_result_per_run_and_scope_on_the_right_set(w):
     rid, sets, _ = w.frozen(n=4, per_source={"mpea": 3, "tamu_fcc": 1}, keys=["no_exclusions"])
     w.result(rid, sets["primary"])
@@ -942,8 +957,8 @@ def test_one_result_per_run_and_scope_on_the_right_set(w):
     with pytest.raises(IntegrityError, match="uses a sensitivity set"):
         w.result(rid, sets["primary"], scope="sensitivity")
     w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
-               "resid_df, check1_passed, check2_passed, minimums_met) "
-               "VALUES (:r, 'per_source', :s, 4, 0, 1, 3, false, false, false)",
+               "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met) "
+               "VALUES (:r, 'per_source', :s, 4, 0, 1, 1, 3, false, false, false)",
                "ck_analysis_result_source_iff_per_source", r=rid, s=sets["primary"])
     w.result(rid, sets["primary"], scope="per_source", source="mpea", n=3, alloys=1, groups=2)
     w.result(rid, sets["primary"], scope="per_source", source="tamu_fcc", n=1, alloys=0, groups=1)
diff --git a/tests/test_migrations_step7.py b/tests/test_migrations_step7.py
index 0b790bd..a27f395 100644
--- a/tests/test_migrations_step7.py
+++ b/tests/test_migrations_step7.py
@@ -53,14 +53,23 @@ def test_the_downgrade_keeps_0001s_functions_verbatim(name):
 
 
 def test_the_new_result_function_keeps_every_check_of_0001():
-    """Every check of 0001's function is in 0004's, unchanged, except the record count, which now
-    accounts for the records the fit does not use (decision 7)."""
+    """Every check of 0001's function is in 0004's, unchanged, except three: the record count now
+    accounts for the records the fit does not use (decision 7); the minimums count informative groups
+    (owner, 2026-10-06); and the bound of the alloy count by the display label is removed (review
+    finding 2: the label is rounded to 0.1 at.%, the plan's same-alloy rule may be finer)."""
     old, new = checks_of(M0004.ANALYSIS_RESULT_INSERT_0001), body(M0004.ANALYSIS_RESULT_INSERT_0004)
     changed = [c for c in old if c not in new]
-    assert changed == ["IF NEW.n_records <> set_count THEN PERFORM hc_reject('n_records must equal the records of "
-                       "the set used'); END IF;"]
+    assert changed == [
+        "IF NEW.n_records <> set_count THEN PERFORM hc_reject('n_records must equal the records of the set used'); "
+        "END IF;",
+        "IF NEW.n_alloys > set_alloys THEN PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the "
+        "set used'); END IF;",
+        "IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys AND NEW.n_groups "
+        ">= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN PERFORM hc_reject('minimums_met must agree with "
+        "the counts and the plan''s minimums'); END IF;"]
     assert ("IF NEW.n_records + NEW.n_records_not_used <> set_count THEN PERFORM hc_reject('n_records must equal "
             "the records of the set used, less those the fit does not use'); END IF;") in new
+    assert "NEW.n_groups_informative >= p.min_groups" in new and "set_alloys" not in new
 
 
 def test_the_new_calibration_function_keeps_the_run_level_rules_of_0001():
```


### Commit `fb5fd62`

```
fb5fd62 Step 7 review fixes: assumptions register (informative_groups, numerical_zero; reworded entries)

 hypocurate/assumptions.json | 229 ++++++++++++++++++++++++++++++++++++++------
 tests/test_assumptions.py   |   7 +-
 2 files changed, 205 insertions(+), 31 deletions(-)
```

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 210528c..0f18954 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -236,7 +236,7 @@
     "key": "fixed_minimums",
     "name": "Fixed minimums for data sufficiency",
     "state": "in_force",
-    "statement": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent papers and 10 residual degrees of freedom. All four must be met.",
+    "statement": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent informative papers (entry 'informative_groups') and 10 residual degrees of freedom, counted on the records a fit uses. All four must be met.",
     "value": {
       "text": "30 records; 5 alloys; 10 papers; 10 residual degrees of freedom",
       "unit": null
@@ -249,7 +249,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -284,6 +284,12 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "PRD 5.8."
+      },
+      {
+        "value": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent papers and 10 residual degrees of freedom. All four must be met.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "The paper minimum counts informative papers only (owner, 2026-10-06)."
       }
     ],
     "notes": [
@@ -296,7 +302,8 @@
       "tests/test_eligibility.py::test_counts_known_at_the_freeze",
       "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions",
       "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze",
-      "tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes"
+      "tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes",
+      "tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict"
     ]
   },
   {
@@ -495,14 +502,18 @@
     "notes": [
       "Conflicts with PRD 5.10, which says these assumptions are fixed at the rules lock and never estimated from the real outcomes.",
       "This is a safeguard change: it needs a second-model review in step 7 before it is applied.",
-      "Built in step 7 and awaiting the second-model review before the merge (owner, 2026-10-05). It departs from PRD 5.10, which fixes the noise levels in advance and never estimates them from the real outcomes: the estimate uses the frozen outcomes after the freeze, and can change no decision."
+      "Built in step 7 and awaiting the second-model review before the merge (owner, 2026-10-05). It departs from PRD 5.10, which fixes the noise levels in advance and never estimates them from the real outcomes: the estimate uses the frozen outcomes after the freeze, and can change no decision.",
+      "Review fixes (2026-10-06): every estimated calibration states that its intervals cover Monte Carlo uncertainty only, not uncertainty in the estimated scatter and shift, and that it is a diagnostic conditional on the estimate (truncation biases it), not independent validation. A residual at most the numerical zero of the outcome's spread within alloys is a perfect fit: scatter not estimable."
     ],
     "tests": [
       "tests/test_calibration.py::test_a_negative_shift_estimate_is_set_to_zero_and_the_result_says_so",
       "tests/test_calibration.py::test_a_shift_explained_by_the_alloys_cannot_be_estimated",
       "tests/test_calibration.py::test_method_iii_matches_an_independent_computation",
       "tests/test_calibration.py::test_method_iii_recovers_known_noise_levels_on_a_large_generated_dataset",
-      "tests/test_calibration.py::test_the_scatter_cannot_be_estimated_without_residual_freedom_in_the_full_model"
+      "tests/test_calibration.py::test_the_scatter_cannot_be_estimated_without_residual_freedom_in_the_full_model",
+      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_scatter",
+      "tests/test_statistics_boundaries.py::test_every_estimated_calibration_states_what_its_intervals_cover",
+      "tests/test_statistics_boundaries.py::test_small_real_noise_gives_an_estimable_scatter"
     ],
     "pending": {
       "by": "second-model technical review",
@@ -1868,7 +1879,7 @@
     "key": "validity_checks",
     "name": "The two validity checks",
     "state": "in_force",
-    "statement": "Check 1: at least one alloy measured at two distinct grain sizes, or nothing is fitted. Check 2: at least 1 residual degree of freedom and at least 2 independent groups, or the coefficient is reported alone with no uncertainty, no p-value and no verdict. Neither can be waived.",
+    "statement": "Check 1: at least one alloy measured at two grain sizes that are distinct after the transformation, or nothing is fitted. Check 2: at least 1 residual degree of freedom, at least 2 informative groups (entry 'informative_groups'), and a clustered standard error that is finite and above the numerical zero (entry 'numerical_zero'); otherwise the coefficient is reported alone, with the reason, and no uncertainty, no p-value and no verdict. Neither can be waived. The same checks apply to every simulated fit.",
     "value": {
       "text": "check 1: 1 alloy at 2 grain sizes; check 2: 1 residual df and 2 groups",
       "unit": null
@@ -1880,8 +1891,8 @@
       "PRD 5.7; CLAUDE.md, rule 5."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1898,14 +1909,27 @@
         {
           "ref": "sql:ck_analysis_result_check2_consistent"
         },
+        {
+          "ref": "sql:ck_analysis_result_inference_reason"
+        },
         {
           "ref": "python:hypocurate.pipeline.statistics:MODEL_MIN_GRAIN_SIZES",
           "equals": 2
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:INFERENCE_REASONS"
         }
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Check 1: at least one alloy measured at two distinct grain sizes, or nothing is fitted. Check 2: at least 1 residual degree of freedom and at least 2 independent groups, or the coefficient is reported alone with no uncertainty, no p-value and no verdict. Neither can be waived.",
+        "from": "2026-10-04",
+        "to": "2026-10-06",
+        "note": "Step 7 review, finding 1 and the owner's decision on informative papers (2026-10-06)."
+      }
+    ],
     "notes": [],
     "tests": [
       "tests/test_analysis_stage.py::test_use_what_is_available_with_one_group_gives_the_coefficient_only",
@@ -1913,7 +1937,10 @@
       "tests/test_data_model.py::test_stored_counts_must_be_consistent",
       "tests/test_data_model.py::test_the_validity_checks_cannot_be_waived",
       "tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option",
-      "tests/test_statistics.py::test_the_two_validity_checks"
+      "tests/test_statistics.py::test_the_two_validity_checks",
+      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only",
+      "tests/test_statistics_boundaries.py::test_grain_sizes_equal_after_transformation_never_raise",
+      "tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict"
     ]
   },
   {
@@ -2148,13 +2175,15 @@
     },
     "history": [],
     "notes": [
-      "Step 7 finding (reported, not gated): on the sets frozen in step 6 the fixed method gives about 7.8% significant no-effect results for the pooled set and 8.0% for the earlier 98-record set over long runs (40,000 simulations), and the reference script's own loop gives the same; PRD 5.10's 7.2% (6.1% to 8.4%) is not reproduced."
+      "Step 7 finding (reported, not gated): on the sets frozen in step 6 the fixed method gives about 7.8% significant no-effect results for the pooled set and 8.0% for the earlier 98-record set over long runs (40,000 simulations), and the reference script's own loop gives the same; PRD 5.10's 7.2% (6.1% to 8.4%) is not reproduced.",
+      "Review fix (2026-10-06): each simulated fit gets the real fit's validity checks; a simulated standard error that is not finite or not above the numerical zero gives no inference and is not counted as significant."
     ],
     "tests": [
       "tests/test_calibration.py::test_each_world_draws_shifts_then_errors_from_one_seeded_generator",
       "tests/test_calibration.py::test_the_interval_is_the_exact_binomial_interval",
       "tests/test_calibration.py::test_the_seed_is_fixed_by_the_freeze_the_analysis_and_the_method",
-      "tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values"
+      "tests/test_generated_fixed_set.py::test_states_levels_verdicts_and_simulated_counts_equal_the_stored_values",
+      "tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit"
     ]
   },
   {
@@ -5286,12 +5315,19 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it, and so does the estimated power, which is the share detected in the fixed method's effect world, labelled 'estimated power under the stated assumptions'. The power is information only and uses no outcome value, so it is shown also below the minimums.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Review, smaller point (2026-10-06): detection rates both ways, with the false-positive shares."
+      }
+    ],
     "notes": [],
     "key": "smallest_effect",
     "name": "Smallest effect of interest",
     "state": "in_force",
-    "statement": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it, and so does the estimated power, which is the share detected in the fixed method's effect world, labelled 'estimated power under the stated assumptions'. The power is information only and uses no outcome value, so it is shown also below the minimums.",
+    "statement": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it. The detection rate is reported both ways, each beside its false-positive share: under the fixed assumptions (stored as the estimated power, labelled 'estimated power under the stated assumptions', shown also below the minimums, since it uses no outcome value) and under the estimated noise (withheld below the minimums). Both are detection rates of the nominal 5% test, not power for a test shown to keep false positives at 5%. Information only.",
     "value": {
       "text": "150 (default)",
       "unit": "MPa·µm^0.5"
@@ -5304,7 +5340,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "applied": {
       "status": "yes",
@@ -5321,8 +5357,11 @@
       "note": null
     },
     "tests": [
+      "tests/test_analysis_stage.py::test_the_estimated_detection_rate_is_never_stored_for_a_withheld_result",
       "tests/test_calibration.py::test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome",
-      "tests/test_statistics.py::test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting"
+      "tests/test_statistics.py::test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting",
+      "tests/test_statistics_boundaries.py::test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld",
+      "tests/test_statistics_boundaries.py::test_detection_rates_are_reported_both_ways_with_the_false_positive_shares"
     ]
   },
   {
@@ -5363,16 +5402,20 @@
         },
         {
           "ref": "sql:ck_run_evidence_level"
+        },
+        {
+          "ref": "sql:ck_run_evidence_level_iff_completed"
         }
       ],
-      "note": "Copied onto the run by the copy path only; the database checks it agrees with the outcome, verdict and exploratory label but does not require it on a completed run."
+      "note": "Copied onto the run by the copy path; required on every completed run and only on one, and checked against the outcome, verdict and exploratory label by the database (review, smaller point, 2026-10-06)."
     },
     "tests": [
+      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates",
+      "tests/test_analysis_stage.py::test_the_evidence_level_must_agree_with_the_outcome",
+      "tests/test_completion.py::test_a_completed_run_needs_its_evidence_level",
       "tests/test_statistics.py::test_every_result_state_has_its_evidence_level",
       "tests/test_statistics.py::test_the_evidence_scale_is_the_owners",
-      "tests/test_statistics.py::test_the_level_never_feeds_back_into_the_outcome_or_verdict",
-      "tests/test_analysis_stage.py::test_the_evidence_level_must_agree_with_the_outcome",
-      "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates"
+      "tests/test_statistics.py::test_the_level_never_feeds_back_into_the_outcome_or_verdict"
     ]
   },
   {
@@ -5382,12 +5425,19 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Each per-source result has one of four labels, from the locked test and the sign only, no new threshold: 'not enough data' (no p-value; also when the pooled result has none, or a coefficient is exactly zero); 'agrees' (the same decision as pooled at the plan's threshold and the same sign); 'conflicts' (the opposite sign from pooled); 'same direction, different decision' (the same sign, a different decision). Descriptive only; never the verdict.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Review, smaller point (2026-10-06): a zero coefficient has its own reason."
+      }
+    ],
     "notes": [],
     "key": "per_source_labels",
     "name": "Per-source labels",
     "state": "in_force",
-    "statement": "Each per-source result has one of four labels, from the locked test and the sign only, no new threshold: 'not enough data' (no p-value; also when the pooled result has none, or a coefficient is exactly zero); 'agrees' (the same decision as pooled at the plan's threshold and the same sign); 'conflicts' (the opposite sign from pooled); 'same direction, different decision' (the same sign, a different decision). Descriptive only; never the verdict.",
+    "statement": "Each per-source result has one of four labels, from the locked test and the sign only, no new threshold: 'not enough data' (no p-value; also when the pooled result has none, or a coefficient is exactly zero); 'agrees' (the same decision as pooled at the plan's threshold and the same sign); 'conflicts' (the opposite sign from pooled); 'same direction, different decision' (the same sign, a different decision). Descriptive only; never the verdict. Each 'not enough data' carries its reason: no p-value, the pooled result without a decision, or a zero coefficient (zero direction is not missing inference).",
     "value": {
       "text": "agrees; conflicts; same direction, different decision; not enough data",
       "unit": null
@@ -5400,7 +5450,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "applied": {
       "status": "yes",
@@ -5416,14 +5466,24 @@
         },
         {
           "ref": "sql:ck_analysis_result_label_per_source_only"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:LABEL_REASONS",
+          "equals": [
+            "no_p_value",
+            "pooled_without_decision",
+            "zero_coefficient"
+          ]
         }
       ],
       "note": "The edge rules for a pooled result without a decision and a zero coefficient are Claude Code's, stated in planning."
     },
     "tests": [
-      "tests/test_statistics.py::test_the_four_per_source_labels",
+      "tests/test_analysis_stage.py::test_a_label_reason_is_stored_exactly_with_not_enough_data",
       "tests/test_reference_numbers.py::test_mpea_alone_1_per_source_in_the_pooled_run",
-      "tests/test_reference_numbers.py::test_texas_am_alone_1_per_source_in_the_pooled_run"
+      "tests/test_reference_numbers.py::test_texas_am_alone_1_per_source_in_the_pooled_run",
+      "tests/test_statistics.py::test_the_four_per_source_labels",
+      "tests/test_statistics_boundaries.py::test_a_zero_coefficient_has_its_own_reason"
     ]
   },
   {
@@ -5433,14 +5493,21 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Each fit (pooled, per source, sensitivity) uses only alloys with at least two distinct grain sizes among that analysis's own records: the model's own condition, applied by code to grain sizes only. The frozen set is not changed; the records not used are counted and reported as 'not used in this fit'. The stored counts, and the minimums, are the fit's.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Review, finding 3 (2026-10-06): 9.0 and 9.000000000000002 µm transform to one value."
+      }
+    ],
     "notes": [
       "No effect on the reference numbers: the two sources share no alloy."
     ],
     "key": "fit_alloy_rule",
     "name": "Which records a fit uses",
     "state": "in_force",
-    "statement": "Each fit (pooled, per source, sensitivity) uses only alloys with at least two distinct grain sizes among that analysis's own records: the model's own condition, applied by code to grain sizes only. The frozen set is not changed; the records not used are counted and reported as 'not used in this fit'. The stored counts, and the minimums, are the fit's.",
+    "statement": "Each fit (pooled, per source, sensitivity) uses only alloys with at least two grain sizes among that analysis's own records that are distinct after the transformation (by more than the numerical zero): the model's own condition, applied by code to grain sizes only. The frozen set is not changed; the records not used are counted and reported as 'not used in this fit'. The stored counts, and the minimums, are the fit's.",
     "value": {
       "text": "two or more distinct grain sizes per alloy, within each fit",
       "unit": null
@@ -5453,7 +5520,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "applied": {
       "status": "yes",
@@ -5469,8 +5536,10 @@
       "note": null
     },
     "tests": [
+      "tests/test_analysis_stage.py::test_the_database_refuses_records_not_accounted_for",
       "tests/test_statistics.py::test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes",
-      "tests/test_analysis_stage.py::test_the_database_refuses_records_not_accounted_for"
+      "tests/test_statistics_boundaries.py::test_grain_sizes_equal_after_transformation_never_raise",
+      "tests/test_statistics_boundaries.py::test_nearly_equal_transformed_grain_sizes_are_not_distinct"
     ]
   },
   {
@@ -5569,7 +5638,9 @@
       "date": null
     },
     "history": [],
-    "notes": [],
+    "notes": [
+      "Second-model review (2026-10-06): failing closed is safe; keep the explicit skipped-analysis record and invent no singleton papers. Still open: whether a permitted coefficient-only result should remain available when grouping is missing."
+    ],
     "key": "records_without_group",
     "name": "Records without a group in a fit",
     "state": "open",
@@ -5602,5 +5673,103 @@
       "by": "owner",
       "before_step": 8
     }
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
+    "state": "in_force",
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
+    "key": "informative_groups",
+    "name": "Informative papers",
+    "statement": "The minimum of independent papers, and validity check 2's 'at least two groups', count only informative papers: papers whose records help estimate the slope, that is, with at least one record whose transformed grain size differs from its alloy's average by more than the numerical zero. Uninformative papers stay in the fit and are listed with the result, but are not counted. The standard error's small-sample factor and the t distribution's degrees of freedom still use every group of the fit (statsmodels' definition).",
+    "value": {
+      "text": "count informative papers for the minimum and for check 2",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Validity check 2, the paper minimum, the withheld state and the evidence level; on the reference sets every group is informative, so no reference number changed.",
+    "reason": "Groups whose records sit at their alloy's average grain size add nothing to the slope's clustered uncertainty, so counting them inflated the number of independent papers (second-model review, finding 1).",
+    "evidence": [
+      "Second-model review, finding 1 (ChatGPT, 2026-10-06): docs/reviews/step07_review_chatgpt.md.",
+      "Owner's decision, 2026-10-06."
+    ],
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:minimums"
+        },
+        {
+          "ref": "sql:n_groups_informative"
+        },
+        {
+          "ref": "sql:ck_analysis_result_check2_consistent"
+        }
+      ],
+      "note": "Whether the degrees of freedom should also count informative papers only is not decided; they use every group, as CLAUDE.md rule 6 states."
+    },
+    "tests": [
+      "tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict",
+      "tests/test_statistics_boundaries.py::test_a_paper_is_informative_when_its_records_vary_after_removing_the_alloy_average",
+      "tests/test_analysis_stage.py::test_the_reviewers_design_through_the_database",
+      "tests/test_analysis_stage.py::test_the_database_counts_informative_groups_for_check_2_and_the_minimum"
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
+    "state": "in_force",
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
+    "key": "numerical_zero",
+    "name": "Numerical zero",
+    "statement": "A quantity counts as zero when it is at most 1e-10 times its natural scale in the same units: a transformed grain-size difference or contrast against the largest transformed grain size; the clustered standard error against sqrt(Σ ỹ² / Σ x̃²), the slope scale of the data; the residual sum of squares of the scatter estimate against the outcome's spread within alloys (squared). Below it: grain sizes are not distinct, an uncertainty is not estimable (coefficient only), or scatter is not estimable. The same check applies to every simulated fit.",
+    "value": {
+      "text": "1e-10 relative to the natural scale",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Numerical boundaries only: rounding residue is about 1e-16 of the scale, real measurement scatter many orders above 1e-10; no reference number changed.",
+    "reason": "Second-model review, findings 1, 3 and 4: a zero or rounding-residue standard error gave p = 0; equal transformed grain sizes raised an error; a perfect fit was taken for real scatter.",
+    "evidence": [
+      "Second-model review (ChatGPT, 2026-10-06): docs/reviews/step07_review_chatgpt.md."
+    ],
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.statistics:RELATIVE_ZERO",
+          "equals": 1e-10
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only",
+      "tests/test_statistics_boundaries.py::test_small_real_noise_keeps_the_uncertainty_estimable",
+      "tests/test_statistics_boundaries.py::test_the_uncertainty_check_is_scale_aware",
+      "tests/test_statistics_boundaries.py::test_grain_sizes_equal_after_transformation_never_raise",
+      "tests/test_statistics_boundaries.py::test_nearly_equal_transformed_grain_sizes_are_not_distinct",
+      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_scatter",
+      "tests/test_statistics_boundaries.py::test_small_real_noise_gives_an_estimable_scatter",
+      "tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit"
+    ]
   }
 ]
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 11f8479..31f1f07 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -70,7 +70,12 @@ def test_the_owners_eight_decisions_are_recorded_as_decided():
         expected_state = "direction_approved" if key == "calibration_noise_levels" else "in_force"
         assert e["state"] == expected_state, key
         assert e["category"] == category, key
-        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
+        # fixed_minimums: reworded by the owner on 2026-10-06 (informative papers); the 2026-10-05 wording is in history.
+        if key == "fixed_minimums":
+            assert e["decided"] == {"by": OWNER, "date": "2026-10-06"} and "informative" in e["statement"]
+            assert e["history"][-1]["value"].startswith("Under the default sufficiency option, a test needs at least 30")
+        else:
+            assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
         assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}, key
         assert e["applied"]["status"] == status and e["applied"].get("step") == step, key
         assert (status == "partly") == (key in PARTLY), key
```


### Commit `496644e`

```
496644e Step 7: informative papers in the small-sample factor and the degrees of freedom (owner, 2026-10-06)

 CLAUDE.md                           |   2 +-
 hypocurate/assumptions.json         | 102 +++++++++++++++++++++++++++++++-----
 hypocurate/pipeline/analysis.py     |   4 +-
 hypocurate/pipeline/calibration.py  |  11 ++--
 hypocurate/pipeline/statistics.py   |  28 +++++-----
 tests/reference_stats.py            |  36 +++++++++++++
 tests/test_informative_inference.py |  97 ++++++++++++++++++++++++++++++++++
 7 files changed, 248 insertions(+), 32 deletions(-)
```

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index d933113..5fdd597 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -36,7 +36,7 @@ The full specification is `docs/PRD_sprint1.md`. Read the relevant section befor
 3. **Two checkpoints (PRD 5.6).** *Rules lock* before curation: the model, scope, exclusion rules and data-sufficiency option are fixed. *Dataset freeze* before analysis: the record set is fixed and fingerprinted. Nothing changes after its checkpoint, by agent or by person. Later removals are sensitivity analyses only and never change the verdict.
 4. **Stored is not analysed (PRD 5.3).** Every record found is kept. Eligibility for the test is a separate decision by code under the locked rules. Conflicting records are preserved, not automatically pooled.
 5. **Two validity checks that can never be waived (PRD 5.7).** (1) Can a coefficient be fitted? (2) Is inference valid (at least 1 residual degree of freedom and at least 2 independent groups)? If 1 passes and 2 fails: report the coefficient only, with no uncertainty, no p-value and no verdict.
-6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction; one-sided test of k > 0 at 0.05 against a t distribution with (groups − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
+6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction, counting informative papers only (papers whose records help estimate the slope); one-sided test of k > 0 at 0.05 against a t distribution with (informative papers − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
 7. **Data sufficiency is a query parameter fixed at rules lock (PRD 5.8).** Default: fixed minimum (30 records, 5 alloys with at least 2 grain sizes, 10 independent papers, 10 residual degrees of freedom). "Use what is available" waives the threshold only, never the validity checks, and labels the result exploratory.
 8. **A narrower question is a separate record**, linked to the original. The original gets no verdict.
 9. **Three kinds of "nothing found" stay distinct:** a reported negative result, missing evidence, and a failed search.
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 0f18954..e3117af 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -1620,7 +1620,7 @@
     "key": "cluster_robust_se",
     "name": "Grouped standard error",
     "state": "in_force",
-    "statement": "The standard error of k is cluster-robust, with records grouped by each source's grouping unit (the paper for literature data), with the small-sample correction.",
+    "statement": "The standard error of k is cluster-robust, with records grouped by each source's grouping unit (the paper for literature data), summing the scores of informative groups only, with the small-sample correction G/(G-1) × (N-1)/(N-K), G the informative groups (entry 'informative_groups_in_inference').",
     "value": {
       "text": "cluster-robust by grouping unit, with small-sample correction",
       "unit": null
@@ -1632,8 +1632,8 @@
       "PRD 5.7 (uncertainty row); docs/reference/worked_example.py (statsmodels cov_type='cluster')."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1650,13 +1650,22 @@
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "The standard error of k is cluster-robust, with records grouped by each source's grouping unit (the paper for literature data), with the small-sample correction.",
+        "from": "2026-10-04",
+        "to": "2026-10-06",
+        "note": "Owner, 2026-10-06: informative papers in the factor and the degrees of freedom."
+      }
+    ],
     "notes": [
       "The reference numbers used statsmodels' default cluster correction; step 7 states the exact formula.",
       "Step 7: the exact formula is G/(G-1) × (N-1)/(N-K), K = alloys + 1, statsmodels' default for clustered errors (statistics.small_sample_factor)."
     ],
     "tests": [
       "tests/test_generated_fixed_set.py::test_coefficient_uncertainty_and_p_match_the_reference_implementation",
+      "tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only",
+      "tests/test_informative_inference.py::test_the_result_is_more_cautious_than_counting_every_paper",
       "tests/test_statistics.py::test_the_small_sample_correction_is_statsmodels_default"
     ]
   },
@@ -1753,9 +1762,9 @@
     "key": "one_sided_test",
     "name": "The test",
     "state": "in_force",
-    "statement": "Null hypothesis k <= 0, alternative k > 0. One-sided test at a threshold of 0.05 unless the plan sets another, against a t distribution with (number of groups - 1) degrees of freedom.",
+    "statement": "Null hypothesis k <= 0, alternative k > 0. One-sided test at a threshold of 0.05 unless the plan sets another, against a t distribution with (informative groups − 1) degrees of freedom (entry 'informative_groups_in_inference').",
     "value": {
-      "text": "one-sided; threshold 0.05; t with groups - 1 degrees of freedom",
+      "text": "one-sided; threshold 0.05; t with informative groups − 1 degrees of freedom",
       "unit": null
     },
     "category": "statistical",
@@ -1765,8 +1774,8 @@
       "PRD 5.7 (hypotheses row); CLAUDE.md, rule 6."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1787,9 +1796,17 @@
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Null hypothesis k <= 0, alternative k > 0. One-sided test at a threshold of 0.05 unless the plan sets another, against a t distribution with (number of groups - 1) degrees of freedom.",
+        "from": "2026-10-04",
+        "to": "2026-10-06",
+        "note": "Owner, 2026-10-06: informative papers in the factor and the degrees of freedom."
+      }
+    ],
     "notes": [],
     "tests": [
+      "tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only",
       "tests/test_statistics.py::test_a_zero_standard_error_gives_a_defined_p_value",
       "tests/test_statistics.py::test_the_test_is_one_sided"
     ]
@@ -5681,7 +5698,14 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "(as above, and:) The standard error's small-sample factor and the t distribution's degrees of freedom still use every group of the fit (statsmodels' definition).",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Owner, 2026-10-06: they count informative papers too (entry 'informative_groups_in_inference')."
+      }
+    ],
     "notes": [],
     "state": "in_force",
     "decided": {
@@ -5690,7 +5714,7 @@
     },
     "key": "informative_groups",
     "name": "Informative papers",
-    "statement": "The minimum of independent papers, and validity check 2's 'at least two groups', count only informative papers: papers whose records help estimate the slope, that is, with at least one record whose transformed grain size differs from its alloy's average by more than the numerical zero. Uninformative papers stay in the fit and are listed with the result, but are not counted. The standard error's small-sample factor and the t distribution's degrees of freedom still use every group of the fit (statsmodels' definition).",
+    "statement": "The minimum of independent papers, and validity check 2's 'at least two groups', count only informative papers: papers whose records help estimate the slope, that is, with at least one record whose transformed grain size differs from its alloy's average by more than the numerical zero. Uninformative papers stay in the fit and are listed with the result, but are not counted.",
     "value": {
       "text": "count informative papers for the minimum and for check 2",
       "unit": null
@@ -5715,7 +5739,7 @@
           "ref": "sql:ck_analysis_result_check2_consistent"
         }
       ],
-      "note": "Whether the degrees of freedom should also count informative papers only is not decided; they use every group, as CLAUDE.md rule 6 states."
+      "note": null
     },
     "tests": [
       "tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict",
@@ -5771,5 +5795,59 @@
       "tests/test_statistics_boundaries.py::test_small_real_noise_gives_an_estimable_scatter",
       "tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit"
     ]
+  },
+  {
+    "key": "informative_groups_in_inference",
+    "name": "Informative papers in the uncertainty and the test",
+    "state": "in_force",
+    "statement": "The clustered standard error sums the scores of informative papers only, its small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative papers, and the one-sided test uses a t distribution with (informative papers − 1) degrees of freedom: the same count as validity check 2 and the paper minimum. Applied in the real fits and in every simulated fit. With uninformative papers present this gives a larger standard error and fewer degrees of freedom than counting every paper (the cautious direction); where every paper is informative it equals statsmodels' clustered result.",
+    "value": {
+      "text": "G = informative papers in the factor and in the degrees of freedom",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Standard errors, p-values and simulated rejection rates of any fit with uninformative papers; on the reference sets every paper is informative, so no reference number changed.",
+    "reason": "An uninformative paper adds nothing to the slope's clustered variance; counting it in G/(G-1) and in the degrees of freedom made the test less cautious than its information supports.",
+    "evidence": [
+      "Owner's decision, 2026-10-06, after the second-model review (docs/reviews/step07_review_chatgpt.md, finding 1)."
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
+          "ref": "python:hypocurate.pipeline.statistics:small_sample_factor"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:fit"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.calibration:significant_count"
+        },
+        {
+          "ref": "file:CLAUDE.md:(informative papers − 1) degrees of freedom"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only",
+      "tests/test_informative_inference.py::test_the_result_is_more_cautious_than_counting_every_paper",
+      "tests/test_informative_inference.py::test_where_every_paper_is_informative_nothing_changes",
+      "tests/test_informative_inference.py::test_every_simulated_fit_counts_informative_papers_only"
+    ],
+    "history": [],
+    "notes": [
+      "CLAUDE.md rule 6 reworded to match (owner, 2026-10-06)."
+    ]
   }
 ]
diff --git a/hypocurate/pipeline/analysis.py b/hypocurate/pipeline/analysis.py
index bc313b9..f763384 100644
--- a/hypocurate/pipeline/analysis.py
+++ b/hypocurate/pipeline/analysis.py
@@ -144,8 +144,8 @@ def analyse(plan: Mapping, data: Mapping) -> dict:
             if estimated["status"] == "computed":
                 entry["estimated_power_estimated_noise"] = estimated["effect"]["share"]
     return {"freeze_fingerprint": fp, "model": plan["model"]["name"],
-            "test": "one-sided t test of k > 0 against t with (groups - 1) degrees of freedom; "
-                    "cluster-robust standard error by group with the small-sample correction",
+            "test": "one-sided t test of k > 0 against t with (informative groups - 1) degrees of freedom; "
+                    "cluster-robust standard error by group with the small-sample correction over informative groups",
             "alpha": alpha, "sufficiency_option": plan["sufficiency"]["option"], "withheld": withheld,
             "analyses": entries, "not_analysed": not_analysed, "decision": st.decision(pooled, plan, fp)}
 
diff --git a/hypocurate/pipeline/calibration.py b/hypocurate/pipeline/calibration.py
index aa91b5c..75924ef 100644
--- a/hypocurate/pipeline/calibration.py
+++ b/hypocurate/pipeline/calibration.py
@@ -102,8 +102,8 @@ def confidence_flag(low: float, high: float, alpha: float) -> str:
 
 def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
     """How many rows of `outcomes` (simulations × records) the locked test finds significant:
-    the same estimator, standard error, correction, validity checks and one-sided t test as
-    `statistics.fit`. A simulated fit whose standard error is not finite or not above the numerical
+    the same estimator, standard error, correction (informative groups), validity checks and one-sided
+    t test (informative groups - 1 degrees of freedom) as `statistics.fit`. A simulated fit whose standard error is not finite or not above the numerical
     zero gives no inference, so it is never significant (review finding 1)."""
     if not d.counts_allow_inference:
         return 0
@@ -114,14 +114,15 @@ def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
     e = yd - k[:, None] * xd[None, :]
     groups = np.zeros((d.n, d.n_groups))
     groups[np.arange(d.n), d.group] = 1.0
-    scores = (e * xd[None, :]) @ groups
-    variance = (scores ** 2).sum(axis=1) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
+    # Informative groups only, as in the real fit (owner, 2026-10-06).
+    scores = ((e * xd[None, :]) @ groups)[:, d.group_informative]
+    variance = (scores ** 2).sum(axis=1) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)
     with np.errstate(divide="ignore", invalid="ignore"):
         se = np.sqrt(variance)
         scale = np.sqrt((yd ** 2).sum(axis=1) / sxx)
         valid = np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)
         t = np.where(valid, k / np.where(valid, se, 1.0), 0.0)
-    p = stats.t.sf(t, d.n_groups - 1)
+    p = stats.t.sf(t, d.n_groups_informative - 1)
     return int(np.count_nonzero(valid & (p < alpha)))
 
 
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index f7234bb..014e65e 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -6,10 +6,10 @@ alloy + k × (grain size in µm)^-1/2. Ordinary least squares with one intercept
 shared coefficient k, computed by removing each alloy's mean from the predictor and the outcome
 (the same estimate as fitting the alloy intercepts; Frisch-Waugh-Lovell). Its standard error is
 cluster-robust, grouped by each source's grouping unit, with the small-sample correction
-G/(G-1) × (N-1)/(N-K), K = alloys + 1 (statsmodels' default for clustered errors; register
-'cluster_robust_se'). The test is one-sided, k > 0, against a t distribution with G - 1 degrees of
-freedom, at the plan's threshold; "supported" exactly when p < alpha (register
-'p_threshold_comparison').
+G/(G-1) × (N-1)/(N-K), K = alloys + 1, G the informative groups (statsmodels' formula when every
+group is informative; register 'cluster_robust_se'). The test is one-sided, k > 0, against a t
+distribution with G - 1 degrees of freedom, G the informative groups, at the plan's threshold;
+"supported" exactly when p < alpha (register 'p_threshold_comparison').
 
 **Which records a fit uses** (owner, 2026-10-05, decision 7): only alloys with at least
 `MODEL_MIN_GRAIN_SIZES` distinct grain sizes among the analysis's own records, distinct after the
@@ -21,9 +21,10 @@ the records the fit uses** (owner, 2026-10-05).
 **Informative papers** (owner, 2026-10-06; register 'informative_groups'): a group is informative
 when at least one of its records differs from its alloy's average transformed grain size by more
 than the numerical zero, so that the group helps estimate the slope. Uninformative groups stay in
-the fit and are listed, but are not counted for the paper minimum or for validity check 2. The
-standard error's small-sample factor and the t distribution's degrees of freedom still use every
-group of the fit (statsmodels' definition, CLAUDE.md rule 6).
+the fit and are listed, but are not counted for the paper minimum, for validity check 2, for the standard error's
+small-sample factor or for the t distribution's degrees of freedom (owner, 2026-10-06; register
+'informative_groups_in_inference'; CLAUDE.md rule 6). The clustered covariance sums the scores of
+informative groups only (an uninformative group's score is zero up to rounding).
 
 **The two validity checks** can never be waived (CLAUDE.md rule 5): (1) a coefficient can be fitted
 when at least one alloy has two distinct grain sizes; (2) inference is valid with at least 1
@@ -130,6 +131,7 @@ class Design:
     n_alloys_not_used: int
     n_groups_informative: int = 0
     uninformative_groups: tuple = ()
+    group_informative: np.ndarray = None  # per group index: does the group count (informative)?
 
     @property
     def n(self) -> int:
@@ -178,7 +180,8 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
         group=np.array([group_index[o.group] for o in used], dtype=int),
         n_alloys=len(used_alloys), n_groups=len(groups), n_records_in_set=len(obs),
         n_alloys_not_used=len(values) - len(used_alloys), n_groups_informative=len(informative),
-        uninformative_groups=tuple(g for g in groups if g not in informative))
+        uninformative_groups=tuple(g for g in groups if g not in informative),
+        group_informative=np.array([g in informative for g in groups], dtype=bool))
 
 
 def distinct_values(values: list) -> int:
@@ -200,7 +203,7 @@ def demeaned(values: np.ndarray, alloy: np.ndarray, n_alloys: int) -> np.ndarray
 
 
 def small_sample_factor(n: int, n_alloys: int, n_groups: int) -> float:
-    """G/(G-1) × (N-1)/(N-K), K = alloys + 1 (register 'cluster_robust_se')."""
+    """G/(G-1) × (N-1)/(N-K), K = alloys + 1, G the informative groups (register 'cluster_robust_se')."""
     return (n_groups / (n_groups - 1)) * ((n - 1) / (n - n_alloys - 1))
 
 
@@ -237,13 +240,14 @@ def fit(d: Design) -> Fit | None:
     if not d.counts_allow_inference:
         return Fit(k, None, None, None, None, "insufficient_groups")
     e = yd - k * xd
-    scores = np.bincount(d.group, xd * e, d.n_groups)
-    variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups)
+    # Informative groups only (owner, 2026-10-06): their scores, their count in the factor and the df.
+    scores = np.bincount(d.group, xd * e, d.n_groups)[d.group_informative]
+    variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)
     se = math.sqrt(variance) if math.isfinite(variance) and variance >= 0 else math.nan
     if not (math.isfinite(se) and se > RELATIVE_ZERO * math.sqrt(float(yd @ yd) / sxx)):
         return Fit(k, None, None, None, None, "uncertainty_not_estimable")
     t = k / se
-    df = d.n_groups - 1
+    df = d.n_groups_informative - 1
     return Fit(k, se, t, df, one_sided_p(t, df))
 
 
diff --git a/tests/reference_stats.py b/tests/reference_stats.py
index 55376be..17e94db 100644
--- a/tests/reference_stats.py
+++ b/tests/reference_stats.py
@@ -72,3 +72,39 @@ def significant_count(x, alloy, group, outcomes, alpha) -> int:
         m = sm.OLS(y, exog).fit(cov_type="cluster", cov_kwds={"groups": group})
         hits += stats.t.sf(m.params[0] / m.bse[0], g - 1) < alpha
     return int(hits)
+
+
+def informative_groups(rows, relative_zero=1e-10) -> set:
+    """Test-side: groups with a record whose transformed grain size differs from its alloy's average
+    by more than relative_zero × the largest transformed grain size (alloys with two or more grain sizes)."""
+    f = frame(rows)
+    if f.empty:
+        return set()
+    contrast = (f["x"] - f.groupby("alloy")["x"].transform("mean")).abs()
+    return set(f.loc[contrast > relative_zero * f["x"].abs().max(), "group"])
+
+
+def fit_informative(rows) -> dict:
+    """The owner's rule of 2026-10-06 computed independently with an explicit sandwich (numpy, dummy
+    variables, no statsmodels): the clustered covariance sums the scores of informative groups only, the
+    small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative groups, and the one-sided p-value
+    uses t with G - 1 degrees of freedom."""
+    f = frame(rows)
+    informative = informative_groups(rows)
+    alloys = sorted(f["alloy"].unique())
+    x = np.column_stack([f["x"].to_numpy()] + [(f["alloy"] == a).to_numpy(dtype=float) for a in alloys])
+    y = f["y"].to_numpy()
+    bread = np.linalg.inv(x.T @ x)
+    beta = bread @ x.T @ y
+    e = y - x @ beta
+    meat = np.zeros((x.shape[1], x.shape[1]))
+    for g in informative:
+        rows_g = (f["group"] == g).to_numpy()
+        s = x[rows_g].T @ e[rows_g]
+        meat += np.outer(s, s)
+    n, k_params, g_inf = len(f), x.shape[1], len(informative)
+    factor = (g_inf / (g_inf - 1)) * ((n - 1) / (n - k_params))
+    se = float(np.sqrt((bread @ meat @ bread)[0, 0] * factor))
+    k = float(beta[0])
+    return {"k": k, "se": se, "p": float(stats.t.sf(k / se, g_inf - 1)), "groups_informative": g_inf,
+            "groups": f["group"].nunique()}
diff --git a/tests/test_informative_inference.py b/tests/test_informative_inference.py
new file mode 100644
index 0000000..3bd015d
--- /dev/null
+++ b/tests/test_informative_inference.py
@@ -0,0 +1,97 @@
+"""Step 7: the standard error's small-sample factor and the t distribution's degrees of freedom count
+informative papers only, the same count as validity check 2 (owner, 2026-10-06; register
+'informative_groups_in_inference'; CLAUDE.md rule 6). Applied in the real fits and every simulated fit.
+
+The design: four alloys; in each, one record at x = d^-1/2 = 0.2 and one at 0.8 from two of three
+informative papers, and two records at 0.5 (the alloy's average, exactly) from six uninformative
+papers. With all nine papers counted (statsmodels' definition) the factor is 9/8 and the test has 8
+degrees of freedom; with the three informative papers it is 3/2 and 2 degrees of freedom: a larger
+standard error (by exactly sqrt(4/3), since uninformative papers' scores are exactly zero) and a
+larger p-value, the cautious direction.
+"""
+from __future__ import annotations
+
+import math
+
+import numpy as np
+import pytest
+from scipy import stats
+
+import generator as g
+import reference_stats as rs
+from hypocurate.pipeline import analysis
+from hypocurate.pipeline import calibration as cal
+from hypocurate.pipeline import statistics as st
+from test_statistics_boundaries import frozen
+
+
+def design_rows(seed=11):
+    rng = np.random.default_rng(seed)
+    rows, u = [], 0
+    for a in range(4):
+        for d, paper in ((25.0, f"inf-{a % 3}"), (1.5625, f"inf-{(a + 1) % 3}"), (4.0, None), (4.0, None)):
+            if paper is None:
+                paper, u = f"uninf-{u % 6}", u + 1
+            rows.append((a, paper, d, 300.0 + 50 * a + 250.0 * d ** -0.5 + rng.normal(0, 20.0)))
+    return rows
+
+
+def reference_rows(rows):
+    data = frozen(rows, "inf")
+    return [(f"a{a}", f"paper:{p}", d, y) for (a, p, d, y) in rows], data
+
+
+def test_the_design_has_three_informative_and_six_uninformative_papers():
+    rows, data = reference_rows(design_rows())
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
+    assert (pooled["counts"]["n_groups"], pooled["counts"]["n_groups_informative"]) == (9, 3)
+    assert len(pooled["uninformative_groups"]) == 6
+    assert rs.informative_groups(rows) == {f"paper:inf-{i}" for i in range(3)}
+
+
+def test_the_factor_and_degrees_of_freedom_count_informative_papers_only():
+    rows, data = reference_rows(design_rows())
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
+    assert pooled["df"] == 2  # informative papers - 1, not 9 - 1
+    ref = rs.fit_informative(rows)  # independent: explicit sandwich over informative groups
+    assert math.isclose(pooled["estimate"], ref["k"], rel_tol=1e-9)
+    assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-9)
+    assert math.isclose(pooled["p_value"], ref["p"], rel_tol=1e-9)
+
+
+def test_the_result_is_more_cautious_than_counting_every_paper():
+    """Against statsmodels with all nine clusters (the earlier definition): same k, a standard error
+    larger by exactly sqrt(4/3), fewer degrees of freedom, a larger p-value."""
+    rows, data = reference_rows(design_rows())
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
+    every = rs.fit(rows)  # statsmodels, every cluster counted
+    all_p = float(stats.t.sf(every["k"] / every["se"], 9 - 1))
+    assert math.isclose(pooled["estimate"], every["k"], rel_tol=1e-9)
+    assert pooled["std_error"] > every["se"]
+    assert math.isclose(pooled["std_error"] / every["se"], math.sqrt((3 / 2) / (9 / 8)), rel_tol=1e-9)
+    assert pooled["p_value"] > all_p and pooled["df"] < 8
+
+
+@pytest.mark.parametrize("name", ["effect_many_papers", "large_paper_shifts", "single_size_alloys_added"])
+def test_where_every_paper_is_informative_nothing_changes(name):
+    """The statsmodels comparison still holds exactly (and the independent sandwich agrees with it)."""
+    data = g.frozen_data(g.SPECS[name])
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
+    assert pooled["counts"]["n_groups"] == pooled["counts"]["n_groups_informative"]
+    every, mine = rs.fit(g.rows(data)), rs.fit_informative(g.rows(data))
+    for got, a, b in ((pooled["std_error"], every["se"], mine["se"]), (pooled["p_value"], every["p"], mine["p"])):
+        assert math.isclose(got, a, rel_tol=1e-9) and math.isclose(got, b, rel_tol=1e-9)
+
+
+def test_every_simulated_fit_counts_informative_papers_only():
+    """The vectorized simulation decides each simulated fit exactly as the independent sandwich does."""
+    rows, data = reference_rows(design_rows())
+    d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
+    rng = np.random.default_rng(31)
+    outcomes = 120.0 * d.x[None, :] + rng.normal(0, 40, (200, d.n_groups))[:, d.group] + rng.normal(0, 60, (200, d.n))
+    expected = 0
+    for y in outcomes:  # the design's own records, in its order: alloy, group, grain size, outcome
+        sim_rows = [(f"a{d.alloy[i]}", f"g{d.group[i]}", float(d.x[i]) ** -2, float(y[i])) for i in range(d.n)]
+        expected += rs.fit_informative(sim_rows)["p"] < 0.05
+    assert 0 < expected < 200
+    assert cal.significant_count(d, outcomes, 0.05) == expected
```


## 3. Reference numbers recomputed after all the fixes (on `496644e`)

The reference run (MPEA and Texas A&M, reference plan, fixed minimums) through the freeze and `analysis.run_statistics`. Columns: analysis, records, alloys, groups, informative groups, residual df, uninformative groups, k, SE, p, label, label reason, inference reason, fixed calibration (no-effect, effect significant of 2,000), estimated calibration, fixed detection rate, estimated detection rate.

```
ROW pooled 97 22 20 20 74 [] 424.878909890441 64.38104348384877 1.2871510441941738e-06 None None None (157, 2000) (151, 1944) 1.0 0.972
ROW per_source:mpea 76 13 19 19 62 [] 424.0544230818879 62.21603775763125 1.1076022212936783e-06 agrees None None (166, 2000) (161, 1922) 1.0 0.961
ROW per_source:tamu_fcc 21 9 1 1 11 [] 1173.3418673474907 None None not_enough_data no_p_value insufficient_groups insufficient_groups insufficient_groups None None
ROW sensitivity:no_exclusions 97 22 20 20 74 [] 424.878909890441 64.38104348384877 1.2871510441941738e-06 None None None (157, 2000) (145, 1938) 1.0 0.969
ROW sensitivity:tension_and_compression 98 22 21 21 75 [] 428.02404949610104 63.5111223502356 7.398407506070913e-07 None None None (180, 2000) (156, 1960) 1.0 0.98
ROW sensitivity:six_batches_as_groups 97 22 22 22 74 [] 424.878909890441 64.22883580113373 7.511240461762346e-07 None None None (185, 2000) (163, 1952) 1.0 0.976
ROW sensitivity:same_alloy_1_at_pct 97 22 20 20 74 [] 424.878909890441 64.38104348384877 1.2871510441941738e-06 None None None (159, 2000) (171, 1954) 1.0 0.977
ROW sensitivity:source_only_assignments 76 13 19 19 62 [] 424.0544230818879 62.21603775763125 1.1076022212936783e-06 None None None (164, 2000) (193, 1915) 1.0 0.9575
ROW sensitivity:scope_not_confirmed_included 103 23 22 22 79 [] 432.35022685949707 64.86124831533817 6.723688937719326e-07 None None None (150, 2000) (166, 1958) 1.0 0.979
ROW sensitivity:possible_duplicates_separate 97 22 20 20 74 [] 424.878909890441 64.38104348384877 1.2871510441941738e-06 None None None (149, 2000) (148, 1947) 1.0 0.9735
ROW sensitivity:conflicts_survivor_value 97 22 20 20 74 [] 424.878909890441 64.38104348384877 1.2871510441941738e-06 None None None (174, 2000) (170, 1959) 1.0 0.9795
DECISION {"freeze_fingerprint": "3ec87f58975dc9fce3432e51e6a5ee4e4e56d83821e46db966f85fa4e027c907", "state": "sufficient", "outcome": "sufficient", "outcome_wording": "sufficient in the sources searched", "verdict": "supported", "verdict_wording": "supported under the stated model, in the sources searched", "exploratory": false, "evidence_level": 6, "evidence_level_wording": "sufficient with a verdict", "label": null}
```

Against the first build, and against the previous round (before informative papers entered the factor and the degrees of freedom): byte-identical. Every k, SE and p, every simulated count and the freeze fingerprint are unchanged, because every group of every reference set is informative.

## 4. Mutation checks

### Review fixes: `mutations_fix.sh`

```bash
#!/bin/bash
M=/tmp/claude-1000/-workspaces-hypocurate/d40b08e7-9c83-4b0a-8b2e-aa110db4b20f/scratchpad/mutate.sh
B=/workspaces/hypocurate/tests/test_statistics_boundaries.py
$M f01_all_groups_informative pipeline/statistics.py 'n_groups_informative=len(informative),' 'n_groups_informative=len(groups),' $B /workspaces/hypocurate/tests/test_analysis_stage.py
$M f02_no_se_zero_check pipeline/statistics.py 'if not (math.isfinite(se) and se > RELATIVE_ZERO * math.sqrt(float(yd @ yd) / sxx)):' 'if not math.isfinite(se):' $B
$M f03_sims_no_validity pipeline/calibration.py 'valid = np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)' 'valid = np.isfinite(k) | True' $B
$M f04_raw_distinct pipeline/statistics.py 'used_alloys = sorted(a for a, v in values.items() if distinct_values(v) >= MODEL_MIN_GRAIN_SIZES)' 'used_alloys = sorted(a for a, v in values.items() if len(set(v)) >= MODEL_MIN_GRAIN_SIZES)' $B
$M f05_scatter_any_positive pipeline/calibration.py 'rss_f > (RELATIVE_ZERO ** 2) * tss_within' 'rss_f > 0' $B
$M f06_narrow_except pipeline/analysis.py '        except Exception as error:  # review finding 3: nothing bypasses the stage' '        except st.StatisticsError as error:  # review finding 3: nothing bypasses the stage' /workspaces/hypocurate/tests/test_analysis_stage.py
$M f07_trigger_minimum_all_groups db/migrations/versions/0004_statistics_results.py 'AND NEW.n_groups_informative >= p.min_groups' 'AND NEW.n_groups >= p.min_groups' /workspaces/hypocurate/tests/test_analysis_stage.py /workspaces/hypocurate/tests/test_migrations_step7.py
$M f08_db_check2_all_groups db/migrations/versions/0004_statistics_results.py 'COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"' 'COUNTS_ALLOW = "(resid_df >= 1 AND n_groups >= 2)"' /workspaces/hypocurate/tests/test_analysis_stage.py
$M f09_trigger_label_bound_back db/migrations/versions/0004_statistics_results.py '        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        -- The paper minimum' '        IF NEW.n_alloys > (SELECT count(DISTINCT r.alloy) FROM analysis_set_record sr JOIN record r ON r.id = sr.record_id WHERE sr.analysis_set_id = NEW.analysis_set_id) THEN PERFORM hc_reject(''bound''); END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        -- The paper minimum' /workspaces/hypocurate/tests/test_analysis_stage.py /workspaces/hypocurate/tests/test_data_model.py
$M f10_zero_reason_lost pipeline/statistics.py '    if per_source["estimate"] == 0 or pooled["estimate"] == 0:
        return "zero_coefficient"' '' $B
$M f11_estimated_rate_not_withheld pipeline/analysis.py '"estimated": {"withheld": True}}' '"estimated": _rates(cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "estimated"))}' $B
$M f12_no_interval_note pipeline/calibration.py '"interval_note": INTERVAL_NOTE_FIXED if method == "fixed" else INTERVAL_NOTE_ESTIMATED' '"interval_note": INTERVAL_NOTE_FIXED' $B
$M f13_level_not_required db/migrations/versions/0004_statistics_results.py "EVIDENCE_LEVEL_REQUIRED = \"(evidence_level IS NOT NULL) = (status = 'completed')\"" "EVIDENCE_LEVEL_REQUIRED = \"true\"" /workspaces/hypocurate/tests/test_completion.py
```

### Output

```
[f01_all_groups_informative] >       assert (r.n_groups, r.n_groups_informative, r.check2_passed, r.inference_reason) == (11, 1, False,
[f01_all_groups_informative] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict[fixed_minimum]
[f01_all_groups_informative] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_the_reviewers_design_never_gives_a_verdict[use_available]
[f01_all_groups_informative] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_a_paper_is_informative_when_its_records_vary_after_removing_the_alloy_average
[f01_all_groups_informative] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_reviewers_design_through_the_database
[f01_all_groups_informative] 4 failed, 49 passed in 25.74s
[f02_no_se_zero_check]         """Two informative papers, residuals zero up to rounding: the standard error is below the
[f02_no_se_zero_check]         """The coefficient (check 1), and its standard error and one-sided p-value (check 2): only when
[f02_no_se_zero_check]         the counts allow it and the standard error is finite and above the numerical zero."""
[f02_no_se_zero_check] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only
[f02_no_se_zero_check] 1 failed, 18 passed in 1.33s
[f03_sims_no_validity] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit
[f03_sims_no_validity] 1 failed, 18 passed in 1.35s
[f04_raw_distinct] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_nearly_equal_transformed_grain_sizes_are_not_distinct
[f04_raw_distinct] 1 failed, 18 passed in 1.51s
[f05_scatter_any_positive] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_scatter
[f05_scatter_any_positive] 1 failed, 18 passed in 1.48s
[f06_narrow_except] ________ test_an_unexpected_error_in_the_statistics_is_a_logged_refusal ________
[f06_narrow_except]     def test_an_unexpected_error_in_the_statistics_is_a_logged_refusal(engine, monkeypatch):
[f06_narrow_except]         """Finding 3: no exception may bypass the stage's error handling."""
[f06_narrow_except] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_an_unexpected_error_in_the_statistics_is_a_logged_refusal
[f06_narrow_except] 1 failed, 33 passed in 25.38s
[f07_trigger_minimum_all_groups]         except IntegrityError as error:
[f07_trigger_minimum_all_groups]             message = database_message(error)
[f07_trigger_minimum_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_reviewers_design_through_the_database
[f07_trigger_minimum_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_migrations_step7.py::test_the_new_result_function_keeps_every_check_of_0001
[f07_trigger_minimum_all_groups] 2 failed, 40 passed in 26.85s
[f08_db_check2_all_groups]         except IntegrityError as error:
[f08_db_check2_all_groups]             message = database_message(error)
[f08_db_check2_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_reviewers_design_through_the_database
[f08_db_check2_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_counts_informative_groups_for_check_2_and_the_minimum
[f08_db_check2_all_groups] 2 failed, 32 passed in 25.49s
[f10_zero_reason_lost] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_a_zero_coefficient_has_its_own_reason[per_source0-pooled0-zero_coefficient]
[f10_zero_reason_lost] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_a_zero_coefficient_has_its_own_reason[per_source1-pooled1-zero_coefficient]
[f10_zero_reason_lost] 2 failed, 17 passed in 1.50s
[f11_estimated_rate_not_withheld] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld
[f11_estimated_rate_not_withheld] 1 failed, 18 passed in 1.66s
[f12_no_interval_note] FAILED ../../../../../workspaces/hypocurate/tests/test_statistics_boundaries.py::test_every_estimated_calibration_states_what_its_intervals_cover
[f12_no_interval_note] 1 failed, 18 passed in 1.50s
[f13_level_not_required] FAILED ../../../../../workspaces/hypocurate/tests/test_completion.py::test_a_completed_run_needs_its_evidence_level
[f13_level_not_required] 1 failed, 7 passed in 9.19s
# f09 re-run with correct quoting (the first attempt's shell quoting broke the SQL and tested nothing):
[f09_trigger_label_bound_back] E           [SQL: INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) VALUES (%(r)s, %(sc)s, %(s)s, %(src)s, %(n)s, %(a)s, %(g)s, %(gi)s, %(df)s, %(c1)s, %(c2)s, %(mm)s, %(est)s, %(se)s, %(p)s) RETURNING id]
[f09_trigger_label_bound_back] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_two_alloys_with_one_display_label_are_stored
[f09_trigger_label_bound_back] FAILED ../../../../../workspaces/hypocurate/tests/test_data_model.py::test_the_display_label_no_longer_bounds_the_alloy_count
[f09_trigger_label_bound_back] 2 failed, 185 passed in 62.92s (0:01:02)
```

### Informative papers in the factor and the degrees of freedom: `mutations_inf.sh`

```bash
#!/bin/bash
M=/tmp/claude-1000/-workspaces-hypocurate/d40b08e7-9c83-4b0a-8b2e-aa110db4b20f/scratchpad/mutate.sh
I=/workspaces/hypocurate/tests/test_informative_inference.py
$M i01_factor_all_groups pipeline/statistics.py 'small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)' 'small_sample_factor(d.n, d.n_alloys, d.n_groups)' $I
$M i02_df_all_groups pipeline/statistics.py '    df = d.n_groups_informative - 1' '    df = d.n_groups - 1' $I
$M i03_scores_all_groups pipeline/statistics.py 'scores = np.bincount(d.group, xd * e, d.n_groups)[d.group_informative]' 'scores = np.bincount(d.group, xd * e, d.n_groups)' $I
$M i04_sim_factor_all_groups pipeline/calibration.py 'small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)' 'small_sample_factor(d.n, d.n_alloys, d.n_groups)' $I
$M i05_sim_df_all_groups pipeline/calibration.py 'p = stats.t.sf(t, d.n_groups_informative - 1)' 'p = stats.t.sf(t, d.n_groups - 1)' $I
```

### Output

```
[i01_factor_all_groups] >       assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-9)
[i01_factor_all_groups]         """Against statsmodels with all nine clusters (the earlier definition): same k, a standard error
[i01_factor_all_groups] >       assert pooled["std_error"] > every["se"]
[i01_factor_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only
[i01_factor_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_the_result_is_more_cautious_than_counting_every_paper
[i01_factor_all_groups] 2 failed, 5 passed in 3.27s
[i02_df_all_groups]         """Against statsmodels with all nine clusters (the earlier definition): same k, a standard error
[i02_df_all_groups]         assert pooled["std_error"] > every["se"]
[i02_df_all_groups]         assert math.isclose(pooled["std_error"] / every["se"], math.sqrt((3 / 2) / (9 / 8)), rel_tol=1e-9)
[i02_df_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only
[i02_df_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_the_result_is_more_cautious_than_counting_every_paper
[i02_df_all_groups] 2 failed, 5 passed in 3.08s
[i03_scores_all_groups] 7 passed in 3.20s
[i04_sim_factor_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_every_simulated_fit_counts_informative_papers_only
[i04_sim_factor_all_groups] 1 failed, 6 passed in 3.20s
[i05_sim_df_all_groups] FAILED ../../../../../workspaces/hypocurate/tests/test_informative_inference.py::test_every_simulated_fit_counts_informative_papers_only
[i05_sim_df_all_groups] 1 failed, 6 passed in 3.25s
```

i03 survives: an equivalent mutation (an uninformative group's score is zero up to rounding; see the summary).

## 5. Suite output

```
Local (Codespace), on 496644e:
1138 passed in 328.77s (0:05:28)
```

## 6. Questions for the re-check

0. Is counting informative papers in the small-sample factor and the degrees of freedom (the owner's second decision) implemented consistently in the real fits and every simulated fit, and is the independent sandwich a fair check of it?
1. Are the four findings closed: can any design still give a verdict, a p-value or a standard error without at least two informative papers and an estimable uncertainty, in a real fit or a simulated one?
2. Is "informative paper" implemented as the owner defined it, and is the numerical zero (1e-10 of the natural scale) applied consistently and never acting as a scientific threshold?
3. Does migration 0004, as changed, enforce check 2, the reasons and the evidence level completely, and is the downgrade still exact?
4. Is anything new computed from outcome values below the minimums (detection rates, reasons, notes)?
5. Is any claim stronger than the code supports?
