# Build step 9b — fix packet (fix round 1)

Date: 2026-10-09. Branch: `step-09b-worker`. Reviewed head: `368a426`. Head when generated: `a9251d2`. Generated from
the files on disk by a script (`~/hc-work/step09b/fixpacket.py`, quoted in section 9), so every diff and output below
is quoted exactly.

## How to use this packet

ChatGPT's review of `368a426` (`docs/reviews/step09b_review_chatgpt.md`) found the step not safe to merge, with seven
findings. The owner accepted all seven, added a list of extras (below the findings), approved two design choices and
added one requirement to finding 3. This packet covers only this round:
1. the findings and their fixes;
2. the code diff;
3. the tests, new and changed, and the tests that failed before;
4. the register;
5. the mutation checks;
6. the reference comparison with `main`;
7. the suite and the images;
8. the local database;
9. the scripts.

The summary (`step09b_summary.md`) has a "Fix round 1" section near the top. Please confirm each finding is closed, and say
whether anything in this round is stronger in its claims than the code supports.

Commits of this round:

```
a9251d2 Step 9b fix round 1: the takeover race test checks the wait itself, not two Python clock readings (owner, 2026-10-09)
641af6b Step 9b fix round 1 mutation checks: two monitoring tests fail instead of hanging (f14, f15)
d9523ca Step 9b fix round 1: one shutdown check before each child (the earlier one duplicated it)
8a059e8 Step 9b fix round 1, findings 2-7, worker sessions, the two-batch Critic case, register corrections
5b3923d Render: the header comment says the worker is on 1c-2g (owner, 2026-10-09: fix the stale 'cheapest paid plans' comment)
4f16f36 Step 9b plan: fix round 1 instructions and the owner's addition on the claim check
0dcabad Step 9b fix round 1, finding 1: a spending refusal survives a failed save
77abd7e Step 9b: ChatGPT's review, saved verbatim (not safe to merge; seven findings)
```

## 1. The findings and their fixes

### Finding 1: A spending refusal survives a failed save (commit `0dcabad`)

- **The refusal record:** `spend.reserve` writes the refusal's audit row in the transaction that decides it. A refusal is reported only once its record is committed; if that commit fails, the caller sees a failure to save the call, which the owner's split rule treats as a database failure.
- **Recovery:** before closing a running stage as `interrupted`, it looks for a committed refusal against the stage's invocations and keeps that code as the stage's cause. The Planner and the Critic then fail the run as in 9a: nothing is repeated or sent, and the Analyst is never asked after a Critic refusal.
- **Tests:** a real refusal (the run's ceiling, or the monthly cap) at the Planner and at the Critic; the stage's save then refused by a test trigger; recovery. The month change is simulated by moving the counted calls into the previous month, with triggers off.

### Finding 2: Never release a claim with a live child (commit `8a059e8, d9523ca`)

- **The child stops:** `GuardedChild.stop` escalates a SIGTERM not obeyed within 10 s (`STOP_GRACE_SECONDS`) to SIGKILL, and reaps the child.
- **The release:** `worker.work` keeps the child and stops it in `finally` on every exit path before releasing the claim.
- **Shutdown:** checked before each child is started (`d9523ca` removed an earlier duplicate check, so the remaining one is tested alone).

### Finding 3: Losing the lock means stopping (commit `8a059e8`)

- **The worker:** each heartbeat confirms that its update touched the open claim's row and that the lease session still holds CLAIM (`Lease.holds`). Otherwise it sets `lost`, and the worker stops its child at once and gives the run up (`lost`).
- **The child:** its work is bound to its claim. `orchestrator.work_guarded` sets `writes.OWNER` = (claim id, the pid of the session holding its work lock).
- **Each write:** `writes.write` checks, in its own transaction after the run's lock, that the claim is open (its row locked **FOR KEY SHARE**) and that the work lock is still held (`pg_locks`). Otherwise the write is refused `claim_lost`.
- **Each request:** `spend.reserve` checks the same before any request (`ClaimLost`, which the request path reports as a reservation failure).
- **The owner's addition (the check inside the write's transaction):**
  - 0008's update trigger locks the claim row FOR UPDATE before closing it, so any close, a takeover or direct SQL, waits for a write in progress, or the write sees the claim closed.
  - FOR KEY SHARE rather than FOR SHARE: the worker's own heartbeat is a plain update, and under FOR SHARE it would wait behind a long write (storing thousands of records) and wrongly report lost ownership.
- **Tests:**
  - terminating the lease's database session, and the work lock's, while the processes stay alive;
  - a two-connection race of a takeover against a child's write;
  - a stale owner's reservation.

### Finding 4: The recovery exception applies only to old stages (commit `8a059e8`)

`proceed` excuses a lost Critic request only for Critic stages stored before (those recovery processed). The failures of a Critic run now stop the run normally.

### Finding 5: Monitoring cannot block the watchdog (commit `8a059e8`)

- **The monitor:** `queue.Monitor` samples the run's last write on a thread of its own, each query limited to 5 s (`MONITOR_TIMEOUT_MS`, statement and lock timeouts).
- **The main thread** never queries the database while it watches: the whole-run limit, the shutdown check and the lost-ownership check are on its own clock and events.
- **Tests:** a monitoring query made to block forever, at the whole-run limit and at a shutdown; and a monitoring query held by a table lock is cut off.

### Finding 6: The stall allowance starts fresh (commit `8a059e8`)

The allowance counts from `Monitor.progress_at`: the child's launch, and each progress seen after it. Downtime before the attempt does not count.

### Finding 7: Recovery count (commit `8a059e8`)

- **The count:** `run_claim.recovery` (0008 amended, unmerged) marks a claim that took up a run already running, set at the claim and never changed. Recovery counts those claims, this one included, and fails the run when there are more than 3. The first run's claim is not one.
- **Test:** real claim histories, each attempt a claim worked by the worker's code and stopped by a shutdown: three recoveries go on, and the fourth is refused.

**The owner's decisions in this round (2026-10-09):**
- The refusal's audit row is written in the transaction that decides the refusal.
- The claim check (claim open and work lock held) lives in `writes.write` and `spend.reserve`, refusing `claim_lost`.
- The check runs inside the write's transaction with the claim row locked, so a takeover that closes the claim waits for the write or the write sees the closed claim. A two-connection race test. For model requests, the check before the reservation is enough.

### Also (the owner's list)

- **Worker sessions:** the worker's and its child's sessions set `client_connection_check_interval` to 1 s and TCP keepalives (30/10/3) on both sides (`db.engine.WORKER_SESSION`, `make_engine(worker_session=True)`); register `worker_session_settings` (new).
- **The kill case "mid-Critic, batch 1 of 2":** 110 rows in both sources raise 110 flags naming two records each (two batches, at most 100 per request); the worker is killed during the first; after recovery the second is never sent and the run completes. New coverage, not a fix.
- **`render.yaml`'s stale header comment** is corrected (`5b3923d`), its own commit. The full `render.yaml` diff against `main` is below.
- **The register** is corrected wherever it promised more than the code: `queue_and_claims`, `stuck_child_limits`, `recovery_policy`, `spending_caps`; `worker_session_settings` is new (148 entries).

### The full `render.yaml` diff against `main` (`c7458d0`)

```diff
diff --git a/render.yaml b/render.yaml
index fe61f3e..87d6c06 100644
--- a/render.yaml
+++ b/render.yaml
@@ -2,7 +2,8 @@
 # services; nothing exists on Render until the owner connects it as a Blueprint.
 # Checked against render.com/docs/blueprint-spec on 2026-10-04.
 #
-# Plans: the cheapest paid plans (owner decision, 2026-10-04).
+# Plans: the cheapest paid plans (owner decision, 2026-10-04), except the worker: 1c-2g (owner decision,
+# 2026-10-08, after the step 9b memory measurement on 0.5 CPU / 512 MB).
 # autoDeployTrigger checksPass: Render deploys a commit on main only after its
 # GitHub checks pass, and never when a check fails or no check is found.
 # Region: all three in one region, so the services reach the database over
@@ -38,7 +39,7 @@ services:
     name: hypocurate-worker
     runtime: docker
     region: oregon
-    plan: 0.5c-512mb
+    plan: 1c-2g
     branch: main
     autoDeployTrigger: checksPass
     dockerfilePath: ./Dockerfile
```

## 2. Code diff (`368a426..HEAD`, the package with 0008; the register is in section 4)

