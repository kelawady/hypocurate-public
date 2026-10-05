"""Shared write path of the step 6 pipeline: the locking protocol, refusals and their log.

**Every write follows the protocol of step 3** (README, "Database migrations"): one
`run_transaction` (retried on 40P01 / 40001), `SET LOCAL lock_timeout`, then
`hc_write_lock(p_run => …)` before anything is written to the run or its child rows.

**Reads and writes are apart.** Inclusion and Checks read through their access objects
(`dispatch.bind_code`), each read one transaction under the run's lock; never call the access
layer while holding the run's lock. The write transaction that follows takes the lock again
and re-checks, by ids and codes only (never record values), that nothing it read has changed
since: the stage, the records, the flags, the decisions.

**A refusal is logged, then raised** (PRD 14.2: changes after a checkpoint are rejected and
logged). Our own refusals (the stage has moved on, something changed since it was read,
constructed data in a run not marked as a test) and the database's (a trigger or a
constraint) are written to `audit_log` in their own short transaction **without**
`hc_write_lock`: the named exception of step 5 (register entry
'audit_failure_rows_without_run_lock'), extended in step 6 to refusals of these write paths
(owner, 2026-10-05). The row holds the function, a fixed code and, for a database refusal,
the database's own message (our triggers' fixed texts). If the database cannot take the row,
the process log (`hypocurate.pipeline`) is the fallback.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError, IntegrityError

from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction

LOG = logging.getLogger("hypocurate.pipeline")
LOCK_TIMEOUT_MS = ACCESS_LOCK_TIMEOUT_MS
# The roles under which the pipeline's own writes are logged.
WRITE_ROLES = ("extraction", "checks", "inclusion", "checkpoint")
CODES = {
    "stage_mismatch": "the run is not at the stage this step needs",
    "changed_since_read": "the run's records, flags or decisions changed after they were read",
    "already_done": "this step has already been done for the run",
    "constructed_data_unmarked": "constructed test data in a run not marked as a test",
    "rejected_by_database": "the database refused the write",
    "invalid_plan": "the plan is not valid for the supported template",
    "tag_not_available": "a tag value of the plan is not an approved value of the fixed lists",
}
CONSTRUCTED_MARK = "constructed_test_data"


class Refused(Exception):
    """A pipeline write refused; already logged in audit_log (or the process log)."""

    def __init__(self, function: str, code: str, message: str | None = None):
        self.function, self.code, self.message = function, code, message
        super().__init__(f"{function} refused: {CODES[code]}" + (f" ({message})" if message else ""))


_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :f, false, :d)").bindparams(bindparam("d", type_=JSONB))


def log_refusal(engine: Engine, run_id: int, role: str, function: str, code: str, message: str | None = None) -> None:
    """One refusal row in its own transaction, without the run lock (the named exception)."""
    detail: dict[str, Any] = {"result": "rejected", "code": code}
    if message:
        detail["message"] = message[:300]

    def write(conn: Connection):
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
        stage = actual_stage(conn, run_id, status) if status else "none"
        conn.execute(_AUDIT, dict(r=run_id if status else None, role=role, stage=stage, f=function, d=detail))

    try:
        run_transaction(engine, write)
    except Exception as error:  # the database is unavailable: the process log is the fallback
        LOG.error(json.dumps({"refusal_fallback": {"run": run_id, "role": role, "function": function, **detail},
                              "error": type(error).__name__}, sort_keys=True))


def database_message(error: DBAPIError) -> str:
    """The database's own refusal text: the first line, our triggers' fixed messages."""
    orig = getattr(error, "orig", None)
    diag = getattr(orig, "diag", None)
    primary = getattr(diag, "message_primary", None)
    return (primary or str(orig or error)).splitlines()[0][:300]


def write(engine: Engine, run_id: int, role: str, function: str, body: Callable[[Connection, str], Any]) -> Any:
    """Runs `body(conn, stage)` in one locked transaction; logs and raises any refusal."""

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(LOCK_TIMEOUT_MS)}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        return body(conn, actual_stage(conn, run_id, status))

    try:
        return run_transaction(engine, transaction)
    except Refused as refused:
        log_refusal(engine, run_id, role, function, refused.code, refused.message)
        raise
    except IntegrityError as error:
        message = database_message(error)
        log_refusal(engine, run_id, role, function, "rejected_by_database", message)
        raise Refused(function, "rejected_by_database", message) from None


def constructed_unmarked(conn: Connection, run_id: int, source_keys: list[str]) -> bool:
    """True if any of `source_keys` is constructed test data and the run is not marked as a test."""
    from hypocurate.sources.versions import SOURCES
    if not any(SOURCES[k].constructed for k in source_keys if k in SOURCES):
        return False
    flags = conn.execute(text("SELECT experiment_flags FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
    return not (isinstance(flags, dict) and flags.get(CONSTRUCTED_MARK) is True)


def run_record_sources(conn: Connection, run_id: int) -> list[str]:
    return list(conn.execute(text(
        "SELECT DISTINCT s.key FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
        "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r"), dict(r=run_id)).scalars())


def record_ids(conn: Connection, run_id: int) -> list[int]:
    return list(conn.execute(text("SELECT id FROM record WHERE extraction_run_id = :r ORDER BY id"),
                             dict(r=run_id)).scalars())


def flag_index(conn: Connection, run_id: int) -> list[tuple[int, str, str, tuple[int, ...]]]:
    rows = conn.execute(text(
        "SELECT f.id, f.kind, f.category, coalesce(array_agg(fr.record_id ORDER BY fr.record_id) "
        "FILTER (WHERE fr.record_id IS NOT NULL), '{}') FROM flag f LEFT JOIN flag_record fr ON fr.flag_id = f.id "
        "WHERE f.run_id = :r GROUP BY f.id ORDER BY f.id"), dict(r=run_id)).all()
    return [(i, k, c, tuple(ids)) for i, k, c, ids in rows]


def code_stage(conn: Connection, run_id: int, stage: str, input_: dict, output: dict) -> int:
    """A finished stage result of a code step (role NULL): written running, then done."""
    sid = conn.execute(text(
        "INSERT INTO stage_result (run_id, stage, attempt, role, input) VALUES (:r, :s, "
        "(SELECT coalesce(max(attempt), 0) + 1 FROM stage_result WHERE run_id = :r AND stage = :s), NULL, :i) "
        "RETURNING id").bindparams(bindparam("i", type_=JSONB)), dict(r=run_id, s=stage, i=input_)).scalar_one()
    conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = :o WHERE id = :s")
                 .bindparams(bindparam("o", type_=JSONB)), dict(o=output, s=sid))
    return sid
