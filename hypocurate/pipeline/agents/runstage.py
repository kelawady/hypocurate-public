"""An agent's stage within a run (step 8b): opened before any request, closed after the answer is checked.

`open_stage` writes, in one short transaction under the run's lock (the locking protocol), a running
stage result for the role and the one invocation record of the agent call (0005: the invocation names
the run, the stage and the role, and its setting is the one the run recorded at dispatch). It commits
before the access read and before any request, so no model call ever runs inside a database
transaction (the request path's own transactions are in `spend`). `close_stage` writes the stage's
output and its status ('done' or 'failed') in another locked transaction. Neither ever holds a
transaction open across a request.
"""
from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.pipeline.writes import Refused, write


def open_stage(engine: Engine, run_id: int, role: str, stage: str) -> tuple[int, int]:
    """(stage result id, invocation id) for one agent call of `role` at `stage` of the run."""

    def body(conn: Connection, _actual: str):
        row = conn.execute(text("SELECT ras.agent_setting_id, a.model FROM run_agent_setting ras JOIN agent_setting a "
                                "ON a.id = ras.agent_setting_id WHERE ras.run_id = :r AND ras.role = :o"),
                           dict(r=run_id, o=role)).one_or_none()
        if row is None:
            raise Refused(f"open_{role}", "stage_mismatch", "the role's settings were not recorded at dispatch")
        sid = conn.execute(text(
            "INSERT INTO stage_result (run_id, stage, attempt, role, agent_setting_id, model) VALUES (:r, :s, "
            "(SELECT coalesce(max(attempt), 0) + 1 FROM stage_result WHERE run_id = :r AND stage = :s), :o, :a, :m) "
            "RETURNING id"), dict(r=run_id, s=stage, o=role, a=row.agent_setting_id, m=row.model)).scalar_one()
        inv = conn.execute(text("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
                                "VALUES ('run', :r, :s, :o, :a) RETURNING id"),
                           dict(r=run_id, s=sid, o=role, a=row.agent_setting_id)).scalar_one()
        return sid, inv

    return write(engine, run_id, role, f"open_{role}", body)


def close_stage(engine: Engine, run_id: int, stage_id: int, status: str, output: Mapping[str, Any],
                input_: Mapping[str, Any] | None = None) -> None:
    """Writes the stage's output (and the input it was given, as stored facts) and its final status."""

    def body(conn: Connection, _actual: str):
        conn.execute(text("UPDATE stage_result SET status = :st, finished_at = now(), output = :o, input = :i "
                          "WHERE id = :s AND run_id = :r").bindparams(bindparam("o", type_=JSONB),
                                                                       bindparam("i", type_=JSONB)),
                     dict(st=status, o=dict(output), i=dict(input_) if input_ is not None else None, s=stage_id,
                          r=run_id))

    write(engine, run_id, "agent", "close_stage", body)
