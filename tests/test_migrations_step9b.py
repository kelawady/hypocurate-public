"""Step 9b: migration 0008, `run_claim` (the step 9 plan approved by the owner on 2026-10-08; docs/reviews/step09b_plan.md).

A claim is a worker's hold on one run: who (worker), the guarded child's pid, when it was claimed, its heartbeat (R6:
written on the claim row, never the run row), and how it was released, once. One open claim per run. Claims are
history: never deleted. 0001 to 0007 untouched; up, down, up gives the same schema; the downgrade refuses while a
claim exists; a failed upgrade changes nothing."""
from __future__ import annotations

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")


def m0008():
    return SCRIPTS.get_revision("0008").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


def claim(w, rid, worker="host:1"):
    return w.val("INSERT INTO run_claim (run_id, worker) VALUES (:r, :w) RETURNING id", r=rid, w=worker)


def release(w, cid, reason="finished"):
    w.run_sql("UPDATE run_claim SET released_at = now(), release_reason = :x WHERE id = :c", x=reason, c=cid)


# --- the migration ------------------------------------------------------------------------------------------

def test_0008_is_the_head_and_follows_0007():
    assert migrate.head_revision() == "0008" and m0008().down_revision == "0007"


def test_0008_replaces_no_earlier_function():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006", "0007")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m0008().FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m0008().FUNCTIONS)


def test_up_down_up_restores_0007(engine):
    migrate.upgrade(engine, "0007")
    at_0007 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0007")
    assert snapshot(engine) == at_0007
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0007")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_claim_insert() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before and migrate.current_revision(engine) == "0007"


def test_the_downgrade_refuses_while_a_claim_exists(db):
    w = World(db)
    claim(w, w.run())
    before = snapshot(db)
    with pytest.raises(Exception, match="0008 is in use"):
        migrate.downgrade(db, "0007")
    assert snapshot(db) == before and migrate.current_revision(db) == "0008"


def test_the_release_reasons_are_the_codes():
    from hypocurate.pipeline import queue
    assert m0008().RELEASE_REASONS == REASONS == queue.RELEASE_REASONS


# --- a claim ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["queued", "running", "waiting"])
def test_an_open_run_is_claimed_with_the_databases_times(w, status):
    rid = w.run()
    if status != "queued":
        w.start(rid)
    if status == "waiting":  # a Planner run at its wait (0007)
        sid = w.stage(rid, "planner", "planner")
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=sid)
        w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
        w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)
    cid = w.val("INSERT INTO run_claim (run_id, worker, claimed_at, heartbeat_at) VALUES (:r, 'host:1', "
                "'2000-01-01', '2000-01-01') RETURNING id", r=rid)
    assert w.val("SELECT claimed_at > '2001-01-01' AND heartbeat_at = claimed_at FROM run_claim WHERE id = :c", c=cid)


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_an_ended_run_is_never_claimed(w, status):
    rid = w.running()
    if status == "failed":
        w.fail(rid)
    else:
        w.complete(rid, "insufficient", level=1)
    w.rejected("INSERT INTO run_claim (run_id, worker) VALUES (:r, 'host:1')", "only an open run is claimed", r=rid)


def test_one_open_claim_per_run(w):
    rid = w.run()
    cid = claim(w, rid)
    with pytest.raises(IntegrityError, match="uq_run_claim_open"):
        claim(w, rid, "host:2")
    release(w, cid, "lost")
    claim(w, rid, "host:2")
    assert w.val("SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 2


@pytest.mark.parametrize("worker", ["", "  ", "x" * 201])
def test_a_claim_names_its_worker(w, worker):
    with pytest.raises(IntegrityError, match="ck_run_claim_worker_named"):
        claim(w, w.run(), worker)


def test_the_heartbeat_is_the_databases_time_and_needs_no_run_lock(w):
    """R6: the heartbeat is written on the claim row; a run lock held elsewhere does not hold it back."""
    rid = w.run()
    cid = claim(w, rid)
    with w.e.connect() as holder:
        tx = holder.begin()
        holder.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        with w.e.connect() as beat:
            beat.execute(text("SET lock_timeout = '2s'"))
            beat.execute(text("UPDATE run_claim SET heartbeat_at = '2000-01-01' WHERE id = :c"), dict(c=cid))
            beat.commit()
        tx.rollback()
    assert w.val("SELECT heartbeat_at > '2001-01-01' FROM run_claim WHERE id = :c", c=cid)


def test_the_childs_pid_is_set_once(w):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET child_pid = 4242 WHERE id = :c", c=cid)
    w.rejected("UPDATE run_claim SET child_pid = 4343 WHERE id = :c", "a claim's child is recorded once", c=cid)


@pytest.mark.parametrize("column, value", [("run_id", "999"), ("worker", "'host:9'"), ("claimed_at", "now() - interval '1 h'")])
def test_what_a_claim_records_never_changes(w, column, value):
    rid = w.run()
    cid = claim(w, rid)
    w.rejected(f"UPDATE run_claim SET {column} = {value} WHERE id = :c", "what a claim records cannot change", c=cid)


@pytest.mark.parametrize("reason", REASONS)
def test_a_claim_is_released_once_with_a_reason_at_the_databases_time(w, reason):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET released_at = '2000-01-01', release_reason = :x WHERE id = :c", x=reason, c=cid)
    assert w.val("SELECT released_at > '2001-01-01' FROM run_claim WHERE id = :c", c=cid)
    w.rejected("UPDATE run_claim SET heartbeat_at = now() WHERE id = :c", "a released claim is final", c=cid)
    w.rejected("UPDATE run_claim SET release_reason = 'lost' WHERE id = :c", "a released claim is final", c=cid)


def test_a_release_needs_a_known_reason(w):
    cid = claim(w, w.run())
    with pytest.raises(IntegrityError, match="ck_run_claim_release"):
        release(w, cid, "because")
    w.rejected("UPDATE run_claim SET release_reason = 'finished' WHERE id = :c", "ck_run_claim_released_with_reason",
               c=cid)


def test_what_recovery_found_is_recorded_with_the_release(w):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET found = '{\"calls_closed\": 1}', released_at = now(), release_reason = "
              "'stopped_for_recovery' WHERE id = :c", c=cid)
    assert w.val("SELECT found->>'calls_closed' FROM run_claim WHERE id = :c", c=cid) == "1"


def test_claims_are_never_deleted(w):
    cid = claim(w, w.run())
    w.rejected("DELETE FROM run_claim WHERE id = :c", "never deleted", c=cid)
    w.rejected("TRUNCATE run_claim", "never deleted")
