"""`hypocurate documents …` (Sprint 2 pilot, R2): the selection, the reach steps and the reach table. Run locally in
the Codespace (owner, 2026-10-22); parsing needs the parse environment (`documents.store.PARSE_PYTHON_ENV`)."""
from __future__ import annotations

import json
import sys

from sqlalchemy.engine import Engine

SOURCES = ("mpea",)


def add_parser(sub) -> None:
    docs = sub.add_parser("documents", help="the pilot's documents: selection, reach steps and the reach table")
    docs_sub = docs.add_subparsers(dest="documents_command", required=True)
    for name, text in (("select", "list the papers behind the compilation's FCC grain-size records"),
                       ("gather", "look up, download and check supplements for papers not yet looked up (network)"),
                       ("parse", "parse the stored articles that have no parse yet (parse environment)"),
                       ("retry-patterns", "try publishers' standard PDF addresses for open-access papers not fetched"),
                       ("add-by-hand", "load a PDF a person fetched in a browser (done by hand in this pilot)"),
                       ("reach", "print the reach table and its milestones")):
        p = docs_sub.add_parser(name, help=text)
        p.add_argument("--source", default="mpea", choices=SOURCES)
        if name == "reach":
            p.add_argument("--csv", help="also write the table as CSV to this file")
        if name == "add-by-hand":
            p.add_argument("--doi", required=True, help="the paper's DOI (one of the selection's papers)")
            p.add_argument("--file", required=True, help="the PDF as downloaded")
            p.add_argument("--url", required=True, help="the address the PDF was downloaded from in the browser")
            p.add_argument("--by", required=True, help="the name of the person who fetched it")


def _selection(engine: Engine, source: str):
    from hypocurate.documents.select import fcc_grain_size
    from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
    with engine.connect() as conn:
        version = load_sealed_version(conn, latest_sealed_version_id(conn, source))
    return fcc_grain_size(version)


def command(args, engine: Engine) -> int:
    selection = _selection(engine, args.source)
    if args.documents_command == "select":
        print(json.dumps({"source": selection.source_key, "version_fingerprint": selection.version_fingerprint,
                          "phase_field": selection.phase_field, "phase_column": selection.phase_column,
                          "papers": len(selection.papers), "records": selection.records,
                          "records_without_doi": selection.records_without_doi}))
        for p in selection.papers:
            print(f"{p.records:3d} {p.records_with_yield_strength:3d}  {p.doi_key}")
        return 0
    if args.documents_command == "gather":
        from hypocurate.documents.steps import gather
        gather(engine, selection)
        return 0
    if args.documents_command == "parse":
        from hypocurate.documents.steps import parse_all
        parse_all(engine, selection)
        return 0
    if args.documents_command == "retry-patterns":
        from hypocurate.documents.steps import retry_patterns
        retry_patterns(engine, selection)
        return 0
    if args.documents_command == "add-by-hand":
        from hypocurate.documents import store
        from hypocurate.documents.steps import why_automation_failed
        from hypocurate.sources.normalize import doi_group_key
        key = doi_group_key(args.doi)
        paper = next((p for p in selection.papers if p.doi_key == key), None)
        if paper is None:
            print(f"error: {args.doi} is not one of the selection's papers", file=sys.stderr)
            return 1
        with open(args.file, "rb") as f:
            pdf = f.read()
        try:
            doc = store.add_by_hand(engine, paper.doi, key, pdf, args.url, why_automation_failed(engine, key), args.by)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(json.dumps({"document": doc, "doi_key": key, "bytes": len(pdf), "by": args.by}))
        return 0
    from hypocurate.documents import reach
    table = reach.rows(engine, selection)
    for r in table:
        print(f"{r.compilation_records:3d}  {r.doi_key:45s} oa={r.oa_flag:14s} pdf={r.downloaded:3s} "
              f"hand={r.fetched_by_hand:3s} "
              f"parsed={r.parsed[:30]:30s} tables={r.tables_found if r.tables_found is not None else '-'} "
              f"supplements={r.supplements}")
    print(json.dumps(reach.milestones(table)))
    if args.csv:
        with open(args.csv, "w", encoding="utf-8") as f:
            f.write(reach.to_csv(table))
        print(f"written {args.csv}", file=sys.stderr)
    return 0
