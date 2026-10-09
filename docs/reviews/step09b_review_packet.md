# Build step 9b — review packet

Date: 2026-10-08. Branch: `step-09b-worker`, from `main` at `c7458d0`. Head when generated: `8fc9c93`. Generated from
the files on disk by a script (`~/hc-work/step09b/packet.py`, quoted in section 10), so every diff and output below is
quoted exactly.

## How to use this packet

Step 9b builds the queue and the worker: claims and their heartbeat (migration 0008), the guarded child that dies
with its parent, recovery when a run is taken up again, and the command line through the claim. It holds safeguard
changes (listed at the top of the summary), so please review against `docs/reviews/checklist.md` and answer the
questions at the end of the summary. Sections: 1 the summary; 2 the code diff; 3 the new test files; 4 the changed
tests; 5 the register; 6 the reference comparison with `main`; 7 the mutation checks; 8 new tests on `main`'s code;
9 the suite and the images; 10 the measurements on 0.5 CPU; 11 the plan and the scripts.

## 1. The summary

# Build step 9b — summary for review

Date: 2026-10-08/09. Branch: `step-09b-worker` (from `main` at `c7458d0`). **Status: built; pushed for the second-model review; not merged** (the owner's end point for 9b: "End with the summary and review packet, push, and stop. Do not merge.").

PRD Section 15, step 9 ("Worker and queue"), second part: job claiming, the heartbeat, recovery (resume or fail), and criterion 14.4. Part 9a (merged and live, schema 0007) built the wait at the rules lock and the confirmation, cancel, dispatch again, the stored ceiling, and an orchestrator that takes every step from stored rows. The approved plan, with every owner decision binding 9b, is in `docs/reviews/step09b_plan.md` (on the branch, so it survives a session's memory being compacted).

**Safeguard changes in 9b (second-model review before any merge; CLAUDE.md "How we work" item 5):**

1. **Migration 0008**, `run_claim`: claims, the heartbeat, one open claim per run.
2. **The guarded runner:** `start_guarded`, and the child's death signal with the parent check (owner's addition A3).
3. **The claim protocol:** two session advisory locks plus one locked transaction. The heartbeat is written on the claim row, a named exception to the locking protocol (R6).
4. **Recovery:** closing open calls and stages; the per-role rule after a recovery, split by cause (the owner's answer of 2026-10-08); `MAX_RECOVERIES`.
5. **The worker:** the stuck-child limits (A4) and SIGTERM.

6. **`render.yaml`: the worker's plan, from `0.5c-512mb` to `1c-2g`** (the owner's decision of 2026-10-08, after the memory measurement below), as its own commit, with `test_skeleton`'s plan pin following. Nothing else in `render.yaml` changed. **For the reviewer:**
   - **When it applies:** a `render.yaml` change takes effect at the push to `main`, through Render's Blueprint sync, *before* the checks pass, and redeploys the code already running (CLAUDE.md, item 10). A plan change depends on no new code, so it is safe to apply then; the new code follows once the run is green.
   - **Cost:** from about $7 to about $25 a month for the worker, from the merge on.
   - **A stale comment:** the file's header comment ("Plans: the cheapest paid plans") is no longer accurate for the worker. It was left as it is because the owner said nothing else in `render.yaml` changes; the owner may want it reworded in a later commit.

**Not changed:** `.github/workflows/`, the Dockerfile, Compose, the dependency locks. 0001 to 0007 are untouched. The access layer's allow-lists are unchanged.

## The owner's decisions that bind 9b

From the step 9 plan (`step09b_plan.md` quotes each in full):
- **Q2:** keep the Render worker at 0.5c-512mb; measure first.
- **Q3:** an interrupted paid stage: the Planner is repeated once; the Critic and the Analyst are not.
- **A3:** the child dies with its parent.
- **A4:** the stuck-child limits.
- **The note:** report the statistics stage at about 10,000 simulations.
- **R1, R2, R6:** the CLI through the claim; `--queue`, `queue`, `worker`; the heartbeat on the claim row.

**The owner's answer on recovery (2026-10-08), split by cause:**
- **A recording failure, or any database failure while saving a call** (`recording_failed`, `reservation_failed`): the Q3 per-role rule, as for an interruption. The call is closed and counted at its reserved maximum. Then the Planner is repeated once, the Critic's remaining batches are skipped, or the run completes with "explanation unavailable" after the Analyst.
- **A spending refusal stays a stop, exactly as in 9a.** Recovery only finishes the bookkeeping and ends the run as 9a does: the Analyst completes the run; the Planner and the Critic stop it. It never sends another request and never moves on to a later paid stage.
- **A test for each case at each agent**, including that a Critic spending refusal still prevents the Analyst's request after recovery.

## Measurements on 0.5 CPU / 512 MB (the runtime image, `docker run --cpus 0.5 --memory 512m`)

| What | Result |
|---|---|
| Worker parent, peak resident memory | **78.8 MiB** |
| Guarded child, peak resident memory | **387.9 MiB** |
| The container (cgroup `memory.peak`, which also counts reclaimable file cache) | **512.0 MiB: the limit** |
| One fixed-plan run, start to completion | 21.1 s (statistics 2.9 s, Analyst 9.5 s against the stub) |
| The statistics stage at 2,000 simulations (now) | **3.2 s**, peak 199 MiB |
| The statistics stage at 10,000 simulations (step 11) | **8.7 s**, peak 239 MiB |
| The stuck-child limits | 900 s without a write; 1,800 s in all |

**Memory is close to the limit.** The run completed, but the container reached its 512 MiB limit; the sum of the two processes' peaks is 466.7 MiB, or 91%. **The owner decided to upgrade the worker to 1c-2g** (2026-10-08; item 6 above), in this branch, so it goes live with the 9b merge. For the record, the options reported were:
- **Upgrade the Render worker to 1c-2g**, about $25 instead of $7 a month: a `render.yaml` change, with the owner's go. Recommended before any live run on Render. (Chosen.)
- **Keep 512 MB.** A child killed for memory is taken up again by recovery, and after 3 recoveries the run fails `attempts_exhausted`, so no run is left running. But a run that always needs more memory would never finish there.
- **Shrink the child**, for example not loading the model libraries for code stages. That changes the guarded child's imports, a safeguard area, and would be its own reviewed step.

**The statistics stage fits easily.** At about 10,000 simulations it takes 8.7 s on 0.5 CPU, far inside 900 s and 1,800 s. The calibration is computed before the stage is written, so the run writes nothing during it; even so, it stays far below the stall limit.

How it was measured: the stub provider served the Analyst. A fixed-plan run was worked by `python -m hypocurate.worker --once` in the container, with a sampler reading each process's `VmHWM` every 0.1 s. The 10,000-simulation figure comes from a measurement-only fixed run on a scratch database, its plan locked with `n_simulations` 10,000. The scripts are in the packet.

**Worker parent imports:** it never imports dspy, litellm or scipy, which is tested. It does load numpy, through the source adapters' spreadsheet library (`openpyxl`), because the guarded runner's package imports the access layer. Moving that import after the child's file guard made the guard refuse a read of `/etc/mime.types`. Preloading `openpyxl` would change the guarded runner's `PRELOADED` list, a safeguard, so the move was undone (commit `f60a13b`). The 78.8 MiB above includes numpy.

## What was built (each commit on the branch)

| Commit | What |
|---|---|
| `dbf0e2e`, `cd230cd` | The approved plan saved on the branch; the owner's answer on recovery; b0 (dumps from `main`) |
| `9c999ed` | b1: migration 0008, `run_claim` |
| `6a5f965` | b2 and b3: `pipeline/queue.py`, the worker, `guarded.start_guarded` and the death signal, `orchestrator.work_guarded`, `pipeline/recovery.py`, the orchestrator's `recovered` rule |
| `f60a13b` | The lazy `openpyxl` import undone (above) |
| `3e539a6` | b4: the CLI through the claim; `--queue`, `queue`, `worker` |
| `823236a` | b5: the kill matrix; the sweep that finishes a missing narrower question; the step 2 idle-loop tests re-pointed |
| `a5ba354` | The register |
| `0b49e0c` | A test of the work lock (a second child of a held run is busy) |

## Migration 0008

`run_claim`, one row per claim, never deleted:
- its run, its worker (1–200 characters), the guarded child's pid (recorded once), and the claim's time and heartbeat (both the database's time);
- its release: once, at the database's time, with a reason from a fixed list, plus what recovery found (`found`, a JSON object);
- only an open run is claimed, and a partial unique index allows one open claim per run;
- while open, only the heartbeat, the pid (once), `found` and the release may change; once released, a claim is final.

The update trigger reads no run row, so a heartbeat never waits behind the run's lock. The downgrade refuses while a claim exists. Up, down and up, direct SQL and failed-upgrade tests are in `tests/test_migrations_step9b.py`.

## A claim, the heartbeat, and "dead"

**A claim** has two parts:
1. On its own autocommit lease connection, the worker takes the run's session lock CLAIM without waiting, and checks that the run's WORK lock is free.
2. In one transaction under the run's lock, it re-checks the run, closes a stale open claim as `lost`, records its claim, and starts the run (queued, or a confirmed waiting run, becomes running).

**The guarded child** holds WORK on its own connection for its whole work. A second child of the same run returns `busy`, writing nothing. While WORK is held, for example by an orphan child, no worker can claim the run.

**The heartbeat:** a thread of the worker writes every 15 s, on the claim row only.

**Dead:** a claim whose heartbeat is older than 120 s, with both locks free. A claim released for recovery or at shutdown is claimable at once.

**Order:** running runs first, then confirmed waiting runs, then queued runs in the order of dispatch.

**The worker** (`python -m hypocurate.worker [--once]`, also `hypocurate worker`):
- each cycle, it finishes a missing narrower question, then claims a run;
- if the run was running, it runs recovery's bookkeeping first;
- it starts the guarded child from its main thread and watches it: A4 (no write for 900 s, or 1,800 s in all) kills it, SIGTERM stops it;
- it releases the claim as `finished`, `waiting`, `stopped_for_recovery`, `child_stuck`, `child_failed` or `shutdown`;
- idle, it looks again every 60 s and logs whether the database answers, never its address.

**`run`, `dispatch` and `confirm`** work their run inline through the same claim and worker code (R1), printing what they printed before. With `--queue` they return at once for a worker. **`queue`** lists the open runs: stage, worker, heartbeat age, time since the last write, recoveries.

## Recovery

Recovery is bookkeeping, done in one transaction under the run's lock:
1. every model call still `started` is closed `interrupted`, so it counts at its maximum; the code is `recording_failed` when its stage ended on one, else `worker_stopped`;
2. every running stage is closed `failed` (`interrupted`); an Analyst stage also shows "explanation unavailable (interrupted)";
3. a run taken up more than 3 times fails `attempts_exhausted`.

It writes no plan, record, set, freeze or confirmation; a source scan checks this. The run then goes on by the normal path, with `recovered=True`:

| Cause | Planner | Critic | Analyst |
|---|---|---|---|
| Interrupted; recording failure; reservation failure | Repeated once (a second loss fails: "interrupted: the worker stopped during the Planner's request twice; dispatch the query again as a new run") | Remaining batches skipped; the run goes on | Not repeated; the run completes, "explanation unavailable" |
| Spending refusal | Fails `spending_refused` | Fails `spending_refused`; no Analyst request | Completes (A3, B2) |

**The kill matrix found a gap.** If the worker died between the partly-sufficient copy and the narrower question, the original was already completed, so no worker would ever claim it again, and 9a's fix runs only when the orchestrator is called on that run. The worker's sweep now finishes such a question each cycle, never creating a second.

## Tests

**The whole suite:** 2,123 tests (up from 2,021 on `main`), all passing locally (32 min 49 s) and in the test image rebuilt on this head (43 min 21 s). The suite grew by about 10 minutes, mostly the worker and kill-matrix tests, which run real worker processes.

**The GitHub run's suite step:** the last known figure is 19 min 8 s (the 9a main run, 37838900076; the job limit is 40 minutes since `4784d15`). The 9b branch run's figure does not exist yet when this summary is committed (the run starts with the push). It is reported with the push and added here in the first commit of the review round. From the local ratio it is expected at about 28 minutes, still under the limit (the owner asked for this figure in every summary).

**Mutation checks** (scratch copy, `PYTHONPATH`, one fault at a time; packet, section 7). There were 27 faults:
- **0008:** d01–d04;
- **claims and the heartbeat:** q01–q05;
- **the death signal (A3):** g01–g03;
- **the worker** (A4, shutdown, the child's pid, the `recovered` flag, the work lock): w01–w06;
- **recovery:** r01–r04;
- **the narrower sweep:** s01;
- **the orchestrator's rule after recovery:** o01–o04.

**The first run caught 24 of 26, and the control run was clean.** q02 and q03 survived, each hidden by the other guard: the candidate query and the claim transaction both refuse a live claim and an unconfirmed waiting run. Three tests now reach each guard on its own, and q05 (the transaction's own confirmation check) was added. test_queue.py was the only test file changed, and all five q faults were re-run: **all caught, control clean**.

**The images**, rebuilt on this head:
- the package's SHA-256 over every file is the same in the repository, the runtime image and the test image;
- the test image's `tests/` is identical to the repository's, and the runtime image holds no `tests/` or `docs/`;
- the runtime image's guard checks pass with its own package;
- the build cache is pruned after the rebuild (never the volumes).

**The reference comparison:** the five reference runs, and the whole orchestrator runs (fixed plan, Planner FCC, Planner BCC, the partly-sufficient original and its narrower question), are **byte-identical to `main`** (`c7458d0`). The orchestrator dumps run the orchestrator directly. The worker path is compared in the kill matrix: each run taken up after a kill gives the same fingerprints and results as an uninterrupted run of the same query.

**New test files (99 tests; the counts before the code):**
- `test_migrations_step9b.py` (30): 29 failed before 0008. Up/down/up passed: nothing above 0007 to round-trip.
- `test_guarded_parent.py` (6): 6 failed (no `start_guarded`).
- `test_queue.py` (12): 12 failed (no module).
- `test_worker.py` (11): failed. The old idle worker ignores `--once` and never exits, so the run was stopped.
- `test_recovery.py` (20): 14 of the first 18 failed. The 4 that passed are guards: the three spending refusals already stop as in 9a, and the source scan. Two were added later: the sweep, and the wording pin.
- `test_cli_step9b.py` (6): 6 failed.
- `test_kill_matrix.py` (14): written after the code. It found the narrower-question gap, which was fixed with its own test.

**The kill matrix:** a real worker process is killed with SIGKILL at each point:
- after the lock; between sources; before Checks; before Inclusion; before the freeze; mid-statistics;
- mid-Planner; before the narrowing; during the Critic's request; mid-Analyst;
- between the partly copy and the narrower question.

It also covers a restart with a run waiting at the lock, and criterion 14.4 bullets 2 and 4. After each kill:
- the child died within 2 s;
- the run was taken up again;
- no stage was left running and no call started;
- every lost call was counted at its maximum;
- no request was repeated except the one Planner repeat;
- the plan and freeze fingerprints and every analysis result equal those of an uninterrupted run of the same query.

**Two limits of the kill matrix, stated plainly:**
- **"Mid-Critic, batch 1 of 2" is not exercised.** The batch size is an agent setting recorded at dispatch, and with the test data there is one batch. The case kills the worker during the Critic's request.
- **The test stall waits on a lock the test holds**, not on a sleep. A killed child's batched statements stay queued in its database session, which goes on executing them; with a long sleep per row it would run for hours. Once the lock is released they drain at once and roll back, since no COMMIT ever comes.

**The same fact matters in production.** A killed child's session can hold the run's lock while it drains, until it rolls back. A recovery's claim then waits, and retries. A connection setting, `client_connection_check_interval`, would end such sessions sooner. That would change how the code connects to the database, so it is proposed here, not made.

**Changed tests (none weakened):**

| Test | Change | Reason |
|---|---|---|
| `test_health.py::test_worker_idles_and_checks_the_database` | **Renamed** `test_the_idle_worker_looks_for_work_every_sweep_and_checks_the_database`. The same checks on the new loop: idle every 60 s (`queue.SWEEP_SECONDS`), the database reachable logged. It uses a scratch database, since the worker now reads the queue's tables. | The step 2 idle loop is replaced by the worker |
| `test_health.py::test_worker_logs_an_unreachable_database` | `sleep=` became `wait=`; the same assertions (no address in the log) | Same |
| `test_migrations_step9a.py`: the head pin, two head-revision assertions | 0008 is the head | New migration |
| `test_migrations.expected_triggers` | Adds 0008's triggers | Same |
| `test_cli_step9a.py::test_confirm_takes_no_ceiling` | The pinned parameter list gains `to_queue`; still no ceiling | `confirm --queue` (R2) |
| `test_worker.py::test_the_worker_parent_loads_no_model_or_statistics_library` (new in 9b) | numpy taken off the list | numpy was my own addition; the plan names dspy, litellm and scipy (see "Worker parent imports") |

## Register

**147 entries.**
- **New:** `queue_and_claims`, `stuck_child_limits`, `recovery_policy`, `guarded_child_dies_with_parent`.
- **Reworded** (earlier wording in history): `worker_poll_interval` (it now names `queue.SWEEP_SECONDS`, still 60), `resumable_run`, `run_order_and_failures`.
- The wording is Claude Code's draft, for the owner's review.

## Left for step 10 (screens)

- the Confirm and Cancel buttons, Dispatch again, the queue under Review and dispatch, the month-cap message;
- run viewer polling and the waiting stage state;
- claim, heartbeat and recovery facts on the run page;
- criterion 14.4 bullets 1 (close the browser) and 3 (web restart);
- labels on lists.

A test checks that the web code imports none of the queue, the worker, the orchestrator or recovery.

## Open items

1. **Memory:** decided; the worker moves to 1c-2g with the merge (item 6).
2. **`client_connection_check_interval`:** proposed (above).
3. **The Render worker** has no `ANTHROPIC_API_KEY`; the owner adds it when live runs on Render are wanted.
4. **The worker on Render runs the code of the next merge.** `render.yaml` already starts `python -m hypocurate.worker`, now the real worker.

## Questions for the reviewer

1. Can two workers, or a worker and an orphan child, ever work one run at once? Can a cancel race a start?
2. Does recovery ever repeat a paid request beyond the one Planner repeat, send a request after a spending refusal, or skip counting a lost call at its maximum?
3. Can a run be left running for good (stuck child, lost claim, repeated crashes)?
4. Does the heartbeat's exception to the locking protocol open any race?
5. Does `start_guarded` with the death signal leave a window in which a child runs unwatched?
6. Migration 0008: do its rules hold against direct SQL, and is the downgrade exact?
7. Is any claim in this summary, the code or the register stronger than the code supports?

## 2. Code diff (`c7458d0..HEAD`, the package with migration 0008; the register is in section 5)

```diff
diff --git a/hypocurate/access/guarded.py b/hypocurate/access/guarded.py
index fc1dc19..c937985 100644
--- a/hypocurate/access/guarded.py
+++ b/hypocurate/access/guarded.py
@@ -21,6 +21,13 @@ The guard's refusals come back on the child's standard error; the parent copies
 the audit log as a failure (code `file_guard`) for the run given in `audit`, or to the
 process log if no run is given or the database cannot take it.
 
+Step 9b (owner's addition A3, 2026-10-08): `start_guarded` starts the same child without waiting for it, for the
+worker, which must keep its heartbeat going and watch the child while it works. It may be called only from the
+main thread, and it passes the parent's pid: the child then sets PR_SET_PDEATHSIG(SIGKILL) first thing, so it
+dies with the thread that started it (the main thread, which lives as long as the worker), and exits at once
+(`PARENT_GONE_EXIT`) if its parent is not that process any more (the parent died before the signal was set).
+`run_guarded` is unchanged.
+
 This is a tripwire against *accidental* file access by trusted code, not a sandbox (see
 `file_guard`). This is the only place that installs it. The pipeline's entry points (the
 command line's run command, step 8; the worker's run of a claimed job, step 9) run each
@@ -33,9 +40,11 @@ import importlib
 import json
 import os
 import shutil
+import signal
 import subprocess
 import sys
 import tempfile
+import threading
 from typing import Any
 
 from hypocurate.access import file_guard
@@ -59,6 +68,8 @@ class GuardedRunError(Exception):
 
 
 MAX_REPORTED = 100  # refusals copied into the audit log per run; the rest are counted
+PARENT_GONE_EXIT = 3  # step 9b (A3): the child found that the process that started it is gone
+PR_SET_PDEATHSIG = 1  # linux/prctl.h
 
 
 def _as_text(captured) -> str:
@@ -112,17 +123,91 @@ def run_guarded(target: str, payload: Any = None, env: dict[str, str] | None = N
     finally:
         shutil.rmtree(scratch, ignore_errors=True)
     _report_refusals(completed.stderr, audit)
-    lines = completed.stdout.strip().splitlines()
+    return _answer(completed.stdout, completed.stderr, completed.returncode)
+
+
+def _answer(stdout: str, stderr: str, returncode: int) -> Any:
+    lines = stdout.strip().splitlines()
     try:
         answer = json.loads(lines[-1])
     except (IndexError, ValueError):
-        raise GuardedRunError(f"the guarded process gave no answer (exit {completed.returncode}): "
-                              f"{completed.stderr.strip()[-2000:]}") from None
+        raise GuardedRunError(f"the guarded process gave no answer (exit {returncode}): {stderr.strip()[-2000:]}") from None
     if not answer.get("ok"):
         raise GuardedRunError(answer.get("error", "unknown error"))
     return answer["result"]
 
 
+class GuardedChild:
+    """A guarded child started by `start_guarded`: its pid, and its answer once it ends."""
+
+    def __init__(self, proc: subprocess.Popen, scratch: str, audit):
+        self.proc, self.pid, self._scratch, self._audit = proc, proc.pid, scratch, audit
+        self._out = self._err = ""
+
+    def wait_for(self, seconds: float) -> bool:
+        """Waits up to `seconds` for the child to end (reading its output meanwhile); True once it has ended."""
+        try:
+            out, err = self.proc.communicate(timeout=seconds)
+        except subprocess.TimeoutExpired:
+            return False
+        self._out, self._err = out or "", err or ""
+        return True
+
+    def stop(self, sig: int = signal.SIGKILL) -> None:
+        """Ends the child (SIGKILL by default) and waits for it."""
+        if self.proc.poll() is None:
+            self.proc.send_signal(sig)
+        self.wait_for(30)
+
+    def result(self, timeout: float | None = None) -> Any:
+        """The child's answer (GuardedRunError if it failed); its refusals reported; its scratch removed."""
+        try:
+            if not self.wait_for(timeout if timeout is not None else 10 ** 9):
+                self.stop()
+                raise subprocess.TimeoutExpired(self.proc.args, timeout)
+        finally:
+            _report_refusals(_as_text(self._err), self._audit)
+            shutil.rmtree(self._scratch, ignore_errors=True)
+        return _answer(self._out, self._err, self.proc.returncode)
+
+    def discard(self) -> None:
+        """For a child that was stopped: its refusals reported and its scratch removed; no answer is read."""
+        _report_refusals(_as_text(self._err), self._audit)
+        shutil.rmtree(self._scratch, ignore_errors=True)
+
+
+def start_guarded(target: str, payload: Any = None, env: dict[str, str] | None = None, audit=None) -> GuardedChild:
+    """Starts `target(payload)` in a guarded child that dies with this process's main thread (A3), and returns at
+    once. Only from the main thread: the death signal follows the thread that started the child."""
+    if threading.current_thread() is not threading.main_thread():
+        raise RuntimeError("a guarded child is started only from the main thread (it dies with the thread that "
+                           "started it)")
+    if not target.startswith("hypocurate.") or ":" not in target:
+        raise ValueError(f"target {target!r} must be 'hypocurate.<module>:<function>'")
+    scratch = tempfile.mkdtemp(prefix=file_guard.SCRATCH_PREFIX, dir=file_guard.SYSTEM_TEMP)
+    try:
+        proc = subprocess.Popen([sys.executable, "-m", MODULE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
+                                stderr=subprocess.PIPE, text=True, env=env if env is not None else dict(os.environ))
+        proc.stdin.write(json.dumps({"target": target, "payload": payload, "scratch": scratch,
+                                     "parent_pid": os.getpid()}))
+        proc.stdin.close()
+    except Exception:
+        shutil.rmtree(scratch, ignore_errors=True)
+        raise
+    return GuardedChild(proc, scratch, audit)
+
+
+def _die_with_parent(parent_pid: int) -> None:
+    """A3: the kernel sends SIGKILL when the thread that started this process ends; then the fork race is closed by
+    checking that the parent is still the process that started it."""
+    import ctypes
+    libc = ctypes.CDLL("libc.so.6", use_errno=True)
+    if libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL, 0, 0, 0) != 0:
+        os._exit(PARENT_GONE_EXIT)  # the death signal could not be set: never run unwatched
+    if os.getppid() != parent_pid:
+        os._exit(PARENT_GONE_EXIT)
+
+
 def existing_path_entries(paths: list[str]) -> list[str]:
     """The import-path entries that exist, in order (step 8a, owner 2026-10-06)."""
     return [p for p in paths if os.path.exists(p)]
@@ -130,6 +215,8 @@ def existing_path_entries(paths: list[str]) -> list[str]:
 
 def _main() -> int:
     request = json.loads(sys.stdin.read())
+    if request.get("parent_pid") is not None:  # step 9b (A3): started by `start_guarded`
+        _die_with_parent(int(request["parent_pid"]))
     scratch = request["scratch"]
     for name in SCRATCH_ENV:
         os.environ[name] = scratch
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 956b31d..a45ec89 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -49,16 +49,22 @@ def main(argv: list[str] | None = None) -> int:
     run.add_argument("--fixed-plan", action="store_true", help="the reference plan, Planner bypassed (14.1a)")
     run.add_argument("--test-data", action="store_true", help="mark the run as a test with constructed data")
     run.add_argument("--ceiling", help="the most this run's model calls may cost, in USD (refused above it)")
+    run.add_argument("--queue", action="store_true", help="dispatch and return at once; a worker runs it (step 9b)")
     dispatch = sub.add_parser("dispatch", help="dispatch a submitted query by its number and run it (may cost money)")
     dispatch.add_argument("number", help="the query number, e.g. Q-0002")
     dispatch.add_argument("--by", help="the name of the person confirming the domain (not with --again)")
     dispatch.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
+    dispatch.add_argument("--queue", action="store_true", help="dispatch and return at once; a worker runs it")
     dispatch.add_argument("--again", action="store_true",
                           help="a new run of a query whose earlier run ended (refused while another run is open)")
     confirm = sub.add_parser("confirm", help="show a waiting run's question as tested; a named person confirms it, "
                                              "and the run goes on (may cost money)")
     confirm.add_argument("run", type=int)
     confirm.add_argument("--by", required=True, help="the name of the person confirming")
+    confirm.add_argument("--queue", action="store_true", help="record the confirmation; a worker runs the rest")
+    sub.add_parser("queue", help="list the queued, waiting and running runs, with their claims and heartbeats")
+    worker = sub.add_parser("worker", help="the background worker: claims runs and works them (PRD 12)")
+    worker.add_argument("--once", action="store_true", help="claim one run, if there is one, work it and stop")
     cancel = sub.add_parser("cancel", help="cancel a queued or waiting run")
     cancel.add_argument("run", type=int)
     cancel.add_argument("--by", required=True, help="the name of the person cancelling")
@@ -75,7 +81,10 @@ def main(argv: list[str] | None = None) -> int:
         reachable = database_reachable(engine)
         print("database reachable" if reachable else "database NOT reachable")
         return 0 if reachable else 1
-    if args.command in ("run", "dispatch", "show", "confirm", "cancel"):
+    if args.command == "worker":
+        from hypocurate import worker as background
+        return background.run(once=args.once, engine=engine)
+    if args.command in ("run", "dispatch", "show", "confirm", "cancel", "queue"):
         from hypocurate.cli_runs import command
         return command(args, engine)
     return _sources(args, engine)
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index 6952c08..37a6507 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -45,7 +45,10 @@ def command(args, engine: Engine) -> int:
             print(json.dumps({"run": args.run, "status": "failed", "failure": reason}, ensure_ascii=False))
             return 0
         if args.command == "confirm":  # fix round 1, finding 4: no ceiling here; it is stored at dispatch
-            return _confirm(engine, args.run, args.by)
+            return _confirm(engine, args.run, args.by, getattr(args, "queue", False))
+        if args.command == "queue":
+            print(json.dumps(queue_rows(engine), indent=2, ensure_ascii=False, default=str))
+            return 0
         ceiling = _ceiling(args.ceiling)
         if args.command == "run":
             q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
@@ -76,6 +79,8 @@ def command(args, engine: Engine) -> int:
         print(f"error: {error}", file=sys.stderr)
         return 1
     print(json.dumps({"query": number, "run": run_id, "status": "dispatched"}), flush=True)
+    if getattr(args, "queue", False):  # step 9b (R1): returns at once; a worker takes the run up
+        return 0
     return _run(engine, run_id, ceiling)
 
 
@@ -92,24 +97,78 @@ def _ceiling(value: str | None) -> Decimal | None:
 
 
 def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
-    """Two guarded calls: up to the rules lock (or the wait for a person, step 9a), then on to the end. Between them
-    the original claim and the question as tested are printed (owner's decision B), before the run goes on."""
-    from hypocurate.access.guarded import GuardedRunError, run_guarded
-    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None}
-    try:
-        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "prepare"},
-                             timeout=3600, audit=(engine, run_id))
-        print(json.dumps({"claim": _claim(engine, run_id), "question_as_tested": report.get("question_as_tested")},
-                         ensure_ascii=False), flush=True)
-        if report.get("ready"):
-            rest = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "proceed"},
-                               timeout=3600, audit=(engine, run_id))
-            report = {**rest, "stages": report["stages"] + rest["stages"]}
-    except GuardedRunError:
-        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
+    """Step 9b (R1): the run is worked inline through the same claim and worker code as the background worker: up to
+    the rules lock (or the wait for a person, step 9a), then on to the end, in two guarded children under one claim.
+    Between them the original claim and the question as tested are printed (owner's decision B), before the run goes
+    on. The ceiling is the one stored at dispatch (step 9a)."""
+    return _work_inline(engine, run_id, ("prepare", "proceed"), print_reading=True)
+
+
+def _work_inline(engine: Engine, run_id: int, phases: tuple, print_reading: bool) -> int:
+    from hypocurate import worker
+    from hypocurate.pipeline import queue
+    claim = queue.claim(engine, run_id, worker.worker_name())
+    if claim is None:  # a worker holds it: wait until it ends, waits or stops, then show what is stored
+        _wait_for(engine, run_id)
+        return _print_shown(engine, run_id, {"stages": None, "failure": None})
+    reports = {}
+
+    def on_phase(phase: str, report: dict) -> None:
+        reports[phase] = report
+        if phase == "prepare" and print_reading:
+            print(json.dumps({"claim": _claim(engine, run_id), "question_as_tested": report.get("question_as_tested")},
+                             ensure_ascii=False), flush=True)
+
+    out = worker.work(engine, claim, phases=phases, on_phase=on_phase)
+    if out["release"] in ("child_failed", "child_stuck", "shutdown"):
+        print(f"error: run {run_id} did not finish in the guarded process ({out['why']}; see the process log); "
               f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
         return 1
-    return _print_shown(engine, run_id, report)
+    stages = [s for p in phases if p in reports for s in (reports[p].get("stages") or [])]
+    last = reports.get(phases[-1]) or reports.get(phases[0]) or {}
+    return _print_shown(engine, run_id, {"stages": stages, "failure": last.get("failure")})
+
+
+def _wait_for(engine: Engine, run_id: int, poll: float = 2.0) -> None:
+    """Until the run ends, waits for a person, or has no open claim (a worker let it go)."""
+    import time
+    from hypocurate.pipeline import queue
+    deadline = time.monotonic() + queue.RUN_TIMEOUT_SECONDS
+    while time.monotonic() < deadline:
+        with engine.connect() as conn:
+            status, held = conn.execute(text(
+                "SELECT r.status, EXISTS (SELECT 1 FROM run_claim c WHERE c.run_id = r.id AND c.released_at IS NULL) "
+                "FROM run r WHERE r.id = :r"), dict(r=run_id)).one()
+        if status in ("completed", "failed", "waiting") or not held:
+            return
+        time.sleep(poll)
+
+
+def queue_rows(engine: Engine) -> list[dict]:
+    """`queue` (R2): every queued, waiting or running run, with its stage, its claim's worker and heartbeat age, the
+    time since the run last wrote anything (A4), and how often it was taken up again."""
+    from hypocurate.access.stage import actual_stage
+    from hypocurate.pipeline import confirmation, queue
+    out = []
+    with engine.connect() as conn:
+        runs = conn.execute(text(
+            "SELECT r.id, r.status, h.number, EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS "
+            "confirmed, c.worker, extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age, "
+            "(SELECT count(*) FROM run_claim x WHERE x.run_id = r.id AND x.released_at IS NOT NULL AND "
+            "x.release_reason NOT IN ('waiting', 'finished')) AS recoveries FROM run r "
+            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+            "LEFT JOIN run_claim c ON c.run_id = r.id AND c.released_at IS NULL "
+            "WHERE r.status IN ('queued', 'waiting', 'running') ORDER BY r.queued_at, r.id")).all()
+        for r in runs:
+            out.append({
+                "run": r.id, "query": r.number, "status": r.status, "stage": actual_stage(conn, r.id, r.status),
+                "waiting_for": (confirmation.WAITING_FOR if r.status == "waiting" and not r.confirmed else
+                                "a worker (confirmed)" if r.status == "waiting" else None),
+                "worker": r.worker, "heartbeat_age_seconds": round(float(r.heartbeat_age), 1)
+                if r.heartbeat_age is not None else None,
+                "seconds_since_last_write": round(queue.seconds_since_last_write(conn, r.id), 1),
+                "recoveries": int(r.recoveries)})
+    return out
 
 
 def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
@@ -125,10 +184,9 @@ def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
     return 0 if shown["status"] in ("completed", "failed", "waiting") else 1
 
 
-def _confirm(engine: Engine, run_id: int, by: str) -> int:
+def _confirm(engine: Engine, run_id: int, by: str, to_queue: bool = False) -> int:
     """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest. The run's
     ceiling is the one stored at dispatch (fix round 1, finding 4: a lower one given here would be lost on a restart)."""
-    from hypocurate.access.guarded import GuardedRunError, run_guarded
     from hypocurate.pipeline import confirmation
     with engine.connect() as conn:
         status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
@@ -139,15 +197,10 @@ def _confirm(engine: Engine, run_id: int, by: str) -> int:
     content, words = confirmation.show(engine, run_id)
     print(words, flush=True)
     confirmation.confirm(engine, run_id, by, shown=content)
-    payload = {"run_id": run_id, "ceiling": None, "phase": "proceed"}
-    try:
-        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", payload, timeout=3600,
-                             audit=(engine, run_id))
-    except GuardedRunError:
-        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
-              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
-        return 1
-    return _print_shown(engine, run_id, report)
+    if to_queue:  # step 9b (R2): confirmed; a worker takes it up
+        print(json.dumps({"run": run_id, "status": "waiting", "confirmed": True, "queued": True}), flush=True)
+        return 0
+    return _work_inline(engine, run_id, ("proceed",), print_reading=False)
 
 
 def _claim(engine: Engine, run_id: int) -> str:
diff --git a/hypocurate/db/migrations/versions/0008_run_claim.py b/hypocurate/db/migrations/versions/0008_run_claim.py
new file mode 100644
index 0000000..06317e3
--- /dev/null
+++ b/hypocurate/db/migrations/versions/0008_run_claim.py
@@ -0,0 +1,147 @@
+"""Claims: a worker's hold on one run, with its heartbeat (build step 9b).
+
+Revision ID: 0008
+Revises: 0007
+Create Date: 2026-10-08
+
+Approved by the owner on 2026-10-08 (the step 9 plan, R6; docs/reviews/step09b_plan.md), subject to the
+second-model review before merging. 0001 to 0007 untouched: no earlier function is replaced.
+
+run_claim, one row per claim, never deleted:
+- the run, the worker (1-200 characters, `host:pid`), the guarded child's pid (recorded once), the claim's time
+  and its heartbeat (both the database's time), and how it was released: once, at the database's time, with a
+  reason from a fixed list (`RELEASE_REASONS`), and what recovery found (`found`, a JSON object);
+- only an open run (queued, running or waiting) is claimed, and at most one claim per run is open (a partial
+  unique index);
+- while a claim is open only its heartbeat, its child's pid (once), `found` and the release may change; once
+  released it is final.
+The heartbeat is written on the claim row, not the run row (R6), so it never waits behind a transaction that holds
+the run's lock: the update trigger reads no run row. A named exception to the locking protocol, like audit rows.
+
+Works with the previous release's code: it never reads or writes run_claim. The live database has never had a run.
+
+Downgrade refuses while any claim exists (claims are history), then drops what 0008 added.
+
+Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it keeps
+working with the previous release's code; and it has a downgrade.
+"""
+from alembic import op
+import sqlalchemy as sa
+from sqlalchemy.dialects import postgresql
+
+revision = '0008'
+down_revision = '0007'
+branch_labels = None
+depends_on = None
+
+# Copied here so the migration does not change when the code does (tests check they equal queue.RELEASE_REASONS).
+RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
+WORKER_MAX = 200
+
+
+def _in(column: str, values) -> str:
+    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"
+
+
+FUNCTIONS = [
+    # A claim of an open run, at the database's time.
+    """
+    CREATE FUNCTION hc_run_claim_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF hc_lock_run(NEW.run_id) NOT IN ('queued', 'running', 'waiting') THEN
+            PERFORM hc_reject('only an open run is claimed (queued, running or waiting)');
+        END IF;
+        IF NEW.released_at IS NOT NULL OR NEW.release_reason IS NOT NULL OR NEW.found IS NOT NULL THEN
+            PERFORM hc_reject('a claim is released after it is made');
+        END IF;
+        NEW.claimed_at := now();
+        NEW.heartbeat_at := NEW.claimed_at;
+        RETURN NEW;
+    END $$
+    """,
+    # While open: the heartbeat (the database's time), the child's pid once, what recovery found, the release once.
+    # Reads no run row (R6): a heartbeat never waits behind the run's lock.
+    """
+    CREATE FUNCTION hc_run_claim_update() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF OLD.released_at IS NOT NULL THEN
+            PERFORM hc_reject('a released claim is final');
+        END IF;
+        IF NEW.run_id <> OLD.run_id OR NEW.worker <> OLD.worker OR NEW.claimed_at <> OLD.claimed_at THEN
+            PERFORM hc_reject('what a claim records cannot change');
+        END IF;
+        IF OLD.child_pid IS NOT NULL AND NEW.child_pid IS DISTINCT FROM OLD.child_pid THEN
+            PERFORM hc_reject('a claim''s child is recorded once');
+        END IF;
+        IF NEW.heartbeat_at IS DISTINCT FROM OLD.heartbeat_at THEN
+            NEW.heartbeat_at := clock_timestamp();
+        END IF;
+        IF NEW.released_at IS NOT NULL THEN
+            NEW.released_at := clock_timestamp();
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+]
+FUNCTION_NAMES = ["hc_run_claim_insert()", "hc_run_claim_update()"]
+
+NO_DELETE = ["run_claim"]
+CHECKED = [
+    ("run_claim", "INSERT", "hc_run_claim_insert", "hc_run_claim_insert"),
+    ("run_claim", "UPDATE", "hc_run_claim_update", "hc_run_claim_update"),
+]
+TRIGGERS = (
+    [f"CREATE TRIGGER hc_{t}_no_delete BEFORE DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION hc_no_delete()"
+     for t in NO_DELETE]
+    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION hc_no_delete()"
+       for t in NO_DELETE]
+    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
+       for table, event, t, f in CHECKED]
+)
+
+
+def upgrade() -> None:
+    op.create_table(
+        'run_claim',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('run_id', sa.BigInteger(), nullable=False),
+        sa.Column('worker', sa.Text(), nullable=False),
+        sa.Column('child_pid', sa.Integer(), nullable=True),
+        sa.Column('claimed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.Column('heartbeat_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
+        sa.Column('release_reason', sa.Text(), nullable=True),
+        sa.Column('found', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
+        sa.CheckConstraint(f"length(btrim(worker)) BETWEEN 1 AND {WORKER_MAX}", name=op.f('ck_run_claim_worker_named')),
+        sa.CheckConstraint(f"release_reason IS NULL OR {_in('release_reason', RELEASE_REASONS)}",
+                           name=op.f('ck_run_claim_release')),
+        sa.CheckConstraint("(released_at IS NULL) = (release_reason IS NULL)",
+                           name=op.f('ck_run_claim_released_with_reason')),
+        sa.CheckConstraint("found IS NULL OR jsonb_typeof(found) = 'object'", name=op.f('ck_run_claim_found_object')),
+        sa.CheckConstraint("child_pid IS NULL OR child_pid > 0", name=op.f('ck_run_claim_child_pid')),
+        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_claim_run_id')),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_run_claim')),
+    )
+    op.create_index('uq_run_claim_open', 'run_claim', ['run_id'], unique=True,
+                    postgresql_where=sa.text('released_at IS NULL'))
+    for f in FUNCTIONS:
+        op.execute(f)
+    for t in TRIGGERS:
+        op.execute(t)
+
+
+IN_USE = """
+    DO $$
+    BEGIN
+        IF EXISTS (SELECT 1 FROM run_claim) THEN
+            RAISE EXCEPTION 'hypocurate: migration 0008 is in use (a claim exists); not downgraded';
+        END IF;
+    END $$
+"""
+
+
+def downgrade() -> None:
+    op.execute(IN_USE)
+    op.drop_table('run_claim')
+    for f in FUNCTION_NAMES:
+        op.execute(f"DROP FUNCTION {f}")
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index cbfb137..b95c1e6 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -412,6 +412,33 @@ class RulesConfirmation(Base):
     )
 
 
+# Step 9b (0008): how a claim ends; the same list as pipeline/queue.RELEASE_REASONS (tests check both).
+RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
+
+
+class RunClaim(Base):
+    """Step 9b (0008; R6): a worker's hold on one open run, with the guarded child's pid (once), its heartbeat (on
+    this row, never the run row) and how it was released (once). One open claim per run. Never deleted."""
+    __tablename__ = "run_claim"
+    id: Mapped[int] = pk()
+    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
+    worker: Mapped[str] = mapped_column(Text)
+    child_pid: Mapped[int | None] = mapped_column(Integer)
+    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
+    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
+    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
+    release_reason: Mapped[str | None] = mapped_column(Text)
+    found: Mapped[dict | None] = mapped_column(JSONB)
+    __table_args__ = (
+        Index("uq_run_claim_open", "run_id", unique=True, postgresql_where=sql("released_at IS NULL")),
+        CheckConstraint("length(btrim(worker)) BETWEEN 1 AND 200", name="worker_named"),
+        CheckConstraint(f"release_reason IS NULL OR {one_of('release_reason', RELEASE_REASONS)}", name="release"),
+        CheckConstraint("(released_at IS NULL) = (release_reason IS NULL)", name="released_with_reason"),
+        CheckConstraint("found IS NULL OR jsonb_typeof(found) = 'object'", name="found_object"),
+        CheckConstraint("child_pid IS NULL OR child_pid > 0", name="child_pid"),
+    )
+
+
 class Plan(Base):
     """The locked plan (PRD 5.1, 5.6). Inserted at the rules lock, never changed.
     The columns the database checks against are explicit; the rest is `content`."""
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
index 8bd6ebc..d918076 100644
--- a/hypocurate/pipeline/orchestrator.py
+++ b/hypocurate/pipeline/orchestrator.py
@@ -52,6 +52,7 @@ from hypocurate.pipeline import analysis, checkpoints, checks, completion, confi
 from hypocurate.pipeline import narrowing, queries, reading
 from hypocurate.pipeline.agents import analyst, critic, planner
 from hypocurate.pipeline.agents.lm import RUN_STOPS
+from hypocurate.pipeline.recovery import PLANNER_REPEATS, RECOVERABLE
 from hypocurate.pipeline.writes import Refused, write
 
 SPENDING = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
@@ -67,6 +68,8 @@ REASONS = {
     "narrower_plan_missing": "the original's narrowing decision holds no narrower plan",
     "spending_refused": "a spending cap or ceiling was reached before the request was sent",
     "refused": "a checkpoint or write refused",
+    # Step 9b (owner, Q3): the Planner's request was lost a second time.
+    "interrupted": "the worker stopped during the Planner's request twice; dispatch the query again as a new run",
 }
 
 
@@ -124,16 +127,27 @@ def _stage_code(row) -> str:
     return (row.output or {}).get("code") if isinstance(row.output, dict) else None
 
 
-def _agent_stop(engine: Engine, run_id: int, stage: str) -> str | None:
+def _agent_stop(engine: Engine, run_id: int, stage: str, recovered: bool = False) -> str | None:
     """Fix round 1, finding 1: the code of a stop the role's latest stored stage holds (a recording or reservation
-    failure, or a stage left running), whatever its status; None when there is no such stop."""
+    failure, or a stage left running), whatever its status; None when there is no such stop. Step 9b: after recovery
+    a lost request (`recovery.RECOVERABLE`) is no stop: the run goes on without asking the role again."""
     latest = _stored(engine, run_id, stage, done=False)
     if latest is None or latest.status in ("done", "skipped"):
         return None
     code = _stage_code(latest)
+    if recovered and code in RECOVERABLE:
+        return None
     return code if code in RUN_STOPS or code == LEFT_RUNNING else None
 
 
+def _lost(engine: Engine, run_id: int, stage: str) -> int:
+    """How many of the role's stages ended with a lost request (`recovery.RECOVERABLE`)."""
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = :s AND status = "
+                                 "'failed' AND output->>'code' = ANY(:c)"),
+                            dict(r=run_id, s=stage, c=list(RECOVERABLE))).scalar_one()
+
+
 def _critic_failures(engine: Engine, run_id: int) -> list:
     """The codes of the Critic's stored stages that did not end done or skipped, in order (as `run_critic` reports
     its batches' failures)."""
@@ -148,19 +162,21 @@ def _exists(engine: Engine, sql: str, run_id: int) -> bool:
         return bool(conn.execute(text(f"SELECT EXISTS ({sql})"), dict(r=run_id)).scalar_one())
 
 
-def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
+        recovered: bool = False) -> RunReport:
     """Runs the run to its end (completed or failed), to its wait for a person's confirmation, or leaves it running
     if a call stayed open: `prepare`, then, unless the run ended or waits there, `proceed`."""
-    report = prepare(engine, run_id, ceiling=ceiling, client_options=client_options)
+    report = prepare(engine, run_id, ceiling=ceiling, client_options=client_options, recovered=recovered)
     if not report.ready:
         return report
-    rest = proceed(engine, run_id, ceiling=ceiling, client_options=client_options)
+    rest = proceed(engine, run_id, ceiling=ceiling, client_options=client_options, recovered=recovered)
     rest.stages = report.stages + rest.stages
     rest.question_as_tested = report.question_as_tested
     return rest
 
 
-def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
+            recovered: bool = False) -> RunReport:
     """Up to the rules lock: start; the narrower question's plan check, the fixed plan, or the Planner and the
     narrowing decision (the partly-sufficient path ends here). A run whose plan comes from a model's answer then
     waits (step 9a). `ready` when the run goes on to `proceed` now; the question as tested is in the report (owner's
@@ -205,9 +221,14 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         stored = _stored(engine, run_id, "planner", done=False)
         if stored is not None and stored.status != "done":  # fix round 1, finding 1: an earlier stop stays a stop
             code = _stage_code(stored)
-            if stored.status == "running" or code in RUN_STOPS:
+            if recovered and code in RECOVERABLE:  # step 9b (owner, Q3): the Planner is repeated once
+                if _lost(engine, run_id, "planner") > PLANNER_REPEATS:
+                    return _failed(engine, report, "interrupted")
+                stored = None
+            elif stored.status == "running" or code in RUN_STOPS:
                 return _stopped(engine, report, code)
-            return _failed(engine, report, "spending_refused" if code in SPENDING else "planner_failed", code)
+            else:
+                return _failed(engine, report, "spending_refused" if code in SPENDING else "planner_failed", code)
         if stored is None:
             result = planner.run_planner(engine, run_id, **agent_kw)
             report.stages.append("planner")
@@ -231,7 +252,7 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if decision["result"] == "claim_not_one_plan":
             return _failed(engine, report, "claim_not_one_plan", decision["reason"])
         if decision["result"] == "partly_sufficient":
-            stop = _agent_stop(engine, run_id, "analyst")
+            stop = _agent_stop(engine, run_id, "analyst", recovered)
             if stop:
                 return _stopped(engine, report, stop)
             if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
@@ -247,7 +268,8 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         return _failed(engine, report, "refused", refused.code)
 
 
-def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None,
+            recovered: bool = False) -> RunReport:
     """From the rules lock to the end. A waiting run goes on only once a person has confirmed it (it is then running
     again); a waiting run that no one confirmed is left as it is. The plan is `confirmation.plan_to_lock`'s, built
     again from what is stored, so nothing is carried between the two in memory. Each step after the lock runs only
@@ -280,7 +302,8 @@ def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
             failures = c.failures
         else:  # fix round 1, finding 1: the Critic's stored stages decide, as they did when it ran
             failures = _critic_failures(engine, run_id)
-        stops = [f for f in failures if f in RUN_STOPS or f == LEFT_RUNNING]
+        # Step 9b (owner, 2026-10-08): after recovery a lost Critic request is not repeated and the run goes on.
+        stops = [f for f in failures if (f in RUN_STOPS or f == LEFT_RUNNING) and not (recovered and f in RECOVERABLE)]
         if stops:
             return _stopped(engine, report, stops[0])
         spent = [f for f in failures if f in SPENDING]
@@ -295,7 +318,7 @@ def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
         if _stored(engine, run_id, "statistics") is None:
             analysis.run_statistics(engine, run_id)
         report.stages += ["inclusion", "dataset freeze", "statistics"]
-        stop = _agent_stop(engine, run_id, "analyst")
+        stop = _agent_stop(engine, run_id, "analyst", recovered)
         if stop:
             return _stopped(engine, report, stop)
         if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
@@ -398,3 +421,26 @@ def run_guarded(payload: dict) -> dict:
         return json.loads(json.dumps(r.__dict__, default=str))
     finally:
         engine.dispose()
+
+
+def work_guarded(payload: dict) -> dict:
+    """The worker's child (step 9b): holds the run's work lock on its own connection for its whole work (another child
+    of the same run is refused it and returns `busy`, writing nothing), then runs the phase. The lock goes when this
+    process ends, however it ends."""
+    from hypocurate.config import load_settings
+    from hypocurate.db.engine import make_engine
+    from hypocurate.pipeline import queue
+    engine = make_engine(load_settings(web=False).database_url)
+    run_id = int(payload["run_id"])
+    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
+    try:
+        holder.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-work-{run_id}"))
+        if not holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(run_id))).scalar():
+            return {"busy": True}
+        phase = {"prepare": prepare, "proceed": proceed}.get(payload.get("phase"), run)
+        r = phase(engine, run_id, client_options=payload.get("client_options"),
+                  recovered=bool(payload.get("recovered")))
+        return json.loads(json.dumps(r.__dict__, default=str))
+    finally:
+        holder.close()
+        engine.dispose()
diff --git a/hypocurate/pipeline/queue.py b/hypocurate/pipeline/queue.py
new file mode 100644
index 0000000..5dae406
--- /dev/null
+++ b/hypocurate/pipeline/queue.py
@@ -0,0 +1,239 @@
+"""The queue: claims, the heartbeat and the worker's hold on a run (build step 9b; docs/reviews/step09b_plan.md,
+"Claims, heartbeat, and dead"; register 'queue_and_claims').
+
+**A claim** (`claim_next`, or `claim` for one run):
+1. on its own lease connection (autocommit, so no transaction stays open), the worker takes, without waiting, a session
+   advisory lock (CLAIM, run), then checks that (WORK, run) is free (the guarded child holds WORK for its whole work;
+   an orphan child still holding it keeps every worker off the run);
+2. in one locked transaction (the locking protocol: `hc_write_lock(p_run)` first) it re-checks the run, closes a stale
+   open claim as `lost`, records its claim (migration 0008: one open claim per run) and starts the run: queued ->
+   running, or a confirmed waiting run -> running.
+Every worker takes CLAIM before anything else, so two workers can never both hold a run; a cancel and a start are
+serialised by the run's lock.
+
+**Claimable:** a queued run with no open claim; a waiting run a person has confirmed, with no open claim; a running
+run with no open claim (released for recovery, or never claimed) or whose open claim's heartbeat is older than
+`STALE_SECONDS` (its worker is taken to be dead), always subject to the two locks being free. Running runs come
+first (they are taken up again), then confirmed waiting runs, then queued runs in the order of dispatch.
+
+**The heartbeat** (`Heartbeat`, owner R6) is a thread of the worker that writes `run_claim.heartbeat_at` every
+`HEARTBEAT_SECONDS`, on the claim row, never the run row, so it never waits behind the run's lock (a named exception
+to the locking protocol, like audit rows). A release (`release`) follows the protocol.
+
+This module is imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
+"""
+from __future__ import annotations
+
+import json
+import logging
+import threading
+from dataclasses import dataclass
+
+from sqlalchemy import Connection, Engine, bindparam, text
+from sqlalchemy.dialects.postgresql import JSONB
+
+from hypocurate.db.retry import run_transaction
+
+LOG = logging.getLogger("hypocurate.worker")
+
+# How a claim ends (migration 0008 holds the same list).
+RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
+# The owner's approved values (step 9 plan; register 'queue_and_claims', 'stuck_child_limits').
+HEARTBEAT_SECONDS = 15
+STALE_SECONDS = 120        # 8 missed beats: the claim's worker is taken to be dead
+STALL_SECONDS = 900        # A4: no write by the run for this long: the child is stuck
+RUN_TIMEOUT_SECONDS = 1800  # A4: the whole run, as a backstop
+SWEEP_SECONDS = 60         # the worker looks for work this often when idle (and on start)
+LOCK_TIMEOUT_MS = 5000
+# Session advisory locks, one per run (the run id in the low 32 bits). Their high words ("HCLA", "HCWR") keep them
+# apart from the single-key locks used elsewhere (spend.MONTH_LOCK_KEY, confirmation.SOURCES_LOCK_KEY, migrate's).
+_CLAIM_NS, _WORK_NS = 0x48434C41, 0x48435752
+
+
+def _key(ns: int, run_id: int) -> int:
+    if not 0 < int(run_id) < 2 ** 32:
+        raise ValueError("a run id for an advisory lock is below 2**32")
+    return (ns << 32) | int(run_id)
+
+
+def claim_key(run_id: int) -> int:
+    return _key(_CLAIM_NS, run_id)
+
+
+def work_key(run_id: int) -> int:
+    return _key(_WORK_NS, run_id)
+
+
+class Lease:
+    """The worker's lease connection for one claim: autocommit, holding the session lock (CLAIM, run)."""
+
+    def __init__(self, engine: Engine, run_id: int):
+        self.run_id = run_id
+        self._conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
+        self._conn.execute(text("SELECT set_config('application_name', :a, false)"), dict(a=f"hc-lease-{run_id}"))
+
+    def try_take(self) -> bool:
+        """CLAIM taken, and WORK free (taken and let go at once); False, holding nothing, otherwise."""
+        if not self._conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=claim_key(self.run_id))).scalar():
+            return False
+        if not self._conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=work_key(self.run_id))).scalar():
+            self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=claim_key(self.run_id)))
+            return False
+        self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=work_key(self.run_id)))
+        return True
+
+    def close(self) -> None:
+        """Lets go of the lock (by closing the session) and the connection."""
+        try:
+            self._conn.execute(text("SELECT pg_advisory_unlock_all(), set_config('application_name', '', false)"))
+        except Exception:  # noqa: BLE001 (closing the session lets go of it anyway)
+            pass
+        self._conn.close()
+
+
+@dataclass
+class Claim:
+    id: int
+    run_id: int
+    status_before: str  # 'queued', 'waiting' or 'running' (a running run is taken up again: recovery first)
+    lease: Lease
+
+
+_CANDIDATES = text("""
+    SELECT r.id FROM run r
+    LEFT JOIN run_claim c ON c.run_id = r.id AND c.released_at IS NULL
+    WHERE (c.id IS NULL OR c.heartbeat_at < clock_timestamp() - make_interval(secs => :stale))
+      AND (r.status IN ('queued', 'running')
+           OR (r.status = 'waiting' AND EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id)))
+      AND (CAST(:only AS bigint) IS NULL OR r.id = CAST(:only AS bigint))
+    ORDER BY CASE r.status WHEN 'running' THEN 0 WHEN 'waiting' THEN 1 ELSE 2 END, r.queued_at, r.id
+    LIMIT 100""")
+
+
+def _take(engine: Engine, run_id: int, worker: str, stale_seconds: float) -> tuple[int, str] | None:
+    """The claim's transaction: (claim id, status before) or None if the run is no longer claimable."""
+
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        if status not in ("queued", "running", "waiting"):
+            return None
+        if status == "waiting" and not conn.execute(
+                text("SELECT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = :r)"), dict(r=run_id)).scalar():
+            return None
+        open_claim = conn.execute(text(
+            "SELECT id, heartbeat_at < clock_timestamp() - make_interval(secs => :s) AS stale, heartbeat_at "
+            "FROM run_claim WHERE run_id = :r AND released_at IS NULL"), dict(r=run_id, s=stale_seconds)).one_or_none()
+        if open_claim is not None:
+            if not open_claim.stale:
+                return None
+            conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = 'lost', found = :f "
+                              "WHERE id = :c").bindparams(bindparam("f", type_=JSONB)),
+                         dict(c=open_claim.id, f={"stale_heartbeat_at": open_claim.heartbeat_at.isoformat()}))
+        cid = conn.execute(text("INSERT INTO run_claim (run_id, worker) VALUES (:r, :w) RETURNING id"),
+                           dict(r=run_id, w=worker)).scalar_one()
+        if status == "queued":
+            conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=run_id))
+        elif status == "waiting":  # confirmed: it goes on (the database requires the confirmation, 0007)
+            conn.execute(text("UPDATE run SET status = 'running' WHERE id = :r"), dict(r=run_id))
+        return cid, status
+
+    return run_transaction(engine, body)
+
+
+def claim_next(engine: Engine, worker: str, *, only: int | None = None,
+               stale_seconds: float = STALE_SECONDS) -> Claim | None:
+    """The next claimable run, claimed by `worker`; None if there is none (or `only` is not claimable)."""
+    with engine.connect() as conn:
+        candidates = [r for (r,) in conn.execute(_CANDIDATES, dict(stale=stale_seconds, only=only)).all()]
+    for run_id in candidates:
+        lease = Lease(engine, run_id)
+        try:
+            if not lease.try_take():
+                lease.close()
+                continue
+            taken = _take(engine, run_id, worker, stale_seconds)
+        except Exception:
+            lease.close()
+            raise
+        if taken is None:
+            lease.close()
+            continue
+        cid, before = taken
+        LOG.info(json.dumps({"claimed": run_id, "claim": cid, "worker": worker, "status_before": before}))
+        return Claim(cid, run_id, before, lease)
+    return None
+
+
+def claim(engine: Engine, run_id: int, worker: str) -> Claim | None:
+    """A claim of exactly this run (the command line works its own run inline, R1); None if it is held or not open."""
+    return claim_next(engine, worker, only=run_id)
+
+
+def record_child(engine: Engine, c: Claim, pid: int) -> None:
+    """The guarded child's pid on the claim (once; 0008)."""
+    with engine.begin() as conn:
+        conn.execute(text("UPDATE run_claim SET child_pid = :p WHERE id = :c AND released_at IS NULL"),
+                     dict(p=pid, c=c.id))
+
+
+def release(engine: Engine, c: Claim, reason: str, found: dict | None = None) -> None:
+    """Ends the claim once, with its reason (and what recovery found), under the run's lock; then lets go of the lease.
+    If the database cannot take the release, the lease is let go anyway: the open claim's heartbeat then goes stale
+    and another worker takes the run over (`lost`)."""
+    if reason not in RELEASE_REASONS:
+        raise ValueError(reason)
+
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=c.run_id))
+        conn.execute(text("UPDATE run_claim SET released_at = now(), release_reason = :x, found = CAST(:f AS jsonb) "
+                          "WHERE id = :c AND released_at IS NULL"),
+                     dict(x=reason, f=json.dumps(found) if found is not None else None, c=c.id))
+
+    try:
+        run_transaction(engine, body)
+        LOG.info(json.dumps({"released": c.run_id, "claim": c.id, "reason": reason}))
+    finally:
+        c.lease.close()
+
+
+class Heartbeat(threading.Thread):
+    """Writes the claim's heartbeat every `interval` seconds until stopped (R6: on the claim row only)."""
+
+    def __init__(self, engine: Engine, claim_id: int, interval: float = HEARTBEAT_SECONDS):
+        super().__init__(name=f"heartbeat-{claim_id}", daemon=True)
+        self._engine, self._claim, self._interval = engine, claim_id, interval
+        self._stop_event = threading.Event()
+
+    def run(self) -> None:
+        while not self._stop_event.wait(self._interval):
+            try:
+                with self._engine.begin() as conn:
+                    conn.execute(text("UPDATE run_claim SET heartbeat_at = clock_timestamp() WHERE id = :c "
+                                      "AND released_at IS NULL"), dict(c=self._claim))
+            except Exception as error:  # noqa: BLE001 (the next beat tries again; a long gap makes the claim stale)
+                LOG.error(json.dumps({"heartbeat_failed": self._claim, "error": type(error).__name__}))
+
+    def stop(self) -> None:
+        self._stop_event.set()
+        self.join(30)
+
+
+_LAST_WRITE = text("""
+    SELECT extract(epoch FROM clock_timestamp() - greatest(
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
+def seconds_since_last_write(conn: Connection, run_id: int) -> float:
+    """A4: seconds since the run last wrote anything that shows progress (its status times, a stage or call started or
+    finished, a source searched, a record stored, the confirmation, the lock, the freeze)."""
+    return float(conn.execute(_LAST_WRITE, dict(r=run_id)).scalar_one())
diff --git a/hypocurate/pipeline/recovery.py b/hypocurate/pipeline/recovery.py
new file mode 100644
index 0000000..7fd5346
--- /dev/null
+++ b/hypocurate/pipeline/recovery.py
@@ -0,0 +1,98 @@
+"""Recovery of a run taken up again (build step 9b; docs/reviews/step09b_plan.md, "Recovery"; register
+'recovery_policy').
+
+When a worker claims a run that is already running (its worker died, it was shut down, it stopped on a recording or
+reservation failure, or its child was stuck), `recover` does the bookkeeping first, in one transaction under the
+run's lock (the locking protocol):
+1. every model call of the run still `started` is closed `interrupted`, with no usage, so it keeps counting at its
+   reserved maximum in every cap and total (code `recording_failed` when its stage ended on a recording failure,
+   else `worker_stopped`);
+2. every stage still `running` is closed `failed` with code `interrupted`;
+3. if the run has now been taken up more than `MAX_RECOVERIES` times, it fails: `attempts_exhausted`.
+It writes no plan, record, set, freeze or confirmation; forward progress goes only through the normal path (the
+orchestrator, which takes every step from stored rows) and its database guards. The worker then runs the orchestrator
+with `recovered=True`, which applies the owner's rule, split by cause (2026-10-08):
+- an interruption, a recording failure, or any database failure while saving a call (`RECOVERABLE`): the Q3 per-role
+  rule. The Planner is repeated once (`PLANNER_REPEATS`; a second loss fails the run); the Critic's remaining batches
+  are skipped; after the Analyst the run completes with "explanation unavailable";
+- a spending refusal stays a stop, exactly as in 9a.
+What was found is recorded on the claim's release.
+
+Imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
+"""
+from __future__ import annotations
+
+import json
+import logging
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.db.retry import run_transaction
+
+LOG = logging.getLogger("hypocurate.worker")
+MAX_RECOVERIES = 3   # the owner's approved value (step 9 plan; register 'recovery_policy')
+PLANNER_REPEATS = 1  # owner, Q3
+# The stops recovery takes up by the per-role rule (owner, 2026-10-08): the request was lost, or the database could not
+# save the call. A spending refusal is never among them.
+RECOVERABLE = ("interrupted", "recording_failed", "reservation_failed")
+LOCK_TIMEOUT_MS = 5000
+# How an Analyst stage closed by recovery is shown (owner, Q3); tests check it is agents.analyst.UNAVAILABLE's wording.
+ANALYST_INTERRUPTED = "explanation unavailable (interrupted)"
+EXHAUSTED = ("attempts_exhausted: the run stopped at {stage} {n} times without finishing; dispatch it again as a new "
+             "run")
+
+
+def finish_narrower_questions(engine: Engine) -> list[str]:
+    """The worker's sweep: an original completed as partly sufficient whose narrower question was not created (the
+    worker stopped between the copy and the question; no worker claims a completed run) gets it now, and a draft left
+    by such a stop is submitted. Never a second one (`queries.create_narrower`; one per run, 0007). Returns the numbers."""
+    from hypocurate.pipeline import queries
+    with engine.connect() as conn:
+        rows = conn.execute(text(
+            "SELECT r.id, (SELECT s.output FROM stage_result s WHERE s.run_id = r.id AND s.stage = 'narrowing' AND "
+            "s.status = 'done' ORDER BY s.id DESC LIMIT 1) AS decision FROM run r WHERE r.status = 'completed' AND "
+            "r.outcome = 'partly_sufficient' AND (NOT EXISTS (SELECT 1 FROM hypothesis h WHERE h.narrower_of_run_id = "
+            "r.id) OR EXISTS (SELECT 1 FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE "
+            "h.narrower_of_run_id = r.id AND hv.status = 'draft'))")).all()
+    done = []
+    for run_id, decision in rows:
+        if isinstance(decision, dict) and isinstance(decision.get("narrower_scope"), dict):
+            done.append(queries.create_narrower(engine, run_id, decision["narrower_scope"]).number)
+            LOG.info(json.dumps({"narrower_question_finished": run_id}))
+    return done
+
+
+def recover(engine: Engine, run_id: int) -> dict:
+    """Recovery's bookkeeping for a running run that a worker has just claimed; what was found."""
+
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        if status != "running":
+            return {"status": status}
+        calls = conn.execute(text(
+            "UPDATE model_call mc SET status = 'interrupted', finished_at = now(), error = CASE WHEN EXISTS ("
+            "SELECT 1 FROM stage_result s WHERE s.id = mc.stage_result_id AND s.status = 'failed' AND "
+            "s.output->>'code' = 'recording_failed') THEN 'recording_failed' ELSE 'worker_stopped' END "
+            "WHERE mc.run_id = :r AND mc.status = 'started'"), dict(r=run_id)).rowcount
+        stages = conn.execute(text(
+            "UPDATE stage_result SET status = 'failed', finished_at = now(), output = coalesce(output, '{}'::jsonb) "
+            "|| jsonb_build_object('code', 'interrupted') || CASE WHEN stage = 'analyst' THEN "
+            "jsonb_build_object('shown', CAST(:shown AS text)) ELSE '{}'::jsonb END "
+            "WHERE run_id = :r AND status = 'running'"), dict(r=run_id, shown=ANALYST_INTERRUPTED)).rowcount
+        earlier = conn.execute(text(
+            "SELECT count(*) FROM run_claim WHERE run_id = :r AND released_at IS NOT NULL "
+            "AND release_reason NOT IN ('waiting', 'finished')"), dict(r=run_id)).scalar_one()
+        found = {"calls_closed": calls, "stages_closed": stages, "recoveries": earlier + 1}
+        if earlier + 1 > MAX_RECOVERIES:
+            from hypocurate.access.stage import actual_stage
+            stage = actual_stage(conn, run_id, status)
+            reason = EXHAUSTED.format(stage=stage.replace("_", " "), n=earlier + 1)
+            conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
+                         dict(f=reason, r=run_id))
+            found["failed"] = reason
+        return found
+
+    found = run_transaction(engine, body)
+    LOG.info(json.dumps({"recovered": run_id, **found}))
+    return found
diff --git a/hypocurate/worker.py b/hypocurate/worker.py
index 532d1ef..fafa87b 100644
--- a/hypocurate/worker.py
+++ b/hypocurate/worker.py
@@ -1,32 +1,172 @@
-"""The background worker (PRD Section 6).
+"""The background worker (PRD Section 6; build step 9b; docs/reviews/step09b_plan.md).
 
-Step 2: an idle loop. It checks that the database answers, logs, and sleeps.
-The queue, heartbeat and pipeline arrive in step 9. Run with
-`python -m hypocurate.worker`.
+`python -m hypocurate.worker [--once]` (also `hypocurate worker`): claims a run (`pipeline.queue`), keeps its claim's
+heartbeat on a thread of its own, takes the run up again after recovery's bookkeeping if it was running
+(`pipeline.recovery`), runs the orchestrator in a guarded child started from the main thread (it dies with the
+worker, owner's addition A3), watches the child, and releases the claim with its reason:
+- `finished` (the run completed or failed), `waiting` (it waits for a person), `stopped_for_recovery` (it stopped
+  and stays running: recovery takes it up at the next claim);
+- `child_stuck` (A4: the run wrote nothing for `STALL_SECONDS`, or ran for `RUN_TIMEOUT_SECONDS`: the child is killed),
+  `child_failed` (the child gave no answer), `shutdown` (SIGTERM: the child is stopped).
+Idle, it looks for work every `SWEEP_SECONDS` (and at once on start). `--once` claims one run, if there is one,
+and returns. The worker never imports dspy, litellm or scipy (owner, Q2: memory); the child does.
 """
 from __future__ import annotations
 
+import argparse
+import json
 import logging
+import os
+import signal
+import socket
+import threading
 import time
+from typing import Any, Callable
 
+from sqlalchemy import Engine, text
+
+from hypocurate.access import guarded
 from hypocurate.config import load_settings
-from hypocurate.db.engine import database_reachable, make_engine
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import queue, recovery
 
 log = logging.getLogger("hypocurate.worker")
-IDLE_SECONDS = 60
+CHILD_TARGET = "hypocurate.pipeline.orchestrator:work_guarded"
+WATCH_SECONDS = 1.0  # how often the worker looks at its child
+
+
+def worker_name() -> str:
+    return f"{socket.gethostname()}:{os.getpid()}"[:200]
+
+
+def _status(engine: Engine, run_id: int) -> str:
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
+
 
+def _watch(engine: Engine, run_id: int, child: guarded.GuardedChild, started: float, stop: threading.Event,
+           stall_seconds: float, run_timeout: float) -> str:
+    """'ended', or why the child is to be stopped: 'shutdown', 'run_timeout' or 'stalled'."""
+    while True:
+        if child.wait_for(WATCH_SECONDS):
+            return "ended"
+        if stop.is_set():
+            return "shutdown"
+        if time.monotonic() - started > run_timeout:
+            return "run_timeout"
+        try:
+            with engine.connect() as conn:
+                quiet = queue.seconds_since_last_write(conn, run_id)
+        except Exception:  # noqa: BLE001 (the database is away: the run limit still applies)
+            continue
+        if quiet > stall_seconds:
+            return "stalled"
 
-def run(max_cycles: int | None = None, sleep=time.sleep) -> None:
-    settings = load_settings(web=False)
-    engine = make_engine(settings.database_url)
+
+def work(engine: Engine, claim: queue.Claim, *, phases=("run",), on_phase: Callable[[str, dict], None] | None = None,
+         stop: threading.Event | None = None, stall_seconds: float = queue.STALL_SECONDS,
+         run_timeout: float = queue.RUN_TIMEOUT_SECONDS, heartbeat_interval: float = queue.HEARTBEAT_SECONDS,
+         client_options: dict | None = None) -> dict[str, Any]:
+    """Works one claimed run (from the main thread) and releases its claim; returns the last phase's report, the
+    release reason and, for a stopped child, why."""
+    stop = stop or threading.Event()
+    beat = queue.Heartbeat(engine, claim.id, interval=heartbeat_interval)
+    beat.start()
+    started = time.monotonic()
+    found: dict | None = None
+    report: dict | None = None
+    try:
+        if claim.status_before == "running":
+            found = recovery.recover(engine, claim.run_id) or None
+        for i, phase in enumerate(phases):
+            if found and found.get("failed"):  # recovery ended the run (attempts exhausted)
+                break
+            child = guarded.start_guarded(CHILD_TARGET, {"run_id": claim.run_id, "phase": phase,
+                                                         "client_options": client_options,
+                                                         "recovered": claim.status_before == "running"},
+                                          audit=(engine, claim.run_id))
+            if i == 0:
+                queue.record_child(engine, claim, child.pid)
+            why = _watch(engine, claim.run_id, child, started, stop, stall_seconds, run_timeout)
+            if why != "ended":
+                child.stop(signal.SIGTERM if why == "shutdown" else signal.SIGKILL)
+                child.discard()
+                reason = "shutdown" if why == "shutdown" else "child_stuck"
+                queue.release(engine, claim, reason, found)
+                log.warning(json.dumps({"child_stopped": claim.run_id, "why": why}))
+                return {"report": report, "release": reason, "why": why}
+            try:
+                report = child.result(timeout=60)
+            except guarded.GuardedRunError:
+                queue.release(engine, claim, "child_failed", found)
+                return {"report": report, "release": "child_failed", "why": "no_answer"}
+            if report.get("busy"):  # another child holds the run's work lock
+                queue.release(engine, claim, "child_failed", found)
+                return {"report": report, "release": "child_failed", "why": "busy"}
+            if on_phase:
+                on_phase(phase, report)
+            if phase == "prepare" and not report.get("ready"):
+                break
+        status = _status(engine, claim.run_id)
+        reason = ("finished" if status in ("completed", "failed") else "waiting" if status == "waiting"
+                  else "stopped_for_recovery")
+        queue.release(engine, claim, reason, found)
+        return {"report": report, "release": reason, "why": None}
+    except BaseException:
+        try:
+            queue.release(engine, claim, "child_failed", found)
+        except Exception:  # noqa: BLE001 (the lease is let go anyway: the claim goes stale)
+            pass
+        raise
+    finally:
+        beat.stop()
+
+
+def run(once: bool = False, engine: Engine | None = None, max_cycles: int | None = None,
+        wait: Callable[[float], Any] | None = None) -> int:
+    """The worker loop. SIGTERM (a deploy) and SIGINT stop it after its child is stopped and its claim released.
+    Each cycle it finishes any narrower question left by a stop (`recovery.finish_narrower_questions`) and claims the
+    next run; idle, it logs whether the database answers (never its address) and looks again after `SWEEP_SECONDS`.
+    `max_cycles` and `wait` are for tests."""
+    engine = engine or make_engine(load_settings(web=False).database_url)
+    stop = threading.Event()
+    wait = wait or stop.wait
+    if threading.current_thread() is threading.main_thread():
+        for sig in (signal.SIGTERM, signal.SIGINT):
+            signal.signal(sig, lambda *_: stop.set())
+    name = worker_name()
+    log.info(json.dumps({"worker_started": name, "once": once}))
     cycles = 0
-    while max_cycles is None or cycles < max_cycles:
-        reachable = database_reachable(engine)
-        log.info("worker idle: no pipeline yet; database %s", "reachable" if reachable else "NOT reachable")
+    while not stop.is_set() and (max_cycles is None or cycles < max_cycles):
         cycles += 1
-        sleep(IDLE_SECONDS)
+        try:
+            recovery.finish_narrower_questions(engine)
+            claim = queue.claim_next(engine, name)
+        except Exception as error:  # noqa: BLE001 (the database is away: say so, try again later)
+            log.error("worker idle: database NOT reachable (%s)", type(error).__name__)
+            claim = None
+        else:
+            if claim is None:
+                log.info("worker idle: nothing to claim; database reachable")
+        if claim is None:
+            if once:
+                break
+            wait(queue.SWEEP_SECONDS)
+            continue
+        work(engine, claim, stop=stop)
+        if once:
+            break
+    log.info(json.dumps({"worker_stopped": name}))
+    return 0
+
+
+def main(argv: list[str] | None = None) -> int:
+    parser = argparse.ArgumentParser(prog="hypocurate worker")
+    parser.add_argument("--once", action="store_true", help="claim one run, if there is one, work it and stop")
+    args = parser.parse_args(argv)
+    return run(once=args.once)
 
 
 if __name__ == "__main__":
     logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
-    run()
+    raise SystemExit(main())
```
## 3. New test files

### `tests/test_cli_step9b.py`

```python
"""Step 9b, b4: the command line through the claim (owner's approval of R1, R2; docs/reviews/step09b_plan.md).

`run`, `dispatch` and `confirm` work their run inline through the same claim and worker code as the background
worker (a claim row, its heartbeat, the guarded child), printing what they printed before; `--queue` returns at once
and leaves the run to a worker; `queue` lists the open runs; `hypocurate worker [--once]` is the worker (PRD 12)."""
from __future__ import annotations

import json

from sqlalchemy import text

from hypocurate.pipeline import confirmation, queue
from test_cli_runs import hc
from test_orchestrator import FCC_CLAIM, planner_body, responder
from test_worker import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_run_works_its_run_through_a_claim(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    assert code == 0, err
    rid = json.loads(out.split("\n", 1)[0])["run"]
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT child_pid IS NOT NULL, release_reason FROM run_claim WHERE run_id = :r"),
                            dict(r=rid)).all()
    assert [tuple(r) for r in rows] == [(True, "finished")]


def test_run_with_queue_returns_at_once_and_a_worker_finishes_the_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                        "--queue")
    assert code == 0, err
    lines = out.strip().split("\n")
    first = json.loads(lines[0])
    assert first["status"] == "dispatched" and len(lines) == 1
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=first["run"]) == "queued"
    code, out, err = hc(capsys, "worker", "--once")
    assert code == 0, err
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=first["run"]) == "completed"


def test_queue_lists_the_open_runs_with_what_they_wait_for(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")  # stops at the wait
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                   "--queue")
    queued = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "queue")
    assert code == 0, err
    rows = {r["run"]: r for r in json.loads(out)}
    assert rows[queued]["status"] == "queued" and rows[queued]["worker"] is None
    waiting = next(r for r in rows.values() if r["status"] == "waiting")
    assert waiting["waiting_for"] == confirmation.WAITING_FOR
    assert waiting["recoveries"] == 0 and waiting["seconds_since_last_write"] >= 0


def test_queue_shows_a_claims_worker_and_heartbeat(engine, stub, capsys):
    stub.respond(responder())
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer",
                   "--queue")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    c = queue.claim(engine, rid, "host:7")
    try:
        rows = {r["run"]: r for r in json.loads(hc(capsys, "queue")[1])}
        assert rows[rid]["worker"] == "host:7" and rows[rid]["heartbeat_age_seconds"] >= 0
        assert rows[rid]["status"] == "running"
    finally:
        queue.release(engine, c, "stopped_for_recovery")


def test_confirm_with_queue_records_the_confirmation_and_leaves_the_run_to_a_worker(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer", "--queue")
    assert code == 0, err
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"  # confirmed, for a worker
    hc(capsys, "worker", "--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"


def test_confirm_works_the_rest_through_a_claim(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    _, out, _ = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    with engine.connect() as conn:
        reasons = [r for (r,) in conn.execute(text("SELECT release_reason FROM run_claim WHERE run_id = :r ORDER BY id"),
                                               dict(r=rid)).all()]
    assert reasons == ["waiting", "finished"]
```
### `tests/test_guarded_parent.py`

```python
"""Step 9b, addition A3 (owner, 2026-10-08; docs/reviews/step09b_plan.md): the guarded child dies with its parent.

The worker's main thread starts the child (`guarded.start_guarded`); the child sets PR_SET_PDEATHSIG(SIGKILL) first
thing, then checks that its parent is still the process that started it. Tests run a small parent process (a script
written for the test) so it can be killed without killing the test."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time

import pytest

from hypocurate.access import guarded

PARENT = """
import json, sys, threading
from hypocurate.access import guarded
seconds = float(sys.argv[1])
child = guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": seconds}])
print(json.dumps({"child": child.pid}), flush=True)
if len(sys.argv) > 2 and sys.argv[2] == "thread_exits":
    t = threading.Thread(target=lambda: None)   # a thread of the parent (like the heartbeat) that ends
    t.start(); t.join()
print(json.dumps({"result": child.result(timeout=60)}), flush=True)
"""


def gone(pid: int) -> bool:
    """The process no longer runs (it does not exist, or only its zombie is left)."""
    try:
        with open(f"/proc/{pid}/status") as f:
            return any(line.startswith("State:") and "Z" in line.split()[1] for line in f)
    except FileNotFoundError:
        return True


def start_parent(tmp_path, *args):
    script = tmp_path / "parent.py"
    script.write_text(PARENT)
    proc = subprocess.Popen([sys.executable, str(script), *args], stdout=subprocess.PIPE, text=True,
                            env=dict(os.environ))
    child = json.loads(proc.stdout.readline())["child"]
    return proc, child


def test_the_child_dies_within_two_seconds_when_its_parent_is_killed(tmp_path):
    parent, child = start_parent(tmp_path, "60")
    time.sleep(0.5)
    assert not gone(child)
    parent.send_signal(signal.SIGKILL)
    parent.wait(5)
    deadline = time.time() + 2
    while not gone(child) and time.time() < deadline:
        time.sleep(0.05)
    assert gone(child), "the child outlived its parent"


def test_the_child_outlives_a_thread_of_its_parent_that_exits(tmp_path):
    """PR_SET_PDEATHSIG follows the thread that started the child: a heartbeat-like thread ending must not kill it."""
    parent, child = start_parent(tmp_path, "2", "thread_exits")
    out = json.loads(parent.stdout.readline())
    parent.wait(10)
    assert out == {"result": ["ok"]}


def test_a_child_is_started_only_from_the_main_thread():
    errors = []

    def start():
        try:
            guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": 0}])
        except RuntimeError as error:
            errors.append(str(error))

    t = threading.Thread(target=start)
    t.start()
    t.join(10)
    assert errors and "main thread" in errors[0]


def test_a_child_whose_parent_is_already_gone_exits_at_once():
    """The fork race: the parent died before the child set its death signal; the child sees another parent."""
    request = {"target": "hypocurate.access.guard_probe:probe", "payload": [{"op": "sleep", "seconds": 30}],
               "scratch": "/tmp", "parent_pid": 2 ** 30}  # above Linux's largest pid: never the real parent (in a
    # container the test process itself may be pid 1)
    started = time.time()
    done = subprocess.run([sys.executable, "-m", guarded.MODULE], input=json.dumps(request), capture_output=True,
                          text=True, timeout=20)
    assert time.time() - started < 10
    assert done.returncode == guarded.PARENT_GONE_EXIT and '"ok": true' not in done.stdout


def test_start_guarded_gives_the_same_answer_as_run_guarded():
    child = guarded.start_guarded("hypocurate.access.guard_probe:probe", [{"op": "sleep", "seconds": 0}])
    assert child.result(timeout=60) == guarded.run_guarded("hypocurate.access.guard_probe:probe",
                                                           [{"op": "sleep", "seconds": 0}], timeout=60) == ["ok"]


def test_a_child_that_fails_raises_guarded_run_error():
    child = guarded.start_guarded("hypocurate.access.guard_probe:no_such_function", [])
    with pytest.raises(guarded.GuardedRunError):
        child.result(timeout=60)
```
### `tests/test_kill_matrix.py`

```python
"""Step 9b, b5: the worker killed at each stage, then the run taken up again (docs/reviews/step09b_plan.md, "Tests").

Each case: an uninterrupted run of the query first (the reference), then the query dispatched again; a real worker
process works the second run and is killed (SIGKILL) at the chosen point: a test-only trigger sleeps at a write, or the
local stub kills the worker while it serves the chosen request. The child dies with the worker (A3). The run is then
claimed again once its claim is stale (a shortened, test-only staleness) and worked in this process. Checks:
- no stage stays running and no call stays started; every lost call ends `interrupted` and counts at its maximum;
- no request is repeated except the one allowed Planner repeat;
- the plan and freeze fingerprints and every analysis result equal the uninterrupted run's."""
from __future__ import annotations

import os
import signal
import time

import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate import worker
from hypocurate.pipeline import confirmation, queries, queue
from test_guarded_parent import gone
from test_worker import engine, stub, wait_until, worker as start_worker  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def results(engine, rid):
    with engine.connect() as conn:
        return (conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=rid)).scalar(),
                conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar(),
                tuple(conn.execute(text("SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r"),
                                   dict(r=rid)).one()),
                [tuple(r) for r in conn.execute(text(
                    "SELECT scope, n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM "
                    "analysis_result WHERE run_id = :r ORDER BY scope, n_records, estimate"), dict(r=rid)).all()])


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def number_of(engine, rid):
    return one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                       "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)


def complete(engine, rid):
    """Works the run to its end with the worker's code in this process (confirming a wait by a named person)."""
    for _ in range(4):
        status = one(engine, "SELECT status FROM run WHERE id = :r", r=rid)
        if status in ("completed", "failed"):
            return
        if status == "waiting" and not one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid):
            confirmation.confirm(engine, rid, by="Ada Reviewer")
        c = queue.claim_next(engine, "test:recover", only=rid, stale_seconds=1)
        if c is None:
            time.sleep(1.2)
            continue
        worker.work(engine, c, heartbeat_interval=0.5)


STALL_KEY = 0x48435453 << 32  # "HCTS": the test's own lock, apart from the code's


def stall(engine, table, when="true"):
    """A test-only trigger: each matching write waits for a lock the test holds, so the run makes no progress. Returns
    the holder. (A lock, not a sleep: a killed child's batched statements are already queued in its session, which
    goes on executing them; once the test lets go of the lock they drain at once and, with no COMMIT ever coming,
    roll back.)"""
    holder = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    holder.execute(text("SELECT pg_advisory_lock(:k)"), dict(k=STALL_KEY))
    with engine.begin() as conn:
        conn.execute(text(f"CREATE FUNCTION hc_test_stall() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          f"PERFORM pg_advisory_xact_lock({STALL_KEY}); RETURN NEW; END $$"))
        conn.execute(text(f"CREATE TRIGGER zz_hc_test_stall BEFORE INSERT ON {table} FOR EACH ROW WHEN ({when}) "
                          f"EXECUTE FUNCTION hc_test_stall()"))
    return holder


def unstall(engine, table, holder):
    holder.execute(text("SELECT pg_advisory_unlock_all()"))
    holder.close()
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL lock_timeout = '60s'"))
        conn.execute(text(f"DROP TRIGGER IF EXISTS zz_hc_test_stall ON {table}"))
        conn.execute(text("DROP FUNCTION IF EXISTS hc_test_stall()"))


def sleeping(engine):
    """A run's write is held at the test's lock."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' AND wait_event = "
                                 "'advisory' AND datname = current_database()")).scalar() > 0


def kill_worker_and_child(engine, proc, rid):
    child = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid)
    proc.send_signal(signal.SIGKILL)
    proc.wait(10)
    if child:
        assert wait_until(lambda: gone(child), 2), "the child outlived the worker"


def assert_bookkeeping(engine, rid):
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r AND status = 'started'", r=rid) == 0
    lost = one(engine, "SELECT coalesce(sum(max_cost), 0) FROM model_call WHERE run_id = :r AND status = 'interrupted'",
               r=rid)
    assert one(engine, "SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid) >= lost


def reference_and_second(engine, stub, body=None, claim=to.FCC_CLAIM, fixed=True):
    """The uninterrupted run (worked to its end) and a second run of the same query, queued."""
    stub.respond(to.responder(body))
    first = to.dispatched(engine, claim=claim, fixed_plan=fixed)
    complete(engine, first)
    return first, queries.dispatch_again(engine, number_of(engine, first))


@pytest.mark.parametrize("point, table, when", [
    ("after the lock", "record", "true"),
    ("between sources", "record", "NEW.source_version_id = {second}"),
    ("before Checks", "stage_result", "NEW.stage = 'checks'"),
    ("before Inclusion", "stage_result", "NEW.stage = 'inclusion'"),
    ("before the freeze", "run_snapshot", "true"),
    ("mid-statistics", "analysis_result", "true"),
])
def test_a_worker_killed_at_a_code_stage_is_taken_up_with_the_same_results(engine, stub, point, table, when):
    first, rid = reference_and_second(engine, stub)
    analyst_before = requests(stub, "report")
    if "{second}" in when:  # the version of the source stored second, in the order the code stores them
        from hypocurate.pipeline import extract
        second = extract.pending_sources(engine, rid)[1]
        when = when.format(second=one(engine, "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = "
                                              "rs.source_id WHERE rs.run_id = :r AND s.key = :k", r=rid, k=second))
    holder = stall(engine, table, when)
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120), point
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, table, holder)
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert results(engine, rid) == results(engine, first)
    assert requests(stub, "report") == analyst_before + 1  # one Analyst request for the second run


def kill_on(stub, field, body=None):
    """The stub kills the worker the first time it serves a request asking for `field`."""
    state = {"pid": None, "done": False}
    answer = to.responder(body)

    def respond(raw):
        if f"[[ ## {field} ## ]]" in raw and not state["done"] and state["pid"]:
            state["done"] = True
            os.kill(state["pid"], signal.SIGKILL)
            time.sleep(0.5)
        return answer(raw)

    stub.respond(respond)
    return state


def test_a_worker_killed_mid_planner_repeats_the_planner_once(engine, stub):
    first, rid = reference_and_second(engine, stub, body=to.planner_body(), fixed=False)
    plans_before = requests(stub, "plan")
    state = kill_on(stub, "plan", to.planner_body())
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(120)
    assert state["done"]
    assert wait_until(lambda: one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1, 10)
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert requests(stub, "plan") == plans_before + 2  # the lost request and its one repeat
    assert one(engine, "SELECT error FROM model_call WHERE run_id = :r AND status = 'interrupted'", r=rid) == \
        "worker_stopped"
    assert results(engine, rid)[1:] == results(engine, first)[1:]  # (the plan fingerprints: same plan content)
    assert results(engine, rid)[0] == results(engine, first)[0]


def test_a_worker_killed_before_the_narrowing_takes_it_up_without_asking_the_planner_again(engine, stub):
    first, rid = reference_and_second(engine, stub, body=to.planner_body(), fixed=False)
    plans_before = requests(stub, "plan")
    holder = stall(engine, "stage_result", "NEW.stage = 'narrowing'")
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, "stage_result", holder)
    complete(engine, rid)
    assert requests(stub, "plan") == plans_before + 1
    assert results(engine, rid) == results(engine, first)


def test_a_worker_killed_mid_analyst_completes_with_the_explanation_unavailable(engine, stub):
    from hypocurate import cli_runs
    first, rid = reference_and_second(engine, stub)
    reports_before = requests(stub, "report")
    state = kill_on(stub, "report")
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(300)
    assert state["done"]
    complete(engine, rid)
    assert_bookkeeping(engine, rid)
    assert requests(stub, "report") == reports_before + 1  # not repeated
    assert cli_runs.show(engine, rid)["analyst_text"] == {"unavailable": "explanation unavailable (interrupted)"}
    assert results(engine, rid) == results(engine, first)


def test_a_worker_killed_during_the_critics_request_is_taken_up_without_another_critic_request(migrated_database,
                                                                                                stub, monkeypatch):
    """Flags naming two records (small constructed data, a marked test run): the worker is killed during the Critic's
    first request; the run is taken up without another Critic request and completes. (The batch size is an agent
    setting recorded at dispatch; with these flags there is one batch, so "batch 1 of 2" is not exercised here.)"""
    import pipeline_world as pw
    import stub_provider as sp
    from hypocurate.db.engine import make_engine
    from stats_world import small_rows
    from test_critic import CONFLICT, PAIR_MPEA, PAIR_OTHER, PAIR_SAME, SOURCES
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    eng = make_engine(migrated_database)
    with eng.begin() as conn:
        db = conn.execute(text("SELECT current_database()")).scalar()
        conn.execute(text(f'ALTER DATABASE "{db}" SET client_connection_check_interval = \'100ms\''))
    pw.registered_files(eng, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT + [PAIR_SAME, PAIR_MPEA]),
                              "controlled_duplicates": pw.mpea_csv([PAIR_SAME, PAIR_OTHER])})
    q = queries.create(eng, to.FCC_CLAIM, SOURCES)
    queries.submit(eng, q.version_id)
    queries.confirm_domain(eng, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(eng, q.version_id, fixed_plan=True, constructed_test_data=True)
    state = kill_on(stub, "classification")
    proc = start_worker("--once", wait=False)
    state["pid"] = proc.pid
    proc.wait(300)
    assert state["done"]
    critic_requests = requests(stub, "classification")
    complete(eng, rid)
    assert one(eng, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "classification") == critic_requests  # not repeated
    assert_bookkeeping(eng, rid)
    eng.dispose()


def test_a_worker_killed_between_the_partly_copy_and_the_narrower_question_leaves_exactly_one(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    holder = stall(engine, "hypothesis", "NEW.narrower_of_run_id IS NOT NULL")
    try:
        proc = start_worker("--once", wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        kill_worker_and_child(engine, proc, rid)
    finally:
        unstall(engine, "hypothesis", holder)
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) == "partly_sufficient"
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
    start_worker("--once")  # the worker's sweep finishes it
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
    start_worker("--once")
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1


def test_a_run_waiting_at_the_lock_when_the_worker_restarts_is_left_alone_until_confirmed(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    calls = one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid)
    start_worker("--once")  # a restart: nothing claimed, nothing sent
    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == calls
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"


def test_14_4_a_run_stopped_by_its_cap_fails_with_the_reason_and_is_dispatched_again(engine, stub):
    """Criterion 14.4, bullet 4 (at the Planner; R5): the cap stops the run before a request is sent, it is marked
    failed with the reason, and it can be dispatched again as a new run."""
    stub.respond(to.responder(to.planner_body()))
    q = queries.create(engine, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    from decimal import Decimal
    rid = queries.dispatch(engine, q.version_id, ceiling=Decimal("0.0001"))
    start_worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "plan") == 0
    again = queries.dispatch_again(engine, q.number)
    assert again != rid and one(engine, "SELECT status FROM run WHERE id = :r", r=again) == "queued"


def test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run(engine, stub):
    """Criterion 14.4, bullet 2: the worker is stopped (SIGTERM, as a deploy) during a run, then restarted: the run
    resumes from its last completed stage and finishes; it is never left running."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    holder = stall(engine, "run_snapshot")
    try:
        proc = start_worker(wait=False)
        assert wait_until(lambda: sleeping(engine), 120)
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=120)
    finally:
        unstall(engine, "run_snapshot", holder)
    assert one(engine, "SELECT release_reason FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid) == \
        "shutdown"
    start_worker("--once")  # restarted: a shutdown claim is claimable at once
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert_bookkeeping(engine, rid)
```
### `tests/test_migrations_step9b.py`

```python
"""Step 9b: migration 0008, `run_claim` (the step 9 plan approved by the owner on 2026-10-08; docs/reviews/step09b_plan.md).

A claim is a worker's hold on one run: who (worker), the guarded child's pid, when it was claimed, its heartbeat (R6:
written on the claim row, never the run row), and how it was released, once. One open claim per run. Claims are
history: never deleted. 0001 to 0007 untouched; up, down, up gives the same schema; the downgrade refuses while a
claim exists; a failed upgrade changes nothing."""
from __future__ import annotations

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")


def m0008():
    return SCRIPTS.get_revision("0008").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


def claim(w, rid, worker="host:1"):
    return w.val("INSERT INTO run_claim (run_id, worker) VALUES (:r, :w) RETURNING id", r=rid, w=worker)


def release(w, cid, reason="finished"):
    w.run_sql("UPDATE run_claim SET released_at = now(), release_reason = :x WHERE id = :c", x=reason, c=cid)


# --- the migration ------------------------------------------------------------------------------------------

def test_0008_is_the_head_and_follows_0007():
    assert migrate.head_revision() == "0008" and m0008().down_revision == "0007"


def test_0008_replaces_no_earlier_function():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006", "0007")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m0008().FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m0008().FUNCTIONS)


def test_up_down_up_restores_0007(engine):
    migrate.upgrade(engine, "0007")
    at_0007 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0007")
    assert snapshot(engine) == at_0007
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0007")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_claim_insert() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before and migrate.current_revision(engine) == "0007"


def test_the_downgrade_refuses_while_a_claim_exists(db):
    w = World(db)
    claim(w, w.run())
    before = snapshot(db)
    with pytest.raises(Exception, match="0008 is in use"):
        migrate.downgrade(db, "0007")
    assert snapshot(db) == before and migrate.current_revision(db) == "0008"


def test_the_release_reasons_are_the_codes():
    from hypocurate.pipeline import queue
    assert m0008().RELEASE_REASONS == REASONS == queue.RELEASE_REASONS


# --- a claim ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["queued", "running", "waiting"])
def test_an_open_run_is_claimed_with_the_databases_times(w, status):
    rid = w.run()
    if status != "queued":
        w.start(rid)
    if status == "waiting":  # a Planner run at its wait (0007)
        sid = w.stage(rid, "planner", "planner")
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=sid)
        w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
        w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)
    cid = w.val("INSERT INTO run_claim (run_id, worker, claimed_at, heartbeat_at) VALUES (:r, 'host:1', "
                "'2000-01-01', '2000-01-01') RETURNING id", r=rid)
    assert w.val("SELECT claimed_at > '2001-01-01' AND heartbeat_at = claimed_at FROM run_claim WHERE id = :c", c=cid)


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_an_ended_run_is_never_claimed(w, status):
    rid = w.running()
    if status == "failed":
        w.fail(rid)
    else:
        w.complete(rid, "insufficient", level=1)
    w.rejected("INSERT INTO run_claim (run_id, worker) VALUES (:r, 'host:1')", "only an open run is claimed", r=rid)


def test_one_open_claim_per_run(w):
    rid = w.run()
    cid = claim(w, rid)
    with pytest.raises(IntegrityError, match="uq_run_claim_open"):
        claim(w, rid, "host:2")
    release(w, cid, "lost")
    claim(w, rid, "host:2")
    assert w.val("SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 2


@pytest.mark.parametrize("worker", ["", "  ", "x" * 201])
def test_a_claim_names_its_worker(w, worker):
    with pytest.raises(IntegrityError, match="ck_run_claim_worker_named"):
        claim(w, w.run(), worker)


def test_the_heartbeat_is_the_databases_time_and_needs_no_run_lock(w):
    """R6: the heartbeat is written on the claim row; a run lock held elsewhere does not hold it back."""
    rid = w.run()
    cid = claim(w, rid)
    with w.e.connect() as holder:
        tx = holder.begin()
        holder.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        with w.e.connect() as beat:
            beat.execute(text("SET lock_timeout = '2s'"))
            beat.execute(text("UPDATE run_claim SET heartbeat_at = '2000-01-01' WHERE id = :c"), dict(c=cid))
            beat.commit()
        tx.rollback()
    assert w.val("SELECT heartbeat_at > '2001-01-01' FROM run_claim WHERE id = :c", c=cid)


def test_the_childs_pid_is_set_once(w):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET child_pid = 4242 WHERE id = :c", c=cid)
    w.rejected("UPDATE run_claim SET child_pid = 4343 WHERE id = :c", "a claim's child is recorded once", c=cid)


@pytest.mark.parametrize("column, value", [("run_id", "999"), ("worker", "'host:9'"), ("claimed_at", "now() - interval '1 h'")])
def test_what_a_claim_records_never_changes(w, column, value):
    rid = w.run()
    cid = claim(w, rid)
    w.rejected(f"UPDATE run_claim SET {column} = {value} WHERE id = :c", "what a claim records cannot change", c=cid)


@pytest.mark.parametrize("reason", REASONS)
def test_a_claim_is_released_once_with_a_reason_at_the_databases_time(w, reason):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET released_at = '2000-01-01', release_reason = :x WHERE id = :c", x=reason, c=cid)
    assert w.val("SELECT released_at > '2001-01-01' FROM run_claim WHERE id = :c", c=cid)
    w.rejected("UPDATE run_claim SET heartbeat_at = now() WHERE id = :c", "a released claim is final", c=cid)
    w.rejected("UPDATE run_claim SET release_reason = 'lost' WHERE id = :c", "a released claim is final", c=cid)


def test_a_release_needs_a_known_reason(w):
    cid = claim(w, w.run())
    with pytest.raises(IntegrityError, match="ck_run_claim_release"):
        release(w, cid, "because")
    w.rejected("UPDATE run_claim SET release_reason = 'finished' WHERE id = :c", "ck_run_claim_released_with_reason",
               c=cid)


def test_what_recovery_found_is_recorded_with_the_release(w):
    cid = claim(w, w.run())
    w.run_sql("UPDATE run_claim SET found = '{\"calls_closed\": 1}', released_at = now(), release_reason = "
              "'stopped_for_recovery' WHERE id = :c", c=cid)
    assert w.val("SELECT found->>'calls_closed' FROM run_claim WHERE id = :c", c=cid) == "1"


def test_claims_are_never_deleted(w):
    cid = claim(w, w.run())
    w.rejected("DELETE FROM run_claim WHERE id = :c", "never deleted", c=cid)
    w.rejected("TRUNCATE run_claim", "never deleted")
```
### `tests/test_queue.py`

```python
"""Step 9b, b2: claims and the heartbeat (docs/reviews/step09b_plan.md, "Claims, heartbeat, and dead").

A worker claims a run by taking, without waiting, a session advisory lock (CLAIM, run) on its own lease connection and
checking that (WORK, run) is free; then, in one locked transaction, it re-checks the run, closes a stale claim as
`lost`, records its claim and starts the run (queued -> running, or a confirmed waiting run -> running). Two workers
can never both hold a run."""
from __future__ import annotations

import threading
import time

import pytest
from sqlalchemy import text

from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queue
from model_builder import World


@pytest.fixture
def w(db):
    return World(db)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def waiting_run(w, confirmed=False):
    rid = w.running()
    sid = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=sid)
    narrowed = w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
    w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)
    if confirmed:  # confirmed by a named person, still waiting to be taken up
        from model_builder import FP
        w.run_sql("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                  "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, '{}', 'shown')",
                  r=rid, fp=FP, p=sid, n=narrowed)
    return rid


def test_a_queued_run_is_claimed_and_started(w):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    try:
        assert (c.run_id, c.status_before) == (rid, "queued")
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
        assert one(w.e, "SELECT worker FROM run_claim WHERE id = :c AND released_at IS NULL", c=c.id) == "host:1"
    finally:
        c.lease.close()


def test_two_workers_never_hold_one_run(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    try:
        assert first.run_id == rid
        assert queue.claim_next(w.e, "host:2") is None  # the run is held; nothing else to claim
    finally:
        first.lease.close()


def test_claims_at_the_same_moment_give_the_run_to_one_worker(w):
    rid = w.run()
    got, barrier = [], threading.Barrier(4)

    def claim(name):
        barrier.wait()
        c = queue.claim_next(w.e, name)
        got.append(c)

    threads = [threading.Thread(target=claim, args=(f"host:{i}",)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    held = [c for c in got if c is not None]
    try:
        assert len(held) == 1 and held[0].run_id == rid
        assert one(w.e, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    finally:
        for c in held:
            c.lease.close()


def test_a_run_whose_work_lock_is_held_by_an_orphan_child_is_not_claimed(w):
    rid = w.run()
    with w.e.connect() as orphan:
        assert orphan.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
        assert queue.claim_next(w.e, "host:1") is None
        orphan.execute(text("SELECT pg_advisory_unlock(:k)"), dict(k=queue.work_key(rid)))
        orphan.commit()
    c = queue.claim_next(w.e, "host:1")
    assert c is not None and c.run_id == rid
    c.lease.close()


def test_a_waiting_run_is_claimed_only_once_confirmed(w):
    rid = waiting_run(w)
    assert queue.claim_next(w.e, "host:1") is None
    other = waiting_run(w, confirmed=True)
    c = queue.claim_next(w.e, "host:1")
    try:
        assert (c.run_id, c.status_before) == (other, "waiting")
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=other) == "running"
        assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    finally:
        c.lease.close()


def test_a_running_run_with_a_live_claim_is_left_alone_and_a_stale_one_is_taken_over(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    first.lease.close()  # the worker's lease connection is gone (its process died), the claim row stays open
    assert queue.claim_next(w.e, "host:2") is None  # its heartbeat is fresh: not dead yet
    time.sleep(1.2)
    c = queue.claim_next(w.e, "host:2", stale_seconds=1)
    try:
        assert (c.run_id, c.status_before) == (rid, "running")
        assert one(w.e, "SELECT release_reason FROM run_claim WHERE id = :c", c=first.id) == "lost"
    finally:
        c.lease.close()


def test_a_claim_released_for_recovery_is_claimable_at_once(w):
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    queue.release(w.e, first, "stopped_for_recovery")
    c = queue.claim_next(w.e, "host:2")
    try:
        assert c.run_id == rid and c.status_before == "running"
    finally:
        c.lease.close()


@pytest.mark.parametrize("reason", ["finished", "waiting"])
def test_a_released_claim_frees_both_locks(w, reason):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    queue.release(w.e, c, reason)
    with w.e.connect() as conn:
        assert conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.claim_key(rid))).scalar()
        conn.execute(text("SELECT pg_advisory_unlock_all()"))
    assert one(w.e, "SELECT release_reason FROM run_claim WHERE id = :c", c=c.id) == reason


def test_the_heartbeat_thread_beats_and_stops(w):
    rid = w.run()
    c = queue.claim_next(w.e, "host:1")
    first = one(w.e, "SELECT heartbeat_at FROM run_claim WHERE id = :c", c=c.id)
    beat = queue.Heartbeat(w.e, c.id, interval=0.2)
    beat.start()
    time.sleep(1.0)
    beat.stop()
    later = one(w.e, "SELECT heartbeat_at FROM run_claim WHERE id = :c", c=c.id)
    assert later > first and not beat.is_alive()
    c.lease.close()


def test_the_time_since_the_last_write_counts_stage_and_call_rows(w):
    rid = w.running(agents=True)
    sid = w.stage(rid, "planner", "planner")
    time.sleep(1.1)
    with w.e.connect() as conn:
        quiet = queue.seconds_since_last_write(conn, rid)
    w.call(rid, sid)
    with w.e.connect() as conn:
        assert quiet >= 1 and queue.seconds_since_last_write(conn, rid) < quiet


def test_the_keys_never_meet_other_locks():
    from hypocurate.pipeline.agents.spend import MONTH_LOCK_KEY
    from hypocurate.pipeline.confirmation import SOURCES_LOCK_KEY
    keys = {queue.claim_key(1), queue.work_key(1), queue.claim_key(2 ** 31), queue.work_key(2 ** 31)}
    assert len(keys) == 4 and not keys & {MONTH_LOCK_KEY, SOURCES_LOCK_KEY}
    with pytest.raises(ValueError):
        queue.claim_key(2 ** 32)


# --- added after the mutation checks (q02, q03): each guard reached on its own ---------------------------------

def test_the_claim_transaction_itself_refuses_a_run_with_a_live_claim(w):
    """Mutation q02: the candidate query leaves out a run with a live claim, so the claim transaction's own re-check
    (the race between the query and the transaction) is reached directly here."""
    rid = w.run()
    first = queue.claim_next(w.e, "host:1")
    try:
        assert queue._take(w.e, rid, "host:2", queue.STALE_SECONDS) is None
        assert one(w.e, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 1
    finally:
        first.lease.close()


def test_the_claim_transaction_itself_refuses_an_unconfirmed_waiting_run(w):
    rid = waiting_run(w)
    assert queue._take(w.e, rid, "host:1", queue.STALE_SECONDS) is None
    assert one(w.e, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_an_unconfirmed_waiting_run_is_not_even_a_candidate(w):
    """Mutation q03: the candidate query's own rule (the claim transaction would refuse it too)."""
    rid = waiting_run(w)
    confirmed = waiting_run(w, confirmed=True)
    with w.e.connect() as conn:
        listed = [r for (r,) in conn.execute(queue._CANDIDATES, dict(stale=queue.STALE_SECONDS, only=None)).all()]
    assert confirmed in listed and rid not in listed
```
### `tests/test_recovery.py`

```python
"""Step 9b, b3: recovery when a run is taken up again (docs/reviews/step09b_plan.md, "Recovery"; the owner's answer of
2026-10-08, split by cause).

Recovery's bookkeeping closes every open call as `interrupted` (counted at its reserved maximum) and every running stage
as failed (`interrupted`); a run recovered more than `MAX_RECOVERIES` times fails. Then the run goes on by the normal
path, and:
- an interruption, a recording failure or any database failure while saving a call (`recording_failed`,
  `reservation_failed`): the Q3 per-role rule. The Planner is repeated once (a second loss fails the run); the Critic's
  remaining batches are skipped; after the Analyst the run completes with "explanation unavailable";
- a spending refusal (a cap was reached) stays a stop, exactly as in 9a: the Planner and the Critic fail the run, the
  Analyst completes it; no further request, never a later paid stage.
Each case is set up as the request path leaves it, the worker then claims the run and works it (in this process; the
child is a real guarded process; every call goes to the local stub)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

import test_orchestrator as to
from hypocurate import worker
from hypocurate.pipeline import confirmation, queue, queries, recovery
from test_resume_step9a import agent_stage, fixed_run_after_checks, fixed_run_after_statistics, kw
from test_worker import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def requests(stub, field):
    return sum(f"[[ ## {field} ## ]]" in r["raw"].decode() for r in stub.requests)


def open_call(engine, rid, stage_id):
    """A model call left started (the request was sent, or its recording failed)."""
    with engine.begin() as conn:
        inv = conn.execute(text("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
                                "SELECT 'run', :r, :s, s.role, ras.agent_setting_id FROM stage_result s JOIN "
                                "run_agent_setting ras ON ras.run_id = s.run_id AND ras.role = s.role WHERE s.id = :s "
                                "RETURNING id"), dict(r=rid, s=stage_id)).scalar()
        return conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                                 "price_table_version, max_cost) SELECT :r, :s, :i, role, 'claude-opus-5-5', 'p', 0.4 "
                                 "FROM stage_result WHERE id = :s RETURNING id"), dict(r=rid, s=stage_id, i=inv)).scalar()


def lost_stage(engine, rid, stage, how):
    """An agent stage left as the request path leaves it: 'interrupted' (running, its call open), 'recording_failed'
    (its call open, then the stage failed with the code), 'reservation_failed' (failed, no call)."""
    sid = agent_stage(engine, rid, stage, "running")
    if how in ("interrupted", "recording_failed"):
        open_call(engine, rid, sid)
    if how != "interrupted":
        with engine.begin() as conn:
            conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), "
                              "output = CAST(:o AS jsonb) WHERE id = :s"), dict(o=f'{{"code": "{how}"}}', s=sid))
    return sid


def take_up(engine, rid):
    """The worker claims the run (it is running, with no open claim) and works it."""
    c = queue.claim(engine, rid, "test:recovery")
    assert c is not None and c.status_before == "running"
    return worker.work(engine, c, heartbeat_interval=0.5)


def planner_left(engine, stub, how):
    """A Planner run whose Planner stage is left as `how`: 'interrupted' (running, its call open), 'recording_failed'
    (failed, its call open), 'reservation_failed' (failed, no call) or 'spending_cap_run' (failed, no call)."""
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    sid = agent_stage(engine, rid, "planner", "running")
    if how in ("interrupted", "recording_failed"):
        open_call(engine, rid, sid)
    if how != "interrupted":
        with engine.begin() as conn:
            conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), "
                              "output = CAST(:o AS jsonb) WHERE id = :s"), dict(o=f'{{"code": "{how}"}}', s=sid))
    return rid


def assert_closed_and_counted(engine, rid):
    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r AND status = 'started'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0
    lost = one(engine, "SELECT coalesce(sum(max_cost), 0) FROM model_call WHERE run_id = :r AND status = 'interrupted'",
               r=rid)
    counted = one(engine, "SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)
    assert counted >= lost  # every lost call counts at its reserved maximum


# --- the Planner -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_planner_request_is_repeated_once(engine, stub, how):
    rid = planner_left(engine, stub, how)
    out = take_up(engine, rid)
    assert out["release"] == "waiting" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert requests(stub, "plan") == 1  # the one repeat
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 2
    assert_closed_and_counted(engine, rid)
    if how != "reservation_failed":
        assert one(engine, "SELECT error FROM model_call WHERE run_id = :r AND status = 'interrupted'", r=rid) == (
            "worker_stopped" if how == "interrupted" else "recording_failed")


def test_a_second_lost_planner_request_fails_the_run_with_the_reason(engine, stub):
    rid = planner_left(engine, stub, "interrupted")
    with engine.begin() as conn:  # a first repeat that was lost too
        conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now(), output = "
                          "'{\"code\": \"interrupted\"}' WHERE run_id = :r AND status = 'running'"), dict(r=rid))
        conn.execute(text("UPDATE model_call SET status = 'interrupted', finished_at = now(), error = 'worker_stopped' "
                          "WHERE run_id = :r"), dict(r=rid))
    agent_stage(engine, rid, "planner", "running")
    take_up(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == (
        "interrupted: the worker stopped during the Planner's request twice; dispatch the query again as a new run")
    assert requests(stub, "plan") == 0


def test_a_planner_spending_refusal_stays_a_stop_after_recovery(engine, stub):
    rid = planner_left(engine, stub, "spending_cap_run")
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert len(stub.requests) == 0


# --- the Critic -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_critic_request_skips_the_remaining_batches_and_the_run_goes_on(engine, stub, how):
    rid = fixed_run_after_checks(engine, stub)
    lost_stage(engine, rid, "critic", how)
    before = requests(stub, "classification")
    out = take_up(engine, rid)
    assert out["release"] == "finished" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "classification") == before  # not repeated
    assert requests(stub, "report") == 1  # the Analyst goes on
    assert_closed_and_counted(engine, rid)


def test_a_critic_spending_refusal_stays_a_stop_and_the_analyst_is_never_asked(engine, stub):
    rid = fixed_run_after_checks(engine, stub)
    agent_stage(engine, rid, "critic", "failed", "spending_cap_run")
    take_up(engine, rid)
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")
    assert requests(stub, "report") == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 0


# --- the Analyst ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("how", ["interrupted", "recording_failed", "reservation_failed"])
def test_a_lost_analyst_request_completes_the_run_with_the_explanation_unavailable(engine, stub, how):
    from hypocurate import cli_runs
    rid = fixed_run_after_statistics(engine, stub)
    lost_stage(engine, rid, "analyst", how)
    before = requests(stub, "report")
    take_up(engine, rid)
    assert (one(engine, "SELECT status FROM run WHERE id = :r", r=rid), one(engine, "SELECT outcome FROM run WHERE "
                                                                                   "id = :r", r=rid)) == (
        "completed", "sufficient")
    assert requests(stub, "report") == before
    assert cli_runs.show(engine, rid)["analyst_text"]["unavailable"].startswith("explanation unavailable")
    assert_closed_and_counted(engine, rid)


def test_an_analyst_spending_refusal_completes_the_run_as_in_9a(engine, stub):
    rid = fixed_run_after_statistics(engine, stub)
    agent_stage(engine, rid, "analyst", "failed", "spending_cap_run")
    before = requests(stub, "report")
    take_up(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert requests(stub, "report") == before


def test_a_lost_analyst_request_on_the_partly_sufficient_path_completes_and_creates_the_narrower_question(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, **kw(stub)).answer)
    lost_stage(engine, rid, "analyst", "recording_failed")
    take_up(engine, rid)
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) == "partly_sufficient"
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1


# --- recovery's own rules -------------------------------------------------------------------------------------

def test_a_run_recovered_more_than_max_recoveries_times_fails(engine, stub):
    rid = fixed_run_after_checks(engine, stub)
    for i in range(recovery.MAX_RECOVERIES):
        c = queue.claim(engine, rid, f"test:{i}")
        queue.release(engine, c, "stopped_for_recovery")
    out = take_up(engine, rid)
    assert out["release"] == "finished"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith(
        f"attempts_exhausted: the run stopped at curation {recovery.MAX_RECOVERIES + 1} times without finishing")
    assert len([r for r in stub.requests if "[[ ## report ## ]]" in r["raw"].decode()]) == 0


def test_recovery_writes_no_plan_record_set_freeze_or_confirmation(engine, stub):
    """Recovery is bookkeeping only (a source scan of the module: it never writes those tables)."""
    import pathlib
    source = pathlib.Path(recovery.__file__).read_text(encoding="utf-8")
    for table in ("plan", "record", "analysis_set", "run_snapshot", "rules_confirmation", "run_record"):
        assert f"INSERT INTO {table} " not in source and f"INSERT INTO {table}(" not in source


def test_what_recovery_found_is_recorded_on_the_claim(engine, stub):
    rid = planner_left(engine, stub, "interrupted")
    take_up(engine, rid)
    found = one(engine, "SELECT found FROM run_claim WHERE run_id = :r ORDER BY id DESC LIMIT 1", r=rid)
    assert found["calls_closed"] == 1 and found["stages_closed"] == 1 and found["recoveries"] == 1


def test_a_repeat_that_would_pass_the_run_cap_is_refused_before_it_is_sent(engine, stub):
    """Caps across crashes: the lost call counts at its maximum, so a repeat past the cap is never sent."""
    rid = planner_left(engine, stub, "interrupted")
    sid = one(engine, "SELECT id FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid)
    open_call_cost = Decimal("1.99")
    with engine.begin() as conn:  # a second lost call of the same stage, near the cap
        inv = conn.execute(text("SELECT invocation_id FROM model_call WHERE run_id = :r"), dict(r=rid)).scalar()
        conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                          "price_table_version, max_cost) VALUES (:r, :s, :i, 'planner', 'claude-opus-5-5', 'p', :m)"),
                     dict(r=rid, s=sid, i=inv, m=open_call_cost))
    take_up(engine, rid)
    assert requests(stub, "plan") == 0
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid).startswith("spending_refused: ")


def test_the_interrupted_explanation_uses_the_analysts_own_wording():
    from hypocurate.pipeline.agents.analyst import UNAVAILABLE
    assert recovery.ANALYST_INTERRUPTED == f"{UNAVAILABLE} (interrupted)"


def test_the_sweep_finishes_a_narrower_question_left_by_a_stop_and_never_makes_a_second(engine, stub):
    from hypocurate.pipeline import completion, narrowing
    from hypocurate.pipeline.agents import analyst, planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, **kw(stub)).answer)
    analyst.run_analyst(engine, rid, **kw(stub))
    completion.copy_partly_sufficient(engine, rid)  # the stop: completed, no narrower question
    assert len(recovery.finish_narrower_questions(engine)) == 1
    assert recovery.finish_narrower_questions(engine) == []
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
```
### `tests/test_worker.py`

```python
"""Step 9b, b2: the worker (docs/reviews/step09b_plan.md). `python -m hypocurate.worker [--once]` claims a run, keeps
its claim's heartbeat, runs the orchestrator in a guarded child that holds the run's work lock, watches the child
(A4: stuck after a time with no write, or after the whole-run limit; SIGTERM: shut down), and releases the claim with
its reason. Every model call goes to the local stub (no live call)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, queue
from test_guarded_parent import gone


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database, monkeypatch, stub):
    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
        monkeypatch.setenv(k, v)
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    pw.registered(e, ("mpea", "tamu_fcc"))
    with e.begin() as conn:  # a backend notices quickly that its client is gone (a killed child's sleeping query)
        conn.execute(text("SELECT set_config('client_connection_check_interval', '100ms', false)"))
        db = conn.execute(text("SELECT current_database()")).scalar()
        conn.execute(text(f'ALTER DATABASE "{db}" SET client_connection_check_interval = \'100ms\''))
    yield e
    e.dispose()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def worker(*args, wait=True):
    proc = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=dict(os.environ))
    if wait:
        out, err = proc.communicate(timeout=600)
        assert proc.returncode == 0, err[-3000:]
    return proc


def claims(engine, rid):
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(text("SELECT worker, child_pid IS NOT NULL, release_reason FROM run_claim "
                                                    "WHERE run_id = :r ORDER BY id"), dict(r=rid)).all()]


def stall_at(engine, table):
    """A test-only trigger: the run's next write to `table` sleeps, so the child makes no progress."""
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_test_stall() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
                          "PERFORM pg_sleep(120); RETURN NEW; END $$"))
        conn.execute(text(f"CREATE TRIGGER zz_hc_test_stall BEFORE INSERT ON {table} FOR EACH ROW "
                          f"EXECUTE FUNCTION hc_test_stall()"))


def unstall(engine, table):
    with engine.begin() as conn:
        conn.execute(text(f"DROP TRIGGER zz_hc_test_stall ON {table}"))
        conn.execute(text("DROP FUNCTION hc_test_stall()"))


def sleeping(engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'PgSleep' AND "
                                 "datname = current_database()")).scalar() > 0


def wait_until(predicate, seconds=60):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return False


def test_the_worker_parent_loads_no_model_or_statistics_library():
    """Owner, Q2 (memory on 512 MB; the plan: "the parent never imports dspy, litellm or scipy"). numpy is not on the
    list: the parent imports the access package (for the guarded runner), whose source adapters import openpyxl,
    which imports numpy. Keeping it out would mean loading openpyxl after the child's file guard is installed, which
    the guard refuses (it reads /etc/mime.types). The memory measurement (b5) includes it."""
    code = ("import sys, hypocurate.worker, hypocurate.pipeline.queue, hypocurate.pipeline.recovery; "
            "print([m for m in ('dspy', 'litellm', 'scipy', 'statsmodels') if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert out.stdout.strip() == "[]", out.stderr


def test_worker_once_with_nothing_to_do_returns(engine):
    started = time.time()
    worker("--once")
    assert time.time() - started < 60


def test_worker_once_completes_a_fixed_plan_run(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    (name, child_recorded, reason), = claims(engine, rid)
    assert name.endswith(tuple("0123456789")) and child_recorded and reason == "finished"


def test_a_planner_run_waits_then_a_worker_finishes_it_once_confirmed(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert claims(engine, rid)[-1][2] == "waiting"
    worker("--once")  # not confirmed: nothing to claim
    assert len(claims(engine, rid)) == 1
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    worker("--once")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert [c[2] for c in claims(engine, rid)] == ["waiting", "finished"]


def test_two_workers_and_one_run_give_one_claim_and_no_repeated_request(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    a, b = worker("--once", wait=False), worker("--once", wait=False)
    for p in (a, b):
        p.communicate(timeout=600)
        assert p.returncode == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
    assert len(claims(engine, rid)) == 1
    analyst = [r for r in stub.requests if "[[ ## report ## ]]" in r["raw"].decode()]
    assert len(analyst) == 1


def test_sigterm_shuts_the_worker_down_releasing_its_claim_and_stopping_its_child(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        p = worker(wait=False)
        assert wait_until(lambda: sleeping(engine))
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r", r=rid)
        p.send_signal(signal.SIGTERM)
        p.communicate(timeout=120)
        assert p.returncode == 0
        assert claims(engine, rid)[-1][2] == "shutdown"
        assert wait_until(lambda: gone(pid), 5)
        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"  # taken up again later
    finally:
        unstall(engine, "run_snapshot")


def test_killing_the_worker_kills_its_child_and_frees_the_runs_locks(engine, stub):
    """A3, with the real worker: SIGKILL of the worker kills the child within 2 s, and the work lock is released."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        p = worker(wait=False)
        assert wait_until(lambda: sleeping(engine))
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE run_id = :r", r=rid)
        p.send_signal(signal.SIGKILL)
        p.wait(10)
        assert wait_until(lambda: gone(pid), 2), "the child outlived the worker"

        def locks_free():
            with engine.connect() as conn:
                free = all(conn.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=k)).scalar()
                           for k in (queue.claim_key(rid), queue.work_key(rid)))
                conn.execute(text("SELECT pg_advisory_unlock_all()"))
                return free
        assert wait_until(locks_free, 10)
        assert claims(engine, rid)[-1][2] is None  # the claim stays open; its heartbeat goes stale
    finally:
        unstall(engine, "run_snapshot")


def test_a_stuck_child_is_stopped_and_its_claim_released_for_recovery(engine, stub):
    """A4, at a shortened test-only limit: no write for the limit -> the child is killed, the claim `child_stuck`."""
    from hypocurate import worker as w
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:stuck")
        out = w.work(engine, c, stall_seconds=3, heartbeat_interval=0.5)
        assert out["release"] == "child_stuck"
        assert claims(engine, rid)[-1][2] == "child_stuck"
        pid = one(engine, "SELECT child_pid FROM run_claim WHERE id = :c", c=c.id)
        assert wait_until(lambda: gone(pid), 5)
    finally:
        unstall(engine, "run_snapshot")


def test_the_whole_run_limit_stops_a_child_that_keeps_writing_too_long(engine, stub):
    from hypocurate import worker as w
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    stall_at(engine, "run_snapshot")
    try:
        c = queue.claim(engine, rid, "test:timeout")
        out = w.work(engine, c, run_timeout=2, stall_seconds=10 ** 6, heartbeat_interval=0.5)
        assert out["release"] == "child_stuck" and out["why"] == "run_timeout"
    finally:
        unstall(engine, "run_snapshot")


def test_the_web_service_never_claims_or_runs_a_pipeline():
    """Step 10 shows the queue; until then the web code imports neither the queue, the worker nor the orchestrator."""
    import ast
    import pathlib
    web = pathlib.Path(__file__).resolve().parents[1] / "hypocurate" / "web"
    for path in web.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else []
            module = getattr(node, "module", None) or ""
            assert not any(x in (module, *names) for x in ("queue", "worker", "orchestrator", "recovery",
                                                           "hypocurate.pipeline.queue", "hypocurate.worker",
                                                           "hypocurate.pipeline.orchestrator")), path


def test_a_child_whose_run_is_held_by_another_child_is_busy_and_writes_nothing(engine, stub):
    """The work lock: a second child of the same run (an orphan still at work) returns `busy` at once."""
    from hypocurate.pipeline import orchestrator, queries
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    queries.start(engine, rid)
    with engine.connect() as holder:
        assert holder.execute(text("SELECT pg_try_advisory_lock(:k)"), dict(k=queue.work_key(rid))).scalar()
        assert orchestrator.work_guarded({"run_id": rid}) == {"busy": True}
        holder.execute(text("SELECT pg_advisory_unlock_all()"))
        holder.commit()
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
```
## 4. Changed tests and test helpers (diff)

```diff
diff --git a/tests/test_cli_step9a.py b/tests/test_cli_step9a.py
index a1ef7cf..9de0563 100644
--- a/tests/test_cli_step9a.py
+++ b/tests/test_cli_step9a.py
@@ -130,4 +130,6 @@ def test_confirm_takes_no_ceiling(engine, capsys):
     with pytest.raises(SystemExit) as stopped:
         cli.main(["confirm", "1", "--by", "Ada Reviewer", "--ceiling", "0.10"])
     assert stopped.value.code == 2
-    assert list(inspect.signature(cli_runs._confirm).parameters) == ["engine", "run_id", "by"]
+    # Step 9b: `to_queue` added (R2, `confirm --queue`); still no ceiling.
+    params = list(inspect.signature(cli_runs._confirm).parameters)
+    assert params == ["engine", "run_id", "by", "to_queue"] and "ceiling" not in params
diff --git a/tests/test_health.py b/tests/test_health.py
index dc0c905..2f7bd6c 100644
--- a/tests/test_health.py
+++ b/tests/test_health.py
@@ -57,19 +57,24 @@ def test_health_shows_no_secrets(database_url):
         assert database_url not in text and "postgresql" not in text
 
 
-def test_worker_idles_and_checks_the_database(database_url, monkeypatch, caplog):
-    monkeypatch.setenv("DATABASE_URL", database_url)
+def test_the_idle_worker_looks_for_work_every_sweep_and_checks_the_database(migrated_database, monkeypatch, caplog):
+    """Step 9b: was test_worker_idles_and_checks_the_database (the step 2 idle loop, replaced by the worker); the same
+    checks on the new loop: idle, it looks again every 60 s (queue.SWEEP_SECONDS) and logs that the database answers.
+    (A scratch database: the worker now reads the queue's tables.)"""
+    from hypocurate.pipeline import queue
+    monkeypatch.setenv("DATABASE_URL", migrated_database)
     sleeps = []
     with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
-        worker.run(max_cycles=2, sleep=sleeps.append)
-    assert sleeps == [worker.IDLE_SECONDS] * 2
-    assert caplog.text.count("no pipeline yet; database reachable") == 2
+        worker.run(max_cycles=2, wait=sleeps.append)
+    assert sleeps == [queue.SWEEP_SECONDS] * 2 == [60, 60]
+    assert caplog.text.count("nothing to claim; database reachable") == 2
 
 
 def test_worker_logs_an_unreachable_database(monkeypatch, caplog):
+    """Step 9b: the same checks on the new loop (was `sleep=`, now `wait=`)."""
     monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
     with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
-        worker.run(max_cycles=1, sleep=lambda s: None)
+        worker.run(max_cycles=1, wait=lambda s: None)
     assert "database NOT reachable" in caplog.text
     assert "planted-pw-7319" not in caplog.text  # the URL's password is never logged
 
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 2cb02fd..740c08e 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -67,6 +67,9 @@ def expected_triggers() -> set[tuple[str, str]]:
     m7 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0007").module  # step 9a
     names |= {(t, f"hc_{t}_append_only") for t in m7.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m7.APPEND_ONLY}
     names |= {(t, trigger) for t, _, trigger, _ in m7.CHECKED}
+    m8 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0008").module  # step 9b
+    names |= {(t, f"hc_{t}_no_delete") for t in m8.NO_DELETE} | {(t, f"hc_{t}_no_truncate") for t in m8.NO_DELETE}
+    names |= {(t, trigger) for t, _, trigger, _ in m8.CHECKED}
     return names
 
 
diff --git a/tests/test_migrations_step9a.py b/tests/test_migrations_step9a.py
index b7c4406..1d8e958 100644
--- a/tests/test_migrations_step9a.py
+++ b/tests/test_migrations_step9a.py
@@ -82,8 +82,9 @@ def confirmed(w, rid, planner=None, narrowed=None, fp=FP):
 
 # --- the migration ------------------------------------------------------------------------------------------
 
-def test_0007_is_the_head_and_follows_0006():
-    assert migrate.head_revision() == "0007" and m0007().down_revision == "0006"
+def test_0007_follows_0006():
+    # Step 9b: 0008 is now the head (tests/test_migrations_step9b.py).
+    assert m0007().down_revision == "0006"
 
 
 def test_the_only_earlier_function_replaced_is_hc_run_update_and_only_its_status_changes_differ():
@@ -149,7 +150,8 @@ def test_the_downgrade_refuses_while_0007_is_in_use(db, use):
     before = snapshot(db)
     with pytest.raises(Exception, match="0007 is in use"):
         migrate.downgrade(db, "0006")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0007"
+    # Step 9b: the database stays at the head, now 0008 (0008's own downgrade is undone with the refused transaction).
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
 
 
 # --- waiting (owner, Q1, Q5) --------------------------------------------------------------------------------
@@ -613,7 +615,7 @@ def test_the_downgrade_is_not_blocked_by_ceilings_equal_to_the_run_cap(db):
     w.run()
     migrate.downgrade(db, "0006")
     assert migrate.current_revision(db) == "0006"
-    migrate.upgrade(db)
+    migrate.upgrade(db)  # (step 9b: through 0008, which holds no claim here)
 
 
 def test_an_explicit_null_ceiling_on_a_new_run_stores_the_run_cap(w):
diff --git a/tests/test_skeleton.py b/tests/test_skeleton.py
index 86e95fb..4156e33 100644
--- a/tests/test_skeleton.py
+++ b/tests/test_skeleton.py
@@ -321,7 +321,8 @@ def test_render_describes_web_worker_and_database():
 
 def test_render_plans_are_the_approved_ones():
     r = render()
-    assert {s["type"]: s["plan"] for s in r["services"]} == {"web": "0.5c-512mb", "worker": "0.5c-512mb"}
+    # Step 9b (owner's decision, 2026-10-08, after the 0.5-CPU memory measurement): the worker on 1c-2g.
+    assert {s["type"]: s["plan"] for s in r["services"]} == {"web": "0.5c-512mb", "worker": "1c-2g"}
     assert r["databases"][0]["plan"] == "0.1c-256mb"
     # 1 GB disk (owner decision, 2026-10-04); Render's default would be 15 GB, which cannot be reduced.
     assert r["databases"][0]["diskSizeGB"] == 1
```
## 5. Assumptions register (147 entries; 4 new, 3 changed)

### New: `queue_and_claims`

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
### New: `stuck_child_limits`

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
### New: `recovery_policy`

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
### New: `guarded_child_dies_with_parent`

```json
{
 "key": "guarded_child_dies_with_parent",
 "name": "The guarded child dies with its worker",
 "state": "in_force",
 "statement": "The worker's main thread starts the guarded child (guarded.start_guarded refuses any other thread) and passes its pid; the child sets PR_SET_PDEATHSIG(SIGKILL) first thing, then exits at once if its parent is not that process any more (the parent died before the signal was set). The child holds the run's work lock on its own connection, so even an orphan keeps every worker off the run until it ends. run_guarded (the command line before step 9b) is unchanged.",
 "value": {
  "text": "SIGKILL with the parent",
  "unit": null
 },
 "category": "operational",
 "affects": "Every guarded child the worker starts.",
 "reason": "Owner's addition A3 (step 9 plan).",
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
    "ref": "python:hypocurate.access.guarded:PR_SET_PDEATHSIG",
    "equals": 1
   },
   {
    "ref": "python:hypocurate.access.guarded:PARENT_GONE_EXIT",
    "equals": 3
   },
   {
    "ref": "python:hypocurate.access.guarded:start_guarded"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_guarded_parent.py::test_the_child_dies_within_two_seconds_when_its_parent_is_killed",
  "tests/test_guarded_parent.py::test_the_child_outlives_a_thread_of_its_parent_that_exits",
  "tests/test_guarded_parent.py::test_a_child_is_started_only_from_the_main_thread",
  "tests/test_guarded_parent.py::test_a_child_whose_parent_is_already_gone_exits_at_once",
  "tests/test_worker.py::test_killing_the_worker_kills_its_child_and_frees_the_runs_locks"
 ],
 "history": [],
 "notes": []
}
```
### Changed: `worker_poll_interval` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "worker_poll_interval",
 "name": "Worker idle interval",
 "state": "in_force",
 "statement": "When the worker has nothing to claim, it looks for work again after 60 seconds (and at once on start), and logs whether the database answers (never its address).",
 "value": {
  "text": "60",
  "unit": "seconds"
 },
 "category": "operational",
 "affects": "Worker logs only; it runs nothing yet.",
 "reason": "The queue comes in step 9.",
 "evidence": [
  "Step 2 summary."
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
    "ref": "python:hypocurate.pipeline.queue:SWEEP_SECONDS",
    "equals": 60
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "The idle worker checks the database and sleeps 60 seconds between checks.",
   "from": "2026-10-04",
   "to": "2026-10-08",
   "note": "Step 9b (owner's go, 2026-10-08): the step 2 idle loop is replaced by the worker; the interval keeps its value."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_health.py::test_the_idle_worker_looks_for_work_every_sweep_and_checks_the_database",
  "tests/test_health.py::test_worker_logs_an_unreachable_database"
 ]
}
```
### Changed: `run_order_and_failures` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "run_order_and_failures",
 "name": "The run order and what a failure does to a run",
 "state": "in_force",
 "statement": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or, after a named person's confirmation of the question as tested (the run waits for it; step 9a), the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan), which also waits for the confirmation. A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until recovery takes it up (register 'recovery_policy', step 9b). Taken up again, the run reads each agent's latest stored stage whatever its status, so such a stop, a stage left running or a stored spending refusal has the same effect as when it happened (register 'resumable_run'). No model call runs inside a database transaction.",
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
  },
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or, after a named person's confirmation of the question as tested (the run waits for it; step 9a), the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan), which also waits for the confirmation. A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9b's recovery. Taken up again, the run reads each agent's latest stored stage whatever its status, so such a stop, a stage left running or a stored spending refusal has the same effect as when it happened (register 'resumable_run'). No model call runs inside a database transaction.",
   "from": "2026-10-08",
   "to": "2026-10-08",
   "note": "Step 9b: recovery is built."
  }
 ]
}
```
### Changed: `resumable_run` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "resumable_run",
 "name": "A run is taken up again from what is stored",
 "state": "in_force",
 "statement": "The orchestrator decides every step from stored rows, never from memory, and reads each agent's latest stored stage whatever its status before deciding what comes next. An earlier stop stays a stop: a Planner, Critic or Analyst stage that ended with a recording or reservation failure, or is still running, stops the run again (no further request, nothing more written; the run stays running for step 9b's recovery); a stored spending refusal at the Planner or the Critic fails the run, and a Planner stage that failed for any other reason fails it as the Planner's failure, so the Planner is never asked again in 9a; an Analyst stage that failed for any other reason, a spending refusal included, leaves code's decision standing (A3, B2). A done Planner stage is used, not repeated; a run already confirmed, or past its lock, goes on to the lock or past it without waiting again; a stored narrowing decision is used; after the lock, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the statistics and the completion run only if their stored result is absent; an agent stage that exists (the Critic's, the Analyst's) is never started again; a completed partly-sufficient original without its narrower question gets it, and never a second one (a database index allows one per run; a draft left by a stop is submitted). A run on its first pass takes exactly the steps it took before. Recovery after a crash (closing open stages and calls, the Planner's one repeat) is register 'recovery_policy' (step 9b); without a recovery a stage left running stops the run.",
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
 "history": [
  {
   "value": "The orchestrator decides every step from stored rows, never from memory, and reads each agent's latest stored stage whatever its status before deciding what comes next. An earlier stop stays a stop: a Planner, Critic or Analyst stage that ended with a recording or reservation failure, or is still running, stops the run again (no further request, nothing more written; the run stays running for step 9b's recovery); a stored spending refusal at the Planner or the Critic fails the run, and a Planner stage that failed for any other reason fails it as the Planner's failure, so the Planner is never asked again in 9a; an Analyst stage that failed for any other reason, a spending refusal included, leaves code's decision standing (A3, B2). A done Planner stage is used, not repeated; a run already confirmed, or past its lock, goes on to the lock or past it without waiting again; a stored narrowing decision is used; after the lock, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the statistics and the completion run only if their stored result is absent; an agent stage that exists (the Critic's, the Analyst's) is never started again; a completed partly-sufficient original without its narrower question gets it, and never a second one (a database index allows one per run; a draft left by a stop is submitted). A run on its first pass takes exactly the steps it took before. Recovery after a crash (closing open stages and calls, the Planner's one repeat after an interruption) is step 9b; until then a stage left running stops the run.",
   "from": "2026-10-08",
   "to": "2026-10-08",
   "note": "Step 9b: recovery is built."
  }
 ],
 "notes": []
}
```
## 6. Reference comparison with `main`

Dumped on `main`'s code (`c7458d0`) before any change, twice (byte-identical), and on this head. Byte comparison of every file:

```
head a2adaaf
IDENTICAL fixed_plan.json
IDENTICAL narrower.json
IDENTICAL partly_original.json
IDENTICAL planner_bcc.json
IDENTICAL planner_fcc.json
IDENTICAL reference.json
```

Leaf-by-leaf differences of the orchestrator dumps:

```
== fixed_plan: 0 differing leaves
== planner_fcc: 0 differing leaves
== planner_bcc: 0 differing leaves
== partly_original: 0 differing leaves
== narrower: 0 differing leaves
```

The SHA-256 sums of `main`'s dumps:

```
e4738ce533043d8f7d2c30ecc822459876bd0331bc11a05606b4688e5ac240ae  main/fixed_plan.json
c5cb1b6ba43a040d154988188940277954d716d540aa9e63bcc4b55351e690fa  main/narrower.json
bc3b965fb53e7df7f8734b96466d7181ff64ce57f2e1c8261c45f96481db9db7  main/partly_original.json
9a07b215038d2af5b86d3f36f2c203964be0d81f361c2b973d113a2af9c01fdf  main/planner_bcc.json
92e281fa074ea97d2b9380612548fdf020c01cd3bfb5244d72705b854fe72d89  main/planner_fcc.json
4797b3c17da38ae50d9954f38406c5639992ca1097e389faae363d6f5257345f  main/reference.json
```

The comparison script:

```python
"""Leaf-by-leaf comparison of main/<case>.json with branch/<case>.json (step 9a, a0 dumps)."""
import json, sys
def walk(x, y, p, out):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            walk(x.get(k, "<absent>"), y.get(k, "<absent>"), f"{p}.{k}", out)
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (u, v) in enumerate(zip(x, y)):
            walk(u, v, f"{p}[{i}]", out)
    elif x != y:
        out.append((p, x, y))
for case in sys.argv[1:]:
    a, b = json.load(open(f"main/{case}.json")), json.load(open(f"branch/{case}.json"))
    out = []
    walk(a, b, "", out)
    print(f"== {case}: {len(out)} differing leaves")
    for p, x, y in out:
        print(f"  {p}: {json.dumps(x, ensure_ascii=False)[:160]} -> {json.dumps(y, ensure_ascii=False)[:160]}")
```

The dump tests:

```python
"""Scratch (not committed): whole runs through the orchestrator, every call to the local stub, dumped without
row ids and times to $ORCHDUMP_DIR/<case>.json, for the byte comparison of step 9a with main (milestone a0).

On the branch a run on the Planner's path (or a narrower question's) stops at 'waiting'; `advance` then confirms it
by a named person and runs the rest (on main that branch is never reached)."""
import json
import os

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate import cli_runs
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries

DROP = {"id", "run_id", "stage_result_id", "invocation_id", "agent_setting_id", "analysis_set_id",
        "analysis_result_id", "hypothesis_version_id", "hypothesis_id", "narrower_of_run_id", "extraction_run_id"}
TABLES = ["run", "plan", "run_tag", "run_snapshot", "run_source", "run_record", "analysis_set", "analysis_result",
          "calibration_result", "flag", "stage_result", "model_call", "agent_invocation"]
UNORDERED = ("run_source", "run_record", "run_tag")


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in sorted(x.items()) if k not in DROP and not k.endswith("_at")}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


def advance(engine, rid, stub):
    """Runs the run to its end the way the code of this checkout does."""
    report = orchestrator.run(engine, rid, client_options=sp.client_options(stub))
    if report.status == "waiting":  # step 9a only
        from hypocurate.pipeline import confirmation
        confirmation.confirm(engine, rid, by="Ada Reviewer")
        report = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
    return report


def dump(engine, rid, name):
    out = {}
    with engine.connect() as conn:
        for t in TABLES:
            col = "id" if t == "run" else "run_id"
            has_id = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = :t "
                                       "AND column_name = 'id')"), dict(t=t)).scalar_one()
            order = "ORDER BY id" if has_id and t not in UNORDERED else ""
            rows = clean([r[0] for r in conn.execute(text(
                f"SELECT row_to_json(x) FROM (SELECT * FROM {t} WHERE {col} = :r {order}) x"), dict(r=rid)).all()])
            if t in UNORDERED or not has_id:
                rows.sort(key=lambda r: json.dumps(r, sort_keys=True))
            out[t] = rows
        out["records"] = clean([r[0] for r in conn.execute(text(
            "SELECT row_to_json(x) FROM (SELECT * FROM record WHERE extraction_run_id = :r ORDER BY id) x"),
            dict(r=rid)).all()])
        out["narrower_question"] = clean([r[0] for r in conn.execute(text(
            "SELECT row_to_json(x) FROM (SELECT h.number, hv.text, hv.status, hv.sufficiency_option FROM hypothesis h "
            "JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE h.narrower_of_run_id = :r) x"),
            dict(r=rid)).all()])
    shown = cli_runs.show(engine, rid)
    shown.pop("run", None)
    # Step 9b: the confirmation time in a confirmed run's label is normalised, so two dumps of one code are equal.
    import re
    out["show"] = json.loads(re.sub(r"on \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", "on <time> UTC",
                                    json.dumps(shown, default=str, ensure_ascii=False)))
    with open(os.path.join(os.environ["ORCHDUMP_DIR"], f"{name}.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str, ensure_ascii=False)


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def test_fixed_plan(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert advance(engine, rid, stub).status == "completed"
    dump(engine, rid, "fixed_plan")


def test_planner_fcc(engine, stub):
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    assert advance(engine, rid, stub).status == "completed"
    dump(engine, rid, "planner_fcc")


def test_planner_bcc_insufficient(engine, stub):
    stub.respond(to.responder(to.BCC))
    rid = to.dispatched(engine, claim=to.BCC_CLAIM)
    assert advance(engine, rid, stub).status == "completed"
    dump(engine, rid, "planner_bcc")


def test_partly_and_narrower(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    assert advance(engine, rid, stub).outcome == "partly_sufficient"
    dump(engine, rid, "partly_original")
    number = cli_runs.show(engine, rid)["narrower_question"]
    vid = queries.submitted_version(engine, number)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    nid = queries.dispatch(engine, vid)
    assert advance(engine, nid, stub).status == "completed"
    dump(engine, nid, "narrower")
```
```python
"""Scratch (not committed): dumps the reference runs' full statistics output to REFDUMP_OUT."""
import json, os
from test_reference_numbers import runs  # noqa: F401 (the module fixture)


def test_dump(runs):
    out = {}
    for key, r in runs.items():
        records = [{"identity": [rec["stable_identity"] if "stable_identity" in rec else None], **{k: rec[k] for k in sorted(rec) if k not in ("id",)}}
                   for rec in r["data"]["records"]]
        out[key] = {"run": [str(x) for x in r["run"]], "decision": r["out"]["decision"],
                    "analyses": r["out"]["analyses"], "not_analysed": r["out"].get("not_analysed"),
                    "n_records": len(records)}
    with open(os.environ["REFDUMP_OUT"], "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
```
## 7. Mutation checks (each fault against its named tests; a control run with no mutation last)

```
First run, all 26 faults on the tests as they stood (q02 and q03 survived: each hidden by the other guard):
d01      CAUGHT  1 failed, 29 passed in 8.35s
d02      CAUGHT  2 failed, 28 passed in 11.45s
d03      CAUGHT  7 failed, 23 passed in 10.16s
d04      CAUGHT  1 failed, 29 passed in 8.67s
q01      CAUGHT  1 failed, 11 passed in 8.80s
q02      SURVIVED  12 passed in 8.30s
q03      SURVIVED  12 passed in 8.82s
q04      CAUGHT  1 failed, 11 passed in 8.76s
g01      CAUGHT  1 failed, 5 passed in 7.40s
g02      CAUGHT  2 failed, 4 passed in 9.16s
g03      CAUGHT  2 failed, 4 passed in 9.33s
w01      CAUGHT  1 failed, 10 passed in 203.19s (0:03:23)
w02      CAUGHT  1 failed, 10 passed in 203.66s (0:03:23)
w03      CAUGHT  1 failed, 10 passed in 74.39s (0:01:14)
w04      CAUGHT  1 failed, 10 passed in 74.43s (0:01:14)
w05      CAUGHT  10 failed, 10 passed in 77.10s (0:01:17)
w06      CAUGHT  1 failed, 10 passed in 83.10s (0:01:23)
r01      CAUGHT  9 failed, 11 passed in 124.42s (0:02:04)
r02      CAUGHT  6 failed, 14 passed in 97.12s (0:01:37)
r03      CAUGHT  1 failed, 19 passed in 132.46s (0:02:12)
r04      CAUGHT  1 failed, 19 passed in 127.19s (0:02:07)
s01      CAUGHT  1 failed in 10.54s
o01      CAUGHT  1 failed, 19 passed in 128.91s (0:02:08)
o02      CAUGHT  3 failed, 17 passed in 125.07s (0:02:05)
o03      CAUGHT  2 failed, 18 passed in 106.40s (0:01:46)
o04      CAUGHT  5 failed, 15 passed in 95.05s (0:01:35)
control  clean  82 passed in 215.59s (0:03:35)

Three tests were added to test_queue.py (each guard reached on its own) and q05 (the claim transaction's own confirmation check) was added. test_queue.py was the only test file changed; the q mutations were re-run:
q01      CAUGHT  1 failed, 14 passed in 9.94s
q02      CAUGHT  1 failed, 14 passed in 9.44s
q03      CAUGHT  1 failed, 14 passed in 9.49s
q04      CAUGHT  1 failed, 14 passed in 9.56s
q05      CAUGHT  1 failed, 14 passed in 9.45s
control  clean  82 passed in 216.48s (0:03:36)

After the pid fix in test_guarded_parent.py (2**30 instead of 1; the test image runs pytest as pid 1), the death-signal mutations were re-run:
g01      CAUGHT  1 failed, 5 passed in 9.50s
g02      CAUGHT  2 failed, 4 passed in 11.25s
g03      CAUGHT  2 failed, 4 passed in 11.65s
```

The specification and the runner:

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
 ("w01", "worker.py", "        if quiet > stall_seconds:", "        if False:", W),
 ("w02", "worker.py", "        if time.monotonic() - started > run_timeout:", "        if False:", W),
 ("w03", "worker.py", "                reason = \"shutdown\" if why == \"shutdown\" else \"child_stuck\"",
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
 ("r03", "pipeline/recovery.py", "        if earlier + 1 > MAX_RECOVERIES:", "        if False:", REC),
 ("r04", "pipeline/recovery.py", "THEN 'recording_failed' ELSE 'worker_stopped' END",
  "THEN 'worker_stopped' ELSE 'worker_stopped' END", REC),
 ("s01", "worker.py", "            recovery.finish_narrower_questions(engine)\n", "", PARTLY),
 # the orchestrator's rule after recovery
 ("o01", "pipeline/orchestrator.py", "                if _lost(engine, run_id, \"planner\") > PLANNER_REPEATS:",
  "                if False:", REC),
 ("o02", "pipeline/orchestrator.py", "    if recovered and code in RECOVERABLE:\n        return None",
  "    if False:\n        return None", REC),
 ("o03", "pipeline/orchestrator.py", "and not (recovered and f in RECOVERABLE)]", "]", REC),
 ("o04", "pipeline/orchestrator.py",
  "            if recovered and code in RECOVERABLE:  # step 9b (owner, Q3): the Planner is repeated once",
  "            if False:  # step 9b (owner, Q3): the Planner is repeated once", REC),
]
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
for mid, f, old, new, tests in MUTATIONS + [("control", None, None, None, ["test_migrations_step9b.py", "test_queue.py", "test_guarded_parent.py", "test_worker.py", "test_recovery.py"])]:
    shutil.rmtree(os.path.join(M, "hypocurate"), ignore_errors=True)
    shutil.copytree("/workspaces/hypocurate/hypocurate", os.path.join(M, "hypocurate"))
    if f:
        p = os.path.join(M, "hypocurate", f); s = open(p).read()
        assert s.count(old) >= 1, (mid, "pattern not found")
        open(p, "w").write(s.replace(old, new, 1))
    out = subprocess.run([sys.executable if False else "/workspaces/hypocurate/.venv/bin/pytest", "-q", "-p", "no:cacheprovider",
                          "--rootdir=/workspaces/hypocurate"] + [T + t for t in tests], cwd=os.path.expanduser("~/hc-work/step09b"),
                         env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    caught = "failed" in out or "error" in out
    line = f"{mid:8} {'CAUGHT' if caught else ('clean' if mid == 'control' else 'SURVIVED')}  {out}"
    print(line, flush=True); results.append(line)
```
## 8. New tests on `main`'s code

Each new test file was written before its code and run against it; the counts are in the summary ("Tests") and in each commit message. The kill matrix was written after the code; it found the missing narrower-question sweep, fixed with its own test.

## 9. The suite and the images

The whole suite on this head (locally):

```
2123 passed, 1 warning in 1969.99s (0:32:49)
local exit 0
```

The whole suite in the test image, rebuilt on this head:

```
2123 passed, 1 warning in 2601.58s (0:43:21)
exit 0
```

The package in the repository, the runtime image and the test image (SHA-256 over every file):

```
head:    8fc9c93
repo:    ecc70f984ad8e428244fe5584b34efe9a98f5b3c708e46e3d01d536310a94c9a  -
runtime: ecc70f984ad8e428244fe5584b34efe9a98f5b3c708e46e3d01d536310a94c9a  -
test:    ecc70f984ad8e428244fe5584b34efe9a98f5b3c708e46e3d01d536310a94c9a  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
```

The guard checks inside the runtime image (its own package; no pytest in the image):

```
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmp5kay_k4i/.env is outside the approved inputs of pipeline code']}
```
```python
"""The guard tests' checks (tests/test_agent_libraries.py, the step 8b ones), run in the runtime image with its
own package: the image has no pytest and no tests/."""
import io, logging, os, tempfile
stream = io.StringIO()
logging.basicConfig(level=logging.WARNING, stream=stream)
from hypocurate.access.guarded import PRELOADED, run_guarded
PROBE = "hypocurate.access.guard_probe:probe"
results = {}
assert PRELOADED == ("psycopg", "scipy"), PRELOADED
results["statistics_libraries"] = run_guarded(PROBE, [{"op": "statistics_libraries"}], env=dict(os.environ), timeout=300)
results["refusals_after_clean_import"] = [l for l in stream.getvalue().splitlines() if "file_guard" in l]
results["agent_libraries"] = run_guarded(PROBE, [{"op": "agent_libraries"}], env=dict(os.environ), timeout=300)
d = tempfile.mkdtemp(); planted = os.path.join(d, ".env"); open(planted, "w").write("PLANTED_SECRET=x\n")
results["after"] = run_guarded(PROBE, [{"op": "statistics_libraries"}, {"op": "ctypes_string_at"}, {"op": "ctypes"},
                                       {"op": "dotenv", "path": planted}], env=dict(os.environ), timeout=300)
assert results["statistics_libraries"] == ["ok"], results
assert results["refusals_after_clean_import"] == [], results
assert results["agent_libraries"] == ["ok"], results
a = results["after"]
assert a[0] == "ok"
assert a[1] == "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code", a
assert a[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code", a
assert a[3].startswith("refused: file guard: reading"), a
print("ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE"); print(results)
```
## 10. The measurements on 0.5 CPU / 512 MB (runtime image)

```
NOTICE:  database "hc_measure_9b" does not exist, skipping
schema at 0008
== the worker and its child, one fixed-plan run (2,000 simulations), 0.5 CPU / 512 MB
MEASURE {"processes": [{"pid": "7", "cmd": "python -m hypocurate.worker --once ", "peak_rss_mib": 78.8}, {"pid": "10", "cmd": "/usr/local/bin/python -m hypocurate.access.guarded ", "peak_rss_mib": 387.9}], "container_peak_mib": 512.0}
/home/codespace/hc-work/step09b/measure/measure.sh: line 16: bc: command not found
wall  s
run 1 completed 21.1 s
checks|
critic|0.5
inclusion|0.9
dataset_freeze|1.1
statistics|2.9
gap_facts|0.0
analyst|9.5
== the statistics stage at 2000 simulations, 0.5 CPU / 512 MB
STATS {"n_simulations": 2000, "records_to_freeze_s": 3.6, "statistics_s": 3.2}
MEASURE {"processes": [{"pid": "8", "cmd": "python /m/stats10k.py 2000 ", "peak_rss_mib": 199.4}], "container_peak_mib": 189.3}
== the statistics stage at 10000 simulations, 0.5 CPU / 512 MB
STATS {"n_simulations": 10000, "records_to_freeze_s": 3.8, "statistics_s": 8.7}
MEASURE {"processes": [{"pid": "7", "cmd": "python /m/stats10k.py 10000 ", "peak_rss_mib": 239.1}], "container_peak_mib": 204.7}
```
### `~/hc-work/step09b/measure/measure.sh`

```bash
#!/bin/bash
# Scratch (not committed): memory and timing of the worker and its child on 0.5 CPU / 512 MB in the runtime image.
set -e
cd /workspaces/hypocurate
BASE="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
URL="${BASE%/*}/hc_measure_9b"
docker compose exec -T db psql -U hypocurate -d postgres -qc "DROP DATABASE IF EXISTS hc_measure_9b" -c "CREATE DATABASE hc_measure_9b"
DATABASE_URL="$URL" .venv/bin/python -m hypocurate.db.migrate upgrade
DATABASE_URL="$URL" .venv/bin/hypocurate sources register mpea tamu_fcc > /dev/null
.venv/bin/python ~/hc-work/step09b/measure/stub_server.py > /tmp/hc_stub_url &
STUB=$!; sleep 3; STUB_URL="$(head -1 /tmp/hc_stub_url)"
DATABASE_URL="$URL" .venv/bin/hypocurate run "In FCC multi-principal-element alloys, yield strength rises as grain size falls" --sources mpea,tamu_fcc --fixed-plan --by "measurement" --queue > /dev/null
RUN="docker run --rm --network host --cpus 0.5 --memory 512m -e DATABASE_URL -e ANTHROPIC_API_BASE=$STUB_URL -e ANTHROPIC_BASE_URL=$STUB_URL -e ANTHROPIC_API_KEY=sk-stub -v $HOME/hc-work/step09b/measure:/m:ro --entrypoint sh hypocurate:runtime -c"
export DATABASE_URL="$URL"
echo "== the worker and its child, one fixed-plan run (2,000 simulations), 0.5 CPU / 512 MB"
T0=$(date +%s.%N); $RUN 'python /m/sampler.py & S=$!; python -m hypocurate.worker --once; touch /tmp/measure.stop; wait $S' 2>&1 | grep -E "MEASURE|Traceback|Error" || true; echo "wall $(echo "$(date +%s.%N) - $T0" | bc) s"
docker compose exec -T db psql -U hypocurate -d hc_measure_9b -At -c "SELECT 'run ' || id || ' ' || status || ' ' || round(extract(epoch FROM completed_at - started_at)::numeric, 1) || ' s' FROM run" -c "SELECT s.stage, round(extract(epoch FROM s.finished_at - lag(s.finished_at) OVER (ORDER BY s.id))::numeric, 1) FROM stage_result s ORDER BY s.id"
for N in 2000 10000; do
  echo "== the statistics stage at $N simulations, 0.5 CPU / 512 MB"
  $RUN "python /m/sampler.py & S=\$!; python /m/stats10k.py $N; touch /tmp/measure.stop; wait \$S" 2>&1 | grep -E "STATS|MEASURE|Traceback|Error" || true
done
kill $STUB
docker compose exec -T db psql -U hypocurate -d postgres -qc "DROP DATABASE hc_measure_9b"
```
### `~/hc-work/step09b/measure/sampler.py`

```python
"""Scratch: inside the container, every 0.1 s, each hypocurate process's peak resident memory (VmHWM) so far, and the
container's whole peak (cgroup v2 memory.peak) at the end."""
import json, os, time
peaks, names = {}, {}
stop = "/tmp/measure.stop"
while not os.path.exists(stop):
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode()
            if ("hypocurate" not in cmd and "stats10k" not in cmd) or "sampler.py" in cmd:
                continue
            for line in open(f"/proc/{pid}/status"):
                if line.startswith("VmHWM:"):
                    kb = int(line.split()[1])
                    peaks[pid] = max(peaks.get(pid, 0), kb)
                    names[pid] = cmd[:80]
        except OSError:
            pass
    time.sleep(0.1)
out = {"processes": [{"pid": p, "cmd": names[p], "peak_rss_mib": round(peaks[p] / 1024, 1)} for p in peaks]}
try:
    out["container_peak_mib"] = round(int(open("/sys/fs/cgroup/memory.peak").read()) / 2 ** 20, 1)
except OSError:
    out["container_peak_mib"] = None
print("MEASURE " + json.dumps(out), flush=True)
```
### `~/hc-work/step09b/measure/stats10k.py`

```python
"""Scratch: inside the runtime container, a measurement-only fixed run whose locked plan asks for N simulations; the
steps run in order and the statistics stage is timed. Not the reference plan; the run is marked as a measurement by
nothing but its database (a scratch database, dropped afterwards)."""
import json, os, sys, time
from hypocurate.config import load_settings
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion, queries
from hypocurate.pipeline import plan as plans
n = int(sys.argv[1])
engine = make_engine(load_settings(web=False).database_url)
q = queries.create(engine, "measurement: FCC yield strength and grain size", ["mpea", "tamu_fcc"])
queries.submit(engine, q.version_id)
queries.confirm_domain(engine, q.version_id, by="measurement")
rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
queries.start(engine, rid)
p = plans.reference_plan(q.version_id)
p["calibration"]["n_simulations"] = n
checkpoints.lock_rules(engine, rid, p)
t0 = time.monotonic(); extract.store_records(engine, rid); checks.run_checks(engine, rid)
inclusion.decide_run(engine, rid); checkpoints.freeze_dataset(engine, rid); t1 = time.monotonic()
analysis.run_statistics(engine, rid); t2 = time.monotonic()
print("STATS " + json.dumps({"n_simulations": n, "records_to_freeze_s": round(t1 - t0, 1),
                             "statistics_s": round(t2 - t1, 1)}), flush=True)
```
### `~/hc-work/step09b/measure/stub_server.py`

```python
"""Scratch (not committed): the tests' local stub provider, served for the measurement run (no live call)."""
import sys, time
sys.path.insert(0, "/workspaces/hypocurate/tests")
import stub_provider as sp
import test_orchestrator as to
s = sp.StubProvider()
s.respond(to.responder())
print(s.base_url, flush=True)
while True:
    time.sleep(3600)
```
## 11. The plan and the scripts

### The approved 9b plan (`docs/reviews/step09b_plan.md`)

```markdown
# Build step 9b — the approved plan (queue, worker, recovery)

**Source.** Taken from the step 9 plan the owner approved on 2026-10-08 (questions Q1–Q7, recommendations R1–R8,
additions A1–A4), with what step 9a changed (merged and live as `c7458d0`, schema 0007). This file is the working
plan for 9b; it is kept on the branch so nothing is lost if a session's memory is compacted. **Go for 9b: the owner,
2026-10-08** ("Go for step 9b. This is my decision."). Branch `step-09b-worker` from `main` at `c7458d0`.

## The owner's decisions that bind 9b

| # | Decision (verbatim where quoted) |
|---|---|
| Q2 | **Render:** keep the worker on 0.5c-512mb (~$7/month). Measure the peak memory of the worker and its child in the runtime image; come back with the upgrade (1c-2g, ~$25) only if it is too close. **No `render.yaml` change in step 9.** |
| Q3 | **An interrupted paid stage:** the Planner is repeated **once**, as a new attempt; a second loss fails the run. The Critic is not repeated: its remaining flags stay "not classified" and the run goes on. The Analyst is not repeated: the run completes with "explanation unavailable (interrupted)". The lost call is always closed `interrupted` and counted at its reserved maximum. |
| A3 | **The child dies with its parent.** The worker's **main thread** starts the child (`Popen`); the heartbeat runs on its own thread. The child sets `PR_SET_PDEATHSIG(SIGKILL)` first thing in `guarded._main`, then checks that `getppid()` equals the parent pid passed in its request (closing the fork race). Tests: the heartbeat thread stops (made to exit) while the child keeps working and finishes; SIGKILL of the worker kills the child within 2 s, and the child's work lock is released; the child is started from the main thread (asserted on the thread that starts it). |
| A4 | **A stuck child.** `STALL_SECONDS = 900`: if the run writes nothing (no stage or call row started or finished, no status change) for 900 s, the parent kills the child and releases the claim as `child_stuck`, and recovery applies (900 s covers one agent call's two requests at the 300 s request timeout, plus 300 s of margin). `RUN_TIMEOUT_SECONDS = 1800`, the whole run, as a backstop. Both in the register. `queue` shows, per run, the time since its last write besides the heartbeat age. Test: a child stalled by a test trigger is killed at a (shortened, test-only) limit, and its run is recovered. (Live runs on the dev DB took 10–41 s; the longest stage 36 s, the longest call 17 s.) |
| Note | **Measuring the statistics stage (owner):** "when you measure a run on 0.5 CPU, also report how long the statistics stage takes, because step 11 will raise the simulation count to about 10,000 and I need to know whether the 900 and 1,800 second limits will still fit." |
| R1 | `run`/`dispatch` work the run inline **through the same claim code**, up to the wait or the end, then print `show`'s output (PRD 12). `--queue` returns at once after the dispatch line, for the worker. |
| R2 | New commands: `queue` (queued, waiting and running runs, with stage, worker, heartbeat age, time since last write, recoveries); `worker [--once]`; `confirm <run> --by NAME [--queue]`. (`cancel` and `dispatch --again` were built in 9a; `confirm` takes no `--ceiling`, 9a fix round 1.) |
| R6 | **The heartbeat on the claim row**, not the run row, so it never waits behind a run lock: a named exception to the locking protocol, like audit rows. `run.heartbeat_at` and `run.current_stage` stay unused. |
| 9a rule | "A spending failure or any RUN_STOPS reason stays a stop after a resume … Interrupted stages and the one allowed Planner repeat stay in 9b." (9a fix round 1, owner.) |
| Go-for-9b rules | Failing tests first; full suite before every push; mutation checks on each new safeguard; reference runs byte-identical to `main`; no live model calls; no change to `render.yaml` or the workflows; stop if any reference number or fingerprint changes. Report the suite time (local and the GitHub suite step), the peak memory of the worker and its child on 0.5 CPU, and how long the statistics stage takes. End with the summary and review packet, push, and stop. **Do not merge.** |

Standing rules (from 9a): a reference number or fingerprint changes → stop all work; a mutation survives → add a test
and continue; a test seems wrong or would need weakening → stop that item and continue the others; `render.yaml` and
`.github/workflows/` are never touched. Report the GitHub suite step's duration in every summary (owner, 2026-10-08).

**Open question for the owner (asked 2026-10-08, needed by b3):** when recovery finds a stored recording or
reservation failure (a 9a stop), does it apply the Q3 per-role rule (recommended: close and count the call at its
maximum, then Planner once more / Critic skipped / Analyst "explanation unavailable"), or fail the run with a stated
reason? **Answer (owner, 2026-10-08), split by cause:**
- **A recording failure, or any database failure while saving a call** (`recording_failed`, and `reservation_failed`, the
  database failing to save the reservation): apply the Q3 per-role rule, as for an interruption. Close the call, count
  it at its reserved maximum, then repeat the Planner once, skip the Critic's remaining batches, or complete with
  "explanation unavailable" after the Analyst.
- **A spending refusal (a cap was reached):** it stays a stop, exactly as in 9a. Recovery only finishes the bookkeeping
  and ends the run the way 9a already does: the Analyst completes the run; the Planner and the Critic stop it. It never
  sends another request and never moves on to a later paid stage.
- **Tests:** one for each case at each of the three agents, including that a spending refusal at the Critic still
  prevents the Analyst's request after recovery.
- The two possible b5 items (memory near 512 MB; the statistics stage at ~10,000 simulations not fitting the limits)
  are fine as described: stop that item, report the numbers and options, carry on with the rest.

## Recovery: what happens at each stage

First, always, as bookkeeping only:
1. Every `started` call of the run is closed `interrupted` (`worker_stopped`, or `recording_failed`), with no usage. It keeps counting at `max_cost` in every cap and view.
2. Every `running` stage is closed `failed` (`interrupted`).
3. What was found is recorded on the claim row.

Recovery never writes a plan, a record, a set, a freeze or a confirmation. Forward progress goes only through the
normal path (the 9a orchestrator, which takes every step from stored rows) and its database guards.

| Where it stopped | Decision | Why |
|---|---|---|
| Queued | Claimed and started normally | Nothing written yet |
| Planner mid-call | **Repeated once** (new attempt, reserved against the caps); a second loss fails the run with `interrupted: the worker stopped during the Planner's request twice; dispatch the query again as a new run` | Nothing locked or confirmed yet; the cost is counted and shown (Q3) |
| Planner closed failed / domain mismatch, run not failed | Failed with the reason from the stored stage | Replays code's decision (9a) |
| Planner done, no narrowing | Narrowing resumed from the stored answer | Deterministic (9a) |
| Narrowing `proceed`, not confirmed | **Waiting**: nothing done | Waiting for a person; recovery never confirms |
| Narrowing `claim_not_one_plan` | Failed with the stored reason | Replays the decision |
| Partly path: Analyst mid-call | Not repeated; copy plus narrower question; "explanation unavailable (interrupted)" | A3/B2, Q3 |
| Completed partly sufficient with no narrower question | Narrower question finished (9a, idempotent) | The run is final |
| Confirmed, no plan | Rules lock by the normal path; the database checks the confirmation's fingerprint | A checkpoint reached normally |
| Locked: sources pending, Checks, Inclusion, freeze, statistics | Resumed from the first stage not done (9a) | Each one transaction, detectable, deterministic |
| Critic mid-batch, or between batches | Not repeated; remaining flags "not classified"; on to Inclusion | No decision reads the class (Q3) |
| Analyst mid-call (after statistics) | Not repeated; completed with "explanation unavailable (interrupted)" | A3/B2, Q3 |
| A recording or reservation failure stored (9a stop) | The Q3 per-role rule, as for an interruption (owner's answer) | The call is counted at its maximum; a database failure is not the run's fault |
| A spending refusal stored | Stays a stop, as in 9a: the Planner and the Critic fail the run; the Analyst completes it. No further request | A cap was reached (owner's answer) |
| A run recovered more than 3 times (`MAX_RECOVERIES`) | Failed: `attempts_exhausted: the run stopped at <stage> <n> times without finishing; dispatch it again as a new run` | A run is never left running for good |

## Claims, heartbeat, and "dead"

- **Claim:** the worker takes, without waiting, a session advisory lock `(CLAIM, run)` on its own lease connection and checks that `(WORK, run)` is free; then, in one locked transaction: re-check the run, close any stale claim as `lost`, insert a `run_claim` row, and move queued→running (or a confirmed waiting run→running). A partial unique index allows one open claim per run. Two workers can never both work a run; the cancel-versus-start race is closed by the same transaction.
- **The guarded child** takes `(WORK, run)` on its own connection for its whole work and exits at once, writing nothing, if it cannot. It dies with its parent (A3). Even if that failed, the orphan's lock keeps every other worker off the run.
- **Heartbeat:** a thread in the worker parent writes `run_claim.heartbeat_at` every **15 s** (`HEARTBEAT_SECONDS`).
- **Dead** means silent for **120 s** (`STALE_SECONDS`, 8 missed beats) *and* both advisory locks free. A claim released as `shutdown` or `stopped_for_recovery` can be claimed again at once. The child is killed after 900 s with no write, or 1,800 s in all (A4).
- **The worker shows it is alive** in `queue` (heartbeat age, time since last write), the claim rows, and the process log (one line per claim, release and recovery). The sweep runs on start and every 60 s.
- **Deploy (SIGTERM):** stop claiming, send SIGTERM to the child, release the claim as `shutdown`. A request in flight becomes an interrupted call (the table above).
- The parent never imports dspy, litellm or scipy, which keeps memory low (Q2).

## Migration 0008 (hand-written)

`run_claim`: worker, child pid, claimed, heartbeat, released, `release_reason` (`finished`, `waiting`,
`stopped_for_recovery`, `child_failed`, `child_stuck`, `shutdown`, `lost`), and what recovery found; no delete; only
the heartbeat may change while the claim is open; released once; one open claim per run (partial unique index).
Trigger names sort after earlier ones per table and event. Tested up, down and up, against direct SQL, and with the
previous release's code.

## Milestones (estimates as given to the owner, 2026-10-08)

| M | What | Est. |
|---|---|---|
| b0 | This file; branch; golden dumps from `main` (`c7458d0`) | 0.5 h |
| b1 | 0008 + tests | 1.5 h |
| b2 | `pipeline/queue.py` (claim, locks, heartbeat thread), `worker.py` loop, SIGTERM; `guarded.py` Popen path + PDEATHSIG (A3) | 3.5 h |
| b3 | `pipeline/recovery.py` (the table, `MAX_RECOVERIES`, `PLANNER_REPEATS`, reasons in plain words; A4 limits) | 2.5 h |
| b4 | CLI inline-through-claim, `--queue`, `queue`, `worker --once` | 1 h |
| b5 | Kill matrix, two workers, recording failure, checkpoint restarts, caps, 14.4; memory and timing on 0.5 CPU, incl. the statistics stage now and estimated at ~10,000 simulations | 4 h |
| b6 | Register, mutations, images, reference comparison, suites, summary, packet, push | 2 h |

## Tests

- **Kill points.** Code stages: a test-only trigger in the scratch database does `pg_sleep` at the chosen write; the test waits until `pg_stat_activity` shows it, then SIGKILLs the child or the parent. Agent stages: the stub provider kills the process while the request is in flight. No hook in production code.
- **Kill the worker at each stage:** mid-Planner (repeat, then complete; twice → failed with the reason), before narrowing, while waiting, after the lock, between sources, before Checks, mid-Critic batch 1 of 2, before Inclusion, before the freeze, mid-statistics, mid-Analyst, between the partly copy and the narrower question (exactly one). Each case: no stage stays running and no call stays started; every lost call ends `interrupted`, counted at its maximum; no stub request is repeated except the one Planner repeat; final fingerprints and results equal the uninterrupted run's.
- **Kill the parent:** the child dies, its lock is released, another worker recovers the run (A3 tests).
- **Two workers:** two worker processes and one queued run → one claim, no duplicated request; two claims at once → one gets nothing; an orphan child holding the work lock → the run cannot be claimed.
- **Recording failure:** a test trigger makes `finish` fail; the run stays open; after the trigger is dropped, recovery closes the call at its maximum and applies the rule (the open question).
- **Restart with a run at each checkpoint:** waiting before the lock (no claim, no call; after confirm it completes); after the lock; after the freeze — each resumes with the same results.
- **Caps across crashes:** repeated interruptions stay within $2; a repeat that would pass the cap is refused before sending; the stored ceiling holds after recovery; the month near $50 → a recovery repeat is refused `spending_cap_month`.
- **Stuck child (A4):** killed at a shortened test-only limit; its run is recovered.
- **Criterion 14.4**, bullets 2 and 4. **Reference runs byte-identical to `main`.** The web code never claims or runs a pipeline.

## Left for step 10 (screens)

Confirm and Cancel buttons; Dispatch again; the queue under Review and dispatch; the month-cap message; run viewer
polling and the waiting stage state; claim, heartbeat and recovery facts on the run page; criterion 14.4 bullets 1
(close the browser) and 3 (web restart); labels on lists (`constructed_test_runs`).

## Register entries (9b)

The queue and claims; the recovery policy; `HEARTBEAT_SECONDS` (15), `STALE_SECONDS` (120), `STALL_SECONDS` (900),
`RUN_TIMEOUT_SECONDS` (1800), `MAX_RECOVERIES` (3), `PLANNER_REPEATS` (1); the guarded runner's parent-death rule;
the heartbeat exception to the locking protocol.

## Progress

- [x] b0 (dumps from main c7458d0 in ~/hc-work/step09b/refdump/main, SHA256SUMS; a second dump identical; the confirmation time in labels normalised)  - [x] b1 (9c999ed)  - [x] b2+b3 (6a5f965; adapter change undone in the next commit)  - [x] b4  - [x] b5 (823236a; memory at the 512 MiB limit -> owner: worker to 1c-2g, ae8aa00; statistics 8.7 s at 10,000)  - [x] b6 (register a5ba354; 27/27 mutations caught after three tests; images hashed; reference byte-identical; suites, packet, push: in progress)
```
### `~/hc-work/step09b/register_9b.py`

```python
"""Step 9b register entries (scratch; run from the repo root with the project's Python)."""
import json
P = "hypocurate/assumptions.json"
d = json.load(open(P, encoding="utf-8"))
by = {e["key"]: e for e in d}
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-08"}
NR = {"status": "not_reviewed", "name": None, "date": None}
PLAN = "Step 9 plan approved by the owner on 2026-10-08 (R6, Q2, Q3, A3, A4); docs/reviews/step09b_plan.md; the owner's answer on recovery (2026-10-08)."


def new(key, name, statement, value, unit, affects, reason, settings, tests, notes=()):
    assert key not in by, key
    e = {"key": key, "name": name, "state": "in_force", "statement": statement, "value": {"text": value, "unit": unit},
         "category": "operational", "affects": affects, "reason": reason, "evidence": [PLAN], "decided": OWNER,
         "expert_review": NR, "sensitivity": None, "applied": {"status": "yes", "settings": settings, "note": None},
         "tests": tests, "history": [], "notes": list(notes)}
    d.append(e)
    by[key] = e


def reword(key, old, new_text, note):
    e = by[key]
    assert e["statement"].count(old) == 1, (key, old[:60])
    e["history"].append({"value": e["statement"], "from": e["decided"]["date"], "to": "2026-10-08", "note": note})
    e["statement"] = e["statement"].replace(old, new_text)
    e["decided"] = OWNER


new("queue_and_claims", "The queue: claims and the heartbeat",
    "A worker claims one run at a time: on its own autocommit lease connection it takes, without waiting, a session "
    "advisory lock on the run (CLAIM) and checks that the run's WORK lock is free; then, in one transaction under the "
    "run's lock, it re-checks the run, closes a stale open claim as 'lost', records its claim (run_claim; one open claim "
    "per run) and starts the run (queued, or a confirmed waiting run, becomes running). The guarded child holds the "
    "run's WORK lock for its whole work; an orphan child holding it keeps every worker off the run. A claim's heartbeat "
    "is written every 15 seconds by a thread of the worker on the claim row, never the run row, so it never waits behind "
    "the run's lock (a named exception to the locking protocol, like audit rows). A claim is taken to be dead when its "
    "heartbeat is older than 120 seconds; a claim released for recovery or at shutdown is claimable at once. Running runs "
    "are taken up first, then confirmed waiting runs, then queued runs in the order of dispatch. The worker parent never "
    "imports dspy, litellm or scipy (it does load numpy, through the source adapters' spreadsheet library).",
    "heartbeat 15 s; dead after 120 s", "seconds", "Every run worked by the worker or the command line (PRD 8 'Queue', 'Restart').",
    "PRD 8; the owner's approval of R6 and of the claims design (step 9 plan).",
    [{"ref": "python:hypocurate.pipeline.queue:HEARTBEAT_SECONDS", "equals": 15},
     {"ref": "python:hypocurate.pipeline.queue:STALE_SECONDS", "equals": 120},
     {"ref": "python:hypocurate.pipeline.queue:RELEASE_REASONS",
      "equals": ["finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost"]},
     {"ref": "sql:uq_run_claim_open"}, {"ref": "sql:hc_run_claim_update"}],
    ["tests/test_queue.py::test_two_workers_never_hold_one_run",
     "tests/test_queue.py::test_claims_at_the_same_moment_give_the_run_to_one_worker",
     "tests/test_queue.py::test_a_run_whose_work_lock_is_held_by_an_orphan_child_is_not_claimed",
     "tests/test_queue.py::test_a_running_run_with_a_live_claim_is_left_alone_and_a_stale_one_is_taken_over",
     "tests/test_migrations_step9b.py::test_the_heartbeat_is_the_databases_time_and_needs_no_run_lock",
     "tests/test_worker.py::test_two_workers_and_one_run_give_one_claim_and_no_repeated_request",
     "tests/test_worker.py::test_the_worker_parent_loads_no_model_or_statistics_library"],
    notes=["Measured on 0.5 CPU / 512 MB in the runtime image (2026-10-08): worker parent peak 78.8 MiB; guarded child "
           "387.9 MiB; the container's cgroup peak reached its 512 MiB limit (it counts reclaimable file cache). The "
           "upgrade (1c-2g) is the owner's decision (Q2)."])

new("stuck_child_limits", "A stuck child",
    "The worker kills its child, releases the claim as 'child_stuck' and lets recovery take the run up when the run "
    "has written nothing (a status change, a stage or call started or finished, a source searched, a record stored, "
    "the confirmation, the lock, the freeze) for 900 seconds, or after 1,800 seconds in all. 900 seconds covers one "
    "agent call's two requests at the 300-second request timeout plus 300 seconds of margin. A deploy (SIGTERM) stops "
    "the child and releases the claim as 'shutdown'.",
    "900 s without a write; 1,800 s in all", "seconds", "Every run worked by the worker.",
    "Owner's addition A4 (step 9 plan). Live runs took 10-41 s; on 0.5 CPU a fixed-plan run took 21.1 s, the statistics "
    "stage 3.2 s at 2,000 simulations and 8.7 s at 10,000 (measured 2026-10-08).",
    [{"ref": "python:hypocurate.pipeline.queue:STALL_SECONDS", "equals": 900},
     {"ref": "python:hypocurate.pipeline.queue:RUN_TIMEOUT_SECONDS", "equals": 1800},
     {"ref": "python:hypocurate.pipeline.agents.lm:DEFAULT_TIMEOUT_SECONDS", "equals": 300}],
    ["tests/test_worker.py::test_a_stuck_child_is_stopped_and_its_claim_released_for_recovery",
     "tests/test_worker.py::test_the_whole_run_limit_stops_a_child_that_keeps_writing_too_long",
     "tests/test_worker.py::test_sigterm_shuts_the_worker_down_releasing_its_claim_and_stopping_its_child",
     "tests/test_queue.py::test_the_time_since_the_last_write_counts_stage_and_call_rows"])

new("recovery_policy", "Recovery when a run is taken up again",
    "When a worker claims a run that is already running, recovery first closes every open model call as "
    "'interrupted' (counted at its reserved maximum under every cap) and every running stage as failed "
    "('interrupted'); a run taken up more than 3 times fails ('attempts_exhausted'). It writes no plan, record, set, "
    "freeze or confirmation. The run then goes on by the normal path, by cause (owner, 2026-10-08): an interruption, a "
    "recording failure or any database failure while saving a call follows the per-role rule (the Planner is repeated "
    "once, a second loss fails the run; the Critic's remaining batches are skipped; after the Analyst the run completes "
    "with 'explanation unavailable'); a spending refusal stays a stop, exactly as in 9a (the Planner and the Critic fail "
    "the run, the Analyst completes it; no further request, never a later paid stage). The worker also finishes a "
    "narrower question that a stop left uncreated (never a second).",
    "3 recoveries; the Planner repeated once", None, "Every run left open by a crash, a stop or a deploy (PRD 8, 14.4).",
    "Owner's answer Q3 (step 9 plan) and the owner's answer on recovery, split by cause (2026-10-08).",
    [{"ref": "python:hypocurate.pipeline.recovery:MAX_RECOVERIES", "equals": 3},
     {"ref": "python:hypocurate.pipeline.recovery:PLANNER_REPEATS", "equals": 1},
     {"ref": "python:hypocurate.pipeline.recovery:RECOVERABLE",
      "equals": ["interrupted", "recording_failed", "reservation_failed"]},
     {"ref": "python:hypocurate.pipeline.recovery:ANALYST_INTERRUPTED", "equals": "explanation unavailable (interrupted)"}],
    ["tests/test_recovery.py::test_a_lost_planner_request_is_repeated_once",
     "tests/test_recovery.py::test_a_second_lost_planner_request_fails_the_run_with_the_reason",
     "tests/test_recovery.py::test_a_critic_spending_refusal_stays_a_stop_and_the_analyst_is_never_asked",
     "tests/test_recovery.py::test_a_lost_analyst_request_completes_the_run_with_the_explanation_unavailable",
     "tests/test_recovery.py::test_a_run_recovered_more_than_max_recoveries_times_fails",
     "tests/test_kill_matrix.py::test_a_worker_killed_at_a_code_stage_is_taken_up_with_the_same_results",
     "tests/test_kill_matrix.py::test_a_worker_killed_mid_planner_repeats_the_planner_once",
     "tests/test_kill_matrix.py::test_14_4_a_worker_stopped_mid_run_and_restarted_finishes_the_run"])

new("guarded_child_dies_with_parent", "The guarded child dies with its worker",
    "The worker's main thread starts the guarded child (guarded.start_guarded refuses any other thread) and passes its "
    "pid; the child sets PR_SET_PDEATHSIG(SIGKILL) first thing, then exits at once if its parent is not that process "
    "any more (the parent died before the signal was set). The child holds the run's work lock on its own connection, "
    "so even an orphan keeps every worker off the run until it ends. run_guarded (the command line before step 9b) is "
    "unchanged.",
    "SIGKILL with the parent", None, "Every guarded child the worker starts.",
    "Owner's addition A3 (step 9 plan).",
    [{"ref": "python:hypocurate.access.guarded:PR_SET_PDEATHSIG", "equals": 1},
     {"ref": "python:hypocurate.access.guarded:PARENT_GONE_EXIT", "equals": 3},
     {"ref": "python:hypocurate.access.guarded:start_guarded"}],
    ["tests/test_guarded_parent.py::test_the_child_dies_within_two_seconds_when_its_parent_is_killed",
     "tests/test_guarded_parent.py::test_the_child_outlives_a_thread_of_its_parent_that_exits",
     "tests/test_guarded_parent.py::test_a_child_is_started_only_from_the_main_thread",
     "tests/test_guarded_parent.py::test_a_child_whose_parent_is_already_gone_exits_at_once",
     "tests/test_worker.py::test_killing_the_worker_kills_its_child_and_frees_the_runs_locks"])

reword("resumable_run", "Recovery after a crash (closing open stages and calls, the Planner's one repeat after an interruption) is step "
       "9b; until then a stage left running stops the run.",
       "Recovery after a crash (closing open stages and calls, the Planner's one repeat) is register 'recovery_policy' "
       "(step 9b); without a recovery a stage left running stops the run.",
       "Step 9b: recovery is built.")
reword("run_order_and_failures", "until step 9b's recovery.",
       "until recovery takes it up (register 'recovery_policy', step 9b).",
       "Step 9b: recovery is built.")

with open(P, "w", encoding="utf-8") as f:
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(len(d), "entries")
```
### `~/hc-work/step09b/packet.py`

````python
"""Builds docs/reviews/step09b_review_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step09b"
BASE = "c7458d0"
OUT = Path("docs/reviews/step09b_review_packet.md")
PLAN = Path("docs/reviews/step09b_plan.md")


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
parts = [f"""# Build step 9b — review packet

Date: 2026-10-08. Branch: `step-09b-worker`, from `main` at `{BASE}`. Head when generated: `{head}`. Generated from
the files on disk by a script (`~/hc-work/step09b/packet.py`, quoted in section 10), so every diff and output below is
quoted exactly.

## How to use this packet

Step 9b builds the queue and the worker: claims and their heartbeat (migration 0008), the guarded child that dies
with its parent, recovery when a run is taken up again, and the command line through the claim. It holds safeguard
changes (listed at the top of the summary), so please review against `docs/reviews/checklist.md` and answer the
questions at the end of the summary. Sections: 1 the summary; 2 the code diff; 3 the new test files; 4 the changed
tests; 5 the register; 6 the reference comparison with `main`; 7 the mutation checks; 8 new tests on `main`'s code;
9 the suite and the images; 10 the measurements on 0.5 CPU; 11 the plan and the scripts.

"""]
parts.append("## 1. The summary\n\n" + read("docs/reviews/step09b_summary.md") + "\n")
diff = sh("git", "diff", f"{BASE}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{BASE}..HEAD`, the package with migration 0008; the register is in section 5)\n\n"
             + fence(diff, "diff"))
new_tests = sh("git", "diff", "--name-only", "--diff-filter=A", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 3. New test files\n\n" + "".join(f"### `{p}`\n\n" + fence(read(p), "python") for p in new_tests))
changed = sh("git", "diff", "--name-only", "--diff-filter=M", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 4. Changed tests and test helpers (diff)\n\n" + fence(sh("git", "diff", f"{BASE}..HEAD", "--", *changed),
                                                                       "diff"))
reg_old = {e["key"]: e for e in json.loads(sh("git", "show", f"{BASE}:hypocurate/assumptions.json"))}
reg_new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
added = [k for k in reg_new if k not in reg_old]
modified = [k for k in reg_new if k in reg_old and reg_new[k] != reg_old[k]]
reg = "".join(f"### New: `{k}`\n\n" + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in added)
reg += "".join(f"### Changed: `{k}` (the entry as it now stands; earlier wording in its history)\n\n"
               + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in modified)
parts.append(f"## 5. Assumptions register ({len(reg_new)} entries; {len(added)} new, {len(modified)} changed)\n\n" + reg)
parts.append("## 6. Reference comparison with `main`\n\nDumped on `main`'s code (`" + BASE + "`) before any change, twice "
             "(byte-identical), and on this head. Byte comparison of every file:\n\n"
             + fence(read(HOME / "refdump/cmp_final.txt")) + "\nLeaf-by-leaf differences of the orchestrator dumps:\n\n"
             + fence(read(HOME / "refdump/compare_final_output.txt")) + "\nThe SHA-256 sums of `main`'s dumps:\n\n"
             + fence(read(HOME / "refdump/main/SHA256SUMS")) + "\nThe comparison script:\n\n"
             + fence(read(HOME / "refdump/compare.py"), "python") + "\nThe dump tests:\n\n"
             + fence(read(HOME / "refdump/test_zz_orchdump.py"), "python")
             + fence(read(HOME / "refdump/test_zz_refdump.py"), "python"))
parts.append("## 7. Mutation checks (each fault against its named tests; a control run with no mutation last)\n\n"
             + fence(read(HOME / "final_mutations.log")) + "\nThe specification and the runner:\n\n"
             + fence(read(HOME / "mspec/mutations.py"), "python") + fence(read(HOME / "mspec/run_any.py"), "python"))
parts.append("## 8. New tests on `main`'s code\n\nEach new test file was written before its code and run against it; "
             "the counts are in the summary (\"Tests\") and in each commit message. The kill matrix was written after "
             "the code; it found the missing narrower-question sweep, fixed with its own test.\n\n")
parts.append("## 9. The suite and the images\n\nThe whole suite on this head (locally):\n\n"
             + fence(lines_with(HOME / "final_full.log", "passed", "failed", "exit"))
             + "\nThe whole suite in the test image, rebuilt on this head:\n\n"
             + fence(lines_with(HOME / "image_suite.log", "passed", "failed", "exit"))
             + "\nThe package in the repository, the runtime image and the test image (SHA-256 over every file):\n\n"
             + fence(read(HOME / "image_hashes.txt"))
             + "\nThe guard checks inside the runtime image (its own package; no pytest in the image):\n\n"
             + fence(read(HOME / "image_guard.log")) + fence(read(HOME / "imgcheck/guard_in_image.py"), "python"))
parts.append("## 10. The measurements on 0.5 CPU / 512 MB (runtime image)\n\n" + fence(read(HOME / "measure/measure_output.txt"))
             + "".join(f"### `~/hc-work/step09b/measure/{m}`\n\n" + fence(read(HOME / "measure" / m), "python" if m.endswith(".py") else "bash")
                       for m in ("measure.sh", "sampler.py", "stats10k.py", "stub_server.py")))
scripts = ["register_9b.py", "packet.py"]
parts.append("## 11. The plan and the scripts\n\n### The approved 9b plan (`docs/reviews/step09b_plan.md`)\n\n"
             + fence(read(PLAN), "markdown")
             + "".join(f"### `~/hc-work/step09b/{s}`\n\n" + fence(read(HOME / s), "python") for s in scripts))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
