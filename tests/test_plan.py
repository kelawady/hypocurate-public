"""Step 6: the plan model (PRD 5.1). Plans follow PLAN_SCHEMA exactly; every setting that
affects eligibility or grouping is a value of the plan; the default plan takes each value from
the domain profile's named setting (owner, 2026-10-05)."""
from __future__ import annotations

import copy

import pytest

from hypocurate.access.allowlist import PLAN_SCHEMA
from hypocurate.access.fields import project
from hypocurate.pipeline import plan as pl
from hypocurate.pipeline import profile as p
from hypocurate.pipeline.plan import PlanError, default_plan, fingerprint, reference_plan, tags_for, validate


def test_the_default_plan_is_valid_and_is_its_own_projection():
    content = default_plan(7)
    assert validate(content) == content
    assert project(content, PLAN_SCHEMA) == content
    assert set(content) == set(PLAN_SCHEMA) == set(pl.PARTS)
    assert set(content["rules"]) == set(PLAN_SCHEMA["rules"]) == set(pl.RULES)


def test_the_reference_plan_is_the_default_plan_under_the_owners_decisions():
    ref = reference_plan(7)
    assert ref == default_plan(7)
    assert ref["scope"] == {"alloy_class": ["multi-principal-element (high-entropy) alloy"],
                            "temperature_band": ["room temperature"], "test_type": ["tension"], "phase_class": ["FCC"]}
    assert ref["exclusion_rules"] == [{"rule": "grain_size_range", "min": 0.1}]
    assert ref["sufficiency"] == {"option": "fixed_minimum", "min_records": 30, "min_alloys": 5, "min_groups": 10,
                                  "min_resid_df": 10}
    assert ref["rules"] == {
        "same_alloy_decimals": 1, "duplicate_tolerance": 0.02,
        "survivor_source_order": ["mpea", "tamu_fcc", "controlled_duplicates"], "min_grain_sizes": 2,
        "room_temperature_min": 20.0, "room_temperature_max": 25.0, "single_phase": "required",
        "accepted_value_statuses": ["converted", "assigned_from_source", "assigned_by_decision"],
        "grouping": [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "dataset"},
                     {"source": "controlled_duplicates", "unit": "paper"}]}
    assert ref["sensitivity_analyses"] == [
        "no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
        "source_only_assignments", "scope_not_confirmed_included", "possible_duplicates_separate",
        "conflicts_survivor_value"]
    assert ref["eligibility_rules"] == [
        {"flag_kind": "invalid_value", "rule": "invalid_value"},
        {"flag_kind": "exact_duplicate", "rule": "duplicate_counted_once"},
        {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "identity_unresolved"},
        {"flag_kind": "possible_duplicate", "rule": "duplicate_counted_once"},
        {"flag_kind": "values_disagree", "rule": "conflict_unresolved"}]
    assert ref["profile"] == {"name": "grain_size_strengthening", "version": p.PROFILE_VERSION}
    assert ref["model"] == {"name": "hall_petch_alloy_intercepts", "null": "k <= 0", "alternative": "k > 0",
                            "alpha": 0.05}
    assert ref["variables"]["predictor"] == {"field": "grain_size", "unit": "µm", "transformation": "inverse_square_root"}


def test_each_default_comes_from_its_named_setting(monkeypatch):
    """Changing a profile constant changes the default plan: the plan reads it from there."""
    for name, path, new in [("PERMITTED_TEST_TYPES", ("scope", "test_type"), ("compression",)),
                            ("GRAIN_SIZE_FLOOR_UM", ("exclusion_rules", 0, "min"), 0.5),
                            ("DUPLICATE_TOLERANCE", ("rules", "duplicate_tolerance"), 0.05),
                            ("MIN_GRAIN_SIZES_PER_ALLOY", ("rules", "min_grain_sizes"), 3),
                            ("SAME_ALLOY_DECIMALS_DEFAULT", ("rules", "same_alloy_decimals"), 0),
                            ("ROOM_TEMPERATURE_C", ("rules", "room_temperature_max"), (18.0, 27.0)),
                            ("SURVIVOR_SOURCE_ORDER", ("rules", "survivor_source_order"),
                             ("tamu_fcc", "mpea", "controlled_duplicates")),
                            ("ACCEPTED_VALUE_STATUSES", ("rules", "accepted_value_statuses"), ("converted",)),
                            ("PROFILE_VERSION", ("profile", "version"), 99)]:
        with monkeypatch.context() as m:
            m.setattr(p, name, new)
            value = default_plan(1)
            for k in path:
                value = value[k]
            expected = new[1] if name == "ROOM_TEMPERATURE_C" else list(new) if isinstance(new, tuple) else new
            assert value == expected, name
    with monkeypatch.context() as m:
        m.setattr(p, "FIXED_MINIMUMS", {"min_records": 3, "min_alloys": 2, "min_groups": 2, "min_resid_df": 1})
        assert default_plan(1)["sufficiency"]["min_records"] == 3


