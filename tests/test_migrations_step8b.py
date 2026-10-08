"""Step 8b: migration 0006 (approved by the owner on 2026-10-07, subject to the second-model review).

0001 to 0005 untouched; no earlier function is replaced (each new rule is its own function and
trigger, named to fire after the earlier one on the same table and event); up, down, up gives the
same schema; the downgrade refuses while a query uses another option than the default; a failed
upgrade changes nothing. Then the rules 0006 adds, each with an allowed and a refused case:
- the query's sufficiency option (owner, A2): on the version, fixed once submitted, the original's on a
  narrower question, and the plan's must equal it;
- partly sufficient (owner, A5): only with no plan, no stored record and a done narrowing decision of
  partly sufficient; and no plan after such a decision;
- the Critic's class from its fixed list and its reason bounded (owner, A7)."""
from __future__ import annotations

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX
from hypocurate.db import models
from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import FP, World
from test_migrations import assert_schema_is_empty, snapshot
from test_migrations_step6 import body

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module


def m0006():
    """Migration 0006's module (looked up when a test runs, so each test fails alone where it is absent)."""
    return SCRIPTS.get_revision("0006").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


# --- the migration -------------------------------------------------------------------------------

def test_0006_is_the_head_and_follows_0005():
    assert migrate.head_revision() == "0006" and m0006().down_revision == "0005"


def test_0006_replaces_no_earlier_function():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m0006().FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m0006().FUNCTIONS)


@pytest.mark.parametrize("table, earlier", [("hypothesis_version", "hc_version_insert"),
                                            ("hypothesis_version", "hc_version_update"),
                                            ("plan", "hc_plan_insert"), ("run", "hc_run_update"),
                                            ("run", "hc_run_insert")])
# (run UPDATE also covers hc_run_update_statement_version, fix round 1)
def test_each_new_trigger_fires_after_the_earlier_one_on_its_table(table, earlier):
    """PostgreSQL fires BEFORE triggers in name order: 0001's messages keep their priority."""
    names = [t for tb, _, t, _ in m0006().CHECKED if tb == table and t.startswith(earlier)]
    assert names and all(n > earlier for n in names)


def test_the_critic_classes_are_the_codes_of_the_vocabulary():
    assert m0006().CRITIC_CLASSES == models.CRITIC_CLASSES == tuple(sorted(CRITIC_CLASSES))
    assert m0006().CRITIC_REASON_MAX == models.CRITIC_REASON_MAX == CRITIC_REASON_MAX


def test_up_down_up_restores_0005(engine):
    migrate.upgrade(engine, "0005")
    at_0005 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0005")
    assert snapshot(engine) == at_0005
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0005")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_partly_sufficient() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0005"


def test_the_downgrade_refuses_while_a_query_uses_another_option(db):
    w = World(db)
    w.draft(sufficiency="use_available")
    before = snapshot(db)
    with pytest.raises(Exception, match="0006 is in use"):
        migrate.downgrade(db, "0005")
    assert snapshot(db) == before and migrate.current_revision(db) == "0006"


# --- the query's sufficiency option (A2) ---------------------------------------------------------

def test_a_version_without_an_option_uses_the_default(w):
    """The previous release's code inserts versions without the option."""
    vid = w.val("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                "VALUES (:h, 1, 'claim', :d) RETURNING id", h=w.hypothesis(), d=w.domain["grain_size_strengthening"])
    assert w.val("SELECT sufficiency_option FROM hypothesis_version WHERE id = :v", v=vid) == "fixed_minimum"


def test_the_option_comes_from_the_fixed_list(w):
    with pytest.raises(IntegrityError, match="ck_hypothesis_version_sufficiency_option"):
        w.draft(sufficiency="power_based")


def test_the_option_can_change_while_a_draft_and_never_after(w):
    vid = w.draft()
    w.run_sql("UPDATE hypothesis_version SET sufficiency_option = 'use_available' WHERE id = :v", v=vid)
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET sufficiency_option = 'fixed_minimum' WHERE id = :v",
               "sufficiency option is fixed once the version is submitted", v=vid)


