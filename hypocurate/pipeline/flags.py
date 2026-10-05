"""The code checks that raise flags (PRD 5.3; build step 6). Pure functions.

Input: exactly what Checks' access object returns (`records_full`, the projected `plan`).
Checks sees every value (PRD 4) and only raises flags; Inclusion decides what a flag means
under the locked plan. **Per-record rules (invalid values) and pairwise comparisons that feed a
whole-group classification** (duplicate, conflict, ambiguous group); no model, slope, residual or
hypothesis of the plan, so agreement with the relationship under test can never decide which
records are credible (PRD 5.3). The matching settings are read from the locked plan; the fixed
policies listed in `eligibility.py` (which conditions are compared, how a paper is identified,
the ambiguity rule) are code.

Flags (owner, 2026-10-05):
- `invalid_value` / "physically impossible": tensile strength below yield strength, or a
  grain size of zero or less. One flag per record.
- Duplicates and conflicts, **only between records of different sources** (register
  'conflict_pairing_rule'); rows within one source are separate measurements. Two records
  are *candidates* when they have the same alloy (the plan's same-alloy rule), grain sizes
  within the plan's tolerance (a matching tolerance), and nothing known that differs: the
  same paper or a paper unknown on one side, and the same test conditions (test type,
  test temperature) or a condition unknown on one side.
  - same paper and every condition known: yield strengths within the tolerance → an exact
    duplicate; beyond it → a conflict (`values_disagree`, "differ beyond tolerance");
  - the paper or a condition unknown on one side: yield strengths within the tolerance → a
    possible duplicate; beyond it → not a candidate (nothing says it is the same measurement).
  Candidate links form groups (connected components). A group with two or more records from
  one source, or one in which some pair is not linked, is ambiguous: `possible_duplicate`,
  "several candidates" (nothing is paired on a guess); its definite conflicts, if any, get a
  `values_disagree` flag of their own (review finding 4). Otherwise a group with any conflicting
  pair is a conflict, else a possible duplicate if any link is possible, else an exact
  duplicate. One flag per group, naming all its records (plus that conflict flag).
- Relative difference: |a − b| / min(|a|, |b|) (register 'values_disagree_tolerance').
- The numbers compared are stored with the flag for audit (`compared_values`) and never
  returned to the Critic (step 5).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Iterable, Mapping

from hypocurate.sources.normalize import doi_group_key, identity_hash, same_alloy_key

VALUE_STATUSES = ("converted", "assigned_from_source", "assigned_by_decision")


@dataclass
class Flag:
    kind: str
    category: str
    records: list[int]
    compared_values: dict = field(default_factory=dict)


def relative_difference(a: float, b: float) -> float:
    small = min(abs(a), abs(b))
    if a == b:
        return 0.0
    return abs(a - b) / small if small > 0 else math.inf


def _value(rec: Mapping, f: str, statuses=VALUE_STATUSES) -> Any:
    entry = rec["harmonized"].get(f) if isinstance(rec.get("harmonized"), Mapping) else None
    if isinstance(entry, Mapping) and entry.get("status") in statuses:
        return entry.get("value")
    return None


def _number(rec: Mapping, f: str, statuses=VALUE_STATUSES) -> float | None:
    v = _value(rec, f, statuses)
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


# The outcome Checks compares: the one supported model's (re-check finding 2b; plans with
# another outcome are refused at validation, `eligibility.SUPPORTED_OUTCOMES`).
COMPARED_OUTCOME = "yield_strength"


def _doi(rec: Mapping) -> str | None:
    doi = rec.get("paper_doi")
    return doi_group_key(doi) if isinstance(doi, str) and doi.strip() else None


def _reference(rec: Mapping) -> str | None:
    """The paper reference as reported, normalized: spaces collapsed, case-folded."""
    ref = rec.get("paper_reference")
    return " ".join(ref.split()).casefold() if isinstance(ref, str) and ref.strip() else None


def same_paper(a: Mapping, b: Mapping) -> bool | None:
    """Whether two records cite the same paper, from their own normalized paper references only
    (re-check finding 2a: never from the plan's grouping, which is for clustering): both DOIs
    known, compare them; else both references known, compare them; else unknown (None)."""
    da, db = _doi(a), _doi(b)
    if da and db:
        return da == db
    ra, rb = _reference(a), _reference(b)
    if ra and rb:
        return ra == rb
    return None


def invalid_values(records: Iterable[Mapping], outcome: str | None = None) -> list[Flag]:
    """Physically impossible values, on every record whatever the plan's outcome (re-check
    finding 2b): tensile strength below yield strength; a grain size of zero or less."""
    out = []
    for r in records:
        ys, uts, gs = _number(r, "yield_strength"), _number(r, "ultimate_tensile_strength"), _number(r, "grain_size")
        reasons = {}
        if ys is not None and uts is not None and uts < ys:
            reasons["ultimate_tensile_strength_below_yield_strength"] = [uts, ys]
        if gs is not None and gs <= 0:
            reasons["grain_size_not_positive"] = [gs]
        if reasons:
            out.append(Flag("invalid_value", "physically impossible", [r["id"]], reasons))
    return out


@dataclass(frozen=True)
class Matching:
    """The settings that decide which records are compared (step 6 review, finding 2): the
    same-alloy step, the tolerance and the value statuses that count as known. Not the grouping,
    which is for clustering only (re-check finding 2a)."""
    decimals: int
    tolerance: float
    statuses: tuple


def matching(plan: Mapping[str, Any], key: str = "primary") -> Matching:
    """The matching settings of set `key` under the locked plan (its own change applied)."""
    from hypocurate.pipeline.eligibility import settings
    st = settings(plan, key)
    return Matching(st.decimals, plan["rules"]["duplicate_tolerance"], tuple(sorted(st.statuses)))


def _condition(a: Mapping, b: Mapping, statuses=VALUE_STATUSES) -> str:
    """'same', 'unknown' (a condition missing on one side) or 'differs'."""
    state = "same"
    for f in ("test_type", "test_temperature"):
        va, vb = _value(a, f, statuses), _value(b, f, statuses)
        if va is None or vb is None:
            state = "unknown"
        elif va != vb:
            return "differs"
    return state


def _link(a: Mapping, b: Mapping, plan: Mapping, m: Matching) -> tuple[str, dict] | None:
    """The candidate link between two records of different sources, or None."""
    tol, outcome, st = m.tolerance, COMPARED_OUTCOME, m.statuses
    ga, gb, ya, yb = (_number(a, "grain_size", st), _number(b, "grain_size", st), _number(a, outcome, st),
                      _number(b, outcome, st))
    if None in (ga, gb, ya, yb) or relative_difference(ga, gb) > tol:
        return None
    paper = same_paper(a, b)
    if paper is False:
        return None
    cond = _condition(a, b, st)
    if cond == "differs":
        return None
    numbers = {"grain_size": [ga, gb], outcome: [ya, yb], "relative_difference": relative_difference(ya, yb)}
    within = numbers["relative_difference"] <= tol
    if paper is True and cond == "same":
        return ("exact" if within else "conflict"), numbers
    return ("possible", numbers) if within else None


def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any], m: Matching | None = None) -> list[Flag]:
    m = m or matching(plan)
    by_alloy: dict[str, list[Mapping]] = defaultdict(list)
    for r in records:
        comp = _value(r, "composition", m.statuses)
        if isinstance(comp, Mapping) and comp:
            by_alloy[same_alloy_key(dict(comp), m.decimals)].append(r)
    links: dict[tuple[int, int], tuple[str, dict]] = {}
    for group in by_alloy.values():
        for a, b in combinations(sorted(group, key=lambda r: r["id"]), 2):
            if a["source"] != b["source"]:
                link = _link(a, b, plan, m)
                if link:
                    links[(a["id"], b["id"])] = link
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for a, b in links:
        parent[find(a)] = find(b)
    components: dict[int, list[int]] = defaultdict(list)
    for x in list(parent):
        components[find(x)].append(x)
    source = {r["id"]: r["source"] for r in records}
    flags = []
    for ids in sorted(sorted(c) for c in components.values()):
        pairs = {(a, b): links[(a, b)] for a, b in combinations(ids, 2) if (a, b) in links}
        compared = {f"{a}-{b}": {"link": kind, **numbers} for (a, b), (kind, numbers) in pairs.items()}
        sources = [source[i] for i in ids]
        kinds = {kind for kind, _ in pairs.values()}
        if len(set(sources)) < len(sources) or len(pairs) < len(ids) * (len(ids) - 1) // 2:
            flags.append(Flag("possible_duplicate", "several candidates", ids, compared))
            # Review finding 4: a definite conflict inside an ambiguous group is kept as its own
            # flag, so that a set that counts the group separately still excludes it.
            conflicting = sorted({i for (a, b), (kind, _) in pairs.items() if kind == "conflict" for i in (a, b)})
            if conflicting:
                flags.append(Flag("values_disagree", "differ beyond tolerance", conflicting,
                                  {k: v for k, v in compared.items() if v["link"] == "conflict"}))
        elif "conflict" in kinds:
            flags.append(Flag("values_disagree", "differ beyond tolerance", ids, compared))
        else:
            identical = all(n["relative_difference"] == 0 and n["grain_size"][0] == n["grain_size"][1]
                            for _, n in pairs.values())
            category = "identical values" if identical else "within tolerance"
            flags.append(Flag("possible_duplicate" if "possible" in kinds else "exact_duplicate", category, ids,
                              compared))
    return flags


def raise_flags(plan: Mapping[str, Any], records: list[Mapping]) -> list[Flag]:
    """Every flag for the run's records under the locked plan, in a fixed order."""
    return invalid_values(records) + duplicate_groups(records, plan)


def set_flags(plan: Mapping[str, Any], records: list[Mapping]) -> dict[str, list[Flag]]:
    """For each sensitivity set whose matching settings differ from the primary set's, the
    duplicate, conflict and ambiguity flags under its own settings (step 6 review, finding 2).
    Invalid values do not depend on matching; the set uses the primary set's."""
    primary = matching(plan)
    out = {}
    for key in plan["sensitivity_analyses"]:
        m = matching(plan, key)
        if m != primary:
            out[key] = duplicate_groups(records, plan, m)
    return out
