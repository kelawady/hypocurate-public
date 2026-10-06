"""Eligibility decisions under the locked plan (PRD 5.3; build step 6). Pure functions.

Input: exactly what Inclusion's access object returns (`record_conditions`, `flags_kind`,
the projected `plan`, each sensitivity set's own matching flags): no outcome value. This module
imports nothing from the domain profile.

**Settings and fixed policies** (step 6 review; owner, 2026-10-06). The plan's settings (scope,
exclusion rules, eligibility rules within the fixed choices, `rules`, sufficiency) are read from
the locked plan only, never from the domain profile. These are **fixed policies in code**, the
same for every plan: which statuses carry a value; what counts as physically invalid (tensile
strength below yield strength, grain size of zero or less); which test conditions are compared
(test type and temperature); how a paper is identified (the DOI's derived key; a source grouped
by dataset cites itself); the room-temperature band's name; the order of the rules; the
ambiguity rule; the fixed rules for the primary set (register 'primary_set_invariants'); the
structure of the survivor rule and its stable tie-breaker; the change each sensitivity key
applies; and the code roles' field lists. Changing one is a code change with its register entry
('fixed_policies_in_code').

Each record gets one rule code, the first that applies (owner, 2026-10-05):

1. `model_recalled`: the record is model-recalled.
2. `invalid_value`: a flag the plan maps to `invalid_value` (physically impossible).
3. `out_of_scope`: a known value outside the scope (test type; reported temperature outside
   the room-temperature range, or a band outside the scope; microstructure, or phase class).
4. `missing_value`: composition, predictor or outcome without an accepted value.
5. `group_unknown`: the record has no group under the set's grouping (a paper-grouped record
   without a DOI; a batch-grouped record without a batch). No group is invented (owner,
   2026-10-06, step 7b; register 'records_without_group'). After rules 1-4, so that a record out of
   scope or missing a value keeps that more basic reason; before identity, so that a record without
   a group is never chosen as a survivor and never pushes out its grouped twin; before the
   grain-size count, so that alloys are counted on records that can be analysed.
6. `scope_not_confirmed`: a scope value missing, or held with a status the plan does not accept.
7. `excluded_by_rule`: an exclusion rule from the menu (for example grain size below 0.1 µm).
8. Identity, among records that passed 1–7, per flag the plan maps:
   `identity_unresolved` (every record of an ambiguous group), `conflict_unresolved` (every
   record of a group whose values disagree), `duplicate_counted_once` (every record but the
   survivor of an exact or possible duplicate group).
9. `single_grain_size`: the alloy (same-alloy rule) has fewer than the plan's distinct grain
   sizes among records that passed 1–8, so duplicates are resolved before grain sizes are
   counted (owner, 2026-10-05).
10. `in_scope`: eligible.

**Sensitivity sets** (register 'sensitivity_one_change'): each differs from the primary set in
exactly one named respect; every other rule applies unchanged. `SENSITIVITY_CHANGES` lists
the change of each key. The variation each key applies is fixed by the key (its name in the
vocabulary), not by a number in the plan. The set 'without_most_influential_paper' (step 7b) is the
primary set minus every record of the paper holding the largest share of slope information
(`most_influential`); its records get `most_influential_paper` in that set only.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping

from hypocurate.pipeline import statistics
from hypocurate.sources.normalize import same_alloy_key

PRIMARY = "primary"
# Rule 5 (owner, 2026-10-06; register 'records_without_group').
NO_GROUP_RULE = "group_unknown"
# The sensitivity set without the most influential paper, and the rule its removed records get in
# that set (owner, 2026-10-06; register 'most_influential_paper_set').
INFLUENCE_KEY = "without_most_influential_paper"
INFLUENCE_RULE = "most_influential_paper"
# Sprint 1 supports one model (CLAUDE.md rule 6): its outcome is yield strength. Plan validation
# refuses any other (re-check finding 2b; register 'supported_outcomes').
SUPPORTED_OUTCOMES = ("yield_strength",)
FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_counted_once")

# Fixed rules, not plan defaults (owner, 2026-10-06; register 'primary_set_invariants'): what each
# flag means for the primary set. Every plan has exactly these eligibility-rule entries (flag kind,
# category), with a rule from the allowed choices; validation refuses anything else, and so does
# `settings` for a plan that bypassed validation. No plan, including one a model writes, can count
# an exact duplicate twice, admit any record connected to a definite conflict, an invalid value or
# an unresolved-identity group. Conflicts are not a plan choice (third confirmation, owner
# 2026-10-06): no record of a conflict-connected group enters primary; a survivor's value is
# counted only in the sensitivity set 'conflicts_survivor_value' (`conflict_survivor_allowed`).
# The one plan choice: a possible duplicate is counted once (the default) or both records are
# counted.
FLAG_RULE_CHOICES = {
    ("invalid_value", None): ("invalid_value",),
    ("exact_duplicate", None): ("duplicate_counted_once",),
    ("values_disagree", None): ("conflict_unresolved",),
    ("possible_duplicate", "several candidates"): ("identity_unresolved",),
    ("possible_duplicate", None): ("duplicate_counted_once", "in_scope"),
}


def ordered_rules(eligibility_rules) -> tuple:
    """A plan's eligibility rules in lookup order: entries naming a category first, then the
    others, each group in the plan's order. `lookup` takes the first that matches."""
    entries = [(e.get("flag_kind"), e.get("category"), e.get("rule")) for e in eligibility_rules]
    return tuple(sorted(entries, key=lambda t: t[1] is None))


