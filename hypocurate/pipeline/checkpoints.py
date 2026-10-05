"""The two checkpoints (PRD 5.6; build step 6): the rules lock and the dataset freeze.

**Rules lock** (`lock_rules`): the plan, validated against the template, is stored with its
fingerprint and the database's time, with the run's three tags, in one transaction under the
run's lock. After it nothing in the plan can change: the database refuses any change to a
plan or a second plan (migration 0001), and this path refuses and logs a second lock.

**Dataset freeze** (`freeze_dataset`): Inclusion's access object reads the locked plan, the
record conditions and the flags; code recomputes every set from them and checks that the
stored decisions and sets are exactly what the locked rules produce. Then, in one locked
transaction that re-checks the records, flags and decisions by id, it stores:
- the counts of each set, known from structure and grain sizes only (no outcome value): records,
  alloys, alloys with enough grain sizes, independent groups and residual degrees of freedom,
  for the primary set, each source within it and each sensitivity set, with whether the plan's
  minimums are met, as information (`stage_result` "dataset_freeze"); step 7 writes the
  analysis results and decides the outcome;
- the fingerprint: SHA-256 of the canonical JSON of the plan's fingerprint, every set's records
  (each with a hash of its stored content) and every set's rules, and the counts;
- `run_snapshot`, or, when no record is eligible, the run-level "no dataset frozen" row
  (PRD 5.6: no dataset is frozen and no test is run).
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import bindparam, Text

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, log_refusal,
                                        record_ids, run_record_sources, write)


def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
    """Locks the run's rules with `content`; returns the plan's fingerprint."""
    try:
        plan = validate(content)
        tags = tags_for(plan)
    except PlanError as error:
        log_refusal(engine, run_id, "checkpoint", "lock_rules", "invalid_plan", str(error))
        raise Refused("lock_rules", "invalid_plan", str(error)) from None
    fp = fingerprint(plan)

    def body(conn: Connection, stage: str):
        if stage != "before_lock":
            raise Refused("lock_rules", "already_done" if stage != "none" else "stage_mismatch")
        version = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        if plan["hypothesis_version"] != version:
            raise Refused("lock_rules", "invalid_plan", "the plan names another hypothesis version")
        # Review finding 3: every chosen source has a survivor priority and a grouping unit.
        chosen = set(conn.execute(text("SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id "
                                       "WHERE rs.run_id = :r AND rs.source_version_id IS NOT NULL"),
                                  dict(r=run_id)).scalars())
        rules = plan["rules"]
        for name, covered in (("survivor_source_order", set(rules["survivor_source_order"])),
                              ("grouping", {g["source"] for g in rules["grouping"]})):
            if chosen - covered:
                raise Refused("lock_rules", "invalid_plan",
                              f"{name} leaves out chosen sources: {', '.join(sorted(chosen - covered))}")
        ids = []
        for kind, value in tags.items():
            tid = conn.execute(text("SELECT id FROM tag_value WHERE kind = :k AND value = :v AND status = 'approved'"),
                               dict(k=kind, v=value)).scalar_one_or_none()
            if tid is None:
                raise Refused("lock_rules", "tag_not_available", f"{kind}: {value}")
            ids.append(tid)
        s = plan["sufficiency"]
        conn.execute(text(
            "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
            "min_resid_df, sensitivity_analysis_keys) VALUES (:r, :c, :fp, :o, :a, :b, :g, :d, :k)").bindparams(
            bindparam("c", type_=JSONB), bindparam("k", type_=ARRAY(Text))),
            dict(r=run_id, c=plan, fp=fp, o=s["option"], a=s["min_records"], b=s["min_alloys"], g=s["min_groups"],
                 d=s["min_resid_df"], k=list(plan["sensitivity_analyses"])))
        for tid in ids:
            conn.execute(text("INSERT INTO run_tag (run_id, tag_value_id) VALUES (:r, :t)"), dict(r=run_id, t=tid))
        return fp

    return write(engine, run_id, "checkpoint", "lock_rules", body)


def _set_records(conn: Connection, run_id: int) -> dict[str, list[int]]:
    rows = conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a LEFT JOIN analysis_set_record asr "
                             "ON asr.analysis_set_id = a.id WHERE a.run_id = :r"), dict(r=run_id)).all()
    out: dict[str, list[int]] = {}
    for key, rid in rows:
        out.setdefault(key, [])
        if rid is not None:
            out[key].append(rid)
    return {k: sorted(v) for k, v in out.items()}


def freeze_dataset(engine: Engine, run_id: int) -> dict:
    """Freezes the analysis dataset (or records that none is frozen); returns the freeze record."""
    data = role_input(bind_code(engine, run_id, "inclusion"))
    plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
    by_id = {r["id"]: r for r in records}
    sets = el.all_sets(plan, records, flags)
    members = {key: el.members(rules) for key, rules in sets.items()}
    counts: dict[str, Any] = {key: el.counts(plan, by_id, ids, key) for key, ids in members.items()}
    counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
                                                            if by_id[i]["source"] == source])
                            for source in sorted({by_id[i]["source"] for i in members[el.PRIMARY]})}
    content = {
        "plan": data["plan"]["fingerprint"],
        "sets": {key: [[i, by_id[i]["fingerprint"]] for i in ids] for key, ids in members.items()},
        "rules": {key: {str(i): rule for i, rule in sorted(rules.items())} for key, rules in sets.items()},
        "counts": counts,
    }
    fp = hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
    read_ids = sorted(by_id)
    read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("freeze_dataset", "already_done" if stage in ("analysis", "closed_without_freeze")
                          else "stage_mismatch")
        if constructed_unmarked(conn, run_id, run_record_sources(conn, run_id)):
            raise Refused("freeze_dataset", "constructed_data_unmarked")
        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
            raise Refused("freeze_dataset", "changed_since_read")
        stored = dict(conn.execute(text("SELECT record_id, rule FROM run_record WHERE run_id = :r"),
                                   dict(r=run_id)).all())
        if stored != sets[el.PRIMARY] or _set_records(conn, run_id) != members:
            raise Refused("freeze_dataset", "changed_since_read",
                          "the stored decisions are not what the locked rules produce")
        record = {"fingerprint": fp, "counts": counts, "frozen": bool(members[el.PRIMARY])}
        code_stage(conn, run_id, "dataset_freeze", {"plan": data["plan"]["fingerprint"]}, record)
        if members[el.PRIMARY]:
            conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
                         dict(r=run_id, fp=fp, n=len(members[el.PRIMARY])))
        else:
            conn.execute(text("INSERT INTO calibration_result (run_id, status, reason) "
                              "VALUES (:r, 'unavailable', 'no_dataset_frozen')"), dict(r=run_id))
        return record

    return write(engine, run_id, "checkpoint", "freeze_dataset", body)
