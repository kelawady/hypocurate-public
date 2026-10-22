"""Sprint 2 pilot, R2: the reach steps (PRD v1.2; the owner's decisions of 2026-10-22).

The selection uses Sprint 1's FCC definition (eligibility's single-phase rule, the microstructure field, column
`PROPERTY: Microstructure`) and is pinned: 28 papers, 107 records, 92 with a yield strength. The lookup prefers
Unpaywall's flag and lists PDF addresses without repeats; a download keeps only a PDF within the cap and records every
attempt with its cause; the supplement check answers 'yes' or 'not found by automatic check', never 'none'; the parser
takes Docling, falls back to pymupdf when Docling fails or finds no tables, and records every attempt; the canonical
JSON is byte-stable. End to end over two papers with a stub network and a fake parser: the stored rows give a reach
table with one row per paper, four milestones, and a recorded failure where a step failed. No live call is made."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

from hypocurate.documents import lookup as lk
from hypocurate.documents import parse_worker, reach, select, steps, store
from hypocurate.documents.select import Paper, Selection
from hypocurate.pipeline import profile
from source_helpers import sealed_from_disk

PDF = b"%PDF-1.7\n% test\n"


# --- the selection ---------------------------------------------------------------------------------------------------

def test_the_selection_uses_sprint1s_fcc_definition_and_is_pinned():
    s = select.fcc_grain_size(sealed_from_disk("mpea"))
    assert profile.SINGLE_PHASE == "required" and profile.PHASE_CLASSES == ("FCC",)
    assert (s.phase_field, s.phase_column) == ("microstructure", "PROPERTY: Microstructure")
    assert (len(s.papers), s.records, s.records_without_doi) == (28, 107, 0)
    assert sum(p.records_with_yield_strength for p in s.papers) == 92
    assert s.papers[0].doi_key == "doi:10.1016/j.actamat.2019.04.017" and s.papers[0].records == 25
    assert [p.records for p in s.papers] == sorted((p.records for p in s.papers), reverse=True)
    assert len({p.doi_key for p in s.papers}) == 28 and all(p.doi_key.startswith("doi:10.") for p in s.papers)


def test_the_selection_follows_the_profiles_phase_rule(monkeypatch):
    monkeypatch.setattr(profile, "SINGLE_PHASE", "not_required")
    s = select.fcc_grain_size(sealed_from_disk("mpea"))
    assert (s.phase_field, s.phase_column) == ("phase_class", "PROPERTY: BCC/FCC/other")
    assert s.records == 106  # the phase column counts one record fewer than the microstructure column


# --- lookup, download, supplements -----------------------------------------------------------------------------------

def stub(routes):
    """A stand-in for `http_get`: the first route whose key occurs in the URL answers; anything else is a 404."""
    calls = []

    def get(url, accept="*/*"):
        calls.append(url)
        for key, resp in routes.items():
            if key in url:
                status, body = resp[:2]
                ctype = resp[2] if len(resp) > 2 else ""
                body = json.dumps(body).encode() if isinstance(body, dict) else body
                return lk.Response(url, status, body, ctype, url, None if status == 200 else f"HTTP {status}")
        return lk.Response(url, 404, b"", "", url, "HTTP 404")
    get.calls = calls
    return get


UNPAYWALL_OA = {"is_oa": True, "oa_status": "gold",
                "best_oa_location": {"url_for_pdf": "https://pub.example/a.pdf", "license": "cc-by",
                                     "url_for_landing_page": "https://pub.example/a"},
                "oa_locations": [{"url_for_pdf": "https://pub.example/a.pdf"}, {"url_for_pdf": "https://repo.example/a.pdf"}]}
OPENALEX_OA = {"open_access": {"is_oa": True, "oa_status": "gold"},
               "best_oa_location": {"is_oa": True, "pdf_url": "https://repo.example/a.pdf"},
               "locations": [{"is_oa": True, "pdf_url": "https://other.example/a.pdf"}, {"is_oa": False, "pdf_url": "x"}],
               "primary_location": {"landing_page_url": "https://pub.example/a"}}


def test_the_lookup_prefers_unpaywalls_flag_and_lists_pdf_addresses_once():
    get = stub({"openalex": (200, OPENALEX_OA), "unpaywall": (200, UNPAYWALL_OA)})
    found = lk.lookup("10.1000/A", "doi:10.1000/a", get, pause=0)
    assert found.is_oa is True and found.flag_source == "unpaywall" and not found.flags_disagree
    assert found.pdf_candidates() == [("https://pub.example/a.pdf", "unpaywall"), ("https://repo.example/a.pdf", "unpaywall"),
                                      ("https://other.example/a.pdf", "openalex")]
    assert found.license == "cc-by" and found.oa_status == "gold"
    assert [e.action for e in found.log] == ["openalex_lookup", "unpaywall_lookup"]
    assert all("{contact}" in e.url and lk.CONTACT_EMAIL not in e.url for e in found.log)


def test_the_lookup_records_disagreement_and_failure():
    closed = {**UNPAYWALL_OA, "is_oa": False}
    found = lk.lookup("10.1000/A", "doi:10.1000/a", stub({"openalex": (200, OPENALEX_OA), "unpaywall": (200, closed)}), 0)
    assert found.is_oa is False and found.flags_disagree
    only_openalex = lk.lookup("10.1000/A", "doi:10.1000/a", stub({"openalex": (200, OPENALEX_OA), "unpaywall": (503, b"")}), 0)
    assert only_openalex.is_oa is True and only_openalex.flag_source == "openalex"
    assert only_openalex.log[1].outcome == "error" and only_openalex.log[1].http_status == 503
    neither = lk.lookup("10.1000/A", "doi:10.1000/a", stub({}), 0)
    assert neither.is_oa is None and [e.outcome for e in neither.log] == ["not_found", "not_found"]


def test_a_download_keeps_only_a_pdf_within_the_cap_and_records_every_attempt(monkeypatch):
    found = lk.lookup("10.1000/A", "doi:10.1000/a", stub({"openalex": (200, OPENALEX_OA), "unpaywall": (200, UNPAYWALL_OA)}), 0)
    got = lk.download(found, stub({"pub.example": (403, b""), "repo.example": (200, b"<html>login</html>", "text/html"),
                                   "other.example": (200, PDF, "application/pdf")}), 0)
    assert got.pdf == PDF and got.source == "openalex" and got.url == "https://other.example/a.pdf"
    assert [(e.outcome, e.http_status) for e in got.log] == [("refused", 403), ("failed", 200), ("ok", 200)]
    assert "not a PDF" in got.log[1].detail
    monkeypatch.setattr(lk, "DOCUMENT_MAX_BYTES", 5)
    too_big = lk.download(found, stub({"pub.example": (200, PDF)}), 0)
    assert too_big.pdf is None and any("larger than" in (e.detail or "") for e in too_big.log)
    none = lk.download(lk.lookup("10.1000/A", "doi:10.1000/a", stub({}), 0), stub({}), 0)
    assert none.pdf is None and [e.outcome for e in none.log] == ["not_found"]


def test_the_supplement_check_says_yes_or_not_found_by_automatic_check_never_none():
    found = lk.lookup("10.1000/A", "doi:10.1000/a", stub({"openalex": (200, OPENALEX_OA), "unpaywall": (200, UNPAYWALL_OA)}), 0)
    page = b'<html><a href="/doi/suppl/10.1000/a/mmc1.pdf">Supplementary data 1</a></html>'
    yes = lk.supplements(found, stub({"pub.example/a": (200, page, "text/html")}), 0)
    assert yes.found and yes.value == "yes" and yes.url == "https://pub.example/doi/suppl/10.1000/a/mmc1.pdf"
    no_link = lk.supplements(found, stub({"pub.example/a": (200, b"<html><a href='/x'>PDF</a></html>")}), 0)
    blocked = lk.supplements(found, stub({}), 0)
    for check in (no_link, blocked):
        assert not check.found and check.value == "not found by automatic check" != "none"
    assert lk.NOT_FOUND_BY_AUTOMATIC_CHECK == "not found by automatic check"


# --- the parser ------------------------------------------------------------------------------------------------------

def fake(name, tables=0, fail=False):
    def run(path):
        if fail:
            raise RuntimeError(f"{name} broke")
        return {"parser": name, "parser_version": "9", "pages": 2, "texts": [{"index": 0, "page": 1, "text": "x"}],
                "tables": [{"index": i, "page": 1, "caption": None, "rows": [["a"]]} for i in range(tables)]}
    return run


@pytest.mark.parametrize("docling,pymupdf,chosen,fallback,attempts", [
    (fake("docling", 2), fake("pymupdf", 1), "docling", False, 1),           # Docling found tables: pymupdf not tried
    (fake("docling", 0), fake("pymupdf", 1), "pymupdf", True, 2),            # no tables: pymupdf found some
    (fake("docling", 0), fake("pymupdf", 0), "docling", False, 2),           # neither found tables: Docling's text
    (fake("docling", fail=True), fake("pymupdf", 0), "pymupdf", True, 2),    # Docling failed
])
def test_docling_first_then_pymupdf_when_docling_fails_or_finds_no_tables(docling, pymupdf, chosen, fallback, attempts):
    result = parse_worker.parse("x.pdf", docling, pymupdf)
    assert result["status"] == "parsed" and result["parser"] == chosen and result["fallback_used"] is fallback
    assert result["format"] == parse_worker.FORMAT and len(result["attempts"]) == attempts


def test_the_attempts_are_listed_and_a_double_failure_is_a_failed_parse():
    first = parse_worker.parse("x.pdf", fake("docling", 2), fake("pymupdf", 1))
    assert [a["parser"] for a in first["attempts"]] == ["docling"]
    both = parse_worker.parse("x.pdf", fake("docling", fail=True), fake("pymupdf", fail=True))
    assert both["status"] == "failed" and [a["outcome"] for a in both["attempts"]] == ["failed", "failed"]
    assert "docling broke" in both["attempts"][0]["error"]


def test_the_canonical_json_is_byte_stable():
    a = parse_worker.canonical({"b": 1, "a": [{"z": "µm", "y": None}]})
    b = parse_worker.canonical({"a": [{"y": None, "z": "µm"}], "b": 1})
    assert a == b == '{"a":[{"y":null,"z":"µm"}],"b":1}'


def test_the_parse_worker_imports_only_the_standard_library_at_module_level():
    """So the parse environment needs nothing from the project, and the project needs no parser."""
    import ast
    tree = ast.parse(open(parse_worker.__file__, encoding="utf-8").read())
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    names = {a.name.split(".")[0] for n in top for a in n.names} | {n.module.split(".")[0] for n in top
                                                                     if isinstance(n, ast.ImportFrom) and n.module}
    assert names <= {"__future__", "json", "sys", "importlib", "annotations", "metadata"}, names


# --- end to end over two papers (stub network, fake parser) ----------------------------------------------------------

def two_papers():
    return Selection("mpea", "f" * 64, "microstructure", "PROPERTY: Microstructure", ("FCC",), (
        Paper("10.1000/A", "doi:10.1000/a", 3, 2, ("r1", "r2", "r3")),
        Paper("10.1000/B", "doi:10.1000/b", 1, 1, ("r4",))), 0)


def test_gather_parse_and_the_reach_table_over_two_papers(db):
    engine = db
    get = stub({"openalex.org/works/doi:10.1000/a": (200, OPENALEX_OA), "unpaywall.org/v2/10.1000/a": (200, UNPAYWALL_OA),
                "pub.example/a.pdf": (200, PDF), "pub.example/a": (200, b"<a href='s.zip'>Supplementary material</a>"),
                "openalex.org/works/doi:10.1000/b": (200, {"open_access": {"is_oa": False}}),
                "unpaywall.org/v2/10.1000/b": (200, {"is_oa": False})})
    said = []
    steps.gather(engine, two_papers(), get, pause=0, say=said.append)
    steps.gather(engine, two_papers(), get, pause=0, say=said.append)  # a second gather skips what is stored
    assert sum("skipped" in s for s in said) == 2
    steps.parse_all(engine, two_papers(), runner=lambda pdf: {**parse_worker.parse("x", fake("docling", 2)),
                                                              "pages": 2}, say=said.append)
    table = reach.rows(engine, two_papers())
    assert [r.doi_key for r in table] == ["doi:10.1000/a", "doi:10.1000/b"]
    a, b = table
    assert (a.oa_flag, a.downloaded, a.parsed, a.parser, a.tables_found, a.supplements) == \
        ("yes", "yes", "yes", "docling", 2, "yes")
    assert (b.oa_flag, b.downloaded, b.download_cause, b.parsed) == ("no", "no", "not_found: no open-access PDF address",
                                                                     "no document")
    assert b.supplements == "not found by automatic check"
    assert reach.milestones(table) == {
        "all": {"papers": 2, "records": 4}, "open_access_flag": {"papers": 1, "records": 3},
        "full_text_downloaded": {"papers": 1, "records": 3}, "fetched_by_hand": {"papers": 0, "records": 0},
        "text_and_tables_parsed": {"papers": 1, "records": 3},
        "supplements_available": {"papers": 1, "records": 3}}
    with engine.connect() as conn:
        actions = conn.execute(text("SELECT doi_key, action, outcome FROM search_log ORDER BY id")).all()
        parsed = conn.execute(text("SELECT parsed FROM document_parse")).scalar_one()
    assert ("doi:10.1000/a", "openalex_lookup", "found") in actions and ("doi:10.1000/a", "download", "ok") in actions
    assert ("doi:10.1000/a", "parse", "ok") in actions and ("doi:10.1000/b", "unpaywall_lookup", "found") in actions
    assert json.loads(parsed)["parser"] == "docling"
    csv_text = reach.to_csv(table)
    import csv as _csv
    rows = list(_csv.DictReader(csv_text.splitlines()))
    assert csv_text.splitlines()[0].startswith("doi,doi_key,compilation_records")
    assert all(r["supplements"] != "none" for r in rows)  # the supplements column never asserts 'none'
    assert [r["access_method"] for r in rows] == ["none", ""]  # access 'none' is a method, not an absence


def test_a_failed_parse_is_stored_with_its_reason(db):
    engine = db
    get = stub({"openalex.org": (200, OPENALEX_OA), "unpaywall.org": (200, UNPAYWALL_OA), "pub.example/a.pdf": (200, PDF)})
    one = Selection("mpea", "f" * 64, "microstructure", "PROPERTY: Microstructure", ("FCC",),
                    (Paper("10.1000/A", "doi:10.1000/a", 3, 2, ("r1",)),), 0)
    steps.gather(engine, one, get, pause=0, say=lambda s: None)
    steps.parse_all(engine, one, runner=lambda pdf: parse_worker.parse("x", fake("docling", fail=True),
                                                                       fake("pymupdf", fail=True)), say=lambda s: None)
    (row,) = reach.rows(engine, one)
    assert row.downloaded == "yes" and row.parsed.startswith("failed: docling: RuntimeError: docling broke")


def test_the_real_parse_runner_reports_a_missing_parse_environment():
    result = store.run_parser(PDF, python="/nonexistent/python")
    assert result["status"] == "failed"


def test_a_fetch_by_hand_records_the_url_the_person_and_why_automation_failed_and_is_shown_apart(db):
    """Owner, 2026-10-22: a by-hand fetch keeps the automated milestone as measured, is labelled, and its cause is
    'obtained by manual fetch (access: institutional_credential)'; no public/paywalled distinction (owner,
    2026-10-23)."""
    engine = db
    blocked = {**UNPAYWALL_OA, "best_oa_location": {"url_for_landing_page": "https://pub.example/a"}, "oa_locations": []}
    get = stub({"openalex.org/works/doi:10.1000/a": (200, {"open_access": {"is_oa": True}}),
                "unpaywall.org/v2/10.1000/a": (200, blocked),
                "openalex.org/works/doi:10.1000/b": (200, {"open_access": {"is_oa": False}}),
                "unpaywall.org/v2/10.1000/b": (200, {"is_oa": False})})
    steps.gather(engine, two_papers(), get, pause=0, say=lambda s: None)
    why = steps.why_automation_failed(engine, "doi:10.1000/a")
    assert why == "not_found: no open-access PDF address"
    with pytest.raises(ValueError, match="not a PDF"):
        store.add_by_hand(engine, "10.1000/A", "doi:10.1000/a", b"<html>", "https://pub.example/a.pdf", why, "K")
    doc = store.add_by_hand(engine, "10.1000/A", "doi:10.1000/a", PDF, "https://pub.example/a/pdf", why,
                            "Khalid El-Awady")
    a, b = reach.rows(engine, two_papers())
    assert (a.oa_flag, a.downloaded, a.fetched_by_hand, a.access_cause, a.document_id) == \
        ("yes", "no", "yes", "obtained by manual fetch (access: institutional_credential)", doc)
    assert a.access_method == "institutional_credential"
    assert b.access_cause == "not obtained under the configured sources" and b.access_method is None
    assert "paywalled" not in reach.to_csv([a, b]) and "open access" not in a.access_cause
    assert reach.milestones([a, b])["full_text_downloaded"]["papers"] == 0
    assert reach.milestones([a, b])["fetched_by_hand"]["papers"] == 1
    with engine.connect() as conn:
        entry = conn.execute(text("SELECT url, actor, by_hand, detail, document_id FROM search_log "
                                  "WHERE action = 'fetch_by_hand'")).one()
        stored = conn.execute(text("SELECT oa_source, by_hand, fetched_by, oa_url FROM document WHERE id = :d"),
                              dict(d=doc)).one()
    assert entry.url == "https://pub.example/a/pdf" and entry.actor == "Khalid El-Awady" and entry.by_hand
    assert entry.detail == ("obtained by manual fetch (access: institutional_credential); "
                            "automation: not_found: no open-access PDF address") and entry.document_id == doc
    assert tuple(stored) == ("by_hand", True, "Khalid El-Awady", "https://pub.example/a/pdf")


def test_publisher_patterns_for_tandf_and_mdpi_and_none_for_elsevier():
    cands, log = lk.publisher_patterns("doi:10.1080/21663831.2018.1553803", stub({}), 0)
    assert cands == [("https://www.tandfonline.com/doi/pdf/10.1080/21663831.2018.1553803?download=true", "pattern:tandf")]
    cands, log = lk.publisher_patterns("doi:10.3390/coatings9010016",
                                       lambda url, accept="*/*": lk.Response(url, 200, b"", "text/html",
                                                                             "https://www.mdpi.com/2079-6412/9/1/16"), 0)
    assert cands == [("https://www.mdpi.com/2079-6412/9/1/16/pdf", "pattern:mdpi")] and log[0].outcome == "found"
    cands, log = lk.publisher_patterns("doi:10.3390/coatings9010016", stub({}), 0)
    assert cands == [] and log[0].outcome == "failed" and "landing page not reached" in log[0].detail
    assert lk.publisher_patterns("doi:10.1016/j.actamat.2018.12.012", stub({}), 0) == ([], [])
