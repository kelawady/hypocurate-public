"""Step 7: the statistics module reproduces the approved reference numbers independently (PRD 14.1a,
13.1; CLAUDE.md "Reference numbers"; register 'reference_numbers', 'reference_test_tolerance').

**Which path produces each result.** Every run below goes through the real pipeline (adapters,
Checks, Inclusion, the dataset freeze) under the reference plan, then `analysis.run_statistics`,
which reads the frozen sets through the Statistics access object:

| Reference result | Path |
|---|---|
| Pooled | reference run (MPEA + Texas A&M, fixed minimums): its pooled analysis |
| Nine sensitivity sets (the ninth approved 2026-10-06) | the same reference run: each set's sensitivity analysis |
| MPEA alone (1) | the reference run's per-source analysis for MPEA: full numbers, label "agrees"; run level 6 |
| MPEA alone (2) | a run that chose MPEA only, "use what is available": pooled analysis; it meets every minimum, so full numbers, a verdict, not exploratory; level 6 |
| MPEA alone (3) | a run that chose MPEA only, fixed minimums: pooled analysis; full numbers, a verdict; level 6 |
| Texas A&M alone (1) | the reference run's per-source analysis for Texas A&M: coefficient only (one group), label "not enough data"; run level 6 (from the pooled result) |
| Texas A&M alone (2) | a run that chose Texas A&M only, "use what is available": pooled analysis; coefficient only, no verdict; level 4 |
| Texas A&M alone (3) | a run that chose Texas A&M only, fixed minimums: withheld (21 records < 30, 1 group < 10): counts against each minimum and the 21 records found, no coefficient; level 3 |

**Tolerances, two tiers.**
1. Against the approved numbers, which are rounded: half a unit in the last digit stated. k and
   its standard error are stated to 0.1, so ±0.05; a p-value stated to two significant figures
   must lie in the interval that rounds to them (for 1.3e-6: [1.25e-6, 1.35e-6)). Counts are exact.
   This is tighter than the register's earlier ±1 (replaced with the owner's approval, 2026-10-05).
2. Package against the independent reference implementation (`reference_stats`, statsmodels) on
   the same frozen data: relative 1e-9 (same closed-form quantities in double precision; observed
   differences are below 1e-13).
Each "±" is one standard error (cluster-robust, by group), not a confidence interval.
"""
from __future__ import annotations

import math

import pytest

import pipeline_world as pw
import reference_stats as rs
from conftest import _create, _drop, url_for
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources.normalize import same_alloy_key
from stats_world import rows_of

# Approved values (owner, 2026-10-06; CLAUDE.md and the step 6 summary's table): records, alloys,
# groups, residual df, k, standard error, p-value as stated.
APPROVED = {
    "pooled": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "per_source:mpea": (76, 13, 19, 62, "424.1", "62.2", "1.1e-6"),
    "sensitivity:no_exclusions": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:tension_and_compression": (98, 22, 21, 75, "428.0", "63.5", "7.4e-7"),
    "sensitivity:six_batches_as_groups": (97, 22, 22, 74, "424.9", "64.2", "7.5e-7"),
    "sensitivity:same_alloy_1_at_pct": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:source_only_assignments": (76, 13, 19, 62, "424.1", "62.2", "1.1e-6"),
    "sensitivity:scope_not_confirmed_included": (103, 23, 22, 79, "432.4", "64.9", "6.7e-7"),
    "sensitivity:possible_duplicates_separate": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    "sensitivity:conflicts_survivor_value": (97, 22, 20, 74, "424.9", "64.4", "1.3e-6"),
    # Step 7b: without the group with the largest share of slope information; approved by the owner on
    # 2026-10-06 as reported (register 'reference_numbers').
    "sensitivity:without_most_influential_paper": (89, 22, 19, 66, "393.5", "90.5", "1.9e-4"),
}
TAMU = (21, 9, 1, 11, "1173.3")  # coefficient only (step 6 table; CLAUDE.md: "≈ 1173")


