"""Step 10b, fix round 1: migration 0009, `action_record` (the owner's answer of 2026-10-11 after ChatGPT's review,
finding 3: "New table action_record, migration 0009, as you recommend. Also write a row for confirm and cancel").

One row per person's action: the action (a fixed list), where (website, command line, code), the name given (required
on the website, none for code's own action), what it acted on (as the action requires), and the database's time.
Append-only. 0001 to 0008 untouched; up, down, up gives the same schema; the downgrade refuses while a row exists; a
failed upgrade changes nothing."""
from __future__ import annotations

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import actions, migrate, models
from hypocurate.db.engine import make_engine
from model_builder import World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
           "cancel", "confirm_rules", "register_source")


def m0009():
    return SCRIPTS.get_revision("0009").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


def insert(w, action="create", channel="website", actor="Ada", v=None, r=None, s=None, at=None):
    return w.val("INSERT INTO action_record (action, channel, actor, hypothesis_version_id, run_id, source_version_id"
                 + (", at" if at else "") + ") VALUES (:a, :c, :n, :v, :r, :s" + (", :at" if at else "")
                 + ") RETURNING id", a=action, c=channel, n=actor, v=v, r=r, s=s, at=at)


# --- the migration ------------------------------------------------------------------------------------------

def test_0009_is_the_head_and_follows_0008():
    assert migrate.head_revision() == "0009" and m0009().down_revision == "0008"


def test_0009_replaces_no_earlier_function():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m0009().FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m0009().FUNCTIONS)


def test_up_down_up_restores_0008(engine):
    migrate.upgrade(engine, "0008")
    at_0008 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0008")
    assert snapshot(engine) == at_0008
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0008")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_action_record_insert() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before and migrate.current_revision(engine) == "0008"


def test_the_downgrade_refuses_while_an_action_is_recorded(db):
    w = World(db)
    insert(w, v=w.draft())
    before = snapshot(db)
    with pytest.raises(Exception, match="0009 is in use"):
        migrate.downgrade(db, "0008")
    assert snapshot(db) == before and migrate.current_revision(db) == "0009"


def test_the_lists_are_the_codes():
    assert m0009().ACTIONS == ACTIONS == models.ACTIONS
    assert m0009().CHANNELS == models.CHANNELS == (actions.WEBSITE, actions.COMMAND_LINE, actions.CODE)
    assert m0009().TARGETS == models.ACTION_TARGETS and set(m0009().TARGETS) == set(ACTIONS)


# --- a row --------------------------------------------------------------------------------------------------

def test_the_time_is_the_databases(w):
    aid = insert(w, v=w.draft(), at="2000-01-01")
    assert w.val("SELECT at > '2001-01-01' FROM action_record WHERE id = :a", a=aid)


def test_rows_are_never_changed_deleted_or_truncated(w):
    aid = insert(w, v=w.draft())
    w.rejected("UPDATE action_record SET actor = 'Someone else' WHERE id = :a", "append-only", a=aid)
    w.rejected("DELETE FROM action_record WHERE id = :a", "append-only", a=aid)
    w.rejected("TRUNCATE action_record", "append-only")
    assert w.val("SELECT actor FROM action_record WHERE id = :a", a=aid) == "Ada"


@pytest.mark.parametrize("actor", [None, "", " Ada", "x" * 201])
def test_an_action_on_the_website_names_its_person(w, actor):
    with pytest.raises(IntegrityError, match="ck_action_record_(website_named|actor)"):
        insert(w, actor=actor, v=w.draft())


def test_the_command_line_may_give_no_name_and_code_gives_none(w):
    vid = w.draft()
    insert(w, channel="command line", actor=None, v=vid)
    insert(w, channel="code", actor=None, v=vid)
    with pytest.raises(IntegrityError, match="ck_action_record_code_unnamed"):
        insert(w, channel="code", actor="Ada", v=vid)


@pytest.mark.parametrize("action,channel", [("approve", "website"), ("create", "email")])
def test_only_the_fixed_actions_and_channels(w, action, channel):
    with pytest.raises(IntegrityError, match="ck_action_record_(action|channel)"):
        insert(w, action=action, channel=channel, v=w.draft())


def test_each_action_names_exactly_what_it_acts_on(w):
    vid = w.dispatched()
    rid = w.run(vid)
    sv = w.version["mpea"]
    targets = {"v": vid, "r": rid, "s": sv}
    for action, kinds in models.ACTION_TARGETS.items():
        insert(w, action=action, **{k: targets[k] for k in kinds})  # exactly its targets: accepted
        missing = {k: targets[k] for k in kinds[1:]}  # without its first target
        with pytest.raises(IntegrityError, match="ck_action_record_targets"):
            insert(w, action=action, **missing)
        extra = next(k for k in "vrs" if k not in kinds)  # with one it does not act on
        with pytest.raises(IntegrityError, match="ck_action_record_targets"):
            insert(w, action=action, **{k: targets[k] for k in kinds}, **{extra: targets[extra]})
