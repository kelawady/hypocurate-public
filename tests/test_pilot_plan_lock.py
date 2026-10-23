"""Sprint 2 pilot, merge review A2 and C2 (2026-10-23): the plan schema now admits the pilot source key, so the rules
lock must refuse a plan that names a pilot source the run did not choose; an ordinary Sprint 1 plan (fixed or from
the Planner's template) is unchanged and still locks; a pilot plan built first does not change a later Sprint 1 plan in
the same process."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline.agents.planner import build_plan
from hypocurate.pipeline.writes import Refused

RT = {"band": "room temperature"}
SCOPE = {"alloy_class": ["multi-principal-element (high-entropy) alloy"], "phase_class": ["FCC"],
         "test_type": ["tension"], "temperature_band": [RT]}


@pytest.fixture
def engine(db):
    pw.registered(db)
    return db


def _names_pilot(plan) -> bool:
    return "extracted_pilot" in plan["rules"]["survivor_source_order"] or any(
        g["source"] == "extracted_pilot" for g in plan["rules"]["grouping"])


def test_an_ordinary_sprint1_plan_validates_unchanged_and_names_no_pilot_source(engine):
    rid = pw.dispatched_run(engine)
    v = pw.version_of(engine, rid)
    fixed = plans.reference_plan(v)
    planner = build_plan(v, SCOPE, "yield_strength", [{"rule": "grain_size_range", "min": 0.1}], "fixed_minimum")
    for p in (fixed, planner):
        assert plans.validate(p) == p and not _names_pilot(p)
    assert checkpoints.lock_rules(engine, rid, fixed) == plans.fingerprint(fixed)


@pytest.mark.parametrize("where", ["survivor_source_order", "grouping", "both"])
def test_a_plan_naming_the_pilot_source_on_a_run_without_it_is_refused(engine, where):
    rid = pw.dispatched_run(engine, sources=("mpea", "tamu_fcc"))
    p = plans.reference_plan(pw.version_of(engine, rid))
    if where in ("survivor_source_order", "both"):
        p["rules"]["survivor_source_order"].append("extracted_pilot")
    if where in ("grouping", "both"):
        p["rules"]["grouping"].append({"source": "extracted_pilot", "unit": "paper"})
    plans.validate(p)  # the schema admits the key...
    with pytest.raises(Refused) as refused:  # ...the lock refuses it for a run that did not choose it
        checkpoints.lock_rules(engine, rid, p)
    assert refused.value.code == "invalid_plan" and "pilot source the run did not choose" in refused.value.message
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM plan WHERE run_id = :r"), dict(r=rid)).scalar() == 0


def test_a_pilot_plan_built_first_does_not_change_a_later_sprint1_plan():
    before = plans.reference_plan(7)
    pilot = plans.with_pilot_sources(plans.reference_plan(7), ("mpea", "extracted_pilot"))
    assert _names_pilot(pilot) and plans.reference_plan(7) == before and not _names_pilot(plans.reference_plan(7))
    assert plans.with_pilot_sources(plans.reference_plan(7), ("mpea",)) == before


def test_the_locks_pilot_list_is_a_code_list_matching_the_profile():
    """The lock reads the pilot keys from the plan vocabulary, not the profile (Sprint 1's rule:
    test_eligibility.py::test_decision_code_does_not_import_the_domain_profile); the two lists agree."""
    from hypocurate.access.vocabulary import PILOT_SOURCE_KEYS, SOURCE_KEYS
    from hypocurate.pipeline import profile
    assert PILOT_SOURCE_KEYS == frozenset(profile.PILOT_SOURCES) and PILOT_SOURCE_KEYS <= SOURCE_KEYS
