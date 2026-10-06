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


# Review, test weakness: expected strings written out by hand, not computed with the
# adapter's own formatter. Source: the cell values in the file's XML
# (xl/worksheets/sheet1.xml, rows 2, 3 and 9). The XML stores some doubles at 17
# significant digits (K2 "140.19999999999999", N2 "34.299999999999997"); the reported text
# is the shortest decimal that reads back as the same double ("140.2", "34.3"). Integer
# cells read as integers ("4", "301"), and an empty cell is "".
EXPECTED_TEXT = {
    "BBA01": {"Iteration": "BBA", "Alloy Name": "BBA01", "Al": "4", "Co": "8", "Cr": "4", "Ni": "48",
              "Hardness, HV": "140.2", "SD, HV": "3.8", "YS (MPa)": "284.2", "SD, YS": "34.3",
              "Cold Work (%Reduction)": "60", "Recrystallization Temp(℃)": "950", "Holding time (h)": "0.5",
              "Grain Size(µm)": "23", "SD, Grain Size(µm)": "13"},
    "BBA02": {"Cr": "0", "Ni": "52", "Hardness, HV": "151.5", "YS (MPa)": "301", "SD, YS": "6.6",
              "Grain Size(µm)": "31.94", "SD, Grain Size(µm)": "18.45"},
    "BBA09": {"Cu": "0", "V": "12", "Hardness, HV": "200.9", "SD, HV": "8", "YS (MPa)": "", "SD, YS": "",
              "Grain Size(µm)": "30.79", "SD, Grain Size(µm)": "22.57"},
}


def test_reported_text_matches_independently_written_strings(records):
    by_name = {r.reported["Alloy Name"].text: r for r in records}
    for name, expected in EXPECTED_TEXT.items():
        assert {col: by_name[name].reported[col].text for col in expected} == expected, name


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
    """Step 6 (owner, 2026-10-05): two assigned statuses. Test type and phase class are
    assigned from the source's own statements; the band and the microstructure by decision.
    Step 8a (owner, 2026-10-06): the first two come from the frozen curation (the Curator's proposals
    the owner accepted), quoting the same passages the adapter cited by hand before (version 2)."""
    for r in records:
        t, p = r.harmonized["test_type"], r.harmonized["phase_class"]
        assert (t.value, t.status, p.value, p.status) == ("tension", "assigned_from_source", "FCC",
                                                          "assigned_from_source")
        assert t.citation.quote == ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while "
                                    "Vickers indentation tests provided the HV.")
        assert p.citation.quote == "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."
        assert t.citation.location.startswith("line 177; Curator proposal 5") and "Khalid El-Awady" in t.citation.location
        assert p.citation.location.startswith("line 173; Curator proposal 2")
        assert t.citation.document == "tamu_fcc: documentation/main.tex (sealed with the source)"
        b, m = r.harmonized["test_temperature_band"], r.harmonized["microstructure"]
        assert (b.value, b.status, b.citation) == ("room temperature", "assigned_by_decision",
                                                   tamu_fcc.TEMPERATURE_DECISION)
        assert (m.value, m.status, m.citation) == ("FCC", "assigned_by_decision", tamu_fcc.MICROSTRUCTURE_DECISION)
        out = r.to_json()["harmonized"]
        assert out["test_type"]["status"] == "assigned_from_source" and out["test_type"]["citation"]["quote"]
        assert out["microstructure"]["status"] == "assigned_by_decision" and out["microstructure"]["citation"]["quote"]
    by_status = lambda status: {k for r in records for k, v in r.harmonized.items() if v.status == status}
    assert by_status("assigned_from_source") == {"test_type", "phase_class"}
    assert by_status("assigned_by_decision") == {"test_temperature_band", "microstructure"}


def test_decision_citations_quote_the_register():
    """The citation of a value assigned by decision is the register entry's own statement."""
    entries = {e["key"]: e for e in json.loads((REPO / "hypocurate" / "assumptions.json").read_text())}
    for key, citation in (("tamu_test_temperature", tamu_fcc.TEMPERATURE_DECISION),
                          ("tamu_microstructure", tamu_fcc.MICROSTRUCTURE_DECISION)):
        e = entries[key]
        assert citation.document == "hypocurate/assumptions.json"
        assert citation.quote == e["statement"]
        assert f"'{key}'" in citation.location and e["decided"]["date"] in citation.location
        assert e["state"] == "in_force"


def test_assigned_and_reported_stay_distinguishable(records):
    for r in records:
        for v in r.harmonized.values():
            assert (v.status in ("assigned_from_source", "assigned_by_decision")) <= (v.citation is not None)
        assert all(isinstance(rep, Reported) and not hasattr(rep, "citation") for rep in r.reported.values())
        assert "tension" not in {rep.text for rep in r.reported.values()}
        assert "room temperature" not in {rep.text for rep in r.reported.values()}


