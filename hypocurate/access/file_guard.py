"""A tripwire against accidental file access by pipeline code (step 5; review finding 1).

**What it is.** In the process that runs one pipeline run (`guarded.run_guarded`), a Python
audit hook (`sys.addaudithook`) refuses, with `PermissionError`, what *trusted, reviewed*
pipeline code should never do by mistake:
- reading or listing anything outside the Python installation (standard library, installed
  packages, the certificate bundle) and the `hypocurate` package's code: so the repository
  root, `tests/`, `docs/` (including `docs/reviews/`) and `data/`;
- writing anywhere but the run's private scratch directory;
- relative paths;
- starting another program (`subprocess`, `os.system`, `exec`, `spawn`, `fork`) and loading a
  new native library through `ctypes`.
Each refusal is written as one bounded line to the process's standard error, and the parent
copies it into the audit log as a failure (code `file_guard`) when it knows the run.

**What it is not.** Python's own documentation warns that audit hooks are not suitable for
implementing a sandbox, because code in the same process can bypass them
(https://docs.python.org/3/library/sys.html#sys.addaudithook; PEP 578). In particular, as the
step 5 review showed:
- a file descriptor that is already open can still be read;
- the guard's own state can be changed from inside the process;
- `ctypes`, once imported (the database driver imports it before the guard is installed),
  can still read and write process memory directly (`from_address`; tested). Foreign calls
  raise an audit event the hook refuses (`string_at` was refused in our runs, though the
  review reports it working in its setup), but that is no barrier to code that tries;
- sockets, and so the database with the credentials the process has, are not restricted;
- the child inherits its environment, and startup hooks or modules imported before the guard
  run unguarded;
- checking a path and then opening it is not atomic.
So it catches accidents by our own code; it does not stop code that tries to get around it.
That is enough under the threat model (owner, 2026-10-05; CLAUDE.md, register 'threat_model'):
agents return text only and never execute code, and only trusted code runs. Agents that
execute code are in the backlog, with operating-system isolation as a precondition.

**The one construction-level guarantee** about answer material is the deployed image: it
contains no `tests/` and no `docs/` (Dockerfile; checked in CI by `scripts/check_runtime_image.py`).
In development the files exist on disk, and only this tripwire stands in the way of an
accidental read.

`install()` runs only in the process started by `python -m hypocurate.access.guarded`, once,
with a private scratch directory; it refuses to run in any other process, so the web service,
the migrations, the `sources` commands (registration reads `data/`) and the tests are never
guarded.
"""
from __future__ import annotations

import json
import os
import stat
import sys
import sysconfig
import tempfile
from pathlib import Path

GUARDED_MAIN = "hypocurate.access.guarded"
PACKAGE_DIR = os.path.realpath(Path(__file__).resolve().parent.parent)
# The system temporary directory, read when this module is imported (before the guarded
# process points TMPDIR at its scratch directory). Scratch directories live directly in it.
SYSTEM_TEMP = os.path.realpath(tempfile.gettempdir())
SCRATCH_PREFIX = "hc-run-"

# Events that start another program or load native code: always refused.
REFUSED_EVENTS = frozenset({
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty",
    "pty.spawn", "ctypes.dlopen", "ctypes.dlsym", "ctypes.call_function",
})
# Events that change the file system: allowed only inside the scratch directory.
WRITE_EVENTS = frozenset({
    "os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.chown", "os.utime", "os.truncate",
    "os.link", "os.symlink", "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree",
    "shutil.move", "shutil.rmtree", "shutil.chown", "shutil.make_archive", "shutil.unpack_archive",
})
LIST_EVENTS = frozenset({"os.listdir", "os.scandir"})
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND

_state: dict = {"installed": False, "scratch": None, "read_roots": ()}


def installed() -> bool:
    return _state["installed"]


def scratch_directory() -> str | None:
    return _state["scratch"]


def read_roots() -> tuple[str, ...]:
    """The directories the guarded process may read: the Python installation and the package."""
    paths = sysconfig.get_paths()
    roots = {os.path.realpath(paths[k]) for k in ("stdlib", "platstdlib", "purelib", "platlib")}
    roots.add(PACKAGE_DIR)
    return tuple(sorted(roots))


def _inside(path: str, roots) -> bool:
    return any(path == r or path.startswith(r + os.sep) for r in roots)


def _resolve(path) -> str | None:
    """The real absolute path, or None for a relative one (refused)."""
    path = os.fsdecode(path)
    if not os.path.isabs(path):
        return None
    return os.path.realpath(path)


REPORT_PREFIX = "HCGUARD "  # one line per refusal on standard error, read by guarded.run_guarded


def _printable(value: str, limit: int = 200) -> str:
    return "".join(c if c.isprintable() else "?" for c in value[:limit])


def _refuse(what: str, event: str = "open") -> None:
    message = f"file guard: {what} is outside the approved inputs of pipeline code"
    try:  # no audit event is raised by writing to an already-open stream
        sys.stderr.write(REPORT_PREFIX + json.dumps({"event": _printable(event, 40), "what": _printable(what)}) + "\n")
        sys.stderr.flush()
    except Exception:
        pass
    raise PermissionError(message)


def _check_path(path, writing: bool) -> None:
    if path is None or isinstance(path, int):  # an already-open descriptor (checked when opened)
        return
    real = _resolve(path)
    if real is None:
        _refuse(f"relative path {os.fsdecode(path)!r}", "relative_path")
    scratch = _state["scratch"]
    allowed = _inside(real, (scratch,)) if writing else _inside(real, _state["read_roots"] + (scratch,))
    if not allowed:
        _refuse(f"{'writing' if writing else 'reading'} {real}", "write" if writing else "read")


def _hook(event: str, args: tuple) -> None:
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool((flags or 0) & _WRITE_FLAGS)
        _check_path(path, writing)
    elif event in LIST_EVENTS:
        _check_path(args[0] if args and args[0] is not None else os.getcwd(), writing=False)
    elif event in WRITE_EVENTS:
        for a in args:
            if isinstance(a, (str, bytes, os.PathLike)):
                _check_path(a, writing=True)
    elif event in REFUSED_EVENTS:
        _refuse(f"{event}", event)


def check_scratch(scratch: str) -> None:
    """A scratch directory must be a fresh, empty, private `hc-run-*` directory directly in
    the system temporary directory, so that it can never open up anything else."""
    info = os.lstat(scratch)
    if (os.path.dirname(scratch) != SYSTEM_TEMP or not os.path.basename(scratch).startswith(SCRATCH_PREFIX)
            or not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_uid != os.getuid() or os.listdir(scratch)):
        raise RuntimeError(f"unsuitable scratch directory {scratch}")


def install(scratch: str) -> None:
    """Installs the guard for the rest of this process. Only `python -m hypocurate.access.guarded`
    may call it, once, with its private scratch directory."""
    main = sys.modules.get("__main__")
    spec = getattr(main, "__spec__", None)
    if spec is None or spec.name != GUARDED_MAIN:
        raise RuntimeError("the file guard is installed only in the process started by "
                           f"`python -m {GUARDED_MAIN}`")
    if _state["installed"]:
        raise RuntimeError("the file guard is already installed")
    scratch = os.path.realpath(scratch)
    check_scratch(scratch)
    sys.dont_write_bytecode = True  # no .pyc written next to the package
    _state.update(installed=True, scratch=scratch, read_roots=read_roots())
    sys.addaudithook(_hook)
