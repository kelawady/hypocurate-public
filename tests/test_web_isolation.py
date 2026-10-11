"""Step 10a: the web service never calls a model, never claims a run and never runs a pipeline (owner's step 10 brief;
criterion 14.4: closing the browser or restarting the web service never affects a run).

A fresh process builds the app, signs in and opens every run page; afterwards no model library (dspy, litellm), and
none of the queue, the worker, the orchestrator, recovery or the guarded runner is loaded in it. The source scan of
tests/test_worker.py (direct imports in web/) still holds; this checks what a page actually loads.

Step 10b, fix round 1 (ChatGPT's review; the owner): the same check for every page 10b added (queries, new query,
query, edit, review, sources and the connection test, each agent page, help, the plot on the run page, the workbook
and the CSV) and for every write the website makes (create, edit, return, dispatch, dispatch again, register).
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


PROBE_10B = textwrap.dedent("""
    import json, re, sys
    from fastapi.testclient import TestClient
    from hypocurate.config import Settings
    from hypocurate.web.app import create_app
    url, completed, draft, submitted, again = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    s = Settings(env="development", database_url=url, password="test-password-not-a-secret", session_secret="s" * 40,
                 version="test")
    c = TestClient(create_app(s), base_url="http://testserver", follow_redirects=False)
    assert c.post("/login", data={"password": "test-password-not-a-secret", "name": "Probe"}).status_code == 303
    import base64
    payload = c.cookies["hypocurate_session"].split(".")[0]
    token = json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4)))["csrf"]
    def shown(page):
        return {"version_id": re.search(r'name="version_id" value="(\\d+)"', page).group(1),
                "version_fingerprint": re.search(r'name="version_fingerprint" value="([0-9a-f]{64})"', page).group(1)}
    pages = ["/queries", "/queries/new", f"/queries/{draft}", f"/queries/{draft}/edit", "/review",
             f"/review/{submitted}", "/sources", "/sources/mpea/test", "/agents/planner", "/agents/curator",
             "/agents/critic", "/agents/analyst", "/agents/commentator", "/help", "/help?q=grain", f"/runs/{completed}",
             f"/runs/{completed}/workbook", f"/runs/{completed}/records.csv", f"/queries/{again}"]
    codes = {p: c.get(p).status_code for p in pages}
    form = {"csrf_token": token, "claim": "Yield strength rises as grain size falls", "sources": ["mpea"],
            "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "note": ""}
    writes = {
        "create": c.post("/queries", data={**form, "action": "save"}).status_code,
        "edit": c.post(f"/queries/{draft}/edit", data={**form, "action": "submit",
                                                       **shown(c.get(f"/queries/{draft}/edit").text)}).status_code,
        "return": c.post(f"/review/{draft}/return", data={"csrf_token": token, "comment": "narrow it",
                                                          **shown(c.get(f"/review/{draft}").text)}).status_code,
        "dispatch": c.post(f"/review/{submitted}/dispatch", data={"csrf_token": token,
                                                                  "domain": "grain_size_strengthening",
                                                                  **shown(c.get(f"/review/{submitted}").text)}
                           ).status_code,
        "again": c.post(f"/queries/{again}/again", data={"csrf_token": token,
                                                         **shown(c.get(f"/queries/{again}").text)}).status_code,
        "register": c.post("/sources/tamu_fcc/register", data={"csrf_token": token}).status_code,
    }
    print(json.dumps({"codes": codes, "writes": writes, "loaded": sorted(
        m for m in sys.modules if m.startswith(("dspy", "litellm", "hypocurate")))}))
""")


def test_every_10b_page_and_write_loads_no_model_library_and_no_pipeline_runner(migrated_database, tmp_path):
    from hypocurate.pipeline import queries
    e = make_engine(migrated_database)
    stub = sp.StubProvider()
    try:
        pw.registered(e, ("mpea",))
        stub.respond(to.responder(to.planner_body()))
        q = queries.create(e, to.FCC_CLAIM, ["mpea"])
        queries.submit(e, q.version_id)
        queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
        done = queries.dispatch(e, q.version_id, fixed_plan=True)
        assert to.run(e, done, stub).status == "completed"
        draft = queries.create(e, to.FCC_CLAIM, ["mpea"]).number
        submitted = queries.create(e, to.FCC_CLAIM, ["mpea"], submit=True).number
    finally:
        stub.close()
        e.dispose()
    probe = tmp_path / "probe.py"
    probe.write_text(PROBE_10B, encoding="utf-8")
    root = pathlib.Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root)}
    out = subprocess.run([sys.executable, str(probe), migrated_database, str(done), draft, submitted, q.number],
                         cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-2000:]
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert set(result["codes"].values()) == {200}, result["codes"]
    assert result["writes"] == {"create": 303, "edit": 303, "return": 303, "dispatch": 303, "again": 303,
                                "register": 200}, result["writes"]
    loaded = set(result["loaded"])
    assert {"hypocurate.pipeline.plot", "hypocurate.pipeline.workbook", "hypocurate.pipeline.queries",
            "hypocurate.sources.versions"} <= loaded  # the probe did load the 10b pages and writes
    assert not [m for m in loaded if m in FORBIDDEN or m.split(".")[0] in ("dspy", "litellm")], loaded
