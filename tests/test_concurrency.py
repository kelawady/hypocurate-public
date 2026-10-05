"""Step 3 fix, review finding 1: the locking protocol, shown with two connections.

In each test, transaction A does its write and stays open. Transaction B starts in a
thread and must wait on A's lock (checked in pg_stat_activity). A then commits, and B
either sees A's committed write (serialized) or is rejected. Every race the review
describes is run in both orders."""
import threading
import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from model_builder import FP, World, files_fingerprint, sha


@pytest.fixture
def w(db):
    return World(db)


def waiting_on_a_lock(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
            "AND wait_event_type = 'Lock' AND state = 'active'")).scalar()


def race(engine, first: str, second: str, first_params=None, second_params=None):
    """Runs `first` in an open transaction A, then `second` in transaction B in a thread.
    Asserts that B waited on A's lock, commits A, and returns B's error (or None)."""
    outcome = {}

    def run_second():
        try:
            with engine.begin() as b:
                b.execute(text(second), second_params or {})
            outcome["error"] = None
        except Exception as error:  # reported to the test below
            outcome["error"] = error

    with engine.connect() as a:
        tx = a.begin()
        a.execute(text(first), first_params or {})
        thread = threading.Thread(target=run_second)
        thread.start()
        deadline = time.monotonic() + 10
        while waiting_on_a_lock(engine) == 0 and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert thread.is_alive() and waiting_on_a_lock(engine) == 1, "B should be waiting on A's lock"
        tx.commit()
    thread.join(30)
    assert not thread.is_alive()
    return outcome["error"]


def rejected(error, match):
    assert isinstance(error, IntegrityError), error
    assert match in str(error), str(error)


# --- primary-set member against the dataset freeze ---------------------------------------------------

def set_up_freeze(w):
    """A locked run with two eligible records: one already in primary, one not yet."""
    rid = w.locked()
    first, second = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, first)
    w.decide(rid, second)
    primary = w.analysis_set(rid)
    w.add(primary, first)
    return rid, primary, second


def test_member_first_then_freeze_counts_it(w):
    rid, primary, second = set_up_freeze(w)
    error = race(w.e, "INSERT INTO analysis_set_record VALUES (:s, :c)",
                 "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 2)",
                 dict(s=primary, c=second), dict(r=rid, fp=FP))
    assert error is None  # the freeze waited and saw both members
    assert w.val("SELECT n_records FROM run_snapshot WHERE run_id = :r", r=rid) == 2


def test_freeze_first_then_flag_is_rejected(w):
    rid = w.locked()
    first = w.record(rid, key="a")
    w.decide(rid, first)
    w.add(w.analysis_set(rid), first)
    late = w.record(rid, key="b")
    w.decide(rid, late, eligible=False, rule="out of scope")
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
                 dict(r=rid, fp=FP), dict(r=rid))
    rejected(error, "after the dataset freeze")


def test_freeze_first_then_sensitivity_member_is_rejected(w):
    rid = w.running()
    w.lock(rid, keys=["scope_not_confirmed"])
    first, other = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, first)
    w.decide(rid, other, eligible=False, rule="scope not confirmed")
    w.add(w.analysis_set(rid), first)
    sensitivity = w.analysis_set(rid, "scope_not_confirmed")
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 "INSERT INTO analysis_set_record VALUES (:s, :c)",
                 dict(r=rid, fp=FP), dict(s=sensitivity, c=other))
    rejected(error, "after the dataset freeze")
    assert w.val("SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sensitivity) == 0


# --- chosen sources against submission ----------------------------------------------------------------

def test_source_first_then_submission_includes_it(w):
    vid = w.draft(sources=("mpea",))
    error = race(w.e, "INSERT INTO hypothesis_version_source VALUES (:v, :s)",
                 "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v",
                 dict(v=vid, s=w.source["tamu_fcc"]), dict(v=vid))
    assert error is None
    assert w.val("SELECT count(*) FROM hypothesis_version_source WHERE hypothesis_version_id = :v", v=vid) == 2


def test_submission_first_then_source_is_rejected(w):
    vid = w.draft(sources=("mpea",))
    error = race(w.e, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v",
                 "INSERT INTO hypothesis_version_source VALUES (:v, :s)",
                 dict(v=vid), dict(v=vid, s=w.source["tamu_fcc"]))
    rejected(error, "only while the version is a draft")
    assert w.val("SELECT count(*) FROM hypothesis_version_source WHERE hypothesis_version_id = :v", v=vid) == 1


# --- dispatch metadata against starting the run ---------------------------------------------------------

def agent_setting(w):
    return w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 1, 'i', 'm') "
                 "RETURNING id")


