"""What a query looks like to a person: read-only views for the query screens (build step 10b; PRD 9.1 to 9.3).

The queries list (paged by an ID cursor, as the runs list), one query with its versions and runs, the review list
(submitted versions, newest first) and one submitted version for review, and the choices the new-query form offers.
Every page is read from one snapshot (`run_view.snapshot`). Nothing here writes; the writes are `pipeline.queries`'s.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import run_view
from hypocurate.pipeline.run_view import STATUS_WORDS, money, snapshot, tokens

# Short source names for the queries list (owner's review, 2026-10-11); a query's own page gives the full names.
SOURCE_SHORT_NAMES = {"mpea": "MPEA", "tamu_fcc": "Texas A&M", "controlled_duplicates": "controlled duplicates"}
QUERIES_PER_PAGE = 50  # step 10b: as the runs list (register 'runs_list_pages' gives the reason for a cursor)
VERSION_STATUS_WORDS = {"draft": "draft", "submitted": "submitted for review", "returned": "returned for edits",
                        "dispatched": "dispatched"}
SUFFICIENCY_WORDS = {"fixed_minimum": "fixed minimum", "use_available": "use what is available (exploratory)"}


class NoSuchQuery(LookupError):
    pass


def _sources(conn: Connection, version_id: int) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(text(
        "SELECT s.key, s.name, s.data_kind FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
        "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=version_id)).all()]


def _latest_run(conn: Connection, hypothesis_id: int):
    return conn.execute(text(
        "SELECT r.id, r.status, r.outcome, r.evidence_level, r.experiment_flags FROM run r JOIN hypothesis_version hv "
        "ON hv.id = r.hypothesis_version_id WHERE hv.hypothesis_id = :h ORDER BY r.id DESC LIMIT 1"),
        dict(h=hypothesis_id)).one_or_none()


def _action(status: str, number: str, run_id: int | None) -> dict:
    """PRD 9.1: Edit for a draft or returned query, Review for a submitted one, Open run for a dispatched one."""
    if status in ("draft", "returned"):
        return {"label": "Edit", "href": f"/queries/{number}/edit"}
    if status == "submitted":
        return {"label": "Review", "href": f"/review/{number}"}
    return {"label": "Open run", "href": f"/runs/{run_id}"} if run_id else {"label": "Open", "href": f"/queries/{number}"}


def queries_list(engine: Engine, before: int | None = None, per_page: int = QUERIES_PER_PAGE) -> dict:
    """One page of queries, newest first, with each query's latest version; the next page's cursor is the last query
    shown (as the runs list)."""
    if before is not None and before < 1:
        raise NoSuchQuery(f"no queries before {before}")
    with snapshot(engine) as conn:
        total = conn.execute(text("SELECT count(*) FROM hypothesis")).scalar_one()
        rows = conn.execute(text(
            "SELECT h.id, h.number, h.narrower_of_run_id, v.id AS version_id, v.version_number, v.text, v.status, "
            "d.name AS domain, to_char(h.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created, "
            "coalesce(t.cap_cost, 0) AS cost FROM hypothesis h "
            "JOIN LATERAL (SELECT * FROM hypothesis_version x WHERE x.hypothesis_id = h.id "
            "ORDER BY x.version_number DESC LIMIT 1) v ON true JOIN domain d ON d.id = v.domain_id "
            "LEFT JOIN model_call_totals_by_query t ON t.hypothesis_id = h.id "
            "WHERE CAST(:before AS bigint) IS NULL OR h.id < :before ORDER BY h.id DESC LIMIT :n"),
            dict(before=before, n=per_page + 1)).all()
        more, rows = len(rows) > per_page, rows[:per_page]
        out = []
        for r in rows:
            run = _latest_run(conn, r.id)
            status = (STATUS_WORDS[run.status] if r.status == "dispatched" and run else VERSION_STATUS_WORDS[r.status])
            if run is not None and (run.experiment_flags or {}).get("constructed_test_data"):
                status += f" ({run_view.TEST_RUN_BADGE})"  # register 'constructed_test_runs': the label on every list
            out.append({
                "id": r.id, "number": r.number, "version": r.version_number, "created": r.created, "domain": r.domain,
                "claim": r.text, "narrower": r.narrower_of_run_id is not None,
                "sources": ", ".join(SOURCE_SHORT_NAMES.get(s["key"], s["key"]) for s in _sources(conn, r.version_id)),
                "status_words": status,
                "outcome": (run.outcome.replace("_", " ") + " in the sources searched")
                if run is not None and run.outcome else None,
                "cost": money(r.cost), "action": _action(r.status, r.number, run.id if run else None)})
    if not total:
        words = "No query yet."
    else:
        words = f"{total} quer{'y' if total == 1 else 'ies'} in all; " + (
            "the newest first." if before is None else "older queries, newest first.")
    return {"queries": out, "total": total, "words": words, "newest": before is not None,
            "older": out[-1]["id"] if more else None}


def query_page(engine: Engine, number: str) -> dict:
    """One query: every version (newest first) with its runs, the query's tokens and cost, and what can be done."""
    with snapshot(engine) as conn:
        h = conn.execute(text("SELECT id, number, narrower_of_run_id FROM hypothesis WHERE number = :n"),
                         dict(n=number)).one_or_none()
        if h is None:
            raise NoSuchQuery(f"no query {number}")
        versions = []
        for v in conn.execute(text(
                "SELECT v.id, v.version_number, v.text, v.status, v.note, v.review_comment, v.sufficiency_option, "
                "d.name AS domain, d.key AS domain_key, cd.name AS confirmed_domain, "
                "to_char(v.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created "
                "FROM hypothesis_version v JOIN domain d ON d.id = v.domain_id "
                "LEFT JOIN domain cd ON cd.id = v.confirmed_domain_id WHERE v.hypothesis_id = :h "
                "ORDER BY v.version_number DESC"), dict(h=h.id)).all():
            runs = [{"run": r.id, "status_words": STATUS_WORDS[r.status],
                     "evidence": run_view.evidence(r.evidence_level, None, None,
                                                   bool((r.experiment_flags or {}).get("constructed_test_data")),
                                                   failed=r.status == "failed")}
                    for r in conn.execute(text("SELECT id, status, evidence_level, experiment_flags FROM run WHERE "
                                               "hypothesis_version_id = :v ORDER BY id DESC"), dict(v=v.id)).all()]
            versions.append({"version": v.version_number, "claim": v.text, "status": v.status,
                             "status_words": VERSION_STATUS_WORDS[v.status], "note": v.note,
                             "review_comment": v.review_comment, "created": v.created,
                             "domain": v.confirmed_domain or v.domain, "domain_key": v.domain_key,
                             "sufficiency_key": v.sufficiency_option,
                             "sufficiency": SUFFICIENCY_WORDS.get(v.sufficiency_option, v.sufficiency_option),
                             "sources": _sources(conn, v.id), "runs": runs})
        cost = conn.execute(text("SELECT * FROM model_call_totals_by_query WHERE hypothesis_id = :h"),
                            dict(h=h.id)).one_or_none()
        open_run = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE "
            "hv.hypothesis_id = :h AND r.status IN ('queued', 'waiting', 'running'))"), dict(h=h.id)).scalar_one()
        original = conn.execute(text(
            "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h "
            "ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=h.narrower_of_run_id)).scalar_one_or_none() \
            if h.narrower_of_run_id else None
    latest = versions[0]
    c = dict(cost._mapping) if cost else {}
    return {"number": h.number, "versions": versions, "latest": latest, "narrower_of": original,
            "cost": {"calls": int(c.get("calls") or 0), "input_tokens": tokens(c.get("input_tokens")),
                     "output_tokens": tokens(c.get("output_tokens")), "counted": money(c.get("cap_cost"))},
            "can_edit": latest["status"] in ("draft", "returned"), "can_submit": latest["status"] == "draft",
            "can_review": latest["status"] == "submitted",
            "can_dispatch_again": latest["status"] == "dispatched" and not open_run}


def form_options(engine: Engine) -> dict:
    """What the new-query form offers: the domains (supported or not), the registered sources with their kind of
    data, and the sufficiency options with the fixed minimums."""
    from hypocurate.pipeline import profile
    from hypocurate.sources.versions import SOURCES
    with snapshot(engine) as conn:
        domains = [dict(r._mapping) for r in conn.execute(text(
            "SELECT key, name, supported FROM domain ORDER BY supported DESC, name")).all()]
        sources = [dict(r._mapping) for r in conn.execute(text(
            "SELECT key, name, data_kind, enabled, adapter_status FROM source ORDER BY enabled DESC, key")).all()]
    for s in sources:
        d = SOURCES.get(s["key"])
        s["constructed"] = bool(d and d.constructed)
    m = profile.FIXED_MINIMUMS
    return {"domains": domains, "sources": sources,
            "sufficiency": [
                {"key": "fixed_minimum", "words": SUFFICIENCY_WORDS["fixed_minimum"],
                 "detail": f"{m['min_records']} records, {m['min_alloys']} alloys with at least 2 grain sizes, "
                           f"{m['min_groups']} informative groups, {m['min_resid_df']} residual degrees of freedom"},
                {"key": "use_available", "words": SUFFICIENCY_WORDS["use_available"],
                 "detail": "the minimums are waived, never the validity checks; the result is labelled exploratory"}]}


def review_list(engine: Engine) -> list[dict]:
    """The review picker (PRD 9.3): every submitted version, newest first."""
    with snapshot(engine) as conn:
        return [dict(r._mapping) for r in conn.execute(text(
            "SELECT h.number, v.version_number AS version, v.text AS claim, d.name AS domain, "
            "to_char(v.submitted_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS submitted "
            "FROM hypothesis_version v JOIN hypothesis h ON h.id = v.hypothesis_id JOIN domain d ON d.id = v.domain_id "
            "WHERE v.status = 'submitted' ORDER BY v.submitted_at DESC, v.id DESC")).all()]


def review_page(engine: Engine, number: str) -> dict:
    """One submitted version for review (PRD 9.3): the hypothesis, the domain to confirm or change, the sufficiency
    option, the chosen sources, the latest stored settings version of each role a run records, the caps, the note."""
    from hypocurate.pipeline.agents import settings, spend
    page = query_page(engine, number)
    latest = page["latest"]
    if latest["status"] != "submitted":
        return {**page, "reviewable": False}
    with snapshot(engine) as conn:
        version_id, domain_key = conn.execute(text(
            "SELECT v.id, d.key FROM hypothesis_version v JOIN hypothesis h ON h.id = v.hypothesis_id JOIN domain d "
            "ON d.id = v.domain_id WHERE h.number = :n AND v.status = 'submitted'"), dict(n=number)).one()
        agents = [{"role": role, "version": conn.execute(text(
            "SELECT max(version) FROM agent_setting WHERE role = :r"), dict(r=role)).scalar_one()}
            for role in settings.RUN_ROLES]
    return {**page, "reviewable": True, "version_id": version_id, "domain_key": domain_key,
            "options": form_options(engine), "agents": agents,
            "caps": {"per_run": money(spend.RUN_CAP_USD), "monthly": money(spend.MONTH_CAP_USD)},
            "queue": run_view.queue_rows(engine)}

