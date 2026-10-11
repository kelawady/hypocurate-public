# Build step 10a — review packet

Branch `step-10a-run-pages`, head `1a7d243`, against `main` `ba83c3d`. Generated from the files on disk by a script (quoted at the end).

## 1. The summary

# Build step 10a — summary for review

Date: 2026-10-11. Branch: `step-10a-run-pages` (from `main` at `ba83c3d`). **Status: built, pushed, not merged; stopped for the owner's morning review of the register entries, then the second-model review.**

PRD Section 15, step 10 ("Website screens"), first part. The owner split step 10 into:
- **10a (this part):** the run pages (runs list, run viewer, evidence dial, confirmation and cancel, live state), the fixes from the first live runs, and a faster suite;
- **10b (next):** queries, new query, review and dispatch, Critic flags, data sources, agents, plot, workbook, Help page.

The approved plan, with every owner decision of 2026-10-11 (four planning answers, six additions, two screenshot reviews, the overnight answers), is quoted at the end.

## Safeguard changes (second-model review before any merge; CLAUDE.md "How we work" item 5)

1. **The signed-in person's name.**
   - Sign-in takes the shared password and a name, which is fixed for the session.
   - It is recorded as the `by` of confirm and cancel.
2. **CSRF tokens on every write.** One token per session, checked in constant time before anything is done.
3. **The web write paths:** confirm (`confirmation.confirm`) and cancel (`queries.cancel`). Nothing else.
4. **`confirmation.confirm(shown_fingerprint=)`.** The page sends back the SHA-256 of the content it showed; other content is refused as `content_changed`.
5. **The confirmation text:**
   - "informative groups";
   - "1 model call";
   - the label now and the label once confirmed.
6. **`reading.stored`:** the label's provenance comes from the run's own plan source.
7. **The suite's speed:** a parallel run was built, measured and taken out again (owner's decision); the suite runs serially as before. See "The suite's speed (a5)".

**Not changed:**
- `.github/workflows/`, the Dockerfile, Compose, `render.yaml`;
- the runtime lock; no migration (schema stays 0008);
- the access layer and its allow-lists (`access.stage.actual_stage` included);
- the orchestrator, recovery and the guarded runner.

The web service imports none of the queue, the worker, the orchestrator, recovery, the guarded runner or a model library. A fresh process that opens every page is checked for this.

## What was built

| Commit | What |
|---|---|
| `e3897e7` | Read-only run views (`pipeline/run_view.py`; `show` and `queue_rows` moved from `cli_runs` unchanged); `pipeline/progress.py` (the last-write query, moved from `queue`); the confirmation fingerprint and wording; the provenance label; `statistics.EVIDENCE_SHORT`; the worker's `run_finished` log line; `queue`'s stage words; the fix summary's suite times. The glossary move (`git mv`, content unchanged) landed in this commit because it was already staged. |
| `deed860` | The parallel suite (taken out again in `1a7d243`): `pytest-xdist` 3.8.0 and `execnet` in the dev lock; `-n 2 --dist loadgroup`; `conftest.SERIAL_FILES`; `tests/test_parallel_isolation.py`. |
| `2c82b6c` | The web: routes, templates, `dial.py`, `security.py`, `glossary.py`, `textfmt.py`, `static/poll.js` and `info.js`, the stylesheet; the glossary's two new entries; CLAUDE.md's new glossary path; the register; the screenshots. |
| `5662200` | The page-isolation probe sets `PYTHONPATH` to this checkout (it failed in the test image). |
| `f8f5671` | An empty commit for the second GitHub run (the owner's overnight answer 2). |
| `1a7d243` | Back to serial (owner's decision): `pytest-xdist` and `-n`/`--dist` removed; `SERIAL_FILES` kept as a record; `parallel_suite` not yet applied (step 11). |

**On the commit grouping:** some files carry changes from two of these themes, so the commits are grouped by theme and only the final commit is guaranteed to pass the whole suite.

### The screens

- **Runs list.** Every run, newest first, with:
  - a small dial;
  - "No evidence level yet (not completed)", or "failed: no evidence level";
  - status in words, outcome, cost.
- **Run viewer.** For a completed run, in this order:
  1. code's results statement, with the dial and the verdict beside it;
  2. the Analyst's text under its label;
  3. each source alone and all together;
  4. the sensitivity sets by display name and description;
  5. cautions (code's own, split from the statement without rewording);
  6. checkpoints, sources searched;
  7. tokens and cost, per stage and in total.
- **An open run** (queued, waiting or running) shows:
  - its state: "waiting at the rules lock"; or running, with its stage in words; or failed, with its reason;
  - the claim facts: worker, heartbeat age, time since the last write, claims and recoveries;
  - Confirm and Cancel where they apply.
- **The dial.** Half a circle of six separate segments in one blue that darkens with the level:
  - a needle on the run's level, its segment outlined;
  - "Level n of 6: <label>";
  - the verdict beside it, never in it;
  - hatched, with the stored label, for a marked test run;
  - no text inside the SVG.
- **Confirmation.**
  - The page shows `confirmation.render`'s text line for line, the same text the command line prints, then the button.
  - It sends back the content's fingerprint.
  - It names the signed-in person and the label they will give.
  - Cancel is offered too.
- **Live state.**
  - `static/poll.js` asks for `/runs/<id>/state` every 5 s. Polling stops by the server's choice: an open run's state carries its own address, an ended run's carries none.
  - **Checked in a real browser:** four requests while the run was queued; after a cancel from another session the page reloaded once and showed "failed", with no request in the next 20 s.
- **Text on the screens.**
  - Nothing below 12 px.
  - Superscript units (screens only).
  - The Analyst's text in a safe Markdown subset (bold, lists, simple tables), everything escaped first.
  - Tables become stacked cards on a phone.

### The fixes from the live run (docs/reviews/live_run_render_2026-10-10.md, open items)

| Item | Done |
|---|---|
| 2 "independent groups" | "informative groups" in the confirmation text |
| 3 `queue` stage "none" | "waiting at the rules lock" / "queued (not started)" (in `run_view.queue_rows`; `actual_stage` unchanged) |
| 4 the label at confirming | the text shows "Now labelled: …" and "Once confirmed, labelled: …" |
| 7 the fix's suite times | added to `fix_agent_contracts_summary.md` (branch 21:45, run 38092510866; main 32:16, run 38093958140) |
| log lines | the claim was already logged (`claimed`); a `run_finished` line with status and outcome or failure reason |

### The owner's review of the screenshots

**The provenance label (a defect the owner found).**
- **What was wrong:** local run 2 (a Planner run of step 8b) was labelled "the fixed reference plan". Step 8b's Planner stage stored no reading, and the label fell back to the fixed plan's.
- **The fix:** the label now comes from the run's own plan source. A Planner reading locked with no confirmation reads "the Planner's reading of the claim; not verified by code; this run predates confirmation".
- **Checked on every run in the development database:** runs 1 and 2 changed, and nothing else did.
- **The format:** the owner kept statement format 2 and asked for a register note on `results_statement` (added).

**The other changes asked for**, each with a test:
- the safe Markdown subset for the Analyst's text;
- "not recorded" for an old run's ceiling;
- no long wording under the dial;
- the survivor set's wording;
- "with a minimum missed" in the help text;
- "failed: no evidence level";
- superscript units;
- "1 model call".

## The suite's speed (a5): tried, measured, taken out

The owner approved a parallel run (`pytest-xdist`) on two conditions: no test sees another's data, and no re-runs.

**Isolation (condition 1).**
- Every test that needs tables has its own database with a random name, made from a template each pytest process makes for itself.
- Advisory locks are per database.
- The database at `DATABASE_URL` is opened only by the read-only health tests.
- `tests/test_parallel_isolation.py` checks this by scanning the tests. It stays in the suite.

**What was measured.**

| Run | Workers | Time | Result |
|---|---|---|---|
| Serial, `main` (a0) | — | 34:50 | 2,220 passed |
| Serial, branch, before the final edits | — | 36:06 | 1 failed: a pinned "1 model calls" (the owner changed it to the singular) |
| Parallel, local | 4 | 34:10 | 1 failed: `test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance` (released `child_stuck`, expected `finished`) |
| Parallel, local | 2 | 32:05 | 1 failed: the register's reference to the old `-n 4` text (fixed) |
| Final serial against parallel, local, on `2c82b6c` | 2 | 35:58 serial, 31:37 parallel | the same 2,292 test ids with the same outcome (all passed), compared from the JUnit XML of both runs |
| GitHub run 38142724721 (`5662200`) | 2 | suite step 26:20 | green |
| GitHub run 38144600449 (`f8f5671`, empty commit) | 2 | suite step 26:45 | **failed:** the same stall-allowance test |

**Why it failed.**
- The test gives the worker's child a 6 s stall allowance. Under parallel load the child can take longer to start.
- It was already in the group of timing tests run on one worker. That group keeps those tests from overlapping one another, not from the load of the other worker, so pinning could not help.
- On 2 cores the suite is CPU-bound: each kill-matrix case restarts processes that re-import the package. Parallel workers gained only 10–20%.

**The owner's decision (2026-10-11):** back to serial for 10a, and revisit the suite's speed in step 11 as its own reviewed change.
- `pytest-xdist` and the `-n`/`--dist` options are removed; the dev lock equals `main`'s.
- `conftest.SERIAL_FILES` stays as a record of the tests a parallel run must keep apart from other load.
- The register entry `parallel_suite` reads "not yet, step 11", with these measurements.

**GitHub runs on the final head** (suite step, "Run the suite in the test image"): run 38142724721 (`5662200`, 2 workers): 26 min 20 s, green; run 38144600449 (`f8f5671`, 2 workers): 26 min 45 s, failed (the stall-allowance test). The run on the final head (serial) is reported to the owner when it ends and goes into this summary in the review round's first commit (as in step 9b).

## Tests

**The whole suite:** 2,292 tests (2,220 on `main`), all passing locally on the final head `1a7d243`, serially, in 38 min 04 s.

**New test files:**
- `test_web_runs.py`;
- `test_web_state.py`;
- `test_web_textfmt.py`;
- `test_web_isolation.py`;
- `test_confirmation_step10.py`;
- `test_reading_step10.py`;
- `test_parallel_isolation.py` (kept after the parallel run was taken out).

**New tests in existing files:**
- `test_worker.py`: the log lines;
- `test_cli_step9b.py`: the queue's stage words.

**Failed before the code** (the new tests run against `main`'s package, from a folder without one of its own):
- **11 failed:**
  - the confirmation fingerprint, wording and label tests (8);
  - the page-isolation probe;
  - the worker's log line;
  - `queue`'s stage words (`main` says "none" for both).
- **4 files could not import on `main`** (no `run_view`, `dial`, `security` or `textfmt`): `test_web_runs.py`, `test_web_state.py`, `test_web_textfmt.py`, `test_reading_step10.py`.
- **4 passed:** the parallel-isolation checks, which test the suite's setup rather than the package.
- **Separately, against the old `reading.py` alone:** the provenance test failed, and the other 3 in its file passed (guards).

**Changed tests, and why** (none weakened, none removed):

| Test | Change | Reason |
|---|---|---|
| `test_login.py::sign_in` (helper) | sends a name | owner's answer 1 (name at sign-in) |
| `test_login.py::test_cookie_holds_only_the_signed_in_flag` | **renamed** `…_the_name_and_the_form_token`; the cookie holds exactly `signed_in`, `name`, `csrf` | answer 1, addition 1 |
| `test_assumptions.py::signed_in` (helper) | sends a name | answer 1 |
| `test_assumptions.py::PARTLY` | `question_as_tested` is now fully applied | the website's Confirm button is built |
| `test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself` | callers {`cli_runs.py`, `app.py`}; parameters gain `shown_fingerprint` | the approved plan (web confirm) and addition 2; still one run, one name, the only insert in `confirmation.py` |
| `test_confirmation.py::test_the_cost_shown_is_the_runs_counted_and_reported_cost` | "1 model call," | owner's review (singular) |

**Reference runs:** byte-identical to `main` in all six dumps (the statistics reference runs; the fixed-plan, Planner FCC, Planner BCC, partly-sufficient and narrower orchestrator runs). The harness does not dump `rules_confirmation`, so the changed confirmation text is checked by its own tests, not by this comparison.

**Images:** rebuilt on this code. The package's SHA-256 over every file is the same in the repository, the runtime image and the test image (84da618a…); the test image's `tests/` equals the repository's; the runtime image holds no `tests/` or `docs/`, and does hold `hypocurate/web/glossary.json`; the guard checks pass in the runtime image. The whole suite in the test image on `5662200`: 2,292 passed in 32 min 27 s (the first image run, on `2c82b6c`, found a defect in the new isolation test, which cleared `PYTHONPATH`; fixed in `5662200`). Locally on `5662200`: 2,292 passed in 31 min 40 s. The build cache was pruned afterwards. **The final head** (the return to serial) changes the register, the dev lock, `conftest.py` and one test after these image checks, so the images were not rebuilt locally for it. The GitHub run on the final head builds both images, checks the runtime image and runs the suite in the test image.

## Register

**156 entries.** 8 new, each with the owner's decision of 2026-10-11 and Claude Code's wording, for the owner's review:
- `signed_in_name`;
- `csrf_tokens`;
- `confirmation_shown_fingerprint`;
- `evidence_dial`;
- `sensitivity_set_display_names`;
- `live_run_state`;
- `screen_text`;
- `parallel_suite` (not yet applied: step 11).

**Notes and corrections:**
- **Notes added:** on `results_statement` (the owner's wording) and on `question_as_tested`.
- **`question_as_tested`:** now "yes" (the Confirm button), with `PREDATES_LABEL` named.
- **`constructed_test_runs`:** what is done names 10a's screens; pending, step 10b.
- **The badge** shows the stored label, `TEST_RUN_LABEL`.

## What 10a does not do or claim

- **The name is not authenticated.** Under one shared password it records who said they acted, as `--by` does.
- **Sign-out carries no CSRF token** (it writes no data).
- **The polling stop** is tested by the server's contract and the script's source in the suite, and by Playwright outside it. The suite's image has no browser.
- **The screenshots** were taken on a scratch copy of the local development database, with three runs added through the stub. The live database is untouched.
- **Not built yet (10b):** queries, dispatch, the Critic flags page, sources, agents, plot, workbook, Help page.
- **Left for step 11:**
  - deployment and the 14.7 walk-through;
  - the audit-log view;
  - how evaluation runs are confirmed;
  - the analysis-specific seed;
  - `ANTHROPIC_API_KEY` and a Blueprint sync.

## PRD corrections and clarifications (for the next PRD update)

1. **PRD 6 and 9.4:** live updates use a small script of our own, not HTMX (owner, 2026-10-11).
2. **PRD 6 and 11:** plots and workbooks will be built on request from stored rows; the `artifact` table is unused in sprint 1 (owner, answer 3).
3. **PRD 9.7:** the glossary is `hypocurate/web/glossary.json`.
4. **PRD 9.4:** the evidence-level dial with short labels; the verdict beside it.
5. **PRD 6, Login:** the sign-in takes a name, fixed for the session.

## Questions for the reviewer

1. Can any website path write except through `confirmation.confirm` and `queries.cancel`, or without the session's token?
2. Can a confirmation be recorded for content other than what the page displayed?
3. Does any page compute a result or a statement, rather than show code's?
4. Is the provenance label right for every kind of run (fixed, narrower, Planner confirmed, Planner predating confirmation, waiting, cancelled)?
5. Is the record of the parallel attempt (register `parallel_suite`, conftest's `SERIAL_FILES`) accurate, and does the serial suite keep every test's data apart?
6. Is any claim here, in the code or in the register stronger than the code supports?


## 2. Commits

```
1a7d243 Step 10a: the suite runs serially again (owner's decision); the parallel run is for step 11
f8f5671 CI repeat for the a5 parallel check (2 of 3)
5662200 Step 10a: the page-isolation probe uses this checkout's package in the test image too
2c82b6c Step 10a: the run pages, the evidence dial, confirmation and cancel on the website; register entries
deed860 Step 10a: the suite runs in parallel (pytest-xdist, 2 workers, one serial group)
e3897e7 Step 10a: read-only run views; confirmation fingerprint and wording; provenance label; worker log line

```

## 3. Files changed

```
 CLAUDE.md                                          |   2 +-
 docs/reviews/fix_agent_contracts_summary.md        |   5 +
 docs/reviews/step10a_screenshots/00_sign_in.png    | Bin 0 -> 19820 bytes
 docs/reviews/step10a_screenshots/01_runs_list.png  | Bin 0 -> 451462 bytes
 .../step10a_screenshots/02_run_sufficient.png      | Bin 0 -> 1081631 bytes
 .../step10a_screenshots/03_run_insufficient.png    | Bin 0 -> 458543 bytes
 .../04_run_coefficient_only.png                    | Bin 0 -> 592852 bytes
 .../step10a_screenshots/05_run_test_run.png        | Bin 0 -> 802977 bytes
 .../reviews/step10a_screenshots/06_run_waiting.png | Bin 0 -> 182082 bytes
 .../step10a_screenshots/07_confirmation.png        | Bin 0 -> 249673 bytes
 docs/reviews/step10a_screenshots/08_run_queued.png | Bin 0 -> 112576 bytes
 .../step10a_screenshots/09_info_popup_open.png     | Bin 0 -> 220666 bytes
 .../10_run_sufficient_phone.png                    | Bin 0 -> 3252763 bytes
 .../step10a_screenshots/11_after_end_failed.png    | Bin 0 -> 107008 bytes
 .../12_phone_per_source_table.png                  | Bin 0 -> 218971 bytes
 .../step10a_screenshots/13_phone_runs_list.png     | Bin 0 -> 152881 bytes
 hypocurate/assumptions.json                        | 422 ++++++++++++++++-
 hypocurate/cli_runs.py                             | 119 +----
 hypocurate/pipeline/confirmation.py                |  42 +-
 hypocurate/pipeline/progress.py                    |  28 ++
 hypocurate/pipeline/queue.py                       |  20 +-
 hypocurate/pipeline/reading.py                     |  37 +-
 hypocurate/pipeline/run_view.py                    | 462 +++++++++++++++++++
 hypocurate/pipeline/statistics.py                  |  10 +
 hypocurate/web/app.py                              | 148 +++++-
 hypocurate/web/dial.py                             |  69 +++
 {docs => hypocurate/web}/glossary.json             |   4 +-
 hypocurate/web/glossary.py                         |  51 +++
 hypocurate/web/security.py                         |  62 +++
 hypocurate/web/static/info.js                      |  49 ++
 hypocurate/web/static/poll.js                      |  38 ++
 hypocurate/web/static/style.css                    | 104 ++++-
 hypocurate/web/templates/_dial.html                |   8 +
 hypocurate/web/templates/_state.html               |  29 ++
 hypocurate/web/templates/assumptions.html          |   2 +-
 hypocurate/web/templates/base.html                 |  30 +-
 hypocurate/web/templates/confirm.html              |  34 ++
 hypocurate/web/templates/home.html                 |   6 +-
 hypocurate/web/templates/login.html                |  10 +-
 hypocurate/web/templates/run.html                  | 113 +++++
 hypocurate/web/templates/runs.html                 |  23 +
 hypocurate/web/textfmt.py                          |  82 ++++
 hypocurate/worker.py                               |  15 +
 tests/conftest.py                                  |  16 +
 tests/test_assumptions.py                          |   6 +-
 tests/test_cli_step9b.py                           |  11 +
 tests/test_confirmation.py                         |  10 +-
 tests/test_confirmation_step10.py                  | 104 +++++
 tests/test_login.py                                |  12 +-
 tests/test_parallel_isolation.py                   |  55 +++
 tests/test_reading_step10.py                       |  82 ++++
 tests/test_web_isolation.py                        |  75 +++
 tests/test_web_runs.py                             | 503 +++++++++++++++++++++
 tests/test_web_state.py                            | 151 +++++++
 tests/test_web_textfmt.py                          |  35 ++
 tests/test_worker.py                               |  17 +
 56 files changed, 2894 insertions(+), 207 deletions(-)

```

## 4. The full diff (screenshots left out; the lock's new hash lines shown, others unchanged)

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index e9ffc88..b1e7088 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -64,7 +64,7 @@ The access layer and its tests guard against **our own code** leaking data to a
 
 - `PRD_sprint1.md` — the specification (PDF copy alongside).
 - `HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf` — background and research questions.
-- `glossary.json` — the 41 explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
+- The glossary is no longer here: since step 10a it is `hypocurate/web/glossary.json` (the deployed image holds no `docs/`; owner, 2026-10-11). It holds the explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
 - `mockup_screens/` — the nine target screens.
 - `reference/worked_example.py`, `reference/calibration_example.py` — the scripts that produced the reference numbers. They contain file paths from another machine; treat them as a statement of method, not as code to import.
 
diff --git a/docs/reviews/fix_agent_contracts_summary.md b/docs/reviews/fix_agent_contracts_summary.md
index ace028b..0297563 100644
--- a/docs/reviews/fix_agent_contracts_summary.md
+++ b/docs/reviews/fix_agent_contracts_summary.md
@@ -76,6 +76,11 @@ On 2026-10-10 the owner ran the first two live runs on Render, through the real
   - `SENTENCES`: the direction is placed as its own sentence.
   - `test_agent_core::test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer`: the note now includes the reason, and the literal reason is checked.
 - **The whole suite:** 2,215 tests, all passing locally (36 min 37 s) on `436b518`. The final local run before the push and the GitHub suite step are given below.
+- **Added on 2026-10-11 (step 10a; the live-run record's open item 7), as they were missing:**
+  - **The final local run before the push:** 2,220 tests, all passing, 36 min 36 s (finished 2026-10-10 22:43:40 UTC).
+  - **The GitHub suite step** ("Run the suite in the test image"):
+    - the branch: **21 min 45 s** (`1ddf508`, run 38092510866);
+    - `main` after the merge: **32 min 16 s** (`51257cb`, run 38093958140).
 
 ## Mutation checks
 
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 3bbd575..2814792 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -5008,8 +5008,8 @@
           "ref": "python:hypocurate.pipeline.results:REAL_RUN"
         }
       ],
-      "done": "The mark and the refusals at storage, inclusion and freeze (step 6). Step 7: the label on every stored analysis and calibration result and on the statistics and gap-facts stage results of a marked run (checked by the database for result rows), and one named condition that leaves marked runs out of every aggregate (pipeline/results.py, REAL_RUN).",
-      "pending": "The label and the exclusion on every screen and list (step 10).",
+      "done": "The mark and the refusals at storage, inclusion and freeze (step 6). Step 7: the label on every stored analysis and calibration result and on the statistics and gap-facts stage results of a marked run (checked by the database for result rows), and one named condition that leaves marked runs out of every aggregate (pipeline/results.py, REAL_RUN). Step 10a: the run viewer shows the label on a marked run, and the runs list marks it (a hatched dial and a 'test run' badge).",
+      "pending": "The label and the exclusion on the remaining screens and lists (step 10b).",
       "step": 10,
       "note": "The guard is in code; the database itself does not refuse a constructed record."
     },
@@ -5030,7 +5030,8 @@
       "tests/test_analysis_stage.py::test_a_marked_run_with_no_dataset_frozen_is_labelled_too",
       "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records",
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
-      "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test"
+      "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test",
+      "tests/test_web_runs.py::test_a_marked_test_runs_dial_is_hatched_with_a_badge"
     ]
   },
   {
@@ -7437,7 +7438,7 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.pipeline.reading:LABELS"
@@ -7454,12 +7455,13 @@
         {
           "ref": "python:hypocurate.pipeline.reading:CONFIRMED_LABEL",
           "equals": "the Planner's reading of the claim; not verified by code; confirmed by {by} on {at}"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.reading:PREDATES_LABEL",
+          "equals": "the Planner's reading of the claim; not verified by code; this run predates confirmation"
         }
       ],
-      "done": "Step 8b fix round 1: the text and label written by code, stored with the Planner's stage output, the defaulted-mark check, printed by `run`/`dispatch` before the rules lock and by `show`. Step 9a: confirmed by a named person at the rules lock from the command line (`confirm`); the label once confirmed.",
-      "pending": "The Confirm button on the website (step 10).",
-      "step": 10,
-      "note": null
+      "note": "Step 8b fix round 1: the text and label written by code. Step 9a: confirmed from the command line (`confirm`). Step 10a: the Confirm button on the website (the same function and content); the label comes from the run's own plan source, never a fallback to the fixed plan."
     },
     "history": [
       {
@@ -7475,7 +7477,9 @@
         "note": "Step 9a (owner, 2026-10-08): the confirmation at the rules lock, from the command line; the label once confirmed."
       }
     ],
-    "notes": [],
+    "notes": [
+      "2026-10-11 (step 10a; owner's review of the screenshots): a Planner run whose plan was locked before confirmations existed was labelled as the fixed reference plan; its label is now 'the Planner's reading of the claim; not verified by code; this run predates confirmation'. In the development database, runs 1 and 2 are the only ones changed."
+    ],
     "tests": [
       "tests/test_reading.py::test_the_label_says_whose_reading_it_is_and_that_a_person_confirms_it",
       "tests/test_reading.py::test_each_exclusion_rule_in_words",
@@ -7484,7 +7488,10 @@
       "tests/test_orchestrator.py::test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested_and_waits",
       "tests/test_cli_runs.py::test_run_prints_the_claim_and_the_planners_reading_before_the_report_and_show_keeps_it",
       "tests/test_cli_runs.py::test_a_fixed_plan_runs_reading_is_the_reference_plans",
-      "tests/test_confirmation.py::test_once_confirmed_the_question_as_tested_says_by_whom_and_when"
+      "tests/test_confirmation.py::test_once_confirmed_the_question_as_tested_says_by_whom_and_when",
+      "tests/test_reading_step10.py::test_a_planner_run_locked_before_confirmations_is_never_labelled_as_the_fixed_plan",
+      "tests/test_reading_step10.py::test_a_waiting_planner_run_is_labelled_not_yet_confirmed_and_once_confirmed_says_by_whom",
+      "tests/test_web_runs.py::test_confirming_records_the_signed_in_name_and_exactly_the_text_shown_and_runs_nothing"
     ]
   },
   {
@@ -7966,7 +7973,9 @@
         "note": "Second-model re-check (docs/reviews/step08b_recheck_chatgpt.md) and the owner's decisions: rendered in the current format always (the earlier claim that the wording follows the recorded format was unsupported); not-fitted branch; spread whenever its figures exist."
       }
     ],
-    "notes": [],
+    "notes": [
+      "2026-10-11 (step 10a; owner's decision to keep format 2): format 2's provenance label of the question as tested was corrected for Planner runs that predate confirmation. Such a run, whose plan was locked before confirmations existed (migration 0007) and which stored no reading with its Planner stage, was labelled \"the fixed reference plan; not read from the claim\"; it now reads \"the Planner's reading of the claim; not verified by code; this run predates confirmation\". No run after confirmations existed is affected. In the development database, runs 1 and 2 are the only ones changed."
+    ],
     "tests": [
       "tests/test_statement.py::test_the_reference_run_s_statement",
       "tests/test_statement.py::test_the_statement_is_present_when_the_analyst_fails_and_holds_nothing_it_wrote",
@@ -8831,5 +8840,396 @@
     ],
     "history": [],
     "notes": []
