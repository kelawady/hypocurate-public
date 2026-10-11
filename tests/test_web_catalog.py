"""Step 10b: the Critic's flags on the run page (with their advice label), the data sources page with registration and
"Test connection and show sample records" (PRD 9.6; registration is a safeguard write, with the CSRF token), and the
read-only agent pages with their "Fixed in code" panel (PRD 9.5)."""
from __future__ import annotations

import re

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_critic as tc
from hypocurate.access.allowlist import ALLOWED, FIELDS
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import catalog_view
from hypocurate.pipeline.agents import analyst, critic, planner
from test_web_runs import plain, signed_in, token

NAME = "Grace Reviewer"


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def bare(migrated_database):
    """A database with only MPEA registered (so other sources defined in code are not registered yet)."""
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea",))
    yield e, migrated_database
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


# --- the Critic's flags ---------------------------------------------------------------------------------------------

def test_the_run_page_shows_each_flag_and_the_critics_class_under_its_advice_label(migrated_database, stub):
    e = make_engine(migrated_database)
    try:
        pw.registered_files(e, {"mpea": pw.mpea_csv(tc.small_rows(3, papers=3) + tc.CONFLICT + [tc.PAIR_SAME,
                                                                                               tc.PAIR_MPEA]),
                                "controlled_duplicates": pw.mpea_csv([tc.PAIR_SAME, tc.PAIR_OTHER])})
        rid = tc.checked_run(e, tc.version(e))
        multi = tc.multi_flag_ids(e, rid)
        stub.respond(lambda raw: tc.reply({str(f): {"class": "same_measurement", "reason": "same paper and alloy"}
                                           for f in multi}))
        tc.run_critic(e, rid, stub)
        page = plain(signed_in(e, migrated_database).get(f"/runs/{rid}").text)
        assert "Flags raised by code" in page
        assert page.count(f"same measurement reported twice: same paper and alloy {critic.ADVICE_LABEL}") == len(multi)
        assert "not classified: single-record flag" in page
    finally:
        e.dispose()


# --- data sources ---------------------------------------------------------------------------------------------------

def test_the_sources_page_lists_each_source_with_its_facts_and_the_unregistered_ones(bare):
    engine, url = bare
    page = plain(signed_in(engine, url).get("/sources").text)
    assert "MPEA dataset (Borg et al. 2020)" in page and "measured" in page and "available" in page
    assert "Defined in code, not registered yet" in page and "Texas A&M FCC dataset" in page
    assert f"Register as {NAME}" in page  # the button names the signed-in person


def test_registering_a_source_from_the_website_records_it_and_names_the_person(bare):
    engine, url = bare
    c = signed_in(engine, url, NAME)
    r = c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)})
    assert r.status_code == 200 and f"tamu_fcc registered by {NAME}: version" in plain(r.text)
    assert one(engine, "SELECT count(*) FROM source WHERE key = 'tamu_fcc'") == 1
    assert one(engine, "SELECT count(*) FROM source_version sv JOIN source s ON s.id = sv.source_id WHERE "
                       "s.key = 'tamu_fcc' AND sv.sealed_at IS NOT NULL") >= 1
    again = c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)})
    assert "was already registered with this version" in plain(again.text)


@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
def test_registration_without_the_sessions_token_is_refused_and_writes_nothing(bare, sent):
    engine, url = bare
    c = signed_in(engine, url, NAME)
    before = (one(engine, "SELECT count(*) FROM source"), one(engine, "SELECT count(*) FROM source_version"))
    data = {} if sent is None else {"csrf_token": sent}
    assert c.post("/sources/tamu_fcc/register", data=data).status_code == 403
    assert (one(engine, "SELECT count(*) FROM source"), one(engine, "SELECT count(*) FROM source_version")) == before


def test_an_unknown_source_is_refused_with_the_reason(bare):
    engine, url = bare
    c = signed_in(engine, url, NAME)
    r = c.post("/sources/no_such_source/register", data={"csrf_token": token(c)})
    assert r.status_code == 409 and "Not registered: unknown source" in plain(r.text)


def test_the_connection_test_shows_sample_records_and_writes_nothing(bare):
    engine, url = bare
    tables = ("source", "source_version", "record", "audit_log")
    before = [one(engine, f"SELECT count(*) FROM {t}") for t in tables]
    page = plain(signed_in(engine, url).get("/sources/mpea/test").text)
    assert "Connection test: mpea" in page and "records read" in page
    assert [one(engine, f"SELECT count(*) FROM {t}") for t in tables] == before
    assert "Connection test not done for tamu_fcc" in plain(signed_in(engine, url).get("/sources/tamu_fcc/test").text)


# --- agents ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["planner", "curator", "critic", "analyst", "commentator"])
def test_each_agent_page_shows_exactly_what_the_access_layer_lets_the_role_receive(bare, role):
    engine, url = bare
    page = signed_in(engine, url).get(f"/agents/{role}").text
    receives = plain(page.split("<h3>Receives</h3>", 1)[1].split("<h3>Returns</h3>", 1)[0])
    expected = {f for fields in (ALLOWED.get(role) or {}).values() for f in fields}
    shown = set(re.findall(r"<strong>([a-z ]+)</strong>: ", page.split("<h3>Receives</h3>", 1)[1]
                           .split("<h3>Returns</h3>", 1)[0]))
    assert shown == {f.replace("_", " ") for f in expected}
    for f in expected:
        assert " ".join(FIELDS[f].split()) in receives
    if not expected:
        assert "Nothing, at any stage." in receives
    assert catalog_view.MAY_CALL in plain(page) and catalog_view.MAY_NOT[role] in plain(page)


def test_each_agent_page_says_what_the_role_returns_from_the_roles_own_description(bare):
    engine, url = bare
    c = signed_in(engine, url)
    for role, module in (("planner", planner), ("critic", critic), ("analyst", analyst)):
        assert " ".join(module.OUTPUT_DESCRIPTION.split()) in plain(c.get(f"/agents/{role}").text), role
    assert c.get("/agents/nobody").status_code == 404
    assert c.get("/agents").headers["location"] == "/agents/planner"
