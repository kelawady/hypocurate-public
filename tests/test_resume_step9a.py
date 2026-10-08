"""Step 9a: the orchestrator takes every step from what is stored, so a run stopped between steps is taken up again
where it stopped, never repeating a step whose result is stored, and never repeating an agent stage that exists
(owner's approval of the step 9 plan, 2026-10-08: a3 and Q3). Stops are made by calling the steps one by one, as
the orchestrator does, and then calling `proceed` (or `prepare`) as a later process would. Step 9b adds the stops
made by killing the worker."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import stub_provider as sp
import test_orchestrator as to
from hypocurate.pipeline import checkpoints, checks, completion, confirmation, extract, inclusion, orchestrator
from hypocurate.pipeline import queries
from test_confirmation import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def stages(engine, rid):
    return one(engine, "SELECT string_agg(stage || ':' || status, ',' ORDER BY id) FROM stage_result WHERE run_id = :r",
               r=rid)


def kw(stub):
    return dict(client_options=sp.client_options(stub))


def reference(engine, stub):
    """An uninterrupted fixed-plan run's stored results, to compare with."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert orchestrator.run(engine, rid, **kw(stub)).status == "completed"
    return results(engine, rid)


def results(engine, rid):
    """The plan's content less its query version, the outcome and every analysis result. (The fingerprints are not
    compared: they include the query version, which differs between the two runs, step 8b open item 3.)"""
    with engine.connect() as conn:
        return ({k: v for k, v in conn.execute(text("SELECT content FROM plan WHERE run_id = :r"),
                                                dict(r=rid)).scalar().items() if k != "hypothesis_version"},
                conn.execute(text("SELECT outcome, verdict, evidence_level FROM run WHERE id = :r"), dict(r=rid)).one(),
                [tuple(r) for r in conn.execute(text(
                    "SELECT scope, n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM "
                    "analysis_result WHERE run_id = :r ORDER BY scope, n_records, estimate"), dict(r=rid)).all()])


def fixed_run_to_lock(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert orchestrator.prepare(engine, rid, **kw(stub)).ready
    with engine.connect() as conn:
        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
    return rid


@pytest.mark.parametrize("stop", ["after_lock", "between_sources", "after_checks", "after_critic", "after_inclusion",
                                  "after_freeze", "after_statistics", "after_analyst"])
def test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results(engine, stub, stop):
    expected = reference(engine, stub)
    rid = fixed_run_to_lock(engine, stub)
    order = ["between_sources", "after_checks", "after_critic", "after_inclusion", "after_freeze",
             "after_statistics", "after_analyst"]
    steps = order[:order.index(stop) + 1] if stop != "after_lock" else []
    from hypocurate.pipeline import analysis
    from hypocurate.pipeline.agents import analyst, critic
    for step in steps:
        if step == "between_sources":  # one source stored, the other still pending
            with engine.connect() as conn:
                key = conn.execute(text("SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE "
                                        "rs.run_id = :r AND rs.search_status = 'pending' ORDER BY s.key LIMIT 1"),
                                   dict(r=rid)).scalar()
            extract.store_source(engine, rid, key)
        elif step == "after_checks":
            extract.store_records(engine, rid)
            checks.run_checks(engine, rid)
        elif step == "after_critic":
            critic.run_critic(engine, rid, **kw(stub))
        elif step == "after_inclusion":
            inclusion.decide_run(engine, rid)
        elif step == "after_freeze":
            checkpoints.freeze_dataset(engine, rid)
        elif step == "after_statistics":
            analysis.run_statistics(engine, rid)
        elif step == "after_analyst":
            analyst.run_analyst(engine, rid, **kw(stub))
    before = stages(engine, rid)
    requests = len(stub.requests)
    report = orchestrator.proceed(engine, rid, **kw(stub))
    assert (report.status, report.failure) == ("completed", None), report
    assert results(engine, rid) == expected
    after = stages(engine, rid)
    assert after.startswith(before or "")  # nothing stored before the stop is touched
    for name in ("checks", "inclusion", "dataset_freeze", "statistics", "critic", "analyst"):
        assert after.count(f"{name}:") == 1, (name, after)  # never a step twice
    if stop == "after_analyst":
        assert len(stub.requests) == requests  # the Analyst is not asked again


def test_a_completed_run_is_left_as_it_is(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    orchestrator.run(engine, rid, **kw(stub))
    before, requests = stages(engine, rid), len(stub.requests)
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert (report.status, report.ready) == ("completed", False)
    assert stages(engine, rid) == before and len(stub.requests) == requests


def test_a_done_planner_stage_is_used_and_the_planner_is_not_asked_again(engine, stub):
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    planner.run_planner(engine, rid, **kw(stub))  # the stop: after the Planner, before the narrowing decision
    assert len(stub.requests) == 1
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.status == "waiting" and len(stub.requests) == 1
    assert stages(engine, rid) == "planner:done,narrowing:done"


def test_a_stored_narrowing_decision_is_used_and_not_taken_again(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid, **kw(stub))
    narrowing.run_narrowing(engine, rid, result.answer)  # the stop: before the wait
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.status == "waiting"
    assert stages(engine, rid) == "planner:done,narrowing:done"


def test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import analyst, planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid, **kw(stub))
    decision = narrowing.run_narrowing(engine, rid, result.answer)
    analyst.run_analyst(engine, rid, **kw(stub))
    completion.copy_partly_sufficient(engine, rid)  # the stop: completed, no narrower question yet
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
    requests = len(stub.requests)
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.narrower_question and len(stub.requests) == requests
    again = orchestrator.prepare(engine, rid, **kw(stub))
    assert again.narrower_question in (None, report.narrower_question)
    q = queries.create_narrower(engine, rid, decision["narrower_scope"])  # a later call never makes a second one
    assert q.number == report.narrower_question
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
    assert one(engine, "SELECT hv.status FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
                       "WHERE h.narrower_of_run_id = :r", r=rid) == "submitted"


def test_a_narrower_question_left_as_a_draft_by_a_stop_is_submitted(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    report = to.run(engine, rid, stub)
    vid = queries.submitted_version(engine, report.narrower_question)
    with engine.begin() as conn:  # as if the stop came between create and submit
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        conn.execute(text("UPDATE hypothesis_version SET status = 'draft', submitted_at = NULL WHERE id = :v"),
                     dict(v=vid))
    decision = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid)
    q = queries.create_narrower(engine, rid, decision["narrower_scope"])
    assert q.version_id == vid
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=vid) == "submitted"


def test_a_run_whose_primary_set_is_empty_is_taken_up_after_inclusion_without_deciding_again(engine, stub):
    """Inclusion's own guard reads the run's eligibility rows, which a run with no eligible record may not have; the
    orchestrator reads Inclusion's stored stage instead (step 9 design, the idempotency audit)."""
    from hypocurate.pipeline.agents import critic
    stub.respond(to.responder(to.BCC))
    rid = to.dispatched(engine, claim=to.BCC_CLAIM)
    assert orchestrator.run(engine, rid, **kw(stub)).status == "waiting"
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    orchestrator._go_on(engine, rid)
    with engine.connect() as conn:
        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    critic.run_critic(engine, rid, **kw(stub))
    inclusion.decide_run(engine, rid)  # the stop
    report = orchestrator.proceed(engine, rid, **kw(stub))
    assert (report.status, report.outcome, report.failure) == ("completed", "insufficient", None)
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 1
