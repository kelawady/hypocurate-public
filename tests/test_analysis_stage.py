"""Step 7: the analysis stage through the database: what is stored in each result state, what is
withheld, the test-run label, the refusals, and the rules the database itself enforces on results
(migration 0004).

Result states (owner, 2026-10-05): sufficient with a verdict (6); exploratory (5); coefficient only
(4); below the minimums under the fixed option (3, withheld run-wide: counts and records only);
coefficient cannot be fitted (2, pure tests only: eligibility rule 8 leaves the primary set no
alloy with fewer than two grain sizes); no dataset frozen (1).
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, completion, results
from hypocurate.pipeline.writes import TEST_RUN_LABEL, Refused
from pipeline_fixtures import frozen_run
from stats_world import audit_codes, rows_of, run_on, small_rows, val

LABEL = "test run: includes constructed data"


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


@pytest.fixture(scope="module")
def reference(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        yield engine, rid, analysis.run_statistics(engine, rid)


def result_rows(engine, rid):
    return rows_of(engine, "SELECT ar.*, a.key AS set_key, s.key AS source_key FROM analysis_result ar "
                           "JOIN analysis_set a ON a.id = ar.analysis_set_id LEFT JOIN source s ON s.id = ar.source_id "
                           "WHERE ar.run_id = :r ORDER BY ar.id", r=rid)


def calibration_rows(engine, rid):
    return rows_of(engine, "SELECT * FROM calibration_result WHERE run_id = :r ORDER BY id", r=rid)


# --- sufficient with a verdict (the reference run) ------------------------------------------------

def test_every_analysis_is_stored_with_both_calibrations(reference):
    engine, rid, out = reference
    rows = result_rows(engine, rid)
    assert [(r.scope, r.set_key, r.source_key) for r in rows] == [
        ("pooled", "primary", None), ("per_source", "primary", "mpea"), ("per_source", "primary", "tamu_fcc")] + [
        ("sensitivity", k, None) for k in ("no_exclusions", "tension_and_compression", "six_batches_as_groups",
                                           "same_alloy_1_at_pct", "source_only_assignments",
                                           "scope_not_confirmed_included", "possible_duplicates_separate",
                                           "conflicts_survivor_value")]
    assert all(r.withheld is False and r.test_run_label is None and r.n_records_not_used == 0 for r in rows)
    cal = calibration_rows(engine, rid)
    assert len(cal) == 2 * len(rows)
    assert {(c.analysis_result_id, c.method) for c in cal} == {(r.id, m) for r in rows for m in ("fixed", "estimated")}
    pooled = rows[0]
    assert (pooled.n_records, pooled.n_alloys, pooled.n_groups, pooled.resid_df, pooled.minimums_met) == (
        97, 22, 20, 74, True)
    assert pooled.label is None and pooled.estimated_power is not None
    tamu = rows[2]
    assert (tamu.check1_passed, tamu.check2_passed, tamu.std_error, tamu.p_value, tamu.label) == (
        True, False, None, None, "not_enough_data")
    assert [(c.status, c.reason) for c in cal if c.analysis_result_id == tamu.id] == [
        ("unavailable", "insufficient_groups")] * 2
    assert rows[1].label == "agrees"


def test_the_record_of_statistical_significance_and_the_decision(reference):
    """PRD 5.9: estimate and uncertainty, test, p-value and threshold, counts, the two checks, df
    and groups, the sufficiency option and whether it was met, estimated power, per-source and
    sensitivity results."""
    engine, rid, out = reference
    stored = analysis.stored_record(engine, rid)
    assert stored == out
    assert stored["decision"] == {
        "freeze_fingerprint": val(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid),
        "state": "sufficient", "outcome": "sufficient", "outcome_wording": "sufficient in the sources searched",
        "verdict": "supported", "verdict_wording": "supported under the stated model, in the sources searched",
        "exploratory": False, "evidence_level": 6, "evidence_level_wording": "sufficient with a verdict",
        "label": None}
    pooled = stored["analyses"][0]
    for key in ("estimate", "std_error", "t", "df", "p_value", "alpha", "counts", "checks", "minimums",
                "minimums_met", "estimated_power", "power_label", "calibration"):
        assert pooled[key] is not None, key
    assert pooled["df"] == 19 and stored["sufficiency_option"] == "fixed_minimum" and stored["test_run_label"] is None


def test_the_run_is_not_completed_by_the_analysis_stage(reference):
    engine, rid, _ = reference
    assert rows_of(engine, "SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("running", None, None, None)]


def test_a_second_analysis_is_refused_and_logged(reference):
    engine, rid, _ = reference
    with pytest.raises(Refused) as refused:
        analysis.run_statistics(engine, rid)
    assert refused.value.code == "already_done"
    assert "already_done" in audit_codes(engine, rid, "run_statistics")


def test_no_analysis_before_the_freeze(engine):
    pw.registered(engine, ("mpea",))
    rid = pw.locked_run(engine, sources=("mpea",))
    with pytest.raises(Refused) as refused:
        analysis.run_statistics(engine, rid)
    assert refused.value.code == "stage_mismatch"
    assert audit_codes(engine, rid, "run_statistics") == ["stage_mismatch"]
    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0


# --- below the minimums under the fixed option: withheld run-wide --------------------------------

def test_below_the_minimums_every_analysis_holds_counts_and_records_only(engine):
    """Decision 1: 3 alloys at two grain sizes, 3 papers: inference is valid, but 6 records < 30."""
    rid = run_on(engine, small_rows(3, papers=3))
    out = analysis.run_statistics(engine, rid)
    assert out["withheld"] and out["decision"]["state"] == "below_minimums"
    assert out["decision"]["evidence_level"] == 3 and out["decision"]["label"] == "data found; not enough to test"
    assert out["decision"]["verdict"] is None and out["decision"]["outcome"] == "insufficient"
    for e in out["analyses"]:
        assert e["withheld"] and (e["estimate"], e["std_error"], e["t"], e["p_value"], e["significant"]) == (
            None, None, None, None, None)
        assert e["label_text"] == "data found; not enough to test"
        assert set(e["minimums"]) == {"records", "alloys", "groups", "resid_df"}
        assert len(e["records_found"]) == e["counts"]["n_records_in_set"]
        assert all(v["status"] == "unavailable" for v in e["calibration"].values())
    pooled = out["analyses"][0]
    assert pooled["minimums"]["records"] == {"count": 6, "minimum": 30, "met": False}
    assert pooled["checks"]["inference_valid"] and pooled["estimated_power"] is not None  # no outcome used
    for r in result_rows(engine, rid):
        assert r.withheld and r.estimate is None and r.std_error is None and r.p_value is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "below_minimums")}
    # Nothing computed from outcomes anywhere in what is stored: the real outcomes can be anything.
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]


def test_withheld_results_do_not_depend_on_the_outcome_values():
    """Below the minimums nothing computed from outcomes is kept: replacing every outcome value
    changes nothing in what would be stored (the power and counts come from structure only)."""
    import generator as g
    data = g.frozen_data(g.SPECS["small_but_valid"])
    plan = g.plan("fixed_minimum", n_simulations=300)
    first = analysis.analyse(plan, data)
    for value in (-5000.0, 0.0, 12345.6):
        other = {**data, "records": [{**r, "outcome": value + i} for i, r in enumerate(data["records"])]}
        assert analysis.analyse(plan, other) == first
    assert first["withheld"]


def test_use_what_is_available_gives_an_exploratory_verdict_on_the_same_data(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    out = analysis.run_statistics(engine, rid)
    assert (out["decision"]["state"], out["decision"]["evidence_level"], out["decision"]["exploratory"]) == (
        "exploratory", 5, True)
    assert out["decision"]["verdict"] in ("supported", "not_supported") and out["decision"]["label"] == "exploratory"
    pooled = result_rows(engine, rid)[0]
    assert not pooled.withheld and not pooled.minimums_met and pooled.p_value is not None
    assert {c.method: c.status for c in calibration_rows(engine, rid)}["fixed"] == "computed"
    completion.copy_decision(engine, rid)
    assert rows_of(engine, "SELECT outcome, exploratory, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("sufficient", True, 5)]


def test_use_what_is_available_with_one_group_gives_the_coefficient_only(engine):
    rid = run_on(engine, small_rows(3, papers=1), option="use_available")
    out = analysis.run_statistics(engine, rid)
    pooled = out["analyses"][0]
    assert (out["decision"]["state"], out["decision"]["evidence_level"]) == ("coefficient_only", 4)
    assert pooled["estimate"] is not None and pooled["std_error"] is None and pooled["p_value"] is None
    assert out["decision"]["verdict"] is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}


def test_the_fixed_option_with_one_group_withholds_even_the_coefficient(engine):
    """Decision 1: below the minimums, the coefficient-only rule does not apply."""
    rid = run_on(engine, small_rows(3, papers=1))
    out = analysis.run_statistics(engine, rid)
    assert out["decision"]["evidence_level"] == 3 and out["analyses"][0]["estimate"] is None
    assert {(c.status, c.reason) for c in calibration_rows(engine, rid)} == {("unavailable", "insufficient_groups")}


# --- no dataset frozen ------------------------------------------------------------------------------

def test_a_run_with_no_dataset_frozen_gets_level_one_and_its_gap_facts(engine):
    """Every record out of scope (compression) or without a grain size: no dataset frozen."""
    rows = [pw.mpea_row("CoCrFeNi", 1.0, 400.0, test="C"), pw.mpea_row("CoCrFeNi", 9.0, 300.0, test="C"),
            {**pw.mpea_row("CoCrNi", 1.0, 500.0), "PROPERTY: grain size ($\\mu$m)": ""}]
    rid = run_on(engine, rows)
    out = analysis.run_statistics(engine, rid)
    assert out["decision"] == {**out["decision"], "state": "no_dataset_frozen", "evidence_level": 1,
                               "outcome": "insufficient", "verdict": None, "freeze_fingerprint": None}
    assert out["analyses"] == []
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert facts["records_lacking_fields"]["mpea"]["grain_size"] == 1
    assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]
    assert facts["minimums"]["records"] == {"count": 0, "minimum": 30, "met": False}
    assert facts["eligibility_rules"] == {"missing_value": 1, "out_of_scope": 2}
    assert facts["sources"] == [{"source": "mpea", "search_status": "searched", "nothing_found": None}]
    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
    completion.copy_decision(engine, rid)
    assert rows_of(engine, "SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("completed", "insufficient", None, 1)]


def test_the_gap_facts_hold_no_text_and_no_outcome_value(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    analysis.run_statistics(engine, rid)
    facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
    assert set(facts) == {"minimums", "minimums_missed", "records_lacking_fields", "eligibility_rules", "sources",
                          "test_run_label"}
    yields = {r[0] for r in rows_of(engine, "SELECT (harmonized->'yield_strength'->>'value') FROM record "
                                            "WHERE extraction_run_id = :r", r=rid)}
    flat = repr(facts)
    assert not any(y in flat for y in yields)


# --- marked test runs ---------------------------------------------------------------------------------

def test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates(engine):
    pw.registered(engine, ("mpea", "tamu_fcc", "controlled_duplicates"))
    marked = pw.through_freeze(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    real = pw.through_freeze(engine, sources=("mpea", "tamu_fcc"))
    out = analysis.run_statistics(engine, marked)
    analysis.run_statistics(engine, real)
    assert TEST_RUN_LABEL == LABEL
    assert out["test_run_label"] == LABEL and out["decision"]["evidence_level"] == 6  # keeps its level
    # The extract's two records without a paper enter only 'possible_duplicates_separate': that descriptive
    # analysis is not analysed (no group invented), and nothing is stored for it; the others are.
    assert out["not_analysed"] == [{"analysis": "sensitivity:possible_duplicates_separate", "scope": "sensitivity",
                                    "set": "possible_duplicates_separate", "source": None,
                                    "reason": "records_without_group", "n_records_without_group": 2,
                                    "n_records_in_set": out["not_analysed"][0]["n_records_in_set"]}]
    assert "possible_duplicates_separate" not in {r.set_key for r in result_rows(engine, marked)}
    assert {r.test_run_label for r in result_rows(engine, marked)} == {LABEL}
    assert {c.test_run_label for c in calibration_rows(engine, marked)} == {LABEL}
    assert rows_of(engine, "SELECT output->>'test_run_label' FROM stage_result WHERE run_id = :r "
                           "AND stage IN ('statistics', 'gap_facts')", r=marked) == [(LABEL,), (LABEL,)]
    assert {r.test_run_label for r in result_rows(engine, real)} == {None}
    for rid in (marked, real):
        completion.copy_decision(engine, rid)
    with engine.connect() as conn:
        assert [r.id for r in results.real_runs(conn)] == [real]
        assert results.real_outcome_counts(conn) == {"sufficient": 1}
        assert {r.run_id for r in results.real_analysis_results(conn)} == {real}
    assert val(engine, "SELECT evidence_level FROM run WHERE id = :r", r=marked) == 6


def test_a_marked_run_with_no_dataset_frozen_is_labelled_too(engine):
    rows = [pw.mpea_row("CoCrFeNi", 1.0, 400.0, test="C")]
    rid = run_on(engine, rows, marked=True)
    assert rows_of(engine, "SELECT test_run_label FROM calibration_result WHERE run_id = :r", r=rid) == [(LABEL,)]
    assert analysis.run_statistics(engine, rid)["test_run_label"] == LABEL


# --- what the database refuses (migration 0004) -------------------------------------------------------

def _insert_result(engine, rid, **over):
    """A result row; one with a p-value gets, by default, what must be stored with it (merge decision):
    the description, t df = informative papers - 1, the effective number and the largest share."""
    sets = dict(rows_of(engine, "SELECT key, id FROM analysis_set WHERE run_id = :r", r=rid))
    n = val(engine, "SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sets["primary"])
    cols = dict(run_id=rid, scope="pooled", analysis_set_id=sets["primary"], n_records=n, n_alloys=3, n_groups=3,
                n_groups_informative=3, effective_papers=3.0, resid_df=n - 4, check1_passed=True, check2_passed=True,
                minimums_met=False,
                estimate=None, std_error=None, p_value=None)
    if over.get("p_value") is not None:
        informative = over.get("n_groups_informative", cols["n_groups_informative"])
        cols.update(t_df=informative - 1, largest_paper_share=0.5,
                    p_value_description="approximate, nominal, one-sided cluster-robust p-value under the locked method")
    cols.update(over)
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO analysis_result ({', '.join(cols)}) VALUES "
                          f"({', '.join(':' + c for c in cols)})"), cols)


def test_the_database_computes_withheld_and_refuses_a_number_in_a_withheld_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # fixed option, 6 records: the pooled result is withheld
    with pytest.raises(IntegrityError, match="withheld must equal"):
        _insert_result(engine, rid, withheld=False)
    with pytest.raises(IntegrityError, match="ck_analysis_result_estimate_iff_check1"):
        _insert_result(engine, rid, estimate=300.0)
    with pytest.raises(IntegrityError, match="ck_analysis_result_std_error_iff_check2"):
        _insert_result(engine, rid, std_error=10.0)
    _insert_result(engine, rid)  # withheld filled in by the database
    assert val(engine, "SELECT withheld FROM analysis_result WHERE run_id = :r", r=rid) is True


def test_the_database_refuses_a_per_source_result_before_the_pooled_one(engine):
    rid = run_on(engine, small_rows(3, papers=3))
    src = val(engine, "SELECT id FROM source WHERE key = 'mpea'")
    with pytest.raises(IntegrityError, match="pooled result is written before"):
        _insert_result(engine, rid, scope="per_source", source_id=src)


def test_the_database_refuses_a_label_on_a_pooled_result_and_power_without_inference(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_label_per_source_only"):
        _insert_result(engine, rid, label="agrees", estimate=1.0, std_error=1.0, p_value=0.1)
    with pytest.raises(IntegrityError, match="ck_analysis_result_power_needs_check2"):
        _insert_result(engine, rid, n_groups=1, n_groups_informative=1, check2_passed=False, estimate=1.0,
                       estimated_power=0.5)
    with pytest.raises(IntegrityError, match="test-run label exactly when"):
        _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, test_run_label=LABEL)


def test_the_database_refuses_records_not_accounted_for(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="n_records must equal"):
        _insert_result(engine, rid, n_records=5, resid_df=1, estimate=1.0, std_error=1.0, p_value=0.1)
    _insert_result(engine, rid, n_records=4, n_records_not_used=2, n_alloys=2, n_groups=2, n_groups_informative=2,
                   resid_df=1, estimate=1.0, std_error=1.0, p_value=0.1)


def test_the_database_refuses_calibration_that_does_not_match_the_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # withheld
    analysis.run_statistics(engine, rid)
    pooled = val(engine, "SELECT id FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
    numbers = ("'{\"scatter\": 60}', 2000, 7, 0.05, 0.04, 0.06, 1.0, 0.99, 1.0, 'none'")
    insert = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, "
              "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, "
              "confidence_flag) VALUES (:r, :a, :m, :st, :re, {n})")
    none = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"
    for method, status, reason, nums, match in (
            ("fixed", "computed", None, numbers, "computed exactly when"),
            ("fixed", "unavailable", "insufficient_groups", none, "must match the validity checks"),
            (None, "unavailable", "below_minimums", none, "ck_calibration_result_method_iff_analysis")):
        with pytest.raises(IntegrityError, match=match):
            with engine.begin() as conn:
                conn.execute(text(insert.format(n=nums)), dict(r=rid, a=pooled, m=method, st=status, re=reason))
    with pytest.raises(IntegrityError, match="uq_calibration_result_scope"):
        with engine.begin() as conn:
            conn.execute(text(insert.format(n=none)), dict(r=rid, a=pooled, m="fixed", st="unavailable",
                                                          re="below_minimums"))


def test_the_database_requires_the_fixed_method_where_inference_is_valid(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1)
    pooled = val(engine, "SELECT id FROM analysis_result WHERE run_id = :r", r=rid)
    insert = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason) "
              "VALUES (:r, :a, :m, 'unavailable', :re)")
    with pytest.raises(IntegrityError, match="computed exactly when"):
        with engine.begin() as conn:
            conn.execute(text(insert), dict(r=rid, a=pooled, m="fixed", re="shift_not_estimable"))
    with engine.begin() as conn:  # the estimated method may name why the noise cannot be estimated
        conn.execute(text(insert), dict(r=rid, a=pooled, m="estimated", re="shift_not_estimable"))


@pytest.mark.parametrize("outcome, verdict, exploratory, level, ok", [
    ("insufficient", None, False, 1, True), ("insufficient", None, False, 4, True),
    ("partly_sufficient", None, False, 3, True), ("insufficient", None, False, 6, False),
    ("insufficient", None, False, 5, False), ("insufficient", None, False, 7, False),
    ("insufficient", None, False, 0, False),
])
def test_the_evidence_level_must_agree_with_the_outcome(engine, outcome, verdict, exploratory, level, ok):
    pw.registered(engine, ("mpea",))
    rid = pw.dispatched_run(engine, sources=("mpea",))
    update = ("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
              "exploratory = :x, evidence_level = :e WHERE id = :r")
    params = dict(o=outcome, v=verdict, x=exploratory, e=level, r=rid)
    if ok:
        with engine.begin() as conn:
            conn.execute(text(update), params)
    else:
        with pytest.raises(IntegrityError, match="ck_run_evidence_level"):
            with engine.begin() as conn:
                conn.execute(text(update), params)


# --- review fixes (ChatGPT, 2026-10-06) ---------------------------------------------------------------

def test_two_alloys_with_one_display_label_are_stored(engine):
    """Finding 2: Fe50.01Ni49.99 and Fe50.04Ni49.96 both display as Fe50Ni50. Under a plan rounding
    compositions to 0.01 at.% they are two alloys, each at three grain sizes; the result must be stored
    (the trigger no longer bounds the alloy count by the display label)."""
    rows = [pw.mpea_row(formula, d, ys, doi=f"10.1016/j.test.2026.{p:03d}")
            for formula, base in (("Fe50.01Ni49.99", 200.0), ("Fe50.04Ni49.96", 260.0))
            for p, (d, ys) in enumerate(((1.0, base + 300), (4.0, base + 150), (16.0, base + 75)), start=1)]
    rid = run_on(engine, rows, option="use_available", rules={"same_alloy_decimals": 2})
    assert {r[0] for r in rows_of(engine, "SELECT alloy FROM record WHERE extraction_run_id = :r", r=rid)} == {"Fe50Ni50"}
    out = analysis.run_statistics(engine, rid)
    assert out["analyses"][0]["counts"]["n_alloys"] == 2
    assert result_rows(engine, rid)[0].n_alloys == 2


def test_an_unexpected_error_in_the_statistics_is_a_logged_refusal(engine, monkeypatch):
    """Finding 3: no exception may bypass the stage's error handling."""
    from hypocurate.pipeline import statistics as st
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")

    def broken(d):
        raise ZeroDivisionError("float division by zero")

    monkeypatch.setattr(st, "fit", broken)
    with pytest.raises(Refused) as refused:
        analysis.run_statistics(engine, rid)
    assert refused.value.code == "statistics_failed"
    assert audit_codes(engine, rid, "run_statistics") == ["statistics_failed"]
    assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0


