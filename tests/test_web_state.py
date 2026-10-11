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


def test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart(own, stub):
    """Criterion 14.4, bullets 1 and 3: a worker works the run; one web app reads its state and is then dropped (the
    browser closed); a new app on the same database (the web service restarted) reads on until the run ends. The run
    completes with the reference result, worked by the worker alone; the web service wrote nothing."""
    engine, url = own
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    proc = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", "--once"], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=dict(os.environ))
    try:
        first = signed_in(engine, url)
        seen = {first.get(f"/runs/{rid}/state").status_code for _ in range(3)}
        assert seen == {200}
        del first  # the browser is closed
        second = signed_in(engine, url)  # the web service restarted: a new app, nothing carried over
        deadline = time.time() + 300
        while time.time() < deadline and "data-ended" not in second.get(f"/runs/{rid}/state").text:
            time.sleep(0.5)
        out, err = proc.communicate(timeout=300)
        assert proc.returncode == 0, err[-3000:]
    finally:
        if proc.poll() is None:
            proc.kill()
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    pooled = run_view.show(engine, rid)["results"][0]
    assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
    assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
    with engine.connect() as conn:
        claims = conn.execute(text("SELECT worker, release_reason FROM run_claim WHERE run_id = :r"), dict(r=rid)).all()
    assert len(claims) == 1 and claims[0].release_reason == "finished"
    page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
    assert "Level 6 of 6: tested answer" in page and "completed" in page
