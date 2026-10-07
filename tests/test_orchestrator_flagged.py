"""Step 8b fix round 1: the orchestrator on constructed data that raises flags, so the Critic is really called.

- Replaces the earlier Critic-failure test, which used the reference data (no flags) and so could pass without
  any Critic request (ChatGPT's review, "Tests").
- Finding 3: a recording or reservation failure stops the run: no further Critic batch and no Analyst call; the
  run stays running (and a call whose recording failed stays started) for step 9's recovery.

Every model call goes to the local stub provider.
"""
from __future__ import annotations

from types import MappingProxyType

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline.agents import settings as agent_settings
from hypocurate.pipeline.agents import spend
from stats_world import small_rows
from test_critic import CONFLICT
from test_orchestrator import responder

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    yield e
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def dispatched(engine, flags_per_call=None, monkeypatch=None):
    """A fixed-plan run on the constructed data; `flags_per_call` is recorded in the Critic's settings version."""
    if flags_per_call is not None:
        c = agent_settings.SETTINGS["critic"]
        changed = MappingProxyType({**c, "limits": MappingProxyType({**c["limits"], "max_flags_per_call": flags_per_call})})
        monkeypatch.setattr(agent_settings, "SETTINGS", MappingProxyType({**agent_settings.SETTINGS, "critic": changed}))
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True)


def run(engine, rid, stub):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def kinds(stub) -> list[str]:
    """Which role each request was for, in order."""
    out = []
    for r in stub.requests:
        raw = r["raw"].decode()
        out.append("critic" if "[[ ## classification ## ]]" in raw else "analyst" if "[[ ## report ## ]]" in raw
                   else "other")
    return out


def test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes(engine, stub):
    def respond(raw):
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification="prose, not JSON"))
        return responder()(raw)
    stub.respond(respond)
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    flags = one(engine, "SELECT count(*) FROM flag WHERE run_id = :r", r=rid)
    assert flags >= 2                                                     # the data raise flags
    assert kinds(stub)[:2] == ["critic", "critic"]                        # the Critic was asked, and corrected once
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'critic'", r=rid) == "failed"
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0
    assert report.status == "completed" and "analyst" in kinds(stub)      # the run went on to the end
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_an_accounting_failure_at_the_critic_stops_the_run_with_no_further_request(engine, stub, monkeypatch,
                                                                                    failure):
    attempts = []

    def broken(*a, **kw):
        attempts.append(1)
        raise RuntimeError("database gone")

    rid = dispatched(engine, flags_per_call=1, monkeypatch=monkeypatch)
    stub.respond(responder())
    monkeypatch.setattr(spend, "finish" if failure == "recording_failed" else "reserve", broken)
    report = run(engine, rid, stub)
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r", r=rid) >= 2  # two batches were due
    assert attempts == [1]                                                # one reservation or one recording only
    assert kinds(stub) == (["critic"] if failure == "recording_failed" else [])  # no second batch, no Analyst
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'critic'", r=rid) == 1
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0
    assert report.status == "running" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert failure in report.failure
    if failure == "recording_failed":
        assert one(engine, "SELECT count(*) FROM model_call mc JOIN agent_invocation i ON i.id = mc.invocation_id "
                           "WHERE i.run_id = :r AND mc.status = 'started'", r=rid) == 1


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_an_accounting_failure_at_the_analyst_stops_the_run_before_completion(engine, stub, monkeypatch, failure):
    def critic_ok(raw):
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification="{}"))
        return responder()(raw)

    stub.respond(critic_ok)
    rid = dispatched(engine)
    real = {"finish": spend.finish, "reserve": spend.reserve}
    name = "finish" if failure == "recording_failed" else "reserve"

    def broken_for_the_analyst(db, *a, **kw):
        with db.connect() as conn:
            role = conn.execute(text("SELECT role FROM stage_result WHERE run_id = :r AND status = 'running'"),
                                dict(r=rid)).scalar()
        if role == "analyst":
            raise RuntimeError("database gone")
        return real[name](db, *a, **kw)

    monkeypatch.setattr(spend, name, broken_for_the_analyst)
    report = run(engine, rid, stub)
    assert report.status == "running" and failure in report.failure
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) is None   # nothing copied
