"""The note's P6 tables (Sprint 2 pilot, R7; owner, 2026-10-23, register 'pilot_s2_scoring'): the same rows and the
same columns for S0 (the Extractor's reference-blind output) and S2 (after the owner's acceptances and corrections),
so the two read side by side. One row per paper and table (vs annotation, vs compilation), then a pooled row per
table; each table names its snapshot. Built from the database and the annotation file alone, on each paper's
standing S0 (`evidence.standing_outputs`)."""
from __future__ import annotations

import csv
import io

from sqlalchemy.engine import Engine

COLUMNS = ("snapshot", "paper", "table", "reference_rows", "deferred", "denominator", "matched", "recall_or_recovery",
           "predictions_own", "precision_strict", "matched_to_compilation", "not_in_compilation_pending",
           "gs_value_correct", "ys_value_correct", "links_correct", "provenance_resolves", "condition_not_stated")
SUMMED = ("reference_rows", "deferred", "denominator", "matched", "predictions_own", "gs_value_correct",
          "ys_value_correct", "links_correct", "provenance_resolves", "condition_not_stated", "strict_errors",
          "unmatched_pending_adjudication")
LABEL = {"S0": "S0: the Extractor's verified, reference-blind output (first-pass, owner-annotated; provisional)",
         "S2": "S2: after the owner's acceptances and corrections (corrected performance; provisional)"}


def _row(snapshot, paper, table, m) -> dict:
    own = m.get("predictions_own") or 0
    comp = table == "vs compilation"
    return {"snapshot": snapshot, "paper": paper, "table": table, "reference_rows": m["reference_rows"],
            "deferred": m["deferred"], "denominator": m["denominator"], "matched": m["matched"],
            "recall_or_recovery": (f"{m['matched'] / m['denominator']:.3f}" if m["denominator"] else ""),
            "predictions_own": own,
            "precision_strict": (f"{(own - m['strict_errors']) / own:.3f}" if own else ""),
            "matched_to_compilation": m["matched"] if comp else "",
            "not_in_compilation_pending": m["unmatched_pending_adjudication"] if comp else "",
            **{k: m[k] for k in ("gs_value_correct", "ys_value_correct", "links_correct", "provenance_resolves",
                                 "condition_not_stated")}}


def build(engine: Engine) -> list[dict]:
    from hypocurate.pipeline import evidence as ev
    from hypocurate.scoring import score as sc
    from hypocurate.sources import adapters
    from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
    with engine.connect() as conn:
        outputs = ev.standing_outputs(conn)
        records = adapters.read(load_sealed_version(conn, latest_sealed_version_id(conn, "mpea"))).records
    rows = []
    for snapshot, predict in (("S0", sc.predictions_s0), ("S2", sc.predictions_s2)):
        pooled = {t: dict.fromkeys(SUMMED, 0) for t in ("vs annotation", "vs compilation")}
        for key, out in outputs:
            preds, _ = predict(engine, out)
            ann = sc.annotation_obs(engine, key) or None
            comp, _ = sc.compilation_obs(records, key, ann)
            tables = ([("vs annotation", sc.score_paper(preds, ann, "annotation"))] if ann else []) + [
                ("vs compilation", sc.score_paper(preds, comp, "compilation"))]
            for t, s in tables:
                m = s.metrics()
                rows.append(_row(snapshot, key.removeprefix("doi:"), t, m))
                for k in SUMMED:
                    pooled[t][k] += m.get(k) or 0
        rows += [_row(snapshot, "POOLED", t, m) for t, m in pooled.items()]
    return rows


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def to_markdown(rows: list[dict]) -> str:
    out = []
    for snap in ("S0", "S2"):
        out += [f"**{LABEL[snap]}**", "", "| " + " | ".join(COLUMNS[1:]) + " |", "|" + "---|" * (len(COLUMNS) - 1)]
        out += ["| " + " | ".join(str(r[c]) for c in COLUMNS[1:]) + " |" for r in rows if r["snapshot"] == snap]
        out.append("")
    return "\n".join(out)
