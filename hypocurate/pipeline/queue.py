"""The queue: claims, the heartbeat and the worker's hold on a run (build step 9b; docs/reviews/step09b_plan.md,
"Claims, heartbeat, and dead"; register 'queue_and_claims').

**A claim** (`claim_next`, or `claim` for one run):
1. on its own lease connection (autocommit, so no transaction stays open), the worker takes, without waiting, a session
   advisory lock (CLAIM, run), then checks that (WORK, run) is free (the guarded child holds WORK for its whole work;
   an orphan child still holding it keeps every worker off the run);
2. in one locked transaction (the locking protocol: `hc_write_lock(p_run)` first) it re-checks the run, closes a stale
   open claim as `lost`, records its claim (migration 0008: one open claim per run) and starts the run: queued ->
   running, or a confirmed waiting run -> running.
Every worker takes CLAIM before anything else, so two workers can never both hold a run; a cancel and a start are
serialised by the run's lock.

**Claimable:** a queued run with no open claim; a waiting run a person has confirmed, with no open claim; a running
run with no open claim (released for recovery, or never claimed) or whose open claim's heartbeat is older than
`STALE_SECONDS` (its worker is taken to be dead), always subject to the two locks being free. Running runs come
first (they are taken up again), then confirmed waiting runs, then queued runs in the order of dispatch.

**The heartbeat** (`Heartbeat`, owner R6) is a thread of the worker that writes `run_claim.heartbeat_at` every
`HEARTBEAT_SECONDS`, on the claim row, never the run row, so it never waits behind the run's lock (a named exception
to the locking protocol, like audit rows). A release (`release`) follows the protocol.

This module is imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.db.retry import run_transaction

LOG = logging.getLogger("hypocurate.worker")

# How a claim ends (migration 0008 holds the same list).
RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
# The owner's approved values (step 9 plan; register 'queue_and_claims', 'stuck_child_limits').
HEARTBEAT_SECONDS = 15
STALE_SECONDS = 120        # 8 missed beats: the claim's worker is taken to be dead
STALL_SECONDS = 900        # A4: no write by the run for this long: the child is stuck
RUN_TIMEOUT_SECONDS = 1800  # A4: the whole run, as a backstop
SWEEP_SECONDS = 60         # the worker looks for work this often when idle (and on start)
LOCK_TIMEOUT_MS = 5000
# Session advisory locks, one per run (the run id in the low 32 bits). Their high words ("HCLA", "HCWR") keep them
# apart from the single-key locks used elsewhere (spend.MONTH_LOCK_KEY, confirmation.SOURCES_LOCK_KEY, migrate's).
_CLAIM_NS, _WORK_NS = 0x48434C41, 0x48435752


def _key(ns: int, run_id: int) -> int:
    if not 0 < int(run_id) < 2 ** 32:
        raise ValueError("a run id for an advisory lock is below 2**32")
    return (ns << 32) | int(run_id)


def claim_key(run_id: int) -> int:
    return _key(_CLAIM_NS, run_id)


def work_key(run_id: int) -> int:
    return _key(_WORK_NS, run_id)


class Lease:
    """The worker's lease connection for one claim: autocommit, holding the session lock (CLAIM, run)."""

    def __init__(self, engine: Engine, run_id: int):
        self.run_id = run_id
        self._conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
        self._conn.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-lease-{run_id}"))

    def try_take(self) -> bool:
        """CLAIM taken, and WORK free (taken and let go at once); False, holding nothing, otherwise."""
        if not self._conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=claim_key(self.run_id))).scalar():
            return False
        if not self._conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=work_key(self.run_id))).scalar():
            self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=claim_key(self.run_id)))
            return False
        self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=work_key(self.run_id)))
        return True

    def close(self) -> None:
        """Lets go of the lock (by closing the session) and the connection."""
        try:
            self._conn.execute(text("SELECT pg_advisory_unlock_all(), set_config('application_name', '', false)"))
        except Exception:  # noqa: BLE001 (closing the session lets go of it anyway)
            pass
        self._conn.close()


@dataclass
class Claim:
    id: int
    run_id: int
    status_before: str  # 'queued', 'waiting' or 'running' (a running run is taken up again: recovery first)
    lease: Lease


_CANDIDATES = text("""
    SELECT r.id FROM run r
    LEFT JOIN run_claim c ON c.run_id = r.id AND c.released_at IS NULL
    WHERE (c.id IS NULL OR c.heartbeat_at < clock_timestamp() - make_interval(secs => :stale))
      AND (r.status IN ('queued', 'running')
           OR (r.status = 'waiting' AND EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id)))
      AND (CAST(:only AS bigint) IS NULL OR r.id = CAST(:only AS bigint))
    ORDER BY CASE r.status WHEN 'running' THEN 0 WHEN 'waiting' THEN 1 ELSE 2 END, r.queued_at, r.id
    LIMIT 100""")


