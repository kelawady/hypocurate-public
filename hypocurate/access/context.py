"""The access context: what one agent call may read, captured once (step 5 review, finding 2).

Immutable. Created only by the trusted dispatcher (`dispatch.bind`), which reads the role from
the run's recorded agent settings, the stage from the database, and checks a Curator's source
against the run's `run_source` rows. Every read of an access object uses this one context.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessContext:
    """A run context (run_id set), or, from step 8a, a registration context: no run, the Curator,
    stage 'registration', the sealed source version its invocation names; or, from the Sprint 2 pilot, a document
    context: no run, the Extractor, stage 'document', the parsed document its invocation names."""
    run_id: int | None
    role: str
    stage: str
    source_key: str | None = None
    agent_setting_id: int | None = None
    source_version_id: int | None = None
    invocation_id: int | None = None
    document_parse_id: int | None = None
