"""Sprint 2 pilot: 'docling + row split v1' (owner, 2026-10-23). A merged row is split only when its multi-item cells
agree in count and are numeric; one-item cells are copied; text is verbatim; every new row records its source row and
part; a row that does not qualify stays merged and is counted; the split parse is a new parse, the old one kept."""
from __future__ import annotations

import hashlib
import json

from sqlalchemy import text

from hypocurate.documents import rowsplit as rs
from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline.extraction import provenance as pv
from hypocurate.pipeline.extraction.interface import ParsedDocument, Provenance

IJPLAS_TABLE = {"index": 0, "page": 6, "caption": "Table 1",
                "rows": [["Alloy", "Homogenization temperature (°C)", "Reduction in thickness (%)",
                          "Annealing temperature (°C), time (h)", "Grain size (μm)"],
                         ["Cr20Fe6Co34Ni34Mo6", "1200 1200 1200 1200 1200 1200", "70 70 70 70 70 70",
                          "675, 1 700, 1 800, 1 900, 1 1000, 1 1150, 1", "0.7 0.8 1.2 3.2 18.2 94.1"],
                         ["CrMnFeCoNi", "1200 1200 1200", "87 87 87", "800, 1 900, 1", "4.4 6.9 50"],
                         ["MnFeNi", "1100", "", "", "30"]]}
PARSED = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
          "pages": 8, "attempts": [], "texts": [{"index": 0, "page": 6, "text": "Table 1 lists the conditions."}],
          "tables": [IJPLAS_TABLE]}


def test_items_are_separated_by_spaces_not_after_a_comma():
    assert rs.items("675, 1 700, 1 800, 1") == ["675, 1", "700, 1", "800, 1"]
    assert rs.items("0.7 0.8 1.2") == ["0.7", "0.8", "1.2"] and rs.items(" ") == []


def test_the_ijplas_row_splits_into_six_and_the_inconsistent_row_stays_merged():
    new, summary = rs.split_parse(PARSED)
    rows = new["tables"][0]["rows"]
    assert summary == {"rows_split": 1, "rows_merged": 1, "tables_changed": 1}
    assert rows[1] == ["Cr20Fe6Co34Ni34Mo6", "1200", "70", "675, 1", "0.7"]
    assert rows[6] == ["Cr20Fe6Co34Ni34Mo6", "1200", "70", "1150, 1", "94.1"]
    assert rows[7] == IJPLAS_TABLE["rows"][2] and rows[8] == IJPLAS_TABLE["rows"][3]  # 3,3,2,3: not split
    assert new["tables"][0]["rows_merged"] == [2] and new["tables"][0]["source_rows"] == IJPLAS_TABLE["rows"]
    assert new["tables"][0]["row_origin"][3] == {"source_row": 1, "part": 3, "of": 6}
    assert new["parser_version"] == "2.141.0+rowsplit-1" and new["derived"]["rule"] == "docling + row split v1"
    assert PARSED["tables"][0]["rows"] == IJPLAS_TABLE["rows"]  # the input is not changed


def test_text_cells_and_single_numbers_are_never_split():
    assert rs.split_row(["CoCrFeMnNi", "annealed 1 h at 800 °C", "4.4", "360"]) is None
    assert rs.split_row(["A", "1 2", "x y"]) is None  # only one numeric multi-item cell
    assert rs.split_parse(PARSED | {"tables": [{"index": 0, "page": 1, "caption": None,
                                                "rows": [["a", "b"], ["1", "2"]]}]})[1]["tables_changed"] == 0


def test_a_split_rows_provenance_resolves_and_names_its_merged_source_cell():
    new, _ = rs.split_parse(PARSED)
    doc = ParsedDocument(1, 2, "a" * 64, "doi:10.1016/j.ijplas.2018.10.005", new)
    assert pv.problem(doc, Provenance(6, "700, 1 | 0.8", 0, 2)) is None
    src = pv.source_of(doc, 0, 2)
    assert src["source_row"] == 1 and (src["part"], src["of"]) == (2, 6)
    assert src["source_cells"][4] == "0.7 0.8 1.2 3.2 18.2 94.1"
    assert pv.source_of(doc, 0, 7) is None


def test_the_split_parse_is_stored_as_a_new_parse_and_logged(db):
    from model_builder import World
    w = World(db)
    pdf = b"%PDF-1.7\n% rowsplit\n"
    doc_id = w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand, access_method) VALUES "
                   "('10.1000/rs.1', 'doi:10.1000/rs.1', 'by_hand', :p, :h, 'K. El-Awady', true, "
                   "'institutional_credential') RETURNING id",
                   p=pdf, h=hashlib.sha256(pdf).hexdigest())
    body = canonical(PARSED)
    old = w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
                "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 8, 1) "
                "RETURNING id", d=doc_id, b=body, h=hashlib.sha256(body.encode()).hexdigest())
    new, summary = rs.store_split(db, old)
    assert new and new != old and summary["rows_split"] == 1
    with db.connect() as conn:
        parses = conn.execute(text("SELECT id, parser_version, parsed FROM document_parse WHERE document_id = :d "
                                   "ORDER BY id"), dict(d=doc_id)).all()
        entry = conn.execute(text("SELECT detail FROM search_log WHERE action = 'parse'")).scalar_one()
    assert [p.parser_version for p in parses] == ["2.141.0", "2.141.0+rowsplit-1"]
    assert json.loads(parses[0].parsed) == PARSED and json.loads(parses[1].parsed)["derived"]["from_parse"] == old
    assert entry == f"docling + row split v1 on parse {old}: 1 row(s) split, 1 left merged"
    assert rs.store_split(db, new)[0] is None  # already split: nothing more to do
