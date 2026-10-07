"""Step 8b fix round 1, owner's decision A (with the owner's changes of 2026-10-07, F-Q2): the results statement.

Code writes a short fixed statement from the stored facts of every completed run, whether or not the Analyst
succeeded: the question as asked and as tested, the outcome and verdict wording, the evidence level, the model
sentence, the estimate with its unit and the four figures together, the spread of the slope information, one
sensitivity line, the calibration summary and the main cautions chosen by fixed rules. It is built from stored rows
whenever it is shown (`statement.build`), so it is present for every completed run and holds nothing a model wrote.
Every model call goes to the local stub provider.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, analyst_names, completion, orchestrator, queries, reading, statement
from stats_world import run_on, small_rows
from test_orchestrator import (BCC, BCC_CLAIM, FCC_CLAIM, PARTLY, PARTLY_CLAIM, planner_body, responder)

MPEA = "multi-principal-element (high-entropy) alloys"
TESTED_FIXED = (f"Question as tested ({reading.LABELS['fixed']}): yield strength against grain size, in {MPEA}; "
                "phase class FCC; test type tension; room temperature, 20 to 25 °C; excluding records with a grain size "
                "below 0.1 µm.")


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


@pytest.fixture
def bare(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def run_claim(engine, stub, claim=FCC_CLAIM, fixed_plan=False, analyst=None, planner_answer=None):
    kw = {"analyst": analyst} if analyst else {}
    stub.respond(responder(planner_answer, **kw))
    q = queries.create(engine, claim, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def stored_stats(engine, rid):
    with engine.connect() as conn:
        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'"),
                            dict(r=rid)).scalar()


def test_the_reference_run_s_statement(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    lines = statement.build(engine, report.run_id)["lines"]
    calibration = analyst_names.calibration_summary(stored_stats(engine, report.run_id)["analyses"][0]["calibration"],
                                                    0.05)
    assert lines == [
        f"Question as asked: {FCC_CLAIM}",
        TESTED_FIXED,
        "Outcome: sufficient in the sources searched. Verdict: supported under the stated model, in the sources "
        "searched.",
        "Evidence level: 6 (sufficient with a verdict).",
        analyst_names.MODEL_SENTENCE,
        "Pooled estimate: 424.9 MPa·µm^0.5, standard error 64.4 MPa·µm^0.5; an approximate, nominal, one-sided "
        "p ≈ 1.3e-6; 97 records on 22 alloys; from 20 informative groups, an effective number of groups of 3.94, a "
        "largest share of 38.7% and 19 degrees of freedom.",
        "The estimate is positive, the direction the claim describes.",
        "Spread of the slope information: an effective number of groups of 3.94 out of 20 informative groups; "
        "largest share 38.7%.",
        analyst_names.GROUP_DEFINITION,
        "Sensitivity: 9 of 9 sets in agreement with the pooled result; estimates from 393.5 MPa·µm^0.5 to "
        "432.4 MPa·µm^0.5.",
        calibration,
        "Main cautions:",
        f"  - {statement.ASSOCIATION}",
        f"  - {statement.OVER_CONFIDENT}",
        "  - Texas A&M FCC dataset (Mulukutla et al. 2026): not testable alone (too few groups).",
    ]
    assert calibration.count(analyst_names.display.INTERVAL_NOTE) == 1  # the interval described once (owner)


def test_the_statement_is_present_when_the_analyst_fails_and_holds_nothing_it_wrote(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True, analyst=lambda raw: "The data do not exist {outcome_wording}.")
    assert report.status == "completed" and report.explanation.startswith("explanation unavailable")
    built = statement.build(engine, report.run_id)
    assert built["lines"][0] == f"Question as asked: {FCC_CLAIM}" and "424.9 MPa·µm^0.5" in built["text"]
    assert "do not exist" not in built["text"]


def test_a_planner_run_s_statement_labels_the_planner_s_reading(engine, stub):
    report = run_claim(engine, stub, planner_answer=planner_body())
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[1].startswith(f"Question as tested ({reading.LABELS['planner']}): yield strength against grain size")
    assert reading.LABELS["planner"] == ("the Planner's reading of the claim; not verified by code and, in this "
                                         "version, not confirmed by a person")
    assert "test type tension (assumed: the claim does not state it)" in lines[1]


def test_nothing_frozen_shows_each_count_against_its_minimum_and_the_records_found_per_source(engine, stub):
    report = run_claim(engine, stub, claim=BCC_CLAIM, planner_answer=BCC)
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[2] == "Outcome: insufficient in the sources searched. No verdict."
    assert lines[3] == "Evidence level: 1 (no dataset frozen)."
    assert lines[4] == "Nothing was tested: no dataset was frozen (missing evidence)."
    assert lines[5] == ("Counts against the minimums: 0 of 30 records; 0 of 5 alloys with at least 2 grain sizes; "
                        "0 of 10 informative groups; no residual degrees of freedom (minimum 10).")
    with engine.connect() as conn:
        found = dict(conn.execute(text("SELECT s.key, count(*) FROM record r JOIN source_version sv ON sv.id = "
                                       "r.source_version_id JOIN source s ON s.id = sv.source_id WHERE "
                                       "r.extraction_run_id = :r GROUP BY s.key"), dict(r=report.run_id)).all())
    mpea = next(x for x in lines if x.startswith("  MPEA dataset"))
    assert mpea.startswith(f"  MPEA dataset (Borg et al. 2020): {found['mpea']:,} records found; ")
    assert "lack a grain size" in mpea and "lack a yield strength" in mpea
    assert lines[-1] == "Main cautions: none beyond those above."


def test_partly_sufficient_shows_the_counts_per_part_and_the_narrower_question_to_dispatch(engine, stub):
    report = run_claim(engine, stub, claim=PARTLY_CLAIM, planner_answer=PARTLY)
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[2] == ("Outcome: partly sufficient in the sources searched. The original question was not tested "
                        "and has no verdict.")
    assert lines[3] == "Evidence level: 1 (original question not tested; a narrower question was proposed)."
    parts = next(x for x in lines if x.startswith("Records with a grain size and the outcome"))
    assert "candidates before any eligibility decision" in parts and "cryogenic" in parts and ": 0" in parts
    assert lines[-1] == (f"Narrower question {report.narrower_question}: phase class FCC; test type tension; room "
                         "temperature. It is not run until a person dispatches it.")


@pytest.mark.parametrize("case", ["exploratory", "coefficient_only", "below_minimums"])
def test_the_other_kinds(bare, case):
    kw, option = {"exploratory": (dict(papers=3), "use_available"), "coefficient_only": (dict(papers=1), "use_available"),
                  "below_minimums": (dict(papers=3, base=7311.0), "fixed_minimum")}[case]
    rid = run_on(bare, small_rows(3, **kw), option=option, agents=("analyst",))
    analysis.run_statistics(bare, rid)
    completion.copy_decision(bare, rid)
    lines = statement.build(bare, rid)["lines"]
    text_ = "\n".join(lines)
    if case == "exploratory":
        assert lines[2].startswith("Outcome: sufficient in the sources searched (exploratory). Verdict: supported")
        assert lines[3] == "Evidence level: 5 (use what is available with a minimum missed (exploratory))."
        assert f"  - {statement.EXPLORATORY}" in lines and f"  - {statement.ASSOCIATION}" in lines
        assert any(x.startswith("Spread of the slope information: an effective number of groups of 3.00 out of 3 "
                                "informative groups; largest share 33.3%.") for x in lines)
    elif case == "coefficient_only":
        assert lines[2] == "Outcome: insufficient in the sources searched. No verdict."
        assert any(x.startswith("Pooled estimate: 298.5 MPa·µm^0.5, the coefficient only (insufficient groups): no "
                                "uncertainty, no p-value and no verdict; 6 records on 3 alloys") for x in lines)
        assert "Spread of the slope information" not in text_ and "p ≈" not in text_
        assert lines[-1] == "Main cautions: none beyond those above."
    else:
        assert lines[2] == ("Outcome: insufficient in the sources searched (data found; not enough to test). "
                            "No verdict.")
        assert "No estimate is shown: the minimums were not met." in lines
        assert ("Counts against the minimums: 6 of 30 records; 3 of 5 alloys with at least 2 grain sizes; 3 of 10 "
                "informative groups; 2 of 10 residual degrees of freedom.") in lines
        assert analyst_names.MODEL_SENTENCE not in lines and "MPa·µm^0.5" not in text_   # nothing estimated shown
        assert any(x.startswith("  MPEA dataset (Borg et al. 2020): 6 records found") for x in lines)


def test_a_failed_run_has_no_statement(engine, stub):
    report = run_claim(engine, stub, planner_answer=planner_body(domain_matches=False))
    assert report.status == "failed" and statement.build(engine, report.run_id) is None
