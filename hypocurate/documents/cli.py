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
                       ("extract", "run the Extractor (extract, verify, freeze S0) on one parsed paper (costs money)"),
                       ("rowsplit", "apply 'docling + row split v1' to the newest parse of every article in the selection"),
                       ("reconcile", "run the Reconciler on a paper's newest S0 (costs money)"),
                       ("evidence", "apply the R6 rules to the standing v4 S0s and print observations by state and reason"),
                       ("review-export", "write the owner's review sheet (.xlsx) over the newest v4 S0s"),
                       ("review-load", "load a returned review sheet: decisions, corrections, findings, minutes"),
                       ("reach", "print the reach table and its milestones")):
        p = docs_sub.add_parser(name, help=text)
        p.add_argument("--source", default="mpea", choices=SOURCES)
        if name == "reach":
            p.add_argument("--csv", help="also write the table as CSV to this file")
        if name == "reconcile":
            p.add_argument("--doi", required=True)
        if name == "evidence":
            p.add_argument("--status-only", action="store_true", help="print the states without applying the rules")
        if name == "review-export":
            p.add_argument("--out", required=True, help="the .xlsx file to write")
        if name == "review-load":
            p.add_argument("--file", required=True, help="the returned .xlsx file")
            p.add_argument("--by", required=True, help="the person who made the decisions")
            p.add_argument("--no-minutes", action="store_true",
                           help="the Minutes tab is not the owner's time (e.g. an AI-assisted review): not logged")
        if name == "extract":
            p.add_argument("--doi", required=True, help="the paper's DOI (one of the selection's papers)")
            p.add_argument("--spec", default="H1_v1", help="the evidence specification (default H1_v1)")
        if name == "add-by-hand":
            p.add_argument("--doi", required=True, help="the paper's DOI (one of the selection's papers)")
            p.add_argument("--file", required=True, help="the PDF as downloaded")
            p.add_argument("--url", required=True, help="the address the PDF was downloaded from in the browser")
            p.add_argument("--by", required=True, help="the name of the person who fetched it")
            p.add_argument("--access-method", default="institutional_credential",
                           choices=("none", "registration", "api_key", "institutional_credential", "manual_fetch"),
                           help="how the document was accessed (default: institutional_credential)")
            p.add_argument("--access-note", default="fetched manually")


def _selection(engine: Engine, source: str):
    from hypocurate.documents.select import fcc_grain_size
    from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
    with engine.connect() as conn:
        version = load_sealed_version(conn, latest_sealed_version_id(conn, source))
    return fcc_grain_size(version)