+  },
+  {
+    "key": "signed_in_name",
+    "name": "The signed-in person's name, fixed for the session",
+    "state": "in_force",
+    "statement": "The sign-in form takes the shared password and the person's name (1 to 200 characters, spaces collapsed). The name is kept in the signed session cookie and is the name recorded by every action that names a person on the website (in step 10a: confirming the question as tested and cancelling a run). It cannot change within a session: signing in again while signed in is refused, so a new name means signing out and in again. A session signed before step 10a, which has no name, may read but not act. Nothing proves who typed the name: under the one shared password it records who said they acted, as --by does on the command line.",
+    "value": {
+      "text": "name at sign-in; 1-200 characters; fixed for the session",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every confirmation and cancellation made on the website.",
+    "reason": "Owner's answer 1 to the step 10 plan (name at sign-in) and addition 3 (the name cannot change within a session).",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.web.security:NAME_MAX",
+          "equals": 200
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_signing_in_needs_a_name_and_keeps_it_with_a_token",
+      "tests/test_web_runs.py::test_the_name_cannot_change_within_a_session",
+      "tests/test_web_runs.py::test_a_session_without_a_name_cannot_act",
+      "tests/test_web_runs.py::test_cancel_records_the_signed_in_name",
+      "tests/test_login.py::test_cookie_holds_only_the_signed_in_flag_the_name_and_the_form_token"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "csrf_tokens",
+    "name": "Every website action that writes carries the session's token",
+    "state": "in_force",
+    "statement": "A random token (32 bytes, URL-safe) is made at sign-in and kept in the signed session cookie. Every form that writes carries it in the hidden field csrf_token, and the server compares it in constant time before doing anything; a request without the session's token, with an empty one or with another session's, is refused with 403 and writes nothing. In step 10a the writes are confirm and cancel; dispatch, dispatch again, domain confirmation and source registration (step 10b) will carry it too. Sign-out writes nothing and carries none. The cookie is also SameSite=Lax.",
+    "value": {
+      "text": "a token per session, checked on every write",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every website action that writes.",
+    "reason": "Owner's addition 1 to the step 10 plan.",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.web.security:CSRF_FIELD",
+          "equals": "csrf_token"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_a_write_without_the_sessions_token_is_refused_and_writes_nothing",
+      "tests/test_web_runs.py::test_another_sessions_token_is_refused"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "confirmation_shown_fingerprint",
+    "name": "A confirmation is of the content the page showed",
+    "state": "in_force",
+    "statement": "The confirmation page sends back the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8) of the content it displayed. confirmation.confirm compares it, inside the transaction that records the confirmation, with the run's current content, and refuses any difference as content_changed (as it refuses other content given whole by the command line). A page that sends no fingerprint is refused the same way. The website is the second caller of confirm, after the command line; confirm still takes one run and one name.",
+    "value": {
+      "text": "SHA-256 of the canonical content",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every confirmation made on the website.",
+    "reason": "Owner's addition 2 to the step 10 plan.",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.confirmation:content_fingerprint"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_confirmation_step10.py::test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item",
+      "tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded",
+      "tests/test_confirmation_step10.py::test_content_that_changed_after_it_was_shown_is_refused",
+      "tests/test_web_runs.py::test_a_confirmation_of_content_other_than_what_was_shown_is_refused",
+      "tests/test_web_runs.py::test_a_confirmation_without_the_shown_contents_fingerprint_is_refused",
+      "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "evidence_dial",
+    "name": "The evidence-level dial",
+    "state": "in_force",
+    "statement": "The run viewer shows the run's evidence level (set by code; it never changes the verdict) as a half circle of six separate segments in one blue that darkens with the level (never red to green), with a needle on the run's level and its segment outlined, and the words \"Level n of 6: <short label>\". The short labels: 6 tested answer, 5 exploratory answer, 4 coefficient only, 3 below the minimums, 2 no coefficient fitted, 1 nothing tested. The verdict is shown beside the dial, never in it. A marked test run's dial is hatched, with a \"test run\" badge. The runs list shows a small dial; a run not completed shows no level (\"failed: no evidence level\" for a failed run). The dial holds no text: every word is HTML beside it.",
+    "value": {
+      "text": "six segments; one hue; the labels stated",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The run viewer and the runs list.",
+    "reason": "Owner's step 10 brief; answer 2 (the draft labels); review of the screenshots, 2026-10-11 (no long wording under the dial; failed runs).",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.web.dial:SHADES",
+          "equals": [
+            "#dde6f3",
+            "#b9cbe7",
+            "#8ea9d6",
+            "#6286c2",
+            "#3a63a6",
+            "#1d3f78"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.pipeline.statistics:EVIDENCE_SHORT"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.run_view:FAILED_NO_LEVEL",
+          "equals": "failed: no evidence level"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_the_short_labels_are_the_owners_set",
+      "tests/test_web_runs.py::test_the_dial_has_one_hue_that_darkens_with_the_level",
+      "tests/test_web_runs.py::test_the_needle_points_at_the_runs_level",
+      "tests/test_web_runs.py::test_the_dial_shows_the_level_and_label_with_the_verdict_beside_it_not_in_it",
+      "tests/test_web_runs.py::test_a_marked_test_runs_dial_is_hatched_with_a_badge",
+      "tests/test_web_runs.py::test_the_runs_list_shows_a_small_dial_for_every_run",
+      "tests/test_web_runs.py::test_the_large_dial_shows_the_level_label_without_the_long_wording"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "sensitivity_set_display_names",
+    "name": "Sensitivity sets shown by name, never by internal key",
+    "state": "in_force",
+    "statement": "The screens name each sensitivity set in words and describe its one change for readers; the internal keys are never shown. The ninth set keeps its approved name, \"without the group with the largest share of slope information\", with the eligibility code's description. The survivor set's description is the owner's: \"Conflicting values, left out of the main result, are included once each, using the survivor's value.\"",
+    "value": {
+      "text": "display names and descriptions",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The run viewer's sensitivity table.",
+    "reason": "Owner's step 10 brief (display names, never internal names) and review of the screenshots (the survivor set's wording).",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.run_view:SET_DISPLAY_NAMES"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.run_view:SET_DESCRIPTIONS"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_sensitivity_sets_are_shown_by_display_name_never_by_internal_name",
+      "tests/test_web_runs.py::test_every_sensitivity_set_has_a_display_name_and_a_description",
+      "tests/test_web_runs.py::test_the_survivor_set_says_that_conflicting_values_are_normally_left_out"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "live_run_state",
+    "name": "An open run's page updates itself and stops when the run ends",
+    "state": "in_force",
+    "statement": "While a run is queued, waiting or running, its page asks for the run's state every 5 seconds (static/poll.js, a script of our own, not HTMX). The server decides when this ends: an open run's state carries its own address, an ended run's (completed or failed) carries none; the script asks again only when the state it received carries an address, and on an ended state reloads the page once to show the results. Every state read is read-only; the web service never claims a run or runs a stage, so closing the browser or restarting the web service never affects a run (criterion 14.4).",
+    "value": {
+      "text": "every 5 s while the run is open",
+      "unit": "seconds"
+    },
+    "category": "operational",
+    "affects": "The run viewer.",
+    "reason": "Owner's step 10 brief (the page updates by itself) and answer of 2026-10-11 (a script of our own; polling stops at an end state, with a test).",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.run_view:OPEN_STATUSES",
+          "equals": [
+            "queued",
+            "waiting",
+            "running"
+          ]
+        },
+        {
+          "ref": "file:hypocurate/web/static/poll.js:var INTERVAL_MS = 5000;"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_state.py::test_an_open_runs_page_polls_its_own_state_and_an_ended_runs_page_does_not",
+      "tests/test_web_state.py::test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended",
+      "tests/test_web_state.py::test_the_script_asks_again_only_when_the_state_it_received_carries_an_address",
+      "tests/test_web_state.py::test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart",
+      "tests/test_web_isolation.py::test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "screen_text",
+    "name": "How text is shown on the screens",
+    "state": "in_force",
+    "statement": "No text on any screen is smaller than 12 px (sizes in rem, at least 0.75rem). The Analyst's text is shown in a small safe subset of Markdown (paragraphs, bold, bulleted and numbered lists, simple tables), with everything the model wrote escaped first. Exponents in units are written as superscripts on the screens only; stored text and the command line keep \"^\".",
+    "value": {
+      "text": "at least 12 px; a safe subset; superscripts on screens",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every screen.",
+    "reason": "Owner's addition 6 to the step 10 plan and review of the screenshots (2026-10-11).",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.web.textfmt:model_text"
+        },
+        {
+          "ref": "python:hypocurate.web.textfmt:units"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_no_text_on_any_screen_is_smaller_than_12px",
+      "tests/test_web_textfmt.py::test_bold_lists_and_a_simple_table_are_rendered_and_no_raw_signs_remain",
+      "tests/test_web_textfmt.py::test_everything_the_model_writes_is_escaped",
+      "tests/test_web_runs.py::test_units_are_written_with_a_real_superscript_on_the_screens"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "parallel_suite",
+    "name": "The regression suite runs serially; a parallel run is for step 11",
+    "state": "in_force",
+    "statement": "The suite runs serially (plain `pytest -q`). A parallel run with pytest-xdist was tried in step 10a and taken out: on 4 workers locally (2-core machine) it took 34 min 10 s against 36 min 06 s serially, and a test with a 6 s stall allowance (test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance) failed under the load although it ran in a group on one worker; on 2 workers it took 31 min 37 s locally against 35 min 58 s serially (the same 2,292 tests and outcomes), and on GitHub the suite step took 26 min 20 s (green) and 26 min 45 s (that test failed again), against about 32 minutes serially. Every test still has a database of its own with a random name; the files that would need keeping apart from other load are listed in tests/conftest.py SERIAL_FILES. The suite's speed is revisited in step 11 as its own reviewed change.",
+    "value": {
+      "text": "serial; revisit in step 11",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every run of the regression suite, locally and on GitHub.",
+    "reason": "The GitHub suite step took about 32 of the job's 40 minutes; the owner's answer 4 to the step 10 plan approved a parallel run on conditions (no test sees another's data; no re-runs); the owner chose serial for 10a on 2026-10-11 after the stall-allowance test failed under parallel load on GitHub.",
+    "evidence": [
+      "Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and the overnight answers (quoted in docs/reviews/step10a_summary.md)."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "not_yet",
+      "step": 11,
+      "note": "Isolation checks kept: tests/test_parallel_isolation.py."
+    },
+    "tests": [
+      "tests/test_parallel_isolation.py::test_databases_are_made_only_by_conftest_with_random_names",
+      "tests/test_parallel_isolation.py::test_only_the_read_only_health_tests_open_the_shared_database",
+      "tests/test_parallel_isolation.py::test_each_test_database_is_made_from_a_template_of_this_process",
+      "tests/test_parallel_isolation.py::test_the_serial_group_names_only_existing_test_files"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
   }
 ]
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index 37a6507..2e31d42 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -29,6 +29,9 @@ from sqlalchemy import Engine, text
 from sqlalchemy.exc import IntegrityError
 
 from hypocurate.pipeline import queries
+# Step 10a: moved to the read-only `run_view` (shared with the screens), unchanged; imported here under their names.
+from hypocurate.pipeline.run_view import (analyst_text, critic_flags, question_as_tested, queue_rows,  # noqa: F401
+                                          show)
 
 
 def command(args, engine: Engine) -> int:
@@ -144,33 +147,6 @@ def _wait_for(engine: Engine, run_id: int, poll: float = 2.0) -> None:
         time.sleep(poll)
 
 
-def queue_rows(engine: Engine) -> list[dict]:
-    """`queue` (R2): every queued, waiting or running run, with its stage, its claim's worker and heartbeat age, the
-    time since the run last wrote anything (A4), and how often it was taken up again."""
-    from hypocurate.access.stage import actual_stage
-    from hypocurate.pipeline import confirmation, queue
-    out = []
-    with engine.connect() as conn:
-        runs = conn.execute(text(
-            "SELECT r.id, r.status, h.number, EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS "
-            "confirmed, c.worker, extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age, "
-            "(SELECT count(*) FROM run_claim x WHERE x.run_id = r.id AND x.released_at IS NOT NULL AND "
-            "x.release_reason NOT IN ('waiting', 'finished')) AS recoveries FROM run r "
-            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
-            "LEFT JOIN run_claim c ON c.run_id = r.id AND c.released_at IS NULL "
-            "WHERE r.status IN ('queued', 'waiting', 'running') ORDER BY r.queued_at, r.id")).all()
-        for r in runs:
-            out.append({
-                "run": r.id, "query": r.number, "status": r.status, "stage": actual_stage(conn, r.id, r.status),
-                "waiting_for": (confirmation.WAITING_FOR if r.status == "waiting" and not r.confirmed else
-                                "a worker (confirmed)" if r.status == "waiting" else None),
-                "worker": r.worker, "heartbeat_age_seconds": round(float(r.heartbeat_age), 1)
-                if r.heartbeat_age is not None else None,
-                "seconds_since_last_write": round(queue.seconds_since_last_write(conn, r.id), 1),
-                "recoveries": int(r.recoveries)})
-    return out
-
-
 def _print_shown(engine: Engine, run_id: int, report: dict) -> int:
     # One presentation everywhere (owner, after the re-check): the same output as `show` (code's statement first, then
     # the Analyst's text under its label), with the stages run and the run's failure, if any. The orchestration
@@ -207,92 +183,3 @@ def _claim(engine: Engine, run_id: int) -> str:
     with engine.connect() as conn:
         return conn.execute(text("SELECT hv.text FROM run r JOIN hypothesis_version hv ON hv.id = "
                                  "r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).scalar_one()
-
-
-def question_as_tested(engine: Engine, run_id: int) -> dict | None:
-    from hypocurate.pipeline import reading
-    with engine.connect() as conn:
-        return reading.stored(conn, run_id)
-
-
-def analyst_text(explained) -> dict:
-    """The Analyst's stored explanation, always with its label; or that it is unavailable (code's own words)."""
-    from hypocurate.pipeline.agents import analyst
-    if isinstance(explained, dict) and explained.get("report"):
-        return {"label": analyst.LABEL, "text": explained["report"]}
-    if isinstance(explained, dict):
-        return {"unavailable": explained.get("shown") or analyst.UNAVAILABLE}
-    return {"unavailable": analyst.UNAVAILABLE}
-
-
-def critic_flags(engine: Engine, run_id: int) -> list[dict]:
-    """Each flag as shown: code's kind and category, its records, and the Critic's class or why there is none."""
-    from hypocurate.pipeline.agents import critic
-    return critic.flag_display(engine, run_id)
-
-
-def show(engine: Engine, run_id: int) -> dict | None:
-    from hypocurate.pipeline import statement
-    from hypocurate.pipeline import statistics as st
-    with engine.connect() as conn:
-        run = conn.execute(text(
-            "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
-            "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
-            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
-            "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
-        if run is None:
-            return None
-
-        def output(stage):
-            return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
-                                     "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
-
-        stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
-        results = [dict(r._mapping) for r in conn.execute(text(
-            "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
-            "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
-            "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
-            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
-        narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
-                                dict(r=run_id)).scalar_one_or_none()
-        original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
-                                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
-                                dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
-        cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
-    decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
-    built = statement.build(engine, run_id)  # decision A: code's statement, for every completed run
-    return {
-        # One presentation everywhere (owner, after the re-check): code's statement first, then the Analyst's text,
-        # only with the statement and only under its label; `run` and `dispatch` print this same output.
-        "statement": built["lines"] if built else None,
-        "analyst_text": analyst_text(explained) if built else None,
-        "run": run.id, "query": run.number, "claim": run.text, "outcome_code": run.outcome,
-        "question_as_tested": question_as_tested(engine, run.id), "status": run.status,
-        "narrower_question_of": original, "narrower_question": narrower,
-        # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
-        "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
-                else "the Planner's",
-        "sufficiency_option": run.sufficiency_option,
-        "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
-        "verdict": decision.get("verdict_wording") if run.verdict else None,
-        "exploratory": run.exploratory, "evidence_level": run.evidence_level,
-        "evidence_level_wording": decision.get("evidence_level_wording") if run.status == "completed" else None,
-        "label": decision.get("label"), "failure": run.failure_reason,
-        "results": [r for r in results if not r["withheld"]] if results else [],
-        "withheld": [{k: r[k] for k in ("scope", "source", "analysis_set", "n_records", "n_alloys", "n_groups",
-                                         "resid_df", "minimums_met")} for r in results if r["withheld"]],
-        "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
-        "sources": (gap or {}).get("sources"),
-        "statement_format": ({"current": built["format_version"], "recorded": built["recorded_format_version"]}
-                             if built else None),
-        "flags": critic_flags(engine, run_id),
-        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
-        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
-        # Step 9a: only for a waiting run, so every other run's output is as before.
-        **({"waiting_for": _waiting_for()} if run.status == "waiting" else {}),
-    }
-
-
-def _waiting_for() -> str:
-    from hypocurate.pipeline.confirmation import WAITING_FOR
-    return WAITING_FOR
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
index bd6f346..ba3e0ac 100644
--- a/hypocurate/pipeline/confirmation.py
+++ b/hypocurate/pipeline/confirmation.py
@@ -22,6 +22,8 @@ fixed-plan run of an ordinary question (criterion 14.1a) never waits.
 """
 from __future__ import annotations
 
+import hashlib
+import json
 from decimal import Decimal
 from typing import Any, Mapping
 
@@ -215,12 +217,26 @@ def _parts_lines(parts: list[dict]) -> list[str]:
     return [f"  {x['part']}: {', '.join(x['values'])}" + (f" ({x['marked']})" if x["marked"] else "") for x in parts]
 
 
+ONCE_BY, ONCE_AT = "the person who confirms", "the time of confirming (UTC)"
+
+
+def label_once_confirmed(label: str, by: str = ONCE_BY, at: str = ONCE_AT) -> str:
+    """The label the question as tested carries once confirmed (`reading._confirmed`'s wording)."""
+    if label == reading.LABELS["planner"]:
+        return reading.CONFIRMED_LABEL.format(by=by, at=at)
+    return f"{label}; confirmed by {by} on {at}"
+
+
 def render(c: Mapping[str, Any]) -> str:
     """The text shown before a person confirms (A2): every item of the content, in words."""
     n = c["narrowing"]
+    tested = c["question_as_tested"]
     lines = [f"Run {c['run']} of {c['query']} waits for {WAITING_FOR} before its rules lock.",
              f"Original question: {c['original_question']}",
-             f"Question as tested ({c['question_as_tested']['label']}): {c['question_as_tested']['text']}"]
+             f"Question as tested: {tested['text']}",
+             # Step 10a (the live-run record's open item 4): the label now, and the label once confirmed.
+             f"  Now labelled: {tested['label']}",
+             f"  Once confirmed, labelled: {label_once_confirmed(tested['label'])}"]
     if n["narrowed"]:
         lines.append(f"Narrowed: this is the narrower question of {n['original_query']} ({n['original_question']}).")
         lines.append("  Why: code found no candidate record in the sources searched for "
@@ -240,18 +256,26 @@ def render(c: Mapping[str, Any]) -> str:
     lines.append("Exclusion rules: " + ("; ".join(c["exclusion_rules"]) if c["exclusion_rules"] else "none"))
     s = c["sufficiency"]
     lines.append(f"Sufficiency option: {s['option'].replace('_', ' ')} (minimums: {s['min_records']} records, "
-                 f"{s['min_alloys']} alloys with at least 2 grain sizes, {s['min_groups']} independent groups, "
+                 f"{s['min_alloys']} alloys with at least 2 grain sizes, {s['min_groups']} informative groups, "
                  f"{s['min_resid_df']} residual degrees of freedom)")
     lines.append("Sources: " + "; ".join(
         f"{x['source']} version {x['version_fingerprint'][:12]}" if x["chosen"] else f"{x['source']} not chosen"
         for x in c["sources"]))
     k = c["cost_so_far"]
+    calls = f"{k['calls']} model call" + ("" if k["calls"] == 1 else "s")
     lines.append(f"Cost so far: ${k['counted_usd']} counted toward the caps (reported ${k['reported_usd']}; "
-                 f"{k['calls']} model calls, {k['calls_without_reported_cost']} without a reported cost)")
+                 f"{calls}, {k['calls_without_reported_cost']} without a reported cost)")
     lines.append(f"Plan to be locked: fingerprint {c['plan_fingerprint']}")
     return "\n".join(lines)
 
 
+def content_fingerprint(c: Mapping[str, Any]) -> str:
+    """SHA-256 of the content's canonical JSON (keys sorted, no spaces, UTF-8): what a confirmation page sends back so
+    that `confirm` can check it is still the content shown (owner's addition 2 of 2026-10-11)."""
+    canonical = json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
+    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
+
+
 def show(engine: Engine, run_id: int) -> tuple[dict, str]:
     """The content and its text, for a waiting run (what `confirm` prints before recording anything)."""
     with engine.connect() as conn:
@@ -259,9 +283,12 @@ def show(engine: Engine, run_id: int) -> tuple[dict, str]:
     return c, render(c)
 
 
-def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None) -> dict:
-    """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; the
-    confirmation is refused if it is no longer the current content. Returns the stored content and text."""
+def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None,
+            shown_fingerprint: str | None = None) -> dict:
+    """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; or
+    `shown_fingerprint`: the `content_fingerprint` of the content a page displayed (step 10a, owner's addition 2). The
+    confirmation is refused as `content_changed` if either differs from the current content, read in the same
+    transaction as the insert. Returns the stored content and text."""
     name = (by or "").strip()
     if not name or len(name) > CONFIRMED_BY_MAX:
         raise QueryRefused("name_required", f"a confirmation names the person (1 to {CONFIRMED_BY_MAX} characters)")
@@ -282,7 +309,8 @@ def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | Non
             c = content(conn, run_id)
         except NotLockable as error:
             raise QueryRefused(error.code, "the stored rows give no plan to lock") from None
-        if shown is not None and dict(shown) != c:
+        if (shown is not None and dict(shown) != c) or \
+                (shown_fingerprint is not None and shown_fingerprint != content_fingerprint(c)):
             raise QueryRefused("content_changed", "what was shown is no longer the run's current content; show it "
                                                   "again before confirming")
         words = render(c)
diff --git a/hypocurate/pipeline/progress.py b/hypocurate/pipeline/progress.py
new file mode 100644
index 0000000..d00f3a0
--- /dev/null
+++ b/hypocurate/pipeline/progress.py
@@ -0,0 +1,28 @@
+"""How long since a run last wrote anything (step 9b, A4; moved here from `pipeline.queue` in step 10a so that the
+screens can show it without importing the queue).
+
+Read-only. The worker's stall limit uses the same query through `queue`, which imports it from here; the screens and
+the command line's `queue` use it through `pipeline.run_view`. The web service imports neither the queue nor the
+worker (tests/test_web_isolation.py).
+"""
+from __future__ import annotations
+
+from sqlalchemy import Connection, text
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
diff --git a/hypocurate/pipeline/queue.py b/hypocurate/pipeline/queue.py
index 208b754..138cccf 100644
--- a/hypocurate/pipeline/queue.py
+++ b/hypocurate/pipeline/queue.py
@@ -42,6 +42,7 @@ from sqlalchemy import Connection, Engine, bindparam, text
 from sqlalchemy.dialects.postgresql import JSONB
 
 from hypocurate.db.retry import run_transaction
+from hypocurate.pipeline.progress import seconds_since_last_write  # noqa: F401 (step 10a: moved; still named here)
 
 LOG = logging.getLogger("hypocurate.worker")
 
@@ -257,19 +258,6 @@ class Heartbeat(threading.Thread):
         self.join(30)
 
 
-_LAST_WRITE = text("""
-    SELECT extract(epoch FROM clock_timestamp() - greatest(
-        r.queued_at, r.started_at, r.completed_at, r.failed_at,
-        (SELECT max(greatest(started_at, finished_at)) FROM stage_result WHERE run_id = r.id),
-        (SELECT max(greatest(started_at, finished_at)) FROM model_call WHERE run_id = r.id),
-        (SELECT max(decided_at) FROM run_source WHERE run_id = r.id),
-        (SELECT max(created_at) FROM record WHERE extraction_run_id = r.id),
-        (SELECT max(confirmed_at) FROM rules_confirmation WHERE run_id = r.id),
-        (SELECT locked_at FROM plan WHERE run_id = r.id),
-        (SELECT frozen_at FROM run_snapshot WHERE run_id = r.id)))
-    FROM run r WHERE r.id = :r""")
-
-
 _LAST_WRITE_EPOCH = text("""
     SELECT extract(epoch FROM greatest(
         r.queued_at, r.started_at, r.completed_at, r.failed_at,
@@ -324,9 +312,3 @@ class Monitor(threading.Thread):
 
     def stop(self) -> None:
         self._stop_event.set()  # never joined: a sample that blocks must not hold back the worker
-
-
-def seconds_since_last_write(conn: Connection, run_id: int) -> float:
-    """A4: seconds since the run last wrote anything that shows progress (its status times, a stage or call started or
-    finished, a source searched, a record stored, the confirmation, the lock, the freeze)."""
-    return float(conn.execute(_LAST_WRITE, dict(r=run_id)).scalar_one())
diff --git a/hypocurate/pipeline/reading.py b/hypocurate/pipeline/reading.py
index 1f6ad63..a578756 100644
--- a/hypocurate/pipeline/reading.py
+++ b/hypocurate/pipeline/reading.py
@@ -31,6 +31,8 @@ LABELS = {
 PART_LABELS = {"phase_class": "phase class", "test_type": "test type"}
 # Owner, 2026-10-08 (step 9a, question 2): the label once a person has confirmed the reading at the rules lock.
 CONFIRMED_LABEL = "the Planner's reading of the claim; not verified by code; confirmed by {by} on {at}"
+# Owner, 2026-10-11 (step 10a review): a Planner run whose plan was locked before confirmations existed (step 8b runs).
+PREDATES_LABEL = "the Planner's reading of the claim; not verified by code; this run predates confirmation"
 STATED = "as the claim states"
 ASSUMED = "assumed: the claim does not state it"
 
@@ -101,27 +103,40 @@ def from_plan(plan: Mapping[str, Any], source: str) -> dict[str, str]:
 
 
 def stored(conn: Connection, run_id: int) -> dict | None:
-    """The question as tested of a run: the Planner's stored reading, else the reading of its locked plan (fixed
-    or narrower), else the Planner's reading of a partly-sufficient original (no plan), else none. Once a named
-    person confirmed it (step 9a), its label says by whom and when."""
+    """The question as tested of a run: the Planner's stored reading, else the reading of its locked plan, else none
+    (a partly-sufficient original with no stored reading has no plan). The label's source is the run's own: a
+    narrower question's run, a fixed-plan run, or a Planner run, never a fallback to the fixed plan (step 10a: the
+    owner found a Planner run of step 8b, which stored no reading with its stage, labelled as the fixed reference
+    plan). Once a named person confirmed it (step 9a), its label says by whom and when; a Planner reading whose plan
+    was locked with no confirmation predates confirmations (`PREDATES_LABEL`)."""
+    run = conn.execute(text(
+        "SELECT r.fixed_plan, h.narrower_of_run_id, p.content AS plan FROM run r JOIN hypothesis_version hv ON hv.id = "
+        "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id LEFT JOIN plan p ON p.run_id = r.id "
+        "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
+    if run is None:
+        return None
     out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' AND status = "
                             "'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
     if isinstance(out, dict) and out.get("question_as_tested"):
-        return _confirmed(conn, run_id, out["question_as_tested"])
-    row = conn.execute(text("SELECT p.content, h.narrower_of_run_id FROM plan p JOIN run r ON r.id = p.run_id JOIN "
-                            "hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = "
-                            "hv.hypothesis_id WHERE p.run_id = :r"), dict(r=run_id)).one_or_none()
-    if row is None:
+        tested = out["question_as_tested"]
+    elif run.plan is None:
         return None
-    return _confirmed(conn, run_id, from_plan(row.content, "narrower" if row.narrower_of_run_id is not None else "fixed"))
+    else:
+        source = "narrower" if run.narrower_of_run_id is not None else "fixed" if run.fixed_plan else "planner"
+        tested = from_plan(run.plan, source)
+    return _confirmed(conn, run_id, tested, locked=run.plan is not None)
 
 
-def _confirmed(conn: Connection, run_id: int, tested: dict) -> dict:
-    """The reading with its label once a person confirmed it (owner, 2026-10-08, question 2); else as it is."""
+def _confirmed(conn: Connection, run_id: int, tested: dict, locked: bool = False) -> dict:
+    """The reading with its label once a person confirmed it (owner, 2026-10-08, question 2); a Planner reading locked
+    with no confirmation (only possible before step 9a's migration 0007) says that it predates confirmation (owner,
+    2026-10-11); else as it is."""
     row = conn.execute(text("SELECT confirmed_by, to_char(confirmed_at AT TIME ZONE 'UTC', "
                             "'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS at FROM rules_confirmation WHERE run_id = :r"),
                        dict(r=run_id)).one_or_none()
     if row is None:
+        if locked and tested["label"] == LABELS["planner"]:
+            return {**tested, "label": PREDATES_LABEL}
         return tested
     if tested["label"] == LABELS["planner"]:
         label = CONFIRMED_LABEL.format(by=row.confirmed_by, at=row.at)
diff --git a/hypocurate/pipeline/run_view.py b/hypocurate/pipeline/run_view.py
new file mode 100644
index 0000000..8f29b6f
--- /dev/null
+++ b/hypocurate/pipeline/run_view.py
@@ -0,0 +1,462 @@
+"""What a run looks like to a person: read-only views for the command line and the screens (build step 10a).
+
+`show` and `queue_rows` moved here from `cli_runs` unchanged (the command line imports them from here, so its output is
+the same). `run_page`, `runs_list` and `confirmation_page` give the screens everything they show as ready-made words
+and numbers: every number is formatted by `pipeline.display`, every statement line by `pipeline.statement`, and the
+confirmation content by `pipeline.confirmation`. A template only places these strings; it computes nothing (owner,
+step 10 brief).
+
+Nothing here writes, claims a run, runs a pipeline stage or calls a model; it imports neither the queue, the worker,
+the orchestrator nor recovery (tests/test_web_isolation.py).
+"""
+from __future__ import annotations
+
+from decimal import Decimal
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.db.models import TEST_RUN_LABEL
+from hypocurate.pipeline import display, progress
+from hypocurate.pipeline import statistics as st
+
+# What a run's status is called on the screens (step 10a; the live-run record's open item 3: a waiting run is shown as
+# waiting at the rules lock, never as stage "none").
+STATUS_WORDS = {"queued": "queued", "waiting": "waiting at the rules lock", "running": "running",
+                "completed": "completed", "failed": "failed"}
+WAITING_STAGE = "waiting at the rules lock"
+QUEUE_STAGE_WORDS = {"waiting": WAITING_STAGE, "queued": "queued (not started)"}  # the command line's `queue`
+# The stage of a running run (`access.stage.actual_stage`, unchanged), in words.
+STAGE_WORDS = {"before_lock": "before the rules lock (the Planner and code's narrowing decision)",
+               "narrowed": "after code's narrowing decision (no plan is locked)",
+               "curation": "curation (after the rules lock, before the dataset freeze)",
+               "closed_without_freeze": "closing without a dataset freeze",
+               "analysis": "analysis (after the dataset freeze)",
+               "final": "finished", "final_without_freeze": "finished without a dataset freeze",
+               "none": "not started"}
+# The sensitivity sets as people read them (step 10a; register 'sensitivity_set_display_names'). The internal keys are
+# never shown. The ninth set's name is the one eligibility already shows (`INFLUENCE_DISPLAY_NAME`).
+SET_DISPLAY_NAMES = {
+    "primary": "the locked plan's set (gives the verdict)",
+    "no_exclusions": "with no exclusion rules",
+    "tension_and_compression": "with tension and compression tests",
+    "six_batches_as_groups": "with Texas A&M grouped by its six batches",
+    "same_alloy_1_at_pct": "with alloys matched at 1 at.%",
+    "source_only_assignments": "with values assigned from the source only",
+    "scope_not_confirmed_included": "with records of unconfirmed scope included",
+    "possible_duplicates_separate": "with possible duplicates counted separately",
+    "conflicts_survivor_value": "with conflicting values counted once (survivor rule)",
+}
+# The one change of each set, in words for people (the eligibility code's own description, `SENSITIVITY_CHANGES`,
+# names internal sets; the ninth set's description is that one, which names none).
+SET_DESCRIPTIONS = {
+    "no_exclusions": "The plan's exclusion rules are dropped; the scope is kept.",
+    "tension_and_compression": "Tests in tension and in compression are both accepted.",
+    "six_batches_as_groups": "The Texas A&M records are grouped by their six batches instead of as one group; the "
+                             "records are the same.",
+    "same_alloy_1_at_pct": "Compositions are rounded to 1 at.% when deciding whether two records are the same alloy.",
+    "source_only_assignments": "Only values converted or assigned from the source are accepted; values assigned by "
+                               "decision are left out.",
+    "scope_not_confirmed_included": "Records whose scope cannot be confirmed are treated as in scope.",
+    "possible_duplicates_separate": "Records in unresolved or possible duplicate groups count as separate "
+                                    "measurements.",
+    # Owner's wording (2026-10-11): say that these values are normally left out.
+    "conflicts_survivor_value": "Conflicting values, left out of the main result, are included once each, using the "
+                                "survivor's value.",
+}
+STAGE_NAMES = {"planner": "Planner", "narrowing": "narrowing decision (code)", "curation": "curation (code)",
+               "checks": "checks (code)", "critic": "Critic", "inclusion": "inclusion (code)",
+               "dataset_freeze": "dataset freeze (code)", "statistics": "statistics (code)",
+               "gap_facts": "gap facts (code)", "analyst": "Analyst"}
+OPEN_STATUSES = ("queued", "waiting", "running")  # the screens update these by themselves (static/poll.js)
+NOT_COMPLETED = "No evidence level yet (not completed)"
+FAILED_NO_LEVEL = "failed: no evidence level"  # owner, 2026-10-11
+# The stored label of a marked run (register 'constructed_test_runs'), shown as it is stored.
+TEST_RUN_BADGE = TEST_RUN_LABEL
+
+
+def _set_description(key: str | None) -> str:
+    from hypocurate.pipeline.eligibility import INFLUENCE_KEY, SENSITIVITY_CHANGES
+    if key == INFLUENCE_KEY:
+        return SENSITIVITY_CHANGES[INFLUENCE_KEY][:1].upper() + SENSITIVITY_CHANGES[INFLUENCE_KEY][1:] + "."
+    return SET_DESCRIPTIONS.get(key or "", "")
+
+
+def _set_display_name(key: str | None) -> str:
+    from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, INFLUENCE_KEY
+    if key == INFLUENCE_KEY:
+        return INFLUENCE_DISPLAY_NAME
+    return SET_DISPLAY_NAMES.get(key or "", "another sensitivity set")
+
+
+def money(value) -> str:
+    """US dollars to six decimals, as the run record holds them."""
+    return f"${Decimal(value or 0):.6f}"
+
+
+def tokens(value) -> str:
+    return f"{int(value or 0):,}"
+
+
+# --- moved from cli_runs (step 10a), unchanged ---------------------------------------------------------------------
+
+def question_as_tested(engine: Engine, run_id: int) -> dict | None:
+    from hypocurate.pipeline import reading
+    with engine.connect() as conn:
+        return reading.stored(conn, run_id)
+
+
+def analyst_text(explained) -> dict:
+    """The Analyst's stored explanation, always with its label; or that it is unavailable (code's own words)."""
+    from hypocurate.pipeline.agents import analyst
+    if isinstance(explained, dict) and explained.get("report"):
+        return {"label": analyst.LABEL, "text": explained["report"]}
+    if isinstance(explained, dict):
+        return {"unavailable": explained.get("shown") or analyst.UNAVAILABLE}
+    return {"unavailable": analyst.UNAVAILABLE}
+
+
+def critic_flags(engine: Engine, run_id: int) -> list[dict]:
+    """Each flag as shown: code's kind and category, its records, and the Critic's class or why there is none."""
+    from hypocurate.pipeline.agents import critic
+    return critic.flag_display(engine, run_id)
+
+
+def queue_rows(engine: Engine) -> list[dict]:
+    """`queue` (R2): every queued, waiting or running run, with its stage, its claim's worker and heartbeat age, the
+    time since the run last wrote anything (A4), and how often it was taken up again."""
+    from hypocurate.access.stage import actual_stage
+    from hypocurate.pipeline import confirmation
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
+                # Step 10a (the live-run record's open item 3): a waiting or queued run says where it is, never
+                # "none" (the access layer's `actual_stage` is unchanged).
+                "run": r.id, "query": r.number, "status": r.status,
+                "stage": QUEUE_STAGE_WORDS.get(r.status) or actual_stage(conn, r.id, r.status),
+                "waiting_for": (confirmation.WAITING_FOR if r.status == "waiting" and not r.confirmed else
+                                "a worker (confirmed)" if r.status == "waiting" else None),
+                "worker": r.worker, "heartbeat_age_seconds": round(float(r.heartbeat_age), 1)
+                if r.heartbeat_age is not None else None,
+                "seconds_since_last_write": round(progress.seconds_since_last_write(conn, r.id), 1),
+                "recoveries": int(r.recoveries)})
+    return out
+
+
+def show(engine: Engine, run_id: int) -> dict | None:
+    from hypocurate.pipeline import statement
+    with engine.connect() as conn:
+        run = conn.execute(text(
+            "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
+            "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
+            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+            "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
+        if run is None:
+            return None
+
+        def output(stage):
+            return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
+                                     "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
+
+        stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
+        results = [dict(r._mapping) for r in conn.execute(text(
+            "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
+            "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
+            "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
+            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
+        narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
+                                dict(r=run_id)).scalar_one_or_none()
+        original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
+                                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
+                                dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
+        cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
+    decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
+    built = statement.build(engine, run_id)  # decision A: code's statement, for every completed run
+    return {
+        # One presentation everywhere (owner, after the re-check): code's statement first, then the Analyst's text,
+        # only with the statement and only under its label; `run` and `dispatch` print this same output.
+        "statement": built["lines"] if built else None,
+        "analyst_text": analyst_text(explained) if built else None,
+        "run": run.id, "query": run.number, "claim": run.text, "outcome_code": run.outcome,
+        "question_as_tested": question_as_tested(engine, run.id), "status": run.status,
+        "narrower_question_of": original, "narrower_question": narrower,
+        # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
+        "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
+                else "the Planner's",
+        "sufficiency_option": run.sufficiency_option,
+        "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
+        "verdict": decision.get("verdict_wording") if run.verdict else None,
+        "exploratory": run.exploratory, "evidence_level": run.evidence_level,
+        "evidence_level_wording": decision.get("evidence_level_wording") if run.status == "completed" else None,
+        "label": decision.get("label"), "failure": run.failure_reason,
+        "results": [r for r in results if not r["withheld"]] if results else [],
+        "withheld": [{k: r[k] for k in ("scope", "source", "analysis_set", "n_records", "n_alloys", "n_groups",
+                                         "resid_df", "minimums_met")} for r in results if r["withheld"]],
+        "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
+        "sources": (gap or {}).get("sources"),
+        "statement_format": ({"current": built["format_version"], "recorded": built["recorded_format_version"]}
+                             if built else None),
+        "flags": critic_flags(engine, run_id),
+        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
+        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
+        # Step 9a: only for a waiting run, so every other run's output is as before.
+        **({"waiting_for": _waiting_for()} if run.status == "waiting" else {}),
+    }
+
+
+def _waiting_for() -> str:
+    from hypocurate.pipeline.confirmation import WAITING_FOR
+    return WAITING_FOR
+
+
+# --- the screens (step 10a) ----------------------------------------------------------------------------------------
+
+def evidence(level: int | None, verdict_wording: str | None, wording: str | None, test_run: bool,
+             failed: bool = False) -> dict:
+    """The evidence level as the dial shows it: the level, its short label (`statistics.EVIDENCE_SHORT`), the long
+    wording code stored, the verdict shown beside the dial, and whether the run is a marked test run."""
+    if level is None:
+        return {"level": None, "words": FAILED_NO_LEVEL if failed else NOT_COMPLETED, "wording": None,
+                "verdict": None, "test_run": test_run}
+    return {"level": level, "words": f"Level {level} of {len(st.EVIDENCE_SHORT)}: {st.EVIDENCE_SHORT[level]}",
+            "wording": wording, "verdict": verdict_wording, "test_run": test_run}
+
+
+def _result_words(e: Mapping, withheld: bool) -> str:
+    """One result in words, from stored numbers formatted by `display`."""
+    if withheld or e.get("withheld"):
+        return "withheld: the minimums were not met"
+    if e.get("estimate") is None:
+        reason = str(e.get("inference_reason") or "coefficient not fitted").replace("_", " ")
+        return f"no coefficient fitted ({reason})"
+    k = display.coefficient(e["estimate"])
+    if e.get("p_value") is None:
+        reason = str(e.get("inference_reason") or "no valid inference").replace("_", " ")
+        return f"{k}; coefficient only ({reason}): no uncertainty, no p-value"
+    return f"{k} ± {display.coefficient(e['std_error'])} (one standard error); {display.p_phrase(e['p_value'])}"
+
+
+def _counts_words(e: Mapping) -> dict:
+    c = e.get("counts") or {}
+    return {"records": c.get("n_records"), "alloys": c.get("n_alloys"), "groups": c.get("n_groups"),
+            "informative": c.get("n_groups_informative"), "resid_df": c.get("resid_df")}
+
+
+def _tables(stats: Mapping, kinds: Mapping[str, str]) -> dict:
+    """Per-source and sensitivity rows from the stored statistics output (the order `statement` uses)."""
+    from hypocurate.pipeline import analyst_names as an
+    from hypocurate.pipeline.statement import _ordered, _source_name
+    analyses = _ordered(stats.get("analyses") or [])
+    withheld, alpha = bool(stats.get("withheld")), stats.get("alpha")
+    if not analyses:
+        return {"pooled": None, "per_source": [], "sensitivity": []}
+    pooled = analyses[0]
+    inference = pooled.get("p_value") is not None and not withheld
+    per_source = [{"name": "All sources together", "kind": ", ".join(sorted(set(kinds.values()))) or "—",
+                   **_counts_words(pooled), "result": _result_words(pooled, withheld),
+                   "against": "gives the verdict" if inference else "no verdict"}]
+    for e in analyses:
+        if e.get("scope") == "per_source":
+            per_source.append({"name": _source_name(e["source"]), "kind": kinds.get(e["source"], "—"),
+                               **_counts_words(e), "result": _result_words(e, withheld),
+                               "against": an.label_words(e) if e.get("label") else "—"})
+    sensitivity = []
+    for e in analyses:
+        if e.get("scope") != "sensitivity":
+            continue
+        against = "—"
+        if inference and e.get("estimate") is not None:
+            against = an.label_words({**e, "label": st.label(e, pooled, alpha)})
+        sensitivity.append({"name": _set_display_name(e.get("set")), "change": _set_description(e.get("set")),
+                            **_counts_words(e), "result": _result_words(e, withheld), "against": against})
+    return {"pooled": pooled, "per_source": per_source, "sensitivity": sensitivity}
+
+
+def _statement_parts(lines: list[str] | None) -> dict:
+    """Code's statement split for the page into its body, its cautions and its format lines. The lines are
+    `statement.build`'s, unchanged and in their order; nothing is reworded."""
+    if not lines:
+        return {"body": [], "cautions": [], "format": []}
+    start = next((i for i, x in enumerate(lines) if x.startswith("Main cautions")), None)
+    end = next((i for i, x in enumerate(lines) if x.startswith("Statement format ")), len(lines))
+    if start is None:
+        return {"body": lines[:end], "cautions": [], "format": lines[end:]}
+    return {"body": lines[:start], "cautions": lines[start:end], "format": lines[end:]}
+
+
+def _analyst(a: Mapping | None) -> dict | None:
+    """The Analyst's stored text, always with its label, or why there is none."""
+    if a is None:
+        return None
+    if a.get("text"):  # shown in a small safe subset of Markdown (web/textfmt.model_text)
+        return {"label": a["label"], "text": a["text"]}
+    return {"unavailable": a.get("unavailable")}
+
+
+def _claim_facts(conn: Connection, run_id: int) -> dict:
+    row = conn.execute(text(
+        "SELECT c.worker, to_char(c.claimed_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS claimed, "
+        "extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age FROM run_claim c "
+        "WHERE c.run_id = :r AND c.released_at IS NULL"), dict(r=run_id)).one_or_none()
+    claims = conn.execute(text(
+        "SELECT count(*) AS claims, count(*) FILTER (WHERE recovery) AS recoveries FROM run_claim WHERE run_id = :r"),
+        dict(r=run_id)).one()
+    return {"worker": row.worker if row else None, "claimed": row.claimed if row else None,
+            "heartbeat_age": f"{float(row.heartbeat_age):.1f} s" if row and row.heartbeat_age is not None else None,
+            "since_last_write": f"{progress.seconds_since_last_write(conn, run_id):.1f} s",
+            "claims": int(claims.claims), "recoveries": int(claims.recoveries)}
+
+
+def _time(conn: Connection, column: str, table: str, run_id: int, key: str = "run_id") -> str | None:
+    return conn.execute(text(f"SELECT to_char({column} AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') "
+                             f"FROM {table} WHERE {key} = :r"), dict(r=run_id)).scalar_one_or_none()
+
+
+def run_page(engine: Engine, run_id: int) -> dict | None:
+    """Everything the run viewer shows, as ready-made words and numbers."""
+    from hypocurate.access.stage import actual_stage
+    shown = show(engine, run_id)
+    if shown is None:
+        return None
+    with engine.connect() as conn:
+        head = conn.execute(text(
+            "SELECT r.status, r.experiment_flags, r.spending_ceiling, r.agent_mode, hv.version_number, d.name AS domain, "
+            "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS queued, "
+            "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS ended, "
+            "EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS confirmed "
+            "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+            "JOIN domain d ON d.id = coalesce(hv.confirmed_domain_id, hv.domain_id) WHERE r.id = :r"),
+            dict(r=run_id)).one()
+        tags = conn.execute(text(
+            "SELECT tv.kind, tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r "
+            "ORDER BY tv.kind, tv.value"), dict(r=run_id)).all()
+        plan = conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
+        freeze = conn.execute(text("SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r"),
+                              dict(r=run_id)).one_or_none()
+        locked_at, frozen_at = _time(conn, "locked_at", "plan", run_id), _time(conn, "frozen_at", "run_snapshot", run_id)
+        stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
+                                  "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+        kinds = dict(conn.execute(text("SELECT s.key, s.data_kind FROM run_source rs JOIN source s ON s.id = "
+                                       "rs.source_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
+        sources = conn.execute(text(
+            "SELECT s.key, s.name, rs.search_status, rs.nothing_found FROM run_source rs JOIN source s ON s.id = "
+            "rs.source_id WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()
+        stages = conn.execute(text(
+            "SELECT sr.stage, sr.attempt, sr.status, sr.model, t.calls, t.input_tokens, t.output_tokens, t.reported_cost "
+            "FROM stage_result sr LEFT JOIN model_call_totals_by_stage t ON t.stage_result_id = sr.id "
+            "WHERE sr.run_id = :r ORDER BY sr.id"), dict(r=run_id)).all()
+        stage = actual_stage(conn, run_id, head.status) if head.status == "running" else None
+        facts = _claim_facts(conn, run_id) if head.status in ("queued", "waiting", "running") else None
+    test_run = bool((head.experiment_flags or {}).get("constructed_test_data"))
+    cost = shown["tokens_and_cost"] or {}
+    tables = _tables(stats or {}, kinds)
+    return {
+        "run": run_id, "query": shown["query"], "version": head.version_number, "claim": shown["claim"],
+        "status": head.status, "status_words": STATUS_WORDS[head.status],
+        "stage_words": STAGE_WORDS.get(stage) if stage else (WAITING_STAGE if head.status == "waiting" else None),
+        "waiting_for": shown.get("waiting_for"), "confirmed": head.confirmed,
+        "can_confirm": head.status == "waiting" and not head.confirmed,
+        "can_cancel": head.status in ("queued", "waiting"),
+        "open": head.status in OPEN_STATUSES,
+        "failure": shown["failure"], "domain": head.domain, "queued": head.queued, "ended": head.ended,
+        "tags": [f"{k.replace('_', ' ')}: {v}" for k, v in tags], "plan_kind": shown["plan"],
+        "agent_mode": head.agent_mode.replace("_", " "), "ceiling": money(head.spending_ceiling) if head.spending_ceiling is not None else "not recorded",
+        "test_run": test_run, "test_run_badge": TEST_RUN_BADGE if test_run else None,
+        "question_as_tested": shown["question_as_tested"],
+        "evidence": evidence(shown["evidence_level"], shown["verdict"], shown["evidence_level_wording"], test_run,
+                             failed=head.status == "failed"),
+        "outcome": shown["outcome"], "verdict": shown["verdict"], "exploratory": shown["exploratory"],
+        "statement": _statement_parts(shown["statement"]),
+        "analyst": _analyst(shown["analyst_text"]),
+        "per_source": tables["per_source"], "sensitivity": tables["sensitivity"],
+        "checkpoints": {"rules_lock": {"at": locked_at, "fingerprint": plan},
+                        "dataset_freeze": {"at": frozen_at, "fingerprint": freeze.fingerprint if freeze else None,
+                                           "records": freeze.n_records if freeze else None}},
+        "sources": [{"name": s.name, "status": s.search_status.replace("_", " "),
+                     "nothing_found": s.nothing_found.replace("_", " ") if s.nothing_found else None} for s in sources],
+        "flags": shown["flags"],
+        "stages": [{"name": STAGE_NAMES.get(s.stage, s.stage), "attempt": s.attempt, "status": s.status,
+                    "model": s.model, "calls": int(s.calls or 0), "input_tokens": tokens(s.input_tokens),
+                    "output_tokens": tokens(s.output_tokens), "cost": money(s.reported_cost)} for s in stages],
+        "cost": {"calls": int(cost.get("calls") or 0),
+                 "calls_words": f"{int(cost.get('calls') or 0)} model call{'' if int(cost.get('calls') or 0) == 1 else 's'}", "input_tokens": tokens(cost.get("input_tokens")),
+                 "output_tokens": tokens(cost.get("output_tokens")), "reported": money(cost.get("reported_cost")),
+                 "counted": money(cost.get("cap_cost")),
+                 "unconfirmed_calls": int(cost.get("unconfirmed_calls") or 0)},
+        "claim_facts": facts,
+        "p_value_description": shown["p_value_description"],
+    }
+
+
+def runs_list(engine: Engine, limit: int = 200) -> list[dict]:
+    """Every run, newest first: query, claim, status, outcome, evidence level and cost."""
+    with engine.connect() as conn:
+        rows = conn.execute(text(
+            "SELECT r.id, r.status, r.evidence_level, r.verdict, r.experiment_flags, h.number, hv.text, "
+            "r.outcome, to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS queued, "
+            "coalesce(t.cap_cost, 0) AS cost FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+            "JOIN hypothesis h ON h.id = hv.hypothesis_id LEFT JOIN model_call_totals_by_run t ON t.run_id = r.id "
+            "ORDER BY r.id DESC LIMIT :n"), dict(n=limit)).all()
+    out = []
+    for r in rows:
+        test_run = bool((r.experiment_flags or {}).get("constructed_test_data"))
+        out.append({"run": r.id, "query": r.number, "claim": r.text, "status": r.status,
+                    "status_words": STATUS_WORDS[r.status], "queued": r.queued,
+                    "outcome": r.outcome.replace("_", " ") + " in the sources searched" if r.outcome else None,
+                    "evidence": evidence(r.evidence_level, None, None, test_run, failed=r.status == "failed"),
+                    "cost": money(r.cost)})
+    return out
+
+
+def _text_rows(words: str) -> list[dict]:
+    """The confirmation text, line by line, for the page: each line's leading words before its first colon as a
+    heading, the rest as its value; the words are `confirmation.render`'s, unchanged."""
+    rows = []
+    for line in words.split("\n"):
+        indent = len(line) - len(line.lstrip(" "))
+        body = line.strip()
+        head, sep, rest = body.partition(": ")
+        if sep and len(head) <= 60 and not head.endswith("."):
+            rows.append({"indent": indent > 0, "head": head, "value": rest})
+        else:
+            rows.append({"indent": indent > 0, "head": None, "value": body})
+    return rows
+
+
+def confirmation_page(engine: Engine, run_id: int, name: str | None) -> dict | None:
+    """A waiting run's confirmation: the content and its text exactly as `confirm` shows them, the content's
+    fingerprint, which the page sends back (owner's addition 2), and the label the question as tested will carry once
+    `name` confirms it."""
+    from hypocurate.pipeline import confirmation
+    page = run_page(engine, run_id)
+    if page is None:
+        return None
+    if not page["can_confirm"]:
+        return {**page, "content": None}
+    content, words = confirmation.show(engine, run_id)
+    after = confirmation.label_once_confirmed(content["question_as_tested"]["label"], by=name or "you",
+                                              at="the time you confirm (UTC)")
+    return {**page, "content": content, "text": words, "rows": _text_rows(words),
+            "content_fingerprint": confirmation.content_fingerprint(content), "label_after": after}
+
+
+def spending(engine: Engine) -> dict:
+    """The menu's spending panel: the caps and this month's spend as the monthly cap counts it (`spend.month_total`),
+    with the month's tokens (calendar month, UTC)."""
+    from hypocurate.pipeline.agents import spend
+    with engine.connect() as conn:
+        counted = spend.month_total(conn)
+        month_tokens = conn.execute(text(
+            "SELECT coalesce(sum(input_tokens + output_tokens), 0) FROM model_call WHERE date_trunc('month', "
+            "started_at AT TIME ZONE 'UTC') = date_trunc('month', now() AT TIME ZONE 'UTC')")).scalar_one()
+    return {"per_run_cap": money(spend.RUN_CAP_USD), "monthly_cap": money(spend.MONTH_CAP_USD),
+            "month_counted": money(counted), "month_tokens": tokens(month_tokens)}
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index 31d3c6f..545047e 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -118,6 +118,16 @@ EVIDENCE_LEVELS = MappingProxyType({
     2: "coefficient cannot be fitted",
     1: "no dataset frozen",
 })
+# The dial's short label for each level (owner, 2026-10-11, step 10a answer 2; register 'evidence_dial'): shown as
+# "Level n of 6: <label>", with the long wording above beneath it. Descriptive only, like the level.
+EVIDENCE_SHORT = MappingProxyType({
+    6: "tested answer",
+    5: "exploratory answer",
+    4: "coefficient only",
+    3: "below the minimums",
+    2: "no coefficient fitted",
+    1: "nothing tested",
+})
 # Owner's addition 1 (2026-10-06; step 8b): a partly-sufficient original question is at level 1, shown as
 # this wording (it was never tested; code's narrowing decision proposed a narrower question).
 PARTLY_SUFFICIENT_WORDING = "original question not tested; a narrower question was proposed"
diff --git a/hypocurate/web/app.py b/hypocurate/web/app.py
index 15e6504..ab99d20 100644
--- a/hypocurate/web/app.py
+++ b/hypocurate/web/app.py
@@ -1,20 +1,27 @@
-"""The web service (PRD Section 6): login, health page, a placeholder home page, and the
-read-only assumptions register (step 4b, /assumptions).
+"""The web service (PRD Section 6): login, health page, the read-only assumptions register (step 4b, /assumptions),
+and from step 10a the run pages: the runs list, the run viewer, the confirmation of the question as tested, and cancel.
 
 Every page needs the shared login except exactly /login and /health, and the
 files under /static/. The session is a signed cookie (Starlette
-SessionMiddleware, itsdangerous) holding only {"signed_in": true}; in
+SessionMiddleware, itsdangerous) holding {"signed_in": true, "name": ..., "csrf": ...}
+(step 10a: the name given at sign-in and the token every write carries; `web/security.py`); in
 production it is sent over HTTPS only. There is no server-side session record:
 rotating SESSION_SECRET ends every session (README, "Sessions").
+
+The web service never calls a model, never claims a run and never runs a pipeline stage (step 10 brief). It reads
+through `pipeline.run_view` and writes only through the pipeline's own functions: `confirmation.confirm` and
+`queries.cancel` in 10a. A confirmed run is taken up by the worker; closing the browser or restarting this service
+never affects a run (criterion 14.4).
 """
 from __future__ import annotations
 
 from pathlib import Path
 
-from fastapi import FastAPI, Form, Request
+from fastapi import FastAPI, Form, HTTPException, Request
 from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
 from fastapi.staticfiles import StaticFiles
 from fastapi.templating import Jinja2Templates
+from markupsafe import Markup
 from sqlalchemy import Engine
 from starlette.middleware.sessions import SessionMiddleware
 
@@ -22,6 +29,7 @@ from hypocurate import assumptions
 from hypocurate.config import Settings, load_settings
 from hypocurate.db.engine import database_reachable, make_engine
 from hypocurate.db.migrate import schema_status
+from hypocurate.web import dial, glossary, security, textfmt
 from hypocurate.web.login_throttle import Attempt, LoginThrottle
 
 HERE = Path(__file__).resolve().parent
@@ -29,10 +37,29 @@ SESSION_COOKIE = "hypocurate_session"
 SESSION_MAX_AGE = 12 * 60 * 60
 PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
 STATIC_PREFIX = "/static/"
+# What the run page says after an action: fixed words, chosen by a fixed key (never text from the address).
+DONE = {"confirmed": "Confirmed under your name. The run waits for a worker to take it up; this page updates by itself.",
+        "cancelled": "Cancelled under your name."}
+ALREADY_SIGNED_IN = "You are signed in as {name}. To act under another name, sign out first, then sign in again."
 
 templates = Jinja2Templates(directory=HERE / "templates")
 
 
+def _info(key: str) -> Markup:
+    """An information button (PRD 9.7) with the glossary's text; opens on hover, focus and click, closes on Escape
+    or when focus leaves (static/info.js)."""
+    e = glossary.entry(key)
+    tip = f"tip-{key}"
+    return Markup(
+        f'<span class="info"><button type="button" class="info-button" aria-label="Explain: {Markup.escape(e["term"])}"'
+        f' aria-describedby="{tip}" aria-expanded="false">i</button>'
+        f'<span class="info-text" role="tooltip" id="{tip}" hidden>{Markup.escape(e["text"])}</span></span>')
+
+
+templates.env.globals.update(info=_info, dial=dial.svg)
+templates.env.filters.update(units=textfmt.units, model_text=textfmt.model_text)
+
+
 def create_app(
     settings: Settings | None = None,
     engine: Engine | None = None,
@@ -47,6 +74,7 @@ def create_app(
         register = assumptions.load_register()
     else:
         assumptions.validate(register)
+    glossary.entries()  # likewise the glossary
 
     app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)
 
@@ -69,30 +97,51 @@ def create_app(
     )
     app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
 
+    def page(request: Request, name: str, context: dict, status_code: int = 200, spending: bool = True):
+        """A signed-in page: the menu with the signed-in name, the session's form token, and the spending panel (on
+        the pages that read the database; the home and assumptions pages do not)."""
+        from hypocurate.pipeline import run_view
+        return templates.TemplateResponse(request, name, {
+            **context, "signed_in_as": request.session.get("name") or "", "csrf_token": security.csrf_token(request),
+            "csrf_field": security.CSRF_FIELD, "spending": run_view.spending(engine) if spending else None},
+            status_code=status_code)
+
     @app.get("/", response_class=HTMLResponse)
     def home(request: Request):
-        return templates.TemplateResponse(request, "home.html", {})
+        return page(request, "home.html", {}, spending=False)
 
     @app.get("/login", response_class=HTMLResponse)
     def login_form(request: Request):
-        return templates.TemplateResponse(request, "login.html", {"error": None})
+        return templates.TemplateResponse(request, "login.html", {
+            "error": None, "current_name": (request.session.get("name") or "a session without a name") if request.session.get("signed_in") else None,
+            "name_max": security.NAME_MAX})
 
     @app.post("/login")
-    def login(request: Request, password: str = Form("")) -> Response:
+    def login(request: Request, password: str = Form(""), name: str = Form("")) -> Response:
+        if request.session.get("signed_in"):  # owner's addition 3: the name cannot change within a session
+            current = request.session.get("name") or "a session without a name"
+            return templates.TemplateResponse(
+                request, "login.html", {"error": ALREADY_SIGNED_IN.format(name=current),
+                                        "current_name": current, "name_max": security.NAME_MAX}, status_code=409)
         result = throttle.attempt(password, settings.password)
         if result is Attempt.OK:
-            request.session.clear()
-            request.session["signed_in"] = True
+            try:
+                clean = security.clean_name(name)
+            except security.NameRefused as refused:
+                return templates.TemplateResponse(request, "login.html", {
+                    "error": str(refused), "current_name": None, "name_max": security.NAME_MAX}, status_code=400)
+            security.start_session(request, clean)
             return RedirectResponse("/", status_code=303)
         if result is Attempt.THROTTLED:
             return templates.TemplateResponse(
                 request, "login.html",
-                {"error": "Too many failed attempts. Try again in a few minutes."},
+                {"error": "Too many failed attempts. Try again in a few minutes.", "current_name": None,
+                 "name_max": security.NAME_MAX},
                 status_code=429,
             )
         return templates.TemplateResponse(
-            request, "login.html", {"error": "Wrong password."}, status_code=401
-        )
+            request, "login.html", {"error": "Wrong password.", "current_name": None, "name_max": security.NAME_MAX},
+            status_code=401)
 
     @app.post("/logout")
     def logout(request: Request) -> Response:
@@ -103,13 +152,84 @@ def create_app(
     def assumptions_page(request: Request, review: str | None = None):
         """Read-only: generated from hypocurate/assumptions.json; nothing is edited here."""
         not_reviewed_only = review == "not_reviewed"
-        return templates.TemplateResponse(request, "assumptions.html", {
+        return page(request, "assumptions.html", {
             "sections": assumptions.page_sections(register, not_reviewed_only=not_reviewed_only),
             "counts": assumptions.summary_counts(register),
             "not_reviewed_only": not_reviewed_only,
             "categories": assumptions.CATEGORIES,
             "review_labels": assumptions.REVIEW_STATUSES,
-        })
+        }, spending=False)
+
+    # --- the run pages (step 10a) ---------------------------------------------------------------------------------
+
+    @app.get("/runs", response_class=HTMLResponse)
+    def runs(request: Request):
+        from hypocurate.pipeline import run_view
+        return page(request, "runs.html", {"runs": run_view.runs_list(engine)})
+
+    @app.get("/runs/{run_id}", response_class=HTMLResponse)
+    def run(request: Request, run_id: int):
+        from hypocurate.pipeline import run_view
+        shown = run_view.run_page(engine, run_id)
+        if shown is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        return page(request, "run.html", {"r": shown, "message": DONE.get(request.query_params.get("done", ""))})
+
+    @app.get("/runs/{run_id}/state", response_class=HTMLResponse)
+    def run_state(request: Request, run_id: int):
+        """The run's state alone, which static/poll.js asks for while the run is open. Read-only, like every page."""
+        from hypocurate.pipeline import run_view
+        shown = run_view.run_page(engine, run_id)
+        if shown is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        return templates.TemplateResponse(request, "_state.html", {
+            "r": shown, "csrf_token": security.csrf_token(request), "csrf_field": security.CSRF_FIELD},
+            headers={"Cache-Control": "no-store"})
+
+    @app.get("/runs/{run_id}/confirm", response_class=HTMLResponse)
+    def confirm_form(request: Request, run_id: int):
+        from hypocurate.pipeline import run_view
+        shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
+        if shown is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        return page(request, "confirm.html", {"r": shown, "error": None})
+
+    @app.post("/runs/{run_id}/confirm")
+    def confirm(request: Request, run_id: int, csrf_token: str = Form(""), content_fingerprint: str = Form("")):
+        from hypocurate.pipeline import confirmation, queries, run_view
+        security.check_csrf(request, csrf_token)
+        name = security.signed_in_name(request)
+        if run_view.run_page(engine, run_id) is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        try:
+            if not content_fingerprint:
+                raise queries.QueryRefused("content_changed", "the page sent no fingerprint of what it showed; show "
+                                                              "it again before confirming")
+            confirmation.confirm(engine, run_id, name, shown_fingerprint=content_fingerprint)
+        except queries.QueryRefused as refused:
+            shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
+            if shown is None:
+                raise HTTPException(status_code=404, detail=f"no run {run_id}") from None
+            return page(request, "confirm.html", {"r": shown, "error": f"Not confirmed: {refused.reason}"},
+                        status_code=409)
+        return RedirectResponse(f"/runs/{run_id}?done=confirmed", status_code=303)
+
+    @app.post("/runs/{run_id}/cancel")
+    def cancel(request: Request, run_id: int, csrf_token: str = Form("")):
+        from hypocurate.pipeline import queries, run_view
+        security.check_csrf(request, csrf_token)
+        name = security.signed_in_name(request)
+        if run_view.run_page(engine, run_id) is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        try:
+            queries.cancel(engine, run_id, by=name)
+        except queries.QueryRefused as refused:
+            shown = run_view.run_page(engine, run_id)
+            if shown is None:
+                raise HTTPException(status_code=404, detail=f"no run {run_id}") from None
+            return page(request, "run.html", {"r": shown, "message": None, "error": f"Not cancelled: {refused.reason}"},
+                        status_code=409)
+        return RedirectResponse(f"/runs/{run_id}?done=cancelled", status_code=303)
 
     @app.get("/health")
     def health(request: Request) -> Response:
diff --git a/hypocurate/web/dial.py b/hypocurate/web/dial.py
new file mode 100644
index 0000000..9154b36
--- /dev/null
+++ b/hypocurate/web/dial.py
@@ -0,0 +1,69 @@
+"""The evidence-level dial (step 10a; owner's brief and answer 2 of 2026-10-11).
+
+A half circle of six separate segments, one per level, in one hue that darkens with the level (never red to green),
+with a needle on the run's level. A marked test run's dial is hatched; its "test run" badge and every word are HTML
+next to the drawing, never text inside it, so no text on the page is smaller than 12 px (owner's addition 6). The
+verdict is shown beside the dial by the page, never in it. The level comes from the run (`run.evidence_level`, set by
+code); this module only draws it.
+"""
+from __future__ import annotations
+
+import math
+from itertools import count
+
+from markupsafe import Markup
+
+LEVELS = 6
+# One hue (blue, 215°), lightest at level 1, darkest at level 6 (register 'evidence_dial').
+SHADES = ("#dde6f3", "#b9cbe7", "#8ea9d6", "#6286c2", "#3a63a6", "#1d3f78")
+EMPTY = "#eceef2"
+NEEDLE = "#1d2330"
+SIZES = {"large": 220, "small": 64}
+_ids = count(1)
+
+
+def _point(cx: float, cy: float, r: float, degrees: float) -> tuple[float, float]:
+    a = math.radians(degrees)
+    return cx + r * math.cos(a), cy - r * math.sin(a)
+
+
+def _segment(i: int, cx: float, cy: float, outer: float, inner: float, gap: float) -> str:
+    """Segment i (1..6) from the left (180°) to the right (0°), as an annulus path."""
+    span = 180 / LEVELS
+    start, end = 180 - (i - 1) * span - gap / 2, 180 - i * span + gap / 2
+    x1, y1 = _point(cx, cy, outer, start)
+    x2, y2 = _point(cx, cy, outer, end)
+    x3, y3 = _point(cx, cy, inner, end)
+    x4, y4 = _point(cx, cy, inner, start)
+    return (f"M{x1:.2f},{y1:.2f} A{outer},{outer} 0 0 1 {x2:.2f},{y2:.2f} L{x3:.2f},{y3:.2f} "
+            f"A{inner},{inner} 0 0 0 {x4:.2f},{y4:.2f} Z")
+
+
+def svg(level: int | None, test_run: bool = False, size: str = "large", label: str = "") -> Markup:
+    """The dial as inline SVG. `label` is its accessible name (the words shown beside it)."""
+    width = SIZES[size]
+    cx, cy, outer, inner = 100, 100, 92, 58
+    uid = next(_ids)
+    parts = [f'<svg class="dial dial-{size}" width="{width}" height="{width // 2 + 4}" viewBox="0 0 200 104" '
+             f'role="img" aria-label="{Markup.escape(label)}" xmlns="http://www.w3.org/2000/svg">']
+    if test_run:
+        parts.append(f'<defs><pattern id="hatch{uid}" width="8" height="8" patternUnits="userSpaceOnUse" '
+                     f'patternTransform="rotate(45)"><rect width="8" height="8" fill="none"/>'
+                     f'<line x1="0" y1="0" x2="0" y2="8" stroke="#ffffff" stroke-width="3"/></pattern></defs>')
+    for i in range(1, LEVELS + 1):
+        d = _segment(i, cx, cy, outer, inner, 3)
+        fill = SHADES[i - 1] if level is not None else EMPTY
+        mark = f' stroke="{NEEDLE}" stroke-width="3"' if i == level else ""  # the run's level is outlined too
+        parts.append(f'<path class="seg seg-{i}{" current" if i == level else ""}" d="{d}" fill="{fill}"{mark}/>')
+        if test_run:
+            parts.append(f'<path d="{d}" fill="url(#hatch{uid})"/>')
+    if level is not None:
+        if not 1 <= level <= LEVELS:
+            raise ValueError(f"evidence level {level} is outside 1 to {LEVELS}")
+        angle = 180 - (level - 0.5) * 180 / LEVELS
+        x, y = _point(cx, cy, inner - 6, angle)  # ends inside the ring, so it shows on any shade
+        parts.append(f'<line class="needle" x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{NEEDLE}" '
+                     f'stroke-width="5" stroke-linecap="round"/>')
+        parts.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{NEEDLE}"/>')
+    parts.append("</svg>")
+    return Markup("".join(parts))
diff --git a/docs/glossary.json b/hypocurate/web/glossary.json
similarity index 90%
rename from docs/glossary.json
rename to hypocurate/web/glossary.json
index 713af7d..9c6cfc7 100644
--- a/docs/glossary.json
+++ b/hypocurate/web/glossary.json
@@ -39,5 +39,7 @@
 {"key":"datasources","screen":"Data sources","term":"Data sources","text":"The sources the system can search, with their licence and kind of data."},
 {"key":"adapter","screen":"Data sources","term":"Adapter","text":"The piece of code that reads a source and converts its records to the common format. A source can be switched on only when its adapter is ready and the connection test passes."},
 {"key":"testconn","screen":"Data sources","term":"Test connection","text":"Reads a few records from the source and shows them in the common format, so that you can check the adapter before switching the source on."},
-{"key":"spending","screen":"All screens","term":"Spending","text":"The caps in force, and the cost and tokens used this month."}
+{"key":"spending","screen":"All screens","term":"Spending","text":"The caps in force, and the cost and tokens used this month."},
+{"key":"evidence_level","screen":"Run viewer; Runs","term":"Evidence level","text":"How far the data in the sources searched could take the question, from 1 to 6, set by code from the result: 6 a tested answer with a verdict; 5 an exploratory answer, with a minimum missed; 4 a coefficient only, without a valid uncertainty; 3 data found but below the minimums; 2 no coefficient could be fitted; 1 nothing tested. It describes the evidence, not whether the claim is true, and it never changes the verdict, which is shown beside the dial. A hatched dial marks a test run on constructed data."},
+{"key":"confirmation","screen":"Run viewer","term":"Confirm the question as tested","text":"When the plan comes from a language model's reading of the claim, the run waits before the rules lock until a named person checks what will be tested: the scope, the outcome, the exclusion rules and the minimums. The confirmation records the name, the time and exactly the text shown; if anything changed since the page was opened, it is refused and the page must be opened again. Confirming shows that a person saw the reading, not that it is right."}
 ]
diff --git a/hypocurate/web/glossary.py b/hypocurate/web/glossary.py
new file mode 100644
index 0000000..98c0939
--- /dev/null
+++ b/hypocurate/web/glossary.py
@@ -0,0 +1,51 @@
+"""The explanation texts (PRD 9.7): one file, `hypocurate/web/glossary.json`, keyed by identifier. The information
+buttons and the Help page read it; no explanation text is written in a template (step 10a moved the file from
+`docs/glossary.json`, because the deployed image holds no `docs/`).
+
+Each entry: `key` (unique), `term`, `screen` (where it appears) and `text` (two or three plain sentences).
+"""
+from __future__ import annotations
+
+import json
+from functools import lru_cache
+from pathlib import Path
+from types import MappingProxyType
+from typing import Mapping
+
+PATH = Path(__file__).resolve().parent / "glossary.json"
+FIELDS = ("key", "screen", "term", "text")
+
+
+class GlossaryError(ValueError):
+    pass
+
+
+def validate(entries: list) -> None:
+    if not isinstance(entries, list) or not entries:
+        raise GlossaryError("the glossary is a non-empty list")
+    seen = set()
+    for e in entries:
+        if not isinstance(e, dict) or set(e) != set(FIELDS) or not all(isinstance(e[f], str) and e[f].strip()
+                                                                       for f in FIELDS):
+            raise GlossaryError(f"an entry must have exactly {', '.join(FIELDS)}, each a non-empty text")
+        if e["key"] in seen:
+            raise GlossaryError(f"duplicate key {e['key']}")
+        seen.add(e["key"])
+
+
+@lru_cache(maxsize=1)
+def entries() -> tuple[Mapping[str, str], ...]:
+    data = json.loads(PATH.read_text(encoding="utf-8"))
+    validate(data)
+    return tuple(MappingProxyType(dict(e)) for e in data)
+
+
+def by_key() -> Mapping[str, Mapping[str, str]]:
+    return MappingProxyType({e["key"]: e for e in entries()})
+
+
+def entry(key: str) -> Mapping[str, str]:
+    found = by_key().get(key)
+    if found is None:
+        raise KeyError(f"no glossary entry {key!r}")
+    return found
diff --git a/hypocurate/web/security.py b/hypocurate/web/security.py
new file mode 100644
index 0000000..55ad654
--- /dev/null
+++ b/hypocurate/web/security.py
@@ -0,0 +1,62 @@
+"""The signed-in person's name and the protection of actions that write (step 10a; owner's answer 1 and additions 1
+and 3 of 2026-10-11; register 'signed_in_name', 'csrf_tokens').
+
+**The name.** The sign-in form takes the shared password and the person's name (1 to `NAME_MAX` characters). The name
+is kept in the signed session cookie for the session's life and is the `by` of every action that names a person
+(confirm, cancel; dispatch and domain confirmation in 10b). It cannot change within a session: signing in again while
+signed in is refused, so a new name means signing out and in again. Nothing proves who typed the name; it records who
+said they acted, under the shared password, as `--by` does on the command line.
+
+**The CSRF token.** A random token (`secrets.token_urlsafe`) is made at sign-in and kept in the same signed cookie.
+Every form that writes carries it in a hidden field, and every write checks it (`check_csrf`, constant-time compare)
+before anything is done; a request without the session's token is refused with 403 and writes nothing. Sign-out writes
+nothing and carries no token. The cookie is SameSite=Lax as well (app.py).
+"""
+from __future__ import annotations
+
+import hmac
+import secrets
+
+from fastapi import HTTPException, Request
+
+from hypocurate.db.models import CONFIRMED_BY_MAX
+
+NAME_MAX = CONFIRMED_BY_MAX  # the confirmation's own limit (migration 0007), so every recorded name fits
+CSRF_FIELD = "csrf_token"
+CSRF_REFUSED = "This form has expired or did not come from this site. Reload the page and try again."
+
+
+class NameRefused(ValueError):
+    pass
+
+
+def clean_name(value: str | None) -> str:
+    name = " ".join((value or "").split())
+    if not 1 <= len(name) <= NAME_MAX:
+        raise NameRefused(f"Give your name (1 to {NAME_MAX} characters).")
+    return name
+
+
+def start_session(request: Request, name: str) -> None:
+    request.session.clear()
+    request.session.update({"signed_in": True, "name": name, "csrf": secrets.token_urlsafe(32)})
+
+
+def signed_in_name(request: Request) -> str:
+    """The name given at sign-in. A session without one (signed in before step 10a) cannot act; it must sign in
+    again."""
+    name = request.session.get("name")
+    if not isinstance(name, str) or not name:
+        raise HTTPException(status_code=403, detail="Sign out and sign in again with your name.")
+    return name
+
+
+def csrf_token(request: Request) -> str:
+    return request.session.get("csrf") or ""
+
+
+def check_csrf(request: Request, token: str | None) -> None:
+    expected = request.session.get("csrf")
+    if not isinstance(expected, str) or not expected or not isinstance(token, str) \
+            or not hmac.compare_digest(expected.encode(), token.encode()):
+        raise HTTPException(status_code=403, detail=CSRF_REFUSED)
diff --git a/hypocurate/web/static/info.js b/hypocurate/web/static/info.js
new file mode 100644
index 0000000..9fee923
--- /dev/null
+++ b/hypocurate/web/static/info.js
@@ -0,0 +1,49 @@
+// Information buttons (PRD 9.7): open on hover, keyboard focus, click or tap; close on Escape or when focus leaves.
+// The text comes from the glossary file, inserted by the server; this script only shows and hides it. Events are
+// handled on the document, so buttons in a part of the page replaced by poll.js work too.
+(function () {
+  var pinned = null;
+
+  function set(box, open) {
+    var b = box.querySelector(".info-button"), t = box.querySelector(".info-text");
+    if (!b || !t) return;
+    t.hidden = !open;
+    b.setAttribute("aria-expanded", open ? "true" : "false");
+    if (open) {  // open towards the side with room, so the text stays on the screen
+      box.classList.remove("flip");
+      if (t.getBoundingClientRect().right > document.documentElement.clientWidth - 8) box.classList.add("flip");
+    }
+  }
+
+  function boxOf(node) { return node && node.closest ? node.closest(".info") : null; }
+
+  document.addEventListener("mouseover", function (ev) {
+    var box = boxOf(ev.target);
+    if (box) set(box, true);
+  });
+  document.addEventListener("mouseout", function (ev) {
+    var box = boxOf(ev.target);
+    if (box && box !== pinned && !box.contains(ev.relatedTarget)) set(box, false);
+  });
+  document.addEventListener("focusin", function (ev) {
+    var box = boxOf(ev.target);
+    if (box) set(box, true);
+  });
+  document.addEventListener("focusout", function (ev) {
+    var box = boxOf(ev.target);
+    if (box && !box.contains(ev.relatedTarget)) { if (pinned === box) pinned = null; set(box, false); }
+  });
+  document.addEventListener("click", function (ev) {
+    var b = ev.target.closest ? ev.target.closest(".info-button") : null;
+    if (!b) return;
+    ev.preventDefault();
+    var box = boxOf(b);
+    pinned = pinned === box ? null : box;
+    set(box, pinned === box);
+  });
+  document.addEventListener("keydown", function (ev) {
+    if (ev.key !== "Escape") return;
+    var box = boxOf(ev.target);
+    if (box) { if (pinned === box) pinned = null; set(box, false); }
+  });
+})();
diff --git a/hypocurate/web/static/poll.js b/hypocurate/web/static/poll.js
new file mode 100644
index 0000000..54f4327
--- /dev/null
+++ b/hypocurate/web/static/poll.js
@@ -0,0 +1,38 @@
+// Live state of an open run (step 10a; owner, 2026-10-11: a small script of our own, not HTMX).
+// The server decides when polling ends: a state fragment of an open run (queued, waiting or running) carries
+// data-poll with its own address; one of an ended run (completed or failed) carries data-ended="true" and no address.
+// This script asks again only when the fragment it just received carries data-poll; on data-ended it reloads the
+// page once to show the results and schedules nothing more. A page without data-poll never polls.
+(function () {
+  var INTERVAL_MS = 5000;
+
+  function schedule(url) {
+    window.setTimeout(function () { tick(url); }, INTERVAL_MS);
+  }
+
+  function tick(url) {
+    fetch(url, { credentials: "same-origin", cache: "no-store", headers: { "Accept": "text/html" } })
+      .then(function (response) {
+        if (!response.ok) { throw new Error("state " + response.status); }
+        return response.text();
+      })
+      .then(function (html) {
+        var holder = document.createElement("div");
+        holder.innerHTML = html;
+        var next = holder.querySelector("#run-state");
+        var current = document.getElementById("run-state");
+        if (!next || !current) { return; }  // not a state (for example the sign-in page): stop
+        if (next.getAttribute("data-ended") === "true") { window.location.reload(); return; }  // ended: stop
+        current.replaceWith(next);
+        var again = next.getAttribute("data-poll");
+        if (again) { schedule(again); }
+      })
+      .catch(function () { schedule(url); });  // the network or the service is down for a moment: ask again
+  }
+
+  document.addEventListener("DOMContentLoaded", function () {
+    var state = document.getElementById("run-state");
+    var url = state && state.getAttribute("data-poll");
+    if (url) { schedule(url); }
+  });
+})();
diff --git a/hypocurate/web/static/style.css b/hypocurate/web/static/style.css
index 7002065..cc9d28f 100644
--- a/hypocurate/web/static/style.css
+++ b/hypocurate/web/static/style.css
@@ -1,32 +1,114 @@
-:root { --fg: #1d2330; --muted: #5b6475; --bg: #ffffff; --line: #d8dde6; --accent: #2457c5; --bad: #b3261e; --good: #1f7a3a; }
+/* HypoCurate screens (step 10a). Sizes in rem only (1rem = 16px); nothing below 0.75rem = 12px (owner's addition 6;
+   tests/test_web_pages.py checks every font-size here). */
+:root { --fg: #1d2330; --muted: #5b6475; --bg: #ffffff; --panel: #f6f7f9; --line: #d8dde6; --accent: #2457c5;
+        --bad: #b3261e; --good: #1f7a3a; --menu: #17233b; --menu-fg: #e8ecf4; --model: #eef3fb; }
 * { box-sizing: border-box; }
-body { margin: 0; font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
+body { margin: 0; font: 1rem/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
 header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--line); }
 .brand { font-weight: 600; }
 main { max-width: 32rem; margin: 2rem auto; padding: 0 16px; }
+main.wide { max-width: 72rem; }
 label { display: block; margin-bottom: 4px; }
 input { width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 4px; font: inherit; }
-button { margin-top: 12px; padding: 8px 16px; border: 0; border-radius: 4px; background: var(--accent); color: #fff; font: inherit; cursor: pointer; }
-.logout button { margin: 0; }
+button, .button { display: inline-block; margin-top: 12px; padding: 8px 16px; border: 0; border-radius: 4px; background: var(--accent); color: #fff; font: inherit; cursor: pointer; text-decoration: none; }
+button.secondary, .button.secondary { background: #e7ebf2; color: var(--fg); }
+button.link { background: none; color: var(--menu-fg); padding: 0; margin: 0; text-decoration: underline; }
 .error { color: var(--bad); }
 .ok { color: var(--good); }
+.notice { background: #eaf4ec; border-left: 4px solid var(--good); padding: 8px 12px; }
 th { text-align: left; padding-right: 16px; color: var(--muted); font-weight: 500; }
-/* Assumptions register (step 4b): plain table; full styling comes with the step 10 screens. */
-main.wide { max-width: 72rem; }
-.nav { display: flex; align-items: center; gap: 16px; }
 .muted { color: var(--muted); }
+.small { font-size: 0.875rem; }
 a { color: var(--accent); }
-code { font-size: 0.9em; overflow-wrap: anywhere; }
+code, .mono { font-family: ui-monospace, monospace; font-size: 0.875rem; overflow-wrap: anywhere; }
+h1 { font-size: 1.5rem; line-height: 1.3; margin: 0.25rem 0 0.5rem; }
+h2 { font-size: 1.125rem; margin: 0 0 0.5rem; }
+h3 { font-size: 1rem; margin: 0 0 0.25rem; }
+section { margin: 1.25rem 0; padding: 1rem 1.25rem; border: 1px solid var(--line); border-radius: 6px; }
+.crumbs { color: var(--muted); margin: 0; }
+.nav { display: flex; align-items: center; gap: 16px; }
+
+/* The left menu (signed-in pages). */
+body.app { display: grid; grid-template-columns: 15rem 1fr; min-height: 100vh; }
+body.app main { margin: 1.5rem auto; width: 100%; }
+.menu { background: var(--menu); color: var(--menu-fg); padding: 1rem; }
+.menu .brand { font-size: 1.25rem; margin-bottom: 1rem; }
+.menu ul { list-style: none; margin: 0 0 1.5rem; padding: 0; }
+.menu li a { display: block; color: var(--menu-fg); text-decoration: none; padding: 6px 10px; border-radius: 4px; }
+.menu li a[aria-current="page"] { background: #fff; color: var(--menu); font-weight: 600; }
+.menu .spending { border: 0; padding: 0; margin: 0 0 1.5rem; }
+.menu .spending h2 { font-size: 1rem; }
+.menu dl { margin: 0; font-size: 0.875rem; } .menu dt { color: #b7c1d6; } .menu dd { margin: 0 0 6px; }
+.menu .who { font-size: 0.875rem; }
+.menu .info-button { background: #334468; }
+@media (max-width: 48rem) { body.app { display: block; } .menu { padding: 12px 16px; } .menu ul { display: flex; gap: 8px; margin-bottom: 8px; } .menu .spending { display: none; } }
+
+/* Information buttons (PRD 9.7). */
+.info { position: relative; display: inline-block; vertical-align: middle; }
+.info-button { margin: 0 0 0 4px; width: 1.25rem; height: 1.25rem; padding: 0; border-radius: 50%; font-size: 0.75rem; font-weight: 700; line-height: 1.25rem; background: #5b6b8c; }
+.info-text { position: absolute; z-index: 10; left: 0; top: 1.6rem; width: 20rem; max-width: 80vw; padding: 10px 12px; background: #fff; color: var(--fg); border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,.15); font-size: 0.875rem; font-weight: 400; line-height: 1.45; text-align: left; }
+
+/* Run viewer. */
+.badge { display: inline-block; margin-left: 6px; padding: 0 8px; border-radius: 4px; font-size: 0.875rem; }
+.badge.test-run { background: #fff4e5; color: #8a4b00; border: 1px dashed #8a4b00; margin-left: 0; }
+.badge.exploratory { background: #fff4e5; color: #8a4b00; margin-left: 0; }
+.badge.unreviewed { background: #fdecea; color: var(--bad); }
+.badge.open-badge { background: #fff4e5; color: #8a4b00; }
+.outcome { background: #fbf4ea; }
+.outcome-row { display: flex; flex-wrap: wrap; gap: 24px; align-items: center; }
+.verdict .outcome-words { font-size: 1.25rem; font-weight: 600; }
+.verdict .verdict-words { font-size: 1.125rem; }
+.dial-box { display: flex; flex-direction: column; align-items: center; gap: 4px; }
+.dial-box.small { flex-direction: row; gap: 8px; }
+.dial-level { font-weight: 600; font-size: 1rem; }
+.dial-box.small .dial-level { font-size: 0.75rem; font-weight: 500; max-width: 9rem; }
+.dial-box.small .badge { font-size: 0.75rem; }
+.statement p, .confirm-text .crow { margin: 0 0 6px; }
+.indent { padding-left: 1.5rem; }
+.analyst { background: var(--model); }
+.analyst .label { font-size: 0.875rem; color: var(--muted); font-style: italic; }
+table.data { width: 100%; border-collapse: collapse; }
+table.data th, table.data td { text-align: left; vertical-align: top; padding: 6px 10px 6px 0; border-bottom: 1px solid var(--line); }
+table.data tr.pooled td { font-weight: 600; }
+table.data td .muted { font-size: 0.875rem; }
+.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
+.card { border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px; }
+.card p { margin: 0 0 4px; }
+.facts { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; margin: 8px 0; }
+.facts dt { color: var(--muted); } .facts dd { margin: 0; }
+.state-line { font-size: 1.125rem; margin: 0 0 4px; }
+.actions { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
+.actions form { margin: 0; }
+.confirm-text { background: var(--panel); }
+.chead { font-weight: 600; }
+.confirm-form, .cancel-form { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
+@media (max-width: 48rem) {
+  .cards { grid-template-columns: 1fr; }
+  /* Tables become stacked cards on a phone: one row per card, each cell under its column's name. */
+  table.data, table.data tbody, table.data tr, table.data td { display: block; width: 100%; }
+  table.data thead { display: none; }
+  table.data tr { border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; margin-bottom: 10px; }
+  table.data td { border: 0; padding: 2px 0; }
+  table.data td[data-label]::before { content: attr(data-label) ": "; color: var(--muted); font-weight: 600; }
+  table.runs td:nth-child(2) { white-space: normal; }
+  body.app main { margin: 1rem auto; }
+}
+
+/* Assumptions register (step 4b). */
 .register { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
 .register th, .register td { text-align: left; vertical-align: top; padding: 8px 12px 8px 0; }
 .register thead th { border-bottom: 2px solid var(--line); }
 .register tbody { border-bottom: 1px solid var(--line); }
 .register tr.more td { padding-top: 0; }
 .register .unreviewed-scientific td:first-child { border-left: 4px solid var(--bad); padding-left: 8px; }
-.badge { display: inline-block; margin-left: 6px; padding: 0 6px; border-radius: 4px; font-size: 0.85em; }
-.badge.unreviewed { background: #fdecea; color: var(--bad); }
-.badge.open-badge { background: #fff4e5; color: #8a4b00; }
 details summary { cursor: pointer; color: var(--muted); }
 dl { margin: 8px 0; } dt { font-weight: 600; margin-top: 6px; } dd { margin-left: 0; }
 dd ul { margin: 0; padding-left: 1.2em; }
 @media (max-width: 48rem) { .register thead { display: none; } .register td { display: block; padding-right: 0; } }
+.statement-row { display: grid; grid-template-columns: 1fr 15rem; gap: 20px; align-items: start; }
+.statement aside.outcome { border: 1px solid #f0d5b0; border-radius: 6px; padding: 12px; text-align: center; }
+.statement aside .outcome-words { font-size: 1rem; font-weight: 600; margin-top: 8px; }
+.statement aside .verdict-words { font-size: 1rem; }
+@media (max-width: 60rem) { .statement-row { grid-template-columns: 1fr; } }
+.info.flip .info-text { left: auto; right: 0; }
+table.runs td:nth-child(2) { white-space: nowrap; }
diff --git a/hypocurate/web/templates/_dial.html b/hypocurate/web/templates/_dial.html
new file mode 100644
index 0000000..47aaf76
--- /dev/null
+++ b/hypocurate/web/templates/_dial.html
@@ -0,0 +1,8 @@
+{# The evidence dial with its words beside it (owner's brief). `e` is run_view.evidence(...). #}
+<div class="dial-box{% if small %} small{% endif %}">
+  {{ dial(e.level, e.test_run, "small" if small else "large", e.words) }}
+  <div class="dial-words">
+    <div class="dial-level">{{ e.words }}</div>
+    {% if e.test_run %}<span class="badge test-run">test run</span>{% endif %}
+  </div>
+</div>
diff --git a/hypocurate/web/templates/_state.html b/hypocurate/web/templates/_state.html
new file mode 100644
index 0000000..def2101
--- /dev/null
+++ b/hypocurate/web/templates/_state.html
@@ -0,0 +1,29 @@
+{# The run's state; replaced while the run is open (step 10a, a3). #}
+<section class="state state-{{ r.status }}" id="run-state" aria-live="polite"
+  {%- if r.open %} data-poll="/runs/{{ r.run }}/state"{% else %} data-ended="true"{% endif %}>
+  <h2>Status {{ info("status") }}</h2>
+  <p class="state-line"><strong>{{ r.status_words }}</strong>{% if r.stage_words and r.status == "running" %}: {{ r.stage_words }}{% endif %}</p>
+  {% if r.status == "waiting" %}
+    {% if r.confirmed %}<p>Confirmed; waiting for a worker to take it up.</p>
+    {% else %}<p>Waits for {{ r.waiting_for }}.</p>{% endif %}
+  {% endif %}
+  {% if r.failure %}<p class="error">Failed: {{ r.failure }}</p>{% endif %}
+  {% if r.claim_facts %}
+  <dl class="facts">
+    <dt>Worker</dt><dd>{{ r.claim_facts.worker or "none holds it" }}{% if r.claim_facts.claimed %} (since {{ r.claim_facts.claimed }}){% endif %}</dd>
+    <dt>Heartbeat</dt><dd>{{ r.claim_facts.heartbeat_age + " ago" if r.claim_facts.heartbeat_age else "none" }}</dd>
+    <dt>Last write</dt><dd>{{ r.claim_facts.since_last_write }} ago</dd>
+    <dt>Claims; recoveries</dt><dd>{{ r.claim_facts.claims }}; {{ r.claim_facts.recoveries }}</dd>
+  </dl>
+  {% endif %}
+  {% if r.can_confirm or r.can_cancel %}
+  <div class="actions">
+    {% if r.can_confirm %}<a class="button" href="/runs/{{ r.run }}/confirm">Review and confirm the question as tested</a>{% endif %}
+    {% if r.can_cancel %}
+    <form method="post" action="/runs/{{ r.run }}/cancel">
+      <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+      <button type="submit" class="secondary">Cancel this run</button>
+    </form>{% endif %}
+  </div>
+  {% endif %}
+</section>
diff --git a/hypocurate/web/templates/assumptions.html b/hypocurate/web/templates/assumptions.html
index 2cc8142..693f3d3 100644
--- a/hypocurate/web/templates/assumptions.html
+++ b/hypocurate/web/templates/assumptions.html
@@ -1,7 +1,7 @@
 {% extends "base.html" %}
 {% block title %}Assumptions · HypoCurate{% endblock %}
 {% block main_attrs %} class="wide"{% endblock %}
-{% block nav %}<nav class="nav"><a href="/">Home</a><form method="post" action="/logout" class="logout"><button type="submit">Sign out</button></form></nav>{% endblock %}
+{% set active = "assumptions" %}
 {% block content %}
 
 <h1>Assumptions</h1>
diff --git a/hypocurate/web/templates/base.html b/hypocurate/web/templates/base.html
index a83a0a1..a4aba67 100644
--- a/hypocurate/web/templates/base.html
+++ b/hypocurate/web/templates/base.html
@@ -5,9 +5,35 @@
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <title>{% block title %}HypoCurate{% endblock %}</title>
   <link rel="stylesheet" href="/static/style.css">
+  <script src="/static/info.js" defer></script>
+  <script src="/static/poll.js" defer></script>
 </head>
-<body>
-  <header><span class="brand">HypoCurate</span>{% block nav %}{% endblock %}</header>
+<body{% if signed_in_as is defined %} class="app"{% endif %}>
+{% if signed_in_as is defined %}
+  <nav class="menu" aria-label="Main">
+    <div class="brand">HypoCurate</div>
+    <ul>
+      <li><a href="/"{% if active == "home" %} aria-current="page"{% endif %}>Home</a></li>
+      <li><a href="/runs"{% if active == "runs" %} aria-current="page"{% endif %}>Runs</a></li>
+      <li><a href="/assumptions"{% if active == "assumptions" %} aria-current="page"{% endif %}>Assumptions</a></li>
+    </ul>
+    {% if spending %}
+    <section class="spending" aria-label="Spending">
+      <h2>Spending {{ info("spending") }}</h2>
+      <dl>
+        <dt>Per-run cap</dt><dd>{{ spending.per_run_cap }}</dd>
+        <dt>Monthly cap</dt><dd>{{ spending.monthly_cap }}</dd>
+        <dt>Counted this month</dt><dd>{{ spending.month_counted }}</dd>
+        <dt>Tokens this month</dt><dd>{{ spending.month_tokens }}</dd>
+      </dl>
+    </section>
+    {% endif %}
+    <div class="who">Signed in: <strong>{{ signed_in_as or "no name (sign in again)" }}</strong>
+      <form method="post" action="/logout" class="logout"><button type="submit" class="link">Sign out</button></form></div>
+  </nav>
+{% else %}
+  <header><span class="brand">HypoCurate</span></header>
+{% endif %}
   <main{% block main_attrs %}{% endblock %}>{% block content %}{% endblock %}</main>
 </body>
 </html>
diff --git a/hypocurate/web/templates/confirm.html b/hypocurate/web/templates/confirm.html
new file mode 100644
index 0000000..81ce897
--- /dev/null
+++ b/hypocurate/web/templates/confirm.html
@@ -0,0 +1,34 @@
+{% extends "base.html" %}
+{% set active = "runs" %}
+{% block title %}Confirm run {{ r.run }} · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<p class="crumbs"><a href="/runs">Runs</a> › <a href="/runs/{{ r.run }}">{{ r.query }} · run {{ r.run }}</a> › confirmation</p>
+<h1>Confirm the question as tested {{ info("confirmation") }}</h1>
+{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+{% if r.content is none %}
+  <p>Run {{ r.run }} is not waiting for a confirmation ({{ r.status_words }}{% if r.confirmed %}; already confirmed{% endif %}).</p>
+  <p><a href="/runs/{{ r.run }}">Back to the run</a></p>
+{% else %}
+<section class="confirm-what">
+  <p>The run waits at the rules lock. Nothing is locked until a named person confirms what will be tested. Read it all; your confirmation records your name, the time, and exactly this text.</p>
+</section>
+<section class="confirm-text" aria-label="What you confirm">
+  {% for row in r.rows %}
+    <div class="crow{% if row.indent %} indent{% endif %}">{% if row.head %}<span class="chead">{{ row.head }}:</span> {% endif %}{{ row.value }}</div>
+  {% endfor %}
+</section>
+<form method="post" action="/runs/{{ r.run }}/confirm" class="confirm-form">
+  <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+  <input type="hidden" name="content_fingerprint" value="{{ r.content_fingerprint }}">
+  <p>Confirming as <strong>{{ signed_in_as }}</strong>. Once you confirm, the question as tested is labelled: {{ r.label_after }}.</p>
+  <button type="submit">Confirm the question as tested</button>
+  <a class="button secondary" href="/runs/{{ r.run }}">Back without confirming</a>
+</form>
+<form method="post" action="/runs/{{ r.run }}/cancel" class="cancel-form">
+  <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+  <button type="submit" class="secondary">Cancel this run instead</button>
+</form>
+<p class="muted small">Content fingerprint {{ r.content_fingerprint }}</p>
+{% endif %}
+{% endblock %}
diff --git a/hypocurate/web/templates/home.html b/hypocurate/web/templates/home.html
index 8bde491..64f903d 100644
--- a/hypocurate/web/templates/home.html
+++ b/hypocurate/web/templates/home.html
@@ -1,7 +1,7 @@
 {% extends "base.html" %}
-{% block nav %}<form method="post" action="/logout" class="logout"><button type="submit">Sign out</button></form>{% endblock %}
+{% set active = "home" %}
 {% block content %}
 <h1>Signed in</h1>
-<p>The skeleton is running. The screens arrive in build step 10.</p>
-<p><a href="/assumptions">Assumptions</a> · <a href="/health">Health</a></p>
+<p>Step 10a: the run pages. <a href="/runs">Runs</a> lists every dispatched run; a run waiting at the rules lock is confirmed or cancelled from its page.</p>
+<p><a href="/runs">Runs</a> · <a href="/assumptions">Assumptions</a> · <a href="/health">Health</a></p>
 {% endblock %}
diff --git a/hypocurate/web/templates/login.html b/hypocurate/web/templates/login.html
index 00ce29b..e7f5198 100644
--- a/hypocurate/web/templates/login.html
+++ b/hypocurate/web/templates/login.html
@@ -3,9 +3,17 @@
 {% block content %}
 <h1>Sign in</h1>
 {% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+{% if current_name %}
+<p>You are signed in as <strong>{{ current_name }}</strong>. <a href="/">Continue</a>, or sign out to sign in under another name.</p>
+<form method="post" action="/logout"><button type="submit">Sign out</button></form>
+{% else %}
 <form method="post" action="/login">
+  <label for="name">Your name</label>
+  <input id="name" name="name" type="text" autocomplete="name" maxlength="{{ name_max }}" required autofocus>
+  <p class="muted small">Recorded with what you confirm or cancel. It stays the same until you sign out.</p>
   <label for="password">Password</label>
-  <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
+  <input id="password" name="password" type="password" autocomplete="current-password" required>
   <button type="submit">Sign in</button>
 </form>
+{% endif %}
 {% endblock %}
diff --git a/hypocurate/web/templates/run.html b/hypocurate/web/templates/run.html
new file mode 100644
index 0000000..e1ba39a
--- /dev/null
+++ b/hypocurate/web/templates/run.html
@@ -0,0 +1,113 @@
+{% extends "base.html" %}
+{% set active = "runs" %}
+{% block title %}Run {{ r.run }} · {{ r.query }} · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<p class="crumbs"><a href="/runs">Runs</a> › {{ r.query }} · version {{ r.version }} · run {{ r.run }} {{ info("version") }} · <strong>{{ r.status_words }}</strong></p>
+<h1>{{ r.claim }}</h1>
+<p class="muted">Domain: {{ r.domain }}{% for t in r.tags %} · {{ t }}{% endfor %} · plan: {{ r.plan_kind }} · agent mode: {{ r.agent_mode }} · dispatched {{ r.queued }}{% if r.ended %} · ended {{ r.ended }}{% endif %}</p>
+{% if r.test_run_badge %}<p class="badge test-run">{{ r.test_run_badge }}</p>{% endif %}
+{% if message %}<p class="notice" role="status">{{ message }}</p>{% endif %}
+{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+
+{% if r.status != "completed" %}{% include "_state.html" %}{% endif %}
+
+{% if r.status == "completed" %}
+<section class="statement">
+  <div class="statement-row">
+    <div class="statement-text">
+      <h2>Results statement (written by code) {{ info("sig") }}</h2>
+      {% for line in r.statement.body %}<p class="{{ 'indent' if line.startswith('  ') else '' }}">{{ line|units }}</p>{% endfor %}
+    </div>
+    <aside class="outcome" aria-label="Evidence level and verdict">
+      <h3>Evidence level {{ info("evidence_level") }}</h3>
+      {% with e = r.evidence, small = false %}{% include "_dial.html" %}{% endwith %}
+      <div class="verdict">
+        <div class="outcome-words">{{ r.outcome }} {{ info("outcome") }}</div>
+        <div class="verdict-words">{% if r.verdict %}Verdict: {{ r.verdict }}{% else %}No verdict{% endif %}</div>
+        {% if r.exploratory %}<div class="badge exploratory">exploratory {{ info("exploratory") }}</div>{% endif %}
+      </div>
+    </aside>
+  </div>
+</section>
+{% elif r.question_as_tested %}
+<section>
+  <h2>Question as tested</h2>
+  <p>{{ r.question_as_tested.text }}</p>
+  <p class="muted">{{ r.question_as_tested.label }}</p>
+</section>
+{% endif %}
+
+{% if r.status == "completed" %}
+<section class="analyst">
+  <h2>Explanation by the Analyst</h2>
+  {% if r.analyst and r.analyst.text %}
+    <p class="label">{{ r.analyst.label }}</p>
+    <div class="model-text">{{ r.analyst.text|model_text }}</div>
+  {% elif r.analyst %}
+    <p class="muted">{{ r.analyst.unavailable }}</p>
+  {% endif %}
+</section>
+
+{% if r.per_source %}
+<section>
+  <h2>Each source alone, and all together {{ info("persource") }}</h2>
+  <table class="data">
+    <thead><tr><th>Source</th><th>Kind of data {{ info("kinds") }}</th><th>Records</th><th>Alloys</th><th>Groups</th><th>Result</th><th>Against the pooled result</th></tr></thead>
+    <tbody>{% for x in r.per_source %}
+      <tr{% if loop.first %} class="pooled"{% endif %}><td data-label="Source">{{ x.name }}</td><td data-label="Kind of data">{{ x.kind }}</td><td data-label="Records">{{ x.records }}</td><td data-label="Alloys">{{ x.alloys }}</td><td data-label="Groups">{{ x.groups }}</td><td data-label="Result">{{ x.result|units }}</td><td data-label="Against the pooled result">{{ x.against }}</td></tr>
+    {% endfor %}</tbody>
+  </table>
+  {% if r.p_value_description %}<p class="muted">Each ± is one standard error (cluster-robust, by group), not a confidence interval. Each p-value is an {{ r.p_value_description }}.</p>{% endif %}
+</section>
+{% endif %}
+
+{% if r.sensitivity %}
+<section>
+  <h2>Sensitivity sets {{ info("sig_sens") }}</h2>
+  <p class="muted">Shown beside the verdict; they never change it.</p>
+  <table class="data">
+    <thead><tr><th>Set</th><th>Records</th><th>Alloys</th><th>Groups</th><th>Result</th><th>Against the pooled result</th></tr></thead>
+    <tbody>{% for x in r.sensitivity %}
+      <tr><td data-label="Set">{{ x.name }}<div class="muted">{{ x.change }}</div></td><td data-label="Records">{{ x.records }}</td><td data-label="Alloys">{{ x.alloys }}</td><td data-label="Groups">{{ x.groups }}</td><td data-label="Result">{{ x.result|units }}</td><td data-label="Against the pooled result">{{ x.against }}</td></tr>
+    {% endfor %}</tbody>
+  </table>
+</section>
+{% endif %}
+
+<section>
+  <h2>Cautions</h2>
+  {% for line in r.statement.cautions %}<p class="{{ 'indent' if line.startswith('  ') else '' }}">{{ line|units }}</p>{% endfor %}
+</section>
+{% endif %}
+
+<section>
+  <h2>Checkpoints</h2>
+  <div class="cards">
+    <div class="card"><h3>Checkpoint 1: rules lock {{ info("lock") }}</h3>
+      {% if r.checkpoints.rules_lock.at %}<p>{{ r.checkpoints.rules_lock.at }}</p><p class="mono">{{ r.checkpoints.rules_lock.fingerprint }}</p>{% else %}<p class="muted">Not reached.</p>{% endif %}</div>
+    <div class="card"><h3>Checkpoint 2: dataset freeze {{ info("freeze") }}</h3>
+      {% if r.checkpoints.dataset_freeze.at %}<p>{{ r.checkpoints.dataset_freeze.at }} · {{ r.checkpoints.dataset_freeze.records }} records</p><p class="mono">{{ r.checkpoints.dataset_freeze.fingerprint }}</p>{% else %}<p class="muted">Not reached.</p>{% endif %}</div>
+  </div>
+</section>
+
+{% if r.sources %}
+<section>
+  <h2>Sources {{ info("sources") }}</h2>
+  <ul>{% for s in r.sources %}<li>{{ s.name }}: {{ s.status }}{% if s.nothing_found %} ({{ s.nothing_found }}){% endif %}</li>{% endfor %}</ul>
+</section>
+{% endif %}
+
+<section>
+  <h2>Tokens and cost {{ info("cost") }}</h2>
+  <p>{{ r.cost.calls_words }} · {{ r.cost.input_tokens }} input and {{ r.cost.output_tokens }} output tokens · cost reported by the provider {{ r.cost.reported }} · counted toward the caps {{ r.cost.counted }}{% if r.cost.unconfirmed_calls %} ({{ r.cost.unconfirmed_calls }} calls without a reported cost, counted at their maximum){% endif %} · ceiling for this run {{ r.ceiling }}</p>
+  {% if r.stages %}
+  <table class="data">
+    <thead><tr><th>Stage {{ info("stages") }}</th><th>Attempt</th><th>Status</th><th>Model</th><th>Calls</th><th>Input tokens</th><th>Output tokens</th><th>Cost</th></tr></thead>
+    <tbody>{% for s in r.stages %}<tr><td data-label="Stage">{{ s.name }}</td><td data-label="Attempt">{{ s.attempt }}</td><td data-label="Status">{{ s.status }}</td><td data-label="Model">{{ s.model or "—" }}</td><td data-label="Calls">{{ s.calls }}</td><td data-label="Input tokens">{{ s.input_tokens }}</td><td data-label="Output tokens">{{ s.output_tokens }}</td><td data-label="Cost">{{ s.cost }}</td></tr>{% endfor %}</tbody>
+  </table>
+  {% endif %}
+</section>
+
+{% if r.statement.format %}<p class="muted">{% for line in r.statement.format %}{{ line }} {% endfor %}</p>{% endif %}
+{% endblock %}
diff --git a/hypocurate/web/templates/runs.html b/hypocurate/web/templates/runs.html
new file mode 100644
index 0000000..bff9b37
--- /dev/null
+++ b/hypocurate/web/templates/runs.html
@@ -0,0 +1,23 @@
+{% extends "base.html" %}
+{% set active = "runs" %}
+{% block title %}Runs · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Runs</h1>
+<p class="muted">Every dispatched run, newest first. {{ info("queue") }}</p>
+{% if not runs %}<p>No run yet.</p>{% else %}
+<table class="data runs">
+  <thead><tr><th>Evidence {{ info("evidence_level") }}</th><th>Run</th><th>Claim</th><th>Status {{ info("status") }}</th><th>Outcome {{ info("outcome") }}</th><th>Cost {{ info("cost") }}</th></tr></thead>
+  <tbody>{% for x in runs %}
+    <tr>
+      <td data-label="Evidence">{% with e = x.evidence, small = true %}{% include "_dial.html" %}{% endwith %}</td>
+      <td data-label="Run"><a href="/runs/{{ x.run }}">{{ x.query }} · run {{ x.run }}</a><div class="muted">{{ x.queued }}</div></td>
+      <td data-label="Claim">{{ x.claim }}</td>
+      <td data-label="Status">{{ x.status_words }}</td>
+      <td data-label="Outcome">{{ x.outcome or "—" }}</td>
+      <td data-label="Cost">{{ x.cost }}</td>
+    </tr>
+  {% endfor %}</tbody>
+</table>
+{% endif %}
+{% endblock %}
diff --git a/hypocurate/web/textfmt.py b/hypocurate/web/textfmt.py
new file mode 100644
index 0000000..3f8905c
--- /dev/null
+++ b/hypocurate/web/textfmt.py
@@ -0,0 +1,82 @@
+"""How text is shown on the screens (step 10a; owner's review of the screenshots, 2026-10-11).
+
+- `units`: escapes a code-written line and writes exponents as superscripts (MPa·µm^0.5 becomes MPa·µm<sup>0.5</sup>).
+  Screens only; the stored text, the command line and the workbook keep "^".
+- `model_text`: the Analyst's text (written by a language model) in a small safe subset of Markdown: paragraphs, bold
+  (`**…**`), bulleted and numbered lists, and simple tables (`| a | b |`, with the `|---|` line dropped). Everything
+  is escaped first, so the model's text can never add markup of its own; any other Markdown sign is left as text
+  except leading heading marks (`#`), which are dropped. Exponents are written as in `units`.
+"""
+from __future__ import annotations
+
+import re
+
+from markupsafe import Markup, escape
+
+_EXPONENT = re.compile(r"\^(-?\d+(?:\.\d+)?(?:/\d+)?)")
+_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
+_BULLET = re.compile(r"^\s*[-*•]\s+(.*)$")
+_NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
+_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
+_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
+_HEADING = re.compile(r"^\s*#{1,6}\s+")
+
+
+def _inline(raw: str) -> str:
+    """One escaped line with bold and exponents: the only markup added, and only around escaped text."""
+    out = str(escape(raw))
+    out = _BOLD.sub(r"<strong>\1</strong>", out)
+    return _EXPONENT.sub(r"<sup>\1</sup>", out)
+
+
+def units(line: str) -> Markup:
+    return Markup(_EXPONENT.sub(r"<sup>\1</sup>", str(escape(line))))
+
+
+def _cells(row: str) -> list[str]:
+    return [c.strip() for c in row.strip().strip("|").split("|")]
+
+
+def _table(rows: list[str]) -> str:
+    body = [r for r in rows if not _TABLE_RULE.match(r)]
+    head, rest = (body[0], body[1:]) if len(body) > 1 and any(_TABLE_RULE.match(r) for r in rows) else (None, body)
+    parts = ['<table class="data model-table">']
+    if head is not None:
+        parts.append("<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in _cells(head)) + "</tr></thead>")
+    parts.append("<tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>"
+                                     for r in rest) + "</tbody></table>")
+    return "".join(parts)
+
+
+def model_text(text: str | None) -> Markup:
+    lines = (text or "").replace("\r\n", "\n").split("\n")
+    blocks: list[str] = []
+    i = 0
+    while i < len(lines):
+        line = lines[i]
+        if not line.strip():
+            i += 1
+            continue
+        if _TABLE_ROW.match(line):
+            rows = []
+            while i < len(lines) and (_TABLE_ROW.match(lines[i]) or _TABLE_RULE.match(lines[i])) and lines[i].strip():
+                rows.append(lines[i])
+                i += 1
+            blocks.append(_table(rows))
+            continue
+        for pattern, tag in ((_BULLET, "ul"), (_NUMBERED, "ol")):
+            if pattern.match(line):
+                items = []
+                while i < len(lines) and pattern.match(lines[i]):
+                    items.append(f"<li>{_inline(pattern.match(lines[i]).group(1))}</li>")
+                    i += 1
+                blocks.append(f"<{tag}>{''.join(items)}</{tag}>")
+                break
+        else:
+            para = []
+            while i < len(lines) and lines[i].strip() and not _TABLE_ROW.match(lines[i]) \
+                    and not _BULLET.match(lines[i]) and not _NUMBERED.match(lines[i]):
+                para.append(_inline(_HEADING.sub("", lines[i]).strip()))
+                i += 1
+            blocks.append("<p>" + " ".join(para) + "</p>")
+    return Markup("".join(blocks))
diff --git a/hypocurate/worker.py b/hypocurate/worker.py
index f804148..5e59876 100644
--- a/hypocurate/worker.py
+++ b/hypocurate/worker.py
@@ -44,6 +44,19 @@ def _status(engine: Engine, run_id: int) -> str:
         return conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
 
 
+def _log_finished(engine: Engine, run_id: int) -> None:
+    """Step 10a (the live-run record): one log line for each run that ended under this worker, with its status and
+    its outcome or failure reason as stored (code's own words)."""
+    try:
+        with engine.connect() as conn:
+            row = conn.execute(text("SELECT status, outcome, failure_reason FROM run WHERE id = :r"),
+                               dict(r=run_id)).one()
+        log.info(json.dumps({"run_finished": run_id, "status": row.status, "outcome": row.outcome,
+                             "failure": row.failure_reason}, ensure_ascii=False))
+    except Exception:  # noqa: BLE001 (a log line never fails the worker)
+        log.error(json.dumps({"run_finished_unreadable": run_id}))
+
+
 def _watch(child: guarded.GuardedChild, started: float, stop: threading.Event, lost: threading.Event,
            monitor: queue.Monitor, stall_seconds: float, run_timeout: float) -> str:
     """'ended', or why the child is to be stopped: 'shutdown', 'ownership_lost', 'run_timeout' or 'stalled'. Every
@@ -146,6 +159,8 @@ def work(engine: Engine, claim: queue.Claim, *, phases=("run",), on_phase: Calla
             queue.release(engine, claim, reason, found)
         except Exception:  # noqa: BLE001 (the lease is let go anyway: the claim goes stale)
             log.error(json.dumps({"release_failed": claim.run_id}))
+        if reason == "finished":
+            _log_finished(engine, claim.run_id)
 
 
 def run(once: bool = False, engine: Engine | None = None, max_cycles: int | None = None,
diff --git a/tests/conftest.py b/tests/conftest.py
index 2e22523..433fffc 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -96,3 +96,19 @@ def db(migrated_database):
     engine = make_engine(migrated_database)
     yield engine
     engine.dispose()
+
+
+# Step 10a, a5 (owner, 2026-10-11): the suite runs serially. A parallel run (pytest-xdist) was tried on 4 and then 2
+# workers: on the 2-core machines it gained little, and a test with a 6 s stall allowance
+# (test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance) failed under the
+# load, locally on 4 workers and on GitHub on 2, although it was in a group run on one worker. The owner chose serial
+# for 10a and to revisit the suite's speed in step 11 (register 'parallel_suite'). Kept as a record for that: the
+# files that measure time, race threads or processes, or send signals, which a parallel run would need to keep apart
+# from other load (tests/test_parallel_isolation.py checks that they exist). Every test still has its own database.
+SERIAL_FILES = frozenset({
+    "test_access_dispatch.py", "test_access_layer.py", "test_agent_core.py", "test_checkpoints.py",
+    "test_cli_step9b.py", "test_concurrency.py", "test_confirmation.py", "test_guarded_parent.py",
+    "test_kill_matrix.py", "test_login.py", "test_login_throttle.py", "test_migrations.py",
+    "test_migrations_step9a.py", "test_queue.py", "test_source_versions.py", "test_web_state.py", "test_worker.py",
+    "test_worker_fix1.py", "test_write_retry.py",
+})
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 09ba857..b87a8b5 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -60,7 +60,8 @@ def test_every_category_has_entries_and_keys_are_unique():
 # Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
-PARTLY = {"constructed_test_runs", "question_as_tested"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
+# Step 10a: question_as_tested fully applied (the website's Confirm button).
+PARTLY = {"constructed_test_runs"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -453,7 +454,8 @@ def page_client(register=None):
 
 def signed_in(register=None):
     c = page_client(register)
-    assert c.post("/login", data={"password": PASSWORD}).status_code == 303
+    # Step 10a (owner, 2026-10-11, answer 1): the sign-in form also takes the person's name.
+    assert c.post("/login", data={"password": PASSWORD, "name": "Test Person"}).status_code == 303
     return c
 
 
diff --git a/tests/test_cli_step9b.py b/tests/test_cli_step9b.py
index 7bc33c9..2a6d0fa 100644
--- a/tests/test_cli_step9b.py
+++ b/tests/test_cli_step9b.py
@@ -97,3 +97,14 @@ def test_confirm_works_the_rest_through_a_claim(engine, stub, capsys):
         reasons = [r for (r,) in conn.execute(text("SELECT release_reason FROM run_claim WHERE run_id = :r ORDER BY id"),
                                                dict(r=rid)).all()]
     assert reasons == ["waiting", "finished"]
+
+
+def test_queue_says_where_a_waiting_or_queued_run_is_never_none(engine, stub, capsys):
+    """Step 10a (the live-run record's open item 3): `queue` showed stage "none" for a run waiting at the rules lock."""
+    stub.respond(responder(planner_body()))
+    hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")  # stops at the wait
+    hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer", "--queue")
+    code, out, err = hc(capsys, "queue")
+    assert code == 0, err
+    stages = {r["status"]: r["stage"] for r in json.loads(out)}
+    assert stages == {"waiting": "waiting at the rules lock", "queued": "queued (not started)"}
diff --git a/tests/test_confirmation.py b/tests/test_confirmation.py
index 1da16f6..e9319b8 100644
--- a/tests/test_confirmation.py
+++ b/tests/test_confirmation.py
@@ -275,9 +275,10 @@ def test_a_cancelled_waiting_run_is_not_confirmed(engine, stub):
 
 def test_no_code_confirms_in_bulk_or_by_itself():
     """No bulk or automatic confirmation in step 9 (owner, 2026-10-08): `confirm` takes one run and one name, and
-    the only caller in the package is the command line's `confirm` command."""
+    the only callers in the package are the command line's `confirm` command and, from step 10a (owner's approved
+    plan, 2026-10-11), the web page's confirm action; step 10a adds the shown content's fingerprint (addition 2)."""
     params = list(inspect.signature(confirmation.confirm).parameters)
-    assert params == ["engine", "run_id", "by", "shown"]
+    assert params == ["engine", "run_id", "by", "shown", "shown_fingerprint"]
     package = pathlib.Path(confirmation.__file__).parents[1]
     callers = []
     for path in package.rglob("*.py"):
@@ -288,7 +289,7 @@ def test_no_code_confirms_in_bulk_or_by_itself():
                 callers.append(path.name)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "confirm":
                 callers.append(path.name)
-    assert callers == ["cli_runs.py"], callers
+    assert sorted(callers) == ["app.py", "cli_runs.py"], callers
     source = pathlib.Path(cli_runs.__file__).read_text(encoding="utf-8")
     assert "INSERT INTO rules_confirmation" not in source
     inserts = [p.name for p in package.rglob("*.py") if "INSERT INTO rules_confirmation" in p.read_text(encoding="utf-8")]
@@ -334,7 +335,8 @@ def test_the_cost_shown_is_the_runs_counted_and_reported_cost(engine, stub):
                                           ":r"), dict(r=rid)).one()
     assert Decimal(content["cost_so_far"]["counted_usd"]) == cap > 0
     assert Decimal(content["cost_so_far"]["reported_usd"]) == reported > 0
-    assert f"Cost so far: ${cap:.6f} counted toward the caps (reported ${reported:.6f}; 1 model calls" in words
+    # Step 10a (owner's review, 2026-10-11): "1 model call", in the singular.
+    assert f"Cost so far: ${cap:.6f} counted toward the caps (reported ${reported:.6f}; 1 model call," in words
 
 
 def test_code_locks_only_the_confirmed_plan_and_says_so(engine, stub):
diff --git a/tests/test_confirmation_step10.py b/tests/test_confirmation_step10.py
new file mode 100644
index 0000000..6cf6286
--- /dev/null
+++ b/tests/test_confirmation_step10.py
@@ -0,0 +1,104 @@
+"""Step 10a, owner's addition 2 (2026-10-11): a confirmation page sends back a fingerprint of the content it showed,
+and `confirmation.confirm` refuses other content as `content_changed`, as it refuses other content given whole (step
+9a). Whole runs through the orchestrator, every model call to the local stub."""
+from __future__ import annotations
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import confirmation, orchestrator, queries
+
+
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+@pytest.fixture
+def engine(migrated_database):
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e
+    e.dispose()
+
+
+def waiting(engine, stub):
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
+    return rid
+
+
+def confirmations(engine, rid):
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT count(*) FROM rules_confirmation WHERE run_id = :r"), dict(r=rid)).scalar()
+
+
+def test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item():
+    import hashlib
+    import json
+    c = {"run": 1, "query": "Q-0001", "cost_so_far": {"counted_usd": "0.017640", "calls": 1}, "names": ["ä", "b"]}
+    expected = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
+                              .encode("utf-8")).hexdigest()
+    assert confirmation.content_fingerprint(c) == expected
+    assert confirmation.content_fingerprint(dict(reversed(list(c.items())))) == expected  # key order does not count
+    assert confirmation.content_fingerprint({**c, "cost_so_far": {"counted_usd": "0.017641", "calls": 1}}) != expected
+    assert confirmation.content_fingerprint({**c, "names": ["b", "ä"]}) != expected  # list order does
+
+
+def test_a_matching_fingerprint_confirms(engine, stub):
+    rid = waiting(engine, stub)
+    content, words = confirmation.show(engine, rid)
+    stored = confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=confirmation.content_fingerprint(content))
+    assert stored["shown"] == words and confirmations(engine, rid) == 1
+
+
+@pytest.mark.parametrize("sent", ["", "0" * 64, "not hex"])
+def test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded(engine, stub, sent):
+    rid = waiting(engine, stub)
+    with pytest.raises(queries.QueryRefused) as refused:
+        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=sent)
+    assert refused.value.code == "content_changed"
+    assert confirmations(engine, rid) == 0
+
+
+def test_content_that_changed_after_it_was_shown_is_refused(engine, stub, monkeypatch):
+    """What `confirm` compares is the content as it reads inside its own transaction: content that differs from what
+    the page showed (here one item more) is refused."""
+    rid = waiting(engine, stub)
+    shown = confirmation.content_fingerprint(confirmation.show(engine, rid)[0])
+    original = confirmation.content
+    monkeypatch.setattr(confirmation, "content", lambda conn, run_id: {**original(conn, run_id), "changed": True})
+    with pytest.raises(queries.QueryRefused) as refused:
+        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=shown)
+    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0
+
+
+def test_the_text_shown_says_informative_groups_the_label_now_and_once_confirmed_and_counts_calls_rightly(engine, stub):
+    """The live-run record's open items 2 and 4 (step 10a, a4) and the owner's review: "informative groups", the label
+    at the moment of confirming, and "1 model call" in the singular."""
+    rid = waiting(engine, stub)
+    content, words = confirmation.show(engine, rid)
+    assert "10 informative groups" in words and "independent" not in words
+    assert "Question as tested: yield strength against grain size" in words
+    assert "  Now labelled: the Planner's reading of the claim; not verified by code and, in this version, not " \
+           "confirmed by a person" in words.split("\n")
+    assert "  Once confirmed, labelled: the Planner's reading of the claim; not verified by code; confirmed by the " \
+           "person who confirms on the time of confirming (UTC)" in words.split("\n")
+    assert content["cost_so_far"]["calls"] == 1 and "(reported $" in words and "; 1 model call, 0 without" in words
+    stored = confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=confirmation.content_fingerprint(content))
+    assert stored["shown"] == words  # what is stored is exactly what was shown
+
+
+def test_the_label_once_confirmed_follows_the_readings_own_wording():
+    from hypocurate.pipeline import reading
+    assert confirmation.label_once_confirmed(reading.LABELS["planner"], "Ada", "2026-10-11 10:00:00 UTC") == \
+        reading.CONFIRMED_LABEL.format(by="Ada", at="2026-10-11 10:00:00 UTC")
+    assert confirmation.label_once_confirmed(reading.LABELS["narrower"], "Ada", "then") == \
+        reading.LABELS["narrower"] + "; confirmed by Ada on then"
diff --git a/tests/test_login.py b/tests/test_login.py
index 360f28a..6109170 100644
--- a/tests/test_login.py
+++ b/tests/test_login.py
@@ -16,6 +16,7 @@ from hypocurate.web.app import SESSION_COOKIE, SESSION_MAX_AGE, create_app
 from hypocurate.web.login_throttle import MAX_FAILURES, LoginThrottle
 
 PASSWORD = "test-password-not-a-secret"
+NAME = "Test Person"
 SECRET = "s" * 40
 UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"
 # Paths that only look like the public ones (review finding 3).
@@ -42,7 +43,8 @@ def client(env="development", throttle=None, app=None):
 
 
 def sign_in(c, password=PASSWORD):
-    return c.post("/login", data={"password": password})
+    # Step 10a (owner, 2026-10-11, answer 1): the sign-in form also takes the person's name.
+    return c.post("/login", data={"password": password, "name": NAME})
 
 
 def cookie_payload(value):
@@ -119,10 +121,14 @@ def test_logout_ends_the_session():
 
 # --- the cookie ---------------------------------------------------------------------
 
-def test_cookie_holds_only_the_signed_in_flag():
+def test_cookie_holds_only_the_signed_in_flag_the_name_and_the_form_token():
+    """Step 10a (owner, 2026-10-11, answer 1 and addition 1): the cookie also holds the name given at sign-in and the
+    token every write carries; nothing else."""
     c = client()
     sign_in(c)
-    assert cookie_payload(c.cookies[SESSION_COOKIE]) == {"signed_in": True}
+    payload = cookie_payload(c.cookies[SESSION_COOKIE])
+    assert set(payload) == {"signed_in", "name", "csrf"}
+    assert payload["signed_in"] is True and payload["name"] == NAME and len(payload["csrf"]) >= 40
 
 
 def test_tampered_cookie_is_rejected():
diff --git a/tests/test_parallel_isolation.py b/tests/test_parallel_isolation.py
new file mode 100644
index 0000000..0282bbe
--- /dev/null
+++ b/tests/test_parallel_isolation.py
@@ -0,0 +1,55 @@
+"""Step 10a, a5 (owner's condition 1 for a parallel suite, 2026-10-11): no test can see another test's data. The suite
+runs serially since the owner's decision of 2026-10-11 (register 'parallel_suite'); these checks keep it ready for a
+parallel run.
+
+How it holds: every test that needs tables gets a database of its own, made and dropped by tests/conftest.py
+(`empty_database`, `migrated_database`; random names), from a template each pytest process makes for itself (under
+xdist, one per worker). These checks keep it that way: databases are made only by conftest's `_create`, with random
+names; the one database not made for a test (`DATABASE_URL`'s own) is opened only by the read-only /health and
+`check-db` tests; and the serial group names only files that exist.
+"""
+from __future__ import annotations
+
+import ast
+import os
+import pathlib
+import re
+
+import conftest
+
+TESTS = pathlib.Path(__file__).resolve().parent
+# The tests that open DATABASE_URL's own database: /health and `check-db`, which only read (the schema revision).
+READS_THE_SHARED_DATABASE = {"test_health.py"}
+
+
+def test_databases_are_made_only_by_conftest_with_random_names():
+    for path in TESTS.glob("*.py"):
+        source = path.read_text(encoding="utf-8")
+        if path.name in ("conftest.py", "test_parallel_isolation.py"):
+            continue
+        assert "CREATE DATABASE" not in source.upper(), path.name
+    body = (TESTS / "conftest.py").read_text(encoding="utf-8")
+    assert 'name = f"{prefix}_{uuid.uuid4().hex[:12]}"' in body  # a fresh random name for every database made
+
+
+def test_only_the_read_only_health_tests_open_the_shared_database():
+    """`database_url` (DATABASE_URL's own database) may be named by a test only to make scratch databases from it
+    (`url_for`, `_create`), except in the health tests, which open it to read its schema revision."""
+    for path in TESTS.glob("test_*.py"):
+        tree = ast.parse(path.read_text(encoding="utf-8"))
+        for node in ast.walk(tree):
+            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "make_engine":
+                args = [a.id for a in node.args if isinstance(a, ast.Name)]
+                if "database_url" in args:
+                    assert path.name in READS_THE_SHARED_DATABASE, path.name
+        if path.name in READS_THE_SHARED_DATABASE:
+            text_ = path.read_text(encoding="utf-8")
+            assert not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", text_), path.name
+
+
+def test_each_test_database_is_made_from_a_template_of_this_process(template_database):
+    assert re.fullmatch(r"hypocurate_tmpl_[0-9a-f]{12}", template_database), template_database
+
+
+def test_the_serial_group_names_only_existing_test_files():
+    assert conftest.SERIAL_FILES and all((TESTS / name).is_file() for name in conftest.SERIAL_FILES)
diff --git a/tests/test_reading_step10.py b/tests/test_reading_step10.py
new file mode 100644
index 0000000..5088d61
--- /dev/null
+++ b/tests/test_reading_step10.py
@@ -0,0 +1,82 @@
+"""Step 10a (owner's review of the screenshots, 2026-10-11): the question as tested is labelled by the run's own plan
+source, never by a fallback to the fixed reference plan. The owner found local run 2 (a Planner run of step 8b, the BCC
+claim at 1000 °C) labelled "the fixed reference plan; not read from the claim": step 8b's Planner stage stored no
+reading, so the label fell back to the fixed plan's. A Planner reading locked with no confirmation (possible only
+before migration 0007) now says it predates confirmation; every other label is as before."""
+from __future__ import annotations
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import checkpoints, confirmation, orchestrator, reading, run_view
+from hypocurate.pipeline.plan import reference_plan
+
+
+@pytest.fixture
+def engine(migrated_database):
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e
+    e.dispose()
+
+
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+def planner_path_run_locked_before_confirmations(engine) -> int:
+    """The shape of local runs 1 and 2: not a fixed-plan run, a plan locked, no stored reading, no confirmation."""
+    rid = pw.dispatched_run(engine)
+    vid = pw.version_of(engine, rid)
+    with engine.begin() as conn:  # a second run of the same version, on the Planner's path (fixed_plan false)
+        other = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan) VALUES (:v, false) RETURNING id"),
+                             dict(v=vid)).scalar_one()
+        conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) SELECT :o, "
+                          "source_id, source_version_id, search_status FROM run_source WHERE run_id = :r"),
+                     dict(o=other, r=rid))
+        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'test: superseded' "
+                          "WHERE id = :r"), dict(r=rid))
+        conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :o"), dict(o=other))
+    checkpoints.lock_rules(engine, other, reference_plan(vid))
+    return other
+
+
+def label(engine, rid):
+    with engine.connect() as conn:
+        return reading.stored(conn, rid)
+
+
+def test_a_planner_run_locked_before_confirmations_is_never_labelled_as_the_fixed_plan(engine):
+    rid = planner_path_run_locked_before_confirmations(engine)
+    tested = label(engine, rid)
+    assert tested["label"] == reading.PREDATES_LABEL == ("the Planner's reading of the claim; not verified by code; "
+                                                          "this run predates confirmation")
+    assert tested["source"] == "planner"
+    assert "fixed reference plan" not in str(run_view.show(engine, rid))
+
+
+def test_a_fixed_plan_run_keeps_the_fixed_label(engine):
+    rid = pw.locked_run(engine)
+    assert label(engine, rid)["label"] == reading.LABELS["fixed"]
+
+
+def test_a_waiting_planner_run_is_labelled_not_yet_confirmed_and_once_confirmed_says_by_whom(engine, stub):
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
+    assert label(engine, rid)["label"] == reading.LABELS["planner"]
+    confirmation.confirm(engine, rid, by="Ada Reviewer")
+    assert label(engine, rid)["label"].startswith("the Planner's reading of the claim; not verified by code; "
+                                                  "confirmed by Ada Reviewer on ")
+
+
+def test_a_run_of_no_plan_and_no_reading_has_no_question_as_tested(engine):
+    rid = pw.dispatched_run(engine)
+    assert label(engine, rid) is None
diff --git a/tests/test_web_isolation.py b/tests/test_web_isolation.py
new file mode 100644
index 0000000..223aa76
--- /dev/null
+++ b/tests/test_web_isolation.py
@@ -0,0 +1,75 @@
+"""Step 10a: the web service never calls a model, never claims a run and never runs a pipeline (owner's step 10 brief;
+criterion 14.4: closing the browser or restarting the web service never affects a run).
+
+A fresh process builds the app, signs in and opens every run page; afterwards no model library (dspy, litellm), and
+none of the queue, the worker, the orchestrator, recovery or the guarded runner is loaded in it. The source scan of
+tests/test_worker.py (direct imports in web/) still holds; this checks what a page actually loads.
+"""
+from __future__ import annotations
+
+import json
+import os
+import pathlib
+import subprocess
+import sys
+import textwrap
+
+import pytest
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+
+FORBIDDEN = ("dspy", "litellm", "hypocurate.pipeline.queue", "hypocurate.worker", "hypocurate.pipeline.orchestrator",
+             "hypocurate.pipeline.recovery", "hypocurate.access.guarded", "hypocurate.pipeline.agents.interface")
+
+PROBE = textwrap.dedent("""
+    import json, re, sys
+    from fastapi.testclient import TestClient
+    from hypocurate.config import Settings
+    from hypocurate.web.app import create_app
+    url, completed, waiting = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
+    s = Settings(env="development", database_url=url, password="test-password-not-a-secret", session_secret="s" * 40,
+                 version="test")
+    c = TestClient(create_app(s), base_url="http://testserver", follow_redirects=False)
+    assert c.post("/login", data={"password": "test-password-not-a-secret", "name": "Probe"}).status_code == 303
+    codes = [c.get(p).status_code for p in ("/", "/runs", f"/runs/{completed}", f"/runs/{waiting}",
+                                            f"/runs/{waiting}/confirm", "/assumptions")]
+    print(json.dumps({"codes": codes, "loaded": sorted(m for m in sys.modules if m.startswith(("dspy", "litellm",
+                                                                                          "hypocurate")))}))
+""")
+
+
+@pytest.fixture
+def engine(migrated_database):
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e
+    e.dispose()
+
+
+def test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner(engine, migrated_database, tmp_path):
+    stub = sp.StubProvider()
+    try:
+        stub.respond(to.responder(to.planner_body()))
+        done = to.dispatched(engine, fixed_plan=True)
+        assert to.run(engine, done, stub).status == "completed"
+        waiting = to.dispatched(engine)
+        from hypocurate.pipeline import orchestrator
+        assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
+    finally:
+        stub.close()
+    probe = tmp_path / "probe.py"
+    probe.write_text(PROBE, encoding="utf-8")
+    # The package from this checkout (installed in a venv, or only on the path as in the test image).
+    root = pathlib.Path(__file__).resolve().parents[1]
+    env = {**os.environ, "PYTHONPATH": str(root)}
+    out = subprocess.run([sys.executable, str(probe), migrated_database, str(done), str(waiting)], cwd=tmp_path,
+                         env=env, capture_output=True, text=True, timeout=300)
+    assert out.returncode == 0, out.stderr[-2000:]
+    result = json.loads(out.stdout.strip().splitlines()[-1])
+    assert result["codes"] == [200, 200, 200, 200, 200, 200]
+    loaded = set(result["loaded"])
+    assert "hypocurate.web.app" in loaded and "hypocurate.pipeline.run_view" in loaded  # the probe did load the pages
+    assert not [m for m in loaded if m in FORBIDDEN or m.split(".")[0] in ("dspy", "litellm")], loaded
diff --git a/tests/test_web_runs.py b/tests/test_web_runs.py
new file mode 100644
index 0000000..2484342
--- /dev/null
+++ b/tests/test_web_runs.py
@@ -0,0 +1,503 @@
+"""Step 10a: the run pages (owner's step 10 brief and approval of 2026-10-11, with additions 1 to 3 and 6).
+
+The run viewer (code's statement first, then the Analyst's text under its label, per-source results, sensitivity sets
+by display name, cautions, cost), the evidence dial, the confirmation of the question as tested by the signed-in
+person (the same content and function as the command line's `confirm`, with the shown content's fingerprint sent
+back), cancel, the name fixed for the session, and CSRF tokens on every write.
+
+One database per module holds the runs that are only read; every test that writes builds its own waiting run on a
+database of its own. Every model call goes to the local stub (as tests/test_orchestrator.py).
+"""
+from __future__ import annotations
+
+import base64
+import html
+import json
+import re
+
+import pytest
+from fastapi.testclient import TestClient
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from conftest import _create, _drop, url_for
+from hypocurate.config import Settings
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import confirmation, orchestrator, queries, run_view
+from hypocurate.pipeline import statistics as st
+from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, SENSITIVITY_CHANGES
+from hypocurate.web import dial, security
+from hypocurate.web.app import SESSION_COOKIE, create_app
+
+PASSWORD = "test-password-not-a-secret"
+SECRET = "s" * 40
+NAME = "Grace Reviewer"
+
+
+def make_client(engine, url):
+    s = Settings(env="development", database_url=url, password=PASSWORD, session_secret=SECRET, version="test")
+    return TestClient(create_app(s, engine=engine), base_url="http://testserver", follow_redirects=False)
+
+
+def signed_in(engine, url, name=NAME):
+    c = make_client(engine, url)
+    assert c.post("/login", data={"password": PASSWORD, "name": name}).status_code == 303
+    return c
+
+
+def session(c) -> dict:
+    payload = c.cookies[SESSION_COOKIE].split(".")[0]
+    return json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4)))
+
+
+def token(c) -> str:
+    return session(c)["csrf"]
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def plain(page: str) -> str:
+    """The page's visible text, tags removed and entities decoded, whitespace collapsed; a superscript is read back
+    as "^" (the screens write exponents as superscripts; the stored text has "^")."""
+    page = page.replace("<sup>", "^").replace("</sup>", "")
+    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page)).split())
+
+
+def completed(engine, stub, claim=to.FCC_CLAIM, fixed_plan=True, marked=False):
+    stub.respond(to.responder(to.BCC if claim == to.BCC_CLAIM else None))
+    q = queries.create(engine, claim, ("mpea", "tamu_fcc"))
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan, constructed_test_data=marked)
+    assert to.run(engine, rid, stub).status == "completed"
+    return rid
+
+
+def waiting(engine, stub):
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
+    return rid
+
+
+@pytest.fixture(scope="module")
+def world(admin, database_url, template_database):
+    """Runs that are only read: the 14.1a fixed-plan run, the BCC claim (insufficient), a marked test run, a waiting
+    Planner run, a queued run and a cancelled one."""
+    name = _create(admin, "hypocurate_t", template=template_database)
+    url = url_for(database_url, name)
+    engine = make_engine(url)
+    stub = sp.StubProvider()
+    try:
+        pw.registered(engine, ("mpea", "tamu_fcc"))
+        runs = {"sufficient": completed(engine, stub), "insufficient": completed(engine, stub, to.BCC_CLAIM, False),
+                "test_run": completed(engine, stub, marked=True), "waiting": waiting(engine, stub),
+                "queued": to.dispatched(engine, fixed_plan=True), "cancelled": to.dispatched(engine, fixed_plan=True)}
+        queries.cancel(engine, runs["cancelled"], by="Ada Reviewer")
+        yield engine, url, runs
+    finally:
+        stub.close()
+        engine.dispose()
+        _drop(admin, name)
+
+
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+@pytest.fixture
+def own(migrated_database):
+    """A database of its own, for a test that writes."""
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e, migrated_database
+    e.dispose()
+
+
+# --- the run viewer --------------------------------------------------------------------------------------------------
+
+def test_the_run_viewer_shows_codes_statement_first_then_the_analysts_text_then_sources_sets_cautions_and_cost(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
+    lines = run_view.show(engine, runs["sufficient"])["statement"]
+    first_line = next(x for x in lines if x.startswith("Outcome:"))
+    order = [first_line, "Explanation by the Analyst", "written by a language model; values inserted from the run "
+             "record; narrative not verified", "Each source alone, and all together", "Sensitivity sets", "Cautions",
+             "Tokens and cost"]
+    at = [page.index(x) for x in order]
+    assert at == sorted(at), dict(zip(order, at))
+
+
+def test_every_line_of_codes_statement_is_on_the_page_unchanged(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
+    for line in run_view.show(engine, runs["sufficient"])["statement"]:
+        assert " ".join(line.split()) in page, line
+
+
+def test_the_reference_numbers_are_shown_as_code_formatted_them(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
+    assert "424.9 MPa·µm^0.5 ± 64.4 MPa·µm^0.5 (one standard error)" in page
+    assert "424.1 MPa·µm^0.5 ± 62.2 MPa·µm^0.5" in page
+    assert "1173.3 MPa·µm^0.5; coefficient only (insufficient groups): no uncertainty, no p-value" in page
+
+
+def test_sensitivity_sets_are_shown_by_display_name_never_by_internal_name(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
+    assert INFLUENCE_DISPLAY_NAME in plain(page)
+    for key in [*SENSITIVITY_CHANGES, "primary"]:
+        assert key not in page, key
+    for key, name in run_view.SET_DISPLAY_NAMES.items():
+        if key != "primary":
+            assert html.escape(name) in page, name
+
+
+def test_the_dial_shows_the_level_and_label_with_the_verdict_beside_it_not_in_it(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
+    svg = re.search(r'<svg class="dial dial-large".*?</svg>', page, re.S).group(0)
+    assert "Level 6 of 6: tested answer" in plain(page)
+    assert "Verdict: supported under the stated model, in the sources searched" in plain(page)
+    assert "supported" not in svg and "<text" not in svg
+    assert svg.count('class="seg seg-') == 6 and 'class="seg seg-6 current"' in svg and "hatch" not in svg
+
+
+def test_an_insufficient_run_shows_no_verdict_and_level_1(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['insufficient']}").text)
+    assert "No verdict" in page and "Verdict:" not in page
+    assert "Level 1 of 6: nothing tested" in page
+    assert "insufficient in the sources searched" in page
+    assert "do not exist" not in page
+
+
+def test_a_marked_test_runs_dial_is_hatched_with_a_badge(world):
+    engine, url, runs = world
+    c = signed_in(engine, url)
+    page = c.get(f"/runs/{runs['test_run']}").text
+    svg = re.search(r'<svg class="dial dial-large".*?</svg>', page, re.S).group(0)
+    assert "<pattern id=\"hatch" in svg and "url(#hatch" in svg
+    assert run_view.TEST_RUN_BADGE in plain(page) and "test run" in plain(page)
+    real = c.get(f"/runs/{runs['sufficient']}").text
+    assert run_view.TEST_RUN_BADGE not in plain(real)
+
+
+def test_the_runs_list_shows_a_small_dial_for_every_run(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get("/runs").text
+    assert page.count('class="dial dial-small"') == len(runs)
+    assert page.count("Level 6 of 6: tested answer") >= 2 and "Level 1 of 6: nothing tested" in page
+    shown = plain(page)  # the visible words (each dial's words are also its accessible name)
+    assert shown.count(run_view.NOT_COMPLETED) == 2  # the waiting and the queued run
+    assert shown.count(run_view.FAILED_NO_LEVEL) == 1  # the cancelled run (owner, 2026-10-11)
+    assert f'aria-label="{run_view.FAILED_NO_LEVEL}"' in page
+
+
+def test_states_are_shown_in_words_and_a_waiting_run_waits_at_the_rules_lock(world):
+    engine, url, runs = world
+    c = signed_in(engine, url)
+    waiting_page = plain(c.get(f"/runs/{runs['waiting']}").text)
+    assert "waiting at the rules lock" in waiting_page and "none" not in waiting_page.split("Status", 1)[1][:80]
+    assert f"Waits for {confirmation.WAITING_FOR}" in waiting_page
+    assert "queued" in plain(c.get(f"/runs/{runs['queued']}").text)
+
+
+def test_an_unknown_run_is_not_found(world):
+    engine, url, _ = world
+    assert signed_in(engine, url).get("/runs/999999").status_code == 404
+
+
+# --- the dial itself -------------------------------------------------------------------------------------------------
+
+def test_the_dial_has_one_hue_that_darkens_with_the_level():
+    def lightness(hex_colour):
+        r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
+        return (max(r, g, b) + min(r, g, b)) / 2
+
+    def hue(hex_colour):
+        import colorsys
+        r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
+        return colorsys.rgb_to_hls(r, g, b)[0] * 360
+    shades = dial.SHADES
+    assert len(shades) == dial.LEVELS == len(st.EVIDENCE_SHORT) == len(st.EVIDENCE_LEVELS) == 6
+    assert all(lightness(a) > lightness(b) for a, b in zip(shades, shades[1:]))
+    assert max(hue(s) for s in shades) - min(hue(s) for s in shades) < 10  # one hue, not red to green
+
+
+@pytest.mark.parametrize("level", range(1, 7))
+def test_the_needle_points_at_the_runs_level(level):
+    svg = str(dial.svg(level, label=f"Level {level}"))
+    assert svg.count(" current") == 1 and f'class="seg seg-{level} current"' in svg
+    x2 = float(re.search(r'class="needle"[^>]*x2="([-\d.]+)"', svg).group(1))
+    assert (x2 < 100) == (level <= 3)  # levels 1 to 3 on the left half
+
+
+def test_the_dial_refuses_a_level_outside_1_to_6():
+    for level in (0, 7):
+        with pytest.raises(ValueError):
+            dial.svg(level)
+
+
+def test_the_short_labels_are_the_owners_set():
+    assert dict(st.EVIDENCE_SHORT) == {6: "tested answer", 5: "exploratory answer", 4: "coefficient only",
+                                       3: "below the minimums", 2: "no coefficient fitted", 1: "nothing tested"}
+
+
+# --- the confirmation page and the confirmation ------------------------------------------------------------------------
+
+def test_the_confirmation_page_shows_exactly_what_the_command_line_shows(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['waiting']}/confirm").text
+    content, words = confirmation.show(engine, runs["waiting"])
+    for line in words.split("\n"):
+        assert " ".join(line.split()) in plain(page), line
+    assert f'name="content_fingerprint" value="{confirmation.content_fingerprint(content)}"' in page
+    assert f"Confirming as {NAME}" in plain(page)
+
+
+def test_the_confirmation_page_shows_the_label_now_and_the_label_once_confirmed(world):
+    """The live-run record's open item 4: the text shown at the moment of confirming says the label now and the label
+    once confirmed (the same text on the command line); beside the button, the label under the signed-in name."""
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['waiting']}/confirm").text)
+    assert "Now labelled: the Planner's reading of the claim; not verified by code and, in this version, not " \
+           "confirmed by a person" in page
+    assert "Once confirmed, labelled: the Planner's reading of the claim; not verified by code; confirmed by the " \
+           "person who confirms on the time of confirming (UTC)" in page
+    assert f"Once you confirm, the question as tested is labelled: the Planner's reading of the claim; not verified " \
+           f"by code; confirmed by {NAME} on the time you confirm (UTC)." in page
+
+
+def test_confirming_records_the_signed_in_name_and_exactly_the_text_shown_and_runs_nothing(own, stub):
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    page = c.get(f"/runs/{rid}/confirm").text
+    fp = re.search(r'name="content_fingerprint" value="([0-9a-f]{64})"', page).group(1)
+    stages = one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid)
+    calls = len(stub.requests)
+    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "content_fingerprint": fp})
+    assert r.status_code == 303 and r.headers["location"] == f"/runs/{rid}?done=confirmed"
+    with engine.connect() as conn:
+        row = conn.execute(text("SELECT confirmed_by, shown FROM rules_confirmation WHERE run_id = :r"),
+                           dict(r=rid)).one()
+    assert row.confirmed_by == NAME and row.shown == confirmation.show(engine, rid)[1]
+    # The web service runs nothing: the run still waits for a worker; no stage, claim or model call was added.
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == stages
+    assert one(engine, "SELECT count(*) FROM run_claim WHERE run_id = :r", r=rid) == 0
+    assert len(stub.requests) == calls
+    assert "Confirmed under your name" in plain(c.get(f"/runs/{rid}?done=confirmed").text)
+
+
+def test_a_confirmation_of_content_other_than_what_was_shown_is_refused(own, stub):
+    """Owner's addition 2: the page sends back the fingerprint of what it showed; other content is content_changed."""
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    for fp in ("0" * 64, confirmation.content_fingerprint({"run": rid})):
+        r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "content_fingerprint": fp})
+        assert r.status_code == 409 and "show it again before confirming" in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
+
+
+def test_a_confirmation_without_the_shown_contents_fingerprint_is_refused(own, stub):
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c)})
+    assert r.status_code == 409
+    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
+
+
+@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
+def test_a_write_without_the_sessions_token_is_refused_and_writes_nothing(own, stub, sent):
+    """Owner's addition 1: confirm and cancel (10a's writes) refuse a request without the session's token."""
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    fp = confirmation.content_fingerprint(confirmation.show(engine, rid)[0])
+    extra = {} if sent is None else {"csrf_token": sent}
+    assert c.post(f"/runs/{rid}/confirm", data={"content_fingerprint": fp, **extra}).status_code == 403
+    assert c.post(f"/runs/{rid}/cancel", data=extra).status_code == 403
+    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
+
+
+def test_another_sessions_token_is_refused(own, stub):
+    engine, url = own
+    rid = waiting(engine, stub)
+    a, b = signed_in(engine, url), signed_in(engine, url, "Other Person")
+    assert token(a) != token(b)
+    assert b.post(f"/runs/{rid}/cancel", data={"csrf_token": token(a)}).status_code == 403
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
+
+
+def test_cancel_records_the_signed_in_name(own, stub):
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    r = c.post(f"/runs/{rid}/cancel", data={"csrf_token": token(c)})
+    assert r.status_code == 303
+    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=rid) == \
+        queries.CANCELLED["waiting"].format(by=NAME)
+
+
+def test_a_completed_run_cannot_be_cancelled_and_the_reason_is_shown(world):
+    engine, url, runs = world
+    c = signed_in(engine, url)
+    r = c.post(f"/runs/{runs['sufficient']}/cancel", data={"csrf_token": token(c)})
+    assert r.status_code == 409 and "Not cancelled:" in plain(r.text)
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=runs["sufficient"]) == "completed"
+
+
+def test_a_completed_run_has_no_confirmation_to_give(world):
+    engine, url, runs = world
+    c = signed_in(engine, url)
+    assert "is not waiting for a confirmation" in plain(c.get(f"/runs/{runs['sufficient']}/confirm").text)
+    r = c.post(f"/runs/{runs['sufficient']}/confirm", data={"csrf_token": token(c), "content_fingerprint": "0" * 64})
+    assert r.status_code == 409
+
+
+# --- the name at sign-in ---------------------------------------------------------------------------------------------
+
+def test_signing_in_needs_a_name_and_keeps_it_with_a_token(world):
+    engine, url, _ = world
+    c = make_client(engine, url)
+    for bad in ("", "   ", "x" * (security.NAME_MAX + 1)):
+        r = c.post("/login", data={"password": PASSWORD, "name": bad})
+        assert r.status_code == 400 and SESSION_COOKIE not in c.cookies
+    assert c.post("/login", data={"password": PASSWORD, "name": "  Ada   Lovelace "}).status_code == 303
+    s = session(c)
+    assert set(s) == {"signed_in", "name", "csrf"} and s["name"] == "Ada Lovelace" and len(s["csrf"]) >= 40
+    assert "Signed in: Ada Lovelace" in plain(c.get("/runs").text)
+
+
+def test_the_name_cannot_change_within_a_session(world):
+    """Owner's addition 3: a new name means signing out and in again."""
+    engine, url, _ = world
+    c = signed_in(engine, url, "First Name")
+    before = session(c)
+    r = c.post("/login", data={"password": PASSWORD, "name": "Second Name"})
+    assert r.status_code == 409 and "signed in as First Name" in plain(r.text)
+    assert session(c) == before
+    c.post("/logout")
+    assert c.post("/login", data={"password": PASSWORD, "name": "Second Name"}).status_code == 303
+    assert session(c)["name"] == "Second Name" and session(c)["csrf"] != before["csrf"]
+
+
+def test_a_session_without_a_name_cannot_act(own, stub):
+    """A cookie signed before step 10a holds no name: it may read but must sign in again before it acts."""
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    from itsdangerous import TimestampSigner
+    old = base64.b64encode(json.dumps({"signed_in": True, "csrf": "t" * 43}).encode())
+    c.cookies.set(SESSION_COOKIE, TimestampSigner(SECRET).sign(old).decode())
+    assert c.get(f"/runs/{rid}").status_code == 200
+    assert c.post(f"/runs/{rid}/cancel", data={"csrf_token": "t" * 43}).status_code == 403
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
+
+
+# --- text size and the glossary --------------------------------------------------------------------------------------
+
+def test_no_text_on_any_screen_is_smaller_than_12px():
+    """Owner's addition 6: every font-size in the stylesheet is in rem (no em, which compounds) and at least
+    0.75rem = 12 px; no template sets a size of its own; the dial holds no text."""
+    import pathlib
+    web = pathlib.Path(dial.__file__).resolve().parent
+    css = (web / "static" / "style.css").read_text(encoding="utf-8")
+    sizes = re.findall(r"font(?:-size)?\s*:\s*([^;}]+)", css)
+    assert sizes
+    for value in sizes:
+        for number, unit in re.findall(r"([\d.]+)(rem|px|em|pt|%|vw|vh)\b", value):
+            assert unit in ("rem", "px"), value
+            assert float(number) * (16 if unit == "rem" else 1) >= 12, value
+    for t in (web / "templates").glob("*.html"):
+        assert "font-size" not in t.read_text(encoding="utf-8") and "style=" not in t.read_text(encoding="utf-8"), t
+    for level in (None, *range(1, 7)):
+        for size in dial.SIZES:
+            assert "<text" not in str(dial.svg(level, True, size))
+
+
+def test_every_information_button_in_the_templates_has_a_glossary_entry():
+    import pathlib
+    from hypocurate.web import glossary
+    web = pathlib.Path(dial.__file__).resolve().parent
+    used = set()
+    for t in (web / "templates").glob("*.html"):
+        used |= set(re.findall(r'info\("([a-z_]+)"\)', t.read_text(encoding="utf-8")))
+    assert used and used <= set(glossary.by_key())
+    assert "evidence_level" in used
+
+
+def test_an_information_button_has_its_accessible_name_and_the_glossary_text(world):
+    from hypocurate.web import glossary
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
+    e = glossary.entry("evidence_level")
+    assert f'aria-label="Explain: {html.escape(e["term"])}"' in page
+    assert html.escape(e["text"]) in page
+
+
+def test_every_sensitivity_set_has_a_display_name_and_a_description():
+    from hypocurate.pipeline.eligibility import INFLUENCE_KEY
+    for key in SENSITIVITY_CHANGES:
+        assert run_view._set_display_name(key) != "another sensitivity set", key
+        assert run_view._set_description(key), key
+    assert set(run_view.SET_DESCRIPTIONS) | {INFLUENCE_KEY} == set(SENSITIVITY_CHANGES)
+
+
+# --- the owner's review of the screenshots (2026-10-11) ---------------------------------------------------------------
+
+def test_units_are_written_with_a_real_superscript_on_the_screens(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
+    assert "MPa·µm<sup>0.5</sup>" in page and "µm^0.5" not in page
+    assert "^0.5" in " ".join(run_view.show(engine, runs["sufficient"])["statement"])  # the stored text keeps "^"
+
+
+def test_the_large_dial_shows_the_level_label_without_the_long_wording(world):
+    engine, url, runs = world
+    page = signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text
+    box = re.search(r'<div class="dial-box">.*?</div>\s*</div>', page, re.S).group(0)
+    assert "Level 6 of 6: tested answer" in box and st.EVIDENCE_LEVELS[6] not in box
+
+
+def test_the_survivor_set_says_that_conflicting_values_are_normally_left_out():
+    assert run_view._set_description("conflicts_survivor_value") == (
+        "Conflicting values, left out of the main result, are included once each, using the survivor's value.")
+
+
+def test_the_evidence_level_help_says_a_minimum_missed():
+    from hypocurate.web import glossary
+    text_ = glossary.entry("evidence_level")["text"]
+    assert "5 an exploratory answer, with a minimum missed;" in text_ and "waived" not in text_
+
+
+def test_one_model_call_is_singular(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
+    assert "1 model call ·" in page and "1 model calls" not in page
+
+
+def test_an_old_run_without_a_stored_ceiling_shows_not_recorded(own, stub):
+    """Runs dispatched before migration 0007 have no ceiling. The database never lets a new run store none (0007's
+    trigger), so the test makes an old run's row by switching triggers off for one statement on its own database."""
+    engine, url = own
+    rid = to.dispatched(engine, fixed_plan=True)
+    with engine.begin() as conn:
+        conn.execute(text("SET LOCAL session_replication_role = replica"))
+        conn.execute(text("UPDATE run SET spending_ceiling = NULL WHERE id = :r"), dict(r=rid))
+    page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
+    assert "ceiling for this run not recorded" in page and "$0.000000" not in page.split("ceiling for this run")[1][:20]
diff --git a/tests/test_web_state.py b/tests/test_web_state.py
new file mode 100644
index 0000000..7d69ecd
--- /dev/null
+++ b/tests/test_web_state.py
@@ -0,0 +1,151 @@
+"""Step 10a, milestone a3: run states and live updates (owner's brief: the page updates by itself while a run is in
+progress; owner, 2026-10-11: a small polling script of our own, which stops once the run reaches an end state).
+
+The server decides when polling ends: an open run's state carries `data-poll` (its own address); an ended run's carries
+`data-ended` and no address; `static/poll.js` asks again only when the state it received carries `data-poll`. These tests
+check that contract on every state, and the script's source for the rule; the browser itself is checked separately
+with Playwright (step 10a summary). Criterion 14.4: a run goes on to its end whether or not a page is open, and across
+a restart of the web service, because the web service only reads.
+"""
+from __future__ import annotations
+
+import os
+import pathlib
+import re
+import subprocess
+import sys
+import time
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import orchestrator, queries, run_view
+from test_web_runs import make_client, plain, signed_in, token
+
+POLL_JS = pathlib.Path(run_view.__file__).resolve().parents[1] / "web" / "static" / "poll.js"
+
+
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+@pytest.fixture
+def own(migrated_database, monkeypatch, stub):
+    for k, v in (("DATABASE_URL", migrated_database), ("ANTHROPIC_API_BASE", stub.base_url),
+                 ("ANTHROPIC_BASE_URL", stub.base_url), ("ANTHROPIC_API_KEY", sp.DUMMY_KEY)):
+        monkeypatch.setenv(k, v)
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e, migrated_database
+    e.dispose()
+
+
+def state_attrs(page: str) -> str:
+    return re.search(r'<section class="state[^"]*" id="run-state"[^>]*>', page, re.S).group(0)
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def test_an_open_runs_page_polls_its_own_state_and_an_ended_runs_page_does_not(own, stub):
+    engine, url = own
+    c = signed_in(engine, url)
+    queued = to.dispatched(engine, fixed_plan=True)
+    assert f'data-poll="/runs/{queued}/state"' in state_attrs(c.get(f"/runs/{queued}").text)
+    stub.respond(to.responder(to.planner_body()))
+    waiting = to.dispatched(engine)
+    assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
+    assert f'data-poll="/runs/{waiting}/state"' in state_attrs(c.get(f"/runs/{waiting}").text)
+    running = pw.locked_run(engine)
+    page = c.get(f"/runs/{running}").text
+    assert f'data-poll="/runs/{running}/state"' in state_attrs(page)
+    assert re.search(r"running\s*:\s*" + re.escape(run_view.STAGE_WORDS["curation"]), plain(page))  # stage in words
+    # Ended: a completed run's page has no state to poll; a failed run's state says it ended and carries no address.
+    stub.respond(to.responder())
+    assert to.run(engine, queued, stub).status == "completed"
+    done = c.get(f"/runs/{queued}").text
+    assert "data-poll" not in done and 'id="run-state"' not in done
+    queries.cancel(engine, waiting, by="Ada Reviewer")
+    failed = state_attrs(c.get(f"/runs/{waiting}").text)
+    assert 'data-ended="true"' in failed and "data-poll" not in failed
+
+
+def test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended(own, stub):
+    engine, url = own
+    c = signed_in(engine, url)
+    rid = to.dispatched(engine, fixed_plan=True)
+    first = c.get(f"/runs/{rid}/state")
+    assert first.status_code == 200 and first.headers["cache-control"] == "no-store"
+    assert f'data-poll="/runs/{rid}/state"' in state_attrs(first.text) and "queued" in plain(first.text)
+    assert c.post(f"/runs/{rid}/cancel", data={"csrf_token": token(c)}).status_code == 303
+    ended = c.get(f"/runs/{rid}/state").text
+    assert 'data-ended="true"' in state_attrs(ended) and "data-poll" not in ended
+    assert "Failed: cancelled: cancelled by Grace Reviewer before it started" in plain(ended)
+
+
+def test_the_state_fragment_needs_the_login_and_a_known_run(own):
+    engine, url = own
+    rid = to.dispatched(engine, fixed_plan=True)
+    assert make_client(engine, url).get(f"/runs/{rid}/state").status_code == 303
+    assert signed_in(engine, url).get("/runs/999999/state").status_code == 404
+
+
+def test_the_script_asks_again_only_when_the_state_it_received_carries_an_address():
+    """The script's rule, from its source: one timer, set only by `schedule`; `schedule` is called on start and after
+    a fragment only when that fragment carries data-poll, and on a network error (the same address); on data-ended the
+    page reloads and nothing is scheduled."""
+    js = POLL_JS.read_text(encoding="utf-8")
+    assert js.count("setTimeout") == 1 and js.count("setInterval") == 0
+    assert re.search(r"function schedule\(url\) \{\s*window\.setTimeout\(", js)
+    calls = re.findall(r"^.*schedule\((?!url\) \{).*$", js, re.M)
+    assert len(calls) == 3, calls
+    assert any("if (url) { schedule(url); }" in c for c in calls)        # start: only with an address
+    assert any("if (again) { schedule(again); }" in c for c in calls)    # after a fragment: only with an address
+    assert any(".catch(function () { schedule(url); })" in c for c in calls)  # a failed request: the same address
+    ended = re.search(r'if \(next\.getAttribute\("data-ended"\) === "true"\) \{([^}]*)\}', js).group(1)
+    assert "location.reload()" in ended and "return" in ended and "schedule" not in ended
+    again = js.index('var again = next.getAttribute("data-poll");')
+    assert js.index('getAttribute("data-ended")') < again  # an ended fragment never reaches the next schedule
+
+
+def test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart(own, stub):
+    """Criterion 14.4, bullets 1 and 3: a worker works the run; one web app reads its state and is then dropped (the
+    browser closed); a new app on the same database (the web service restarted) reads on until the run ends. The run
+    completes with the reference result, worked by the worker alone; the web service wrote nothing."""
+    engine, url = own
+    stub.respond(to.responder())
+    rid = to.dispatched(engine, fixed_plan=True)
+    proc = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", "--once"], stdout=subprocess.PIPE,
+                            stderr=subprocess.PIPE, text=True, env=dict(os.environ))
+    try:
+        first = signed_in(engine, url)
+        seen = {first.get(f"/runs/{rid}/state").status_code for _ in range(3)}
+        assert seen == {200}
+        del first  # the browser is closed
+        second = signed_in(engine, url)  # the web service restarted: a new app, nothing carried over
+        deadline = time.time() + 300
+        while time.time() < deadline and "data-ended" not in second.get(f"/runs/{rid}/state").text:
+            time.sleep(0.5)
+        out, err = proc.communicate(timeout=300)
+        assert proc.returncode == 0, err[-3000:]
+    finally:
+        if proc.poll() is None:
+            proc.kill()
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
+    pooled = run_view.show(engine, rid)["results"][0]
+    assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
+    assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
+    with engine.connect() as conn:
+        claims = conn.execute(text("SELECT worker, release_reason FROM run_claim WHERE run_id = :r"), dict(r=rid)).all()
+    assert len(claims) == 1 and claims[0].release_reason == "finished"
+    page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
+    assert "Level 6 of 6: tested answer" in page and "completed" in page
diff --git a/tests/test_web_textfmt.py b/tests/test_web_textfmt.py
new file mode 100644
index 0000000..d8a3ad5
--- /dev/null
+++ b/tests/test_web_textfmt.py
@@ -0,0 +1,35 @@
+"""Step 10a (owner's review of the screenshots, 2026-10-11): the Analyst's text showed raw ** and |---|. It is shown in a
+small safe subset of Markdown (bold, lists, simple tables), everything escaped first; exponents are superscripts on the
+screens only."""
+from __future__ import annotations
+
+from hypocurate.web.textfmt import model_text, units
+
+
+def test_bold_lists_and_a_simple_table_are_rendered_and_no_raw_signs_remain():
+    text = ("The claim is **supported** here.\n\n- first point\n- second **point**\n\n1. one\n2. two\n\n"
+            "| Source | Estimate |\n|---|---:|\n| MPEA | 424.1 MPa·µm^0.5 |\n| Texas A&M | 1173.3 |")
+    out = str(model_text(text))
+    assert "<p>The claim is <strong>supported</strong> here.</p>" in out
+    assert "<ul><li>first point</li><li>second <strong>point</strong></li></ul>" in out
+    assert "<ol><li>one</li><li>two</li></ol>" in out
+    assert "<thead><tr><th>Source</th><th>Estimate</th></tr></thead>" in out
+    assert "<td>424.1 MPa·µm<sup>0.5</sup></td>" in out and "<td>Texas A&amp;M</td>" in out
+    assert "**" not in out and "---" not in out and "|" not in out
+
+
+def test_everything_the_model_writes_is_escaped():
+    out = str(model_text('<script>alert(1)</script> **<b>x</b>** <img src=x onerror=y> & "q"\n- <i>item</i>'))
+    assert "<script>" not in out and "<b>" not in out and "<img" not in out and "<i>" not in out
+    assert "&lt;script&gt;" in out and "<strong>&lt;b&gt;x&lt;/b&gt;</strong>" in out and "&amp;" in out
+    assert "<li>&lt;i&gt;item&lt;/i&gt;</li>" in out
+
+
+def test_a_heading_mark_is_dropped_and_other_signs_stay_as_text():
+    out = str(model_text("## Result\nA * B and 2 ^ x"))
+    assert out == "<p>Result A * B and 2 ^ x</p>"
+
+
+def test_units_escapes_and_writes_exponents_as_superscripts():
+    assert str(units("k = 424.9 MPa·µm^0.5 and d^-1/2 <x>")) == \
+        "k = 424.9 MPa·µm<sup>0.5</sup> and d<sup>-1/2</sup> &lt;x&gt;"
diff --git a/tests/test_worker.py b/tests/test_worker.py
index ae13ca3..60b7164 100644
--- a/tests/test_worker.py
+++ b/tests/test_worker.py
@@ -249,3 +249,20 @@ def test_a_child_whose_run_is_held_by_another_child_is_busy_and_writes_nothing(e
         holder.commit()
     assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == 0
     assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+
+
+def test_the_worker_logs_each_claim_and_each_finished_run(engine, stub):
+    """Step 10a (the live-run record): the worker's log has one line for the claim and one for the finished run, with
+    its status and outcome, so the Render log shows both."""
+    import json as _json
+    stub.respond(to.responder())
+    rid = to.dispatched(engine, fixed_plan=True)
+    proc = worker("--once", wait=False)
+    out, err = proc.communicate(timeout=600)
+    assert proc.returncode == 0, err[-3000:]
+    events = [_json.loads(line[line.index("{"):]) for line in (out + err).splitlines() if "{" in line
+              and ('"claimed"' in line or '"run_finished"' in line)]
+    assert [e for e in events if "claimed" in e] == [{"claimed": rid, "claim": events[0]["claim"],
+                                                     "worker": events[0]["worker"], "status_before": "queued"}]
+    assert [e for e in events if "run_finished" in e] == [{"run_finished": rid, "status": "completed",
+                                                          "outcome": "sufficient", "failure": None}]

```

## 5. Test output

### main, serial with timings (a0)
```
(3207 durations < 0.005s hidden.  Use -vv to show these durations.)
2220 passed, 1 warning in 2090.39s (0:34:50)
exit 0
```
### 4 workers (first parallel run)
```
=========================== short test summary info ============================
FAILED tests/test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance
1 failed, 2291 passed, 4 warnings in 2050.30s (0:34:10)
exit 1
```
### 2 workers (second parallel run)
```
=========================== short test summary info ============================
FAILED tests/test_assumptions.py::test_every_applied_entry_names_settings_that_exist_and_match
1 failed, 2291 passed, 2 warnings in 1925.50s (0:32:05)
exit 1
```
### Final serial and parallel on 2c82b6c
```
2292 passed, 1 warning in 2158.67s (0:35:58)
exit 0
2292 passed, 2 warnings in 1897.35s (0:31:37)
exit 0
```
### Serial against parallel (JUnit)
```
serial: 2292 tests {'passed': 2292}
parallel: 2292 tests {'passed': 2292}
only serial: []
only parallel: []
different outcome: []
IDENTICAL

```
### Local whole suite on 5662200
```
2292 passed, 2 warnings in 1900.36s (0:31:40)
exit 0
```
### Local whole suite on the final head (serial)
```
2292 passed, 1 warning in 2284.28s (0:38:04)
exit 0
```
### The test image's suite on 5662200
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2292 passed, 2 warnings in 1947.21s (0:32:27)
exit 0
Sun Oct 11 13:17:43 UTC 2026
```
### Image hashes
```
head:    2c82b6c
repo:    84da618adda8f2fb06a57a85fc6d5ea7a31e87dc84654a1ec93bffece8dd8acc  -
runtime: 84da618adda8f2fb06a57a85fc6d5ea7a31e87dc84654a1ec93bffece8dd8acc  -
test:    84da618adda8f2fb06a57a85fc6d5ea7a31e87dc84654a1ec93bffece8dd8acc  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
/app/hypocurate/web/glossary.json

```
### The new tests against main's package (failed before)
```
E         {'queued': 'none'} != {'queued': 'queued (not started)'}
E         {'waiting': 'none'} != {'waiting': 'waiting at the rules lock'}
E         Use -v to get more diff

pkg/tests/test_cli_step9b.py:110: AssertionError
=========================== short test summary info ============================
FAILED pkg/tests/test_confirmation_step10.py::test_a_matching_fingerprint_confirms
FAILED pkg/tests/test_web_isolation.py::test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner
FAILED pkg/tests/test_confirmation_step10.py::test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item
FAILED pkg/tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded[]
FAILED pkg/tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded[not hex]
FAILED pkg/tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded[0000000000000000000000000000000000000000000000000000000000000000]
FAILED pkg/tests/test_confirmation_step10.py::test_content_that_changed_after_it_was_shown_is_refused
FAILED pkg/tests/test_confirmation_step10.py::test_the_label_once_confirmed_follows_the_readings_own_wording
FAILED pkg/tests/test_confirmation_step10.py::test_the_text_shown_says_informative_groups_the_label_now_and_once_confirmed_and_counts_calls_rightly
FAILED pkg/tests/test_worker.py::test_the_worker_logs_each_claim_and_each_finished_run
FAILED pkg/tests/test_cli_step9b.py::test_queue_says_where_a_waiting_or_queued_run_is_never_none
ERROR pkg/tests/test_web_runs.py - ImportError while importing test module '/...
ERROR pkg/tests/test_web_state.py - ImportError while importing test module '...
ERROR pkg/tests/test_web_textfmt.py - ImportError while importing test module...
ERROR pkg/tests/test_reading_step10.py - ImportError while importing test mod...
11 failed, 4 passed, 4 errors in 72.19s (0:01:12)
```
### Reference dumps against main
```
== fixed_plan: 0 differing leaves
== planner_fcc: 0 differing leaves
== planner_bcc: 0 differing leaves
== partly_original: 0 differing leaves
== narrower: 0 differing leaves

```
### The browser check of polling (Playwright, outside the suite)
```
{"state_requests_before_end": 4, "seconds_open_to_end": 20.5, "state_requests_in_20s_after_end": 0, "state_text": "Status i\n\nfailed\n\nFailed: cancelled: cancelled by Grace Reviewer before it started", "poll_attribute_after_end": null}

```

## 6. Scratch scripts

### packet/packet.py
```python
"""Scratch: builds docs/reviews/step10a_review_packet.md from files on disk (summary, the full diff against main
without the screenshots and the lock's hash lines, test outputs, the comparisons)."""
import pathlib, subprocess
R = pathlib.Path("/workspaces/hypocurate"); W = pathlib.Path.home() / "hc-work/step10a"
def sh(*a): return subprocess.run(a, cwd=R, capture_output=True, text=True, check=True).stdout
def tail(p, n=6): return "\n".join(pathlib.Path(p).read_text(encoding="utf-8").splitlines()[-n:])
out = ["# Build step 10a — review packet", "",
       f"Branch `step-10a-run-pages`, head `{sh('git','rev-parse','--short','HEAD').strip()}`, against `main` `ba83c3d`. "
       "Generated from the files on disk by a script (quoted at the end).", "",
       "## 1. The summary", "", (R / "docs/reviews/step10a_summary.md").read_text(encoding="utf-8"), "",
       "## 2. Commits", "", "```", sh("git", "log", "--oneline", "main..HEAD"), "```", "",
       "## 3. Files changed", "", "```", sh("git", "diff", "--stat", "main...HEAD"), "```", "",
       "## 4. The full diff (screenshots left out; the lock's new hash lines shown, others unchanged)", "",
       "```diff", sh("git", "diff", "main...HEAD", "--", ".", ":(exclude)docs/reviews/step10a_screenshots",
                     ":(exclude)docs/reviews/step10a_summary.md", ":(exclude)docs/reviews/step10a_review_packet.md"), "```", "",
       "## 5. Test output", "",
       "### main, serial with timings (a0)", "```", tail(W / "durations_main.log", 3), "```",
       "### 4 workers (first parallel run)", "```", tail(W / "parallel1.log", 4), "```",
       "### 2 workers (second parallel run)", "```", tail(W / "parallel2.log", 4), "```",
       "### Final serial and parallel on 2c82b6c", "```", tail(W / "final_serial.log", 2), tail(W / "final_parallel.log", 2), "```",
       "### Serial against parallel (JUnit)", "```",
       subprocess.run([str(R / ".venv/bin/python"), str(W / "compare_junit.py"), str(W / "final_serial.xml"),
                       str(W / "final_parallel.xml")], capture_output=True, text=True).stdout, "```",
       "### Local whole suite on 5662200", "```", tail(W / "final2_local.log", 2), "```",
       "### Local whole suite on the final head (serial)", "```", tail(W / "final3_local.log", 2), "```",
       "### The test image's suite on 5662200", "```", tail(W / "final2_image.log", 4), "```",
       "### Image hashes", "```", (W / "image_hashes.txt").read_text(encoding="utf-8"), "```",
       "### The new tests against main's package (failed before)", "```", tail(W / "before/before.log", 22), "```",
       "### Reference dumps against main", "```", (W / "refdump/compare_output.txt").read_text(encoding="utf-8"), "```",
       "### The browser check of polling (Playwright, outside the suite)", "```", (W / "shots/poll_result.txt").read_text(encoding="utf-8"), "```", "",
       "## 6. Scratch scripts", ""]
for name in ("packet/packet.py", "compare_junit.py", "register_entries.py", "register_note.py", "shots/world.py",
             "shots/shots.py", "shots/poll_check.py", "shots/poll_host.py"):
    out += [f"### {name}", "```python", (W / name).read_text(encoding="utf-8"), "```", ""]
(R / "docs/reviews/step10a_review_packet.md").write_text("\n".join(out), encoding="utf-8")
print("written")

```

### compare_junit.py
```python
"""Scratch (not committed): serial against parallel, from JUnit XML: the same test ids, and the same outcome for each."""
import sys, xml.etree.ElementTree as ET
def outcomes(path):
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        tid = f"{tc.get('classname')}::{tc.get('name')}"
        kind = "passed"
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                kind = child.tag
        assert tid not in out, f"duplicate id {tid}"
        out[tid] = kind
    return out
a, b = outcomes(sys.argv[1]), outcomes(sys.argv[2])
print(f"serial: {len(a)} tests {dict((k, list(a.values()).count(k)) for k in set(a.values()))}")
print(f"parallel: {len(b)} tests {dict((k, list(b.values()).count(k)) for k in set(b.values()))}")
print("only serial:", sorted(set(a) - set(b))[:20])
print("only parallel:", sorted(set(b) - set(a))[:20])
diff = sorted(t for t in set(a) & set(b) if a[t] != b[t])
print("different outcome:", diff[:20])
print("IDENTICAL" if not (set(a) ^ set(b)) and not diff else "DIFFERENT")

```

### register_entries.py
```python
"""Scratch: the step 10a register entries (Claude Code's drafts; the owner reviews them in the morning, 2026-10-11)."""
import json
import pathlib

p = pathlib.Path("/workspaces/hypocurate/hypocurate/assumptions.json")
r = json.loads(p.read_text(encoding="utf-8"))
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-11"}
NR = {"status": "not_reviewed", "name": None, "date": None}
PLAN = ("Step 10 plan approved by the owner on 2026-10-11, with additions 1-6, the answers at the screenshot review and "
        "the overnight answers (quoted in docs/reviews/step10a_summary.md).")
DRAFT = "Wording drafted by Claude Code for the owner's review (2026-10-11)."
W = "tests/test_web_runs.py::"


def entry(key, name, statement, value, unit, affects, reason, settings, tests, category="operational"):
    return {"key": key, "name": name, "state": "in_force", "statement": statement,
            "value": {"text": value, "unit": unit}, "category": category, "affects": affects, "reason": reason,
            "evidence": [PLAN], "decided": OWNER, "expert_review": NR, "sensitivity": None,
            "applied": {"status": "yes", "settings": settings, "note": None}, "tests": tests, "history": [],
            "notes": [DRAFT]}


new = [
    entry("signed_in_name", "The signed-in person's name, fixed for the session",
          "The sign-in form takes the shared password and the person's name (1 to 200 characters, spaces collapsed). "
          "The name is kept in the signed session cookie and is the name recorded by every action that names a person "
          "on the website (in step 10a: confirming the question as tested and cancelling a run). It cannot change "
          "within a session: signing in again while signed in is refused, so a new name means signing out and in "
          "again. A session signed before step 10a, which has no name, may read but not act. Nothing proves who typed "
          "the name: under the one shared password it records who said they acted, as --by does on the command line.",
          "name at sign-in; 1-200 characters; fixed for the session", None,
          "Every confirmation and cancellation made on the website.",
          "Owner's answer 1 to the step 10 plan (name at sign-in) and addition 3 (the name cannot change within a "
          "session).",
          [{"ref": "python:hypocurate.web.security:NAME_MAX", "equals": 200}],
          [W + "test_signing_in_needs_a_name_and_keeps_it_with_a_token",
           W + "test_the_name_cannot_change_within_a_session", W + "test_a_session_without_a_name_cannot_act",
           W + "test_cancel_records_the_signed_in_name",
           "tests/test_login.py::test_cookie_holds_only_the_signed_in_flag_the_name_and_the_form_token"]),
    entry("csrf_tokens", "Every website action that writes carries the session's token",
          "A random token (32 bytes, URL-safe) is made at sign-in and kept in the signed session cookie. Every form "
          "that writes carries it in the hidden field csrf_token, and the server compares it in constant time before "
          "doing anything; a request without the session's token, with an empty one or with another session's, is "
          "refused with 403 and writes nothing. In step 10a the writes are confirm and cancel; dispatch, dispatch "
          "again, domain confirmation and source registration (step 10b) will carry it too. Sign-out writes nothing "
          "and carries none. The cookie is also SameSite=Lax.",
          "a token per session, checked on every write", None, "Every website action that writes.",
          "Owner's addition 1 to the step 10 plan.",
          [{"ref": "python:hypocurate.web.security:CSRF_FIELD", "equals": "csrf_token"}],
          [W + "test_a_write_without_the_sessions_token_is_refused_and_writes_nothing",
           W + "test_another_sessions_token_is_refused"]),
    entry("confirmation_shown_fingerprint", "A confirmation is of the content the page showed",
          "The confirmation page sends back the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8) of the "
          "content it displayed. confirmation.confirm compares it, inside the transaction that records the "
          "confirmation, with the run's current content, and refuses any difference as content_changed (as it "
          "refuses other content given whole by the command line). A page that sends no fingerprint is refused the "
          "same way. The website is the second caller of confirm, after the command line; confirm still takes one "
          "run and one name.",
          "SHA-256 of the canonical content", None, "Every confirmation made on the website.",
          "Owner's addition 2 to the step 10 plan.",
          [{"ref": "python:hypocurate.pipeline.confirmation:content_fingerprint"}],
          ["tests/test_confirmation_step10.py::test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_"
           "changes_with_any_item",
           "tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_"
           "recorded",
           "tests/test_confirmation_step10.py::test_content_that_changed_after_it_was_shown_is_refused",
           W + "test_a_confirmation_of_content_other_than_what_was_shown_is_refused",
           W + "test_a_confirmation_without_the_shown_contents_fingerprint_is_refused",
           "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself"]),
    entry("evidence_dial", "The evidence-level dial",
          "The run viewer shows the run's evidence level (set by code; it never changes the verdict) as a half circle "
          "of six separate segments in one blue that darkens with the level (never red to green), with a needle on "
          "the run's level and its segment outlined, and the words \"Level n of 6: <short label>\". The short labels: "
          "6 tested answer, 5 exploratory answer, 4 coefficient only, 3 below the minimums, 2 no coefficient fitted, "
          "1 nothing tested. The verdict is shown beside the dial, never in it. A marked test run's dial is hatched, "
          "with a \"test run\" badge. The runs list shows a small dial; a run not completed shows no level (\"failed: "
          "no evidence level\" for a failed run). The dial holds no text: every word is HTML beside it.",
          "six segments; one hue; the labels stated", None, "The run viewer and the runs list.",
          "Owner's step 10 brief; answer 2 (the draft labels); review of the screenshots, 2026-10-11 (no long wording "
          "under the dial; failed runs).",
          [{"ref": "python:hypocurate.web.dial:SHADES",
            "equals": ["#dde6f3", "#b9cbe7", "#8ea9d6", "#6286c2", "#3a63a6", "#1d3f78"]},
           {"ref": "python:hypocurate.pipeline.statistics:EVIDENCE_SHORT"},
           {"ref": "python:hypocurate.pipeline.run_view:FAILED_NO_LEVEL", "equals": "failed: no evidence level"}],
          [W + "test_the_short_labels_are_the_owners_set", W + "test_the_dial_has_one_hue_that_darkens_with_the_level",
           W + "test_the_needle_points_at_the_runs_level",
           W + "test_the_dial_shows_the_level_and_label_with_the_verdict_beside_it_not_in_it",
           W + "test_a_marked_test_runs_dial_is_hatched_with_a_badge",
           W + "test_the_runs_list_shows_a_small_dial_for_every_run",
           W + "test_the_large_dial_shows_the_level_label_without_the_long_wording"]),
    entry("sensitivity_set_display_names", "Sensitivity sets shown by name, never by internal key",
          "The screens name each sensitivity set in words and describe its one change for readers; the internal keys "
          "are never shown. The ninth set keeps its approved name, \"without the group with the largest share of "
          "slope information\", with the eligibility code's description. The survivor set's description is the "
          "owner's: \"Conflicting values, left out of the main result, are included once each, using the survivor's "
          "value.\"",
          "display names and descriptions", None, "The run viewer's sensitivity table.",
          "Owner's step 10 brief (display names, never internal names) and review of the screenshots (the survivor "
          "set's wording).",
          [{"ref": "python:hypocurate.pipeline.run_view:SET_DISPLAY_NAMES"},
           {"ref": "python:hypocurate.pipeline.run_view:SET_DESCRIPTIONS"}],
          [W + "test_sensitivity_sets_are_shown_by_display_name_never_by_internal_name",
           W + "test_every_sensitivity_set_has_a_display_name_and_a_description",
           W + "test_the_survivor_set_says_that_conflicting_values_are_normally_left_out"]),
    entry("live_run_state", "An open run's page updates itself and stops when the run ends",
          "While a run is queued, waiting or running, its page asks for the run's state every 5 seconds "
          "(static/poll.js, a script of our own, not HTMX). The server decides when this ends: an open run's state "
          "carries its own address, an ended run's (completed or failed) carries none; the script asks again only "
          "when the state it received carries an address, and on an ended state reloads the page once to show the "
          "results. Every state read is read-only; the web service never claims a run or runs a stage, so closing the "
          "browser or restarting the web service never affects a run (criterion 14.4).",
          "every 5 s while the run is open", "seconds", "The run viewer.",
          "Owner's step 10 brief (the page updates by itself) and answer of 2026-10-11 (a script of our own; polling "
          "stops at an end state, with a test).",
          [{"ref": "python:hypocurate.pipeline.run_view:OPEN_STATUSES", "equals": ["queued", "waiting", "running"]},
           {"ref": "file:hypocurate/web/static/poll.js:var INTERVAL_MS = 5000;"}],
          ["tests/test_web_state.py::test_an_open_runs_page_polls_its_own_state_and_an_ended_runs_page_does_not",
           "tests/test_web_state.py::test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended",
           "tests/test_web_state.py::test_the_script_asks_again_only_when_the_state_it_received_carries_an_address",
           "tests/test_web_state.py::test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart",
           "tests/test_web_isolation.py::test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner"]),
    entry("screen_text", "How text is shown on the screens",
          "No text on any screen is smaller than 12 px (sizes in rem, at least 0.75rem). The Analyst's text is shown in "
          "a small safe subset of Markdown (paragraphs, bold, bulleted and numbered lists, simple tables), with "
          "everything the model wrote escaped first. Exponents in units are written as superscripts on the screens "
          "only; stored text and the command line keep \"^\".",
          "at least 12 px; a safe subset; superscripts on screens", None, "Every screen.",
          "Owner's addition 6 to the step 10 plan and review of the screenshots (2026-10-11).",
          [{"ref": "python:hypocurate.web.textfmt:model_text"}, {"ref": "python:hypocurate.web.textfmt:units"}],
          [W + "test_no_text_on_any_screen_is_smaller_than_12px",
           "tests/test_web_textfmt.py::test_bold_lists_and_a_simple_table_are_rendered_and_no_raw_signs_remain",
           "tests/test_web_textfmt.py::test_everything_the_model_writes_is_escaped",
           W + "test_units_are_written_with_a_real_superscript_on_the_screens"]),
    entry("parallel_suite", "The regression suite runs in parallel",
          "The suite runs with pytest-xdist on 4 workers (-n 4 --dist loadgroup, pyproject.toml). Every test that "
          "needs tables has a database of its own with a random name, made from a template each worker makes for "
          "itself; the database at DATABASE_URL is opened only by the read-only health tests. Test files that measure "
          "time, race threads or processes, or send signals form one group that runs on a single worker, one test "
          "after another (tests/conftest.py SERIAL_FILES; a group never deselects a test). A test that fails even once "
          "in parallel and passes alone is added to that group, never re-run (no rerun plugin or retry flag); if more "
          "than three files would need it, the suite drops to 2 workers. The test image still runs plain `pytest -q`.",
          "4 workers; one serial group", None, "Every run of the regression suite, locally and on GitHub.",
          "The GitHub suite step took about 32 of the job's 40 minutes; owner's answer 4 to the step 10 plan with two "
          "conditions, and the overnight answers of 2026-10-11.",
          [{"ref": "file:pyproject.toml:-n 4 --dist loadgroup"},
           {"ref": "file:tests/conftest.py:SERIAL_FILES = frozenset({"}],
          ["tests/test_parallel_isolation.py::test_databases_are_made_only_by_conftest_with_random_names",
           "tests/test_parallel_isolation.py::test_only_the_read_only_health_tests_open_the_shared_database",
           "tests/test_parallel_isolation.py::test_each_xdist_worker_has_its_own_template",
           "tests/test_parallel_isolation.py::test_the_serial_group_names_only_existing_test_files"]),
]
keys = {e["key"] for e in r}
for e in new:
    assert e["key"] not in keys, e["key"]
r.extend(new)
p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(r))

```

### register_note.py
```python
"""Scratch: adds the owner's note (2026-10-11) to the register entry 'results_statement'."""
import json, pathlib
p = pathlib.Path("/workspaces/hypocurate/hypocurate/assumptions.json")
r = json.loads(p.read_text(encoding="utf-8"))
e = next(x for x in r if x["key"] == "results_statement")
note = ("2026-10-11 (step 10a; owner's decision to keep format 2): format 2's provenance label of the question as "
        "tested was corrected for Planner runs that predate confirmation. Such a run, whose plan was locked before "
        "confirmations existed (migration 0007) and which stored no reading with its Planner stage, was labelled "
        "\"the fixed reference plan; not read from the claim\"; it now reads \"the Planner's reading of the claim; "
        "not verified by code; this run predates confirmation\". No run after confirmations existed is affected. "
        "In the development database, runs 1 and 2 are the only ones changed.")
assert note not in e["notes"]
e["notes"].append(note)
p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(e["notes"]))

```

### shots/world.py
```python
"""Scratch (not committed): a copy of the local dev database for the step 10a screenshots, plus three runs through
the local stub: a coefficient-only run (Texas A&M alone, use what is available), a marked test run (fixed plan) and a
waiting Planner run, and one queued run. Run with PYTHONPATH=tests, DATABASE_URL = the dev database."""
import os, sys
from sqlalchemy import make_url, text
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
import stub_provider as sp
import test_orchestrator as to

dev = os.environ["DATABASE_URL"]
target = sys.argv[1]
admin = make_engine(dev).execution_options(isolation_level="AUTOCOMMIT")
src = make_url(dev).database
with admin.connect() as c:
    c.execute(text(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)'))
    c.execute(text(f'CREATE DATABASE "{target}" TEMPLATE "{src}"'))
admin.dispose()
url = make_url(dev).set(database=target).render_as_string(hide_password=False)
e = make_engine(url)
stub = sp.StubProvider()
opts = sp.client_options(stub)
out = {}
try:
    stub.respond(to.responder())
    q = queries.create(e, to.FCC_CLAIM, ("tamu_fcc",), sufficiency="use_available")
    queries.submit(e, q.version_id); queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(e, q.version_id, fixed_plan=True)
    out["coefficient_only"] = (rid, orchestrator.run(e, rid, client_options=opts).status)
    q = queries.create(e, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(e, q.version_id); queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(e, q.version_id, fixed_plan=True, constructed_test_data=True)
    out["test_run"] = (rid, orchestrator.run(e, rid, client_options=opts).status)
    stub.respond(to.responder(to.planner_body()))
    q = queries.create(e, to.FCC_CLAIM, ("mpea", "tamu_fcc"))
    queries.submit(e, q.version_id); queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(e, q.version_id)
    out["waiting"] = (rid, orchestrator.run(e, rid, client_options=opts).status)
    q = queries.create(e, "In FCC multi-principal-element alloys, finer grains give a higher yield strength", ("mpea", "tamu_fcc"))
    queries.submit(e, q.version_id); queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    out["queued"] = (queries.dispatch(e, q.version_id, fixed_plan=True), "queued")
finally:
    stub.close()
print(out)

```

### shots/shots.py
```python
"""Scratch (not committed): screenshots of the step 10a pages, taken by headless Chromium (Playwright) in a throwaway
container. Argument: a JSON of run ids. Writes PNGs to /w/out."""
import json, os, sys
from playwright.sync_api import sync_playwright
base = os.environ.get("BASE", "http://127.0.0.1:8010")
ids = json.loads(sys.argv[1])
os.makedirs("/w/out", exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    pg = ctx.new_page()
    pg.goto(base + "/login")
    pg.screenshot(path="/w/out/00_sign_in.png", full_page=True)
    pg.fill("#name", "Ada Reviewer"); pg.fill("#password", os.environ["PW"]); pg.click("button[type=submit]")
    shots = [("01_runs_list", "/runs"), ("02_run_sufficient", f"/runs/{ids['sufficient']}"),
             ("03_run_insufficient", f"/runs/{ids['insufficient']}"),
             ("04_run_coefficient_only", f"/runs/{ids['coefficient_only']}"),
             ("05_run_test_run", f"/runs/{ids['test_run']}"), ("06_run_waiting", f"/runs/{ids['waiting']}"),
             ("07_confirmation", f"/runs/{ids['waiting']}/confirm"), ("08_run_queued", f"/runs/{ids['queued']}")]
    for name, path in shots:
        pg.goto(base + path)
        pg.screenshot(path=f"/w/out/{name}.png", full_page=True)
    pg.goto(base + f"/runs/{ids['sufficient']}")
    pg.focus(".statement aside .info-button")
    pg.screenshot(path="/w/out/09_info_popup_open.png", clip={"x": 0, "y": 0, "width": 1280, "height": 700})
    m = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    mp = m.new_page()
    mp.goto(base + "/login"); mp.fill("#name", "Ada Reviewer"); mp.fill("#password", os.environ["PW"]); mp.click("button[type=submit]")
    mp.goto(base + f"/runs/{ids['sufficient']}")
    mp.screenshot(path="/w/out/10_run_sufficient_phone.png", full_page=True)
    b.close()
print("done")

```

### shots/poll_check.py
```python
"""Scratch (not committed), runs in the screenshot container: opens a queued run's page, records every request for its
state, waits until the page shows the run ended (another session cancels it), then watches 20 s more."""
import json, os, sys, time
from playwright.sync_api import sync_playwright
base, rid = "http://127.0.0.1:8010", int(sys.argv[1])
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    seen = []
    pg.on("request", lambda r: seen.append((round(time.time(), 1), r.url)) if "/state" in r.url else None)
    pg.goto(base + "/login"); pg.fill("#name", "Ada Reviewer"); pg.fill("#password", os.environ["PW"])
    pg.click("button[type=submit]")
    pg.goto(base + f"/runs/{rid}")
    opened = time.time()
    pg.wait_for_selector("#run-state[data-ended='true']", timeout=120000)
    ended = time.time()
    n_at_end = len(seen)
    time.sleep(20)
    text = pg.inner_text("#run-state")
    print(json.dumps({"state_requests_before_end": n_at_end, "seconds_open_to_end": round(ended - opened, 1),
                      "state_requests_in_20s_after_end": len(seen) - n_at_end, "state_text": text[:160],
                      "poll_attribute_after_end": pg.get_attribute("#run-state", "data-poll")}))
    pg.screenshot(path="/w/out/11_after_end_failed.png", full_page=True)
    b.close()

```

### shots/poll_host.py
```python
"""Scratch (not committed): dispatches a queued run on the screenshot database, starts poll_check.py in a throwaway
container, cancels the run 15 s later from another session, and prints the browser's report."""
import os, subprocess, sys, time
from sqlalchemy import make_url
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
url = make_url(os.environ["DATABASE_URL"]).set(database="hc_shots_10a").render_as_string(hide_password=False)
e = make_engine(url)
q = queries.create(e, "In FCC multi-principal-element alloys, yield strength rises as grain size falls (poll check)",
                   ("mpea", "tamu_fcc"))
queries.submit(e, q.version_id); queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
rid = queries.dispatch(e, q.version_id, fixed_plan=True)
here = os.path.dirname(os.path.abspath(__file__))
proc = subprocess.Popen(["docker", "run", "--rm", "--network", "host", "-v", f"{here}:/w", "-e", f"PW={os.environ['PW']}",
                         "python:3.14-slim", "sh", "-c",
                         "pip install -q playwright >/dev/null 2>&1 && playwright install --with-deps --only-shell "
                         f"chromium >/tmp/i.log 2>&1; python /w/poll_check.py {rid}; chown -R {os.getuid()}:{os.getgid()} /w/out"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
# wait until the browser has made a few state requests (the container installs Chromium first)
deadline = time.time() + 600
while time.time() < deadline:
    with open(os.path.join(here, "web.log")) as f:
        if f.read().count(f"/runs/{rid}/state") >= 3:
            break
    time.sleep(1)
print("cancelling run", rid, flush=True)
queries.cancel(e, rid, by="Grace Reviewer")
out, _ = proc.communicate(timeout=600)
print(out.strip().splitlines()[-1])

```
