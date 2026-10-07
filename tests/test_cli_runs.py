"""Step 8b, milestone 7: criteria 14.1 and 14.3 from the command line (`hypocurate run | dispatch | show`). Each
run executes in the guarded process; the model provider is the local stub, reached through the environment the
guarded child inherits (no live call)."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate import cli
from hypocurate.db.engine import make_engine
from test_orchestrator import BCC, BCC_CLAIM, FCC_CLAIM, PARTLY, PARTLY_CLAIM, planner_body, responder


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database, monkeypatch, stub):
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.setenv("ANTHROPIC_API_BASE", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", sp.DUMMY_KEY)
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def hc(capsys, *argv):
    code = cli.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def report_of(out: str) -> dict:
    """The run's report: the JSON after the dispatch line."""
    first, rest = out.split("\n", 1)
    return {**json.loads(first), "report": json.loads(rest)}


def guard_refusals(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT detail FROM audit_log WHERE run_id = :r AND NOT allowed "
                                 "AND detail->>'code' = 'file_guard'"), dict(r=run_id)).scalars().all()


def test_14_1a_run_with_the_fixed_plan_and_show_it(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    assert code == 0, err
    r = report_of(out)
    assert r["query"].startswith("Q-") and r["report"]["status"] == "completed" and r["report"]["outcome"] == "sufficient"
    assert guard_refusals(engine, r["run"]) == []
    code, out, err = hc(capsys, "show", str(r["run"]))
    shown = json.loads(out)
    assert shown["outcome"] == "sufficient in the sources searched"
    assert shown["verdict"] == "supported under the stated model, in the sources searched"
    pooled = next(x for x in shown["results"] if x["scope"] == "pooled")
    assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
    assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
    assert shown["explanation_label"] == "model explanation; numbers checked against the run record"
    assert shown["tokens_and_cost"] is not None


def test_14_1b_run_with_the_planner(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "sufficient" and "planner" in r["report"]["stages"]
    assert guard_refusals(engine, r["run"]) == []


def test_14_3_the_bcc_claim_from_the_command_line(engine, stub, capsys):
    stub.respond(responder(BCC))
    code, out, err = hc(capsys, "run", BCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "insufficient"
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    assert shown["outcome"] == "insufficient in the sources searched" and shown["verdict"] is None
    assert shown["results"] == [] and shown["nothing_found"] == "missing_evidence"
    assert shown["evidence_level_wording"] == "no dataset frozen"


def test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line(engine, stub, capsys):
    stub.respond(responder(PARTLY))
    code, out, err = hc(capsys, "run", PARTLY_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "partly_sufficient"
    number = r["report"]["narrower_question"]
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    assert shown["outcome"] == "partly sufficient in the sources searched" and shown["narrower_question"] == number
    assert shown["evidence_level_wording"] == "original question not tested; a narrower question was proposed"
    code, out, err = hc(capsys, "dispatch", number, "--by", "Ada Reviewer")
    n = report_of(out)
    assert code == 0 and n["report"]["outcome"] == "sufficient" and n["report"]["stages"][0] == "fixed plan"
    narrower = json.loads(hc(capsys, "show", str(n["run"]))[1])
    assert narrower["narrower_question_of"] == r["query"] and narrower["plan"] == "from the narrowing decision"


@pytest.fixture
def small(migrated_database, monkeypatch, stub):
    """A source below the fixed minimums: 3 alloys at two grain sizes, from 3 papers (or 1 paper)."""
    from stats_world import small_rows
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.setenv("ANTHROPIC_API_BASE", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", sp.DUMMY_KEY)
    e = make_engine(migrated_database)

    def register(papers):
        pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=papers))})
    yield e, register
    e.dispose()


@pytest.mark.parametrize("papers, expected", [
    # Passes both validity checks, below the minimums: exploratory under 'use what is available', insufficient
    # (withheld) under the fixed minimum.
    (3, {"use_available": ("sufficient", True, 5), "fixed_minimum": ("insufficient", False, 3)}),
    # One paper: validity check 2 fails, so neither option gives a verdict.
    (1, {"use_available": ("insufficient", False, 4), "fixed_minimum": ("insufficient", False, 3)}),
])
def test_14_3_the_sufficiency_option_on_data_below_the_minimums(small, stub, capsys, papers, expected):
    engine, register = small
    register(papers)
    stub.respond(responder())
    got = {}
    for option in ("use_available", "fixed_minimum"):
        code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea", "--fixed-plan", "--sufficiency", option,
                            "--by", "Ada Reviewer")
        assert code == 0, err
        r = report_of(out)
        with engine.connect() as conn:
            got[option] = tuple(conn.execute(text("SELECT outcome, exploratory, evidence_level FROM run WHERE id = :r"),
                                             dict(r=r["run"])).one())
        shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
        if got[option][1]:
            assert shown["label"] == "exploratory"
        if option == "fixed_minimum":
            assert shown["results"] == [] and shown["label"] == "data found; not enough to test"
    assert got == expected


