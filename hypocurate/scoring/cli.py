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
    load = scoring_sub.add_parser("load-annotation", help="load an annotation file (refused whole on any problem)")
    load.add_argument("file")
    load.add_argument("--by", required=True, help="the name of the person loading it")


def command(args, engine: Engine | None) -> int:
    if args.scoring_command == "template":
        from hypocurate.scoring.template import workbook
        data = workbook()
        with open(args.out, "wb") as f:
            f.write(data)
        print(json.dumps({"written": args.out, "bytes": len(data)}))
        return 0
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
