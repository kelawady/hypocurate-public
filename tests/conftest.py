"""Shared fixtures. Tests that need PostgreSQL fail, never skip, when it is not reachable.

Step 3: tests that need tables never touch the database at DATABASE_URL. Each gets
its own scratch database, dropped afterwards:
- `empty_database`: a new, empty database (the migration tests start here);
- `migrated_database`: a copy of a template database migrated once per session
  (owner's addition 4, for speed). The template itself is migrated from empty.
"""
import os
import uuid

import pytest
from sqlalchemy import make_url, text

from hypocurate.db import migrate
from hypocurate.db.engine import database_reachable, make_engine

HOW_TO = (
    "This test needs PostgreSQL. Run the suite with `docker compose run --rm test`, "
    "or start the database with `docker compose up -d db` and set DATABASE_URL "
    "(see README)."
)


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.fail("DATABASE_URL is not set. " + HOW_TO)
    if not database_reachable(make_engine(url)):
        pytest.fail("The database at DATABASE_URL does not answer. " + HOW_TO)
    return url


def url_for(database_url: str, name: str) -> str:
    return make_url(database_url).set(database=name).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def admin(database_url):
    """Creates and drops scratch databases. Never used for anything else."""
    engine = make_engine(database_url).execution_options(isolation_level="AUTOCOMMIT")
    yield engine
    engine.dispose()


def _create(admin, prefix: str, template: str | None = None) -> str:
    name = f"{prefix}_{uuid.uuid4().hex[:12]}"
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"' + (f' TEMPLATE "{template}"' if template else "")))
    return name


def _drop(admin, name: str) -> None:
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


@pytest.fixture
def empty_database(admin, database_url):
    name = _create(admin, "hypocurate_t")
    yield url_for(database_url, name)
    _drop(admin, name)


@pytest.fixture(scope="session")
def template_database(admin, database_url):
    name = _create(admin, "hypocurate_tmpl")
    engine = make_engine(url_for(database_url, name))
    migrate.upgrade(engine)
    engine.dispose()  # a template must have no open connections
    yield name
    _drop(admin, name)


@pytest.fixture
def migrated_database(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    yield url_for(database_url, name)
    _drop(admin, name)


@pytest.fixture
def db(migrated_database):
    """An engine on a freshly migrated scratch database."""
    engine = make_engine(migrated_database)
    yield engine
    engine.dispose()
