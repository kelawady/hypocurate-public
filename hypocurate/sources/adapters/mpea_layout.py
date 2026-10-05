"""Adapter for the MPEA column layout (Borg et al. 2020): the MPEA dataset itself and the
controlled duplicate extract, which copies its header verbatim (step 1).

- One record per data row, in file order; no row is dropped. An entirely blank line is
  listed in `blank_rows`, not turned into a record.
- Origin key: `<file>:row:<n>`, n the 0-based data row (the row numbering used in
  step 1). One record per row, so `item_index` is 0.
- Every column is kept as reported text, with the unit its header states.
- **Paper identity (grouping): the DOI** (`REFERENCE: doi`), as in the reference script.
  In the frozen MPEA file it is one-to-one with `IDENTIFIER: Reference ID`. A blank DOI
  gives a record whose group is unknown, with the reason; the Reference ID is never used
  in its place, and no group is invented.
- Units are those of the headers (µm, MPa, HV, °C); values are converted unchanged.
- Text values (DOI, title, categories) are kept exactly as reported, surrounding spaces
  included; only a whitespace-only cell counts as blank.
"""
from __future__ import annotations

import csv
import io

from hypocurate.sources import normalize as n
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, CommonRecord,
                                       Group, Reported, Value)
from hypocurate.sources.versions import SealedVersion

HEADER = (
    "IDENTIFIER: Reference ID", "FORMULA", "PROPERTY: Microstructure", "PROPERTY: Processing method",
    "PROPERTY: BCC/FCC/other", "PROPERTY: grain size ($\\mu$m)", "PROPERTY: Exp. Density (g/cm$^3$)",
    "PROPERTY: Calculated Density (g/cm$^3$)", "PROPERTY: HV", "PROPERTY: Type of test",
    "PROPERTY: Test temperature ($^\\circ$C)", "PROPERTY: YS (MPa)", "PROPERTY: UTS (MPa)",
    "PROPERTY: Elongation (%)", "PROPERTY: Elongation plastic (%)", "PROPERTY: Exp. Young modulus (GPa)",
    "PROPERTY: Calculated Young modulus (GPa)", "PROPERTY: O content (wppm)", "PROPERTY: N content (wppm)",
    "PROPERTY: C content (wppm)", "REFERENCE: doi", "REFERENCE: year", "REFERENCE: title",
)

# The unit each column's header states (None: none stated, or text).
UNITS = {
    "PROPERTY: grain size ($\\mu$m)": "µm", "PROPERTY: Exp. Density (g/cm$^3$)": "g/cm³",
    "PROPERTY: Calculated Density (g/cm$^3$)": "g/cm³", "PROPERTY: HV": "HV",
    "PROPERTY: Test temperature ($^\\circ$C)": "°C", "PROPERTY: YS (MPa)": "MPa", "PROPERTY: UTS (MPa)": "MPa",
    "PROPERTY: Elongation (%)": "%", "PROPERTY: Elongation plastic (%)": "%",
    "PROPERTY: Exp. Young modulus (GPa)": "GPa", "PROPERTY: Calculated Young modulus (GPa)": "GPa",
    "PROPERTY: O content (wppm)": "wppm", "PROPERTY: N content (wppm)": "wppm",
    "PROPERTY: C content (wppm)": "wppm",
}

TEST_TYPE_CODES = {"T": "tension", "C": "compression"}

NO_COLUMN = "the source has no column for this field"


def _text(value: str) -> Value:
    """A categorical value, kept verbatim."""
    if value.strip() == "":
        return Value(None, None, "not_reported", "blank in the source")
    return Value(value, None, "converted")


