"""Step 9b fix round 2 (owner, 2026-10-09; ChatGPT's second review, docs/reviews/step09b_recheck_chatgpt.md).

Finding 1: finishing a model call checks ownership like every other write of the child. A stale child cannot finish
an open call; the call stays started, and recovery closes it as interrupted, counted at its maximum.

Finding 2: a refusal whose transaction committed, but whose acknowledgement never reached Python (a connection error
after the commit), leaves the agent's stage failed with `reservation_failed`, a recoverable code. Recovery must still
treat it as the spending stop it was: the run fails `spending_refused`, nothing is repeated or sent, the Analyst is
never asked after the Critic, also once the month has changed; and the stage's stored history is kept as it was."""
from __future__ import annotations

from decimal import Decimal

import psycopg
import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate.pipeline import queue, recovery, writes
from hypocurate.pipeline.agents import spend
from hypocurate.pipeline.agents.runstage import open_stage
from hypocurate.pipeline import orchestrator, queries
from test_recovery_spending import change_the_month, fill_the_month, flagged, requests, take_up  # noqa: F401
from test_worker import engine, stub  # noqa: F401 (fixtures)
from test_worker_fix1 import owned


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


@pytest.mark.parametrize("how", ["work_lock_gone", "taken_over"])
def test_a_stale_child_cannot_finish_an_open_call_and_recovery_closes_it_at_its_maximum(engine, stub, monkeypatch, how):
    rid = to.dispatched(engine, fixed_plan=True)
    c, holder, pid = owned(engine, rid)
    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
    _, inv = open_stage(engine, rid, "analyst", "analyst")
    call = spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))  # owned: reserved
    if how == "work_lock_gone":
        holder.invalidate()  # the work lock's session ends; the provider's reply arrives after
    else:
        queue.release(engine, c, "lost")  # the claim is closed by a takeover
    with pytest.raises(spend.ClaimLost):
        spend.finish(engine, call, "succeeded", input_tokens=10, output_tokens=10, cached_tokens=0,
                     cost=Decimal("0.001"))
    with pytest.raises(spend.ClaimLost):
        spend.finish(engine, call, "failed", code="provider_unavailable")
    assert one(engine, "SELECT status FROM model_call WHERE id = :c", c=call) == "started"
    if how == "work_lock_gone":
        queue.release(engine, c, "lost")
    else:
        holder.invalidate()
    c.lease.close()
    monkeypatch.setattr(writes, "OWNER", None)  # recovery runs as the next worker's own code
    recovery.recover(engine, rid)
    assert one(engine, "SELECT status FROM model_call WHERE id = :c", c=call) == "interrupted"
    assert one(engine, "SELECT input_tokens IS NULL AND cost IS NULL FROM model_call WHERE id = :c", c=call)
    assert one(engine, "SELECT coalesce(cost, max_cost) FROM model_call WHERE id = :c", c=call) == Decimal("0.01")


def test_an_owner_still_finishes_its_call(engine, stub, monkeypatch):
    rid = to.dispatched(engine, fixed_plan=True)
    c, holder, pid = owned(engine, rid)
    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
    _, inv = open_stage(engine, rid, "analyst", "analyst")
    call = spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
    spend.finish(engine, call, "succeeded", input_tokens=10, output_tokens=10, cached_tokens=0, cost=Decimal("0.001"))
    assert one(engine, "SELECT status FROM model_call WHERE id = :c", c=call) == "succeeded"
    holder.invalidate()
    c.lease.close()


# --- finding 2 --------------------------------------------------------------------------------------------------

def lost_acknowledgement(patch):
    """The refusal's transaction commits (its audit row with it); then the connection fails before Python hears."""
    real = spend.run_transaction

    def flaky(engine, fn):
        outcome = real(engine, fn)
        if isinstance(outcome, tuple) and outcome[0] == "refused":
            raise psycopg.OperationalError("test: the connection was lost after the commit")
        return outcome
    patch.setattr(spend, "run_transaction", flaky)


