"""Step 9a: migration 0007 (owner's approval of the step 9 plan, 2026-10-08, subject to the second-model review).

The run waits at the rules lock for a named person (owner, Q1): a new run status 'waiting'; an append-only
`rules_confirmation` bound to the plan that will be locked (its fingerprint) and to the source versions the
narrowing counts were taken on (owner's addition A1); the plan backstop; the spending ceiling stored on the run
(R5); one narrower question per original run. 0001's `hc_run_update` is the only earlier function replaced, and
only its list of status changes differs. Up, down, up gives the same schema; the downgrade refuses while anything
0007 adds is in use; a failed upgrade changes nothing."""
from __future__ import annotations

import json

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import FP, World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
OTHER_FP = "e" * 64
CONTENT = '{"question": "shown"}'


def m0007():
    """Migration 0007's module (looked up when a test runs, so each test fails alone where it is absent)."""
    return SCRIPTS.get_revision("0007").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


# --- helpers: a Planner run and a narrower question's run, each up to the wait ---------------------------------

def planner_run(w, narrowing="proceed", sources=("mpea", "tamu_fcc")):
    """A running run with a done Planner stage and code's narrowing decision (the stored source versions)."""
    rid = w.running()
    planner = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=planner)
    narrowed = None
    if narrowing is not None:
        narrowed = w.narrowing(rid, result=narrowing, output={"sources": w.counted(sources)})
    return rid, planner, narrowed


def narrower_run(w, sources=("mpea", "tamu_fcc")):
    original = w.running()
    w.partly(original, narrower_plan={"model": "hall_petch"}, sources=sources)
    vid = w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1)
    return w.running(vid=vid)


def wait(w, rid):
    w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)


def confirm(w, rid, planner=None, narrowed=None, fp=FP, by="Ada Reviewer"):
    return w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                 "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, CAST(:c AS jsonb), 'shown') "
                 "RETURNING id", r=rid, b=by, fp=fp, p=planner, n=narrowed, c=CONTENT)


def confirmed(w, rid, planner=None, narrowed=None, fp=FP):
    """Waiting, confirmed, then running again: the rules may now be locked."""
    wait(w, rid)
    confirm(w, rid, planner, narrowed, fp)
    w.run_sql("UPDATE run SET status = 'running' WHERE id = :r", r=rid)


# --- the migration ------------------------------------------------------------------------------------------

def test_0007_is_the_head_and_follows_0006():
    assert migrate.head_revision() == "0007" and m0007().down_revision == "0006"


def test_the_only_earlier_function_replaced_is_hc_run_update_and_only_its_status_changes_differ():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert {f.split("(")[0] for f in m0007().FUNCTION_NAMES} & earlier == set()
    original = next(f for f in M0001.FUNCTIONS if "FUNCTION hc_run_update()" in f)
    assert original.count(m0007().TRANSITIONS_0001) == 1
    assert m0007().RUN_UPDATE_0007 == original.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION").replace(
        m0007().TRANSITIONS_0001, m0007().TRANSITIONS_0007)
    assert m0007().RUN_UPDATE_0001 == original.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")
    assert m0007().TRANSITIONS_0007.startswith(m0007().TRANSITIONS_0001[:-1])
    assert "waiting" in m0007().TRANSITIONS_0007 and "waiting" not in m0007().TRANSITIONS_0001


@pytest.mark.parametrize("table, event, earlier", [("run", "UPDATE", "hc_run_update"), ("run", "INSERT", "hc_run_insert"),
                                                   ("plan", "INSERT", "hc_plan_insert")])
def test_each_new_trigger_fires_after_the_earlier_ones_on_its_table(table, event, earlier):
    """PostgreSQL fires BEFORE triggers of one table and event in name order: the earlier rules' messages keep their
    priority. (Second review round: compared per table and event; the run INSERT case added with its new trigger.)"""
    m6 = SCRIPTS.get_revision("0006").module
    before = [earlier] + [t for tb, ev, t, _ in m6.CHECKED if tb == table and ev == event and t.startswith(earlier)]
    names = [t for tb, ev, t, _ in m0007().CHECKED if tb == table and ev == event]
    assert names and all(n > b for n in names for b in before)


