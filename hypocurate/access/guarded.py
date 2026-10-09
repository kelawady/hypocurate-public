"""Runs pipeline code in a fresh process under the file guard's tripwire (`file_guard`).

`run_guarded("hypocurate.module:function", payload, audit=(engine, run_id))` starts
`python -m hypocurate.access.guarded`, sends it the target and a JSON payload, and returns
the target's JSON result. The child:

1. receives a private scratch directory (mode 0700, created by the parent, which removes it
   when the child ends, however it ends) and points `TMPDIR`, `MPLCONFIGDIR` and
   `XDG_CACHE_HOME` at it, for libraries that need a cache or temporary files (the
   plotting library in step 7); its working directory is the scratch directory;
2. removes the repository root from its import path (the `hypocurate` package is already
   imported and keeps its own path) and every import-path entry that does not exist (owner,
   2026-10-06: otherwise each later import probes them, for example the standard library's zip,
   and the guard refuses those probes, which would fill the audit log with refusals that are not
   mistakes), and imports the modules in `PRELOADED`;
3. installs the guard;
4. imports the target, which must be inside the `hypocurate` package, calls it with the
   payload, writes the result to its standard output and exits.

The guard's refusals come back on the child's standard error; the parent copies each into
the audit log as a failure (code `file_guard`) for the run given in `audit`, or to the
process log if no run is given or the database cannot take it.

Step 9b (owner's addition A3, 2026-10-08): `start_guarded` starts the same child without waiting for it, for the
worker, which must keep its heartbeat going and watch the child while it works. It may be called only from the
main thread, and it passes the parent's pid: the child then sets PR_SET_PDEATHSIG(SIGKILL) first thing, so it
dies with the thread that started it (the main thread, which lives as long as the worker), and exits at once
(`PARENT_GONE_EXIT`) if its parent is not that process any more (the parent died before the signal was set).
`run_guarded` is unchanged.

This is a tripwire against *accidental* file access by trusted code, not a sandbox (see
`file_guard`). This is the only place that installs it. The pipeline's entry points (the
command line's run command, step 8; the worker's run of a claimed job, step 9) run each
pipeline run through `run_guarded`. The web service, the migrations, the `sources` commands
and the test process do not.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from typing import Any

from hypocurate.access import file_guard

MODULE = "hypocurate.access.guarded"
SCRATCH_ENV = ("TMPDIR", "MPLCONFIGDIR", "XDG_CACHE_HOME")
# Imported before the guard is installed: the database driver imports `ctypes`, which loads
# the process's own symbols when it is first imported, and the guard refuses the audit events
# of a ctypes load. Importing it first changes what the guard sees only for that import. After
# installation the guard refuses the ctypes audit events it intercepts (a new library load, a
# symbol lookup, a foreign call); it does not stop preloaded ctypes from reading process memory
# directly, which raises no such event (a documented limit; see file_guard).
# Step 8b (owner, 2026-10-07): scipy too, for the same reason: importing it makes a ctypes foreign call at
# load time (scipy/_lib/_ccallback_c.pyx), which the guard refuses; the run's statistics import scipy.stats.
# After installation every ctypes event is still refused. (statsmodels is test-only and never imported here.)
PRELOADED = ("psycopg", "scipy")


class GuardedRunError(Exception):
    """The guarded process failed; the message is its error."""


MAX_REPORTED = 100  # refusals copied into the audit log per run; the rest are counted
PARENT_GONE_EXIT = 3  # step 9b (A3): the child found that the process that started it is gone
STOP_GRACE_SECONDS = 10  # step 9b fix round 1 (finding 2): a SIGTERM not obeyed within this is escalated to SIGKILL
PR_SET_PDEATHSIG = 1  # linux/prctl.h


def _as_text(captured) -> str:
    """Captured output as text: TimeoutExpired may hold bytes even in text mode, or nothing."""
    if captured is None:
        return ""
    return captured.decode("utf-8", "replace") if isinstance(captured, bytes) else captured


def _report_refusals(stderr: str, audit) -> None:
    """Copies the guard's refusal lines into the audit log (or the process log)."""
    from hypocurate.access.context import AccessContext
    from hypocurate.access.layer import LOG, log_failure
    reports = []
    for line in stderr.splitlines():
        if line.startswith(file_guard.REPORT_PREFIX):
            try:
                r = json.loads(line[len(file_guard.REPORT_PREFIX):])
                reports.append({"event": str(r.get("event", ""))[:40], "what": str(r.get("what", ""))[:200]})
            except ValueError:
                reports.append({"event": "unreadable", "what": ""})
    for i, r in enumerate(reports[:MAX_REPORTED]):
        extra = dict(r, **({"more": len(reports) - MAX_REPORTED} if i == MAX_REPORTED - 1
                           and len(reports) > MAX_REPORTED else {}))
        if audit is None:
            LOG.warning(json.dumps({"file_guard": extra}, sort_keys=True))
        else:
            engine, run_id = audit
            log_failure(engine, AccessContext(int(run_id), "invalid", "invalid"), "guarded_run", "file_guard",
                        **extra)


