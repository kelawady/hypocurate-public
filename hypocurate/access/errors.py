"""The one error the access layer raises for a refused read (PRD 4)."""
from __future__ import annotations


class AccessDenied(Exception):
    """A role asked for a field it may not receive at the run's stage, or claimed a stage
    the run is not in. The refusal is already in the audit log when this is raised."""

    def __init__(self, role: str, stage: str, field: str, reason: str):
        self.role, self.stage, self.field, self.reason = role, stage, field, reason
        super().__init__(f"access denied: {role} at {stage} asked for {field!r}: {reason}")
