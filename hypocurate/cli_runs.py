"""The command line's `run`, `dispatch` and `show` (PRD Section 12; build step 8b), and `confirm` and `cancel`
(step 9a).

`run` creates the query, submits it, records the named person's domain confirmation (A9), dispatches it and
runs it in the guarded process (`access.guarded.run_guarded`, with the run's audit log for the guard's
refusals). `dispatch Q-…` does the same for an already submitted query, such as a narrower question (Q10);
a narrower question's run locks the plan its original's narrowing decision stored (A8). `show` prints what the
database holds for a run: status, outcome and wordings, the pooled result unless withheld, the per-source
results, the minimums, the kind of nothing found, the Analyst's explanation (or that it is unavailable),
the narrower question and the run's tokens and cost. Errors print fixed codes and reasons; the guarded
child's error text is never printed (it may quote anything).

Step 9a (owner's approval of the step 9 plan, 2026-10-08; R1, R2, R3): a run whose plan comes from a model's answer
(the Planner's, or a narrower question's) stops before its rules lock and waits for a named person: `run` and
`dispatch` then print `show`'s output with what the run waits for and the command to confirm it. `confirm <run>
--by NAME` prints what the person confirms (`confirmation.render`) before anything is recorded, records the
confirmation with exactly that text, and runs the rest, printing `show`'s output. One run per command, never in
bulk. `cancel <run> --by NAME` cancels a queued or waiting run. `dispatch Q-… --again` dispatches a new run of a
query whose earlier run ended. `--ceiling` is stored on the run at dispatch (R5), and only there: `confirm` takes none
(fix round 1, finding 4); none given stores the per-run cap (owner, 2026-10-08).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from hypocurate.pipeline import queries
# Step 10a: moved to the read-only `run_view` (shared with the screens), unchanged; imported here under their names.
from hypocurate.pipeline.run_view import (analyst_text, critic_flags, question_as_tested, queue_rows,  # noqa: F401
                                          show)


def command(args, engine: Engine) -> int:
    try:
        if args.command == "show":
            out = show(engine, args.run)
            if out is None:
                print(f"error: no run {args.run}", file=sys.stderr)
                return 1
            print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
            return 0
        if args.command == "cancel":
            reason = queries.cancel(engine, args.run, by=args.by)
            print(json.dumps({"run": args.run, "status": "failed", "failure": reason}, ensure_ascii=False))
            return 0
        if args.command == "confirm":  # fix round 1, finding 4: no ceiling here; it is stored at dispatch
            return _confirm(engine, args.run, args.by, getattr(args, "queue", False))
        if args.command == "queue":
            print(json.dumps(queue_rows(engine), indent=2, ensure_ascii=False, default=str))
            return 0
        ceiling = _ceiling(args.ceiling)
        if args.command == "run":
            q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
                               domain=args.domain, sufficiency=args.sufficiency)
            queries.submit(engine, q.version_id)
            queries.confirm_domain(engine, q.version_id, by=args.by)
            run_id = queries.dispatch(engine, q.version_id, fixed_plan=args.fixed_plan,
                                      constructed_test_data=args.test_data, ceiling=ceiling)
            number = q.number
        elif args.again:
            run_id, number = queries.dispatch_again(engine, args.number, ceiling=ceiling), args.number
        else:
            if args.by is None:
                raise ValueError("--by names the person confirming the domain")
            vid = queries.submitted_version(engine, args.number)
            queries.confirm_domain(engine, vid, by=args.by)
            # A narrower question's plan follows from its link (finding 1).
            run_id = queries.dispatch(engine, vid, ceiling=ceiling)
            number = args.number
    except queries.QueryRefused as refused:
        print(f"error: {refused.code}: {refused.reason}", file=sys.stderr)
        return 1
    except IntegrityError as error:  # the database's own fixed refusal (for example an unsupported domain)
        from hypocurate.pipeline.writes import database_message
        print(f"error: {database_message(error)}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"query": number, "run": run_id, "status": "dispatched"}), flush=True)
    if getattr(args, "queue", False):  # step 9b (R1): returns at once; a worker takes the run up
        return 0
    return _run(engine, run_id, ceiling)


def _ceiling(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        ceiling = Decimal(value)
    except InvalidOperation:
        raise ValueError("the ceiling is a number of US dollars") from None
    if not ceiling > 0:
        raise ValueError("the ceiling is a positive number of US dollars")
    return ceiling


def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
    """Step 9b (R1): the run is worked inline through the same claim and worker code as the background worker: up to
    the rules lock (or the wait for a person, step 9a), then on to the end, in two guarded children under one claim.
    Between them the original claim and the question as tested are printed (owner's decision B), before the run goes
    on. The ceiling is the one stored at dispatch (step 9a)."""
    return _work_inline(engine, run_id, ("prepare", "proceed"), print_reading=True)


def _work_inline(engine: Engine, run_id: int, phases: tuple, print_reading: bool) -> int:
    from hypocurate import worker
    from hypocurate.pipeline import queue
    claim = queue.claim(engine, run_id, worker.worker_name())
    if claim is None:  # a worker holds it: wait until it ends, waits or stops, then show what is stored
        _wait_for(engine, run_id)
        return _print_shown(engine, run_id, {"stages": None, "failure": None})
    reports = {}

    def on_phase(phase: str, report: dict) -> None:
        reports[phase] = report
        if phase == "prepare" and print_reading:
            print(json.dumps({"claim": _claim(engine, run_id), "question_as_tested": report.get("question_as_tested")},
                             ensure_ascii=False), flush=True)

    out = worker.work(engine, claim, phases=phases, on_phase=on_phase)
    if out["release"] in ("child_failed", "child_stuck", "shutdown"):
        print(f"error: run {run_id} did not finish in the guarded process ({out['why']}; see the process log); "
              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
        return 1
    stages = [s for p in phases if p in reports for s in (reports[p].get("stages") or [])]
    last = reports.get(phases[-1]) or reports.get(phases[0]) or {}
    return _print_shown(engine, run_id, {"stages": stages, "failure": last.get("failure")})


def _wait_for(engine: Engine, run_id: int, poll: float = 2.0) -> None:
    """Until the run ends, waits for a person, or has no open claim (a worker let it go)."""
    import time
    from hypocurate.pipeline import queue
    deadline = time.monotonic() + queue.RUN_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        with engine.connect() as conn:
            status, held = conn.execute(text(
                "SELECT r.status, EXISTS (SELECT 1 FROM run_claim c WHERE c.run_id = r.id AND c.released_at IS NULL) "
                "FROM run r WHERE r.id = :r"), dict(r=run_id)).one()
        if status in ("completed", "failed", "waiting") or not held:
            return
        time.sleep(poll)


def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
    # One presentation everywhere (owner, after the re-check): the same output as `show` (code's statement first, then
    # the Analyst's text under its label), with the stages run and the run's failure, if any. The orchestration
    # report's own explanation is never printed. Step 9a: a waiting run's output says what it waits for and how to
    # confirm it.
    shown = show(engine, run_id)
    out = {**shown, "stages": report.get("stages"), "run_failure": report.get("failure")}
    if shown["status"] == "waiting":
        out["next"] = f'hypocurate confirm {run_id} --by "<name>"'
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0 if shown["status"] in ("completed", "failed", "waiting") else 1


def _confirm(engine: Engine, run_id: int, by: str, to_queue: bool = False) -> int:
    """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest. The run's
    ceiling is the one stored at dispatch (fix round 1, finding 4: a lower one given here would be lost on a restart)."""
    from hypocurate.pipeline import confirmation
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
    if status is None:
        raise queries.QueryRefused("unknown_run", f"no run {run_id}")
    if status != "waiting":
        raise queries.QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
    content, words = confirmation.show(engine, run_id)
    print(words, flush=True)
    # Fix round 1, finding 1: the text printed is checked too, so what is stored is exactly what was printed.
    confirmation.confirm(engine, run_id, by, shown=content,
                         shown_fingerprint=confirmation.shown_fingerprint(content, words))
    if to_queue:  # step 9b (R2): confirmed; a worker takes it up
        print(json.dumps({"run": run_id, "status": "waiting", "confirmed": True, "queued": True}), flush=True)
        return 0
    return _work_inline(engine, run_id, ("proceed",), print_reading=False)


def _claim(engine: Engine, run_id: int) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT hv.text FROM run r JOIN hypothesis_version hv ON hv.id = "
                                 "r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).scalar_one()
