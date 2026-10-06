"""Third confirmation (ChatGPT, 2026-10-06), the owner's fixed rule: no record connected to a
definite conflict enters the primary set, under any plan. A survivor is allowed only in the
sensitivity set 'conflicts_survivor_value'. Enforced at validation (test_plan), at application
and at the freeze.

The reviewer's case: an exact chain A-B touching a conflict B-C, and a plan mapping conflicts to
"counted once". Two shapes Checks can produce:
- "one paper": A, B and C cite the same DOI and C reports the measurement 10% higher; Checks flags
  the group A, B, C as a conflict and keeps the exact pair A-B;
- "only through B": A and B cite the same DOI (A 404, B 400 MPa: exact), C has no DOI and B's
  reference text (408.5 MPa: a conflict with B, 2.1%), and A-C is only a possible duplicate
  (1.1%). The group is labelled possible duplicate; the exact pair A-B and the conflict pair B-C
  are kept as their own flags; A is linked to the conflict only through B. (Without the A-C link
  the group is not fully linked and Checks labels it "several candidates", excluded anyway.) Through the
sprint 1 adapters a three-source chain cannot arise (Texas A&M reports no test temperature), so
it is tested on the shared functions; the pipeline tests use the controlled extract's real
conflicting rows 7-8 (MPEA row 1278 and its copy with yield strength x 1.3)."""
from __future__ import annotations

import copy

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, eligibility as el, extract, inclusion, plan as plan_module
from hypocurate.pipeline.flags import raise_flags, set_flags
from hypocurate.pipeline.plan import reference_plan
from hypocurate.pipeline.writes import Refused
from test_eligibility import PLAN, cond
from test_flags import rec


def survivor_plan(base):
    plan = copy.deepcopy(base)
    for e in plan["eligibility_rules"]:
        if e["flag_kind"] == "values_disagree":
            e["rule"] = "duplicate_counted_once"
    return plan


@pytest.fixture
def no_validation(monkeypatch):
    """Switches off the rule guards (validation and the check when rules are built)."""
    monkeypatch.setattr(el, "fixed_rule_problems", lambda rules: [])
    monkeypatch.setattr(plan_module, "fixed_rule_problems", lambda rules: [])


SHAPES = {
    "one paper": ((400.0, "10.1/d", "Reference X"), (400.0, "10.1/d", "Reference X"), (440.0, "10.1/d", "Reference X"),
                  [("values_disagree", [1, 2, 3]), ("exact_duplicate", [1, 2])]),
    "only through B": ((404.0, "10.1/d", "Reference X"), (400.0, "10.1/d", "Reference Y"), (408.5, None, "Reference Y"),
                       [("possible_duplicate", [1, 2, 3]), ("exact_duplicate", [1, 2]), ("values_disagree", [2, 3])]),
}


def _chain(shape="only through B"):
    (ya, da, ra), (yb, db, rb), (yc, dc, rc), expected = SHAPES[shape]
    plan = survivor_plan(PLAN)
    # Step 7b: C (no DOI in one shape) is grouped by dataset so that it keeps a group; identity is
    # unchanged (Checks' paper identity never reads the grouping).
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "dataset"}]
    full = [rec(1, "mpea", ys=ya, doi=da, reference=ra), rec(2, "tamu_fcc", ys=yb, doi=db, reference=rb),
            rec(3, "controlled_duplicates", ys=yc, doi=dc, reference=rc),
            rec(4, "mpea", gs=40.0, ys=300.0, doi=da, reference=ra)]
    flags = [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
             for n, f in enumerate(raise_flags(plan, full), start=1)]
    per_set = {k: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
               for k, fs in set_flags(plan, full).items()}
    records = [cond(1, "mpea"), cond(2, "tamu_fcc"), cond(3, "controlled_duplicates", doi=dc is not None),
               cond(4, "mpea", gs=40.0)]
    assert [(f["kind"], f["records"]) for f in flags] == expected
    return plan, records, flags, per_set


@pytest.mark.parametrize("shape", SHAPES)
def test_the_reviewers_chain_enters_primary_with_none_of_its_records(no_validation, shape):
    plan, records, flags, per_set = _chain(shape)
    sets = el.all_sets(plan, records, flags, per_set)
    assert {i: sets["primary"][i] for i in (1, 2, 3)} == {i: "conflict_unresolved" for i in (1, 2, 3)}
    # The survivor is allowed only in the sensitivity set that names it.
    assert sum(sets["conflicts_survivor_value"][i] == "in_scope" for i in (1, 2, 3)) == 1
    for key, rules in sets.items():
        if key != "conflicts_survivor_value":
            assert all(rules[i] != "in_scope" for i in (1, 2, 3)), key


@pytest.mark.parametrize("shape", SHAPES)
def test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group(no_validation, shape):
    plan, records, flags, _ = _chain(shape)
    recs = {r["id"]: r for r in records}
    for member in (1, 2, 3):  # A alone (only exact-linked to the conflict), B alone, C alone
        problems = el.primary_set_problems({member, 4}, recs, flags, True, grouping=el.settings(plan).grouping)
        assert any("conflict" in p for p in problems), member
    assert el.primary_set_problems({4}, recs, flags, True, grouping=el.settings(plan).grouping) == []


# --- through the real pipeline: the controlled extract's conflicting rows 7-8 --------------------------

def _decided(db, monkeypatch, bypass_application=False):
    pw.registered(db, ("mpea", "controlled_duplicates"))
    if bypass_application:  # a simulated gap in the application rule as well
        monkeypatch.setattr(el, "conflict_survivor_allowed", lambda key: True, raising=False)
    rid = pw.dispatched_run(db, sources=("mpea", "controlled_duplicates"), marked=True)
    content = survivor_plan(reference_plan(pw.version_of(db, rid)))
    checkpoints.lock_rules(db, rid, content)
    extract.store_records(db, rid)
    checks.run_checks(db, rid)
    sets = inclusion.decide_run(db, rid)
    with db.connect() as conn:
        ids = dict(conn.execute(text("SELECT source_item_key, id FROM record WHERE extraction_run_id = :r AND "
                                     "source_item_key IN ('MPEA_dataset.csv:row:1278', 'extract.csv:row:6')"),
                                dict(r=rid)).all())
    return rid, sets, ids["MPEA_dataset.csv:row:1278"], ids["extract.csv:row:6"]


def test_a_plan_mapping_conflicts_to_counted_once_admits_neither_record(db, monkeypatch, no_validation):
    rid, sets, mpea, copy_ = _decided(db, monkeypatch)
    assert (sets["primary"][mpea], sets["primary"][copy_]) == ("conflict_unresolved", "conflict_unresolved")
    assert (sets["conflicts_survivor_value"][mpea], sets["conflicts_survivor_value"][copy_]) == \
        ("in_scope", "duplicate_counted_once")
    assert checkpoints.freeze_dataset(db, rid)["frozen"] is True


def test_the_freeze_refuses_one_conflict_record_with_every_safeguard_bypassed(db, monkeypatch, no_validation):
    rid, sets, mpea, copy_ = _decided(db, monkeypatch, bypass_application=True)
    assert sets["primary"][mpea] == "in_scope"  # the bypass let the survivor in
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(db, rid)
    assert refused.value.code == "invariant_broken" and "conflict" in refused.value.message
