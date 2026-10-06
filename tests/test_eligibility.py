"""Step 6: eligibility decisions under the locked plan (PRD 5.3; `hypocurate.pipeline.eligibility`).

Records here are in the `record_conditions` format Inclusion receives (no outcome value).
Owner, 2026-10-05: one rule per record, the first that applies, in the order of the module
docstring; duplicates are resolved before grain sizes are counted; a conflict and an ambiguous
group enter the primary set with none of their records; every plan setting is read from the locked
plan, never from the domain profile.
"""
from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import profile
from hypocurate.pipeline.plan import default_plan

PLAN = default_plan(1)
STATUS_FIELDS = ("composition", "grain_size", "yield_strength", "test_type", "test_temperature",
                 "test_temperature_band", "microstructure", "phase_class")


def cond(i, source="mpea", comp=None, gs=10.0, temp=25.0, test_type="tension", micro="FCC", phase="FCC", band=None,
         doi=True, row=None, kind="measured", ys=True, status=None, paper="p1", batch=None):
    """A record as Inclusion receives it."""
    st = {f: "not_reported" for f in STATUS_FIELDS}
    st.update({"composition": "converted", "grain_size": "converted" if gs is not None else "not_reported",
               "yield_strength": "converted" if ys else "not_reported",
               "test_type": "converted" if test_type else "not_reported",
               "test_temperature": "converted" if temp is not None else "not_reported",
               "test_temperature_band": "assigned_by_decision" if band else "not_reported",
               "microstructure": "converted" if micro else "not_reported",
               "phase_class": "converted" if phase else "not_reported"})
    st.update(status or {})
    row = i if row is None else row
    return {"id": i, "source": source, "row": row, "origin": f"{source}.csv:row:{row}", "item_index": 0,
            "version_fingerprint": "v" * 64, "kind": kind, "fingerprint": "f" * 64,
            "has_doi": doi, "paper": paper if doi else None, "batch": batch,
            "composition": comp if comp is not None else {"Co": 50.0, "Ni": 50.0}, "status": st,
            "values": {"grain_size": gs, "test_temperature": temp},
            "categories": {"test_type": test_type, "test_temperature_band": band, "microstructure": micro,
                           "phase_class": phase, "processing_method": None}}


def pair(i, gs, **kw):
    """Two grain sizes of one alloy, so that the alloy passes the grain-size rule."""
    return [cond(i, gs=gs, **kw), cond(i + 1, gs=gs * 4, **kw)]


def flag(kind, category, *records, fid=1):
    return {"id": fid, "kind": kind, "category": category, "records": list(records)}


def decide(records, flags=(), plan=PLAN, key=el.PRIMARY):
    return el.decide(plan, records, list(flags), key)


def grouped_by_dataset(*sources, plan=PLAN):
    """A plan grouping `sources` by dataset (step 7b): their records keep a group without a DOI, so a
    test of identity or the survivor rule can use a record without a DOI. Grouping never changes
    identity: Checks' paper identity reads the DOI and reference only (step 6 re-check, finding 2a)."""
    plan = copy.deepcopy(plan)
    plan["rules"]["grouping"] = [{"source": g["source"], "unit": "dataset" if g["source"] in sources else g["unit"]}
                                 for g in plan["rules"]["grouping"]]
    return plan


# --- one rule per record, the first that applies ---------------------------------------------

def test_each_rule_on_its_own():
    records = [*pair(1, 10.0),
               cond(10, kind="model_recalled"),
               cond(11, test_type="compression"), cond(12, temp=600.0), cond(13, micro="FCC+BCC"),
               cond(14, ys=False), cond(15, status={"grain_size": "not_convertible"}, gs=None),
               cond(16, temp=None), cond(17, micro=None), cond(18, test_type=None),
               cond(19, gs=0.05, comp={"Co": 40.0, "Ni": 60.0}), cond(20, gs=4.0, comp={"Co": 40.0, "Ni": 60.0}),
               cond(21, comp={"Co": 30.0, "Ni": 70.0})]
    got = decide(records, [flag("invalid_value", "physically impossible", 2)])
    assert got == {1: "single_grain_size", 2: "invalid_value", 10: "model_recalled", 11: "out_of_scope", 12: "out_of_scope",
                   13: "out_of_scope", 14: "missing_value", 15: "missing_value", 16: "scope_not_confirmed",
                   17: "scope_not_confirmed", 18: "scope_not_confirmed", 19: "excluded_by_rule",
                   20: "single_grain_size", 21: "single_grain_size"}
    # Record 1's partner is invalid, so its alloy is left with one grain size; without the flag
    # both enter.
    assert decide(records)[1] == decide(records)[2] == "in_scope"


