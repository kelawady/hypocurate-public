# Build step 9a — fix packet (fix round 1)

Date: 2026-10-08. Branch: `step-09a-waiting`. Reviewed head: `f1ccddf`. Head when generated: `7fc5ee3`. Generated from
the files on disk by a script (`~/hc-work/step09a/fixpacket.py`, quoted in section 9), so every diff and output below
is quoted exactly.

## How to use this packet

ChatGPT's review of `f1ccddf` (`docs/reviews/step09a_review_chatgpt.md`) found the step not safe to merge, with five
findings. The owner accepted all five and added one decision: every run stores its effective ceiling at dispatch. This
packet covers only this round:
1. the findings and their fixes;
2. the code diff;
3. the tests, new and changed, and the tests that failed before;
4. the register;
5. the mutation checks;
6. the reference comparison with `main`;
7. the suite and the images;
8. the local database;
9. the scripts.

The summary (`step09a_summary.md`) carries an update note at the top. Please confirm each finding is closed, and say
whether anything in this round is stronger in its claims than the code supports.

Commits of this round:

```
7fc5ee3 Step 9a fix round 1: register corrections
0b436df Step 9a fix round 1, finding 4: no ceiling at confirmation
47c4f7c Step 9a fix round 1, findings 2 and 5, and the owner's stored ceiling (0007 amended; unmerged)
0b5ab5b Step 9a fix round 1, findings 1 and 3: a resume respects earlier stops; a confirmed run goes on
30cc905 Step 9a: ChatGPT's review, saved verbatim (not safe to merge; five findings)
```

## 1. The findings and their fixes

### Finding 1: A resume respects earlier stops (commit `0b5ab5b`)

Before each agent step, `proceed`/`prepare` read the role's latest stored stage whatever its status (`_stored(..., done=False)`, `_agent_stop`, `_critic_failures`, `_stage_code`).
- **A stop stays a stop:** a recording or reservation failure (`lm.RUN_STOPS`), or a stage still running (`stage_left_running`), stops the run again. No further request is made, nothing more is written, and the run stays running for 9b.
- **Planner:** a stored spending refusal fails the run as `spending_refused`; any other stored failure fails it as `planner_failed`. The Planner is never asked again in 9a.
- **Critic:** its stored stages decide as they did when it ran. A stop stops the run; a spending refusal fails it; any other failure lets the run go on.
- **Analyst:** a stop stops the run before completion, also on the partly-sufficient path, before the copy and the narrower question. Any other failure, a spending refusal included, completes the run with code's decision (A3, B2).
- **Left for 9b:** interrupted stages and the one Planner repeat.

### Finding 2: Source freshness in the database, with a shared lock (commit `47c4f7c`)

