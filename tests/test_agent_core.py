"""Step 8a: the request path every agent call takes (register 'model_call_recording',
'request_failure_policy', 'spending_caps', 'model_prices').

Each test drives real requests through DSPy and litellm to a local stub of the provider
(`stub_provider`), so what is checked is the actual outbound request, as bytes, and the rows the
database holds afterwards. One test per row of the failure table approved for step 8a, plus the
reservation before each request, the caps, the month-wide lock, and no open transaction while a
request is in flight.

What these tests do not cover: a real provider's behaviour (the live tests, run only with the
owner's go), and any role's own checks (the Curator's are in tests/test_curator.py).
"""
from __future__ import annotations

import json
import threading
from decimal import Decimal

import pytest
from sqlalchemy import text

import stub_provider as sp
from hypocurate.pipeline.agents import interface, lm, prices, spend
from hypocurate.pipeline.agents.interface import call_agent
from hypocurate.pipeline.agents.libraries import load
from model_builder import World

_, dspy = load()
MODEL = "claude-sonnet-5-5"
PLANTED = "ZQPLANTED-4711"


class Ask(dspy.Signature):
    """Answer the question in one short sentence."""
    question: str = dspy.InputField()
    note: str = dspy.InputField()
    answer: str = dspy.OutputField()


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def registration(w, label="docs"):
    v = w.new_version("tamu_fcc", label)
    w.add_file(v, "table.csv", f"a,{label}\n".encode())
    w.add_file(v, "documentation/main.tex", b"Quasistatic tensile testing was used throughout.\n", role="documentation")
    w.seal(v)
    return w.val("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                 "VALUES ('registration', :v, 'curator', :a) RETURNING id", v=v, a=w.agent_setting("curator"))


def ask(db, inv, stub, *, question="What is tested?", timeout_seconds=30, ceiling=None, max_output_chars=2000,
        check=None, lm_options=None):
    return call_agent(db, inv, Ask, {"question": question}, model=MODEL, max_tokens=500,
                      max_output_chars=max_output_chars, ceiling=ceiling, lm_options=lm_options,
                      client_options=sp.client_options(stub, timeout_seconds), check=check)


def calls(w, inv):
    return w.rows("SELECT status, input_tokens, output_tokens, cached_tokens, cost, max_cost, error, model, "
                  "price_table_version FROM model_call WHERE invocation_id = :i ORDER BY id", i=inv)


# --- a request that succeeds -------------------------------------------------------------------------

def test_a_request_is_reserved_sent_once_and_recorded_with_its_usage_and_cost(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="Tension."), input_tokens=1300, output_tokens=40, cache_read=100))
    result = ask(db, inv, stub, lm_options={"reasoning_effort": "medium"})
    assert result.failure is None and result.outputs == {"answer": "Tension."} and result.attempts == ["ok"]
    [row] = calls(w, inv)
    # The provider reports 1300 uncached input tokens and 100 read from its cache; the stored input is
    # their total (as DSPy reports it), with the cached part separately, each priced at its own rate.
    assert (row.status, row.input_tokens, row.output_tokens, row.cached_tokens) == ("succeeded", 1400, 40, 100)
    assert row.cost == prices.cost(MODEL, 1400, 40, 100, 0) == Decimal("0.00302")
    assert row.max_cost > row.cost and row.model == MODEL and row.price_table_version == prices.PRICE_TABLE_VERSION
    [request] = stub.requests
    assert request["path"] == "/v1/messages" and request["headers"]["x-api-key"] == sp.DUMMY_KEY
    body = json.loads(request["raw"])
    assert body["model"] == MODEL and body["max_tokens"] == 500
    assert body["output_config"] == {"effort": "medium"}
    assert "tools" not in body and "tool_choice" not in body  # no tool is ever offered


