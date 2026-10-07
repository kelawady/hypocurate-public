"""Step 5 review fixes: the trusted dispatcher, the immutable context, logging of denials and
failures, one snapshot per input, real concurrent checkpoint transitions, and the
vocabularies with their unrecognized counts.
"""
from __future__ import annotations

import logging
import subprocess
import threading
import time
import traceback

import pytest
from sqlalchemy import text

import access_world as aw
from access_testing import access_for
from hypocurate.access import Access, AccessDenied, AccessFailed, bind, layer, role_input, vocabulary
from hypocurate.access.allowlist import allowed
from hypocurate.access.context import AccessContext
from hypocurate.access import guarded
from hypocurate.access.guarded import run_guarded
from hypocurate.db.engine import make_engine
from hypocurate.sources import connection


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    yield e
    e.dispose()


def audit(engine, run=None, null_run=False):
    where = "WHERE run_id IS NULL " if null_run else ("WHERE run_id = :r " if run else "")
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log " + where
                                 + "ORDER BY id"), dict(r=run)).all()


# --- The dispatcher -------------------------------------------------------------------------

def test_bind_reads_the_role_from_the_runs_agent_settings_and_the_stage_from_the_database(engine):
    world = aw.build(engine, "curation")
    for role in ("critic", "analyst", "planner"):
        a = bind(engine, world.run, world.settings[role])
        assert a.context == AccessContext(world.run, role, "curation", None, world.settings[role])
    # Step 8a: the Curator binds to a run with no source and then has nothing at a run stage.
    curator = bind(engine, world.run, world.settings["curator"])
    assert curator.context.role == "curator" and curator.context.source_key is None
    assert role_input(bind(engine, world.run, world.settings["critic"]))["flags_kind"]
    binds = [r for r in audit(engine, world.run) if r.function == "bind"]
    assert len(binds) == 5 and all(r.allowed and r.detail["result"] == "allowed" for r in binds)


def test_bind_refuses_a_setting_or_source_the_run_did_not_record(engine):
    world = aw.build(engine, "curation")
    stray = aw.val(world.w, "INSERT INTO agent_setting (role, version, instruction, model) "
                            "VALUES ('analyst', 2, 'x', 'model-a') RETURNING id")
    # Step 8a: no run role is bound to a source, the Curator included (it reads at registration).
    cases = [(dict(agent_setting_id=stray), "setting_not_recorded"),
             (dict(agent_setting_id=world.settings["curator"], source_key="mpea"), "source_not_for_role"),
             (dict(agent_setting_id=world.settings["curator"], source_key="controlled_duplicates"),
              "source_not_for_role"),
             (dict(agent_setting_id=world.settings["critic"], source_key="mpea"), "source_not_for_role")]
    for kw, code in cases:
        with pytest.raises(AccessDenied) as denied:
            bind(engine, world.run, **kw)
        assert denied.value.code == code
    rows = [(r.function, r.allowed, r.detail["result"], r.detail["code"]) for r in audit(engine, world.run)
            if r.function == "bind"]
    assert rows == [("bind", False, "denied", code) for _, code in cases]


def test_bind_logs_an_unknown_run_as_a_failure_with_no_run(engine):
    aw.build(engine, "before_lock")
    with pytest.raises(AccessFailed) as failed:
        bind(engine, 999999, 1)
    assert failed.value.code == "unknown_run"
    rows = audit(engine, null_run=True)
    assert [(r.function, r.detail["result"], r.detail["code"], r.detail["requested_run"]) for r in rows] == [
        ("bind", "failed", "unknown_run", 999999)]


def test_an_access_object_has_no_public_constructor_and_cannot_be_changed(engine):
    world = aw.build(engine, "before_lock")
    with pytest.raises(TypeError, match="only by hypocurate.access.dispatch.bind"):
        Access(engine, AccessContext(world.run, "analyst", "analysis"))
    a = bind(engine, world.run, world.settings["planner"])
    with pytest.raises(AttributeError):
        a._context = AccessContext(world.original_run, "analyst", "final")
    with pytest.raises(AttributeError):
        a.context.run_id = world.original_run
    with pytest.raises(TypeError):
        bind(engine, str(world.run), world.settings["planner"])


# --- Denials and failures are logged apart ---------------------------------------------------

def test_a_readers_error_is_a_logged_failure(engine, monkeypatch):
    world = aw.build(engine, "curation")

    def broken(conn, ctx):
        raise ValueError("something with 48213.579 inside")

    monkeypatch.setitem(layer.READERS, "flags_kind", broken)
    with pytest.raises(AccessFailed) as failed:
        access_for(engine, world.run, "critic", "curation").get("flags_kind")
    assert failed.value.code == "reader_error" and "48213" not in str(failed.value)
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail) == (
        "flags_kind", False, {"result": "failed", "code": "reader_error", "error_class": "ValueError"})