- **The check:** `hc_rules_confirmation_insert` takes advisory lock `SOURCES_LOCK_KEY`, then refuses when a source the run uses has a sealed version newer than the run's, or a source exists that the run did not record at dispatch.
- **Registration and sealing:** `hc_sources_lock` takes the same lock when a source is inserted, or a version is inserted sealed or becomes sealed. 0001 never allows a version to be inserted sealed, so that trigger is a backstop only.
- **The Python path:** `confirmation.confirm` takes the lock before its own check, so the check and the insert see the same sources, and a registration that commits meanwhile gets code's reason.
- **Lock order:** the run's lock, then the sources lock. Registration takes no run lock, so there is no cycle.
- **Scope** (the owner's wording, "any source the run uses"): a newer version of a source the query did not choose is no change. The code's check is the same.

### Finding 3: A confirmed run goes on through run() (commit `0b5ab5b`)

`prepare` recognises an existing confirmation or a locked plan, and goes on to `proceed` (ready) without waiting again. `proceed` moves a confirmed waiting run to running, as before.

### Finding 4: No ceiling at confirmation (commit `0b436df`)

`confirm --ceiling` and `_confirm`'s ceiling are removed. The ceiling is stored only at dispatch, and `spend.reserve` reads it on every request.

### Finding 5: Cancel in the database (commit `47c4f7c`)

`hc_run_waiting` refuses a change to failed with a reason beginning "cancelled:" unless the run was queued or waiting. Other failures from running stay allowed.

### Finding Owner: Every run stores its effective ceiling (commit `47c4f7c`)

- **Dispatch:** `_new_run` stores the given ceiling, or the per-run cap (`queries.spend_cap()`, which is `spend.RUN_CAP_USD`).
- **The database:** 0007 sets the column's default to the cap (`CEILING_DEFAULT`, tested equal to `RUN_CAP_USD`), so a dispatch by the previous release's code stores it too. The default is set after the column is added, so runs before 0007 stay empty.
- **The downgrade** refuses only a ceiling below the cap. A ceiling equal to the cap says no more than the cap, and refusing it would make 0007 impossible to downgrade once any run exists.

**The owner's three choices, stated before the build:**
- "Newer since the narrowing" is checked against the run's own versions. That covers everything since the narrowing and also a version sealed between dispatch and narrowing.
- The ceiling has a database default.
- The downgrade refuses only a ceiling below the cap.

## 2. Code diff (`f1ccddf..HEAD`, the package with 0007; the register is in section 4)

```diff
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index d8f4542..956b31d 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -59,7 +59,6 @@ def main(argv: list[str] | None = None) -> int:
                                              "and the run goes on (may cost money)")
     confirm.add_argument("run", type=int)
     confirm.add_argument("--by", required=True, help="the name of the person confirming")
-    confirm.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
     cancel = sub.add_parser("cancel", help="cancel a queued or waiting run")
     cancel.add_argument("run", type=int)
     cancel.add_argument("--by", required=True, help="the name of the person cancelling")
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index 885c2a3..6952c08 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -16,7 +16,8 @@ Step 9a (owner's approval of the step 9 plan, 2026-10-08; R1, R2, R3): a run who
 --by NAME` prints what the person confirms (`confirmation.render`) before anything is recorded, records the
 confirmation with exactly that text, and runs the rest, printing `show`'s output. One run per command, never in
 bulk. `cancel <run> --by NAME` cancels a queued or waiting run. `dispatch Q-… --again` dispatches a new run of a
-query whose earlier run ended. `--ceiling` is stored on the run at dispatch (R5).
+query whose earlier run ended. `--ceiling` is stored on the run at dispatch (R5), and only there: `confirm` takes none
+(fix round 1, finding 4); none given stores the per-run cap (owner, 2026-10-08).
 """
 from __future__ import annotations
 
@@ -43,9 +44,9 @@ def command(args, engine: Engine) -> int:
             reason = queries.cancel(engine, args.run, by=args.by)
             print(json.dumps({"run": args.run, "status": "failed", "failure": reason}, ensure_ascii=False))
             return 0
+        if args.command == "confirm":  # fix round 1, finding 4: no ceiling here; it is stored at dispatch
+            return _confirm(engine, args.run, args.by)
         ceiling = _ceiling(args.ceiling)
-        if args.command == "confirm":
-            return _confirm(engine, args.run, args.by, ceiling)
         if args.command == "run":
             q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
                                domain=args.domain, sufficiency=args.sufficiency)
@@ -124,8 +125,9 @@ def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
     return 0 if shown["status"] in ("completed", "failed", "waiting") else 1
 
 
-def _confirm(engine: Engine, run_id: int, by: str, ceiling: Decimal | None) -> int:
-    """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest."""
+def _confirm(engine: Engine, run_id: int, by: str) -> int:
+    """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest. The run's
+    ceiling is the one stored at dispatch (fix round 1, finding 4: a lower one given here would be lost on a restart)."""
     from hypocurate.access.guarded import GuardedRunError, run_guarded
     from hypocurate.pipeline import confirmation
     with engine.connect() as conn:
@@ -137,7 +139,7 @@ def _confirm(engine: Engine, run_id: int, by: str, ceiling: Decimal | None) -> i
     content, words = confirmation.show(engine, run_id)
     print(words, flush=True)
     confirmation.confirm(engine, run_id, by, shown=content)
-    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None, "phase": "proceed"}
+    payload = {"run_id": run_id, "ceiling": None, "phase": "proceed"}
     try:
         report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", payload, timeout=3600,
                              audit=(engine, run_id))
diff --git a/hypocurate/db/migrations/versions/0007_rules_confirmation.py b/hypocurate/db/migrations/versions/0007_rules_confirmation.py
index 19b79ea..7f0cfa7 100644
--- a/hypocurate/db/migrations/versions/0007_rules_confirmation.py
+++ b/hypocurate/db/migrations/versions/0007_rules_confirmation.py
@@ -17,8 +17,11 @@ run:
 - 0001's `hc_run_update` is replaced, with its body unchanged except the list of status changes, which gains
   running -> waiting, waiting -> waiting, waiting -> running and waiting -> failed. It is the only earlier
   function replaced; the downgrade restores 0001's text exactly.
-- `spending_ceiling` (R5): a lower ceiling than the per-run cap, stored at dispatch, positive and finite,
-  never changed (it joins what a run records at dispatch).
+- `spending_ceiling` (R5): the run's effective ceiling, stored at dispatch, positive and finite, never changed (it
+  joins what a run records at dispatch). The owner's decision (fix round 1): every new run stores one; none given is
+  the per-run cap ($2, the column's default), so the column is never empty for a run dispatched after 0007.
+- a failure reason 'cancelled: ...' only from queued or waiting (fix round 1, finding 5); other failures from running
+  stay allowed.
 rules_confirmation (Q1, A1, A2), append-only, one per run:
 - only for a waiting run; by a named person (1-200 characters); at the database's time;
 - the fingerprint of the plan that will be locked, in the plan fingerprint format;
@@ -26,6 +29,9 @@ rules_confirmation (Q1, A1, A2), append-only, one per run:
   proceed); a narrower question's names neither;
 - the source versions the narrowing counts were taken on (the run's own decision, or the original's for a
   narrower question) are exactly the run's versions;
+- no source the run uses has a newer sealed version than the run's, and no source was registered after the run's
+  dispatch (fix round 1, finding 2). It takes one advisory lock that registering a source and sealing a version take
+  too, so a registration and a confirmation cannot slip past each other;
 - the content shown (a JSON object) and the exact text shown (not empty).
 plan:
 - a plan for a run with a Planner stage (any attempt) or of a narrower question is locked only with that run's
@@ -41,7 +47,8 @@ Planner runs and narrower questions are refused at the lock (deliberately: no pl
 locked without a person); its fixed-plan runs are unaffected. The owner checks the live database for runs in
 progress before the deploy (R7).
 
-Downgrade refuses while a run is waiting, a confirmation exists or a ceiling is set, then drops what 0007
+Downgrade refuses while a run is waiting, a confirmation exists or a ceiling below the run cap is set (a ceiling
+equal to the cap says no more than the cap), then drops what 0007
 added and restores 0001's function and status rule.
 
 Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it
@@ -59,6 +66,14 @@ depends_on = None
 STATUSES_0001 = ('queued', 'running', 'completed', 'failed')
 STATUSES_0007 = ('queued', 'running', 'waiting', 'completed', 'failed')
 CONFIRMED_BY_MAX = 200
+# Fix round 1, finding 2: one transaction-scoped advisory lock taken by registering a source, by sealing a source
+# version and by a confirmation, so neither can slip past the other ("hcsrces"; tests check it equals
+# pipeline/confirmation.SOURCES_LOCK_KEY; single-bigint keys in use elsewhere: spend.MONTH_LOCK_KEY, migrate's lock).
+SOURCES_LOCK_KEY = 0x68637372636573
+# The owner's decision (2026-10-08): every new run stores its effective ceiling at dispatch; none given is the per-run
+# cap. The default (tests check it equals spend.RUN_CAP_USD) also covers a dispatch by the previous release's code.
+# It is set after the column is added, so runs dispatched before 0007 keep no ceiling.
+CEILING_DEFAULT = "2"
 
 TRANSITIONS_0001 = """(('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                              ('running', 'running'), ('running', 'completed'), ('running', 'failed'))"""
@@ -135,6 +150,11 @@ FUNCTIONS = [
         IF NEW.spending_ceiling IS DISTINCT FROM OLD.spending_ceiling THEN
             PERFORM hc_reject('what a run records at dispatch cannot change');
         END IF;
+        -- Fix round 1, finding 5: a cancel (a failure reason 'cancelled: ...') only from queued or waiting.
+        IF NEW.status = 'failed' AND OLD.status NOT IN ('queued', 'waiting')
+           AND NEW.failure_reason LIKE 'cancelled:%' THEN
+            PERFORM hc_reject('a run is cancelled only while it is queued or waiting');
+        END IF;
         IF OLD.status = 'running' AND NEW.status = 'waiting' THEN
             IF NOT {NEEDS_CONFIRMATION.format(run='NEW.id')} THEN
                 PERFORM hc_reject('only a run whose plan comes from the Planner or a narrower question waits');
@@ -173,6 +193,19 @@ FUNCTIONS = [
         IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'waiting' THEN
             PERFORM hc_reject('only a run waiting for confirmation is confirmed');
         END IF;
+        -- Fix round 1, finding 2: the registered sources as they are now, after any registration or seal in progress
+        -- has committed (the shared lock; each statement below reads with a new snapshot).
+        PERFORM pg_advisory_xact_lock(29382745069413747);  -- SOURCES_LOCK_KEY
+        IF EXISTS (SELECT 1 FROM run_source rs JOIN source_version sv ON sv.source_id = rs.source_id
+                   WHERE rs.run_id = NEW.run_id AND rs.source_version_id IS NOT NULL AND sv.sealed_at IS NOT NULL
+                     AND sv.id > rs.source_version_id) THEN
+            PERFORM hc_reject('a confirmation is refused: a source the run uses has a newer sealed version than the '
+                              'run''s (the narrowing no longer describes the registered sources)');
+        END IF;
+        IF EXISTS (SELECT 1 FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.run_id
+                                                             AND rs.source_id = s.id)) THEN
+            PERFORM hc_reject('a confirmation is refused: a source was registered after the run''s dispatch');
+        END IF;
         NEW.confirmed_at := now();
         SELECT h.narrower_of_run_id INTO original
         FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
@@ -230,8 +263,16 @@ FUNCTIONS = [
         RETURN NEW;
     END $$
     """,
+    # Fix round 1, finding 2: registering a source and sealing a version take the confirmation's lock.
+    f"""
+    CREATE FUNCTION hc_sources_lock() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        PERFORM pg_advisory_xact_lock({SOURCES_LOCK_KEY});
+        RETURN NEW;
+    END $$
+    """,
 ]
-FUNCTION_NAMES = ["hc_run_waiting()", "hc_rules_confirmation_insert()", "hc_plan_rules_confirmed()"]
+FUNCTION_NAMES = ["hc_run_waiting()", "hc_rules_confirmation_insert()", "hc_plan_rules_confirmed()", "hc_sources_lock()"]
 
 APPEND_ONLY = ["rules_confirmation"]
 # (table, event, trigger, function). Each trigger's name sorts after the earlier triggers on its table.
@@ -239,13 +280,19 @@ CHECKED = [
     ("run", "UPDATE", "hc_run_update_waiting", "hc_run_waiting"),
     ("rules_confirmation", "INSERT", "hc_rules_confirmation_insert", "hc_rules_confirmation_insert"),
     ("plan", "INSERT", "hc_plan_insert_rules_confirmed", "hc_plan_rules_confirmed"),
+    ("source", "INSERT", "hc_source_insert_sources_lock", "hc_sources_lock"),
+    ("source_version", "INSERT", "hc_source_version_insert_sources_lock", "hc_sources_lock"),
+    ("source_version", "UPDATE", "hc_source_version_update_sources_lock", "hc_sources_lock"),
 ]
+# Fix round 1, finding 2: a version takes the lock only when it is (or becomes) sealed; a new source always.
+WHEN = {"hc_source_version_insert_sources_lock": "WHEN (NEW.sealed_at IS NOT NULL) ",
+        "hc_source_version_update_sources_lock": "WHEN (OLD.sealed_at IS NULL AND NEW.sealed_at IS NOT NULL) "}
 TRIGGERS = (
     [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
      f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
     + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
        f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
-    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
+    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW {WHEN.get(t, '')}EXECUTE FUNCTION {f}()"
        for table, event, t, f in CHECKED]
 )
 
@@ -259,6 +306,7 @@ def upgrade() -> None:
     op.create_check_constraint(op.f('ck_run_status'), 'run', _in('status', STATUSES_0007))
     op.execute(RUN_UPDATE_0007)
     op.add_column('run', sa.Column('spending_ceiling', sa.Numeric(), nullable=True))
+    op.alter_column('run', 'spending_ceiling', server_default=sa.text(CEILING_DEFAULT))
     op.create_check_constraint(op.f('ck_run_spending_ceiling'), 'run',
                                "spending_ceiling IS NULL OR (spending_ceiling > 0 AND spending_ceiling < 'Infinity')")
     op.create_table(
@@ -293,12 +341,12 @@ def upgrade() -> None:
         op.execute(t)
 
 
-IN_USE = """
+IN_USE = f"""
     DO $$
     BEGIN
-        IF EXISTS (SELECT 1 FROM run WHERE status = 'waiting' OR spending_ceiling IS NOT NULL)
+        IF EXISTS (SELECT 1 FROM run WHERE status = 'waiting' OR spending_ceiling < {CEILING_DEFAULT})
            OR EXISTS (SELECT 1 FROM rules_confirmation) THEN
-            RAISE EXCEPTION 'hypocurate: migration 0007 is in use (a waiting run, a confirmation or a spending ceiling); not downgraded';
+            RAISE EXCEPTION 'hypocurate: migration 0007 is in use (a waiting run, a confirmation or a spending ceiling below the run cap); not downgraded';
         END IF;
     END $$
 """
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index b339ffe..cbfb137 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -351,7 +351,8 @@ class Run(Base):
     # Step 8b fix round 1 (migration 0006): the results statement's format version, recorded when the run completes.
     statement_format_version: Mapped[int | None] = mapped_column(SmallInteger)
     # Step 9a (0007; register 'spending_caps'): a lower ceiling than the per-run cap, stored at dispatch, never changed.
-    spending_ceiling: Mapped[Decimal | None] = mapped_column(Numeric)
+    # Fix round 1 (owner, 2026-10-08): none given is the per-run cap, the column's default (runs before 0007: empty).
+    spending_ceiling: Mapped[Decimal | None] = mapped_column(Numeric, server_default=sql("2"))
     failure_reason: Mapped[str | None] = mapped_column(Text)
     agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
     fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
index 43c52e4..bd6f346 100644
--- a/hypocurate/pipeline/confirmation.py
+++ b/hypocurate/pipeline/confirmation.py
@@ -35,6 +35,9 @@ from hypocurate.pipeline import reading
 from hypocurate.pipeline.queries import LOCK_TIMEOUT_MS, QueryRefused
 
 WAITING_FOR = "confirmation of the question as tested by a named person"
+# Fix round 1, finding 2: the lock that registering a source, sealing a version and a confirmation share (0007 holds
+# the same number); `confirm` takes it before its own check, so the check and the insert see the same sources.
+SOURCES_LOCK_KEY = 0x68637372636573
 SOURCES_CHANGED = ("sources_changed", "{changes} since this run's narrowing; cancel this run and dispatch the query "
                                       "again")
 PART_WORDS = {"alloy_class": "alloy class", "phase_class": "phase class", "test_type": "test type",
@@ -271,6 +274,7 @@ def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | Non
         if conn.execute(text("SELECT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = :r)"),
                         dict(r=run_id)).scalar_one():
             raise QueryRefused("already_confirmed", f"run {run_id} is already confirmed")
+        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=SOURCES_LOCK_KEY))
         changes = source_changes(conn, run_id)
         if changes:
             raise QueryRefused(SOURCES_CHANGED[0], SOURCES_CHANGED[1].format(changes="; ".join(changes)))
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
index c139a05..8bd6ebc 100644
--- a/hypocurate/pipeline/orchestrator.py
+++ b/hypocurate/pipeline/orchestrator.py
@@ -114,6 +114,35 @@ def _stored(engine: Engine, run_id: int, stage: str, done: bool = True):
                             dict(r=run_id, s=stage)).one_or_none()
 
 
+LEFT_RUNNING = "stage_left_running"  # an agent stage still running: step 9b's recovery closes it
+
+
+def _stage_code(row) -> str:
+    """The fixed code a stored agent stage ended with; LEFT_RUNNING for a stage still running."""
+    if row.status == "running":
+        return LEFT_RUNNING
+    return (row.output or {}).get("code") if isinstance(row.output, dict) else None
+
+
+def _agent_stop(engine: Engine, run_id: int, stage: str) -> str | None:
+    """Fix round 1, finding 1: the code of a stop the role's latest stored stage holds (a recording or reservation
+    failure, or a stage left running), whatever its status; None when there is no such stop."""
+    latest = _stored(engine, run_id, stage, done=False)
+    if latest is None or latest.status in ("done", "skipped"):
+        return None
+    code = _stage_code(latest)
+    return code if code in RUN_STOPS or code == LEFT_RUNNING else None
+
+
+def _critic_failures(engine: Engine, run_id: int) -> list:
+    """The codes of the Critic's stored stages that did not end done or skipped, in order (as `run_critic` reports
+    its batches' failures)."""
+    with engine.connect() as conn:
+        rows = conn.execute(text("SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = 'critic' "
+                                 "AND status NOT IN ('done', 'skipped') ORDER BY id"), dict(r=run_id)).all()
+    return [_stage_code(r) for r in rows]
+
+
 def _exists(engine: Engine, sql: str, run_id: int) -> bool:
     with engine.connect() as conn:
         return bool(conn.execute(text(f"SELECT EXISTS ({sql})"), dict(r=run_id)).scalar_one())
@@ -147,7 +176,16 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         decided = _stored(engine, run_id, "narrowing")
         report.narrower_question = queries.create_narrower(engine, run_id, decided.output["narrower_scope"]).number
         return _done(engine, report)
-    elif row.status != "running":  # waiting for a person, or ended: nothing to prepare
+    elif row.status != "running" and row.status != "waiting":  # ended: nothing to prepare
+        return _done(engine, report)
+    # Fix round 1, finding 3: a run already confirmed, or past its lock, goes on to `proceed` without waiting again.
+    if _exists(engine, "SELECT 1 FROM rules_confirmation WHERE run_id = :r UNION ALL SELECT 1 FROM plan WHERE run_id = :r",
+               run_id):
+        with engine.connect() as conn:
+            report.question_as_tested = reading.stored(conn, run_id)
+        report.ready = True
+        return _done(engine, report)
+    if row.status == "waiting":  # waiting for a person: not stuck, nothing to prepare
         return _done(engine, report)
     try:
         # A narrower question is recognised by its link to its original, never by the run's flag (fix round,
@@ -164,7 +202,12 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
             report.question_as_tested = reading.from_plan(confirmation.reference_plan(row), "fixed")
             report.ready = True
             return _done(engine, report)
-        stored = _stored(engine, run_id, "planner")
+        stored = _stored(engine, run_id, "planner", done=False)
+        if stored is not None and stored.status != "done":  # fix round 1, finding 1: an earlier stop stays a stop
+            code = _stage_code(stored)
+            if stored.status == "running" or code in RUN_STOPS:
+                return _stopped(engine, report, code)
+            return _failed(engine, report, "spending_refused" if code in SPENDING else "planner_failed", code)
         if stored is None:
             result = planner.run_planner(engine, run_id, **agent_kw)
             report.stages.append("planner")
@@ -188,6 +231,9 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if decision["result"] == "claim_not_one_plan":
             return _failed(engine, report, "claim_not_one_plan", decision["reason"])
         if decision["result"] == "partly_sufficient":
+            stop = _agent_stop(engine, run_id, "analyst")
+            if stop:
+                return _stopped(engine, report, stop)
             if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
                 if _explain(engine, report, agent_kw) in RUN_STOPS:
                     return _stopped(engine, report, report.explanation_failure)
@@ -231,12 +277,15 @@ def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'critic'", run_id):
             c = critic.run_critic(engine, run_id, **agent_kw)
             report.stages.append("critic")
-            stops = [f for f in c.failures if f in RUN_STOPS]
-            if stops:
-                return _stopped(engine, report, stops[0])
-            spent = [f for f in c.failures if f in SPENDING]
-            if spent:
-                return _failed(engine, report, "spending_refused", spent[0])
+            failures = c.failures
+        else:  # fix round 1, finding 1: the Critic's stored stages decide, as they did when it ran
+            failures = _critic_failures(engine, run_id)
+        stops = [f for f in failures if f in RUN_STOPS or f == LEFT_RUNNING]
+        if stops:
+            return _stopped(engine, report, stops[0])
+        spent = [f for f in failures if f in SPENDING]
+        if spent:
+            return _failed(engine, report, "spending_refused", spent[0])
         if _stored(engine, run_id, "inclusion") is None:
             inclusion.decide_run(engine, run_id)
         if _stored(engine, run_id, "dataset_freeze") is None and not _exists(
@@ -246,6 +295,9 @@ def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if _stored(engine, run_id, "statistics") is None:
             analysis.run_statistics(engine, run_id)
         report.stages += ["inclusion", "dataset freeze", "statistics"]
+        stop = _agent_stop(engine, run_id, "analyst")
+        if stop:
+            return _stopped(engine, report, stop)
         if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
             if _explain(engine, report, agent_kw) in RUN_STOPS:
                 return _stopped(engine, report, report.explanation_failure)
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
index b6ea7af..afdc0fb 100644
--- a/hypocurate/pipeline/queries.py
+++ b/hypocurate/pipeline/queries.py
@@ -182,6 +182,12 @@ def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, const
     return run_transaction(engine, body)
 
 
+def spend_cap() -> Decimal:
+    """The per-run cap, stored as the ceiling when none is given (owner, 2026-10-08: every run stores its ceiling)."""
+    from hypocurate.pipeline.agents.spend import RUN_CAP_USD
+    return RUN_CAP_USD
+
+
 def _new_run(conn: Connection, version_id: int, fixed_plan: bool, constructed_test_data: bool,
              ceiling: Decimal | None, setting_ids: Mapping[str, int]) -> int:
     """The queued run of a dispatched version, with everything a run records at dispatch."""
@@ -191,7 +197,8 @@ def _new_run(conn: Connection, version_id: int, fixed_plan: bool, constructed_te
     flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
     rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags, spending_ceiling) "
                             "VALUES (:v, :f, CAST(:x AS jsonb), :c) RETURNING id"),
-                       dict(v=version_id, f=fixed_plan or narrower, x=flags, c=ceiling)).scalar_one()
+                       dict(v=version_id, f=fixed_plan or narrower, x=flags,
+                            c=ceiling if ceiling is not None else spend_cap())).scalar_one()
     chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
                               dict(v=version_id)).scalars())
     for sid, key, latest in conn.execute(text(
```
## 3. Tests

### Tests added or changed in this round (diff)

```diff
diff --git a/tests/test_cli_step9a.py b/tests/test_cli_step9a.py
index d087757..a1ef7cf 100644
--- a/tests/test_cli_step9a.py
+++ b/tests/test_cli_step9a.py
@@ -120,3 +120,14 @@ def test_dispatch_without_again_still_names_the_reviewer(engine, capsys):
     queries.submit(engine, q.version_id)
     code, out, err = hc(capsys, "dispatch", q.number)
     assert code == 1 and "--by names the person confirming the domain" in err
+
+
+def test_confirm_takes_no_ceiling(engine, capsys):
+    """Fix round 1, finding 4: the ceiling is set only at dispatch (stored on the run); confirm has no --ceiling."""
+    import inspect
+    import pytest
+    from hypocurate import cli, cli_runs
+    with pytest.raises(SystemExit) as stopped:
+        cli.main(["confirm", "1", "--by", "Ada Reviewer", "--ceiling", "0.10"])
+    assert stopped.value.code == 2
+    assert list(inspect.signature(cli_runs._confirm).parameters) == ["engine", "run_id", "by"]
diff --git a/tests/test_confirmation.py b/tests/test_confirmation.py
index 8468931..1da16f6 100644
--- a/tests/test_confirmation.py
+++ b/tests/test_confirmation.py
@@ -349,3 +349,42 @@ def test_code_locks_only_the_confirmed_plan_and_says_so(engine, stub):
     report = proceed(engine, rid, stub)
     assert report.status == "failed" and report.failure == "refused: a checkpoint or write refused (not_confirmed)"
     assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+
+
+def test_confirm_waits_for_a_seal_in_progress_and_gives_its_own_reason(engine, stub):
+    """Fix round 1, finding 2: `confirm` takes the shared lock before its own source check, so a registration that
+    commits during the confirmation is seen by the check (code's reason, not the database's backstop)."""
+    import threading
+    import time
+    from sqlalchemy import create_engine
+    from model_builder import sha, version_fingerprint
+    rid = waiting(engine, stub)
+    sealer = create_engine(engine.url, connect_args={"options": "-c TimeZone=UTC"})
+    conn = sealer.connect()
+    tx = conn.begin()
+    src = conn.execute(text("SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = 'mpea'")).one()
+    v = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', '2026-10-08') "
+                          "RETURNING id"), dict(s=src.id)).scalar()
+    data = b"newer,data\n"
+    conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'x.csv', :h, :c)"),
+                 dict(v=v, h=sha(data), c=data))
+    conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
+                 dict(f=version_fingerprint({"x.csv": data}, src.source_type, src.data_kind, src.grouping_unit), v=v))
+    outcome = {}
+
+    def confirm_it():
+        try:
+            confirmation.confirm(engine, rid, by="Ada Reviewer")
+            outcome["code"] = "confirmed"
+        except queries.QueryRefused as refused:
+            outcome["code"] = refused.code
+
+    t = threading.Thread(target=confirm_it)
+    t.start()
+    time.sleep(1.0)
+    assert t.is_alive()  # waiting for the seal's lock
+    tx.commit()
+    t.join(10)
+    conn.close()
+    sealer.dispose()
+    assert outcome["code"] == "sources_changed"
diff --git a/tests/test_migrations_step9a.py b/tests/test_migrations_step9a.py
index f260e58..4ee6ac5 100644
--- a/tests/test_migrations_step9a.py
+++ b/tests/test_migrations_step9a.py
@@ -419,3 +419,196 @@ def test_a_run_has_at_most_one_narrower_question(w):
     w.hypothesis(narrower_of=original)
     with pytest.raises(IntegrityError, match="uq_hypothesis_narrower_of_run_id"):
         w.hypothesis(narrower_of=original)
