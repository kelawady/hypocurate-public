# Build step 9a — review packet

Date: 2026-10-08. Branch: `step-09a-waiting`, from `main` at `ed46b48`. Head when generated: `774c5e0`. Generated from
the files on disk by a script (`~/hc-work/step09a/packet.py`, quoted in section 10), so every diff and output below is
quoted exactly.

## How to use this packet

Step 9a builds the wait at the rules lock and its confirmation by a named person, cancel, dispatch again, the spending
ceiling stored on the run, two dispatch refusals, and an orchestrator that takes every step from stored rows (the
queue, the worker and recovery are step 9b). It holds safeguard changes (listed at the top of the summary), so please
review against `docs/reviews/checklist.md` and answer the questions at the end of the summary. Sections: 1 the summary;
2 the code diff; 3 the new test files; 4 the changed tests; 5 the register; 6 the reference comparison with `main`;
7 the mutation checks; 8 new tests on `main`'s code; 9 the suite and the images; 10 the plan file and the scripts.

## 1. The summary

# Build step 9a — summary for review

Date: 2026-10-08. Branch: `step-09a-waiting` (from `main` at `ed46b48`). **Status: built, whole suite passing; pushed for the second-model review; not merged** (the owner's end point for 9a: "full suite, summary, packet, push the branch, stop. No merge").

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
| `run.spending_ceiling`: positive and finite, set at dispatch, never changed. | CHECK, `hc_run_waiting` |
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
- The database refuses a confirmation whose narrowing counted other versions.

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
- a ceiling only as given now;
- refused, with "another run of this query is queued, waiting or running", while any run of the query is open.

**The ceiling** (`--ceiling`) is stored on the run at dispatch. `spend.reserve` applies the lower of the stored ceiling and any ceiling the caller gives, so it holds after a crash or a restart.

**Dispatch refusals:**
- At the monthly cap: "this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, or until the owner raises the cap" (the owner's words). It counts the month's calls as the cap does.
- For constructed test data: "`<source>` is constructed test data; dispatch it only as a marked test run".

## The command line

- **`run`, `dispatch`:** on the Planner or narrower path, after the claim and question-as-tested line, they print `show`'s output with `waiting_for` and `next` (`hypocurate confirm <run> --by "<name>"`). The exit code is 0.
- **`confirm <run> --by NAME [--ceiling]`:** prints what is confirmed, records it, runs the rest in the guarded process, and prints `show`'s output.
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

## 2. Code diff (`ed46b48..HEAD`, the package with migration 0007; the register is in section 5)

```diff
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 879f1c6..d8f4542 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -51,8 +51,18 @@ def main(argv: list[str] | None = None) -> int:
     run.add_argument("--ceiling", help="the most this run's model calls may cost, in USD (refused above it)")
     dispatch = sub.add_parser("dispatch", help="dispatch a submitted query by its number and run it (may cost money)")
     dispatch.add_argument("number", help="the query number, e.g. Q-0002")
-    dispatch.add_argument("--by", required=True, help="the name of the person confirming the domain")
+    dispatch.add_argument("--by", help="the name of the person confirming the domain (not with --again)")
     dispatch.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
+    dispatch.add_argument("--again", action="store_true",
+                          help="a new run of a query whose earlier run ended (refused while another run is open)")
+    confirm = sub.add_parser("confirm", help="show a waiting run's question as tested; a named person confirms it, "
+                                             "and the run goes on (may cost money)")
+    confirm.add_argument("run", type=int)
+    confirm.add_argument("--by", required=True, help="the name of the person confirming")
+    confirm.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
+    cancel = sub.add_parser("cancel", help="cancel a queued or waiting run")
+    cancel.add_argument("run", type=int)
+    cancel.add_argument("--by", required=True, help="the name of the person cancelling")
     show = sub.add_parser("show", help="print a run's outcome and summary")
     show.add_argument("run", type=int)
     args = parser.parse_args(argv)
@@ -66,7 +76,7 @@ def main(argv: list[str] | None = None) -> int:
         reachable = database_reachable(engine)
         print("database reachable" if reachable else "database NOT reachable")
         return 0 if reachable else 1
-    if args.command in ("run", "dispatch", "show"):
+    if args.command in ("run", "dispatch", "show", "confirm", "cancel"):
         from hypocurate.cli_runs import command
         return command(args, engine)
     return _sources(args, engine)
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index e887787..885c2a3 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -1,4 +1,5 @@
-"""The command line's `run`, `dispatch` and `show` (PRD Section 12; build step 8b).
+"""The command line's `run`, `dispatch` and `show` (PRD Section 12; build step 8b), and `confirm` and `cancel`
+(step 9a).
 
 `run` creates the query, submits it, records the named person's domain confirmation (A9), dispatches it and
 runs it in the guarded process (`access.guarded.run_guarded`, with the run's audit log for the guard's
@@ -8,6 +9,14 @@ database holds for a run: status, outcome and wordings, the pooled result unless
 results, the minimums, the kind of nothing found, the Analyst's explanation (or that it is unavailable),
 the narrower question and the run's tokens and cost. Errors print fixed codes and reasons; the guarded
 child's error text is never printed (it may quote anything).
+
+Step 9a (owner's approval of the step 9 plan, 2026-10-08; R1, R2, R3): a run whose plan comes from a model's answer
+(the Planner's, or a narrower question's) stops before its rules lock and waits for a named person: `run` and
+`dispatch` then print `show`'s output with what the run waits for and the command to confirm it. `confirm <run>
+--by NAME` prints what the person confirms (`confirmation.render`) before anything is recorded, records the
+confirmation with exactly that text, and runs the rest, printing `show`'s output. One run per command, never in
+bulk. `cancel <run> --by NAME` cancels a queued or waiting run. `dispatch Q-… --again` dispatches a new run of a
+query whose earlier run ended. `--ceiling` is stored on the run at dispatch (R5).
 """
 from __future__ import annotations
 
@@ -30,19 +39,30 @@ def command(args, engine: Engine) -> int:
                 return 1
             print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
             return 0
+        if args.command == "cancel":
+            reason = queries.cancel(engine, args.run, by=args.by)
+            print(json.dumps({"run": args.run, "status": "failed", "failure": reason}, ensure_ascii=False))
+            return 0
         ceiling = _ceiling(args.ceiling)
+        if args.command == "confirm":
+            return _confirm(engine, args.run, args.by, ceiling)
         if args.command == "run":
             q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
                                domain=args.domain, sufficiency=args.sufficiency)
             queries.submit(engine, q.version_id)
             queries.confirm_domain(engine, q.version_id, by=args.by)
             run_id = queries.dispatch(engine, q.version_id, fixed_plan=args.fixed_plan,
-                                      constructed_test_data=args.test_data)
+                                      constructed_test_data=args.test_data, ceiling=ceiling)
             number = q.number
+        elif args.again:
+            run_id, number = queries.dispatch_again(engine, args.number, ceiling=ceiling), args.number
         else:
+            if args.by is None:
+                raise ValueError("--by names the person confirming the domain")
             vid = queries.submitted_version(engine, args.number)
             queries.confirm_domain(engine, vid, by=args.by)
-            run_id = queries.dispatch(engine, vid)  # a narrower question's plan follows from its link (finding 1)
+            # A narrower question's plan follows from its link (finding 1).
+            run_id = queries.dispatch(engine, vid, ceiling=ceiling)
             number = args.number
     except queries.QueryRefused as refused:
         print(f"error: {refused.code}: {refused.reason}", file=sys.stderr)
@@ -71,8 +91,8 @@ def _ceiling(value: str | None) -> Decimal | None:
 
 
 def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
-    """Two guarded calls: up to the rules lock, then on to the end. Between them the original claim and the
-    question as tested are printed (owner's decision B), before the run goes on."""
+    """Two guarded calls: up to the rules lock (or the wait for a person, step 9a), then on to the end. Between them
+    the original claim and the question as tested are printed (owner's decision B), before the run goes on."""
     from hypocurate.access.guarded import GuardedRunError, run_guarded
     payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None}
     try:
@@ -88,13 +108,44 @@ def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
         print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
               f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
         return 1
+    return _print_shown(engine, run_id, report)
+
+
+def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
     # One presentation everywhere (owner, after the re-check): the same output as `show` (code's statement first, then
     # the Analyst's text under its label), with the stages run and the run's failure, if any. The orchestration
-    # report's own explanation is never printed.
+    # report's own explanation is never printed. Step 9a: a waiting run's output says what it waits for and how to
+    # confirm it.
     shown = show(engine, run_id)
-    print(json.dumps({**shown, "stages": report.get("stages"), "run_failure": report.get("failure")},
-                     indent=2, ensure_ascii=False, default=str))
-    return 0 if shown["status"] in ("completed", "failed") else 1
+    out = {**shown, "stages": report.get("stages"), "run_failure": report.get("failure")}
+    if shown["status"] == "waiting":
+        out["next"] = f'hypocurate confirm {run_id} --by "<name>"'
+    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
+    return 0 if shown["status"] in ("completed", "failed", "waiting") else 1
+
+
+def _confirm(engine: Engine, run_id: int, by: str, ceiling: Decimal | None) -> int:
+    """Prints what is confirmed, records one named person's confirmation of exactly that, then runs the rest."""
+    from hypocurate.access.guarded import GuardedRunError, run_guarded
+    from hypocurate.pipeline import confirmation
+    with engine.connect() as conn:
+        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
+    if status is None:
+        raise queries.QueryRefused("unknown_run", f"no run {run_id}")
+    if status != "waiting":
+        raise queries.QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
+    content, words = confirmation.show(engine, run_id)
+    print(words, flush=True)
+    confirmation.confirm(engine, run_id, by, shown=content)
+    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None, "phase": "proceed"}
+    try:
+        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", payload, timeout=3600,
+                             audit=(engine, run_id))
+    except GuardedRunError:
+        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
+              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
+        return 1
+    return _print_shown(engine, run_id, report)
 
 
 def _claim(engine: Engine, run_id: int) -> str:
@@ -182,4 +233,11 @@ def show(engine: Engine, run_id: int) -> dict | None:
         "flags": critic_flags(engine, run_id),
         "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
         "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
+        # Step 9a: only for a waiting run, so every other run's output is as before.
+        **({"waiting_for": _waiting_for()} if run.status == "waiting" else {}),
     }
+
+
+def _waiting_for() -> str:
+    from hypocurate.pipeline.confirmation import WAITING_FOR
+    return WAITING_FOR
diff --git a/hypocurate/db/migrations/versions/0007_rules_confirmation.py b/hypocurate/db/migrations/versions/0007_rules_confirmation.py
new file mode 100644
index 0000000..19b79ea
--- /dev/null
+++ b/hypocurate/db/migrations/versions/0007_rules_confirmation.py
@@ -0,0 +1,320 @@
+"""The run waits at the rules lock for a named person; the spending ceiling on the run (build step 9a).
+
+Revision ID: 0007
+Revises: 0006
+Create Date: 2026-10-08
+
+Approved by the owner on 2026-10-08 (step 9 plan: Q1, Q5, R5 and addition A1), subject to the second-model
+review before merging.
+
+run:
+- a new status, 'waiting': a run whose plan comes from a model's answer stops before its rules lock until a
+  named person confirms the question as tested (Q1). It waits only then: from 'running', with no plan, no
+  stage running and no model call open, and either a Planner stage and code's latest narrowing decision to
+  proceed, or as a narrower question's run (Q5; a fixed-plan run of an ordinary question never waits). It
+  waits once; it goes on to 'running' only with a confirmation; it can fail (a cancel) and never completes.
+  Every rule of 0001 that writes to a run requires 'running', so nothing is written to a waiting run.
+- 0001's `hc_run_update` is replaced, with its body unchanged except the list of status changes, which gains
+  running -> waiting, waiting -> waiting, waiting -> running and waiting -> failed. It is the only earlier
+  function replaced; the downgrade restores 0001's text exactly.
+- `spending_ceiling` (R5): a lower ceiling than the per-run cap, stored at dispatch, positive and finite,
+  never changed (it joins what a run records at dispatch).
+rules_confirmation (Q1, A1, A2), append-only, one per run:
+- only for a waiting run; by a named person (1-200 characters); at the database's time;
+- the fingerprint of the plan that will be locked, in the plan fingerprint format;
+- a Planner run's confirmation names the run's done Planner stage and its latest narrowing decision (to
+  proceed); a narrower question's names neither;
+- the source versions the narrowing counts were taken on (the run's own decision, or the original's for a
+  narrower question) are exactly the run's versions;
+- the content shown (a JSON object) and the exact text shown (not empty).
+plan:
+- a plan for a run with a Planner stage (any attempt) or of a narrower question is locked only with that run's
+  confirmation of exactly its fingerprint. A run with no Planner stage and no narrower link (a fixed-plan run,
+  and the step 6-8 test worlds that lock a plan directly) is unaffected: the orchestrator builds a Planner plan
+  only from a stored Planner stage (scoping stated in the step 9a summary).
+hypothesis:
+- at most one narrower question per original run (a unique index), so a repeated completion step can never
+  create a second one.
+
+Works with the previous release's code: it never sets 'waiting' and writes no confirmation or ceiling. Its
+Planner runs and narrower questions are refused at the lock (deliberately: no plan from a model's answer is
+locked without a person); its fixed-plan runs are unaffected. The owner checks the live database for runs in
+progress before the deploy (R7).
+
+Downgrade refuses while a run is waiting, a confirmation exists or a ceiling is set, then drops what 0007
+added and restores 0001's function and status rule.
+
+Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it
+keeps working with the previous release's code; and it has a downgrade.
+"""
+from alembic import op
+import sqlalchemy as sa
+from sqlalchemy.dialects import postgresql
+
+revision = '0007'
+down_revision = '0006'
+branch_labels = None
+depends_on = None
+
+STATUSES_0001 = ('queued', 'running', 'completed', 'failed')
+STATUSES_0007 = ('queued', 'running', 'waiting', 'completed', 'failed')
+CONFIRMED_BY_MAX = 200
+
+TRANSITIONS_0001 = """(('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
+                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))"""
+TRANSITIONS_0007 = """(('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
+                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'),
+                                             ('running', 'waiting'), ('waiting', 'waiting'), ('waiting', 'running'),
+                                             ('waiting', 'failed'))"""
+
+# 0001's function, copied verbatim (tests/test_migrations_step9a.py checks it against 0001's own text).
+RUN_UPDATE_0001 = """
+    CREATE OR REPLACE FUNCTION hc_run_update() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE p plan; pooled analysis_result; n_pooled int;
+    BEGIN
+        IF OLD.status IN ('completed', 'failed') THEN
+            PERFORM hc_reject('a ' || OLD.status || ' run is final');
+        END IF;
+        IF NEW.hypothesis_version_id <> OLD.hypothesis_version_id OR NEW.agent_mode <> OLD.agent_mode
+           OR NEW.fixed_plan <> OLD.fixed_plan OR NEW.experiment_flags <> OLD.experiment_flags
+           OR NEW.queued_at <> OLD.queued_at THEN
+            PERFORM hc_reject('what a run records at dispatch cannot change');
+        END IF;
+        IF NOT ((OLD.status, NEW.status) IN (('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
+                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))) THEN
+            PERFORM hc_reject('run status cannot go from ' || OLD.status || ' to ' || NEW.status);
+        END IF;
+        IF OLD.status = 'queued' AND NEW.status = 'running' AND EXISTS (
+            SELECT 1 FROM source s WHERE s.created_at <= NEW.queued_at
+              AND NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.id AND rs.source_id = s.id)) THEN
+            PERFORM hc_reject('a run starts only with a run_source row for every source registered at dispatch');
+        END IF;
+        IF NEW.status IN ('completed', 'failed') THEN
+            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
+               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
+                PERFORM hc_reject('a run ends only when no stage is running and no model call is open');
+            END IF;
+        END IF;
+        IF NEW.status = 'completed' AND NEW.outcome = 'sufficient' THEN
+            SELECT * INTO p FROM plan WHERE run_id = NEW.id;
+            IF NOT FOUND THEN
+                PERFORM hc_reject('a sufficient outcome needs a locked plan');
+            END IF;
+            SELECT count(*) INTO n_pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
+            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
+            IF n_pooled <> 1 OR pooled.check2_passed IS NOT TRUE THEN
+                PERFORM hc_reject('a sufficient outcome needs exactly one pooled result that passed both validity checks');
+            END IF;
+            IF p.sufficiency_option = 'fixed_minimum' AND NOT pooled.minimums_met THEN
+                PERFORM hc_reject('under fixed_minimum, a sufficient outcome needs the minimums met');
+            END IF;
+            IF NEW.exploratory <> (p.sufficiency_option = 'use_available' AND NOT pooled.minimums_met) THEN
+                PERFORM hc_reject('exploratory must equal: use_available and the minimums not met');
+            END IF;
+        END IF;
+        RETURN NEW;
+    END $$
+    """
+RUN_UPDATE_0007 = RUN_UPDATE_0001.replace(TRANSITIONS_0001, TRANSITIONS_0007)
+assert RUN_UPDATE_0007 != RUN_UPDATE_0001
+
+# Shared by three functions: does the run's plan come from a model's answer (a Planner stage, any attempt), or is
+# it a narrower question's run? Both need a person's confirmation before the lock.
+NEEDS_CONFIRMATION = """(EXISTS (SELECT 1 FROM stage_result WHERE run_id = {run} AND stage = 'planner')
+            OR EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
+                       JOIN hypothesis h ON h.id = hv.hypothesis_id
+                       WHERE r.id = {run} AND h.narrower_of_run_id IS NOT NULL))"""
+
+FUNCTIONS = [
+    # Waiting (Q1, Q5) and the ceiling recorded at dispatch (R5). (0001's hc_run_update, which fires first, holds
+    # the run's row and has checked the status change itself.)
+    f"""
+    CREATE FUNCTION hc_run_waiting() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE latest jsonb;
+    BEGIN
+        IF NEW.spending_ceiling IS DISTINCT FROM OLD.spending_ceiling THEN
+            PERFORM hc_reject('what a run records at dispatch cannot change');
+        END IF;
+        IF OLD.status = 'running' AND NEW.status = 'waiting' THEN
+            IF NOT {NEEDS_CONFIRMATION.format(run='NEW.id')} THEN
+                PERFORM hc_reject('only a run whose plan comes from the Planner or a narrower question waits');
+            END IF;
+            IF EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = NEW.id) THEN
+                PERFORM hc_reject('a run waits once: it is already confirmed');
+            END IF;
+            IF EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id) THEN
+                PERFORM hc_reject('a run waits only before its rules lock');
+            END IF;
+            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
+               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
+                PERFORM hc_reject('a run waits only when no stage is running and no model call is open');
+            END IF;
+            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'planner') THEN
+                SELECT CASE WHEN status = 'done' THEN output END INTO latest FROM stage_result
+                WHERE run_id = NEW.id AND stage = 'narrowing' ORDER BY id DESC LIMIT 1;
+                IF latest IS NULL OR latest->>'result' IS DISTINCT FROM 'proceed' THEN
+                    PERFORM hc_reject('a Planner run waits only after code''s narrowing decision to proceed');
+                END IF;
+            END IF;
+        END IF;
+        IF OLD.status = 'waiting' AND NEW.status = 'running'
+           AND NOT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = NEW.id) THEN
+            PERFORM hc_reject('a waiting run goes on only after a person confirms the question as tested');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # The confirmation (Q1, A1): of a waiting run, by a named person, at the database's time, naming the stages it
+    # rests on, on the source versions the narrowing counts were taken on.
+    """
+    CREATE FUNCTION hc_rules_confirmation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE original bigint; planner_run boolean; decision jsonb; stored text[]; current text[];
+    BEGIN
+        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'waiting' THEN
+            PERFORM hc_reject('only a run waiting for confirmation is confirmed');
+        END IF;
+        NEW.confirmed_at := now();
+        SELECT h.narrower_of_run_id INTO original
+        FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
+        JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = NEW.run_id;
+        planner_run := EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'planner');
+        IF original IS NOT NULL AND NOT planner_run THEN
+            IF NEW.planner_stage_result_id IS NOT NULL OR NEW.narrowing_stage_result_id IS NOT NULL THEN
+                PERFORM hc_reject('a narrower question''s confirmation names no Planner or narrowing stage of its own');
+            END IF;
+            SELECT output INTO decision FROM stage_result
+            WHERE run_id = original AND stage = 'narrowing' AND status = 'done'
+              AND output->>'result' = 'partly_sufficient'
+            ORDER BY id DESC LIMIT 1;
+        ELSE
+            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.planner_stage_result_id AND run_id = NEW.run_id
+                             AND stage = 'planner' AND status = 'done')
+               OR NEW.narrowing_stage_result_id IS DISTINCT FROM (
+                    SELECT id FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing'
+                    ORDER BY id DESC LIMIT 1)
+               OR NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.narrowing_stage_result_id
+                                AND status = 'done' AND output->>'result' = 'proceed') THEN
+                PERFORM hc_reject('a Planner run''s confirmation names the run''s done Planner stage and its latest '
+                                  'narrowing decision (to proceed)');
+            END IF;
+            SELECT output INTO decision FROM stage_result WHERE id = NEW.narrowing_stage_result_id;
+        END IF;
+        SELECT coalesce(array_agg((e->>'source') || ' ' || (e->>'version_fingerprint')
+                                  ORDER BY (e->>'source') || ' ' || (e->>'version_fingerprint')), '{}')
+        INTO stored
+        FROM jsonb_array_elements(CASE WHEN jsonb_typeof(decision->'sources') = 'array'
+                                       THEN decision->'sources' ELSE '[]'::jsonb END) e;
+        SELECT coalesce(array_agg(s.key || ' ' || sv.fingerprint ORDER BY s.key || ' ' || sv.fingerprint), '{}')
+        INTO current
+        FROM run_source rs JOIN source s ON s.id = rs.source_id
+        JOIN source_version sv ON sv.id = rs.source_version_id
+        WHERE rs.run_id = NEW.run_id;
+        IF decision IS NULL OR stored IS DISTINCT FROM current THEN
+            PERFORM hc_reject('a confirmation is only for the run''s own source versions, which must be the source '
+                              'versions the narrowing counts were taken on');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # The plan backstop (Q1): a plan from a model's answer is locked only as confirmed by a person.
+    # (0001's hc_plan_insert, which fires first, has locked the run.)
+    f"""
+    CREATE FUNCTION hc_plan_rules_confirmed() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF {NEEDS_CONFIRMATION.format(run='NEW.run_id')}
+           AND NOT EXISTS (SELECT 1 FROM rules_confirmation
+                           WHERE run_id = NEW.run_id AND plan_fingerprint = NEW.fingerprint) THEN
+            PERFORM hc_reject('a plan from the Planner or for a narrower question needs a person''s confirmation of '
+                              'exactly this plan (its fingerprint) before the rules lock');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+]
+FUNCTION_NAMES = ["hc_run_waiting()", "hc_rules_confirmation_insert()", "hc_plan_rules_confirmed()"]
+
+APPEND_ONLY = ["rules_confirmation"]
+# (table, event, trigger, function). Each trigger's name sorts after the earlier triggers on its table.
+CHECKED = [
+    ("run", "UPDATE", "hc_run_update_waiting", "hc_run_waiting"),
+    ("rules_confirmation", "INSERT", "hc_rules_confirmation_insert", "hc_rules_confirmation_insert"),
+    ("plan", "INSERT", "hc_plan_insert_rules_confirmed", "hc_plan_rules_confirmed"),
+]
+TRIGGERS = (
+    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
+     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
+    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
+       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
+    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
+       for table, event, t, f in CHECKED]
+)
+
+
+def _in(column: str, values) -> str:
+    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"
+
+
+def upgrade() -> None:
+    op.drop_constraint(op.f('ck_run_status'), 'run', type_='check')
+    op.create_check_constraint(op.f('ck_run_status'), 'run', _in('status', STATUSES_0007))
+    op.execute(RUN_UPDATE_0007)
+    op.add_column('run', sa.Column('spending_ceiling', sa.Numeric(), nullable=True))
+    op.create_check_constraint(op.f('ck_run_spending_ceiling'), 'run',
+                               "spending_ceiling IS NULL OR (spending_ceiling > 0 AND spending_ceiling < 'Infinity')")
+    op.create_table(
+        'rules_confirmation',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('run_id', sa.BigInteger(), nullable=False),
+        sa.Column('confirmed_by', sa.Text(), nullable=False),
+        sa.Column('confirmed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.Column('plan_fingerprint', sa.Text(), nullable=False),
+        sa.Column('planner_stage_result_id', sa.BigInteger(), nullable=True),
+        sa.Column('narrowing_stage_result_id', sa.BigInteger(), nullable=True),
+        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
+        sa.Column('shown', sa.Text(), nullable=False),
+        sa.CheckConstraint(f"length(btrim(confirmed_by)) BETWEEN 1 AND {CONFIRMED_BY_MAX}",
+                           name=op.f('ck_rules_confirmation_named')),
+        sa.CheckConstraint("plan_fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_rules_confirmation_fingerprint_format')),
+        sa.CheckConstraint("jsonb_typeof(content) = 'object' AND length(shown) > 0",
+                           name=op.f('ck_rules_confirmation_content_and_text')),
+        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_rules_confirmation_run_id')),
+        sa.ForeignKeyConstraint(['planner_stage_result_id'], ['stage_result.id'],
+                                name=op.f('fk_rules_confirmation_planner_stage_result_id')),
+        sa.ForeignKeyConstraint(['narrowing_stage_result_id'], ['stage_result.id'],
+                                name=op.f('fk_rules_confirmation_narrowing_stage_result_id')),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_rules_confirmation')),
+        sa.UniqueConstraint('run_id', name=op.f('uq_rules_confirmation_run_id')),
+    )
+    op.create_index('uq_hypothesis_narrower_of_run_id', 'hypothesis', ['narrower_of_run_id'], unique=True,
+                    postgresql_where=sa.text('narrower_of_run_id IS NOT NULL'))
+    for f in FUNCTIONS:
+        op.execute(f)
+    for t in TRIGGERS:
+        op.execute(t)
+
+
+IN_USE = """
+    DO $$
+    BEGIN
+        IF EXISTS (SELECT 1 FROM run WHERE status = 'waiting' OR spending_ceiling IS NOT NULL)
+           OR EXISTS (SELECT 1 FROM rules_confirmation) THEN
+            RAISE EXCEPTION 'hypocurate: migration 0007 is in use (a waiting run, a confirmation or a spending ceiling); not downgraded';
+        END IF;
+    END $$
+"""
+
+
+def downgrade() -> None:
+    op.execute(IN_USE)
+    for t in reversed(TRIGGERS):
+        name, table = t.split()[2], t.split(" ON ")[1].split()[0]
+        op.execute(f"DROP TRIGGER {name} ON {table}")
+    for f in FUNCTION_NAMES:
+        op.execute(f"DROP FUNCTION {f}")
+    op.drop_index('uq_hypothesis_narrower_of_run_id', table_name='hypothesis')
+    op.drop_table('rules_confirmation')
+    op.drop_constraint(op.f('ck_run_spending_ceiling'), 'run', type_='check')
+    op.drop_column('run', 'spending_ceiling')
+    op.execute(RUN_UPDATE_0001)
+    op.drop_constraint(op.f('ck_run_status'), 'run', type_='check')
+    op.create_check_constraint(op.f('ck_run_status'), 'run', _in('status', STATUSES_0001))
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 9d6a40d..b339ffe 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -268,6 +268,9 @@ class Hypothesis(Base):
     narrower_of_run_id: Mapped[int | None] = mapped_column(
         ForeignKey("run.id", use_alter=True))
     created_at: Mapped[datetime] = created()
+    # Step 9a (0007): at most one narrower question per original run.
+    __table_args__ = (Index("uq_hypothesis_narrower_of_run_id", "narrower_of_run_id", unique=True,
+                            postgresql_where=sql("narrower_of_run_id IS NOT NULL")),)
 
 
 VERSION_STATUSES = ("draft", "submitted", "returned", "dispatched")
@@ -322,7 +325,8 @@ class HypothesisVersionSource(Base):
 
 # --- Runs ----------------------------------------------------------------------
 
-RUN_STATUSES = ("queued", "running", "completed", "failed")
+# Step 9a (0007): 'waiting' for a named person's confirmation of the question as tested, before the rules lock.
+RUN_STATUSES = ("queued", "running", "waiting", "completed", "failed")
 OUTCOMES = ("sufficient", "partly_sufficient", "insufficient")
 VERDICTS = ("supported", "not_supported")
 
@@ -346,6 +350,8 @@ class Run(Base):
     evidence_level: Mapped[int | None] = mapped_column(SmallInteger)
     # Step 8b fix round 1 (migration 0006): the results statement's format version, recorded when the run completes.
     statement_format_version: Mapped[int | None] = mapped_column(SmallInteger)
+    # Step 9a (0007; register 'spending_caps'): a lower ceiling than the per-run cap, stored at dispatch, never changed.
+    spending_ceiling: Mapped[Decimal | None] = mapped_column(Numeric)
     failure_reason: Mapped[str | None] = mapped_column(Text)
     agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
     fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
@@ -370,6 +376,8 @@ class Run(Base):
         CheckConstraint("(evidence_level IS NOT NULL) = (status = 'completed')", name="evidence_level_iff_completed"),
         CheckConstraint("statement_format_version IS NULL OR statement_format_version >= 1",
                         name="statement_format_version"),
+        CheckConstraint("spending_ceiling IS NULL OR (spending_ceiling > 0 AND spending_ceiling < 'Infinity')",
+                        name="spending_ceiling"),
         CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
         CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
         CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
@@ -379,6 +387,30 @@ class Run(Base):
 
 
 
+CONFIRMED_BY_MAX = 200
+
+
+class RulesConfirmation(Base):
+    """Step 9a (0007; owner, Q1, A1, A2): a named person's confirmation of the question as tested, for a run waiting
+    at its rules lock: the fingerprint of the plan that will be locked, the stages it rests on, the content shown
+    and the exact text shown. One per run, at the database's time. Append-only."""
+    __tablename__ = "rules_confirmation"
+    id: Mapped[int] = pk()
+    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
+    confirmed_by: Mapped[str] = mapped_column(Text)
+    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
+    plan_fingerprint: Mapped[str] = mapped_column(Text)
+    planner_stage_result_id: Mapped[int | None] = mapped_column(ForeignKey("stage_result.id"))
+    narrowing_stage_result_id: Mapped[int | None] = mapped_column(ForeignKey("stage_result.id"))
+    content: Mapped[dict] = mapped_column(JSONB)
+    shown: Mapped[str] = mapped_column(Text)
+    __table_args__ = (
+        CheckConstraint(f"length(btrim(confirmed_by)) BETWEEN 1 AND {CONFIRMED_BY_MAX}", name="named"),
+        CheckConstraint(f"plan_fingerprint {SHA256}", name="fingerprint_format"),
+        CheckConstraint("jsonb_typeof(content) = 'object' AND length(shown) > 0", name="content_and_text"),
+    )
+
+
 class Plan(Base):
     """The locked plan (PRD 5.1, 5.6). Inserted at the rules lock, never changed.
     The columns the database checks against are explicit; the rest is `content`."""
diff --git a/hypocurate/pipeline/agents/spend.py b/hypocurate/pipeline/agents/spend.py
index b111ebf..c4789c7 100644
--- a/hypocurate/pipeline/agents/spend.py
+++ b/hypocurate/pipeline/agents/spend.py
@@ -12,7 +12,8 @@ while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
 - the calendar month (UTC, by the database's start time): at most `MONTH_CAP_USD` over every call
   recorded in this database;
 - optionally a lower ceiling the caller names (the live curation call: $0.50, owner 2026-10-06),
-  over the same run or invocation.
+  over the same run or invocation; for a run, also the ceiling stored on the run at dispatch (step 9a, R5:
+  it holds after a crash or a restart), the lower of the two.
 A refusal sends nothing, is logged in `audit_log` in its own transaction (function 'model_call',
 result 'rejected', a fixed code) and raises `SpendingRefused`.
 
@@ -66,6 +67,11 @@ _MONTH_TOTAL = ("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_ca
                 "WHERE date_trunc('month', started_at AT TIME ZONE 'UTC') = date_trunc('month', now() AT TIME ZONE 'UTC')")
 
 
+def month_total(conn: Connection) -> Decimal:
+    """This calendar month's counted spend (UTC), as the monthly cap counts it (step 9a: dispatch reads it)."""
+    return conn.execute(text(_MONTH_TOTAL)).scalar_one()
+
+
 def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, ceiling: Decimal | None = None) -> int:
     """The new call's id, recorded as started; or SpendingRefused (logged)."""
     if not isinstance(max_cost, Decimal) or not max_cost > 0:
@@ -85,17 +91,20 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
         else:
             stage = "registration"
         conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
+        limit = ceiling
         if inv.scope == "run":
             spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                       "WHERE run_id = :r"), dict(r=inv.run_id)).scalar_one()
             cap, cap_code = RUN_CAP_USD, "spending_cap_run"
+            stored = conn.execute(text("SELECT spending_ceiling FROM run WHERE id = :r"), dict(r=inv.run_id)).scalar_one()
+            limit = min(x for x in (ceiling, stored) if x is not None) if (ceiling, stored) != (None, None) else None
         else:
             spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                       "WHERE invocation_id = :i"), dict(i=invocation_id)).scalar_one()
             cap, cap_code = CURATION_CAP_USD, "spending_cap_curation"
         month = conn.execute(text(_MONTH_TOTAL)).scalar_one()
         code = (cap_code if spent + max_cost > cap else
-                "ceiling_reached" if ceiling is not None and spent + max_cost > ceiling else
+                "ceiling_reached" if limit is not None and spent + max_cost > limit else
                 "spending_cap_month" if month + max_cost > MONTH_CAP_USD else None)
         if code:
             return ("refused", code, inv, stage, {"spent": str(spent), "month": str(month)})
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
new file mode 100644
index 0000000..43c52e4
--- /dev/null
+++ b/hypocurate/pipeline/confirmation.py
@@ -0,0 +1,303 @@
+"""The confirmation of the question as tested, at the rules lock (build step 9a; owner's answers Q1, Q5 and additions
+A1, A2 of 2026-10-08; register 'rules_confirmation').
+
+A run whose plan comes from a model's answer (the Planner's, or a narrower question's, whose exclusion rules and
+outcome come from its original's Planner answer) waits before its rules lock until a named person confirms it. A
+fixed-plan run of an ordinary question (criterion 14.1a) never waits.
+
+- `plan_to_lock`: the one place that builds the plan a run will lock, from what is stored (the narrower question's
+  stored plan after its source-version check, the reference plan, or the Planner's stored answer after a narrowing
+  decision to proceed). The orchestrator locks exactly this plan, so the confirmed fingerprint is the locked one.
+- `content`: what the person is shown (A2), built by code from stored rows only: the original question, the
+  question as tested, what was narrowed and why, each scope part marked stated or assumed, the outcome, the
+  exclusion rules, the sufficiency option, the plan's fingerprint, the source versions, and the cost so far.
+  `render` turns it into the text shown. Step 10 shows the same content on the screen.
+- `source_changes`: A1. A waiting run uses exactly the sealed versions recorded at dispatch (the database refuses
+  any change to them). A confirmation is refused when a chosen source has a newer sealed version, or a source was
+  registered after dispatch: the narrowing decision would no longer describe the registered sources.
+- `confirm`: one run, one named person (no bulk or automatic confirmation in step 9). In one transaction under the
+  run's lock: the run is waiting and not yet confirmed, the sources are unchanged, and the content is what was
+  shown; then the confirmation is stored with the content and the exact text shown (the database re-checks the
+  run, the stages and the source versions, migration 0007).
+"""
+from __future__ import annotations
+
+from decimal import Decimal
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, bindparam, text
+from sqlalchemy.dialects.postgresql import JSONB
+
+from hypocurate.db.models import CONFIRMED_BY_MAX
+from hypocurate.db.retry import run_transaction
+from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline import reading
+from hypocurate.pipeline.queries import LOCK_TIMEOUT_MS, QueryRefused
+
+WAITING_FOR = "confirmation of the question as tested by a named person"
+SOURCES_CHANGED = ("sources_changed", "{changes} since this run's narrowing; cancel this run and dispatch the query "
+                                      "again")
+PART_WORDS = {"alloy_class": "alloy class", "phase_class": "phase class", "test_type": "test type",
+              "temperature_band": "temperature band"}
+
+
+class NotLockable(Exception):
+    """The stored rows give no plan to lock (a fixed failure code)."""
+
+    def __init__(self, code: str):
+        self.code = code
+        super().__init__(code)
+
+
+def _run(conn: Connection, run_id: int):
+    return conn.execute(text(
+        "SELECT r.id, r.status, r.fixed_plan, r.queued_at, r.hypothesis_version_id, hv.text, hv.sufficiency_option, "
+        "h.number, h.narrower_of_run_id FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+        "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=run_id)).one_or_none()
+
+
+def needs_confirmation(conn: Connection, run_id: int) -> bool:
+    """As the database decides it (0007): a Planner stage (any attempt), or a narrower question's run."""
+    return bool(conn.execute(text(
+        "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'planner') OR EXISTS ("
+        "SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h "
+        "ON h.id = hv.hypothesis_id WHERE r.id = :r AND h.narrower_of_run_id IS NOT NULL)"), dict(r=run_id)).scalar_one())
+
+
+def _latest(conn: Connection, run_id: int, stage: str, done: bool = True):
+    return conn.execute(text(
+        "SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = :s "
+        + ("AND status = 'done' " if done else "") + "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).one_or_none()
+
+
+def _narrower_plan(conn: Connection, run_id: int, original: int, version_id: int) -> dict:
+    """The narrower plan stored by the original's narrowing decision, on the versions its counts were taken on."""
+    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :o AND stage = 'narrowing' "
+                            "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(o=original)).scalar_one_or_none()
+    current = sorted(tuple(r) for r in conn.execute(text(
+        "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
+        "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
+    if not isinstance(out, dict) or not isinstance(out.get("narrower_plan"), dict):
+        raise NotLockable("narrower_plan_missing")
+    stored = sorted((s["source"], s["version_fingerprint"]) for s in out.get("sources") or [])
+    if stored != current:  # B1
+        raise NotLockable("narrowing_sources_changed")
+    body = out["narrower_plan"]
+    if plans.fingerprint(body) != out.get("narrower_plan_fingerprint"):
+        raise NotLockable("narrower_plan_missing")
+    return {"hypothesis_version": version_id, **body}
+
+
+def _planner_plan(conn: Connection, run_id: int, row) -> dict:
+    """The plan from the Planner's stored answer, only after a stored narrowing decision to proceed."""
+    from hypocurate.pipeline.agents import planner
+    stored, decided = _latest(conn, run_id, "planner"), _latest(conn, run_id, "narrowing")
+    if stored is None or not isinstance(stored.output, dict) or decided is None \
+            or (decided.output or {}).get("result") != "proceed":
+        raise NotLockable("stage_mismatch")
+    a = stored.output["answer"]
+    return planner.build_plan(row.hypothesis_version_id, a["claim_scope"], a["outcome"], a["exclusion_rules"],
+                              row.sufficiency_option)
+
+
+def reference_plan(row) -> dict:
+    plan = plans.reference_plan(row.hypothesis_version_id)
+    plan["sufficiency"]["option"] = row.sufficiency_option
+    return plan
+
+
+def plan_to_lock(conn: Connection, run_id: int) -> dict:
+    """The plan the run will lock, built from stored rows only, or NotLockable."""
+    row = _run(conn, run_id)
+    if row.narrower_of_run_id is not None:
+        return _narrower_plan(conn, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+    if row.fixed_plan:
+        return reference_plan(row)
+    return _planner_plan(conn, run_id, row)
+
+
+def plan_fingerprint(plan: Mapping[str, Any]) -> str:
+    """As the rules lock computes it (`checkpoints.lock_rules`)."""
+    return plans.fingerprint(plans.validate(plan))
+
+
+def source_changes(conn: Connection, run_id: int) -> list[str]:
+    """A1: each chosen source with a newer sealed version than the run's, and each source registered after
+    dispatch, in words; empty when the registered sources are as the run's narrowing saw them."""
+    changes = [f"{key} has a newer version" for (key,) in conn.execute(text(
+        "SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r "
+        "AND rs.source_version_id IS NOT NULL AND EXISTS (SELECT 1 FROM source_version sv WHERE sv.source_id = "
+        "s.id AND sv.sealed_at IS NOT NULL AND sv.id > rs.source_version_id) ORDER BY s.key"), dict(r=run_id)).all()]
+    changes += [f"{key} was registered" for (key,) in conn.execute(text(
+        "SELECT s.key FROM source s WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = :r "
+        "AND rs.source_id = s.id) ORDER BY s.key"), dict(r=run_id)).all()]
+    return changes
+
+
+def _value_words(part: str, value: Any) -> str:
+    if part == "temperature_band" and isinstance(value, Mapping):
+        return reading.band_words(value)
+    if part == "alloy_class":
+        return reading.plural(str(value))
+    return str(value)
+
+
+def _scope_parts(scope: Mapping, stated: Mapping | None) -> list[dict]:
+    return [{"part": PART_WORDS[part], "values": [_value_words(part, v) for v in scope[part]],
+             "marked": None if stated is None else (reading.STATED if stated.get(part) else reading.ASSUMED)}
+            for part in ("alloy_class", "phase_class", "test_type", "temperature_band") if part in scope]
+
+
+def _counts(parts: list | None) -> list[dict]:
+    return [{"part": PART_WORDS[x["part"]], "value": _value_words(x["part"], x["value"]), "candidate_records": x["n"]}
+            for x in parts or []]
+
+
+def _money(value) -> str:
+    return f"{Decimal(value):.6f}"
+
+
+def content(conn: Connection, run_id: int) -> dict:
+    """What the person confirms (A2), from stored rows only. JSON-safe."""
+    row = _run(conn, run_id)
+    plan = plan_to_lock(conn, run_id)
+    fp = plan_fingerprint(plan)
+    planner_stage = narrowing_stage = None
+    if row.narrower_of_run_id is not None:
+        original = conn.execute(text(
+            "SELECT h.number, hv.text FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+            "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :o"), dict(o=row.narrower_of_run_id)).one()
+        decision = _latest(conn, row.narrower_of_run_id, "narrowing").output
+        tested = reading.from_plan(plan, "narrower")
+        stated = decision.get("scope_stated")
+        narrowing = {"narrowed": True, "original_query": original.number, "original_question": original.text,
+                     "original_scope": _scope_parts(decision["claim_scope"], None),
+                     "parts_without_candidate_records": _counts([{**z, "n": 0} for z in decision["zero_parts"]]),
+                     "candidate_records": _counts(decision.get("part_counts")),
+                     "narrower_scope": _scope_parts(decision["narrower_scope"], None), "reason": decision["reason"]}
+        scope = {k: plan["scope"][k] for k in ("alloy_class", "phase_class", "test_type")}
+        scope["temperature_band"] = decision["narrower_scope"]["temperature_band"]
+    else:
+        p, n = _latest(conn, run_id, "planner"), _latest(conn, run_id, "narrowing")
+        planner_stage, narrowing_stage = p.id, n.id
+        tested = p.output["question_as_tested"]
+        stated = n.output.get("scope_stated")
+        scope = p.output["answer"]["claim_scope"]
+        narrowing = {"narrowed": False, "decision": n.output["result"], "reason": n.output["reason"],
+                     "candidate_records": _counts(n.output.get("part_counts"))}
+    sources = [dict(r._mapping) for r in conn.execute(text(
+        "SELECT s.key AS source, sv.fingerprint AS version_fingerprint, rs.search_status FROM run_source rs "
+        "JOIN source s ON s.id = rs.source_id LEFT JOIN source_version sv ON sv.id = rs.source_version_id "
+        "WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()]
+    cost = conn.execute(text("SELECT calls, cap_cost, reported_cost, unconfirmed_calls FROM model_call_totals_by_run "
+                             "WHERE run_id = :r"), dict(r=run_id)).one()
+    s = plan["sufficiency"]
+    return {
+        "run": int(row.id), "query": row.number, "original_question": row.text, "question_as_tested": dict(tested),
+        "narrowing": narrowing, "scope_parts": _scope_parts(scope, stated),
+        "outcome": plan["variables"]["outcome"]["field"].replace("_", " "),
+        "exclusion_rules": [reading.exclusion_words(r) for r in plan.get("exclusion_rules") or []],
+        "sufficiency": {"option": s["option"], "min_records": s["min_records"], "min_alloys": s["min_alloys"],
+                        "min_groups": s["min_groups"], "min_resid_df": s["min_resid_df"]},
+        "plan_fingerprint": fp,
+        "sources": [{"source": x["source"], "version_fingerprint": x["version_fingerprint"],
+                     "chosen": x["search_status"] != "not_selected"} for x in sources],
+        "cost_so_far": {"counted_usd": _money(cost.cap_cost), "reported_usd": _money(cost.reported_cost),
+                        "calls": int(cost.calls), "calls_without_reported_cost": int(cost.unconfirmed_calls)},
+        "planner_stage_result_id": planner_stage, "narrowing_stage_result_id": narrowing_stage,
+    }
+
+
+def _parts_lines(parts: list[dict]) -> list[str]:
+    return [f"  {x['part']}: {', '.join(x['values'])}" + (f" ({x['marked']})" if x["marked"] else "") for x in parts]
+
+
+def render(c: Mapping[str, Any]) -> str:
+    """The text shown before a person confirms (A2): every item of the content, in words."""
+    n = c["narrowing"]
+    lines = [f"Run {c['run']} of {c['query']} waits for {WAITING_FOR} before its rules lock.",
+             f"Original question: {c['original_question']}",
+             f"Question as tested ({c['question_as_tested']['label']}): {c['question_as_tested']['text']}"]
+    if n["narrowed"]:
+        lines.append(f"Narrowed: this is the narrower question of {n['original_query']} ({n['original_question']}).")
+        lines.append("  Why: code found no candidate record in the sources searched for "
+                     + "; ".join(f"{x['part']} {x['value']}" for x in n["parts_without_candidate_records"]) + ".")
+        lines.append("  Original scope:")
+        lines += ["  " + x for x in _parts_lines(n["original_scope"])]
+        lines.append("  Narrower scope:")
+        lines += ["  " + x for x in _parts_lines(n["narrower_scope"])]
+    else:
+        lines.append(f"Narrowed: no (code's narrowing decision: {n['decision']}; {n['reason'].replace('_', ' ')}).")
+    lines.append("  Candidate records per claim part (structure only, before any rule): "
+                 + ("; ".join(f"{x['part']} {x['value']}: {x['candidate_records']}" for x in n["candidate_records"])
+                    or "none counted"))
+    lines.append("Scope parts:")
+    lines += _parts_lines(c["scope_parts"])
+    lines.append(f"Outcome: {c['outcome']} against grain size")
+    lines.append("Exclusion rules: " + ("; ".join(c["exclusion_rules"]) if c["exclusion_rules"] else "none"))
+    s = c["sufficiency"]
+    lines.append(f"Sufficiency option: {s['option'].replace('_', ' ')} (minimums: {s['min_records']} records, "
+                 f"{s['min_alloys']} alloys with at least 2 grain sizes, {s['min_groups']} independent groups, "
+                 f"{s['min_resid_df']} residual degrees of freedom)")
+    lines.append("Sources: " + "; ".join(
+        f"{x['source']} version {x['version_fingerprint'][:12]}" if x["chosen"] else f"{x['source']} not chosen"
+        for x in c["sources"]))
+    k = c["cost_so_far"]
+    lines.append(f"Cost so far: ${k['counted_usd']} counted toward the caps (reported ${k['reported_usd']}; "
+                 f"{k['calls']} model calls, {k['calls_without_reported_cost']} without a reported cost)")
+    lines.append(f"Plan to be locked: fingerprint {c['plan_fingerprint']}")
+    return "\n".join(lines)
+
+
+def show(engine: Engine, run_id: int) -> tuple[dict, str]:
+    """The content and its text, for a waiting run (what `confirm` prints before recording anything)."""
+    with engine.connect() as conn:
+        c = content(conn, run_id)
+    return c, render(c)
+
+
+def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None) -> dict:
+    """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; the
+    confirmation is refused if it is no longer the current content. Returns the stored content and text."""
+    name = (by or "").strip()
+    if not name or len(name) > CONFIRMED_BY_MAX:
+        raise QueryRefused("name_required", f"a confirmation names the person (1 to {CONFIRMED_BY_MAX} characters)")
+
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        if status != "waiting":
+            raise QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
+        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = :r)"),
+                        dict(r=run_id)).scalar_one():
+            raise QueryRefused("already_confirmed", f"run {run_id} is already confirmed")
+        changes = source_changes(conn, run_id)
+        if changes:
+            raise QueryRefused(SOURCES_CHANGED[0], SOURCES_CHANGED[1].format(changes="; ".join(changes)))
+        try:
+            c = content(conn, run_id)
+        except NotLockable as error:
+            raise QueryRefused(error.code, "the stored rows give no plan to lock") from None
+        if shown is not None and dict(shown) != c:
+            raise QueryRefused("content_changed", "what was shown is no longer the run's current content; show it "
+                                                  "again before confirming")
+        words = render(c)
+        conn.execute(text(
+            "INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
+            "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, :c, :s)").bindparams(
+            bindparam("c", type_=JSONB)), dict(r=run_id, b=name, fp=c["plan_fingerprint"],
+                                                p=c["planner_stage_result_id"], n=c["narrowing_stage_result_id"],
+                                                c=c, s=words))
+        return {"content": c, "shown": words}
+
+    try:
+        return run_transaction(engine, body)
+    except QueryRefused:
+        raise
+    except Exception as error:  # the database's own refusal (0007), in its fixed words
+        from sqlalchemy.exc import IntegrityError
+        from hypocurate.pipeline.writes import database_message
+        if isinstance(error, IntegrityError):
+            raise QueryRefused("rejected_by_database", database_message(error)) from None
+        raise
+
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
index aab9ec5..c139a05 100644
--- a/hypocurate/pipeline/orchestrator.py
+++ b/hypocurate/pipeline/orchestrator.py
@@ -1,17 +1,31 @@
 """The orchestrator: one run, stage by stage (step 8b; PRD 3; the run order of the step 8 plan, corrected by the
-owner's answer A1; register 'run_order').
+owner's answer A1; register 'run_order'). Step 9a: the run waits at the rules lock for a named person, and every
+step is taken from what is stored, so a run can be taken up again where it stopped (register 'rules_confirmation',
+'resumable_run').
 
     Planner -> narrowing decision (code, before any lock)
       partly sufficient: Analyst (narrowing facts) -> copy_partly_sufficient -> narrower question; stop
       claim not one plan: the run fails before the lock (A11)
+      proceed: the run WAITS for a named person's confirmation of the question as tested (step 9a, Q1)
     -> rules lock -> store records -> Checks -> Critic -> Inclusion -> dataset freeze -> statistics
     -> Analyst -> completion (copy_decision)
 
-A narrower question's run bypasses the Planner (and the narrowing): it locks exactly the narrower plan its
-original's narrowing decision stored (A8), after checking that the run's source versions are those the counts
-were taken on (B1). It is recognised by the question's link to its original, never by a flag (fix round,
-finding 1); the database refuses its plan otherwise (0006). A fixed-plan run of an ordinary question uses the
-reference plan of criterion 14.1a.
+A narrower question's run bypasses the Planner (and the narrowing): after checking that its source versions are
+those its original's counts were taken on (B1), it waits for the confirmation too (step 9a, Q5), then locks exactly
+the narrower plan its original's narrowing decision stored (A8). It is recognised by the question's link to its
+original, never by a flag (fix round, finding 1). A fixed-plan run of an ordinary question uses the reference plan
+of criterion 14.1a and never waits.
+
+**The plan locked** is `confirmation.plan_to_lock`'s, the one place that builds it from stored rows; a run that
+waited locks only the plan whose fingerprint the person confirmed (code here, and the database, 0007).
+
+**Taken up again from stored rows** (step 9a): `prepare` and `proceed` decide each step from what is stored, never
+from memory. A done Planner stage is used, not repeated; a stored narrowing decision is used, not taken again; once
+the lock is written, records are stored only for sources still pending, and Checks, Inclusion, the freeze, the
+statistics and the completion run only if their stored result is absent. An agent stage that exists already (the
+Critic's, the Analyst's) is never started again here (owner, Q3: an interrupted Critic or Analyst is not repeated;
+step 9b's recovery closes such a stage and applies the rule for its role). A run on its first pass takes exactly
+the steps it took before step 9a.
 
 **Code decides everything** (CLAUDE.md, rule 1); each agent's answer is checked by code before it is used.
 **No model call runs inside a database transaction**: every step below uses its own short transactions, and
@@ -24,7 +38,7 @@ unclassified and the run goes on (no decision reads the class). Any Analyst fail
 included, leaves code's decision standing: the run completes with "explanation unavailable" (A3, B2). A
 recording or a reservation failure at any agent (`lm.RUN_STOPS`) stops the run at once: no further model request
 is made (no further Critic batch, no Analyst), nothing more is written, and the run stays running (a call whose
-recording failed stays started) for step 9's recovery; `run` reports it (fix round, finding 3).
+recording failed stays started) for step 9b's recovery; `run` reports it (fix round, finding 3).
 """
 from __future__ import annotations
 
@@ -34,9 +48,8 @@ from typing import Any, Mapping
 
 from sqlalchemy import Connection, Engine, text
 
-from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion, narrowing, queries
-from hypocurate.pipeline import reading
-from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline import analysis, checkpoints, checks, completion, confirmation, extract, inclusion
+from hypocurate.pipeline import narrowing, queries, reading
 from hypocurate.pipeline.agents import analyst, critic, planner
 from hypocurate.pipeline.agents.lm import RUN_STOPS
 from hypocurate.pipeline.writes import Refused, write
@@ -93,28 +106,22 @@ def _row(engine: Engine, run_id: int):
             "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=run_id)).one()
 
 
-def _narrower_plan(engine: Engine, run_id: int, original: int, version_id: int) -> tuple[dict | None, str | None]:
-    """The narrower plan stored by the original's narrowing decision, for this run (A8), or a failure code."""
+def _stored(engine: Engine, run_id: int, stage: str, done: bool = True):
+    """The latest stage result of `stage` (only a done one, unless `done` is false), or None."""
     with engine.connect() as conn:
-        out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :o AND stage = 'narrowing' "
-                                "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(o=original)).scalar_one_or_none()
-        current = sorted(tuple(r) for r in conn.execute(text(
-            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
-            "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
-    if not isinstance(out, dict) or not isinstance(out.get("narrower_plan"), dict):
-        return None, "narrower_plan_missing"
-    stored = sorted((s["source"], s["version_fingerprint"]) for s in out.get("sources") or [])
-    if stored != current:  # B1
-        return None, "narrowing_sources_changed"
-    body = out["narrower_plan"]
-    if plans.fingerprint(body) != out.get("narrower_plan_fingerprint"):
-        return None, "narrower_plan_missing"
-    return {"hypothesis_version": version_id, **body}, None
+        return conn.execute(text("SELECT id, status, output FROM stage_result WHERE run_id = :r AND stage = :s "
+                                 + ("AND status = 'done' " if done else "") + "ORDER BY id DESC LIMIT 1"),
+                            dict(r=run_id, s=stage)).one_or_none()
+
+
+def _exists(engine: Engine, sql: str, run_id: int) -> bool:
+    with engine.connect() as conn:
+        return bool(conn.execute(text(f"SELECT EXISTS ({sql})"), dict(r=run_id)).scalar_one())
 
 
 def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
-    """Runs the run to its end (completed or failed), or leaves it running if a call stayed open: `prepare`, then,
-    unless the run ended there, `proceed`."""
+    """Runs the run to its end (completed or failed), to its wait for a person's confirmation, or leaves it running
+    if a call stayed open: `prepare`, then, unless the run ended or waits there, `proceed`."""
     report = prepare(engine, run_id, ceiling=ceiling, client_options=client_options)
     if not report.ready:
         return report
@@ -125,27 +132,40 @@ def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[st
 
 
 def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
-    """Up to the rules lock: start; the narrower question's or the fixed plan, or the Planner and the narrowing
-    decision (the partly-sufficient path ends here). `ready` when the run goes on to `proceed`; the question as
-    tested is in the report (owner's decision B: the command line prints it before the run goes on)."""
+    """Up to the rules lock: start; the narrower question's plan check, the fixed plan, or the Planner and the
+    narrowing decision (the partly-sufficient path ends here). A run whose plan comes from a model's answer then
+    waits (step 9a). `ready` when the run goes on to `proceed` now; the question as tested is in the report (owner's
+    decision B: the command line prints it before the run goes on)."""
     report = RunReport(run_id)
     agent_kw = dict(ceiling=ceiling, client_options=client_options)
     row = _row(engine, run_id)
     if row.status == "queued":
         queries.start(engine, run_id)
+    elif row.status == "completed" and _done(engine, report).outcome == "partly_sufficient":
+        # Step 9a: an original completed as partly sufficient whose narrower question was not created (a stop between
+        # the two) gets it now; one per run (create_narrower is idempotent; the database allows one, 0007).
+        decided = _stored(engine, run_id, "narrowing")
+        report.narrower_question = queries.create_narrower(engine, run_id, decided.output["narrower_scope"]).number
+        return _done(engine, report)
+    elif row.status != "running":  # waiting for a person, or ended: nothing to prepare
+        return _done(engine, report)
     try:
         # A narrower question is recognised by its link to its original, never by the run's flag (fix round,
         # finding 1): it always locks the stored narrower plan, after the source-version check (A8, B1).
         if row.narrower_of_run_id is not None:
-            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+            plan, code = _lockable(engine, run_id)
             if code:
                 return _failed(engine, report, code)
             report.stages.append("fixed plan")
             report.question_as_tested = reading.from_plan(plan, "narrower")
-        elif row.fixed_plan:
+            return _wait(engine, report)
+        if row.fixed_plan:
             report.stages.append("fixed plan")
-            report.question_as_tested = reading.from_plan(_reference_plan(row), "fixed")
-        else:
+            report.question_as_tested = reading.from_plan(confirmation.reference_plan(row), "fixed")
+            report.ready = True
+            return _done(engine, report)
+        stored = _stored(engine, run_id, "planner")
+        if stored is None:
             result = planner.run_planner(engine, run_id, **agent_kw)
             report.stages.append("planner")
             if result.failure in RUN_STOPS:
@@ -153,95 +173,133 @@ def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mappin
             if result.failure is not None:
                 return _failed(engine, report, "spending_refused" if result.failure in SPENDING else "planner_failed",
                                result.failure)
-            report.question_as_tested = _stored_reading(engine, result.stage_id)
-            answer = result.answer
-            if not answer.domain_matches:
-                return _failed(engine, report, "domain_mismatch")
+            answer, stage_id = result.answer, result.stage_id
+        else:  # step 9a: a done Planner stage is used, never repeated
+            answer, stage_id = planner.Answer(**stored.output["answer"]), stored.id
+        report.question_as_tested = _stored_reading(engine, stage_id)
+        if not answer.domain_matches:
+            return _failed(engine, report, "domain_mismatch")
+        decided = _stored(engine, run_id, "narrowing")
+        if decided is None:
             decision = narrowing.run_narrowing(engine, run_id, answer)
             report.stages.append(f"narrowing: {decision['result']}")
-            if decision["result"] == "claim_not_one_plan":
-                return _failed(engine, report, "claim_not_one_plan", decision["reason"])
-            if decision["result"] == "partly_sufficient":
+        else:  # step 9a: a stored narrowing decision is used, never taken again
+            decision = decided.output
+        if decision["result"] == "claim_not_one_plan":
+            return _failed(engine, report, "claim_not_one_plan", decision["reason"])
+        if decision["result"] == "partly_sufficient":
+            if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
                 if _explain(engine, report, agent_kw) in RUN_STOPS:
                     return _stopped(engine, report, report.explanation_failure)
+            if _row(engine, run_id).status == "running":
                 completion.copy_partly_sufficient(engine, run_id)
-                q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
-                report.narrower_question = q.number
-                return _done(engine, report)
-        report.ready = True
-        return _done(engine, report)
+            q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
+            report.narrower_question = q.number
+            return _done(engine, report)
+        return _wait(engine, report)
     except Refused as refused:
         return _failed(engine, report, "refused", refused.code)
 
 
 def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
-    """From the rules lock to the end, for a run `prepare` left ready. The plan is built again from what is stored
-    (the narrower question's stored plan with its checks, the reference plan, or the Planner's stored answer after
-    a narrowing decision to proceed), so nothing is carried between the two in memory."""
+    """From the rules lock to the end. A waiting run goes on only once a person has confirmed it (it is then running
+    again); a waiting run that no one confirmed is left as it is. The plan is `confirmation.plan_to_lock`'s, built
+    again from what is stored, so nothing is carried between the two in memory. Each step after the lock runs only
+    if its stored result is absent (step 9a)."""
     report = RunReport(run_id)
     agent_kw = dict(ceiling=ceiling, client_options=client_options)
     row = _row(engine, run_id)
     try:
+        if row.status == "waiting":
+            if not _exists(engine, "SELECT 1 FROM rules_confirmation WHERE run_id = :r", run_id):
+                return _done(engine, report)  # waiting for a person: not stuck, nothing to do
+            _go_on(engine, run_id)
+            row = _row(engine, run_id)
         if row.status != "running":
             raise Refused("proceed", "stage_mismatch", "the run is not running")
-        if row.narrower_of_run_id is not None:
-            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+        if not _exists(engine, "SELECT 1 FROM plan WHERE run_id = :r", run_id):
+            plan, code = _lockable(engine, run_id)
             if code:
                 return _failed(engine, report, code)
-        elif row.fixed_plan:
-            plan = _reference_plan(row)
-        else:
-            plan = _planner_plan(engine, run_id, row)
-        checkpoints.lock_rules(engine, run_id, plan)
-        report.stages.append("rules lock")
-        extract.store_records(engine, run_id)
-        checks.run_checks(engine, run_id)
+            _require_confirmed(engine, run_id, plan)
+            checkpoints.lock_rules(engine, run_id, plan)
+            report.stages.append("rules lock")
+        extract.store_records(engine, run_id)  # only the sources still pending
+        if _stored(engine, run_id, "checks") is None:
+            checks.run_checks(engine, run_id)
         report.stages += ["records stored", "checks"]
-        c = critic.run_critic(engine, run_id, **agent_kw)
-        report.stages.append("critic")
-        stops = [f for f in c.failures if f in RUN_STOPS]
-        if stops:
-            return _stopped(engine, report, stops[0])
-        spent = [f for f in c.failures if f in SPENDING]
-        if spent:
-            return _failed(engine, report, "spending_refused", spent[0])
-        inclusion.decide_run(engine, run_id)
-        checkpoints.freeze_dataset(engine, run_id)
-        analysis.run_statistics(engine, run_id)
+        if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'critic'", run_id):
+            c = critic.run_critic(engine, run_id, **agent_kw)
+            report.stages.append("critic")
+            stops = [f for f in c.failures if f in RUN_STOPS]
+            if stops:
+                return _stopped(engine, report, stops[0])
+            spent = [f for f in c.failures if f in SPENDING]
+            if spent:
+                return _failed(engine, report, "spending_refused", spent[0])
+        if _stored(engine, run_id, "inclusion") is None:
+            inclusion.decide_run(engine, run_id)
+        if _stored(engine, run_id, "dataset_freeze") is None and not _exists(
+                engine, "SELECT 1 FROM calibration_result WHERE run_id = :r AND analysis_result_id IS NULL "
+                        "AND reason = 'no_dataset_frozen'", run_id):
+            checkpoints.freeze_dataset(engine, run_id)
+        if _stored(engine, run_id, "statistics") is None:
+            analysis.run_statistics(engine, run_id)
         report.stages += ["inclusion", "dataset freeze", "statistics"]
-        if _explain(engine, report, agent_kw) in RUN_STOPS:
-            return _stopped(engine, report, report.explanation_failure)
+        if not _exists(engine, "SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'", run_id):
+            if _explain(engine, report, agent_kw) in RUN_STOPS:
+                return _stopped(engine, report, report.explanation_failure)
         completion.copy_decision(engine, run_id)
         return _done(engine, report)
     except Refused as refused:
         return _failed(engine, report, "refused", refused.code)
 
 
-def _reference_plan(row) -> dict:
-    plan = plans.reference_plan(row.hypothesis_version_id)
-    plan["sufficiency"]["option"] = row.sufficiency_option
-    return plan
+def _lockable(engine: Engine, run_id: int) -> tuple[dict | None, str | None]:
+    """`confirmation.plan_to_lock`'s plan, or the failure code of a narrower question whose plan cannot be locked."""
+    try:
+        with engine.connect() as conn:
+            return confirmation.plan_to_lock(conn, run_id), None
+    except confirmation.NotLockable as error:
+        if error.code == "stage_mismatch":
+            raise Refused("proceed", "stage_mismatch", "no Planner answer with a narrowing decision to proceed") from None
+        return None, error.code
 
 
-def _stored_reading(engine: Engine, stage_id: int) -> dict | None:
+def _require_confirmed(engine: Engine, run_id: int, plan: Mapping) -> None:
+    """A run that waited locks only the plan whose fingerprint the person confirmed (the database checks it too)."""
     with engine.connect() as conn:
-        return conn.execute(text("SELECT output->'question_as_tested' FROM stage_result WHERE id = :s"),
-                            dict(s=stage_id)).scalar_one()
+        if not confirmation.needs_confirmation(conn, run_id):
+            return
+        confirmed = conn.execute(text("SELECT plan_fingerprint FROM rules_confirmation WHERE run_id = :r"),
+                                 dict(r=run_id)).scalar_one_or_none()
+    if confirmed != confirmation.plan_fingerprint(plan):
+        raise Refused("lock_rules", "not_confirmed", "no person's confirmation of exactly this plan")
+
 
+def _wait(engine: Engine, report: RunReport) -> RunReport:
+    """The run waits for a named person's confirmation of the question as tested (step 9a, Q1)."""
 
-def _planner_plan(engine: Engine, run_id: int, row) -> dict:
-    """The plan from the Planner's stored answer, only after a stored narrowing decision to proceed."""
+    def body(conn: Connection, _stage: str):
+        conn.execute(text("UPDATE run SET status = 'waiting' WHERE id = :r"), dict(r=report.run_id))
+
+    write(engine, report.run_id, "orchestrator", "wait", body)
+    return _done(engine, report)
+
+
+def _go_on(engine: Engine, run_id: int) -> None:
+    """A confirmed waiting run is running again (the database requires the confirmation, 0007)."""
+
+    def body(conn: Connection, _stage: str):
+        conn.execute(text("UPDATE run SET status = 'running' WHERE id = :r AND status = 'waiting'"), dict(r=run_id))
+
+    write(engine, run_id, "orchestrator", "go_on", body)
+
+
+def _stored_reading(engine: Engine, stage_id: int) -> dict | None:
     with engine.connect() as conn:
-        stored = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' AND "
-                                   "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
-        decided = conn.execute(text("SELECT output->>'result' FROM stage_result WHERE run_id = :r AND stage = "
-                                    "'narrowing' AND status = 'done' ORDER BY id DESC LIMIT 1"),
-                               dict(r=run_id)).scalar_one_or_none()
-    if not isinstance(stored, dict) or decided != "proceed":
-        raise Refused("proceed", "stage_mismatch", "no Planner answer with a narrowing decision to proceed")
-    a = stored["answer"]
-    return planner.build_plan(row.hypothesis_version_id, a["claim_scope"], a["outcome"], a["exclusion_rules"],
-                              row.sufficiency_option)
+        return conn.execute(text("SELECT output->'question_as_tested' FROM stage_result WHERE id = :s"),
+                            dict(s=stage_id)).scalar_one()
 
 
 def _explain(engine: Engine, report: RunReport, agent_kw: Mapping) -> str | None:
@@ -270,7 +328,7 @@ def _done(engine: Engine, report: RunReport) -> RunReport:
 def _failed(engine: Engine, report: RunReport, code: str, detail: str | None = None) -> RunReport:
     try:
         report.failure = fail_run(engine, report.run_id, code, detail)
-    except Refused as refused:  # a call still open (its recording failed): step 9 recovers the run
+    except Refused as refused:  # a call still open (its recording failed): step 9b recovers the run
         report.failure = f"{code} ({detail}); the run could not be ended: {refused.code}"
     return _done(engine, report)
 
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
index de5c034..b6ea7af 100644
--- a/hypocurate/pipeline/queries.py
+++ b/hypocurate/pipeline/queries.py
@@ -14,6 +14,15 @@ Every write follows the locking protocol (README, "Database migrations"): `run_t
   role (`settings.RUN_ROLES`). A fixed-plan run (criterion 14.1a, or a narrower question's run, A8) records
   `fixed_plan`. The database refuses an unsupported domain with its own message (PRD 5.5, 14.3).
 - `start`: queued -> running.
+- Step 9a (owner's approval of the step 9 plan, 2026-10-08; the reasons' wording approved with the go for 9a):
+  - `dispatch` stores the run's spending ceiling (R5; read by `spend.reserve` on every request, so it holds after
+    a crash or a restart) and refuses when this month's counted model calls have reached the monthly cap (R5; PRD
+    8, 9.3), or when a chosen source is constructed test data and the run is not marked as a test (Q6; the
+    storage guard stays as the backstop);
+  - `dispatch_again`: a new queued run of a query whose earlier run ended (PRD 8, 14.4), recording what that run
+    recorded (fixed plan, test mark; a ceiling only as given), refused while another run of the query is open;
+  - `cancel`: a named person cancels a queued or a waiting run (R3); a started run cannot be cancelled in
+    sprint 1.
 - `create_narrower`: the narrower question of a run completed as partly sufficient (owner, Q10, A8): a
   separate query linked to that run, created as submitted, with its original's domain, sources and option,
   and a text built by code from `NARROWER_TEXT`.
@@ -22,6 +31,7 @@ from __future__ import annotations
 
 import json
 from dataclasses import dataclass
+from decimal import Decimal
 from typing import Iterable, Mapping
 
 from sqlalchemy import Connection, Engine, text
@@ -34,6 +44,16 @@ REVIEWER_MAX = 200
 # The narrower question's text (owner, A8; register 'narrower_question_text'): code-built, never a model's.
 NARROWER_TEXT = "{original} (narrower question: {scope})"
 CONSTRUCTED_MARK = "constructed_test_data"
+OPEN_STATUSES = ("queued", "waiting", "running")
+# Step 9a: the fixed reasons (owner, 2026-10-08; the monthly cap's in the owner's own words).
+REASONS = {
+    "month_cap_reached": "this month's model calls have reached the monthly cap ($50); dispatch is refused until next "
+                         "month, or until the owner raises the cap",
+    "constructed_source_unmarked": "{source} is constructed test data; dispatch it only as a marked test run",
+    "already_open": "another run of this query is queued, waiting or running",
+}
+CANCELLED = {"queued": "cancelled: cancelled by {by} before it started",
+             "waiting": "cancelled: cancelled by {by} while waiting for confirmation of the question as tested"}
 
 
 class QueryRefused(Exception):
@@ -120,41 +140,125 @@ def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None
     run_transaction(engine, body)
 
 
-def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False) -> int:
+def _ceiling(ceiling) -> Decimal | None:
+    if ceiling is None:
+        return None
+    if not isinstance(ceiling, Decimal) or not ceiling.is_finite() or not ceiling > 0:
+        raise QueryRefused("invalid_ceiling", "the ceiling is a positive amount of US dollars")
+    return ceiling
+
+
+def _dispatch_checks(conn: Connection, version_id: int, constructed_test_data: bool) -> None:
+    """Step 9a: the monthly cap (R5) and constructed test data (Q6), in the dispatching transaction."""
+    from hypocurate.pipeline.agents import spend
+    from hypocurate.sources.versions import SOURCES
+    if spend.month_total(conn) >= spend.MONTH_CAP_USD:
+        raise QueryRefused("month_cap_reached", REASONS["month_cap_reached"])
+    if not constructed_test_data:
+        for key in conn.execute(text("SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = "
+                                     "hvs.source_id WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"),
+                                dict(v=version_id)).scalars():
+            if key in SOURCES and SOURCES[key].constructed:
+                raise QueryRefused("constructed_source_unmarked",
+                                   REASONS["constructed_source_unmarked"].format(source=key))
+
+
+def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False,
+             ceiling: Decimal | None = None) -> int:
     """Dispatches the version; returns the queued run's id. `fixed_plan` asks for the reference plan (14.1a). A
     narrower question's run always uses the plan its original's narrowing decision stored: that comes from the
     question's link to its original, never from the caller's flag (step 8b fix round, finding 1; the database
-    refuses such a run without the flag, migration 0006)."""
+    refuses such a run without the flag, migration 0006). `ceiling`: stored on the run (step 9a, R5)."""
+    ceiling = _ceiling(ceiling)
     setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}
 
     def body(conn: Connection):
         _lock_version(conn, version_id)
-        narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv JOIN "
-                                     "hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v"),
-                                dict(v=version_id)).scalar_one()
+        _dispatch_checks(conn, version_id, constructed_test_data)
         conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
                      dict(v=version_id))
-        flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
-        rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
-                                "VALUES (:v, :f, CAST(:x AS jsonb)) RETURNING id"),
-                           dict(v=version_id, f=fixed_plan or narrower, x=flags)).scalar_one()
-        chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
-                                  dict(v=version_id)).scalars())
-        for sid, key, latest in conn.execute(text(
-                "SELECT s.id, s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id "
-                "AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) FROM source s ORDER BY s.id")).all():
-            if sid in chosen:
-                if latest is None:
-                    raise QueryRefused("source_not_sealed", f"the chosen source {key!r} has no sealed version")
-                conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
-                                  "VALUES (:r, :s, :sv, 'pending')"), dict(r=rid, s=sid, sv=latest))
-            else:
-                conn.execute(text("INSERT INTO run_source (run_id, source_id, search_status) "
-                                  "VALUES (:r, :s, 'not_selected')"), dict(r=rid, s=sid))
-        for role, setting in setting_ids.items():
-            conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :s)"),
-                         dict(r=rid, o=role, s=setting))
-        return rid
+        return _new_run(conn, version_id, fixed_plan, constructed_test_data, ceiling, setting_ids)
+
+    return run_transaction(engine, body)
+
+
+def _new_run(conn: Connection, version_id: int, fixed_plan: bool, constructed_test_data: bool,
+             ceiling: Decimal | None, setting_ids: Mapping[str, int]) -> int:
+    """The queued run of a dispatched version, with everything a run records at dispatch."""
+    narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv JOIN "
+                                 "hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v"),
+                            dict(v=version_id)).scalar_one()
+    flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
+    rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags, spending_ceiling) "
+                            "VALUES (:v, :f, CAST(:x AS jsonb), :c) RETURNING id"),
+                       dict(v=version_id, f=fixed_plan or narrower, x=flags, c=ceiling)).scalar_one()
+    chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
+                              dict(v=version_id)).scalars())
+    for sid, key, latest in conn.execute(text(
+            "SELECT s.id, s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id "
+            "AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) FROM source s ORDER BY s.id")).all():
+        if sid in chosen:
+            if latest is None:
+                raise QueryRefused("source_not_sealed", f"the chosen source {key!r} has no sealed version")
+            conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
+                              "VALUES (:r, :s, :sv, 'pending')"), dict(r=rid, s=sid, sv=latest))
+        else:
+            conn.execute(text("INSERT INTO run_source (run_id, source_id, search_status) "
+                              "VALUES (:r, :s, 'not_selected')"), dict(r=rid, s=sid))
+    for role, setting in setting_ids.items():
+        conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :s)"),
+                     dict(r=rid, o=role, s=setting))
+    return rid
+
+
+def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = None) -> int:
+    """A new queued run of query `number`'s dispatched version, once no run of the query is open (PRD 8, 14.4). It
+    records what the version's latest run recorded (fixed plan, test mark), and the ceiling only as given now."""
+    ceiling = _ceiling(ceiling)
+    with engine.connect() as conn:
+        vid = conn.execute(text(
+            "SELECT hv.id FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
+            "WHERE h.number = :n AND hv.status = 'dispatched' ORDER BY hv.version_number DESC LIMIT 1"),
+            dict(n=number)).scalar_one_or_none()
+    if vid is None:
+        raise QueryRefused("not_dispatched", f"query {number} has no dispatched version to dispatch again")
+    setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}
+
+    def body(conn: Connection):
+        _lock_version(conn, vid)
+        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = "
+                             "r.hypothesis_version_id WHERE hv.hypothesis_id = (SELECT hypothesis_id FROM "
+                             "hypothesis_version WHERE id = :v) AND r.status IN ('queued', 'waiting', 'running'))"),
+                        dict(v=vid)).scalar_one():
+            raise QueryRefused("already_open", REASONS["already_open"])
+        last = conn.execute(text("SELECT fixed_plan, experiment_flags FROM run WHERE hypothesis_version_id = :v "
+                                 "ORDER BY id DESC LIMIT 1"), dict(v=vid)).one()
+        marked = isinstance(last.experiment_flags, dict) and last.experiment_flags.get(CONSTRUCTED_MARK) is True
+        _dispatch_checks(conn, vid, marked)
+        return _new_run(conn, vid, last.fixed_plan, marked, ceiling, setting_ids)
+
+    return run_transaction(engine, body)
+
+
+def cancel(engine: Engine, run_id: int, by: str) -> str:
+    """A named person cancels a queued or a waiting run (R3); returns the reason recorded. Refused for any other
+    status (a started run cannot be cancelled in sprint 1)."""
+    name = by.strip() if isinstance(by, str) else ""
+    if not name or len(name) > REVIEWER_MAX:
+        raise QueryRefused("name_required", f"a cancel names the person (1 to {REVIEWER_MAX} characters)")
+
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        if conn.execute(text("SELECT count(*) FROM run WHERE id = :r"), dict(r=run_id)).scalar_one() == 0:
+            raise QueryRefused("unknown_run", f"no run {run_id}")
+        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        if status not in CANCELLED:
+            raise QueryRefused("not_cancellable", f"run {run_id} is {status}; only a queued or a waiting run can be "
+                                                  "cancelled (a started run cannot be cancelled in sprint 1)")
+        reason = CANCELLED[status].format(by=name)
+        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
+                     dict(f=reason, r=run_id))
+        return reason
 
     return run_transaction(engine, body)
 
