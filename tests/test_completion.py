"""Step 7: the function that copies the stored decision onto the run only copies (owner, 2026-10-05).

It refuses, and logs the refusal, when the stored decision is missing or belongs to a different
freeze fingerprint; it computes nothing; the database checks the copy again.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, completion
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.writes import Refused, code_stage
from stats_world import audit_codes, rows_of, run_on, small_rows, val


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def run_row(engine, rid):
    return rows_of(engine, "SELECT status, outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r",
                   r=rid)[0]


def test_the_decision_is_copied_unchanged(engine):
    rid = run_on(engine, small_rows(6, sizes=(1.0, 4.0, 16.0), papers=12, repeats=2), mins=(30, 5, 10, 10))
    stored = analysis.run_statistics(engine, rid)["decision"]
    assert stored["state"] == "sufficient"
    copied = completion.copy_decision(engine, rid)
    assert copied == stored
    assert tuple(run_row(engine, rid)) == ("completed", stored["outcome"], stored["verdict"], stored["exploratory"],
                                           stored["evidence_level"])


def test_it_refuses_a_missing_decision_and_logs_it(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_missing"
    assert audit_codes(engine, rid, "copy_decision") == ["decision_missing"]
    assert run_row(engine, rid).status == "running"


def test_it_refuses_a_decision_of_another_freeze_and_logs_it(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    decision = st.decision(None, {"sufficiency": {"option": "fixed_minimum"}}, "0" * 64)
    with engine.begin() as conn:
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        code_stage(conn, rid, "statistics", {}, {"decision": decision})
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_not_current"
    assert audit_codes(engine, rid, "copy_decision") == ["decision_not_current"]
    assert run_row(engine, rid).status == "running"


def test_a_run_with_a_freeze_refuses_a_decision_without_one(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    with engine.begin() as conn:
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        code_stage(conn, rid, "statistics", {}, {"decision": st.decision(None, {"sufficiency": {
            "option": "fixed_minimum"}}, None)})
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "decision_not_current"


def test_it_copies_what_is_stored_and_never_recomputes(engine, monkeypatch):
    """A stored decision that differs from what the statistics would give (here: 'not supported'
    on data that support the claim) is copied as stored. The copy reads only the stored decision."""
    rid = run_on(engine, small_rows(6, sizes=(1.0, 4.0, 16.0), papers=12, repeats=2))
    real = st.decision

    def altered(pooled, plan, fp):
        return {**real(pooled, plan, fp), "verdict": "not_supported"}

    monkeypatch.setattr(st, "decision", altered)
    stored = analysis.run_statistics(engine, rid)
    monkeypatch.undo()
    assert stored["analyses"][0]["significant"] is True and stored["decision"]["verdict"] == "not_supported"
    completion.copy_decision(engine, rid)
    assert run_row(engine, rid).verdict == "not_supported"


def test_it_refuses_before_the_analysis_stage_and_after_completion(engine):
    pw.registered(engine, ("mpea",))
    rid = pw.locked_run(engine, sources=("mpea",))
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "stage_mismatch"
    done = run_on(engine, small_rows(3, papers=3), register=False)
    analysis.run_statistics(engine, done)
    completion.copy_decision(engine, done)
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, done)
    assert refused.value.code == "stage_mismatch"


def test_the_database_checks_the_copy_again(engine, monkeypatch):
    """A stored decision claiming 'sufficient' for a withheld run is refused by the database
    (hc_run_update: under the fixed option, a sufficient outcome needs the minimums met)."""
    rid = run_on(engine, small_rows(3, papers=3))
    real = st.decision

    def claims_sufficient(pooled, plan, fp):
        return {**real(pooled, plan, fp), "outcome": "sufficient", "verdict": "supported", "evidence_level": 6}

    monkeypatch.setattr(st, "decision", claims_sufficient)
    analysis.run_statistics(engine, rid)
    monkeypatch.undo()
    with pytest.raises(Refused) as refused:
        completion.copy_decision(engine, rid)
    assert refused.value.code == "rejected_by_database"
    assert run_row(engine, rid).status == "running"


def test_a_completed_run_needs_its_evidence_level(engine):
    """Review (smaller point): the evidence level is required on every completed run."""
    from sqlalchemy.exc import IntegrityError
    pw.registered(engine, ("mpea",))
    rid = pw.dispatched_run(engine, sources=("mpea",))
    with pytest.raises(IntegrityError, match="ck_run_evidence_level_iff_completed"):
        with engine.begin() as conn:
            conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' "
                              "WHERE id = :r"), dict(r=rid))
