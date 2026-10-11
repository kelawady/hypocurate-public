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

# Step 8b: the regression suite makes no live model call (owner's standing requirement). For the whole test
# process, and every guarded child it starts (they copy this environment): no provider credential, and the
# provider's address is a closed local port, so a request without the stub's own address and key can never
# leave the machine. Tests that call an agent pass the stub's address (stub_provider.client_options).
NO_PROVIDER = "http://127.0.0.1:9"
for _name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
    os.environ.pop(_name, None)
os.environ["ANTHROPIC_API_BASE"] = NO_PROVIDER
os.environ["ANTHROPIC_BASE_URL"] = NO_PROVIDER

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


# Step 10a, a5 (owner, 2026-10-11): the suite runs in parallel with pytest-xdist (`-n 4 --dist loadgroup`, pyproject).
# Each test already has a database of its own (above): `migrated_database` and `empty_database` are new databases with
# random names, dropped after the test, and every xdist worker makes its own template (`template_database` is
# session-scoped, so once per worker process). Advisory locks are per database. The files below hold tests that
# measure time, race threads or processes, or send signals: they run one after another on a single worker
# (`xdist_group`, which never deselects a test). A test that fails even once in parallel and passes alone is added here
# (or the suite drops to 2 workers), never re-run: there is no rerun plugin or retry flag.
SERIAL_FILES = frozenset({
    "test_access_dispatch.py", "test_access_layer.py", "test_agent_core.py", "test_checkpoints.py",
    "test_cli_step9b.py", "test_concurrency.py", "test_confirmation.py", "test_guarded_parent.py",
    "test_kill_matrix.py", "test_login.py", "test_login_throttle.py", "test_migrations.py",
    "test_migrations_step9a.py", "test_queue.py", "test_source_versions.py", "test_web_state.py", "test_worker.py",
    "test_worker_fix1.py", "test_write_retry.py",
})
SERIAL_GROUP = "serial"


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.name in SERIAL_FILES:
            item.add_marker(pytest.mark.xdist_group(SERIAL_GROUP))
