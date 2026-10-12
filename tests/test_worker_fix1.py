"""Step 9b fix round 1, findings 2 to 7 (owner, 2026-10-09; docs/reviews/step09b_plan.md, "Fix round 1").

2. Never release a claim with a live child: on every exit path the child is stopped and reaped first; a SIGTERM that
   does not work is escalated to SIGKILL; no child is started once shutdown was asked for.
3. Losing the lock means stopping: the worker fails closed when its lease session is lost; the child's work is bound
   to its claim (checked in each write's own transaction, the claim row locked FOR SHARE; and before a reservation),
   so a stale owner is refused before any further request or write.
4. The recovery exception applies only to stages stored before: a failure of a Critic run after recovery stops.
5. Monitoring cannot block the watchdog: monitoring queries are time-limited and run off the main thread; the
   whole-run kill and the shutdown check do not wait for them.
6. The stall allowance starts at the attempt's launch: downtime before it does not count.
7. Recovery attempts are counted explicitly (claims that took up a running run), excluding the first run."""
from __future__ import annotations

import signal
import subprocess
import sys
import tempfile
import threading
import time

import pytest
from sqlalchemy import text

import stub_provider as sp
import test_orchestrator as to
from hypocurate import worker
from hypocurate.access import guarded
from hypocurate.pipeline import queries, queue, recovery, writes
from test_guarded_parent import gone
from test_kill_matrix import STALL_KEY, sleeping, stall, unstall
from test_worker import engine, stub, wait_until  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def fixed_run(engine, stub):
    stub.respond(to.responder())
    return to.dispatched(engine, fixed_plan=True)


# --- finding 2 --------------------------------------------------------------------------------------------

def test_a_failure_after_the_child_started_stops_and_reaps_it_before_the_claim_is_released(engine, stub, monkeypatch):
    rid = fixed_run(engine, stub)
    started, at_release = [], []
    real_start, real_release = guarded.start_guarded, queue.release

    def start(*a, **k):
        child = real_start(*a, **k)
        started.append(child)
        return child

    def record_child(*a, **k):
        raise RuntimeError("the claim row could not be written")

    def release(engine_, claim, reason, found=None):
        at_release.append((reason, [gone(c.pid) for c in started]))
        return real_release(engine_, claim, reason, found)

    monkeypatch.setattr(guarded, "start_guarded", start)
    monkeypatch.setattr(queue, "record_child", record_child)
    monkeypatch.setattr(queue, "release", release)
    c = queue.claim(engine, rid, "test:f2")
    with pytest.raises(RuntimeError):
        worker.work(engine, c, heartbeat_interval=0.5)
    assert started and at_release == [("child_failed", [True])]  # the child was gone before the release


