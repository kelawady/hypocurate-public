"""One read function per field of the access contract (`hypocurate.access.allowlist`).

Every function reads only rows of the access object's own run (single-run scope), and
builds its output from named keys only. Nothing is copied whole and then trimmed: a key
or value that is not named here never reaches a role. The layer (`layer.py`) calls these
inside its transaction, after the run is locked and the role's field is checked.

Stored records carry their fields in the common record format of step 4
(`CommonRecord.to_json()`): `harmonized` maps a field name to {value, unit, status, ...}.

Blinded views (the fields listed for the Planner, the Critic, the gap report and the
Commentator without a freeze) carry text only from vocabularies (`vocabulary.py`) or the
marker "unrecognized"; the plan is projected recursively by `PLAN_SCHEMA`. The post-freeze
fields (`records_full`, `flags_full`, `results`, `stage_outputs`, `run_cost`) return the stored
rows of the run: after the freeze the Analyst and the Commentator may see outcomes.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping

from sqlalchemy import Connection, text

from hypocurate.access import vocabulary as vocab
from hypocurate.access.allowlist import (BATCH_COLUMNS, CATEGORY_FIELDS, CONDITION_COUNT_FIELDS,
                                         CONDITION_RANGE_FIELDS, OUTCOME_FIELDS, PLAN_SCHEMA, POWER_SCHEMA,
                                         SOURCE_META_FIELDS)
from hypocurate.access.context import AccessContext as Context
from hypocurate.pipeline.binding import binding, record_identity
from hypocurate.sources import adapters
from hypocurate.sources.normalize import alloy_label, doi_group_key, identity_hash, same_alloy_key
from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, VALUE_STATUSES, AdapterError
from hypocurate.sources.versions import SOURCES, UnsealedVersion, load_sealed_version

HAS_VALUE = VALUE_STATUSES
UNITS = frozenset(u for u in HARMONIZED_FIELDS.values() if u)


class Refused(Exception):
    """A field function refuses this read (for example a Curator asking for a source its
    run did not record). The layer logs it as a denial with this code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


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
    """The run's chosen sources (a version recorded at dispatch), in key order, with the
    interpretation settings of that sealed version (never the mutable source row's)."""
    return _rows(conn, "SELECT s.key, sv.source_type, sv.data_kind, sv.grouping_unit, rs.source_version_id "
                       "FROM run_source rs JOIN source s ON s.id = rs.source_id "
                       "JOIN source_version sv ON sv.id = rs.source_version_id "
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


def _category(field: str, entry: Any) -> str | None:
    """A category field's value through its vocabulary (or the marker), only if it has a
    value status; None otherwise."""
    if _status(entry) in HAS_VALUE:
        return vocab.category(field, entry.get("value"))
    return None


def _unrecognized(harmonized_rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Per category field, how many values are unrecognized (counts only)."""
    return vocab.unrecognized_counts((f, h.get(f, {}).get("value")) for h in harmonized_rows
                                     for f in CATEGORY_FIELDS if _status(h.get(f)) in HAS_VALUE)


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
    """Counts by field status and by category value (through the vocabularies), and the
    unrecognized counts. Never a value of a non-category field."""
    harmonized_rows = list(harmonized_rows)
    n = 0
    by_status = {f: Counter() for f in HARMONIZED_FIELDS}
    by_category = {f: Counter() for f in CATEGORY_FIELDS}
    for h in harmonized_rows:
        n += 1
        for f in HARMONIZED_FIELDS:
            by_status[f][_status(h.get(f)) or "missing"] += 1
        for f in CATEGORY_FIELDS:
            value = _category(f, h.get(f))
            if value is not None:
                by_category[f][value] += 1
    return {"n_records": n,
            "by_status": {f: dict(sorted(c.items())) for f, c in by_status.items()},
            "by_category": {f: dict(sorted(c.items())) for f, c in by_category.items()},
            "unrecognized": _unrecognized(harmonized_rows)}


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
    """Name, licence and fields available from the code's source definitions; interpretation
    settings from the sealed version the run recorded. The source registry's text never."""
    out = []
    for row in _chosen_sources(conn, ctx):
        d = SOURCES.get(row.key)
        values = {"key": row.key,
                  "name": d.name if d else vocab.UNRECOGNIZED,
                  "source_type": row.source_type, "data_kind": row.data_kind,
                  "licence": d.licence if d else vocab.UNRECOGNIZED,
                  "grouping_unit": row.grouping_unit,
                  "fields_available": [f for f in d.properties_covered if f in HARMONIZED_FIELDS] if d else []}
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


def project(value: Any, schema: Any) -> Any:
    """`value` projected by `schema` (allowlist.PLAN_SCHEMA): named keys only, recursively;
    vocabulary leaves give the value or the marker; number, integer, field and unit leaves
    give the value or nothing. Returns None for nothing."""
    if isinstance(schema, Mapping):
        if not isinstance(value, Mapping):
            return None
        out = {}
        for key, sub in schema.items():
            if key in value:
                p = project(value[key], sub)
                if p is not None:
                    out[key] = p
        return out
    if isinstance(schema, tuple) and schema[0] == "list":
        if not isinstance(value, list):
            return None
        return [p for p in (project(v, schema[1]) for v in value) if p is not None]
    if isinstance(schema, frozenset):
        return vocab.code(value, schema)
    if isinstance(value, bool):
        return None
    if schema == "number":
        return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None
    if schema == "integer":
        return value if isinstance(value, int) else None
    if schema == "field":
        return value if isinstance(value, str) and value in HARMONIZED_FIELDS else None
    if schema == "unit":
        return value if isinstance(value, str) and value in UNITS else None
    raise ValueError(f"unknown schema leaf {schema!r}")


def source_documentation(conn: Connection, ctx: Context) -> dict:
    """The documentation files of the one sealed version the Curator's invocation names, as text
    (step 8a). Never a data file and never another version."""
    if ctx.source_version_id is None:
        raise Refused("no_source")
    version = load_sealed_version(conn, ctx.source_version_id)
    return {"source": version.source_key,
            "documents": {path: content.decode("utf-8") for path, content in sorted(version.documentation.items())}}


def curation_targets(conn: Connection, ctx: Context) -> dict:
    """The fields the Curator may propose a value for, with their vocabularies (step 8a)."""
    return {field: dict(spec) for field, spec in vocab.CURATION_TARGETS.items()}


def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
    """No measured number of any field (owner, 2026-10-05): statuses, categories from their
    vocabularies, identity. No paper title and no origin key (step 5 review, finding 3)."""
    out = []
    for r in _stored_records(conn, ctx):
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        composition = _composition(h.get("composition"))
        out.append({
            "id": r.id, "source": r.source, "item_index": r.item_index, "kind": r.kind,
            # The label is derived by code from the composition, never taken from the source.
            "alloy": alloy_label(composition) if composition else None,
            "composition": composition, "paper_doi": vocab.doi(r.paper_doi),
            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
            "categories": {f: _category(f, h.get(f)) for f in CATEGORY_FIELDS},
        })
    return out


_ROW = re.compile(r":row:(\d+)$")
# The non-outcome measured values Inclusion needs (scope and the grain-size rules).
CONDITION_NUMBERS = ("grain_size", "test_temperature")


def record_conditions(conn: Connection, ctx: Context) -> list[dict]:
    """For Inclusion (code; step 6). No outcome value: outcome fields give their status only.
    No value as reported and no free text: categories through their vocabularies, the paper
    (from the DOI) and the batch as hashes, the row number from the origin key."""
    out = []
    for r in _stored_records(conn, ctx):
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        reported = r.reported if isinstance(r.reported, Mapping) else {}
        row = _ROW.search(r.source_item_key or "")
        batch_column = BATCH_COLUMNS.get(r.source)
        batch = reported.get(batch_column, {}).get("text") if batch_column else None
        doi = r.paper_doi if isinstance(r.paper_doi, str) and r.paper_doi.strip() else None
        content = {"version_fingerprint": r.version_fingerprint, "origin": r.source_item_key,
                   "item_index": r.item_index, "kind": r.kind, "harmonized": r.harmonized, "reported": r.reported,
                   "paper_reference": r.paper_reference, "paper_doi": r.paper_doi}
        out.append({
            "id": r.id, "source": r.source, "row": int(row.group(1)) if row else None, "kind": r.kind,
            # Stable identity (step 6 review, findings 3 and 5): for tie-breaks and the freeze
            # fingerprint, never a database id. The origin key carries no value.
            "version_fingerprint": r.version_fingerprint, "origin": r.source_item_key, "item_index": r.item_index,
            # A hash of the stored record (for the freeze fingerprint): it carries no value.
            "fingerprint": hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"),
                                                     ensure_ascii=False).encode("utf-8")).hexdigest(),
            "has_doi": doi is not None,
            "paper": identity_hash(doi_group_key(doi)) if doi else None,
            "batch": identity_hash(batch) if isinstance(batch, str) and batch.strip() else None,
            "composition": _composition(h.get("composition")),
            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
            "values": {f: _number(h.get(f)) for f in CONDITION_NUMBERS if f not in OUTCOME_FIELDS},
            "categories": {f: _category(f, h.get(f)) for f in CATEGORY_FIELDS},
        })
    return out


