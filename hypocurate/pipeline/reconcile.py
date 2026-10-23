"""The Reconciler (Sprint 2 pilot, PRD v1.2 R5; owner, 2026-10-23: per document, before the runs, a deviation from
the PRD's wording 'in the run' that matches Design 3.9; register 'pilot_reconciler_placement').

One document invocation (role 'reconciler') on the parsed document of an S0. It reads, through the access layer,
the parsed document, that S0's candidates and the compilation's (MPEA's) records for the same paper, and proposes
mappings with quotes: an alias to a composition, a column to a field, condition text to a category, or 'same
observation' as a compilation record. Code then applies and checks each proposal with Sprint 1's normalizers and
vocabularies, unchanged (`applied`), keeps the original as written (`subject`), and records it as a mapping in state
'proposed' (rule 'reconciler'), or 'unresolved' (rule 'reconciler-check') when code's check fails, with the reason.
The owner accepts, rejects or corrects each one on the review sheet (`pipeline.review_sheet`). Nothing here ever
writes to S0; its events are S1's."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.access.dispatch import bind_invocation
from hypocurate.access.vocabulary import PHASE_CLASSES, TEMPERATURE_BANDS, TEST_TYPES
from hypocurate.db.models import MAPPING_KINDS, VALUE_FIELDS
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline import profile
from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.agents.interface import call_agent
from hypocurate.pipeline.agents.settings import ensure_setting, reconciler_variant, recorded
from hypocurate.pipeline.extraction.model_extractor import parse_json, render_document
from hypocurate.scoring.score import quantity
from hypocurate.sources.normalize import formula_to_atomic_percent, same_alloy_key

FIELDS = ("parsed_document", "s0_records", "compilation_records")
RULE, CHECK_RULE = "reconciler", "reconciler-check"
CATEGORIES = {"test_type": TEST_TYPES, "test_temperature_band": TEMPERATURE_BANDS, "phase": PHASE_CLASSES}
TOLERANCE = Decimal(str(profile.DUPLICATE_TOLERANCE))
MAPPING_VERSION = "reconcile-v2"  # v2 (2026-10-23): units converted in the same-observation check; v1 compared the first number as written  # the prompt version and this module's checks
NO_KEY = "(none given)"  # a same-observation proposal without a key: stored, and unresolved by code's check


def signature(instruction: str):
    _, dspy = libraries.load()

    class ReconcileSignature(dspy.Signature):
        document: str = dspy.InputField(desc="The paper: text blocks and table rows, each with its page and indexes.")
        observations: str = dspy.InputField(desc="The observations read from the paper, as JSON (item_index, values).")
        compilation: str = dspy.InputField(desc="The compilation's records for this paper, as JSON (key, values).")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        mappings: str = dspy.OutputField(desc="One JSON object {\"mappings\": [...]}.")
    return ReconcileSignature.with_instructions(instruction)


def check_answer(outputs: Mapping[str, str]) -> str | None:
    data = parse_json(outputs["mappings"])
    ok = isinstance(data, dict) and isinstance(data.get("mappings"), list) and all(
        isinstance(m, dict) and m.get("kind") in MAPPING_KINDS and str(m.get("subject") or "").strip()
        for m in data["mappings"])
    check_answer.last_reason = None if ok else ("the answer is not one JSON object with a 'mappings' list whose "
                                                "entries name a known kind and a subject")
    check_answer.last_problems = [] if ok else [check_answer.last_reason]
    return None if ok else "malformed"


check_answer.last_reason, check_answer.last_problems = None, []


def _rel(a, b) -> Decimal | None:
    if a is None or b is None:
        return None
    a, b = Decimal(str(a)), Decimal(str(b))
    small = min(abs(a), abs(b))
    return abs(a - b) / small if small else None


def apply(m: Mapping[str, Any], observations: Mapping[int, Mapping], compilation: Mapping[str, Mapping]) -> dict:
    """What code makes of one proposal with Sprint 1's normalizers and vocabularies: {'ok': bool, ...}."""
    kind, proposed = m["kind"], m.get("proposed") or {}
    if m.get("observation") is not None and m["observation"] not in observations:
        return {"ok": False, "reason": f"no observation {m['observation']} in the S0"}
    if kind == "alias_to_composition":
        comp, why = formula_to_atomic_percent(str(proposed.get("composition") or "").replace(" ", ""))
        return {"ok": True, "same_alloy_key": same_alloy_key(comp)} if comp else {"ok": False, "reason": why}
    if kind == "condition_to_category":
        f, c = proposed.get("field"), proposed.get("category")
        if f not in CATEGORIES or c not in CATEGORIES[f]:
            return {"ok": False, "reason": f"category {c!r} is not in the vocabulary of {f!r}"}
        return {"ok": True, "field": f, "category": c}
    if kind == "column_to_field":
        f = proposed.get("field")
        return {"ok": True, "field": f} if f in VALUE_FIELDS else {"ok": False, "reason": f"unknown field {f!r}"}
    key = m.get("compilation_key")
    if key not in compilation:
        return {"ok": False, "reason": f"no compilation record {key!r} for this paper"}
    obs = observations.get(m.get("observation"))
    if obs is None:
        return {"ok": False, "reason": "a same-observation link names an observation"}
    rec = compilation[key]
    values = {v["field"]: v for v in obs["values"]}
    out = {"ok": True}
    for f, ck in (("grain_size", "grain_size_um"), ("yield_strength", "yield_strength_mpa")):
        # Converted to the compilation's units with the scorer's conversions (µm, MPa) before comparing (review finding,
        # 2026-10-23: nm was compared as µm). A range, figure-only or unknown unit is reported as not compared.
        v = values.get(f) or {}
        q = quantity(f, v.get("text"), v.get("unit"))
        d = _rel(q.low, rec.get(ck)) if q.kind == "number" and q.unit_known else None
        out[f"{f}_relative_difference"] = None if d is None else f"{d:.4f}"
        out[f"{f}_within_tolerance"] = None if d is None else d <= TOLERANCE
    return out


