"""One adapter per registered source (PRD 6.1, 10). Each takes a sealed source version
and returns its records in the common record format (`hypocurate.sources.record`).
An adapter converts and reports: it never decides eligibility, never drops a record and
never corrects a value silently."""
from __future__ import annotations

from typing import Callable, Mapping
from types import MappingProxyType

from hypocurate.sources.adapters import mpea_layout, tamu_fcc
from hypocurate.sources.record import AdapterError, AdapterResult
from hypocurate.sources.versions import SealedVersion

ADAPTERS: Mapping[str, Callable[[SealedVersion], AdapterResult]] = MappingProxyType({
    "mpea": mpea_layout.read,
    "controlled_duplicates": mpea_layout.read,
    "tamu_fcc": tamu_fcc.read,
})


def read(version: SealedVersion) -> AdapterResult:
    """Reads a sealed version with its source's adapter."""
    adapter = ADAPTERS.get(version.source_key)
    if adapter is None:
        raise AdapterError(f"no adapter for source {version.source_key!r}")
    return adapter(version)
