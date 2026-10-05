"""How each record was extracted (build step 6; register entry 'record_extraction_provenance').

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-05

Additive. Each stored record states how it was extracted: by adapter code (with the
adapter's name and version) or, from step 8, by an agent, so that records extracted by code
can always be told apart from records an agent extracts later (owner, 2026-10-05).

- A new nullable column `record.extraction` (JSONB) with a CHECK on its shape: an object
  whose `method`, `name` and `version` are present JSON strings, `method` 'adapter' or 'agent',
  `name` and `version` non-empty; the check is made explicitly true or false. Existing
  rows keep NULL (the live database has none; every record before this step was a test row).
- `hc_record_insert` is replaced: **every check of 0001 is kept unchanged, in the same
  order**, and one is added at the end: a new record must carry `extraction`.
- 0001 and 0002 are untouched.
- **Works with the previous release's code:** that code inserts no records outside tests.
- **Downgrade** restores 0001's `hc_record_insert` exactly and drops the column; the
  extraction values stored in it are lost.

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

# Every key present and a JSON string, and the whole condition true: a missing key or a JSON null
# gives SQL NULL inside, which coalesce turns into false, so it cannot pass as an unknown result
# (step 6 review, finding 6; changed in place before 0003 ran on the live database).
SHAPE = ("extraction IS NULL OR coalesce(jsonb_typeof(extraction) = 'object' "
         "AND jsonb_typeof(extraction->'method') = 'string' AND jsonb_typeof(extraction->'name') = 'string' "
         "AND jsonb_typeof(extraction->'version') = 'string' "
         "AND (extraction->>'method') IN ('adapter', 'agent') "
         "AND length(extraction->>'name') > 0 AND length(extraction->>'version') > 0, false)")

# 0001's function, verbatim (restored by the downgrade).
RECORD_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        RETURN NEW;
    END $$
    """

# The same checks, then the new requirement.
RECORD_INSERT_0003 = """
    CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        IF NEW.extraction IS NULL THEN
            PERFORM hc_reject('a record states how it was extracted (adapter or agent, with name and version)');
        END IF;
        RETURN NEW;
    END $$
    """


def upgrade() -> None:
    op.add_column('record', sa.Column('extraction', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_check_constraint(op.f('ck_record_extraction_shape'), 'record', SHAPE)
    op.execute(RECORD_INSERT_0003)


def downgrade() -> None:
    op.execute(RECORD_INSERT_0001)
    op.drop_constraint(op.f('ck_record_extraction_shape'), 'record', type_='check')
    op.drop_column('record', 'extraction')