def test_up_down_up_restores_0006(engine):
    migrate.upgrade(engine, "0006")
    at_0006 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0006")
    assert snapshot(engine) == at_0006  # 0001's hc_run_update and ck_run_status exactly as before
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0006")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_waiting() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0006"


@pytest.mark.parametrize("use", ["waiting", "confirmation", "ceiling"])
def test_the_downgrade_refuses_while_0007_is_in_use(db, use):
    w = World(db)
    if use == "ceiling":
        vid = w.dispatched()
        w.val("INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, 0.5) RETURNING id", v=vid)
    else:
        rid, planner, narrowed = planner_run(w)
        wait(w, rid)
        if use == "confirmation":
            confirm(w, rid, planner, narrowed)
            w.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x' WHERE id = :r", r=rid)
    before = snapshot(db)
    with pytest.raises(Exception, match="0007 is in use"):
        migrate.downgrade(db, "0006")
    assert snapshot(db) == before and migrate.current_revision(db) == "0007"


# --- waiting (owner, Q1, Q5) --------------------------------------------------------------------------------

def test_a_planner_run_waits_after_a_narrowing_decision_to_proceed(w):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_a_narrower_questions_run_waits_before_its_lock(w):
    rid = narrower_run(w)
    wait(w, rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


@pytest.mark.parametrize("shape, match", [
    ("no_narrowing", "waits only after code's narrowing decision to proceed"),
    ("partly", "waits only after code's narrowing decision to proceed"),
    ("fixed_plan", "only a run whose plan comes from the Planner or a narrower question waits"),
    ("no_planner", "only a run whose plan comes from the Planner or a narrower question waits"),
    ("locked", "a run waits only before its rules lock"),
    ("stage_running", "a run waits only when no stage is running and no model call is open"),
    ("call_open", "a run waits only when no stage is running and no model call is open"),
])
def test_a_run_waits_only_at_the_rules_lock_of_a_plan_that_needs_a_person(w, shape, match):
    if shape == "fixed_plan":
        rid = w.running(fixed_plan=True)
    elif shape == "no_planner":
        rid = w.running()
    elif shape in ("no_narrowing", "partly"):
        rid, _, _ = planner_run(w, narrowing=None if shape == "no_narrowing" else "partly_sufficient")
    else:
        rid, _, _ = planner_run(w)
        if shape == "locked":  # a plan written past the backstop (disabled for this case only)
            w.run_sql("ALTER TABLE plan DISABLE TRIGGER hc_plan_insert_rules_confirmed")
            w.lock(rid)
            w.run_sql("ALTER TABLE plan ENABLE TRIGGER hc_plan_insert_rules_confirmed")
    if shape == "stage_running":
        w.stage(rid, "critic", "critic")
    if shape == "call_open":
        rid = w.running(agents=True)
        planner = w.stage(rid, "planner", "planner")
        w.call(rid, planner)
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=planner)
        w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", match, r=rid)


def test_a_run_never_waits_again_after_its_confirmation(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed)
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", "a run waits once", r=rid)


@pytest.mark.parametrize("sql, match", [
    ("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, 'curation', NULL, 1)", "running"),
    ("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
     "min_resid_df) VALUES (:r, '{}', '" + FP + "', 'fixed_minimum', 4, 1, 2, 1)", "a plan is locked only while"),
])
def test_nothing_is_written_to_a_waiting_run(w, sql, match):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    w.rejected(sql, match, r=rid)


