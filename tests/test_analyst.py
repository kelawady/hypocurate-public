"""Step 8b, milestone 6: the Analyst and its text checks (owner, Q6, Q8, A3, B2). Every model call goes to the
local stub provider."""
from __future__ import annotations

import json
import re

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
# number check compares tokens exactly (was: rounding to the shown precision accepted). Fix round 1: the function
# that turned every float into its display string is deleted (owner); the same strings are written by the named
# formatting functions.
FACTS = {"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
                      "verdict_wording": "supported under the stated model, in the sources searched"},
         "analyses": [{"estimate": display.one_decimal(424.93), "std_error": display.one_decimal(64.41),
                       "n_records": 97, "detection": display.percent(0.0465),
                       "largest_paper_share": display.percent(0.387),
                       "p_value_phrase": display.p_phrase(1.287e-06),
                       "paper_figures_phrase": display.figures_phrase(20, 3.9358, 0.38673, 19)}]}


def test_the_named_formatting_functions_give_the_display_strings_and_phrases():
    a = FACTS["analyses"][0]
    assert (a["estimate"], a["std_error"], a["detection"], a["largest_paper_share"]) == ("424.9", "64.4", "4.7%", "38.7%")
    # Fix round 1 (owner's wording fix): no brackets, so the phrase reads the same inside parentheses.
    assert a["p_value_phrase"] == "an approximate, nominal, one-sided p ≈ 1.3e-6"
    assert a["paper_figures_phrase"] == ("20 informative groups, an effective number of groups of 3.94, a largest "
                                         "share of 38.7% and 19 degrees of freedom")  # 'groups' (owner, 2026-10-07)
    assert display.coefficient(424.93) == "424.9 MPa·µm^0.5" and not hasattr(display, "display")


