"""The background worker (PRD Section 6; build step 9b; docs/reviews/step09b_plan.md).

`python -m hypocurate.worker [--once]` (also `hypocurate worker`): claims a run (`pipeline.queue`), keeps its claim's
heartbeat on a thread of its own, takes the run up again after recovery's bookkeeping if it was running
(`pipeline.recovery`), runs the orchestrator in a guarded child started from the main thread (it dies with the
worker, owner's addition A3), watches the child, and releases the claim with its reason:
- `finished` (the run completed or failed), `waiting` (it waits for a person), `stopped_for_recovery` (it stopped
  and stays running: recovery takes it up at the next claim);
- `child_stuck` (A4: the run wrote nothing for `STALL_SECONDS`, or ran for `RUN_TIMEOUT_SECONDS`: the child is killed),
  `child_failed` (the child gave no answer), `shutdown` (SIGTERM: the child is stopped).
Idle, it looks for work every `SWEEP_SECONDS` (and at once on start). `--once` claims one run, if there is one,
and returns. The worker never imports dspy, litellm or scipy (owner, Q2: memory); the child does.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import socket
import threading
import time
from typing import Any, Callable

from sqlalchemy import Engine, text

from hypocurate.access import guarded
from hypocurate.config import load_settings
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queue, recovery

log = logging.getLogger("hypocurate.worker")
CHILD_TARGET = "hypocurate.pipeline.orchestrator:work_guarded"
WATCH_SECONDS = 1.0  # how often the worker looks at its child (and its events)


def worker_name() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"[:200]


def _status(engine: Engine, run_id: int) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()


def _watch(child: guarded.GuardedChild, started: float, stop: threading.Event, lost: threading.Event,
           monitor: queue.Monitor, stall_seconds: float, run_timeout: float) -> str:
    """'ended', or why the child is to be stopped: 'shutdown', 'ownership_lost', 'run_timeout' or 'stalled'. Every
    check is on this thread's own clock or an event (fix round 1, finding 5): the database is read only by the
    monitor's thread, whose samples are time-limited and never waited for. The stall allowance counts from
    `monitor.progress_at`: this child's launch, or the last progress the monitor saw since (finding 6)."""
    while True:
        if child.wait_for(WATCH_SECONDS):
            return "ended"
        if stop.is_set():
            return "shutdown"
        if lost.is_set():
            return "ownership_lost"
        now = time.monotonic()
        if now - started > run_timeout:
            return "run_timeout"
        if now - monitor.progress_at > stall_seconds:
            return "stalled"


def _end_child(child: guarded.GuardedChild | None, why: str | None) -> None:
    """Stops and reaps the child (finding 2): SIGTERM at a shutdown (escalated to SIGKILL if not obeyed), else SIGKILL."""
    if child is not None and child.alive():
        child.stop(signal.SIGTERM if why == "shutdown" else signal.SIGKILL)
    if child is not None:
        child.discard()


