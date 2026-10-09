"""Step 9b, b4: the command line through the claim (owner's approval of R1, R2; docs/reviews/step09b_plan.md).

`run`, `dispatch` and `confirm` work their run inline through the same claim and worker code as the background
worker (a claim row, its heartbeat, the guarded child), printing what they printed before; `--queue` returns at once
and leaves the run to a worker; `queue` lists the open runs; `hypocurate worker [--once]` is the worker (PRD 12)."""
from __future__ import annotations

import json

from sqlalchemy import text

from hypocurate.pipeline import confirmation, queue
from test_cli_runs import hc
from test_orchestrator import FCC_CLAIM, planner_body, responder
from test_worker import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_run_works_its_run_through_a_claim(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    assert code == 0, err
    rid = json.loads(out.split("\n", 1)[0])["run"]
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT child_pid IS NOT NULL, release_reason FROM run_claim WHERE run_id = :r"),
                            dict(r=rid)).all()
    assert [tuple(r) for r in rows] == [(True, "finished")]


def test_run_with_queue_returns_at_once_and_a_worker_finishes_the_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                        "--queue")
    assert code == 0, err
    lines = out.strip().split("\n")
    first = json.loads(lines[0])
    assert first["status"] == "dispatched" and len(lines) == 1
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=first["run"]) == "queued"
    code, out, err = hc(capsys, "worker", "--once")
    assert code == 0, err
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=first["run"]) == "completed"


def test_queue_lists_the_open_runs_with_what_they_wait_for(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")  # stops at the wait
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                   "--queue")
    queued = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "queue")
    assert code == 0, err
    rows = {r["run"]: r for r in json.loads(out)}
    assert rows[queued]["status"] == "queued" and rows[queued]["worker"] is None
    waiting = next(r for r in rows.values() if r["status"] == "waiting")
    assert waiting["waiting_for"] == confirmation.WAITING_FOR
    assert waiting["recoveries"] == 0 and waiting["seconds_since_last_write"] >= 0


def test_queue_shows_a_claims_worker_and_heartbeat(engine, stub, capsys):
    stub.respond(responder())
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                   "--queue")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    c = queue.claim(engine, rid, "host:7")
    try:
        rows = {r["run"]: r for r in json.loads(hc(capsys, "queue")[1])}
        assert rows[rid]["worker"] == "host:7" and rows[rid]["heartbeat_age_seconds"] >= 0
        assert rows[rid]["status"] == "running"
    finally:
        queue.release(engine, c, "stopped_for_recovery")


def test_confirm_with_queue_records_the_confirmation_and_leaves_the_run_to_a_worker(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer", "--queue")
    assert code == 0, err
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"  # confirmed, for a worker
    hc(capsys, "worker", "--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"


def test_confirm_works_the_rest_through_a_claim(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    with engine.connect() as conn:
        reasons = [r for (r,) in conn.execute(text("SELECT release_reason FROM run_claim WHERE run_id = :r ORDER BY id"),
                                               dict(r=rid)).all()]
    assert reasons == ["waiting", "finished"]
