"""The data-access layer: role and stage objects, the audit log, AccessDenied (step 5).

- `allowlist`: the allowed fields per role and stage (the access contract, PRD 4), the
  threat model, the plan schema and the accepted disclosures;
- `vocabulary`: the controlled vocabularies of the blinded views;
- `dispatch.bind`: the only way to obtain an access object, for one agent call;
- `layer.Access`: the access object every agent read goes through; logs every read,
  denial and failure;
- `inputs.role_input`: a role's projected input at its stage, in one transaction under the
  run's lock;
- `file_guard` and `guarded`: a tripwire against accidental file access by pipeline code
  (not a sandbox).
"""
from hypocurate.access.dispatch import bind, bind_invocation
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.inputs import role_input
from hypocurate.access.layer import Access

__all__ = ["Access", "AccessDenied", "AccessFailed", "bind", "bind_invocation", "role_input"]
