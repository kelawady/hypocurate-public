"""Sprint 2 pilot, R5 and R10: the owner's review sheet (owner, 2026-10-23; register 'pilot_review_sheet').

The export lists every open item for the owner, sorted by paper, then page, table and row, with a minutes cell per
paper; decided items are not listed again. The loader stores the file with its hash and turns each decision into a
state event by the owner (accept -> accepted, reject -> disputed, correct -> accepted with the correction in the
reason), each value correction into a value_correction (the value as read unchanged), each finding into an
auditor_finding and each minutes row into an owner_time_log. A file with any unreadable row is refused whole, listing
every problem, and nothing is written."""
from __future__ import annotations

import hashlib
import io

import pytest
from openpyxl import load_workbook
from sqlalchemy import text

from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline import review_sheet as rs
from hypocurate.pipeline.extraction import s0
from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
from hypocurate.pipeline.extraction.interface import EvidenceSpec, ParsedDocument

DOI = "10.1016/j.ijplas.2018.10.005"
PV = "none"  # the fixture extractor's prompt version
PARSED = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
          "pages": 8, "attempts": [],
          "texts": [{"index": 0, "page": 6, "text": "The alloys were annealed."}],
          "tables": [{"index": 0, "page": 6, "caption": "Table 1",
                      "rows": [["Alloy", "State", "Grain size (µm)", "Yield strength (MPa)"],
                               ["Cr20Fe6Co34Ni34Mo6", "700 °C 1 h", "0.8", "1100"],
                               ["Cr20Fe6Co34Ni34Mo6", "900 °C 1 h", "5.1", "640"]]}]}


@pytest.fixture
def sheet(db):
    pdf = b"%PDF-1.7\n% review sheet test\n"
    body = canonical(PARSED)
    with db.begin() as conn:
        doc = conn.execute(text("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand, "
                                "access_method, access_note) VALUES (:d, :k, 'by_hand', :p, :h, 'K. El-Awady', true, "
                                "'institutional_credential', 'fetched manually') RETURNING id"),
                           dict(d=DOI, k="doi:" + DOI, p=pdf, h=hashlib.sha256(pdf).hexdigest())).scalar_one()
        parse_id = conn.execute(text(
            "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
            "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 8, 1) "
            "RETURNING id"), dict(d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())).scalar_one()
    with db.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    f = s0.store_and_freeze(db, document, FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1")))
    with db.begin() as conn:
        obs = conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x ORDER BY item_index"),
                           dict(x=f.output_id)).scalars().all()
        mappings = []
        for o, kind, subject, state in ((obs[1], "condition_to_category", "900 °C 1 h", "proposed"),
                                        (obs[0], "alias_to_composition", "Cr20Fe6Co34Ni34Mo6", "proposed"),
                                        (obs[0], "column_to_field", "State", "unresolved")):
            m = conn.execute(text("INSERT INTO reconciler_mapping (extraction_output_id, observation_id, kind, subject, "
                                  "proposed, applied, mapping_version) VALUES (:x, :o, :k, :s, '{}', '{\"ok\": true}', "
                                  "'reconcile-v1') RETURNING id"), dict(x=f.output_id, o=o, k=kind, s=subject)).scalar_one()
            conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, "
                              "by_rule, reason) VALUES ('mapping', :m, :x, :s, 'reconciler', NULL)"),
                         dict(m=m, x=f.output_id, s=state))
            mappings.append(m)
    return f.output_id, obs, mappings


def _book(content: bytes):
    return load_workbook(io.BytesIO(content))


def _save(wb) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_the_export_lists_open_items_by_paper_then_page_table_row_with_minutes_and_repair_candidates(db, sheet):
    out, obs, (m_row2, m_row1, m_unres) = sheet
    wb = _book(rs.export(db, prompt_version=PV))
    assert wb.sheetnames == ["Proposals", "Corrections", "Findings", "Repair candidates", "Minutes", "Read me"]
    rows = list(wb["Proposals"].iter_rows(values_only=True))
    assert rows[0] == rs.PROPOSAL_COLUMNS
    items = [r[0] for r in rows[1:]]
    # sorted by location: row 1's two mappings (in id order) before row 2's; the same-table-row links are not listed
    assert items == [f"mapping:{m_row1}", f"mapping:{m_unres}", f"mapping:{m_row2}"]
    assert all(r[1] == DOI and r[2].startswith("p. 6, table 0") for r in rows[1:])
    assert all(r[9] is None for r in rows[1:])  # the owner's cells are empty
    assert [tuple(r) for r in wb["Minutes"].iter_rows(values_only=True)][1:] == [(DOI, "review_sheet", None)]
    repair = list(wb["Repair candidates"].iter_rows(values_only=True))[1:]
    assert {r[0] for r in repair} == {f"observation:{o}" for o in obs}  # neither test type nor temperature stated
    assert all(r[3] == "test_type, test_temperature" for r in repair)
    assert [c for c in next(wb["Corrections"].iter_rows(values_only=True))] == list(rs.CORRECTION_COLUMNS)