def test_a_waiting_run_goes_on_only_with_a_confirmation(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    w.rejected("UPDATE run SET status = 'running' WHERE id = :r", "goes on only after a person confirms", r=rid)
    confirm(w, rid, planner, narrowed)
    w.run_sql("UPDATE run SET status = 'running' WHERE id = :r", r=rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "running"


def test_a_waiting_run_can_fail_and_never_completes(w):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient', "
               "evidence_level = 1 WHERE id = :r", "run status cannot go from waiting to completed", r=rid)
    w.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'cancelled: x' WHERE id = :r",
              r=rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"


def test_a_queued_run_cannot_wait(w):
    rid = w.run()
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", "run status cannot go from queued to waiting", r=rid)


# --- the confirmation (owner, Q1, A1, A2) -------------------------------------------------------------------

def test_a_confirmation_is_recorded_with_the_databases_time_and_is_append_only(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    cid = confirm(w, rid, planner, narrowed)
    assert w.rows("SELECT confirmed_by, plan_fingerprint FROM rules_confirmation WHERE id = :c", c=cid) == [
        ("Ada Reviewer", FP)]
    w.rejected("UPDATE rules_confirmation SET confirmed_by = 'Someone Else' WHERE id = :c", "append-only", c=cid)
    w.rejected("DELETE FROM rules_confirmation WHERE id = :c", "append-only", c=cid)
    w.rejected("TRUNCATE rules_confirmation CASCADE", "append-only")


def test_the_database_sets_the_confirmation_time(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    cid = w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, confirmed_at, plan_fingerprint, "
                "planner_stage_result_id, narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', "
                "'2000-01-01', :fp, :p, :n, '{}', 'shown') RETURNING id", r=rid, fp=FP, p=planner, n=narrowed)
    assert w.val("SELECT confirmed_at > '2001-01-01' FROM rules_confirmation WHERE id = :c", c=cid)


def test_only_a_waiting_run_is_confirmed_and_only_once(w):
    rid, planner, narrowed = planner_run(w)
    with pytest.raises(IntegrityError, match="only a run waiting for confirmation is confirmed"):
        confirm(w, rid, planner, narrowed)
    wait(w, rid)
    confirm(w, rid, planner, narrowed)
    with pytest.raises(IntegrityError):
        confirm(w, rid, planner, narrowed)


@pytest.mark.parametrize("by", ["", "   ", "x" * 201])
def test_a_confirmation_names_a_person(w, by):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    with pytest.raises(IntegrityError, match="ck_rules_confirmation_named"):
        confirm(w, rid, planner, narrowed, by=by)


def test_the_confirmed_fingerprint_has_the_plan_fingerprint_format(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    with pytest.raises(IntegrityError, match="ck_rules_confirmation_fingerprint_format"):
        confirm(w, rid, planner, narrowed, fp="not-a-fingerprint")


@pytest.mark.parametrize("shape", ["no_stages", "other_planner", "earlier_narrowing", "other_run"])
def test_a_planner_runs_confirmation_names_its_planner_stage_and_its_latest_narrowing_decision(w, shape):
    rid, planner, narrowed = planner_run(w)
    if shape == "earlier_narrowing":  # a later narrowing row: the confirmation must name the latest
        later = w.stage(rid, "narrowing", None, attempt=2)
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = (SELECT output FROM "
                  "stage_result WHERE id = :n) WHERE id = :s", n=narrowed, s=later)
        assert later > narrowed
    wait(w, rid)
    if shape == "no_stages":
        planner, narrowed = None, None
    elif shape == "other_planner":
        other, p2, _ = planner_run(w)
        planner = p2
    elif shape == "other_run":
        other, p2, n2 = planner_run(w)
        planner, narrowed = p2, n2
    with pytest.raises(IntegrityError, match="names the run's done Planner stage and its latest narrowing decision"):
        confirm(w, rid, planner, narrowed)


def test_a_narrower_questions_confirmation_names_no_stage(w):
    rid = narrower_run(w)
    wait(w, rid)
    other, planner, narrowed = planner_run(w)
    with pytest.raises(IntegrityError, match="a narrower question's confirmation names no Planner or narrowing"):
        confirm(w, rid, planner, narrowed)
    confirm(w, rid)
    assert w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("path", ["planner", "narrower"])
@pytest.mark.parametrize("counted", ["other_fingerprint", "fewer_sources"])
def test_a_confirmation_is_refused_when_the_counted_source_versions_are_not_the_runs(w, path, counted):
    """Owner's addition A1, at the database: a run never locks on a narrowing decision taken on other versions."""
    sources = w.counted(("mpea", "tamu_fcc"))
    if counted == "other_fingerprint":
        sources[0]["version_fingerprint"] = "f" * 64
    else:
        sources = sources[:1]
    if path == "planner":
        rid, planner, _ = planner_run(w, narrowing=None)
        narrowed = w.narrowing(rid, result="proceed", output={"sources": sources})
    else:
        original = w.running()
        w.narrowing(original, output={"narrower_plan": {}, "sources": sources})
        w.complete(original, "partly_sufficient", level=1)
        rid = w.running(vid=w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1))
        planner = narrowed = None
    wait(w, rid)
    with pytest.raises(IntegrityError, match="the source versions the narrowing counts were taken on"):
        confirm(w, rid, planner, narrowed)


def test_a_confirmation_holds_its_content_and_the_text_shown(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    for content, shown in (("[]", "shown"), ('{"a": 1}', "")):
        with pytest.raises(IntegrityError, match="ck_rules_confirmation_content_and_text"):
            w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                  "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, CAST(:c AS jsonb), :s) "
                  "RETURNING id", r=rid, fp=FP, p=planner, n=narrowed, c=content, s=shown)


# --- the plan backstop --------------------------------------------------------------------------------------

def test_a_planner_runs_plan_needs_its_confirmation(w):
    rid, _, _ = planner_run(w)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


def test_a_planner_runs_plan_must_be_the_confirmed_plan(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed, fp=OTHER_FP)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


def test_the_confirmed_plan_is_locked(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed)
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


def test_a_narrower_questions_plan_needs_its_confirmation(w):
    rid = narrower_run(w)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid, content={"model": "hall_petch"})


@pytest.mark.parametrize("kind", ["fixed_plan", "no_planner_stage"])
def test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation(w, kind):
    """Guard: a fixed-plan run (14.1a) never waits (owner, Q5); a run with no Planner stage (the step 6-8 test
    worlds, which lock a plan directly) keeps its premises (the scoping stated in the step 9a summary)."""
    rid = w.running(fixed_plan=True) if kind == "fixed_plan" else w.running()
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


def test_a_failed_planner_attempt_still_needs_the_confirmation(w):
    rid = w.running()
    w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE run_id = :r", r=rid)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


# --- the spending ceiling (R5) and one narrower question per run ----------------------------------------------

def test_the_spending_ceiling_is_stored_at_dispatch_and_never_changed(w):
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, 0.5) RETURNING id", v=vid)
    assert float(w.val("SELECT spending_ceiling FROM run WHERE id = :r", r=rid)) == 0.5
    w.rejected("UPDATE run SET spending_ceiling = 1 WHERE id = :r", "what a run records at dispatch cannot change",
               r=rid)
    w.rejected("UPDATE run SET spending_ceiling = NULL WHERE id = :r", "what a run records at dispatch cannot change",
               r=rid)


