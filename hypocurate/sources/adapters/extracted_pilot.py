"""Adapter for the 'extracted (pilot)' source (Sprint 2 pilot, R9; `hypocurate.sources.pilot`).

One record per row of `extracted_pilot.csv`, in file order; strict CSV, the exact header, or the file is refused.
Grain size and yield strength are the numbers code converted from the paper's stated values (µm, MPa: 'converted');
the test temperature is converted when one temperature was stated, otherwise not reported. Test type, temperature
band and phase come from a mapping a person accepted, with the paper's quote ('assigned_from_source', citing the
document by its SHA-256), or, for the test type, from the stated text read by code ('converted'). The microstructure is
the accepted phase (single phase: the paper's statement the mapping quotes). Paper identity: the DOI."""
from __future__ import annotations

import csv
import io

from hypocurate.sources import normalize as n
from hypocurate.sources.pilot import COLUMNS, DATA_FILE
from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation, CommonRecord, Group,
                                       Reported, Value)
from hypocurate.sources.versions import SealedVersion

ADAPTER_VERSION = "1"
NOT_STATED = "not stated in a form code could read, or no accepted mapping"


def _assigned(value: str, quote: str, sha: str, what: str) -> Value:
    if not value:
        return Value(None, None, "not_reported", NOT_STATED)
    if not quote.strip():
        return Value(value, None, "converted")
    return Value(value, None, "assigned_from_source", citation=Citation(f"document sha256 {sha}", what, quote))


def _record(version: SealedVersion, i: int, cells: dict[str, str]) -> CommonRecord:
    h: dict[str, Value] = {}
    comp, reason = n.formula_to_atomic_percent(cells["composition_formula"].replace(" ", ""))
    if comp:
        h["composition"] = Value(comp, "at.%", "converted")
    elif cells["composition_formula"].strip():
        h["composition"] = Value(None, "at.%", "not_convertible", reason)
    else:
        h["composition"] = Value(None, "at.%", "not_reported", "no accepted composition mapping")
    h["grain_size"] = n.number(cells["grain_size_um"], "µm", "not a stated number")
    h["yield_strength"] = n.number(cells["yield_strength_mpa"], "MPa", "not a stated number")
    h["test_temperature"] = n.number(cells["test_temperature_c"], "°C", "one temperature not stated")
    sha = cells["document_sha256"]
    h["test_type"] = _assigned(cells["test_type"], cells["test_type_quote"], sha, "test type mapping")
    h["test_temperature_band"] = _assigned(cells["test_temperature_band"], cells["test_temperature_band_quote"], sha,
                                           "temperature band mapping")
    h["phase_class"] = _assigned(cells["phase"], cells["phase_quote"], sha, "phase mapping")
    h["microstructure"] = _assigned(cells["phase"], cells["phase_quote"], sha, "phase mapping (single phase)")
    h["processing_method"] = Value(None, None, "not_reported", "the paper's processing is kept as written")
    for name in ("grain_size_sd", "yield_strength_sd", "ultimate_tensile_strength", "hardness", "hardness_sd",
                 "cold_work", "recrystallization_temperature", "holding_time"):
        h[name] = Value(None, HARMONIZED_FIELDS[name], "not_reported", "not extracted in the pilot")
    key = n.doi_group_key(cells["paper_doi"])
    group = Group("paper", key) if key else Group("paper", None, "no DOI: paper unknown")
    alloy = n.alloy_label(comp) if comp else None
    reported = {c: Reported(c, cells[c], None) for c in COLUMNS}
    return CommonRecord(version.source_key, version.fingerprint, f"{DATA_FILE}:{cells['record_key']}", 0,
                        version.data_kind, alloy, None, cells["paper_doi"], group, h, reported)


def read(version: SealedVersion) -> AdapterResult:
    version.verify()
    content = version.data_files.get(DATA_FILE)
    if content is None or len(version.data_files) != 1:
        raise AdapterError(f"expected one file {DATA_FILE}, found {sorted(version.data_files)}")
    try:
        rows = list(csv.reader(io.StringIO(content.decode("utf-8"), newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        raise AdapterError(f"{DATA_FILE}: {error}; the file is refused") from None
    if not rows or tuple(rows[0]) != COLUMNS:
        raise AdapterError(f"{DATA_FILE}: line 1: the header is not the pilot layout; the file is refused")
    records = []
    for i, r in enumerate(rows[1:]):
        if len(r) != len(COLUMNS):
            raise AdapterError(f"{DATA_FILE}: row {i + 1}: expected {len(COLUMNS)} fields, found {len(r)}")
        records.append(_record(version, i, dict(zip(COLUMNS, r))))
    return AdapterResult(tuple(records))