@dataclass
class ReconcileRun:
    output_id: int
    invocation: int | None = None
    mappings: int = 0
    unresolved: int = 0
    failure: str | None = None
    cost: Decimal = Decimal("0")
    by_kind: dict = field(default_factory=dict)


def reconcile(engine: Engine, output_id: int, client_options: Mapping[str, Any] | None = None) -> ReconcileRun:
    """One Reconciler call on the S0 of `output_id`; its mappings stored with their states (S1 events)."""
    run = ReconcileRun(output_id)
    with engine.connect() as conn:
        parse_id = conn.execute(text("SELECT document_parse_id FROM extraction_output x JOIN evidence_snapshot s ON "
                                     "s.extraction_output_id = x.id AND s.name = 'S0' WHERE x.id = :x"),
                                dict(x=output_id)).scalar_one()
    setting = ensure_setting(engine, "reconciler", reconciler_variant())

    def invoke(conn: Connection):
        inv = conn.execute(text("INSERT INTO agent_invocation (scope, role, agent_setting_id) VALUES ('document', "
                                "'reconciler', :a) RETURNING id"), dict(a=setting)).scalar_one()
        conn.execute(text("INSERT INTO document_invocation (invocation_id, document_parse_id) VALUES (:i, :p)"),
                     dict(i=inv, p=parse_id))
        return inv
    run.invocation = run_transaction(engine, invoke)
    access = bind_invocation(engine, run.invocation)
    data = {f: access.get(f) for f in FIELDS}
    if data["s0_records"]["extraction_output_id"] != output_id:
        raise ValueError("the newest S0 on this parse is not the one asked for")
    s = recorded(engine, run.invocation)
    result = call_agent(engine, run.invocation, signature(s["instruction"]),
                        {"document": render_document(data["parsed_document"]),
                         "observations": json.dumps(data["s0_records"]["observations"], ensure_ascii=False, default=str),
                         "compilation": json.dumps(data["compilation_records"], ensure_ascii=False, default=str)},
                        model=s["model"], max_tokens=s["limits"]["max_tokens"],
                        max_output_chars=s["limits"]["max_output_chars"],
                        lm_options={"reasoning_effort": s["settings"]["reasoning_effort"]},
                        client_options=client_options, check=check_answer)
    run.cost = _spent(engine, run.invocation)
    if result.failure is not None:
        run.failure = result.failure
        return run
    observations = {o["item_index"]: o for o in data["s0_records"]["observations"]}
    compilation = {r["key"]: r for r in data["compilation_records"]}
    proposals = parse_json(result.outputs["mappings"])["mappings"]
    with engine.connect() as conn:
        obs_ids = dict(conn.execute(text("SELECT item_index, id FROM candidate_observation WHERE extraction_output_id = "
                                         ":x"), dict(x=output_id)).all())

    def store(conn: Connection):
        for m in proposals:
            applied = apply(m, observations, compilation)
            mid = conn.execute(text(
                "INSERT INTO reconciler_mapping (extraction_output_id, observation_id, kind, subject, proposed, applied, "
                "quote, compilation_key, mapping_version, invocation_id) VALUES (:x, :o, :k, :s, CAST(:p AS jsonb), "
                "CAST(:a AS jsonb), :q, :c, :v, :i) RETURNING id"),
                dict(x=output_id, o=obs_ids.get(m.get("observation")), k=m["kind"], s=str(m["subject"])[:2000],
                     p=json.dumps(m.get("proposed") or {}, ensure_ascii=False), a=json.dumps(applied, default=str),
                     q=(m.get("quote") or None) and str(m["quote"])[:2000],
                     c=((m.get("compilation_key") or NO_KEY) if m["kind"] == "same_observation" else None),
                     v=MAPPING_VERSION, i=run.invocation)).scalar_one()
            state, rule, reason = ("proposed", RULE, None) if applied["ok"] else ("unresolved", CHECK_RULE,
                                                                                    applied["reason"][:2000])
            conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                              "by_rule, reason) VALUES ('mapping', :m, :x, :s, :r, :why)"),
                         dict(m=mid, x=output_id, s=state, r=rule, why=reason))
            run.mappings += 1
            run.unresolved += state == "unresolved"
            run.by_kind[m["kind"]] = run.by_kind.get(m["kind"], 0) + 1
    run_transaction(engine, store)
    return run


def _spent(engine: Engine, invocation: int) -> Decimal:
    with engine.connect() as conn:
        return Decimal(conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                         "WHERE invocation_id = :i"), dict(i=invocation)).scalar_one())