def run_guarded(target: str, payload: Any = None, env: dict[str, str] | None = None,
                timeout: float | None = None, audit=None) -> Any:
    """Runs `target(payload)` in a guarded child process and returns its JSON result.
    `audit`: (engine, run_id), where the guard's refusals are logged as failures."""
    if not target.startswith("hypocurate.") or ":" not in target:
        raise ValueError(f"target {target!r} must be 'hypocurate.<module>:<function>'")
    # mode 0700, in the system temporary directory; removed here, whatever the child does
    scratch = tempfile.mkdtemp(prefix=file_guard.SCRATCH_PREFIX, dir=file_guard.SYSTEM_TEMP)
    try:
        try:
            completed = subprocess.run([sys.executable, "-m", MODULE],
                                       input=json.dumps({"target": target, "payload": payload, "scratch": scratch}),
                                       capture_output=True, text=True, timeout=timeout,
                                       env=env if env is not None else dict(os.environ))
        except subprocess.TimeoutExpired as expired:
            # The child is killed; what it wrote before (possibly as bytes) is still reported.
            _report_refusals(_as_text(expired.stderr), audit)
            raise
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    _report_refusals(completed.stderr, audit)
    return _answer(completed.stdout, completed.stderr, completed.returncode)


def _answer(stdout: str, stderr: str, returncode: int) -> Any:
    lines = stdout.strip().splitlines()
    try:
        answer = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise GuardedRunError(f"the guarded process gave no answer (exit {returncode}): {stderr.strip()[-2000:]}") from None
    if not answer.get("ok"):
        raise GuardedRunError(answer.get("error", "unknown error"))
    return answer["result"]


class GuardedChild:
    """A guarded child started by `start_guarded`: its pid, and its answer once it ends."""

    def __init__(self, proc: subprocess.Popen, scratch: str, audit):
        self.proc, self.pid, self._scratch, self._audit = proc, proc.pid, scratch, audit
        self._out = self._err = ""

    def wait_for(self, seconds: float) -> bool:
        """Waits up to `seconds` for the child to end (reading its output meanwhile); True once it has ended."""
        try:
            out, err = self.proc.communicate(timeout=seconds)
        except subprocess.TimeoutExpired:
            return False
        self._out, self._err = out or "", err or ""
        return True

    def alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self, sig: int = signal.SIGKILL) -> None:
        """Ends the child and reaps it: `sig` (SIGKILL by default); a SIGTERM not obeyed within `STOP_GRACE_SECONDS`
        is escalated to SIGKILL (fix round 1, finding 2). Returns only once the child has ended."""
        if self.proc.poll() is None:
            self.proc.send_signal(sig)
        if not self.wait_for(STOP_GRACE_SECONDS if sig != signal.SIGKILL else 30) and self.proc.poll() is None:
            self.proc.kill()
            self.wait_for(30)
        self.proc.wait()

    def result(self, timeout: float | None = None) -> Any:
        """The child's answer (GuardedRunError if it failed); its refusals reported; its scratch removed."""
        try:
            if not self.wait_for(timeout if timeout is not None else 10 ** 9):
                self.stop()
                raise subprocess.TimeoutExpired(self.proc.args, timeout)
        finally:
            _report_refusals(_as_text(self._err), self._audit)
            shutil.rmtree(self._scratch, ignore_errors=True)
        return _answer(self._out, self._err, self.proc.returncode)

    def discard(self) -> None:
        """For a child that was stopped: its refusals reported and its scratch removed; no answer is read."""
        _report_refusals(_as_text(self._err), self._audit)
        shutil.rmtree(self._scratch, ignore_errors=True)


