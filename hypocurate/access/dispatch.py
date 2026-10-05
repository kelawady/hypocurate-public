"""The trusted dispatcher: the only way to obtain an access object (step 5 review, finding 2).

`bind(engine, run_id, agent_setting_id, source_key=None)` is called by trusted orchestration
code (steps 8 and 9) for one agent call. It never takes a role, a stage or a run chosen by
anything a model controls:
- the **role** is read from the run's recorded agent settings (`run_agent_setting`): the
  setting being invoked must be recorded for this run, and its role is the one recorded;
- the **stage** is read from the database;
- a **source** is bound only for the Curator, and must be one of the run's `run_source` rows
  with a recorded version.
The result is an `Access` around an immutable `AccessContext`. The binding itself is
logged (function "bind"): allowed, denied with its code, or failed. Every later read checks
again that the run is still at the bound stage.

Nothing a model controls ever receives SQL, a database connection or a file path (CLAUDE.md):
agents get text built from `role_input` and from reads through this object only.

`bind_code(engine, run_id, role)` (step 6, owner 2026-10-05) binds the two **code roles** of
PRD 4, Inclusion and Checks, which have no agent setting. It is called by trusted pipeline
code (`hypocurate.pipeline`) only. It refuses any other role (`not_a_code_role`), reads the
stage from the database, and binds only where the role has fields (the curation stage);
elsewhere it is refused with `empty_list`. Every bind is logged like an agent's. An agent
setting can never bind as a code role: `bind` reads the role from `run_agent_setting`, whose
roles are the five agent roles (a database CHECK).
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError

from hypocurate.access.allowlist import CODE_ROLES, allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.layer import (_AUDIT, _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, DENIALS, Access, _detail, _row,
                                     bounded_source, keep_in_process_log, log_failure)
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction, sqlstate

UNBOUND = "invalid"  # the role logged for a binding refused before a role is known


def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | None = None,
         lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
    """An access object for one agent call, or AccessDenied / AccessFailed (logged)."""
    if not isinstance(run_id, int) or isinstance(run_id, bool) or not isinstance(agent_setting_id, int):
        raise TypeError("bind takes an integer run id and an integer agent setting id")
    probe = AccessContext(run_id, UNBOUND, UNBOUND, source_key, agent_setting_id)

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=run_id)).scalar_one():
            return ("unknown_run", None)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        stage = actual_stage(conn, run_id, status)
        role = conn.execute(text("SELECT role FROM run_agent_setting WHERE run_id = :r AND agent_setting_id = :a"),
                            dict(r=run_id, a=agent_setting_id)).scalar_one_or_none()
        ctx = AccessContext(run_id, role or UNBOUND, stage, source_key, agent_setting_id)
        code = None
        if role is None:
            code = "setting_not_recorded"
        elif role != "curator" and source_key is not None:
            code = "source_not_for_role"
        elif role == "curator" and source_key is None:
            code = "no_source"
        elif role == "curator" and not conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM run_source rs JOIN source s ON s.id = rs.source_id "
                "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL)"),
                dict(r=run_id, k=source_key)).scalar_one():
            code = "source_not_recorded"
        extra = {"agent_setting": agent_setting_id}
        result = "denied" if code else "allowed"
        conn.execute(_AUDIT, _row(ctx, run_id, "bind", code is None, _detail(ctx, result, code, stage, **extra)))
        return (result, code, ctx)

    failure = None
    try:
        outcome = run_transaction(engine, transaction)
    except DBAPIError as error:
        failure = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
        keep_in_process_log(probe, "bind", failure, error)
    if failure is not None:  # raised outside the handler: nothing of the original travels with it
        log_failure(engine, probe, "bind", failure, agent_setting=agent_setting_id)
        raise AccessFailed(UNBOUND, UNBOUND, "bind", failure)
    if outcome[0] == "unknown_run":
        log_failure(engine, probe, "bind", "unknown_run", run_known=False, agent_setting=agent_setting_id)
        raise AccessFailed(UNBOUND, UNBOUND, "bind", "unknown_run")
    result, code, ctx = outcome
    if result == "denied":
        raise AccessDenied(ctx.role, ctx.stage, "bind", code, DENIALS[code])
    return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)


def bind_code(engine: Engine, run_id: int, role: str, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
    """An access object for a code role (Inclusion or Checks), or AccessDenied / AccessFailed
    (logged)."""
    if not isinstance(run_id, int) or isinstance(run_id, bool):
        raise TypeError("bind_code takes an integer run id")
    named = role if isinstance(role, str) and role in CODE_ROLES else UNBOUND
    probe = AccessContext(run_id, named, UNBOUND)

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=run_id)).scalar_one():
            return ("unknown_run", None)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        stage = actual_stage(conn, run_id, status)
        ctx = AccessContext(run_id, named, stage)
        code = None
        if named == UNBOUND:
            code = "not_a_code_role"
        elif not allowed(named, stage):
            code = "empty_list"
        result = "denied" if code else "allowed"
        conn.execute(_AUDIT, _row(ctx, run_id, "bind", code is None, _detail(ctx, result, code, stage, code_role=True)))
        return (result, code, ctx)

    failure = None
    try:
        outcome = run_transaction(engine, transaction)
    except DBAPIError as error:
        failure = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
        keep_in_process_log(probe, "bind", failure, error)
    if failure is not None:
        log_failure(engine, probe, "bind", failure, code_role=True)
        raise AccessFailed(named, UNBOUND, "bind", failure)
    if outcome[0] == "unknown_run":
        log_failure(engine, probe, "bind", "unknown_run", run_known=False, code_role=True)
        raise AccessFailed(named, UNBOUND, "bind", "unknown_run")
    result, code, ctx = outcome
    if result == "denied":
        raise AccessDenied(ctx.role, ctx.stage, "bind", code, DENIALS[code])
    return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)


__all__ = ["bind", "bind_code", "bounded_source"]