def _harmonize(cells: dict[str, str]) -> tuple[dict[str, Value], str | None]:
    h: dict[str, Value] = {}
    composition, reason = n.formula_to_atomic_percent(cells["FORMULA"])
    if composition is None:
        status = "not_reported" if cells["FORMULA"].strip() == "" else "not_convertible"
        h["composition"] = Value(None, "at.%", status, reason)
        alloy = None
    else:
        h["composition"] = Value(composition, "at.%", "converted")
        alloy = n.alloy_label(composition)
    h["grain_size"] = n.number(cells["PROPERTY: grain size ($\\mu$m)"], "µm")
    h["yield_strength"] = n.number(cells["PROPERTY: YS (MPa)"], "MPa")
    h["ultimate_tensile_strength"] = n.number(cells["PROPERTY: UTS (MPa)"], "MPa")
    h["hardness"] = n.number(cells["PROPERTY: HV"], "HV")
    h["test_temperature"] = n.number(cells["PROPERTY: Test temperature ($^\\circ$C)"], "°C")
    h["test_temperature_band"] = Value(None, None, "not_reported",
                                       "the source reports a temperature in °C, not a band")
    code = cells["PROPERTY: Type of test"]
    if code.strip() == "":
        h["test_type"] = Value(None, None, "not_reported", "blank in the source")
    elif code.strip() in TEST_TYPE_CODES:
        h["test_type"] = Value(TEST_TYPE_CODES[code.strip()], None, "converted")
    else:
        h["test_type"] = Value(None, None, "not_convertible", f"unknown test type code {code!r}")
    h["phase_class"] = _text(cells["PROPERTY: BCC/FCC/other"])
    h["microstructure"] = _text(cells["PROPERTY: Microstructure"])
    h["processing_method"] = _text(cells["PROPERTY: Processing method"])
    for name in ("grain_size_sd", "yield_strength_sd", "hardness_sd", "cold_work",
                 "recrystallization_temperature", "holding_time"):
        h[name] = Value(None, HARMONIZED_FIELDS[name], "not_reported", NO_COLUMN)
    return h, alloy


def read(version: SealedVersion) -> AdapterResult:
    version.verify()
    if version.grouping_unit != "paper":
        raise AdapterError(f"the MPEA-layout adapter groups by paper; version {version.id} "
                           f"has grouping unit {version.grouping_unit!r}")
    if len(version.files) != 1:
        raise AdapterError(f"expected one CSV file, found {sorted(version.files)}")
    (path, content), = version.files.items()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AdapterError(f"{path} is not UTF-8: {error}") from None
    rows = csv.reader(io.StringIO(decoded, newline=""))
    header = tuple(next(rows, ()))
    if header != HEADER:
        raise AdapterError(f"{path}: the header is not the MPEA layout")
    records, blank = [], []
    for i, fields in enumerate(rows):
        if not fields or all(f.strip() == "" for f in fields):
            blank.append(i)
            continue
        records.append(_record(version, path, i, fields))
    return AdapterResult(tuple(records), tuple(blank))


def _record(version: SealedVersion, path: str, i: int, fields: list[str]) -> CommonRecord:
    key = f"{path}:row:{i}"
    reported = {}
    for name, value in zip(HEADER, fields):
        reported[name] = Reported(name, value, UNITS.get(name))
    for extra, value in enumerate(fields[len(HEADER):], start=len(HEADER) + 1):
        reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", value, None)
    if len(fields) != len(HEADER):
        reason = f"the row has {len(fields)} fields, the header {len(HEADER)}"
        harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
        return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None, None, None,
                            Group("paper", None, reason), harmonized, reported)
    cells = dict(zip(HEADER, fields))
    harmonized, alloy = _harmonize(cells)
    # Kept exactly as reported (one MPEA DOI has a leading space); only a whitespace-only
    # cell counts as blank.
    doi = cells["REFERENCE: doi"] if cells["REFERENCE: doi"].strip() else None
    title = cells["REFERENCE: title"] if cells["REFERENCE: title"].strip() else None
    group = Group("paper", f"doi:{doi}") if doi else Group("paper", None, "no DOI in the source: paper unknown")
    return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy, title, doi,
                        group, harmonized, reported)
