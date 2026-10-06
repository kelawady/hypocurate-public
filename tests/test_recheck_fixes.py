"""Step 7 re-check fixes (ChatGPT, 2026-10-06) and the owner's decision on concentrated evidence.

Owner (2026-10-06): for every analysis, the effective number of papers (Σ I_g)² / Σ I_g², I_g a paper's
sum of squared within-alloy deviations of the transformed grain size, and the largest single paper's
share are stored with the result. Validity check 2 requires an effective number of at least 2; below
that, the coefficient only, with the reason 'evidence_concentrated'. The minimum of 10 remains the
count of informative papers. The same check applies in every simulated fit.
"""
from __future__ import annotations

import math
import random

import numpy as np
import pytest
from scipy import stats

import generator as g
import reference_stats as rs
from hypocurate.pipeline import analysis
from hypocurate.pipeline import calibration as cal
from hypocurate.pipeline import statistics as st
from test_statistics_boundaries import frozen


def as_reference(rows):
    return [(f"a{a}", f"paper:{p}", d, y) for (a, p, d, y) in rows]


def design_of(rows, name="r"):
    return st.design(analysis.observations(frozen(rows, name)["records"], g.plan(), "primary"), "inverse_square_root")


def nudged_rows():
    """The reviewer's nudged design: the original five alloys × six records, the four mean-valued
    predictors in each alloy moved to 0.5 ± 0.000001 (alternating), so every paper is informative."""
    sizes, ys = (16.0, 16.0 / 9.0, 4.0, 4.0, 4.0, 4.0), (400.0, 600.0, 470.0, 510.0, 500.0, 490.0)
    rows, n = [], 0
    for a in range(5):
        for j in range(6):
            paper = "paper-00" if j < 2 else f"paper-{1 + n % 10:02d}"
            n += j >= 2
            x = sizes[j] ** -0.5 if j < 2 else 0.5 + (1e-6 if j % 2 == 0 else -1e-6)
            rows.append((a, paper, x ** -2, ys[j] + 100.0 * a))
    return rows


def counterexample_rows():
    """The reviewer's counterexample: one alloy, five papers, one record each; small contrasts carry
    large residuals."""
    xs = (1.999, 2.001, 2 + 1e-10, 2 - 1e-10, 2.0)
    offsets = (1e-6, 1e-6, 100.0, 100.0, -200.0 - 2e-6)
    return [(0, f"p{i}", x ** -2, 300.0 + 0.01 * x + o) for i, (x, o) in enumerate(zip(xs, offsets))]


# --- concentrated evidence (owner's decision) -------------------------------------------------------

@pytest.mark.parametrize("option", ["fixed_minimum", "use_available"])
def test_the_nudged_design_gives_no_verdict(option):
    out = analysis.analyse(g.plan(option, n_simulations=200), frozen(nudged_rows(), "nudge"))
    pooled = out["analyses"][0]
    assert pooled["counts"]["n_groups_informative"] == 11  # every paper counts as informative...
    assert pooled["counts"]["effective_papers"] < 1.001  # ...but one paper carries the information
    assert pooled["counts"]["largest_paper_share"] > 0.999
    assert out["decision"]["verdict"] is None and pooled["p_value"] is None and pooled["std_error"] is None
    assert pooled["checks"]["inference_valid"] is False and pooled["inference_reason"] == "evidence_concentrated"
    assert {c["reason"] for c in pooled["calibration"].values()} == {"evidence_concentrated"}
    if option == "use_available":
        assert out["decision"]["evidence_level"] == 4 and pooled["estimate"] is not None


def test_the_effective_number_of_papers_is_the_owners_formula():
    for spec in g.FIXED_SET:
        data = g.frozen_data(spec)
        d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
        if not d.coefficient_fitted:
            assert (d.effective_papers, d.largest_paper_share) == (0.0, None)
            continue
        n_eff, share = rs.effective_papers(g.rows(data))
        assert math.isclose(d.effective_papers, n_eff, rel_tol=1e-9), spec.name
        assert math.isclose(d.largest_paper_share, share, rel_tol=1e-9), spec.name
        assert d.effective_papers <= d.n_groups_informative + 1e-9


