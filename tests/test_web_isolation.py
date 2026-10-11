"""Step 10a: the web service never calls a model, never claims a run and never runs a pipeline (owner's step 10 brief;
criterion 14.4: closing the browser or restarting the web service never affects a run).

A fresh process builds the app, signs in and opens every run page; afterwards no model library (dspy, litellm), and
none of the queue, the worker, the orchestrator, recovery or the guarded runner is loaded in it. The source scan of
tests/test_worker.py (direct imports in web/) still holds; this checks what a page actually loads.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine

FORBIDDEN = ("dspy", "litellm", "hypocurate.pipeline.queue", "hypocurate.worker", "hypocurate.pipeline.orchestrator",
             "hypocurate.pipeline.recovery", "hypocurate.access.guarded", "hypocurate.pipeline.agents.interface")

PROBE = textwrap.dedent("""
    import json, re, sys
    from fastapi.testclient import TestClient
    from hypocurate.config import Settings
    from hypocurate.web.app import create_app
    url, completed, waiting = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    s = Settings(env="development", database_url=url, password="test-password-not-a-secret", session_secret="s" * 40,
                 version="test")
    c = TestClient(create_app(s), base_url="http://testserver", follow_redirects=False)
    assert c.post("/login", data={"password": "test-password-not-a-secret", "name": "Probe"}).status_code == 303
    codes = [c.get(p).status_code for p in ("/", "/runs", f"/runs/{completed}", f"/runs/{waiting}",
                                            f"/runs/{waiting}/confirm", "/assumptions")]
    print(json.dumps({"codes": codes, "loaded": sorted(m for m in sys.modules if m.startswith(("dspy", "litellm",
                                                                                          "hypocurate")))}))
""")


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner(engine, migrated_database, tmp_path):
    stub = sp.StubProvider()
    try:
        stub.respond(to.responder(to.planner_body()))
        done = to.dispatched(engine, fixed_plan=True)
        assert to.run(engine, done, stub).status == "completed"
        waiting = to.dispatched(engine)
        from hypocurate.pipeline import orchestrator
        assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
    finally:
        stub.close()
    probe = tmp_path / "probe.py"
    probe.write_text(PROBE, encoding="utf-8")
    # The package from this checkout (installed in a venv, or only on the path as in the test image).
    root = pathlib.Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root)}
    out = subprocess.run([sys.executable, str(probe), migrated_database, str(done), str(waiting)], cwd=tmp_path,
                         env=env, capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-2000:]
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["codes"] == [200, 200, 200, 200, 200, 200]
    loaded = set(result["loaded"])
    assert "hypocurate.web.app" in loaded and "hypocurate.pipeline.run_view" in loaded  # the probe did load the pages
    assert not [m for m in loaded if m in FORBIDDEN or m.split(".")[0] in ("dspy", "litellm")], loaded