def _filled(db, sheet):
    out, obs, (m_row2, m_row1, m_unres) = sheet
    wb = _book(rs.export(db, prompt_version=PV))
    ws = wb["Proposals"]
    for r in range(2, ws.max_row + 1):
        item = ws.cell(r, 1).value
        d = {f"mapping:{m_row1}": ("accept", "", ""), f"mapping:{m_unres}": ("reject", "", "the State column is the "
             "processing state, not a field"), f"mapping:{m_row2}": ("correct", "annealed 900 °C, 1 h", "as in the text")}[item]
        for c, v in zip((10, 11, 12), d):
            ws.cell(r, c).value = v or None
    wb["Corrections"].append([f"observation:{obs[1]}", "grain_size", "5.7", "µm", "Table 1 reads 5.7; the parse dropped a digit"])
    wb["Findings"].append([f"observation:{obs[0]}", "missing_context", "search_target", "the test temperature is not stated"])
    wb["Minutes"]["C2"] = 17
    return wb, out, obs, (m_row2, m_row1, m_unres)


def test_the_loader_turns_decisions_corrections_findings_and_minutes_into_rows_by_the_owner(db, sheet):
    wb, out, obs, (m_row2, m_row1, m_unres) = _filled(db, sheet)
    content = _save(wb)
    with db.connect() as conn:
        before = conn.execute(text("SELECT id, value_text FROM candidate_value WHERE observation_id = :o AND "
                                   "field = 'grain_size'"), dict(o=obs[1])).one()
    loaded = rs.load(db, "review_KE_v1.xlsx", content, "K. El-Awady", prompt_version=PV)
    assert (loaded.decisions, loaded.corrections, loaded.findings, loaded.minutes_rows) == (3, 1, 1, 1)
    with db.connect() as conn:
        rf = conn.execute(text("SELECT sha256, loaded_by FROM review_file WHERE id = :i"), dict(i=loaded.review_file)).one()
        assert rf == (hashlib.sha256(content).hexdigest(), "K. El-Awady")
        events = {r.object_id: r for r in conn.execute(text(
            "SELECT DISTINCT ON (object_id) object_id, state, by_person, by_rule, reason FROM evidence_state_event "
            "WHERE object_kind = 'mapping' ORDER BY object_id, id DESC")).all()}
        assert (events[m_row1].state, events[m_row1].by_person, events[m_row1].by_rule) == ("accepted", "K. El-Awady", None)
        assert events[m_unres].state == "disputed" and "processing state" in events[m_unres].reason
        assert events[m_row2].state == "accepted" and events[m_row2].reason.startswith("corrected: annealed 900 °C, 1 h")
        vc = conn.execute(text("SELECT value_id, corrected_text, unit, reason, by_person FROM value_correction")).one()
        assert (vc.value_id, vc.corrected_text, vc.unit, vc.by_person) == (before.id, "5.7", "µm", "K. El-Awady")
        after = conn.execute(text("SELECT value_text FROM candidate_value WHERE id = :v"), dict(v=before.id)).scalar()
        assert after == before.value_text  # the value as read is never changed
        f = conn.execute(text("SELECT object_kind, object_id, finding_kind, consequence, review_file_id "
                              "FROM auditor_finding")).one()
        assert tuple(f) == ("observation", obs[0], "missing_context", "search_target", loaded.review_file)
        t = conn.execute(text("SELECT doi_key, activity, minutes, review_file_id FROM owner_time_log")).one()
        assert tuple(t) == ("doi:" + DOI, "review_sheet", 17, loaded.review_file)
    # decided items are not listed again
    again = list(_book(rs.export(db, prompt_version=PV))["Proposals"].iter_rows(values_only=True))[1:]
    assert again == []


