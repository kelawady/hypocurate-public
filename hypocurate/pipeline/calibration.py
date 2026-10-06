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
  3. σe² = RSS_F / (N - r_F). Not estimable when N <= r_F, or when RSS_F is at most the numerical
     zero of the outcome's spread within alloys (RSS_F <= RELATIVE_ZERO² × Σ ỹ²): a perfect fit,
     whose residue is rounding, gives no scatter to simulate (review finding 4).
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
method, labelled "estimated power under the stated assumptions". It uses no outcome value. The
detection rate is reported both ways (review, smaller point), each beside its false-positive share:
fixed (shown also below the minimums) and estimated (withheld below the minimums). Both are detection
rates of the nominal 5% test, not power for a test shown to keep false positives at 5%.

**What the intervals cover**: Monte Carlo uncertainty only. For the estimated method they do not
cover uncertainty in the estimated scatter and shift; it is a diagnostic conditional on the estimate,
not independent validation (stated with every result, `interval_note`).

**Each simulated fit gets the real fit's validity checks**: a simulated standard error that is not
finite or not above the numerical zero gives no inference and is not counted as significant.
"""
from __future__ import annotations

import hashlib
import math
from typing import Mapping

import numpy as np
from scipy import stats

from hypocurate.pipeline.statistics import RELATIVE_ZERO, Design, demeaned, small_sample_factor

CONFIDENCE = 0.95
FLAG_WORDING = {
    "over_confident": "the method is over-confident on this data structure under the stated assumptions",
    "under_confident": "the method is under-confident on this data structure under the stated assumptions",
    "none": None,
}
# Relative tolerances of the estimator's linear algebra (numerical zero).
TRACE_TOLERANCE = 1e-9
# What the intervals cover (review, smaller point): stated with every calibration.
INTERVAL_NOTE_FIXED = "The intervals cover Monte Carlo (simulation) uncertainty only."
INTERVAL_NOTE_ESTIMATED = ("The intervals cover Monte Carlo (simulation) uncertainty only, not uncertainty in the "
                           "estimated scatter and shift. This is a diagnostic conditional on the estimated noise "
                           "(a shift truncated at zero biases it), not independent validation.")


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
    the same estimator, standard error, correction, validity checks and one-sided t test as
    `statistics.fit`. A simulated fit whose standard error is not finite or not above the numerical
    zero gives no inference, so it is never significant (review finding 1)."""
    if not d.counts_allow_inference:
        return 0
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
        se = np.sqrt(variance)
        scale = np.sqrt((yd ** 2).sum(axis=1) / sxx)
        valid = np.isfinite(se) & np.isfinite(k) & (se > RELATIVE_ZERO * scale)
        t = np.where(valid, k / np.where(valid, se, 1.0), 0.0)
    p = stats.t.sf(t, d.n_groups - 1)
    return int(np.count_nonzero(valid & (p < alpha)))


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
    within = demeaned(d.y, d.alloy, d.n_alloys)
    tss_within = float(within @ within)
    out = {"estimation": "henderson_iii", "rss_reduced": rss_r, "rank_reduced": rank_r, "rss_full": rss_f,
           "rank_full": rank_f, "trace": trace, "n_records": n, "tss_within_alloys": tss_within}
    # Review finding 4: a residual at most the numerical zero of the outcome's within-alloy spread is
    # rounding residue (a perfect fit), not scatter.
    if n <= rank_f or not (math.isfinite(rss_f) and rss_f > (RELATIVE_ZERO ** 2) * tss_within):
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
                   "design": "fixed: the fit's records, alloys, groups and grain sizes",
                   "interval_note": INTERVAL_NOTE_FIXED if method == "fixed" else INTERVAL_NOTE_ESTIMATED}
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
