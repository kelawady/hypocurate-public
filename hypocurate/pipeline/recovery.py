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
# How an Analyst stage closed by recovery is shown (owner, Q3); tests check it is agents.analyst.UNAVAILABLE's wording.
ANALYST_INTERRUPTED = "explanation unavailable (interrupted)"
EXHAUSTED = ("attempts_exhausted: the run stopped at {stage} {n} times without finishing; dispatch it again as a new "
             "run")


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
        stages = conn.execute(text(
            "UPDATE stage_result SET status = 'failed', finished_at = now(), output = coalesce(output, '{}'::jsonb) "
            "|| jsonb_build_object('code', 'interrupted') || CASE WHEN stage = 'analyst' THEN "
            "jsonb_build_object('shown', CAST(:shown AS text)) ELSE '{}'::jsonb END "
            "WHERE run_id = :r AND status = 'running'"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount
        earlier = conn.execute(text(
            "SELECT count(*) FROM run_claim WHERE run_id = :r AND released_at IS NOT NULL "
            "AND release_reason NOT IN ('waiting', 'finished')"), dict(r=run_id)).scalar_one()
        found = {"calls_closed": calls, "stages_closed": stages, "recoveries": earlier + 1}
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