```diff
diff --git a/hypocurate/access/guarded.py b/hypocurate/access/guarded.py
index c937985..00f04c6 100644
--- a/hypocurate/access/guarded.py
+++ b/hypocurate/access/guarded.py
@@ -69,6 +69,7 @@ class GuardedRunError(Exception):
 
 MAX_REPORTED = 100  # refusals copied into the audit log per run; the rest are counted
 PARENT_GONE_EXIT = 3  # step 9b (A3): the child found that the process that started it is gone
+STOP_GRACE_SECONDS = 10  # step 9b fix round 1 (finding 2): a SIGTERM not obeyed within this is escalated to SIGKILL
 PR_SET_PDEATHSIG = 1  # linux/prctl.h
 
 
@@ -153,11 +154,18 @@ class GuardedChild:
         self._out, self._err = out or "", err or ""
         return True
 
+    def alive(self) -> bool:
+        return self.proc.poll() is None
+
     def stop(self, sig: int = signal.SIGKILL) -> None:
-        """Ends the child (SIGKILL by default) and waits for it."""
+        """Ends the child and reaps it: `sig` (SIGKILL by default); a SIGTERM not obeyed within `STOP_GRACE_SECONDS`
+        is escalated to SIGKILL (fix round 1, finding 2). Returns only once the child has ended."""
         if self.proc.poll() is None:
             self.proc.send_signal(sig)
-        self.wait_for(30)
+        if not self.wait_for(STOP_GRACE_SECONDS if sig != signal.SIGKILL else 30) and self.proc.poll() is None:
+            self.proc.kill()
+            self.wait_for(30)
+        self.proc.wait()
 
     def result(self, timeout: float | None = None) -> Any:
         """The child's answer (GuardedRunError if it failed); its refusals reported; its scratch removed."""
diff --git a/hypocurate/db/engine.py b/hypocurate/db/engine.py
index 47db92f..3fa5500 100644
--- a/hypocurate/db/engine.py
+++ b/hypocurate/db/engine.py
@@ -8,7 +8,14 @@ from sqlalchemy import Engine, create_engine, text
 SESSION_TIME_ZONE = "UTC"  # register 'database_session_time_zone'
 
 
-def make_engine(database_url: str) -> Engine:
+# Step 9b fix round 1 (owner, 2026-10-09): a worker's and its child's sessions check every second whether their client
+# is still there (so PostgreSQL abandons a query of a process that died) and keep TCP alive, so a lost connection is
+# noticed (the server side's keepalives; the client's below).
+WORKER_SESSION = {"client_connection_check_interval": "1s", "tcp_keepalives_idle": "30",
+                  "tcp_keepalives_interval": "10", "tcp_keepalives_count": "3"}
+
+
+def make_engine(database_url: str, *, worker_session: bool = False) -> Engine:
     # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
     if database_url.startswith("postgresql://"):
         database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
@@ -16,8 +23,12 @@ def make_engine(database_url: str) -> Engine:
     # interprets timestamps without reading a zone file, which the file guard would refuse (a server
     # zone such as 'Etc/UTC' makes it open /usr/share/zoneinfo). Every query states its zone where it
     # matters ('AT TIME ZONE ...'), and the servers used so far run in UTC already.
-    return create_engine(database_url, pool_pre_ping=True,
-                         connect_args={"connect_timeout": 3, "options": f"-c TimeZone={SESSION_TIME_ZONE}"})
+    options = f"-c TimeZone={SESSION_TIME_ZONE}"
+    connect_args: dict = {"connect_timeout": 3}
+    if worker_session:
+        options += "".join(f" -c {k}={v}" for k, v in WORKER_SESSION.items())
+        connect_args.update(keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
+    return create_engine(database_url, pool_pre_ping=True, connect_args={**connect_args, "options": options})
 
 
 def database_reachable(engine: Engine) -> bool:
diff --git a/hypocurate/db/migrations/versions/0008_run_claim.py b/hypocurate/db/migrations/versions/0008_run_claim.py
index 06317e3..7e40924 100644
--- a/hypocurate/db/migrations/versions/0008_run_claim.py
+++ b/hypocurate/db/migrations/versions/0008_run_claim.py
@@ -14,7 +14,10 @@ run_claim, one row per claim, never deleted:
 - only an open run (queued, running or waiting) is claimed, and at most one claim per run is open (a partial
   unique index);
 - while a claim is open only its heartbeat, its child's pid (once), `found` and the release may change; once
-  released it is final.
+  released it is final;
+- (fix round 1) `recovery`: whether the claim took up a run already running (a recovery attempt), never changed;
+  closing a claim locks its row FOR UPDATE first, so it waits for a write of the claim's child in progress (which
+  holds the row FOR KEY SHARE, `pipeline/writes.owner_holds`).
 The heartbeat is written on the claim row, not the run row (R6), so it never waits behind a transaction that holds
 the run's lock: the update trigger reads no run row. A named exception to the locking protocol, like audit rows.
 
@@ -73,6 +76,14 @@ FUNCTIONS = [
         IF OLD.child_pid IS NOT NULL AND NEW.child_pid IS DISTINCT FROM OLD.child_pid THEN
             PERFORM hc_reject('a claim''s child is recorded once');
         END IF;
+        IF NEW.recovery IS DISTINCT FROM OLD.recovery THEN
+            PERFORM hc_reject('what a claim records cannot change');
+        END IF;
+        -- Fix round 1, finding 3 (owner, 2026-10-09): closing a claim waits for any write of its child in progress
+        -- (which holds the row FOR KEY SHARE), so the write commits first or sees the claim closed.
+        IF NEW.released_at IS NOT NULL THEN
+            PERFORM 1 FROM run_claim WHERE id = OLD.id FOR UPDATE;
+        END IF;
         IF NEW.heartbeat_at IS DISTINCT FROM OLD.heartbeat_at THEN
             NEW.heartbeat_at := clock_timestamp();
         END IF;
@@ -112,6 +123,9 @@ def upgrade() -> None:
         sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
         sa.Column('release_reason', sa.Text(), nullable=True),
         sa.Column('found', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
+        # Fix round 1, finding 7: the claim took up a run that was already running (a recovery attempt), set at the
+        # claim and never changed; the first run's claim (from queued or waiting) is not one.
+        sa.Column('recovery', sa.Boolean(), server_default=sa.text('false'), nullable=False),
         sa.CheckConstraint(f"length(btrim(worker)) BETWEEN 1 AND {WORKER_MAX}", name=op.f('ck_run_claim_worker_named')),
         sa.CheckConstraint(f"release_reason IS NULL OR {_in('release_reason', RELEASE_REASONS)}",
                            name=op.f('ck_run_claim_release')),
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index b95c1e6..357f4e6 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -429,6 +429,7 @@ class RunClaim(Base):
     released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
     release_reason: Mapped[str | None] = mapped_column(Text)
     found: Mapped[dict | None] = mapped_column(JSONB)
+    recovery: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))  # fix round 1, finding 7
     __table_args__ = (
         Index("uq_run_claim_open", "run_id", unique=True, postgresql_where=sql("released_at IS NULL")),
         CheckConstraint("length(btrim(worker)) BETWEEN 1 AND 200", name="worker_named"),
diff --git a/hypocurate/pipeline/agents/spend.py b/hypocurate/pipeline/agents/spend.py
index c4789c7..be00ce4 100644
--- a/hypocurate/pipeline/agents/spend.py
+++ b/hypocurate/pipeline/agents/spend.py
@@ -14,8 +14,11 @@ while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
 - optionally a lower ceiling the caller names (the live curation call: $0.50, owner 2026-10-06),
   over the same run or invocation; for a run, also the ceiling stored on the run at dispatch (step 9a, R5:
   it holds after a crash or a restart), the lower of the two.
-A refusal sends nothing, is logged in `audit_log` in its own transaction (function 'model_call',
-result 'rejected', a fixed code) and raises `SpendingRefused`.
+A refusal sends nothing, is logged in `audit_log` (function 'model_call', result 'rejected', a fixed code,
+the invocation) and raises `SpendingRefused`. Step 9b fix round 1 (finding 1): the audit row is written in the
+same transaction that decides the refusal, so a refusal is reported only once its record is committed (if the
+commit fails, the caller sees a failure to save the call instead); recovery reads that record to keep a refusal a
+stop even when the agent's stage could not be saved.
 
 **After the request** (`finish`): one transaction (a run call takes the run's lock first) finishes
 the call exactly once, with the reported usage and its cost, or as failed with no usage (counted at
@@ -53,6 +56,10 @@ CODES = {
 FINISH_CODES = ("model_auth", "provider_rejected", "provider_unavailable", "cost_unknown")
 
 
+class ClaimLost(Exception):
+    """Step 9b fix round 1 (finding 3): a worker's child no longer holds the run; nothing is reserved or sent."""
+
+
 class SpendingRefused(Exception):
     """No request was sent; the refusal is logged."""
 
@@ -82,11 +89,15 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
         inv = conn.execute(text("SELECT scope, run_id, stage_result_id, role FROM agent_invocation WHERE id = :i"),
                            dict(i=invocation_id)).one_or_none()
         if inv is None:
+            conn.execute(_AUDIT, _refusal_row(invocation_id, None, None, "invocation_unknown", max_cost, ceiling, None))
             return ("refused", "invocation_unknown", None, None, None)
         # Every lock before any total is read (step 8a review, finding 3): the run's lock first (the
         # locking protocol), then the month-wide lock; read in the same order everywhere.
         if inv.scope == "run":
             status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=inv.run_id)).scalar_one()
+            from hypocurate.pipeline.writes import owner_holds
+            if not owner_holds(conn, inv.run_id):  # step 9b fix round 1, finding 3: before any request
+                raise ClaimLost("the run's claim was closed or its work lock is gone")
             stage = actual_stage(conn, inv.run_id, status)
         else:
             stage = "registration"
@@ -107,7 +118,9 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
                 "ceiling_reached" if limit is not None and spent + max_cost > limit else
                 "spending_cap_month" if month + max_cost > MONTH_CAP_USD else None)
         if code:
-            return ("refused", code, inv, stage, {"spent": str(spent), "month": str(month)})
+            totals = {"spent": str(spent), "month": str(month)}
+            conn.execute(_AUDIT, _refusal_row(invocation_id, inv, stage, code, max_cost, ceiling, totals))
+            return ("refused", code, inv, stage, totals)
         call = conn.execute(text(
             "INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
             "VALUES (:r, :s, :i, :o, :m, :p, :c) RETURNING id"),
@@ -118,22 +131,15 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
     outcome = run_transaction(engine, transaction)
     if outcome[0] == "reserved":
         return outcome[1]
-    _, code, inv, stage, totals = outcome
-    _log_refusal(engine, invocation_id, inv, stage, code, max_cost, ceiling, totals)
-    raise SpendingRefused(code)
+    raise SpendingRefused(outcome[1])
 
 
-def _log_refusal(engine, invocation_id, inv, stage, code, max_cost, ceiling, totals) -> None:
+def _refusal_row(invocation_id, inv, stage, code, max_cost, ceiling, totals) -> dict:
     detail = {"result": "rejected", "code": code, "invocation": int(invocation_id), "max_cost": str(max_cost)}
     if ceiling is not None:
         detail["ceiling"] = str(ceiling)
     detail.update(totals or {})
-    row = dict(r=inv.run_id if inv else None, role=inv.role if inv else "invalid", stage=stage or "none", d=detail)
-    try:
-        run_transaction(engine, lambda conn: conn.execute(_AUDIT, row))
-    except Exception as error:  # the process log is the fallback
-        LOG.error(json.dumps({"refusal_fallback": {**row, "function": "model_call"}, "error": type(error).__name__},
-                             sort_keys=True, default=str))
+    return dict(r=inv.run_id if inv else None, role=inv.role if inv else "invalid", stage=stage or "none", d=detail)
 
 
 def finish(engine: Engine, call_id: int, status: str, *, input_tokens: int | None = None,
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
index d918076..62f7307 100644
--- a/hypocurate/pipeline/orchestrator.py
+++ b/hypocurate/pipeline/orchestrator.py
@@ -299,11 +299,13 @@ def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'critic'", run_id):
             c = critic.run_critic(engine, run_id, **agent_kw)
             report.stages.append("critic")
-            failures = c.failures
+            failures, stored = c.failures, False
         else:  # fix round 1, finding 1: the Critic's stored stages decide, as they did when it ran
-            failures = _critic_failures(engine, run_id)
-        # Step 9b (owner, 2026-10-08): after recovery a lost Critic request is not repeated and the run goes on.
-        stops = [f for f in failures if (f in RUN_STOPS or f == LEFT_RUNNING) and not (recovered and f in RECOVERABLE)]
+            failures, stored = _critic_failures(engine, run_id), True
+        # Step 9b (owner, 2026-10-08): after recovery a lost Critic request is not repeated and the run goes on. Fix
+        # round 1, finding 4: only for stages stored before (those recovery processed), never for a Critic run now.
+        excused = recovered and stored
+        stops = [f for f in failures if (f in RUN_STOPS or f == LEFT_RUNNING) and not (excused and f in RECOVERABLE)]
         if stops:
             return _stopped(engine, report, stops[0])
         spent = [f for f in failures if f in SPENDING]
@@ -430,13 +432,19 @@ def work_guarded(payload: dict) -> dict:
     from hypocurate.config import load_settings
     from hypocurate.db.engine import make_engine
     from hypocurate.pipeline import queue
-    engine = make_engine(load_settings(web=False).database_url)
+    engine = make_engine(load_settings(web=False).database_url, worker_session=True)
     run_id = int(payload["run_id"])
     holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
     try:
         holder.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-work-{run_id}"))
         if not holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(run_id))).scalar():
             return {"busy": True}
+        if payload.get("claim_id") is not None:  # step 9b fix round 1, finding 3: the work is bound to this claim
+            from hypocurate.pipeline import writes
+            writes.OWNER = (int(payload["claim_id"]), holder.execute(text("SELECT pg_backend_pid()")).scalar())
+            with engine.connect() as conn:
+                if not writes.owner_holds(conn, run_id):
+                    return {"busy": True}
         phase = {"prepare": prepare, "proceed": proceed}.get(payload.get("phase"), run)
         r = phase(engine, run_id, client_options=payload.get("client_options"),
                   recovered=bool(payload.get("recovered")))
diff --git a/hypocurate/pipeline/queue.py b/hypocurate/pipeline/queue.py
index 5dae406..208b754 100644
--- a/hypocurate/pipeline/queue.py
+++ b/hypocurate/pipeline/queue.py
@@ -20,6 +20,14 @@ first (they are taken up again), then confirmed waiting runs, then queued runs i
 `HEARTBEAT_SECONDS`, on the claim row, never the run row, so it never waits behind the run's lock (a named exception
 to the locking protocol, like audit rows). A release (`release`) follows the protocol.
 
+**Ownership** (fix round 1, finding 3): each beat also confirms that the claim is still open (the update touched its
+row) and that the lease session still holds CLAIM; otherwise `lost` is set and the worker stops its child at once
+(fail closed). The child's own writes and reservations check its claim and its work lock (`writes.owner_holds`).
+**Monitoring** (findings 5 and 6): `Monitor` samples the run's last write on a thread of its own, each query
+time-limited (`MONITOR_TIMEOUT_MS`), and records when it last saw progress; the worker's main thread never waits for
+it, so the whole-run limit and the shutdown check keep their own clock, and the stall allowance counts from the
+attempt's launch (downtime before it does not count) and restarts at each progress seen.
+
 This module is imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
 """
 from __future__ import annotations
@@ -27,6 +35,7 @@ from __future__ import annotations
 import json
 import logging
 import threading
+import time
 from dataclasses import dataclass
 
 from sqlalchemy import Connection, Engine, bindparam, text
@@ -45,6 +54,7 @@ STALL_SECONDS = 900        # A4: no write by the run for this long: the child is
 RUN_TIMEOUT_SECONDS = 1800  # A4: the whole run, as a backstop
 SWEEP_SECONDS = 60         # the worker looks for work this often when idle (and on start)
 LOCK_TIMEOUT_MS = 5000
+MONITOR_TIMEOUT_MS = 5000  # fix round 1, finding 5: a monitoring query is cut off after this
 # Session advisory locks, one per run (the run id in the low 32 bits). Their high words ("HCLA", "HCWR") keep them
 # apart from the single-key locks used elsewhere (spend.MONTH_LOCK_KEY, confirmation.SOURCES_LOCK_KEY, migrate's).
 _CLAIM_NS, _WORK_NS = 0x48434C41, 0x48435752
@@ -70,7 +80,9 @@ class Lease:
     def __init__(self, engine: Engine, run_id: int):
         self.run_id = run_id
         self._conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
-        self._conn.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-lease-{run_id}"))
+        self._conn.execute(text("SELECT set_config('application_name', :a, false), "
+                                "set_config('statement_timeout', :t, false)"),
+                           dict(a=f"hc-lease-{run_id}", t=str(MONITOR_TIMEOUT_MS)))
 
     def try_take(self) -> bool:
         """CLAIM taken, and WORK free (taken and let go at once); False, holding nothing, otherwise."""
@@ -82,10 +94,25 @@ class Lease:
         self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=work_key(self.run_id)))
         return True
 
+    def holds(self) -> bool:
+        """Fix round 1, finding 3: the lease session is alive and still holds CLAIM (taking it again only counts up)."""
+        try:
+            if not self._conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=claim_key(self.run_id))).scalar():
+                return False
+            self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=claim_key(self.run_id)))
+            held = self._conn.execute(text(
+                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted "
+                "AND classid = :c AND objid = :o AND objsubid = 1"),
+                dict(c=_CLAIM_NS, o=int(self.run_id))).scalar()
+            return held >= 1
+        except Exception:  # noqa: BLE001 (the session is gone: the lock is gone with it)
+            return False
+
     def close(self) -> None:
         """Lets go of the lock (by closing the session) and the connection."""
         try:
-            self._conn.execute(text("SELECT pg_advisory_unlock_all(), set_config('application_name', '', false)"))
+            self._conn.execute(text("SELECT pg_advisory_unlock_all(), set_config('application_name', '', false), "
+                                    "set_config('statement_timeout', '0', false)"))
         except Exception:  # noqa: BLE001 (closing the session lets go of it anyway)
             pass
         self._conn.close()
@@ -130,8 +157,8 @@ def _take(engine: Engine, run_id: int, worker: str, stale_seconds: float) -> tup
             conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = 'lost', found = :f "
                               "WHERE id = :c").bindparams(bindparam("f", type_=JSONB)),
                          dict(c=open_claim.id, f={"stale_heartbeat_at": open_claim.heartbeat_at.isoformat()}))
-        cid = conn.execute(text("INSERT INTO run_claim (run_id, worker) VALUES (:r, :w) RETURNING id"),
-                           dict(r=run_id, w=worker)).scalar_one()
+        cid = conn.execute(text("INSERT INTO run_claim (run_id, worker, recovery) VALUES (:r, :w, :rec) RETURNING id"),
+                           dict(r=run_id, w=worker, rec=status == "running")).scalar_one()
         if status == "queued":
             conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=run_id))
         elif status == "waiting":  # confirmed: it goes on (the database requires the confirmation, 0007)
@@ -199,21 +226,31 @@ def release(engine: Engine, c: Claim, reason: str, found: dict | None = None) ->
 
 
 class Heartbeat(threading.Thread):
-    """Writes the claim's heartbeat every `interval` seconds until stopped (R6: on the claim row only)."""
+    """Writes the claim's heartbeat every `interval` seconds until stopped (R6: on the claim row only). With a `lease`
+    and a `lost` event (fix round 1, finding 3), each beat also confirms ownership: the beat touched the open claim's
+    row, and the lease still holds CLAIM. Otherwise `lost` is set (fail closed: the worker stops its child)."""
 
-    def __init__(self, engine: Engine, claim_id: int, interval: float = HEARTBEAT_SECONDS):
+    def __init__(self, engine: Engine, claim_id: int, interval: float = HEARTBEAT_SECONDS, lease: Lease | None = None,
+                 lost: threading.Event | None = None):
         super().__init__(name=f"heartbeat-{claim_id}", daemon=True)
         self._engine, self._claim, self._interval = engine, claim_id, interval
+        self._lease, self.lost = lease, lost or threading.Event()
         self._stop_event = threading.Event()
 
     def run(self) -> None:
         while not self._stop_event.wait(self._interval):
             try:
                 with self._engine.begin() as conn:
-                    conn.execute(text("UPDATE run_claim SET heartbeat_at = clock_timestamp() WHERE id = :c "
-                                      "AND released_at IS NULL"), dict(c=self._claim))
-            except Exception as error:  # noqa: BLE001 (the next beat tries again; a long gap makes the claim stale)
+                    conn.execute(text(f"SET LOCAL statement_timeout = {MONITOR_TIMEOUT_MS}"))
+                    touched = conn.execute(text("UPDATE run_claim SET heartbeat_at = clock_timestamp() WHERE id = :c "
+                                                "AND released_at IS NULL"), dict(c=self._claim)).rowcount
+            except Exception as error:  # noqa: BLE001 (ownership cannot be confirmed: fail closed)
                 LOG.error(json.dumps({"heartbeat_failed": self._claim, "error": type(error).__name__}))
+                touched = 0
+            if touched != 1 or (self._lease is not None and not self._lease.holds()):
+                LOG.error(json.dumps({"ownership_lost": self._claim}))
+                self.lost.set()
+                return
 
     def stop(self) -> None:
         self._stop_event.set()
@@ -233,6 +270,62 @@ _LAST_WRITE = text("""
     FROM run r WHERE r.id = :r""")
 
 
+_LAST_WRITE_EPOCH = text("""
+    SELECT extract(epoch FROM greatest(
+        r.queued_at, r.started_at, r.completed_at, r.failed_at,
+        (SELECT max(greatest(started_at, finished_at)) FROM stage_result WHERE run_id = r.id),
+        (SELECT max(greatest(started_at, finished_at)) FROM model_call WHERE run_id = r.id),
+        (SELECT max(decided_at) FROM run_source WHERE run_id = r.id),
+        (SELECT max(created_at) FROM record WHERE extraction_run_id = r.id),
+        (SELECT max(confirmed_at) FROM rules_confirmation WHERE run_id = r.id),
+        (SELECT locked_at FROM plan WHERE run_id = r.id),
+        (SELECT frozen_at FROM run_snapshot WHERE run_id = r.id)))
+    FROM run r WHERE r.id = :r""")
+
+
+def last_write_epoch(conn: Connection, run_id: int) -> float:
+    """The time (epoch seconds) of the run's last write that shows progress."""
+    return float(conn.execute(_LAST_WRITE_EPOCH, dict(r=run_id)).scalar_one())
+
+
+def sample_last_write(engine: Engine, run_id: int) -> float:
+    """`last_write_epoch` under a time limit (fix round 1, finding 5): a blocked query is cut off, never waited for."""
+    with engine.begin() as conn:
+        conn.execute(text(f"SET LOCAL statement_timeout = {MONITOR_TIMEOUT_MS}"))
+        conn.execute(text(f"SET LOCAL lock_timeout = {MONITOR_TIMEOUT_MS}"))
+        return last_write_epoch(conn, run_id)
+
+
+class Monitor(threading.Thread):
+    """Fix round 1, findings 5 and 6: samples the run's last write off the main thread and records when it last saw
+    progress (`progress_at`, monotonic), starting at the attempt's launch: earlier downtime does not count."""
+
+    def __init__(self, engine: Engine, run_id: int, interval: float = 5.0):
+        super().__init__(name=f"monitor-{run_id}", daemon=True)
+        self._engine, self._run, self._interval = engine, run_id, interval
+        self._stop_event = threading.Event()
+        self.progress_at = time.monotonic()
+        self._last: float | None = None
+
+    def launched(self) -> None:
+        """A child was launched: its allowance starts now."""
+        self.progress_at = time.monotonic()
+
+    def run(self) -> None:
+        while not self._stop_event.is_set():
+            try:
+                seen = sample_last_write(self._engine, self._run)
+                if self._last is not None and seen > self._last:
+                    self.progress_at = time.monotonic()
+                self._last = seen if self._last is None else max(self._last, seen)
+            except Exception:  # noqa: BLE001 (no sample: no progress seen; the allowance keeps running)
+                pass
+            self._stop_event.wait(self._interval)
+
+    def stop(self) -> None:
+        self._stop_event.set()  # never joined: a sample that blocks must not hold back the worker
+
+
 def seconds_since_last_write(conn: Connection, run_id: int) -> float:
     """A4: seconds since the run last wrote anything that shows progress (its status times, a stage or call started or
     finished, a source searched, a record stored, the confirmation, the lock, the freeze)."""
diff --git a/hypocurate/pipeline/recovery.py b/hypocurate/pipeline/recovery.py
index 7fd5346..f327452 100644
--- a/hypocurate/pipeline/recovery.py
+++ b/hypocurate/pipeline/recovery.py
@@ -36,6 +36,8 @@ PLANNER_REPEATS = 1  # owner, Q3
 # save the call. A spending refusal is never among them.
 RECOVERABLE = ("interrupted", "recording_failed", "reservation_failed")
 LOCK_TIMEOUT_MS = 5000
+# The refusals a stage keeps as its cause (spend.CODES; the curation cap never applies to a run).
+SPENDING_CODES = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
 # How an Analyst stage closed by recovery is shown (owner, Q3); tests check it is agents.analyst.UNAVAILABLE's wording.
 ANALYST_INTERRUPTED = "explanation unavailable (interrupted)"
 EXHAUSTED = ("attempts_exhausted: the run stopped at {stage} {n} times without finishing; dispatch it again as a new "
@@ -75,19 +77,33 @@ def recover(engine: Engine, run_id: int) -> dict:
             "SELECT 1 FROM stage_result s WHERE s.id = mc.stage_result_id AND s.status = 'failed' AND "
             "s.output->>'code' = 'recording_failed') THEN 'recording_failed' ELSE 'worker_stopped' END "
             "WHERE mc.run_id = :r AND mc.status = 'started'"), dict(r=run_id)).rowcount
-        stages = conn.execute(text(
+        # Fix round 1, finding 1: a running stage whose request was refused by a spending cap (the refusal's record,
+        # committed with the decision) keeps that cause; only a stage with no such record was interrupted.
+        refused = conn.execute(text(
+            "UPDATE stage_result s SET status = 'failed', finished_at = now(), output = coalesce(s.output, '{}'::jsonb) "
+            "|| jsonb_build_object('code', a.code) || CASE WHEN s.stage = 'analyst' THEN jsonb_build_object('shown', "
+            "'explanation unavailable (' || a.code || ')') ELSE '{}'::jsonb END "
+            "FROM (SELECT DISTINCT ON (i.stage_result_id) i.stage_result_id, al.detail->>'code' AS code "
+            "      FROM agent_invocation i JOIN audit_log al ON al.function = 'model_call' AND NOT al.allowed "
+            "      AND al.detail->>'invocation' = i.id::text AND al.detail->>'code' = ANY(:codes) "
+            "      WHERE i.run_id = :r ORDER BY i.stage_result_id, al.id DESC) a "
+            "WHERE s.id = a.stage_result_id AND s.run_id = :r AND s.status = 'running'"),
+            dict(r=run_id, codes=list(SPENDING_CODES))).rowcount
+        stages = refused + conn.execute(text(
             "UPDATE stage_result SET status = 'failed', finished_at = now(), output = coalesce(output, '{}'::jsonb) "
             "|| jsonb_build_object('code', 'interrupted') || CASE WHEN stage = 'analyst' THEN "
             "jsonb_build_object('shown', CAST(:shown AS text)) ELSE '{}'::jsonb END "
             "WHERE run_id = :r AND status = 'running'"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount
-        earlier = conn.execute(text(
-            "SELECT count(*) FROM run_claim WHERE run_id = :r AND released_at IS NOT NULL "
-            "AND release_reason NOT IN ('waiting', 'finished')"), dict(r=run_id)).scalar_one()
-        found = {"calls_closed": calls, "stages_closed": stages, "recoveries": earlier + 1}
-        if earlier + 1 > MAX_RECOVERIES:
+        # Fix round 1, finding 7: recovery attempts counted explicitly, the claims that took up a running run (this
+        # one included); the first run's claim is not one.
+        attempts = conn.execute(text("SELECT count(*) FROM run_claim WHERE run_id = :r AND recovery"),
+                                dict(r=run_id)).scalar_one()
+        attempts = max(attempts, 1)  # a run taken up with no claim recorded as a recovery (stopped outside a worker)
+        found = {"calls_closed": calls, "stages_closed": stages, "refusals_kept": refused, "recoveries": attempts}
+        if attempts > MAX_RECOVERIES:
             from hypocurate.access.stage import actual_stage
             stage = actual_stage(conn, run_id, status)
-            reason = EXHAUSTED.format(stage=stage.replace("_", " "), n=earlier + 1)
+            reason = EXHAUSTED.format(stage=stage.replace("_", " "), n=attempts)
             conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
                          dict(f=reason, r=run_id))
             found["failed"] = reason
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index 1106be0..d523eee 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -69,7 +69,31 @@ CODES = {
     "narrowed": "code's narrowing decision is partly sufficient: the original question locks no plan",
     # Step 9a (owner, Q1): a run that waited locks only the plan whose fingerprint the person confirmed.
     "not_confirmed": "no person's confirmation of exactly this plan (its fingerprint) before the rules lock",
+    # Step 9b fix round 1 (finding 3): a worker's child whose claim was closed, or whose work lock is gone.
+    "claim_lost": "this process no longer holds the run (its claim was closed or its work lock is gone)",
 }
+# Step 9b fix round 1 (finding 3; owner, 2026-10-09): set in a worker's child to (its claim's id, the backend pid of the
+# session holding its work lock). Every write then checks, in its own transaction after the run's lock, that the claim
+# is still open and that the work lock is still held; otherwise the write is refused `claim_lost`. The claim row is
+# locked FOR KEY SHARE: closing a claim takes FOR UPDATE on its row first (migration 0008's trigger), so a takeover
+# waits for a write in progress, or the write sees the claim closed; the worker's heartbeat (a plain update) does not
+# conflict with it, so a long write never holds back a heartbeat.
+OWNER: tuple[int, int] | None = None
+_WORK_NS = 0x48435752  # queue's work-lock namespace (queue.py imports nothing from here; tests check they agree)
+
+
+def owner_holds(conn: Connection, run_id: int) -> bool:
+    """For a worker's child (`OWNER` set): its claim is open (row locked FOR SHARE) and its work lock still held."""
+    if OWNER is None:
+        return True
+    claim_id, holder_pid = OWNER
+    claim = conn.execute(text("SELECT id FROM run_claim WHERE id = :c AND run_id = :r AND released_at IS NULL "
+                              "FOR KEY SHARE"), dict(c=claim_id, r=run_id)).scalar_one_or_none()
+    if claim is None:
+        return False
+    return bool(conn.execute(text(
+        "SELECT EXISTS (SELECT 1 FROM pg_locks WHERE locktype = 'advisory' AND granted AND pid = :p "
+        "AND classid = :ns AND objid = :r AND objsubid = 1)"), dict(p=holder_pid, ns=_WORK_NS, r=int(run_id))).scalar())
 CONSTRUCTED_MARK = "constructed_test_data"
 # Step 7 (owner, 2026-10-05; register 'constructed_test_runs'): TEST_RUN_LABEL, on every stored
 # result of a marked run, comes from one named place, the database model, whose CHECKs use it.
@@ -125,6 +149,8 @@ def write(engine: Engine, run_id: int, role: str, function: str, body: Callable[
     def transaction(conn: Connection):
         conn.execute(text(f"SET LOCAL lock_timeout = {int(LOCK_TIMEOUT_MS)}"))
         status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        if not owner_holds(conn, run_id):  # step 9b fix round 1, finding 3
+            raise Refused(function, "claim_lost")
         return body(conn, actual_stage(conn, run_id, status))
 
     try:
diff --git a/hypocurate/worker.py b/hypocurate/worker.py
index fafa87b..f804148 100644
--- a/hypocurate/worker.py
+++ b/hypocurate/worker.py
@@ -32,7 +32,7 @@ from hypocurate.pipeline import queue, recovery
 
 log = logging.getLogger("hypocurate.worker")
 CHILD_TARGET = "hypocurate.pipeline.orchestrator:work_guarded"
-WATCH_SECONDS = 1.0  # how often the worker looks at its child
+WATCH_SECONDS = 1.0  # how often the worker looks at its child (and its events)
 
 
 def worker_name() -> str:
@@ -44,65 +44,89 @@ def _status(engine: Engine, run_id: int) -> str:
         return conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
 
 
-def _watch(engine: Engine, run_id: int, child: guarded.GuardedChild, started: float, stop: threading.Event,
-           stall_seconds: float, run_timeout: float) -> str:
-    """'ended', or why the child is to be stopped: 'shutdown', 'run_timeout' or 'stalled'."""
+def _watch(child: guarded.GuardedChild, started: float, stop: threading.Event, lost: threading.Event,
+           monitor: queue.Monitor, stall_seconds: float, run_timeout: float) -> str:
+    """'ended', or why the child is to be stopped: 'shutdown', 'ownership_lost', 'run_timeout' or 'stalled'. Every
+    check is on this thread's own clock or an event (fix round 1, finding 5): the database is read only by the
+    monitor's thread, whose samples are time-limited and never waited for. The stall allowance counts from
+    `monitor.progress_at`: this child's launch, or the last progress the monitor saw since (finding 6)."""
     while True:
         if child.wait_for(WATCH_SECONDS):
             return "ended"
         if stop.is_set():
             return "shutdown"
-        if time.monotonic() - started > run_timeout:
+        if lost.is_set():
+            return "ownership_lost"
+        now = time.monotonic()
+        if now - started > run_timeout:
             return "run_timeout"
-        try:
-            with engine.connect() as conn:
-                quiet = queue.seconds_since_last_write(conn, run_id)
-        except Exception:  # noqa: BLE001 (the database is away: the run limit still applies)
-            continue
-        if quiet > stall_seconds:
+        if now - monitor.progress_at > stall_seconds:
             return "stalled"
 
 
+def _end_child(child: guarded.GuardedChild | None, why: str | None) -> None:
+    """Stops and reaps the child (finding 2): SIGTERM at a shutdown (escalated to SIGKILL if not obeyed), else SIGKILL."""
+    if child is not None and child.alive():
+        child.stop(signal.SIGTERM if why == "shutdown" else signal.SIGKILL)
+    if child is not None:
+        child.discard()
+
+
 def work(engine: Engine, claim: queue.Claim, *, phases=("run",), on_phase: Callable[[str, dict], None] | None = None,
          stop: threading.Event | None = None, stall_seconds: float = queue.STALL_SECONDS,
          run_timeout: float = queue.RUN_TIMEOUT_SECONDS, heartbeat_interval: float = queue.HEARTBEAT_SECONDS,
          client_options: dict | None = None) -> dict[str, Any]:
     """Works one claimed run (from the main thread) and releases its claim; returns the last phase's report, the
-    release reason and, for a stopped child, why."""
+    release reason and, for a stopped child, why. Fix round 1 (finding 2): the claim is released only after the child
+    has been stopped and reaped, on every exit path, and no child is started once shutdown was asked for."""
     stop = stop or threading.Event()
-    beat = queue.Heartbeat(engine, claim.id, interval=heartbeat_interval)
+    lost = threading.Event()
+    beat = queue.Heartbeat(engine, claim.id, interval=heartbeat_interval, lease=claim.lease, lost=lost)
+    monitor = queue.Monitor(engine, claim.run_id, interval=min(5.0, max(0.5, stall_seconds / 4)))
     beat.start()
+    monitor.start()
     started = time.monotonic()
     found: dict | None = None
     report: dict | None = None
+    child: guarded.GuardedChild | None = None
+    reason, why = "child_failed", "error"
     try:
         if claim.status_before == "running":
             found = recovery.recover(engine, claim.run_id) or None
         for i, phase in enumerate(phases):
             if found and found.get("failed"):  # recovery ended the run (attempts exhausted)
                 break
-            child = guarded.start_guarded(CHILD_TARGET, {"run_id": claim.run_id, "phase": phase,
+            if stop.is_set():
+                reason, why = "shutdown", "shutdown"
+                return {"report": report, "release": reason, "why": why}
+            if lost.is_set():
+                reason, why = "lost", "ownership_lost"
+                return {"report": report, "release": reason, "why": why}
+            child = guarded.start_guarded(CHILD_TARGET, {"run_id": claim.run_id, "phase": phase, "claim_id": claim.id,
                                                          "client_options": client_options,
                                                          "recovered": claim.status_before == "running"},
                                           audit=(engine, claim.run_id))
+            monitor.launched()
             if i == 0:
                 queue.record_child(engine, claim, child.pid)
-            why = _watch(engine, claim.run_id, child, started, stop, stall_seconds, run_timeout)
-            if why != "ended":
-                child.stop(signal.SIGTERM if why == "shutdown" else signal.SIGKILL)
-                child.discard()
-                reason = "shutdown" if why == "shutdown" else "child_stuck"
-                queue.release(engine, claim, reason, found)
-                log.warning(json.dumps({"child_stopped": claim.run_id, "why": why}))
+            watched = _watch(child, started, stop, lost, monitor, stall_seconds, run_timeout)
+            if watched != "ended":
+                _end_child(child, watched)
+                child = None
+                reason = {"shutdown": "shutdown", "ownership_lost": "lost"}.get(watched, "child_stuck")
+                why = watched
+                log.warning(json.dumps({"child_stopped": claim.run_id, "why": watched}))
                 return {"report": report, "release": reason, "why": why}
             try:
                 report = child.result(timeout=60)
             except guarded.GuardedRunError:
-                queue.release(engine, claim, "child_failed", found)
-                return {"report": report, "release": "child_failed", "why": "no_answer"}
-            if report.get("busy"):  # another child holds the run's work lock
-                queue.release(engine, claim, "child_failed", found)
-                return {"report": report, "release": "child_failed", "why": "busy"}
+                child = None
+                reason, why = "child_failed", "no_answer"
+                return {"report": report, "release": reason, "why": why}
+            child = None
+            if report.get("busy"):  # another child holds the run's work lock, or the claim is not this child's
+                reason, why = "child_failed", "busy"
+                return {"report": report, "release": reason, "why": why}
             if on_phase:
                 on_phase(phase, report)
             if phase == "prepare" and not report.get("ready"):
@@ -110,16 +134,18 @@ def work(engine: Engine, claim: queue.Claim, *, phases=("run",), on_phase: Calla
         status = _status(engine, claim.run_id)
         reason = ("finished" if status in ("completed", "failed") else "waiting" if status == "waiting"
                   else "stopped_for_recovery")
-        queue.release(engine, claim, reason, found)
-        return {"report": report, "release": reason, "why": None}
-    except BaseException:
-        try:
-            queue.release(engine, claim, "child_failed", found)
-        except Exception:  # noqa: BLE001 (the lease is let go anyway: the claim goes stale)
-            pass
-        raise
+        why = None
+        if lost.is_set():
+            reason, why = "lost", "ownership_lost"
+        return {"report": report, "release": reason, "why": why}
     finally:
+        _end_child(child, "error")  # never release with a live child (finding 2)
         beat.stop()
+        monitor.stop()
+        try:
+            queue.release(engine, claim, reason, found)
+        except Exception:  # noqa: BLE001 (the lease is let go anyway: the claim goes stale)
+            log.error(json.dumps({"release_failed": claim.run_id}))
 
 
 def run(once: bool = False, engine: Engine | None = None, max_cycles: int | None = None,
@@ -128,7 +154,7 @@ def run(once: bool = False, engine: Engine | None = None, max_cycles: int | None
     Each cycle it finishes any narrower question left by a stop (`recovery.finish_narrower_questions`) and claims the
     next run; idle, it logs whether the database answers (never its address) and looks again after `SWEEP_SECONDS`.
     `max_cycles` and `wait` are for tests."""
-    engine = engine or make_engine(load_settings(web=False).database_url)
+    engine = engine or make_engine(load_settings(web=False).database_url, worker_session=True)
     stop = threading.Event()
     wait = wait or stop.wait
     if threading.current_thread() is threading.main_thread():
```
## 3. Tests

