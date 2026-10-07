"""The Analyst's named facts (step 8b; owner, 2026-10-07: placeholders and fewer facts; register 'analyst_names').

The Analyst writes no digits: wherever it wants a number, a p-value, the paper figures, the outcome or the verdict,
it writes the name of a fact in braces, for example {pooled_estimate}; code replaces each name with its display
string or ready-made phrase (`agents.text_checks.render`). This module builds those names from what code stored:

- the decision: {outcome_wording} (always to be used), {verdict_wording} (to be used when there is a verdict),
  {evidence_level}, {evidence_level_wording}, {result_label};
- the plan: {alpha}, {sufficiency_option}, each minimum ({minimum_records}, ...), and where the scope came from:
  per scope part a note {scope_alloy_class}, {scope_phase_class}, {scope_test_type}, {scope_temperature_band}
  ("the claim did not state a test type; tension was assumed"), or {scope_source} for a fixed plan;
- the pooled result: counts, each count against its minimum ({count_records}, {met_records}, ...), and unless
  withheld the estimate, its standard error, {pooled_p_phrase} and {pooled_figures_phrase};
- per source (its key in the name): counts, label and, unless withheld, estimate, standard error and phrases;
- both calibrations of the pooled result (fixed and estimated noise): shares with intervals and the flag; below the
  minimums only the fixed-noise detection and false-positive shares, which use no outcome value;
- a summary of the sensitivity sets, built by code (owner, 2026-10-07): how many sets; how many under each of the
  four per-source labels, classified against the pooled result by the same function (`statistics.label`); the
  names of the sets not labelled "agrees"; the smallest and largest estimate with their sets; and the result
  without the group holding the largest share of slope information. The full per-set numbers are not given;
- for a run with no dataset frozen: the gap facts (records lacking each field per source, the kind of nothing
  found, the minimums missed);
- at 'narrowed': the claim's parts with their counts, the parts with none, the narrower scope.

Every value is a string (display strings and phrases from `pipeline.display`; counts as written). Names hold
lower-case letters and underscores only, so a digit can never be part of a name. Below the minimums no name gives an
estimate, a standard error, a p-value or the paper figures (owner's standing requirement).
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from hypocurate.pipeline import display
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, INFLUENCE_KEY

NAME = re.compile(r"[a-z_]+")
LABEL_WORDS = {"agrees": "agrees", "conflicts": "conflicts",
               "same_direction_different_decision": "same direction, different decision",
               "not_enough_data": "not enough data"}
SCOPE_WORDS = {"alloy_class": "an alloy class", "phase_class": "a phase class", "test_type": "a test type",
               "temperature_band": "a temperature"}
SCOPE_LABELS = {"alloy_class": "alloy class", "phase_class": "phase class", "test_type": "test type",
                "temperature_band": "temperature"}
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _s(v: Any) -> str:
    """A value as text: integers as written, floats through the display rules' fallback, words as they are."""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return display.fallback(v)
    return str(v)


def _key(source: str) -> str:
    return re.sub(r"[^a-z_]", "_", source.lower())


def band_words(band: Mapping | str) -> str:
    if not isinstance(band, Mapping):
        return str(band)
    if band.get("band") == "room temperature" or "min" not in band:
        return str(band.get("band"))
    return f"{band['band']} ({display.at_most_one_decimal(band['min'])} to {display.at_most_one_decimal(band['max'])} °C)"


def scope_value_words(part: str, values: list) -> str:
    return ", ".join(band_words(v) if part == "temperature_band" else str(v) for v in values)


def scope_notes(scope: Mapping | None, stated: Mapping | None) -> dict[str, str]:
    """Per scope part: stated by the claim, or the Planner's default (owner, 2026-10-07)."""
    if not scope or not stated:
        return {}
    out = {}
    for part, label in SCOPE_LABELS.items():
        if part not in scope:
            continue
        values = scope_value_words(part, scope[part])
        out[f"scope_{part}"] = (f"{label} {values}, as the claim states" if stated.get(part)
                                else f"the claim did not state {SCOPE_WORDS[part]}; {values} was assumed")
    return out


def _set_name(key: str) -> str:
    return INFLUENCE_DISPLAY_NAME if key == INFLUENCE_KEY else key.replace("_", " ")


