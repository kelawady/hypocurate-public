"""Sprint 2 pilot, R11: the H2 evidence inventory (PRD v1.2; owner, 2026-10-22, D25/D27).

The H2 selection reproduces the PRD's anchor (131 compilation records at >= 800 °C, BCC, none with a grain size). The
inventory is built from stored rows: its status is 'inventory; analysis deferred to a versioned protocol'; the causes
separate compilation records lacking a grain size, papers not obtained under the configured sources, papers not
parsed and observations read without a stated grain size; recovered records carry their provenance, grain-size type
and state. The page and the workbook show the same inventory."""
from __future__ import annotations

import hashlib
import io

import pytest
from openpyxl import load_workbook
from sqlalchemy import text

from hypocurate.documents.parse_worker import canonical
from hypocurate.documents.select import bcc_high_temperature
from hypocurate.pipeline import inventory
from hypocurate.pipeline.extraction import s0
from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
from hypocurate.pipeline.extraction.interface import EvidenceSpec, ParsedDocument
from hypocurate.sources import versions

H2_DOI = "10.1016/j.actamat.2019.06.032"  # one of the H2 papers (30 compilation records)


@pytest.fixture
def mpea(db):
    versions.register(db, "mpea")
    return db


def test_the_h2_selection_reproduces_the_prd_anchor(mpea):
    with mpea.connect() as conn:
        sel = bcc_high_temperature(versions.load_sealed_version(conn, versions.latest_sealed_version_id(conn, "mpea")))
    assert (sel.records, len(sel.papers), sel.records_without_doi) == (131, 20, 0)
    assert sum(p.records_with_yield_strength for p in sel.papers) == 127
    assert sum(p.records_with_grain_size for p in sel.papers) == 0
    assert sel.papers[0].doi_key == "doi:" + H2_DOI and sel.papers[0].records == 30


def test_with_nothing_obtained_every_cause_is_counted_and_nothing_is_recovered(mpea):
    with mpea.connect() as conn:
        inv = inventory.build(conn)
    assert inv.status == "inventory; analysis deferred to a versioned protocol"
    assert inv.causes["compilation records lacking a grain size"] == 131
    assert inv.causes["papers not obtained under the configured sources, no open copy listed"] == 20
    assert inv.totals["recovered"] == 0 and inv.recovered == [] and inv.by_state == {}


def test_a_read_paper_gives_recovered_records_with_type_state_and_provenance(mpea, monkeypatch):
    from hypocurate.pipeline import evidence
    monkeypatch.setattr(evidence, "PROMPT_VERSION", "none")  # the fixture extractor's prompt version
    parsed = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
              "pages": 4, "attempts": [], "texts": [{"index": 0, "page": 3, "text": "Compression at 1000 °C."}],
              "tables": [{"index": 0, "page": 3, "caption": "Table 2", "rows": [
                  ["Alloy", "Grain size (µm)", "Yield strength (MPa)", "Temperature"],
                  ["NbMoTaW", "200", "550", "1000 °C"], ["NbMoTaW", "80", "figure only", "1000 °C"]]}]}
    body, pdf = canonical(parsed), b"%PDF-1.7\n% h2 inventory\n"
    with mpea.begin() as conn:
        doc = conn.execute(text("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand, "
                                "access_method) VALUES (:d, :k, 'by_hand', :p, :h, 'K. El-Awady', true, 'manual_fetch') "
                                "RETURNING id"), dict(d=H2_DOI, k="doi:" + H2_DOI, p=pdf,
                                                      h=hashlib.sha256(pdf).hexdigest())).scalar_one()
        pid = conn.execute(text("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, "
                                "parsed, parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, "
                                "'parsed', :b, :h, 4, 1) RETURNING id"),
                           dict(d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())).scalar_one()
    with mpea.connect() as conn:
        document = ParsedDocument.load(conn, pid)
    s0.store_and_freeze(mpea, document, FixtureExtractor().extract(document, EvidenceSpec.load("H2_v1")))
    with mpea.connect() as conn:
        inv = inventory.build(conn)
    assert inv.totals["papers_read"] == 1 and inv.totals["observations"] == 2 and inv.totals["recovered"] == 1
    assert inv.causes["observations read with no yield strength stated as a number"] == 1
    assert inv.causes["papers not obtained under the configured sources, no open copy listed"] == 19
    (r,) = inv.recovered
    assert (r["grain_size"], r["yield_strength"], r["grain_size_type"], r["state"]) == ("200", "550", "not recorded",
                                                                                         "proposed")
    assert r["grain_size_provenance"] == "p. 3, table 0, row 1"
    assert inv.by_state == {("proposed", "not recorded"): 2}
    wb = load_workbook(io.BytesIO(inventory.workbook(inv)))
    assert wb.sheetnames == ["Summary", "Papers", "Recovered records"]
    summary = [r[:2] for r in wb["Summary"].iter_rows(values_only=True)]
    assert ("H2 evidence inventory", inventory.STATUS) in summary and ("recovered", 1) in summary


def test_the_inventory_page_and_workbook_are_served_to_a_signed_in_person(mpea, migrated_database):
    from test_web_runs import signed_in
    c = signed_in(mpea, migrated_database)
    page = c.get("/pilot/h2")
    assert page.status_code == 200 and inventory.STATUS in page.text and "Counts by cause" in page.text
    assert "No record recovered in the sources searched." in page.text
    book = c.get("/pilot/h2/workbook")
    assert book.status_code == 200 and book.content[:2] == b"PK"
    from test_web_runs import make_client
    assert make_client(mpea, migrated_database).get("/pilot/h2").status_code in (302, 303, 401)  # signed in only
