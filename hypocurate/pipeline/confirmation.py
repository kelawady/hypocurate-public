"""The confirmation of the question as tested, at the rules lock (build step 9a; owner's answers Q1, Q5 and additions
A1, A2 of 2026-10-08; register 'rules_confirmation').

A run whose plan comes from a model's answer (the Planner's, or a narrower question's, whose exclusion rules and
outcome come from its original's Planner answer) waits before its rules lock until a named person confirms it. A
fixed-plan run of an ordinary question (criterion 14.1a) never waits.

- `plan_to_lock`: the one place that builds the plan a run will lock, from what is stored (the narrower question's
  stored plan after its source-version check, the reference plan, or the Planner's stored answer after a narrowing
  decision to proceed). The orchestrator locks exactly this plan, so the confirmed fingerprint is the locked one.
- `content`: what the person is shown (A2), built by code from stored rows only: the original question, the
  question as tested, what was narrowed and why, each scope part marked stated or assumed, the outcome, the
  exclusion rules, the sufficiency option, the plan's fingerprint, the source versions, and the cost so far.
  `render` turns it into the text shown. Step 10 shows the same content on the screen.
- `source_changes`: A1. A waiting run uses exactly the sealed versions recorded at dispatch (the database refuses
  any change to them). A confirmation is refused when a chosen source has a newer sealed version, or a source was
  registered after dispatch: the narrowing decision would no longer describe the registered sources.
- `confirm`: one run, one named person (no bulk or automatic confirmation in step 9). In one transaction under the
  run's lock: the run is waiting and not yet confirmed, the sources are unchanged, and the content is what was
  shown; then the confirmation is stored with the content and the exact text shown (the database re-checks the
  run, the stages and the source versions, migration 0007).
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.db.models import CONFIRMED_BY_MAX
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import reading
from hypocurate.pipeline.queries import LOCK_TIMEOUT_MS, QueryRefused

WAITING_FOR = "confirmation of the question as tested by a named person"
# Fix round 1, finding 2: the lock that registering a source, sealing a version and a confirmation share (0007 holds
# the same number); `confirm` takes it before its own check, so the check and the insert see the same sources.
SOURCES_LOCK_KEY = 0x68637372636573
SOURCES_CHANGED = ("sources_changed", "{changes} since this run's narrowing; cancel this run and dispatch the query "
                                      "again")
PART_WORDS = {"alloy_class": "alloy class", "phase_class": "phase class", "test_type": "test type",
              "temperature_band": "temperature band"}


class NotLockable(Exception):
    """The stored rows give no plan to lock (a fixed failure code)."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _run(conn: Connection, run_id: int):
    return conn.execute(text(
        "SELECT r.id, r.status, r.fixed_plan, r.queued_at, r.hypothesis_version_id, hv.text, hv.sufficiency_option, "
        "h.number, h.narrower_of_run_id FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
        "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=run_id)).one_or_none()


def needs_confirmation(conn: Connection, run_id: int) -> bool:
    """As the database decides it (0007): a Planner stage (any attempt), or a narrower question's run."""
    return bool(conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'planner') OR EXISTS ("
        "SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h "
        "ON h.id = hv.hypothesis_id WHERE r.id = :r AND h.narrower_of_run_id IS NOT NULL)"), dict(r=run_id)).scalar_one())