def _extract(engine: Engine, args) -> int:
    from sqlalchemy import text
    from hypocurate.pipeline.extraction import model_extractor as mx
    from hypocurate.sources.normalize import doi_group_key
    key = doi_group_key(args.doi)
    with engine.connect() as conn:
        parse_id = conn.execute(text(
            "SELECT p.id FROM document_parse p JOIN document d ON d.id = p.document_id WHERE d.doi_key = :k "
            "AND d.kind = 'article' AND p.status = 'parsed' ORDER BY p.id DESC LIMIT 1"), dict(k=key)).scalar()
    if parse_id is None:
        print(f"error: no parsed document for {args.doi}", file=sys.stderr)
        return 1
    run = mx.extract_document(engine, parse_id, args.spec)
    report = {"doi_key": key, "parse": parse_id, "failure": run.failure, "calls": run.calls, "cost_usd": str(run.cost),
              "draft_output": run.draft_output_id,
              "s0": None if run.frozen is None else {"output": run.frozen.output_id, "snapshot": run.frozen.snapshot_id,
                                                     "raw_sha256": run.frozen.raw_sha256,
                                                     "events_sha256": run.frozen.events_sha256,
                                                     "observations": run.frozen.observations},
              "verification": None if run.verified is None else run.verified.answers,
              "conversion_problems": None if run.verified is None else len(run.verified.conversion)}
    print(json.dumps(report, indent=1))
    stops = mx.stop_reasons(run)
    for s in stops:
        print(f"STOP (owner's rule): {s}", file=sys.stderr)
    return 2 if stops else (1 if run.failure else 0)


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
            doc = store.add_by_hand(engine, paper.doi, key, pdf, args.url, why_automation_failed(engine, key), args.by,
                                    args.access_method, args.access_note)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(json.dumps({"document": doc, "doi_key": key, "bytes": len(pdf), "by": args.by}))
        return 0
    if args.documents_command == "extract":
        return _extract(engine, args)
    if args.documents_command == "reconcile":
        from sqlalchemy import text
        from hypocurate.pipeline.reconcile import reconcile
        from hypocurate.pipeline.evidence import PROMPT_VERSION, standing_outputs
        from hypocurate.sources.normalize import doi_group_key
        with engine.connect() as conn:
            output = dict(standing_outputs(conn)).get(doi_group_key(args.doi))
        if output is None:
            print(f"error: no {PROMPT_VERSION} S0 for {args.doi}", file=sys.stderr)
            return 1
        run = reconcile(engine, output)
        print(json.dumps({"doi": args.doi, "output": output, "invocation": run.invocation, "mappings": run.mappings,
                          "unresolved": run.unresolved, "by_kind": run.by_kind, "failure": run.failure,
                          "cost_usd": str(run.cost)}))
        return 1 if run.failure else 0
    if args.documents_command == "evidence":
        from hypocurate.pipeline import evidence
        from hypocurate.sources import adapters
        from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
        with engine.connect() as conn:
            outputs = evidence.standing_outputs(conn)
            version = load_sealed_version(conn, latest_sealed_version_id(conn, "mpea"))
        compilation = {r.source_item_key: r for r in adapters.read(version).records}
        applied = None if args.status_only else evidence.apply_rules(engine, outputs)
        with engine.connect() as conn:
            statuses = evidence.status(conn, outputs, compilation)
        per_paper: dict = {}
        for st in statuses:
            per_paper.setdefault(st.doi_key, []).append(st)
        print(json.dumps({"rules": applied, "outputs": dict(outputs), "all": evidence.counts(statuses),
                          "primary_extracted": len(evidence.primary_extracted(statuses)),
                          "re_reports": sum(1 for st in statuses if st.rereport_of),
                          "re_reports_values_disagree": sum(1 for st in statuses if st.rereport_of and st.values_agree is False),
                          "per_paper": {k: evidence.counts(v) for k, v in sorted(per_paper.items())}}, indent=1))
        return 0
    if args.documents_command == "review-export":
        from pathlib import Path
        from hypocurate.pipeline import review_sheet
        Path(args.out).write_bytes(review_sheet.export(engine))
        print(f"wrote {args.out}")
        return 0
    if args.documents_command == "review-load":
        from pathlib import Path
        from hypocurate.pipeline import review_sheet
        path = Path(args.file)
        try:
            loaded = review_sheet.load(engine, path.name, path.read_bytes(), args.by,
                                       minutes_are_owner_time=not args.no_minutes)
        except review_sheet.SheetRefused as e:
            print("the review sheet is refused; nothing was written:", file=sys.stderr)
            for problem in e.problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        print(json.dumps(loaded.__dict__))
        return 0
    if args.documents_command == "rowsplit":
        from sqlalchemy import text
        from hypocurate.documents.rowsplit import store_split
        with engine.connect() as conn:
            newest = conn.execute(text(
                "SELECT DISTINCT ON (d.doi_key) d.doi_key, p.id FROM document_parse p JOIN document d ON d.id = p.document_id "
                "WHERE d.kind = 'article' AND p.status = 'parsed' AND d.doi_key = ANY(:k) ORDER BY d.doi_key, p.id DESC"),
                dict(k=[p.doi_key for p in selection.papers])).all()
        for key, parse_id in newest:
            new, summary = store_split(engine, parse_id)
            print(json.dumps({"doi_key": key, "parse": parse_id, "new_parse": new} | summary))
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
