"""Storing a run's records after the rules lock (PRD 5.6, 10; build step 6).

For tabular sources the adapters (code) extract the records: each chosen source's sealed
version, recorded for the run at dispatch, is read by its adapter, and every record it
returns is stored in the run, unchanged and in file order, with how it was extracted
(`record.extraction`: method "adapter", the adapter's name and version; owner, 2026-10-05).
Every record found is kept; eligibility is decided later by code (PRD 5.3). What the Curator
agent does for tabular sources is an open owner decision for step 8; this step does not
settle it.

One transaction per source, under the run's lock (`writes.write`). The source's search
status becomes `searched`; an adapter that refuses the file makes it `failed` with the kind of
nothing found `failed_search` (PRD 3.1), and nothing is stored from it. Records of a
constructed source (the controlled duplicate extract) are refused, and the refusal logged,
unless the run is marked as a test (register 'constructed_test_runs').
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.pipeline.writes import Refused, constructed_unmarked, write
from hypocurate.sources import adapters
from hypocurate.sources.record import AdapterError
from hypocurate.sources.versions import UnsealedVersion, load_sealed_version

_INSERT = text(
    "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, alloy, harmonized, "
    "reported, paper_reference, paper_doi, extraction) VALUES (:r, :v, :k, :i, :kind, :a, :h, :rep, :pr, :pd, :x)"
).bindparams(bindparam("h", type_=JSONB), bindparam("rep", type_=JSONB), bindparam("x", type_=JSONB))


def pending_sources(engine: Engine, run_id: int) -> list[str]:
    with engine.connect() as conn:
        return list(conn.execute(text(
            "SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r "
            "AND rs.search_status = 'pending' AND rs.source_version_id IS NOT NULL ORDER BY s.key"),
            dict(r=run_id)).scalars())


def store_source(engine: Engine, run_id: int, source_key: str) -> int:
    """Stores the records of one chosen source; returns how many were stored."""

    def body(conn: Connection, stage: str) -> int:
        if stage != "curation":
            raise Refused("store_records", "stage_mismatch")
        row = conn.execute(text(
            "SELECT rs.source_id, rs.source_version_id, rs.search_status FROM run_source rs "
            "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r AND s.key = :k"),
            dict(r=run_id, k=source_key)).one_or_none()
        if row is None or row.source_version_id is None:
            raise Refused("store_records", "stage_mismatch", "the source is not chosen for this run")
        if row.search_status != "pending":
            raise Refused("store_records", "already_done")
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'checks')"),
                        dict(r=run_id)).scalar_one():
            raise Refused("store_records", "checks_done")
        if constructed_unmarked(conn, run_id, [source_key]):
            raise Refused("store_records", "constructed_data_unmarked")
        try:
            result = adapters.read(load_sealed_version(conn, row.source_version_id))
        except (AdapterError, UnsealedVersion) as error:
            conn.execute(text("UPDATE run_source SET search_status = 'failed', nothing_found = 'failed_search', "
                              "failure_reason = :f, decided_at = now() WHERE run_id = :r AND source_id = :s"),
                         dict(f=f"the adapter refused the source version ({type(error).__name__})", r=run_id,
                              s=row.source_id))
            return 0
        extraction = adapters.extraction(source_key)
        params = []
        for rec in result.records:
            j = rec.to_json()
            params.append(dict(r=run_id, v=row.source_version_id, k=j["source_item_key"], i=j["item_index"],
                               kind=j["kind"], a=j["alloy"], h=j["harmonized"], rep=j["reported"],
                               pr=j["paper_reference"], pd=j["paper_doi"], x=extraction))
        if params:
            conn.execute(_INSERT, params)
        conn.execute(text("UPDATE run_source SET search_status = 'searched', decided_at = now() "
                          "WHERE run_id = :r AND source_id = :s"), dict(r=run_id, s=row.source_id))
        return len(params)

    return write(engine, run_id, "extraction", "store_records", body)


def store_records(engine: Engine, run_id: int) -> dict[str, int]:
    """Stores the records of every chosen source still pending, one source per transaction."""
    return {key: store_source(engine, run_id, key) for key in pending_sources(engine, run_id)}