def test_the_whole_request_is_the_instruction_and_the_inputs(w, db, stub):
    """The complete outbound request: the signature's instruction and field descriptions, the
    question and the note 'none'; no history, no other content."""
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="Yes.")))
    ask(db, inv, stub, question="Is it tension?")
    body = stub.bodies()[0]
    assert set(body) <= {"model", "max_tokens", "system", "messages", "thinking", "output_config"}
    assert len(body["messages"]) == 1 and body["messages"][0]["role"] == "user"
    user = json.dumps(body["messages"][0]["content"])
    assert "Is it tension?" in user and "[[ ## note ## ]]\\nnone" in user
    assert "Answer the question in one short sentence." in json.dumps(body["system"])


# --- the failure table --------------------------------------------------------------------------------

def test_an_unavailable_provider_is_tried_once_more_with_the_same_request(w, db, stub):
    inv = registration(w)
    stub.queue(sp.error(500, "api_error"), sp.reply(sp.fields(answer="Fine.")))
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable", "ok"] and result.failure is None
    first, second = calls(w, inv)
    assert (first.status, first.input_tokens, first.cost, first.error) == ("failed", None, None, "provider_unavailable")
    assert second.status == "succeeded"
    assert stub.requests[0]["raw"] == stub.requests[1]["raw"]


@pytest.mark.parametrize("step", [sp.error(429, "rate_limit_error"), sp.error(503, "overloaded_error"),
                                  sp.error(500, "api_error")])
def test_two_unavailable_answers_end_the_call(w, db, stub, step):
    inv = registration(w)
    stub.queue(step, step)
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable"] * 2 and result.failure == "provider_unavailable"
    assert [r.status for r in calls(w, inv)] == ["failed", "failed"]


def test_a_timeout_is_an_unavailable_provider(w, db, stub):
    inv = registration(w)
    stub.queue(sp.timeout(3), sp.timeout(3))
    result = ask(db, inv, stub, timeout_seconds=1)
    assert result.failure == "provider_unavailable" and len(calls(w, inv)) == 2


@pytest.mark.parametrize("status, kind, code", [(401, "authentication_error", "model_auth"),
                                                (403, "permission_error", "model_auth"),
                                                (400, "invalid_request_error", "provider_rejected")])
def test_refused_credentials_or_requests_are_not_retried_and_no_provider_text_is_kept(w, db, stub, status, kind, code):
    inv = registration(w)
    stub.queue(sp.error(status, kind, f"provider says {PLANTED}"))
    result = ask(db, inv, stub)
    assert result.attempts == [code] and result.failure == code and len(stub.requests) == 1
    [row] = calls(w, inv)
    assert (row.status, row.error, row.cost) == ("failed", code, None)
    stored = json.dumps([list(r) for r in w.rows("SELECT * FROM model_call")] +
                        [list(r) for r in w.rows("SELECT * FROM audit_log")], default=str)
    assert PLANTED not in stored and PLANTED not in str(lm.AgentFailure(code))


@pytest.mark.parametrize("first, code", [
    (sp.reply(f"no fields at all {PLANTED}"), "malformed"),
    (sp.reply("   "), "empty"),
    (sp.reply(sp.fields(answer="cut"), stop="max_tokens"), "truncated"),
    (sp.tool_call(), "tool_call"),
    (sp.reply(sp.fields(answer="x" * 3000)), "over_long"),
])
def test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer(w, db, stub, first, code):
    inv = registration(w)
    stub.queue(first, sp.reply(sp.fields(answer="Better.")))
    result = ask(db, inv, stub)
    assert result.attempts == [code, "ok"] and result.outputs == {"answer": "Better."}
    assert [r.status for r in calls(w, inv)] == ["succeeded", "succeeded"]  # both recorded with their usage
    retry = json.dumps(stub.bodies()[1])
    # Owner, 2026-10-10: the note also names the specific reason the check gave (None for these codes but malformed).
    assert interface.correction_note(code, result.reasons[0]).replace('"', '\\"') in retry
    assert result.reasons == ["missing output field: answer" if code == "malformed" else None, None]
    assert PLANTED not in retry and "x" * 100 not in retry and "/etc/x" not in retry
    assert retry.count("[[ ## note ## ]]") == stub.bodies()[0].__str__().count("[[ ## note ## ]]")


