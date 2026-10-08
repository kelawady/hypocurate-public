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
from answer_shapes import WRONG, variants
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


# Fix round 1 (owner, 2026-10-07): only a flag naming two or more records is sent to the Critic. Flags between
# records are raised across sources only, so two pairs are split between MPEA and a second source in MPEA layout:
# one the same values in both (an exact duplicate), one whose yield strength differs beyond the tolerance. The
# CONFLICT rows above stay as single-record flags, which are not sent. Distinctive numbers, for the planted test.
PAIR_SAME = pw.mpea_row("CoCrFeNi", 5.0, 5123.125, doi="10.1016/j.test.2026.102")
PAIR_MPEA = pw.mpea_row("CoCrNi", 3.0, 6123.375, doi="10.1016/j.test.2026.101")
PAIR_OTHER = pw.mpea_row("CoCrNi", 3.0, 7960.375, doi="10.1016/j.test.2026.101")
SOURCES = ("mpea", "controlled_duplicates")
NOT_SENT_VALUES = ("7311.375", "8911.625", "7311.4", "8911.6", "5511.25", "4411.5",
                   "6123.375", "7960.375", "5123.125", "6123.4", "7960.4", "5123.1")


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
                            "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
    yield e
    e.dispose()


def version(engine, sources=SOURCES):
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       sources)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q.version_id


def checked_run(engine, vid):
    """A run of version `vid` through Checks: its flags are raised, nothing decided yet."""
    # The second source is constructed test data: its runs are marked as tests (fix round 1).
    if not one(engine, "SELECT count(*) FROM run WHERE hypothesis_version_id = :v", v=vid):
        rid = queries.dispatch(engine, vid, constructed_test_data=True)
    else:
        rid = pw.run_of_version(engine, vid, SOURCES, marked=True, agents=("planner", "critic", "analyst"))
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

def multi_flag_ids(engine, rid):
    """The flags naming two or more records: the only ones sent to the Critic (fix round 1)."""
    return [r[0] for r in rows(engine, "SELECT f.id FROM flag f WHERE f.run_id = :r AND (SELECT count(*) FROM "
                                       "flag_record fr WHERE fr.flag_id = f.id) >= 2 ORDER BY f.id", r=rid)]


def test_the_critics_complete_request_holds_no_compared_number_or_outcome(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = multi_flag_ids(engine, rid)
    assert len(flags) == 2  # the two pairs split between the sources
    stub.queue(reply({str(f): {"class": "cannot_tell", "reason": "the metadata are the same"} for f in flags}))
    run_critic(engine, rid, stub)
    raw = stub.requests[0]["raw"].decode()
    for v in NOT_SENT_VALUES:
        assert v not in raw, v
    assert "compared_values" not in raw and "tools" not in json.loads(raw)
    assert CRITIC_INSTRUCTION in json.dumps(json.loads(raw), ensure_ascii=False)
    # The kind and category of each flag sent are told; a single-record flag is not sent (fix round 1; was: the
    # single-record 'invalid_value' flags were sent).
    assert "differ beyond tolerance" in raw and "values_disagree" in raw and "exact_duplicate" in raw
    assert "invalid_value" not in raw and "physically impossible" not in raw


def test_each_flag_is_its_own_block_and_the_instruction_says_so(engine, stub):
    """Owner, 2026-10-07: each flag stands alone; the request renders each as its own separated block."""
    rid = checked_run(engine, version(engine))
    flags = multi_flag_ids(engine, rid)
    stub.queue(reply({str(f): {"class": "cannot_tell", "reason": "x"} for f in flags}))
    run_critic(engine, rid, stub)
    content = json.dumps(json.loads(stub.requests[0]["raw"]), ensure_ascii=False)
    for f in flags:
        assert f"=== Flag {f}: judge this flag on its own ===" in content and f"=== end of flag {f} ===" in content
    assert "Each flag stands alone: judge it only on the records it names, and never compare records across flags." \
        in CRITIC_INSTRUCTION


def test_each_valid_entry_is_written_once_and_an_invalid_one_is_left_unclassified(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = multi_flag_ids(engine, rid)
    good, *rest = flags
    assert rest
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
    data = {"flags_kind": [{"id": i, "records": [10 * i, 10 * i + 1]} for i in range(7)]}
    assert [len(b) for b in critic.batches(data, 3)] == [3, 3, 1]


# --- scope: only flags naming two or more records are sent (owner, 2026-10-07, fix round 1) -------------------

def test_only_flags_naming_two_or_more_records_are_batched():
    data = {"flags_kind": [{"id": 1, "records": [5]}, {"id": 2, "records": [5, 6]}, {"id": 3, "records": [7, 8, 9]},
                           {"id": 4, "records": []}]}
    assert [[f["id"] for f in b] for b in critic.batches(data, 10)] == [[2, 3]]
    assert critic.MIN_RECORDS == 2


def test_a_single_record_flag_is_never_sent_and_is_shown_as_not_classified(engine, stub):
    from hypocurate import cli_runs
    rid = checked_run(engine, version(engine))
    single = [f for f in flag_ids(engine, rid) if f not in multi_flag_ids(engine, rid)]
    assert len(single) == 2
    stub.respond(lambda raw: reply({str(f): {"class": "same_measurement", "reason": "same paper and alloy"}
                                    for f in multi_flag_ids(engine, rid)}))
    out = run_critic(engine, rid, stub)
    assert len(stub.requests) == 1 and out.classified == 2
    content = json.dumps(json.loads(stub.requests[0]["raw"]), ensure_ascii=False)
    for f in single:
        assert f"=== Flag {f}:" not in content
        assert rows(engine, "SELECT critic_class, critic_reason FROM flag WHERE id = :f", f=f) == [(None, None)]
        assert str(f) not in out.refused
    stage = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stages[0])
    assert sorted(stage["not_sent"]) == sorted(single)
    shown = {x["flag"]: x for x in cli_runs.critic_flags(engine, rid)}
    for f in single:
        assert shown[f]["critic"] == "not classified: single-record flag" and shown[f]["records"] == 1
        assert shown[f]["kind"] == "invalid_value" and shown[f]["category"] == "physically impossible"
    for f in multi_flag_ids(engine, rid):
        assert shown[f]["critic"] == "same measurement reported twice: same paper and alloy"


def test_a_run_with_only_single_record_flags_makes_no_critic_call(migrated_database, stub):
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    rid = checked_run(engine, version(engine, ("mpea",)))
    assert len(flag_ids(engine, rid)) == 2 and multi_flag_ids(engine, rid) == []
    out = run_critic(engine, rid, stub)
    assert stub.requests == [] and out.classified == 0 and out.failures == []
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stages[0]) == "skipped"
    assert one(engine, "SELECT output->>'reason' FROM stage_result WHERE id = :s", s=out.stages[0]) == \
        "no_multi_record_flags"
    assert one(engine, "SELECT count(*) FROM model_call") == 0


