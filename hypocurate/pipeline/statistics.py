"""The supported statistical model, its two validity checks, data sufficiency and the verdict
(PRD 5.7, 5.8; CLAUDE.md rules 5 to 7; build step 7). Pure functions: no database, no model.

**The one model** (CLAUDE.md rule 6; register 'model_form'): yield strength = a baseline per
alloy + k × (grain size in µm)^-1/2. Ordinary least squares with one intercept per alloy and one
shared coefficient k, computed by removing each alloy's mean from the predictor and the outcome
(the same estimate as fitting the alloy intercepts; Frisch-Waugh-Lovell). Its standard error is
cluster-robust, grouped by each source's grouping unit, with the small-sample correction
G/(G-1) × (N-1)/(N-K), K = alloys + 1, G the informative groups (statsmodels' formula when every
group is informative; register 'cluster_robust_se'). The test is one-sided, k > 0, against a t
distribution with G - 1 degrees of freedom, G the informative groups, at the plan's threshold;
"supported" exactly when p < alpha (register 'p_threshold_comparison').

**Which records a fit uses** (owner, 2026-10-05, decision 7): only alloys with at least
`MODEL_MIN_GRAIN_SIZES` distinct grain sizes among the analysis's own records, distinct after the
transformation by more than the numerical zero (review finding 3: 9.0 and 9.000000000000002 µm give
the same d^-1/2). This is the model's own condition, applied to grain sizes only; the frozen set is
not changed and the others are reported as "not used in this fit". **The minimums are counted on
the records the fit uses** (owner, 2026-10-05).

**Informative papers** (owner, 2026-10-06; register 'informative_groups'): a group is informative
when at least one of its records differs from its alloy's average transformed grain size by more
than the numerical zero, so that the group helps estimate the slope. Uninformative groups stay in
the fit and are listed, but are not counted for the paper minimum, for validity check 2's group count, for the standard
error's small-sample factor or for the t distribution's degrees of freedom (owner, 2026-10-06;
register 'informative_groups_in_inference'; CLAUDE.md rule 6). The clustered covariance sums
**every** group's score (re-check finding 2: a small contrast times a large residual can matter).

**Effective number of papers** (owner, 2026-10-06; register 'effective_papers'): with I_g a group's
sum of squared within-alloy deviations of the transformed grain size, (Σ I_g)² / Σ I_g², and the
largest single group's share max I_g / Σ I_g, stored with every result. Validity check 2 needs at
least `MIN_EFFECTIVE_PAPERS` (2); below it the coefficient alone, reason 'evidence_concentrated'.
It measures how concentrated the within-alloy predictor contrast is; it is not an estimate of
independent sample size, and passing the floor does not establish reliable inference.

**The two validity checks** can never be waived (CLAUDE.md rule 5): (1) a coefficient can be fitted
when at least one alloy has two distinct grain sizes; (2) inference is valid with at least 1
residual degree of freedom (records - alloys - 1), at least 2 informative groups, and a clustered
standard error that is finite and above the scale-aware numerical zero (review finding 1). Check 1
only: the coefficient alone, no uncertainty, no p-value, no verdict, with the reason.

**Numerical zero** (`RELATIVE_ZERO`, `ARITHMETIC_ZERO`, register 'numerical_zero'): an arithmetic
safeguard, not a scientific minimum. A predictor range counts as zero when it is at most
`RELATIVE_ZERO` (1e-10) times the largest transformed grain size. Residuals count as zero (a perfect
fit, so no uncertainty and no scatter can be estimated) when their root mean square is at most the
larger of `RELATIVE_ZERO` times the outcome's spread within alloys and `ARITHMETIC_ZERO` (1e-12) times
the largest outcome magnitude (re-check finding 5: rounding comes from the baselines too). A standard
error must also exceed `RELATIVE_ZERO` × sqrt(Σ ỹ² / Σ x̃²). Within-alloy centring subtracts each
alloy's first value before taking the mean (stable centring). Rounding residue is about 1e-16 of these
scales; real measurement scatter is many orders above them.

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
# A quantity at most this fraction of its natural scale is numerically zero (register 'numerical_zero').
RELATIVE_ZERO = 1e-10
# Residuals at most this fraction of the largest outcome magnitude are rounding (register 'numerical_zero').
ARITHMETIC_ZERO = 1e-12
# Validity check 2: the effective number of papers at least this (owner, 2026-10-06; register 'effective_papers').
MIN_EFFECTIVE_PAPERS = 2.0
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
# Stored with every p-value (owner, at the merge decision, 2026-10-06; register 'p_value_reporting'). The
# informative paper count, the effective number of papers, the largest paper's share and the t degrees
# of freedom are stored with it, to be shown together. The effective number is a concentration
# diagnostic, never a number of independent papers.
P_VALUE_DESCRIPTION = "approximate, nominal, one-sided cluster-robust p-value under the locked method"
def detection_note(alpha: float) -> str:
    """The detection note with the plan's locked threshold (re-check, smaller point)."""
    return (f"detection rates of the nominal α = {alpha:g} test (the plan's locked threshold) under the stated "
            f"assumptions (fixed and estimated noise), with its false-positive shares under the same assumptions; "
            f"not power for a test shown to keep false positives at α = {alpha:g}")

