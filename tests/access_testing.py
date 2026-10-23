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


def registration_access_for(engine, invocation_id, source_version_id, role="curator", stage="registration",
                            source_key=None, lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
    """A registration context (step 8a) the dispatcher would or would not produce."""
    return Access(engine, AccessContext(None, role, stage, source_key, None, source_version_id=source_version_id,
                                        invocation_id=invocation_id), lock_timeout_ms=lock_timeout_ms,
                  _trusted=_TRUSTED)


def document_access_for(engine, invocation_id, document_parse_id, role="extractor", stage="document",
                        lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
    """A document context (Sprint 2 pilot) the dispatcher would or would not produce."""
    return Access(engine, AccessContext(None, role, stage, None, None, invocation_id=invocation_id,
                                        document_parse_id=document_parse_id), lock_timeout_ms=lock_timeout_ms,
                  _trusted=_TRUSTED)
