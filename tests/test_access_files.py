"""Step 5: the file guard, a tripwire against accidental file access by trusted pipeline code.

Each test starts real guarded processes (`run_guarded`) and probes them from inside
(`hypocurate.access.guard_probe`). The tests show what the tripwire catches when our own code
makes a mistake: reading or listing answer material (`tests/`), review documents
(`docs/reviews/`), the frozen files (`data/`) or the repository root, by any of Python's usual
ways of opening a file; writing outside the private scratch directory; starting another
program; loading a new native library. They also show that what pipeline code needs still
works (templates, the database driver, the certificate bundle, the scratch directory, a role's
input through the dispatcher).

They do **not** show that the guard cannot be bypassed: it can, by code that tries (an open
descriptor, the guard's own state, preloaded ctypes; see `file_guard` and Python's warning on
audit hooks). `test_preloaded_ctypes_still_works_a_documented_limit` records one such limit.
The construction-level guarantee is the deployed image without `tests/` and `docs/`
(`tests/test_check_runtime_image.py`).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import sqlalchemy

import pytest

import access_world as aw
from hypocurate.access import bind, file_guard, role_input
from hypocurate.access.guarded import GuardedRunError, run_guarded
from hypocurate.db.engine import make_engine

REPO = Path(__file__).resolve().parent.parent
PROBE = "hypocurate.access.guard_probe:probe"
HOWS = ("open", "io.open", "pathlib", "os.open")


def probe(actions, database_url=None):
    env = dict(os.environ)
    if database_url:
        env["DATABASE_URL"] = database_url
    return run_guarded(PROBE, actions, env=env, timeout=120)


def test_answers_reviews_data_and_the_repository_root_cannot_be_read():
    targets = [REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv",
               REPO / "tests" / "fixtures" / "controlled_duplicates" / "build.py",
               REPO / "docs" / "reviews" / "step01_summary.md", REPO / "docs" / "reviews" / "checklist.md",
               REPO / "data" / "sources" / "mpea" / "MPEA_dataset.csv", REPO / "data" / "manifest.json",
               REPO / "data" / "controlled_duplicates" / "extract.csv", REPO / "CLAUDE.md", REPO / "README.md"]
    for t in targets:
        assert t.is_file(), t  # they exist: the refusals are the guard's, not missing files
    actions = [{"op": "read", "path": str(t), "how": how} for t in targets for how in HOWS]
    results = probe(actions)
    for action, result in zip(actions, results):
        assert result.startswith("refused: file guard: reading"), (action, result)


def test_the_repository_root_and_the_answer_directories_cannot_be_listed():
    dirs = [REPO, REPO / "tests", REPO / "tests" / "fixtures", REPO / "docs" / "reviews", REPO / "data"]
    actions = [{"op": "list", "path": str(d), "how": how} for d in dirs for how in ("listdir", "scandir")]
    for action, result in zip(actions, probe(actions)):
        assert result.startswith("refused: file guard"), (action, result)


def test_relative_paths_are_refused():
    actions = [{"op": "read", "path": p} for p in ("tests/fixtures/controlled_duplicates/truth.csv",
                                                   "../tests/x", "data/manifest.json", "x.txt")]
    for result in probe(actions):
        assert result.startswith("refused: file guard: relative path"), result


def test_the_python_installation_and_the_package_code_can_be_read():
    targets = [REPO / "hypocurate" / "assumptions.json", Path(os.__file__), Path(sqlalchemy.__file__)]
    actions = [{"op": "read", "path": str(t)} for t in targets]
    actions.append({"op": "list", "path": str(REPO / "hypocurate"), "how": "scandir"})
    for action, result in zip(actions, probe(actions)):
        assert result.startswith("ok"), (action, result)


def test_writes_outside_the_scratch_directory_are_refused():
    name = f"hc-written-{uuid.uuid4().hex}.txt"  # unique, and removed below even if the guard fails
    site = Path(sqlalchemy.__file__).parent.parent
    targets = [REPO / "hypocurate" / name, site / name, REPO / name, REPO / "tests" / name,
               Path(tempfile.gettempdir()) / name]
    try:
        results = probe([{"op": "write", "path": str(t)} for t in targets])
        created = [t for t in targets if t.exists()]
    finally:
        for t in targets:
            t.unlink(missing_ok=True)
    assert created == []
    for t, result in zip(targets, results):
        assert result.startswith("refused: file guard: writing"), (t, result)


def test_a_library_can_use_the_private_scratch_directory_which_is_removed_afterwards():
    write, scratch = probe([{"op": "write_scratch"}, {"op": "scratch"}])
    assert write == "ok in True"
    _, path, mode, cwd = scratch.split()
    assert mode == "0o700" and cwd == path and Path(path).name.startswith("hc-run-")
    assert not Path(path).exists()


def test_no_other_program_and_no_new_native_library():
    results = probe([{"op": "subprocess"}, {"op": "system"}, {"op": "ctypes"}])
    assert results[0] == "refused: file guard: subprocess.Popen is outside the approved inputs of pipeline code"
    assert results[1] == "refused: file guard: os.system is outside the approved inputs of pipeline code"
    assert results[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code"


def test_templates_database_and_certificates_work_under_the_guard(migrated_database):
    """Owner's addition C: the guard is not bought by breaking what pipeline code needs."""
    results = probe([{"op": "render"}, {"op": "database"}, {"op": "certificates"}], migrated_database)
    assert results == ["ok True", "ok True", "ok True"]