@pytest.mark.parametrize("first, second, record", [
    ("model_recalled", "invalid_value", dict(kind="model_recalled")),
    ("invalid_value", "out_of_scope", dict(test_type="compression")),
    ("out_of_scope", "missing_value", dict(test_type="compression", ys=False)),
    ("missing_value", "scope_not_confirmed", dict(ys=False, temp=None)),
    ("scope_not_confirmed", "excluded_by_rule", dict(temp=None, gs=0.05)),
])
def test_rule_order(first, second, record):
    r = cond(5, **record)
    flags = [flag("invalid_value", "physically impossible", 5)] if "invalid_value" in (first, second) else []
    assert decide([r, *pair(1, 10.0)], flags)[5] == first


def test_excluded_and_identity_come_before_the_grain_size_count():
    """Rule 6 before rule 7 before rule 8: a record excluded by a rule, or not surviving its
    duplicate group, does not count as a grain size of its alloy."""
    records = [cond(1, gs=0.05), cond(2, gs=10.0)]
    assert decide(records) == {1: "excluded_by_rule", 2: "single_grain_size"}


def test_duplicates_are_resolved_before_grain_sizes_are_counted():
    """Owner, 2026-10-05: an alloy whose only two records are a cross-source duplicate pair at
    1.79 and 1.8 µm is not eligible: the pair is one grain size, its survivor's."""
    records = [cond(1, gs=1.79), cond(2, "controlled_duplicates", gs=1.8)]
    dup = flag("exact_duplicate", "within tolerance", 1, 2)
    assert decide(records, [dup]) == {1: "single_grain_size", 2: "duplicate_counted_once"}
    # Without the flag the two grain sizes would count as two and both enter.
    assert decide(records) == {1: "in_scope", 2: "in_scope"}


def test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them():
    tamu = dict(source="tamu_fcc", temp=None, band="room temperature", doi=False,
                status={"microstructure": "assigned_by_decision", "test_type": "assigned_from_source",
                        "phase_class": "assigned_from_source"})
    records = pair(1, 10.0, **tamu)
    assert set(decide(records).values()) == {"in_scope"}
    assert set(decide(records, key="source_only_assignments").values()) == {"scope_not_confirmed"}
    assert set(decide(records, key="scope_not_confirmed_included").values()) == {"in_scope"}


# --- identity: survivors, conflicts, ambiguous groups ---------------------------------------

def test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule():
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=40.0,
                                                                              doi=False)]
    flags = [flag("exact_duplicate", "identical values", 1, 3, fid=1),
             flag("possible_duplicate", "identical values", 2, 4, fid=2)]
    # Step 7b: grouped by paper, record 4 (no DOI) has no group: rule 5, before identity.
    assert decide(records, flags)[4] == "group_unknown"
    plan = grouped_by_dataset("controlled_duplicates")
    assert decide(records, flags, plan) == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once",
                                            4: "duplicate_counted_once"}
    sep = decide(records, flags, plan, key="possible_duplicates_separate")
    assert sep == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once", 4: "in_scope"}


def test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi():
    """Step 1 open item 3: a non-MPEA survivor. The extract record carries the paper's DOI, the
    MPEA record does not: rule 1 keeps the extract record."""
    records = [cond(1, "mpea", gs=10.0, doi=False), cond(2, "controlled_duplicates", gs=10.0, doi=True),
               cond(3, "controlled_duplicates", gs=40.0)]
    possible = [flag("possible_duplicate", "identical values", 1, 2)]
    assert decide(records, possible)[1] == "group_unknown"  # step 7b: no DOI, grouped by paper
    got = decide(records, possible, grouped_by_dataset("mpea"))
    assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}


