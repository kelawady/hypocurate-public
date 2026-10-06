# Build step 7 — second fix packet (after the re-check)

Date: 2026-10-06. Branch: `step-07-statistics`. Code reviewed: commit `1320840` (this packet and the summary update are added in the next commit and change no code). GitHub Actions on that commit: success (1,155 passed, runtime image OK), https://github.com/kelawady/hypocurate/actions/runs/37419050238.

Generated from the files on disk by a script, so every diff and output below is quoted exactly.

## How to use this packet

Your re-check of 2026-10-06 (`docs/reviews/step07_recheck_chatgpt.md`) closed the original cases and the display-label trigger, and found five open items. The owner accepted all of them and decided how to treat concentrated evidence (the effective number of papers). This packet holds only what changed since the re-check: the fix table, the per-commit diffs, the recomputed reference numbers with the effective number of papers, the mutation checks and the suite output. The summary (`docs/reviews/step07_summary.md`) describes the whole state; the first fix packet (`docs/reviews/step07_fix_packet.md`) now carries a correction notice for its false "equivalent mutation" claim. Your review is advice; the test suite is the gate.

## 1. The fixes (from the summary)

## Re-check and fixes (ChatGPT, 2026-10-06)

The re-check (`docs/reviews/step07_recheck_chatgpt.md`, verbatim): the original cases are closed, the display-label trigger is fixed, but not safe to merge. The owner accepted every item and decided how to treat concentrated evidence. Fix packet: `docs/reviews/step07_fix2_packet.md`.

**Owner's decision (2026-10-06):** for every analysis, the effective number of papers (Σ I_g)² / Σ I_g², I_g a paper's sum of squared within-alloy deviations of the transformed grain size, and the largest single paper's share are computed and stored with every result. Validity check 2 requires an effective number of at least 2; below that, the coefficient only, reason `evidence_concentrated`. The paper minimum (10) remains the count of informative papers. The same check applies in every simulated fit. Register entry `effective_papers`.

| Item | Fix | Tests (failed on the code before the fix unless marked) |
|---|---|---|
| **1. Concentrated evidence.** The reviewer's nudged design (the four mean-valued predictors at 0.5 ± 0.000001) made all 11 papers informative though one carries almost all the information: SE ≈ 0.0003, p ≈ 5e-58, null rejection 51% | The owner's effective-papers rule, in `design` (structure only, so also for withheld results), check 2, every simulated fit and the database (`effective_papers`, `largest_paper_share`; check 2's constraint requires ≥ 2; reason `evidence_concentrated`, derived by the trigger) | `test_the_nudged_design_gives_no_verdict` (both options: effective number 1.00000000006, share > 0.999, coefficient only); `test_the_effective_number_of_papers_is_the_owners_formula` (against a test-side pandas computation on the fixed set); `test_every_simulated_fit_requires_two_effective_papers`; `test_the_effective_number_and_share_are_reported_with_every_result`; database: `test_the_database_requires_two_effective_papers_for_check_2`, `test_the_effective_number_and_share_are_stored_with_every_result` |
| **2. Scores dropped from the covariance.** Not always cautious: the reviewer's five-paper counterexample gave p = 0.0366 (filtered) against 0.1685 (every paper counted); the packet's "equivalent mutation" claim was false | Every group's score is summed; the informative count applies to the factor and the degrees of freedom only, in `fit` and `significant_count`. The independent check is replaced: `reference_stats.fit_informative` is an explicit sandwich in **60-digit decimal arithmetic** that keeps every score and shares no code with the package. statsmodels' own clustered covariance comes out negative (NaN SE) on this ill-conditioned single-alloy design, so it cannot serve here; it is kept for the well-conditioned designs where every paper is informative | `test_the_counterexample_keeps_every_papers_score` (two informative papers of five, effective number 2.00000000000004; p equals the decimal check, ≥ the all-paper 0.1685, which the decimal check reproduces); `test_simulated_fits_keep_every_papers_score` (300 simulated fits with the counterexample's structure: the old code found 32 significant, the decimal check 2) |
| **4. Distinctness by adjacent gaps.** [1, 1+1.5e-10] kept the alloy; adding 1+0.75e-10 removed it | `has_contrast`: the full range against the tolerance | `test_adding_a_record_never_removes_an_alloys_contrast` (the chain, and 2,000 random insertions); `test_an_alloy_keeps_its_contrast_in_a_design_when_a_middle_record_is_added` |
| **5. Numerical zero at the data's scale.** Baselines of 200 to 900 MPa and k = 1e-5, exact: SE ≈ 7e-14, p ≈ 4e-25, scatter 3e-13 MPa "estimable" | Residuals are rounding when their root mean square is at most the larger of 1e-10 × the outcome's within-alloy root mean square and `ARITHMETIC_ZERO` = 1e-12 × the largest outcome magnitude: no uncertainty and no scatter then. Stable centring (each alloy's first value subtracted first) in the fit, the simulations and method III's least squares. Applied in every simulated fit | `test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference` (fit and scatter); `test_simulated_perfect_fits_on_large_baselines_are_never_significant` (added after mutation r10 survived). Guards (passed before): `test_a_perfect_fit_is_judged_the_same_whatever_the_baselines` (shifts 0, 1e3, 1e6 MPa); `test_small_real_noise_with_large_baselines_stays_estimable` (0.01 MPa on 200 to 900 MPa is estimated: an arithmetic safeguard, not a scientific minimum) |
| **6. The detection note hardcoded 5%** | `detection_note(alpha)` states the plan's locked threshold | `test_the_detection_note_states_the_plans_threshold` (α = 0.01) |

**Changed tests, none removed:** `test_statistics.py`: `test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes` now expects check 2 to fail with `evidence_concentrated` (its two papers carry unequal information, effective number 1.8); `test_the_two_validity_checks`: the case that passed check 2 has an effective number of about 1.1, so it now fails, and a balanced two-paper case (outcomes chosen so the scores are not both zero) is added as the passing case. Helpers: `model_builder.result()` and `_insert_result` give an effective number equal to the informative count. `reference_stats.fit_informative` is rewritten (above).

**Reference numbers after the re-check fixes: no approved number changed.** Recomputed on the reference run: counts, labels, reasons, every simulated count under both calibrations, detection rates and the decision are identical. k, SE and p differ from the previous round only in the last one or two digits (about 1e-16 relative; for example pooled k 424.878909890441 → 424.87890989044104, SE 64.38104348384877 → 64.3810434838488), because the stable centring adds the same numbers in a different order. Every result still rounds to its approved figure, and every tolerance test passes unchanged. The effective number of papers (check 2 needs at least 2; every set passes, except Texas A&M alone, which already fails on its single group):

| Set | Effective number of papers | Largest single paper's share |
|---|---|---|
| pooled | 3.9359 | 38.7% |
| per_source:mpea | 3.9272 | 38.7% |
| per_source:tamu_fcc | 1.0 | 100.0% |
| sensitivity:no_exclusions | 3.9359 | 38.7% |
| sensitivity:tension_and_compression | 3.9976 | 38.7% |
| sensitivity:six_batches_as_groups | 3.9359 | 38.7% |
| sensitivity:same_alloy_1_at_pct | 3.9359 | 38.7% |
| sensitivity:source_only_assignments | 3.9272 | 38.7% |
| sensitivity:scope_not_confirmed_included | 4.0666 | 38.0% |
| sensitivity:possible_duplicates_separate | 3.9359 | 38.7% |
| sensitivity:conflicts_survivor_value | 3.9359 | 38.7% |

The pooled set's 20 informative papers carry the information of about 3.9 equally informative papers, and the largest single paper holds about 39% of it.

**Mutations of the re-check fixes:** 10, all caught (r10, the residual floor in the simulations, survived at first and is caught after a new test). Restoring the old score filter (r02) is caught by the counterexample.


## 2. Commits

```
1320840 Step 7 re-check fixes: register (effective_papers; informative_groups_in_inference, numerical_zero, validity_checks, smallest_effect reworded)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

f0ad7c2 Step 7 re-check fixes: migration 0004 stores the effective number of papers and the largest share; check 2 needs two effective papers

0004 has not run on the live database (still at 0003), so it is changed in place. The two new
database tests fail before the fix (no such columns).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

66bd3da Step 7 re-check fixes: effective papers, every score kept, range-based distinctness, arithmetic zero, locked threshold in the note

Owner's decision on concentrated evidence (effective number of papers >= 2 for check 2); re-check
findings 1, 2, 4, 5 and the smaller point. The independent check is now an explicit sandwich in
60-digit decimal arithmetic that keeps every score (statsmodels' own covariance goes negative on the
reviewer's ill-conditioned counterexample). tests/test_recheck_fixes.py: 11 tests failed before the fix
(14 tests in all; the guards passed). Two old expectations in test_statistics.py follow the decision
(effective number 1.8 and 1.1 < 2), with a balanced case added.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

### Commit `66bd3da`

```
66bd3da Step 7 re-check fixes: effective papers, every score kept, range-based distinctness, arithmetic zero, locked threshold in the note

 hypocurate/pipeline/analysis.py    |   9 +-
 hypocurate/pipeline/calibration.py |  27 +++--
 hypocurate/pipeline/statistics.py  | 118 +++++++++++++++------
 tests/reference_stats.py           |  66 +++++++-----
 tests/test_recheck_fixes.py        | 206 +++++++++++++++++++++++++++++++++++++
 tests/test_statistics.py           |  11 +-
 6 files changed, 365 insertions(+), 72 deletions(-)
```

```diff
diff --git a/hypocurate/pipeline/analysis.py b/hypocurate/pipeline/analysis.py
index f763384..4d9cf63 100644
--- a/hypocurate/pipeline/analysis.py
+++ b/hypocurate/pipeline/analysis.py
@@ -132,7 +132,7 @@ def analyse(plan: Mapping, data: Mapping) -> dict:
         # even below the minimums (owner, decision 5).
         fixed = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "fixed")
         entry["estimated_power"], entry["power_label"] = fixed["effect"]["share"], st.POWER_LABEL
-        entry["detection_note"] = st.DETECTION_NOTE
+        entry["detection_note"] = st.detection_note(alpha)
         if withheld:
             entry["calibration"] = {"fixed": _unavailable("below_minimums"),
                                     "estimated": _unavailable("below_minimums")}
@@ -190,8 +190,8 @@ _RESULT = text(
     "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, resid_df, "
     "check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, estimated_power, label, withheld, "
     "n_records_not_used, test_run_label, n_groups_informative, inference_reason, label_reason, "
-    "estimated_power_estimated_noise) VALUES (:r, :scope, :set, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, "
-    ":p, :pw, :lab, :wh, :nu, :tl, :gi, :ir, :lr, :pe) RETURNING id")
+    "estimated_power_estimated_noise, effective_papers, largest_paper_share) VALUES (:r, :scope, :set, :src, :n, :a, "
+    ":g, :df, :c1, :c2, :mm, :est, :se, :p, :pw, :lab, :wh, :nu, :tl, :gi, :ir, :lr, :pe, :ep, :ls) RETURNING id")
 _CALIBRATION = text(
     "INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, n_simulations, "
     "seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, confidence_flag, "
@@ -255,7 +255,8 @@ def run_statistics(engine: Engine, run_id: int) -> dict:
                 c1=e["checks"]["coefficient_fitted"], c2=e["checks"]["inference_valid"], mm=e["minimums_met"],
                 est=e["estimate"], se=e["std_error"], p=e["p_value"], pw=e["estimated_power"], lab=e["label"],
                 wh=e["withheld"], nu=c["n_records_not_used"], tl=label, gi=c["n_groups_informative"],
-                ir=e["inference_reason"], lr=e["label_reason"], pe=e["estimated_power_estimated_noise"])).scalar_one()
+                ir=e["inference_reason"], lr=e["label_reason"], pe=e["estimated_power_estimated_noise"],
+                ep=c["effective_papers"] if c["n_alloys"] else None, ls=c["largest_paper_share"])).scalar_one()
             for method in ("fixed", "estimated"):
                 conn.execute(_CALIBRATION, _calibration_row(run_id, rid, method, e["calibration"][method], label))
         output = {**record, "test_run_label": label}
