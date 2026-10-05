"""Checks (code; PRD 4, 5.3; build step 6): raise the flags of a run's records.

Reads through its own access object (`dispatch.bind_code(…, "checks")`: the locked plan and
every stored value) once every chosen source is stored, computes the flags with `pipeline.flags` (per-record rules, and pairwise comparisons that feed a
whole-group classification
only), then writes them in one transaction under the run's lock that re-checks the records by
id. Checks never decides eligibility. Flags are raised once per run, before the freeze; the
numbers compared are stored for audit and never returned to the Critic.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline.flags import Flag, raise_flags, set_flags
from hypocurate.pipeline.writes import (Refused, binding, code_stage, flag_index, pending_sources, record_ids,
                                        record_identity, write)


def run_checks(engine: Engine, run_id: int) -> list[Flag]:
    data = role_input(bind_code(engine, run_id, "checks"))
    plan, records = data["plan"]["content"], data["records_full"]
    flags = raise_flags(plan, records)
    per_set = set_flags(plan, records)
    read_ids = sorted(r["id"] for r in records)
    identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
    covered = binding(identity_of.values(), [(f.kind, f.category, [identity_of[i] for i in f.records]) for f in flags])

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("raise_flags", "stage_mismatch")
        if flag_index(conn, run_id) or conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'checks')"),
                dict(r=run_id)).scalar_one():
            raise Refused("raise_flags", "already_done")
        if pending_sources(conn, run_id):
            raise Refused("raise_flags", "extraction_unfinished")
        if record_ids(conn, run_id) != read_ids:
            raise Refused("raise_flags", "changed_since_read")
        for f in flags:
            fid = conn.execute(text("INSERT INTO flag (run_id, kind, category, compared_values) "
                                    "VALUES (:r, :k, :c, :v) RETURNING id").bindparams(bindparam("v", type_=JSONB)),
                               dict(r=run_id, k=f.kind, c=f.category, v=f.compared_values)).scalar_one()
            conn.execute(text("INSERT INTO flag_record (flag_id, record_id) VALUES (:f, :r)"),
                         [dict(f=fid, r=rid) for rid in f.records])
        counts: dict[str, int] = {}
        for f in flags:
            counts[f"{f.kind}/{f.category}"] = counts.get(f"{f.kind}/{f.category}", 0) + 1
        code_stage(conn, run_id, "checks", {"plan": data["plan"]["fingerprint"], "records": len(read_ids)},
                   {"flags": dict(sorted(counts.items())), "binding": covered,
                    # Step 6 review, finding 2: the matching flags of each sensitivity set whose matching
                    # settings differ (kind, category, records; the numbers stay in Checks).
                    "set_flags": {key: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
                                  for key, fs in per_set.items()}})
        return flags

    return write(engine, run_id, "checks", "raise_flags", body)
