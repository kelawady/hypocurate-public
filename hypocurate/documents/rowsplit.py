"""Docling + row split v1 (owner, 2026-10-23; register 'pilot_row_split'): a fixed rule that splits a table row
Docling merged, applied to a stored parse and stored as a new parse (the old one is kept).

A row (never the header, row 0) is split into N rows when:
- every one of its non-empty cells holds either one item or exactly N items, N >= 2;
- at least two cells hold N items, and every cell with N items holds numeric items only.
Items are separated by whitespace not preceded by a comma, so '675, 1 700, 1' holds two items ('675, 1', '700, 1').
A one-item cell is copied to every new row; the k-th item of each N-item cell goes to the k-th new row. Text is copied
verbatim; no number is changed. Each table that has split rows records `row_origin`: for every row of the new table,
the source row and the part (k of N), so a provenance of a split row resolves to the merged source cell too.

A row that has a cell with two or more numeric items but does not meet the rule stays as it was and is listed in the
table's `rows_merged` (the source row indexes): 'rows merged by the parser', counted per paper as a parse-quality
cause."""
from __future__ import annotations

import copy
import re

RULE = "docling + row split v1"
PARSER_VERSION_SUFFIX = "+rowsplit-1"
_ITEM_SPLIT = re.compile(r"(?<!,)\s+")
_NUMERIC_ITEM = re.compile(r"^[~∼≈<>]?\d+(?:\.\d+)?(?:,\s*\d+(?:\.\d+)?)?$")


def items(cell: str) -> list[str]:
    return [i for i in _ITEM_SPLIT.split(cell.strip()) if i] if cell and cell.strip() else []


def _numeric(parts: list[str]) -> bool:
    return bool(parts) and all(_NUMERIC_ITEM.match(p) for p in parts)


def split_row(row: list[str]) -> list[list[str]] | None:
    """The new rows, or None when the row is not split under the rule."""
    parts = [items(c) for c in row]
    counts = {len(p) for p in parts if len(p) >= 2}
    if len(counts) != 1:
        return None
    n = counts.pop()
    multi = [p for p in parts if len(p) == n]
    if len(multi) < 2 or not all(_numeric(p) for p in multi):
        return None
    if any(len(p) not in (0, 1, n) for p in parts):
        return None
    return [[(p[k] if len(p) == n else row[j].strip() if len(p) == 1 else "") for j, p in enumerate(parts)]
            for k in range(n)]


def merged(row: list[str]) -> bool:
    """A row with a cell holding two or more numeric items (a merged row, whether split or not)."""
    return any(len(p) >= 2 and _numeric(p) for p in (items(c) for c in row))


def split_parse(parsed: dict) -> tuple[dict, dict]:
    """The new parse (canonical form) and a summary {'rows_split': n, 'rows_merged': m, 'tables_changed': t}."""
    out = copy.deepcopy(parsed)
    split_n = merged_n = changed = 0
    for table in out.get("tables", []):
        rows, origin, still_merged = [], [], []
        for r, row in enumerate(table.get("rows", [])):
            new = split_row(row) if r > 0 else None
            if new:
                rows += new
                origin += [{"source_row": r, "part": k + 1, "of": len(new)} for k in range(len(new))]
                split_n += 1
            else:
                rows.append(row)
                origin.append({"source_row": r, "part": 1, "of": 1})
                if r > 0 and merged(row):
                    still_merged.append(r)
        merged_n += len(still_merged)
        if len(rows) != len(table.get("rows", [])):
            table["source_rows"] = table["rows"]
            table["rows"], table["row_origin"] = rows, origin
            changed += 1
        if still_merged:
            table["rows_merged"] = still_merged
    if changed:
        out["derived"] = {"rule": RULE, "rows_split": split_n, "rows_merged": merged_n}
        out["parser_version"] = str(out.get("parser_version", "")) + PARSER_VERSION_SUFFIX
    return out, {"rows_split": split_n, "rows_merged": merged_n, "tables_changed": changed}


def store_split(engine, parse_id: int) -> tuple[int | None, dict]:
    """Stores the split parse as a new parse of the same document when a table changes (the old parse kept), with a
    search-log entry naming the rule; returns (the new parse id or None, the summary)."""
    import hashlib
    import json
    from sqlalchemy import text
    from hypocurate.db.retry import run_transaction
    from hypocurate.documents.parse_worker import canonical
    from hypocurate.documents.store import CODE, log
    from hypocurate.documents.lookup import LogEntry
    with engine.connect() as conn:
        row = conn.execute(text("SELECT p.document_id, p.parser, p.fallback_used, p.parsed, d.doi_key FROM "
                                "document_parse p JOIN document d ON d.id = p.document_id WHERE p.id = :p "
                                "AND p.status = 'parsed'"), dict(p=parse_id)).one()
    new, summary = split_parse(json.loads(row.parsed))
    if not summary["tables_changed"]:
        return None, summary
    new["derived"]["from_parse"] = parse_id
    body = canonical(new)

    def write(conn):
        pid = conn.execute(text(
            "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
            "parsed_sha256, pages, tables_found) VALUES (:d, :p, :v, :f, 'parsed', :b, :h, :n, :t) RETURNING id"),
            dict(d=row.document_id, p=row.parser, v=new["parser_version"], f=row.fallback_used, b=body,
                 h=hashlib.sha256(body.encode("utf-8")).hexdigest(), n=max(1, int(new.get("pages") or 1)),
                 t=len(new.get("tables", [])))).scalar_one()
        log(conn, [LogEntry("parse", row.doi_key, "ok", None, None,
                            f"{RULE} on parse {parse_id}: {summary['rows_split']} row(s) split, "
                            f"{summary['rows_merged']} left merged")], CODE, row.document_id)
        return pid
    return run_transaction(engine, write), summary