def test_a_second_unusable_answer_ends_the_call(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply("garbage"), sp.reply("garbage again"))
    result = ask(db, inv, stub)
    assert result.attempts == ["malformed", "malformed"] and result.failure == "malformed" and result.outputs is None


def test_a_refusal_is_not_retried(w, db, stub):
    inv = registration(w)
    stub.queue(sp.refusal())
    result = ask(db, inv, stub)
    assert result.attempts == ["refused"] and len(stub.requests) == 1
    assert calls(w, inv)[0].status == "succeeded"  # the provider charged for it: recorded with its usage


def test_a_role_check_that_fails_is_corrected_like_a_parse_failure(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="not json")), sp.reply(sp.fields(answer='{"ok": true}')))
    def check(outputs):
        try:
            json.loads(outputs["answer"])
        except ValueError:
            return "malformed"
        return None
    result = ask(db, inv, stub, check=check)
    assert result.attempts == ["malformed", "ok"] and result.outputs == {"answer": '{"ok": true}'}


def test_a_reply_without_usage_is_unreadable_failed_and_counted_at_its_maximum(w, db, stub):
    """litellm cannot read a reply with no usage block (it raises a connection error): the call is
    recorded as failed with no usage, counted at its maximum cost, and tried once more like an
    unavailable provider. Nothing is ever counted below its maximum when the cost is not known."""
    inv = registration(w)
    stub.queue(sp.no_usage(sp.fields(answer="Free?")), sp.no_usage(sp.fields(answer="Free?")))
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable"] * 2 and result.outputs is None
    rows = calls(w, inv)
    assert [(r.status, r.cost) for r in rows] == [("failed", None), ("failed", None)]
    assert w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month") == sum(r.max_cost for r in rows)


def test_a_readable_reply_with_empty_usage_is_cost_unknown(w, db, stub):
    """The engine's own check, for a reply litellm can read but whose usage is empty."""
    class Inner:
        def complete(self, request):
            from types import SimpleNamespace
            return SimpleNamespace(usage=None, finish_reason="stop", text="[[ ## answer ## ]]\nx", tool_calls=())

        def close(self):
            pass

    inv = registration(w)
    engine = lm.RecordedEngine(db, inv, MODEL, max_output_chars=100)
    engine._inner = Inner()
    from dspy.lm15 import Request, Config
    from dspy._vendor.lm15.types import Message
    with pytest.raises(lm.AgentFailure) as failed:
        engine.complete(Request(model=MODEL, messages=(Message.user("q"),), config=Config(max_tokens=10)))
    assert failed.value.code == "cost_unknown" == engine.last_failure
    [row] = calls(w, inv)
    assert (row.status, row.cost, row.error) == ("failed", None, "cost_unknown")


def test_a_reply_whose_recording_fails_is_discarded_and_the_call_stays_open(w, db, stub, monkeypatch):
    inv = registration(w)
    real = spend.finish

    def broken(engine, call, status, **kw):
        if status == "succeeded":
            raise RuntimeError(f"database gone {PLANTED}")
        return real(engine, call, status, **kw)

    monkeypatch.setattr(spend, "finish", broken)
    stub.queue(sp.reply(sp.fields(answer="Kept?")))
    result = ask(db, inv, stub)
    assert result.attempts == ["recording_failed"] and result.outputs is None
    assert calls(w, inv)[0].status == "started"  # counted at its maximum cost; recovery is step 9


def test_an_unpriced_model_is_refused_before_anything_is_reserved(w, db, stub):
    inv = registration(w)
    with pytest.raises(prices.UnknownModel):
        call_agent(db, inv, Ask, {"question": "q"}, model="some-other-model", max_tokens=10, max_output_chars=10,
                   client_options=sp.client_options(stub))
    assert calls(w, inv) == [] and stub.requests == []


# --- reservation and caps ------------------------------------------------------------------------------

