"""Adapter for the Texas A&M FCC dataset (Mulukutla et al. 2026), read from its
spreadsheet, the source of record (step 1).

- One record per data row of the workbook's one sheet, `GS_MasterTable_Iterations `
  (the name ends with a space in the file), in sheet order; no row is dropped. An
  entirely blank row is listed in `blank_rows`.
- Origin key: `<file>:row:<n>`, n the 0-based data row of that sheet (the adapter reads
  only that sheet). `item_index` is 0.
- Every column is kept as reported: the header and the cell value as text (numbers in
  their shortest exact form), with the unit the header states.
- Composition: eight columns of atomic percentages (Al … V). The headers state no unit;
  the unit is documented in the paper (citation on the value). A sum other than 100 is
  marked, never rescaled.
- **Paper identity (grouping): the dataset.** The dataset is the source, with no
  per-record paper (PRD 10), so every record has the one group `dataset:<DOI>`. The
  batch (`Iteration`, six values) is kept as reported. **The grouping unit is an open
  decision for the owner (PRD 17, decision 9):** one group in sprint 1; batches only if
  the owner agrees they are independent enough. This adapter refuses any other unit.
- Values not in the file are set only where the source's own documentation states them,
  as `assigned` with the exact passage (owner, 2026-10-05, step 4 question 3):
  test type `tension`, phase class `FCC`. **Test temperature is not assigned**: the
  repository states no test temperature for these measurements (step 4 summary), so the
  temperature and its band are `not_reported`, and the owner decides later.
"""
from __future__ import annotations

import io
import math
import zipfile

import openpyxl

from hypocurate.sources import normalize as n
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation,
                                       CommonRecord, Group, Reported, Value)
from hypocurate.sources.versions import SealedVersion

SHEET = "GS_MasterTable_Iterations "  # verbatim: the sheet name ends with a space
HEADER = (
    "Iteration", "Alloy Name", "Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V", "Hardness, HV", "SD, HV",
    "YS (MPa)", "SD, YS", "Cold Work (%Reduction)", "Recrystallization Temp(℃)", "Holding time (h)",
    "Grain Size(µm)", "SD, Grain Size(µm)",
)
ELEMENT_COLUMNS = ("Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V")
# Units the headers state. "SD, YS" states none; an SD has the unit of its quantity.
UNITS = {
    "Hardness, HV": "HV", "SD, HV": "HV", "YS (MPa)": "MPa", "Cold Work (%Reduction)": "% reduction",
    "Recrystallization Temp(℃)": "°C", "Holding time (h)": "h", "Grain Size(µm)": "µm",
    "SD, Grain Size(µm)": "µm",
}

DATASET_DOI = "10.5281/zenodo.22798856"
DATASET_REFERENCE = ("Mulukutla, M. et al. (2026). Revisiting Hall-Petch strengthening in FCC "
                     "multi-principal element alloys: data and analysis pipeline (v1.1.0). Zenodo. "
                     "doi:10.5281/zenodo.22798856")

_REPO = "ArroyaveLab/2026-mulukutla-hall-petch@11390ee516c1a17cacdde318b40d5d6889d4007f"
TEST_TYPE_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 177 (Dataset and descriptors, Alloy Synthesis and characterization)",
    "Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
    "tests provided the HV.")
PHASE_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 173 (Dataset and descriptors, Alloy Synthesis and characterization)",
    "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.")
COMPOSITION_UNIT_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 399 (Results, Family 3)",
    "Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider "
    "interval.")

TEMPERATURE_NOT_REPORTED = ("no per-record temperature; the source states no test temperature for its "
                            "own measurements (owner decides; step 4 summary)")
NO_COLUMN = "the source has no column for this field"


