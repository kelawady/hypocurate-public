"""Step 8b fix round 1, finding 2: each role builds its request from the settings version recorded for its
invocation (instruction, model, limits and options), never from the settings current when the request is made.

Each test records version A (the current settings) at dispatch, then makes the current settings version B (a
changed instruction, effort and limits, the same model) and stores B, as a later deployment would on its next
dispatch, and only then runs the role. The request must be A's. Every model call goes to the local stub provider.
"""
from __future__ import annotations

import json
from types import MappingProxyType

import pytest

import stub_provider as sp
from hypocurate.pipeline.agents import settings as agent_settings
from test_analyst import BELOW, below_minimums
from test_analyst import reply as analyst_reply
from test_critic import checked_run, flag_ids, version
from test_critic import reply as critic_reply
from test_curator import answer as curator_answer
from test_curator import register_base, run_curate
from test_planner_narrowing import answer as planner_answer
from test_planner_narrowing import plan_run, running

MARKER = "VERSION-B-MARKER"
OTHER_EFFORT = {"low": "high", "medium": "high", "high": "low"}
HAIKU_BUDGET = {"low": 1024, "medium": 2048, "high": 4096}


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def version_b(role: str) -> dict:
    """The role's current settings changed in everything but the model."""
    a = agent_settings.SETTINGS[role]
    limits = {**a["limits"], "max_tokens": a["limits"]["max_tokens"] + 1000}
    if "max_flags_per_call" in limits:
        limits["max_flags_per_call"] = 1
    effort = OTHER_EFFORT[a["settings"]["reasoning_effort"]]
    return MappingProxyType({"instruction": f"{a['instruction']} {MARKER}", "model": a["model"],
                             "limits": MappingProxyType(limits),
                             "settings": MappingProxyType({**a["settings"], "reasoning_effort": effort})})


def make_current(monkeypatch, engine, role: str) -> dict:
    """Version B becomes the current settings and is stored; returns version A (what the run recorded)."""
    a = agent_settings.SETTINGS[role]
    monkeypatch.setattr(agent_settings, "SETTINGS", MappingProxyType({**agent_settings.SETTINGS, role: version_b(role)}))
    agent_settings.ensure_setting(engine, role)
    return a


def assert_request_is(body: dict, a) -> None:
    raw = json.dumps(body, ensure_ascii=False)
    assert MARKER not in raw
    assert body["model"].endswith(a["model"])
    assert body["max_tokens"] == a["limits"]["max_tokens"]
    effort = a["settings"]["reasoning_effort"]
    if "haiku" in a["model"]:  # litellm (locked version) sends Haiku's effort as a thinking budget
        assert body["thinking"] == {"type": "enabled", "budget_tokens": HAIKU_BUDGET[effort]}
    else:
        assert body["output_config"] == {"effort": effort}


def test_the_planner_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    from hypocurate.db.engine import make_engine
    engine = make_engine(migrated_database)
    try:
        rid = running(engine)
        a = make_current(monkeypatch, engine, "planner")
        stub.queue(sp.reply(planner_answer()))
        plan_run(engine, rid, stub)
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_critic_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    import pipeline_world as pw
    from hypocurate.db.engine import make_engine
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    try:
        pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
        rid = checked_run(engine, version(engine))
        flags = flag_ids(engine, rid)
        assert len(flags) >= 2  # version B's limit of one flag per call would make one call per flag
        a = make_current(monkeypatch, engine, "critic")
        stub.respond(lambda raw: critic_reply({str(f): {"class": "cannot_tell", "reason": "same metadata"}
                                               for f in flags}))
        from hypocurate.pipeline.agents import critic
        critic.run_critic(engine, rid, client_options=sp.client_options(stub))
        assert len(stub.requests) == 1
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_analyst_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    from hypocurate.db.engine import make_engine
    from hypocurate.pipeline.agents import analyst
    engine = make_engine(migrated_database)
    try:
        rid = below_minimums(engine)
        a = make_current(monkeypatch, engine, "analyst")
        stub.queue(analyst_reply(BELOW))
        analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_curators_request_follows_the_setting_its_invocation_records(db, stub, monkeypatch):
    """The Curator's invocation records the setting at the call (registration scope); the request is built from
    that recorded row, so the audit record and the request cannot differ."""
    register_base(db)
    a_id = agent_settings.ensure_setting(db, "curator")
    a = make_current(monkeypatch, db, "curator")
    monkeypatch.setattr(agent_settings, "ensure_setting", lambda engine, role: a_id)
    stub.queue(sp.reply(curator_answer()))
    run_curate(db, "tamu_fcc", stub)
    assert_request_is(stub.bodies()[0], a)
