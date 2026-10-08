"""The Planner (step 8b; PRD 3 step 3, 5.1, 5.4; owner's answers Q5, A11; register 'planner_answer').

The Planner reads the claim, the domain, the chosen sources' descriptions, the approved tag values and the
record counts (its access list at 'before_lock'; never an outcome value). It answers one JSON object:

    {"domain_matches": true | false,
     "claim_scope": {"alloy_class": [...], "phase_class": [...], "test_type": [...],
                     "temperature_band": [{"band": "room temperature"} | {"band": "elevated" | "cryogenic",
                                                                          "min": <°C>, "max": <°C>}, ...]},
     "stated": {"alloy_class": true | false, "phase_class": ..., "test_type": ..., "temperature_band": ...},
     "outcome": "yield_strength",
     "exclusion_rules": [{"rule": <menu>, "min": <n>, "max": <n>, "values": [...]}, ...],
     "narrower": null | {"phase_class": [...], "test_type": [...], "temperature_band": [...]}}

Every value comes from a fixed list; there is no free text and no other key. **Code decides** (CLAUDE.md,
rule 1): `check` refuses an answer whose shape, values or plan are not valid (`invalid_plan`, corrected once
by the common interface); `build_plan` makes the plan from the profile's defaults and only these
parameters: the model, the rules, the eligibility rules, the calibration and the data-sufficiency option
never come from the model (the option is the query's, A2). The plan's scope is the claim's scope; a claim
that is not one plan (more than one alloy class, temperature band or test type, A11) gets no plan here,
and the narrowing decision (`pipeline.narrowing`) decides what happens. Code builds any narrower scope from its
own counts (owner, 2026-10-07, after live run C); a narrower scope the Planner gives anyway is checked for its
shape, stored, and never used.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from hypocurate.access.allowlist import ALLOY_CLASSES, EXCLUSION_RULES
from hypocurate.access.vocabulary import PHASE_CLASSES, TEST_TYPES
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import profile as p
from hypocurate.pipeline import reading
from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.eligibility import SUPPORTED_OUTCOMES

KEYS = {"domain_matches", "claim_scope", "stated", "outcome", "exclusion_rules", "narrower"}
SCOPE_KEYS = {"alloy_class", "phase_class", "test_type", "temperature_band"}
NARROWER_KEYS = {"phase_class", "test_type", "temperature_band"}  # alloy class is not countable (Q5)
BANDS = tuple(p.SUPPORTED_BANDS)
CATEGORY_RULE_VALUES = {"phase": sorted(PHASE_CLASSES), "test_type": sorted(TEST_TYPES)}
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)

OUTPUT_DESCRIPTION = ("One JSON object with exactly the keys domain_matches, claim_scope, outcome, exclusion_rules "
                      "and narrower, in the form and with the values given in 'allowed'. Nothing else.")


def signature(instruction: str):
    _, dspy = libraries.load()

    class PlannerSignature(dspy.Signature):
        claim: str = dspy.InputField(desc="The claim in words, with its query number.")
        domain: str = dspy.InputField(desc="The query's confirmed domain.")
        sources: str = dspy.InputField(desc="The chosen sources' descriptions, as JSON.")
        counts: str = dspy.InputField(desc="Counts of each source's records by field status and category value.")
        allowed: str = dspy.InputField(desc="The answer's form, the allowed values and the defaults, as JSON.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        plan: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)

    return PlannerSignature.with_instructions(instruction)


# The profile's default of each scope part: what the Planner must give for a part it marks as not stated by the
# claim (owner's decision B, fix round 1; register 'question_as_tested'). One named place: also the defaults the
# Planner is shown.
DEFAULT_SCOPE: Mapping[str, list] = MappingProxyType({
    "alloy_class": list(p.ALLOY_CLASSES), "phase_class": list(p.PHASE_CLASSES),
    "test_type": list(p.PERMITTED_TEST_TYPES), "temperature_band": [{"band": plans.ROOM_TEMPERATURE}]})


def allowed_values(tag_values: list[Mapping]) -> dict:
    """The answer's form and allowed values, built by code from the vocabularies, the approved tag values
    and the profile's defaults (no run data)."""
    approved = sorted(t["value"] for t in tag_values if t.get("kind") == "alloy_class")
    return {
        "form": {"domain_matches": "true or false",
                 "claim_scope": {"alloy_class": "list", "phase_class": "list", "test_type": "list",
                                 "temperature_band": "list of {band} or {band, min, max} in °C"},
                 "stated": {"alloy_class": "true if the claim states it, false if you used the default",
                            "phase_class": "true or false", "test_type": "true or false",
                            "temperature_band": "true or false"},
                 "outcome": "one value", "exclusion_rules": "list of {rule, min?, max?, values?}",
                 "narrower": "null (code decides any narrower scope from its own counts)"},
        "alloy_class": [a for a in approved if a in ALLOY_CLASSES],
        "phase_class": sorted(PHASE_CLASSES - {"other"}),
        "test_type": sorted(TEST_TYPES),
        "temperature_band": list(BANDS),
        "room_temperature_c": list(p.ROOM_TEMPERATURE_C),
        "outcome": list(SUPPORTED_OUTCOMES),
        "exclusion_rule_menu": {"grain_size_range": "min and/or max in µm", "temperature_range": "min and/or max in °C",
                                "phase": CATEGORY_RULE_VALUES["phase"], "test_type": CATEGORY_RULE_VALUES["test_type"]},
        "defaults": {**{k: list(v) for k, v in DEFAULT_SCOPE.items()},
                     "outcome": p.OUTCOME[0],
                     "exclusion_rules": [{"rule": "grain_size_range", "min": float(p.GRAIN_SIZE_FLOOR_UM)}]},
    }


