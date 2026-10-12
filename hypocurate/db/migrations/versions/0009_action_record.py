"""Who did what: one row per person's action (build step 10b, fix round 1).

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-11

Approved by the owner on 2026-10-11 ("New table action_record, migration 0009, as you recommend. Also write a row
for confirm and cancel, which already store the name elsewhere, so that 'who did what' is complete in one place;
keep their existing records unchanged"), after ChatGPT's review of step 10b (finding 3), subject to the second-model
re-check before merging. 0001 to 0008 untouched: no earlier function is replaced.

action_record, append-only (never updated, deleted or truncated):
- the action, from a fixed list (`ACTIONS`); where it was done (`CHANNELS`: the website, the command line, or code);
- the actor's name as given (1-200 characters, trimmed), required for an action on the website (the signed-in name);
  absent when none was given at the command line, and for code's own action (a narrower question code creates);
- what it acted on: the query version, the run and/or the source version, as the action requires (`TARGETS`);
- the time, the database's (set by the insert trigger, whatever the insert says).
It is written in the same transaction as the write it records (pipeline/queries.py, pipeline/confirmation.py,
sources/versions.py). It is a record, not a gate: no other table's rule reads it.

Works with the previous release's code: it never reads or writes action_record.

Downgrade locks the table (ACCESS EXCLUSIVE) and refuses while any row exists (the rows are history), then drops what 0009 added;
the lock comes first, so an insert not yet committed is waited for and counted.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it keeps
working with the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None

# Copied here so the migration does not change when the code does (tests check they equal the code's lists).
ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
           "cancel", "confirm_rules", "register_source")
CHANNELS = ("website", "command line", "code")
ACTOR_MAX = 200
# What each action names: v = the query version, r = the run, s = the source version.
TARGETS = {"create": "v", "edit": "v", "new_version": "v", "submit": "v", "return": "v", "confirm_domain": "v",
           "dispatch": "vr", "dispatch_again": "vr", "cancel": "r", "confirm_rules": "r", "register_source": "s"}
COLUMNS = {"v": "hypothesis_version_id", "r": "run_id", "s": "source_version_id"}


def _in(column: str, values) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def targets_check() -> str:
    """Each action names exactly what it acts on, and nothing else."""
    cases = []
    for action, kinds in TARGETS.items():
        parts = [f"{col} IS {'NOT ' if k in kinds else ''}NULL" for k, col in COLUMNS.items()]
        cases.append(f"(action = '{action}' AND " + " AND ".join(parts) + ")")
    return " OR ".join(cases)


FUNCTIONS = [
    # The database's time, whatever the insert says.
    """
    CREATE FUNCTION hc_action_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.at := now();
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_action_record_insert()"]

APPEND_ONLY = ["action_record"]
CHECKED = [("action_record", "INSERT", "hc_action_record_insert", "hc_action_record_insert")]
TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
       for table, event, t, f in CHECKED]
)


def upgrade() -> None:
    op.create_table(
        'action_record',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=True),
        sa.Column('run_id', sa.BigInteger(), nullable=True),
        sa.Column('source_version_id', sa.BigInteger(), nullable=True),
        sa.CheckConstraint(_in('action', ACTIONS), name=op.f('ck_action_record_action')),
        sa.CheckConstraint(_in('channel', CHANNELS), name=op.f('ck_action_record_channel')),
        sa.CheckConstraint(f"actor IS NULL OR (actor = btrim(actor) AND length(actor) BETWEEN 1 AND {ACTOR_MAX})",
                           name=op.f('ck_action_record_actor')),
        sa.CheckConstraint("channel <> 'website' OR actor IS NOT NULL", name=op.f('ck_action_record_website_named')),
        sa.CheckConstraint("channel <> 'code' OR actor IS NULL", name=op.f('ck_action_record_code_unnamed')),
        sa.CheckConstraint(targets_check(), name=op.f('ck_action_record_targets')),
        sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'],
                                name=op.f('fk_action_record_hypothesis_version_id')),
        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_action_record_run_id')),
        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
                                name=op.f('fk_action_record_source_version_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_action_record')),
    )
    op.create_index('ix_action_record_hypothesis_version_id', 'action_record', ['hypothesis_version_id'])
    op.create_index('ix_action_record_run_id', 'action_record', ['run_id'])
    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)


# Re-check item 1 (ChatGPT; the owner, 2026-10-12): the table is locked before it is looked at, in the downgrade's
# own transaction, so an action inserted but not yet committed is waited for and seen, never dropped unseen.
LOCK = "LOCK TABLE action_record IN ACCESS EXCLUSIVE MODE"
IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM action_record) THEN
            RAISE EXCEPTION 'hypocurate: migration 0009 is in use (an action is recorded); not downgraded';
        END IF;
    END $$
"""


def downgrade() -> None:
    op.execute(LOCK)
    op.execute(IN_USE)
    op.drop_table('action_record')
    for f in FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
