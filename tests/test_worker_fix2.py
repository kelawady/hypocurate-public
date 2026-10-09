"""Step 9b fix round 2 (owner, 2026-10-09; ChatGPT's second review, docs/reviews/step09b_recheck_chatgpt.md).

Finding 1: finishing a model call checks ownership like every other write of the child. A stale child cannot finish
an open call; the call stays started, and recovery closes it as interrupted, counted at its maximum."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate.pipeline import queue, recovery, writes
from hypocurate.pipeline.agents import spend
from hypocurate.pipeline.agents.runstage import open_stage
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
