"""Claims: a worker's hold on one run, with its heartbeat (build step 9b).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-08

Approved by the owner on 2026-10-08 (the step 9 plan, R6; docs/reviews/step09b_plan.md), subject to the
second-model review before merging. 0001 to 0007 untouched: no earlier function is replaced.

run_claim, one row per claim, never deleted:
- the run, the worker (1-200 characters, `host:pid`), the guarded child's pid (recorded once), the claim's time
  and its heartbeat (both the database's time), and how it was released: once, at the database's time, with a
  reason from a fixed list (`RELEASE_REASONS`), and what recovery found (`found`, a JSON object);
- only an open run (queued, running or waiting) is claimed, and at most one claim per run is open (a partial
  unique index);
- while a claim is open only its heartbeat, its child's pid (once), `found` and the release may change; once
  released it is final;
- (fix round 1) `recovery`: whether the claim took up a run already running (a recovery attempt), never changed;
  closing a claim locks its row FOR UPDATE first, so it waits for a write of the claim's child in progress (which
  holds the row FOR KEY SHARE, `pipeline/writes.owner_holds`).
The heartbeat is written on the claim row, not the run row (R6), so it never waits behind a transaction that holds
the run's lock: the update trigger reads no run row. A named exception to the locking protocol, like audit rows.

Works with the previous release's code: it never reads or writes run_claim. The live database has never had a run.

Downgrade refuses while any claim exists (claims are history), then drops what 0008 added.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it keeps
working with the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

# Copied here so the migration does not change when the code does (tests check they equal queue.RELEASE_REASONS).
RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
WORKER_MAX = 200


def _in(column: str, values) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


FUNCTIONS = [
    # A claim of an open run, at the database's time.
    """
    CREATE FUNCTION hc_run_claim_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) NOT IN ('queued', 'running', 'waiting') THEN
            PERFORM hc_reject('only an open run is claimed (queued, running or waiting)');
        END IF;
        IF NEW.released_at IS NOT NULL OR NEW.release_reason IS NOT NULL OR NEW.found IS NOT NULL THEN
            PERFORM hc_reject('a claim is released after it is made');
        END IF;
        NEW.claimed_at := now();
        NEW.heartbeat_at := NEW.claimed_at;
        RETURN NEW;
    END $$
    """,
    # While open: the heartbeat (the database's time), the child's pid once, what recovery found, the release once.
    # Reads no run row (R6): a heartbeat never waits behind the run's lock.
    """
    CREATE FUNCTION hc_run_claim_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF OLD.released_at IS NOT NULL THEN
            PERFORM hc_reject('a released claim is final');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.worker <> OLD.worker OR NEW.claimed_at <> OLD.claimed_at THEN
            PERFORM hc_reject('what a claim records cannot change');
        END IF;
        IF OLD.child_pid IS NOT NULL AND NEW.child_pid IS DISTINCT FROM OLD.child_pid THEN
            PERFORM hc_reject('a claim''s child is recorded once');
        END IF;
        IF NEW.recovery IS DISTINCT FROM OLD.recovery THEN
            PERFORM hc_reject('what a claim records cannot change');
        END IF;
        -- Fix round 1, finding 3 (owner, 2026-10-09): closing a claim waits for any write of its child in progress
        -- (which holds the row FOR KEY SHARE), so the write commits first or sees the claim closed.
        IF NEW.released_at IS NOT NULL THEN
            PERFORM 1 FROM run_claim WHERE id = OLD.id FOR UPDATE;
        END IF;
        IF NEW.heartbeat_at IS DISTINCT FROM OLD.heartbeat_at THEN
            NEW.heartbeat_at := clock_timestamp();
        END IF;
        IF NEW.released_at IS NOT NULL THEN
            NEW.released_at := clock_timestamp();
        END IF;
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_run_claim_insert()", "hc_run_claim_update()"]

NO_DELETE = ["run_claim"]
CHECKED = [
    ("run_claim", "INSERT", "hc_run_claim_insert", "hc_run_claim_insert"),
    ("run_claim", "UPDATE", "hc_run_claim_update", "hc_run_claim_update"),
]
TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_no_delete BEFORE DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION hc_no_delete()"
     for t in NO_DELETE]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION hc_no_delete()"
       for t in NO_DELETE]
    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
       for table, event, t, f in CHECKED]
)


def upgrade() -> None:
    op.create_table(
        'run_claim',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('run_id', sa.BigInteger(), nullable=False),
        sa.Column('worker', sa.Text(), nullable=False),
        sa.Column('child_pid', sa.Integer(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('release_reason', sa.Text(), nullable=True),
        sa.Column('found', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Fix round 1, finding 7: the claim took up a run that was already running (a recovery attempt), set at the
        # claim and never changed; the first run's claim (from queued or waiting) is not one.
        sa.Column('recovery', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.CheckConstraint(f"length(btrim(worker)) BETWEEN 1 AND {WORKER_MAX}", name=op.f('ck_run_claim_worker_named')),
        sa.CheckConstraint(f"release_reason IS NULL OR {_in('release_reason', RELEASE_REASONS)}",
                           name=op.f('ck_run_claim_release')),
        sa.CheckConstraint("(released_at IS NULL) = (release_reason IS NULL)",
                           name=op.f('ck_run_claim_released_with_reason')),
        sa.CheckConstraint("found IS NULL OR jsonb_typeof(found) = 'object'", name=op.f('ck_run_claim_found_object')),
        sa.CheckConstraint("child_pid IS NULL OR child_pid > 0", name=op.f('ck_run_claim_child_pid')),
        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_claim_run_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_run_claim')),
    )
    op.create_index('uq_run_claim_open', 'run_claim', ['run_id'], unique=True,
                    postgresql_where=sa.text('released_at IS NULL'))
    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)


IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM run_claim) THEN
            RAISE EXCEPTION 'hypocurate: migration 0008 is in use (a claim exists); not downgraded';
        END IF;
    END $$
"""


def downgrade() -> None:
    op.execute(IN_USE)
    op.drop_table('run_claim')
    for f in FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
