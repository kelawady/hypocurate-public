"""Step 9a: the run waits at the rules lock for a named person (owner's approval of the step 9 plan, 2026-10-08: Q1,
Q5, additions A1 and A2, and the go for 9a: no bulk or automatic confirmation; the label once confirmed).

Whole runs through the orchestrator, every model call to the local stub (as tests/test_orchestrator.py)."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import pathlib

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate import cli_runs
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries

LABEL = "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on "


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


def run(engine, rid, stub):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def proceed(engine, rid, stub):
    return orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def waiting(engine, stub, body=None, claim=to.FCC_CLAIM):
    stub.respond(to.responder(body or to.planner_body()))
    rid = to.dispatched(engine, claim=claim)
    report = run(engine, rid, stub)
    assert report.status == "waiting", report
    return rid


def narrower_waiting(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    original = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    assert run(engine, original, stub).outcome == "partly_sufficient"
    number = cli_runs.show(engine, original)["narrower_question"]
    vid = queries.submitted_version(engine, number)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    rid = queries.dispatch(engine, vid)
    before = len(stub.requests)
    assert run(engine, rid, stub).status == "waiting"
    assert len(stub.requests) == before  # a narrower question's run never asks the Planner
    return rid, original


def newer_version(engine, key="mpea"):
    """A newer sealed version of a registered source (a new file), as a later registration would add."""
    from model_builder import sha, version_fingerprint
    with engine.begin() as conn:
        src = conn.execute(text("SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = :k"),
                           dict(k=key)).one()
        vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', "
                                "'2026-10-08') RETURNING id"), dict(s=src.id)).scalar_one()
        data = b"newer,data\n"
        conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'x.csv', "
                          ":h, :c)"), dict(v=vid, h=sha(data), c=data))
        fp = version_fingerprint({"x.csv": data}, src.source_type, src.data_kind, src.grouping_unit)
        conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
                     dict(f=fp, v=vid))


# --- the wait (Q1, Q5) --------------------------------------------------------------------------------------

def test_a_planner_run_waits_before_its_rules_lock_and_nothing_more_is_done(engine, stub):
    rid = waiting(engine, stub)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT string_agg(stage, ',' ORDER BY id) FROM stage_result WHERE run_id = :r", r=rid) == \
        "planner,narrowing"
    assert len(stub.requests) == 1  # the Planner only
    assert cli_runs.show(engine, rid)["waiting_for"] == confirmation.WAITING_FOR


def test_a_waiting_run_that_no_one_confirmed_is_left_as_it_is(engine, stub):
    rid = waiting(engine, stub)
    for again in (run, proceed):
        report = again(engine, rid, stub)
        assert (report.status, report.failure) == ("waiting", None)
    assert len(stub.requests) == 1
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_a_fixed_plan_run_never_waits(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert run(engine, rid, stub).status == "completed"
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0


def test_a_narrower_questions_run_waits_and_goes_on_once_confirmed(engine, stub):
    rid, _ = narrower_waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert proceed(engine, rid, stub).status == "completed"


def test_once_confirmed_the_run_locks_exactly_the_confirmed_plan_and_completes(engine, stub):
    rid = waiting(engine, stub)
    stored = confirmation.confirm(engine, rid, by="Ada Reviewer")
    report = proceed(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "sufficient")
    assert one(engine, "SELECT fingerprint FROM plan WHERE run_id = :r", r=rid) == \
        stored["content"]["plan_fingerprint"] == \
        one(engine, "SELECT plan_fingerprint FROM rules_confirmation WHERE run_id = :r", r=rid)


def test_the_planner_is_not_asked_again_after_the_wait(engine, stub):
    rid = waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    proceed(engine, rid, stub)
    planner_requests = [r for r in stub.requests if "[[ ## plan ## ]]" in r["raw"].decode("utf-8", "replace")]
    assert len(planner_requests) == 1
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 1


# --- what is shown and stored (A2) --------------------------------------------------------------------------

def test_confirm_shows_every_item_and_stores_exactly_the_text_shown(engine, stub):
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    stored = confirmation.confirm(engine, rid, by="Ada Reviewer", shown=content)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT content, shown, confirmed_by FROM rules_confirmation WHERE run_id = :r"),
                           dict(r=rid)).one()
    assert row.shown == words == stored["shown"] == confirmation.render(row.content)  # byte for byte
    assert hashlib.sha256(row.shown.encode()).digest() == hashlib.sha256(words.encode()).digest()
    assert row.content == content and row.confirmed_by == "Ada Reviewer"
    tested = content["question_as_tested"]
    for item in (to.FCC_CLAIM, tested["text"], tested["label"], "Narrowed: no", "Candidate records per claim part",
                 "alloy class:", "phase class: FCC (as the claim states)", "test type: tension",
                 "temperature band: room temperature", "Outcome: yield strength against grain size",
                 "Exclusion rules: excluding records with a grain size below 0.1 µm",
                 "Sufficiency option: fixed minimum (minimums: 30 records",
                 "Sources: mpea version", "Cost so far: $", "Plan to be locked: fingerprint " + content["plan_fingerprint"]):
        assert item in words, item
    assert content["cost_so_far"]["calls"] == 1


def test_the_narrower_questions_confirmation_shows_what_was_narrowed_and_why(engine, stub):
    rid, original = narrower_waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                         "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=original)
    assert f"Narrowed: this is the narrower question of {number}" in words
    assert "Why: code found no candidate record in the sources searched for temperature band cryogenic" in words
    assert "Original scope:" in words and "Narrower scope:" in words
    assert content["narrowing"]["narrowed"] is True
    assert content["planner_stage_result_id"] is None and content["narrowing_stage_result_id"] is None


@pytest.mark.parametrize("change", ["exclusion", "stated", "cost"])
def test_the_content_changes_when_any_of_its_inputs_changes(engine, stub, change):
    first = confirmation.show(engine, waiting(engine, stub))[0]
    if change == "exclusion":
        body = to.planner_body(exclusion_rules=[{"rule": "grain_size_range", "min": 0.2}])
    elif change == "stated":
        body = to.planner_body(stated={"alloy_class": True, "phase_class": True, "test_type": True,
                                       "temperature_band": False})
    else:  # the Planner's first answer cannot be read: one corrected request, two calls in this run's record
        body = to.planner_body()
        stub.queue(sp.reply("not the answer form"))
    rid = waiting(engine, stub, body=body)
    second = confirmation.show(engine, rid)[0]
    differing = {k for k in first if first[k] != second[k]} - {"run", "query", "planner_stage_result_id",
                                                                "narrowing_stage_result_id"}
    expected = {"exclusion": {"exclusion_rules", "plan_fingerprint", "question_as_tested"},
                "stated": {"scope_parts", "question_as_tested"}, "cost": {"cost_so_far"}}[change]
    assert expected <= differing, differing


def test_a_confirmation_is_refused_when_what_was_shown_is_no_longer_current(engine, stub):
    rid = waiting(engine, stub)
    content, _ = confirmation.show(engine, rid)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer", shown={**content, "cost_so_far": {}})
    assert refused.value.code == "content_changed"
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0


# --- the sources while the run waits (A1) -------------------------------------------------------------------

def test_a_newer_version_registered_while_the_run_waits_refuses_the_confirmation(engine, stub):
    rid = waiting(engine, stub)
    before = one(engine, "SELECT array_agg(source_version_id ORDER BY source_id) FROM run_source WHERE run_id = :r",
                 r=rid)
    newer_version(engine, "mpea")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert (refused.value.code, refused.value.reason) == (
        "sources_changed", "mpea has a newer version since this run's narrowing; cancel this run and dispatch the "
                           "query again")
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    # The run's own versions never change (0001): they are those recorded at dispatch.
    assert one(engine, "SELECT array_agg(source_version_id ORDER BY source_id) FROM run_source WHERE run_id = :r",
               r=rid) == before


def test_a_source_registered_while_the_run_waits_refuses_the_confirmation(engine, stub):
    rid = waiting(engine, stub)
    pw.registered(engine, ("controlled_duplicates",))
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.reason == ("controlled_duplicates was registered since this run's narrowing; cancel this run "
                                    "and dispatch the query again")


def test_the_unchanged_sources_are_confirmed(engine, stub):
    rid = waiting(engine, stub)
    with engine.connect() as conn:
        assert confirmation.source_changes(conn, rid) == []
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


# --- one run, one named person; the label (owner, 2026-10-08) -----------------------------------------------

@pytest.mark.parametrize("by", ["", "   ", None, "x" * 201])
def test_a_confirmation_names_the_person(engine, stub, by):
    rid = waiting(engine, stub)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by=by)
    assert refused.value.code == "name_required"


def test_only_a_waiting_run_is_confirmed_and_only_once(engine, stub):
    stub.respond(to.responder())
    fixed = to.dispatched(engine, fixed_plan=True)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, fixed, by="Ada Reviewer")
    assert refused.value.code == "not_waiting"
    rid = waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "already_confirmed"


def test_a_cancelled_waiting_run_is_not_confirmed(engine, stub):
    rid = waiting(engine, stub)
    queries.cancel(engine, rid, by="Ada Reviewer")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "not_waiting"


def test_no_code_confirms_in_bulk_or_by_itself():
    """No bulk or automatic confirmation in step 9 (owner, 2026-10-08): `confirm` takes one run and one name, and
    the only callers in the package are the command line's `confirm` command and, from step 10a (owner's approved
    plan, 2026-10-11), the web page's confirm action; step 10a adds the shown content's fingerprint (addition 2)."""
    params = list(inspect.signature(confirmation.confirm).parameters)
    assert params == ["engine", "run_id", "by", "shown", "shown_fingerprint"]
    package = pathlib.Path(confirmation.__file__).parents[1]
    callers = []
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "confirm" \
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "confirmation":
                callers.append(path.name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "confirm":
                callers.append(path.name)
    assert sorted(callers) == ["app.py", "cli_runs.py"], callers
    source = pathlib.Path(cli_runs.__file__).read_text(encoding="utf-8")
    assert "INSERT INTO rules_confirmation" not in source
    inserts = [p.name for p in package.rglob("*.py") if "INSERT INTO rules_confirmation" in p.read_text(encoding="utf-8")]
    assert inserts == ["confirmation.py"]


def test_once_confirmed_the_question_as_tested_says_by_whom_and_when(engine, stub):
    rid = waiting(engine, stub)
    before = cli_runs.show(engine, rid)["question_as_tested"]["label"]
    assert before == "the Planner's reading of the claim; not verified by code and, in this version, not confirmed " \
                     "by a person"
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    after = cli_runs.show(engine, rid)["question_as_tested"]["label"]
    assert after.startswith(LABEL) and after.endswith(" UTC")
    proceed(engine, rid, stub)
    assert cli_runs.show(engine, rid)["question_as_tested"]["label"] == after


# --- added after the mutation checks (c03, c06, o04) --------------------------------------------------------

def test_a_running_run_is_refused_by_codes_own_check(engine, stub):
    """Mutation c03: code refuses a run that is not waiting itself (the database's refusal is the backstop)."""
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, client_options=sp.client_options(stub)).answer)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert (refused.value.code, refused.value.reason) == (
        "not_waiting", f"run {rid} is not waiting for confirmation (it is running)")


