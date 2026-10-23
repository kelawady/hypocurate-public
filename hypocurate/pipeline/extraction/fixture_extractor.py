"""A second, trivial Extractor behind the same interface (PRD v1.2 R4 acceptance): it reads a fixture's table rows
directly, with no model. Each row whose cells hold an alloy, a grain size and a yield strength becomes one record,
every value cited to its table row, linked by 'same_table_row'. Used by the tests and the two-paper end-to-end check;
it is not an extraction method for real papers."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from hypocurate.pipeline.extraction.interface import (CandidateRecord, EvidenceSpec, ExtractionResult, Link, Method,
                                                      ParsedDocument, Provenance, Value)

METHOD = Method(method="fixture", name="fixture_extractor", version="1", prompt_version="none")
COLUMNS = {"alloy": "alloy", "grain size": "grain_size", "yield strength": "yield_strength", "state": "processing_state",
           "specimen": "specimen_label", "test": "test_type", "temperature": "test_temperature"}


def _number(text: str) -> Decimal | None:
    try:
        return Decimal(text.split()[0])
    except (InvalidOperation, IndexError):
        return None


class FixtureExtractor:
    method = METHOD

    def extract(self, document: ParsedDocument, spec: EvidenceSpec) -> ExtractionResult:
        records = []
        for table in document.content.get("tables", []):
            header = [c.casefold() for c in table["rows"][0]] if table["rows"] else []
            fields = {i: next((f for k, f in COLUMNS.items() if k in h), None) for i, h in enumerate(header)}
            for r, row in enumerate(table["rows"][1:], start=1):
                values = []
                for i, cell in enumerate(row):
                    field = fields.get(i)
                    if field and cell.strip():
                        p = Provenance(page=table["page"] or 1, snippet=cell, table_index=table["index"], row_index=r)
                        values.append(Value(field, cell, _number(cell) if field in ("grain_size", "yield_strength")
                                            else None, provenance=p))
                names = {v.field for v in values}
                if {"alloy", "grain_size", "yield_strength"} <= names:
                    link_p = Provenance(page=table["page"] or 1, snippet=" ".join(row), table_index=table["index"],
                                        row_index=r)
                    records.append(CandidateRecord(tuple(values), (Link("grain_size", "yield_strength",
                                                                        "same_table_row", link_p),)))
        raw = json.dumps({"records": len(records), "spec": f"{spec.key} v{spec.version}"}, sort_keys=True)
        return ExtractionResult(METHOD, raw, tuple(records))
