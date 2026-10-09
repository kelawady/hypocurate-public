"""The orchestrator: one run, stage by stage (step 8b; PRD 3; the run order of the step 8 plan, corrected by the
owner's answer A1; register 'run_order'). Step 9a: the run waits at the rules lock for a named person, and every
step is taken from what is stored, so a run can be taken up again where it stopped (register 'rules_confirmation',
'resumable_run').

    Planner -> narrowing decision (code, before any lock)
      partly sufficient: Analyst (narrowing facts) -> copy_partly_sufficient -> narrower question; stop
      claim not one plan: the run fails before the lock (A11)
      proceed: the run WAITS for a named person's confirmation of the question as tested (step 9a, Q1)
    -> rules lock -> store records -> Checks -> Critic -> Inclusion -> dataset freeze -> statistics
    -> Analyst -> completion (copy_decision)

A narrower question's run bypasses the Planner (and the narrowing): after checking that its source versions are
those its original's counts were taken on (B1), it waits for the confirmation too (step 9a, Q5), then locks exactly
the narrower plan its original's narrowing decision stored (A8). It is recognised by the question's link to its
original, never by a flag (fix round, finding 1). A fixed-plan run of an ordinary question uses the reference plan
of criterion 14.1a and never waits.

**The plan locked** is `confirmation.plan_to_lock`'s, the one place that builds it from stored rows; a run that
waited locks only the plan whose fingerprint the person confirmed (code here, and the database, 0007).

**Taken up again from stored rows** (step 9a): `prepare` and `proceed` decide each step from what is stored, never
from memory. A done Planner stage is used, not repeated; a stored narrowing decision is used, not taken again; once
the lock is written, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the
statistics and the completion run only if their stored result is absent. An agent stage that exists already (the
Critic's, the Analyst's) is never started again here (owner, Q3: an interrupted Critic or Analyst is not repeated;
step 9b's recovery closes such a stage and applies the rule for its role). A run on its first pass takes exactly
the steps it took before step 9a.

**Code decides everything** (CLAUDE.md, rule 1); each agent's answer is checked by code before it is used.
**No model call runs inside a database transaction**: every step below uses its own short transactions, and
the agents' stages are opened and closed around the request (`agents.runstage`).

**Failures** (the step 8b failure table): a Planner failure, a domain mismatch, a claim that is not one plan,
a refused checkpoint or write, a spending refusal at the Planner or the Critic, or changed source versions
for a narrower question fail the run with a stated reason (`fail_run`). A Critic failure leaves flags
unclassified and the run goes on (no decision reads the class). Any Analyst failure, a spending refusal
included, leaves code's decision standing: the run completes with "explanation unavailable" (A3, B2). A
recording or a reservation failure at any agent (`lm.RUN_STOPS`) stops the run at once: no further model request
is made (no further Critic batch, no Analyst), nothing more is written, and the run stays running (a call whose
recording failed stays started) for step 9b's recovery; `run` reports it (fix round, finding 3).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import analysis, checkpoints, checks, completion, confirmation, extract, inclusion
from hypocurate.pipeline import narrowing, queries, reading, recovery
from hypocurate.pipeline.agents import analyst, critic, planner
from hypocurate.pipeline.agents.lm import RUN_STOPS
from hypocurate.pipeline.recovery import PLANNER_REPEATS, RECOVERABLE
from hypocurate.pipeline.writes import Refused, write

SPENDING = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
STOPPED = "the run stopped and stays open for recovery (step 9); no further model request was made"
# Fixed reasons of a failed run (failure_reason: "<code>: <reason>").
REASONS = {
    "planner_failed": "the Planner gave no usable plan",
    "domain_mismatch": "the Planner judged that the claim belongs to another domain (PRD 5.5)",
    "claim_not_one_plan": "the claim covers more than one temperature band, test type or alloy class; "
                          "submit one question per band, test type and alloy class",
    "narrowing_sources_changed": "the narrower question's source versions are not those its original's counts "
                                 "were taken on",
    "narrower_plan_missing": "the original's narrowing decision holds no narrower plan",
    "spending_refused": "a spending cap or ceiling was reached before the request was sent",
    "refused": "a checkpoint or write refused",
    # Step 9b (owner, Q3): the Planner's request was lost a second time.
    "interrupted": "the worker stopped during the Planner's request twice; dispatch the query again as a new run",
}


@dataclass
class RunReport:
    run_id: int
    status: str = "running"
    outcome: str | None = None
    failure: str | None = None
    stages: list = field(default_factory=list)
    narrower_question: str | None = None
    explanation: str | None = None
    explanation_failure: str | None = None
    question_as_tested: dict | None = None
    ready: bool = False  # prepared: the run goes on to the rules lock (`proceed`)


def fail_run(engine: Engine, run_id: int, code: str, detail: str | None = None) -> str:
    """Marks the run failed with "<code>: <reason>" (and the detail code, if any)."""
    reason = f"{code}: {REASONS[code]}" + (f" ({detail})" if detail else "")

    def body(conn: Connection, _stage: str):
        conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now() "
                          "WHERE run_id = :r AND status = 'running'"), dict(r=run_id))
        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
                     dict(f=reason[:500], r=run_id))

    write(engine, run_id, "orchestrator", "fail_run", body)
    return reason


def _row(engine: Engine, run_id: int):
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT r.status, r.fixed_plan, r.hypothesis_version_id, hv.sufficiency_option, h.narrower_of_run_id "
            "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
            "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=run_id)).one()


def _stored(engine: Engine, run_id: int, stage: str, done: bool = True):
    """The latest stage result of `stage` (only a done one, unless `done` is false), or None."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = :s "
                                 + ("AND status = 'done' " if done else "") + "ORDER BY id DESC LIMIT 1"),
                            dict(r=run_id, s=stage)).one_or_none()


