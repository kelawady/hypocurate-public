"""How long since a run last wrote anything (step 9b, A4; moved here from `pipeline.queue` in step 10a so that the
screens can show it without importing the queue).

Read-only. The worker's stall limit uses the same query through `queue`, which imports it from here; the screens and
the command line's `queue` use it through `pipeline.run_view`. The web service imports neither the queue nor the
worker (tests/test_web_isolation.py).
"""
from __future__ import annotations

from sqlalchemy import Connection, text

_LAST_WRITE = text("""
    SELECT extract(epoch FROM clock_timestamp() - greatest(
        r.queued_at, r.started_at, r.completed_at, r.failed_at,
        (SELECT max(greatest(started_at, finished_at)) FROM stage_result WHERE run_id = r.id),
        (SELECT max(greatest(started_at, finished_at)) FROM model_call WHERE run_id = r.id),
        (SELECT max(decided_at) FROM run_source WHERE run_id = r.id),
        (SELECT max(created_at) FROM record WHERE extraction_run_id = r.id),
        (SELECT max(confirmed_at) FROM rules_confirmation WHERE run_id = r.id),
        (SELECT locked_at FROM plan WHERE run_id = r.id),
        (SELECT frozen_at FROM run_snapshot WHERE run_id = r.id)))
    FROM run r WHERE r.id = :r""")


def seconds_since_last_write(conn: Connection, run_id: int) -> float:
    """A4: seconds since the run last wrote anything that shows progress (its status times, a stage or call started or
    finished, a source searched, a record stored, the confirmation, the lock, the freeze)."""
    return float(conn.execute(_LAST_WRITE, dict(r=run_id)).scalar_one())