### Tests added or changed in this round (diff)

```diff
diff --git a/tests/test_kill_matrix.py b/tests/test_kill_matrix.py
index 5b98609..be364a7 100644
--- a/tests/test_kill_matrix.py
+++ b/tests/test_kill_matrix.py
@@ -318,3 +318,41 @@ def test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run(engine, st
     start_worker("--once")  # restarted: a shutdown claim is claimable at once
     assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
     assert_bookkeeping(engine, rid)
+
+
+def test_a_worker_killed_during_the_critics_first_of_two_batches_skips_the_second(migrated_database, stub, monkeypatch):
+    """Fix round 1 (owner, 2026-10-09): 'mid-Critic, batch 1 of 2'. 110 rows present in both sources raise 110 flags
+    naming two records each; the Critic sends at most 100 per request (its recorded setting), so two batches. The
+    worker is killed during the first; after recovery the second is never sent and the run completes."""
+    import pipeline_world as pw
+    import stub_provider as sp
+    from hypocurate.db.engine import make_engine
+    from stats_world import small_rows
+    from test_critic import SOURCES
+    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
+                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
+        monkeypatch.setenv(k, v)
+    eng = make_engine(migrated_database)
+    with eng.begin() as conn:
+        db = conn.execute(text("SELECT current_database()")).scalar()
+        conn.execute(text(f'ALTER DATABASE "{db}" SET client_connection_check_interval = \'100ms\''))
+    pairs = [pw.mpea_row("CoCrFeNi", 1.0 + i / 10, 5000.0 + i, doi=f"10.1016/j.test.2026.{300 + i}") for i in range(110)]
+    pw.registered_files(eng, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + pairs),
+                              "controlled_duplicates": pw.mpea_csv(pairs)})
+    q = queries.create(eng, to.FCC_CLAIM, SOURCES)
+    queries.submit(eng, q.version_id)
+    queries.confirm_domain(eng, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(eng, q.version_id, fixed_plan=True, constructed_test_data=True)
+    state = kill_on(stub, "classification")
+    proc = start_worker("--once", wait=False)
+    state["pid"] = proc.pid
+    proc.wait(600)
+    assert state["done"]
+    two_or_more = one(eng, "SELECT count(*) FROM flag f WHERE f.run_id = :r AND (SELECT count(*) FROM flag_record fr "
+                           "WHERE fr.flag_id = f.id) >= 2", r=rid)
+    assert two_or_more > 100  # two batches
+    complete(eng, rid)
+    assert one(eng, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
+    assert requests(stub, "classification") == 1  # the second batch was never sent
+    assert_bookkeeping(eng, rid)
+    eng.dispose()
diff --git a/tests/test_recovery_spending.py b/tests/test_recovery_spending.py
new file mode 100644
index 0000000..b3f597d
--- /dev/null
+++ b/tests/test_recovery_spending.py
@@ -0,0 +1,187 @@
+"""Step 9b fix round 1, finding 1 (owner, 2026-10-09): a spending refusal survives a failed save.
+
+A real refusal (the run's ceiling, or the monthly cap) at the Planner or the Critic, then the agent's stage cannot be
+saved (a test-only trigger refuses the update), so the stage stays running and the run stays open. Recovery must
+find the refusal's record and keep it a stop: the run fails `spending_refused`, nothing is repeated or sent, and the
+Analyst is never asked after a Critic refusal; also when the month has changed since (the monthly total no longer
+reaches the cap), since the refusal is what was decided then."""
+from __future__ import annotations
+
+from decimal import Decimal
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate import worker
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import orchestrator, queries, queue
+from hypocurate.pipeline.agents import spend
+from test_worker import engine, stub  # noqa: F401 (fixtures)
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def requests(stub, field):
+    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)
+
+
+def fail_saving(engine, stage):
+    with engine.begin() as conn:
+        conn.execute(text(f"CREATE FUNCTION hc_test_failsave() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
+                          f"IF NEW.stage = '{stage}' AND NEW.status = 'failed' THEN "
+                          f"RAISE EXCEPTION 'test: the stage cannot be saved'; END IF; RETURN NEW; END $$"))
+        conn.execute(text("CREATE TRIGGER zz_hc_test_failsave BEFORE UPDATE ON stage_result FOR EACH ROW "
+                          "EXECUTE FUNCTION hc_test_failsave()"))
+
+
+def allow_saving(engine):
+    with engine.begin() as conn:
+        conn.execute(text("DROP TRIGGER zz_hc_test_failsave ON stage_result"))
+        conn.execute(text("DROP FUNCTION hc_test_failsave()"))
+
+
+def fill_the_month(engine, rid):
+    """Calls of another run that bring this month's counted total to the monthly cap (after dispatch, which the cap
+    would refuse)."""
+    other = to.dispatched(engine, fixed_plan=True)  # another query's run, holding the month's calls
+    queries.start(engine, other)
+    from hypocurate.pipeline.agents.runstage import open_stage
+    _, inv = open_stage(engine, other, "analyst", "analyst")
+    with engine.begin() as conn:
+        for _ in range(int(spend.MONTH_CAP_USD // 2)):
+            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
+                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, "
+                              "'claude-opus-5-5', 'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
+    return other
+
+
+def change_the_month(engine, other):
+    """The month changes: the other run's calls now belong to the previous month (test only, triggers off)."""
+    with engine.begin() as conn:
+        conn.execute(text("ALTER TABLE model_call DISABLE TRIGGER USER"))
+        conn.execute(text("UPDATE model_call SET started_at = started_at - interval '40 days' WHERE run_id = :r"),
+                     dict(r=other))
+        conn.execute(text("ALTER TABLE model_call ENABLE TRIGGER USER"))
+    with engine.connect() as conn:
+        assert spend.month_total(conn) < spend.MONTH_CAP_USD
+
+
+def take_up(engine, rid):
+    c = queue.claim(engine, rid, "test:recovery")
+    assert c is not None and c.status_before == "running"
+    return worker.work(engine, c, heartbeat_interval=0.5)
+
+
+def refused_with_unsaved_stage(engine, stub, stage, rid):
+    """Runs the orchestrator in this process up to the refusal at `stage`, whose failed stage cannot be saved."""
+    fail_saving(engine, stage)
+    try:
+        orchestrator.run(engine, rid, client_options=sp.client_options(stub))
+    except Exception:  # noqa: BLE001 (the save failed; how the run's process ends does not matter here)
+        pass
+    finally:
+        allow_saving(engine)
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = :s ORDER BY id DESC LIMIT 1",
+               r=rid, s=stage) == "running"
+
+
+@pytest.mark.parametrize("cause", ["ceiling", "month", "month_then_changed"])
+def test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery(engine, stub, cause):
+    stub.respond(to.responder(to.planner_body()))
+    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001") if cause == "ceiling" else None)
+    other = fill_the_month(engine, rid) if cause != "ceiling" else None
+    refused_with_unsaved_stage(engine, stub, "planner", rid)
+    if cause == "month_then_changed":
+        change_the_month(engine, other)
+    take_up(engine, rid)
+    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
+    assert requests(stub, "plan") == 0  # never sent, before or after the recovery
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 1
+    assert one(engine, "SELECT output->>'code' FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == (
+        "ceiling_reached" if cause == "ceiling" else "spending_cap_month")
+
+
+@pytest.fixture
+def flagged(migrated_database, monkeypatch, stub):
+    """A marked test run on small constructed data whose flags name two records each (the Critic is asked)."""
+    from stats_world import small_rows
+    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME
+    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
+                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
+        monkeypatch.setenv(k, v)
+    e = make_engine(migrated_database)
+    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
+                            "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
+    yield e
+    e.dispose()
+
+
+@pytest.mark.parametrize("cause", ["month", "month_then_changed"])
+def test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked(flagged, stub, cause):
+    from test_critic import SOURCES
+    engine = flagged
+    stub.respond(to.responder())
+    q = queries.create(engine, to.FCC_CLAIM, SOURCES)
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True)
+    # The month's calls (another marked run of the same query's sources).
+    q2 = queries.create(engine, to.FCC_CLAIM, SOURCES)
+    queries.submit(engine, q2.version_id)
+    queries.confirm_domain(engine, q2.version_id, by="Ada Reviewer")
+    other = queries.dispatch(engine, q2.version_id, fixed_plan=True, constructed_test_data=True)
+    queries.start(engine, other)
+    from hypocurate.pipeline.agents.runstage import open_stage
+    _, inv = open_stage(engine, other, "analyst", "analyst")
+    with engine.begin() as conn:
+        for _ in range(int(spend.MONTH_CAP_USD // 2)):
+            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
+                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, "
+                              "'claude-opus-5-5', 'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
+    refused_with_unsaved_stage(engine, stub, "critic", rid)
+    if cause == "month_then_changed":
+        change_the_month(engine, other)
+    take_up(engine, rid)
+    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
+    assert requests(stub, "classification") == 0 and requests(stub, "report") == 0
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0
+
+
+def test_a_refusal_is_reported_only_once_its_record_is_committed(engine, stub, monkeypatch):
+    """The refusal and its audit record are one transaction: if the record cannot be written, the refusal is not
+    reported as one (the caller sees a failure to save the call instead)."""
+    from hypocurate.pipeline.agents.runstage import open_stage
+    stub.respond(to.responder())
+    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001"))
+    queries.start(engine, rid)
+    _, inv = open_stage(engine, rid, "planner", "planner")
+    with pytest.raises(spend.SpendingRefused):
+        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
+    assert one(engine, "SELECT count(*) FROM audit_log WHERE function = 'model_call' AND NOT allowed AND "
+                       "detail->>'invocation' = :i AND detail->>'code' = 'ceiling_reached'", i=str(inv)) == 1
+    with engine.begin() as conn:
+        conn.execute(text("CREATE FUNCTION hc_test_noaudit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
+                          "RAISE EXCEPTION 'test: no audit row'; END $$"))
+        conn.execute(text("CREATE TRIGGER zz_hc_test_noaudit BEFORE INSERT ON audit_log FOR EACH ROW "
+                          "EXECUTE FUNCTION hc_test_noaudit()"))
+    try:
+        with pytest.raises(Exception) as raised:
+            spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
+        assert not isinstance(raised.value, spend.SpendingRefused)
+    finally:
+        with engine.begin() as conn:
+            conn.execute(text("DROP TRIGGER zz_hc_test_noaudit ON audit_log"))
+            conn.execute(text("DROP FUNCTION hc_test_noaudit()"))
diff --git a/tests/test_worker_fix1.py b/tests/test_worker_fix1.py
new file mode 100644
index 0000000..0121db8
--- /dev/null
+++ b/tests/test_worker_fix1.py
@@ -0,0 +1,394 @@
+"""Step 9b fix round 1, findings 2 to 7 (owner, 2026-10-09; docs/reviews/step09b_plan.md, "Fix round 1").
+
+2. Never release a claim with a live child: on every exit path the child is stopped and reaped first; a SIGTERM that
+   does not work is escalated to SIGKILL; no child is started once shutdown was asked for.
+3. Losing the lock means stopping: the worker fails closed when its lease session is lost; the child's work is bound
+   to its claim (checked in each write's own transaction, the claim row locked FOR SHARE; and before a reservation),
+   so a stale owner is refused before any further request or write.
+4. The recovery exception applies only to stages stored before: a failure of a Critic run after recovery stops.
+5. Monitoring cannot block the watchdog: monitoring queries are time-limited and run off the main thread; the
+   whole-run kill and the shutdown check do not wait for them.
+6. The stall allowance starts at the attempt's launch: downtime before it does not count.
+7. Recovery attempts are counted explicitly (claims that took up a running run), excluding the first run."""
+from __future__ import annotations
+
+import signal
+import subprocess
+import sys
+import tempfile
+import threading
+import time
+
+import pytest
+from sqlalchemy import text
+
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate import worker
+from hypocurate.access import guarded
+from hypocurate.pipeline import queries, queue, recovery, writes
+from test_guarded_parent import gone
+from test_kill_matrix import STALL_KEY, sleeping, stall, unstall
+from test_worker import engine, stub, wait_until  # noqa: F401 (fixtures)
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def requests(stub, field):
+    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)
+
+
+def fixed_run(engine, stub):
+    stub.respond(to.responder())
+    return to.dispatched(engine, fixed_plan=True)
+
+
+# --- finding 2 --------------------------------------------------------------------------------------------
+
+def test_a_failure_after_the_child_started_stops_and_reaps_it_before_the_claim_is_released(engine, stub, monkeypatch):
+    rid = fixed_run(engine, stub)
+    started, at_release = [], []
+    real_start, real_release = guarded.start_guarded, queue.release
+
+    def start(*a, **k):
+        child = real_start(*a, **k)
+        started.append(child)
+        return child
+
+    def record_child(*a, **k):
+        raise RuntimeError("the claim row could not be written")
+
+    def release(engine_, claim, reason, found=None):
+        at_release.append((reason, [gone(c.pid) for c in started]))
+        return real_release(engine_, claim, reason, found)
+
+    monkeypatch.setattr(guarded, "start_guarded", start)
+    monkeypatch.setattr(queue, "record_child", record_child)
+    monkeypatch.setattr(queue, "release", release)
+    c = queue.claim(engine, rid, "test:f2")
+    with pytest.raises(RuntimeError):
+        worker.work(engine, c, heartbeat_interval=0.5)
+    assert started and at_release == [("child_failed", [True])]  # the child was gone before the release
+
+
+def test_a_child_that_ignores_sigterm_is_killed(tmp_path):
+    proc = subprocess.Popen([sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, "
+                             "signal.SIG_IGN); print('ready', flush=True); time.sleep(120)"],
+                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
+    assert proc.stdout.readline().strip() == "ready"
+    child = guarded.GuardedChild(proc, tempfile.mkdtemp(dir=tmp_path), None)
+    started = time.time()
+    child.stop(signal.SIGTERM)
+    assert proc.poll() is not None and proc.returncode == -signal.SIGKILL
+    assert time.time() - started < guarded.STOP_GRACE_SECONDS + 5
+
+
+def test_no_child_is_started_once_shutdown_was_asked_for(engine, stub, monkeypatch):
+    rid = fixed_run(engine, stub)
+
+    def start(*a, **k):
+        raise AssertionError("a child was started after shutdown")
+
+    monkeypatch.setattr(guarded, "start_guarded", start)
+    stop = threading.Event()
+    stop.set()
+    c = queue.claim(engine, rid, "test:f2")
+    out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
+    assert out["release"] == "shutdown"
+    assert one(engine, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == "shutdown"
+
+
+# --- finding 3 --------------------------------------------------------------------------------------------
+
+def terminate(engine, application_name):
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity WHERE application_name "
+                                 "= :a AND datname = current_database()"), dict(a=application_name)).scalar()
+
+
+def test_losing_the_lease_session_stops_the_child_and_gives_up_the_run(engine, stub):
+    """The lease's lock session is terminated while the worker and its child stay alive."""
+    rid = fixed_run(engine, stub)
+    holder = stall(engine, "run_snapshot")
+    try:
+        c = queue.claim(engine, rid, "test:f3")
+        threading.Thread(target=lambda: (wait_until(lambda: sleeping(engine), 60),
+                                         terminate(engine, f"hc-lease-{rid}")), daemon=True).start()
+        out = worker.work(engine, c, heartbeat_interval=0.3)
+        assert out["why"] == "ownership_lost"
+        pid = one(engine, "SELECT child_pid FROM run_claim WHERE id = :c", c=c.id)
+        assert wait_until(lambda: gone(pid), 5)
+        assert one(engine, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == "lost"
+        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    finally:
+        unstall(engine, "run_snapshot", holder)
+
+
+def test_losing_the_work_session_refuses_the_childs_next_write(engine, stub):
+    """The child's work-lock session is terminated while the child stays alive: its next write is refused."""
+    rid = fixed_run(engine, stub)
+    holder = stall(engine, "run_snapshot")
+    try:
+        c = queue.claim(engine, rid, "test:f3w")
+
+        def cut():
+            wait_until(lambda: sleeping(engine), 60)
+            terminate(engine, f"hc-work-{rid}")
+            time.sleep(0.5)
+            holder.execute(text("SELECT pg_advisory_unlock_all()"))  # the stalled write goes on; the next one is refused
+
+        threading.Thread(target=cut, daemon=True).start()
+        worker.work(engine, c, heartbeat_interval=0.3)
+        assert one(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r AND detail->>'code' = 'claim_lost'",
+                   r=rid) >= 1
+        assert one(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
+        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    finally:
+        unstall(engine, "run_snapshot", holder)
+
+
+def owned(engine, rid):
+    """This process acting as a run's child: a claim, and the work lock held on a session of its own."""
+    queries.start(engine, rid)
+    c = queue.claim(engine, rid, "test:owner")
+    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
+    assert holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
+    pid = holder.execute(text("SELECT pg_backend_pid()")).scalar()
+    return c, holder, pid
+
+
+def test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused(engine, stub, monkeypatch):
+    """Two connections: a child's write holds its claim row (FOR SHARE) while it works; a takeover closing the claim
+    waits for that write to commit; the child's next write sees the closed claim and is refused."""
+    rid = to.dispatched(engine, fixed_plan=True)
+    c, holder, pid = owned(engine, rid)
+    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
+    done = {}
+
+    def slow_write():
+        def body(conn, _stage):
+            # The database's time at the end of the write's work, just before its commit.
+            done["body_end"] = conn.execute(text("SELECT pg_sleep(2), clock_timestamp()")).one()[1]
+        writes.write(engine, rid, "test", "slow", body)
+
+    t = threading.Thread(target=slow_write)
+    t.start()
+    time.sleep(0.5)
+    started = time.monotonic()
+    with engine.begin() as conn:  # the takeover's close of the claim (without the run's lock: the claim row decides)
+        conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = 'lost' WHERE id = :c"),
+                     dict(c=c.id))
+    waited = time.monotonic() - started
+    t.join(10)
+    # It waited for the write: the close took at least 1 s (the write held the row about 1.5 s more), and the claim's
+    # release time (the database's clock, set once the trigger has the row) is after the end of the write's work.
+    assert waited >= 1.0
+    assert one(engine, "SELECT released_at FROM run_claim WHERE id = :c", c=c.id) >= done["body_end"]
+    with pytest.raises(writes.Refused) as refused:
+        writes.write(engine, rid, "test", "next", lambda conn, _s: None)
+    assert refused.value.code == "claim_lost"
+    holder.invalidate()
+    c.lease.close()
+
+
+def test_a_write_is_refused_once_the_work_lock_session_is_gone(engine, stub, monkeypatch):
+    rid = to.dispatched(engine, fixed_plan=True)
+    c, holder, pid = owned(engine, rid)
+    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
+    writes.write(engine, rid, "test", "first", lambda conn, _s: None)  # owned: allowed
+    holder.invalidate()  # the work lock's session ends (a close would only return it to the pool, lock and all)
+    with pytest.raises(writes.Refused) as refused:
+        writes.write(engine, rid, "test", "second", lambda conn, _s: None)
+    assert refused.value.code == "claim_lost"
+    c.lease.close()
+
+
+def test_a_stale_owner_is_refused_before_its_reservation(engine, stub, monkeypatch):
+    from decimal import Decimal
+    from hypocurate.pipeline.agents import spend
+    from hypocurate.pipeline.agents.runstage import open_stage
+    rid = to.dispatched(engine, fixed_plan=True)
+    c, holder, pid = owned(engine, rid)
+    monkeypatch.setattr(writes, "OWNER", (c.id, pid))
+    _, inv = open_stage(engine, rid, "analyst", "analyst")
+    queue.release(engine, c, "lost")  # taken over
+    with pytest.raises(spend.ClaimLost):
+        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.01"))
+    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 0
+    holder.invalidate()
+
+
+# --- finding 4 --------------------------------------------------------------------------------------------
+
+def test_a_critic_run_after_recovery_that_fails_to_record_its_call_stops_the_run(migrated_database, stub, monkeypatch):
+    import pipeline_world as pw
+    from hypocurate.db.engine import make_engine
+    from hypocurate.pipeline import checkpoints, checks, confirmation, extract
+    from stats_world import small_rows
+    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME, SOURCES
+    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
+                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
+        monkeypatch.setenv(k, v)
+    e = make_engine(migrated_database)
+    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
+                            "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
+    stub.respond(to.responder())
+    q = queries.create(e, to.FCC_CLAIM, SOURCES)
+    queries.submit(e, q.version_id)
+    queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(e, q.version_id, fixed_plan=True, constructed_test_data=True)
+    queries.start(e, rid)
+    with e.connect() as conn:
+        checkpoints.lock_rules(e, rid, confirmation.plan_to_lock(conn, rid))
+    extract.store_records(e, rid)
+    checks.run_checks(e, rid)  # the stop: before the Critic
+    with e.begin() as conn:  # the Critic's call cannot be recorded (a test-only trigger)
+        conn.execute(text("CREATE FUNCTION hc_test_norecord() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
+                          "RAISE EXCEPTION 'test: the call cannot be recorded'; END $$"))
+        conn.execute(text("CREATE TRIGGER zz_hc_test_norecord BEFORE UPDATE ON model_call FOR EACH ROW "
+                          "EXECUTE FUNCTION hc_test_norecord()"))
+    try:
+        c = queue.claim(e, rid, "test:f4")
+        assert c.status_before == "running"  # taken up: recovered
+        worker.work(e, c, heartbeat_interval=0.5)
+    finally:
+        with e.begin() as conn:
+            conn.execute(text("DROP TRIGGER zz_hc_test_norecord ON model_call"))
+            conn.execute(text("DROP FUNCTION hc_test_norecord()"))
+    assert requests(stub, "classification") >= 1
+    assert requests(stub, "report") == 0  # stopped: no Analyst
+    assert one(e, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+    assert one(e, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0
+    e.dispose()
+
+
+# --- findings 5 and 6 ----------------------------------------------------------------------------------------
+
+BLOCKED_SECONDS = 60  # far beyond each test's limit; bounded so a watchdog that waits on it fails, not hangs
+
+
+def blocked_monitoring(monkeypatch):
+    never = threading.Event()
+    monkeypatch.setattr(queue, "last_write_epoch", lambda conn, run_id: never.wait(BLOCKED_SECONDS))
+
+
+def test_a_blocked_monitoring_query_does_not_hold_back_the_whole_run_limit(engine, stub, monkeypatch):
+    rid = fixed_run(engine, stub)
+    holder = stall(engine, "run_snapshot")
+    blocked_monitoring(monkeypatch)
+    try:
+        c = queue.claim(engine, rid, "test:f5")
+        started = time.monotonic()
+        out = worker.work(engine, c, run_timeout=3, stall_seconds=10 ** 6, heartbeat_interval=0.5)
+        assert out["why"] == "run_timeout" and time.monotonic() - started < 15
+    finally:
+        unstall(engine, "run_snapshot", holder)
+
+
+def test_a_blocked_monitoring_query_does_not_hold_back_shutdown(engine, stub, monkeypatch):
+    rid = fixed_run(engine, stub)
+    holder = stall(engine, "run_snapshot")
+    blocked_monitoring(monkeypatch)
+    try:
+        c = queue.claim(engine, rid, "test:f5s")
+        stop = threading.Event()
+        threading.Timer(3, stop.set).start()
+        started = time.monotonic()
+        out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
+        assert out["release"] == "shutdown" and time.monotonic() - started < 3 + guarded.STOP_GRACE_SECONDS + 5
+    finally:
+        unstall(engine, "run_snapshot", holder)
+
+
+def test_the_monitoring_query_is_time_limited(engine, stub):
+    rid = fixed_run(engine, stub)
+    with engine.connect() as locker:
+        tx = locker.begin()
+        locker.execute(text("LOCK TABLE stage_result IN ACCESS EXCLUSIVE MODE"))
+        # On a thread, so a sample with no time limit fails this test instead of hanging the suite.
+        result = {}
+
+        def sample():
+            try:
+                queue.sample_last_write(engine, rid)
+                result["outcome"] = "returned"
+            except Exception as e:  # noqa: BLE001 (the timeout's error is the expected outcome)
+                result["outcome"] = e
+        started = time.monotonic()
+        t = threading.Thread(target=sample, daemon=True)
+        t.start()
+        t.join(queue.MONITOR_TIMEOUT_MS / 1000 + 3)
+        alive = t.is_alive()
+        tx.rollback()  # releases a sample still waiting
+        t.join(10)
+        assert not alive, "the monitoring query waited past its time limit"
+        assert isinstance(result.get("outcome"), Exception)
+        assert time.monotonic() - started < queue.MONITOR_TIMEOUT_MS / 1000 + 13
+
+
+def test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance(engine, stub):
+    """A run stopped after its lock, idle for longer than the allowance, then taken up: the new child gets the full
+    allowance from its launch and completes."""
+    from hypocurate.pipeline import checkpoints, confirmation
+    rid = fixed_run(engine, stub)
+    queries.start(engine, rid)
+    with engine.connect() as conn:
+        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
+    time.sleep(7)  # idle: longer than the allowance below
+    c = queue.claim(engine, rid, "test:f6")
+    out = worker.work(engine, c, stall_seconds=6, heartbeat_interval=0.5)
+    assert out["release"] == "finished" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
+
+
+# --- finding 7 --------------------------------------------------------------------------------------------
+
+def test_three_recoveries_are_allowed_and_the_fourth_is_refused_with_real_claim_histories(engine, stub):
+    """Each attempt is a real claim worked by the worker's code and stopped by a shutdown while its child is held at
+    the freeze; the first claim (from queued) is the first run, not a recovery."""
+    rid = fixed_run(engine, stub)
+    holder = stall(engine, "run_snapshot")
+    try:
+        for attempt in range(1 + recovery.MAX_RECOVERIES):  # the first run, then three recoveries
+            c = queue.claim(engine, rid, f"test:{attempt}")
+            assert c is not None and c.status_before == ("queued" if attempt == 0 else "running")
+            stop = threading.Event()
+            threading.Thread(target=lambda: (wait_until(lambda: sleeping(engine), 60), stop.set()), daemon=True).start()
+            out = worker.work(engine, c, stop=stop, heartbeat_interval=0.5)
+            assert out["release"] == "shutdown", attempt
+            assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+        c = queue.claim(engine, rid, "test:4")  # the fourth recovery
+        worker.work(engine, c, heartbeat_interval=0.5)
+    finally:
+        unstall(engine, "run_snapshot", holder)
+    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith(
+        f"attempts_exhausted: the run stopped at curation {recovery.MAX_RECOVERIES + 1} times without finishing")
+    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r AND recovery", r=rid) == 4
+
+
+# --- the owner's addition: worker sessions notice a client that is gone ------------------------------------------
+
+def test_worker_sessions_check_for_a_lost_client_every_second_with_tcp_keepalives(migrated_database):
+    from hypocurate.db.engine import WORKER_SESSION, make_engine
+    e = make_engine(migrated_database, worker_session=True)
+    with e.connect() as conn:
+        shown = {k: conn.execute(text(f"SHOW {k}")).scalar() for k in
+                 ("client_connection_check_interval", "tcp_keepalives_idle", "tcp_keepalives_interval",
+                  "tcp_keepalives_count")}
+    e.dispose()
+    assert shown == {"client_connection_check_interval": "1s", "tcp_keepalives_idle": "30",
+                     "tcp_keepalives_interval": "10", "tcp_keepalives_count": "3"}
+    assert WORKER_SESSION["client_connection_check_interval"] == "1s"
+    plain = make_engine(migrated_database)
+    with plain.connect() as conn:
+        assert conn.execute(text("SHOW client_connection_check_interval")).scalar() == "0"
+    plain.dispose()
+
+
+def test_the_worker_and_its_child_use_worker_sessions():
+    import inspect
+    from hypocurate.pipeline import orchestrator
+    assert "worker_session=True" in inspect.getsource(worker.run)
+    assert "worker_session=True" in inspect.getsource(orchestrator.work_guarded)
```

