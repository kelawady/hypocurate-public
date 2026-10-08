"""Step 9b, b5: the worker killed at each stage, then the run taken up again (docs/reviews/step09b_plan.md, "Tests").

Each case: an uninterrupted run of the query first (the reference), then the query dispatched again; a real worker
process works the second run and is killed (SIGKILL) at the chosen point: a test-only trigger sleeps at a write, or the
local stub kills the worker while it serves the chosen request. The child dies with the worker (A3). The run is then
claimed again once its claim is stale (a shortened, test-only staleness) and worked in this process. Checks:
- no stage stays running and no call stays started; every lost call ends `interrupted` and counts at its maximum;
- no request is repeated except the one allowed Planner repeat;
- the plan and freeze fingerprints and every analysis result equal the uninterrupted run's."""
from __future__ import annotations

import os
import signal
import time

import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate import worker
from hypocurate.pipeline import confirmation, queries, queue
from test_guarded_parent import gone
from test_worker import engine, stub, wait_until, worker as start_worker  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def results(engine, rid):
    with engine.connect() as conn:
        return (conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=rid)).scalar(),
                conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar(),
                tuple(conn.execute(text("SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r"),
                                   dict(r=rid)).one()),
                [tuple(r) for r in conn.execute(text(
                    "SELECT scope, n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM "
                    "analysis_result WHERE run_id = :r ORDER BY scope, n_records, estimate"), dict(r=rid)).all()])


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def number_of(engine, rid):
    return one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                       "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)


def complete(engine, rid):
    """Works the run to its end with the worker's code in this process (confirming a wait by a named person)."""
    for _ in range(4):
        status = one(engine, "SELECT status FROM run WHERE id = :r", r=rid)
        if status in ("completed", "failed"):
            return
        if status == "waiting" and not one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid):
            confirmation.confirm(engine, rid, by="Ada Reviewer")
        c = queue.claim_next(engine, "test:recover", only=rid, stale_seconds=1)
        if c is None:
            time.sleep(1.2)
            continue
        worker.work(engine, c, heartbeat_interval=0.5)


STALL_KEY = 0x48435453 << 32  # "HCTS": the test's own lock, apart from the code's


