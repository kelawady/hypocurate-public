"""Builds rows through the real lifecycle, in plain SQL, one transaction per step,
so the step 3 tests exercise the database rules exactly as later code will meet them."""
from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

FP = "0" * 64  # a well-formed fingerprint
# How a test record was extracted (record.extraction, required from migration 0003, step 6).
EXTRACTION = '{"method": "adapter", "name": "test", "version": "1"}'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_digest(files: dict[str, bytes]) -> str:
    """A source version's files digest (owner, 2026-10-05): SHA-256 of one line
    "<sha256>  <path>\\n" per file, sorted by path (the sha256sum format)."""
    listing = "".join(f"{sha(files[path])}  {path}\n" for path in sorted(files))
    return sha(listing.encode())


def version_fingerprint(files: dict[str, bytes], source_type: str, data_kind: str, grouping_unit: str) -> str:
    """A source version's identity (re-check item 2): the files digest plus the
    interpretation settings, one "<name> <value>\\n" line each."""
    text = (f"files {files_digest(files)}\nsource_type {source_type}\n"
            f"data_kind {data_kind}\ngrouping_unit {grouping_unit}\n")
    return sha(text.encode())


class World:
    def __init__(self, engine):
        self.e = engine
        self.domain = {k: v for k, v in self.rows("SELECT key, id FROM domain")}
        self.source = {}
        self.version = {}
        for key, unit in (("mpea", "paper"), ("tamu_fcc", "dataset")):
            self.add_source(key, grouping_unit=unit)

    def add_source(self, key, data_kind="measured", source_type="uploaded_table", grouping_unit="paper"):
        """Registers a source with one sealed version holding one data file."""
        self.source[key] = self.val(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES (:k, :k, :t, 'test', :d, 'available', true, :u) RETURNING id",
            k=key, t=source_type, d=data_kind, u=grouping_unit)
        self.version[key] = self.new_version(key)
        self.add_file(self.version[key], f"{key}.csv", f"{key},data\n".encode())
        self.seal(self.version[key])
        return self.source[key]

    def new_version(self, key, label="v1"):
        return self.val("INSERT INTO source_version (source_id, label, obtained_on) "
                        "VALUES (:s, :l, '2026-10-04') RETURNING id", s=self.source[key], l=label)

    def add_file(self, version, path, content):
        self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)",
                     v=version, p=path, h=sha(content), c=content)

    def files(self, version):
        return {p: bytes(c) for p, c in self.rows(
            "SELECT path, content FROM source_file WHERE source_version_id = :v", v=version)}

    def settings(self, version):
        return self.rows("SELECT source_type, data_kind, grouping_unit FROM source_version WHERE id = :v",
                         v=version)[0]

    def fingerprint(self, version, files=None):
        return version_fingerprint(files if files is not None else self.files(version), *self.settings(version))

    def seal(self, version, fingerprint=None):
        fingerprint = fingerprint or self.fingerprint(version)
        self.run_sql("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                     v=version, fp=fingerprint)

    # --- plumbing ---------------------------------------------------------------------
    def run_sql(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params)

    def val(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params).scalar()

    def rows(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params).all()

    def rejected(self, sql, match, **params):
        """The statement is refused by the database with a message matching `match`."""
        with pytest.raises(IntegrityError, match=match):
            self.run_sql(sql, **params)

    # --- queries ----------------------------------------------------------------------
    def hypothesis(self, narrower_of=None):
        return self.val("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id", r=narrower_of)

    def draft(self, hypothesis=None, number=1, domain="grain_size_strengthening", sources=("mpea", "tamu_fcc")):
        hypothesis = hypothesis or self.hypothesis()
        vid = self.val(
            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
            "VALUES (:h, :n, 'Yield strength rises as grain size falls', :d) RETURNING id",
            h=hypothesis, n=number, d=self.domain[domain])
        for s in sources:
            self.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=self.source[s])
        return vid

    def submit(self, vid):
        self.run_sql("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)

    def confirm(self, vid, domain="grain_size_strengthening"):
        self.run_sql("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() "
                     "WHERE id = :v", v=vid, d=self.domain[domain])

    def dispatch_version(self, vid):
        self.run_sql("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)

    def dispatched(self, **kw):
        vid = self.draft(**kw)
        self.submit(vid)
        self.confirm(vid, kw.get("domain", "grain_size_strengthening"))
        self.dispatch_version(vid)
        return vid

    # --- runs -------------------------------------------------------------------------
    def run(self, vid=None, sources=("mpea", "tamu_fcc")):
        """Dispatch: a queued run with a run_source row for every registered source."""
        vid = vid or self.dispatched()
        rid = self.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
        for key in self.source:
            if key in sources:
                self.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                             "VALUES (:r, :s, :sv, 'pending')", r=rid, s=self.source[key], sv=self.version[key])
            else:
                self.run_sql("INSERT INTO run_source (run_id, source_id, search_status) "
                             "VALUES (:r, :s, 'not_selected')", r=rid, s=self.source[key])
        return rid

    def start(self, rid):
        self.run_sql("UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)

    def running(self, **kw):
        rid = self.run(**kw)
        self.start(rid)
        return rid

    def locked(self, **kw):
        """A running run whose rules are locked: records may now be extracted."""
        rid = self.running(**kw)
        self.lock(rid)
        return rid

    def lock(self, rid, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1), tags=()):
        """The rules lock, in one transaction with its tags."""
        with self.e.begin() as conn:
            pid = conn.execute(text(
                "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
                "min_groups, min_resid_df, sensitivity_analysis_keys) "
                "VALUES (:r, '{}', :fp, :o, :a, :b, :c, :d, :k) RETURNING id"),
                dict(r=rid, fp=FP, o=option, a=mins[0], b=mins[1], c=mins[2], d=mins[3], k=list(keys))).scalar()
            for tag in tags:
                conn.execute(text("INSERT INTO run_tag VALUES (:r, :t)"), dict(r=rid, t=tag))
        return pid

    def search(self, rid, source="mpea", status="searched", nothing_found=None, reason=None):
        self.run_sql("UPDATE run_source SET search_status = :st, nothing_found = :nf, failure_reason = :fr, "
                     "decided_at = now() WHERE run_id = :r AND source_id = :s",
                     st=status, nf=nothing_found, fr=reason, r=rid, s=self.source[source])

    def record(self, rid, source="mpea", key="row-1", kind=None, index=0):
        kind = kind or self.val("SELECT data_kind FROM source_version WHERE id = :v", v=self.version[source])
        return self.val(
            "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, "
            "alloy, harmonized, reported, extraction) VALUES (:r, :sv, :k, :i, :kind, 'CoCrNi', '{}', '{}', "
            "CAST(:x AS jsonb)) RETURNING id",
            r=rid, sv=self.version[source], k=key, i=index, kind=kind, x=EXTRACTION)

    def decide(self, rid, rec, eligible=True, rule="in_scope"):
        self.run_sql("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)",
                     r=rid, c=rec, e=eligible, u=rule)

    def analysis_set(self, rid, key="primary"):
        return self.val("INSERT INTO analysis_set (run_id, key) VALUES (:r, :k) RETURNING id", r=rid, k=key)

    def add(self, set_id, rec):
        self.run_sql("INSERT INTO analysis_set_record VALUES (:s, :c)", s=set_id, c=rec)

    def freeze(self, rid, n):
        self.run_sql("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)",
                     r=rid, fp=FP, n=n)

    def frozen(self, n=4, per_source=None, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1)):
        """A running run, locked and frozen, with n eligible records in its primary set.
        per_source: {"mpea": 3, "tamu_fcc": 1}; default: all from MPEA."""
        per_source = per_source or {"mpea": n}
        rid = self.running()
        self.lock(rid, option=option, keys=keys, mins=mins)
        primary = self.analysis_set(rid)
        recs = []
        for source, count in per_source.items():
            self.search(rid, source)
            for i in range(count):
                rec = self.record(rid, source=source, key=f"{source}-{i}")
                self.decide(rid, rec)
                self.add(primary, rec)
                recs.append(rec)
        sets = {"primary": primary}
        for k in keys:
            sets[k] = self.analysis_set(rid, k)
        self.freeze(rid, sum(per_source.values()))
        return rid, sets, recs

    def result(self, rid, set_id, scope="pooled", n=4, alloys=1, groups=2, source=None, minimums_met=None,
               mins=(4, 1, 2, 1)):
        """An analysis result whose fields follow the validity-check definitions."""
        resid = n - alloys - 1
        check1 = alloys >= 1
        check2 = check1 and resid >= 1 and groups >= 2
        if minimums_met is None:
            minimums_met = n >= mins[0] and alloys >= mins[1] and groups >= mins[2] and resid >= mins[3]
        return self.val(
            "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, "
            "resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
            "VALUES (:r, :sc, :s, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
            r=rid, sc=scope, s=set_id, src=self.source[source] if source else None, n=n, a=alloys, g=groups,
            df=resid, c1=check1, c2=check2, mm=minimums_met, est=428.0 if check1 else None,
            se=64.0 if check2 else None, p=1e-6 if check2 else None)

    def complete(self, rid, outcome, verdict=None, exploratory=False):
        self.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
                     "exploratory = :x WHERE id = :r", o=outcome, v=verdict, x=exploratory, r=rid)

    def fail(self, rid, reason="worker stopped"):
        self.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r",
                     f=reason, r=rid)

    def stage(self, rid, stage="planner", role="planner", attempt=1):
        return self.val("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :o, :a) RETURNING id",
                        r=rid, s=stage, o=role, a=attempt)

    def call(self, rid, stage_id, max_cost=0.5, role="planner"):
        return self.val(
            "INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
            "VALUES (:r, :s, :o, 'model-a', 'prices-2026-10', :m) RETURNING id",
            r=rid, s=stage_id, o=role, m=max_cost)

    def finish_call(self, call_id, status="succeeded", usage=(1000, 200, 0, 0.01)):
        i, o, c, cost = usage if usage else (None, None, None, None)
        self.run_sql("UPDATE model_call SET status = :st, input_tokens = :i, output_tokens = :o, "
                     "cached_tokens = :c, cost = :cost, finished_at = now() WHERE id = :id",
                     st=status, i=i, o=o, c=c, cost=cost, id=call_id)
