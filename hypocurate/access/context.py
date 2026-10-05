"""The access context: what one agent call may read, captured once (step 5 review, finding 2).

Immutable. Created only by the trusted dispatcher (`dispatch.bind`), which reads the role from
the run's recorded agent settings, the stage from the database, and checks a Curator's source
against the run's `run_source` rows. Every read of an access object uses this one context.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessContext:
    run_id: int
    role: str
    stage: str
    source_key: str | None = None
    agent_setting_id: int | None = None
