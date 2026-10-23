"""Step 3: migrations. Up, down and up again on an empty database; a failed
upgrade changes nothing; concurrent upgrades are serialized; the command line.

Every test here starts from an empty scratch database, never from the template."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.schema import CreateTable

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.db.models import Base

REPO = Path(__file__).resolve().parents[1]
MIGRATION = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0001").module
# Step 8a: 0005 adds three append-only tables with their own checked inserts.
MIGRATION_0005 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0005").module


def snapshot(engine) -> dict:
    """Everything the migrations create in the public schema, as text, for comparison."""
    queries = {
        "tables": "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public'",
        "columns": """SELECT table_name, column_name, data_type, is_nullable, column_default, is_identity
                      FROM information_schema.columns WHERE table_schema = 'public'""",
        "constraints": """SELECT conrelid::regclass::text, conname, pg_get_constraintdef(c.oid)
                          FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
                          WHERE n.nspname = 'public'""",
        "indexes": "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'",
        "triggers": """SELECT tgrelid::regclass::text, tgname, pg_get_triggerdef(t.oid) FROM pg_trigger t
                       JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
                       WHERE n.nspname = 'public' AND NOT t.tgisinternal""",
        "functions": """SELECT p.proname, pg_get_function_identity_arguments(p.oid), p.prosrc FROM pg_proc p
                        JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public'""",
        "views": "SELECT viewname, definition FROM pg_views WHERE schemaname = 'public'",
        "sequences": "SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'",
        "types": """SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE n.nspname = 'public' AND t.typtype IN ('e', 'd', 'c')
                      AND NOT EXISTS (SELECT 1 FROM pg_class c WHERE c.reltype = t.oid)""",
    }
    with engine.connect() as conn:
        return {k: sorted(tuple(map(str, row)) for row in conn.execute(text(q))) for k, q in queries.items()}


def expected_triggers() -> set[tuple[str, str]]:
    m = MIGRATION
    names = {(t, f"hc_{t}_append_only") for t in m.APPEND_ONLY}
    names |= {(t, f"hc_{t}_no_truncate") for t in m.APPEND_ONLY + m.NO_DELETE + ["hypothesis_version_source"]}
    names |= {(t, f"hc_{t}_no_delete") for t in m.NO_DELETE}
    names |= {(t, f) for t, _, f in m.CHECKED}
    m5 = MIGRATION_0005
    names |= {(t, f"hc_{t}_append_only") for t in m5.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m5.APPEND_ONLY}
    names |= {(t, f) for t, _, f in m5.CHECKED}
    m6 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0006").module  # step 8b
    names |= {(t, trigger) for t, _, trigger, _ in m6.CHECKED}
    m7 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0007").module  # step 9a
    names |= {(t, f"hc_{t}_append_only") for t in m7.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m7.APPEND_ONLY}
    names |= {(t, trigger) for t, _, trigger, _ in m7.CHECKED}
    m8 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0008").module  # step 9b
    names |= {(t, f"hc_{t}_no_delete") for t in m8.NO_DELETE} | {(t, f"hc_{t}_no_truncate") for t in m8.NO_DELETE}
    names |= {(t, trigger) for t, _, trigger, _ in m8.CHECKED}
    m9 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0009").module  # step 10b, fix round 1
    names |= {(t, f"hc_{t}_append_only") for t in m9.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m9.APPEND_ONLY}
    names |= {(t, trigger) for t, _, trigger, _ in m9.CHECKED}
    m10 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0010").module  # Sprint 2 pilot (R1)
    names |= {(t, f"hc_{t}_append_only") for t in m10.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m10.APPEND_ONLY}
    names |= {(t, trigger) for t, _, trigger, _ in m10.CHECKED} | set(m10.CONSTRAINT_TRIGGERS)
    return names


def model_check_names() -> set[str]:
    names = set()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        names |= set(re.findall(r"CONSTRAINT (ck_\w+) CHECK", ddl))
    return names


