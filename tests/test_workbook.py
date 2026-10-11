"""Step 10b: the workbook and the records CSV (PRD 11), built on request from stored rows, for every outcome; the
website's download and the command line's `export` give the same content; each states the code version that built
it; its totals equal the run's recorded model calls (criterion 14.5)."""
from __future__ import annotations

import csv
import io
import json
from decimal import Decimal

import pytest
from openpyxl import load_workbook
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries, workbook
from test_web_runs import make_client, signed_in


@pytest.fixture(scope="module")
def world(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    url = url_for(database_url, name)
    engine = make_engine(url)
    stub = sp.StubProvider()
    try:
        pw.registered(engine, ("mpea", "tamu_fcc"))
        stub.respond(to.responder())
        reference = to.dispatched(engine, fixed_plan=True)
        assert to.run(engine, reference, stub).status == "completed"
        stub.respond(to.responder(to.BCC))
        insufficient = to.dispatched(engine, claim=to.BCC_CLAIM)
        assert to.run(engine, insufficient, stub).status == "completed"
        cancelled = to.dispatched(engine, fixed_plan=True)
        queries.cancel(engine, cancelled, by="Ada Reviewer")
        yield engine, url, {"reference": reference, "insufficient": insufficient, "cancelled": cancelled}
    finally:
        stub.close()
        engine.dispose()
        _drop(admin, name)


def sheets(data: bytes) -> dict[str, list[tuple]]:
    wb = load_workbook(io.BytesIO(data), read_only=True)
    return {ws.title: [tuple(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}


def items(rows) -> dict:
    return {r[0]: r[1] for r in rows[2:]}


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test(world):
    engine, _, runs = world
    s = sheets(workbook.build(engine, runs["reference"]))
    assert list(s) == list(workbook.SHEETS)
    for rows in s.values():
        assert rows[0][0] == workbook.version_line()
    used, other = s["Records used"], s["Records not used"]
    header = used[1]
    ids = {r[header.index("record")] for r in used[2:]}
    with engine.connect() as conn:
        primary = set(conn.execute(text(
            "SELECT asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
            "WHERE a.run_id = :r AND a.key = 'primary'"), dict(r=runs["reference"])).scalars())
    assert ids == primary and len(ids) == 97
    found = one(engine, "SELECT count(*) FROM record WHERE extraction_run_id = :r", r=runs["reference"])
    assert len(other) - 2 == found - 97
    assert {"rule", "flags", "sensitivity sets", "eligible"} <= set(other[1])
    for field in ("grain_size", "grain_size unit", "grain_size status", "yield_strength", "values as reported"):
        assert field in header
    summary = items(s["Run summary"])
    assert summary["Outcome"] == "sufficient in the sources searched"
    assert summary["Rules lock"].startswith("20") and "fingerprint" in summary["Dataset freeze"]
    assert "424.9 MPa·µm^0.5 ± 64.4 MPa·µm^0.5" in summary["Result: All sources together"]
    significance = s["Significance and commentary"]
    assert any(r[1] == workbook.COMMENTARY_NONE for r in significance)
    assert any(str(r[0]).startswith("Calibration (estimated)") for r in significance)


def test_the_workbooks_totals_equal_the_recorded_model_calls(world):
    """Criterion 14.5: the totals equal the sum of the recorded model calls."""
    engine, _, runs = world
    with engine.connect() as conn:
        n, cost = conn.execute(text("SELECT count(*), coalesce(sum(cost), 0) FROM model_call WHERE run_id = :r"),
                               dict(r=runs["reference"])).one()
    total = items(sheets(workbook.build(engine, runs["reference"]))["Run summary"])["Total"]
    assert total.startswith(f"{n} model call") and f"reported ${Decimal(cost):.6f}" in total


@pytest.mark.parametrize("which", ["insufficient", "cancelled"])
def test_every_outcome_has_a_workbook(world, which):
    engine, _, runs = world
    s = sheets(workbook.build(engine, runs[which]))
    assert list(s) == list(workbook.SHEETS) and len(s["Records used"]) == 2  # no record in a test
    summary = items(s["Run summary"])
    assert summary["Dataset freeze"] == "not reached"
    if which == "cancelled":
        assert summary["Failure"].startswith("The run was cancelled by Ada Reviewer")


def test_the_records_csv_has_one_row_per_record_found(world):
    engine, _, runs = world
    rows = list(csv.reader(io.StringIO(workbook.records_csv(engine, runs["reference"]))))
    assert rows[0] == [f"# {workbook.version_line()}"]
    body = rows[2:]
    assert len(body) == one(engine, "SELECT count(*) FROM record WHERE extraction_run_id = :r", r=runs["reference"])
    assert sum(1 for r in body if r[rows[1].index("used in the test")] == "yes") == 97


def test_the_same_stored_rows_give_the_same_workbook_and_it_names_the_code_version(world, monkeypatch):
    engine, _, runs = world
    assert sheets(workbook.build(engine, runs["reference"])) == sheets(workbook.build(engine, runs["reference"]))
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123abcd")
    assert sheets(workbook.build(engine, runs["reference"]))["Run summary"][0][0] == \
        "Workbook format 1; built by code version 0123abcd."


def test_the_website_download_and_the_command_lines_export_give_the_same_workbook(world, tmp_path, monkeypatch, capsys):
    from hypocurate import cli
    engine, url, runs = world
    rid = runs["reference"]
    assert make_client(engine, url).get(f"/runs/{rid}/workbook").status_code == 303  # needs the login
    r = signed_in(engine, url).get(f"/runs/{rid}/workbook")
    assert r.status_code == 200 and r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert f'filename="hypocurate-run-{rid}.xlsx"' in r.headers["content-disposition"]
    monkeypatch.setenv("DATABASE_URL", url)
    out = tmp_path / "run.xlsx"
    assert cli.main(["export", str(rid), "--out", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["written"] == str(out)
    assert sheets(out.read_bytes()) == sheets(r.content)
    csv_out = tmp_path / "run.csv"
    assert cli.main(["export", str(rid), "--out", str(csv_out), "--csv"]) == 0
    assert csv_out.read_text(encoding="utf-8") == signed_in(engine, url).get(f"/runs/{rid}/records.csv").text
    assert cli.main(["export", "999999", "--out", str(tmp_path / "x")]) == 1