LEFT_RUNNING = "stage_left_running"  # an agent stage still running: step 9b's recovery closes it


def _stage_code(row) -> str:
    """The fixed code a stored agent stage ended with; LEFT_RUNNING for a stage still running."""
    if row.status == "running":
        return LEFT_RUNNING
    return (row.output or {}).get("code") if isinstance(row.output, dict) else None


def _evidenced(engine: Engine, row) -> str:
    """The stage's code for deciding what follows (step 9b fix round 2, owner, 2026-10-09): a lost request
    (`recovery.RECOVERABLE`) whose spending refusal was committed is that refusal's code; the stored stage is kept as
    it is."""
    code = _stage_code(row)
    if code in RECOVERABLE:
        with engine.connect() as conn:
            return recovery.refusal_code(conn, row.id) or code
    return code


def _agent_stop(engine: Engine, run_id: int, stage: str, recovered: bool = False) -> str | None:
    """Fix round 1, finding 1: the code of a stop the role's latest stored stage holds (a recording or reservation
    failure, or a stage left running), whatever its status; None when there is no such stop. Step 9b: after recovery
    a lost request (`recovery.RECOVERABLE`) is no stop: the run goes on without asking the role again."""
    latest = _stored(engine, run_id, stage, done=False)
    if latest is None or latest.status in ("done", "skipped"):
        return None
    code = _stage_code(latest)
    if recovered and code in RECOVERABLE:
        return None
    return code if code in RUN_STOPS or code == LEFT_RUNNING else None


def _lost(engine: Engine, run_id: int, stage: str) -> int:
    """How many of the role's stages ended with a lost request (`recovery.RECOVERABLE`)."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = :s AND status = "
                                 "'failed' AND output->>'code' = ANY(:c)"),
                            dict(r=run_id, s=stage, c=list(RECOVERABLE))).scalar_one()


def _critic_failures(engine: Engine, run_id: int) -> list:
    """The codes of the Critic's stored stages that did not end done or skipped, in order (as `run_critic` reports
    its batches' failures)."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = 'critic' "
                                 "AND status NOT IN ('done', 'skipped') ORDER BY id"), dict(r=run_id)).all()
    return [_evidenced(engine, r) for r in rows]


def _exists(engine: Engine, sql: str, run_id: int) -> bool:
    with engine.connect() as conn:
        return bool(conn.execute(text(f"SELECT EXISTS ({sql})"), dict(r=run_id)).scalar_one())


def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
        recovered: bool = False) -> RunReport:
    """Runs the run to its end (completed or failed), to its wait for a person's confirmation, or leaves it running
    if a call stayed open: `prepare`, then, unless the run ended or waits there, `proceed`."""
    report = prepare(engine, run_id, ceiling=ceiling, client_options=client_options, recovered=recovered)
    if not report.ready:
        return report
    rest = proceed(engine, run_id, ceiling=ceiling, client_options=client_options, recovered=recovered)
    rest.stages = report.stages + rest.stages
    rest.question_as_tested = report.question_as_tested
    return rest


