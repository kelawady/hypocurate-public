"""The common record format every source adapter returns (PRD Section 10; step 4).

One `CommonRecord` per observation, mirroring the `record` table (step 3) so that a
later step can store it unchanged: its origin (`source_item_key`, `item_index`), the
kind of data, a display label for the alloy, the paper and its grouping identity, the
harmonized values (the full-precision composition among them) and the values as
reported. The adapter states no alloy identity: when two compositions are the same
alloy is decided under the plan (step 6).

An adapter converts and reports. The format therefore has no field for eligibility,
flags, duplicates or survivors: those are decided by code under the locked plan
(steps 6 and 7). Every harmonized value carries its status:

- `converted`: read from the source and converted (possibly unchanged) to the unit shown;
- `not_reported`: blank in the source, or the source has no such column (the reason says which);
- `not_convertible`: present in the source but could not be converted; the reason says why,
  and the text as reported is kept in `reported`;
- `assigned`: not in the data file, set by the adapter from the source's own documentation.
  It always carries a `Citation` (file, location and the exact passage), so an assigned
  value can never be mistaken for a reported one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

STATUSES = ("converted", "not_reported", "not_convertible", "assigned")

# The harmonized fields, the same for every adapter, with their units (None: no unit).
# A source without a column for a field reports it as `not_reported`.
HARMONIZED_FIELDS: Mapping[str, str | None] = MappingProxyType({
    "composition": "at.%",
    "grain_size": "µm",
    "grain_size_sd": "µm",
    "yield_strength": "MPa",
    "yield_strength_sd": "MPa",
    "ultimate_tensile_strength": "MPa",
    "hardness": "HV",
    "hardness_sd": "HV",
    "test_type": None,
    "test_temperature": "°C",
    "test_temperature_band": None,
    "phase_class": None,
    "microstructure": None,
    "processing_method": None,
    "cold_work": "% reduction",
    "recrystallization_temperature": "°C",
    "holding_time": "h",
})

TEST_TYPES = ("tension", "compression")


@dataclass(frozen=True)
class Citation:
    """Where an assigned value (or a unit not stated in the data file) comes from."""
    document: str  # e.g. "ArroyaveLab/2026-mulukutla-hall-petch@11390ee paper/main.tex"
    location: str  # e.g. "line 177"
    quote: str  # the exact passage

    def __post_init__(self):
        for name in ("document", "location", "quote"):
            if not getattr(self, name).strip():
                raise ValueError(f"a citation needs a {name}")

    def to_json(self) -> dict:
        return {"document": self.document, "location": self.location, "quote": self.quote}


@dataclass(frozen=True)
class Value:
    """One harmonized value with its unit and status."""
    value: Any
    unit: str | None
    status: str
    reason: str | None = None
    citation: Citation | None = None

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}")
        if self.status in ("converted", "assigned") and self.value is None:
            raise ValueError(f"a {self.status} value needs a value")
        if self.status in ("not_reported", "not_convertible"):
            if self.value is not None:
                raise ValueError(f"a {self.status} value has no value")
            if not self.reason:
                raise ValueError(f"a {self.status} value needs a reason")
        if self.status == "assigned" and self.citation is None:
            raise ValueError("an assigned value needs a citation")
        if self.citation is not None and self.status not in ("assigned", "converted"):
            raise ValueError("only an assigned value, or a converted value whose unit is documented "
                             "outside the data file, carries a citation")
        if isinstance(self.value, dict):
            object.__setattr__(self, "value", MappingProxyType(dict(self.value)))

    def to_json(self) -> dict:
        out = {"value": dict(self.value) if isinstance(self.value, Mapping) else self.value,
               "unit": self.unit, "status": self.status}
        if self.reason is not None:
            out["reason"] = self.reason
        if self.citation is not None:
            out["citation"] = self.citation.to_json()
        return out


@dataclass(frozen=True)
class Reported:
    """A value exactly as the source gives it: the column header and the cell text."""
    column: str
    text: str  # "" for a blank cell
    unit: str | None  # the unit the source states for this column, or None

    def to_json(self) -> dict:
        return {"column": self.column, "text": self.text, "unit": self.unit}


@dataclass(frozen=True)
class Group:
    """The grouping (independence) identity used for cluster-robust errors (PRD 5.7)."""
    unit: str  # the version's grouping unit: "paper" or "dataset"
    key: str | None
    reason: str | None = None  # why there is no key

    def __post_init__(self):
        if (self.key is None) == (self.reason is None):
            raise ValueError("a group has either a key or the reason it has none")

    def to_json(self) -> dict:
        return {"unit": self.unit, "key": self.key, "reason": self.reason}


@dataclass(frozen=True)
class CommonRecord:
    source_key: str
    version_fingerprint: str
    source_item_key: str  # stable origin key within the source version
    item_index: int
    kind: str  # the version's kind of data
    alloy: str | None  # display label only, never an identity (see normalize.alloy_label); None if not convertible
    paper_reference: str | None
    paper_doi: str | None
    group: Group
    harmonized: Mapping[str, Value] = field(default_factory=dict)
    reported: Mapping[str, Reported] = field(default_factory=dict)

    def __post_init__(self):
        if not self.source_item_key:
            raise ValueError("a record needs its origin key")
        if set(self.harmonized) != set(HARMONIZED_FIELDS):
            raise ValueError(f"harmonized fields differ from the common set: "
                             f"{sorted(set(self.harmonized) ^ set(HARMONIZED_FIELDS))}")
        for name, v in self.harmonized.items():
            if v.unit != HARMONIZED_FIELDS[name]:
                raise ValueError(f"{name}: unit {v.unit!r}, expected {HARMONIZED_FIELDS[name]!r}")
        object.__setattr__(self, "harmonized", MappingProxyType(dict(self.harmonized)))
        object.__setattr__(self, "reported", MappingProxyType(dict(self.reported)))

    def to_json(self) -> dict:
        return {
            "source_key": self.source_key,
            "version_fingerprint": self.version_fingerprint,
            "source_item_key": self.source_item_key,
            "item_index": self.item_index,
            "kind": self.kind,
            "alloy": self.alloy,
            "paper_reference": self.paper_reference,
            "paper_doi": self.paper_doi,
            "group": self.group.to_json(),
            "harmonized": {k: v.to_json() for k, v in self.harmonized.items()},
            "reported": {k: r.to_json() for k, r in self.reported.items()},
        }


@dataclass(frozen=True)
class AdapterResult:
    """What an adapter read: one record per data row, in file order, and the data rows
    that were entirely blank (listed, never silently skipped)."""
    records: tuple[CommonRecord, ...]
    blank_rows: tuple[int, ...] = ()


class AdapterError(Exception):
    """The file as a whole cannot be read by this adapter (wrong layout, wrong encoding,
    an unsealed or altered version). Raised before any record is returned."""
