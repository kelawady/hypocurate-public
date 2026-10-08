"""Step 8b: the regression suite makes no live model call (owner's standing requirement). The test process and every
guarded child it starts have no provider credential, and the provider's address is a closed local port
(tests/conftest.py); a call that does not name the stub can therefore never leave the machine."""
from __future__ import annotations

import os

import pytest

import pipeline_world as pw
from conftest import NO_PROVIDER
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents import planner


def test_the_test_process_has_no_provider_credential_and_a_closed_local_address():
    assert "ANTHROPIC_API_KEY" not in os.environ and "ANTHROPIC_AUTH_TOKEN" not in os.environ
    assert os.environ["ANTHROPIC_API_BASE"] == os.environ["ANTHROPIC_BASE_URL"] == NO_PROVIDER
    assert NO_PROVIDER.startswith("http://127.0.0.1:")


@pytest.mark.parametrize("key, expected", [(None, "model_auth"), ("a-key-that-is-not-real", "provider_unavailable")])
def test_an_agent_call_without_the_stub_never_reaches_a_provider(migrated_database, monkeypatch, key, expected):
    """With no key the library refuses before sending (model_auth); with a key the request goes to the closed
    local port (provider_unavailable). In neither case is any usage recorded."""
    if key:
        monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    engine = make_engine(migrated_database)
    pw.registered(engine, ("mpea",))
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid)
    assert result.failure == expected
    from sqlalchemy import text
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM model_call WHERE run_id = :r AND input_tokens IS NOT NULL"),
                            dict(r=rid)).scalar() == 0
