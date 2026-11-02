"""Midway submission (owner's brief and approval of 2026-11-02): leftover labels taken off the screens.

The home page no longer names a build step, and the run page's header no longer shows the agent mode. The agent mode
stays a stored column and a row of the workbook's run summary (owner's answer: a factual record, not a screen label).
"""
from __future__ import annotations

import pytest

import pipeline_world as pw
import stub_provider as sp
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import workbook
from test_web_runs import completed, plain, signed_in
from test_workbook import items, sheets


@pytest.fixture(scope="module")
def world(admin, database_url, template_database):
    """One completed fixed-plan run (the 14.1a reference), only read."""
    name = _create(admin, "hypocurate_t", template=template_database)
    url = url_for(database_url, name)
    engine = make_engine(url)
    stub = sp.StubProvider()
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        yield engine, url, {"sufficient": completed(engine, stub)}
    finally:
        stub.close()
        engine.dispose()
        _drop(admin, name)


# --- C: leftover labels ----------------------------------------------------------------------------------------------

def test_the_home_page_names_no_build_step_and_keeps_its_links(world):
    engine, url, _ = world
    page = signed_in(engine, url).get("/").text
    assert "step 10" not in plain(page).lower()
    for link in ('href="/queries"', 'href="/runs"', 'href="/help"', 'href="/assumptions"'):
        assert link in page


def test_the_run_page_header_shows_no_agent_mode(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    assert "agent mode" not in page.lower()
    assert "four roles" not in page.lower()


def test_the_workbook_still_records_the_agent_mode(world):
    engine, _, runs = world
    summary = items(sheets(workbook.build(engine, runs["sufficient"]))["Run summary"])
    assert summary["Agent mode"] == "four roles"
