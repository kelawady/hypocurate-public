"""Step 6: the code roles Inclusion and Checks read through access objects (PRD 4; owner,
2026-10-05; register entry 'code_role_access').

**Guaranteed, and tested here:** Inclusion receives no outcome value (the projected-data
search of step 5 over its complete input, with values planted everywhere the world stores
them), so no eligibility decision can depend on a record's outcome directly or on its
position relative to the tested relationship.

**Not claimed:** that outcomes play no part at all. Checks receives every value and compares
them to classify duplicates, conflicts and physically invalid records, and Inclusion acts on
those flag kinds (`tests/test_flags.py` shows that Checks uses per-record rules and pairwise
comparisons that feed a whole-group classification
rules).
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import access_world as aw
from hypocurate.access import AccessDenied, AccessFailed, role_input
from hypocurate.access.allowlist import ALLOWED, ALL_ROLES, CODE_ALLOWED, CODE_ROLES, OUTCOME_FIELDS, ROLES, allowed
from hypocurate.access.dispatch import bind, bind_code
from hypocurate.db.engine import make_engine
from hypocurate.sources import adapters
from hypocurate.sources.normalize import doi_group_key, identity_hash
from hypocurate.sources.record import HARMONIZED_FIELDS
from test_access_projected import leaks


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def audit(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log WHERE run_id = :r "
                                 "ORDER BY id"), dict(r=run_id)).all()


def test_the_code_lists_match_the_owners_decision():
    assert CODE_ROLES == ("inclusion", "checks") and ALL_ROLES == ROLES + CODE_ROLES
    assert not set(CODE_ROLES) & set(ALLOWED)  # the agent table is unchanged
    assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {"inclusion": {"curation"}, "checks": {"curation"}}
    # set_flags: step 6 review, finding 2 (each sensitivity set's matching flags, codes and ids only).
    assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind", "set_flags"}
    assert allowed("checks", "curation") == {"plan", "records_full"}
    for role in CODE_ROLES:
        for stage in ("none", "before_lock", "analysis", "closed_without_freeze", "final", "final_without_freeze"):
            assert allowed(role, stage) == frozenset()


def test_code_roles_bind_at_curation_and_every_bind_is_logged(engine):
    world = aw.build(engine, "curation")
    for role in CODE_ROLES:
        access = bind_code(engine, world.run, role)
        assert (access.context.role, access.context.stage, access.context.agent_setting_id) == (role, "curation", None)
    rows = [r for r in audit(engine, world.run) if r.function == "bind" and r.role in CODE_ROLES]
    assert [(r.role, r.allowed, r.detail["result"]) for r in rows] == [("inclusion", True, "allowed"),
                                                                    ("checks", True, "allowed")]


@pytest.mark.parametrize("stage", ["queued", "before_lock", "analysis", "closed_without_freeze", "final"])
def test_code_roles_do_not_bind_at_any_other_stage(engine, stage):
    world = aw.build(engine, stage)
    for role in CODE_ROLES:
        with pytest.raises(AccessDenied) as denied:
            bind_code(engine, world.run, role)
        assert denied.value.code == "empty_list"
        row = [r for r in audit(engine, world.run) if r.function == "bind"][-1]
        assert (row.role, row.allowed, row.detail["code"], row.detail["code_role"]) == (role, False, "empty_list", True)


def test_only_code_roles_bind_without_an_agent_setting(engine):
    world = aw.build(engine, "curation")
    for role in ROLES + ("analysis", "", "Inclusion"):
        with pytest.raises(AccessDenied) as denied:
            bind_code(engine, world.run, role)
        assert denied.value.code == "not_a_code_role"
    rows = [r for r in audit(engine, world.run) if r.function == "bind"]
    assert {(r.role, r.allowed, r.detail["code"]) for r in rows} == {("invalid", False, "not_a_code_role")}
    with pytest.raises(AccessFailed) as failed:
        bind_code(engine, 10 ** 9, "checks")
    assert failed.value.code == "unknown_run"


def test_an_agent_setting_cannot_bind_as_a_code_role(engine):
    """`bind` takes the role from run_agent_setting, whose roles are the five agent roles."""
    world = aw.build(engine, "curation")
    for role, setting in world.settings.items():
        assert bind(engine, world.run, setting, source_key="mpea" if role == "curator" else None).context.role == role
    with engine.connect() as conn:
        setting = conn.execute(text("SELECT id FROM agent_setting LIMIT 1")).scalar()
    for role in CODE_ROLES:
        with pytest.raises(IntegrityError, match="ck_agent_setting_role"):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO agent_setting (role, version, instruction, model) "
                                  "VALUES (:o, 1, 'x', 'm')"), dict(o=role))
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) "
                                  "VALUES (:r, :o, :a)"), dict(r=world.run, o=role, a=setting))


def test_inclusion_receives_no_outcome_value(engine):
    """The projected-data search over Inclusion's complete input finds none of the planted
    outcome values; Checks' input (all values, by design) is the positive control."""
    world = aw.build(engine, "curation")
    inclusion = role_input(bind_code(engine, world.run, "inclusion"))
    assert set(inclusion) == {"plan", "record_conditions", "flags_kind", "set_flags"}
    assert leaks(inclusion, aw.PLANTED.values()) == []
    assert aw.DIRECTION not in json.dumps(inclusion)
    checks = role_input(bind_code(engine, world.run, "checks"))
    assert any(f.startswith(f"{aw.PLANTED['yield_strength']}:") for f in leaks(checks, aw.PLANTED.values()))
    rows = [r for r in audit(engine, world.run) if r.role in CODE_ROLES and r.function != "bind"]
    assert {(r.role, r.function, r.allowed) for r in rows} == {
        ("inclusion", "plan", True), ("inclusion", "record_conditions", True), ("inclusion", "flags_kind", True),
        ("inclusion", "set_flags", True),
        ("checks", "plan", True), ("checks", "records_full", True)}