### Changed expectations

No existing assertion changed. `test_kill_matrix.py` gains the two-batch Critic case and a stall helper that returns its lock holder; its other cases are unchanged.

Three of this round's own tests were changed after they were first written:
- `test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused` (`a9251d2`, the owner's approval): its check compared two Python clock readings, which can come in either order by scheduling chance (one failure in the whole suite). It now checks the wait itself, on the takeover's clock and on the database's.
- `test_the_monitoring_query_is_time_limited` and `blocked_monitoring` (`641af6b`): they fail instead of hanging on f14 and f15. No assertion changed.

### The tests of this round on the reviewed code (`368a426`'s package, scratch copy, `PYTHONPATH`)

Run from a directory with no `hypocurate` package: the worker tests start `python -m hypocurate.worker`, and `-m` puts the current directory first, so a run from the repository would start the worker on the new code (a first attempt did, and was discarded).

```
FAILED tests/test_recovery_spending.py::test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery[ceiling]
FAILED tests/test_recovery_spending.py::test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery[month]
FAILED tests/test_recovery_spending.py::test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery[month_then_changed]
FAILED tests/test_recovery_spending.py::test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked[month]
FAILED tests/test_recovery_spending.py::test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked[month_then_changed]
FAILED tests/test_recovery_spending.py::test_a_refusal_is_reported_only_once_its_record_is_committed
FAILED tests/test_worker_fix1.py::test_a_failure_after_the_child_started_stops_and_reaps_it_before_the_claim_is_released
FAILED tests/test_worker_fix1.py::test_a_child_that_ignores_sigterm_is_killed
FAILED tests/test_worker_fix1.py::test_no_child_is_started_once_shutdown_was_asked_for
FAILED tests/test_worker_fix1.py::test_losing_the_lease_session_stops_the_child_and_gives_up_the_run
FAILED tests/test_worker_fix1.py::test_losing_the_work_session_refuses_the_childs_next_write
FAILED tests/test_worker_fix1.py::test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused
FAILED tests/test_worker_fix1.py::test_a_write_is_refused_once_the_work_lock_session_is_gone
FAILED tests/test_worker_fix1.py::test_a_stale_owner_is_refused_before_its_reservation
FAILED tests/test_worker_fix1.py::test_a_critic_run_after_recovery_that_fails_to_record_its_call_stops_the_run
FAILED tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_the_whole_run_limit
FAILED tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_shutdown
FAILED tests/test_worker_fix1.py::test_the_monitoring_query_is_time_limited
FAILED tests/test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance
FAILED tests/test_worker_fix1.py::test_three_recoveries_are_allowed_and_the_fourth_is_refused_with_real_claim_histories
FAILED tests/test_worker_fix1.py::test_worker_sessions_check_for_a_lost_client_every_second_with_tcp_keepalives
FAILED tests/test_worker_fix1.py::test_the_worker_and_its_child_use_worker_sessions
22 failed, 1 passed, 1 warning in 165.77s (0:02:45)
```
## 4. The register (148 entries; 5 changed in this round)

Entries new on this unmerged branch are corrected in place (their reviewed wording is shown here); `spending_caps`, on `main`, keeps its earlier wording in its history.

### `spending_caps`

Before (`368a426`):

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one stored on the run at dispatch, which holds after a crash or a restart), is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. Every run dispatched after migration 0007 stores its ceiling: the one given at dispatch, or else the per-run cap (the owner's decision, 2026-10-08; the column's default, and an insert trigger that replaces an explicit NULL, so even direct SQL cannot store a new run without one; runs before 0007 keep none). The ceiling is set only at dispatch; `confirm` takes none. The monthly cap counts the calls recorded in this database only. At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
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
   },
   {
    "ref": "sql:hc_run_ceiling"
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
  "tests/test_cli_step9a.py::test_confirm_takes_no_ceiling",
  "tests/test_migrations_step9a.py::test_an_explicit_null_ceiling_on_a_new_run_stores_the_run_cap"
 ]
}
```

Now:

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one stored on the run at dispatch, which holds after a crash or a restart), is not sent, and the refusal is logged in the same transaction that decides it: a refusal is reported only once its record is committed (otherwise the caller sees a failure to save the call). So two concurrent reservations can never both pass the same cap or ceiling. Every run dispatched after migration 0007 stores its ceiling: the one given at dispatch, or else the per-run cap (the owner's decision, 2026-10-08; the column's default, and an insert trigger that replaces an explicit NULL, so even direct SQL cannot store a new run without one; runs before 0007 keep none). The ceiling is set only at dispatch; `confirm` takes none. The monthly cap counts the calls recorded in this database only. At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
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
  "date": "2026-10-09"
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
   },
   {
    "ref": "sql:hc_run_ceiling"
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
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one stored on the run at dispatch, which holds after a crash or a restart), is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. Every run dispatched after migration 0007 stores its ceiling: the one given at dispatch, or else the per-run cap (the owner's decision, 2026-10-08; the column's default, and an insert trigger that replaces an explicit NULL, so even direct SQL cannot store a new run without one; runs before 0007 keep none). The ceiling is set only at dispatch; `confirm` takes none. The monthly cap counts the calls recorded in this database only. At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
   "from": "2026-10-08",
   "to": "2026-10-09",
   "note": "Step 9b fix round 1 (owner, 2026-10-09, finding 1): the refusal's record is written in the transaction that decides it."
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
  "tests/test_cli_step9a.py::test_confirm_takes_no_ceiling",
  "tests/test_migrations_step9a.py::test_an_explicit_null_ceiling_on_a_new_run_stores_the_run_cap",
  "tests/test_recovery_spending.py::test_a_refusal_is_reported_only_once_its_record_is_committed"
 ]
}
```
### `queue_and_claims`

