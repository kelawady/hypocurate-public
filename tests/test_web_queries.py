"""Step 10b: the query pages (PRD 9.1 to 9.3; owner's go of 2026-10-11).

New query (save draft, submit), the queries list (an ID cursor, as the runs list), one query with its versions,
editing (a draft in place; a returned query as its next version, PRD 9.2), review and dispatch (the domain confirmed
under the signed-in name; return for edits with a comment; the refusals in code's words: the monthly cap, constructed
test data, a domain not yet supported), dispatch again, and a CSRF token on every write. The web service only writes
through `pipeline.queries`; a dispatched run waits for a worker.
"""
from __future__ import annotations

import re
from decimal import Decimal

import pytest
from sqlalchemy import text

import pipeline_world as pw
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries, query_view
from hypocurate.pipeline.agents import spend
from test_queries_step9a import _spend_this_month
from test_web_runs import plain, signed_in, token

CLAIM = to.FCC_CLAIM
NAME = "Grace Reviewer"


@pytest.fixture
def own(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def new_query(c, action="save", claim=CLAIM, sources=("mpea", "tamu_fcc"), domain="grain_size_strengthening",
              sufficiency="fixed_minimum", note=""):
    r = c.post("/queries", data={"csrf_token": token(c), "claim": claim, "sources": list(sources), "domain": domain,
                                 "sufficiency": sufficiency, "note": note, "action": action})
    assert r.status_code == 303, plain(r.text)[:400]
    return r.headers["location"].rsplit("/", 1)[1]


def latest(engine, number):
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT v.version_number, v.status, v.text, v.note, v.review_comment, d.key AS domain, "
            "cd.key AS confirmed_domain FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
            "JOIN domain d ON d.id = v.domain_id LEFT JOIN domain cd ON cd.id = v.confirmed_domain_id "
            "WHERE h.number = :n ORDER BY v.version_number DESC LIMIT 1"), dict(n=number)).one()


# --- the flow -----------------------------------------------------------------------------------------------------

def test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_signed_in_name(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, note="please check the band")
    v = latest(engine, number)
    assert (v.version_number, v.status, v.text, v.note) == (1, "draft", CLAIM, "please check the band")
    assert "Edit the draft" in plain(c.get(f"/queries/{number}").text)
    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " (edited)",
                                                "sources": ["mpea"], "domain": "grain_size_strengthening",
                                                "sufficiency": "use_available", "note": "", "action": "submit"})
    assert r.status_code == 303
    v = latest(engine, number)
    assert (v.version_number, v.status, v.text) == (1, "submitted", CLAIM + " (edited)")  # a draft is edited in place
    page = plain(c.get(f"/review/{number}").text)
    assert f"{number} · version 1" in page and "Dispatching as Grace Reviewer" in page
    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening",
                                                  "ceiling": "0.40"})
    assert r.status_code == 303 and r.headers["location"].startswith("/runs/")
    rid = int(r.headers["location"].rsplit("/", 1)[1])
    v = latest(engine, number)
    assert v.status == "dispatched" and v.confirmed_domain == "grain_size_strengthening"
    assert v.review_comment == f"domain confirmed on the website by {NAME}"
    # The web service runs nothing: the run is queued for a worker, with the ceiling given.
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("0.40")
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == 0


def test_a_returned_query_is_edited_as_its_next_version_and_the_returned_one_is_kept(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit")
    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "name the test type"})
    assert r.status_code == 303
    v = latest(engine, number)
    assert v.status == "returned" and v.review_comment == f"returned by {NAME}: name the test type"
    form = plain(c.get(f"/queries/{number}/edit").text)
    assert "Saving creates version 2; version 1 is kept unchanged" in form
    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " in tension",
                                                "sources": ["mpea", "tamu_fcc"], "domain": "grain_size_strengthening",
                                                "sufficiency": "fixed_minimum", "note": "", "action": "save"})
    assert r.status_code == 303
    v = latest(engine, number)
    assert (v.version_number, v.status, v.text) == (2, "draft", CLAIM + " in tension")
    with engine.connect() as conn:
        first = conn.execute(text("SELECT v.status, v.text FROM hypothesis h JOIN hypothesis_version v ON "
                                  "v.hypothesis_id = h.id WHERE h.number = :n AND v.version_number = 1"),
                             dict(n=number)).one()
    assert tuple(first) == ("returned", CLAIM)


def test_return_needs_a_comment(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit")
    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "  "})
    assert r.status_code == 409 and "say what to change" in plain(r.text)
    assert latest(engine, number).status == "submitted"


def test_dispatch_again_makes_a_new_run_once_the_last_one_ended(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit")
    first = int(c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c),
                                                          "domain": "grain_size_strengthening"}).headers["location"]
                .rsplit("/", 1)[1])
    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
    assert r.status_code == 409 and queries.REASONS["already_open"] in plain(r.text)  # the first run is still open
    queries.cancel(engine, first, by=NAME)
    assert "Dispatch again" in plain(c.get(f"/queries/{number}").text)
    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
    assert r.status_code == 303 and int(r.headers["location"].rsplit("/", 1)[1]) > first


# --- the refusals, in code's words ---------------------------------------------------------------------------------