@@ -184,7 +288,18 @@ def scope_in_words(scope: Mapping) -> str:
 
 
 def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping) -> Query:
-    """The narrower question of a run completed as partly sufficient, created as submitted (Q10)."""
+    """The narrower question of a run completed as partly sufficient, created as submitted (Q10). Step 9a: taken up
+    again after a stop, it finishes what was begun (a draft left by a stop is submitted) and never creates a second
+    one (the database allows one per run, 0007)."""
+    with engine.connect() as conn:
+        existing = conn.execute(text(
+            "SELECT h.id, h.number, hv.id AS vid, hv.status FROM hypothesis h JOIN hypothesis_version hv ON "
+            "hv.hypothesis_id = h.id WHERE h.narrower_of_run_id = :r ORDER BY hv.version_number LIMIT 1"),
+            dict(r=original_run)).one_or_none()
+    if existing is not None:
+        if existing.status == "draft":
+            submit(engine, existing.vid)
+        return Query(existing.id, existing.number, existing.vid)
     with engine.connect() as conn:
         row = conn.execute(text(
             "SELECT hv.text, d.key AS domain, hv.sufficiency_option, hv.id AS vid FROM run r "
diff --git a/hypocurate/pipeline/reading.py b/hypocurate/pipeline/reading.py
index 869b3fe..1f6ad63 100644
--- a/hypocurate/pipeline/reading.py
+++ b/hypocurate/pipeline/reading.py
@@ -4,8 +4,8 @@ Code writes, from a scope and its exclusion rules, the question a run actually t
 size, each scope part in words (a band other than room temperature with its range), and each exclusion rule. For a
 run with the Planner, these are the Planner's reading of the claim: each part is marked as the claim states it or
 as assumed (the Planner's own marks, checked only in that a part marked assumed must hold the profile's default),
-and the label says the reading is not verified by code and that a person confirms it at the rules lock on the
-website (step 10). For a fixed-plan run, or a narrower question's run, the reading comes from that plan.
+and the label says the reading is not verified by code and, until a named person confirms it at the rules lock
+(step 9a), that no person has; once confirmed, it says by whom and when (owner, 2026-10-08). For a fixed-plan run, or a narrower question's run, the reading comes from that plan.
 
 The text is stored with the Planner's stage output (the Planner's reading) and, for a fixed or narrower plan,
 follows from the locked plan; the command line prints it beside the original claim before the run goes on to the
@@ -29,6 +29,8 @@ LABELS = {
     "narrower": "the narrower plan stored by the original question's narrowing decision",
 }
 PART_LABELS = {"phase_class": "phase class", "test_type": "test type"}
+# Owner, 2026-10-08 (step 9a, question 2): the label once a person has confirmed the reading at the rules lock.
+CONFIRMED_LABEL = "the Planner's reading of the claim; not verified by code; confirmed by {by} on {at}"
 STATED = "as the claim states"
 ASSUMED = "assumed: the claim does not state it"
 
@@ -100,14 +102,29 @@ def from_plan(plan: Mapping[str, Any], source: str) -> dict[str, str]:
 
 def stored(conn: Connection, run_id: int) -> dict | None:
     """The question as tested of a run: the Planner's stored reading, else the reading of its locked plan (fixed
-    or narrower), else the Planner's reading of a partly-sufficient original (no plan), else none."""
+    or narrower), else the Planner's reading of a partly-sufficient original (no plan), else none. Once a named
+    person confirmed it (step 9a), its label says by whom and when."""
     out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' AND status = "
                             "'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
     if isinstance(out, dict) and out.get("question_as_tested"):
-        return out["question_as_tested"]
+        return _confirmed(conn, run_id, out["question_as_tested"])
     row = conn.execute(text("SELECT p.content, h.narrower_of_run_id FROM plan p JOIN run r ON r.id = p.run_id JOIN "
                             "hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = "
                             "hv.hypothesis_id WHERE p.run_id = :r"), dict(r=run_id)).one_or_none()
     if row is None:
         return None
-    return from_plan(row.content, "narrower" if row.narrower_of_run_id is not None else "fixed")
+    return _confirmed(conn, run_id, from_plan(row.content, "narrower" if row.narrower_of_run_id is not None else "fixed"))
+
+
+def _confirmed(conn: Connection, run_id: int, tested: dict) -> dict:
+    """The reading with its label once a person confirmed it (owner, 2026-10-08, question 2); else as it is."""
+    row = conn.execute(text("SELECT confirmed_by, to_char(confirmed_at AT TIME ZONE 'UTC', "
+                            "'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS at FROM rules_confirmation WHERE run_id = :r"),
+                       dict(r=run_id)).one_or_none()
+    if row is None:
+        return tested
+    if tested["label"] == LABELS["planner"]:
+        label = CONFIRMED_LABEL.format(by=row.confirmed_by, at=row.at)
+    else:
+        label = f"{tested['label']}; confirmed by {row.confirmed_by} on {row.at}"
+    return {**tested, "label": label}
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index da00ed5..1106be0 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -67,6 +67,8 @@ CODES = {
     "decision_not_current": "the stored decision belongs to a different freeze than the run's",
     # Step 8b.
     "narrowed": "code's narrowing decision is partly sufficient: the original question locks no plan",
+    # Step 9a (owner, Q1): a run that waited locks only the plan whose fingerprint the person confirmed.
+    "not_confirmed": "no person's confirmation of exactly this plan (its fingerprint) before the rules lock",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
 # Step 7 (owner, 2026-10-05; register 'constructed_test_runs'): TEST_RUN_LABEL, on every stored
```
## 3. New test files

### `tests/test_cli_step9a.py`

```python
"""Step 9a: the command line's wait, `confirm`, `cancel`, `dispatch --again` and the stored `--ceiling` (owner's
approval of the step 9 plan, 2026-10-08: R1, R2, R3, R5, A2; no bulk or automatic confirmation). Each run executes in
the guarded process; the model provider is the local stub (no live call)."""
from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import text

from hypocurate.pipeline import confirmation, queries
from test_cli_runs import engine, hc, stub  # noqa: F401 (fixtures)
from test_confirmation import newer_version
from test_orchestrator import FCC_CLAIM, planner_body, responder


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def run_to_wait(capsys, engine, stub):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    first, reading, rest = out.split("\n", 2)
    return code, json.loads(first)["run"], json.loads(rest), err


def test_run_stops_at_the_wait_and_says_what_it_waits_for(engine, stub, capsys):
    code, rid, report, err = run_to_wait(capsys, engine, stub)
    assert code == 0, err
    assert report["status"] == "waiting" and report["waiting_for"] == confirmation.WAITING_FOR
    assert report["next"] == f'hypocurate confirm {rid} --by "<name>"'
    assert report["statement"] is None and report["outcome"] is None
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    shown = json.loads(hc(capsys, "show", str(rid))[1])
    assert shown["waiting_for"] == confirmation.WAITING_FOR


def test_confirm_prints_what_is_confirmed_before_the_report_and_stores_exactly_that_text(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    printed, report = out[:out.index("\n{")], json.loads(out[out.index("\n{") + 1:])
    assert printed == one(engine, "SELECT shown FROM rules_confirmation WHERE run_id = :r", r=rid)
    assert printed.startswith(f"Run {rid} of ")
    assert report["status"] == "completed" and report["outcome_code"] == "sufficient"
    assert report["question_as_tested"]["label"].startswith(
        "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on ")


def test_confirm_needs_a_waiting_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 1 and err.startswith(f"error: not_waiting: run {rid} is not waiting for confirmation")
    code, out, err = hc(capsys, "confirm", "999", "--by", "Ada Reviewer")
    assert code == 1 and err.startswith("error: unknown_run")


def test_confirm_is_refused_when_the_sources_changed_and_nothing_is_recorded(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    newer_version(engine, "tamu_fcc")
    code, out, err = hc(capsys, "confirm", str(rid), "--by", "Ada Reviewer")
    assert code == 1
    assert err.strip() == ("error: sources_changed: tamu_fcc has a newer version since this run's narrowing; cancel "
                           "this run and dispatch the query again")
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_cancel_a_waiting_run_then_dispatch_the_query_again(engine, stub, capsys):
    _, rid, _, _ = run_to_wait(capsys, engine, stub)
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 0, err
    assert json.loads(out) == {"run": rid, "status": "failed", "failure": "cancelled: cancelled by Ada Reviewer while "
                                                                          "waiting for confirmation of the question as tested"}
    number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                         "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)
    code, out, err = hc(capsys, "dispatch", number, "--again")
    assert code == 0, err
    again = json.loads(out.split("\n", 1)[0])["run"]
    assert again != rid and json.loads(out.split("\n", 2)[2])["status"] == "waiting"
    code, out, err = hc(capsys, "dispatch", number, "--again")
    assert code == 1 and err.strip() == "error: already_open: another run of this query is queued, waiting or running"


def test_cancel_refuses_a_started_or_ended_run(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    rid = json.loads(out.split("\n", 1)[0])["run"]
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 1 and err.startswith(f"error: not_cancellable: run {rid} is completed")


def test_a_queued_run_is_cancelled_from_the_command_line(engine, capsys):
    q = queries.create(engine, FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    code, out, err = hc(capsys, "cancel", str(rid), "--by", "Ada Reviewer")
    assert code == 0 and json.loads(out)["failure"] == "cancelled: cancelled by Ada Reviewer before it started"


def test_the_ceiling_given_to_run_is_stored_on_the_run(engine, stub, capsys):
    rid, _, _ = run_with_ceiling(capsys, engine, stub)
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("1.5")


def run_with_ceiling(capsys, engine, stub):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer",
                        "--ceiling", "1.5")
    return json.loads(out.split("\n", 1)[0])["run"], out, err


def test_dispatch_without_again_still_names_the_reviewer(engine, capsys):
    q = queries.create(engine, FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    code, out, err = hc(capsys, "dispatch", q.number)
    assert code == 1 and "--by names the person confirming the domain" in err
```
### `tests/test_confirmation.py`

```python
"""Step 9a: the run waits at the rules lock for a named person (owner's approval of the step 9 plan, 2026-10-08: Q1,
Q5, additions A1 and A2, and the go for 9a: no bulk or automatic confirmation; the label once confirmed).

