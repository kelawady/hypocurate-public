"""The narrowing decision (step 8b; PRD 5.4; owner, Q5, A1, A8, A11, B1; register 'narrowing_decision').

Taken by code, right after the Planner and before any lock, on counts of structure only: the code role
'narrowing' reads `candidate_counts` (per chosen source, from the sealed version recorded at dispatch:
counts per combination of categories, reported temperature and field statuses; never an outcome value).

**Claim parts** are each phase class, each temperature band (with its range) and each test type of the
claim's scope as the Planner stated it (code checked its shape); alloy class is not countable (Q5). A part's
count is the number of records that have a grain size and the plan's outcome at an accepted status, fall in
that part, and fall in the claim's values on the other two dimensions. Temperature is judged as eligibility
rule 3 judges it: a reported temperature decides (room temperature by the profile's range, another band by
the claim's range); otherwise the band; otherwise the record is not counted. Statuses are the profile's
accepted value statuses.

**The decision** (`decide`, pure):
- no part has zero records: `proceed` if the claim is one plan, else `claim_not_one_plan` (A11);
- some part has zero records: the narrower scope is the claim's scope less exactly those parts, built by code
  (owner, 2026-10-07, after live run C: the Planner cannot see which part has no candidate record; a proposal of
  its, if any, is stored as `proposed_narrower` and never used). If a dimension is left empty, nothing is
  testable: `proceed` (the original then ends insufficient) or `claim_not_one_plan`. If the narrower scope
  makes a valid plan: `partly_sufficient`, with the narrower plan (less its hypothesis version) and its
  fingerprint; if not (`narrower_invalid`), the original goes on (`proceed`) or stops (`claim_not_one_plan`).

`run_narrowing` stores the decision as the code stage 'narrowing' (with the counts' fingerprint and each
source's version fingerprint, B1) in one locked transaction at 'before_lock'. A decision of partly
sufficient moves the run to 'narrowed' (A4): no plan can be locked after it (code and database).
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.access.dispatch import bind_code
from hypocurate.access.errors import AccessDenied
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import profile as p
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.agents.planner import Answer, build_plan, one_plan, plan_without_version
from hypocurate.pipeline.writes import Refused, code_stage, log_refusal, write

ROLE = "narrowing"
DIMENSIONS = ("phase_class", "test_type", "temperature_band")
STATUSES = frozenset(p.ACCEPTED_VALUE_STATUSES)
RT_MIN, RT_MAX = p.ROOM_TEMPERATURE_C
# Owner's addition 1 (2026-10-06): how a partly-sufficient original's level 1 is shown.
PARTLY_DECISION = {"state": "partly_sufficient", "outcome": "partly_sufficient",
                   "outcome_wording": "partly sufficient in the sources searched", "verdict": None,
                   "verdict_wording": None, "exploratory": False, "evidence_level": 1,
                   "evidence_level_wording": st.PARTLY_SUFFICIENT_WORDING, "label": None}


def _known(cell: Mapping, field: str) -> bool:
    return cell["status"].get(field) in STATUSES


def usable(cell: Mapping, outcome: str) -> bool:
    """A grain size and the outcome, each at an accepted status."""
    return cell["grain_size_present"] and _known(cell, "grain_size") and _known(cell, outcome)


def matches(cell: Mapping, dimension: str, value: Any) -> bool:
    if dimension in ("phase_class", "test_type"):
        return _known(cell, dimension) and cell["categories"][dimension] == value
    t = cell["test_temperature"]
    if _known(cell, "test_temperature") and t is not None:
        low, high = (RT_MIN, RT_MAX) if value["band"] == plans.ROOM_TEMPERATURE else (value["min"], value["max"])
        return low <= t <= high
    if _known(cell, "test_temperature_band"):
        return cell["categories"]["test_temperature_band"] == value["band"]
    return False


def part_counts(counts: list[Mapping], scope: Mapping, outcome: str) -> list[dict]:
    """Per claim part, the records that count for it (see the module docstring)."""
    cells = [c for source in counts if source.get("readable") for c in source["cells"] if usable(c, outcome)]
    out = []
    for dimension in DIMENSIONS:
        others = [d for d in DIMENSIONS if d != dimension]
        for value in scope[dimension]:
            n = sum(c["n"] for c in cells if matches(c, dimension, value)
                    and all(any(matches(c, d, v) for v in scope[d]) for d in others))
            out.append({"part": dimension, "value": value, "n": n})
    return out


def _same(a: list, b: list) -> bool:
    key = lambda v: plans.canonical(v) if isinstance(v, Mapping) else v  # noqa: E731
    return sorted(map(key, a)) == sorted(map(key, b))


def decide(answer: Answer, counts: list[Mapping], hypothesis_version_id: int, sufficiency_option: str) -> dict:
    """The narrowing decision from the checked answer and the structure counts (pure)."""
    scope = answer.claim_scope
    is_one = one_plan(scope)
    parts = part_counts(counts, scope, answer.outcome)
    zero = [{"part": x["part"], "value": x["value"]} for x in parts if x["n"] == 0]
    fallback = "proceed" if is_one else "claim_not_one_plan"
    out = {"claim_scope": scope, "scope_stated": dict(answer.stated), "part_counts": parts, "zero_parts": zero,
           "narrower_scope": None, "proposed_narrower": answer.narrower}
    if not zero:
        return {**out, "result": fallback, "reason": "no_part_without_records"}
    narrower = {d: [v for v in scope[d] if not any(z["part"] == d and z["value"] == v for z in zero)] for d in DIMENSIONS}
    if not all(narrower.values()):
        return {**out, "result": fallback, "reason": "no_part_with_records"}
    out["narrower_scope"] = narrower
    # Owner, 2026-10-07 (after live run C): code builds the narrower scope from its own counts; the Planner
    # cannot see which part has no candidate record, so a proposal of its, if any, is stored and never used.
    if len(scope["alloy_class"]) != 1 or not one_plan(narrower):
        return {**out, "result": fallback, "reason": "narrower_invalid"}
    try:
        plan = build_plan(hypothesis_version_id, narrower, answer.outcome, answer.exclusion_rules,
                          sufficiency_option, alloy_class=scope["alloy_class"])
    except plans.PlanError:
        return {**out, "result": fallback, "reason": "narrower_invalid"}
    body = plan_without_version(plan)
    return {**out, "result": "partly_sufficient", "reason": "zero_parts_and_narrower_plan",
            "narrower_plan": body, "narrower_plan_fingerprint": plans.fingerprint(body),
            "decision": dict(PARTLY_DECISION)}


def counts_fingerprint(counts: list[Mapping]) -> str:
    return hashlib.sha256(plans.canonical({"candidate_counts": counts}).encode("utf-8")).hexdigest()


def run_narrowing(engine: Engine, run_id: int, answer: Answer) -> dict:
    """Reads the structure counts (code role 'narrowing'), decides and stores the decision."""
    try:
        counts = role_input(bind_code(engine, run_id, ROLE))["candidate_counts"]
    except AccessDenied as denied:
        log_refusal(engine, run_id, ROLE, "run_narrowing", "stage_mismatch", denied.code)
        raise Refused("run_narrowing", "stage_mismatch", denied.code) from None

    def body(conn: Connection, stage: str):
        if stage != "before_lock":
            raise Refused("run_narrowing", "stage_mismatch")
        row = conn.execute(_VERSION, dict(r=run_id)).one()
        decision = decide(answer, counts, row.hypothesis_version_id, row.sufficiency_option)
        output = {**decision, "counts_fingerprint": counts_fingerprint(counts),
                  "sources": [{"source": c["source"], "version_fingerprint": c["version_fingerprint"],
                               "readable": c["readable"]} for c in counts]}
        code_stage(conn, run_id, "narrowing", {"claim_scope": answer.claim_scope}, output)
        return output

    return write(engine, run_id, ROLE, "run_narrowing", body)


_VERSION = text("SELECT r.hypothesis_version_id, hv.sufficiency_option FROM run r JOIN hypothesis_version hv "
                "ON hv.id = r.hypothesis_version_id WHERE r.id = :r")
