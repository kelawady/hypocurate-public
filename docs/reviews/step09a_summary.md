# Build step 9a — summary for review

> **Update, 2026-10-08: fix round 1.** ChatGPT's review (`step09a_review_chatgpt.md`) found the step **not safe to merge**, with five findings. The owner accepted all five and decided that every run stores its effective ceiling at dispatch. Each fix came with tests that failed on the code before it.
>
> | Finding | What was wrong | What changed |
> |---|---|---|
> | 1 | A resume read only done stages: it could ask the Planner again after a failed reservation, run the Analyst after a Critic accounting failure, or complete after an Analyst one. | Before each agent step the orchestrator reads the role's latest stored stage, whatever its status. An earlier stop stays a stop; a stored spending refusal still fails the run. |
> | 2 | The database did not check the sources' freshness, and the Python check could race a registration. | The confirmation trigger refuses a newer sealed version of a source the run uses, or a source registered after dispatch. A confirmation, a source registration and a version seal share one advisory lock; `confirm` takes it before its own check. |
> | 3 | `run()` could not take up a confirmed run: `prepare()` tried to wait again. | `prepare()` recognises a confirmation or a locked plan and goes on to `proceed()`. |
> | 4 | A ceiling given at confirmation was lost on a restart. | `confirm --ceiling` is removed: the ceiling is set only at dispatch. |
> | 5 | "Cancel only when queued or waiting" was not a database rule. | The database refuses a failure reason beginning "cancelled:" unless the run was queued or waiting. |
> | Owner | — | Every new run stores its ceiling. None given means the per-run cap ($2), set by code and by the column's default; older runs stay empty. |
>
> **Checks on this round's code (`7fc5ee3`):**
> - The whole suite passes: 2,019 tests, locally and in the rebuilt test image.
> - 35 of this round's new tests failed on the reviewed code; the rest are guards by design.
> - Mutation checks: 18 of 18 new faults and 39 of 39 earlier ones caught, both control runs clean.
> - The reference runs are byte-identical to `main`. The whole runs differ only by `spending_ceiling` (now 2, the owner's decision) and the confirmed label.
> - Both images were rebuilt, and their package is identical to the repository's. The Codespace restarted during the checks; the images had to be rebuilt after a pruned build cache.
>
> 0007 was amended in place (unmerged; never applied to the live database). The details, the tests that failed before, the mutation checks and the register changes are in `step09a_fix_packet.md`. The sections below describe the state after the fixes. Where a passage was corrected, it says so.

Date: 2026-10-08. Branch: `step-09a-waiting` (from `main` at `ed46b48`). **Status: fix round 1 done; pushed for the second review; not merged** (the owner's end point for 9a: "full suite, summary, packet, push the branch, stop. No merge").

PRD Section 15, step 9 ("Worker and queue"), first part. The owner split step 9 into two parts, each reviewed and merged separately:
- **9a (this part):** the wait at the rules lock and the confirmation by a named person; cancel; dispatch again; the spending ceiling stored on the run; two new dispatch refusals; an orchestrator that takes every step from stored rows. The command line only.
- **9b (next):** the queue, claims, heartbeat, the worker loop, the guarded runner's change, recovery after a crash, and criterion 14.4.

The plan, every owner answer and the progress checklist are in the step 9 plan file (quoted in the packet).

**Safeguard changes in 9a (second-model review before any merge; CLAUDE.md "How we work" item 5):**

1. **Migration 0007:** the status `waiting`; `rules_confirmation`; the plan backstop; `run.spending_ceiling`; one narrower question per run. It replaces 0001's `hc_run_update`, extending only its list of status changes.
2. **The confirmation path** (`pipeline/confirmation.py`): what is shown, the source check, one run and one named person.
3. **The orchestrator:**
   - it waits before the lock, and locks only the confirmed plan;
   - it takes every step from stored rows;
   - it never repeats a stored step or an existing agent stage.
4. **Spending:** the stored ceiling, read by `spend.reserve`; the monthly cap checked at dispatch.
5. **The dispatch refusal for constructed test data**, in front of the storage guard (owner, Q6).

**Not changed:** `render.yaml`, `.github/workflows/`, the Dockerfile, Compose, and the dependency locks (checked with `git diff --name-only main..HEAD`). The access layer, its allow-lists and the guarded runner are unchanged. No PRD document is changed; corrections are listed at the end.

## The owner's decisions (2026-10-08)

Planning answers, one question at a time:

| # | Decision |
|---|---|
| Q1 | The run **waits at the rules lock** for a named person to confirm the question as tested, after the Planner and a narrowing decision to proceed. The dataset freeze stays automatic. |
| Q2 | Render: the worker stays on its current plan; memory is measured in 9b. No `render.yaml` change in step 9. |
| Q3 | An interrupted paid stage: the Planner is repeated once; the Critic and the Analyst are not repeated. This is 9b's recovery. In 9a, an agent stage that exists is never started again. |
| Q4 | Existing tests that go through the Planner or a narrower question get one confirm step in their setup. No assertion changes; each change is listed below. |
| Q5 | Planner runs and narrower questions' runs wait. A fixed-plan run (14.1a, the reference runs) does not. |
| Q6 | Dispatch refuses a query naming a constructed source unless the run is marked as a test. The storage guard stays as the backstop. |
| Q7 | Step 9 is split into 9a and 9b. |
| R1–R8 | Approved recommendations: `run`/`dispatch` behaviour, the new commands, cancel only when queued or waiting, no expiry of a waiting run, spending, the heartbeat on the claim row (9b), the live check before the deploy, and the PRD-update list. |
| A1 | Which sources a waiting run uses. A confirmation is refused when the registered sources changed since the narrowing; it is never redone. With a test. |
| A2 | What `confirm` shows, stored exactly as shown. Step 10 shows the same content. |
| A3, A4 | 9b: the child dies with its parent; a stuck child is visible and limited (900 s without a write, 1,800 s in all). |
| Go for 9a | All defaults. The six reasons are worded as proposed, the monthly cap's in the owner's words. The label once confirmed. Claude drafts the register entries. The dev DB is backed up and migrated. No live call. The rules for surprises. **No bulk or automatic confirmation in step 9** (step 11 decides how evaluation runs are confirmed). |

**One scoping for the reviewer (stated to the owner during the build).** The database recognises a run that must wait by a **Planner stage (any attempt)** or by a **narrower link**. It does not use `fixed_plan = false`.
- **Why:** the step 6–8 test worlds lock plans directly on runs that have no Planner (16 files and helpers). Holding them to a confirmation would change hundreds of tests' premises.
- **What it means:** a run with no Planner stage and no narrower link is not held to a confirmation by the database. In the code, the orchestrator builds a plan from a model's answer only from a stored Planner stage (`confirmation.plan_to_lock`), so no path in our code locks such a plan without a confirmation.
- **What it does not cover:** direct SQL that locks a plan on a run with no Planner stage. That is outside the threat model (our own code), and stated plainly here.
- **The strict alternative** (every non-fixed run) would need a confirmation in every plan-locking test helper. The owner can ask for it as a follow-up.

## What was built (each commit on the branch)

| Commit | What |
|---|---|
| `cd4b38b` | Migration 0007, the models, the migration tests; test worlds that lock a narrower question's plan confirm it first. |
| `70bc74c` | `queries`: cancel, dispatch again, the stored ceiling, the month-cap and test-data refusals, an idempotent narrower question; `spend.reserve` reads the stored ceiling. |
| `394a425` | `pipeline/confirmation.py`; the orchestrator (the wait, the confirmed plan, every step from stored rows); the label once confirmed. |
| `d929839` | The command line: the wait, `confirm`, `cancel`, `dispatch --again`, `--ceiling` stored. |
| `0016c36` | The register. |
| `97bffda` | After the mutation checks: three tests, and the fixed text for code's own `not_confirmed` refusal (a defect the new test found). |

## Migration 0007

0001 to 0006 are untouched as files. One earlier function is replaced: 0001's `hc_run_update`, copied verbatim with only its list of status changes extended. A test checks the text against 0001's own text. Every new rule is its own function, with a trigger named to fire after the earlier ones on its table.

| Rule | Where |
|---|---|
| Status `waiting`. New changes: running → waiting, waiting → running, waiting → failed (and waiting → waiting). Waiting → completed is refused. | `ck_run_status`, `hc_run_update` (0001's body) |
| A run waits only if (a) its plan comes from the Planner or a narrower question, (b) it has no plan, no stage running and no call open, (c) on the Planner path, code's latest narrowing decision is to proceed, and (d) it has not waited before. It goes on only with a confirmation. | `hc_run_waiting` (trigger `hc_run_update_waiting`) |
| No stage, model call, invocation, plan, record or result is written to a waiting run (only its status may change; audit rows are written in every state). | 0001's rules, which require `running` |
| `rules_confirmation`, append-only, one per run, at the database's time. It is only for a waiting run and names a person (1–200 characters). It holds the plan fingerprint (plan format), the content (a JSON object) and the text shown (not empty). A Planner run's confirmation names its done Planner stage and its latest narrowing decision; a narrower question's names neither. The source versions the narrowing counted must equal the run's (A1). | table, CHECKs, `hc_rules_confirmation_insert` |
| A plan for a run with a Planner stage, or for a narrower question, needs a confirmation of exactly its fingerprint. | `hc_plan_rules_confirmed` (trigger `hc_plan_insert_rules_confirmed`) |
| `run.spending_ceiling`: positive and finite, set at dispatch, never changed. *Fix round 1 (owner):* its default is the per-run cap, set after the column is added (older runs stay empty). | CHECK, default, `hc_run_waiting` |
| *Fix round 1:* a failure reason beginning "cancelled:" only from queued or waiting (finding 5). | `hc_run_waiting` |
| *Fix round 1:* a confirmation, a source registration and a version seal take one advisory lock; the confirmation refuses a newer sealed version of a source the run uses, or a source registered after dispatch (finding 2). | `hc_rules_confirmation_insert`, `hc_sources_lock` |
| At most one narrower question per original run. | unique index `uq_hypothesis_narrower_of_run_id` |

**The previous release's code with 0007:** it never sets `waiting` and writes no confirmation or ceiling. Its Planner runs and narrower questions are refused at the lock, deliberately; its fixed-plan runs are unaffected. The owner checks the live database for runs in progress before the deploy (R7).

**The downgrade** refuses while a run waits, a confirmation exists or a ceiling is set. It then restores 0001's function and status rule exactly (tested up, down, up with every function's source compared).

## A run that waits

```
Planner -> narrowing (code) -proceed-> WAITING -confirm(by)-> rules lock -> ... -> completed
narrower question's run: source-version check (B1) -> WAITING -> confirm(by) -> rules lock -> ...
fixed-plan run (14.1a): straight to the lock (never waits)
```

**What `confirm` shows** (A2) is built by code from stored rows only (`confirmation.content`) and rendered by `confirmation.render`:
- the original question;
- the question as tested, with its label;
- what was narrowed and why: for a narrower question, its original, the parts with no candidate record, and the original and narrower scopes; otherwise "not narrowed", with code's decision and the candidate counts per part;
- each scope part, marked as the claim states it or assumed;
- the outcome, the exclusion rules, the sufficiency option and its minimums;
- the source versions;
- the cost so far (counted toward the caps, and reported);
- the fingerprint of the plan to be locked.

The command line prints this text before anything is recorded. The confirmation stores the content and that exact text. It is refused if the content changed between showing and recording (`content_changed`).

**Sources while waiting** (A1):
- A waiting run uses exactly the sealed versions recorded at dispatch; 0001 refuses any change to them.
- `confirm` is refused when a chosen source has a newer sealed version, or a source was registered after dispatch. The reason reads: "`<source>` has a newer version (or was registered) since this run's narrowing; cancel this run and dispatch the query again". Nothing is redone or written.
- The database refuses a confirmation whose narrowing counted other versions. *Corrected (fix round 1, finding 2):* it now also refuses a newer sealed version of a source the run uses, or a source registered after dispatch, under a lock shared with registration and sealing.

**One run, one named person:**
- `confirmation.confirm(engine, run_id, by, shown)` takes one run and a name.
- A source scan checks that the command line's `confirm` is the only caller in the package, and that `confirmation.py` holds the only insert.

**The label once confirmed** (owner, question 2):
- A Planner reading: "the Planner's reading of the claim; not verified by code; confirmed by `<name>` on `<UTC time>`".
- Another reading (a narrower or fixed plan): its label gains "; confirmed by `<name>` on `<UTC time>`".
- It is applied in `reading.stored`, so `show` and code's statement say the same.

## Every step from stored rows

`prepare` and `proceed` decide each step from what is stored, never from memory:
- A done Planner stage is used; the Planner is not asked again.
- A stored narrowing decision is used.
- After the lock:
  - records are stored only for sources still pending;
  - Checks, Inclusion (by its stage row), the freeze and the statistics run only if their stored result is absent;
  - a Critic or Analyst stage that exists is never started again.
- A completed partly-sufficient original without its narrower question gets it, and never a second one; a draft left by a stop is submitted.

**A run on its first pass takes exactly the steps it took before.** The reference comparison below shows it.

What 9a does **not** do: close a stage or a call left open by a crash, or repeat the Planner once. That is 9b's recovery (Q3).

## Cancel, dispatch again, the ceiling, the dispatch refusals

**Cancel** (`queries.cancel`, `cancel <run> --by`) works only on a queued or waiting run. The run fails with:
- "cancelled: cancelled by `<name>` before it started", or
- "cancelled: cancelled by `<name>` while waiting for confirmation of the question as tested".

A started or ended run is refused (`not_cancellable`).

**Dispatch again** (`queries.dispatch_again`, `dispatch Q-… --again`):
- a new queued run of the query's dispatched version, with the latest run's fixed-plan flag and test mark;
- a ceiling only as given now; *corrected (fix round 1, owner):* none given stores the per-run cap;
- refused, with "another run of this query is queued, waiting or running", while any run of the query is open.

**The ceiling** (`--ceiling`) is stored on the run at dispatch. `spend.reserve` applies the lower of the stored ceiling and any ceiling the caller gives, so it holds after a crash or a restart.

**Dispatch refusals:**
- At the monthly cap: "this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, or until the owner raises the cap" (the owner's words). It counts the month's calls as the cap does.
- For constructed test data: "`<source>` is constructed test data; dispatch it only as a marked test run".

## The command line

- **`run`, `dispatch`:** on the Planner or narrower path, after the claim and question-as-tested line, they print `show`'s output with `waiting_for` and `next` (`hypocurate confirm <run> --by "<name>"`). The exit code is 0.
- **`confirm <run> --by NAME`** (*corrected, finding 4:* no `--ceiling`)**:** prints what is confirmed, records it, runs the rest in the guarded process, and prints `show`'s output.
- **`cancel <run> --by NAME`.**
- **`dispatch Q-… --again [--ceiling]`.**
- **`show`** gains `waiting_for`, but only for a waiting run, so every other run's output is as before.

## Reference comparison with `main` (milestone a0)

Before any change, two sets of dumps were taken from `main`'s code:
- the reference runs of `test_reference_numbers.py`;
- whole orchestrator runs, without ids and times: the fixed-plan run, a Planner run (FCC), the BCC claim, and the partly-sufficient original with its narrower question.

Every table of each run was dumped: run, plan, tags, snapshot, sources, eligibility rows, sets, results, calibration, flags, stage results, model calls, invocations, records and the narrower question, plus `show`'s output. A second dump of `main` was byte-identical, so the dumps are deterministic. The same dumps on the branch (the Planner runs confirmed):

| Dump | Result |
|---|---|
| Reference runs (statistics output) | **byte-identical** |
| Fixed-plan run | only `run.spending_ceiling: null` (the new column) |
| Planner FCC, Planner BCC | the new column; and `show`'s question-as-tested label and statement line, now with "confirmed by Ada Reviewer on …" |
| Partly-sufficient original | only the new column |
| Narrower question | the new column; and the label and statement line, with "; confirmed by …" |

**No result, stage output, record, model call, plan, fingerprint or decision changed.** The comparison script and its output are in the packet.

## Tests

**The whole suite passes:** 1,977 tests (up from 1,847 on `main`), both locally and in the test image rebuilt on the same code (packet, section 9).

**The images were rebuilt on the final code.** The package's SHA-256 over every file is the same in the repository, the runtime image and the test image. The test image's `tests/` is identical to the repository's, and the runtime image holds no `tests/` or `docs/`. The runtime image's guard checks pass with its own package. The build cache is pruned after the rebuild (never the volumes).

**Mutation checks** were run in a scratch copy of the package with `PYTHONPATH`, one fault at a time, each against the named test files (packet, section 7). There were 39 deliberate faults:
- **0007's rules:** d01–d09;
- **the confirmation and the label:** c01–c07;
- **the orchestrator:** o01–o12;
- **queries and spend:** q01–q07, s01–s02;
- **the command line:** l01–l02.

**Three survived the first run**, and a test was added for each:
- **c03** (`confirm` accepting a running run): the database refused it anyway, but no test reached code's own check.
- **c06** (the cost shown as $0): no assertion on the figure.
- **o04** (code's check that the plan locked is the confirmed one, removed): the database backstop refused the lock instead.

**The o04 test also found a defect.** `Refused("lock_rules", "not_confirmed")` had no fixed text in `writes.CODES`, so code's own check raised `KeyError` instead of failing the run with a stated reason. The code is added (commit `97bffda`). All 39 were re-run on the final tests, with a control run (results in the packet).

**New test files (and the counts before the code):**
- `test_migrations_step9a.py` (53): 49 failed on `main`'s package. The 4 that passed: two guards by design (a fixed-plan run, and a run with no Planner stage, lock without a confirmation); a queued run cannot wait (0001 already refuses it); and up/down/up, which has nothing above 0006 to round-trip on `main`.
- `test_queries_step9a.py` (28): 27 failed. The one that passed is a guard: a constructed source not chosen does not refuse dispatch.
- `test_confirmation.py` (23), `test_resume_step9a.py` (14), `test_cli_step9a.py` (9): fail on `main`'s package by import (no `confirmation` module).

**Tests changed, and why.** None was removed or skipped; none was weakened.

| Test or helper | Change | Reason |
|---|---|---|
| `model_builder.World.confirm_rules` (new helper) | Waiting, a confirmation of the given fingerprint, then running | Q4 |
| `access_world.lock`, `access_world.build` (the earlier run) | Confirm the narrower question's run before its lock | 0007: a narrower question's plan needs a confirmation (Q4) |
| `test_access_dispatch.py::test_a_rules_lock_committed_while_a_read_waits_closes_the_planner[narrower_question]` | Confirms before the Planner's read is bound; the race is unchanged | Same |
| `test_migrations_step8b.py::test_0006_is_the_head_and_follows_0005` | **Renamed** `test_0006_follows_0005`; the head assertion moved to the 9a file | 0007 is the head |
| `test_migrations_step8b.py::test_the_downgrade_refuses_while_a_query_uses_another_option` | The revision expected after the refused downgrade is the head (0007) | Same |
| `test_migrations_step8b.py`: two narrower-plan lock tests | Confirm first | Q4 |
| `test_migrations.expected_triggers` | Adds 0007's triggers | New migration |
| `test_orchestrator.py::run` (helper) | Confirms a waiting run by a named person, then runs the rest (stages joined) | Q4 |
| `test_orchestrator.py::test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested` | **Renamed** `..._and_waits`. Asserts `prepare` leaves the run waiting, not ready; then confirms, and `proceed` completes from the rules lock | Q1 changes exactly this premise (the only assertion change besides the label below) |
| `test_statement.py::run_claim` (helper) | Confirms a waiting run | Q4 |
| `test_statement.py::test_a_planner_run_s_statement_labels_the_planner_s_reading` | The statement's label is the confirmed label; the unconfirmed label text is still pinned | Owner, question 2 |
| `test_cli_runs.py::hc_confirmed` (new helper) | `run`/`dispatch`, then `confirm` if the run waits; the same output shape, stages of both commands | Q4 |
| `test_cli_runs.py`: the four Planner and narrower tests | Use `hc_confirmed`; assertions unchanged | Q4 |
| `test_assumptions.py::test_the_step_6_decisions_carry_the_owners_wording` | `constructed_test_runs`'s decision date is 2026-10-08, its 2026-10-05 wording in history | Reworded for Q6 |

## Assumptions register

**143 entries:** 142 in force and 1 direction approved; 141 applied "yes" and 2 "partly" (`constructed_test_runs`, `question_as_tested`, whose website button is step 10).

- **New:** `rules_confirmation`, `resumable_run`, `run_cancel`, `dispatch_again`, `dispatch_refusals`.
- **Reworded** (earlier wording in history): `spending_caps`, `question_as_tested`, `run_order_and_failures`, `constructed_test_runs`.
- The wording of the new entries is Claude Code's draft, for the owner's review.

## What 9a does not do or claim

- **No queue or worker yet.** `run`, `dispatch` and `confirm` work the run inline, as before (9b).
- **No recovery after a crash.** A stage or call left open by a crash, or by a recording failure, stays open until 9b.
- **Confirmation shows; it does not verify.** The question as tested is still the Planner's reading. A person's confirmation shows that a named person saw it; it does not show the reading is right.
- **The database scoping** described above.
- **Live database:** after this merges, the previous release's Planner runs would be refused at the lock. The live database has no source registered, so it can have no such run; the owner checks before the deploy.

## Open items

1. The local development database was backed up (`pg_dump`, kept in the session's work folder) and migrated to 0007 on 2026-10-08 (owner's default). Its 12 runs, 21 model calls and $1.027756 are kept; `show` prints them with the new code, and `cancel` refuses a completed one.
2. Step 10: the Confirm and Cancel buttons, the queue screen, the waiting stage state.
3. Step 11: how the evaluation runs are confirmed (owner).

## PRD corrections and clarifications (for the next PRD update)

1. **PRD 3 step 4, 5.6, 9.4:** a run whose plan comes from a model's answer waits before the rules lock for a named person's confirmation of the question as tested (new status `waiting`). The dataset freeze stays automatic.
2. **PRD 7:** `rules_confirmation`; `run.spending_ceiling`; status `waiting`.
3. **PRD 8:** dispatch refuses at the monthly cap and for unmarked constructed test data. A failed run is dispatched again as a new run (`dispatch --again`). Cancel works on a queued or waiting run only.
4. **PRD 12:** `confirm`, `cancel`, `dispatch --again`; `run` stops at the wait on the Planner path.

## Questions for the reviewer

1. Can a plan from the Planner's answer, or for a narrower question, be locked without a named person's confirmation of exactly that plan, through any path in our code? Is the database scoping (a Planner stage or a narrower link) sound for our own code, as stated?
2. Can a confirmation be recorded for other source versions than those the narrowing counted, for content other than what was shown, or for more than one run at once?
3. Does taking each step from stored rows ever repeat a stored step, skip one, or change a result on a first pass?
4. Do the stored ceiling and the dispatch refusals hold as stated? Can a cancel race a start?
5. Migration 0007: is `hc_run_update` 0001's exactly, apart from the status changes? Do the new rules hold against direct SQL, and is the downgrade exact?
6. Is any claim in this summary, the code or the register stronger than the code supports?