def work(engine: Engine, claim: queue.Claim, *, phases=("run",), on_phase: Callable[[str, dict], None] | None = None,
         stop: threading.Event | None = None, stall_seconds: float = queue.STALL_SECONDS,
         run_timeout: float = queue.RUN_TIMEOUT_SECONDS, heartbeat_interval: float = queue.HEARTBEAT_SECONDS,
         client_options: dict | None = None) -> dict[str, Any]:
    """Works one claimed run (from the main thread) and releases its claim; returns the last phase's report, the
    release reason and, for a stopped child, why. Fix round 1 (finding 2): the claim is released only after the child
    has been stopped and reaped, on every exit path, and no child is started once shutdown was asked for."""
    stop = stop or threading.Event()
    lost = threading.Event()
    beat = queue.Heartbeat(engine, claim.id, interval=heartbeat_interval, lease=claim.lease, lost=lost)
    monitor = queue.Monitor(engine, claim.run_id, interval=min(5.0, max(0.5, stall_seconds / 4)))
    beat.start()
    monitor.start()
    started = time.monotonic()
    found: dict | None = None
    report: dict | None = None
    child: guarded.GuardedChild | None = None
    reason, why = "child_failed", "error"
    try:
        if claim.status_before == "running":
            found = recovery.recover(engine, claim.run_id) or None
        for i, phase in enumerate(phases):
            if found and found.get("failed"):  # recovery ended the run (attempts exhausted)
                break
            if stop.is_set():
                reason, why = "shutdown", "shutdown"
                return {"report": report, "release": reason, "why": why}
            if lost.is_set():
                reason, why = "lost", "ownership_lost"
                return {"report": report, "release": reason, "why": why}
            child = guarded.start_guarded(CHILD_TARGET, {"run_id": claim.run_id, "phase": phase, "claim_id": claim.id,
                                                         "client_options": client_options,
                                                         "recovered": claim.status_before == "running"},
                                          audit=(engine, claim.run_id))
            monitor.launched()
            if i == 0:
                queue.record_child(engine, claim, child.pid)
            watched = _watch(child, started, stop, lost, monitor, stall_seconds, run_timeout)
            if watched != "ended":
                _end_child(child, watched)
                child = None
                reason = {"shutdown": "shutdown", "ownership_lost": "lost"}.get(watched, "child_stuck")
                why = watched
                log.warning(json.dumps({"child_stopped": claim.run_id, "why": watched}))
                return {"report": report, "release": reason, "why": why}
            try:
                report = child.result(timeout=60)
            except guarded.GuardedRunError:
                child = None
                reason, why = "child_failed", "no_answer"
                return {"report": report, "release": reason, "why": why}
            child = None
            if report.get("busy"):  # another child holds the run's work lock, or the claim is not this child's
                reason, why = "child_failed", "busy"
                return {"report": report, "release": reason, "why": why}
            if on_phase:
                on_phase(phase, report)
            if phase == "prepare" and not report.get("ready"):
                break
        status = _status(engine, claim.run_id)
        reason = ("finished" if status in ("completed", "failed") else "waiting" if status == "waiting"
                  else "stopped_for_recovery")
        why = None
        if lost.is_set():
            reason, why = "lost", "ownership_lost"
        return {"report": report, "release": reason, "why": why}
    finally:
        _end_child(child, "error")  # never release with a live child (finding 2)
        beat.stop()
        monitor.stop()
        try:
            queue.release(engine, claim, reason, found)
        except Exception:  # noqa: BLE001 (the lease is let go anyway: the claim goes stale)
            log.error(json.dumps({"release_failed": claim.run_id}))


def run(once: bool = False, engine: Engine | None = None, max_cycles: int | None = None,
        wait: Callable[[float], Any] | None = None) -> int:
    """The worker loop. SIGTERM (a deploy) and SIGINT stop it after its child is stopped and its claim released.
    Each cycle it finishes any narrower question left by a stop (`recovery.finish_narrower_questions`) and claims the
    next run; idle, it logs whether the database answers (never its address) and looks again after `SWEEP_SECONDS`.
    `max_cycles` and `wait` are for tests."""
    engine = engine or make_engine(load_settings(web=False).database_url, worker_session=True)
    stop = threading.Event()
    wait = wait or stop.wait
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stop.set())
    name = worker_name()
    log.info(json.dumps({"worker_started": name, "once": once}))
    cycles = 0
    while not stop.is_set() and (max_cycles is None or cycles < max_cycles):
        cycles += 1
        try:
            recovery.finish_narrower_questions(engine)
            claim = queue.claim_next(engine, name)
        except Exception as error:  # noqa: BLE001 (the database is away: say so, try again later)
            log.error("worker idle: database NOT reachable (%s)", type(error).__name__)
            claim = None
        else:
            if claim is None:
                log.info("worker idle: nothing to claim; database reachable")
        if claim is None:
            if once:
                break
            wait(queue.SWEEP_SECONDS)
            continue
        work(engine, claim, stop=stop)
        if once:
            break
    log.info(json.dumps({"worker_stopped": name}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypocurate worker")
    parser.add_argument("--once", action="store_true", help="claim one run, if there is one, work it and stop")
    args = parser.parse_args(argv)
    return run(once=args.once)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    raise SystemExit(main())
