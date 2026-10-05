"""The web service (PRD Section 6): login, health page, a placeholder home page, and the
read-only assumptions register (step 4b, /assumptions).

Every page needs the shared login except exactly /login and /health, and the
files under /static/. The session is a signed cookie (Starlette
SessionMiddleware, itsdangerous) holding only {"signed_in": true}; in
production it is sent over HTTPS only. There is no server-side session record:
rotating SESSION_SECRET ends every session (README, "Sessions").
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate import assumptions
from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.db.migrate import schema_status
from hypocurate.web.login_throttle import Attempt, LoginThrottle

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
STATIC_PREFIX = "/static/"

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_throttle: LoginThrottle | None = None,
    register: list[dict] | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    throttle = login_throttle or LoginThrottle()
    # Read and validated once at start: an invalid register stops the service starting.
    if register is None:
        register = assumptions.load_register()
    else:
        assumptions.validate(register)

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        public = path in PUBLIC_PATHS or path.startswith(STATIC_PREFIX)
        if not public and not request.session.get("signed_in"):
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)

    # Added after require_login so that it runs first and the session is available.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=SESSION_COOKIE,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.production,
    )
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html", {})

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form("")) -> Response:
        result = throttle.attempt(password, settings.password)
        if result is Attempt.OK:
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        if result is Attempt.THROTTLED:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password."}, status_code=401
        )

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/assumptions", response_class=HTMLResponse)
    def assumptions_page(request: Request, review: str | None = None):
        """Read-only: generated from hypocurate/assumptions.json; nothing is edited here."""
        not_reviewed_only = review == "not_reviewed"
        return templates.TemplateResponse(request, "assumptions.html", {
            "sections": assumptions.page_sections(register, not_reviewed_only=not_reviewed_only),
            "counts": assumptions.summary_counts(register),
            "not_reviewed_only": not_reviewed_only,
            "categories": assumptions.CATEGORIES,
            "review_labels": assumptions.REVIEW_STATUSES,
        })

    @app.get("/health")
    def health(request: Request) -> Response:
        db_ok = database_reachable(engine)
        status = {"web": "ok", "database": "ok" if db_ok else "unreachable", "version": settings.version,
                  # Informational (step 3): confirms a deploy migrated; never changes the status code.
                  "schema": schema_status(engine) if db_ok else {"revision": None, "at_head": False}}
        code = 200 if db_ok else 503
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(request, "health.html", {"status": status}, status_code=code)
        return JSONResponse(status, status_code=code)

    return app