def test_temperature_is_not_reported_and_the_band_is_assigned_by_decision(records):
    for r in records:
        v = r.harmonized["test_temperature"]
        assert (v.status, v.value) == ("not_reported", None)
        assert "states no test temperature" in v.reason
        assert r.harmonized["test_temperature_band"].status == "assigned_by_decision"


def test_composition_in_atomic_percent(records):
    for r in records:
        c = r.harmonized["composition"]
        assert c.status == "converted" and c.citation == tamu_fcc.COMPOSITION_UNIT_CITATION
        assert sum(c.value.values()) == pytest.approx(100, abs=1e-9)
        for e in tamu_fcc.ELEMENT_COLUMNS:
            assert c.value.get(e, 0.0) == float(r.reported[e].text)
    # 82 distinct compositions (PRD 10); their display labels happen to be distinct too.
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
        _row(c18="=1+1"),         # 4: a formula in the grain-size SD, not a value
        [None] * 19,              # 5: blank row
        GOOD + ["extra"],         # 6: an extra column
        _row(c17=-5),             # 7: negative grain size: converted as reported, not judged here
        _row(c17="12.5"),         # 8: a number stored as text
        _row(c4="=A1"),           # 9: a formula in an element column
    ]
    result = tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook(rows)}))
    by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
    assert result.blank_rows == (5,)
    assert sorted(by_row) == [0, 1, 2, 3, 4, 6, 7, 8, 9]

    def h(i, field):
        return by_row[i].harmonized[field]

    assert by_row[0].alloy == "Al4Co8Cr4Cu4Fe16Mn12Ni48V4"
    assert h(1, "composition").status == "not_convertible" and h(1, "composition").reason == "Cr: not a number: 'abc'"
    assert by_row[1].alloy is None and by_row[1].reported["Cr"].text == "abc"
    assert h(2, "composition").reason == "percentages sum to 99, not 100"
    assert h(3, "yield_strength").status == "not_reported"
    # Finding 4: only the field the formula cell feeds is affected; everything else is as
    # in the ordinary row 0, assignments and the deliberately not-reported temperature too.
    assert h(4, "grain_size_sd").status == "not_convertible"
    assert h(4, "grain_size_sd").reason == "the cell holds a formula, not a value: '=1+1'"
    assert by_row[4].reported["SD, Grain Size(µm)"].text == "=1+1"
    assert {k: v for k, v in by_row[4].harmonized.items() if k != "grain_size_sd"} == \
        {k: v for k, v in by_row[0].harmonized.items() if k != "grain_size_sd"}
    assert (h(4, "grain_size").value, h(4, "yield_strength").value) == (23.0, 284.2)
    # Step 8a (adapter version 3): with no curation in this constructed version, no test type is assigned.
    assert (h(4, "test_type").status, h(4, "test_type").reason) == ("not_reported", tamu_fcc.CURATED)
    assert h(4, "test_temperature").status == "not_reported"
    assert h(4, "test_temperature").reason == tamu_fcc.TEMPERATURE_NOT_REPORTED
    assert by_row[4].alloy == by_row[0].alloy
    # A formula in an element column affects the composition only.
    assert h(9, "composition").status == "not_convertible" and h(9, "composition").reason.startswith("Cr: ")
    assert by_row[9].alloy is None
    assert {k: v for k, v in by_row[9].harmonized.items() if k != "composition"} == \
        {k: v for k, v in by_row[0].harmonized.items() if k != "composition"}
    assert by_row[6].reported["(column 20, no header)"].text == "extra"
    assert (h(7, "grain_size").status, h(7, "grain_size").value) == ("converted", -5.0)
    assert (h(8, "grain_size").status, h(8, "grain_size").value) == ("converted", 12.5)


def test_a_composition_that_overflows_is_marked_and_the_other_rows_are_kept():
    """Re-check item 5: Fe and Ni at 1e308 overflowed the sum and aborted the whole file."""
    rows = [GOOD, _row(c6=1e308, c8=1e308), _row(c1="X03")]
    result = tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook(rows)}))
    assert [r.source_item_key for r in result.records] == [f"{FILE}:row:{i}" for i in range(3)]
    assert [r.reported["Alloy Name"].text for r in result.records] == ["X01", "X01", "X03"]
    assert result.records[1].reported["Fe"].text == "1e+308"
    bad = result.records[1].harmonized["composition"]
    assert (bad.status, bad.reason) == ("not_convertible", "percentage above 100 for Fe, Ni")
    assert result.records[1].alloy is None
    assert result.records[1].harmonized["grain_size"].value == 23.0
    assert result.records[0].harmonized["composition"].status == "converted"
    assert result.records[2].harmonized["composition"].status == "converted"


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
