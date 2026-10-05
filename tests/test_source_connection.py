"""Step 4: 'test connection and show sample records' (PRD 9.6), and the command line."""
import json

import pytest
from sqlalchemy import text

from hypocurate import cli
from hypocurate.sources import connection
from hypocurate.sources.record import HARMONIZED_FIELDS
from hypocurate.sources.versions import SOURCES, UnsealedVersion, register

TABLES = ("source", "source_version", "source_file", "record", "audit_log", "run", "hypothesis")


def counts(engine):
    with engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABLES}


@pytest.fixture
def registered(db):
    for key in SOURCES:
        register(db, key)
    return db


@pytest.mark.parametrize("key,total", [("mpea", 1545), ("tamu_fcc", 94), ("controlled_duplicates", 16)])
def test_it_returns_sample_records_in_the_common_format(registered, key, total):
    before = counts(registered)
    report = connection.test_connection(registered, key, n=3)
    assert counts(registered) == before
    assert report.source_key == key and report.records_read == total and report.blank_rows == 0
    assert len(report.sample) == 3
    assert [r.source_item_key.rsplit(":", 1)[1] for r in report.sample] == ["0", "1", "2"]
    assert all(set(r.harmonized) == set(HARMONIZED_FIELDS) for r in report.sample)
    assert all(r.version_fingerprint == report.fingerprint for r in report.sample)
    assert sum(report.status_counts.values()) == total * len(HARMONIZED_FIELDS)
    json.dumps(report.to_json())


def test_assigned_values_are_shown_with_their_citation(registered):
    report = connection.test_connection(registered, "tamu_fcc", n=1).to_json()
    test_type = report["sample"][0]["harmonized"]["test_type"]
    assert test_type["status"] == "assigned_from_source"
    assert "Quasistatic tensile testing" in test_type["citation"]["quote"]
    band = report["sample"][0]["harmonized"]["test_temperature_band"]
    assert band["status"] == "assigned_by_decision" and "'tamu_test_temperature'" in band["citation"]["location"]
    # Two fields from the source and two by decision, for each of the 94 records (step 6).
    assert report["status_counts"]["assigned_from_source"] == 94 * 2
    assert report["status_counts"]["assigned_by_decision"] == 94 * 2
    assert "assigned" not in report["status_counts"]


def test_it_needs_a_sealed_version(db):
    with pytest.raises(UnsealedVersion, match="no sealed version"):
        connection.test_connection(db, "mpea")


def test_the_transaction_is_read_only(registered, monkeypatch):
    """A write slipped into the read would be refused by PostgreSQL."""
    original = connection.load_sealed_version

    def writing_loader(conn, vid):
        conn.execute(text("UPDATE source SET enabled = enabled"))
        return original(conn, vid)

    monkeypatch.setattr(connection, "load_sealed_version", writing_loader)
    with pytest.raises(Exception, match="read-only transaction"):
        connection.test_connection(registered, "mpea")


def test_the_command_line(db, migrated_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.delenv("HYPOCURATE_ENV", raising=False)
    assert cli.main(["sources", "register"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert [line.split(":")[0] for line in out] == list(SOURCES)
    assert all("registered and sealed" in line for line in out)
    assert cli.main(["sources", "register", "mpea"]) == 0
    assert "already registered" in capsys.readouterr().out
    assert cli.main(["sources", "test", "tamu_fcc", "-n", "2"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["records_read"] == 94 and len(shown["sample"]) == 2
    assert shown["sample"][0]["harmonized"]["test_type"]["status"] == "assigned_from_source"
    assert cli.main(["sources", "register", "nope"]) == 1
    assert "unknown source" in capsys.readouterr().err
