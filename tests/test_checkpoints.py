"""Step 6: the rules lock and the dataset freeze (PRD 5.6), the pipeline's write paths and their
refusals (PRD 14.2: changes after a checkpoint are rejected and logged), and the guard that keeps
constructed test data out of a run not marked as a test (register 'constructed_test_runs').

Real sources, registered from their frozen files, in scratch databases."""
from __future__ import annotations

import json
import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

import pipeline_world as pw
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import checkpoints, checks, extract, inclusion, writes
from hypocurate.pipeline.plan import default_plan, fingerprint, reference_plan
from hypocurate.pipeline.writes import Refused
from hypocurate.sources import adapters
from source_helpers import sealed_from_disk


@pytest.fixture
def engine(db):
    pw.registered(db)
    return db


def q(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def refusals(engine, run_id):
    return [(r.role, r.function, r.detail["code"]) for r in q(
        engine, "SELECT role, function, detail FROM audit_log WHERE run_id = :r AND detail->>'result' = 'rejected' "
                "ORDER BY id", r=run_id)]


def stage(engine, run_id):
    from hypocurate.access.stage import actual_stage
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        return actual_stage(conn, run_id, status)


# --- the rules lock ------------------------------------------------------------------------

def test_the_lock_stores_the_plan_its_fingerprint_and_three_tags_in_one_transaction(engine):
    rid = pw.dispatched_run(engine)
    content = reference_plan(pw.version_of(engine, rid))
    assert checkpoints.lock_rules(engine, rid, content) == fingerprint(content)
    (row,) = q(engine, "SELECT content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
                       "min_resid_df, sensitivity_analysis_keys, xmin::text AS tx FROM plan WHERE run_id = :r", r=rid)
    assert row.content == content and row.fingerprint == fingerprint(content)
    assert (row.sufficiency_option, row.min_records, row.min_alloys, row.min_groups, row.min_resid_df) == \
        ("fixed_minimum", 30, 5, 10, 10)
    assert row.sensitivity_analysis_keys == content["sensitivity_analyses"]
    tags = q(engine, "SELECT tv.kind, tv.value, rt.xmin::text AS tx FROM run_tag rt "
                     "JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r ORDER BY tv.kind", r=rid)
    assert [(t.kind, t.value) for t in tags] == [
        ("alloy_class", "multi-principal-element (high-entropy) alloy"), ("property", "yield strength"),
        ("test_condition", "room-temperature tension")]
    assert {t.tx for t in tags} == {row.tx}  # the lock's own transaction
    assert stage(engine, rid) == "curation"


def test_a_second_lock_or_a_changed_plan_is_refused_and_logged(engine):
    rid = pw.locked_run(engine)
    changed = reference_plan(pw.version_of(engine, rid))
    changed["rules"]["duplicate_tolerance"] = 0.5
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, changed)
    assert refused.value.code == "already_done"
    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "already_done")]
    # The database itself refuses any change to a locked plan, whoever tries.
    with pytest.raises(IntegrityError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(text("UPDATE plan SET content = '{}' WHERE run_id = :r"), dict(r=rid))
    assert q(engine, "SELECT content FROM plan WHERE run_id = :r", r=rid)[0].content == \
        reference_plan(pw.version_of(engine, rid))


def test_an_invalid_plan_or_one_for_another_version_is_refused_and_logged(engine):
    rid = pw.dispatched_run(engine)
    bad = default_plan(pw.version_of(engine, rid))
    bad["rules"]["note"] = "free text"
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, bad)
    assert refused.value.code == "invalid_plan"
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, default_plan(pw.version_of(engine, rid) + 1000))
    assert refused.value.code == "invalid_plan" and "another hypothesis version" in refused.value.message
    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "invalid_plan")] * 2
    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0


@pytest.mark.parametrize("setting, value", [
    ("survivor_source_order", ["mpea", "controlled_duplicates"]),  # tamu_fcc chosen but not ordered
    ("survivor_source_order", []),
    ("grouping", [{"source": "mpea", "unit": "paper"}]),  # tamu_fcc chosen but not grouped
    ("grouping", []),
])
def test_the_lock_refuses_settings_that_leave_out_a_chosen_source(engine, setting, value):
    """Review finding 3: the survivor order and the grouping must cover every chosen source, or a
    survivor or a group would depend on something other than the plan."""
    rid = pw.dispatched_run(engine, sources=("mpea", "tamu_fcc"))
    content = reference_plan(pw.version_of(engine, rid))
    content["rules"][setting] = value
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, content)
    assert refused.value.code == "invalid_plan"
    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "invalid_plan")]
    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0


