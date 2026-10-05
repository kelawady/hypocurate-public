"""Step 4b: the assumptions register (`hypocurate/assumptions.json`) and its read-only page.

- Every entry follows the schema; the validator refuses each kind of malformed entry.
- The owner's eight decisions of 2026-10-05 are present as decided.
- **Every entry marked "applied: yes" names at least one setting that exists in the code,
  and where the register gives a value, the code holds that value** (CLAUDE.md, "How we
  work", item 12). A setting renamed or changed in code without the register fails here.
- GET /assumptions needs the login, is generated from the register, and offers no editing.
"""
import copy
import json
import re

import pytest
from markupsafe import escape
from fastapi.testclient import TestClient

from hypocurate import assumptions as a
from hypocurate.db.engine import make_engine
from hypocurate.web.app import create_app
from test_login import PASSWORD, settings

REGISTER = a.load_register()
BY_KEY = {e["key"]: e for e in REGISTER}
OWNER = "owner (Khalid El-Awady)"

# The owner's eight decisions of 2026-10-05 (step 4b instructions, a to h).
OWNER_DECISIONS = {
    "tamu_test_temperature": ("scientific", 6),
    "permitted_test_types": ("scientific", 6),
    "tamu_grouping_unit": ("statistical", None),  # already applied: the adapter's grouping unit
    "same_alloy_rule": ("scientific", 6),
    "fixed_minimums": ("statistical", 6),
    "values_disagree_tolerance": ("data_handling", 6),
    "calibration_noise_levels": ("statistical", 7),
    "tag_starting_lists": ("data_handling", 6),
}


# --- Schema ---------------------------------------------------------------------------

def test_the_register_file_follows_the_schema():
    raw = json.loads(a.REGISTER_PATH.read_text(encoding="utf-8"))
    a.validate(raw)
    assert len(raw) == len(BY_KEY) >= 50


def test_every_category_has_entries_and_keys_are_unique():
    assert {e["category"] for e in REGISTER} == set(a.CATEGORIES)
    assert len({e["key"] for e in REGISTER}) == len(REGISTER)


def test_the_owners_eight_decisions_are_recorded_as_decided():
    for key, (category, step) in OWNER_DECISIONS.items():
        e = BY_KEY[key]
        assert e["state"] == "in_force", key
        assert e["category"] == category, key
        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
        assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}, key
        if step is None:
            assert e["applied"]["status"] == "yes", key
        else:
            assert e["applied"] == {**e["applied"], "status": "not_yet", "step": step}, key


def test_decisions_carry_the_owners_wording():
    assert "assigned by decision" in BY_KEY["tamu_test_temperature"]["value"]["text"]
    assert BY_KEY["permitted_test_types"]["sensitivity"] == "Tension and compression together."
    assert "row:139" in " ".join(BY_KEY["permitted_test_types"]["notes"])
    assert BY_KEY["tamu_grouping_unit"]["sensitivity"] == "Six batches as six groups."
    same_alloy = BY_KEY["same_alloy_rule"]
    assert "rounded compositions are identical" in same_alloy["statement"]
    assert "within" not in same_alloy["statement"]  # the owner's corrected wording
    assert "1 at.%" in same_alloy["sensitivity"]
    assert "min(|a|, |b|)" in BY_KEY["values_disagree_tolerance"]["statement"]
    assert "not final" in " ".join(BY_KEY["values_disagree_tolerance"]["notes"])
    calibration = BY_KEY["calibration_noise_levels"]
    assert "fixed at the rules lock and applied by code" in calibration["statement"]
    assert "no person or agent chooses the values" in calibration["statement"]
    notes = " ".join(calibration["notes"])
    assert "PRD 5.10" in notes and "second-model review in step 7" in notes and "both ways" in notes
    assert BY_KEY["p_threshold_comparison"]["value"]["text"] == "p < 0.05"


def test_open_decisions_have_no_value_in_force():
    open_entries = [e for e in REGISTER if e["state"] == "open"]
    assert [e["key"] for e in open_entries] == ["tamu_microstructure"]
    for e in open_entries:
        assert e["value"] is None and e["decided"] is None and e["pending"]["by"] == "owner"


def entry(**changes):
    e = copy.deepcopy(BY_KEY["session_length"])
    e.update(changes)
    return e