def lookup(rules: tuple, kind: str, category: str | None) -> str | None:
    """The rule a flag of this kind and category gets: the first matching entry."""
    for k, c, rule in rules:
        if k == kind and (c is None or c == category):
            return rule
    return None


def fixed_rule_problems(eligibility_rules) -> list[str]:
    """What breaks the fixed rules in a plan's eligibility rules (empty if nothing). Duplicate
    entries are refused, and each flag kind and category is resolved exactly as `lookup` resolves
    it when the rules are applied (re-check finding 3)."""
    from hypocurate.access.vocabulary import FLAG_CATEGORIES
    keys = [(e.get("flag_kind"), e.get("category")) for e in eligibility_rules]
    name = lambda k: f"{k[0]}{'/' + k[1] if k[1] else ''}"
    problems = [f"{name(k)}: more than one entry" for k in sorted(set(keys), key=str) if keys.count(k) > 1]
    problems += [f"{name(k)}: missing" for k in FLAG_RULE_CHOICES if k not in keys]
    problems += [f"{name(k)}: not a flag the plan sets a rule for" for k in sorted(set(keys), key=str)
                 if k not in FLAG_RULE_CHOICES]
    rules = ordered_rules(eligibility_rules)
    for kind in sorted({k for k, _ in FLAG_RULE_CHOICES}):
        for category in sorted(FLAG_CATEGORIES):
            allowed = FLAG_RULE_CHOICES.get((kind, category), FLAG_RULE_CHOICES.get((kind, None), ()))
            got = lookup(rules, kind, category)
            if got not in allowed:
                problems.append(f"{kind} ({category}): resolves to {got} (allowed: {', '.join(allowed)})")
    return sorted(set(problems))

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
    INFLUENCE_KEY: "the records of the most influential paper (the largest share of slope information, from "
                   "grain sizes, alloys and groups only) are removed",
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
    conflict_survivor: bool = False  # only in 'conflicts_survivor_value' (`conflict_survivor_allowed`)


def conflict_survivor_allowed(key: str) -> bool:
    """The one place a conflict-connected group may keep a survivor (third confirmation, owner
    2026-10-06): the sensitivity set 'conflicts_survivor_value', never primary, whatever the plan."""
    return key == "conflicts_survivor_value"


