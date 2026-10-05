"""Test-only construction of access objects (step 5 review, finding 2).

Outside the tests, an access object comes only from the trusted dispatcher
(`hypocurate.access.dispatch.bind`), which reads the role from the run's recorded agent
settings and the stage from the database. The tests also need contexts the dispatcher would
never produce (an unknown role, a stale or wrong stage, a source the run did not record), to
show that every read still refuses them. They use this helper, which no package code imports.
"""
from hypocurate.access.context import AccessContext
from hypocurate.access.layer import _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, Access


def access_for(engine, run_id, role, stage, source_key=None, lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
    return Access(engine, AccessContext(run_id, role, stage, source_key), lock_timeout_ms=lock_timeout_ms,
                  _trusted=_TRUSTED)
