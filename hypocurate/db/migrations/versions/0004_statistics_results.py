"""Step 7 results: the withheld state, the records a fit does not use, the test-run label, both
calibration methods, the fourth per-source label and the run's evidence level (build step 7).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05

Approved by the owner on 2026-10-05, subject to the second-model review before merging. Additive:
0001 to 0003 are untouched; the two trigger functions replaced here keep every check of 0001.

analysis_result:
- `withheld` (owner, decision 1): under the fixed option, when the pooled fit misses a minimum,
  every analysis of the run holds counts only. **The database computes it**: the insert trigger
  derives it from the plan and the pooled result (for the pooled row: fixed option and minimums
  not met; for any other row: the run's pooled row, which must exist first). A caller's value
  must agree; a missing value is filled in. Estimate, standard error and p-value are present
  exactly when their check passed **and the row is not withheld** (the three CHECKs of 0001 keep
  their names, with "AND NOT withheld" added).
- `n_records_not_used` (decision 7): records of the set the fit does not use (alloys with fewer
  than two distinct grain sizes within this analysis). The trigger now checks
  n_records + n_records_not_used = the records of the set used; the stored counts are the fit's.
- `test_run_label`: "test run: includes constructed data" exactly when the run is marked.
- The label CHECK gains `same_direction_different_decision` (decision 2/3); a label only on a
  per-source row; an estimated power only where inference is valid.

calibration_result:
- `method` ('fixed' or 'estimated'): present exactly on rows of an analysis; the one run-level
  row ("no dataset frozen") has none. The unique index becomes (run, analysis, method).
- Reasons gain `below_minimums`, `scatter_not_estimable`, `shift_not_estimable`.
- `test_run_label`, as above.
- The insert trigger: computed only where inference is valid and the result is not withheld;
  where it is, the fixed method must be computed and the estimated one is computed or names why
  the noise cannot be estimated; every other reason must match the validity checks and the
  withheld state.

run:
- `evidence_level` 1 to 6 (owner, 2026-10-05; register 'evidence_level_scale'). Written only by
  the copy path (`pipeline/completion.py`); when present it must agree with the outcome: 6 = a
  verdict and not exploratory, 5 = a verdict and exploratory, 1 to 4 = no verdict; present only
  with an outcome. **The database does not require it** on a completed run.

Marked runs are left out of every aggregate by `pipeline/results.py` (`real_runs`), in code, not by
a view (register 'constructed_test_runs').

Works with the previous release's code: that code writes no analysis or calibration result
except the run-level "no dataset frozen" row, which keeps its shape (an unmarked run needs no
label), and never completes a run.

Downgrade refuses while any row uses what 0004 adds (a withheld result, an unused record, a test
label, an estimated calibration, a new reason or label, an evidence level), then restores 0001's
functions, constraints and index exactly.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
transaction (no CONCURRENTLY, no autocommit_block); it keeps working with the previous release's
code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

TEST_RUN_LABEL = "test run: includes constructed data"
MARKED = "coalesce((SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = NEW.run_id) = 'true', false)"

# 0001's functions, verbatim (restored by the downgrade).
ANALYSIS_RESULT_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        RETURN NEW;
    END $$
    """