def _take(engine: Engine, run_id: int, worker: str, stale_seconds: float) -> tuple[int, str] | None:
    """The claim's transaction: (claim id, status before) or None if the run is no longer claimable."""

    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        if status not in ("queued", "running", "waiting"):
            return None
        if status == "waiting" and not conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = :r)"), dict(r=run_id)).scalar():
            return None
        open_claim = conn.execute(text(
            "SELECT id, heartbeat_at < clock_timestamp() - make_interval(secs => :s) AS stale, heartbeat_at "
            "FROM run_claim WHERE run_id = :r AND released_at IS NULL"), dict(r=run_id, s=stale_seconds)).one_or_none()
        if open_claim is not None:
            if not open_claim.stale:
                return None
            conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = 'lost', found = :f "
                              "WHERE id = :c").bindparams(bindparam("f", type_=JSONB)),
                         dict(c=open_claim.id, f={"stale_heartbeat_at": open_claim.heartbeat_at.isoformat()}))
        cid = conn.execute(text("INSERT INTO run_claim (run_id, worker) VALUES (:r, :w) RETURNING id"),
                           dict(r=run_id, w=worker)).scalar_one()
        if status == "queued":
            conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=run_id))
        elif status == "waiting":  # confirmed: it goes on (the database requires the confirmation, 0007)
            conn.execute(text("UPDATE run SET status = 'running' WHERE id = :r"), dict(r=run_id))
        return cid, status

    return run_transaction(engine, body)


def claim_next(engine: Engine, worker: str, *, only: int | None = None,
               stale_seconds: float = STALE_SECONDS) -> Claim | None:
    """The next claimable run, claimed by `worker`; None if there is none (or `only` is not claimable)."""
    with engine.connect() as conn:
        candidates = [r for (r,) in conn.execute(_CANDIDATES, dict(stale=stale_seconds, only=only)).all()]
    for run_id in candidates:
        lease = Lease(engine, run_id)
        try:
            if not lease.try_take():
                lease.close()
                continue
            taken = _take(engine, run_id, worker, stale_seconds)
        except Exception:
            lease.close()
            raise
        if taken is None:
            lease.close()
            continue
        cid, before = taken
        LOG.info(json.dumps({"claimed": run_id, "claim": cid, "worker": worker, "status_before": before}))
        return Claim(cid, run_id, before, lease)
    return None


def claim(engine: Engine, run_id: int, worker: str) -> Claim | None:
    """A claim of exactly this run (the command line works its own run inline, R1); None if it is held or not open."""
    return claim_next(engine, worker, only=run_id)


def record_child(engine: Engine, c: Claim, pid: int) -> None:
    """The guarded child's pid on the claim (once; 0008)."""
    with engine.begin() as conn:
        conn.execute(text("UPDATE run_claim SET child_pid = :p WHERE id = :c AND released_at IS NULL"),
                     dict(p=pid, c=c.id))


def release(engine: Engine, c: Claim, reason: str, found: dict | None = None) -> None:
    """Ends the claim once, with its reason (and what recovery found), under the run's lock; then lets go of the lease.
    If the database cannot take the release, the lease is let go anyway: the open claim's heartbeat then goes stale
    and another worker takes the run over (`lost`)."""
    if reason not in RELEASE_REASONS:
        raise ValueError(reason)

    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=c.run_id))
        conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = :x, found = CAST(:f AS jsonb) "
                          "WHERE id = :c AND released_at IS NULL"),
                     dict(x=reason, f=json.dumps(found) if found is not None else None, c=c.id))

    try:
        run_transaction(engine, body)
        LOG.info(json.dumps({"released": c.run_id, "claim": c.id, "reason": reason}))
    finally:
        c.lease.close()


class Heartbeat(threading.Thread):
    """Writes the claim's heartbeat every `interval` seconds until stopped (R6: on the claim row only)."""

    def __init__(self, engine: Engine, claim_id: int, interval: float = HEARTBEAT_SECONDS):
        super().__init__(name=f"heartbeat-{claim_id}", daemon=True)
        self._engine, self._claim, self._interval = engine, claim_id, interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                with self._engine.begin() as conn:
                    conn.execute(text("UPDATE run_claim SET heartbeat_at = clock_timestamp() WHERE id = :c "
                                      "AND released_at IS NULL"), dict(c=self._claim))
            except Exception as error:  # noqa: BLE001 (the next beat tries again; a long gap makes the claim stale)
                LOG.error(json.dumps({"heartbeat_failed": self._claim, "error": type(error).__name__}))

    def stop(self) -> None:
        self._stop_event.set()
        self.join(30)


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
