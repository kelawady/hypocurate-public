"""Midway submission (owner's brief and approval of 2026-11-02): leftover labels taken off the screens, and the Plan
panel on the run page.

C: the home page no longer names a build step, and the run page's header no longer shows the agent mode. The agent mode
stays a stored column and a row of the workbook's run summary (owner's answer: a factual record, not a screen label).

B: the Plan panel shows the locked plan as the parts of Table 1 of the midway report, display only. Owner's answers:
the stored plan exactly (conditions equal, the residual degrees of freedom included), grouping only for the run's own
sources, a set about a source the run did not choose marked not applicable; the Hypothesis row is the stored claim with
the question as tested under it; the panel sits below the Results statement, and there is none before the rules lock.
"""
from __future__ import annotations

import pytest

import pipeline_world as pw
import stub_provider as sp
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import eligibility, run_view, workbook
from hypocurate.pipeline.plan import reference_plan, with_pilot_sources
from test_web_runs import completed, plain, signed_in, waiting
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
        yield engine, url, {"sufficient": completed(engine, stub), "waiting": waiting(engine, stub)}
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


# --- B: the Plan panel -----------------------------------------------------------------------------------------------

NAMES = {"mpea": "MPEA", "tamu_fcc": "Texas A&M FCC"}
PILOT = {"mpea": "MPEA", "extracted_pilot": "Extracted records"}


def rows(plan, names=NAMES) -> dict[str, str]:
    return {r["part"]: r["setting"] for r in run_view.plan_rows(plan, names)}


def test_the_reference_plan_is_shown_as_the_parts_of_table_1():
    r = rows(reference_plan(1))
    assert list(r) == list(run_view.PLAN_PARTS)
    assert r["Population"] == "multi-principal-element (high-entropy) alloys; phase class FCC; single phase only"
    assert r["Test conditions"] == "test type tension; room temperature, 20 to 25 °C"
    assert r["Exclusions"].startswith("excluding records with a grain size below 0.1 µm; excluding records with "
                                      "physically impossible values")
    assert r["Same alloy"] == "compositions identical after rounding to 0.1 at.%"
    assert "grain sizes within 2%" in r["Same record"] and "the same test conditions" in r["Same record"]
    assert "yield strengths within 2%" in r["Same record"] and "conflict and are left out" in r["Same record"]
    assert r["Model"].startswith("yield strength = a baseline for each alloy + k × (grain size in µm)^-1/2")
    assert r["Test"].startswith("one-sided, k > 0 against k <= 0 at the 0.05 level")
    assert "MPEA: by paper; Texas A&M FCC: by the whole dataset" in r["Test"]
    assert r["Minimum evidence"] == ("30 records, 5 alloys with at least 2 grain sizes, 10 informative groups (papers "
                                     "or datasets that help estimate k), 10 residual degrees of freedom")
    assert r["Checks"].startswith("9 sensitivity sets")
    assert run_view.NOT_APPLICABLE not in r["Checks"]
    assert "with alloys matched at 1 at.%;" in r["Checks"] and "atomic percent" not in r["Checks"]


def test_every_setting_is_read_from_the_plan_not_from_a_default():
    """A planted plan: every value changed from the profile's shows on the panel."""
    plan = reference_plan(1)
    plan["rules"].update(room_temperature_min=18.0, room_temperature_max=28.0, same_alloy_decimals=2,
                         duplicate_tolerance=0.05, min_grain_sizes=3, survivor_source_order=["tamu_fcc", "mpea"])
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "batch"}]
    plan["model"]["alpha"] = 0.01
    plan["sufficiency"].update(min_records=31, min_alloys=6, min_groups=11, min_resid_df=12)
    plan["exclusion_rules"] = [{"rule": "grain_size_range", "min": 0.2}]
    plan["scope"]["test_type"] = ["compression"]
    r = rows(plan)
    assert r["Test conditions"] == "test type compression; room temperature, 18 to 28 °C"
    assert r["Same alloy"] == "compositions identical after rounding to 0.01 at.%"
    assert "within 5%" in r["Same record"] and "within 2%" not in r["Same record"]
    assert "in the order Texas A&M FCC then MPEA" in r["Same record"]
    assert "at least 3 distinct grain sizes" in r["Model"]
    assert "at the 0.01 level" in r["Test"] and "Texas A&M FCC: by batch" in r["Test"]
    assert r["Minimum evidence"].startswith("31 records, 6 alloys with at least 3 grain sizes, 11 informative groups")
    assert r["Minimum evidence"].endswith("12 residual degrees of freedom")
    assert "below 0.2 µm" in r["Exclusions"]