def stopped_with_reservation_failed(engine, stub, monkeypatch, stage, rid):
    """Runs the orchestrator in this process to the refusal at `stage`; the stage is saved failed
    `reservation_failed` and the run stays open (a stop), with the refusal's record committed."""
    with monkeypatch.context() as patch:  # only this run of the orchestrator, in this process
        lost_acknowledgement(patch)
        report = orchestrator.run(engine, rid, client_options=__import__("stub_provider").client_options(stub))
    assert report.failure and report.failure.startswith("reservation_failed")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    history = [tuple(r) for r in engine.connect().execute(text(
        "SELECT id, status, output->>'code' FROM stage_result WHERE run_id = :r AND stage = :s ORDER BY id"),
        dict(r=rid, s=stage)).all()]
    assert history[-1][1:] == ("failed", "reservation_failed")
    assert one(engine, "SELECT count(*) FROM audit_log WHERE function = 'model_call' AND NOT allowed AND run_id = :r "
                       "AND detail->>'code' = ANY(:c)", r=rid, c=list(recovery.SPENDING_CODES)) == 1
    return history


@pytest.mark.parametrize("cause", ["ceiling", "month", "month_then_changed"])
def test_a_planner_refusal_whose_answer_was_lost_stays_a_stop_after_recovery(engine, stub, monkeypatch, cause):
    stub.respond(to.responder(to.planner_body()))
    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001") if cause == "ceiling" else None)
    other = fill_the_month(engine, rid) if cause != "ceiling" else None
    history = stopped_with_reservation_failed(engine, stub, monkeypatch, "planner", rid)
    if cause == "month_then_changed":
        change_the_month(engine, other)
    take_up(engine, rid)
    assert (one(engine, "SELECT coalesce(failure_reason, status) FROM run WHERE id = :r", r=rid) or "").startswith(
        "spending_refused: ")
    assert requests(stub, "plan") == 0  # never sent, before or after the recovery (no repeat)
    assert [tuple(r) for r in engine.connect().execute(text(
        "SELECT id, status, output->>'code' FROM stage_result WHERE run_id = :r AND stage = 'planner' ORDER BY id"),
        dict(r=rid)).all()] == history  # the stored history is kept as it was


@pytest.mark.parametrize("cause", ["ceiling", "month", "month_then_changed"])
def test_a_critic_refusal_whose_answer_was_lost_stays_a_stop_and_the_analyst_is_never_asked(flagged, stub,
                                                                                            monkeypatch, cause):
    from test_critic import SOURCES
    engine = flagged
    stub.respond(to.responder())
    q = queries.create(engine, to.FCC_CLAIM, SOURCES)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True,
                           ceiling=Decimal("0.0001") if cause == "ceiling" else None)
    other = None
    if cause != "ceiling":
        q2 = queries.create(engine, to.FCC_CLAIM, SOURCES)
        queries.submit(engine, q2.version_id)
        queries.confirm_domain(engine, q2.version_id, by="Ada Reviewer")
        other = queries.dispatch(engine, q2.version_id, fixed_plan=True, constructed_test_data=True)
        queries.start(engine, other)
        _, inv = open_stage(engine, other, "analyst", "analyst")
        with engine.begin() as conn:
            for _ in range(int(spend.MONTH_CAP_USD // 2)):
                conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                                  "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, "
                                  "'claude-opus-5-5', 'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
    history = stopped_with_reservation_failed(engine, stub, monkeypatch, "critic", rid)
    if cause == "month_then_changed":
        change_the_month(engine, other)
    take_up(engine, rid)
    assert (one(engine, "SELECT coalesce(failure_reason, status) FROM run WHERE id = :r", r=rid) or "").startswith(
        "spending_refused: ")
    assert requests(stub, "classification") == 0 and requests(stub, "report") == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0
    assert [tuple(r) for r in engine.connect().execute(text(
        "SELECT id, status, output->>'code' FROM stage_result WHERE run_id = :r AND stage = 'critic' ORDER BY id"),
        dict(r=rid)).all()] == history
