"""Step 8b fix round 1, owner's decision A (with the owner's changes of 2026-10-07, F-Q2): the results statement.

Code writes a short fixed statement from the stored facts of every completed run, whether or not the Analyst
succeeded: the question as asked and as tested, the outcome and verdict wording, the evidence level, the model
sentence, the estimate with its unit and the four figures together, the spread of the slope information, one
sensitivity line, the calibration summary and the main cautions chosen by fixed rules. It is built from stored rows
whenever it is shown (`statement.build`), so it is present for every completed run and holds nothing a model wrote.
Every model call goes to the local stub provider.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

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
        f"Statement format {statement.FORMAT_VERSION}.",   # completed under the current format: nothing more
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
    assert lines[-2:] == ["Main cautions: none beyond those above.", f"Statement format {statement.FORMAT_VERSION}."]


def test_partly_sufficient_shows_the_counts_per_part_and_the_narrower_question_to_dispatch(engine, stub):
    report = run_claim(engine, stub, claim=PARTLY_CLAIM, planner_answer=PARTLY)
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[2] == ("Outcome: partly sufficient in the sources searched. The original question was not tested "
                        "and has no verdict.")
    assert lines[3] == "Evidence level: 1 (original question not tested; a narrower question was proposed)."
    parts = next(x for x in lines if x.startswith("Records with a grain size and the outcome"))
    assert "candidates before any eligibility decision" in parts and "cryogenic" in parts and ": 0" in parts
    assert lines[-1] == f"Statement format {statement.FORMAT_VERSION}."  # owner, after the re-check
    assert lines[-2] == (f"Narrower question {report.narrower_question}: phase class FCC; test type tension; room "
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
        # Re-check (owner): the spread is shown whenever its figures exist, also without inference (was: absent).
        assert ("Spread of the slope information: an effective number of groups of 1.00 out of 1 informative groups; "
                "largest share 100.0%.") in lines and "p ≈" not in text_
        assert lines[-2:] == ["Main cautions: none beyond those above.", f"Statement format {statement.FORMAT_VERSION}."]
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


# --- a pure function of the stored rows, with a format version (owner, 2026-10-07) ------------------------------

FIXTURE = Path(__file__).parent / "fixtures" / "statement_facts.json"
# The rendered text of every case in FIXTURE under the current format. A change of wording changes this fingerprint
# and must come with a new FORMAT_VERSION. Only the current format is rendered (owner, after the re-check): a run
# completed under an earlier format is shown with the current wording and a line naming its own format.
RENDERED_CURRENT = (2, "43e07bf2cdcf01076fa38386b2f0e87bb376eec2227cd27aca7c24d05297f312")


def facts_of(engine, rid):
    with engine.connect() as conn:
        return statement.facts(conn, rid)


def test_the_same_stored_rows_give_the_same_text_whatever_the_record_ids(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    vid = pw.version_of(engine, report.run_id)
    again = pw.run_of_version(engine, vid, ("mpea", "tamu_fcc"), agents=("planner", "critic", "analyst"))
    assert orchestrator.run(engine, again, client_options=sp.client_options(stub)).outcome == "sufficient"
    with engine.connect() as conn:
        ids = [set(conn.execute(text("SELECT id FROM record WHERE extraction_run_id = :r"), dict(r=r)).scalars())
               for r in (report.run_id, again)]
    assert ids[0] and not ids[0] & ids[1]                                   # other records, other ids
    assert statement.build(engine, again)["text"] == statement.build(engine, report.run_id)["text"]
    f = facts_of(engine, again)
    assert not [i for i in ids[1] if f'"id": {i}' in json.dumps(f)]          # no record identity in the facts
    assert not set(statement.IDENTITY_KEYS) & set(json.dumps(f).replace('"', " ").split())


def test_the_facts_never_hold_the_stored_lists_of_record_ids(bare):
    rid = run_on(bare, small_rows(3, papers=3, base=7311.0), agents=("analyst",))
    out = analysis.run_statistics(bare, rid)
    completion.copy_decision(bare, rid)
    assert [i for e in out["analyses"] for i in e.get("records_found") or []]   # stored with the statistics
    assert "records_found" not in json.dumps(facts_of(bare, rid))


def test_the_order_of_the_stored_results_does_not_change_the_text(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    f = facts_of(engine, report.run_id)
    expected = statement.render(f)
    rng = random.Random(3)
    for _ in range(5):
        shuffled = json.loads(json.dumps(f))
        rng.shuffle(shuffled["statistics"]["analyses"])
        rng.shuffle(shuffled["gap"]["sources"])
        shuffled["found"] = dict(reversed(list(shuffled["found"].items())))
        assert statement.render(shuffled) == expected


def test_each_completion_records_the_format_version_and_show_gives_it(engine, stub):
    from hypocurate import cli_runs
    for report in (run_claim(engine, stub, fixed_plan=True),
                   run_claim(engine, stub, claim=PARTLY_CLAIM, planner_answer=PARTLY)):
        with engine.connect() as conn:
            recorded = conn.execute(text("SELECT statement_format_version FROM run WHERE id = :r"),
                                    dict(r=report.run_id)).scalar()
        assert recorded == statement.FORMAT_VERSION
        shown = cli_runs.show(engine, report.run_id)
        assert shown["statement_format"] == {"current": statement.FORMAT_VERSION, "recorded": statement.FORMAT_VERSION}
        assert shown["statement"] == statement.build(engine, report.run_id)["lines"]


def rendered_fingerprint() -> str:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    text_ = "\n\n".join(f"{name}\n" + "\n".join(statement.render(f)) for name, f in sorted(cases.items()))
    return hashlib.sha256(text_.encode("utf-8")).hexdigest()


ALL_KINDS = ("sufficient", "planner", "exploratory", "coefficient_only", "coefficient_only_concentrated",
             "below_minimums", "not_fitted", "nothing_frozen", "partly_sufficient")


def test_the_wording_of_the_current_format_is_pinned():
    """Every case of the fixture rendered with the current code has the fingerprint pinned for the current format;
    changing any wording fails this test until FORMAT_VERSION is raised and the fingerprint replaced."""
    assert "records_found" not in FIXTURE.read_text(encoding="utf-8")
    assert RENDERED_CURRENT == (statement.FORMAT_VERSION, rendered_fingerprint())


def test_the_fixture_covers_every_outcome_and_evidence_level_and_each_renders():
    """Re-check: the fixture claimed every outcome but lacked the not-fitted one (whose rendering raised)."""
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(cases) == set(ALL_KINDS)
    assert {f["evidence_level"] for f in cases.values()} == {1, 2, 3, 4, 5, 6}
    assert {f["outcome"] for f in cases.values()} == {"sufficient", "insufficient", "partly_sufficient"}
    reasons = {(f.get("statistics") or {}).get("analyses", [{}])[0].get("inference_reason") for f in cases.values()
               if (f.get("statistics") or {}).get("analyses")}
    assert {"coefficient_not_fitted", "insufficient_groups", "evidence_concentrated"} <= reasons
    for name, f in cases.items():
        lines = statement.render(f)
        assert lines[0].startswith("Question as asked: ") and lines[-1].startswith(("Statement format ", "This run ",
                                                                                     "The format ")), name


def test_a_run_whose_coefficient_cannot_be_fitted_shows_no_number_of_it():
    f = json.loads(FIXTURE.read_text(encoding="utf-8"))["not_fitted"]
    lines = statement.render(f)
    text_ = "\n".join(lines)
    assert "Evidence level: 2 (coefficient cannot be fitted)." in lines
    assert ("No coefficient could be fitted (coefficient not fitted): no estimate, no uncertainty, no p-value and no "
            "verdict; of the 4 records in the set, 4 could not be used (1 alloys).") in lines
    assert "MPa·µm^0.5" not in text_ and "p ≈" not in text_ and "Pooled estimate" not in text_
    assert analyst_names.MODEL_SENTENCE not in lines


def test_a_concentrated_coefficient_only_result_shows_its_spread():
    """Re-check: the spread is shown whenever its figures exist, compared only with the run's own count."""
    f = json.loads(FIXTURE.read_text(encoding="utf-8"))["coefficient_only_concentrated"]
    lines = statement.render(f)
    assert any(x.startswith("Pooled estimate: ") and "the coefficient only (evidence concentrated): no uncertainty, "
               "no p-value and no verdict" in x for x in lines)
    assert "Spread of the slope information: an effective number of groups of 1.00 out of 2 informative groups; " \
           "largest share 100.0%." in lines