def test_a_rule_the_plan_does_not_hold_is_not_shown():
    plan = reference_plan(1)
    plan["eligibility_rules"] = [e for e in plan["eligibility_rules"]
                                 if e["rule"] not in ("invalid_value", "conflict_unresolved")]
    r = rows(plan)
    assert "impossible" not in r["Exclusions"]
    assert "left out" not in r["Same record"]


def test_use_what_is_available_says_the_minimums_are_waived_never_the_validity_checks():
    plan = reference_plan(1)
    plan["sufficiency"]["option"] = "use_available"
    assert rows(plan)["Minimum evidence"].startswith("use what is available: the minimums are waived, never the "
                                                     "validity checks")


def test_a_band_other_than_room_temperature_shows_the_plans_own_range():
    plan = reference_plan(1)
    plan["scope"]["temperature_band"] = ["elevated"]
    plan["rules"]["temperature_range"] = {"min": 1000.0, "max": 1000.0}
    assert rows(plan)["Test conditions"] == "test type tension; elevated, 1000 °C"


def test_the_pilot_plan_lists_only_the_runs_own_sources_and_marks_the_texas_am_set_not_applicable():
    """Run 11's shape: MPEA and the extracted records; the plan still names Texas A&M (the reference plan's)."""
    r = rows(with_pilot_sources(reference_plan(1), PILOT), PILOT)
    assert "Texas A&M" not in r["Test"] and "MPEA: by paper; Extracted records: by paper" in r["Test"]
    assert "in the order MPEA then Extracted records" in r["Same record"]
    assert "with Texas A&M grouped by its six batches (not applicable to this run's sources)" in r["Checks"]
    assert r["Checks"].count(run_view.NOT_APPLICABLE) == 1


def test_a_set_marked_by_source_changes_only_that_sources_grouping():
    """`SET_SOURCE` agrees with the change `eligibility.settings` makes."""
    plan = reference_plan(1)
    base = eligibility.settings(plan)
    for key, source in run_view.SET_SOURCE.items():
        changed = eligibility.settings(plan, key)
        assert {k for k in base.grouping if base.grouping[k] != changed.grouping[k]} == {source}
        assert changed == base.__class__(**{**base.__dict__, "grouping": changed.grouping})


def test_the_completed_run_shows_the_plan_panel_below_the_results_statement(world):
    engine, url, runs = world
    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
    text_ = plain(page)
    at = [text_.index(x) for x in ("Results statement (written by code)", "Plan (fixed at the rules lock)",
                                   "Explanation by the Analyst")]
    assert at == sorted(at)
    panel = text_[at[1]:at[2]]
    shown = run_view.run_page(engine, runs["sufficient"])
    assert "Hypothesis " + shown["claim"] in panel
    assert "Question as tested: " + shown["question_as_tested"]["text"] in panel
    for row in shown["plan_rows"]:
        assert f"{row['part']} {row['setting']}" in panel
    assert shown["checkpoints"]["rules_lock"]["fingerprint"] in panel
    assert "(grain size in µm)<sup>-1/2</sup>" in page


def test_a_run_before_the_rules_lock_has_no_plan_panel(world):
    engine, url, runs = world
    page = plain(signed_in(engine, url).get(f"/runs/{runs['waiting']}").text)
    assert "Plan (fixed at the rules lock)" not in page
    assert run_view.run_page(engine, runs["waiting"])["plan_rows"] is None
