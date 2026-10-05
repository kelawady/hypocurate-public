"""Checks of the file guard from inside a guarded process (`guarded.run_guarded`).

`probe(actions)` performs each action and reports "ok", or "refused: ..." when the guard
refused it. It is how the tests (and, later, a deploy-time self-check) show what the
tripwire catches. It reads nothing it reports beyond a byte count. It does not show that
the guard cannot be bypassed: it cannot be, by design (see `file_guard`).
"""
from __future__ import annotations

import io
import os
import pathlib
import ssl
import subprocess
import tempfile
from typing import Any, Callable


def _read(path: str, how: str) -> str:
    if how == "open":
        with open(path, "rb") as f:
            return f"ok {len(f.read())} bytes"
    if how == "io.open":
        with io.open(path, "rb") as f:
            return f"ok {len(f.read())} bytes"
    if how == "pathlib":
        return f"ok {len(pathlib.Path(path).read_bytes())} bytes"
    if how == "os.open":
        fd = os.open(path, os.O_RDONLY)
        os.close(fd)
        return "ok"
    raise ValueError(how)


def _list(path: str, how: str) -> str:
    if how == "listdir":
        return f"ok {len(os.listdir(path))} entries"
    if how == "scandir":
        with os.scandir(path) as it:
            return f"ok {sum(1 for _ in it)} entries"
    raise ValueError(how)


def _write(path: str) -> str:
    with open(path, "w") as f:
        f.write("x")
    return "ok"


def _write_scratch(_: Any) -> str:
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("cache")
        name = f.name
    with open(name) as f:
        assert f.read() == "cache"
    os.remove(name)
    cache = os.path.join(os.environ["MPLCONFIGDIR"], "cache.txt")
    with open(cache, "w") as f:
        f.write("x")
    return f"ok in {os.path.dirname(name) == os.environ['TMPDIR']}"


def _scratch(_: Any) -> str:
    """Where the scratch directory is, and its permissions (it is removed when the run ends)."""
    return f"ok {os.environ['TMPDIR']} {oct(os.stat(os.environ['TMPDIR']).st_mode & 0o777)} {os.getcwd()}"


def _render(_: Any) -> str:
    from hypocurate.web.app import templates
    html = templates.get_template("login.html").render(error=None)
    return f"ok {'<form' in html}"


def _database(_: Any) -> str:
    from sqlalchemy import text
    from hypocurate.db.engine import make_engine
    engine = make_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        value = conn.execute(text("SELECT now() IS NOT NULL AND 1 = 1")).scalar_one()
    engine.dispose()
    return f"ok {value}"


def _certificates(_: Any) -> str:
    import urllib.request
    context = ssl.create_default_context()
    urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    return f"ok {context.cert_store_stats()['x509_ca'] > 0}"


def _subprocess(_: Any) -> str:
    subprocess.run(["true"], check=True)
    return "ok"


def _system(_: Any) -> str:
    os.system("true")
    return "ok"


def _ctypes(_: Any) -> str:
    import ctypes
    ctypes.CDLL(None)
    return "ok"


def _ctypes_string_at(_: Any) -> str:
    """Calls through preloaded ctypes functions (string_at) raise the call event the guard refuses."""
    import ctypes
    return f"ok {ctypes.string_at(ctypes.c_char_p(b'x'), 1)!r}"


def _ctypes_from_address(_: Any) -> str:
    """A documented limit of the tripwire: ctypes, once imported before the guard (by the database
    driver), can still read process memory directly (`from_address`); only new library loads and
    foreign calls are refused."""
    import ctypes
    buffer = ctypes.create_string_buffer(b"x")
    return f"ok {ctypes.c_char.from_address(ctypes.addressof(buffer)).value!r}"


def _register(_: Any) -> str:
    from hypocurate.sources.versions import SOURCES, read_definition_files
    read_definition_files(SOURCES["mpea"])
    return "ok"


def _role_input(action: dict) -> str:
    """A role's complete input, built through the dispatcher and the access layer inside the
    guarded process."""
    import base64
    import json
    from hypocurate.access import bind, role_input
    from hypocurate.db.engine import make_engine
    engine = make_engine(os.environ["DATABASE_URL"])
    access = bind(engine, action["run"], action["agent_setting"], source_key=action.get("source"))
    out = json.dumps(role_input(access), sort_keys=True,
                     default=lambda b: base64.b64encode(b).decode() if isinstance(b, bytes) else str(b))
    engine.dispose()
    return out


ACTIONS: dict[str, Callable[[dict], str]] = {
    "read": lambda a: _read(a["path"], a.get("how", "open")),
    "list": lambda a: _list(a["path"], a.get("how", "listdir")),
    "write": lambda a: _write(a["path"]),
    "write_scratch": _write_scratch, "scratch": _scratch, "render": _render, "database": _database, "certificates": _certificates,
    "subprocess": _subprocess, "system": _system, "ctypes": _ctypes, "ctypes_string_at": _ctypes_string_at,
    "ctypes_from_address": _ctypes_from_address,
    "register": _register,
    "role_input": _role_input,
}


def probe(actions: list[dict]) -> list[str]:
    out = []
    for action in actions:
        try:
            out.append(ACTIONS[action["op"]](action))
        except PermissionError as error:
            out.append(f"refused: {error}")
        except Exception as error:
            out.append(f"error: {type(error).__name__}: {error}")
    return out
