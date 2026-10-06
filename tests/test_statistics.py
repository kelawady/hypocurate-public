"""Step 7: the supported model, the validity checks, the minimums, the verdict, the labels and
the evidence level (PRD 5.7 to 5.9; CLAUDE.md rules 5 to 7; owner's decisions of 2026-10-05).
Pure functions, no database."""
from __future__ import annotations

import ast
import math
import random
from pathlib import Path

import numpy as np
import pytest

import generator as g
import reference_stats as rs
from hypocurate.pipeline import analysis, profile
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.plan import PlanError, default_plan, validate

PACKAGE = Path(__file__).resolve().parents[1] / "hypocurate" / "pipeline"


def obs(rows):
    """(identity, alloy, group, grain size, outcome) tuples as observations."""
    return [st.Observation(*r) for r in rows]


def test_the_model_is_the_one_supported_model():
    assert st.MODEL_MIN_GRAIN_SIZES == 2
    assert set(st.TRANSFORMATIONS) == {"inverse_square_root"}
    assert st.TRANSFORMATIONS["inverse_square_root"](4.0) == 0.5
    assert default_plan(1)["model"] == {"name": "hall_petch_alloy_intercepts", "null": "k <= 0",
                                        "alternative": "k > 0", "alpha": 0.05}


def test_the_small_sample_correction_is_statsmodels_default():
    """G/(G-1) × (N-1)/(N-K), K = alloys + 1 (register 'cluster_robust_se')."""
    assert st.small_sample_factor(97, 22, 20) == pytest.approx((20 / 19) * (96 / 74), rel=1e-15)


def test_the_fit_matches_the_reference_on_a_hand_made_dataset():
    rows = [("r1", "A", "p1", 1.0, 500.0), ("r2", "A", "p2", 4.0, 420.0), ("r3", "A", "p3", 16.0, 390.0),
            ("r4", "B", "p1", 1.0, 700.0), ("r5", "B", "p2", 9.0, 600.0), ("r6", "B", "p3", 25.0, 585.0),
            ("r7", "C", "p4", 2.0, 300.0), ("r8", "C", "p4", 8.0, 260.0)]
    f = st.fit(st.design(obs(rows), "inverse_square_root"))
    ref = rs.fit([(a, gr, d, y) for _, a, gr, d, y in rows])
    assert math.isclose(f.estimate, ref["k"], rel_tol=1e-9) and math.isclose(f.std_error, ref["se"], rel_tol=1e-9)
    assert math.isclose(f.p_value, ref["p"], rel_tol=1e-9) and f.df == 3


def test_the_test_is_one_sided():
    """k < 0 gives p > 0.5: a negative slope is never support for k > 0."""
    data = g.frozen_data(g.SPECS["negative_effect"])
    pooled = analysis.analyse(g.plan("use_available"), data)["analyses"][0]
    assert pooled["estimate"] < 0 and pooled["p_value"] > 0.5 and pooled["significant"] is False


def test_supported_exactly_when_p_is_strictly_below_alpha():
    assert st.significant(0.0499999, 0.05) is True
    assert st.significant(0.05, 0.05) is False
    assert st.significant(0.0500001, 0.05) is False
    assert st.significant(None, 0.05) is None
    plan = g.plan("use_available")
    pooled = {"withheld": False, "checks": {"coefficient_fitted": True, "inference_valid": True},
              "minimums_met": True, "p_value": 0.05}
    assert st.decision(pooled, plan, "f")["verdict"] == "not_supported"
    assert st.decision({**pooled, "p_value": 0.049}, plan, "f")["verdict"] == "supported"


def test_a_zero_standard_error_gives_a_defined_p_value():
    assert st.one_sided_p(math.inf, 5) == 0.0 and st.one_sided_p(-math.inf, 5) == 1.0


