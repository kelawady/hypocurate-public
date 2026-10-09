"""The database engine. Login uses a signed cookie, not a table; the health page asks
whether the database answers. The tables (step 3) are in `models.py` and are created
only by the migrations (`migrate.py`)."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

SESSION_TIME_ZONE = "UTC"  # register 'database_session_time_zone'


# Step 9b fix round 1 (owner, 2026-10-09): a worker's and its child's sessions check every second whether their client
# is still there (so PostgreSQL abandons a query of a process that died) and keep TCP alive, so a lost connection is
# noticed (the server side's keepalives; the client's below).
WORKER_SESSION = {"client_connection_check_interval": "1s", "tcp_keepalives_idle": "30",
                  "tcp_keepalives_interval": "10", "tcp_keepalives_count": "3"}


def make_engine(database_url: str, *, worker_session: bool = False) -> Engine:
    # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    # The session's time zone is UTC by name (step 8a review; owner, 2026-10-07): the driver then
    # interprets timestamps without reading a zone file, which the file guard would refuse (a server
    # zone such as 'Etc/UTC' makes it open /usr/share/zoneinfo). Every query states its zone where it
    # matters ('AT TIME ZONE ...'), and the servers used so far run in UTC already.
    options = f"-c TimeZone={SESSION_TIME_ZONE}"
    connect_args: dict = {"connect_timeout": 3}
    if worker_session:
        options += "".join(f" -c {k}={v}" for k, v in WORKER_SESSION.items())
        connect_args.update(keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
    return create_engine(database_url, pool_pre_ping=True, connect_args={**connect_args, "options": options})


def database_reachable(engine: Engine) -> bool:
    """True if the database answers `SELECT 1`. Never raises."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
