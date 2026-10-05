"""Step 6 test helper: runs on the real frozen sources, through the real lifecycle.

`registered(engine)` registers the three sources from their frozen files (step 4 code).
`dispatched_run(...)` creates a query with the chosen sources, submits, confirms and dispatches
it, and starts the run (a run_source row for every registered source, as dispatch writes them).
`through_freeze(...)` locks the plan, stores the records, raises the flags, decides and freezes
(step 6 code), and returns the run's id.
"""
from __future__ import annotations

import json

from sqlalchemy import text

from hypocurate.pipeline import checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources.versions import register

SOURCE_KEYS = ("mpea", "tamu_fcc", "controlled_duplicates")


def registered(engine, keys=SOURCE_KEYS) -> dict[str, int]:
    return {k: register(engine, k).version_id for k in keys}


def _val(engine, sql, **params):
    with engine.begin() as conn:
        result = conn.execute(text(sql), params)
        return result.scalar() if result.returns_rows else None


def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
    """A running run of the reference claim that chose `sources`."""
    with engine.connect() as conn:
        registry = dict(conn.execute(text(
            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
        domain = conn.execute(text("SELECT id FROM domain WHERE key = 'grain_size_strengthening'")).scalar_one()
    h = _val(engine, "INSERT INTO hypothesis DEFAULT VALUES RETURNING id")
    vid = _val(engine, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) VALUES "
                       "(:h, 1, 'In FCC multi-principal-element alloys, yield strength rises as grain size falls', "
                       ":d) RETURNING id", h=h, d=domain)
    for key in sources:
        _val(engine, "INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=ids[key])
    _val(engine, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)
    _val(engine, "UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
         v=vid, d=domain)
    _val(engine, "UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)
    return run_of_version(engine, vid, sources, marked)


def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False) -> int:
    """Another running run of an already dispatched hypothesis version."""
    with engine.connect() as conn:
        registry = dict(conn.execute(text(
            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
    flags = json.dumps({"constructed_test_data": True} if marked else {})
    rid = _val(engine, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                       "VALUES (:v, true, CAST(:f AS jsonb)) RETURNING id", v=vid, f=flags)
    for key, version in registry.items():
        if key in sources:
            _val(engine, "INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                         "VALUES (:r, :s, :sv, 'pending')", r=rid, s=ids[key], sv=version)
        else:
            _val(engine, "INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
                 r=rid, s=ids[key])
    _val(engine, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)
    return rid


def version_of(engine, run_id) -> int:
    return _val(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=run_id)


def locked_run(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = dispatched_run(engine, sources, marked)
    checkpoints.lock_rules(engine, rid, plan or reference_plan(version_of(engine, rid)))
    return rid


def through_freeze(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = locked_run(engine, sources, marked, plan)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid
