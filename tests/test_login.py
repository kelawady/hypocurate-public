"""Step 2: the single shared login (PRD Section 6, "Login"), with the fixes for
the second-model review of step 2 (findings 2, 3, 4 and 6)."""
import base64
import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import itsdangerous.timed
import pytest
from fastapi.testclient import TestClient

from hypocurate.config import ConfigError, Settings, load_settings
from hypocurate.db.engine import make_engine
from hypocurate.web.app import SESSION_COOKIE, SESSION_MAX_AGE, create_app
from hypocurate.web.login_throttle import MAX_FAILURES, LoginThrottle

PASSWORD = "test-password-not-a-secret"
NAME = "Test Person"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"
# Paths that only look like the public ones (review finding 3).
LOOKALIKES = ["/loginx", "/login-admin", "/login/admin", "/healthz", "/health-private",
              "/health/export", "/staticx", "/static"]


def settings(env="development", password=PASSWORD, secret=SECRET):
    return Settings(env=env, database_url=UNREACHABLE_DB, password=password,
                    session_secret=secret, version="test")


def make_app(env="development", throttle=None, password=PASSWORD, secret=SECRET):
    s = settings(env, password, secret)
    app = create_app(s, engine=make_engine(s.database_url), login_throttle=throttle)
    for path in LOOKALIKES:
        app.add_api_route(path, lambda: {"protected": True}, methods=["GET"])
    return app


def client(env="development", throttle=None, app=None):
    base = "https://testserver" if env == "production" else "http://testserver"
    return TestClient(app or make_app(env, throttle), base_url=base, follow_redirects=False)


def sign_in(c, password=PASSWORD):
    # Step 10a (owner, 2026-10-11, answer 1): the sign-in form also takes the person's name.
    return c.post("/login", data={"password": password, "name": NAME})


def cookie_payload(value):
    """The session cookie is base64(JSON) . timestamp . signature; return the JSON."""
    return json.loads(base64.b64decode(value.split(".")[0]))


# --- which paths need the login ----------------------------------------------------

def test_pages_redirect_to_login_when_signed_out():
    c = client()
    for path in ["/", "/anything", "/runs/1"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_page_and_static_are_public():
    c = client()
    assert c.get("/login").status_code == 200
    assert c.get("/static/style.css").status_code == 200


@pytest.mark.parametrize("path", LOOKALIKES)
def test_lookalike_paths_are_protected(path):
    """Only /login and /health exactly, and files under /static/, are public."""
    c = client()
    r = c.get(path)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    sign_in(c)
    if path == "/static":
        return  # the static mount answers here once signed in; the point is the redirect above
    assert c.get(path).json() == {"protected": True}


def test_no_api_docs_before_or_after_login():
    c = client()
    paths = ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"]
    for path in paths:
        assert c.get(path).status_code == 303
    sign_in(c)
    for path in paths:
        assert c.get(path).status_code == 404, path


# --- password -----------------------------------------------------------------------

def test_wrong_password_is_refused_and_gives_no_session():
    c = client()
    r = sign_in(c, "wrong-password")
    assert r.status_code == 401
    assert SESSION_COOKIE not in r.cookies
    assert c.get("/").status_code == 303


def test_empty_password_is_refused():
    c = client()
    assert c.post("/login", data={}).status_code == 401


def test_right_password_gives_a_session():
    c = client()
    r = sign_in(c)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert c.get("/").status_code == 200


def test_logout_ends_the_session():
    c = client()
    sign_in(c)
    r = c.post("/logout")
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert c.get("/").status_code == 303


# --- the cookie ---------------------------------------------------------------------

def test_cookie_holds_only_the_signed_in_flag_the_name_and_the_form_token():
    """Step 10a (owner, 2026-10-11, answer 1 and addition 1): the cookie also holds the name given at sign-in and the
    token every write carries; nothing else."""
    c = client()
    sign_in(c)
    payload = cookie_payload(c.cookies[SESSION_COOKIE])
    assert set(payload) == {"signed_in", "name", "csrf"}
    assert payload["signed_in"] is True and payload["name"] == NAME and len(payload["csrf"]) >= 40


def test_tampered_cookie_is_rejected():
    c = client()
    sign_in(c)
    value = c.cookies[SESSION_COOKIE]
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, value[:-2] + ("AA" if value[-2:] != "AA" else "BB"))
    assert c.get("/").status_code == 303


