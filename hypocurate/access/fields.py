"""One read function per field of the access contract (`hypocurate.access.allowlist`).

Every function reads only rows of the access object's own run (single-run scope), and
builds its output from named keys only. Nothing is copied whole and then trimmed: a key
or value that is not named here never reaches a role. The layer (`layer.py`) calls these
inside its transaction, after the run is locked and the role's field is checked.

Stored records carry their fields in the common record format of step 4
(`CommonRecord.to_json()`): `harmonized` maps a field name to {value, unit, status, ...}.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping

from sqlalchemy import Connection, text

from hypocurate.access.allowlist import (CATEGORY_FIELDS, CONDITION_COUNT_FIELDS, CONDITION_RANGE_FIELDS,
                                         PLAN_KEYS, SOURCE_META_FIELDS)
from hypocurate.sources import adapters
from hypocurate.sources.normalize import same_alloy_key
from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, AdapterError
from hypocurate.sources.versions import UnsealedVersion, load_sealed_version

HAS_VALUE = ("converted", "assigned")


class Refused(Exception):
    """A field function refuses this read (for example a Curator asking for a source its
    run did not record). The layer logs it as denied and raises AccessDenied."""


@dataclass(frozen=True)
class Context:
    run_id: int
    role: str
    source_key: str | None  # the Curator's one source


def _plain(v: Any) -> Any:
    """A database value as plain JSON: times as ISO text, exact numbers as text."""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


def _rows(conn: Connection, sql: str, **params) -> list:
    return conn.execute(text(sql), dict(params)).all()


# --- Shared readers -----------------------------------------------------------------

def _chosen_sources(conn: Connection, ctx: Context) -> list:
    """The run's chosen sources (a version recorded at dispatch), in key order."""
    return _rows(conn, "SELECT s.key, s.name, s.source_type, s.data_kind, s.licence, s.grouping_unit, "
                       "s.properties_covered, rs.source_version_id FROM run_source rs "
                       "JOIN source s ON s.id = rs.source_id "
                       "WHERE rs.run_id = :r AND rs.source_version_id IS NOT NULL ORDER BY s.key", r=ctx.run_id)


def _stored_records(conn: Connection, ctx: Context) -> list:
    return _rows(conn, "SELECT rec.id, s.key AS source, rec.source_item_key, rec.item_index, rec.kind, rec.alloy, "
                       "rec.harmonized, rec.reported, rec.paper_reference, rec.paper_doi, "
                       "sv.fingerprint AS version_fingerprint FROM record rec "
                       "JOIN source_version sv ON sv.id = rec.source_version_id "
                       "JOIN source s ON s.id = sv.source_id "
                       "WHERE rec.extraction_run_id = :r ORDER BY rec.id", r=ctx.run_id)


def _status(entry: Any) -> str | None:
    """A field's status, only if it is one of the known statuses."""
    if isinstance(entry, Mapping) and entry.get("status") in STATUSES:
        return entry["status"]
    return None


def _number(entry: Any) -> float | None:
    """A field's value, only if it has a value status and is a finite number."""
    if _status(entry) in HAS_VALUE:
        v = entry.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
            return float(v)
    return None


def _category(entry: Any) -> str | None:
    """A category field's value, only if it has a value status and is text."""
    if _status(entry) in HAS_VALUE and isinstance(entry.get("value"), str):
        return entry["value"]
    return None


def _composition(entry: Any) -> dict[str, float] | None:
    """A composition (element -> atomic %), only if every amount is a finite number."""
    if _status(entry) not in HAS_VALUE or not isinstance(entry.get("value"), Mapping):
        return None
    out = {}
    for element, amount in entry["value"].items():
        if not (isinstance(element, str) and element.isalpha() and len(element) <= 2):
            return None
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount):
            return None
        out[element] = float(amount)
    return out


def _counts(harmonized_rows: Iterable[Mapping[str, Any]]) -> dict:
    """Counts by field status and by category value. Never a value of a non-category field."""
    n = 0
    by_status = {f: Counter() for f in HARMONIZED_FIELDS}
    by_category = {f: Counter() for f in CATEGORY_FIELDS}
    for h in harmonized_rows:
        n += 1
        for f in HARMONIZED_FIELDS:
            by_status[f][_status(h.get(f)) or "missing"] += 1
        for f in CATEGORY_FIELDS:
            value = _category(h.get(f))
            if value is not None:
                by_category[f][value] += 1
    return {"n_records": n,
            "by_status": {f: dict(sorted(c.items())) for f, c in by_status.items()},
            "by_category": {f: dict(sorted(c.items())) for f, c in by_category.items()}}


