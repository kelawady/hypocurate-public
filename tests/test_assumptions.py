"""Step 4b: the assumptions register (`hypocurate/assumptions.json`) and its read-only page.

- Every entry follows the schema; the validator refuses each kind of malformed entry.
- The owner's decisions of 2026-10-05 and the step 4b review's corrections are present.
- **Reference and value checks:** every entry applied in code (fully or partly) names at
  least one setting that exists, and where the register gives a value, the code holds it
  (CLAUDE.md, "How we work", item 12). A setting renamed or changed without the register
  fails here. These checks do **not** show that an entry's wording matches what the code
  does (step 4b review, finding 1): behaviour is covered by the regression tests each
  applied entry names, and this file checks only that those tests exist.
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
    "tamu_grouping_unit": ("statistical", 7),  # partly applied: the adapter's grouping unit
    "same_alloy_rule": ("scientific", 6),  # partly applied from step 5: the gap report's summaries
    "fixed_minimums": ("statistical", 6),  # partly applied: the database's checks
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


PARTLY = {"tamu_grouping_unit", "papers_independent", "sufficiency_options", "controlled_extract_disabled",
          "validity_checks", "fixed_minimums", "grain_size_transformation_at_analysis", "assigned_value_statuses",
          "same_alloy_rule"}  # step 5: the gap report's condition summaries group alloys under the rule


def test_the_owners_eight_decisions_are_recorded_as_decided():
    for key, (category, step) in OWNER_DECISIONS.items():
        e = BY_KEY[key]
        # Review finding 4: the calibration direction is approved, its technical review pending.
        expected_state = "direction_approved" if key == "calibration_noise_levels" else "in_force"
        assert e["state"] == expected_state, key
        assert e["category"] == category, key
        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
        assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}, key
        status = "partly" if key in PARTLY else "not_yet"
        assert e["applied"]["status"] == status and e["applied"]["step"] == step, key


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
    assert "conflict_pairing_rule" in " ".join(BY_KEY["values_disagree_tolerance"]["notes"])
    calibration = BY_KEY["calibration_noise_levels"]
    assert "fixed at the rules lock and applied by code" in calibration["statement"]
    assert "no person or agent chooses the values" in calibration["statement"]
    notes = " ".join(calibration["notes"])
    assert "PRD 5.10" in notes and "second-model review in step 7" in notes and "both ways" in notes
    assert BY_KEY["p_threshold_comparison"]["value"]["text"] == "p < α (α = 0.05 by default)"


# --- The step 4b review (second model, 2026-10-05), accepted by the owner -------------------

def test_partly_applied_entries_say_what_is_done_and_what_is_pending():
    """Finding 2: no entry says 'Yes' while its principal safeguard is pending."""
    assert {e["key"] for e in REGISTER if e["applied"]["status"] == "partly"} == PARTLY
    for key in PARTLY:
        applied = BY_KEY[key]["applied"]
        assert applied["done"] and applied["pending"] and applied["settings"], key


def test_the_survivor_rule_has_the_owners_step_1_wording():
    """Finding 3: a DOI identifies the cited paper, not where a record was extracted."""
    e = BY_KEY["duplicate_survivor_rule"]
    assert e["statement"].startswith("1) Prefer the record that carries the original paper reference (DOI).")
    assert "directly" not in e["statement"] and "detected" not in e["statement"]
    assert "extraction-origin metadata, which does not exist" in " ".join(e["notes"])
    assert "detected by the original paper's DOI" in e["history"][0]["value"]  # the withdrawn wording


def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review():
    """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)."""
    assert [e["key"] for e in REGISTER if e["state"] == "open"] == []
    pairing = BY_KEY["conflict_pairing_rule"]
    assert pairing["state"] == "in_force" and "pending" not in pairing
    assert pairing["decided"] == {"by": OWNER, "date": "2026-10-05"}
    assert pairing["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
    assert pairing["applied"]["status"] == "not_yet" and pairing["applied"]["step"] == 6
    assert pairing["statement"] == (
        "Duplicates and conflicts are looked for only between records from different sources that cite the "
        "same paper with the same alloy, grain size and test conditions. Rows within one source are always "
        "separate measurements (repeat specimens).")
    notes = " ".join(pairing["notes"])
    assert "a source that repeats its own row by mistake is not caught" in notes
    assert "Not reviewed by an expert." in notes
    assert pairing["history"][0]["value"].startswith("open decision:")
    assert [e["key"] for e in REGISTER if e["state"] == "direction_approved"] == ["calibration_noise_levels"]
    assert BY_KEY["calibration_noise_levels"]["pending"] == {"by": "second-model technical review", "before_step": 7}


REVIEW_ADDITIONS = {
    "association_not_causation": "scientific", "measurement_error_not_propagated": "scientific",
    "equal_row_weights": "statistical", "selection_and_missingness": "statistical",
    "no_multiplicity_adjustment": "statistical", "calibration_error_model": "statistical",
    "few_groups_approximate": "statistical", "observation_unit": "data_handling",
}


def test_the_eight_missing_assumptions_are_added_not_reviewed():
    for key, category in REVIEW_ADDITIONS.items():
        e = BY_KEY[key]
        assert e["category"] == category and e["state"] == "in_force", key
        assert e["expert_review"]["status"] == "not_reviewed" and e["affects"], key
    assert "never imply proof of cause" in " ".join(BY_KEY["association_not_causation"]["notes"])
    assert "not the mean of" in BY_KEY["measurement_error_not_propagated"]["statement"]
    assert "not each paper or alloy" in BY_KEY["equal_row_weights"]["statement"]
    assert "publication bias" in BY_KEY["selection_and_missingness"]["statement"]
    assert "do not keep a 5% false-positive rate" in BY_KEY["no_multiplicity_adjustment"]["statement"]
    assert "It does not simulate source discovery" in BY_KEY["calibration_error_model"]["statement"]
    assert "approximations" in BY_KEY["few_groups_approximate"]["statement"]
    assert "repeated specimens" in BY_KEY["observation_unit"]["statement"]


def test_the_small_corrections():
    assert "CSV" in BY_KEY["malformed_files_refused"]["statement"]
    assert "Spreadsheets are handled differently" in BY_KEY["malformed_files_refused"]["statement"]
    assert "may change the calibration" in BY_KEY["normal_errors_in_calibration"]["affects"]
    assert "optimistic" not in json.dumps(BY_KEY["normal_errors_in_calibration"])
    session = BY_KEY["session_length"]["statement"]
    assert "12 hours after sign-in" in session and "do not renew" in session


def test_every_entry_applied_in_code_names_regression_tests_that_exist():
    """Finding 1: behaviour is covered by named regression tests, which must exist."""
    applied = [e for e in REGISTER if e["applied"]["status"] in ("yes", "partly")]
    assert all(e["tests"] for e in applied)
    missing = [m for e in REGISTER for m in a.named_tests_missing(e)]
    assert not missing, "\n".join(missing)


def test_a_named_test_that_does_not_exist_is_reported():
    e = copy.deepcopy(BY_KEY["login_throttle"])
    e["tests"] = ["tests/test_login_throttle.py::test_no_such_test", "tests/test_nothing.py::test_x",
                  "tests/test_login_throttle.py::test_defaults_are_as_approved"]
    assert a.named_tests_missing(e) == ["login_throttle: tests/test_login_throttle.py::test_no_such_test does not exist",
                                        "login_throttle: tests/test_nothing.py::test_x does not exist"]


def test_the_microstructure_decision_is_recorded():
    """Owner, 2026-10-05: the open decision 'tamu_microstructure' became a decision."""
    assert "tamu_microstructure" not in [e["key"] for e in REGISTER if e["state"] == "open"]
    e = BY_KEY["tamu_microstructure"]
    assert e["state"] == "in_force" and e["category"] == "scientific"
    assert e["value"]["text"] == "single-phase FCC (assigned by decision)"
    assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}
    assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
    assert e["applied"]["status"] == "not_yet" and e["applied"]["step"] == 6
    evidence = " ".join(e["evidence"])
    for cited in ("main.tex line 138", "main.tex line 173", "supplementary.tex line 61", "main.tex line 175",
                  "main.tex line 177", "supplementary.tex line 65"):
        assert cited in evidence, cited
    notes = " ".join(e["notes"])
    assert "81 compositions" in notes and "82" in notes
    assert "No passage states the result of the XRD phase check." in notes
    assert "Not reviewed by an expert." in notes
    assert "without these records" in e["sensitivity"]
    assert e["history"][0]["value"].endswith("(open decision)")


def open_entry():
    """An open decision built for the tests, independent of the register's own."""
    e = copy.deepcopy(BY_KEY["tamu_microstructure"])
    e.update(key="an_open_question", state="open", value=None, decided=None, history=[],
             pending={"by": "owner", "before_step": 6})
    return e