def test_forged_payload_with_old_signature_is_rejected():
    c = client()
    sign_in(c)
    _, ts, sig = c.cookies[SESSION_COOKIE].split(".")
    forged = base64.b64encode(json.dumps({"signed_in": True, "role": "admin"}).encode()).decode()
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, f"{forged}.{ts}.{sig}")
    assert c.get("/").status_code == 303


def test_cookie_signed_with_another_secret_is_rejected():
    forger = client(app=make_app(secret="o" * 40))
    sign_in(forger)
    c = client()
    c.cookies.set(SESSION_COOKIE, forger.cookies[SESSION_COOKIE])
    assert c.get("/").status_code == 303


def test_production_cookie_is_secure_httponly_lax_with_max_age():
    c = client("production")
    header = sign_in(c).headers["set-cookie"].lower()
    assert "secure" in header
    assert "httponly" in header
    assert "samesite=lax" in header
    assert f"max-age={SESSION_MAX_AGE}" in header


def test_password_is_not_in_pages():
    c = client()
    sign_in(c)
    assert PASSWORD not in c.get("/").text
    assert PASSWORD not in c.get("/login").text


# --- sessions: rotation, expiry, copied cookie (review finding 4) ----------------------

def test_rotating_the_secret_and_password_ends_existing_sessions():
    """How to revoke access (README, "Sessions"): change SESSION_SECRET with the password."""
    old = client()
    sign_in(old)
    cookie = old.cookies[SESSION_COOKIE]
    rotated = client(app=make_app(password="a-new-password-after-rotation", secret="n" * 40))
    rotated.cookies.set(SESSION_COOKIE, cookie)
    assert rotated.get("/").status_code == 303
    assert sign_in(rotated, PASSWORD).status_code == 401
    assert sign_in(rotated, "a-new-password-after-rotation").status_code == 303


def test_changing_only_the_password_does_not_end_sessions():
    """Stated limitation: the password alone is not in the cookie, so the secret must rotate too."""
    old = client()
    sign_in(old)
    new = client(app=make_app(password="a-new-password-after-rotation"))
    new.cookies.set(SESSION_COOKIE, old.cookies[SESSION_COOKIE])
    assert new.get("/").status_code == 200


def test_session_expires_after_max_age(monkeypatch):
    now = {"t": 1_800_000_000}
    monkeypatch.setattr(itsdangerous.timed.TimestampSigner, "get_timestamp", lambda self: now["t"])
    c = client()
    sign_in(c)
    now["t"] += SESSION_MAX_AGE - 60
    assert c.get("/").status_code == 200
    now["t"] += 61
    assert c.get("/").status_code == 303


def test_ordinary_requests_do_not_renew_the_session(monkeypatch):
    """Step 4b review: the session ends 12 hours after sign-in, however much it is used.
    The middleware re-signs the cookie only when the session data change (at sign-in)."""
    now = {"t": 1_800_000_000}
    monkeypatch.setattr(itsdangerous.timed.TimestampSigner, "get_timestamp", lambda self: now["t"])
    c = client()
    assert "set-cookie" in sign_in(c).headers
    for _ in range(3):
        now["t"] += SESSION_MAX_AGE // 4
        r = c.get("/")
        assert r.status_code == 200 and "set-cookie" not in r.headers
    now["t"] += SESSION_MAX_AGE // 4 + 1  # 12 hours and 1 second after sign-in
    assert c.get("/").status_code == 303