+
+
+# --- fix round 1, finding 2: source freshness enforced by the database, serialised with registration -------------
+
+def seal_newer(w, key="mpea"):
+    v = w.new_version(key, label="newer")
+    w.add_file(v, f"{key}-newer.csv", f"{key},newer\n".encode())
+    w.seal(v)
+    return v
+
+
+@pytest.mark.parametrize("path", ["planner", "narrower"])
+@pytest.mark.parametrize("change", ["newer_version", "new_source"])
+def test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing(w, path, change):
+    """Direct SQL (the review's case): the run's own versions still match the narrowing, but the registered sources
+    no longer do."""
+    if path == "planner":
+        rid, planner, narrowed = planner_run(w)
+    else:
+        rid, planner, narrowed = narrower_run(w), None, None
+    wait(w, rid)
+    if change == "newer_version":
+        seal_newer(w)
+        match = "a source the run uses has a newer sealed version"
+    else:
+        w.add_source("later_source")
+        match = "a source was registered after the run's dispatch"
+    with pytest.raises(IntegrityError, match=match):
+        confirm(w, rid, planner, narrowed)
+    assert w.val("SELECT count(*) FROM rules_confirmation") == 0
+
+
+def test_a_newer_version_of_a_source_the_run_does_not_use_is_no_change(w):
+    """Guard (owner's wording: 'any source the run uses'): a newer version of a source the query did not choose does
+    not refuse the confirmation; the code's check (`confirmation.source_changes`) looks at chosen sources too."""
+    rid = w.running(sources=("mpea",))
+    planner = w.stage(rid, "planner", "planner")
+    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=planner)
+    narrowed = w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea",))})
+    wait(w, rid)
+    seal_newer(w, "tamu_fcc")
+    confirm(w, rid, planner, narrowed)
+    assert w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1
+
+
+def named_engine(db, name):
+    from sqlalchemy import create_engine
+    return create_engine(db.url, connect_args={"application_name": name, "options": "-c TimeZone=UTC"})
+
+
+def _blocked(engine, application_name):
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name = :a AND "
+                                 "wait_event_type = 'Lock'"), dict(a=application_name)).scalar() == 1
+
+
+def test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses(db):
+    """Two connections: a registration seals a newer version and has not committed; the confirmation waits for it
+    (the shared lock), then sees the new version and is refused."""
+    import threading
+    import time
+    w = World(db)
+    rid, planner, narrowed = planner_run(w)
+    wait(w, rid)
+    sealer = named_engine(db, "hc-test-sealer")
+    confirmer = named_engine(db, "hc-test-confirmer")
+    seal_conn = sealer.connect()
+    tx = seal_conn.begin()
+    v = seal_conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', "
+                               "'2026-10-08') RETURNING id"), dict(s=w.source["mpea"])).scalar()
+    from model_builder import sha, version_fingerprint
+    data = b"mpea,newer\n"
+    seal_conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'n.csv', :h, :c)"),
+                      dict(v=v, h=sha(data), c=data))
+    fp = version_fingerprint({"n.csv": data}, *w.settings(w.version["mpea"]))
+    seal_conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"), dict(f=fp, v=v))
+    outcome = {}
+
+    def confirm_it():
+        try:
+            with confirmer.begin() as conn:
+                conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, "
+                                  "planner_stage_result_id, narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', "
+                                  ":fp, :p, :n, '{}', 'x')"), dict(r=rid, fp=FP, p=planner, n=narrowed))
+            outcome["result"] = "confirmed"
+        except IntegrityError as error:
+            outcome["result"] = str(error.orig)
+
+    t = threading.Thread(target=confirm_it)
+    t.start()
+    deadline = time.time() + 10
+    while not _blocked(db, "hc-test-confirmer") and time.time() < deadline:
+        time.sleep(0.05)
+    assert _blocked(db, "hc-test-confirmer"), "the confirmation did not wait for the seal"
+    tx.commit()
+    t.join(10)
+    seal_conn.close()
+    sealer.dispose()
+    confirmer.dispose()
+    assert "a source the run uses has a newer sealed version" in outcome["result"]
+
+
+def test_a_confirmation_in_progress_holds_back_a_seal(db):
+    """The other order: the confirmation holds the shared lock until it commits; the seal waits, then succeeds."""
+    import threading
+    import time
+    w = World(db)
+    rid, planner, narrowed = planner_run(w)
+    wait(w, rid)
+    confirmer = named_engine(db, "hc-test-confirmer")
+    sealer = named_engine(db, "hc-test-sealer")
+    conf_conn = confirmer.connect()
+    tx = conf_conn.begin()
+    conf_conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
+                           "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, '{}', 'x')"),
+                      dict(r=rid, fp=FP, p=planner, n=narrowed))
+    v = w.new_version("mpea", label="newer")
+    w.add_file(v, "mpea-newer.csv", b"mpea,newer\n")
+    fp = w.fingerprint(v)
+    done = {}
+
+    def seal_it():
+        with sealer.begin() as conn:
+            conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
+                         dict(f=fp, v=v))
+        done["sealed"] = True
+
+    t = threading.Thread(target=seal_it)
+    t.start()
+    deadline = time.time() + 10
+    while not _blocked(db, "hc-test-sealer") and time.time() < deadline:
+        time.sleep(0.05)
+    assert _blocked(db, "hc-test-sealer"), "the seal did not wait for the confirmation"
+    tx.commit()
+    t.join(10)
+    conf_conn.close()
+    confirmer.dispose()
+    sealer.dispose()
+    assert done.get("sealed") and w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1
+
+
+def test_the_shared_lock_key_is_the_codes(engine):
+    from hypocurate.pipeline import confirmation
+    assert m0007().SOURCES_LOCK_KEY == confirmation.SOURCES_LOCK_KEY
+    insert = next(f for f in m0007().FUNCTIONS if "hc_rules_confirmation_insert()" in f)
+    lock = next(f for f in m0007().FUNCTIONS if "hc_sources_lock()" in f)
+    assert f"pg_advisory_xact_lock({confirmation.SOURCES_LOCK_KEY})" in insert
+    assert f"pg_advisory_xact_lock({confirmation.SOURCES_LOCK_KEY})" in lock
+
+
+# --- fix round 1, finding 5: a "cancelled" failure only from queued or waiting ----------------------------------
+
+@pytest.mark.parametrize("start, reason, allowed", [
+    ("running", "cancelled: cancelled by Ada before it started", False),
+    ("running", "cancelled:x", False),
+    ("running", "worker stopped", True),
+    ("queued", "cancelled: cancelled by Ada before it started", True),
+    ("waiting", "cancelled: cancelled by Ada while waiting for confirmation of the question as tested", True),
+])
+def test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting(w, start, reason, allowed):
+    """Direct SQL (the review's case): ordinary failures from running stay allowed."""
+    if start == "queued":
+        rid = w.run()
+    elif start == "running":
+        rid = w.running()
+    else:
+        rid, _, _ = planner_run(w)
+        wait(w, rid)
+    sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
+    if allowed:
+        w.run_sql(sql, f=reason, r=rid)
+        assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"
+    else:
+        w.rejected(sql, "a run is cancelled only while it is queued or waiting", f=reason, r=rid)
+
+
+# --- the owner's decision (2026-10-08): every new run stores its effective ceiling ---------------------------------
+
+def test_a_run_dispatched_without_a_ceiling_stores_the_run_cap(w):
+    """The database default (so a dispatch by the previous release's code stores it too) equals the code's cap."""
+    from hypocurate.pipeline.agents import spend
+    rid = w.run()
+    assert w.val("SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == spend.RUN_CAP_USD
+    assert m0007().CEILING_DEFAULT == str(spend.RUN_CAP_USD)
+
+
+def test_the_downgrade_is_not_blocked_by_ceilings_equal_to_the_run_cap(db):
+    """Only a ceiling below the run cap would be lost; one equal to it says no more than the cap."""
+    w = World(db)
+    w.run()
+    migrate.downgrade(db, "0006")
+    assert migrate.current_revision(db) == "0006"
+    migrate.upgrade(db)
diff --git a/tests/test_queries_step9a.py b/tests/test_queries_step9a.py
index 4f80639..0d055a5 100644
--- a/tests/test_queries_step9a.py
+++ b/tests/test_queries_step9a.py
@@ -124,7 +124,8 @@ def test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recor
                                 "FROM run WHERE id = :r"), dict(r=again)).one()
     assert (row.status, row.hypothesis_version_id, row.fixed_plan, row.experiment_flags) == (
         "queued", q.version_id, True, {})
-    assert row.spending_ceiling is None  # a ceiling is given with each dispatch, never inherited
+    # A ceiling is given with each dispatch, never inherited; none given stores the run cap (owner, 2026-10-08).
+    assert row.spending_ceiling == spend.RUN_CAP_USD
 
 
 @pytest.mark.parametrize("status", ["queued", "running", "waiting"])