def spent(w, inv_or_run, amount, run=False):
    """A finished call of `amount` on a run's invocation or a registration invocation."""
    if run:
        inv = w.invocation(inv_or_run, w.stage(inv_or_run))
    else:
        inv = inv_or_run
    call = spend.reserve(w.e, inv, MODEL, Decimal(amount))
    spend.finish(w.e, call, "succeeded", input_tokens=1, output_tokens=1, cached_tokens=0, cost=Decimal(amount))
    return inv


def refusals(w):
    return [(r.function, r.allowed, r.detail["code"]) for r in
            w.rows("SELECT function, allowed, detail FROM audit_log WHERE function = 'model_call' ORDER BY id")]


def test_the_run_cap_refuses_a_request_before_it_is_sent(w, db, stub):
    rid = w.running(agents=True)
    inv = spent(w, rid, "1.999", run=True)
    stub.queue(sp.reply(sp.fields(answer="x")))
    result = ask(db, inv, stub)
    assert result.attempts == ["spending_cap_run"] and stub.requests == []
    assert refusals(w) == [("model_call", False, "spending_cap_run")]
    assert w.val("SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1


def test_the_curation_cap_and_a_ceiling_refuse_before_sending(w, db, stub):
    inv = spent(w, registration(w), "1.999")
    assert ask(db, inv, stub).attempts == ["spending_cap_curation"]
    fresh = registration(w, "other")
    assert ask(db, fresh, stub, ceiling=Decimal("0.0001")).attempts == ["ceiling_reached"]
    assert stub.requests == [] and [c for _, _, c in refusals(w)] == ["spending_cap_curation", "ceiling_reached"]


def test_the_month_cap_counts_every_call_including_unconfirmed_ones(w, db, stub):
    big = spent(w, registration(w, "a"), "1.99")
    for i in range(24):
        spent(w, registration(w, f"m{i}"), "1.99")      # 25 x 1.99 = 49.75 this month
    open_call = spend.reserve(db, registration(w, "open"), MODEL, Decimal("0.249"))  # started: counts at its max
    assert open_call and big
    result = ask(db, registration(w, "last"), stub)
    assert result.attempts == ["spending_cap_month"] and stub.requests == []


def test_two_reservations_cannot_both_pass_the_month_cap(w, db):
    for i in range(25):
        spent(w, registration(w, f"m{i}"), "1.99")      # 49.75
    a, b = registration(w, "a"), registration(w, "b")
    outcomes, barrier = [], threading.Barrier(2)

    def go(inv):
        barrier.wait()
        try:
            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal("0.2"))))
        except spend.SpendingRefused as refused:
            outcomes.append(("refused", refused.code))

    threads = [threading.Thread(target=go, args=(i,)) for i in (a, b)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(o[0] for o in outcomes) == ["ok", "refused"]
    assert [o[1] for o in outcomes if o[0] == "refused"] == ["spending_cap_month"]


def test_no_database_transaction_is_open_while_a_request_is_in_flight(w, db, stub):
    inv = registration(w)
    seen = []

    def watch():
        with db.connect() as conn:
            seen.append(conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                "AND pid <> pg_backend_pid() AND state LIKE 'idle in transaction%'")).scalar())

    stub.on_request(watch)
    stub.queue(sp.error(500, "api_error"), sp.reply(sp.fields(answer="ok")))
    ask(db, inv, stub)
    assert seen == [0, 0]


def test_the_price_table_names_the_owners_models():
    from hypocurate.pipeline.agents.settings import MODELS
    assert set(MODELS.values()) <= set(prices.PRICES)
    assert prices.PRICES["claude-opus-5-5"].input == 4 and prices.PRICES["claude-opus-5-5"].output == 20
    assert prices.PRICES["claude-sonnet-5-5"].input == 2 and prices.PRICES["claude-sonnet-5-5"].output == 10
    assert prices.PRICES["claude-haiku-4-5"].input == 1 and prices.PRICES["claude-haiku-4-5"].output == 5
    # The bound covers the request's bytes and its output limit at full price.
    assert prices.max_cost(MODEL, 1000, 100) == (Decimal(2000) * 2 + Decimal(100) * 10) / 1_000_000


