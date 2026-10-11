"""The web service (PRD Section 6): login, health page, the read-only assumptions register (step 4b, /assumptions),
and from step 10a the run pages: the runs list, the run viewer, the confirmation of the question as tested, and cancel.

Every page needs the shared login except exactly /login and /health, and the
files under /static/. The session is a signed cookie (Starlette
SessionMiddleware, itsdangerous) holding {"signed_in": true, "name": ..., "csrf": ...}
(step 10a: the name given at sign-in and the token every write carries; `web/security.py`); in
production it is sent over HTTPS only. There is no server-side session record:
rotating SESSION_SECRET ends every session (README, "Sessions").

The web service never calls a model, never claims a run and never runs a pipeline stage (step 10 brief). It reads
through `pipeline.run_view` and writes only through the pipeline's own functions: `confirmation.confirm` and
`queries.cancel` in 10a. A confirmed run is taken up by the worker; closing the browser or restarting this service
never affects a run (criterion 14.4).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate import assumptions
from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.db.migrate import schema_status
from hypocurate.web import dial, glossary, security, textfmt
from hypocurate.web.login_throttle import Attempt, LoginThrottle

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
STATIC_PREFIX = "/static/"
# What the run page says after an action: fixed words, chosen by a fixed key (never text from the address).
DONE = {"confirmed": "Confirmed under your name. The run waits for a worker to take it up; this page updates by itself.",
        "cancelled": "Cancelled under your name."}
ALREADY_SIGNED_IN = "You are signed in as {name}. To act under another name, sign out first, then sign in again."

templates = Jinja2Templates(directory=HERE / "templates")


def _info(key: str) -> Markup:
    """An information button (PRD 9.7) with the glossary's text; opens on hover, focus and click, closes on Escape
    or when focus leaves (static/info.js)."""
    e = glossary.entry(key)
    tip = f"tip-{key}"
    return Markup(
        f'<span class="info"><button type="button" class="info-button" aria-label="Explain: {Markup.escape(e["term"])}"'
        f' aria-describedby="{tip}" aria-expanded="false">i</button>'
        f'<span class="info-text" role="tooltip" id="{tip}" hidden>{Markup.escape(e["text"])}</span></span>')


templates.env.globals.update(info=_info, dial=dial.svg)
templates.env.filters.update(units=textfmt.units, model_text=textfmt.model_text)


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
    glossary.entries()  # likewise the glossary

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

    def page(request: Request, name: str, context: dict, status_code: int = 200, spending: bool = True):
        """A signed-in page: the menu with the signed-in name, the session's form token, and the spending panel (on
        the pages that read the database; the home and assumptions pages do not)."""
        from hypocurate.pipeline import run_view
        return templates.TemplateResponse(request, name, {
            **context, "signed_in_as": request.session.get("name") or "", "csrf_token": security.csrf_token(request),
            "csrf_field": security.CSRF_FIELD, "spending": run_view.spending(engine) if spending else None},
            status_code=status_code)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return page(request, "home.html", {}, spending=False)

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {
            "error": None, "current_name": (request.session.get("name") or "a session without a name") if request.session.get("signed_in") else None,
            "name_max": security.NAME_MAX})

    @app.post("/login")
    def login(request: Request, password: str = Form(""), name: str = Form("")) -> Response:
        if request.session.get("signed_in"):  # owner's addition 3: the name cannot change within a session
            current = request.session.get("name") or "a session without a name"
            return templates.TemplateResponse(
                request, "login.html", {"error": ALREADY_SIGNED_IN.format(name=current),
                                        "current_name": current, "name_max": security.NAME_MAX}, status_code=409)
        result = throttle.attempt(password, settings.password)
        if result is Attempt.OK:
            try:
                clean = security.clean_name(name)
            except security.NameRefused as refused:
                return templates.TemplateResponse(request, "login.html", {
                    "error": str(refused), "current_name": None, "name_max": security.NAME_MAX}, status_code=400)
            security.start_session(request, clean)
            return RedirectResponse("/", status_code=303)
        if result is Attempt.THROTTLED:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes.", "current_name": None,
                 "name_max": security.NAME_MAX},
                status_code=429,
            )
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password.", "current_name": None, "name_max": security.NAME_MAX},
            status_code=401)

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/assumptions", response_class=HTMLResponse)
    def assumptions_page(request: Request, review: str | None = None):
        """Read-only: generated from hypocurate/assumptions.json; nothing is edited here."""
        not_reviewed_only = review == "not_reviewed"
        return page(request, "assumptions.html", {
            "sections": assumptions.page_sections(register, not_reviewed_only=not_reviewed_only),
            "counts": assumptions.summary_counts(register),
            "not_reviewed_only": not_reviewed_only,
            "categories": assumptions.CATEGORIES,
            "review_labels": assumptions.REVIEW_STATUSES,
        }, spending=False)

    # --- the run pages (step 10a) ---------------------------------------------------------------------------------

    @app.get("/runs", response_class=HTMLResponse)
    def runs(request: Request, before: int | None = Query(None)):
        from hypocurate.pipeline import run_view
        try:
            listed = run_view.runs_list(engine, before)
        except run_view.NoSuchPage as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        return page(request, "runs.html", {"listed": listed, "runs": listed["runs"]})

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run(request: Request, run_id: int):
        from hypocurate.pipeline import run_view
        shown = run_view.run_page(engine, run_id)
        if shown is None:
            raise HTTPException(status_code=404, detail=f"no run {run_id}")
        figure = None
        if shown["status"] == "completed":  # step 10b: the plot, built on request from stored rows
            from hypocurate.pipeline import plot
            d = plot.data(engine, run_id)
            figure = {**d, "svg": plot.svg(d) if d.get("plot") else None,
                      "legend": plot.legend(d) if d.get("plot") else []}
        return page(request, "run.html", {"r": shown, "plot": figure,
                                          "message": DONE.get(request.query_params.get("done", ""))})

    @app.get("/runs/{run_id}/state", response_class=HTMLResponse)
    def run_state(request: Request, run_id: int):
        """The run's state alone, which static/poll.js asks for while the run is open. Read-only, like every page."""
        from hypocurate.pipeline import run_view
        shown = run_view.run_page(engine, run_id)
        if shown is None:
            raise HTTPException(status_code=404, detail=f"no run {run_id}")
        return templates.TemplateResponse(request, "_state.html", {
            "r": shown, "csrf_token": security.csrf_token(request), "csrf_field": security.CSRF_FIELD},
            headers={"Cache-Control": "no-store"})

    @app.get("/runs/{run_id}/confirm", response_class=HTMLResponse)
    def confirm_form(request: Request, run_id: int):
        from hypocurate.pipeline import run_view
        shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
        if shown is None:
            raise HTTPException(status_code=404, detail=f"no run {run_id}")
        return page(request, "confirm.html", {"r": shown, "error": None})

    @app.post("/runs/{run_id}/confirm")
    def confirm(request: Request, run_id: int, csrf_token: str = Form(""), shown_fingerprint: str = Form("")):
        from hypocurate.pipeline import confirmation, queries, run_view
        security.check_csrf(request, csrf_token)
        name = security.signed_in_name(request)
        if run_view.run_page(engine, run_id) is None:
            raise HTTPException(status_code=404, detail=f"no run {run_id}")
        try:
            if not shown_fingerprint:
                raise queries.QueryRefused("content_changed", "the page sent no fingerprint of what it showed; show "
                                                              "it again before confirming")
            confirmation.confirm(engine, run_id, name, shown_fingerprint=shown_fingerprint)
        except queries.QueryRefused as refused:
            shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
            if shown is None:
                raise HTTPException(status_code=404, detail=f"no run {run_id}") from None
            return page(request, "confirm.html", {"r": shown, "error": f"Not confirmed: {refused.reason}"},
                        status_code=409)
        return RedirectResponse(f"/runs/{run_id}?done=confirmed", status_code=303)

    @app.post("/runs/{run_id}/cancel")
    def cancel(request: Request, run_id: int, csrf_token: str = Form("")):
        from hypocurate.pipeline import queries, run_view
        security.check_csrf(request, csrf_token)
        name = security.signed_in_name(request)
        if run_view.run_page(engine, run_id) is None:
            raise HTTPException(status_code=404, detail=f"no run {run_id}")
        try:
            queries.cancel(engine, run_id, by=name)
        except queries.QueryRefused as refused:
            shown = run_view.run_page(engine, run_id)
            if shown is None:
                raise HTTPException(status_code=404, detail=f"no run {run_id}") from None
            return page(request, "run.html", {"r": shown, "message": None, "error": f"Not cancelled: {refused.reason}"},
                        status_code=409)
        return RedirectResponse(f"/runs/{run_id}?done=cancelled", status_code=303)

    # --- the query pages (step 10b; PRD 9.1 to 9.3) ----------------------------------------------------------------

    def refused_words(error: Exception) -> str:
        """A refusal in code's fixed words: a query refusal's reason, or the database's own fixed message."""
        from sqlalchemy.exc import IntegrityError
        from hypocurate.pipeline import queries
        from hypocurate.pipeline.writes import database_message
        if isinstance(error, queries.QueryRefused):
            return error.reason
        if isinstance(error, IntegrityError):
            return database_message(error)
        raise error

    def form_values(form) -> dict:
        return {"claim": form.get("claim", ""), "domain": form.get("domain", ""),
                "sufficiency": form.get("sufficiency", "fixed_minimum"), "note": form.get("note", ""),
                "sources": form.getlist("sources"), "action": form.get("action", "save")}

    @app.get("/queries", response_class=HTMLResponse)
    def queries_page(request: Request, before: int | None = Query(None)):
        from hypocurate.pipeline import query_view
        try:
            listed = query_view.queries_list(engine, before)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        return page(request, "queries.html", {"listed": listed, "active": "queries"})

    @app.get("/queries/new", response_class=HTMLResponse)
    def new_query_form(request: Request):
        from hypocurate.pipeline import query_view
        return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": None,
                                                 "values": None, "error": None, "active": "new"})

    @app.post("/queries")
    async def new_query(request: Request):
        from hypocurate.pipeline import queries, query_view
        form = await request.form()
        security.check_csrf(request, form.get(security.CSRF_FIELD))
        security.signed_in_name(request)
        v = form_values(form)
        try:
            q = queries.create(engine, v["claim"], v["sources"], domain=v["domain"], sufficiency=v["sufficiency"],
                               note=v["note"])
            if v["action"] == "submit":
                queries.submit(engine, q.version_id)
        except Exception as error:  # noqa: BLE001 (refused_words re-raises anything that is not a fixed refusal)
            return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": None,
                                                     "values": v, "error": refused_words(error), "active": "new"},
                        status_code=409)
        return RedirectResponse(f"/queries/{q.number}", status_code=303)

    @app.get("/queries/{number}", response_class=HTMLResponse)
    def query_detail(request: Request, number: str):
        from hypocurate.pipeline import query_view
        try:
            shown = query_view.query_page(engine, number)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        return page(request, "query.html", {"q": shown, "error": None, "active": "queries"})

    @app.get("/queries/{number}/edit", response_class=HTMLResponse)
    def edit_query_form(request: Request, number: str):
        from hypocurate.pipeline import query_view
        try:
            shown = query_view.query_page(engine, number)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        latest = shown["latest"]
        values = {"claim": latest["claim"], "note": latest["note"] or "", "sufficiency": latest["sufficiency_key"],
                  "sources": [s["key"] for s in latest["sources"]], "domain": latest["domain_key"]}
        return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
                                                 "q": shown, "values": values, "error": None, "active": "queries"})

    @app.post("/queries/{number}/edit")
    async def edit_query(request: Request, number: str):
        from hypocurate.pipeline import queries, query_view
        form = await request.form()
        security.check_csrf(request, form.get(security.CSRF_FIELD))
        security.signed_in_name(request)
        v = form_values(form)
        try:
            shown = query_view.query_page(engine, number)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        try:
            change = queries.new_version if shown["latest"]["status"] == "returned" else queries.update_draft
            vid = change(engine, number, v["claim"], v["sources"], v["domain"], v["sufficiency"], v["note"])
            if v["action"] == "submit":
                queries.submit(engine, vid)
        except Exception as error:  # noqa: BLE001
            return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
                                                     "q": shown, "values": v, "error": refused_words(error),
                                                     "active": "queries"}, status_code=409)
        return RedirectResponse(f"/queries/{number}", status_code=303)

    @app.post("/queries/{number}/again")
    async def dispatch_again(request: Request, number: str):
        from hypocurate.pipeline import queries, query_view
        form = await request.form()
        security.check_csrf(request, form.get(security.CSRF_FIELD))
        security.signed_in_name(request)
        try:
            rid = queries.dispatch_again(engine, number)
        except Exception as error:  # noqa: BLE001
            try:
                shown = query_view.query_page(engine, number)
            except query_view.NoSuchQuery as missing:
                raise HTTPException(status_code=404, detail=str(missing)) from None
            return page(request, "query.html", {"q": shown, "error": f"Not dispatched: {refused_words(error)}",
                                                "active": "queries"}, status_code=409)
        return RedirectResponse(f"/runs/{rid}", status_code=303)

    @app.get("/review", response_class=HTMLResponse)
    def review_index(request: Request):
        from hypocurate.pipeline import query_view, run_view
        return page(request, "review.html", {"picker": query_view.review_list(engine), "q": None,
                                             "queue": run_view.queue_rows(engine), "error": None, "active": "review"})

    @app.get("/review/{number}", response_class=HTMLResponse)
    def review_query(request: Request, number: str):
        from hypocurate.pipeline import query_view
        try:
            shown = query_view.review_page(engine, number)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
                                             "queue": shown.get("queue"), "error": None, "active": "review"})

    async def review_action(request: Request, number: str, act):
        from hypocurate.pipeline import query_view
        form = await request.form()
        security.check_csrf(request, form.get(security.CSRF_FIELD))
        name = security.signed_in_name(request)
        try:
            shown = query_view.review_page(engine, number)
        except query_view.NoSuchQuery as error:
            raise HTTPException(status_code=404, detail=str(error)) from None
        try:
            if not shown["reviewable"]:
                from hypocurate.pipeline.queries import QueryRefused
                raise QueryRefused("not_submitted", f"query {number} is {shown['latest']['status_words']}; only a "
                                                    "submitted query is reviewed")
            return act(form, name, shown)
        except Exception as error:  # noqa: BLE001
            return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
                                                 "queue": shown.get("queue"), "active": "review",
                                                 "error": refused_words(error)}, status_code=409)

    @app.post("/review/{number}/dispatch")
    async def review_dispatch(request: Request, number: str):
        from hypocurate.pipeline import queries

        def act(form, name, shown):
            ceiling = (form.get("ceiling") or "").strip()
            try:
                ceiling = Decimal(ceiling) if ceiling else None
            except InvalidOperation:
                raise queries.QueryRefused("ceiling", "the ceiling is a number of US dollars") from None
            if ceiling is not None and not ceiling > 0:
                raise queries.QueryRefused("ceiling", "the ceiling is a positive number of US dollars")
            queries.confirm_domain(engine, shown["version_id"], by=name, domain=form.get("domain") or None,
                                   where=queries.WEBSITE)
            rid = queries.dispatch(engine, shown["version_id"], ceiling=ceiling)
            return RedirectResponse(f"/runs/{rid}", status_code=303)

        return await review_action(request, number, act)

    @app.post("/review/{number}/return")
    async def review_return(request: Request, number: str):
        from hypocurate.pipeline import queries

        def act(form, name, shown):
            queries.return_for_edits(engine, shown["version_id"], by=name, comment=form.get("comment", ""))
            return RedirectResponse(f"/queries/{number}", status_code=303)

        return await review_action(request, number, act)

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