def test_dispatch_metadata_first_then_start_waits(w):
    setting, rid = agent_setting(w), w.run()
    error = race(w.e, "INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)",
                 "UPDATE run SET status = 'running', started_at = now() WHERE id = :r",
                 dict(r=rid, s=setting), dict(r=rid))
    assert error is None
    assert w.val("SELECT count(*) FROM run_agent_setting WHERE run_id = :r", r=rid) == 1


def test_start_first_then_dispatch_metadata_is_rejected(w):
    setting, rid = agent_setting(w), w.run()
    error = race(w.e, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r",
                 "INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)",
                 dict(r=rid), dict(r=rid, s=setting))
    rejected(error, "recorded at dispatch")


# --- a child write against completion ----------------------------------------------------------------------

COMPLETE = "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r"


def test_flag_first_then_completion_waits(w):
    rid = w.running()
    error = race(w.e, "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')", COMPLETE,
                 dict(r=rid), dict(r=rid))
    assert error is None
    assert w.val("SELECT count(*) FROM flag WHERE run_id = :r", r=rid) == 1


def test_completion_first_then_flag_is_rejected(w):
    rid = w.running()
    error = race(w.e, COMPLETE, "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
                 dict(r=rid), dict(r=rid))
    rejected(error, "only while the run is running")


def test_completion_first_then_search_result_is_rejected(w):
    rid = w.running()
    error = race(w.e, COMPLETE, "UPDATE run_source SET search_status = 'searched', decided_at = now() "
                                "WHERE run_id = :r AND source_id = :s",
                 dict(r=rid), dict(r=rid, s=w.source["mpea"]))
    rejected(error, "only while the run is running")
    assert w.val("SELECT search_status FROM run_source WHERE run_id = :r AND source_id = :s",
                 r=rid, s=w.source["mpea"]) == "pending"


# --- "no dataset frozen" against the freeze -------------------------------------------------------------------

NO_DATASET = ("INSERT INTO calibration_result (run_id, status, reason) "
              "VALUES (:r, 'unavailable', 'no_dataset_frozen')")


def ready_to_freeze(w):
    rid = w.locked()
    rec = w.record(rid)
    w.decide(rid, rec)
    w.add(w.analysis_set(rid), rec)
    return rid


def test_no_dataset_first_then_freeze_is_rejected(w):
    rid = ready_to_freeze(w)
    error = race(w.e, NO_DATASET, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 dict(r=rid), dict(r=rid, fp=FP))
    rejected(error, "already recorded that no dataset was frozen")


def test_freeze_first_then_no_dataset_is_rejected(w):
    rid = ready_to_freeze(w)
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)", NO_DATASET,
                 dict(r=rid, fp=FP), dict(r=rid))
    rejected(error, "calibration is reported per analysis")


# --- a source file against sealing its version --------------------------------------------------------------------

def test_file_first_then_sealing_includes_it(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    both = files_fingerprint({"a.csv": b"a", "b.csv": b"b"})
    error = race(w.e, "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                 "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                 dict(v=sv, h=sha(b"b"), c=b"b"), dict(v=sv, fp=both))
    assert error is None  # the seal waited, then fingerprinted both files


def test_sealing_first_then_file_is_rejected(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    error = race(w.e, "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                 "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                 dict(v=sv, fp=files_fingerprint({"a.csv": b"a"})), dict(v=sv, h=sha(b"b"), c=b"b"))
    rejected(error, "sealed source version")
    assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=sv) == 1