def test_a_narrower_question_has_its_originals_option(w):
    original = partly_run(w, sufficiency="use_available")
    h = w.hypothesis(narrower_of=original)
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 1, 'narrower', :d)", "the sufficiency option of its original",
               h=h, d=w.domain["grain_size_strengthening"])
    vid = w.draft(hypothesis=h, sufficiency="use_available")
    w.rejected("UPDATE hypothesis_version SET sufficiency_option = 'fixed_minimum' WHERE id = :v",
               "the sufficiency option of its original", v=vid)


@pytest.mark.parametrize("query, plan, refused", [("fixed_minimum", "fixed_minimum", False),
                                                  ("use_available", "use_available", False),
                                                  ("fixed_minimum", "use_available", True),
                                                  ("use_available", "fixed_minimum", True)])
def test_the_plans_option_is_the_querys(w, query, plan, refused):
    rid = w.running(sufficiency=query)
    if refused:
        with pytest.raises(IntegrityError, match="the plan's sufficiency option is the query's"):
            w.lock(rid, option=plan)
    else:
        w.lock(rid, option=plan)
        assert w.val("SELECT sufficiency_option FROM plan WHERE run_id = :r", r=rid) == plan


def test_the_plans_own_option_check_still_refuses_an_unknown_option(w):
    """Behind the new trigger (which fires first, before any CHECK), 0001's CHECK still holds:
    reached here with the new trigger disabled in this transaction only."""
    rid = w.running()
    with w.e.begin() as conn:
        conn.execute(text("ALTER TABLE plan DISABLE TRIGGER hc_plan_insert_query"))
        with pytest.raises(IntegrityError, match="ck_plan_sufficiency_option"):
            with conn.begin_nested():
                conn.execute(text("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, "
                                  "min_alloys, min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'power_based', "
                                  "30, 5, 10, 10)"), dict(r=rid, fp=FP))
        conn.execute(text("ALTER TABLE plan ENABLE TRIGGER hc_plan_insert_query"))


# --- partly sufficient (A5) ---------------------------------------------------------------------

def narrowing(w, rid, result="partly_sufficient", status="done"):
    """A code stage result of the narrowing decision (role NULL), as `writes.code_stage` writes it."""
    sid = w.stage(rid, "narrowing", None)
    if status != "running":
        w.run_sql("UPDATE stage_result SET status = :st, finished_at = now(), output = CAST(:o AS jsonb) "
                  "WHERE id = :s", st=status, o=f'{{"result": "{result}"}}', s=sid)
    return sid


def complete_partly(w, rid):
    w.complete(rid, "partly_sufficient", level=1)


def partly_run(w, sufficiency="fixed_minimum"):
    rid = w.running(sufficiency=sufficiency)
    narrowing(w, rid)
    complete_partly(w, rid)
    return rid


def test_a_run_completes_as_partly_sufficient_with_its_narrowing_decision_and_no_plan(w):
    rid = partly_run(w)
    assert w.rows("SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("completed", "partly_sufficient", None, 1)]


@pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
def test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient(w, shape):
    rid = w.running()
    if shape == "proceed":
        narrowing(w, rid, result="proceed")
    elif shape == "running":
        narrowing(w, rid, status="running")
    elif shape == "failed":
        narrowing(w, rid, status="failed")
    if shape == "running":  # a running stage blocks any end first (0001); finish it as failed instead
        w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE run_id = :r", r=rid)
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "evidence_level = 1 WHERE id = :r", "partly sufficient needs a narrowing decision", r=rid)


def test_partly_sufficient_is_refused_for_a_run_with_a_plan(w):
    rid = w.running()
    w.lock(rid)
    narrowing(w, rid)  # written after the lock by direct SQL: the database still refuses the outcome
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "evidence_level = 1 WHERE id = :r", "partly sufficient is only for a run with no plan", r=rid)