@pytest.mark.parametrize("bad, message", [
    (lambda e: e.pop("affects"), "missing"),
    (lambda e: e.update(extra=1), "unknown"),
    (lambda e: e.update(key="Bad Key"), "key"),
    (lambda e: e.update(category="physics"), "category"),
    (lambda e: e.update(state="draft"), "state"),
    (lambda e: e.update(statement="  "), "statement"),
    (lambda e: e.update(evidence=[]), "evidence"),
    (lambda e: e["decided"].update(date="5 Oct 2026"), "date"),
    (lambda e: e["decided"].update(date="2026-13-01"), "date"),
    (lambda e: e["expert_review"].update(status="approved"), "expert_review.status"),
    (lambda e: e["expert_review"].update(name="Prof. X"), "not reviewed has no name"),
    (lambda e: e.update(expert_review={"status": "accepted", "name": None, "date": None}), "expert_review.name"),
    (lambda e: e.update(expert_review={"status": "disputed", "name": "Prof. X", "date": None}), "expert_review.date"),
    (lambda e: e.update(applied={"status": "yes", "settings": [], "note": None}), "at least one named setting"),
    (lambda e: e.update(applied={"status": "yes", "note": None}), "missing"),
    (lambda e: e.update(applied={"status": "maybe", "note": None}), "applied.status"),
    (lambda e: e.update(applied={"status": "not_yet", "step": 4, "note": None}), "build step"),
    (lambda e: e.update(applied={"status": "not_yet", "step": 13, "note": None}), "build step"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-05", "to": "2026-10-04", "note": None}]), "after"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-01", "to": "2026-10-03", "note": None},
                                 {"value": "y", "from": "2026-10-02", "to": "2026-10-04", "note": None}]), "date order"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-01", "to": "2026-10-09", "note": None}]),
     "after the current value was decided"),
    (lambda e: e.update(value=None), "value"),
    (lambda e: e.update(state="open"), "missing ['pending']"),
    (lambda e: e.update(state="open", pending={"by": "owner", "before_step": 6}), "open decision has value null"),
    (lambda e: e.update(pending={"by": "owner", "before_step": 6}), "unknown"),
])
def test_the_validator_refuses_malformed_entries(bad, message):
    e = entry()
    bad(e)
    with pytest.raises(a.RegisterError, match=re.escape(message)):
        a.validate([e])


def test_the_validator_refuses_duplicate_keys_and_an_empty_register():
    with pytest.raises(a.RegisterError, match="duplicate key"):
        a.validate([entry(), entry()])
    with pytest.raises(a.RegisterError, match="non-empty list"):
        a.validate([])


def test_an_open_decision_needs_who_decides_and_by_when():
    e = copy.deepcopy(BY_KEY["tamu_microstructure"])
    del e["pending"]
    with pytest.raises(a.RegisterError, match="missing"):
        a.validate([e])
    e["pending"] = {"by": "owner", "before_step": 3}
    with pytest.raises(a.RegisterError, match="build step"):
        a.validate([e])


# --- Applied in code: a named setting ---------------------------------------------------

def test_every_applied_entry_names_settings_that_exist_and_match():
    applied = [e for e in REGISTER if e["applied"]["status"] == "yes"]
    assert len(applied) >= 20
    problems = [p for e in applied for p in a.check_settings(e)]
    assert not problems, "\n".join(problems)


def test_applied_values_are_compared_where_the_register_gives_them():
    """Spot-check that `equals` is used for the numeric and categorical defaults."""
    compared = {s["ref"]: s["equals"] for e in REGISTER if e["applied"]["status"] == "yes"
                for s in e["applied"]["settings"] if "equals" in s}
    assert compared["python:hypocurate.web.login_throttle:MAX_FAILURES"] == 5
    assert compared["python:hypocurate.web.login_throttle:WINDOW_SECONDS"] == 900
    assert compared["python:hypocurate.web.app:SESSION_MAX_AGE"] == 12 * 60 * 60
    assert compared["python:hypocurate.sources.versions:MAX_FILE_BYTES"] == 5 * 1024 * 1024
    assert compared["python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit"] == "dataset"
    assert compared["python:hypocurate.db.retry:run_transaction(attempts)"] == 5


@pytest.mark.parametrize("ref", [
    "python:hypocurate.web.login_throttle:NO_SUCH_SETTING",
    "python:hypocurate.no_such_module:X",
    "python:hypocurate.sources.versions:SOURCES.no_such_source.grouping_unit",
    "python:hypocurate.db.retry:run_transaction(no_such_parameter)",
    "python:hypocurate.db.retry:run_transaction(fn)",  # no default
    "sql:ck_no_such_constraint",
    "sql:ck_source_file_max",  # part of a name is not the name
    "file:Dockerfile:--workers 4",
    "file:../outside:anything",
    "file:no/such/file:x",
    "env:HYPOCURATE_ENV",
])
def test_a_reference_to_nothing_is_refused(ref):
    with pytest.raises(a.SettingNotFound):
        a.resolve_setting(ref)


def test_a_wrong_value_or_a_missing_setting_is_reported():
    e = copy.deepcopy(BY_KEY["login_throttle"])
    e["applied"]["settings"][0]["equals"] = 6
    assert a.check_settings(e) == [
        "login_throttle: python:hypocurate.web.login_throttle:MAX_FAILURES is 5 in the code, the register says 6"]
    e["applied"]["settings"][0]["ref"] = "python:hypocurate.web.login_throttle:MAX_FAILED"
    assert len(a.check_settings(e)) == 1 and "not found" in a.check_settings(e)[0]