def _calibration(prefix: str, c: Mapping | None) -> dict[str, str]:
    if not isinstance(c, Mapping) or c.get("status") != "computed":
        reason = (c or {}).get("reason") if isinstance(c, Mapping) else None
        return {f"{prefix}_unavailable": str(reason or "not computed").replace("_", " ")}
    a = c.get("assumptions") or {}
    return {f"{prefix}_false_positive": display.percent(c["null"]["share"]),
            f"{prefix}_false_positive_low": display.percent(c["null"]["ci_low"]),
            f"{prefix}_false_positive_high": display.percent(c["null"]["ci_high"]),
            f"{prefix}_detection": display.percent(c["effect"]["share"]),
            f"{prefix}_detection_low": display.percent(c["effect"]["ci_low"]),
            f"{prefix}_detection_high": display.percent(c["effect"]["ci_high"]),
            f"{prefix}_flag": str(c.get("flag_wording") or c.get("confidence_flag")),
            f"{prefix}_scatter": display.at_most_one_decimal(a["scatter"]) if "scatter" in a else "not given",
            f"{prefix}_shift": display.at_most_one_decimal(a["shift"]) if "shift" in a else "not given"}


def _result(prefix: str, e: Mapping, withheld: bool) -> dict[str, str]:
    c = e.get("counts") or {}
    out = {f"{prefix}_records": _s(c.get("n_records")), f"{prefix}_alloys": _s(c.get("n_alloys")),
           f"{prefix}_groups": _s(c.get("n_groups")),
           f"{prefix}_inference": "valid" if (e.get("checks") or {}).get("inference_valid") else "not valid"}
    if e.get("inference_reason"):
        out[f"{prefix}_inference_reason"] = str(e["inference_reason"]).replace("_", " ")
    if withheld:
        return out
    if e.get("estimate") is not None:
        out[f"{prefix}_estimate"] = display.one_decimal(e["estimate"])
    if e.get("std_error") is not None:
        out[f"{prefix}_std_error"] = display.one_decimal(e["std_error"])
    if e.get("p_value") is not None:
        out[f"{prefix}_p_phrase"] = display.p_phrase(e["p_value"])
    if all(x is not None for x in (c.get("n_groups_informative"), c.get("effective_papers"),
                                   c.get("largest_paper_share"), e.get("df"))):
        out[f"{prefix}_figures_phrase"] = display.figures_phrase(c["n_groups_informative"], c["effective_papers"],
                                                                 c["largest_paper_share"], e["df"])
    return out


def sensitivity_summary(analyses: list[Mapping], pooled: Mapping, alpha: float, withheld: bool) -> dict[str, str]:
    """The sensitivity sets classified against the pooled result with the per-source labels and function."""
    sets = [e for e in analyses if e.get("scope") == "sensitivity"]
    out = {"sensitivity_sets": str(len(sets))}
    labels = {e["set"]: st.label(e, pooled, alpha) for e in sets}
    for code, words in LABEL_WORDS.items():
        out[f"sensitivity_{code}"] = str(sum(1 for v in labels.values() if v == code))
    others = [f"{_set_name(k)} ({LABEL_WORDS[v]})" for k, v in labels.items() if v != "agrees"]
    out["sensitivity_not_agreeing"] = "; ".join(others) if others else "none"
    estimated = [e for e in sets if e.get("estimate") is not None]
    if estimated and not withheld:
        low = min(estimated, key=lambda e: e["estimate"])
        high = max(estimated, key=lambda e: e["estimate"])
        out.update(sensitivity_smallest_estimate=display.one_decimal(low["estimate"]),
                   sensitivity_smallest_set=_set_name(low["set"]),
                   sensitivity_largest_estimate=display.one_decimal(high["estimate"]),
                   sensitivity_largest_set=_set_name(high["set"]))
    influential = next((e for e in sets if e["set"] == INFLUENCE_KEY), None)
    if influential is not None:
        out.update(_result("without_largest_share", influential, withheld))
        out["without_largest_share_label"] = LABEL_WORDS[labels[INFLUENCE_KEY]]
    return out