def test_an_unknown_run_is_a_logged_failure(engine):
    aw.build(engine, "before_lock")
    with pytest.raises(AccessFailed) as failed:
        access_for(engine, 424242, "planner", "before_lock").get("claim")
    assert failed.value.code == "unknown_run"
    assert audit(engine, null_run=True)[-1].detail == {"result": "failed", "code": "unknown_run",
                                                      "requested_run": 424242}


def test_when_the_database_is_unavailable_the_process_log_is_the_fallback(caplog):
    down = make_engine("postgresql://nobody@127.0.0.1:1/none")
    with caplog.at_level(logging.ERROR, logger="hypocurate.access"):
        with pytest.raises(AccessFailed) as failed:
            access_for(down, 7, "planner", "before_lock").get("claim")
    assert failed.value.code == "database_error"
    assert any('"audit_fallback"' in r.getMessage() and '"database_error"' in r.getMessage() for r in caplog.records)


def test_role_input_is_never_silently_empty(engine):
    world = aw.build(engine, "curation")
    with pytest.raises(AccessDenied) as denied:
        role_input(access_for(engine, world.run, "planner", "curation"))
    assert denied.value.code == "empty_list"
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail["code"]) == ("role_input", False, "empty_list")


def test_only_validated_bounded_strings_are_logged(engine):
    world = aw.build(engine, "before_lock")
    long_role = "planner-" + "48213.579" * 500
    for kw in (dict(role=long_role, stage="before_lock"), dict(role="planner", stage=long_role)):
        with pytest.raises(AccessDenied) as denied:
            access_for(engine, world.run, **kw).get("claim")
        assert "48213" not in str(denied.value)
    with pytest.raises(AccessDenied) as denied:
        access_for(engine, world.run, "planner", "before_lock").get("x" * 9000)
    assert "xxx" not in str(denied.value)
    rows = audit(engine, world.run)
    assert [(r.role, r.stage, r.function) for r in rows] == [("invalid", "before_lock", "claim"),
                                                            ("planner", "invalid", "claim"),
                                                            ("planner", "before_lock", "invalid")]
    assert rows[0].detail["given_role_length"] == len(long_role)
    assert all(len(str(r)) < 400 for r in rows)


def test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log(engine, caplog):
    world = aw.build(engine, "before_lock")
    target = str(aw.REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv")
    run_guarded("hypocurate.access.guard_probe:probe", [{"op": "read", "path": target}], timeout=60,
                audit=(engine, world.run))
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail["result"], row.detail["code"], row.detail["event"]) == (
        "guarded_run", False, "failed", "file_guard", "read")
    assert "truth.csv" in row.detail["what"]
    with caplog.at_level(logging.WARNING, logger="hypocurate.access"):
        run_guarded("hypocurate.access.guard_probe:probe", [{"op": "read", "path": target}], timeout=60)
    assert any('"file_guard"' in r.getMessage() for r in caplog.records)


# --- One snapshot; real concurrent checkpoint transitions -------------------------------------

def test_a_roles_whole_input_is_read_in_one_transaction(engine):
    world = aw.build(engine, "curation")
    role_input(bind(engine, world.run, world.settings["critic"]))
    with engine.connect() as conn:
        txns = conn.execute(text("SELECT DISTINCT xmin::text FROM audit_log WHERE run_id = :r AND function <> 'bind'"),
                            dict(r=world.run)).all()
    assert len(txns) == 1


def _waiting(engine) -> bool:
    with engine.connect() as probe:
        return probe.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                                  "AND wait_event_type = 'Lock' AND query LIKE '%hc_write_lock%'")).scalar() > 0


def _race(engine, url, read, transition):
    """`transition(conn)` runs in a transaction that holds the run's lock; `read()` starts in a
    thread and must wait; the transition commits; the read then sees the new stage."""
    holder = make_engine(url)
    out = {}
    with holder.connect() as conn:
        tx = conn.begin()
        transition(conn)
        t = threading.Thread(target=lambda: out.update(result=_outcome(read)))
        t.start()
        for _ in range(100):
            if _waiting(engine):
                break
            time.sleep(0.05)
        assert _waiting(engine) and "result" not in out
        tx.commit()
        t.join(10)
    holder.dispose()
    return out["result"]


