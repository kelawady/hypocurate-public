"""The errors of the access layer (PRD 4).

`AccessDenied`: a policy refusal (the field is not on the role's list at the run's stage, the
stage has changed, the source is not the run's). `AccessFailed`: the read could not be done
(unknown run, lock timeout, a reader's error, the database unavailable). Both are logged
before they are raised (`layer.py`); their messages hold only validated, bounded strings.
"""
from __future__ import annotations


class AccessDenied(Exception):
    """A policy refusal, already in the audit log (or the process log) when raised."""

    def __init__(self, role: str, stage: str, field: str, code: str, reason: str):
        self.role, self.stage, self.field, self.code, self.reason = role, stage, field, code, reason
        super().__init__(f"access denied: {role} at {stage} asked for {field}: {reason}")


class AccessFailed(Exception):
    """An access failure, already in the audit log (or the process log) when raised."""

    def __init__(self, role: str, stage: str, field: str, code: str):
        self.role, self.stage, self.field, self.code = role, stage, field, code
        super().__init__(f"access failed: {role} at {stage} asking for {field}: {code}")