def test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order():
    records = [cond(1, "controlled_duplicates", gs=10.0, doi=False), cond(2, "tamu_fcc", gs=10.0, doi=False),
               cond(3, "tamu_fcc", gs=40.0, doi=False)]
    assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)])[1] == "group_unknown"  # step 7b
    plan = grouped_by_dataset("controlled_duplicates")
    got = decide(records, [flag("exact_duplicate", "identical values", 1, 2)], plan)
    assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}
    reordered = copy.deepcopy(plan)
    reordered["rules"]["survivor_source_order"] = ["controlled_duplicates", "mpea", "tamu_fcc"]
    assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)], reordered)[1] == "in_scope"


@pytest.mark.parametrize("order", [["tamu_fcc"], ["mpea", "controlled_duplicates", "tamu_fcc"]])
def test_the_survivor_does_not_depend_on_database_ids_or_insertion_order(order):
    """Review finding 3: the same records with their database ids exchanged, and listed in another
    order, keep the same survivor. The final tie-breaker is stable identity (source, origin key,
    item index), never the database id; an incomplete source order is refused at the lock
    (test_checkpoints)."""
    plan = copy.deepcopy(PLAN)
    plan["rules"]["survivor_source_order"] = order
    survivors = set()
    for a_id, b_id, reverse in ((1, 2, False), (2, 1, False), (1, 2, True), (2, 1, True)):
        a = cond(a_id, "mpea", gs=10.0, row=7)
        b = cond(b_id, "controlled_duplicates", gs=10.0, row=7)
        records = [b, a] if reverse else [a, b]
        got = decide(records + [cond(9, "mpea", gs=40.0, row=8)],
                     [flag("exact_duplicate", "identical values", *sorted([a_id, b_id]))], plan)
        survivors.add(next(r["source"] for r in (a, b) if got[r["id"]] == "in_scope"))
    assert len(survivors) == 1


def test_survivor_rule_three_the_lowest_row_within_one_source():
    st = el.settings(PLAN)
    a, b = cond(1, "mpea", row=900), cond(2, "mpea", row=12)
    assert min([a, b], key=lambda r: el.survivor_key(r, st))["id"] == 2


