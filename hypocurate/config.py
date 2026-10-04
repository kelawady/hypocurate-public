"""Settings from environment variables (PRD Section 6, "Login"; CLAUDE.md, "Secrets").

Secrets come only from the environment (`.env` locally, Render's environment
settings in production). Their values are never logged or shown; `Settings`
hides them from its repr.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

PRODUCTION = "production"
DEVELOPMENT = "development"
MIN_PASSWORD_LENGTH = 12
MIN_SESSION_SECRET_LENGTH = 32


class ConfigError(RuntimeError):
    """A required setting is missing or unsafe. The message names the setting, never its value."""


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str = field(repr=False)
    password: str = field(repr=False)
    session_secret: str = field(repr=False)
    version: str

    @property
    def production(self) -> bool:
        return self.env == PRODUCTION


def load_settings(environ: dict[str, str] | None = None, *, web: bool = True) -> Settings:
    """Read and check the settings.

    The database URL is always required. The login password and the session
    secret are required, and must be long enough, for the web service
    (`web=True`); the worker and the command line do not use them.
    """
    e = os.environ if environ is None else environ
    env = e.get("HYPOCURATE_ENV", DEVELOPMENT)
    if env not in (PRODUCTION, DEVELOPMENT):
        raise ConfigError(f"HYPOCURATE_ENV must be '{PRODUCTION}' or '{DEVELOPMENT}'")
    settings = Settings(
        env=env,
        database_url=e.get("DATABASE_URL", ""),
        password=e.get("HYPOCURATE_PASSWORD", ""),
        session_secret=e.get("SESSION_SECRET", ""),
        # Render sets RENDER_GIT_COMMIT; elsewhere the version is unknown.
        version=e.get("RENDER_GIT_COMMIT", "") or "unknown",
    )
    problems = []
    if not settings.database_url:
        problems.append("DATABASE_URL is not set")
    if web and len(settings.password) < MIN_PASSWORD_LENGTH:
        problems.append(f"HYPOCURATE_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters")
    if web and len(settings.session_secret) < MIN_SESSION_SECRET_LENGTH:
        problems.append(f"SESSION_SECRET must be at least {MIN_SESSION_SECRET_LENGTH} characters")
    if problems:
        raise ConfigError("; ".join(problems))
    return settings
