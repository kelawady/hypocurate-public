"""The data sources and the agents, as people see them (build step 10b; PRD 9.5 and 9.6). Read-only.

- `sources_page`: every registered source (type, kind of data, licence, adapter status, whether it is on, its latest
  sealed version), and every source defined in code that is not registered yet. Registering one, and "Test connection
  and show sample records", are the pipeline's own functions (`sources.versions.register`,
  `sources.connection.test_connection`); the website only calls them.
- `agent_page`: a role's latest stored settings version (instruction, model, limits, role settings), read-only in
  sprint 1, and the "Fixed in code" panel: what the role receives at each stage (the access layer's own allow-lists
  and field descriptions), what it returns (the role's own output description), what it may call, and what it may not
  do. What a role receives and returns comes from the settings that enforce it; what it may call and may not do are
  fixed sentences summarizing CLAUDE.md's rules (`MAY_CALL`, `MAY_NOT`), not read from code.
"""
from __future__ import annotations

from sqlalchemy import Engine, text

from hypocurate.pipeline.run_view import snapshot

ROLE_NAMES = {"planner": "Planner", "curator": "Curator", "critic": "Critic", "analyst": "Analyst",
              "commentator": "Commentator"}
# What each role may not do (CLAUDE.md, "Rules the code must never break", 2), in the screens' words.
MAY_NOT = {
    "planner": "It fills the plan's template parameters from counts only and never sees an outcome value. Code checks "
               "its answer, and a named person confirms the question as tested before anything is locked.",
    "curator": "It proposes extraction details for a source's documentation, never the direction of a claim; it has no "
               "say over which records are included. The owner accepts or rejects each proposal.",
    "critic": "It classifies flags that code raised, from sources and metadata; it is told the kind of flag, not the "
              "numbers, and never sees outcome values. Its classes are advice only and are not used in decisions.",
    "analyst": "It explains results that code has already computed; code inserts every number, and its text is "
               "labelled as not verified.",
    "commentator": "Not built in sprint 1 (PRD 15, step 12): it reads nothing at any stage.",
}
MAY_CALL = "Nothing: agents return text only. No agent is given a tool, a database connection, SQL or a file path."


def sources_page(engine: Engine) -> dict:
    from hypocurate.sources.versions import SOURCES
    with snapshot(engine) as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(
            "SELECT s.key, s.name, s.source_type, s.data_kind, s.licence, s.adapter_status, s.enabled, "
            "s.grouping_unit, v.fingerprint, v.label AS version_label, "
            "to_char(v.sealed_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS sealed FROM source s "
            "LEFT JOIN LATERAL (SELECT sv.fingerprint, sv.label, sv.sealed_at FROM source_version sv WHERE "
            "sv.source_id = s.id AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) v ON true "
            "ORDER BY s.enabled DESC, s.key")).all()]
    registered = {r["key"] for r in rows}
    for r in rows:
        d = SOURCES.get(r["key"])
        r.update(constructed=bool(d and d.constructed), adapter_words="available" if r["adapter_status"] == "available"
                 else "adapter needed", enabled_words="on" if r["enabled"] else "off",
                 short_fingerprint=(r["fingerprint"] or "")[:12])
    unregistered = [{"key": k, "name": d.name, "data_kind": d.data_kind, "licence": d.licence,
                     "constructed": d.constructed} for k, d in SOURCES.items() if k not in registered]
    return {"sources": rows, "unregistered": unregistered}


def connection_page(engine: Engine, key: str, n: int = 5) -> dict:
    """'Test connection and show sample records' (PRD 9.6): the report of `connection.test_connection` (read-only)."""
    from hypocurate.sources.connection import test_connection
    report = test_connection(engine, key, n).to_json()
    sample = []
    for r in report["sample"]:
        h = r.get("harmonized") or {}

        def value(field):
            entry = h.get(field) or {}
            v = entry.get("value")
            return (f"{v:g} {entry.get('unit') or ''}".strip() if isinstance(v, (int, float)) else
                    (str(v) if v is not None else f"— ({entry.get('status', 'missing').replace('_', ' ')})"))
        sample.append({"item": r.get("source_item_key"), "alloy": r.get("alloy") or "—",
                       "grain_size": value("grain_size"), "yield_strength": value("yield_strength"),
                       "paper": r.get("paper_reference") or r.get("paper_doi") or "—"})
    return {**report, "sample_rows": sample,
            "statuses": ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(report["status_counts"].items())),
            "unrecognized_words": ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(report["unrecognized"]
                                                                                            .items()) if v) or "none"}


def _receives(role: str) -> list[dict]:
    from hypocurate.access.allowlist import ALLOWED, FIELDS
    out = []
    for stage, fields in sorted((ALLOWED.get(role) or {}).items()):
        out.append({"stage": stage.replace("_", " "),
                    "fields": [{"field": f.replace("_", " "), "words": FIELDS.get(f, "")} for f in sorted(fields)]})
    return out


def _returns(role: str) -> str:
    import importlib
    if role == "commentator":
        return "Nothing yet (step 12)."
    module = importlib.import_module(f"hypocurate.pipeline.agents.{role}")
    return getattr(module, "OUTPUT_DESCRIPTION", "Text, checked by code.")


def agents_list(engine: Engine) -> list[dict]:
    with snapshot(engine) as conn:
        versions = dict(conn.execute(text("SELECT role, max(version) FROM agent_setting GROUP BY role")).all())
    return [{"role": r, "name": n, "version": versions.get(r)} for r, n in ROLE_NAMES.items()]


def agent_page(engine: Engine, role: str) -> dict | None:
    if role not in ROLE_NAMES:
        return None
    with snapshot(engine) as conn:
        row = conn.execute(text(
            "SELECT version, instruction, model, limits, settings, "
            "to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created FROM agent_setting "
            "WHERE role = :r ORDER BY version DESC LIMIT 1"), dict(r=role)).one_or_none()
    stored = None
    if row is not None:
        stored = {"version": row.version, "instruction": row.instruction, "model": row.model, "created": row.created,
                  "limits": [f"{k.replace('_', ' ')}: {v}" for k, v in sorted((row.limits or {}).items())],
                  "settings": [f"{k.replace('_', ' ')}: {v}" for k, v in sorted((row.settings or {}).items())]}
    return {"role": role, "name": ROLE_NAMES[role], "stored": stored, "receives": _receives(role),
            "returns": _returns(role), "may_call": MAY_CALL, "may_not": MAY_NOT[role],
            "roles": agents_list(engine)}