@pytest.mark.parametrize("phrase", [
    "k = 424.9 ± 64.4", "97 records", "an approximate, nominal, one-sided p ≈ 1.3e-6", "4.7%",
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
    # Owner, 2026-10-07: the word-based p-value and figures rules were removed (placeholders guarantee them).
    (GOOD + " The p-value is 1.3e-6.", FACTS["decision"], []),
    (GOOD + " The value 1.3e-6 is small.", FACTS["decision"], []),
    (GOOD + " It rests on 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and "
            "19 degrees of freedom.", FACTS["decision"], []),
    (GOOD + " It rests on 20 informative papers.", FACTS["decision"], []),
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
    assert f"The pooled estimate is {display.coefficient(pooled['estimate'])} ± {display.coefficient(pooled['std_error'])}, " \
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
    # Owner, 2026-10-07: with a verdict the pooled phrases are required (was: the word-based p-value and figures rules).
    "p-value phrase missing": (FOLLOWS_ALL.replace(", with {pooled_p_phrase}", ""), "result_phrases_missing"),
    "figures phrase missing": (FOLLOWS_ALL.replace(" It rests on {pooled_figures_phrase}.", ""), "result_phrases_missing"),
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
        {"attempt": 1, "problems": [{"unknown_names": 1, "digits_outside_placeholders": 4, "required_missing": 0,
                                     "result_phrases_missing": 0}]},
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
    # Plain label wording and units (owner, 2026-10-07).
    assert out["sensitivity_not_agreeing"] == (
        "tension and compression (in the same direction as the pooled result, with a different test result); "
        "same alloy 1 at pct (in conflict with the pooled result (the opposite sign)); "
        "six batches as groups (not testable alone)")
    assert (out["sensitivity_smallest_estimate"], out["sensitivity_smallest_set"]) == ("-50.0 MPa·µm^0.5",
                                                                                      "same alloy 1 at pct")
    assert (out["sensitivity_largest_estimate"], out["sensitivity_largest_set"]) == ("410.0 MPa·µm^0.5", "no exclusions")
    assert out["without_largest_share_estimate"] == "390.0 MPa·µm^0.5"
    assert out["without_largest_share_label"] == "in agreement with the pooled result"
    assert out["without_largest_share_p_phrase"] == "an approximate, nominal, one-sided p ≈ 3.0e-5"  # fix round 1: no brackets


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



def test_the_words_p_value_and_paper_figures_are_allowed_now(engine, stub):
    """Owner, 2026-10-07: the two word-based rules are gone; the phrases carry the numbers."""
    rid, _ = exploratory(engine)
    text_ = FOLLOWS_ALL + " The p-value and the largest share above come from {pooled_groups} groups."
    stub.queue(reply(text_))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and len(stub.requests) == 1


def test_without_a_verdict_the_pooled_phrases_are_not_required(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply(BELOW))
    assert analyst.run_analyst(engine, rid, client_options=sp.client_options(stub)).failure is None


def test_no_fact_name_exposes_a_bare_p_value_or_an_individual_paper_figure(engine):
    """Owner, 2026-10-07: a p-value and the paper figures (informative papers, effective number, largest share, degrees
    of freedom) exist only inside the phrase names."""
    rid, pooled = exploratory(engine)
    names = names_of(engine, rid)
    phrase_names = {k for k in names if k.endswith(("_p_phrase", "_figures_phrase"))}
    assert {"pooled_p_phrase", "pooled_figures_phrase"} <= phrase_names
    # No name for a figure on its own (the 'without_largest_share_' names are the set's own results, and resid_df the
    # residual degrees of freedom of the minimums, not the test's).
    assert not [k for k in names if k not in phrase_names and ("informative" in k or "effective" in k or "p_value" in k
                                                               or k.endswith(("_share", "_t_df")))]
    c = pooled["counts"]
    bare = {display.p_value(pooled["p_value"]), display.two_decimals(c["effective_papers"]),
            display.percent(c["largest_paper_share"])}
    for k, v in names.items():
        if k not in phrase_names:
            assert not set(text_checks.tokens(v)) & bare, (k, v)
    # Fix round 1 (ChatGPT's finding 4): the earlier version of this test missed the informative-group count, which
    # the group minimum's count ('count_groups', with 'met_groups') exposed on its own. No name carries the count of
    # informative groups (the minimum's count) any more; the statement written by code shows the minimums.
    assert "count_groups" not in names and "met_groups" not in names
    informative = pooled["minimums"]["groups"]["count"]
    assert informative == c["n_groups_informative"]
    assert not [k for k, v in names.items() if k.startswith(("count_", "met_")) and k.endswith("groups")]


@pytest.mark.parametrize("kind", ["exploratory", "withheld", "narrowed", "fixed wordings"])
def test_no_remaining_rule_fires_on_text_the_facts_supply(engine, kind):
    """Owner's review question, 2026-10-07: every code-built value, of each kind of run, and every fixed wording the
    facts can carry, passes the remaining wording rules when written into a text that uses the outcome (and verdict)."""
    from hypocurate.pipeline import calibration, narrowing
    from hypocurate.pipeline import statistics as st
    from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME
    from test_planner_narrowing import TWO_BANDS, NARROWER, answer_of, cell, counts
    if kind == "exploratory":
        names = names_of(engine, exploratory(engine)[0])
    elif kind == "withheld":
        names = names_of(engine, below_minimums(engine))
    elif kind == "narrowed":
        d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=NARROWER),
                             counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
        names = analyst_names.narrowing_names(d)
    else:
        fixed = (list(calibration.FLAG_WORDING.values()) + list(st.EVIDENCE_LEVELS.values()) +
                 list(st.OUTCOME_WORDING.values()) + list(analyst_names.LABEL_WORDS.values()) +
                 [INFLUENCE_DISPLAY_NAME, st.BELOW_MINIMUMS_LABEL, st.EXPLORATORY_LABEL, st.PARTLY_SUFFICIENT_WORDING,
                  "missing evidence", "failed search", "insufficient groups", "evidence concentrated",
                  "uncertainty not estimable", "coefficient not fitted"])
        names = {"outcome_wording": "insufficient in the sources searched",
                 **{f"fixed_{LETTER}": w for LETTER, w in zip("abcdefghijklmnopqrstuvwxyz", [w for w in fixed if w])}}
    decision = {"outcome_wording": names["outcome_wording"], "verdict": "verdict_wording" in names,
                "verdict_wording": names.get("verdict_wording")}
    head = names["outcome_wording"] + (" " + names["verdict_wording"] if "verdict_wording" in names else "")
    for v in names.values():
        assert text_checks.wording_problems(f"{head}. {v}.", decision) == [], v


# --- owner's additions after reading a live explanation (2026-10-07): code-built sentences, units, plain names --

FW = "the method is over-confident on this data structure under the stated assumptions"


def cal(share, low, high, flag):
    return {"status": "computed", "null": {"share": share, "ci_low": low, "ci_high": high}, "flag_wording": flag}


@pytest.mark.parametrize("calibrations, ending", [
    ({"estimated": cal(0.082, 0.071, 0.095, FW), "fixed": cal(0.089, 0.077, 0.102, FW)}, f" Under both, {FW}."),
    ({"estimated": cal(0.082, 0.071, 0.095, FW), "fixed": cal(0.05, 0.04, 0.06, None)},
     f" Under noise levels estimated from the data, {FW}; under fixed illustrative noise levels, the share is consistent "
     "with the nominal level under the stated assumptions."),
])
def test_the_calibration_summary_covers_both_calibrations_and_their_flags(calibrations, ending):
    s = analyst_names.calibration_summary(calibrations, 0.05)
    assert s.startswith("In the simulation check, with noise levels estimated from the data, the test was significant "
                        "in 8.2% of simulations with no effect (7.1% to 9.5%, a 95% simulation interval covering "
                        "simulation uncertainty only); with fixed illustrative noise levels")
    assert "against a nominal level of 5.0%." in s and s.endswith(ending)


@pytest.mark.parametrize("estimate, note", [
    (424.9, "the estimate is positive, the direction the claim describes"),
    (-12.0, "the estimate is negative, opposite to the direction the claim describes"),
    (None, None),
])
def test_the_direction_note_is_built_from_the_sign_and_the_claims_direction(estimate, note):
    assert analyst_names.direction_note(estimate, "k > 0") == note


def test_the_plain_label_for_a_single_group_source():
    assert analyst_names.label_words({"label": "not_enough_data", "inference_reason": "insufficient_groups"}) == \
        "not testable alone (too few groups)"  # fix round 1 wording
    assert analyst_names.label_words({"label": "agrees"}) == "in agreement with the pooled result"


def test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level(engine):
    rid, pooled = exploratory(engine)
    names = names_of(engine, rid)
    assert names["scope_source"] == analyst_names.FIXED_PLAN_SENTENCE  # the test world's runs use a fixed plan
    assert names["model_sentence"] == analyst_names.MODEL_SENTENCE
    assert names["group_definition"] == analyst_names.GROUP_DEFINITION
    assert names["direction_note"] == analyst_names.direction_note(pooled["estimate"], "k > 0")
    assert names["nominal_level"] == "5.0%" and "alpha" not in names
    assert names["pooled_estimate"].endswith(" MPa·µm^0.5") and names["pooled_std_error"].endswith(" MPa·µm^0.5")
    assert names["estimated_calibration_name"] == "noise levels estimated from the data"
    assert names["fixed_calibration_name"] == "fixed illustrative noise levels"
    assert names["fixed_scatter"].endswith(" MPa") and names["fixed_shift"].endswith(" MPa")
    assert names["fixed_false_positive_interval"].endswith(", a 95% simulation interval covering simulation "
                                                           "uncertainty only")
    assert names["calibration_summary"].startswith("In the simulation check, ")


SENTENCES = ("The claim is that yield strength rises as grain size falls. The outcome is {outcome_wording}, and the "
             "claim is {verdict_wording}, with {pooled_p_phrase}, from {pooled_figures_phrase}. {calibration_summary} "
             "{scope_source} {model_sentence} The pooled estimate is {pooled_estimate}; {direction_note}. "
             "{group_definition}")


def test_a_text_using_the_code_built_sentences_is_accepted(engine, stub):
    rid, _ = exploratory(engine)
    stub.queue(reply(SENTENCES))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and out.report == text_checks.render(SENTENCES, names_of(engine, rid))


def test_the_failure_facts_of_a_corrected_attempt_are_stored(engine, stub):
    """Owner, 2026-10-07: also when a later attempt is accepted."""
    rid = below_minimums(engine)
    stub.queue(reply("ZQDIG The outcome is {outcome_wording}; 12 records."), reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["attempts"] == ["digit_outside_placeholder", "ok"]
    assert stored["failure_details"] == [{"attempt": 1, "problems": [{"unknown_names": 0, "digits_outside_placeholders": 2,
                                                                      "required_missing": 0,
                                                                      "result_phrases_missing": 0}]}]
    assert "ZQDIG" not in json.dumps(stored)


# --- finding 5 (fix round 1): answer shapes ---------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["", "{}", "[]", "null", "{outcome_wording", "{{outcome_wording}}", "{Outcome_wording}",
                                 "{a.b}", "{outcome_wording} {}", "{outcome_wording} {[]}", '{"report": []}'])
