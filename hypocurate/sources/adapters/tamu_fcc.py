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
- Values not in the file are set with one of two statuses (register entry
  'assigned_value_statuses'), each with its citation:
  - `assigned_from_source`, where the source's own documentation states them: from step 8a
    (version 3) these come only from the version's sealed curation, the Curator's proposals the
    owner accepted (`sources.curated`; test type `tension`, phase class `FCC`, both quoted from
    paper/main.tex); this adapter leaves them not reported;
  - `assigned_by_decision`, where the source does not state them and the owner decided
    (register entries 'tamu_test_temperature' and 'tamu_microstructure', 2026-10-05):
    temperature band `room temperature`, microstructure `FCC` (single-phase).
  The numeric test temperature stays `not_reported`: neither the source nor the decision
  gives a number.
"""
from __future__ import annotations

import io
import math
import zipfile


from hypocurate.sources import normalize as n
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation,
                                       CommonRecord, Group, Reported, Value)
from hypocurate.sources.versions import SealedVersion

# The adapter's version, stored with every record it extracts (record.extraction; step 6).
# Raise it whenever what the adapter returns for the same file changes.
# 2: the two assigned statuses; band and microstructure by decision (step 6). 3 (step 8a): test type and
# phase class no longer assigned here; a curated version supplies them (owner, 2026-10-06).
ADAPTER_VERSION = "3"

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
COMPOSITION_UNIT_CITATION = Citation(
    f"{_REPO} paper/main.tex", "line 399 (Results, Family 3)",
    "Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider "
    "interval.")

# Decisions recorded in the assumptions register (status `assigned_by_decision`). The quote is
# the entry's statement; tests check it against the register.
REGISTER = "hypocurate/assumptions.json"
TEMPERATURE_DECISION = Citation(
    REGISTER, "entry 'tamu_test_temperature' (decided by the owner, Khalid El-Awady, 2026-10-05)",
    "The Texas A&M records are treated as tested at room temperature. The value is 'assigned by decision': "
    "the source does not report it and does not state it explicitly.")
MICROSTRUCTURE_DECISION = Citation(
    REGISTER, "entry 'tamu_microstructure' (decided by the owner, Khalid El-Awady, 2026-10-05)",
    "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source "
    "does not state it explicitly as a result.")

TEMPERATURE_NOT_REPORTED = ("no per-record temperature; the source states no test temperature for its "
                            "own measurements (the room-temperature band is assigned by decision)")
NO_COLUMN = "the source has no column for this field"
CURATED = ("the spreadsheet has no column for this field; the source's documentation states it, and a curated "
           "version supplies it (step 8a)")


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
    h["test_type"] = Value(None, None, "not_reported", CURATED)
    h["phase_class"] = Value(None, None, "not_reported", CURATED)
    h["test_temperature"] = Value(None, "°C", "not_reported", TEMPERATURE_NOT_REPORTED)
    h["test_temperature_band"] = Value("room temperature", None, "assigned_by_decision",
                                       citation=TEMPERATURE_DECISION)
    h["microstructure"] = Value("FCC", None, "assigned_by_decision", citation=MICROSTRUCTURE_DECISION)
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
    # Step 8a: a version may also hold documentation and a curation file; the adapter reads its data.
    if len(version.data_files) != 1:
        raise AdapterError(f"expected one spreadsheet, found {sorted(version.data_files)}")
    (path, content), = version.data_files.items()
    try:
        # Step 9b: imported here, not at module load: openpyxl imports numpy, and the worker parent, which imports
        # this module through the access layer, never loads it (owner, Q2: memory on 512 MB).
        import openpyxl
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