def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
    """The settings of set `key` under the locked plan's content."""
    r, s, v = plan["rules"], plan["scope"], plan["variables"]
    problems = fixed_rule_problems(plan["eligibility_rules"])
    if problems:
        raise ValueError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
    flag_rules = ordered_rules(plan["eligibility_rules"])
    base = Settings(
        outcome=v["outcome"]["field"], predictor=v["predictor"]["field"], test_types=frozenset(s["test_type"]),
        bands=frozenset(s["temperature_band"]), phase_classes=frozenset(s["phase_class"]),
        single_phase=r["single_phase"] == "required", rt_min=r["room_temperature_min"],
        rt_max=r["room_temperature_max"], statuses=frozenset(r["accepted_value_statuses"]),
        exclusions=tuple(tuple(sorted(e.items(), key=lambda kv: kv[0])) for e in plan["exclusion_rules"]),
        flag_rules=flag_rules, decimals=r["same_alloy_decimals"], min_grain_sizes=r["min_grain_sizes"],
        survivor_order=tuple(r["survivor_source_order"]),
        grouping={g["source"]: g["unit"] for g in r["grouping"]},
        conflict_survivor=conflict_survivor_allowed(key))
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
        return base  # its one change is `conflict_survivor`, set above
    if key == INFLUENCE_KEY:
        return base  # its one change is applied to the primary set's decisions (`decide`)
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


def has_group(rec: Mapping, st: Settings) -> bool:
    """Rule 5: does the record have a group under the set's grouping (`group`)?"""
    return group(rec, st) is not None


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
    return lookup(st.flag_rules, flag["kind"], flag["category"])


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
    for r in records.values():  # 3-7
        if r["id"] in rules:
            continue
        sc = scope(r, st)
        if sc == "out":
            rules[r["id"]] = "out_of_scope"
        elif _missing(r, st):
            rules[r["id"]] = "missing_value"
        elif not has_group(r, st):
            rules[r["id"]] = NO_GROUP_RULE
        elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
            rules[r["id"]] = "scope_not_confirmed"
        elif _excluded(r, st):
            rules[r["id"]] = "excluded_by_rule"
    _identity(records, flags, rules, st)  # 8
    sizes: dict[str, set] = defaultdict(set)  # 9
    for r in records.values():
        if r["id"] not in rules:
            sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
    for r in records.values():
        if r["id"] not in rules:
            rules[r["id"]] = ("single_grain_size" if len(sizes[alloy(r, st.decimals)]) < st.min_grain_sizes
                              else "in_scope")
    if key == INFLUENCE_KEY:  # the set's one change, on the primary decisions above
        for i in most_influential(plan, records, members(rules))["records"]:
            rules[i] = INFLUENCE_RULE
    return rules


def most_influential(plan: Mapping[str, Any], records: Mapping[int, Mapping], ids: Iterable[int]) -> dict:
    """The paper (the group under the primary grouping) holding the largest share of slope
    information among the primary set's records `ids` (owner, 2026-10-06; register
    'most_influential_paper_set'). I_g comes from `statistics.slope_information`: grain sizes, alloys
    (the plan's same-alloy rule) and groups only; the records carry no outcome value. Shares within
    `statistics.RELATIVE_ZERO` of the largest are tied; a tie is broken by each tied paper's earliest
    record under (the plan's survivor source order, the lowest row in the source file, the stable
    identity: source-version fingerprint, origin key, item index), never a database id or an order.
    Without any slope information nothing is removed (reason 'no_slope_information')."""
    st = settings(plan)
    # A primary record without a group exists only if rule 5 was bypassed; it is no paper's, and the
    # freeze's invariant (7) refuses such a primary set.
    chosen = [records[i] for i in ids if group(records[i], st) is not None]
    items = [(f"{r['version_fingerprint']}|{r['origin']}|{r['item_index']}", alloy(r, st.decimals), group(r, st),
              r["values"][st.predictor]) for r in chosen]
    info = statistics.slope_information(items, plan["variables"]["predictor"]["transformation"])
    total = sum(info.values())
    if not total > 0:
        return {"group": None, "share": None, "tied": [], "records": [], "n_records": 0, "n_alloys": 0,
                "reason": "no_slope_information"}
    top = max(info.values())
    tied = sorted(g for g, v in info.items() if v >= top - statistics.RELATIVE_ZERO * top)

    def earliest(g: str) -> tuple:
        return min(influence_tie_key(r, st) for r in chosen if group(r, st) == g)

    pick = min(tied, key=earliest)
    removed = sorted(r["id"] for r in chosen if group(r, st) == pick)
    return {"group": pick, "share": info[pick] / total, "tied": tied, "records": removed,
            "n_records": len(removed), "n_alloys": len({alloy(records[i], st.decimals) for i in removed}),
            "reason": None}