def test_a_conflict_enters_with_neither_record():
    """Decision C (owner, 2026-10-05): neither in primary; 'conflicts_survivor_value' counts the
    group once by the survivor rule."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=40.0)]
    conflict = [flag("values_disagree", "differ beyond tolerance", 1, 3)]
    assert decide(records, conflict) == {1: "conflict_unresolved", 2: "single_grain_size",
                                         3: "conflict_unresolved", 4: "single_grain_size"}
    assert decide(records, conflict, key="conflicts_survivor_value") == {
        1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once", 4: "in_scope"}  # 4: the alloy has 10 and 40 µm
    assert decide(records, conflict, key="possible_duplicates_separate") == decide(records, conflict)


def test_an_ambiguous_group_enters_with_none_of_its_records():
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=10.1),
               cond(5, "controlled_duplicates", gs=40.0)]
    ambiguous = [flag("possible_duplicate", "several candidates", 1, 3, 4)]
    got = decide(records, ambiguous)
    assert {i: got[i] for i in (1, 3, 4)} == {1: "identity_unresolved", 3: "identity_unresolved",
                                             4: "identity_unresolved"}
    assert decide(records, ambiguous, key="possible_duplicates_separate") == {i: "in_scope" for i in (1, 2, 3, 4, 5)}
    assert decide(records, ambiguous, key="conflicts_survivor_value") == got


def test_an_ambiguous_group_keeps_its_conflict_in_every_set():
    """Review finding 4, the reviewer's example: A reports 400 with a DOI, B 400 without, C 440 with
    A's DOI (three sources), and A's alloy has another grain size. A-C is a definite conflict, A-B a
    possible duplicate, B-C no link: the group is ambiguous. The flags come from Checks' rules
    (`flags.raise_flags`), and the resulting sets are checked, not only the labels."""
    from test_flags import rec
    plan = copy.deepcopy(PLAN)
    # Step 7b: B (no DOI) is grouped by dataset so that it keeps a group; identity is unchanged.
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "controlled_duplicates", "unit": "dataset"},
                                 {"source": "tamu_fcc", "unit": "paper"}]
    full = [rec(1, "mpea", ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
            rec(3, "tamu_fcc", ys=440.0), rec(4, "mpea", gs=40.0, ys=300.0)]
    from hypocurate.pipeline.flags import raise_flags
    flags = [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
             for n, f in enumerate(raise_flags(plan, full), start=1)]
    records = [cond(1, "mpea"), cond(2, "controlled_duplicates", doi=False), cond(3, "tamu_fcc"),
               cond(4, "mpea", gs=40.0)]
    primary = decide(records, flags, plan)
    assert {i: primary[i] for i in (1, 2, 3)} == {i: "identity_unresolved" for i in (1, 2, 3)}
    separate = decide(records, flags, plan, "possible_duplicates_separate")
    # The unresolved identity is lifted, the conflict is not: A and C stay out, B enters.
    assert {i: separate[i] for i in (1, 2, 3)} == {1: "conflict_unresolved", 2: "in_scope", 3: "conflict_unresolved"}
    survivor = decide(records, flags, plan, "conflicts_survivor_value")
    assert {i: survivor[i] for i in (1, 2, 3)} == {i: "identity_unresolved" for i in (1, 2, 3)}


def _mixed(plan, full):
    from hypocurate.pipeline.flags import raise_flags
    return [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
            for n, f in enumerate(raise_flags(plan, full), start=1)]


def test_a_mixed_group_never_admits_an_exact_duplicate_twice():
    """Confirmation finding 2, the reviewer's case: A and B exact, C possible (third source, no
    paper identity), another grain size present. Definite relationships first (A-B counted once),
    then the plan's possible-duplicate choice on what remains."""
    from test_flags import rec
    full = [rec(1, "mpea"), rec(2, "controlled_duplicates"), rec(3, "tamu_fcc", doi=None), rec(4, "mpea", gs=40.0)]
    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc", doi=False),
               cond(4, "mpea", gs=40.0)]
    flags = _mixed(PLAN, full)
    both = copy.deepcopy(PLAN)  # the plan's choice: possible duplicates both counted
    for e in both["eligibility_rules"]:
        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
            e["rule"] = "in_scope"
    got = decide(records, flags, both)
    assert sorted(got[i] for i in (1, 2)) == ["duplicate_counted_once", "in_scope"]
    assert got[3] == "in_scope"
    default = decide(records, flags)  # possible counted once: one survivor of the three
    assert sum(default[i] == "in_scope" for i in (1, 2, 3)) == 1
    separate = decide(records, flags, key="possible_duplicates_separate")
    assert sorted(separate[i] for i in (1, 2)) == ["duplicate_counted_once", "in_scope"] and separate[3] == "in_scope"


def test_a_conflict_inside_a_mixed_group_stays_out_and_the_others_follow_the_plan():
    from test_flags import rec
    full = [rec(1, "mpea", ys=400.0), rec(2, "controlled_duplicates", ys=410.0), rec(3, "tamu_fcc", ys=405.0, doi=None),
            rec(4, "mpea", gs=40.0)]
    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc", doi=False),
               cond(4, "mpea", gs=40.0)]
    flags = _mixed(PLAN, full)
    for key in (el.PRIMARY, "possible_duplicates_separate"):
        got = decide(records, flags, key=key)
        assert (got[1], got[2], got[3]) == ("conflict_unresolved", "conflict_unresolved", "in_scope"), key
    survivor = decide(records, flags, key="conflicts_survivor_value")
    assert sum(survivor[i] == "in_scope" for i in (1, 2)) <= 1


