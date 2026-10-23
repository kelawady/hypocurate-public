"""The 'extracted (pilot)' source (Sprint 2 pilot, PRD v1.2 R9; owner, 2026-10-23, register 'pilot_extracted_source').

A sealed source version built from the R6 freeze, never from data/: one CSV with every accepted extracted record
(the primary set's new records and the re-reports, flagged), and `documentation/freeze.txt` with the S2 snapshot,
its events hash, the accepted record ids and the R-rereport flags. Code builds every value from the stored candidate
values (after loaded corrections) and the mappings a person accepted; nothing a model wrote is read except through
those accepted objects. Its definition is kept apart from Sprint 1's `SOURCES`, so registering Sprint 1's sources
(and their tests) is unchanged; `register_frozen` registers and seals it with Sprint 1's registration function.

In a pooled run, a re-report is counted once by Sprint 1's own checks and inclusion: same paper, same alloy, values
within tolerance -> exact duplicate -> 'duplicate counted once', the MPEA record surviving (the survivor order puts
this source last)."""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.retry import run_transaction
from hypocurate.sources.versions import Registered, SourceDefinition, _register_in

KEY = "extracted_pilot"
DATA_FILE = "extracted_pilot.csv"
FREEZE_FILE = "documentation/freeze.txt"
DEFINITION = SourceDefinition(
    key=KEY, name="Extracted records (Sprint 2 pilot)", source_type="paper_search", data_kind="measured",
    grouping_unit="paper", licence="extracted from the cited papers; the papers are not redistributed", address=None,
    properties_covered=("yield_strength", "grain_size"), enabled=True, directory="", data_files=(DATA_FILE,),
    version_label="pilot freeze", manifest_section=(), documentation_files=(FREEZE_FILE,))
COLUMNS = ("record_key", "paper_doi", "alloy_as_written", "composition_formula", "composition_quote",
           "grain_size_um", "grain_size_as_written", "grain_size_provenance",
           "yield_strength_mpa", "yield_strength_as_written", "yield_strength_provenance",
           "test_type", "test_type_quote", "test_temperature_c", "test_temperature_as_written",
           "test_temperature_band", "test_temperature_band_quote", "phase", "phase_quote", "processing_state",
           "document_sha256", "rereport_of", "values_agree", "qualifiers")
_TEMPERATURE = re.compile(r"^\s*[~∼≈]?\s*(-?\d+(?:\.\d+)?)\s*(K|°C|ºC|C)\s*$")


def temperature_c(written: str | None) -> Decimal | None:
    """A single stated temperature in K or °C, in °C; None for anything else (a list, 'room temperature')."""
    m = _TEMPERATURE.match(written or "")
    if not m:
        return None
    v = Decimal(m.group(1))
    return v - Decimal("273.15") if m.group(2) == "K" else v


def plain(d: Decimal) -> str:
    """A number in plain notation without trailing zeros ('20', not '2E+1')."""
    t = format(d, "f")
    return t.rstrip("0").rstrip(".") if "." in t else t


def _where(p: dict | None) -> str:
    if not p:
        return ""
    if p.get("table_index") is not None:
        return f"p. {p['page']}, table {p['table_index']}, row {p['row_index']}"
    return f"p. {p['page']}, {'passage' if p.get('passage') else 'sentence'}: {(p.get('sentence') or '')[:200]}"


