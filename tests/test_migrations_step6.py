"""Step 6: migrations 0002 (tag starting lists, data only) and 0003 (record.extraction).

Owner, 2026-10-05: both are in the up, down, up test and the failure-rollback test; 0002 is
safe on a database that already has some values and its downgrade leaves the rows; 0003 is
additive and its replaced insert trigger keeps every check of 0001 and adds only the new
requirement. Every test starts from an empty scratch database."""
import json
import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import profile
from test_migrations import assert_schema_is_empty, assert_schema_is_head, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0002 = SCRIPTS.get_revision("0002").module
M0003 = SCRIPTS.get_revision("0003").module
REGISTER = json.loads((migrate.MIGRATIONS.parents[1] / "assumptions.json").read_text(encoding="utf-8"))


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


def tags(engine) -> dict:
    with engine.connect() as conn:
        return {(k, v): s for k, v, s in conn.execute(text("SELECT kind, value, status FROM tag_value"))}


def record_insert_source(engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = 'hc_record_insert'")).scalar_one()


def columns(engine, table) -> set:
    with engine.connect() as conn:
        return set(conn.execute(text("SELECT column_name FROM information_schema.columns "
                                     "WHERE table_schema = 'public' AND table_name = :t"), dict(t=table)).scalars())


def body(sql: str) -> str:
    """A function's body between the $$ quotes, with whitespace normalized."""
    return " ".join(sql.split("$$")[1].split())


# --- 0002 ------------------------------------------------------------------------------------

def test_the_seeded_lists_are_the_registers_and_the_profiles():
    """The migration's lists, the domain profile's and the register entry's statement agree."""
    assert {k: tuple(v) for k, v in M0002.TAG_STARTING_LISTS.items()} == \
        {k: tuple(v) for k, v in profile.TAG_STARTING_LISTS.items()}
    statement = next(e for e in REGISTER if e["key"] == "tag_starting_lists")["statement"]
    names = {"property": "Property", "alloy_class": "Alloy class", "test_condition": "Test condition"}
    assert statement == " ".join(f"{names[k]}: {', '.join(v)}." for k, v in M0002.TAG_STARTING_LISTS.items())
    assert sum(len(v) for v in M0002.TAG_STARTING_LISTS.values()) == 19


def test_0002_changes_no_schema_and_seeds_19_approved_values(engine):
    migrate.upgrade(engine, "0001")
    before = snapshot(engine)
    migrate.upgrade(engine, "0002")
    after = snapshot(engine)
    assert after == before  # no table, column, constraint, index, trigger, function or view changed
    seeded = tags(engine)
    assert len(seeded) == 19 and set(seeded.values()) == {"approved"}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM tag_value WHERE decided_at IS NULL "
                                 "OR proposed_by_run_id IS NOT NULL")).scalar() == 0


def test_0002_is_safe_on_a_database_that_already_has_some_values(engine):
    """An existing value keeps its row and its status; nothing is duplicated."""
    migrate.upgrade(engine, "0001")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO tag_value (kind, value, status) VALUES ('property', 'yield strength', "
                          "'proposed')"))
        conn.execute(text("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('alloy_class', "
                          "'steel', 'rejected', now())"))
        conn.execute(text("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('test_condition', "
                          "'cryogenic', 'approved', now())"))
        ids = dict(conn.execute(text("SELECT value, id FROM tag_value")).all())
    migrate.upgrade(engine)
    got = tags(engine)
    assert len(got) == 19
    assert got[("property", "yield strength")] == "proposed"
    assert got[("alloy_class", "steel")] == "rejected"
    assert got[("test_condition", "cryogenic")] == "approved"
    with engine.connect() as conn:
        assert dict(conn.execute(text("SELECT value, id FROM tag_value WHERE value IN "
                                      "('yield strength', 'steel', 'cryogenic')")).all()) == ids
    assert sum(s == "approved" for s in got.values()) == 17


