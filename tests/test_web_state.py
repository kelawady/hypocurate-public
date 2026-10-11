"""Step 10a, milestone a3: run states and live updates (owner's brief: the page updates by itself while a run is in
progress; owner, 2026-10-11: a small polling script of our own, which stops once the run reaches an end state).

The server decides when polling ends: an open run's state carries `data-poll` (its own address); an ended run's carries
`data-ended` and no address; `static/poll.js` asks again only when the state it received carries `data-poll`. These tests
check that contract on every state, and the script's source for the rule; the browser itself is checked separately
with Playwright (step 10a summary). Criterion 14.4: a run goes on to its end whether or not a page is open, and across
a restart of the web service, because the web service only reads.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import time

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries, run_view
from test_web_runs import make_client, plain, signed_in, token

POLL_JS = pathlib.Path(run_view.__file__).resolve().parents[1] / "web" / "static" / "poll.js"


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def own(migrated_database, monkeypatch, stub):
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


def state_attrs(page: str) -> str:
    return re.search(r'<section class="state[^"]*" id="run-state"[^>]*>', page, re.S).group(0)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_an_open_runs_page_polls_its_own_state_and_an_ended_runs_page_does_not(own, stub):
    engine, url = own
    c = signed_in(engine, url)
    queued = to.dispatched(engine, fixed_plan=True)
    assert f'data-poll="/runs/{queued}/state"' in state_attrs(c.get(f"/runs/{queued}").text)
    stub.respond(to.responder(to.planner_body()))
    waiting = to.dispatched(engine)
    assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
    assert f'data-poll="/runs/{waiting}/state"' in state_attrs(c.get(f"/runs/{waiting}").text)
    running = pw.locked_run(engine)
    page = c.get(f"/runs/{running}").text
    assert f'data-poll="/runs/{running}/state"' in state_attrs(page)
    assert re.search(r"running\s*:\s*" + re.escape(run_view.STAGE_WORDS["curation"]), plain(page))  # stage in words
    # Ended: a completed run's page has no state to poll; a failed run's state says it ended and carries no address.
    stub.respond(to.responder())
    assert to.run(engine, queued, stub).status == "completed"
    done = c.get(f"/runs/{queued}").text
    assert "data-poll" not in done and 'id="run-state"' not in done
    queries.cancel(engine, waiting, by="Ada Reviewer")
    failed = state_attrs(c.get(f"/runs/{waiting}").text)
    assert 'data-ended="true"' in failed and "data-poll" not in failed


def test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended(own, stub):
    engine, url = own
    c = signed_in(engine, url)
    rid = to.dispatched(engine, fixed_plan=True)
    first = c.get(f"/runs/{rid}/state")
    assert first.status_code == 200 and first.headers["cache-control"] == "no-store"
    assert f'data-poll="/runs/{rid}/state"' in state_attrs(first.text) and "queued" in plain(first.text)
    assert c.post(f"/runs/{rid}/cancel", data={"csrf_token": token(c)}).status_code == 303
    ended = c.get(f"/runs/{rid}/state").text
    assert 'data-ended="true"' in state_attrs(ended) and "data-poll" not in ended
    assert "Failed: cancelled: cancelled by Grace Reviewer before it started" in plain(ended)


def test_the_state_fragment_needs_the_login_and_a_known_run(own):
    engine, url = own
    rid = to.dispatched(engine, fixed_plan=True)
    assert make_client(engine, url).get(f"/runs/{rid}/state").status_code == 303
    assert signed_in(engine, url).get("/runs/999999/state").status_code == 404


def test_the_script_asks_again_only_when_the_state_it_received_carries_an_address():
    """The script's rule, from its source: one timer, set only by `schedule`; `schedule` is called on start and after
    a fragment only when that fragment carries data-poll, and on a network error (the same address); on data-ended the
    page reloads and nothing is scheduled."""
    js = POLL_JS.read_text(encoding="utf-8")
    assert js.count("setTimeout") == 1 and js.count("setInterval") == 0
    assert re.search(r"function schedule\(url\) \{\s*window\.setTimeout\(", js)
    calls = re.findall(r"^.*schedule\((?!url\) \{).*$", js, re.M)
    assert len(calls) == 3, calls
    assert any("if (url) { schedule(url); }" in c for c in calls)        # start: only with an address
    assert any("if (again) { schedule(again); }" in c for c in calls)    # after a fragment: only with an address
    assert any(".catch(function () { schedule(url); })" in c for c in calls)  # a failed request: the same address
    ended = re.search(r'if \(next\.getAttribute\("data-ended"\) === "true"\) \{([^}]*)\}', js).group(1)
    assert "location.reload()" in ended and "return" in ended and "schedule" not in ended
    again = js.index('var again = next.getAttribute("data-poll");')
    assert js.index('getAttribute("data-ended")') < again  # an ended fragment never reaches the next schedule


def free_port() -> int:
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class WebProcess:
    """The web service as its own process (uvicorn, the image's command), on a database of its own."""

    PASSWORD = "test-password-not-a-secret"

    def __init__(self, database_url: str):
        import secrets
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = {**os.environ, "HYPOCURATE_ENV": "development", "HYPOCURATE_PASSWORD": self.PASSWORD,
               "SESSION_SECRET": secrets.token_hex(32), "DATABASE_URL": database_url}
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "hypocurate.web.main:app", "--host",
                                      "127.0.0.1", "--port", str(self.port), "--workers", "1"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=env)
        import httpx
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                if httpx.get(self.base + "/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        else:
            self.stop()
            raise AssertionError("the web process did not start")
        self.client = httpx.Client(base_url=self.base, follow_redirects=False, timeout=30)
        assert self.client.post("/login", data={"password": self.PASSWORD, "name": "Ada Reviewer"}).status_code == 303

    def state(self, rid: int) -> str:
        r = self.client.get(f"/runs/{rid}/state")
        assert r.status_code == 200
        return r.text

    def stop(self) -> int:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=30)
        if getattr(self, "client", None) is not None:
            self.client.close()
        return self.proc.returncode