def test_copied_cookie_still_works_after_logout():
    """Stated limitation of cookie-only sessions (no session table in sprint 1):
    logout clears this browser's cookie but cannot revoke a copy. A copy works
    until it expires (SESSION_MAX_AGE) or SESSION_SECRET is rotated."""
    original = client()
    sign_in(original)
    copy = client()
    copy.cookies.set(SESSION_COOKIE, original.cookies[SESSION_COOKIE])
    original.post("/logout")
    assert original.get("/").status_code == 303
    assert copy.get("/").status_code == 200


# --- throttling of failed logins (review finding 2) --------------------------------------

def test_wrong_attempts_beyond_the_bound_receive_429():
    c = client(throttle=LoginThrottle())
    codes = [sign_in(c, "wrong-password").status_code for _ in range(MAX_FAILURES + 3)]
    assert codes == [401] * MAX_FAILURES + [429] * 3


def test_correct_password_is_accepted_while_throttled():
    c = client(throttle=LoginThrottle())
    for _ in range(MAX_FAILURES + 3):
        sign_in(c, "wrong-password")
    r = sign_in(c)
    assert r.status_code == 303
    assert c.get("/").status_code == 200


def test_concurrent_wrong_attempts_respect_the_bound():
    """Fifty simultaneous wrong attempts through the web app: exactly MAX_FAILURES are
    counted, the rest refused; a correct login in the middle of them still succeeds."""
    app = make_app(throttle=LoginThrottle())
    start = threading.Barrier(10)  # 50 attempts = 5 full groups released together

    def wrong(_):
        c = client(app=app)
        try:
            start.wait(timeout=5)
        except threading.BrokenBarrierError:
            pass
        return sign_in(c, "wrong-password").status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(wrong, i) for i in range(50)]
        right = client(app=app)
        right_code = sign_in(right).status_code
        codes = Counter(f.result() for f in futures)
    assert codes == {401: MAX_FAILURES, 429: 50 - MAX_FAILURES}
    assert right_code == 303
    assert right.get("/").status_code == 200


# --- settings -----------------------------------------------------------------------

GOOD = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d",
        "HYPOCURATE_PASSWORD": "p" * 24, "SESSION_SECRET": SECRET}


def test_settings_load_when_complete():
    assert load_settings(GOOD).production


@pytest.mark.parametrize("missing", ["DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"])
def test_web_refuses_to_start_without_a_secret(missing):
    env = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_production_password_must_be_at_least_24_characters():
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD must be at least 24"):
        load_settings({**GOOD, "HYPOCURATE_PASSWORD": "p" * 23})
    assert load_settings({**GOOD, "HYPOCURATE_PASSWORD": "p" * 24}).production


def test_development_password_must_be_at_least_12_characters():
    dev = {**GOOD, "HYPOCURATE_ENV": "development"}
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD must be at least 12"):
        load_settings({**dev, "HYPOCURATE_PASSWORD": "p" * 11})
    assert not load_settings({**dev, "HYPOCURATE_PASSWORD": "p" * 12}).production


def test_web_refuses_a_short_session_secret():
    with pytest.raises(ConfigError, match="SESSION_SECRET"):
        load_settings({**GOOD, "SESSION_SECRET": "short"})


def test_config_errors_never_contain_values():
    env = {**GOOD, "HYPOCURATE_PASSWORD": "tiny-pw", "SESSION_SECRET": "tiny-secret"}
    with pytest.raises(ConfigError) as e:
        load_settings(env)
    assert "tiny-pw" not in str(e.value) and "tiny-secret" not in str(e.value)


def test_worker_needs_no_login_secrets():
    env = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d"}
    assert load_settings(env, web=False).password == ""


def test_unknown_env_is_refused():
    with pytest.raises(ConfigError):
        load_settings({**GOOD, "HYPOCURATE_ENV": "staging"})


def test_settings_repr_hides_secrets():
    text = repr(load_settings(GOOD))
    assert "p" * 24 not in text and SECRET not in text and "planted-pw-7319" not in text