def test_a_fit_uses_only_alloys_with_two_distinct_grain_sizes():
    """Decision 7: the model's own condition, on grain sizes only; the others are reported as not
    used in this fit, and the counts are the fit's (decision 12)."""
    rows = [("r1", "A", "p1", 1.0, 500.0), ("r2", "A", "p2", 4.0, 420.0), ("r3", "A", "p2", 4.0, 425.0),
            ("r4", "B", "p1", 2.0, 700.0), ("r5", "B", "p3", 2.0, 690.0),  # one distinct size
            ("r6", "C", "p4", 3.0, 300.0)]
    d = st.design(obs(rows), "inverse_square_root")
    assert (d.n, d.n_alloys, d.n_groups, d.n_records_in_set, d.n_alloys_not_used) == (3, 1, 2, 6, 2)
    assert d.resid_df == 1 and d.coefficient_fitted
    # Re-check (owner, 2026-10-06): the two papers carry unequal information (effective number 1.8 < 2),
    # so check 2 fails on concentrated evidence; the counts below are unaffected.
    assert not d.counts_allow_inference and d.counts_reason == "evidence_concentrated"
    entry = st.analysis_entry(d, g.plan("use_available", minimums=(3, 1, 2, 1)), withheld=False)
    assert entry["counts"]["n_records_not_used"] == 3
    assert entry["minimums"]["records"] == {"count": 3, "minimum": 3, "met": True}
    assert entry["minimums_met"]
    entry4 = st.analysis_entry(d, g.plan("use_available", minimums=(4, 1, 2, 1)), withheld=False)
    assert not entry4["minimums_met"]  # 6 records in the set, but the fit uses 3


@pytest.mark.parametrize("rows, check1, check2", [
    ([("a", "A", "p1", 1.0, 1.0)], False, False),                                           # one record
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 1.0, 2.0)], False, False),              # one grain size
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0)], True, False),               # resid df 0
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p1", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, False),  # 1 group
    # Re-check (owner, 2026-10-06): this design's information is concentrated in p1 (effective number
    # about 1.1), so check 2 now fails; the balanced case after it passes.
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p2", 4.0, 2.0), ("c", "A", "p1", 9.0, 3.0)], True, False),
    ([("a", "A", "p1", 1.0, 1.0), ("b", "A", "p1", 4.0, 2.0), ("c", "A", "p2", 1.0, 1.5), ("d", "A", "p2", 4.0, 2.9)],
     True, True),
])
def test_the_two_validity_checks(rows, check1, check2):
    d = st.design(obs(rows), "inverse_square_root")
    assert (d.coefficient_fitted, d.counts_allow_inference) == (check1, check2)  # step 7 review: renamed
    f = st.fit(d)
    assert (f is not None) == check1
    if check1:
        assert (f.std_error is not None, f.p_value is not None) == (check2, check2)


def test_results_do_not_depend_on_record_order_or_ids():
    """Records are sorted by stable identity before any arithmetic: shuffling gives bit-identical
    numbers."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    plan = g.plan("use_available", n_simulations=200)
    first = analysis.analyse(plan, data)
    rnd = random.Random(7)
    for _ in range(3):
        records = list(data["records"])
        rnd.shuffle(records)
        new_ids = list(range(1000, 1000 + len(records)))
        rnd.shuffle(new_ids)
        remap = {r["id"]: i for r, i in zip(records, new_ids)}
        shuffled = {**data, "records": [{**r, "id": remap[r["id"]]} for r in records],
                    "sets": {"primary": [remap[i] for i in reversed(data["sets"]["primary"])]}}
        assert analysis.analyse(plan, shuffled) == first


def test_two_records_with_one_identity_are_refused():
    rows = [("same", "A", "p1", 1.0, 1.0), ("same", "A", "p2", 4.0, 2.0)]
    with pytest.raises(st.StatisticsError):
        st.design(obs(rows), "inverse_square_root")


def test_a_record_without_a_group_is_refused_never_given_one():
    """Register 'paper_grouping_by_doi': no group is invented. The analysis refuses."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    data["records"][0]["paper"] = None
    with pytest.raises(st.StatisticsError, match="records_without_group"):
        analysis.analyse(g.plan(), data)


