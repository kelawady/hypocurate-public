"""The data-access layer: role and stage objects, the audit log, AccessDenied (step 5).

- `allowlist`: the allowed fields per role and stage (the access contract, PRD 4);
- `layer.Access`: the access object every agent read goes through; logs every read;
- `inputs.role_input`: a role's complete input at its stage;
- `file_guard` and `guarded`: the approved input files of pipeline code, enforced in the
  process that runs a pipeline.
"""
from hypocurate.access.errors import AccessDenied
from hypocurate.access.inputs import role_input
from hypocurate.access.layer import Access

__all__ = ["Access", "AccessDenied", "role_input"]
