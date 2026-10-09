"""Step 9b, b2: claims and the heartbeat (docs/reviews/step09b_plan.md, "Claims, heartbeat, and dead").

A worker claims a run by taking, without waiting, a session advisory lock (CLAIM, run) on its own lease connection and
checking that (WORK, run) is free; then, in one locked transaction, it re-checks the run, closes a stale claim as
`lost`, records its claim and starts the run (queued -> running, or a confirmed waiting run -> running). Two workers
can never both hold a run."""
from __future__ import annotations

import threading
import time

import pytest
from sqlalchemy import text

from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queue
from model_builder import World


@pytest.fixture
def w(db):
    return World(db)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def waiting_run(w, confirmed=False):
    rid = w.running()
    sid = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=sid)
    narrowed = w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
    w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)
    if confirmed:  # confirmed by a named person, still waiting to be taken up
        from model_builder import FP
        w.run_sql("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                  "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, '{}', 'shown')",
                  r=rid, fp=FP, p=sid, n=narrowed)
    return rid


def test_a_queued_run_is_claimed_and_started(w):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    try:
        assert (c.run_id, c.status_before) == (rid, "queued")
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
        assert one(w.e, "SELECT worker FROM run_claim WHERE id = :c AND released_at IS NULL", c=c.id) == "host:1"
    finally:
        c.lease.close()


def test_two_workers_never_hold_one_run(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    try:
        assert first.run_id == rid
        assert queue.claim_next(w.e, "host:2") is None  # the run is held; nothing else to claim
    finally:
        first.lease.close()


def test_claims_at_the_same_moment_give_the_run_to_one_worker(w):
    rid = w.run()
    got, barrier = [], threading.Barrier(4)

    def claim(name):
        barrier.wait()
        c = queue.claim_next(w.e, name)
        got.append(c)

    threads = [threading.Thread(target=claim, args=(f"host:{i}",)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    held = [c for c in got if c is not None]
    try:
        assert len(held) == 1 and held[0].run_id == rid
        assert one(w.e, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    finally:
        for c in held:
            c.lease.close()


def test_a_run_whose_work_lock_is_held_by_an_orphan_child_is_not_claimed(w):
    rid = w.run()
    with w.e.connect() as orphan:
        assert orphan.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
        assert queue.claim_next(w.e, "host:1") is None
        orphan.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=queue.work_key(rid)))
        orphan.commit()
    c = queue.claim_next(w.e, "host:1")
    assert c is not None and c.run_id == rid
    c.lease.close()


def test_a_waiting_run_is_claimed_only_once_confirmed(w):
    rid = waiting_run(w)
    assert queue.claim_next(w.e, "host:1") is None
    other = waiting_run(w, confirmed=True)
    c = queue.claim_next(w.e, "host:1")
    try:
        assert (c.run_id, c.status_before) == (other, "waiting")
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=other) == "running"
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    finally:
        c.lease.close()


def test_a_running_run_with_a_live_claim_is_left_alone_and_a_stale_one_is_taken_over(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    first.lease.close()  # the worker's lease connection is gone (its process died), the claim row stays open
    assert queue.claim_next(w.e, "host:2") is None  # its heartbeat is fresh: not dead yet
    time.sleep(1.2)
    c = queue.claim_next(w.e, "host:2", stale_seconds=1)
    try:
        assert (c.run_id, c.status_before) == (rid, "running")
        assert one(w.e, "SELECT release_reason FROM run_claim WHERE id = :c", c=first.id) == "lost"
    finally:
        c.lease.close()


def test_a_claim_released_for_recovery_is_claimable_at_once(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    queue.release(w.e, first, "stopped_for_recovery")
    c = queue.claim_next(w.e, "host:2")
    try:
        assert c.run_id == rid and c.status_before == "running"
    finally:
        c.lease.close()


@pytest.mark.parametrize("reason", ["finished", "waiting"])
def test_a_released_claim_frees_both_locks(w, reason):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    queue.release(w.e, c, reason)
    with w.e.connect() as conn:
        assert conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.claim_key(rid))).scalar()
        conn.execute(text("SELECT pg_advisory_unlock_all()"))
    assert one(w.e, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == reason


def test_the_heartbeat_thread_beats_and_stops(w):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    first = one(w.e, "SELECT heartbeat_at FROM run_claim WHERE id = :c", c=c.id)
    beat = queue.Heartbeat(w.e, c.id, interval=0.2)
    beat.start()
    time.sleep(1.0)
    beat.stop()
    later = one(w.e, "SELECT heartbeat_at FROM run_claim WHERE id = :c", c=c.id)
    assert later > first and not beat.is_alive()
    c.lease.close()


def test_the_time_since_the_last_write_counts_stage_and_call_rows(w):
    rid = w.running(agents=True)
    sid = w.stage(rid, "planner", "planner")
    time.sleep(1.1)
    with w.e.connect() as conn:
        quiet = queue.seconds_since_last_write(conn, rid)
    w.call(rid, sid)
    with w.e.connect() as conn:
        assert quiet >= 1 and queue.seconds_since_last_write(conn, rid) < quiet


def test_the_keys_never_meet_other_locks():
    from hypocurate.pipeline.agents.spend import MONTH_LOCK_KEY
    from hypocurate.pipeline.confirmation import SOURCES_LOCK_KEY
    keys = {queue.claim_key(1), queue.work_key(1), queue.claim_key(2 ** 31), queue.work_key(2 ** 31)}
    assert len(keys) == 4 and not keys & {MONTH_LOCK_KEY, SOURCES_LOCK_KEY}
    with pytest.raises(ValueError):
        queue.claim_key(2 ** 32)


# --- added after the mutation checks (q02, q03): each guard reached on its own ---------------------------------

def test_the_claim_transaction_itself_refuses_a_run_with_a_live_claim(w):
    """Mutation q02: the candidate query leaves out a run with a live claim, so the claim transaction's own re-check
    (the race between the query and the transaction) is reached directly here."""
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    try:
        assert queue._take(w.e, rid, "host:2", queue.STALE_SECONDS) is None
        assert one(w.e, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    finally:
        first.lease.close()


def test_the_claim_transaction_itself_refuses_an_unconfirmed_waiting_run(w):
    rid = waiting_run(w)
    assert queue._take(w.e, rid, "host:1", queue.STALE_SECONDS) is None
    assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_an_unconfirmed_waiting_run_is_not_even_a_candidate(w):
    """Mutation q03: the candidate query's own rule (the claim transaction would refuse it too)."""
    rid = waiting_run(w)
    confirmed = waiting_run(w, confirmed=True)
    with w.e.connect() as conn:
        listed = [r for (r,) in conn.execute(queue._CANDIDATES, dict(stale=queue.STALE_SECONDS, only=None)).all()]
    assert confirmed in listed and rid not in listed
