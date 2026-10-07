"""Step 8b, milestone 5: the Critic (owner, A7) and the owner's standing requirement that no code decision reads
the Critic's class. Every model call goes to the local stub provider."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.access.vocabulary import CRITIC_CLASSES
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion, queries
from hypocurate.pipeline.agents import critic
from hypocurate.pipeline.agents.settings import CRITIC_INSTRUCTION
from stats_world import plan_for, small_rows

import hypocurate

PACKAGE = Path(hypocurate.__file__).resolve().parent  # the code under test (a mutation copy too)
# Two records whose tensile strength is below their yield strength: Checks raises an invalid-value flag on
# each (flags between records are raised across sources only). Distinctive numbers, for the planted test.
CONFLICT = [{**pw.mpea_row("CoCrNi", 2.0, 7311.375, doi="10.1016/j.test.2026.001"), "PROPERTY: UTS (MPa)": "5511.25"},
            {**pw.mpea_row("CoCrNi", 4.0, 8911.625, doi="10.1016/j.test.2026.002"), "PROPERTY: UTS (MPa)": "4411.5"}]


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    yield e
    e.dispose()


def version(engine):
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q.version_id


def checked_run(engine, vid):
    """A run of version `vid` through Checks: its flags are raised, nothing decided yet."""
    if not one(engine, "SELECT count(*) FROM run WHERE hypothesis_version_id = :v", v=vid):
        rid = queries.dispatch(engine, vid)
    else:
        rid = pw.run_of_version(engine, vid, ("mpea",), agents=("planner", "critic", "analyst"))
    if one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued":
        queries.start(engine, rid)
    checkpoints.lock_rules(engine, rid, plan_for(vid))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    return rid


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def flag_ids(engine, rid):
    return [r[0] for r in rows(engine, "SELECT id FROM flag WHERE run_id = :r ORDER BY id", r=rid)]


def reply(entries):
    return sp.reply(sp.fields(classification=json.dumps(entries)))


def run_critic(engine, rid, stub):
    return critic.run_critic(engine, rid, client_options=sp.client_options(stub))


# --- the request and the answer --------------------------------------------------------------------------

def test_the_critics_complete_request_holds_no_compared_number_or_outcome(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = flag_ids(engine, rid)
    assert flags  # the conflicting pair raised at least one flag
    stub.queue(reply({str(f): {"class": "cannot_tell", "reason": "the metadata are the same"} for f in flags}))
    run_critic(engine, rid, stub)
    raw = stub.requests[0]["raw"].decode()
    for v in ("7311.375", "8911.625", "7311.4", "8911.6", "5511.25", "4411.5"):
        assert v not in raw, v
    assert "compared_values" not in raw and "tools" not in json.loads(raw)
    assert CRITIC_INSTRUCTION in json.dumps(json.loads(raw), ensure_ascii=False)
    assert "physically impossible" in raw and "invalid_value" in raw  # the kind and category are told


def test_each_valid_entry_is_written_once_and_an_invalid_one_is_left_unclassified(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = flag_ids(engine, rid)
    good, *rest = flags
    answer = {str(good): {"class": "same_measurement", "reason": "same DOI, alloy and grain size"},
              "999999": {"class": "cannot_tell"}}
    for f in rest:
        answer[str(f)] = {"class": "agrees"}  # not an allowed class
    stub.queue(reply(answer))
    out = run_critic(engine, rid, stub)
    assert len(stub.requests) == 1  # per-entry refusals are not retried
    assert rows(engine, "SELECT critic_class, critic_reason FROM flag WHERE id = :f", f=good) == [
        ("same_measurement", "same DOI, alloy and grain size")]
    assert out.refused["999999"] == "unknown_flag"
    for f in rest:
        assert out.refused[str(f)] == "class_not_allowed"
        assert one(engine, "SELECT critic_class FROM flag WHERE id = :f", f=f) is None


@pytest.mark.parametrize("entry, code", [({"class": "cannot_tell", "reason": "x" * 301}, "reason_not_allowed"),
                                         ({"class": "cannot_tell", "reason": "  "}, "reason_not_allowed"),
                                         ({"class": "cannot_tell", "extra": 1}, "malformed_entry"),
                                         ("cannot_tell", "malformed_entry")])
def test_a_reason_is_never_truncated_and_an_entry_has_a_fixed_form(entry, code):
    got = critic.classify({"7": entry}, [{"id": 7, "records": []}])
    assert got.refused == {"7": code} and not got.accepted


def test_a_malformed_answer_is_corrected_once_then_every_flag_stays_unclassified(engine, stub):
    rid = checked_run(engine, version(engine))
    stub.queue(sp.reply(sp.fields(classification="the first flag looks like a duplicate")),
               sp.reply(sp.fields(classification="still prose")))
    out = run_critic(engine, rid, stub)
    assert out.failures == ["malformed"] and len(stub.requests) == 2
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stages[0]) == "failed"


def test_flags_are_sent_in_batches():
    data = {"flags_kind": [{"id": i, "records": []} for i in range(7)]}
    assert [len(b) for b in critic.batches(data, 3)] == [3, 3, 1]


def test_with_no_flag_nothing_is_sent(migrated_database, stub):
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3))})
    rid = checked_run(engine, version(engine))
    assert flag_ids(engine, rid) == []
    out = run_critic(engine, rid, stub)
    assert stub.requests == [] and out.classified == 0
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stages[0]) == "skipped"


# --- no code decision reads the Critic's class (the owner's standing requirement) -----------------------

def decided(engine, rid):
    """Everything code decides after the Critic: the eligibility decisions and sets by stable identity, the
    freeze record and its fingerprint, and the stored statistics and gap facts."""
    inclusion.decide_run(engine, rid)
    freeze = checkpoints.freeze_dataset(engine, rid)
    # The freeze record names the most influential group's records by database id (not part of the
    # fingerprint), which differs between any two runs: compared here by stable identity.
    influential = freeze.get("most_influential") or {}
    if "records" in influential:
        influential["records"] = [one(engine, "SELECT source_item_key || ':' || item_index FROM record WHERE id = :i",
                                      i=i) for i in influential["records"]]
    analysis.run_statistics(engine, rid)
    identity = "rec.source_item_key || ':' || rec.item_index"
    return {
        "decisions": rows(engine, f"SELECT {identity}, rr.eligible, rr.rule FROM run_record rr JOIN record rec "
                                  f"ON rec.id = rr.record_id WHERE rr.run_id = :r ORDER BY 1", r=rid),
        "sets": rows(engine, f"SELECT a.key, {identity} FROM analysis_set a JOIN analysis_set_record asr ON "
                             f"asr.analysis_set_id = a.id JOIN record rec ON rec.id = asr.record_id "
                             f"WHERE a.run_id = :r ORDER BY 1, 2", r=rid),
        "freeze": freeze,
        "statistics": one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid),
        "gap_facts": one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid),
    }


def test_changing_every_class_changes_no_decision_set_fingerprint_or_result(engine):
    vid = version(engine)
    plain = checked_run(engine, vid)
    classified = checked_run(engine, vid)
    flags = flag_ids(engine, classified)
    assert flags
    rng = random.Random(8)
    with engine.begin() as conn:
        for f in flags:
            conn.execute(text("UPDATE flag SET critic_class = :c, critic_reason = 'random', classified_at = now() "
                              "WHERE id = :f"), dict(c=rng.choice(sorted(CRITIC_CLASSES)), f=f))
    a, b = decided(engine, plain), decided(engine, classified)
    assert a["freeze"]["fingerprint"] == b["freeze"]["fingerprint"]
    assert a == b


def test_no_decision_path_reads_the_critics_class():
    """A source scan behind the test above: outside the Critic's own module, only `flags_full` (a field on no
    role's list until step 12) reads the class; no pipeline module does."""
    readers = []
    for path in PACKAGE.rglob("*.py"):
        rel = "hypocurate/" + path.relative_to(PACKAGE).as_posix()
        if "/migrations/" in rel or rel in ("hypocurate/db/models.py", "hypocurate/access/vocabulary.py"):
            continue
        if re.search(r"critic_class|critic_reason", path.read_text()):
            readers.append(rel)
    assert sorted(readers) == ["hypocurate/access/fields.py", "hypocurate/pipeline/agents/critic.py"]
    fields = (PACKAGE / "access/fields.py").read_text()
    uses = [m.start() for m in re.finditer(r"critic_class", fields)]
    start = fields.index("def flags_full(")
    end = fields.index("\ndef ", start + 1)
    assert uses and all(start <= u < end for u in uses)