# Why validity check 2 failed (stored with the result; migration 0004).
INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "evidence_concentrated", "uncertainty_not_estimable")

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
# Why a per-source result is "not enough data" (review, smaller point): zero direction is not missing inference.
LABEL_REASONS = ("no_p_value", "pooled_without_decision", "zero_coefficient")


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
    n_groups_informative: int = 0
    uninformative_groups: tuple = ()
    group_informative: np.ndarray = None  # per group index: does the group count (informative)?
    effective_papers: float = 0.0  # (Σ I_g)² / Σ I_g²; 0 without a coefficient
    largest_paper_share: float | None = None  # max I_g / Σ I_g

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
    def counts_allow_inference(self) -> bool:
        """Validity check 2's structure: a residual degree of freedom, two informative groups and an
        effective number of papers of at least two. The standard error must also be estimable (`fit`)."""
        return self.counts_reason is None

    @property
    def counts_reason(self) -> str | None:
        if not self.coefficient_fitted:
            return "coefficient_not_fitted"
        if not (self.resid_df >= 1 and self.n_groups_informative >= 2):
            return "insufficient_groups"
        if not self.effective_papers >= MIN_EFFECTIVE_PAPERS:
            return "evidence_concentrated"
        return None


def design(observations: Iterable[Observation], transformation: str) -> Design:
    """The fit's records: alloys with at least two distinct grain sizes among these records."""
    obs = sorted(observations, key=lambda o: o.identity)
    if len({o.identity for o in obs}) != len(obs):
        raise StatisticsError("two records share one stable identity")
    transform = TRANSFORMATIONS[transformation]
    values: dict[str, list] = {}
    for o in obs:
        if not (math.isfinite(o.grain_size) and o.grain_size > 0 and math.isfinite(o.outcome)):
            raise StatisticsError("a record in a frozen set has no finite positive grain size or finite outcome")
        values.setdefault(o.alloy, []).append(transform(o.grain_size))
    used_alloys = sorted(a for a, v in values.items() if has_contrast(v))  # MODEL_MIN_GRAIN_SIZES = 2
    keep = set(used_alloys)
    used = [o for o in obs if o.alloy in keep]
    groups = sorted({o.group for o in used})
    alloy_index = {a: i for i, a in enumerate(used_alloys)}
    group_index = {g: i for i, g in enumerate(groups)}
    x = np.array([transform(o.grain_size) for o in used], dtype=float)
    alloy = np.array([alloy_index[o.alloy] for o in used], dtype=int)
    informative: set = set()
    effective, largest = 0.0, None
    if used:
        deviation, info = _information(x, alloy, len(used_alloys),
                                       np.array([group_index[o.group] for o in used]), len(groups))
        contrast = np.abs(deviation)
        informative = {o.group for o, c in zip(used, contrast) if c > RELATIVE_ZERO * float(np.abs(x).max())}
        total = float(info.sum())
        if total > 0:
            effective, largest = total ** 2 / float(info @ info), float(info.max()) / total
    return Design(
        x=x, y=np.array([o.outcome for o in used], dtype=float), alloy=alloy,
        group=np.array([group_index[o.group] for o in used], dtype=int),
        n_alloys=len(used_alloys), n_groups=len(groups), n_records_in_set=len(obs),
        n_alloys_not_used=len(values) - len(used_alloys), n_groups_informative=len(informative),
        uninformative_groups=tuple(g for g in groups if g not in informative),
        group_informative=np.array([g in informative for g in groups], dtype=bool),
        effective_papers=effective, largest_paper_share=largest)