diff --git a/hypocurate/pipeline/calibration.py b/hypocurate/pipeline/calibration.py
index 75924ef..fd73e54 100644
--- a/hypocurate/pipeline/calibration.py
+++ b/hypocurate/pipeline/calibration.py
@@ -62,7 +62,8 @@ from typing import Mapping
 import numpy as np
 from scipy import stats
 
-from hypocurate.pipeline.statistics import RELATIVE_ZERO, Design, demeaned, small_sample_factor
+from hypocurate.pipeline.statistics import (ARITHMETIC_ZERO, RELATIVE_ZERO, Design, demeaned,
+                                            residuals_numerically_zero, small_sample_factor)
 
 CONFIDENCE = 0.95
 FLAG_WORDING = {
@@ -114,13 +115,14 @@ def significant_count(d: Design, outcomes: np.ndarray, alpha: float) -> int:
     e = yd - k[:, None] * xd[None, :]
     groups = np.zeros((d.n, d.n_groups))
     groups[np.arange(d.n), d.group] = 1.0
-    # Informative groups only, as in the real fit (owner, 2026-10-06).
-    scores = ((e * xd[None, :]) @ groups)[:, d.group_informative]
+    # Every group's score, informative groups in the factor and the df, as in the real fit.
+    scores = (e * xd[None, :]) @ groups
     variance = (scores ** 2).sum(axis=1) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)
     with np.errstate(divide="ignore", invalid="ignore"):
         se = np.sqrt(variance)
         scale = np.sqrt((yd ** 2).sum(axis=1) / sxx)
-        valid = np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)
+        valid = (np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)
+                 & ~residuals_numerically_zero(e, yd, outcomes))
         t = np.where(valid, k / np.where(valid, se, 1.0), 0.0)
     p = stats.t.sf(t, d.n_groups_informative - 1)
     return int(np.count_nonzero(valid & (p < alpha)))
@@ -158,8 +160,14 @@ def henderson_iii(d: Design) -> dict:
     groups[np.arange(n), d.group] = 1.0
     reduced = np.column_stack([alloys, d.x])
     full = np.column_stack([alloys, groups, d.x])
-    rss_r, rank_r = _rss_and_rank(reduced, d.y)
-    rss_f, rank_f = _rss_and_rank(full, d.y)
+    # Stable centring: both models have alloy intercepts, so subtracting each alloy's first value
+    # changes no residual and keeps large baselines out of the least squares.
+    first = {}
+    for i, a in enumerate(d.alloy):
+        first.setdefault(int(a), d.y[i])
+    y = d.y - np.array([first[int(a)] for a in d.alloy])
+    rss_r, rank_r = _rss_and_rank(reduced, y)
+    rss_f, rank_f = _rss_and_rank(full, y)
     q, _ = np.linalg.qr(reduced)
     residual_groups = groups - q @ (q.T @ groups)
     trace = float((residual_groups ** 2).sum())
@@ -167,9 +175,10 @@ def henderson_iii(d: Design) -> dict:
     tss_within = float(within @ within)
     out = {"estimation": "henderson_iii", "rss_reduced": rss_r, "rank_reduced": rank_r, "rss_full": rss_f,
            "rank_full": rank_f, "trace": trace, "n_records": n, "tss_within_alloys": tss_within}
-    # Review finding 4: a residual at most the numerical zero of the outcome's within-alloy spread is
-    # rounding residue (a perfect fit), not scatter.
-    if n <= rank_f or not (math.isfinite(rss_f) and rss_f > (RELATIVE_ZERO ** 2) * tss_within):
+    # Review finding 4 and re-check finding 5: residuals at most the numerical zero (of the outcome's
+    # within-alloy spread, or of the largest outcome magnitude) are rounding residue, not scatter.
+    floor = max((RELATIVE_ZERO ** 2) * tss_within, n * (ARITHMETIC_ZERO * float(np.abs(d.y).max())) ** 2)
+    if n <= rank_f or not (math.isfinite(rss_f) and rss_f > floor):
         return {**out, "reason": "scatter_not_estimable"}
     scatter_sq = rss_f / (n - rank_f)
     out["scatter_squared"] = scatter_sq
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index 014e65e..f62c99b 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -21,10 +21,15 @@ the records the fit uses** (owner, 2026-10-05).
 **Informative papers** (owner, 2026-10-06; register 'informative_groups'): a group is informative
 when at least one of its records differs from its alloy's average transformed grain size by more
 than the numerical zero, so that the group helps estimate the slope. Uninformative groups stay in
-the fit and are listed, but are not counted for the paper minimum, for validity check 2, for the standard error's
-small-sample factor or for the t distribution's degrees of freedom (owner, 2026-10-06; register
-'informative_groups_in_inference'; CLAUDE.md rule 6). The clustered covariance sums the scores of
-informative groups only (an uninformative group's score is zero up to rounding).
+the fit and are listed, but are not counted for the paper minimum, for validity check 2's group count, for the standard
+error's small-sample factor or for the t distribution's degrees of freedom (owner, 2026-10-06;
+register 'informative_groups_in_inference'; CLAUDE.md rule 6). The clustered covariance sums
+**every** group's score (re-check finding 2: a small contrast times a large residual can matter).
+
+**Effective number of papers** (owner, 2026-10-06; register 'effective_papers'): with I_g a group's
+sum of squared within-alloy deviations of the transformed grain size, (Σ I_g)² / Σ I_g², and the
+largest single group's share max I_g / Σ I_g, stored with every result. Validity check 2 needs at
+least `MIN_EFFECTIVE_PAPERS` (2); below it the coefficient alone, reason 'evidence_concentrated'.
 
 **The two validity checks** can never be waived (CLAUDE.md rule 5): (1) a coefficient can be fitted
 when at least one alloy has two distinct grain sizes; (2) inference is valid with at least 1
@@ -32,11 +37,15 @@ residual degree of freedom (records - alloys - 1), at least 2 informative groups
 standard error that is finite and above the scale-aware numerical zero (review finding 1). Check 1
 only: the coefficient alone, no uncertainty, no p-value, no verdict, with the reason.
 
-**Numerical zero** (`RELATIVE_ZERO`, register 'numerical_zero'): a quantity counts as zero when it is
-at most `RELATIVE_ZERO` times its natural scale in the same units: a predictor contrast against the
-largest transformed grain size; a standard error against sqrt(Σ ỹ² / Σ x̃²), the slope scale of the
-data. Rounding residue is about 1e-16 of the scale; any real measurement scatter is many orders above
-1e-10.
+**Numerical zero** (`RELATIVE_ZERO`, `ARITHMETIC_ZERO`, register 'numerical_zero'): an arithmetic
+safeguard, not a scientific minimum. A predictor range counts as zero when it is at most
+`RELATIVE_ZERO` (1e-10) times the largest transformed grain size. Residuals count as zero (a perfect
+fit, so no uncertainty and no scatter can be estimated) when their root mean square is at most the
+larger of `RELATIVE_ZERO` times the outcome's spread within alloys and `ARITHMETIC_ZERO` (1e-12) times
+the largest outcome magnitude (re-check finding 5: rounding comes from the baselines too). A standard
+error must also exceed `RELATIVE_ZERO` × sqrt(Σ ỹ² / Σ x̃²). Within-alloy centring subtracts each
+alloy's first value before taking the mean (stable centring). Rounding residue is about 1e-16 of these
+scales; real measurement scatter is many orders above them.
 
 **Below the minimums under the fixed option** (owner, 2026-10-05, decision 1): when the pooled fit
 misses any minimum, every analysis of the run is withheld: counts against each minimum, which were
@@ -62,6 +71,10 @@ from scipy import stats
 MODEL_MIN_GRAIN_SIZES = 2
 # A quantity at most this fraction of its natural scale is numerically zero (register 'numerical_zero').
 RELATIVE_ZERO = 1e-10
+# Residuals at most this fraction of the largest outcome magnitude are rounding (register 'numerical_zero').
+ARITHMETIC_ZERO = 1e-12
+# Validity check 2: the effective number of papers at least this (owner, 2026-10-06; register 'effective_papers').
+MIN_EFFECTIVE_PAPERS = 2.0
 # The predictor's transformation, by the locked plan's code (register
 # 'grain_size_transformation_at_analysis').
 TRANSFORMATIONS = MappingProxyType({"inverse_square_root": lambda d: d ** -0.5})
@@ -78,12 +91,14 @@ OUTCOME_WORDING = MappingProxyType({
 BELOW_MINIMUMS_LABEL = "data found; not enough to test"
 EXPLORATORY_LABEL = "exploratory"
 POWER_LABEL = "estimated power under the stated assumptions"
-DETECTION_NOTE = ("detection rates of the nominal 5% test under the stated assumptions (fixed and estimated noise), "
-                  "with its false-positive shares under the same assumptions; not power for a test shown to keep "
-                  "false positives at 5%")
+def detection_note(alpha: float) -> str:
+    """The detection note with the plan's locked threshold (re-check, smaller point)."""
+    return (f"detection rates of the nominal α = {alpha:g} test (the plan's locked threshold) under the stated "
+            f"assumptions (fixed and estimated noise), with its false-positive shares under the same assumptions; "
+            f"not power for a test shown to keep false positives at α = {alpha:g}")
 
 # Why validity check 2 failed (stored with the result; migration 0004).
-INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "uncertainty_not_estimable")
+INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "evidence_concentrated", "uncertainty_not_estimable")
 
 # The evidence level (owner, 2026-10-05; register 'evidence_level_scale'): descriptive only, derived
 # by `evidence_level` from the result state, never by an agent; it never affects the outcome or the
@@ -132,6 +147,8 @@ class Design:
     n_groups_informative: int = 0
     uninformative_groups: tuple = ()
     group_informative: np.ndarray = None  # per group index: does the group count (informative)?
+    effective_papers: float = 0.0  # (Σ I_g)² / Σ I_g²; 0 without a coefficient
+    largest_paper_share: float | None = None  # max I_g / Σ I_g
 
     @property
     def n(self) -> int:
@@ -147,9 +164,19 @@ class Design:
 
     @property
     def counts_allow_inference(self) -> bool:
-        """Validity check 2's counts: a residual degree of freedom and two informative groups. The
-        standard error must also be estimable (`fit`)."""
-        return self.coefficient_fitted and self.resid_df >= 1 and self.n_groups_informative >= 2
+        """Validity check 2's structure: a residual degree of freedom, two informative groups and an
+        effective number of papers of at least two. The standard error must also be estimable (`fit`)."""
+        return self.counts_reason is None
+
+    @property
+    def counts_reason(self) -> str | None:
+        if not self.coefficient_fitted:
+            return "coefficient_not_fitted"
+        if not (self.resid_df >= 1 and self.n_groups_informative >= 2):
+            return "insufficient_groups"
+        if not self.effective_papers >= MIN_EFFECTIVE_PAPERS:
+            return "evidence_concentrated"
+        return None
 
 
 def design(observations: Iterable[Observation], transformation: str) -> Design:
@@ -163,7 +190,7 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
         if not (math.isfinite(o.grain_size) and o.grain_size > 0 and math.isfinite(o.outcome)):
             raise StatisticsError("a record in a frozen set has no finite positive grain size or finite outcome")
         values.setdefault(o.alloy, []).append(transform(o.grain_size))
-    used_alloys = sorted(a for a, v in values.items() if distinct_values(v) >= MODEL_MIN_GRAIN_SIZES)
+    used_alloys = sorted(a for a, v in values.items() if has_contrast(v))  # MODEL_MIN_GRAIN_SIZES = 2
     keep = set(used_alloys)
     used = [o for o in obs if o.alloy in keep]
     groups = sorted({o.group for o in used})
@@ -172,34 +199,55 @@ def design(observations: Iterable[Observation], transformation: str) -> Design:
     x = np.array([transform(o.grain_size) for o in used], dtype=float)
     alloy = np.array([alloy_index[o.alloy] for o in used], dtype=int)
     informative: set = set()
+    effective, largest = 0.0, None
     if used:
-        contrast = np.abs(demeaned(x, alloy, len(used_alloys)))
+        deviation = demeaned(x, alloy, len(used_alloys))
+        contrast = np.abs(deviation)
         informative = {o.group for o, c in zip(used, contrast) if c > RELATIVE_ZERO * float(np.abs(x).max())}
+        info = np.bincount(np.array([group_index[o.group] for o in used]), deviation ** 2, len(groups))
+        total = float(info.sum())
+        if total > 0:
+            effective, largest = total ** 2 / float(info @ info), float(info.max()) / total
     return Design(
         x=x, y=np.array([o.outcome for o in used], dtype=float), alloy=alloy,
         group=np.array([group_index[o.group] for o in used], dtype=int),
         n_alloys=len(used_alloys), n_groups=len(groups), n_records_in_set=len(obs),
         n_alloys_not_used=len(values) - len(used_alloys), n_groups_informative=len(informative),
         uninformative_groups=tuple(g for g in groups if g not in informative),
-        group_informative=np.array([g in informative for g in groups], dtype=bool))
+        group_informative=np.array([g in informative for g in groups], dtype=bool),
+        effective_papers=effective, largest_paper_share=largest)
 
 
-def distinct_values(values: list) -> int:
-    """How many values differ from each other by more than the numerical zero (relative to the
-    largest): numerical distinctness of transformed grain sizes (review finding 3)."""
-    ordered = sorted(values)
-    tolerance = RELATIVE_ZERO * max(abs(v) for v in ordered)
-    return 1 + sum(1 for a, b in zip(ordered, ordered[1:]) if b - a > tolerance)
+def has_contrast(values: list) -> bool:
+    """At least two distinct transformed grain sizes: the full range exceeds the numerical zero
+    (relative to the largest value). Adding a value can never remove a contrast (re-check finding 4)."""
+    return max(values) - min(values) > RELATIVE_ZERO * max(abs(v) for v in values)
 
 
 def demeaned(values: np.ndarray, alloy: np.ndarray, n_alloys: int) -> np.ndarray:
-    """Each value minus its alloy's mean (works on the last axis, for one or many outcome rows)."""
+    """Each value minus its alloy's mean (works on the last axis, for one or many outcome rows).
+    Stable centring (re-check finding 5): each alloy's first value is subtracted before the mean is
+    taken, so large baselines do not swamp the within-alloy differences."""
     counts = np.bincount(alloy, minlength=n_alloys).astype(float)
+    first = np.full(n_alloys, -1)
+    for i in range(alloy.size - 1, -1, -1):
+        first[alloy[i]] = i
     if values.ndim == 1:
-        return values - (np.bincount(alloy, values, n_alloys) / counts)[alloy]
+        shifted = values - values[first][alloy]
+        return shifted - (np.bincount(alloy, shifted, n_alloys) / counts)[alloy]
+    shifted = values - values[:, first][:, alloy]
     indicator = np.zeros((alloy.size, n_alloys))
     indicator[np.arange(alloy.size), alloy] = 1.0
-    return values - ((values @ indicator) / counts)[:, alloy]
+    return shifted - ((shifted @ indicator) / counts)[:, alloy]
+
+
+def residuals_numerically_zero(residuals: np.ndarray, centred: np.ndarray, raw: np.ndarray) -> np.ndarray:
+    """Per row (last axis): are the residuals rounding residue? Their root mean square at most the
+    larger of RELATIVE_ZERO × the centred outcome's root mean square and ARITHMETIC_ZERO × the largest
+    raw outcome magnitude (register 'numerical_zero')."""
+    rms = lambda v: np.sqrt(np.mean(v ** 2, axis=-1))  # noqa: E731
+    floor = np.maximum(RELATIVE_ZERO * rms(centred), ARITHMETIC_ZERO * np.max(np.abs(raw), axis=-1))
+    return rms(residuals) <= floor
 
 
 def small_sample_factor(n: int, n_alloys: int, n_groups: int) -> float:
@@ -238,10 +286,12 @@ def fit(d: Design) -> Fit | None:
     if not math.isfinite(k):
         raise StatisticsError("the coefficient is not finite")
     if not d.counts_allow_inference:
-        return Fit(k, None, None, None, None, "insufficient_groups")
+        return Fit(k, None, None, None, None, d.counts_reason)
     e = yd - k * xd
-    # Informative groups only (owner, 2026-10-06): their scores, their count in the factor and the df.
-    scores = np.bincount(d.group, xd * e, d.n_groups)[d.group_informative]
+    if bool(residuals_numerically_zero(e, yd, d.y)):
+        return Fit(k, None, None, None, None, "uncertainty_not_estimable")
+    # Every group's score in the sum (re-check finding 2); informative groups in the factor and the df.
+    scores = np.bincount(d.group, xd * e, d.n_groups)
     variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)
     se = math.sqrt(variance) if math.isfinite(variance) and variance >= 0 else math.nan
     if not (math.isfinite(se) and se > RELATIVE_ZERO * math.sqrt(float(yd @ yd) / sxx)):