def test_dispatch_at_the_monthly_cap_is_refused_with_the_owners_words(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit")
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
    assert r.status_code == 409 and queries.REASONS["month_cap_reached"] in plain(r.text)
    assert latest(engine, number).status == "submitted"


def test_dispatch_of_constructed_test_data_is_refused_with_its_reason(own):
    engine, url = own
    pw.registered(engine, ("controlled_duplicates",))
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit", sources=("mpea", "controlled_duplicates"))
    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
    assert r.status_code == 409
    assert queries.REASONS["constructed_source_unmarked"].format(source="controlled_duplicates") in plain(r.text)


def test_a_domain_not_yet_supported_cannot_be_dispatched_and_the_message_says_why(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit", domain="fatigue")
    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "fatigue"})
    assert r.status_code == 409 and "the confirmed domain is not supported yet" in plain(r.text)
    assert one(engine, "SELECT count(*) FROM run") == 0


def test_a_new_query_without_a_claim_or_a_source_is_refused_and_kept_on_the_form(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    r = c.post("/queries", data={"csrf_token": token(c), "claim": " ", "sources": ["mpea"],
                                 "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "action": "save"})
    assert r.status_code == 409 and "state the hypothesis" in plain(r.text)
    r = c.post("/queries", data={"csrf_token": token(c), "claim": CLAIM, "domain": "grain_size_strengthening",
                                 "sufficiency": "fixed_minimum", "action": "save"})
    assert r.status_code == 409 and "chooses at least one source" in plain(r.text) and CLAIM in r.text
    assert one(engine, "SELECT count(*) FROM hypothesis") == 0


# --- CSRF on every write --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("route", ["/queries", "/queries/{n}/edit", "/queries/{n}/again", "/review/{n}/dispatch",
                                   "/review/{n}/return"])
@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
def test_every_query_write_refuses_a_request_without_the_sessions_token(own, route, sent):
    engine, url = own
    c = signed_in(engine, url, NAME)
    number = new_query(c, action="submit")
    before = (one(engine, "SELECT count(*) FROM hypothesis"), one(engine, "SELECT count(*) FROM hypothesis_version"),
              one(engine, "SELECT count(*) FROM run"), latest(engine, number).status)
    data = {"claim": CLAIM, "sources": ["mpea"], "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum",
            "comment": "x", "action": "save", **({} if sent is None else {"csrf_token": sent})}
    assert c.post(route.format(n=number), data=data).status_code == 403
    after = (one(engine, "SELECT count(*) FROM hypothesis"), one(engine, "SELECT count(*) FROM hypothesis_version"),
             one(engine, "SELECT count(*) FROM run"), latest(engine, number).status)
    assert after == before


# --- the list -------------------------------------------------------------------------------------------------------

def test_the_queries_list_goes_through_every_query_once_while_queries_are_added(own):
    engine, url = own
    old = queries.create(engine, "An old draft", ["mpea"]).number
    existing = [old] + [queries.create(engine, f"Claim {i}", ["mpea"]).number
                        for i in range(query_view.QUERIES_PER_PAGE + 20)]
    c = signed_in(engine, url, NAME)
    order, address = [], "/queries"
    while address:
        page = c.get(address)
        assert page.status_code == 200
        order += re.findall(r'<td data-label="Query"><a href="/queries/(Q-\d+)"', page.text)
        nxt = re.search(r'<a [^>]*rel="next"[^>]*href="([^"]+)"', page.text)
        address = nxt.group(1) if nxt else None
        for i in range(query_view.QUERIES_PER_PAGE):
            queries.create(engine, f"Added {i}", ["mpea"])
    seen = [n for n in order if n in set(existing)]
    assert seen == sorted(existing, key=lambda n: int(n[2:]), reverse=True) and seen[-1] == old
    assert len(seen) == len(set(seen))


def test_the_list_shows_each_querys_status_and_the_action_the_prd_names(own):
    engine, url = own
    c = signed_in(engine, url, NAME)
    draft = new_query(c)
    submitted = new_query(c, action="submit")
    page = c.get("/queries").text
    assert f'href="/queries/{draft}/edit">Edit</a>' in page and f'href="/review/{submitted}">Review</a>' in page
    assert "draft" in plain(page) and "submitted for review" in plain(page)


# --- the functions --------------------------------------------------------------------------------------------------

def test_only_a_draft_is_edited_in_place_and_only_a_returned_query_gets_a_new_version(own):
    engine, _ = own
    q = queries.create(engine, CLAIM, ["mpea"])
    with pytest.raises(queries.QueryRefused) as refused:
        queries.new_version(engine, q.number, CLAIM, ["mpea"], "grain_size_strengthening", "fixed_minimum", None)
    assert refused.value.code == "not_returned"
    queries.submit(engine, q.version_id)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.update_draft(engine, q.number, CLAIM, ["mpea"], "grain_size_strengthening", "fixed_minimum", None)
    assert refused.value.code == "not_a_draft"
    with pytest.raises(queries.QueryRefused) as refused:
        queries.return_for_edits(engine, q.version_id, by="", comment="x")
    assert refused.value.code == "reviewer_missing"
