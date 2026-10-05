"""The plan model (PRD 5.1; build step 6).

A plan is plain JSON content that follows `PLAN_SCHEMA` exactly (owner, 2026-10-05): named
keys at every level, vocabulary values, numbers, integers, common field names and units, and
no free text. `validate` refuses content that its own projection would change (an unknown
key, a value outside a vocabulary, a number where a code belongs), content missing a part,
and content that the sprint-1 template does not support.

Every setting that affects which records are eligible or how they are grouped is in the
plan (`rules`, `scope`, `exclusion_rules`, `eligibility_rules`, `sufficiency`), and the
plan records the domain profile its defaults came from (`profile`). The default and the
reference plans are built from the domain profile (`hypocurate.pipeline.profile`), its one
named place for each default. Plans are fixed inputs in step 6; the Planner (step 8) fills the
same template.

The fingerprint is the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Mapping

from hypocurate.access.allowlist import PLAN_SCHEMA
from hypocurate.access.fields import project
from hypocurate.access.vocabulary import SENSITIVITY_KEYS
from hypocurate.pipeline import profile as p

PARTS = ("hypothesis_version", "variables", "scope", "model", "sufficiency", "fields_to_extract", "exclusion_rules",
         "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules")
RULES = ("same_alloy_decimals", "duplicate_tolerance", "survivor_source_order", "min_grain_sizes",
         "room_temperature_min", "room_temperature_max", "single_phase", "accepted_value_statuses", "grouping")
# What each eligibility-rule code does when the plan names it for a flag (PRD 5.3).
FLAG_RULE_CODES = frozenset({"invalid_value", "duplicate_counted_once", "identity_unresolved", "conflict_unresolved",
                             "in_scope"})
MENU_RULES = frozenset({"grain_size_range", "temperature_range", "phase", "test_type"})


class PlanError(ValueError):
    """The content is not a valid plan for the supported template."""


def default_plan(hypothesis_version_id: int) -> dict:
    """The default plan of the grain-size strengthening profile, every value from its named setting."""
    return {
        "hypothesis_version": hypothesis_version_id,
        "variables": {"outcome": {"field": p.OUTCOME[0], "unit": p.OUTCOME[1]},
                      "predictor": {"field": p.PREDICTOR[0], "unit": p.PREDICTOR[1],
                                    "transformation": p.TRANSFORMATION}},
        "scope": {"alloy_class": list(p.ALLOY_CLASSES), "temperature_band": list(p.TEMPERATURE_BANDS),
                  "test_type": list(p.PERMITTED_TEST_TYPES), "phase_class": list(p.PHASE_CLASSES)},
        "model": {"name": p.MODEL, "null": "k <= 0", "alternative": "k > 0", "alpha": float(p.ALPHA)},
        "sufficiency": {"option": p.SUFFICIENCY_OPTION, **dict(p.FIXED_MINIMUMS)},
        "fields_to_extract": list(p.FIELDS_TO_EXTRACT),
        "exclusion_rules": [{"rule": "grain_size_range", "min": float(p.GRAIN_SIZE_FLOOR_UM)}],
        "eligibility_rules": [
            {"flag_kind": "invalid_value", "rule": "invalid_value"},
            {"flag_kind": "exact_duplicate", "rule": "duplicate_counted_once"},
            {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "identity_unresolved"},
            {"flag_kind": "possible_duplicate", "rule": "duplicate_counted_once"},
            {"flag_kind": "values_disagree", "rule": "conflict_unresolved"},
        ],
        "verdict_statement": "pooled_test_gives_verdict",
        "sensitivity_analyses": list(p.SENSITIVITY_ANALYSES),
        "profile": {"name": p.PROFILE_NAME, "version": p.PROFILE_VERSION},
        "rules": {"same_alloy_decimals": p.SAME_ALLOY_DECIMALS_DEFAULT,
                  "duplicate_tolerance": float(p.DUPLICATE_TOLERANCE),
                  "survivor_source_order": list(p.SURVIVOR_SOURCE_ORDER),
                  "min_grain_sizes": p.MIN_GRAIN_SIZES_PER_ALLOY,
                  "room_temperature_min": float(p.ROOM_TEMPERATURE_C[0]),
                  "room_temperature_max": float(p.ROOM_TEMPERATURE_C[1]),
                  "single_phase": p.SINGLE_PHASE,
                  "accepted_value_statuses": list(p.ACCEPTED_VALUE_STATUSES),
                  "grouping": [{"source": s, "unit": u} for s, u in p.GROUPING.items()]},
    }


def reference_plan(hypothesis_version_id: int) -> dict:
    """The fixed reference plan of acceptance criterion 14.1a (the Planner bypassed): the
    default plan under the owner's step 6 decisions."""
    return default_plan(hypothesis_version_id)