def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
            recovered: bool = False) -> RunReport:
    """Up to the rules lock: start; the narrower question's plan check, the fixed plan, or the Planner and the
    narrowing decision (the partly-sufficient path ends here). A run whose plan comes from a model's answer then
    waits (step 9a). `ready` when the run goes on to `proceed` now; the question as tested is in the report (owner's
    decision B: the command line prints it before the run goes on)."""
    report = RunReport(run_id)
    agent_kw = dict(ceiling=ceiling, client_options=client_options)
    row = _row(engine, run_id)
    if row.status == "queued":
        queries.start(engine, run_id)
    elif row.status == "completed" and _done(engine, report).outcome == "partly_sufficient":
        # Step 9a: an original completed as partly sufficient whose narrower question was not created (a stop between
        # the two) gets it now; one per run (create_narrower is idempotent; the database allows one, 0007).
        decided = _stored(engine, run_id, "narrowing")
        report.narrower_question = queries.create_narrower(engine, run_id, decided.output["narrower_scope"]).number
        return _done(engine, report)
    elif row.status != "running" and row.status != "waiting":  # ended: nothing to prepare
        return _done(engine, report)
    # Fix round 1, finding 3: a run already confirmed, or past its lock, goes on to `proceed` without waiting again.
    if _exists(engine, "SELECT 1 FROM rules_confirmation WHERE run_id = :r UNION ALL SELECT 1 FROM plan WHERE run_id = :r",
               run_id):
        with engine.connect() as conn:
            report.question_as_tested = reading.stored(conn, run_id)
        report.ready = True
        return _done(engine, report)
    if row.status == "waiting":  # waiting for a person: not stuck, nothing to prepare
        return _done(engine, report)
    try:
        # A narrower question is recognised by its link to its original, never by the run's flag (fix round,
        # finding 1): it always locks the stored narrower plan, after the source-version check (A8, B1).
        if row.narrower_of_run_id is not None:
            plan, code = _lockable(engine, run_id)
            if code:
                return _failed(engine, report, code)
            report.stages.append("fixed plan")
            report.question_as_tested = reading.from_plan(plan, "narrower")
            return _wait(engine, report)
        if row.fixed_plan:
            report.stages.append("fixed plan")
            report.question_as_tested = reading.from_plan(confirmation.reference_plan(row), "fixed")
            report.ready = True
            return _done(engine, report)
        stored = _stored(engine, run_id, "planner", done=False)
        if stored is not None and stored.status != "done":  # fix round 1, finding 1: an earlier stop stays a stop
            code = _evidenced(engine, stored)
            if recovered and code in RECOVERABLE:  # step 9b (owner, Q3): the Planner is repeated once
                if _lost(engine, run_id, "planner") > PLANNER_REPEATS:
                    return _failed(engine, report, "interrupted")
                stored = None
            elif stored.status == "running" or code in RUN_STOPS:
                return _stopped(engine, report, code)
            else:
                return _failed(engine, report, "spending_refused" if code in SPENDING else "planner_failed", code)
        if stored is None:
            result = planner.run_planner(engine, run_id, **agent_kw)
            report.stages.append("planner")
            if result.failure in RUN_STOPS:
                return _stopped(engine, report, result.failure)
            if result.failure is not None:
                return _failed(engine, report, "spending_refused" if result.failure in SPENDING else "planner_failed",
                               result.failure)
            answer, stage_id = result.answer, result.stage_id
        else:  # step 9a: a done Planner stage is used, never repeated
            answer, stage_id = planner.Answer(**stored.output["answer"]), stored.id
        report.question_as_tested = _stored_reading(engine, stage_id)
        if not answer.domain_matches:
            return _failed(engine, report, "domain_mismatch")
        decided = _stored(engine, run_id, "narrowing")
        if decided is None:
            decision = narrowing.run_narrowing(engine, run_id, answer)
            report.stages.append(f"narrowing: {decision['result']}")
        else:  # step 9a: a stored narrowing decision is used, never taken again
            decision = decided.output
        if decision["result"] == "claim_not_one_plan":
            return _failed(engine, report, "claim_not_one_plan", decision["reason"])
        if decision["result"] == "partly_sufficient":
            stop = _agent_stop(engine, run_id, "analyst", recovered)
            if stop:
                return _stopped(engine, report, stop)
            if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
                if _explain(engine, report, agent_kw) in RUN_STOPS:
                    return _stopped(engine, report, report.explanation_failure)
            if _row(engine, run_id).status == "running":
                completion.copy_partly_sufficient(engine, run_id)
            q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
            report.narrower_question = q.number
            return _done(engine, report)
        return _wait(engine, report)
    except Refused as refused:
        return _failed(engine, report, "refused", refused.code)