def test_an_analyst_text_of_any_shape_gets_a_code_never_an_exception(raw):
    """The Analyst's answer is text; whatever its shape, the check returns a failure code or accepts it."""
    from hypocurate.pipeline.agents import analyst
    check = analyst.make_check({"analyst_facts": {"kind": "analysis", "names": {
        "outcome_wording": "insufficient in the sources searched"}}})
    assert check({"report": raw}) in (None, "empty", "malformed", "unknown_name", "digit_outside_placeholder",
                                      "wording_refused", "result_phrases_missing", "numbers_unmatched")


# --- the owner's wording fixes from live run A on Render (2026-10-10) -------------------------------------------

from hypocurate.pipeline import analyst_names as an  # noqa: E402
from hypocurate.pipeline import statement  # noqa: E402

RUN_A_FRAME = "Because of the {direction_sentence}, the result points the way the claim describes."
PLACEMENT_REASON = "{direction_sentence} is a whole sentence: place it as a sentence of its own"


@pytest.mark.parametrize("estimate", [424.9, -12.0, 0.0])
def test_the_direction_sentence_reads_correctly_for_every_value_it_can_take(estimate):
    s = an.direction_sentence(estimate, "k > 0")
    assert s[0].isupper() and s.endswith(".") and s.count(".") == 1
    assert s == statement._cap(an.direction_note(estimate, "k > 0")) + "."  # the statement's own line, unchanged
    names = {"direction_sentence": s, "outcome_wording": "sufficient in the sources searched"}
    for template in ("{direction_sentence} The outcome is {outcome_wording}.",
                     "The outcome is {outcome_wording}. {direction_sentence}",
                     "The outcome is {outcome_wording}.\n{direction_sentence}\n"):
        assert text_checks.placement_problems(template, names) == []
        rendered = text_checks.render(template, names)
        assert "the the" not in rendered and ".." not in rendered and s in rendered
    assert text_checks.placement_problems(RUN_A_FRAME, names) == [PLACEMENT_REASON]