def test_the_lock_waits_for_the_run_lock(engine, monkeypatch):
    """The write path takes hc_write_lock first: while another transaction holds the run's lock
    the lock waits, then fails after the lock timeout, and nothing is written."""
    rid = pw.dispatched_run(engine)
    monkeypatch.setattr(writes, "LOCK_TIMEOUT_MS", 300)
    with engine.connect() as holder:
        holder.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        started = time.monotonic()
        with pytest.raises(DBAPIError, match="lock timeout"):
            checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
        assert time.monotonic() - started >= 0.3
        holder.rollback()
    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0


def test_every_write_path_takes_the_run_lock_before_it_writes(engine):
    """Locking protocol (step 3): in every transaction of the pipeline's write paths, each INSERT or
    UPDATE comes after `hc_write_lock(p_run => …)`. Refusal rows in audit_log are the named
    exception (written without the run lock)."""
    from sqlalchemy import event
    violations, state = [], {}

    def on_begin(conn):
        state[id(conn)] = False

    def on_execute(conn, cursor, statement, parameters, context, executemany):
        s = " ".join(statement.split()).upper()
        if "HC_WRITE_LOCK(" in s:
            state[id(conn)] = True
        elif s.startswith(("INSERT", "UPDATE")) and not s.startswith("INSERT INTO AUDIT_LOG") \
                and not state.get(id(conn), False):
            violations.append(s[:80])

    event.listen(engine, "begin", on_begin)
    event.listen(engine, "before_cursor_execute", on_execute)
    try:
        rid = pw.dispatched_run(engine, sources=("tamu_fcc",))
        violations.clear()  # the test's own dispatch is not a pipeline write path
        checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
        extract.store_records(engine, rid)
        checks.run_checks(engine, rid)
        inclusion.decide_run(engine, rid)
        checkpoints.freeze_dataset(engine, rid)
    finally:
        event.remove(engine, "begin", on_begin)
        event.remove(engine, "before_cursor_execute", on_execute)
    assert violations == []
    assert stage(engine, rid) == "analysis"


def _between_read_and_write(monkeypatch, module, engine, change):
    """Runs `change` after the step has read through its access object and before its write."""
    original = module.write

    def write(*args, **kwargs):
        change()
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "write", write)


def _add_record(engine, rid, key):
    version = q(engine, "SELECT source_version_id FROM run_source WHERE run_id = :r AND source_version_id IS NOT NULL",
                r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, :k, 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"),
                     dict(r=rid, v=version, k=key))


@pytest.mark.parametrize("step", ["checks", "inclusion", "freeze"])
def test_a_change_between_a_steps_read_and_its_write_is_refused(engine, monkeypatch, step):
    """Each step reads through its access object, then writes in a separate locked transaction
    that re-checks by id what it read. A record added in between is refused as a change."""
    rid = pw.locked_run(engine, sources=("tamu_fcc",))
    extract.store_records(engine, rid)
    if step != "checks":
        checks.run_checks(engine, rid)
    if step == "freeze":
        inclusion.decide_run(engine, rid)
    module, call, function = {"checks": (checks, checks.run_checks, "raise_flags"),
                              "inclusion": (inclusion, inclusion.decide_run, "decide"),
                              "freeze": (checkpoints, checkpoints.freeze_dataset, "freeze_dataset")}[step]
    _between_read_and_write(monkeypatch, module, engine, lambda: _add_record(engine, rid, f"added-{step}"))
    with pytest.raises(Refused) as refused:
        call(engine, rid)
    assert refused.value.code == "changed_since_read"
    assert refusals(engine, rid)[-1][1:] == (function, "changed_since_read")


# --- Checks bound to the records it covered (step 6 review, finding 1) ---------------------------

def _conflict_ids(engine, rid):
    """The MPEA and extract records of extract row 7 (MPEA row 1278): a real conflict (YS x 1.3)."""
    rows = dict(q(engine, "SELECT source_item_key, id FROM record WHERE extraction_run_id = :r AND source_item_key "
                          "IN ('MPEA_dataset.csv:row:1278', 'extract.csv:row:6')", r=rid))
    return rows["MPEA_dataset.csv:row:1278"], rows["extract.csv:row:6"]


