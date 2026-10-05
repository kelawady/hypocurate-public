"""'Test connection and show sample records' (PRD 9.6; step 4).

Loads the latest sealed version of a source, reads it with its adapter, and returns the
first few records in the common record format, with counts. It only reads: the
transaction is READ ONLY, so it cannot write to the database."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sqlalchemy import Engine, text

from hypocurate.sources import adapters
from hypocurate.sources.record import CommonRecord
from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version


@dataclass(frozen=True)
class ConnectionReport:
    source_key: str
    version_id: int
    version_label: str
    fingerprint: str
    records_read: int
    blank_rows: int
    status_counts: dict[str, int]  # harmonized values by status, over all records read
    sample: tuple[CommonRecord, ...]

    def to_json(self) -> dict:
        return {
            "source_key": self.source_key, "version_id": self.version_id, "version_label": self.version_label,
            "fingerprint": self.fingerprint, "records_read": self.records_read, "blank_rows": self.blank_rows,
            "status_counts": self.status_counts, "sample": [r.to_json() for r in self.sample],
        }


def test_connection(engine: Engine, key: str, n: int = 5) -> ConnectionReport:
    if n < 1:
        raise ValueError("n must be at least 1")
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        version = load_sealed_version(conn, latest_sealed_version_id(conn, key))
        conn.rollback()
    result = adapters.read(version)
    counts = Counter(v.status for r in result.records for v in r.harmonized.values())
    return ConnectionReport(key, version.id, version.label, version.fingerprint, len(result.records),
                            len(result.blank_rows), dict(sorted(counts.items())), result.records[:n])


test_connection.__test__ = False  # a function, not a pytest test
