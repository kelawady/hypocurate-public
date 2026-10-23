"""The H2 evidence inventory (Sprint 2 pilot, PRD v1.2 R11; owner, 2026-10-22, D25/D27; register 'pilot_h2_inventory').

H2: BCC multi-principal-element alloys at >= 800 °C, tension and compression both recorded; the qualifying grain size
is either type, recorded per record (as-processed, or at or after the test temperature). No analysis runs: the status
is STATUS. Built on request from stored rows only, for the page and the workbook:
- per paper of the H2 selection: its compilation records (and how many have a grain size), whether a document was
  obtained, parsed, and read (an H2 S0), and its extracted observations by state;
- the recovered records (observations with a stated grain size and yield strength) with their provenance, grain-size
  type and state;
- the counts by cause for the rest: compilation records lacking a grain size; papers not obtained under the configured
  sources (an open copy listed but not fetched by program, or none listed; stated with the configuration, no
  public/paywalled distinction) or not parsed; observations read with no grain size (or none stated as a number).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Connection

from hypocurate.documents.reach import CONFIGURATION, LISTED_NOT_FETCHED, NOT_OBTAINED
from hypocurate.pipeline import evidence as ev

STATUS = "inventory; analysis deferred to a versioned protocol"
H2_SPEC = "H2 v1"


@dataclass
class Inventory:
    status: str
    papers: list = field(default_factory=list)       # one dict per paper
    recovered: list = field(default_factory=list)    # one dict per observation with grain size and yield strength
    causes: dict = field(default_factory=dict)       # cause -> count (with its unit in the key)
    by_state: dict = field(default_factory=dict)     # (state, grain-size type) -> count
    totals: dict = field(default_factory=dict)


def _where(p: dict | None) -> str:
    from hypocurate.sources.pilot import _where as where
    return where(p)


def build(conn: Connection) -> Inventory:
    from hypocurate.documents.select import bcc_high_temperature
    from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
    selection = bcc_high_temperature(load_sealed_version(conn, latest_sealed_version_id(conn, "mpea")))
    outputs = dict(ev.standing_outputs(conn, spec=H2_SPEC))
    statuses = {s.observation_id: s for s in ev.status(conn, sorted(outputs.items()))} if outputs else {}
    world = ev._load(conn, sorted(outputs.items())) if outputs else None  # R6's own reading of the stated values
    inv = Inventory(STATUS)
    causes = {"compilation records lacking a grain size": 0, f"papers {LISTED_NOT_FETCHED}": 0,
              f"papers {NOT_OBTAINED}, no open copy listed": 0, "papers not parsed": 0,
              "papers obtained and parsed, not read (no H2 extraction)": 0,
              "observations read with no grain size stated as a number": 0,
              "observations read with no yield strength stated as a number": 0}
    for p in selection.papers:
        docs = conn.execute(text("SELECT d.id, (SELECT count(*) FROM document_parse x WHERE x.document_id = d.id AND "
                                 "x.status = 'parsed') AS parsed FROM document d WHERE d.doi_key = :k AND d.kind = "
                                 "'article'"), dict(k=p.doi_key)).all()
        oa = conn.execute(text("SELECT detail FROM search_log WHERE doi_key = :k AND action = 'select' AND detail LIKE "
                               "'lookup summary: %' ORDER BY id DESC LIMIT 1"), dict(k=p.doi_key)).scalar() or ""
        oa_flag = bool(json.loads(oa.removeprefix("lookup summary: ")).get("is_oa")) if oa else False
        out = outputs.get(p.doi_key)
        row = {"doi": p.doi, "compilation_records": p.records, "with_yield_strength": p.records_with_yield_strength,
               "with_grain_size": p.records_with_grain_size, "open_access_flag": oa_flag, "obtained": bool(docs),
               "parsed": any(d.parsed for d in docs), "read": out is not None, "observations": 0, "recovered": 0}
        causes["compilation records lacking a grain size"] += p.records - p.records_with_grain_size
        if not docs:
            causes[f"papers {LISTED_NOT_FETCHED}" if oa_flag else
                   f"papers {NOT_OBTAINED}, no open copy listed"] += 1
        elif not row["parsed"]:
            causes["papers not parsed"] += 1
        elif out is None:
            causes["papers obtained and parsed, not read (no H2 extraction)"] += 1
        if out is not None:
            for o in conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x ORDER BY "
                                       "item_index"), dict(x=out)).scalars():
                row["observations"] += 1
                vals = {v.field: v for v in conn.execute(text(
                    "SELECT field, value_text, unit, provenance FROM candidate_value WHERE observation_id = :o"),
                    dict(o=o)).all()}
                st = statuses.get(o)
                gs_ok = ev._stated(world, o, "grain_size")[0]
                ys_ok = ev._stated(world, o, "yield_strength")[0]
                if not gs_ok:
                    causes["observations read with no grain size stated as a number"] += 1
                elif not ys_ok:
                    causes["observations read with no yield strength stated as a number"] += 1
                gtype = (vals["grain_size_type"].value_text if "grain_size_type" in vals else "not recorded")
                state = st.category if st else "proposed"
                inv.by_state[(state, gtype)] = inv.by_state.get((state, gtype), 0) + 1
                if gs_ok and ys_ok:
                    row["recovered"] += 1
                    show = lambda f: (f"{vals[f].value_text} {vals[f].unit or ''}".strip() if f in vals else "")  # noqa
                    inv.recovered.append({
                        "observation": o, "doi": p.doi, "alloy": show("alloy"), "grain_size": show("grain_size"),
                        "grain_size_type": gtype, "yield_strength": show("yield_strength"),
                        "test_type": show("test_type"), "test_temperature": show("test_temperature"), "state": state,
                        "reason": st.reason if st else "", "grain_size_provenance": _where(vals["grain_size"].provenance),
                        "yield_strength_provenance": _where(vals["yield_strength"].provenance)})
        inv.papers.append(row)
    inv.causes = causes
    inv.totals = {"configuration": CONFIGURATION, "papers": len(selection.papers), "compilation_records": selection.records,
                  "papers_obtained": sum(r["obtained"] for r in inv.papers),
                  "papers_parsed": sum(r["parsed"] for r in inv.papers), "papers_read": sum(r["read"] for r in inv.papers),
                  "observations": sum(r["observations"] for r in inv.papers), "recovered": len(inv.recovered)}
    return inv


def workbook(inv: Inventory) -> bytes:
    import io
    from openpyxl import Workbook
    from hypocurate.pipeline.workbook import _append, version_line
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    _append(ws, [version_line()])
    _append(ws, ["H2 evidence inventory", STATUS])
    for k, v in inv.totals.items():
        _append(ws, [k.replace("_", " "), v])
    _append(ws, [])
    _append(ws, ["Cause", "Count"])
    for k, v in inv.causes.items():
        _append(ws, [k, v])
    _append(ws, [])
    _append(ws, ["State", "Grain-size type", "Observations"])
    for (s, t), n in sorted(inv.by_state.items()):
        _append(ws, [s, t, n])
    sheets = (("Papers", ("doi", "compilation_records", "with_yield_strength", "with_grain_size", "open_access_flag",
                          "obtained", "parsed", "read", "observations", "recovered"), inv.papers),
              ("Recovered records", ("observation", "doi", "alloy", "grain_size", "grain_size_type", "yield_strength",
                                     "test_type", "test_temperature", "state", "reason", "grain_size_provenance",
                                     "yield_strength_provenance"), inv.recovered))
    for title, cols, rows in sheets:
        w = wb.create_sheet(title)
        _append(w, [version_line()])
        _append(w, list(cols))
        for r in rows:
            _append(w, [("yes" if r[c] is True else "no" if r[c] is False else r[c]) for c in cols])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