def _outcome(read):
    try:
        return ("allowed", read())
    except AccessDenied as denied:
        return ("denied", denied.code)


def test_a_rules_lock_committed_while_a_read_waits_closes_the_planner(engine):
    world = aw.build(engine, "before_lock")
    planner = bind(engine, world.run, world.settings["planner"])

    def rules_lock(conn):
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        conn.execute(text("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, "
                          "min_alloys, min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'fixed_minimum', 4, 1, 2, 1)"),
                     dict(r=world.run, fp=aw.FP))

    assert _race(engine, engine.test_url, lambda: role_input(planner), rules_lock) == ("denied", "stage_mismatch")


def test_a_freeze_committed_while_reads_wait_closes_the_critic_and_opens_the_analyst(engine):
    world = aw.build(engine, "curation")
    w = world.w
    critic = bind(engine, world.run, world.settings["critic"])
    primary = w.analysis_set(world.run)
    for rec in world.records:
        w.decide(world.run, rec)
        w.add(primary, rec)

    def freeze(conn):
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
                     dict(r=world.run, fp=aw.FP, n=len(world.records)))

    assert _race(engine, engine.test_url, lambda: critic.get("flags_kind"), freeze) == ("denied", "stage_mismatch")
    analyst = access_for(engine, world.run, "analyst", "analysis")
    # Step 8b (Q6): the Analyst's list no longer holds records_full; coverage is on it at every stage.
    kind, got = _outcome(lambda: analyst.get("coverage"))
    assert kind == "allowed" and [s["source"] for s in got["sources"]] == ["mpea", "tamu_fcc"]


# --- Vocabularies and unrecognized counts -------------------------------------------------------

def test_vocabularies_mark_what_they_do_not_know():
    assert vocabulary.category("microstructure", "FCC+BCC+Sec.") == "FCC+BCC+Sec."
    assert vocabulary.category("microstructure", "FCC; yield strength 48213.579 MPa") == "unrecognized"
    assert vocabulary.category("phase_class", "fcc") == "unrecognized"
    assert vocabulary.category("test_type", None) == "unrecognized"
    assert vocabulary.code("primary", vocabulary.ANALYSIS_SET_KEYS) == "primary"
    assert vocabulary.code("drop 48213.579", vocabulary.SENSITIVITY_KEYS) == "unrecognized"
    assert vocabulary.unrecognized_counts([("phase_class", "FCC"), ("phase_class", "x"), ("microstructure", "y")]) \
        == {"microstructure": 1, "phase_class": 1}


def test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure():
    """Register 'accepted_disclosures': a syntactically valid DOI may contain digits."""
    assert vocabulary.doi(" 10.1038/ncomms10602") == "10.1038/ncomms10602"
    assert vocabulary.doi("10.1234/48213.579") == "10.1234/48213.579"
    assert vocabulary.doi("doi 48213.579") == "unrecognized"
    assert vocabulary.doi("") is None


def test_the_frozen_sources_have_no_unrecognized_category_value():
    from source_helpers import sealed_from_disk
    from hypocurate.sources import adapters
    for key in ("mpea", "tamu_fcc"):
        recs = adapters.read(sealed_from_disk(key)).records
        values = [(f, r.harmonized[f].value) for r in recs for f in vocabulary.CATEGORY_FIELDS
                  if r.harmonized[f].status in ("converted", "assigned_from_source", "assigned_by_decision")]
        assert vocabulary.unrecognized_counts(values) == {}, key


def test_unrecognized_values_are_counted_in_coverage_and_test_connection(engine):
    """Owner, 2026-10-05: counts only, per run and per source, never the values."""
    world = aw.build(engine, "analysis")
    cov = access_for(engine, world.run, "analyst", "analysis").get("coverage")
    assert cov["sources"][0] == {"source": "mpea", "search_status": "searched", "nothing_found": None,
                                 "unrecognized": {"microstructure": 1, "phase_class": 1, "processing_method": 1}}
    assert cov["sources"][1]["unrecognized"] == {} and "failure_reason" not in cov["sources"][1]
    report = connection.test_connection(engine, "mpea", n=1).to_json()  # the planted version is the latest
    assert report["unrecognized"] == {"microstructure": 1, "phase_class": 1, "processing_method": 1}
    assert "48213" not in str(report["unrecognized"])