def _information(x: np.ndarray, alloy: np.ndarray, n_alloys: int, group: np.ndarray, n_groups: int) -> tuple:
    """The within-alloy deviations of the transformed grain size, and I_g per group index: the
    group's sum of squared deviations (register 'effective_papers'). No outcome is used."""
    deviation = demeaned(x, alloy, n_alloys)
    return deviation, np.bincount(group, deviation ** 2, n_groups)


def slope_information(items: Iterable[tuple], transformation: str) -> dict[str, float]:
    """{group: I_g} for records given as (stable identity, alloy, group, grain size in µm): the same
    computation as `design` (identity order, alloys with two or more distinct transformed grain sizes,
    stable centring), from grain sizes, alloys and groups only, never an outcome. Used by `design` for
    the effective number of papers and by Inclusion to choose the paper of the sensitivity set
    'without_most_influential_paper' (step 7b; register 'most_influential_paper_set')."""
    rows = sorted(items, key=lambda t: t[0])
    transform = TRANSFORMATIONS[transformation]
    values: dict[str, list] = {}
    for _, alloy, _, d in rows:
        if not (math.isfinite(d) and d > 0):
            raise StatisticsError("a record has no finite positive grain size")
        values.setdefault(alloy, []).append(transform(d))
    used_alloys = sorted(a for a, v in values.items() if has_contrast(v))
    keep = set(used_alloys)
    used = [t for t in rows if t[1] in keep]
    groups = sorted({t[2] for t in used})
    if not used:
        return {}
    alloy_index = {a: i for i, a in enumerate(used_alloys)}
    group_index = {g: i for i, g in enumerate(groups)}
    _, info = _information(np.array([transform(t[3]) for t in used], dtype=float),
                           np.array([alloy_index[t[1]] for t in used], dtype=int), len(used_alloys),
                           np.array([group_index[t[2]] for t in used], dtype=int), len(groups))
    return {g: float(info[i]) for g, i in group_index.items()}


def has_contrast(values: list) -> bool:
    """At least two distinct transformed grain sizes: the full range exceeds the numerical zero
    (relative to the largest value). Adding a value can never remove a contrast (re-check finding 4)."""
    return max(values) - min(values) > RELATIVE_ZERO * max(abs(v) for v in values)


def demeaned(values: np.ndarray, alloy: np.ndarray, n_alloys: int) -> np.ndarray:
    """Each value minus its alloy's mean (works on the last axis, for one or many outcome rows).
    Stable centring (re-check finding 5): each alloy's first value is subtracted before the mean is
    taken, so large baselines do not swamp the within-alloy differences."""
    counts = np.bincount(alloy, minlength=n_alloys).astype(float)
    first = np.full(n_alloys, -1)
    for i in range(alloy.size - 1, -1, -1):
        first[alloy[i]] = i
    if values.ndim == 1:
        shifted = values - values[first][alloy]
        return shifted - (np.bincount(alloy, shifted, n_alloys) / counts)[alloy]
    shifted = values - values[:, first][:, alloy]
    indicator = np.zeros((alloy.size, n_alloys))
    indicator[np.arange(alloy.size), alloy] = 1.0
    return shifted - ((shifted @ indicator) / counts)[:, alloy]


def residuals_numerically_zero(residuals: np.ndarray, centred: np.ndarray, raw: np.ndarray) -> np.ndarray:
    """Per row (last axis): are the residuals rounding residue? Their root mean square at most the
    larger of RELATIVE_ZERO × the centred outcome's root mean square and ARITHMETIC_ZERO × the largest
    raw outcome magnitude (register 'numerical_zero')."""
    rms = lambda v: np.sqrt(np.mean(v ** 2, axis=-1))  # noqa: E731
    floor = np.maximum(RELATIVE_ZERO * rms(centred), ARITHMETIC_ZERO * np.max(np.abs(raw), axis=-1))
    return rms(residuals) <= floor


def small_sample_factor(n: int, n_alloys: int, n_groups: int) -> float:
    """G/(G-1) × (N-1)/(N-K), K = alloys + 1, G the informative groups (register 'cluster_robust_se')."""
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
    reason: str | None = None  # why there is no inference (INFERENCE_REASONS), or None


