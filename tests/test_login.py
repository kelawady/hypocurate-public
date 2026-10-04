"""Step 2: the single shared login (PRD Section 6, "Login")."""
import pytest
from fastapi.testclient import TestClient

from hypocurate.config import ConfigError, Settings, load_settings
from hypocurate.db.engine import make_engine
from hypocurate.web.app import SESSION_COOKIE, create_app
from hypocurate.web.login_limit import MAX_FAILURES, LoginLimit

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"


def settings(env="development"):
    return Settings(env=env, database_url=UNREACHABLE_DB, password=PASSWORD,
                    session_secret=SECRET, version="test")


def client(env="development", limit=None):
    s = settings(env)
    app = create_app(s, engine=make_engine(s.database_url), login_limit=limit)
    base = "https://testserver" if env == "production" else "http://testserver"
    return TestClient(app, base_url=base, follow_redirects=False)


def sign_in(c, password=PASSWORD):
    return c.post("/login", data={"password": password})


def test_pages_redirect_to_login_when_signed_out():
    c = client()
    for path in ["/", "/anything", "/runs/1"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_page_and_static_are_public():
    c = client()
    assert c.get("/login").status_code == 200
    assert c.get("/static/style.css").status_code == 200


def test_no_api_docs_exposed():
    c = client()
    for path in ["/docs", "/redoc", "/openapi.json"]:
        assert c.get(path).status_code == 303


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


def test_tampered_cookie_is_rejected():
    c = client()
    sign_in(c)
    value = c.cookies[SESSION_COOKIE]
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, value[:-2] + ("AA" if value[-2:] != "AA" else "BB"))
    assert c.get("/").status_code == 303


def test_cookie_signed_with_another_secret_is_rejected():
    other = Settings(env="development", database_url=UNREACHABLE_DB, password=PASSWORD,
                     session_secret="o" * 40, version="test")
    forger = TestClient(create_app(other, engine=make_engine(UNREACHABLE_DB)), follow_redirects=False)
    sign_in(forger)
    c = client()
    c.cookies.set(SESSION_COOKIE, forger.cookies[SESSION_COOKIE])
    assert c.get("/").status_code == 303


def test_production_cookie_is_secure_httponly_lax():
    c = client("production")
    header = sign_in(c).headers["set-cookie"].lower()
    assert "secure" in header
    assert "httponly" in header
    assert "samesite=lax" in header


def test_password_is_not_in_the_cookie_or_pages():
    c = client()
    r = sign_in(c)
    assert PASSWORD not in r.headers.get("set-cookie", "")
    assert PASSWORD not in c.get("/").text
    assert PASSWORD not in c.get("/login").text


def test_lockout_after_failures_refuses_even_the_right_password():
    c = client(limit=LoginLimit())
    for _ in range(MAX_FAILURES):
        assert sign_in(c, "wrong-password").status_code == 401
    r = sign_in(c)
    assert r.status_code == 429
    assert SESSION_COOKIE not in r.cookies
    assert c.get("/").status_code == 303


# --- settings -------------------------------------------------------------------

GOOD = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d",
        "HYPOCURATE_PASSWORD": PASSWORD, "SESSION_SECRET": SECRET}


def test_settings_load_when_complete():
    assert load_settings(GOOD).production


@pytest.mark.parametrize("missing", ["DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"])
def test_web_refuses_to_start_without_a_secret(missing):
    env = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_web_refuses_short_secrets():
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD"):
        load_settings({**GOOD, "HYPOCURATE_PASSWORD": "short"})
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
    assert PASSWORD not in text and SECRET not in text and "planted-pw-7319" not in text
