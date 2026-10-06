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
