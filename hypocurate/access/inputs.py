"""A role's complete input at its stage, as data (PRD 4, testing requirement).

`role_input(access)` reads every field on the role's list in one transaction under the run's
lock: one snapshot of the run data protected by the run-lock protocol.
It never returns an empty input: a role with no field at its stage gets AccessDenied
(logged). The agents (step 8) build their prompts from this and answer their tool calls
through the same access object. This is the **projected data** a role receives; the actual
outbound model request (instructions, message history, tool errors, retry prompts) is a step 8
acceptance requirement to test.
"""
from __future__ import annotations

from typing import Any

from hypocurate.access.layer import Access


def role_input(access: Access) -> dict[str, Any]:
    return access.read_all()