@pytest.mark.parametrize("ceiling", [0, -1, "'Infinity'"])
def test_the_spending_ceiling_is_a_positive_finite_amount(w, ceiling):
    vid = w.dispatched()
    with pytest.raises(IntegrityError, match="ck_run_spending_ceiling"):
        w.val(f"INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, {ceiling}) RETURNING id", v=vid)


def test_a_run_has_at_most_one_narrower_question(w):
    original = w.running()
    w.partly(original)
    w.hypothesis(narrower_of=original)
    with pytest.raises(IntegrityError, match="uq_hypothesis_narrower_of_run_id"):
        w.hypothesis(narrower_of=original)


# --- fix round 1, finding 2: source freshness enforced by the database, serialised with registration -------------

def seal_newer(w, key="mpea"):
    v = w.new_version(key, label="newer")
    w.add_file(v, f"{key}-newer.csv", f"{key},newer\n".encode())
    w.seal(v)
    return v


@pytest.mark.parametrize("path", ["planner", "narrower"])
@pytest.mark.parametrize("change", ["newer_version", "new_source"])
def test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing(w, path, change):
    """Direct SQL (the review's case): the run's own versions still match the narrowing, but the registered sources
    no longer do."""
    if path == "planner":
        rid, planner, narrowed = planner_run(w)
    else:
        rid, planner, narrowed = narrower_run(w), None, None
    wait(w, rid)
    if change == "newer_version":
        seal_newer(w)
        match = "a source the run uses has a newer sealed version"
    else:
        w.add_source("later_source")
        match = "a source was registered after the run's dispatch"
    with pytest.raises(IntegrityError, match=match):
        confirm(w, rid, planner, narrowed)
    assert w.val("SELECT count(*) FROM rules_confirmation") == 0


