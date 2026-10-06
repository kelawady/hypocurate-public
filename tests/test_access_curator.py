"""Step 8a: the Curator's access at registration (owner, 2026-10-06, Q2; safeguard change).

The Curator runs when a source version is registered, never in a run. It is bound by
`dispatch.bind_invocation` from one registration invocation, and its complete input is the
documentation of that one sealed version and the target fields: no data file (which holds outcome
values), no claim (so not its direction), no plan, no other version. Every read is logged with no
run, naming the version and the invocation.

What these tests do not cover: the model request built from this input (the agent-core tests,
through the local stub provider), and anything the documentation itself says.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

from access_testing import registration_access_for
from hypocurate.access import AccessDenied, AccessFailed, bind, bind_invocation, role_input
from hypocurate.access.allowlist import FIELDS, allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.db.models import CURATION_FIELDS
from model_builder import World

PLANTED_OUTCOME = 987.6543  # a yield strength in the data file
DATA = f"alloy,grain_size,yield_strength\nZQX1,4.0,{PLANTED_OUTCOME}\n".encode()
DOC = ("Quasistatic tensile testing was used to determine 0.2% offset YS.\n"
       "The dataset contains 94 FCC alloy conditions.\n")
OTHER_DOC = "A different version's documentation: ZQOTHERDOC.\n"


@pytest.fixture
def w(db):
    return World(db)


def sealed(w, key, label, doc):
    v = w.new_version(key, label)
    w.add_file(v, "table.csv", DATA + label.encode())
    w.add_file(v, "documentation/main.tex", doc.encode(), role="documentation")
    w.seal(v)
    return v


def registration(w, version):
    return w.val("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                 "VALUES ('registration', :v, 'curator', :a) RETURNING id", v=version, a=w.agent_setting("curator"))


def audit(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT run_id, role, stage, function, allowed, detail FROM audit_log ORDER BY id")).all()


def test_the_curator_is_listed_only_at_registration_with_two_fields():
    assert allowed("curator", "registration") == {"source_documentation", "curation_targets"}
    assert set(CURATION_TARGETS) == set(CURATION_FIELDS)
    assert "source_content" not in FIELDS and "plan_fields_to_extract" not in FIELDS


def test_bind_invocation_binds_the_curator_to_its_version_with_no_run(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    inv = registration(w, v)
    a = bind_invocation(db, inv)
    assert a.context == AccessContext(None, "curator", "registration", "tamu_fcc", w.agent_setting("curator"),
                                      source_version_id=v, invocation_id=inv)
    [row] = [r for r in audit(db) if r.function == "bind"]
    assert row.run_id is None and row.allowed and row.stage == "registration"
    assert row.detail["source_version"] == v and row.detail["invocation"] == inv


def test_the_curators_complete_input_is_its_versions_documentation_and_the_targets(w, db):
    """A run exists whose claim states the direction, and the version's data file holds a planted
    outcome value; another version has its own documentation. None of it reaches the Curator."""
    w.running()  # a run with the claim "Yield strength rises as grain size falls"
    v = sealed(w, "tamu_fcc", "docs", DOC)
    sealed(w, "tamu_fcc", "other", OTHER_DOC)
    got = role_input(bind_invocation(db, registration(w, v)))
    assert set(got) == {"source_documentation", "curation_targets"}
    assert got["source_documentation"] == {"source": "tamu_fcc", "documents": {"documentation/main.tex": DOC}}
    assert got["curation_targets"] == {f: dict(s) for f, s in CURATION_TARGETS.items()}
    encoded = json.dumps(got)
    for absent in (str(PLANTED_OUTCOME), "9876543", "ZQX1", "table.csv", "ZQOTHERDOC", "rises", "grain size falls"):
        assert absent not in encoded, absent
    reads = [r for r in audit(db) if r.function != "bind"]
    assert {(r.function, r.allowed) for r in reads} == {("source_documentation", True), ("curation_targets", True)}
    assert all(r.run_id is None and r.detail["source_version"] == v for r in reads)


def test_a_registration_access_reads_no_run_field(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    a = bind_invocation(db, registration(w, v))
    for field in ("claim", "records_full", "sources_meta", "plan", "record_counts", "flags_kind"):
        with pytest.raises(AccessDenied) as denied:
            a.get(field)
        assert denied.value.code == "not_on_list"


def test_a_context_naming_another_version_or_role_is_refused(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    other = sealed(w, "tamu_fcc", "other", OTHER_DOC)
    inv = registration(w, v)
    for a in (registration_access_for(db, inv, other), registration_access_for(db, inv, v, role="planner")):
        with pytest.raises(AccessDenied):
            a.get("source_documentation")
    with pytest.raises(AccessDenied) as denied:
        registration_access_for(db, inv, other).get("source_documentation")
    assert denied.value.code == "stage_mismatch"


def test_an_unknown_invocation_is_a_logged_failure(w, db):
    with pytest.raises(AccessFailed) as failed:
        bind_invocation(db, 10 ** 9)
    assert failed.value.code == "unknown_invocation"
    [row] = audit(db)
    assert row.run_id is None and not row.allowed and row.detail == {"result": "failed", "code": "unknown_invocation",
                                                                      "invocation": 10 ** 9}
    with pytest.raises(AccessFailed) as failed:
        registration_access_for(db, 10 ** 9, 1).get("curation_targets")
    assert failed.value.code == "unknown_invocation"


def test_bind_invocation_for_a_run_takes_the_run_and_setting_from_the_record(w, db):
    """Two valid runs: the invocation of run B binds run B, whatever the caller holds."""
    a_run, b_run = w.running(agents=True), w.running(agents=True)
    inv_b = w.invocation(b_run, w.stage(b_run))
    got = bind_invocation(db, inv_b)
    setting = w.val("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = 'planner'", r=b_run)
    assert got.context == AccessContext(b_run, "planner", "before_lock", None, setting, invocation_id=inv_b)
    assert bind(db, a_run, setting).context.run_id == a_run  # bind itself takes what it is given