def influence_tie_key(rec: Mapping, st: Settings) -> tuple:
    """The tie-break of `most_influential` for one record (owner, 2026-10-06): the plan's survivor
    source order, the row in the source file, then the stable identity."""
    order = st.survivor_order.index(rec["source"]) if rec["source"] in st.survivor_order else len(st.survivor_order)
    return (order, rec["row"] if rec["row"] is not None else math.inf, rec["version_fingerprint"], rec["origin"],
            rec["item_index"])


class MissingSetFlags(ValueError):
    """A sensitivity set needs its own matching flags and the Checks result lacks them."""


def needs_own_flags(plan: Mapping[str, Any], key: str) -> bool:
    """Whether set `key` changes a matching setting (the same-alloy step or the value statuses), so
    that it needs its own duplicate, conflict and ambiguity flags from Checks."""
    if key == PRIMARY:
        return False
    a, b = settings(plan), settings(plan, key)
    return (a.decimals, a.statuses) != (b.decimals, b.statuses)


def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | None,
              plan: Mapping[str, Any] | None = None) -> list[Mapping]:
    """The flags set `key` applies: its own matching flags from Checks where its matching settings
    differ (step 6 review, finding 2), with the primary set's invalid-value flags; else the primary
    set's flags. A required result that is missing is refused, never read as "no flags"
    (re-check finding 1)."""
    if plan is not None and needs_own_flags(plan, key) and (not set_flags or key not in set_flags):
        raise MissingSetFlags(f"the Checks result has no flags for the set {key!r}")
    if not set_flags or key not in set_flags:
        return flags
    own = [{"id": 10 ** 12 + n, **f} for n, f in enumerate(set_flags[key])]
    return [f for f in flags if f["kind"] == "invalid_value"] + own


def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: Iterable[Mapping],
                         marked: bool, *, grouping: Mapping[str, str]) -> list[str]:
    """The result check of the freeze (owner, 2026-10-06; register 'primary_set_invariants'): what
    in the primary set itself breaks an invariant, whatever the plan said. `flags` are the Checks
    flags, including every retained pairwise exact or conflict result (two-record flags inside
    mixed groups), so exact and conflict pairs are checked pair by pair, never through a group's
    label (confirmation, 2026-10-06); identity and validity are independent of the plan's grouping
    and outcome. `records` gives
    each member's kind, source, paper and batch; `marked` is the run's test mark; `grouping` is the
    primary set's grouping (source -> unit), for invariant (7), no record without a group (step 7b,
    owner 2026-10-06), checked with `group_in` itself, not through rule 5. Empty if nothing."""
    from hypocurate.sources.versions import SOURCES
    out = []
    flags = list(flags)
    # At most one record per chain of exact pairs (confirmation round 2), and no record at all of a
    # group linked to a definite conflict (third confirmation, owner 2026-10-06): the groups are
    # formed here from Checks' flags, independently of how Inclusion resolved them.
    exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate"]
    conflicting = {i for f in flags if f["kind"] == "values_disagree" for i in f["records"]}
    for group in components(exact):
        inside = sorted(i for i in group if i in members)
        if len(inside) > 1:
            out.append(f"an exact duplicate counted twice: records {inside}")
    for group in components(exact + [f["records"] for f in flags if f["kind"] == "values_disagree"]):
        inside = sorted(i for i in group if i in members)
        if set(group) & conflicting and inside:
            out.append(f"a record connected to a conflict: records {inside}")
    for f in flags:
        inside = sorted(i for i in f["records"] if i in members)
        if f["kind"] == "invalid_value" and inside:
            out.append(f"an invalid value: records {inside}")
        elif f["kind"] == "possible_duplicate" and f["category"] == "several candidates" and inside:
            out.append(f"a group of unresolved identity: records {inside}")
    recalled = sorted(i for i in members if records[i]["kind"] == "model_recalled")
    if recalled:
        out.append(f"model-recalled records: {recalled}")
    # Its own test of the source definition, so that switching off the earlier guard does not
    # switch off this check.
    constructed = sorted(i for i in members if getattr(SOURCES.get(records[i]["source"]), "constructed", False))
    if constructed and not marked:
        out.append(f"constructed records in a run not marked as a test: {constructed}")
    ungrouped = sorted(i for i in members if group_in(records[i], grouping) is None)
    if ungrouped:
        out.append(f"records without a group: {ungrouped}")
    return out