def test_a_file_with_any_unreadable_row_is_refused_whole_and_nothing_is_written(db, sheet):
    wb, out, obs, _ = _filled(db, sheet)
    ws = wb["Proposals"]
    ws.cell(2, 10).value = "maybe"                                # not a decision
    ws.cell(3, 10).value, ws.cell(3, 12).value = "reject", None   # a rejection without a reason
    wb["Corrections"].append([f"observation:{obs[0]}", "strain_rate", "1e-3", "", "not read"])  # no such value
    wb["Findings"].append([f"observation:{obs[0]}", "bad_kind", "search_target", "x"])
    wb["Minutes"]["C2"] = 2000
    with pytest.raises(rs.SheetRefused) as e:
        rs.load(db, "review_KE_v1.xlsx", _save(wb), "K. El-Awady", prompt_version=PV)
    problems = e.value.problems
    assert len(problems) == 5
    assert any("'maybe'" in p for p in problems) and any("needs a reason" in p for p in problems)
    assert any("is a repair, not a correction" in p for p in problems)
    assert any("not in the lists" in p for p in problems) and any("0 to 1440" in p for p in problems)
    with db.connect() as conn:
        for t in ("review_file", "value_correction", "auditor_finding", "owner_time_log"):
            assert conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM evidence_state_event WHERE by_person IS NOT NULL")).scalar() == 0


def test_a_sheet_whose_columns_differ_from_the_exports_is_refused(db, sheet):
    wb = _book(rs.export(db, prompt_version=PV))
    wb["Proposals"].cell(1, 10).value = "verdict"
    with pytest.raises(rs.SheetRefused, match="columns differ"):
        rs.load(db, "review_KE_v1.xlsx", _save(wb), "K. El-Awady", prompt_version=PV)


def _cli(argv):
    import argparse
    from hypocurate.documents import cli
    parser = argparse.ArgumentParser()
    cli.add_parser(parser.add_subparsers(dest="command"))
    return cli, parser.parse_args(argv)


def test_the_cli_reconciles_the_newest_s0_of_the_prompt_version_and_round_trips_the_sheet(db, sheet, tmp_path,
                                                                                        monkeypatch, capsys):
    out, obs, _ = sheet
    from hypocurate.sources import versions
    versions.register(db, "mpea")  # the documents commands read the selection first
    monkeypatch.setattr(rs, "PROMPT_VERSION", PV)
    from hypocurate.pipeline import evidence
    monkeypatch.setattr(evidence, "PROMPT_VERSION", PV)  # the reconcile command reads the standing S0 from there
    import hypocurate.pipeline.reconcile as rc
    called = []
    monkeypatch.setattr(rc, "reconcile", lambda engine, output: called.append(output) or rc.ReconcileRun(output))
    cli, args = _cli(["documents", "reconcile", "--doi", DOI.upper()])
    assert cli.command(args, db) == 0 and called == [out]
    cli, args = _cli(["documents", "reconcile", "--doi", "10.1016/j.actamat.2099.01.001"])
    assert cli.command(args, db) == 1 and "no none S0" in capsys.readouterr().err
    path = tmp_path / "review_KE_v1.xlsx"
    cli, args = _cli(["documents", "review-export", "--out", str(path)])
    assert cli.command(args, db) == 0
    wb = _book(path.read_bytes())
    wb["Proposals"].cell(2, 10).value = "maybe"
    path.write_bytes(_save(wb))
    cli, args = _cli(["documents", "review-load", "--file", str(path), "--by", "K. El-Awady"])
    assert cli.command(args, db) == 1 and "'maybe'" in capsys.readouterr().err
    wb["Proposals"].cell(2, 10).value = "accept"
    path.write_bytes(_save(wb))
    assert cli.command(args, db) == 0 and '"decisions": 1' in capsys.readouterr().out


def test_minutes_that_are_not_owner_time_are_not_logged_and_the_file_is_kept_whole(db, sheet):
    """Owner, 2026-10-23: an AI-assisted review's Minutes tab (fractional AI minutes) is not owner time."""
    wb, out, obs, _ = _filled(db, sheet)
    wb["Minutes"]["C2"] = 1.4  # refused as owner time
    content = _save(wb)
    with pytest.raises(rs.SheetRefused, match="whole number"):
        rs.load(db, "review_KE_v1.xlsx", content, "K. El-Awady", prompt_version=PV)
    loaded = rs.load(db, "review_KE_v1.xlsx", content, "K. El-Awady", prompt_version=PV, minutes_are_owner_time=False)
    assert (loaded.decisions, loaded.minutes_rows) == (3, 0)
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM owner_time_log")).scalar() == 0
        assert conn.execute(text("SELECT sha256 FROM review_file")).scalar() == hashlib.sha256(content).hexdigest()