CALIBRATION_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF (NEW.status = 'computed') <> a.check2_passed THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid');
        END IF;
        IF NEW.reason = 'coefficient_not_fitted' AND a.check1_passed
           OR NEW.reason = 'insufficient_groups' AND NOT (a.check1_passed AND NOT a.check2_passed) THEN
            PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
        END IF;
        RETURN NEW;
    END $$
    """

ANALYSIS_RESULT_INSERT_0004 = """
    CREATE OR REPLACE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int; pooled analysis_result; computed boolean;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records + NEW.n_records_not_used <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used, less those the fit does not use');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        -- Step 7, decision 1: withheld run-wide when the pooled fit misses a minimum under the fixed option.
        IF NEW.scope = 'pooled' THEN
            computed := p.sufficiency_option = 'fixed_minimum' AND NOT NEW.minimums_met;
        ELSE
            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.run_id AND scope = 'pooled';
            IF NOT FOUND THEN
                PERFORM hc_reject('the pooled result is written before any other result of the run');
            END IF;
            computed := pooled.withheld;
        END IF;
        IF NEW.withheld IS NULL THEN
            NEW.withheld := computed;
        ELSIF NEW.withheld <> computed THEN
            PERFORM hc_reject('withheld must equal: the fixed option and the pooled minimums not met');
        END IF;
        IF (NEW.test_run_label IS NOT NULL) <> """ + MARKED + """ THEN
            PERFORM hc_reject('a result carries the test-run label exactly when its run is marked as a test');
        END IF;
        RETURN NEW;
    END $$
    """

CALIBRATION_INSERT_0004 = """
    CREATE OR REPLACE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result; expected text;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF (NEW.test_run_label IS NOT NULL) <> """ + MARKED + """ THEN
            PERFORM hc_reject('a result carries the test-run label exactly when its run is marked as a test');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF NEW.status = 'computed' AND NOT (a.check2_passed AND NOT a.withheld) THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid and the result is not withheld');
        END IF;
        IF NEW.status = 'unavailable' AND a.check2_passed AND NOT a.withheld
           AND NOT (NEW.method = 'estimated' AND NEW.reason IN ('scatter_not_estimable', 'shift_not_estimable')) THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid and the result is not withheld '
                              '(the estimated method may name why the noise cannot be estimated)');
        END IF;
        IF NEW.status = 'unavailable' AND NOT (a.check2_passed AND NOT a.withheld) THEN
            expected := CASE WHEN NOT a.check1_passed THEN 'coefficient_not_fitted'
                             WHEN NOT a.check2_passed THEN 'insufficient_groups'
                             ELSE 'below_minimums' END;
            IF NEW.reason IS NOT NULL AND NEW.reason <> expected THEN  -- a missing reason: the CHECK refuses it
                PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """

NEW_LABELS = "('agrees', 'conflicts', 'not_enough_data', 'same_direction_different_decision')"
OLD_LABELS = "('agrees', 'conflicts', 'not_enough_data')"
NEW_REASONS = ("('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups', 'below_minimums', "
               "'scatter_not_estimable', 'shift_not_estimable')")
OLD_REASONS = "('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')"

EVIDENCE_LEVEL = ("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
                  "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                  "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))")

IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM analysis_result WHERE withheld OR n_records_not_used <> 0
                   OR test_run_label IS NOT NULL OR label = 'same_direction_different_decision')
           OR EXISTS (SELECT 1 FROM calibration_result WHERE method = 'estimated' OR test_run_label IS NOT NULL
                      OR reason IN ('below_minimums', 'scatter_not_estimable', 'shift_not_estimable'))
           OR EXISTS (SELECT 1 FROM run WHERE evidence_level IS NOT NULL) THEN
            RAISE EXCEPTION USING MESSAGE = 'hypocurate: 0004 cannot be downgraded while step 7 results use it',
                                  ERRCODE = 'check_violation';
        END IF;
    END $$
    """


