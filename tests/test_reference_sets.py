"""Step 6: the reference run's record sets under the owner's decisions (PRD 14.1a), and the
rule that each sensitivity set differs from the primary set in exactly one named respect.

The reference run (fixed reference plan, MPEA and Texas A&M, not marked as a test) goes
through the freeze. Its primary set is the reference script's selection
(`docs/reference/worked_example.py`, reproduced test-side in
`test_reference_counts_from_adapters.py`) without MPEA row 139, the compression test the
tension-only decision removes; the 21 Texas A&M records stay eligible through their
room-temperature band and microstructure assigned by decision. The counts are those known at
the freeze (no outcome value); the coefficients are recomputed test-side and reported in the
step 6 summary, and become tests in step 7.
"""
from __future__ import annotations

from collections import Counter

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources import adapters
from pipeline_fixtures import decisions, frozen_run
from source_helpers import sealed_from_disk
from test_reference_counts_from_adapters import mpea_reference_set, tamu_reference_set

ROW_139 = "MPEA_dataset.csv:row:139"


@pytest.fixture(scope="module")
def reference(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        from sqlalchemy import text
        with engine.connect() as conn:
            freeze = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'dataset_freeze'"),
                                  dict(r=rid)).scalar_one()
            snapshot = conn.execute(text("SELECT n_records FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar_one()
        yield {**decisions(engine, rid), "freeze": freeze, "snapshot": snapshot}


@pytest.fixture(scope="module")
def with_extract(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc", "controlled_duplicates"),
                    marked=True) as (engine, rid):
        yield decisions(engine, rid)


def origins(run, key="primary", source=None):
    return {run["origin"][i] for i in run["sets"][key] if source is None or run["source"][i] == source}


def test_the_primary_set_is_the_reference_selection_without_row_139(reference):
    mpea = {r.source_item_key for r in mpea_reference_set(adapters.read(sealed_from_disk("mpea")).records)}
    tamu = {r.source_item_key for r in tamu_reference_set(adapters.read(sealed_from_disk("tamu_fcc")).records)}
    assert len(mpea) == 77 and ROW_139 in mpea and len(tamu) == 21
    assert origins(reference, source="mpea") == mpea - {ROW_139}
    assert origins(reference, source="tamu_fcc") == tamu
    row_139 = next(i for i, o in reference["origin"].items() if o == ROW_139)
    assert reference["rules"]["primary"][row_139] == "out_of_scope"
    assert row_139 in reference["sets"]["tension_and_compression"]


def test_every_record_has_one_decision_with_its_rule(reference):
    assert len(reference["rules"]["primary"]) == 1545 + 94 == len(reference["origin"])
    assert reference["sets"]["primary"] == {i for i, r in reference["rules"]["primary"].items() if r == "in_scope"}
    by_source = {s: Counter(r for i, r in reference["rules"]["primary"].items() if reference["source"][i] == s)
                 for s in ("mpea", "tamu_fcc")}
    # Texas A&M: 21 eligible, 72 from alloys measured at one grain size, 1 without yield strength (PRD 10).
    assert by_source["tamu_fcc"] == {"in_scope": 21, "single_grain_size": 72, "missing_value": 1}
    assert by_source["mpea"]["in_scope"] == 76
    assert sum(by_source["mpea"].values()) == 1545


def test_the_two_sources_share_no_measurement(reference):
    assert [f for f in reference["flags"] if f["kind"] != "invalid_value"] == []


def test_the_counts_known_at_the_freeze(reference):
    c = reference["freeze"]["counts"]
    pick = lambda d: {k: d[k] for k in ("n_records", "n_alloys", "n_groups", "resid_df", "minimums_met")}
    assert reference["snapshot"] == 97
    assert pick(c["primary"]) == {"n_records": 97, "n_alloys": 22, "n_groups": 20, "resid_df": 74,
                                  "minimums_met": True}
    assert pick(c["per_source"]["mpea"]) == {"n_records": 76, "n_alloys": 13, "n_groups": 19, "resid_df": 62,
                                             "minimums_met": True}
    per_tamu = c["per_source"]["tamu_fcc"]
    assert pick(per_tamu) == {"n_records": 21, "n_alloys": 9, "n_groups": 1, "resid_df": 11, "minimums_met": False}
    assert per_tamu["check1_inputs_met"] and not per_tamu["check2_inputs_met"]  # one group: no grouped uncertainty
    # Tension and compression together is the earlier reference selection (98, 22 alloys, 21 groups).
    assert pick(c["tension_and_compression"]) == {"n_records": 98, "n_alloys": 22, "n_groups": 21, "resid_df": 75,
                                                  "minimums_met": True}
    # The 21 eligible Texas A&M records come from three of the six batches (counted test-side).
    tamu = tamu_reference_set(adapters.read(sealed_from_disk("tamu_fcc")).records)
    assert Counter(r.reported["Iteration"].text for r in tamu) == {"CBA": 7, "CBB": 7, "CBC": 7}
    assert pick(c["six_batches_as_groups"])["n_groups"] == 19 + 3
    assert pick(c["source_only_assignments"]) == {"n_records": 76, "n_alloys": 13, "n_groups": 19, "resid_df": 62,
                                                  "minimums_met": True}


# --- one named change per sensitivity set ---------------------------------------------------

CASCADE = {"in_scope", "single_grain_size", "duplicate_counted_once"}
SCOPE_FIELDS = ("test_type", "test_temperature", "test_temperature_band", "microstructure", "phase_class")


def _regrouped(key, run):
    """Records whose duplicate group differs under the set's own matching flags (step 6 review,
    finding 2): a matching change can change identity decisions, not only grain-size counts."""
    if key not in run["set_flags"]:
        return set()
    own = {frozenset(f["records"]) for f in run["set_flags"][key]}
    primary = {frozenset(f["records"]) for f in run["flags"] if f["kind"] != "invalid_value"}
    return set().union(*(own ^ primary)) if own ^ primary else set()


def _direct(key, run, i):
    """Is record i one the set's named change applies to directly?"""
    c, primary = run["conditions"][i], run["rules"]["primary"][i]
    in_flag = lambda kind: any(i in f["records"] for f in run["flags"] if f["kind"] == kind)
    if i in _regrouped(key, run):
        return True
    return {
        "no_exclusions": primary == "excluded_by_rule",
        "tension_and_compression": c["categories"]["test_type"] == "compression",
        "six_batches_as_groups": False,
        "same_alloy_1_at_pct": False,
        "source_only_assignments": any(c["status"][f] == "assigned_by_decision" for f in SCOPE_FIELDS),
        "scope_not_confirmed_included": primary == "scope_not_confirmed",
        "possible_duplicates_separate": in_flag("possible_duplicate"),
        "conflicts_survivor_value": in_flag("values_disagree"),
        # Step 7b: the records of the removed paper (checked to be one whole paper below).
        el.INFLUENCE_KEY: run["rules"][el.INFLUENCE_KEY][i] == el.INFLUENCE_RULE,
    }[key]


def _check_one_change(run):
    plan = reference_plan(1)
    differing_total = {}
    for key in plan["sensitivity_analyses"]:
        primary, other = run["rules"]["primary"], run["rules"][key]
        differing = {i for i in primary if primary[i] != other[i]}
        direct = {i for i in differing if _direct(key, run, i)}
        decimals = 0 if key == "same_alloy_1_at_pct" else 1
        alloy = lambda i: el.alloy(run["conditions"][i], decimals)
        touched_alloys = {alloy(i) for i in run["conditions"] if _direct(key, run, i)}
        touched_groups = {i for f in run["flags"] if any(_direct(key, run, j) for j in f["records"])
                          for i in f["records"]}
        for i in differing - direct:
            # The rest changed only through the grain-size count (rule 8) or a survivor (rule 7) that
            # the change reached: never through any other rule.
            assert primary[i] in CASCADE and other[i] in CASCADE, (key, run["origin"][i], primary[i], other[i])
            assert key == "same_alloy_1_at_pct" or alloy(i) in touched_alloys or i in touched_groups, \
                (key, run["origin"][i])
            if key == "same_alloy_1_at_pct":
                # Corrected after the review (finding 2): besides the grain-size count, identity
                # decisions change for records regrouped by the set's own flags (direct, above).
                assert {primary[i], other[i]} <= {"in_scope", "single_grain_size", "duplicate_counted_once"}
        assert run["sets"][key] == {i for i, r in other.items() if r == "in_scope"}
        if key == el.INFLUENCE_KEY:
            # Step 7b: exactly the primary members of one paper (primary grouping) leave; nothing cascades.
            assert differing == direct and {primary[i] for i in differing} == {"in_scope"}
            st = el.settings(plan)
            removed_groups = {el.group(run["conditions"][i], st) for i in differing}
            assert len(removed_groups) == 1
            assert differing == {i for i in run["sets"]["primary"]
                                 if el.group(run["conditions"][i], st) in removed_groups}
        differing_total[key] = len(differing)
    return differing_total


def test_each_sensitivity_set_differs_from_primary_only_by_its_named_change(reference):
    """Owner, 2026-10-05 (register 'sensitivity_one_change'), on the reference run."""
    differing = _check_one_change(reference)
    assert differing["six_batches_as_groups"] == 0
    assert reference["sets"]["six_batches_as_groups"] == reference["sets"]["primary"]
    for key in ("tension_and_compression", "source_only_assignments", "scope_not_confirmed_included",
                "without_most_influential_paper"):
        assert differing[key] > 0, key


def test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts(with_extract):
    """The same, on a marked run with the controlled extract, where possible duplicates and
    conflicts exist."""
    differing = _check_one_change(with_extract)
    for key in ("conflicts_survivor_value", "scope_not_confirmed_included", "without_most_influential_paper"):
        assert differing[key] > 0, key
    # Step 7b (owner, 2026-10-06): the extract's only possible duplicates with an eligible twin (rows 5-6)
    # have no DOI, so no group: rule 5 excludes them in every set, before identity, and this set now
    # equals primary here. Counting possible duplicates separately is still exercised where both records
    # have a group (test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule).
    assert differing["possible_duplicates_separate"] == 0
    assert set(el.SENSITIVITY_CHANGES) == set(reference_plan(1)["sensitivity_analyses"])
