"""The reach steps for a selection, each skipped when its result is already stored (R2): look up, download, check
for supplements, parse. Run from the command line in the Codespace (owner, 2026-10-22: reach runs locally, then
loads); never by the worker or the website."""
from __future__ import annotations

from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from hypocurate.documents import lookup as lk
from hypocurate.documents import store
from hypocurate.documents.select import Selection


def _done(engine: Engine, doi_key: str, action: str) -> bool:
    with engine.connect() as conn:
        return conn.execute(text("SELECT EXISTS (SELECT 1 FROM search_log WHERE doi_key = :k AND action = :a)"),
                            dict(k=doi_key, a=action)).scalar()


def gather(engine: Engine, selection: Selection, get=lk.http_get, pause: float = lk.PAUSE_S,
           say: Callable[[str], None] = print) -> None:
    """Lookup, download and supplement check for every paper not yet looked up."""
    for p in selection.papers:
        if _done(engine, p.doi_key, "unpaywall_lookup"):
            say(f"{p.doi_key}: looked up before; skipped")
            continue
        found = lk.lookup(p.doi, p.doi_key, get, pause)
        store.record_lookup(engine, found)
        doc = None
        if found.pdf_candidates():
            doc = store.store_document(engine, found, lk.download(found, get, pause))
        else:
            store.store_document(engine, found, lk.Download(None, None, None, (
                lk.LogEntry("download", p.doi_key, "not_found", None, None, "no open-access PDF address"),)))
        check = lk.supplements(found, get, pause)
        store.run_transaction(engine, lambda conn: store.log(conn, check.log))
        say(f"{p.doi_key}: oa={found.is_oa} pdf={'stored' if doc else 'no'} supplements={check.value}")


def parse_all(engine: Engine, selection: Selection, runner=store.run_parser, say: Callable[[str], None] = print) -> None:
    """Parses every stored article of the selection that has no parse yet."""
    with engine.connect() as conn:
        todo = conn.execute(text(
            "SELECT d.id, d.doi_key, d.pdf FROM document d WHERE d.kind = 'article' AND d.doi_key = ANY(:k) "
            "AND NOT EXISTS (SELECT 1 FROM document_parse p WHERE p.document_id = d.id) ORDER BY d.id"),
            dict(k=[p.doi_key for p in selection.papers])).all()
    for doc_id, key, pdf in todo:
        result = runner(bytes(pdf))
        store.store_parse(engine, doc_id, key, result)
        say(f"{key}: {result.get('status')} " + (f"{result.get('parser')}, {len(result.get('tables', []))} tables"
                                                  if result.get("status") == "parsed" else ""))


def _summary(engine: Engine, doi_key: str) -> dict | None:
    import json
    with engine.connect() as conn:
        detail = conn.execute(text("SELECT detail FROM search_log WHERE doi_key = :k AND action = 'select' "
                                   "AND detail LIKE 'lookup summary: %' ORDER BY id DESC LIMIT 1"),
                              dict(k=doi_key)).scalar()
    return json.loads(detail.removeprefix("lookup summary: ")) if detail else None


def _has_document(engine: Engine, doi_key: str) -> bool:
    with engine.connect() as conn:
        return conn.execute(text("SELECT EXISTS (SELECT 1 FROM document WHERE kind = 'article' AND doi_key = :k)"),
                            dict(k=doi_key)).scalar()


def retry_patterns(engine: Engine, selection: Selection, get=lk.http_get, pause: float = lk.PAUSE_S,
                   say: Callable[[str], None] = print) -> None:
    """For open-access papers with no document, the publishers' standard PDF addresses (owner, 2026-10-22)."""
    for p in selection.papers:
        summary = _summary(engine, p.doi_key)
        if not summary or not summary["is_oa"] or _has_document(engine, p.doi_key):
            continue
        candidates, found_log = lk.publisher_patterns(p.doi_key, get, pause)
        if not candidates:  # no pattern for this publisher, or its landing page was not reached (already logged)
            extra = [] if found_log else [lk.LogEntry("download", p.doi_key, "not_found", None, None,
                                                      "publisher pattern: none for this publisher")]
            store.run_transaction(engine, lambda conn: store.log(conn, found_log + extra))
            say(f"{p.doi_key}: " + ("publisher pattern: landing page not reached" if found_log else "no publisher pattern"))
            continue
        got = lk.download_from(p.doi_key, candidates, get, pause)
        got = lk.Download(got.pdf, got.url, got.source, tuple(found_log) + tuple(
            lk.LogEntry(e.action, e.doi_key, e.outcome, e.url, e.http_status,
                        f"publisher pattern: {e.detail or ''}".strip()[:lk.DETAIL_MAX]) for e in got.log))
        found = lk.Lookup(p.doi, p.doi_key, unpaywall={"is_oa": True, "oa_status": summary.get("oa_status"),
                                                       "best_oa_location": {"license": summary.get("license")}})
        doc = store.store_document(engine, found, got, oa_source=summary.get("flag_source") or "unpaywall")
        say(f"{p.doi_key}: pattern {'stored' if doc else 'failed'}")


def why_automation_failed(engine: Engine, doi_key: str) -> str:
    """The automated download attempts for a paper, in one line (recorded with a fetch by hand)."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT outcome, http_status, detail FROM search_log WHERE doi_key = :k "
                                 "AND action = 'download' ORDER BY id"), dict(k=doi_key)).all()
    if not rows:
        return "no automated download was attempted"
    return "; ".join(f"{o}" + (f" (HTTP {s})" if s else "") + (f": {d}" if d else "") for o, s, d in rows)[:1500]
