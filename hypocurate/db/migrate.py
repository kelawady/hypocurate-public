"""Database migrations (build step 3). Run as:

    python -m hypocurate.db.migrate upgrade              # to head; Render's pre-deploy command
    python -m hypocurate.db.migrate current
    python -m hypocurate.db.migrate downgrade <revision> [--confirm-data-loss]

How it behaves, and only this:
- The whole upgrade runs in one transaction (PostgreSQL has transactional DDL).
  If any statement fails, nothing is applied: no table and no change to
  `alembic_version`. The command exits non-zero, so Render fails the deploy and
  keeps the previous version running.
- `env.py` takes a transaction-level advisory lock before reading the current
  revision, so two upgrades started together (web and worker deploying the same
  commit) run one after the other; the second finds the database at head.
- A downgrade drops tables and their data. In production it refuses unless
  `--confirm-data-loss` is given.

The Alembic configuration is built here, not read from an `alembic.ini`, so the
deployed image holds only `hypocurate/`, `data/` and `requirements.lock`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine

from hypocurate.config import load_settings
from hypocurate.db.engine import make_engine

MIGRATIONS = Path(__file__).parent / "migrations"
# Any fixed number; shared by every process that migrates this database.
ADVISORY_LOCK_KEY = 0x48594343  # "HYCC"


def alembic_config(engine: Engine) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    # Passed as an object, never as a URL string: the URL holds the password, and
    # Alembic's config file syntax would also misread a '%' in it.
    cfg.attributes["engine"] = engine
    return cfg


def head_revision() -> str:
    heads = ScriptDirectory(str(MIGRATIONS)).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"expected exactly one migration head, found {len(heads)}")
    return heads[0]


def current_revision(engine: Engine) -> str | None:
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def schema_status(engine: Engine) -> dict:
    """For /health: the database's revision and whether it is the code's head. Never raises."""
    try:
        revision = current_revision(engine)
    except Exception:
        return {"revision": None, "at_head": False}
    return {"revision": revision, "at_head": revision == head_revision()}


def upgrade(engine: Engine, revision: str = "head") -> None:
    command.upgrade(alembic_config(engine), revision)


def downgrade(engine: Engine, revision: str) -> None:
    command.downgrade(alembic_config(engine), revision)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m hypocurate.db.migrate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("upgrade", help="migrate to the latest revision (one transaction)")
    sub.add_parser("current", help="print the database's revision")
    down = sub.add_parser("downgrade", help="migrate down to a revision; drops tables and their data")
    down.add_argument("revision", help="target revision, or 'base' for an empty schema")
    down.add_argument("--confirm-data-loss", action="store_true",
                      help="required in production: the downgrade deletes data")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    engine = make_engine(settings.database_url)
    if args.command == "upgrade":
        upgrade(engine)
        print(f"schema at {current_revision(engine)}")
    elif args.command == "current":
        print(current_revision(engine) or "empty (no revision)")
    else:
        if settings.production and not args.confirm_data_loss:
            print("refused: a downgrade drops tables and their data. In production, add "
                  "--confirm-data-loss after taking a backup (README, 'Database migrations').",
                  file=sys.stderr)
            return 2
        downgrade(engine, args.revision)
        print(f"schema at {current_revision(engine) or 'empty (no revision)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
