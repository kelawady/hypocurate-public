"""Step 10a: the run pages (owner's step 10 brief and approval of 2026-10-11, with additions 1 to 3 and 6).

The run viewer (code's statement first, then the Analyst's text under its label, per-source results, sensitivity sets
by display name, cautions, cost), the evidence dial, the confirmation of the question as tested by the signed-in
person (the same content and function as the command line's `confirm`, with the shown content's fingerprint sent
back), cancel, the name fixed for the session, and CSRF tokens on every write.

One database per module holds the runs that are only read; every test that writes builds its own waiting run on a
database of its own. Every model call goes to the local stub (as tests/test_orchestrator.py).
"""
from __future__ import annotations

import base64
import html
import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from conftest import _create, _drop, url_for
from hypocurate.config import Settings
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries, run_view
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, SENSITIVITY_CHANGES
from hypocurate.web import dial, security
from hypocurate.web.app import SESSION_COOKIE, create_app

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
NAME = "Grace Reviewer"


def make_client(engine, url):
    s = Settings(env="development", database_url=url, password=PASSWORD, session_secret=SECRET, version="test")
    return TestClient(create_app(s, engine=engine), base_url="http://testserver", follow_redirects=False)


def signed_in(engine, url, name=NAME):
    c = make_client(engine, url)
    assert c.post("/login", data={"password": PASSWORD, "name": name}).status_code == 303
    return c


def session(c) -> dict:
    payload = c.cookies[SESSION_COOKIE].split(".")[0]
    return json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4)))


def token(c) -> str:
    return session(c)["csrf"]


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def plain(page: str) -> str:
    """The page's visible text, tags removed and entities decoded, whitespace collapsed; a superscript is read back
    as "^" (the screens write exponents as superscripts; the stored text has "^")."""
    page = page.replace("<sup>", "^").replace("</sup>", "")
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page)).split())


def completed(engine, stub, claim=to.FCC_CLAIM, fixed_plan=True, marked=False):
    stub.respond(to.responder(to.BCC if claim == to.BCC_CLAIM else None))
    q = queries.create(engine, claim, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan, constructed_test_data=marked)
    assert to.run(engine, rid, stub).status == "completed"
    return rid


