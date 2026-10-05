"""Confirmation (ChatGPT, 2026-10-06), finding 2 and the freeze check: a mixed group keeps its
definite pairwise relationships, through the real pipeline and at the freeze.

The reviewer's case: A (MPEA) and B (the extract) cite the same DOI with identical conditions and
values; C (Texas A&M, a third source) matches both but has no paper identity. Another grain size
is present. The plan chooses to count possible duplicates both (a permitted choice)."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, eligibility, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.pipeline.writes import Refused

DOI = "10.1016/j.test.2026.001"


@pytest.fixture
def run(db):
    pw.registered_files(db, {
        "mpea": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0, doi=DOI), pw.mpea_row("Co50Ni50", 40.0, 250.0, doi=DOI)]),
        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0, doi=DOI)]),
        "tamu_fcc": pw.tamu_xlsx([{"Iteration": "CBA", "Alloy Name": "Co50Ni50", "Co": 50.0, "Ni": 50.0,
                                   "YS (MPa)": 300.0, "Grain Size(µm)": 10.0}])})
    content = reference_plan(0)
    for e in content["eligibility_rules"]:
        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
            e["rule"] = "in_scope"  # the plan's choice: possible duplicates both counted
    rid = pw.dispatched_run(db, sources=("mpea", "controlled_duplicates", "tamu_fcc"), marked=True)
    content["hypothesis_version"] = pw.version_of(db, rid)
    checkpoints.lock_rules(db, rid, content)
    extract.store_records(db, rid)
    checks.run_checks(db, rid)
    return rid


def _origins(db, rid, rule=None):
    with db.connect() as conn:
        return {f"{s}:{k}": r for s, k, r in conn.execute(text(
            "SELECT s.key, rec.source_item_key, rr.rule FROM run_record rr JOIN record rec ON rec.id = rr.record_id "
            "JOIN source_version sv ON sv.id = rec.source_version_id JOIN source s ON s.id = sv.source_id "
            "WHERE rr.run_id = :r"), dict(r=rid))}


def test_the_pipeline_never_admits_the_exact_duplicate_twice(db, run):
    inclusion.decide_run(db, run)
    rules = _origins(db, run)
    a, b = rules["mpea:MPEA_dataset.csv:row:0"], rules["controlled_duplicates:extract.csv:row:0"]
    assert sorted([a, b]) == ["duplicate_counted_once", "in_scope"]
    assert rules["tamu_fcc:Grain_Size_Summary_v3.xlsx:row:0"] == "in_scope"
    assert checkpoints.freeze_dataset(db, run)["frozen"] is True


def test_the_freeze_check_catches_the_exact_pair_with_eligibility_bypassed(db, run, monkeypatch):
    """The eligibility safeguards bypassed (an exact pair treated as 'counted separately'): the
    freeze check, using Checks' retained pairwise result, still refuses."""
    original = eligibility.flag_rule
    monkeypatch.setattr(eligibility, "flag_rule",
                        lambda f, st: "in_scope" if f["kind"] == "exact_duplicate" else original(f, st))
    inclusion.decide_run(db, run)
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(db, run)
    assert refused.value.code == "invariant_broken" and "exact duplicate" in refused.value.message
