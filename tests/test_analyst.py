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


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def names_of(engine, rid):
    """The named facts the Analyst is given for the run (through its access object)."""
    from hypocurate.access import bind, role_input
    setting = one(engine, "SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = 'analyst'",
                  r=rid)
    return role_input(bind(engine, rid, setting))["analyst_facts"]["names"]


def below_minimums(engine):
    rid = run_on(engine, small_rows(3, papers=3, base=7311.0), agents=("analyst",))
    analysis.run_statistics(engine, rid)
    return rid


# Step 8b (owner, 2026-10-07): the Analyst writes no digits; it refers to facts by name, and code renders the text.
BELOW = ("The outcome is {outcome_wording}: the pooled set has {pooled_records} records, below the minimum of "
         "{minimum_records}, so no test was run and no estimate is shown.")


def test_below_the_minimums_the_analysts_request_holds_no_outcome_value(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    names = names_of(engine, rid)
    expected = text_checks.render(BELOW, names)
    assert out.failure is None and out.report == expected
    assert expected.startswith("The outcome is insufficient in the sources searched: the pooled set has 6 records")
    raw = stub.requests[0]["raw"].decode()
    with engine.connect() as conn:
        values = [float(v) for v in conn.execute(text("SELECT harmonized->'yield_strength'->>'value' FROM record "
                                                      "WHERE extraction_run_id = :r"), dict(r=rid)).scalars()]
    for v in values:
        assert repr(v) not in raw and f"{v:g}" not in raw, v
    sent = json.loads(raw)
    assert "tools" not in sent and ANALYST_INSTRUCTION in json.dumps(sent, ensure_ascii=False)
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["report"] == expected and stored["template"] == BELOW


def test_a_run_below_the_minimums_offers_no_estimate_names(engine):
    names = names_of(engine, below_minimums(engine))
    assert not [k for k in names if k.endswith(("_estimate", "_std_error", "_p_phrase", "_figures_phrase"))]
    assert "pooled_records" in names and "minimum_records" in names


@pytest.mark.parametrize("bad, code", [
    ("The outcome is {outcome_wording}: 31 records were found.", "digit_outside_placeholder"),
    ("The outcome is {outcome_wording}: the estimate is {pooled_estimate}.", "unknown_name"),  # withheld: no such name
    ("The outcome is {outcome_wording}, with {pooled_recordz} records.", "unknown_name"),
    ("The outcome is {outcome_wording}: grain sizes do not exist.", "wording_refused"),
    ("The outcome is {outcome_wording}, but the claim is supported.", "wording_refused"),
    ("The data were insufficient in the sources searched.", "wording_refused"),  # {outcome_wording} not used
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
    stub.queue(reply("The outcome is {outcome_wording}: 31 records."), reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.report == text_checks.render(BELOW, names_of(engine, rid)) and len(stub.requests) == 2


def test_the_analyst_changes_no_stored_decision(engine, stub):
    rid = below_minimums(engine)
    before = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid)
    stub.queue(reply(BELOW))
    analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid) == before
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"


# --- above the minimums: the phrases, the owner's rules and the shape of the live diagnostic answer -------------

def exploratory(engine):
    """A run above the validity checks under 'use what is available': its facts hold the pooled estimate, its
    p-value phrase and its paper figures phrase."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    return rid, out["analyses"][0]


FOLLOWS_ALL = ("The data are {outcome_wording}, and the claim is {verdict_wording}. The pooled estimate is "
               "{pooled_estimate} ± {pooled_std_error}, with {pooled_p_phrase}. It rests on {pooled_figures_phrase}.")


def test_a_correct_text_is_accepted_and_rendered_with_the_exact_strings(engine, stub):
    rid, pooled = exploratory(engine)
    stub.queue(reply(FOLLOWS_ALL))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and len(stub.requests) == 1
    c = pooled["counts"]
    assert f"The pooled estimate is {display.one_decimal(pooled['estimate'])} ± {display.one_decimal(pooled['std_error'])}, " \
           f"with {display.p_phrase(pooled['p_value'])}. It rests on " \
           f"{display.figures_phrase(c['n_groups_informative'], c['effective_papers'], c['largest_paper_share'], pooled['df'])}." \
           in out.report
    assert "{" not in out.report and "}" not in out.report


def diagnostic_shape(pooled):
    """The shape of the live diagnostic answer (2026-10-07): numbers written out at full precision."""
    c = pooled["counts"]
    return ("The data are {outcome_wording}, and the claim is {verdict_wording}. The estimated coefficient is "
            f"{pooled['estimate']!r}. The p-value is {pooled['p_value']!r}, an approximate, nominal, one-sided "
            f"cluster-robust p-value under the locked method. The support comes from {c['n_groups_informative']} "
            "informative papers.")


def test_the_diagnostic_answers_shape_is_refused_and_the_same_with_placeholders_is_stored(engine, stub):
    rid, pooled = exploratory(engine)
    old = diagnostic_shape(pooled)
    stub.queue(reply(old), reply(FOLLOWS_ALL))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert json.loads(stub.requests[1]["raw"])  # corrected once
    assert "digit_outside_placeholder" in stub.requests[1]["raw"].decode()
    assert out.failure is None and out.report == text_checks.render(FOLLOWS_ALL, names_of(engine, rid))


BREAKS = {
    "causes": (FOLLOWS_ALL + " Grain refinement causes the strengthening.", "wording_refused"),
    "caused by": (FOLLOWS_ALL + " The rise is caused by smaller grains.", "wording_refused"),
    "causal": (FOLLOWS_ALL + " The link is causal.", "wording_refused"),
    "confirms the claim": (FOLLOWS_ALL + " This confirms the claim.", "wording_refused"),
    "confirms the hypothesis": (FOLLOWS_ALL + " This confirms the hypothesis.", "wording_refused"),
    "effective number as independent": (FOLLOWS_ALL + " The effective number counts independent papers.",
                                        "wording_refused"),
    "p-value outside its phrase": (FOLLOWS_ALL + " The p-value is small.", "wording_refused"),
    "figures outside their phrase": (FOLLOWS_ALL + " It rests on {pooled_groups} informative papers.",
                                     "wording_refused"),
    "verdict not used": ("The data are {outcome_wording}.", "wording_refused"),
    "a digit": (FOLLOWS_ALL + " It used 97 records.", "digit_outside_placeholder"),
    "an unknown name": (FOLLOWS_ALL.replace("{pooled_estimate}", "{pooled_estimat}"), "unknown_name"),
}


@pytest.mark.parametrize("rule", sorted(BREAKS))
def test_a_text_breaking_each_rule_is_refused(engine, stub, rule):
    rid, _ = exploratory(engine)
    bad, code = BREAKS[rule]
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, code) and len(stub.requests) == 2


# --- failure facts: counts or rule names only, never the answer's text ----------------------------------------

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
    assert "ZQPROSE" not in json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))


def test_a_refused_text_stores_counts_or_rule_names_and_no_text(engine, stub):
    rid = below_minimums(engine)
    digits = "ZQDIG The outcome is {outcome_wording}; 12 and 34 records, {nosuch}."
    bad = "ZQBAD The outcome is {outcome_wording}; grain refinement causes strength."
    stub.queue(reply(digits), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "wording_refused"
    assert details_of(engine, out.stage_id) == [
        {"attempt": 1, "problems": [{"unknown_names": 1, "digits_outside_placeholders": 4, "required_missing": 0}]},
        {"attempt": 2, "problems": ["forbidden: causes"]}]
    stored = json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))
    assert "ZQDIG" not in stored and "ZQBAD" not in stored


# --- the named facts built by code (owner, 2026-10-07) ----------------------------------------------------------

from hypocurate.pipeline import analyst_names


def entry(key, estimate, p, scope="sensitivity", valid=True):
    return {"scope": scope, "set": key, "source": None, "estimate": estimate, "std_error": 10.0 if p else None,
            "p_value": p, "df": 9 if p else None, "checks": {"coefficient_fitted": estimate is not None,
                                                            "inference_valid": valid and p is not None},
            "counts": {"n_records": 30, "n_alloys": 5, "n_groups": 10, "n_groups_informative": 10,
                       "effective_papers": 6.5, "largest_paper_share": 0.2}, "withheld": False}


POOLED = entry("primary", 400.0, 1e-6, scope="pooled")


def test_the_sensitivity_sets_are_labelled_with_the_per_source_function():
    sets = [entry("no_exclusions", 410.0, 2e-6),                      # agrees
            entry("tension_and_compression", 120.0, 0.2),             # same direction, different decision
            entry("same_alloy_1_at_pct", -50.0, 0.9),                 # conflicts
            entry("six_batches_as_groups", 380.0, None, valid=False),  # not enough data
            entry("without_most_influential_paper", 390.0, 3e-5)]     # agrees
    out = analyst_names.sensitivity_summary([POOLED] + sets, POOLED, 0.05, withheld=False)
    assert (out["sensitivity_sets"], out["sensitivity_agrees"], out["sensitivity_same_direction_different_decision"],
            out["sensitivity_conflicts"], out["sensitivity_not_enough_data"]) == ("5", "2", "1", "1", "1")
    assert out["sensitivity_not_agreeing"] == ("tension and compression (same direction, different decision); "
                                               "same alloy 1 at pct (conflicts); six batches as groups (not enough data)")
    assert (out["sensitivity_smallest_estimate"], out["sensitivity_smallest_set"]) == ("-50.0", "same alloy 1 at pct")
    assert (out["sensitivity_largest_estimate"], out["sensitivity_largest_set"]) == ("410.0", "no exclusions")
    assert out["without_largest_share_estimate"] == "390.0" and out["without_largest_share_label"] == "agrees"
    assert out["without_largest_share_p_phrase"] == "p ≈ 3.0e-5 (approximate, nominal, one-sided)"


def test_a_withheld_result_gives_no_estimate_name_even_if_numbers_were_stored():
    """Behind the statistics (which store no number for a withheld result) the name builder refuses them too."""
    stats = {"decision": {"outcome_wording": "insufficient in the sources searched", "evidence_level": 3,
                          "evidence_level_wording": "below the minimums under the fixed option"},
             "withheld": True, "analyses": [POOLED, entry("per", 410.0, 2e-6, scope="per_source") | {"source": "mpea"},
                                            entry("no_exclusions", 410.0, 2e-6)]}
    plan = {"alpha": 0.05, "sufficiency_option": "fixed_minimum", "minimums": {"records": 30}}
    names = analyst_names.analysis_names(stats, {}, plan, {})
    assert not [k for k in names if k.endswith(("_estimate", "_std_error", "_p_phrase", "_figures_phrase"))]
    assert "pooled_records" in names and "mpea_records" in names