def _rows(conn: Connection, accepted: list) -> list[dict]:
    from hypocurate.pipeline.extraction.identity import test_type_key
    from hypocurate.scoring.score import quantity
    rows = []
    for st in accepted:
        o = st.observation_id
        doc = conn.execute(text("SELECT d.doi, d.pdf_sha256 FROM candidate_observation c JOIN extraction_output x ON "
                                "x.id = c.extraction_output_id JOIN document_parse p ON p.id = x.document_parse_id "
                                "JOIN document d ON d.id = p.document_id WHERE c.id = :o"), dict(o=o)).one()
        vals = {}
        for v in conn.execute(text("SELECT v.id, v.field, v.value_text, v.unit, v.provenance, c.corrected_text, "
                                   "c.unit AS c_unit FROM candidate_value v LEFT JOIN LATERAL (SELECT corrected_text, "
                                   "unit FROM value_correction WHERE value_id = v.id ORDER BY id DESC LIMIT 1) c ON true "
                                   "WHERE v.observation_id = :o"), dict(o=o)).all():
            vals[v.field] = v
        maps = conn.execute(text(
            "SELECT m.kind, m.proposed, m.quote FROM reconciler_mapping m WHERE m.observation_id = :o AND (SELECT e.state "
            "FROM evidence_state_event e WHERE e.object_kind = 'mapping' AND e.object_id = m.id ORDER BY e.id DESC "
            "LIMIT 1) = 'accepted' ORDER BY m.id"), dict(o=o)).all()

        def mapped(kind: str, fld: str | None = None):
            return next((m for m in maps if m.kind == kind and (fld is None or (m.proposed or {}).get("field") == fld)),
                        None)

        def written(f: str) -> tuple[str, str | None]:
            v = vals.get(f)
            if v is None:
                return "", None
            return (v.corrected_text or v.value_text), (v.c_unit if v.corrected_text else v.unit)
        num = {}
        for f in ("grain_size", "yield_strength"):
            t, u = written(f)
            q = quantity(f, t, u)
            num[f] = (plain(q.low) if q.kind == "number" else "", f"{t} {u or ''}".strip())
        alias, tt, band, phase = (mapped("alias_to_composition"), mapped("condition_to_category", "test_type"),
                                  mapped("condition_to_category", "test_temperature_band"),
                                  mapped("condition_to_category", "phase"))
        t_text, t_unit = written("test_temperature")
        t_c = temperature_c(f"{t_text} {t_unit or ''}".strip()) if t_text else None
        ty_text, _ = written("test_type")
        rows.append({
            "record_key": f"observation:{o}", "paper_doi": doc.doi, "alloy_as_written": written("alloy")[0],
            "composition_formula": (alias.proposed or {}).get("composition", "") if alias else "",
            "composition_quote": (alias.quote or "") if alias else "",
            "grain_size_um": num["grain_size"][0], "grain_size_as_written": num["grain_size"][1],
            "grain_size_provenance": _where(vals["grain_size"].provenance),
            "yield_strength_mpa": num["yield_strength"][0], "yield_strength_as_written": num["yield_strength"][1],
            "yield_strength_provenance": _where(vals["yield_strength"].provenance),
            "test_type": (tt.proposed or {}).get("category", "") if tt else (
                test_type_key(ty_text) if test_type_key(ty_text) in ("tension", "compression") else ""),
            "test_type_quote": (tt.quote or "") if tt else "",
            "test_temperature_c": "" if t_c is None else plain(t_c),
            "test_temperature_as_written": f"{t_text} {t_unit or ''}".strip(),
            "test_temperature_band": (band.proposed or {}).get("category", "") if band else "",
            "test_temperature_band_quote": (band.quote or "") if band else "",
            "phase": (phase.proposed or {}).get("category", "") if phase else "",
            "phase_quote": (phase.quote or "") if phase else "",
            "processing_state": written("processing_state")[0], "document_sha256": doc.pdf_sha256,
            "rereport_of": st.rereport_of or "", "values_agree": "" if st.values_agree is None else str(st.values_agree),
            "qualifiers": "; ".join(st.qualifiers)})
    return rows


def build_files(conn: Connection, frozen) -> dict[str, bytes]:
    """The version's two files from a freeze (`evidence.Frozen`): the CSV and the freeze record."""
    rows = _rows(conn, sorted(frozen.accepted, key=lambda s: s.observation_id))
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    record = {"s1_snapshot": frozen.s1, "s2_snapshot": frozen.s2, "s2_events_sha256": frozen.events_sha256,
              "accepted_records": [s.observation_id for s in sorted(frozen.accepted, key=lambda s: s.observation_id)],
              "rereport_of": {str(s.observation_id): s.rereport_of for s in frozen.accepted if s.rereport_of},
              "primary_set_new_records": sorted(s.observation_id for s in frozen.primary)}
    return {DATA_FILE: buf.getvalue().encode("utf-8"),
            FREEZE_FILE: (json.dumps(record, indent=1, sort_keys=True) + "\n").encode("utf-8")}


@dataclass(frozen=True)
class Sealed:
    registered: Registered
    files: dict


def register_frozen(engine: Engine, frozen, by: str) -> Sealed:
    """Builds the files from the freeze and registers and seals them as a version of the pilot source (Sprint 1's
    registration: the same digest, identity and seal checks), recorded with the person's name."""
    from hypocurate.db import actions
    actions.actor(by, "command line")

    def body(conn: Connection) -> Sealed:
        files = build_files(conn, frozen)
        done = _register_in(conn, DEFINITION, files, date.today(), f"pilot freeze S2 {frozen.events_sha256[:12]}")
        if done.created:
            actions.record(conn, "register_source", by, "command line", source_version=done.version_id)
        return Sealed(done, files)
    return run_transaction(engine, body)