Before (`368a426`):

```json
{
 "key": "queue_and_claims",
 "name": "The queue: claims and the heartbeat",
 "state": "in_force",
 "statement": "A worker claims one run at a time: on its own autocommit lease connection it takes, without waiting, a session advisory lock on the run (CLAIM) and checks that the run's WORK lock is free; then, in one transaction under the run's lock, it re-checks the run, closes a stale open claim as 'lost', records its claim (run_claim; one open claim per run) and starts the run (queued, or a confirmed waiting run, becomes running). The guarded child holds the run's WORK lock for its whole work; an orphan child holding it keeps every worker off the run. A claim's heartbeat is written every 15 seconds by a thread of the worker on the claim row, never the run row, so it never waits behind the run's lock (a named exception to the locking protocol, like audit rows). A claim is taken to be dead when its heartbeat is older than 120 seconds; a claim released for recovery or at shutdown is claimable at once. Running runs are taken up first, then confirmed waiting runs, then queued runs in the order of dispatch. The worker parent never imports dspy, litellm or scipy (it does load numpy, through the source adapters' spreadsheet library).",
 "value": {
  "text": "heartbeat 15 s; dead after 120 s",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Every run worked by the worker or the command line (PRD 8 'Queue', 'Restart').",
 "reason": "PRD 8; the owner's approval of R6 and of the claims design (step 9 plan).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.queue:HEARTBEAT_SECONDS",
    "equals": 15
   },
   {
    "ref": "python:hypocurate.pipeline.queue:STALE_SECONDS",
    "equals": 120
   },
   {
    "ref": "python:hypocurate.pipeline.queue:RELEASE_REASONS",
    "equals": [
     "finished",
     "waiting",
     "stopped_for_recovery",
     "child_failed",
     "child_stuck",
     "shutdown",
     "lost"
    ]
   },
   {
    "ref": "sql:uq_run_claim_open"
   },
   {
    "ref": "sql:hc_run_claim_update"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queue.py::test_two_workers_never_hold_one_run",
  "tests/test_queue.py::test_claims_at_the_same_moment_give_the_run_to_one_worker",
  "tests/test_queue.py::test_a_run_whose_work_lock_is_held_by_an_orphan_child_is_not_claimed",
  "tests/test_queue.py::test_a_running_run_with_a_live_claim_is_left_alone_and_a_stale_one_is_taken_over",
  "tests/test_migrations_step9b.py::test_the_heartbeat_is_the_databases_time_and_needs_no_run_lock",
  "tests/test_worker.py::test_two_workers_and_one_run_give_one_claim_and_no_repeated_request",
  "tests/test_worker.py::test_the_worker_parent_loads_no_model_or_statistics_library"
 ],
 "history": [],
 "notes": [
  "Measured on 0.5 CPU / 512 MB in the runtime image (2026-10-08): worker parent peak 78.8 MiB; guarded child 387.9 MiB; the container's cgroup peak reached its 512 MiB limit (it counts reclaimable file cache). The upgrade (1c-2g) is the owner's decision (Q2)."
 ]
}
```

Now:

