"""A run's stage, read from the database (never taken from the caller).

Called inside the access layer's transaction, after `hc_write_lock` has locked the run, so
the stage cannot change between this check and the read that follows.
"""
from __future__ import annotations

from sqlalchemy import Connection, text


def actual_stage(conn: Connection, run_id: int, status: str) -> str:
    """The stage of run `run_id`, whose locked status is `status` (from `hc_write_lock`)."""
    if status == "completed":
        frozen = conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r)"),
                              dict(r=run_id)).scalar_one()
        return "final" if frozen else "final_without_freeze"
    if status != "running":  # queued, failed
        return "none"
    row = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'narrowing' AND status = 'done' "
        "AND output->>'result' = 'partly_sufficient') AS narrowed, "
        "EXISTS (SELECT 1 FROM plan WHERE run_id = :r) AS locked, "
        "EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r) AS frozen, "
        "EXISTS (SELECT 1 FROM calibration_result WHERE run_id = :r AND analysis_result_id IS NULL "
        "AND reason = 'no_dataset_frozen') AS closed"), dict(r=run_id)).one()
    if not row.locked:
        # Step 8b (A4): after code's narrowing decision of partly sufficient, no plan is ever locked.
        return "narrowed" if row.narrowed else "before_lock"
    if row.frozen:
        return "analysis"
    if row.closed:
        return "closed_without_freeze"
    return "curation"