def test_every_simulated_fit_requires_two_effective_papers():
    d = design_of(nudged_rows(), "nudge")
    rng = np.random.default_rng(4)
    outcomes = rng.normal(0, 60, (300, d.n)) + rng.normal(0, 40, (300, d.n_groups))[:, d.group]
    assert cal.significant_count(d, outcomes, 0.05) == 0


def test_the_effective_number_and_share_are_reported_with_every_result():
    out = analysis.analyse(g.plan("fixed_minimum", n_simulations=50), g.frozen_data(g.SPECS["small_but_valid"]))
    for e in out["analyses"]:  # also withheld results: structure only, no outcome
        assert e["withheld"] and e["counts"]["effective_papers"] > 0 and 0 < e["counts"]["largest_paper_share"] <= 1


# --- every paper's score stays in the covariance -----------------------------------------------------

def test_the_counterexample_keeps_every_papers_score():
    """Every paper's score in the sandwich; informative papers (two) only in the factor and the df. The
    result equals the independent check (the 60-digit decimal sandwich of `reference_stats.fit_informative`,
    which keeps every score) and is no less cautious than counting every paper; the old filtered result (p = 0.0366) is gone."""
    rows = counterexample_rows()
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(rows, "ce"))["analyses"][0]
    d = design_of(rows, "ce")
    assert (d.n_groups, d.n_groups_informative) == (5, 2) and d.effective_papers >= 2
    ref = rs.fit_informative(as_reference(rows))  # every score; informative papers in factor and df
    every = rs.fit_informative(as_reference(rows), count="all")  # the earlier, all-paper definition
    assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-6)
    assert math.isclose(pooled["p_value"], ref["p"], rel_tol=1e-6)
    assert math.isclose(every["p"], 0.1685, abs_tol=5e-5)  # the reviewer's all-paper figure
    assert pooled["df"] == 1 and pooled["p_value"] >= every["p"]
    assert not math.isclose(pooled["p_value"], 0.0366, rel_tol=0.01)


def test_simulated_fits_keep_every_papers_score():
    """Simulated outcomes with the counterexample's structure (residuals near zero on the two
    informative papers, large on the others): each simulated fit is decided as the independent check
    decides it, which keeps every paper's score."""
    rows = counterexample_rows()
    d = design_of(rows, "ce")
    rng = np.random.default_rng(8)
    informative = np.abs(st.demeaned(d.x, d.alloy, d.n_alloys)) > 1e-6
    noise = np.zeros((300, d.n))
    # As in the counterexample, each kind's residuals sum to zero, so the alloy's average absorbs none of them.
    for mask, size in ((informative, 1e-6), (~informative, 100.0)):
        idx = np.flatnonzero(mask)
        draws = rng.normal(0, size, (300, idx.size - 1))
        noise[:, idx[:-1]], noise[:, idx[-1]] = draws, -draws.sum(axis=1)
    outcomes = 300.0 + 0.01 * d.x[None, :] + noise
    expected = 0
    for y in outcomes:
        sim = [(f"a{d.alloy[i]}", f"g{d.group[i]}", float(d.x[i]) ** -2, float(y[i])) for i in range(d.n)]
        expected += rs.fit_informative(sim)["p"] < 0.05
    assert cal.significant_count(d, outcomes, 0.05) == expected


# --- distinct grain sizes from the full range ---------------------------------------------------------

def test_adding_a_record_never_removes_an_alloys_contrast():
    """The reviewer's chain: [1, 1+1.5e-10] has contrast; inserting 1+0.75e-10 must keep it."""
    assert st.has_contrast([1.0, 1.0 + 1.5e-10])
    assert st.has_contrast([1.0, 1.0 + 0.75e-10, 1.0 + 1.5e-10])
    assert not st.has_contrast([1.0, 1.0 + 0.5e-10])
    rnd = random.Random(1)
    for _ in range(2000):
        values = [1.0 + rnd.uniform(0, 3e-10) for _ in range(rnd.randint(2, 6))]
        if st.has_contrast(values):
            assert st.has_contrast(values + [rnd.uniform(min(values), max(values))])
            assert st.has_contrast(values + [1.0 + rnd.uniform(-1e-9, 1e-9)])