@pytest.mark.parametrize("estimate, alternative", [(None, "k > 0"), (424.9, None), (424.9, "k < 0")])
def test_there_is_no_direction_sentence_without_an_estimate_or_the_claims_direction(estimate, alternative):
    assert an.direction_sentence(estimate, alternative) is None


@pytest.mark.parametrize("template", [
    "{model_sentence} The outcome is {outcome_wording}.",
    "The outcome is {outcome_wording}! {model_sentence}",
    "The outcome is {outcome_wording}? {model_sentence}",
    "The outcome is {outcome_wording}.\n- {model_sentence}\n* {group_definition}",
    "{model_sentence} {group_definition}",
    "The outcome is {outcome_wording}:\n\n{model_sentence}",
])
def test_a_whole_sentence_placed_as_its_own_sentence_is_accepted(template):
    names = {"model_sentence": an.MODEL_SENTENCE, "group_definition": an.GROUP_DEFINITION,
             "outcome_wording": "sufficient in the sources searched"}
    assert text_checks.placement_problems(template, names) == []


@pytest.mark.parametrize("template, name", [
    ("As {model_sentence} The outcome is {outcome_wording}.", "model_sentence"),
    ("The outcome is {outcome_wording} ({model_sentence})", "model_sentence"),
    ("The outcome is {outcome_wording}: {group_definition}", "group_definition"),
    ("{model_sentence}, so the outcome is {outcome_wording}.", "model_sentence"),
    ("{group_definition} {outcome_wording} is the outcome.", "group_definition"),
    ("The outcome is {outcome_wording}, and {group_definition}", "group_definition"),
])
def test_a_whole_sentence_inside_another_sentence_is_refused_with_its_name(template, name):
    names = {"model_sentence": an.MODEL_SENTENCE, "group_definition": an.GROUP_DEFINITION,
             "outcome_wording": "sufficient in the sources searched"}
    assert text_checks.placement_problems(template, names) == [
        "{" + name + "} is a whole sentence: place it as a sentence of its own"]