def render_inputs(planner_input: Mapping[str, Any]) -> dict[str, str]:
    """The Planner's request inputs, built only from its complete access-layer input and code's lists."""
    c = planner_input["claim"]
    return {"claim": json.dumps(c, sort_keys=True, ensure_ascii=False),
            "domain": json.dumps(planner_input["domain"], sort_keys=True, ensure_ascii=False),
            "sources": json.dumps(planner_input["sources_meta"], sort_keys=True, ensure_ascii=False),
            "counts": json.dumps(planner_input["record_counts"], sort_keys=True, ensure_ascii=False),
            "allowed": json.dumps(allowed_values(planner_input["tag_values"]), sort_keys=True, ensure_ascii=False)}


def parse(text: str) -> dict | None:
    body = text.strip()
    fenced = _FENCE.match(body)
    if fenced:
        body = fenced.group(1)
    try:
        value = json.loads(body)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


# --- The answer's shape ------------------------------------------------------------------------------

class AnswerInvalid(ValueError):
    pass


def _number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _word(v, allowed) -> bool:
    """A vocabulary value: text first, then membership (a list or object never reaches a membership test;
    fix round, finding 5)."""
    return isinstance(v, str) and v in allowed


def _values(v, allowed, what) -> list:
    if not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v) or len(set(v)) != len(v) \
            or not all(x in allowed for x in v):
        raise AnswerInvalid(f"{what}: a non-empty list of distinct allowed values")
    return list(v)


def _bands(v) -> list[dict]:
    if not isinstance(v, list) or not v:
        raise AnswerInvalid("temperature_band: a non-empty list")
    out, seen = [], set()
    for b in v:
        if not isinstance(b, dict) or not _word(b.get("band"), BANDS):
            raise AnswerInvalid("temperature_band: each {band} from the list")
        if b["band"] == plans.ROOM_TEMPERATURE:
            if set(b) != {"band"}:
                raise AnswerInvalid("room temperature takes no range")
            band = {"band": b["band"]}
        else:
            if set(b) != {"band", "min", "max"} or not (_number(b["min"]) and _number(b["max"])) or b["min"] > b["max"]:
                raise AnswerInvalid("an elevated or cryogenic band names its range, min not above max")
            band = {"band": b["band"], "min": float(b["min"]), "max": float(b["max"])}
        if band["band"] in seen:
            raise AnswerInvalid("each band once")
        seen.add(band["band"])
        out.append(band)
    return out


