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

## Fix round 1 (owner, 2026-10-09): all seven findings accepted

Owner's instructions (verbatim essentials): fix each finding on `step-09b-worker` with a failing test first, then a
fix packet for a second review; do not merge. (1) Record a spending refusal durably against its request (the existing
refusal audit row) and have recovery check it before classifying a running stage as interrupted; test a real refusal
followed by a failed save, at the Planner and the Critic, including across a month change. (2) Never release a claim
with a live child: stop and reap it on every exit path; escalate a SIGTERM that doesn't work to SIGKILL; check for
shutdown before starting a child. (3) Losing the lock means stopping: worker and child fail closed; bind the child's
work to the current claim so a stale owner is refused before any further request or write; test by terminating the
lock-holding sessions while the processes stay alive. **Owner's addition:** do the claim check inside the same
transaction as the write and lock the claim row there (`SELECT … FOR SHARE`), so a takeover that closes the claim
waits for that write or the write sees the closed claim and refuses; a two-connection test of a takeover racing a
child write; for model requests the check before the reservation is enough. (4) The recovery exception applies only
to old stages. (5) Monitoring cannot block the watchdog: time-limit monitoring queries; the 1,800 s kill and the
shutdown check independent of them; test with a blocked monitoring connection. (6) The stall allowance starts at the
current attempt's launch and resets on progress. (7) Count recovery attempts explicitly, excluding the first run;
test three recoveries then refusal of the fourth with real claim histories. Also: the kill case "mid-Critic, batch 1
of 2" with two-batch data; `client_connection_check_interval` 1 s for worker sessions plus TCP keepalives; fix the
stale "cheapest paid plans" comment in render.yaml; the full render.yaml diff in the fix packet; correct the register
wherever it promises more than the code. **Design choices approved (owner, 2026-10-09):** the refusal's audit row in
the deciding transaction; the claim/lock check in `writes.write` and `spend.reserve` (`claim_lost`).

- [x] finding 1 (refusal durable; 6 tests failed before)
