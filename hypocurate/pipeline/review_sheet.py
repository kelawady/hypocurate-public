"""The owner's review sheet (Sprint 2 pilot, R5 and R10; owner, 2026-10-23, register 'pilot_review_sheet').

Export: one .xlsx over the v4 S0s (owner, 2026-10-23) with four sheets:
- 'Proposals': every open item the owner must decide, sorted by paper, then page, table and row: the Reconciler's
  mappings in state 'proposed' or 'unresolved', and every link that is not a same-table-row link (Table 3: such a link
  is accepted only by the owner). Each row: the item's reference, the observation it belongs to, the item as written,
  what is proposed, the quote or provenance, code's check, and three cells for the owner: decision (accept / reject /
  correct), corrected value, reason.
- 'Corrections': the owner's corrections of values as read (R10), one per row: the observation, the field, the corrected
  value, its unit and the reason. Each becomes a `value_correction`; the value as read is never changed.
- 'Findings': the owner's Auditor findings, one per row: the item's reference, the finding (FINDING_KINDS) and its
  consequence from the design's Table 2 (CONSEQUENCES), with a sentence.
- 'Repair candidates': observations with a context field (test type or temperature) not stated, for the repair trace.
- 'Minutes': the owner's minutes per paper (P9).
Load: the file is stored with its hash (`review_file`); each decision becomes a state event by the owner: accept ->
'accepted'; reject -> 'disputed'; correct -> 'accepted' with the corrected value in the reason (a mapping or link
holds no value of its own; the proposal as made stays where it is); each correction a `value_correction`; each finding an `auditor_finding`; each minutes row an `owner_time_log`. A file with any unreadable row
is refused whole, listing every problem."""
from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.models import CONSEQUENCES, FINDING_KINDS, TIME_ACTIVITIES
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.workbook import _append

PROMPT_VERSION = "v4"  # the owner's decision of 2026-10-23: the Reconciler, R6 and the H1 runs use v4 S0s only
DECISIONS = ("accept", "reject", "correct")
PROPOSAL_COLUMNS = ("item", "paper_doi", "location", "observation", "item_type", "as_written", "proposed",
                    "quote_or_provenance", "code_check", "decision", "corrected_value", "reason")
CORRECTION_COLUMNS = ("observation", "field", "corrected_value", "unit", "reason")
FINDING_COLUMNS = ("item", "finding", "consequence", "detail")
REPAIR_COLUMNS = ("item", "paper_doi", "observation", "missing", "location")
MINUTE_COLUMNS = ("paper_doi", "activity", "minutes")
_ITEM = re.compile(r"^(mapping|link|observation):(\d+)$")


def outputs(conn: Connection, prompt_version: str | None = None) -> list:
    """The newest S0 output of every paper under the prompt version (v4 for the owner's sheet)."""
    return conn.execute(text(
        "SELECT DISTINCT ON (d.doi_key) d.doi_key, x.id FROM extraction_output x "
        "JOIN document_parse p ON p.id = x.document_parse_id JOIN document d ON d.id = p.document_id "
        "JOIN evidence_snapshot s ON s.extraction_output_id = x.id AND s.name = 'S0' "
        "WHERE x.method->>'prompt_version' = :v ORDER BY d.doi_key, x.id DESC"), dict(v=prompt_version or PROMPT_VERSION)).all()


def _newest_state(conn: Connection, kind: str, object_id: int) -> str:
    return conn.execute(text("SELECT state FROM evidence_state_event WHERE object_kind = :k AND object_id = :o "
                             "ORDER BY id DESC LIMIT 1"), dict(k=kind, o=object_id)).scalar()


def _where(p: dict | None) -> tuple:
    if not p:
        return (9999, 9999, 9999, "")
    if p.get("table_index") is not None:
        return (p["page"], p["table_index"], p["row_index"], f"p. {p['page']}, table {p['table_index']}, row {p['row_index']}")
    kind = "passage" if p.get("passage") else "sentence"
    return (p["page"], 9998, 0, f"p. {p['page']}, {kind}: {p.get('sentence', '')[:120]}")