def assert_schema_is_head(engine):
    with engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []
        db_checks = {r[0] for r in conn.execute(text(
            "SELECT conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
            "WHERE n.nspname = 'public' AND contype = 'c'"))}
        domains = conn.execute(text("SELECT key FROM domain ORDER BY key")).scalars().all()
        approved_tags = conn.execute(text("SELECT count(*) FROM tag_value WHERE status = 'approved'")).scalar()
    assert db_checks == model_check_names()
    assert approved_tags == 19  # migration 0002 (step 6)
    s = snapshot(engine)
    assert {(t, n) for t, n, _ in s["triggers"]} == expected_triggers()
    assert {v for v, _ in s["views"]} == set(MIGRATION.VIEW_NAMES)
    assert domains == ["fatigue", "grain_size_strengthening", "other"]
    assert migrate.current_revision(engine) == migrate.head_revision()


def assert_schema_is_empty(engine):
    s = snapshot(engine)
    # Alembic keeps its own bookkeeping table, empty; nothing else may remain.
    assert s["tables"] == [("alembic_version", "BASE TABLE")]
    assert [c for c in s["constraints"] if c[0] != "alembic_version"] == []
    for kind in ("triggers", "functions", "views", "sequences", "types"):
        assert s[kind] == [], kind
    assert migrate.current_revision(engine) is None


# --- revisions ------------------------------------------------------------------------

# Revisions that only insert rows, whose downgrade leaves the rows (owner, 2026-10-05): tag
# values can never be deleted. Their downgrade is tested by behaviour in test_migrations_step6.py.
DATA_ONLY = {"0002"}


def test_exactly_one_head_and_every_revision_has_a_downgrade():
    scripts = ScriptDirectory(str(migrate.MIGRATIONS))
    assert len(scripts.get_heads()) == 1
    revisions = {rev.revision for rev in scripts.walk_revisions()}
    assert DATA_ONLY <= revisions
    for rev in scripts.walk_revisions():
        source = Path(rev.path).read_text()
        body = source.split("def downgrade() -> None:", 1)[1]
        if rev.revision in DATA_ONLY:
            # A data-only revision: its upgrade changes no schema, and its downgrade does nothing.
            upgrade = source.split("def upgrade() -> None:", 1)[1].split("def downgrade", 1)[0]
            assert not re.search(r"op\.(create|add|drop|alter)_", upgrade), rev.revision
            assert "op." not in body and body.strip().startswith('"""'), rev.revision
        else:
            assert "drop" in body.lower(), rev.revision


def test_migrations_stay_inside_the_one_transaction():
    """No statement may escape the upgrade transaction (README, 'Database migrations')."""
    env = (migrate.MIGRATIONS / "env.py").read_text()
    assert "transaction_per_migration=False" in env
    assert env.index("pg_advisory_xact_lock") < env.index("context.run_migrations()")
    for path in list((migrate.MIGRATIONS / "versions").glob("*.py")) + [migrate.MIGRATIONS / "script.py.mako"]:
        source = path.read_text()
        docstring = source.split('"""')[1]  # the module docstring states these rules in words
        code = "\n".join(line for line in source.replace(docstring, "").splitlines()
                          if not line.lstrip().startswith("#")).upper()  # comments may say "committed"
        for forbidden in ("CONCURRENTLY", "AUTOCOMMIT_BLOCK", "COMMIT", "VACUUM"):
            assert not re.search(rf"\b{forbidden}\b", code), (path.name, forbidden)


def test_migrations_ship_inside_the_package():
    """The deployed image holds only hypocurate/, data/ and the lock; the migrations are in hypocurate/."""
    assert migrate.MIGRATIONS.is_relative_to(REPO / "hypocurate")
    assert not (REPO / "alembic.ini").exists()


# --- up, down, up -------------------------------------------------------------------------

def test_up_down_up_on_an_empty_database(empty_database):
    engine = make_engine(empty_database)
    try:
        assert snapshot(engine)["tables"] == []
        migrate.upgrade(engine)
        assert_schema_is_head(engine)
        first = snapshot(engine)

        migrate.downgrade(engine, "base")
        assert_schema_is_empty(engine)

        migrate.upgrade(engine)
        assert_schema_is_head(engine)
        assert snapshot(engine) == first
    finally:
        engine.dispose()