Whole runs through the orchestrator, every model call to the local stub (as tests/test_orchestrator.py)."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import pathlib

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
import test_orchestrator as to
from hypocurate import cli_runs
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import confirmation, orchestrator, queries

LABEL = "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on "


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


def run(engine, rid, stub):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def proceed(engine, rid, stub):
    return orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def waiting(engine, stub, body=None, claim=to.FCC_CLAIM):
    stub.respond(to.responder(body or to.planner_body()))
    rid = to.dispatched(engine, claim=claim)
    report = run(engine, rid, stub)
    assert report.status == "waiting", report
    return rid


def narrower_waiting(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    original = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    assert run(engine, original, stub).outcome == "partly_sufficient"
    number = cli_runs.show(engine, original)["narrower_question"]
    vid = queries.submitted_version(engine, number)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    rid = queries.dispatch(engine, vid)
    before = len(stub.requests)
    assert run(engine, rid, stub).status == "waiting"
    assert len(stub.requests) == before  # a narrower question's run never asks the Planner
    return rid, original


def newer_version(engine, key="mpea"):
    """A newer sealed version of a registered source (a new file), as a later registration would add."""
    from model_builder import sha, version_fingerprint
    with engine.begin() as conn:
        src = conn.execute(text("SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = :k"),
                           dict(k=key)).one()
        vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, 'newer', "
                                "'2026-10-08') RETURNING id"), dict(s=src.id)).scalar_one()
        data = b"newer,data\n"
        conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'x.csv', "
                          ":h, :c)"), dict(v=vid, h=sha(data), c=data))
        fp = version_fingerprint({"x.csv": data}, src.source_type, src.data_kind, src.grouping_unit)
        conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :f WHERE id = :v"),
                     dict(f=fp, v=vid))