MET = {"records": {"count": 97, "minimum": 30, "met": True}, "alloys": {"count": 22, "minimum": 5, "met": True},
       "groups": {"count": 20, "minimum": 10, "met": True}, "resid_df": {"count": 74, "minimum": 10, "met": True}}
BELOW_MINS = {"records": {"count": 6, "minimum": 30, "met": False}, "alloys": {"count": 3, "minimum": 5, "met": False},
              "groups": {"count": 3, "minimum": 10, "met": False}, "resid_df": {"count": 2, "minimum": 10, "met": False}}
PLAN_MINIMUMS = {"records": 30, "alloys": 5, "groups": 10, "resid_df": 10}


@pytest.mark.parametrize("minimums, option, expected", [
    (MET, "fixed_minimum", "The minimums for a test: at least 30 records (met); at least 5 alloys with at least 2 grain "
                           "sizes (met); at least 10 informative groups (met); at least 10 residual degrees of freedom "
                           "(met)."),
    (BELOW_MINS, "fixed_minimum", "The minimums for a test: at least 30 records (not met); at least 5 alloys with at "
                                  "least 2 grain sizes (not met); at least 10 informative groups (not met); at least 10 "
                                  "residual degrees of freedom (not met)."),
    ({**MET, "records": {"count": 6, "minimum": 30, "met": False}}, "use_available",
     "The minimums for a test: at least 30 records (not met; waived: use what is available); at least 5 alloys with at "
     "least 2 grain sizes (met); at least 10 informative groups (met); at least 10 residual degrees of freedom (met)."),
    (None, "fixed_minimum", "The minimums for a test: at least 30 records (not assessed: no dataset was frozen); at "
                            "least 5 alloys with at least 2 grain sizes (not assessed: no dataset was frozen); at least "
                            "10 informative groups (not assessed: no dataset was frozen); at least 10 residual degrees "
                            "of freedom (not assessed: no dataset was frozen)."),
])
def test_the_minimums_sentence_gives_every_minimum_its_status(minimums, option, expected):
    s = an.minimums_sentence(PLAN_MINIMUMS, minimums, option)
    assert s == expected
    for words in statement.MINIMUM_WORDS.values():  # every minimum, each with its status
        assert re.search(rf"at least \d+ {re.escape(words)} \((met|not met[^)]*|not assessed[^)]*)\)", s), words
    assert " 20 " not in s and " 3 " not in s  # never the informative-group count