def test_no_plan_is_locked_after_a_narrowing_decision_of_partly_sufficient(w):
    rid = w.running()
    narrowing(w, rid)
    with pytest.raises(IntegrityError, match="no plan is locked after a narrowing decision of partly sufficient"):
        w.lock(rid)


def test_a_narrowing_decision_to_proceed_allows_the_lock(w):
    rid = w.running()
    narrowing(w, rid, result="proceed")
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("outcome", ["insufficient", "sufficient"])
def test_other_outcomes_are_unaffected_by_the_new_rule(w, outcome):
    """'insufficient' completes as before; 'sufficient' keeps 0001's own refusal."""
    rid, sets, _ = w.frozen()
    if outcome == "insufficient":
        w.complete(rid, "insufficient", level=1)
        assert w.val("SELECT outcome FROM run WHERE id = :r", r=rid) == "insufficient"
    else:
        w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'sufficient', "
                   "verdict = 'supported', evidence_level = 6 WHERE id = :r", "exactly one pooled result", r=rid)


# --- the Critic's class and reason (A7) -----------------------------------------------------------

def a_flag(w):
    rid = w.locked()
    return rid, w.val("INSERT INTO flag (run_id, kind, category) VALUES (:r, 'values_disagree', "
                      "'differ beyond tolerance') RETURNING id", r=rid)


@pytest.mark.parametrize("cls", sorted(CRITIC_CLASSES))
def test_each_critic_class_is_accepted(w, cls):
    _, fid = a_flag(w)
    w.run_sql("UPDATE flag SET critic_class = :c, critic_reason = 'same DOI and composition', "
              "classified_at = now() WHERE id = :f", c=cls, f=fid)


@pytest.mark.parametrize("cls, reason, match", [
    ("agrees", None, "ck_flag_critic_class"),
    ("same_measurement", "x" * 301, "ck_flag_critic_reason"),
    ("same_measurement", "   ", "ck_flag_critic_reason"),
])
def test_a_class_outside_the_list_or_an_unbounded_reason_is_refused(w, cls, reason, match):
    _, fid = a_flag(w)
    w.rejected("UPDATE flag SET critic_class = :c, critic_reason = :r, classified_at = now() WHERE id = :f",
               match, c=cls, r=reason, f=fid)


def test_a_reason_needs_a_class(w):
    _, fid = a_flag(w)
    w.rejected("UPDATE flag SET critic_reason = 'a reason' WHERE id = :f", "ck_flag_critic_reason", f=fid)


def test_a_class_without_a_reason_is_allowed(w):
    _, fid = a_flag(w)
    w.run_sql("UPDATE flag SET critic_class = 'cannot_tell', classified_at = now() WHERE id = :f", f=fid)


# --- a narrower question's run (fix round 1, finding 1; owner F-Q1: the backstop is in 0006) -------------------

BODY = {"model": "hall_petch", "scope": {"phase_class": ["FCC"]}, "alpha": 0.05}


def narrower_version(w, original):
    """A dispatched version of a narrower question of `original` (same sources as the world's runs)."""
    return w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1)


def partly_original(w, body=BODY, sources=("mpea", "tamu_fcc")):
    rid = w.running()
    w.partly(rid, narrower_plan=body, sources=sources)
    return rid


