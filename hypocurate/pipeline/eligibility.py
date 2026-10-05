"""Eligibility decisions under the locked plan (PRD 5.3; build step 6). Pure functions.

Input: exactly what Inclusion's access object returns (`record_conditions`, `flags_kind`,
the projected `plan`): no outcome value. **Every setting is read from the locked plan**
(owner, 2026-10-05); this module imports nothing from the domain profile.

Each record gets one rule code, the first that applies (owner, 2026-10-05):

1. `model_recalled`: the record is model-recalled.
2. `invalid_value`: a flag the plan maps to `invalid_value` (physically impossible).
3. `out_of_scope`: a known value outside the scope (test type; reported temperature outside
   the room-temperature range, or a band outside the scope; microstructure, or phase class).
4. `missing_value`: composition, predictor or outcome without an accepted value.
5. `scope_not_confirmed`: a scope value missing, or held with a status the plan does not accept.
6. `excluded_by_rule`: an exclusion rule from the menu (for example grain size below 0.1 µm).
7. Identity, among records that passed 1–6, per flag the plan maps:
   `identity_unresolved` (every record of an ambiguous group), `conflict_unresolved` (every
   record of a group whose values disagree), `duplicate_counted_once` (every record but the
   survivor of an exact or possible duplicate group).
8. `single_grain_size`: the alloy (same-alloy rule) has fewer than the plan's distinct grain
   sizes among records that passed 1–7, so duplicates are resolved before grain sizes are
   counted (owner, 2026-10-05).
9. `in_scope`: eligible.

**Sensitivity sets** (register 'sensitivity_one_change'): each differs from the primary set in
exactly one named respect; every other rule applies unchanged. `SENSITIVITY_CHANGES` lists
the change of each key. The variation each key applies is fixed by the key (its name in the
vocabulary), not by a number in the plan.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping

from hypocurate.sources.normalize import same_alloy_key

PRIMARY = "primary"
FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_counted_once")

# Fixed rules, not plan defaults (owner, 2026-10-06; register 'primary_set_invariants'): what each
# flag means for the primary set. Every plan has exactly these eligibility-rule entries (flag kind,
# category), with a rule from the allowed choices; validation refuses anything else, and so does
# `settings` for a plan that bypassed validation. No plan, including one a model writes, can count
# an exact duplicate twice, admit both records of a conflict, an invalid value or an unresolved-
# identity group. The only plan choices: a conflict enters with neither record (the default) or
# with the survivor's value counted once; a possible duplicate is counted once (the default) or
# both records are counted.
FLAG_RULE_CHOICES = {
    ("invalid_value", None): ("invalid_value",),
    ("exact_duplicate", None): ("duplicate_counted_once",),
    ("values_disagree", None): ("conflict_unresolved", "duplicate_counted_once"),
    ("possible_duplicate", "several candidates"): ("identity_unresolved",),
    ("possible_duplicate", None): ("duplicate_counted_once", "in_scope"),
}


def fixed_rule_problems(eligibility_rules) -> list[str]:
    """What breaks the fixed rules in a plan's eligibility rules (empty if nothing)."""
    got = {(e.get("flag_kind"), e.get("category")): e.get("rule") for e in eligibility_rules}
    problems = [f"{kind}{'/' + cat if cat else ''}: missing" for kind, cat in FLAG_RULE_CHOICES
                if (kind, cat) not in got]
    for key, rule in got.items():
        allowed = FLAG_RULE_CHOICES.get(key)
        if allowed is None:
            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: not a flag the plan sets a rule for")
        elif rule not in allowed:
            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: {rule} (allowed: {', '.join(allowed)})")
    return problems

# The one change of each sensitivity set (owner, 2026-10-05).
SENSITIVITY_CHANGES = {
    "no_exclusions": "the menu exclusion rules are dropped; the scope is kept",
    "tension_and_compression": "permitted test types: tension and compression",
    "six_batches_as_groups": "Texas A&M grouped by its six batches (the same records as primary)",
    "same_alloy_1_at_pct": "the same-alloy rule rounds to 1 at.%",
    "source_only_assignments": "accepted value statuses: converted and assigned from source only",
    "scope_not_confirmed_included": "records whose scope cannot be confirmed are treated as in scope",
    "possible_duplicates_separate": "records of unresolved or possible duplicate groups count as separate "
                                    "measurements",
    "conflicts_survivor_value": "conflict groups are counted once by the survivor rule",
}


@dataclass(frozen=True)
class Settings:
    """The plan's settings as one set applies them."""
    outcome: str
    predictor: str
    test_types: frozenset
    bands: frozenset
    phase_classes: frozenset
    single_phase: bool
    rt_min: float
    rt_max: float
    statuses: frozenset
    exclusions: tuple
    flag_rules: tuple  # ((kind, category or None, rule), ...), most specific first
    decimals: int
    min_grain_sizes: int
    survivor_order: tuple
    grouping: Mapping[str, str]
    scope_unconfirmed_ok: bool = False


