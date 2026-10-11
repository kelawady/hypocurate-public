"""Step 10b, fix round 1 (ChatGPT's review of 2026-10-11, three findings accepted by the owner).

1. Act only on the version shown: review, return, dispatch, dispatch again and edit forms send the displayed version's
   id and a fingerprint of its content; the pipeline checks both under the version lock and refuses a stale submission
   ("This query has changed since you opened it; reload the page"). Two-session tests.
2. No formulas in exports: every text cell in the workbook is a string cell; in the CSV, text starting with =, +, -, @,
   tab or carriage return is neutralised, and numbers stay numbers.
3. Who did it: every write stores the signed-in name in `action_record` (migration 0009), in the same transaction;
   confirm and cancel too (owner's addition).
"""
from __future__ import annotations

import csv
import io
import re

import pytest
from openpyxl import load_workbook
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries, workbook
from stats_world import small_rows
from test_web_runs import plain, signed_in, token

STALE = "This query has changed since you opened it; reload the page"
ALICE, BOB = "Alice Reviewer", "Bob Editor"
CLAIM = to.FCC_CLAIM


@pytest.fixture
def own(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def shown(page: str) -> dict:
    """The version id and fingerprint a page's form carries."""
    return {"version_id": re.search(r'name="version_id" value="(\d+)"', page).group(1),
            "version_fingerprint": re.search(r'name="version_fingerprint" value="([0-9a-f]{64})"', page).group(1)}


def new_query(c, action="submit", claim=CLAIM, note=""):
    r = c.post("/queries", data={"csrf_token": token(c), "claim": claim, "sources": ["mpea", "tamu_fcc"],
                                 "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "note": note,
                                 "action": action})
    assert r.status_code == 303, plain(r.text)[:300]
    return r.headers["location"].rsplit("/", 1)[1]


def edit_form(claim=CLAIM, action="submit"):
    return {"claim": claim, "sources": ["mpea", "tamu_fcc"], "domain": "grain_size_strengthening",
            "sufficiency": "fixed_minimum", "note": "", "action": action}


# --- finding 1: act only on the version shown ------------------------------------------------------------------------

def test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2(own):
    engine, url = own
    alice, bob = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
    number = new_query(bob)
    seen_by_alice = shown(alice.get(f"/review/{number}").text)  # Alice opens version 1
    assert bob.post(f"/review/{number}/return", data={"csrf_token": token(bob), "comment": "narrow it",
                                                      **shown(bob.get(f"/review/{number}").text)}).status_code == 303
    assert bob.post(f"/queries/{number}/edit", data={"csrf_token": token(bob), **edit_form(CLAIM + " in tension"),
                                                     **shown(bob.get(f"/queries/{number}/edit").text)}).status_code == 303
    r = alice.post(f"/review/{number}/dispatch", data={"csrf_token": token(alice), "domain": "grain_size_strengthening",
                                                       **seen_by_alice})
    assert r.status_code == 409 and STALE in plain(r.text)
    assert one(engine, "SELECT count(*) FROM run") == 0  # version 2 was not dispatched
    r = alice.post(f"/review/{number}/return", data={"csrf_token": token(alice), "comment": "x", **seen_by_alice})
    assert r.status_code == 409 and STALE in plain(r.text)


def test_a_changed_version_is_refused_even_with_the_same_id(own):
    """The fingerprint covers the content: a draft edited in another tab after this one opened is refused."""
    engine, url = own
    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
    number = new_query(a, action="save")
    tab_a, tab_b = shown(a.get(f"/queries/{number}/edit").text), shown(b.get(f"/queries/{number}/edit").text)
    assert tab_a["version_id"] == tab_b["version_id"]
    assert a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("first edit", "save"),
                                                   **tab_a}).status_code == 303
    r = b.post(f"/queries/{number}/edit", data={"csrf_token": token(b), **edit_form("second edit", "save"), **tab_b})
    assert r.status_code == 409 and STALE in plain(r.text)
    assert one(engine, "SELECT v.text FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
                       "h.number = :n", n=number) == "first edit"  # never overwritten by the older form