def test_a_reservation_waits_for_the_month_wide_lock(w, db):
    """Deterministic: while another transaction holds the month-wide lock, a reservation waits, so two
    reservations never read the month's total at the same time. (The race test above may pass by
    timing alone; this one cannot.)"""
    inv = registration(w)
    done = threading.Event()
    with db.connect() as holder:
        holder.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=spend.MONTH_LOCK_KEY))
        thread = threading.Thread(target=lambda: (spend.reserve(db, inv, MODEL, Decimal("0.01")), done.set()))
        thread.start()
        assert not done.wait(1.5)  # still waiting for the lock
        holder.rollback()          # releases it
    assert done.wait(10)
    thread.join()
    assert len(calls(w, inv)) == 1


# --- review fixes (ChatGPT, 2026-10-07) -------------------------------------------------------------------------
# Finding 3: the serialization lock is taken before the invocation's (or run's) total is read.

def _waiting_for_advisory_locks(db, n, timeout=10.0):
    import time
    deadline = time.monotonic() + timeout
    with db.connect() as conn:
        while time.monotonic() < deadline:
            waiting = conn.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted"))
            if waiting.scalar_one() >= n:
                return
            conn.rollback()
            time.sleep(0.05)
    raise AssertionError(f"{n} reservations never waited for the month-wide lock")


def _race(db, inv, amount, ceiling=None):
    """Two reservations on the same invocation, released together: deterministic, not timing-dependent.
    Both are made to wait for the month-wide lock first; if either read its total before taking the lock,
    both would read the same stale total."""
    outcomes = []

    def go():
        try:
            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal(amount), ceiling)))
        except spend.SpendingRefused as refused:
            outcomes.append(("refused", refused.code))

    with db.connect() as holder:
        holder.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=spend.MONTH_LOCK_KEY))
        threads = [threading.Thread(target=go) for _ in range(2)]
        [t.start() for t in threads]
        _waiting_for_advisory_locks(db, 2)
        holder.rollback()
    [t.join(30) for t in threads]
    return sorted(outcomes)


def test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap(w, db):
    inv = spent(w, registration(w), "1.70")
    outcomes = _race(db, inv, "0.20")
    assert [o[0] for o in outcomes] == ["ok", "refused"] and outcomes[1][1] == "spending_cap_curation"
    assert w.val("SELECT sum(coalesce(cost, max_cost)) FROM model_call WHERE invocation_id = :i", i=inv) <= 2


def test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling(w, db):
    inv = spent(w, registration(w), "0.30")
    outcomes = _race(db, inv, "0.15", ceiling=Decimal("0.50"))
    assert [o[0] for o in outcomes] == ["ok", "refused"] and outcomes[1][1] == "ceiling_reached"
    assert w.val("SELECT sum(coalesce(cost, max_cost)) FROM model_call WHERE invocation_id = :i", i=inv) <= Decimal(
        "0.50")


def test_two_reservations_on_one_run_cannot_both_pass_the_run_cap(w, db):
    rid = w.running(agents=True)
    inv = spent(w, rid, "1.70", run=True)
    outcomes, done = [], []

    def go():
        try:
            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal("0.20"))))
        except spend.SpendingRefused as refused:
            outcomes.append(("refused", refused.code))

    threads = [threading.Thread(target=go) for _ in range(2)]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    assert sorted(o[0] for o in outcomes) == ["ok", "refused"]
    assert [o[1] for o in outcomes if o[0] == "refused"] == ["spending_cap_run"]


# Finding 4: a recording failure on any branch stops the call; the reservation stays at its maximum.

class _NoUsage:
    """An engine whose reply litellm could read but whose usage is empty (the engine's own branch)."""
    requests = 0

    def __init__(self, **_):
        pass

    def complete(self, request):
        from types import SimpleNamespace
        type(self).requests += 1
        return SimpleNamespace(usage=None, finish_reason="stop", text="[[ ## answer ## ]]\nx", tool_calls=())

    def close(self):
        pass