@pytest.mark.parametrize("value", [
    lambda: an.MODEL_SENTENCE, lambda: an.GROUP_DEFINITION, lambda: an.FIXED_PLAN_SENTENCE,
    lambda: an.NARROWER_PLAN_SENTENCE,
    *(lambda e=e: an.direction_sentence(e, "k > 0") for e in (424.9, -12.0, 0.0)),
    *(lambda m=m, o=o: an.minimums_sentence(PLAN_MINIMUMS, m, o)
      for m, o in ((MET, "fixed_minimum"), (BELOW_MINS, "use_available"), (None, "fixed_minimum"))),
])
def test_every_value_of_a_whole_sentence_name_is_a_complete_sentence(value):
    value = value()
    assert value[0].isupper() and value.rstrip().endswith(".")


def test_below_the_minimums_the_facts_give_every_minimum_with_its_status_and_no_bare_minimum(engine):
    names = names_of(engine, below_minimums(engine))
    assert "minimums_sentence" in names and not [k for k in names if k.startswith("minimum_")]
    assert "at least 10 informative groups (not met)" in names["minimums_sentence"]
    assert "direction_note" not in names


def test_the_facts_give_the_direction_as_a_whole_sentence(engine):
    rid, pooled = exploratory(engine)
    names = names_of(engine, rid)
    assert names["direction_sentence"] == an.direction_sentence(pooled["estimate"], "k > 0")
    assert "direction_note" not in names
    assert set(text_checks.SENTENCE_NAMES) >= {"direction_sentence", "minimums_sentence", "model_sentence",
                                               "group_definition", "calibration_summary", "scope_source"}


def test_every_placeholder_named_in_the_instruction_is_a_fact_the_analyst_is_given(engine):
    rid, _ = exploratory(engine)
    names = set(names_of(engine, rid))
    named = set(re.findall(r"\{([a-z_]+)\}", ANALYST_INSTRUCTION)) - {"name"}
    assert named <= names, named - names


def test_run_as_garbled_frame_is_corrected_naming_the_sentence_rule_and_the_reason_is_stored(engine, stub):
    rid, _ = exploratory(engine)
    garbled = FOLLOWS_ALL + " " + RUN_A_FRAME
    stub.queue(reply(garbled), reply(FOLLOWS_ALL + " {direction_sentence}"))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["attempts"] == ["wording_refused", "ok"]
    assert stored["attempt_reasons"] == [PLACEMENT_REASON, None]
    assert PLACEMENT_REASON.replace('"', '\\"') in stub.requests[1]["raw"].decode()


@pytest.mark.parametrize("template, code, reason", [
    ("The claim is {verdict_wording}, with {pooled_p_phrase} from {pooled_figures_phrase}.", "wording_refused",
     "the text does not use {outcome_wording}"),
    ("The outcome is {outcome_wording}; the claim is {verdict_wording}.", "result_phrases_missing",
     "the text does not use {pooled_p_phrase}, {pooled_figures_phrase}"),
    (FOLLOWS_ALL + " There were 12 records.", "digit_outside_placeholder", "digits outside placeholders: 2"),
    (FOLLOWS_ALL + " {zq_unknown_name}", "unknown_name", "placeholders that name no fact given: 1"),
    (FOLLOWS_ALL + " This proves it.", "wording_refused", "wording rule: forbidden: proves"),
])
def test_each_analyst_refusal_has_a_specific_reason_in_codes_words(engine, stub, template, code, reason):
    rid, _ = exploratory(engine)
    stub.queue(reply(template), reply(template))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["attempts"] == [code, code] and stored["attempt_reasons"] == [reason, reason]
    assert "zq_unknown" not in json.dumps(stored) and "12 records" not in json.dumps(stored)
