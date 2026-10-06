"""Inclusion (code; PRD 4, 5.3; build step 6): every record's eligibility under the locked rules.

Reads through its own access object (`dispatch.bind_code(…, "inclusion")`): the locked plan,
the record conditions and the flags by kind and category. **It receives no outcome value**, so
no eligibility decision can depend on a record's outcome directly or on its position relative
to the tested relationship. It does act on the flags Checks raised, which compared values
(register 'code_role_access').

`pipeline.eligibility` decides one rule per record for the primary set and for every
sensitivity set the plan names. One transaction under the run's lock re-checks the records
and flags by id, then writes a decision for every record (`run_record`: eligible exactly when
the rule is `in_scope`, with the rule that decided it), each set (`analysis_set`,
`analysis_set_record`), and a code stage result "inclusion" listing each sensitivity set's
rules where they differ from the primary set's. Decisions are written once, before the freeze.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, text

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, decide_sets, flag_index,
                                        inclusion_input, record_identity,
                                        record_ids, require_checks_cover, run_record_sources, write)


def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
    data = inclusion_input(engine, run_id, "inclusion", "decide")
    plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
    sets = decide_sets(engine, run_id, "inclusion", "decide", data)
    read_ids = sorted(r["id"] for r in records)
    read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
    identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("decide", "stage_mismatch")
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_record WHERE run_id = :r)"), dict(r=run_id)).scalar_one():
            raise Refused("decide", "already_done")
        if constructed_unmarked(conn, run_id, run_record_sources(conn, run_id)):
            raise Refused("decide", "constructed_data_unmarked")
        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
            raise Refused("decide", "changed_since_read")
        require_checks_cover(conn, run_id, "decide", identity_of, [(k, c, r) for _, k, c, r in read_flags])
        primary = sets[el.PRIMARY]
        if primary:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)"),
                         [dict(r=run_id, c=rid, e=rule == "in_scope", u=rule) for rid, rule in sorted(primary.items())])
        for key, rules in sets.items():
            sid = conn.execute(text("INSERT INTO analysis_set (run_id, key) VALUES (:r, :k) RETURNING id"),
                               dict(r=run_id, k=key)).scalar_one()
            ids = el.members(rules)
            if ids:
                conn.execute(text("INSERT INTO analysis_set_record (analysis_set_id, record_id) VALUES (:s, :c)"),
                             [dict(s=sid, c=rid) for rid in ids])
        differences = {key: {str(rid): rule for rid, rule in sorted(rules.items()) if rule != primary[rid]}
                       for key, rules in sets.items() if key != el.PRIMARY}
        totals = {key: {rule: sum(r == rule for r in rules.values()) for rule in sorted(set(rules.values()))}
                  for key, rules in sets.items()}
        code_stage(conn, run_id, "inclusion", {"plan": data["plan"]["fingerprint"], "records": len(read_ids),
                                               "flags": len(read_flags)},
                   {"rules": totals, "differences_from_primary": differences,
                    "changes": {k: el.SENSITIVITY_CHANGES[k] for k in sets if k != el.PRIMARY},
                    **({"most_influential": el.most_influential(plan, {r["id"]: r for r in records},
                                                                el.members(primary))}
                       if el.INFLUENCE_KEY in sets else {})})
        return sets

    return write(engine, run_id, "inclusion", "decide", body)
