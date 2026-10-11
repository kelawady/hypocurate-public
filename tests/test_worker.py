"""Step 9b, b2: the worker (docs/reviews/step09b_plan.md). `python -m hypocurate.worker [--once]` claims a run, keeps
its claim's heartbeat, runs the orchestrator in a guarded child that holds the run's work lock, watches the child
(A4: stuck after a time with no write, or after the whole-run limit; SIGTERM: shut down), and releases the claim with
its reason. Every model call goes to the local stub (no live call)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, queue
from test_guarded_parent import gone


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database, monkeypatch, stub):
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    pw.registered(e, ("mpea", "tamu_fcc"))
    with e.begin() as conn:  # a backend notices quickly that its client is gone (a killed child's sleeping query)
        conn.execute(text("SELECT set_config('client_connection_check_interval', '100ms', false)"))
        db = conn.execute(text("SELECT current_database()")).scalar()
        conn.execute(text(f'ALTER DATABASE "{db}" SET client_connection_check_interval = \'100ms\''))
    yield e
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def worker(*args, wait=True):
    proc = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=dict(os.environ))
    if wait:
        out, err = proc.communicate(timeout=600)
        assert proc.returncode == 0, err[-3000:]
    return proc


def claims(engine, rid):
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(text("SELECT worker, child_pid IS NOT NULL, release_reason FROM run_claim "
                                                    "WHERE run_id = :r ORDER BY id"), dict(r=rid)).all()]


def stall_at(engine, table):
    """A test-only trigger: the run's next write to `table` sleeps, so the child makes no progress."""
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_test_stall() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          "PERFORM pg_sleep(120); RETURN NEW; END $$"))
        conn.execute(text(f"CREATE TRIGGER zz_hc_test_stall BEFORE INSERT ON {table} FOR EACH ROW "
                          f"EXECUTE FUNCTION hc_test_stall()"))


def unstall(engine, table):
    with engine.begin() as conn:
        conn.execute(text(f"DROP TRIGGER zz_hc_test_stall ON {table}"))
        conn.execute(text("DROP FUNCTION hc_test_stall()"))


def sleeping(engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'PgSleep' AND "
                                 "datname = current_database()")).scalar() > 0


def wait_until(predicate, seconds=60):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return False