def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
    """The settings of set `key` under the locked plan's content."""
    r, s, v = plan["rules"], plan["scope"], plan["variables"]
    problems = fixed_rule_problems(plan["eligibility_rules"])
    if problems:
        raise ValueError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
    flag_rules = tuple(sorted(((e["flag_kind"], e.get("category"), e["rule"]) for e in plan["eligibility_rules"]),
                              key=lambda t: t[1] is None))
    base = Settings(
        outcome=v["outcome"]["field"], predictor=v["predictor"]["field"], test_types=frozenset(s["test_type"]),
        bands=frozenset(s["temperature_band"]), phase_classes=frozenset(s["phase_class"]),
        single_phase=r["single_phase"] == "required", rt_min=r["room_temperature_min"],
        rt_max=r["room_temperature_max"], statuses=frozenset(r["accepted_value_statuses"]),
        exclusions=tuple(tuple(sorted(e.items(), key=lambda kv: kv[0])) for e in plan["exclusion_rules"]),
        flag_rules=flag_rules, decimals=r["same_alloy_decimals"], min_grain_sizes=r["min_grain_sizes"],
        survivor_order=tuple(r["survivor_source_order"]),
        grouping={g["source"]: g["unit"] for g in r["grouping"]})
    if key == PRIMARY:
        return base
    if key not in plan["sensitivity_analyses"]:
        raise KeyError(f"the locked plan names no analysis {key!r}")
    if key == "no_exclusions":
        return replace(base, exclusions=())
    if key == "tension_and_compression":
        return replace(base, test_types=frozenset({"tension", "compression"}))
    if key == "six_batches_as_groups":
        return replace(base, grouping={**base.grouping, "tamu_fcc": "batch"})
    if key == "same_alloy_1_at_pct":
        return replace(base, decimals=0)
    if key == "source_only_assignments":
        return replace(base, statuses=base.statuses - {"assigned_by_decision"})
    if key == "scope_not_confirmed_included":
        return replace(base, scope_unconfirmed_ok=True)
    if key == "possible_duplicates_separate":
        return replace(base, flag_rules=tuple((k, c, "in_scope" if k == "possible_duplicate" else rule)
                                              for k, c, rule in base.flag_rules))
    if key == "conflicts_survivor_value":
        return replace(base, flag_rules=tuple((k, c, "duplicate_counted_once" if rule == "conflict_unresolved"
                                               else rule) for k, c, rule in base.flag_rules))
    raise KeyError(f"no change is defined for the analysis {key!r}")


# --- One record --------------------------------------------------------------------------

def _known(rec: Mapping, field: str, st: Settings) -> bool:
    return rec["status"].get(field) in st.statuses


def scope(rec: Mapping, st: Settings) -> str:
    """'in', 'out' or 'unconfirmed' for one record's scope."""
    verdicts = []
    # Test type.
    if _known(rec, "test_type", st):
        verdicts.append(rec["categories"]["test_type"] in st.test_types)
    else:
        verdicts.append(None)
    # Temperature: a reported temperature decides; otherwise the band.
    t = rec["values"].get("test_temperature")
    if _known(rec, "test_temperature", st) and t is not None:
        verdicts.append("room temperature" in st.bands and st.rt_min <= t <= st.rt_max)
    elif _known(rec, "test_temperature_band", st):
        verdicts.append(rec["categories"]["test_temperature_band"] in st.bands)
    else:
        verdicts.append(None)
    # Single phase: the microstructure is exactly one of the scope's phase classes.
    field = "microstructure" if st.single_phase else "phase_class"
    if _known(rec, field, st):
        verdicts.append(rec["categories"][field] in st.phase_classes)
    else:
        verdicts.append(None)
    if any(v is False for v in verdicts):
        return "out"
    return "unconfirmed" if any(v is None for v in verdicts) else "in"


def _missing(rec: Mapping, st: Settings) -> bool:
    if rec["composition"] is None or not _known(rec, "composition", st):
        return True
    return not (_known(rec, st.predictor, st) and _known(rec, st.outcome, st)) or \
        rec["values"].get(st.predictor) is None


def _excluded(rec: Mapping, st: Settings) -> bool:
    for items in st.exclusions:
        e = dict(items)
        lo, hi = e.get("min", -math.inf), e.get("max", math.inf)
        if e["rule"] == "grain_size_range":
            g = rec["values"].get("grain_size")
            if g is not None and not lo <= g <= hi:
                return True
        elif e["rule"] == "temperature_range":
            t = rec["values"].get("test_temperature")
            if t is not None and _known(rec, "test_temperature", st) and not lo <= t <= hi:
                return True
        elif e["rule"] == "test_type":
            if _known(rec, "test_type", st) and rec["categories"]["test_type"] not in e["values"]:
                return True
        elif e["rule"] == "phase":
            if _known(rec, "phase_class", st) and rec["categories"]["phase_class"] not in e["values"]:
                return True
    return False


def alloy(rec: Mapping, decimals: int) -> str | None:
    return same_alloy_key(rec["composition"], decimals) if rec["composition"] else None


def flag_rule(flag: Mapping, st: Settings) -> str | None:
    for kind, category, rule in st.flag_rules:
        if kind == flag["kind"] and (category is None or category == flag["category"]):
            return rule
    return None