```json
{
 "key": "queue_and_claims",
 "name": "The queue: claims and the heartbeat",
 "state": "in_force",
 "statement": "A worker claims one run at a time: on its own autocommit lease connection it takes, without waiting, a session advisory lock on the run (CLAIM) and checks that the run's WORK lock is free; then, in one transaction under the run's lock, it re-checks the run, closes a stale open claim as 'lost', records its claim (run_claim; one open claim per run) and starts the run (queued, or a confirmed waiting run, becomes running). The guarded child holds the run's WORK lock for its whole work; an orphan child holding it keeps every worker off the run. A claim's heartbeat is written every 15 seconds by a thread of the worker on the claim row, never the run row, so it never waits behind the run's lock (a named exception to the locking protocol, like audit rows). Each beat also confirms ownership: the beat touched the open claim's row and the lease session still holds CLAIM; otherwise the worker stops its child at once and gives the run up ('lost'). The child's work is bound to its claim: every write checks, in its own transaction after the run's lock, that the claim is open (its row locked FOR KEY SHARE; closing a claim locks the row FOR UPDATE first, so a takeover waits for a write in progress or the write sees the claim closed) and that the child's work lock is still held; a reservation checks the same before any request. A stale owner is refused ('claim_lost') before any further write or request (fix round 1, finding 3). A claim is taken to be dead when its heartbeat is older than 120 seconds; a claim released for recovery or at shutdown is claimable at once. Running runs are taken up first, then confirmed waiting runs, then queued runs in the order of dispatch. The worker parent never imports dspy, litellm or scipy (it does load numpy, through the source adapters' spreadsheet library).",
 "value": {
  "text": "heartbeat 15 s; dead after 120 s",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Every run worked by the worker or the command line (PRD 8 'Queue', 'Restart').",
 "reason": "PRD 8; the owner's approval of R6 and of the claims design (step 9 plan).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.queue:HEARTBEAT_SECONDS",
    "equals": 15
   },
   {
    "ref": "python:hypocurate.pipeline.queue:STALE_SECONDS",
    "equals": 120
   },
   {
    "ref": "python:hypocurate.pipeline.queue:RELEASE_REASONS",
    "equals": [
     "finished",
     "waiting",
     "stopped_for_recovery",
     "child_failed",
     "child_stuck",
     "shutdown",
     "lost"
    ]
   },
   {
    "ref": "sql:uq_run_claim_open"
   },
   {
    "ref": "sql:hc_run_claim_update"
   },
   {
    "ref": "python:hypocurate.pipeline.writes:owner_holds"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queue.py::test_two_workers_never_hold_one_run",
  "tests/test_queue.py::test_claims_at_the_same_moment_give_the_run_to_one_worker",
  "tests/test_queue.py::test_a_run_whose_work_lock_is_held_by_an_orphan_child_is_not_claimed",
  "tests/test_queue.py::test_a_running_run_with_a_live_claim_is_left_alone_and_a_stale_one_is_taken_over",
  "tests/test_migrations_step9b.py::test_the_heartbeat_is_the_databases_time_and_needs_no_run_lock",
  "tests/test_worker.py::test_two_workers_and_one_run_give_one_claim_and_no_repeated_request",
  "tests/test_worker.py::test_the_worker_parent_loads_no_model_or_statistics_library",
  "tests/test_worker_fix1.py::test_losing_the_lease_session_stops_the_child_and_gives_up_the_run",
  "tests/test_worker_fix1.py::test_losing_the_work_session_refuses_the_childs_next_write",
  "tests/test_worker_fix1.py::test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused",
  "tests/test_worker_fix1.py::test_a_stale_owner_is_refused_before_its_reservation"
 ],
 "history": [],
 "notes": [
  "Measured on 0.5 CPU / 512 MB in the runtime image (2026-10-08): worker parent peak 78.8 MiB; guarded child 387.9 MiB; the container's cgroup peak reached its 512 MiB limit (it counts reclaimable file cache). The upgrade (1c-2g) is the owner's decision (Q2)."
 ]
}
```
### `stuck_child_limits`

Before (`368a426`):

```json
{
 "key": "stuck_child_limits",
 "name": "A stuck child",
 "state": "in_force",
 "statement": "The worker kills its child, releases the claim as 'child_stuck' and lets recovery take the run up when the run has written nothing (a status change, a stage or call started or finished, a source searched, a record stored, the confirmation, the lock, the freeze) for 900 seconds, or after 1,800 seconds in all. 900 seconds covers one agent call's two requests at the 300-second request timeout plus 300 seconds of margin. A deploy (SIGTERM) stops the child and releases the claim as 'shutdown'.",
 "value": {
  "text": "900 s without a write; 1,800 s in all",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Every run worked by the worker.",
 "reason": "Owner's addition A4 (step 9 plan). Live runs took 10-41 s; on 0.5 CPU a fixed-plan run took 21.1 s, the statistics stage 3.2 s at 2,000 simulations and 8.7 s at 10,000 (measured 2026-10-08).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.queue:STALL_SECONDS",
    "equals": 900
   },
   {
    "ref": "python:hypocurate.pipeline.queue:RUN_TIMEOUT_SECONDS",
    "equals": 1800
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:DEFAULT_TIMEOUT_SECONDS",
    "equals": 300
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_worker.py::test_a_stuck_child_is_stopped_and_its_claim_released_for_recovery",
  "tests/test_worker.py::test_the_whole_run_limit_stops_a_child_that_keeps_writing_too_long",
  "tests/test_worker.py::test_sigterm_shuts_the_worker_down_releasing_its_claim_and_stopping_its_child",
  "tests/test_queue.py::test_the_time_since_the_last_write_counts_stage_and_call_rows"
 ],
 "history": [],
 "notes": []
}
```

Now:

```json
{
 "key": "stuck_child_limits",
 "name": "A stuck child",
 "state": "in_force",
 "statement": "The worker kills its child, releases the claim as 'child_stuck' and lets recovery take the run up when no progress has been seen for 900 seconds since the later of the child's launch and the last progress (downtime before the attempt does not count; fix round 1, finding 6), or after 1,800 seconds in all. Progress is the run's last write (a status change, a stage or call started or finished, a source searched, a record stored, the confirmation, the lock, the freeze), sampled by a thread of the worker with each query cut off after 5 seconds; the worker's main thread never waits for it, so the whole-run limit and the shutdown check keep their own clock (finding 5). 900 seconds covers one agent call's two requests at the 300-second request timeout plus 300 seconds of margin. A deploy (SIGTERM) stops the child (a SIGTERM not obeyed within 10 seconds is escalated to SIGKILL) and releases the claim as 'shutdown'. On every exit path the child is stopped and reaped before the claim is released, and no child is started once shutdown was asked for (finding 2).",
 "value": {
  "text": "900 s without a write; 1,800 s in all",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Every run worked by the worker.",
 "reason": "Owner's addition A4 (step 9 plan). Live runs took 10-41 s; on 0.5 CPU a fixed-plan run took 21.1 s, the statistics stage 3.2 s at 2,000 simulations and 8.7 s at 10,000 (measured 2026-10-08).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.queue:STALL_SECONDS",
    "equals": 900
   },
   {
    "ref": "python:hypocurate.pipeline.queue:RUN_TIMEOUT_SECONDS",
    "equals": 1800
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:DEFAULT_TIMEOUT_SECONDS",
    "equals": 300
   },
   {
    "ref": "python:hypocurate.pipeline.queue:MONITOR_TIMEOUT_MS",
    "equals": 5000
   },
   {
    "ref": "python:hypocurate.access.guarded:STOP_GRACE_SECONDS",
    "equals": 10
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_worker.py::test_a_stuck_child_is_stopped_and_its_claim_released_for_recovery",
  "tests/test_worker.py::test_the_whole_run_limit_stops_a_child_that_keeps_writing_too_long",
  "tests/test_worker.py::test_sigterm_shuts_the_worker_down_releasing_its_claim_and_stopping_its_child",
  "tests/test_queue.py::test_the_time_since_the_last_write_counts_stage_and_call_rows",
  "tests/test_worker_fix1.py::test_a_failure_after_the_child_started_stops_and_reaps_it_before_the_claim_is_released",
  "tests/test_worker_fix1.py::test_a_child_that_ignores_sigterm_is_killed",
  "tests/test_worker_fix1.py::test_no_child_is_started_once_shutdown_was_asked_for",
  "tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_the_whole_run_limit",
  "tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_shutdown",
  "tests/test_worker_fix1.py::test_the_monitoring_query_is_time_limited",
  "tests/test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance"
 ],
 "history": [],
 "notes": []
}
```
### `recovery_policy`

Before (`368a426`):

```json
{
 "key": "recovery_policy",
 "name": "Recovery when a run is taken up again",
 "state": "in_force",
 "statement": "When a worker claims a run that is already running, recovery first closes every open model call as 'interrupted' (counted at its reserved maximum under every cap) and every running stage as failed ('interrupted'); a run taken up more than 3 times fails ('attempts_exhausted'). It writes no plan, record, set, freeze or confirmation. The run then goes on by the normal path, by cause (owner, 2026-10-08): an interruption, a recording failure or any database failure while saving a call follows the per-role rule (the Planner is repeated once, a second loss fails the run; the Critic's remaining batches are skipped; after the Analyst the run completes with 'explanation unavailable'); a spending refusal stays a stop, exactly as in 9a (the Planner and the Critic fail the run, the Analyst completes it; no further request, never a later paid stage). The worker also finishes a narrower question that a stop left uncreated (never a second).",
 "value": {
  "text": "3 recoveries; the Planner repeated once",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run left open by a crash, a stop or a deploy (PRD 8, 14.4).",
 "reason": "Owner's answer Q3 (step 9 plan) and the owner's answer on recovery, split by cause (2026-10-08).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.recovery:MAX_RECOVERIES",
    "equals": 3
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:PLANNER_REPEATS",
    "equals": 1
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:RECOVERABLE",
    "equals": [
     "interrupted",
     "recording_failed",
     "reservation_failed"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:ANALYST_INTERRUPTED",
    "equals": "explanation unavailable (interrupted)"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_recovery.py::test_a_lost_planner_request_is_repeated_once",
  "tests/test_recovery.py::test_a_second_lost_planner_request_fails_the_run_with_the_reason",
  "tests/test_recovery.py::test_a_critic_spending_refusal_stays_a_stop_and_the_analyst_is_never_asked",
  "tests/test_recovery.py::test_a_lost_analyst_request_completes_the_run_with_the_explanation_unavailable",
  "tests/test_recovery.py::test_a_run_recovered_more_than_max_recoveries_times_fails",
  "tests/test_kill_matrix.py::test_a_worker_killed_at_a_code_stage_is_taken_up_with_the_same_results",
  "tests/test_kill_matrix.py::test_a_worker_killed_mid_planner_repeats_the_planner_once",
  "tests/test_kill_matrix.py::test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run"
 ],
 "history": [],
 "notes": []
}
```

Now:

```json
{
 "key": "recovery_policy",
 "name": "Recovery when a run is taken up again",
 "state": "in_force",
 "statement": "When a worker claims a run that is already running, recovery first closes every open model call as 'interrupted' (counted at its reserved maximum under every cap) and every running stage as failed: with the spending refusal recorded against its request when there is one (the refusal and its record are one transaction), else 'interrupted' (fix round 1, finding 1). Recovery attempts are counted explicitly (the claims that took up a running run; the first run is not one): the fourth fails the run ('attempts_exhausted'; finding 7). It writes no plan, record, set, freeze or confirmation. The run then goes on by the normal path, by cause (owner, 2026-10-08): an interruption, a recording failure or any database failure while saving a call, of a stage stored before the recovery, follows the per-role rule (a failure of an agent run after the recovery stops the run normally; finding 4) (the Planner is repeated once, a second loss fails the run; the Critic's remaining batches are skipped; after the Analyst the run completes with 'explanation unavailable'); a spending refusal stays a stop, exactly as in 9a (the Planner and the Critic fail the run, the Analyst completes it; no further request, never a later paid stage). The worker also finishes a narrower question that a stop left uncreated (never a second).",
 "value": {
  "text": "3 recoveries; the Planner repeated once",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run left open by a crash, a stop or a deploy (PRD 8, 14.4).",
 "reason": "Owner's answer Q3 (step 9 plan) and the owner's answer on recovery, split by cause (2026-10-08).",
 "evidence": [
  "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."
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
    "ref": "python:hypocurate.pipeline.recovery:MAX_RECOVERIES",
    "equals": 3
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:PLANNER_REPEATS",
    "equals": 1
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:RECOVERABLE",
    "equals": [
     "interrupted",
     "recording_failed",
     "reservation_failed"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:ANALYST_INTERRUPTED",
    "equals": "explanation unavailable (interrupted)"
   },
   {
    "ref": "python:hypocurate.pipeline.recovery:SPENDING_CODES",
    "equals": [
     "spending_cap_run",
     "spending_cap_month",
     "ceiling_reached"
    ]
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_recovery.py::test_a_lost_planner_request_is_repeated_once",
  "tests/test_recovery.py::test_a_second_lost_planner_request_fails_the_run_with_the_reason",
  "tests/test_recovery.py::test_a_critic_spending_refusal_stays_a_stop_and_the_analyst_is_never_asked",
  "tests/test_recovery.py::test_a_lost_analyst_request_completes_the_run_with_the_explanation_unavailable",
  "tests/test_recovery.py::test_a_run_recovered_more_than_max_recoveries_times_fails",
  "tests/test_kill_matrix.py::test_a_worker_killed_at_a_code_stage_is_taken_up_with_the_same_results",
  "tests/test_kill_matrix.py::test_a_worker_killed_mid_planner_repeats_the_planner_once",
  "tests/test_kill_matrix.py::test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run",
  "tests/test_recovery_spending.py::test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery",
  "tests/test_recovery_spending.py::test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked",
  "tests/test_worker_fix1.py::test_a_critic_run_after_recovery_that_fails_to_record_its_call_stops_the_run",
  "tests/test_worker_fix1.py::test_three_recoveries_are_allowed_and_the_fourth_is_refused_with_real_claim_histories",
  "tests/test_kill_matrix.py::test_a_worker_killed_during_the_critics_first_of_two_batches_skips_the_second"
 ],
 "history": [],
 "notes": []
}
```
### `worker_session_settings`

Before (`368a426`):

```json
null
```

Now:

```json
{
 "key": "worker_session_settings",
 "name": "Worker sessions notice a lost client",
 "state": "in_force",
 "statement": "The worker's and its child's database sessions set client_connection_check_interval to 1 second (PostgreSQL abandons a query whose client is gone) and TCP keepalives (idle 30 s, interval 10 s, 3 probes) on both sides, so a lost connection is noticed. Other sessions (the web service, the command line's own) keep the server's defaults.",
 "value": {
  "text": "1 s; keepalives 30/10/3",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Every database session of the worker and its child.",
 "reason": "The second-model review of step 9b; owner's decision, 2026-10-09.",
 "evidence": [
  "docs/reviews/step09b_review_chatgpt.md; docs/reviews/step09b_plan.md, 'Fix round 1'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-09"
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
    "ref": "python:hypocurate.db.engine:WORKER_SESSION",
    "equals": {
     "client_connection_check_interval": "1s",
     "tcp_keepalives_idle": "30",
     "tcp_keepalives_interval": "10",
     "tcp_keepalives_count": "3"
    }
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_worker_fix1.py::test_worker_sessions_check_for_a_lost_client_every_second_with_tcp_keepalives",
  "tests/test_worker_fix1.py::test_the_worker_and_its_child_use_worker_sessions"
 ],
 "history": [],
 "notes": []
}
```
## 5. Mutation checks

The faults of this round, each against the named tests, with a control run:

```
Run 3 (the database restarted after the Codespace stop; run 1 was cut short by the session's end at f14, run 2 had the database down and is discarded):
f01      CAUGHT  6 failed in 64.21s (0:01:04)
f02      CAUGHT  5 failed, 1 passed in 49.40s
f03      CAUGHT  1 failed, 15 passed in 201.67s (0:03:21)
f04      CAUGHT  1 failed, 15 passed in 93.51s (0:01:33)
f05      CAUGHT  1 failed, 15 passed in 94.89s (0:01:34)
f06      CAUGHT  1 failed, 15 passed in 97.28s (0:01:37)
f07      CAUGHT  1 failed, 15 passed in 96.30s (0:01:36)
f08      CAUGHT  3 failed, 13 passed in 97.18s (0:01:37)
f09      CAUGHT  1 failed, 15 passed in 91.66s (0:01:31)
f10      CAUGHT  1 failed, 15 passed in 91.41s (0:01:31)
f11      CAUGHT  2 failed, 14 passed in 96.88s (0:01:36)
f12      CAUGHT  1 failed, 15 passed in 90.30s (0:01:30)
f13      CAUGHT  1 failed, 15 passed in 91.86s (0:01:31)
f14      CAUGHT  1 failed, 15 passed in 93.88s (0:01:33)
f15      HUNG  no result in 1200 s
f16      CAUGHT  2 failed, 14 passed in 101.38s (0:01:41)
f17      CAUGHT  1 failed, 15 passed, 1 warning in 89.23s (0:01:29)
f18      CAUGHT  2 failed, 14 passed, 1 warning in 89.81s (0:01:29)
f19      CAUGHT  1 failed, 15 passed in 91.18s (0:01:31)
control  CAUGHT  1 failed, 103 passed in 348.48s (0:05:48)

f14 had hung on its first run (run 1: killed after 41 min; the harness then logged it SURVIVED). test_the_monitoring_query_is_time_limited now samples on a thread with a deadline; in run 3, f14 is caught in 94 s.
f15 hung in run 3 (the watchdog blocked on the test's forever-waiting stub). blocked_monitoring now waits 60 s (far beyond each test's limit), the assertions unchanged; f15 re-run, with a control:
f15      CAUGHT  7 failed, 9 passed, 3 warnings in 164.10s (0:02:44)
control  clean  104 passed in 350.10s (0:05:50)

The harness now labels a run with errors ERROR and one with no result in 1200 s HUNG; neither counts as a catch. The first control (run 3) had 1 failure in 104 while an f15 diagnosis ran on the same database and CPU; its output was not kept. The two later controls, run alone, are clean, and the harness now keeps each run's full output.
```

The earlier 9b faults (27), re-run on the final tests, with the control run:

```
d01      CAUGHT  1 failed, 29 passed in 9.99s
d02      CAUGHT  2 failed, 28 passed in 9.86s
d03      CAUGHT  7 failed, 23 passed in 10.06s
d04      CAUGHT  1 failed, 29 passed in 15.70s
q01      CAUGHT  1 failed, 14 passed in 14.12s
q02      CAUGHT  1 failed, 14 passed in 10.45s
q03      CAUGHT  1 failed, 14 passed in 10.48s
q04      CAUGHT  1 failed, 14 passed in 10.37s
g01      CAUGHT  1 failed, 5 passed in 7.66s
g02      CAUGHT  2 failed, 4 passed in 11.82s
g03      CAUGHT  1 failed, 5 passed in 7.92s
w01      CAUGHT  1 failed, 10 passed in 210.31s (0:03:30)
w02      CAUGHT  1 failed, 10 passed in 216.37s (0:03:36)
w03      CAUGHT  1 failed, 10 passed in 87.10s (0:01:27)
w04      CAUGHT  1 failed, 10 passed in 84.03s (0:01:24)
w05      CAUGHT  10 failed, 10 passed in 89.28s (0:01:29)
w06      CAUGHT  8 failed, 3 passed in 153.36s (0:02:33)
r01      CAUGHT  9 failed, 11 passed in 141.65s (0:02:21)
r02      CAUGHT  6 failed, 14 passed in 110.60s (0:01:50)
r03      CAUGHT  1 failed, 19 passed in 149.45s (0:02:29)
r04      CAUGHT  1 failed, 19 passed in 137.21s (0:02:17)
s01      CAUGHT  1 failed in 11.54s
o01      CAUGHT  1 failed, 19 passed in 141.92s (0:02:21)
o02      CAUGHT  3 failed, 17 passed in 136.63s (0:02:16)
o03      CAUGHT  2 failed, 18 passed in 117.44s (0:01:57)
o04      CAUGHT  5 failed, 15 passed in 107.18s (0:01:47)
q05      CAUGHT  1 failed, 14 passed in 10.03s
control  clean  104 passed in 350.59s (0:05:50)
```

f09 and f10 (the two lock faults) re-run on the race test as changed in `a9251d2`:

```
f09      CAUGHT  1 failed, 15 passed in 100.41s (0:01:40)
f10      CAUGHT  1 failed, 15 passed in 91.68s (0:01:31)
control  clean  104 passed in 348.66s (0:05:48)
```

The specification of this round:

```python
"""Step 9b fix round 1 mutations (scratch copy, PYTHONPATH). Same format as mutations.py."""
T = "/workspaces/hypocurate/tests/"
SP, WF = ["test_recovery_spending.py"], ["test_worker_fix1.py"]
M08 = "db/migrations/versions/0008_run_claim.py"
MUTATIONS = [
 # finding 1
 ("f01", "pipeline/agents/spend.py", "            conn.execute(_AUDIT, _refusal_row(invocation_id, inv, stage, code, max_cost, ceiling, totals))", "            pass", SP),
 ("f02", "pipeline/recovery.py", "            \"WHERE s.id = a.stage_result_id AND s.run_id = :r AND s.status = 'running'\"),", "            \"WHERE false AND s.id = a.stage_result_id\"),", SP),
 # finding 2
 ("f03", "access/guarded.py", "            self.proc.kill()", "            pass", WF),
 ("f04", "worker.py", "        _end_child(child, \"error\")  # never release with a live child (finding 2)", "        pass", WF),
 ("f05", "worker.py", "            if stop.is_set():\n                reason, why = \"shutdown\", \"shutdown\"", "            if False:\n                reason, why = \"shutdown\", \"shutdown\"", WF),
 # finding 3
 ("f06", "pipeline/queue.py", "            if touched != 1 or (self._lease is not None and not self._lease.holds()):", "            if False:", WF),
 ("f07", "pipeline/queue.py", "            if touched != 1 or (self._lease is not None and not self._lease.holds()):", "            if touched != 1:", WF),
 ("f08", "pipeline/writes.py", "        if not owner_holds(conn, run_id):  # step 9b fix round 1, finding 3", "        if False:", WF),
 ("f09", "pipeline/writes.py", "\"FOR KEY SHARE\"), dict(c=claim_id, r=run_id)).scalar_one_or_none()", "\"\"), dict(c=claim_id, r=run_id)).scalar_one_or_none()", WF),
 ("f10", M08, "            PERFORM 1 FROM run_claim WHERE id = OLD.id FOR UPDATE;", "            NULL;", WF),
 ("f11", "pipeline/writes.py", "    return bool(conn.execute(text(\n        \"SELECT EXISTS (SELECT 1 FROM pg_locks", "    return True or bool(conn.execute(text(\n        \"SELECT EXISTS (SELECT 1 FROM pg_locks", WF),
 ("f12", "pipeline/agents/spend.py", "            if not owner_holds(conn, inv.run_id):  # step 9b fix round 1, finding 3: before any request", "            if False:", WF),
 # finding 4
 ("f13", "pipeline/orchestrator.py", "        excused = recovered and stored", "        excused = recovered", WF),
 # findings 5 and 6
 ("f14", "pipeline/queue.py", "        conn.execute(text(f\"SET LOCAL statement_timeout = {MONITOR_TIMEOUT_MS}\"))\n        conn.execute(text(f\"SET LOCAL lock_timeout = {MONITOR_TIMEOUT_MS}\"))\n        return last_write_epoch", "        return last_write_epoch", WF),
 ("f15", "worker.py", "        now = time.monotonic()\n        if now - started > run_timeout:", "        queue.last_write_epoch(None, 0)\n        now = time.monotonic()\n        if now - started > run_timeout:", WF),
 ("f16", "pipeline/queue.py", "                if self._last is not None and seen > self._last:\n                    self.progress_at = time.monotonic()", "                if True:\n                    self.progress_at = time.monotonic() - (time.time() - seen)", WF),
 # finding 7
 ("f17", "pipeline/queue.py", "rec=status == \"running\")).scalar_one()", "rec=True)).scalar_one()", WF),
 ("f18", "pipeline/recovery.py", "\"SELECT count(*) FROM run_claim WHERE run_id = :r AND recovery\"", "\"SELECT count(*) FROM run_claim WHERE run_id = :r\"", WF),
 # worker sessions
 ("f19", "db/engine.py", "    if worker_session:", "    if False:", WF),
]
```

The earlier specification (w01-w03, r03 and o03 re-pointed at the changed code):

```python
"""Every step 9b mutation (scratch copy, PYTHONPATH). Each: (id, file under hypocurate/, old, new, tests). A mutation
is caught when at least one named test fails."""
T = "/workspaces/hypocurate/tests/"
M08 = "db/migrations/versions/0008_run_claim.py"
MIG, Q, G, W, REC = ["test_migrations_step9b.py"], ["test_queue.py"], ["test_guarded_parent.py"], ["test_worker.py"], \
    ["test_recovery.py"]
PARTLY = ["test_kill_matrix.py::test_a_worker_killed_between_the_partly_copy_and_the_narrower_question_leaves_exactly_one"]
MUTATIONS = [
 # 0008
 ("d01", M08, "    op.create_index('uq_run_claim_open', 'run_claim', ['run_id'], unique=True,",
  "    op.create_index('uq_run_claim_open', 'run_claim', ['run_id'], unique=False,", MIG),
 ("d02", M08, "        IF hc_lock_run(NEW.run_id) NOT IN ('queued', 'running', 'waiting') THEN", "        IF false THEN", MIG),
 ("d03", M08, "        IF OLD.released_at IS NOT NULL THEN", "        IF false THEN", MIG),
 ("d04", M08, "            NEW.heartbeat_at := clock_timestamp();", "            NULL;", MIG),
 # claims and the heartbeat
 ("q01", "pipeline/queue.py",
  "        if not self._conn.execute(text(\"SELECT pg_try_advisory_lock(:k)\"), dict(k=work_key(self.run_id))).scalar():",
  "        if False:", Q),
 ("q02", "pipeline/queue.py", "            if not open_claim.stale:\n                return None",
  "            if False:\n                return None", Q),
 ("q03", "pipeline/queue.py",
  "           OR (r.status = 'waiting' AND EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id)))",
  "           OR r.status = 'waiting')", Q),
 ("q04", "pipeline/queue.py", "        while not self._stop_event.wait(self._interval):",
  "        while False and not self._stop_event.wait(self._interval):", Q),
 # the child dies with its parent (A3)
 ("g01", "access/guarded.py", "    if threading.current_thread() is not threading.main_thread():", "    if False:", G),
 ("g02", "access/guarded.py", "        _die_with_parent(int(request[\"parent_pid\"]))", "        pass", G),
 ("g03", "access/guarded.py", "    if os.getppid() != parent_pid:", "    if False:", G),
 # the worker (A4, shutdown, the work lock)
 ("w01", "worker.py", "        if now - monitor.progress_at > stall_seconds:", "        if False:", W),
 ("w02", "worker.py", "        if now - started > run_timeout:", "        if False:", W),
 ("w03", "worker.py", "                reason = {\"shutdown\": \"shutdown\", \"ownership_lost\": \"lost\"}.get(watched, \"child_stuck\")",
  "                reason = \"child_stuck\"", W),
 ("w04", "worker.py", "                queue.record_child(engine, claim, child.pid)", "                pass", W),
 ("w05", "worker.py", "\"recovered\": claim.status_before == \"running\"},", "\"recovered\": False},", REC),
 ("w06", "pipeline/orchestrator.py",
  "        if not holder.execute(text(\"SELECT pg_try_advisory_lock(:k)\"), dict(k=queue.work_key(run_id))).scalar():",
  "        if False:", W),
 # recovery
 ("r01", "pipeline/recovery.py", "            \"WHERE mc.run_id = :r AND mc.status = 'started'\"), dict(r=run_id)).rowcount",
  "            \"WHERE false\"), dict(r=run_id)).rowcount", REC),
 ("r02", "pipeline/recovery.py",
  "            \"WHERE run_id = :r AND status = 'running'\"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount",
  "            \"WHERE false\"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount", REC),
 ("r03", "pipeline/recovery.py", "        if attempts > MAX_RECOVERIES:", "        if False:", REC),
 ("r04", "pipeline/recovery.py", "THEN 'recording_failed' ELSE 'worker_stopped' END",
  "THEN 'worker_stopped' ELSE 'worker_stopped' END", REC),
 ("s01", "worker.py", "            recovery.finish_narrower_questions(engine)\n", "", PARTLY),
 # the orchestrator's rule after recovery
 ("o01", "pipeline/orchestrator.py", "                if _lost(engine, run_id, \"planner\") > PLANNER_REPEATS:",
  "                if False:", REC),
 ("o02", "pipeline/orchestrator.py", "    if recovered and code in RECOVERABLE:\n        return None",
  "    if False:\n        return None", REC),
 ("o03", "pipeline/orchestrator.py", "and not (excused and f in RECOVERABLE)]", "]", REC),
 ("o04", "pipeline/orchestrator.py",
  "            if recovered and code in RECOVERABLE:  # step 9b (owner, Q3): the Planner is repeated once",
  "            if False:  # step 9b (owner, Q3): the Planner is repeated once", REC),
]
# (Fix round 1: w01, w02, w03, r03 and o03 re-pointed at the changed lines; the same faults.)
# Added after the first run (q02 and q03 survived, each hidden by the other guard): q05, the claim transaction's own
# confirmation check.
MUTATIONS.append(("q05", "pipeline/queue.py",
                  "    if status == \"waiting\" and not conn.execute(", "    if False and not conn.execute(", Q))
```
```python
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import sys as _s; from importlib import import_module as _i; _m = _i(_s.argv[1] if len(_s.argv) > 1 else "mutations"); MUTATIONS, T = _m.MUTATIONS, _m.T
M = os.path.expanduser("~/hc-work/step09b/mut")
env = dict(os.environ, PYTHONPATH=M)
env["DATABASE_URL"] = open("/workspaces/hypocurate/.env").read().split("DATABASE_URL=")[1].split("\n")[0]
results = []
for mid, f, old, new, tests in MUTATIONS + [("control", None, None, None, ["test_migrations_step9b.py", "test_queue.py", "test_guarded_parent.py", "test_worker.py", "test_recovery.py",
                                                             "test_worker_fix1.py", "test_recovery_spending.py"])]:
    shutil.rmtree(os.path.join(M, "hypocurate"), ignore_errors=True)
    shutil.copytree("/workspaces/hypocurate/hypocurate", os.path.join(M, "hypocurate"))
    if f:
        p = os.path.join(M, "hypocurate", f); s = open(p).read()
        assert s.count(old) >= 1, (mid, "pattern not found")
        open(p, "w").write(s.replace(old, new, 1))
    # A run with errors (setup, not an assertion) or one that hangs is never counted as a catch: it is labelled
    # ERROR or HUNG and inspected by hand.
    try:
        out = subprocess.run(["/workspaces/hypocurate/.venv/bin/pytest", "-q", "-rf", "-p", "no:cacheprovider",
                              "--rootdir=/workspaces/hypocurate"] + [T + t for t in tests],
                             cwd=os.path.expanduser("~/hc-work/step09b"), env=env, capture_output=True, text=True,
                             timeout=1200).stdout.strip()
        open(os.path.expanduser(f"~/hc-work/step09b/mutout_{mid}.txt"), "w").write(out)  # the full output, kept
        out = out.splitlines()[-1]
    except subprocess.TimeoutExpired:
        out = "no result in 1200 s"
    if out.startswith("no result"):
        verdict = "HUNG"
    elif "error" in out:
        verdict = "ERROR"
    elif "failed" in out:
        verdict = "CAUGHT"
    else:
        verdict = "clean" if mid == "control" else "SURVIVED"
    line = f"{mid:8} {verdict}  {out}"
    print(line, flush=True); results.append(line)
```
## 6. Reference comparison with `main`

The same dumps as in the review packet, on this head:

```
head 641af6b
IDENTICAL fixed_plan.json
IDENTICAL narrower.json
IDENTICAL partly_original.json
IDENTICAL planner_bcc.json
IDENTICAL planner_fcc.json
IDENTICAL reference.json
```

```
== fixed_plan: 0 differing leaves
== planner_fcc: 0 differing leaves
== planner_bcc: 0 differing leaves
== partly_original: 0 differing leaves
== narrower: 0 differing leaves
```
## 7. The suite and the images

The whole suite on this head (locally):

```
2146 passed, 1 warning in 2185.57s (0:36:25)
local exit 0
```

In the test image, rebuilt on this head (run with `docker run --network host` against the same database: since the Codespace restart, the Compose network drops traffic between containers; the image's own command, the Compose service's four variables):

```
2146 passed, 1 warning in 2502.99s (0:41:42)
exit 0
```

The package in the repository and in both images:

```
head:    a9251d2
repo:    2a17dee1afba0e7bbfca0061017c36b4cdd1792c760ab543f38ba4f423e833ed  -
runtime: 2a17dee1afba0e7bbfca0061017c36b4cdd1792c760ab543f38ba4f423e833ed  -
test:    2a17dee1afba0e7bbfca0061017c36b4cdd1792c760ab543f38ba4f423e833ed  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
(the runtime image was built on d9523ca; the commits since change only tests/ and docs/, so its package is unchanged)
```

The guard checks in the runtime image:

```
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmpcu7quhoc/.env is outside the approved inputs of pipeline code']}
```
## 8. The local development database

