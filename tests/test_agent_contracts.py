"""The contract between what each agent is told and what code's check of its answer accepts and requires (owner,
2026-10-10, after live run B on Render failed with 'invalid_plan': the Planner's output description named five keys
while the check required six). For every agent (Planner, Analyst, Critic, Curator), the keys and rules named in the
request must equal those the check accepts and requires. No database and no model call: the requests are rendered
offline with the role's own signature."""
from __future__ import annotations

import json
import re

import pytest

from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX, CURATION_TARGETS
from hypocurate.pipeline.agents import analyst, critic, curator, libraries, planner, text_checks
from hypocurate.pipeline.agents.settings import ANALYST_INSTRUCTION, CRITIC_INSTRUCTION, CURATOR_INSTRUCTION, \
    PLANNER_INSTRUCTION

MPEA_CLASS = "multi-principal-element (high-entropy) alloy"


def rendered(signature, inputs: dict) -> str:
    """The text of the request DSPy's ChatAdapter builds for the role (system and user messages)."""
    _, dspy = libraries.load()
    messages = dspy.ChatAdapter(use_json_adapter_fallback=False).format(signature, demos=[], inputs=inputs)
    return "\n".join(m["content"] for m in messages)


def listed(phrase: str) -> set[str]:
    """The items of a list written 'a, b and c'."""
    return {x.strip() for x in re.split(r",\s*|\s+and\s+", phrase) if x.strip()}


# --- the Planner -----------------------------------------------------------------------------------------------

def planner_named_keys() -> set[str]:
    m = re.search(r"exactly the keys (.+?), in the form", planner.OUTPUT_DESCRIPTION)
    assert m, "the Planner's output description names its keys"
    return listed(m.group(1))


def test_the_planners_output_description_names_exactly_the_keys_the_check_requires():
    assert planner_named_keys() == set(planner.KEYS)


def test_the_planners_answer_form_names_the_keys_and_scope_parts_the_check_requires():
    form = planner.allowed_values([{"kind": "alloy_class", "value": MPEA_CLASS}])["form"]
    assert set(form) == set(planner.KEYS)
    assert set(form["claim_scope"]) == planner.SCOPE_KEYS and set(form["stated"]) == planner.SCOPE_KEYS


def test_every_key_the_planners_check_requires_is_named_in_its_request():
    text_ = rendered(planner.signature(PLANNER_INSTRUCTION),
                     {k: "x" for k in ("claim", "domain", "sources", "counts", "allowed", "note")})
    for key in planner.KEYS:
        assert re.search(rf"\b{key}\b", text_), key


def test_an_answer_with_exactly_the_keys_the_planner_is_told_is_accepted():
    """An answer that follows the output description to the letter (only the keys it names) passes the check."""
    full = {"domain_matches": True,
            "claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                            "temperature_band": [{"band": "room temperature"}]},
            "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
            "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}],
            "narrower": None}
    told = {k: v for k, v in full.items() if k in planner_named_keys()}
    check = planner.make_check(1, "fixed_minimum", {MPEA_CLASS})
    assert check({"plan": json.dumps(told)}) is None


# --- the Critic ------------------------------------------------------------------------------------------------

def critic_named_entry_keys() -> set[str]:
    return set(re.findall(r'"(\w+)":', critic.OUTPUT_DESCRIPTION))


def test_the_critics_output_description_names_exactly_the_entry_keys_its_check_accepts():
    named = critic_named_entry_keys()
    batch = [{"id": 7}]
    entry = {"class": sorted(CRITIC_CLASSES)[0], "reason": "the records name different specimens"}
    assert set(entry) == named
    assert critic.classify({"7": {k: entry[k] for k in named}}, batch).accepted  # every named key is accepted
    assert critic.classify({"7": {**entry, "extra": "x"}}, batch).refused == {"7": "malformed_entry"}
    for key in named - {"reason"}:  # the reason is optional; every other named key is required
        assert critic.classify({"7": {k: v for k, v in entry.items() if k != key}}, batch).refused


def test_the_critics_limits_and_classes_in_the_request_are_the_checks():
    m = re.search(r"at most (\d+) characters", critic.OUTPUT_DESCRIPTION)
    assert m and int(m.group(1)) == CRITIC_REASON_MAX
    inputs = critic.render_inputs({"sources_meta": [], "record_metadata": [], "flags_kind": []}, [])
    assert set(json.loads(inputs["classes"])) == set(CRITIC_CLASSES)
    assert "class" in CRITIC_INSTRUCTION or "classif" in CRITIC_INSTRUCTION


# --- the Curator -----------------------------------------------------------------------------------------------

def test_the_curators_output_description_names_exactly_the_entry_keys_its_check_requires():
    named = set(re.findall(r'"(\w+)":', curator.OUTPUT_DESCRIPTION))
    assert named == {"value", "quote"}
    assert '"not stated"' in curator.OUTPUT_DESCRIPTION
    # The check (`_entry`) requires exactly these keys: one missing or one more is refused as malformed.
    for entry in ({"value": "tension"}, {"quote": "q"}, {"value": "tension", "quote": "q", "extra": 1}):
        assert curator._entry("test_type", entry, {}).refusal_code == "malformed_entry"
    assert curator._entry("test_type", "not stated", {}).status == "not_stated"


def test_the_curators_request_names_exactly_the_targets_its_check_reads():
    inputs = curator.render_inputs({"source_documentation": {"documents": {}},
                                    "curation_targets": dict(CURATION_TARGETS)})
    assert set(json.loads(inputs["targets"])) == set(CURATION_TARGETS)
    proposals, others = curator.proposals_from(json.dumps({}), {})
    assert {p.field for p in proposals} == set(CURATION_TARGETS) and others == []
    assert "not stated" in CURATOR_INSTRUCTION


# --- the Analyst -----------------------------------------------------------------------------------------------

def test_every_name_the_analysts_check_requires_is_named_in_its_instruction():
    for name in (*text_checks.REQUIRED, "verdict_wording", *text_checks.REQUIRED_WITH_VERDICT):
        assert "{" + name + "}" in ANALYST_INSTRUCTION, name


def test_the_whole_sentences_the_analyst_is_told_to_place_alone_are_those_its_check_enforces():
    """The owner's wording fix (live run A): a code-built sentence must stand as a sentence of its own. The instruction
    names exactly the sentences the check holds to that rule."""
    sentence = next(s for s in re.split(r"(?<=\.)\s+", ANALYST_INSTRUCTION) if "sentence of its own" in s)
    assert set(re.findall(r"\{([a-z_]+)\}", sentence)) == set(text_checks.SENTENCE_NAMES)


def test_the_analysts_output_description_and_instruction_agree_on_placeholders():
    assert "{name}" in analyst.OUTPUT_DESCRIPTION and "No digits" in analyst.OUTPUT_DESCRIPTION
    assert "Write no digits" in ANALYST_INSTRUCTION
