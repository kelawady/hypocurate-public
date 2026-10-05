"""Tag starting lists (build step 6; PRD 5.5; register entry 'tag_starting_lists').

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05

Data only: no schema change. Inserts the owner's starting values of the three fixed tag
lists as approved, so that every database has them before any run locks its three tags
(the same way 0001 seeds the domains).

- **Safe on a database that already has some of the values:** each row is inserted with
  `ON CONFLICT (kind, value) DO NOTHING`. A value that already exists keeps its row and its
  status (proposed, approved or rejected); it is not changed.
- **Works with the previous release's code:** step 5 code only reads approved tag values.
- **Downgrade does nothing** (owner, 2026-10-05): tag values can never be deleted (trigger
  `hc_tag_value_no_delete`), and a run may already have attached one. The rows stay; only
  the revision goes back to 0001. Going down to base removes them with the whole table
  (0001's downgrade).

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

# The owner's starting lists (register entry 'tag_starting_lists', 2026-10-05), written out
# here so that this migration stays as it was when it was written.
TAG_STARTING_LISTS = {
    "property": ("yield strength", "ultimate tensile strength", "hardness", "elongation", "fatigue life"),
    "alloy_class": ("multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy", "titanium alloy",
                    "nickel alloy", "copper alloy", "magnesium alloy", "other"),
    "test_condition": ("room-temperature tension", "room-temperature compression", "elevated temperature",
                       "cryogenic", "hardness test", "fatigue"),
}


def upgrade() -> None:
    insert = sa.text("INSERT INTO tag_value (kind, value, status, decided_at) "
                     "VALUES (:kind, :value, 'approved', now()) ON CONFLICT (kind, value) DO NOTHING")
    for kind, values in TAG_STARTING_LISTS.items():
        for value in values:
            op.execute(insert.bindparams(kind=kind, value=value))


def downgrade() -> None:
    """Data-only revision: the rows stay (see the module docstring)."""