def test_an_unsupported_domain_is_refused_and_the_message_says_why(engine, stub, capsys):
    code, out, err = hc(capsys, "run", "Fatigue life falls with porosity", "--sources", "mpea", "--domain", "fatigue",
                        "--by", "Ada Reviewer")
    assert code == 1 and "dispatch blocked: the confirmed domain is not supported yet" in err
    assert stub.requests == []


def test_a_run_needs_a_named_reviewer(engine, capsys):
    with pytest.raises(SystemExit) as exited:
        cli.main(["run", FCC_CLAIM, "--sources", "mpea"])
    assert exited.value.code == 2
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea", "--by", "  ")
    assert code == 1 and "reviewer_missing" in err


def test_show_an_unknown_run(engine, capsys):
    code, out, err = hc(capsys, "show", "999999")
    assert code == 1 and "no run 999999" in err


def test_14_3_a_source_that_cannot_be_read_is_a_failed_search_not_missing_evidence(small, stub, capsys):
    from stats_world import small_rows
    engine, _ = small
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3)), "tamu_fcc": b"not a workbook"})
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--sufficiency",
                        "use_available", "--by", "Ada Reviewer")
    r = report_of(out)
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    kinds = {s["source"]: (s["search_status"], s["kind"]) for s in shown["sources"]}
    assert kinds["tamu_fcc"] == ("failed", "failed_search")
    assert kinds["mpea"] == ("searched", None)  # its records are in the analysed set
    assert shown["outcome"] == "sufficient in the sources searched"


def test_14_1_the_controlled_duplicates_in_a_marked_test_run(engine, stub, capsys):
    """The constructed extract enters only a run marked as a test; its overlapping records are flagged, kept in
    the store and counted once; the run carries the test-run label."""
    pw.registered(engine, ("controlled_duplicates",))
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,controlled_duplicates", "--fixed-plan",
                        "--test-data", "--by", "Ada Reviewer")
    assert code == 0, err
    rid = report_of(out)["run"]
    with engine.connect() as conn:
        flags = conn.execute(text("SELECT kind, count(*) FROM flag WHERE run_id = :r GROUP BY kind"), dict(r=rid)).all()
        stored = conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"), dict(r=rid)).scalar()
        label = conn.execute(text("SELECT DISTINCT test_run_label FROM analysis_result WHERE run_id = :r"),
                             dict(r=rid)).scalars().all()
        once = conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r AND rule = 'duplicate_counted_once'"),
                            dict(r=rid)).scalar()
    assert dict(flags).get("exact_duplicate", 0) + dict(flags).get("possible_duplicate", 0) > 0
    assert once > 0 and stored > once  # kept in the store, counted once
    assert label == ["test run: includes constructed data"]
    assert any("[[ ## classification ## ]]" in r["raw"].decode() for r in stub.requests)  # the Critic was asked