def test_the_worker_parent_loads_no_model_or_statistics_library():
    """Owner, Q2 (memory on 512 MB; the plan: "the parent never imports dspy, litellm or scipy"). numpy is not on the
    list: the parent imports the access package (for the guarded runner), whose source adapters import openpyxl,
    which imports numpy. Keeping it out would mean loading openpyxl after the child's file guard is installed, which
    the guard refuses (it reads /etc/mime.types). The memory measurement (b5) includes it."""
    code = ("import sys, hypocurate.worker, hypocurate.pipeline.queue, hypocurate.pipeline.recovery; "
            "print([m for m in ('dspy', 'litellm', 'scipy', 'statsmodels') if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert out.stdout.strip() == "[]", out.stderr


def test_worker_once_with_nothing_to_do_returns(engine):
    started = time.time()
    worker("--once")
    assert time.time() - started < 60


def test_worker_once_completes_a_fixed_plan_run(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    (name, child_recorded, reason), = claims(engine, rid)
    assert name.endswith(tuple("0123456789")) and child_recorded and reason == "finished"


def test_a_planner_run_waits_then_a_worker_finishes_it_once_confirmed(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert claims(engine, rid)[-1][2] == "waiting"
    worker("--once")  # not confirmed: nothing to claim
    assert len(claims(engine, rid)) == 1
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert [c[2] for c in claims(engine, rid)] == ["waiting", "finished"]


def test_two_workers_and_one_run_give_one_claim_and_no_repeated_request(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    a, b = worker("--once", wait=False), worker("--once", wait=False)
    for p in (a, b):
        p.communicate(timeout=600)
        assert p.returncode == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert len(claims(engine, rid)) == 1
    analyst = [r for r in stub.requests if "[[ ## report ## ]]" in r["raw"].decode()]
    assert len(analyst) == 1


def test_sigterm_shuts_the_worker_down_releasing_its_claim_and_stopping_its_child(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        p = worker(wait=False)
        assert wait_until(lambda: sleeping(engine))
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r", r=rid)
        p.send_signal(signal.SIGTERM)
        p.communicate(timeout=120)
        assert p.returncode == 0
        assert claims(engine, rid)[-1][2] == "shutdown"
        assert wait_until(lambda: gone(pid), 5)
        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"  # taken up again later
    finally:
        unstall(engine, "run_snapshot")


def test_killing_the_worker_kills_its_child_and_frees_the_runs_locks(engine, stub):
    """A3, with the real worker: SIGKILL of the worker kills the child within 2 s, and the work lock is released."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        p = worker(wait=False)
        assert wait_until(lambda: sleeping(engine))
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r", r=rid)
        p.send_signal(signal.SIGKILL)
        p.wait(10)
        assert wait_until(lambda: gone(pid), 2), "the child outlived the worker"

        def locks_free():
            with engine.connect() as conn:
                free = all(conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=k)).scalar()
                           for k in (queue.claim_key(rid), queue.work_key(rid)))
                conn.execute(text("SELECT pg_advisory_unlock_all()"))
                return free
        assert wait_until(locks_free, 10)
        assert claims(engine, rid)[-1][2] is None  # the claim stays open; its heartbeat goes stale
    finally:
        unstall(engine, "run_snapshot")


def test_a_stuck_child_is_stopped_and_its_claim_released_for_recovery(engine, stub):
    """A4, at a shortened test-only limit: no write for the limit -> the child is killed, the claim `child_stuck`."""
    from hypocurate import worker as w
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:stuck")
        out = w.work(engine, c, stall_seconds=3, heartbeat_interval=0.5)
        assert out["release"] == "child_stuck"
        assert claims(engine, rid)[-1][2] == "child_stuck"
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE id = :c", c=c.id)
        assert wait_until(lambda: gone(pid), 5)
    finally:
        unstall(engine, "run_snapshot")


def test_the_whole_run_limit_stops_a_child_that_keeps_writing_too_long(engine, stub):
    from hypocurate import worker as w
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:timeout")
        out = w.work(engine, c, run_timeout=2, stall_seconds=10 ** 6, heartbeat_interval=0.5)
        assert out["release"] == "child_stuck" and out["why"] == "run_timeout"
    finally:
        unstall(engine, "run_snapshot")


def test_the_web_service_never_claims_or_runs_a_pipeline():
    """Step 10 shows the queue; until then the web code imports neither the queue, the worker nor the orchestrator."""
    import ast
    import pathlib
    web = pathlib.Path(__file__).resolve().parents[1] / "hypocurate" / "web"
    for path in web.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else []
            module = getattr(node, "module", None) or ""
            assert not any(x in (module, *names) for x in ("queue", "worker", "orchestrator", "recovery",
                                                           "hypocurate.pipeline.queue", "hypocurate.worker",
                                                           "hypocurate.pipeline.orchestrator")), path


def test_a_child_whose_run_is_held_by_another_child_is_busy_and_writes_nothing(engine, stub):
    """The work lock: a second child of the same run (an orphan still at work) returns `busy` at once."""
    from hypocurate.pipeline import orchestrator, queries
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    queries.start(engine, rid)
    with engine.connect() as holder:
        assert holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
        assert orchestrator.work_guarded({"run_id": rid}) == {"busy": True}
        holder.execute(text("SELECT pg_advisory_unlock_all()"))
        holder.commit()
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_the_worker_logs_each_claim_and_each_finished_run(engine, stub):
    """Step 10a (the live-run record): the worker's log has one line for the claim and one for the finished run, with
    its status and outcome, so the Render log shows both."""
    import json as _json
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    proc = worker("--once", wait=False)
    out, err = proc.communicate(timeout=600)
    assert proc.returncode == 0, err[-3000:]
    events = [_json.loads(line[line.index("{"):]) for line in (out + err).splitlines() if "{" in line
              and ('"claimed"' in line or '"run_finished"' in line)]
    assert [e for e in events if "claimed" in e] == [{"claimed": rid, "claim": events[0]["claim"],
                                                     "worker": events[0]["worker"], "status_before": "queued"}]
    assert [e for e in events if "run_finished" in e] == [{"run_finished": rid, "status": "completed",
                                                          "outcome": "sufficient", "failure": None}]
