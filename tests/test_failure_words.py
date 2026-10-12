"""Step 10b (owner's request of 2026-10-11): a failed run is explained in plain English first - what happened, what was
and was not done, what the person can do next - with the codes second, as "Technical detail: …"; a source a run never
reached reads "not searched (the run ended first)"; the runs list uses the same plain wording."""
from __future__ import annotations

import re

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import failure_words, orchestrator, queries, run_view
from hypocurate.pipeline.agents import spend
from test_queries_step9a import _spend_this_month
from test_web_runs import plain, signed_in

OWNERS_EXAMPLE = ("The run stopped before anything was tested. The Planner proposed a plan twice, and both times code's "
                  "checks refused it, so nothing was locked or searched. You can dispatch the question again as a new "
                  "run.")


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def own(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e, migrated_database
    e.dispose()


def failed_planner_run(engine, stub):
    stub.respond(to.responder(to.planner_body(outcome="hardness")))  # refused by code's checks, twice
    rid = to.dispatched(engine)
    report = orchestrator.run(engine, rid, client_options=sp.client_options(stub))
    assert report.status == "failed" and report.failure.startswith("planner_failed:")
    return rid


def explained(engine, rid):
    with engine.connect() as conn:
        reason = conn.execute(text("SELECT failure_reason FROM run WHERE id = :r"), dict(r=rid)).scalar_one()
        return failure_words.explain(conn, rid, reason)


def test_the_owners_example_a_planner_refused_twice(own, stub):
    engine, url = own
    rid = failed_planner_run(engine, stub)
    e = explained(engine, rid)
    assert e["words"] == OWNERS_EXAMPLE
    assert e["technical"] == "Technical detail: planner_failed, invalid_plan."
    assert e["reasons"]  # this version stores the reason for each refused attempt, in code's words
    page = signed_in(engine, url).get(f"/runs/{rid}").text
    shown = plain(page)
    assert shown.index(OWNERS_EXAMPLE) < shown.index("Technical detail: planner_failed, invalid_plan.")
    assert "Code's reasons for refusing the Planner's answers:" in shown
    assert "Failed: planner_failed" not in shown  # the codes come second, never first
    for name in ("MPEA dataset (Borg et al. 2020)", "Texas A&M FCC dataset (Mulukutla et al. 2026)"):
        assert f"{name}: not searched (the run ended first)" in shown and f"{name}: pending" not in shown


def test_the_runs_list_says_it_in_plain_words_too(own, stub):
    engine, url = own
    rid = failed_planner_run(engine, stub)
    row = re.search(rf'href="/runs/{rid}".*?<td data-label="Status">([^<]*)</td>',
                    signed_in(engine, url).get("/runs").text, re.S).group(1)
    assert row == "failed: the Planner&#39;s plan was refused"


def test_a_cancelled_run_names_the_person_and_says_what_was_done(own, stub):
    engine, _ = own
    queued = to.dispatched(engine, fixed_plan=True)
    queries.cancel(engine, queued, by="Grace Reviewer")
    assert explained(engine, queued)["words"] == (
        "The run was cancelled by Grace Reviewer before it started: nothing was asked, locked, searched or paid for. "
        "You can dispatch the question again as a new run.")
    stub.respond(to.responder(to.planner_body()))
    waiting = to.dispatched(engine)
    assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
    queries.cancel(engine, waiting, by="Grace Reviewer")
    e = explained(engine, waiting)
    assert e["words"].startswith("The run was cancelled by Grace Reviewer while it waited for a person to confirm")
    assert e["technical"] == "Technical detail: cancelled."


def test_a_spending_cap_says_which_cap_and_what_to_do(own, stub):
    engine, _ = own
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "failed"
    e = explained(engine, rid)
    assert e["words"] == ("The run stopped because its next model request would have gone over this month's spending "
                          "cap; the request was not sent and nothing more was paid for. Nothing was locked or "
                          "searched. Dispatch it again next month, or once the owner raises the monthly cap.")
    assert e["technical"] == "Technical detail: spending_refused, spending_cap_month."


@pytest.mark.parametrize("reason, start", [
    ("domain_mismatch: x", "The run stopped before anything was tested: the Planner judged that the claim belongs"),
    ("claim_not_one_plan: x (narrower_missing)", "The run stopped before anything was tested: the claim covers more"),
    ("interrupted: x", "The run stopped because the worker was interrupted twice while the Planner was being asked"),
    ("attempts_exhausted: the run stopped at analysis 4 times", "The run stopped after the worker was interrupted"),
    ("refused: a checkpoint or write refused (invariant_broken)", "The run stopped because code refused one of its steps"
                                                                   " (the primary set breaks a rule no plan can change"),
    ("planner_failed: x (provider_unavailable)", "The run stopped before anything was tested: the model provider could "
                                                 "not be reached"),
    ("planner_failed: x (malformed)", "The run stopped before anything was tested. The Planner answered once, but"),
    ("something_new: an unforeseen stop", "The run stopped: an unforeseen stop. Nothing was locked or searched."),
])
def test_every_stored_failure_reads_as_plain_words_first(own, reason, start):
    engine, _ = own
    rid = to.dispatched(engine, fixed_plan=True)
    with engine.connect() as conn:
        e = failure_words.explain(conn, rid, reason)
    assert e["words"].startswith(start), e["words"]
    assert e["words"].endswith(".") and "  " not in e["words"] and "_" not in e["words"]
    assert e["technical"].startswith("Technical detail: ")


def test_every_failure_code_the_orchestrator_stores_has_its_own_explanation():
    for code in orchestrator.REASONS:
        if code != "planner_failed":
            assert code in failure_words.EXPLAIN, code
    assert set(failure_words.SHORT) == set(failure_words.EXPLAIN)


def test_a_completed_run_never_shows_a_source_as_pending(own):
    """A completed run whose source was never searched (as when the run stopped short of it) reads 'not searched'."""
    engine, url = own
    rid = to.dispatched(engine, fixed_plan=True)
    queries.cancel(engine, rid, by="Ada")
    page = run_view.run_page(engine, rid)
    assert {s["status"] for s in page["sources"]} == {run_view.NOT_REACHED}