def test_a_narrower_questions_run_must_use_the_stored_plan(w):
    vid = narrower_version(w, partly_original(w))
    w.rejected("INSERT INTO run (hypothesis_version_id, fixed_plan) VALUES (:v, false)",
               "a narrower question's run uses the plan stored by its original's narrowing decision", v=vid)
    rid = w.run(vid=vid)
    assert w.val("SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True


def test_a_narrower_questions_plan_equal_to_the_stored_narrower_plan_is_locked(w):
    vid = narrower_version(w, partly_original(w))
    rid = w.running(vid=vid)
    w.lock(rid, content={"hypothesis_version": vid, **BODY})
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("content", [{}, {"model": "hall_petch", "scope": {"phase_class": ["BCC"]}, "alpha": 0.05},
                                     {"hypothesis_version": 0, **BODY, "alpha": 0.1}])
def test_a_narrower_questions_plan_other_than_the_stored_one_is_refused(w, content):
    vid = narrower_version(w, partly_original(w))
    rid = w.running(vid=vid)
    with pytest.raises(IntegrityError, match="is the narrower plan stored by its original's narrowing decision"):
        w.lock(rid, content=content)


def test_a_narrower_questions_plan_is_refused_when_the_original_stored_no_narrower_plan(w):
    original = w.running()
    w.narrowing(original, output={"sources": w.counted(("mpea", "tamu_fcc"))})
    w.complete(original, "partly_sufficient", level=1)
    vid = narrower_version(w, original)
    rid = w.running(vid=vid)
    with pytest.raises(IntegrityError, match="is the narrower plan stored by its original's narrowing decision"):
        w.lock(rid, content={"hypothesis_version": vid, **BODY})


@pytest.mark.parametrize("counted", ["other_fingerprint", "fewer_sources"])
def test_a_narrower_questions_plan_is_refused_on_other_source_versions(w, counted):
    """B1 at the database: the run's source versions are those the original's narrowing counts were taken on."""
    original = w.running()
    sources = w.counted(("mpea", "tamu_fcc"))
    if counted == "other_fingerprint":
        sources[0]["version_fingerprint"] = "f" * 64
    else:
        sources = sources[:1]
    w.narrowing(original, output={"narrower_plan": BODY, "sources": sources})
    w.complete(original, "partly_sufficient", level=1)
    vid = narrower_version(w, original)
    rid = w.running(vid=vid)
    with pytest.raises(IntegrityError, match="the source versions its original's narrowing counts were taken on"):
        w.lock(rid, content={"hypothesis_version": vid, **BODY})


def test_the_source_versions_are_compared_whatever_their_stored_order(w):
    original = w.running()
    w.narrowing(original, output={"narrower_plan": BODY, "sources": w.counted(("tamu_fcc", "mpea"))})
    w.complete(original, "partly_sufficient", level=1)
    vid = narrower_version(w, original)
    rid = w.running(vid=vid)
    w.lock(rid, content={"hypothesis_version": vid, **BODY})
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


def test_an_ordinary_runs_plan_is_unaffected_by_the_narrower_rule(w):
    rid = w.running()
    assert w.val("SELECT fixed_plan FROM run WHERE id = :r", r=rid) is False
    w.lock(rid, content={"anything": 1})
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


# --- the statement's format version on the run (fix round 1, owner 2026-10-07) -----------------------------------

def test_the_format_version_is_recorded_only_in_the_update_that_completes_the_run(w):
    rid = w.running()
    w.rejected("UPDATE run SET statement_format_version = 1 WHERE id = :r",
               "the statement format version is recorded when the run completes", r=rid)
    w.narrowing(rid)
    w.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
              "evidence_level = 1, statement_format_version = 1 WHERE id = :r", r=rid)
    assert w.val("SELECT statement_format_version FROM run WHERE id = :r", r=rid) == 1
    w.rejected("UPDATE run SET statement_format_version = 2 WHERE id = :r", "a completed run is final", r=rid)  # 0001


def test_a_run_completed_without_a_format_version_keeps_none(w):
    """The previous release's code completes runs without it (0006 keeps working with it): the statement then says
    the version was not recorded."""
    rid = w.running()
    w.partly(rid)
    assert w.val("SELECT statement_format_version FROM run WHERE id = :r", r=rid) is None
    w.rejected("UPDATE run SET statement_format_version = 1 WHERE id = :r", "a completed run is final", r=rid)  # 0001


def test_a_failed_run_never_gets_a_format_version(w):
    rid = w.running()
    w.rejected("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x', statement_format_version = 1 "
               "WHERE id = :r", "the statement format version is recorded when the run completes", r=rid)


def test_the_format_version_is_positive(w):
    rid = w.running()
    w.narrowing(rid)
    with pytest.raises(IntegrityError, match="ck_run_statement_format_version"):
        w.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
                  "evidence_level = 1, statement_format_version = 0 WHERE id = :r", r=rid)
