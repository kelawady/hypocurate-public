"""The database engine. Step 2 creates no tables: login uses a signed cookie and
the health page only asks whether the database answers."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text


def make_engine(database_url: str) -> Engine:
    # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def database_reachable(engine: Engine) -> bool:
    """True if the database answers `SELECT 1`. Never raises."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