def start_guarded(target: str, payload: Any = None, env: dict[str, str] | None = None, audit=None) -> GuardedChild:
    """Starts `target(payload)` in a guarded child that dies with this process's main thread (A3), and returns at
    once. Only from the main thread: the death signal follows the thread that started the child."""
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("a guarded child is started only from the main thread (it dies with the thread that "
                           "started it)")
    if not target.startswith("hypocurate.") or ":" not in target:
        raise ValueError(f"target {target!r} must be 'hypocurate.<module>:<function>'")
    scratch = tempfile.mkdtemp(prefix=file_guard.SCRATCH_PREFIX, dir=file_guard.SYSTEM_TEMP)
    try:
        proc = subprocess.Popen([sys.executable, "-m", MODULE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env if env is not None else dict(os.environ))
        proc.stdin.write(json.dumps({"target": target, "payload": payload, "scratch": scratch,
                                     "parent_pid": os.getpid()}))
        proc.stdin.close()
    except Exception:
        shutil.rmtree(scratch, ignore_errors=True)
        raise
    return GuardedChild(proc, scratch, audit)


def _die_with_parent(parent_pid: int) -> None:
    """A3: the kernel sends SIGKILL when the thread that started this process ends; then the fork race is closed by
    checking that the parent is still the process that started it."""
    import ctypes
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    if libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL, 0, 0, 0) != 0:
        os._exit(PARENT_GONE_EXIT)  # the death signal could not be set: never run unwatched
    if os.getppid() != parent_pid:
        os._exit(PARENT_GONE_EXIT)


def existing_path_entries(paths: list[str]) -> list[str]:
    """The import-path entries that exist, in order (step 8a, owner 2026-10-06)."""
    return [p for p in paths if os.path.exists(p)]


def _main() -> int:
    request = json.loads(sys.stdin.read())
    if request.get("parent_pid") is not None:  # step 9b (A3): started by `start_guarded`
        _die_with_parent(int(request["parent_pid"]))
    scratch = request["scratch"]
    for name in SCRATCH_ENV:
        os.environ[name] = scratch
    tempfile.tempdir = scratch
    os.chdir(scratch)
    package_parent = os.path.dirname(file_guard.PACKAGE_DIR)
    sys.path[:] = [p for p in sys.path if p not in ("", ".") and os.path.realpath(p) != package_parent]
    sys.path[:] = existing_path_entries(sys.path)
    sys.path_importer_cache.clear()
    for name in PRELOADED:
        importlib.import_module(name)
    file_guard.install(scratch)
    try:
        module_name, function = request["target"].split(":", 1)
        if not module_name.startswith("hypocurate."):
            raise ValueError(f"target {request['target']!r} is outside the package")
        result = getattr(importlib.import_module(module_name), function)(request["payload"])
        answer = {"ok": True, "result": result}
    except Exception as error:  # reported to the parent, which raises GuardedRunError
        answer = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    sys.stdout.write("\n" + json.dumps(answer) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