@@ -270,3 +271,9 @@ def test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test(e
 def test_a_constructed_source_not_chosen_does_not_refuse_dispatch(engine):
     rid = queries.dispatch(engine, submitted(engine).version_id)
     assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
+
+
+def test_a_dispatch_without_a_ceiling_stores_the_run_cap(engine):
+    """The owner's decision (2026-10-08): every run stores its effective ceiling at dispatch; none given is the cap."""
+    rid = queries.dispatch(engine, submitted(engine).version_id)
+    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == spend.RUN_CAP_USD
diff --git a/tests/test_resume_step9a.py b/tests/test_resume_step9a.py
index 2660d24..8e5af56 100644
--- a/tests/test_resume_step9a.py
+++ b/tests/test_resume_step9a.py
@@ -5,6 +5,8 @@ the orchestrator does, and then calling `proceed` (or `prepare`) as a later proc
 made by killing the worker."""
 from __future__ import annotations
 
+import json
+
 import pytest
 from sqlalchemy import text
 
@@ -192,3 +194,174 @@ def test_a_run_whose_primary_set_is_empty_is_taken_up_after_inclusion_without_de
     report = orchestrator.proceed(engine, rid, **kw(stub))
     assert (report.status, report.outcome, report.failure) == ("completed", "insufficient", None)
     assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 1
+
+
+# --- fix round 1, finding 1: a resume respects an earlier stop (owner, 2026-10-08) ---------------------------------
+# Before deciding the next step the orchestrator reads the latest stored stage whatever its status. A spending failure
+# or any RUN_STOPS reason stays a stop after a resume. Interrupted stages and the one Planner repeat are step 9b's.
+
+def agent_stage(engine, rid, stage, status, code=None):
+    """An agent stage as the request path leaves it (direct SQL): failed with its fixed code, or still running."""
+    with engine.begin() as conn:
+        attempt = conn.execute(text("SELECT coalesce(max(attempt), 0) + 1 FROM stage_result WHERE run_id = :r AND "
+                                    "stage = :s"), dict(r=rid, s=stage)).scalar()
+        sid = conn.execute(text("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :s, :a) "
+                                "RETURNING id"), dict(r=rid, s=stage, a=attempt)).scalar()
+        if status != "running":
+            conn.execute(text("UPDATE stage_result SET status = :st, finished_at = now(), output = CAST(:o AS jsonb) "
+                              "WHERE id = :i"), dict(st=status, o=json.dumps({"code": code}), i=sid))
+    return sid
+
+
+def planner_run_running(engine, stub):
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    queries.start(engine, rid)
+    return rid
+
+
+def test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again(engine, stub, monkeypatch):
+    """The review's first case, through the real request path: the reservation cannot be written."""
+    from hypocurate.pipeline.agents import spend
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+
+    def broken(*a, **k):
+        raise RuntimeError("the database could not take the reservation")
+
+    monkeypatch.setattr(spend, "reserve", broken)
+    first = orchestrator.run(engine, rid, **kw(stub))
+    assert first.failure.startswith("reservation_failed:") and first.status == "running"
+    monkeypatch.undo()
+    again = orchestrator.run(engine, rid, **kw(stub))
+    assert again.failure.startswith("reservation_failed:") and again.status == "running"
+    assert len(stub.requests) == 0  # never sent, before or after the resume
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 1
+
+
+@pytest.mark.parametrize("code, failure", [("spending_cap_run", "spending_refused: "), ("ceiling_reached", "spending_refused: "),
+                                           ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
+                                           (None, "stage_left_running: ")])
+def test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated(engine, stub, code, failure):
+    rid = planner_run_running(engine, stub)
+    agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
+    report = orchestrator.run(engine, rid, **kw(stub))
+    assert report.failure.startswith(failure), report
+    assert len(stub.requests) == 0
+    stays_open = code in ("recording_failed", None)
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == ("running" if stays_open else "failed")
+
+
+def fixed_run_after_checks(engine, stub):
+    rid = fixed_run_to_lock(engine, stub)
+    extract.store_records(engine, rid)
+    checks.run_checks(engine, rid)
+    return rid
+
+
+@pytest.mark.parametrize("code, failure, status", [("reservation_failed", "reservation_failed: ", "running"),
+                                                   ("recording_failed", "recording_failed: ", "running"),
+                                                   ("spending_cap_run", "spending_refused: ", "failed"),
+                                                   (None, "stage_left_running: ", "running")])
+def test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst(engine, stub, code, failure,
+                                                                                         status):
+    rid = fixed_run_after_checks(engine, stub)
+    requests = len(stub.requests)
+    agent_stage(engine, rid, "critic", "running" if code is None else "failed", code)
+    report = orchestrator.run(engine, rid, **kw(stub))
+    assert report.failure.startswith(failure), report
+    assert len(stub.requests) == requests  # no Analyst request
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == status
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage IN ('inclusion', 'analyst')",
+               r=rid) == 0
+
+
+def test_an_ordinary_critic_failure_still_lets_the_run_go_on(engine, stub):
+    """Guard: a Critic batch that failed for its answer leaves its flags unclassified and the run goes on (8b)."""
+    rid = fixed_run_after_checks(engine, stub)
+    agent_stage(engine, rid, "critic", "failed", "malformed")
+    assert orchestrator.run(engine, rid, **kw(stub)).status == "completed"
+
+
+def fixed_run_after_statistics(engine, stub):
+    from hypocurate.pipeline import analysis
+    from hypocurate.pipeline.agents import critic
+    rid = fixed_run_after_checks(engine, stub)
+    critic.run_critic(engine, rid, **kw(stub))
+    inclusion.decide_run(engine, rid)
+    checkpoints.freeze_dataset(engine, rid)
+    analysis.run_statistics(engine, rid)
+    return rid
+
+
+@pytest.mark.parametrize("code", ["recording_failed", "reservation_failed", None])
+def test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed(engine, stub, code):
+    rid = fixed_run_after_statistics(engine, stub)
+    requests = len(stub.requests)
+    agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
+    report = orchestrator.run(engine, rid, **kw(stub))
+    assert report.failure and report.status == "running", report
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    assert len(stub.requests) == requests
+
+
+@pytest.mark.parametrize("code", ["spending_cap_run", "wording_refused"])
+def test_an_ordinary_or_spending_analyst_failure_still_completes_with_codes_decision(engine, stub, code):
+    """Guard (A3, B2): any Analyst failure but an accounting one leaves code's decision standing."""
+    rid = fixed_run_after_statistics(engine, stub)
+    agent_stage(engine, rid, "analyst", "failed", code)
+    assert orchestrator.run(engine, rid, **kw(stub)).status == "completed"
+
+
+@pytest.mark.parametrize("code", ["recording_failed", None])
+def test_a_partly_sufficient_originals_analyst_accounting_failure_stops_before_the_copy(engine, stub, code):
+    from hypocurate.pipeline import narrowing
+    from hypocurate.pipeline.agents import planner
+    stub.respond(to.responder(to.PARTLY))
+    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
+    queries.start(engine, rid)
+    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, **kw(stub)).answer)
+    requests = len(stub.requests)
+    agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
+    report = orchestrator.run(engine, rid, **kw(stub))
+    assert report.failure and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
+    assert len(stub.requests) == requests
+
+
+# --- fix round 1, finding 3: a confirmed run is taken up through run() without waiting again ------------------------
+
+def confirmed_run_stopped(engine, stub, kind, stop):
+    """A Planner run or a narrower question's run, confirmed, then stopped: still waiting (confirmed), running again
+    before the rules lock, or after it."""
+    if kind == "planner":
+        stub.respond(to.responder(to.planner_body()))
+        rid = to.dispatched(engine)
+    else:
+        stub.respond(to.responder(to.PARTLY))
+        original = to.dispatched(engine, claim=to.PARTLY_CLAIM)
+        number = orchestrator.run(engine, original, **kw(stub)).narrower_question
+        vid = queries.submitted_version(engine, number)
+        queries.confirm_domain(engine, vid, by="Ada Reviewer")
+        rid = queries.dispatch(engine, vid)
+    assert orchestrator.run(engine, rid, **kw(stub)).status == "waiting"
+    confirmation.confirm(engine, rid, by="Ada Reviewer")
+    if stop in ("before_lock", "after_lock"):
+        orchestrator._go_on(engine, rid)
+    if stop == "after_lock":
+        with engine.connect() as conn:
+            checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
+    return rid
+
+
+@pytest.mark.parametrize("kind", ["planner", "narrower"])
+@pytest.mark.parametrize("stop", ["confirmed_waiting", "before_lock", "after_lock"])
+def test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run(engine, stub, kind, stop):
+    rid = confirmed_run_stopped(engine, stub, kind, stop)
+    planner_requests = sum("[[ ## plan ## ]]" in r["raw"].decode() for r in stub.requests)
+    report = orchestrator.run(engine, rid, **kw(stub))
+    assert (report.status, report.outcome, report.failure) == ("completed", "sufficient", None), report
+    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
+    assert one(engine, "SELECT fingerprint FROM plan WHERE run_id = :r", r=rid) == \
+        one(engine, "SELECT plan_fingerprint FROM rules_confirmation WHERE run_id = :r", r=rid)
+    assert sum("[[ ## plan ## ]]" in r["raw"].decode() for r in stub.requests) == planner_requests  # no Planner again
```

### Changed expectations (reasons)

- `test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded`: the new run's ceiling is the run cap (was asserted empty). Reason: the owner's decision.
- No other existing assertion changed. A test written in this round, and changed before the fix, now checks the owner's wording: a newer version of a source the run does not use is no change (`test_a_newer_version_of_a_source_the_run_does_not_use_is_no_change`, a guard).

### The tests of this round on the reviewed code (`f1ccddf`'s package, scratch copy, `PYTHONPATH`)

The selection also picked up earlier resume tests, which pass there. The new tests that pass there are guards by design: an ordinary Critic or Analyst failure, a newer version of an unused source, the allowed failures, and the downgrade at the cap.

```
_ test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again _
    def test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again(engine, stub, monkeypatch):
        assert first.failure.startswith("reservation_failed:") and first.status == "running"
>       assert again.failure.startswith("reservation_failed:") and again.status == "running"
ERROR    hypocurate.pipeline:lm.py:100 {"agent_request_failure": "reservation_failed", "exception_types": ["RuntimeError"], "raised_at": ["/home/codespace/hc-work/step09a/prefix/hypocurate/pipeline/agents/lm.py:129 complete", "/workspaces/hypocurate/tests/test_resume_step9a.py:230 broken"]}
                                               ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
        agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
                                               ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
        agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
_ test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[malformed-planner_failed: ] _
failure = 'planner_failed: '
                                               ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
        agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
_ test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[recording_failed-recording_failed: ] _
code = 'recording_failed', failure = 'recording_failed: '
                                               ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
        agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
                                               ("malformed", "planner_failed: "), ("recording_failed", "recording_failed: "),
        agent_stage(engine, rid, "planner", "running" if code is None else "failed", code)
