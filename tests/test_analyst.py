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

from hypocurate.pipeline import display

# Step 8b (owner, 2026-10-07, after the live set): the facts carry display strings and ready-made phrases; the
# number check compares tokens exactly (was: rounding to the shown precision accepted).
FACTS = display.display({"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
                                      "verdict_wording": "supported under the stated model, in the sources searched"},
                         "analyses": [{"estimate": 424.93, "std_error": 64.41, "n_records": 97, "detection": 0.0465,
                                       "largest_paper_share": 0.387,
                                       "p_value_phrase": display.p_phrase(1.287e-06),
                                       "paper_figures_phrase": display.figures_phrase(20, 3.9358, 0.38673, 19)}]})


def test_the_facts_carry_display_strings_and_phrases():
    a = FACTS["analyses"][0]
    assert (a["estimate"], a["std_error"], a["detection"], a["largest_paper_share"]) == ("424.9", "64.4", "4.7%", "38.7%")
    assert a["p_value_phrase"] == "p ≈ 1.3e-6 (approximate, nominal, one-sided)"
    assert a["paper_figures_phrase"] == ("20 informative papers, an effective number of papers of 3.94, a largest "
                                         "share of 38.7% and 19 degrees of freedom")


@pytest.mark.parametrize("phrase", [
    "k = 424.9 ± 64.4", "97 records", "p ≈ 1.3e-6 (approximate, nominal, one-sided)", "4.7%",
    "38.7% of the slope information", "the model k × (grain size)^-1/2", "a 95% interval", "validity check 2",
    "an effective number of papers of 3.94",
])
def test_numbers_exactly_as_given_match(phrase):
    assert text_checks.unmatched_numbers(phrase, FACTS) == []


