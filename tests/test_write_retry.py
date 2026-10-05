"""Step 4: `run_transaction` retries the whole transaction on deadlock (40P01) or
serialization failure (40001), and on nothing else (step 3, open item 3)."""
import threading

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from hypocurate.db.retry import run_transaction, sqlstate


class _Orig(Exception):
    def __init__(self, state):
        super().__init__(state)
        self.sqlstate = state


def failure(state):
    return OperationalError("SELECT 1", {}, _Orig(state))


def add_source(conn, key):
    conn.execute(text(
        "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
        "VALUES (:k, :k, 'uploaded_table', 'test', 'measured', 'available', true, 'paper')"), dict(k=key))


@pytest.mark.parametrize("state", ["40P01", "40001"])
def test_a_retryable_failure_reruns_the_whole_transaction(db, state):
    calls = []

    def fn(conn):
        calls.append(1)
        add_source(conn, "retry")  # would violate the unique key if the first attempt had stayed
        if len(calls) == 1:
            raise failure(state)
        return "done"

    assert run_transaction(db, fn, backoff=0) == "done"
    assert len(calls) == 2
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM source WHERE key = 'retry'")).scalar() == 1


def test_other_errors_are_not_retried(db):
    calls = []

    def fn(conn):
        calls.append(1)
        add_source(conn, "dup")
        add_source(conn, "dup")

    with pytest.raises(IntegrityError) as error:
        run_transaction(db, fn, backoff=0)
    assert sqlstate(error.value) == "23505" and len(calls) == 1
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM source")).scalar() == 0


def test_it_gives_up_after_the_last_attempt(db):
    calls = []

    def fn(conn):
        calls.append(1)
        raise failure("40P01")

    with pytest.raises(OperationalError):
        run_transaction(db, fn, attempts=3, backoff=0)
    assert len(calls) == 3


def test_a_real_deadlock_is_retried_to_completion(db):
    """Two transactions lock two source rows in opposite orders. PostgreSQL aborts one
    with 40P01; run_transaction runs it again, and both complete."""
    with db.begin() as conn:
        add_source(conn, "a")
        add_source(conn, "b")
    barrier = threading.Barrier(2)
    attempts = {"ab": 0, "ba": 0}
    results, errors = [], []

    def worker(first, second, name):
        def fn(conn):
            attempts[name] += 1
            conn.execute(text("SELECT 1 FROM source WHERE key = :k FOR UPDATE"), dict(k=first))
            if attempts[name] == 1:
                barrier.wait(10)
            conn.execute(text("SELECT 1 FROM source WHERE key = :k FOR UPDATE"), dict(k=second))
            return name
        try:
            results.append(run_transaction(db, fn, backoff=0.01))
        except Exception as error:  # reported below
            errors.append(error)

    threads = [threading.Thread(target=worker, args=("a", "b", "ab")),
               threading.Thread(target=worker, args=("b", "a", "ba"))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert errors == []
    assert sorted(results) == ["ab", "ba"]
    assert sorted(attempts.values()) == [1, 2]