# --- labels, states, levels -------------------------------------------------------------------

def _r(estimate, p):
    return {"estimate": estimate, "p_value": p}


@pytest.mark.parametrize("per_source, pooled, expected", [
    (_r(400, 1e-5), _r(420, 1e-6), "agrees"),                                   # same sign, both significant
    (_r(30, 0.4), _r(20, 0.3), "agrees"),                                       # same sign, both not
    (_r(-50, 0.9), _r(420, 1e-6), "conflicts"),                                 # opposite sign
    (_r(-50, 0.01), _r(-20, 0.9), "same_direction_different_decision"),         # same sign, different decision
    (_r(-50, 0.9), _r(20, 0.3), "conflicts"),                                   # opposite sign, same decision
    (_r(100, 0.2), _r(420, 1e-6), "same_direction_different_decision"),
    (_r(1173, None), _r(424, 1e-6), "not_enough_data"),                         # no p-value
    (_r(400, 1e-5), _r(424, None), "not_enough_data"),                          # pooled has no decision
    (_r(0.0, 0.5), _r(424, 1e-6), "not_enough_data"),                           # no sign
])
def test_the_four_per_source_labels(per_source, pooled, expected):
    """Owner, 2026-10-05: from the locked test and the sign only; descriptive."""
    assert st.label(per_source, pooled, 0.05) == expected


def _pooled(withheld=False, c1=True, c2=True, met=True, p=0.01):
    return {"withheld": withheld, "checks": {"coefficient_fitted": c1, "inference_valid": c2},
            "minimums_met": met, "p_value": p}


