"""The extraction workbook (Sprint 2 pilot, R12 first part): every S0 candidate of one paper with its provenance, so a
reviewer can open the PDF and find each value and each link. One row per candidate observation:

- source document: DOI, the stored PDF's SHA-256, how it was fetched (by program / by hand, by whom, from where);
- for grain size and yield strength: the value and unit as written, the provenance (page, table and row, or sentence;
  the snippet), whether it resolves in the stored parse, and any ambiguity note;
- link provenance: the grain size - yield strength link's kind, provenance and note;
- extraction method: name, version, model, prompt version, the S0 snapshot and its hashes;
- against the compilation: 'matched compilation record <key>' or the scorer's class (pending adjudication, duplicate,
  values from different specimens, cited row marked).

Every text cell is a string cell, never a formula (Sprint 1's rule, `pipeline.workbook._append`). Built on request from
stored rows; nothing is written back."""
from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import text
from sqlalchemy.engine import Engine

from hypocurate.pipeline.extraction import provenance as pv
from hypocurate.pipeline.extraction.interface import ParsedDocument, Provenance
from hypocurate.pipeline.workbook import _append

COLUMNS = ("observation", "reported_from", "source_document", "pdf_sha256", "fetched",
           "alloy", "processing_state", "test_type", "test_temperature",
           "grain_size", "grain_size_unit", "grain_size_provenance", "grain_size_resolves", "grain_size_note",
           "yield_strength", "yield_strength_unit", "yield_strength_provenance", "yield_strength_resolves",
           "yield_strength_note", "link_kind", "link_provenance", "link_note",
           "extraction_method", "snapshot", "against_compilation")


def _where(p: dict | None) -> str:
    if not p:
        return ""
    place = (f"p. {p['page']}, table {p['table_index']}, row {p['row_index']}" if p.get("table_index") is not None
             else f"p. {p['page']}, sentence: {p.get('sentence', '')}")
    return f"{place}; snippet: {p['snippet']}"


def _resolves(document: ParsedDocument, p: dict | None) -> str:
    if not p:
        return "no provenance"
    try:
        why = pv.problem(document, Provenance(p["page"], p["snippet"], p.get("table_index"), p.get("row_index"),
                                              p.get("sentence")))
    except ValueError as e:
        return f"no: {e}"
    return "yes" if why is None else f"no: {why}"


def build(engine: Engine, output_id: int, against: dict[str, str] | None = None) -> bytes:
    """The workbook for one verified extraction output. `against`: per observation ref ('obs:<id>'), the scorer's
    result against the compilation."""
    against = against or {}
    with engine.connect() as conn:
        out = conn.execute(text(
            "SELECT x.method, x.document_parse_id, d.doi, d.pdf_sha256, d.by_hand, d.fetched_by, d.oa_url, s.id AS snap, "
            "s.events_sha256, s.raw_sha256 FROM extraction_output x JOIN document_parse p ON p.id = x.document_parse_id "
            "JOIN document d ON d.id = p.document_id JOIN evidence_snapshot s ON s.extraction_output_id = x.id "
            "AND s.name = 'S0' WHERE x.id = :x"), dict(x=output_id)).one()
        document = ParsedDocument.load(conn, out.document_parse_id)
        observations = conn.execute(text("SELECT id, identity FROM candidate_observation WHERE extraction_output_id = :x "
                                         "ORDER BY item_index"), dict(x=output_id)).all()
        values = conn.execute(text("SELECT observation_id, field, value_text, unit, provenance, ambiguity_note FROM "
                                   "candidate_value WHERE observation_id = ANY(:o)"),
                              dict(o=[o.id for o in observations])).all()
        links = conn.execute(text(
            "SELECT l.observation_id, l.kind, l.provenance, l.ambiguity_note FROM extraction_link l JOIN candidate_value a "
            "ON a.id = l.from_value_id JOIN candidate_value b ON b.id = l.to_value_id WHERE l.observation_id = ANY(:o) "
            "AND ARRAY[a.field, b.field] <@ ARRAY['grain_size', 'yield_strength'] AND a.field <> b.field"),
            dict(o=[o.id for o in observations])).all()
    by_obs: dict = {}
    for v in values:
        by_obs.setdefault(v.observation_id, {})[v.field] = v
    link_of = {l.observation_id: l for l in links}
    m = out.method
    method = f"{m.get('name')} {m.get('version')}; {m.get('model')}; prompts {m.get('prompt_version')}; {m.get('step')}"
    snapshot = f"S0 #{out.snap}; events {out.events_sha256[:16]}…; raw {out.raw_sha256[:16]}…"
    fetched = f"by hand by {out.fetched_by} from {out.oa_url}" if out.by_hand else f"by program from {out.oa_url}"
    wb = Workbook()
    ws = wb.active
    ws.title = "Extracted (S0)"
    _append(ws, COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"
    for o in observations:
        v = by_obs.get(o.id, {})
        ident = o.identity
        get = lambda f, attr: getattr(v[f], attr) if f in v else None  # noqa: E731
        link = link_of.get(o.id)
        _append(ws, [
            f"obs:{o.id}", ident.get("reported_from", "this paper"), out.doi, out.pdf_sha256, fetched,
            get("alloy", "value_text"), get("processing_state", "value_text"), get("test_type", "value_text"),
            get("test_temperature", "value_text"),
            get("grain_size", "value_text"), get("grain_size", "unit"), _where(get("grain_size", "provenance")),
            _resolves(document, get("grain_size", "provenance")) if "grain_size" in v else "",
            get("grain_size", "ambiguity_note"),
            get("yield_strength", "value_text"), get("yield_strength", "unit"),
            _where(get("yield_strength", "provenance")),
            _resolves(document, get("yield_strength", "provenance")) if "yield_strength" in v else "",
            get("yield_strength", "ambiguity_note"),
            link.kind if link else "no link", _where(link.provenance) if link else "", link.ambiguity_note if link else "",
            method, snapshot, against.get(f"obs:{o.id}", "not scored")])
    readme = wb.create_sheet("Read me")
    for line in (__doc__ or "").splitlines():
        _append(readme, [line])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def against_compilation(score_report: dict, table: str = "vs compilation (MPEA)") -> dict[str, str]:
    """Per prediction ref, the scorer's result against the compilation, from `score.report`."""
    out = {}
    for key, pairs in score_report["pairs"].items():
        if key.startswith(table):
            for p in pairs:
                out[p["prediction"]] = f"matched compilation record {p['reference'].removeprefix('cmp:')}"
    for key, lists in score_report["unmatched"].items():
        if key.startswith(table):
            for name, refs in lists.items():
                for ref in refs:
                    out[ref] = name.replace("_", " ")
    return out
