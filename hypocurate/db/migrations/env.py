"""Alembic environment. Online mode only, with the engine passed in by
`hypocurate.db.migrate`. The whole run is one transaction, and the advisory
lock is taken inside it before Alembic reads the current revision."""
from alembic import context
from sqlalchemy import text

from hypocurate.db.migrate import ADVISORY_LOCK_KEY
from hypocurate.db.models import Base

engine = context.config.attributes["engine"]

with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        transaction_per_migration=False,  # one transaction for the whole upgrade
    )
    with context.begin_transaction():
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ADVISORY_LOCK_KEY})
        context.run_migrations()
