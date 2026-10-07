"""Step 8b, milestone 6: the Analyst and its text checks (owner, Q6, Q8, A3, B2). Every model call goes to the
local stub provider."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis
from hypocurate.pipeline.agents import analyst, text_checks
from hypocurate.pipeline.agents.settings import ANALYST_INSTRUCTION
from stats_world import run_on, small_rows

FACTS = {"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
                      "verdict_wording": "supported under the stated model, in the sources searched"},
         "analyses": [{"estimate": 424.93, "std_error": 64.41, "p_value": 1.3e-06, "n_records": 97,
                       "detection": 0.0465, "largest_paper_share": 0.387}]}


# --- the number check -------------------------------------------------------------------------------------

@pytest.mark.parametrize("phrase", [
    "k = 424.93", "k = 424.9 ± 64.4", "k is about 425", "97 records", "p ≈ 1.3e-6", "p = 1.3 × 10^-6",
    "p = 1.3×10⁻⁶", "4.65%", "38.7% of the slope information", "the model k × (grain size)^-1/2",
    "a 95% interval", "validity check 2", "4.7%",
])
def test_numbers_as_given_or_rounded_to_their_shown_precision_match(phrase):
    assert text_checks.unmatched_numbers(phrase, FACTS) == []


@pytest.mark.parametrize("phrase, bad", [
    ("k = 427", "427"), ("k = 424.95", "424.95"), ("98 records", "98"), ("p = 1.4e-6", "1.4e-6"),
    ("4.6%", "4.6%"), ("about 6×10^-7", "6×10^-7"), ("1,000 records", "1,000"),
])
def test_a_number_not_in_the_facts_is_caught(phrase, bad):
    assert text_checks.unmatched_numbers(phrase, FACTS) == [bad]


# --- the wording check ------------------------------------------------------------------------------------

GOOD = "The result is sufficient in the sources searched, and k > 0 is supported under the stated model, in the " \
       "sources searched."
NONE = {"outcome_wording": "insufficient in the sources searched", "verdict": None}


@pytest.mark.parametrize("text_, decision, problems", [
    (GOOD, FACTS["decision"], []),
    ("The result is sufficient.", FACTS["decision"], ["outcome wording missing", "verdict wording missing"]),
    ("Insufficient in the sources searched: grain sizes do not exist for BCC alloys.", NONE,
     ["forbidden: do not exist"]),
    ("Insufficient in the sources searched, yet the claim is supported.", NONE,
     ["a verdict is stated where there is none"]),
    ("Insufficient in the sources searched; this proves nothing either way.", NONE, ["forbidden: proves"]),
    ("Insufficient in the sources searched. The supported model needs grain sizes.", NONE, []),
])
def test_the_wording_rules(text_, decision, problems):
    assert text_checks.wording_problems(text_, decision) == problems


# --- the Analyst's call -----------------------------------------------------------------------------------

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


def reply(report):
    return sp.reply(sp.fields(report=report))


def below_minimums(engine):
    rid = run_on(engine, small_rows(3, papers=3, base=7311.0), agents=("analyst",))
    analysis.run_statistics(engine, rid)
    return rid


BELOW = ("The data are insufficient in the sources searched: the pooled set has 6 records, below the minimum of 30, "
         "so no test was run and no estimate is shown.")


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_below_the_minimums_the_analysts_request_holds_no_outcome_value(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and out.report == BELOW
    raw = stub.requests[0]["raw"].decode()
    with engine.connect() as conn:
        values = [float(v) for v in conn.execute(text("SELECT harmonized->'yield_strength'->>'value' FROM record "
                                                      "WHERE extraction_run_id = :r"), dict(r=rid)).scalars()]
    for v in values:
        assert repr(v) not in raw and f"{v:g}" not in raw, v
    sent = json.loads(raw)
    assert "tools" not in sent and ANALYST_INSTRUCTION in json.dumps(sent, ensure_ascii=False)
    assert one(engine, "SELECT output->>'report' FROM stage_result WHERE id = :s", s=out.stage_id) == BELOW


@pytest.mark.parametrize("bad, code", [
    ("The data are insufficient in the sources searched: 31 records were found.", "numbers_unmatched"),
    ("The data are insufficient in the sources searched: grain sizes do not exist.", "wording_refused"),
    ("The data are insufficient in the sources searched, but the claim is supported.", "wording_refused"),
])
def test_a_text_failing_a_check_twice_is_discarded(engine, stub, bad, code):
    rid = below_minimums(engine)
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, code) and len(stub.requests) == 2
    retry = stub.requests[1]["raw"].decode()
    assert code in retry
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stage_id) == "failed"
    assert one(engine, "SELECT output->>'shown' FROM stage_result WHERE id = :s", s=out.stage_id) == \
        f"explanation unavailable ({code})"
    assert one(engine, "SELECT output ? 'report' FROM stage_result WHERE id = :s", s=out.stage_id) is False


def test_a_corrected_text_is_stored(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply("The data are insufficient: 31 records."), reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.report == BELOW and len(stub.requests) == 2


def test_the_analyst_changes_no_stored_decision(engine, stub):
    rid = below_minimums(engine)
    before = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid)
    stub.queue(reply(BELOW))
    analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid) == before
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"


# --- the owner's additions before the live set (2026-10-07): recorded responses through the stub -------------

def exploratory(engine):
    """A run above the validity checks under 'use what is available': its facts hold a p-value and the paper
    figures (informative papers, effective number, largest share, degrees of freedom)."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    pooled = out["analyses"][0]
    c = pooled["counts"]
    d = out["decision"]
    return rid, {"outcome": d["outcome_wording"], "verdict": d["verdict_wording"], "estimate": repr(pooled["estimate"]),
                 "p": repr(pooled["p_value"]), "informative": c["n_groups_informative"],
                 "effective": repr(c["effective_papers"]), "share": repr(c["largest_paper_share"]), "df": pooled["df"]}


