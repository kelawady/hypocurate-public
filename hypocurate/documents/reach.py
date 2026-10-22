"""The reach table (R2, P1): one row per paper behind the selection, with four milestones, computed from the stored
search log, documents and parses, never typed in (owner, 2026-10-22, register 'reach_milestones').

1. Open-access flag: Unpaywall's flag where it answered, else OpenAlex's; 'lookup failed' when neither answered.
2. Full text downloaded (by a program): a stored PDF fetched by code; otherwise the cause from the download attempts.
   A PDF a person fetched in a browser is shown apart (`fetched_by_hand`), so the automated reach stays as measured;
   its cause is "free to read in a browser, not fetchable by a program", distinct from "not open access".
3. Text and tables parsed: the newest parse of the newest document, with its parser and the tables found; a failure
   with its reason; 'not parsed yet' when none was tried.
4. Supplements available: 'yes' when a landing page links a supplementary file; otherwise 'not found by automatic
   check' (never 'none': the column never asserts that a paper has no supplement), or 'not checked'."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine

from hypocurate.documents.lookup import NOT_FOUND_BY_AUTOMATIC_CHECK
from hypocurate.documents.select import Selection
from hypocurate.documents.store import BROWSER_ONLY

DOWNLOADED_BY_PROGRAM = "downloaded by a program"
NOT_OPEN_ACCESS = "not open access in the lookup services (paywalled)"
OPEN_NOT_FETCHED = "open access, not fetched"

YES, NO = "yes", "no"


@dataclass(frozen=True)
class ReachRow:
    doi: str
    doi_key: str
    compilation_records: int
    records_with_yield_strength: int
    phase_column: str
    oa_flag: str
    oa_status: str | None
    license: str | None
    downloaded: str
    download_cause: str | None
    fetched_by_hand: str
    access_cause: str
    document_id: int | None
    parsed: str
    parser: str | None
    tables_found: int | None
    supplements: str


def _newest(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = r  # rows come ordered by id, so the last one stays
    return out


def rows(engine: Engine, selection: Selection) -> list[ReachRow]:
    keys = [p.doi_key for p in selection.papers]
    with engine.connect() as conn:
        log = conn.execute(text("SELECT doi_key, action, outcome, http_status, detail FROM search_log "
                                "WHERE doi_key = ANY(:k) ORDER BY id"), dict(k=keys)).mappings().all()
        articles = conn.execute(text("SELECT id, doi_key, by_hand FROM document WHERE kind = 'article' "
                                     "AND doi_key = ANY(:k) ORDER BY id"), dict(k=keys)).mappings().all()
        docs = _newest(articles, "doi_key")
        by_program = _newest([a for a in articles if not a["by_hand"]], "doi_key")
        by_hand = _newest([a for a in articles if a["by_hand"]], "doi_key")
        parses = _newest(conn.execute(text(
            "SELECT p.document_id, p.status, p.parser, p.tables_found, p.failure_reason FROM document_parse p "
            "JOIN document d ON d.id = p.document_id WHERE d.doi_key = ANY(:k) ORDER BY p.id"),
            dict(k=keys)).mappings().all(), "document_id")
    out = []
    for p in selection.papers:
        mine = [e for e in log if e["doi_key"] == p.doi_key]
        summaries = [json.loads(e["detail"].removeprefix("lookup summary: ")) for e in mine
                     if e["action"] == "select" and (e["detail"] or "").startswith("lookup summary: ")]
        summary = summaries[-1] if summaries else None
        if summary is None:
            oa = "not looked up"
        elif summary["is_oa"] is None:
            oa = "lookup failed"
        else:
            oa = YES if summary["is_oa"] else NO
        doc = docs.get(p.doi_key)
        downloads = [e for e in mine if e["action"] == "download"]
        if p.doi_key in by_program:
            downloaded, cause = YES, None
        elif not downloads:
            downloaded, cause = NO, "not attempted" if oa == YES else "not open access" if oa == NO else oa
        else:
            downloaded = NO
            cause = "; ".join(f"{e['outcome']}" + (f" (HTTP {e['http_status']})" if e["http_status"] else "")
                              + (f": {e['detail']}" if e["detail"] and e["outcome"] != "ok" else "") for e in downloads)
        parse = parses.get(doc["id"]) if doc else None
        if doc is None:
            parsed = "no document"
        elif parse is None:
            parsed = "not parsed yet"
        elif parse["status"] == "parsed":
            parsed = YES
        else:
            parsed = f"failed: {parse['failure_reason']}"
        hand = YES if p.doi_key in by_hand else NO
        access = (DOWNLOADED_BY_PROGRAM if downloaded == YES else BROWSER_ONLY if hand == YES
                  else NOT_OPEN_ACCESS if oa == NO else OPEN_NOT_FETCHED if oa == YES else oa)
        checks = [e for e in mine if e["action"] == "supplement_check"]
        supplements = (YES if any(e["outcome"] == "found" for e in checks)
                       else NOT_FOUND_BY_AUTOMATIC_CHECK if checks else "not checked")
        out.append(ReachRow(p.doi, p.doi_key, p.records, p.records_with_yield_strength, selection.phase_column, oa,
                            (summary or {}).get("oa_status"), (summary or {}).get("license"), downloaded, cause,
                            hand, access, doc["id"] if doc else None, parsed, parse["parser"] if parse and parse["status"] == "parsed"
                            else None, parse["tables_found"] if parse and parse["status"] == "parsed" else None,
                            supplements))
    return out


def milestones(table: list[ReachRow]) -> dict:
    """The reach number at each milestone: papers, and the compilation records behind them."""
    def count(pred):
        sel = [r for r in table if pred(r)]
        return {"papers": len(sel), "records": sum(r.compilation_records for r in sel)}
    return {"all": count(lambda r: True),
            "open_access_flag": count(lambda r: r.oa_flag == YES),
            "full_text_downloaded": count(lambda r: r.downloaded == YES),
            "fetched_by_hand": count(lambda r: r.fetched_by_hand == YES),
            "text_and_tables_parsed": count(lambda r: r.parsed == YES),
            "supplements_available": count(lambda r: r.supplements == YES)}


def to_csv(table: list[ReachRow]) -> str:
    buf = io.StringIO()
    names = list(ReachRow.__dataclass_fields__)
    writer = csv.DictWriter(buf, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    for r in table:
        writer.writerow(asdict(r))
    return buf.getvalue()
