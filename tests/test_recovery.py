"""Step 9b, b3: recovery when a run is taken up again (docs/reviews/step09b_plan.md, "Recovery"; the owner's answer of
2026-10-08, split by cause).

Recovery's bookkeeping closes every open call as `interrupted` (counted at its reserved maximum) and every running stage
as failed (`interrupted`); a run recovered more than `MAX_RECOVERIES` times fails. Then the run goes on by the normal
path, and:
- an interruption, a recording failure or any database failure while saving a call (`recording_failed`,
  `reservation_failed`): the Q3 per-role rule. The Planner is repeated once (a second loss fails the run); the Critic's
  remaining batches are skipped; after the Analyst the run completes with "explanation unavailable";
- a spending refusal (a cap was reached) stays a stop, exactly as in 9a: the Planner and the Critic fail the run, the
  Analyst completes it; no further request, never a later paid stage.
Each case is set up as the request path leaves it, the worker then claims the run and works it (in this process; the
child is a real guarded process; every call goes to the local stub)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate import worker
from hypocurate.pipeline import confirmation, queue, queries, recovery
from test_resume_step9a import agent_stage, fixed_run_after_checks, fixed_run_after_statistics, kw
from test_worker import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def open_call(engine, rid, stage_id):
    """A model call left started (the request was sent, or its recording failed)."""
    with engine.begin() as conn:
        inv = conn.execute(text("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
                                "SELECT 'run', :r, :s, s.role, ras.agent_setting_id FROM stage_result s JOIN "
                                "run_agent_setting ras ON ras.run_id = s.run_id AND ras.role = s.role WHERE s.id = :s "
                                "RETURNING id"), dict(r=rid, s=stage_id)).scalar()
        return conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                                 "price_table_version, max_cost) SELECT :r, :s, :i, role, 'claude-opus-5-5', 'p', 0.4 "
                                 "FROM stage_result WHERE id = :s RETURNING id"), dict(r=rid, s=stage_id, i=inv)).scalar()


def lost_stage(engine, rid, stage, how):
    """An agent stage left as the request path leaves it: 'interrupted' (running, its call open), 'recording_failed'
    (its call open, then the stage failed with the code), 'reservation_failed' (failed, no call)."""
    sid = agent_stage(engine, rid, stage, "running")
    if how in ("interrupted", "recording_failed"):
        open_call(engine, rid, sid)
    if how != "interrupted":
        with engine.begin() as conn:
            conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), "
                              "output = CAST(:o AS jsonb) WHERE id = :s"), dict(o=f'{{"code": "{how}"}}', s=sid))
    return sid


def take_up(engine, rid):
    """The worker claims the run (it is running, with no open claim) and works it."""
    c = queue.claim(engine, rid, "test:recovery")
    assert c is not None and c.status_before == "running"
    return worker.work(engine, c, heartbeat_interval=0.5)


def planner_left(engine, stub, how):
    """A Planner run whose Planner stage is left as `how`: 'interrupted' (running, its call open), 'recording_failed'
    (failed, its call open), 'reservation_failed' (failed, no call) or 'spending_cap_run' (failed, no call)."""
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    sid = agent_stage(engine, rid, "planner", "running")
    if how in ("interrupted", "recording_failed"):
        open_call(engine, rid, sid)
    if how != "interrupted":
        with engine.begin() as conn:
            conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), "
                              "output = CAST(:o AS jsonb) WHERE id = :s"), dict(o=f'{{"code": "{how}"}}', s=sid))
    return rid


def assert_closed_and_counted(engine, rid):
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r AND status = 'started'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0
    lost = one(engine, "SELECT coalesce(sum(max_cost), 0) FROM model_call WHERE run_id = :r AND status = 'interrupted'",
               r=rid)
    counted = one(engine, "SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)
    assert counted >= lost  # every lost call counts at its reserved maximum


# --- the Planner -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_planner_request_is_repeated_once(engine, stub, how):
    rid = planner_left(engine, stub, how)
    out = take_up(engine, rid)
    assert out["release"] == "waiting" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert requests(stub, "plan") == 1  # the one repeat
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 2
    assert_closed_and_counted(engine, rid)
    if how != "reservation_failed":
        assert one(engine, "SELECT error FROM model_call WHERE run_id = :r AND status = 'interrupted'", r=rid) == (
            "worker_stopped" if how == "interrupted" else "recording_failed")


def test_a_second_lost_planner_request_fails_the_run_with_the_reason(engine, stub):
    rid = planner_left(engine, stub, "interrupted")
    with engine.begin() as conn:  # a first repeat that was lost too
        conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), output = "
                          "'{\"code\": \"interrupted\"}' WHERE run_id = :r AND status = 'running'"), dict(r=rid))
        conn.execute(text("UPDATE model_call SET status = 'interrupted', finished_at = now(), error = 'worker_stopped' "
                          "WHERE run_id = :r"), dict(r=rid))
    agent_stage(engine, rid, "planner", "running")
    take_up(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == (
        "interrupted: the worker stopped during the Planner's request twice; dispatch the query again as a new run")
    assert requests(stub, "plan") == 0


def test_a_planner_spending_refusal_stays_a_stop_after_recovery(engine, stub):
    rid = planner_left(engine, stub, "spending_cap_run")
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert len(stub.requests) == 0


# --- the Critic -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_critic_request_skips_the_remaining_batches_and_the_run_goes_on(engine, stub, how):
    rid = fixed_run_after_checks(engine, stub)
    lost_stage(engine, rid, "critic", how)
    before = requests(stub, "classification")
    out = take_up(engine, rid)
    assert out["release"] == "finished" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "classification") == before  # not repeated
    assert requests(stub, "report") == 1  # the Analyst goes on
    assert_closed_and_counted(engine, rid)


def test_a_critic_spending_refusal_stays_a_stop_and_the_analyst_is_never_asked(engine, stub):
    rid = fixed_run_after_checks(engine, stub)
    agent_stage(engine, rid, "critic", "failed", "spending_cap_run")
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "report") == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0


# --- the Analyst ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_analyst_request_completes_the_run_with_the_explanation_unavailable(engine, stub, how):
    from hypocurate import cli_runs
    rid = fixed_run_after_statistics(engine, stub)
    lost_stage(engine, rid, "analyst", how)
    before = requests(stub, "report")
    take_up(engine, rid)
    assert (one(engine, "SELECT status FROM run WHERE id = :r", r=rid), one(engine, "SELECT outcome FROM run WHERE "
                                                                                   "id = :r", r=rid)) == (
        "completed", "sufficient")
    assert requests(stub, "report") == before
    assert cli_runs.show(engine, rid)["analyst_text"]["unavailable"].startswith("explanation unavailable")
    assert_closed_and_counted(engine, rid)


def test_an_analyst_spending_refusal_completes_the_run_as_in_9a(engine, stub):
    rid = fixed_run_after_statistics(engine, stub)
    agent_stage(engine, rid, "analyst", "failed", "spending_cap_run")
    before = requests(stub, "report")
    take_up(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "report") == before


def test_a_lost_analyst_request_on_the_partly_sufficient_path_completes_and_creates_the_narrower_question(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, **kw(stub)).answer)
    lost_stage(engine, rid, "analyst", "recording_failed")
    take_up(engine, rid)
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) == "partly_sufficient"
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1


# --- recovery's own rules -------------------------------------------------------------------------------------

def test_a_run_recovered_more_than_max_recoveries_times_fails(engine, stub):
    rid = fixed_run_after_checks(engine, stub)
    for i in range(recovery.MAX_RECOVERIES):
        c = queue.claim(engine, rid, f"test:{i}")
        queue.release(engine, c, "stopped_for_recovery")
    out = take_up(engine, rid)
    assert out["release"] == "finished"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith(
        f"attempts_exhausted: the run stopped at curation {recovery.MAX_RECOVERIES + 1} times without finishing")
    assert len([r for r in stub.requests if "[[ ## report ## ]]" in r["raw"].decode()]) == 0


def test_recovery_writes_no_plan_record_set_freeze_or_confirmation(engine, stub):
    """Recovery is bookkeeping only (a source scan of the module: it never writes those tables)."""
    import pathlib
    source = pathlib.Path(recovery.__file__).read_text(encoding="utf-8")
    for table in ("plan", "record", "analysis_set", "run_snapshot", "rules_confirmation", "run_record"):
        assert f"INSERT INTO {table} " not in source and f"INSERT INTO {table}(" not in source


def test_what_recovery_found_is_recorded_on_the_claim(engine, stub):
    rid = planner_left(engine, stub, "interrupted")
    take_up(engine, rid)
    found = one(engine, "SELECT found FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid)
    assert found["calls_closed"] == 1 and found["stages_closed"] == 1 and found["recoveries"] == 1


def test_a_repeat_that_would_pass_the_run_cap_is_refused_before_it_is_sent(engine, stub):
    """Caps across crashes: the lost call counts at its maximum, so a repeat past the cap is never sent."""
    rid = planner_left(engine, stub, "interrupted")
    sid = one(engine, "SELECT id FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid)
    open_call_cost = Decimal("1.99")
    with engine.begin() as conn:  # a second lost call of the same stage, near the cap
        inv = conn.execute(text("SELECT invocation_id FROM model_call WHERE run_id = :r"), dict(r=rid)).scalar()
        conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                          "price_table_version, max_cost) VALUES (:r, :s, :i, 'planner', 'claude-opus-5-5', 'p', :m)"),
                     dict(r=rid, s=sid, i=inv, m=open_call_cost))
    take_up(engine, rid)
    assert requests(stub, "plan") == 0
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")


def test_the_interrupted_explanation_uses_the_analysts_own_wording():
    from hypocurate.pipeline.agents.analyst import UNAVAILABLE
    assert recovery.ANALYST_INTERRUPTED == f"{UNAVAILABLE} (interrupted)"


def test_the_sweep_finishes_a_narrower_question_left_by_a_stop_and_never_makes_a_second(engine, stub):
    from hypocurate.pipeline import completion, narrowing
    from hypocurate.pipeline.agents import analyst, planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, **kw(stub)).answer)
    analyst.run_analyst(engine, rid, **kw(stub))
    completion.copy_partly_sufficient(engine, rid)  # the stop: completed, no narrower question
    assert len(recovery.finish_narrower_questions(engine)) == 1
    assert recovery.finish_narrower_questions(engine) == []
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
