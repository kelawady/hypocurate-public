"""The query's sufficiency option, the partly-sufficient rules and the Critic's class (build step 8b).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-07

Approved by the owner on 2026-10-07 (step 8b plan, answers A2, A5 and A7), subject to the second-model
review before merging. 0001 to 0005 are untouched: no earlier function is replaced. Each new rule is its
own function with its own trigger, named so that it fires after the earlier trigger on the same table
and event (PostgreSQL fires BEFORE triggers in name order), so the earlier rules' messages keep their
priority.

hypothesis_version (A2: the data-sufficiency option is a parameter of the query, chosen before dispatch):
- `sufficiency_option`, 'fixed_minimum' (default) or 'use_available'. It can change only while the
  version is a draft; a narrower question has its original's option.
plan:
- the locked plan's `sufficiency_option` must equal its run's query's option;
- no plan is inserted for a run with a done narrowing decision of partly sufficient (A5).
run (A5):
- a run completes as 'partly_sufficient' only with no plan, no stored record, and a done 'narrowing'
  stage result whose output's result is 'partly_sufficient'. (0001 already requires no verdict, and 0004
  an evidence level consistent with it.)
flag (A7):
- `critic_class` is one of the Critic's fixed codes; `critic_reason` is at most 300 characters, not
  blank, and only with a class.

Works with the previous release's code: it inserts versions without the option (they get the
default, which is the only option that code's plans use), never completes a run as partly
sufficient, and writes no Critic class. The live database holds no run.

Downgrade refuses while a query uses another option than the default (its option would be lost),
then drops what 0006 added.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
transaction; it keeps working with the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

OPTIONS = ('fixed_minimum', 'use_available')
# The Critic's codes, copied here so the migration does not change when the code does
# (tests/test_migrations_step8b.py checks that they equal access.vocabulary.CRITIC_CLASSES).
CRITIC_CLASSES = ('cannot_tell', 'different_specimens_or_conditions', 'possible_transcription_or_unit_error',
                  'same_measurement')
CRITIC_REASON_MAX = 300


def _in(column: str, values) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


FUNCTIONS = [
    # The query's option: fixed once the version leaves draft; a narrower question has its original's.
    """
    CREATE FUNCTION hc_version_option() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original text;
    BEGIN
        IF TG_OP = 'UPDATE' AND OLD.status <> 'draft' AND NEW.sufficiency_option IS DISTINCT FROM OLD.sufficiency_option THEN
            PERFORM hc_reject('the sufficiency option is fixed once the version is submitted; an edit is a new version');
        END IF;
        SELECT hv.sufficiency_option INTO original
        FROM hypothesis h
        JOIN run r ON r.id = h.narrower_of_run_id
        JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
        WHERE h.id = NEW.hypothesis_id;
        IF original IS NOT NULL AND NEW.sufficiency_option IS DISTINCT FROM original THEN
            PERFORM hc_reject('a narrower question has the sufficiency option of its original');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The locked plan's option is the query's; no plan after a narrowing decision of partly sufficient.
    # (0001's hc_plan_insert, which fires first, has locked the run.)
    """
    CREATE FUNCTION hc_plan_query() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.sufficiency_option IS DISTINCT FROM (
                SELECT hv.sufficiency_option FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
                WHERE r.id = NEW.run_id) THEN
            PERFORM hc_reject('the plan''s sufficiency option is the query''s (chosen before dispatch)');
        END IF;
        IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing' AND status = 'done'
                     AND output->>'result' = 'partly_sufficient') THEN
            PERFORM hc_reject('no plan is locked after a narrowing decision of partly sufficient');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Partly sufficient: the original question is never tested (no plan, no record) and code's narrowing
    # decision is stored. (0001's hc_run_update, which fires first, holds the run's row.)
    """
    CREATE FUNCTION hc_run_partly_sufficient() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.status = 'completed' AND NEW.outcome = 'partly_sufficient' THEN
            IF EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id)
               OR EXISTS (SELECT 1 FROM record WHERE extraction_run_id = NEW.id) THEN
                PERFORM hc_reject('partly sufficient is only for a run with no plan and no record');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'narrowing'
                             AND status = 'done' AND output->>'result' = 'partly_sufficient') THEN
                PERFORM hc_reject('partly sufficient needs a narrowing decision of partly sufficient');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_version_option()", "hc_plan_query()", "hc_run_partly_sufficient()"]

# (table, event, trigger, function). Each trigger's name sorts after the earlier trigger it follows.
CHECKED = [
    ("hypothesis_version", "INSERT", "hc_version_insert_option", "hc_version_option"),
    ("hypothesis_version", "UPDATE", "hc_version_update_option", "hc_version_option"),
    ("plan", "INSERT", "hc_plan_insert_query", "hc_plan_query"),
    ("run", "UPDATE", "hc_run_update_partly_sufficient", "hc_run_partly_sufficient"),
]
TRIGGERS = [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
            for table, event, t, f in CHECKED]


def upgrade() -> None:
    op.add_column('hypothesis_version', sa.Column('sufficiency_option', sa.Text(),
                                                  server_default=sa.text("'fixed_minimum'"), nullable=False))
    op.create_check_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version',
                               _in('sufficiency_option', OPTIONS))
    op.create_check_constraint(op.f('ck_flag_critic_class'), 'flag',
                               f"critic_class IS NULL OR {_in('critic_class', CRITIC_CLASSES)}")
    op.create_check_constraint(op.f('ck_flag_critic_reason'), 'flag',
                               f"critic_reason IS NULL OR (critic_class IS NOT NULL "
                               f"AND length(btrim(critic_reason)) BETWEEN 1 AND {CRITIC_REASON_MAX})")
    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)


IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM hypothesis_version WHERE sufficiency_option <> 'fixed_minimum') THEN
            RAISE EXCEPTION 'hypocurate: migration 0006 is in use (a query uses another sufficiency option); not downgraded';
        END IF;
    END $$
"""


def downgrade() -> None:
    op.execute(IN_USE)
    for table, _, t, _ in CHECKED:
        op.execute(f"DROP TRIGGER {t} ON {table}")
    for f in FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
    op.drop_constraint(op.f('ck_flag_critic_reason'), 'flag', type_='check')
    op.drop_constraint(op.f('ck_flag_critic_class'), 'flag', type_='check')
    op.drop_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version', type_='check')
    op.drop_column('hypothesis_version', 'sufficiency_option')