def test_a_newer_version_of_a_source_the_run_does_not_use_is_no_change(w):
    """Guard (owner's wording: 'any source the run uses'): a newer version of a source the query did not choose does
    not refuse the confirmation; the code's check (`confirmation.source_changes`) looks at chosen sources too."""
    rid = w.running(sources=("mpea",))
    planner = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=planner)
    narrowed = w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea",))})
    wait(w, rid)
    seal_newer(w, "tamu_fcc")
    confirm(w, rid, planner, narrowed)
    assert w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


def named_engine(db, name):
    from sqlalchemy import create_engine
    return create_engine(db.url, connect_args={"application_name": name, "options": "-c TimeZone=UTC"})


def _blocked(engine, application_name):
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name = :a AND "
                                 "wait_event_type = 'Lock'"), dict(a=application_name)).scalar() == 1


def test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses(db):
    """Two connections: a registration seals a newer version and has not committed; the confirmation waits for it
    (the shared lock), then sees the new version and is refused."""
    import threading
    import time
    w = World(db)
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    sealer = named_engine(db, "hc-test-sealer")
    confirmer = named_engine(db, "hc-test-confirmer")
    seal_conn = sealer.connect()
    tx = seal_conn.begin()
    v = seal_conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', "
                               "'2026-10-08') RETURNING id"), dict(s=w.source["mpea"])).scalar()
    from model_builder import sha, version_fingerprint
    data = b"mpea,newer\n"
    seal_conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'n.csv', :h, :c)"),
                      dict(v=v, h=sha(data), c=data))
    fp = version_fingerprint({"n.csv": data}, *w.settings(w.version["mpea"]))
    seal_conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"), dict(f=fp, v=v))
    outcome = {}

    def confirm_it():
        try:
            with confirmer.begin() as conn:
                conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, "
                                  "planner_stage_result_id, narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', "
                                  ":fp, :p, :n, '{}', 'x')"), dict(r=rid, fp=FP, p=planner, n=narrowed))
            outcome["result"] = "confirmed"
        except IntegrityError as error:
            outcome["result"] = str(error.orig)

    t = threading.Thread(target=confirm_it)
    t.start()
    deadline = time.time() + 10
    while not _blocked(db, "hc-test-confirmer") and time.time() < deadline:
        time.sleep(0.05)
    assert _blocked(db, "hc-test-confirmer"), "the confirmation did not wait for the seal"
    tx.commit()
    t.join(10)
    seal_conn.close()
    sealer.dispose()
    confirmer.dispose()
    assert "a source the run uses has a newer sealed version" in outcome["result"]


