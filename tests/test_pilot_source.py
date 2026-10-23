"""Sprint 2 pilot, R9: the 'extracted (pilot)' source built from the R6 freeze, its adapter, the plan for a run that
uses it, and the augmented pool through Sprint 1's own checks, inclusion, freeze and statistics (re-reports counted
once, the MPEA record surviving). Every model call goes to the local stub provider."""
from __future__ import annotations

import csv
import io
import json
from datetime import date

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import evidence as ev
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline.confirmation import reference_plan
from hypocurate.sources import adapters, pilot
from hypocurate.sources.versions import _register_in, latest_sealed_version_id, load_sealed_version
from test_evidence import COMPILATION, OWNER, _person, paper  # noqa: F401 (the fixture)
from test_orchestrator import FCC_CLAIM, responder


def test_a_plan_without_the_pilot_source_is_unchanged_and_with_it_the_source_comes_last():
    base = plans.reference_plan(7)
    assert plans.with_pilot_sources(plans.reference_plan(7), ("mpea", "tamu_fcc")) == base
    row = type("Row", (), {"hypothesis_version_id": 7, "sufficiency_option": "fixed_minimum"})
    assert reference_plan(row) == base
    p = reference_plan(row, ("mpea", "extracted_pilot"))
    assert p["rules"]["survivor_source_order"] == base["rules"]["survivor_source_order"] + ["extracted_pilot"]
    assert p["rules"]["grouping"][-1] == {"source": "extracted_pilot", "unit": "paper"}
    plans.validate(p)  # the plan schema accepts the pilot source


def test_the_source_is_built_from_the_freeze_and_read_by_its_adapter(db, paper):  # noqa: F811
    p = paper
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    ev.apply_rules(db, p.outputs)
    frozen = ev.freeze(db, p.outputs, OWNER, COMPILATION)
    sealed = pilot.register_frozen(db, frozen, OWNER)
    assert sealed.registered.created and pilot.register_frozen(db, frozen, OWNER).registered.created is False
    record = json.loads(sealed.files[pilot.FREEZE_FILE])
    assert record["s2_events_sha256"] == frozen.events_sha256 and record["accepted_records"] == sorted(p.obs[:3])
    assert record["rereport_of"] == {str(p.obs[0]): "rec:0", str(p.obs[1]): "rec:1"}
    assert record["primary_set_new_records"] == [p.obs[2]]
    with db.connect() as conn:
        version = load_sealed_version(conn, latest_sealed_version_id(conn, pilot.KEY))
    records = adapters.read(version).records
    assert [r.source_item_key for r in records] == [f"extracted_pilot.csv:observation:{o}" for o in sorted(p.obs[:3])]
    new = records[2].harmonized
    assert (new["grain_size"].value, new["yield_strength"].value) == (5.0, 500.0)
    assert new["grain_size"].status == "converted"
    assert (new["composition"].status, new["composition"].reason) == ("not_reported", "no accepted composition mapping")
    assert records[0].reported["rereport_of"].text == "rec:0"
    rows = list(csv.DictReader(io.StringIO(sealed.files[pilot.DATA_FILE].decode())))
    assert rows[2]["grain_size_provenance"] == "p. 2, table 0, row 3"


def test_temperatures_are_converted_only_when_one_is_stated():
    assert pilot.temperature_c("293 K") == pilot.temperature_c("19.85 °C")
    assert pilot.temperature_c("77, 293, 473 K") is None and pilot.temperature_c("room temperature") is None


# --- The augmented pool through Sprint 1's pipeline -------------------------------------------------------------
DOI = "10.1016/j.actamat.2018.12.012"
QUOTE = "tensile tests at room temperature"


