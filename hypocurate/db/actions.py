"""Who did what (step 10b, fix round 1; migration 0009; owner, 2026-10-11).

`record` writes one `action_record` row on the caller's connection, so it commits or rolls back with the write it
records. The name is stored as given (trimmed): the website passes the signed-in name, which it requires; the command
line passes `--by` where given, and no name otherwise; code's own action (a narrower question) has none. Nothing
proves who typed a name (the step 10a sign-in). A record, not a gate: no rule reads it.
"""
from __future__ import annotations

from sqlalchemy import Connection, text

from hypocurate.db.models import ACTIONS, CHANNELS

WEBSITE, COMMAND_LINE, CODE = CHANNELS
ACTOR_MAX = 200


class UnnamedAction(ValueError):
    """An action on the website without the signed-in name, or a name longer than 200 characters."""


def actor(by: str | None, channel: str) -> str | None:
    """The name to store: trimmed; none for code's own action; required on the website."""
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}")
    name = by.strip() if isinstance(by, str) else ""
    if channel == CODE:
        return None
    if len(name) > ACTOR_MAX or (channel == WEBSITE and not name):
        raise UnnamedAction(f"an action on the website names the signed-in person (1 to {ACTOR_MAX} characters)")
    return name or None


def record(conn: Connection, action: str, by: str | None, channel: str, *, version: int | None = None,
           run: int | None = None, source_version: int | None = None) -> None:
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    conn.execute(text(
        "INSERT INTO action_record (action, channel, actor, hypothesis_version_id, run_id, source_version_id) "
        "VALUES (:a, :c, :n, :v, :r, :s)"),
        dict(a=action, c=channel, n=actor(by, channel), v=version, r=run, s=source_version))
