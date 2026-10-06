"""The curation workflow at source registration (step 8a; owner, 2026-10-06, Q2 and Q3;
register 'curator_registration', 'curation_acceptance').

1. `curate(key)`: one Curator call on the source's newest sealed version, through one registration
   invocation (`agent_invocation`) bound by the dispatcher; refused before any model call for a
   source not grouped by dataset (a compilation of papers: a source-wide value would be a guess for
   each paper), for a version without documentation, or for a version already curated. Every
   proposal is stored (`curator_proposal`) as code decided it.
2. `decide(proposal, accepted|rejected, by)`: a person's decision on a proposal that passed the
   checks, written once with the database's time. The command line takes the name as given.
3. `seal_curation(key)`: a new sealed version: the base version's files plus `curation.json`, the
   accepted values only, each with its quote, document, line, proposal, model and settings version,
   who accepted it and when. Unanswered and rejected proposals are left out (the field stays
   unassigned). Sealed by the same registration code, so its fingerprint covers the curation.
4. `curation_file(key)`: that file's bytes, to be frozen into `data/` (with the owner's approval):
   registering the frozen source then gives the same curated version in any database, with no
   model call.

Adapters apply the curated values only where the table gives no value (`adapters.apply_curation`).
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from hypocurate.db.retry import run_transaction
from hypocurate.sources.curated import CURATION_FORMAT
from hypocurate.sources.versions import (CURATION_PATH, SOURCES, Registered, _register_in, latest_sealed_version_id,
                                         load_sealed_version)

CODES = {
    "unknown_source": "no such source",
    "compilation_source": "the source is grouped by paper (a compilation): a value for the whole source would be a "
                          "guess for each paper, so it is not curated (owner, 2026-10-06)",
    "no_documentation": "the source's newest version holds no documentation",
    "already_curated": "the source's newest version is already a curated version",
    "unknown_proposal": "no such proposal",
    "not_decidable": "only a proposal that passed the checks can be accepted or rejected",
    "already_decided": "this proposal has already been decided",
    "nothing_curated": "the version has no curation invocation",
    "conflicting_acceptances": "more than one proposal is accepted for the same field",
}


class CurationRefused(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"{code}: {CODES[code]}")


def _version(engine: Engine, key: str):
    if key not in SOURCES:
        raise CurationRefused("unknown_source")
    with engine.connect() as conn:
        return load_sealed_version(conn, latest_sealed_version_id(conn, key))


def curate(engine: Engine, key: str, *, ceiling: Decimal | None = None,
           client_options: Mapping[str, Any] | None = None) -> dict:
    """One Curator call and its stored proposals; a summary for the command line."""
    from hypocurate.access.dispatch import bind_invocation
    from hypocurate.access.inputs import role_input
    from hypocurate.pipeline.agents import curator
    from hypocurate.pipeline.agents.interface import call_agent
    from hypocurate.pipeline.agents.settings import SETTINGS, ensure_setting

    version = _version(engine, key)
    if version.grouping_unit != "dataset":
        raise CurationRefused("compilation_source")
    if CURATION_PATH in version.files:
        raise CurationRefused("already_curated")
    if not version.documentation:
        raise CurationRefused("no_documentation")
    setting = ensure_setting(engine, "curator")
    invocation = run_transaction(engine, lambda conn: conn.execute(text(
        "INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
        "VALUES ('registration', :v, 'curator', :a) RETURNING id"), dict(v=version.id, a=setting)).scalar_one())
    data = role_input(bind_invocation(engine, invocation))
    s = SETTINGS["curator"]
    result = call_agent(engine, invocation, curator.signature(s["instruction"]), curator.render_inputs(data),
                        model=s["model"], max_tokens=s["limits"]["max_tokens"],
                        max_output_chars=s["limits"]["max_output_chars"], ceiling=ceiling,
                        lm_options=dict(s["settings"]), client_options=client_options, check=curator.check)
    summary = {"source": key, "version": version.id, "invocation": invocation, "attempts": result.attempts,
               "calls": result.calls}
    if result.failure is not None:
        return {**summary, "status": "failed", "code": result.failure, "proposals": [], "ignored_keys": []}
    proposals, ignored = curator.proposals_from(result.outputs["proposals"], data["source_documentation"]["documents"])

    def store(conn):
        ids = []
        for p in proposals:
            ids.append(conn.execute(text(
                "INSERT INTO curator_proposal (invocation_id, source_version_id, field, status, value, quote, "
                "document_path, line, term, refusal_code) VALUES (:i, :v, :f, :st, CAST(:val AS jsonb), :q, :d, :l, "
                ":t, :rc) RETURNING id"),
                # No value is SQL NULL, never the JSON value null (the database's shape checks).
                dict(i=invocation, v=version.id, f=p.field, st=p.status,
                     val=None if p.value is None else json.dumps(p.value), q=p.quote, d=p.document,
                     l=p.line, t=p.term, rc=p.refusal_code)).scalar_one())
        return ids

    ids = run_transaction(engine, store)
    return {**summary, "status": "done", "ignored_keys": ignored,
            "proposals": [{"id": i, **p.__dict__} for i, p in zip(ids, proposals)]}


def proposals(engine: Engine, key: str) -> list[dict]:
    """The proposals for the source's newest version, with any decision."""
    version = _version(engine, key)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT p.id, p.invocation_id, p.field, p.status, p.value, p.quote, p.document_path, p.line, p.term, "
            "p.refusal_code, d.decision, d.decided_by, d.decided_at FROM curator_proposal p "
            "LEFT JOIN curator_decision d ON d.proposal_id = p.id WHERE p.source_version_id = :v ORDER BY p.id"),
            dict(v=version.id)).mappings().all()
    return [{**r, "decided_at": r["decided_at"].isoformat() if r["decided_at"] else None} for r in rows]