def reported_text(value) -> str:
    """A cell value as text: "" for an empty cell, numbers in their shortest exact form."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _number(value, unit: str | None) -> Value:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Value(None, unit, "not_reported", "blank in the source")
    if isinstance(value, str) and value.startswith("="):
        # Only the field this cell feeds is affected (step 4 review, finding 4).
        return Value(None, unit, "not_convertible", f"the cell holds a formula, not a value: {value!r}")
    if isinstance(value, bool):
        return Value(None, unit, "not_convertible", f"not a number: {value!r}")
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            return Value(None, unit, "not_convertible", f"not a finite number: {value!r}")
        return Value(float(value), unit, "converted")
    return n.number(str(value), unit)


def _composition(cells: dict) -> tuple[Value, str | None]:
    columns: dict[str, float | None] = {}
    for symbol in ELEMENT_COLUMNS:
        v = _number(cells[symbol], "at.%")
        if v.status == "not_convertible":
            return Value(None, "at.%", "not_convertible", f"{symbol}: {v.reason}"), None
        columns[symbol] = v.value
    composition, reason = n.percent_columns_to_atomic_percent(columns)
    if composition is None:
        return Value(None, "at.%", "not_convertible", reason), None
    return Value(composition, "at.%", "converted", citation=COMPOSITION_UNIT_CITATION), n.alloy_label(composition)


def _harmonize(cells: dict) -> tuple[dict[str, Value], str | None]:
    h: dict[str, Value] = {}
    h["composition"], alloy = _composition(cells)
    h["grain_size"] = _number(cells["Grain Size(µm)"], "µm")
    h["grain_size_sd"] = _number(cells["SD, Grain Size(µm)"], "µm")
    h["yield_strength"] = _number(cells["YS (MPa)"], "MPa")
    h["yield_strength_sd"] = _number(cells["SD, YS"], "MPa")
    h["hardness"] = _number(cells["Hardness, HV"], "HV")
    h["hardness_sd"] = _number(cells["SD, HV"], "HV")
    h["cold_work"] = _number(cells["Cold Work (%Reduction)"], "% reduction")
    h["recrystallization_temperature"] = _number(cells["Recrystallization Temp(℃)"], "°C")
    h["holding_time"] = _number(cells["Holding time (h)"], "h")
    h["test_type"] = Value("tension", None, "assigned", citation=TEST_TYPE_CITATION)
    h["phase_class"] = Value("FCC", None, "assigned", citation=PHASE_CITATION)
    h["test_temperature"] = Value(None, "°C", "not_reported", TEMPERATURE_NOT_REPORTED)
    h["test_temperature_band"] = Value(None, None, "not_reported", TEMPERATURE_NOT_REPORTED)
    h["microstructure"] = Value(None, None, "not_reported",
                                "the source does not state the phases present per record")
    h["processing_method"] = Value(None, None, "not_reported",
                                   "the source gives processing parameters (cold work, recrystallization "
                                   "temperature, holding time), not a processing-method category")
    h["ultimate_tensile_strength"] = Value(None, "MPa", "not_reported", NO_COLUMN)
    assert set(h) == set(HARMONIZED_FIELDS)
    return h, alloy


def read(version: SealedVersion) -> AdapterResult:
    version.verify()
    if version.grouping_unit != "dataset":
        raise AdapterError(f"the Texas A&M adapter supports the grouping unit 'dataset' only "
                           f"(PRD 17, decision 9); version {version.id} has {version.grouping_unit!r}")
    if len(version.files) != 1:
        raise AdapterError(f"expected one spreadsheet, found {sorted(version.files)}")
    (path, content), = version.files.items()
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False)
    except (zipfile.BadZipFile, OSError, ValueError, KeyError) as error:
        raise AdapterError(f"{path} is not a readable spreadsheet: {error}") from None
    if SHEET not in workbook.sheetnames:
        raise AdapterError(f"{path} has no sheet {SHEET!r}")
    rows = workbook[SHEET].iter_rows(values_only=True)
    header = list(next(rows, ()))
    while header and header[-1] is None:  # empty cells past the last header (a wider data row)
        header.pop()
    if tuple(header) != HEADER:
        raise AdapterError(f"{path}: the header of {SHEET!r} is not the Texas A&M layout")
    records, blank = [], []
    for i, values in enumerate(rows):
        if all(v is None or (isinstance(v, str) and v.strip() == "") for v in values):
            blank.append(i)
            continue
        records.append(_record(version, path, i, values))
    workbook.close()
    return AdapterResult(tuple(records), tuple(blank))


def _record(version: SealedVersion, path: str, i: int, values: tuple) -> CommonRecord:
    key = f"{path}:row:{i}"
    reported = {name: Reported(name, reported_text(v), UNITS.get(name)) for name, v in zip(HEADER, values)}
    for extra, v in enumerate(values[len(HEADER):], start=len(HEADER) + 1):
        if v is not None:
            reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", reported_text(v), None)
    group = Group("dataset", f"dataset:{DATASET_DOI}")
    harmonized, alloy = _harmonize(dict(zip(HEADER, values)))
    return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy,
                        DATASET_REFERENCE, None, group, harmonized, reported)
