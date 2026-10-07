"""Step 8b, milestone 2: the access layer's changes (owner, 2026-10-07; safeguard changes, reviewed with 8b).

- the stage 'narrowed' (A4): a running run with no plan and code's narrowing decision of partly
  sufficient; the Analyst alone reads there; no plan can be locked there (code and database);
- the code role 'narrowing' (Q5): before the lock, `candidate_counts` only: counts of structure, no
  outcome value, no composition;
- the Analyst's facts (Q6): stored facts only, and below the minimums nothing computed from outcome
  values (the owner's standing requirement), shown on a real run through the pipeline.
The Analyst's lists, the Commentator's empty lists and the planted-value tests at each Analyst stage are
in test_access_layer.py and test_access_projected.py.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import access_world as aw
import pipeline_world as pw
from hypocurate.access import AccessDenied, bind, role_input
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints
from hypocurate.pipeline.plan import reference_plan
from hypocurate.pipeline.writes import Refused
from stats_world import run_on, small_rows


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def stage_of(engine, run_id):
    with engine.connect() as conn:
        from hypocurate.access.stage import actual_stage
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        return actual_stage(conn, run_id, status)


# --- the stage 'narrowed' (A4) -----------------------------------------------------------------------

def test_a_narrowing_decision_of_partly_sufficient_moves_the_run_to_narrowed(engine):
    world = aw.build(engine, "before_lock")
    assert stage_of(engine, world.run) == "before_lock"
    aw.code_output(world.w, world.run, "narrowing", {"result": "proceed", "reason": "no_part_without_records"})
    assert stage_of(engine, world.run) == "before_lock"  # a decision to proceed leaves the lock open
    aw.code_output(world.w, world.run, "narrowing", {"result": "partly_sufficient"}, attempt=2)
    assert stage_of(engine, world.run) == "narrowed"


def test_at_narrowed_only_the_analyst_reads(engine):
    world = aw.build(engine, "narrowed")
    for role in ("planner", "critic", "commentator"):
        with pytest.raises(AccessDenied):
            role_input(bind(engine, world.run, world.settings[role]))
    assert set(role_input(bind(engine, world.run, world.settings["analyst"]))) == {
        "claim", "domain", "sources_meta", "coverage", "analyst_facts"}
    for role in ("narrowing", "inclusion", "checks", "statistics", "gap_facts"):
        with pytest.raises(AccessDenied):
            bind_code(engine, world.run, role)


def test_no_plan_is_locked_at_narrowed_by_code_or_by_the_database(engine):
    world = aw.build(engine, "narrowed")
    with engine.connect() as conn:
        vid = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=world.run)).scalar()
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, world.run, reference_plan(vid))
    assert refused.value.code == "narrowed"
    with pytest.raises(IntegrityError, match="no plan is locked after a narrowing decision"):
        aw.lock(world.w, world.run)


# --- the code role 'narrowing' (Q5) -------------------------------------------------------------------

def test_candidate_counts_are_counts_of_structure_only(engine):
    world = aw.build(engine, "before_lock")
    got = role_input(bind_code(engine, world.run, "narrowing"))
    assert set(got) == {"candidate_counts"}
    counts = got["candidate_counts"]
    assert [c["source"] for c in counts] == ["mpea", "tamu_fcc"]
    mpea, tamu = counts
    assert tamu["readable"] is False and len(tamu["version_fingerprint"]) == 64  # the world's placeholder file
    assert mpea["readable"] and mpea["n_records"] == 8 == sum(c["n"] for c in mpea["cells"])
    for cell in mpea["cells"]:
        assert set(cell) == {"categories", "test_temperature", "status", "grain_size_present", "n"}
        assert set(cell["categories"]) == {"phase_class", "test_type", "test_temperature_band"}
    text_of = json.dumps(got)
    for v in aw.PLANTED.values():
        assert str(v) not in text_of and repr(v) not in text_of
    assert "composition" not in text_of and "Co" not in text_of  # no composition, no alloy label


@pytest.mark.parametrize("world_stage", ["curation", "analysis", "closed_without_freeze", "narrowed"])
def test_the_narrowing_role_binds_only_before_the_lock(engine, world_stage):
    world = aw.build(engine, world_stage)
    with pytest.raises(AccessDenied) as denied:
        bind_code(engine, world.run, "narrowing")
    assert denied.value.code == "empty_list"


# --- the Analyst's facts on a real run (Q6; the owner's requirement below the minimums) ---------------

def analyst_input(engine, run_id):
    with engine.connect() as conn:
        setting = conn.execute(text("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r "
                                    "AND role = 'analyst'"), dict(r=run_id)).scalar_one()
    return role_input(bind(engine, run_id, setting))


def stored_outcomes(engine, run_id) -> list[float]:
    with engine.connect() as conn:
        return [float(v) for v in conn.execute(text(
            "SELECT harmonized->'yield_strength'->>'value' FROM record WHERE extraction_run_id = :r"),
            dict(r=run_id)).scalars() if v is not None]


FROM_OUTCOMES = ("estimate", "std_error", "t", "df", "p_value", "p_value_description", "significant",
                 "estimated_power_estimated_noise")


def test_below_the_minimums_the_analysts_facts_hold_nothing_computed_from_outcomes(engine):
    rows = small_rows(3, papers=3, base=7311.0)  # distinctive outcome values
    rid = run_on(engine, rows, agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    assert out["withheld"] and out["decision"]["state"] == "below_minimums"
    got = analyst_input(engine, rid)
    facts = got["analyst_facts"]
    assert facts["kind"] == "analysis" and facts["withheld"] is True
    assert facts["decision"]["evidence_level"] == 3 and facts["decision"]["verdict"] is None
    for e in facts["analyses"]:
        assert e["withheld"] is True
        assert not set(FROM_OUTCOMES) & set(e) and "calibration" not in e and "records_found" not in e
        # The fixed-noise detection rate uses no outcome value: it stays (owner, 2026-10-07), wherever the
        # counts allow inference; where they do not, there is none to show.
        shown = e["checks"]["inference_valid"]
        assert (e["detection_fixed"] is not None) == shown and (e["estimated_power"] is not None) == shown
    assert any(e["detection_fixed"] for e in facts["analyses"])
    text_of = json.dumps(got)
    values = stored_outcomes(engine, rid)
    assert len(values) == len(rows)
    for v in values:
        assert repr(v) not in text_of and f"{v:g}" not in text_of, v


def test_above_the_minimums_the_analysts_facts_carry_the_stored_estimate(engine):
    """Positive control for the test above: the same path, not withheld, carries the numbers."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    facts = analyst_input(engine, rid)["analyst_facts"]
    pooled, stored = facts["analyses"][0], out["analyses"][0]
    # Step 8b (owner, 2026-10-07): display strings and the ready-made p-value phrase, rounded by code.
    from hypocurate.pipeline import display
    assert pooled["estimate"] == display.one_decimal(stored["estimate"]) and "p_value" not in pooled
    assert pooled["p_value_phrase"] == display.p_phrase(stored["p_value"])
    assert facts["decision"]["state"] == "exploratory" and facts["decision"]["verdict"] in ("supported",
                                                                                           "not_supported")


def test_the_analysts_facts_are_refused_until_code_has_stored_them(engine):
    rid = run_on(engine, small_rows(3, papers=3), agents=("analyst",))
    with pytest.raises(AccessDenied) as denied:
        analyst_input(engine, rid)
    assert denied.value.code == "facts_missing"
