"""The signed-in person's name and the protection of actions that write (step 10a; owner's answer 1 and additions 1
and 3 of 2026-10-11; register 'signed_in_name', 'csrf_tokens').

**The name.** The sign-in form takes the shared password and the person's name (1 to `NAME_MAX` characters). The name
is kept in the signed session cookie for the session's life and is the `by` of every action that names a person
(confirm, cancel; dispatch and domain confirmation in 10b). It cannot change within a session: signing in again while
signed in is refused, so a new name means signing out and in again. Nothing proves who typed the name; it records who
said they acted, under the shared password, as `--by` does on the command line.

**The CSRF token.** A random token (`secrets.token_urlsafe`) is made at sign-in and kept in the same signed cookie.
Every form that writes carries it in a hidden field, and every write checks it (`check_csrf`, constant-time compare)
before anything is done; a request without the session's token is refused with 403 and writes nothing. Sign-out writes
nothing and carries no token. The cookie is SameSite=Lax as well (app.py).
"""
from __future__ import annotations

import hmac
import secrets

from fastapi import HTTPException, Request

from hypocurate.db.models import CONFIRMED_BY_MAX

NAME_MAX = CONFIRMED_BY_MAX  # the confirmation's own limit (migration 0007), so every recorded name fits
CSRF_FIELD = "csrf_token"
CSRF_REFUSED = "This form has expired or did not come from this site. Reload the page and try again."


class NameRefused(ValueError):
    pass


def clean_name(value: str | None) -> str:
    name = " ".join((value or "").split())
    if not 1 <= len(name) <= NAME_MAX:
        raise NameRefused(f"Give your name (1 to {NAME_MAX} characters).")
    return name


def start_session(request: Request, name: str) -> None:
    request.session.clear()
    request.session.update({"signed_in": True, "name": name, "csrf": secrets.token_urlsafe(32)})


def signed_in_name(request: Request) -> str:
    """The name given at sign-in. A session without one (signed in before step 10a) cannot act; it must sign in
    again."""
    name = request.session.get("name")
    if not isinstance(name, str) or not name:
        raise HTTPException(status_code=403, detail="Sign out and sign in again with your name.")
    return name


def csrf_token(request: Request) -> str:
    return request.session.get("csrf") or ""


def check_csrf(request: Request, token: str | None) -> None:
    expected = request.session.get("csrf")
    if not isinstance(expected, str) or not expected or not isinstance(token, str) \
            or not hmac.compare_digest(expected.encode(), token.encode()):
        raise HTTPException(status_code=403, detail=CSRF_REFUSED)