@@ -329,13 +379,13 @@ def decision(pooled: Mapping | None, plan: Mapping, freeze_fingerprint: str | No
 def analysis_entry(d: Design, plan: Mapping, withheld: bool) -> dict:
     """One analysis: counts, checks, minimums, and (unless withheld) the numbers from outcomes."""
     m = minimums(d, plan["sufficiency"])
-    counts_reason = None if d.counts_allow_inference else \
-        "coefficient_not_fitted" if not d.coefficient_fitted else "insufficient_groups"
+    counts_reason = d.counts_reason
     entry = {
         "counts": {"n_records_in_set": d.n_records_in_set, "n_records": d.n,
                    "n_records_not_used": d.n_records_in_set - d.n, "n_alloys": d.n_alloys,
                    "n_alloys_not_used": d.n_alloys_not_used, "n_groups": d.n_groups,
-                   "n_groups_informative": d.n_groups_informative, "resid_df": d.resid_df},
+                   "n_groups_informative": d.n_groups_informative, "resid_df": d.resid_df,
+                   "effective_papers": d.effective_papers, "largest_paper_share": d.largest_paper_share},
         "uninformative_groups": list(d.uninformative_groups),
         # Withheld: judged on the counts only (no outcome is used, so no standard error is computed).
         "checks": {"coefficient_fitted": d.coefficient_fitted, "inference_valid": d.counts_allow_inference},
diff --git a/tests/reference_stats.py b/tests/reference_stats.py
index 17e94db..c8a4bd7 100644
--- a/tests/reference_stats.py
+++ b/tests/reference_stats.py
@@ -84,27 +84,47 @@ def informative_groups(rows, relative_zero=1e-10) -> set:
     return set(f.loc[contrast > relative_zero * f["x"].abs().max(), "group"])
 
 
-def fit_informative(rows) -> dict:
-    """The owner's rule of 2026-10-06 computed independently with an explicit sandwich (numpy, dummy
-    variables, no statsmodels): the clustered covariance sums the scores of informative groups only, the
-    small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative groups, and the one-sided p-value
-    uses t with G - 1 degrees of freedom."""
+def fit_informative(rows, count: str = "informative") -> dict:
+    """The owner's rule (2026-10-06, as corrected after the re-check), computed independently in
+    60-digit decimal arithmetic (Python's `decimal`), so floating-point conditioning cannot affect it:
+    within-alloy centring, k = Σ x̃ỹ / Σ x̃², residuals e = ỹ - k x̃, the clustered variance summing
+    **every** paper's score (no filtering), the factor G/(G-1) × (N-1)/(N-K) and a one-sided t test
+    with G - 1 degrees of freedom, where G is the informative papers (`count="informative"`) or every
+    paper (`count="all"`, the earlier definition). It shares no code with the package."""
+    from decimal import Decimal, localcontext
     f = frame(rows)
-    informative = informative_groups(rows)
-    alloys = sorted(f["alloy"].unique())
-    x = np.column_stack([f["x"].to_numpy()] + [(f["alloy"] == a).to_numpy(dtype=float) for a in alloys])
-    y = f["y"].to_numpy()
-    bread = np.linalg.inv(x.T @ x)
-    beta = bread @ x.T @ y
-    e = y - x @ beta
-    meat = np.zeros((x.shape[1], x.shape[1]))
-    for g in informative:
-        rows_g = (f["group"] == g).to_numpy()
-        s = x[rows_g].T @ e[rows_g]
-        meat += np.outer(s, s)
-    n, k_params, g_inf = len(f), x.shape[1], len(informative)
-    factor = (g_inf / (g_inf - 1)) * ((n - 1) / (n - k_params))
-    se = float(np.sqrt((bread @ meat @ bread)[0, 0] * factor))
-    k = float(beta[0])
-    return {"k": k, "se": se, "p": float(stats.t.sf(k / se, g_inf - 1)), "groups_informative": g_inf,
-            "groups": f["group"].nunique()}
+    groups_inf = informative_groups(rows)
+    with localcontext() as ctx:
+        ctx.prec = 60
+        x = [Decimal(v) for v in f["x"]]
+        y = [Decimal(v) for v in f["y"]]
+        alloys, groups = list(f["alloy"]), list(f["group"])
+        mean_x, mean_y = {}, {}
+        for a in set(alloys):
+            idx = [i for i, b in enumerate(alloys) if b == a]
+            mean_x[a] = sum(x[i] for i in idx) / len(idx)
+            mean_y[a] = sum(y[i] for i in idx) / len(idx)
+        xt = [x[i] - mean_x[alloys[i]] for i in range(len(x))]
+        yt = [y[i] - mean_y[alloys[i]] for i in range(len(y))]
+        sxx = sum(v * v for v in xt)
+        k = sum(a * b for a, b in zip(xt, yt)) / sxx
+        e = [yt[i] - k * xt[i] for i in range(len(x))]
+        scores = {}
+        for i, g in enumerate(groups):
+            scores[g] = scores.get(g, Decimal(0)) + xt[i] * e[i]
+        n, k_params = len(x), len(set(alloys)) + 1
+        g_count = len(groups_inf) if count == "informative" else len(set(groups))
+        factor = (Decimal(g_count) / (g_count - 1)) * (Decimal(n - 1) / (n - k_params))
+        variance = sum(s * s for s in scores.values()) / (sxx * sxx) * factor
+        se = float(variance.sqrt())
+    return {"k": float(k), "se": se, "p": float(stats.t.sf(float(k) / se, g_count - 1)), "df": g_count - 1,
+            "groups_informative": len(groups_inf), "groups": len(set(groups))}
+
+
+def effective_papers(rows) -> tuple:
+    """Test-side: (Σ I_g)² / Σ I_g² and max I_g / Σ I_g, I_g a paper's sum of squared within-alloy
+    deviations of the transformed grain size."""
+    f = frame(rows)
+    dev = f["x"] - f.groupby("alloy")["x"].transform("mean")
+    info = (dev ** 2).groupby(f["group"]).sum()
+    return float(info.sum() ** 2 / (info ** 2).sum()), float(info.max() / info.sum())
diff --git a/tests/test_recheck_fixes.py b/tests/test_recheck_fixes.py
new file mode 100644
index 0000000..c1a8c17
--- /dev/null
+++ b/tests/test_recheck_fixes.py
@@ -0,0 +1,206 @@
+"""Step 7 re-check fixes (ChatGPT, 2026-10-06) and the owner's decision on concentrated evidence.
+
+Owner (2026-10-06): for every analysis, the effective number of papers (Σ I_g)² / Σ I_g², I_g a paper's
+sum of squared within-alloy deviations of the transformed grain size, and the largest single paper's
+share are stored with the result. Validity check 2 requires an effective number of at least 2; below
+that, the coefficient only, with the reason 'evidence_concentrated'. The minimum of 10 remains the
+count of informative papers. The same check applies in every simulated fit.
+"""
+from __future__ import annotations
+
+import math
+import random
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
+def as_reference(rows):
+    return [(f"a{a}", f"paper:{p}", d, y) for (a, p, d, y) in rows]
+
+
+def design_of(rows, name="r"):
+    return st.design(analysis.observations(frozen(rows, name)["records"], g.plan(), "primary"), "inverse_square_root")
+
+
+def nudged_rows():
+    """The reviewer's nudged design: the original five alloys × six records, the four mean-valued
+    predictors in each alloy moved to 0.5 ± 0.000001 (alternating), so every paper is informative."""
+    sizes, ys = (16.0, 16.0 / 9.0, 4.0, 4.0, 4.0, 4.0), (400.0, 600.0, 470.0, 510.0, 500.0, 490.0)
+    rows, n = [], 0
+    for a in range(5):
+        for j in range(6):
+            paper = "paper-00" if j < 2 else f"paper-{1 + n % 10:02d}"
+            n += j >= 2
+            x = sizes[j] ** -0.5 if j < 2 else 0.5 + (1e-6 if j % 2 == 0 else -1e-6)
+            rows.append((a, paper, x ** -2, ys[j] + 100.0 * a))
+    return rows
+
+
+def counterexample_rows():
+    """The reviewer's counterexample: one alloy, five papers, one record each; small contrasts carry
+    large residuals."""
+    xs = (1.999, 2.001, 2 + 1e-10, 2 - 1e-10, 2.0)
+    offsets = (1e-6, 1e-6, 100.0, 100.0, -200.0 - 2e-6)
+    return [(0, f"p{i}", x ** -2, 300.0 + 0.01 * x + o) for i, (x, o) in enumerate(zip(xs, offsets))]
+
+
+# --- concentrated evidence (owner's decision) -------------------------------------------------------
+
+@pytest.mark.parametrize("option", ["fixed_minimum", "use_available"])
+def test_the_nudged_design_gives_no_verdict(option):
+    out = analysis.analyse(g.plan(option, n_simulations=200), frozen(nudged_rows(), "nudge"))
+    pooled = out["analyses"][0]
+    assert pooled["counts"]["n_groups_informative"] == 11  # every paper counts as informative...
+    assert pooled["counts"]["effective_papers"] < 1.001  # ...but one paper carries the information
+    assert pooled["counts"]["largest_paper_share"] > 0.999
+    assert out["decision"]["verdict"] is None and pooled["p_value"] is None and pooled["std_error"] is None
+    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "evidence_concentrated"
+    assert {c["reason"] for c in pooled["calibration"].values()} == {"evidence_concentrated"}
+    if option == "use_available":
+        assert out["decision"]["evidence_level"] == 4 and pooled["estimate"] is not None
+
+
+def test_the_effective_number_of_papers_is_the_owners_formula():
+    for spec in g.FIXED_SET:
+        data = g.frozen_data(spec)
+        d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
+        if not d.coefficient_fitted:
+            assert (d.effective_papers, d.largest_paper_share) == (0.0, None)
+            continue
+        n_eff, share = rs.effective_papers(g.rows(data))
+        assert math.isclose(d.effective_papers, n_eff, rel_tol=1e-9), spec.name
+        assert math.isclose(d.largest_paper_share, share, rel_tol=1e-9), spec.name
+        assert d.effective_papers <= d.n_groups_informative + 1e-9
+
+
+def test_every_simulated_fit_requires_two_effective_papers():
+    d = design_of(nudged_rows(), "nudge")
+    rng = np.random.default_rng(4)
+    outcomes = rng.normal(0, 60, (300, d.n)) + rng.normal(0, 40, (300, d.n_groups))[:, d.group]
+    assert cal.significant_count(d, outcomes, 0.05) == 0
+
+
+def test_the_effective_number_and_share_are_reported_with_every_result():
+    out = analysis.analyse(g.plan("fixed_minimum", n_simulations=50), g.frozen_data(g.SPECS["small_but_valid"]))
+    for e in out["analyses"]:  # also withheld results: structure only, no outcome
+        assert e["withheld"] and e["counts"]["effective_papers"] > 0 and 0 < e["counts"]["largest_paper_share"] <= 1
+
+
+# --- every paper's score stays in the covariance -----------------------------------------------------
+
+def test_the_counterexample_keeps_every_papers_score():
+    """Every paper's score in the sandwich; informative papers (two) only in the factor and the df. The
+    result equals the independent check (statsmodels' covariance over every cluster, rescaled) and is no
+    less cautious than counting every paper; the old filtered result (p = 0.0366) is gone."""
+    rows = counterexample_rows()
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, "ce"))["analyses"][0]
+    d = design_of(rows, "ce")
+    assert (d.n_groups, d.n_groups_informative) == (5, 2) and d.effective_papers >= 2
+    ref = rs.fit_informative(as_reference(rows))  # every score; informative papers in factor and df
+    every = rs.fit_informative(as_reference(rows), count="all")  # the earlier, all-paper definition
+    assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-6)
+    assert math.isclose(pooled["p_value"], ref["p"], rel_tol=1e-6)
+    assert math.isclose(every["p"], 0.1685, abs_tol=5e-5)  # the reviewer's all-paper figure
+    assert pooled["df"] == 1 and pooled["p_value"] >= every["p"]
+    assert not math.isclose(pooled["p_value"], 0.0366, rel_tol=0.01)
+
+
+def test_simulated_fits_keep_every_papers_score():
+    """Simulated outcomes with the counterexample's structure (residuals near zero on the two
+    informative papers, large on the others): each simulated fit is decided as the independent check
+    decides it, which keeps every paper's score."""
+    rows = counterexample_rows()
+    d = design_of(rows, "ce")
+    rng = np.random.default_rng(8)
+    informative = np.abs(st.demeaned(d.x, d.alloy, d.n_alloys)) > 1e-6
+    noise = np.zeros((300, d.n))
+    # As in the counterexample, each kind's residuals sum to zero, so the alloy's average absorbs none of them.
+    for mask, size in ((informative, 1e-6), (~informative, 100.0)):
+        idx = np.flatnonzero(mask)
+        draws = rng.normal(0, size, (300, idx.size - 1))
+        noise[:, idx[:-1]], noise[:, idx[-1]] = draws, -draws.sum(axis=1)
+    outcomes = 300.0 + 0.01 * d.x[None, :] + noise
+    expected = 0
+    for y in outcomes:
+        sim = [(f"a{d.alloy[i]}", f"g{d.group[i]}", float(d.x[i]) ** -2, float(y[i])) for i in range(d.n)]
+        expected += rs.fit_informative(sim)["p"] < 0.05
+    assert cal.significant_count(d, outcomes, 0.05) == expected
+
+
+# --- distinct grain sizes from the full range ---------------------------------------------------------
+
+def test_adding_a_record_never_removes_an_alloys_contrast():
+    """The reviewer's chain: [1, 1+1.5e-10] has contrast; inserting 1+0.75e-10 must keep it."""
+    assert st.has_contrast([1.0, 1.0 + 1.5e-10])
+    assert st.has_contrast([1.0, 1.0 + 0.75e-10, 1.0 + 1.5e-10])
+    assert not st.has_contrast([1.0, 1.0 + 0.5e-10])
+    rnd = random.Random(1)
+    for _ in range(2000):
+        values = [1.0 + rnd.uniform(0, 3e-10) for _ in range(rnd.randint(2, 6))]
+        if st.has_contrast(values):
+            assert st.has_contrast(values + [rnd.uniform(min(values), max(values))])
+            assert st.has_contrast(values + [1.0 + rnd.uniform(-1e-9, 1e-9)])
+
+
+def test_an_alloy_keeps_its_contrast_in_a_design_when_a_middle_record_is_added():
+    base = [(0, "p1", 1.0, 400.0), (0, "p2", (1.0 + 1.5e-10) ** -2, 410.0), (1, "p1", 1.0, 500.0), (1, "p2", 4.0, 420.0)]
+    with_middle = base + [(0, "p3", (1.0 + 0.75e-10) ** -2, 405.0)]
+    assert design_of(base, "c1").n_alloys == design_of(with_middle, "c2").n_alloys
+
+
+# --- the numerical zero at the data's own scale ---------------------------------------------------------
+
+def big_baseline_rows(k=1e-5, noise=0.0, seed=2):
+    rng = np.random.default_rng(seed)
+    return [(a, f"p{(j + a) % 5}", d, 200.0 + 175.0 * a + k * d ** -0.5 + (rng.normal(0, noise) if noise else 0.0))
+            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
+
+
+def test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference():
+    """Baselines 200 to 900 MPa, k = 1e-5, no noise: residuals are rounding at the data's scale."""
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(big_baseline_rows(), "big"))["analyses"][0]
+    assert pooled["inference_reason"] == "uncertainty_not_estimable" and pooled["p_value"] is None
+    assert math.isclose(pooled["estimate"], 1e-5, rel_tol=1e-3)
+    assert cal.henderson_iii(design_of(big_baseline_rows(), "big"))["reason"] == "scatter_not_estimable"
+
+
+def test_a_perfect_fit_is_judged_the_same_whatever_the_baselines():
+    for shift in (0.0, 1e3, 1e6):
+        rows = [(a, p, d, y + shift) for a, p, d, y in big_baseline_rows(k=250.0)]
+        pooled = analysis.analyse(g.plan("use_available", n_simulations=20), frozen(rows, f"s{shift}"))["analyses"][0]
+        assert pooled["inference_reason"] == "uncertainty_not_estimable", shift
+
+
+def test_small_real_noise_with_large_baselines_stays_estimable():
+    """An arithmetic safeguard, not a scientific minimum: 0.01 MPa of scatter on 200 to 900 MPa is estimated."""
+    rows = big_baseline_rows(k=250.0, noise=0.01)
+    pooled = analysis.analyse(g.plan("use_available", n_simulations=20), frozen(rows, "noisy"))["analyses"][0]
+    assert pooled["inference_reason"] is None and pooled["std_error"] > 0
+    assert cal.henderson_iii(design_of(rows, "noisy"))["reason"] in (None, "shift_not_estimable")
+
+
+# --- the detection note states the locked threshold -----------------------------------------------------
+
+def test_the_detection_note_states_the_plans_threshold():
+    plan = g.plan("use_available", n_simulations=50)
+    plan["model"]["alpha"] = 0.01
+    pooled = analysis.analyse(plan, g.frozen_data(g.SPECS["effect_many_papers"]))["analyses"][0]
+    assert "α = 0.01" in pooled["detection_note"] and "5%" not in pooled["detection_note"]
+
+
+def test_simulated_perfect_fits_on_large_baselines_are_never_significant():
+    """The residual floor applies in every simulated fit: exact outcomes on baselines of 200 to 900 MPa
+    with a tiny slope (where the standard-error check alone lets rounding through)."""
+    d = design_of(big_baseline_rows(), "big")
+    baselines = 200.0 + 175.0 * d.alloy
+    exact = np.vstack([baselines + k * d.x for k in (1e-5, 3e-5, 1e-4)])
+    assert cal.significant_count(d, exact, 0.05) == 0
diff --git a/tests/test_statistics.py b/tests/test_statistics.py
index 43f089f..d15fbe7 100644
--- a/tests/test_statistics.py
+++ b/tests/test_statistics.py
@@ -79,7 +79,10 @@ def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
             ("r6", "C", "p4", 3.0, 300.0)]
     d = st.design(obs(rows), "inverse_square_root")
     assert (d.n, d.n_alloys, d.n_groups, d.n_records_in_set, d.n_alloys_not_used) == (3, 1, 2, 6, 2)
