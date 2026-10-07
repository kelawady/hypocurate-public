"""Applying a sealed curation to a source's records (step 8a; owner, 2026-10-06, Q2).

A curated version holds `curation.json`: the Curator's proposals a person accepted, sealed with the
source (`sources.curation.seal_curation`). Each value applies to every record of the version **only
where the record's field is not reported** (the table gives no value and no owner decision assigned
one); it never overrides a reported, converted or decided value. It is stored with the status
'assigned_from_source' and a citation: the documentation file, the line, the exact quote, and the
proposal, model and settings version, who accepted it and when.

**The file is checked against the version it is attached to** (`check_curation`; step 8a review,
finding 1), before it is sealed into a version (registration and seal-curation, `versions._register_in`)
and again before it is applied (`curated_values`):
- its format and source, and exactly the expected keys;
- its base version: the fingerprint of the version's own files without `curation.json`, under the
  version's interpretation settings, must be the one the file names (an export copied onto another
  version of the same source, whose data or documentation differ, is refused);
- every entry: a target field; the value, quote, document, line and term pass the current checks
  (`quotes.check`) against that version's documentation, found on the stated line with the stated
  term;
- the acceptance fields: proposal and settings version positive integers, a model name, the
  acceptor's name (1 to 200 characters, not blank), the acceptance time with its time zone, a note
  or none (at most 2,000 characters).
Anything else refuses the whole version, like any malformed file (register 'malformed_files_refused').

What this cannot show: that a person really accepted the values. That is recorded in the database
where the curation happened (`curator_decision`). **The one trusted import is the exact approved
export replayed on the same base**: the file the owner approved and froze in `data/` (pinned by its
manifest fingerprint), registered with the base version's own files (register 'curation_acceptance').
"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from typing import Mapping

from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation, Value
from hypocurate.sources.versions import (CURATION_PATH, SealedVersion, file_role, files_digest,
                                         version_identity)

CURATION_FORMAT = 1
DOCUMENT_KEYS = {"format", "source", "base_version", "values"}
ENTRY_KEYS = {"value", "document", "line", "quote", "term", "proposal", "model", "agent_setting_version",
              "accepted_by", "accepted_at", "note"}
ACCEPTOR_MAX, NOTE_MAX = 200, 2000  # the database's bounds on a decision (migration 0005)


class CurationInvalid(ValueError):
    """A curation file that does not check out against its version."""


def _positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def check_curation(files: Mapping[str, bytes], source_key: str, source_type: str, data_kind: str,
                   grouping_unit: str) -> dict:
    """The curation file in `files`, checked against the other files (see the module docstring);
    CurationInvalid otherwise."""
    from hypocurate.pipeline.agents import quotes
    try:
        doc = json.loads(files[CURATION_PATH].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, ValueError) as error:
        raise CurationInvalid(f"not readable ({type(error).__name__})") from None
    if not isinstance(doc, dict) or set(doc) != DOCUMENT_KEYS:
        raise CurationInvalid("not the expected keys")
    if doc["format"] != CURATION_FORMAT or doc["source"] != source_key:
        raise CurationInvalid("format or source")
    base_files = {p: c for p, c in files.items() if p != CURATION_PATH}
    base = doc["base_version"]
    if not (isinstance(base, dict) and set(base) == {"label", "fingerprint"} and isinstance(base["label"], str)
            and base["label"].strip()):
        raise CurationInvalid("base version")
    if base["fingerprint"] != version_identity(files_digest(base_files), source_type, data_kind, grouping_unit):
        raise CurationInvalid("the base version's fingerprint is not this version's")
    documents = {}
    for path, content in base_files.items():
        if file_role(path) == "documentation":
            try:
                documents[path] = content.decode("utf-8")
            except UnicodeDecodeError:
                raise CurationInvalid(f"{path} is not UTF-8") from None
    values = doc["values"]
    if not isinstance(values, dict):
        raise CurationInvalid("values")
    for field, e in values.items():
        if field not in CURATION_TARGETS or not isinstance(e, dict) or set(e) != ENTRY_KEYS:
            raise CurationInvalid(f"entry {field!r}")
        if not (isinstance(e["document"], str) and e["document"] in documents and isinstance(e["quote"], str)):
            raise CurationInvalid(f"entry {field!r}: document")
        result = quotes.check(field, e["value"], e["quote"], {e["document"]: documents[e["document"]]})
        if result.code is not None:
            raise CurationInvalid(f"entry {field!r}: {result.code}")
        if not _positive_int(e["line"]) or result.located.line != e["line"] or result.term != e["term"]:
            raise CurationInvalid(f"entry {field!r}: line or term")
        if not (_positive_int(e["proposal"]) and _positive_int(e["agent_setting_version"])
                and isinstance(e["model"], str) and e["model"].strip()):
            raise CurationInvalid(f"entry {field!r}: proposal, model or settings version")
        by = e["accepted_by"]
        if not (isinstance(by, str) and by.strip() and len(by) <= ACCEPTOR_MAX):
            raise CurationInvalid(f"entry {field!r}: acceptor")
        try:
            when = datetime.fromisoformat(e["accepted_at"]) if isinstance(e["accepted_at"], str) else None
        except ValueError:
            when = None
        if when is None or when.tzinfo is None:
            raise CurationInvalid(f"entry {field!r}: acceptance time")
        if not (e["note"] is None or (isinstance(e["note"], str) and len(e["note"]) <= NOTE_MAX)):
            raise CurationInvalid(f"entry {field!r}: note")
    return doc


def curated_values(version: SealedVersion) -> dict[str, Value]:
    if CURATION_PATH not in version.files:
        return {}
    try:
        doc = check_curation(version.files, version.source_key, version.source_type, version.data_kind,
                             version.grouping_unit)
    except CurationInvalid as error:
        raise AdapterError(f"{CURATION_PATH}: cannot be read as a curation file for this version ({error})") from None
    out = {}
    for field, e in doc["values"].items():
        where = (f"line {e['line']}; Curator proposal {e['proposal']} ({e['model']}, settings version "
                 f"{e['agent_setting_version']}), accepted by {e['accepted_by']} on {e['accepted_at'][:10]}")
        out[field] = Value(e["value"], HARMONIZED_FIELDS[field], "assigned_from_source",
                           citation=Citation(f"{version.source_key}: {e['document']} (sealed with the source)",
                                             where, e["quote"]))
    return out


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
