"""A role's complete input at its stage (PRD 4, testing requirement).

`role_input` reads every field on the role's list through the role's access object; it is
everything that role can receive at that stage. The agents (step 8) build their prompts
and answer their tool calls from this and from the same access object only, so the access
tests on this input cover what an agent sees. Fields take no parameters, so the complete
input is one read of each listed field.
"""
from __future__ import annotations

from typing import Any

from hypocurate.access.allowlist import allowed
from hypocurate.access.layer import Access


def role_input(access: Access) -> dict[str, Any]:
    """Every field `access.role` may receive at `access.stage`, read through `access`.
    Raises AccessDenied (logged) if the run is not at that stage."""
    return {field: access.get(field) for field in sorted(allowed(access.role, access.stage))}
