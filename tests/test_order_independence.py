"""Confirmation round 2 (ChatGPT, 2026-10-06): no decision may depend on record ids, flag ids or
insertion order. Records linked by a chain of exact-duplicate pairs are one measurement: one
survivor by the plan's survivor rule (the last tie-break is the source's stable identity). A chain
touching a definite conflict enters with none of its records and none of the conflicting ones. The
freeze check verifies at most one record per chain.

The reviewer's A, B, C case (A-B exact by DOI, B-C exact by reference text, A-C possible) needs
three sources with known, equal test conditions; through the sprint 1 adapters Texas A&M reports no
test temperature, so it cannot arise there. It is tested on the same functions Checks, Inclusion
and the freeze use. The permutation test then runs through the real pipeline on the controlled
extract and on the real reference data."""
from __future__ import annotations

import copy
import itertools
import random

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, eligibility as el, extract, inclusion
from hypocurate.pipeline.flags import raise_flags, set_flags
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources import adapters
from hypocurate.sources.record import AdapterResult
from test_eligibility import PLAN, cond
from test_flags import rec

GROUPING = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
            {"source": "controlled_duplicates", "unit": "paper"}]
D = "10.1016/j.test.2026.042"


def plan_counting_possible_both():
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = GROUPING
    for e in plan["eligibility_rules"]:
        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
            e["rule"] = "in_scope"
    return plan


# The reviewer's records, by name: (source, DOI, reference text, grain size); E is another grain size.
ABC = {"A": ("mpea", D, "Reference X", 10.0), "B": ("tamu_fcc", D, "Reference Y", 10.0),
       "C": ("controlled_duplicates", None, "Reference Y", 10.0), "E": ("mpea", D, "Reference X", 40.0)}
ROW = {"A": 3, "B": 5, "C": 7, "E": 4}


def _decide_abc(plan, ids: dict, order: list):
    full = [rec(ids[n], s, gs=g, doi=doi, reference=ref) for n, (s, doi, ref, g) in ABC.items()]
    full = [full[list(ABC).index(n)] for n in order]
    flags = [{"id": 900 - k, "kind": f.kind, "category": f.category, "records": f.records}
             for k, f in enumerate(raise_flags(plan, full))]
    conds = {}
    for n, (s, doi, ref, g) in ABC.items():
        c = cond(ids[n], s, gs=g, doi=doi is not None, row=ROW[n])
        c["origin"] = f"{s}.csv:row:{ROW[n]}"
        conds[n] = c
    records = [conds[n] for n in order]
    per_set = {k: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
               for k, fs in set_flags(plan, full).items()}
    sets = el.all_sets(plan, records, flags, per_set)
    name = {ids[n]: n for n in ABC}
    by_id = {c["id"]: c for c in records}
    members = {k: el.members(r) for k, r in sets.items()}
    fp = checkpoints.freeze_fingerprint("p" * 64, by_id, members, sets, {})
    return ({k: {name[i]: r for i, r in rules.items()} for k, rules in sets.items()}, fp,
            el.primary_set_problems(set(members["primary"]), by_id, flags, True))


def test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order():
    plan = plan_counting_possible_both()
    results = set()
    for perm in itertools.permutations([11, 12, 13]):
        for order in (["A", "B", "C", "E"], ["C", "B", "A", "E"], ["E", "B", "C", "A"]):
            ids = {"A": perm[0], "B": perm[1], "C": perm[2], "E": 14}
            decided, fp, problems = _decide_abc(plan, ids, order)
            assert problems == [], (ids, order, problems)
            results.add((repr(sorted((k, sorted(v.items())) for k, v in decided.items())), fp))
    assert len(results) == 1
    decided = eval(next(iter(results))[0])
    primary = dict(dict(decided)["primary"])
    # One measurement: A, B and C are linked by exact pairs; one survivor by the survivor rule
    # (A: a DOI, and MPEA first in the source order).
    assert (primary["A"], primary["B"], primary["C"]) == ("in_scope", "duplicate_counted_once", "duplicate_counted_once")


