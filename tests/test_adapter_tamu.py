"""Step 4: the Texas A&M adapter on the frozen spreadsheet, and on planted rows.

Assigned values (owner, step 4 question 3) are set only where the source's own paper
states them, always with the passage, and stay distinguishable from reported values.
The test temperature is not stated, so it is not reported."""
import csv
import dataclasses
import io
import json
from collections import Counter
from pathlib import Path

import openpyxl
import pytest

from hypocurate.sources import adapters
from hypocurate.sources.adapters import tamu_fcc
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, Reported
from source_helpers import sealed, sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
XLSX = REPO / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
INPUTS = REPO / "data/sources/tamu_fcc/inputs.csv"
FILE = "Grain_Size_Summary_v3.xlsx"


@pytest.fixture(scope="module")
def records():
    result = adapters.read(sealed_from_disk("tamu_fcc"))
    assert result.blank_rows == ()
    return result.records


@pytest.fixture(scope="module")
def sheet_rows():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    rows = list(wb[tamu_fcc.SHEET].iter_rows(values_only=True))
    wb.close()
    return rows[1:]


def test_one_record_per_sample_none_dropped(records, sheet_rows):
    assert len(sheet_rows) == len(records) == 94
    assert [r.source_item_key for r in records] == [f"{FILE}:row:{i}" for i in range(94)]
    assert all(r.source_key == "tamu_fcc" and r.kind == "measured" and r.item_index == 0 for r in records)


def test_every_value_is_kept_as_reported(records, sheet_rows):
    for record, row in zip(records, sheet_rows):
        assert list(record.reported) == list(tamu_fcc.HEADER)
        assert [r.text for r in record.reported.values()] == [tamu_fcc.reported_text(v) for v in row]
    units = records[0].reported
    assert (units["Grain Size(µm)"].unit, units["YS (MPa)"].unit, units["Hardness, HV"].unit) == ("µm", "MPa", "HV")
    assert units["Al"].unit is None  # the header states none; the paper does (citation on the value)


def test_the_sample_without_yield_strength_is_kept(records):
    missing = [r for r in records if r.harmonized["yield_strength"].status != "converted"]
    assert [r.reported["Alloy Name"].text for r in missing] == ["BBA09"]
    assert missing[0].harmonized["yield_strength"].reason == "blank in the source"
    assert missing[0].harmonized["grain_size"].status == "converted"


def test_one_group_the_dataset(records):
    assert {r.group.key for r in records} == {"dataset:10.5281/zenodo.22798856"}
    assert {r.group.unit for r in records} == {"dataset"}
    assert {r.paper_reference for r in records} == {tamu_fcc.DATASET_REFERENCE}
    assert {r.paper_doi for r in records} == {None}
    # The batch is kept as reported, for the owner's grouping decision (PRD 17, decision 9).
    assert Counter(r.reported["Iteration"].text for r in records) == {
        "CBA": 23, "CBC": 21, "BBA": 18, "CBB": 15, "BBB": 9, "BBC": 8}


def test_assigned_values_carry_their_passage(records):
    for r in records:
        t, p = r.harmonized["test_type"], r.harmonized["phase_class"]
        assert (t.value, t.status, t.citation) == ("tension", "assigned", tamu_fcc.TEST_TYPE_CITATION)
        assert (p.value, p.status, p.citation) == ("FCC", "assigned", tamu_fcc.PHASE_CITATION)
        assert "Quasistatic tensile testing" in t.citation.quote and t.citation.location.startswith("line 177")
        assert "94 FCC alloy conditions" in p.citation.quote
        out = r.to_json()["harmonized"]
        assert out["test_type"]["status"] == "assigned" and out["test_type"]["citation"]["quote"]
    assigned = {k for r in records for k, v in r.harmonized.items() if v.status == "assigned"}
    assert assigned == {"test_type", "phase_class"}


def test_assigned_and_reported_stay_distinguishable(records):
    for r in records:
        for v in r.harmonized.values():
            assert (v.status == "assigned") <= (v.citation is not None)
        assert all(isinstance(rep, Reported) and not hasattr(rep, "citation") for rep in r.reported.values())
        assert "tension" not in {rep.text for rep in r.reported.values()}


def test_temperature_is_not_reported(records):
    for r in records:
        for name in ("test_temperature", "test_temperature_band"):
            v = r.harmonized[name]
            assert (v.status, v.value) == ("not_reported", None)
            assert "states no test temperature" in v.reason