def test_skipping_checks_is_refused_at_inclusion_and_the_freeze(engine):
    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    extract.store_records(engine, rid)
    for call, function in ((inclusion.decide_run, "decide"), (checkpoints.freeze_dataset, "freeze_dataset")):
        with pytest.raises(Refused) as refused:
            call(engine, rid)
        assert refused.value.code == "checks_not_done"
        assert refusals(engine, rid)[-1][1:] == (function, "checks_not_done")
    assert q(engine, "SELECT count(*) FROM run_record WHERE run_id = :r", r=rid)[0][0] == 0


def test_checks_wait_until_every_chosen_source_is_stored(engine):
    """Store MPEA, then Checks while the extract is still pending: refused; after the extract is
    stored, Checks covers both and the real conflict is flagged and kept out."""
    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    extract.store_source(engine, rid, "mpea")
    with pytest.raises(Refused) as refused:
        checks.run_checks(engine, rid)
    assert refused.value.code == "extraction_unfinished"
    extract.store_source(engine, rid, "controlled_duplicates")
    checks.run_checks(engine, rid)
    with pytest.raises(Refused) as refused:  # nothing more is stored after Checks
        extract.store_source(engine, rid, "controlled_duplicates")
    sets = inclusion.decide_run(engine, rid)
    mpea, copy = _conflict_ids(engine, rid)
    assert (sets["primary"][mpea], sets["primary"][copy]) == ("conflict_unresolved", "conflict_unresolved")


def test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze(engine):
    """A conflicting copy added after Checks (by plain SQL: storage refuses it) is not covered by
    the Checks result, so Inclusion and the freeze refuse."""
    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    mpea, _ = _conflict_ids(engine, rid)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, alloy, "
            "harmonized, reported, paper_reference, paper_doi, extraction) SELECT r.extraction_run_id, "
            "(SELECT source_version_id FROM record WHERE source_item_key = 'extract.csv:row:6' AND extraction_run_id = :r), "
            "'added-after-checks', 0, r.kind, r.alloy, jsonb_set(r.harmonized, '{yield_strength,value}', "
            "to_jsonb((r.harmonized->'yield_strength'->>'value')::float * 1.5)), r.reported, r.paper_reference, "
            "r.paper_doi, r.extraction FROM record r WHERE r.id = :m"), dict(r=rid, m=mpea))
    with pytest.raises(Refused) as refused:
        inclusion.decide_run(engine, rid)
    assert refused.value.code == "checks_not_current"
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code in ("checks_not_current", "changed_since_read")
    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0


# --- records, flags and decisions between the checkpoints ------------------------------------

def test_records_are_stored_only_after_the_lock_with_how_they_were_extracted(engine):
    rid = pw.dispatched_run(engine)
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "mpea")
    assert refused.value.code == "stage_mismatch"
    assert refusals(engine, rid) == [("extraction", "store_records", "stage_mismatch")]
    checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
    assert extract.store_records(engine, rid) == {"mpea": 1545, "tamu_fcc": 94}
    rows = q(engine, "SELECT s.key, r.source_item_key, r.harmonized, r.extraction FROM record r JOIN source_version sv "
                     "ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
                     "WHERE r.extraction_run_id = :r ORDER BY r.id", r=rid)
    assert {(r.key, json.dumps(r.extraction, sort_keys=True)) for r in rows} == {
        ("mpea", json.dumps({"method": "adapter", "name": "mpea_layout", "version": "1"}, sort_keys=True)),
        ("tamu_fcc", json.dumps({"method": "adapter", "name": "tamu_fcc", "version": "2"}, sort_keys=True))}
    # Unchanged and in file order: the adapter's own output.
    expected = adapters.read(sealed_from_disk("tamu_fcc")).records
    tamu = [r for r in rows if r.key == "tamu_fcc"]
    assert [r.source_item_key for r in tamu] == [e.source_item_key for e in expected]
    assert [r.harmonized for r in tamu] == [e.to_json()["harmonized"] for e in expected]
    assert {r.search_status for r in q(engine, "SELECT search_status FROM run_source WHERE run_id = :r "
                                                "AND source_version_id IS NOT NULL", r=rid)} == {"searched"}
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "mpea")
    assert refused.value.code == "already_done"


