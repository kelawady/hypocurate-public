# Build step 10b — summary for review

Date: 2026-10-11. Branch: `step-10b-screens` (from `main` at `7620f77`, step 10a merged). **Status: fix round 1 built (ChatGPT's three findings, accepted by the owner); pushed once for the re-check, not merged; register entries waiting for the owner's approval.** The fix round is the last section.

PRD Section 15, step 10 ("Website screens"), second part. 10a (run pages) is merged and live. 10b builds the rest of PRD 9 and 11:
- the query pages;
- the Critic's flags;
- data sources and agents;
- the plot and the workbook;
- the Help page.

The plan, with every owner decision, is in the step 10 plan file (quoted in the packet).

## Safeguard changes (second-model review before any merge; CLAUDE.md "How we work" item 5)

1. **New write paths on the website, each with the session's CSRF token:**
   - new query, edit, submit;
   - return for edits;
   - dispatch, dispatch again;
   - registering a source (the owner's addition 4: a safeguard).

   Every write goes through the pipeline's own functions (`pipeline.queries`, `sources.versions.register`). A request without the session's token is refused with 403 and writes nothing; a test covers each route.
2. **New functions in `pipeline/queries.py`:** `update_draft` (a draft only), `new_version` (only after a return), `return_for_edits` (a named reviewer and a comment), and `confirm_domain(where=)`. The database's own version rules (0001) are unchanged and back each one.
3. **`reading.provenance`:** the Plan column's words, from what is stored only.

**Not changed:** `render.yaml`, the Dockerfile, Compose, `.github/workflows/`, the locks, the migrations (schema stays 0008), the access layer and its allow-lists, the orchestrator, the worker, recovery, the statistics.

## What was built (each commit)

| Commit | What |
|---|---|
| `1ebd31c` | b1: queries list, new query, query page, edit (draft in place; returned → next version), review and dispatch (domain confirmed under the signed-in name, ceiling, return with a comment, the queue), dispatch again; the runs list's Plan column |
| `22e456e` | b3: the plot; the edit form keeps a version's own choices; screenshots |
| `80d58b2`, `25a3ee5` | The owner's screenshot review: markers fixed per source; axes limited to the records in the fit; a narrow drawing for phones; the phone menu wraps; short source names in the list; "used in the fit (coefficient only…)"; the narrower question's Plan wording |
| `c1d2b3c` | A failed run explained in plain English first, the codes second; "not searched (the run ended first)" (owner's request) |
| `c7a6371` | Each sensitivity set says what it changes compared with the main result; "atomic percent (at.%)" once (owner's request) |
| `c8450c7` | b2: the Critic's flags with the advice label; data sources with registration and the connection test; read-only agent pages |
| `fa462b1` | b4: the workbook and records CSV, built on request; CLI `export` |
| `23eb179` | b5: the Help page; every glossary entry has a button |
| `ceccc3d` | Register; a marked test run labelled in the queries list and the run queue |

### The owner's decisions in 10b (2026-10-11)

**The go:** "Go for step 10b, as planned and approved, on a new branch from main", with:
- a screenshot stop after the query pages and the plot;
- one push per review round;
- a warning before cutting the help page or the agent pages (neither was cut).

**The plot (answer):** raw values with one line per alloy at the stored slope.

**Plan column (request):** "fixed reference plan", "Planner's reading", "Planner's reading, confirmed by <name>", "Planner's reading; predates confirmation", from the stored plan source, readable on a phone. After the review: "narrower question, built by code from run N".

**Screenshot review:** the query pages and the Plan column were approved, with these changes:
- plot markers fixed per source, with a test on every point;
- axes limited, with a count of the records outside;
- the plot and the menu fit a phone;
- short source names in the list;
- the coefficient-only legend wording;
- the narrower Plan wording.

**Requests during the build:**
- plain-English failures, with the owner's run 2 example word for word;
- each sensitivity set says what it changes compared with the main result.

## The screens

- **Queries** (PRD 9.1):
  - number, created, domain, hypothesis, short sources, status, outcome, cost, and the action (Edit, Review, Open run);
  - pages of 50 by an ID cursor;
  - a marked test run labelled.
- **New query and edit** (9.2):
  - hypothesis, domain (unsupported ones marked), sources with their kind of data, how much data is enough, note;
  - save draft or submit;
  - a returned query is saved as its next version.
- **Review and dispatch** (9.3):
  - the submitted queries on the left;
  - the domain confirmed or changed, under the signed-in name;
  - the sufficiency option, the sources, the agent settings versions, the caps and the note;
  - dispatch with an optional ceiling, or return for edits with a comment;
  - the run queue below.
  - Refusals appear in code's words: the monthly cap, constructed test data, a domain not yet supported.
- **The run page gains:**
  - the plot;
  - the Critic's flags under the advice label;
  - the commentary section (none in sprint 1);
  - the terms of the record of statistical significance with their buttons;
  - the workbook and CSV downloads;
  - plain failures.
- **Data sources** (9.6): registered sources and their facts, code-defined sources to register, and the connection test.
- **Agents** (9.5): one read-only page per role, with "Fixed in code" taken from the access layer's allow-lists and each role's own output description.
- **Help** (9.7): every explanation by screen, searchable.

## The plot

- **Built on request from stored rows**, never stored. Each record's own outcome is plotted against grain size^-1/2.
- **Markers:** a fixed shape per source; filled for a record in the test, a cross for sensitivity-only, hollow for not used.
- **Lines:** one per alloy over its own grain sizes, at the stored slope; none, with the reason, below the minimums or with no coefficient.
- **The check that matters:** the plotted "used" points, refitted test-side (least squares with one baseline per alloy), give back the stored slope within 1e-9 (97 records, 22 alloys). So the plot shows the fit's own records and alloys.
- It states its format and the code version that built it.

## Tests

- **The whole suite:** 2,391 tests (2,302 on `main`), all passing locally on `ceccc3d`, serially, in 38 min 04 s.
- **New test files:**
  - `test_web_queries.py`;
  - `test_plot.py`;
  - `test_failure_words.py`;
  - `test_web_catalog.py`;
  - `test_workbook.py`;
  - `test_help.py`;
  - new tests in `test_web_runs.py`.
- **Failed before** (the new test files run against `main`'s package, `7620f77`):
  - **5 files cannot import there:** `test_web_queries`, `test_plot`, `test_failure_words`, `test_web_catalog`, `test_workbook`.
  - **`test_help.py`:** 3 failed. The 2 that pass are guards that also hold on `main`: no template repeats an explanation, and `/help` needs the login.

**Changed tests, and why** (none weakened, none removed):

| Test | Change | Reason |
|---|---|---|
| `test_plot.py`: three of its own tests (written in 10b before the review) | count only drawn markers; both drawings; the wide drawing's min-width | the owner's review (limited axes, phone drawing) |
| `test_web_runs.py::test_a_narrower_questions_run_says_so` (written in 10b) | the owner's wording with the original run | the owner's review |
| `test_web_state.py::test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended` (10a) | expects the plain words and "Technical detail: cancelled." | the owner's request (plain failures) |
| `test_assumptions.py::PARTLY` and `::test_the_step_6_decisions_carry_the_owners_wording` | `constructed_test_runs` is fully applied by step 10 (it pinned "pending in step 10") | its label is now on every screen and list |

**Mutation checks:** 9 faults, all caught, each by the test written for it; the control run is clean (128 tests). The faults:
- k1–k3: CSRF removed from new query, registration, review;
- k4: markers by order;
- k5: the attempts' count;
- k6: the narrower Plan wording;
- k7: the draft guard;
- k8: full names in the list;
- k9: the workbook's version line.

**Reference runs:** byte-identical to `main` in all six dumps.

**Images:**
- **Rebuilt on `ceccc3d`:** the package's SHA-256 is the same in the repository, the runtime image and the test image; the test image's `tests/` equals the repository's; the runtime image holds no `tests/` or `docs/`; the guard checks pass in it.
- **The suite in the test image:** 1 failed and 2,390 passed (42 min 15 s).
  - **The failure:** `test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance` (a 9b test) released `child_stuck` instead of `finished`. It gives the worker's child a 6-second stall allowance, and the child was judged stalled.
  - **The same test** failed in 10a under parallel load (locally on 4 workers, and on GitHub on 2), which is why the parallel suite was taken out. This time it failed in a serial run.
  - **Not caused by 10b:** the worker's child imports none of 10b's new modules (checked).
  - **Not re-run to hide it.** It passed in the local run of the same head. It is a timing-sensitive test that the image's slower run can fail; how to handle it is the owner's decision.

**GitHub run:** run 38177624362 on `a25caf0`, green; the suite step took 26 min 35 s (job 27 min 50 s).

## Register

**166 entries.** 9 new, each with the owner's decisions of 2026-10-11; the wording is Claude Code's draft, for the owner's review:
- `query_versions_on_the_website`;
- `queries_list`;
- `runs_list_plan_column`;
- `failure_explanations`;
- `run_plot`;
- `run_workbook`;
- `web_source_registration`;
- `agent_pages`;
- `help_page`.

**Changed entries:**
- `sensitivity_set_display_names`: reworded (its earlier wording in its history).
- `constructed_test_runs`: fully applied.

## What 10b does not do or claim

- **Registering a source** covers sources defined in code. A person's own source from a form needs an adapter first; it is for a later sprint.
- **Marking a run as a test with constructed data** stays on the command line. The website shows the refusal with its reason.
- **The agent pages:**
  - "May call" and "may not do" are fixed sentences summarizing CLAUDE.md's rules, not read from code;
  - the settings shown are the latest stored version, and a dispatch records the code's current settings.
- **The workbook's cells** are the same for the same stored rows; its zip timestamps are the spreadsheet library's, so the bytes may differ.
- **The phone layout** is designed for screens at least 360 px wide.
- **Left for step 11:**
  - deployment and the 14.7 walk-through;
  - the audit-log view;
  - how evaluation runs are confirmed;
  - the analysis-specific seed;
  - the suite's speed;
  - the API key and Blueprint sync.

## PRD corrections and clarifications (for the next PRD update)

1. **PRD 9.1:** short source names in the list; a cursor for pages; the Plan column.
2. **PRD 9.4:** the plot's form (the owner's answer); plain-English failures with "Technical detail".
3. **PRD 9.6:** registration covers code-defined sources.
4. **PRD 11 and 6:** the workbook and plot are built on request; the `artifact` table is unused in sprint 1.

## Questions for the reviewer

1. Can any website path write except through the pipeline's functions, or without the session's token?
2. Does any page or download compute a result rather than show code's stored result (the plot's lines in particular)?
3. Is any failure explanation or Plan wording stronger than what is stored supports?
4. Can a query version change in a way the database's rules or PRD 9.2 do not allow?
5. Is any claim here, in the code or in the register stronger than the code supports?

## Fix round 1 (ChatGPT's review of 2026-10-11: "not safe to merge")

The review is saved verbatim as `docs/reviews/step10b_review_chatgpt.md`. The owner accepted all three findings, with
the instruction: "Fix them on step-10b-screens, each with a failing test first, then write a fix packet for a short
re-check. Do not merge." The fix packet is `docs/reviews/step10b_fix_packet.md`.

**The owner's approvals during the round (2026-10-12):**
- keep the extra rows in the workbook's run summary sheet (note, review comment, who did what);
- the changed `confirm` parameter test, listed below as a changed test;
- command-line actions without a name are stored as such.

### Finding 1: act only on the version shown

**The bug:** the review page's Dispatch and Return used the query's latest version at the time of the click, so an
old tab could dispatch a version it never showed. An old edit form could also overwrite a newer draft.

**The fix:**
- **What the forms send:** the edit form, both review forms and Dispatch again send the version they displayed and a
  fingerprint of its content (`queries.version_fingerprint`). That is a SHA-256 of the canonical JSON of its query,
  number, status, hypothesis, domains, option, note, sources and review comment.
- **Read from the page's own snapshot:** the id and fingerprint come from the same snapshot as the content the page
  shows (`query_view.query_page`). `review_page` no longer reads the version a second time.
- **Checked under the version lock:** every write (`update_draft`, `new_version`, `return_for_edits`,
  `confirm_domain`, `dispatch`, `dispatch_again`) compares both with the stored version inside its own transaction.
  A difference is refused with the owner's words: "This query has changed since you opened it; reload the page". On
  the website both are required, so a form that sends neither is refused the same way.
- **Confirm, then dispatch:** the review's dispatch confirms the domain first, then dispatches with the fingerprint
  that confirmation returned. A change between the two transactions is therefore refused too.
- **An old edit form after a refusal:** it keeps the version it showed, so only a reload acts on the newer one.
- **Saving and submitting** from one form is now one transaction (`submit=True`).
- **The command line** names the version it acts on and is not checked this way.

### Finding 2: no formulas in exports

- **The workbook:** every text cell is written as a string cell (`workbook._append`), whatever it begins with.
- **The CSV:** text beginning with =, +, -, @, a tab or a carriage return gets a leading apostrophe
  (`workbook.csv_cell`). Numbers, and text that is exactly a number, are written as they are.
- **Two rows added to the run summary sheet:** the query's note and review comment, and who did what (from
  `action_record`). They were added so that notes and names are among the cells tested.

### Finding 3: record who did it (migration 0009, `action_record`)

**The owner's answer:** "New table action_record, migration 0009, as you recommend. Also write a row for confirm and
cancel, which already store the name elsewhere, so that 'who did what' is complete in one place; keep their existing
records unchanged."

**What a row holds:** one row per action, written in the same transaction as the write it records
(`db/actions.record`):
- the action, from a fixed list: create, edit, new version, submit, return, domain confirmation, dispatch, dispatch
  again, cancel, confirmation of the question as tested, and registering a source;
- where it was done: the website, the command line or code;
- the name given;
- what it acted on, which the database checks per action;
- the database's time.

**What the database enforces:**
- the rows are append-only;
- a website row must have a name, and code's row has none;
- the downgrade refuses while any row exists.

**Where the name comes from:**
- **The website:** every write passes the signed-in name.
- **The command line:** passes `--by` where the command has it. `sources register` gains an optional `--by`, and
  `dispatch --again` records `--by` if given. A command without a name is recorded with none, as such.
- **Code:** a narrower question that code creates is recorded as code's, with no name.

**Unchanged:** the confirmation's and the cancellation's own records, and the stored review-comment words.

### Isolation

A second fresh-process probe (`test_web_isolation.py`) checks every 10b page and every website write. That is the
queries, new query, query, edit, review, sources, the connection test, each agent page, help, the run page with its
plot, the workbook and the CSV. None of them loads a model library or the queue, worker, orchestrator, recovery or
guarded runner.

### The stall test (the owner's decision, before the review)

`test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance` failed once in the
test image. The owner decided: "widen it now".
- **The test-only allowance:** 20 s, with a 22 s downtime before the attempt.
- **A one-shot hold on the first `record` insert** makes the child's write come after the monitor's first sample.
- **The production value (900 s)** is unchanged.
- **Its mutation is still caught:** downtime counted against the allowance. The control run is clean (`a4b29d9`).

### Tests

- **The whole suite:** 2,419 tests, all passing locally on `410eaa7`, serially, in 40 min 26 s (the first run on `c3cb765`: 2,418 passed and 1 failed, the pinned `confirm` signature, listed below).
- **New tests:**
  - `test_web_fix10b.py`, 11 tests:
    - two-session tests for review and editing;
    - a form that sends no version, or a forged one;
    - the pipeline's own refusal;
    - exported cell types, with formula-like text planted in the hypothesis, the paper references, the note, the
      names and the Analyst's text;
    - every CSV formula sign;
    - every website write's stored name;
    - registration and confirmation rows;
    - append-only rows.
  - `test_migrations_step10b.py`: migration 0009.
  - In `test_web_isolation.py`: the 10b pages and writes probe.
- **Failed before:** the new tests, run against the reviewed package (`a4b29d9`):
  - `test_migrations_step10b.py` cannot import there: there is no `db.actions` module;
  - all 12 others fail (the 11 in `test_web_fix10b.py` and the isolation probe): no version fields on the forms, a stale dispatch accepted, no `by` or `submit` parameters,
    and no `action_record` table.

  Several stop at a missing parameter before reaching the behaviour. The mutation checks show each behaviour is
  tested.
- **Mutation checks:** 16 faults, all caught, each by a test written for it; the control run is clean (27 tests).

  | Finding | Faults |
  |---|---|
  | 1, act on the version shown | no stale check; the website may send no version; review acts on the latest version (the original bug); edit uses the latest version; a fingerprint without the content |
  | 2, no formulas in exports | formula cells in the workbook; the CSV not neutralised; only "=" neutralised |
  | 3, who did it | no action rows; a website create with no name; no confirmation row; no registration row; dispatch again with no name; the time not forced to the database's; rows mutable; a website row without a name allowed |
- **Reference runs:** byte-identical to `main` in all six dumps.
- **Images:** rebuilt on `410eaa7`. The package's SHA-256 is the same in the repository, the runtime image and the test image (checked again after a Codespace restart). The test image's `tests/` equals the repository's, the runtime image holds no `tests/` or `docs/`, and the guard checks pass in it. The suite in the test image: 2,419 passed (44 min 23 s). The Docker build cache was pruned.
- **Schema:** now 0009. The summary's "not changed" list above said the migrations stay at 0008; that was true of
  10b before this fix round.

**Changed tests, and why** (none weakened, none removed):

| Test | Change | Reason |
|---|---|---|
| `test_web_queries.py`: 7 tests that post to the query forms | each sends the version its page showed (`shown`); the dispatch-again refusal while a run is open sends the stored version, as there is no form then | the website now refuses a write without the version shown (finding 1) |
| `test_migrations_step9b.py::test_0008_is_the_head_and_follows_0007` | now `test_0008_follows_0007` | 0009 is the head; the head check moved to `test_migrations_step10b.py` |
| `test_migrations_step9b.py::test_the_downgrade_refuses_while_a_claim_exists` | expects the head (0009) after the refused downgrade, not "0008" | the database stays at the head |
| `test_migrations.py::expected_triggers` | adds 0009's triggers | the new table |
| `test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself` | the pinned parameter list gains `via` | where the confirmation was made, for its action row; still one run, one name, the same two callers |

### Register

**169 entries.** Three new ones, drafts for the owner's review:
- `action_record`;
- `act_on_version_shown`;
- `export_no_formulas`.

Two 10b drafts were revised:
- **`query_versions_on_the_website`:** says that writes act only on the version shown and are recorded; its setting
  `queries.WEBSITE` is replaced by `queries.WHERE_WORDS`, because `WEBSITE` now names where a write came from.
- **`web_source_registration`:** "under the signed-in name" is now true and says where the name is stored.

`signed_in_name` (10a, approved wording) is unchanged.