def _set_rule(content, kind, category, rule):
    for e in content["eligibility_rules"]:
        if e["flag_kind"] == kind and e.get("category") == category:
            e["rule"] = rule


def test_the_plan_choices_that_remain():
    """Conflicts: neither (default) or the survivor's value counted once. Possible duplicates:
    counted once (default) or counted separately."""
    for kind, rule in (("values_disagree", "duplicate_counted_once"), ("possible_duplicate", "in_scope")):
        content = default_plan(1)
        _set_rule(content, kind, None, rule)
        validate(content)


@pytest.mark.parametrize("change, message", [
    (lambda c: c.update(extra=1), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(note="free text"), "outside PLAN_SCHEMA"),
    (lambda c: c["scope"].update(test_type=["tension", "bending"]), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(same_alloy_decimals=1.5), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(survivor_source_order=["mpea", "elsewhere"]), "outside PLAN_SCHEMA"),
    (lambda c: c.pop("rules"), "lacks rules"),
    (lambda c: c["rules"].pop("grouping"), "rules are exactly"),
    (lambda c: c["scope"].update(temperature_band=["cryogenic"]), "room-temperature band only"),
    (lambda c: c["rules"].update(min_grain_sizes=1), "out of range"),
    (lambda c: c["rules"].update(room_temperature_min=30.0), "out of range"),
    (lambda c: c["rules"].update(survivor_source_order=["mpea", "mpea"]), "each source once"),
    (lambda c: c["rules"].update(accepted_value_statuses=["assigned_by_decision"]), "include 'converted'"),
    (lambda c: c["sufficiency"].update(min_records=0), "at least 1"),
    (lambda c: c["exclusion_rules"].append({"rule": "grain_size_range"}), "minimum or a maximum"),
    (lambda c: c["eligibility_rules"].append({"flag_kind": "values_disagree", "rule": "in_scope"}), "one eligibility"),
    # Owner, 2026-10-06: fixed rules a plan can never change (register 'primary_set_invariants').
    (lambda c: _set_rule(c, "values_disagree", None, "in_scope"), "fixed rule"),
    (lambda c: _set_rule(c, "exact_duplicate", None, "in_scope"), "fixed rule"),
    (lambda c: _set_rule(c, "invalid_value", None, "in_scope"), "fixed rule"),
    (lambda c: _set_rule(c, "possible_duplicate", "several candidates", "in_scope"), "fixed rule"),
    (lambda c: _set_rule(c, "possible_duplicate", "several candidates", "duplicate_counted_once"), "fixed rule"),
    (lambda c: c.update(eligibility_rules=[e for e in c["eligibility_rules"] if e["flag_kind"] != "values_disagree"]),
     "fixed rule"),
    (lambda c: c.update(eligibility_rules=[e for e in c["eligibility_rules"] if e["flag_kind"] != "invalid_value"]),
     "fixed rule"),
    (lambda c: c["eligibility_rules"].append({"flag_kind": "exact_duplicate", "category": "within tolerance",
                                              "rule": "in_scope"}), "fixed rule"),
    (lambda c: c["eligibility_rules"].append({"flag_kind": "model_recalled", "rule": "out_of_scope"}),
     "flag rule codes"),
    (lambda c: c["sensitivity_analyses"].append("removal_after_lock"), "named once each"),
    (lambda c: c["model"].update(alpha=1.5), "threshold"),
    (lambda c: c["variables"]["predictor"].update(field="hardness"), "grain size"),
])
def test_invalid_plans_are_refused(change, message):
    content = default_plan(1)
    change(content)
    with pytest.raises(PlanError, match=message):
        validate(content)


def test_the_fingerprint_is_the_canonical_json_and_changes_with_any_value():
    a, b = default_plan(1), default_plan(1)
    b = dict(reversed(list(b.items())))  # key order does not matter
    assert fingerprint(a) == fingerprint(b) and len(fingerprint(a)) == 64
    c = copy.deepcopy(a)
    c["rules"]["duplicate_tolerance"] = 0.021
    assert fingerprint(c) != fingerprint(a)


def test_three_tags_one_per_kind_from_the_plan():
    assert tags_for(default_plan(1)) == {"property": "yield strength",
                                         "alloy_class": "multi-principal-element (high-entropy) alloy",
                                         "test_condition": "room-temperature tension"}
    for value in tags_for(default_plan(1)).values():
        assert any(value in values for values in p.TAG_STARTING_LISTS.values())
    two = default_plan(1)
    two["scope"]["test_type"] = ["tension", "compression"]
    with pytest.raises(PlanError, match="three tags"):
        tags_for(two)