def components(groups: Iterable[Iterable[int]]) -> list[list[int]]:
    """Connected components of records linked by the given groups (each group links all its
    members): a pure function of the links, whatever their order or the ids' values."""
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for group in groups:
        group = list(group)
        for x in group:
            find(x)
        for a, b in zip(group, group[1:]):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    out: dict[int, list[int]] = defaultdict(list)
    for x in parent:
        out[find(x)].append(x)
    return [sorted(c) for c in out.values()]


def _identity(records: Mapping[int, Mapping], flags: list[Mapping], rules: dict[int, str], st: Settings) -> None:
    """Rule 7 (confirmation round 2, 2026-10-06): no decision depends on record ids, flag ids or
    the order of flags. In this order, each step a whole-group decision:
    1. unresolved identity: every pending record of an ambiguous group;
    2. definite relationships: records linked by a chain of exact-duplicate pairs are one
       measurement, and a definite conflict links its records as well. In a connected group that
       touches a conflict every pending record is `conflict_unresolved`, whatever the plan says
       (third confirmation, owner 2026-10-06); only in 'conflicts_survivor_value'
       (`st.conflict_survivor`) does it keep one survivor. A group of exact duplicates only keeps
       one survivor;
    3. the plan's possible-duplicate choice on what remains: counted once, one survivor per
       connected possible group, or both counted.
    A survivor is chosen by the plan's survivor rule (`survivor_key`), whose last tie-break is the
    source's stable identity (source, origin key, item index)."""
    def pending(ids):
        return [i for i in ids if i in records and i not in rules]

    for f in flags:  # 1
        if flag_rule(f, st) == "identity_unresolved":
            for i in pending(f["records"]):
                rules[i] = "identity_unresolved"
    exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate" and flag_rule(f, st) == "duplicate_counted_once"]
    conflict = [f["records"] for f in flags if f["kind"] == "values_disagree"]  # every one: not a plan choice
    in_conflict = {i for c in conflict for i in c}
    for group in components(exact + conflict):  # 2
        live = pending(group)
        if in_conflict & set(group) and not st.conflict_survivor:
            for i in live:
                rules[i] = "conflict_unresolved"
        elif live:
            survivor = min(live, key=lambda i: survivor_key(records[i], st))
            for i in live:
                if i != survivor:
                    rules[i] = "duplicate_counted_once"
    possible = [f["records"] for f in flags if f["kind"] == "possible_duplicate"
                and flag_rule(f, st) == "duplicate_counted_once"]
    for group in components(possible):  # 3
        live = pending(group)
        if live:
            survivor = min(live, key=lambda i: survivor_key(records[i], st))
            for i in live:
                if i != survivor:
                    rules[i] = "duplicate_counted_once"


def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping],
             set_flags: Mapping[str, list] | None = None) -> dict[str, dict[int, str]]:
    """The primary set and every sensitivity set the plan names, each with its own flags."""
    return {key: decide(plan, records, flags_for(key, flags, set_flags, plan), key)
            for key in (PRIMARY, *plan["sensitivity_analyses"])}


def members(rules: Mapping[int, str]) -> list[int]:
    return sorted(rid for rid, rule in rules.items() if rule == "in_scope")


# --- Counts known at the freeze (structure and predictor only, no outcome) ----------------

def group(rec: Mapping, st: Settings) -> str | None:
    """The record's independent group under the set's grouping (PRD 5.7)."""
    return group_in(rec, st.grouping)


def group_in(rec: Mapping, grouping: Mapping[str, str]) -> str | None:
    """The record's group under a grouping (source -> unit), or None: no group is invented."""
    unit = grouping.get(rec["source"])
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