@pytest.mark.parametrize("branch", ["provider_failure", "unreadable_reply", "no_usage", "success"])
def test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum(w, db, stub, monkeypatch, caplog, branch):
    from hypocurate.pipeline.agents import libraries
    inv = registration(w)

    def broken(*a, **kw):
        raise RuntimeError(f"database gone {PLANTED}")

    monkeypatch.setattr(spend, "finish", broken)
    if branch == "no_usage":
        _NoUsage.requests = 0
        monkeypatch.setattr(libraries, "litellm_engine", lambda **kw: _NoUsage(**kw))
    stub.queue(*{"provider_failure": [sp.error(500, "api_error")] * 2,
                 "unreadable_reply": [sp.no_usage(sp.fields(answer="x"))] * 2,
                 "no_usage": [],
                 "success": [sp.reply(sp.fields(answer="Kept?"))] * 2}[branch])
    result = ask(db, inv, stub)
    assert result.attempts == ["recording_failed"] and result.outputs is None
    assert len(stub.requests) + _NoUsage.requests * (branch == "no_usage") == 1   # no further request
    [row] = calls(w, inv)
    assert row.status == "started"                                                 # counted at its maximum
    assert w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month") == row.max_cost
    assert PLANTED not in caplog.text


def test_a_reservation_that_cannot_be_written_sends_nothing(w, db, stub, monkeypatch, caplog):
    inv = registration(w)

    def broken(*a, **kw):
        raise RuntimeError(f"database gone {PLANTED}")

    monkeypatch.setattr(spend, "reserve", broken)
    stub.queue(sp.reply(sp.fields(answer="x")))
    result = ask(db, inv, stub)
    assert result.attempts == ["reservation_failed"] and stub.requests == [] and calls(w, inv) == []
    assert PLANTED not in caplog.text and "RuntimeError" in caplog.text


# The overclaim on logs: the agent request path logs a failure's type and where it was raised, never its text.

def test_provider_error_text_never_reaches_the_process_log(w, db, stub, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    inv = registration(w)
    stub.queue(sp.error(400, "invalid_request_error", f"bad request {PLANTED}"))
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_rejected"]
    assert "agent_request_failure" in caplog.text and PLANTED not in caplog.text


# The request's headers (ChatGPT, question 1): exactly the transport's and the provider's own, no input in any.

def test_the_request_headers_carry_nothing_of_the_input(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="Yes.")))
    ask(db, inv, stub, question=f"Is it tension? {PLANTED}")
    [request] = stub.requests
    headers = {k.lower(): v for k, v in request["headers"].items()}
    assert set(headers) == {"host", "accept-encoding", "connection", "user-agent", "anthropic-version", "accept",
                            "content-type", "x-api-key", "content-length"}
    assert headers["x-api-key"] == sp.DUMMY_KEY and headers["anthropic-version"] == "2023-06-01"
    assert headers["user-agent"].startswith("litellm/") and headers["content-type"] == "application/json"
    assert not any(PLANTED in v or "tension" in v for v in headers.values())
    assert PLANTED in request["raw"].decode()  # the planted value is in the body, so the check above can fail


@pytest.mark.parametrize("facts, reason", [
    (None, None),
    ({"output_headers_present": {"answer": False}, "completed_marker": False, "header_count": 0, "answer_empty": True},
     "the answer was empty"),
    ({"output_headers_present": {"answer": False, "plan": True}, "completed_marker": True, "header_count": 2,
      "answer_empty": False}, "missing output field: answer"),
    ({"output_headers_present": {"answer": True}, "completed_marker": False, "header_count": 1, "answer_empty": False},
     "missing the closing completed marker"),
    ({"output_headers_present": {"answer": True}, "completed_marker": True, "header_count": 2, "answer_empty": False},
     None),
])
def test_the_reason_for_an_unreadable_answer_comes_from_its_form_facts_only(facts, reason):
    """Owner, 2026-10-10: the specific reason named in the corrective note; never the answer's text."""
    assert interface.parse_reason(facts) == reason
