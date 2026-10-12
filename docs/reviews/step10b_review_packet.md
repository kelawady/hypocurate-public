# Build step 10b — review packet

Branch `step-10b-screens`, head `ceccc3d`, against `main` `7620f77`. Generated from the files on disk by a script (quoted at the end).

## 1. The summary

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


## 2. Commits

```
ceccc3d Step 10b: register entries; a marked test run labelled in the queries list and the run queue
23eb179 Step 10b, b5: the Help page; every glossary entry has a button on some screen
fa462b1 Step 10b, b4: the workbook and the records CSV, built on request; the command line's export
c8450c7 Step 10b, b2: the Critic's flags on the run page, data sources with registration, read-only agent pages
c7a6371 Step 10b: each sensitivity set says what it changes compared with the main result (owner's request)
c1d2b3c Step 10b: a failed run explained in plain English first, the codes second (owner's request)
25a3ee5 Step 10b: the phone plot's y-axis label clears its numbers; corrected plot screenshots for the owner
80d58b2 Step 10b: the owner's screenshot review - plot markers by source, limited axes, phone plot and menu, short names
22e456e Step 10b, b3: the plot; the edit form keeps a version's own choices; screenshots for the owner's review
1ebd31c Step 10b, b1: the query pages and the runs list's Plan column

```

## 3. Files changed

```
 .../step10b_screenshots/01_queries_list.png        | Bin 0 -> 669711 bytes
 docs/reviews/step10b_screenshots/02_new_query.png  | Bin 0 -> 103449 bytes
 .../step10b_screenshots/03_query_dispatched.png    | Bin 0 -> 113774 bytes
 .../step10b_screenshots/04_query_returned.png      | Bin 0 -> 93578 bytes
 .../05_edit_returned_new_version.png               | Bin 0 -> 122485 bytes
 docs/reviews/step10b_screenshots/06_edit_draft.png | Bin 0 -> 117236 bytes
 .../step10b_screenshots/07_review_and_dispatch.png | Bin 0 -> 170706 bytes
 .../08_runs_list_plan_column.png                   | Bin 0 -> 474607 bytes
 .../step10b_screenshots/09_run_plot_reference.png  | Bin 0 -> 1203863 bytes
 .../10_run_plot_coefficient_only.png               | Bin 0 -> 699510 bytes
 .../reviews/step10b_screenshots/11_run_no_plot.png | Bin 0 -> 483196 bytes
 .../step10b_screenshots/12_plot_close_up.png       | Bin 0 -> 114773 bytes
 .../step10b_screenshots/13_phone_queries_list.png  | Bin 0 -> 179862 bytes
 docs/reviews/step10b_screenshots/14_phone_plot.png | Bin 0 -> 192812 bytes
 .../15_plot_reference_corrected.png                | Bin 0 -> 158065 bytes
 .../16_plot_texas_am_only_corrected.png            | Bin 0 -> 109293 bytes
 .../17_phone_plot_corrected.png                    | Bin 0 -> 238105 bytes
 .../18_phone_menu_and_queries.png                  | Bin 0 -> 171084 bytes
 hypocurate/assumptions.json                        | 492 ++++++++++++++++++++-
 hypocurate/cli.py                                  |  15 +
 hypocurate/pipeline/catalog_view.py                | 117 +++++
 hypocurate/pipeline/failure_words.py               | 155 +++++++
 hypocurate/pipeline/plot.py                        | 234 ++++++++++
 hypocurate/pipeline/queries.py                     | 116 ++++-
 hypocurate/pipeline/query_view.py                  | 187 ++++++++
 hypocurate/pipeline/reading.py                     |  24 +
 hypocurate/pipeline/run_view.py                    |  85 ++--
 hypocurate/pipeline/workbook.py                    | 241 ++++++++++
 hypocurate/web/app.py                              | 284 +++++++++++-
 hypocurate/web/static/style.css                    |  19 +
 hypocurate/web/templates/_state.html               |   6 +-
 hypocurate/web/templates/agent.html                |  32 ++
 hypocurate/web/templates/base.html                 |   6 +
 hypocurate/web/templates/help.html                 |  21 +
 hypocurate/web/templates/queries.html              |  31 ++
 hypocurate/web/templates/query.html                |  41 ++
 hypocurate/web/templates/query_form.html           |  40 ++
 hypocurate/web/templates/review.html               |  60 +++
 hypocurate/web/templates/run.html                  |  29 ++
 hypocurate/web/templates/runs.html                 |   3 +-
 hypocurate/web/templates/sources.html              |  47 ++
 tests/test_assumptions.py                          |   6 +-
 tests/test_failure_words.py                        | 142 ++++++
 tests/test_help.py                                 |  65 +++
 tests/test_plot.py                                 | 201 +++++++++
 tests/test_web_catalog.py                          | 138 ++++++
 tests/test_web_queries.py                          | 294 ++++++++++++
 tests/test_web_runs.py                             |  56 +++
 tests/test_web_state.py                            |   4 +-
 tests/test_workbook.py                             | 144 ++++++
 50 files changed, 3282 insertions(+), 53 deletions(-)

```

## 4. The full diff (screenshots and this packet left out)

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 2f94630..f1e8609 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4994,7 +4994,7 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.pipeline.writes:CONSTRUCTED_MARK",
@@ -5008,10 +5008,7 @@
           "ref": "python:hypocurate.pipeline.results:REAL_RUN"
         }
       ],
-      "done": "The mark and the refusals at storage, inclusion and freeze (step 6). Step 7: the label on every stored analysis and calibration result and on the statistics and gap-facts stage results of a marked run (checked by the database for result rows), and one named condition that leaves marked runs out of every aggregate (pipeline/results.py, REAL_RUN). Step 10a: the run viewer shows the label on a marked run, and the runs list marks it (a hatched dial and a 'test run' badge).",
-      "pending": "The label and the exclusion on the remaining screens and lists (step 10b).",
-      "step": 10,
-      "note": "The guard is in code; the database itself does not refuse a constructed record."
+      "note": "The guard is in code; the database itself does not refuse a constructed record. Step 10: the run page, the runs list and a query's runs show the label (hatched dial), and the workbook's summary."
     },
     "history": [
       {
@@ -5031,7 +5028,8 @@
       "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records",
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
       "tests/test_queries_step9a.py::test_dispatch_refuses_a_constructed_source_unless_the_run_is_a_marked_test",
-      "tests/test_web_runs.py::test_a_marked_test_runs_dial_is_hatched_with_a_badge"
+      "tests/test_web_runs.py::test_a_marked_test_runs_dial_is_hatched_with_a_badge",
+      "tests/test_workbook.py::test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test"
     ]
   },
   {
@@ -9058,7 +9056,7 @@
     "key": "sensitivity_set_display_names",
     "name": "Sensitivity sets shown by name, never by internal key",
     "state": "in_force",
-    "statement": "The screens name each sensitivity set in words and describe its one change for readers; the internal keys are never shown. The ninth set keeps its approved name, \"without the group with the largest share of slope information\", with the eligibility code's description. The survivor set's description is the owner's: \"Conflicting values, left out of the main result, are included once each, using the survivor's value.\"",
+    "statement": "The screens name each sensitivity set in words and say what its one change does compared with the main result, with the main result's own rule read from the run's locked plan; the internal keys are never shown. 'atomic percent (at.%)' is written out once, in the 1 at.% set's name. The ninth set keeps its approved name, 'without the group with the largest share of slope information'. The survivor set's description is the owner's: 'Conflicting values, left out of the main result, are included once each, using the survivor's value.'",
     "value": {
       "text": "display names and descriptions",
       "unit": null
@@ -9094,11 +9092,21 @@
     "tests": [
       "tests/test_web_runs.py::test_sensitivity_sets_are_shown_by_display_name_never_by_internal_name",
       "tests/test_web_runs.py::test_every_sensitivity_set_has_a_display_name_and_a_description",
-      "tests/test_web_runs.py::test_the_survivor_set_says_that_conflicting_values_are_normally_left_out"
+      "tests/test_web_runs.py::test_the_survivor_set_says_that_conflicting_values_are_normally_left_out",
+      "tests/test_web_runs.py::test_every_set_description_says_what_the_main_result_does_instead",
+      "tests/test_web_runs.py::test_the_one_at_pct_set_names_the_main_results_own_rounding_from_the_plan"
+    ],
+    "history": [
+      {
+        "from": "2026-10-11",
+        "to": "2026-10-11",
+        "value": "display names and descriptions",
+        "note": "the descriptions named the set's change only; the owner asked (2026-10-11) that each say what it changes compared with the main result"
+      }
     ],
-    "history": [],
     "notes": [
-      "Wording approved by the owner, 2026-10-11."
+      "Wording approved by the owner, 2026-10-11.",
+      "2026-10-11 (step 10b): reworded for the owner's request; Wording drafted by Claude Code for the owner's review (2026-10-11)."
     ]
   },
   {
@@ -9299,5 +9307,469 @@
       "Wording and page size (50) approved by the owner, 2026-10-11.",
       "2026-10-11: reworded for the ID cursor (fix round 2; the owner's decision to fix and merge)."
     ]
+  },
+  {
+    "key": "query_versions_on_the_website",
+    "name": "Query versions on the website",
+    "state": "in_force",
+    "statement": "A new query is saved as a draft or submitted for review. A draft is edited in place (it was never submitted). A submitted query is reviewed: the reviewer confirms or changes the domain under the signed-in name ('domain confirmed on the website by <name>') and dispatches it, with an optional ceiling, or returns it for edits with a comment ('returned by <name>: <comment>'). A returned or dispatched version never changes: editing a returned query creates its next version, a draft, and earlier versions are kept (PRD 9.2). A query whose last run ended can be dispatched again as a new run. Every write carries the session's CSRF token; refusals are shown in code's words (the monthly cap, constructed test data, a domain not yet supported).",
+    "value": {
+      "text": "draft in place; returned -> next version",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The query pages (PRD 9.1 to 9.3).",
+    "reason": "PRD 9.1 to 9.3; the owner's go for 10b; the default for drafts stated to the owner on 2026-10-11.",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.queries:update_draft"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:new_version"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:return_for_edits"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:WEBSITE",
+          "equals": "on the website"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:CLAIM_MAX",
+          "equals": 2000
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:NOTE_MAX",
+          "equals": 2000
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:COMMENT_MAX",
+          "equals": 2000
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_queries.py::test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_signed_in_name",
+      "tests/test_web_queries.py::test_a_returned_query_is_edited_as_its_next_version_and_the_returned_one_is_kept",
+      "tests/test_web_queries.py::test_every_query_write_refuses_a_request_without_the_sessions_token",
+      "tests/test_web_queries.py::test_only_a_draft_is_edited_in_place_and_only_a_returned_query_gets_a_new_version"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "queries_list",
+    "name": "The queries list",
+    "state": "in_force",
+    "statement": "The queries list shows every query, newest first, in pages of 50 followed by an ID cursor (as the runs list), with short source names (MPEA, Texas A&M); a query's own page gives the full names. Each row's action is the PRD's: Edit for a draft or returned query, Review for a submitted one, Open run for a dispatched one.",
+    "value": {
+      "text": "50 a page; short source names",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The queries list (PRD 9.1).",
+    "reason": "PRD 9.1; the owner's screenshot review of 2026-10-11 (short source names).",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.query_view:QUERIES_PER_PAGE",
+          "equals": 50
+        },
+        {
+          "ref": "python:hypocurate.pipeline.query_view:SOURCE_SHORT_NAMES"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_queries.py::test_the_queries_list_goes_through_every_query_once_while_queries_are_added",
+      "tests/test_web_queries.py::test_the_queries_list_uses_short_source_names_and_the_query_page_full_ones"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "runs_list_plan_column",
+    "name": "The runs list's Plan column",
+    "state": "in_force",
+    "statement": "The runs list says where each run's question as tested came from, from what is stored (the run's fixed-plan flag, its narrower link, its locked plan, its confirmation), never a guess: 'fixed reference plan', 'Planner's reading', 'Planner's reading, confirmed by <name>', 'Planner's reading; predates confirmation', or 'narrower question, built by code from run <N>'.",
+    "value": {
+      "text": "the owner's wording",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The runs list.",
+    "reason": "The owner's requests of 2026-10-11.",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.reading:PROVENANCE_WORDS"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.reading:provenance"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_runs.py::test_the_runs_list_says_where_each_runs_question_as_tested_came_from",
+      "tests/test_web_runs.py::test_a_narrower_questions_run_says_so"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "failure_explanations",
+    "name": "A failed run explained in plain English",
+    "state": "in_force",
+    "statement": "A failed run's page explains the failure in plain English first: what happened, what was and was not done (read from the stored rows: plan locked, sources searched, dataset frozen), and what the person can do next, one fixed explanation per stored failure code; the Planner's stored rejection reasons in code's words; then 'Technical detail: <code>, <detail>.' A source a run never reached reads 'not searched (the run ended first)'. The runs list shows a short plain form.",
+    "value": {
+      "text": "plain words first, codes second",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Failed runs' pages and the runs list.",
+    "reason": "The owner's request of 2026-10-11.",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.failure_words:EXPLAIN"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.failure_words:SHORT"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.run_view:NOT_REACHED",
+          "equals": "not searched (the run ended first)"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_failure_words.py::test_the_owners_example_a_planner_refused_twice",
+      "tests/test_failure_words.py::test_every_failure_code_the_orchestrator_stores_has_its_own_explanation",
+      "tests/test_failure_words.py::test_the_runs_list_says_it_in_plain_words_too"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "run_plot",
+    "name": "The plot of a run",
+    "state": "in_force",
+    "statement": "Built on request from stored rows, never stored: each record's own outcome (MPa) against grain size^-1/2; a fixed marker shape per source (circles MPEA, triangles Texas A&M, squares the controlled duplicates, diamonds any other), filled for a record in the test, a cross for one used only in a sensitivity set, hollow for one not used. One line per alloy in the test over its own grain sizes, all with the stored slope; no lines below the minimums or with no coefficient, with the reason; no plot when nothing was frozen. A coefficient-only fit says 'used in the fit (coefficient only: no valid uncertainty, not a test)'. The axes cover the records used and the sensitivity-only ones, and a line says how many records not used lie outside. A narrow drawing is shown on a phone so the text stays at least 12 px. It states its format and the code version that built it.",
+    "value": {
+      "text": "raw values; per-alloy lines with the stored slope",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The run page (PRD 9.4).",
+    "reason": "The owner's answer of 2026-10-11 (raw values and per-alloy lines) and screenshot review (markers by source, limited axes, phone, coefficient-only wording).",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.plot:PLOT_FORMAT",
+          "equals": 1
+        },
+        {
+          "ref": "python:hypocurate.pipeline.plot:SOURCE_SHAPES",
+          "equals": {
+            "mpea": "circle",
+            "tamu_fcc": "triangle",
+            "controlled_duplicates": "square"
+          }
+        },
+        {
+          "ref": "python:hypocurate.pipeline.plot:USED_COEFFICIENT_ONLY"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.plot:LAYOUTS"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_plot.py::test_the_used_points_fit_back_to_the_stored_slope_and_each_alloy_gets_one_line",
+      "tests/test_plot.py::test_every_marker_has_its_sources_fixed_shape_never_its_order",
+      "tests/test_plot.py::test_the_view_is_limited_to_the_records_in_the_fit_and_says_how_many_lie_outside",
+      "tests/test_plot.py::test_the_plot_states_its_format_and_the_code_version_that_built_it",
+      "tests/test_plot.py::test_the_phone_drawing_keeps_its_text_at_12_px_or_more"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "run_workbook",
+    "name": "The run's workbook and records CSV",
+    "state": "in_force",
+    "statement": "Built on request from stored rows, never stored, for every outcome: PRD 11's four sheets (records used; records not used with the rule, flags and sensitivity sets; significance and commentary; run summary) and a records CSV. Each states its format and the code version that built it. The website's download and the command line's export use the same functions. The artifact table stays unused in sprint 1.",
+    "value": {
+      "text": "four sheets; built on request",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The download (PRD 11) and 'hypocurate export'.",
+    "reason": "PRD 11; the owner's answer 3 to the step 10 plan (built on request).",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.workbook:WORKBOOK_FORMAT",
+          "equals": 1
+        },
+        {
+          "ref": "python:hypocurate.pipeline.workbook:SHEETS",
+          "equals": [
+            "Records used",
+            "Records not used",
+            "Significance and commentary",
+            "Run summary"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_workbook.py::test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test",
+      "tests/test_workbook.py::test_the_workbooks_totals_equal_the_recorded_model_calls",
+      "tests/test_workbook.py::test_every_outcome_has_a_workbook",
+      "tests/test_workbook.py::test_the_website_download_and_the_command_lines_export_give_the_same_workbook"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "web_source_registration",
+    "name": "Registering a source from the website",
+    "state": "in_force",
+    "statement": "The data sources page lists every registered source and every source defined in code that is not registered yet; registering one calls sources.versions.register (as the command line's 'sources register'), under the signed-in name and with the session's CSRF token; a request without the token is refused and writes nothing. 'Test connection and show sample records' only reads. A source of a person's own, from a form, needs an adapter in code first and is for a later sprint.",
+    "value": {
+      "text": "code-defined sources only; CSRF",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The data sources page (PRD 9.6).",
+    "reason": "The owner's addition 4 to the step 10 plan (a safeguard, with the same review as the other write paths).",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.sources.versions:register"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_catalog.py::test_registering_a_source_from_the_website_records_it_and_names_the_person",
+      "tests/test_web_catalog.py::test_registration_without_the_sessions_token_is_refused_and_writes_nothing",
+      "tests/test_web_catalog.py::test_the_connection_test_shows_sample_records_and_writes_nothing"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "agent_pages",
+    "name": "The agent pages",
+    "state": "in_force",
+    "statement": "One read-only page per role with its latest stored settings version and a 'Fixed in code' panel: what the role receives at each stage (the access layer's own allow-lists and field descriptions), what it returns (the role's own output description), what it may call and what it may not do (fixed sentences summarizing CLAUDE.md's rules).",
+    "value": {
+      "text": "read-only",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The agent pages (PRD 9.5).",
+    "reason": "PRD 9.5.",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.catalog_view:MAY_CALL"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.catalog_view:MAY_NOT"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_catalog.py::test_each_agent_page_shows_exactly_what_the_access_layer_lets_the_role_receive",
+      "tests/test_web_catalog.py::test_each_agent_page_says_what_the_role_returns_from_the_roles_own_description"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
+  },
+  {
+    "key": "help_page",
+    "name": "The Help page and the information buttons",
+    "state": "in_force",
+    "statement": "Every explanation lives in one file, hypocurate/web/glossary.json; every entry has an information button on some screen, every button names an entry, no template repeats an explanation's text, and the Help page lists every entry by where it appears, with a search.",
+    "value": {
+      "text": "one glossary file",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every screen; the Help page (PRD 9.7).",
+    "reason": "PRD 9.7; criterion 14.5.",
+    "evidence": [
+      "Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "file:hypocurate/web/glossary.json:\"key\":\"outcome\""
+        },
+        {
+          "ref": "python:hypocurate.web.app:STATEMENT_TERMS"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_help.py::test_every_glossary_entry_has_a_button_and_every_button_has_an_entry",
+      "tests/test_help.py::test_no_template_repeats_an_explanations_text",
+      "tests/test_help.py::test_the_help_page_lists_every_explanation_and_where_it_appears"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+    ]
   }
 ]
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index a45ec89..1af3c2d 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -70,6 +70,10 @@ def main(argv: list[str] | None = None) -> int:
     cancel.add_argument("--by", required=True, help="the name of the person cancelling")
     show = sub.add_parser("show", help="print a run's outcome and summary")
     show.add_argument("run", type=int)
+    export = sub.add_parser("export", help="write a run's workbook (PRD 11, 12), or with --csv its records")
+    export.add_argument("run", type=int)
+    export.add_argument("--out", required=True, help="the file to write")
+    export.add_argument("--csv", action="store_true", help="the records as CSV instead of the workbook")
     args = parser.parse_args(argv)
 
     settings = load_settings(web=False)
@@ -84,6 +88,17 @@ def main(argv: list[str] | None = None) -> int:
     if args.command == "worker":
         from hypocurate import worker as background
         return background.run(once=args.once, engine=engine)
+    if args.command == "export":  # step 10b: the same functions as the website's download
+        from hypocurate.pipeline import workbook
+        data = workbook.records_csv(engine, args.run) if args.csv else workbook.build(engine, args.run)
+        if data is None:
+            print(f"error: no run {args.run}", file=sys.stderr)
+            return 1
+        content = data.encode("utf-8") if isinstance(data, str) else data
+        with open(args.out, "wb") as f:
+            f.write(content)
+        print(json.dumps({"run": args.run, "written": args.out, "bytes": len(content)}))
+        return 0
     if args.command in ("run", "dispatch", "show", "confirm", "cancel", "queue"):
         from hypocurate.cli_runs import command
         return command(args, engine)
diff --git a/hypocurate/pipeline/catalog_view.py b/hypocurate/pipeline/catalog_view.py
new file mode 100644
index 0000000..707250a
--- /dev/null
+++ b/hypocurate/pipeline/catalog_view.py
@@ -0,0 +1,117 @@
+"""The data sources and the agents, as people see them (build step 10b; PRD 9.5 and 9.6). Read-only.
+
+- `sources_page`: every registered source (type, kind of data, licence, adapter status, whether it is on, its latest
+  sealed version), and every source defined in code that is not registered yet. Registering one, and "Test connection
+  and show sample records", are the pipeline's own functions (`sources.versions.register`,
+  `sources.connection.test_connection`); the website only calls them.
+- `agent_page`: a role's latest stored settings version (instruction, model, limits, role settings), read-only in
+  sprint 1, and the "Fixed in code" panel: what the role receives at each stage (the access layer's own allow-lists
+  and field descriptions), what it returns (the role's own output description), what it may call, and what it may not
+  do. What a role receives and returns comes from the settings that enforce it; what it may call and may not do are
+  fixed sentences summarizing CLAUDE.md's rules (`MAY_CALL`, `MAY_NOT`), not read from code.
+"""
+from __future__ import annotations
+
+from sqlalchemy import Engine, text
+
+from hypocurate.pipeline.run_view import snapshot
+
+ROLE_NAMES = {"planner": "Planner", "curator": "Curator", "critic": "Critic", "analyst": "Analyst",
+              "commentator": "Commentator"}
+# What each role may not do (CLAUDE.md, "Rules the code must never break", 2), in the screens' words.
+MAY_NOT = {
+    "planner": "It fills the plan's template parameters from counts only and never sees an outcome value. Code checks "
+               "its answer, and a named person confirms the question as tested before anything is locked.",
+    "curator": "It proposes extraction details for a source's documentation, never the direction of a claim; it has no "
+               "say over which records are included. The owner accepts or rejects each proposal.",
+    "critic": "It classifies flags that code raised, from sources and metadata; it is told the kind of flag, not the "
+              "numbers, and never sees outcome values. Its classes are advice only and are not used in decisions.",
+    "analyst": "It explains results that code has already computed; code inserts every number, and its text is "
+               "labelled as not verified.",
+    "commentator": "Not built in sprint 1 (PRD 15, step 12): it reads nothing at any stage.",
+}
+MAY_CALL = "Nothing: agents return text only. No agent is given a tool, a database connection, SQL or a file path."
+
+
+def sources_page(engine: Engine) -> dict:
+    from hypocurate.sources.versions import SOURCES
+    with snapshot(engine) as conn:
+        rows = [dict(r._mapping) for r in conn.execute(text(
+            "SELECT s.key, s.name, s.source_type, s.data_kind, s.licence, s.adapter_status, s.enabled, "
+            "s.grouping_unit, v.fingerprint, v.label AS version_label, "
+            "to_char(v.sealed_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS sealed FROM source s "
+            "LEFT JOIN LATERAL (SELECT sv.fingerprint, sv.label, sv.sealed_at FROM source_version sv WHERE "
+            "sv.source_id = s.id AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) v ON true "
+            "ORDER BY s.enabled DESC, s.key")).all()]
+    registered = {r["key"] for r in rows}
+    for r in rows:
+        d = SOURCES.get(r["key"])
+        r.update(constructed=bool(d and d.constructed), adapter_words="available" if r["adapter_status"] == "available"
+                 else "adapter needed", enabled_words="on" if r["enabled"] else "off",
+                 short_fingerprint=(r["fingerprint"] or "")[:12])
+    unregistered = [{"key": k, "name": d.name, "data_kind": d.data_kind, "licence": d.licence,
+                     "constructed": d.constructed} for k, d in SOURCES.items() if k not in registered]
+    return {"sources": rows, "unregistered": unregistered}
+
+
+def connection_page(engine: Engine, key: str, n: int = 5) -> dict:
+    """'Test connection and show sample records' (PRD 9.6): the report of `connection.test_connection` (read-only)."""
+    from hypocurate.sources.connection import test_connection
+    report = test_connection(engine, key, n).to_json()
+    sample = []
+    for r in report["sample"]:
+        h = r.get("harmonized") or {}
+
+        def value(field):
+            entry = h.get(field) or {}
+            v = entry.get("value")
+            return (f"{v:g} {entry.get('unit') or ''}".strip() if isinstance(v, (int, float)) else
+                    (str(v) if v is not None else f"— ({entry.get('status', 'missing').replace('_', ' ')})"))
+        sample.append({"item": r.get("source_item_key"), "alloy": r.get("alloy") or "—",
+                       "grain_size": value("grain_size"), "yield_strength": value("yield_strength"),
+                       "paper": r.get("paper_reference") or r.get("paper_doi") or "—"})
+    return {**report, "sample_rows": sample,
+            "statuses": ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(report["status_counts"].items())),
+            "unrecognized_words": ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(report["unrecognized"]
+                                                                                            .items()) if v) or "none"}
+
+
+def _receives(role: str) -> list[dict]:
+    from hypocurate.access.allowlist import ALLOWED, FIELDS
+    out = []
+    for stage, fields in sorted((ALLOWED.get(role) or {}).items()):
+        out.append({"stage": stage.replace("_", " "),
+                    "fields": [{"field": f.replace("_", " "), "words": FIELDS.get(f, "")} for f in sorted(fields)]})
+    return out
+
+
+def _returns(role: str) -> str:
+    import importlib
+    if role == "commentator":
+        return "Nothing yet (step 12)."
+    module = importlib.import_module(f"hypocurate.pipeline.agents.{role}")
+    return getattr(module, "OUTPUT_DESCRIPTION", "Text, checked by code.")
+
+
+def agents_list(engine: Engine) -> list[dict]:
+    with snapshot(engine) as conn:
+        versions = dict(conn.execute(text("SELECT role, max(version) FROM agent_setting GROUP BY role")).all())
+    return [{"role": r, "name": n, "version": versions.get(r)} for r, n in ROLE_NAMES.items()]
+
+
+def agent_page(engine: Engine, role: str) -> dict | None:
+    if role not in ROLE_NAMES:
+        return None
+    with snapshot(engine) as conn:
+        row = conn.execute(text(
+            "SELECT version, instruction, model, limits, settings, "
+            "to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created FROM agent_setting "
+            "WHERE role = :r ORDER BY version DESC LIMIT 1"), dict(r=role)).one_or_none()
+    stored = None
+    if row is not None:
+        stored = {"version": row.version, "instruction": row.instruction, "model": row.model, "created": row.created,
+                  "limits": [f"{k.replace('_', ' ')}: {v}" for k, v in sorted((row.limits or {}).items())],
+                  "settings": [f"{k.replace('_', ' ')}: {v}" for k, v in sorted((row.settings or {}).items())]}
+    return {"role": role, "name": ROLE_NAMES[role], "stored": stored, "receives": _receives(role),
+            "returns": _returns(role), "may_call": MAY_CALL, "may_not": MAY_NOT[role],
+            "roles": agents_list(engine)}
diff --git a/hypocurate/pipeline/failure_words.py b/hypocurate/pipeline/failure_words.py
new file mode 100644
index 0000000..d2f19eb
--- /dev/null
+++ b/hypocurate/pipeline/failure_words.py
@@ -0,0 +1,155 @@
+"""A failed run explained in plain English (build step 10b; owner's request of 2026-10-11).
+
+The page says first, in plain sentences, what happened, what was and was not done, and what the person can do next;
+then the codes, as "Technical detail: …". Every sentence is fixed text chosen by the stored failure code (and its
+detail code), with the facts it names read from the stored rows: whether a plan was locked, the sources searched, a
+dataset frozen; the number of Planner attempts; the name in a cancellation. Where the Planner's stage stored a
+specific reason for refusing an answer, it is shown too, in code's own words. Nothing a model wrote is shown here.
+"""
+from __future__ import annotations
+
+import re
+from typing import Mapping
+
+from sqlalchemy import Connection, text
+
+# One plain explanation per failure code (failure_reason "<code>: <reason>[ (<detail>)]"). {done}: what was done
+# before the stop, from the stored rows. {attempts}, {each}: the Planner's attempts. {by}: the person who cancelled.
+EXPLAIN = {
+    "planner_failed": ("The run stopped before anything was tested. The Planner proposed a plan {attempts}, and {each} "
+                       "code's checks refused it, so nothing was locked or searched. You can dispatch the question "
+                       "again as a new run."),
+    "planner_unreadable": ("The run stopped before anything was tested. The Planner answered {attempts}, but {each} "
+                           "the answer was not in the form code can read, so nothing was locked or searched. You can "
+                           "dispatch the question again as a new run."),
+    "planner_unreachable": ("The run stopped before anything was tested: the model provider could not be reached "
+                            "when the Planner was asked, so nothing was locked or searched. You can dispatch the "
+                            "question again as a new run once the provider answers."),
+    "planner_declined": ("The run stopped before anything was tested: the Planner's model declined to answer, so "
+                         "nothing was locked or searched. You can reword the hypothesis and dispatch it again."),
+    "planner_provider_refused": ("The run stopped before anything was tested: the model provider refused the "
+                                 "Planner's request ({words}), so nothing was locked or searched. The provider's "
+                                 "settings need checking before the question is dispatched again."),
+    "domain_mismatch": ("The run stopped before anything was tested: the Planner judged that the claim belongs to "
+                        "another domain, so nothing was locked or searched. Check the query's domain, then dispatch "
+                        "it again as a new run."),
+    "claim_not_one_plan": ("The run stopped before anything was tested: the claim covers more than one temperature "
+                           "band, test type or alloy class, and one run tests one of each, so nothing was locked or "
+                           "searched. Edit the query into one question per band, test type and alloy class, and "
+                           "dispatch each."),
+    "narrowing_sources_changed": ("The run stopped before anything was tested: the sources changed after the original "
+                                  "question's narrowing decision counted them, so the narrower plan no longer "
+                                  "describes them, and nothing was locked or searched. Dispatch the original question "
+                                  "again as a new run."),
+    "narrower_plan_missing": ("The run stopped before anything was tested: the original question's narrowing decision "
+                              "holds no narrower plan, so nothing was locked or searched. Dispatch the original "
+                              "question again as a new run."),
+    "spending_refused": ("The run stopped because its next model request would have gone over {cap}; the request was "
+                         "not sent and nothing more was paid for. {done} {next_step}"),
+    "refused": ("The run stopped because code refused one of its steps ({words}). {done} You can dispatch the question "
+                "again as a new run; if it stops the same way, the step needs looking at."),
+    "interrupted": ("The run stopped because the worker was interrupted twice while the Planner was being asked, and "
+                    "it is not asked a third time; nothing was locked or searched. You can dispatch the question "
+                    "again as a new run."),
+    "attempts_exhausted": ("The run stopped after the worker was interrupted and took it up again too many times. "
+                           "{done} You can dispatch the question again as a new run."),
+    "cancelled_queued": ("The run was cancelled by {by} before it started: nothing was asked, locked, searched or paid "
+                         "for. You can dispatch the question again as a new run."),
+    "cancelled_waiting": ("The run was cancelled by {by} while it waited for a person to confirm the question as "
+                          "tested: the Planner had been asked, but nothing was locked or searched. You can dispatch "
+                          "the question again as a new run."),
+    "other": ("The run stopped: {reason}. {done} You can dispatch the question again as a new run."),
+}
+CAPS = {"spending_cap_run": "the run's spending cap", "spending_cap_month": "this month's spending cap",
+        "ceiling_reached": "the ceiling set for this run"}
+NEXT_STEP = {"spending_cap_run": "You can dispatch it again as a new run; its cap is the per-run cap.",
+             "spending_cap_month": "Dispatch it again next month, or once the owner raises the monthly cap.",
+             "ceiling_reached": "You can dispatch it again as a new run with a higher ceiling."}
+UNREADABLE = ("malformed", "truncated", "empty", "over_long", "tool_call")
+PROVIDER = ("model_auth", "provider_rejected", "cost_unknown")
+SHORT = {"planner_failed": "the Planner's plan was refused", "planner_unreadable": "the Planner's answer was unreadable",
+         "planner_unreachable": "the model provider could not be reached",
+         "planner_declined": "the Planner's model declined to answer",
+         "planner_provider_refused": "the model provider refused the request",
+         "domain_mismatch": "the claim belongs to another domain",
+         "claim_not_one_plan": "the claim covers more than one question",
+         "narrowing_sources_changed": "the sources changed", "narrower_plan_missing": "no narrower plan",
+         "spending_refused": "a spending cap was reached", "refused": "code refused a step",
+         "interrupted": "interrupted twice at the Planner", "attempts_exhausted": "interrupted too many times",
+         "cancelled_queued": "cancelled before it started", "cancelled_waiting": "cancelled while waiting",
+         "other": "stopped"}
+
+
+def parse(reason: str) -> tuple[str, str | None]:
+    """The code and the detail code of a stored failure reason ("<code>: <words>[ (<detail>)]")."""
+    code = reason.split(":", 1)[0].strip()
+    detail = re.search(r"\(([a-z_]+)\)\s*$", reason)
+    return code, detail.group(1) if detail else None
+
+
+def _done(conn: Connection, run_id: int) -> str:
+    """What was done before the stop, from the stored rows."""
+    locked = conn.execute(text("SELECT EXISTS (SELECT 1 FROM plan WHERE run_id = :r)"), dict(r=run_id)).scalar()
+    frozen = conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r)"), dict(r=run_id)).scalar()
+    searched = conn.execute(text("SELECT count(*) FROM run_source WHERE run_id = :r AND search_status = 'searched'"),
+                            dict(r=run_id)).scalar()
+    if frozen:
+        return "The rules were locked and the dataset frozen, but no result was recorded."
+    if locked and searched:
+        return "The rules were locked and the sources searched, but no dataset was frozen and nothing was tested."
+    if locked:
+        return "The rules were locked, but no source was searched and nothing was tested."
+    return "Nothing was locked or searched."
+
+
+def _attempts(conn: Connection, run_id: int) -> tuple[list[str], list[str]]:
+    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' "
+                            "ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+    out = out if isinstance(out, Mapping) else {}
+    attempts = [a for a in out.get("attempts") or [] if isinstance(a, str)]
+    reasons = [r for r in out.get("attempt_reasons") or [] if isinstance(r, str) and r]
+    return attempts, reasons
+
+
+def _times(n: int) -> tuple[str, str]:
+    return {1: ("once", "the"), 2: ("twice", "both times")}.get(n, (f"{n} times", "each time"))
+
+
+def explain(conn: Connection, run_id: int, reason: str | None) -> dict | None:
+    """The plain explanation of a failed run: its sentences, the Planner's stored reasons in code's words (if any), a
+    short form for lists, and the technical detail."""
+    if not reason:
+        return None
+    from hypocurate.pipeline.agents.lm import FAILURES
+    from hypocurate.pipeline.writes import CODES
+    code, detail = parse(reason)
+    key, values, reasons = code, {"done": _done(conn, run_id)}, []
+    if code == "planner_failed":
+        attempts, reasons = _attempts(conn, run_id)
+        n = max(1, len([a for a in attempts if a != "ok"]))
+        times, each = _times(n)
+        each = "each time" if each == "the" else each
+        values.update(attempts=times, each=each if n > 1 else "")
+        if detail in UNREADABLE:
+            key = "planner_unreadable"
+        elif detail == "provider_unavailable":
+            key = "planner_unreachable"
+        elif detail == "refused":
+            key = "planner_declined"
+        elif detail in PROVIDER:
+            key, values["words"] = "planner_provider_refused", FAILURES[detail][0]
+    elif code == "spending_refused":
+        values.update(cap=CAPS.get(detail, "a spending cap or ceiling"),
+                      next_step=NEXT_STEP.get(detail, "You can dispatch it again as a new run."))
+    elif code == "refused":
+        words = CODES.get(detail, "a write was refused") if detail else "a write was refused"
+        values["words"] = re.sub(r"\s*\(register '[^']*'\)", "", words)  # register keys belong to the detail
+    elif code == "cancelled":
+        m = re.match(r"cancelled: cancelled by (.+?) (before it started|while waiting.*)$", reason)
+        key = "cancelled_waiting" if m and m.group(2).startswith("while") else "cancelled_queued"
+        values["by"] = m.group(1) if m else "a person"
+    elif code not in EXPLAIN:
+        key, values["reason"] = "other", reason.split(":", 1)[-1].strip().rstrip(".")
+    words = " ".join(EXPLAIN[key].format(**values).split())  # one space wherever a value was left empty
+    return {"words": words, "short": f"failed: {SHORT[key]}", "reasons": reasons,
+            "technical": "Technical detail: " + ", ".join(x for x in (code, detail) if x) + "."}
diff --git a/hypocurate/pipeline/plot.py b/hypocurate/pipeline/plot.py
new file mode 100644
index 0000000..16be4ca
--- /dev/null
+++ b/hypocurate/pipeline/plot.py
@@ -0,0 +1,234 @@
+"""The plot of a run (PRD 9.4; build step 10b; owner's answer of 2026-10-11): built on request from stored rows, never
+stored (the artifact table stays unused in sprint 1).
+
+**What it shows.** Every record the run found that has a grain size and the outcome: its own outcome value (MPa)
+against grain size^-1/2 (µm^-1/2). Marker shape by source; a filled marker for a record in the test (the primary set),
+a cross for a record used only in a sensitivity set, a hollow marker for a record not used. When the test fitted a
+coefficient that is shown (not withheld below the minimums), each alloy in the test gets a line segment over its own
+grain-size range, all with the stored slope k: the alloy's baseline is its mean outcome minus k times its mean
+grain size^-1/2, the arithmetic of the fit with one baseline per alloy. With no coefficient, or below the minimums,
+there are no lines and the reason is stated; with no dataset frozen there is no plot.
+
+**What it is built from.** The run's stored records, its analysis sets and its stored statistics output, read in one
+snapshot; alloys are grouped by `eligibility.alloy` with the primary set's own rounding (as the statistics stage
+groups them), and the records' values are projected as the access layer projects them for the statistics stage.
+Nothing is fitted here: k is the stored estimate. The plot states its format and the code version that built it.
+"""
+from __future__ import annotations
+
+import math
+import os
+from collections import defaultdict
+from typing import Mapping
+
+from markupsafe import Markup
+from sqlalchemy import Engine, text
+
+from hypocurate.pipeline import display
+from hypocurate.pipeline.run_view import snapshot
+
+PLOT_FORMAT = 1
+# A fixed marker shape for each source (owner's screenshot review, 2026-10-11: never by order of appearance);
+# a source not named here is drawn as a diamond.
+SOURCE_SHAPES = {"mpea": "circle", "tamu_fcc": "triangle", "controlled_duplicates": "square"}
+OTHER_SHAPE = "diamond"
+USED, SENSITIVITY_ONLY, NOT_USED = "used in the test", "used only in a sensitivity set", "not used"
+# The legend's words for "used" when the fit gave a coefficient only (owner's review, 2026-10-11).
+USED_COEFFICIENT_ONLY = "used in the fit (coefficient only: no valid uncertainty, not a test)"
+# Two drawings of the same plot (owner's review: it scales to the screen, axis words included): a wide one and a
+# narrow one for a phone, each with its font chosen so that text is never below 12 px where it is shown (style.css:
+# the wide one from 56rem, never narrower than 540 px; the narrow one below, on screens at least 360 px wide).
+LAYOUTS = {"wide": {"w": 720, "h": 460, "left": 84, "right": 20, "top": 20, "bottom": 64, "font": 16, "r": 5,
+                    "ticks": 5},
+           "narrow": {"w": 320, "h": 300, "left": 72, "right": 10, "top": 12, "bottom": 52, "font": 14, "r": 4,
+                      "ticks": 4}}
+W, FONT = LAYOUTS["wide"]["w"], LAYOUTS["wide"]["font"]
+
+
+def code_version() -> str:
+    """The code version that built the plot, as /health reports it (Render's commit), else "unknown"."""
+    return os.environ.get("RENDER_GIT_COMMIT", "") or "unknown"
+
+
+def version_line(kind: str, fmt: int) -> str:
+    return f"{kind} format {fmt}; built by code version {code_version()}."
+
+
+def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
+    span = hi - lo or 1.0
+    raw = span / n
+    mag = 10 ** math.floor(math.log10(raw))
+    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=raw)
+    start = math.ceil(lo / step) * step
+    out, v = [], start
+    while v <= hi + 1e-9:
+        out.append(round(v, 10))
+        v += step
+    return out
+
+
+def data(engine: Engine, run_id: int) -> dict | None:
+    """The plot's points, segments and words, from one snapshot; None for an unknown run."""
+    from hypocurate.access.fields import _composition, _number
+    from hypocurate.pipeline import eligibility as el
+    from hypocurate.sources.versions import SOURCES
+    with snapshot(engine) as conn:
+        run = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).one_or_none()
+        if run is None:
+            return None
+        frozen = conn.execute(text("SELECT 1 FROM run_snapshot WHERE run_id = :r"), dict(r=run_id)).scalar()
+        plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
+        stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
+                                  "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+        if not frozen or plan is None:
+            return {"plot": False, "reason": "No plot: no dataset was frozen, so nothing was tested."
+                    if run.status in ("completed", "failed") else "No plot yet: the dataset is not frozen.",
+                    "version": version_line("Plot", PLOT_FORMAT)}
+        members: dict[str, set[int]] = defaultdict(set)
+        for key, rid in conn.execute(text(
+                "SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id "
+                "= a.id WHERE a.run_id = :r"), dict(r=run_id)).all():
+            members[key].add(rid)
+        rows = conn.execute(text(
+            "SELECT r.id, s.key AS source, r.harmonized FROM record r JOIN source_version sv ON sv.id = "
+            "r.source_version_id JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r ORDER BY r.id"),
+            dict(r=run_id)).all()
+    outcome_field = (plan.get("variables") or {}).get("outcome", {}).get("field")
+    decimals = el.settings(plan, el.PRIMARY).decimals
+    primary = members.get(el.PRIMARY, set())
+    others = set().union(*(v for k, v in members.items() if k != el.PRIMARY)) if members else set()
+    sources = sorted({r.source for r in rows})
+    points = []
+    for r in rows:
+        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
+        gs, y = _number(h.get("grain_size")), _number(h.get(outcome_field))
+        if gs is None or y is None or gs <= 0:
+            continue
+        composition = _composition(h.get("composition"))
+        use = USED if r.id in primary else SENSITIVITY_ONLY if r.id in others else NOT_USED
+        points.append({"x": gs ** -0.5, "y": y, "source": r.source, "use": use,
+                       "alloy": el.alloy({"composition": composition}, decimals) if composition else None})
+    pooled = next((a for a in (stats or {}).get("analyses") or [] if a.get("scope") == "pooled"), None)
+    k, reason = None, None
+    if pooled is None:
+        reason = "No fitted lines: the statistics were not computed."
+    elif (stats or {}).get("withheld") or pooled.get("withheld"):
+        reason = "No fitted lines: the minimums were not met, so no estimate is shown."
+    elif pooled.get("estimate") is None:
+        reason = "No fitted lines: no coefficient could be fitted."
+    else:
+        k = pooled["estimate"]
+    coefficient_only = k is not None and pooled.get("p_value") is None
+    segments = []
+    if k is not None:
+        by_alloy: dict[str, list[dict]] = defaultdict(list)
+        for p in points:
+            if p["use"] == USED and p["alloy"]:
+                by_alloy[p["alloy"]].append(p)
+        for alloy, ps in sorted(by_alloy.items()):
+            xs = [p["x"] for p in ps]
+            if len(set(xs)) < 2:
+                continue
+            mx, my = sum(xs) / len(xs), sum(p["y"] for p in ps) / len(ps)
+            base = my - k * mx
+            segments.append({"x0": min(xs), "x1": max(xs), "y0": base + k * min(xs), "y1": base + k * max(xs)})
+    names = {s: (SOURCES[s].name if s in SOURCES else s) for s in sources}
+    return {"plot": True, "points": points, "segments": segments, "k": k, "reason": reason,
+            "coefficient_only": coefficient_only,
+            "sources": [{"key": s, "name": names[s], "shape": SOURCE_SHAPES.get(s, OTHER_SHAPE)} for s in sources],
+            "counts": {u: sum(1 for p in points if p["use"] == u) for u in (USED, SENSITIVITY_ONLY, NOT_USED)},
+            "k_words": display.coefficient(k) if k is not None else None,
+            "version": version_line("Plot", PLOT_FORMAT)}
+
+
+def _marker(shape: str, x: float, y: float, use: str, r: float, source: str) -> str:
+    """One record's marker, with its source and use as attributes (the tests read them)."""
+    tag = f' class="pt" data-source="{source}" data-use="{use}"'
+    if use == SENSITIVITY_ONLY:
+        return (f'<path{tag} data-shape="cross" d="M{x - r:.1f},{y - r:.1f} L{x + r:.1f},{y + r:.1f} M{x - r:.1f},'
+                f'{y + r:.1f} L{x + r:.1f},{y - r:.1f}" stroke="#b45309" stroke-width="2" fill="none"/>')
+    fill = "#2457c5" if use == USED else "none"
+    stroke = "#2457c5" if use == USED else "#7b8494"
+    common = f'{tag} data-shape="{shape}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'
+    if shape == "circle":
+        return f'<circle{common} cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
+    if shape == "triangle":
+        return (f'<path{common} d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y + r:.1f} '
+                f'L{x - r - 1:.1f},{y + r:.1f} Z"/>')
+    if shape == "square":
+        return f'<rect{common} x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" height="{2 * r}"/>'
+    return (f'<path{common} d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y:.1f} L{x:.1f},{y + r + 1:.1f} '
+            f'L{x - r - 1:.1f},{y:.1f} Z"/>')
+
+
+def view(d: Mapping) -> dict:
+    """The axes' range (owner's review: limited to the records used and the sensitivity-only ones, and the lines) and
+    how many records not used lie outside it."""
+    shown = [p for p in d["points"] if p["use"] != NOT_USED]
+    basis = shown or d["points"]
+    xs = [p["x"] for p in basis] + [s["x0"] for s in d["segments"]] + [s["x1"] for s in d["segments"]]
+    ys = [p["y"] for p in basis] + [s["y0"] for s in d["segments"]] + [s["y1"] for s in d["segments"]]
+    x1, y1 = max(xs) * 1.05, max(ys) * 1.08
+    y0 = min(0.0, min(ys))
+    outside = sum(1 for p in d["points"] if p["use"] == NOT_USED and not (0 <= p["x"] <= x1 and y0 <= p["y"] <= y1))
+    return {"x0": 0.0, "x1": x1, "y0": y0, "y1": y1, "outside": outside}
+
+
+def svg(d: Mapping, layout: str = "wide") -> Markup:
+    """The plot as inline SVG in one of `LAYOUTS` (axis words inside, at the layout's font; legend and words are HTML
+    beside it). Records not used that lie outside the view are not drawn; `legend` says how many."""
+    pts = d["points"]
+    if not pts:
+        return Markup("")
+    L = LAYOUTS[layout]
+    w, h, left, right, top, bottom, font, r = (L[k] for k in ("w", "h", "left", "right", "top", "bottom", "font", "r"))
+    v = view(d)
+    x0, x1, y0, y1 = v["x0"], v["x1"], v["y0"], v["y1"]
+    px = lambda val: left + (val - x0) / (x1 - x0 or 1) * (w - left - right)  # noqa: E731
+    py = lambda val: h - bottom - (val - y0) / (y1 - y0 or 1) * (h - top - bottom)  # noqa: E731
+    out = [f'<svg class="plot plot-{layout}" viewBox="0 0 {w} {h}" role="img" aria-label="Yield strength against grain '
+           f'size to the power minus one half, one point per record" xmlns="http://www.w3.org/2000/svg" '
+           f'font-family="system-ui, sans-serif" font-size="{font}">',
+           f'<rect x="{left}" y="{top}" width="{w - left - right}" height="{h - top - bottom}" fill="#ffffff" '
+           f'stroke="#d8dde6"/>']
+    for t in _ticks(x0, x1, L["ticks"]):
+        out.append(f'<line x1="{px(t):.1f}" y1="{h - bottom}" x2="{px(t):.1f}" y2="{h - bottom + 5}" stroke="#5b6475"/>'
+                   f'<text x="{px(t):.1f}" y="{h - bottom + font + 6}" text-anchor="middle" fill="#5b6475">{t:g}</text>')
+    for t in _ticks(y0, y1, L["ticks"]):
+        out.append(f'<line x1="{left - 5}" y1="{py(t):.1f}" x2="{left}" y2="{py(t):.1f}" stroke="#5b6475"/>'
+                   f'<text x="{left - 8}" y="{py(t) + font / 3:.1f}" text-anchor="end" fill="#5b6475">{t:g}</text>')
+    out.append(f'<text x="{(left + w - right) / 2:.0f}" y="{h - 8}" text-anchor="middle" fill="#1d2330">grain size'
+               f'<tspan baseline-shift="super" font-size="{font}">-1/2</tspan> (µm<tspan baseline-shift="super" '
+               f'font-size="{font}">-1/2</tspan>)</text>')
+    out.append(f'<text transform="translate({font},{(top + h - bottom) / 2:.0f}) rotate(-90)" text-anchor="middle" '
+               f'fill="#1d2330">yield strength (MPa)</text>')
+    for seg in d["segments"]:
+        out.append(f'<line class="fit" x1="{px(seg["x0"]):.1f}" y1="{py(seg["y0"]):.1f}" x2="{px(seg["x1"]):.1f}" '
+                   f'y2="{py(seg["y1"]):.1f}" stroke="#1d3f78" stroke-width="2"/>')
+    for use in (NOT_USED, SENSITIVITY_ONLY, USED):  # used records drawn last, on top
+        for p in pts:
+            if p["use"] != use or not (x0 <= p["x"] <= x1 and y0 <= p["y"] <= y1):
+                continue
+            out.append(_marker(SOURCE_SHAPES.get(p["source"], OTHER_SHAPE), px(p["x"]), py(p["y"]), use, r,
+                               p["source"]))
+    out.append("</svg>")
+    return Markup("".join(out))
+
+
+def legend(d: Mapping) -> list[str]:
+    """The legend in words (HTML beside the plot)."""
+    used = USED_COEFFICIENT_ONLY if d.get("coefficient_only") else USED
+    lines = [f"{s['name']}: {s['shape']}s" for s in d["sources"]]
+    lines += [f"Filled: {used} ({d['counts'][USED]}); crosses: {SENSITIVITY_ONLY} ({d['counts'][SENSITIVITY_ONLY]}); "
+              f"hollow: {NOT_USED} ({d['counts'][NOT_USED]})."]
+    outside = view(d)["outside"] if d["points"] else 0
+    if outside:
+        lines.append(f"The view shows the records used and the sensitivity-only ones; {outside} record"
+                     f"{'' if outside == 1 else 's'} not used lie{'s' if outside == 1 else ''} outside it.")
+    if d["segments"]:
+        lines.append(f"Lines: one per alloy in the {'fit' if d.get('coefficient_only') else 'test'} "
+                     f"({len(d['segments'])}), over its own grain sizes, each with the stored slope k = {d['k_words']}; "
+                     f"an alloy's baseline is its own (one baseline per alloy).")
+    elif d.get("reason"):
+        lines.append(d["reason"])
+    return lines
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
index afdc0fb..5314709 100644
--- a/hypocurate/pipeline/queries.py
+++ b/hypocurate/pipeline/queries.py
@@ -94,8 +94,9 @@ def _source_ids(conn: Connection, keys: Iterable[str]) -> list[int]:
 
 
 def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "grain_size_strengthening",
-           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None) -> Query:
-    """A new query with one draft version."""
+           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None, note: str | None = None) -> Query:
+    """A new query with one draft version (step 10b: with the submitter's optional note)."""
+    claim, note = _claim_text(claim), _note_text(note)
     sources = list(dict.fromkeys(sources))
     if not sources:
         raise QueryRefused("no_source", "a query chooses at least one source")
@@ -105,8 +106,9 @@ def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "gr
         h = conn.execute(text("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id, number"),
                          dict(r=narrower_of_run)).one()
         vid = conn.execute(text(
-            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option) "
-            "VALUES (:h, 1, :t, :d, :o) RETURNING id"), dict(h=h.id, t=claim, d=domain_id, o=sufficiency)).scalar_one()
+            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option, note) "
+            "VALUES (:h, 1, :t, :d, :o, :n) RETURNING id"),
+            dict(h=h.id, t=claim, d=domain_id, o=sufficiency, n=note)).scalar_one()
         for sid in source_ids:
             conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
         return Query(h.id, h.number, vid)
@@ -123,8 +125,10 @@ def submit(engine: Engine, version_id: int) -> None:
     run_transaction(engine, body)
 
 
-def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None) -> None:
-    """A named person confirms the domain (or changes it to `domain`) while the version is submitted."""
+def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None,
+                   where: str = "at the command line") -> None:
+    """A named person confirms the domain (or changes it to `domain`) while the version is submitted. `where`: the
+    command line, or the website (step 10b)."""
     if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
         raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")
 
@@ -135,7 +139,7 @@ def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None
         domain_id = _domain_id(conn, domain) if domain else chosen
         conn.execute(text("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now(), "
                           "review_comment = :c WHERE id = :v"),
-                     dict(d=domain_id, c=f"domain confirmed at the command line by {by.strip()}", v=version_id))
+                     dict(d=domain_id, c=f"domain confirmed {where} by {by.strip()}", v=version_id))
 
     run_transaction(engine, body)
 
@@ -321,6 +325,104 @@ def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping)
     return q
 
 
+CLAIM_MAX = 2000      # step 10b: the hypothesis text, as typed on the new-query page
+NOTE_MAX = 2000       # the submitter's note to the reviewer
+COMMENT_MAX = 2000    # the reviewer's comment when returning a query
+WEBSITE = "on the website"  # where a domain is confirmed (step 10b)
+
+
+def _claim_text(claim: str) -> str:
+    text_ = (claim or "").strip()  # trimmed only: the claim's words are kept as written
+    if not 1 <= len(text_) <= CLAIM_MAX:
+        raise QueryRefused("claim_required", f"state the hypothesis (1 to {CLAIM_MAX} characters)")
+    return text_
+
+
+def _note_text(note: str | None) -> str | None:
+    note = (note or "").strip()
+    if len(note) > NOTE_MAX:
+        raise QueryRefused("note_too_long", f"the note is at most {NOTE_MAX} characters")
+    return note or None
+
+
+def _version(conn: Connection, number: str):
+    """The latest version of query `number`, locked."""
+    row = conn.execute(text(
+        "SELECT hv.id, hv.status, hv.version_number, h.id AS hypothesis_id, h.narrower_of_run_id FROM hypothesis h "
+        "JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE h.number = :n ORDER BY hv.version_number DESC "
+        "LIMIT 1"), dict(n=number)).one_or_none()
+    if row is None:
+        raise QueryRefused("unknown_query", f"no query {number}")
+    _lock_version(conn, row.id)
+    return row
+
+
+def update_draft(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
+                 note: str | None) -> int:
+    """Step 10b: a draft is edited in place (it was never submitted); its sources are replaced. Returns its id."""
+    claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
+    if not sources:
+        raise QueryRefused("no_source", "a query chooses at least one source")
+
+    def body(conn: Connection):
+        v = _version(conn, number)
+        if v.status != "draft":
+            raise QueryRefused("not_a_draft", f"query {number} is {v.status}; only a draft is edited in place")
+        conn.execute(text("UPDATE hypothesis_version SET text = :t, domain_id = :d, sufficiency_option = :o, "
+                          "note = :n WHERE id = :v"),
+                     dict(t=claim, d=_domain_id(conn, domain), o=sufficiency, n=note, v=v.id))
+        conn.execute(text("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v"), dict(v=v.id))
+        for sid in _source_ids(conn, sources):
+            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=v.id, s=sid))
+        return v.id
+
+    return run_transaction(engine, body)
+
+
+def new_version(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
+                note: str | None) -> int:
+    """Step 10b (PRD 9.2): editing a returned query creates its next version, a draft; earlier versions are kept
+    unchanged. Returns the new version's id."""
+    claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
+    if not sources:
+        raise QueryRefused("no_source", "a query chooses at least one source")
+
+    def body(conn: Connection):
+        v = _version(conn, number)
+        if v.status != "returned":
+            raise QueryRefused("not_returned", f"query {number} is {v.status}; a new version follows a returned one")
+        vid = conn.execute(text(
+            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option, note) "
+            "VALUES (:h, :n, :t, :d, :o, :note) RETURNING id"),
+            dict(h=v.hypothesis_id, n=v.version_number + 1, t=claim, d=_domain_id(conn, domain), o=sufficiency,
+                 note=note)).scalar_one()
+        for sid in _source_ids(conn, sources):
+            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
+        return vid
+
+    return run_transaction(engine, body)
+
+
+def return_for_edits(engine: Engine, version_id: int, by: str, comment: str) -> None:
+    """Step 10b (PRD 9.3): the reviewer returns a submitted version for edits, with a comment; it never changes again,
+    and an edit is its next version."""
+    if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
+        raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")
+    comment = (comment or "").strip()
+    if not 1 <= len(comment) <= COMMENT_MAX:
+        raise QueryRefused("comment_required", f"say what to change (1 to {COMMENT_MAX} characters)")
+
+    def body(conn: Connection):
+        status = _lock_version(conn, version_id)
+        if status != "submitted":
+            raise QueryRefused("not_submitted", f"this version is {status}; only a submitted version is returned")
+        conn.execute(text("UPDATE hypothesis_version SET status = 'returned', returned_at = now(), "
+                          "review_comment = :c WHERE id = :v"),
+                     dict(c=f"returned by {by.strip()}: {comment}", v=version_id))
+
+    run_transaction(engine, body)
+
+
 def submitted_version(engine: Engine, number: str) -> int:
     """The submitted version of query `number` (for `hypocurate dispatch Q-…`)."""
     with engine.connect() as conn:
diff --git a/hypocurate/pipeline/query_view.py b/hypocurate/pipeline/query_view.py
new file mode 100644
index 0000000..fa5c5c8
--- /dev/null
+++ b/hypocurate/pipeline/query_view.py
@@ -0,0 +1,187 @@
+"""What a query looks like to a person: read-only views for the query screens (build step 10b; PRD 9.1 to 9.3).
+
+The queries list (paged by an ID cursor, as the runs list), one query with its versions and runs, the review list
+(submitted versions, newest first) and one submitted version for review, and the choices the new-query form offers.
+Every page is read from one snapshot (`run_view.snapshot`). Nothing here writes; the writes are `pipeline.queries`'s.
+"""
+from __future__ import annotations
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.pipeline import run_view
+from hypocurate.pipeline.run_view import STATUS_WORDS, money, snapshot, tokens
+
+# Short source names for the queries list (owner's review, 2026-10-11); a query's own page gives the full names.
+SOURCE_SHORT_NAMES = {"mpea": "MPEA", "tamu_fcc": "Texas A&M", "controlled_duplicates": "controlled duplicates"}
+QUERIES_PER_PAGE = 50  # step 10b: as the runs list (register 'runs_list_pages' gives the reason for a cursor)
+VERSION_STATUS_WORDS = {"draft": "draft", "submitted": "submitted for review", "returned": "returned for edits",
+                        "dispatched": "dispatched"}
+SUFFICIENCY_WORDS = {"fixed_minimum": "fixed minimum", "use_available": "use what is available (exploratory)"}
+
+
+class NoSuchQuery(LookupError):
+    pass
+
+
+def _sources(conn: Connection, version_id: int) -> list[dict]:
+    return [dict(r._mapping) for r in conn.execute(text(
+        "SELECT s.key, s.name, s.data_kind FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
+        "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=version_id)).all()]
+
+
+def _latest_run(conn: Connection, hypothesis_id: int):
+    return conn.execute(text(
+        "SELECT r.id, r.status, r.outcome, r.evidence_level, r.experiment_flags FROM run r JOIN hypothesis_version hv "
+        "ON hv.id = r.hypothesis_version_id WHERE hv.hypothesis_id = :h ORDER BY r.id DESC LIMIT 1"),
+        dict(h=hypothesis_id)).one_or_none()
+
+
+def _action(status: str, number: str, run_id: int | None) -> dict:
+    """PRD 9.1: Edit for a draft or returned query, Review for a submitted one, Open run for a dispatched one."""
+    if status in ("draft", "returned"):
+        return {"label": "Edit", "href": f"/queries/{number}/edit"}
+    if status == "submitted":
+        return {"label": "Review", "href": f"/review/{number}"}
+    return {"label": "Open run", "href": f"/runs/{run_id}"} if run_id else {"label": "Open", "href": f"/queries/{number}"}
+
+
+def queries_list(engine: Engine, before: int | None = None, per_page: int = QUERIES_PER_PAGE) -> dict:
+    """One page of queries, newest first, with each query's latest version; the next page's cursor is the last query
+    shown (as the runs list)."""
+    if before is not None and before < 1:
+        raise NoSuchQuery(f"no queries before {before}")
+    with snapshot(engine) as conn:
+        total = conn.execute(text("SELECT count(*) FROM hypothesis")).scalar_one()
+        rows = conn.execute(text(
+            "SELECT h.id, h.number, h.narrower_of_run_id, v.id AS version_id, v.version_number, v.text, v.status, "
+            "d.name AS domain, to_char(h.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created, "
+            "coalesce(t.cap_cost, 0) AS cost FROM hypothesis h "
+            "JOIN LATERAL (SELECT * FROM hypothesis_version x WHERE x.hypothesis_id = h.id "
+            "ORDER BY x.version_number DESC LIMIT 1) v ON true JOIN domain d ON d.id = v.domain_id "
+            "LEFT JOIN model_call_totals_by_query t ON t.hypothesis_id = h.id "
+            "WHERE CAST(:before AS bigint) IS NULL OR h.id < :before ORDER BY h.id DESC LIMIT :n"),
+            dict(before=before, n=per_page + 1)).all()
+        more, rows = len(rows) > per_page, rows[:per_page]
+        out = []
+        for r in rows:
+            run = _latest_run(conn, r.id)
+            status = (STATUS_WORDS[run.status] if r.status == "dispatched" and run else VERSION_STATUS_WORDS[r.status])
+            if run is not None and (run.experiment_flags or {}).get("constructed_test_data"):
+                status += f" ({run_view.TEST_RUN_BADGE})"  # register 'constructed_test_runs': the label on every list
+            out.append({
+                "id": r.id, "number": r.number, "version": r.version_number, "created": r.created, "domain": r.domain,
+                "claim": r.text, "narrower": r.narrower_of_run_id is not None,
+                "sources": ", ".join(SOURCE_SHORT_NAMES.get(s["key"], s["key"]) for s in _sources(conn, r.version_id)),
+                "status_words": status,
+                "outcome": (run.outcome.replace("_", " ") + " in the sources searched")
+                if run is not None and run.outcome else None,
+                "cost": money(r.cost), "action": _action(r.status, r.number, run.id if run else None)})
+    if not total:
+        words = "No query yet."
+    else:
+        words = f"{total} quer{'y' if total == 1 else 'ies'} in all; " + (
+            "the newest first." if before is None else "older queries, newest first.")
+    return {"queries": out, "total": total, "words": words, "newest": before is not None,
+            "older": out[-1]["id"] if more else None}
+
+
+def query_page(engine: Engine, number: str) -> dict:
+    """One query: every version (newest first) with its runs, the query's tokens and cost, and what can be done."""
+    with snapshot(engine) as conn:
+        h = conn.execute(text("SELECT id, number, narrower_of_run_id FROM hypothesis WHERE number = :n"),
+                         dict(n=number)).one_or_none()
+        if h is None:
+            raise NoSuchQuery(f"no query {number}")
+        versions = []
+        for v in conn.execute(text(
+                "SELECT v.id, v.version_number, v.text, v.status, v.note, v.review_comment, v.sufficiency_option, "
+                "d.name AS domain, d.key AS domain_key, cd.name AS confirmed_domain, "
+                "to_char(v.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS created "
+                "FROM hypothesis_version v JOIN domain d ON d.id = v.domain_id "
+                "LEFT JOIN domain cd ON cd.id = v.confirmed_domain_id WHERE v.hypothesis_id = :h "
+                "ORDER BY v.version_number DESC"), dict(h=h.id)).all():
+            runs = [{"run": r.id, "status_words": STATUS_WORDS[r.status],
+                     "evidence": run_view.evidence(r.evidence_level, None, None,
+                                                   bool((r.experiment_flags or {}).get("constructed_test_data")),
+                                                   failed=r.status == "failed")}
+                    for r in conn.execute(text("SELECT id, status, evidence_level, experiment_flags FROM run WHERE "
+                                               "hypothesis_version_id = :v ORDER BY id DESC"), dict(v=v.id)).all()]
+            versions.append({"version": v.version_number, "claim": v.text, "status": v.status,
+                             "status_words": VERSION_STATUS_WORDS[v.status], "note": v.note,
+                             "review_comment": v.review_comment, "created": v.created,
+                             "domain": v.confirmed_domain or v.domain, "domain_key": v.domain_key,
+                             "sufficiency_key": v.sufficiency_option,
+                             "sufficiency": SUFFICIENCY_WORDS.get(v.sufficiency_option, v.sufficiency_option),
+                             "sources": _sources(conn, v.id), "runs": runs})
+        cost = conn.execute(text("SELECT * FROM model_call_totals_by_query WHERE hypothesis_id = :h"),
+                            dict(h=h.id)).one_or_none()
+        open_run = conn.execute(text(
+            "SELECT EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE "
+            "hv.hypothesis_id = :h AND r.status IN ('queued', 'waiting', 'running'))"), dict(h=h.id)).scalar_one()
+        original = conn.execute(text(
+            "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h "
+            "ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=h.narrower_of_run_id)).scalar_one_or_none() \
+            if h.narrower_of_run_id else None
+    latest = versions[0]
+    c = dict(cost._mapping) if cost else {}
+    return {"number": h.number, "versions": versions, "latest": latest, "narrower_of": original,
+            "cost": {"calls": int(c.get("calls") or 0), "input_tokens": tokens(c.get("input_tokens")),
+                     "output_tokens": tokens(c.get("output_tokens")), "counted": money(c.get("cap_cost"))},
+            "can_edit": latest["status"] in ("draft", "returned"), "can_submit": latest["status"] == "draft",
+            "can_review": latest["status"] == "submitted",
+            "can_dispatch_again": latest["status"] == "dispatched" and not open_run}
+
+
+def form_options(engine: Engine) -> dict:
+    """What the new-query form offers: the domains (supported or not), the registered sources with their kind of
+    data, and the sufficiency options with the fixed minimums."""
+    from hypocurate.pipeline import profile
+    from hypocurate.sources.versions import SOURCES
+    with snapshot(engine) as conn:
+        domains = [dict(r._mapping) for r in conn.execute(text(
+            "SELECT key, name, supported FROM domain ORDER BY supported DESC, name")).all()]
+        sources = [dict(r._mapping) for r in conn.execute(text(
+            "SELECT key, name, data_kind, enabled, adapter_status FROM source ORDER BY enabled DESC, key")).all()]
+    for s in sources:
+        d = SOURCES.get(s["key"])
+        s["constructed"] = bool(d and d.constructed)
+    m = profile.FIXED_MINIMUMS
+    return {"domains": domains, "sources": sources,
+            "sufficiency": [
+                {"key": "fixed_minimum", "words": SUFFICIENCY_WORDS["fixed_minimum"],
+                 "detail": f"{m['min_records']} records, {m['min_alloys']} alloys with at least 2 grain sizes, "
+                           f"{m['min_groups']} informative groups, {m['min_resid_df']} residual degrees of freedom"},
+                {"key": "use_available", "words": SUFFICIENCY_WORDS["use_available"],
+                 "detail": "the minimums are waived, never the validity checks; the result is labelled exploratory"}]}
+
+
+def review_list(engine: Engine) -> list[dict]:
+    """The review picker (PRD 9.3): every submitted version, newest first."""
+    with snapshot(engine) as conn:
+        return [dict(r._mapping) for r in conn.execute(text(
+            "SELECT h.number, v.version_number AS version, v.text AS claim, d.name AS domain, "
+            "to_char(v.submitted_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS submitted "
+            "FROM hypothesis_version v JOIN hypothesis h ON h.id = v.hypothesis_id JOIN domain d ON d.id = v.domain_id "
+            "WHERE v.status = 'submitted' ORDER BY v.submitted_at DESC, v.id DESC")).all()]
+
+
+def review_page(engine: Engine, number: str) -> dict:
+    """One submitted version for review (PRD 9.3): the hypothesis, the domain to confirm or change, the sufficiency
+    option, the chosen sources, the latest stored settings version of each role a run records, the caps, the note."""
+    from hypocurate.pipeline.agents import settings, spend
+    page = query_page(engine, number)
+    latest = page["latest"]
+    if latest["status"] != "submitted":
+        return {**page, "reviewable": False}
+    with snapshot(engine) as conn:
+        version_id, domain_key = conn.execute(text(
+            "SELECT v.id, d.key FROM hypothesis_version v JOIN hypothesis h ON h.id = v.hypothesis_id JOIN domain d "
+            "ON d.id = v.domain_id WHERE h.number = :n AND v.status = 'submitted'"), dict(n=number)).one()
+        agents = [{"role": role, "version": conn.execute(text(
+            "SELECT max(version) FROM agent_setting WHERE role = :r"), dict(r=role)).scalar_one()}
+            for role in settings.RUN_ROLES]
+    return {**page, "reviewable": True, "version_id": version_id, "domain_key": domain_key,
+            "options": form_options(engine), "agents": agents,
+            "caps": {"per_run": money(spend.RUN_CAP_USD), "monthly": money(spend.MONTH_CAP_USD)},
+            "queue": run_view.queue_rows(engine)}
+
diff --git a/hypocurate/pipeline/reading.py b/hypocurate/pipeline/reading.py
index a578756..f747750 100644
--- a/hypocurate/pipeline/reading.py
+++ b/hypocurate/pipeline/reading.py
@@ -127,6 +127,30 @@ def stored(conn: Connection, run_id: int) -> dict | None:
     return _confirmed(conn, run_id, tested, locked=run.plan is not None)
 
 
+# Step 10b (owner, 2026-10-11): where a run's question as tested came from, in short words for the runs list, from
+# what is stored (the run's fixed-plan flag, its narrower link, its locked plan, its confirmation), never a guess.
+PROVENANCE_WORDS = {"fixed": "fixed reference plan", "narrower": "narrower question, built by code from run {run}",
+                    "planner": "Planner's reading", "confirmed": "Planner's reading, confirmed by {by}",
+                    "predates": "Planner's reading; predates confirmation"}  # narrower: owner's wording, 2026-10-11
+
+
+def provenance(conn: Connection, run_id: int) -> str:
+    """The short provenance of a run's question as tested (the run page's label, shortened)."""
+    row = conn.execute(text(
+        "SELECT r.fixed_plan, h.narrower_of_run_id AS narrower, "
+        "EXISTS (SELECT 1 FROM plan p WHERE p.run_id = r.id) AS locked, "
+        "(SELECT confirmed_by FROM rules_confirmation rc WHERE rc.run_id = r.id) AS confirmed_by FROM run r "
+        "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+        "WHERE r.id = :r"), dict(r=run_id)).one()
+    if row.narrower is not None:
+        return PROVENANCE_WORDS["narrower"].format(run=row.narrower)
+    if row.fixed_plan:
+        return PROVENANCE_WORDS["fixed"]
+    if row.confirmed_by:
+        return PROVENANCE_WORDS["confirmed"].format(by=row.confirmed_by)
+    return PROVENANCE_WORDS["predates"] if row.locked else PROVENANCE_WORDS["planner"]
+
+
 def _confirmed(conn: Connection, run_id: int, tested: dict, locked: bool = False) -> dict:
     """The reading with its label once a person confirmed it (owner, 2026-10-08, question 2); a Planner reading locked
     with no confirmation (only possible before step 9a's migration 0007) says that it predates confirmation (owner,
diff --git a/hypocurate/pipeline/run_view.py b/hypocurate/pipeline/run_view.py
index 0ad84bb..5ef096a 100644
--- a/hypocurate/pipeline/run_view.py
+++ b/hypocurate/pipeline/run_view.py
@@ -18,7 +18,7 @@ from typing import Any, Iterator, Mapping
 from sqlalchemy import Connection, Engine, text
 
 from hypocurate.db.models import TEST_RUN_LABEL
-from hypocurate.pipeline import display, progress
+from hypocurate.pipeline import display, failure_words, progress
 from hypocurate.pipeline import statistics as st
 
 # What a run's status is called on the screens (step 10a; the live-run record's open item 3: a waiting run is shown as
@@ -42,25 +42,30 @@ SET_DISPLAY_NAMES = {
     "no_exclusions": "with no exclusion rules",
     "tension_and_compression": "with tension and compression tests",
     "six_batches_as_groups": "with Texas A&M grouped by its six batches",
-    "same_alloy_1_at_pct": "with alloys matched at 1 at.%",
+    "same_alloy_1_at_pct": "with alloys matched at 1 atomic percent (at.%)",
     "source_only_assignments": "with values assigned from the source only",
     "scope_not_confirmed_included": "with records of unconfirmed scope included",
     "possible_duplicates_separate": "with possible duplicates counted separately",
     "conflicts_survivor_value": "with conflicting values counted once (survivor rule)",
 }
-# The one change of each set, in words for people (the eligibility code's own description, `SENSITIVITY_CHANGES`,
-# names internal sets; the ninth set's description is that one, which names none).
+# The one change of each set, in words for people, and what the main result does instead (owner's review,
+# 2026-10-11). The main result's rule is read from the run's locked plan ({…} filled by `_set_description`).
 SET_DESCRIPTIONS = {
-    "no_exclusions": "The plan's exclusion rules are dropped; the scope is kept.",
-    "tension_and_compression": "Tests in tension and in compression are both accepted.",
-    "six_batches_as_groups": "The Texas A&M records are grouped by their six batches instead of as one group; the "
-                             "records are the same.",
-    "same_alloy_1_at_pct": "Compositions are rounded to 1 at.% when deciding whether two records are the same alloy.",
-    "source_only_assignments": "Only values converted or assigned from the source are accepted; values assigned by "
-                               "decision are left out.",
-    "scope_not_confirmed_included": "Records whose scope cannot be confirmed are treated as in scope.",
+    "no_exclusions": "The plan's exclusion rules are dropped ({exclusions}); the main result applies them. The scope is "
+                     "kept.",
+    "tension_and_compression": "Tests in tension and in compression are both accepted, instead of {test_types} only, "
+                               "as in the main result.",
+    "six_batches_as_groups": "The Texas A&M records are grouped by their six batches, instead of as one group (the "
+                             "whole dataset), as in the main result; the records are the same.",
+    "same_alloy_1_at_pct": "Compositions are rounded to 1 at.% when deciding whether two records are the same alloy, "
+                           "instead of to {main_rounding} at.%, as in the main result.",
+    "source_only_assignments": "Only values converted or assigned from the source are accepted; the main result also "
+                               "accepts values assigned by decision.",
+    "scope_not_confirmed_included": "Records whose scope cannot be confirmed are treated as in scope; the main result "
+                                    "leaves them out.",
     "possible_duplicates_separate": "Records in unresolved or possible duplicate groups count as separate "
-                                    "measurements.",
+                                    "measurements; in the main result a possible duplicate group counts once (by the "
+                                    "survivor rule) and an unresolved one is left out.",
     # Owner's wording (2026-10-11): say that these values are normally left out.
     "conflicts_survivor_value": "Conflicting values, left out of the main result, are included once each, using the "
                                 "survivor's value.",
@@ -71,6 +76,7 @@ STAGE_NAMES = {"planner": "Planner", "narrowing": "narrowing decision (code)", "
                "gap_facts": "gap facts (code)", "analyst": "Analyst"}
 OPEN_STATUSES = ("queued", "waiting", "running")  # the screens update these by themselves (static/poll.js)
 NOT_COMPLETED = "No evidence level yet (not completed)"
+NOT_REACHED = "not searched (the run ended first)"
 FAILED_NO_LEVEL = "failed: no evidence level"  # owner, 2026-10-11
 # The stored label of a marked run (register 'constructed_test_runs'), shown as it is stored.
 TEST_RUN_BADGE = TEST_RUN_LABEL
@@ -90,11 +96,21 @@ def snapshot(engine: Engine) -> Iterator[Connection]:
             yield conn
 
 
-def _set_description(key: str | None) -> str:
+def _set_description(key: str | None, plan: Mapping | None = None) -> str:
+    """The set's one change and what the main result does instead, with the main result's rule from `plan` (the run's
+    locked plan; the profile's defaults when none is given)."""
+    from hypocurate.pipeline import plan as plans
+    from hypocurate.pipeline import reading
     from hypocurate.pipeline.eligibility import INFLUENCE_KEY, SENSITIVITY_CHANGES
     if key == INFLUENCE_KEY:
-        return SENSITIVITY_CHANGES[INFLUENCE_KEY][:1].upper() + SENSITIVITY_CHANGES[INFLUENCE_KEY][1:] + "."
-    return SET_DESCRIPTIONS.get(key or "", "")
+        return (SENSITIVITY_CHANGES[INFLUENCE_KEY][:1].upper() + SENSITIVITY_CHANGES[INFLUENCE_KEY][1:]
+                + "; the main result keeps them.")
+    p = plan or plans.reference_plan(0)
+    rules = p.get("exclusion_rules") or []
+    values = {"exclusions": "; ".join(reading.exclusion_words(r) for r in rules) if rules else "none in this plan",
+              "test_types": " and ".join(p["scope"]["test_type"]),
+              "main_rounding": f"{10 ** -p['rules']['same_alloy_decimals']:g}"}
+    return SET_DESCRIPTIONS.get(key or "", "").format(**values)
 
 
 def _set_display_name(key: str | None) -> str:
@@ -155,8 +171,8 @@ def queue_rows(engine: Engine) -> list[dict]:
     out = []
     with engine.connect() as conn:
         runs = conn.execute(text(
-            "SELECT r.id, r.status, h.number, EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS "
-            "confirmed, c.worker, extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age, "
+            "SELECT r.id, r.status, h.number, r.experiment_flags, EXISTS (SELECT 1 FROM rules_confirmation rc WHERE "
+            "rc.run_id = r.id) AS confirmed, c.worker, extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age, "
             "(SELECT count(*) FROM run_claim x WHERE x.run_id = r.id AND x.released_at IS NOT NULL AND "
             "x.release_reason NOT IN ('waiting', 'finished')) AS recoveries FROM run r "
             "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
@@ -173,7 +189,9 @@ def queue_rows(engine: Engine) -> list[dict]:
                 "worker": r.worker, "heartbeat_age_seconds": round(float(r.heartbeat_age), 1)
                 if r.heartbeat_age is not None else None,
                 "seconds_since_last_write": round(progress.seconds_since_last_write(conn, r.id), 1),
-                "recoveries": int(r.recoveries)})
+                "recoveries": int(r.recoveries),
+                # Step 10b (register 'constructed_test_runs'): the label on every list.
+                "test_run": bool((r.experiment_flags or {}).get("constructed_test_data"))})
     return out
 
 
@@ -281,7 +299,7 @@ def _counts_words(e: Mapping) -> dict:
             "informative": c.get("n_groups_informative"), "resid_df": c.get("resid_df")}
 
 
-def _tables(stats: Mapping, kinds: Mapping[str, str]) -> dict:
+def _tables(stats: Mapping, kinds: Mapping[str, str], plan: Mapping | None = None) -> dict:
     """Per-source and sensitivity rows from the stored statistics output (the order `statement` uses)."""
     from hypocurate.pipeline import analyst_names as an
     from hypocurate.pipeline.statement import _ordered, _source_name
@@ -306,7 +324,7 @@ def _tables(stats: Mapping, kinds: Mapping[str, str]) -> dict:
         against = "—"
         if inference and e.get("estimate") is not None:
             against = an.label_words({**e, "label": st.label(e, pooled, alpha)})
-        sensitivity.append({"name": _set_display_name(e.get("set")), "change": _set_description(e.get("set")),
+        sensitivity.append({"name": _set_display_name(e.get("set")), "change": _set_description(e.get("set"), plan),
                             **_counts_words(e), "result": _result_words(e, withheld), "against": against})
     return {"pooled": pooled, "per_source": per_source, "sensitivity": sensitivity}
 
@@ -373,7 +391,8 @@ def run_page_in(conn: Connection, run_id: int) -> dict | None:
     tags = conn.execute(text(
         "SELECT tv.kind, tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r "
         "ORDER BY tv.kind, tv.value"), dict(r=run_id)).all()
-    plan = conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
+    locked = conn.execute(text("SELECT fingerprint, content FROM plan WHERE run_id = :r"), dict(r=run_id)).one_or_none()
+    plan = locked.fingerprint if locked else None
     freeze = conn.execute(text("SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r"),
                           dict(r=run_id)).one_or_none()
     locked_at, frozen_at = _time(conn, "locked_at", "plan", run_id), _time(conn, "frozen_at", "run_snapshot", run_id)
@@ -392,7 +411,7 @@ def run_page_in(conn: Connection, run_id: int) -> dict | None:
     facts = _claim_facts(conn, run_id) if head.status in ("queued", "waiting", "running") else None
     test_run = bool((head.experiment_flags or {}).get("constructed_test_data"))
     cost = shown["tokens_and_cost"] or {}
-    tables = _tables(stats or {}, kinds)
+    tables = _tables(stats or {}, kinds, locked.content if locked else None)
     return {
         "run": run_id, "query": shown["query"], "version": head.version_number, "claim": shown["claim"],
         "status": head.status, "status_words": STATUS_WORDS[head.status],
@@ -415,9 +434,12 @@ def run_page_in(conn: Connection, run_id: int) -> dict | None:
         "checkpoints": {"rules_lock": {"at": locked_at, "fingerprint": plan},
                         "dataset_freeze": {"at": frozen_at, "fingerprint": freeze.fingerprint if freeze else None,
                                            "records": freeze.n_records if freeze else None}},
-        "sources": [{"name": s.name, "status": s.search_status.replace("_", " "),
+        "failure_plain": failure_words.explain(conn, run_id, shown["failure"]) if head.status == "failed" else None,
+        # Owner, 2026-10-11: a source a run never reached because it ended first is "not searched", never "pending".
+        "sources": [{"name": s.name, "status": (NOT_REACHED if s.search_status == "pending" and head.status in
+                                                ("completed", "failed") else s.search_status.replace("_", " ")),
                      "nothing_found": s.nothing_found.replace("_", " ") if s.nothing_found else None} for s in sources],
-        "flags": shown["flags"],
+        "flags": [{**f, "kind_words": f["kind"].replace("_", " ")} for f in shown["flags"]],
         "stages": [{"name": STAGE_NAMES.get(s.stage, s.stage), "attempt": s.attempt, "status": s.status,
                     "model": s.model, "calls": int(s.calls or 0), "input_tokens": tokens(s.input_tokens),
                     "output_tokens": tokens(s.output_tokens), "cost": money(s.reported_cost)} for s in stages],
@@ -441,23 +463,28 @@ def runs_list(engine: Engine, before: int | None = None, per_page: int = RUNS_PE
     re-check: an offset shifted when runs were added between pages, repeating some and never reaching others; a run's
     id never changes, so following "older runs" goes through every run that existed when the list was opened exactly
     once). One snapshot for the count and the rows."""
+    from hypocurate.pipeline import reading
     if before is not None and before < 1:
         raise NoSuchPage(f"no runs before run {before}")
     with snapshot(engine) as conn:
         total = conn.execute(text("SELECT count(*) FROM run")).scalar_one()
         rows = conn.execute(text(
             "SELECT r.id, r.status, r.evidence_level, r.verdict, r.experiment_flags, h.number, hv.text, "
-            "r.outcome, to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS queued, "
+            "r.outcome, r.failure_reason, "
+            "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS queued, "
             "coalesce(t.cap_cost, 0) AS cost FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
             "JOIN hypothesis h ON h.id = hv.hypothesis_id LEFT JOIN model_call_totals_by_run t ON t.run_id = r.id "
             "WHERE CAST(:before AS bigint) IS NULL OR r.id < :before ORDER BY r.id DESC LIMIT :n"),
             dict(before=before, n=per_page + 1)).all()  # one more than shown: is there an older page?
-    more, rows = len(rows) > per_page, rows[:per_page]
+        more, rows = len(rows) > per_page, rows[:per_page]
+        plans = {r.id: reading.provenance(conn, r.id) for r in rows}  # step 10b: the "Plan" column, same snapshot
+        failures = {r.id: failure_words.explain(conn, r.id, r.failure_reason) for r in rows if r.status == "failed"}
     out = []
     for r in rows:
         test_run = bool((r.experiment_flags or {}).get("constructed_test_data"))
-        out.append({"run": r.id, "query": r.number, "claim": r.text, "status": r.status,
-                    "status_words": STATUS_WORDS[r.status], "queued": r.queued,
+        out.append({"run": r.id, "query": r.number, "claim": r.text, "status": r.status, "plan": plans[r.id],
+                    "status_words": failures[r.id]["short"] if r.id in failures else STATUS_WORDS[r.status],
+                    "queued": r.queued,
                     "outcome": r.outcome.replace("_", " ") + " in the sources searched" if r.outcome else None,
                     "evidence": evidence(r.evidence_level, None, None, test_run, failed=r.status == "failed"),
                     "cost": money(r.cost)})
diff --git a/hypocurate/pipeline/workbook.py b/hypocurate/pipeline/workbook.py
new file mode 100644
index 0000000..d61aa86
--- /dev/null
+++ b/hypocurate/pipeline/workbook.py
@@ -0,0 +1,241 @@
+"""The run's workbook and records CSV (PRD 11; build step 10b): built on request from stored rows, never stored; the
+same function serves the website's download and the command line's `export`.
+
+Four sheets:
+- **Records used:** one row per record in the test (the primary set): source, item, alloy, kind of data, paper, each
+  harmonized value with its unit and status (and the citation of a value assigned from the source or by decision),
+  and the values as originally reported.
+- **Records not used:** every other record the run found, with the same columns, the rule that decided it, the flags
+  code raised on it, and the sensitivity sets that use it.
+- **Significance and commentary:** code's results statement, the calibration with its assumptions, and the commentary
+  (none in sprint 1: the Commentator is step 12).
+- **Run summary:** the query and version, domain and tags, the locked plan, the rules lock and dataset freeze (times
+  and fingerprints), each result (pooled, per source, sensitivity sets by name), the outcome, the sources searched
+  and not, tokens and cost per stage and in total, the agent mode and settings versions, the source versions.
+Every sheet's first line states the workbook's format and the code version that built it. The workbook's document
+dates are the run's dispatch time; the same stored rows give the same cells (the zip file's own timestamps, written by
+the spreadsheet library, are not fixed, so the bytes may differ). Read in one snapshot.
+"""
+from __future__ import annotations
+
+import csv
+import io
+import json
+from datetime import datetime, timezone
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.pipeline import plot, run_view
+from hypocurate.pipeline.eligibility import PRIMARY
+from hypocurate.pipeline.run_view import snapshot
+
+WORKBOOK_FORMAT = 1
+SHEETS = ("Records used", "Records not used", "Significance and commentary", "Run summary")
+BASE_COLUMNS = ("record", "source", "item", "alloy", "kind of data", "paper reference", "paper DOI")
+COMMENTARY_NONE = "No commentary: the Commentator is not built in sprint 1 (PRD 15, step 12)."
+
+
+def version_line() -> str:
+    return plot.version_line("Workbook", WORKBOOK_FORMAT)
+
+
+def _value(entry: Any) -> Any:
+    if not isinstance(entry, Mapping):
+        return None
+    v = entry.get("value")
+    if isinstance(v, Mapping):  # a composition: element and atomic percent
+        return " ".join(f"{k}{amount:g}" for k, amount in sorted(v.items()))
+    return v
+
+
+def _citation(entry: Any) -> str | None:
+    c = entry.get("citation") if isinstance(entry, Mapping) else None
+    if not isinstance(c, Mapping):
+        return None
+    return "; ".join(str(c[k]) for k in ("document", "location", "quote") if c.get(k))
+
+
+def _reported(reported: Any) -> str:
+    if not isinstance(reported, Mapping):
+        return ""
+    return "; ".join(f"{k}: {v.get('text')}" + (f" {v['unit']}" if v.get("unit") else "")
+                     for k, v in sorted(reported.items()) if isinstance(v, Mapping))
+
+
+def _records(conn: Connection, run_id: int) -> tuple[list[dict], list[str]]:
+    rows = conn.execute(text(
+        "SELECT r.id, s.key AS source, r.source_item_key, r.alloy, r.kind, r.paper_reference, r.paper_doi, "
+        "r.harmonized, r.reported, rr.eligible, rr.rule FROM record r JOIN source_version sv ON sv.id = "
+        "r.source_version_id JOIN source s ON s.id = sv.source_id LEFT JOIN run_record rr ON rr.run_id = :r AND "
+        "rr.record_id = r.id WHERE r.extraction_run_id = :r ORDER BY s.key, r.id"), dict(r=run_id)).all()
+    sets: dict[int, list[str]] = {}
+    for key, rid in conn.execute(text(
+            "SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
+            "WHERE a.run_id = :r ORDER BY a.key"), dict(r=run_id)).all():
+        sets.setdefault(rid, []).append(key)
+    flags: dict[int, list[str]] = {}
+    for kind, category, rid in conn.execute(text(
+            "SELECT f.kind, f.category, fr.record_id FROM flag f JOIN flag_record fr ON fr.flag_id = f.id "
+            "WHERE f.run_id = :r ORDER BY f.id"), dict(r=run_id)).all():
+        flags.setdefault(rid, []).append(kind.replace("_", " ") + (f" ({category})" if category else ""))
+    fields = sorted({f for r in rows if isinstance(r.harmonized, Mapping) for f in r.harmonized})
+    out = []
+    for r in rows:
+        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
+        row = {"record": r.id, "source": r.source, "item": r.source_item_key, "alloy": r.alloy, "kind of data": r.kind,
+               "paper reference": r.paper_reference, "paper DOI": r.paper_doi}
+        for f in fields:
+            e = h.get(f)
+            row[f] = _value(e)
+            row[f"{f} unit"] = e.get("unit") if isinstance(e, Mapping) else None
+            row[f"{f} status"] = (e.get("status") or "").replace("_", " ") if isinstance(e, Mapping) else "missing"
+            row[f"{f} citation"] = _citation(e)
+        row["values as reported"] = _reported(r.reported)
+        in_sets = sets.get(r.id, [])
+        row["_used"] = PRIMARY in in_sets
+        row["eligible"] = {True: "yes", False: "no", None: "not decided"}[r.eligible]
+        row["rule"] = (r.rule or "").replace("_", " ") or None
+        row["flags"] = "; ".join(flags.get(r.id, [])) or None
+        row["sensitivity sets"] = "; ".join(run_view._set_display_name(k) for k in in_sets
+                                            if k != PRIMARY) or None
+        out.append(row)
+    columns = list(BASE_COLUMNS)
+    for f in fields:
+        columns += [f, f"{f} unit", f"{f} status", f"{f} citation"]
+    columns.append("values as reported")
+    return out, columns
+
+
+def _summary(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
+    page = run_view.run_page_in(conn, run_id)
+    head = conn.execute(text(
+        "SELECT r.agent_mode, r.experiment_flags, to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS "
+        "queued, to_char(r.started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS started, "
+        "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS ended "
+        "FROM run r WHERE r.id = :r"), dict(r=run_id)).one()
+    plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
+    settings = conn.execute(text(
+        "SELECT ras.role, ag.version FROM run_agent_setting ras JOIN agent_setting ag ON ag.id = ras.agent_setting_id "
+        "WHERE ras.run_id = :r ORDER BY ras.role"), dict(r=run_id)).all()
+    versions = conn.execute(text(
+        "SELECT s.key, sv.label, sv.fingerprint, rs.search_status FROM run_source rs JOIN source s ON s.id = "
+        "rs.source_id LEFT JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r ORDER BY s.key"),
+        dict(r=run_id)).all()
+    cp = page["checkpoints"]
+    rows: list[tuple[str, Any]] = [
+        ("Query", f"{page['query']}, version {page['version']}"), ("Run", run_id),
+        ("Hypothesis", page["claim"]), ("Domain", page["domain"]), ("Tags", "; ".join(page["tags"]) or None),
+        ("Status", page["status_words"]), ("Outcome", page["outcome"]), ("Verdict", page["verdict"]),
+        ("Evidence level", page["evidence"]["words"]),
+        ("Question as tested", (page["question_as_tested"] or {}).get("text")),
+        ("Its source", (page["question_as_tested"] or {}).get("label")),
+        ("Test run", run_view.TEST_RUN_BADGE if page["test_run"] else "no"),
+        ("Failure", page["failure_plain"]["words"] if page.get("failure_plain") else None),
+        ("Failure, technical detail", page["failure_plain"]["technical"] if page.get("failure_plain") else None),
+        ("Rules lock", f"{cp['rules_lock']['at']}; fingerprint {cp['rules_lock']['fingerprint']}"
+         if cp["rules_lock"]["at"] else "not reached"),
+        ("Dataset freeze", f"{cp['dataset_freeze']['at']}; {cp['dataset_freeze']['records']} records; fingerprint "
+                           f"{cp['dataset_freeze']['fingerprint']}" if cp["dataset_freeze"]["at"] else "not reached"),
+        ("Locked plan", json.dumps(plan, sort_keys=True, ensure_ascii=False) if plan else None)]
+    for x in page["per_source"]:
+        rows.append((f"Result: {x['name']}", f"{x['records']} records, {x['alloys']} alloys, {x['groups']} groups; "
+                                              f"{x['result']}; {x['against']}"))
+    for x in page["sensitivity"]:
+        rows.append((f"Sensitivity: {x['name']}", f"{x['records']} records; {x['result']}; {x['against']}"))
+    for v in versions:
+        rows.append((f"Source: {v.key}", f"{v.search_status.replace('_', ' ')}; version {v.label or '—'}; "
+                                         f"fingerprint {v.fingerprint or '—'}"))
+    for s in page["stages"]:
+        rows.append((f"Stage: {s['name']} (attempt {s['attempt']})", f"{s['status']}; model {s['model'] or '—'}; "
+                     f"{s['calls']} calls; {s['input_tokens']} input and {s['output_tokens']} output tokens; {s['cost']}"))
+    c = page["cost"]
+    rows += [("Total", f"{c['calls_words']}; {c['input_tokens']} input and {c['output_tokens']} output tokens; "
+                       f"reported {c['reported']}; counted toward the caps {c['counted']}"),
+             ("Agent mode", head.agent_mode.replace("_", " ")),
+             ("Agent settings versions", "; ".join(f"{r.role} {r.version}" for r in settings) or None),
+             ("Dispatched (UTC)", head.queued), ("Started (UTC)", head.started), ("Ended (UTC)", head.ended)]
+    return rows
+
+
+def _significance(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
+    page = run_view.run_page_in(conn, run_id)
+    st = page["statement"]
+    rows = [("Results statement (written by code)", line) for line in st["body"] + st["cautions"] + st["format"]]
+    if not rows:
+        rows.append(("Results statement (written by code)", "None: the run did not complete."))
+    stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND status = "
+                              "'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none() or {}
+    pooled = next((a for a in stats.get("analyses") or [] if a.get("scope") == "pooled"), None)
+    for method, c in sorted(((pooled or {}).get("calibration") or {}).items()):
+        if c.get("status") != "computed":
+            rows.append((f"Calibration ({method})", f"unavailable: {str(c.get('reason') or '').replace('_', ' ')}"))
+            continue
+        rows.append((f"Calibration ({method})",
+                     f"no effect: significant in {c['null']['significant']} of {c['n_simulations']} "
+                     f"({c['null']['share']:.4f}; 95% interval {c['null']['ci_low']:.4f} to {c['null']['ci_high']:.4f}); "
+                     f"smallest effect that matters: {c['effect']['share']:.4f}; flag: "
+                     f"{(c.get('flag_wording') or c.get('confidence_flag') or 'none')}; seed {c.get('seed')}"))
+        rows.append((f"Calibration assumptions ({method})", json.dumps(c.get("assumptions"), sort_keys=True,
+                                                                         ensure_ascii=False)))
+    if not pooled:
+        rows.append(("Calibration", "unavailable: no dataset was frozen" if page["checkpoints"]["dataset_freeze"]["at"]
+                     is None else "unavailable"))
+    rows.append(("Commentary", COMMENTARY_NONE))
+    analyst = page.get("analyst") or {}
+    if analyst.get("text"):
+        rows.append(("Explanation by the Analyst", f"[{analyst['label']}] {analyst['text']}"))
+    return rows
+
+
+def _dispatched(conn: Connection, run_id: int) -> datetime:
+    t = conn.execute(text("SELECT queued_at FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
+    return t.astimezone(timezone.utc).replace(tzinfo=None)
+
+
+def build(engine: Engine, run_id: int) -> bytes | None:
+    """The workbook (.xlsx) of a run, or None for an unknown run."""
+    from openpyxl import Workbook
+    with snapshot(engine) as conn:
+        if conn.execute(text("SELECT 1 FROM run WHERE id = :r"), dict(r=run_id)).scalar() is None:
+            return None
+        records, columns = _records(conn, run_id)
+        significance, summary, when = _significance(conn, run_id), _summary(conn, run_id), _dispatched(conn, run_id)
+    wb = Workbook()
+    wb.remove(wb.active)
+    used = [r for r in records if r["_used"]]
+    other = [r for r in records if not r["_used"]]
+    for title, rows, extra in ((SHEETS[0], used, ()), (SHEETS[1], other, ("eligible", "rule", "flags",
+                                                                           "sensitivity sets"))):
+        ws = wb.create_sheet(title)
+        ws.append([version_line()])
+        ws.append([*columns, *extra])
+        for r in rows:
+            ws.append([r.get(c) for c in (*columns, *extra)])
+    for title, rows in ((SHEETS[2], significance), (SHEETS[3], summary)):
+        ws = wb.create_sheet(title)
+        ws.append([version_line()])
+        ws.append(["Item", "Value"])
+        for item, value in rows:
+            ws.append([item, value])
+    wb.properties.created = wb.properties.modified = when
+    wb.properties.creator = "HypoCurate"
+    out = io.BytesIO()
+    wb.save(out)
+    return out.getvalue()
+
+
+def records_csv(engine: Engine, run_id: int) -> str | None:
+    """Every record the run found, one row each, with whether it was used in the test."""
+    with snapshot(engine) as conn:
+        if conn.execute(text("SELECT 1 FROM run WHERE id = :r"), dict(r=run_id)).scalar() is None:
+            return None
+        records, columns = _records(conn, run_id)
+    buf = io.StringIO()
+    w = csv.writer(buf, lineterminator="\n")
+    w.writerow([f"# {version_line()}"])
+    header = [*columns, "used in the test", "eligible", "rule", "flags", "sensitivity sets"]
+    w.writerow(header)
+    for r in records:
+        w.writerow([r.get(c) if c != "used in the test" else ("yes" if r["_used"] else "no") for c in header])
+    return buf.getvalue()
diff --git a/hypocurate/web/app.py b/hypocurate/web/app.py
index 1f2cbca..1b9ee93 100644
--- a/hypocurate/web/app.py
+++ b/hypocurate/web/app.py
@@ -15,6 +15,7 @@ never affects a run (criterion 14.4).
 """
 from __future__ import annotations
 
+from decimal import Decimal, InvalidOperation
 from pathlib import Path
 
 from fastapi import FastAPI, Form, HTTPException, Query, Request
@@ -56,7 +57,15 @@ def _info(key: str) -> Markup:
         f'<span class="info-text" role="tooltip" id="{tip}" hidden>{Markup.escape(e["text"])}</span></span>')
 
 
-templates.env.globals.update(info=_info, dial=dial.svg)
+def _term(key: str) -> Markup:
+    """A glossary term's name with its information button (PRD 9.7)."""
+    return Markup(f'<span class="term">{Markup.escape(glossary.entry(key)["term"])}{_info(key)}</span>')
+
+
+# The terms of the results statement and the calibration, each with its button (PRD 9.7: every row of the record
+# of statistical significance has one).
+STATEMENT_TERMS = ("sig_estimate", "sig_test", "sig_validity", "sig_data", "sig_suff", "sig_source", "sig_other", "cal")
+templates.env.globals.update(info=_info, dial=dial.svg, term=_term, statement_terms=STATEMENT_TERMS)
 templates.env.filters.update(units=textfmt.units, model_text=textfmt.model_text)
 
 
@@ -177,7 +186,15 @@ def create_app(
         shown = run_view.run_page(engine, run_id)
         if shown is None:
             raise HTTPException(status_code=404, detail=f"no run {run_id}")
-        return page(request, "run.html", {"r": shown, "message": DONE.get(request.query_params.get("done", ""))})
+        figure = None
+        if shown["status"] == "completed":  # step 10b: the plot, built on request from stored rows
+            from hypocurate.pipeline import plot
+            d = plot.data(engine, run_id)
+            figure = {**d, "svg": plot.svg(d) if d.get("plot") else None,
+                      "svg_narrow": plot.svg(d, "narrow") if d.get("plot") else None,
+                      "legend": plot.legend(d) if d.get("plot") else []}
+        return page(request, "run.html", {"r": shown, "plot": figure,
+                                          "message": DONE.get(request.query_params.get("done", ""))})
 
     @app.get("/runs/{run_id}/state", response_class=HTMLResponse)
     def run_state(request: Request, run_id: int):
@@ -190,6 +207,27 @@ def create_app(
             "r": shown, "csrf_token": security.csrf_token(request), "csrf_field": security.CSRF_FIELD},
             headers={"Cache-Control": "no-store"})
 
+    @app.get("/runs/{run_id}/workbook")
+    def run_workbook(request: Request, run_id: int):
+        """PRD 11: the run's workbook, built on request from stored rows."""
+        from hypocurate.pipeline import workbook
+        data = workbook.build(engine, run_id)
+        if data is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
+                        headers={"Content-Disposition": f'attachment; filename="hypocurate-run-{run_id}.xlsx"',
+                                 "Cache-Control": "no-store"})
+
+    @app.get("/runs/{run_id}/records.csv")
+    def run_records_csv(request: Request, run_id: int):
+        from hypocurate.pipeline import workbook
+        data = workbook.records_csv(engine, run_id)
+        if data is None:
+            raise HTTPException(status_code=404, detail=f"no run {run_id}")
+        return Response(data, media_type="text/csv; charset=utf-8",
+                        headers={"Content-Disposition": f'attachment; filename="hypocurate-run-{run_id}-records.csv"',
+                                 "Cache-Control": "no-store"})
+
     @app.get("/runs/{run_id}/confirm", response_class=HTMLResponse)
     def confirm_form(request: Request, run_id: int):
         from hypocurate.pipeline import run_view
@@ -235,6 +273,248 @@ def create_app(
                         status_code=409)
         return RedirectResponse(f"/runs/{run_id}?done=cancelled", status_code=303)
 
+    # --- the query pages (step 10b; PRD 9.1 to 9.3) ----------------------------------------------------------------
+
+    def refused_words(error: Exception) -> str:
+        """A refusal in code's fixed words: a query refusal's reason, or the database's own fixed message."""
+        from sqlalchemy.exc import IntegrityError
+        from hypocurate.pipeline import queries
+        from hypocurate.pipeline.writes import database_message
+        if isinstance(error, queries.QueryRefused):
+            return error.reason
+        if isinstance(error, IntegrityError):
+            return database_message(error)
+        raise error
+
+    def form_values(form) -> dict:
+        return {"claim": form.get("claim", ""), "domain": form.get("domain", ""),
+                "sufficiency": form.get("sufficiency", "fixed_minimum"), "note": form.get("note", ""),
+                "sources": form.getlist("sources"), "action": form.get("action", "save")}
+
+    @app.get("/queries", response_class=HTMLResponse)
+    def queries_page(request: Request, before: int | None = Query(None)):
+        from hypocurate.pipeline import query_view
+        try:
+            listed = query_view.queries_list(engine, before)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        return page(request, "queries.html", {"listed": listed, "active": "queries"})
+
+    @app.get("/queries/new", response_class=HTMLResponse)
+    def new_query_form(request: Request):
+        from hypocurate.pipeline import query_view
+        return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": None,
+                                                 "values": None, "error": None, "active": "new"})
+
+    @app.post("/queries")
+    async def new_query(request: Request):
+        from hypocurate.pipeline import queries, query_view
+        form = await request.form()
+        security.check_csrf(request, form.get(security.CSRF_FIELD))
+        security.signed_in_name(request)
+        v = form_values(form)
+        try:
+            q = queries.create(engine, v["claim"], v["sources"], domain=v["domain"], sufficiency=v["sufficiency"],
+                               note=v["note"])
+            if v["action"] == "submit":
+                queries.submit(engine, q.version_id)
+        except Exception as error:  # noqa: BLE001 (refused_words re-raises anything that is not a fixed refusal)
+            return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": None,
+                                                     "values": v, "error": refused_words(error), "active": "new"},
+                        status_code=409)
+        return RedirectResponse(f"/queries/{q.number}", status_code=303)
+
+    @app.get("/queries/{number}", response_class=HTMLResponse)
+    def query_detail(request: Request, number: str):
+        from hypocurate.pipeline import query_view
+        try:
+            shown = query_view.query_page(engine, number)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        return page(request, "query.html", {"q": shown, "error": None, "active": "queries"})
+
+    @app.get("/queries/{number}/edit", response_class=HTMLResponse)
+    def edit_query_form(request: Request, number: str):
+        from hypocurate.pipeline import query_view
+        try:
+            shown = query_view.query_page(engine, number)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        latest = shown["latest"]
+        values = {"claim": latest["claim"], "note": latest["note"] or "", "sufficiency": latest["sufficiency_key"],
+                  "sources": [s["key"] for s in latest["sources"]], "domain": latest["domain_key"]}
+        return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
+                                                 "q": shown, "values": values, "error": None, "active": "queries"})
+
+    @app.post("/queries/{number}/edit")
+    async def edit_query(request: Request, number: str):
+        from hypocurate.pipeline import queries, query_view
+        form = await request.form()
+        security.check_csrf(request, form.get(security.CSRF_FIELD))
+        security.signed_in_name(request)
+        v = form_values(form)
+        try:
+            shown = query_view.query_page(engine, number)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        try:
+            change = queries.new_version if shown["latest"]["status"] == "returned" else queries.update_draft
+            vid = change(engine, number, v["claim"], v["sources"], v["domain"], v["sufficiency"], v["note"])
+            if v["action"] == "submit":
+                queries.submit(engine, vid)
+        except Exception as error:  # noqa: BLE001
+            return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
+                                                     "q": shown, "values": v, "error": refused_words(error),
+                                                     "active": "queries"}, status_code=409)
+        return RedirectResponse(f"/queries/{number}", status_code=303)
+
+    @app.post("/queries/{number}/again")
+    async def dispatch_again(request: Request, number: str):
+        from hypocurate.pipeline import queries, query_view
+        form = await request.form()
+        security.check_csrf(request, form.get(security.CSRF_FIELD))
+        security.signed_in_name(request)
+        try:
+            rid = queries.dispatch_again(engine, number)
+        except Exception as error:  # noqa: BLE001
+            try:
+                shown = query_view.query_page(engine, number)
+            except query_view.NoSuchQuery as missing:
+                raise HTTPException(status_code=404, detail=str(missing)) from None
+            return page(request, "query.html", {"q": shown, "error": f"Not dispatched: {refused_words(error)}",
+                                                "active": "queries"}, status_code=409)
+        return RedirectResponse(f"/runs/{rid}", status_code=303)
+
+    @app.get("/review", response_class=HTMLResponse)
+    def review_index(request: Request):
+        from hypocurate.pipeline import query_view, run_view
+        return page(request, "review.html", {"picker": query_view.review_list(engine), "q": None,
+                                             "queue": run_view.queue_rows(engine), "error": None, "active": "review"})
+
+    @app.get("/review/{number}", response_class=HTMLResponse)
+    def review_query(request: Request, number: str):
+        from hypocurate.pipeline import query_view
+        try:
+            shown = query_view.review_page(engine, number)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
+                                             "queue": shown.get("queue"), "error": None, "active": "review"})
+
+    async def review_action(request: Request, number: str, act):
+        from hypocurate.pipeline import query_view
+        form = await request.form()
+        security.check_csrf(request, form.get(security.CSRF_FIELD))
+        name = security.signed_in_name(request)
+        try:
+            shown = query_view.review_page(engine, number)
+        except query_view.NoSuchQuery as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        try:
+            if not shown["reviewable"]:
+                from hypocurate.pipeline.queries import QueryRefused
+                raise QueryRefused("not_submitted", f"query {number} is {shown['latest']['status_words']}; only a "
+                                                    "submitted query is reviewed")
+            return act(form, name, shown)
+        except Exception as error:  # noqa: BLE001
+            return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
+                                                 "queue": shown.get("queue"), "active": "review",
+                                                 "error": refused_words(error)}, status_code=409)
+
+    @app.post("/review/{number}/dispatch")
+    async def review_dispatch(request: Request, number: str):
+        from hypocurate.pipeline import queries
+
+        def act(form, name, shown):
+            ceiling = (form.get("ceiling") or "").strip()
+            try:
+                ceiling = Decimal(ceiling) if ceiling else None
+            except InvalidOperation:
+                raise queries.QueryRefused("ceiling", "the ceiling is a number of US dollars") from None
+            if ceiling is not None and not ceiling > 0:
+                raise queries.QueryRefused("ceiling", "the ceiling is a positive number of US dollars")
+            queries.confirm_domain(engine, shown["version_id"], by=name, domain=form.get("domain") or None,
+                                   where=queries.WEBSITE)
+            rid = queries.dispatch(engine, shown["version_id"], ceiling=ceiling)
+            return RedirectResponse(f"/runs/{rid}", status_code=303)
+
+        return await review_action(request, number, act)
+
+    @app.post("/review/{number}/return")
+    async def review_return(request: Request, number: str):
+        from hypocurate.pipeline import queries
+
+        def act(form, name, shown):
+            queries.return_for_edits(engine, shown["version_id"], by=name, comment=form.get("comment", ""))
+            return RedirectResponse(f"/queries/{number}", status_code=303)
+
+        return await review_action(request, number, act)
+
+    # --- data sources and agents (step 10b; PRD 9.5, 9.6) ---------------------------------------------------------
+
+    @app.get("/sources", response_class=HTMLResponse)
+    def sources_page(request: Request):
+        from hypocurate.pipeline import catalog_view
+        return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": None, "error": None,
+                                              "message": None, "active": "sources"})
+
+    @app.get("/sources/{key}/test", response_class=HTMLResponse)
+    def source_test(request: Request, key: str):
+        from hypocurate.pipeline import catalog_view
+        try:
+            report = catalog_view.connection_page(engine, key)
+        except Exception as error:  # noqa: BLE001 (an unknown or unregistered source: the reason in words)
+            return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": None,
+                                                  "message": None, "active": "sources",
+                                                  "error": f"Connection test not done for {key}: the source is not "
+                                                           "registered, or its sealed version could not be read."},
+                        status_code=409)
+        return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": report, "error": None,
+                                              "message": None, "active": "sources"})
+
+    @app.post("/sources/{key}/register")
+    async def source_register(request: Request, key: str):
+        """Registers a source defined in code (sources.versions.register; a safeguard write, with the CSRF token)."""
+        from hypocurate.pipeline import catalog_view
+        from hypocurate.sources import versions
+        form = await request.form()
+        security.check_csrf(request, form.get(security.CSRF_FIELD))
+        name = security.signed_in_name(request)
+        try:
+            done = versions.register(engine, key)
+        except versions.RegistrationError as error:
+            return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": None,
+                                                  "message": None, "active": "sources",
+                                                  "error": f"Not registered: {error}"}, status_code=409)
+        message = (f"{key} registered by {name}: version {done.label}, fingerprint {done.fingerprint[:12]}."
+                   if done.created else f"{key} was already registered with this version ({done.fingerprint[:12]}).")
+        return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": None, "error": None,
+                                              "message": message, "active": "sources"})
+
+    @app.get("/agents", response_class=HTMLResponse)
+    def agents_index(request: Request):
+        return RedirectResponse("/agents/planner", status_code=303)
+
+    @app.get("/agents/{role}", response_class=HTMLResponse)
+    def agent(request: Request, role: str):
+        from hypocurate.pipeline import catalog_view
+        shown = catalog_view.agent_page(engine, role)
+        if shown is None:
+            raise HTTPException(status_code=404, detail=f"no role {role}")
+        return page(request, "agent.html", {"a": shown, "active": "agents"})
+
+    @app.get("/help", response_class=HTMLResponse)
+    def help_page(request: Request, q: str = ""):
+        """PRD 9.7: every explanation, where it appears, searchable; read from the glossary file only."""
+        q = q.strip()
+        entries = list(glossary.entries())
+        shown = [e for e in entries if not q or q.lower() in (e["term"] + " " + e["text"] + " " + e["screen"]).lower()]
+        groups: dict[str, list] = {}
+        for e in shown:
+            groups.setdefault(e["screen"], []).append(e)
+        return page(request, "help.html", {"q": q, "shown": shown, "total": len(entries),
+                                           "groups": list(groups.items()), "active": "help"}, spending=False)
+
     @app.get("/health")
     def health(request: Request) -> Response:
         db_ok = database_reachable(engine)
diff --git a/hypocurate/web/static/style.css b/hypocurate/web/static/style.css
index 364be14..21a2e7d 100644
--- a/hypocurate/web/static/style.css
+++ b/hypocurate/web/static/style.css
@@ -113,3 +113,22 @@ dd ul { margin: 0; padding-left: 1.2em; }
 .info.flip .info-text { left: auto; right: 0; }
 table.runs td:nth-child(2) { white-space: nowrap; }
 .pages { display: flex; gap: 16px; align-items: baseline; margin: 1rem 0; }
+.query-form { margin: 1rem 0; } .query-form textarea { width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 4px; font: inherit; }
+fieldset { border: 1px solid var(--line); border-radius: 6px; margin: 12px 0; padding: 8px 12px; }
+legend { font-weight: 600; padding: 0 4px; }
+label.choice { display: block; margin: 4px 0; } label.choice input { width: auto; margin-right: 6px; }
+.badge.kind { background: #e8f3ea; color: var(--good); margin-left: 4px; }
+.review-grid { display: grid; grid-template-columns: 18rem 1fr; gap: 20px; align-items: start; }
+.picker ul { list-style: none; margin: 0; padding: 0; } .picker li { border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; }
+.picker li.current { border-color: var(--accent); background: #eef3fb; }
+@media (max-width: 60rem) { .review-grid { grid-template-columns: 1fr; } }
+.plot-box { overflow-x: auto; } svg.plot { height: auto; display: block; }
+svg.plot-wide { width: 100%; min-width: 540px; } svg.plot-narrow { display: none; width: 100%; }
+@media (max-width: 56rem) { svg.plot-wide { display: none; } svg.plot-narrow { display: block; } }
+@media (max-width: 48rem) { section { padding: 0.75rem; } .menu ul { flex-wrap: wrap; } }
+.legend { margin: 8px 0; padding-left: 1.2em; }
+.inline-form { display: inline; } .inline-form button { margin: 0 0 0 8px; padding: 4px 10px; }
+pre.instruction { white-space: pre-wrap; background: var(--panel); padding: 10px 12px; border-radius: 6px; font-size: 0.875rem; }
+nav.pages a[aria-current="page"] { font-weight: 600; text-decoration: none; }
+.terms .term { white-space: nowrap; }
+.help-entry { margin: 0 0 1rem; } .help-entry h3 { margin-bottom: 2px; }
diff --git a/hypocurate/web/templates/_state.html b/hypocurate/web/templates/_state.html
index def2101..13556f2 100644
--- a/hypocurate/web/templates/_state.html
+++ b/hypocurate/web/templates/_state.html
@@ -7,7 +7,11 @@
     {% if r.confirmed %}<p>Confirmed; waiting for a worker to take it up.</p>
     {% else %}<p>Waits for {{ r.waiting_for }}.</p>{% endif %}
   {% endif %}
-  {% if r.failure %}<p class="error">Failed: {{ r.failure }}</p>{% endif %}
+  {% if r.failure_plain %}
+  <p class="failure-words">{{ r.failure_plain.words }}</p>
+  {% if r.failure_plain.reasons %}<p>Code's reasons for refusing the Planner's answers: {% for x in r.failure_plain.reasons %}{{ x }}{% if not loop.last %}; {% endif %}{% endfor %}.</p>{% endif %}
+  <p class="muted small">{{ r.failure_plain.technical }}</p>
+  {% elif r.failure %}<p class="error">Failed: {{ r.failure }}</p>{% endif %}
   {% if r.claim_facts %}
   <dl class="facts">
     <dt>Worker</dt><dd>{{ r.claim_facts.worker or "none holds it" }}{% if r.claim_facts.claimed %} (since {{ r.claim_facts.claimed }}){% endif %}</dd>
diff --git a/hypocurate/web/templates/agent.html b/hypocurate/web/templates/agent.html
new file mode 100644
index 0000000..10c5b8e
--- /dev/null
+++ b/hypocurate/web/templates/agent.html
@@ -0,0 +1,32 @@
+{% extends "base.html" %}
+{% block title %}{{ a.name }} · Agents · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Agents {{ info("agents") }}</h1>
+<nav class="pages" aria-label="Roles">{% for r in a.roles %}<a href="/agents/{{ r.role }}"{% if r.role == a.role %} aria-current="page"{% endif %}>{{ r.name }}</a>{% endfor %}</nav>
+<section>
+  <h2>{{ a.name }}: settings {% if a.stored %}version {{ a.stored.version }}{% endif %} {{ info("agentversion") }}</h2>
+  <p class="muted">Read-only in sprint 1. A run records the settings version it used; editing and "save as new version" come later.</p>
+  {% if a.stored %}
+  <dl class="facts">
+    <dt>Model</dt><dd>{{ a.stored.model }}</dd>
+    <dt>Saved</dt><dd>{{ a.stored.created }}</dd>
+    <dt>Limits</dt><dd>{{ a.stored.limits|join("; ") or "none" }}</dd>
+    <dt>Role settings</dt><dd>{{ a.stored.settings|join("; ") or "none" }}</dd>
+  </dl>
+  <h3>Instruction</h3>
+  <pre class="instruction">{{ a.stored.instruction }}</pre>
+  {% else %}<p>No settings version is stored for this role yet; the first run that uses it records one.</p>{% endif %}
+</section>
+<section>
+  <h2>Fixed in code {{ info("fixed") }}</h2>
+  <h3>Receives</h3>
+  {% if a.receives %}{% for st in a.receives %}
+  <p><strong>At the {{ st.stage }} stage:</strong></p>
+  <ul>{% for f in st.fields %}<li><strong>{{ f.field }}</strong>: {{ f.words }}</li>{% endfor %}</ul>
+  {% endfor %}{% else %}<p>Nothing, at any stage.</p>{% endif %}
+  <h3>Returns</h3><p>{{ a.returns }}</p>
+  <h3>May call</h3><p>{{ a.may_call }}</p>
+  <h3>May not</h3><p>{{ a.may_not }}</p>
+</section>
+{% endblock %}
diff --git a/hypocurate/web/templates/base.html b/hypocurate/web/templates/base.html
index a4aba67..dbd0e0f 100644
--- a/hypocurate/web/templates/base.html
+++ b/hypocurate/web/templates/base.html
@@ -14,7 +14,13 @@
     <div class="brand">HypoCurate</div>
     <ul>
       <li><a href="/"{% if active == "home" %} aria-current="page"{% endif %}>Home</a></li>
+      <li><a href="/queries"{% if active == "queries" %} aria-current="page"{% endif %}>Queries</a></li>
+      <li><a href="/queries/new"{% if active == "new" %} aria-current="page"{% endif %}>New query</a></li>
+      <li><a href="/review"{% if active == "review" %} aria-current="page"{% endif %}>Review and dispatch</a></li>
       <li><a href="/runs"{% if active == "runs" %} aria-current="page"{% endif %}>Runs</a></li>
+      <li><a href="/agents"{% if active == "agents" %} aria-current="page"{% endif %}>Agents</a></li>
+      <li><a href="/sources"{% if active == "sources" %} aria-current="page"{% endif %}>Data sources</a></li>
+      <li><a href="/help"{% if active == "help" %} aria-current="page"{% endif %}>Help</a></li>
       <li><a href="/assumptions"{% if active == "assumptions" %} aria-current="page"{% endif %}>Assumptions</a></li>
     </ul>
     {% if spending %}
diff --git a/hypocurate/web/templates/help.html b/hypocurate/web/templates/help.html
new file mode 100644
index 0000000..7f14e0f
--- /dev/null
+++ b/hypocurate/web/templates/help.html
@@ -0,0 +1,21 @@
+{% extends "base.html" %}
+{% block title %}Help · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Help</h1>
+<p class="muted">Every explanation the information buttons show, in one place, from the one glossary file.</p>
+<form method="get" action="/help" class="help-search">
+  <label for="q">Search the explanations</label>
+  <input id="q" name="q" value="{{ q }}" type="search">
+  <button type="submit">Search</button>{% if q %} <a href="/help">Show all</a>{% endif %}
+</form>
+<p class="muted">{{ shown|length }} of {{ total }} explanations{% if q %} contain “{{ q }}”{% endif %}.</p>
+{% for screen, entries in groups %}
+<section>
+  <h2>{{ screen }}</h2>
+  {% for e in entries %}
+  <div class="help-entry" id="{{ e.key }}"><h3>{{ e.term }}</h3><p>{{ e.text }}</p></div>
+  {% endfor %}
+</section>
+{% endfor %}
+{% endblock %}
diff --git a/hypocurate/web/templates/queries.html b/hypocurate/web/templates/queries.html
new file mode 100644
index 0000000..4644f13
--- /dev/null
+++ b/hypocurate/web/templates/queries.html
@@ -0,0 +1,31 @@
+{% extends "base.html" %}
+{% block title %}Queries · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Queries {{ info("queries") }}</h1>
+<p class="muted">{{ listed.words }} <a class="button" href="/queries/new">New query</a></p>
+{% if listed.queries %}
+<table class="data">
+  <thead><tr><th>Query</th><th>Created</th><th>Domain {{ info("domain") }}</th><th>Hypothesis {{ info("hypothesis") }}</th><th>Sources</th><th>Status {{ info("status") }}</th><th>Outcome {{ info("outcome") }}</th><th>Cost {{ info("cost") }}</th><th></th></tr></thead>
+  <tbody>{% for x in listed.queries %}
+    <tr>
+      <td data-label="Query"><a href="/queries/{{ x.number }}">{{ x.number }}</a>{% if x.version > 1 %}<div class="muted">version {{ x.version }}</div>{% endif %}{% if x.narrower %}<div class="muted">narrower question</div>{% endif %}</td>
+      <td data-label="Created">{{ x.created }}</td>
+      <td data-label="Domain">{{ x.domain }}</td>
+      <td data-label="Hypothesis">{{ x.claim }}</td>
+      <td data-label="Sources">{{ x.sources }}</td>
+      <td data-label="Status">{{ x.status_words }}</td>
+      <td data-label="Outcome">{{ x.outcome or "—" }}</td>
+      <td data-label="Cost">{{ x.cost }}</td>
+      <td data-label="Action"><a href="{{ x.action.href }}">{{ x.action.label }}</a></td>
+    </tr>
+  {% endfor %}</tbody>
+</table>
+{% endif %}
+{% if listed.newest or listed.older %}
+<nav class="pages" aria-label="Pages of the queries list">
+  {% if listed.newest %}<a rel="first" href="/queries">Newest queries</a>{% endif %}
+  {% if listed.older %}<a rel="next" href="/queries?before={{ listed.older }}">Older queries</a>{% endif %}
+</nav>
+{% endif %}
+{% endblock %}
diff --git a/hypocurate/web/templates/query.html b/hypocurate/web/templates/query.html
new file mode 100644
index 0000000..d2830ac
--- /dev/null
+++ b/hypocurate/web/templates/query.html
@@ -0,0 +1,41 @@
+{% extends "base.html" %}
+{% block title %}{{ q.number }} · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<p class="crumbs"><a href="/queries">Queries</a> › {{ q.number }}</p>
+<h1>{{ q.latest.claim }}</h1>
+<p class="muted">{{ q.number }} · version {{ q.latest.version }} · {{ q.latest.status_words }}{% if q.narrower_of %} · the narrower question of <a href="/queries/{{ q.narrower_of }}">{{ q.narrower_of }}</a>{% endif %} · {{ q.cost.calls }} model call{{ "" if q.cost.calls == 1 else "s" }}, {{ q.cost.input_tokens }} input and {{ q.cost.output_tokens }} output tokens, {{ q.cost.counted }} {{ info("cost") }}</p>
+{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+<div class="actions">
+  {% if q.can_edit %}<a class="button" href="/queries/{{ q.number }}/edit">{% if q.latest.status == "returned" %}Edit (a new version){% else %}Edit the draft{% endif %}</a>{% endif %}
+  {% if q.can_review %}<a class="button" href="/review/{{ q.number }}">Review and dispatch</a>{% endif %}
+  {% if q.can_dispatch_again %}
+  <form method="post" action="/queries/{{ q.number }}/again">
+    <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+    <button type="submit">Dispatch again (a new run)</button>
+  </form>{% endif %}
+</div>
+{% for v in q.versions %}
+<section>
+  <h2>Version {{ v.version }} · {{ v.status_words }} {{ info("version") }}</h2>
+  <p>{{ v.claim }}</p>
+  <dl class="facts">
+    <dt>Domain</dt><dd>{{ v.domain }}</dd>
+    <dt>Sources</dt><dd>{% for s in v.sources %}{{ s.name }} ({{ s.data_kind }}){% if not loop.last %}; {% endif %}{% endfor %}</dd>
+    <dt>How much data is enough</dt><dd>{{ v.sufficiency }}</dd>
+    <dt>Created</dt><dd>{{ v.created }}</dd>
+    {% if v.note %}<dt>Note</dt><dd>{{ v.note }}</dd>{% endif %}
+    {% if v.review_comment %}<dt>Review</dt><dd>{{ v.review_comment }}</dd>{% endif %}
+  </dl>
+  {% if v.runs %}
+  <table class="data runs">
+    <thead><tr><th>Evidence</th><th>Run</th><th>Status</th></tr></thead>
+    <tbody>{% for x in v.runs %}
+      <tr><td data-label="Evidence">{% with e = x.evidence, small = true %}{% include "_dial.html" %}{% endwith %}</td>
+          <td data-label="Run"><a href="/runs/{{ x.run }}">run {{ x.run }}</a></td><td data-label="Status">{{ x.status_words }}</td></tr>
+    {% endfor %}</tbody>
+  </table>
+  {% endif %}
+</section>
+{% endfor %}
+{% endblock %}
diff --git a/hypocurate/web/templates/query_form.html b/hypocurate/web/templates/query_form.html
new file mode 100644
index 0000000..0c2c8ae
--- /dev/null
+++ b/hypocurate/web/templates/query_form.html
@@ -0,0 +1,40 @@
+{% extends "base.html" %}
+{% block title %}{% if number %}Edit {{ number }}{% else %}New query{% endif %} · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+{% if number %}<p class="crumbs"><a href="/queries">Queries</a> › <a href="/queries/{{ number }}">{{ number }}</a> › edit</p>{% endif %}
+<h1>{% if number %}Edit {{ number }}{% else %}New query{% endif %}</h1>
+{% if number and q and q.latest.status == "returned" %}
+<p class="notice">Version {{ q.latest.version }}: {{ q.latest.review_comment }}. Saving creates version {{ q.latest.version + 1 }}; version {{ q.latest.version }} is kept unchanged. {{ info("version") }}</p>
+{% endif %}
+{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+<form method="post" action="{% if number %}/queries/{{ number }}/edit{% else %}/queries{% endif %}" class="query-form">
+  <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+  <label for="claim">Hypothesis {{ info("hypothesis") }}</label>
+  <textarea id="claim" name="claim" rows="3" required>{{ values.claim if values else "" }}</textarea>
+  <fieldset><legend>Domain {{ info("domain") }}</legend>
+    {% for d in options.domains %}
+    <label class="choice"><input type="radio" name="domain" value="{{ d.key }}"
+      {%- if (values and values.domain == d.key) or ((not values or not values.domain) and loop.first) %} checked{% endif %}> {{ d.name }}{% if not d.supported %} <span class="muted">(not yet supported: cannot be dispatched)</span>{% endif %}</label>
+    {% endfor %}
+  </fieldset>
+  <fieldset><legend>Data sources {{ info("sources") }}</legend>
+    {% for s in options.sources %}
+    <label class="choice"><input type="checkbox" name="sources" value="{{ s.key }}"
+      {%- if values and s.key in values.sources %} checked{% elif not values and s.enabled %} checked{% endif %}> {{ s.name }} <span class="badge kind">{{ s.data_kind }}</span>{% if s.constructed %} <span class="muted">(constructed test data: dispatched only as a marked test run, from the command line)</span>{% endif %}{% if not s.enabled %} <span class="muted">(off)</span>{% endif %}</label>
+    {% endfor %}
+  </fieldset>
+  <fieldset><legend>How much data is enough {{ info("sufficiency") }}</legend>
+    {% for o in options.sufficiency %}
+    <label class="choice"><input type="radio" name="sufficiency" value="{{ o.key }}"
+      {%- if (values and values.sufficiency == o.key) or ((not values or not values.sufficiency) and loop.first) %} checked{% endif %}> {{ o.words }} <span class="muted">({{ o.detail }})</span></label>
+    {% endfor %}
+  </fieldset>
+  <label for="note">Note to the reviewer (optional)</label>
+  <textarea id="note" name="note" rows="2">{{ values.note if values else "" }}</textarea>
+  <div class="actions">
+    <button type="submit" name="action" value="save" class="secondary">Save draft</button>
+    <button type="submit" name="action" value="submit">Submit for review</button>
+  </div>
+</form>
+{% endblock %}
diff --git a/hypocurate/web/templates/review.html b/hypocurate/web/templates/review.html
new file mode 100644
index 0000000..d0145d6
--- /dev/null
+++ b/hypocurate/web/templates/review.html
@@ -0,0 +1,60 @@
+{% extends "base.html" %}
+{% block title %}Review and dispatch · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Review and dispatch {{ info("review") }}</h1>
+<div class="review-grid">
+  <nav class="picker" aria-label="Submitted queries">
+    <h2>Submitted {{ info("picker") }}</h2>
+    {% if not picker %}<p class="muted">No query is waiting for review.</p>{% endif %}
+    <ul>{% for p in picker %}
+      <li{% if q and q.number == p.number %} class="current"{% endif %}><a href="/review/{{ p.number }}">{{ p.number }} · version {{ p.version }}</a>
+        <div class="muted">{{ p.submitted }} · {{ p.domain }}</div><div>{{ p.claim }}</div></li>
+    {% endfor %}</ul>
+  </nav>
+  <div>
+  {% if error %}<p class="error" role="alert">Not done: {{ error }}</p>{% endif %}
+  {% if q and q.reviewable %}
+  <section>
+    <h2>{{ q.number }} · version {{ q.latest.version }}</h2>
+    <p>{{ q.latest.claim }}</p>
+    <dl class="facts">
+      <dt>How much data is enough {{ info("sufficiency") }}</dt><dd>{{ q.latest.sufficiency }}</dd>
+      <dt>Sources</dt><dd>{% for s in q.latest.sources %}{{ s.name }} ({{ s.data_kind }}){% if not loop.last %}; {% endif %}{% endfor %}</dd>
+      <dt>Agent settings {{ info("agentversion") }}</dt><dd>{% for a in q.agents %}{{ a.role }}: {% if a.version %}version {{ a.version }}{% else %}none stored yet{% endif %}{% if not loop.last %}; {% endif %}{% endfor %} <span class="muted">(dispatch records the code's current settings, a new version if they changed)</span></dd>
+      <dt>Spending caps {{ info("cap") }}</dt><dd>{{ q.caps.per_run }} per run; {{ q.caps.monthly }} per month</dd>
+      {% if q.latest.note %}<dt>Note</dt><dd>{{ q.latest.note }}</dd>{% endif %}
+    </dl>
+    <form method="post" action="/review/{{ q.number }}/dispatch" class="query-form">
+      <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+      <fieldset><legend>Domain: confirm or change {{ info("domain") }}</legend>
+        {% for d in q.options.domains %}
+        <label class="choice"><input type="radio" name="domain" value="{{ d.key }}"{% if d.key == q.domain_key %} checked{% endif %}> {{ d.name }}{% if not d.supported %} <span class="muted">(not yet supported)</span>{% endif %}</label>
+        {% endfor %}
+      </fieldset>
+      <label for="ceiling">Ceiling for this run in US dollars (optional; at most the per-run cap)</label>
+      <input id="ceiling" name="ceiling" inputmode="decimal" placeholder="{{ q.caps.per_run }}">
+      <p>Dispatching as <strong>{{ signed_in_as }}</strong>.</p>
+      <button type="submit">Dispatch</button>
+    </form>
+    <form method="post" action="/review/{{ q.number }}/return" class="query-form">
+      <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+      <label for="comment">Return for edits: what should change?</label>
+      <textarea id="comment" name="comment" rows="2" required></textarea>
+      <button type="submit" class="secondary">Return for edits</button>
+    </form>
+  </section>
+  {% elif q %}
+  <p>{{ q.number }} is {{ q.latest.status_words }}; only a submitted query is reviewed. <a href="/queries/{{ q.number }}">Open it</a>.</p>
+  {% endif %}
+  <section>
+    <h2>Run queue {{ info("queue") }}</h2>
+    {% if not queue %}<p class="muted">No run is queued, waiting or running.</p>{% else %}
+    <table class="data">
+      <thead><tr><th>Run</th><th>Query</th><th>Status</th><th>Stage</th><th>Worker</th></tr></thead>
+      <tbody>{% for x in queue %}<tr><td data-label="Run"><a href="/runs/{{ x.run }}">run {{ x.run }}</a></td><td data-label="Query">{{ x.query }}{% if x.test_run %} <span class="badge test-run">test run</span>{% endif %}</td><td data-label="Status">{{ x.status }}</td><td data-label="Stage">{{ x.stage }}</td><td data-label="Worker">{{ x.worker or "none" }}</td></tr>{% endfor %}</tbody>
+    </table>{% endif %}
+  </section>
+  </div>
+</div>
+{% endblock %}
diff --git a/hypocurate/web/templates/run.html b/hypocurate/web/templates/run.html
index e1ba39a..f8b3773 100644
--- a/hypocurate/web/templates/run.html
+++ b/hypocurate/web/templates/run.html
@@ -6,6 +6,7 @@
 <p class="crumbs"><a href="/runs">Runs</a> › {{ r.query }} · version {{ r.version }} · run {{ r.run }} {{ info("version") }} · <strong>{{ r.status_words }}</strong></p>
 <h1>{{ r.claim }}</h1>
 <p class="muted">Domain: {{ r.domain }}{% for t in r.tags %} · {{ t }}{% endfor %} · plan: {{ r.plan_kind }} · agent mode: {{ r.agent_mode }} · dispatched {{ r.queued }}{% if r.ended %} · ended {{ r.ended }}{% endif %}</p>
+<p class="downloads"><a class="button" href="/runs/{{ r.run }}/workbook">Download data (workbook)</a> <a href="/runs/{{ r.run }}/records.csv">Records as CSV</a> {{ info("download") }}</p>
 {% if r.test_run_badge %}<p class="badge test-run">{{ r.test_run_badge }}</p>{% endif %}
 {% if message %}<p class="notice" role="status">{{ message }}</p>{% endif %}
 {% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
@@ -18,6 +19,7 @@
     <div class="statement-text">
       <h2>Results statement (written by code) {{ info("sig") }}</h2>
       {% for line in r.statement.body %}<p class="{{ 'indent' if line.startswith('  ') else '' }}">{{ line|units }}</p>{% endfor %}
+      <p class="terms muted">Terms: {% for k in statement_terms %}{{ term(k) }}{% if not loop.last %} · {% endif %}{% endfor %}</p>
     </div>
     <aside class="outcome" aria-label="Evidence level and verdict">
       <h3>Evidence level {{ info("evidence_level") }}</h3>
@@ -49,6 +51,17 @@
   {% endif %}
 </section>
 
+{% if plot %}
+<section class="plot-section">
+  <h2>Plot of the data and the fitted relationship {{ info("plot") }}</h2>
+  {% if plot.svg %}
+  <div class="plot-box">{{ plot.svg }}{{ plot.svg_narrow }}</div>
+  <ul class="legend">{% for line in plot.legend %}<li>{{ line|units }}</li>{% endfor %}</ul>
+  {% else %}<p>{{ plot.reason }}</p>{% endif %}
+  <p class="muted small">{{ plot.version }}</p>
+</section>
+{% endif %}
+
 {% if r.per_source %}
 <section>
   <h2>Each source alone, and all together {{ info("persource") }}</h2>
@@ -75,12 +88,28 @@
 </section>
 {% endif %}
 
+<section>
+  <h2>Commentary {{ info("commentary") }}</h2>
+  <p class="muted">No commentary: the Commentator is not built in sprint 1 (PRD 15, step 12).</p>
+</section>
+
 <section>
   <h2>Cautions</h2>
   {% for line in r.statement.cautions %}<p class="{{ 'indent' if line.startswith('  ') else '' }}">{{ line|units }}</p>{% endfor %}
 </section>
 {% endif %}
 
+{% if r.flags %}
+<section>
+  <h2>Flags raised by code {{ info("records") }}</h2>
+  <table class="data">
+    <thead><tr><th>Flag</th><th>Kind</th><th>Category</th><th>Records</th><th>The Critic's class</th></tr></thead>
+    <tbody>{% for f in r.flags %}<tr><td data-label="Flag">{{ f.flag }}</td><td data-label="Kind">{{ f.kind_words }}</td><td data-label="Category">{{ f.category or "—" }}</td><td data-label="Records">{{ f.records }}</td>
+      <td data-label="The Critic's class">{{ f.critic }}{% if f.critic_label %}<div class="label">{{ f.critic_label }}</div>{% endif %}</td></tr>{% endfor %}</tbody>
+  </table>
+</section>
+{% endif %}
+
 <section>
   <h2>Checkpoints</h2>
   <div class="cards">
diff --git a/hypocurate/web/templates/runs.html b/hypocurate/web/templates/runs.html
index ce67385..27a98c3 100644
--- a/hypocurate/web/templates/runs.html
+++ b/hypocurate/web/templates/runs.html
@@ -7,12 +7,13 @@
 <p class="muted">{{ listed.words }} {{ info("queue") }}</p>
 {% if runs %}
 <table class="data runs">
-  <thead><tr><th>Evidence {{ info("evidence_level") }}</th><th>Run</th><th>Claim</th><th>Status {{ info("status") }}</th><th>Outcome {{ info("outcome") }}</th><th>Cost {{ info("cost") }}</th></tr></thead>
+  <thead><tr><th>Evidence {{ info("evidence_level") }}</th><th>Run</th><th>Claim</th><th>Plan {{ info("fixedplan") }}</th><th>Status {{ info("status") }}</th><th>Outcome {{ info("outcome") }}</th><th>Cost {{ info("cost") }}</th></tr></thead>
   <tbody>{% for x in runs %}
     <tr>
       <td data-label="Evidence">{% with e = x.evidence, small = true %}{% include "_dial.html" %}{% endwith %}</td>
       <td data-label="Run"><a href="/runs/{{ x.run }}">{{ x.query }} · run {{ x.run }}</a><div class="muted">{{ x.queued }}</div></td>
       <td data-label="Claim">{{ x.claim }}</td>
+      <td data-label="Plan">{{ x.plan }}</td>
       <td data-label="Status">{{ x.status_words }}</td>
       <td data-label="Outcome">{{ x.outcome or "—" }}</td>
       <td data-label="Cost">{{ x.cost }}</td>
diff --git a/hypocurate/web/templates/sources.html b/hypocurate/web/templates/sources.html
new file mode 100644
index 0000000..854e43c
--- /dev/null
+++ b/hypocurate/web/templates/sources.html
@@ -0,0 +1,47 @@
+{% extends "base.html" %}
+{% block title %}Data sources · HypoCurate{% endblock %}
+{% block main_attrs %} class="wide"{% endblock %}
+{% block content %}
+<h1>Data sources {{ info("datasources") }}</h1>
+{% if message %}<p class="notice" role="status">{{ message }}</p>{% endif %}
+{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
+<table class="data">
+  <thead><tr><th>Source</th><th>Type</th><th>Kind of data {{ info("kinds") }}</th><th>Licence</th><th>Adapter {{ info("adapter") }}</th><th>On</th><th>Latest sealed version</th><th></th></tr></thead>
+  <tbody>{% for x in s.sources %}
+    <tr>
+      <td data-label="Source">{{ x.name }}{% if x.constructed %}<div class="muted">constructed test data: only in a marked test run</div>{% endif %}</td>
+      <td data-label="Type">{{ x.source_type }}</td>
+      <td data-label="Kind of data"><span class="badge kind">{{ x.data_kind }}</span></td>
+      <td data-label="Licence">{{ x.licence }}</td>
+      <td data-label="Adapter">{{ x.adapter_words }}</td>
+      <td data-label="On">{{ x.enabled_words }}</td>
+      <td data-label="Latest sealed version">{% if x.fingerprint %}{{ x.version_label }} · {{ x.short_fingerprint }} · {{ x.sealed }}{% else %}none{% endif %}</td>
+      <td data-label="Test"><a href="/sources/{{ x.key }}/test">Test connection {{ info("testconn") }}</a></td>
+    </tr>
+  {% endfor %}</tbody>
+</table>
+{% if s.unregistered %}
+<section>
+  <h2>Defined in code, not registered yet</h2>
+  <p class="muted">Registering reads the source's frozen files and seals a version. A new source needs an adapter in code first; registering a source of your own from a form is for a later sprint.</p>
+  <ul>{% for x in s.unregistered %}
+    <li>{{ x.name }} <span class="badge kind">{{ x.data_kind }}</span>
+      <form method="post" action="/sources/{{ x.key }}/register" class="inline-form">
+        <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+        <button type="submit">Register as {{ signed_in_as }}</button>
+      </form></li>
+  {% endfor %}</ul>
+</section>
+{% endif %}
+{% if report %}
+<section>
+  <h2>Connection test: {{ report.source_key }}</h2>
+  <p>Version {{ report.version_label }} · fingerprint {{ report.fingerprint[:12] }} · {{ report.records_read }} records read · {{ report.blank_rows }} blank rows.</p>
+  <p class="muted">Values by status: {{ report.statuses }}. Category values outside the fixed lists: {{ report.unrecognized_words }}.</p>
+  <table class="data">
+    <thead><tr><th>Item</th><th>Alloy</th><th>Grain size</th><th>Yield strength</th><th>Paper</th></tr></thead>
+    <tbody>{% for r in report.sample_rows %}<tr><td data-label="Item">{{ r.item }}</td><td data-label="Alloy">{{ r.alloy }}</td><td data-label="Grain size">{{ r.grain_size }}</td><td data-label="Yield strength">{{ r.yield_strength }}</td><td data-label="Paper">{{ r.paper }}</td></tr>{% endfor %}</tbody>
+  </table>
+</section>
+{% endif %}
+{% endblock %}
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index b87a8b5..ea91098 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -61,7 +61,7 @@ def test_every_category_has_entries_and_keys_are_unique():
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
 # Step 10a: question_as_tested fully applied (the website's Confirm button).
-PARTLY = {"constructed_test_runs"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
+PARTLY: set = set()  # step 10b: constructed_test_runs fully applied (its label on every screen); step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -252,7 +252,9 @@ def test_the_step_6_decisions_carry_the_owners_wording():
     access = BY_KEY["code_role_access"]["statement"]
     assert "Inclusion receives no outcome value" in access and "Not claimed: that outcomes play no part at all" in access
     assert "test run: includes constructed data" in BY_KEY["constructed_test_runs"]["statement"]
-    assert BY_KEY["constructed_test_runs"]["applied"]["step"] == 10
+    # Step 10b: the label is on every screen and list, so the entry is fully applied (it was pending step 10).
+    assert BY_KEY["constructed_test_runs"]["applied"]["status"] == "yes"
+    assert "Step 10" in BY_KEY["constructed_test_runs"]["applied"]["note"]
     assert "adapter code, with the adapter's name and version" in BY_KEY["record_extraction_provenance"]["statement"]
     assert "Duplicates are resolved before grain sizes are counted." in BY_KEY["eligibility_rule_order"]["statement"]
     assert "step 1 answer file" in " ".join(BY_KEY["duplicate_survivor_rule"]["notes"])
diff --git a/tests/test_failure_words.py b/tests/test_failure_words.py
new file mode 100644
index 0000000..9243ef0
--- /dev/null
+++ b/tests/test_failure_words.py
@@ -0,0 +1,142 @@
+"""Step 10b (owner's request of 2026-10-11): a failed run is explained in plain English first - what happened, what was
+and was not done, what the person can do next - with the codes second, as "Technical detail: …"; a source a run never
+reached reads "not searched (the run ended first)"; the runs list uses the same plain wording."""
+from __future__ import annotations
+
+import re
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import failure_words, orchestrator, queries, run_view
+from hypocurate.pipeline.agents import spend
+from test_queries_step9a import _spend_this_month
+from test_web_runs import plain, signed_in
+
+OWNERS_EXAMPLE = ("The run stopped before anything was tested. The Planner proposed a plan twice, and both times code's "
+                  "checks refused it, so nothing was locked or searched. You can dispatch the question again as a new "
+                  "run.")
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
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e, migrated_database
+    e.dispose()
+
+
+def failed_planner_run(engine, stub):
+    stub.respond(to.responder(to.planner_body(outcome="hardness")))  # refused by code's checks, twice
+    rid = to.dispatched(engine)
+    report = orchestrator.run(engine, rid, client_options=sp.client_options(stub))
+    assert report.status == "failed" and report.failure.startswith("planner_failed:")
+    return rid
+
+
+def explained(engine, rid):
+    with engine.connect() as conn:
+        reason = conn.execute(text("SELECT failure_reason FROM run WHERE id = :r"), dict(r=rid)).scalar_one()
+        return failure_words.explain(conn, rid, reason)
+
+
+def test_the_owners_example_a_planner_refused_twice(own, stub):
+    engine, url = own
+    rid = failed_planner_run(engine, stub)
+    e = explained(engine, rid)
+    assert e["words"] == OWNERS_EXAMPLE
+    assert e["technical"] == "Technical detail: planner_failed, invalid_plan."
+    assert e["reasons"]  # this version stores the reason for each refused attempt, in code's words
+    page = signed_in(engine, url).get(f"/runs/{rid}").text
+    shown = plain(page)
+    assert shown.index(OWNERS_EXAMPLE) < shown.index("Technical detail: planner_failed, invalid_plan.")
+    assert "Code's reasons for refusing the Planner's answers:" in shown
+    assert "Failed: planner_failed" not in shown  # the codes come second, never first
+    for name in ("MPEA dataset (Borg et al. 2020)", "Texas A&M FCC dataset (Mulukutla et al. 2026)"):
+        assert f"{name}: not searched (the run ended first)" in shown and f"{name}: pending" not in shown
+
+
+def test_the_runs_list_says_it_in_plain_words_too(own, stub):
+    engine, url = own
+    rid = failed_planner_run(engine, stub)
+    row = re.search(rf'href="/runs/{rid}".*?<td data-label="Status">([^<]*)</td>',
+                    signed_in(engine, url).get("/runs").text, re.S).group(1)
+    assert row == "failed: the Planner&#39;s plan was refused"
+
+
+def test_a_cancelled_run_names_the_person_and_says_what_was_done(own, stub):
+    engine, _ = own
+    queued = to.dispatched(engine, fixed_plan=True)
+    queries.cancel(engine, queued, by="Grace Reviewer")
+    assert explained(engine, queued)["words"] == (
+        "The run was cancelled by Grace Reviewer before it started: nothing was asked, locked, searched or paid for. "
+        "You can dispatch the question again as a new run.")
+    stub.respond(to.responder(to.planner_body()))
+    waiting = to.dispatched(engine)
+    assert orchestrator.run(engine, waiting, client_options=sp.client_options(stub)).status == "waiting"
+    queries.cancel(engine, waiting, by="Grace Reviewer")
+    e = explained(engine, waiting)
+    assert e["words"].startswith("The run was cancelled by Grace Reviewer while it waited for a person to confirm")
+    assert e["technical"] == "Technical detail: cancelled."
+
+
+def test_a_spending_cap_says_which_cap_and_what_to_do(own, stub):
+    engine, _ = own
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    _spend_this_month(engine, spend.MONTH_CAP_USD)
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "failed"
+    e = explained(engine, rid)
+    assert e["words"] == ("The run stopped because its next model request would have gone over this month's spending "
+                          "cap; the request was not sent and nothing more was paid for. Nothing was locked or "
+                          "searched. Dispatch it again next month, or once the owner raises the monthly cap.")
+    assert e["technical"] == "Technical detail: spending_refused, spending_cap_month."
+
+
+@pytest.mark.parametrize("reason, start", [
+    ("domain_mismatch: x", "The run stopped before anything was tested: the Planner judged that the claim belongs"),
+    ("claim_not_one_plan: x (narrower_missing)", "The run stopped before anything was tested: the claim covers more"),
+    ("interrupted: x", "The run stopped because the worker was interrupted twice while the Planner was being asked"),
+    ("attempts_exhausted: the run stopped at analysis 4 times", "The run stopped after the worker was interrupted"),
+    ("refused: a checkpoint or write refused (invariant_broken)", "The run stopped because code refused one of its steps"
+                                                                   " (the primary set breaks a rule no plan can change"),
+    ("planner_failed: x (provider_unavailable)", "The run stopped before anything was tested: the model provider could "
+                                                 "not be reached"),
+    ("planner_failed: x (malformed)", "The run stopped before anything was tested. The Planner answered once, but"),
+    ("something_new: an unforeseen stop", "The run stopped: an unforeseen stop. Nothing was locked or searched."),
+])
+def test_every_stored_failure_reads_as_plain_words_first(own, reason, start):
+    engine, _ = own
+    rid = to.dispatched(engine, fixed_plan=True)
+    with engine.connect() as conn:
+        e = failure_words.explain(conn, rid, reason)
+    assert e["words"].startswith(start), e["words"]
+    assert e["words"].endswith(".") and "  " not in e["words"] and "_" not in e["words"]
+    assert e["technical"].startswith("Technical detail: ")
+
+
+def test_every_failure_code_the_orchestrator_stores_has_its_own_explanation():
+    for code in orchestrator.REASONS:
+        if code != "planner_failed":
+            assert code in failure_words.EXPLAIN, code
+    assert set(failure_words.SHORT) == set(failure_words.EXPLAIN)
+
+
+def test_a_completed_run_never_shows_a_source_as_pending(own):
+    """A completed run whose source was never searched (as when the run stopped short of it) reads 'not searched'."""
+    engine, url = own
+    rid = to.dispatched(engine, fixed_plan=True)
+    queries.cancel(engine, rid, by="Ada")
+    page = run_view.run_page(engine, rid)
+    assert {s["status"] for s in page["sources"]} == {run_view.NOT_REACHED}
diff --git a/tests/test_help.py b/tests/test_help.py
new file mode 100644
index 0000000..6c0bd0c
--- /dev/null
+++ b/tests/test_help.py
@@ -0,0 +1,65 @@
+"""Step 10b: the Help page and the information buttons (PRD 9.7; criterion 14.5): one glossary file; every entry has a
+button on some screen and appears on the Help page; every key a template uses exists; no template repeats an
+explanation's text; the Help page can be searched."""
+from __future__ import annotations
+
+import html
+import pathlib
+import re
+
+import pytest
+
+from hypocurate.db.engine import make_engine
+from hypocurate.web import app as web_app
+from hypocurate.web import glossary
+from test_web_runs import make_client, plain, signed_in
+
+TEMPLATES = pathlib.Path(web_app.__file__).resolve().parent / "templates"
+
+
+@pytest.fixture
+def own(migrated_database):
+    e = make_engine(migrated_database)
+    yield e, migrated_database
+    e.dispose()
+
+
+def used_keys() -> set[str]:
+    keys = set(web_app.STATEMENT_TERMS)
+    for t in TEMPLATES.glob("*.html"):
+        keys |= set(re.findall(r'(?:info|term)\("([a-z_]+)"\)', t.read_text(encoding="utf-8")))
+    return keys
+
+
+def test_every_glossary_entry_has_a_button_and_every_button_has_an_entry():
+    keys = set(glossary.by_key())
+    assert used_keys() == keys, {"no button": sorted(keys - used_keys()), "no entry": sorted(used_keys() - keys)}
+
+
+def test_no_template_repeats_an_explanations_text():
+    for t in TEMPLATES.glob("*.html"):
+        source = t.read_text(encoding="utf-8")
+        for e in glossary.entries():
+            assert e["text"][:60] not in source, (t.name, e["key"])
+
+
+def test_the_help_page_lists_every_explanation_and_where_it_appears(own):
+    engine, url = own
+    page = signed_in(engine, url).get("/help").text
+    shown = plain(page)
+    assert f"{len(glossary.entries())} of {len(glossary.entries())} explanations" in shown
+    for e in glossary.entries():
+        assert html.escape(e["text"], quote=False) in page.replace("&#39;", "'"), e["key"]
+        assert f'id="{e["key"]}"' in page
+
+
+def test_the_help_page_can_be_searched(own):
+    engine, url = own
+    shown = plain(signed_in(engine, url).get("/help?q=spending cap").text)
+    assert "Spending cap" in shown and "Checkpoint 1: rules lock" not in shown
+    assert "contain “spending cap”" in shown
+
+
+def test_the_help_page_needs_the_login(own):
+    engine, url = own
+    assert make_client(engine, url).get("/help").status_code == 303
diff --git a/tests/test_plot.py b/tests/test_plot.py
new file mode 100644
index 0000000..cf8156b
--- /dev/null
+++ b/tests/test_plot.py
@@ -0,0 +1,201 @@
+"""Step 10b: the plot (PRD 9.4; owner's answer of 2026-10-11: raw values, marker shape by source, crosses for
+sensitivity-only records, hollow for records not used, one line segment per alloy in the test with the stored slope).
+
+The check that matters most: the points the plot marks as used in the test, grouped by the plot's alloys, give back
+the stored slope when fitted test-side (least squares with one baseline per alloy, numpy) - so the plot shows the fit's
+own records and alloys, and its lines are the fit's lines.
+"""
+from __future__ import annotations
+
+import re
+
+import numpy as np
+import pytest
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from conftest import _create, _drop, url_for
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import plot, queries, run_view
+from test_web_runs import plain, signed_in
+
+
+def completed(engine, stub, claim=to.FCC_CLAIM, sources=("mpea", "tamu_fcc"), sufficiency="fixed_minimum",
+              fixed_plan=True):
+    stub.respond(to.responder(to.BCC if claim == to.BCC_CLAIM else None))
+    q = queries.create(engine, claim, sources, sufficiency=sufficiency)
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)
+    assert to.run(engine, rid, stub).status == "completed"
+    return rid
+
+
+@pytest.fixture(scope="module")
+def world(admin, database_url, template_database):
+    name = _create(admin, "hypocurate_t", template=template_database)
+    url = url_for(database_url, name)
+    engine = make_engine(url)
+    stub = sp.StubProvider()
+    try:
+        pw.registered(engine, ("mpea", "tamu_fcc"))
+        runs = {"reference": completed(engine, stub),
+                "withheld": completed(engine, stub, sources=("tamu_fcc",)),
+                "coefficient_only": completed(engine, stub, sources=("tamu_fcc",), sufficiency="use_available"),
+                "nothing_frozen": completed(engine, stub, to.BCC_CLAIM, fixed_plan=False),
+                "open": to.dispatched(engine, fixed_plan=True)}
+        yield engine, url, runs
+    finally:
+        stub.close()
+        engine.dispose()
+        _drop(admin, name)
+
+
+def fitted_slope(points) -> float:
+    """Test-side least squares with one baseline per alloy (independent of the statistics module)."""
+    alloys = sorted({p["alloy"] for p in points})
+    X = np.zeros((len(points), len(alloys) + 1))
+    for i, p in enumerate(points):
+        X[i, alloys.index(p["alloy"])] = 1.0
+        X[i, -1] = p["x"]
+    return float(np.linalg.lstsq(X, np.array([p["y"] for p in points]), rcond=None)[0][-1])
+
+
+def test_the_used_points_fit_back_to_the_stored_slope_and_each_alloy_gets_one_line(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["reference"])
+    used = [p for p in d["points"] if p["use"] == plot.USED]
+    assert len(used) == 97 and len({p["alloy"] for p in used}) == 22  # the reference test: 97 records, 22 alloys
+    stored = run_view.show(engine, runs["reference"])["results"][0]["estimate"]
+    assert d["k"] == stored
+    assert abs(fitted_slope(used) - stored) <= 1e-9 * abs(stored)
+    assert len(d["segments"]) == 22
+    for s in d["segments"]:  # every line has the stored slope
+        assert abs((s["y1"] - s["y0"]) / (s["x1"] - s["x0"]) - stored) <= 1e-9 * abs(stored)
+
+
+def test_records_are_marked_by_how_they_were_used_and_shaped_by_source(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["reference"])
+    uses = {p["use"] for p in d["points"]}
+    assert uses == {plot.USED, plot.SENSITIVITY_ONLY, plot.NOT_USED}
+    assert [s["key"] for s in d["sources"]] == ["mpea", "tamu_fcc"] and d["sources"][0]["shape"] != d["sources"][1]["shape"]
+    svg = str(plot.svg(d))
+    # Owner's review: records not used outside the view are not drawn (the legend counts them).
+    assert svg.count('class="fit"') == 22 and len(markers(svg)) == len(d["points"]) - plot.view(d)["outside"]
+
+
+def test_below_the_minimums_there_are_points_but_no_lines_and_the_reason(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["withheld"])
+    assert d["plot"] and d["points"] and d["segments"] == [] and d["k"] is None
+    assert d["reason"] == "No fitted lines: the minimums were not met, so no estimate is shown."
+    assert d["reason"] in plot.legend(d)
+
+
+def test_a_coefficient_only_result_draws_its_lines_with_the_stored_coefficient(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["coefficient_only"])
+    stored = run_view.show(engine, runs["coefficient_only"])["results"][0]["estimate"]
+    assert d["k"] == stored and d["segments"]
+    used = [p for p in d["points"] if p["use"] == plot.USED]
+    assert abs(fitted_slope(used) - stored) <= 1e-9 * abs(stored)
+
+
+def test_with_no_dataset_frozen_there_is_no_plot_and_the_reason_is_stated(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["nothing_frozen"])
+    assert d["plot"] is False and d["reason"] == "No plot: no dataset was frozen, so nothing was tested."
+
+
+def test_the_plot_states_its_format_and_the_code_version_that_built_it(world, monkeypatch):
+    engine, _, runs = world
+    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
+    assert plot.data(engine, runs["reference"])["version"] == "Plot format 1; built by code version unknown."
+    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123abcd")
+    assert plot.data(engine, runs["reference"])["version"] == "Plot format 1; built by code version 0123abcd."
+
+
+def test_the_run_page_shows_the_plot_of_a_completed_run_only(world):
+    engine, url, runs = world
+    c = signed_in(engine, url)
+    page = c.get(f"/runs/{runs['reference']}").text
+    assert '<svg class="plot plot-wide"' in page and '<svg class="plot plot-narrow"' in page
+    assert "built by code version" in plain(page)
+    assert "each with the stored slope k = 424.9 MPa·µm^0.5" in plain(page)
+    assert "No plot: no dataset was frozen" in plain(c.get(f"/runs/{runs['nothing_frozen']}").text)
+    assert '<svg class="plot' not in c.get(f"/runs/{runs['open']}").text
+
+
+def test_the_plots_text_is_never_drawn_below_12_px():
+    """Owner's addition 6: the SVG's text is FONT units in a viewBox W wide, and the plot is never narrower than the
+    stylesheet's min-width, so FONT * min-width / W >= 12."""
+    import pathlib
+    css = (pathlib.Path(plot.__file__).resolve().parents[1] / "web" / "static" / "style.css").read_text()
+    min_width = float(re.search(r"svg\.plot-wide \{[^}]*min-width: (\d+)px", css).group(1))
+    assert plot.FONT * min_width / plot.W >= 12
+    svg = str(plot.svg({"points": [{"x": 0.5, "y": 300.0, "source": "mpea", "use": plot.USED}], "segments": [],
+                        "sources": [{"key": "mpea", "name": "MPEA", "shape": "circle"}]}))
+    sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', svg)]
+    assert sizes and min(sizes) >= plot.FONT
+
+
+# --- the owner's screenshot review (2026-10-11) ------------------------------------------------------------------------
+
+def markers(svg: str) -> list[dict]:
+    return [dict(re.findall(r'data-(source|use|shape)="([^"]*)"', m)) for m in re.findall(r'<[^>]*class="pt"[^>]*>', svg)]
+
+
+@pytest.mark.parametrize("layout", ["wide", "narrow"])
+def test_every_marker_has_its_sources_fixed_shape_never_its_order(world, layout):
+    engine, _, runs = world
+    for key in ("reference", "coefficient_only"):
+        drawn = markers(str(plot.svg(plot.data(engine, runs[key]), layout)))
+        assert drawn
+        for m in drawn:
+            expected = "cross" if m["use"] == plot.SENSITIVITY_ONLY else plot.SOURCE_SHAPES[m["source"]]
+            assert m["shape"] == expected, m
+    reference = markers(str(plot.svg(plot.data(engine, runs["reference"]), layout)))
+    assert sum(1 for m in reference if m["source"] == "tamu_fcc" and m["use"] == plot.USED) == 21  # Texas A&M in the test
+    assert {m["shape"] for m in reference if m["source"] == "tamu_fcc" and m["use"] == plot.USED} == {"triangle"}
+
+
+def test_a_texas_a_and_m_only_runs_legend_says_triangles(world):
+    engine, _, runs = world
+    legend = plot.legend(plot.data(engine, runs["coefficient_only"]))
+    assert legend[0] == "Texas A&M FCC dataset (Mulukutla et al. 2026): triangles"
+
+
+def test_the_view_is_limited_to_the_records_in_the_fit_and_says_how_many_lie_outside(world):
+    engine, _, runs = world
+    d = plot.data(engine, runs["reference"])
+    v = plot.view(d)
+    kept = [p for p in d["points"] if p["use"] != plot.NOT_USED]
+    assert v["x1"] <= max(max(p["x"] for p in kept), max(s["x1"] for s in d["segments"])) * 1.05 + 1e-12
+    outside = [p for p in d["points"] if p["use"] == plot.NOT_USED and not (v["x0"] <= p["x"] <= v["x1"]
+                                                                          and v["y0"] <= p["y"] <= v["y1"])]
+    assert v["outside"] == len(outside) > 0
+    assert f"{len(outside)} records not used lie outside it." in " ".join(plot.legend(d))
+    drawn = markers(str(plot.svg(d)))
+    assert len(drawn) == len(d["points"]) - len(outside)  # nothing outside the view is drawn
+
+
+def test_a_coefficient_only_legend_does_not_call_the_fit_a_test(world):
+    engine, _, runs = world
+    legend = " ".join(plot.legend(plot.data(engine, runs["coefficient_only"])))
+    assert "Filled: used in the fit (coefficient only: no valid uncertainty, not a test)" in legend
+    assert "used in the test" not in legend and "one per alloy in the fit" in legend
+    assert "Filled: used in the test (97)" in " ".join(plot.legend(plot.data(engine, runs["reference"])))
+
+
+def test_the_phone_drawing_keeps_its_text_at_12_px_or_more():
+    """The narrow drawing is shown below 56rem on screens at least 360 px wide: the content is the screen less the
+    16 px gutters and the section's 12 px padding on each side (style.css)."""
+    import pathlib
+    css = (pathlib.Path(plot.__file__).resolve().parents[1] / "web" / "static" / "style.css").read_text()
+    assert "@media (max-width: 56rem) { svg.plot-wide { display: none; } svg.plot-narrow { display: block; } }" in css
+    n = plot.LAYOUTS["narrow"]
+    assert n["font"] * (360 - 2 * 16 - 2 * 12) / n["w"] >= 12
+    w = plot.LAYOUTS["wide"]
+    assert w["font"] * 540 / w["w"] >= 12
diff --git a/tests/test_web_catalog.py b/tests/test_web_catalog.py
new file mode 100644
index 0000000..5fba9bf
--- /dev/null
+++ b/tests/test_web_catalog.py
@@ -0,0 +1,138 @@
+"""Step 10b: the Critic's flags on the run page (with their advice label), the data sources page with registration and
+"Test connection and show sample records" (PRD 9.6; registration is a safeguard write, with the CSRF token), and the
+read-only agent pages with their "Fixed in code" panel (PRD 9.5)."""
+from __future__ import annotations
+
+import re
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_critic as tc
+from hypocurate.access.allowlist import ALLOWED, FIELDS
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import catalog_view
+from hypocurate.pipeline.agents import analyst, critic, planner
+from test_web_runs import plain, signed_in, token
+
+NAME = "Grace Reviewer"
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
+def bare(migrated_database):
+    """A database with only MPEA registered (so other sources defined in code are not registered yet)."""
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea",))
+    yield e, migrated_database
+    e.dispose()
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+# --- the Critic's flags ---------------------------------------------------------------------------------------------
+
+def test_the_run_page_shows_each_flag_and_the_critics_class_under_its_advice_label(migrated_database, stub):
+    e = make_engine(migrated_database)
+    try:
+        pw.registered_files(e, {"mpea": pw.mpea_csv(tc.small_rows(3, papers=3) + tc.CONFLICT + [tc.PAIR_SAME,
+                                                                                               tc.PAIR_MPEA]),
+                                "controlled_duplicates": pw.mpea_csv([tc.PAIR_SAME, tc.PAIR_OTHER])})
+        rid = tc.checked_run(e, tc.version(e))
+        multi = tc.multi_flag_ids(e, rid)
+        stub.respond(lambda raw: tc.reply({str(f): {"class": "same_measurement", "reason": "same paper and alloy"}
+                                           for f in multi}))
+        tc.run_critic(e, rid, stub)
+        page = plain(signed_in(e, migrated_database).get(f"/runs/{rid}").text)
+        assert "Flags raised by code" in page
+        assert page.count(f"same measurement reported twice: same paper and alloy {critic.ADVICE_LABEL}") == len(multi)
+        assert "not classified: single-record flag" in page
+    finally:
+        e.dispose()
+
+
+# --- data sources ---------------------------------------------------------------------------------------------------
+
+def test_the_sources_page_lists_each_source_with_its_facts_and_the_unregistered_ones(bare):
+    engine, url = bare
+    page = plain(signed_in(engine, url).get("/sources").text)
+    assert "MPEA dataset (Borg et al. 2020)" in page and "measured" in page and "available" in page
+    assert "Defined in code, not registered yet" in page and "Texas A&M FCC dataset" in page
+    assert f"Register as {NAME}" in page  # the button names the signed-in person
+
+
+def test_registering_a_source_from_the_website_records_it_and_names_the_person(bare):
+    engine, url = bare
+    c = signed_in(engine, url, NAME)
+    r = c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)})
+    assert r.status_code == 200 and f"tamu_fcc registered by {NAME}: version" in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM source WHERE key = 'tamu_fcc'") == 1
+    assert one(engine, "SELECT count(*) FROM source_version sv JOIN source s ON s.id = sv.source_id WHERE "
+                       "s.key = 'tamu_fcc' AND sv.sealed_at IS NOT NULL") >= 1
+    again = c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)})
+    assert "was already registered with this version" in plain(again.text)
+
+
+@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
+def test_registration_without_the_sessions_token_is_refused_and_writes_nothing(bare, sent):
+    engine, url = bare
+    c = signed_in(engine, url, NAME)
+    before = (one(engine, "SELECT count(*) FROM source"), one(engine, "SELECT count(*) FROM source_version"))
+    data = {} if sent is None else {"csrf_token": sent}
+    assert c.post("/sources/tamu_fcc/register", data=data).status_code == 403
+    assert (one(engine, "SELECT count(*) FROM source"), one(engine, "SELECT count(*) FROM source_version")) == before
+
+
+def test_an_unknown_source_is_refused_with_the_reason(bare):
+    engine, url = bare
+    c = signed_in(engine, url, NAME)
+    r = c.post("/sources/no_such_source/register", data={"csrf_token": token(c)})
+    assert r.status_code == 409 and "Not registered: unknown source" in plain(r.text)
+
+
+def test_the_connection_test_shows_sample_records_and_writes_nothing(bare):
+    engine, url = bare
+    tables = ("source", "source_version", "record", "audit_log")
+    before = [one(engine, f"SELECT count(*) FROM {t}") for t in tables]
+    page = plain(signed_in(engine, url).get("/sources/mpea/test").text)
+    assert "Connection test: mpea" in page and "records read" in page
+    assert [one(engine, f"SELECT count(*) FROM {t}") for t in tables] == before
+    assert "Connection test not done for tamu_fcc" in plain(signed_in(engine, url).get("/sources/tamu_fcc/test").text)
+
+
+# --- agents ---------------------------------------------------------------------------------------------------------
+
+@pytest.mark.parametrize("role", ["planner", "curator", "critic", "analyst", "commentator"])
+def test_each_agent_page_shows_exactly_what_the_access_layer_lets_the_role_receive(bare, role):
+    engine, url = bare
+    page = signed_in(engine, url).get(f"/agents/{role}").text
+    receives = plain(page.split("<h3>Receives</h3>", 1)[1].split("<h3>Returns</h3>", 1)[0])
+    expected = {f for fields in (ALLOWED.get(role) or {}).values() for f in fields}
+    shown = set(re.findall(r"<strong>([a-z ]+)</strong>: ", page.split("<h3>Receives</h3>", 1)[1]
+                           .split("<h3>Returns</h3>", 1)[0]))
+    assert shown == {f.replace("_", " ") for f in expected}
+    for f in expected:
+        assert " ".join(FIELDS[f].split()) in receives
+    if not expected:
+        assert "Nothing, at any stage." in receives
+    assert catalog_view.MAY_CALL in plain(page) and catalog_view.MAY_NOT[role] in plain(page)
+
+
+def test_each_agent_page_says_what_the_role_returns_from_the_roles_own_description(bare):
+    engine, url = bare
+    c = signed_in(engine, url)
+    for role, module in (("planner", planner), ("critic", critic), ("analyst", analyst)):
+        assert " ".join(module.OUTPUT_DESCRIPTION.split()) in plain(c.get(f"/agents/{role}").text), role
+    assert c.get("/agents/nobody").status_code == 404
+    assert c.get("/agents").headers["location"] == "/agents/planner"
diff --git a/tests/test_web_queries.py b/tests/test_web_queries.py
new file mode 100644
index 0000000..464439f
--- /dev/null
+++ b/tests/test_web_queries.py
@@ -0,0 +1,294 @@
+"""Step 10b: the query pages (PRD 9.1 to 9.3; owner's go of 2026-10-11).
+
+New query (save draft, submit), the queries list (an ID cursor, as the runs list), one query with its versions,
+editing (a draft in place; a returned query as its next version, PRD 9.2), review and dispatch (the domain confirmed
+under the signed-in name; return for edits with a comment; the refusals in code's words: the monthly cap, constructed
+test data, a domain not yet supported), dispatch again, and a CSRF token on every write. The web service only writes
+through `pipeline.queries`; a dispatched run waits for a worker.
+"""
+from __future__ import annotations
+
+import re
+from decimal import Decimal
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import queries, query_view
+from hypocurate.pipeline.agents import spend
+from test_queries_step9a import _spend_this_month
+from test_web_runs import plain, signed_in, token
+
+CLAIM = to.FCC_CLAIM
+NAME = "Grace Reviewer"
+
+
+@pytest.fixture
+def own(migrated_database):
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e, migrated_database
+    e.dispose()
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def new_query(c, action="save", claim=CLAIM, sources=("mpea", "tamu_fcc"), domain="grain_size_strengthening",
+              sufficiency="fixed_minimum", note=""):
+    r = c.post("/queries", data={"csrf_token": token(c), "claim": claim, "sources": list(sources), "domain": domain,
+                                 "sufficiency": sufficiency, "note": note, "action": action})
+    assert r.status_code == 303, plain(r.text)[:400]
+    return r.headers["location"].rsplit("/", 1)[1]
+
+
+def latest(engine, number):
+    with engine.connect() as conn:
+        return conn.execute(text(
+            "SELECT v.version_number, v.status, v.text, v.note, v.review_comment, d.key AS domain, "
+            "cd.key AS confirmed_domain FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
+            "JOIN domain d ON d.id = v.domain_id LEFT JOIN domain cd ON cd.id = v.confirmed_domain_id "
+            "WHERE h.number = :n ORDER BY v.version_number DESC LIMIT 1"), dict(n=number)).one()
+
+
+# --- the flow -----------------------------------------------------------------------------------------------------
+
+def test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_signed_in_name(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, note="please check the band")
+    v = latest(engine, number)
+    assert (v.version_number, v.status, v.text, v.note) == (1, "draft", CLAIM, "please check the band")
+    assert "Edit the draft" in plain(c.get(f"/queries/{number}").text)
+    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " (edited)",
+                                                "sources": ["mpea"], "domain": "grain_size_strengthening",
+                                                "sufficiency": "use_available", "note": "", "action": "submit"})
+    assert r.status_code == 303
+    v = latest(engine, number)
+    assert (v.version_number, v.status, v.text) == (1, "submitted", CLAIM + " (edited)")  # a draft is edited in place
+    page = plain(c.get(f"/review/{number}").text)
+    assert f"{number} · version 1" in page and "Dispatching as Grace Reviewer" in page
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening",
+                                                  "ceiling": "0.40"})
+    assert r.status_code == 303 and r.headers["location"].startswith("/runs/")
+    rid = int(r.headers["location"].rsplit("/", 1)[1])
+    v = latest(engine, number)
+    assert v.status == "dispatched" and v.confirmed_domain == "grain_size_strengthening"
+    assert v.review_comment == f"domain confirmed on the website by {NAME}"
+    # The web service runs nothing: the run is queued for a worker, with the ceiling given.
+    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
+    assert one(engine, "SELECT spending_ceiling FROM run WHERE id = :r", r=rid) == Decimal("0.40")
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid) == 0
+
+
+def test_a_returned_query_is_edited_as_its_next_version_and_the_returned_one_is_kept(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit")
+    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "name the test type"})
+    assert r.status_code == 303
+    v = latest(engine, number)
+    assert v.status == "returned" and v.review_comment == f"returned by {NAME}: name the test type"
+    form = plain(c.get(f"/queries/{number}/edit").text)
+    assert "Saving creates version 2; version 1 is kept unchanged" in form
+    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " in tension",
+                                                "sources": ["mpea", "tamu_fcc"], "domain": "grain_size_strengthening",
+                                                "sufficiency": "fixed_minimum", "note": "", "action": "save"})
+    assert r.status_code == 303
+    v = latest(engine, number)
+    assert (v.version_number, v.status, v.text) == (2, "draft", CLAIM + " in tension")
+    with engine.connect() as conn:
+        first = conn.execute(text("SELECT v.status, v.text FROM hypothesis h JOIN hypothesis_version v ON "
+                                  "v.hypothesis_id = h.id WHERE h.number = :n AND v.version_number = 1"),
+                             dict(n=number)).one()
+    assert tuple(first) == ("returned", CLAIM)
+
+
+def test_return_needs_a_comment(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit")
+    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "  "})
+    assert r.status_code == 409 and "say what to change" in plain(r.text)
+    assert latest(engine, number).status == "submitted"
+
+
+def test_dispatch_again_makes_a_new_run_once_the_last_one_ended(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit")
+    first = int(c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c),
+                                                          "domain": "grain_size_strengthening"}).headers["location"]
+                .rsplit("/", 1)[1])
+    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
+    assert r.status_code == 409 and queries.REASONS["already_open"] in plain(r.text)  # the first run is still open
+    queries.cancel(engine, first, by=NAME)
+    assert "Dispatch again" in plain(c.get(f"/queries/{number}").text)
+    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
+    assert r.status_code == 303 and int(r.headers["location"].rsplit("/", 1)[1]) > first
+
+
+# --- the refusals, in code's words ---------------------------------------------------------------------------------
+
+def test_dispatch_at_the_monthly_cap_is_refused_with_the_owners_words(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit")
+    _spend_this_month(engine, spend.MONTH_CAP_USD)
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
+    assert r.status_code == 409 and queries.REASONS["month_cap_reached"] in plain(r.text)
+    assert latest(engine, number).status == "submitted"
+
+
+def test_dispatch_of_constructed_test_data_is_refused_with_its_reason(own):
+    engine, url = own
+    pw.registered(engine, ("controlled_duplicates",))
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit", sources=("mpea", "controlled_duplicates"))
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
+    assert r.status_code == 409
+    assert queries.REASONS["constructed_source_unmarked"].format(source="controlled_duplicates") in plain(r.text)
+
+
+def test_a_domain_not_yet_supported_cannot_be_dispatched_and_the_message_says_why(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit", domain="fatigue")
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "fatigue"})
+    assert r.status_code == 409 and "the confirmed domain is not supported yet" in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM run") == 0
+
+
+def test_a_new_query_without_a_claim_or_a_source_is_refused_and_kept_on_the_form(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    r = c.post("/queries", data={"csrf_token": token(c), "claim": " ", "sources": ["mpea"],
+                                 "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "action": "save"})
+    assert r.status_code == 409 and "state the hypothesis" in plain(r.text)
+    r = c.post("/queries", data={"csrf_token": token(c), "claim": CLAIM, "domain": "grain_size_strengthening",
+                                 "sufficiency": "fixed_minimum", "action": "save"})
+    assert r.status_code == 409 and "chooses at least one source" in plain(r.text) and CLAIM in r.text
+    assert one(engine, "SELECT count(*) FROM hypothesis") == 0
+
+
+# --- CSRF on every write --------------------------------------------------------------------------------------------
+
+@pytest.mark.parametrize("route", ["/queries", "/queries/{n}/edit", "/queries/{n}/again", "/review/{n}/dispatch",
+                                   "/review/{n}/return"])
+@pytest.mark.parametrize("sent", [None, "", "not-the-token"])
+def test_every_query_write_refuses_a_request_without_the_sessions_token(own, route, sent):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, action="submit")
+    before = (one(engine, "SELECT count(*) FROM hypothesis"), one(engine, "SELECT count(*) FROM hypothesis_version"),
+              one(engine, "SELECT count(*) FROM run"), latest(engine, number).status)
+    data = {"claim": CLAIM, "sources": ["mpea"], "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum",
+            "comment": "x", "action": "save", **({} if sent is None else {"csrf_token": sent})}
+    assert c.post(route.format(n=number), data=data).status_code == 403
+    after = (one(engine, "SELECT count(*) FROM hypothesis"), one(engine, "SELECT count(*) FROM hypothesis_version"),
+             one(engine, "SELECT count(*) FROM run"), latest(engine, number).status)
+    assert after == before
+
+
+# --- the list -------------------------------------------------------------------------------------------------------
+
+def test_the_queries_list_goes_through_every_query_once_while_queries_are_added(own):
+    engine, url = own
+    old = queries.create(engine, "An old draft", ["mpea"]).number
+    existing = [old] + [queries.create(engine, f"Claim {i}", ["mpea"]).number
+                        for i in range(query_view.QUERIES_PER_PAGE + 20)]
+    c = signed_in(engine, url, NAME)
+    order, address = [], "/queries"
+    while address:
+        page = c.get(address)
+        assert page.status_code == 200
+        order += re.findall(r'<td data-label="Query"><a href="/queries/(Q-\d+)"', page.text)
+        nxt = re.search(r'<a [^>]*rel="next"[^>]*href="([^"]+)"', page.text)
+        address = nxt.group(1) if nxt else None
+        for i in range(query_view.QUERIES_PER_PAGE):
+            queries.create(engine, f"Added {i}", ["mpea"])
+    seen = [n for n in order if n in set(existing)]
+    assert seen == sorted(existing, key=lambda n: int(n[2:]), reverse=True) and seen[-1] == old
+    assert len(seen) == len(set(seen))
+
+
+def test_the_list_shows_each_querys_status_and_the_action_the_prd_names(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    draft = new_query(c)
+    submitted = new_query(c, action="submit")
+    page = c.get("/queries").text
+    assert f'href="/queries/{draft}/edit">Edit</a>' in page and f'href="/review/{submitted}">Review</a>' in page
+    assert "draft" in plain(page) and "submitted for review" in plain(page)
+
+
+# --- the functions --------------------------------------------------------------------------------------------------
+
+def test_only_a_draft_is_edited_in_place_and_only_a_returned_query_gets_a_new_version(own):
+    engine, _ = own
+    q = queries.create(engine, CLAIM, ["mpea"])
+    with pytest.raises(queries.QueryRefused) as refused:
+        queries.new_version(engine, q.number, CLAIM, ["mpea"], "grain_size_strengthening", "fixed_minimum", None)
+    assert refused.value.code == "not_returned"
+    queries.submit(engine, q.version_id)
+    with pytest.raises(queries.QueryRefused) as refused:
+        queries.update_draft(engine, q.number, CLAIM, ["mpea"], "grain_size_strengthening", "fixed_minimum", None)
+    assert refused.value.code == "not_a_draft"
+    with pytest.raises(queries.QueryRefused) as refused:
+        queries.return_for_edits(engine, q.version_id, by="", comment="x")
+    assert refused.value.code == "reviewer_missing"
+
+
+def test_the_edit_form_keeps_the_versions_own_choices(own):
+    """The form opens with the version's domain, sufficiency option, sources and note (step 10b, found in the
+    screenshots: it fell back to the defaults)."""
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c, sources=("tamu_fcc",), domain="fatigue", sufficiency="use_available", note="keep me")
+    form = c.get(f"/queries/{number}/edit").text
+    assert re.search(r'name="domain" value="fatigue" checked', form)
+    assert not re.search(r'name="domain" value="grain_size_strengthening" checked', form)
+    assert re.search(r'name="sufficiency" value="use_available" checked', form)
+    assert re.search(r'name="sources" value="tamu_fcc" checked', form)
+    assert not re.search(r'name="sources" value="mpea" checked', form) and "keep me" in form
+
+
+def test_the_queries_list_uses_short_source_names_and_the_query_page_full_ones(own):
+    engine, url = own
+    c = signed_in(engine, url, NAME)
+    number = new_query(c)
+    listed = plain(c.get("/queries").text)
+    assert "MPEA, Texas A&M" in listed and "Borg et al." not in listed
+    assert "MPEA dataset (Borg et al. 2020)" in plain(c.get(f"/queries/{number}").text)
+
+
+def test_every_menu_item_is_reachable_on_a_phone(own):
+    """The phone menu wraps (no item is pushed off the screen) and lists every page, Assumptions included."""
+    import pathlib
+    engine, url = own
+    page = signed_in(engine, url, NAME).get("/queries").text
+    nav = re.search(r'<nav class="menu".*?</nav>', page, re.S).group(0)
+    for label in ("Home", "Queries", "New query", "Review and dispatch", "Runs", "Assumptions"):
+        assert f">{label}</a>" in nav, label
+    css = (pathlib.Path(query_view.__file__).resolve().parents[1] / "web" / "static" / "style.css").read_text()
+    assert ".menu ul { flex-wrap: wrap; }" in css
+
+
+def test_a_marked_test_run_is_labelled_in_the_queries_list_and_the_queue(own):
+    """Register 'constructed_test_runs': the label on every screen and list (step 10b)."""
+    from hypocurate.pipeline import run_view
+    engine, url = own
+    q = queries.create(engine, CLAIM, ["mpea"])
+    queries.submit(engine, q.version_id)
+    queries.confirm_domain(engine, q.version_id, by=NAME)
+    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True)
+    c = signed_in(engine, url, NAME)
+    assert f"queued ({run_view.TEST_RUN_BADGE})" in plain(c.get("/queries").text)
+    assert next(r for r in run_view.queue_rows(engine) if r["run"] == rid)["test_run"] is True
+    pending = new_query(c, action="submit")
+    assert "test run" in plain(c.get(f"/review/{pending}").text)
diff --git a/tests/test_web_runs.py b/tests/test_web_runs.py
index 743340c..a2a136a 100644
--- a/tests/test_web_runs.py
+++ b/tests/test_web_runs.py
@@ -501,3 +501,59 @@ def test_an_old_run_without_a_stored_ceiling_shows_not_recorded(own, stub):
         conn.execute(text("UPDATE run SET spending_ceiling = NULL WHERE id = :r"), dict(r=rid))
     page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
     assert "ceiling for this run not recorded" in page and "$0.000000" not in page.split("ceiling for this run")[1][:20]
+
+
+# --- step 10b: the runs list's "Plan" column (owner, 2026-10-11) -------------------------------------------------------
+
+def test_the_runs_list_says_where_each_runs_question_as_tested_came_from(own, stub):
+    """From what is stored, never a guess: a fixed-plan run, a Planner run waiting, a Planner run confirmed by a named
+    person, and a Planner-path run locked before confirmations existed (the shape of local runs 1 and 2)."""
+    from hypocurate.pipeline import confirmation, reading
+    from test_reading_step10 import planner_path_run_locked_before_confirmations
+    engine, url = own
+    fixed = to.dispatched(engine, fixed_plan=True)
+    planner = waiting(engine, stub)
+    confirmed = waiting(engine, stub)
+    confirmation.confirm(engine, confirmed, by="Ada Reviewer")
+    predates = planner_path_run_locked_before_confirmations(engine)
+    page = signed_in(engine, url).get("/runs").text
+    plans = dict((int(r), p) for r, p in re.findall(
+        r'<td data-label="Run"><a href="/runs/(\d+)".*?<td data-label="Plan">([^<]*)</td>', page, re.S))
+    assert plans[fixed] == reading.PROVENANCE_WORDS["fixed"] == "fixed reference plan"
+    assert plans[planner] == "Planner&#39;s reading"
+    assert plans[confirmed] == "Planner&#39;s reading, confirmed by Ada Reviewer"
+    assert plans[predates] == "Planner&#39;s reading; predates confirmation"
+
+
+def test_a_narrower_questions_run_says_so(own, stub):
+    from hypocurate.pipeline import reading
+    from test_confirmation import narrower_waiting
+    engine, url = own
+    rid, original = narrower_waiting(engine, stub)
+    with engine.connect() as conn:
+        assert reading.provenance(conn, rid) == f"narrower question, built by code from run {original}"
+        assert reading.provenance(conn, original) == "Planner's reading"  # partly sufficient: never locked
+
+
+# --- step 10b: each sensitivity set says what it changes compared with the main result (owner, 2026-10-11) ---------
+
+def test_every_set_description_says_what_the_main_result_does_instead():
+    from hypocurate.pipeline.eligibility import INFLUENCE_KEY
+    for key in SENSITIVITY_CHANGES:
+        assert "main result" in run_view._set_description(key), key
+    assert run_view._set_description(INFLUENCE_KEY).endswith("; the main result keeps them.")
+
+
+def test_the_one_at_pct_set_names_the_main_results_own_rounding_from_the_plan():
+    from hypocurate.pipeline.plan import reference_plan
+    plan = reference_plan(1)
+    assert "instead of to 0.1 at.%, as in the main result" in run_view._set_description("same_alloy_1_at_pct", plan)
+    plan["rules"]["same_alloy_decimals"] = 2
+    assert "instead of to 0.01 at.%, as in the main result" in run_view._set_description("same_alloy_1_at_pct", plan)
+
+
+def test_atomic_percent_is_written_out_once_on_the_run_page(world):
+    engine, url, runs = world
+    page = plain(signed_in(engine, url).get(f"/runs/{runs['sufficient']}").text)
+    assert page.count("atomic percent (at.%)") == 1
+    assert page.index("atomic percent (at.%)") < page.index("rounded to 1 at.%")
diff --git a/tests/test_web_state.py b/tests/test_web_state.py
index 9def8dd..70ca252 100644
--- a/tests/test_web_state.py
+++ b/tests/test_web_state.py
@@ -89,7 +89,9 @@ def test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_e
     assert c.post(f"/runs/{rid}/cancel", data={"csrf_token": token(c)}).status_code == 303
     ended = c.get(f"/runs/{rid}/state").text
     assert 'data-ended="true"' in state_attrs(ended) and "data-poll" not in ended
-    assert "Failed: cancelled: cancelled by Grace Reviewer before it started" in plain(ended)
+    # Step 10b (owner, 2026-10-11): the failure in plain words first, the codes second.
+    assert "The run was cancelled by Grace Reviewer before it started" in plain(ended)
+    assert "Technical detail: cancelled." in plain(ended)
 
 
 def test_the_state_fragment_needs_the_login_and_a_known_run(own):
diff --git a/tests/test_workbook.py b/tests/test_workbook.py
new file mode 100644
index 0000000..f28dc3f
--- /dev/null
+++ b/tests/test_workbook.py
@@ -0,0 +1,144 @@
+"""Step 10b: the workbook and the records CSV (PRD 11), built on request from stored rows, for every outcome; the
+website's download and the command line's `export` give the same content; each states the code version that built
+it; its totals equal the run's recorded model calls (criterion 14.5)."""
+from __future__ import annotations
+
+import csv
+import io
+import json
+from decimal import Decimal
+
+import pytest
+from openpyxl import load_workbook
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from conftest import _create, _drop, url_for
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import queries, workbook
+from test_web_runs import make_client, signed_in
+
+
+@pytest.fixture(scope="module")
+def world(admin, database_url, template_database):
+    name = _create(admin, "hypocurate_t", template=template_database)
+    url = url_for(database_url, name)
+    engine = make_engine(url)
+    stub = sp.StubProvider()
+    try:
+        pw.registered(engine, ("mpea", "tamu_fcc"))
+        stub.respond(to.responder())
+        reference = to.dispatched(engine, fixed_plan=True)
+        assert to.run(engine, reference, stub).status == "completed"
+        stub.respond(to.responder(to.BCC))
+        insufficient = to.dispatched(engine, claim=to.BCC_CLAIM)
+        assert to.run(engine, insufficient, stub).status == "completed"
+        cancelled = to.dispatched(engine, fixed_plan=True)
+        queries.cancel(engine, cancelled, by="Ada Reviewer")
+        yield engine, url, {"reference": reference, "insufficient": insufficient, "cancelled": cancelled}
+    finally:
+        stub.close()
+        engine.dispose()
+        _drop(admin, name)
+
+
+def sheets(data: bytes) -> dict[str, list[tuple]]:
+    wb = load_workbook(io.BytesIO(data), read_only=True)
+    return {ws.title: [tuple(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
+
+
+def items(rows) -> dict:
+    return {r[0]: r[1] for r in rows[2:]}
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test(world):
+    engine, _, runs = world
+    s = sheets(workbook.build(engine, runs["reference"]))
+    assert list(s) == list(workbook.SHEETS)
+    for rows in s.values():
+        assert rows[0][0] == workbook.version_line()
+    used, other = s["Records used"], s["Records not used"]
+    header = used[1]
+    ids = {r[header.index("record")] for r in used[2:]}
+    with engine.connect() as conn:
+        primary = set(conn.execute(text(
+            "SELECT asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
+            "WHERE a.run_id = :r AND a.key = 'primary'"), dict(r=runs["reference"])).scalars())
+    assert ids == primary and len(ids) == 97
+    found = one(engine, "SELECT count(*) FROM record WHERE extraction_run_id = :r", r=runs["reference"])
+    assert len(other) - 2 == found - 97
+    assert {"rule", "flags", "sensitivity sets", "eligible"} <= set(other[1])
+    for field in ("grain_size", "grain_size unit", "grain_size status", "yield_strength", "values as reported"):
+        assert field in header
+    summary = items(s["Run summary"])
+    assert summary["Outcome"] == "sufficient in the sources searched"
+    assert summary["Rules lock"].startswith("20") and "fingerprint" in summary["Dataset freeze"]
+    assert "424.9 MPa·µm^0.5 ± 64.4 MPa·µm^0.5" in summary["Result: All sources together"]
+    significance = s["Significance and commentary"]
+    assert any(r[1] == workbook.COMMENTARY_NONE for r in significance)
+    assert any(str(r[0]).startswith("Calibration (estimated)") for r in significance)
+
+
+def test_the_workbooks_totals_equal_the_recorded_model_calls(world):
+    """Criterion 14.5: the totals equal the sum of the recorded model calls."""
+    engine, _, runs = world
+    with engine.connect() as conn:
+        n, cost = conn.execute(text("SELECT count(*), coalesce(sum(cost), 0) FROM model_call WHERE run_id = :r"),
+                               dict(r=runs["reference"])).one()
+    total = items(sheets(workbook.build(engine, runs["reference"]))["Run summary"])["Total"]
+    assert total.startswith(f"{n} model call") and f"reported ${Decimal(cost):.6f}" in total
+
+
+@pytest.mark.parametrize("which", ["insufficient", "cancelled"])
+def test_every_outcome_has_a_workbook(world, which):
+    engine, _, runs = world
+    s = sheets(workbook.build(engine, runs[which]))
+    assert list(s) == list(workbook.SHEETS) and len(s["Records used"]) == 2  # no record in a test
+    summary = items(s["Run summary"])
+    assert summary["Dataset freeze"] == "not reached"
+    if which == "cancelled":
+        assert summary["Failure"].startswith("The run was cancelled by Ada Reviewer")
+
+
+def test_the_records_csv_has_one_row_per_record_found(world):
+    engine, _, runs = world
+    rows = list(csv.reader(io.StringIO(workbook.records_csv(engine, runs["reference"]))))
+    assert rows[0] == [f"# {workbook.version_line()}"]
+    body = rows[2:]
+    assert len(body) == one(engine, "SELECT count(*) FROM record WHERE extraction_run_id = :r", r=runs["reference"])
+    assert sum(1 for r in body if r[rows[1].index("used in the test")] == "yes") == 97
+
+
+def test_the_same_stored_rows_give_the_same_workbook_and_it_names_the_code_version(world, monkeypatch):
+    engine, _, runs = world
+    assert sheets(workbook.build(engine, runs["reference"])) == sheets(workbook.build(engine, runs["reference"]))
+    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123abcd")
+    assert sheets(workbook.build(engine, runs["reference"]))["Run summary"][0][0] == \
+        "Workbook format 1; built by code version 0123abcd."
+
+
+def test_the_website_download_and_the_command_lines_export_give_the_same_workbook(world, tmp_path, monkeypatch, capsys):
+    from hypocurate import cli
+    engine, url, runs = world
+    rid = runs["reference"]
+    assert make_client(engine, url).get(f"/runs/{rid}/workbook").status_code == 303  # needs the login
+    r = signed_in(engine, url).get(f"/runs/{rid}/workbook")
+    assert r.status_code == 200 and r.headers["content-type"].startswith(
+        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
+    assert f'filename="hypocurate-run-{rid}.xlsx"' in r.headers["content-disposition"]
+    monkeypatch.setenv("DATABASE_URL", url)
+    out = tmp_path / "run.xlsx"
+    assert cli.main(["export", str(rid), "--out", str(out)]) == 0
+    assert json.loads(capsys.readouterr().out)["written"] == str(out)
+    assert sheets(out.read_bytes()) == sheets(r.content)
+    csv_out = tmp_path / "run.csv"
+    assert cli.main(["export", str(rid), "--out", str(csv_out), "--csv"]) == 0
+    assert csv_out.read_text(encoding="utf-8") == signed_in(engine, url).get(f"/runs/{rid}/records.csv").text
+    assert cli.main(["export", "999999", "--out", str(tmp_path / "x")]) == 1

```

## 5. Test output

### The whole suite, locally
```
2391 passed, 1 warning in 2284.44s (0:38:04)
exit 0
```
### The whole suite in the test image
```
psycopg.errors.AdminShutdown: terminating connection due to administrator command

exit 1
```
### Image hashes and checks
```
head:    ceccc3d
repo:    35eaecb65a6418ced6a943d5aa2e136cdfc355512a9dc963d8fb8c1a32586cb0  -
runtime: 35eaecb65a6418ced6a943d5aa2e136cdfc355512a9dc963d8fb8c1a32586cb0  -
test:    35eaecb65a6418ced6a943d5aa2e136cdfc355512a9dc963d8fb8c1a32586cb0  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
guard checks in the runtime image: 1

```
### The new test files against main's package (failed before)
```

pkg/tests/test_help.py:59: AssertionError
=========================== short test summary info ============================
FAILED pkg/tests/test_help.py::test_every_glossary_entry_has_a_button_and_every_button_has_an_entry
FAILED pkg/tests/test_help.py::test_the_help_page_lists_every_explanation_and_where_it_appears
FAILED pkg/tests/test_help.py::test_the_help_page_can_be_searched - assert ('...
ERROR pkg/tests/test_web_queries.py
ERROR pkg/tests/test_plot.py
ERROR pkg/tests/test_failure_words.py
ERROR pkg/tests/test_web_catalog.py
ERROR pkg/tests/test_workbook.py
3 failed, 2 passed, 5 errors in 3.99s
```
### Mutation checks
```
control: clean: 128 passed in 108.37s (0:01:48)
k1_new_query_without_csrf: caught: 1 failed, 8 passed in 6.05s
k2_register_without_csrf: caught: 1 failed, 3 passed in 9.17s
k3_review_without_csrf: caught: 1 failed, 11 passed in 6.96s
k4_marker_by_order: caught: 1 failed, 8 passed in 18.96s
k5_failure_times_once: caught: 1 failed in 8.43s
k6_narrower_without_run: caught: 1 failed, 45 passed in 41.04s
k7_draft_guard_removed: caught: 1 failed, 25 passed in 11.93s
k8_full_names_in_list: caught: 1 failed, 27 passed in 12.72s
k9_workbook_without_version: caught: 1 failed in 21.22s

```
### Reference dumps against main
```
fixed_plan.json identical
narrower.json identical
partly_original.json identical
planner_bcc.json identical
planner_fcc.json identical
reference.json identical

```

## 6. Scratch scripts

### packet/packet.py
```python
"""Scratch: builds docs/reviews/step10b_review_packet.md from the files on disk (summary, the full diff against main
without the screenshots, test outputs, comparisons, scratch scripts)."""
import pathlib
import subprocess

R = pathlib.Path("/workspaces/hypocurate")
W = pathlib.Path.home() / "hc-work/step10b"


def sh(*a):
    return subprocess.run(a, cwd=R, capture_output=True, text=True, check=True).stdout


def tail(p, n=6):
    return "\n".join(pathlib.Path(p).read_text(encoding="utf-8").splitlines()[-n:])


out = ["# Build step 10b — review packet", "",
       f"Branch `step-10b-screens`, head `{sh('git', 'rev-parse', '--short', 'HEAD').strip()}`, against `main` "
       "`7620f77`. Generated from the files on disk by a script (quoted at the end).", "",
       "## 1. The summary", "", (R / "docs/reviews/step10b_summary.md").read_text(encoding="utf-8"), "",
       "## 2. Commits", "", "```", sh("git", "log", "--oneline", "main..HEAD"), "```", "",
       "## 3. Files changed", "", "```", sh("git", "diff", "--stat", "main...HEAD"), "```", "",
       "## 4. The full diff (screenshots and this packet left out)", "",
       "```diff", sh("git", "diff", "main...HEAD", "--", ".", ":(exclude)docs/reviews/step10b_screenshots",
                     ":(exclude)docs/reviews/step10b_review_packet.md"), "```", "",
       "## 5. Test output", "",
       "### The whole suite, locally", "```", tail(W / "full.log", 2), "```",
       "### The whole suite in the test image", "```", tail(W / "image_suite.log", 3), "```",
       "### Image hashes and checks", "```", (W / "image_hashes.txt").read_text(encoding="utf-8"), "```",
       "### The new test files against main's package (failed before)", "```", tail(W / "before/before.log", 12), "```",
       "### Mutation checks", "```", (W / "mut/mutations.log").read_text(encoding="utf-8"), "```",
       "### Reference dumps against main", "```", (W / "refdump_compare.txt").read_text(encoding="utf-8"), "```", "",
       "## 6. Scratch scripts", ""]
for name in ("packet/packet.py", "mut/mutate.py", "register10b.py", "shots/world.py", "shots/shots.py",
             "shots/plotshots.py"):
    out += [f"### {name}", "```python", (W / name).read_text(encoding="utf-8"), "```", ""]
(R / "docs/reviews/step10b_review_packet.md").write_text("\n".join(out), encoding="utf-8")
print("written")

```

### mut/mutate.py
```python
"""Scratch: step 10b mutation checks. Each fault is applied to a fresh copy of the package (with data/ beside it), the
named tests run with PYTHONPATH on the copy from a folder without a package, and the run must fail."""
import json, os, pathlib, shutil, subprocess, sys
R = pathlib.Path("/workspaces/hypocurate"); W = pathlib.Path.home() / "hc-work/step10b/mut"
FIX = ["tests/test_web_queries.py", "tests/test_web_catalog.py", "tests/test_plot.py", "tests/test_failure_words.py",
       "tests/test_workbook.py"]
APP = "hypocurate/web/app.py"
CSRF = "        security.check_csrf(request, form.get(security.CSRF_FIELD))\n"
FAULTS = {
 "k1_new_query_without_csrf": (APP, CSRF + "        security.signed_in_name(request)\n        v = form_values(form)\n        try:\n            q = queries.create(",
                               "        security.signed_in_name(request)\n        v = form_values(form)\n        try:\n            q = queries.create(",
                               ["tests/test_web_queries.py"]),
 "k2_register_without_csrf": (APP, CSRF + "        name = security.signed_in_name(request)\n        try:\n            done = versions.register(",
                              "        name = security.signed_in_name(request)\n        try:\n            done = versions.register(",
                              ["tests/test_web_catalog.py"]),
 "k3_review_without_csrf": (APP, CSRF + "        name = security.signed_in_name(request)\n        try:\n            shown = query_view.review_page(",
                            "        name = security.signed_in_name(request)\n        try:\n            shown = query_view.review_page(",
                            ["tests/test_web_queries.py"]),
 "k4_marker_by_order": ("hypocurate/pipeline/plot.py", 'out.append(_marker(SOURCE_SHAPES.get(p["source"], OTHER_SHAPE),',
                        'out.append(_marker(("circle", "triangle")[sorted({q["source"] for q in pts}).index(p["source"]) % 2],',
                        ["tests/test_plot.py"]),
 "k5_failure_times_once": ("hypocurate/pipeline/failure_words.py", 'return {1: ("once", "the"), 2: ("twice", "both times")}',
                           'return {1: ("once", "the"), 2: ("once", "the")}', ["tests/test_failure_words.py"]),
 "k6_narrower_without_run": ("hypocurate/pipeline/reading.py", '"narrower": "narrower question, built by code from run {run}"',
                             '"narrower": "narrower question plan"', ["tests/test_web_runs.py"]),
 "k7_draft_guard_removed": ("hypocurate/pipeline/queries.py", '        if v.status != "draft":\n',
                            '        if False:\n', ["tests/test_web_queries.py"]),
 "k8_full_names_in_list": ("hypocurate/pipeline/query_view.py", 'SOURCE_SHORT_NAMES.get(s["key"], s["key"])', 's["name"]',
                           ["tests/test_web_queries.py"]),
 "k9_workbook_without_version": ("hypocurate/pipeline/workbook.py",
                                 '        ws.append([version_line()])\n        ws.append(["Item", "Value"])',
                                 '        ws.append(["Item", "Value"])', ["tests/test_workbook.py"]),
}
env = {**os.environ, "DATABASE_URL": [l.split("=", 1)[1].strip() for l in (R / ".env").read_text().splitlines() if l.startswith("DATABASE_URL=")][0]}
results = {}
names = sys.argv[1:] or ["control", *FAULTS]
for name in names:
    copy = W / "copy"
    shutil.rmtree(copy, ignore_errors=True); copy.mkdir()
    shutil.copytree(R / "hypocurate", copy / "hypocurate", ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "data").symlink_to(R / "data")
    files = FIX + ["tests/test_web_runs.py"]
    if name != "control":
        path, old, new, files = FAULTS[name]
        f = copy / path; s = f.read_text(encoding="utf-8")
        assert s.count(old) == 1, (name, s.count(old)); f.write_text(s.replace(old, new), encoding="utf-8")
    run_dir = W / "run"; run_dir.mkdir(exist_ok=True)
    try:
        out = subprocess.run([str(R / ".venv/bin/pytest"), "-q", "-p", "no:cacheprovider", "-x", "--rootdir", str(R),
                              *[str(R / f) for f in files]], cwd=run_dir, capture_output=True, text=True,
                             env={**env, "PYTHONPATH": str(copy)}, timeout=1800)
        tail = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "NO OUTPUT"
        verdict = ("clean" if out.returncode == 0 else "ERROR") if name == "control" else (
            "caught" if out.returncode == 1 and "failed" in tail else "SURVIVED" if out.returncode == 0 else "ERROR")
    except subprocess.TimeoutExpired:
        tail, verdict = "timeout", "HUNG"
    results[name] = (verdict, tail)
    (W / f"out_{name}.txt").write_text(out.stdout if verdict != "HUNG" else "timeout", encoding="utf-8")
    print(f"{name}: {verdict}: {tail}", flush=True)

```

### register10b.py
```python
"""Scratch: the step 10b register entries (Claude Code's wording, for the owner's review; decisions as noted)."""
import json, pathlib
p = pathlib.Path("/workspaces/hypocurate/hypocurate/assumptions.json")
r = json.loads(p.read_text(encoding="utf-8"))
by = {e["key"]: e for e in r}
OWNER = {"by": "owner (Khalid El-Awady)", "date": "2026-10-11"}
NR = {"status": "not_reviewed", "name": None, "date": None}
EV = ["Step 10b: the owner's go and screenshot review of 2026-10-11 (quoted in docs/reviews/step10b_summary.md)."]
DRAFT = "Wording drafted by Claude Code for the owner's review (2026-10-11)."


def entry(key, name, statement, value, affects, reason, settings, tests, unit=None):
    return {"key": key, "name": name, "state": "in_force", "statement": statement, "value": {"text": value, "unit": unit},
            "category": "operational", "affects": affects, "reason": reason, "evidence": EV, "decided": OWNER,
            "expert_review": NR, "sensitivity": None, "applied": {"status": "yes", "settings": settings, "note": None},
            "tests": tests, "history": [], "notes": [DRAFT]}


Q = "tests/test_web_queries.py::"
P = "tests/test_plot.py::"
new = [
 entry("query_versions_on_the_website", "Query versions on the website",
       "A new query is saved as a draft or submitted for review. A draft is edited in place (it was never submitted). A "
       "submitted query is reviewed: the reviewer confirms or changes the domain under the signed-in name ('domain "
       "confirmed on the website by <name>') and dispatches it, with an optional ceiling, or returns it for edits with "
       "a comment ('returned by <name>: <comment>'). A returned or dispatched version never changes: editing a returned "
       "query creates its next version, a draft, and earlier versions are kept (PRD 9.2). A query whose last run ended "
       "can be dispatched again as a new run. Every write carries the session's CSRF token; refusals are shown in "
       "code's words (the monthly cap, constructed test data, a domain not yet supported).",
       "draft in place; returned -> next version", "The query pages (PRD 9.1 to 9.3).",
       "PRD 9.1 to 9.3; the owner's go for 10b; the default for drafts stated to the owner on 2026-10-11.",
       [{"ref": "python:hypocurate.pipeline.queries:update_draft"}, {"ref": "python:hypocurate.pipeline.queries:new_version"},
        {"ref": "python:hypocurate.pipeline.queries:return_for_edits"},
        {"ref": "python:hypocurate.pipeline.queries:WEBSITE", "equals": "on the website"},
        {"ref": "python:hypocurate.pipeline.queries:CLAIM_MAX", "equals": 2000},
        {"ref": "python:hypocurate.pipeline.queries:NOTE_MAX", "equals": 2000},
        {"ref": "python:hypocurate.pipeline.queries:COMMENT_MAX", "equals": 2000}],
       [Q + "test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_signed_in_name",
        Q + "test_a_returned_query_is_edited_as_its_next_version_and_the_returned_one_is_kept",
        Q + "test_every_query_write_refuses_a_request_without_the_sessions_token",
        Q + "test_only_a_draft_is_edited_in_place_and_only_a_returned_query_gets_a_new_version"]),
 entry("queries_list", "The queries list",
       "The queries list shows every query, newest first, in pages of 50 followed by an ID cursor (as the runs list), "
       "with short source names (MPEA, Texas A&M); a query's own page gives the full names. Each row's action is the "
       "PRD's: Edit for a draft or returned query, Review for a submitted one, Open run for a dispatched one.",
       "50 a page; short source names", "The queries list (PRD 9.1).",
       "PRD 9.1; the owner's screenshot review of 2026-10-11 (short source names).",
       [{"ref": "python:hypocurate.pipeline.query_view:QUERIES_PER_PAGE", "equals": 50},
        {"ref": "python:hypocurate.pipeline.query_view:SOURCE_SHORT_NAMES"}],
       [Q + "test_the_queries_list_goes_through_every_query_once_while_queries_are_added",
        Q + "test_the_queries_list_uses_short_source_names_and_the_query_page_full_ones"]),
 entry("runs_list_plan_column", "The runs list's Plan column",
       "The runs list says where each run's question as tested came from, from what is stored (the run's fixed-plan "
       "flag, its narrower link, its locked plan, its confirmation), never a guess: 'fixed reference plan', 'Planner's "
       "reading', 'Planner's reading, confirmed by <name>', 'Planner's reading; predates confirmation', or 'narrower "
       "question, built by code from run <N>'.",
       "the owner's wording", "The runs list.", "The owner's requests of 2026-10-11.",
       [{"ref": "python:hypocurate.pipeline.reading:PROVENANCE_WORDS"}, {"ref": "python:hypocurate.pipeline.reading:provenance"}],
       ["tests/test_web_runs.py::test_the_runs_list_says_where_each_runs_question_as_tested_came_from",
        "tests/test_web_runs.py::test_a_narrower_questions_run_says_so"]),
 entry("failure_explanations", "A failed run explained in plain English",
       "A failed run's page explains the failure in plain English first: what happened, what was and was not done (read "
       "from the stored rows: plan locked, sources searched, dataset frozen), and what the person can do next, one fixed "
       "explanation per stored failure code; the Planner's stored rejection reasons in code's words; then 'Technical "
       "detail: <code>, <detail>.' A source a run never reached reads 'not searched (the run ended first)'. The runs "
       "list shows a short plain form.",
       "plain words first, codes second", "Failed runs' pages and the runs list.", "The owner's request of 2026-10-11.",
       [{"ref": "python:hypocurate.pipeline.failure_words:EXPLAIN"}, {"ref": "python:hypocurate.pipeline.failure_words:SHORT"},
        {"ref": "python:hypocurate.pipeline.run_view:NOT_REACHED", "equals": "not searched (the run ended first)"}],
       ["tests/test_failure_words.py::test_the_owners_example_a_planner_refused_twice",
        "tests/test_failure_words.py::test_every_failure_code_the_orchestrator_stores_has_its_own_explanation",
        "tests/test_failure_words.py::test_the_runs_list_says_it_in_plain_words_too"]),
 entry("run_plot", "The plot of a run",
       "Built on request from stored rows, never stored: each record's own outcome (MPa) against grain size^-1/2; a fixed "
       "marker shape per source (circles MPEA, triangles Texas A&M, squares the controlled duplicates, diamonds any "
       "other), filled for a record in the test, a cross for one used only in a sensitivity set, hollow for one not "
       "used. One line per alloy in the test over its own grain sizes, all with the stored slope; no lines below the "
       "minimums or with no coefficient, with the reason; no plot when nothing was frozen. A coefficient-only fit says "
       "'used in the fit (coefficient only: no valid uncertainty, not a test)'. The axes cover the records used and the "
       "sensitivity-only ones, and a line says how many records not used lie outside. A narrow drawing is shown on a "
       "phone so the text stays at least 12 px. It states its format and the code version that built it.",
       "raw values; per-alloy lines with the stored slope", "The run page (PRD 9.4).",
       "The owner's answer of 2026-10-11 (raw values and per-alloy lines) and screenshot review (markers by source, "
       "limited axes, phone, coefficient-only wording).",
       [{"ref": "python:hypocurate.pipeline.plot:PLOT_FORMAT", "equals": 1},
        {"ref": "python:hypocurate.pipeline.plot:SOURCE_SHAPES", "equals": {"mpea": "circle", "tamu_fcc": "triangle",
                                                                           "controlled_duplicates": "square"}},
        {"ref": "python:hypocurate.pipeline.plot:USED_COEFFICIENT_ONLY"}, {"ref": "python:hypocurate.pipeline.plot:LAYOUTS"}],
       [P + "test_the_used_points_fit_back_to_the_stored_slope_and_each_alloy_gets_one_line",
        P + "test_every_marker_has_its_sources_fixed_shape_never_its_order",
        P + "test_the_view_is_limited_to_the_records_in_the_fit_and_says_how_many_lie_outside",
        P + "test_the_plot_states_its_format_and_the_code_version_that_built_it",
        P + "test_the_phone_drawing_keeps_its_text_at_12_px_or_more"]),
 entry("run_workbook", "The run's workbook and records CSV",
       "Built on request from stored rows, never stored, for every outcome: PRD 11's four sheets (records used; records "
       "not used with the rule, flags and sensitivity sets; significance and commentary; run summary) and a records "
       "CSV. Each states its format and the code version that built it. The website's download and the command line's "
       "export use the same functions. The artifact table stays unused in sprint 1.",
       "four sheets; built on request", "The download (PRD 11) and 'hypocurate export'.",
       "PRD 11; the owner's answer 3 to the step 10 plan (built on request).",
       [{"ref": "python:hypocurate.pipeline.workbook:WORKBOOK_FORMAT", "equals": 1},
        {"ref": "python:hypocurate.pipeline.workbook:SHEETS", "equals": ["Records used", "Records not used",
                                                                         "Significance and commentary", "Run summary"]}],
       ["tests/test_workbook.py::test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test",
        "tests/test_workbook.py::test_the_workbooks_totals_equal_the_recorded_model_calls",
        "tests/test_workbook.py::test_every_outcome_has_a_workbook",
        "tests/test_workbook.py::test_the_website_download_and_the_command_lines_export_give_the_same_workbook"]),
 entry("web_source_registration", "Registering a source from the website",
       "The data sources page lists every registered source and every source defined in code that is not registered "
       "yet; registering one calls sources.versions.register (as the command line's 'sources register'), under the "
       "signed-in name and with the session's CSRF token; a request without the token is refused and writes nothing. "
       "'Test connection and show sample records' only reads. A source of a person's own, from a form, needs an adapter "
       "in code first and is for a later sprint.",
       "code-defined sources only; CSRF", "The data sources page (PRD 9.6).",
       "The owner's addition 4 to the step 10 plan (a safeguard, with the same review as the other write paths).",
       [{"ref": "python:hypocurate.sources.versions:register"}],
       ["tests/test_web_catalog.py::test_registering_a_source_from_the_website_records_it_and_names_the_person",
        "tests/test_web_catalog.py::test_registration_without_the_sessions_token_is_refused_and_writes_nothing",
        "tests/test_web_catalog.py::test_the_connection_test_shows_sample_records_and_writes_nothing"]),
 entry("agent_pages", "The agent pages",
       "One read-only page per role with its latest stored settings version and a 'Fixed in code' panel: what the role "
       "receives at each stage (the access layer's own allow-lists and field descriptions), what it returns (the role's "
       "own output description), what it may call and what it may not do (fixed sentences summarizing CLAUDE.md's "
       "rules).",
       "read-only", "The agent pages (PRD 9.5).", "PRD 9.5.",
       [{"ref": "python:hypocurate.pipeline.catalog_view:MAY_CALL"}, {"ref": "python:hypocurate.pipeline.catalog_view:MAY_NOT"}],
       ["tests/test_web_catalog.py::test_each_agent_page_shows_exactly_what_the_access_layer_lets_the_role_receive",
        "tests/test_web_catalog.py::test_each_agent_page_says_what_the_role_returns_from_the_roles_own_description"]),
 entry("help_page", "The Help page and the information buttons",
       "Every explanation lives in one file, hypocurate/web/glossary.json; every entry has an information button on some "
       "screen, every button names an entry, no template repeats an explanation's text, and the Help page lists every "
       "entry by where it appears, with a search.",
       "one glossary file", "Every screen; the Help page (PRD 9.7).", "PRD 9.7; criterion 14.5.",
       [{"ref": "file:hypocurate/web/glossary.json:\"key\":\"outcome\""}, {"ref": "python:hypocurate.web.app:STATEMENT_TERMS"}],
       ["tests/test_help.py::test_every_glossary_entry_has_a_button_and_every_button_has_an_entry",
        "tests/test_help.py::test_no_template_repeats_an_explanations_text",
        "tests/test_help.py::test_the_help_page_lists_every_explanation_and_where_it_appears"]),
]
for e in new:
    assert e["key"] not in by, e["key"]
r.extend(new)
s = by["sensitivity_set_display_names"]
old_statement = s["statement"]
s["statement"] = ("The screens name each sensitivity set in words and say what its one change does compared with the main "
                  "result, with the main result's own rule read from the run's locked plan; the internal keys are never "
                  "shown. 'atomic percent (at.%)' is written out once, in the 1 at.% set's name. The ninth set keeps its "
                  "approved name, 'without the group with the largest share of slope information'. The survivor set's "
                  "description is the owner's: 'Conflicting values, left out of the main result, are included once "
                  "each, using the survivor's value.'")
s["history"].append({"from": "2026-10-11", "to": "2026-10-11", "value": s["value"]["text"],
                     "note": "the descriptions named the set's change only; the owner asked (2026-10-11) that each say what "
                             "it changes compared with the main result"})
s["decided"] = OWNER
s["notes"].append("2026-10-11 (step 10b): reworded for the owner's request; " + DRAFT)
s["tests"] += ["tests/test_web_runs.py::test_every_set_description_says_what_the_main_result_does_instead",
               "tests/test_web_runs.py::test_the_one_at_pct_set_names_the_main_results_own_rounding_from_the_plan"]
c = by["constructed_test_runs"]
c["applied"] = {"status": "yes", "settings": c["applied"]["settings"],
                "note": "The guard is in code; the database itself does not refuse a constructed record. Step 10: the run "
                        "page, the runs list and a query's runs show the label (hatched dial), and the workbook's summary."}
c["tests"].append("tests/test_workbook.py::test_the_reference_runs_workbook_has_the_four_sheets_and_the_records_in_the_test")
p.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(r))

```

### shots/world.py
```python
"""Scratch (not committed): the 10b screenshot database: the 10a world (a copy of the dev database plus four runs
through the stub), then queries in every state: a draft, a submitted one, a returned one with a comment."""
import os, runpy, sys
sys.argv = ["world10a.py", sys.argv[1]]
runpy.run_path(os.path.join(os.path.dirname(__file__), "world10a.py"), run_name="__main__")
from sqlalchemy import make_url
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
url = make_url(os.environ["DATABASE_URL"]).set(database=sys.argv[1]).render_as_string(hide_password=False)
e = make_engine(url)
d = queries.create(e, "In FCC multi-principal-element alloys tested in compression, finer grains raise yield strength",
                   ["mpea", "tamu_fcc"], note="A draft, not yet submitted.")
s = queries.create(e, "Grain refinement strengthens BCC refractory multi-principal-element alloys at room temperature",
                   ["mpea"], sufficiency="use_available", note="Please check whether the BCC data are enough.")
queries.submit(e, s.version_id)
r = queries.create(e, "Smaller grains make alloys stronger", ["mpea", "tamu_fcc"])
queries.submit(e, r.version_id)
queries.return_for_edits(e, r.version_id, by="Ada Reviewer", comment="name the alloy class and the test temperature")
print({"draft": d.number, "submitted": s.number, "returned": r.number})

```

### shots/shots.py
```python
"""Scratch (not committed): the 10b screenshots (query pages, the plot), by headless Chromium in a throwaway container."""
import os
from playwright.sync_api import sync_playwright
base = "http://127.0.0.1:8011"
with sync_playwright() as p:
    b = p.chromium.launch()
    def session(width, height, scale):
        ctx = b.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
        pg = ctx.new_page()
        pg.goto(base + "/login"); pg.fill("#name", "Ada Reviewer"); pg.fill("#password", os.environ["PW"])
        pg.click("button[type=submit]")
        return pg
    pg = session(1280, 900, 1)
    for name, path in [("01_queries_list", "/queries"), ("02_new_query", "/queries/new"),
                       ("03_query_dispatched", "/queries/Q-0014"), ("04_query_returned", "/queries/Q-0021"),
                       ("05_edit_returned_new_version", "/queries/Q-0021/edit"), ("06_edit_draft", "/queries/Q-0019/edit"),
                       ("07_review_and_dispatch", "/review/Q-0020"), ("08_runs_list_plan_column", "/runs"),
                       ("09_run_plot_reference", "/runs/14"), ("10_run_plot_coefficient_only", "/runs/15"),
                       ("11_run_no_plot", "/runs/2")]:
        pg.goto(base + path)
        pg.screenshot(path=f"/w/out/{name}.png", full_page=True)
    pg.goto(base + "/runs/14")
    pg.locator(".plot-section").screenshot(path="/w/out/12_plot_close_up.png")
    ph = session(390, 844, 2)
    ph.goto(base + "/queries"); ph.screenshot(path="/w/out/13_phone_queries_list.png")
    ph.goto(base + "/runs/14"); ph.locator(".plot-section").screenshot(path="/w/out/14_phone_plot.png")
    b.close()
print("done")

```

### shots/plotshots.py
```python
import os
from playwright.sync_api import sync_playwright
base = "http://127.0.0.1:8011"
with sync_playwright() as p:
    b = p.chromium.launch()
    def session(w, h, s):
        pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=s).new_page()
        pg.goto(base + "/login"); pg.fill("#name", "Ada Reviewer"); pg.fill("#password", os.environ["PW"]); pg.click("button[type=submit]")
        return pg
    pg = session(1280, 900, 1)
    pg.goto(base + "/runs/14"); pg.locator(".plot-section").screenshot(path="/w/out/15_plot_reference_corrected.png")
    pg.goto(base + "/runs/15"); pg.locator(".plot-section").screenshot(path="/w/out/16_plot_texas_am_only_corrected.png")
    ph = session(390, 844, 2)
    ph.goto(base + "/runs/14"); ph.locator(".plot-section").screenshot(path="/w/out/17_phone_plot_corrected.png")
    ph.goto(base + "/queries"); ph.screenshot(path="/w/out/18_phone_menu_and_queries.png")
    b.close()
print("done")

```
