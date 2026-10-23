"""The pilot's evidence bundle (Sprint 2 pilot; owner, 2026-10-22, register 'pilot_bundle_load').

Extraction, the Reconciler, the owner's review and the R6 rules run locally against the development database. The
bundle carries their rows to the live database, which only the owner reaches (he loads it from his own terminal with
the live database address he sets himself; Claude Code never sees it):

- `export(engine)`: one zip with `manifest.json` (format, the source database's schema revision, per table the row
  count and the SHA-256 of its file, and the snapshots' event hashes) and one JSON file per table. Tables: the pilot's
  own (0010: document, document_parse, search_log, extraction_output, candidates, links, mappings, state events,
  snapshots, annotation, review, owner time, findings, corrections), the document invocations with their agent
  settings and model calls, and the sealed 'extracted (pilot)' versions' files.
- `load(engine, content)`: refused unless every pilot table is empty and the manifest's hashes match. In one
  transaction, rows are replayed in their original creation order, so every database rule is checked again as it was
  the first time (S0 holds exactly its output's events; no event before S0; a mapping from a reconciler on the same
  document; a correction on a value of an output with its S0). The pilot tables keep their ids (so every snapshot's
  event ids and hash are unchanged); the shared tables (agent_setting, agent_invocation, model_call) get the live
  database's ids, and the pilot rows that name them are rewritten. A model call is replayed as Sprint 1 records one:
  inserted as started, then finished, so its times are the load's; the original times are in the bundle. The pilot
  source's versions are registered again from their files (the same digest and fingerprint). After the load, every
  snapshot's events hash is recomputed and compared with the manifest; any difference rolls the load back.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.retry import run_transaction

FORMAT = "hypocurate-pilot-bundle-1"
# The pilot's own tables, in the order a row may depend on another (for ties in time), with their time column.
PILOT_TABLES = (("document", "fetched_at"), ("search_log", "at"), ("document_parse", "created_at"),
                ("extraction_output", "created_at"), ("candidate_observation", "created_at"),
                ("candidate_value", "created_at"), ("extraction_link", "created_at"),
                ("reconciler_mapping", "created_at"), ("evidence_state_event", "at"), ("evidence_snapshot", "taken_at"),
                ("annotation_file", "loaded_at"), ("annotation_row", None), ("review_file", "loaded_at"),
                ("owner_time_log", "at"), ("auditor_finding", "at"), ("value_correction", "at"))
# Columns a trigger sets from the database's clock: never inserted.
CLOCK = {"fetched_at", "at", "created_at", "taken_at", "loaded_at", "started_at", "finished_at"}


class BundleRefused(ValueError):
    pass


def _json(v):
    if isinstance(v, (bytes, memoryview)):
        return {"$bytes": base64.b64encode(bytes(v)).decode()}
    if isinstance(v, Decimal):
        return {"$decimal": str(v)}
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _unjson(v):
    if isinstance(v, dict) and set(v) == {"$bytes"}:
        return base64.b64decode(v["$bytes"])
    if isinstance(v, dict) and set(v) == {"$decimal"}:
        return Decimal(v["$decimal"])
    return v


def _rows(conn: Connection, sql: str, **params) -> list[dict]:
    return [{k: _json(v) for k, v in r._mapping.items()} for r in conn.execute(text(sql), params).all()]


def export(engine: Engine) -> bytes:
    from hypocurate.sources.pilot import KEY
    with engine.connect() as conn:
        tables = {t: _rows(conn, f"SELECT * FROM {t} ORDER BY id" if t != "annotation_row" else
                           "SELECT * FROM annotation_row ORDER BY id") for t, _ in PILOT_TABLES}
        tables["document_invocation"] = _rows(conn, "SELECT * FROM document_invocation ORDER BY invocation_id")
        inv_ids = [r["invocation_id"] for r in tables["document_invocation"]]
        tables["agent_invocation"] = _rows(conn, "SELECT * FROM agent_invocation WHERE id = ANY(:i) ORDER BY id",
                                           i=inv_ids)
        tables["agent_setting"] = _rows(conn, "SELECT * FROM agent_setting WHERE id IN (SELECT agent_setting_id FROM "
                                              "agent_invocation WHERE id = ANY(:i)) ORDER BY id", i=inv_ids)
        tables["model_call"] = _rows(conn, "SELECT * FROM model_call WHERE invocation_id = ANY(:i) ORDER BY id",
                                     i=inv_ids)
        tables["pilot_source_file"] = _rows(conn, (
            "SELECT v.id AS version_id, v.label, v.obtained_on, f.path, f.content FROM source_version v "
            "JOIN source s ON s.id = v.source_id JOIN source_file f ON f.source_version_id = v.id "
            "WHERE s.key = :k AND v.sealed_at IS NOT NULL ORDER BY v.id, f.path"), k=KEY)
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        snapshots = {str(r.id): r.events_sha256 for r in conn.execute(text("SELECT id, events_sha256 FROM "
                                                                           "evidence_snapshot")).all()}
    files = {f"{t}.json": json.dumps(rows, sort_keys=True, ensure_ascii=False).encode() for t, rows in tables.items()}
    manifest = {"format": FORMAT, "schema_revision": revision, "snapshots": snapshots,
                "tables": {name.removesuffix(".json"): {"rows": len(json.loads(b)), "sha256": hashlib.sha256(b).hexdigest()}
                           for name, b in files.items()}}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=1, sort_keys=True))
        for name, b in sorted(files.items()):
            z.writestr(name, b)
    return buf.getvalue()


def _read(content: bytes) -> tuple[dict, dict]:
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("format") != FORMAT:
            raise BundleRefused(f"not a {FORMAT} bundle")
        tables = {}
        for t, meta in manifest["tables"].items():
            b = z.read(f"{t}.json")
            if hashlib.sha256(b).hexdigest() != meta["sha256"]:
                raise BundleRefused(f"{t}.json does not match the manifest's hash")
            tables[t] = [{k: _unjson(v) for k, v in r.items()} for r in json.loads(b)]
    return manifest, tables


def _insert(conn: Connection, table: str, row: dict, keep_id: bool = True) -> int | None:
    cols = [c for c in row if c not in CLOCK and (keep_id or c != "id")]
    jsonb = {c for c, t in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE "
                                             "table_name = :t"), dict(t=table)).all() if t == "jsonb"}
    values = ", ".join(f"CAST(:{c} AS jsonb)" if c in jsonb else f":{c}" for c in cols)
    params = {c: (json.dumps(row[c]) if c in jsonb and row[c] is not None else row[c]) for c in cols}
    returning = " RETURNING id" if "id" in row else ""
    r = conn.execute(text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({values}){returning}"), params)
    return r.scalar_one() if returning else None


def load(engine: Engine, content: bytes, by: str) -> dict:
    manifest, tables = _read(content)
    from hypocurate.sources.pilot import DEFINITION
    from hypocurate.sources.versions import _register_in

    def run(conn: Connection) -> dict:
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != manifest["schema_revision"]:
            raise BundleRefused(f"the database is at schema {revision}, the bundle at {manifest['schema_revision']}")
        for t, _ in PILOT_TABLES:
            if conn.execute(text(f"SELECT EXISTS (SELECT 1 FROM {t})")).scalar():
                raise BundleRefused(f"{t} is not empty: a bundle is loaded once, into empty pilot tables")
        settings, invocations = {}, {}
        for s in tables["agent_setting"]:
            same = conn.execute(text("SELECT id, instruction, model FROM agent_setting WHERE role = :r AND version = :v"),
                                dict(r=s["role"], v=s["version"])).one_or_none()
            if same is not None and (same.instruction, same.model) != (s["instruction"], s["model"]):
                raise BundleRefused(f"agent setting {s['role']} v{s['version']} differs in the database")
            settings[s["id"]] = same.id if same is not None else _insert(conn, "agent_setting", s, keep_id=False)
        calls_of: dict = {}
        for m in tables["model_call"]:
            calls_of.setdefault(m["invocation_id"], []).append(m)
        doc_inv = {d["invocation_id"]: d for d in tables["document_invocation"]}
        # Every row with its time and rank; a document invocation (with its calls) goes just before the first pilot
        # row that names it.
        events = []
        file_time = {f["id"]: f["loaded_at"] for f in tables["annotation_file"]}
        for rank, (t, clock) in enumerate(PILOT_TABLES):
            for r in tables[t]:
                when = r.get(clock) if clock else file_time[r["annotation_file_id"]]  # a row: its file's time
                events.append((when, rank, r.get("id") or 0, t, r))
        events.sort(key=lambda e: (e[0], e[1], e[2]))
        invs = {i["id"]: i for i in tables["agent_invocation"]}

        def ensure_invocation(old: int | None) -> int | None:
            if old is None or old in invocations:
                return invocations.get(old)
            i = dict(invs[old])
            i["agent_setting_id"] = settings[i["agent_setting_id"]]
            new = _insert(conn, "agent_invocation", i, keep_id=False)
            invocations[old] = new
            d = dict(doc_inv[old])
            d["invocation_id"] = new
            _insert(conn, "document_invocation", d)
            for m in calls_of.get(old, []):
                start = {k: v for k, v in m.items() if k not in ("status", "input_tokens", "output_tokens",
                                                                   "cached_tokens", "cost", "error")}
                start["invocation_id"], start["status"] = new, "started"
                mid = _insert(conn, "model_call", start, keep_id=False)
                if m["status"] != "started":
                    conn.execute(text("UPDATE model_call SET status = :s, input_tokens = :i, output_tokens = :o, "
                                      "cached_tokens = :c, cost = :cost, error = :e, finished_at = now() WHERE id = :id"),
                                 dict(s=m["status"], i=m["input_tokens"], o=m["output_tokens"], c=m["cached_tokens"],
                                      cost=m["cost"], e=m["error"], id=mid))
            return new
        parse_invocations = {}
        for d in tables["document_invocation"]:
            parse_invocations.setdefault(d["document_parse_id"], []).append(d["invocation_id"])
        for _, _, _, t, r in events:
            row = dict(r)
            if t == "extraction_output" or t == "reconciler_mapping":
                # the invocations of this parse that started before this row (the extraction's or the reconciler's)
                row["invocation_id"] = ensure_invocation(row.get("invocation_id"))
            _insert(conn, t, row)
        for old in invs:  # invocations no pilot row names (e.g. a call that failed before any output)
            ensure_invocation(old)
        for t, _ in PILOT_TABLES:
            if t != "annotation_row" and tables[t]:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), (SELECT max(id) FROM {t}))"))
            elif t == "annotation_row" and tables[t] and "id" in tables[t][0]:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('annotation_row', 'id'), "
                                  "(SELECT max(id) FROM annotation_row))"))
        versions = {}
        for f in tables["pilot_source_file"]:
            versions.setdefault((f["version_id"], f["label"], f["obtained_on"]), {})[f["path"]] = f["content"]
        sealed = []
        for (vid, label, obtained), files in sorted(versions.items()):
            done = _register_in(conn, DEFINITION, files, date.fromisoformat(str(obtained)[:10]), label)
            sealed.append(done.fingerprint)
        for sid, sha in manifest["snapshots"].items():
            ids = conn.execute(text("SELECT event_ids FROM evidence_snapshot WHERE id = :s"), dict(s=int(sid))).scalar()
            if hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest() != sha:
                raise BundleRefused(f"snapshot {sid}'s events hash differs after the load")
        return {"tables": {t: len(rows) for t, rows in tables.items()}, "invocations": len(invocations),
                "pilot_versions": sealed, "snapshots_checked": len(manifest["snapshots"]), "loaded_by": by}
    return run_transaction(engine, run)
