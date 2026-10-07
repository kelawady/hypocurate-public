"""The Curator (step 8a; owner, 2026-10-06, Q2 and Q3; register 'curator_registration').

At registration of a source version grouped by dataset, the Curator reads that version's
documentation and proposes, for each target field, one value that holds for all of the source's
measurements, with the exact sentence it relied on, or says "not stated". It is not told any claim,
plan or data row (its access list holds only the documentation and the targets).

Code decides what a proposal is: `proposals_from` checks each entry (the field is a target, the
value is allowed, the quote is found in the documentation at word boundaries, holds a listed term and, for a
test condition, a testing word; `quotes.check`) and
stores it as 'proposed', 'refused' with a code, or 'not_stated'. A proposal takes effect only when a
person accepts it (`sources.curation`), and only where a table gives no value.

The answer's form: one JSON object, one key per target field; each value is "not stated" or
{"value": ..., "quote": ...}. A missing key means "not stated"; a key that is not a target is
ignored and reported. An answer that is not such an object is malformed (corrected once, by the
common interface).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.pipeline.agents import libraries, quotes

OUTPUT_DESCRIPTION = ('One JSON object with one key per target field. The value of each key is either the string '
                      '"not stated" or an object {"value": <one of the allowed values, or a number in degrees '
                      'Celsius for test_temperature>, "quote": "<the one sentence that states it, copied word for '
                      'word>"}. Nothing else.')
STORED_MAX = 4000  # the database's bound on stored text (migration 0005)
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)


def signature(instruction: str):
    _, dspy = libraries.load()

    class CuratorSignature(dspy.Signature):
        documentation: str = dspy.InputField(desc="The source's documentation files, each introduced by its path.")
        targets: str = dspy.InputField(desc="The target fields, as JSON: each with its allowed values or unit.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        proposals: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)

    return CuratorSignature.with_instructions(instruction)


def render_inputs(curator_input: Mapping[str, Any]) -> dict[str, str]:
    """The Curator's request inputs, built only from its complete access-layer input."""
    documents = curator_input["source_documentation"]["documents"]
    documentation = "\n".join(f"=== {path} ===\n{text}" for path, text in sorted(documents.items()))
    return {"documentation": documentation,
            "targets": json.dumps(curator_input["curation_targets"], sort_keys=True, ensure_ascii=False)}


def parse(text: str) -> dict | None:
    """The answer as a JSON object, or None. Surrounding whitespace and one ``` fence are allowed."""
    body = text.strip()
    fenced = _FENCE.match(body)
    if fenced:
        body = fenced.group(1)
    try:
        value = json.loads(body)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def check(outputs: Mapping[str, str]) -> str | None:
    """The common interface's check: None if the answer can be read, else "malformed"."""
    return None if parse(outputs["proposals"]) is not None else "malformed"


@dataclass(frozen=True)
class Proposal:
    field: str
    status: str  # 'proposed', 'refused', 'not_stated'
    value: Any = None
    quote: str | None = None
    document: str | None = None
    line: int | None = None
    term: str | None = None
    refusal_code: str | None = None


def _stored(value: Any) -> Any:
    """What a refused entry keeps of the model's value: JSON within the bound, else nothing."""
    try:
        text = json.dumps(value)
    except (TypeError, ValueError):
        return None
    return value if len(text) <= STORED_MAX else None


def _entry(field: str, entry: Any, documents: Mapping[str, str]) -> Proposal:
    if isinstance(entry, str) and entry.strip().lower() == "not stated":
        return Proposal(field, "not_stated")
    if not (isinstance(entry, dict) and set(entry) == {"value", "quote"} and isinstance(entry["quote"], str)):
        return Proposal(field, "refused", refusal_code="malformed_entry")
    value, quote = entry["value"], entry["quote"]
    result = quotes.check(field, value, quote, documents)
    if result.code is not None:
        return Proposal(field, "refused", refusal_code=result.code, value=_stored(value), quote=quote[:STORED_MAX])
    return Proposal(field, "proposed", value=value, quote=quote, document=result.located.document,
                    line=result.located.line, term=result.term)


def proposals_from(text: str, documents: Mapping[str, str]) -> tuple[list[Proposal], list[str]]:
    """One proposal per target field (in field order) and the keys that are not targets."""
    data = parse(text)
    if data is None:
        raise ValueError("the answer is not a JSON object")  # the interface's check refuses it first
    proposals = [_entry(field, data.get(field, "not stated"), documents) for field in sorted(CURATION_TARGETS)]
    return proposals, sorted(k for k in data if k not in CURATION_TARGETS)
