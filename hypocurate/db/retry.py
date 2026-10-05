"""Retry a whole transaction on deadlock or serialization failure (step 3, open item 3).

Every write path from step 4 on runs inside `run_transaction`. The function `fn`
receives a connection inside a fresh transaction and does all its work there: its
first statement takes the locks the protocol asks for (`hc_write_lock` for runs and
hypothesis versions; the source row for source registration). If PostgreSQL aborts
the transaction with SQLSTATE 40P01 (deadlock) or 40001 (serialization failure),
everything it wrote is rolled back, so `fn` is simply run again from the start.
Any other error is raised unchanged.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from sqlalchemy import Connection, Engine
from sqlalchemy.exc import DBAPIError

T = TypeVar("T")

RETRYABLE_SQLSTATES = frozenset({"40P01", "40001"})


def sqlstate(error: BaseException) -> str | None:
    """The SQLSTATE of a database error, or None."""
    orig = getattr(error, "orig", None)
    return getattr(orig, "sqlstate", None)


def run_transaction(engine: Engine, fn: Callable[[Connection], T], attempts: int = 5,
                    backoff: float = 0.05) -> T:
    """Runs `fn(conn)` in one transaction and commits; retries the whole transaction
    on 40P01 / 40001, at most `attempts` times in all."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            with engine.begin() as conn:
                return fn(conn)
        except DBAPIError as error:
            if sqlstate(error) not in RETRYABLE_SQLSTATES or attempt == attempts:
                raise
            time.sleep(backoff * attempt)
    raise AssertionError("unreachable")