def test_composition_in_atomic_percent(records):
    for r in records:
        c = r.harmonized["composition"]
        assert c.status == "converted" and c.citation == tamu_fcc.COMPOSITION_UNIT_CITATION
        assert sum(c.value.values()) == pytest.approx(100, abs=1e-9)
        for e in tamu_fcc.ELEMENT_COLUMNS:
            assert c.value.get(e, 0.0) == float(r.reported[e].text)
    # 82 distinct compositions (PRD 10), and the naming keeps them distinct.
    assert len({tuple(sorted(r.harmonized["composition"].value.items())) for r in records}) == 82
    assert len({r.alloy for r in records}) == 82


def test_agrees_with_the_authors_csv_view(records):
    with open(INPUTS, encoding="utf-8", newline="") as f:
        view = {row["Alloy"]: row for row in csv.DictReader(f)}
    assert len(view) == 94
    for r in records:
        row = view[r.reported["Alloy Name"].text]
        h = r.harmonized
        assert h["grain_size"].value == pytest.approx(float(row["GrainSize"]))
        assert h["hardness"].value == pytest.approx(float(row["HV"]))
        if row["YS"]:
            assert h["yield_strength"].value == pytest.approx(float(row["YS"]))
        else:
            assert h["yield_strength"].status == "not_reported"
        for e in tamu_fcc.ELEMENT_COLUMNS:
            assert h["composition"].value.get(e, 0.0) == pytest.approx(float(row[e]))


# --- Planted rows --------------------------------------------------------------------

def workbook(rows, sheet=tamu_fcc.SHEET, header=tamu_fcc.HEADER) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(list(header))
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


GOOD = ["BBA", "X01", 4, 8, 4, 4, 16, 12, 48, 4, 140.2, 3.8, 284.2, 34.3, 60, 950, 0.5, 23, 13]


def _row(**changes):
    row = list(GOOD)
    for col, value in changes.items():
        row[int(col[1:])] = value
    return row


def test_planted_values_are_kept_and_marked():
    rows = [
        GOOD,
        _row(c4="abc"),           # 1: a percentage that is not a number
        _row(c8=47),              # 2: percentages sum to 99
        _row(c12=None),           # 3: blank yield strength
        _row(c17="=1+1"),         # 4: a formula, not a value
        [None] * 19,              # 5: blank row
        GOOD + ["extra"],         # 6: an extra column
        _row(c17=-5),             # 7: negative grain size: converted as reported, not judged here
        _row(c17="12.5"),         # 8: a number stored as text
    ]
    result = tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook(rows)}))
    by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
    assert result.blank_rows == (5,)
    assert sorted(by_row) == [0, 1, 2, 3, 4, 6, 7, 8]

    def h(i, field):
        return by_row[i].harmonized[field]

    assert by_row[0].alloy == "Al4Co8Cr4Cu4Fe16Mn12Ni48V4"
    assert h(1, "composition").status == "not_convertible" and h(1, "composition").reason == "Cr: not a number: 'abc'"
    assert by_row[1].alloy is None and by_row[1].reported["Cr"].text == "abc"
    assert h(2, "composition").reason == "percentages sum to 99, not 100"
    assert h(3, "yield_strength").status == "not_reported"
    assert all(v.status == "not_convertible" for v in by_row[4].harmonized.values())
    assert by_row[4].reported["Grain Size(µm)"].text == "=1+1"
    assert by_row[6].reported["(column 20, no header)"].text == "extra"
    assert (h(7, "grain_size").status, h(7, "grain_size").value) == ("converted", -5.0)
    assert (h(8, "grain_size").status, h(8, "grain_size").value) == ("converted", 12.5)


def test_another_layout_is_refused():
    with pytest.raises(AdapterError, match="no sheet"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], sheet="Other")}))
    with pytest.raises(AdapterError, match="header"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], header=("a",) * 19)}))
    with pytest.raises(AdapterError, match="not a readable spreadsheet"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: b"not a spreadsheet"}))


def test_the_batch_grouping_unit_is_refused_until_the_owner_decides():
    with pytest.raises(AdapterError, match="decision 9"):
        tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD])}, grouping_unit="batch"))


def test_records_serialize_to_json(records):
    out = json.loads(json.dumps(records[0].to_json()))
    assert set(out["harmonized"]) == set(HARMONIZED_FIELDS)
    assert out["group"] == {"unit": "dataset", "key": "dataset:10.5281/zenodo.22798856", "reason": None}
