"""Shared fixtures. Tests that need PostgreSQL fail, never skip, when it is not reachable."""
import os

import pytest

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