E       AssertionError: RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...of the claim; not verified by code and, in this version, not confirmed by a person", 'source': 'planner'}, ready=False)
E        +      where 'refused: a checkpoint or write refused (rejected_by_database)' = RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...of the claim; not verified by code and, in this version, not confirmed by a person", 'source': 'planner'}, ready=False).failure
_ test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[reservation_failed-reservation_failed: -running] _
code = 'reservation_failed', failure = 'reservation_failed: '
    @pytest.mark.parametrize("code, failure, status", [("reservation_failed", "reservation_failed: ", "running"),
                                                       ("recording_failed", "recording_failed: ", "running"),
                                                       ("spending_cap_run", "spending_refused: ", "failed"),
        agent_stage(engine, rid, "critic", "running" if code is None else "failed", code)
_ test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[recording_failed-recording_failed: -running] _
code = 'recording_failed', failure = 'recording_failed: ', status = 'running'
    @pytest.mark.parametrize("code, failure, status", [("reservation_failed", "reservation_failed: ", "running"),
                                                       ("recording_failed", "recording_failed: ", "running"),
                                                       ("spending_cap_run", "spending_refused: ", "failed"),
        agent_stage(engine, rid, "critic", "running" if code is None else "failed", code)
_ test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[spending_cap_run-spending_refused: -failed] _
code = 'spending_cap_run', failure = 'spending_refused: ', status = 'failed'
    @pytest.mark.parametrize("code, failure, status", [("reservation_failed", "reservation_failed: ", "running"),
                                                       ("recording_failed", "recording_failed: ", "running"),
                                                       ("spending_cap_run", "spending_refused: ", "failed"),
        agent_stage(engine, rid, "critic", "running" if code is None else "failed", code)
    @pytest.mark.parametrize("code, failure, status", [("reservation_failed", "reservation_failed: ", "running"),
                                                       ("recording_failed", "recording_failed: ", "running"),
                                                       ("spending_cap_run", "spending_refused: ", "failed"),
        agent_stage(engine, rid, "critic", "running" if code is None else "failed", code)
E       AssertionError: RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...rain size below 0.1 µm', 'label': 'the fixed reference plan; not read from the claim', 'source': 'fixed'}, ready=False)
E        +      where 'refused: a checkpoint or write refused (rejected_by_database)' = RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...rain size below 0.1 µm', 'label': 'the fixed reference plan; not read from the claim', 'source': 'fixed'}, ready=False).failure
_ test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed[recording_failed] _
code = 'recording_failed'
    @pytest.mark.parametrize("code", ["recording_failed", "reservation_failed", None])
        agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
_ test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed[reservation_failed] _
code = 'reservation_failed'
    @pytest.mark.parametrize("code", ["recording_failed", "reservation_failed", None])
        agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
    @pytest.mark.parametrize("code", ["recording_failed", "reservation_failed", None])
        agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
E       AssertionError: RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...rain size below 0.1 µm', 'label': 'the fixed reference plan; not read from the claim', 'source': 'fixed'}, ready=False)
E       assert ('refused: a checkpoint or write refused (rejected_by_database)' and 'failed' == 'running'
E        +  where 'refused: a checkpoint or write refused (rejected_by_database)' = RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...rain size below 0.1 µm', 'label': 'the fixed reference plan; not read from the claim', 'source': 'fixed'}, ready=False).failure
E         + failed)
_ test_a_partly_sufficient_originals_analyst_accounting_failure_stops_before_the_copy[recording_failed] _
code = 'recording_failed'
    @pytest.mark.parametrize("code", ["recording_failed", None])
        agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
    @pytest.mark.parametrize("code", ["recording_failed", None])
        agent_stage(engine, rid, "analyst", "running" if code is None else "failed", code)
E       assert ('refused: a checkpoint or write refused (rejected_by_database)' and 'failed' == 'running'
E        +  where 'refused: a checkpoint or write refused (rejected_by_database)' = RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...of the claim; not verified by code and, in this version, not confirmed by a person", 'source': 'planner'}, ready=False).failure
E         + failed)
E       AssertionError: RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...of the claim; not verified by code and, in this version, not confirmed by a person", 'source': 'planner'}, ready=False)
E       assert ('failed', No...by_database)') == ('completed',...icient', None)
E         At index 0 diff: 'failed' != 'completed'
E       AssertionError: RunReport(run_id=2, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa... 'label': "the narrower plan stored by the original question's narrowing decision", 'source': 'narrower'}, ready=False)
E       assert ('failed', No...by_database)') == ('completed',...icient', None)
E         At index 0 diff: 'failed' != 'completed'
E       AssertionError: RunReport(run_id=1, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa...of the claim; not verified by code and, in this version, not confirmed by a person", 'source': 'planner'}, ready=False)
E       assert ('failed', No...by_database)') == ('completed',...icient', None)
E         At index 0 diff: 'failed' != 'completed'
E       AssertionError: RunReport(run_id=2, status='failed', outcome=None, failure='refused: a checkpoint or write refused (rejected_by_databa... 'label': "the narrower plan stored by the original question's narrowing decision", 'source': 'narrower'}, ready=False)
E       assert ('failed', No...by_database)') == ('completed',...icient', None)
E         At index 0 diff: 'failed' != 'completed'
        sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
            assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"
sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
        sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
            assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"
sql = "UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"
_ test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded _
    def test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded(engine):
        set_status(engine, first, "failed")
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_lock]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[between_sources]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_checks]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_critic]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_inclusion]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_freeze]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_statistics]
PASSED tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results[after_analyst]
PASSED tests/test_resume_step9a.py::test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question
PASSED tests/test_resume_step9a.py::test_a_narrower_question_left_as_a_draft_by_a_stop_is_submitted
PASSED tests/test_resume_step9a.py::test_an_ordinary_critic_failure_still_lets_the_run_go_on
PASSED tests/test_resume_step9a.py::test_an_ordinary_or_spending_analyst_failure_still_completes_with_codes_decision[spending_cap_run]
PASSED tests/test_resume_step9a.py::test_an_ordinary_or_spending_analyst_failure_still_completes_with_codes_decision[wording_refused]
PASSED tests/test_migrations_step9a.py::test_a_newer_version_of_a_source_the_run_does_not_use_is_no_change
PASSED tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting[running-worker stopped-True]
PASSED tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting[queued-cancelled: cancelled by Ada before it started-True]
PASSED tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting[waiting-cancelled: cancelled by Ada while waiting for confirmation of the question as tested-True]
PASSED tests/test_migrations_step9a.py::test_the_downgrade_is_not_blocked_by_ceilings_equal_to_the_run_cap
PASSED tests/test_queries_step9a.py::test_without_a_ceiling_the_run_cap_holds
FAILED tests/test_resume_step9a.py::test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again
FAILED tests/test_resume_step9a.py::test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[spending_cap_run-spending_refused: ]
FAILED tests/test_resume_step9a.py::test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[ceiling_reached-spending_refused: ]
FAILED tests/test_resume_step9a.py::test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[malformed-planner_failed: ]
FAILED tests/test_resume_step9a.py::test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[recording_failed-recording_failed: ]
FAILED tests/test_resume_step9a.py::test_a_stored_planner_failure_is_replayed_and_the_planner_is_never_repeated[None-stage_left_running: ]
FAILED tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[reservation_failed-reservation_failed: -running]
FAILED tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[recording_failed-recording_failed: -running]
FAILED tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[spending_cap_run-spending_refused: -failed]
FAILED tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst[None-stage_left_running: -running]
FAILED tests/test_resume_step9a.py::test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed[recording_failed]
FAILED tests/test_resume_step9a.py::test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed[reservation_failed]
FAILED tests/test_resume_step9a.py::test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed[None]
FAILED tests/test_resume_step9a.py::test_a_partly_sufficient_originals_analyst_accounting_failure_stops_before_the_copy[recording_failed]
FAILED tests/test_resume_step9a.py::test_a_partly_sufficient_originals_analyst_accounting_failure_stops_before_the_copy[None]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[confirmed_waiting-planner]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[confirmed_waiting-narrower]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[before_lock-planner]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[before_lock-narrower]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[after_lock-planner]
FAILED tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run[after_lock-narrower]
FAILED tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing[newer_version-planner]
FAILED tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing[newer_version-narrower]
FAILED tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing[new_source-planner]
FAILED tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing[new_source-narrower]
FAILED tests/test_migrations_step9a.py::test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses
FAILED tests/test_migrations_step9a.py::test_a_confirmation_in_progress_holds_back_a_seal
FAILED tests/test_migrations_step9a.py::test_the_shared_lock_key_is_the_codes
FAILED tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting[running-cancelled: cancelled by Ada before it started-False]
FAILED tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting[running-cancelled:x-False]
FAILED tests/test_migrations_step9a.py::test_a_run_dispatched_without_a_ceiling_stores_the_run_cap
FAILED tests/test_confirmation.py::test_confirm_waits_for_a_seal_in_progress_and_gives_its_own_reason
FAILED tests/test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded
FAILED tests/test_queries_step9a.py::test_a_dispatch_without_a_ceiling_stores_the_run_cap
FAILED tests/test_cli_step9a.py::test_confirm_takes_no_ceiling - Failed: DID ...
35 failed, 19 passed, 83 deselected in 201.27s (0:03:21)
```
## 4. The register (143 entries; 5 changed in this round)

`resumable_run`, `rules_confirmation` and `run_cancel` are new on this unmerged branch, so they are corrected in place. Their reviewed wording is shown here. `run_order_and_failures` and `spending_caps` keep main's wording in their history.

### `spending_caps`

Before (`f1ccddf`):

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one stored on the run at dispatch, which holds after a crash or a restart), is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. The monthly cap counts the calls recorded in this database only. At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
 "value": {
  "text": "$2 per run; $2 per curation; $50 per month",
  "unit": "USD"
 },
 "category": "operational",
 "affects": "Whether a run or a model call may proceed.",
 "reason": "CLAUDE.md, rule 12.",
 "evidence": [
  "CLAUDE.md, rule 12; step 3 summary, 'Step 9 requirements'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.spend:RUN_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:CURATION_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:MONTH_CAP_USD",
    "equals": 50
   },
   {
    "ref": "sql:ck_run_spending_ceiling"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Model calls may cost at most $2 per run and $50 per calendar month (UTC), counting calls without a reported cost at their upper bound.",
   "from": "2026-10-04",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): the per-curation cap and the enforcement before each request."
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction (the run's lock for a run call, then one month-wide advisory lock) that records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. The monthly cap counts the calls recorded in this database only.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a registration call read its curation total before taking the month-wide lock, so two concurrent reservations could both pass the curation cap or a lower ceiling (ChatGPT's review of step 8a, finding 3). Fixed 2026-10-07."
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. The monthly cap counts the calls recorded in this database only.",
   "from": "2026-10-07",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08, R5): the ceiling stored on the run; the monthly cap also blocks dispatch."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_agent_core.py::test_the_run_cap_refuses_a_request_before_it_is_sent",
  "tests/test_agent_core.py::test_the_curation_cap_and_a_ceiling_refuse_before_sending",
  "tests/test_agent_core.py::test_the_month_cap_counts_every_call_including_unconfirmed_ones",
  "tests/test_agent_core.py::test_two_reservations_cannot_both_pass_the_month_cap",
  "tests/test_agent_core.py::test_a_reservation_waits_for_the_month_wide_lock",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling",
  "tests/test_agent_core.py::test_two_reservations_on_one_run_cannot_both_pass_the_run_cap",
  "tests/test_queries_step9a.py::test_the_stored_ceiling_holds_when_the_caller_names_none",
  "tests/test_queries_step9a.py::test_the_lower_of_the_stored_and_the_given_ceiling_holds"
 ]
}
```