# --- The fields ---------------------------------------------------------------------

def claim(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT h.number, hv.version_number, hv.text, h.narrower_of_run_id IS NOT NULL AS narrower "
                      "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                      "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=ctx.run_id)[0]
    return {"query": row.number, "version": row.version_number, "text": row.text, "narrower_question": row.narrower}


def domain(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT d.key, d.name, d.profile_name FROM run r "
                      "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                      "JOIN domain d ON d.id = hv.confirmed_domain_id WHERE r.id = :r", r=ctx.run_id)[0]
    return {"key": row.key, "name": row.name, "profile": row.profile_name}


def sources_meta(conn: Connection, ctx: Context) -> list[dict]:
    out = []
    for row in _chosen_sources(conn, ctx):
        if ctx.role == "curator" and row.key != ctx.source_key:
            continue
        values = {"key": row.key, "name": row.name, "source_type": row.source_type, "data_kind": row.data_kind,
                  "licence": row.licence, "grouping_unit": row.grouping_unit,
                  "fields_available": [f for f in row.properties_covered if f in HARMONIZED_FIELDS]}
        out.append({k: values[k] for k in SOURCE_META_FIELDS})
    return out


def tag_values(conn: Connection, ctx: Context) -> list[dict]:
    return [{"kind": kind, "value": value} for kind, value in _rows(
        conn, "SELECT kind, value FROM tag_value WHERE status = 'approved' ORDER BY kind, value")]


def record_counts(conn: Connection, ctx: Context) -> list[dict]:
    """Computed by code from each chosen source's sealed version, through its adapter
    (records are stored only after the rules lock)."""
    out = []
    for row in _chosen_sources(conn, ctx):
        try:
            result = adapters.read(load_sealed_version(conn, row.source_version_id))
        except (AdapterError, UnsealedVersion):
            out.append({"source": row.key, "readable": False})
            continue
        counts = _counts({f: v.to_json() for f, v in r.harmonized.items()} for r in result.records)
        out.append({"source": row.key, "readable": True, **counts})
    return out


def _fields_to_extract(content: Any) -> list[str]:
    """The plan's list of fields to extract: only names of the common fields, in order;
    anything else in the list is withheld."""
    listed = content.get("fields_to_extract") if isinstance(content, Mapping) else None
    out: list[str] = []
    for f in listed if isinstance(listed, list) else []:
        if isinstance(f, str) and f in HARMONIZED_FIELDS and f not in out:
            out.append(f)
    return out


def plan_fields_to_extract(conn: Connection, ctx: Context) -> list[str]:
    return _fields_to_extract(_rows(conn, "SELECT content FROM plan WHERE run_id = :r", r=ctx.run_id)[0].content)


def source_content(conn: Connection, ctx: Context) -> dict:
    """The sealed files of the Curator's one source, from the version its run recorded."""
    if ctx.source_key is None:
        raise Refused("the Curator reads one named source; none was given")
    vid = conn.execute(text(
        "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
        "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL"),
        dict(r=ctx.run_id, k=ctx.source_key)).scalar_one_or_none()
    if vid is None:
        raise Refused(f"source {ctx.source_key!r} is not recorded for this run")
    version = load_sealed_version(conn, vid)
    return {"source": ctx.source_key, "files": dict(version.files)}


def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
    """No measured number of any field (owner, 2026-10-05): statuses, categories, identity."""
    out = []
    for r in _stored_records(conn, ctx):
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        out.append({
            "id": r.id, "source": r.source, "origin": r.source_item_key, "item_index": r.item_index,
            "kind": r.kind, "alloy": r.alloy, "composition": _composition(h.get("composition")),
            "paper_reference": r.paper_reference, "paper_doi": r.paper_doi,
            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
            "categories": {f: _category(h.get(f)) for f in CATEGORY_FIELDS},
        })
    return out


def _flag_records(conn: Connection, ctx: Context) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for flag_id, record_id in _rows(conn, "SELECT fr.flag_id, fr.record_id FROM flag_record fr "
                                          "JOIN flag f ON f.id = fr.flag_id WHERE f.run_id = :r "
                                          "ORDER BY fr.flag_id, fr.record_id", r=ctx.run_id):
        out.setdefault(flag_id, []).append(record_id)
    return out


def flags_kind(conn: Connection, ctx: Context) -> list[dict]:
    """Kind, category and records only: never the numbers compared (PRD 4)."""
    records = _flag_records(conn, ctx)
    return [{"id": f.id, "kind": f.kind, "category": f.category, "records": records.get(f.id, [])}
            for f in _rows(conn, "SELECT id, kind, category FROM flag WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def flags_full(conn: Connection, ctx: Context) -> list[dict]:
    records = _flag_records(conn, ctx)
    return [{"id": f.id, "kind": f.kind, "category": f.category, "records": records.get(f.id, []),
             "compared_values": f.compared_values, "critic_class": f.critic_class,
             "critic_reason": f.critic_reason, "raised_at": _plain(f.raised_at),
             "classified_at": _plain(f.classified_at)}
            for f in _rows(conn, "SELECT id, kind, category, compared_values, critic_class, critic_reason, "
                                 "raised_at, classified_at FROM flag WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def plan(conn: Connection, ctx: Context) -> dict:
    p = _rows(conn, "SELECT content, fingerprint, locked_at, sufficiency_option, min_records, min_alloys, "
                    "min_groups, min_resid_df, sensitivity_analysis_keys, power_assumptions "
                    "FROM plan WHERE run_id = :r", r=ctx.run_id)[0]
    content = p.content if isinstance(p.content, Mapping) else {}
    # The named parts as written at the rules lock; the field list as the Curator gets it.
    # (The structure of the other parts is step 6's plan model, which projects each part.)
    named = {k: content[k] for k in PLAN_KEYS if k in content}
    if "fields_to_extract" in named:
        named["fields_to_extract"] = _fields_to_extract(content)
    return {"content": named,
            "fingerprint": p.fingerprint, "locked_at": _plain(p.locked_at),
            "sufficiency_option": p.sufficiency_option,
            "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
                         "resid_df": p.min_resid_df},
            "sensitivity_analyses": list(p.sensitivity_analysis_keys),
            "power_assumptions": p.power_assumptions}


def records_full(conn: Connection, ctx: Context) -> list[dict]:
    return [{"id": r.id, "source": r.source, "origin": r.source_item_key, "item_index": r.item_index,
             "kind": r.kind, "alloy": r.alloy, "harmonized": r.harmonized, "reported": r.reported,
             "paper_reference": r.paper_reference, "paper_doi": r.paper_doi,
             "version_fingerprint": r.version_fingerprint}
            for r in _stored_records(conn, ctx)]


def decisions(conn: Connection, ctx: Context) -> dict:
    sets: dict[str, list[int]] = {}
    for key, record_id in _rows(conn, "SELECT a.key, asr.record_id FROM analysis_set a "
                                      "LEFT JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
                                      "WHERE a.run_id = :r ORDER BY a.key, asr.record_id", r=ctx.run_id):
        sets.setdefault(key, [])
        if record_id is not None:
            sets[key].append(record_id)
    return {"records": [{"record": rec, "eligible": eligible, "rule": rule} for rec, eligible, rule in _rows(
                conn, "SELECT record_id, eligible, rule FROM run_record WHERE run_id = :r ORDER BY record_id",
                r=ctx.run_id)],
            "sets": sets}


def results(conn: Connection, ctx: Context) -> dict:
    run = _rows(conn, "SELECT status, outcome, verdict, exploratory, fixed_plan, agent_mode, failure_reason "
                      "FROM run WHERE id = :r", r=ctx.run_id)[0]
    snap = _rows(conn, "SELECT fingerprint, n_records, frozen_at FROM run_snapshot WHERE run_id = :r", r=ctx.run_id)
    analyses = _rows(conn, "SELECT ar.id, ar.scope, a.key AS analysis_set, s.key AS source, ar.n_records, "
                           "ar.n_alloys, ar.n_groups, ar.resid_df, ar.check1_passed, ar.check2_passed, "
                           "ar.minimums_met, ar.estimate, ar.std_error, ar.p_value, ar.estimated_power, ar.label "
                           "FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
                           "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id",
                     r=ctx.run_id)
    calibration = _rows(conn, "SELECT analysis_result_id, status, reason, assumptions, n_simulations, seed, "
                              "null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, "
                              "confidence_flag FROM calibration_result WHERE run_id = :r ORDER BY id", r=ctx.run_id)
    return {"run": {k: _plain(v) for k, v in run._mapping.items()},
            "freeze": {k: _plain(v) for k, v in snap[0]._mapping.items()} if snap else None,
            "analyses": [{k: _plain(v) for k, v in a._mapping.items()} for a in analyses],
            "calibration": [{k: _plain(v) for k, v in c._mapping.items()} for c in calibration]}


def coverage(conn: Connection, ctx: Context) -> dict:
    per_source = [{"source": key, "search_status": st, "nothing_found": nf, "failure_reason": fr}
                  for key, st, nf, fr in _rows(
                      conn, "SELECT s.key, rs.search_status, rs.nothing_found, rs.failure_reason FROM run_source rs "
                            "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r ORDER BY s.key", r=ctx.run_id)]
    view = _rows(conn, "SELECT * FROM run_search_coverage WHERE run_id = :r", r=ctx.run_id)[0]
    return {"sources": per_source,
            "lists": {k: list(v) if v is not None else [] for k, v in view._mapping.items() if k != "run_id"}}


def stage_outputs(conn: Connection, ctx: Context) -> list[dict]:
    return [{k: _plain(v) for k, v in s._mapping.items()} for s in _rows(
        conn, "SELECT id, stage, attempt, role, status, input, output, reasoning, tool_calls, model, "
              "started_at, finished_at FROM stage_result WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def run_cost(conn: Connection, ctx: Context) -> dict:
    total = _rows(conn, "SELECT * FROM model_call_totals_by_run WHERE run_id = :r", r=ctx.run_id)[0]
    stages = _rows(conn, "SELECT * FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage_result_id",
                   r=ctx.run_id)
    return {"total": {k: _plain(v) for k, v in total._mapping.items() if k != "run_id"},
            "stages": [{k: _plain(v) for k, v in s._mapping.items() if k != "run_id"} for s in stages]}


def stored_record_counts(conn: Connection, ctx: Context) -> list[dict]:
    by_source: dict[str, list] = {}
    for r in _stored_records(conn, ctx):
        by_source.setdefault(r.source, []).append(r.harmonized if isinstance(r.harmonized, Mapping) else {})
    return [{"source": key, **_counts(rows)} for key, rows in sorted(by_source.items())]


def _summary(harmonized_rows: list[Mapping[str, Any]]) -> dict:
    out: dict[str, Any] = {"n_records": len(harmonized_rows)}
    for f in CONDITION_RANGE_FIELDS:
        values = [v for v in (_number(h.get(f)) for h in harmonized_rows) if v is not None]
        out[f] = {"n": len(values), "min": min(values) if values else None, "max": max(values) if values else None}
    for f in CONDITION_COUNT_FIELDS:
        out[f] = dict(sorted(Counter(v for v in (_category(h.get(f)) for h in harmonized_rows)
                                     if v is not None).items()))
    return out


def condition_summaries(conn: Connection, ctx: Context) -> dict:
    """Owner, 2026-10-05: summaries of the non-outcome conditions the stored records cover,
    per alloy (grouped by the same-alloy rule) and overall. No row-level value, no outcome."""
    rows = [r.harmonized if isinstance(r.harmonized, Mapping) else {} for r in _stored_records(conn, ctx)]
    groups: dict[str, list] = {}
    for h in rows:
        composition = _composition(h.get("composition"))
        key = same_alloy_key(composition) if composition else "composition not available"
        groups.setdefault(key, []).append(h)
    return {"overall": _summary(rows),
            "per_alloy": [{"alloy": key, **_summary(g)} for key, g in sorted(groups.items())]}


READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
    "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
    "record_counts": record_counts, "plan_fields_to_extract": plan_fields_to_extract,
    "source_content": source_content, "record_metadata": record_metadata, "flags_kind": flags_kind,
    "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
    "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
    "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
}