def test_identity_applies_only_among_records_that_passed_the_earlier_rules():
    """Extract rows 13–14 (owner, 2026-10-05): the extract record is 'scope not confirmed'
    (rule 5 before rule 7); its MPEA twin survives. With scope not confirmed included, the
    duplicate rule still counts the measurement once."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0, temp=None)]
    possible = [flag("possible_duplicate", "identical values", 1, 3)]
    assert decide(records, possible) == {1: "in_scope", 2: "in_scope", 3: "scope_not_confirmed"}
    assert decide(records, possible, key="scope_not_confirmed_included")[3] == "duplicate_counted_once"


# --- every plan setting from the locked plan (fixed policies: eligibility.py) ------------------

def _changed(path, value):
    plan = copy.deepcopy(PLAN)
    target = plan
    for k in path[:-1]:
        target = target[k]
    target[path[-1]] = value
    return plan


@pytest.mark.parametrize("path, value, records, flags, record, before, after", [
    (("rules", "same_alloy_decimals"), 0, [cond(1, comp={"Co": 50.4, "Ni": 49.6}),
                                           cond(2, comp={"Co": 50.2, "Ni": 49.8}, gs=40.0)], [], 1,
     "single_grain_size", "in_scope"),
    (("rules", "min_grain_sizes"), 3, pair(1, 10.0), [], 1, "in_scope", "single_grain_size"),
    (("rules", "room_temperature_min"), 23.0, [*pair(1, 10.0, temp=22.0)], [], 1, "in_scope", "out_of_scope"),
    (("rules", "room_temperature_max"), 21.0, [*pair(1, 10.0)], [], 1, "in_scope", "out_of_scope"),
    (("rules", "single_phase"), "not_required", [*pair(1, 10.0, micro="FCC+BCC")], [], 1, "out_of_scope",
     "in_scope"),
    (("rules", "accepted_value_statuses"), ["converted", "assigned_from_source"],
     [*pair(1, 10.0, temp=None, band="room temperature")], [], 1, "in_scope", "scope_not_confirmed"),
    (("rules", "survivor_source_order"), ["controlled_duplicates", "mpea", "tamu_fcc"],
     [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
     [flag("exact_duplicate", "identical values", 1, 3)], 1, "in_scope", "duplicate_counted_once"),
    (("scope", "test_type"), ["compression"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
    (("scope", "phase_class"), ["BCC"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
    (("exclusion_rules",), [{"rule": "grain_size_range", "min": 20.0}], pair(1, 10.0), [], 1, "in_scope",
     "excluded_by_rule"),
    # The one plan choice left (third confirmation, owner 2026-10-06): possible duplicates counted
    # once (default) or both. (Replaces the case that chose the survivor's value for a conflict,
    # which is no longer a plan choice.)
    (("eligibility_rules",), [{**e, "rule": "in_scope"} if e["flag_kind"] == "possible_duplicate"
                              and e.get("category") is None else e for e in PLAN["eligibility_rules"]],
     [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
     [flag("possible_duplicate", "identical values", 1, 3)], 3, "duplicate_counted_once", "in_scope"),
    (("variables", "outcome", "field"), "hardness", pair(1, 10.0), [], 1, "in_scope", "missing_value"),
])
def test_each_setting_is_read_from_the_locked_plan(path, value, records, flags, record, before, after):
    """Owner, 2026-10-05: a plan whose value differs from the profile's default changes the
    decision accordingly; code that read the value from anywhere else would not."""
    assert decide(records, flags)[record] == before
    assert decide(records, flags, _changed(path, value))[record] == after


@pytest.mark.parametrize("kind, category, rule", [
    ("exact_duplicate", None, "in_scope"),  # an exact duplicate counted twice
    ("values_disagree", None, "in_scope"),  # both records of a conflict
    ("values_disagree", None, "duplicate_counted_once"),  # one record of a conflict (third confirmation)
    ("invalid_value", None, "in_scope"),  # an invalid value
    ("possible_duplicate", "several candidates", "in_scope"),  # an unresolved-identity group
    ("possible_duplicate", "several candidates", "duplicate_counted_once"),
])
def test_no_plan_can_put_these_records_in_the_primary_set(kind, category, rule):
    """Owner, 2026-10-06 (register 'primary_set_invariants'): fixed rules, not plan defaults. A
    plan that bypassed validation is refused when its settings are built, too."""
    plan = copy.deepcopy(PLAN)
    for e in plan["eligibility_rules"]:
        if e["flag_kind"] == kind and e.get("category") == category:
            e["rule"] = rule
    with pytest.raises(ValueError, match="fixed rule"):
        el.settings(plan)


@pytest.mark.parametrize("extra", [
    {"flag_kind": "exact_duplicate", "rule": "in_scope"},  # the re-check's case: prepended, first match wins
    {"flag_kind": "values_disagree", "rule": "in_scope"},
    {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "in_scope"},
    {"flag_kind": "exact_duplicate", "category": "identical values", "rule": "in_scope"},  # a narrower entry
])
def test_the_application_time_guard_refuses_duplicate_or_shadowing_entries(extra):
    """Re-check finding 3: the guard applied with the rules resolves entries exactly as the rule
    lookup does (first match, category entries first), and refuses duplicate entries, so a plan
    that bypassed validation cannot admit both copies of an exact duplicate."""
    plan = copy.deepcopy(PLAN)
    plan["eligibility_rules"].insert(0, extra)
    with pytest.raises(ValueError, match="fixed rule"):
        el.settings(plan)
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)]
    with pytest.raises(ValueError, match="fixed rule"):
        decide(records, [flag("exact_duplicate", "identical values", 1, 3)], plan)


def test_the_fixed_rules_hold_in_every_set_the_plan_names():
    """Sensitivity sets change only what their key names: conflicts keep 'neither' or the survivor's
    value; exact duplicates stay counted once; invalid values and ambiguous groups stay out except
    that 'possible_duplicates_separate' counts ambiguous groups separately."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0),
               cond(5, "tamu_fcc", doi=False), cond(6, "tamu_fcc", doi=False, gs=40.0)]
    for flags, primary_out in (([flag("exact_duplicate", "identical values", 1, 3)], {3}),
                               ([flag("invalid_value", "physically impossible", 1)], {1})):
        for key in (el.PRIMARY, *PLAN["sensitivity_analyses"]):
            got = decide(records, flags, key=key)
            assert all(got[i] != "in_scope" for i in primary_out), (key, flags)


