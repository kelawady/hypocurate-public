"""Builds `SealedVersion` objects for adapter tests without a database. The real path
(`load_sealed_version`) is tested in test_source_versions.py; these objects carry a
correct digest and identity, so `verify()` passes exactly as for a loaded version."""
from __future__ import annotations

from datetime import datetime, timezone

from hypocurate.sources.versions import (SOURCES, SealedVersion, files_digest, read_definition_files,
                                         version_identity)


def sealed(key: str, files: dict[str, bytes], grouping_unit: str | None = None, version_id: int = 1) -> SealedVersion:
    d = SOURCES[key]
    unit = grouping_unit or d.grouping_unit
    digest = files_digest(files)
    return SealedVersion(version_id, key, d.version_label, d.source_type, d.data_kind, unit,
                         datetime.now(timezone.utc), digest,
                         version_identity(digest, d.source_type, d.data_kind, unit), files)


def sealed_from_disk(key: str) -> SealedVersion:
    files, _ = read_definition_files(SOURCES[key])
    return sealed(key, files)
