"""Step 7: the standard error's small-sample factor and the t distribution's degrees of freedom count
informative papers only, the same count as validity check 2 (owner, 2026-10-06; register
'informative_groups_in_inference'; CLAUDE.md rule 6). Applied in the real fits and every simulated fit.

The design: four alloys; in each, one record at x = d^-1/2 = 0.2 and one at 0.8 from two of three
informative papers, and two records at 0.5 (the alloy's average, exactly) from six uninformative
papers. With all nine papers counted (statsmodels' definition) the factor is 9/8 and the test has 8
degrees of freedom; with the three informative papers it is 3/2 and 2 degrees of freedom: a larger
standard error (by exactly sqrt(4/3), since uninformative papers' scores are exactly zero) and a
larger p-value, the cautious direction.
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
from test_statistics_boundaries import frozen


def design_rows(seed=11):
    rng = np.random.default_rng(seed)
    rows, u = [], 0
    for a in range(4):
        for d, paper in ((25.0, f"inf-{a % 3}"), (1.5625, f"inf-{(a + 1) % 3}"), (4.0, None), (4.0, None)):
            if paper is None:
                paper, u = f"uninf-{u % 6}", u + 1
            rows.append((a, paper, d, 300.0 + 50 * a + 250.0 * d ** -0.5 + rng.normal(0, 20.0)))
    return rows


def reference_rows(rows):
    data = frozen(rows, "inf")
    return [(f"a{a}", f"paper:{p}", d, y) for (a, p, d, y) in rows], data


def test_the_design_has_three_informative_and_six_uninformative_papers():
    rows, data = reference_rows(design_rows())
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
    assert (pooled["counts"]["n_groups"], pooled["counts"]["n_groups_informative"]) == (9, 3)
    assert len(pooled["uninformative_groups"]) == 6
    assert rs.informative_groups(rows) == {f"paper:inf-{i}" for i in range(3)}


def test_the_factor_and_degrees_of_freedom_count_informative_papers_only():
    rows, data = reference_rows(design_rows())
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
    assert pooled["df"] == 2  # informative papers - 1, not 9 - 1
    ref = rs.fit_informative(rows)  # independent: explicit sandwich over informative groups
    assert math.isclose(pooled["estimate"], ref["k"], rel_tol=1e-9)
    assert math.isclose(pooled["std_error"], ref["se"], rel_tol=1e-9)
    assert math.isclose(pooled["p_value"], ref["p"], rel_tol=1e-9)


def test_the_result_is_more_cautious_than_counting_every_paper():
    """Against statsmodels with all nine clusters (the earlier definition): same k, a standard error
    larger by exactly sqrt(4/3), fewer degrees of freedom, a larger p-value."""
    rows, data = reference_rows(design_rows())
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
    every = rs.fit(rows)  # statsmodels, every cluster counted
    all_p = float(stats.t.sf(every["k"] / every["se"], 9 - 1))
    assert math.isclose(pooled["estimate"], every["k"], rel_tol=1e-9)
    assert pooled["std_error"] > every["se"]
    assert math.isclose(pooled["std_error"] / every["se"], math.sqrt((3 / 2) / (9 / 8)), rel_tol=1e-9)
    assert pooled["p_value"] > all_p and pooled["df"] < 8


@pytest.mark.parametrize("name", ["effect_many_papers", "large_paper_shifts", "single_size_alloys_added"])
def test_where_every_paper_is_informative_nothing_changes(name):
    """The statsmodels comparison still holds exactly (and the independent sandwich agrees with it)."""
    data = g.frozen_data(g.SPECS[name])
    pooled = analysis.analyse(g.plan("use_available", n_simulations=50), data)["analyses"][0]
    assert pooled["counts"]["n_groups"] == pooled["counts"]["n_groups_informative"]
    every, mine = rs.fit(g.rows(data)), rs.fit_informative(g.rows(data))
    for got, a, b in ((pooled["std_error"], every["se"], mine["se"]), (pooled["p_value"], every["p"], mine["p"])):
        assert math.isclose(got, a, rel_tol=1e-9) and math.isclose(got, b, rel_tol=1e-9)


def test_every_simulated_fit_counts_informative_papers_only():
    """The vectorized simulation decides each simulated fit exactly as the independent sandwich does."""
    rows, data = reference_rows(design_rows())
    d = st.design(analysis.observations(data["records"], g.plan(), "primary"), "inverse_square_root")
    rng = np.random.default_rng(31)
    outcomes = 120.0 * d.x[None, :] + rng.normal(0, 40, (200, d.n_groups))[:, d.group] + rng.normal(0, 60, (200, d.n))
    expected = 0
    for y in outcomes:  # the design's own records, in its order: alloy, group, grain size, outcome
        sim_rows = [(f"a{d.alloy[i]}", f"g{d.group[i]}", float(d.x[i]) ** -2, float(y[i])) for i in range(d.n)]
        expected += rs.fit_informative(sim_rows)["p"] < 0.05
    assert 0 < expected < 200
    assert cal.significant_count(d, outcomes, 0.05) == expected