Now:

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one stored on the run at dispatch, which holds after a crash or a restart), is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. Every run dispatched after migration 0007 stores its ceiling: the one given at dispatch, or else the per-run cap (the owner's decision, 2026-10-08; the column's default). The ceiling is set only at dispatch; `confirm` takes none. The monthly cap counts the calls recorded in this database only. At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
 "value": {
  "text": "$2 per run; $2 per curation; $50 per month",
  "unit": "USD"
 },
 "category": "operational",
 "affects": "Whether a run or a model call may proceed.",
 "reason": "CLAUDE.md, rule 12.",
 "evidence": [
  "CLAUDE.md, rule 12; step 3 summary, 'Step 9 requirements'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.spend:RUN_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:CURATION_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:MONTH_CAP_USD",
    "equals": 50
   },
   {
    "ref": "sql:ck_run_spending_ceiling"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:spend_cap"
   },
   {
    "ref": "sql:CEILING_DEFAULT"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Model calls may cost at most $2 per run and $50 per calendar month (UTC), counting calls without a reported cost at their upper bound.",
   "from": "2026-10-04",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): the per-curation cap and the enforcement before each request."
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction (the run's lock for a run call, then one month-wide advisory lock) that records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. The monthly cap counts the calls recorded in this database only.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a registration call read its curation total before taking the month-wide lock, so two concurrent reservations could both pass the curation cap or a lower ceiling (ChatGPT's review of step 8a, finding 3). Fixed 2026-10-07."
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. The monthly cap counts the calls recorded in this database only.",
   "from": "2026-10-07",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08, R5): the ceiling stored on the run; the monthly cap also blocks dispatch."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_agent_core.py::test_the_run_cap_refuses_a_request_before_it_is_sent",
  "tests/test_agent_core.py::test_the_curation_cap_and_a_ceiling_refuse_before_sending",
  "tests/test_agent_core.py::test_the_month_cap_counts_every_call_including_unconfirmed_ones",
  "tests/test_agent_core.py::test_two_reservations_cannot_both_pass_the_month_cap",
  "tests/test_agent_core.py::test_a_reservation_waits_for_the_month_wide_lock",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling",
  "tests/test_agent_core.py::test_two_reservations_on_one_run_cannot_both_pass_the_run_cap",
  "tests/test_queries_step9a.py::test_the_stored_ceiling_holds_when_the_caller_names_none",
  "tests/test_queries_step9a.py::test_the_lower_of_the_stored_and_the_given_ceiling_holds",
  "tests/test_queries_step9a.py::test_a_dispatch_without_a_ceiling_stores_the_run_cap",
  "tests/test_migrations_step9a.py::test_a_run_dispatched_without_a_ceiling_stores_the_run_cap",
  "tests/test_cli_step9a.py::test_confirm_takes_no_ceiling"
 ]
}
```
### `run_order_and_failures`

Before (`f1ccddf`):

```json
{
 "key": "run_order_and_failures",
 "name": "The run order and what a failure does to a run",
 "state": "in_force",
 "statement": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or, after a named person's confirmation of the question as tested (the run waits for it; step 9a), the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan), which also waits for the confirmation. A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9b's recovery. No model call runs inside a database transaction.",
 "value": {
  "text": "the step 8b run order and failure table",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run's stages and endings (PRD 3, 8, 14.4).",
 "reason": "The step 8 plan's run order, corrected by the owner (A1); the failure table approved with the plan.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers A1, A3, A11, B1, B2.",
  "Step 8b second-model review, findings 1 and 3 (docs/reviews/step08b_review_chatgpt.md)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.orchestrator:run"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:REASONS"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:RUN_STOPS",
    "equals": [
     "recording_failed",
     "reservation_failed"
    ]
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_orchestrator.py::test_14_1a_the_fixed_plan_run_reproduces_the_reference_and_repeats_identically",
  "tests/test_orchestrator.py::test_14_1b_the_planners_plan_is_locked_and_the_run_completes",
  "tests/test_orchestrator.py::test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_planner_fails_the_run",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_critic_fails_the_run",
  "tests/test_orchestrator.py::test_no_model_call_is_made_while_a_database_transaction_is_open",
  "tests/test_orchestrator_flagged.py::test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_critic_stops_the_run_with_no_further_request",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_analyst_stops_the_run_before_completion",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question"
 ],
 "history": [
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a, or a narrower question's stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A call whose recording failed stays open, so the run stays running until step 9's recovery. No model call runs inside a database transaction.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (ChatGPT review, findings 1 and 3): a narrower question is recognised by its link; recording and reservation failures stop the run with no further request."
  },
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9's recovery. No model call runs inside a database transaction.",
   "from": "2026-10-07",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08, Q1 and Q5): the wait for a person's confirmation before the lock."
  }
 ]
}
```

Now:

```json
{
 "key": "run_order_and_failures",
 "name": "The run order and what a failure does to a run",
 "state": "in_force",
 "statement": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or, after a named person's confirmation of the question as tested (the run waits for it; step 9a), the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan), which also waits for the confirmation. A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9b's recovery. Taken up again, the run reads each agent's latest stored stage whatever its status, so such a stop, a stage left running or a stored spending refusal has the same effect as when it happened (register 'resumable_run'). No model call runs inside a database transaction.",
 "value": {
  "text": "the step 8b run order and failure table",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run's stages and endings (PRD 3, 8, 14.4).",
 "reason": "The step 8 plan's run order, corrected by the owner (A1); the failure table approved with the plan.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers A1, A3, A11, B1, B2.",
  "Step 8b second-model review, findings 1 and 3 (docs/reviews/step08b_review_chatgpt.md)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.orchestrator:run"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:REASONS"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:RUN_STOPS",
    "equals": [
     "recording_failed",
     "reservation_failed"
    ]
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_orchestrator.py::test_14_1a_the_fixed_plan_run_reproduces_the_reference_and_repeats_identically",
  "tests/test_orchestrator.py::test_14_1b_the_planners_plan_is_locked_and_the_run_completes",
  "tests/test_orchestrator.py::test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_planner_fails_the_run",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_critic_fails_the_run",
  "tests/test_orchestrator.py::test_no_model_call_is_made_while_a_database_transaction_is_open",
  "tests/test_orchestrator_flagged.py::test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_critic_stops_the_run_with_no_further_request",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_analyst_stops_the_run_before_completion",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question"
 ],
 "history": [
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a, or a narrower question's stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A call whose recording failed stays open, so the run stays running until step 9's recovery. No model call runs inside a database transaction.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (ChatGPT review, findings 1 and 3): a narrower question is recognised by its link; recording and reservation failures stop the run with no further request."
  },
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9's recovery. No model call runs inside a database transaction.",
   "from": "2026-10-07",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08, Q1 and Q5): the wait for a person's confirmation before the lock."
  }
 ]
}
```
### `rules_confirmation`

Before (`f1ccddf`):

```json
{
 "key": "rules_confirmation",
 "name": "The run waits at the rules lock for a named person",
 "state": "in_force",
 "statement": "A run whose plan comes from a model's answer waits before its rules lock, with status 'waiting', until a named person confirms the question as tested: a run with a Planner stage (after code's narrowing decision to proceed), and a narrower question's run (its outcome and exclusion rules come from its original's Planner answer). A fixed-plan run of an ordinary question (criterion 14.1a) never waits. Before anything is recorded the person is shown, from stored rows only: the original question, the question as tested, what was narrowed and why, each scope part marked stated or assumed, the outcome, the exclusion rules, the sufficiency option, the fingerprint of the plan to be locked, the source versions and the cost so far; the confirmation stores that content and the exact text shown. A confirmation is for one run and one named person (no bulk or automatic confirmation in step 9). It is refused when a chosen source has a newer sealed version, or a source was registered, since dispatch (the run's own versions never change); nothing is redone. The database refuses a plan from a model's answer unless its fingerprint is the confirmed one, and refuses every write to a waiting run; the dataset freeze stays automatic. Scoping: the database recognises a run that must wait by a Planner stage (any attempt) or a narrower link, so a run with no Planner stage and no narrower link (the test worlds of steps 6-8 that lock a plan directly) is not held to it; the orchestrator builds a Planner plan only from a stored Planner stage.",
 "value": {
  "text": "waits at the rules lock; one named person per run",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run whose plan comes from the Planner or a narrower question (PRD 3, 5.6, 9.4).",
 "reason": "The second-model review of step 8b found claim interpretation unchecked; the owner chose a person's confirmation at the rules lock (Q1), for every plan built from a model's answer (Q5), bound to the plan locked and to the source versions the narrowing counted (A1), showing everything the plan rests on (A2).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.confirmation:WAITING_FOR",
    "equals": "confirmation of the question as tested by a named person"
   },
   {
    "ref": "python:hypocurate.db.models:CONFIRMED_BY_MAX",
    "equals": 200
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:SOURCES_CHANGED"
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:plan_to_lock"
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:render"
   },
   {
    "ref": "sql:hc_plan_rules_confirmed"
   },
   {
    "ref": "sql:hc_rules_confirmation_insert"
   },
   {
    "ref": "sql:hc_run_waiting"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_confirmation.py::test_a_planner_run_waits_before_its_rules_lock_and_nothing_more_is_done",
  "tests/test_confirmation.py::test_confirm_shows_every_item_and_stores_exactly_the_text_shown",
  "tests/test_confirmation.py::test_a_newer_version_registered_while_the_run_waits_refuses_the_confirmation",
  "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself",
  "tests/test_migrations_step9a.py::test_a_planner_runs_plan_must_be_the_confirmed_plan",
  "tests/test_migrations_step9a.py::test_a_confirmation_is_refused_when_the_counted_source_versions_are_not_the_runs",
  "tests/test_migrations_step9a.py::test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation"
 ],
 "history": [],
 "notes": [
  "Step 11 decides how the evaluation runs are confirmed (owner, 2026-10-08). The website's Confirm button is step 10."
 ]
}
```

Now:

```json
{
 "key": "rules_confirmation",
 "name": "The run waits at the rules lock for a named person",
 "state": "in_force",
 "statement": "A run whose plan comes from a model's answer waits before its rules lock, with status 'waiting', until a named person confirms the question as tested: a run with a Planner stage (after code's narrowing decision to proceed), and a narrower question's run (its outcome and exclusion rules come from its original's Planner answer). A fixed-plan run of an ordinary question (criterion 14.1a) never waits. Before anything is recorded the person is shown, from stored rows only: the original question, the question as tested, what was narrowed and why, each scope part marked stated or assumed, the outcome, the exclusion rules, the sufficiency option, the fingerprint of the plan to be locked, the source versions and the cost so far; the confirmation stores that content and the exact text shown. A confirmation is for one run and one named person (no bulk or automatic confirmation in step 9). It is refused when a source the run uses has a newer sealed version than the run's, or a source was registered after the run's dispatch (the run's own versions never change); nothing is redone. The database enforces this too: the confirmation takes one advisory lock that registering a source and sealing a version also take, then checks the registered sources, so a registration and a confirmation cannot slip past each other (fix round 1, finding 2). A run already confirmed is never made to wait again. The database refuses a plan from a model's answer unless its fingerprint is the confirmed one, and refuses every write to a waiting run; the dataset freeze stays automatic. Scoping: the database recognises a run that must wait by a Planner stage (any attempt) or a narrower link, so a run with no Planner stage and no narrower link (the test worlds of steps 6-8 that lock a plan directly) is not held to it; the orchestrator builds a Planner plan only from a stored Planner stage.",
 "value": {
  "text": "waits at the rules lock; one named person per run",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run whose plan comes from the Planner or a narrower question (PRD 3, 5.6, 9.4).",
 "reason": "The second-model review of step 8b found claim interpretation unchecked; the owner chose a person's confirmation at the rules lock (Q1), for every plan built from a model's answer (Q5), bound to the plan locked and to the source versions the narrowing counted (A1), showing everything the plan rests on (A2).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.confirmation:WAITING_FOR",
    "equals": "confirmation of the question as tested by a named person"
   },
   {
    "ref": "python:hypocurate.db.models:CONFIRMED_BY_MAX",
    "equals": 200
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:SOURCES_CHANGED"
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:plan_to_lock"
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:render"
   },
   {
    "ref": "sql:hc_plan_rules_confirmed"
   },
   {
    "ref": "sql:hc_rules_confirmation_insert"
   },
   {
    "ref": "sql:hc_run_waiting"
   },
   {
    "ref": "python:hypocurate.pipeline.confirmation:SOURCES_LOCK_KEY",
    "equals": 29382745069413747
   },
   {
    "ref": "sql:hc_sources_lock"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_confirmation.py::test_a_planner_run_waits_before_its_rules_lock_and_nothing_more_is_done",
  "tests/test_confirmation.py::test_confirm_shows_every_item_and_stores_exactly_the_text_shown",
  "tests/test_confirmation.py::test_a_newer_version_registered_while_the_run_waits_refuses_the_confirmation",
  "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself",
  "tests/test_migrations_step9a.py::test_a_planner_runs_plan_must_be_the_confirmed_plan",
  "tests/test_migrations_step9a.py::test_a_confirmation_is_refused_when_the_counted_source_versions_are_not_the_runs",
  "tests/test_migrations_step9a.py::test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation",
  "tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing",
  "tests/test_migrations_step9a.py::test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses",
  "tests/test_migrations_step9a.py::test_a_confirmation_in_progress_holds_back_a_seal"
 ],
 "history": [],
 "notes": [
  "Step 11 decides how the evaluation runs are confirmed (owner, 2026-10-08). The website's Confirm button is step 10."
 ]
}
```
### `resumable_run`

Before (`f1ccddf`):

```json
{
 "key": "resumable_run",
 "name": "A run is taken up again from what is stored",
 "state": "in_force",
 "statement": "The orchestrator decides every step from stored rows, never from memory: a done Planner stage is used, not repeated; a stored narrowing decision is used; after the lock, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the statistics and the completion run only if their stored result is absent; an agent stage that exists (the Critic's, the Analyst's) is never started again; a completed partly-sufficient original without its narrower question gets it, and never a second one (a database index allows one per run; a draft left by a stop is submitted). A run on its first pass takes exactly the steps it took before. Recovery after a crash (closing open stages and calls, the Planner's one repeat) is step 9b.",
 "value": {
  "text": "next step from stored rows",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run that stops between steps (PRD 8 'Restart', 14.4).",
 "reason": "Step 9: a run must be taken up where it stopped without repeating a paid or a stored step (owner, Q3).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.orchestrator:proceed"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:create_narrower"
   },
   {
    "ref": "sql:uq_hypothesis_narrower_of_run_id"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results",
  "tests/test_resume_step9a.py::test_a_done_planner_stage_is_used_and_the_planner_is_not_asked_again",
  "tests/test_resume_step9a.py::test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question",
  "tests/test_migrations_step9a.py::test_a_run_has_at_most_one_narrower_question"
 ],
 "history": [],
 "notes": []
}
```

Now:

```json
{
 "key": "resumable_run",
 "name": "A run is taken up again from what is stored",
 "state": "in_force",
 "statement": "The orchestrator decides every step from stored rows, never from memory, and reads each agent's latest stored stage whatever its status before deciding what comes next. An earlier stop stays a stop: a Planner, Critic or Analyst stage that ended with a recording or reservation failure, or is still running, stops the run again (no further request, nothing more written; the run stays running for step 9b's recovery); a stored spending refusal at the Planner or the Critic fails the run, and a Planner stage that failed for any other reason fails it as the Planner's failure, so the Planner is never asked again in 9a; an Analyst stage that failed for any other reason, a spending refusal included, leaves code's decision standing (A3, B2). A done Planner stage is used, not repeated; a run already confirmed, or past its lock, goes on to the lock or past it without waiting again; a stored narrowing decision is used; after the lock, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the statistics and the completion run only if their stored result is absent; an agent stage that exists (the Critic's, the Analyst's) is never started again; a completed partly-sufficient original without its narrower question gets it, and never a second one (a database index allows one per run; a draft left by a stop is submitted). A run on its first pass takes exactly the steps it took before. Recovery after a crash (closing open stages and calls, the Planner's one repeat after an interruption) is step 9b; until then a stage left running stops the run.",
 "value": {
  "text": "next step from stored rows",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run that stops between steps (PRD 8 'Restart', 14.4).",
 "reason": "Step 9: a run must be taken up where it stopped without repeating a paid or a stored step (owner, Q3).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.orchestrator:proceed"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:create_narrower"
   },
   {
    "ref": "sql:uq_hypothesis_narrower_of_run_id"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:LEFT_RUNNING",
    "equals": "stage_left_running"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results",
  "tests/test_resume_step9a.py::test_a_done_planner_stage_is_used_and_the_planner_is_not_asked_again",
  "tests/test_resume_step9a.py::test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question",
  "tests/test_migrations_step9a.py::test_a_run_has_at_most_one_narrower_question",
  "tests/test_resume_step9a.py::test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again",
  "tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst",
  "tests/test_resume_step9a.py::test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed",
  "tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run"
 ],
 "history": [],
 "notes": []
}
```
### `run_cancel`

Before (`f1ccddf`):

```json
{
 "key": "run_cancel",
 "name": "A person cancels a queued or waiting run",
 "state": "in_force",
 "statement": "A named person cancels a run that is queued or waiting; it fails with 'cancelled: cancelled by <name> before it started' or 'cancelled: cancelled by <name> while waiting for confirmation of the question as tested'. A started run cannot be cancelled in sprint 1; an ended run cannot be cancelled.",
 "value": {
  "text": "queued or waiting only",
  "unit": null
 },
 "category": "operational",
 "affects": "Stopping a run (PRD 14.4; the owner's step 9 brief).",
 "reason": "Owner's step 9 brief ('a person can cancel a queued or waiting run'); R3.",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.queries:CANCELLED"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queries_step9a.py::test_a_queued_run_is_cancelled_with_the_persons_name",
  "tests/test_queries_step9a.py::test_a_waiting_run_is_cancelled_with_the_persons_name",
  "tests/test_queries_step9a.py::test_a_started_or_ended_run_is_not_cancelled"
 ],
 "history": [],
 "notes": []
}
```

Now:

```json
{
 "key": "run_cancel",
 "name": "A person cancels a queued or waiting run",
 "state": "in_force",
 "statement": "A named person cancels a run that is queued or waiting; it fails with 'cancelled: cancelled by <name> before it started' or 'cancelled: cancelled by <name> while waiting for confirmation of the question as tested'. A started run cannot be cancelled in sprint 1; an ended run cannot be cancelled. The database refuses a failure reason beginning 'cancelled:' unless the run was queued or waiting; other failures from running stay allowed (fix round 1, finding 5).",
 "value": {
  "text": "queued or waiting only",
  "unit": null
 },
 "category": "operational",
 "affects": "Stopping a run (PRD 14.4; the owner's step 9 brief).",
 "reason": "Owner's step 9 brief ('a person can cancel a queued or waiting run'); R3.",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-08"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.queries:CANCELLED"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queries_step9a.py::test_a_queued_run_is_cancelled_with_the_persons_name",
  "tests/test_queries_step9a.py::test_a_waiting_run_is_cancelled_with_the_persons_name",
  "tests/test_queries_step9a.py::test_a_started_or_ended_run_is_not_cancelled",
  "tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting"
 ],
 "history": [],
 "notes": []
}
```
## 5. Mutation checks

The 18 faults of this round, each against the named tests (the lock faults f12 and f13 only against their two-connection test, so a behavioural test catches them, not the lock-key text check):

```
f01      CAUGHT  6 failed, 32 passed in 211.32s (0:03:31)
f02      CAUGHT  1 failed, 37 passed in 199.13s (0:03:19)
f03      CAUGHT  2 failed, 36 passed in 200.02s (0:03:20)
f04      CAUGHT  4 failed, 34 passed in 209.71s (0:03:29)
f05      CAUGHT  1 failed, 37 passed in 197.15s (0:03:17)
f06      CAUGHT  3 failed, 35 passed in 195.53s (0:03:15)
f07      CAUGHT  2 failed, 36 passed in 194.07s (0:03:14)
f08      CAUGHT  5 failed, 33 passed in 192.56s (0:03:12)
f09      CAUGHT  6 failed, 32 passed in 161.29s (0:02:41)
f10      CAUGHT  3 failed, 65 passed in 20.82s
f11      CAUGHT  2 failed, 66 passed in 20.86s
f12      CAUGHT  1 failed in 11.76s
f13      CAUGHT  1 failed in 11.76s
f14      CAUGHT  1 failed, 26 passed in 66.49s (0:01:06)
f15      CAUGHT  2 failed, 66 passed in 21.51s
f16      CAUGHT  2 failed, 27 passed in 11.03s
f17      CAUGHT  1 failed, 67 passed in 21.29s
f18      CAUGHT  1 failed, 9 passed in 99.46s (0:01:39)
control  clean  172 passed in 378.98s (0:06:18)
```

The 39 earlier faults, re-run on the final tests, with the control run:

```
d01      CAUGHT  1 failed, 67 passed in 21.58s
d02      CAUGHT  1 failed, 67 passed in 22.10s
d03      CAUGHT  7 failed, 61 passed in 23.05s
d04      CAUGHT  4 failed, 64 passed in 21.06s
d05      CAUGHT  1 failed, 67 passed in 21.30s
d06      CAUGHT  1 failed, 67 passed in 21.24s
d07      CAUGHT  2 failed, 66 passed in 21.79s
d08      CAUGHT  1 failed, 67 passed in 21.17s
d09      CAUGHT  1 failed, 67 passed in 21.47s
c01      CAUGHT  3 failed, 24 passed in 68.12s (0:01:08)
c02      CAUGHT  1 failed, 26 passed in 68.71s (0:01:08)
c03      CAUGHT  1 failed, 26 passed in 68.33s (0:01:08)
c04      CAUGHT  1 failed, 26 passed in 69.85s (0:01:09)
c05      CAUGHT  1 failed, 26 passed in 68.18s (0:01:08)
c06      CAUGHT  1 failed, 26 passed in 69.10s (0:01:09)
c07      CAUGHT  1 failed, 26 passed in 64.01s (0:01:04)
o01      CAUGHT  2 failed, 25 passed in 64.27s (0:01:04)
o02      CAUGHT  22 failed, 5 passed in 49.78s
o03      CAUGHT  1 failed, 26 passed in 69.65s (0:01:09)
o04      CAUGHT  1 failed, 51 passed in 143.47s (0:02:23)
o05      CAUGHT  4 failed, 34 passed in 196.77s (0:03:16)
o06      CAUGHT  3 failed, 35 passed in 198.05s (0:03:18)
o07      CAUGHT  14 failed, 24 passed in 213.29s (0:03:33)
o08      CAUGHT  10 failed, 28 passed in 192.47s (0:03:12)
o09      CAUGHT  7 failed, 31 passed in 206.57s (0:03:26)
o10      CAUGHT  1 failed, 37 passed in 200.59s (0:03:20)
o11      CAUGHT  1 failed, 37 passed in 198.19s (0:03:18)
o12      CAUGHT  17 failed, 21 passed in 178.24s (0:02:58)
q01      CAUGHT  2 failed, 27 passed in 10.88s
q02      CAUGHT  1 failed, 28 passed in 11.04s
q03      CAUGHT  1 failed, 28 passed in 10.80s
q04      CAUGHT  1 failed, 28 passed in 10.81s
q05      CAUGHT  2 failed, 36 passed in 194.46s (0:03:14)
q06      CAUGHT  1 failed, 37 passed in 197.40s (0:03:17)
q07      CAUGHT  2 failed, 27 passed in 11.19s
s01      CAUGHT  2 failed, 27 passed in 10.88s
s02      CAUGHT  1 failed, 28 passed in 10.81s
l01      CAUGHT  1 failed, 9 passed in 95.74s (0:01:35)
l02      CAUGHT  1 failed, 9 passed in 95.83s (0:01:35)
control  clean  172 passed in 372.55s (0:06:12)
```

The specification of this round:

```python
"""Step 9a fix round 1 mutations (scratch copy, PYTHONPATH). Same format as mutations.py."""
T = "/workspaces/hypocurate/tests/"
M07 = "db/migrations/versions/0007_rules_confirmation.py"
O = "pipeline/orchestrator.py"
MIG, Q, C, R, CLI = ["test_migrations_step9a.py"], ["test_queries_step9a.py"], ["test_confirmation.py"], \
    ["test_resume_step9a.py"], ["test_cli_step9a.py"]
