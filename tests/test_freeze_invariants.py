"""Re-check, the owner's addition (2026-10-06): the freeze verifies the primary set itself against
every item of register entry 'primary_set_invariants', using the Checks flags (identity and
validity computed independently of the plan's grouping and outcome settings) and the records'
kind and source:
- no two members form an exact duplicate pair;
- no member is connected to a definite conflict (third confirmation, owner 2026-10-06: none, not
  "at most one");
- no member carries an invalid-value flag;
- no member belongs to an unresolved-identity group;
- no member is model-recalled;
- no member comes from a constructed source in a run not marked as a test;
- no member lacks a group under the primary grouping (step 7b, owner 2026-10-06).
A freeze that fails any of them is refused and logged.

Each end-to-end case uses a plan deliberately built to slip past settings validation: the
guards are switched off for the test (a simulated gap), so only the check on the result can
stop it. That includes the reviewer's two cases (grouping by dataset; another outcome)."""
from __future__ import annotations

import copy

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, eligibility, extract, inclusion, plan as plan_module, writes
from hypocurate.pipeline.plan import reference_plan
from hypocurate.pipeline.writes import Refused


# --- the check itself, item by item ---------------------------------------------------------------

def rec(i, source="mpea", kind="measured", paper="p"):
    return {"id": i, "source": source, "kind": kind, "paper": paper, "batch": None}


GROUPING = {"mpea": "paper", "tamu_fcc": "dataset", "controlled_duplicates": "paper"}


def problems(members, flags=(), records=None, marked=False):
    records = records or {i: rec(i) for i in members}
    return eligibility.primary_set_problems(set(members), records, list(flags), marked, grouping=GROUPING)


def flag(kind, category, *ids):
    return {"id": 1, "kind": kind, "category": category, "records": list(ids)}


@pytest.mark.parametrize("case, members, flags, records, marked, expected", [
    ("exact duplicate counted twice", {1, 2}, [flag("exact_duplicate", "identical values", 1, 2)], None, False,
     "exact duplicate"),
    ("both records of a conflict", {1, 2}, [flag("values_disagree", "differ beyond tolerance", 1, 2)], None, False,
     "conflict"),
    ("an invalid value", {1}, [flag("invalid_value", "physically impossible", 1)], None, False, "invalid value"),
    ("an unresolved-identity group", {1}, [flag("possible_duplicate", "several candidates", 1, 2, 3)], None, False,
     "unresolved identity"),
    ("a model-recalled record", {1}, [], {1: rec(1, kind="model_recalled")}, False, "model-recalled"),
    ("a constructed record in an unmarked run", {1}, [], {1: rec(1, source="controlled_duplicates")}, False,
     "constructed"),
    ("a record without a group", {1}, [], {1: rec(1, paper=None)}, False, "without a group"),
])
def test_each_invariant_is_checked_on_the_primary_set(case, members, flags, records, marked, expected):
    got = problems(members, flags, records, marked)
    assert len(got) == 1 and expected in got[0], (case, got)


def test_what_the_invariants_allow():
    """One survivor of a duplicate; one record of a conflict counted by the survivor rule is not in
    primary by default, but a plan may choose it; possible duplicates; a constructed record in a
    marked run."""
    assert problems({1, 3}, [flag("exact_duplicate", "identical values", 1, 2)]) == []
    # Third confirmation (owner, 2026-10-06): no record of a conflict-connected group, not even one.
    assert problems({1}, [flag("values_disagree", "differ beyond tolerance", 1, 2)]) != []
    assert problems({1, 2}, [flag("possible_duplicate", "identical values", 1, 2)]) == []
    assert problems({1}, [], {1: rec(1, source="controlled_duplicates")}, marked=True) == []


# --- end to end: plans that slip past settings validation ------------------------------------------

@pytest.fixture
def no_guard(monkeypatch):
    """Switches off the settings guards (validation and application time), as a gap would."""
    monkeypatch.setattr(eligibility, "fixed_rule_problems", lambda rules: [])
    monkeypatch.setattr(plan_module, "fixed_rule_problems", lambda rules: [])
    monkeypatch.setattr(plan_module, "SUPPORTED_OUTCOMES", ("yield_strength", "ultimate_tensile_strength"))


def _rule(content, kind, category, rule):
    for e in content["eligibility_rules"]:
        if e["flag_kind"] == kind and e.get("category") == category:
            e["rule"] = rule
    return content


def _through_decisions(db, sources, content, marked=True):
    rid = pw.dispatched_run(db, sources=sources, marked=marked)
    content["hypothesis_version"] = pw.version_of(db, rid)
    checkpoints.lock_rules(db, rid, content)
    extract.store_records(db, rid)
    checks.run_checks(db, rid)
    inclusion.decide_run(db, rid)
    return rid


