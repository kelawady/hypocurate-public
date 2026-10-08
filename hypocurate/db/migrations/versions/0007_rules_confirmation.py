"""The run waits at the rules lock for a named person; the spending ceiling on the run (build step 9a).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-08

Approved by the owner on 2026-10-08 (step 9 plan: Q1, Q5, R5 and addition A1), subject to the second-model
review before merging.

run:
- a new status, 'waiting': a run whose plan comes from a model's answer stops before its rules lock until a
  named person confirms the question as tested (Q1). It waits only then: from 'running', with no plan, no
  stage running and no model call open, and either a Planner stage and code's latest narrowing decision to
  proceed, or as a narrower question's run (Q5; a fixed-plan run of an ordinary question never waits). It
  waits once; it goes on to 'running' only with a confirmation; it can fail (a cancel) and never completes.
  Every rule of 0001 that writes to a run requires 'running', so nothing is written to a waiting run.
- 0001's `hc_run_update` is replaced, with its body unchanged except the list of status changes, which gains
  running -> waiting, waiting -> waiting, waiting -> running and waiting -> failed. It is the only earlier
  function replaced; the downgrade restores 0001's text exactly.
- `spending_ceiling` (R5): the run's effective ceiling, stored at dispatch, positive and finite, never changed (it
  joins what a run records at dispatch). The owner's decision (fix round 1): every new run stores one; none given is
  the per-run cap ($2, the column's default), so the column is never empty for a run dispatched after 0007. An insert
  trigger replaces an explicit NULL with the cap too (second review, owner 2026-10-08), so even direct SQL cannot
  store a new run without a ceiling.
- a failure reason 'cancelled: ...' only from queued or waiting (fix round 1, finding 5); other failures from running
  stay allowed.
rules_confirmation (Q1, A1, A2), append-only, one per run:
- only for a waiting run; by a named person (1-200 characters); at the database's time;
- the fingerprint of the plan that will be locked, in the plan fingerprint format;
- a Planner run's confirmation names the run's done Planner stage and its latest narrowing decision (to
  proceed); a narrower question's names neither;
- the source versions the narrowing counts were taken on (the run's own decision, or the original's for a
  narrower question) are exactly the run's versions;
- no source the run uses has a newer sealed version than the run's, and no source was registered after the run's
  dispatch (fix round 1, finding 2). It takes one advisory lock that registering a source and sealing a version take
  too, so a registration and a confirmation cannot slip past each other;
- the content shown (a JSON object) and the exact text shown (not empty).
plan:
- a plan for a run with a Planner stage (any attempt) or of a narrower question is locked only with that run's
  confirmation of exactly its fingerprint. A run with no Planner stage and no narrower link (a fixed-plan run,
  and the step 6-8 test worlds that lock a plan directly) is unaffected: the orchestrator builds a Planner plan
  only from a stored Planner stage (scoping stated in the step 9a summary).
hypothesis:
- at most one narrower question per original run (a unique index), so a repeated completion step can never
  create a second one.

Works with the previous release's code: it never sets 'waiting' and writes no confirmation or ceiling. Its
Planner runs and narrower questions are refused at the lock (deliberately: no plan from a model's answer is
locked without a person); its fixed-plan runs are unaffected. The owner checks the live database for runs in
progress before the deploy (R7).

Downgrade refuses while a run is waiting, a confirmation exists or a ceiling below the run cap is set (a ceiling
equal to the cap says no more than the cap), then drops what 0007
added and restores 0001's function and status rule.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it
keeps working with the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None

STATUSES_0001 = ('queued', 'running', 'completed', 'failed')
STATUSES_0007 = ('queued', 'running', 'waiting', 'completed', 'failed')
CONFIRMED_BY_MAX = 200
# Fix round 1, finding 2: one transaction-scoped advisory lock taken by registering a source, by sealing a source
# version and by a confirmation, so neither can slip past the other ("hcsrces"; tests check it equals
# pipeline/confirmation.SOURCES_LOCK_KEY; single-bigint keys in use elsewhere: spend.MONTH_LOCK_KEY, migrate's lock).
SOURCES_LOCK_KEY = 0x68637372636573
# The owner's decision (2026-10-08): every new run stores its effective ceiling at dispatch; none given is the per-run
# cap. The default (tests check it equals spend.RUN_CAP_USD) also covers a dispatch by the previous release's code.
# It is set after the column is added, so runs dispatched before 0007 keep no ceiling.
CEILING_DEFAULT = "2"

TRANSITIONS_0001 = """(('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))"""
TRANSITIONS_0007 = """(('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'),
                                             ('running', 'waiting'), ('waiting', 'waiting'), ('waiting', 'running'),
                                             ('waiting', 'failed'))"""

# 0001's function, copied verbatim (tests/test_migrations_step9a.py checks it against 0001's own text).
RUN_UPDATE_0001 = """
    CREATE OR REPLACE FUNCTION hc_run_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE p plan; pooled analysis_result; n_pooled int;
    BEGIN
        IF OLD.status IN ('completed', 'failed') THEN
            PERFORM hc_reject('a ' || OLD.status || ' run is final');
        END IF;
        IF NEW.hypothesis_version_id <> OLD.hypothesis_version_id OR NEW.agent_mode <> OLD.agent_mode
           OR NEW.fixed_plan <> OLD.fixed_plan OR NEW.experiment_flags <> OLD.experiment_flags
           OR NEW.queued_at <> OLD.queued_at THEN
            PERFORM hc_reject('what a run records at dispatch cannot change');
        END IF;
        IF NOT ((OLD.status, NEW.status) IN (('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))) THEN
            PERFORM hc_reject('run status cannot go from ' || OLD.status || ' to ' || NEW.status);
        END IF;
        IF OLD.status = 'queued' AND NEW.status = 'running' AND EXISTS (
            SELECT 1 FROM source s WHERE s.created_at <= NEW.queued_at
              AND NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.id AND rs.source_id = s.id)) THEN
            PERFORM hc_reject('a run starts only with a run_source row for every source registered at dispatch');
        END IF;
        IF NEW.status IN ('completed', 'failed') THEN
            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
                PERFORM hc_reject('a run ends only when no stage is running and no model call is open');
            END IF;
        END IF;
        IF NEW.status = 'completed' AND NEW.outcome = 'sufficient' THEN
            SELECT * INTO p FROM plan WHERE run_id = NEW.id;
            IF NOT FOUND THEN
                PERFORM hc_reject('a sufficient outcome needs a locked plan');
            END IF;
            SELECT count(*) INTO n_pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            IF n_pooled <> 1 OR pooled.check2_passed IS NOT TRUE THEN
                PERFORM hc_reject('a sufficient outcome needs exactly one pooled result that passed both validity checks');
            END IF;
            IF p.sufficiency_option = 'fixed_minimum' AND NOT pooled.minimums_met THEN
                PERFORM hc_reject('under fixed_minimum, a sufficient outcome needs the minimums met');
            END IF;
            IF NEW.exploratory <> (p.sufficiency_option = 'use_available' AND NOT pooled.minimums_met) THEN
                PERFORM hc_reject('exploratory must equal: use_available and the minimums not met');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """
RUN_UPDATE_0007 = RUN_UPDATE_0001.replace(TRANSITIONS_0001, TRANSITIONS_0007)
assert RUN_UPDATE_0007 != RUN_UPDATE_0001

# Shared by three functions: does the run's plan come from a model's answer (a Planner stage, any attempt), or is
# it a narrower question's run? Both need a person's confirmation before the lock.
NEEDS_CONFIRMATION = """(EXISTS (SELECT 1 FROM stage_result WHERE run_id = {run} AND stage = 'planner')
            OR EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
                       JOIN hypothesis h ON h.id = hv.hypothesis_id
                       WHERE r.id = {run} AND h.narrower_of_run_id IS NOT NULL))"""

FUNCTIONS = [
    # Waiting (Q1, Q5) and the ceiling recorded at dispatch (R5). (0001's hc_run_update, which fires first, holds
    # the run's row and has checked the status change itself.)
    f"""
    CREATE FUNCTION hc_run_waiting() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE latest jsonb;
    BEGIN
        IF NEW.spending_ceiling IS DISTINCT FROM OLD.spending_ceiling THEN
            PERFORM hc_reject('what a run records at dispatch cannot change');
        END IF;
        -- Fix round 1, finding 5: a cancel (a failure reason 'cancelled: ...') only from queued or waiting.
        IF NEW.status = 'failed' AND OLD.status NOT IN ('queued', 'waiting')
           AND NEW.failure_reason LIKE 'cancelled:%' THEN
            PERFORM hc_reject('a run is cancelled only while it is queued or waiting');
        END IF;
        IF OLD.status = 'running' AND NEW.status = 'waiting' THEN
            IF NOT {NEEDS_CONFIRMATION.format(run='NEW.id')} THEN
                PERFORM hc_reject('only a run whose plan comes from the Planner or a narrower question waits');
            END IF;
            IF EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = NEW.id) THEN
                PERFORM hc_reject('a run waits once: it is already confirmed');
            END IF;
            IF EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id) THEN
                PERFORM hc_reject('a run waits only before its rules lock');
            END IF;
            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
                PERFORM hc_reject('a run waits only when no stage is running and no model call is open');
            END IF;
            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'planner') THEN
                SELECT CASE WHEN status = 'done' THEN output END INTO latest FROM stage_result
                WHERE run_id = NEW.id AND stage = 'narrowing' ORDER BY id DESC LIMIT 1;
                IF latest IS NULL OR latest->>'result' IS DISTINCT FROM 'proceed' THEN
                    PERFORM hc_reject('a Planner run waits only after code''s narrowing decision to proceed');
                END IF;
            END IF;
        END IF;
        IF OLD.status = 'waiting' AND NEW.status = 'running'
           AND NOT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = NEW.id) THEN
            PERFORM hc_reject('a waiting run goes on only after a person confirms the question as tested');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The confirmation (Q1, A1): of a waiting run, by a named person, at the database's time, naming the stages it
    # rests on, on the source versions the narrowing counts were taken on.
    """
    CREATE FUNCTION hc_rules_confirmation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original bigint; planner_run boolean; decision jsonb; stored text[]; current text[];
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'waiting' THEN
            PERFORM hc_reject('only a run waiting for confirmation is confirmed');
        END IF;
        -- Fix round 1, finding 2: the registered sources as they are now, after any registration or seal in progress
        -- has committed (the shared lock; each statement below reads with a new snapshot).
        PERFORM pg_advisory_xact_lock(29382745069413747);  -- SOURCES_LOCK_KEY
        IF EXISTS (SELECT 1 FROM run_source rs JOIN source_version sv ON sv.source_id = rs.source_id
                   WHERE rs.run_id = NEW.run_id AND rs.source_version_id IS NOT NULL AND sv.sealed_at IS NOT NULL
                     AND sv.id > rs.source_version_id) THEN
            PERFORM hc_reject('a confirmation is refused: a source the run uses has a newer sealed version than the '
                              'run''s (the narrowing no longer describes the registered sources)');
        END IF;
        IF EXISTS (SELECT 1 FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.run_id
                                                             AND rs.source_id = s.id)) THEN
            PERFORM hc_reject('a confirmation is refused: a source was registered after the run''s dispatch');
        END IF;
        NEW.confirmed_at := now();
        SELECT h.narrower_of_run_id INTO original
        FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
        JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = NEW.run_id;
        planner_run := EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'planner');
        IF original IS NOT NULL AND NOT planner_run THEN
            IF NEW.planner_stage_result_id IS NOT NULL OR NEW.narrowing_stage_result_id IS NOT NULL THEN
                PERFORM hc_reject('a narrower question''s confirmation names no Planner or narrowing stage of its own');
            END IF;
            SELECT output INTO decision FROM stage_result
            WHERE run_id = original AND stage = 'narrowing' AND status = 'done'
              AND output->>'result' = 'partly_sufficient'
            ORDER BY id DESC LIMIT 1;
        ELSE
            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.planner_stage_result_id AND run_id = NEW.run_id
                             AND stage = 'planner' AND status = 'done')
               OR NEW.narrowing_stage_result_id IS DISTINCT FROM (
                    SELECT id FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing'
                    ORDER BY id DESC LIMIT 1)
               OR NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.narrowing_stage_result_id
                                AND status = 'done' AND output->>'result' = 'proceed') THEN
                PERFORM hc_reject('a Planner run''s confirmation names the run''s done Planner stage and its latest '
                                  'narrowing decision (to proceed)');
            END IF;
            SELECT output INTO decision FROM stage_result WHERE id = NEW.narrowing_stage_result_id;
        END IF;
        SELECT coalesce(array_agg((e->>'source') || ' ' || (e->>'version_fingerprint')
                                  ORDER BY (e->>'source') || ' ' || (e->>'version_fingerprint')), '{}')
        INTO stored
        FROM jsonb_array_elements(CASE WHEN jsonb_typeof(decision->'sources') = 'array'
                                       THEN decision->'sources' ELSE '[]'::jsonb END) e;
        SELECT coalesce(array_agg(s.key || ' ' || sv.fingerprint ORDER BY s.key || ' ' || sv.fingerprint), '{}')
        INTO current
        FROM run_source rs JOIN source s ON s.id = rs.source_id
        JOIN source_version sv ON sv.id = rs.source_version_id
        WHERE rs.run_id = NEW.run_id;
        IF decision IS NULL OR stored IS DISTINCT FROM current THEN
            PERFORM hc_reject('a confirmation is only for the run''s own source versions, which must be the source '
                              'versions the narrowing counts were taken on');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The plan backstop (Q1): a plan from a model's answer is locked only as confirmed by a person.
    # (0001's hc_plan_insert, which fires first, has locked the run.)
    f"""
    CREATE FUNCTION hc_plan_rules_confirmed() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF {NEEDS_CONFIRMATION.format(run='NEW.run_id')}
           AND NOT EXISTS (SELECT 1 FROM rules_confirmation
                           WHERE run_id = NEW.run_id AND plan_fingerprint = NEW.fingerprint) THEN
            PERFORM hc_reject('a plan from the Planner or for a narrower question needs a person''s confirmation of '
                              'exactly this plan (its fingerprint) before the rules lock');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Second review (owner, 2026-10-08): no new run is stored without a ceiling, even by direct SQL; an explicit NULL
    # becomes the per-run cap (the column's default covers only a column left out). Runs before 0007 keep theirs.
    f"""
    CREATE FUNCTION hc_run_ceiling() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.spending_ceiling IS NULL THEN
            NEW.spending_ceiling := {CEILING_DEFAULT};
        END IF;
        RETURN NEW;
    END $$
    """,
    # Fix round 1, finding 2: registering a source and sealing a version take the confirmation's lock.
    f"""
    CREATE FUNCTION hc_sources_lock() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM pg_advisory_xact_lock({SOURCES_LOCK_KEY});
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_run_waiting()", "hc_rules_confirmation_insert()", "hc_plan_rules_confirmed()", "hc_run_ceiling()",
                  "hc_sources_lock()"]