def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
            recovered: bool = False) -> RunReport:
    """From the rules lock to the end. A waiting run goes on only once a person has confirmed it (it is then running
    again); a waiting run that no one confirmed is left as it is. The plan is `confirmation.plan_to_lock`'s, built
    again from what is stored, so nothing is carried between the two in memory. Each step after the lock runs only
    if its stored result is absent (step 9a)."""
    report = RunReport(run_id)
    agent_kw = dict(ceiling=ceiling, client_options=client_options)
    row = _row(engine, run_id)
    try:
        if row.status == "waiting":
            if not _exists(engine, "SELECT 1 FROM rules_confirmation WHERE run_id = :r", run_id):
                return _done(engine, report)  # waiting for a person: not stuck, nothing to do
            _go_on(engine, run_id)
            row = _row(engine, run_id)
        if row.status != "running":
            raise Refused("proceed", "stage_mismatch", "the run is not running")
        if not _exists(engine, "SELECT 1 FROM plan WHERE run_id = :r", run_id):
            plan, code = _lockable(engine, run_id)
            if code:
                return _failed(engine, report, code)
            _require_confirmed(engine, run_id, plan)
            checkpoints.lock_rules(engine, run_id, plan)
            report.stages.append("rules lock")
        extract.store_records(engine, run_id)  # only the sources still pending
        if _stored(engine, run_id, "checks") is None:
            checks.run_checks(engine, run_id)
        report.stages += ["records stored", "checks"]
        if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'critic'", run_id):
            c = critic.run_critic(engine, run_id, **agent_kw)
            report.stages.append("critic")
            failures, stored = c.failures, False
        else:  # fix round 1, finding 1: the Critic's stored stages decide, as they did when it ran
            failures, stored = _critic_failures(engine, run_id), True
        # Step 9b (owner, 2026-10-08): after recovery a lost Critic request is not repeated and the run goes on. Fix
        # round 1, finding 4: only for stages stored before (those recovery processed), never for a Critic run now.
        excused = recovered and stored
        stops = [f for f in failures if (f in RUN_STOPS or f == LEFT_RUNNING) and not (excused and f in RECOVERABLE)]
        if stops:
            return _stopped(engine, report, stops[0])
        spent = [f for f in failures if f in SPENDING]
        if spent:
            return _failed(engine, report, "spending_refused", spent[0])
        if _stored(engine, run_id, "inclusion") is None:
            inclusion.decide_run(engine, run_id)
        if _stored(engine, run_id, "dataset_freeze") is None and not _exists(
                engine, "SELECT 1 FROM calibration_result WHERE run_id = :r AND analysis_result_id IS NULL "
                        "AND reason = 'no_dataset_frozen'", run_id):
            checkpoints.freeze_dataset(engine, run_id)
        if _stored(engine, run_id, "statistics") is None:
            analysis.run_statistics(engine, run_id)
        report.stages += ["inclusion", "dataset freeze", "statistics"]
        stop = _agent_stop(engine, run_id, "analyst", recovered)
        if stop:
            return _stopped(engine, report, stop)
        if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
            if _explain(engine, report, agent_kw) in RUN_STOPS:
                return _stopped(engine, report, report.explanation_failure)
        completion.copy_decision(engine, run_id)
        return _done(engine, report)
    except Refused as refused:
        return _failed(engine, report, "refused", refused.code)


def _lockable(engine: Engine, run_id: int) -> tuple[dict | None, str | None]:
    """`confirmation.plan_to_lock`'s plan, or the failure code of a narrower question whose plan cannot be locked."""
    try:
        with engine.connect() as conn:
            return confirmation.plan_to_lock(conn, run_id), None
    except confirmation.NotLockable as error:
        if error.code == "stage_mismatch":
            raise Refused("proceed", "stage_mismatch", "no Planner answer with a narrowing decision to proceed") from None
        return None, error.code


def _require_confirmed(engine: Engine, run_id: int, plan: Mapping) -> None:
    """A run that waited locks only the plan whose fingerprint the person confirmed (the database checks it too)."""
    with engine.connect() as conn:
        if not confirmation.needs_confirmation(conn, run_id):
            return
        confirmed = conn.execute(text("SELECT plan_fingerprint FROM rules_confirmation WHERE run_id = :r"),
                                 dict(r=run_id)).scalar_one_or_none()
    if confirmed != confirmation.plan_fingerprint(plan):
        raise Refused("lock_rules", "not_confirmed", "no person's confirmation of exactly this plan")