def test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version(own):
    engine, url = own
    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
    number = new_query(a)
    a.post(f"/review/{number}/return", data={"csrf_token": token(a), "comment": "edit", **shown(a.get(f"/review/{number}").text)})
    tab_a, tab_b = shown(a.get(f"/queries/{number}/edit").text), shown(b.get(f"/queries/{number}/edit").text)
    assert a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("v2 by Alice", "save"),
                                                   **tab_a}).status_code == 303
    r = b.post(f"/queries/{number}/edit", data={"csrf_token": token(b), **edit_form("v2 by Bob", "save"), **tab_b})
    assert r.status_code == 409 and STALE in plain(r.text)
    assert one(engine, "SELECT count(*) FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
                       "h.number = :n", n=number) == 2


def test_a_form_without_the_version_it_showed_is_refused(own):
    engine, url = own
    c = signed_in(engine, url, ALICE)
    number = new_query(c)
    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
    assert r.status_code == 409 and STALE in plain(r.text) and one(engine, "SELECT count(*) FROM run") == 0
    draft = new_query(c, action="save")
    r = c.post(f"/queries/{draft}/edit", data={"csrf_token": token(c), **edit_form("no version sent", "save")})
    assert r.status_code == 409 and STALE in plain(r.text)
    assert one(engine, "SELECT v.text FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
                       "h.number = :n", n=draft) == CLAIM
    r = c.post(f"/queries/{draft}/edit", data={"csrf_token": token(c), **edit_form("a forged id", "save"),
                                               "version_id": "1", "version_fingerprint": "0" * 64})
    assert r.status_code == 409 and STALE in plain(r.text)


def test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock(own):
    engine, _ = own
    q = queries.create(engine, CLAIM, ["mpea"], by=ALICE)
    queries.submit(engine, q.version_id, by=ALICE)
    fp = queries.version_fingerprint(engine, q.version_id)
    queries.return_for_edits(engine, q.version_id, by=BOB, comment="x", expected_fingerprint=fp)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, q.version_id, by=ALICE, expected_fingerprint=fp)
    assert refused.value.code == "stale" and refused.value.reason == STALE


# --- finding 2: no formulas in exports -------------------------------------------------------------------------------

FORMULA = "=1+1"


def planted_run(engine, stub):
    """A completed run whose stored text begins with formula signs: the hypothesis, a paper reference (MPEA title),
    the note, the names, and the Analyst's text."""
    starts = ("=", "+", "-", "@", "=", "+")
    rows = [{**r, "REFERENCE: title": f"{starts[i]}1+1 title {i}"} for i, r in enumerate(small_rows(3, papers=3))]
    pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
    stub.respond(to.responder(analyst=lambda raw: "+Plain text {outcome_wording}."))
    q = queries.create(engine, f"{FORMULA} yield strength rises as grain size falls", ["mpea"], note="@note", by="-Mallory")
    queries.submit(engine, q.version_id, by="-Mallory")
    queries.confirm_domain(engine, q.version_id, by="=Eve")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, by="=Eve")
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "completed"
    return rid


def test_every_text_cell_of_the_workbook_is_a_string_cell(migrated_database, stub):
    engine = make_engine(migrated_database)
    try:
        rid = planted_run(engine, stub)
        wb = load_workbook(io.BytesIO(workbook.build(engine, rid)))
        texts = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
        assert texts and all(c.data_type == "s" for c in texts), [c.coordinate for c in texts if c.data_type != "s"]
        values = {c.value for c in texts}
        assert f"{FORMULA} yield strength rises as grain size falls" in values  # kept as written, as a string
        assert {"=1+1 title 0", "+1+1 title 1", "-1+1 title 2", "@1+1 title 3"} <= values and "@note" in values
        assert any(v.startswith("=Eve, ") for v in values) and any(v.startswith("-Mallory, ") for v in values)  # names
        assert any("+Plain text" in v for v in values)  # the Analyst's text
        numbers = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row
                   if isinstance(c.value, (int, float)) and not isinstance(c.value, bool)]
        assert numbers and all(c.data_type == "n" for c in numbers)  # numbers stay numbers
    finally:
        engine.dispose()


def test_the_csv_neutralises_formula_text_and_keeps_numbers(migrated_database, stub):
    engine = make_engine(migrated_database)
    try:
        rid = planted_run(engine, stub)
        rows = list(csv.reader(io.StringIO(workbook.records_csv(engine, rid))))
        cells = [c for r in rows[1:] for c in r]
        assert not [c for c in cells if c[:1] in ("=", "+", "-", "@", "\t", "\r")]
        for i, start in enumerate(("=", "+", "-", "@")):
            assert f"'{start}1+1 title {i}" in cells
        header = rows[1]
        assert re.fullmatch(r"-?\d+(\.\d+)?", rows[2][header.index("grain_size")])  # a number, unchanged
    finally:
        engine.dispose()


