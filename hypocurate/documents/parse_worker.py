"""Parses one PDF into the canonical JSON (owner, 2026-10-22: Docling first, pymupdf when Docling fails or finds no
tables; registers 'parser_choice', 'parsed_storage').

Run by `documents.parse` in the separate parse environment (Docling and pymupdf are not in the project's locks or any
image), as `python -m hypocurate.documents.parse_worker IN.pdf OUT.json`. It imports only the standard library and the
two parsers, so the parse environment needs nothing else from the project.

The canonical form (`FORMAT`): {"format", "parser", "parser_version", "fallback_used", "pages", "texts": [{"index",
"page", "text"}], "tables": [{"index", "page", "caption", "rows": [[cell text, ...], ...]}], "attempts": [...]}.
Pages count from 1; table and text indexes from 0, in reading order. Serialized with sorted keys, UTF-8, no spaces
(`canonical`), so the same parse gives the same bytes and the same SHA-256."""
from __future__ import annotations

import json
import sys
from importlib import metadata

FORMAT = "hypocurate-parse-1"


def canonical(doc: dict) -> str:
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _clean(s) -> str:
    return " ".join(str(s or "").split())


def with_docling(path: str) -> dict:
    from docling.document_converter import DocumentConverter
    doc = DocumentConverter().convert(path).document
    texts, tables = [], []
    for item in doc.texts:
        text = _clean(getattr(item, "text", ""))
        if text:
            page = item.prov[0].page_no if getattr(item, "prov", None) else None
            texts.append({"index": len(texts), "page": page, "text": text})
    for table in doc.tables:
        grid = table.data.grid if table.data else []
        rows = [[_clean(cell.text) for cell in row] for row in grid]
        page = table.prov[0].page_no if getattr(table, "prov", None) else None
        try:
            caption = _clean(table.caption_text(doc)) or None
        except Exception:  # a caption is optional; its absence is recorded as null
            caption = None
        tables.append({"index": len(tables), "page": page, "caption": caption, "rows": rows})
    pages = len(doc.pages) if getattr(doc, "pages", None) else max([t["page"] or 0 for t in texts] + [1])
    return {"parser": "docling", "parser_version": metadata.version("docling"), "pages": pages, "texts": texts,
            "tables": tables}


def with_pymupdf(path: str) -> dict:
    import pymupdf
    texts, tables = [], []
    with pymupdf.open(path) as pdf:
        for number, page in enumerate(pdf, start=1):
            for block in page.get_text("blocks", sort=True):
                text = _clean(block[4])
                if text and block[6] == 0:  # text blocks only
                    texts.append({"index": len(texts), "page": number, "text": text})
            for table in page.find_tables().tables:
                rows = [[_clean(c) for c in row] for row in table.extract()]
                tables.append({"index": len(tables), "page": number, "caption": None, "rows": rows})
        pages = pdf.page_count
    return {"parser": "pymupdf", "parser_version": metadata.version("pymupdf"), "pages": pages, "texts": texts,
            "tables": tables}


def parse(path: str, primary=with_docling, fallback=with_pymupdf) -> dict:
    """Docling first; pymupdf when Docling fails or finds no tables. pymupdf's result is kept only when it found
    tables (or Docling failed); otherwise Docling's. Every attempt is listed in `attempts`."""
    attempts = []
    first = second = None
    try:
        first = primary(path)
        attempts.append({"parser": first["parser"], "outcome": "parsed", "tables": len(first["tables"])})
    except Exception as e:  # recorded, never hidden: the parse row lists it
        attempts.append({"parser": "docling", "outcome": "failed", "error": f"{type(e).__name__}: {str(e)[:300]}"})
    if first is None or not first["tables"]:
        try:
            second = fallback(path)
            attempts.append({"parser": second["parser"], "outcome": "parsed", "tables": len(second["tables"])})
        except Exception as e:
            attempts.append({"parser": "pymupdf", "outcome": "failed", "error": f"{type(e).__name__}: {str(e)[:300]}"})
    if first is not None and (second is None or not second["tables"]):
        chosen, fallback_used = first, False
    elif second is not None:
        chosen, fallback_used = second, True
    else:
        return {"format": FORMAT, "status": "failed", "attempts": attempts}
    return {"format": FORMAT, "status": "parsed", "fallback_used": fallback_used, "attempts": attempts, **chosen}


def main(argv: list[str]) -> int:
    source, target = argv
    result = parse(source)
    with open(target, "w", encoding="utf-8") as f:
        f.write(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
