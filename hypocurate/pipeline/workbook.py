"""The run's workbook and records CSV (PRD 11; build step 10b): built on request from stored rows, never stored; the
same function serves the website's download and the command line's `export`.

Four sheets:
- **Records used:** one row per record in the test (the primary set): source, item, alloy, kind of data, paper, each
  harmonized value with its unit and status (and the citation of a value assigned from the source or by decision),
  and the values as originally reported.
- **Records not used:** every other record the run found, with the same columns, the rule that decided it, the flags
  code raised on it, and the sensitivity sets that use it.
- **Significance and commentary:** code's results statement, the calibration with its assumptions, and the commentary
  (none in sprint 1: the Commentator is step 12).
- **Run summary:** the query and version, domain and tags, the locked plan, the rules lock and dataset freeze (times
  and fingerprints), each result (pooled, per source, sensitivity sets by name), the outcome, the sources searched
  and not, tokens and cost per stage and in total, the agent mode and settings versions, the source versions.
Every sheet's first line states the workbook's format and the code version that built it. The workbook's document
dates are the run's dispatch time; the same stored rows give the same cells (the zip file's own timestamps, written by
the spreadsheet library, are not fixed, so the bytes may differ). Read in one snapshot.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import plot, run_view
from hypocurate.pipeline.eligibility import PRIMARY
from hypocurate.pipeline.run_view import snapshot

WORKBOOK_FORMAT = 1
SHEETS = ("Records used", "Records not used", "Significance and commentary", "Run summary")
BASE_COLUMNS = ("record", "source", "item", "alloy", "kind of data", "paper reference", "paper DOI")
COMMENTARY_NONE = "No commentary: the Commentator is not built in sprint 1 (PRD 15, step 12)."


def version_line() -> str:
    return plot.version_line("Workbook", WORKBOOK_FORMAT)


def _value(entry: Any) -> Any:
    if not isinstance(entry, Mapping):
        return None
    v = entry.get("value")
    if isinstance(v, Mapping):  # a composition: element and atomic percent
        return " ".join(f"{k}{amount:g}" for k, amount in sorted(v.items()))
    return v


def _citation(entry: Any) -> str | None:
    c = entry.get("citation") if isinstance(entry, Mapping) else None
    if not isinstance(c, Mapping):
        return None
    return "; ".join(str(c[k]) for k in ("document", "location", "quote") if c.get(k))


def _reported(reported: Any) -> str:
    if not isinstance(reported, Mapping):
        return ""
    return "; ".join(f"{k}: {v.get('text')}" + (f" {v['unit']}" if v.get("unit") else "")
                     for k, v in sorted(reported.items()) if isinstance(v, Mapping))


def _records(conn: Connection, run_id: int) -> tuple[list[dict], list[str]]:
    rows = conn.execute(text(
        "SELECT r.id, s.key AS source, r.source_item_key, r.alloy, r.kind, r.paper_reference, r.paper_doi, "
        "r.harmonized, r.reported, rr.eligible, rr.rule FROM record r JOIN source_version sv ON sv.id = "
        "r.source_version_id JOIN source s ON s.id = sv.source_id LEFT JOIN run_record rr ON rr.run_id = :r AND "
        "rr.record_id = r.id WHERE r.extraction_run_id = :r ORDER BY s.key, r.id"), dict(r=run_id)).all()
    sets: dict[int, list[str]] = {}
    for key, rid in conn.execute(text(
            "SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
            "WHERE a.run_id = :r ORDER BY a.key"), dict(r=run_id)).all():
        sets.setdefault(rid, []).append(key)
    flags: dict[int, list[str]] = {}
    for kind, category, rid in conn.execute(text(
            "SELECT f.kind, f.category, fr.record_id FROM flag f JOIN flag_record fr ON fr.flag_id = f.id "
            "WHERE f.run_id = :r ORDER BY f.id"), dict(r=run_id)).all():
        flags.setdefault(rid, []).append(kind.replace("_", " ") + (f" ({category})" if category else ""))
    fields = sorted({f for r in rows if isinstance(r.harmonized, Mapping) for f in r.harmonized})
    out = []
    for r in rows:
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        row = {"record": r.id, "source": r.source, "item": r.source_item_key, "alloy": r.alloy, "kind of data": r.kind,
               "paper reference": r.paper_reference, "paper DOI": r.paper_doi}
        for f in fields:
            e = h.get(f)
            row[f] = _value(e)
            row[f"{f} unit"] = e.get("unit") if isinstance(e, Mapping) else None
            row[f"{f} status"] = (e.get("status") or "").replace("_", " ") if isinstance(e, Mapping) else "missing"
            row[f"{f} citation"] = _citation(e)
        row["values as reported"] = _reported(r.reported)
        in_sets = sets.get(r.id, [])
        row["_used"] = PRIMARY in in_sets
        row["eligible"] = {True: "yes", False: "no", None: "not decided"}[r.eligible]
        row["rule"] = (r.rule or "").replace("_", " ") or None
        row["flags"] = "; ".join(flags.get(r.id, [])) or None
        row["sensitivity sets"] = "; ".join(run_view._set_display_name(k) for k in in_sets
                                            if k != PRIMARY) or None
        out.append(row)
    columns = list(BASE_COLUMNS)
    for f in fields:
        columns += [f, f"{f} unit", f"{f} status", f"{f} citation"]
    columns.append("values as reported")
    return out, columns


def _summary(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
    page = run_view.run_page_in(conn, run_id)
    head = conn.execute(text(
        "SELECT r.agent_mode, r.experiment_flags, to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS "
        "queued, to_char(r.started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS started, "
        "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS ended "
        "FROM run r WHERE r.id = :r"), dict(r=run_id)).one()
    plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
    settings = conn.execute(text(
        "SELECT ras.role, ag.version FROM run_agent_setting ras JOIN agent_setting ag ON ag.id = ras.agent_setting_id "
        "WHERE ras.run_id = :r ORDER BY ras.role"), dict(r=run_id)).all()
    versions = conn.execute(text(
        "SELECT s.key, sv.label, sv.fingerprint, rs.search_status FROM run_source rs JOIN source s ON s.id = "
        "rs.source_id LEFT JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r ORDER BY s.key"),
        dict(r=run_id)).all()
    cp = page["checkpoints"]
    rows: list[tuple[str, Any]] = [
        ("Query", f"{page['query']}, version {page['version']}"), ("Run", run_id),
        ("Hypothesis", page["claim"]), ("Domain", page["domain"]), ("Tags", "; ".join(page["tags"]) or None),
        ("Status", page["status_words"]), ("Outcome", page["outcome"]), ("Verdict", page["verdict"]),
        ("Evidence level", page["evidence"]["words"]),
        ("Question as tested", (page["question_as_tested"] or {}).get("text")),
        ("Its source", (page["question_as_tested"] or {}).get("label")),
        ("Test run", run_view.TEST_RUN_BADGE if page["test_run"] else "no"),
        ("Failure", page["failure_plain"]["words"] if page.get("failure_plain") else None),
        ("Failure, technical detail", page["failure_plain"]["technical"] if page.get("failure_plain") else None),
        ("Rules lock", f"{cp['rules_lock']['at']}; fingerprint {cp['rules_lock']['fingerprint']}"
         if cp["rules_lock"]["at"] else "not reached"),
        ("Dataset freeze", f"{cp['dataset_freeze']['at']}; {cp['dataset_freeze']['records']} records; fingerprint "
                           f"{cp['dataset_freeze']['fingerprint']}" if cp["dataset_freeze"]["at"] else "not reached"),
        ("Locked plan", json.dumps(plan, sort_keys=True, ensure_ascii=False) if plan else None)]
    for x in page["per_source"]:
        rows.append((f"Result: {x['name']}", f"{x['records']} records, {x['alloys']} alloys, {x['groups']} groups; "
                                              f"{x['result']}; {x['against']}"))
    for x in page["sensitivity"]:
        rows.append((f"Sensitivity: {x['name']}", f"{x['records']} records; {x['result']}; {x['against']}"))
    for v in versions:
        rows.append((f"Source: {v.key}", f"{v.search_status.replace('_', ' ')}; version {v.label or '—'}; "
                                         f"fingerprint {v.fingerprint or '—'}"))
    for s in page["stages"]:
        rows.append((f"Stage: {s['name']} (attempt {s['attempt']})", f"{s['status']}; model {s['model'] or '—'}; "
                     f"{s['calls']} calls; {s['input_tokens']} input and {s['output_tokens']} output tokens; {s['cost']}"))
    c = page["cost"]
    rows += [("Total", f"{c['calls_words']}; {c['input_tokens']} input and {c['output_tokens']} output tokens; "
                       f"reported {c['reported']}; counted toward the caps {c['counted']}"),
             ("Agent mode", head.agent_mode.replace("_", " ")),
             ("Agent settings versions", "; ".join(f"{r.role} {r.version}" for r in settings) or None),
             ("Dispatched (UTC)", head.queued), ("Started (UTC)", head.started), ("Ended (UTC)", head.ended)]
    return rows


def _significance(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
    page = run_view.run_page_in(conn, run_id)
    st = page["statement"]
    rows = [("Results statement (written by code)", line) for line in st["body"] + st["cautions"] + st["format"]]
    if not rows:
        rows.append(("Results statement (written by code)", "None: the run did not complete."))
    stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND status = "
                              "'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none() or {}
    pooled = next((a for a in stats.get("analyses") or [] if a.get("scope") == "pooled"), None)
    for method, c in sorted(((pooled or {}).get("calibration") or {}).items()):
        if c.get("status") != "computed":
            rows.append((f"Calibration ({method})", f"unavailable: {str(c.get('reason') or '').replace('_', ' ')}"))
            continue
        rows.append((f"Calibration ({method})",
                     f"no effect: significant in {c['null']['significant']} of {c['n_simulations']} "
                     f"({c['null']['share']:.4f}; 95% interval {c['null']['ci_low']:.4f} to {c['null']['ci_high']:.4f}); "
                     f"smallest effect that matters: {c['effect']['share']:.4f}; flag: "
                     f"{(c.get('flag_wording') or c.get('confidence_flag') or 'none')}; seed {c.get('seed')}"))
        rows.append((f"Calibration assumptions ({method})", json.dumps(c.get("assumptions"), sort_keys=True,
                                                                         ensure_ascii=False)))
    if not pooled:
        rows.append(("Calibration", "unavailable: no dataset was frozen" if page["checkpoints"]["dataset_freeze"]["at"]
                     is None else "unavailable"))
    rows.append(("Commentary", COMMENTARY_NONE))
    analyst = page.get("analyst") or {}
    if analyst.get("text"):
        rows.append(("Explanation by the Analyst", f"[{analyst['label']}] {analyst['text']}"))
    return rows


def _dispatched(conn: Connection, run_id: int) -> datetime:
    t = conn.execute(text("SELECT queued_at FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
    return t.astimezone(timezone.utc).replace(tzinfo=None)


def build(engine: Engine, run_id: int) -> bytes | None:
    """The workbook (.xlsx) of a run, or None for an unknown run."""
    from openpyxl import Workbook
    with snapshot(engine) as conn:
        if conn.execute(text("SELECT 1 FROM run WHERE id = :r"), dict(r=run_id)).scalar() is None:
            return None
        records, columns = _records(conn, run_id)
        significance, summary, when = _significance(conn, run_id), _summary(conn, run_id), _dispatched(conn, run_id)
    wb = Workbook()
    wb.remove(wb.active)
    used = [r for r in records if r["_used"]]
    other = [r for r in records if not r["_used"]]
    for title, rows, extra in ((SHEETS[0], used, ()), (SHEETS[1], other, ("eligible", "rule", "flags",
                                                                           "sensitivity sets"))):
        ws = wb.create_sheet(title)
        ws.append([version_line()])
        ws.append([*columns, *extra])
        for r in rows:
            ws.append([r.get(c) for c in (*columns, *extra)])
    for title, rows in ((SHEETS[2], significance), (SHEETS[3], summary)):
        ws = wb.create_sheet(title)
        ws.append([version_line()])
        ws.append(["Item", "Value"])
        for item, value in rows:
            ws.append([item, value])
    wb.properties.created = wb.properties.modified = when
    wb.properties.creator = "HypoCurate"
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def records_csv(engine: Engine, run_id: int) -> str | None:
    """Every record the run found, one row each, with whether it was used in the test."""
    with snapshot(engine) as conn:
        if conn.execute(text("SELECT 1 FROM run WHERE id = :r"), dict(r=run_id)).scalar() is None:
            return None
        records, columns = _records(conn, run_id)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow([f"# {version_line()}"])
    header = [*columns, "used in the test", "eligible", "rule", "flags", "sensitivity sets"]
    w.writerow(header)
    for r in records:
        w.writerow([r.get(c) if c != "used in the test" else ("yes" if r["_used"] else "no") for c in header])
    return buf.getvalue()
