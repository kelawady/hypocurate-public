"""Copying the stored decision onto the run (build step 7; owner, 2026-10-05).

`copy_decision` **only copies**. It writes the decision stored by the analysis stage (outcome,
verdict, exploratory label and evidence level, in the "statistics" stage result) onto the run and
completes it, unchanged; it computes nothing. It refuses, and logs the refusal, when the stored
decision is missing (`decision_missing`) or belongs to a different freeze fingerprint than the
run's (`decision_not_current`; a run with no dataset frozen has a decision with no fingerprint,
and a run with a freeze must have the decision of that freeze).

The orchestrator (steps 8 and 9) calls it after the Analyst. "Partly sufficient" is not set here:
how it reaches the run is a step 8 decision (proposal: its own stored code decision, copied by the
same fingerprint-checked path). The database checks the copy again (run CHECKs and the
`hc_run_update` trigger: a sufficient outcome needs one pooled result that passed both validity
checks and, under the fixed option, the minimums met; the evidence level must agree with the
outcome, verdict and exploratory label).
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline.writes import Refused, write

ROLE = "completion"


def copy_decision(engine: Engine, run_id: int) -> dict:
    """Completes the run with its stored decision; returns the decision copied."""

    def body(conn: Connection, stage: str):
        if stage not in ("analysis", "closed_without_freeze"):
            raise Refused("copy_decision", "stage_mismatch")
        output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' "
                                   "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
        decision = output.get("decision") if isinstance(output, dict) else None
        if not isinstance(decision, dict):
            raise Refused("copy_decision", "decision_missing")
        snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                dict(r=run_id)).scalar_one_or_none()
        if decision.get("freeze_fingerprint") != snapshot:
            raise Refused("copy_decision", "decision_not_current")
        conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
                          "exploratory = :x, evidence_level = :e WHERE id = :r"),
                     dict(o=decision["outcome"], v=decision["verdict"], x=decision["exploratory"],
                          e=decision["evidence_level"], r=run_id))
        return decision

    return write(engine, run_id, ROLE, "copy_decision", body)