SEAL_FIRST = ["test_migrations_step9a.py::test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses"]
CONF_FIRST = ["test_migrations_step9a.py::test_a_confirmation_in_progress_holds_back_a_seal"]
MUTATIONS = [
 # Finding 1: an earlier stop stays a stop
 ("f01", O, "        if stored is not None and stored.status != \"done\":", "        if False:", R),
 ("f02", O, "            if stored.status == \"running\" or code in RUN_STOPS:", "            if code in RUN_STOPS:", R),
 ("f03", O, "            return _failed(engine, report, \"spending_refused\" if code in SPENDING else \"planner_failed\", code)", "            return _failed(engine, report, \"planner_failed\", code)", R),
 ("f04", O, "            failures = _critic_failures(engine, run_id)", "            failures = []", R),
 ("f05", O, "        stops = [f for f in failures if f in RUN_STOPS or f == LEFT_RUNNING]", "        stops = [f for f in failures if f in RUN_STOPS]", R),
 ("f06", O, "report.stages += [\"inclusion\", \"dataset freeze\", \"statistics\"]\n        stop = _agent_stop(", "report.stages += [\"inclusion\", \"dataset freeze\", \"statistics\"]\n        stop = None and _agent_stop(", R),
 ("f07", O, "            stop = _agent_stop(engine, run_id, \"analyst\")", "            stop = None", R),
 ("f08", O, "    return code if code in RUN_STOPS or code == LEFT_RUNNING else None", "    return None", R),
 # Finding 3: a confirmed run goes on without waiting again
 ("f09", O, "    if _exists(engine, \"SELECT 1 FROM rules_confirmation WHERE run_id = :r UNION ALL", "    if False and _exists(engine, \"SELECT 1 FROM rules_confirmation WHERE run_id = :r UNION ALL", R),
 # Finding 2: source freshness in the database, the shared lock
 ("f10", M07, "                     AND sv.id > rs.source_version_id) THEN", "                     AND false) THEN", MIG),
 ("f11", M07, "        IF EXISTS (SELECT 1 FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.run_id", "        IF false AND EXISTS (SELECT 1 FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.run_id", MIG),
 ("f12", M07, "        PERFORM pg_advisory_xact_lock(29382745069413747);  -- SOURCES_LOCK_KEY", "        -- the lock removed", SEAL_FIRST),
 ("f13", M07, "        PERFORM pg_advisory_xact_lock({SOURCES_LOCK_KEY});\n        RETURN NEW;", "        RETURN NEW;", CONF_FIRST),
 ("f14", "pipeline/confirmation.py", "        conn.execute(text(\"SELECT pg_advisory_xact_lock(:k)\"), dict(k=SOURCES_LOCK_KEY))\n", "", C),
 # Finding 5: cancel in the database
 ("f15", M07, "           AND NEW.failure_reason LIKE 'cancelled:%' THEN", "           AND false THEN", MIG),
 # The owner's decision: every new run stores its ceiling
 ("f16", "pipeline/queries.py", "                            c=ceiling if ceiling is not None else spend_cap())).scalar_one()", "                            c=ceiling)).scalar_one()", Q),
 ("f17", M07, "    op.alter_column('run', 'spending_ceiling', server_default=sa.text(CEILING_DEFAULT))\n", "", MIG),
 # Finding 4: no ceiling at confirmation
 ("f18", "cli.py", "    confirm.add_argument(\"--by\", required=True, help=\"the name of the person confirming\")\n", "    confirm.add_argument(\"--by\", required=True, help=\"the name of the person confirming\")\n    confirm.add_argument(\"--ceiling\")\n", CLI),
]
```
```python
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import sys as _s; from importlib import import_module as _i; _m = _i(_s.argv[1] if len(_s.argv) > 1 else "mutations"); MUTATIONS, T = _m.MUTATIONS, _m.T
M = os.path.expanduser("~/hc-work/step09a/mut")
env = dict(os.environ, PYTHONPATH=M)
env["DATABASE_URL"] = open("/workspaces/hypocurate/.env").read().split("DATABASE_URL=")[1].split("\n")[0]
results = []
for mid, f, old, new, tests in MUTATIONS + [("control", None, None, None, ["test_migrations_step9a.py", "test_queries_step9a.py", "test_confirmation.py", "test_resume_step9a.py", "test_cli_step9a.py"])]:
    shutil.rmtree(os.path.join(M, "hypocurate"), ignore_errors=True)
    shutil.copytree("/workspaces/hypocurate/hypocurate", os.path.join(M, "hypocurate"))
    if f:
        p = os.path.join(M, "hypocurate", f); s = open(p).read()
        assert s.count(old) >= 1, (mid, "pattern not found")
        open(p, "w").write(s.replace(old, new, 1))
    out = subprocess.run([sys.executable if False else "/workspaces/hypocurate/.venv/bin/pytest", "-q", "-p", "no:cacheprovider",
                          "--rootdir=/workspaces/hypocurate"] + [T + t for t in tests], cwd=os.path.expanduser("~/hc-work/step09a"),
                         env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    caught = "failed" in out or "error" in out
    line = f"{mid:8} {'CAUGHT' if caught else ('clean' if mid == 'control' else 'SURVIVED')}  {out}"
    print(line, flush=True); results.append(line)
```
## 6. Reference comparison with `main`

The same dumps as in the review packet, on this head:

```
head 7fc5ee3
DIFFERENT fixed_plan.json
DIFFERENT narrower.json
DIFFERENT partly_original.json
DIFFERENT planner_bcc.json
DIFFERENT planner_fcc.json
IDENTICAL reference.json
```

```
== fixed_plan: 1 differing leaves
  .run[0].spending_ceiling: "<absent>" -> 2
== planner_fcc: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> 2
  .show.question_as_tested.label: "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person" -> "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person): yield strength against grain siz -> "Question as tested (the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC): yield strength against gra
== planner_bcc: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> 2
  .show.question_as_tested.label: "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person" -> "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person): yield strength against grain siz -> "Question as tested (the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC): yield strength against gra
== partly_original: 1 differing leaves
  .run[0].spending_ceiling: "<absent>" -> 2
== narrower: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> 2
  .show.question_as_tested.label: "the narrower plan stored by the original question's narrowing decision" -> "the narrower plan stored by the original question's narrowing decision; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the narrower plan stored by the original question's narrowing decision): yield strength against grain size, in multi-principal-element (hig -> "Question as tested (the narrower plan stored by the original question's narrowing decision; confirmed by Ada Reviewer on <time> UTC): yield streng
```
## 7. The suite and the images

The whole suite on this head (locally):

```
2019 passed, 1 warning in 1327.07s (0:22:07)
local exit 0
```

In the test image, rebuilt on this head:

```
2019 passed, 1 warning in 1389.46s (0:23:09)
exit 0
```

The package in the repository and in both images:

```
head:    7fc5ee3
repo:    9061b47606e349fa1c4580b83ca840d8d02f4143223e2f0069d31a5718b6d646  -
runtime: 9061b47606e349fa1c4580b83ca840d8d02f4143223e2f0069d31a5718b6d646  -
test:    9061b47606e349fa1c4580b83ca840d8d02f4143223e2f0069d31a5718b6d646  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
```

The guard checks in the runtime image:

```
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmp5n_sdav5/.env is outside the approved inputs of pipeline code']}
```
## 8. The local development database

It was migrated to the reviewed 0007 earlier. It was backed up (`pg_dump`), downgraded with the reviewed version of 0007 from a scratch copy (it had no waiting run, no confirmation and no ceiling), and upgraded to the amended 0007. Its 12 runs, 21 model calls and $1.027756 are kept; the old runs have no ceiling, and the column's default is 2.

## 9. The scripts

### `~/hc-work/step09a/register_fix1.py`

```python
"""Step 9a fix round 1: register corrections (scratch; run from the repo root with the project's Python). The entries
new on this unmerged branch are corrected in place (their earlier, unmerged wording is in the fix packet); an entry
that exists on main keeps main's wording in its history, as before."""
import json
P = "hypocurate/assumptions.json"
d = json.load(open(P, encoding="utf-8"))
by = {e["key"]: e for e in d}


def rep(key, old, new, field="statement"):
    e = by[key]
    assert e[field].count(old) == 1, (key, old[:60])
    e[field] = e[field].replace(old, new)


rep("resumable_run", "The orchestrator decides every step from stored rows, never from memory: a done Planner stage is used, not "
    "repeated;",
    "The orchestrator decides every step from stored rows, never from memory, and reads each agent's latest stored "
    "stage whatever its status before deciding what comes next. An earlier stop stays a stop: a Planner, Critic or "
    "Analyst stage that ended with a recording or reservation failure, or is still running, stops the run again (no "
    "further request, nothing more written; the run stays running for step 9b's recovery); a stored spending refusal "
    "at the Planner or the Critic fails the run, and a Planner stage that failed for any other reason fails it as the "
    "Planner's failure, so the Planner is never asked again in 9a; an Analyst stage that failed for any other reason, a "
    "spending refusal included, leaves code's decision standing (A3, B2). A done Planner stage is used, not repeated; a "
    "run already confirmed, or past its lock, goes on to the lock or past it without waiting again;")
rep("resumable_run", "Recovery after a crash (closing open stages and calls, the Planner's one repeat) is step 9b.",
    "Recovery after a crash (closing open stages and calls, the Planner's one repeat after an interruption) is step "
    "9b; until then a stage left running stops the run.")
by["resumable_run"]["tests"] += [
    "tests/test_resume_step9a.py::test_a_failed_planner_reservation_stays_a_stop_and_the_planner_is_not_asked_again",
    "tests/test_resume_step9a.py::test_a_stored_critic_accounting_or_spending_failure_stops_the_run_before_the_analyst",
    "tests/test_resume_step9a.py::test_a_stored_analyst_accounting_failure_or_open_stage_is_never_completed",
    "tests/test_resume_step9a.py::test_a_confirmed_run_stopped_around_the_lock_is_completed_through_run"]
by["resumable_run"]["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.orchestrator:LEFT_RUNNING",
                                                   "equals": "stage_left_running"})

rep("run_order_and_failures", "the run stays running (a call whose recording failed stays started) until step 9b's recovery.",
    "the run stays running (a call whose recording failed stays started) until step 9b's recovery. Taken up again, "
    "the run reads each agent's latest stored stage whatever its status, so such a stop, a stage left running or a "
    "stored spending refusal has the same effect as when it happened (register 'resumable_run').")

rep("rules_confirmation", "It is refused when a chosen source has a newer sealed version, or a source was registered, since dispatch "
    "(the run's own versions never change); nothing is redone.",
    "It is refused when a source the run uses has a newer sealed version than the run's, or a source was registered "
    "after the run's dispatch (the run's own versions never change); nothing is redone. The database enforces this "
    "too: the confirmation takes one advisory lock that registering a source and sealing a version also take, then "
    "checks the registered sources, so a registration and a confirmation cannot slip past each other (fix round 1, "
    "finding 2). A run already confirmed is never made to wait again.")
by["rules_confirmation"]["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.confirmation:SOURCES_LOCK_KEY",
                                                        "equals": 0x68637372636573})