def _exclusions(v) -> list[dict]:
    if not isinstance(v, list):
        raise AnswerInvalid("exclusion_rules: a list")
    out = []
    for e in v:
        if not isinstance(e, dict) or not _word(e.get("rule"), EXCLUSION_RULES):
            raise AnswerInvalid("an exclusion rule comes from the menu")
        if e["rule"] in ("grain_size_range", "temperature_range"):
            if not set(e) - {"rule"} or set(e) - {"rule", "min", "max"} or not all(_number(e[k]) for k in e if k != "rule"):
                raise AnswerInvalid("a range rule names a minimum and/or maximum")
            out.append({k: (float(x) if k != "rule" else x) for k, x in e.items()})
        else:
            if set(e) != {"rule", "values"}:
                raise AnswerInvalid("a phase or test-type rule names its values")
            out.append({"rule": e["rule"], "values": _values(e["values"], CATEGORY_RULE_VALUES[e["rule"]], e["rule"])})
    return out


def _scope(v, keys) -> dict:
    if not isinstance(v, dict) or set(v) != keys:
        raise AnswerInvalid(f"a scope has exactly {', '.join(sorted(keys))}")
    out = {"phase_class": _values(v["phase_class"], PHASE_CLASSES - {"other"}, "phase_class"),
           "test_type": _values(v["test_type"], TEST_TYPES, "test_type"),
           "temperature_band": _bands(v["temperature_band"])}
    if "alloy_class" in keys:
        out["alloy_class"] = _values(v["alloy_class"], ALLOY_CLASSES, "alloy_class")
    return out


@dataclass(frozen=True)
class Answer:
    domain_matches: bool
    claim_scope: dict
    outcome: str
    exclusion_rules: list
    narrower: dict | None
    stated: dict  # owner, 2026-10-07: per scope part, stated by the claim (True) or the Planner's default (False)


def read_answer(data: Mapping) -> Answer:
    if set(data) != KEYS:
        raise AnswerInvalid("the answer has exactly the keys " + ", ".join(sorted(KEYS)))
    if not isinstance(data["domain_matches"], bool):
        raise AnswerInvalid("domain_matches is true or false")
    if not _word(data["outcome"], SUPPORTED_OUTCOMES):
        raise AnswerInvalid("the outcome comes from the list")
    narrower = None if data["narrower"] is None else _scope(data["narrower"], NARROWER_KEYS)
    stated = data["stated"]
    if not isinstance(stated, dict) or set(stated) != SCOPE_KEYS or not all(isinstance(v, bool) for v in stated.values()):
        raise AnswerInvalid("'stated' marks each scope part true (stated by the claim) or false (defaulted)")
    scope = _scope(data["claim_scope"], SCOPE_KEYS)
    for part, is_stated in stated.items():
        if not is_stated and _sorted(scope[part]) != _sorted(DEFAULT_SCOPE[part]):
            raise AnswerInvalid(f"{part} is marked as not stated by the claim but is not the default")
    return Answer(data["domain_matches"], scope, data["outcome"], _exclusions(data["exclusion_rules"]), narrower,
                  dict(sorted(stated.items())))


def _sorted(values: list) -> list:
    return sorted(values, key=lambda v: json.dumps(v, sort_keys=True))


# --- The plan, built by code -------------------------------------------------------------------------

def one_plan(scope: Mapping) -> bool:
    """Owner, A11: one alloy class, one temperature band and one test type make one plan (its three tags)."""
    return len(scope.get("alloy_class", [None])) == 1 and len(scope["temperature_band"]) == 1 \
        and len(scope["test_type"]) == 1