def decide(engine: Engine, proposal_id: int, decision: str, by: str, note: str | None = None) -> dict:
    if decision not in ("accepted", "rejected"):
        raise ValueError(decision)

    def transaction(conn):
        status = conn.execute(text("SELECT status FROM curator_proposal WHERE id = :p"),
                              dict(p=proposal_id)).scalar_one_or_none()
        if status is None:
            return "unknown_proposal"
        if status != "proposed":
            return "not_decidable"
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM curator_decision WHERE proposal_id = :p)"),
                        dict(p=proposal_id)).scalar_one():
            return "already_decided"
        conn.execute(text("INSERT INTO curator_decision (proposal_id, decision, decided_by, note) "
                          "VALUES (:p, :d, :b, :n)"), dict(p=proposal_id, d=decision, b=by, n=note))
        return None

    try:
        code = run_transaction(engine, transaction)
    except IntegrityError:  # a concurrent second decision (unique), or the database's own refusal
        code = "already_decided"
    if code:
        raise CurationRefused(code)
    return {"proposal": proposal_id, "decision": decision, "decided_by": by}


def _accepted(conn, version_id: int) -> list:
    return conn.execute(text(
        "SELECT p.id, p.field, p.value, p.quote, p.document_path, p.line, p.term, s.model, s.version AS setting_version, "
        "d.decided_by, d.decided_at, d.note FROM curator_proposal p "
        "JOIN curator_decision d ON d.proposal_id = p.id AND d.decision = 'accepted' "
        "JOIN agent_invocation i ON i.id = p.invocation_id JOIN agent_setting s ON s.id = i.agent_setting_id "
        "WHERE p.source_version_id = :v ORDER BY p.field, p.id"), dict(v=version_id)).all()


def curation_document(version, accepted) -> bytes:
    """The curation file: accepted values only, deterministic bytes."""
    values = {}
    for r in accepted:
        values[r.field] = {"value": r.value, "document": r.document_path, "line": r.line, "quote": r.quote,
                           "term": r.term, "proposal": r.id, "model": r.model, "agent_setting_version": r.setting_version,
                           "accepted_by": r.decided_by, "accepted_at": r.decided_at.isoformat(), "note": r.note}
    body = {"format": CURATION_FORMAT, "source": version.source_key,
            "base_version": {"label": version.label, "fingerprint": version.fingerprint}, "values": values}
    return (json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def seal_curation(engine: Engine, key: str) -> Registered:
    version = _version(engine, key)
    if CURATION_PATH in version.files:
        raise CurationRefused("already_curated")
    definition = SOURCES[key]

    def transaction(conn):
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM agent_invocation WHERE source_version_id = :v)"),
                            dict(v=version.id)).scalar_one():
            return ("refused", "nothing_curated")
        accepted = _accepted(conn, version.id)
        fields = [r.field for r in accepted]
        if len(fields) != len(set(fields)):
            return ("refused", "conflicting_acceptances")
        files = {**dict(version.files), CURATION_PATH: curation_document(version, accepted)}
        obtained = conn.execute(text("SELECT obtained_on FROM source_version WHERE id = :v"),
                                dict(v=version.id)).scalar_one()
        return ("ok", _register_in(conn, definition, files, obtained, label=f"{version.label} + curation"))

    outcome = run_transaction(engine, transaction)
    if outcome[0] == "refused":
        raise CurationRefused(outcome[1])
    return outcome[1]


def curate_guarded(payload: dict) -> dict:
    """The command line's `sources curate`, run in the guarded process (the tripwire watches the agent
    code). Only JSON-safe values cross back; the parent never prints the child's error text."""
    from hypocurate.config import load_settings
    from hypocurate.db.engine import make_engine
    engine = make_engine(load_settings(web=False).database_url)
    try:
        ceiling = Decimal(payload["ceiling"]) if payload.get("ceiling") is not None else None
        return json.loads(json.dumps(curate(engine, payload["key"], ceiling=ceiling,
                                            client_options=payload.get("client_options")), default=str))
    finally:
        engine.dispose()


def curation_file(engine: Engine, key: str) -> bytes:
    """The curation file of the source's newest (curated) version."""
    version = _version(engine, key)
    if CURATION_PATH not in version.files:
        raise CurationRefused("nothing_curated")
    return version.files[CURATION_PATH]
