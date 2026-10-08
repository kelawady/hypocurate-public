"""Step 9a: the command line's wait, `confirm`, `cancel`, `dispatch --again` and the stored `--ceiling` (owner's
approval of the step 9 plan, 2026-10-08: R1, R2, R3, R5, A2; no bulk or automatic confirmation). Each run executes in
the guarded process; the model provider is the local stub (no live call)."""
from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import text

from hypocurate.pipeline import confirmation, queries
from test_cli_runs import engine, hc, stub  # noqa: F401 (fixtures)
from test_confirmation import newer_version
from test_orchestrator import FCC_CLAIM, planner_body, responder


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def run_to_wait(capsys, engine, stub):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    first, reading, rest = out.split("\n", 2)
    return code, json.loads(first)["run"], json.loads(rest), err


def test_run_stops_at_the_wait_and_says_what_it_waits_for(engine, stub, capsys):
    code, rid, report, err = run_to_wait(capsys, engine, stub)
    assert code == 0, err
    assert report["status"] == "waiting" and report["waiting_for"] == confirmation.WAITING_FOR
    assert report["next"] == f'hypocurate confirm {rid} --by "<name>"'
    assert report["statement"] is None and report["outcome"] is None
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    shown = json.loads(hc(capsys, "show", str(rid))[1])
    assert shown["waiting_for"] == confirmation.WAITING_FOR


def test_confirm_prints_what_is_confirmed_before_the_report_and_stores_exactly_that_text(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    printed, report = out[:out.index("\n{")], json.loads(out[out.index("\n{") + 1:])
    assert printed == one(engine, "SELECT shown FROM rules_confirmation WHERE run_id = :r", r=rid)
    assert printed.startswith(f"Run {rid} of ")
    assert report["status"] == "completed" and report["outcome_code"] == "sufficient"
    assert report["question_as_tested"]["label"].startswith(
        "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on ")


def test_confirm_needs_a_waiting_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 1 and err.startswith(f"error: not_waiting: run {rid} is not waiting for confirmation")
    code, out, err = hc(capsys, "confirm", "999", "--by", "Ada Reviewer")
    assert code == 1 and err.startswith("error: unknown_run")


def test_confirm_is_refused_when_the_sources_changed_and_nothing_is_recorded(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    newer_version(engine, "tamu_fcc")
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 1
    assert err.strip() == ("error: sources_changed: tamu_fcc has a newer version since this run's narrowing; cancel "
                           "this run and dispatch the query again")
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_cancel_a_waiting_run_then_dispatch_the_query_again(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    assert json.loads(out) == {"run": rid, "status": "failed", "failure": "cancelled: cancelled by Ada Reviewer while "
                                                                          "waiting for confirmation of the question as tested"}
    number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                         "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)
    code, out, err = hc(capsys, "dispatch", number, "--again")
    assert code == 0, err
    again = json.loads(out.split("\n", 1)[0])["run"]
    assert again != rid and json.loads(out.split("\n", 2)[2])["status"] == "waiting"
    code, out, err = hc(capsys, "dispatch", number, "--again")
    assert code == 1 and err.strip() == "error: already_open: another run of this query is queued, waiting or running"


def test_cancel_refuses_a_started_or_ended_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 1 and err.startswith(f"error: not_cancellable: run {rid} is completed")


def test_a_queued_run_is_cancelled_from_the_command_line(engine, capsys):
    q = queries.create(engine, FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 0 and json.loads(out)["failure"] == "cancelled: cancelled by Ada Reviewer before it started"


def test_the_ceiling_given_to_run_is_stored_on_the_run(engine, stub, capsys):
    rid, _, _ = run_with_ceiling(capsys, engine, stub)
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("1.5")


def run_with_ceiling(capsys, engine, stub):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer",
                        "--ceiling", "1.5")
    return json.loads(out.split("\n", 1)[0])["run"], out, err


def test_dispatch_without_again_still_names_the_reviewer(engine, capsys):
    q = queries.create(engine, FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    code, out, err = hc(capsys, "dispatch", q.number)
    assert code == 1 and "--by names the person confirming the domain" in err


def test_confirm_takes_no_ceiling(engine, capsys):
    """Fix round 1, finding 4: the ceiling is set only at dispatch (stored on the run); confirm has no --ceiling."""
    import inspect
    import pytest
    from hypocurate import cli, cli_runs
    with pytest.raises(SystemExit) as stopped:
        cli.main(["confirm", "1", "--by", "Ada Reviewer", "--ceiling", "0.10"])
    assert stopped.value.code == 2
    assert list(inspect.signature(cli_runs._confirm).parameters) == ["engine", "run_id", "by"]
