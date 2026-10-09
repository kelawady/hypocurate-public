"""Recovery of a run taken up again (build step 9b; docs/reviews/step09b_plan.md, "Recovery"; register
'recovery_policy').

When a worker claims a run that is already running (its worker died, it was shut down, it stopped on a recording or
reservation failure, or its child was stuck), `recover` does the bookkeeping first, in one transaction under the
run's lock (the locking protocol):
1. every model call of the run still `started` is closed `interrupted`, with no usage, so it keeps counting at its
   reserved maximum in every cap and total (code `recording_failed` when its stage ended on a recording failure,
   else `worker_stopped`);
2. every stage still `running` is closed `failed` with code `interrupted`;
3. if the run has now been taken up more than `MAX_RECOVERIES` times, it fails: `attempts_exhausted`.
It writes no plan, record, set, freeze or confirmation; forward progress goes only through the normal path (the
orchestrator, which takes every step from stored rows) and its database guards. The worker then runs the orchestrator
with `recovered=True`, which applies the owner's rule, split by cause (2026-10-08):
- an interruption, a recording failure, or any database failure while saving a call (`RECOVERABLE`): the Q3 per-role
  rule. The Planner is repeated once (`PLANNER_REPEATS`; a second loss fails the run); the Critic's remaining batches
  are skipped; after the Analyst the run completes with "explanation unavailable";
- a spending refusal stays a stop, exactly as in 9a.
What was found is recorded on the claim's release.

Imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import Connection, Engine, text

from hypocurate.db.retry import run_transaction

LOG = logging.getLogger("hypocurate.worker")
MAX_RECOVERIES = 3   # the owner's approved value (step 9 plan; register 'recovery_policy')
PLANNER_REPEATS = 1  # owner, Q3
# The stops recovery takes up by the per-role rule (owner, 2026-10-08): the request was lost, or the database could not
# save the call. A spending refusal is never among them.
RECOVERABLE = ("interrupted", "recording_failed", "reservation_failed")
LOCK_TIMEOUT_MS = 5000
# The refusals a stage keeps as its cause (spend.CODES; the curation cap never applies to a run).
SPENDING_CODES = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
# How an Analyst stage closed by recovery is shown (owner, Q3); tests check it is agents.analyst.UNAVAILABLE's wording.
ANALYST_INTERRUPTED = "explanation unavailable (interrupted)"
EXHAUSTED = ("attempts_exhausted: the run stopped at {stage} {n} times without finishing; dispatch it again as a new "
             "run")


def finish_narrower_questions(engine: Engine) -> list[str]:
    """The worker's sweep: an original completed as partly sufficient whose narrower question was not created (the
    worker stopped between the copy and the question; no worker claims a completed run) gets it now, and a draft left
    by such a stop is submitted. Never a second one (`queries.create_narrower`; one per run, 0007). Returns the numbers."""
    from hypocurate.pipeline import queries
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT r.id, (SELECT s.output FROM stage_result s WHERE s.run_id = r.id AND s.stage = 'narrowing' AND "
            "s.status = 'done' ORDER BY s.id DESC LIMIT 1) AS decision FROM run r WHERE r.status = 'completed' AND "
            "r.outcome = 'partly_sufficient' AND (NOT EXISTS (SELECT 1 FROM hypothesis h WHERE h.narrower_of_run_id = "
            "r.id) OR EXISTS (SELECT 1 FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE "
            "h.narrower_of_run_id = r.id AND hv.status = 'draft'))")).all()
    done = []
    for run_id, decision in rows:
        if isinstance(decision, dict) and isinstance(decision.get("narrower_scope"), dict):
            done.append(queries.create_narrower(engine, run_id, decision["narrower_scope"]).number)
            LOG.info(json.dumps({"narrower_question_finished": run_id}))
    return done


def recover(engine: Engine, run_id: int) -> dict:
    """Recovery's bookkeeping for a running run that a worker has just claimed; what was found."""

    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        if status != "running":
            return {"status": status}
        calls = conn.execute(text(
            "UPDATE model_call mc SET status = 'interrupted', finished_at = now(), error = CASE WHEN EXISTS ("
            "SELECT 1 FROM stage_result s WHERE s.id = mc.stage_result_id AND s.status = 'failed' AND "
            "s.output->>'code' = 'recording_failed') THEN 'recording_failed' ELSE 'worker_stopped' END "
            "WHERE mc.run_id = :r AND mc.status = 'started'"), dict(r=run_id)).rowcount
        # Fix round 1, finding 1: a running stage whose request was refused by a spending cap (the refusal's record,
        # committed with the decision) keeps that cause; only a stage with no such record was interrupted.
        refused = conn.execute(text(
            "UPDATE stage_result s SET status = 'failed', finished_at = now(), output = coalesce(s.output, '{}'::jsonb) "
            "|| jsonb_build_object('code', a.code) || CASE WHEN s.stage = 'analyst' THEN jsonb_build_object('shown', "
            "'explanation unavailable (' || a.code || ')') ELSE '{}'::jsonb END "
            "FROM (SELECT DISTINCT ON (i.stage_result_id) i.stage_result_id, al.detail->>'code' AS code "
            "      FROM agent_invocation i JOIN audit_log al ON al.function = 'model_call' AND NOT al.allowed "
            "      AND al.detail->>'invocation' = i.id::text AND al.detail->>'code' = ANY(:codes) "
            "      WHERE i.run_id = :r ORDER BY i.stage_result_id, al.id DESC) a "
            "WHERE s.id = a.stage_result_id AND s.run_id = :r AND s.status = 'running'"),
            dict(r=run_id, codes=list(SPENDING_CODES))).rowcount
        stages = refused + conn.execute(text(
            "UPDATE stage_result SET status = 'failed', finished_at = now(), output = coalesce(output, '{}'::jsonb) "
            "|| jsonb_build_object('code', 'interrupted') || CASE WHEN stage = 'analyst' THEN "
            "jsonb_build_object('shown', CAST(:shown AS text)) ELSE '{}'::jsonb END "
            "WHERE run_id = :r AND status = 'running'"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount
        earlier = conn.execute(text(
            "SELECT count(*) FROM run_claim WHERE run_id = :r AND released_at IS NOT NULL "
            "AND release_reason NOT IN ('waiting', 'finished')"), dict(r=run_id)).scalar_one()
        found = {"calls_closed": calls, "stages_closed": stages, "refusals_kept": refused, "recoveries": earlier + 1}
        if earlier + 1 > MAX_RECOVERIES:
            from hypocurate.access.stage import actual_stage
            stage = actual_stage(conn, run_id, status)
            reason = EXHAUSTED.format(stage=stage.replace("_", " "), n=earlier + 1)
            conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
                         dict(f=reason, r=run_id))
            found["failed"] = reason
        return found

    found = run_transaction(engine, body)
    LOG.info(json.dumps({"recovered": run_id, **found}))
    return found
