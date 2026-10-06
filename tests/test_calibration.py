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
    assert d.counts_allow_inference
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
        return {"status": "computed", "reason": None, "assumptions": {"scatter": 1.0, "shift": 1.0}, "seed": 1,
                "n_simulations": 1,
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