def waiting(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
    return rid


@pytest.fixture(scope="module")
def world(admin, database_url, template_database):
    """Runs that are only read: the 14.1a fixed-plan run, the BCC claim (insufficient), a marked test run, a waiting
    Planner run, a queued run and a cancelled one."""
    name = _create(admin, "hypocurate_t", template=template_database)
    url = url_for(database_url, name)
    engine = make_engine(url)
    stub = sp.StubProvider()
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        runs = {"sufficient": completed(engine, stub), "insufficient": completed(engine, stub, to.BCC_CLAIM, False),
                "test_run": completed(engine, stub, marked=True), "waiting": waiting(engine, stub),
                "queued": to.dispatched(engine, fixed_plan=True), "cancelled": to.dispatched(engine, fixed_plan=True)}
        queries.cancel(engine, runs["cancelled"], by="Ada Reviewer")
        yield engine, url, runs
    finally:
        stub.close()
        engine.dispose()
        _drop(admin, name)


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def own(migrated_database):
    """A database of its own, for a test that writes."""
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


# --- the run viewer --------------------------------------------------------------------------------------------------

def test_the_run_viewer_shows_codes_statement_first_then_the_analysts_text_then_sources_sets_cautions_and_cost(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    lines = run_view.show(engine, runs["sufficient"])["statement"]
    first_line = next(x for x in lines if x.startswith("Outcome:"))
    order = [first_line, "Explanation by the Analyst", "written by a language model; values inserted from the run "
             "record; narrative not verified", "Each source alone, and all together", "Sensitivity sets", "Cautions",
             "Tokens and cost"]
    at = [page.index(x) for x in order]
    assert at == sorted(at), dict(zip(order, at))


def test_every_line_of_codes_statement_is_on_the_page_unchanged(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    for line in run_view.show(engine, runs["sufficient"])["statement"]:
        assert " ".join(line.split()) in page, line


def test_the_reference_numbers_are_shown_as_code_formatted_them(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    assert "424.9 MPa·µm^0.5 ± 64.4 MPa·µm^0.5 (one standard error)" in page
    assert "424.1 MPa·µm^0.5 ± 62.2 MPa·µm^0.5" in page
    assert "1173.3 MPa·µm^0.5; coefficient only (insufficient groups): no uncertainty, no p-value" in page


def test_sensitivity_sets_are_shown_by_display_name_never_by_internal_name(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    assert INFLUENCE_DISPLAY_NAME in plain(page)
    for key in [*SENSITIVITY_CHANGES, "primary"]:
        assert key not in page, key
    for key, name in run_view.SET_DISPLAY_NAMES.items():
        if key != "primary":
            assert html.escape(name) in page, name


def test_the_dial_shows_the_level_and_label_with_the_verdict_beside_it_not_in_it(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    svg = re.search(r'<svg class="dial dial-large".*?</svg>', page, re.S).group(0)
    assert "Level 6 of 6: tested answer" in plain(page)
    assert "Verdict: supported under the stated model, in the sources searched" in plain(page)
    assert "supported" not in svg and "<text" not in svg
    assert svg.count('class="seg seg-') == 6 and 'class="seg seg-6 current"' in svg and "hatch" not in svg


def test_an_insufficient_run_shows_no_verdict_and_level_1(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['insufficient']}").text)
    assert "No verdict" in page and "Verdict:" not in page
    assert "Level 1 of 6: nothing tested" in page
    assert "insufficient in the sources searched" in page
    assert "do not exist" not in page


def test_a_marked_test_runs_dial_is_hatched_with_a_badge(world):
    engine, url, runs = world
    c = signed_in(engine, url)
    page = c.get(f"/runs/{runs['test_run']}").text
    svg = re.search(r'<svg class="dial dial-large".*?</svg>', page, re.S).group(0)
    assert "<pattern id=\"hatch" in svg and "url(#hatch" in svg
    assert run_view.TEST_RUN_BADGE in plain(page) and "test run" in plain(page)
    real = c.get(f"/runs/{runs['sufficient']}").text
    assert run_view.TEST_RUN_BADGE not in plain(real)


def test_the_runs_list_shows_a_small_dial_for_every_run(world):
    engine, url, runs = world
    page = signed_in(engine, url).get("/runs").text
    assert page.count('class="dial dial-small"') == len(runs)
    assert page.count("Level 6 of 6: tested answer") >= 2 and "Level 1 of 6: nothing tested" in page
    shown = plain(page)  # the visible words (each dial's words are also its accessible name)
    assert shown.count(run_view.NOT_COMPLETED) == 2  # the waiting and the queued run
    assert shown.count(run_view.FAILED_NO_LEVEL) == 1  # the cancelled run (owner, 2026-10-11)
    assert f'aria-label="{run_view.FAILED_NO_LEVEL}"' in page


def test_states_are_shown_in_words_and_a_waiting_run_waits_at_the_rules_lock(world):
    engine, url, runs = world
    c = signed_in(engine, url)
    waiting_page = plain(c.get(f"/runs/{runs['waiting']}").text)
    assert "waiting at the rules lock" in waiting_page and "none" not in waiting_page.split("Status", 1)[1][:80]
    assert f"Waits for {confirmation.WAITING_FOR}" in waiting_page
    assert "queued" in plain(c.get(f"/runs/{runs['queued']}").text)


def test_an_unknown_run_is_not_found(world):
    engine, url, _ = world
    assert signed_in(engine, url).get("/runs/999999").status_code == 404


# --- the dial itself -------------------------------------------------------------------------------------------------

def test_the_dial_has_one_hue_that_darkens_with_the_level():
    def lightness(hex_colour):
        r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
        return (max(r, g, b) + min(r, g, b)) / 2

    def hue(hex_colour):
        import colorsys
        r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
        return colorsys.rgb_to_hls(r, g, b)[0] * 360
    shades = dial.SHADES
    assert len(shades) == dial.LEVELS == len(st.EVIDENCE_SHORT) == len(st.EVIDENCE_LEVELS) == 6
    assert all(lightness(a) > lightness(b) for a, b in zip(shades, shades[1:]))
    assert max(hue(s) for s in shades) - min(hue(s) for s in shades) < 10  # one hue, not red to green


@pytest.mark.parametrize("level", range(1, 7))
def test_the_needle_points_at_the_runs_level(level):
    svg = str(dial.svg(level, label=f"Level {level}"))
    assert svg.count(" current") == 1 and f'class="seg seg-{level} current"' in svg
    x2 = float(re.search(r'class="needle"[^>]*x2="([-\d.]+)"', svg).group(1))
    assert (x2 < 100) == (level <= 3)  # levels 1 to 3 on the left half


def test_the_dial_refuses_a_level_outside_1_to_6():
    for level in (0, 7):
        with pytest.raises(ValueError):
            dial.svg(level)


def test_the_short_labels_are_the_owners_set():
    assert dict(st.EVIDENCE_SHORT) == {6: "tested answer", 5: "exploratory answer", 4: "coefficient only",
                                       3: "below the minimums", 2: "no coefficient fitted", 1: "nothing tested"}


# --- the confirmation page and the confirmation ------------------------------------------------------------------------

def test_the_confirmation_page_shows_exactly_what_the_command_line_shows(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['waiting']}/confirm").text
    content, words = confirmation.show(engine, runs["waiting"])
    for line in words.split("\n"):
        assert " ".join(line.split()) in plain(page), line
    assert f'name="shown_fingerprint" value="{confirmation.shown_fingerprint(content, words)}"' in page
    assert f"Confirming as {NAME}" in plain(page)


def test_the_confirmation_page_shows_the_label_now_and_the_label_once_confirmed(world):
    """The live-run record's open item 4: the text shown at the moment of confirming says the label now and the label
    once confirmed (the same text on the command line); beside the button, the label under the signed-in name."""
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['waiting']}/confirm").text)
    assert "Now labelled: the Planner's reading of the claim; not verified by code and, in this version, not " \
           "confirmed by a person" in page
    assert "Once confirmed, labelled: the Planner's reading of the claim; not verified by code; confirmed by the " \
           "person who confirms on the time of confirming (UTC)" in page
    assert f"Once you confirm, the question as tested is labelled: the Planner's reading of the claim; not verified " \
           f"by code; confirmed by {NAME} on the time you confirm (UTC)." in page


def test_confirming_records_the_signed_in_name_and_exactly_the_text_shown_and_runs_nothing(own, stub):
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    page = c.get(f"/runs/{rid}/confirm").text
    fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
    stages = one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid)
    calls = len(stub.requests)
    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
    assert r.status_code == 303 and r.headers["location"] == f"/runs/{rid}?done=confirmed"
    with engine.connect() as conn:
        row = conn.execute(text("SELECT confirmed_by, shown FROM rules_confirmation WHERE run_id = :r"),
                           dict(r=rid)).one()
    assert row.confirmed_by == NAME and row.shown == confirmation.show(engine, rid)[1]
    # The web service runs nothing: the run still waits for a worker; no stage, claim or model call was added.
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == stages
    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 0
    assert len(stub.requests) == calls
    assert "Confirmed under your name" in plain(c.get(f"/runs/{rid}?done=confirmed").text)


def test_a_confirmation_of_content_other_than_what_was_shown_is_refused(own, stub):
    """Owner's addition 2: the page sends back the fingerprint of what it showed; other content is content_changed."""
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    for fp in ("0" * 64, confirmation.shown_fingerprint({"run": rid}, "another text")):
        r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
        assert r.status_code == 409 and "show it again before confirming" in plain(r.text)
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0


def test_a_confirmation_without_the_shown_contents_fingerprint_is_refused(own, stub):
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c)})
    assert r.status_code == 409
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0


@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
def test_a_write_without_the_sessions_token_is_refused_and_writes_nothing(own, stub, sent):
    """Owner's addition 1: confirm and cancel (10a's writes) refuse a request without the session's token."""
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    fp = confirmation.shown_fingerprint(*confirmation.show(engine, rid))
    extra = {} if sent is None else {"csrf_token": sent}
    assert c.post(f"/runs/{rid}/confirm", data={"shown_fingerprint": fp, **extra}).status_code == 403
    assert c.post(f"/runs/{rid}/cancel", data=extra).status_code == 403
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_another_sessions_token_is_refused(own, stub):
    engine, url = own
    rid = waiting(engine, stub)
    a, b = signed_in(engine, url), signed_in(engine, url, "Other Person")
    assert token(a) != token(b)
    assert b.post(f"/runs/{rid}/cancel", data={"csrf_token": token(a)}).status_code == 403
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_cancel_records_the_signed_in_name(own, stub):
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    r = c.post(f"/runs/{rid}/cancel", data={"csrf_token": token(c)})
    assert r.status_code == 303
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
        queries.CANCELLED["waiting"].format(by=NAME)


def test_a_completed_run_cannot_be_cancelled_and_the_reason_is_shown(world):
    engine, url, runs = world
    c = signed_in(engine, url)
    r = c.post(f"/runs/{runs['sufficient']}/cancel", data={"csrf_token": token(c)})
    assert r.status_code == 409 and "Not cancelled:" in plain(r.text)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=runs["sufficient"]) == "completed"