def analysis_names(stats: Mapping, gap: Mapping, plan: Mapping, scope_note: Mapping[str, str]) -> dict[str, str]:
    """The names of a run after the analysis stage (with or without a dataset frozen)."""
    d = stats.get("decision") or {}
    names: dict[str, str] = {"outcome_wording": str(d.get("outcome_wording")),
                             "evidence_level": _s(d.get("evidence_level")),
                             "evidence_level_wording": str(d.get("evidence_level_wording"))}
    if d.get("verdict"):
        names["verdict_wording"] = str(d.get("verdict_wording"))
    if d.get("label"):
        names["result_label"] = str(d["label"])
    names["alpha"] = display.as_given(plan["alpha"])
    names["sufficiency_option"] = str(plan["sufficiency_option"]).replace("_", " ")
    for k, v in plan["minimums"].items():
        names[f"minimum_{k}"] = _s(v)
    names.update(scope_note)
    withheld = bool(stats.get("withheld"))
    analyses = [e for e in stats.get("analyses") or [] if isinstance(e, Mapping)]
    if analyses:
        pooled = analyses[0]
        names.update(_result("pooled", pooled, withheld))
        for k, m in (pooled.get("minimums") or {}).items():
            names[f"count_{k}"] = _s(m.get("count"))
            names[f"met_{k}"] = "met" if m.get("met") else "not met"
        cal = pooled.get("calibration") or {}
        if withheld:  # the fixed-noise shares use no outcome value (owner, 2026-10-07)
            fixed = (pooled.get("detection") or {}).get("fixed") or {}
            if "detection" in fixed:
                names.update(fixed_detection=display.percent(fixed["detection"]),
                             fixed_false_positive=display.percent(fixed["false_positive"]))
        else:
            names.update(_calibration("fixed", cal.get("fixed")))
            names.update(_calibration("estimated", cal.get("estimated")))
        for e in analyses:
            if e.get("scope") == "per_source":
                prefix = _key(e["source"])
                names.update(_result(prefix, e, withheld))
                if e.get("label"):
                    names[f"{prefix}_label"] = LABEL_WORDS.get(e["label"], str(e["label"]))
        names.update(sensitivity_summary(analyses, pooled, plan["alpha"], withheld))
    missed = gap.get("minimums_missed") or []
    names["minimums_missed"] = ", ".join(str(m).replace("_", " ") for m in missed) if missed else "none"
    if gap.get("kind"):
        names["nothing_found"] = str(gap["kind"]).replace("_", " ")
    for s in gap.get("sources") or []:
        prefix = _key(s["source"])
        if s.get("kind"):
            names[f"{prefix}_nothing_found"] = str(s["kind"]).replace("_", " ")
        names[f"{prefix}_search"] = str(s.get("search_status"))
    for source, fields in (gap.get("records_lacking_fields") or {}).items():
        for field, n in fields.items():
            if n:
                names[f"{_key(source)}_lacking_{_key(field)}"] = _s(n)
    return names


def narrowing_names(n: Mapping) -> dict[str, str]:
    """The names of a partly-sufficient original at 'narrowed'."""
    d = n.get("decision") or {}
    names = {"outcome_wording": str(d.get("outcome_wording")), "evidence_level": _s(d.get("evidence_level")),
             "evidence_level_wording": str(d.get("evidence_level_wording"))}
    names.update(scope_notes(n.get("claim_scope"), n.get("scope_stated")))
    for letter, part in zip(LETTERS, n.get("part_counts") or []):
        value = band_words(part["value"]) if part["part"] == "temperature_band" else str(part["value"])
        names[f"part_{letter}"] = f"{SCOPE_LABELS.get(part['part'], part['part'])} {value}"
        names[f"part_{letter}_records"] = _s(part["n"])
    zero = n.get("zero_parts") or []
    names["parts_without_records"] = "; ".join(
        f"{SCOPE_LABELS.get(z['part'], z['part'])} {band_words(z['value']) if z['part'] == 'temperature_band' else z['value']}"
        for z in zero) or "none"
    narrower = n.get("narrower_scope") or {}
    names["narrower_scope"] = "; ".join(f"{SCOPE_LABELS[p]} {scope_value_words(p, v)}" for p, v in narrower.items()
                                        if p in SCOPE_LABELS)
    return names


def check_names(names: Mapping[str, str]) -> None:
    bad = [k for k in names if not NAME.fullmatch(k)]
    if bad:
        raise ValueError(f"fact names hold lower-case letters and underscores only: {bad}")