def test_record_conditions_carry_statuses_conditions_and_hashed_identities(engine):
    world = aw.build(engine, "curation")
    got = bind_code(engine, world.run, "inclusion").get("record_conditions")
    with engine.connect() as conn:
        stored = {r.id: r for r in conn.execute(text(
            "SELECT id, source_item_key, paper_doi, harmonized FROM record WHERE extraction_run_id = :r"),
            dict(r=world.run))}
    assert [r["id"] for r in got] == sorted(stored)
    for r in got:
        assert set(r) == {"id", "source", "row", "kind", "version_fingerprint", "origin", "item_index", "fingerprint",
                          "has_doi", "paper", "batch", "composition", "status", "values", "categories"}
        assert len(r["fingerprint"]) == 64
        s = stored[r["id"]]
        assert set(r["status"]) == set(HARMONIZED_FIELDS)
        assert set(r["values"]) == {"grain_size", "test_temperature"} and not set(r["values"]) & OUTCOME_FIELDS
        assert r["row"] == int(s.source_item_key.rsplit(":", 1)[1])
        assert (r["origin"], r["item_index"]) == (s.source_item_key, 0)
        doi = s.paper_doi if s.paper_doi and s.paper_doi.strip() else None
        assert r["has_doi"] == (doi is not None)
        assert r["paper"] == (identity_hash(doi_group_key(doi)) if doi else None)
        assert r["paper"] is None or (len(r["paper"]) == 64 and (doi or "") not in json.dumps(r))
        assert r["values"]["grain_size"] == s.harmonized["grain_size"].get("value")
    # The DOI planted with an outcome value reaches Inclusion only as a hash.
    assert all("doi " not in json.dumps(r) for r in got)


def test_record_conditions_hash_the_batch_for_texas_am(engine):
    world = aw.build(engine, "curation")
    w = world.w
    vid = w.version["tamu_fcc"]
    # The world's Texas A&M version is a placeholder; store two rows of the real one instead.
    from source_helpers import sealed_from_disk
    records = adapters.read(sealed_from_disk("tamu_fcc")).records[:2]
    with engine.begin() as conn:
        for r in records:
            j = r.to_json()
            conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                              "kind, alloy, harmonized, reported, paper_reference, paper_doi, extraction) VALUES "
                              "(:r, :v, :k, 0, 'measured', :a, CAST(:h AS jsonb), CAST(:rep AS jsonb), :pr, NULL, "
                              "CAST(:x AS jsonb))"),
                         dict(r=world.run, v=vid, k=j["source_item_key"], a=j["alloy"], h=json.dumps(j["harmonized"]),
                              rep=json.dumps(j["reported"]), pr=j["paper_reference"],
                              x=json.dumps(adapters.extraction("tamu_fcc"))))
    got = [r for r in bind_code(engine, world.run, "inclusion").get("record_conditions") if r["source"] == "tamu_fcc"]
    assert [r["batch"] for r in got] == [identity_hash(r.reported["Iteration"].text) for r in records]
    assert all(r["paper"] is None and r["has_doi"] is False for r in got)
    assert got[0]["status"]["microstructure"] == "assigned_by_decision"
    assert got[0]["categories"]["test_temperature_band"] == "room temperature"
    assert got[0]["status"]["yield_strength"] == "converted" and "yield_strength" not in got[0]["values"]
