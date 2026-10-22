"""S0, the reference-blind snapshot (PRD v1.2 Section 4; owner, 2026-10-22, register 'snapshot_definitions'): the
Extractor's output per document, stored and frozen with its hash in one transaction, before any compilation
matching, acceptance or correction. Nothing that uses the compilation (R-link-1, R-rereport) imports this module or
writes these rows; the database refuses any other state event on the output's objects before its S0 exists, and any
new candidate after it.

What is stored: the raw output exactly as returned (with its SHA-256); one candidate observation per record, with its
identity computed by code (`extraction.identity`); each value as written and each link, with its provenance or an
explicit ambiguity marker; one 'proposed' event by the rule 'extraction' for every observation and link; and the S0
snapshot listing exactly those events, the time and the raw hash. A value or link the Extractor returned with neither
a provenance nor an ambiguity note is stored as ambiguous with the note `NO_PROVENANCE`: an explicit, code-written
marker (the raw output keeps what was returned), never a silent repair."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.models import EXTRACTION_RULE
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.extraction.identity import identity
from hypocurate.pipeline.extraction.interface import CandidateRecord, ExtractionResult, ParsedDocument

NO_PROVENANCE = "the extractor gave no provenance and no ambiguity note"
TAKEN_BY = "code"
IDENTITY_FIELDS = ("alloy", "composition", "processing_state", "test_type", "test_temperature", "specimen_label")


@dataclass(frozen=True)
class Frozen:
    output_id: int
    snapshot_id: int
    raw_sha256: str
    events_sha256: str
    observations: int


def record_identity(document: ParsedDocument, record: CandidateRecord, index: int):
    """The record's identity: its own fields; its location is the yield strength's provenance, else the grain size's,
    else 'unlocated item <n>' (an output-local identifier, never matching another output's)."""
    get = lambda f: record.value(f).text if record.value(f) else None
    located = next((record.value(f).provenance for f in ("yield_strength", "grain_size")
                    if record.value(f) and record.value(f).provenance), None)
    location = located.location if located else f"unlocated item {index}"
    temp = record.value("test_temperature")
    return identity(document.doi_key, get("alloy"), get("processing_state"), get("test_type"), get("test_temperature"),
                    get("specimen_label"), location, composition=get("composition"),
                    test_temperature_unit=temp.unit if temp else None)


def _jsonb(value) -> str | None:
    return None if value is None else json.dumps(value, sort_keys=True)


def _store(conn: Connection, document: ParsedDocument, result: ExtractionResult) -> Frozen:
    raw_sha = hashlib.sha256(result.raw_output.encode("utf-8")).hexdigest()
    out = conn.execute(text(
        "INSERT INTO extraction_output (document_parse_id, parse_sha256, method, status, raw_output, raw_sha256, "
        "invocation_id) VALUES (:p, :h, CAST(:m AS jsonb), :s, :r, :rh, :i) RETURNING id"),
        dict(p=document.parse_id, h=document.parse_sha256, m=_jsonb(result.method.to_json()), s=result.status,
             r=result.raw_output, rh=raw_sha, i=result.invocation_id)).scalar_one()
    for index, record in enumerate(result.records):
        ident = record_identity(document, record, index)
        obs = conn.execute(text(
            "INSERT INTO candidate_observation (extraction_output_id, item_index, identity, identity_key) "
            "VALUES (:x, :i, CAST(:d AS jsonb), :k) RETURNING id"),
            dict(x=out, i=index, d=_jsonb(ident.to_json()), k=ident.key)).scalar_one()
        value_ids = {}
        for v in record.values:
            note = v.ambiguity_note or (NO_PROVENANCE if v.provenance is None else None)
            value_ids[v.field] = conn.execute(text(
                "INSERT INTO candidate_value (observation_id, field, value_text, value_number, unit, definition, "
                "provenance, ambiguous, ambiguity_note) VALUES (:o, :f, :t, :n, :u, :d, CAST(:p AS jsonb), :a, :note) "
                "RETURNING id"),
                dict(o=obs, f=v.field, t=v.text, n=v.number, u=v.unit, d=v.definition,
                     p=_jsonb(v.provenance.to_json(document.document_id, document.parse_sha256)) if v.provenance else None,
                     a=note is not None, note=note)).scalar_one()
        conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                          "by_rule) VALUES ('observation', :o, :x, 'proposed', :r)"), dict(o=obs, x=out, r=EXTRACTION_RULE))
        for link in record.links:
            if link.from_field not in value_ids or link.to_field not in value_ids:
                raise ValueError(f"record {index}: a link names a value the record does not have "
                                 f"({link.from_field} - {link.to_field})")
            note = link.ambiguity_note or (NO_PROVENANCE if link.provenance is None or link.kind is None else None)
            lid = conn.execute(text(
                "INSERT INTO extraction_link (observation_id, from_value_id, to_value_id, kind, provenance, ambiguous, "
                "ambiguity_note) VALUES (:o, :a, :b, :k, CAST(:p AS jsonb), :amb, :note) RETURNING id"),
                dict(o=obs, a=value_ids[link.from_field], b=value_ids[link.to_field], k=link.kind,
                     p=_jsonb(link.provenance.to_json(document.document_id, document.parse_sha256))
                     if link.provenance else None, amb=note is not None, note=note)).scalar_one()
            conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                              "by_rule) VALUES ('link', :l, :x, 'proposed', :r)"), dict(l=lid, x=out, r=EXTRACTION_RULE))
    ids = conn.execute(text("SELECT id FROM evidence_state_event WHERE extraction_output_id = :x ORDER BY id"),
                       dict(x=out)).scalars().all()
    events_sha = hashlib.sha256(",".join(map(str, ids)).encode("utf-8")).hexdigest()
    snap = conn.execute(text(
        "INSERT INTO evidence_snapshot (name, extraction_output_id, raw_sha256, event_ids, events_sha256, taken_by) "
        "VALUES ('S0', :x, :h, CAST(:ids AS bigint[]), :eh, :by) RETURNING id"),
        dict(x=out, h=raw_sha, ids="{" + ",".join(map(str, ids)) + "}", eh=events_sha, by=TAKEN_BY)).scalar_one()
    return Frozen(out, snap, raw_sha, events_sha, len(result.records))


def store_and_freeze(engine: Engine, document: ParsedDocument, result: ExtractionResult) -> Frozen:
    """Stores one extraction output and freezes its S0, in one transaction."""
    return run_transaction(engine, lambda conn: _store(conn, document, result))
