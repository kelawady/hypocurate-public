"""The approved input files of pipeline code (step 1 open item 4; step 5).

Pipeline code reads source data only as the sealed bytes of the source versions its run
recorded, through the access layer (`fields.source_content`, `fields.record_counts`); the
access layer has no function that takes a file path. This module makes everything else on
disk unreachable in the process that runs a pipeline, by construction:

- `install()` adds a Python audit hook, which cannot be removed once added. From then on
  the process may **read** only the Python installation (standard library and installed
  packages, including the certificate bundle) and the `hypocurate` package's own code
  directory, and may **write** only in its private scratch directory. Everything else is
  refused with `PermissionError`: in particular the repository root, `tests/`, `docs/`
  (and so `docs/reviews/`) and `data/`. Relative paths are refused (the hook cannot see a
  `dir_fd` they may be relative to). Starting another program (`subprocess`, `os.system`,
  `exec`, `spawn`, `fork`) and loading native code through `ctypes` are refused.
- It is installed only in a process started for one pipeline run, by
  `python -m hypocurate.access.guarded` (`guarded.run_guarded`), which exits when the run
  ends. `install()` refuses to run in any other process, so the guard can never be
  installed in a process that later needs those paths: the web service, the migrations,
  the command line's `sources` commands (registration reads `data/`) and the test process
  never install it.

Limit: an audit hook sees what Python code opens. Files that C libraries open themselves
(libpq's configuration, OpenSSL's certificate store) are not seen, and native code could
bypass the hook entirely, which is why loading native code through `ctypes` is refused.
It is an in-process guard, not an operating-system sandbox. The deployed image holds no
`tests/` or `docs/` at all (step 2, checked in CI).
"""
from __future__ import annotations

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


def _refuse(what: str) -> None:
    raise PermissionError(f"file guard: {what} is outside the approved inputs of pipeline code")


def _check_path(path, writing: bool) -> None:
    if path is None or isinstance(path, int):  # an already-open descriptor (checked when opened)
        return
    real = _resolve(path)
    if real is None:
        _refuse(f"relative path {os.fsdecode(path)!r}")
    scratch = _state["scratch"]
    allowed = _inside(real, (scratch,)) if writing else _inside(real, _state["read_roots"] + (scratch,))
    if not allowed:
        _refuse(f"{'writing' if writing else 'reading'} {real}")


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
        _refuse(f"{event}")


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
