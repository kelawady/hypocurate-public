"""Does a provenance resolve in the stored parse? (PRD v1.2 R4, acceptance 2: "resolving to a stored page or table").

A table provenance resolves when its table exists, is on the cited page (when the parser gave the table a page), has
the cited row, and every word of the snippet occurs in that row; the cell separator '|' of the Extractor's rendering
(`model_extractor.render_document`) is not a word of the paper and is ignored (2026-10-23). A sentence provenance resolves when the sentence
occurs on the cited page and the snippet occurs in the sentence. Words are compared case-folded with runs of
whitespace collapsed. This is the 'supported' check of the acceptance matrix (a provenance check, not a correctness
check); it reads the parse only, never the compilation."""
from __future__ import annotations

from hypocurate.pipeline.extraction.interface import CandidateRecord, ParsedDocument, Provenance


CELL_SEPARATOR = "|"  # how the Extractor's rendering joins a table row's cells


def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()


def problem(document: ParsedDocument, p: Provenance) -> str | None:
    """None when the provenance resolves; otherwise what does not."""
    pages = int(document.content.get("pages") or 0)
    if not 1 <= p.page <= max(pages, 1):
        return f"page {p.page} is not in the document ({pages} pages)"
    if p.table_index is not None:
        table = document.table(p.table_index)
        if table is None:
            return f"no table {p.table_index}"
        if table.get("page") is not None and table["page"] != p.page:
            return f"table {p.table_index} is on page {table['page']}, not {p.page}"
        rows = table.get("rows", [])
        if not 0 <= p.row_index < len(rows):
            return f"table {p.table_index} has no row {p.row_index}"
        row = _norm(" ".join(rows[p.row_index]))
        missing = [w for w in _norm(p.snippet).split() if w not in row and w != CELL_SEPARATOR]
        return f"snippet words not in the row: {missing[:5]}" if missing else None
    page = _norm(document.page_text(p.page))
    if _norm(p.sentence) not in page:
        return f"the sentence is not on page {p.page}"
    if _norm(p.snippet) not in _norm(p.sentence):
        return "the snippet is not in the sentence"
    return None


def source_of(document: ParsedDocument, table_index: int, row_index: int) -> dict | None:
    """For a row the row split made (owner, 2026-10-23): the merged source row it came from and its part; None for a
    row that was not split."""
    table = document.table(table_index)
    origin = (table or {}).get("row_origin")
    if not origin or not 0 <= row_index < len(origin) or origin[row_index]["of"] == 1:
        return None
    o = origin[row_index]
    return {"source_row": o["source_row"], "part": o["part"], "of": o["of"],
            "source_cells": table["source_rows"][o["source_row"]]}


def problems(document: ParsedDocument, record: CandidateRecord) -> list[str]:
    """Every value's and link's provenance that does not resolve, by field."""
    out = []
    for v in record.values:
        if v.provenance is not None and (why := problem(document, v.provenance)):
            out.append(f"{v.field}: {why}")
    for link in record.links:
        if link.provenance is not None and (why := problem(document, link.provenance)):
            out.append(f"link {link.from_field}-{link.to_field}: {why}")
    return out