def half_unit(stated: str) -> float:
    """Half a unit in the last digit of a stated number ("424.9" -> 0.05; "1.3e-6" -> 0.05e-6)."""
    mantissa, _, exponent = stated.partition("e")
    decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
    return 0.5 * 10 ** (-decimals) * (10 ** int(exponent) if exponent else 1)


def within(value: float, stated: str) -> bool:
    return abs(value - float(stated)) <= half_unit(stated) * (1 + 1e-12)


def test_half_a_unit_in_the_last_digit():
    assert half_unit("424.9") == pytest.approx(0.05) and half_unit("1173.3") == pytest.approx(0.05)
    assert half_unit("1.3e-6") == pytest.approx(0.05e-6) and half_unit("7.4e-7") == pytest.approx(0.05e-7)
    assert within(424.94, "424.9") and not within(424.96, "424.9")


def _run(engine, sources, option="fixed_minimum"):
    rid = pw.dispatched_run(engine, sources=sources, sufficiency=option)  # step 8b (0006): the query's option
    plan = reference_plan(pw.version_of(engine, rid))
    plan["sufficiency"]["option"] = option
    checkpoints.lock_rules(engine, rid, plan)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid


@pytest.fixture(scope="module")
def runs(admin, database_url, template_database):
    """Five runs in one scratch database, each through the freeze and the analysis stage."""
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        out = {}
        for key, sources, option in (("reference", ("mpea", "tamu_fcc"), "fixed_minimum"),
                                     ("mpea_use", ("mpea",), "use_available"), ("mpea_fixed", ("mpea",), "fixed_minimum"),
                                     ("tamu_use", ("tamu_fcc",), "use_available"),
                                     ("tamu_fixed", ("tamu_fcc",), "fixed_minimum")):
            rid = _run(engine, sources, option)
            data = bind_code(engine, rid, "statistics").get("frozen_analysis_data")
            stats_out = analysis.run_statistics(engine, rid)
            completion.copy_decision(engine, rid)
            run = rows_of(engine, "SELECT outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r", r=rid)[0]
            out[key] = {"rid": rid, "data": data, "out": stats_out, "run": run,
                        "analyses": {e["analysis"]: e for e in stats_out["analyses"]}}
        yield out
    finally:
        engine.dispose()
        _drop(admin, name)


def check_approved(entry, approved):
    n, alloys, groups, df, k, se, p = approved
    c = entry["counts"]
    assert (c["n_records"], c["n_alloys"], c["n_groups"], c["resid_df"]) == (n, alloys, groups, df)
    assert within(entry["estimate"], k), (entry["estimate"], k)
    assert within(entry["std_error"], se), (entry["std_error"], se)
    assert within(entry["p_value"], p), (entry["p_value"], p)


# --- tier 1: the approved numbers ----------------------------------------------------------------------

def test_pooled(runs):
    ref = runs["reference"]
    check_approved(ref["analyses"]["pooled"], APPROVED["pooled"])
    assert ref["out"]["decision"]["verdict"] == "supported"
    assert tuple(ref["run"]) == ("sufficient", "supported", False, 6)


@pytest.mark.parametrize("key", [k for k in APPROVED if k.startswith("sensitivity:")])
def test_each_sensitivity_set(runs, key):
    """Sensitivity sets go through the same code as the primary set; they never change the verdict."""
    entry = runs["reference"]["analyses"][key]
    check_approved(entry, APPROVED[key])
    assert entry["label"] is None and "verdict" not in entry


def test_mpea_alone_1_per_source_in_the_pooled_run(runs):
    entry = runs["reference"]["analyses"]["per_source:mpea"]
    check_approved(entry, APPROVED["per_source:mpea"])
    assert entry["label"] == "agrees" and runs["reference"]["run"].evidence_level == 6


@pytest.mark.parametrize("key, option", [("mpea_use", "use_available"), ("mpea_fixed", "fixed_minimum")])
def test_mpea_alone_2_and_3_as_its_own_run(runs, key, option):
    r = runs[key]
    pooled = r["analyses"]["pooled"]
    check_approved(pooled, APPROVED["per_source:mpea"])
    assert pooled["minimums_met"] and not pooled["withheld"]
    assert r["out"]["sufficiency_option"] == option
    assert tuple(r["run"]) == ("sufficient", "supported", False, 6)  # minimums met: not exploratory


def test_texas_am_alone_1_per_source_in_the_pooled_run(runs):
    entry = runs["reference"]["analyses"]["per_source:tamu_fcc"]
    n, alloys, groups, df, k = TAMU
    c = entry["counts"]
    assert (c["n_records"], c["n_alloys"], c["n_groups"], c["resid_df"]) == (n, alloys, groups, df)
    assert within(entry["estimate"], k) and entry["std_error"] is None and entry["p_value"] is None
    assert entry["label"] == "not_enough_data" and runs["reference"]["run"].evidence_level == 6
    assert {m: (c["status"], c["reason"]) for m, c in entry["calibration"].items()} == {
        "fixed": ("unavailable", "insufficient_groups"), "estimated": ("unavailable", "insufficient_groups")}


def test_texas_am_alone_2_use_what_is_available(runs):
    r = runs["tamu_use"]
    pooled = r["analyses"]["pooled"]
    assert within(pooled["estimate"], TAMU[4]) and pooled["std_error"] is None and pooled["p_value"] is None
    assert r["out"]["decision"]["state"] == "coefficient_only"
    assert tuple(r["run"]) == ("insufficient", None, False, 4)


def test_texas_am_alone_3_fixed_minimums_withheld(runs):
    r = runs["tamu_fixed"]
    pooled = r["analyses"]["pooled"]
    assert pooled["withheld"] and pooled["estimate"] is None
    assert pooled["minimums"] == {"records": {"count": 21, "minimum": 30, "met": False},
                                  "alloys": {"count": 9, "minimum": 5, "met": True},
                                  "groups": {"count": 1, "minimum": 10, "met": False},
                                  "resid_df": {"count": 11, "minimum": 10, "met": True}}
    assert len(pooled["records_found"]) == 21 and pooled["label_text"] == "data found; not enough to test"
    assert r["out"]["decision"]["state"] == "below_minimums"
    assert tuple(r["run"]) == ("insufficient", None, False, 3)
    assert all(e["estimate"] is None for e in r["out"]["analyses"])  # run-wide


# --- tier 2: against the independent reference implementation ---------------------------------------

def _rows(data, set_key, source=None):
    """Test-side alloy and group keys, independent of the package's eligibility module."""
    decimals = 0 if set_key == "same_alloy_1_at_pct" else 1
    out = []
    for r in data["records"]:
        if r["id"] not in set(data["sets"][set_key]) or (source and r["source"] != source):
            continue
        if r["source"] == "tamu_fcc":
            group = f"batch:{r['batch']}" if set_key == "six_batches_as_groups" else "dataset:tamu_fcc"
        else:
            group = f"paper:{r['paper']}"
        out.append((same_alloy_key(r["composition"], decimals), group, r["grain_size"], r["outcome"]))
    return out


@pytest.mark.parametrize("key", list(APPROVED) + ["per_source:tamu_fcc"])
def test_every_reference_result_matches_the_reference_implementation(runs, key):
    ref = runs["reference"]
    scope, _, name = key.partition(":")
    set_key = name if scope == "sensitivity" else "primary"
    expected = rs.fit(_rows(ref["data"], set_key, name if scope == "per_source" else None))
    got = ref["analyses"][key]
    assert (got["counts"]["n_records"], got["counts"]["n_alloys"], got["counts"]["n_groups"]) == (
        expected["n"], expected["alloys"], expected["groups"])
    for mine, theirs in ((got["estimate"], expected["k"]), (got["std_error"], expected["se"]),
                         (got["p_value"], expected["p"])):
        assert (mine is None and theirs is None) or math.isclose(mine, theirs, rel_tol=1e-9)


