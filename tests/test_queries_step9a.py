"""Step 9a: cancel, dispatch again, the spending ceiling stored at dispatch and the two new dispatch refusals
(owner's approval of the step 9 plan, 2026-10-08: R2, R3, R5, Q6; the reasons' wording approved with the go for 9a,
the monthly cap's in the owner's own words)."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents import spend

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
MONTH_CAP_REASON = ("this month's model calls have reached the monthly cap ($50); dispatch is refused until next "
                    "month, or until the owner raises the cap")


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc", "controlled_duplicates"))
    yield e
    e.dispose()


def submitted(engine, sources=("mpea", "tamu_fcc")):
    q = queries.create(engine, CLAIM, sources)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def set_status(engine, rid, status):
    with engine.begin() as conn:
        if status == "running":
            conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=rid))
        elif status == "failed":
            conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x' WHERE id = :r"),
                         dict(r=rid))


def waiting_run(engine):
    """A Planner run at its wait (stage rows as the orchestrator stores them, by direct SQL)."""
    rid = queries.dispatch(engine, submitted(engine).version_id)
    queries.start(engine, rid)
    with engine.begin() as conn:
        sources = [{"source": k, "version_fingerprint": f} for k, f in conn.execute(text(
            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id JOIN source_version sv "
            "ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=rid)).all()]
        for stage, role, output in (("planner", "planner", {}), ("narrowing", None, {"result": "proceed",
                                                                                      "sources": sources})):
            sid = conn.execute(text("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :o, 1) "
                                    "RETURNING id"), dict(r=rid, s=stage, o=role)).scalar_one()
            conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = CAST(:o AS jsonb) "
                              "WHERE id = :s"), dict(s=sid, o=json.dumps(output)))
        conn.execute(text("UPDATE run SET status = 'waiting' WHERE id = :r"), dict(r=rid))
    return rid


# --- cancel (R3) ------------------------------------------------------------------------------------------

def test_a_queued_run_is_cancelled_with_the_persons_name(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    queries.cancel(engine, rid, by="Ada Reviewer")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
        "cancelled: cancelled by Ada Reviewer before it started"


def test_a_waiting_run_is_cancelled_with_the_persons_name(engine):
    rid = waiting_run(engine)
    queries.cancel(engine, rid, by="  Ada Reviewer ")
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
        "cancelled: cancelled by Ada Reviewer while waiting for confirmation of the question as tested"


@pytest.mark.parametrize("status", ["running", "failed"])
def test_a_started_or_ended_run_is_not_cancelled(engine, status):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    set_status(engine, rid, "running")
    if status == "failed":
        set_status(engine, rid, "failed")
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "not_cancellable"
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == status


@pytest.mark.parametrize("by", ["", "   ", "x" * 201, None])
def test_a_cancel_names_the_person(engine, by):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, rid, by=by)
    assert refused.value.code == "name_required"
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"


def test_cancelling_an_unknown_run_is_refused(engine):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, 999, by="Ada Reviewer")
    assert refused.value.code == "unknown_run"


# --- dispatch again (R2; PRD 8 and 14.4: a failed run is dispatched again as a new run) -----------------------

def test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded(engine):
    q = submitted(engine)
    first = queries.dispatch(engine, q.version_id, fixed_plan=True, ceiling=Decimal("0.5"))
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    again = queries.dispatch_again(engine, q.number)
    assert again != first
    with engine.connect() as conn:
        row = conn.execute(text("SELECT status, hypothesis_version_id, fixed_plan, experiment_flags, spending_ceiling "
                                "FROM run WHERE id = :r"), dict(r=again)).one()
    assert (row.status, row.hypothesis_version_id, row.fixed_plan, row.experiment_flags) == (
        "queued", q.version_id, True, {})
    # A ceiling is given with each dispatch, never inherited; none given stores the run cap (owner, 2026-10-08).
    assert row.spending_ceiling == spend.RUN_CAP_USD


@pytest.mark.parametrize("status", ["queued", "running", "waiting"])
def test_dispatch_again_is_refused_while_another_run_of_the_query_is_open(engine, status):
    if status == "waiting":
        rid = waiting_run(engine)
        number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                             "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)
    else:
        q = submitted(engine)
        rid, number = queries.dispatch(engine, q.version_id), q.number
        if status == "running":
            set_status(engine, rid, "running")
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, number)
    assert (refused.value.code, refused.value.reason) == (
        "already_open", "another run of this query is queued, waiting or running")
    assert one(engine, "SELECT count(*) FROM run") == 1


def test_dispatch_again_needs_a_dispatched_query(engine):
    q = submitted(engine)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, q.number)
    assert refused.value.code == "not_dispatched"


def test_a_marked_test_run_is_dispatched_again_marked(engine):
    q = submitted(engine, sources=("mpea", "controlled_duplicates"))
    first = queries.dispatch(engine, q.version_id, constructed_test_data=True)
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    again = queries.dispatch_again(engine, q.number)
    assert one(engine, "SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = :r", r=again) == "true"


# --- the ceiling stored at dispatch (R5) ------------------------------------------------------------------

def test_the_ceiling_is_stored_at_dispatch(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id, ceiling=Decimal("0.25"))
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("0.25")


@pytest.mark.parametrize("ceiling", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_a_ceiling_is_a_positive_amount(engine, ceiling):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, submitted(engine).version_id, ceiling=ceiling)
    assert refused.value.code == "invalid_ceiling"


def _call_run(engine, ceiling):
    """A running run with the code's settings recorded and an open Planner stage and invocation."""
    rid = queries.dispatch(engine, submitted(engine).version_id, ceiling=ceiling)
    queries.start(engine, rid)
    from hypocurate.pipeline.agents.runstage import open_stage
    _, inv = open_stage(engine, rid, "planner", "planner")
    return rid, inv


