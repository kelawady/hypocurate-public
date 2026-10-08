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
query whose earlier run ended. `--ceiling` is stored on the run at dispatch (R5).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from hypocurate.pipeline import queries


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
        ceiling = _ceiling(args.ceiling)
        if args.command == "confirm":
            return _confirm(engine, args.run, args.by, ceiling)
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
    """Two guarded calls: up to the rules lock (or the wait for a person, step 9a), then on to the end. Between them
    the original claim and the question as tested are printed (owner's decision B), before the run goes on."""
    from hypocurate.access.guarded import GuardedRunError, run_guarded
    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None}
    try:
        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "prepare"},
                             timeout=3600, audit=(engine, run_id))
        print(json.dumps({"claim": _claim(engine, run_id), "question_as_tested": report.get("question_as_tested")},
                         ensure_ascii=False), flush=True)
        if report.get("ready"):
            rest = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "proceed"},
                               timeout=3600, audit=(engine, run_id))
            report = {**rest, "stages": report["stages"] + rest["stages"]}
    except GuardedRunError:
        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
        return 1
    return _print_shown(engine, run_id, report)


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


def _confirm(engine: Engine, run_id: int, by: str, ceiling: Decimal | None) -> int:
    """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest."""
    from hypocurate.access.guarded import GuardedRunError, run_guarded
    from hypocurate.pipeline import confirmation
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
    if status is None:
        raise queries.QueryRefused("unknown_run", f"no run {run_id}")
    if status != "waiting":
        raise queries.QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
    content, words = confirmation.show(engine, run_id)
    print(words, flush=True)
    confirmation.confirm(engine, run_id, by, shown=content)
    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None, "phase": "proceed"}
    try:
        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", payload, timeout=3600,
                             audit=(engine, run_id))
    except GuardedRunError:
        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
        return 1
    return _print_shown(engine, run_id, report)


def _claim(engine: Engine, run_id: int) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT hv.text FROM run r JOIN hypothesis_version hv ON hv.id = "
                                 "r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).scalar_one()


def question_as_tested(engine: Engine, run_id: int) -> dict | None:
    from hypocurate.pipeline import reading
    with engine.connect() as conn:
        return reading.stored(conn, run_id)


def analyst_text(explained) -> dict:
    """The Analyst's stored explanation, always with its label; or that it is unavailable (code's own words)."""
    from hypocurate.pipeline.agents import analyst
    if isinstance(explained, dict) and explained.get("report"):
        return {"label": analyst.LABEL, "text": explained["report"]}
    if isinstance(explained, dict):
        return {"unavailable": explained.get("shown") or analyst.UNAVAILABLE}
    return {"unavailable": analyst.UNAVAILABLE}


def critic_flags(engine: Engine, run_id: int) -> list[dict]:
    """Each flag as shown: code's kind and category, its records, and the Critic's class or why there is none."""
    from hypocurate.pipeline.agents import critic
    return critic.flag_display(engine, run_id)


def show(engine: Engine, run_id: int) -> dict | None:
    from hypocurate.pipeline import statement
    from hypocurate.pipeline import statistics as st
    with engine.connect() as conn:
        run = conn.execute(text(
            "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
            "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
            "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
        if run is None:
            return None

        def output(stage):
            return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
                                     "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()

        stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
        results = [dict(r._mapping) for r in conn.execute(text(
            "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
            "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
            "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
        narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
                                dict(r=run_id)).scalar_one_or_none()
        original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
                                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
                                dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
        cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
    decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
    built = statement.build(engine, run_id)  # decision A: code's statement, for every completed run
    return {
        # One presentation everywhere (owner, after the re-check): code's statement first, then the Analyst's text,
        # only with the statement and only under its label; `run` and `dispatch` print this same output.
        "statement": built["lines"] if built else None,
        "analyst_text": analyst_text(explained) if built else None,
        "run": run.id, "query": run.number, "claim": run.text, "outcome_code": run.outcome,
        "question_as_tested": question_as_tested(engine, run.id), "status": run.status,
        "narrower_question_of": original, "narrower_question": narrower,
        # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
        "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
                else "the Planner's",
        "sufficiency_option": run.sufficiency_option,
        "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
        "verdict": decision.get("verdict_wording") if run.verdict else None,
        "exploratory": run.exploratory, "evidence_level": run.evidence_level,
        "evidence_level_wording": decision.get("evidence_level_wording") if run.status == "completed" else None,
        "label": decision.get("label"), "failure": run.failure_reason,
        "results": [r for r in results if not r["withheld"]] if results else [],
        "withheld": [{k: r[k] for k in ("scope", "source", "analysis_set", "n_records", "n_alloys", "n_groups",
                                         "resid_df", "minimums_met")} for r in results if r["withheld"]],
        "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
        "sources": (gap or {}).get("sources"),
        "statement_format": ({"current": built["format_version"], "recorded": built["recorded_format_version"]}
                             if built else None),
        "flags": critic_flags(engine, run_id),
        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
        # Step 9a: only for a waiting run, so every other run's output is as before.
        **({"waiting_for": _waiting_for()} if run.status == "waiting" else {}),
    }


def _waiting_for() -> str:
    from hypocurate.pipeline.confirmation import WAITING_FOR
    return WAITING_FOR