@pytest.mark.parametrize("recorded, tail", [
    (None, ["Statement format {v}.", "The format this run was completed under was not recorded."]),
    (1, ["Statement format {v}.", "This run was completed under format 1."]),
    ("current", ["Statement format {v}."])])
def test_the_statement_is_always_in_the_current_format_and_says_when_the_run_was_under_another(recorded, tail):
    """Owner, after the re-check: the current format always; the run's own format named when it differs."""
    f = json.loads(FIXTURE.read_text(encoding="utf-8"))["sufficient"]
    f["recorded_format_version"] = statement.FORMAT_VERSION if recorded == "current" else recorded
    v = statement.FORMAT_VERSION
    assert v != 1
    lines = statement.render(f)
    assert lines[-len(tail):] == [x.format(v=v) for x in tail]
    assert lines[:-len(tail)] == statement.render({**f, "recorded_format_version": v})[:-1]


@pytest.mark.parametrize("case", ALL_KINDS)
def test_every_kind_renders_the_same_whatever_the_order_of_its_stored_lists(case):
    """Mutation f35 (fix round 1): the order test above uses a run with an estimate, which lists no sources' records;
    here every kind, the nothing-frozen one with two sources, has each stored list reversed."""
    f = json.loads(FIXTURE.read_text(encoding="utf-8"))[case]
    expected = statement.render(f)
    flipped = json.loads(json.dumps(f))
    for path in (("statistics", "analyses"), ("gap", "sources")):
        node = flipped
        for k in path[:-1]:
            node = node.get(k) or {}
        if isinstance(node.get(path[-1]), list):
            node[path[-1]] = list(reversed(node[path[-1]]))
    flipped["found"] = dict(reversed(list((flipped.get("found") or {}).items())))
    if case == "nothing_frozen":
        assert len(f["gap"]["sources"]) == 2 and flipped["gap"]["sources"] != f["gap"]["sources"]
    assert statement.render(flipped) == expected
