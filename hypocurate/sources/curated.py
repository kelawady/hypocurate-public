"""Applying a sealed curation to a source's records (step 8a; owner, 2026-10-06, Q2).

A curated version holds `curation.json`: the Curator's proposals a person accepted, sealed with the
source (`sources.curation.seal_curation`). Each value applies to every record of the version **only
where the record's field is not reported** (the table gives no value and no owner decision assigned
one); it never overrides a reported, converted or decided value. It is stored with the status
'assigned_from_source' and a citation: the documentation file, the line, the exact quote, and the
proposal, model and settings version, who accepted it and when.

A curation file that cannot be read exactly as written (wrong format, another source, a field that is
not a target) refuses the whole version, like any malformed file (register 'malformed_files_refused').
"""
from __future__ import annotations

import dataclasses
import json
from typing import Mapping

from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation, Value
from hypocurate.sources.versions import CURATION_PATH, SealedVersion

CURATION_FORMAT = 1
ENTRY_KEYS = {"value", "document", "line", "quote", "term", "proposal", "model", "agent_setting_version",
              "accepted_by", "accepted_at", "note"}


def curated_values(version: SealedVersion) -> dict[str, Value]:
    raw = version.files.get(CURATION_PATH)
    if raw is None:
        return {}
    try:
        doc = json.loads(raw.decode("utf-8"))
        if doc.get("format") != CURATION_FORMAT or doc.get("source") != version.source_key:
            raise ValueError("format or source")
        out = {}
        for field, e in doc["values"].items():
            if field not in CURATION_TARGETS or set(e) != ENTRY_KEYS:
                raise ValueError(f"entry {field!r}")
            where = (f"line {int(e['line'])}; Curator proposal {int(e['proposal'])} ({e['model']}, settings version "
                     f"{int(e['agent_setting_version'])}), accepted by {e['accepted_by']} on {e['accepted_at'][:10]}")
            out[field] = Value(e["value"], HARMONIZED_FIELDS[field], "assigned_from_source",
                               citation=Citation(f"{version.source_key}: {e['document']} (sealed with the source)",
                                                 where, e["quote"]))
        return out
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise AdapterError(f"{CURATION_PATH}: cannot be read as a curation file ({error})") from None


def apply_curation(result: AdapterResult, version: SealedVersion) -> AdapterResult:
    values: Mapping[str, Value] = curated_values(version)
    if not values:
        return result
    records = []
    for r in result.records:
        h = dict(r.harmonized)
        for field, value in values.items():
            if h[field].status == "not_reported":
                h[field] = value
        records.append(dataclasses.replace(r, harmonized=h))
    return AdapterResult(tuple(records), result.blank_rows)