def test_a_child_that_ignores_sigterm_is_killed(tmp_path):
    proc = subprocess.Popen([sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, "
                             "signal.SIG_IGN); print('ready', flush=True); time.sleep(120)"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout.readline().strip() == "ready"
    child = guarded.GuardedChild(proc, tempfile.mkdtemp(dir=tmp_path), None)
    started = time.time()
    child.stop(signal.SIGTERM)
    assert proc.poll() is not None and proc.returncode == -signal.SIGKILL
    assert time.time() - started < guarded.STOP_GRACE_SECONDS + 5


def test_no_child_is_started_once_shutdown_was_asked_for(engine, stub, monkeypatch):
    rid = fixed_run(engine, stub)

    def start(*a, **k):
        raise AssertionError("a child was started after shutdown")

    monkeypatch.setattr(guarded, "start_guarded", start)
    stop = threading.Event()
    stop.set()
    c = queue.claim(engine, rid, "test:f2")
    out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
    assert out["release"] == "shutdown"
    assert one(engine, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == "shutdown"


# --- finding 3 --------------------------------------------------------------------------------------------

def terminate(engine, application_name):
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity WHERE application_name "
                                 "= :a AND datname = current_database()"), dict(a=application_name)).scalar()


def test_losing_the_lease_session_stops_the_child_and_gives_up_the_run(engine, stub):
    """The lease's lock session is terminated while the worker and its child stay alive."""
    rid = fixed_run(engine, stub)
    holder = stall(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:f3")
        threading.Thread(target=lambda: (wait_until(lambda: sleeping(engine), 60),
                                         terminate(engine, f"hc-lease-{rid}")), daemon=True).start()
        out = worker.work(engine, c, heartbeat_interval=0.3)
        assert out["why"] == "ownership_lost"
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE id = :c", c=c.id)
        assert wait_until(lambda: gone(pid), 5)
        assert one(engine, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == "lost"
        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    finally:
        unstall(engine, "run_snapshot", holder)


def test_losing_the_work_session_refuses_the_childs_next_write(engine, stub):
    """The child's work-lock session is terminated while the child stays alive: its next write is refused."""
    rid = fixed_run(engine, stub)
    holder = stall(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:f3w")

        def cut():
            wait_until(lambda: sleeping(engine), 60)
            terminate(engine, f"hc-work-{rid}")
            time.sleep(0.5)
            holder.execute(text("SELECT pg_advisory_unlock_all()"))  # the stalled write goes on; the next one is refused

        threading.Thread(target=cut, daemon=True).start()
        worker.work(engine, c, heartbeat_interval=0.3)
        assert one(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r AND detail->>'code' = 'claim_lost'",
                   r=rid) >= 1
        assert one(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    finally:
        unstall(engine, "run_snapshot", holder)


def owned(engine, rid):
    """This process acting as a run's child: a claim, and the work lock held on a session of its own."""
    queries.start(engine, rid)
    c = queue.claim(engine, rid, "test:owner")
    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    assert holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
    pid = holder.execute(text("SELECT pg_backend_pid()")).scalar()
    return c, holder, pid


def test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused(engine, stub, monkeypatch):
    """Two connections: a child's write holds its claim row (FOR SHARE) while it works; a takeover closing the claim
    waits for that write to commit; the child's next write sees the closed claim and is refused."""
    rid = to.dispatched(engine, fixed_plan=True)
    c, holder, pid = owned(engine, rid)
    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
    done = {}

    def slow_write():
        def body(conn, _stage):
            # The database's time at the end of the write's work, just before its commit.
            done["body_end"] = conn.execute(text("SELECT pg_sleep(2), clock_timestamp()")).one()[1]
        writes.write(engine, rid, "test", "slow", body)

    t = threading.Thread(target=slow_write)
    t.start()
    time.sleep(0.5)
    started = time.monotonic()
    with engine.begin() as conn:  # the takeover's close of the claim (without the run's lock: the claim row decides)
        conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = 'lost' WHERE id = :c"),
                     dict(c=c.id))
    waited = time.monotonic() - started
    t.join(10)
    # It waited for the write: the close took at least 1 s (the write held the row about 1.5 s more), and the claim's
    # release time (the database's clock, set once the trigger has the row) is after the end of the write's work.
    assert waited >= 1.0
    assert one(engine, "SELECT released_at FROM run_claim WHERE id = :c", c=c.id) >= done["body_end"]
    with pytest.raises(writes.Refused) as refused:
        writes.write(engine, rid, "test", "next", lambda conn, _s: None)
    assert refused.value.code == "claim_lost"
    holder.invalidate()
    c.lease.close()


def test_a_write_is_refused_once_the_work_lock_session_is_gone(engine, stub, monkeypatch):
    rid = to.dispatched(engine, fixed_plan=True)
    c, holder, pid = owned(engine, rid)
    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
    writes.write(engine, rid, "test", "first", lambda conn, _s: None)  # owned: allowed
    holder.invalidate()  # the work lock's session ends (a close would only return it to the pool, lock and all)
    with pytest.raises(writes.Refused) as refused:
        writes.write(engine, rid, "test", "second", lambda conn, _s: None)
    assert refused.value.code == "claim_lost"
    c.lease.close()


def test_a_stale_owner_is_refused_before_its_reservation(engine, stub, monkeypatch):
    from decimal import Decimal
    from hypocurate.pipeline.agents import spend
    from hypocurate.pipeline.agents.runstage import open_stage
    rid = to.dispatched(engine, fixed_plan=True)
    c, holder, pid = owned(engine, rid)
    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
    _, inv = open_stage(engine, rid, "analyst", "analyst")
    queue.release(engine, c, "lost")  # taken over
    with pytest.raises(spend.ClaimLost):
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 0
    holder.invalidate()


# --- finding 4 --------------------------------------------------------------------------------------------

def test_a_critic_run_after_recovery_that_fails_to_record_its_call_stops_the_run(migrated_database, stub, monkeypatch):
    import pipeline_world as pw
    from hypocurate.db.engine import make_engine
    from hypocurate.pipeline import checkpoints, checks, confirmation, extract
    from stats_world import small_rows
    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME, SOURCES
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
                            "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
    stub.respond(to.responder())
    q = queries.create(e, to.FCC_CLAIM, SOURCES)
    queries.submit(e, q.version_id)
    queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(e, q.version_id, fixed_plan=True, constructed_test_data=True)
    queries.start(e, rid)
    with e.connect() as conn:
        checkpoints.lock_rules(e, rid, confirmation.plan_to_lock(conn, rid))
    extract.store_records(e, rid)
    checks.run_checks(e, rid)  # the stop: before the Critic
    with e.begin() as conn:  # the Critic's call cannot be recorded (a test-only trigger)
        conn.execute(text("CREATE FUNCTION hc_test_norecord() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          "RAISE EXCEPTION 'test: the call cannot be recorded'; END $$"))
        conn.execute(text("CREATE TRIGGER zz_hc_test_norecord BEFORE UPDATE ON model_call FOR EACH ROW "
                          "EXECUTE FUNCTION hc_test_norecord()"))
    try:
        c = queue.claim(e, rid, "test:f4")
        assert c.status_before == "running"  # taken up: recovered
        worker.work(e, c, heartbeat_interval=0.5)
    finally:
        with e.begin() as conn:
            conn.execute(text("DROP TRIGGER zz_hc_test_norecord ON model_call"))
            conn.execute(text("DROP FUNCTION hc_test_norecord()"))
    assert requests(stub, "classification") >= 1
    assert requests(stub, "report") == 0  # stopped: no Analyst
    assert one(e, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert one(e, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0
    e.dispose()


# --- findings 5 and 6 ----------------------------------------------------------------------------------------

BLOCKED_SECONDS = 60  # far beyond each test's limit; bounded so a watchdog that waits on it fails, not hangs


def blocked_monitoring(monkeypatch):
    never = threading.Event()
    monkeypatch.setattr(queue, "last_write_epoch", lambda conn, run_id: never.wait(BLOCKED_SECONDS))


def test_a_blocked_monitoring_query_does_not_hold_back_the_whole_run_limit(engine, stub, monkeypatch):
    rid = fixed_run(engine, stub)
    holder = stall(engine, "run_snapshot")
    blocked_monitoring(monkeypatch)
    try:
        c = queue.claim(engine, rid, "test:f5")
        started = time.monotonic()
        out = worker.work(engine, c, run_timeout=3, stall_seconds=10 ** 6, heartbeat_interval=0.5)
        assert out["why"] == "run_timeout" and time.monotonic() - started < 15
    finally:
        unstall(engine, "run_snapshot", holder)


def test_a_blocked_monitoring_query_does_not_hold_back_shutdown(engine, stub, monkeypatch):
    rid = fixed_run(engine, stub)
    holder = stall(engine, "run_snapshot")
    blocked_monitoring(monkeypatch)
    try:
        c = queue.claim(engine, rid, "test:f5s")
        stop = threading.Event()
        threading.Timer(3, stop.set).start()
        started = time.monotonic()
        out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
        assert out["release"] == "shutdown" and time.monotonic() - started < 3 + guarded.STOP_GRACE_SECONDS + 5
    finally:
        unstall(engine, "run_snapshot", holder)


def test_the_monitoring_query_is_time_limited(engine, stub):
    rid = fixed_run(engine, stub)
    with engine.connect() as locker:
        tx = locker.begin()
        locker.execute(text("LOCK TABLE stage_result IN ACCESS EXCLUSIVE MODE"))
        # On a thread, so a sample with no time limit fails this test instead of hanging the suite.
        result = {}

        def sample():
            try:
                queue.sample_last_write(engine, rid)
                result["outcome"] = "returned"
            except Exception as e:  # noqa: BLE001 (the timeout's error is the expected outcome)
                result["outcome"] = e
        started = time.monotonic()
        t = threading.Thread(target=sample, daemon=True)
        t.start()
        t.join(queue.MONITOR_TIMEOUT_MS / 1000 + 3)
        alive = t.is_alive()
        tx.rollback()  # releases a sample still waiting
        t.join(10)
        assert not alive, "the monitoring query waited past its time limit"
        assert isinstance(result.get("outcome"), Exception)
        assert time.monotonic() - started < queue.MONITOR_TIMEOUT_MS / 1000 + 13


TEST_STALL_SECONDS = 20     # the test's stall allowance (production: queue.STALL_SECONDS, 900)
TEST_DOWNTIME_SECONDS = 22  # longer than TEST_STALL_SECONDS
FIRST_WRITE_HOLD_SECONDS = 6  # longer than the stall watch's first sample (min(5, TEST_STALL_SECONDS / 4) s)


def test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance(engine, stub):
    """A run stopped after its lock, idle for longer than the allowance, then taken up: the new child gets the full
    allowance from its launch and completes."""
    from hypocurate.pipeline import checkpoints, confirmation
    rid = fixed_run(engine, stub)
    queries.start(engine, rid)
    with engine.connect() as conn:
        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
    # Step 10b (owner's decision, 2026-10-11): the test's allowance is 20 s, not 6 s, so a slow machine's child start
    # fits in it (the image's run once judged the child stalled at 6 s); the downtime stays longer than the allowance,
    # so the test still checks that downtime before the attempt does not count. Production keeps STALL_SECONDS (900).
    # The child's first write waits FIRST_WRITE_HOLD_SECONDS (a one-shot test trigger), so the stall watch samples
    # (every min(5, allowance / 4) s) before any new write: if downtime counted, that sample would see a last write
    # older than the allowance and stop the child (9b fix round 1, mutation f16). The hold plus the child's start still
    # fits in the allowance.
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE hc_test_hold_once (x int)"))
        conn.execute(text("INSERT INTO hc_test_hold_once VALUES (1)"))
        conn.execute(text(f"CREATE FUNCTION hc_test_hold_once() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          f"IF EXISTS (SELECT 1 FROM hc_test_hold_once) THEN DELETE FROM hc_test_hold_once; "
                          f"PERFORM pg_sleep({FIRST_WRITE_HOLD_SECONDS}); END IF; RETURN NULL; END $$"))
        # On the child's first write only (its records); the parent's recovery bookkeeping, before the launch, writes
        # stage rows and must not use up the hold.
        conn.execute(text("CREATE TRIGGER zz_hc_test_hold_once BEFORE INSERT ON record "
                          "FOR EACH STATEMENT EXECUTE FUNCTION hc_test_hold_once()"))
    time.sleep(TEST_DOWNTIME_SECONDS)  # idle: longer than the allowance below
    c = queue.claim(engine, rid, "test:f6")
    out = worker.work(engine, c, stall_seconds=TEST_STALL_SECONDS, heartbeat_interval=0.5)
    assert out["release"] == "finished" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"


# --- finding 7 --------------------------------------------------------------------------------------------

def test_three_recoveries_are_allowed_and_the_fourth_is_refused_with_real_claim_histories(engine, stub):
    """Each attempt is a real claim worked by the worker's code and stopped by a shutdown while its child is held at
    the freeze; the first claim (from queued) is the first run, not a recovery."""
    rid = fixed_run(engine, stub)
    holder = stall(engine, "run_snapshot")
    try:
        for attempt in range(1 + recovery.MAX_RECOVERIES):  # the first run, then three recoveries
            c = queue.claim(engine, rid, f"test:{attempt}")
            assert c is not None and c.status_before == ("queued" if attempt == 0 else "running")
            stop = threading.Event()
            threading.Thread(target=lambda: (wait_until(lambda: sleeping(engine), 60), stop.set()), daemon=True).start()
            out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
            assert out["release"] == "shutdown", attempt
            assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
        c = queue.claim(engine, rid, "test:4")  # the fourth recovery
        worker.work(engine, c, heartbeat_interval=0.5)
    finally:
        unstall(engine, "run_snapshot", holder)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith(
        f"attempts_exhausted: the run stopped at curation {recovery.MAX_RECOVERIES + 1} times without finishing")
    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r AND recovery", r=rid) == 4


# --- the owner's addition: worker sessions notice a client that is gone ------------------------------------------

def test_worker_sessions_check_for_a_lost_client_every_second_with_tcp_keepalives(migrated_database):
    from hypocurate.db.engine import WORKER_SESSION, make_engine
    e = make_engine(migrated_database, worker_session=True)
    with e.connect() as conn:
        shown = {k: conn.execute(text(f"SHOW {k}")).scalar() for k in
                 ("client_connection_check_interval", "tcp_keepalives_idle", "tcp_keepalives_interval",
                  "tcp_keepalives_count")}
    e.dispose()
    assert shown == {"client_connection_check_interval": "1s", "tcp_keepalives_idle": "30",
                     "tcp_keepalives_interval": "10", "tcp_keepalives_count": "3"}
    assert WORKER_SESSION["client_connection_check_interval"] == "1s"
    plain = make_engine(migrated_database)
    with plain.connect() as conn:
        assert conn.execute(text("SHOW client_connection_check_interval")).scalar() == "0"
    plain.dispose()


def test_the_worker_and_its_child_use_worker_sessions():
    import inspect
    from hypocurate.pipeline import orchestrator
    assert "worker_session=True" in inspect.getsource(worker.run)
    assert "worker_session=True" in inspect.getsource(orchestrator.work_guarded)