def test_grouping_is_read_from_the_locked_plan():
    records = {r["id"]: r for r in [*pair(1, 10.0, paper="a"), *pair(3, 10.0, paper="b", comp={"Co": 40.0, "Ni": 60.0}),
                                    *pair(5, 10.0, source="tamu_fcc", doi=False, batch="x"),
                                    cond(7, source="tamu_fcc", doi=False, batch="y", gs=20.0)]}
    assert el.counts(PLAN, records, records)["n_groups"] == 3  # two papers, one dataset
    assert el.counts(PLAN, records, records, "six_batches_as_groups")["n_groups"] == 4  # two papers, two batches
    one = _changed(("rules", "grouping"), [{"source": "mpea", "unit": "dataset"},
                                           {"source": "tamu_fcc", "unit": "dataset"}])
    assert el.counts(one, records, records)["n_groups"] == 2


def test_decisions_ignore_the_domain_profile(monkeypatch):
    """With every profile constant replaced by a different value, the decisions under the same
    locked plan do not change: the decision code reads none of them."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0),
               cond(5, temp=None), cond(6, gs=0.05), *pair(7, 10.0, source="tamu_fcc", temp=None,
                                                          band="room temperature", doi=False)]
    flags = [flag("exact_duplicate", "identical values", 1, 3)]
    before = {k: decide(records, flags, key=k) for k in (el.PRIMARY, *PLAN["sensitivity_analyses"])}
    for name in dir(profile):
        if name.isupper():
            monkeypatch.setattr(profile, name, None)
    after = {k: decide(records, flags, key=k) for k in (el.PRIMARY, *PLAN["sensitivity_analyses"])}
    assert after == before


@pytest.mark.parametrize("module", ["eligibility", "flags", "inclusion", "checks", "checkpoints"])
def test_decision_code_does_not_import_the_domain_profile(module):
    tree = ast.parse((Path(el.__file__).parent / f"{module}.py").read_text())
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "hypocurate.pipeline.profile" not in imported and "profile" not in names


def test_counts_known_at_the_freeze():
    records = {r["id"]: r for r in [*pair(1, 10.0, paper="a"), *pair(3, 1.0, paper="b", comp={"Co": 40.0, "Ni": 60.0})]}
    got = el.counts(PLAN, records, records)
    assert {k: got[k] for k in ("n_records", "n_alloys", "n_alloys_two_grain_sizes", "n_groups", "resid_df")} == \
        {"n_records": 4, "n_alloys": 2, "n_alloys_two_grain_sizes": 2, "n_groups": 2, "resid_df": 1}
    assert got["check1_inputs_met"] and got["check2_inputs_met"] and not got["minimums_met"]
    assert got["minimums"] == {"records": False, "alloys": False, "groups": False, "resid_df": False}


# --- Step 7b: a record without a group (owner, 2026-10-06; register 'records_without_group') -------

def test_a_record_without_a_group_is_stored_but_not_eligible_with_its_own_rule():
    """A literature record whose paper is not known (no DOI) has no group under paper grouping: it
    gets a decision of its own, `group_unknown`, and is in no set. No group is invented."""
    records = [*pair(1, 10.0), *pair(3, 10.0, doi=False, comp={"Co": 40.0, "Ni": 60.0})]
    for key in (el.PRIMARY, *PLAN["sensitivity_analyses"]):
        rules = decide(records, key=key)
        assert (rules[3], rules[4]) == ("group_unknown", "group_unknown"), key
        assert set(rules) == {1, 2, 3, 4}  # every stored record has its decision


@pytest.mark.parametrize("record, expected", [
    (dict(doi=False, kind="model_recalled"), "model_recalled"),
    (dict(doi=False, test_type="compression"), "out_of_scope"),
    (dict(doi=False, gs=None), "missing_value"),
    (dict(doi=False, temp=None), "group_unknown"),     # scope not confirmed comes after it
    (dict(doi=False, gs=0.05), "group_unknown"),        # excluded by a rule comes after it
    (dict(doi=True, temp=None), "scope_not_confirmed"),
])
def test_group_unknown_is_rule_5_after_missing_value(record, expected):
    """Owner, 2026-10-06: rule 5, after missing value and before scope not confirmed, the menu
    exclusions, identity and the grain-size count."""
    assert decide([cond(5, **record), *pair(1, 10.0)])[5] == expected


def test_a_record_without_a_group_is_never_a_survivor():
    """Before identity: a record without a group can never be chosen as the survivor of its
    duplicate group and push out its grouped twin (the measurement would be lost). Here the plan's
    source order would prefer the extract record, which has no DOI and so no group; the Texas A&M
    record (grouped by dataset) survives, in primary and in every set."""
    plan = copy.deepcopy(PLAN)
    plan["rules"]["survivor_source_order"] = ["controlled_duplicates", "mpea", "tamu_fcc"]
    tamu = dict(source="tamu_fcc", doi=False, batch="b1")
    records = [cond(1, **tamu), cond(2, gs=40.0, **tamu), cond(3, "controlled_duplicates", doi=False)]
    possible = flag("possible_duplicate", "within tolerance", 1, 3)
    for key in (el.PRIMARY, *plan["sensitivity_analyses"]):
        rules = decide(records, [possible], plan, key)
        # In the set without the most influential paper the one group (the dataset) is the one removed.
        kept = "most_influential_paper" if key == el.INFLUENCE_KEY else "in_scope"
        assert (rules[1], rules[2], rules[3]) == (kept, kept, "group_unknown"), key


def test_the_group_is_judged_under_each_sets_own_grouping():
    """Texas A&M is grouped by dataset in primary and by batch in 'six_batches_as_groups': a record
    without a batch has a group in primary and none in that set (the same `group` function)."""
    tamu = dict(source="tamu_fcc", doi=False)
    records = [cond(1, batch="b1", **tamu), cond(2, gs=40.0, batch="b1", **tamu),
               cond(3, gs=20.0, batch=None, **tamu)]
    assert decide(records) == {1: "in_scope", 2: "in_scope", 3: "in_scope"}
    assert decide(records, key="six_batches_as_groups") == {1: "in_scope", 2: "in_scope", 3: "group_unknown"}


def test_alloys_are_counted_on_records_with_a_group():
    """Before the grain-size count (rule 9): a grain size held only by a record without a group does
    not make its alloy eligible."""
    records = [cond(1, gs=10.0), cond(2, gs=40.0, doi=False)]
    assert decide(records) == {1: "single_grain_size", 2: "group_unknown"}