def test_preloaded_ctypes_still_works_a_documented_limit():
    """Review finding 1: ctypes imported before the guard can still read process memory directly.
    (A foreign call such as string_at raises the call event, which the tripwire refuses here.)"""
    assert probe([{"op": "ctypes_from_address"}, {"op": "ctypes_string_at"}]) == [
        "ok b'x'", "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code"]


def test_source_registration_cannot_run_under_the_guard():
    result, = probe([{"op": "register"}])
    assert result == ("error: RegistrationError: source registration reads data/ and cannot run in a guarded "
                      "pipeline process (step 5)")


def test_a_roles_complete_input_is_the_same_inside_the_guard(migrated_database):
    engine = make_engine(migrated_database)
    world = aw.build(engine, "before_lock")
    expected = role_input(bind(engine, world.run, world.settings["planner"]))
    engine.dispose()
    got, = probe([{"op": "role_input", "run": world.run, "agent_setting": world.settings["planner"]}],
                 migrated_database)
    assert json.loads(got) == json.loads(json.dumps(expected, sort_keys=True))


def test_the_guard_cannot_be_installed_outside_the_guarded_process():
    with pytest.raises(RuntimeError, match="installed only in the process started by"):
        file_guard.install(tempfile.gettempdir())
    assert not file_guard.installed()


def test_run_guarded_runs_only_package_code():
    for target in ("tests.access_world:build", "os:system", "hypocurate.access.guard_probe"):
        with pytest.raises(ValueError):
            run_guarded(target, [])
    with pytest.raises(GuardedRunError, match="ModuleNotFoundError"):
        run_guarded("hypocurate.no_such_module:f", [], timeout=60)


def test_the_test_process_itself_is_not_guarded():
    assert not file_guard.installed()
    assert (REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv").read_bytes()
    assert sys.modules["__main__"].__spec__ is None or sys.modules["__main__"].__spec__.name != file_guard.GUARDED_MAIN


@pytest.mark.parametrize("scratch", ["tests", "data", "repo", "not_private", "not_empty", "wrong_name"])
def test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else(scratch):
    """The scratch directory is where writes are allowed; the child accepts only a fresh,
    empty, private hc-run-* directory directly in the system temporary directory."""
    made = None
    if scratch in ("tests", "data"):
        path = REPO / scratch
    elif scratch == "repo":
        path = REPO
    else:
        made = Path(tempfile.mkdtemp(prefix="hc-run-" if scratch != "wrong_name" else "other-",
                                     dir=file_guard.SYSTEM_TEMP))
        if scratch == "not_private":
            made.chmod(0o755)
        if scratch == "not_empty":
            (made / "x").write_text("x")
        path = made
    try:
        done = subprocess.run([sys.executable, "-m", "hypocurate.access.guarded"], capture_output=True, text=True,
                              input=json.dumps({"target": "hypocurate.access.guard_probe:probe", "payload": [],
                                                "scratch": str(path)}), timeout=60)
    finally:
        if made:
            for f in made.iterdir():
                f.unlink()
            made.rmdir()
    assert done.returncode != 0 and "unsuitable scratch directory" in done.stderr
