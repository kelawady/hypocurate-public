"""Costs and times for the pilot's evidence package (Sprint 2 pilot, PRD v1.2 R15, P9; register 'pilot_costs').

Every number comes from stored rows, never from memory:
- per document: the model calls of its document invocations (`model_call` joined through `document_invocation`), by
  role (extractor, reconciler): calls, calls that failed, input and output tokens, and dollars (`cost`, the price of a
  succeeded call; a failed or interrupted call is reported with no cost), and the wall time of its calls (first start to last finish
  of each invocation, summed);
- per run: the run's model calls and dollars, and the wall time of each stage (`stage_result`, start to finish);
- the owner's time (`owner_time_log`) by activity and paper.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection


def per_document(conn: Connection) -> list[dict]:
    rows = conn.execute(text(
        "SELECT d.doi_key, d.id AS document, i.role, i.id AS invocation, count(m.id) AS calls, "
        "count(m.id) FILTER (WHERE m.status <> 'succeeded') AS failed, coalesce(sum(m.input_tokens), 0) AS input_tokens, "
        "coalesce(sum(m.output_tokens), 0) AS output_tokens, coalesce(sum(m.cost), 0) AS cost, "
        "extract(epoch FROM max(m.finished_at) - min(m.started_at)) AS seconds "
        "FROM document_invocation di JOIN agent_invocation i ON i.id = di.invocation_id "
        "JOIN document_parse p ON p.id = di.document_parse_id JOIN document d ON d.id = p.document_id "
        "LEFT JOIN model_call m ON m.invocation_id = i.id GROUP BY d.doi_key, d.id, i.role, i.id")).all()
    out: dict = {}
    for r in rows:
        k = (r.doi_key, r.document, r.role)
        e = out.setdefault(k, {"doi_key": r.doi_key, "document": r.document, "role": r.role, "invocations": 0,
                               "calls": 0, "failed_calls": 0, "input_tokens": 0, "output_tokens": 0,
                               "cost_usd": Decimal("0"), "wall_seconds": 0.0})
        e["invocations"] += 1
        e["calls"] += r.calls
        e["failed_calls"] += r.failed
        e["input_tokens"] += int(r.input_tokens)
        e["output_tokens"] += int(r.output_tokens)
        e["cost_usd"] += Decimal(r.cost)
        e["wall_seconds"] += float(r.seconds or 0)
    return sorted(out.values(), key=lambda e: (e["doi_key"], e["document"], e["role"]))


def per_run(conn: Connection, run_ids: list[int]) -> list[dict]:
    out = []
    for rid in run_ids:
        m = conn.execute(text("SELECT count(*) AS calls, count(*) FILTER (WHERE status <> 'succeeded') AS failed, "
                              "coalesce(sum(input_tokens), 0) AS i, coalesce(sum(output_tokens), 0) AS o, "
                              "coalesce(sum(cost), 0) AS cost FROM model_call WHERE run_id = :r"), dict(r=rid)).one()
        stages = [{"stage": s.stage, "attempt": s.attempt, "status": s.status, "seconds": float(s.seconds or 0)}
                  for s in conn.execute(text(
                      "SELECT stage, attempt, status, extract(epoch FROM finished_at - started_at) AS seconds "
                      "FROM stage_result WHERE run_id = :r ORDER BY started_at, id"), dict(r=rid)).all()]
        out.append({"run": rid, "calls": m.calls, "failed_calls": m.failed, "input_tokens": int(m.i),
                    "output_tokens": int(m.o), "cost_usd": Decimal(m.cost), "stages": stages})
    return out


def owner_time(conn: Connection) -> list[dict]:
    return [{"activity": r.activity, "doi_key": r.doi_key, "minutes": int(r.minutes), "entries": r.n}
            for r in conn.execute(text("SELECT activity, doi_key, sum(minutes) AS minutes, count(*) AS n FROM "
                                       "owner_time_log GROUP BY activity, doi_key ORDER BY activity, doi_key")).all()]


def report(conn: Connection, run_ids: list[int] = ()) -> dict:
    docs = per_document(conn)
    runs = per_run(conn, list(run_ids))
    return {"per_document": docs, "per_run": runs, "owner_time": owner_time(conn),
            "totals": {"documents_cost_usd": sum((d["cost_usd"] for d in docs), Decimal("0")),
                       "documents_calls": sum(d["calls"] for d in docs),
                       "documents_failed_calls": sum(d["failed_calls"] for d in docs),
                       "runs_cost_usd": sum((r["cost_usd"] for r in runs), Decimal("0"))}}
