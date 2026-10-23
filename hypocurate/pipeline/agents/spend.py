"""Reserving and recording model calls; the spending caps (step 8a; register 'spending_caps').

**Before every request** (`reserve`): one transaction checks the caps and records the call as
started with its maximum cost; it is finished before the request is sent, so no model call ever
happens inside a database transaction. A run call takes the run's lock first (the locking protocol);
every reservation then takes one month-wide advisory lock, and only then reads any total, so two
reservations can never both pass the same cap or ceiling (the run's, the curation's or the month's)
on a stale total. (Before the step 8a review fix a registration call read its total before the lock.) The caps count every recorded call at its reported cost, or at its maximum cost
while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
- a run: at most `RUN_CAP_USD` over all its calls;
- a registration invocation (the Curator): at most `CURATION_CAP_USD` over its calls;
- a document invocation (the Extractor, Sprint 2 pilot): at most `DOCUMENT_CAP_USD` over its calls;
- the calendar month (UTC, by the database's start time): at most `MONTH_CAP_USD` over every call
  recorded in this database;
- optionally a lower ceiling the caller names (the live curation call: $0.50, owner 2026-10-06),
  over the same run or invocation; for a run, also the ceiling stored on the run at dispatch (step 9a, R5:
  it holds after a crash or a restart), the lower of the two.
A refusal sends nothing, is logged in `audit_log` (function 'model_call', result 'rejected', a fixed code,
the invocation) and raises `SpendingRefused`. Step 9b fix round 1 (finding 1): the audit row is written in the
same transaction that decides the refusal, so a refusal is reported only once its record is committed (if the
commit fails, the caller sees a failure to save the call instead); recovery reads that record to keep a refusal a
stop even when the agent's stage could not be saved.

**After the request** (`finish`): one transaction (a run call takes the run's lock first) finishes
the call exactly once, with the reported usage and its cost, or as failed with no usage (counted at
its maximum cost) and a fixed code. Never any provider text.

Limitation, stated plainly: the monthly cap counts the calls recorded in this database only; calls
made from another database (a local or test database) are not counted toward the live site's month.
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.agents.prices import PRICE_TABLE_VERSION

LOG = logging.getLogger("hypocurate.pipeline")
RUN_CAP_USD = Decimal("2")         # CLAUDE.md rule 12; register 'spending_caps'
MONTH_CAP_USD = Decimal("50")      # CLAUDE.md rule 12; register 'spending_caps'
CURATION_CAP_USD = Decimal("2")    # step 8a (owner, 2026-10-06): one curation, like one run
DOCUMENT_CAP_USD = Decimal("2")    # Sprint 2 pilot (owner, 2026-10-22): one Extractor invocation on one document
MONTH_LOCK_KEY = 0x68636D6F6E7468  # pg_advisory_xact_lock key of the monthly cap ("hcmonth")
CODES = {
    "spending_cap_run": "the run's model calls would exceed the per-run cap",
    "spending_cap_curation": "the curation's model calls would exceed the per-curation cap",
    "spending_cap_document": "the document invocation's model calls would exceed the per-document cap",
    "spending_cap_month": "the month's model calls would exceed the monthly cap",
    "ceiling_reached": "the calls would exceed the ceiling set for this call",
    "invocation_unknown": "no such invocation",
}
FINISH_CODES = ("model_auth", "provider_rejected", "provider_unavailable", "cost_unknown")


class ClaimLost(Exception):
    """Step 9b fix round 1 (finding 3): a worker's child no longer holds the run; nothing is reserved or sent, and
    (fix round 2) a call it reserved is not finished by it."""


class SpendingRefused(Exception):
    """No request was sent; the refusal is logged."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"model call refused: {CODES[code]}")


