"""Step 8a: the model-call libraries (DSPy, litellm) and the file guard (owner, 2026-10-06).

litellm reads a `.env` file when it is imported unless `LITELLM_MODE` is `PRODUCTION`; the
tripwire caught it reading the repository's `.env` (which holds the secrets) in a guarded run.
`hypocurate.pipeline.agents.libraries` is the one place that imports them, and it sets that mode
first. Importing them under the guard also made Python probe a `sys.path` entry that does not
exist (the standard library's zip); the guarded process now drops such entries before the guard
is installed (owner's decision), so a clean agent import logs no refusal while the tripwire still
watches everything the libraries do (a planted `.env` read is still refused).

What these tests do not show: that the libraries make no other file access on code paths not
exercised here (a real model request is tested in the agent-core tests, through a local stub
provider).
"""
from __future__ import annotations

import ast
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from hypocurate.access import guarded
from hypocurate.access.guarded import run_guarded

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "hypocurate"
PROBE = "hypocurate.access.guard_probe:probe"


def _guard_lines(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if "file_guard" in r.getMessage()]


def test_the_agent_libraries_import_under_the_guard_with_no_refusal(caplog):
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    result = run_guarded(PROBE, [{"op": "agent_libraries"}], env=dict(os.environ), timeout=300)
    assert result == ["ok"]
    assert _guard_lines(caplog) == []


def test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard(tmp_path, caplog):
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    planted = tmp_path / ".env"
    planted.write_text("PLANTED_SECRET=do-not-read\n")
    result = run_guarded(PROBE, [{"op": "agent_libraries"}, {"op": "dotenv", "path": str(planted)}],
                         env=dict(os.environ), timeout=300)
    assert result[0] == "ok"
    assert result[1].startswith("refused: file guard: reading"), result
    assert any(str(planted) in line for line in _guard_lines(caplog))


def test_the_statistics_libraries_import_under_the_guard_with_no_refusal(caplog):
    """Step 8b (owner, 2026-10-07): scipy is preloaded (PRELOADED), since importing it makes a ctypes foreign
    call at load time; then what a guarded run imports loads with no refusal, and loads no statsmodels (test-only),
    pandas or patsy."""
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    assert run_guarded(PROBE, [{"op": "statistics_libraries"}], env=dict(os.environ), timeout=300) == ["ok"]
    assert _guard_lines(caplog) == []


def test_after_the_statistics_libraries_a_ctypes_call_and_a_planted_env_read_are_still_refused(tmp_path, caplog):
    """Preloading scipy changes what the guard sees only for that import."""
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    planted = tmp_path / ".env"
    planted.write_text("PLANTED_SECRET=do-not-read\n")
    result = run_guarded(PROBE, [{"op": "statistics_libraries"}, {"op": "ctypes_string_at"}, {"op": "ctypes"},
                                 {"op": "dotenv", "path": str(planted)}], env=dict(os.environ), timeout=300)
    assert result[0] == "ok"
    assert result[1] == "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code"
    assert result[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code"
    assert result[3].startswith("refused: file guard: reading"), result


def test_missing_path_entries_are_dropped_and_the_others_kept(tmp_path):
    present = tmp_path / "present"
    present.mkdir()
    entries = [str(present), str(tmp_path / "missing"), str(tmp_path / "missing.zip"), str(present)]
    assert guarded.existing_path_entries(entries) == [str(present), str(present)]


def test_the_libraries_never_read_a_dotenv_file_outside_the_guard(tmp_path):
    """A fresh interpreter in a directory holding a `.env`, with LITELLM_MODE set to DEV in its
    environment: loading the libraries through our module opens no `.env` file and leaves the
    planted variable unset."""
    (tmp_path / ".env").write_text("PLANTED_SECRET=do-not-read\n")
    script = (
        "import sys, json, os\n"
        "opened = []\n"
        "sys.addaudithook(lambda e, a: opened.append(str(a[0])) if e == 'open' and a and "
        "str(a[0]).endswith('.env') else None)\n"
        "from hypocurate.pipeline.agents import libraries\n"
        "libraries.load()\n"
        "print(json.dumps({'opened': opened, 'planted': os.environ.get('PLANTED_SECRET'),"
        " 'mode': os.environ.get('LITELLM_MODE')}))\n")
    env = {k: v for k, v in os.environ.items() if k != "PLANTED_SECRET"}
    env["LITELLM_MODE"] = "DEV"
    done = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env, capture_output=True,
                          text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-2000:]
    out = json.loads(done.stdout.strip().splitlines()[-1])
    assert out == {"opened": [], "planted": None, "mode": "PRODUCTION"}


def test_only_the_libraries_module_imports_dspy_or_litellm():
    """A tripwire for our own code: every other module goes through `libraries.load()`, which
    sets the environment first."""
    allowed = PACKAGE / "pipeline" / "agents" / "libraries.py"
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        if path == allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(n.split(".")[0] in ("dspy", "litellm") for n in names):
                offenders.append(str(path.relative_to(REPO)))
    assert offenders == []