-    assert d.resid_df == 1 and d.coefficient_fitted and d.counts_allow_inference
+    assert d.resid_df == 1 and d.coefficient_fitted
+    # Re-check (owner, 2026-10-06): the two papers carry unequal information (effective number 1.8 < 2),
+    # so check 2 fails on concentrated evidence; the counts below are unaffected.
+    assert not d.counts_allow_inference and d.counts_reason == "evidence_concentrated"
     entry = st.analysis_entry(d, g.plan("use_available", minimums=(3, 1, 2, 1)), withheld=False)
     assert entry["counts"]["n_records_not_used"] == 3
     assert entry["minimums"]["records"] == {"count": 3, "minimum": 3, "met": True}
@@ -93,7 +96,11 @@ def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
     ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 1.0, 2.0)], False, False),              # one grain size
     ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0)], True, False),               # resid df 0
     ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p1", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, False),  # 1 group
-    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, True),
+    # Re-check (owner, 2026-10-06): this design's information is concentrated in p1 (effective number
+    # about 1.1), so check 2 now fails; the balanced case after it passes.
+    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, False),
+    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p1", 4.0, 2.0), ("c", "A", "p2", 1.0, 1.5), ("d", "A", "p2", 4.0, 2.9)],
+     True, True),
 ])
 def test_the_two_validity_checks(rows, check1, check2):
     d = st.design(obs(rows), "inverse_square_root")
```


### Commit `f0ad7c2`

```
f0ad7c2 Step 7 re-check fixes: migration 0004 stores the effective number of papers and the largest share; check 2 needs two effective papers

 .../migrations/versions/0004_statistics_results.py | 37 ++++++++++++++++------
 hypocurate/db/models.py                            | 19 ++++++++---
 tests/model_builder.py                             |  8 +++--
 tests/test_analysis_stage.py                       | 20 +++++++++++-
 4 files changed, 66 insertions(+), 18 deletions(-)
```

```diff
diff --git a/hypocurate/db/migrations/versions/0004_statistics_results.py b/hypocurate/db/migrations/versions/0004_statistics_results.py
index 6015532..fadc966 100644
--- a/hypocurate/db/migrations/versions/0004_statistics_results.py
+++ b/hypocurate/db/migrations/versions/0004_statistics_results.py
@@ -25,6 +25,9 @@ analysis_result:
   implication (check 2 needs a coefficient, a residual degree of freedom and two informative groups,
   but can also fail on an unestimable uncertainty), and `inference_reason` states why it failed
   (derived by the trigger where the counts determine it; 'uncertainty_not_estimable' must be given).
+- `effective_papers` ((Σ I_g)² / Σ I_g², I_g a paper's sum of squared within-alloy deviations of the
+  transformed grain size) and `largest_paper_share` (re-check, owner 2026-10-06): check 2 also needs
+  an effective number of at least 2; below it the reason is 'evidence_concentrated'.
 - `label_reason` (present exactly with "not enough data") and `estimated_power_estimated_noise`
   (the detection rate under the estimated noise; never on a withheld result).
 - `test_run_label`: "test run: includes constructed data" exactly when the run is marked.
@@ -171,11 +174,12 @@ ANALYSIS_RESULT_INSERT_0004 = """
                                 AND NEW.n_groups_informative >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
             PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
         END IF;
-        -- Why check 2 failed, where the counts determine it; an unestimable uncertainty must be stated.
+        -- Why check 2 failed, where the structure determines it; an unestimable uncertainty must be stated.
         IF NEW.inference_reason IS NULL AND NOT NEW.check2_passed THEN
             NEW.inference_reason := CASE WHEN NOT NEW.check1_passed THEN 'coefficient_not_fitted'
                                          WHEN NOT (NEW.resid_df >= 1 AND NEW.n_groups_informative >= 2)
-                                         THEN 'insufficient_groups' END;
+                                         THEN 'insufficient_groups'
+                                         WHEN coalesce(NEW.effective_papers, 0) < 2 THEN 'evidence_concentrated' END;
         END IF;
         -- Step 7, decision 1: withheld run-wide when the pooled fit misses a minimum under the fixed option.
         IF NEW.scope = 'pooled' THEN
@@ -239,14 +243,17 @@ CALIBRATION_INSERT_0004 = """
 NEW_LABELS = "('agrees', 'conflicts', 'not_enough_data', 'same_direction_different_decision')"
 OLD_LABELS = "('agrees', 'conflicts', 'not_enough_data')"
 NEW_REASONS = ("('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups', 'below_minimums', "
-               "'scatter_not_estimable', 'shift_not_estimable', 'uncertainty_not_estimable')")
-INFERENCE_REASONS = "('coefficient_not_fitted', 'insufficient_groups', 'uncertainty_not_estimable')"
+               "'scatter_not_estimable', 'shift_not_estimable', 'uncertainty_not_estimable', 'evidence_concentrated')")
+INFERENCE_REASONS = ("('coefficient_not_fitted', 'insufficient_groups', 'evidence_concentrated', "
+                     "'uncertainty_not_estimable')")
 LABEL_REASONS = "('no_p_value', 'pooled_without_decision', 'zero_coefficient')"
 COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"