def build_plan(hypothesis_version_id: int, scope: Mapping, outcome: str, exclusion_rules: list,
               sufficiency_option: str, alloy_class: list | None = None) -> dict:
    """The plan for a one-plan scope: the profile's default plan with only these parameters set. Raises
    PlanError if the result is not valid."""
    plan = plans.default_plan(hypothesis_version_id)
    band = scope["temperature_band"][0]
    plan["scope"] = {"alloy_class": list(alloy_class or scope["alloy_class"]), "temperature_band": [band["band"]],
                     "test_type": list(scope["test_type"]), "phase_class": list(scope["phase_class"])}
    plan["variables"]["outcome"] = {"field": outcome, "unit": "MPa"}
    plan["exclusion_rules"] = [dict(e) for e in exclusion_rules]
    plan["sufficiency"]["option"] = sufficiency_option
    if band["band"] != plans.ROOM_TEMPERATURE:
        plan["rules"][plans.RANGE_RULE] = {"min": band["min"], "max": band["max"]}
    plans.validate(plan)
    plans.tags_for(plan)
    return plan


def plan_without_version(plan: Mapping) -> dict:
    """A plan less its hypothesis version (A8: the narrower question's run adds its own)."""
    return {k: v for k, v in plan.items() if k != "hypothesis_version"}


def make_check(hypothesis_version_id: int, sufficiency_option: str, approved_alloy_classes: set[str]):
    """The common interface's check of a Planner answer: None, 'malformed' or 'invalid_plan'."""

    def check(outputs: Mapping[str, str]) -> str | None:
        data = parse(outputs["plan"])
        if data is None:
            return "malformed"
        try:
            answer = read_answer(data)
            if not answer.domain_matches:
                return None  # a valid answer: the run stops before the lock (PRD 5.5)
            if not set(answer.claim_scope["alloy_class"]) <= approved_alloy_classes:
                raise AnswerInvalid("an alloy class is not an approved tag value")
            if one_plan(answer.claim_scope):
                build_plan(hypothesis_version_id, answer.claim_scope, answer.outcome, answer.exclusion_rules,
                           sufficiency_option)
        except (AnswerInvalid, plans.PlanError):
            return "invalid_plan"
        return None

    return check


# --- One Planner call within a run --------------------------------------------------------------------

@dataclass(frozen=True)
class PlannerResult:
    answer: Answer | None
    failure: str | None
    stage_id: int
    invocation_id: int
    calls: list


def run_planner(engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> PlannerResult:
    """The Planner's stage: opened (stage result and invocation) before the request, its input read through the
    access layer, one agent call through the common interface, the answer checked by code, the stage closed
    with the checked answer or the failure code. No model call runs inside a database transaction."""
    from sqlalchemy import text
    from hypocurate.access.dispatch import bind_invocation
    from hypocurate.access.inputs import role_input
    from hypocurate.pipeline.agents.interface import call_agent
    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
    from hypocurate.pipeline.agents.settings import recorded

    stage_id, invocation = open_stage(engine, run_id, "planner", "planner")
    data = role_input(bind_invocation(engine, invocation))
    with engine.connect() as conn:
        row = conn.execute(text("SELECT r.hypothesis_version_id, hv.sufficiency_option FROM run r JOIN "
                                "hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"),
                           dict(r=run_id)).one()
    approved = {t["value"] for t in data["tag_values"] if t.get("kind") == "alloy_class"}
    s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
    inputs = render_inputs(data)
    result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
                        max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
                        ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
                        check=make_check(row.hypothesis_version_id, row.sufficiency_option, approved))
    if result.failure is not None:
        close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts},
                    input_=inputs)
        return PlannerResult(None, result.failure, stage_id, invocation, result.calls)
    answer = read_answer(parse(result.outputs["plan"]))
    # Decision B: the question as tested, in code's words, labelled as the Planner's reading.
    tested = reading.question_as_tested(answer.claim_scope, answer.outcome, answer.exclusion_rules, answer.stated,
                                        "planner")
    close_stage(engine, run_id, stage_id, "done", {"answer": answer.__dict__, "attempts": result.attempts,
                                                   "question_as_tested": tested}, input_=inputs)
    return PlannerResult(answer, None, stage_id, invocation, result.calls)

