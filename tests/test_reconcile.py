"""Sprint 2 pilot, R5: the Reconciler (owner, 2026-10-23: per document, before the runs).

Its complete input is the parsed document, the newest S0's candidates and the compilation's records for the same
paper; an Extractor call cannot read the compilation's records (the owner's condition of 2026-10-22). Its proposals are
stored as mappings with what code made of them (Sprint 1's normalizers and vocabularies), in state 'proposed', or
'unresolved' with code's reason; nothing is dropped; S0 is never touched (its events are S1's)."""
from __future__ import annotations

import hashlib
import json

import pytest
from sqlalchemy import text

import stub_provider as sp
from hypocurate.access.dispatch import bind_invocation
from hypocurate.access.errors import AccessDenied
from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline import reconcile as rc
from hypocurate.pipeline.agents.settings import ensure_setting, extractor_variant, reconciler_variant
from hypocurate.pipeline.extraction import model_extractor as mx
from hypocurate.pipeline.extraction import s0
from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
from hypocurate.pipeline.extraction.interface import EvidenceSpec, ParsedDocument
from hypocurate.sources import versions

DOI = "10.1016/j.ijplas.2018.10.005"
PDF = b"%PDF-1.7\n% reconcile test\n"
PARSED = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
          "pages": 8, "attempts": [],
          "texts": [{"index": 0, "page": 6, "text": "The Cr20Fe6Co34Ni34Mo6 alloy was tested in tension at room temperature."}],
          "tables": [{"index": 0, "page": 6, "caption": "Table 1",
                      "rows": [["Alloy", "State", "Grain size (µm)", "Yield strength (MPa)"],
                               ["Cr20Fe6Co34Ni34Mo6", "700 °C 1 h", "0.8", "1100"]]}]}


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def frozen(db):
    versions.register(db, "mpea")
    body = canonical(PARSED)
    with db.begin() as conn:
        doc = conn.execute(text("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand, "
                                "access_method, access_note) VALUES (:d, :k, 'by_hand', :p, :h, 'K. El-Awady', true, "
                                "'institutional_credential', 'fetched manually') RETURNING id"),
                           dict(d=DOI, k="doi:" + DOI, p=PDF, h=hashlib.sha256(PDF).hexdigest())).scalar_one()
        parse_id = conn.execute(text(
            "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
            "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 8, 1) "
            "RETURNING id"), dict(d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())).scalar_one()
    with db.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    return s0.store_and_freeze(db, document, FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1"))), parse_id


def test_the_reconcilers_input_is_the_document_its_s0_and_the_compilations_records_for_that_paper(db, frozen):
    f, parse_id = frozen
    inv = mx._invocation(db, parse_id, ensure_setting(db, "extractor", extractor_variant("extract", "H1_v1")))
    with pytest.raises(AccessDenied) as e:  # the owner's condition: an extractor call never reads the compilation
        bind_invocation(db, inv).get("compilation_records")
    assert e.value.code == "not_on_list"
    setting = ensure_setting(db, "reconciler", reconciler_variant())
    with db.begin() as conn:
        rinv = conn.execute(text("INSERT INTO agent_invocation (scope, role, agent_setting_id) VALUES ('document', "
                                 "'reconciler', :a) RETURNING id"), dict(a=setting)).scalar_one()
        conn.execute(text("INSERT INTO document_invocation (invocation_id, document_parse_id) VALUES (:i, :p)"),
                     dict(i=rinv, p=parse_id))
    access = bind_invocation(db, rinv)
    records = access.get("compilation_records")
    assert len(records) == 7 and {r["key"] for r in records} >= {"MPEA_dataset.csv:row:810"}
    assert access.get("s0_records")["extraction_output_id"] == f.output_id
    with pytest.raises(AccessDenied):
        access.get("extraction_spec")  # not on the Reconciler's list


def answer(*mappings):
    return sp.fields(mappings=json.dumps({"mappings": list(mappings)}))


def test_proposals_are_applied_by_code_stored_with_their_states_and_s0_is_untouched(db, frozen, stub):
    f, _ = frozen
    stub.queue(sp.reply(answer(
        {"kind": "alias_to_composition", "observation": 0, "subject": "Cr20Fe6Co34Ni34Mo6",
         "proposed": {"composition": "Cr20Fe6Co34Ni34Mo6"}, "quote": "The Cr20Fe6Co34Ni34Mo6 alloy"},
        {"kind": "condition_to_category", "observation": 0, "subject": "tension",
         "proposed": {"field": "test_type", "category": "tensile"}, "quote": "tested in tension"},
        {"kind": "same_observation", "observation": 0, "subject": "0.8 µm, 1100 MPa",
         "compilation_key": "MPEA_dataset.csv:row:810", "proposed": {}, "quote": "700 °C 1 h"},
        {"kind": "same_observation", "observation": 0, "subject": "no key given", "proposed": {}, "quote": "x"}),
        input_tokens=3000, output_tokens=500))
    with db.connect() as conn:
        s0_before = conn.execute(text("SELECT event_ids, events_sha256 FROM evidence_snapshot WHERE name = 'S0'")).one()
    run = rc.reconcile(db, f.output_id, client_options=sp.client_options(stub))
    assert run.failure is None and run.mappings == 4 and run.unresolved == 2
    with db.connect() as conn:
        rows = conn.execute(text("SELECT m.kind, m.subject, m.applied, m.compilation_key, e.state, e.by_rule, e.reason "
                                 "FROM reconciler_mapping m JOIN evidence_state_event e ON e.object_kind = 'mapping' "
                                 "AND e.object_id = m.id ORDER BY m.id")).all()
        s0_after = conn.execute(text("SELECT event_ids, events_sha256 FROM evidence_snapshot WHERE name = 'S0'")).one()
    alias, cond, same, keyless = rows
    assert alias.state == "proposed" and alias.applied["same_alloy_key"].startswith("Co 34.0 Cr 20.0")
    assert alias.subject == "Cr20Fe6Co34Ni34Mo6"  # the original as written is kept
    assert (cond.state, cond.by_rule) == ("unresolved", "reconciler-check") and "not in the vocabulary" in cond.reason
    assert same.state == "proposed" and same.applied["grain_size_within_tolerance"] is True
    assert same.applied["yield_strength_within_tolerance"] is True
    assert (keyless.compilation_key, keyless.state) == ("(none given)", "unresolved")
    assert tuple(s0_before) == tuple(s0_after)  # S0 never changes
    body = stub.bodies()[0]
    assert "MPEA_dataset.csv:row:810" in json.dumps(body)  # the Reconciler does see the compilation (S1, never S0)
    assert run.cost > 0


def test_the_same_observation_check_converts_units_before_comparing():
    """Review finding (2026-10-23): coatings rows in nm showed a 999-fold difference that is 0 % once converted."""
    obs = {0: {"values": [{"field": "grain_size", "text": "27.6", "unit": "nm"},
                          {"field": "yield_strength", "text": "∼1.1", "unit": "GPa"}]},
           1: {"values": [{"field": "grain_size", "text": "0.2–20", "unit": "µm"},
                          {"field": "yield_strength", "text": "figure only", "unit": None}]}}
    comp = {"k": {"grain_size_um": 0.0276, "yield_strength_mpa": 1100.0}}
    out = rc.apply({"kind": "same_observation", "observation": 0, "compilation_key": "k"}, obs, comp)
    assert out["grain_size_relative_difference"] == "0.0000" and out["grain_size_within_tolerance"] is True
    assert out["yield_strength_relative_difference"] == "0.0000" and out["yield_strength_within_tolerance"] is True
    out = rc.apply({"kind": "same_observation", "observation": 1, "compilation_key": "k"}, obs, comp)
    assert out["grain_size_within_tolerance"] is None and out["yield_strength_within_tolerance"] is None  # not compared
