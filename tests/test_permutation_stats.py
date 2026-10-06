"""Step 7: results are a pure function of the frozen set and the locked plan (owner, 2026-10-05).

The same data, stored three times with record ids and insertion order permuted (each source's
records shuffled, the sources stored in a shuffled order, unrelated records of another run inserted
first so every id shifts), give identical analysis results, calibration results (seeds included),
stored decision, record of statistical significance and gap facts.
"""
from __future__ import annotations

import random

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources import adapters
from hypocurate.sources.record import AdapterResult

RESULT_COLUMNS = ("scope", "n_records", "n_alloys", "n_groups", "resid_df", "check1_passed", "check2_passed",
                  "minimums_met", "estimate", "std_error", "p_value", "estimated_power", "label", "withheld",
                  "n_records_not_used", "test_run_label")
CALIBRATION_COLUMNS = ("method", "status", "reason", "assumptions", "n_simulations", "seed", "null_share",
                       "null_ci_low", "null_ci_high", "effect_share", "effect_ci_low", "effect_ci_high",
                       "confidence_flag", "test_run_label")


def _permuted_analysis(db, vid, sources, seed, monkeypatch, marked):
    rnd = random.Random(seed)
    real_read = adapters.read

    def shuffled(version):
        result = real_read(version)
        records = list(result.records)
        rnd.shuffle(records)
        return AdapterResult(tuple(records), result.blank_rows)

    with monkeypatch.context() as m:
        m.setattr(extract.adapters, "read", shuffled)
        for _ in range(seed):
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
    out = analysis.run_statistics(db, rid)
    with db.connect() as conn:
        keyed = {r.id: (r.key, r.source) for r in conn.execute(text(
            "SELECT ar.id, a.key, s.key AS source FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r"), dict(r=rid))}
        rows = {keyed[r.id]: tuple(getattr(r, c) for c in RESULT_COLUMNS) for r in conn.execute(text(
            "SELECT * FROM analysis_result WHERE run_id = :r"), dict(r=rid))}
        cal = {(keyed[r.analysis_result_id], r.method): tuple(getattr(r, c) for c in CALIBRATION_COLUMNS)
               for r in conn.execute(text("SELECT * FROM calibration_result WHERE run_id = :r"), dict(r=rid))}
        facts = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'"),
                             dict(r=rid)).scalar_one()
    return out, rows, cal, facts


@pytest.mark.parametrize("sources, marked", [(("mpea", "tamu_fcc"), False), (("mpea", "controlled_duplicates"), True)],
                         ids=["reference_data", "controlled_extract"])
def test_permuted_ids_and_insertion_order_give_identical_results(db, monkeypatch, sources, marked):
    pw.registered(db, ("mpea", "tamu_fcc", "controlled_duplicates"))
    vid = pw.version_of(db, pw.dispatched_run(db, sources=("tamu_fcc",)))
    results = [_permuted_analysis(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
    first = results[0]
    assert first[0]["analyses"][0]["estimate"] is not None and len(first[2]) == 2 * len(first[1])
    for other in results[1:]:
        assert other[0] == first[0]  # the record of statistical significance and the decision, seeds included
        assert other[1] == first[1]  # every analysis result
        assert other[2] == first[2]  # every calibration result
        assert other[3] == first[3]  # the gap facts