def test_an_open_decision_has_no_value_in_force():
    a.validate([open_entry()])
    for field, value in (("value", {"text": "x", "unit": None}), ("decided", {"by": "owner", "date": "2026-10-05"})):
        e = open_entry()
        e[field] = value
        with pytest.raises(a.RegisterError, match="open decision has value null"):
            a.validate([e])


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
    (lambda e: e.update(state="direction_approved"), "missing ['pending']"),
    (lambda e: e.update(state="direction_approved", pending={"by": "review", "before_step": 13}), "build step"),
    (lambda e: e.update(tests=[]), "names the regression tests"),
    (lambda e: e.update(tests=["tests/test_login.py:test_x"]), "tests[0]"),
    (lambda e: e.pop("tests"), "missing"),
    (lambda e: e.update(applied={"status": "partly", "settings": [{"ref": "x"}], "done": "d", "pending": "p",
                                 "note": None}), "missing ['step']"),
    (lambda e: e.update(applied={"status": "partly", "settings": [{"ref": "x"}], "done": " ", "pending": "p",
                                 "step": 6, "note": None}), "applied.done"),
    (lambda e: e.update(applied={"status": "partly", "settings": [], "done": "d", "pending": "p",
                                 "step": 6, "note": None}), "at least one named setting"),
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
    e = open_entry()
    del e["pending"]
    with pytest.raises(a.RegisterError, match="missing"):
        a.validate([e])
    e["pending"] = {"by": "owner", "before_step": 3}
    with pytest.raises(a.RegisterError, match="build step"):
        a.validate([e])