@pytest.mark.parametrize("phrase, bad", [
    ("p was 1.4e-6.", "1.4e-6"),  # scientific notation at the end of a sentence is one token
    ("k = 424.93", "424.93"), ("k is about 425", "425"), ("98 records", "98"), ("p = 1.4e-6", "1.4e-6"),
    ("4.65%", "4.65%"), ("0.387", "0.387"), ("1,000 records", "1000"), ("p = 1.3e-06", "1.3e-06"),
])
def test_a_number_not_given_as_shown_is_caught(phrase, bad):
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
    (GOOD + " The pooled p ≈ 1.3e-6 (approximate, nominal, one-sided).", FACTS["decision"], []),
    (GOOD + " The p-value is 1.3e-6.", FACTS["decision"], ["a p-value outside its ready-made phrase"]),
    (GOOD + " The value 1.3e-6 is small.", FACTS["decision"], ["a p-value outside its ready-made phrase"]),
    (GOOD + " It rests on 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and "
            "19 degrees of freedom.", FACTS["decision"], []),
    (GOOD + " It rests on 20 informative papers.", FACTS["decision"], ["paper figures outside their ready-made phrase"]),
    (GOOD + " The effective number is not a count of independent papers.", FACTS["decision"],
     ["the effective number described as independent"]),
])
def test_the_wording_rules(text_, decision, problems):
    assert text_checks.wording_problems(text_, decision, FACTS) == problems


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
    """A run above the validity checks under 'use what is available': its facts hold a p-value phrase and a paper
    figures phrase. Returns the run and the display strings and phrases the Analyst is given."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    pooled = out["analyses"][0]
    c = pooled["counts"]
    d = out["decision"]
    return rid, {"outcome": d["outcome_wording"], "verdict": d["verdict_wording"],
                 "estimate": display.one_decimal(pooled["estimate"]), "p": display.p_value(pooled["p_value"]),
                 "p_phrase": display.p_phrase(pooled["p_value"]), "informative": c["n_groups_informative"],
                 "figures": display.figures_phrase(c["n_groups_informative"], c["effective_papers"],
                                                   c["largest_paper_share"], pooled["df"]),
                 "raw": pooled}


def follows_all(f):
    return (f"The data are {f['outcome']}, and the claim is {f['verdict']}. The pooled estimate is {f['estimate']}, "
            f"with {f['p_phrase']}. It rests on {f['figures']}.")


def diagnostic_shape(f):
    """The shape of the live diagnostic answer (2026-10-07): full float precision, the description written out once
    and then referred to, the figures given one by one."""
    r = f["raw"]
    c = r["counts"]
    return (f"The data are {f['outcome']}, and the claim is {f['verdict']}. The estimated coefficient is "
            f"{r['estimate']!r}. The p-value is {r['p_value']!r}, an approximate, nominal, one-sided cluster-robust "
            f"p-value under the locked method. A sensitivity estimate has a p-value of {r['p_value']!r} (same "
            f"description as above). The support comes from {c['n_groups_informative']} informative papers, an "
            f"effective number of {c['effective_papers']!r}, a largest share of {c['largest_paper_share']!r}, and "
            f"{r['df']} degrees of freedom.")


BREAKS = {
    "causes": lambda f: follows_all(f) + " Grain refinement causes the strengthening.",
    "caused by": lambda f: follows_all(f) + " The rise is caused by smaller grains.",
    "causal": lambda f: follows_all(f) + " The link is causal.",
    "confirms the claim": lambda f: follows_all(f) + " This confirms the claim.",
    "confirms the hypothesis": lambda f: follows_all(f) + " This confirms the hypothesis.",
    "effective number as independent": lambda f: follows_all(f) + " The effective number counts independent papers.",
    "p-value outside its phrase": lambda f: follows_all(f) + f" The p-value is {f['p']}.",
    "figures outside their phrase": lambda f: (f"The data are {f['outcome']}, and the claim is {f['verdict']}. It rests "
                                              f"on {f['informative']} informative papers."),
}


def test_a_text_following_every_rule_is_stored(engine, stub):
    rid, f = exploratory(engine)
    stub.queue(reply(follows_all(f)))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and out.report == follows_all(f) and len(stub.requests) == 1


def test_the_diagnostic_answers_shape_is_refused_and_the_same_with_the_phrases_is_stored(engine, stub):
    """Owner, 2026-10-07: from the shape of the live diagnostic answer."""
    rid, f = exploratory(engine)
    old = diagnostic_shape(f)
    stub.queue(reply(old), reply(old))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "numbers_unmatched"  # full float precision is not what the facts give
    stub.queue(reply(follows_all(f)))  # the same run's Analyst stage again (attempt 2)
    out2 = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out2.failure is None and out2.report == follows_all(f)


@pytest.mark.parametrize("rule", sorted(BREAKS))
def test_a_text_breaking_each_new_rule_is_refused(engine, stub, rule):
    rid, f = exploratory(engine)
    bad = BREAKS[rule](f)
    assert bad != follows_all(f)
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, "wording_refused") and len(stub.requests) == 2


# --- failure facts (owner, 2026-10-07, after the live set): fixed facts only, never the answer's text ---------

def details_of(engine, stage_id):
    return one(engine, "SELECT output->'failure_details' FROM stage_result WHERE id = :s", s=stage_id)


def test_an_unparsable_answer_stores_its_form_facts_and_no_text(engine, stub):
    rid = below_minimums(engine)
    prose = "ZQPROSE an explanation written without the field markers"
    stub.queue(sp.reply(prose), sp.reply(prose))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "malformed"
    details = details_of(engine, out.stage_id)
    assert details == [{"attempt": n, "parse": {"output_headers_present": {"report": False}, "completed_marker": False,
                                                "header_count": 0, "answer_empty": False}} for n in (1, 2)]
    stored = json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))
    assert "ZQPROSE" not in stored


def test_a_refused_text_stores_the_names_of_the_rules_it_broke_and_no_text(engine, stub):
    rid = below_minimums(engine)
    bad = "ZQBAD The data are insufficient in the sources searched; grain refinement causes strength."
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "wording_refused"
    assert details_of(engine, out.stage_id) == [{"attempt": n, "problems": ["forbidden: causes"]} for n in (1, 2)]
    assert "ZQBAD" not in json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))