# --- the wait (Q1, Q5) --------------------------------------------------------------------------------------

def test_a_planner_run_waits_before_its_rules_lock_and_nothing_more_is_done(engine, stub):
    rid = waiting(engine, stub)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT string_agg(stage, ',' ORDER BY id) FROM stage_result WHERE run_id = :r", r=rid) == \
        "planner,narrowing"
    assert len(stub.requests) == 1  # the Planner only
    assert cli_runs.show(engine, rid)["waiting_for"] == confirmation.WAITING_FOR


def test_a_waiting_run_that_no_one_confirmed_is_left_as_it_is(engine, stub):
    rid = waiting(engine, stub)
    for again in (run, proceed):
        report = again(engine, rid, stub)
        assert (report.status, report.failure) == ("waiting", None)
    assert len(stub.requests) == 1
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_a_fixed_plan_run_never_waits(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert run(engine, rid, stub).status == "completed"
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0


def test_a_narrower_questions_run_waits_and_goes_on_once_confirmed(engine, stub):
    rid, _ = narrower_waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert proceed(engine, rid, stub).status == "completed"


def test_once_confirmed_the_run_locks_exactly_the_confirmed_plan_and_completes(engine, stub):
    rid = waiting(engine, stub)
    stored = confirmation.confirm(engine, rid, by="Ada Reviewer")
    report = proceed(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "sufficient")
    assert one(engine, "SELECT fingerprint FROM plan WHERE run_id = :r", r=rid) == \
        stored["content"]["plan_fingerprint"] == \
        one(engine, "SELECT plan_fingerprint FROM rules_confirmation WHERE run_id = :r", r=rid)


def test_the_planner_is_not_asked_again_after_the_wait(engine, stub):
    rid = waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    proceed(engine, rid, stub)
    planner_requests = [r for r in stub.requests if "[[ ## plan ## ]]" in r["raw"].decode("utf-8", "replace")]
    assert len(planner_requests) == 1
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid) == 1


# --- what is shown and stored (A2) --------------------------------------------------------------------------

def test_confirm_shows_every_item_and_stores_exactly_the_text_shown(engine, stub):
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    stored = confirmation.confirm(engine, rid, by="Ada Reviewer", shown=content)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT content, shown, confirmed_by FROM rules_confirmation WHERE run_id = :r"),
                           dict(r=rid)).one()
    assert row.shown == words == stored["shown"] == confirmation.render(row.content)  # byte for byte
    assert hashlib.sha256(row.shown.encode()).digest() == hashlib.sha256(words.encode()).digest()
    assert row.content == content and row.confirmed_by == "Ada Reviewer"
    tested = content["question_as_tested"]
    for item in (to.FCC_CLAIM, tested["text"], tested["label"], "Narrowed: no", "Candidate records per claim part",
                 "alloy class:", "phase class: FCC (as the claim states)", "test type: tension",
                 "temperature band: room temperature", "Outcome: yield strength against grain size",
                 "Exclusion rules: excluding records with a grain size below 0.1 µm",
                 "Sufficiency option: fixed minimum (minimums: 30 records",
                 "Sources: mpea version", "Cost so far: $", "Plan to be locked: fingerprint " + content["plan_fingerprint"]):
        assert item in words, item
    assert content["cost_so_far"]["calls"] == 1


def test_the_narrower_questions_confirmation_shows_what_was_narrowed_and_why(engine, stub):
    rid, original = narrower_waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                         "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=original)
    assert f"Narrowed: this is the narrower question of {number}" in words
    assert "Why: code found no candidate record in the sources searched for temperature band cryogenic" in words
    assert "Original scope:" in words and "Narrower scope:" in words
    assert content["narrowing"]["narrowed"] is True
    assert content["planner_stage_result_id"] is None and content["narrowing_stage_result_id"] is None


@pytest.mark.parametrize("change", ["exclusion", "stated", "cost"])
def test_the_content_changes_when_any_of_its_inputs_changes(engine, stub, change):
    first = confirmation.show(engine, waiting(engine, stub))[0]
    if change == "exclusion":
        body = to.planner_body(exclusion_rules=[{"rule": "grain_size_range", "min": 0.2}])
    elif change == "stated":
        body = to.planner_body(stated={"alloy_class": True, "phase_class": True, "test_type": True,
                                       "temperature_band": False})
    else:  # the Planner's first answer cannot be read: one corrected request, two calls in this run's record
        body = to.planner_body()
        stub.queue(sp.reply("not the answer form"))
    rid = waiting(engine, stub, body=body)
    second = confirmation.show(engine, rid)[0]
    differing = {k for k in first if first[k] != second[k]} - {"run", "query", "planner_stage_result_id",
                                                                "narrowing_stage_result_id"}
    expected = {"exclusion": {"exclusion_rules", "plan_fingerprint", "question_as_tested"},
                "stated": {"scope_parts", "question_as_tested"}, "cost": {"cost_so_far"}}[change]
    assert expected <= differing, differing


def test_a_confirmation_is_refused_when_what_was_shown_is_no_longer_current(engine, stub):
    rid = waiting(engine, stub)
    content, _ = confirmation.show(engine, rid)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer", shown={**content, "cost_so_far": {}})
    assert refused.value.code == "content_changed"
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0


# --- the sources while the run waits (A1) -------------------------------------------------------------------

def test_a_newer_version_registered_while_the_run_waits_refuses_the_confirmation(engine, stub):
    rid = waiting(engine, stub)
    before = one(engine, "SELECT array_agg(source_version_id ORDER BY source_id) FROM run_source WHERE run_id = :r",
                 r=rid)
    newer_version(engine, "mpea")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert (refused.value.code, refused.value.reason) == (
        "sources_changed", "mpea has a newer version since this run's narrowing; cancel this run and dispatch the "
                           "query again")
    assert one(engine, "SELECT count(*) FROM rules_confirmation") == 0
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
    # The run's own versions never change (0001): they are those recorded at dispatch.
    assert one(engine, "SELECT array_agg(source_version_id ORDER BY source_id) FROM run_source WHERE run_id = :r",
               r=rid) == before


def test_a_source_registered_while_the_run_waits_refuses_the_confirmation(engine, stub):
    rid = waiting(engine, stub)
    pw.registered(engine, ("controlled_duplicates",))
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.reason == ("controlled_duplicates was registered since this run's narrowing; cancel this run "
                                    "and dispatch the query again")


def test_the_unchanged_sources_are_confirmed(engine, stub):
    rid = waiting(engine, stub)
    with engine.connect() as conn:
        assert confirmation.source_changes(conn, rid) == []
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


# --- one run, one named person; the label (owner, 2026-10-08) -----------------------------------------------

@pytest.mark.parametrize("by", ["", "   ", None, "x" * 201])
def test_a_confirmation_names_the_person(engine, stub, by):
    rid = waiting(engine, stub)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by=by)
    assert refused.value.code == "name_required"


def test_only_a_waiting_run_is_confirmed_and_only_once(engine, stub):
    stub.respond(to.responder())
    fixed = to.dispatched(engine, fixed_plan=True)
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, fixed, by="Ada Reviewer")
    assert refused.value.code == "not_waiting"
    rid = waiting(engine, stub)
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "already_confirmed"


def test_a_cancelled_waiting_run_is_not_confirmed(engine, stub):
    rid = waiting(engine, stub)
    queries.cancel(engine, rid, by="Ada Reviewer")
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "not_waiting"


def test_no_code_confirms_in_bulk_or_by_itself():
    """No bulk or automatic confirmation in step 9 (owner, 2026-10-08): `confirm` takes one run and one name, and
    the only caller in the package is the command line's `confirm` command."""
    params = list(inspect.signature(confirmation.confirm).parameters)
    assert params == ["engine", "run_id", "by", "shown"]
    package = pathlib.Path(confirmation.__file__).parents[1]
    callers = []
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "confirm" \
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "confirmation":
                callers.append(path.name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "confirm":
                callers.append(path.name)
    assert callers == ["cli_runs.py"], callers
    source = pathlib.Path(cli_runs.__file__).read_text(encoding="utf-8")
    assert "INSERT INTO rules_confirmation" not in source
    inserts = [p.name for p in package.rglob("*.py") if "INSERT INTO rules_confirmation" in p.read_text(encoding="utf-8")]
    assert inserts == ["confirmation.py"]


def test_once_confirmed_the_question_as_tested_says_by_whom_and_when(engine, stub):
    rid = waiting(engine, stub)
    before = cli_runs.show(engine, rid)["question_as_tested"]["label"]
    assert before == "the Planner's reading of the claim; not verified by code and, in this version, not confirmed " \
                     "by a person"
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    after = cli_runs.show(engine, rid)["question_as_tested"]["label"]
    assert after.startswith(LABEL) and after.endswith(" UTC")
    proceed(engine, rid, stub)
    assert cli_runs.show(engine, rid)["question_as_tested"]["label"] == after


# --- added after the mutation checks (c03, c06, o04) --------------------------------------------------------

def test_a_running_run_is_refused_by_codes_own_check(engine, stub):
    """Mutation c03: code refuses a run that is not waiting itself (the database's refusal is the backstop)."""
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    narrowing.run_narrowing(engine, rid, planner.run_planner(engine, rid, client_options=sp.client_options(stub)).answer)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    with pytest.raises(queries.QueryRefused) as refused:
        confirmation.confirm(engine, rid, by="Ada Reviewer")
    assert (refused.value.code, refused.value.reason) == (
        "not_waiting", f"run {rid} is not waiting for confirmation (it is running)")


def test_the_cost_shown_is_the_runs_counted_and_reported_cost(engine, stub):
    """Mutation c06: the cost so far is the run's own total, counted as the caps count it."""
    from decimal import Decimal
    rid = waiting(engine, stub)
    content, words = confirmation.show(engine, rid)
    with engine.connect() as conn:
        cap, reported = conn.execute(text("SELECT cap_cost, reported_cost FROM model_call_totals_by_run WHERE run_id = "
                                          ":r"), dict(r=rid)).one()
    assert Decimal(content["cost_so_far"]["counted_usd"]) == cap > 0
    assert Decimal(content["cost_so_far"]["reported_usd"]) == reported > 0
    assert f"Cost so far: ${cap:.6f} counted toward the caps (reported ${reported:.6f}; 1 model calls" in words


def test_code_locks_only_the_confirmed_plan_and_says_so(engine, stub):
    """Mutation o04: a confirmation of another fingerprint (written past the code by direct SQL) stops the run with
    code's own reason before the lock is tried; the database's backstop is not what refuses it."""
    rid = waiting(engine, stub)
    content, _ = confirmation.show(engine, rid)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                          "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada Reviewer', :fp, :p, :n, '{}', 'x')"),
                     dict(r=rid, fp="e" * 64, p=content["planner_stage_result_id"], n=content["narrowing_stage_result_id"]))
    report = proceed(engine, rid, stub)
    assert report.status == "failed" and report.failure == "refused: a checkpoint or write refused (not_confirmed)"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
```
### `tests/test_migrations_step9a.py`

```python
"""Step 9a: migration 0007 (owner's approval of the step 9 plan, 2026-10-08, subject to the second-model review).

The run waits at the rules lock for a named person (owner, Q1): a new run status 'waiting'; an append-only
`rules_confirmation` bound to the plan that will be locked (its fingerprint) and to the source versions the
narrowing counts were taken on (owner's addition A1); the plan backstop; the spending ceiling stored on the run
(R5); one narrower question per original run. 0001's `hc_run_update` is the only earlier function replaced, and
only its list of status changes differs. Up, down, up gives the same schema; the downgrade refuses while anything
0007 adds is in use; a failed upgrade changes nothing."""
from __future__ import annotations

import json

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import FP, World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
OTHER_FP = "e" * 64
CONTENT = '{"question": "shown"}'


def m0007():
    """Migration 0007's module (looked up when a test runs, so each test fails alone where it is absent)."""
    return SCRIPTS.get_revision("0007").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


# --- helpers: a Planner run and a narrower question's run, each up to the wait ---------------------------------

def planner_run(w, narrowing="proceed", sources=("mpea", "tamu_fcc")):
    """A running run with a done Planner stage and code's narrowing decision (the stored source versions)."""
    rid = w.running()
    planner = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=planner)
    narrowed = None
    if narrowing is not None:
        narrowed = w.narrowing(rid, result=narrowing, output={"sources": w.counted(sources)})
    return rid, planner, narrowed


def narrower_run(w, sources=("mpea", "tamu_fcc")):
    original = w.running()
    w.partly(original, narrower_plan={"model": "hall_petch"}, sources=sources)
    vid = w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1)
    return w.running(vid=vid)


def wait(w, rid):
    w.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)


def confirm(w, rid, planner=None, narrowed=None, fp=FP, by="Ada Reviewer"):
    return w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                 "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, CAST(:c AS jsonb), 'shown') "
                 "RETURNING id", r=rid, b=by, fp=fp, p=planner, n=narrowed, c=CONTENT)


def confirmed(w, rid, planner=None, narrowed=None, fp=FP):
    """Waiting, confirmed, then running again: the rules may now be locked."""
    wait(w, rid)
    confirm(w, rid, planner, narrowed, fp)
    w.run_sql("UPDATE run SET status = 'running' WHERE id = :r", r=rid)


# --- the migration ------------------------------------------------------------------------------------------

def test_0007_is_the_head_and_follows_0006():
    assert migrate.head_revision() == "0007" and m0007().down_revision == "0006"


def test_the_only_earlier_function_replaced_is_hc_run_update_and_only_its_status_changes_differ():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert {f.split("(")[0] for f in m0007().FUNCTION_NAMES} & earlier == set()
    original = next(f for f in M0001.FUNCTIONS if "FUNCTION hc_run_update()" in f)
    assert original.count(m0007().TRANSITIONS_0001) == 1
    assert m0007().RUN_UPDATE_0007 == original.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION").replace(
        m0007().TRANSITIONS_0001, m0007().TRANSITIONS_0007)
    assert m0007().RUN_UPDATE_0001 == original.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")
    assert m0007().TRANSITIONS_0007.startswith(m0007().TRANSITIONS_0001[:-1])
    assert "waiting" in m0007().TRANSITIONS_0007 and "waiting" not in m0007().TRANSITIONS_0001


@pytest.mark.parametrize("table, earlier", [("run", "hc_run_update"), ("plan", "hc_plan_insert")])
def test_each_new_trigger_fires_after_the_earlier_ones_on_its_table(table, earlier):
    """PostgreSQL fires BEFORE triggers in name order: the earlier rules' messages keep their priority."""
    m6 = SCRIPTS.get_revision("0006").module
    before = [earlier] + [t for tb, _, t, _ in m6.CHECKED if tb == table and t.startswith(earlier)]
    names = [t for tb, _, t, _ in m0007().CHECKED if tb == table]
    assert names and all(n > b for n in names for b in before)


def test_up_down_up_restores_0006(engine):
    migrate.upgrade(engine, "0006")
    at_0006 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0006")
    assert snapshot(engine) == at_0006  # 0001's hc_run_update and ck_run_status exactly as before
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0006")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_waiting() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0006"


@pytest.mark.parametrize("use", ["waiting", "confirmation", "ceiling"])
def test_the_downgrade_refuses_while_0007_is_in_use(db, use):
    w = World(db)
    if use == "ceiling":
        vid = w.dispatched()
        w.val("INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, 0.5) RETURNING id", v=vid)
    else:
        rid, planner, narrowed = planner_run(w)
        wait(w, rid)
        if use == "confirmation":
            confirm(w, rid, planner, narrowed)
            w.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x' WHERE id = :r", r=rid)
    before = snapshot(db)
    with pytest.raises(Exception, match="0007 is in use"):
        migrate.downgrade(db, "0006")
    assert snapshot(db) == before and migrate.current_revision(db) == "0007"


# --- waiting (owner, Q1, Q5) --------------------------------------------------------------------------------

def test_a_planner_run_waits_after_a_narrowing_decision_to_proceed(w):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


def test_a_narrower_questions_run_waits_before_its_lock(w):
    rid = narrower_run(w)
    wait(w, rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "waiting"


@pytest.mark.parametrize("shape, match", [
    ("no_narrowing", "waits only after code's narrowing decision to proceed"),
    ("partly", "waits only after code's narrowing decision to proceed"),
    ("fixed_plan", "only a run whose plan comes from the Planner or a narrower question waits"),
    ("no_planner", "only a run whose plan comes from the Planner or a narrower question waits"),
    ("locked", "a run waits only before its rules lock"),
    ("stage_running", "a run waits only when no stage is running and no model call is open"),
    ("call_open", "a run waits only when no stage is running and no model call is open"),
])
def test_a_run_waits_only_at_the_rules_lock_of_a_plan_that_needs_a_person(w, shape, match):
    if shape == "fixed_plan":
        rid = w.running(fixed_plan=True)
    elif shape == "no_planner":
        rid = w.running()
    elif shape in ("no_narrowing", "partly"):
        rid, _, _ = planner_run(w, narrowing=None if shape == "no_narrowing" else "partly_sufficient")
    else:
        rid, _, _ = planner_run(w)
        if shape == "locked":  # a plan written past the backstop (disabled for this case only)
            w.run_sql("ALTER TABLE plan DISABLE TRIGGER hc_plan_insert_rules_confirmed")
            w.lock(rid)
            w.run_sql("ALTER TABLE plan ENABLE TRIGGER hc_plan_insert_rules_confirmed")
    if shape == "stage_running":
        w.stage(rid, "critic", "critic")
    if shape == "call_open":
        rid = w.running(agents=True)
        planner = w.stage(rid, "planner", "planner")
        w.call(rid, planner)
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=planner)
        w.narrowing(rid, result="proceed", output={"sources": w.counted(("mpea", "tamu_fcc"))})
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", match, r=rid)


def test_a_run_never_waits_again_after_its_confirmation(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed)
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", "a run waits once", r=rid)


@pytest.mark.parametrize("sql, match", [
    ("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, 'curation', NULL, 1)", "running"),
    ("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
     "min_resid_df) VALUES (:r, '{}', '" + FP + "', 'fixed_minimum', 4, 1, 2, 1)", "a plan is locked only while"),
])
def test_nothing_is_written_to_a_waiting_run(w, sql, match):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    w.rejected(sql, match, r=rid)


