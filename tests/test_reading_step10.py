"""Step 10a (owner's review of the screenshots, 2026-10-11): the question as tested is labelled by the run's own plan
source, never by a fallback to the fixed reference plan. The owner found local run 2 (a Planner run of step 8b, the BCC
claim at 1000 °C) labelled "the fixed reference plan; not read from the claim": step 8b's Planner stage stored no
reading, so the label fell back to the fixed plan's. A Planner reading locked with no confirmation (possible only
before migration 0007) now says it predates confirmation; every other label is as before."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import checkpoints, confirmation, orchestrator, reading, run_view
from hypocurate.pipeline.plan import reference_plan


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def planner_path_run_locked_before_confirmations(engine) -> int:
    """The shape of local runs 1 and 2: not a fixed-plan run, a plan locked, no stored reading, no confirmation."""
    rid = pw.dispatched_run(engine)
    vid = pw.version_of(engine, rid)
    with engine.begin() as conn:  # a second run of the same version, on the Planner's path (fixed_plan false)
        other = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan) VALUES (:v, false) RETURNING id"),
                             dict(v=vid)).scalar_one()
        conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) SELECT :o, "
                          "source_id, source_version_id, search_status FROM run_source WHERE run_id = :r"),
                     dict(o=other, r=rid))
        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'test: superseded' "
                          "WHERE id = :r"), dict(r=rid))
        conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :o"), dict(o=other))
    checkpoints.lock_rules(engine, other, reference_plan(vid))
    return other


def label(engine, rid):
    with engine.connect() as conn:
        return reading.stored(conn, rid)


def test_a_planner_run_locked_before_confirmations_is_never_labelled_as_the_fixed_plan(engine):
    rid = planner_path_run_locked_before_confirmations(engine)
    tested = label(engine, rid)
    assert tested["label"] == reading.PREDATES_LABEL == ("the Planner's reading of the claim; not verified by code; "
                                                          "this run predates confirmation")
    assert tested["source"] == "planner"
    assert "fixed reference plan" not in str(run_view.show(engine, rid))


def test_a_fixed_plan_run_keeps_the_fixed_label(engine):
    rid = pw.locked_run(engine)
    assert label(engine, rid)["label"] == reading.LABELS["fixed"]


def test_a_waiting_planner_run_is_labelled_not_yet_confirmed_and_once_confirmed_says_by_whom(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
    assert label(engine, rid)["label"] == reading.LABELS["planner"]
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert label(engine, rid)["label"].startswith("the Planner's reading of the claim; not verified by code; "
                                                  "confirmed by Ada Reviewer on ")


def test_a_run_of_no_plan_and_no_reading_has_no_question_as_tested(engine):
    rid = pw.dispatched_run(engine)
    assert label(engine, rid) is None
