"""Step 7: the code roles Statistics and the gap facts read through access objects (PRD 4; owner,
2026-10-05; a safeguard change, reviewed by a second model).

**Statistics** binds only at the analysis stage (a dataset frozen, the run running) and receives
exactly the locked plan and `frozen_analysis_data`: the frozen sets and, for the records in them
only, what the model needs. It sees outcome values (it must: it fits them), but never those of
records outside the frozen sets, never values as reported, never another run's data.

**The gap facts** bind at the analysis stage and when the run closed without a freeze, and receive
no outcome value (the projected-data search with planted values, as for the Planner and Critic).

**Not claimed:** anything beyond the threat model (CLAUDE.md): the access layer guards against our
own code leaking data; Statistics is trusted code, not a sandboxed reader.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import access_world as aw
from hypocurate.access import AccessDenied, role_input
from hypocurate.access.allowlist import ALLOWED, CODE_ALLOWED, ROLES, allowed
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from pipeline_fixtures import frozen_run
from test_access_projected import leaks

STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")
RECORD_KEYS = {"id", "source", "version_fingerprint", "origin", "item_index", "composition", "paper", "batch",
               "grain_size", "outcome"}


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def audit(engine, run_id, role):
    with engine.connect() as conn:
        return conn.execute(text("SELECT function, allowed, detail FROM audit_log WHERE run_id = :r AND role = :o "
                                 "ORDER BY id"), dict(r=run_id, o=role)).all()


def test_the_lists_are_the_owners_decision():
    assert {s: set(v) for s, v in CODE_ALLOWED["statistics"].items()} == {"analysis": {"plan", "frozen_analysis_data"}}
    assert {s: set(v) for s, v in CODE_ALLOWED["gap_facts"].items()} == {
        "analysis": {"plan", "decisions", "stored_record_counts", "coverage"},
        "closed_without_freeze": {"plan", "decisions", "stored_record_counts", "coverage"}}
    for stage in STAGES:
        if stage != "analysis":
            assert allowed("statistics", stage) == frozenset()
        for role in ROLES:  # no agent ever receives the statistics field
            assert "frozen_analysis_data" not in allowed(role, stage)
    assert not {"records_full", "flags_full", "results", "stage_outputs"} & set().union(*CODE_ALLOWED["gap_facts"].values())


@pytest.mark.parametrize("stage", ["queued", "before_lock", "curation", "closed_without_freeze", "final"])
def test_statistics_binds_at_no_other_stage(engine, stage):
    world = aw.build(engine, stage)
    with pytest.raises(AccessDenied) as denied:
        bind_code(engine, world.run, "statistics")
    assert denied.value.code == "empty_list"
    row = audit(engine, world.run, "statistics")[-1]
    assert (row.function, row.allowed, row.detail["code"]) == ("bind", False, "empty_list")


@pytest.mark.parametrize("stage", ["queued", "before_lock", "curation", "final", "final_without_freeze"])
def test_the_gap_facts_bind_at_no_other_stage(engine, stage):
    world = aw.build(engine, stage)
    with pytest.raises(AccessDenied):
        bind_code(engine, world.run, "gap_facts")


def test_the_complete_input_of_statistics(engine):
    """Exactly the plan and the frozen data; the frozen records with exactly the named keys; the
    world's planted outcome value is there (the positive control: Statistics fits outcomes), the
    other runs' value is not; every read is logged."""
    world = aw.build(engine, "analysis")
    got = role_input(bind_code(engine, world.run, "statistics"))
    assert set(got) == {"plan", "frozen_analysis_data"}
    data = got["frozen_analysis_data"]
    assert set(data) == {"freeze_fingerprint", "outcome_field", "sets", "records"}
    assert data["outcome_field"] == "yield_strength"
    assert {r["id"] for r in data["records"]} == set(world.records) == set(data["sets"]["primary"])
    assert all(set(r) == RECORD_KEYS for r in data["records"])
    assert any(r["outcome"] == aw.PLANTED["yield_strength"] for r in data["records"])
    assert leaks(got, [aw.OTHER]) == []  # nothing from another run
    assert not any(f.startswith(f"{aw.PLANTED['ultimate_tensile_strength']}:") for f in leaks(got, aw.PLANTED.values()))
    rows = audit(engine, world.run, "statistics")
    assert [(r.function, r.allowed) for r in rows][0] == ("bind", True)
    assert sorted((r.function, r.allowed) for r in rows[1:]) == [("frozen_analysis_data", True), ("plan", True)]


def test_records_outside_the_frozen_sets_never_reach_statistics(admin, database_url, template_database):
    """On the reference run: 1,639 records stored, the frozen sets hold 103 distinct records; only
    those are returned, and no value as reported."""
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        data = bind_code(engine, rid, "statistics").get("frozen_analysis_data")
        with engine.connect() as conn:
            members = set(conn.execute(text("SELECT DISTINCT asr.record_id FROM analysis_set_record asr JOIN analysis_set a "
                                            "ON a.id = asr.analysis_set_id WHERE a.run_id = :r"), dict(r=rid)).scalars())
            stored = conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"),
                                  dict(r=rid)).scalar()
            outside = conn.execute(text("SELECT reported FROM record WHERE extraction_run_id = :r AND id <> ALL(:m)"),
                                   dict(r=rid, m=list(members))).scalars().all()
        assert {r["id"] for r in data["records"]} == members and len(members) < stored
        assert all(set(r) == RECORD_KEYS for r in data["records"])
        flat = json.dumps(data)
        assert "reported" not in flat and "harmonized" not in flat
        # Text cells as reported for records outside the sets (titles, raw cells) never appear.
        texts = {c["text"] for rep in outside for c in rep.values() if isinstance(c, dict) and isinstance(c.get("text"), str)
                 and len(c["text"]) > 25}
        assert texts and not any(t in flat for t in texts)


@pytest.mark.parametrize("stage", ["analysis", "closed_without_freeze"])
def test_the_gap_facts_receive_no_outcome_value(engine, stage):
    """The projected-data search over the gap facts' complete input finds none of the planted
    outcome values, nor the other runs' value."""
    world = aw.build(engine, stage)
    got = role_input(bind_code(engine, world.run, "gap_facts"))
    assert set(got) == {"plan", "decisions", "stored_record_counts", "coverage"}
    assert leaks(got, list(aw.PLANTED.values()) + [aw.OTHER]) == []


def test_the_reader_itself_refuses_without_a_freeze(engine):
    """A second line behind the stage list (which already allows the field only at the analysis
    stage, where a freeze exists): the reader refuses a run with no snapshot."""
    from hypocurate.access.context import AccessContext
    from hypocurate.access.fields import Refused, frozen_analysis_data
    world = aw.build(engine, "curation")
    with engine.connect() as conn, pytest.raises(Refused) as refused:
        frozen_analysis_data(conn, AccessContext(world.run, "statistics", "analysis"))
    assert refused.value.code == "not_frozen"