# --- step 7b: the set without the most influential paper (owner, 2026-10-06) ------------------------

INFLUENCE = "sensitivity:without_most_influential_paper"


def _information_by_group(rows):
    """Test-side I_g (pandas; register 'effective_papers'), independent of the package."""
    f = rs.frame(rows)
    dev = f["x"] - f.groupby("alloy")["x"].transform("mean")
    return (dev ** 2).groupby(f["group"]).sum()


def test_the_set_without_the_most_influential_paper(runs):
    """The paper removed is the one test-side pandas finds with the largest I_g on the pooled set
    (no tie on these data); the set is the primary set minus exactly its records; its result matches
    the independent implementations; it is descriptive and leaves the decision as the pooled result
    alone gives it."""
    from hypocurate.pipeline import statistics as st
    ref = runs["reference"]
    data = ref["data"]
    info = _information_by_group(_rows(data, "primary")).sort_values(ascending=False)
    assert info.iloc[0] > info.iloc[1] * (1 + 1e-6)  # a clear maximum: the tie-break is not used here
    removed = info.index[0]
    assert info.iloc[0] / info.sum() == pytest.approx(ref["analyses"]["pooled"]["counts"]["largest_paper_share"],
                                                       rel=1e-12)
    by_id = {r["id"]: r for r in data["records"]}
    group_of = lambda r: "dataset:tamu_fcc" if r["source"] == "tamu_fcc" else f"paper:{r['paper']}"  # noqa: E731
    assert set(data["sets"]["without_most_influential_paper"]) == {
        i for i in data["sets"]["primary"] if group_of(by_id[i]) != removed}
    got = ref["analyses"][INFLUENCE]
    rows = _rows(data, "without_most_influential_paper")
    decimal = rs.fit_informative(rows)
    assert got["counts"]["n_groups_informative"] == decimal["groups_informative"]
    assert got["df"] == decimal["df"]
    for mine, theirs in ((got["estimate"], decimal["k"]), (got["std_error"], decimal["se"]),
                         (got["p_value"], decimal["p"])):
        assert math.isclose(mine, theirs, rel_tol=1e-9)
    effective, share = rs.effective_papers(rows)
    assert math.isclose(got["counts"]["effective_papers"], effective, rel_tol=1e-9)
    assert math.isclose(got["counts"]["largest_paper_share"], share, rel_tol=1e-9)
    assert got["label"] is None and "verdict" not in got
    pooled = ref["analyses"]["pooled"]
    assert ref["out"]["decision"] == st.decision(pooled, reference_plan(1), ref["out"]["freeze_fingerprint"])


def test_the_set_without_the_most_influential_paper_as_approved(runs):
    """Approved by the owner on 2026-10-06, as reported: the counts, k, its standard error and p (in
    APPROVED, also checked by `test_each_sensitivity_set`), the four quantities and the removed group."""
    ref = runs["reference"]
    got = ref["analyses"][INFLUENCE]
    check_approved(got, APPROVED[INFLUENCE])
    c = got["counts"]
    assert (c["n_groups_informative"], got["df"]) == (19, 18)
    assert within(c["effective_papers"], "3.24") and within(c["largest_paper_share"], "0.521")
    pooled = ref["analyses"]["pooled"]["counts"]
    removed = set(ref["data"]["sets"]["primary"]) - set(ref["data"]["sets"]["without_most_influential_paper"])
    by_id = {r["id"]: r for r in ref["data"]["records"]}
    assert len(removed) == 8 and len({same_alloy_key(by_id[i]["composition"], 1) for i in removed}) == 1
    assert pooled["n_records"] - len(removed) == c["n_records"]