def test_resolved_values_use_json_terms():
    assert a.resolve_setting("python:hypocurate.db.retry:RETRYABLE_SQLSTATES") == ["40001", "40P01"]
    assert a.resolve_setting("python:hypocurate.sources.record:STATUSES") == [
        "converted", "not_reported", "not_convertible", "assigned"]


# --- The page ----------------------------------------------------------------------------

def page_client(register=None):
    s = settings()
    app = create_app(s, engine=make_engine(s.database_url), register=register)
    return TestClient(app, base_url="http://testserver", follow_redirects=False)


def signed_in(register=None):
    c = page_client(register)
    assert c.post("/login", data={"password": PASSWORD}).status_code == 303
    return c


def test_the_page_needs_the_login():
    c = page_client()
    for path in ["/assumptions", "/assumptions?review=not_reviewed", "/assumptions/"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login", path


def test_the_page_shows_every_entry_grouped_with_open_decisions_first():
    html = signed_in().get("/assumptions").text
    headings = re.findall(r"<h2>([^<]+)</h2>", html)
    assert headings == ["Open decisions", "Scientific", "Statistical", "Data handling", "Operational"]
    for e in REGISTER:
        assert f'id="{e["key"]}"' in html, e["key"]
    sections = re.split(r"<h2>", html)[1:]
    for (label, group), section in zip(a.page_sections(REGISTER), sections):
        assert section.startswith(label)
        assert re.findall(r'<tbody id="([a-z0-9_]+)"', section) == [e["key"] for e in group]


def test_the_summary_line_counts_open_decisions_and_unreviewed_scientific_entries():
    html = signed_in().get("/assumptions").text
    summary = re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1)
    n_open = sum(e["state"] == "open" for e in REGISTER)
    n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
    assert f"{n_open} open decision" in summary
    assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
    assert html.index('id="summary"') < html.index("<h2>")


def reviewed(key, status):
    e = copy.deepcopy(BY_KEY[key])
    e["expert_review"] = {"status": status, "name": "Prof. Test Reviewer", "date": "2026-10-06"}
    return e


def test_unreviewed_scientific_entries_are_marked_and_reviewed_ones_are_not():
    register = [reviewed("exponent_fixed", "accepted")] + [e for e in REGISTER if e["key"] != "exponent_fixed"]
    html = signed_in(register).get("/assumptions").text
    bodies = dict(re.findall(r'<tbody id="([a-z0-9_]+)"(.*?)</tbody>', html, re.S))
    for e in register:
        marked = "Not reviewed by an expert</span>" in bodies[e["key"]]
        should = e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed"
        assert marked == should, e["key"]
    assert "Reviewed and accepted: Prof. Test Reviewer, 2026-10-06" in bodies["exponent_fixed"]
    assert "unreviewed-scientific" not in html.split('id="exponent_fixed"')[0].rsplit("<tbody", 1)[1]


def test_the_filter_shows_only_entries_not_reviewed_by_an_expert():
    register = ([reviewed("exponent_fixed", "accepted"), reviewed("session_length", "disputed")]
                + [e for e in REGISTER if e["key"] not in ("exponent_fixed", "session_length")])
    c = signed_in(register)
    everything = c.get("/assumptions").text
    filtered = c.get("/assumptions?review=not_reviewed").text
    assert 'id="exponent_fixed"' in everything and 'id="session_length"' in everything
    shown = re.findall(r'<tbody id="([a-z0-9_]+)"', filtered)
    assert set(shown) == {e["key"] for e in register if e["expert_review"]["status"] == "not_reviewed"}
    assert 'href="/assumptions">Show all' in filtered


def test_each_row_expands_to_reason_evidence_history_and_sensitivity():
    html = signed_in().get("/assumptions").text
    body = re.search(r'<tbody id="values_disagree_tolerance"(.*?)</tbody>', html, re.S).group(1)
    e = BY_KEY["values_disagree_tolerance"]
    assert "<details>" in body
    for text in [e["reason"], e["evidence"][0], e["history"][0]["value"], e["notes"][0], "Sensitivity analysis"]:
        assert str(escape(text)) in body, text
    applied = re.search(r'<tbody id="session_length"(.*?)</tbody>', html, re.S).group(1)
    assert "<code>python:hypocurate.web.app:SESSION_MAX_AGE</code>" in applied
    assert "Not yet: step 7" in re.search(r'<tbody id="exponent_fixed"(.*?)</tbody>', html, re.S).group(1)


def test_the_page_is_read_only():
    c = signed_in()
    html = c.get("/assumptions").text
    assert re.findall(r"<form[^>]*>", html) == ['<form method="post" action="/logout" class="logout">']
    assert "<input" not in html and "<textarea" not in html and "<select" not in html
    for method in ("post", "put", "patch", "delete"):
        assert getattr(c, method)("/assumptions").status_code == 405, method


def test_the_service_does_not_start_with_an_invalid_register():
    bad = [entry(category="physics")]
    with pytest.raises(a.RegisterError):
        page_client(bad)


def test_the_home_page_links_to_the_register():
    assert 'href="/assumptions"' in signed_in().get("/").text
