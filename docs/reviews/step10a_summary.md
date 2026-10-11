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
