"""The trusted dispatcher: the only way to obtain an access object (step 5 review, finding 2).

`bind(engine, run_id, agent_setting_id, source_key=None)` is called by trusted orchestration
code (steps 8 and 9) for one agent call. It never takes a role, a stage or a run chosen by
anything a model controls:
- the **role** is read from the run's recorded agent settings (`run_agent_setting`): the
  setting being invoked must be recorded for this run, and its role is the one recorded;
- the **stage** is read from the database;
- no run role is bound to a source (step 8a, owner 2026-10-06: the Curator reads a source version
  at registration, never in a run; `source_not_for_role`).
The result is an `Access` around an immutable `AccessContext`. The binding itself is
logged (function "bind"): allowed, denied with its code, or failed. Every later read checks
again that the run is still at the bound stage.

Nothing a model controls ever receives SQL, a database connection or a file path (CLAUDE.md):
agents get text built from `role_input` and from reads through this object only.

`bind_invocation(engine, invocation_id)` (step 8a) binds one agent call from its invocation record
alone (step 5 re-check: run, setting and source come from one record, never assembled
separately): a run invocation binds as `bind` does, for its run and setting; a registration
invocation binds the Curator to the one sealed source version it names, with no run (stage
'registration'). Every bind is logged; an unknown invocation is a logged failure.

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
                                     bounded_source, document_stage, keep_in_process_log, log_failure,
                                     registration_stage)
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction, sqlstate

UNBOUND = "invalid"  # the role logged for a binding refused before a role is known


def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | None = None,
         lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS, _invocation_id: int | None = None) -> Access:
    """An access object for one agent call, or AccessDenied / AccessFailed (logged)."""
    if not isinstance(run_id, int) or isinstance(run_id, bool) or not isinstance(agent_setting_id, int):
        raise TypeError("bind takes an integer run id and an integer agent setting id")
    probe = AccessContext(run_id, UNBOUND, UNBOUND, source_key, agent_setting_id, invocation_id=_invocation_id)

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=run_id)).scalar_one():
            return ("unknown_run", None)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        stage = actual_stage(conn, run_id, status)
        role = conn.execute(text("SELECT role FROM run_agent_setting WHERE run_id = :r AND agent_setting_id = :a"),
                            dict(r=run_id, a=agent_setting_id)).scalar_one_or_none()
        ctx = AccessContext(run_id, role or UNBOUND, stage, source_key, agent_setting_id, invocation_id=_invocation_id)
        code = None
        if role is None:
            code = "setting_not_recorded"
        elif source_key is not None:
            code = "source_not_for_role"
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


def bind_invocation(engine: Engine, invocation_id: int, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
    """An access object for the agent call recorded by `invocation_id`, or AccessDenied / AccessFailed
    (logged). Run, role, setting and source all come from that one record."""
    if not isinstance(invocation_id, int) or isinstance(invocation_id, bool):
        raise TypeError("bind_invocation takes an integer invocation id")
    try:
        row = run_transaction(engine, lambda conn: conn.execute(text(
            "SELECT i.scope, i.run_id, i.role, i.agent_setting_id, i.source_version_id, s.key AS source_key, "
            "di.document_parse_id FROM agent_invocation i LEFT JOIN source_version sv ON sv.id = i.source_version_id "
            "LEFT JOIN source s ON s.id = sv.source_id LEFT JOIN document_invocation di ON di.invocation_id = i.id "
            "WHERE i.id = :i"), dict(i=invocation_id)).one_or_none())
    except DBAPIError as error:
        probe = AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id)
        keep_in_process_log(probe, "bind", "database_error", error)
        failure = True
    else:
        failure = False
    if failure:
        log_failure(engine, AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id), "bind", "database_error")
        raise AccessFailed(UNBOUND, UNBOUND, "bind", "database_error")
    if row is None:
        log_failure(engine, AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id), "bind",
                    "unknown_invocation", run_known=False)
        raise AccessFailed(UNBOUND, UNBOUND, "bind", "unknown_invocation")
    if row.scope == "run":
        return bind(engine, row.run_id, row.agent_setting_id, lock_timeout_ms=lock_timeout_ms,
                    _invocation_id=invocation_id)
    if row.scope == "document":  # Sprint 2 pilot: the Extractor on one parsed document, no run
        ctx = AccessContext(None, row.role, "document", None, row.agent_setting_id, invocation_id=invocation_id,
                            document_parse_id=row.document_parse_id)
    else:
        ctx = AccessContext(None, row.role, "registration", row.source_key, row.agent_setting_id,
                            source_version_id=row.source_version_id, invocation_id=invocation_id)

    def transaction(conn: Connection):
        stage = document_stage(conn, ctx) if row.scope == "document" else registration_stage(conn, ctx)
        code = None if stage == ctx.stage else "stage_mismatch"
        conn.execute(_AUDIT, _row(ctx, None, "bind", code is None,
                                  _detail(ctx, "denied" if code else "allowed", code, stage,
                                          agent_setting=row.agent_setting_id)))
        return code

    code = run_transaction(engine, transaction)
    if code is not None:
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


__all__ = ["bind", "bind_code", "bind_invocation", "bounded_source"]
