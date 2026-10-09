"""Step 9b fix round 1, finding 1 (owner, 2026-10-09): a spending refusal survives a failed save.

A real refusal (the run's ceiling, or the monthly cap) at the Planner or the Critic, then the agent's stage cannot be
saved (a test-only trigger refuses the update), so the stage stays running and the run stays open. Recovery must
find the refusal's record and keep it a stop: the run fails `spending_refused`, nothing is repeated or sent, and the
Analyst is never asked after a Critic refusal; also when the month has changed since (the monthly total no longer
reaches the cap), since the refusal is what was decided then."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate import worker
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries, queue
from hypocurate.pipeline.agents import spend
from test_worker import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def fail_saving(engine, stage):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE FUNCTION hc_test_failsave() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          f"IF NEW.stage = '{stage}' AND NEW.status = 'failed' THEN "
                          f"RAISE EXCEPTION 'test: the stage cannot be saved'; END IF; RETURN NEW; END $$"))
        conn.execute(text("CREATE TRIGGER zz_hc_test_failsave BEFORE UPDATE ON stage_result FOR EACH ROW "
                          "EXECUTE FUNCTION hc_test_failsave()"))


def allow_saving(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TRIGGER zz_hc_test_failsave ON stage_result"))
        conn.execute(text("DROP FUNCTION hc_test_failsave()"))


def fill_the_month(engine, rid):
    """Calls of another run that bring this month's counted total to the monthly cap (after dispatch, which the cap
    would refuse)."""
    other = to.dispatched(engine, fixed_plan=True)  # another query's run, holding the month's calls
    queries.start(engine, other)
    from hypocurate.pipeline.agents.runstage import open_stage
    _, inv = open_stage(engine, other, "analyst", "analyst")
    with engine.begin() as conn:
        for _ in range(int(spend.MONTH_CAP_USD // 2)):
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, "
                              "'claude-opus-5-5', 'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
    return other


def change_the_month(engine, other):
    """The month changes: the other run's calls now belong to the previous month (test only, triggers off)."""
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE model_call DISABLE TRIGGER USER"))
        conn.execute(text("UPDATE model_call SET started_at = started_at - interval '40 days' WHERE run_id = :r"),
                     dict(r=other))
        conn.execute(text("ALTER TABLE model_call ENABLE TRIGGER USER"))
    with engine.connect() as conn:
        assert spend.month_total(conn) < spend.MONTH_CAP_USD


def take_up(engine, rid):
    c = queue.claim(engine, rid, "test:recovery")
    assert c is not None and c.status_before == "running"
    return worker.work(engine, c, heartbeat_interval=0.5)


def refused_with_unsaved_stage(engine, stub, stage, rid):
    """Runs the orchestrator in this process up to the refusal at `stage`, whose failed stage cannot be saved."""
    fail_saving(engine, stage)
    try:
        orchestrator.run(engine, rid, client_options=sp.client_options(stub))
    except Exception:  # noqa: BLE001 (the save failed; how the run's process ends does not matter here)
        pass
    finally:
        allow_saving(engine)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = :s ORDER BY id DESC LIMIT 1",
               r=rid, s=stage) == "running"


@pytest.mark.parametrize("cause", ["ceiling", "month", "month_then_changed"])
def test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery(engine, stub, cause):
    stub.respond(to.responder(to.planner_body()))
    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001") if cause == "ceiling" else None)
    other = fill_the_month(engine, rid) if cause != "ceiling" else None
    refused_with_unsaved_stage(engine, stub, "planner", rid)
    if cause == "month_then_changed":
        change_the_month(engine, other)
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "plan") == 0  # never sent, before or after the recovery
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 1
    assert one(engine, "SELECT output->>'code' FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == (
        "ceiling_reached" if cause == "ceiling" else "spending_cap_month")


@pytest.fixture
def flagged(migrated_database, monkeypatch, stub):
    """A marked test run on small constructed data whose flags name two records each (the Critic is asked)."""
    from stats_world import small_rows
    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
                            "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
    yield e
    e.dispose()


@pytest.mark.parametrize("cause", ["month", "month_then_changed"])
def test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked(flagged, stub, cause):
    from test_critic import SOURCES
    engine = flagged
    stub.respond(to.responder())
    q = queries.create(engine, to.FCC_CLAIM, SOURCES)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True)
    # The month's calls (another marked run of the same query's sources).
    q2 = queries.create(engine, to.FCC_CLAIM, SOURCES)
    queries.submit(engine, q2.version_id)
    queries.confirm_domain(engine, q2.version_id, by="Ada Reviewer")
    other = queries.dispatch(engine, q2.version_id, fixed_plan=True, constructed_test_data=True)
    queries.start(engine, other)
    from hypocurate.pipeline.agents.runstage import open_stage
    _, inv = open_stage(engine, other, "analyst", "analyst")
    with engine.begin() as conn:
        for _ in range(int(spend.MONTH_CAP_USD // 2)):
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, "
                              "'claude-opus-5-5', 'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
    refused_with_unsaved_stage(engine, stub, "critic", rid)
    if cause == "month_then_changed":
        change_the_month(engine, other)
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "classification") == 0 and requests(stub, "report") == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0


def test_a_refusal_is_reported_only_once_its_record_is_committed(engine, stub, monkeypatch):
    """The refusal and its audit record are one transaction: if the record cannot be written, the refusal is not
    reported as one (the caller sees a failure to save the call instead)."""
    from hypocurate.pipeline.agents.runstage import open_stage
    stub.respond(to.responder())
    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001"))
    queries.start(engine, rid)
    _, inv = open_stage(engine, rid, "planner", "planner")
    with pytest.raises(spend.SpendingRefused):
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
    assert one(engine, "SELECT count(*) FROM audit_log WHERE function = 'model_call' AND NOT allowed AND "
                       "detail->>'invocation' = :i AND detail->>'code' = 'ceiling_reached'", i=str(inv)) == 1
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_test_noaudit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          "RAISE EXCEPTION 'test: no audit row'; END $$"))
        conn.execute(text("CREATE TRIGGER zz_hc_test_noaudit BEFORE INSERT ON audit_log FOR EACH ROW "
                          "EXECUTE FUNCTION hc_test_noaudit()"))
    try:
        with pytest.raises(Exception) as raised:
            spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
        assert not isinstance(raised.value, spend.SpendingRefused)
    finally:
        with engine.begin() as conn:
            conn.execute(text("DROP TRIGGER zz_hc_test_noaudit ON audit_log"))
            conn.execute(text("DROP FUNCTION hc_test_noaudit()"))