def test_a_completed_run_has_no_confirmation_to_give(world):
    engine, url, runs = world
    c = signed_in(engine, url)
    assert "is not waiting for a confirmation" in plain(c.get(f"/runs/{runs['sufficient']}/confirm").text)
    r = c.post(f"/runs/{runs['sufficient']}/confirm", data={"csrf_token": token(c), "shown_fingerprint": "0" * 64})
    assert r.status_code == 409


# --- the name at sign-in ---------------------------------------------------------------------------------------------

def test_signing_in_needs_a_name_and_keeps_it_with_a_token(world):
    engine, url, _ = world
    c = make_client(engine, url)
    for bad in ("", "   ", "x" * (security.NAME_MAX + 1)):
        r = c.post("/login", data={"password": PASSWORD, "name": bad})
        assert r.status_code == 400 and SESSION_COOKIE not in c.cookies
    assert c.post("/login", data={"password": PASSWORD, "name": "  Ada   Lovelace "}).status_code == 303
    s = session(c)
    assert set(s) == {"signed_in", "name", "csrf"} and s["name"] == "Ada Lovelace" and len(s["csrf"]) >= 40
    assert "Signed in: Ada Lovelace" in plain(c.get("/runs").text)


def test_the_name_cannot_change_within_a_session(world):
    """Owner's addition 3: a new name means signing out and in again."""
    engine, url, _ = world
    c = signed_in(engine, url, "First Name")
    before = session(c)
    r = c.post("/login", data={"password": PASSWORD, "name": "Second Name"})
    assert r.status_code == 409 and "signed in as First Name" in plain(r.text)
    assert session(c) == before
    c.post("/logout")
    assert c.post("/login", data={"password": PASSWORD, "name": "Second Name"}).status_code == 303
    assert session(c)["name"] == "Second Name" and session(c)["csrf"] != before["csrf"]


