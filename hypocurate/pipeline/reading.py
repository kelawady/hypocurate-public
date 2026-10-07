"""The question as tested (step 8b fix round 1, owner's decision B; register 'question_as_tested').

Code writes, from a scope and its exclusion rules, the question a run actually tests: the outcome against grain
size, each scope part in words (a band other than room temperature with its range), and each exclusion rule. For a
run with the Planner, these are the Planner's reading of the claim: each part is marked as the claim states it or
as assumed (the Planner's own marks, checked only in that a part marked assumed must hold the profile's default),
and the label says the reading is not verified by code and that a person confirms it at the rules lock on the
website (step 10). For a fixed-plan run, or a narrower question's run, the reading comes from that plan.

The text is stored with the Planner's stage output (the Planner's reading) and, for a fixed or narrower plan,
follows from the locked plan; the command line prints it beside the original claim before the run goes on to the
rules lock, and `show` prints it.
"""
from __future__ import annotations

from typing import Any, Mapping

from hypocurate.pipeline import display
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import profile as p

LABELS = {
    "planner": "the Planner's reading of the claim; not verified by code; a person confirms it at the rules lock on "
               "the website (step 10)",
    "fixed": "the fixed reference plan (criterion 14.1a); not read from the claim",
    "narrower": "the narrower plan stored by the original question's narrowing decision",
}
PART_LABELS = {"phase_class": "phase class", "test_type": "test type"}
STATED = "as the claim states"
ASSUMED = "assumed: the claim does not state it"


def _number(v: float) -> str:
    return display.at_most_one_decimal(float(v))


def band_words(band: Mapping) -> str:
    if band["band"] == plans.ROOM_TEMPERATURE:
        lo, hi = p.ROOM_TEMPERATURE_C
    else:
        lo, hi = band["min"], band["max"]
    return f"{band['band']}, {_number(lo)} to {_number(hi)} °C"


def exclusion_words(rule: Mapping) -> str:
    kind = rule["rule"]
    if kind in ("grain_size_range", "temperature_range"):
        unit = "µm" if kind == "grain_size_range" else "°C"
        what = "with a grain size" if kind == "grain_size_range" else "tested"
        lo, hi = rule.get("min"), rule.get("max")
        if lo is not None and hi is not None:
            return f"excluding records {what} outside {_number(lo)} to {_number(hi)} {unit}"
        if lo is not None:
            return f"excluding records {what} below {_number(lo)} {unit}"
        return f"excluding records {what} above {_number(hi)} {unit}"
    label = "phase class" if kind == "phase" else "test type"
    return f"excluding records of a {label} other than {', '.join(rule['values'])}"


def question_as_tested(scope: Mapping, outcome: str, exclusion_rules: list, stated: Mapping | None,
                       source: str) -> dict[str, str]:
    """`scope` in the Planner's answer form (bands as {band, min, max}); `stated` the Planner's marks, or None."""

    def mark(part: str, words: str) -> str:
        if stated is None:
            return words
        return f"{words} ({STATED if stated.get(part) else ASSUMED})"

    parts = [mark("alloy_class", ", ".join(scope["alloy_class"]))]
    for part in ("phase_class", "test_type"):
        parts.append(mark(part, f"{PART_LABELS[part]} {', '.join(scope[part])}"))
    parts.append(mark("temperature_band", "; ".join(band_words(b) for b in scope["temperature_band"])))
    parts += [exclusion_words(r) for r in exclusion_rules]
    head = f"{outcome.replace('_', ' ')} against grain size, in "
    return {"text": head + "; ".join(parts), "label": LABELS[source], "source": source}


def from_plan(plan: Mapping[str, Any], source: str) -> dict[str, str]:
    """The reading of a locked (or reference) plan: its scope, its band's range and its exclusion rules."""
    s = plan["scope"]
    bands = []
    for name in s["temperature_band"]:
        r = plan.get("rules", {}).get(plans.RANGE_RULE) if name != plans.ROOM_TEMPERATURE else None
        bands.append({"band": name, **({"min": r["min"], "max": r["max"]} if r else {})})
    scope = {"alloy_class": s["alloy_class"], "phase_class": s["phase_class"], "test_type": s["test_type"],
             "temperature_band": bands}
    return question_as_tested(scope, plan["variables"]["outcome"]["field"], plan.get("exclusion_rules") or [], None,
                              source)