by["rules_confirmation"]["applied"]["settings"].append({"ref": "sql:hc_sources_lock"})
by["rules_confirmation"]["tests"] += [
    "tests/test_migrations_step9a.py::test_a_confirmation_is_refused_after_a_source_change_since_the_narrowing",
    "tests/test_migrations_step9a.py::test_a_seal_in_progress_holds_back_a_confirmation_which_then_refuses",
    "tests/test_migrations_step9a.py::test_a_confirmation_in_progress_holds_back_a_seal"]

rep("run_cancel", "A started run cannot be cancelled in sprint 1; an ended run cannot be cancelled.",
    "A started run cannot be cancelled in sprint 1; an ended run cannot be cancelled. The database refuses a failure "
    "reason beginning 'cancelled:' unless the run was queued or waiting; other failures from running stay allowed (fix "
    "round 1, finding 5).")
by["run_cancel"]["tests"].append(
    "tests/test_migrations_step9a.py::test_a_cancelled_failure_is_allowed_only_from_queued_or_waiting")

e = by["spending_caps"]
rep("spending_caps", "a lower ceiling (the lower of one the caller names and, for a run, the one "
    "stored on the run at dispatch, which holds after a crash or a restart), is not sent",
    "a lower ceiling (the lower of one the caller names and, for a run, the one "
    "stored on the run at dispatch, which holds after a crash or a restart), is not sent")
rep("spending_caps", "So two concurrent reservations can never both pass the same cap or ceiling.",
    "So two concurrent reservations can never both pass the same cap or ceiling. Every run dispatched after migration "
    "0007 stores its ceiling: the one given at dispatch, or else the per-run cap (the owner's decision, 2026-10-08; the "
    "column's default). The ceiling is set only at dispatch; `confirm` takes none.")
e["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.queries:spend_cap"})
e["applied"]["settings"].append({"ref": "sql:CEILING_DEFAULT"})
e["tests"] += ["tests/test_queries_step9a.py::test_a_dispatch_without_a_ceiling_stores_the_run_cap",
               "tests/test_migrations_step9a.py::test_a_run_dispatched_without_a_ceiling_stores_the_run_cap",
               "tests/test_cli_step9a.py::test_confirm_takes_no_ceiling"]

with open(P, "w", encoding="utf-8") as f:
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(len(d), "entries")
```
### `~/hc-work/step09a/fixpacket.py`

````python
"""Builds docs/reviews/step09a_fix_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step09a"
REVIEWED = "f1ccddf"  # the head ChatGPT reviewed
OUT = Path("docs/reviews/step09a_fix_packet.md")


def sh(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fence(text: str, lang: str = "") -> str:
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


def read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def lines_with(path, *words) -> str:
    return "\n".join(l for l in read(path).splitlines() if any(w in l for w in words))


head = sh("git", "rev-parse", "--short", "HEAD").strip()
commits = sh("git", "log", "--format=%h %s", f"{REVIEWED}..HEAD").strip()
FINDINGS = [
    ("1", "A resume respects earlier stops", "0b5ab5b",
     "Before each agent step, `proceed`/`prepare` read the role's latest stored stage whatever its status "
     "(`_stored(..., done=False)`, `_agent_stop`, `_critic_failures`, `_stage_code`).\n"
     "- **A stop stays a stop:** a recording or reservation failure (`lm.RUN_STOPS`), or a stage still running (`stage_left_running`), stops the run again. No further request is made, nothing more is written, and the run stays running for 9b.\n"
     "- **Planner:** a stored spending refusal fails the run as `spending_refused`; any other stored failure fails it as `planner_failed`. The Planner is never asked again in 9a.\n"
     "- **Critic:** its stored stages decide as they did when it ran. A stop stops the run; a spending refusal fails it; any other failure lets the run go on.\n"
     "- **Analyst:** a stop stops the run before completion, also on the partly-sufficient path, before the copy and the narrower question. Any other failure, a spending refusal included, completes the run with code's decision (A3, B2).\n"
     "- **Left for 9b:** interrupted stages and the one Planner repeat."),
    ("2", "Source freshness in the database, with a shared lock", "47c4f7c",
     "- **The check:** `hc_rules_confirmation_insert` takes advisory lock `SOURCES_LOCK_KEY`, then refuses when a source the run uses has a sealed version newer than the run's, or a source exists that the run did not record at dispatch.\n"
     "- **Registration and sealing:** `hc_sources_lock` takes the same lock when a source is inserted, or a version is inserted sealed or becomes sealed. 0001 never allows a version to be inserted sealed, so that trigger is a backstop only.\n"
     "- **The Python path:** `confirmation.confirm` takes the lock before its own check, so the check and the insert see the same sources, and a registration that commits meanwhile gets code's reason.\n"
     "- **Lock order:** the run's lock, then the sources lock. Registration takes no run lock, so there is no cycle.\n"
     "- **Scope** (the owner's wording, \"any source the run uses\"): a newer version of a source the query did not choose is no change. The code's check is the same."),
    ("3", "A confirmed run goes on through run()", "0b5ab5b",
     "`prepare` recognises an existing confirmation or a locked plan, and goes on to `proceed` (ready) without waiting "
     "again. `proceed` moves a confirmed waiting run to running, as before."),
    ("4", "No ceiling at confirmation", "0b436df",
     "`confirm --ceiling` and `_confirm`'s ceiling are removed. The ceiling is stored only at dispatch, and "
     "`spend.reserve` reads it on every request."),
    ("5", "Cancel in the database", "47c4f7c",
     "`hc_run_waiting` refuses a change to failed with a reason beginning \"cancelled:\" unless the run was queued or "
     "waiting. Other failures from running stay allowed."),
    ("Owner", "Every run stores its effective ceiling", "47c4f7c",
     "- **Dispatch:** `_new_run` stores the given ceiling, or the per-run cap (`queries.spend_cap()`, which is `spend.RUN_CAP_USD`).\n"
     "- **The database:** 0007 sets the column's default to the cap (`CEILING_DEFAULT`, tested equal to `RUN_CAP_USD`), so a dispatch by the previous release's code stores it too. The default is set after the column is added, so runs before 0007 stay empty.\n"
     "- **The downgrade** refuses only a ceiling below the cap. A ceiling equal to the cap says no more than the cap, and refusing it would make 0007 impossible to downgrade once any run exists."),
]
parts = [f"""# Build step 9a — fix packet (fix round 1)

Date: 2026-10-08. Branch: `step-09a-waiting`. Reviewed head: `{REVIEWED}`. Head when generated: `{head}`. Generated from
the files on disk by a script (`~/hc-work/step09a/fixpacket.py`, quoted in section 9), so every diff and output below
is quoted exactly.

## How to use this packet

ChatGPT's review of `{REVIEWED}` (`docs/reviews/step09a_review_chatgpt.md`) found the step not safe to merge, with five
findings. The owner accepted all five and added one decision: every run stores its effective ceiling at dispatch. This
packet covers only this round:
1. the findings and their fixes;
2. the code diff;
3. the tests, new and changed, and the tests that failed before;
4. the register;
5. the mutation checks;
6. the reference comparison with `main`;
7. the suite and the images;
8. the local database;
9. the scripts.

The summary (`step09a_summary.md`) carries an update note at the top. Please confirm each finding is closed, and say
whether anything in this round is stronger in its claims than the code supports.

Commits of this round:

""" + fence(commits) + "\n"]
body = "## 1. The findings and their fixes\n\n"
for num, title, commit, text in FINDINGS:
    body += f"### Finding {num}: {title} (commit `{commit}`)\n\n{text}\n\n"
body += ("**The owner's three choices, stated before the build:**\n"
         "- \"Newer since the narrowing\" is checked against the run's own versions. That covers everything since "
         "the narrowing and also a version sealed between dispatch and narrowing.\n"
         "- The ceiling has a database default.\n"
         "- The downgrade refuses only a ceiling below the cap.\n\n")
parts.append(body)
diff = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{REVIEWED}..HEAD`, the package with 0007; the register is in section 4)\n\n"
             + fence(diff, "diff"))
tdiff = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "tests")
parts.append("## 3. Tests\n\n### Tests added or changed in this round (diff)\n\n" + fence(tdiff, "diff")
             + "\n### Changed expectations (reasons)\n\n"
             "- `test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded`: "
             "the new run's ceiling is the run cap (was asserted empty). Reason: the owner's decision.\n"
             "- No other existing assertion changed. A test written in this round, and changed before the fix, now "
             "checks the owner's wording: a newer version of a source the run does not use is no change "
             "(`test_a_newer_version_of_a_source_the_run_does_not_use_is_no_change`, a guard).\n\n"
             "### The tests of this round on the reviewed code (`" + REVIEWED + "`'s package, scratch copy, `PYTHONPATH`)\n\n"
             "The selection also picked up earlier resume tests, which pass there. The new tests that pass there are "
             "guards by design: an ordinary Critic or Analyst failure, a newer version of an unused source, the "
             "allowed failures, and the downgrade at the cap.\n\n"
             + fence(lines_with(HOME / "fix1_failed_before.log", "PASSED", "FAILED", "passed", "failed")))
old = {e["key"]: e for e in json.loads(sh("git", "show", f"{REVIEWED}:hypocurate/assumptions.json"))}
new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
changed = [k for k in new if old.get(k) != new[k]]
reg = ""
for k in changed:
    reg += f"### `{k}`\n\nBefore (`{REVIEWED}`):\n\n" + fence(json.dumps(old.get(k), indent=1, ensure_ascii=False), "json")
    reg += "\nNow:\n\n" + fence(json.dumps(new[k], indent=1, ensure_ascii=False), "json")
parts.append(f"## 4. The register ({len(new)} entries; {len(changed)} changed in this round)\n\n"
             "`resumable_run`, `rules_confirmation` and `run_cancel` are new on this unmerged branch, so they are "
             "corrected in place. Their reviewed wording is shown here. `run_order_and_failures` and `spending_caps` "
             "keep main's wording in their history.\n\n" + reg)
parts.append("## 5. Mutation checks\n\nThe 18 faults of this round, each against the named tests (the lock faults "
             "f12 and f13 only against their two-connection test, so a behavioural test catches them, not the "
             "lock-key text check):\n\n" + fence(read(HOME / "fix1_mutations.log"))
             + "\nThe 39 earlier faults, re-run on the final tests, with the control run:\n\n"
             + fence(read(HOME / "fix1_mutations_earlier.log"))
             + "\nThe specification of this round:\n\n" + fence(read(HOME / "mspec/mutations_fix1.py"), "python")
             + fence(read(HOME / "mspec/run_any.py"), "python"))
parts.append("## 6. Reference comparison with `main`\n\nThe same dumps as in the review packet, on this head:\n\n"
             + fence(read(HOME / "refdump/cmp_fix1.txt")) + "\n" + fence(read(HOME / "refdump/compare_fix1_output.txt")))
parts.append("## 7. The suite and the images\n\nThe whole suite on this head (locally):\n\n"
             + fence(lines_with(HOME / "fix1_final_full.log", "passed", "failed", "exit"))
             + "\nIn the test image, rebuilt on this head:\n\n"
             + fence(lines_with(HOME / "fix1_image_suite.log", "passed", "failed", "exit"))
             + "\nThe package in the repository and in both images:\n\n" + fence(read(HOME / "fix1_image_hashes.txt"))
             + "\nThe guard checks in the runtime image:\n\n" + fence(read(HOME / "fix1_image_guard.log")))
parts.append("## 8. The local development database\n\nIt was migrated to the reviewed 0007 earlier. It was backed up "
             "(`pg_dump`), downgraded with the reviewed version of 0007 from a scratch copy (it had no waiting run, "
             "no confirmation and no ceiling), and upgraded to the amended 0007. Its 12 runs, 21 model calls and "
             "$1.027756 are kept; the old runs have no ceiling, and the column's default is 2.\n\n")
parts.append("## 9. The scripts\n\n" + "".join(f"### `~/hc-work/step09a/{s}`\n\n" + fence(read(HOME / s), "python")
                                         for s in ("register_fix1.py", "fixpacket.py")))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