def _latest(conn: Connection, run_id: int, stage: str, done: bool = True):
    return conn.execute(text(
        "SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = :s "
        + ("AND status = 'done' " if done else "") + "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).one_or_none()


def _narrower_plan(conn: Connection, run_id: int, original: int, version_id: int) -> dict:
    """The narrower plan stored by the original's narrowing decision, on the versions its counts were taken on."""
    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :o AND stage = 'narrowing' "
                            "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(o=original)).scalar_one_or_none()
    current = sorted(tuple(r) for r in conn.execute(text(
        "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
        "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
    if not isinstance(out, dict) or not isinstance(out.get("narrower_plan"), dict):
        raise NotLockable("narrower_plan_missing")
    stored = sorted((s["source"], s["version_fingerprint"]) for s in out.get("sources") or [])
    if stored != current:  # B1
        raise NotLockable("narrowing_sources_changed")
    body = out["narrower_plan"]
    if plans.fingerprint(body) != out.get("narrower_plan_fingerprint"):
        raise NotLockable("narrower_plan_missing")
    return {"hypothesis_version": version_id, **body}


def _planner_plan(conn: Connection, run_id: int, row) -> dict:
    """The plan from the Planner's stored answer, only after a stored narrowing decision to proceed."""
    from hypocurate.pipeline.agents import planner
    stored, decided = _latest(conn, run_id, "planner"), _latest(conn, run_id, "narrowing")
    if stored is None or not isinstance(stored.output, dict) or decided is None \
            or (decided.output or {}).get("result") != "proceed":
        raise NotLockable("stage_mismatch")
    a = stored.output["answer"]
    return planner.build_plan(row.hypothesis_version_id, a["claim_scope"], a["outcome"], a["exclusion_rules"],
                              row.sufficiency_option)


def reference_plan(row) -> dict:
    plan = plans.reference_plan(row.hypothesis_version_id)
    plan["sufficiency"]["option"] = row.sufficiency_option
    return plan


def plan_to_lock(conn: Connection, run_id: int) -> dict:
    """The plan the run will lock, built from stored rows only, or NotLockable."""
    row = _run(conn, run_id)
    if row.narrower_of_run_id is not None:
        return _narrower_plan(conn, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
    if row.fixed_plan:
        return reference_plan(row)
    return _planner_plan(conn, run_id, row)


def plan_fingerprint(plan: Mapping[str, Any]) -> str:
    """As the rules lock computes it (`checkpoints.lock_rules`)."""
    return plans.fingerprint(plans.validate(plan))


def source_changes(conn: Connection, run_id: int) -> list[str]:
    """A1: each chosen source with a newer sealed version than the run's, and each source registered after
    dispatch, in words; empty when the registered sources are as the run's narrowing saw them."""
    changes = [f"{key} has a newer version" for (key,) in conn.execute(text(
        "SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r "
        "AND rs.source_version_id IS NOT NULL AND EXISTS (SELECT 1 FROM source_version sv WHERE sv.source_id = "
        "s.id AND sv.sealed_at IS NOT NULL AND sv.id > rs.source_version_id) ORDER BY s.key"), dict(r=run_id)).all()]
    changes += [f"{key} was registered" for (key,) in conn.execute(text(
        "SELECT s.key FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = :r "
        "AND rs.source_id = s.id) ORDER BY s.key"), dict(r=run_id)).all()]
    return changes


def _value_words(part: str, value: Any) -> str:
    if part == "temperature_band" and isinstance(value, Mapping):
        return reading.band_words(value)
    if part == "alloy_class":
        return reading.plural(str(value))
    return str(value)


def _scope_parts(scope: Mapping, stated: Mapping | None) -> list[dict]:
    return [{"part": PART_WORDS[part], "values": [_value_words(part, v) for v in scope[part]],
             "marked": None if stated is None else (reading.STATED if stated.get(part) else reading.ASSUMED)}
            for part in ("alloy_class", "phase_class", "test_type", "temperature_band") if part in scope]


def _counts(parts: list | None) -> list[dict]:
    return [{"part": PART_WORDS[x["part"]], "value": _value_words(x["part"], x["value"]), "candidate_records": x["n"]}
            for x in parts or []]


def _money(value) -> str:
    return f"{Decimal(value):.6f}"


def content(conn: Connection, run_id: int) -> dict:
    """What the person confirms (A2), from stored rows only. JSON-safe."""
    row = _run(conn, run_id)
    plan = plan_to_lock(conn, run_id)
    fp = plan_fingerprint(plan)
    planner_stage = narrowing_stage = None
    if row.narrower_of_run_id is not None:
        original = conn.execute(text(
            "SELECT h.number, hv.text FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
            "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :o"), dict(o=row.narrower_of_run_id)).one()
        decision = _latest(conn, row.narrower_of_run_id, "narrowing").output
        tested = reading.from_plan(plan, "narrower")
        stated = decision.get("scope_stated")
        narrowing = {"narrowed": True, "original_query": original.number, "original_question": original.text,
                     "original_scope": _scope_parts(decision["claim_scope"], None),
                     "parts_without_candidate_records": _counts([{**z, "n": 0} for z in decision["zero_parts"]]),
                     "candidate_records": _counts(decision.get("part_counts")),
                     "narrower_scope": _scope_parts(decision["narrower_scope"], None), "reason": decision["reason"]}
        scope = {k: plan["scope"][k] for k in ("alloy_class", "phase_class", "test_type")}
        scope["temperature_band"] = decision["narrower_scope"]["temperature_band"]
    else:
        p, n = _latest(conn, run_id, "planner"), _latest(conn, run_id, "narrowing")
        planner_stage, narrowing_stage = p.id, n.id
        tested = p.output["question_as_tested"]
        stated = n.output.get("scope_stated")
        scope = p.output["answer"]["claim_scope"]
        narrowing = {"narrowed": False, "decision": n.output["result"], "reason": n.output["reason"],
                     "candidate_records": _counts(n.output.get("part_counts"))}
    sources = [dict(r._mapping) for r in conn.execute(text(
        "SELECT s.key AS source, sv.fingerprint AS version_fingerprint, rs.search_status FROM run_source rs "
        "JOIN source s ON s.id = rs.source_id LEFT JOIN source_version sv ON sv.id = rs.source_version_id "
        "WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()]
    cost = conn.execute(text("SELECT calls, cap_cost, reported_cost, unconfirmed_calls FROM model_call_totals_by_run "
                             "WHERE run_id = :r"), dict(r=run_id)).one()
    s = plan["sufficiency"]
    return {
        "run": int(row.id), "query": row.number, "original_question": row.text, "question_as_tested": dict(tested),
        "narrowing": narrowing, "scope_parts": _scope_parts(scope, stated),
        "outcome": plan["variables"]["outcome"]["field"].replace("_", " "),
        "exclusion_rules": [reading.exclusion_words(r) for r in plan.get("exclusion_rules") or []],
        "sufficiency": {"option": s["option"], "min_records": s["min_records"], "min_alloys": s["min_alloys"],
                        "min_groups": s["min_groups"], "min_resid_df": s["min_resid_df"]},
        "plan_fingerprint": fp,
        "sources": [{"source": x["source"], "version_fingerprint": x["version_fingerprint"],
                     "chosen": x["search_status"] != "not_selected"} for x in sources],
        "cost_so_far": {"counted_usd": _money(cost.cap_cost), "reported_usd": _money(cost.reported_cost),
                        "calls": int(cost.calls), "calls_without_reported_cost": int(cost.unconfirmed_calls)},
        "planner_stage_result_id": planner_stage, "narrowing_stage_result_id": narrowing_stage,
    }


def _parts_lines(parts: list[dict]) -> list[str]:
    return [f"  {x['part']}: {', '.join(x['values'])}" + (f" ({x['marked']})" if x["marked"] else "") for x in parts]


ONCE_BY, ONCE_AT = "the person who confirms", "the time of confirming (UTC)"


def label_once_confirmed(label: str, by: str = ONCE_BY, at: str = ONCE_AT) -> str:
    """The label the question as tested carries once confirmed (`reading._confirmed`'s wording)."""
    if label == reading.LABELS["planner"]:
        return reading.CONFIRMED_LABEL.format(by=by, at=at)
    return f"{label}; confirmed by {by} on {at}"


def render(c: Mapping[str, Any]) -> str:
    """The text shown before a person confirms (A2): every item of the content, in words."""
    n = c["narrowing"]
    tested = c["question_as_tested"]
    lines = [f"Run {c['run']} of {c['query']} waits for {WAITING_FOR} before its rules lock.",
             f"Original question: {c['original_question']}",
             f"Question as tested: {tested['text']}",
             # Step 10a (the live-run record's open item 4): the label now, and the label once confirmed.
             f"  Now labelled: {tested['label']}",
             f"  Once confirmed, labelled: {label_once_confirmed(tested['label'])}"]
    if n["narrowed"]:
        lines.append(f"Narrowed: this is the narrower question of {n['original_query']} ({n['original_question']}).")
        lines.append("  Why: code found no candidate record in the sources searched for "
                     + "; ".join(f"{x['part']} {x['value']}" for x in n["parts_without_candidate_records"]) + ".")
        lines.append("  Original scope:")
        lines += ["  " + x for x in _parts_lines(n["original_scope"])]
        lines.append("  Narrower scope:")
        lines += ["  " + x for x in _parts_lines(n["narrower_scope"])]
    else:
        lines.append(f"Narrowed: no (code's narrowing decision: {n['decision']}; {n['reason'].replace('_', ' ')}).")
    lines.append("  Candidate records per claim part (structure only, before any rule): "
                 + ("; ".join(f"{x['part']} {x['value']}: {x['candidate_records']}" for x in n["candidate_records"])
                    or "none counted"))
    lines.append("Scope parts:")
    lines += _parts_lines(c["scope_parts"])
    lines.append(f"Outcome: {c['outcome']} against grain size")
    lines.append("Exclusion rules: " + ("; ".join(c["exclusion_rules"]) if c["exclusion_rules"] else "none"))
    s = c["sufficiency"]
    lines.append(f"Sufficiency option: {s['option'].replace('_', ' ')} (minimums: {s['min_records']} records, "
                 f"{s['min_alloys']} alloys with at least 2 grain sizes, {s['min_groups']} informative groups, "
                 f"{s['min_resid_df']} residual degrees of freedom)")
    lines.append("Sources: " + "; ".join(
        f"{x['source']} version {x['version_fingerprint'][:12]}" if x["chosen"] else f"{x['source']} not chosen"
        for x in c["sources"]))
    k = c["cost_so_far"]
    calls = f"{k['calls']} model call" + ("" if k["calls"] == 1 else "s")
    lines.append(f"Cost so far: ${k['counted_usd']} counted toward the caps (reported ${k['reported_usd']}; "
                 f"{calls}, {k['calls_without_reported_cost']} without a reported cost)")
    lines.append(f"Plan to be locked: fingerprint {c['plan_fingerprint']}")
    return "\n".join(lines)


def content_fingerprint(c: Mapping[str, Any]) -> str:
    """SHA-256 of the content's canonical JSON (keys sorted, no spaces, UTF-8): what a confirmation page sends back so
    that `confirm` can check it is still the content shown (owner's addition 2 of 2026-10-11)."""
    canonical = json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def show(engine: Engine, run_id: int) -> tuple[dict, str]:
    """The content and its text, for a waiting run (what `confirm` prints before recording anything)."""
    with engine.connect() as conn:
        c = content(conn, run_id)
    return c, render(c)


def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None,
            shown_fingerprint: str | None = None) -> dict:
    """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; or
    `shown_fingerprint`: the `content_fingerprint` of the content a page displayed (step 10a, owner's addition 2). The
    confirmation is refused as `content_changed` if either differs from the current content, read in the same
    transaction as the insert. Returns the stored content and text."""
    name = (by or "").strip()
    if not name or len(name) > CONFIRMED_BY_MAX:
        raise QueryRefused("name_required", f"a confirmation names the person (1 to {CONFIRMED_BY_MAX} characters)")

    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        if status != "waiting":
            raise QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = :r)"),
                        dict(r=run_id)).scalar_one():
            raise QueryRefused("already_confirmed", f"run {run_id} is already confirmed")
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=SOURCES_LOCK_KEY))
        changes = source_changes(conn, run_id)
        if changes:
            raise QueryRefused(SOURCES_CHANGED[0], SOURCES_CHANGED[1].format(changes="; ".join(changes)))
        try:
            c = content(conn, run_id)
        except NotLockable as error:
            raise QueryRefused(error.code, "the stored rows give no plan to lock") from None
        if (shown is not None and dict(shown) != c) or \
                (shown_fingerprint is not None and shown_fingerprint != content_fingerprint(c)):
            raise QueryRefused("content_changed", "what was shown is no longer the run's current content; show it "
                                                  "again before confirming")
        words = render(c)
        conn.execute(text(
            "INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
            "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, :c, :s)").bindparams(
            bindparam("c", type_=JSONB)), dict(r=run_id, b=name, fp=c["plan_fingerprint"],
                                                p=c["planner_stage_result_id"], n=c["narrowing_stage_result_id"],
                                                c=c, s=words))
        return {"content": c, "shown": words}

    try:
        return run_transaction(engine, body)
    except QueryRefused:
        raise
    except Exception as error:  # the database's own refusal (0007), in its fixed words
        from sqlalchemy.exc import IntegrityError
        from hypocurate.pipeline.writes import database_message
        if isinstance(error, IntegrityError):
            raise QueryRefused("rejected_by_database", database_message(error)) from None
        raise