def test_the_stored_ceiling_holds_when_the_caller_names_none(engine):
    """After a crash or a restart, the request path reads the ceiling from the run, not from a caller's memory."""
    rid, inv = _call_run(engine, Decimal("0.10"))
    spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"))
    assert refused.value.code == "ceiling_reached"


def test_the_lower_of_the_stored_and_the_given_ceiling_holds(engine):
    rid, inv = _call_run(engine, Decimal("1.00"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"), Decimal("0.05"))
    assert refused.value.code == "ceiling_reached"
    rid2, inv2 = _call_run(engine, Decimal("0.05"))
    with pytest.raises(spend.SpendingRefused):
        spend.reserve(engine, inv2, "claude-opus-5-5", Decimal("0.06"), Decimal("1.00"))


def test_without_a_ceiling_the_run_cap_holds(engine):
    rid, inv = _call_run(engine, None)
    spend.reserve(engine, inv, "claude-opus-5-5", Decimal("1.5"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.6"))
    assert refused.value.code == "spending_cap_run"


# --- the monthly cap blocks dispatch (R5; PRD 8, 9.3) -----------------------------------------------------

def _spend_this_month(engine, amount):
    rid, inv = _call_run(engine, None)
    with engine.begin() as conn:  # other runs' calls, counted as the caps count them (cost, or maximum while unknown)
        for _ in range(int(amount // Decimal("2"))):
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, 'claude-opus-5-5', "
                              "'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
        rest = amount % Decimal("2")
        if rest:
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, 'claude-opus-5-5', "
                              "'p', :m FROM agent_invocation WHERE id = :i"), dict(i=inv, m=rest))


def test_dispatch_is_refused_once_the_months_calls_reach_the_monthly_cap(engine):
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    q = submitted(engine)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, q.version_id)
    assert (refused.value.code, refused.value.reason) == ("month_cap_reached", MONTH_CAP_REASON)
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=q.version_id) == "submitted"


def test_dispatch_is_allowed_below_the_monthly_cap(engine):
    _spend_this_month(engine, spend.MONTH_CAP_USD - Decimal("0.01"))
    rid = queries.dispatch(engine, submitted(engine).version_id)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"


def test_dispatch_again_is_refused_at_the_monthly_cap(engine):
    q = submitted(engine)
    first = queries.dispatch(engine, q.version_id)
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, q.number)
    assert refused.value.code == "month_cap_reached"


# --- constructed test data (owner, Q6) --------------------------------------------------------------------

def test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test(engine):
    q = submitted(engine, sources=("mpea", "controlled_duplicates"))
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, q.version_id)
    assert (refused.value.code, refused.value.reason) == (
        "constructed_source_unmarked",
        "controlled_duplicates is constructed test data; dispatch it only as a marked test run")
    assert one(engine, "SELECT count(*) FROM run") == 0
    rid = queries.dispatch(engine, q.version_id, constructed_test_data=True)
    assert one(engine, "SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = :r", r=rid) == "true"


def test_a_constructed_source_not_chosen_does_not_refuse_dispatch(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"


def test_a_dispatch_without_a_ceiling_stores_the_run_cap(engine):
    """The owner's decision (2026-10-08): every run stores its effective ceiling at dispatch; none given is the cap."""
    rid = queries.dispatch(engine, submitted(engine).version_id)
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == spend.RUN_CAP_USD
