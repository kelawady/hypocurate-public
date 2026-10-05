"""Adapter for the MPEA column layout (Borg et al. 2020): the MPEA dataset itself and the
controlled duplicate extract, which copies its header verbatim (step 1).

- One record per data row, in file order; no row is dropped. An entirely blank line is
  listed in `blank_rows`, not turned into a record.
- Strict CSV parsing: a quoting error or a row with the wrong number of fields refuses
  the whole file with an `AdapterError` naming the file, the line and the reason. No
  partial extraction is returned. A legitimate quoted field may span lines; the row
  number in the origin key counts records, not physical lines.
- Origin key: `<file>:row:<n>`, n the 0-based data row (the row numbering used in
  step 1). One record per row, so `item_index` is 0.
- Every column is kept as reported text, with the unit its header states.
- **Paper identity (grouping): the DOI** (`REFERENCE: doi`), as in the reference script.
  `paper_doi` and the reported text keep the DOI exactly as in the file; the group key is
  derived from it by `normalize.doi_group_key` (whitespace trimmed, a URL or `doi:`
  wrapper removed, ASCII case-folded; step 4 review, finding 1), so formatting
  differences do not split one paper. A blank DOI gives a record whose group is unknown,
  with the reason; the Reference ID is never used in its place, and no group is invented.
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

# The adapter's version, stored with every record it extracts (record.extraction; step 6).
# Raise it whenever what the adapter returns for the same file changes.
ADAPTER_VERSION = "1"

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
    # Strict parsing (step 4 review, finding 3): a quoting error, or a row with the wrong
    # number of fields, refuses the whole file. A partial extraction is never returned,
    # because a stray quote can swallow the rows after it. The message names the file, the
    # line and the reason, so whoever supplied the file can correct it.
    rows = csv.reader(io.StringIO(decoded, newline=""), strict=True)
    header = tuple(_next(rows, path, 1) or ())
    if header != HEADER:
        raise AdapterError(f"{path}: line 1: the header is not the MPEA layout; the file is refused")
    records, blank = [], []
    i, start = 0, rows.line_num + 1
    while (fields := _next(rows, path, start)) is not None:
        end = rows.line_num
        lines = f"line {start}" if end == start else f"lines {start}-{end}"
        if not fields or all(f.strip() == "" for f in fields):
            blank.append(i)
        elif len(fields) != len(HEADER):
            raise AdapterError(f"{path}: {lines}: expected {len(HEADER)} fields, found {len(fields)}; "
                               "the file is refused")
        else:
            records.append(_record(version, path, i, fields))
        i, start = i + 1, end + 1
    return AdapterResult(tuple(records), tuple(blank))


def _next(rows, path: str, start: int) -> list[str] | None:
    """The next row, or None at the end of the file. A parsing error refuses the file."""
    try:
        return next(rows)
    except StopIteration:
        return None
    except csv.Error as error:
        raise AdapterError(f"{path}: line {start}: the record starting on this line cannot be parsed "
                           f"({error}, detected at line {rows.line_num}); the file is refused") from None


def _record(version: SealedVersion, path: str, i: int, fields: list[str]) -> CommonRecord:
    key = f"{path}:row:{i}"
    reported = {name: Reported(name, value, UNITS.get(name)) for name, value in zip(HEADER, fields)}
    cells = dict(zip(HEADER, fields))
    harmonized, alloy = _harmonize(cells)
    # Kept exactly as reported (one MPEA DOI has a leading space); only a whitespace-only
    # cell counts as blank.
    doi = cells["REFERENCE: doi"] if cells["REFERENCE: doi"].strip() else None
    title = cells["REFERENCE: title"] if cells["REFERENCE: title"].strip() else None
    group_key = n.doi_group_key(doi) if doi else None
    group = Group("paper", group_key) if group_key else Group("paper", None, "no DOI in the source: paper unknown")
    return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy, title, doi,
                        group, harmonized, reported)