def test_a_waiting_run_goes_on_only_with_a_confirmation(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    w.rejected("UPDATE run SET status = 'running' WHERE id = :r", "goes on only after a person confirms", r=rid)
    confirm(w, rid, planner, narrowed)
    w.run_sql("UPDATE run SET status = 'running' WHERE id = :r", r=rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "running"


def test_a_waiting_run_can_fail_and_never_completes(w):
    rid, _, _ = planner_run(w)
    wait(w, rid)
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient', "
               "evidence_level = 1 WHERE id = :r", "run status cannot go from waiting to completed", r=rid)
    w.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'cancelled: x' WHERE id = :r",
              r=rid)
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "failed"


def test_a_queued_run_cannot_wait(w):
    rid = w.run()
    w.rejected("UPDATE run SET status = 'waiting' WHERE id = :r", "run status cannot go from queued to waiting", r=rid)


# --- the confirmation (owner, Q1, A1, A2) -------------------------------------------------------------------

def test_a_confirmation_is_recorded_with_the_databases_time_and_is_append_only(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    cid = confirm(w, rid, planner, narrowed)
    assert w.rows("SELECT confirmed_by, plan_fingerprint FROM rules_confirmation WHERE id = :c", c=cid) == [
        ("Ada Reviewer", FP)]
    w.rejected("UPDATE rules_confirmation SET confirmed_by = 'Someone Else' WHERE id = :c", "append-only", c=cid)
    w.rejected("DELETE FROM rules_confirmation WHERE id = :c", "append-only", c=cid)
    w.rejected("TRUNCATE rules_confirmation CASCADE", "append-only")


def test_the_database_sets_the_confirmation_time(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    cid = w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, confirmed_at, plan_fingerprint, "
                "planner_stage_result_id, narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', "
                "'2000-01-01', :fp, :p, :n, '{}', 'shown') RETURNING id", r=rid, fp=FP, p=planner, n=narrowed)
    assert w.val("SELECT confirmed_at > '2001-01-01' FROM rules_confirmation WHERE id = :c", c=cid)


def test_only_a_waiting_run_is_confirmed_and_only_once(w):
    rid, planner, narrowed = planner_run(w)
    with pytest.raises(IntegrityError, match="only a run waiting for confirmation is confirmed"):
        confirm(w, rid, planner, narrowed)
    wait(w, rid)
    confirm(w, rid, planner, narrowed)
    with pytest.raises(IntegrityError):
        confirm(w, rid, planner, narrowed)


@pytest.mark.parametrize("by", ["", "   ", "x" * 201])
def test_a_confirmation_names_a_person(w, by):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    with pytest.raises(IntegrityError, match="ck_rules_confirmation_named"):
        confirm(w, rid, planner, narrowed, by=by)


def test_the_confirmed_fingerprint_has_the_plan_fingerprint_format(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    with pytest.raises(IntegrityError, match="ck_rules_confirmation_fingerprint_format"):
        confirm(w, rid, planner, narrowed, fp="not-a-fingerprint")


@pytest.mark.parametrize("shape", ["no_stages", "other_planner", "earlier_narrowing", "other_run"])
def test_a_planner_runs_confirmation_names_its_planner_stage_and_its_latest_narrowing_decision(w, shape):
    rid, planner, narrowed = planner_run(w)
    if shape == "earlier_narrowing":  # a later narrowing row: the confirmation must name the latest
        later = w.stage(rid, "narrowing", None, attempt=2)
        w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = (SELECT output FROM "
                  "stage_result WHERE id = :n) WHERE id = :s", n=narrowed, s=later)
        assert later > narrowed
    wait(w, rid)
    if shape == "no_stages":
        planner, narrowed = None, None
    elif shape == "other_planner":
        other, p2, _ = planner_run(w)
        planner = p2
    elif shape == "other_run":
        other, p2, n2 = planner_run(w)
        planner, narrowed = p2, n2
    with pytest.raises(IntegrityError, match="names the run's done Planner stage and its latest narrowing decision"):
        confirm(w, rid, planner, narrowed)


def test_a_narrower_questions_confirmation_names_no_stage(w):
    rid = narrower_run(w)
    wait(w, rid)
    other, planner, narrowed = planner_run(w)
    with pytest.raises(IntegrityError, match="a narrower question's confirmation names no Planner or narrowing"):
        confirm(w, rid, planner, narrowed)
    confirm(w, rid)
    assert w.val("SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("path", ["planner", "narrower"])
@pytest.mark.parametrize("counted", ["other_fingerprint", "fewer_sources"])
def test_a_confirmation_is_refused_when_the_counted_source_versions_are_not_the_runs(w, path, counted):
    """Owner's addition A1, at the database: a run never locks on a narrowing decision taken on other versions."""
    sources = w.counted(("mpea", "tamu_fcc"))
    if counted == "other_fingerprint":
        sources[0]["version_fingerprint"] = "f" * 64
    else:
        sources = sources[:1]
    if path == "planner":
        rid, planner, _ = planner_run(w, narrowing=None)
        narrowed = w.narrowing(rid, result="proceed", output={"sources": sources})
    else:
        original = w.running()
        w.narrowing(original, output={"narrower_plan": {}, "sources": sources})
        w.complete(original, "partly_sufficient", level=1)
        rid = w.running(vid=w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1))
        planner = narrowed = None
    wait(w, rid)
    with pytest.raises(IntegrityError, match="the source versions the narrowing counts were taken on"):
        confirm(w, rid, planner, narrowed)


def test_a_confirmation_holds_its_content_and_the_text_shown(w):
    rid, planner, narrowed = planner_run(w)
    wait(w, rid)
    for content, shown in (("[]", "shown"), ('{"a": 1}', "")):
        with pytest.raises(IntegrityError, match="ck_rules_confirmation_content_and_text"):
            w.val("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
                  "narrowing_stage_result_id, content, shown) VALUES (:r, 'Ada', :fp, :p, :n, CAST(:c AS jsonb), :s) "
                  "RETURNING id", r=rid, fp=FP, p=planner, n=narrowed, c=content, s=shown)


# --- the plan backstop --------------------------------------------------------------------------------------

def test_a_planner_runs_plan_needs_its_confirmation(w):
    rid, _, _ = planner_run(w)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


def test_a_planner_runs_plan_must_be_the_confirmed_plan(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed, fp=OTHER_FP)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


def test_the_confirmed_plan_is_locked(w):
    rid, planner, narrowed = planner_run(w)
    confirmed(w, rid, planner, narrowed)
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


def test_a_narrower_questions_plan_needs_its_confirmation(w):
    rid = narrower_run(w)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid, content={"model": "hall_petch"})


@pytest.mark.parametrize("kind", ["fixed_plan", "no_planner_stage"])
def test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation(w, kind):
    """Guard: a fixed-plan run (14.1a) never waits (owner, Q5); a run with no Planner stage (the step 6-8 test
    worlds, which lock a plan directly) keeps its premises (the scoping stated in the step 9a summary)."""
    rid = w.running(fixed_plan=True) if kind == "fixed_plan" else w.running()
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


def test_a_failed_planner_attempt_still_needs_the_confirmation(w):
    rid = w.running()
    w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE run_id = :r", r=rid)
    with pytest.raises(IntegrityError, match="needs a person's confirmation of exactly this plan"):
        w.lock(rid)


# --- the spending ceiling (R5) and one narrower question per run ----------------------------------------------

def test_the_spending_ceiling_is_stored_at_dispatch_and_never_changed(w):
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, 0.5) RETURNING id", v=vid)
    assert float(w.val("SELECT spending_ceiling FROM run WHERE id = :r", r=rid)) == 0.5
    w.rejected("UPDATE run SET spending_ceiling = 1 WHERE id = :r", "what a run records at dispatch cannot change",
               r=rid)
    w.rejected("UPDATE run SET spending_ceiling = NULL WHERE id = :r", "what a run records at dispatch cannot change",
               r=rid)


@pytest.mark.parametrize("ceiling", [0, -1, "'Infinity'"])
def test_the_spending_ceiling_is_a_positive_finite_amount(w, ceiling):
    vid = w.dispatched()
    with pytest.raises(IntegrityError, match="ck_run_spending_ceiling"):
        w.val(f"INSERT INTO run (hypothesis_version_id, spending_ceiling) VALUES (:v, {ceiling}) RETURNING id", v=vid)


def test_a_run_has_at_most_one_narrower_question(w):
    original = w.running()
    w.partly(original)
    w.hypothesis(narrower_of=original)
    with pytest.raises(IntegrityError, match="uq_hypothesis_narrower_of_run_id"):
        w.hypothesis(narrower_of=original)
```
### `tests/test_queries_step9a.py`

```python
"""Step 9a: cancel, dispatch again, the spending ceiling stored at dispatch and the two new dispatch refusals
(owner's approval of the step 9 plan, 2026-10-08: R2, R3, R5, Q6; the reasons' wording approved with the go for 9a,
the monthly cap's in the owner's own words)."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import text

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents import spend

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
MONTH_CAP_REASON = ("this month's model calls have reached the monthly cap ($50); dispatch is refused until next "
                    "month, or until the owner raises the cap")


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc", "controlled_duplicates"))
    yield e
    e.dispose()


def submitted(engine, sources=("mpea", "tamu_fcc")):
    q = queries.create(engine, CLAIM, sources)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def set_status(engine, rid, status):
    with engine.begin() as conn:
        if status == "running":
            conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=rid))
        elif status == "failed":
            conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x' WHERE id = :r"),
                         dict(r=rid))


def waiting_run(engine):
    """A Planner run at its wait (stage rows as the orchestrator stores them, by direct SQL)."""
    rid = queries.dispatch(engine, submitted(engine).version_id)
    queries.start(engine, rid)
    with engine.begin() as conn:
        sources = [{"source": k, "version_fingerprint": f} for k, f in conn.execute(text(
            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id JOIN source_version sv "
            "ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=rid)).all()]
        for stage, role, output in (("planner", "planner", {}), ("narrowing", None, {"result": "proceed",
                                                                                      "sources": sources})):
            sid = conn.execute(text("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :o, 1) "
                                    "RETURNING id"), dict(r=rid, s=stage, o=role)).scalar_one()
            conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = CAST(:o AS jsonb) "
                              "WHERE id = :s"), dict(s=sid, o=json.dumps(output)))
        conn.execute(text("UPDATE run SET status = 'waiting' WHERE id = :r"), dict(r=rid))
    return rid


# --- cancel (R3) ------------------------------------------------------------------------------------------

def test_a_queued_run_is_cancelled_with_the_persons_name(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    queries.cancel(engine, rid, by="Ada Reviewer")
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "failed"
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
        "cancelled: cancelled by Ada Reviewer before it started"


def test_a_waiting_run_is_cancelled_with_the_persons_name(engine):
    rid = waiting_run(engine)
    queries.cancel(engine, rid, by="  Ada Reviewer ")
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
        "cancelled: cancelled by Ada Reviewer while waiting for confirmation of the question as tested"


@pytest.mark.parametrize("status", ["running", "failed"])
def test_a_started_or_ended_run_is_not_cancelled(engine, status):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    set_status(engine, rid, "running")
    if status == "failed":
        set_status(engine, rid, "failed")
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, rid, by="Ada Reviewer")
    assert refused.value.code == "not_cancellable"
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == status


@pytest.mark.parametrize("by", ["", "   ", "x" * 201, None])
def test_a_cancel_names_the_person(engine, by):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, rid, by=by)
    assert refused.value.code == "name_required"
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"


def test_cancelling_an_unknown_run_is_refused(engine):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.cancel(engine, 999, by="Ada Reviewer")
    assert refused.value.code == "unknown_run"


# --- dispatch again (R2; PRD 8 and 14.4: a failed run is dispatched again as a new run) -----------------------

def test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded(engine):
    q = submitted(engine)
    first = queries.dispatch(engine, q.version_id, fixed_plan=True, ceiling=Decimal("0.5"))
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    again = queries.dispatch_again(engine, q.number)
    assert again != first
    with engine.connect() as conn:
        row = conn.execute(text("SELECT status, hypothesis_version_id, fixed_plan, experiment_flags, spending_ceiling "
                                "FROM run WHERE id = :r"), dict(r=again)).one()
    assert (row.status, row.hypothesis_version_id, row.fixed_plan, row.experiment_flags) == (
        "queued", q.version_id, True, {})
    assert row.spending_ceiling is None  # a ceiling is given with each dispatch, never inherited


@pytest.mark.parametrize("status", ["queued", "running", "waiting"])
def test_dispatch_again_is_refused_while_another_run_of_the_query_is_open(engine, status):
    if status == "waiting":
        rid = waiting_run(engine)
        number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                             "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=rid)
    else:
        q = submitted(engine)
        rid, number = queries.dispatch(engine, q.version_id), q.number
        if status == "running":
            set_status(engine, rid, "running")
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, number)
    assert (refused.value.code, refused.value.reason) == (
        "already_open", "another run of this query is queued, waiting or running")
    assert one(engine, "SELECT count(*) FROM run") == 1


def test_dispatch_again_needs_a_dispatched_query(engine):
    q = submitted(engine)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, q.number)
    assert refused.value.code == "not_dispatched"


def test_a_marked_test_run_is_dispatched_again_marked(engine):
    q = submitted(engine, sources=("mpea", "controlled_duplicates"))
    first = queries.dispatch(engine, q.version_id, constructed_test_data=True)
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    again = queries.dispatch_again(engine, q.number)
    assert one(engine, "SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = :r", r=again) == "true"


# --- the ceiling stored at dispatch (R5) ------------------------------------------------------------------

def test_the_ceiling_is_stored_at_dispatch(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id, ceiling=Decimal("0.25"))
    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("0.25")


@pytest.mark.parametrize("ceiling", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_a_ceiling_is_a_positive_amount(engine, ceiling):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, submitted(engine).version_id, ceiling=ceiling)
    assert refused.value.code == "invalid_ceiling"


def _call_run(engine, ceiling):
    """A running run with the code's settings recorded and an open Planner stage and invocation."""
    rid = queries.dispatch(engine, submitted(engine).version_id, ceiling=ceiling)
    queries.start(engine, rid)
    from hypocurate.pipeline.agents.runstage import open_stage
    _, inv = open_stage(engine, rid, "planner", "planner")
    return rid, inv


def test_the_stored_ceiling_holds_when_the_caller_names_none(engine):
    """After a crash or a restart, the request path reads the ceiling from the run, not from a caller's memory."""
    rid, inv = _call_run(engine, Decimal("0.10"))
    spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"))
    assert refused.value.code == "ceiling_reached"


def test_the_lower_of_the_stored_and_the_given_ceiling_holds(engine):
    rid, inv = _call_run(engine, Decimal("1.00"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.06"), Decimal("0.05"))
    assert refused.value.code == "ceiling_reached"
    rid2, inv2 = _call_run(engine, Decimal("0.05"))
    with pytest.raises(spend.SpendingRefused):
        spend.reserve(engine, inv2, "claude-opus-5-5", Decimal("0.06"), Decimal("1.00"))


def test_without_a_ceiling_the_run_cap_holds(engine):
    rid, inv = _call_run(engine, None)
    spend.reserve(engine, inv, "claude-opus-5-5", Decimal("1.5"))
    with pytest.raises(spend.SpendingRefused) as refused:
        spend.reserve(engine, inv, "claude-opus-5-5", Decimal("0.6"))
    assert refused.value.code == "spending_cap_run"


# --- the monthly cap blocks dispatch (R5; PRD 8, 9.3) -----------------------------------------------------

def _spend_this_month(engine, amount):
    rid, inv = _call_run(engine, None)
    with engine.begin() as conn:  # other runs' calls, counted as the caps count them (cost, or maximum while unknown)
        for _ in range(int(amount // Decimal("2"))):
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, 'claude-opus-5-5', "
                              "'p', 2 FROM agent_invocation WHERE id = :i"), dict(i=inv))
        rest = amount % Decimal("2")
        if rest:
            conn.execute(text("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, "
                              "price_table_version, max_cost) SELECT run_id, stage_result_id, id, role, 'claude-opus-5-5', "
                              "'p', :m FROM agent_invocation WHERE id = :i"), dict(i=inv, m=rest))


def test_dispatch_is_refused_once_the_months_calls_reach_the_monthly_cap(engine):
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    q = submitted(engine)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, q.version_id)
    assert (refused.value.code, refused.value.reason) == ("month_cap_reached", MONTH_CAP_REASON)
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=q.version_id) == "submitted"


def test_dispatch_is_allowed_below_the_monthly_cap(engine):
    _spend_this_month(engine, spend.MONTH_CAP_USD - Decimal("0.01"))
    rid = queries.dispatch(engine, submitted(engine).version_id)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"


def test_dispatch_again_is_refused_at_the_monthly_cap(engine):
    q = submitted(engine)
    first = queries.dispatch(engine, q.version_id)
    set_status(engine, first, "running")
    set_status(engine, first, "failed")
    _spend_this_month(engine, spend.MONTH_CAP_USD)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch_again(engine, q.number)
    assert refused.value.code == "month_cap_reached"


# --- constructed test data (owner, Q6) --------------------------------------------------------------------

def test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test(engine):
    q = submitted(engine, sources=("mpea", "controlled_duplicates"))
    with pytest.raises(queries.QueryRefused) as refused:
        queries.dispatch(engine, q.version_id)
    assert (refused.value.code, refused.value.reason) == (
        "constructed_source_unmarked",
        "controlled_duplicates is constructed test data; dispatch it only as a marked test run")
    assert one(engine, "SELECT count(*) FROM run") == 0
    rid = queries.dispatch(engine, q.version_id, constructed_test_data=True)
    assert one(engine, "SELECT experiment_flags->>'constructed_test_data' FROM run WHERE id = :r", r=rid) == "true"


def test_a_constructed_source_not_chosen_does_not_refuse_dispatch(engine):
    rid = queries.dispatch(engine, submitted(engine).version_id)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
```
### `tests/test_resume_step9a.py`

```python
"""Step 9a: the orchestrator takes every step from what is stored, so a run stopped between steps is taken up again
where it stopped, never repeating a step whose result is stored, and never repeating an agent stage that exists
(owner's approval of the step 9 plan, 2026-10-08: a3 and Q3). Stops are made by calling the steps one by one, as
the orchestrator does, and then calling `proceed` (or `prepare`) as a later process would. Step 9b adds the stops
made by killing the worker."""
from __future__ import annotations

import pytest
from sqlalchemy import text

import stub_provider as sp
import test_orchestrator as to
from hypocurate.pipeline import checkpoints, checks, completion, confirmation, extract, inclusion, orchestrator
from hypocurate.pipeline import queries
from test_confirmation import engine, stub  # noqa: F401 (fixtures)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def stages(engine, rid):
    return one(engine, "SELECT string_agg(stage || ':' || status, ',' ORDER BY id) FROM stage_result WHERE run_id = :r",
               r=rid)


def kw(stub):
    return dict(client_options=sp.client_options(stub))


def reference(engine, stub):
    """An uninterrupted fixed-plan run's stored results, to compare with."""
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert orchestrator.run(engine, rid, **kw(stub)).status == "completed"
    return results(engine, rid)


def results(engine, rid):
    """The plan's content less its query version, the outcome and every analysis result. (The fingerprints are not
    compared: they include the query version, which differs between the two runs, step 8b open item 3.)"""
    with engine.connect() as conn:
        return ({k: v for k, v in conn.execute(text("SELECT content FROM plan WHERE run_id = :r"),
                                                dict(r=rid)).scalar().items() if k != "hypothesis_version"},
                conn.execute(text("SELECT outcome, verdict, evidence_level FROM run WHERE id = :r"), dict(r=rid)).one(),
                [tuple(r) for r in conn.execute(text(
                    "SELECT scope, n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM "
                    "analysis_result WHERE run_id = :r ORDER BY scope, n_records, estimate"), dict(r=rid)).all()])


def fixed_run_to_lock(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    assert orchestrator.prepare(engine, rid, **kw(stub)).ready
    with engine.connect() as conn:
        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
    return rid


@pytest.mark.parametrize("stop", ["after_lock", "between_sources", "after_checks", "after_critic", "after_inclusion",
                                  "after_freeze", "after_statistics", "after_analyst"])
def test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results(engine, stub, stop):
    expected = reference(engine, stub)
    rid = fixed_run_to_lock(engine, stub)
    order = ["between_sources", "after_checks", "after_critic", "after_inclusion", "after_freeze",
             "after_statistics", "after_analyst"]
    steps = order[:order.index(stop) + 1] if stop != "after_lock" else []
    from hypocurate.pipeline import analysis
    from hypocurate.pipeline.agents import analyst, critic
    for step in steps:
        if step == "between_sources":  # one source stored, the other still pending
            with engine.connect() as conn:
                key = conn.execute(text("SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE "
                                        "rs.run_id = :r AND rs.search_status = 'pending' ORDER BY s.key LIMIT 1"),
                                   dict(r=rid)).scalar()
            extract.store_source(engine, rid, key)
        elif step == "after_checks":
            extract.store_records(engine, rid)
            checks.run_checks(engine, rid)
        elif step == "after_critic":
            critic.run_critic(engine, rid, **kw(stub))
        elif step == "after_inclusion":
            inclusion.decide_run(engine, rid)
        elif step == "after_freeze":
            checkpoints.freeze_dataset(engine, rid)
        elif step == "after_statistics":
            analysis.run_statistics(engine, rid)
        elif step == "after_analyst":
            analyst.run_analyst(engine, rid, **kw(stub))
    before = stages(engine, rid)
    requests = len(stub.requests)
    report = orchestrator.proceed(engine, rid, **kw(stub))
    assert (report.status, report.failure) == ("completed", None), report
    assert results(engine, rid) == expected
    after = stages(engine, rid)
    assert after.startswith(before or "")  # nothing stored before the stop is touched
    for name in ("checks", "inclusion", "dataset_freeze", "statistics", "critic", "analyst"):
        assert after.count(f"{name}:") == 1, (name, after)  # never a step twice
    if stop == "after_analyst":
        assert len(stub.requests) == requests  # the Analyst is not asked again


def test_a_completed_run_is_left_as_it_is(engine, stub):
    stub.respond(to.responder())
    rid = to.dispatched(engine, fixed_plan=True)
    orchestrator.run(engine, rid, **kw(stub))
    before, requests = stages(engine, rid), len(stub.requests)
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert (report.status, report.ready) == ("completed", False)
    assert stages(engine, rid) == before and len(stub.requests) == requests


def test_a_done_planner_stage_is_used_and_the_planner_is_not_asked_again(engine, stub):
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    planner.run_planner(engine, rid, **kw(stub))  # the stop: after the Planner, before the narrowing decision
    assert len(stub.requests) == 1
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.status == "waiting" and len(stub.requests) == 1
    assert stages(engine, rid) == "planner:done,narrowing:done"


def test_a_stored_narrowing_decision_is_used_and_not_taken_again(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import planner
    stub.respond(to.responder(to.planner_body()))
    rid = to.dispatched(engine)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid, **kw(stub))
    narrowing.run_narrowing(engine, rid, result.answer)  # the stop: before the wait
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.status == "waiting"
    assert stages(engine, rid) == "planner:done,narrowing:done"


def test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question(engine, stub):
    from hypocurate.pipeline import narrowing
    from hypocurate.pipeline.agents import analyst, planner
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid, **kw(stub))
    decision = narrowing.run_narrowing(engine, rid, result.answer)
    analyst.run_analyst(engine, rid, **kw(stub))
    completion.copy_partly_sufficient(engine, rid)  # the stop: completed, no narrower question yet
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
    requests = len(stub.requests)
    report = orchestrator.prepare(engine, rid, **kw(stub))
    assert report.narrower_question and len(stub.requests) == requests
    again = orchestrator.prepare(engine, rid, **kw(stub))
    assert again.narrower_question in (None, report.narrower_question)
    q = queries.create_narrower(engine, rid, decision["narrower_scope"])  # a later call never makes a second one
    assert q.number == report.narrower_question
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 1
    assert one(engine, "SELECT hv.status FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
                       "WHERE h.narrower_of_run_id = :r", r=rid) == "submitted"


def test_a_narrower_question_left_as_a_draft_by_a_stop_is_submitted(engine, stub):
    stub.respond(to.responder(to.PARTLY))
    rid = to.dispatched(engine, claim=to.PARTLY_CLAIM)
    report = to.run(engine, rid, stub)
    vid = queries.submitted_version(engine, report.narrower_question)
    with engine.begin() as conn:  # as if the stop came between create and submit
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        conn.execute(text("UPDATE hypothesis_version SET status = 'draft', submitted_at = NULL WHERE id = :v"),
                     dict(v=vid))
    decision = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid)
    q = queries.create_narrower(engine, rid, decision["narrower_scope"])
    assert q.version_id == vid
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=vid) == "submitted"


def test_a_run_whose_primary_set_is_empty_is_taken_up_after_inclusion_without_deciding_again(engine, stub):
    """Inclusion's own guard reads the run's eligibility rows, which a run with no eligible record may not have; the
    orchestrator reads Inclusion's stored stage instead (step 9 design, the idempotency audit)."""
    from hypocurate.pipeline.agents import critic
    stub.respond(to.responder(to.BCC))
    rid = to.dispatched(engine, claim=to.BCC_CLAIM)
    assert orchestrator.run(engine, rid, **kw(stub)).status == "waiting"
    confirmation.confirm(engine, rid, by="Ada Reviewer")
    orchestrator._go_on(engine, rid)
    with engine.connect() as conn:
        checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    critic.run_critic(engine, rid, **kw(stub))
    inclusion.decide_run(engine, rid)  # the stop
    report = orchestrator.proceed(engine, rid, **kw(stub))
    assert (report.status, report.outcome, report.failure) == ("completed", "insufficient", None)
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'inclusion'", r=rid) == 1
```
## 4. Changed tests and test helpers (diff)

```diff
diff --git a/tests/access_world.py b/tests/access_world.py
index d480c23..db3e261 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -184,6 +184,7 @@ def planted_plan() -> dict:
 def lock(w: World, run: int) -> None:
     ys = PLANTED["yield_strength"]
     content = planted_plan()
