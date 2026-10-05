"""The access object: one per role, stage and run (PRD 4).

Every read an agent's code path makes goes through `Access.get(field)`. Each call is one
transaction (`run_transaction`, retried on 40P01 / 40001), in this order:

1. `SET LOCAL lock_timeout`, then `hc_write_lock(p_run => run)`: the locking protocol of
   step 3 (the audit row is a write to the run), which also fixes the run's stage until
   commit;
2. the run's actual stage, read from the database (`stage.actual_stage`);
3. the checks: the declared stage equals the actual one, and the field is on the role's
   list for that stage (`allowlist.allowed`);
4. the read, by the field's function (`fields.READERS`), which may still refuse;
5. one `audit_log` row: role, declared stage, field, allowed or denied, and in `detail`
   the actual stage and the reason, never a value;
6. commit.

A refusal writes its denied row and commits, and only then raises `AccessDenied`, so the
row survives the rejection: it is never inside a transaction the caller could roll back.
The object owns its engine and never accepts the caller's connection.

**Never call the access layer while holding a run's lock** (a write transaction that has
called `hc_write_lock` for the same run): the access transaction would wait for it. The
lock timeout turns that wait into an error instead of a hang.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.allowlist import ROLES, STAGES, allowed
from hypocurate.access.errors import AccessDenied
from hypocurate.access.fields import READERS, Context, Refused
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction

# How long an access call waits for a run's lock before failing (milliseconds).
ACCESS_LOCK_TIMEOUT_MS = 5000

_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :field, :allowed, :detail)").bindparams(bindparam("detail", type_=JSONB))


class Access:
    """What one role may read from one run at one stage."""

    def __init__(self, engine: Engine, run_id: int, role: str, stage: str, source_key: str | None = None,
                 lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS):
        self._engine = engine
        self.run_id = int(run_id)
        self.role = role
        self.stage = stage
        self.source_key = source_key
        self._lock_timeout_ms = int(lock_timeout_ms)

    def __repr__(self) -> str:
        return f"Access(run={self.run_id}, role={self.role!r}, stage={self.stage!r})"

    def get(self, field: str) -> Any:
        """The field's content, or AccessDenied (already logged)."""
        outcome = run_transaction(self._engine, lambda conn: self._call(conn, field))
        if outcome[0] == "denied":
            raise AccessDenied(self.role, self.stage, field, outcome[1])
        return outcome[1]

    def _call(self, conn: Connection, field: str) -> tuple[str, Any]:
        conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=self.run_id)).scalar_one()
        actual = actual_stage(conn, self.run_id, status)
        reason = self._refusal(field, actual)
        if reason is None:
            try:
                value = READERS[field](conn, Context(self.run_id, self.role, self.source_key))
            except Refused as refused:
                reason = str(refused)
        detail: dict[str, Any] = {"actual_stage": actual}
        if self.source_key is not None:
            detail["source"] = self.source_key
        if reason is not None:
            detail["reason"] = reason
        conn.execute(_AUDIT, dict(r=self.run_id, role=self.role, stage=self.stage, field=field,
                                  allowed=reason is None, detail=detail))
        return ("denied", reason) if reason is not None else ("allowed", value)

    def _refusal(self, field: str, actual: str) -> str | None:
        if self.role not in ROLES:
            return f"unknown role {self.role!r}"
        if self.stage not in STAGES:
            return f"unknown stage {self.stage!r}"
        if self.stage != actual:
            return f"the run is at stage {actual!r}, not {self.stage!r}"
        if field not in allowed(self.role, actual):
            return f"{field!r} is not on the {self.role}'s list at stage {actual!r}"
        if field not in READERS:  # listed but not implemented: never silently empty
            return f"no reader for {field!r}"
        return None