def upgrade() -> None:
    # analysis_result
    op.add_column('analysis_result', sa.Column('withheld', sa.Boolean(), nullable=True))
    op.execute("UPDATE analysis_result SET withheld = false")
    op.create_check_constraint(op.f('ck_analysis_result_withheld_set'), 'analysis_result', 'withheld IS NOT NULL')
    op.add_column('analysis_result', sa.Column('n_records_not_used', sa.Integer(), server_default=sa.text('0'),
                                               nullable=False))
    op.create_check_constraint(op.f('ck_analysis_result_not_used_not_negative'), 'analysis_result',
                               'n_records_not_used >= 0')
    op.add_column('analysis_result', sa.Column('test_run_label', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_analysis_result_test_run_label'), 'analysis_result',
                               f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'")
    for name, expr in (("estimate_iff_check1", "(check1_passed AND NOT withheld) = (estimate IS NOT NULL)"),
                       ("std_error_iff_check2", "(check2_passed AND NOT withheld) = (std_error IS NOT NULL)"),
                       ("p_value_iff_check2", "(check2_passed AND NOT withheld) = (p_value IS NOT NULL)"),
                       ("label", f"label IS NULL OR label IN {NEW_LABELS}")):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
        op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
    op.create_check_constraint(op.f('ck_analysis_result_label_per_source_only'), 'analysis_result',
                               "label IS NULL OR scope = 'per_source'")
    op.create_check_constraint(op.f('ck_analysis_result_power_needs_check2'), 'analysis_result',
                               'estimated_power IS NULL OR check2_passed')
    op.execute(ANALYSIS_RESULT_INSERT_0004)
    # calibration_result
    op.add_column('calibration_result', sa.Column('method', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_calibration_result_method'), 'calibration_result',
                               "method IS NULL OR method IN ('fixed', 'estimated')")
    op.create_check_constraint(op.f('ck_calibration_result_method_iff_analysis'), 'calibration_result',
                               '(method IS NULL) = (analysis_result_id IS NULL)')
    op.add_column('calibration_result', sa.Column('test_run_label', sa.Text(), nullable=True))
    op.create_check_constraint(op.f('ck_calibration_result_test_run_label'), 'calibration_result',
                               f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'")
    op.drop_constraint(op.f('ck_calibration_result_reason'), 'calibration_result', type_='check')
    op.create_check_constraint(op.f('ck_calibration_result_reason'), 'calibration_result',
                               f"reason IS NULL OR reason IN {NEW_REASONS}")
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id', 'method'],
                    unique=True, postgresql_nulls_not_distinct=True)
    op.execute(CALIBRATION_INSERT_0004)
    # run
    op.add_column('run', sa.Column('evidence_level', sa.SmallInteger(), nullable=True))
    op.create_check_constraint(op.f('ck_run_evidence_level'), 'run', EVIDENCE_LEVEL)


def downgrade() -> None:
    op.execute(IN_USE)
    op.drop_constraint(op.f('ck_run_evidence_level'), 'run', type_='check')
    op.drop_column('run', 'evidence_level')
    op.execute(CALIBRATION_INSERT_0001)
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id'],
                    unique=True, postgresql_nulls_not_distinct=True)
    op.drop_constraint(op.f('ck_calibration_result_reason'), 'calibration_result', type_='check')
    op.create_check_constraint(op.f('ck_calibration_result_reason'), 'calibration_result',
                               f"reason IS NULL OR reason IN {OLD_REASONS}")
    for name in ('test_run_label', 'method_iff_analysis', 'method'):
        op.drop_constraint(op.f(f'ck_calibration_result_{name}'), 'calibration_result', type_='check')
    op.drop_column('calibration_result', 'test_run_label')
    op.drop_column('calibration_result', 'method')
    op.execute(ANALYSIS_RESULT_INSERT_0001)
    for name in ('power_needs_check2', 'label_per_source_only'):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
    for name, expr in (("estimate_iff_check1", "check1_passed = (estimate IS NOT NULL)"),
                       ("std_error_iff_check2", "check2_passed = (std_error IS NOT NULL)"),
                       ("p_value_iff_check2", "check2_passed = (p_value IS NOT NULL)"),
                       ("label", f"label IS NULL OR label IN {OLD_LABELS}")):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
        op.create_check_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', expr)
    for name in ('test_run_label', 'not_used_not_negative', 'withheld_set'):
        op.drop_constraint(op.f(f'ck_analysis_result_{name}'), 'analysis_result', type_='check')
    op.drop_column('analysis_result', 'test_run_label')
    op.drop_column('analysis_result', 'n_records_not_used')
    op.drop_column('analysis_result', 'withheld')