def test_a_session_without_a_name_cannot_act(own, stub):
    """A cookie signed before step 10a holds no name: it may read but must sign in again before it acts."""
    engine, url = own
    rid = waiting(engine, stub)
    c = signed_in(engine, url)
    from itsdangerous import TimestampSigner
    old = base64.b64encode(json.dumps({"signed_in": True, "csrf": "t" * 43}).encode())
    c.cookies.set(SESSION_COOKIE, TimestampSigner(SECRET).sign(old).decode())
    assert c.get(f"/runs/{rid}").status_code == 200
    assert c.post(f"/runs/{rid}/cancel", data={"csrf_token": "t" * 43}).status_code == 403
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


# --- text size and the glossary --------------------------------------------------------------------------------------

def test_no_text_on_any_screen_is_smaller_than_12px():
    """Owner's addition 6: every font-size in the stylesheet is in rem (no em, which compounds) and at least
    0.75rem = 12 px; no template sets a size of its own; the dial holds no text."""
    import pathlib
    web = pathlib.Path(dial.__file__).resolve().parent
    css = (web / "static" / "style.css").read_text(encoding="utf-8")
    sizes = re.findall(r"font(?:-size)?\s*:\s*([^;}]+)", css)
    assert sizes
    for value in sizes:
        for number, unit in re.findall(r"([\d.]+)(rem|px|em|pt|%|vw|vh)\b", value):
            assert unit in ("rem", "px"), value
            assert float(number) * (16 if unit == "rem" else 1) >= 12, value
    for t in (web / "templates").glob("*.html"):
        assert "font-size" not in t.read_text(encoding="utf-8") and "style=" not in t.read_text(encoding="utf-8"), t
    for level in (None, *range(1, 7)):
        for size in dial.SIZES:
            assert "<text" not in str(dial.svg(level, True, size))