def test_a_chain_touching_a_conflict_enters_with_none_of_its_records():
    """A-B exact, B-X conflict (X another record): none of A, B, X enters the primary set."""
    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc"), cond(4, "mpea", gs=40.0),
               cond(5, "tamu_fcc", gs=40.0)]
    flags = [{"id": 2, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
             {"id": 1, "kind": "values_disagree", "category": "differ beyond tolerance", "records": [2, 3]}]
    for ids_order in (flags, list(reversed(flags))):
        got = el.decide(PLAN, records, ids_order)
        assert (got[1], got[2], got[3]) == ("conflict_unresolved",) * 3
    survivor = el.decide(PLAN, records, flags, "conflicts_survivor_value")
    assert sum(survivor[i] == "in_scope" for i in (1, 2, 3)) == 1


def test_the_freeze_check_allows_at_most_one_record_per_chain():
    """A and C in the primary set, B out: no single exact pair is wholly inside, but A and C are
    the same measurement through B."""
    recs = {i: {"id": i, "source": "mpea", "kind": "measured"} for i in (1, 2, 3)}
    flags = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
             {"id": 2, "kind": "exact_duplicate", "category": "identical values", "records": [2, 3]}]
    problems = el.primary_set_problems({1, 3}, recs, flags, True)
    assert len(problems) == 1 and "exact duplicate" in problems[0]
    assert el.primary_set_problems({1}, recs, flags, True) == []
    conflict = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
                {"id": 2, "kind": "values_disagree", "category": "differ beyond tolerance", "records": [2, 3]}]
    assert any("conflict" in p for p in el.primary_set_problems({1, 3}, recs, conflict, True))


# --- through the real pipeline ------------------------------------------------------------------

def _permuted_run(db, vid, sources, seed, monkeypatch, marked):
    """One run of version `vid`, with each source's records stored in a shuffled order, the
    sources stored in a shuffled order, and unrelated records inserted first (shifting every id)."""
    rnd = random.Random(seed)
    real_read = adapters.read

    def shuffled(version):
        result = real_read(version)
        records = list(result.records)
        rnd.shuffle(records)
        return AdapterResult(tuple(records), result.blank_rows)

    with monkeypatch.context() as m:
        m.setattr(extract.adapters, "read", shuffled)
        for _ in range(seed):  # unrelated records: another run's, before this run's
            other = pw.run_of_version(db, vid, sources=("tamu_fcc",))
            checkpoints.lock_rules(db, other, reference_plan(vid))
            extract.store_records(db, other)
        rid = pw.run_of_version(db, vid, sources=sources, marked=marked)
        checkpoints.lock_rules(db, rid, reference_plan(vid))
        order = list(sources)
        rnd.shuffle(order)
        for key in order:
            extract.store_source(db, rid, key)
    checks.run_checks(db, rid)
    inclusion.decide_run(db, rid)
    checkpoints.freeze_dataset(db, rid)
    with db.connect() as conn:
        identity = {i: f"{s}|{k}|{x}" for i, s, k, x in conn.execute(text(
            "SELECT r.id, s.key, r.source_item_key, r.item_index FROM record r JOIN source_version sv "
            "ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r"),
            dict(r=rid))}
        decisions = {identity[i]: rule for i, rule in conn.execute(text(
            "SELECT record_id, rule FROM run_record WHERE run_id = :r"), dict(r=rid))}
        sets = {}
        for key, i in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr "
                                        "ON asr.analysis_set_id = a.id WHERE a.run_id = :r"), dict(r=rid)):
            sets.setdefault(key, set()).add(identity[i])
        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
                             dict(r=rid)).scalar_one()
        diffs = {k: {identity[int(i)]: rule for i, rule in v.items()} for k, v in stage["differences_from_primary"].items()}
        fp = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar_one()
    return decisions, sets, diffs, fp


@pytest.mark.parametrize("sources, marked", [(("mpea", "controlled_duplicates"), True), (("mpea", "tamu_fcc"), False)],
                         ids=["controlled_extract", "reference_data"])
def test_permuted_ids_and_insertion_order_give_the_same_frozen_result(db, monkeypatch, sources, marked):
    """The same data, stored with ids and insertion order permuted three ways: identical decisions
    for every record, identical membership of the primary set and every sensitivity set, and the
    same freeze fingerprint."""
    pw.registered(db, ("mpea", "tamu_fcc", "controlled_duplicates"))
    vid = pw.version_of(db, pw.dispatched_run(db, sources=("tamu_fcc",)))
    results = [_permuted_run(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
    first = results[0]
    assert len(first[0]) > 1000 and first[1]["primary"]
    for other in results[1:]:
        assert other[0] == first[0]  # every record's decision
        assert other[1] == first[1]  # the primary set and every sensitivity set
        assert other[2] == first[2]  # each sensitivity set's rules
        assert other[3] == first[3]  # the freeze fingerprint
