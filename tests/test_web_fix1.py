"""Step 10a, fix round 1 (ChatGPT's review of 2026-10-11, findings 1 to 3, accepted by the owner).

1. The confirmation page's fingerprint covers the text it showed, not only the content: a renderer changed between
   display and submission is refused.
2. The run page is built from one database snapshot: a run that completes while the page is being read is shown
   whole in one state, never as completed with the earlier missing statement.
3. The runs list has pages, so every run stays reachable however many newer runs there are.
"""
from __future__ import annotations

import re

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries, reading, run_view
from test_web_runs import plain, signed_in, token


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def own(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def waiting(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
    return rid


# --- finding 1 ----------------------------------------------------------------------------------------------------

def test_finding_1_a_page_confirmed_after_the_renderer_changed_is_refused(own, stub, monkeypatch):
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    page = c.get(f"/runs/{rid}/confirm").text
    fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
    assert "10 informative groups" in plain(page)
    original = confirmation.render  # a deploy between showing and confirming changes only the wording
    monkeypatch.setattr(confirmation, "render",
                        lambda content: original(content).replace("informative groups", "independent groups"))
    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
    assert r.status_code == 409 and "show it again before confirming" in plain(r.text)
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0


# --- finding 2 ----------------------------------------------------------------------------------------------------

def test_finding_2_a_run_that_completes_while_its_page_is_read_is_shown_in_one_state(own, stub, monkeypatch):
    """The run is queued when the page starts reading; the worker completes it in the middle of the reads (here,
    during the question-as-tested read). The page shows one state throughout: the queued run, still polling."""
    engine, url = own
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    original, done = reading.stored, []

    def completing(conn, run_id):
        if not done:
            done.append(True)
            assert to.run(engine, rid, stub).status == "completed"  # committed by other connections
        return original(conn, run_id)

    monkeypatch.setattr(reading, "stored", completing)
    page = run_view.run_page(engine, rid)
    assert done, "the run did not complete during the page's reads"
    assert page["status"] == "queued" and page["open"] is True
    assert page["statement"]["body"] == [] and page["evidence"]["level"] is None and page["outcome"] is None
    after = run_view.run_page(engine, rid)  # the next read: completed, whole
    assert after["status"] == "completed" and after["open"] is False and after["statement"]["body"]
    assert after["evidence"]["level"] == 6 and after["outcome"] == "sufficient in the sources searched"


def test_finding_2_the_state_fragment_of_such_a_run_keeps_polling(own, stub, monkeypatch):
    engine, url = own
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    c = signed_in(engine, url)
    original, done = reading.stored, []

    def completing(conn, run_id):
        if not done:
            done.append(True)
            assert to.run(engine, rid, stub).status == "completed"
        return original(conn, run_id)

    monkeypatch.setattr(reading, "stored", completing)
    fragment = c.get(f"/runs/{rid}/state").text
    assert done and f'data-poll="/runs/{rid}/state"' in fragment  # the next poll sees it ended
    monkeypatch.setattr(reading, "stored", original)
    assert 'data-ended="true"' in c.get(f"/runs/{rid}/state").text


# --- finding 3 ----------------------------------------------------------------------------------------------------

def test_finding_3_an_old_waiting_run_stays_reachable_through_the_runs_list(own, stub):
    """Over 200 newer runs (the old list's limit): the oldest run, waiting for a confirmation, is found by following
    the list's pages and opens."""
    engine, url = own
    old = waiting(engine, stub)
    newer = [to.dispatched(engine, fixed_plan=True) for _ in range(205)]
    c = signed_in(engine, url)
    seen, address, pages = set(), "/runs", 0
    while address and pages < 50:
        page = c.get(address)
        assert page.status_code == 200
        seen |= {int(x) for x in re.findall(r'href="/runs/(\d+)"', page.text)}
        nxt = re.search(r'<a [^>]*rel="next"[^>]*href="([^"]+)"|<a [^>]*href="([^"]+)"[^>]*rel="next"', page.text)
        address = (nxt.group(1) or nxt.group(2)).replace("&amp;", "&") if nxt else None
        pages += 1
    assert seen == {old, *newer}, f"unreachable: {sorted({old, *newer} - seen)[:5]}"
    assert pages > 1
    opened = plain(c.get(f"/runs/{old}").text)
    assert "waiting at the rules lock" in opened and "Review and confirm the question as tested" in opened


def test_finding_3_the_list_says_which_runs_a_page_shows(own):
    engine, url = own
    for _ in range(run_view.RUNS_PER_PAGE + 3):
        to.dispatched(engine, fixed_plan=True)
    c = signed_in(engine, url)
    total = run_view.RUNS_PER_PAGE + 3
    assert f"Runs 1 to {run_view.RUNS_PER_PAGE} of {total}, newest first." in plain(c.get("/runs").text)
    assert f"Runs {run_view.RUNS_PER_PAGE + 1} to {total} of {total}, newest first." in plain(c.get("/runs?page=2").text)
    assert c.get("/runs?page=0").status_code == 404 and c.get("/runs?page=99").status_code == 404
