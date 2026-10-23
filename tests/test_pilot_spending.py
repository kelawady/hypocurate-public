"""Sprint 2 pilot, merge review A4 (2026-10-23): every new call site (the Extractor's extraction and verification
calls, a retry, the Reconciler's call; a repair fetch's extraction is the same extraction call) reserves under the
per-document-invocation cap and the shared monthly cap before any request is sent: a refusal sends nothing and stores
no candidate. The cap is per document invocation (each extraction step and each Reconciler run is one); the monthly
cap bounds the total across invocations and papers."""
from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import text

import stub_provider as sp
from hypocurate.pipeline import reconcile as rc
from hypocurate.pipeline.agents import spend
from hypocurate.pipeline.extraction import model_extractor as mx
from hypocurate.sources import versions
from test_extractor import ALL_YES, World, draft, gs_ys_record, stored_parse, stub, w  # noqa: F401 (fixtures)
from test_reconcile import frozen  # noqa: F401 (fixture)


def _refusals(db):
    with db.connect() as conn:
        return conn.execute(text("SELECT stage, detail->>'code' FROM audit_log WHERE function = 'model_call' "
                                 "AND NOT allowed ORDER BY id")).all()


def test_the_extraction_call_is_refused_before_any_request_under_the_document_cap(db, stub, monkeypatch):
    monkeypatch.setattr(spend, "DOCUMENT_CAP_USD", Decimal("0.0001"))
    run = mx.extract_document(db, stored_parse(World(db)), "H1_v1", client_options=sp.client_options(stub))
    assert run.frozen is None and stub.requests == [] and "spending_cap_document" in (run.failure or "")
    assert _refusals(db) == [("document", "spending_cap_document")]
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM candidate_observation")).scalar() == 0


def test_the_verification_call_is_refused_before_any_request_under_the_monthly_cap(db, stub, monkeypatch):
    stub.queue(sp.reply(sp.fields(records=draft([gs_ys_record()])), input_tokens=4000, output_tokens=900))
    real = spend.reserve
    calls = []

    def month_spent_after_first(*a, **k):  # the month is full by the time the verification call is reserved
        calls.append(1)
        if len(calls) > 1:
            monkeypatch.setattr(spend, "MONTH_CAP_USD", Decimal("0"))
        return real(*a, **k)
    monkeypatch.setattr(spend, "reserve", month_spent_after_first)
    run = mx.extract_document(db, stored_parse(World(db)), "H1_v1", client_options=sp.client_options(stub))
    assert len(stub.requests) == 1 and run.frozen is None and "spending_cap_month" in (run.failure or "")
    assert _refusals(db) == [("document", "spending_cap_month")]


def test_the_verification_call_is_refused_before_any_request_under_the_document_cap(db, stub, monkeypatch):
    """Merge review round 2 (A4): the verification call's own document invocation, its cap exhausted."""
    stub.queue(sp.reply(sp.fields(records=draft([gs_ys_record()])), input_tokens=4000, output_tokens=900))
    real = spend.reserve
    calls = []

    def cap_spent_after_first(*a, **k):  # the verification invocation's budget is gone when it is reserved
        calls.append(1)
        if len(calls) > 1:
            monkeypatch.setattr(spend, "DOCUMENT_CAP_USD", Decimal("0"))
        return real(*a, **k)
    monkeypatch.setattr(spend, "reserve", cap_spent_after_first)
    run = mx.extract_document(db, stored_parse(World(db)), "H1_v1", client_options=sp.client_options(stub))
    assert len(stub.requests) == 1 and run.frozen is None and "spending_cap_document" in (run.failure or "")
    assert _refusals(db) == [("document", "spending_cap_document")]
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM candidate_observation")).scalar() == 0


def test_a_retry_is_reserved_again_and_refused_when_the_cap_is_reached_between_attempts(db, stub, monkeypatch):
    stub.queue(sp.reply(sp.fields(records="not json"), input_tokens=4000, output_tokens=900))  # malformed: a retry
    real = spend.reserve

    def cap_after_first(engine, invocation, model, bound, *rest):
        with engine.connect() as conn:
            spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call WHERE "
                                      "invocation_id = :i"), dict(i=invocation)).scalar()
        monkeypatch.setattr(spend, "DOCUMENT_CAP_USD", Decimal(spent) + bound if spent == 0 else Decimal(spent))
        return real(engine, invocation, model, bound, *rest)
    monkeypatch.setattr(spend, "reserve", cap_after_first)
    run = mx.extract_document(db, stored_parse(World(db)), "H1_v1", client_options=sp.client_options(stub))
    assert len(stub.requests) == 1 and run.frozen is None  # the retry was never sent
    assert [c for _, c in _refusals(db)] == ["spending_cap_document"]


def test_the_reconciler_call_is_refused_before_any_request_under_either_cap(db, frozen, stub, monkeypatch):  # noqa: F811
    f, _ = frozen
    versions.register(db, "mpea")
    for name, code in (("DOCUMENT_CAP_USD", "spending_cap_document"), ("MONTH_CAP_USD", "spending_cap_month")):
        monkeypatch.setattr(spend, name, Decimal("0"))
        run = rc.reconcile(db, f.output_id, client_options=sp.client_options(stub))
        assert run.failure == code and run.mappings == 0 and stub.requests == []
        monkeypatch.undo()
    assert [c for _, c in _refusals(db)] == ["spending_cap_document", "spending_cap_month"]
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM reconciler_mapping")).scalar() == 0


def test_the_caps_are_the_registered_values():
    assert (spend.DOCUMENT_CAP_USD, spend.MONTH_CAP_USD, spend.RUN_CAP_USD) == (Decimal("2"), Decimal("50"), Decimal("2"))


def test_every_refusal_code_of_the_spending_module_is_a_known_failure_that_stops():
    """Merge review A4: found by the call-site tests above (the document cap's code was missing, so a refusal raised
    a KeyError after nothing was sent)."""
    from hypocurate.pipeline.agents.lm import FAILURES
    for code in spend.CODES:
        assert FAILURES[code][1] == "stop", code