+SPREAD = "coalesce(effective_papers, 0) >= 2"  # re-check (owner, 2026-10-06): two effective papers
 INFERENCE_REASON = ("(inference_reason IS NULL) = check2_passed "
                     "AND (inference_reason IS NOT DISTINCT FROM 'coefficient_not_fitted') = NOT check1_passed "
                     f"AND (inference_reason IS DISTINCT FROM 'insufficient_groups' OR NOT {COUNTS_ALLOW}) "
-                    f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR {COUNTS_ALLOW})")
+                    f"AND (inference_reason IS DISTINCT FROM 'evidence_concentrated' OR ({COUNTS_ALLOW} AND NOT {SPREAD})) "
+                    f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR ({COUNTS_ALLOW} AND {SPREAD}))")
 OLD_REASONS = "('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')"
 
 EVIDENCE_LEVEL = ("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
@@ -260,10 +267,11 @@ IN_USE = """
         IF EXISTS (SELECT 1 FROM analysis_result WHERE withheld OR n_records_not_used <> 0
                    OR test_run_label IS NOT NULL OR label = 'same_direction_different_decision'
                    OR n_groups_informative <> n_groups OR inference_reason = 'uncertainty_not_estimable'
-                   OR label_reason IS NOT NULL OR estimated_power_estimated_noise IS NOT NULL)
+                   OR label_reason IS NOT NULL OR estimated_power_estimated_noise IS NOT NULL
+                   OR effective_papers IS NOT NULL OR inference_reason = 'evidence_concentrated')
            OR EXISTS (SELECT 1 FROM calibration_result WHERE method = 'estimated' OR test_run_label IS NOT NULL
                       OR reason IN ('below_minimums', 'scatter_not_estimable', 'shift_not_estimable',
-                                    'uncertainty_not_estimable'))
+                                    'uncertainty_not_estimable', 'evidence_concentrated'))
            OR EXISTS (SELECT 1 FROM run WHERE evidence_level IS NOT NULL) THEN
             RAISE EXCEPTION USING MESSAGE = 'hypocurate: 0004 cannot be downgraded while step 7 results use it',
                                   ERRCODE = 'check_violation';
@@ -294,6 +302,13 @@ def upgrade() -> None:
     for column in ('inference_reason', 'label_reason'):
         op.add_column('analysis_result', sa.Column(column, sa.Text(), nullable=True))
     op.add_column('analysis_result', sa.Column('estimated_power_estimated_noise', sa.Double(), nullable=True))
+    # Re-check (owner, 2026-10-06): the effective number of papers and the largest paper's share.
+    op.add_column('analysis_result', sa.Column('effective_papers', sa.Double(), nullable=True))
+    op.add_column('analysis_result', sa.Column('largest_paper_share', sa.Double(), nullable=True))
+    op.create_check_constraint(op.f('ck_analysis_result_effective_papers'), 'analysis_result',
+                               'effective_papers IS NULL OR effective_papers >= 0')
+    op.create_check_constraint(op.f('ck_analysis_result_largest_paper_share'), 'analysis_result',
+                               'largest_paper_share IS NULL OR (largest_paper_share > 0 AND largest_paper_share <= 1)')
     op.create_check_constraint(op.f('ck_analysis_result_inference_reason_value'), 'analysis_result',
                                f"inference_reason IS NULL OR inference_reason IN {INFERENCE_REASONS}")
     op.create_check_constraint(op.f('ck_analysis_result_label_reason_value'), 'analysis_result',
@@ -307,7 +322,7 @@ def upgrade() -> None:
                        ("std_error_iff_check2", "(check2_passed AND NOT withheld) = (std_error IS NOT NULL)"),
                        ("p_value_iff_check2", "(check2_passed AND NOT withheld) = (p_value IS NOT NULL)"),
                        ("label", f"label IS NULL OR label IN {NEW_LABELS}"),
-                       ("check2_consistent", f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW})")):
+                       ("check2_consistent", f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW} AND {SPREAD})")):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
         op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
     op.create_check_constraint(op.f('ck_analysis_result_inference_reason'), 'analysis_result', INFERENCE_REASON)
@@ -358,7 +373,8 @@ def downgrade() -> None:
     op.drop_column('calibration_result', 'method')
     op.execute(ANALYSIS_RESULT_INSERT_0001)
     for name in ('power_needs_check2', 'label_per_source_only', 'inference_reason', 'power_estimated_noise',
-                 'label_reason', 'label_reason_value', 'inference_reason_value', 'informative_within_groups'):
+                 'label_reason', 'label_reason_value', 'inference_reason_value', 'informative_within_groups',
+                 'effective_papers', 'largest_paper_share'):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
     for name, expr in (("estimate_iff_check1", "check1_passed = (estimate IS NOT NULL)"),
                        ("std_error_iff_check2", "check2_passed = (std_error IS NOT NULL)"),
@@ -368,7 +384,8 @@ def downgrade() -> None:
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
         op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
     # After the constraints that name them are restored (a dropped column takes its constraints with it).
-    for column in ('estimated_power_estimated_noise', 'label_reason', 'inference_reason', 'n_groups_informative'):
+    for column in ('estimated_power_estimated_noise', 'label_reason', 'inference_reason', 'n_groups_informative',
+                   'effective_papers', 'largest_paper_share'):
         op.drop_column('analysis_result', column)
     for name in ('test_run_label', 'not_used_not_negative', 'withheld_set'):
         op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index c456c81..b2085e8 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -637,9 +637,10 @@ class FlagRecord(Base):
 SCOPES = ("pooled", "per_source", "sensitivity")
 LABELS = ("agrees", "conflicts", "not_enough_data", "same_direction_different_decision")  # 4th: step 7
 TEST_RUN_LABEL = "test run: includes constructed data"
-INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "uncertainty_not_estimable")
+INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "evidence_concentrated", "uncertainty_not_estimable")
 LABEL_REASONS = ("no_p_value", "pooled_without_decision", "zero_coefficient")
 COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"
+SPREAD = "coalesce(effective_papers, 0) >= 2"
 
 
 class AnalysisResult(Base):
@@ -680,6 +681,9 @@ class AnalysisResult(Base):
     inference_reason: Mapped[str | None] = mapped_column(Text)
     label_reason: Mapped[str | None] = mapped_column(Text)
     estimated_power_estimated_noise: Mapped[float | None] = mapped_column(Double)
+    # Re-check (owner, 2026-10-06): concentrated evidence.
+    effective_papers: Mapped[float | None] = mapped_column(Double)
+    largest_paper_share: Mapped[float | None] = mapped_column(Double)
     __table_args__ = (
         ForeignKeyConstraint(["analysis_set_id", "run_id"], ["analysis_set.id", "analysis_set.run_id"],
                              name="fk_analysis_result_analysis_set"),
@@ -696,14 +700,21 @@ class AnalysisResult(Base):
         CheckConstraint("n_records = 0 OR n_groups >= 1", name="records_have_a_group"),
         CheckConstraint("resid_df = n_records - n_alloys - 1", name="resid_df_definition"),
         CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_consistent"),
-        CheckConstraint(f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW})", name="check2_consistent"),
+        CheckConstraint(f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW} AND {SPREAD})",
+                        name="check2_consistent"),
+        CheckConstraint("effective_papers IS NULL OR effective_papers >= 0", name="effective_papers"),
+        CheckConstraint("largest_paper_share IS NULL OR (largest_paper_share > 0 AND largest_paper_share <= 1)",
+                        name="largest_paper_share"),
         CheckConstraint("n_groups_informative BETWEEN 0 AND n_groups", name="informative_within_groups"),
         CheckConstraint("inference_reason IS NULL OR " + one_of("inference_reason", INFERENCE_REASONS),
                         name="inference_reason_value"),
         CheckConstraint("(inference_reason IS NULL) = check2_passed "
                         "AND (inference_reason IS NOT DISTINCT FROM 'coefficient_not_fitted') = NOT check1_passed "
                         f"AND (inference_reason IS DISTINCT FROM 'insufficient_groups' OR NOT {COUNTS_ALLOW}) "
-                        f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR {COUNTS_ALLOW})",
+                        f"AND (inference_reason IS DISTINCT FROM 'evidence_concentrated' OR ({COUNTS_ALLOW} AND NOT "
+                        f"{SPREAD})) "
+                        f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR ({COUNTS_ALLOW} AND "
+                        f"{SPREAD}))",
                         name="inference_reason"),
         CheckConstraint("label_reason IS NULL OR " + one_of("label_reason", LABEL_REASONS), name="label_reason_value"),
         CheckConstraint("(label_reason IS NOT NULL) = (label IS NOT DISTINCT FROM 'not_enough_data')",
@@ -726,7 +737,7 @@ class AnalysisResult(Base):
 
 CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups",
                        "below_minimums", "scatter_not_estimable", "shift_not_estimable",  # step 7
-                       "uncertainty_not_estimable")  # step 7 review fix
+                       "uncertainty_not_estimable", "evidence_concentrated")  # step 7 review fixes
 CALIBRATION_METHODS = ("fixed", "estimated")
 CALIBRATION_NUMBERS = ("assumptions", "n_simulations", "seed", "null_share", "null_ci_low", "null_ci_high",
                        "effect_share", "effect_ci_low", "effect_ci_high", "confidence_flag")
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 156a907..ea489fc 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -232,10 +232,12 @@ class World:
         check1, check2 = check1 and not withheld, check2 and not withheld  # only for the values below
         return self.val(
             "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, "
-            "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
-            "VALUES (:r, :sc, :s, :src, :n, :a, :g, :gi, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
+            "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, "
+            "effective_papers) VALUES (:r, :sc, :s, :src, :n, :a, :g, :gi, :df, :c1, :c2, :mm, :est, :se, :p, :ep) "
+            "RETURNING id",
             r=rid, sc=scope, s=set_id, src=self.source[source] if source else None, n=n, a=alloys, g=groups,
-            gi=informative, df=resid, c1=alloys >= 1, c2=counts_check2, mm=minimums_met,
+            # Re-check: the effective number of papers, as if every informative paper carried equal information.
+            gi=informative, ep=float(informative), df=resid, c1=alloys >= 1, c2=counts_check2, mm=minimums_met,
             est=428.0 if check1 else None,
             se=64.0 if check2 else None, p=1e-6 if check2 else None)
 
diff --git a/tests/test_analysis_stage.py b/tests/test_analysis_stage.py
index 025a14a..442dfcd 100644
--- a/tests/test_analysis_stage.py
+++ b/tests/test_analysis_stage.py
@@ -268,7 +268,8 @@ def _insert_result(engine, rid, **over):
     sets = dict(rows_of(engine, "SELECT key, id FROM analysis_set WHERE run_id = :r", r=rid))
     n = val(engine, "SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sets["primary"])
     cols = dict(run_id=rid, scope="pooled", analysis_set_id=sets["primary"], n_records=n, n_alloys=3, n_groups=3,
-                n_groups_informative=3, resid_df=n - 4, check1_passed=True, check2_passed=True, minimums_met=False,
+                n_groups_informative=3, effective_papers=3.0, resid_df=n - 4, check1_passed=True, check2_passed=True,
+                minimums_met=False,
                 estimate=None, std_error=None, p_value=None)
     cols.update(over)
     with engine.begin() as conn:
@@ -454,3 +455,20 @@ def test_a_label_reason_is_stored_exactly_with_not_enough_data(engine):
     analysis.run_statistics(engine, rid)
     per_source = [r for r in result_rows(engine, rid) if r.scope == "per_source"]
     assert all((r.label == "not_enough_data") == (r.label_reason is not None) for r in per_source)
+
+
+def test_the_database_requires_two_effective_papers_for_check_2(engine):
+    """Re-check (owner, 2026-10-06): check 2 needs an effective number of papers of at least 2."""
+    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
+    with pytest.raises(IntegrityError, match="ck_analysis_result_check2_consistent"):
+        _insert_result(engine, rid, effective_papers=1.5, estimate=1.0, std_error=1.0, p_value=0.1)
+    _insert_result(engine, rid, effective_papers=1.5, check2_passed=False, estimate=1.0)
+    assert rows_of(engine, "SELECT inference_reason FROM analysis_result WHERE run_id = :r", r=rid) == [
+        ("evidence_concentrated",)]
+
+
+def test_the_effective_number_and_share_are_stored_with_every_result(engine):
+    rid = run_on(engine, small_rows(3, papers=3))  # withheld: structure only
+    analysis.run_statistics(engine, rid)
+    for r in result_rows(engine, rid):
+        assert r.effective_papers > 0 and 0 < r.largest_paper_share <= 1
```


### Commit `1320840`

```
1320840 Step 7 re-check fixes: register (effective_papers; informative_groups_in_inference, numerical_zero, validity_checks, smallest_effect reworded)

 hypocurate/assumptions.json | 124 +++++++++++++++++++++++++++++++++++++++-----
 1 file changed, 110 insertions(+), 14 deletions(-)
```

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index e3117af..327fcd3 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -1896,7 +1896,7 @@
     "key": "validity_checks",
     "name": "The two validity checks",
     "state": "in_force",
-    "statement": "Check 1: at least one alloy measured at two grain sizes that are distinct after the transformation, or nothing is fitted. Check 2: at least 1 residual degree of freedom, at least 2 informative groups (entry 'informative_groups'), and a clustered standard error that is finite and above the numerical zero (entry 'numerical_zero'); otherwise the coefficient is reported alone, with the reason, and no uncertainty, no p-value and no verdict. Neither can be waived. The same checks apply to every simulated fit.",
+    "statement": "Check 1: at least one alloy measured at two grain sizes that are distinct after the transformation, or nothing is fitted. Check 2: at least 1 residual degree of freedom, at least 2 informative groups (entry 'informative_groups'), an effective number of papers of at least 2 (entry 'effective_papers'), and a clustered standard error that is finite and above the numerical zero (entry 'numerical_zero'); otherwise the coefficient is reported alone, with the reason, and no uncertainty, no p-value and no verdict. Neither can be waived. The same checks apply to every simulated fit.",
     "value": {
       "text": "check 1: 1 alloy at 2 grain sizes; check 2: 1 residual df and 2 groups",
       "unit": null
@@ -1945,6 +1945,12 @@
         "from": "2026-10-04",
         "to": "2026-10-06",
         "note": "Step 7 review, finding 1 and the owner's decision on informative papers (2026-10-06)."
+      },
+      {
+        "value": "Check 1: at least one alloy measured at two grain sizes that are distinct after the transformation, or nothing is fitted. Check 2: at least 1 residual degree of freedom, at least 2 informative groups (entry 'informative_groups'), and a clustered standard error that is finite and above the numerical zero (entry 'numerical_zero'); otherwise the coefficient is reported alone, with the reason, and no uncertainty, no p-value and no verdict. Neither can be waived. The same checks apply to every simulated fit.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Re-check (owner, 2026-10-06): concentrated evidence."
       }
     ],
     "notes": [],
@@ -1954,6 +1960,7 @@
       "tests/test_data_model.py::test_stored_counts_must_be_consistent",
       "tests/test_data_model.py::test_the_validity_checks_cannot_be_waived",
       "tests/test_generated_fixed_set.py::test_one_alloy_at_two_sizes_and_a_single_group_give_no_verdict_under_either_option",
+      "tests/test_recheck_fixes.py::test_the_nudged_design_gives_no_verdict",
       "tests/test_statistics.py::test_the_two_validity_checks",
       "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only",
       "tests/test_statistics_boundaries.py::test_grain_sizes_equal_after_transformation_never_raise",
@@ -5338,13 +5345,19 @@
         "from": "2026-10-05",
         "to": "2026-10-06",
         "note": "Review, smaller point (2026-10-06): detection rates both ways, with the false-positive shares."
+      },
+      {
+        "value": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it. The detection rate is reported both ways, each beside its false-positive share: under the fixed assumptions (stored as the estimated power, labelled 'estimated power under the stated assumptions', shown also below the minimums, since it uses no outcome value) and under the estimated noise (withheld below the minimums). Both are detection rates of the nominal 5% test, not power for a test shown to keep false positives at 5%. Information only.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Re-check (2026-10-06): the note states the plan's locked threshold, not a fixed 5%."
       }
     ],
     "notes": [],
     "key": "smallest_effect",
     "name": "Smallest effect of interest",
     "state": "in_force",
-    "statement": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it. The detection rate is reported both ways, each beside its false-positive share: under the fixed assumptions (stored as the estimated power, labelled 'estimated power under the stated assumptions', shown also below the minimums, since it uses no outcome value) and under the estimated noise (withheld below the minimums). Both are detection rates of the nominal 5% test, not power for a test shown to keep false positives at 5%. Information only.",
+    "statement": "The smallest effect that matters is a query setting in the plan's 'calibration' part, default 150 MPa·µm^0.5. The calibration's effect world uses it. The detection rate is reported both ways, each beside its false-positive share: under the fixed assumptions (stored as the estimated power, labelled 'estimated power under the stated assumptions', shown also below the minimums, since it uses no outcome value) and under the estimated noise (withheld below the minimums). Both are detection rates of the nominal test at the plan's locked threshold α (stated in the note), not power for a test shown to keep false positives at α. Information only.",
     "value": {
       "text": "150 (default)",
       "unit": "MPa·µm^0.5"
@@ -5376,6 +5389,7 @@
     "tests": [
       "tests/test_analysis_stage.py::test_the_estimated_detection_rate_is_never_stored_for_a_withheld_result",
       "tests/test_calibration.py::test_estimated_power_is_the_fixed_methods_effect_share_and_needs_no_outcome",
+      "tests/test_recheck_fixes.py::test_the_detection_note_states_the_plans_threshold",
       "tests/test_statistics.py::test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting",
       "tests/test_statistics_boundaries.py::test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld",
       "tests/test_statistics_boundaries.py::test_detection_rates_are_reported_both_ways_with_the_false_positive_shares"
@@ -5755,7 +5769,14 @@
       "name": null,
       "date": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "A quantity counts as zero when it is at most 1e-10 times its natural scale in the same units: a transformed grain-size difference or contrast against the largest transformed grain size; the clustered standard error against sqrt(Σ ỹ² / Σ x̃²), the slope scale of the data; the residual sum of squares of the scatter estimate against the outcome's spread within alloys (squared). Below it: grain sizes are not distinct, an uncertainty is not estimable (coefficient only), or scatter is not estimable. The same check applies to every simulated fit.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Re-check findings 4 and 5 (2026-10-06): the adjacent-gap rule could remove a contrast when a record was added; rounding at the scale of large baselines was taken for real residuals."
+      }
+    ],
     "notes": [],
     "state": "in_force",
     "decided": {
@@ -5764,9 +5785,9 @@
     },
     "key": "numerical_zero",
     "name": "Numerical zero",
-    "statement": "A quantity counts as zero when it is at most 1e-10 times its natural scale in the same units: a transformed grain-size difference or contrast against the largest transformed grain size; the clustered standard error against sqrt(Σ ỹ² / Σ x̃²), the slope scale of the data; the residual sum of squares of the scatter estimate against the outcome's spread within alloys (squared). Below it: grain sizes are not distinct, an uncertainty is not estimable (coefficient only), or scatter is not estimable. The same check applies to every simulated fit.",
+    "statement": "An arithmetic safeguard, not a scientific minimum. A transformed grain-size range counts as zero when it is at most 1e-10 times the largest transformed grain size (decided on the full range, so adding a record never removes a contrast). Residuals count as zero (a perfect fit: no uncertainty, no scatter) when their root mean square is at most the larger of 1e-10 times the outcome's root mean square within alloys and 1e-12 times the largest outcome magnitude (rounding also comes from the baselines). A clustered standard error must also exceed 1e-10 × sqrt(Σ ỹ² / Σ x̃²). Within-alloy centring subtracts each alloy's first value before the mean (stable centring). The same checks apply to every simulated fit.",
     "value": {
-      "text": "1e-10 relative to the natural scale",
+      "text": "1e-10 of the natural scale; residuals also 1e-12 of the largest outcome",
       "unit": null
     },
     "category": "statistical",
@@ -5781,32 +5802,44 @@
         {
           "ref": "python:hypocurate.pipeline.statistics:RELATIVE_ZERO",
           "equals": 1e-10
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:ARITHMETIC_ZERO",
+          "equals": 1e-12
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:has_contrast"
         }
       ],
       "note": null
     },
     "tests": [
+      "tests/test_recheck_fixes.py::test_a_perfect_fit_is_judged_the_same_whatever_the_baselines",
+      "tests/test_recheck_fixes.py::test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference",
+      "tests/test_recheck_fixes.py::test_adding_a_record_never_removes_an_alloys_contrast",
+      "tests/test_recheck_fixes.py::test_an_alloy_keeps_its_contrast_in_a_design_when_a_middle_record_is_added",
+      "tests/test_recheck_fixes.py::test_small_real_noise_with_large_baselines_stays_estimable",
+      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_scatter",
       "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only",
-      "tests/test_statistics_boundaries.py::test_small_real_noise_keeps_the_uncertainty_estimable",
-      "tests/test_statistics_boundaries.py::test_the_uncertainty_check_is_scale_aware",
       "tests/test_statistics_boundaries.py::test_grain_sizes_equal_after_transformation_never_raise",
       "tests/test_statistics_boundaries.py::test_nearly_equal_transformed_grain_sizes_are_not_distinct",
-      "tests/test_statistics_boundaries.py::test_an_exact_fit_has_no_estimable_scatter",
       "tests/test_statistics_boundaries.py::test_small_real_noise_gives_an_estimable_scatter",
-      "tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit"
+      "tests/test_statistics_boundaries.py::test_small_real_noise_keeps_the_uncertainty_estimable",
+      "tests/test_statistics_boundaries.py::test_the_simulations_apply_the_same_check_to_each_simulated_fit",
+      "tests/test_statistics_boundaries.py::test_the_uncertainty_check_is_scale_aware"
     ]
   },
   {
     "key": "informative_groups_in_inference",
     "name": "Informative papers in the uncertainty and the test",
     "state": "in_force",
-    "statement": "The clustered standard error sums the scores of informative papers only, its small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative papers, and the one-sided test uses a t distribution with (informative papers − 1) degrees of freedom: the same count as validity check 2 and the paper minimum. Applied in the real fits and in every simulated fit. With uninformative papers present this gives a larger standard error and fewer degrees of freedom than counting every paper (the cautious direction); where every paper is informative it equals statsmodels' clustered result.",
+    "statement": "The clustered standard error sums every paper's score; its small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative papers, and the one-sided test uses a t distribution with (informative papers − 1) degrees of freedom: the same count as validity check 2's group count and the paper minimum. Applied in the real fits and in every simulated fit. Where every paper is informative it equals statsmodels' clustered result.",
     "value": {
       "text": "G = informative papers in the factor and in the degrees of freedom",
       "unit": null
     },
     "category": "statistical",
-    "affects": "Standard errors, p-values and simulated rejection rates of any fit with uninformative papers; on the reference sets every paper is informative, so no reference number changed.",
+    "affects": "Standard errors, p-values and simulated rejection rates of any fit with uninformative papers; on the reference sets every paper is informative.",
     "reason": "An uninformative paper adds nothing to the slope's clustered variance; counting it in G/(G-1) and in the degrees of freedom made the test less cautious than its information supports.",
     "evidence": [
       "Owner's decision, 2026-10-06, after the second-model review (docs/reviews/step07_review_chatgpt.md, finding 1)."
@@ -5840,14 +5873,77 @@
       "note": null
     },
     "tests": [
+      "tests/test_informative_inference.py::test_every_simulated_fit_counts_informative_papers_only",
       "tests/test_informative_inference.py::test_the_factor_and_degrees_of_freedom_count_informative_papers_only",
       "tests/test_informative_inference.py::test_the_result_is_more_cautious_than_counting_every_paper",
       "tests/test_informative_inference.py::test_where_every_paper_is_informative_nothing_changes",
-      "tests/test_informative_inference.py::test_every_simulated_fit_counts_informative_papers_only"
+      "tests/test_recheck_fixes.py::test_simulated_fits_keep_every_papers_score",
+      "tests/test_recheck_fixes.py::test_the_counterexample_keeps_every_papers_score"
+    ],
+    "history": [
+      {
+        "value": "The clustered standard error sums the scores of informative papers only, its small-sample factor is G/(G-1) × (N-1)/(N-K) with G the informative papers, and the one-sided test uses a t distribution with (informative papers − 1) degrees of freedom: the same count as validity check 2 and the paper minimum. Applied in the real fits and in every simulated fit. With uninformative papers present this gives a larger standard error and fewer degrees of freedom than counting every paper (the cautious direction); where every paper is informative it equals statsmodels' clustered result.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Re-check finding 2 (2026-10-06): dropping uninformative papers' scores from the sum is not always cautious (a small contrast times a large residual can matter); every score is kept, the informative count applies to the factor and the degrees of freedom only."
+      }
     ],
-    "history": [],
     "notes": [
-      "CLAUDE.md rule 6 reworded to match (owner, 2026-10-06)."
+      "CLAUDE.md rule 6 reworded to match (owner, 2026-10-06).",
+      "Fewer counted papers raise the factor and lower the degrees of freedom; this is an approximation, not a guarantee of false-positive control (re-check finding 2)."
     ]
+  },
+  {
+    "key": "effective_papers",
+    "name": "Effective number of papers",
+    "state": "in_force",
+    "statement": "For every analysis, the effective number of papers (Σ I_g)² / Σ I_g², with I_g a paper's sum of squared within-alloy deviations of the transformed grain size, and the largest single paper's share max I_g / Σ I_g are computed and stored with the result. Validity check 2 requires an effective number of at least 2; below that, the coefficient only, with the reason 'evidence_concentrated'. The paper minimum (10) remains the count of informative papers. The same check applies in every simulated fit.",
+    "value": {
+      "text": "check 2 needs an effective number of papers of at least 2",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Validity check 2 and the evidence level when the slope information is concentrated in one paper. On the reference sets: pooled 3.94 effective papers (largest share 39%), MPEA alone 3.93 (39%); check 2 still passes, so no verdict changed.",
+    "reason": "Counting papers with any non-zero contrast does not show that they contribute independent information: the reviewer's nudged design had eleven informative papers but almost all information in one, and gave p ≈ 5e-58 with a 51% null rejection rate.",
+    "evidence": [
+      "Second-model re-check (ChatGPT, 2026-10-06), finding 1: docs/reviews/step07_recheck_chatgpt.md (MacKinnon, Nielsen and Webb on cluster count versus effective information).",
+      "Owner's decision, 2026-10-06."
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
+          "ref": "python:hypocurate.pipeline.statistics:MIN_EFFECTIVE_PAPERS",
+          "equals": 2.0
+        },
+        {
+          "ref": "sql:ck_analysis_result_check2_consistent"
+        },
+        {
+          "ref": "sql:effective_papers"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_recheck_fixes.py::test_the_nudged_design_gives_no_verdict",
+      "tests/test_recheck_fixes.py::test_the_effective_number_of_papers_is_the_owners_formula",
+      "tests/test_recheck_fixes.py::test_every_simulated_fit_requires_two_effective_papers",
+      "tests/test_recheck_fixes.py::test_the_effective_number_and_share_are_reported_with_every_result",
+      "tests/test_analysis_stage.py::test_the_database_requires_two_effective_papers_for_check_2",
+      "tests/test_analysis_stage.py::test_the_effective_number_and_share_are_stored_with_every_result"
+    ],
+    "history": [],
+    "notes": []
   }
 ]
```


## 3. Reference numbers recomputed (on `1320840`)

The reference run through the freeze and `analysis.run_statistics`. ROW columns: analysis, records, alloys, groups, informative groups, residual df, uninformative groups, k, SE, p, label, label reason, inference reason, fixed calibration (no-effect, effect significant of 2,000), estimated calibration, fixed and estimated detection rates. EFF: effective number of papers and the largest single paper's share.

```
ROW pooled 97 22 20 20 74 [] 424.87890989044104 64.3810434838488 1.287151044194178e-06 None None None (157, 2000) (151, 1944) 1.0 0.972
EFF pooled 3.9359 0.3867
ROW per_source:mpea 76 13 19 19 62 [] 424.05442308188793 62.21603775763127 1.1076022212936802e-06 agrees None None (166, 2000) (161, 1922) 1.0 0.961
EFF per_source:mpea 3.9272 0.3872
ROW per_source:tamu_fcc 21 9 1 1 11 [] 1173.3418673474905 None None not_enough_data no_p_value insufficient_groups insufficient_groups insufficient_groups None None
EFF per_source:tamu_fcc 1.0 1.0
ROW sensitivity:no_exclusions 97 22 20 20 74 [] 424.87890989044104 64.3810434838488 1.287151044194178e-06 None None None (157, 2000) (145, 1938) 1.0 0.969
EFF sensitivity:no_exclusions 3.9359 0.3867
ROW sensitivity:tension_and_compression 98 22 21 21 75 [] 428.02404949610104 63.51112235023561 7.398407506070927e-07 None None None (180, 2000) (156, 1960) 1.0 0.98
EFF sensitivity:tension_and_compression 3.9976 0.3871
ROW sensitivity:six_batches_as_groups 97 22 22 22 74 [] 424.87890989044104 64.22883580113376 7.511240461762386e-07 None None None (185, 2000) (163, 1952) 1.0 0.976
EFF sensitivity:six_batches_as_groups 3.9359 0.3867
ROW sensitivity:same_alloy_1_at_pct 97 22 20 20 74 [] 424.87890989044104 64.3810434838488 1.287151044194178e-06 None None None (159, 2000) (171, 1954) 1.0 0.977
EFF sensitivity:same_alloy_1_at_pct 3.9359 0.3867
ROW sensitivity:source_only_assignments 76 13 19 19 62 [] 424.05442308188793 62.21603775763127 1.1076022212936802e-06 None None None (164, 2000) (193, 1915) 1.0 0.9575
EFF sensitivity:source_only_assignments 3.9272 0.3872
ROW sensitivity:scope_not_confirmed_included 103 23 22 22 79 [] 432.3502268594971 64.86124831533819 6.72368893771935e-07 None None None (150, 2000) (166, 1958) 1.0 0.979
EFF sensitivity:scope_not_confirmed_included 4.0666 0.3804
ROW sensitivity:possible_duplicates_separate 97 22 20 20 74 [] 424.87890989044104 64.3810434838488 1.287151044194178e-06 None None None (149, 2000) (148, 1947) 1.0 0.9735
EFF sensitivity:possible_duplicates_separate 3.9359 0.3867
ROW sensitivity:conflicts_survivor_value 97 22 20 20 74 [] 424.87890989044104 64.3810434838488 1.287151044194178e-06 None None None (174, 2000) (170, 1959) 1.0 0.9795
EFF sensitivity:conflicts_survivor_value 3.9359 0.3867
DECISION {"freeze_fingerprint": "3ec87f58975dc9fce3432e51e6a5ee4e4e56d83821e46db966f85fa4e027c907", "state": "sufficient", "outcome": "sufficient", "outcome_wording": "sufficient in the sources searched", "verdict": "supported", "verdict_wording": "supported under the stated model, in the sources searched", "exploratory": false, "evidence_level": 6, "evidence_level_wording": "sufficient with a verdict", "label": null}
```

Against the previous round: k, SE and p differ only in the last one or two digits (stable centring); everything else is identical; every result still rounds to its approved figure.

## 4. Mutation checks of the re-check fixes

### `mutations_recheck.sh`

```bash
#!/bin/bash
M=/tmp/claude-1000/-workspaces-hypocurate/d40b08e7-9c83-4b0a-8b2e-aa110db4b20f/scratchpad/mutate.sh
R="/workspaces/hypocurate/tests/test_recheck_fixes.py"
$M r01_no_effective_check pipeline/statistics.py '        if not self.effective_papers >= MIN_EFFECTIVE_PAPERS:
            return "evidence_concentrated"' '' $R
$M r02_filter_scores_again pipeline/statistics.py '    scores = np.bincount(d.group, xd * e, d.n_groups)
    variance' '    scores = np.bincount(d.group, xd * e, d.n_groups)[d.group_informative]
    variance' $R /workspaces/hypocurate/tests/test_informative_inference.py
$M r03_sim_filter_scores pipeline/calibration.py '    scores = (e * xd[None, :]) @ groups' '    scores = ((e * xd[None, :]) @ groups)[:, d.group_informative]' $R
$M r04_adjacent_gaps pipeline/statistics.py '    return max(values) - min(values) > RELATIVE_ZERO * max(abs(v) for v in values)' '    o = sorted(values); return any(b - a > RELATIVE_ZERO * max(abs(v) for v in values) for a, b in zip(o, o[1:]))' $R
$M r05_no_residual_floor pipeline/statistics.py '    if bool(residuals_numerically_zero(e, yd, d.y)):' '    if False:' $R
$M r06_scatter_floor_relative_only pipeline/calibration.py '    floor = max((RELATIVE_ZERO ** 2) * tss_within, n * (ARITHMETIC_ZERO * float(np.abs(d.y).max())) ** 2)' '    floor = (RELATIVE_ZERO ** 2) * tss_within' $R
$M r07_no_arithmetic_term pipeline/statistics.py '    floor = np.maximum(RELATIVE_ZERO * rms(centred), ARITHMETIC_ZERO * np.max(np.abs(raw), axis=-1))' '    floor = RELATIVE_ZERO * rms(centred)' $R
$M r08_fixed_five_percent pipeline/analysis.py '        entry["detection_note"] = st.detection_note(alpha)' '        entry["detection_note"] = st.detection_note(0.05).replace("α = 0.05", "5%")' $R
$M r09_db_check2_without_spread db/migrations/versions/0004_statistics_results.py '("check2_consistent", f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW} AND {SPREAD})")' '("check2_consistent", f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW})")' /workspaces/hypocurate/tests/test_analysis_stage.py
$M r10_sim_no_residual_floor pipeline/calibration.py '                 & ~residuals_numerically_zero(e, yd, outcomes))' '                 )' /workspaces/hypocurate/tests/test_statistics_boundaries.py $R
```

### Output

```
[r01_no_effective_check] >       assert out["decision"]["verdict"] is None and pooled["p_value"] is None and pooled["std_error"] is None
[r01_no_effective_check] >       assert out["decision"]["verdict"] is None and pooled["p_value"] is None and pooled["std_error"] is None
[r01_no_effective_check] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_the_nudged_design_gives_no_verdict[fixed_minimum]
[r01_no_effective_check] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_the_nudged_design_gives_no_verdict[use_available]
[r01_no_effective_check] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_every_simulated_fit_requires_two_effective_papers
[r01_no_effective_check] 3 failed, 10 passed in 3.60s
[r02_filter_scores_again] >       assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-6)
[r02_filter_scores_again] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_the_counterexample_keeps_every_papers_score
[r02_filter_scores_again] 1 failed, 19 passed in 4.30s
[r03_sim_filter_scores] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_simulated_fits_keep_every_papers_score
[r03_sim_filter_scores] 1 failed, 12 passed in 3.49s
[r04_adjacent_gaps] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_adding_a_record_never_removes_an_alloys_contrast
[r04_adjacent_gaps] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_an_alloy_keeps_its_contrast_in_a_design_when_a_middle_record_is_added
[r04_adjacent_gaps] 2 failed, 11 passed in 3.28s
[r05_no_residual_floor] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference
[r05_no_residual_floor] 1 failed, 12 passed in 3.48s
[r06_scatter_floor_relative_only] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference
[r06_scatter_floor_relative_only] 1 failed, 12 passed in 3.47s
[r07_no_arithmetic_term] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference
[r07_no_arithmetic_term] 1 failed, 12 passed in 3.72s
[r08_fixed_five_percent] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_the_detection_note_states_the_plans_threshold
[r08_fixed_five_percent] 1 failed, 12 passed in 3.53s
[r09_db_check2_without_spread] FAILED ../../../../../workspaces/hypocurate/tests/test_analysis_stage.py::test_the_database_requires_two_effective_papers_for_check_2
[r09_db_check2_without_spread] 1 failed, 35 passed in 26.32s
[r10_sim_no_residual_floor] 32 passed in 3.42s

# r10 survived the first run (the simulation test used exact fits without baselines, which the SE check already catches); after adding test_simulated_perfect_fits_on_large_baselines_are_never_significant:
[r10_sim_no_residual_floor] FAILED ../../../../../workspaces/hypocurate/tests/test_recheck_fixes.py::test_simulated_perfect_fits_on_large_baselines_are_never_significant
[r10_sim_no_residual_floor] 1 failed, 13 passed in 3.55s
```

## 5. Suite output

```
Local (Codespace), on 1320840:
1155 passed in 330.04s (0:05:30)
```

## 6. Questions for the second re-check

1. Are the re-check items closed: concentrated evidence (the nudged design), every score in the covariance (the counterexample, real and simulated), distinctness from the full range, and the numerical zero at the data's scale?
2. Is the effective number of papers implemented as the owner defined it, applied in every simulated fit, and stored with every result?
3. Is the decimal-precision sandwich a fair independent check, and is it right that statsmodels cannot serve on the counterexample?
4. Does the arithmetic floor (1e-12 of the largest outcome magnitude) stay an arithmetic safeguard, never a scientific minimum?
5. Is any claim stronger than the code supports?