@pytest.mark.parametrize("pooled, option, state, level", [
    (None, "fixed_minimum", "no_dataset_frozen", 1),
    (_pooled(withheld=True, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(withheld=True, c1=False, c2=False, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(withheld=True, c2=False, met=False), "fixed_minimum", "below_minimums", 3),
    (_pooled(c1=False, c2=False, met=False), "use_available", "not_fitted", 2),
    (_pooled(c2=False, met=False), "use_available", "coefficient_only", 4),
    (_pooled(c2=False, met=True), "fixed_minimum", "coefficient_only", 4),  # a plan whose minimums allow 1 group
    (_pooled(met=False), "use_available", "exploratory", 5),
    (_pooled(met=True), "use_available", "sufficient", 6),
    (_pooled(met=True), "fixed_minimum", "sufficient", 6),
])
def test_every_result_state_has_its_evidence_level(pooled, option, state, level):
    """Owner, 2026-10-05: 6 sufficient with a verdict; 5 exploratory; 4 coefficient only; 3 below the
    minimums under the fixed option; 2 not fitted; 1 no dataset frozen."""
    plan = g.plan(option)
    assert st.result_state(pooled, option) == state
    d = st.decision(pooled, plan, None if pooled is None else "f")
    assert d["evidence_level"] == level == st.evidence_level(state)
    assert (d["verdict"] is not None) == (level >= 5)
    assert d["exploratory"] == (level == 5)
    assert d["outcome"] == ("sufficient" if level >= 5 else "insufficient")
    assert d["evidence_level_wording"] == st.EVIDENCE_LEVELS[level]


def test_the_evidence_scale_is_the_owners():
    assert dict(st.EVIDENCE_LEVELS) == {
        6: "sufficient with a verdict", 5: "use what is available with a minimum missed (exploratory)",
        4: "inference invalid: coefficient only", 3: "below the minimums under the fixed option",
        2: "coefficient cannot be fitted", 1: "no dataset frozen"}
    assert sorted(st.STATE_LEVELS.values()) == [1, 2, 3, 4, 5, 6]


def test_the_wording_is_scoped_to_the_sources_searched():
    """CLAUDE.md rule 13."""
    for text in (*st.VERDICT_WORDING.values(), *st.OUTCOME_WORDING.values()):
        assert text.endswith("in the sources searched")
    assert st.VERDICT_WORDING["supported"] == "supported under the stated model, in the sources searched"
    assert st.BELOW_MINIMUMS_LABEL == "data found; not enough to test"
    assert st.POWER_LABEL == "estimated power under the stated assumptions"


def test_the_level_never_feeds_back_into_the_outcome_or_verdict(monkeypatch):
    """Whatever the level function returns, the outcome and verdict stay the same."""
    plan = g.plan("use_available")
    for pooled in (None, _pooled(), _pooled(met=False), _pooled(c2=False, met=False), _pooled(p=0.5)):
        before = st.decision(pooled, plan, "f")
        monkeypatch.setattr(st, "evidence_level", lambda state: 1)
        after = st.decision(pooled, plan, "f")
        monkeypatch.undo()
        assert {k: after[k] for k in ("outcome", "verdict", "exploratory", "state")} == \
            {k: before[k] for k in ("outcome", "verdict", "exploratory", "state")}


# --- the plan's calibration part --------------------------------------------------------------

def test_the_default_plan_locks_the_calibration_with_each_default_from_its_named_setting():
    cal = default_plan(1)["calibration"]
    assert cal == {"methods": ["fixed", "estimated"], "n_simulations": profile.CALIBRATION_SIMULATIONS,
                   "scatter": profile.CALIBRATION_SCATTER_MPA, "shift": profile.CALIBRATION_SHIFT_MPA,
                   "estimation": profile.CALIBRATION_ESTIMATION, "smallest_effect": profile.SMALLEST_EFFECT}
    assert (cal["n_simulations"], cal["scatter"], cal["shift"], cal["smallest_effect"]) == (2000, 60.0, 40.0, 150.0)
    validate(default_plan(1))


@pytest.mark.parametrize("change", [
    {"methods": ["fixed"]}, {"methods": ["estimated", "fixed"]}, {"n_simulations": 0}, {"scatter": 0.0},
    {"shift": -1.0}, {"smallest_effect": 0.0}, {"estimation": "reml"}, {"chosen_later": 1},
])
def test_an_invalid_calibration_part_is_refused_at_the_lock(change):
    plan = default_plan(1)
    plan["calibration"] = {**plan["calibration"], **change}
    with pytest.raises(PlanError):
        validate(plan)
    del plan["calibration"]
    with pytest.raises(PlanError):
        validate(plan)


def test_statistics_code_imports_nothing_that_decides_inclusion():
    """Statistics never decides inclusion: the statistics, calibration and analysis modules import
    no inclusion, checks, extraction or checkpoint code, and the analysis stage writes no decision
    or set (only results and stage results)."""
    for name in ("statistics.py", "calibration.py", "analysis.py"):
        tree = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
        imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names} | \
                   {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert not imported & {"inclusion", "checks", "extract", "checkpoints", "hypocurate.pipeline.inclusion",
                               "hypocurate.pipeline.checks", "hypocurate.pipeline.extract",
                               "hypocurate.pipeline.checkpoints"}, name
    source = (PACKAGE / "analysis.py").read_text(encoding="utf-8").upper()
    for table in ("RUN_RECORD", "ANALYSIS_SET_RECORD", "INTO ANALYSIS_SET ", "INTO RECORD", "INTO FLAG"):
        assert f"INSERT INTO {table.replace('INTO ', '')}" not in source and "UPDATE " + table not in source


def test_the_reference_numbers_are_not_in_package_code():
    """The statistics module reproduces the reference numbers independently: none of them is
    written in the package (they live in CLAUDE.md, the register and the tests)."""
    for path in PACKAGE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for number in ("424.9", "64.4", "424.1", "62.2", "1173", "1.3e-6", "1.1e-6"):
            assert number not in text, (path.name, number)