def fit(d: Design) -> Fit | None:
    """The coefficient (check 1), and its standard error and one-sided p-value (check 2): only when
    the counts allow it and the standard error is finite and above the numerical zero."""
    if not d.coefficient_fitted:
        return None
    xd = demeaned(d.x, d.alloy, d.n_alloys)
    yd = demeaned(d.y, d.alloy, d.n_alloys)
    sxx = float(xd @ xd)
    if not (math.isfinite(sxx) and sxx > 0):  # excluded by the alloy rule; never divide by it
        raise StatisticsError("the transformed grain sizes have no variation within any alloy")
    k = float(xd @ yd) / sxx
    if not math.isfinite(k):
        raise StatisticsError("the coefficient is not finite")
    if not d.counts_allow_inference:
        return Fit(k, None, None, None, None, d.counts_reason)
    e = yd - k * xd
    if bool(residuals_numerically_zero(e, yd, d.y)):
        return Fit(k, None, None, None, None, "uncertainty_not_estimable")
    # Every group's score in the sum (re-check finding 2); informative groups in the factor and the df.
    scores = np.bincount(d.group, xd * e, d.n_groups)
    variance = float(scores @ scores) / sxx ** 2 * small_sample_factor(d.n, d.n_alloys, d.n_groups_informative)
    se = math.sqrt(variance) if math.isfinite(variance) and variance >= 0 else math.nan
    if not (math.isfinite(se) and se > RELATIVE_ZERO * math.sqrt(float(yd @ yd) / sxx)):
        return Fit(k, None, None, None, None, "uncertainty_not_estimable")
    t = k / se
    df = d.n_groups_informative - 1
    return Fit(k, se, t, df, one_sided_p(t, df))


def minimums(d: Design, sufficiency: Mapping) -> dict:
    """Each count of the fit against its minimum (PRD 5.8)."""
    counts = {"records": d.n, "alloys": d.n_alloys, "groups": d.n_groups_informative, "resid_df": d.resid_df}
    keys = {"records": "min_records", "alloys": "min_alloys", "groups": "min_groups", "resid_df": "min_resid_df"}
    return {name: {"count": counts[name], "minimum": sufficiency[keys[name]],
                   "met": counts[name] >= sufficiency[keys[name]]} for name in counts}


def significant(p_value: float | None, alpha: float) -> bool | None:
    return None if p_value is None else p_value < alpha


def label_reason(per_source: Mapping, pooled: Mapping) -> str | None:
    """Why a per-source result is "not enough data", or None when it can be compared."""
    if per_source.get("p_value") is None:
        return "no_p_value"
    if pooled.get("p_value") is None:
        return "pooled_without_decision"
    if per_source["estimate"] == 0 or pooled["estimate"] == 0:
        return "zero_coefficient"
    return None


def label(per_source: Mapping, pooled: Mapping, alpha: float) -> str:
    """The four per-source labels (owner, 2026-10-05): from the locked test and the sign only."""
    if label_reason(per_source, pooled):
        return "not_enough_data"
    a, b = per_source["estimate"], pooled["estimate"]
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
    counts_reason = d.counts_reason
    entry = {
        "counts": {"n_records_in_set": d.n_records_in_set, "n_records": d.n,
                   "n_records_not_used": d.n_records_in_set - d.n, "n_alloys": d.n_alloys,
                   "n_alloys_not_used": d.n_alloys_not_used, "n_groups": d.n_groups,
                   "n_groups_informative": d.n_groups_informative, "resid_df": d.resid_df,
                   "effective_papers": d.effective_papers, "largest_paper_share": d.largest_paper_share},
        "uninformative_groups": list(d.uninformative_groups),
        # Withheld: judged on the counts only (no outcome is used, so no standard error is computed).
        "checks": {"coefficient_fitted": d.coefficient_fitted, "inference_valid": d.counts_allow_inference},
        "inference_reason": counts_reason,
        "minimums": m, "minimums_met": all(v["met"] for v in m.values()), "withheld": withheld,
        "estimate": None, "std_error": None, "t": None, "df": None, "p_value": None, "p_value_description": None,
        "alpha": plan["model"]["alpha"], "significant": None,
    }
    if withheld:
        return entry
    f = fit(d)
    if f is not None:
        entry.update(estimate=f.estimate, std_error=f.std_error, t=f.t, df=f.df, p_value=f.p_value,
                     significant=significant(f.p_value, plan["model"]["alpha"]), inference_reason=f.reason,
                     p_value_description=P_VALUE_DESCRIPTION if f.p_value is not None else None)
        entry["checks"]["inference_valid"] = f.reason is None
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