def _wait(engine: Engine, report: RunReport) -> RunReport:
    """The run waits for a named person's confirmation of the question as tested (step 9a, Q1)."""

    def body(conn: Connection, _stage: str):
        conn.execute(text("UPDATE run SET status = 'waiting' WHERE id = :r"), dict(r=report.run_id))

    write(engine, report.run_id, "orchestrator", "wait", body)
    return _done(engine, report)


def _go_on(engine: Engine, run_id: int) -> None:
    """A confirmed waiting run is running again (the database requires the confirmation, 0007)."""

    def body(conn: Connection, _stage: str):
        conn.execute(text("UPDATE run SET status = 'running' WHERE id = :r AND status = 'waiting'"), dict(r=run_id))

    write(engine, run_id, "orchestrator", "go_on", body)


def _stored_reading(engine: Engine, stage_id: int) -> dict | None:
    with engine.connect() as conn:
        return conn.execute(text("SELECT output->'question_as_tested' FROM stage_result WHERE id = :s"),
                            dict(s=stage_id)).scalar_one()


def _explain(engine: Engine, report: RunReport, agent_kw: Mapping) -> str | None:
    """The Analyst: any failure but an accounting one leaves code's decision standing (A3, B2). Returns the
    failure code, if any."""
    result = analyst.run_analyst(engine, report.run_id, **agent_kw)
    report.stages.append("analyst")
    report.explanation = result.report if result.failure is None else f"{analyst.UNAVAILABLE} ({result.failure})"
    report.explanation_failure = result.failure
    return result.failure


def _stopped(engine: Engine, report: RunReport, code: str) -> RunReport:
    """An accounting failure (finding 3): nothing more is written or requested; the run stays as it is."""
    report.failure = f"{code}: {STOPPED}"
    return _done(engine, report)


def _done(engine: Engine, report: RunReport) -> RunReport:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT status, outcome FROM run WHERE id = :r"), dict(r=report.run_id)).one()
    report.status, report.outcome = row.status, row.outcome
    return report


def _failed(engine: Engine, report: RunReport, code: str, detail: str | None = None) -> RunReport:
    try:
        report.failure = fail_run(engine, report.run_id, code, detail)
    except Refused as refused:  # a call still open (its recording failed): step 9b recovers the run
        report.failure = f"{code} ({detail}); the run could not be ended: {refused.code}"
    return _done(engine, report)


def run_guarded(payload: dict) -> dict:
    """The command line's run, in the guarded process. Only JSON-safe values cross back."""
    from decimal import Decimal
    from hypocurate.config import load_settings
    from hypocurate.db.engine import make_engine
    engine = make_engine(load_settings(web=False).database_url)
    try:
        ceiling = Decimal(payload["ceiling"]) if payload.get("ceiling") is not None else None
        phase = {"prepare": prepare, "proceed": proceed}.get(payload.get("phase"), run)
        r = phase(engine, int(payload["run_id"]), ceiling=ceiling, client_options=payload.get("client_options"))
        return json.loads(json.dumps(r.__dict__, default=str))
    finally:
        engine.dispose()


def work_guarded(payload: dict) -> dict:
    """The worker's child (step 9b): holds the run's work lock on its own connection for its whole work (another child
    of the same run is refused it and returns `busy`, writing nothing), then runs the phase. The lock goes when this
    process ends, however it ends."""
    from hypocurate.config import load_settings
    from hypocurate.db.engine import make_engine
    from hypocurate.pipeline import queue
    engine = make_engine(load_settings(web=False).database_url, worker_session=True)
    run_id = int(payload["run_id"])
    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    try:
        holder.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-work-{run_id}"))
        if not holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(run_id))).scalar():
            return {"busy": True}
        if payload.get("claim_id") is not None:  # step 9b fix round 1, finding 3: the work is bound to this claim
            from hypocurate.pipeline import writes
            writes.OWNER = (int(payload["claim_id"]), holder.execute(text("SELECT pg_backend_pid()")).scalar())
            with engine.connect() as conn:
                if not writes.owner_holds(conn, run_id):
                    return {"busy": True}
        phase = {"prepare": prepare, "proceed": proceed}.get(payload.get("phase"), run)
        r = phase(engine, run_id, client_options=payload.get("client_options"),
                  recovered=bool(payload.get("recovered")))
        return json.loads(json.dumps(r.__dict__, default=str))
    finally:
        holder.close()
        engine.dispose()