def test_14_4_a_run_goes_on_to_its_end_across_a_restart_of_the_web_process(own, stub):
    """Criterion 14.4, bullets 1 and 3 (fix round 1, finding 4): the web service runs as its own process. A worker
    process works a fixed-plan run and is held at its model request (the Analyst's) by the stub. While it is held,
    the web process is stopped (its browser gone with it) and a new one is started. Then the worker is released.
    The run completes with the reference result, under one claim, with one model request: nothing was repeated."""
    import threading
    engine, url = own
    arrived, release = threading.Event(), threading.Event()

    def hold():
        arrived.set()
        release.wait(180)

    stub.respond(to.responder())
    stub.on_request(hold)
    rid = to.dispatched(engine, fixed_plan=True)
    first = WebProcess(url)
    worker = second = None
    try:
        assert "queued" in plain(first.state(rid))
        worker = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", "--once"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=dict(os.environ))
        assert arrived.wait(300), "the worker never reached its model request"
        held = plain(first.state(rid))
        assert "running" in held and run_view.STAGE_WORDS["analysis"] in held
        assert first.stop() is not None  # the web process is gone, while the run is mid-request
        with pytest.raises(Exception):
            import httpx
            httpx.get(first.base + "/health", timeout=2)
        second = WebProcess(url)  # the web service restarted: a new process, nothing carried over
        assert "running" in plain(second.state(rid))
        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
        release.set()
        out, err = worker.communicate(timeout=300)
        assert worker.returncode == 0, err[-3000:]
        deadline = time.time() + 60
        while time.time() < deadline and 'data-ended="true"' not in second.state(rid):
            time.sleep(0.5)
        page = plain(second.client.get(f"/runs/{rid}").text)
    finally:
        release.set()
        for web in (first, second):
            if web is not None:
                web.stop()
        if worker is not None and worker.poll() is None:
            worker.kill()
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    pooled = run_view.show(engine, rid)["results"][0]
    assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
    assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
    with engine.connect() as conn:
        claims = conn.execute(text("SELECT release_reason FROM run_claim WHERE run_id = :r"), dict(r=rid)).all()
    assert [c.release_reason for c in claims] == ["finished"]  # one claim
    assert len(stub.requests) == 1  # one model request: the Analyst's, never repeated
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1
    assert "Level 6 of 6: tested answer" in page