def test_constructed_data_never_enters_a_run_not_marked_as_a_test(engine):
    """Register 'constructed_test_runs': refused and logged at storage, inclusion and freeze."""
    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"))
    assert extract.store_source(engine, rid, "mpea") == 1545
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "controlled_duplicates")
    assert refused.value.code == "constructed_data_unmarked"
    assert q(engine, "SELECT search_status FROM run_source rs JOIN source s ON s.id = rs.source_id "
                     "WHERE rs.run_id = :r AND s.key = 'controlled_duplicates'", r=rid)[0][0] == "pending"
    # Code that bypassed storage (here: plain SQL) still meets the guard at inclusion and freeze.
    version = q(engine, "SELECT source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
                        "WHERE rs.run_id = :r AND s.key = 'controlled_duplicates'", r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, 'extract.csv:row:0', 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
        # Checks wait until no chosen source is pending (review finding 1): the bypass marks it searched.
        conn.execute(text("UPDATE run_source SET search_status = 'searched', decided_at = now() WHERE run_id = :r "
                          "AND source_version_id = :v"), dict(r=rid, v=version))
    checks.run_checks(engine, rid)
    with pytest.raises(Refused) as refused:
        inclusion.decide_run(engine, rid)
    assert refused.value.code == "constructed_data_unmarked"
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code == "constructed_data_unmarked"
    assert refusals(engine, rid) == [("extraction", "store_records", "constructed_data_unmarked"),
                                     ("inclusion", "decide", "constructed_data_unmarked"),
                                     ("checkpoint", "freeze_dataset", "constructed_data_unmarked")]
    assert q(engine, "SELECT count(*) FROM run_record WHERE run_id = :r", r=rid)[0][0] == 0
    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0


def test_a_marked_run_takes_the_constructed_records(engine):
    rid = pw.through_freeze(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    assert stage(engine, rid) == "analysis"
    assert q(engine, "SELECT count(*) FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
                     "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r "
                     "AND s.key = 'controlled_duplicates'", r=rid)[0][0] == 16


def test_a_change_after_the_decisions_were_read_is_refused_at_the_freeze(engine):
    rid = pw.locked_run(engine, sources=("mpea",))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    # A record added between inclusion and the freeze (the database allows it before the freeze).
    version = q(engine, "SELECT source_version_id FROM run_source WHERE run_id = :r AND source_version_id IS NOT NULL",
                r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, 'added-by-hand', 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    # Since the review (finding 1) the freeze first finds that Checks did not cover the added record.
    assert refused.value.code == "checks_not_current"
    assert refusals(engine, rid)[-1] == ("checkpoint", "freeze_dataset", "checks_not_current")
    assert stage(engine, rid) == "curation"


def test_the_freeze_refuses_decisions_that_are_not_what_the_locked_rules_produce(engine):
    rid = pw.locked_run(engine, sources=("mpea",))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    with pytest.raises(Refused) as refused:  # no decisions at all
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code == "changed_since_read"
    # Decisions written by hand, one of them by choice: the freeze refuses them.
    ids = [r[0] for r in q(engine, "SELECT id FROM record WHERE extraction_run_id = :r ORDER BY id", r=rid)]
    with engine.begin() as conn:
        for rid_ in ids:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)"),
                         dict(r=rid, c=rid_, e=rid_ == ids[0], u="in_scope" if rid_ == ids[0] else "out_of_scope"))
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert "not what the locked rules produce" in refused.value.message


def test_after_the_freeze_every_write_is_refused_and_logged(engine):
    rid = pw.through_freeze(engine)
    before = q(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r", r=rid)[0][0]
    for call, role, function in [
            (lambda: checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid))), "checkpoint",
             "lock_rules"),
            (lambda: checks.run_checks(engine, rid), "checks", "bind"),
            (lambda: inclusion.decide_run(engine, rid), "inclusion", "bind"),
            (lambda: checkpoints.freeze_dataset(engine, rid), "inclusion", "bind")]:
        with pytest.raises(Exception):
            call()
    rows = q(engine, "SELECT role, function, allowed FROM audit_log WHERE run_id = :r AND id > 0 ORDER BY id",
             r=rid)[before:]
    assert [(r.role, r.function, r.allowed) for r in rows] == [
        ("checkpoint", "lock_rules", False), ("checks", "bind", False), ("inclusion", "bind", False),
        ("inclusion", "bind", False)]
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) SELECT :r, id, true, "
                              "'in_scope' FROM record WHERE extraction_run_id = :r LIMIT 1"), dict(r=rid))