def test_the_reviewers_design_through_the_database(engine):
    """Finding 1 end to end: eleven papers, one informative; use what is available gives the
    coefficient only and the database stores the informative count and the reason."""
    rows = []
    # The reviewer's structure with grain sizes written exactly in the file: x = d^-1/2 = 0.2, 0.8 and
    # four times 0.5, the alloy average (16/9 µm cannot be written exactly in a CSV cell).
    sizes, ys = (25.0, 1.5625, 4.0, 4.0, 4.0, 4.0), (400.0, 600.0, 470.0, 510.0, 500.0, 490.0)
    n = 0
    from stats_world import FORMULAS
    for a in range(5):
        for j in range(6):
            paper = 0 if j < 2 else 1 + n % 10
            n += j >= 2
            rows.append(pw.mpea_row(FORMULAS[a], sizes[j], ys[j] + 100 * a,
                                    doi=f"10.1016/j.test.2026.{paper:03d}"))
    rid = run_on(engine, rows, option="use_available")
    out = analysis.run_statistics(engine, rid)
    assert out["decision"]["verdict"] is None and out["decision"]["evidence_level"] == 4
    r = result_rows(engine, rid)[0]
    assert (r.n_groups, r.n_groups_informative, r.check2_passed, r.inference_reason) == (11, 1, False,
                                                                                         "insufficient_groups")
    assert r.estimate is not None and r.std_error is None and r.p_value is None