def test_a_confirmation_in_progress_holds_back_a_seal(db):
    """The other order: the confirmation holds the shared lock until it commits; the seal waits, then succeeds."""
    import threading
    import time
    w = World(db)
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    confirmer = named_engine(db, "hc-test-confirmer")
    sealer = named_engine(db, "hc-test-sealer")
    conf_conn = confirmer.connect()
    tx = conf_conn.begin()
    conf_conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                           "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, '{}', 'x')"),
                      dict(r=rid, fp=FP, p=planner, n=narrowed))
    v = w.new_version("mpea", label="newer")
    w.add_file(v, "mpea-newer.csv", b"mpea,newer\n")
    fp = w.fingerprint(v)
    done = {}

    def seal_it():
        with sealer.begin() as conn:
            conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
                         dict(f=fp, v=v))
        done["sealed"] = True

    t = threading.Thread(target=seal_it)
    t.start()
    deadline = time.time() + 10
    while not _blocked(db, "hc-test-sealer") and time.time() < deadline:
        time.sleep(0.05)
    assert _blocked(db, "hc-test-sealer"), "the seal did not wait for the confirmation"
    tx.commit()
    t.join(10)
    conf_conn.close()
    confirmer.dispose()
    sealer.dispose()
    assert done.get("sealed") and w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


def test_the_shared_lock_key_is_the_codes(engine):
    from hypocurate.pipeline import confirmation
    assert m0007().SOURCES_LOCK_KEY == confirmation.SOURCES_LOCK_KEY
    insert = next(f for f in m0007().FUNCTIONS if "hc_rules_confirmation_insert()" in f)
    lock = next(f for f in m0007().FUNCTIONS if "hc_sources_lock()" in f)
    assert f"pg_advisory_xact_lock({confirmation.SOURCES_LOCK_KEY})" in insert
    assert f"pg_advisory_xact_lock({confirmation.SOURCES_LOCK_KEY})" in lock


# --- fix round 1, finding 5: a "cancelled" failure only from queued or waiting ----------------------------------

@pytest.mark.parametrize("start, reason, allowed", [
    ("running", "cancelled: cancelled by Ada before it started", False),
    ("running", "cancelled:x", False),
    ("running", "worker stopped", True),
    ("queued", "cancelled: cancelled by Ada before it started", True),
    ("waiting", "cancelled: cancelled by Ada while waiting for confirmation of the question as tested", True),
])
def test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting(w, start, reason, allowed):
    """Direct SQL (the review's case): ordinary failures from running stay allowed."""
    if start == "queued":
        rid = w.run()
    elif start == "running":
        rid = w.running()
    else:
        rid, _, _ = planner_run(w)
        wait(w, rid)
    sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
    if allowed:
        w.run_sql(sql, f=reason, r=rid)
        assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    else:
        w.rejected(sql, "a run is cancelled only while it is queued or waiting", f=reason, r=rid)


# --- the owner's decision (2026-10-08): every new run stores its effective ceiling ---------------------------------

def test_a_run_dispatched_without_a_ceiling_stores_the_run_cap(w):
    """The database default (so a dispatch by the previous release's code stores it too) equals the code's cap."""
    from hypocurate.pipeline.agents import spend
    rid = w.run()
    assert w.val("SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == spend.RUN_CAP_USD
    assert m0007().CEILING_DEFAULT == str(spend.RUN_CAP_USD)


def test_the_downgrade_is_not_blocked_by_ceilings_equal_to_the_run_cap(db):
    """Only a ceiling below the run cap would be lost; one equal to it says no more than the cap."""
    w = World(db)
    w.run()
    migrate.downgrade(db, "0006")
    assert migrate.current_revision(db) == "0006"
    migrate.upgrade(db)


def test_an_explicit_null_ceiling_on_a_new_run_stores_the_run_cap(w):
    """Second review (2026-10-08): the default applies only when the column is left out; an insert trigger replaces
    an explicit NULL with the per-run cap, so no new run is stored without a ceiling, even by direct SQL."""
    from hypocurate.pipeline.agents import spend
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, NULL) RETURNING id", v=vid)
    assert w.val("SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == spend.RUN_CAP_USD
    w.rejected("UPDATE run SET spending_ceiling = NULL WHERE id = :r", "what a run records at dispatch cannot change",
               r=rid)
