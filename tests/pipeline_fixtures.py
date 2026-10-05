"""Module-scoped scratch databases for the step 6 tests that run the pipeline once and
check its result in many ways."""
from __future__ import annotations

import contextlib

from sqlalchemy import text

import pipeline_world as pw
from conftest import _create, _drop, url_for
from hypocurate.access.context import AccessContext
from hypocurate.access.fields import record_conditions
from hypocurate.db.engine import make_engine


@contextlib.contextmanager
def frozen_run(admin, database_url, template_database, **kwargs):
    """A scratch database with the three sources registered and one run through the freeze."""
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    try:
        pw.registered(engine)
        yield engine, pw.through_freeze(engine, **kwargs)
    finally:
        engine.dispose()
        _drop(admin, name)


def decisions(engine, run_id) -> dict:
    """The stored decisions: per record its origin, source and rule in each set."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT r.id, r.source_item_key, s.key AS source, rr.rule FROM record r "
            "JOIN source_version sv ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
            "JOIN run_record rr ON rr.record_id = r.id AND rr.run_id = r.extraction_run_id "
            "WHERE r.extraction_run_id = :r"), dict(r=run_id)).all()
        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
                             dict(r=run_id)).scalar_one()
        sets = {}
        for key, rid in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a LEFT JOIN "
                                          "analysis_set_record asr ON asr.analysis_set_id = a.id WHERE a.run_id = :r"),
                                     dict(r=run_id)):
            sets.setdefault(key, set())
            if rid is not None:
                sets[key].add(rid)
        flags = conn.execute(text(
            "SELECT f.id, f.kind, f.category, array_agg(fr.record_id ORDER BY fr.record_id) AS records FROM flag f "
            "JOIN flag_record fr ON fr.flag_id = f.id WHERE f.run_id = :r GROUP BY f.id ORDER BY f.id"),
            dict(r=run_id)).all()
        conditions = {c["id"]: c for c in record_conditions(conn, AccessContext(run_id, "inclusion", "curation"))}
    primary = {r.id: r.rule for r in rows}
    rules = {"primary": primary}
    for key, diff in stage["differences_from_primary"].items():
        rules[key] = {**primary, **{int(i): rule for i, rule in diff.items()}}
    return {"origin": {r.id: r.source_item_key for r in rows}, "source": {r.id: r.source for r in rows},
            "rules": rules, "sets": sets, "conditions": conditions,
            "flags": [{"id": f.id, "kind": f.kind, "category": f.category, "records": list(f.records)} for f in flags]}
