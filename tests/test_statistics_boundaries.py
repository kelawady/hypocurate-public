"""Step 7 review fixes (ChatGPT, 2026-10-06): the boundaries of validity check 2, numerical rank and
numerical zero, and the smaller points. Pure functions, no database.

Owner's decision (2026-10-06): the minimum of independent papers, and validity check 2's "at least
two groups", count only informative papers: papers whose records help estimate the slope (non-zero
grain-size variation after removing each alloy's average). Uninformative papers are kept and listed
but not counted. Inference is valid only if the clustered standard error is finite and above a
scale-aware numerical zero; otherwise the coefficient alone is reported. The simulations apply the
same checks.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

import generator as g
from hypocurate.pipeline import analysis
from hypocurate.pipeline import calibration as cal
from hypocurate.pipeline import statistics as st


def frozen(rows, name="boundary"):
    """rows: (alloy index, paper, grain size, outcome) as frozen analysis data."""
    records = [{"id": i + 1, "source": "mpea", "version_fingerprint": f"gen-{name}", "origin": f"b:{name}:{i}",
                "item_index": i, "composition": {"Qa": float(10 + a), "Qb": float(90 - a)}, "paper": paper,
                "batch": None, "grain_size": float(d), "outcome": float(y)} for i, (a, paper, d, y) in enumerate(rows)]
    return {"freeze_fingerprint": "b" * 64, "outcome_field": "yield_strength",
            "sets": {"primary": [r["id"] for r in records]}, "records": records}


def reviewers_design():
    """ChatGPT's case: five alloys, six records each; within each alloy grain sizes [16, 16/9, 4, 4, 4,
    4]; the first two records of every alloy from one paper, the other twenty spread over ten papers;
    outcomes [400, 600, 470, 510, 500, 490] plus an alloy baseline."""
    sizes = [16.0, 16.0 / 9.0, 4.0, 4.0, 4.0, 4.0]
    ys = [400.0, 600.0, 470.0, 510.0, 500.0, 490.0]
    rows, n = [], 0
    for a in range(5):
        for j in range(6):
            paper = "paper-00" if j < 2 else f"paper-{1 + n % 10:02d}"
            if j >= 2:
                n += 1
            rows.append((a, paper, sizes[j], ys[j] + 100.0 * a))
    return frozen(rows, "reviewer")


# --- finding 1: informative papers and an estimable uncertainty -----------------------------------

@pytest.mark.parametrize("option", ["fixed_minimum", "use_available"])
def test_the_reviewers_design_never_gives_a_verdict(option):
    out = analysis.analyse(g.plan(option, n_simulations=200), reviewers_design())
    pooled = out["analyses"][0]
    assert out["decision"]["verdict"] is None and out["decision"]["outcome"] == "insufficient"
    assert pooled["counts"]["n_groups"] == 11 and pooled["counts"]["n_groups_informative"] == 1
    assert pooled["uninformative_groups"] == [f"paper:paper-{i:02d}" for i in range(1, 11)]
    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "insufficient_groups"
    assert pooled["std_error"] is None and pooled["p_value"] is None
    assert pooled["minimums"]["groups"]["count"] == 1
    if option == "fixed_minimum":  # the paper minimum counts informative papers only: withheld
        assert out["decision"]["evidence_level"] == 3 and pooled["estimate"] is None
    else:
        assert out["decision"]["evidence_level"] == 4 and math.isclose(pooled["estimate"], 400.0, rel_tol=1e-12)
    assert {c["status"] for c in pooled["calibration"].values()} == {"unavailable"}


def test_a_paper_is_informative_when_its_records_vary_after_removing_the_alloy_average():
    obs = [st.Observation("a", "A", "p1", 1.0, 1.0), st.Observation("b", "A", "p1", 4.0, 2.0),  # p1 varies
           st.Observation("c", "A", "p2", 9.0, 3.0),                                          # differs from mean
           st.Observation("d", "B", "p3", 4.0, 1.0), st.Observation("e", "B", "p3", 4.0, 1.5),
           st.Observation("f", "B", "p4", 1.0, 2.0), st.Observation("g", "B", "p4", 9.0, 2.5)]
    d = st.design(obs, "inverse_square_root")
    # Alloy B: x = 0.5, 0.5, 1, 1/3; mean 7/12: p3's records are 1/12 away from it, so p3 is informative.
    assert (d.n_groups, d.n_groups_informative, d.uninformative_groups) == (4, 4, ())
    obs2 = obs[:3] + [st.Observation("d", "B", "p3", 4.0, 1.0), st.Observation("f", "B", "p4", 1.0, 2.0),
                      st.Observation("g", "B", "p4", 16.0 / 9.0, 2.5)]
    d2 = st.design(obs2, "inverse_square_root")  # B: x = 0.5, 1, 0.75; mean 0.75: p4's mean-valued record...
    assert d2.n_groups_informative == 4  # ...but p4 also holds x = 1, so it varies; p3 (x = 0.5) differs too
    obs3 = [st.Observation("a", "A", "p1", 1.0, 1.0), st.Observation("b", "A", "p1", 9.0, 2.0),
            st.Observation("c", "A", "p2", 1.0 / (2.0 / 3.0) ** 2, 3.0)]  # x = 2/3 = the alloy mean
    d3 = st.design(obs3, "inverse_square_root")
    assert (d3.n_groups, d3.n_groups_informative, d3.uninformative_groups) == (2, 1, ("p2",))


def test_an_exact_fit_has_no_estimable_uncertainty_and_gives_the_coefficient_only():
    """Two informative papers, residuals zero up to rounding: the standard error is below the
    scale-aware numerical zero, so no p-value and no verdict."""
    rows = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5)
            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    out = analysis.analyse(g.plan("use_available", n_simulations=100), frozen(rows, "exact"))
    pooled = out["analyses"][0]
    assert pooled["counts"]["n_groups_informative"] >= 2 and pooled["counts"]["resid_df"] >= 1
    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "uncertainty_not_estimable"
    assert math.isclose(pooled["estimate"], 250.0, rel_tol=1e-9) and pooled["std_error"] is None
    assert out["decision"]["verdict"] is None and out["decision"]["evidence_level"] == 4
    assert {c["reason"] for c in pooled["calibration"].values()} == {"uncertainty_not_estimable"}


def test_small_real_noise_keeps_the_uncertainty_estimable():
    """The numerical zero is relative and far below any real scatter: noise of 0.001 MPa on values of
    hundreds of MPa still gives a standard error and a test."""
    rng = np.random.default_rng(5)
    rows = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5 + rng.normal(0, 1e-3))
            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    pooled = analysis.analyse(g.plan("use_available", n_simulations=100), frozen(rows, "noise"))["analyses"][0]
    assert pooled["checks"]["inference_valid"] is True and pooled["inference_reason"] is None
    assert 0 < pooled["std_error"] < 1 and pooled["p_value"] < 1e-6


def test_the_simulations_apply_the_same_check_to_each_simulated_fit():
    """A simulated outcome row that fits exactly is never counted as significant."""
    rows = [(a, f"p{j % 4}", d, 1.0) for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
    exact = np.vstack([300.0 + 250.0 * d.x, 100.0 + 0.0 * d.x])
    assert cal.significant_count(d, exact, 0.05) == 0


def test_the_uncertainty_check_is_scale_aware():
    """The same data in other units (×1e6 or ×1e-6) give the same validity decision."""
    rng = np.random.default_rng(9)
    base = [(a, f"p{j % 4}", d, 300.0 + 40 * a + 250.0 * d ** -0.5 + rng.normal(0, 5.0))
            for a in range(4) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    for scale in (1e-6, 1.0, 1e6):
        rows = [(a, p, d, y * scale) for a, p, d, y in base]
        pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, f"s{scale}"))["analyses"][0]
        assert pooled["checks"]["inference_valid"] is True, scale


# --- finding 3: numerical rank of the transformed design ------------------------------------------

def test_grain_sizes_equal_after_transformation_never_raise():
    """9.0 and 9.000000000000002 transform to the same value: the alloy has no numerical variation,
    so no coefficient is fitted, and nothing raises."""
    assert 9.0 ** -0.5 == 9.000000000000002 ** -0.5
    rows = [(0, "p1", 9.0, 400.0), (0, "p2", 9.000000000000002, 410.0), (0, "p1", 9.0, 405.0),
            (0, "p2", 9.000000000000002, 395.0)]
    out = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, "rank"))
    pooled = out["analyses"][0]
    assert pooled["checks"] == {"coefficient_fitted": False, "inference_valid": False}
    assert pooled["estimate"] is None and pooled["inference_reason"] == "coefficient_not_fitted"
    assert out["decision"]["evidence_level"] == 2


def test_nearly_equal_transformed_grain_sizes_are_not_distinct():
    rows = [(0, "p1", 9.0, 400.0), (0, "p2", 9.0 * (1 + 1e-13), 410.0), (1, "p1", 1.0, 500.0),
            (1, "p2", 4.0, 420.0), (1, "p3", 9.0, 401.0)]
    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
    assert d.n_alloys == 1 and d.n_alloys_not_used == 1


# --- finding 4: a perfect fit has no estimable scatter --------------------------------------------

def test_an_exact_fit_has_no_estimable_scatter():
    rows = [(a, f"p{(j + a) % 5}", d, 300.0 + 40 * a + 100.0 * d ** -0.5)
            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
    est = cal.henderson_iii(d)
    assert est["rss_full"] < 1e-15 and est["reason"] == "scatter_not_estimable"


def test_small_real_noise_gives_an_estimable_scatter():
    rng = np.random.default_rng(3)
    rows = [(a, f"p{(j + a) % 5}", d, 300.0 + 40 * a + 100.0 * d ** -0.5 + rng.normal(0, 0.01))
            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]
    d = st.design(analysis.observations(frozen(rows)["records"], g.plan(), "primary"), "inverse_square_root")
    est = cal.henderson_iii(d)
    assert est["reason"] in (None, "shift_not_estimable") and 0.003 < math.sqrt(est["scatter_squared"]) < 0.03


# --- smaller points ----------------------------------------------------------------------------------

def test_every_estimated_calibration_states_what_its_intervals_cover():
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
    est = cal.calibrate(d, g.plan()["calibration"], 0.05, "f" * 64, "pooled", "estimated")
    note = est["assumptions"]["interval_note"]
    assert "Monte Carlo" in note and "not uncertainty in the estimated scatter and shift" in note
    assert "diagnostic" in note and "not independent validation" in note
    fixed = cal.calibrate(d, g.plan()["calibration"], 0.05, "f" * 64, "pooled", "fixed")
    assert "Monte Carlo" in fixed["assumptions"]["interval_note"]


def test_detection_rates_are_reported_both_ways_with_the_false_positive_shares():
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    pooled = analysis.analyse(g.plan("fixed_minimum", n_simulations=300), data)["analyses"][0]
    rates = pooled["detection"]
    for method in ("fixed", "estimated"):
        c = pooled["calibration"][method]
        assert rates[method] == {"detection": c["effect"]["share"], "detection_ci": [c["effect"]["ci_low"],
                                                                                    c["effect"]["ci_high"]],
                                 "false_positive": c["null"]["share"],
                                 "false_positive_ci": [c["null"]["ci_low"], c["null"]["ci_high"]],
                                 "scatter": c["assumptions"]["scatter"], "shift": c["assumptions"]["shift"]}
    assert pooled["estimated_power"] == rates["fixed"]["detection"]
    assert pooled["estimated_power_estimated_noise"] == rates["estimated"]["detection"]
    assert "nominal" in pooled["detection_note"] and "not power" in pooled["detection_note"]


def test_below_the_minimums_the_fixed_detection_rate_is_shown_and_the_estimated_one_withheld():
    data = g.frozen_data(g.SPECS["small_but_valid"])
    pooled = analysis.analyse(g.plan("fixed_minimum", n_simulations=300), data)["analyses"][0]
    assert pooled["withheld"]
    assert pooled["detection"]["fixed"]["detection"] == pooled["estimated_power"] is not None
    assert pooled["detection"]["estimated"] == {"withheld": True}
    assert pooled["estimated_power_estimated_noise"] is None


@pytest.mark.parametrize("per_source, pooled, reason", [
    ({"estimate": 0.0, "p_value": 0.5}, {"estimate": 424.0, "p_value": 1e-6}, "zero_coefficient"),
    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 0.0, "p_value": 0.5}, "zero_coefficient"),
    ({"estimate": 1173.0, "p_value": None}, {"estimate": 424.0, "p_value": 1e-6}, "no_p_value"),
    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 424.0, "p_value": None}, "pooled_without_decision"),
    ({"estimate": 400.0, "p_value": 1e-6}, {"estimate": 424.0, "p_value": 1e-6}, None),
])
def test_a_zero_coefficient_has_its_own_reason(per_source, pooled, reason):
    """'Not enough data' keeps its label; the reason says why (zero direction or missing inference)."""
    assert st.label_reason(per_source, pooled) == reason
    assert (st.label(per_source, pooled, 0.05) == "not_enough_data") == (reason is not None)