APPEND_ONLY = ["rules_confirmation"]
# (table, event, trigger, function). Each trigger's name sorts after the earlier triggers on its table.
CHECKED = [
    ("run", "UPDATE", "hc_run_update_waiting", "hc_run_waiting"),
    ("rules_confirmation", "INSERT", "hc_rules_confirmation_insert", "hc_rules_confirmation_insert"),
    ("plan", "INSERT", "hc_plan_insert_rules_confirmed", "hc_plan_rules_confirmed"),
    ("run", "INSERT", "hc_run_insert_spending_ceiling", "hc_run_ceiling"),
    ("source", "INSERT", "hc_source_insert_sources_lock", "hc_sources_lock"),
    ("source_version", "INSERT", "hc_source_version_insert_sources_lock", "hc_sources_lock"),
    ("source_version", "UPDATE", "hc_source_version_update_sources_lock", "hc_sources_lock"),
]
# Fix round 1, finding 2: a version takes the lock only when it is (or becomes) sealed; a new source always.
WHEN = {"hc_source_version_insert_sources_lock": "WHEN (NEW.sealed_at IS NOT NULL) ",
        "hc_source_version_update_sources_lock": "WHEN (OLD.sealed_at IS NULL AND NEW.sealed_at IS NOT NULL) "}
TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW {WHEN.get(t, '')}EXECUTE FUNCTION {f}()"
       for table, event, t, f in CHECKED]
)


def _in(column: str, values) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    op.drop_constraint(op.f('ck_run_status'), 'run', type_='check')
    op.create_check_constraint(op.f('ck_run_status'), 'run', _in('status', STATUSES_0007))
    op.execute(RUN_UPDATE_0007)
    op.add_column('run', sa.Column('spending_ceiling', sa.Numeric(), nullable=True))
    op.alter_column('run', 'spending_ceiling', server_default=sa.text(CEILING_DEFAULT))
    op.create_check_constraint(op.f('ck_run_spending_ceiling'), 'run',
                               "spending_ceiling IS NULL OR (spending_ceiling > 0 AND spending_ceiling < 'Infinity')")
    op.create_table(
        'rules_confirmation',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('run_id', sa.BigInteger(), nullable=False),
        sa.Column('confirmed_by', sa.Text(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('plan_fingerprint', sa.Text(), nullable=False),
        sa.Column('planner_stage_result_id', sa.BigInteger(), nullable=True),
        sa.Column('narrowing_stage_result_id', sa.BigInteger(), nullable=True),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('shown', sa.Text(), nullable=False),
        sa.CheckConstraint(f"length(btrim(confirmed_by)) BETWEEN 1 AND {CONFIRMED_BY_MAX}",
                           name=op.f('ck_rules_confirmation_named')),
        sa.CheckConstraint("plan_fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_rules_confirmation_fingerprint_format')),
        sa.CheckConstraint("jsonb_typeof(content) = 'object' AND length(shown) > 0",
                           name=op.f('ck_rules_confirmation_content_and_text')),
        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_rules_confirmation_run_id')),
        sa.ForeignKeyConstraint(['planner_stage_result_id'], ['stage_result.id'],
                                name=op.f('fk_rules_confirmation_planner_stage_result_id')),
        sa.ForeignKeyConstraint(['narrowing_stage_result_id'], ['stage_result.id'],
                                name=op.f('fk_rules_confirmation_narrowing_stage_result_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_rules_confirmation')),
        sa.UniqueConstraint('run_id', name=op.f('uq_rules_confirmation_run_id')),
    )
    op.create_index('uq_hypothesis_narrower_of_run_id', 'hypothesis', ['narrower_of_run_id'], unique=True,
                    postgresql_where=sa.text('narrower_of_run_id IS NOT NULL'))
    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)


IN_USE = f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM run WHERE status = 'waiting' OR spending_ceiling < {CEILING_DEFAULT})
           OR EXISTS (SELECT 1 FROM rules_confirmation) THEN
            RAISE EXCEPTION 'hypocurate: migration 0007 is in use (a waiting run, a confirmation or a spending ceiling below the run cap); not downgraded';
        END IF;
    END $$
"""


def downgrade() -> None:
    op.execute(IN_USE)
    for t in reversed(TRIGGERS):
        name, table = t.split()[2], t.split(" ON ")[1].split()[0]
        op.execute(f"DROP TRIGGER {name} ON {table}")
    for f in FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
    op.drop_index('uq_hypothesis_narrower_of_run_id', table_name='hypothesis')
    op.drop_table('rules_confirmation')
    op.drop_constraint(op.f('ck_run_spending_ceiling'), 'run', type_='check')
    op.drop_column('run', 'spending_ceiling')
    op.execute(RUN_UPDATE_0001)
    op.drop_constraint(op.f('ck_run_status'), 'run', type_='check')
    op.create_check_constraint(op.f('ck_run_status'), 'run', _in('status', STATUSES_0001))
