"""Step 10a, owner's addition 2 (2026-10-11): a confirmation page sends back a fingerprint of the content it showed,
and `confirmation.confirm` refuses other content as `content_changed`, as it refuses other content given whole (step
9a). Whole runs through the orchestrator, every model call to the local stub."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries


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


def waiting(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
    return rid


def confirmations(engine, rid):
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM rules_confirmation WHERE run_id = :r"), dict(r=rid)).scalar()


def test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item():
    """Fix round 1, finding 1: the fingerprint covers the content and the text shown together (it covered the content
    alone before); key order does not count, list order and any item do."""
    import hashlib
    import json
    c = {"run": 1, "query": "Q-0001", "cost_so_far": {"counted_usd": "0.017640", "calls": 1}, "names": ["ä", "b"]}
    words = "Run 1 of Q-0001 waits."
    expected = hashlib.sha256(json.dumps({"content": c, "text": words}, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False).encode("utf-8")).hexdigest()
    assert confirmation.shown_fingerprint(c, words) == expected
    assert confirmation.shown_fingerprint(dict(reversed(list(c.items()))), words) == expected  # key order does not count
    assert confirmation.shown_fingerprint({**c, "cost_so_far": {"counted_usd": "0.017641", "calls": 1}}, words) != expected
    assert confirmation.shown_fingerprint({**c, "names": ["b", "ä"]}, words) != expected  # list order does


def test_a_matching_fingerprint_confirms(engine, stub):
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
    assert stored["shown"] == words and confirmations(engine, rid) == 1


@pytest.mark.parametrize("sent", ["", "0" * 64, "not hex"])
def test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded(engine, stub, sent):
    rid = waiting(engine, stub)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=sent)
    assert refused.value.code == "content_changed"
    assert confirmations(engine, rid) == 0


def test_content_that_changed_after_it_was_shown_is_refused(engine, stub, monkeypatch):
    """What `confirm` compares is the content as it reads inside its own transaction: content that differs from what
    the page showed (here one item more) is refused."""
    rid = waiting(engine, stub)
    shown = confirmation.shown_fingerprint(*confirmation.show(engine, rid))
    original = confirmation.content
    monkeypatch.setattr(confirmation, "content", lambda conn, run_id: {**original(conn, run_id), "changed": True})
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=shown)
    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0


def test_the_text_shown_says_informative_groups_the_label_now_and_once_confirmed_and_counts_calls_rightly(engine, stub):
    """The live-run record's open items 2 and 4 (step 10a, a4) and the owner's review: "informative groups", the label
    at the moment of confirming, and "1 model call" in the singular."""
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    assert "10 informative groups" in words and "independent" not in words
    assert "Question as tested: yield strength against grain size" in words
    assert "  Now labelled: the Planner's reading of the claim; not verified by code and, in this version, not " \
           "confirmed by a person" in words.split("\n")
    assert "  Once confirmed, labelled: the Planner's reading of the claim; not verified by code; confirmed by the " \
           "person who confirms on the time of confirming (UTC)" in words.split("\n")
    assert content["cost_so_far"]["calls"] == 1 and "(reported $" in words and "; 1 model call, 0 without" in words
    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
    assert stored["shown"] == words  # what is stored is exactly what was shown


def test_the_label_once_confirmed_follows_the_readings_own_wording():
    from hypocurate.pipeline import reading
    assert confirmation.label_once_confirmed(reading.LABELS["planner"], "Ada", "2026-10-11 10:00:00 UTC") == \
        reading.CONFIRMED_LABEL.format(by="Ada", at="2026-10-11 10:00:00 UTC")
    assert confirmation.label_once_confirmed(reading.LABELS["narrower"], "Ada", "then") == \
        reading.LABELS["narrower"] + "; confirmed by Ada on then"


# --- Fix round 1, finding 1 (ChatGPT, accepted by the owner, 2026-10-11): the fingerprint covers the text shown ------

def test_a_renderer_changed_between_display_and_submission_is_refused(engine, stub, monkeypatch):
    """The page showed one wording; the code that renders it changed before the person confirmed (a deploy). The
    content is the same, but the text that would be stored is not what the person saw: refused, nothing recorded."""
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    shown = confirmation.shown_fingerprint(content, words)
    original = confirmation.render
    monkeypatch.setattr(confirmation, "render",
                        lambda c: original(c).replace("informative groups", "independent groups"))
    assert confirmation.render(content) != words  # only the renderer changed
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=shown)
    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0


def test_the_fingerprint_covers_the_content_and_the_text_together():
    c = {"run": 1, "query": "Q-0001"}
    assert confirmation.shown_fingerprint(c, "a") != confirmation.shown_fingerprint(c, "b")
    assert confirmation.shown_fingerprint(c, "a") != confirmation.shown_fingerprint({**c, "run": 2}, "a")
    import hashlib
    import json
    assert confirmation.shown_fingerprint(c, "a") == hashlib.sha256(json.dumps(
        {"content": c, "text": "a"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def test_what_is_stored_is_exactly_the_text_the_fingerprint_covered(engine, stub):
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
    with engine.connect() as conn:
        assert conn.execute(text("SELECT shown FROM rules_confirmation WHERE run_id = :r"), dict(r=rid)).scalar() \
            == words == stored["shown"]


def test_the_command_line_refuses_a_text_that_changed_after_it_was_printed(engine, stub, monkeypatch, capsys):
    """Fix round 1, finding 1, on the command line: `confirm` prints the text, then records; if the renderer gives
    another text by then, nothing is recorded."""
    from hypocurate import cli_runs
    rid = waiting(engine, stub)
    original, calls = confirmation.render, []

    def changing(c):
        calls.append(1)
        words = original(c)
        return words if len(calls) == 1 else words.replace("informative groups", "independent groups")

    monkeypatch.setattr(confirmation, "render", changing)
    with pytest.raises(queries.QueryRefused) as refused:
        cli_runs._confirm(engine, rid, "Grace Reviewer")
    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0
    assert "10 informative groups" in capsys.readouterr().out  # what was printed