+    w.confirm_rules(run)  # step 9a (0007; owner, Q4): a narrower question's plan is confirmed by a person first
     sql(w, "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
            "min_groups, min_resid_df, power_assumptions) VALUES (:r, :j_c, :fp, 'fixed_minimum', 4, 1, 2, 1, :j_p)",
         r=run, j_c=content, fp=FP, j_p={"method": "information_only", "scatter": 60.0, "note": f"{ys}",
@@ -270,6 +271,7 @@ def build(engine, stage_name: str) -> AccessWorld:
     w.confirm(vid)
     w.dispatch_version(vid)
     earlier = w.running(vid=vid, sources=("mpea", "tamu_fcc"))
+    w.confirm_rules(earlier)  # step 9a (0007; owner, Q4)
     w.lock(earlier, content=planted_plan())
     store_value_records(w, earlier, OTHER)
     stage(w, earlier, "curator", "curator", f"saw {OTHER}")
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 06e594d..26da84d 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -190,6 +190,15 @@ class World:
                 conn.execute(text("INSERT INTO run_tag VALUES (:r, :t)"), dict(r=rid, t=tag))
         return pid
 
+    def confirm_rules(self, rid, fp=FP, planner=None, narrowed=None, by="Ada Reviewer"):
+        """Step 9a (0007; owner, Q1, Q4): a run whose plan comes from the Planner or a narrower question waits, a named
+        person confirms exactly the plan to be locked (its fingerprint), and the run goes on to the lock."""
+        self.run_sql("UPDATE run SET status = 'waiting' WHERE id = :r", r=rid)
+        self.run_sql("INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
+                     "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, '{}', 'shown')",
+                     r=rid, b=by, fp=fp, p=planner, n=narrowed)
+        self.run_sql("UPDATE run SET status = 'running' WHERE id = :r", r=rid)
+
     def search(self, rid, source="mpea", status="searched", nothing_found=None, reason=None):
         self.run_sql("UPDATE run_source SET search_status = :st, nothing_found = :nf, failure_reason = :fr, "
                      "decided_at = now() WHERE run_id = :r AND source_id = :s",
diff --git a/tests/test_access_dispatch.py b/tests/test_access_dispatch.py
index 5341011..de97790 100644
--- a/tests/test_access_dispatch.py
+++ b/tests/test_access_dispatch.py
@@ -225,6 +225,7 @@ def test_a_rules_lock_committed_while_a_read_waits_closes_the_planner(engine, ru
     if run_kind == "narrower_question":
         world = aw.build(engine, "before_lock")
         run_id, content = world.run, aw.planted_plan()
+        world.w.confirm_rules(run_id)  # step 9a (0007; owner, Q4): confirmed by a person before the race
         planner = bind(engine, run_id, world.settings["planner"])  # bound before the lock, as a running call is
         read = lambda: role_input(planner)  # noqa: E731
     else:
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 60d4156..09ba857 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -262,9 +262,12 @@ def test_the_step_6_decisions_carry_the_owners_wording():
         # reworded sensitivity_one_change and eligibility_rule_order, each with its 2026-10-05 wording in history.
         changed = ("conflicts_not_pooled", "sensitivity_one_change", "eligibility_rule_order")
         # Step 8b (owner, 2026-10-07): code_role_access reworded for the narrowing role, its 2026-10-05 wording in history.
-        date = "2026-10-07" if key == "code_role_access" else "2026-10-06" if key in changed else "2026-10-05"
+        # Step 9a (owner, 2026-10-08, Q6): constructed_test_runs reworded for the refusal at dispatch, its 2026-10-05
+        # wording in history.
+        date = ("2026-10-08" if key == "constructed_test_runs" else "2026-10-07" if key == "code_role_access"
+                else "2026-10-06" if key in changed else "2026-10-05")
         assert e["decided"] == {"by": OWNER, "date": date} and e["expert_review"]["status"] == "not_reviewed"
-        if key in changed[1:] + ("code_role_access",):
+        if key in changed[1:] + ("code_role_access", "constructed_test_runs"):
             assert e["history"][-1]["from"] == "2026-10-05"
 
 
diff --git a/tests/test_cli_runs.py b/tests/test_cli_runs.py
index 90b4fe4..68943e7 100644
--- a/tests/test_cli_runs.py
+++ b/tests/test_cli_runs.py
@@ -40,6 +40,21 @@ def hc(capsys, *argv):
     return code, out, err
 
 
+def hc_confirmed(capsys, *argv):
+    """`run` or `dispatch`; step 9a (0007; owner, Q1, Q4): a run that waits at the rules lock is confirmed by a named
+    person (`confirm <run> --by`), which prints what is confirmed and then the report. The output given back is the
+    command's dispatch line and reading, then the report printed by `confirm` (the same shape as before)."""
+    code, out, err = hc(capsys, *argv)
+    first, reading, rest = out.split("\n", 2)
+    if code != 0 or json.loads(rest).get("status") != "waiting":
+        return code, out, err
+    run_id = json.loads(first)["run"]
+    code, confirmed, err = hc(capsys, "confirm", str(run_id), "--by", "Ada Reviewer")
+    report = json.loads(confirmed[confirmed.index("\n{") + 1:])
+    report["stages"] = json.loads(rest)["stages"] + report["stages"]  # the stages of both commands, as before
+    return code, f"{first}\n{reading}\n{json.dumps(report, indent=2, ensure_ascii=False)}", err
+
+
 def report_of(out: str) -> dict:
     """The run's report: the dispatch line, then (fix round 1, decision B) the claim and the question as tested,
     printed before the run goes on to the rules lock, then the report."""
@@ -74,7 +89,7 @@ def test_14_1a_run_with_the_fixed_plan_and_show_it(engine, stub, capsys):
 
 def test_14_1b_run_with_the_planner(engine, stub, capsys):
     stub.respond(responder(planner_body()))
-    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
+    code, out, err = hc_confirmed(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
     r = report_of(out)
     assert code == 0 and r["report"]["outcome_code"] == "sufficient" and "planner" in r["report"]["stages"]
     assert guard_refusals(engine, r["run"]) == []
@@ -82,7 +97,7 @@ def test_14_1b_run_with_the_planner(engine, stub, capsys):
 
 def test_14_3_the_bcc_claim_from_the_command_line(engine, stub, capsys):
     stub.respond(responder(BCC))
-    code, out, err = hc(capsys, "run", BCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
+    code, out, err = hc_confirmed(capsys, "run", BCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
     r = report_of(out)
     assert code == 0 and r["report"]["outcome_code"] == "insufficient"
     shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
@@ -100,7 +115,7 @@ def test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line(
     shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
     assert shown["outcome"] == "partly sufficient in the sources searched" and shown["narrower_question"] == number
     assert shown["evidence_level_wording"] == "original question not tested; a narrower question was proposed"
-    code, out, err = hc(capsys, "dispatch", number, "--by", "Ada Reviewer")
+    code, out, err = hc_confirmed(capsys, "dispatch", number, "--by", "Ada Reviewer")
     n = report_of(out)
     assert code == 0 and n["report"]["outcome_code"] == "sufficient" and n["report"]["stages"][0] == "fixed plan"
     narrower = json.loads(hc(capsys, "show", str(n["run"]))[1])
@@ -267,7 +282,7 @@ def test_run_dispatch_and_show_print_the_statement_then_the_labelled_analyst_tex
     shown = json.loads(out)
     assert_presented(out, shown, explanation)
     assert {k: v for k, v in r["report"].items() if k not in ("stages", "run_failure")} == shown
-    code, out, err = hc(capsys, "dispatch", r["report"]["narrower_question"], "--by", "Ada Reviewer")
+    code, out, err = hc_confirmed(capsys, "dispatch", r["report"]["narrower_question"], "--by", "Ada Reviewer")
     n = report_of(out)
     assert_presented(out.split("\n", 2)[2], n["report"], stored_explanation(engine, n["run"]))
     assert n["report"]["statement"][-1].startswith("Statement format ")
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 7e86c38..2cb02fd 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -64,6 +64,9 @@ def expected_triggers() -> set[tuple[str, str]]:
     names |= {(t, f) for t, _, f in m5.CHECKED}
     m6 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0006").module  # step 8b
     names |= {(t, trigger) for t, _, trigger, _ in m6.CHECKED}
+    m7 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0007").module  # step 9a
+    names |= {(t, f"hc_{t}_append_only") for t in m7.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m7.APPEND_ONLY}
+    names |= {(t, trigger) for t, _, trigger, _ in m7.CHECKED}
     return names
 
 
diff --git a/tests/test_migrations_step8b.py b/tests/test_migrations_step8b.py
index 58fc1bf..1aa1633 100644
--- a/tests/test_migrations_step8b.py
+++ b/tests/test_migrations_step8b.py
@@ -47,8 +47,9 @@ def w(db):
 
 # --- the migration -------------------------------------------------------------------------------
 
-def test_0006_is_the_head_and_follows_0005():
-    assert migrate.head_revision() == "0006" and m0006().down_revision == "0005"
+def test_0006_follows_0005():
+    # Step 9a: 0007 is now the head (tests/test_migrations_step9a.py).
+    assert m0006().down_revision == "0005"
 
 
 def test_0006_replaces_no_earlier_function():
@@ -104,7 +105,8 @@ def test_the_downgrade_refuses_while_a_query_uses_another_option(db):
     before = snapshot(db)
     with pytest.raises(Exception, match="0006 is in use"):
         migrate.downgrade(db, "0005")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0006"
+    # Step 9a: the database stays at the head, now 0007 (0007's own downgrade is undone with the refused transaction).
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
 
 
 # --- the query's sufficiency option (A2) ---------------------------------------------------------
@@ -308,6 +310,7 @@ def test_a_narrower_questions_run_must_use_the_stored_plan(w):
 def test_a_narrower_questions_plan_equal_to_the_stored_narrower_plan_is_locked(w):
     vid = narrower_version(w, partly_original(w))
     rid = w.running(vid=vid)
+    w.confirm_rules(rid)  # step 9a (0007; owner, Q4): a narrower question's plan is confirmed by a person first
     w.lock(rid, content={"hypothesis_version": vid, **BODY})
     assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
 
@@ -354,6 +357,7 @@ def test_the_source_versions_are_compared_whatever_their_stored_order(w):
     w.complete(original, "partly_sufficient", level=1)
     vid = narrower_version(w, original)
     rid = w.running(vid=vid)
+    w.confirm_rules(rid)  # step 9a (0007; owner, Q4)
     w.lock(rid, content={"hypothesis_version": vid, **BODY})
     assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
 
diff --git a/tests/test_orchestrator.py b/tests/test_orchestrator.py
index cc565e3..6818563 100644
--- a/tests/test_orchestrator.py
+++ b/tests/test_orchestrator.py
@@ -95,7 +95,17 @@ def dispatched(engine, claim=FCC_CLAIM, fixed_plan=False, sufficiency="fixed_min
 
 
 def run(engine, rid, stub, **kw):
-    return orchestrator.run(engine, rid, client_options=sp.client_options(stub), **kw)
+    """The run to its end. Step 9a (0007; owner, Q1, Q4): a run whose plan comes from the Planner or a narrower
+    question waits at the rules lock; a named person confirms it here, and the rest runs (stages joined)."""
+    report = orchestrator.run(engine, rid, client_options=sp.client_options(stub), **kw)
+    if report.status != "waiting":
+        return report
+    from hypocurate.pipeline import confirmation
+    confirmation.confirm(engine, rid, by="Ada Reviewer")
+    rest = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub), **kw)
+    rest.stages = report.stages + rest.stages
+    rest.question_as_tested = report.question_as_tested
+    return rest
 
 
 def one(engine, sql, **params):
@@ -288,14 +298,17 @@ def test_finding_1_the_orchestrator_reads_the_narrower_link_not_the_runs_flag(en
     assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0
 
 
-def test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested(engine, stub):
-    """What the command line prints between its two calls: the run is prepared and nothing is locked yet."""
+def test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested_and_waits(engine, stub):
+    """What the command line prints between its two calls: the run is prepared and nothing is locked yet. Step 9a
+    (owner, Q1): it now waits there for a named person; once confirmed, the rest runs from the rules lock."""
     stub.respond(responder(planner_body()))
     rid = dispatched(engine)
     prepared = orchestrator.prepare(engine, rid, client_options=sp.client_options(stub))
-    assert prepared.ready and prepared.status == "running"
+    assert not prepared.ready and prepared.status == "waiting"
     assert prepared.question_as_tested["source"] == "planner"
     assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+    from hypocurate.pipeline import confirmation
+    confirmation.confirm(engine, rid, by="Ada Reviewer")
     rest = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
     assert (rest.status, rest.outcome) == ("completed", "sufficient") and rest.stages[0] == "rules lock"
 
diff --git a/tests/test_statement.py b/tests/test_statement.py
index b24b0c4..54378b2 100644
--- a/tests/test_statement.py
+++ b/tests/test_statement.py
@@ -59,7 +59,12 @@ def run_claim(engine, stub, claim=FCC_CLAIM, fixed_plan=False, analyst=None, pla
     queries.submit(engine, q.version_id)
     queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
     rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)
-    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))
+    report = orchestrator.run(engine, rid, client_options=sp.client_options(stub))
+    if report.status == "waiting":  # step 9a (0007; owner, Q1, Q4): a named person confirms, and the rest runs
+        from hypocurate.pipeline import confirmation
+        confirmation.confirm(engine, rid, by="Ada Reviewer")
+        report = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
+    return report
 
 
 def stored_stats(engine, rid):
@@ -110,7 +115,10 @@ def test_the_statement_is_present_when_the_analyst_fails_and_holds_nothing_it_wr
 def test_a_planner_run_s_statement_labels_the_planner_s_reading(engine, stub):
     report = run_claim(engine, stub, planner_answer=planner_body())
     lines = statement.build(engine, report.run_id)["lines"]
-    assert lines[1].startswith(f"Question as tested ({reading.LABELS['planner']}): yield strength against grain size")
+    # Step 9a (owner, 2026-10-08, question 2): once confirmed, the label says by whom and when.
+    assert lines[1].startswith("Question as tested (the Planner's reading of the claim; not verified by code; "
+                               "confirmed by Ada Reviewer on ")
+    assert " UTC): yield strength against grain size" in lines[1]
     assert reading.LABELS["planner"] == ("the Planner's reading of the claim; not verified by code and, in this "
                                          "version, not confirmed by a person")
     assert "test type tension (assumed: the claim does not state it)" in lines[1]
```
## 5. Assumptions register (143 entries; 5 new, 4 changed)

### New: `rules_confirmation`

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
### New: `resumable_run`

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
### New: `run_cancel`

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
### New: `dispatch_again`

```json
{
 "key": "dispatch_again",
 "name": "A query dispatched again as a new run",
 "state": "in_force",
 "statement": "A query whose runs have all ended is dispatched again as a new queued run of its dispatched version, recording what the version's latest run recorded (fixed plan, test mark); a spending ceiling only as given with the new dispatch. Refused, with 'another run of this query is queued, waiting or running', while any run of the query is open; the monthly cap and the test-data rule apply as at dispatch.",
 "value": {
  "text": "a new run once no run is open",
  "unit": null
 },
 "category": "operational",
 "affects": "PRD 8 and 14.4 ('dispatched again as a new run').",
 "reason": "PRD 8, 14.4; owner's approval of R2.",
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
    "ref": "python:hypocurate.pipeline.queries:REASONS.already_open",
    "equals": "another run of this query is queued, waiting or running"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded",
  "tests/test_queries_step9a.py::test_dispatch_again_is_refused_while_another_run_of_the_query_is_open"
 ],
 "history": [],
 "notes": []
}
```
### New: `dispatch_refusals`

```json
{
 "key": "dispatch_refusals",
 "name": "Dispatch refused at the monthly cap and for unmarked test data",
 "state": "in_force",
 "statement": "Dispatch is refused when this calendar month's counted model calls (UTC; reported cost, or maximum while none is known) have reached the monthly cap: 'this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, or until the owner raises the cap' (the owner's words). Dispatch is refused when a chosen source is constructed test data and the run is not marked as a test: '<source> is constructed test data; dispatch it only as a marked test run'; the storage guard stays as the backstop and still fails the whole run.",
 "value": {
  "text": "two refusals at dispatch",
  "unit": null
 },
 "category": "operational",
 "affects": "Every dispatch (PRD 8, 9.3; register 'constructed_test_runs').",
 "reason": "PRD 8 ('a monthly cap blocks dispatch'); owner's answers R5 and Q6.",
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
    "ref": "python:hypocurate.pipeline.queries:REASONS.month_cap_reached",
    "equals": "this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, or until the owner raises the cap"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:REASONS.constructed_source_unmarked",
    "equals": "{source} is constructed test data; dispatch it only as a marked test run"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_queries_step9a.py::test_dispatch_is_refused_once_the_months_calls_reach_the_monthly_cap",
  "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test"
 ],
 "history": [],
 "notes": []
}
```
### Changed: `spending_caps` (the entry as it now stands; earlier wording in its history)

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
### Changed: `constructed_test_runs` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "constructed_test_runs",
 "name": "Runs with constructed test data",
 "state": "in_force",
 "statement": "Constructed test data (the controlled duplicate extract) enter only a run marked as a test (run.experiment_flags constructed_test_data, set at dispatch). Dispatch refuses a query naming a constructed source unless the run is marked (step 9a, owner Q6); an unmarked run that reaches them anyway refuses them, and logs the refusal, at record storage, inclusion and the freeze. A marked run may freeze, be analysed and complete normally with a verdict; every place its outcome, verdict or numbers are stored or shown carries 'test run: includes constructed data', and marked runs are excluded from every aggregate, count or list of real results.",
 "value": {
  "text": "marked at dispatch; refused otherwise",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Acceptance 14.1 'Duplicates' and the 14.7 demonstration; every list of real results.",
 "reason": "The extract must never enter a real analysis, yet the duplicate handling must be demonstrable end to end.",
 "evidence": [
  "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
  "status": "partly",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.writes:CONSTRUCTED_MARK",
    "equals": "constructed_test_data"
   },
   {
    "ref": "python:hypocurate.db.models:TEST_RUN_LABEL",
    "equals": "test run: includes constructed data"
   },
   {
    "ref": "python:hypocurate.pipeline.results:REAL_RUN"
   }
  ],
  "done": "The mark and the refusals at storage, inclusion and freeze (step 6). Step 7: the label on every stored analysis and calibration result and on the statistics and gap-facts stage results of a marked run (checked by the database for result rows), and one named condition that leaves marked runs out of every aggregate (pipeline/results.py, REAL_RUN).",
  "pending": "The label and the exclusion on every screen and list (step 10).",
  "step": 10,
  "note": "The guard is in code; the database itself does not refuse a constructed record."
 },
 "history": [
  {
   "value": "Constructed test data (the controlled duplicate extract) enter only a run marked as a test (run.experiment_flags constructed_test_data, set at dispatch). An unmarked run refuses them, and logs the refusal, at record storage, inclusion and the freeze. A marked run may freeze, be analysed and complete normally with a verdict; every place its outcome, verdict or numbers are stored or shown carries 'test run: includes constructed data', and marked runs are excluded from every aggregate, count or list of real results.",
   "from": "2026-10-05",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08, Q6): refused at dispatch; the storage guard stays as the backstop."
  }
 ],
 "notes": [
  "Backlog (owner, 2026-10-06; PRD 18 at the next PRD update): a database rule refusing a constructed source's records in a run not marked as a test. The guard stays in code in sprint 1.",
  "Step 6 review (2026-10-06), for a later step: a source whose definition is unknown to the code should fail closed (be treated as constructed, or refused), not pass the guard."
 ],
 "tests": [
  "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates",
  "tests/test_analysis_stage.py::test_a_marked_run_with_no_dataset_frozen_is_labelled_too",
  "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records",
  "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
  "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test"
 ]
}
```
### Changed: `question_as_tested` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "question_as_tested",
 "name": "The question as tested, beside the claim",
 "state": "in_force",
 "statement": "Code writes the question a run tests from its scope and exclusion rules: the outcome against grain size, the alloy class, phase class, test type and temperature band with its range, and each exclusion rule. For a run with the Planner it is the Planner's reading of the claim, each part marked as the claim states it or as assumed, and is labelled 'the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person' until a named person confirms it at the rules lock (step 9a), then 'the Planner's reading of the claim; not verified by code; confirmed by <name> on <UTC time>' (owner, 2026-10-08); another reading's label gains '; confirmed by <name> on <UTC time>'. Code checks only that a part marked as assumed holds the profile's default; it does not check that the reading matches the claim's words. It is stored with the Planner's stage output; for a fixed-plan run ('the fixed reference plan; not read from the claim') or a narrower question's run it is the reading of that plan, labelled as such. The command line prints it beside the original claim after the Planner and the narrowing decision and before the rules lock (`run` and `dispatch` make two guarded calls, the second rebuilding the plan from what is stored), and `show` prints it. Since step 9a a run with the Planner, and a narrower question's run, wait at the lock for that confirmation (register 'rules_confirmation').",
 "value": {
  "text": "code-written; labelled the Planner's reading; confirmed by a person in step 10",
  "unit": null
 },
 "category": "operational",
 "affects": "What a reader is told the run tested; how a wrong reading of the claim can be noticed.",
 "reason": "The second-model review found that claim interpretation is unchecked: a valid plan and a verdict could be attached to the wrong scientific question. Showing the reading prominently, and checking the defaulted marks, is the owner's response for sprint 1; the confirmation by a person comes with the website's rules lock.",
 "evidence": [
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md, 'Claim interpretation'); owner's decision B (2026-10-07)."
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
  "status": "partly",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.reading:LABELS"
   },
   {
    "ref": "python:hypocurate.pipeline.reading:question_as_tested"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.planner:DEFAULT_SCOPE"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:prepare"
   },
   {
    "ref": "python:hypocurate.pipeline.reading:CONFIRMED_LABEL",
    "equals": "the Planner's reading of the claim; not verified by code; confirmed by {by} on {at}"
   }
  ],
  "done": "Step 8b fix round 1: the text and label written by code, stored with the Planner's stage output, the defaulted-mark check, printed by `run`/`dispatch` before the rules lock and by `show`. Step 9a: confirmed by a named person at the rules lock from the command line (`confirm`); the label once confirmed.",
  "pending": "The Confirm button on the website (step 10).",
  "step": 10,
  "note": null
 },
 "history": [
  {
   "value": "Code writes the question a run tests from its scope and exclusion rules: the outcome against grain size, the alloy class, phase class, test type and temperature band with its range, and each exclusion rule. For a run with the Planner it is the Planner's reading of the claim, each part marked as the claim states it or as assumed, and is labelled 'the Planner's reading of the claim; not verified by code; a person confirms it at the rules lock on the website (step 10)'. Code checks only that a part marked as assumed holds the profile's default; it does not check that the reading matches the claim's words. It is stored with the Planner's stage output; for a fixed-plan run or a narrower question's run it is the reading of that plan, labelled as such. The command line prints it beside the original claim after the Planner and the narrowing decision and before the rules lock (`run` and `dispatch` make two guarded calls, the second rebuilding the plan from what is stored), and `show` prints it. Until step 10 no person confirms it: the run goes on to the lock without a confirmation.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, F-Q2: labels say what is true in this version; no step 10 or website in the label."
  },
  {
   "value": "Code writes the question a run tests from its scope and exclusion rules: the outcome against grain size, the alloy class, phase class, test type and temperature band with its range, and each exclusion rule. For a run with the Planner it is the Planner's reading of the claim, each part marked as the claim states it or as assumed, and is labelled 'the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person' (owner, F-Q2: the label says what is true now; the confirmation by a person comes in step 10). Code checks only that a part marked as assumed holds the profile's default; it does not check that the reading matches the claim's words. It is stored with the Planner's stage output; for a fixed-plan run ('the fixed reference plan; not read from the claim') or a narrower question's run it is the reading of that plan, labelled as such. The command line prints it beside the original claim after the Planner and the narrowing decision and before the rules lock (`run` and `dispatch` make two guarded calls, the second rebuilding the plan from what is stored), and `show` prints it. Until step 10 no person confirms it: the run goes on to the lock without a confirmation.",
   "from": "2026-10-07",
   "to": "2026-10-08",
   "note": "Step 9a (owner, 2026-10-08): the confirmation at the rules lock, from the command line; the label once confirmed."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_reading.py::test_the_label_says_whose_reading_it_is_and_that_a_person_confirms_it",
  "tests/test_reading.py::test_each_exclusion_rule_in_words",
  "tests/test_planner_narrowing.py::test_the_planners_stage_stores_the_question_as_tested_labelled_as_its_reading",
  "tests/test_planner_narrowing.py::test_a_part_marked_defaulted_must_hold_the_default",
  "tests/test_orchestrator.py::test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested_and_waits",
  "tests/test_cli_runs.py::test_run_prints_the_claim_and_the_planners_reading_before_the_report_and_show_keeps_it",
  "tests/test_cli_runs.py::test_a_fixed_plan_runs_reading_is_the_reference_plans",
  "tests/test_confirmation.py::test_once_confirmed_the_question_as_tested_says_by_whom_and_when"
 ]
}
```
### Changed: `run_order_and_failures` (the entry as it now stands; earlier wording in its history)

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
## 6. Reference comparison with `main`

Dumped on `main`'s code (`ed46b48`) before any change, twice (byte-identical), and on this head. Byte comparison of every file:

```
head 97bffda
DIFFERENT fixed_plan.json
DIFFERENT narrower.json
DIFFERENT partly_original.json
DIFFERENT planner_bcc.json
DIFFERENT planner_fcc.json
IDENTICAL reference.json
```

Leaf-by-leaf differences of the orchestrator dumps:

```
== fixed_plan: 1 differing leaves
  .run[0].spending_ceiling: "<absent>" -> null
== planner_fcc: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> null
  .show.question_as_tested.label: "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person" -> "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person): yield strength against grain siz -> "Question as tested (the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC): yield strength against gra
== planner_bcc: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> null
  .show.question_as_tested.label: "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person" -> "the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person): yield strength against grain siz -> "Question as tested (the Planner's reading of the claim; not verified by code; confirmed by Ada Reviewer on <time> UTC): yield strength against gra
== partly_original: 1 differing leaves
  .run[0].spending_ceiling: "<absent>" -> null
== narrower: 3 differing leaves
  .run[0].spending_ceiling: "<absent>" -> null
  .show.question_as_tested.label: "the narrower plan stored by the original question's narrowing decision" -> "the narrower plan stored by the original question's narrowing decision; confirmed by Ada Reviewer on <time> UTC"
  .show.statement[1]: "Question as tested (the narrower plan stored by the original question's narrowing decision): yield strength against grain size, in multi-principal-element (hig -> "Question as tested (the narrower plan stored by the original question's narrowing decision; confirmed by Ada Reviewer on <time> UTC): yield streng
```

The SHA-256 sums of `main`'s dumps:

```
ccfdc37be65985e4a7db42f9d31ca6844841fc63eafa9b3d25e818f210e6e2d3  main/fixed_plan.json
237318317d74424877efca2e8d9d5f582ce45aabc5ad9aa2b224f8b17d1517ea  main/narrower.json
aa63b22cf650c3eafc147a7888ea3a3b084d27c6cedd6e6b5e7ff590d58a61b1  main/partly_original.json
c3568603f98523399fc073b8e27a43f15d4e2f289a82ddb3ffa57d6c7ab04fd9  main/planner_bcc.json
e44746449c178f90000f2374d3e79341b70da18ffbbc9ddd06721f7a7e05a7be  main/planner_fcc.json
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
    out["show"] = json.loads(json.dumps(shown, default=str))
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
## 7. Mutation checks

The first run (three survivors, each then given a test; see the summary):

```
d01      CAUGHT  1 failed, 52 passed in 15.33s
d02      CAUGHT  1 failed, 52 passed in 16.10s
d03      CAUGHT  5 failed, 48 passed in 16.42s
d04      CAUGHT  4 failed, 49 passed in 15.53s
d05      CAUGHT  1 failed, 52 passed in 15.27s
d06      CAUGHT  1 failed, 52 passed in 15.40s
d07      CAUGHT  2 failed, 51 passed in 21.39s
d08      CAUGHT  1 failed, 52 passed in 16.43s
d09      CAUGHT  1 failed, 52 passed in 15.68s
c01      CAUGHT  2 failed, 21 passed in 61.32s (0:01:01)
c02      CAUGHT  1 failed, 22 passed in 61.92s (0:01:01)
c03      SURVIVED  23 passed in 61.85s (0:01:01)
c04      CAUGHT  1 failed, 22 passed in 61.59s (0:01:01)
c05      CAUGHT  1 failed, 22 passed in 62.14s (0:01:02)
c06      SURVIVED  23 passed in 61.10s (0:01:01)
c07      CAUGHT  1 failed, 22 passed in 54.51s
o01      CAUGHT  2 failed, 21 passed in 54.84s
o02      CAUGHT  19 failed, 4 passed in 43.55s
o03      CAUGHT  1 failed, 22 passed in 59.74s
o04      SURVIVED  48 passed in 136.65s (0:02:16)
o05      CAUGHT  2 failed, 12 passed in 110.12s (0:01:50)
o06      CAUGHT  1 failed, 13 passed in 110.12s (0:01:50)
o07      CAUGHT  5 failed, 9 passed in 109.65s (0:01:49)
o08      CAUGHT  5 failed, 9 passed in 104.68s (0:01:44)
o09      CAUGHT  2 failed, 12 passed in 121.47s (0:02:01)
o10      CAUGHT  1 failed, 13 passed in 128.48s (0:02:08)
o11      CAUGHT  1 failed, 13 passed in 132.38s (0:02:12)
o12      CAUGHT  7 failed, 7 passed in 103.90s (0:01:43)
q01      CAUGHT  2 failed, 26 passed in 14.15s
q02      CAUGHT  1 failed, 27 passed in 11.16s
q03      CAUGHT  1 failed, 27 passed in 11.13s
q04      CAUGHT  1 failed, 27 passed in 11.42s
q05      CAUGHT  2 failed, 12 passed in 115.95s (0:01:55)
q06      CAUGHT  1 failed, 13 passed in 115.90s (0:01:55)
q07      CAUGHT  2 failed, 26 passed in 11.12s
s01      CAUGHT  2 failed, 26 passed in 11.05s
s02      CAUGHT  1 failed, 27 passed in 11.09s
l01      CAUGHT  1 failed, 8 passed in 101.74s (0:01:41)
l02      CAUGHT  1 failed, 8 passed in 100.93s (0:01:40)
control  clean  127 passed in 298.35s (0:04:58)
```

All re-run on the final tests, a control run with no mutation last:

```
d01      CAUGHT  1 failed, 52 passed in 18.08s
d02      CAUGHT  1 failed, 52 passed in 17.68s
d03      CAUGHT  5 failed, 48 passed in 18.37s
d04      CAUGHT  4 failed, 49 passed in 17.37s
d05      CAUGHT  1 failed, 52 passed in 16.40s
d06      CAUGHT  1 failed, 52 passed in 16.77s
d07      CAUGHT  2 failed, 51 passed in 16.66s
d08      CAUGHT  1 failed, 52 passed in 16.47s
d09      CAUGHT  1 failed, 52 passed in 16.46s
c01      CAUGHT  2 failed, 24 passed in 69.06s (0:01:09)
c02      CAUGHT  1 failed, 25 passed in 68.36s (0:01:08)
c03      CAUGHT  1 failed, 25 passed in 68.60s (0:01:08)
c04      CAUGHT  1 failed, 25 passed in 69.05s (0:01:09)
c05      CAUGHT  1 failed, 25 passed in 67.39s (0:01:07)
c06      CAUGHT  1 failed, 25 passed in 68.54s (0:01:08)
c07      CAUGHT  1 failed, 25 passed in 63.08s (0:01:03)
o01      CAUGHT  2 failed, 24 passed in 62.71s (0:01:02)
o02      CAUGHT  21 failed, 5 passed in 50.75s
o03      CAUGHT  1 failed, 25 passed in 69.27s (0:01:09)
o04      CAUGHT  1 failed, 50 passed in 153.66s (0:02:33)
o05      CAUGHT  2 failed, 12 passed in 120.47s (0:02:00)
o06      CAUGHT  1 failed, 13 passed in 119.85s (0:01:59)
o07      CAUGHT  5 failed, 9 passed in 115.76s (0:01:55)
o08      CAUGHT  5 failed, 9 passed in 110.77s (0:01:50)
o09      CAUGHT  2 failed, 12 passed in 120.00s (0:01:59)
o10      CAUGHT  1 failed, 13 passed in 117.60s (0:01:57)
o11      CAUGHT  1 failed, 13 passed in 116.80s (0:01:56)
o12      CAUGHT  7 failed, 7 passed in 103.07s (0:01:43)
q01      CAUGHT  2 failed, 26 passed in 11.52s
q02      CAUGHT  1 failed, 27 passed in 11.54s
q03      CAUGHT  1 failed, 27 passed in 11.61s
q04      CAUGHT  1 failed, 27 passed in 11.56s
q05      CAUGHT  2 failed, 12 passed in 118.31s (0:01:58)
q06      CAUGHT  1 failed, 13 passed in 117.31s (0:01:57)
q07      CAUGHT  2 failed, 26 passed in 11.58s
s01      CAUGHT  2 failed, 26 passed in 11.26s
s02      CAUGHT  1 failed, 27 passed in 11.41s
l01      CAUGHT  1 failed, 8 passed in 104.96s (0:01:44)
l02      CAUGHT  1 failed, 8 passed in 103.44s (0:01:43)
control  clean  130 passed in 302.86s (0:05:02)
```

The specification and the runner:

```python
"""Every step 9a mutation (scratch copy, PYTHONPATH). Each: (id, file under hypocurate/, old, new, tests). A mutation
is caught when at least one named test fails."""
T = "/workspaces/hypocurate/tests/"
M07 = "db/migrations/versions/0007_rules_confirmation.py"
MIG, Q, C, R, CLI = ["test_migrations_step9a.py"], ["test_queries_step9a.py"], ["test_confirmation.py"], \
    ["test_resume_step9a.py"], ["test_cli_step9a.py"]
MUTATIONS = [
 # Migration 0007
 ("d01", M07, "        IF OLD.status = 'waiting' AND NEW.status = 'running'\n", "        IF false AND OLD.status = 'waiting' AND NEW.status = 'running'\n", MIG),
 ("d02", M07, "WHERE run_id = NEW.run_id AND plan_fingerprint = NEW.fingerprint) THEN", "WHERE run_id = NEW.run_id) THEN", MIG),
 ("d03", M07, "            OR EXISTS (SELECT 1 FROM run r JOIN", "            OR false AND EXISTS (SELECT 1 FROM run r JOIN", MIG),
 ("d04", M07, "        IF decision IS NULL OR stored IS DISTINCT FROM current THEN", "        IF decision IS NULL THEN", MIG),
 ("d05", M07, "               OR NEW.narrowing_stage_result_id IS DISTINCT FROM (", "               OR false AND NEW.narrowing_stage_result_id IS DISTINCT FROM (", MIG),
 ("d06", M07, "        IF NEW.spending_ceiling IS DISTINCT FROM OLD.spending_ceiling THEN", "        IF false THEN", MIG),
 ("d07", M07, "            IF NOT {NEEDS_CONFIRMATION.format(run='NEW.id')} THEN", "            IF false THEN", MIG),
 ("d08", M07, "            IF EXISTS (SELECT 1 FROM rules_confirmation WHERE run_id = NEW.id) THEN", "            IF false THEN", MIG),
 ("d09", M07, "        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'waiting' THEN", "        IF hc_lock_run(NEW.run_id) NOT IN ('waiting', 'running') THEN", MIG),
 # confirmation
 ("c01", "pipeline/confirmation.py", "        changes = source_changes(conn, run_id)\n", "        changes = []\n", C),
 ("c02", "pipeline/confirmation.py", "        if shown is not None and dict(shown) != c:", "        if False:", C),
 ("c03", "pipeline/confirmation.py", "        if status != \"waiting\":", "        if status not in (\"waiting\", \"running\"):", C),
 ("c04", "pipeline/confirmation.py", "        \"SELECT s.key FROM source s WHERE NOT EXISTS", "        \"SELECT s.key FROM source s WHERE false AND NOT EXISTS", C),
 ("c05", "pipeline/confirmation.py", "    lines.append(\"Exclusion rules: \"", "    lines.append(\"Rules: \"", C),
 ("c06", "pipeline/confirmation.py", "        \"cost_so_far\": {\"counted_usd\": _money(cost.cap_cost)", "        \"cost_so_far\": {\"counted_usd\": _money(0)", C),
 ("c07", "pipeline/reading.py", "    if row is None:\n        return tested\n", "    if True:\n        return tested\n", C),
 # orchestrator
 ("o01", "pipeline/orchestrator.py", "            return _wait(engine, report)\n        if row.fixed_plan:", "            report.ready = True\n            return _done(engine, report)\n        if row.fixed_plan:", C),
 ("o02", "pipeline/orchestrator.py", "        return _wait(engine, report)\n    except Refused", "        report.ready = True\n        return _done(engine, report)\n    except Refused", C),
 ("o03", "pipeline/orchestrator.py", "            if not _exists(engine, \"SELECT 1 FROM rules_confirmation WHERE run_id = :r\", run_id):\n                return _done(engine, report)", "            if False:\n                return _done(engine, report)", C),
 ("o04", "pipeline/orchestrator.py", "    if confirmed != confirmation.plan_fingerprint(plan):", "    if False:", C + ["test_orchestrator.py"]),
 ("o05", "pipeline/orchestrator.py", "        if stored is None:\n            result = planner.run_planner", "        if True:\n            result = planner.run_planner", R),
 ("o06", "pipeline/orchestrator.py", "        if decided is None:\n            decision = narrowing", "        if True:\n            decision = narrowing", R),
 ("o07", "pipeline/orchestrator.py", "        if not _exists(engine, \"SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'critic'\", run_id):", "        if True:", R),
 ("o08", "pipeline/orchestrator.py", "        if _stored(engine, run_id, \"inclusion\") is None:", "        if True:", R),
 ("o09", "pipeline/orchestrator.py", "        if _stored(engine, run_id, \"statistics\") is None:", "        if True:", R),
 ("o10", "pipeline/orchestrator.py", "        if not _exists(engine, \"SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'analyst'\", run_id):\n            if _explain(engine, report, agent_kw) in RUN_STOPS:\n                return _stopped(engine, report, report.explanation_failure)\n        completion", "        if True:\n            if _explain(engine, report, agent_kw) in RUN_STOPS:\n                return _stopped(engine, report, report.explanation_failure)\n        completion", R),
 ("o11", "pipeline/orchestrator.py", "    elif row.status == \"completed\" and _done(engine, report).outcome == \"partly_sufficient\":", "    elif False:", R),
 ("o12", "pipeline/orchestrator.py", "        if _stored(engine, run_id, \"checks\") is None:", "        if True:", R),
 # queries and spend
 ("q01", "pipeline/queries.py", "    if spend.month_total(conn) >= spend.MONTH_CAP_USD:", "    if spend.month_total(conn) > spend.MONTH_CAP_USD:", Q),
 ("q02", "pipeline/queries.py", "            if key in SOURCES and SOURCES[key].constructed:", "            if False:", Q),
 ("q03", "pipeline/queries.py", "        if status not in CANCELLED:", "        if status not in (*CANCELLED, \"running\"):", Q),
 ("q04", "pipeline/queries.py", "AND r.status IN ('queued', 'waiting', 'running'))\"", "AND r.status IN ('queued', 'running'))\"", Q),
 ("q05", "pipeline/queries.py", "    if existing is not None:\n        if existing.status == \"draft\":", "    if False:\n        if existing.status == \"draft\":", R),
 ("q06", "pipeline/queries.py", "    if existing is not None:\n        if existing.status == \"draft\":\n            submit(engine, existing.vid)", "    if existing is not None:\n        if False:\n            submit(engine, existing.vid)", R),
 ("q07", "pipeline/queries.py", "        return _new_run(conn, vid, last.fixed_plan, marked, ceiling, setting_ids)", "        return _new_run(conn, vid, False, False, ceiling, setting_ids)", Q),
 ("s01", "pipeline/agents/spend.py", "            limit = min(x for x in (ceiling, stored) if x is not None) if (ceiling, stored) != (None, None) else None", "            limit = ceiling", Q),
 ("s02", "pipeline/agents/spend.py", "            limit = min(x for x in (ceiling, stored) if x is not None)", "            limit = max(x for x in (ceiling, stored) if x is not None)", Q),
 # command line
 ("l01", "cli_runs.py", "    print(words, flush=True)\n", "", CLI),
 ("l02", "cli_runs.py", "        out[\"next\"] = f'hypocurate confirm {run_id} --by \"<name>\"'", "        pass", CLI),
]
```
```python
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from mutations import MUTATIONS, T
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
## 8. New tests on `main`'s code

`main`'s package (`git archive ed46b48 hypocurate`) with this branch's tests, `PYTHONPATH` set and the working directory outside the repository. The migration and queries tests:

```
____________________ test_a_failed_upgrade_changes_nothing _____________________
    def test_a_failed_upgrade_changes_nothing(engine):
__________ test_a_failed_planner_attempt_still_needs_the_confirmation __________
    def test_a_failed_planner_attempt_still_needs_the_confirmation(w):
        w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE run_id = :r", r=rid)
    @pytest.mark.parametrize("status", ["running", "failed"])
        if status == "failed":
            set_status(engine, rid, "failed")
_____________ test_a_started_or_ended_run_is_not_cancelled[failed] _____________
status = 'failed'
    @pytest.mark.parametrize("status", ["running", "failed"])
        if status == "failed":
            set_status(engine, rid, "failed")
_ test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded _
    def test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded(engine):
        set_status(engine, first, "failed")
        set_status(engine, first, "failed")
PASSED tests/test_migrations_step9a.py::test_up_down_up_restores_0006
PASSED tests/test_migrations_step9a.py::test_a_queued_run_cannot_wait
PASSED tests/test_migrations_step9a.py::test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation[fixed_plan]
PASSED tests/test_migrations_step9a.py::test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation[no_planner_stage]
PASSED tests/test_queries_step9a.py::test_a_constructed_source_not_chosen_does_not_refuse_dispatch
FAILED tests/test_migrations_step9a.py::test_a_failed_upgrade_changes_nothing
FAILED tests/test_migrations_step9a.py::test_a_failed_planner_attempt_still_needs_the_confirmation
FAILED tests/test_queries_step9a.py::test_a_started_or_ended_run_is_not_cancelled[failed]
FAILED tests/test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded
76 failed, 5 passed in 33.12s
```

The other three new files on `main`'s package (they import the new module):

```
ImportError while importing test module '/home/codespace/hc-work/step09a/mainpkg/tests/test_confirmation.py'.
E   ImportError: cannot import name 'confirmation' from 'hypocurate.pipeline' (/home/codespace/hc-work/step09a/mainpkg/hypocurate/pipeline/__init__.py)
ImportError while importing test module '/home/codespace/hc-work/step09a/mainpkg/tests/test_resume_step9a.py'.
E   ImportError: cannot import name 'confirmation' from 'hypocurate.pipeline' (/home/codespace/hc-work/step09a/mainpkg/hypocurate/pipeline/__init__.py)
ImportError while importing test module '/home/codespace/hc-work/step09a/mainpkg/tests/test_cli_step9a.py'.
E   ImportError: cannot import name 'confirmation' from 'hypocurate.pipeline' (/home/codespace/hc-work/step09a/mainpkg/hypocurate/pipeline/__init__.py)
ERROR tests/test_confirmation.py
ERROR tests/test_resume_step9a.py
ERROR tests/test_cli_step9a.py
3 errors in 1.93s
```
## 9. The suite and the images

The whole suite on this head (locally):

```
1977 passed, 1 warning in 1292.83s (0:21:32)
local exit 0
```

The whole suite in the test image, rebuilt on this head:

```
1977 passed, 1 warning in 1386.86s (0:23:06)
exit 0
```

The package in the repository, the runtime image and the test image (SHA-256 over every file):

```
repo:    aa889d88b08670d9491858868dedcb1ac87b1fd02d9f9a1096cf0b1975bf5aa0  -
runtime: aa889d88b08670d9491858868dedcb1ac87b1fd02d9f9a1096cf0b1975bf5aa0  -
test:    aa889d88b08670d9491858868dedcb1ac87b1fd02d9f9a1096cf0b1975bf5aa0  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
```

The guard checks inside the runtime image (its own package; no pytest in the image):

```
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmp9lmxmbzk/.env is outside the approved inputs of pipeline code']}
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
## 10. The plan file and the scripts

### The step 9 plan file (owner's answers and the checklist)

````markdown
# Step 9 — worker, queue and recovery (plan; nothing built yet)

**State of main:** `ed46b48`, 1,847 tests collected, schema 0006 (dev DB up).

## Context

PRD 15 step 9: claiming jobs, a heartbeat, resume or fail, and spending caps; criterion 14.4 must pass. Today `hypocurate/worker.py` is the step-2 idle loop. `run` and `dispatch` run the orchestrator inline, in the guarded child. A crash, a recording failure or a deploy leaves a run `running` with a stage `running` and a call `started`, and nothing ever closes it (the 8b open item). The per-run ceiling lives only in the child's payload, so it is lost on a crash. And nothing stops a rules lock that no person confirmed.

## Owner's decisions in this planning (2026-10-08)

| # | Decision |
|---|---|
| Q1 | **The run waits at the rules lock** for a named person to confirm the question as tested (after the Planner and a narrowing decision of "proceed"). The dataset freeze stays automatic. |
| Q2 | **Render:** keep the worker on 0.5c-512mb (~$7/month). Measure the peak memory of worker and child in the runtime image; come back with the upgrade (1c-2g, ~$25) only if it is too close. No render.yaml change in step 9. |
| Q3 | **Interrupted paid stage:** the Planner is repeated **once**, as a new attempt; a second loss fails the run. The Critic is not repeated: its remaining flags stay "not classified" and the run goes on. The Analyst is not repeated: the run completes with "explanation unavailable (interrupted)". The lost call is always closed `interrupted` and counted at its reserved maximum. |
| Q4 | **Existing tests** that go through the Planner or a narrower question get one confirm step in their setup. No assertion changes; each is listed in the summary. |
| Q5 | **Who waits:** Planner runs and narrower-question runs wait. Fixed-plan runs (14.1a, the reference runs) do not. |
| Q6 | **Constructed data:** dispatch refuses a query naming a constructed source unless it is marked as a test. The storage guard stays as the backstop, and the whole run still fails there. |
| Q7 | **Split into 9a and 9b**, each with its own review and merge. |

## Owner's approval (2026-10-08) and four additions

Approved: the plan, R1–R8 and the split. 9a starts on `step-09a-waiting`. **No bulk or automatic confirmation in step 9.** Every confirmation is one run and one named person; step 11 decides how evaluation runs are confirmed. A test checks that no command or function confirms more than one run, or confirms without a name.

**A1. Sources while a run waits (9a).**
- *What a waiting run uses:* exactly the sealed versions recorded at dispatch (`run_source.source_version_id`). The database already refuses any change to them (0001, `hc_run_source_update`). The narrowing stored those versions' fingerprints (B1).
- *At confirm:*
  - code compares the narrowing's stored fingerprints with the run's versions, and with the newest sealed version of every registered source;
  - if they differ, the confirmation is refused, in plain words: `sources_changed: <source> has a newer version (or <source> was registered) since this run's narrowing; cancel this run and dispatch the query again`;
  - nothing is redone: refusing is simpler and never re-shows a changed decision.
- *Database backstop:* `hc_rules_confirmation_insert` refuses when the stored fingerprints differ from the run's versions.
- *Tests:* (1) a new sealed version registered while the run waits makes confirm refuse, with nothing written; (2) the backstop refuses a direct SQL insert; (3) unchanged sources confirm.

**A2. What confirm shows and stores (9a).** One function (`pipeline/confirmation.py: content(run)`) builds the content, and one renderer turns it into text. `confirm` prints the text before anything is recorded. The row stores the content (jsonb) and the exact text shown. Step 10 renders the same content. It holds:
1. the original question;
2. the question as tested, with its label;
3. what was narrowed and why: for a narrower question, the original's narrowing decision (the part without candidate records, its counts and the narrower scope); for a Planner run, "not narrowed", with the narrowing counts;
4. each scope part, marked stated or defaulted;
5. the outcome, the exclusion rules and the sufficiency option of the plan that will be locked, plus its fingerprint;
6. the sources and their versions;
7. the cost so far: counted (`coalesce(cost, max_cost)`) and reported.

Test: what is stored equals what was printed, byte for byte, and the content changes when any of its inputs changes.

**A3. The child dies with its parent (9b).**
- The worker's **main thread** starts the child (`Popen`); the heartbeat runs on its own thread.
- The child sets `PR_SET_PDEATHSIG(SIGKILL)` first thing in `guarded._main`, then checks that `getppid()` equals the parent pid passed in its request, which closes the fork race.
- Tests:
  - the heartbeat thread stops (made to exit) while the child keeps working and finishes;
  - SIGKILL of the worker kills the child within 2 s, and the child's work lock is released;
  - the child is started from the main thread (asserted on the thread that starts it).

**A4. A stuck child (9b).** Live runs on the dev DB took 10–41 s from start to end; the longest stage took 36 s and the longest call 17 s (12 runs, 21 calls). 3,600 s is not justified, so it is lowered and joined by a progress limit:
- `STALL_SECONDS = 900`: if the run writes nothing (no stage or call row started or finished, no status change) for 900 s, the parent kills the child and releases the claim as `child_stuck`, and recovery applies. 900 s covers one agent call's two requests at the 300 s request timeout, plus 300 s of margin.
- `RUN_TIMEOUT_SECONDS = 1800`, the whole run, as a backstop: 44 times the longest live run.
- Both go in the register. b5 measures a run on 0.5 CPU in the runtime image and reports it against both.
- `queue` shows, per run, the time since its last write, besides the heartbeat age.
- Test: a child stalled by a test trigger is killed at the (shortened, test-only) limit, and its run is recovered.

**Owner, 2026-10-08:** "I approve the updated plan with A1 to A4 as written. Build 9a on step-09a-waiting." **Note for 9b:** the 0.5-CPU measurement also reports how long the statistics stage takes, and what it would take at the step 11 simulation count (~10,000). This shows whether the 900 s and 1,800 s limits still fit.

**Size:** together these add about 1.5 h to 9a (a2/a3) and about 1 h to 9b (b2/b5). The milestones are unchanged.

## Recommendations to approve with this plan (not yet asked; say if any should change)

- **R1 `run`/`dispatch`.** By default they work the run inline through the same claim code, up to the wait or the end, then print `show`'s output (PRD 12 "runs it to completion"). `--queue` returns at once, after the dispatch line, for the worker to pick up. At the wait, the output adds `"waiting_for": "confirmation of the question as tested by a named person"` and the command to run next.
- **R2 New commands:**
  - `confirm <run> --by NAME [--queue]`: prints the question as tested, records the confirmation, then runs the rest or queues it;
  - `cancel <run> --by NAME`;
  - `queue`: queued, waiting and running runs, with stage, worker, heartbeat age and recoveries;
  - `dispatch Q-… --again`: a new run of a dispatched version, refused while another run of it is queued, waiting or running (PRD 8 / 14.4 "dispatched again as a new run");
  - `worker [--once]`.
- **R3 Cancel:** possible for a run that is queued or waiting, which then fails as `cancelled: cancelled by <name> before it started` or `… while waiting for confirmation of the question as tested`. A running run cannot be cancelled in sprint 1.
- **R4** A waiting run never expires; a person cancels it.
- **R5 Spending:**
  - The ceiling is stored on the run at dispatch (`run.spending_ceiling`, never changed), and `spend.reserve` reads it.
  - Dispatch is refused when the month's counted spend has reached $50 (PRD 8, 9.3).
  - The caps stay module constants.
  - A3/B2 stand: a spending refusal at the Analyst completes the run. Criterion 14.4 bullet 4 is tested at the Planner and the Critic.
- **R6 Heartbeat on the claim row**, not the run row, so it never waits behind a run lock. This is a named exception to the locking protocol, like audit rows. `run.heartbeat_at` and `run.current_stage` stay unused; the stage is derived from stored rows (`access/stage.py`).
- **R7 Before the 9a deploy,** the owner checks the live database for runs in progress. After 0007, the previous release's Planner runs are refused at the lock, deliberately.
- **R8 PRD-update list:** the confirmation checkpoint (PRD 3 step 4, 5.6, 9.4); the row lock at claim plus advisory locks (PRD 8); `--queue`, `confirm`, `cancel`, `queue` and `--again` (PRD 12).

---

## How a run moves (after step 9)

```
queued ─claim─► running: Planner → narrowing ─proceed─► WAITING ─confirm(by)─► running: rules lock → … → completed
   │                                      (fixed plan: straight to the lock)   │
   └─cancel(by)─► failed                                   cancel(by) ─────────┘─► failed
```

New status `waiting` (0007). Every child-row trigger already requires `running`, so a waiting run can have no stage, call, invocation or plan written to it, and the access layer gives `none`.

## Recovery: what happens at each stage

First, always, as bookkeeping only:
1. Every `started` call of the run is closed `interrupted` (`worker_stopped`, or `recording_failed`), with no usage. It keeps counting at `max_cost` in every cap and view.
2. Every `running` stage is closed `failed` (`interrupted`).
3. What was found is recorded on the claim row.

Recovery never writes a plan, a record, a set, a freeze or a confirmation. Forward progress goes only through the normal path and its database guards.

| Where it stopped | Decision | Why |
|---|---|---|
| Queued | Claimed and started normally | Nothing written yet |
| Planner mid-call (or its recording failed) | **Repeated once** (new attempt, reserved against the caps); a second loss fails the run with `interrupted: the worker stopped during the Planner's request twice; dispatch the query again as a new run` | Nothing locked or confirmed yet; the cost is counted and shown (Q3) |
| Planner closed failed / domain mismatch, but the run not failed | Failed with the reason from the stored stage | Replays code's decision |
| Planner done, no narrowing | Narrowing **resumed** from the stored answer | Deterministic, one transaction |
| Narrowing `proceed`, not confirmed | **Waiting**: nothing done | Waiting for a person; recovery never confirms |
| Narrowing `claim_not_one_plan` | Failed with the stored reason | Replays the decision |
| Partly path: Analyst mid-call | Not repeated; copy plus narrower question; "explanation unavailable (interrupted)" | A3/B2, Q3 |
| Completed partly sufficient with no narrower question, or one left in draft | Narrower question finished idempotently (unique index in 0007) | The run is final; only its linked record is missing |
| Confirmed, no plan | Rules lock **resumed** by the normal path; the database checks the confirmation's plan fingerprint | A checkpoint reached normally, never by recovery |
| Locked: sources pending, Checks, Inclusion, freeze, statistics | **Resumed** from the first stage not done | Each is one transaction, detectable and deterministic (audit below) |
| Critic mid-batch, or between batches | Not repeated; remaining flags "not classified"; on to Inclusion | No decision reads the class (Q3) |
| Analyst mid-call (after statistics) | Not repeated; completed with "explanation unavailable (interrupted)" | A3/B2, Q3 |
| Statistics and Analyst done, not completed | `copy_decision` **resumed** | One transaction |
| A run recovered more than 3 times (`MAX_RECOVERIES`) | Failed: `attempts_exhausted: the run stopped at <stage> <n> times without finishing; dispatch it again as a new run` | A run is never left running for good |

**Fixes to idempotency found in the audit** (needed for resume):
- Narrowing has no "already done" guard.
- Inclusion's guard reads `run_record`, which is empty when the primary set is empty; it should read its stage row.
- `create_narrower` can create two questions; it gets a unique index.
- The Critic replans every batch.

None of these changes a result.

## Claims, heartbeat, and "dead"

- **Claim (9b):**
  - First the worker takes, without waiting, a session advisory lock `(CLAIM, run)` on its own lease connection, and checks that `(WORK, run)` is free.
  - Then, in one locked transaction: re-check the run, close any stale claim as `lost`, insert a `run_claim` row and move queued→running (or a confirmed waiting run→running).
  - A partial unique index allows one open claim per run.
  - Effect: two workers can never both work a run; the cancel-versus-start race is closed by the same transaction.
- **The guarded child** takes `(WORK, run)` on its own connection for its whole work, and exits at once, writing nothing, if it cannot. It is set to die with its parent (`PR_SET_PDEATHSIG`), a safeguard change to `access/guarded.py`. Even if that fails, the orphan's lock keeps every other worker off the run.
- **Heartbeat:** a thread in the worker parent writes `run_claim.heartbeat_at` **every 15 s**. It keeps beating during a request of up to 300 s.
- **Dead** means silent for **120 s** (8 missed beats), *and* both advisory locks free. A claim released as `shutdown` or `stopped_for_recovery` can be claimed again at once. The child is killed after 900 s with no write, or after 1,800 s in all (A4).
- **The worker shows it is alive** in three places: `queue` (heartbeat age per claim), the claim rows, and the process log (one line per claim, release and recovery). The worker's sweep runs on start and every 60 s.
- **Deploy (SIGTERM):** stop claiming, send SIGTERM to the child, and release the claim as `shutdown`. A request in flight becomes an interrupted call and is handled by the table above.
- The parent never imports dspy, litellm or scipy, which keeps memory low (Q2).

## Migrations (hand-written)

**0007 (9a):**
1. `ck_run_status` gains `waiting`. `hc_run_update` is replaced with 0001's body copied verbatim, plus the waiting transitions only.
2. A new trigger, `hc_run_update_waiting`:
   - running→waiting only with no plan, no stage running and no call open, and a done `proceed` narrowing on the Planner path;
   - waiting→running only with a confirmation;
   - waiting→failed always.
3. `run.spending_ceiling` (> 0, never changed).
4. `rules_confirmation`, append-only: run (unique), `confirmed_by` (1–200 characters), `confirmed_at = now()`, `plan_fingerprint`, the Planner and narrowing stage ids, and the question as tested.
5. `hc_plan_insert_rules_confirmed`: a run that must wait gets a plan only if its fingerprint equals the confirmation's.
6. A unique index on `hypothesis(narrower_of_run_id)`.
7. The downgrade refuses while anything new is in use, then restores 0001's function and constraint exactly.

**0008 (9b):** `run_claim`:
- columns: worker, child pid, claimed, heartbeat, released, `release_reason`, and what recovery found;
- no delete; only the heartbeat may change while the claim is open; released once;
- the one-open-claim index.

Trigger names sort after the earlier ones on the same table. Each migration is tested up, down and up, against direct SQL, and with the previous release's code.

## Milestones and estimates (build time; review rounds come after each part)

**9a: waiting, confirm, cancel, resumable orchestrator** (~10 h)

| M | What | Est. |
|---|---|---|
| a0 | Golden dump from main: reference fixed-plan run plus a Planner run through the stub (results, fingerprints, `show`) | 1 h |
| a1 | 0007 + `models.py` + `test_migrations_step9a.py` (backstops, downgrade, old code) | 2.5 h |
| a2 | `queries.confirm/cancel/redispatch`, stored ceiling, month-cap and constructed-source dispatch refusals | 1.5 h |
| a3 | Orchestrator as a step machine: next step from stored rows; the four idempotency fixes; existing tests get their confirm step (Q4) | 3 h |
| a4 | CLI `confirm`, `cancel`, `dispatch --again`; register entries; full suite, both images, mutations, reference comparison; summary + packet | 2 h |

Questions may come at a1 (wording of the reasons) and a4 (register wording).

**9b: queue, worker, recovery** (~12 h)

| M | What | Est. |
|---|---|---|
| b1 | 0008 + tests | 1.5 h |
| b2 | `pipeline/queue.py` (claim, locks, heartbeat thread), `worker.py` loop, SIGTERM; `guarded.py` Popen path + PDEATHSIG | 3 h |
| b3 | `pipeline/recovery.py` (table above, `MAX_RECOVERIES`, reasons in plain words) | 2 h |
| b4 | CLI inline-through-claim, `--queue`, `queue`, `worker --once` | 1 h |
| b5 | Kill matrix, two workers, recording failure, checkpoint restarts, caps, 14.4 test; memory measurement in the runtime image (Q2) | 3.5 h |
| b6 | Register, full suite, images, mutations, reference comparison, summary + packet | 1 h |

## Tests (added in each part)

**Kill points.**
- *Code stages:* a test-only trigger in the scratch database does `pg_sleep` at the chosen write. The test waits until `pg_stat_activity` shows it, then SIGKILLs the child or the parent.
- *Agent stages:* the stub provider kills the process while the request is in flight.
- No hook in production code.

**Kill the worker at each stage:** mid-Planner (repeat, then complete; twice → failed with the reason), before narrowing, while waiting, after the lock, between sources, before Checks, mid-Critic batch 1 of 2, before Inclusion, before the freeze, mid-statistics, mid-Analyst, and between the partly copy and the narrower question (exactly one created).

Each case checks four things:
- no stage stays running and no call stays started;
- every lost call ends `interrupted` and is counted at its maximum;
- no stub request is repeated except the one allowed Planner repeat;
- final fingerprints and results equal the uninterrupted run's.

**Kill the parent:** the child dies, its lock is released, and another worker recovers the run.

**Two workers:**
- two worker processes and one queued run give exactly one claim and no duplicated request;
- two claims at once: one gets nothing;
- with an orphan child holding the work lock, the run cannot be claimed.

**Recording failure:** a test trigger makes `finish` fail. The run stays open; after the trigger is dropped, recovery closes the call at its maximum and applies the role's rule.

**Restart with a run at each checkpoint:**
- waiting before the lock: no claim and no call; after confirm, it completes;
- after the lock, and after the freeze: each resumes with the same results.

**Caps across crashes:**
- repeated interruptions stay within $2;
- a repeat that would pass the cap is refused before sending;
- the stored ceiling holds after recovery;
- the month near $50: dispatch is refused, and a recovery repeat is refused `spending_cap_month`.

**Waiting, confirmation and cancel:**
- no lock without a confirmation, or with another fingerprint;
- no second confirmation, and none on a run that is not waiting;
- cancel a queued and a waiting run; a running run is refused;
- the wording of every failure reason.

**Criterion 14.4**, bullets 2 and 4. **Reference runs byte-identical to main** (golden dump a0).

## Left for step 10 (screens)

- Confirm and Cancel buttons; Dispatch again; the queue under Review and dispatch; the month-cap message.
- Run viewer polling and the waiting stage state.
- Claim, heartbeat and recovery facts on the run page.
- Criterion 14.4 bullets 1 (close the browser) and 3 (web restart). Step 9b adds only a test that the web code never claims or runs a pipeline.
- Labels on lists (`constructed_test_runs`).

## Workflow

Branch `step-09a-waiting` (then `step-09b-worker`). Failing tests first, with "N failed before" in each commit. Whole suite before every push; rebuild both images, then prune the build cache (never `--volumes`). Mutation checks on every new safeguard. Register entries in the same merge:
- the confirmation;
- the queue and claims;
- the recovery policy;
- `HEARTBEAT_SECONDS`, `STALE_SECONDS`, `RUN_TIMEOUT_SECONDS`, `MAX_RECOVERIES`, `PLANNER_REPEATS`;
- `spending_caps` reworded.

Summary and packet in `docs/reviews/` for each part. render.yaml and workflows stay untouched. Secrets: the Render worker has no `ANTHROPIC_API_KEY`; the owner adds it in the dashboard when live runs on Render are wanted (a test pins the worker's env names in render.yaml, so any render.yaml change is the owner's separate go).

## Verification

- Whole suite locally and in the rebuilt test image.
- `docker compose up worker` with the stub:
  - `run --queue`, then `queue` shows the claim and heartbeat;
  - `kill -9` the worker mid-run, restart it, and the run resumes or fails with its reason;
  - `confirm` and `cancel` from the command line.
- Reference comparison against the a0 dump.
- Peak memory of worker and child measured in the runtime image and reported.

## Owner's go for 9a (2026-10-08): "Go. All defaults", with one wording change

1. Reasons (exact):
   - `cancelled: cancelled by <name> before it started`
   - `cancelled: cancelled by <name> while waiting for confirmation of the question as tested`
   - `sources_changed: <source> has a newer version (or <source> was registered) since this run's narrowing; cancel this run and dispatch the query again`
   - **`month_cap_reached: this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, or until the owner raises the cap`** (owner's wording)
   - `constructed_source_unmarked: <source> is constructed test data; dispatch it only as a marked test run`
   - `already_open: another run of this query is queued, waiting or running`
2. Label once confirmed: "the Planner's reading of the claim; not verified by code; confirmed by <name> on <UTC time>"; before confirmation the current label is kept.
3. Claude drafts the register entries; the owner reviews them in the summary.
4. Dev DB: pg_dump backup, then migrate to 0007; its 12 runs are kept.
5. No live model call in 9a.
6. If something surprises me:
   - a reference number or fingerprint changes: stop all work;
   - a mutation survives: add a test and continue;
   - a test seems wrong or would need weakening: stop that item and continue the others;
   - render.yaml or workflows: never touched.
7. End point: full suite, summary, packet, push the branch, stop. No merge.

## Progress (9a)
- [x] a0 golden dump (02:47 UTC; ~/hc-work/step09a/refdump/main, SHA256SUMS; repeat identical)  - [x] a1 0007 (cd4b38b)  - [x] a2 queries (70bc74c)  - [x] a3 orchestrator (394a425)  - [x] a4 CLI (d929839), register (0016c36), mutation fixes (b07991b); 39/39 caught; images hashed; suite, packet, push: in progress
````
### `~/hc-work/step09a/register_9a.py`

```python
"""Step 9a register entries (scratch; run from the repo root with the project's Python)."""
import json
P = "hypocurate/assumptions.json"
d = json.load(open(P, encoding="utf-8"))
by = {e["key"]: e for e in d}
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-08"}
NOT_REVIEWED = {"status": "not_reviewed", "name": None, "date": None}
PLAN = "Step 9 plan approved by the owner on 2026-10-08 (questions Q1-Q7, R1-R8, additions A1-A4; the go for 9a with the reasons' wording)."


def new(key, name, statement, value, category, affects, reason, settings, tests, evidence=(PLAN,), notes=()):
    assert key not in by, key
    e = {"key": key, "name": name, "state": "in_force", "statement": statement,
         "value": {"text": value, "unit": None}, "category": category, "affects": affects, "reason": reason,
         "evidence": list(evidence), "decided": OWNER, "expert_review": NOT_REVIEWED, "sensitivity": None,
         "applied": {"status": "yes", "settings": settings, "note": None}, "tests": tests, "history": [],
         "notes": list(notes)}
    d.append(e)
    by[key] = e


def reword(key, statement, note, **changes):
    e = by[key]
    e["history"].append({"value": e["statement"], "from": e["decided"]["date"], "to": "2026-10-08", "note": note})
    e["statement"] = statement
    e["decided"] = OWNER
    for k, v in changes.items():
        e[k] = v


new("rules_confirmation", "The run waits at the rules lock for a named person",
    "A run whose plan comes from a model's answer waits before its rules lock, with status 'waiting', until a named "
    "person confirms the question as tested: a run with a Planner stage (after code's narrowing decision to proceed), "
    "and a narrower question's run (its outcome and exclusion rules come from its original's Planner answer). A "
    "fixed-plan run of an ordinary question (criterion 14.1a) never waits. Before anything is recorded the person is "
    "shown, from stored rows only: the original question, the question as tested, what was narrowed and why, each "
    "scope part marked stated or assumed, the outcome, the exclusion rules, the sufficiency option, the fingerprint of "
    "the plan to be locked, the source versions and the cost so far; the confirmation stores that content and the "
    "exact text shown. A confirmation is for one run and one named person (no bulk or automatic confirmation in step "
    "9). It is refused when a chosen source has a newer sealed version, or a source was registered, since dispatch "
    "(the run's own versions never change); nothing is redone. The database refuses a plan from a model's answer "
    "unless its fingerprint is the confirmed one, and refuses every write to a waiting run; the dataset freeze stays "
    "automatic. Scoping: the database recognises a run that must wait by a Planner stage (any attempt) or a narrower "
    "link, so a run with no Planner stage and no narrower link (the test worlds of steps 6-8 that lock a plan "
    "directly) is not held to it; the orchestrator builds a Planner plan only from a stored Planner stage.",
    "waits at the rules lock; one named person per run", "operational",
    "Every run whose plan comes from the Planner or a narrower question (PRD 3, 5.6, 9.4).",
    "The second-model review of step 8b found claim interpretation unchecked; the owner chose a person's "
    "confirmation at the rules lock (Q1), for every plan built from a model's answer (Q5), bound to the plan locked "
    "and to the source versions the narrowing counted (A1), showing everything the plan rests on (A2).",
    [{"ref": "python:hypocurate.pipeline.confirmation:WAITING_FOR",
      "equals": "confirmation of the question as tested by a named person"},
     {"ref": "python:hypocurate.db.models:CONFIRMED_BY_MAX", "equals": 200},
     {"ref": "python:hypocurate.pipeline.confirmation:SOURCES_CHANGED"},
     {"ref": "python:hypocurate.pipeline.confirmation:plan_to_lock"},
     {"ref": "python:hypocurate.pipeline.confirmation:render"},
     {"ref": "sql:hc_plan_rules_confirmed"}, {"ref": "sql:hc_rules_confirmation_insert"}, {"ref": "sql:hc_run_waiting"}],
    ["tests/test_confirmation.py::test_a_planner_run_waits_before_its_rules_lock_and_nothing_more_is_done",
     "tests/test_confirmation.py::test_confirm_shows_every_item_and_stores_exactly_the_text_shown",
     "tests/test_confirmation.py::test_a_newer_version_registered_while_the_run_waits_refuses_the_confirmation",
     "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself",
     "tests/test_migrations_step9a.py::test_a_planner_runs_plan_must_be_the_confirmed_plan",
     "tests/test_migrations_step9a.py::test_a_confirmation_is_refused_when_the_counted_source_versions_are_not_the_runs",
     "tests/test_migrations_step9a.py::test_a_plan_that_comes_from_no_model_answer_is_locked_without_a_confirmation"],
    notes=["Step 11 decides how the evaluation runs are confirmed (owner, 2026-10-08). The website's Confirm button "
           "is step 10."])

new("resumable_run", "A run is taken up again from what is stored",
    "The orchestrator decides every step from stored rows, never from memory: a done Planner stage is used, not "
    "repeated; a stored narrowing decision is used; after the lock, records are stored only for sources still "
    "pending, and Checks, Inclusion, the freeze, the statistics and the completion run only if their stored result "
    "is absent; an agent stage that exists (the Critic's, the Analyst's) is never started again; a completed "
    "partly-sufficient original without its narrower question gets it, and never a second one (a database index "
    "allows one per run; a draft left by a stop is submitted). A run on its first pass takes exactly the steps it "
    "took before. Recovery after a crash (closing open stages and calls, the Planner's one repeat) is step 9b.",
    "next step from stored rows", "operational", "Every run that stops between steps (PRD 8 'Restart', 14.4).",
    "Step 9: a run must be taken up where it stopped without repeating a paid or a stored step (owner, Q3).",
    [{"ref": "python:hypocurate.pipeline.orchestrator:proceed"},
     {"ref": "python:hypocurate.pipeline.queries:create_narrower"},
     {"ref": "sql:uq_hypothesis_narrower_of_run_id"}],
    ["tests/test_resume_step9a.py::test_a_run_stopped_after_a_step_is_taken_up_from_the_next_and_gives_the_same_results",
     "tests/test_resume_step9a.py::test_a_done_planner_stage_is_used_and_the_planner_is_not_asked_again",
     "tests/test_resume_step9a.py::test_a_partly_sufficient_original_stopped_after_its_copy_gets_exactly_one_narrower_question",
     "tests/test_migrations_step9a.py::test_a_run_has_at_most_one_narrower_question"])

new("run_cancel", "A person cancels a queued or waiting run",
    "A named person cancels a run that is queued or waiting; it fails with 'cancelled: cancelled by <name> before it "
    "started' or 'cancelled: cancelled by <name> while waiting for confirmation of the question as tested'. A started "
    "run cannot be cancelled in sprint 1; an ended run cannot be cancelled.",
    "queued or waiting only", "operational", "Stopping a run (PRD 14.4; the owner's step 9 brief).",
    "Owner's step 9 brief ('a person can cancel a queued or waiting run'); R3.",
    [{"ref": "python:hypocurate.pipeline.queries:CANCELLED"}],
    ["tests/test_queries_step9a.py::test_a_queued_run_is_cancelled_with_the_persons_name",
     "tests/test_queries_step9a.py::test_a_waiting_run_is_cancelled_with_the_persons_name",
     "tests/test_queries_step9a.py::test_a_started_or_ended_run_is_not_cancelled"])

new("dispatch_again", "A query dispatched again as a new run",
    "A query whose runs have all ended is dispatched again as a new queued run of its dispatched version, recording "
    "what the version's latest run recorded (fixed plan, test mark); a spending ceiling only as given with the new "
    "dispatch. Refused, with 'another run of this query is queued, waiting or running', while any run of the query is "
    "open; the monthly cap and the test-data rule apply as at dispatch.",
    "a new run once no run is open", "operational", "PRD 8 and 14.4 ('dispatched again as a new run').",
    "PRD 8, 14.4; owner's approval of R2.",
    [{"ref": "python:hypocurate.pipeline.queries:REASONS.already_open",
      "equals": "another run of this query is queued, waiting or running"}],
    ["tests/test_queries_step9a.py::test_a_failed_run_is_dispatched_again_as_a_new_run_with_what_the_first_recorded",
     "tests/test_queries_step9a.py::test_dispatch_again_is_refused_while_another_run_of_the_query_is_open"])

new("dispatch_refusals", "Dispatch refused at the monthly cap and for unmarked test data",
    "Dispatch is refused when this calendar month's counted model calls (UTC; reported cost, or maximum while none is "
    "known) have reached the monthly cap: 'this month's model calls have reached the monthly cap ($50); dispatch is "
    "refused until next month, or until the owner raises the cap' (the owner's words). Dispatch is refused when a "
    "chosen source is constructed test data and the run is not marked as a test: '<source> is constructed test data; "
    "dispatch it only as a marked test run'; the storage guard stays as the backstop and still fails the whole run.",
    "two refusals at dispatch", "operational", "Every dispatch (PRD 8, 9.3; register 'constructed_test_runs').",
    "PRD 8 ('a monthly cap blocks dispatch'); owner's answers R5 and Q6.",
    [{"ref": "python:hypocurate.pipeline.queries:REASONS.month_cap_reached",
      "equals": "this month's model calls have reached the monthly cap ($50); dispatch is refused until next month, "
                "or until the owner raises the cap"},
     {"ref": "python:hypocurate.pipeline.queries:REASONS.constructed_source_unmarked",
      "equals": "{source} is constructed test data; dispatch it only as a marked test run"}],
    ["tests/test_queries_step9a.py::test_dispatch_is_refused_once_the_months_calls_reach_the_monthly_cap",
     "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test"])

e = by["spending_caps"]
reword("spending_caps", e["statement"].replace(
    "a request that would pass a cap, or a lower ceiling the caller names, is not sent",
    "a request that would pass a cap, or a lower ceiling (the lower of one the caller names and, for a run, the one "
    "stored on the run at dispatch, which holds after a crash or a restart), is not sent") +
    " At dispatch, a run is refused once the month's counted calls have reached the monthly cap.",
    "Step 9a (owner, 2026-10-08, R5): the ceiling stored on the run; the monthly cap also blocks dispatch.")
e["applied"]["settings"].append({"ref": "sql:ck_run_spending_ceiling"})
e["tests"] += ["tests/test_queries_step9a.py::test_the_stored_ceiling_holds_when_the_caller_names_none",
               "tests/test_queries_step9a.py::test_the_lower_of_the_stored_and_the_given_ceiling_holds"]

e = by["question_as_tested"]
reword("question_as_tested", e["statement"].replace(
    "and is labelled 'the Planner's reading of the claim; not verified by code and, in this version, not confirmed by "
    "a person' (owner, F-Q2: the label says what is true now; the confirmation by a person comes in step 10)",
    "and is labelled 'the Planner's reading of the claim; not verified by code and, in this version, not confirmed by "
    "a person' until a named person confirms it at the rules lock (step 9a), then 'the Planner's reading of the claim; "
    "not verified by code; confirmed by <name> on <UTC time>' (owner, 2026-10-08); another reading's label gains "
    "'; confirmed by <name> on <UTC time>'").replace(
    " Until step 10 no person confirms it: the run goes on to the lock without a confirmation.",
    " Since step 9a a run with the Planner, and a narrower question's run, wait at the lock for that confirmation "
    "(register 'rules_confirmation')."),
    "Step 9a (owner, 2026-10-08): the confirmation at the rules lock, from the command line; the label once confirmed.")
e["applied"]["done"] += " Step 9a: confirmed by a named person at the rules lock from the command line (`confirm`); the label once confirmed."
e["applied"]["pending"] = "The Confirm button on the website (step 10)."
e["applied"]["settings"].append({"ref": "python:hypocurate.pipeline.reading:CONFIRMED_LABEL",
                                 "equals": "the Planner's reading of the claim; not verified by code; confirmed by {by} on {at}"})
e["tests"] = [t.replace("test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested",
                        "test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested_and_waits")
              for t in e["tests"]] + ["tests/test_confirmation.py::test_once_confirmed_the_question_as_tested_says_by_whom_and_when"]

e = by["run_order_and_failures"]
reword("run_order_and_failures", e["statement"].replace(
    "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock,",
    "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or, after a named "
    "person's confirmation of the question as tested (the run waits for it; step 9a), the rules lock,").replace(
    "so does a narrower question's run, recognised by its link to its original (its stored plan).",
    "so does a narrower question's run, recognised by its link to its original (its stored plan), which also waits "
    "for the confirmation.").replace("until step 9's recovery", "until step 9b's recovery"),
    "Step 9a (owner, 2026-10-08, Q1 and Q5): the wait for a person's confirmation before the lock.")

e = by["constructed_test_runs"]
reword("constructed_test_runs", e["statement"].replace(
    "An unmarked run refuses them, and logs the refusal, at record storage, inclusion and the freeze.",
    "Dispatch refuses a query naming a constructed source unless the run is marked (step 9a, owner Q6); an unmarked "
    "run that reaches them anyway refuses them, and logs the refusal, at record storage, inclusion and the freeze."),
    "Step 9a (owner, 2026-10-08, Q6): refused at dispatch; the storage guard stays as the backstop.")
e["tests"].append("tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test")

with open(P, "w", encoding="utf-8") as f:
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(len(d), "entries")
```
### `~/hc-work/step09a/packet.py`

````python
"""Builds docs/reviews/step09a_review_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step09a"
BASE = "ed46b48"
OUT = Path("docs/reviews/step09a_review_packet.md")
PLAN = Path.home() / ".claude/plans/pasted-content-id-1208-step-9-elegant-walrus.md"


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
parts = [f"""# Build step 9a — review packet

Date: 2026-10-08. Branch: `step-09a-waiting`, from `main` at `{BASE}`. Head when generated: `{head}`. Generated from
the files on disk by a script (`~/hc-work/step09a/packet.py`, quoted in section 10), so every diff and output below is
quoted exactly.

## How to use this packet

Step 9a builds the wait at the rules lock and its confirmation by a named person, cancel, dispatch again, the spending
ceiling stored on the run, two dispatch refusals, and an orchestrator that takes every step from stored rows (the
queue, the worker and recovery are step 9b). It holds safeguard changes (listed at the top of the summary), so please
review against `docs/reviews/checklist.md` and answer the questions at the end of the summary. Sections: 1 the summary;
2 the code diff; 3 the new test files; 4 the changed tests; 5 the register; 6 the reference comparison with `main`;
7 the mutation checks; 8 new tests on `main`'s code; 9 the suite and the images; 10 the plan file and the scripts.

"""]
parts.append("## 1. The summary\n\n" + read("docs/reviews/step09a_summary.md") + "\n")
diff = sh("git", "diff", f"{BASE}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{BASE}..HEAD`, the package with migration 0007; the register is in section 5)\n\n"
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
parts.append("## 7. Mutation checks\n\nThe first run (three survivors, each then given a test; see the summary):\n\n"
             + fence(read(HOME / "mutations.log")) + "\nAll re-run on the final tests, a control run with no mutation "
             "last:\n\n" + fence(read(HOME / "final_mutations.log")) + "\nThe specification and the runner:\n\n"
             + fence(read(HOME / "mspec/mutations.py"), "python") + fence(read(HOME / "mspec/run_all.py"), "python"))
parts.append("## 8. New tests on `main`'s code\n\n`main`'s package (`git archive " + BASE + " hypocurate`) with this "
             "branch's tests, `PYTHONPATH` set and the working directory outside the repository. The migration and "
             "queries tests:\n\n" + fence(lines_with(HOME / "failed_before2.log", "PASSED", "passed", "failed"))
             + "\nThe other three new files on `main`'s package (they import the new module):\n\n"
             + fence(lines_with(HOME / "failed_before.log", "ImportError", "ERROR tests", "errors in")))
parts.append("## 9. The suite and the images\n\nThe whole suite on this head (locally):\n\n"
             + fence(lines_with(HOME / "final_full.log", "passed", "failed", "exit"))
             + "\nThe whole suite in the test image, rebuilt on this head:\n\n"
             + fence(lines_with(HOME / "image_suite.log", "passed", "failed", "exit"))
             + "\nThe package in the repository, the runtime image and the test image (SHA-256 over every file):\n\n"
             + fence(read(HOME / "image_hashes.txt"))
             + "\nThe guard checks inside the runtime image (its own package; no pytest in the image):\n\n"
             + fence(read(HOME / "image_guard.log")) + fence(read(HOME / "imgcheck/guard_in_image.py"), "python"))
scripts = ["register_9a.py", "packet.py"]
parts.append("## 10. The plan file and the scripts\n\n### The step 9 plan file (owner's answers and the checklist)\n\n"
             + fence(read(PLAN), "markdown")
             + "".join(f"### `~/hc-work/step09a/{s}`\n\n" + fence(read(HOME / s), "python") for s in scripts))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
