"""Step 9b, addition A3 (owner, 2026-10-08; docs/reviews/step09b_plan.md): the guarded child dies with its parent.

The worker's main thread starts the child (`guarded.start_guarded`); the child sets PR_SET_PDEATHSIG(SIGKILL) first
thing, then checks that its parent is still the process that started it. Tests run a small parent process (a script
written for the test) so it can be killed without killing the test."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time

import pytest

from hypocurate.access import guarded

PARENT = """
import json, sys, threading
from hypocurate.access import guarded
seconds = float(sys.argv[1])
child = guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": seconds}])
print(json.dumps({"child": child.pid}), flush=True)
if len(sys.argv) > 2 and sys.argv[2] == "thread_exits":
    t = threading.Thread(target=lambda: None)   # a thread of the parent (like the heartbeat) that ends
    t.start(); t.join()
print(json.dumps({"result": child.result(timeout=60)}), flush=True)
"""


def gone(pid: int) -> bool:
    """The process no longer runs (it does not exist, or only its zombie is left)."""
    try:
        with open(f"/proc/{pid}/status") as f:
            return any(line.startswith("State:") and "Z" in line.split()[1] for line in f)
    except FileNotFoundError:
        return True


def start_parent(tmp_path, *args):
    script = tmp_path / "parent.py"
    script.write_text(PARENT)
    proc = subprocess.Popen([sys.executable, str(script), *args], stdout=subprocess.PIPE, text=True,
                            env=dict(os.environ))
    child = json.loads(proc.stdout.readline())["child"]
    return proc, child


def test_the_child_dies_within_two_seconds_when_its_parent_is_killed(tmp_path):
    parent, child = start_parent(tmp_path, "60")
    time.sleep(0.5)
    assert not gone(child)
    parent.send_signal(signal.SIGKILL)
    parent.wait(5)
    deadline = time.time() + 2
    while not gone(child) and time.time() < deadline:
        time.sleep(0.05)
    assert gone(child), "the child outlived its parent"


def test_the_child_outlives_a_thread_of_its_parent_that_exits(tmp_path):
    """PR_SET_PDEATHSIG follows the thread that started the child: a heartbeat-like thread ending must not kill it."""
    parent, child = start_parent(tmp_path, "2", "thread_exits")
    out = json.loads(parent.stdout.readline())
    parent.wait(10)
    assert out == {"result": ["ok"]}


def test_a_child_is_started_only_from_the_main_thread():
    errors = []

    def start():
        try:
            guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": 0}])
        except RuntimeError as error:
            errors.append(str(error))

    t = threading.Thread(target=start)
    t.start()
    t.join(10)
    assert errors and "main thread" in errors[0]


def test_a_child_whose_parent_is_already_gone_exits_at_once():
    """The fork race: the parent died before the child set its death signal; the child sees another parent."""
    request = {"target": "hypocurate.access.guard_probe:probe", "payload": [{"op": "sleep", "seconds": 30}],
               "scratch": "/tmp", "parent_pid": 1}
    started = time.time()
    done = subprocess.run([sys.executable, "-m", guarded.MODULE], input=json.dumps(request), capture_output=True,
                          text=True, timeout=20)
    assert time.time() - started < 10
    assert done.returncode == guarded.PARENT_GONE_EXIT and '"ok": true' not in done.stdout


def test_start_guarded_gives_the_same_answer_as_run_guarded():
    child = guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": 0}])
    assert child.result(timeout=60) == guarded.run_guarded("hypocurate.access.guard_probe:probe",
                                                           [{"op": "sleep", "seconds": 0}], timeout=60) == ["ok"]


def test_a_child_that_fails_raises_guarded_run_error():
    child = guarded.start_guarded("hypocurate.access.guard_probe:no_such_function", [])
    with pytest.raises(guarded.GuardedRunError):
        child.result(timeout=60)