def test_the_gap_report_input_has_codes_not_failure_text(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = role_input(bind(engine, world.run, world.settings["analyst"]))
    assert got["coverage"]["sources"][1]["search_status"] == "failed"
    assert set(got["coverage"]["sources"][1]) == {"source", "search_status", "nothing_found", "unrecognized"}
    # Step 8b (Q6): eligibility decisions no longer reach the Analyst directly; the rule codes reach it only
    # as the gap facts code stored (counts per rule code, from the `decisions` field read by the code role
    # gap_facts, whose codes are tested in test_access_statistics.py).
    assert "decisions" not in got and set(got["analyst_facts"]["gap"]) == {
        "minimums", "minimums_missed", "records_lacking_fields", "eligibility_rules", "sources", "kind"}
    assert set(allowed("analyst", "closed_without_freeze")) == set(got)


# --- Re-check fixes (ChatGPT, 2026-10-05) ----------------------------------------------------

PROBE = "hypocurate.access.guard_probe:probe"


def test_a_refusal_followed_by_a_timeout_is_still_logged(engine):
    """Re-check, finding 5: the child's refusal is reported from the captured standard error even
    when the child times out, and the timeout still propagates."""
    world = aw.build(engine, "before_lock")
    target = str(aw.REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv")
    with pytest.raises(subprocess.TimeoutExpired):
        run_guarded(PROBE, [{"op": "read", "path": target}, {"op": "sleep", "seconds": 120}], timeout=15,
                    audit=(engine, world.run))
    row = audit(engine, world.run)[-1]
    assert (row.function, row.detail["result"], row.detail["code"], row.detail["event"]) == (
        "guarded_run", "failed", "file_guard", "read")
    assert "truth.csv" in row.detail["what"]


def test_a_timeout_with_stderr_as_bytes_is_still_reported(engine, monkeypatch):
    """subprocess.TimeoutExpired may carry the captured output as bytes even in text mode."""
    world = aw.build(engine, "before_lock")
    line = b'HCGUARD {"event": "read", "what": "reading /somewhere/tests/x"}\n'

    def times_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=b"", stderr=line)

    monkeypatch.setattr(guarded.subprocess, "run", times_out)
    with pytest.raises(subprocess.TimeoutExpired):
        run_guarded(PROBE, [], timeout=1, audit=(engine, world.run))
    row = audit(engine, world.run)[-1]
    assert (row.detail["code"], row.detail["what"]) == ("file_guard", "reading /somewhere/tests/x")


def _forwardable(error: BaseException) -> str:
    """Every representation of an error a trusted formatter could forward to a model."""
    return "\n".join([str(error), repr(error), "".join(traceback.format_exception(error)),
                      repr(error.__cause__), repr(error.__context__), str(error.args)])


def test_a_reader_failure_carries_nothing_of_the_original_error(engine, monkeypatch, caplog):
    """Re-check, finding 5: the original error (here with a planted value) stays out of str,
    repr, the chained cause and context, and the formatted traceback; it is kept only in the
    process log."""
    world = aw.build(engine, "curation")

    def broken(conn, ctx):
        raise ValueError(f"leaked yield strength {aw.PLANTED['yield_strength']} MPa")

    monkeypatch.setitem(layer.READERS, "flags_kind", broken)
    with caplog.at_level(logging.ERROR, logger="hypocurate.access"):
        with pytest.raises(AccessFailed) as failed:
            access_for(engine, world.run, "critic", "curation").get("flags_kind")
    error = failed.value
    assert error.__cause__ is None and error.__context__ is None
    forwarded = _forwardable(error)
    assert "48213" not in forwarded and "leaked" not in forwarded and "ValueError" not in forwarded
    process_log = "\n".join(r.getMessage() + (r.exc_text or "") for r in caplog.records)
    assert "leaked yield strength 48213.579 MPa" in process_log


def test_a_database_failure_carries_nothing_of_the_original_error(engine, caplog):
    world = aw.build(engine, "curation")
    holder = make_engine(engine.test_url)
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        with caplog.at_level(logging.ERROR, logger="hypocurate.access"):
            with pytest.raises(AccessFailed) as read_failed:
                access_for(engine, world.run, "critic", "curation", lock_timeout_ms=200).get("flags_kind")
            with pytest.raises(AccessFailed) as bind_failed:
                bind(engine, world.run, world.settings["critic"], lock_timeout_ms=200)
        tx.rollback()
    holder.dispose()
    for error in (read_failed.value, bind_failed.value):
        assert error.code == "lock_timeout"
        assert error.__cause__ is None and error.__context__ is None
        forwarded = _forwardable(error)
        assert "LockNotAvailable" not in forwarded and "hc_write_lock" not in forwarded and "SELECT" not in forwarded
    assert "LockNotAvailable" in "\n".join(r.getMessage() + (r.exc_text or "") for r in caplog.records)
