"""The database engine. Login uses a signed cookie, not a table; the health page asks
whether the database answers. The tables (step 3) are in `models.py` and are created
only by the migrations (`migrate.py`)."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

SESSION_TIME_ZONE = "UTC"  # register 'database_session_time_zone'


def make_engine(database_url: str) -> Engine:
    # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    # The session's time zone is UTC by name (step 8a review; owner, 2026-10-07): the driver then
    # interprets timestamps without reading a zone file, which the file guard would refuse (a server
    # zone such as 'Etc/UTC' makes it open /usr/share/zoneinfo). Every query states its zone where it
    # matters ('AT TIME ZONE ...'), and the servers used so far run in UTC already.
    return create_engine(database_url, pool_pre_ping=True,
                         connect_args={"connect_timeout": 3, "options": f"-c TimeZone={SESSION_TIME_ZONE}"})


def database_reachable(engine: Engine) -> bool:
    """True if the database answers `SELECT 1`. Never raises."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
