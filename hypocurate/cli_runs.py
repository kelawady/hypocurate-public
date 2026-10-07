"""The command line's `run`, `dispatch` and `show` (PRD Section 12; build step 8b).

`run` creates the query, submits it, records the named person's domain confirmation (A9), dispatches it and
runs it in the guarded process (`access.guarded.run_guarded`, with the run's audit log for the guard's
refusals). `dispatch Q-…` does the same for an already submitted query, such as a narrower question (Q10);
a narrower question's run locks the plan its original's narrowing decision stored (A8). `show` prints what the
database holds for a run: status, outcome and wordings, the pooled result unless withheld, the per-source
results, the minimums, the kind of nothing found, the Analyst's explanation (or that it is unavailable),
the narrower question and the run's tokens and cost. Errors print fixed codes and reasons; the guarded
child's error text is never printed (it may quote anything).
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
        ceiling = _ceiling(args.ceiling)
        if args.command == "run":
            q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
                               domain=args.domain, sufficiency=args.sufficiency)
            queries.submit(engine, q.version_id)
            queries.confirm_domain(engine, q.version_id, by=args.by)
            run_id = queries.dispatch(engine, q.version_id, fixed_plan=args.fixed_plan,
                                      constructed_test_data=args.test_data)
            number = q.number
        else:
            vid = queries.submitted_version(engine, args.number)
            queries.confirm_domain(engine, vid, by=args.by)
            run_id = queries.dispatch(engine, vid)  # a narrower question's plan follows from its link (finding 1)
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
    from hypocurate.access.guarded import GuardedRunError, run_guarded
    try:
        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded",
                             {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None},
                             timeout=3600, audit=(engine, run_id))
    except GuardedRunError:
        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("status") in ("completed", "failed") else 1


def show(engine: Engine, run_id: int) -> dict | None:
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
    if isinstance(explained, dict) and explained.get("report"):
        explanation = explained["report"]
    elif isinstance(explained, dict):
        explanation = explained.get("shown") or "explanation unavailable"
    else:
        explanation = None
    return {
        "run": run.id, "query": run.number, "claim": run.text, "status": run.status,
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
        "explanation": explanation, "explanation_label": "model explanation; numbers checked against the run record"
        if isinstance(explained, dict) and explained.get("report") else None,
        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
    }