def canonical(content: Mapping[str, Any]) -> str:
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(content: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()


def validate(content: Any) -> dict:
    """The content as a plan, or PlanError. Returns a deep copy."""
    if not isinstance(content, Mapping):
        raise PlanError("a plan is a JSON object")
    content = copy.deepcopy(dict(content))
    try:
        canonical(content)
    except (TypeError, ValueError) as error:
        raise PlanError(f"the plan is not plain JSON: {error}") from None
    missing = [k for k in PARTS if k not in content]
    if missing:
        raise PlanError(f"the plan lacks {', '.join(missing)}")
    if project(content, PLAN_SCHEMA) != content:
        raise PlanError("the plan has a key, value or type outside PLAN_SCHEMA (its projection would change it)")
    _check_template(content)
    return content


def _check_template(c: dict) -> None:
    v, s, m, r = c["variables"], c["scope"], c["model"], c["rules"]
    if set(v) != {"outcome", "predictor"} or set(v["outcome"]) != {"field", "unit"} or \
            set(v["predictor"]) != {"field", "unit", "transformation"}:
        raise PlanError("variables need an outcome (field, unit) and a predictor (field, unit, transformation)")
    if (v["predictor"]["field"], v["predictor"]["unit"]) != ("grain_size", "µm"):
        raise PlanError("the supported model's predictor is grain size in µm")
    if v["outcome"]["field"] == v["predictor"]["field"]:
        raise PlanError("the outcome and the predictor are different fields")
    if set(m) != {"name", "null", "alternative", "alpha"} or not 0 < m["alpha"] < 1:
        raise PlanError("the model needs its name, hypotheses and a threshold between 0 and 1")
    if set(s) != {"alloy_class", "temperature_band", "test_type", "phase_class"} or not all(s.values()):
        raise PlanError("the scope names alloy classes, temperature bands, test types and phase classes")
    if s["temperature_band"] != ["room temperature"]:
        raise PlanError("sprint 1 supports the room-temperature band only")
    if set(r) != set(RULES):
        raise PlanError(f"the plan's rules are exactly: {', '.join(RULES)}")
    if not (0 <= r["same_alloy_decimals"] <= 3 and r["min_grain_sizes"] >= 2 and 0 <= r["duplicate_tolerance"] < 1
            and math.isfinite(r["room_temperature_min"]) and r["room_temperature_min"] <= r["room_temperature_max"]):
        raise PlanError("a rule is out of range")
    order = r["survivor_source_order"]
    units = [g["source"] for g in r["grouping"]]
    if len(set(order)) != len(order) or len(set(units)) != len(units) or any(set(g) != {"source", "unit"}
                                                                           for g in r["grouping"]):
        raise PlanError("the survivor order and the grouping name each source once")
    if not r["accepted_value_statuses"] or "converted" not in r["accepted_value_statuses"]:
        raise PlanError("the accepted value statuses include 'converted'")
    suff = c["sufficiency"]
    if set(suff) != {"option", "min_records", "min_alloys", "min_groups", "min_resid_df"} or \
            min(suff[k] for k in suff if k != "option") < 1:
        raise PlanError("the sufficiency option needs its four minimums, each at least 1")
    for rule in c["exclusion_rules"]:
        if rule.get("rule") not in MENU_RULES:
            raise PlanError("an exclusion rule comes from the menu (PRD 5.2)")
        if rule["rule"] in ("grain_size_range", "temperature_range") and not ({"min", "max"} & set(rule)):
            raise PlanError("a range rule needs a minimum or a maximum")
        if rule["rule"] in ("phase", "test_type") and not rule.get("values"):
            raise PlanError("a phase or test-type rule needs its values")
    seen = set()
    for e in c["eligibility_rules"]:
        if "flag_kind" not in e or "rule" not in e or e["rule"] not in FLAG_RULE_CODES:
            raise PlanError("an eligibility rule names a flag kind and one of the flag rule codes")
        key = (e["flag_kind"], e.get("category"))
        if key in seen:
            raise PlanError("each flag kind (and category) has one eligibility rule")
        seen.add(key)
    keys = c["sensitivity_analyses"]
    if len(set(keys)) != len(keys) or not set(keys) <= SENSITIVITY_KEYS - {"removal_after_lock"}:
        raise PlanError("sensitivity analyses are named once each, from the vocabulary")


def tags_for(content: Mapping[str, Any]) -> dict[str, str]:
    """The run's three tags (PRD 5.5), one per kind, from the plan."""
    outcome = content["variables"]["outcome"]["field"]
    alloy_classes, types, bands = (content["scope"][k] for k in ("alloy_class", "test_type", "temperature_band"))
    if outcome not in p.PROPERTY_TAGS or len(alloy_classes) != 1 or len(types) != 1 or len(bands) != 1:
        raise PlanError("three tags per run: the plan needs one outcome, one alloy class, one test type and one band")
    condition = p.TEST_CONDITION_TAGS.get((bands[0], types[0]))
    if condition is None:
        raise PlanError("no test-condition tag for this band and test type")
    return {"property": p.PROPERTY_TAGS[outcome], "alloy_class": alloy_classes[0], "test_condition": condition}