# --- the dataset freeze ----------------------------------------------------------------------

def test_the_freeze_records_its_counts_and_fingerprint(engine):
    rid = pw.through_freeze(engine)
    (snap,) = q(engine, "SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r", r=rid)
    (out,) = q(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'dataset_freeze'", r=rid)
    record = out.output
    assert record["fingerprint"] == snap.fingerprint and record["frozen"] is True
    assert snap.n_records == record["counts"]["primary"]["n_records"]
    assert set(record["counts"]) == {"primary", "per_source", *reference_plan(1)["sensitivity_analyses"]}
    assert set(record["counts"]["per_source"]) == {"mpea", "tamu_fcc"}
    stages = [r.stage for r in q(engine, "SELECT stage FROM stage_result WHERE run_id = :r AND role IS NULL "
                                         "ORDER BY id", r=rid)]
    assert stages == ["checks", "inclusion", "dataset_freeze"]
    assert stage(engine, rid) == "analysis"


def test_no_eligible_record_means_no_dataset_is_frozen(engine):
    """PRD 5.6: no dataset is frozen and no test is run; the run is closed without a freeze."""
    rid = pw.dispatched_run(engine, sources=("tamu_fcc",))
    content = reference_plan(pw.version_of(engine, rid))
    content["scope"]["phase_class"] = ["BCC"]
    checkpoints.lock_rules(engine, rid, content)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    sets = inclusion.decide_run(engine, rid)
    assert set(sets["primary"].values()) <= {"out_of_scope", "missing_value"}
    record = checkpoints.freeze_dataset(engine, rid)
    assert record["frozen"] is False and record["counts"]["primary"]["n_records"] == 0
    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0
    assert q(engine, "SELECT status, reason FROM calibration_result WHERE run_id = :r", r=rid) == [
        ("unavailable", "no_dataset_frozen")]
    assert stage(engine, rid) == "closed_without_freeze"


def test_the_fingerprint_does_not_depend_on_database_ids(engine):
    """Review finding 5: two identical runs in the same database, with an unrelated run's records
    inserted between them (so every record id differs), give the same freeze fingerprint."""
    first = pw.through_freeze(engine, sources=("mpea", "tamu_fcc"))
    pw.through_freeze(engine, sources=("tamu_fcc",))  # unrelated inserts
    second = pw.run_of_version(engine, pw.version_of(engine, first), sources=("mpea", "tamu_fcc"))
    checkpoints.lock_rules(engine, second, reference_plan(pw.version_of(engine, first)))
    extract.store_records(engine, second)
    checks.run_checks(engine, second)
    inclusion.decide_run(engine, second)
    checkpoints.freeze_dataset(engine, second)
    fp = {rid: q(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] for rid in (first, second)}
    ids = {rid: q(engine, "SELECT min(id) FROM record WHERE extraction_run_id = :r", r=rid)[0][0] for rid in (first, second)}
    assert ids[first] != ids[second]
    assert fp[first] == fp[second]


def test_the_same_steps_on_another_database_give_the_same_fingerprint(admin, database_url, template_database):
    """The freeze is deterministic: the same frozen sources, plan and steps give the same
    fingerprint, counts and decisions."""
    results = []
    for _ in range(2):
        name = _create(admin, "hypocurate_t", template=template_database)
        engine = make_engine(url_for(database_url, name))
        try:
            pw.registered(engine)
            rid = pw.through_freeze(engine, sources=("mpea", "tamu_fcc", "controlled_duplicates"), marked=True)
            with engine.connect() as conn:
                results.append((conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                             dict(r=rid)).scalar_one(),
                                conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND "
                                                  "stage = 'dataset_freeze'"), dict(r=rid)).scalar_one(),
                                conn.execute(text("SELECT array_agg(rule ORDER BY record_id) FROM run_record "
                                                  "WHERE run_id = :r"), dict(r=rid)).scalar_one()))
        finally:
            engine.dispose()
            _drop(admin, name)
    assert results[0] == results[1]