def follows_all(f):
    return (f"The data are {f['outcome']}, and the claim is {f['verdict']}. The pooled estimate is {f['estimate']}. "
            f"The approximate, nominal, one-sided cluster-robust p-value is {f['p']}. It rests on {f['informative']} "
            f"informative papers, an effective number of {f['effective']}, a largest share of {f['share']} and "
            f"{f['df']} degrees of freedom.")


BREAKS = {
    "causes": lambda f: follows_all(f) + " Grain refinement causes the strengthening.",
    "caused by": lambda f: follows_all(f) + " The rise is caused by smaller grains.",
    "causal": lambda f: follows_all(f) + " The link is causal.",
    "confirms the claim": lambda f: follows_all(f) + " This confirms the claim.",
    "confirms the hypothesis": lambda f: follows_all(f) + " This confirms the hypothesis.",
    "effective number as independent": lambda f: follows_all(f).replace(
        f"an effective number of {f['effective']}", f"an effective number of {f['effective']} independent papers"),
    "p-value without approximate": lambda f: follows_all(f).replace("approximate, nominal, ", "nominal, "),
    "informative count alone": lambda f: (f"The data are {f['outcome']}, and the claim is {f['verdict']}. It rests on "
                                          f"{f['informative']} informative papers."),
}


def test_a_text_following_every_rule_is_stored(engine, stub):
    rid, f = exploratory(engine)
    stub.queue(reply(follows_all(f)))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and out.report == follows_all(f) and len(stub.requests) == 1


@pytest.mark.parametrize("rule", sorted(BREAKS))
def test_a_text_breaking_each_new_rule_is_refused(engine, stub, rule):
    rid, f = exploratory(engine)
    bad = BREAKS[rule](f)
    assert bad != follows_all(f)
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, "wording_refused") and len(stub.requests) == 2
