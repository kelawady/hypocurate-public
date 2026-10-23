"""One adapter per registered source (PRD 6.1, 10). Each takes a sealed source version
and returns its records in the common record format (`hypocurate.sources.record`).
An adapter converts and reports: it never decides eligibility, never drops a record and
never corrects a value silently."""
from __future__ import annotations

from typing import Callable, Mapping
from types import MappingProxyType

from hypocurate.sources.adapters import extracted_pilot, mpea_layout, tamu_fcc
from hypocurate.sources.record import AdapterError, AdapterResult
from hypocurate.sources.versions import SealedVersion

ADAPTERS: Mapping[str, Callable[[SealedVersion], AdapterResult]] = MappingProxyType({
    "mpea": mpea_layout.read,
    "controlled_duplicates": mpea_layout.read,
    "tamu_fcc": tamu_fcc.read,
    "extracted_pilot": extracted_pilot.read,  # Sprint 2 pilot (R9): built from the R6 freeze
})


# How a record was extracted (stored in record.extraction, step 6): by adapter code, with the
# adapter's name and version, so records extracted by code can always be told apart from
# records an agent extracts later (owner, 2026-10-05).
ADAPTER_IDENTITY: Mapping[str, tuple[str, str]] = MappingProxyType({
    "mpea": ("mpea_layout", mpea_layout.ADAPTER_VERSION),
    "controlled_duplicates": ("mpea_layout", mpea_layout.ADAPTER_VERSION),
    "tamu_fcc": ("tamu_fcc", tamu_fcc.ADAPTER_VERSION),
    "extracted_pilot": ("extracted_pilot", extracted_pilot.ADAPTER_VERSION),
})


def extraction(source_key: str) -> dict:
    """The `record.extraction` value for a record this source's adapter extracted."""
    name, version = ADAPTER_IDENTITY[source_key]
    return {"method": "adapter", "name": name, "version": version}


def read(version: SealedVersion) -> AdapterResult:
    """Reads a sealed version with its source's adapter, then applies the version's sealed curation,
    if it has one, where the table gives no value (step 8a; `sources.curated`)."""
    from hypocurate.sources.curated import apply_curation
    adapter = ADAPTERS.get(version.source_key)
    if adapter is None:
        raise AdapterError(f"no adapter for source {version.source_key!r}")
    return apply_curation(adapter(version), version)
