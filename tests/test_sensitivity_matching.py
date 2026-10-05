"""Step 6 review, finding 2: a sensitivity set that changes a matching setting recomputes the
matching flags under its own settings. Checks supplies them (Inclusion stays blind); every other
rule is unchanged.

The reviewer's example, through the real pipeline: Co50.06/Ni49.94 in one source and
Co50.04/Ni49.96 in another, each at two grain sizes, the same paper and values. At 0.1 at.% they
are two alloys (four records enter); at 1 at.% they are one alloy and each grain size is the same
measurement reported twice, so two records enter, not four."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import pipeline_world as pw


@pytest.fixture
def run(db):
    pw.registered_files(db, {
        "mpea": pw.mpea_csv([pw.mpea_row("Co50.06Ni49.94", 10.0, 300.0), pw.mpea_row("Co50.06Ni49.94", 40.0, 250.0)]),
        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50.04Ni49.96", 10.0, 300.0),
                                              pw.mpea_row("Co50.04Ni49.96", 40.0, 250.0)])})
    rid = pw.through_freeze(db, sources=("mpea", "controlled_duplicates"), marked=True)
    with db.connect() as conn:
        sets = {}
        for key, origin in conn.execute(text(
                "SELECT a.key, r.source_item_key || '@' || s.key FROM analysis_set a "
                "JOIN analysis_set_record asr ON asr.analysis_set_id = a.id JOIN record r ON r.id = asr.record_id "
                "JOIN source_version sv ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
                "WHERE a.run_id = :r"), dict(r=rid)):
            sets.setdefault(key, set()).add(origin)
        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
                             dict(r=rid)).scalar_one()
    from pipeline_fixtures import decisions
    return sets, stage, decisions(db, rid)


def test_the_coarser_same_alloy_rule_recomputes_the_duplicates(run):
    sets, stage, _ = run
    assert len(sets["primary"]) == 4  # two alloys at 0.1 at.%, each at two grain sizes
    coarse = sets["same_alloy_1_at_pct"]
    assert len(coarse) == 2
    assert {o.split("@")[1] for o in coarse} == {"mpea"}  # the MPEA records survive (source order)
    assert stage["rules"]["same_alloy_1_at_pct"]["duplicate_counted_once"] == 2


def test_every_other_set_keeps_the_primary_flags(run):
    sets, _, _ = run
    for key in ("no_exclusions", "tension_and_compression", "scope_not_confirmed_included",
                "possible_duplicates_separate", "conflicts_survivor_value"):
        assert sets[key] == sets["primary"], key


def test_the_one_change_rule_holds_with_recomputed_matching_flags(run):
    """The corrected one-change test accepts identity changes that come from the set's own flags."""
    from test_reference_sets import _check_one_change
    differing = _check_one_change(run[2])
    assert differing["same_alloy_1_at_pct"] == 2


# --- Re-check finding 1: reading inputs and verifying Checks in one transaction -------------------

def _coarse_run(db, through="store"):
    pw.registered_files(db, {
        "mpea": pw.mpea_csv([pw.mpea_row("Co50.06Ni49.94", 10.0, 300.0), pw.mpea_row("Co50.06Ni49.94", 40.0, 250.0)]),
        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50.04Ni49.96", 10.0, 300.0),
                                              pw.mpea_row("Co50.04Ni49.96", 40.0, 250.0)])})
    rid = pw.locked_run(db, sources=("mpea", "controlled_duplicates"), marked=True)
    from hypocurate.pipeline import extract
    extract.store_records(db, rid)
    return rid


def test_the_reviewers_interleaving_is_refused(db, monkeypatch):
    """Inclusion reads before Checks has completed; Checks then commits (no primary flags, but
    duplicate flags for the coarser same-alloy set); Inclusion's write follows. Inclusion must not
    write decisions computed without those flags."""
    from hypocurate.pipeline import checks, inclusion
    from hypocurate.pipeline.writes import Refused
    rid = _coarse_run(db)
    original = inclusion.write

    def checks_commit_between_read_and_write(*args, **kwargs):
        checks.run_checks(db, rid)
        return original(*args, **kwargs)

    monkeypatch.setattr(inclusion, "write", checks_commit_between_read_and_write)
    with pytest.raises(Refused) as refused:
        inclusion.decide_run(db, rid)
    assert refused.value.code == "checks_not_done"
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r"), dict(r=rid)).scalar() == 0
    # After the refusal, the normal order: Checks, then Inclusion with the set's own flags.
    monkeypatch.undo()
    checks.run_checks(db, rid)
    sets = inclusion.decide_run(db, rid)
    assert sum(r == "in_scope" for r in sets["same_alloy_1_at_pct"].values()) == 2


def test_a_missing_required_per_set_flag_result_is_a_refusal(db):
    """A completed Checks result that covers the records but lacks the flags a set needs (here the
    coarser same-alloy set) is refused, never read as 'no flags'."""
    from hypocurate.pipeline import inclusion, writes
    from hypocurate.pipeline.writes import Refused
    rid = _coarse_run(db)
    with db.begin() as conn:
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        identities = [writes.record_identity(fp, key, ix) for fp, key, ix in conn.execute(text(
            "SELECT sv.fingerprint, r.source_item_key, r.item_index FROM record r "
            "JOIN source_version sv ON sv.id = r.source_version_id WHERE r.extraction_run_id = :r"), dict(r=rid))]
        writes.code_stage(conn, rid, "checks", {}, {"binding": writes.binding(identities, []), "set_flags": {}})
    with pytest.raises(Refused) as refused:
        inclusion.decide_run(db, rid)
    assert refused.value.code == "set_flags_missing"
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r"), dict(r=rid)).scalar() == 0