def test_every_information_button_in_the_templates_has_a_glossary_entry():
    import pathlib
    from hypocurate.web import glossary
    web = pathlib.Path(dial.__file__).resolve().parent
    used = set()
    for t in (web / "templates").glob("*.html"):
        used |= set(re.findall(r'info\("([a-z_]+)"\)', t.read_text(encoding="utf-8")))
    assert used and used <= set(glossary.by_key())
    assert "evidence_level" in used


def test_an_information_button_has_its_accessible_name_and_the_glossary_text(world):
    from hypocurate.web import glossary
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    e = glossary.entry("evidence_level")
    assert f'aria-label="Explain: {html.escape(e["term"])}"' in page
    assert html.escape(e["text"]) in page


def test_every_sensitivity_set_has_a_display_name_and_a_description():
    from hypocurate.pipeline.eligibility import INFLUENCE_KEY
    for key in SENSITIVITY_CHANGES:
        assert run_view._set_display_name(key) != "another sensitivity set", key
        assert run_view._set_description(key), key
    assert set(run_view.SET_DESCRIPTIONS) | {INFLUENCE_KEY} == set(SENSITIVITY_CHANGES)


# --- the owner's review of the screenshots (2026-10-11) ---------------------------------------------------------------

def test_units_are_written_with_a_real_superscript_on_the_screens(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    assert "MPa·µm<sup>0.5</sup>" in page and "µm^0.5" not in page
    assert "^0.5" in " ".join(run_view.show(engine, runs["sufficient"])["statement"])  # the stored text keeps "^"


def test_the_large_dial_shows_the_level_label_without_the_long_wording(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    box = re.search(r'<div class="dial-box">.*?</div>\s*</div>', page, re.S).group(0)
    assert "Level 6 of 6: tested answer" in box and st.EVIDENCE_LEVELS[6] not in box


def test_the_survivor_set_says_that_conflicting_values_are_normally_left_out():
    assert run_view._set_description("conflicts_survivor_value") == (
        "Conflicting values, left out of the main result, are included once each, using the survivor's value.")


def test_the_evidence_level_help_says_a_minimum_missed():
    from hypocurate.web import glossary
    text_ = glossary.entry("evidence_level")["text"]
    assert "5 an exploratory answer, with a minimum missed;" in text_ and "waived" not in text_


def test_one_model_call_is_singular(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    assert "1 model call ·" in page and "1 model calls" not in page


def test_an_old_run_without_a_stored_ceiling_shows_not_recorded(own, stub):
    """Runs dispatched before migration 0007 have no ceiling. The database never lets a new run store none (0007's
    trigger), so the test makes an old run's row by switching triggers off for one statement on its own database."""
    engine, url = own
    rid = to.dispatched(engine, fixed_plan=True)
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        conn.execute(text("UPDATE run SET spending_ceiling = NULL WHERE id = :r"), dict(r=rid))
    page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
    assert "ceiling for this run not recorded" in page and "$0.000000" not in page.split("ceiling for this run")[1][:20]


# --- step 10b: the runs list's "Plan" column (owner, 2026-10-11) -------------------------------------------------------

def test_the_runs_list_says_where_each_runs_question_as_tested_came_from(own, stub):
    """From what is stored, never a guess: a fixed-plan run, a Planner run waiting, a Planner run confirmed by a named
    person, and a Planner-path run locked before confirmations existed (the shape of local runs 1 and 2)."""
    from hypocurate.pipeline import confirmation, reading
    from test_reading_step10 import planner_path_run_locked_before_confirmations
    engine, url = own
    fixed = to.dispatched(engine, fixed_plan=True)
    planner = waiting(engine, stub)
    confirmed = waiting(engine, stub)
    confirmation.confirm(engine, confirmed, by="Ada Reviewer")
    predates = planner_path_run_locked_before_confirmations(engine)
    page = signed_in(engine, url).get("/runs").text
    plans = dict((int(r), p) for r, p in re.findall(
        r'<td data-label="Run"><a href="/runs/(\d+)".*?<td data-label="Plan">([^<]*)</td>', page, re.S))
    assert plans[fixed] == reading.PROVENANCE_WORDS["fixed"] == "fixed reference plan"
    assert plans[planner] == "Planner&#39;s reading"
    assert plans[confirmed] == "Planner&#39;s reading, confirmed by Ada Reviewer"
    assert plans[predates] == "Planner&#39;s reading; predates confirmation"


def test_a_narrower_questions_run_says_so(own, stub):
    from hypocurate.pipeline import reading
    from test_confirmation import narrower_waiting
    engine, url = own
    rid, original = narrower_waiting(engine, stub)
    with engine.connect() as conn:
        assert reading.provenance(conn, rid) == f"narrower question, built by code from run {original}"
        assert reading.provenance(conn, original) == "Planner's reading"  # partly sufficient: never locked


# --- step 10b: each sensitivity set says what it changes compared with the main result (owner, 2026-10-11) ---------

def test_every_set_description_says_what_the_main_result_does_instead():
    from hypocurate.pipeline.eligibility import INFLUENCE_KEY
    for key in SENSITIVITY_CHANGES:
        assert "main result" in run_view._set_description(key), key
    assert run_view._set_description(INFLUENCE_KEY).endswith("; the main result keeps them.")


def test_the_one_at_pct_set_names_the_main_results_own_rounding_from_the_plan():
    from hypocurate.pipeline.plan import reference_plan
    plan = reference_plan(1)
    assert "instead of to 0.1 at.%, as in the main result" in run_view._set_description("same_alloy_1_at_pct", plan)
    plan["rules"]["same_alloy_decimals"] = 2
    assert "instead of to 0.01 at.%, as in the main result" in run_view._set_description("same_alloy_1_at_pct", plan)


def test_atomic_percent_is_written_out_once_on_the_run_page(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
    assert page.count("atomic percent (at.%)") == 1
    assert page.index("atomic percent (at.%)") < page.index("rounded to 1 at.%")