def test_with_no_flag_nothing_is_sent(migrated_database, stub):
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3))})
    rid = checked_run(engine, version(engine, ("mpea",)))
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


# --- finding 5 (fix round 1): wrong-type answer shapes ---------------------------------------------------------

BATCH = [{"id": 7, "kind": "values_disagree", "category": "c", "records": []},
         {"id": 8, "kind": "values_disagree", "category": "c", "records": []}]
VALID = {"7": {"class": "cannot_tell", "reason": "the metadata are the same"},
         "8": {"class": "same_measurement", "reason": "same paper and alloy"}}


@pytest.mark.parametrize("shape", [{"7": {"class": []}}, {"7": {"class": {}}}, {"7": {"class": ["cannot_tell"]}},
                                   {"7": {"class": {"cannot_tell": 1}}}, {"7": {"class": 1}}, {"7": {"class": None}}])
def test_a_class_of_the_wrong_type_leaves_that_entry_unclassified(shape):
    """The reviewer's reproduction: a list or object as the class raised TypeError at the membership test."""
    out = critic.classify(shape, BATCH)
    assert out.accepted == {} and out.refused["7"] in ("class_not_allowed", "malformed_entry")
    assert out.refused["8"] == "not_answered"


def test_every_wrong_type_at_every_position_is_refused_entry_by_entry():
    for path, value, answer in variants(VALID):
        if not isinstance(answer, dict):
            continue  # not a JSON object: the interface's check makes it malformed (corrected once)
        out = critic.classify(answer, BATCH)                    # never raises
        if not path:                                            # the whole answer replaced by another object
            assert set(out.refused) >= {"7", "8"} and not out.accepted, value
            continue
        touched = str(path[0])
        for key in ("7", "8"):
            if key != touched:
                assert out.accepted.get(int(key)) == (VALID[key]["class"], VALID[key]["reason"]), (path, value)
        if touched in ("7", "8") and int(touched) not in out.accepted:
            assert out.refused[touched], (path, value)


def test_a_non_object_answer_is_malformed():
    for value in WRONG:
        if not isinstance(value, dict):
            assert critic.check({"classification": json.dumps(value)}) == "malformed"



def test_the_request_on_the_controlled_duplicate_file_holds_no_answer_material(migrated_database, stub):
    """The real controlled duplicate extract with MPEA: the flags sent name two records each, and the request holds
    nothing of the answer files (truth.csv, the Critic's key): no case name, explanation or key wording."""
    from test_controlled_duplicates import _row_specific_markers, key_markers
    engine = make_engine(migrated_database)
    pw.registered(engine, SOURCES)
    rid = checked_run(engine, version(engine))
    flags = multi_flag_ids(engine, rid)
    assert len(flags) == 10 and flags == flag_ids(engine, rid)
    stub.respond(lambda raw: reply({str(f): {"class": "cannot_tell", "reason": "x"} for f in flags}))
    run_critic(engine, rid, stub)
    content = json.dumps([json.loads(r["raw"]) for r in stub.requests], ensure_ascii=False)
    leaked = [m for m in _row_specific_markers() | key_markers() if m and m in content]
    assert leaked == []


# --- the Critic's output is labelled wherever it is shown (owner, 2026-10-08, after the confirmation round) -------

ADVICE = "Language-model advice; classification and reason not verified; not used in decisions."


def test_every_shown_critic_classification_carries_the_unverified_advice_label(engine, stub):
    """flag_display and `show` (whose output `run` and `dispatch` print) put the label beside each class and reason;
    a flag with no class (single-record, or not classified) shows code's own words and no label."""
    from hypocurate import cli_runs
    rid = checked_run(engine, version(engine))
    multi = multi_flag_ids(engine, rid)
    stub.respond(lambda raw: reply({str(f): {"class": "same_measurement", "reason": "same paper and alloy"}
                                    for f in multi}))
    run_critic(engine, rid, stub)
    for shown in (critic.flag_display(engine, rid), cli_runs.show(engine, rid)["flags"]):
        by_flag = {x["flag"]: x for x in shown}
        for f in multi:
            assert by_flag[f]["critic"] == "same measurement reported twice: same paper and alloy"
            assert by_flag[f]["critic_label"] == ADVICE
        for f, x in by_flag.items():
            if f not in multi:
                assert x["critic"] == "not classified: single-record flag" and "critic_label" not in x
    assert critic.ADVICE_LABEL == ADVICE