Unchanged: at 0007 (`main`). 0008 was never applied to it, so amending 0008 in place (`recovery`, the trigger's row lock) needs no downgrade there.

## 9. The scripts

### `~/hc-work/step09b/register_fix1.py`

```python
"""Step 9b fix round 1: register corrections (scratch; run from the repo root with the project's Python). The 9b
entries are new on this unmerged branch, so they are corrected in place (their reviewed wording is in the fix packet);
spending_caps exists on main and keeps its history; worker_session_settings is new."""
import json
P = "hypocurate/assumptions.json"
d = json.load(open(P, encoding="utf-8"))
by = {e["key"]: e for e in d}
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-09"}


def rep(key, old, new):
    e = by[key]
    assert e["statement"].count(old) == 1, (key, old[:60])
    e["statement"] = e["statement"].replace(old, new)


rep("queue_and_claims", "A claim's heartbeat "
    "is written every 15 seconds by a thread of the worker on the claim row, never the run row, so it never waits behind "
    "the run's lock (a named exception to the locking protocol, like audit rows).",
    "A claim's heartbeat is written every 15 seconds by a thread of the worker on the claim row, never the run row, so "
    "it never waits behind the run's lock (a named exception to the locking protocol, like audit rows). Each beat also "
    "confirms ownership: the beat touched the open claim's row and the lease session still holds CLAIM; otherwise the "
    "worker stops its child at once and gives the run up ('lost'). The child's work is bound to its claim: every write "
    "checks, in its own transaction after the run's lock, that the claim is open (its row locked FOR KEY SHARE; "
    "closing a claim locks the row FOR UPDATE first, so a takeover waits for a write in progress or the write sees "
    "the claim closed) and that the child's work lock is still held; a reservation checks the same before any "
    "request. A stale owner is refused ('claim_lost') before any further write or request (fix round 1, finding 3).")
by["queue_and_claims"]["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.writes:owner_holds"})
by["queue_and_claims"]["tests"] += [
    "tests/test_worker_fix1.py::test_losing_the_lease_session_stops_the_child_and_gives_up_the_run",
    "tests/test_worker_fix1.py::test_losing_the_work_session_refuses_the_childs_next_write",
    "tests/test_worker_fix1.py::test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused",
    "tests/test_worker_fix1.py::test_a_stale_owner_is_refused_before_its_reservation"]

rep("stuck_child_limits", "The worker kills its child, releases the claim as 'child_stuck' and lets recovery take "
    "the run up when the run has written nothing (a status change, a stage or call started or finished, a source "
    "searched, a record stored, the confirmation, the lock, the freeze) for 900 seconds, or after 1,800 seconds in all.",
    "The worker kills its child, releases the claim as 'child_stuck' and lets recovery take the run up when no progress "
    "has been seen for 900 seconds since the later of the child's launch and the last progress (downtime before the "
    "attempt does not count; fix round 1, finding 6), or after 1,800 seconds in all. Progress is the run's last write "
    "(a status change, a stage or call started or finished, a source searched, a record stored, the confirmation, the "
    "lock, the freeze), sampled by a thread of the worker with each query cut off after 5 seconds; the worker's main "
    "thread never waits for it, so the whole-run limit and the shutdown check keep their own clock (finding 5).")
rep("stuck_child_limits", "A deploy (SIGTERM) stops "
    "the child and releases the claim as 'shutdown'.",
    "A deploy (SIGTERM) stops the child (a SIGTERM not obeyed within 10 seconds is escalated to SIGKILL) and releases "
    "the claim as 'shutdown'. On every exit path the child is stopped and reaped before the claim is released, and no "
    "child is started once shutdown was asked for (finding 2).")
by["stuck_child_limits"]["applied"]["settings"] += [
    {"ref": "python:hypocurate.pipeline.queue:MONITOR_TIMEOUT_MS", "equals": 5000},
    {"ref": "python:hypocurate.access.guarded:STOP_GRACE_SECONDS", "equals": 10}]
by["stuck_child_limits"]["tests"] += [
    "tests/test_worker_fix1.py::test_a_failure_after_the_child_started_stops_and_reaps_it_before_the_claim_is_released",
    "tests/test_worker_fix1.py::test_a_child_that_ignores_sigterm_is_killed",
    "tests/test_worker_fix1.py::test_no_child_is_started_once_shutdown_was_asked_for",
    "tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_the_whole_run_limit",
    "tests/test_worker_fix1.py::test_a_blocked_monitoring_query_does_not_hold_back_shutdown",
    "tests/test_worker_fix1.py::test_the_monitoring_query_is_time_limited",
    "tests/test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance"]

rep("recovery_policy", "every running stage as failed "
    "('interrupted'); a run taken up more than 3 times fails ('attempts_exhausted').",
    "every running stage as failed: with the spending refusal recorded against its request when there is one (the "
    "refusal and its record are one transaction), else 'interrupted' (fix round 1, finding 1). Recovery attempts are "
    "counted explicitly (the claims that took up a running run; the first run is not one): the fourth fails the run "
    "('attempts_exhausted'; finding 7).")
rep("recovery_policy", "an interruption, a "
    "recording failure or any database failure while saving a call follows the per-role rule",
    "an interruption, a recording failure or any database failure while saving a call, of a stage stored before the "
    "recovery, follows the per-role rule (a failure of an agent run after the recovery stops the run normally; finding "
    "4)")
by["recovery_policy"]["applied"]["settings"].append(
    {"ref": "python:hypocurate.pipeline.recovery:SPENDING_CODES",
     "equals": ["spending_cap_run", "spending_cap_month", "ceiling_reached"]})
by["recovery_policy"]["tests"] += [
    "tests/test_recovery_spending.py::test_a_planner_refusal_whose_stage_was_not_saved_stays_a_stop_after_recovery",
    "tests/test_recovery_spending.py::test_a_critic_refusal_whose_stage_was_not_saved_stays_a_stop_and_the_analyst_is_never_asked",
    "tests/test_worker_fix1.py::test_a_critic_run_after_recovery_that_fails_to_record_its_call_stops_the_run",
    "tests/test_worker_fix1.py::test_three_recoveries_are_allowed_and_the_fourth_is_refused_with_real_claim_histories",
    "tests/test_kill_matrix.py::test_a_worker_killed_during_the_critics_first_of_two_batches_skips_the_second"]

e = by["spending_caps"]
o = "is not sent, and the refusal is logged."
assert e["statement"].count(o) == 1
e["history"].append({"value": e["statement"], "from": e["decided"]["date"], "to": "2026-10-09",
                     "note": "Step 9b fix round 1 (owner, 2026-10-09, finding 1): the refusal's record is written in the "
                             "transaction that decides it."})
e["statement"] = e["statement"].replace(o, "is not sent, and the refusal is logged in the same transaction that decides "
                                           "it: a refusal is reported only once its record is committed (otherwise "
                                           "the caller sees a failure to save the call).")
e["decided"] = OWNER
e["tests"].append("tests/test_recovery_spending.py::test_a_refusal_is_reported_only_once_its_record_is_committed")

assert "worker_session_settings" not in by
d.append({"key": "worker_session_settings", "name": "Worker sessions notice a lost client",
          "state": "in_force",
          "statement": "The worker's and its child's database sessions set client_connection_check_interval to 1 second "
                       "(PostgreSQL abandons a query whose client is gone) and TCP keepalives (idle 30 s, interval 10 s, "
                       "3 probes) on both sides, so a lost connection is noticed. Other sessions (the web service, the "
                       "command line's own) keep the server's defaults.",
          "value": {"text": "1 s; keepalives 30/10/3", "unit": "seconds"}, "category": "operational",
          "affects": "Every database session of the worker and its child.",
          "reason": "The second-model review of step 9b; owner's decision, 2026-10-09.",
          "evidence": ["docs/reviews/step09b_review_chatgpt.md; docs/reviews/step09b_plan.md, 'Fix round 1'."],
          "decided": OWNER, "expert_review": {"status": "not_reviewed", "name": None, "date": None},
          "sensitivity": None,
          "applied": {"status": "yes", "settings": [
              {"ref": "python:hypocurate.db.engine:WORKER_SESSION",
               "equals": {"client_connection_check_interval": "1s", "tcp_keepalives_idle": "30",
                          "tcp_keepalives_interval": "10", "tcp_keepalives_count": "3"}}], "note": None},
          "tests": ["tests/test_worker_fix1.py::test_worker_sessions_check_for_a_lost_client_every_second_with_tcp_keepalives",
                    "tests/test_worker_fix1.py::test_the_worker_and_its_child_use_worker_sessions"],
          "history": [], "notes": []})

with open(P, "w", encoding="utf-8") as f:
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(len(d), "entries")
```
### `~/hc-work/step09b/fixpacket.py`

````python
"""Builds docs/reviews/step09b_fix_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step09b"
REVIEWED = "368a426"  # the head ChatGPT reviewed
OUT = Path("docs/reviews/step09b_fix_packet.md")


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
    ("1", "A spending refusal survives a failed save", "0dcabad",
     "- **The refusal record:** `spend.reserve` writes the refusal's audit row in the transaction that decides it. A refusal is reported only once its record is committed; if that commit fails, the caller sees a failure to save the call, which the owner's split rule treats as a database failure.\n"
     "- **Recovery:** before closing a running stage as `interrupted`, it looks for a committed refusal against the stage's invocations and keeps that code as the stage's cause. The Planner and the Critic then fail the run as in 9a: nothing is repeated or sent, and the Analyst is never asked after a Critic refusal.\n"
     "- **Tests:** a real refusal (the run's ceiling, or the monthly cap) at the Planner and at the Critic; the stage's save then refused by a test trigger; recovery. The month change is simulated by moving the counted calls into the previous month, with triggers off."),
    ("2", "Never release a claim with a live child", "8a059e8, d9523ca",
     "- **The child stops:** `GuardedChild.stop` escalates a SIGTERM not obeyed within 10 s (`STOP_GRACE_SECONDS`) to SIGKILL, and reaps the child.\n"
     "- **The release:** `worker.work` keeps the child and stops it in `finally` on every exit path before releasing the claim.\n"
     "- **Shutdown:** checked before each child is started (`d9523ca` removed an earlier duplicate check, so the remaining one is tested alone)."),
    ("3", "Losing the lock means stopping", "8a059e8",
     "- **The worker:** each heartbeat confirms that its update touched the open claim's row and that the lease session still holds CLAIM (`Lease.holds`). Otherwise it sets `lost`, and the worker stops its child at once and gives the run up (`lost`).\n"
     "- **The child:** its work is bound to its claim. `orchestrator.work_guarded` sets `writes.OWNER` = (claim id, the pid of the session holding its work lock).\n"
     "- **Each write:** `writes.write` checks, in its own transaction after the run's lock, that the claim is open (its row locked **FOR KEY SHARE**) and that the work lock is still held (`pg_locks`). Otherwise the write is refused `claim_lost`.\n"
     "- **Each request:** `spend.reserve` checks the same before any request (`ClaimLost`, which the request path reports as a reservation failure).\n"
     "- **The owner's addition (the check inside the write's transaction):**\n"
     "  - 0008's update trigger locks the claim row FOR UPDATE before closing it, so any close, a takeover or direct SQL, waits for a write in progress, or the write sees the claim closed.\n"
     "  - FOR KEY SHARE rather than FOR SHARE: the worker's own heartbeat is a plain update, and under FOR SHARE it would wait behind a long write (storing thousands of records) and wrongly report lost ownership.\n"
     "- **Tests:**\n"
     "  - terminating the lease's database session, and the work lock's, while the processes stay alive;\n"
     "  - a two-connection race of a takeover against a child's write;\n"
     "  - a stale owner's reservation."),
    ("4", "The recovery exception applies only to old stages", "8a059e8",
     "`proceed` excuses a lost Critic request only for Critic stages stored before (those recovery processed). The "
     "failures of a Critic run now stop the run normally."),
    ("5", "Monitoring cannot block the watchdog", "8a059e8",
     "- **The monitor:** `queue.Monitor` samples the run's last write on a thread of its own, each query limited to 5 s (`MONITOR_TIMEOUT_MS`, statement and lock timeouts).\n"
     "- **The main thread** never queries the database while it watches: the whole-run limit, the shutdown check and the lost-ownership check are on its own clock and events.\n"
     "- **Tests:** a monitoring query made to block forever, at the whole-run limit and at a shutdown; and a monitoring query held by a table lock is cut off."),
    ("6", "The stall allowance starts fresh", "8a059e8",
     "The allowance counts from `Monitor.progress_at`: the child's launch, and each progress seen after it. Downtime "
     "before the attempt does not count."),
    ("7", "Recovery count", "8a059e8",
     "- **The count:** `run_claim.recovery` (0008 amended, unmerged) marks a claim that took up a run already running, set at the claim and never changed. Recovery counts those claims, this one included, and fails the run when there are more than 3. The first run's claim is not one.\n"
     "- **Test:** real claim histories, each attempt a claim worked by the worker's code and stopped by a shutdown: three recoveries go on, and the fourth is refused."),
]
EXTRAS = (
    "### Also (the owner's list)\n\n"
    "- **Worker sessions:** the worker's and its child's sessions set `client_connection_check_interval` to 1 s and TCP keepalives (30/10/3) on both sides (`db.engine.WORKER_SESSION`, `make_engine(worker_session=True)`); register `worker_session_settings` (new).\n"
    "- **The kill case \"mid-Critic, batch 1 of 2\":** 110 rows in both sources raise 110 flags naming two records each (two batches, at most 100 per request); the worker is killed during the first; after recovery the second is never sent and the run completes. New coverage, not a fix.\n"
    "- **`render.yaml`'s stale header comment** is corrected (`5b3923d`), its own commit. The full `render.yaml` diff against `main` is below.\n"
    "- **The register** is corrected wherever it promised more than the code: `queue_and_claims`, `stuck_child_limits`, `recovery_policy`, `spending_caps`; `worker_session_settings` is new (148 entries).\n\n")
parts = [f"""# Build step 9b — fix packet (fix round 1)

Date: 2026-10-09. Branch: `step-09b-worker`. Reviewed head: `{REVIEWED}`. Head when generated: `{head}`. Generated from
the files on disk by a script (`~/hc-work/step09b/fixpacket.py`, quoted in section 9), so every diff and output below
is quoted exactly.

## How to use this packet

ChatGPT's review of `{REVIEWED}` (`docs/reviews/step09b_review_chatgpt.md`) found the step not safe to merge, with seven
findings. The owner accepted all seven, added a list of extras (below the findings), approved two design choices and
added one requirement to finding 3. This packet covers only this round:
1. the findings and their fixes;
2. the code diff;
3. the tests, new and changed, and the tests that failed before;
4. the register;
5. the mutation checks;
6. the reference comparison with `main`;
7. the suite and the images;
8. the local database;
9. the scripts.

The summary (`step09b_summary.md`) has a "Fix round 1" section near the top. Please confirm each finding is closed, and say
whether anything in this round is stronger in its claims than the code supports.

Commits of this round:

""" + fence(commits) + "\n"]
body = "## 1. The findings and their fixes\n\n"
for num, title, commit, text in FINDINGS:
    body += f"### Finding {num}: {title} (commit `{commit}`)\n\n{text}\n\n"
body += ("**The owner's decisions in this round (2026-10-09):**\n"
         "- The refusal's audit row is written in the transaction that decides the refusal.\n"
         "- The claim check (claim open and work lock held) lives in `writes.write` and `spend.reserve`, refusing `claim_lost`.\n"
         "- The check runs inside the write's transaction with the claim row locked, so a takeover that closes the "
         "claim waits for the write or the write sees the closed claim. A two-connection race test. For model requests, "
         "the check before the reservation is enough.\n\n")
body += EXTRAS
body += "### The full `render.yaml` diff against `main` (`c7458d0`)\n\n" + fence(sh("git", "diff", "c7458d0..HEAD", "--", "render.yaml"), "diff") + "\n"
parts.append(body)
diff = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{REVIEWED}..HEAD`, the package with 0008; the register is in section 4)\n\n"
             + fence(diff, "diff"))
tdiff = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "tests")
parts.append("## 3. Tests\n\n### Tests added or changed in this round (diff)\n\n" + fence(tdiff, "diff")
             + "\n### Changed expectations\n\n"
             "No existing assertion changed. `test_kill_matrix.py` gains the two-batch Critic case and a stall helper "
             "that returns its lock holder; its other cases are unchanged.\n\n"
             "Three of this round's own tests were changed after they were first written:\n"
             "- `test_a_takeover_waits_for_a_write_in_progress_and_the_next_write_is_refused` (`a9251d2`, the owner's "
             "approval): its check compared two Python clock readings, which can come in either order by scheduling "
             "chance (one failure in the whole suite). It now checks the wait itself, on the takeover's clock and on "
             "the database's.\n"
             "- `test_the_monitoring_query_is_time_limited` and `blocked_monitoring` (`641af6b`): they fail instead "
             "of hanging on f14 and f15. No assertion changed.\n\n"
             "### The tests of this round on the reviewed code (`" + REVIEWED + "`'s package, scratch copy, `PYTHONPATH`)\n\n"
             "Run from a directory with no `hypocurate` package: the worker tests start `python -m hypocurate.worker`, "
             "and `-m` puts the current directory first, so a run from the repository would start the worker on the "
             "new code (a first attempt did, and was discarded).\n\n"
             + fence(lines_with(HOME / "fix1_failed_before.log", "PASSED", "FAILED", "ERROR", "passed", "failed")))
old = {e["key"]: e for e in json.loads(sh("git", "show", f"{REVIEWED}:hypocurate/assumptions.json"))}
new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
changed = [k for k in new if old.get(k) != new[k]]
reg = ""
for k in changed:
    reg += f"### `{k}`\n\nBefore (`{REVIEWED}`):\n\n" + fence(json.dumps(old.get(k), indent=1, ensure_ascii=False), "json")
    reg += "\nNow:\n\n" + fence(json.dumps(new[k], indent=1, ensure_ascii=False), "json")
parts.append(f"## 4. The register ({len(new)} entries; {len(changed)} changed in this round)\n\n"
             "Entries new on this unmerged branch are corrected in place (their reviewed wording is shown here); "
             "`spending_caps`, on `main`, keeps its earlier wording in its history.\n\n" + reg)
parts.append("## 5. Mutation checks\n\nThe faults of this round, each against the named tests, with a control run:\n\n" + fence(read(HOME / "fix1_mutations.log"))
             + "\nThe earlier 9b faults (27), re-run on the final tests, with the control run:\n\n"
             + fence(read(HOME / "fix1_mutations_earlier.log"))
             + "\nf09 and f10 (the two lock faults) re-run on the race test as changed in `a9251d2`:\n\n"
             + fence(read(HOME / "fix1_mutations_f0910.log"))
             + "\nThe specification of this round:\n\n" + fence(read(HOME / "mspec/mutations_fix1.py"), "python")
             + "\nThe earlier specification (w01-w03, r03 and o03 re-pointed at the changed code):\n\n"
             + fence(read(HOME / "mspec/mutations.py"), "python")
             + fence(read(HOME / "mspec/run_any.py"), "python"))
parts.append("## 6. Reference comparison with `main`\n\nThe same dumps as in the review packet, on this head:\n\n"
             + fence(read(HOME / "refdump/cmp_fix1.txt")) + "\n" + fence(read(HOME / "refdump/compare_fix1_output.txt")))
parts.append("## 7. The suite and the images\n\nThe whole suite on this head (locally):\n\n"
             + fence(lines_with(HOME / "fix1_final_full.log", "passed", "failed", "exit"))
             + "\nIn the test image, rebuilt on this head (run with `docker run --network host` against the same "
             "database: since the Codespace restart, the Compose network drops traffic between containers; the image's "
             "own command, the Compose service's four variables):\n\n"
             + fence(lines_with(HOME / "fix1_image_suite.log", "passed", "failed", "exit"))
             + "\nThe package in the repository and in both images:\n\n" + fence(read(HOME / "fix1_image_hashes.txt"))
             + "\nThe guard checks in the runtime image:\n\n" + fence(read(HOME / "fix1_image_guard.log")))
parts.append("## 8. The local development database\n\nUnchanged: at 0007 (`main`). 0008 was never applied to it, "
             "so amending 0008 in place (`recovery`, the trigger's row lock) needs no downgrade there.\n\n")
parts.append("## 9. The scripts\n\n" + "".join(f"### `~/hc-work/step09b/{s}`\n\n" + fence(read(HOME / s), "python")
                                         for s in ("register_fix1.py", "fixpacket.py")))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