def survivor_key(rec: Mapping, st: Settings) -> tuple:
    """Register 'duplicate_survivor_rule': 1) the record that carries the original paper
    reference (DOI); 2) the first source in the plan's order; 3) the lowest row. The final
    tie-breaker is the record's stable identity (source, origin key, item index), never a database
    id (step 6 review, finding 3); the lock refuses a plan whose order leaves out a chosen source."""
    order = st.survivor_order.index(rec["source"]) if rec["source"] in st.survivor_order else len(st.survivor_order)
    return (0 if rec["has_doi"] else 1, order, rec["row"] if rec["row"] is not None else math.inf,
            rec["source"], rec["origin"], rec["item_index"])


# --- A whole set ---------------------------------------------------------------------------

def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[Mapping],
           key: str = PRIMARY) -> dict[int, str]:
    """{record id: rule code} for every record, for set `key` (primary or a sensitivity set)."""
    st = settings(plan, key)
    records = {r["id"]: r for r in records}
    flags = list(flags)
    rules: dict[int, str] = {}
    for r in records.values():  # 1
        if r["kind"] == "model_recalled":
            rules[r["id"]] = "model_recalled"
    for f in flags:  # 2
        if flag_rule(f, st) == "invalid_value":
            for rid in f["records"]:
                rules.setdefault(rid, "invalid_value")
    for r in records.values():  # 3-6
        if r["id"] in rules:
            continue
        sc = scope(r, st)
        if sc == "out":
            rules[r["id"]] = "out_of_scope"
        elif _missing(r, st):
            rules[r["id"]] = "missing_value"
        elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
            rules[r["id"]] = "scope_not_confirmed"
        elif _excluded(r, st):
            rules[r["id"]] = "excluded_by_rule"
    for f in flags:  # 7
        rule = flag_rule(f, st)
        members = [rid for rid in f["records"] if rid in records and rid not in rules]
        if rule in ("identity_unresolved", "conflict_unresolved"):
            for rid in members:
                rules[rid] = rule
        elif rule == "duplicate_counted_once" and members:
            survivor = min(members, key=lambda rid: survivor_key(records[rid], st))
            for rid in members:
                if rid != survivor:
                    rules[rid] = "duplicate_counted_once"
    sizes: dict[str, set] = defaultdict(set)  # 8
    for r in records.values():
        if r["id"] not in rules:
            sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
    for r in records.values():
        if r["id"] not in rules:
            rules[r["id"]] = ("single_grain_size" if len(sizes[alloy(r, st.decimals)]) < st.min_grain_sizes
                              else "in_scope")
    return rules


def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping]) -> dict[str, dict[int, str]]:
    """The primary set and every sensitivity set the plan names."""
    return {key: decide(plan, records, flags, key) for key in (PRIMARY, *plan["sensitivity_analyses"])}


def members(rules: Mapping[int, str]) -> list[int]:
    return sorted(rid for rid, rule in rules.items() if rule == "in_scope")


# --- Counts known at the freeze (structure and predictor only, no outcome) ----------------

def group(rec: Mapping, st: Settings) -> str | None:
    """The record's independent group under the set's grouping (PRD 5.7)."""
    unit = st.grouping.get(rec["source"])
    if unit == "paper":
        return f"paper:{rec['paper']}" if rec["paper"] else None
    if unit == "dataset":
        return f"dataset:{rec['source']}"
    if unit == "batch":
        return f"batch:{rec['source']}:{rec['batch']}" if rec["batch"] else None
    return None


def counts(plan: Mapping[str, Any], records: Mapping[int, Mapping], ids: Iterable[int], key: str = PRIMARY) -> dict:
    """Counts of a record set for the fixed minimums and the two validity checks (PRD 5.7,
    5.8): records, alloys, alloys with at least the plan's distinct grain sizes, independent
    groups, residual degrees of freedom. Information at the freeze; step 7 decides."""
    st = settings(plan, key)
    chosen = [records[i] for i in ids]
    sizes: dict[str, set] = defaultdict(set)
    for r in chosen:
        sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
    groups = {group(r, st) for r in chosen}
    n, n_alloys = len(chosen), len(sizes)
    n_groups = len(groups - {None})
    resid = n - n_alloys - 1
    suff = plan["sufficiency"]
    out = {"n_records": n, "n_alloys": n_alloys,
           "n_alloys_two_grain_sizes": sum(len(v) >= st.min_grain_sizes for v in sizes.values()),
           "n_groups": n_groups, "n_records_without_group": sum(group(r, st) is None for r in chosen),
           "resid_df": resid}
    out["check1_inputs_met"] = out["n_alloys_two_grain_sizes"] >= 1
    out["check2_inputs_met"] = out["check1_inputs_met"] and resid >= 1 and n_groups >= 2
    out["minimums"] = {"records": n >= suff["min_records"],
                       "alloys": out["n_alloys_two_grain_sizes"] >= suff["min_alloys"],
                       "groups": n_groups >= suff["min_groups"], "resid_df": resid >= suff["min_resid_df"]}
    out["minimums_met"] = all(out["minimums"].values())
    return out
