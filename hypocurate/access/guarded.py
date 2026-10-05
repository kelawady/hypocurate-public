"""Runs pipeline code in a fresh process under the file guard's tripwire (`file_guard`).

`run_guarded("hypocurate.module:function", payload, audit=(engine, run_id))` starts
`python -m hypocurate.access.guarded`, sends it the target and a JSON payload, and returns
the target's JSON result. The child:

1. receives a private scratch directory (mode 0700, created by the parent, which removes it
   when the child ends, however it ends) and points `TMPDIR`, `MPLCONFIGDIR` and
   `XDG_CACHE_HOME` at it, for libraries that need a cache or temporary files (the
   plotting library in step 7); its working directory is the scratch directory;
2. removes the repository root from its import path (the `hypocurate` package is already
   imported and keeps its own path), and imports the modules in `PRELOADED`;
3. installs the guard;
4. imports the target, which must be inside the `hypocurate` package, calls it with the
   payload, writes the result to its standard output and exits.

The guard's refusals come back on the child's standard error; the parent copies each into
the audit log as a failure (code `file_guard`) for the run given in `audit`, or to the
process log if no run is given or the database cannot take it.

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
import subprocess
import sys
import tempfile
from typing import Any

from hypocurate.access import file_guard

MODULE = "hypocurate.access.guarded"
SCRATCH_ENV = ("TMPDIR", "MPLCONFIGDIR", "XDG_CACHE_HOME")
# Imported before the guard is installed: the database driver imports `ctypes`, which loads
# the process's own symbols when it is first imported, and the guard refuses any ctypes
# load. Importing it first changes no refusal: after installation every ctypes load,
# symbol lookup and call is still refused, and reading the Python installation is allowed.
PRELOADED = ("psycopg",)


class GuardedRunError(Exception):
    """The guarded process failed; the message is its error."""


MAX_REPORTED = 100  # refusals copied into the audit log per run; the rest are counted


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
        completed = subprocess.run([sys.executable, "-m", MODULE],
                                   input=json.dumps({"target": target, "payload": payload, "scratch": scratch}),
                                   capture_output=True, text=True, timeout=timeout,
                                   env=env if env is not None else dict(os.environ))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    _report_refusals(completed.stderr, audit)
    lines = completed.stdout.strip().splitlines()
    try:
        answer = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise GuardedRunError(f"the guarded process gave no answer (exit {completed.returncode}): "
                              f"{completed.stderr.strip()[-2000:]}") from None
    if not answer.get("ok"):
        raise GuardedRunError(answer.get("error", "unknown error"))
    return answer["result"]


def _main() -> int:
    request = json.loads(sys.stdin.read())
    scratch = request["scratch"]
    for name in SCRATCH_ENV:
        os.environ[name] = scratch
    tempfile.tempdir = scratch
    os.chdir(scratch)
    package_parent = os.path.dirname(file_guard.PACKAGE_DIR)
    sys.path[:] = [p for p in sys.path if p not in ("", ".") and os.path.realpath(p) != package_parent]
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