def test_upgrade_at_head_changes_nothing(empty_database):
    engine = make_engine(empty_database)
    try:
        migrate.upgrade(engine)
        first = snapshot(engine)
        migrate.upgrade(engine)
        assert snapshot(engine) == first
    finally:
        engine.dispose()


def test_a_failed_upgrade_changes_nothing(empty_database):
    """A table planted under a name the migration creates late makes the upgrade
    fail part-way. The one transaction rolls everything back: no new table,
    function, view or revision."""
    engine = make_engine(empty_database)
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE commentary (planted int)"))
        before = snapshot(engine)
        with pytest.raises(ProgrammingError, match="already exists"):
            migrate.upgrade(engine)
        assert snapshot(engine) == before
        assert migrate.current_revision(engine) is None
    finally:
        engine.dispose()


def test_concurrent_upgrades_run_one_after_the_other(empty_database):
    """Web and worker run the pre-deploy command for the same commit. Both wait on
    the advisory lock (held here first), then one migrates and the other finds the
    database at head. Both exit 0 and the seed rows exist once."""
    engine = make_engine(empty_database)
    env = {**os.environ, "DATABASE_URL": empty_database, "HYPOCURATE_ENV": "development"}
    cmd = [sys.executable, "-m", "hypocurate.db.migrate", "upgrade"]
    try:
        with engine.connect() as holder:
            holder.execute(text("SELECT pg_advisory_lock(:k)"), {"k": migrate.ADVISORY_LOCK_KEY})
            procs = [subprocess.Popen(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True) for _ in range(2)]
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                with engine.connect() as probe:
                    waiting = probe.execute(text(
                        "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")).scalar()
                if waiting == 2:
                    break
                time.sleep(0.2)
            assert waiting == 2, "both upgrades should be waiting on the lock"
            holder.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": migrate.ADVISORY_LOCK_KEY})
            holder.commit()
        results = [p.communicate(timeout=120) + (p.returncode,) for p in procs]
        assert [r[2] for r in results] == [0, 0], [r[1][-2000:] for r in results]
        assert_schema_is_head(engine)
    finally:
        engine.dispose()


# --- command line and status -------------------------------------------------------------------

def test_command_line_upgrade_current_downgrade(empty_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", empty_database)
    monkeypatch.setenv("HYPOCURATE_ENV", "development")
    assert migrate.main(["current"]) == 0
    assert "empty" in capsys.readouterr().out
    assert migrate.main(["upgrade"]) == 0
    assert migrate.main(["current"]) == 0
    assert capsys.readouterr().out.strip().endswith(migrate.head_revision())
    assert migrate.main(["downgrade", "base"]) == 0
    engine = make_engine(empty_database)
    try:
        assert_schema_is_empty(engine)
    finally:
        engine.dispose()


def test_production_downgrade_needs_confirmation(empty_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", empty_database)
    monkeypatch.setenv("HYPOCURATE_ENV", "production")
    assert migrate.main(["upgrade"]) == 0
    assert migrate.main(["downgrade", "base"]) == 2
    assert "--confirm-data-loss" in capsys.readouterr().err
    engine = make_engine(empty_database)
    try:
        assert migrate.current_revision(engine) == migrate.head_revision()  # nothing was dropped
        assert migrate.main(["downgrade", "base", "--confirm-data-loss"]) == 0
        assert_schema_is_empty(engine)
    finally:
        engine.dispose()


def test_command_line_never_prints_the_database_password(empty_database, monkeypatch, capsys):
    password = make_engine(empty_database).url.password
    monkeypatch.setenv("DATABASE_URL", empty_database)
    migrate.main(["upgrade"])
    migrate.main(["current"])
    out = capsys.readouterr()
    assert password not in out.out and password not in out.err


def test_schema_status(empty_database):
    engine = make_engine(empty_database)
    try:
        assert migrate.schema_status(engine) == {"revision": None, "at_head": False}
        migrate.upgrade(engine)
        assert migrate.schema_status(engine) == {"revision": migrate.head_revision(), "at_head": True}
    finally:
        engine.dispose()
    unreachable = make_engine("postgresql://nobody:planted-pw-7319@127.0.0.1:1/none")
    assert migrate.schema_status(unreachable) == {"revision": None, "at_head": False}