def set_flags(conn: Connection, ctx: Context) -> dict:
    """The per-set matching flags of the run's completed Checks result (step 6 review, finding 2):
    codes and record ids only.

    Re-check finding 1: read in the same transaction as the role's other fields, under the run's
    lock, and only after verifying that a completed Checks result exists and covers exactly the
    records and flags of the run as they are now; otherwise the read is refused
    (`checks_not_done`, `checks_not_current`), never answered with "no flags"."""
    output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'checks' "
                               "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=ctx.run_id)).scalar_one_or_none()
    if not isinstance(output, Mapping) or not isinstance(output.get("binding"), Mapping):
        raise Refused("checks_not_done")
    identity = {i: record_identity(fp, key, ix) for i, fp, key, ix in _rows(
        conn, "SELECT r.id, sv.fingerprint, r.source_item_key, r.item_index FROM record r "
              "JOIN source_version sv ON sv.id = r.source_version_id WHERE r.extraction_run_id = :r", r=ctx.run_id)}
    flagged = [(f.kind, f.category, [identity[x] for x in _flag_records(conn, ctx).get(f.id, []) if x in identity])
               for f in _rows(conn, "SELECT id, kind, category FROM flag WHERE run_id = :r", r=ctx.run_id)]
    if binding(identity.values(), flagged) != dict(output["binding"]):
        raise Refused("checks_not_current")
    stored = output.get("set_flags", {})
    out = {}
    for key, flags in (stored.items() if isinstance(stored, Mapping) else ()):
        out[vocab.code(key, vocab.SENSITIVITY_KEYS)] = [
            {"kind": vocab.code(f.get("kind"), vocab.FLAG_KINDS), "category": vocab.code(f.get("category"), vocab.FLAG_CATEGORIES),
             "records": [r for r in f.get("records", []) if isinstance(r, int) and not isinstance(r, bool)]}
            for f in flags if isinstance(f, Mapping)]
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
    return [{"id": f.id, "kind": vocab.code(f.kind, vocab.FLAG_KINDS),
             "category": vocab.code(f.category, vocab.FLAG_CATEGORIES), "records": records.get(f.id, [])}
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
    return {"content": project(p.content, PLAN_SCHEMA) or {},
            "fingerprint": p.fingerprint, "locked_at": _plain(p.locked_at),
            "sufficiency_option": p.sufficiency_option,
            "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
                         "resid_df": p.min_resid_df},
            "sensitivity_analyses": [vocab.code(k, vocab.SENSITIVITY_KEYS) for k in p.sensitivity_analysis_keys],
            "power_assumptions": project(p.power_assumptions, POWER_SCHEMA)}


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
        key = vocab.code(key, vocab.ANALYSIS_SET_KEYS)
        sets.setdefault(key, [])
        if record_id is not None:
            sets[key].append(record_id)
    # Step 8b (owner, 2026-10-07): each record's source key, so code can tell which sources contributed.
    return {"records": [{"record": rec, "source": vocab.code(source, vocab.SOURCE_KEYS), "eligible": eligible,
                         "rule": vocab.code(rule, vocab.ELIGIBILITY_RULES)}
                        for rec, source, eligible, rule in _rows(
                conn, "SELECT rr.record_id, s.key, rr.eligible, rr.rule FROM run_record rr "
                      "JOIN record rec ON rec.id = rr.record_id JOIN source_version sv ON sv.id = rec.source_version_id "
                      "JOIN source s ON s.id = sv.source_id WHERE rr.run_id = :r ORDER BY rr.record_id",
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
    """Codes and counts only: no failure text (step 5 review, finding 3). `unrecognized`: per
    source, how many category values of the run's records were unrecognized (owner, 2026-10-05)."""
    by_source: dict[str, list] = {}
    for r in _stored_records(conn, ctx):
        by_source.setdefault(r.source, []).append(r.harmonized if isinstance(r.harmonized, Mapping) else {})
    per_source = [{"source": key, "search_status": st, "nothing_found": nf,
                   "unrecognized": _unrecognized(by_source.get(key, []))}
                  for key, st, nf in _rows(
                      conn, "SELECT s.key, rs.search_status, rs.nothing_found FROM run_source rs "
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
        out[f] = dict(sorted(Counter(v for v in (_category(f, h.get(f)) for h in harmonized_rows)
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


def gap_report(conn: Connection, ctx: Context) -> list[dict]:
    """The output of each Analyst stage of the run, and nothing else of those stages."""
    return [{"stage": s.stage, "attempt": s.attempt, "status": s.status, "output": s.output} for s in _rows(
        conn, "SELECT stage, attempt, status, output FROM stage_result WHERE run_id = :r AND role = 'analyst' "
              "ORDER BY id", r=ctx.run_id)]


def outcome(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT status, outcome, verdict, exploratory FROM run WHERE id = :r", r=ctx.run_id)[0]
    return {"status": row.status, "outcome": row.outcome, "verdict": row.verdict, "exploratory": row.exploratory}


def frozen_analysis_data(conn: Connection, ctx: Context) -> dict:
    """For Statistics (code; step 7): the frozen sets and, for their records only, what the model
    needs. The outcome value is the locked plan's outcome field (sprint 1: yield strength), through
    `_number` (a value status and a finite number, else None). Refused without a freeze."""
    snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                            dict(r=ctx.run_id)).scalar_one_or_none()
    if snapshot is None:
        raise Refused("not_frozen")
    content = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=ctx.run_id)).scalar_one()
    outcome_field = (project(content, PLAN_SCHEMA) or {}).get("variables", {}).get("outcome", {}).get("field")
    sets: dict[str, list[int]] = {}
    for key, record_id in _rows(conn, "SELECT a.key, asr.record_id FROM analysis_set a "
                                      "LEFT JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
                                      "WHERE a.run_id = :r ORDER BY a.key, asr.record_id", r=ctx.run_id):
        key = vocab.code(key, vocab.ANALYSIS_SET_KEYS)
        sets.setdefault(key, [])
        if record_id is not None:
            sets[key].append(record_id)
    members = {i for ids in sets.values() for i in ids}
    records = []
    for r in _stored_records(conn, ctx):
        if r.id not in members:
            continue
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        reported = r.reported if isinstance(r.reported, Mapping) else {}
        batch_column = BATCH_COLUMNS.get(r.source)
        batch = reported.get(batch_column, {}).get("text") if batch_column else None
        doi = r.paper_doi if isinstance(r.paper_doi, str) and r.paper_doi.strip() else None
        records.append({
            "id": r.id, "source": r.source,
            "version_fingerprint": r.version_fingerprint, "origin": r.source_item_key, "item_index": r.item_index,
            "composition": _composition(h.get("composition")),
            "paper": identity_hash(doi_group_key(doi)) if doi else None,
            "batch": identity_hash(batch) if isinstance(batch, str) and batch.strip() else None,
            "grain_size": _number(h.get("grain_size")),
            "outcome": _number(h.get(outcome_field)) if outcome_field in OUTCOME_FIELDS else None,
        })
    return {"freeze_fingerprint": snapshot, "outcome_field": outcome_field if outcome_field in OUTCOME_FIELDS
            else None, "sets": sets, "records": records}


# --- Step 8b: the narrowing decision's counts and the Analyst's facts ---------------------------

# The fields a candidate-count cell names (owner, Q5): the claim's countable parts and what makes a
# record usable (grain size and the outcome at an accepted status). Alloy class is not countable.
CANDIDATE_CATEGORIES = ("phase_class", "test_type", "test_temperature_band")
CANDIDATE_STATUS_FIELDS = CANDIDATE_CATEGORIES + ("test_temperature", "grain_size") + tuple(sorted(OUTCOME_FIELDS))


def candidate_counts(conn: Connection, ctx: Context) -> list[dict]:
    """For the narrowing decision (code; step 8b), before the lock: per chosen source, read through its
    adapter from the sealed version recorded at dispatch (records are stored only after the lock),
    counts of records per cell. A cell is the categories (through their vocabularies), the reported
    test temperature, the status of each field in CANDIDATE_STATUS_FIELDS, and whether a grain size is
    present. Counts and statuses only: no outcome value, no composition, no free text."""
    out = []
    for row in _chosen_sources(conn, ctx):
        version = load_sealed_version(conn, row.source_version_id)
        try:
            result = adapters.read(version)
        except (AdapterError, UnsealedVersion):
            out.append({"source": row.key, "version_fingerprint": version.fingerprint, "readable": False})
            continue
        cells: Counter = Counter()
        for r in result.records:
            h = {f: v.to_json() for f, v in r.harmonized.items()}
            cells[json.dumps({
                "categories": {f: _category(f, h.get(f)) for f in CANDIDATE_CATEGORIES},
                "test_temperature": _number(h.get("test_temperature")),
                "status": {f: _status(h.get(f)) for f in CANDIDATE_STATUS_FIELDS},
                "grain_size_present": _number(h.get("grain_size")) is not None,
            }, sort_keys=True)] += 1
        out.append({"source": row.key, "version_fingerprint": version.fingerprint, "readable": True,
                    "n_records": len(result.records),
                    "cells": [{**json.loads(cell), "n": n} for cell, n in sorted(cells.items())]})
    return out


def _done_output(conn: Connection, run_id: int, stage: str) -> Mapping | None:
    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s AND status = 'done' "
                            "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
    return out if isinstance(out, Mapping) else None


def analyst_facts(conn: Connection, ctx: Context) -> dict:
    """The Analyst's facts (step 8b; owner, Q6 and 2026-10-07): named facts built by code from what it stored
    (`pipeline.analyst_names`), each a finished display string or phrase the Analyst refers to as {name}. Refused
    when the stored facts its stage needs are missing."""
    from hypocurate.pipeline import analyst_names as an
    number = conn.execute(text("SELECT h.number, r.fixed_plan, h.narrower_of_run_id FROM run r JOIN hypothesis_version hv "
                               "ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
                               "WHERE r.id = :r"), dict(r=ctx.run_id)).one()
    if ctx.stage == "narrowed":
        n = _done_output(conn, ctx.run_id, "narrowing")
        if n is None or n.get("result") != "partly_sufficient":
            raise Refused("facts_missing")
        names = an.narrowing_names(n)
        kind = "narrowing"
    else:
        stats, gap = _done_output(conn, ctx.run_id, "statistics"), _done_output(conn, ctx.run_id, "gap_facts")
        if stats is None or gap is None:
            raise Refused("facts_missing")
        p = _rows(conn, "SELECT content, sufficiency_option, min_records, min_alloys, min_groups, min_resid_df "
                        "FROM plan WHERE run_id = :r", r=ctx.run_id)[0]
        content = project(p.content, PLAN_SCHEMA) or {}
        plan_facts = {"alpha": (content.get("model") or {}).get("alpha"),
                      "alternative": (content.get("model") or {}).get("alternative"),
                      "sufficiency_option": p.sufficiency_option,
                      "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
                                   "resid_df": p.min_resid_df}}
        if number.fixed_plan:
            note = {"scope_source": an.NARROWER_PLAN_SENTENCE if number.narrower_of_run_id else an.FIXED_PLAN_SENTENCE}
        else:
            planner = _done_output(conn, ctx.run_id, "planner") or {}
            answer = planner.get("answer") or {}
            note = an.scope_notes(answer.get("claim_scope"), answer.get("stated"))
        names = an.analysis_names(stats, gap, plan_facts, note)
        kind = "analysis" if ctx.stage == "analysis" else "no_dataset_frozen"
    names["query_number"] = str(number.number)
    an.check_names(names)
    return {"kind": kind, "names": dict(sorted(names.items()))}


READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
    "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
    "record_counts": record_counts, "source_documentation": source_documentation,
    "curation_targets": curation_targets, "record_metadata": record_metadata, "flags_kind": flags_kind,
    "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
    "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
    "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
    "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions, "set_flags": set_flags,
    "frozen_analysis_data": frozen_analysis_data, "candidate_counts": candidate_counts,
    "analyst_facts": analyst_facts,
}
