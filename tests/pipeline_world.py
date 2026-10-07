"""Step 6 test helper: runs on the real frozen sources, through the real lifecycle.

`registered(engine)` registers the three sources from their frozen files (step 4 code).
`dispatched_run(...)` creates a query with the chosen sources, submits, confirms and dispatches
it, and starts the run (a run_source row for every registered source, as dispatch writes them).
`through_freeze(...)` locks the plan, stores the records, raises the flags, decides and freezes
(step 6 code), and returns the run's id.
"""
from __future__ import annotations

import json

from sqlalchemy import text

from hypocurate.pipeline import checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources.versions import register

SOURCE_KEYS = ("mpea", "tamu_fcc", "controlled_duplicates")


def registered(engine, keys=SOURCE_KEYS) -> dict[str, int]:
    return {k: register(engine, k).version_id for k in keys}


def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
    """Registers each source key with one sealed version holding the given file (MPEA layout for
    'mpea' and 'controlled_duplicates'), with the settings of the code's source definition. Step 8a:
    a Texas A&M version also holds the frozen curation (the owner's accepted values: test type
    tension, phase class FCC), as the real source does, since adapter version 3 no longer assigns them.
    Step 8a review (finding 1): a curation file must belong to the version it is in, so the version
    also holds the frozen documentation the quotes come from, and the file names this version's own
    base fingerprint (the frozen file's entries otherwise unchanged)."""
    from hypocurate.sources.versions import DATA_DIR, SOURCES, file_role, files_digest, version_identity
    out = {}
    for key, content in files.items():
        d = SOURCES[key]
        name = d.data_files[0]
        with engine.begin() as conn:
            sid = conn.execute(text(
                "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
                "VALUES (:k, :n, :t, :l, :d, 'available', true, :u) RETURNING id"),
                dict(k=key, n=d.name, t=d.source_type, l=d.licence, d=d.data_kind, u=d.grouping_unit)).scalar()
            vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) "
                                    "VALUES (:s, 'test file', '2026-10-06') RETURNING id"), dict(s=sid)).scalar()
            import hashlib
            stored = {name: content}
            if d.curation_file:
                import json
                for doc in d.documentation_files:
                    stored[doc] = (DATA_DIR / d.directory / doc).read_bytes()
                curation = json.loads((DATA_DIR / d.directory / d.curation_file).read_text(encoding="utf-8"))
                curation["base_version"] = {"label": "test file", "fingerprint": version_identity(
                    files_digest(stored), d.source_type, d.data_kind, d.grouping_unit)}
                stored[d.curation_file] = (json.dumps(curation, indent=2, sort_keys=True, ensure_ascii=False)
                                           + "\n").encode("utf-8")
            for path, data in stored.items():
                conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content, role) "
                                  "VALUES (:v, :p, :h, :c, :r)"),
                             dict(v=vid, p=path, h=hashlib.sha256(data).hexdigest(), c=data, r=file_role(path)))
            digest = files_digest(stored)
            conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v"),
                         dict(v=vid, fp=version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)))
        out[key] = vid
    return out


def mpea_csv(rows: list[dict]) -> bytes:
    """An MPEA-layout file: the frozen header, then rows given as {column: value} (others blank)."""
    import csv, io
    from hypocurate.sources.adapters.mpea_layout import HEADER
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(HEADER)
    for r in rows:
        w.writerow([r.get(h, "") for h in HEADER])
    return out.getvalue().encode("utf-8")


def mpea_row(formula, gs, ys, doi="10.1016/j.test.2026.001", test="T", temperature="25.0"):
    return {"FORMULA": formula, "PROPERTY: Microstructure": "FCC", "PROPERTY: BCC/FCC/other": "FCC",
            "PROPERTY: grain size ($\\mu$m)": str(gs), "PROPERTY: Type of test": test,
            "PROPERTY: Test temperature ($^\\circ$C)": temperature, "PROPERTY: YS (MPa)": str(ys),
            "PROPERTY: UTS (MPa)": str(ys * 2), "REFERENCE: doi": doi}


def tamu_xlsx(rows: list[dict]) -> bytes:
    """A Texas A&M-layout workbook: the frozen sheet name and header, then rows given as
    {column: value} (element columns default to 0)."""
    import io
    import openpyxl
    from hypocurate.sources.adapters.tamu_fcc import ELEMENT_COLUMNS, HEADER, SHEET
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append(list(HEADER))
    for r in rows:
        ws.append([r.get(h, 0.0 if h in ELEMENT_COLUMNS else None) for h in HEADER])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _val(engine, sql, **params):
    with engine.begin() as conn:
        result = conn.execute(text(sql), params)
        return result.scalar() if result.returns_rows else None


def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
    """A running run of the reference claim that chose `sources`."""
    with engine.connect() as conn:
        registry = dict(conn.execute(text(
            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
        domain = conn.execute(text("SELECT id FROM domain WHERE key = 'grain_size_strengthening'")).scalar_one()
    h = _val(engine, "INSERT INTO hypothesis DEFAULT VALUES RETURNING id")
    vid = _val(engine, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) VALUES "
                       "(:h, 1, 'In FCC multi-principal-element alloys, yield strength rises as grain size falls', "
                       ":d) RETURNING id", h=h, d=domain)
    for key in sources:
        _val(engine, "INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=ids[key])
    _val(engine, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)
    _val(engine, "UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
         v=vid, d=domain)
    _val(engine, "UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)
    return run_of_version(engine, vid, sources, marked)


def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False) -> int:
    """Another running run of an already dispatched hypothesis version."""
    with engine.connect() as conn:
        registry = dict(conn.execute(text(
            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
    flags = json.dumps({"constructed_test_data": True} if marked else {})
    rid = _val(engine, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                       "VALUES (:v, true, CAST(:f AS jsonb)) RETURNING id", v=vid, f=flags)
    for key, version in registry.items():
        if key in sources:
            _val(engine, "INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                         "VALUES (:r, :s, :sv, 'pending')", r=rid, s=ids[key], sv=version)
        else:
            _val(engine, "INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
                 r=rid, s=ids[key])
    _val(engine, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)
    return rid


def version_of(engine, run_id) -> int:
    return _val(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=run_id)


def locked_run(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = dispatched_run(engine, sources, marked)
    checkpoints.lock_rules(engine, rid, plan or reference_plan(version_of(engine, rid)))
    return rid


def through_freeze(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = locked_run(engine, sources, marked, plan)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid
