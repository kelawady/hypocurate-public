# Build step 10b — summary for review

Date: 2026-10-11. Branch: `step-10b-screens` (from `main` at `7620f77`, step 10a merged). **Status: built, pushed once for the review round, not merged; register entries waiting for the owner's approval; stopped for the second-model review.**

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

**GitHub run:** on the pushed head; its result and suite time are reported to the owner and go into this summary in the review round's first commit.

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
