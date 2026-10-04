"""The web service (PRD Section 6): login, health page, and a placeholder home page.

Every page needs the shared login except /login, /health and /static. The
session is a signed cookie (Starlette SessionMiddleware, itsdangerous); in
production it is sent over HTTPS only.
"""
from __future__ import annotations

import hmac
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.web.login_limit import LoginLimit

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PREFIXES = ("/login", "/health", "/static/")

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_limit: LoginLimit | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    limit = login_limit or LoginLimit()

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        if not path.startswith(PUBLIC_PREFIXES) and not request.session.get("signed_in"):
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
        if limit.seconds_locked() > 0:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
        if hmac.compare_digest(password.encode(), settings.password.encode()):
            limit.record_success()
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        limit.record_failure()
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password."}, status_code=401
        )

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/health")
    def health(request: Request) -> Response:
        db_ok = database_reachable(engine)
        status = {"web": "ok", "database": "ok" if db_ok else "unreachable", "version": settings.version}
        code = 200 if db_ok else 503
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(request, "health.html", {"status": status}, status_code=code)
        return JSONResponse(status, status_code=code)

    return app