def _row(key, gs, ys, rereport=""):
    return {"record_key": key, "paper_doi": DOI, "alloy_as_written": "Al0.1CoCrFeNi",
            "composition_formula": "Al0.1Co1Cr1Fe1Ni1", "composition_quote": "Al0.1CoCrFeNi",
            "grain_size_um": gs, "grain_size_as_written": f"{gs} µm", "grain_size_provenance": "p. 3, table 1, row 1",
            "yield_strength_mpa": ys, "yield_strength_as_written": f"{ys} MPa",
            "yield_strength_provenance": "p. 3, table 1, row 1", "test_type": "tension", "test_type_quote": QUOTE,
            "test_temperature_c": "25", "test_temperature_as_written": "25 °C", "test_temperature_band": "",
            "test_temperature_band_quote": "", "phase": "FCC", "phase_quote": "single-phase FCC",
            "processing_state": "annealed", "document_sha256": "ab" * 32,
            "link_provenance": "same_table_row: p. 3, table 1, row 1; accepted by rule r-link-1",
            "extraction_method": "model_extractor 1, prompt v4", "rereport_of": rereport,
            "values_agree": "True" if rereport else "", "qualifiers": ""}


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea",))
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=pilot.COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows([_row("observation:1", "7", "356", "MPEA_dataset.csv:row:755"),  # a re-report of an MPEA record
                 _row("observation:2", "50", "300")])                            # new, same alloy and paper
    states = [{"observation": 1, "paper": "doi:" + DOI, "state": "accepted", "reason": "", "rereport_of":
               "MPEA_dataset.csv:row:755", "qualifiers": []},
              {"observation": 2, "paper": "doi:" + DOI, "state": "accepted", "reason": "", "rereport_of": None,
               "qualifiers": []},
              {"observation": 3, "paper": "doi:" + DOI, "state": "proposed", "reason": "figure-only yield strength",
               "rereport_of": None, "qualifiers": []}]
    files = {pilot.DATA_FILE: buf.getvalue().encode(), pilot.FREEZE_FILE: b"{}\n",
             pilot.STATES_FILE: json.dumps(states).encode()}
    with e.begin() as conn:
        _register_in(conn, pilot.DEFINITION, files, date(2026, 10, 23), "test freeze")
    yield e
    e.dispose()


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def _run(engine, stub, sources, sufficiency="fixed_minimum"):
    q = queries.create(engine, FCC_CLAIM, sources, sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
    return rid, orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def test_the_augmented_pool_counts_a_re_report_once_with_the_mpea_record_surviving(engine, stub):
    stub.respond(responder())
    rid, report = _run(engine, stub, ("mpea", "extracted_pilot"))
    assert (report.status, report.failure) == ("completed", None)
    with engine.connect() as conn:
        n = conn.execute(text("SELECT n_records FROM analysis_result WHERE run_id = :r AND scope = 'pooled'"),
                         dict(r=rid)).scalar()
        decisions = dict(conn.execute(text(
            "SELECT r.source_item_key, e.rule FROM run_record e JOIN record r ON r.id = e.record_id "
            "JOIN source_version v ON v.id = r.source_version_id JOIN source s ON s.id = v.source_id "
            "WHERE e.run_id = :r AND s.key = 'extracted_pilot'"), dict(r=rid)).all())
    assert n == 77  # MPEA's 76 and the one new record; the re-report counted once
    assert decisions == {"extracted_pilot.csv:observation:1": "duplicate_counted_once",
                         "extracted_pilot.csv:observation:2": "in_scope"}


def test_numbers_are_written_in_plain_notation():
    from decimal import Decimal
    assert [pilot.plain(Decimal(x).normalize()) for x in ("20", "2.50", "0.80", "289.7", "-196.0")] == [
        "20", "2.5", "0.8", "289.7", "-196"]


def test_the_augmented_pool_agrees_with_the_independent_test_side_calculation(engine, stub):
    """PRD v1.2 R9: the augmented pool's estimate equals an independent calculation on its frozen records."""
    from pilot_independent import compare
    stub.respond(responder())
    rid, report = _run(engine, stub, ("mpea", "extracted_pilot"))
    from hypocurate.pipeline import costs
    with engine.connect() as conn:
        result = compare(conn, rid)
        (spent,) = costs.per_run(conn, [rid])  # R15: the run's calls and stage times from stored rows
        calls = conn.execute(text("SELECT count(*) FROM model_call WHERE run_id = :r"), dict(r=rid)).scalar()
    assert result["agree"] and result["package"][0] == 77
    assert spent["calls"] == calls > 0 and spent["cost_usd"] > 0
    assert {s["stage"] for s in spent["stages"]} >= {"inclusion", "statistics"} and all(s["seconds"] >= 0
                                                                                       for s in spent["stages"])


def test_the_workbook_has_the_provenance_columns_and_the_states_sheet_only_for_a_pilot_run(engine, stub):
    """PRD v1.2 R12, and the owner's rule of 2026-10-23: observations counted by state with the reason."""
    from openpyxl import load_workbook
    from hypocurate.pipeline import workbook
    stub.respond(responder())
    rid, _ = _run(engine, stub, ("mpea", "extracted_pilot"))
    wb = load_workbook(io.BytesIO(workbook.build(engine, rid)))
    assert wb.sheetnames == [*workbook.SHEETS, workbook.PILOT_SHEET]
    used = list(wb["Records used"].iter_rows(values_only=True))
    header = list(used[1])
    assert header[len(workbook.BASE_COLUMNS):len(workbook.BASE_COLUMNS) + 5] == list(workbook.PILOT_COLUMNS)
    pilot_rows = [dict(zip(header, r)) for r in used[2:] if r[1] == "extracted_pilot"]
    assert [r["compilation match"] for r in pilot_rows] == ["new"]
    assert pilot_rows[0]["value provenance"] == "grain size: p. 3, table 1, row 1 | yield strength: p. 3, table 1, row 1"
    assert pilot_rows[0]["link provenance"].startswith("same_table_row: p. 3, table 1, row 1")
    assert pilot_rows[0]["extraction method"] == "model_extractor 1, prompt v4"
    other = [dict(zip(list(wb["Records not used"].iter_rows(values_only=True))[1], r))
             for r in list(wb["Records not used"].iter_rows(values_only=True))[2:]]
    rerep = [r for r in other if r["source"] == "extracted_pilot"]
    assert [(r["compilation match"], r["rule"]) for r in rerep] == [
        ("re-report (matched compilation record MPEA_dataset.csv:row:755)", "duplicate counted once")]
    states = [r[:3] for r in wb[workbook.PILOT_SHEET].iter_rows(values_only=True)]
    assert ("proposed", "figure-only yield strength", 1) in states and ("accepted", "new", 1) in states
    mpea_only, _ = _run(engine, stub, ("mpea",))
    plain = load_workbook(io.BytesIO(workbook.build(engine, mpea_only)))
    assert plain.sheetnames == list(workbook.SHEETS)
    assert not set(workbook.PILOT_COLUMNS) & set(list(plain["Records used"].iter_rows(values_only=True))[1])
