"""Step 7: migration 0004 (approved by the owner on 2026-10-05, subject to the second-model review).

Additive; 0001 to 0003 untouched; the two replaced trigger functions keep every check of 0001; up,
down, up gives the same schema; the downgrade refuses while step 7 results use what 0004 adds and
restores 0001's functions exactly; a failed upgrade changes nothing. Every test starts from an
empty scratch database, except the one that needs a run."""
from __future__ import annotations

import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis
from test_migrations import assert_schema_is_empty, assert_schema_is_head, snapshot
from test_migrations_step6 import body, columns

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0004 = SCRIPTS.get_revision("0004").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


def function_source(engine, name) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = :n"), dict(n=name)).scalar_one()


def checks_of(function_sql: str) -> list[str]:
    """Each `IF ... END IF;` block of a function body, whitespace normalized."""
    return re.findall(r"IF .*? END IF;", body(function_sql))


def test_0004_follows_0003():
    """Step 8a: 0004 is no longer the head (0005 follows it; tests/test_migrations_step8a.py)."""
    assert M0004.down_revision == "0003"


@pytest.mark.parametrize("name", ["hc_analysis_result_insert", "hc_calibration_insert"])
def test_the_downgrade_keeps_0001s_functions_verbatim(name):
    original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
    kept = M0004.ANALYSIS_RESULT_INSERT_0001 if name == "hc_analysis_result_insert" else M0004.CALIBRATION_INSERT_0001
    assert body(kept) == body(original)


def test_the_new_result_function_keeps_every_check_of_0001():
    """Every check of 0001's function is in 0004's, unchanged, except three: the record count now
    accounts for the records the fit does not use (decision 7); the minimums count informative groups
    (owner, 2026-10-06); and the bound of the alloy count by the display label is removed (review
    finding 2: the label is rounded to 0.1 at.%, the plan's same-alloy rule may be finer)."""
    old, new = checks_of(M0004.ANALYSIS_RESULT_INSERT_0001), body(M0004.ANALYSIS_RESULT_INSERT_0004)
    changed = [c for c in old if c not in new]
    assert changed == [
        "IF NEW.n_records <> set_count THEN PERFORM hc_reject('n_records must equal the records of the set used'); "
        "END IF;",
        "IF NEW.n_alloys > set_alloys THEN PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the "
        "set used'); END IF;",
        "IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys AND NEW.n_groups "
        ">= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN PERFORM hc_reject('minimums_met must agree with "
        "the counts and the plan''s minimums'); END IF;"]
    assert ("IF NEW.n_records + NEW.n_records_not_used <> set_count THEN PERFORM hc_reject('n_records must equal "
            "the records of the set used, less those the fit does not use'); END IF;") in new
    assert "NEW.n_groups_informative >= p.min_groups" in new and "set_alloys" not in new


def test_the_new_calibration_function_keeps_the_run_level_rules_of_0001():
    old, new = body(M0004.CALIBRATION_INSERT_0001), body(M0004.CALIBRATION_INSERT_0004)
    for kept in ("IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN PERFORM hc_reject('calibration is "
                 "recorded only while the run is running'); END IF;",
                 "IF NEW.analysis_result_id IS NULL THEN IF hc_is_frozen(NEW.run_id) THEN PERFORM hc_reject('a dataset "
                 "was frozen: calibration is reported per analysis'); END IF; RETURN NEW; END IF;"):
        assert kept in old and kept in new
    # 0001's "computed exactly when inference is valid" is kept, strengthened by "and not withheld".
    assert "calibration is computed exactly when inference is valid" in old
    assert "calibration is computed exactly when inference is valid and the result is not withheld" in new


def test_up_down_up(engine):
    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    first = snapshot(engine)
    assert {"withheld", "n_records_not_used", "test_run_label"} <= columns(engine, "analysis_result")
    assert {"method", "test_run_label"} <= columns(engine, "calibration_result")
    assert "evidence_level" in columns(engine, "run")
    migrate.downgrade(engine, "0003")
    assert migrate.current_revision(engine) == "0003"
    assert not {"withheld", "n_records_not_used", "test_run_label"} & columns(engine, "analysis_result")
    assert not {"method", "test_run_label"} & columns(engine, "calibration_result")
    assert "evidence_level" not in columns(engine, "run")
    for name in ("hc_analysis_result_insert", "hc_calibration_insert"):
        original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
        assert " ".join(function_source(engine, name).split()) == body(original)
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0003")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE run ADD COLUMN evidence_level int"))  # 0004 adds it last
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0003"


def test_the_downgrade_refuses_while_step_7_results_use_0004(db):
    """A run with step 7 results: the downgrade refuses, and nothing changes."""
    import stats_world as sw
    rid = sw.run_on(db, sw.small_rows(3, papers=3))
    analysis.run_statistics(db, rid)  # withheld results and 'below_minimums' calibration rows
    before = snapshot(db)
    with pytest.raises(IntegrityError, match="0004 cannot be downgraded while step 7 results use it"):
        migrate.downgrade(db, "0003")
    # Step 8a: the database stays at the head (0005, which holds nothing here, is not undone either:
    # the whole downgrade is one transaction).
    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