def test_an_alloy_keeps_its_contrast_in_a_design_when_a_middle_record_is_added():
    base = [(0, "p1", 1.0, 400.0), (0, "p2", (1.0 + 1.5e-10) ** -2, 410.0), (1, "p1", 1.0, 500.0), (1, "p2", 4.0, 420.0)]
    with_middle = base + [(0, "p3", (1.0 + 0.75e-10) ** -2, 405.0)]
    assert design_of(base, "c1").n_alloys == design_of(with_middle, "c2").n_alloys


# --- the numerical zero at the data's own scale ---------------------------------------------------------

def big_baseline_rows(k=1e-5, noise=0.0, seed=2):
    rng = np.random.default_rng(seed)
    return [(a, f"p{(j + a) % 5}", d, 200.0 + 175.0 * a + k * d ** -0.5 + (rng.normal(0, noise) if noise else 0.0))
            for a in range(5) for j, d in enumerate((1.0, 4.0, 16.0, 64.0))]


def test_a_perfect_fit_with_large_baselines_and_a_tiny_slope_gives_no_inference():
    """Baselines 200 to 900 MPa, k = 1e-5, no noise: residuals are rounding at the data's scale."""
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), frozen(big_baseline_rows(), "big"))["analyses"][0]
    assert pooled["inference_reason"] == "uncertainty_not_estimable" and pooled["p_value"] is None
    assert math.isclose(pooled["estimate"], 1e-5, rel_tol=1e-3)
    assert cal.henderson_iii(design_of(big_baseline_rows(), "big"))["reason"] == "scatter_not_estimable"


def test_a_perfect_fit_is_judged_the_same_whatever_the_baselines():
    for shift in (0.0, 1e3, 1e6):
        rows = [(a, p, d, y + shift) for a, p, d, y in big_baseline_rows(k=250.0)]
        pooled = analysis.analyse(g.plan("use_available", n_simulations=20), frozen(rows, f"s{shift}"))["analyses"][0]
        assert pooled["inference_reason"] == "uncertainty_not_estimable", shift


def test_small_real_noise_with_large_baselines_stays_estimable():
    """An arithmetic safeguard, not a scientific minimum: 0.01 MPa of scatter on 200 to 900 MPa is estimated."""
    rows = big_baseline_rows(k=250.0, noise=0.01)
    pooled = analysis.analyse(g.plan("use_available", n_simulations=20), frozen(rows, "noisy"))["analyses"][0]
    assert pooled["inference_reason"] is None and pooled["std_error"] > 0
    assert cal.henderson_iii(design_of(rows, "noisy"))["reason"] in (None, "shift_not_estimable")


# --- the detection note states the locked threshold -----------------------------------------------------

def test_the_detection_note_states_the_plans_threshold():
    plan = g.plan("use_available", n_simulations=50)
    plan["model"]["alpha"] = 0.01
    pooled = analysis.analyse(plan, g.frozen_data(g.SPECS["effect_many_papers"]))["analyses"][0]
    assert "α = 0.01" in pooled["detection_note"] and "5%" not in pooled["detection_note"]


def test_simulated_perfect_fits_on_large_baselines_are_never_significant():
    """The residual floor applies in every simulated fit: exact outcomes on baselines of 200 to 900 MPa
    with a tiny slope (where the standard-error check alone lets rounding through)."""
    d = design_of(big_baseline_rows(), "big")
    baselines = 200.0 + 175.0 * d.alloy
    exact = np.vstack([baselines + k * d.x for k in (1e-5, 3e-5, 1e-4)])
    assert cal.significant_count(d, exact, 0.05) == 0
