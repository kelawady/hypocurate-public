# Build step 3 — second fix packet (re-check items only)

Date: 2026-10-05. Branch: `step-03-data-model`. The re-check (`docs/reviews/step03_recheck_chatgpt.md`) closed findings 2, 5 and 6 and left four items. This packet covers **only those four**. Each was fixed in migration 0001 in place, because 0001 has never run on the live database (owner's instruction); it is frozen after the merge. One commit per item. GitHub Actions on the last code commit `f3e8f71`: success, 375 passed, https://github.com/kelawady/hypocurate/actions/runs/37251807075.

Generated from the repository by a script. Each item shows that commit's change to code, tests and README as a unified diff with 12 lines of context. The updated `docs/reviews/step03_summary.md` (re-check section, corrected locking section, test changes) is in the repository and is not repeated here.

## How to use this packet

Please check that each item is closed, and that nothing else changed. Your review is advice; the test suite is the gate.

| Item | Commit | Where |
|---|---|---|
| 1. Lock order | `bd6f39a` | `hc_write_lock` in `0001_data_model.py`; the protocol text in the migration, `models.py`, README; `tests/test_concurrency.py` (interleaving tests); `test_write_lock_locks_a_run_or_a_version` |
| 2. Source fingerprints | `c09176e` | `source_version.files_digest`, `hc_files_digest`, `hc_version_identity`, `hc_source_version_update`; the path CHECK; `tests/model_builder.py`; path, revision and sealing tests |
| 3. Finite costs | `1ea2850` | CHECK `ck_model_call_money_finite`; `test_max_cost_must_be_finite`, `test_reported_cost_must_be_finite` |
| 4. Stage role | `f3e8f71` | `hc_stage_result_update`; `test_a_commentator_stage_cannot_be_relabelled`, `test_a_running_stage_cannot_be_relabelled` |

Two tests from the earlier rounds were adjusted in item 2, with unchanged intent:
- the `.zip` case now names the stricter path constraint;
- the sealing test expects the new identity message and also checks the stored digest.

The two sealing races compute the fingerprint with the new identity.

## 1. Lock order: `hc_write_lock` and the protocol (`bd6f39a`)

Adds `hc_write_lock(p_run, p_version)` (version, then run) as the protocol's entry point for application code, and states the protocol and the retry rule in the migration, `models.py` and the README. The claim is corrected: the lock order holds for paths that follow the protocol, not by the child-row triggers alone. Tests: the review's interleaving without the protocol (exactly one transaction aborted, 40P01) and with it (no error), for a stage result and a model call; the helper's own checks.

```diff
diff --git a/README.md b/README.md
index a1d5985..2ce0df7 100644
--- a/README.md
+++ b/README.md
@@ -83,25 +83,31 @@ python -m hypocurate.db.migrate current              # the database's revision
 python -m hypocurate.db.migrate downgrade <revision> # drops tables and their data
 ```
 
 - **On deploy.** Both Render services run `python -m hypocurate.db.migrate upgrade` as their pre-deploy command. It runs after the image is built and before the new version starts. An advisory lock makes the second service wait, after which it finds the schema at the latest revision. `/health` shows the database's revision and whether it is the latest. Locally, `docker compose up` runs the same command in a one-off `migrate` service before web and worker start.
 - **If a migration fails.** The whole upgrade is one transaction, so PostgreSQL undoes all of it: no table and no revision change. The command exits non-zero, Render fails the deploy, and the previous version keeps running. Every migration must therefore stay inside that transaction (no `CREATE INDEX CONCURRENTLY`, no `autocommit_block`); a test checks this.
 - **Every migration keeps working with the previous release's code** (add first, remove in a later release). Reverting a merge on `main` then deploys the old code safely on the newer schema.
 - **Rolling back:**
   1. Preferred: a new migration that undoes the change, deployed the normal way.
   2. Code only: revert the merge on `main`.
   3. Schema: the owner runs `python -m hypocurate.db.migrate downgrade <revision> --confirm-data-loss` in the Render Shell of a service. **This drops tables and their data**; in production it refuses without the flag. Before it, check the backups: Render's point-in-time recovery reaches back 3 days on the Hobby workspace and restores into a *new* database, which costs money.
 - **What the database enforces, and its limits.**
   - Triggers and CHECK constraints refuse, among others: editing a locked plan; changing a frozen dataset; freezing a primary set that leaves out an eligible record; updating or deleting a record; extracting before the rules lock; any curation once a run has ended; adding files to a sealed source version; and a verdict on a run that is not sufficient. A refusal raises an error starting `hypocurate:`.
-  - **Locking.** Every trigger that checks or changes a run's state first locks that run's row; triggers on chosen sources and on dispatch lock the hypothesis version first (lock order: version, then run). A transaction that writes to a run therefore makes every other writer to that run wait until it commits, so long transactions on a run should be avoided.
+  - **Locking protocol (all write paths, from step 4 on).** The lock order is version, then run, then the run's child rows.
+    - Every transaction that will write to a run or its child rows first calls `SELECT hc_write_lock(p_run => <run id>)`.
+    - Every transaction that will change a hypothesis version's chosen sources, submit it or dispatch it first calls `SELECT hc_write_lock(p_version => <version id>)`.
+    - Paths that follow the protocol cannot deadlock with each other.
+    - The triggers also lock the run (or version) before checking its state, which makes the checks race-free. They do not by themselves establish the lock order: an UPDATE of a child row locks that row before its trigger asks for the run lock. A path that skips the protocol can deadlock.
+    - **On a reported deadlock (SQLSTATE `40P01`) or serialization failure (`40001`), retry the whole transaction.** PostgreSQL aborts one transaction and writes nothing from it.
+    - A transaction holding a run's lock makes every other writer to that run wait, so keep such transactions short.
   - **After a run ends.** On a completed run only the commentary, the Commentator's stage and model calls, and artifacts may still be written; on a failed run only the audit log.
   - **Validity checks.** The CHECKs on `analysis_result` are necessary conditions on the stored counts, not the full validity rules of PRD 5.7. Those, and the agreement of the verdict with the pooled result, are computed and tested in step 7.
   - The triggers stop the application and ordinary edits. The database owner can still drop a trigger, so they are not tamper-proof; the fingerprints are the cross-check.
 - **Tests never touch the database at `DATABASE_URL`.** They create scratch databases (`hypocurate_t_…`, from a template migrated once per session) and drop them afterwards. The database user must be allowed to create databases (the local and CI containers' user is).
 
 ## Data
 
 | Path | What it is |
 |---|---|
 | `data/manifest.json` | Fingerprint (SHA-256), size, licence, origin and retrieval date of every frozen file |
 | `data/sources/mpea/` | MPEA dataset (Borg et al. 2020), Apache-2.0 |
 | `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT |
diff --git a/hypocurate/db/migrations/versions/0001_data_model.py b/hypocurate/db/migrations/versions/0001_data_model.py
index 9e8bc7c..f31e4ac 100644
--- a/hypocurate/db/migrations/versions/0001_data_model.py
+++ b/hypocurate/db/migrations/versions/0001_data_model.py
@@ -553,51 +553,59 @@ def downgrade() -> None:
     op.drop_table('hypothesis')
     op.drop_table('domain')
     op.drop_table('agent_setting')
     op.execute("DROP SEQUENCE hypothesis_number_seq")
     for function in reversed(FUNCTION_NAMES):
         op.execute(f"DROP FUNCTION {function}")
 
 
 # ---------------------------------------------------------------------------
 # Hand-written: trigger functions, triggers, views, seed rows.
 # No '%' anywhere: messages are built with ||.
 #
-# Locking protocol (review finding 1). Every trigger that checks or changes a run's
-# state first locks that run's row with hc_lock_run (SELECT ... FOR NO KEY UPDATE),
-# and reads the run's status from that same statement, so it sees the latest
-# committed state. Updates of the run row itself take the same lock. Triggers on
-# chosen sources and on dispatch lock the hypothesis version first (hc_lock_version);
-# submission and dispatch are updates of that row. Lock order: version, then run.
-# A transaction that holds a run's lock makes every other writer to that run wait.
+# Locking protocol (review finding 1; re-check item 1). The lock order is version,
+# then run, then the run's child rows. Two parts:
+#  - The protocol, for application code: every transaction that will write to a run
+#    or its child rows first calls hc_write_lock(p_run => ...); every transaction that
+#    will change a hypothesis version's chosen sources, submit it or dispatch it first
+#    calls hc_write_lock(p_version => ...). Paths that follow it acquire locks in the
+#    order above, so they cannot deadlock with each other.
+#  - The triggers: every trigger that checks or changes a run's state locks the run
+#    (hc_lock_run) and reads its status in the same statement; chosen-source and
+#    dispatch triggers lock the version (hc_lock_version). This makes the checks
+#    race-free. It does NOT by itself establish the lock order: an UPDATE of a child
+#    row locks that row before its trigger asks for the run lock. A path that skips
+#    the protocol can therefore deadlock; PostgreSQL then aborts one transaction
+#    (SQLSTATE 40P01), and callers must retry the whole transaction.
 #
 # What may be written to a run in each state (review finding 3; owner, 2026-10-05):
 #   queued:    run_source and run_agent_setting (dispatch); the run becomes running.
 #   running:   everything of the pipeline, each in its checkpoint order:
 #              plan (+ tags) -> records -> eligibility -> sets -> freeze -> results.
 #   completed: only the commentary, the Commentator's stage and model calls, and
 #              artifacts. None of them can change the outcome, verdict, analysis
 #              results or record sets, which are all final.
 #   failed:    nothing (audit_log is written in every state).
 # A run can complete or fail only when none of its stages is running and none of its
 # model calls is still started.
 # ---------------------------------------------------------------------------
 
 FUNCTION_NAMES = [
     "hc_reject(text)",
     "hc_append_only()",
     "hc_no_delete()",
     "hc_is_frozen(bigint)",
     "hc_lock_run(bigint)",
     "hc_lock_version(bigint)",
+    "hc_write_lock(bigint, bigint)",
     "hc_files_fingerprint(bigint)",
     "hc_original_domain(bigint)",
     "hc_hypothesis_insert()",
     "hc_version_insert()",
     "hc_version_update()",
     "hc_version_source_change()",
     "hc_run_insert()",
     "hc_run_update()",
     "hc_plan_insert()",
     "hc_run_tag_insert()",
     "hc_tag_value_update()",
     "hc_source_update()",
@@ -660,24 +668,54 @@ FUNCTIONS = [
         SELECT status INTO s FROM run WHERE id = p_run FOR NO KEY UPDATE;
         RETURN s;
     END $$
     """,
     """
     CREATE FUNCTION hc_lock_version(p_version bigint) RETURNS text LANGUAGE plpgsql AS $$
     DECLARE s text;
     BEGIN
         SELECT status INTO s FROM hypothesis_version WHERE id = p_version FOR NO KEY UPDATE;
         RETURN s;
     END $$
     """,
+    # The protocol's entry point for application code (re-check item 1): call it first,
+    # before any write to the run's or the version's rows. Locks the version, then the
+    # run; returns the run's status (or the version's, when no run is given).
+    """
+    CREATE FUNCTION hc_write_lock(p_run bigint DEFAULT NULL, p_version bigint DEFAULT NULL)
+    RETURNS text LANGUAGE plpgsql AS $$
+    DECLARE s text;
+    BEGIN
+        IF p_run IS NULL AND p_version IS NULL THEN
+            PERFORM hc_reject('hc_write_lock needs a run or a hypothesis version');
+        END IF;
+        IF p_version IS NOT NULL THEN
+            s := hc_lock_version(p_version);
+            IF s IS NULL THEN
+                PERFORM hc_reject('no hypothesis version ' || p_version);
+            END IF;
+        END IF;
+        IF p_run IS NOT NULL THEN
+            IF p_version IS NOT NULL AND p_version IS DISTINCT FROM
+               (SELECT hypothesis_version_id FROM run WHERE id = p_run) THEN
+                PERFORM hc_reject('run ' || p_run || ' does not belong to hypothesis version ' || p_version);
+            END IF;
+            s := hc_lock_run(p_run);
+            IF s IS NULL THEN
+                PERFORM hc_reject('no run ' || p_run);
+            END IF;
+        END IF;
+        RETURN s;
+    END $$
+    """,
     # A source version's fingerprint (owner, 2026-10-05): SHA-256 of its file list,
     # one line "<sha256>  <path>\\n" per file (the sha256sum format), sorted by path
     # bytewise. Step 4 computes the same in Python.
     """
     CREATE FUNCTION hc_files_fingerprint(p_version bigint) RETURNS text LANGUAGE sql STABLE AS $$
         SELECT encode(sha256(convert_to(
                    string_agg(sha256 || '  ' || path || chr(10), '' ORDER BY path COLLATE "C"), 'UTF8')), 'hex')
         FROM source_file WHERE source_version_id = p_version
     $$
     """,
     # The confirmed domain of the original question, for a narrower query; NULL otherwise.
     """
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 0658b5c..ee49fbd 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -6,27 +6,33 @@ a locked plan cannot change; a frozen dataset cannot change; records are never
 updated; stored is not analysed (`record` versus `run_record` and `analysis_set`);
 a narrower question is a separate query linked to the run it narrows; every
 model call has tokens and cost or counts at its upper bound.
 
 Limitation, stated plainly: the triggers stop the application and ordinary edits.
 The database owner can still drop a trigger; the fingerprints are the cross-check.
 
 No table stores token or cost totals; the views `model_call_totals_by_*` sum
 `model_call`. Search coverage and the kinds of "nothing found" are not stored per
 run either; the view `run_search_coverage` reports them per source, from the run's
 own dispatch-time `run_source` rows.
 
-Locking protocol (review finding 1): every trigger that checks or changes a run's
-state first locks that run's row (FOR NO KEY UPDATE); triggers on chosen sources and
-on dispatch lock the hypothesis version first. Lock order: version, then run.
+Locking protocol (review finding 1; re-check item 1). Lock order: version, then run,
+then the run's child rows. Application code calls `SELECT hc_write_lock(p_run => ...)`
+(or `p_version => ...` for chosen sources, submission and dispatch) first in every
+transaction that writes to them; such paths cannot deadlock with each other. The
+triggers lock the run (or version) before checking its state, which makes the checks
+race-free but does not by itself fix the lock order: an UPDATE of a child row locks
+that row before its trigger asks for the run lock. A path that skips the protocol may
+deadlock; PostgreSQL then aborts one transaction (SQLSTATE 40P01) and the caller must
+retry the whole transaction.
 
 What the CHECKs on `analysis_result` establish (review finding 5): necessary
 conditions on the stored counts only. The full validity rules of PRD 5.7 and the
 agreement of the verdict with the pooled result are computed and tested in step 7.
 """
 from __future__ import annotations
 
 from datetime import date, datetime
 from decimal import Decimal
 
 from sqlalchemy import (
     ARRAY,
diff --git a/tests/test_concurrency.py b/tests/test_concurrency.py
index 9a5deb9..4cfe02c 100644
--- a/tests/test_concurrency.py
+++ b/tests/test_concurrency.py
@@ -222,12 +222,116 @@ def test_file_first_then_sealing_includes_it(w):
                  dict(v=sv, h=sha(b"b"), c=b"b"), dict(v=sv, fp=both))
     assert error is None  # the seal waited, then fingerprinted both files
 
 
 def test_sealing_first_then_file_is_rejected(w):
     sv = w.new_version("mpea", "v2")
     w.add_file(sv, "a.csv", b"a")
     error = race(w.e, "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                  "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                  dict(v=sv, fp=files_fingerprint({"a.csv": b"a"})), dict(v=sv, h=sha(b"b"), c=b"b"))
     rejected(error, "sealed source version")
     assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=sv) == 1
+
+
+# --- the protocol against child-row deadlocks (re-check item 1) ----------------------------------------------
+# A holds the run lock; B updates a child row; A then updates the same child row.
+# The child UPDATE locks its row before its trigger asks for the run lock, so the
+# triggers alone cannot fix the lock order. The protocol does: every writer calls
+# hc_write_lock first.
+
+LOCK_RUN = "SELECT hc_write_lock(p_run => :r)"
+B_WRITES = "UPDATE stage_result SET output = '{\"by\": \"B\"}' WHERE id = :s"
+A_WRITES = "UPDATE stage_result SET output = '{\"by\": \"A\"}' WHERE id = :s"
+
+
+def interleave(engine, b_statements, params):
+    """A: lock the run. B (thread): run b_statements; it must end up waiting on a lock.
+    A: update the same child row, then commit. Returns (A's error, B's error)."""
+    outcome = {}
+
+    def run_b():
+        try:
+            with engine.begin() as b:
+                for sql in b_statements:
+                    b.execute(text(sql), params)
+            outcome["error"] = None
+        except Exception as error:
+            outcome["error"] = error
+
+    a_error = None
+    with engine.connect() as a:
+        tx = a.begin()
+        a.execute(text(LOCK_RUN), params)
+        thread = threading.Thread(target=run_b)
+        thread.start()
+        deadline = time.monotonic() + 10
+        while waiting_on_a_lock(engine) == 0 and time.monotonic() < deadline:
+            time.sleep(0.05)
+        assert waiting_on_a_lock(engine) == 1, "B should be waiting on A's lock"
+        try:
+            a.execute(text(A_WRITES), params)
+            tx.commit()
+        except Exception as error:
+            a_error = error
+            tx.rollback()
+    thread.join(30)
+    assert not thread.is_alive()
+    return a_error, outcome["error"]
+
+
+def deadlocked(error) -> bool:
+    return error is not None and "deadlock detected" in str(error)
+
+
+def test_skipping_the_protocol_can_deadlock(w):
+    """Without the protocol, B locks the child row and then waits for the run; A waits
+    for the child row. PostgreSQL detects the deadlock and aborts one of them
+    (SQLSTATE 40P01); the caller must retry. Nothing is half-written."""
+    rid = w.running()
+    st = w.stage(rid)
+    a_error, b_error = interleave(w.e, [B_WRITES], dict(r=rid, s=st))
+    assert deadlocked(a_error) != deadlocked(b_error), (a_error, b_error)  # exactly one was aborted
+    survivor = "B" if deadlocked(a_error) else "A"
+    assert w.val("SELECT output->>'by' FROM stage_result WHERE id = :s", s=st) == survivor
+
+
+def test_following_the_protocol_does_not_deadlock(w):
+    """With the protocol, B asks for the run lock before touching the child row, so it
+    waits without holding anything A needs. A writes and commits; then B writes."""
+    rid = w.running()
+    st = w.stage(rid)
+    a_error, b_error = interleave(w.e, [LOCK_RUN, B_WRITES], dict(r=rid, s=st))
+    assert a_error is None and b_error is None
+    assert w.val("SELECT output->>'by' FROM stage_result WHERE id = :s", s=st) == "B"
+
+
+def test_following_the_protocol_on_model_calls_does_not_deadlock(w):
+    rid = w.running()
+    call = w.call(rid, w.stage(rid))
+    finish = ("UPDATE model_call SET status = 'interrupted', finished_at = now() WHERE id = :c "
+              "AND status = 'started'")
+    outcome = {}
+
+    def run_b():
+        try:
+            with w.e.begin() as b:
+                b.execute(text(LOCK_RUN), dict(r=rid))
+                b.execute(text(finish), dict(c=call))
+            outcome["error"] = None
+        except Exception as error:
+            outcome["error"] = error
+
+    with w.e.connect() as a:
+        tx = a.begin()
+        a.execute(text(LOCK_RUN), dict(r=rid))
+        thread = threading.Thread(target=run_b)
+        thread.start()
+        deadline = time.monotonic() + 10
+        while waiting_on_a_lock(w.e) == 0 and time.monotonic() < deadline:
+            time.sleep(0.05)
+        assert waiting_on_a_lock(w.e) == 1
+        a.execute(text(finish.replace("interrupted', finished_at", "failed', finished_at")), dict(c=call))
+        tx.commit()
+    thread.join(30)
+    assert outcome["error"] is None  # B's guarded update found the call already finished and changed nothing
+    assert w.val("SELECT status FROM model_call WHERE id = :c", c=call) == "failed"
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index f9cf26d..8d44709 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -1237,12 +1237,25 @@ def test_domains_are_seeded_and_fixed(w):
     rows = w.rows("SELECT key, supported, profile_name FROM domain ORDER BY id")
     assert rows == [("grain_size_strengthening", True, "grain_size_strengthening"),
                     ("fatigue", False, None), ("other", False, None)]
     w.rejected("UPDATE domain SET supported = true", "append-only")
     w.rejected("INSERT INTO domain (key, name, supported) VALUES ('x', 'X', true)", "ck_domain_supported_has_profile")
 
 
 def test_the_audit_log_is_append_only(w):
     w.run_sql("INSERT INTO audit_log (role, stage, function, allowed) VALUES ('planner', 'plan', 'counts', true)")
     w.rejected("UPDATE audit_log SET allowed = false", "append-only")
     w.rejected("DELETE FROM audit_log", "append-only")
     w.rejected("TRUNCATE audit_log", "append-only")
+
+
+# --- the protocol's entry point (re-check item 1) ---------------------------------------------------------
+
+def test_write_lock_locks_a_run_or_a_version(w):
+    rid = w.running()
+    vid = w.val("SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
+    assert w.val("SELECT hc_write_lock(p_run => :r)", r=rid) == "running"
+    assert w.val("SELECT hc_write_lock(p_version => :v)", v=vid) == "dispatched"
+    assert w.val("SELECT hc_write_lock(p_run => :r, p_version => :v)", r=rid, v=vid) == "running"
+    w.rejected("SELECT hc_write_lock(p_run => :r, p_version => :v)", "does not belong", r=rid, v=w.dispatched())
+    w.rejected("SELECT hc_write_lock(p_run => 999999)", "no run 999999")
+    w.rejected("SELECT hc_write_lock()", "needs a run or a hypothesis version")
```

## 2. Source fingerprints: safe paths; files digest plus a version identity (`c09176e`)

`source_file.path` must match `^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$`. At sealing the database sets `files_digest` (SHA-256 of the sorted file list) and requires `fingerprint`, the version's unique identity, to be the SHA-256 of `files <digest>`, `source_type <…>`, `data_kind <…>`, `grouping_unit <…>` (one line each). Tests: unsafe paths including the line-break collision; the same files under a corrected grouping unit seal as a second version; identical files and settings are rejected as a duplicate.

```diff
diff --git a/hypocurate/db/migrations/versions/0001_data_model.py b/hypocurate/db/migrations/versions/0001_data_model.py
index f31e4ac..1024e55 100644
--- a/hypocurate/db/migrations/versions/0001_data_model.py
+++ b/hypocurate/db/migrations/versions/0001_data_model.py
@@ -111,28 +111,31 @@ def upgrade() -> None:
     sa.PrimaryKeyConstraint('id', name=op.f('pk_hypothesis_version')),
     sa.UniqueConstraint('hypothesis_id', 'version_number', name=op.f('uq_hypothesis_version_hypothesis_id_version_number'))
     )
     op.create_table('source_version',
     sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
     sa.Column('source_id', sa.BigInteger(), nullable=False),
     sa.Column('label', sa.Text(), nullable=False),
     sa.Column('obtained_on', sa.Date(), nullable=False),
     sa.Column('source_type', sa.Text(), nullable=False),
     sa.Column('data_kind', sa.Text(), nullable=False),
     sa.Column('grouping_unit', sa.Text(), nullable=False),
     sa.Column('sealed_at', sa.DateTime(timezone=True), nullable=True),
+    sa.Column('files_digest', sa.Text(), nullable=True),
     sa.Column('fingerprint', sa.Text(), nullable=True),
     sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
     sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_fingerprint_format')),
     sa.CheckConstraint('(sealed_at IS NULL) = (fingerprint IS NULL)', name=op.f('ck_source_version_sealed_with_fingerprint')),
+    sa.CheckConstraint("files_digest ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_files_digest_format')),
+    sa.CheckConstraint('(sealed_at IS NULL) = (files_digest IS NULL)', name=op.f('ck_source_version_sealed_with_files_digest')),
     sa.CheckConstraint("source_type IN ('uploaded_table', 'web_interface', 'paper_search', 'model_recall')", name=op.f('ck_source_version_source_type')),
     sa.CheckConstraint("data_kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_source_version_data_kind')),
     sa.CheckConstraint("grouping_unit IN ('paper', 'dataset', 'batch')", name=op.f('ck_source_version_grouping_unit')),
     sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_source_version_source_id')),
     sa.PrimaryKeyConstraint('id', name=op.f('pk_source_version')),
     sa.UniqueConstraint('id', 'source_id', name=op.f('uq_source_version_id_source_id')),
     sa.UniqueConstraint('source_id', 'fingerprint', name=op.f('uq_source_version_source_id_fingerprint'))
     )
     op.create_table('hypothesis_version_source',
     sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=False),
     sa.Column('source_id', sa.BigInteger(), nullable=False),
     sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_hypothesis_version_source_hypothesis_version_id')),
@@ -168,25 +171,25 @@ def upgrade() -> None:
     sa.CheckConstraint("verdict IS NULL OR verdict IN ('supported', 'not_supported')", name=op.f('ck_run_verdict')),
     sa.CheckConstraint('NOT exploratory OR verdict IS NOT NULL', name=op.f('ck_run_exploratory_needs_verdict')),
     sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_run_hypothesis_version_id')),
     sa.PrimaryKeyConstraint('id', name=op.f('pk_run'))
     )
     op.create_foreign_key(op.f('fk_hypothesis_narrower_of_run_id'), 'hypothesis', 'run', ['narrower_of_run_id'], ['id'])
     op.create_table('source_file',
     sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
     sa.Column('source_version_id', sa.BigInteger(), nullable=False),
     sa.Column('path', sa.Text(), nullable=False),
     sa.Column('sha256', sa.Text(), nullable=False),
     sa.Column('content', sa.LargeBinary(), nullable=False),
-    sa.CheckConstraint("path ~ '\\.(csv|xlsx)$'", name=op.f('ck_source_file_data_file_type')),
+    sa.CheckConstraint("path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'", name=op.f('ck_source_file_safe_data_file_path')),
     sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=op.f('ck_source_file_sha256_matches_content')),
     sa.CheckConstraint('octet_length(content) <= 5242880', name=op.f('ck_source_file_max_size')),
     sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'], name=op.f('fk_source_file_source_version_id')),
     sa.PrimaryKeyConstraint('id', name=op.f('pk_source_file')),
     sa.UniqueConstraint('source_version_id', 'path', name=op.f('uq_source_file_source_version_id_path'))
     )
     op.create_table('analysis_set',
     sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
     sa.Column('run_id', sa.BigInteger(), nullable=False),
     sa.Column('key', sa.Text(), nullable=False),
     sa.CheckConstraint("key ~ '^[a-z0-9_]+$'", name=op.f('ck_analysis_set_key_format')),
     sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_analysis_set_run_id')),
@@ -588,25 +591,26 @@ def downgrade() -> None:
 # A run can complete or fail only when none of its stages is running and none of its
 # model calls is still started.
 # ---------------------------------------------------------------------------
 
 FUNCTION_NAMES = [
     "hc_reject(text)",
     "hc_append_only()",
     "hc_no_delete()",
     "hc_is_frozen(bigint)",
     "hc_lock_run(bigint)",
     "hc_lock_version(bigint)",
     "hc_write_lock(bigint, bigint)",
-    "hc_files_fingerprint(bigint)",
+    "hc_files_digest(bigint)",
+    "hc_version_identity(text, text, text, text)",
     "hc_original_domain(bigint)",
     "hc_hypothesis_insert()",
     "hc_version_insert()",
     "hc_version_update()",
     "hc_version_source_change()",
     "hc_run_insert()",
     "hc_run_update()",
     "hc_plan_insert()",
     "hc_run_tag_insert()",
     "hc_tag_value_update()",
     "hc_source_update()",
     "hc_source_version_insert()",
@@ -698,34 +702,46 @@ FUNCTIONS = [
             IF p_version IS NOT NULL AND p_version IS DISTINCT FROM
                (SELECT hypothesis_version_id FROM run WHERE id = p_run) THEN
                 PERFORM hc_reject('run ' || p_run || ' does not belong to hypothesis version ' || p_version);
             END IF;
             s := hc_lock_run(p_run);
             IF s IS NULL THEN
                 PERFORM hc_reject('no run ' || p_run);
             END IF;
         END IF;
         RETURN s;
     END $$
     """,
-    # A source version's fingerprint (owner, 2026-10-05): SHA-256 of its file list,
-    # one line "<sha256>  <path>\\n" per file (the sha256sum format), sorted by path
-    # bytewise. Step 4 computes the same in Python.
+    # A source version's files digest (owner, 2026-10-05; re-check item 2): SHA-256 of its
+    # file list, one line "<sha256>  <path>\n" per file (the sha256sum format), sorted by
+    # path bytewise. Paths cannot hold a line break (CHECK), so the list is unambiguous.
+    # Step 4 computes the same in Python.
     """
-    CREATE FUNCTION hc_files_fingerprint(p_version bigint) RETURNS text LANGUAGE sql STABLE AS $$
+    CREATE FUNCTION hc_files_digest(p_version bigint) RETURNS text LANGUAGE sql STABLE AS $$
         SELECT encode(sha256(convert_to(
                    string_agg(sha256 || '  ' || path || chr(10), '' ORDER BY path COLLATE "C"), 'UTF8')), 'hex')
         FROM source_file WHERE source_version_id = p_version
     $$
     """,
+    # A source version's identity (re-check item 2): SHA-256 of four lines, the files digest
+    # and the three interpretation settings, each "<name> <value>\n". The settings come
+    # from fixed lists (CHECK), so they hold no line break.
+    """
+    CREATE FUNCTION hc_version_identity(p_digest text, p_type text, p_kind text, p_unit text)
+    RETURNS text LANGUAGE sql IMMUTABLE AS $$
+        SELECT encode(sha256(convert_to(
+                   'files ' || p_digest || chr(10) || 'source_type ' || p_type || chr(10)
+                   || 'data_kind ' || p_kind || chr(10) || 'grouping_unit ' || p_unit || chr(10), 'UTF8')), 'hex')
+    $$
+    """,
     # The confirmed domain of the original question, for a narrower query; NULL otherwise.
     """
     CREATE FUNCTION hc_original_domain(p_hypothesis bigint) RETURNS bigint LANGUAGE sql STABLE AS $$
         SELECT hv.confirmed_domain_id
         FROM hypothesis h
         JOIN run r ON r.id = h.narrower_of_run_id
         JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
         WHERE h.id = p_hypothesis
     $$
     """,
     # A narrower question links only to a run whose outcome is partly sufficient (owner, question 1).
     # A completed run never changes, so no lock is needed here.
@@ -923,59 +939,66 @@ FUNCTIONS = [
         IF NEW.key <> OLD.key OR NEW.created_at <> OLD.created_at THEN
             PERFORM hc_reject('a source''s key and registration time cannot change');
         END IF;
         RETURN NEW;
     END $$
     """,
     # A version copies the settings that change how records are read (review finding 4).
     """
     CREATE FUNCTION hc_source_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
     DECLARE s source;
     BEGIN
         SELECT * INTO s FROM source WHERE id = NEW.source_id;
-        IF NEW.sealed_at IS NOT NULL OR NEW.fingerprint IS NOT NULL THEN
+        IF NEW.sealed_at IS NOT NULL OR NEW.fingerprint IS NOT NULL OR NEW.files_digest IS NOT NULL THEN
             PERFORM hc_reject('a source version is sealed after its files are added');
         END IF;
         IF NEW.source_type IS DISTINCT FROM s.source_type AND NEW.source_type IS NOT NULL
            OR NEW.data_kind IS DISTINCT FROM s.data_kind AND NEW.data_kind IS NOT NULL
            OR NEW.grouping_unit IS DISTINCT FROM s.grouping_unit AND NEW.grouping_unit IS NOT NULL THEN
             PERFORM hc_reject('a source version copies its settings from the source');
         END IF;
         NEW.source_type := s.source_type;
         NEW.data_kind := s.data_kind;
         NEW.grouping_unit := s.grouping_unit;
         RETURN NEW;
     END $$
     """,
     # The only change to a version is sealing it, once (owner, 2026-10-05).
     """
     CREATE FUNCTION hc_source_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE digest text;
     BEGIN
         IF OLD.sealed_at IS NOT NULL THEN
             PERFORM hc_reject('a sealed source version cannot change');
         END IF;
         IF NEW.sealed_at IS NULL OR NEW.source_id <> OLD.source_id OR NEW.label <> OLD.label
            OR NEW.obtained_on <> OLD.obtained_on OR NEW.source_type <> OLD.source_type
            OR NEW.data_kind <> OLD.data_kind OR NEW.grouping_unit <> OLD.grouping_unit
            OR NEW.created_at <> OLD.created_at THEN
             PERFORM hc_reject('the only change to a source version is sealing it');
         END IF;
         IF NEW.sealed_at IS DISTINCT FROM now() THEN
             PERFORM hc_reject('sealed_at is set by the database at sealing');
         END IF;
         IF NOT EXISTS (SELECT 1 FROM source_file WHERE source_version_id = NEW.id) THEN
             PERFORM hc_reject('a source version needs at least one file before sealing');
         END IF;
-        IF NEW.fingerprint IS DISTINCT FROM hc_files_fingerprint(NEW.id) THEN
-            PERFORM hc_reject('the fingerprint must be the SHA-256 of the sorted file list');
+        digest := hc_files_digest(NEW.id);
+        IF NEW.files_digest IS NOT NULL AND NEW.files_digest <> digest THEN
+            PERFORM hc_reject('files_digest must be the SHA-256 of the sorted file list');
+        END IF;
+        NEW.files_digest := digest;
+        IF NEW.fingerprint IS DISTINCT FROM hc_version_identity(digest, NEW.source_type, NEW.data_kind,
+                                                                NEW.grouping_unit) THEN
+            PERFORM hc_reject('the fingerprint must be the SHA-256 of the files digest and the interpretation settings');
         END IF;
         RETURN NEW;
     END $$
     """,
     """
     CREATE FUNCTION hc_source_file_insert() RETURNS trigger LANGUAGE plpgsql AS $$
     DECLARE sealed timestamptz;
     BEGIN
         SELECT sealed_at INTO sealed FROM source_version WHERE id = NEW.source_version_id FOR NO KEY UPDATE;
         IF sealed IS NOT NULL THEN
             PERFORM hc_reject('files cannot be added to a sealed source version');
         END IF;
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index ee49fbd..43cce05 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -159,60 +159,69 @@ class Source(Base):
         CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
         CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
         CheckConstraint(one_of("adapter_status", ("adapter_needed", "available")), name="adapter_status"),
         CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
     )
 
 
 class SourceVersion(Base):
     """A snapshot of a source (review finding 4). It holds its own copy of the settings
     that change how records are read, copied from `source` at insert. Files are added,
     then the version is sealed once: the database sets `sealed_at` and checks that
     `fingerprint` is the SHA-256 of the sorted file list. Only a sealed version can be
-    used by a run. Nothing changes after sealing; it is never deleted."""
+    used by a run. Nothing changes after sealing; it is never deleted.
+    At sealing (re-check item 2) the database sets `files_digest`, the SHA-256 of the
+    sorted file list, and requires `fingerprint` to be the SHA-256 of that digest plus
+    the interpretation settings. `fingerprint` is the version's identity (unique per
+    source), so the same files under revised settings seal as a new version."""
     __tablename__ = "source_version"
     id: Mapped[int] = pk()
     source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
     label: Mapped[str] = mapped_column(Text)
     obtained_on: Mapped[date] = mapped_column(Date)
     source_type: Mapped[str] = mapped_column(Text)
     data_kind: Mapped[str] = mapped_column(Text)
     grouping_unit: Mapped[str] = mapped_column(Text)
     sealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
+    files_digest: Mapped[str | None] = mapped_column(Text)
     fingerprint: Mapped[str | None] = mapped_column(Text)
     created_at: Mapped[datetime] = created()
     __table_args__ = (
         UniqueConstraint("source_id", "fingerprint"),
         UniqueConstraint("id", "source_id"),
         CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
         CheckConstraint("(sealed_at IS NULL) = (fingerprint IS NULL)", name="sealed_with_fingerprint"),
+        CheckConstraint(f"files_digest {SHA256}", name="files_digest_format"),
+        CheckConstraint("(sealed_at IS NULL) = (files_digest IS NULL)", name="sealed_with_files_digest"),
         CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
         CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
         CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
     )
 
 
 class SourceFile(Base):
     """A data file an adapter reads (owner decision: only data files, at most 5 MiB).
     Added only before its version is sealed. Append-only."""
     __tablename__ = "source_file"
     id: Mapped[int] = pk()
     source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
     path: Mapped[str] = mapped_column(Text)
     sha256: Mapped[str] = mapped_column(Text)
     content: Mapped[bytes] = mapped_column(LargeBinary)
     __table_args__ = (
         UniqueConstraint("source_version_id", "path"),
         CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
-        CheckConstraint(r"path ~ '\.(csv|xlsx)$'", name="data_file_type"),
+        # Re-check item 2: a safe character set, anchored at both ends, so a path holds no
+        # line break and the sealed file list has one unambiguous line per file.
+        CheckConstraint("path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'", name="safe_data_file_path"),
         CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
     )
 
 
 # --- Agent settings ------------------------------------------------------------
 
 class AgentSetting(Base):
     """Versioned settings per role (PRD 9.5). Append-only: a change is a new version."""
     __tablename__ = "agent_setting"
     id: Mapped[int] = pk()
     role: Mapped[str] = mapped_column(Text)
     version: Mapped[int] = mapped_column(Integer)
diff --git a/tests/model_builder.py b/tests/model_builder.py
index c4b5d86..4a9401b 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -6,31 +6,39 @@ import hashlib
 
 import pytest
 from sqlalchemy import text
 from sqlalchemy.exc import IntegrityError
 
 FP = "0" * 64  # a well-formed fingerprint
 
 
 def sha(data: bytes) -> str:
     return hashlib.sha256(data).hexdigest()
 
 
-def files_fingerprint(files: dict[str, bytes]) -> str:
-    """A source version's fingerprint (owner, 2026-10-05): SHA-256 of one line
+def files_digest(files: dict[str, bytes]) -> str:
+    """A source version's files digest (owner, 2026-10-05): SHA-256 of one line
     "<sha256>  <path>\\n" per file, sorted by path (the sha256sum format)."""
     listing = "".join(f"{sha(files[path])}  {path}\n" for path in sorted(files))
     return sha(listing.encode())
 
 
+def version_fingerprint(files: dict[str, bytes], source_type: str, data_kind: str, grouping_unit: str) -> str:
+    """A source version's identity (re-check item 2): the files digest plus the
+    interpretation settings, one "<name> <value>\\n" line each."""
+    text = (f"files {files_digest(files)}\nsource_type {source_type}\n"
+            f"data_kind {data_kind}\ngrouping_unit {grouping_unit}\n")
+    return sha(text.encode())
+
+
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
@@ -45,26 +53,33 @@ class World:
     def new_version(self, key, label="v1"):
         return self.val("INSERT INTO source_version (source_id, label, obtained_on) "
                         "VALUES (:s, :l, '2026-10-04') RETURNING id", s=self.source[key], l=label)
 
     def add_file(self, version, path, content):
         self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)",
                      v=version, p=path, h=sha(content), c=content)
 
     def files(self, version):
         return {p: bytes(c) for p, c in self.rows(
             "SELECT path, content FROM source_file WHERE source_version_id = :v", v=version)}
 
+    def settings(self, version):
+        return self.rows("SELECT source_type, data_kind, grouping_unit FROM source_version WHERE id = :v",
+                         v=version)[0]
+
+    def fingerprint(self, version, files=None):
+        return version_fingerprint(files if files is not None else self.files(version), *self.settings(version))
+
     def seal(self, version, fingerprint=None):
-        fingerprint = fingerprint or files_fingerprint(self.files(version))
+        fingerprint = fingerprint or self.fingerprint(version)
         self.run_sql("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                      v=version, fp=fingerprint)
 
     # --- plumbing ---------------------------------------------------------------------
     def run_sql(self, sql, **params):
         with self.e.begin() as conn:
             return conn.execute(text(sql), params)
 
     def val(self, sql, **params):
         with self.e.begin() as conn:
             return conn.execute(text(sql), params).scalar()
 
diff --git a/tests/test_concurrency.py b/tests/test_concurrency.py
index 4cfe02c..5153584 100644
--- a/tests/test_concurrency.py
+++ b/tests/test_concurrency.py
@@ -2,25 +2,25 @@
 
 In each test, transaction A does its write and stays open. Transaction B starts in a
 thread and must wait on A's lock (checked in pg_stat_activity). A then commits, and B
 either sees A's committed write (serialized) or is rejected. Every race the review
 describes is run in both orders."""
 import threading
 import time
 
 import pytest
 from sqlalchemy import text
 from sqlalchemy.exc import IntegrityError
 
-from model_builder import FP, World, files_fingerprint, sha
+from model_builder import FP, World, sha
 
 
 @pytest.fixture
 def w(db):
     return World(db)
 
 
 def waiting_on_a_lock(engine) -> int:
     with engine.connect() as conn:
         return conn.execute(text(
             "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
             "AND wait_event_type = 'Lock' AND state = 'active'")).scalar()
@@ -207,37 +207,37 @@ def test_no_dataset_first_then_freeze_is_rejected(w):
 def test_freeze_first_then_no_dataset_is_rejected(w):
     rid = ready_to_freeze(w)
     error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)", NO_DATASET,
                  dict(r=rid, fp=FP), dict(r=rid))
     rejected(error, "calibration is reported per analysis")
 
 
 # --- a source file against sealing its version --------------------------------------------------------------------
 
 def test_file_first_then_sealing_includes_it(w):
     sv = w.new_version("mpea", "v2")
     w.add_file(sv, "a.csv", b"a")
-    both = files_fingerprint({"a.csv": b"a", "b.csv": b"b"})
+    both = w.fingerprint(sv, {"a.csv": b"a", "b.csv": b"b"})
     error = race(w.e, "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                  "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                  dict(v=sv, h=sha(b"b"), c=b"b"), dict(v=sv, fp=both))
     assert error is None  # the seal waited, then fingerprinted both files
 
 
 def test_sealing_first_then_file_is_rejected(w):
     sv = w.new_version("mpea", "v2")
     w.add_file(sv, "a.csv", b"a")
     error = race(w.e, "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                  "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
-                 dict(v=sv, fp=files_fingerprint({"a.csv": b"a"})), dict(v=sv, h=sha(b"b"), c=b"b"))
+                 dict(v=sv, fp=w.fingerprint(sv)), dict(v=sv, h=sha(b"b"), c=b"b"))
     rejected(error, "sealed source version")
     assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=sv) == 1
 
 
 # --- the protocol against child-row deadlocks (re-check item 1) ----------------------------------------------
 # A holds the run lock; B updates a child row; A then updates the same child row.
 # The child UPDATE locks its row before its trigger asks for the run lock, so the
 # triggers alone cannot fix the lock order. The protocol does: every writer calls
 # hc_write_lock first.
 
 LOCK_RUN = "SELECT hc_write_lock(p_run => :r)"
 B_WRITES = "UPDATE stage_result SET output = '{\"by\": \"B\"}' WHERE id = :s"
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index 8d44709..ce9c7ec 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -1,21 +1,21 @@
 """Step 3: the rules the database enforces (PRD 7, with the owner's decisions of
 2026-10-04/05). Every rule has an allowed case and a rejected case, on a freshly
 migrated scratch database. Rejections by a trigger read "hypocurate: ..."; rejections
 by a CHECK name the constraint."""
 import pytest
 from sqlalchemy.exc import IntegrityError
 
 from hypocurate.db.models import MAX_FILE_BYTES
-from model_builder import FP, World, files_fingerprint, sha
+from model_builder import FP, World, files_digest, sha
 
 
 @pytest.fixture
 def w(db):
     return World(db)
 
 
 # --- queries and versions ------------------------------------------------------------------
 
 def test_query_numbers_come_from_a_sequence(w):
     numbers = [w.val("SELECT number FROM hypothesis WHERE id = :h", h=w.hypothesis()) for _ in range(2)]
     assert numbers == ["Q-0001", "Q-0002"]
@@ -1139,25 +1139,25 @@ def test_commentary_comes_after_completion_and_lists_mismatches(w):
 # --- files (owner decision: data files only, 5 MiB) ------------------------------------------------------
 
 SOURCE_FILE = "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:sv, :p, :h, :c)"
 ARTIFACT = ("INSERT INTO artifact (run_id, kind, filename, media_type, sha256, content) "
             "VALUES (:r, 'workbook', 'run.xlsx', 'application/octet-stream', :h, :c)")
 
 
 def test_source_files_are_data_files_up_to_5_mib(w):
     sv = w.new_version("mpea", "v2")  # files are added before the version is sealed
     at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
     w.run_sql(SOURCE_FILE, sv=sv, p="MPEA_dataset.csv", h=sha(at_limit), c=at_limit)
     w.rejected(SOURCE_FILE, "ck_source_file_max_size", sv=sv, p="big.csv", h=sha(over), c=over)
-    w.rejected(SOURCE_FILE, "ck_source_file_data_file_type", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
+    w.rejected(SOURCE_FILE, "ck_source_file_safe_data_file_path", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
     w.rejected(SOURCE_FILE, "ck_source_file_sha256_matches_content", sv=sv, p="other.csv", h=sha(b"a"), c=b"b")
     w.run_sql(SOURCE_FILE, sv=sv, p="Grain_Size_Summary_v3.xlsx", h=sha(b"x"), c=b"x")
     w.rejected("UPDATE source_file SET content = 'y'", "append-only")
     w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "only change to a source version is sealing",
                v=sv)
     w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "sealed source version cannot change",
                v=w.version["mpea"])
 
 
 # --- source versions: sealed files and their interpretation (review finding 4) ------------------------
 
 def test_files_cannot_be_added_after_sealing(w):
@@ -1166,35 +1166,70 @@ def test_files_cannot_be_added_after_sealing(w):
     w.seal(sv)
     with pytest.raises(IntegrityError, match="sealed source version"):
         w.add_file(sv, "b.csv", b"b")
 
 
 def test_sealing_needs_files_and_the_fingerprint_of_the_file_list(w):
     sv = w.new_version("mpea", "v2")
     with pytest.raises(IntegrityError, match="at least one file"):
         w.seal(sv, fingerprint="0" * 64)
     files = {"b.csv": b"second", "a.csv": b"first"}
     for path, content in files.items():
         w.add_file(sv, path, content)
-    with pytest.raises(IntegrityError, match="SHA-256 of the sorted file list"):
+    with pytest.raises(IntegrityError, match="files digest and the interpretation settings"):
         w.seal(sv, fingerprint="0" * 64)
     w.rejected("UPDATE source_version SET sealed_at = now() - interval '1 day', fingerprint = :fp WHERE id = :v",
-               "set by the database", v=sv, fp=files_fingerprint(files))
+               "set by the database", v=sv, fp=w.fingerprint(sv))
+    w.rejected("UPDATE source_version SET sealed_at = now(), fingerprint = :fp, files_digest = :d WHERE id = :v",
+               "files_digest must be the SHA-256", v=sv, fp=w.fingerprint(sv), d="0" * 64)
     w.seal(sv)
-    assert w.val("SELECT fingerprint FROM source_version WHERE id = :v", v=sv) == files_fingerprint(files)
+    assert w.rows("SELECT files_digest, fingerprint FROM source_version WHERE id = :v", v=sv) == [
+        (files_digest(files), w.fingerprint(sv, files))]
     with pytest.raises(IntegrityError, match="sealed source version cannot change"):
         w.seal(sv)
     w.rejected("DELETE FROM source_version WHERE id = :v", "never deleted", v=sv)
 
 
+@pytest.mark.parametrize("path", [
+    "a.csv\n" + "0" * 64 + "  b.csv",   # the re-check's collision: a line break inside a path
+    "a.csv\r", "a b.csv", "../outside.csv", "/abs.csv", "a.csv.zip", "café.csv", "",
+])
+def test_unsafe_file_paths_are_rejected(w, path):
+    """Re-check item 2: a safe character set, anchored at both ends."""
+    with pytest.raises(IntegrityError, match="ck_source_file_safe_data_file_path"):
+        w.add_file(w.new_version("mpea", "v2"), path, b"x")
+
+
+def test_the_same_files_under_revised_settings_seal_as_a_new_version(w):
+    """Re-check item 2: the identity covers the interpretation settings, so a corrected
+    grouping unit can be sealed with the same files; identical files and settings are
+    still a duplicate."""
+    files = {"tamu_fcc.csv": b"tamu_fcc,data\n"}
+    first = w.version["tamu_fcc"]
+    assert w.files(first) == files and w.settings(first)[2] == "dataset"
+    w.run_sql("UPDATE source SET grouping_unit = 'batch' WHERE key = 'tamu_fcc'")
+    revised = w.new_version("tamu_fcc", "v1-batches")
+    w.add_file(revised, "tamu_fcc.csv", files["tamu_fcc.csv"])
+    w.seal(revised)
+    rows = w.rows("SELECT files_digest, fingerprint, grouping_unit FROM source_version WHERE id IN (:a, :b) "
+                  "ORDER BY id", a=first, b=revised)
+    assert rows[0][0] == rows[1][0] == files_digest(files)  # the same files
+    assert rows[0][1] != rows[1][1]                          # a different identity
+    assert [r[2] for r in rows] == ["dataset", "batch"]
+    duplicate = w.new_version("tamu_fcc", "v1-batches-again")
+    w.add_file(duplicate, "tamu_fcc.csv", files["tamu_fcc.csv"])
+    with pytest.raises(IntegrityError, match="uq_source_version_source_id_fingerprint"):
+        w.seal(duplicate)
+
+
 def test_a_new_version_starts_unsealed(w):
     w.rejected("INSERT INTO source_version (source_id, label, obtained_on, sealed_at, fingerprint) "
                "VALUES (:s, 'v2', '2026-10-05', now(), :fp)", "sealed after its files are added",
                s=w.source["mpea"], fp=FP)
 
 
 def test_only_a_sealed_version_can_be_used_by_a_run(w):
     unsealed = w.new_version("mpea", "v2")
     vid = w.dispatched()
     rid = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
     w.rejected("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                "VALUES (:r, :s, :sv, 'pending')", "only a sealed source version", r=rid, s=w.source["mpea"],
```

## 3. Costs: finite values only (`1ea2850`)

CHECK `money_finite`: `max_cost < 'Infinity' AND (cost IS NULL OR cost < 'Infinity')`. PostgreSQL orders numeric NaN above Infinity, so this excludes NaN and +Infinity; -Infinity already fails `> 0` / `>= 0`. Tests: NaN, Infinity and -Infinity for `max_cost` and for `cost`.

```diff
diff --git a/hypocurate/db/migrations/versions/0001_data_model.py b/hypocurate/db/migrations/versions/0001_data_model.py
index 1024e55..03cbe73 100644
--- a/hypocurate/db/migrations/versions/0001_data_model.py
+++ b/hypocurate/db/migrations/versions/0001_data_model.py
@@ -453,24 +453,25 @@ def upgrade() -> None:
     sa.Column('error', sa.Text(), nullable=True),
     sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
     sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
     sa.CheckConstraint("role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_model_call_role')),
     sa.CheckConstraint("status <> 'failed' OR (finished_at IS NOT NULL AND ((input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL) OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL)))", name=op.f('ck_model_call_failed_usage_all_or_none')),
     sa.CheckConstraint("status <> 'interrupted' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_interrupted_has_no_usage')),
     sa.CheckConstraint("status <> 'started' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NULL)", name=op.f('ck_model_call_started_has_no_usage')),
     sa.CheckConstraint("status <> 'succeeded' OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_succeeded_has_usage')),
     sa.CheckConstraint("status IN ('started', 'succeeded', 'failed', 'interrupted')", name=op.f('ck_model_call_status')),
     sa.CheckConstraint('coalesce(input_tokens, 0) >= 0 AND coalesce(output_tokens, 0) >= 0 AND coalesce(cached_tokens, 0) >= 0 AND coalesce(cost, 0) >= 0', name=op.f('ck_model_call_usage_not_negative')),
     sa.CheckConstraint('length(model) > 0 AND length(price_table_version) > 0', name=op.f('ck_model_call_model_and_prices_named')),
     sa.CheckConstraint('max_cost > 0', name=op.f('ck_model_call_max_cost_positive')),
+    sa.CheckConstraint("max_cost < 'Infinity' AND (cost IS NULL OR cost < 'Infinity')", name=op.f('ck_model_call_money_finite')),
     sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'], name='fk_model_call_stage_result'),
     sa.PrimaryKeyConstraint('id', name=op.f('pk_model_call'))
     )
     op.create_index('ix_model_call_run_id', 'model_call', ['run_id'], unique=False)
     op.create_table('run_record',
     sa.Column('run_id', sa.BigInteger(), nullable=False),
     sa.Column('record_id', sa.BigInteger(), nullable=False),
     sa.Column('eligible', sa.Boolean(), nullable=False),
     sa.Column('rule', sa.Text(), nullable=False),
     sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
     sa.CheckConstraint('length(rule) > 0', name=op.f('ck_run_record_rule_named')),
     sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_run_record_record_id')),
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 43cce05..7a2e6e5 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -499,24 +499,27 @@ class ModelCall(Base):
     cost: Mapped[Decimal | None] = mapped_column(Numeric())
     error: Mapped[str | None] = mapped_column(Text)
     started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
     finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
     __table_args__ = (
         ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                              name="fk_model_call_stage_result"),
         Index("ix_model_call_run_id", "run_id"),
         CheckConstraint(one_of("role", ROLES), name="role"),
         CheckConstraint(one_of("status", CALL_STATUSES), name="status"),
         CheckConstraint("length(model) > 0 AND length(price_table_version) > 0", name="model_and_prices_named"),
         CheckConstraint("max_cost > 0", name="max_cost_positive"),
+        # Re-check item 3: unbounded numeric also holds NaN and Infinity; PostgreSQL orders
+        # NaN above Infinity, so "< 'Infinity'" excludes both. -Infinity fails "> 0"/">= 0".
+        CheckConstraint("max_cost < 'Infinity' AND (cost IS NULL OR cost < 'Infinity')", name="money_finite"),
         CheckConstraint(" AND ".join(f"coalesce({c}, 0) >= 0" for c in USAGE), name="usage_not_negative"),
         CheckConstraint(f"status <> 'started' OR ({_all('IS NULL')} AND finished_at IS NULL)",
                         name="started_has_no_usage"),
         CheckConstraint(f"status <> 'succeeded' OR ({_all('IS NOT NULL')} AND finished_at IS NOT NULL)",
                         name="succeeded_has_usage"),
         CheckConstraint(f"status <> 'failed' OR (finished_at IS NOT NULL AND (({_all('IS NULL')}) "
                         f"OR ({_all('IS NOT NULL')})))", name="failed_usage_all_or_none"),
         CheckConstraint(f"status <> 'interrupted' OR ({_all('IS NULL')} AND finished_at IS NOT NULL)",
                         name="interrupted_has_no_usage"),
     )
 
 
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index ce9c7ec..d646c96 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -1078,24 +1078,47 @@ def test_small_costs_are_stored_exactly(w):
     rid = w.running()
     call = w.call(rid, w.stage(rid), max_cost=Decimal("1E-12"))
     w.finish_call(call, "succeeded", (1, 1, 0, Decimal("3E-13")))
     w.call(rid, w.stage(rid, "curator", "curator"), max_cost=Decimal("2E-12"))
     row = w.rows("SELECT reported_cost, unconfirmed_cost_bound, cap_cost FROM model_call_totals_by_run "
                  "WHERE run_id = :r", r=rid)[0]
     assert row == (Decimal("3E-13"), Decimal("2E-12"), Decimal("2.3E-12"))
     w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
                "VALUES (:r, :s, 'planner', 'm', 'p', 0)", "ck_model_call_max_cost_positive",
                r=rid, s=w.val("SELECT min(id) FROM stage_result"))
 
 
+@pytest.mark.parametrize("value, match", [
+    ("NaN", "ck_model_call_money_finite"), ("Infinity", "ck_model_call_money_finite"),
+    ("-Infinity", "ck_model_call_max_cost_positive"),
+])
+def test_max_cost_must_be_finite(w, value, match):
+    """Re-check item 3: NaN and infinity would contaminate totals and caps."""
+    rid = w.running()
+    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
+               "VALUES (:r, :s, 'planner', 'm', 'p', CAST(:v AS numeric))", match, r=rid, s=w.stage(rid), v=value)
+
+
+@pytest.mark.parametrize("value, match", [
+    ("NaN", "ck_model_call_money_finite"), ("Infinity", "ck_model_call_money_finite"),
+    ("-Infinity", "ck_model_call_usage_not_negative"),
+])
+def test_reported_cost_must_be_finite(w, value, match):
+    rid = w.running()
+    call = w.call(rid, w.stage(rid))
+    w.rejected("UPDATE model_call SET status = 'succeeded', input_tokens = 1, output_tokens = 1, cached_tokens = 0, "
+               "cost = CAST(:v AS numeric), finished_at = now() WHERE id = :c", match, c=call, v=value)
+    assert w.val("SELECT status FROM model_call WHERE id = :c", c=call) == "started"
+
+
 def test_call_times_are_set_by_the_database(w):
     rid = w.running()
     st = w.stage(rid)
     w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, started_at) "
                "VALUES (:r, :s, 'planner', 'm', 'p', 1, now() - interval '40 days')", "started_at is set by the database",
                r=rid, s=st)
     call = w.call(rid, st)
     w.rejected("UPDATE model_call SET status = 'interrupted', finished_at = now() - interval '1 day' WHERE id = :c",
                "finished_at is set by the database", c=call)
 
 
 def test_a_run_without_calls_totals_zero(w):
```

## 4. A stage result's role is frozen (`f3e8f71`)

`hc_stage_result_update` rejects a change of `role` (with run, stage name, attempt and start time). Tests: a Commentator stage on a completed run cannot be relabelled to `planner` or NULL, with or without finishing it in the same update; a running stage cannot be relabelled while other fields still update.

```diff
diff --git a/hypocurate/db/migrations/versions/0001_data_model.py b/hypocurate/db/migrations/versions/0001_data_model.py
index 03cbe73..1317499 100644
--- a/hypocurate/db/migrations/versions/0001_data_model.py
+++ b/hypocurate/db/migrations/versions/0001_data_model.py
@@ -1337,26 +1337,26 @@ FUNCTIONS = [
     """,
     """
     CREATE FUNCTION hc_stage_result_update() RETURNS trigger LANGUAGE plpgsql AS $$
     DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
     BEGIN
         IF NOT (s = 'running' OR s = 'completed' AND OLD.stage = 'commentator') THEN
             PERFORM hc_reject('a stage result changes only while its run is running');
         END IF;
         IF OLD.status <> 'running' THEN
             PERFORM hc_reject('a finished stage result is final');
         END IF;
         IF NEW.run_id <> OLD.run_id OR NEW.stage <> OLD.stage OR NEW.attempt <> OLD.attempt
-           OR NEW.started_at <> OLD.started_at THEN
-            PERFORM hc_reject('the identity of a stage result cannot change');
+           OR NEW.role IS DISTINCT FROM OLD.role OR NEW.started_at <> OLD.started_at THEN
+            PERFORM hc_reject('the identity of a stage result (run, stage, attempt, role) cannot change');
         END IF;
         RETURN NEW;
     END $$
     """,
     # Model calls (owner, question 5; review finding 7): written before the request with
     # the database's time, finished exactly once with the database's time. After
     # completion only the Commentator's calls, which count in the run's totals.
     """
     CREATE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
     DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
     BEGIN
         IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index d646c96..29cdb6f 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -1125,24 +1125,44 @@ def test_a_run_without_calls_totals_zero(w):
     rid = w.running()
     assert tuple(map(float, w.rows("SELECT calls, reported_cost, cap_cost FROM model_call_totals_by_run "
                                    "WHERE run_id = :r", r=rid)[0])) == (0, 0, 0)
 
 
 def test_no_table_stores_token_or_cost_totals(w):
     columns = w.rows("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' "
                      "AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' "
                      "AND table_schema = 'public') AND (column_name LIKE '%token%' OR column_name LIKE '%cost%')")
     assert {t for t, _ in columns} == {"model_call"}
 
 
+@pytest.mark.parametrize("finishing", [False, True])
+def test_a_commentator_stage_cannot_be_relabelled(w, finishing):
+    """Re-check item 4: the role is frozen with the stage name, also on a completed
+    run and also in the update that finishes the stage."""
+    rid = w.running()
+    w.complete(rid, "insufficient")
+    st = w.stage(rid, "commentator", "commentator")
+    finish = ", status = 'done', finished_at = now()" if finishing else ""
+    for role in ("'planner'", "NULL"):
+        w.rejected(f"UPDATE stage_result SET role = {role}{finish} WHERE id = :s", "cannot change", s=st)
+    assert w.rows("SELECT role, status FROM stage_result WHERE id = :s", s=st) == [("commentator", "running")]
+
+
+def test_a_running_stage_cannot_be_relabelled(w):
+    rid = w.running()
+    st = w.stage(rid, "planner", "planner")
+    w.rejected("UPDATE stage_result SET role = 'critic' WHERE id = :s", "cannot change", s=st)
+    w.run_sql("UPDATE stage_result SET output = '{}' WHERE id = :s", s=st)  # other fields still update
+
+
 def test_a_finished_stage_result_is_final(w):
     rid = w.running()
     st = w.stage(rid)
     w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=st)
     w.rejected("UPDATE stage_result SET output = '{\"changed\": true}' WHERE id = :s", "is final", s=st)
     w.rejected("DELETE FROM stage_result", "never deleted")
 
 
 # --- commentary ---------------------------------------------------------------------------------------
 
 def test_commentary_comes_after_completion_and_lists_mismatches(w):
     rid = w.running()
```

## Test output

```
$ .venv/bin/pytest -v  (the tests for the four items)
tests/test_concurrency.py::test_skipping_the_protocol_can_deadlock PASSED
tests/test_concurrency.py::test_following_the_protocol_does_not_deadlock PASSED
tests/test_concurrency.py::test_following_the_protocol_on_model_calls_does_not_deadlock PASSED
tests/test_data_model.py::test_max_cost_must_be_finite[NaN-ck_model_call_money_finite] PASSED
tests/test_data_model.py::test_max_cost_must_be_finite[Infinity-ck_model_call_money_finite] PASSED
tests/test_data_model.py::test_max_cost_must_be_finite[-Infinity-ck_model_call_max_cost_positive] PASSED
tests/test_data_model.py::test_reported_cost_must_be_finite[NaN-ck_model_call_money_finite] PASSED
tests/test_data_model.py::test_reported_cost_must_be_finite[Infinity-ck_model_call_money_finite] PASSED
tests/test_data_model.py::test_reported_cost_must_be_finite[-Infinity-ck_model_call_usage_not_negative] PASSED
tests/test_data_model.py::test_a_commentator_stage_cannot_be_relabelled[False] PASSED
tests/test_data_model.py::test_a_commentator_stage_cannot_be_relabelled[True] PASSED
tests/test_data_model.py::test_a_running_stage_cannot_be_relabelled PASSED
tests/test_data_model.py::test_source_files_are_data_files_up_to_5_mib PASSED
tests/test_data_model.py::test_sealing_needs_files_and_the_fingerprint_of_the_file_list PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[a.csv\n0000000000000000000000000000000000000000000000000000000000000000  b.csv] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[a.csv\r] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[a b.csv] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[../outside.csv] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[/abs.csv] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[a.csv.zip] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[caf\xe9.csv] PASSED
tests/test_data_model.py::test_unsafe_file_paths_are_rejected[] PASSED
tests/test_data_model.py::test_the_same_files_under_revised_settings_seal_as_a_new_version PASSED
tests/test_data_model.py::test_write_lock_locks_a_run_or_a_version PASSED
====================== 24 passed, 146 deselected in 7.61s ======================

$ .venv/bin/pytest -q   (whole suite)
375 passed in 52.87s

$ docker compose run --rm test
375 passed in 52.35s
```
