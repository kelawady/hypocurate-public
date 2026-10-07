"""The orchestrator: one run, stage by stage (step 8b; PRD 3; the run order of the step 8 plan, corrected by the
owner's answer A1; register 'run_order').

    Planner -> narrowing decision (code, before any lock)
      partly sufficient: Analyst (narrowing facts) -> copy_partly_sufficient -> narrower question; stop
      claim not one plan: the run fails before the lock (A11)
    -> rules lock -> store records -> Checks -> Critic -> Inclusion -> dataset freeze -> statistics
    -> Analyst -> completion (copy_decision)

A narrower question's run bypasses the Planner (and the narrowing): it locks exactly the narrower plan its
original's narrowing decision stored (A8), after checking that the run's source versions are those the counts
were taken on (B1). It is recognised by the question's link to its original, never by a flag (fix round,
finding 1); the database refuses its plan otherwise (0006). A fixed-plan run of an ordinary question uses the
reference plan of criterion 14.1a.

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
recording failed stays started) for step 9's recovery; `run` reports it (fix round, finding 3).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion, narrowing, queries
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline.agents import analyst, critic, planner
from hypocurate.pipeline.agents.lm import RUN_STOPS
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


def _narrower_plan(engine: Engine, run_id: int, original: int, version_id: int) -> tuple[dict | None, str | None]:
    """The narrower plan stored by the original's narrowing decision, for this run (A8), or a failure code."""
    with engine.connect() as conn:
        out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :o AND stage = 'narrowing' "
                                "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(o=original)).scalar_one_or_none()
        current = sorted(tuple(r) for r in conn.execute(text(
            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
            "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
    if not isinstance(out, dict) or not isinstance(out.get("narrower_plan"), dict):
        return None, "narrower_plan_missing"
    stored = sorted((s["source"], s["version_fingerprint"]) for s in out.get("sources") or [])
    if stored != current:  # B1
        return None, "narrowing_sources_changed"
    body = out["narrower_plan"]
    if plans.fingerprint(body) != out.get("narrower_plan_fingerprint"):
        return None, "narrower_plan_missing"
    return {"hypothesis_version": version_id, **body}, None


def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
    """Runs the run to its end (completed or failed), or leaves it running if a call stayed open."""
    report = RunReport(run_id)
    agent_kw = dict(ceiling=ceiling, client_options=client_options)
    row = _row(engine, run_id)
    if row.status == "queued":
        queries.start(engine, run_id)
    try:
        # A narrower question is recognised by its link to its original, never by the run's flag (fix round,
        # finding 1): it always locks the stored narrower plan, after the source-version check (A8, B1).
        if row.narrower_of_run_id is not None:
            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
            if code:
                return _failed(engine, report, code)
            report.stages.append("fixed plan")
        elif row.fixed_plan:
            plan = plans.reference_plan(row.hypothesis_version_id)
            plan["sufficiency"]["option"] = row.sufficiency_option
            report.stages.append("fixed plan")
        else:
            result = planner.run_planner(engine, run_id, **agent_kw)
            report.stages.append("planner")
            if result.failure in RUN_STOPS:
                return _stopped(engine, report, result.failure)
            if result.failure is not None:
                return _failed(engine, report, "spending_refused" if result.failure in SPENDING else "planner_failed",
                               result.failure)
            answer = result.answer
            if not answer.domain_matches:
                return _failed(engine, report, "domain_mismatch")
            decision = narrowing.run_narrowing(engine, run_id, answer)
            report.stages.append(f"narrowing: {decision['result']}")
            if decision["result"] == "claim_not_one_plan":
                return _failed(engine, report, "claim_not_one_plan", decision["reason"])
            if decision["result"] == "partly_sufficient":
                if _explain(engine, report, agent_kw) in RUN_STOPS:
                    return _stopped(engine, report, report.explanation_failure)
                completion.copy_partly_sufficient(engine, run_id)
                q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
                report.narrower_question = q.number
                return _done(engine, report)
            plan = planner.build_plan(row.hypothesis_version_id, answer.claim_scope, answer.outcome,
                                      answer.exclusion_rules, row.sufficiency_option)
        checkpoints.lock_rules(engine, run_id, plan)
        report.stages.append("rules lock")
        extract.store_records(engine, run_id)
        checks.run_checks(engine, run_id)
        report.stages += ["records stored", "checks"]
        c = critic.run_critic(engine, run_id, **agent_kw)
        report.stages.append("critic")
        stops = [f for f in c.failures if f in RUN_STOPS]
        if stops:
            return _stopped(engine, report, stops[0])
        spent = [f for f in c.failures if f in SPENDING]
        if spent:
            return _failed(engine, report, "spending_refused", spent[0])
        inclusion.decide_run(engine, run_id)
        checkpoints.freeze_dataset(engine, run_id)
        analysis.run_statistics(engine, run_id)
        report.stages += ["inclusion", "dataset freeze", "statistics"]
        if _explain(engine, report, agent_kw) in RUN_STOPS:
            return _stopped(engine, report, report.explanation_failure)
        completion.copy_decision(engine, run_id)
        return _done(engine, report)
    except Refused as refused:
        return _failed(engine, report, "refused", refused.code)


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
    except Refused as refused:  # a call still open (its recording failed): step 9 recovers the run
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
        r = run(engine, int(payload["run_id"]), ceiling=ceiling, client_options=payload.get("client_options"))
        return json.loads(json.dumps(r.__dict__, default=str))
    finally:
        engine.dispose()
