"""`hypocurate scoring …` (Sprint 2 pilot, R7): the annotation template and the annotation loader."""
from __future__ import annotations

import json
import os
import sys

from sqlalchemy.engine import Engine


def add_parser(sub) -> None:
    scoring = sub.add_parser("scoring", help="the pilot's annotation template and loader")
    scoring_sub = scoring.add_subparsers(dest="scoring_command", required=True)
    template = scoring_sub.add_parser("template", help="write the annotation template (.xlsx)")
    template.add_argument("--out", required=True)
    sc = scoring_sub.add_parser("score", help="score a paper's S0 against its annotation and its compilation records")
    sc.add_argument("--doi", required=True)
    sc.add_argument("--out", help="write the full tables (pairs and unmatched lists included) as JSON to this file")
    sc.add_argument("--workbook", help="write the extraction workbook (S0 candidates with provenance) to this .xlsx")
    load = scoring_sub.add_parser("load-annotation", help="load an annotation file (refused whole on any problem)")
    load.add_argument("file")
    load.add_argument("--by", required=True, help="the name of the person loading it")


def _score(engine: Engine, args) -> int:
    """S0 of the newest verified output of the paper, against its annotation (if any) and its MPEA records."""
    from sqlalchemy import text
    from hypocurate.scoring import score as sc
    from hypocurate.sources import adapters
    from hypocurate.sources.normalize import doi_group_key
    from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
    key = doi_group_key(args.doi)
    with engine.connect() as conn:
        output = conn.execute(text(
            "SELECT x.id FROM extraction_output x JOIN document_parse p ON p.id = x.document_parse_id JOIN document d "
            "ON d.id = p.document_id JOIN evidence_snapshot s ON s.extraction_output_id = x.id AND s.name = 'S0' "
            "WHERE d.doi_key = :k ORDER BY x.id DESC LIMIT 1"), dict(k=key)).scalar()
        version = load_sealed_version(conn, latest_sealed_version_id(conn, "mpea"))
    if output is None:
        print(f"error: no S0 for {args.doi}", file=sys.stderr)
        return 1
    preds, described = sc.predictions_s0(engine, output)
    annotation = sc.annotation_obs(engine, key) or None
    comp, note = sc.compilation_obs(adapters.read(version).records, key, annotation)
    tables = []
    if annotation:
        tables.append(("vs annotation", sc.score_paper(preds, annotation, "annotation")))
    s = sc.score_paper(preds, comp, "compilation")
    s.note = note
    tables.append(("vs compilation (MPEA)", s))
    out = sc.report(tables, described | {"compilation_version_fingerprint": version.fingerprint})
    print(json.dumps({"snapshot": out["snapshot"], "rows": out["rows"]}, indent=1, default=str))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, default=str, ensure_ascii=False)
    if args.workbook:
        from hypocurate.scoring import extraction_workbook as xw
        with open(args.workbook, "wb") as f:
            f.write(xw.build(engine, output, xw.against_compilation(out)))
    return 0


def command(args, engine: Engine | None) -> int:
    if args.scoring_command == "template":
        from hypocurate.scoring.template import workbook
        data = workbook()
        with open(args.out, "wb") as f:
            f.write(data)
        print(json.dumps({"written": args.out, "bytes": len(data)}))
        return 0
    if args.scoring_command == "score":
        return _score(engine, args)
    from hypocurate.scoring.annotation import AnnotationRefused, load
    with open(args.file, "rb") as f:
        content = f.read()
    try:
        fid, rows, blank = load(engine, os.path.basename(args.file), content, args.by)
    except AnnotationRefused as e:
        for p in e.problems:
            print(f"refused: {p}", file=sys.stderr)
        return 1
    print(json.dumps({"annotation_file": fid, "rows": rows, "blank_rows_skipped": blank}))
    return 0
