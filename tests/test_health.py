"""Step 2: the health page, the idle worker and the command line against a real PostgreSQL.
Step 3: /health also reports the schema revision (informational)."""
import logging

from fastapi.testclient import TestClient

from hypocurate import cli, worker
from hypocurate.config import Settings
from hypocurate.db.engine import make_engine
from hypocurate.db.migrate import head_revision
from hypocurate.web.app import create_app

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"


def client(database_url):
    s = Settings(env="development", database_url=database_url, password=PASSWORD,
                 session_secret=SECRET, version="abc123")
    return TestClient(create_app(s, engine=make_engine(database_url)), follow_redirects=False)


def test_health_without_login_database_up(migrated_database):
    r = client(migrated_database).get("/health")
    assert r.status_code == 200
    assert r.json() == {"web": "ok", "database": "ok", "version": "abc123",
                        "schema": {"revision": head_revision(), "at_head": True}}


def test_health_reports_an_unmigrated_database_without_failing(empty_database):
    """The schema field is informational: it never changes the status code."""
    r = client(empty_database).get("/health")
    assert r.status_code == 200
    assert r.json()["schema"] == {"revision": None, "at_head": False}


def test_health_page_in_a_browser(migrated_database):
    r = client(migrated_database).get("/health", headers={"accept": "text/html"})
    assert r.status_code == 200
    assert "Database" in r.text and ">ok<" in r.text
    assert f"<code>{head_revision()}</code> (latest)" in r.text


def test_health_reports_database_down_without_crashing():
    r = client(UNREACHABLE_DB).get("/health")
    assert r.status_code == 503
    assert r.json()["database"] == "unreachable"
    assert r.json()["schema"] == {"revision": None, "at_head": False}


def test_health_shows_no_secrets(database_url):
    c = client(database_url)
    for accept in ["application/json", "text/html"]:
        text = c.get("/health", headers={"accept": accept}).text
        assert PASSWORD not in text and SECRET not in text
        assert database_url not in text and "postgresql" not in text


def test_worker_idles_and_checks_the_database(database_url, monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", database_url)
    sleeps = []
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=2, sleep=sleeps.append)
    assert sleeps == [worker.IDLE_SECONDS] * 2
    assert caplog.text.count("no pipeline yet; database reachable") == 2


def test_worker_logs_an_unreachable_database(monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=1, sleep=lambda s: None)
    assert "database NOT reachable" in caplog.text
    assert "planted-pw-7319" not in caplog.text  # the URL's password is never logged


def test_cli_check_db(database_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert cli.main(["check-db"]) == 0
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    assert cli.main(["check-db"]) == 1
    assert "planted-pw-7319" not in capsys.readouterr().out
