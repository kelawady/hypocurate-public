"""Step 8b, milestone 4: the Planner, the narrowing decision and the partly-sufficient copy (owner, Q5, A1, A8,
A11). Every model call goes to the local stub provider: no live call."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import completion, narrowing, queries
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline.agents import planner
from hypocurate.pipeline.agents.settings import PLANNER_INSTRUCTION
from hypocurate.pipeline.statistics import PARTLY_SUFFICIENT_WORDING
from hypocurate.pipeline.writes import Refused

MPEA_CLASS = "multi-principal-element (high-entropy) alloy"
FCC_CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
PARTLY_CLAIM = ("In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, "
                "both at room temperature and at cryogenic temperatures (-196 °C)")
BCC_CLAIM = "Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C"
RT = {"band": "room temperature"}
CRYO = {"band": "cryogenic", "min": -200.0, "max": -150.0}
HOT = {"band": "elevated", "min": 950.0, "max": 1050.0}


def body(**over):
    b = {"domain_matches": True,
         "claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                         "temperature_band": [RT]},
         "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
    b.update(over)
    return b


def answer(**over) -> str:
    return sp.fields(plan=json.dumps(body(**over)))


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def running(engine, claim=FCC_CLAIM, sources=("mpea", "tamu_fcc"), register=True, sufficiency="fixed_minimum"):
    if register:
        pw.registered(engine, sources)
    q = queries.create(engine, claim, sources, sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    queries.start(engine, rid)
    return rid


def plan_run(engine, rid, stub, **kw):
    return planner.run_planner(engine, rid, client_options=sp.client_options(stub), **kw)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def stage(engine, rid):
    from hypocurate.access.stage import actual_stage
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=rid)).scalar_one()
        return actual_stage(conn, rid, status)


# --- the Planner's request and answer ------------------------------------------------------------------

def test_the_planners_complete_request_holds_no_outcome_value(engine, stub):
    """The planted-value test on the raw outbound bytes (PRD 4, 14.2): distinctive outcome values in the
    sealed source never reach the Planner; no tool is offered."""
    rows = [pw.mpea_row("CoCrNi", d, ys, doi=f"10.1016/j.test.2026.00{i}") for i, (d, ys) in
            enumerate([(1.0, 7311.375), (9.0, 6922.125), (4.0, 7104.875)])]
    pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
    rid = running(engine, sources=("mpea",), register=False)
    stub.queue(sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None
    [request] = stub.requests
    raw = request["raw"].decode()
    for v in ("7311.375", "6922.125", "7104.875", "7311.4", "6922.1", "7104.9", "14622.75"):
        assert v not in raw, v
    sent = json.loads(raw)
    assert "tools" not in sent
    assert PLANNER_INSTRUCTION in json.dumps(sent, ensure_ascii=False)
    assert FCC_CLAIM in raw and "record" in raw.lower()


def test_a_valid_answer_is_stored_and_its_plan_is_the_reference_plan(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and result.answer.domain_matches
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    built = planner.build_plan(vid, result.answer.claim_scope, result.answer.outcome, result.answer.exclusion_rules,
                               "fixed_minimum")
    assert built == plans.reference_plan(vid)  # field by field: the defaults plus the claim's scope
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=result.stage_id) == "done"
    assert one(engine, "SELECT output->'answer'->>'outcome' FROM stage_result WHERE id = :s",
               s=result.stage_id) == "yield_strength"


@pytest.mark.parametrize("over", [
    {"rules": {"min_grain_sizes": 1}},  # tries to weaken a fixed rule: not a key of the answer
    {"sufficiency": {"option": "use_available"}},  # the option is the query's, never the model's
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [RT], "eligibility_rules": []}},
    {"outcome": "hardness"},
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [{"band": "elevated"}]}},  # no range
    {"claim_scope": {"alloy_class": ["superalloy"], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [RT]}},
    {"exclusion_rules": [{"rule": "yield_strength_range", "min": 100}]},  # not on the menu
    {"exclusion_rules": [{"rule": "phase", "values": ["HCP"]}]},
    {"domain_matches": "yes"},
    # The shape is right but the plan is not valid (plan.validate): an elevated range inside room temperature.
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [{"band": "elevated", "min": 15.0, "max": 22.0}]}},
])
def test_an_invalid_plan_is_corrected_once_naming_only_the_code_then_the_stage_fails(engine, stub, over):
    rid = running(engine)
    bad = answer(**over)
    stub.queue(sp.reply(bad), sp.reply(bad))
    result = plan_run(engine, rid, stub)
    assert result.answer is None and result.failure == "invalid_plan"
    assert len(stub.requests) == 2
    retry = stub.requests[1]["raw"].decode()
    assert "invalid_plan" in retry and "hardness" not in retry.split("previous answer")[-1][:200]
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=result.stage_id) == "failed"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_a_corrected_answer_is_accepted(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer(outcome="hardness")), sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and len(stub.requests) == 2


def test_a_claim_of_another_domain_is_a_valid_answer(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer(domain_matches=False)))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and result.answer.domain_matches is False


def test_a_claim_that_is_not_one_plan_is_not_an_invalid_answer(engine, stub):
    """A11: two bands are a valid answer; no plan is built from it here (the narrowing decides)."""
    rid = running(engine)
    two = body()["claim_scope"] | {"temperature_band": [RT, CRYO]}
    stub.queue(sp.reply(answer(claim_scope=two)))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and not planner.one_plan(result.answer.claim_scope)


# --- the narrowing decision (pure) -----------------------------------------------------------------------

def cell(phase="FCC", test="tension", band=None, t=25.0, gs=True, ys="converted", n=1):
    status = {"phase_class": "converted", "test_type": "converted", "test_temperature": "converted" if t is not None
              else "not_reported", "test_temperature_band": "converted" if band else "not_reported",
              "grain_size": "converted" if gs else "not_reported", "yield_strength": ys,
              "ultimate_tensile_strength": "not_reported", "hardness": "not_reported", "hardness_sd": "not_reported",
              "yield_strength_sd": "not_reported"}
    return {"categories": {"phase_class": phase, "test_type": test, "test_temperature_band": band},
            "test_temperature": t, "status": status, "grain_size_present": gs, "n": n}


def counts(*cells):
    return [{"source": "mpea", "version_fingerprint": "f" * 64, "readable": True, "n_records": len(cells),
             "cells": list(cells)}]


def answer_of(**over):
    return planner.read_answer(body(**over))


TWO_BANDS = {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
             "temperature_band": [RT, CRYO]}
NARROWER = {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]}


def test_every_part_with_records_proceeds():
    d = narrowing.decide(answer_of(), counts(cell(n=5)), 1, "fixed_minimum")
    assert (d["result"], d["reason"], d["zero_parts"]) == ("proceed", "no_part_without_records", [])
    assert d["part_counts"] == [{"part": "phase_class", "value": "FCC", "n": 5},
                                {"part": "test_type", "value": "tension", "n": 5},
                                {"part": "temperature_band", "value": RT, "n": 5}]


def test_a_part_with_none_and_the_exact_narrower_scope_is_partly_sufficient():
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=NARROWER),
                         counts(cell(n=5), cell(t=-196.0, gs=False, n=9)), 1, "fixed_minimum")
    assert (d["result"], d["zero_parts"]) == ("partly_sufficient", [{"part": "temperature_band", "value": CRYO}])
    assert d["narrower_scope"] == NARROWER and "hypothesis_version" not in d["narrower_plan"]
    assert d["narrower_plan_fingerprint"] == plans.fingerprint(d["narrower_plan"])
    assert d["decision"]["evidence_level"] == 1 and d["decision"]["verdict"] is None
    assert d["decision"]["evidence_level_wording"] == PARTLY_SUFFICIENT_WORDING


@pytest.mark.parametrize("proposed", [
    None,
    {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [CRYO]},
    {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT, CRYO]},
])
def test_code_builds_the_narrower_scope_and_never_uses_the_planners(proposed):
    """Owner, 2026-10-07 (after live run C; was ..._not_exactly_the_parts_with_records_is_declined): the Planner
    cannot see which part has no usable record, so code builds the narrower scope; a proposal is stored only."""
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=proposed),
                         counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
    assert (d["result"], d["narrower_scope"]) == ("partly_sufficient", NARROWER)
    assert d["proposed_narrower"] == (planner.read_answer(body(claim_scope=TWO_BANDS, narrower=proposed)).narrower)


def test_a_one_plan_claim_with_a_part_without_records_is_narrowed_by_code():
    """(Was test_a_declined_narrowing_of_a_one_plan_claim_proceeds.)"""
    two_phases = body()["claim_scope"] | {"phase_class": ["FCC", "BCC"]}
    d = narrowing.decide(answer_of(claim_scope=two_phases, narrower=None), counts(cell(n=5)), 1, "fixed_minimum")
    assert (d["result"], d["zero_parts"]) == ("partly_sufficient", [{"part": "phase_class", "value": "BCC"}])
    assert d["narrower_scope"] == {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]}


def test_a_narrower_scope_that_is_not_one_plan_is_not_used():
    """Two alloy classes: no narrower scope is one plan, so the claim is not one plan."""
    two_classes = TWO_BANDS | {"alloy_class": [MPEA_CLASS, "steel"]}
    d = narrowing.decide(answer_of(claim_scope=two_classes), counts(cell(n=5), cell(t=-196.0, gs=False)), 1,
                         "fixed_minimum")
    assert (d["result"], d["reason"]) == ("claim_not_one_plan", "narrower_invalid")


def test_two_bands_each_with_records_are_not_one_plan():
    """A11: the run fails before the lock; no narrower question."""
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS), counts(cell(n=5), cell(t=-196.0, n=2)), 1, "fixed_minimum")
    assert (d["result"], d["reason"]) == ("claim_not_one_plan", "no_part_without_records")


def test_no_part_with_records_proceeds_to_an_insufficient_run():
    bcc_hot = body()["claim_scope"] | {"phase_class": ["BCC"], "temperature_band": [HOT]}
    d = narrowing.decide(answer_of(claim_scope=bcc_hot), counts(cell(phase="BCC", test="compression", t=1000.0,
                                                                      gs=False, n=90)), 1, "fixed_minimum")
    assert (d["result"], d["reason"]) == ("proceed", "no_part_with_records")


@pytest.mark.parametrize("c, counted", [
    (cell(ys="not_reported"), False), (cell(gs=False), False), (cell(t=None, band="room temperature"), True),
    (cell(t=None, band=None), False), (cell(t=30.0), False), (cell(test="compression"), False),
])
def test_a_record_counts_only_with_a_grain_size_the_outcome_and_a_known_condition(c, counted):
    parts = narrowing.part_counts(counts(c), planner.read_answer(body()).claim_scope, "yield_strength")
    assert all((x["n"] == 1) == counted for x in parts if x["part"] == "temperature_band")


# --- the narrowing decision on the frozen sources, and the partly-sufficient copy ----------------------

def partly_answer():
    return body(claim_scope=TWO_BANDS, narrower=NARROWER)


def test_the_frozen_sources_make_the_cryogenic_claim_partly_sufficient(engine):
    """Structure counts from the frozen files (no model): FCC tension at room temperature has records with a
    grain size and yield strength; at cryogenic temperature none."""
    rid = running(engine, claim=PARTLY_CLAIM)
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(partly_answer()))
    assert out["result"] == "partly_sufficient"
    by = {(x["part"], json.dumps(x["value"], sort_keys=True)): x["n"] for x in out["part_counts"]}
    assert by[("temperature_band", json.dumps(CRYO, sort_keys=True))] == 0
    assert by[("temperature_band", json.dumps(RT, sort_keys=True))] >= 89 + 93
    assert {s["source"] for s in out["sources"]} == {"mpea", "tamu_fcc"}
    assert stage(engine, rid) == "narrowed"


def test_the_frozen_sources_give_the_bcc_claim_nothing_to_test(engine):
    rid = running(engine, claim=BCC_CLAIM)
    bcc = body(claim_scope=body()["claim_scope"] | {"phase_class": ["BCC"], "test_type": ["compression"],
                                                      "temperature_band": [HOT]})
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(bcc))
    assert (out["result"], out["reason"]) == ("proceed", "no_part_with_records")
    assert stage(engine, rid) == "before_lock"


def test_the_partly_sufficient_original_is_completed_by_copying_and_its_narrower_question_created(engine):
    rid = running(engine, claim=PARTLY_CLAIM)
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(partly_answer()))
    decision = completion.copy_partly_sufficient(engine, rid)
    assert decision == out["decision"]
    with engine.connect() as conn:
        assert conn.execute(text("SELECT status, outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r"),
                            dict(r=rid)).one() == ("completed", "partly_sufficient", None, False, 1)
    q = queries.create_narrower(engine, rid, out["narrower_scope"])
    assert one(engine, "SELECT narrower_of_run_id FROM hypothesis WHERE id = :h", h=q.hypothesis_id) == rid


def test_the_copy_refuses_a_run_that_is_not_narrowed(engine):
    rid = running(engine)
    with pytest.raises(Refused) as refused:
        completion.copy_partly_sufficient(engine, rid)
    assert refused.value.code == "stage_mismatch"


def test_the_copy_refuses_a_decision_taken_on_other_source_versions(engine):
    rid = running(engine, claim=PARTLY_CLAIM)
    d = narrowing.decide(planner.read_answer(partly_answer()),
                         counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO stage_result (run_id, stage, status, finished_at, output) VALUES "
                          "(:r, 'narrowing', 'running', NULL, NULL)"), dict(r=rid))
        conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = CAST(:o AS jsonb) "
                          "WHERE run_id = :r AND stage = 'narrowing'"),
                     dict(r=rid, o=json.dumps({**d, "sources": [{"source": "mpea", "version_fingerprint": "f" * 64,
                                                                 "readable": True}]})))
    with pytest.raises(Refused) as refused:
        completion.copy_partly_sufficient(engine, rid)
    assert refused.value.code == "decision_not_current"
