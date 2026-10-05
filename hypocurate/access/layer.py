"""The access object: what one agent call may read from one run (PRD 4).

Created only by the trusted dispatcher (`dispatch.bind`), around an immutable
`AccessContext` captured once. There is no public constructor that takes a caller-chosen
run, role, stage or source (tests use their own helper). Every read goes through `get`
(one field) or `read_all` (every field on the role's list, used by `inputs.role_input`).

**One read is one transaction** (`run_transaction`, retried on 40P01 / 40001):
1. `SET LOCAL lock_timeout`; check that the run exists; `hc_write_lock(p_run => …)`: the
   locking protocol of step 3 (the audit rows are writes to the run). Holding the run's lock,
   the stage cannot change until commit, and neither can run data written by code that follows
   the same protocol (it waits). So `read_all` is one snapshot of the run data protected by the
   run-lock protocol; data outside that protocol is not covered by this claim;
2. the run's actual stage (`stage.actual_stage`);
3. the policy checks per field: known role and stage, the context's stage equals the actual
   one, the field is on the role's list;
4. the reads (`fields.READERS`); a reader may refuse (a policy denial with its code);
5. the audit rows: one per field, `allowed` true for a delivered read, false for a denial;
6. commit, and only then return or raise `AccessDenied`. A refusal therefore survives any
   rollback by the caller.

**Denial and failure are logged apart.** `detail.result` is "allowed", "denied" (a policy
refusal; `AccessDenied`) or "failed" (an access failure; `AccessFailed`): an unknown run, a
lock timeout, a reader's error, the database unavailable, a file-guard refusal
(`guarded.run_guarded`). `detail.code` is a fixed code. Only validated, bounded strings are
logged: a role, stage or field that is not one of ours is logged as "invalid" with its
length; a run id must be an integer.

**Failure rows are a named exception to the locking protocol** (owner, 2026-10-05; register
entry 'audit_failure_rows_without_run_lock'): they are written in their own short
transaction *without* `hc_write_lock`, because there is no run to lock (unknown run) or the
lock is what failed (timeout). An `audit_log` insert takes only a key-share lock on the run,
which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an
unknown run, `run_id` is NULL and the requested id is in `detail`.

**The original error of a failure** (a reader's exception, the database's error) is written,
with its traceback, to the process log only. The `AccessFailed` raised to the caller is raised
outside the handler: no cause, no context, and no text of the original, so a formatter that
forwards it cannot forward the original (re-check, finding 5).

**Fallback.** If a failure row cannot be written (the database is unavailable), the event
goes to the process log (logger `hypocurate.access`, one bounded JSON line). Durable logging
in the database is therefore not unconditional.

**Never call the access layer while holding the same run's lock**: the call would wait for
it, and fails after the lock timeout (logged as a failure).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError

from hypocurate.access.allowlist import ALL_ROLES, FIELDS, STAGES, allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.fields import READERS, Refused
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import RETRYABLE_SQLSTATES, run_transaction, sqlstate

# How long an access call waits for a run's lock before failing (milliseconds).
ACCESS_LOCK_TIMEOUT_MS = 5000

LOG = logging.getLogger("hypocurate.access")

# Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
DENIALS = {
    "unknown_role": "the role is not one of the five agent roles or the two code roles",
    "not_a_code_role": "only the code roles Inclusion and Checks are bound without an agent setting",
    "unknown_stage": "the stage is not one of the access stages",
    "stage_mismatch": "the run is no longer at the stage this access was bound to",
    "not_on_list": "the field is not on the role's list at the run's stage",
    "no_source": "the Curator reads one named source; none was bound",
    "source_not_recorded": "the source is not recorded for this run",
    "source_not_for_role": "only the Curator is bound to a source",
    "setting_not_recorded": "the agent setting is not recorded for this run",
    "empty_list": "the role has no field at this stage",
}
FAILURES = ("unknown_run", "lock_timeout", "reader_error", "database_error", "file_guard")
FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
_SOURCE_KEY = re.compile(r"[a-z][a-z0-9_]{0,40}")

_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :field, :allowed, :detail)").bindparams(bindparam("detail", type_=JSONB))
_TRUSTED = object()  # held by dispatch.bind (and the tests' helper); not a public constructor


def bounded(value: Any, valid: Iterable[str]) -> str:
    """`value` if it is one of ours, else "invalid"."""
    return value if isinstance(value, str) and value in valid else "invalid"


def bounded_source(value: Any) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) and _SOURCE_KEY.fullmatch(value) else "invalid"


def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | None = None, **extra) -> dict:
    d: dict[str, Any] = {"result": result}
    if code is not None:
        d["code"] = code
    if actual is not None:
        d["actual_stage"] = actual
    if ctx.source_key is not None:
        d["source"] = bounded_source(ctx.source_key)
    for name, raw, valid in (("role", ctx.role, ALL_ROLES), ("stage", ctx.stage, STAGES)):
        if bounded(raw, valid) == "invalid" and raw != "invalid":
            d[f"given_{name}_length"] = len(raw) if isinstance(raw, str) else -1
    d.update(extra)
    return d


def _row(ctx: AccessContext, run_id: int | None, function: str, allowed_: bool, detail: dict) -> dict:
    return dict(r=run_id, role=bounded(ctx.role, ALL_ROLES), stage=bounded(ctx.stage, STAGES),
                field=bounded(function, FUNCTIONS), allowed=allowed_, detail=detail)


def log_failure(engine: Engine, ctx: AccessContext, function: str, code: str, run_known: bool = True,
                **extra) -> None:
    """One failure row, in its own transaction, without the run lock (the named exception);
    the process log if the database cannot take it."""
    run_id = ctx.run_id if run_known else None
    detail = _detail(ctx, "failed", code, **extra)
    if not run_known:
        detail["requested_run"] = int(ctx.run_id)
    try:
        run_transaction(engine, lambda conn: conn.execute(_AUDIT, _row(ctx, run_id, function, False, detail)))
    except Exception as error:  # the database is unavailable: the process log is the fallback
        LOG.error(json.dumps({"audit_fallback": _row(ctx, run_id, function, False, detail),
                              "error": type(error).__name__}, sort_keys=True))


def keep_in_process_log(ctx: AccessContext, function: str, code: str, original: BaseException | None) -> None:
    """The original error of an access failure, with its traceback, in the process log only.
    It may hold values a role must not see, so it never travels with the error raised."""
    LOG.error(json.dumps({"access_failure": {"run": ctx.run_id, "role": bounded(ctx.role, ALL_ROLES),
                                             "function": bounded(function, FUNCTIONS), "code": code}},
                         sort_keys=True),
              exc_info=(type(original), original, original.__traceback__) if original is not None else None)


class _ReaderError(Exception):
    def __init__(self, field: str, error: BaseException):
        self.field, self.error_class = field, type(error).__name__
        super().__init__(field)


class Access:
    """What one role may read from one run at one stage. Immutable; see the module docstring."""

    __slots__ = ("_engine", "_context", "_lock_timeout_ms")

    def __init__(self, engine: Engine, context: AccessContext, *, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS,
                 _trusted: object = None):
        if _trusted is not _TRUSTED:
            raise TypeError("an access object is created only by hypocurate.access.dispatch.bind")
        if not isinstance(context, AccessContext) or not isinstance(context.run_id, int):
            raise TypeError("an access object needs an AccessContext with an integer run id")
        object.__setattr__(self, "_engine", engine)
        object.__setattr__(self, "_context", context)
        object.__setattr__(self, "_lock_timeout_ms", int(lock_timeout_ms))

    def __setattr__(self, name, value):
        raise AttributeError("an access object is immutable")

    @property
    def context(self) -> AccessContext:
        return self._context

    def __repr__(self) -> str:
        c = self._context
        return f"Access(run={c.run_id}, role={bounded(c.role, ALL_ROLES)!r}, stage={bounded(c.stage, STAGES)!r})"

    def get(self, field: str) -> Any:
        """One field, or AccessDenied / AccessFailed (already logged)."""
        return self._read(field, (field,))[field]

    def read_all(self) -> dict[str, Any]:
        """Every field on the role's list at its stage, in one transaction (one snapshot of the
        run data protected by the run-lock protocol).
        Never empty: a role with no field at its stage gets AccessDenied (logged)."""
        ctx = self._context
        return self._read("role_input", tuple(sorted(allowed(ctx.role, ctx.stage))))

    def _read(self, function: str, fields: tuple) -> dict[str, Any]:
        ctx, engine = self._context, self._engine
        name = bounded(function if fields != (function,) else fields[0], FUNCTIONS)
        failure = None
        try:
            outcome = run_transaction(engine, lambda conn: self._transaction(conn, ctx, function, fields))
        except _ReaderError as error:
            keep_in_process_log(ctx, error.field, "reader_error", error.__cause__)
            failure = (bounded(error.field, FUNCTIONS), "reader_error", {"error_class": error.error_class})
        except DBAPIError as error:
            code = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
            keep_in_process_log(ctx, name, code, error)
            failure = (name, code, {})
        if failure is not None:
            # Raised outside the handler: the error carries no cause, no context and no text of
            # the original, which stays in the process log only (re-check, finding 5).
            field, code, extra = failure
            log_failure(engine, ctx, field, code, **extra)
            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), field, code)
        kind = outcome[0]
        if kind == "unknown_run":
            log_failure(engine, ctx, name, "unknown_run", run_known=False)
            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), name, "unknown_run")
        if kind == "denied":
            field, code = outcome[1]
            raise AccessDenied(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), bounded(field, FUNCTIONS),
                               code, DENIALS[code])
        return outcome[1]

    def _transaction(self, conn: Connection, ctx: AccessContext, function: str, fields: tuple) -> tuple:
        conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=ctx.run_id)).scalar_one():
            return ("unknown_run",)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=ctx.run_id)).scalar_one()
        actual = actual_stage(conn, ctx.run_id, status)
        if not fields:  # role_input with nothing on the list: never an empty input
            code = ("unknown_role" if ctx.role not in ALL_ROLES else "unknown_stage" if ctx.stage not in STAGES
                    else "empty_list")
            conn.execute(_AUDIT, _row(ctx, ctx.run_id, "role_input", False, _detail(ctx, "denied", code, actual)))
            return ("denied", ("role_input", code))
        values, denied = {}, []
        for field in fields:
            code = _policy(ctx, field, actual)
            if code is None:
                try:
                    values[field] = READERS[field](conn, ctx)
                except Refused as refused:
                    code = refused.code
                except DBAPIError as error:
                    if sqlstate(error) in RETRYABLE_SQLSTATES:
                        raise
                    raise _ReaderError(field, error) from error
                except Exception as error:
                    raise _ReaderError(field, error) from error
            if code is not None:
                denied.append((field, code))
        if denied:  # nothing is delivered; each refused field is logged
            for field, code in denied:
                conn.execute(_AUDIT, _row(ctx, ctx.run_id, field, False, _detail(ctx, "denied", code, actual)))
            return ("denied", denied[0])
        for field in fields:
            conn.execute(_AUDIT, _row(ctx, ctx.run_id, field, True, _detail(ctx, "allowed", None, actual)))
        return ("allowed", values)


def _policy(ctx: AccessContext, field: str, actual: str) -> str | None:
    if ctx.role not in ALL_ROLES:
        return "unknown_role"
    if ctx.stage not in STAGES:
        return "unknown_stage"
    if ctx.stage != actual:
        return "stage_mismatch"
    if field not in allowed(ctx.role, actual) or field not in READERS:
        return "not_on_list"
    return None