def _observation(conn: Connection, obs_id: int | None) -> tuple[str, tuple]:
    if obs_id is None:
        return "", (9999, 9999, 9999, "")
    vals = {r.field: r for r in conn.execute(text("SELECT field, value_text, unit, provenance FROM candidate_value "
                                                  "WHERE observation_id = :o"), dict(o=obs_id)).all()}
    show = lambda f: f"{vals[f].value_text}{' ' + vals[f].unit if vals[f].unit else ''}" if f in vals else "—"  # noqa
    summary = (f"obs:{obs_id} | {show('alloy')} | {show('processing_state')} | d {show('grain_size')} | "
               f"YS {show('yield_strength')}")
    anchor = next((vals[f].provenance for f in ("yield_strength", "grain_size") if f in vals and vals[f].provenance), None)
    return summary, _where(anchor)


def export(engine: Engine, prompt_version: str | None = None) -> bytes:
    rows, repair = [], []
    with engine.connect() as conn:
        for doi_key, out in outputs(conn, prompt_version):
            doi = doi_key.removeprefix("doi:")
            for m in conn.execute(text("SELECT id, observation_id, kind, subject, proposed, applied, quote, compilation_key "
                                       "FROM reconciler_mapping WHERE extraction_output_id = :x ORDER BY id"),
                                  dict(x=out)).all():
                if _newest_state(conn, "mapping", m.id) not in ("proposed", "unresolved"):
                    continue
                summary, where = _observation(conn, m.observation_id)
                proposed = json.dumps(m.proposed, ensure_ascii=False) + (f" record {m.compilation_key}" if m.compilation_key else "")
                rows.append((doi, where, [f"mapping:{m.id}", doi, where[3], summary, m.kind, m.subject, proposed,
                                          m.quote or "", json.dumps(m.applied, ensure_ascii=False), "", "", ""]))
            for l in conn.execute(text(
                    "SELECT l.id, l.observation_id, l.kind, l.provenance, l.ambiguity_note, a.field AS af, b.field AS bf "
                    "FROM extraction_link l JOIN candidate_observation o ON o.id = l.observation_id "
                    "JOIN candidate_value a ON a.id = l.from_value_id JOIN candidate_value b ON b.id = l.to_value_id "
                    "WHERE o.extraction_output_id = :x AND (l.kind IS DISTINCT FROM 'same_table_row' OR l.ambiguous) "
                    "ORDER BY l.id"), dict(x=out)).all():
                if _newest_state(conn, "link", l.id) not in ("proposed", "unresolved", "supported"):
                    continue
                summary, where = _observation(conn, l.observation_id)
                lw = _where(l.provenance)
                rows.append((doi, lw if l.provenance else where,
                             [f"link:{l.id}", doi, (lw if l.provenance else where)[3], summary, "link",
                              f"{l.af} - {l.bf} ({l.kind or 'no kind'})", "accept as one observation",
                              (l.provenance or {}).get("snippet", "") or (l.ambiguity_note or ""), "", "", "", ""]))
            for o in conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x "
                                       "ORDER BY item_index"), dict(x=out)).scalars():
                vals = dict(conn.execute(text("SELECT field, value_text FROM candidate_value WHERE observation_id = :o"),
                                         dict(o=o)).all())
                missing = [f for f in ("test_type", "test_temperature") if not (vals.get(f) or "").strip()]
                if missing:
                    summary, where = _observation(conn, o)
                    repair.append([f"observation:{o}", doi, summary, ", ".join(missing), where[3]])
    rows.sort(key=lambda r: (r[0], r[1][:3]))
    wb = Workbook()
    sheets = [("Proposals", PROPOSAL_COLUMNS, [r[2] for r in rows]), ("Corrections", CORRECTION_COLUMNS, []),
              ("Findings", FINDING_COLUMNS, []),
              ("Repair candidates", REPAIR_COLUMNS, repair),
              ("Minutes", MINUTE_COLUMNS, [[d.removeprefix("doi:"), "review_sheet", ""] for d in sorted({r[0] for r in rows})])]
    for i, (name, columns, data) in enumerate(sheets):
        ws = wb.active if i == 0 else wb.create_sheet(name)
        ws.title = name
        _append(ws, columns)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        ws.freeze_panes = "A2"
        for r in data:
            _append(ws, r)
    readme = wb.create_sheet("Read me")
    for line in (__doc__ or "").splitlines() + ["", "Findings: finding is one of " + ", ".join(FINDING_KINDS) + "; "
                                                "consequence is one of " + ", ".join(CONSEQUENCES) + "."]:
        _append(readme, [line])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class SheetRefused(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("the review sheet is refused: " + "; ".join(problems[:20]))
        self.problems = problems


@dataclass
class Loaded:
    review_file: int
    decisions: int
    corrections: int
    findings: int
    minutes_rows: int


def _rows(wb, name: str, columns: tuple) -> list[tuple[int, dict]]:
    if name not in wb.sheetnames:
        return []
    data = list(wb[name].iter_rows(values_only=True))
    header = tuple(str(c or "").strip() for c in data[0][:len(columns)]) if data else ()
    if header != columns:
        raise SheetRefused([f"sheet '{name}': the columns differ from the export's"])
    return [(i, {c: ("" if v is None else str(v).strip()) for c, v in zip(columns, r)})
            for i, r in enumerate(data[1:], start=2) if any(v not in (None, "") for v in r)]


def _object(conn: Connection, kind: str, oid: int) -> int | None:
    sql = {"mapping": "SELECT extraction_output_id FROM reconciler_mapping WHERE id = :o",
           "observation": "SELECT extraction_output_id FROM candidate_observation WHERE id = :o",
           "link": "SELECT o.extraction_output_id FROM extraction_link l JOIN candidate_observation o "
                   "ON o.id = l.observation_id WHERE l.id = :o"}[kind]
    return conn.execute(text(sql), dict(o=oid)).scalar()


def load(engine: Engine, filename: str, content: bytes, by: str, prompt_version: str | None = None,
         minutes_are_owner_time: bool = True) -> Loaded:
    """`minutes_are_owner_time=False` (owner, 2026-10-23): the Minutes tab is not the owner's time (an AI-assisted
    review) and is not logged; the file is still stored whole with its hash."""
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    proposals, findings = _rows(wb, "Proposals", PROPOSAL_COLUMNS), _rows(wb, "Findings", FINDING_COLUMNS)
    minutes, corrections = _rows(wb, "Minutes", MINUTE_COLUMNS), _rows(wb, "Corrections", CORRECTION_COLUMNS)
    if not minutes_are_owner_time:
        minutes = []
    problems = []
    with engine.connect() as conn:
        plan_events, plan_corrections, plan_findings, plan_minutes = [], [], [], []
        papers = {k for k, _ in outputs(conn, prompt_version)}
        for n, r in proposals:
            d = r["decision"].casefold()
            if not d:
                continue
            m = _ITEM.match(r["item"])
            if d not in DECISIONS:
                problems.append(f"Proposals row {n}: decision {r['decision']!r} is not accept, reject or correct")
            elif not m or m.group(1) == "observation":
                problems.append(f"Proposals row {n}: item {r['item']!r} is not a mapping or link reference")
            elif d == "correct" and not r["corrected_value"]:
                problems.append(f"Proposals row {n}: 'correct' needs a corrected value")
            elif d in ("reject", "correct") and not r["reason"]:
                problems.append(f"Proposals row {n}: '{d}' needs a reason")
            else:
                out = _object(conn, m.group(1), int(m.group(2)))
                if out is None:
                    problems.append(f"Proposals row {n}: no {r['item']}")
                    continue
                state = {"accept": "accepted", "reject": "disputed", "correct": "accepted"}[d]
                reason = (f"corrected: {r['corrected_value']}; " if d == "correct" else "") + r["reason"]
                plan_events.append((m.group(1), int(m.group(2)), out, state, reason or None))
        for n, r in corrections:
            m = _ITEM.match(r["observation"])
            if not m or m.group(1) != "observation":
                problems.append(f"Corrections row {n}: {r['observation']!r} is not a reference like observation:123")
            elif not r["corrected_value"] or not r["reason"]:
                problems.append(f"Corrections row {n}: a correction needs a corrected value and a reason")
            else:
                vid = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = :f"),
                                   dict(o=int(m.group(2)), f=r["field"])).scalar()
                if vid is None:
                    problems.append(f"Corrections row {n}: {r['observation']} has no value {r['field']!r} as read "
                                    "(a value not read is a repair, not a correction)")
                else:
                    plan_corrections.append((vid, r["corrected_value"], r["unit"] or None, r["reason"]))
        for n, r in findings:
            m = _ITEM.match(r["item"])
            if not m:
                problems.append(f"Findings row {n}: item {r['item']!r} is not a reference like observation:123")
            elif r["finding"] not in FINDING_KINDS or r["consequence"] not in CONSEQUENCES:
                problems.append(f"Findings row {n}: finding or consequence not in the lists (see Read me)")
            elif not r["detail"]:
                problems.append(f"Findings row {n}: a finding needs a sentence")
            else:
                out = _object(conn, m.group(1), int(m.group(2)))
                if out is None:
                    problems.append(f"Findings row {n}: no {r['item']}")
                else:
                    plan_findings.append((m.group(1), int(m.group(2)), out, r["finding"], r["consequence"], r["detail"]))
        for n, r in minutes:
            if not r["minutes"]:
                continue
            try:
                mins = float(r["minutes"])
            except ValueError:
                mins = -1.0
            key, activity = "doi:" + r["paper_doi"].casefold(), r["activity"] or "review_sheet"
            if not (mins.is_integer() and 0 <= mins <= 1440):
                problems.append(f"Minutes row {n}: {r['minutes']!r} is not a whole number of minutes from 0 to 1440")
            elif activity not in TIME_ACTIVITIES:
                problems.append(f"Minutes row {n}: activity {activity!r} is not one of " + ", ".join(TIME_ACTIVITIES))
            elif key not in papers:
                problems.append(f"Minutes row {n}: paper {r['paper_doi']!r} is not one of the sheet's papers")
            else:
                plan_minutes.append((key, activity, int(mins)))
    if problems:
        raise SheetRefused(problems)

    def write(conn: Connection) -> Loaded:
        rf = conn.execute(text("INSERT INTO review_file (filename, content, sha256, loaded_by) VALUES (:f, :c, :h, :b) "
                               "RETURNING id"), dict(f=filename, c=content, h=hashlib.sha256(content).hexdigest(),
                                                     b=by)).scalar_one()
        for kind, oid, out, state, reason in plan_events:
            conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                              "by_person, reason) VALUES (:k, :o, :x, :s, :p, :r)"),
                         dict(k=kind, o=oid, x=out, s=state, p=by, r=reason and reason[:2000]))
        for vid, corrected, unit, reason in plan_corrections:
            conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, unit, reason, by_person) "
                              "VALUES (:v, :c, :u, :r, :p)"), dict(v=vid, c=corrected[:2000], u=unit, r=reason[:2000], p=by))
        for kind, oid, out, finding, consequence, detail in plan_findings:
            conn.execute(text("INSERT INTO auditor_finding (object_kind, object_id, extraction_output_id, finding_kind, "
                              "consequence, detail, by_person, review_file_id) VALUES (:k, :o, :x, :f, :c, :d, :p, :rf)"),
                         dict(k=kind, o=oid, x=out, f=finding, c=consequence, d=detail[:2000], p=by, rf=rf))
        for doi_key, activity, mins in plan_minutes:
            conn.execute(text("INSERT INTO owner_time_log (doi_key, activity, minutes, review_file_id, logged_by) "
                              "VALUES (:k, :a, :m, :rf, :p)"), dict(k=doi_key, a=activity, m=mins, rf=rf, p=by))
        return Loaded(rf, len(plan_events), len(plan_corrections), len(plan_findings), len(plan_minutes))
    return run_transaction(engine, write)