# --- finding 3: who did it -------------------------------------------------------------------------------------------

def actions(engine):
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(text(
            "SELECT action, actor, hypothesis_version_id IS NOT NULL, run_id IS NOT NULL, source_version_id IS NOT NULL "
            "FROM action_record ORDER BY id")).all()]


def test_every_website_write_stores_the_signed_in_name(own, stub):
    engine, url = own
    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
    number = new_query(a, action="save")                                            # create
    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("edited", "save"),
                                            **shown(a.get(f"/queries/{number}/edit").text)})  # edit
    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("edited", "submit"),
                                            **shown(a.get(f"/queries/{number}/edit").text)})  # edit, submit
    b.post(f"/review/{number}/return", data={"csrf_token": token(b), "comment": "x",
                                             **shown(b.get(f"/review/{number}").text)})       # return
    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("v2", "submit"),
                                            **shown(a.get(f"/queries/{number}/edit").text)})  # new version, submit
    r = b.post(f"/review/{number}/dispatch", data={"csrf_token": token(b), "domain": "grain_size_strengthening",
                                                   **shown(b.get(f"/review/{number}").text)})  # confirm domain, dispatch
    rid = int(r.headers["location"].rsplit("/", 1)[1])
    b.post(f"/runs/{rid}/cancel", data={"csrf_token": token(b)})                      # cancel
    b.post(f"/queries/{number}/again", data={"csrf_token": token(b), **shown(b.get(f"/queries/{number}").text)})
    rows = actions(engine)
    assert rows[:2] == [("register_source", None, False, False, True)] * 2  # the fixture's, at the command line, unnamed
    got = [(x[0], x[1]) for x in rows[2:]]
    assert got == [("create", ALICE), ("edit", ALICE), ("edit", ALICE), ("submit", ALICE), ("return", BOB),
                   ("new_version", ALICE), ("submit", ALICE), ("confirm_domain", BOB), ("dispatch", BOB),
                   ("cancel", BOB), ("dispatch_again", BOB)], got


def test_registering_a_source_and_confirming_a_run_store_the_name(migrated_database, stub):
    e = make_engine(migrated_database)
    try:
        pw.registered(e, ("mpea",))
        c = signed_in(e, migrated_database, ALICE)
        assert c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)}).status_code == 200
        assert actions(e)[-1] == ("register_source", ALICE, False, False, True)
        stub.respond(to.responder(to.planner_body()))
        rid = to.dispatched(e)
        assert orchestrator.run(e, rid, client_options=sp.client_options(stub)).status == "waiting"
        page = c.get(f"/runs/{rid}/confirm").text
        fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
        assert c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp}).status_code == 303
        assert actions(e)[-1] == ("confirm_rules", ALICE, False, True, False)
        # The confirmation's own record is unchanged (owner): the name is in rules_confirmation as before.
        assert one(e, "SELECT confirmed_by FROM rules_confirmation WHERE run_id = :r", r=rid) == ALICE
    finally:
        e.dispose()


def test_action_records_are_append_only(own):
    from sqlalchemy.exc import IntegrityError, InternalError
    engine, _ = own
    queries.create(engine, CLAIM, ["mpea"], by=ALICE)
    for sql in ("UPDATE action_record SET actor = 'someone else'", "DELETE FROM action_record"):
        with pytest.raises((IntegrityError, InternalError)):
            with engine.begin() as conn:
                conn.execute(text(sql))
    assert actions(engine)[-1][:2] == ("create", ALICE)  # unchanged


def test_every_formula_sign_is_neutralised_in_a_csv_cell_and_numbers_are_kept():
    assert workbook.FORMULA_STARTS == ("=", "+", "-", "@", "\t", "\r")
    for start in workbook.FORMULA_STARTS:
        assert workbook.csv_cell(f"{start}1+1") == f"'{start}1+1"
    for number in (-5.0, 12, 0.5, "-5", "+1e3", "-0.25"):
        assert workbook.csv_cell(number) == number
    assert workbook.csv_cell("plain text") == "plain text" and workbook.csv_cell(None) is None
