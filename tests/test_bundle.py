"""Sprint 2 pilot: the evidence bundle (register 'pilot_bundle_load').

A bundle exported from one database loads into another whose pilot tables are empty and whose shared tables already
hold rows: the pilot rows keep their ids, so every snapshot's events hash is unchanged; invocations and model calls get
the target's ids; the database's rules are checked again in the original order; the pilot source is sealed with the
same fingerprint; the states R6 computes are the same. A second load, a tampered file or another schema is refused,
and a refused load writes nothing."""
from __future__ import annotations

import io
import json
import zipfile

import pytest
from sqlalchemy import text

import stub_provider as sp
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.documents import bundle
from hypocurate.pipeline import evidence as ev
from hypocurate.pipeline import reconcile as rc
from hypocurate.sources import pilot, versions
from test_evidence import COMPILATION, OWNER, _person, paper  # noqa: F401 (fixture)


@pytest.fixture
def target(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    with engine.begin() as conn:  # the live database's shared tables already have rows: ids differ after the load
        for t in ("agent_invocation", "model_call", "agent_setting"):
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), 500)"))
    yield engine
    engine.dispose()
    _drop(admin, name)


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def _source(db, p, stub):
    """A pilot history on the source database: S0s, a Reconciler call (invocation and model call), the owner's
    decisions, the R6 rules, a freeze and the sealed pilot version."""
    versions.register(db, "mpea")  # the Reconciler reads the compilation's records
    stub.queue(sp.reply(sp.fields(mappings=json.dumps({"mappings": [
        {"kind": "alias_to_composition", "observation": 2, "subject": "A3", "proposed": {"composition": "Co50Ni50"},
         "quote": "A3"}]})), input_tokens=2000, output_tokens=300))
    run = rc.reconcile(db, p.out, client_options=sp.client_options(stub))
    assert run.failure is None
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
        mid = conn.execute(text("SELECT id FROM reconciler_mapping WHERE invocation_id IS NOT NULL")).scalar()
        _person(conn, "mapping", mid, p.out, "accepted")
        conn.execute(text("INSERT INTO auditor_finding (object_kind, object_id, extraction_output_id, finding_kind, "
                          "consequence, detail, by_person) VALUES ('observation', :o, :x, 'not_comparable', "
                          "'qualified_unresolved', 'a sentence', :p)"), dict(o=p.obs[0], x=p.out, p=OWNER))
    ev.apply_rules(db, p.outputs)
    frozen = ev.freeze(db, p.outputs, OWNER, COMPILATION)
    return frozen, pilot.register_frozen(db, frozen, OWNER)


def _status(engine, outputs):
    with engine.connect() as conn:
        return [(s.observation_id, s.category, s.reason, s.rereport_of) for s in ev.status(conn, outputs, COMPILATION)]


def test_a_bundle_loads_with_the_same_snapshots_states_and_pilot_version(db, paper, stub, target):  # noqa: F811
    frozen, sealed = _source(db, paper, stub)
    content = bundle.export(db)
    versions.register(target, "mpea")  # as on the live database
    out = bundle.load(target, content, OWNER)
    assert out["snapshots_checked"] == 3 and out["pilot_versions"] == [sealed.registered.fingerprint]
    with db.connect() as a, target.connect() as b:
        for t, _ in bundle.PILOT_TABLES:
            assert a.execute(text(f"SELECT count(*) FROM {t}")).scalar() == b.execute(text(f"SELECT count(*) FROM {t}")
                                                                                      ).scalar(), t
        snaps = "SELECT id, name, event_ids, events_sha256 FROM evidence_snapshot ORDER BY id"
        assert a.execute(text(snaps)).all() == b.execute(text(snaps)).all()
        calls = "SELECT role, status, input_tokens, output_tokens, cost FROM model_call ORDER BY id"
        assert a.execute(text(calls)).all() == b.execute(text(calls)).all()
        assert b.execute(text("SELECT min(id) FROM agent_invocation")).scalar() > 500  # the target's own ids
        mapped = b.execute(text("SELECT i.role FROM reconciler_mapping m JOIN agent_invocation i ON i.id = "
                                "m.invocation_id")).scalars().all()
        assert mapped == ["reconciler"]
    assert _status(db, paper.outputs) == _status(target, paper.outputs)
    with pytest.raises(bundle.BundleRefused, match="not empty"):
        bundle.load(target, content, OWNER)


def test_a_tampered_bundle_or_another_schema_is_refused_and_writes_nothing(db, paper, stub, target):  # noqa: F811
    _source(db, paper, stub)
    content = bundle.export(db)
    src = zipfile.ZipFile(io.BytesIO(content))
    tampered = io.BytesIO()
    with zipfile.ZipFile(tampered, "w") as z:
        for name in src.namelist():
            b = src.read(name)
            z.writestr(name, b.replace(b'"1100"', b'"1200"') if name == "candidate_value.json" else b)
    with pytest.raises(bundle.BundleRefused, match="candidate_value.json does not match"):
        bundle.load(target, tampered.getvalue(), OWNER)
    other = io.BytesIO()
    with zipfile.ZipFile(other, "w") as z:
        for name in src.namelist():
            b = src.read(name)
            if name == "manifest.json":
                m = json.loads(b)
                m["schema_revision"] = "0009"
                b = json.dumps(m).encode()
            z.writestr(name, b)
    with pytest.raises(bundle.BundleRefused, match="schema"):
        bundle.load(target, other.getvalue(), OWNER)
    with target.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM document")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM model_call")).scalar() == 0


def test_the_freeze_command_seals_the_pilot_source(db, paper, monkeypatch, capsys):  # noqa: F811
    import argparse
    from hypocurate.documents import cli
    versions.register(db, "mpea")
    monkeypatch.setattr(ev, "PROMPT_VERSION", "none")
    with db.begin() as conn:
        _person(conn, "link", paper.links[paper.obs[2]], paper.out, "accepted")
    ev.apply_rules(db, paper.outputs)
    parser = argparse.ArgumentParser()
    cli.add_parser(parser.add_subparsers(dest="command"))
    assert cli.command(parser.parse_args(["documents", "freeze", "--by", OWNER]), db) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["primary_new"] == [paper.obs[2]] and out["accepted"] == sorted(paper.obs[:3])
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM source_version v JOIN source s ON s.id = v.source_id "
                                 "WHERE s.key = 'extracted_pilot'")).scalar() == 1