def stall(engine, table, when="true"):
    """A test-only trigger: each matching write waits for a lock the test holds, so the run makes no progress. Returns
    the holder. (A lock, not a sleep: a killed child's batched statements are already queued in its session, which
    goes on executing them; once the test lets go of the lock they drain at once and, with no COMMIT ever coming,
    roll back.)"""
    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    holder.execute(text("SELECT pg_advisory_lock(:k)"), dict(k=STALL_KEY))
    with engine.begin() as conn:
        conn.execute(text(f"CREATE FUNCTION hc_test_stall() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          f"PERFORM pg_advisory_xact_lock({STALL_KEY}); RETURN NEW; END $$"))
        conn.execute(text(f"CREATE TRIGGER zz_hc_test_stall BEFORE INSERT ON {table} FOR EACH ROW WHEN ({when}) "
                          f"EXECUTE FUNCTION hc_test_stall()"))
    return holder


def unstall(engine, table, holder):
    holder.execute(text("SELECT pg_advisory_unlock_all()"))
    holder.close()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL lock_timeout = '60s'"))
        conn.execute(text(f"DROP TRIGGER IF EXISTS zz_hc_test_stall ON {table}"))
        conn.execute(text("DROP FUNCTION IF EXISTS hc_test_stall()"))


def sleeping(engine):
    """A run's write is held at the test's lock."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' AND wait_event = "
                                 "'advisory' AND datname = current_database()")).scalar() > 0


def kill_worker_and_child(engine, proc, rid):
    child = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid)
    proc.send_signal(signal.SIGKILL)
    proc.wait(10)
    if child:
        assert wait_until(lambda: gone(child), 2), "the child outlived the worker"


def assert_bookkeeping(engine, rid):
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r AND status = 'started'", r=rid) == 0
    lost = one(engine, "SELECT coalesce(sum(max_cost), 0) FROM model_call WHERE run_id = :r AND status = 'interrupted'",
               r=rid)
    assert one(engine, "SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid) >= lost


def reference_and_second(engine, stub, body=None, claim=to.FCC_CLAIM, fixed=True):
    """The uninterrupted run (worked to its end) and a second run of the same query, queued."""
    stub.respond(to.responder(body))
    first = to.dispatched(engine, claim=claim, fixed_plan=fixed)
    complete(engine, first)
    return first, queries.dispatch_again(engine, number_of(engine, first))


@pytest.mark.parametrize("point, table, when", [
    ("after the lock", "record", "true"),
    ("between sources", "record", "NEW.source_version_id = {second}"),
    ("before Checks", "stage_result", "NEW.stage = 'checks'"),
    ("before Inclusion", "stage_result", "NEW.stage = 'inclusion'"),
    ("before the freeze", "run_snapshot", "true"),
    ("mid-statistics", "analysis_result", "true"),
])
def test_a_worker_killed_at_a_code_stage_is_taken_up_with_the_same_results(engine, stub, point, table, when):
    first, rid = reference_and_second(engine, stub)
    analyst_before = requests(stub, "report")
    if "{second}" in when:  # the version of the source stored second, in the order the code stores them
        from hypocurate.pipeline import extract
        second = extract.pending_sources(engine, rid)[1]
        when = when.format(second=one(engine, "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = "
                                              "rs.source_id WHERE rs.run_id = :r AND s.key = :k", r=rid, k=second))
    holder = stall(engine, table, when)
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120), point
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, table, holder)
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert results(engine, rid) == results(engine, first)
    assert requests(stub, "report") == analyst_before + 1  # one Analyst request for the second run


def kill_on(stub, field, body=None):
    """The stub kills the worker the first time it serves a request asking for `field`."""
    state = {"pid": None, "done": False}
    answer = to.responder(body)

    def respond(raw):
        if f"[[ ## {field} ## ]]" in raw and not state["done"] and state["pid"]:
            state["done"] = True
            os.kill(state["pid"], signal.SIGKILL)
            time.sleep(0.5)
        return answer(raw)

    stub.respond(respond)
    return state


def test_a_worker_killed_mid_planner_repeats_the_planner_once(engine, stub):
    first, rid = reference_and_second(engine, stub, body=to.planner_body(), fixed=False)
    plans_before = requests(stub, "plan")
    state = kill_on(stub, "plan", to.planner_body())
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(120)
    assert state["done"]
    assert wait_until(lambda: one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1, 10)
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert requests(stub, "plan") == plans_before + 2  # the lost request and its one repeat
    assert one(engine, "SELECT error FROM model_call WHERE run_id = :r AND status = 'interrupted'", r=rid) == \
        "worker_stopped"
    assert results(engine, rid)[1:] == results(engine, first)[1:]  # (the plan fingerprints: same plan content)
    assert results(engine, rid)[0] == results(engine, first)[0]


def test_a_worker_killed_before_the_narrowing_takes_it_up_without_asking_the_planner_again(engine, stub):
    first, rid = reference_and_second(engine, stub, body=to.planner_body(), fixed=False)
    plans_before = requests(stub, "plan")
    holder = stall(engine, "stage_result", "NEW.stage = 'narrowing'")
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, "stage_result", holder)
    complete(engine, rid)
    assert requests(stub, "plan") == plans_before + 1
    assert results(engine, rid) == results(engine, first)


def test_a_worker_killed_mid_analyst_completes_with_the_explanation_unavailable(engine, stub):
    from hypocurate import cli_runs
    first, rid = reference_and_second(engine, stub)
    reports_before = requests(stub, "report")
    state = kill_on(stub, "report")
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(300)
    assert state["done"]
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert requests(stub, "report") == reports_before + 1  # not repeated
    assert cli_runs.show(engine, rid)["analyst_text"] == {"unavailable": "explanation unavailable (interrupted)"}
    assert results(engine, rid) == results(engine, first)


def test_a_worker_killed_during_the_critics_request_is_taken_up_without_another_critic_request(migrated_database,
                                                                                                stub, monkeypatch):
    """Flags naming two records (small constructed data, a marked test run): the worker is killed during the Critic's
    first request; the run is taken up without another Critic request and completes. (The batch size is an agent
    setting recorded at dispatch; with these flags there is one batch, so "batch 1 of 2" is not exercised here.)"""
    import pipeline_world as pw
    import stub_provider as sp
    from hypocurate.db.engine import make_engine
    from stats_world import small_rows
    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME, SOURCES
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    eng = make_engine(migrated_database)
    with eng.begin() as conn:
        db = conn.execute(text("SELECT current_database()")).scalar()
        conn.execute(text(f'ALTER DATABASE "{db}" SET client_connection_check_interval = \'100ms\''))
    pw.registered_files(eng, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
                              "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
    q = queries.create(eng, to.FCC_CLAIM, SOURCES)
    queries.submit(eng, q.version_id)
    queries.confirm_domain(eng, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(eng, q.version_id, fixed_plan=True, constructed_test_data=True)
    state = kill_on(stub, "classification")
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(300)
    assert state["done"]
    critic_requests = requests(stub, "classification")
    complete(eng, rid)
    assert one(eng, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "classification") == critic_requests  # not repeated
    assert_bookkeeping(eng, rid)
    eng.dispose()


def test_a_worker_killed_between_the_partly_copy_and_the_narrower_question_leaves_exactly_one(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    holder = stall(engine, "hypothesis", "NEW.narrower_of_run_id IS NOT NULL")
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, "hypothesis", holder)
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) == "partly_sufficient"
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
    start_worker("--once")  # the worker's sweep finishes it
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
    start_worker("--once")
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1


def test_a_run_waiting_at_the_lock_when_the_worker_restarts_is_left_alone_until_confirmed(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    calls = one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid)
    start_worker("--once")  # a restart: nothing claimed, nothing sent
    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == calls
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"


def test_14_4_a_run_stopped_by_its_cap_fails_with_the_reason_and_is_dispatched_again(engine, stub):
    """Criterion 14.4, bullet 4 (at the Planner; R5): the cap stops the run before a request is sent, it is marked
    failed with the reason, and it can be dispatched again as a new run."""
    stub.respond(to.responder(to.planner_body()))
    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    from decimal import Decimal
    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001"))
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "plan") == 0
    again = queries.dispatch_again(engine, q.number)
    assert again != rid and one(engine, "SELECT status FROM run WHERE id = :r", r=again) == "queued"


def test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run(engine, stub):
    """Criterion 14.4, bullet 2: the worker is stopped (SIGTERM, as a deploy) during a run, then restarted: the run
    resumes from its last completed stage and finishes; it is never left running."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    holder = stall(engine, "run_snapshot")
    try:
        proc = start_worker(wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=120)
    finally:
        unstall(engine, "run_snapshot", holder)
    assert one(engine, "SELECT release_reason FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid) == \
        "shutdown"
    start_worker("--once")  # restarted: a shutdown claim is claimable at once
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert_bookkeeping(engine, rid)
