"""The Extractor interface (Sprint 2 pilot, PRD v1.2 R4; Design D17): one typed function from a parsed document and an
evidence specification to candidate records, each with its values, its links, provenance for both, and a method tag.

An implementation returns what it read, as read: values as written, each with the page and the table row or sentence
it came from and the snippet, or an explicit ambiguity note; links between values with their evidence, or an
ambiguity note. It decides nothing about inclusion, never sees the compilation, and is not told the direction of the
claim. Code computes each record's identity (`extraction.identity`), checks provenance (`extraction.provenance`) and
freezes the output as S0 (`extraction.s0`). The pilot's model-call implementation and the fixture implementation are
two implementations behind this one signature; a later one (Rameshbabu et al.) is a thin adapter to it."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Protocol

from sqlalchemy import text
from sqlalchemy.engine import Connection

from hypocurate.db.models import LINK_KINDS, VALUE_FIELDS

SPECS = Path(__file__).parent / "specs"
PROMPTS = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class Provenance:
    """Where a value or link was read: a page and either a table row or a sentence, with the snippet as parsed. A
    passage (owner, 2026-10-23; register 'pilot_passage_provenance') is a page and a snippet only, which code accepts as
    a text citation: stored with the snippet as its sentence and marked `passage`; weaker than a sentence or a row."""
    page: int
    snippet: str
    table_index: int | None = None
    row_index: int | None = None
    sentence: str | None = None
    passage: bool = False

    @classmethod
    def passage_of(cls, page: int, snippet: str) -> "Provenance":
        return cls(page, snippet, sentence=snippet, passage=True)

    def __post_init__(self):
        if (self.table_index is None) != (self.row_index is None):
            raise ValueError("a table provenance names both the table and the row")
        if self.table_index is None and not self.sentence:
            raise ValueError("a provenance names a table row or a sentence")
        if not self.snippet.strip():
            raise ValueError("a provenance carries the snippet it cites")

    def to_json(self, document_id: int, parse_sha256: str) -> dict:
        out = {"document_id": document_id, "parse_sha256": parse_sha256, "page": self.page, "snippet": self.snippet}
        if self.table_index is not None:
            out |= {"table_index": self.table_index, "row_index": self.row_index}
        if self.sentence:
            out["sentence"] = self.sentence
        if self.passage:
            out["passage"] = True
        return out

    @property
    def location(self) -> str:
        """The location as text: 'p. 5, table 2, row 1' or 'p. 5, sentence: …' (used by the identity)."""
        if self.table_index is not None:
            return f"p. {self.page}, table {self.table_index}, row {self.row_index}"
        kind = "passage" if self.passage else "sentence"
        return f"p. {self.page}, {kind}: {' '.join(self.sentence.split())}"


@dataclass(frozen=True)
class Value:
    field: str  # one of VALUE_FIELDS
    text: str  # as written
    number: Decimal | None = None
    unit: str | None = None
    definition: str | None = None  # e.g. '0.2 % offset', 'linear intercept, twins excluded', 'as-processed'
    provenance: Provenance | None = None
    ambiguity_note: str | None = None

    def __post_init__(self):
        if self.field not in VALUE_FIELDS:
            raise ValueError(f"unknown field {self.field!r}")
        if not self.text.strip():
            raise ValueError("a value is written")

    @property
    def ambiguous(self) -> bool:
        return self.ambiguity_note is not None


@dataclass(frozen=True)
class Link:
    from_field: str
    to_field: str
    kind: str | None = None  # one of LINK_KINDS, with a provenance
    provenance: Provenance | None = None
    ambiguity_note: str | None = None

    def __post_init__(self):
        if self.kind is not None and self.kind not in LINK_KINDS:
            raise ValueError(f"unknown link kind {self.kind!r}")

    @property
    def ambiguous(self) -> bool:
        return self.ambiguity_note is not None


THIS_PAPER = "this paper"


@dataclass(frozen=True)
class CandidateRecord:
    values: tuple[Value, ...]
    links: tuple[Link, ...] = ()
    # 'this paper', or the citation as written when the row reports another paper's data (owner, 2026-10-23, Q-E)
    reported_from: str = THIS_PAPER

    def value(self, name: str) -> Value | None:
        return next((v for v in self.values if v.field == name), None)


@dataclass(frozen=True)
class Method:
    """How the records were extracted (stored on every output; Design D17): the kind ('model_call', 'fixture'), the
    implementation's name and version, the prompt version and, for a model call, the model."""
    method: str
    name: str
    version: str
    prompt_version: str
    model: str | None = None

    def to_json(self) -> dict:
        out = {"method": self.method, "name": self.name, "version": self.version, "prompt_version": self.prompt_version}
        return out | ({"model": self.model} if self.model else {})


@dataclass(frozen=True)
class ExtractionResult:
    method: Method
    raw_output: str  # exactly as returned; frozen in S0 with its hash
    records: tuple[CandidateRecord, ...]
    status: str = "returned"  # or 'failed' (the raw output is still kept)
    invocation_id: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    document_id: int
    parse_id: int
    parse_sha256: str
    doi_key: str
    content: Mapping

    @classmethod
    def load(cls, conn: Connection, parse_id: int) -> "ParsedDocument":
        row = conn.execute(text(
            "SELECT p.id, p.document_id, p.parsed, p.parsed_sha256, d.doi_key FROM document_parse p "
            "JOIN document d ON d.id = p.document_id WHERE p.id = :p AND p.status = 'parsed'"), dict(p=parse_id)).one()
        if hashlib.sha256(row.parsed.encode("utf-8")).hexdigest() != row.parsed_sha256:
            raise ValueError(f"parse {parse_id}: stored text does not match its hash")
        return cls(row.document_id, row.id, row.parsed_sha256, row.doi_key, json.loads(row.parsed))

    def table(self, index: int) -> Mapping | None:
        return next((t for t in self.content.get("tables", []) if t["index"] == index), None)

    def page_text(self, page: int) -> str:
        return " ".join(t["text"] for t in self.content.get("texts", []) if t["page"] == page)


@dataclass(frozen=True)
class EvidenceSpec:
    """An evidence specification as a locked file (PRD Appendix A; register 'evidence_specifications')."""
    key: str
    version: str
    sha256: str
    content: Mapping = field(repr=False)

    @classmethod
    def load(cls, name: str) -> "EvidenceSpec":
        raw = (SPECS / f"{name}.json").read_bytes()
        content = json.loads(raw)
        return cls(content["key"], content["version"], hashlib.sha256(raw).hexdigest(), content)


class Extractor(Protocol):
    method: Method

    def extract(self, document: ParsedDocument, spec: EvidenceSpec) -> ExtractionResult: ...