def _refused(db, rid, expected):
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(db, rid)
    assert refused.value.code == "invariant_broken" and expected in refused.value.message
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar() == 0
        row = conn.execute(text("SELECT role, function, detail FROM audit_log WHERE run_id = :r "
                                "AND detail->>'result' = 'rejected' ORDER BY id DESC LIMIT 1"), dict(r=rid)).one()
    assert (row.role, row.function, row.detail["code"]) == ("checkpoint", "freeze_dataset", "invariant_broken")


def _extract_run(db):
    pw.registered(db, ("mpea", "controlled_duplicates"))
    return reference_plan(0)


def test_an_exact_duplicate_counted_twice_is_refused_at_the_freeze(db, no_guard):
    content = _rule(_extract_run(db), "exact_duplicate", None, "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "exact duplicate")


def test_a_conflict_admitted_past_every_guard_is_refused_at_the_freeze(db, no_guard, monkeypatch):
    """Third confirmation (owner, 2026-10-06): conflicts are no longer a plan rule, so the
    application's own rule is bypassed as well (a survivor allowed in primary); the one conflict
    record that then enters is refused at the freeze."""
    monkeypatch.setattr(eligibility, "conflict_survivor_allowed", lambda key: True)
    content = _rule(_extract_run(db), "values_disagree", None, "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "conflict")


def test_the_reviewers_grouping_case_is_refused_at_the_freeze(db, no_guard):
    """MPEA grouped by dataset, the extract by paper, and the plan admitting exact duplicates: the
    duplicates are still known (Checks' paper identity ignores grouping) and the freeze refuses."""
    content = _extract_run(db)
    content["rules"]["grouping"] = [{"source": "mpea", "unit": "dataset"}, {"source": "tamu_fcc", "unit": "dataset"},
                                    {"source": "controlled_duplicates", "unit": "paper"}]
    _rule(content, "exact_duplicate", None, "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "exact duplicate")


def _invalid_sources(db):
    pw.registered_files(db, {
        "mpea": pw.mpea_csv([{**pw.mpea_row("Co50Ni50", 10.0, 400.0), "PROPERTY: UTS (MPa)": "399"},
                             pw.mpea_row("Co50Ni50", 40.0, 300.0)]),
        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co60Ni40", 10.0, 300.0, doi="10.5555/other")])})


def test_an_invalid_value_is_refused_at_the_freeze(db, no_guard):
    _invalid_sources(db)
    content = _rule(reference_plan(0), "invalid_value", None, "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "invalid value")


def test_the_reviewers_outcome_case_is_refused_at_the_freeze(db, no_guard):
    """Tensile strength as the outcome and invalid values admitted: Checks still flags tensile
    strength 399 below yield strength 400 (independent of the outcome) and the freeze refuses."""
    _invalid_sources(db)
    content = _rule(reference_plan(0), "invalid_value", None, "in_scope")
    content["variables"]["outcome"] = {"field": "ultimate_tensile_strength", "unit": "MPa"}
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "invalid value")


def test_an_unresolved_identity_group_is_refused_at_the_freeze(db, no_guard):
    """One MPEA record with two candidates in the extract: an ambiguous group admitted by the plan."""
    pw.registered_files(db, {
        "mpea": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0), pw.mpea_row("Co50Ni50", 40.0, 250.0)]),
        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0),
                                              pw.mpea_row("Co50Ni50", 10.1, 300.0)])})
    content = _rule(reference_plan(0), "possible_duplicate", "several candidates", "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "unresolved identity")


def test_a_constructed_record_in_an_unmarked_run_is_refused_at_the_freeze(db, monkeypatch):
    """The storage, inclusion and freeze guards switched off: the check on the result still finds
    the constructed records in a run not marked as a test."""
    for module in (extract, inclusion, checkpoints):
        monkeypatch.setattr(module, "constructed_unmarked", lambda conn, run_id, keys: False)
    rid = _through_decisions(db, ("mpea", "controlled_duplicates"), _extract_run(db), marked=False)
    _refused(db, rid, "constructed")


def test_a_record_without_a_group_admitted_past_the_rule_is_refused_at_the_freeze(db, monkeypatch):
    """Step 7b (owner, 2026-10-06): invariant (7). The eligibility rule `group_unknown` switched off,
    and the plan counting possible duplicates both (a choice the plan may make): the extract
    records of answer rows 5-6, which have no DOI and so no group, would enter primary. The check on
    the result finds them, from the primary grouping, and the freeze refuses."""
    monkeypatch.setattr(eligibility, "has_group", lambda rec, st: True)
    content = _rule(_extract_run(db), "possible_duplicate", None, "in_scope")
    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "without a group")


def test_a_texas_am_record_is_not_without_a_group():
    """Grouped by dataset, a Texas A&M record has its group without a DOI; the check reads the plan's
    grouping, not the DOI."""
    assert problems({1}, [], {1: rec(1, source="tamu_fcc", paper=None)}) == []


def test_a_valid_plan_freezes(db):
    """The reference plan on MPEA and the extract (marked) passes the check."""
    content = _extract_run(db)
    rid = _through_decisions(db, ("mpea", "controlled_duplicates"), content)
    assert checkpoints.freeze_dataset(db, rid)["frozen"] is True
