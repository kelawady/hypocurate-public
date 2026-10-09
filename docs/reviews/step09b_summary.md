# Build step 9b — summary for review

Date: 2026-10-08/09. Branch: `step-09b-worker` (from `main` at `c7458d0`). **Status: fix round 1 done; pushed for a second review; not merged.** ChatGPT's review of `368a426` ("not safe to merge", seven findings) is in `docs/reviews/step09b_review_chatgpt.md`. The owner accepted all seven; the fixes are in "Fix round 1" below, and the evidence is in `docs/reviews/step09b_fix_packet.md`.

## Fix round 1 (2026-10-09)

Each finding has tests that failed on the reviewed code (`368a426`) and pass now: **22 new tests failed there**, run with every process (pytest, the worker and its child) on the reviewed code. The one new test that passes there is the "mid-Critic, batch 1 of 2" kill case, which is new coverage, not a fix.

1. **A spending refusal survives a failed save.**
   - **The refusal's record:** its audit row is written in the transaction that decides the refusal (the owner's first design choice). A refusal is reported only once its record is committed.
   - **Recovery** keeps a committed refusal as the stage's cause before it would close the stage as `interrupted`, so the Planner and the Critic still stop the run.
   - **Tested** at the Planner (the run's ceiling, the monthly cap, and the cap after a month change) and at the Critic (the cap, and after a month change); after a Critic refusal the Analyst is never asked.
2. **Never release a claim with a live child.**
   - The worker stops and reaps its child in `finally` on every exit path, before the release.
   - A SIGTERM not obeyed within 10 s (`guarded.STOP_GRACE_SECONDS`) becomes SIGKILL.
   - Shutdown is checked before each child starts.
3. **Losing the lock means stopping.**
   - **The worker:** each heartbeat checks that it touched the open claim and that the lease session still holds its lock; otherwise the worker kills the child and gives the run up (`lost`).
   - **The child:** it is bound to its claim. `writes.write` and `spend.reserve` refuse `claim_lost` unless the claim is open and the child's work lock is held (the owner's second design choice).
   - **The owner's addition:** `writes.write` makes this check inside the write's own transaction, with the claim row locked. A takeover that closes the claim waits for the write, or the write sees the claim closed. For model requests the check comes before the reservation.
   - **One difference from the owner's example:** the row lock is **FOR KEY SHARE**, not FOR SHARE. 0008's update trigger locks the claim row FOR UPDATE before it closes a claim, so closing still waits for a write in progress. Under FOR SHARE, the worker's own heartbeat (a plain update) would wait behind a long write and wrongly report the claim lost.
   - **Tested** by terminating the lock-holding database sessions while the processes stay alive, by a two-connection race of a takeover against a child's write, and with a stale owner's reservation.
   - **The race test's check (changed with the owner's approval, `a9251d2`):** it first compared two Python clock readings taken after each thread's database call. That failed once in the whole suite by scheduling chance. It now checks the wait itself: the takeover's close takes at least 1 s, and the claim's release time on the database's clock is after the end of the write's work. It passes 5 of 5, and fails on both lock faults (f09, f10).
4. **The recovery exception applies only to old stages.** A lost Critic request is excused only for Critic stages stored before the recovery. A Critic run after recovery that fails to record its call stops the run.
5. **Monitoring cannot block the watchdog.** The run's last write is sampled on a thread of its own, each query limited to 5 s (`queue.MONITOR_TIMEOUT_MS`). The main thread never queries while it watches: the 1,800 s limit, the shutdown check and the lost-claim check run on its own clock and events. Tested with a blocked monitoring query.
6. **The stall allowance starts fresh:** 900 s from the attempt's launch, reset on progress; downtime before the attempt does not count.
7. **Recovery count:** `run_claim.recovery` (0008 amended in place, still unmerged) marks a claim that took up a running run. More than 3 such claims fail the run. Tested with real claim histories: three recoveries go on, the fourth is refused.

**Also (the owner's list):**
- **The two-batch kill case:** "mid-Critic, batch 1 of 2", with 110 two-record flags.
- **Worker sessions:** `client_connection_check_interval = 1s` plus TCP keepalives, on both sides (`db.engine.WORKER_SESSION`; register `worker_session_settings`).
- **`render.yaml`'s header comment** now says the worker is on 1c-2g (its own commit). The full `render.yaml` diff is in the fix packet.
- **The register** is corrected where it promised more than the code: `queue_and_claims`, `stuck_child_limits`, `recovery_policy`, `spending_caps`.

**Mutation checks:**
- **The faults:** all 19 faults of this round and all 27 earlier 9b faults are caught.
- **f14 and f15:** their tests first detected these faults only by hanging. Two monitoring tests were changed to fail within their limits instead (`641af6b`, no assertion changed).
- **The harness:** it now labels runs with errors or no result as ERROR or HUNG, never as caught. One run with the database down was discarded.
- **The test image's suite** ran with `docker run --network host` against the same database. Since the Codespace restart, the Compose network drops traffic between containers (a legacy firewall table). The image and the tests are the same, and the hashes are in the packet.

**Reference runs:** byte-identical to `main` (six dumps, 0 differing leaves).

**Suite:** 2,146 tests (2,123 at the review), all passing on `a9251d2`: locally in 36 min 25 s, and in the test image rebuilt on this head in 41 min 42 s. **The GitHub run's suite step** on the reviewed head was 30 min 9 s (run 37874572593). This round's figure comes with the push and is added in the next commit, as before.

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
   - **The header comment** ("Plans: the cheapest paid plans") now names the worker's exception (fix round 1, the owner's instruction of 2026-10-09; its own commit).

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

**The GitHub run's suite step:** **30 min 9 s** on the reviewed head `368a426` (run 37874572593; the job limit is 40 minutes since `4784d15`). The fix round's figure is in "Fix round 1" above.

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

**148 entries** (fix round 1: `worker_session_settings` new; `queue_and_claims`, `stuck_child_limits`, `recovery_policy` and `spending_caps` corrected).
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
2. **`client_connection_check_interval`:** done in fix round 1 (1 s on worker sessions, plus TCP keepalives).
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