_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, 'model_call', false, :d)").bindparams(bindparam("d", type_=JSONB))
_MONTH_TOTAL = ("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                "WHERE date_trunc('month', started_at AT TIME ZONE 'UTC') = date_trunc('month', now() AT TIME ZONE 'UTC')")


def month_total(conn: Connection) -> Decimal:
    """This calendar month's counted spend (UTC), as the monthly cap counts it (step 9a: dispatch reads it)."""
    return conn.execute(text(_MONTH_TOTAL)).scalar_one()


def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, ceiling: Decimal | None = None) -> int:
    """The new call's id, recorded as started; or SpendingRefused (logged)."""
    if not isinstance(max_cost, Decimal) or not max_cost > 0:
        raise ValueError("max_cost must be a positive Decimal")

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(ACCESS_LOCK_TIMEOUT_MS)}"))
        inv = conn.execute(text("SELECT scope, run_id, stage_result_id, role FROM agent_invocation WHERE id = :i"),
                           dict(i=invocation_id)).one_or_none()
        if inv is None:
            conn.execute(_AUDIT, _refusal_row(invocation_id, None, None, "invocation_unknown", max_cost, ceiling, None))
            return ("refused", "invocation_unknown", None, None, None)
        # Every lock before any total is read (step 8a review, finding 3): the run's lock first (the
        # locking protocol), then the month-wide lock; read in the same order everywhere.
        if inv.scope == "run":
            status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=inv.run_id)).scalar_one()
            from hypocurate.pipeline.writes import owner_holds
            if not owner_holds(conn, inv.run_id):  # step 9b fix round 1, finding 3: before any request
                raise ClaimLost("the run's claim was closed or its work lock is gone")
            stage = actual_stage(conn, inv.run_id, status)
        else:
            stage = "document" if inv.scope == "document" else "registration"
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
        limit = ceiling
        if inv.scope == "run":
            spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                      "WHERE run_id = :r"), dict(r=inv.run_id)).scalar_one()
            cap, cap_code = RUN_CAP_USD, "spending_cap_run"
            stored = conn.execute(text("SELECT spending_ceiling FROM run WHERE id = :r"), dict(r=inv.run_id)).scalar_one()
            limit = min(x for x in (ceiling, stored) if x is not None) if (ceiling, stored) != (None, None) else None
        else:
            spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                      "WHERE invocation_id = :i"), dict(i=invocation_id)).scalar_one()
            cap, cap_code = ((DOCUMENT_CAP_USD, "spending_cap_document") if inv.scope == "document"
                             else (CURATION_CAP_USD, "spending_cap_curation"))
        month = conn.execute(text(_MONTH_TOTAL)).scalar_one()
        code = (cap_code if spent + max_cost > cap else
                "ceiling_reached" if limit is not None and spent + max_cost > limit else
                "spending_cap_month" if month + max_cost > MONTH_CAP_USD else None)
        if code:
            totals = {"spent": str(spent), "month": str(month)}
            conn.execute(_AUDIT, _refusal_row(invocation_id, inv, stage, code, max_cost, ceiling, totals))
            return ("refused", code, inv, stage, totals)
        call = conn.execute(text(
            "INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
            "VALUES (:r, :s, :i, :o, :m, :p, :c) RETURNING id"),
            dict(r=inv.run_id, s=inv.stage_result_id, i=invocation_id, o=inv.role, m=model, p=PRICE_TABLE_VERSION,
                 c=max_cost)).scalar_one()
        return ("reserved", call, None, None, None)

    outcome = run_transaction(engine, transaction)
    if outcome[0] == "reserved":
        return outcome[1]
    raise SpendingRefused(outcome[1])


def _refusal_row(invocation_id, inv, stage, code, max_cost, ceiling, totals) -> dict:
    detail = {"result": "rejected", "code": code, "invocation": int(invocation_id), "max_cost": str(max_cost)}
    if ceiling is not None:
        detail["ceiling"] = str(ceiling)
    detail.update(totals or {})
    return dict(r=inv.run_id if inv else None, role=inv.role if inv else "invalid", stage=stage or "none", d=detail)


def finish(engine: Engine, call_id: int, status: str, *, input_tokens: int | None = None,
           output_tokens: int | None = None, cached_tokens: int | None = None, cost: Decimal | None = None,
           code: str | None = None) -> None:
    """Finishes the call once: 'succeeded' with its usage and cost, or 'failed' / 'interrupted' with
    no usage and a fixed code."""
    if status == "succeeded":
        if None in (input_tokens, output_tokens, cached_tokens, cost):
            raise ValueError("a succeeded call has its usage and cost")
    elif status in ("failed", "interrupted"):
        if code not in FINISH_CODES and status == "failed":
            raise ValueError(f"unknown code {code!r}")
    else:
        raise ValueError(status)

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(ACCESS_LOCK_TIMEOUT_MS)}"))
        run_id = conn.execute(text("SELECT run_id FROM model_call WHERE id = :c"), dict(c=call_id)).scalar_one()
        if run_id is not None:
            conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
            # Step 9b fix round 2 (owner, 2026-10-09): a stale child cannot finish its call; the call stays started,
            # and recovery closes it at its maximum.
            from hypocurate.pipeline.writes import owner_holds
            if not owner_holds(conn, run_id):
                raise ClaimLost("the run's claim was closed or its work lock is gone")
        conn.execute(text("UPDATE model_call SET status = :st, input_tokens = :i, output_tokens = :o, "
                          "cached_tokens = :c, cost = :cost, error = :e, finished_at = now() WHERE id = :id"),
                     dict(st=status, i=input_tokens, o=output_tokens, c=cached_tokens, cost=cost, e=code, id=call_id))

    run_transaction(engine, transaction)