def test_up_down_up_through_each_new_revision(engine):
    """Head, down to 0002 (0003 removed), down to 0001 (0002's downgrade leaves the rows),
    up again: the same schema as before, the rows once."""
    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    first = snapshot(engine)
    assert "extraction" in columns(engine, "record")

    migrate.downgrade(engine, "0002")
    assert migrate.current_revision(engine) == "0002"
    assert "extraction" not in columns(engine, "record")
    assert " ".join(record_insert_source(engine).split()) == body(M0003.RECORD_INSERT_0001)
    assert len(tags(engine)) == 19

    migrate.downgrade(engine, "0001")
    assert migrate.current_revision(engine) == "0001"
    assert len(tags(engine)) == 19  # rows stay: tag values are never deleted

    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    assert snapshot(engine) == first
    assert len(tags(engine)) == 19

    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_through_the_new_revisions_changes_nothing(engine):
    """A column planted under the name 0003 adds makes the upgrade fail after 0002 has
    inserted its rows. The one transaction rolls both back: no tag value, no new revision."""
    migrate.upgrade(engine, "0001")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE record ADD COLUMN extraction int"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert tags(engine) == {}
    assert migrate.current_revision(engine) == "0001"


# --- 0003 ------------------------------------------------------------------------------------

def test_0003_keeps_every_check_of_0001_and_adds_one():
    """The replaced function is 0001's, unchanged and in the same order, plus one check at the end."""
    original = next(f for f in M0001.FUNCTIONS if "CREATE FUNCTION hc_record_insert()" in f)
    assert body(M0003.RECORD_INSERT_0001) == body(original)
    added = ("IF NEW.extraction IS NULL THEN PERFORM hc_reject('a record states how it was extracted "
             "(adapter or agent, with name and version)'); END IF;")
    old, new = body(M0003.RECORD_INSERT_0001), body(M0003.RECORD_INSERT_0003)
    assert new == old.replace("RETURN NEW; END", f"{added} RETURN NEW; END")
    assert len(re.findall(r"PERFORM hc_reject", new)) == len(re.findall(r"PERFORM hc_reject", old)) + 1


def _record(conn, run, version, key, extraction):
    conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                      "reported, extraction) VALUES (:r, :v, :k, 'measured', '{}', '{}', CAST(:x AS jsonb))"),
                 dict(r=run, v=version, k=key, x=extraction))


GOOD = {"method": "adapter", "name": "mpea_layout", "version": "1"}


@pytest.mark.parametrize("extraction", [
    {"name": "mpea_layout", "version": "1"},  # method missing (review finding 6)
    {"method": None, "name": "mpea_layout", "version": "1"},
    {"method": 1, "name": "mpea_layout", "version": "1"},
    {"method": "adapter", "version": "1"},  # name missing
    {"method": "adapter", "name": None, "version": "1"},
    {"method": "adapter", "name": 5, "version": "1"},
    {"method": "adapter", "name": {"a": 1}, "version": "1"},
    {"method": "adapter", "name": "mpea_layout"},  # version missing
    {"method": "adapter", "name": "mpea_layout", "version": None},
    {"method": "adapter", "name": "mpea_layout", "version": 1},
    {"method": "adapter", "name": "mpea_layout", "version": ["1"]},
    {"method": "adapter", "name": "", "version": "1"},
    "adapter",
], ids=lambda x: json.dumps(x))
def test_0003_refuses_a_missing_null_or_wrongly_typed_extraction_field(db, extraction):
    """Review finding 6: every key present, a JSON string, and the whole check true (a missing
    value must not pass as SQL NULL)."""
    from model_builder import World
    w = World(db)
    rid = w.locked()
    with pytest.raises(IntegrityError, match="ck_record_extraction_shape"):
        with db.begin() as conn:
            _record(conn, rid, w.version["mpea"], "row-x", json.dumps(extraction))
    with db.begin() as conn:
        _record(conn, rid, w.version["mpea"], "row-ok", json.dumps(GOOD))


def test_0003_a_new_record_states_its_extraction(db):
    from model_builder import World
    w = World(db)
    rid = w.locked()
    good = json.dumps({"method": "adapter", "name": "mpea_layout", "version": "1"})
    with db.begin() as conn:
        _record(conn, rid, w.version["mpea"], "row-1", good)
    with pytest.raises(IntegrityError, match="states how it was extracted"):
        with db.begin() as conn:
            _record(conn, rid, w.version["mpea"], "row-2", None)
    for bad in ({"method": "guess", "name": "x", "version": "1"}, {"method": "agent", "name": "", "version": "1"},
                {"method": "adapter", "name": "x"}, ["adapter"]):
        with pytest.raises(IntegrityError, match="ck_record_extraction_shape"):
            with db.begin() as conn:
                _record(conn, rid, w.version["mpea"], "row-3", json.dumps(bad))
    # Every 0001 check still applies: for example no record before the rules lock.
    with pytest.raises(IntegrityError, match="only after the rules lock"):
        with db.begin() as conn:
            _record(conn, w.running(), w.version["mpea"], "row-4", good)