def test_the_cost_shown_is_the_runs_counted_and_reported_cost(engine, stub):
    """Mutation c06: the cost so far is the run's own total, counted as the caps count it."""
    from decimal import Decimal
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    with engine.connect() as conn:
        cap, reported = conn.execute(text("SELECT cap_cost, reported_cost FROM model_call_totals_by_run WHERE run_id = "
                                          ":r"), dict(r=rid)).one()
    assert Decimal(content["cost_so_far"]["counted_usd"]) == cap > 0
    assert Decimal(content["cost_so_far"]["reported_usd"]) == reported > 0
    # Step 10a (owner's review, 2026-10-11): "1 model call", in the singular.
    assert f"Cost so far: ${cap:.6f} counted toward the caps (reported ${reported:.6f}; 1 model call," in words


def test_code_locks_only_the_confirmed_plan_and_says_so(engine, stub):
    """Mutation o04: a confirmation of another fingerprint (written past the code by direct SQL) stops the run with
    code's own reason before the lock is tried; the database's backstop is not what refuses it."""
    rid = waiting(engine, stub)
    content, _ = confirmation.show(engine, rid)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                          "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada Reviewer', :fp, :p, :n, '{}', 'x')"),
                     dict(r=rid, fp="e" * 64, p=content["planner_stage_result_id"], n=content["narrowing_stage_result_id"]))
    report = proceed(engine, rid, stub)
    assert report.status == "failed" and report.failure == "refused: a checkpoint or write refused (not_confirmed)"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_confirm_waits_for_a_seal_in_progress_and_gives_its_own_reason(engine, stub):
    """Fix round 1, finding 2: `confirm` takes the shared lock before its own source check, so a registration that
    commits during the confirmation is seen by the check (code's reason, not the database's backstop)."""
    import threading
    import time
    from sqlalchemy import create_engine
    from model_builder import sha, version_fingerprint
    rid = waiting(engine, stub)
    sealer = create_engine(engine.url, connect_args={"options": "-c TimeZone=UTC"})
    conn = sealer.connect()
    tx = conn.begin()
    src = conn.execute(text("SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = 'mpea'")).one()
    v = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', '2026-10-08') "
                          "RETURNING id"), dict(s=src.id)).scalar()
    data = b"newer,data\n"
    conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'x.csv', :h, :c)"),
                 dict(v=v, h=sha(data), c=data))
    conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
                 dict(f=version_fingerprint({"x.csv": data}, src.source_type, src.data_kind, src.grouping_unit), v=v))
    outcome = {}

    def confirm_it():
        try:
            confirmation.confirm(engine, rid, by="Ada Reviewer")
            outcome["code"] = "confirmed"
        except queries.QueryRefused as refused:
            outcome["code"] = refused.code

    t = threading.Thread(target=confirm_it)
    t.start()
    time.sleep(1.0)
    assert t.is_alive()  # waiting for the seal's lock
    tx.commit()
    t.join(10)
    conn.close()
    sealer.dispose()
    assert outcome["code"] == "sources_changed"