def test_the_database_counts_informative_groups_for_check_2_and_the_minimum(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_check2_consistent"):
        _insert_result(engine, rid, n_groups=3, n_groups_informative=1, estimate=1.0, std_error=1.0, p_value=0.1)
    _insert_result(engine, rid, n_groups=3, n_groups_informative=1, check2_passed=False, estimate=1.0)
    assert rows_of(engine, "SELECT inference_reason FROM analysis_result WHERE run_id = :r", r=rid) == [
        ("insufficient_groups",)]


def test_the_database_takes_an_uncertainty_that_cannot_be_estimated(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_inference_reason"):
        _insert_result(engine, rid, check2_passed=False, estimate=1.0, inference_reason="insufficient_groups")
    _insert_result(engine, rid, check2_passed=False, estimate=1.0, inference_reason="uncertainty_not_estimable")


def test_the_estimated_detection_rate_is_never_stored_for_a_withheld_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # fixed option: withheld
    with pytest.raises(IntegrityError, match="ck_analysis_result_power_estimated_noise"):
        _insert_result(engine, rid, estimated_power=0.5, estimated_power_estimated_noise=0.4)
    _insert_result(engine, rid, estimated_power=0.5)


def test_a_label_reason_is_stored_exactly_with_not_enough_data(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    analysis.run_statistics(engine, rid)
    per_source = [r for r in result_rows(engine, rid) if r.scope == "per_source"]
    assert all((r.label == "not_enough_data") == (r.label_reason is not None) for r in per_source)


def test_the_database_requires_two_effective_papers_for_check_2(engine):
    """Re-check (owner, 2026-10-06): check 2 needs an effective number of papers of at least 2."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_check2_consistent"):
        _insert_result(engine, rid, effective_papers=1.5, estimate=1.0, std_error=1.0, p_value=0.1)
    _insert_result(engine, rid, effective_papers=1.5, check2_passed=False, estimate=1.0)
    assert rows_of(engine, "SELECT inference_reason FROM analysis_result WHERE run_id = :r", r=rid) == [
        ("evidence_concentrated",)]


def test_the_effective_number_and_share_are_stored_with_every_result(engine):
    rid = run_on(engine, small_rows(3, papers=3))  # withheld: structure only
    analysis.run_statistics(engine, rid)
    for r in result_rows(engine, rid):
        assert r.effective_papers > 0 and 0 < r.largest_paper_share <= 1


P_VALUE_TEXT = "approximate, nominal, one-sided cluster-robust p-value under the locked method"


def test_every_p_value_is_stored_with_its_description_and_the_four_quantities(reference):
    """Owner, at the merge decision (2026-10-06): each result with a p-value stores the fixed description
    and, together, the informative paper count, the effective number, the largest paper's share and the
    t distribution's degrees of freedom, so they can always be shown together."""
    engine, rid, out = reference
    with_p = [r for r in result_rows(engine, rid) if r.p_value is not None]
    assert with_p
    for r in with_p:
        assert r.p_value_description == P_VALUE_TEXT
        assert r.t_df == r.n_groups_informative - 1
        assert r.effective_papers is not None and r.largest_paper_share is not None
    pooled = out["analyses"][0]
    assert pooled["p_value_description"] == P_VALUE_TEXT and pooled["df"] == 19
    assert (pooled["counts"]["n_groups_informative"], round(pooled["counts"]["effective_papers"], 2),
            round(pooled["counts"]["largest_paper_share"], 3)) == (20, 3.94, 0.387)
    assert all(r.p_value_description is None and r.t_df is None for r in result_rows(engine, rid) if r.p_value is None)


def test_the_database_refuses_a_p_value_without_its_description_and_quantities(engine):
    rid = run_on(engine, small_rows(3, papers=3), option="use_available")
    with pytest.raises(IntegrityError, match="ck_analysis_result_reported_together"):
        _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, t_df=None, p_value_description=None)
    with pytest.raises(IntegrityError, match="ck_analysis_result_reported_together"):
        _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, t_df=5)  # not informative - 1
    with pytest.raises(IntegrityError, match="ck_analysis_result_p_value_description"):
        _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1, p_value_description="exact p-value")
    _insert_result(engine, rid, estimate=1.0, std_error=1.0, p_value=0.1)
