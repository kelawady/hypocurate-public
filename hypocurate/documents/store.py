"""Writes what the reach steps found: search-log entries, fetched documents and their parses (R2). Each write is one
transaction (`run_transaction`); these tables belong to no run, so `hc_write_lock` does not apply. Nothing is updated:
a re-fetch or re-parse is a new row (the tables are append-only)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.retry import run_transaction
from hypocurate.documents.lookup import Download, LogEntry, Lookup
from hypocurate.documents.parse_worker import canonical

CODE = "code"  # the actor named for steps code performs
# The parse environment's Python (owner, 2026-10-22: the parsers are installed only where parsing runs).
PARSE_PYTHON_ENV = "HYPOCURATE_PARSE_PYTHON"
PARSE_PYTHON_DEFAULT = "/tmp/hc-parse/venv/bin/python"
PARSE_TIMEOUT_S = 1800
REPO = Path(__file__).resolve().parents[2]


def log(conn: Connection, entries, actor: str = CODE, document_id: int | None = None) -> None:
    for e in entries:
        conn.execute(text("INSERT INTO search_log (action, doi_key, document_id, url, http_status, outcome, detail, actor, "
                          "by_hand) VALUES (:a, :k, :d, :u, :s, :o, :t, :by, :h)"),
                     dict(a=e.action, k=e.doi_key, d=document_id, u=e.url, s=e.http_status, o=e.outcome,
                          t=(e.detail or None) and e.detail[:2000], by=actor, h=e.action == "fetch_by_hand"))


def record_lookup(engine: Engine, found: Lookup) -> None:
    entries = list(found.log)
    entries.append(LogEntry("select", found.doi_key, "ok", None, None, "lookup summary: " + found.summary()))
    run_transaction(engine, lambda conn: log(conn, entries))


def store_document(engine: Engine, found: Lookup, got: Download, actor: str = CODE,
                   oa_source: str | None = None) -> int | None:
    """Stores the downloaded PDF (if any) and the download attempts. Returns the document id, or None. `oa_source`
    names where the open-access status came from when the address did not (a publisher pattern)."""
    def write(conn: Connection):
        doc = None
        if got.pdf is not None:
            doc = conn.execute(text(
                "INSERT INTO document (doi, doi_key, oa_status, oa_source, oa_url, license, pdf, pdf_sha256, fetched_by, "
                "access_method) VALUES (:doi, :k, :st, :src, :u, :lic, :pdf, :h, :by, 'none') RETURNING id"),
                dict(doi=found.doi, k=found.doi_key, st=found.oa_status, src=oa_source or got.source, u=got.url,
                     lic=found.license, pdf=got.pdf, h=hashlib.sha256(got.pdf).hexdigest(), by=actor)).scalar_one()
        log(conn, got.log, actor, doc)
        return doc
    return run_transaction(engine, write)


# A paper a person fetched by hand (owner, 2026-10-22; reworded 2026-10-23, register 'pilot_access_method': no
# public/paywalled distinction; the access method is recorded on the document).
MANUAL_FETCH = "obtained by manual fetch"


def add_by_hand(engine: Engine, doi: str, doi_key: str, pdf: bytes, url: str, why_automation_failed: str,
                by: str, access_method: str = "institutional_credential", access_note: str | None = "fetched manually") -> int:
    """A PDF a person fetched in a browser (done by hand in this pilot): the document, marked by hand, and a
    'fetch_by_hand' entry with the URL used, the person and the reason automation failed."""
    if not pdf.startswith(b"%PDF-"):
        raise ValueError("the file is not a PDF")

    def write(conn: Connection):
        doc = conn.execute(text(
            "INSERT INTO document (doi, doi_key, oa_source, oa_url, pdf, pdf_sha256, fetched_by, by_hand, access_method, "
            "access_note) VALUES (:doi, :k, 'by_hand', :u, :pdf, :h, :by, true, :am, :an) RETURNING id"),
            dict(doi=doi, k=doi_key, u=url, pdf=pdf, h=hashlib.sha256(pdf).hexdigest(), by=by, am=access_method,
                 an=access_note)).scalar_one()
        log(conn, [LogEntry("fetch_by_hand", doi_key, "ok", url[:2000], None,
                            f"{MANUAL_FETCH} (access: {access_method}); automation: {why_automation_failed}"[:2000])],
            by, doc)
        return doc
    return run_transaction(engine, write)


def parse_python() -> str:
    return os.environ.get(PARSE_PYTHON_ENV, PARSE_PYTHON_DEFAULT)


def run_parser(pdf: bytes, python: str | None = None) -> dict:
    """Runs the parse worker in the parse environment on a temporary copy of the PDF; returns its result."""
    with tempfile.TemporaryDirectory(prefix="hc-parse-") as tmp:
        source, target = Path(tmp, "in.pdf"), Path(tmp, "out.json")
        source.write_bytes(pdf)
        env = {**os.environ, "PYTHONPATH": str(REPO), "HF_HOME": os.environ.get("HF_HOME", "/tmp/hc-parse/hf")}
        try:
            done = subprocess.run([python or parse_python(), "-I", "-c",
                                   "import sys; sys.path.insert(0, sys.argv[1]); "
                                   "from hypocurate.documents.parse_worker import main; sys.exit(main(sys.argv[2:]))",
                                   str(REPO), str(source), str(target)],
                                  env=env, capture_output=True, timeout=PARSE_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as e:  # no parse environment, or it ran too long: recorded
            return {"status": "failed", "attempts": [{"parser": "worker", "outcome": "failed",
                                                      "error": f"{type(e).__name__}: {str(e)[:300]}"}]}
        if done.returncode != 0 or not target.exists():
            tail = done.stderr.decode("utf-8", errors="replace").strip().splitlines()[-1:] or ["no output"]
            return {"status": "failed", "attempts": [{"parser": "worker", "outcome": "failed",
                                                      "error": f"exit {done.returncode}: {tail[0][:300]}"}]}
        return json.loads(target.read_text(encoding="utf-8"))


def store_parse(engine: Engine, document_id: int, doi_key: str, result: dict) -> int:
    """Stores one parse result as a document_parse row, and the attempt in the search log."""
    attempts = result.get("attempts", [])

    def write(conn: Connection):
        if result.get("status") == "parsed":
            body = canonical({k: v for k, v in result.items() if k != "status"})
            pid = conn.execute(text(
                "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
                "parsed_sha256, pages, tables_found) VALUES (:d, :p, :v, :f, 'parsed', :b, :h, :n, :t) RETURNING id"),
                dict(d=document_id, p=result["parser"], v=result["parser_version"], f=result["fallback_used"], b=body,
                     h=hashlib.sha256(body.encode("utf-8")).hexdigest(), n=max(1, int(result["pages"] or 1)),
                     t=len(result["tables"]))).scalar_one()
            outcome, detail = "ok", f"{result['parser']}, {len(result['tables'])} tables; attempts: {json.dumps(attempts)}"
        else:
            reason = "; ".join(f"{a.get('parser')}: {a.get('error') or a.get('outcome')}" for a in attempts) or "failed"
            pid = conn.execute(text(
                "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, failure_reason) "
                "VALUES (:d, 'docling', 'n/a', :f, 'failed', :r) RETURNING id"),
                dict(d=document_id, f=any(a.get("parser") == "pymupdf" for a in attempts), r=reason[:2000])).scalar_one()
            outcome, detail = "failed", reason
        log(conn, [LogEntry("parse", doi_key, outcome, None, None, detail[:2000])], CODE, document_id)
        return pid
    return run_transaction(engine, write)