# --- Applied in code: a named setting ---------------------------------------------------

def test_every_applied_entry_names_settings_that_exist_and_match():
    """Reference and value checks only (review finding 1)."""
    applied = [e for e in REGISTER if e["applied"]["status"] in ("yes", "partly")]
    assert len(applied) >= 20
    problems = [p for e in applied for p in a.check_settings(e)]
    assert not problems, "\n".join(problems)


def test_applied_values_are_compared_where_the_register_gives_them():
    """Spot-check that `equals` is used for the numeric and categorical defaults."""
    compared = {s["ref"]: s["equals"] for e in REGISTER if e["applied"]["status"] in ("yes", "partly")
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


HEADINGS = ["Open decisions", "Direction approved, pending technical review",
            "Scientific", "Statistical", "Data handling", "Operational"]


def test_the_page_shows_every_entry_grouped_with_pending_states_first():
    html = signed_in().get("/assumptions").text
    headings = re.findall(r"<h2>([^<]+)</h2>", html)
    assert headings == HEADINGS[1:]  # no open decision since the owner decided the pairing rule (step 5)
    for e in REGISTER:
        assert f'id="{e["key"]}"' in html, e["key"]
    sections = re.split(r"<h2>", html)[1:]
    for (label, group), section in zip(a.page_sections(REGISTER), sections):
        assert section.startswith(label)
        assert re.findall(r'<tbody id="([a-z0-9_]+)"', section) == [e["key"] for e in group]


def test_open_decisions_are_shown_first_when_there_are_any():
    register = REGISTER + [open_entry()]
    html = signed_in(register).get("/assumptions").text
    headings = re.findall(r"<h2>([^<]+)</h2>", html)
    assert headings == HEADINGS
    first = re.split(r"<h2>", html)[1]
    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["an_open_question"]
    assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
    assert "1 open decision</strong>" in html
    second = re.split(r"<h2>", html)[2]
    assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
    assert "pending: second-model technical review, before step 7" in second


def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
    html = signed_in().get("/assumptions").text
    summary = " ".join(re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1).split())
    count = {s: sum(e["state"] == s for e in REGISTER) for s in a.STATES}
    n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
    assert count == {"in_force": len(REGISTER) - 1, "open": 0, "direction_approved": 1}
    assert f"{len(REGISTER)} entries: {count['in_force']} in force" in summary
    assert "0 open decisions</strong>" in summary
    assert "1 direction approved, pending technical review</strong>" in summary
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
    assert "<code>tests/test_login.py::test_session_expires_after_max_age</code>" in applied
    assert "Named settings (reference and value checks only)" in applied


def test_a_partly_applied_entry_shows_done_and_pending_in_its_main_row():
    """Finding 2: the reader sees the pending safeguard without expanding the row."""
    html = signed_in().get("/assumptions").text
    for key in PARTLY:
        body = re.search(rf'<tbody id="{key}"(.*?)</tbody>', html, re.S).group(1)
        main_row = body.split('<tr class="more">')[0]
        applied = BY_KEY[key]["applied"]
        assert "<strong>Partly.</strong>" in main_row, key
        assert str(escape(applied["done"])) in main_row and str(escape(applied["pending"])) in main_row, key
        assert f"Pending (step {applied['step']}):" in main_row, key


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
