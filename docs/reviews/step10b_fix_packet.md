# Build step 10b — fix packet, round 1 (for a short re-check)

Branch `step-10b-screens`, head `410eaa7`. The reviewed head was `a25caf0`; this packet holds only what changed since. Generated from the files on disk by a script (quoted at the end).

## 1. The review being answered (verbatim)

Three problems need fixing before merge.
1. A stale page can act on a different query version.
   Files: web/app.py, web/templates/review.html, web/templates/query_form.html, pipeline/queries.py.
   Failing case: Alice opens version 1 for review. Someone returns it, edits it and submits version 2. Alice presses Dispatch in her old tab: review_action() retrieves the latest version and dispatches version 2, which Alice never reviewed. Return has the same problem. An old edit form can also overwrite a newer draft.
   Smallest fix: Submit the displayed version ID and a content fingerprint; check them inside the pipeline’s write transaction, under the version lock. Refuse stale submissions. Add two-session tests for review and editing.
2. Exports can turn stored text into spreadsheet formulas.
   File: pipeline/workbook.py, functions build() and records_csv().
   Failing case: A hypothesis or paper-reference string of =1+1 becomes an Excel formula. I reproduced this using the packet’s actual export functions: the reloaded workbook cells had formula type f. The CSV also emitted =1+1 unchanged.
   The Analyst’s label prefix protects that particular cell, but other text fields remain exposed.
   Smallest fix: Explicitly write text as string cells in XLSX; neutralize formula-leading text in the spreadsheet-facing CSV while preserving genuine numeric values. Test exported cell types, not just their displayed contents.
3. Several writes do not record the signed-in person.
   Files: web/app.py, pipeline/queries.py, sources/versions.py, tests/test_web_catalog.py.
   Failing case: Create, submit, edit and dispatch-again validate signed_in_name() but discard its return value. Registration uses the name only in its success message; it is not passed to register(). Consequently, these actions have no durable attribution to the person who performed them.
   The registration test passes because it checks the name in the response—not in a stored audit record.
   Smallest fix: Pass the session name into these pipeline functions and persist the actor and action within the write transaction. Test attribution after reopening the stored record.
Verification: I reproduced the formula issue and the stale review handler’s selection of version 2 using extracted functions with mocked database inputs. The remaining findings are from code inspection; I did not run PostgreSQL, Docker or the full suite.
I found no weakened assertion in the listed existing-test changes. However, the fresh-process isolation test still visits only the older run pages, so it does not establish isolation for the new screens. The packet’s failing image-suite stall test also remains unresolved; its cause was not independently verified here.
not safe to merge


## 2. What was done (from the summary)

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


## 3. Commits since the reviewed head

```
410eaa7 Step 10b, fix round 1: the pinned signature of confirmation.confirm gains 'via' (where it was done, for its action row)
c3cb765 Step 10b, fix round 1: act only on the version shown; no formulas in exports; who did what (0009 action_record)
580d6cc Step 10b: ChatGPT's review, verbatim (not safe to merge; three findings accepted by the owner)
a4b29d9 Step 10b: the stall-allowance test widened for slow machines (owner's decision); its mutation still caught

```

## 4. Files changed

```
 docs/reviews/step10b_review_chatgpt.md             |  18 ++
 hypocurate/assumptions.json                        | 196 ++++++++++++++-
 hypocurate/cli.py                                  |   6 +-
 hypocurate/cli_runs.py                             |  10 +-
 hypocurate/db/actions.py                           |  41 ++++
 .../db/migrations/versions/0009_action_record.py   | 131 ++++++++++
 hypocurate/db/models.py                            |  40 +++
 hypocurate/pipeline/confirmation.py                |   8 +-
 hypocurate/pipeline/queries.py                     | 149 ++++++++---
 hypocurate/pipeline/query_view.py                  |  11 +-
 hypocurate/pipeline/workbook.py                    |  56 ++++-
 hypocurate/sources/versions.py                     |  19 +-
 hypocurate/web/app.py                              |  76 ++++--
 hypocurate/web/templates/query.html                |   2 +
 hypocurate/web/templates/query_form.html           |   2 +
 hypocurate/web/templates/review.html               |   4 +
 tests/test_confirmation.py                         |   5 +-
 tests/test_migrations.py                           |   3 +
 tests/test_migrations_step10b.py                   | 145 +++++++++++
 tests/test_migrations_step9b.py                    |   8 +-
 tests/test_web_fix10b.py                           | 273 +++++++++++++++++++++
 tests/test_web_isolation.py                        |  80 ++++++
 tests/test_web_queries.py                          |  37 ++-
 tests/test_worker_fix1.py                          |  26 +-
 24 files changed, 1240 insertions(+), 106 deletions(-)

```

## 5. The diff (the summary and this packet left out)

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index f1e8609..a2aef19 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -9312,7 +9312,7 @@
     "key": "query_versions_on_the_website",
     "name": "Query versions on the website",
     "state": "in_force",
-    "statement": "A new query is saved as a draft or submitted for review. A draft is edited in place (it was never submitted). A submitted query is reviewed: the reviewer confirms or changes the domain under the signed-in name ('domain confirmed on the website by <name>') and dispatches it, with an optional ceiling, or returns it for edits with a comment ('returned by <name>: <comment>'). A returned or dispatched version never changes: editing a returned query creates its next version, a draft, and earlier versions are kept (PRD 9.2). A query whose last run ended can be dispatched again as a new run. Every write carries the session's CSRF token; refusals are shown in code's words (the monthly cap, constructed test data, a domain not yet supported).",
+    "statement": "A new query is saved as a draft or submitted for review. A draft is edited in place (it was never submitted). A submitted query is reviewed: the reviewer confirms or changes the domain under the signed-in name ('domain confirmed on the website by <name>') and dispatches it, with an optional ceiling, or returns it for edits with a comment ('returned by <name>: <comment>'). A returned or dispatched version never changes: editing a returned query creates its next version, a draft, and earlier versions are kept (PRD 9.2). A query whose last run ended can be dispatched again as a new run. Every write carries the session's CSRF token, acts only on the version the page showed (act_on_version_shown) and is recorded with the signed-in name (action_record); refusals are shown in code's words (the monthly cap, constructed test data, a domain not yet supported).",
     "value": {
       "text": "draft in place; returned -> next version",
       "unit": null
@@ -9345,10 +9345,6 @@
         {
           "ref": "python:hypocurate.pipeline.queries:return_for_edits"
         },
-        {
-          "ref": "python:hypocurate.pipeline.queries:WEBSITE",
-          "equals": "on the website"
-        },
         {
           "ref": "python:hypocurate.pipeline.queries:CLAIM_MAX",
           "equals": 2000
@@ -9360,6 +9356,13 @@
         {
           "ref": "python:hypocurate.pipeline.queries:COMMENT_MAX",
           "equals": 2000
+        },
+        {
+          "ref": "python:hypocurate.pipeline.queries:WHERE_WORDS",
+          "equals": {
+            "command line": "at the command line",
+            "website": "on the website"
+          }
         }
       ],
       "note": null
@@ -9372,7 +9375,7 @@
     ],
     "history": [],
     "notes": [
-      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+      "Wording drafted by Claude Code for the owner's review (2026-10-11, revised in fix round 1)."
     ]
   },
   {
@@ -9639,7 +9642,7 @@
     "key": "web_source_registration",
     "name": "Registering a source from the website",
     "state": "in_force",
-    "statement": "The data sources page lists every registered source and every source defined in code that is not registered yet; registering one calls sources.versions.register (as the command line's 'sources register'), under the signed-in name and with the session's CSRF token; a request without the token is refused and writes nothing. 'Test connection and show sample records' only reads. A source of a person's own, from a form, needs an adapter in code first and is for a later sprint.",
+    "statement": "The data sources page lists every registered source and every source defined in code that is not registered yet; registering one calls sources.versions.register (as the command line's 'sources register') with the session's CSRF token, and a version it seals is recorded with the signed-in name in action_record, in the same transaction; a request without the token is refused and writes nothing. 'Test connection and show sample records' only reads. A source of a person's own, from a form, needs an adapter in code first and is for a later sprint.",
     "value": {
       "text": "code-defined sources only; CSRF",
       "unit": null
@@ -9672,11 +9675,12 @@
     "tests": [
       "tests/test_web_catalog.py::test_registering_a_source_from_the_website_records_it_and_names_the_person",
       "tests/test_web_catalog.py::test_registration_without_the_sessions_token_is_refused_and_writes_nothing",
-      "tests/test_web_catalog.py::test_the_connection_test_shows_sample_records_and_writes_nothing"
+      "tests/test_web_catalog.py::test_the_connection_test_shows_sample_records_and_writes_nothing",
+      "tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name"
     ],
     "history": [],
     "notes": [
-      "Wording drafted by Claude Code for the owner's review (2026-10-11)."
+      "Wording drafted by Claude Code for the owner's review (2026-10-11, revised in fix round 1)."
     ]
   },
   {
@@ -9771,5 +9775,179 @@
     "notes": [
       "Wording drafted by Claude Code for the owner's review (2026-10-11)."
     ]
+  },
+  {
+    "key": "action_record",
+    "name": "Who did what: the action record",
+    "state": "in_force",
+    "statement": "Every write a person makes records, in the same transaction, one row of action_record (migration 0009): the action (create, edit, new version, submit, return, domain confirmation, dispatch, dispatch again, cancel, confirmation of the question as tested, registering a source), where it was done (the website, the command line, or code), the name given, what it acted on, and the database's time. On the website the name is the signed-in name, and the database refuses a website row without one. At the command line it is --by where the command takes it; a command without --by is recorded with no name, as such. A narrower question code creates is recorded as code's, with no name. Rows are never changed or deleted. Confirmation and cancel keep their own records as before (rules_confirmation, the run's failure reason); their row here repeats the name so that who did what is in one place. Nothing proves who typed a name (see signed_in_name). It is a record, not a gate: no rule reads it.",
+    "value": {
+      "text": "one row per action; append-only",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every query, run and source-registration write.",
+    "reason": "ChatGPT's review of 10b, finding 3 (create, submit, edit and dispatch again kept no name); the owner's answer: a new table action_record, migration 0009, with rows for confirm and cancel too.",
+    "evidence": [
+      "Step 10b, fix round 1: ChatGPT's review of 2026-10-11 (docs/reviews/step10b_review_chatgpt.md), its three findings accepted by the owner the same day, with the owner's answer on storage (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.db.models:ACTIONS",
+          "equals": [
+            "create",
+            "edit",
+            "new_version",
+            "submit",
+            "return",
+            "confirm_domain",
+            "dispatch",
+            "dispatch_again",
+            "cancel",
+            "confirm_rules",
+            "register_source"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.db.models:CHANNELS",
+          "equals": [
+            "website",
+            "command line",
+            "code"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.db.actions:ACTOR_MAX",
+          "equals": 200
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name",
+      "tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name",
+      "tests/test_web_fix10b.py::test_action_records_are_append_only",
+      "tests/test_migrations_step10b.py::test_an_action_on_the_website_names_its_person",
+      "tests/test_migrations_step10b.py::test_each_action_names_exactly_what_it_acts_on",
+      "tests/test_migrations_step10b.py::test_rows_are_never_changed_deleted_or_truncated"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11, fix round 1)."
+    ]
+  },
+  {
+    "key": "act_on_version_shown",
+    "name": "A page acts only on the version it showed",
+    "state": "in_force",
+    "statement": "Every website form that writes to a query (edit, review's dispatch and return, dispatch again) sends the version it displayed and a fingerprint of that version's content (SHA-256 of its query, number, status, hypothesis, domains, option, note, sources and review comment). The pipeline compares both with the stored version under the version lock, in the write's own transaction, and refuses a difference with \"This query has changed since you opened it; reload the page\". A form that sends neither is refused the same way. So an old review tab never dispatches or returns a newer version, and an old edit form never overwrites a newer draft or makes a second new version. Saving and submitting from one form is one transaction. The command line names the version it acts on and is not checked this way.",
+    "value": {
+      "text": "version id + content fingerprint, checked under the lock",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The query pages (PRD 9.2, 9.3).",
+    "reason": "ChatGPT's review of 10b, finding 1 (a stale review page dispatched a version it never showed); the owner's fix, in the owner's words for the refusal.",
+    "evidence": [
+      "Step 10b, fix round 1: ChatGPT's review of 2026-10-11 (docs/reviews/step10b_review_chatgpt.md), its three findings accepted by the owner the same day, with the owner's answer on storage (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.queries:STALE",
+          "equals": "This query has changed since you opened it; reload the page"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_fix10b.py::test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2",
+      "tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id",
+      "tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version",
+      "tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused",
+      "tests/test_web_fix10b.py::test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11, fix round 1)."
+    ]
+  },
+  {
+    "key": "export_no_formulas",
+    "name": "No formulas in exports",
+    "state": "in_force",
+    "statement": "In the workbook every text cell is written as a string cell, whatever it begins with, so stored text (a hypothesis, a paper reference, a note, a name, the Analyst's text) is never a formula. In the records CSV a text beginning with =, +, -, @, a tab or a carriage return gets a leading apostrophe; a number, or a text that is exactly a number, is written as it is. The stored rows are unchanged.",
+    "value": {
+      "text": "workbook: string cells; CSV: leading apostrophe",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The workbook and records CSV (PRD 11) and 'hypocurate export'.",
+    "reason": "ChatGPT's review of 10b, finding 2 (a stored '=1+1' became a formula cell); the owner's fix.",
+    "evidence": [
+      "Step 10b, fix round 1: ChatGPT's review of 2026-10-11 (docs/reviews/step10b_review_chatgpt.md), its three findings accepted by the owner the same day, with the owner's answer on storage (quoted in docs/reviews/step10b_summary.md)."
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
+          "ref": "python:hypocurate.pipeline.workbook:FORMULA_STARTS",
+          "equals": [
+            "=",
+            "+",
+            "-",
+            "@",
+            "\t",
+            "\r"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.pipeline.workbook:CSV_TEXT_MARK",
+          "equals": "'"
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell",
+      "tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers"
+    ],
+    "history": [],
+    "notes": [
+      "Wording drafted by Claude Code for the owner's review (2026-10-11, fix round 1)."
+    ]
   }
 ]
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 1af3c2d..1f1d359 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -22,6 +22,7 @@ def main(argv: list[str] | None = None) -> int:
     sources_sub = sources.add_subparsers(dest="sources_command", required=True)
     register = sources_sub.add_parser("register", help="register and seal the frozen sources")
     register.add_argument("keys", nargs="*", help="source keys (default: all)")
+    register.add_argument("--by", help="the name of the person registering (recorded with each version sealed)")
     test = sources_sub.add_parser("test", help="read a source and show sample records")
     test.add_argument("key")
     test.add_argument("-n", type=int, default=5, help="number of sample records (default 5)")
@@ -52,7 +53,8 @@ def main(argv: list[str] | None = None) -> int:
     run.add_argument("--queue", action="store_true", help="dispatch and return at once; a worker runs it (step 9b)")
     dispatch = sub.add_parser("dispatch", help="dispatch a submitted query by its number and run it (may cost money)")
     dispatch.add_argument("number", help="the query number, e.g. Q-0002")
-    dispatch.add_argument("--by", help="the name of the person confirming the domain (not with --again)")
+    dispatch.add_argument("--by", help="the name of the person confirming the domain and dispatching (required "
+                                       "without --again; with --again, recorded if given)")
     dispatch.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
     dispatch.add_argument("--queue", action="store_true", help="dispatch and return at once; a worker runs it")
     dispatch.add_argument("--again", action="store_true",
@@ -115,7 +117,7 @@ def _sources(args, engine) -> int:
     try:
         if args.sources_command == "register":
             for key in args.keys or list(SOURCES):
-                r = register(engine, key)
+                r = register(engine, key, by=args.by)
                 state = "registered and sealed" if r.created else "already registered"
                 print(f"{r.key}: {state}; version {r.version_id} ({r.label}); fingerprint {r.fingerprint}")
             return 0
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index 7e9a484..69bafb9 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -55,21 +55,21 @@ def command(args, engine: Engine) -> int:
         ceiling = _ceiling(args.ceiling)
         if args.command == "run":
             q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
-                               domain=args.domain, sufficiency=args.sufficiency)
-            queries.submit(engine, q.version_id)
+                               domain=args.domain, sufficiency=args.sufficiency, by=args.by)
+            queries.submit(engine, q.version_id, by=args.by)
             queries.confirm_domain(engine, q.version_id, by=args.by)
             run_id = queries.dispatch(engine, q.version_id, fixed_plan=args.fixed_plan,
-                                      constructed_test_data=args.test_data, ceiling=ceiling)
+                                      constructed_test_data=args.test_data, ceiling=ceiling, by=args.by)
             number = q.number
         elif args.again:
-            run_id, number = queries.dispatch_again(engine, args.number, ceiling=ceiling), args.number
+            run_id, number = queries.dispatch_again(engine, args.number, ceiling=ceiling, by=args.by), args.number
         else:
             if args.by is None:
                 raise ValueError("--by names the person confirming the domain")
             vid = queries.submitted_version(engine, args.number)
             queries.confirm_domain(engine, vid, by=args.by)
             # A narrower question's plan follows from its link (finding 1).
-            run_id = queries.dispatch(engine, vid, ceiling=ceiling)
+            run_id = queries.dispatch(engine, vid, ceiling=ceiling, by=args.by)
             number = args.number
     except queries.QueryRefused as refused:
         print(f"error: {refused.code}: {refused.reason}", file=sys.stderr)
diff --git a/hypocurate/db/actions.py b/hypocurate/db/actions.py
new file mode 100644
index 0000000..59ea11d
--- /dev/null
+++ b/hypocurate/db/actions.py
@@ -0,0 +1,41 @@
+"""Who did what (step 10b, fix round 1; migration 0009; owner, 2026-10-11).
+
+`record` writes one `action_record` row on the caller's connection, so it commits or rolls back with the write it
+records. The name is stored as given (trimmed): the website passes the signed-in name, which it requires; the command
+line passes `--by` where given, and no name otherwise; code's own action (a narrower question) has none. Nothing
+proves who typed a name (the step 10a sign-in). A record, not a gate: no rule reads it.
+"""
+from __future__ import annotations
+
+from sqlalchemy import Connection, text
+
+from hypocurate.db.models import ACTIONS, CHANNELS
+
+WEBSITE, COMMAND_LINE, CODE = CHANNELS
+ACTOR_MAX = 200
+
+
+class UnnamedAction(ValueError):
+    """An action on the website without the signed-in name, or a name longer than 200 characters."""
+
+
+def actor(by: str | None, channel: str) -> str | None:
+    """The name to store: trimmed; none for code's own action; required on the website."""
+    if channel not in CHANNELS:
+        raise ValueError(f"unknown channel {channel!r}")
+    name = by.strip() if isinstance(by, str) else ""
+    if channel == CODE:
+        return None
+    if len(name) > ACTOR_MAX or (channel == WEBSITE and not name):
+        raise UnnamedAction(f"an action on the website names the signed-in person (1 to {ACTOR_MAX} characters)")
+    return name or None
+
+
+def record(conn: Connection, action: str, by: str | None, channel: str, *, version: int | None = None,
+           run: int | None = None, source_version: int | None = None) -> None:
+    if action not in ACTIONS:
+        raise ValueError(f"unknown action {action!r}")
+    conn.execute(text(
+        "INSERT INTO action_record (action, channel, actor, hypothesis_version_id, run_id, source_version_id) "
+        "VALUES (:a, :c, :n, :v, :r, :s)"),
+        dict(a=action, c=channel, n=actor(by, channel), v=version, r=run, s=source_version))
diff --git a/hypocurate/db/migrations/versions/0009_action_record.py b/hypocurate/db/migrations/versions/0009_action_record.py
new file mode 100644
index 0000000..e223aa8
--- /dev/null
+++ b/hypocurate/db/migrations/versions/0009_action_record.py
@@ -0,0 +1,131 @@
+"""Who did what: one row per person's action (build step 10b, fix round 1).
+
+Revision ID: 0009
+Revises: 0008
+Create Date: 2026-10-11
+
+Approved by the owner on 2026-10-11 ("New table action_record, migration 0009, as you recommend. Also write a row
+for confirm and cancel, which already store the name elsewhere, so that 'who did what' is complete in one place;
+keep their existing records unchanged"), after ChatGPT's review of step 10b (finding 3), subject to the second-model
+re-check before merging. 0001 to 0008 untouched: no earlier function is replaced.
+
+action_record, append-only (never updated, deleted or truncated):
+- the action, from a fixed list (`ACTIONS`); where it was done (`CHANNELS`: the website, the command line, or code);
+- the actor's name as given (1-200 characters, trimmed), required for an action on the website (the signed-in name);
+  absent when none was given at the command line, and for code's own action (a narrower question code creates);
+- what it acted on: the query version, the run and/or the source version, as the action requires (`TARGETS`);
+- the time, the database's (set by the insert trigger, whatever the insert says).
+It is written in the same transaction as the write it records (pipeline/queries.py, pipeline/confirmation.py,
+sources/versions.py). It is a record, not a gate: no other table's rule reads it.
+
+Works with the previous release's code: it never reads or writes action_record.
+
+Downgrade refuses while any row exists (the rows are history), then drops what 0009 added.
+
+Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it keeps
+working with the previous release's code; and it has a downgrade.
+"""
+from alembic import op
+import sqlalchemy as sa
+
+revision = '0009'
+down_revision = '0008'
+branch_labels = None
+depends_on = None
+
+# Copied here so the migration does not change when the code does (tests check they equal the code's lists).
+ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
+           "cancel", "confirm_rules", "register_source")
+CHANNELS = ("website", "command line", "code")
+ACTOR_MAX = 200
+# What each action names: v = the query version, r = the run, s = the source version.
+TARGETS = {"create": "v", "edit": "v", "new_version": "v", "submit": "v", "return": "v", "confirm_domain": "v",
+           "dispatch": "vr", "dispatch_again": "vr", "cancel": "r", "confirm_rules": "r", "register_source": "s"}
+COLUMNS = {"v": "hypothesis_version_id", "r": "run_id", "s": "source_version_id"}
+
+
+def _in(column: str, values) -> str:
+    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"
+
+
+def targets_check() -> str:
+    """Each action names exactly what it acts on, and nothing else."""
+    cases = []
+    for action, kinds in TARGETS.items():
+        parts = [f"{col} IS {'NOT ' if k in kinds else ''}NULL" for k, col in COLUMNS.items()]
+        cases.append(f"(action = '{action}' AND " + " AND ".join(parts) + ")")
+    return " OR ".join(cases)
+
+
+FUNCTIONS = [
+    # The database's time, whatever the insert says.
+    """
+    CREATE FUNCTION hc_action_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        NEW.at := now();
+        RETURN NEW;
+    END $$
+    """,
+]
+FUNCTION_NAMES = ["hc_action_record_insert()"]
+
+APPEND_ONLY = ["action_record"]
+CHECKED = [("action_record", "INSERT", "hc_action_record_insert", "hc_action_record_insert")]
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
+def upgrade() -> None:
+    op.create_table(
+        'action_record',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.Column('action', sa.Text(), nullable=False),
+        sa.Column('channel', sa.Text(), nullable=False),
+        sa.Column('actor', sa.Text(), nullable=True),
+        sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=True),
+        sa.Column('run_id', sa.BigInteger(), nullable=True),
+        sa.Column('source_version_id', sa.BigInteger(), nullable=True),
+        sa.CheckConstraint(_in('action', ACTIONS), name=op.f('ck_action_record_action')),
+        sa.CheckConstraint(_in('channel', CHANNELS), name=op.f('ck_action_record_channel')),
+        sa.CheckConstraint(f"actor IS NULL OR (actor = btrim(actor) AND length(actor) BETWEEN 1 AND {ACTOR_MAX})",
+                           name=op.f('ck_action_record_actor')),
+        sa.CheckConstraint("channel <> 'website' OR actor IS NOT NULL", name=op.f('ck_action_record_website_named')),
+        sa.CheckConstraint("channel <> 'code' OR actor IS NULL", name=op.f('ck_action_record_code_unnamed')),
+        sa.CheckConstraint(targets_check(), name=op.f('ck_action_record_targets')),
+        sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'],
+                                name=op.f('fk_action_record_hypothesis_version_id')),
+        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_action_record_run_id')),
+        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
+                                name=op.f('fk_action_record_source_version_id')),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_action_record')),
+    )
+    op.create_index('ix_action_record_hypothesis_version_id', 'action_record', ['hypothesis_version_id'])
+    op.create_index('ix_action_record_run_id', 'action_record', ['run_id'])
+    for f in FUNCTIONS:
+        op.execute(f)
+    for t in TRIGGERS:
+        op.execute(t)
+
+
+IN_USE = """
+    DO $$
+    BEGIN
+        IF EXISTS (SELECT 1 FROM action_record) THEN
+            RAISE EXCEPTION 'hypocurate: migration 0009 is in use (an action is recorded); not downgraded';
+        END IF;
+    END $$
+"""
+
+
+def downgrade() -> None:
+    op.execute(IN_USE)
+    op.drop_table('action_record')
+    for f in FUNCTION_NAMES:
+        op.execute(f"DROP FUNCTION {f}")
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 357f4e6..6c24ff6 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -440,6 +440,46 @@ class RunClaim(Base):
     )
 
 
+
+# Step 10b, fix round 1 (0009; owner, 2026-10-11): who did what. The same lists as migration 0009 (tests check both).
+ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
+           "cancel", "confirm_rules", "register_source")
+CHANNELS = ("website", "command line", "code")
+# What each action names: v = the query version, r = the run, s = the source version.
+ACTION_TARGETS = {"create": "v", "edit": "v", "new_version": "v", "submit": "v", "return": "v", "confirm_domain": "v",
+                  "dispatch": "vr", "dispatch_again": "vr", "cancel": "r", "confirm_rules": "r", "register_source": "s"}
+_TARGET_COLUMNS = {"v": "hypothesis_version_id", "r": "run_id", "s": "source_version_id"}
+
+
+def _targets_check() -> str:
+    return " OR ".join(
+        f"(action = '{action}' AND " + " AND ".join(
+            f"{col} IS {'NOT ' if k in kinds else ''}NULL" for k, col in _TARGET_COLUMNS.items()) + ")"
+        for action, kinds in ACTION_TARGETS.items())
+
+
+class ActionRecord(Base):
+    """Step 10b, fix round 1 (0009): one row per person's action, written in the same transaction as the write it
+    records: the action, where (website, command line, code), the name given (required on the website), what it acted
+    on, and the database's time. Append-only. A record, not a gate."""
+    __tablename__ = "action_record"
+    id: Mapped[int] = pk()
+    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
+    action: Mapped[str] = mapped_column(Text)
+    channel: Mapped[str] = mapped_column(Text)
+    actor: Mapped[str | None] = mapped_column(Text)
+    hypothesis_version_id: Mapped[int | None] = mapped_column(ForeignKey("hypothesis_version.id"), index=True)
+    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"), index=True)
+    source_version_id: Mapped[int | None] = mapped_column(ForeignKey("source_version.id"))
+    __table_args__ = (
+        CheckConstraint(one_of("action", ACTIONS), name="action"),
+        CheckConstraint(one_of("channel", CHANNELS), name="channel"),
+        CheckConstraint("actor IS NULL OR (actor = btrim(actor) AND length(actor) BETWEEN 1 AND 200)", name="actor"),
+        CheckConstraint("channel <> 'website' OR actor IS NOT NULL", name="website_named"),
+        CheckConstraint("channel <> 'code' OR actor IS NULL", name="code_unnamed"),
+        CheckConstraint(_targets_check(), name="targets"),
+    )
+
 class Plan(Base):
     """The locked plan (PRD 5.1, 5.6). Inserted at the rules lock, never changed.
     The columns the database checks against are explicit; the rest is `content`."""
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
index 0e4ced4..73af0dd 100644
--- a/hypocurate/pipeline/confirmation.py
+++ b/hypocurate/pipeline/confirmation.py
@@ -289,12 +289,14 @@ def show(engine: Engine, run_id: int) -> tuple[dict, str]:
 
 
 def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None,
-            shown_fingerprint: str | None = None) -> dict:
+            shown_fingerprint: str | None = None, *, via: str = "command line") -> dict:
     """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; or
     `shown_fingerprint`: the `shown_fingerprint` of the content and the text displayed (step 10a, owner's addition 2;
     fix round 1, finding 1). The content is read and the text rendered in the same transaction as the insert; the
     confirmation is refused as `content_changed` if either differs from what was shown, so the text stored is exactly
-    the text the fingerprint covered. Returns the stored content and text."""
+    the text the fingerprint covered. Returns the stored content and text. Step 10b, fix round 1 (owner): an
+    `action_record` row too, in the same transaction (`via`: the command line or the website); the confirmation's own
+    row is unchanged."""
     name = (by or "").strip()
     if not name or len(name) > CONFIRMED_BY_MAX:
         raise QueryRefused("name_required", f"a confirmation names the person (1 to {CONFIRMED_BY_MAX} characters)")
@@ -326,6 +328,8 @@ def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | Non
             bindparam("c", type_=JSONB)), dict(r=run_id, b=name, fp=c["plan_fingerprint"],
                                                 p=c["planner_stage_result_id"], n=c["narrowing_stage_result_id"],
                                                 c=c, s=words))
+        from hypocurate.db import actions
+        actions.record(conn, "confirm_rules", name, via, run=run_id)
         return {"content": c, "shown": words}
 
     try:
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
index 5314709..784cdd0 100644
--- a/hypocurate/pipeline/queries.py
+++ b/hypocurate/pipeline/queries.py
@@ -26,6 +26,13 @@ Every write follows the locking protocol (README, "Database migrations"): `run_t
 - `create_narrower`: the narrower question of a run completed as partly sufficient (owner, Q10, A8): a
   separate query linked to that run, created as submitted, with its original's domain, sources and option,
   and a text built by code from `NARROWER_TEXT`.
+- Step 10b, fix round 1 (ChatGPT's review; the owner, 2026-10-11):
+  - who did it: every write records its action, the name given and where (`db/actions.record`, table
+    `action_record`, migration 0009) in its own transaction; `via` is the website, the command line or code;
+  - act only on the version shown: the website sends the version it displayed and its `version_fingerprint`; each
+    write compares both with the stored version under the version lock, in its transaction, and refuses a
+    difference as `stale` (`STALE`). On the website both are required. A page that submits passes `submit=True`,
+    so the version written is the version submitted, in one transaction.
 """
 from __future__ import annotations
 
@@ -36,6 +43,8 @@ from typing import Iterable, Mapping
 
 from sqlalchemy import Connection, Engine, text
 
+from hypocurate.db import actions
+from hypocurate.db.actions import CODE, COMMAND_LINE, WEBSITE as VIA_WEBSITE
 from hypocurate.db.retry import run_transaction
 from hypocurate.pipeline.agents import settings as agent_settings
 
@@ -56,6 +65,11 @@ CANCELLED = {"queued": "cancelled: cancelled by {by} before it started",
              "waiting": "cancelled: cancelled by {by} while waiting for confirmation of the question as tested"}
 
 
+# Step 10b, fix round 1 (owner's words, 2026-10-11): a page acting on a version that changed since it was shown.
+STALE = "This query has changed since you opened it; reload the page"
+WHERE_WORDS = {COMMAND_LINE: "at the command line", VIA_WEBSITE: "on the website"}  # in the stored domain comment
+
+
 class QueryRefused(Exception):
     """A query operation refused with a fixed code and a stated reason."""
 
@@ -76,6 +90,43 @@ def _lock_version(conn: Connection, version_id: int) -> str:
     return conn.execute(text("SELECT hc_write_lock(p_version => :v)"), dict(v=version_id)).scalar_one()
 
 
+def _fingerprint(conn: Connection, version_id: int) -> str | None:
+    """SHA-256 of the canonical JSON of what a page shows of a version: its query, number, status, hypothesis,
+    domains, option, note, sources and review comment."""
+    import hashlib
+    row = conn.execute(text(
+        "SELECT hv.id, h.number, hv.version_number, hv.status, hv.text, d.key AS domain, cd.key AS confirmed_domain, "
+        "hv.sufficiency_option, hv.note, hv.review_comment, ARRAY(SELECT s.key FROM hypothesis_version_source hvs "
+        "JOIN source s ON s.id = hvs.source_id WHERE hvs.hypothesis_version_id = hv.id ORDER BY s.key) AS sources "
+        "FROM hypothesis_version hv JOIN hypothesis h ON h.id = hv.hypothesis_id JOIN domain d ON d.id = hv.domain_id "
+        "LEFT JOIN domain cd ON cd.id = hv.confirmed_domain_id WHERE hv.id = :v"), dict(v=version_id)).one_or_none()
+    if row is None:
+        return None
+    content = dict(row._mapping)
+    content["sources"] = list(content["sources"])
+    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False,
+                                     separators=(",", ":")).encode("utf-8")).hexdigest()
+
+
+def version_fingerprint(bind: Engine | Connection, version_id: int) -> str | None:
+    """The fingerprint of a version as stored now (a page sends it back with the version's id)."""
+    if isinstance(bind, Connection):
+        return _fingerprint(bind, version_id)
+    with bind.connect() as conn:
+        return _fingerprint(conn, version_id)
+
+
+def _check_shown(conn: Connection, version_id: int, expected_version: int | None, expected_fingerprint: str | None,
+                 via: str) -> None:
+    """Under the version lock: the version acted on is the one the page showed, unchanged. The website always sends
+    both; the command line acts on what it names."""
+    if expected_version is None and expected_fingerprint is None and via != VIA_WEBSITE:
+        return
+    if (expected_version is not None and expected_version != version_id) or not expected_fingerprint \
+            or _fingerprint(conn, version_id) != expected_fingerprint:
+        raise QueryRefused("stale", STALE)
+
+
 def _domain_id(conn: Connection, key: str) -> int:
     found = conn.execute(text("SELECT id FROM domain WHERE key = :k"), dict(k=key)).scalar_one_or_none()
     if found is None:
@@ -94,8 +145,11 @@ def _source_ids(conn: Connection, keys: Iterable[str]) -> list[int]:
 
 
 def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "grain_size_strengthening",
-           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None, note: str | None = None) -> Query:
-    """A new query with one draft version (step 10b: with the submitter's optional note)."""
+           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None, note: str | None = None, *,
+           by: str | None = None, via: str = COMMAND_LINE, submit: bool = False) -> Query:
+    """A new query with one draft version (step 10b: with the submitter's optional note); with `submit`, submitted
+    in the same transaction."""
+    actions.actor(by, via)
     claim, note = _claim_text(claim), _note_text(note)
     sources = list(dict.fromkeys(sources))
     if not sources:
@@ -111,37 +165,47 @@ def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "gr
             dict(h=h.id, t=claim, d=domain_id, o=sufficiency, n=note)).scalar_one()
         for sid in source_ids:
             conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
+        actions.record(conn, "create", by, via, version=vid)
+        if submit:
+            _submit_in(conn, vid, by, via)
         return Query(h.id, h.number, vid)
 
     return run_transaction(engine, body)
 
 
-def submit(engine: Engine, version_id: int) -> None:
-    def body(conn: Connection):
-        _lock_version(conn, version_id)
-        conn.execute(text("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v"),
-                     dict(v=version_id))
+def _submit_in(conn: Connection, version_id: int, by: str | None, via: str) -> None:
+    _lock_version(conn, version_id)
+    conn.execute(text("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v"),
+                 dict(v=version_id))
+    actions.record(conn, "submit", by, via, version=version_id)
 
-    run_transaction(engine, body)
+
+def submit(engine: Engine, version_id: int, *, by: str | None = None, via: str = COMMAND_LINE) -> None:
+    actions.actor(by, via)
+    run_transaction(engine, lambda conn: _submit_in(conn, version_id, by, via))
 
 
-def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None,
-                   where: str = "at the command line") -> None:
-    """A named person confirms the domain (or changes it to `domain`) while the version is submitted. `where`: the
-    command line, or the website (step 10b)."""
+def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None, *, via: str = COMMAND_LINE,
+                   expected_fingerprint: str | None = None) -> str:
+    """A named person confirms the domain (or changes it to `domain`) while the version is submitted, on the command
+    line or the website (`via`, step 10b; its words in the stored comment, `WHERE_WORDS`). Returns the version's
+    fingerprint after the change, which the website's dispatch then sends (fix round 1)."""
     if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
         raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")
 
     def body(conn: Connection):
         _lock_version(conn, version_id)
+        _check_shown(conn, version_id, None, expected_fingerprint, via)
         chosen = conn.execute(text("SELECT domain_id FROM hypothesis_version WHERE id = :v"),
                               dict(v=version_id)).scalar_one()
         domain_id = _domain_id(conn, domain) if domain else chosen
         conn.execute(text("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now(), "
                           "review_comment = :c WHERE id = :v"),
-                     dict(d=domain_id, c=f"domain confirmed {where} by {by.strip()}", v=version_id))
+                     dict(d=domain_id, c=f"domain confirmed {WHERE_WORDS[via]} by {by.strip()}", v=version_id))
+        actions.record(conn, "confirm_domain", by, via, version=version_id)
+        return _fingerprint(conn, version_id)
 
-    run_transaction(engine, body)
+    return run_transaction(engine, body)
 
 
 def _ceiling(ceiling) -> Decimal | None:
@@ -168,20 +232,25 @@ def _dispatch_checks(conn: Connection, version_id: int, constructed_test_data: b
 
 
 def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False,
-             ceiling: Decimal | None = None) -> int:
+             ceiling: Decimal | None = None, by: str | None = None, via: str = COMMAND_LINE,
+             expected_fingerprint: str | None = None) -> int:
     """Dispatches the version; returns the queued run's id. `fixed_plan` asks for the reference plan (14.1a). A
     narrower question's run always uses the plan its original's narrowing decision stored: that comes from the
     question's link to its original, never from the caller's flag (step 8b fix round, finding 1; the database
     refuses such a run without the flag, migration 0006). `ceiling`: stored on the run (step 9a, R5)."""
     ceiling = _ceiling(ceiling)
+    actions.actor(by, via)
     setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}
 
     def body(conn: Connection):
         _lock_version(conn, version_id)
+        _check_shown(conn, version_id, None, expected_fingerprint, via)
         _dispatch_checks(conn, version_id, constructed_test_data)
         conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
                      dict(v=version_id))
-        return _new_run(conn, version_id, fixed_plan, constructed_test_data, ceiling, setting_ids)
+        rid = _new_run(conn, version_id, fixed_plan, constructed_test_data, ceiling, setting_ids)
+        actions.record(conn, "dispatch", by, via, version=version_id, run=rid)
+        return rid
 
     return run_transaction(engine, body)
 
@@ -222,10 +291,13 @@ def _new_run(conn: Connection, version_id: int, fixed_plan: bool, constructed_te
     return rid
 
 
-def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = None) -> int:
+def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = None, by: str | None = None,
+                   via: str = COMMAND_LINE, expected_version: int | None = None,
+                   expected_fingerprint: str | None = None) -> int:
     """A new queued run of query `number`'s dispatched version, once no run of the query is open (PRD 8, 14.4). It
     records what the version's latest run recorded (fixed plan, test mark), and the ceiling only as given now."""
     ceiling = _ceiling(ceiling)
+    actions.actor(by, via)
     with engine.connect() as conn:
         vid = conn.execute(text(
             "SELECT hv.id FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
@@ -237,6 +309,7 @@ def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = Non
 
     def body(conn: Connection):
         _lock_version(conn, vid)
+        _check_shown(conn, vid, expected_version, expected_fingerprint, via)
         if conn.execute(text("SELECT EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = "
                              "r.hypothesis_version_id WHERE hv.hypothesis_id = (SELECT hypothesis_id FROM "
                              "hypothesis_version WHERE id = :v) AND r.status IN ('queued', 'waiting', 'running'))"),
@@ -246,12 +319,14 @@ def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = Non
                                  "ORDER BY id DESC LIMIT 1"), dict(v=vid)).one()
         marked = isinstance(last.experiment_flags, dict) and last.experiment_flags.get(CONSTRUCTED_MARK) is True
         _dispatch_checks(conn, vid, marked)
-        return _new_run(conn, vid, last.fixed_plan, marked, ceiling, setting_ids)
+        rid = _new_run(conn, vid, last.fixed_plan, marked, ceiling, setting_ids)
+        actions.record(conn, "dispatch_again", by, via, version=vid, run=rid)
+        return rid
 
     return run_transaction(engine, body)
 
 
-def cancel(engine: Engine, run_id: int, by: str) -> str:
+def cancel(engine: Engine, run_id: int, by: str, *, via: str = COMMAND_LINE) -> str:
     """A named person cancels a queued or a waiting run (R3); returns the reason recorded. Refused for any other
     status (a started run cannot be cancelled in sprint 1)."""
     name = by.strip() if isinstance(by, str) else ""
@@ -269,6 +344,7 @@ def cancel(engine: Engine, run_id: int, by: str) -> str:
         reason = CANCELLED[status].format(by=name)
         conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
                      dict(f=reason, r=run_id))
+        actions.record(conn, "cancel", name, via, run=run_id)  # the failure reason above is unchanged (owner)
         return reason
 
     return run_transaction(engine, body)
@@ -309,7 +385,7 @@ def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping)
             dict(r=original_run)).one_or_none()
     if existing is not None:
         if existing.status == "draft":
-            submit(engine, existing.vid)
+            submit(engine, existing.vid, via=CODE)
         return Query(existing.id, existing.number, existing.vid)
     with engine.connect() as conn:
         row = conn.execute(text(
@@ -320,15 +396,15 @@ def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping)
             "SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
             "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=row.vid)).scalars())
     q = create(engine, NARROWER_TEXT.format(original=row.text, scope=scope_in_words(narrower_scope)), sources,
-               domain=row.domain, sufficiency=row.sufficiency_option, narrower_of_run=original_run)
-    submit(engine, q.version_id)
+               domain=row.domain, sufficiency=row.sufficiency_option, narrower_of_run=original_run, via=CODE)
+    submit(engine, q.version_id, via=CODE)
     return q
 
 
 CLAIM_MAX = 2000      # step 10b: the hypothesis text, as typed on the new-query page
 NOTE_MAX = 2000       # the submitter's note to the reviewer
 COMMENT_MAX = 2000    # the reviewer's comment when returning a query
-WEBSITE = "on the website"  # where a domain is confirmed (step 10b)
+WEBSITE = VIA_WEBSITE  # step 10b: a write from the website (`via`); its words are in WHERE_WORDS
 
 
 def _claim_text(claim: str) -> str:
@@ -358,14 +434,18 @@ def _version(conn: Connection, number: str):
 
 
 def update_draft(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
-                 note: str | None) -> int:
-    """Step 10b: a draft is edited in place (it was never submitted); its sources are replaced. Returns its id."""
+                 note: str | None, *, by: str | None = None, via: str = COMMAND_LINE, submit: bool = False,
+                 expected_version: int | None = None, expected_fingerprint: str | None = None) -> int:
+    """Step 10b: a draft is edited in place (it was never submitted); its sources are replaced. Returns its id. Fix
+    round 1: only the version shown, unchanged, is edited; with `submit`, it is submitted in the same transaction."""
     claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
+    actions.actor(by, via)
     if not sources:
         raise QueryRefused("no_source", "a query chooses at least one source")
 
     def body(conn: Connection):
         v = _version(conn, number)
+        _check_shown(conn, v.id, expected_version, expected_fingerprint, via)
         if v.status != "draft":
             raise QueryRefused("not_a_draft", f"query {number} is {v.status}; only a draft is edited in place")
         conn.execute(text("UPDATE hypothesis_version SET text = :t, domain_id = :d, sufficiency_option = :o, "
@@ -374,21 +454,28 @@ def update_draft(engine: Engine, number: str, claim: str, sources: Iterable[str]
         conn.execute(text("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v"), dict(v=v.id))
         for sid in _source_ids(conn, sources):
             conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=v.id, s=sid))
+        actions.record(conn, "edit", by, via, version=v.id)
+        if submit:
+            _submit_in(conn, v.id, by, via)
         return v.id
 
     return run_transaction(engine, body)
 
 
 def new_version(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
-                note: str | None) -> int:
+                note: str | None, *, by: str | None = None, via: str = COMMAND_LINE, submit: bool = False,
+                expected_version: int | None = None, expected_fingerprint: str | None = None) -> int:
     """Step 10b (PRD 9.2): editing a returned query creates its next version, a draft; earlier versions are kept
-    unchanged. Returns the new version's id."""
+    unchanged. Returns the new version's id. Fix round 1: only from the returned version shown (so an old form
+    never makes a second new version); with `submit`, submitted in the same transaction."""
     claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
+    actions.actor(by, via)
     if not sources:
         raise QueryRefused("no_source", "a query chooses at least one source")
 
     def body(conn: Connection):
         v = _version(conn, number)
+        _check_shown(conn, v.id, expected_version, expected_fingerprint, via)
         if v.status != "returned":
             raise QueryRefused("not_returned", f"query {number} is {v.status}; a new version follows a returned one")
         vid = conn.execute(text(
@@ -398,12 +485,16 @@ def new_version(engine: Engine, number: str, claim: str, sources: Iterable[str],
                  note=note)).scalar_one()
         for sid in _source_ids(conn, sources):
             conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
+        actions.record(conn, "new_version", by, via, version=vid)
+        if submit:
+            _submit_in(conn, vid, by, via)
         return vid
 
     return run_transaction(engine, body)
 
 
-def return_for_edits(engine: Engine, version_id: int, by: str, comment: str) -> None:
+def return_for_edits(engine: Engine, version_id: int, by: str, comment: str, *, via: str = COMMAND_LINE,
+                     expected_fingerprint: str | None = None) -> None:
     """Step 10b (PRD 9.3): the reviewer returns a submitted version for edits, with a comment; it never changes again,
     and an edit is its next version."""
     if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
@@ -414,11 +505,13 @@ def return_for_edits(engine: Engine, version_id: int, by: str, comment: str) ->
 
     def body(conn: Connection):
         status = _lock_version(conn, version_id)
+        _check_shown(conn, version_id, None, expected_fingerprint, via)
         if status != "submitted":
             raise QueryRefused("not_submitted", f"this version is {status}; only a submitted version is returned")
         conn.execute(text("UPDATE hypothesis_version SET status = 'returned', returned_at = now(), "
                           "review_comment = :c WHERE id = :v"),
                      dict(c=f"returned by {by.strip()}: {comment}", v=version_id))
+        actions.record(conn, "return", by, via, version=version_id)
 
     run_transaction(engine, body)
 
diff --git a/hypocurate/pipeline/query_view.py b/hypocurate/pipeline/query_view.py
index fa5c5c8..94ee857 100644
--- a/hypocurate/pipeline/query_view.py
+++ b/hypocurate/pipeline/query_view.py
@@ -8,7 +8,7 @@ from __future__ import annotations
 
 from sqlalchemy import Connection, Engine, text
 
-from hypocurate.pipeline import run_view
+from hypocurate.pipeline import queries, run_view
 from hypocurate.pipeline.run_view import STATUS_WORDS, money, snapshot, tokens
 
 # Short source names for the queries list (owner's review, 2026-10-11); a query's own page gives the full names.
@@ -106,7 +106,9 @@ def query_page(engine: Engine, number: str) -> dict:
                                                    failed=r.status == "failed")}
                     for r in conn.execute(text("SELECT id, status, evidence_level, experiment_flags FROM run WHERE "
                                                "hypothesis_version_id = :v ORDER BY id DESC"), dict(v=v.id)).all()]
-            versions.append({"version": v.version_number, "claim": v.text, "status": v.status,
+            # Fix round 1: the version's id and fingerprint, from this snapshot, so a form acts only on what it shows.
+            versions.append({"id": v.id, "fingerprint": queries.version_fingerprint(conn, v.id),
+                             "version": v.version_number, "claim": v.text, "status": v.status,
                              "status_words": VERSION_STATUS_WORDS[v.status], "note": v.note,
                              "review_comment": v.review_comment, "created": v.created,
                              "domain": v.confirmed_domain or v.domain, "domain_key": v.domain_key,
@@ -173,10 +175,9 @@ def review_page(engine: Engine, number: str) -> dict:
     latest = page["latest"]
     if latest["status"] != "submitted":
         return {**page, "reviewable": False}
+    # Fix round 1: the version acted on is the one shown (its id and fingerprint from query_page's snapshot).
+    version_id, domain_key = latest["id"], latest["domain_key"]
     with snapshot(engine) as conn:
-        version_id, domain_key = conn.execute(text(
-            "SELECT v.id, d.key FROM hypothesis_version v JOIN hypothesis h ON h.id = v.hypothesis_id JOIN domain d "
-            "ON d.id = v.domain_id WHERE h.number = :n AND v.status = 'submitted'"), dict(n=number)).one()
         agents = [{"role": role, "version": conn.execute(text(
             "SELECT max(version) FROM agent_setting WHERE role = :r"), dict(r=role)).scalar_one()}
             for role in settings.RUN_ROLES]
diff --git a/hypocurate/pipeline/workbook.py b/hypocurate/pipeline/workbook.py
index d61aa86..06d2a19 100644
--- a/hypocurate/pipeline/workbook.py
+++ b/hypocurate/pipeline/workbook.py
@@ -15,12 +15,19 @@ Four sheets:
 Every sheet's first line states the workbook's format and the code version that built it. The workbook's document
 dates are the run's dispatch time; the same stored rows give the same cells (the zip file's own timestamps, written by
 the spreadsheet library, are not fixed, so the bytes may differ). Read in one snapshot.
+
+No formulas (step 10b, fix round 1; ChatGPT's review, the owner's decision of 2026-10-11): every text cell of the
+workbook is written as a string cell, whatever it begins with, so stored text (a hypothesis, a paper reference, a
+note, a name, the Analyst's text) is never read as a formula. In the CSV, which a spreadsheet opens as typed, a text
+that begins with =, +, -, @, a tab or a carriage return gets a leading apostrophe (`FORMULA_STARTS`, `csv_cell`); a
+genuine number is written as it is.
 """
 from __future__ import annotations
 
 import csv
 import io
 import json
+import re
 from datetime import datetime, timezone
 from typing import Any, Mapping
 
@@ -34,6 +41,26 @@ WORKBOOK_FORMAT = 1
 SHEETS = ("Records used", "Records not used", "Significance and commentary", "Run summary")
 BASE_COLUMNS = ("record", "source", "item", "alloy", "kind of data", "paper reference", "paper DOI")
 COMMENTARY_NONE = "No commentary: the Commentator is not built in sprint 1 (PRD 15, step 12)."
+# Fix round 1: what a spreadsheet may read as the start of a formula in a CSV cell, and what a genuine number is.
+FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")
+CSV_TEXT_MARK = "'"
+_NUMBER = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?")
+
+
+def csv_cell(value: Any) -> Any:
+    """A CSV cell: text beginning with a formula sign gets a leading apostrophe; numbers (and text that is exactly a
+    number) are kept as they are."""
+    if isinstance(value, str) and value.startswith(FORMULA_STARTS) and not _NUMBER.fullmatch(value):
+        return CSV_TEXT_MARK + value
+    return value
+
+
+def _append(ws, values) -> None:
+    """One row; every text cell a string cell (never a formula)."""
+    ws.append(list(values))
+    for cell in ws[ws.max_row]:
+        if isinstance(cell.value, str):
+            cell.data_type = "s"
 
 
 def version_line() -> str:
@@ -122,10 +149,18 @@ def _summary(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
         "SELECT s.key, sv.label, sv.fingerprint, rs.search_status FROM run_source rs JOIN source s ON s.id = "
         "rs.source_id LEFT JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r ORDER BY s.key"),
         dict(r=run_id)).all()
+    version = conn.execute(text(
+        "SELECT hv.id, hv.note, hv.review_comment FROM run r JOIN hypothesis_version hv ON hv.id = "
+        "r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).one()
+    done = conn.execute(text(
+        "SELECT action, channel, actor, to_char(at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS') AS at FROM "
+        "action_record WHERE hypothesis_version_id = :v OR run_id = :r ORDER BY id"),
+        dict(v=version.id, r=run_id)).all()
     cp = page["checkpoints"]
     rows: list[tuple[str, Any]] = [
         ("Query", f"{page['query']}, version {page['version']}"), ("Run", run_id),
-        ("Hypothesis", page["claim"]), ("Domain", page["domain"]), ("Tags", "; ".join(page["tags"]) or None),
+        ("Hypothesis", page["claim"]), ("Note", version.note), ("Review", version.review_comment),
+        ("Domain", page["domain"]), ("Tags", "; ".join(page["tags"]) or None),
         ("Status", page["status_words"]), ("Outcome", page["outcome"]), ("Verdict", page["verdict"]),
         ("Evidence level", page["evidence"]["words"]),
         ("Question as tested", (page["question_as_tested"] or {}).get("text")),
@@ -155,6 +190,9 @@ def _summary(conn: Connection, run_id: int) -> list[tuple[str, Any]]:
              ("Agent mode", head.agent_mode.replace("_", " ")),
              ("Agent settings versions", "; ".join(f"{r.role} {r.version}" for r in settings) or None),
              ("Dispatched (UTC)", head.queued), ("Started (UTC)", head.started), ("Ended (UTC)", head.ended)]
+    # Fix round 1 (0009): who did what to this version and this run, as recorded.
+    rows += [(f"Action: {a.action.replace('_', ' ')} ({a.channel})", f"{a.actor or 'no name given'}, {a.at} UTC")
+             for a in done]
     return rows
 
 
@@ -208,16 +246,16 @@ def build(engine: Engine, run_id: int) -> bytes | None:
     for title, rows, extra in ((SHEETS[0], used, ()), (SHEETS[1], other, ("eligible", "rule", "flags",
                                                                            "sensitivity sets"))):
         ws = wb.create_sheet(title)
-        ws.append([version_line()])
-        ws.append([*columns, *extra])
+        _append(ws, [version_line()])
+        _append(ws, [*columns, *extra])
         for r in rows:
-            ws.append([r.get(c) for c in (*columns, *extra)])
+            _append(ws, [r.get(c) for c in (*columns, *extra)])
     for title, rows in ((SHEETS[2], significance), (SHEETS[3], summary)):
         ws = wb.create_sheet(title)
-        ws.append([version_line()])
-        ws.append(["Item", "Value"])
+        _append(ws, [version_line()])
+        _append(ws, ["Item", "Value"])
         for item, value in rows:
-            ws.append([item, value])
+            _append(ws, [item, value])
     wb.properties.created = wb.properties.modified = when
     wb.properties.creator = "HypoCurate"
     out = io.BytesIO()
@@ -235,7 +273,7 @@ def records_csv(engine: Engine, run_id: int) -> str | None:
     w = csv.writer(buf, lineterminator="\n")
     w.writerow([f"# {version_line()}"])
     header = [*columns, "used in the test", "eligible", "rule", "flags", "sensitivity sets"]
-    w.writerow(header)
+    w.writerow([csv_cell(c) for c in header])
     for r in records:
-        w.writerow([r.get(c) if c != "used in the test" else ("yes" if r["_used"] else "no") for c in header])
+        w.writerow([csv_cell(r.get(c)) if c != "used in the test" else ("yes" if r["_used"] else "no") for c in header])
     return buf.getvalue()
diff --git a/hypocurate/sources/versions.py b/hypocurate/sources/versions.py
index f72180b..73921fe 100644
--- a/hypocurate/sources/versions.py
+++ b/hypocurate/sources/versions.py
@@ -271,14 +271,27 @@ def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes],
     return Registered(d.key, source_id, version_id, label, digest, identity, created=True)
 
 
-def register(engine: Engine, key: str, data_dir: Path = DATA_DIR, manifest: dict | None = None) -> Registered:
+def register(engine: Engine, key: str, data_dir: Path = DATA_DIR, manifest: dict | None = None, *,
+             by: str | None = None, via: str = "command line") -> Registered:
     """Registers source `key` and seals its version, or returns the identical sealed
-    version if it is already registered. One transaction, retried on 40P01 / 40001."""
+    version if it is already registered. One transaction, retried on 40P01 / 40001.
+    Step 10b, fix round 1: a version sealed here is recorded in `action_record` with the name
+    given (`by`; required on the website) in the same transaction; finding it already
+    registered writes nothing."""
+    from hypocurate.db import actions
     if key not in SOURCES:
         raise RegistrationError(f"unknown source {key!r}; known: {', '.join(SOURCES)}")
+    actions.actor(by, via)
     d = SOURCES[key]
     files, obtained = read_definition_files(d, data_dir, manifest)
-    return run_transaction(engine, lambda conn: _register_in(conn, d, files, obtained))
+
+    def body(conn: Connection) -> Registered:
+        done = _register_in(conn, d, files, obtained)
+        if done.created:
+            actions.record(conn, "register_source", by, via, source_version=done.version_id)
+        return done
+
+    return run_transaction(engine, body)
 
 
 # --- Loading a sealed version for an adapter ----------------------------------------
diff --git a/hypocurate/web/app.py b/hypocurate/web/app.py
index 1b9ee93..a3530ab 100644
--- a/hypocurate/web/app.py
+++ b/hypocurate/web/app.py
@@ -12,6 +12,9 @@ The web service never calls a model, never claims a run and never runs a pipelin
 through `pipeline.run_view` and writes only through the pipeline's own functions: `confirmation.confirm` and
 `queries.cancel` in 10a. A confirmed run is taken up by the worker; closing the browser or restarting this service
 never affects a run (criterion 14.4).
+
+Step 10b, fix round 1: every write passes the signed-in name (recorded in `action_record`), and every form that writes
+to a query sends the version it showed and its fingerprint, which the pipeline checks under the version lock.
 """
 from __future__ import annotations
 
@@ -247,7 +250,7 @@ def create_app(
             if not shown_fingerprint:
                 raise queries.QueryRefused("content_changed", "the page sent no fingerprint of what it showed; show "
                                                               "it again before confirming")
-            confirmation.confirm(engine, run_id, name, shown_fingerprint=shown_fingerprint)
+            confirmation.confirm(engine, run_id, name, shown_fingerprint=shown_fingerprint, via=queries.WEBSITE)
         except queries.QueryRefused as refused:
             shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
             if shown is None:
@@ -264,7 +267,7 @@ def create_app(
         if run_view.run_page(engine, run_id) is None:
             raise HTTPException(status_code=404, detail=f"no run {run_id}")
         try:
-            queries.cancel(engine, run_id, by=name)
+            queries.cancel(engine, run_id, by=name, via=queries.WEBSITE)
         except queries.QueryRefused as refused:
             shown = run_view.run_page(engine, run_id)
             if shown is None:
@@ -286,6 +289,12 @@ def create_app(
             return database_message(error)
         raise error
 
+    def shown_version(form) -> dict:
+        """The version a form showed: its id and fingerprint as sent (fix round 1; checked by the pipeline)."""
+        raw = (form.get("version_id") or "").strip()
+        return {"version_id": int(raw) if raw.isdigit() else None,
+                "version_fingerprint": (form.get("version_fingerprint") or "").strip() or None}
+
     def form_values(form) -> dict:
         return {"claim": form.get("claim", ""), "domain": form.get("domain", ""),
                 "sufficiency": form.get("sufficiency", "fixed_minimum"), "note": form.get("note", ""),
@@ -311,13 +320,11 @@ def create_app(
         from hypocurate.pipeline import queries, query_view
         form = await request.form()
         security.check_csrf(request, form.get(security.CSRF_FIELD))
-        security.signed_in_name(request)
+        name = security.signed_in_name(request)
         v = form_values(form)
         try:
             q = queries.create(engine, v["claim"], v["sources"], domain=v["domain"], sufficiency=v["sufficiency"],
-                               note=v["note"])
-            if v["action"] == "submit":
-                queries.submit(engine, q.version_id)
+                               note=v["note"], by=name, via=queries.WEBSITE, submit=v["action"] == "submit")
         except Exception as error:  # noqa: BLE001 (refused_words re-raises anything that is not a fixed refusal)
             return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": None,
                                                      "values": v, "error": refused_words(error), "active": "new"},
@@ -344,28 +351,32 @@ def create_app(
         values = {"claim": latest["claim"], "note": latest["note"] or "", "sufficiency": latest["sufficiency_key"],
                   "sources": [s["key"] for s in latest["sources"]], "domain": latest["domain_key"]}
         return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
-                                                 "q": shown, "values": values, "error": None, "active": "queries"})
+                                                 "q": shown, "values": values, "error": None, "active": "queries",
+                                                 "shown_version": {"version_id": latest["id"],
+                                                                   "version_fingerprint": latest["fingerprint"]}})
 
     @app.post("/queries/{number}/edit")
     async def edit_query(request: Request, number: str):
         from hypocurate.pipeline import queries, query_view
         form = await request.form()
         security.check_csrf(request, form.get(security.CSRF_FIELD))
-        security.signed_in_name(request)
-        v = form_values(form)
+        name = security.signed_in_name(request)
+        v, sent = form_values(form), shown_version(form)
         try:
             shown = query_view.query_page(engine, number)
         except query_view.NoSuchQuery as error:
             raise HTTPException(status_code=404, detail=str(error)) from None
         try:
+            # The pipeline checks, under the version lock, that the version edited is the one this form showed.
             change = queries.new_version if shown["latest"]["status"] == "returned" else queries.update_draft
-            vid = change(engine, number, v["claim"], v["sources"], v["domain"], v["sufficiency"], v["note"])
-            if v["action"] == "submit":
-                queries.submit(engine, vid)
+            change(engine, number, v["claim"], v["sources"], v["domain"], v["sufficiency"], v["note"], by=name,
+                   via=queries.WEBSITE, submit=v["action"] == "submit", expected_version=sent["version_id"],
+                   expected_fingerprint=sent["version_fingerprint"])
         except Exception as error:  # noqa: BLE001
+            # The form keeps the version it showed: after a refusal as stale, only a reload acts on the newer one.
             return page(request, "query_form.html", {"options": query_view.form_options(engine), "number": number,
                                                      "q": shown, "values": v, "error": refused_words(error),
-                                                     "active": "queries"}, status_code=409)
+                                                     "active": "queries", "shown_version": sent}, status_code=409)
         return RedirectResponse(f"/queries/{number}", status_code=303)
 
     @app.post("/queries/{number}/again")
@@ -373,9 +384,12 @@ def create_app(
         from hypocurate.pipeline import queries, query_view
         form = await request.form()
         security.check_csrf(request, form.get(security.CSRF_FIELD))
-        security.signed_in_name(request)
+        name = security.signed_in_name(request)
+        sent = shown_version(form)
         try:
-            rid = queries.dispatch_again(engine, number)
+            rid = queries.dispatch_again(engine, number, by=name, via=queries.WEBSITE,
+                                         expected_version=sent["version_id"],
+                                         expected_fingerprint=sent["version_fingerprint"])
         except Exception as error:  # noqa: BLE001
             try:
                 shown = query_view.query_page(engine, number)
@@ -401,6 +415,10 @@ def create_app(
         return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
                                              "queue": shown.get("queue"), "error": None, "active": "review"})
 
+    def queries_fingerprint(version_id: int) -> str | None:
+        from hypocurate.pipeline import queries
+        return queries.version_fingerprint(engine, version_id)
+
     async def review_action(request: Request, number: str, act):
         from hypocurate.pipeline import query_view
         form = await request.form()
@@ -410,12 +428,18 @@ def create_app(
             shown = query_view.review_page(engine, number)
         except query_view.NoSuchQuery as error:
             raise HTTPException(status_code=404, detail=str(error)) from None
+        sent = shown_version(form)
         try:
+            from hypocurate.pipeline.queries import STALE, QueryRefused
+            # Fix round 1: a form for another version, or one changed since, says so first (the pipeline checks it
+            # again under the version lock).
+            if sent["version_id"] is None or sent["version_id"] != shown["latest"]["id"] or \
+                    sent["version_fingerprint"] != queries_fingerprint(sent["version_id"]):
+                raise QueryRefused("stale", STALE)
             if not shown["reviewable"]:
-                from hypocurate.pipeline.queries import QueryRefused
                 raise QueryRefused("not_submitted", f"query {number} is {shown['latest']['status_words']}; only a "
                                                     "submitted query is reviewed")
-            return act(form, name, shown)
+            return act(form, name, sent["version_id"], sent["version_fingerprint"])
         except Exception as error:  # noqa: BLE001
             return page(request, "review.html", {"picker": query_view.review_list(engine), "q": shown,
                                                  "queue": shown.get("queue"), "active": "review",
@@ -425,7 +449,7 @@ def create_app(
     async def review_dispatch(request: Request, number: str):
         from hypocurate.pipeline import queries
 
-        def act(form, name, shown):
+        def act(form, name, version_id, fingerprint):
             ceiling = (form.get("ceiling") or "").strip()
             try:
                 ceiling = Decimal(ceiling) if ceiling else None
@@ -433,9 +457,10 @@ def create_app(
                 raise queries.QueryRefused("ceiling", "the ceiling is a number of US dollars") from None
             if ceiling is not None and not ceiling > 0:
                 raise queries.QueryRefused("ceiling", "the ceiling is a positive number of US dollars")
-            queries.confirm_domain(engine, shown["version_id"], by=name, domain=form.get("domain") or None,
-                                   where=queries.WEBSITE)
-            rid = queries.dispatch(engine, shown["version_id"], ceiling=ceiling)
+            confirmed = queries.confirm_domain(engine, version_id, by=name, domain=form.get("domain") or None,
+                                               via=queries.WEBSITE, expected_fingerprint=fingerprint)
+            rid = queries.dispatch(engine, version_id, ceiling=ceiling, by=name, via=queries.WEBSITE,
+                                   expected_fingerprint=confirmed)
             return RedirectResponse(f"/runs/{rid}", status_code=303)
 
         return await review_action(request, number, act)
@@ -444,8 +469,9 @@ def create_app(
     async def review_return(request: Request, number: str):
         from hypocurate.pipeline import queries
 
-        def act(form, name, shown):
-            queries.return_for_edits(engine, shown["version_id"], by=name, comment=form.get("comment", ""))
+        def act(form, name, version_id, fingerprint):
+            queries.return_for_edits(engine, version_id, by=name, comment=form.get("comment", ""), via=queries.WEBSITE,
+                                     expected_fingerprint=fingerprint)
             return RedirectResponse(f"/queries/{number}", status_code=303)
 
         return await review_action(request, number, act)
@@ -475,13 +501,13 @@ def create_app(
     @app.post("/sources/{key}/register")
     async def source_register(request: Request, key: str):
         """Registers a source defined in code (sources.versions.register; a safeguard write, with the CSRF token)."""
-        from hypocurate.pipeline import catalog_view
+        from hypocurate.pipeline import catalog_view, queries
         from hypocurate.sources import versions
         form = await request.form()
         security.check_csrf(request, form.get(security.CSRF_FIELD))
         name = security.signed_in_name(request)
         try:
-            done = versions.register(engine, key)
+            done = versions.register(engine, key, by=name, via=queries.WEBSITE)
         except versions.RegistrationError as error:
             return page(request, "sources.html", {"s": catalog_view.sources_page(engine), "report": None,
                                                   "message": None, "active": "sources",
diff --git a/hypocurate/web/templates/query.html b/hypocurate/web/templates/query.html
index d2830ac..6b38c4b 100644
--- a/hypocurate/web/templates/query.html
+++ b/hypocurate/web/templates/query.html
@@ -12,6 +12,8 @@
   {% if q.can_dispatch_again %}
   <form method="post" action="/queries/{{ q.number }}/again">
     <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+    <input type="hidden" name="version_id" value="{{ q.latest.id }}">
+    <input type="hidden" name="version_fingerprint" value="{{ q.latest.fingerprint }}">
     <button type="submit">Dispatch again (a new run)</button>
   </form>{% endif %}
 </div>
diff --git a/hypocurate/web/templates/query_form.html b/hypocurate/web/templates/query_form.html
index 0c2c8ae..a1098f3 100644
--- a/hypocurate/web/templates/query_form.html
+++ b/hypocurate/web/templates/query_form.html
@@ -10,6 +10,8 @@
 {% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
 <form method="post" action="{% if number %}/queries/{{ number }}/edit{% else %}/queries{% endif %}" class="query-form">
   <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+  {% if shown_version %}<input type="hidden" name="version_id" value="{{ shown_version.version_id }}">
+  <input type="hidden" name="version_fingerprint" value="{{ shown_version.version_fingerprint }}">{% endif %}
   <label for="claim">Hypothesis {{ info("hypothesis") }}</label>
   <textarea id="claim" name="claim" rows="3" required>{{ values.claim if values else "" }}</textarea>
   <fieldset><legend>Domain {{ info("domain") }}</legend>
diff --git a/hypocurate/web/templates/review.html b/hypocurate/web/templates/review.html
index d0145d6..5d32971 100644
--- a/hypocurate/web/templates/review.html
+++ b/hypocurate/web/templates/review.html
@@ -27,6 +27,8 @@
     </dl>
     <form method="post" action="/review/{{ q.number }}/dispatch" class="query-form">
       <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+      <input type="hidden" name="version_id" value="{{ q.latest.id }}">
+      <input type="hidden" name="version_fingerprint" value="{{ q.latest.fingerprint }}">
       <fieldset><legend>Domain: confirm or change {{ info("domain") }}</legend>
         {% for d in q.options.domains %}
         <label class="choice"><input type="radio" name="domain" value="{{ d.key }}"{% if d.key == q.domain_key %} checked{% endif %}> {{ d.name }}{% if not d.supported %} <span class="muted">(not yet supported)</span>{% endif %}</label>
@@ -39,6 +41,8 @@
     </form>
     <form method="post" action="/review/{{ q.number }}/return" class="query-form">
       <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
+      <input type="hidden" name="version_id" value="{{ q.latest.id }}">
+      <input type="hidden" name="version_fingerprint" value="{{ q.latest.fingerprint }}">
       <label for="comment">Return for edits: what should change?</label>
       <textarea id="comment" name="comment" rows="2" required></textarea>
       <button type="submit" class="secondary">Return for edits</button>
diff --git a/tests/test_confirmation.py b/tests/test_confirmation.py
index e9319b8..99ff774 100644
--- a/tests/test_confirmation.py
+++ b/tests/test_confirmation.py
@@ -276,9 +276,10 @@ def test_a_cancelled_waiting_run_is_not_confirmed(engine, stub):
 def test_no_code_confirms_in_bulk_or_by_itself():
     """No bulk or automatic confirmation in step 9 (owner, 2026-10-08): `confirm` takes one run and one name, and
     the only callers in the package are the command line's `confirm` command and, from step 10a (owner's approved
-    plan, 2026-10-11), the web page's confirm action; step 10a adds the shown content's fingerprint (addition 2)."""
+    plan, 2026-10-11), the web page's confirm action; step 10a adds the shown content's fingerprint (addition 2); step
+    10b's fix round 1 adds `via`, where it was done, for its action_record row (owner, 2026-10-11)."""
     params = list(inspect.signature(confirmation.confirm).parameters)
-    assert params == ["engine", "run_id", "by", "shown", "shown_fingerprint"]
+    assert params == ["engine", "run_id", "by", "shown", "shown_fingerprint", "via"]
     package = pathlib.Path(confirmation.__file__).parents[1]
     callers = []
     for path in package.rglob("*.py"):
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 740c08e..9088724 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -70,6 +70,9 @@ def expected_triggers() -> set[tuple[str, str]]:
     m8 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0008").module  # step 9b
     names |= {(t, f"hc_{t}_no_delete") for t in m8.NO_DELETE} | {(t, f"hc_{t}_no_truncate") for t in m8.NO_DELETE}
     names |= {(t, trigger) for t, _, trigger, _ in m8.CHECKED}
+    m9 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0009").module  # step 10b, fix round 1
+    names |= {(t, f"hc_{t}_append_only") for t in m9.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m9.APPEND_ONLY}
+    names |= {(t, trigger) for t, _, trigger, _ in m9.CHECKED}
     return names
 
 
diff --git a/tests/test_migrations_step10b.py b/tests/test_migrations_step10b.py
new file mode 100644
index 0000000..64608a3
--- /dev/null
+++ b/tests/test_migrations_step10b.py
@@ -0,0 +1,145 @@
+"""Step 10b, fix round 1: migration 0009, `action_record` (the owner's answer of 2026-10-11 after ChatGPT's review,
+finding 3: "New table action_record, migration 0009, as you recommend. Also write a row for confirm and cancel").
+
+One row per person's action: the action (a fixed list), where (website, command line, code), the name given (required
+on the website, none for code's own action), what it acted on (as the action requires), and the database's time.
+Append-only. 0001 to 0008 untouched; up, down, up gives the same schema; the downgrade refuses while a row exists; a
+failed upgrade changes nothing."""
+from __future__ import annotations
+
+import pytest
+from alembic.script import ScriptDirectory
+from sqlalchemy import text
+from sqlalchemy.exc import IntegrityError, ProgrammingError
+
+from hypocurate.db import actions, migrate, models
+from hypocurate.db.engine import make_engine
+from model_builder import World
+from test_migrations import assert_schema_is_empty, snapshot
+
+SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
+ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
+           "cancel", "confirm_rules", "register_source")
+
+
+def m0009():
+    return SCRIPTS.get_revision("0009").module
+
+
+@pytest.fixture
+def engine(empty_database):
+    e = make_engine(empty_database)
+    yield e
+    e.dispose()
+
+
+@pytest.fixture
+def w(db):
+    return World(db)
+
+
+def insert(w, action="create", channel="website", actor="Ada", v=None, r=None, s=None, at=None):
+    return w.val("INSERT INTO action_record (action, channel, actor, hypothesis_version_id, run_id, source_version_id"
+                 + (", at" if at else "") + ") VALUES (:a, :c, :n, :v, :r, :s" + (", :at" if at else "")
+                 + ") RETURNING id", a=action, c=channel, n=actor, v=v, r=r, s=s, at=at)
+
+
+# --- the migration ------------------------------------------------------------------------------------------
+
+def test_0009_is_the_head_and_follows_0008():
+    assert migrate.head_revision() == "0009" and m0009().down_revision == "0008"
+
+
+def test_0009_replaces_no_earlier_function():
+    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008")
+               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
+    assert not {f.split("(")[0] for f in m0009().FUNCTION_NAMES} & earlier
+    assert "CREATE OR REPLACE" not in " ".join(m0009().FUNCTIONS)
+
+
+def test_up_down_up_restores_0008(engine):
+    migrate.upgrade(engine, "0008")
+    at_0008 = snapshot(engine)
+    migrate.upgrade(engine)
+    first = snapshot(engine)
+    migrate.downgrade(engine, "0008")
+    assert snapshot(engine) == at_0008
+    migrate.upgrade(engine)
+    assert snapshot(engine) == first
+    migrate.downgrade(engine, "base")
+    assert_schema_is_empty(engine)
+
+
+def test_a_failed_upgrade_changes_nothing(engine):
+    migrate.upgrade(engine, "0008")
+    with engine.begin() as conn:
+        conn.execute(text("CREATE FUNCTION hc_action_record_insert() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
+    before = snapshot(engine)
+    with pytest.raises(ProgrammingError, match="already exists"):
+        migrate.upgrade(engine)
+    assert snapshot(engine) == before and migrate.current_revision(engine) == "0008"
+
+
+def test_the_downgrade_refuses_while_an_action_is_recorded(db):
+    w = World(db)
+    insert(w, v=w.draft())
+    before = snapshot(db)
+    with pytest.raises(Exception, match="0009 is in use"):
+        migrate.downgrade(db, "0008")
+    assert snapshot(db) == before and migrate.current_revision(db) == "0009"
+
+
+def test_the_lists_are_the_codes():
+    assert m0009().ACTIONS == ACTIONS == models.ACTIONS
+    assert m0009().CHANNELS == models.CHANNELS == (actions.WEBSITE, actions.COMMAND_LINE, actions.CODE)
+    assert m0009().TARGETS == models.ACTION_TARGETS and set(m0009().TARGETS) == set(ACTIONS)
+
+
+# --- a row --------------------------------------------------------------------------------------------------
+
+def test_the_time_is_the_databases(w):
+    aid = insert(w, v=w.draft(), at="2000-01-01")
+    assert w.val("SELECT at > '2001-01-01' FROM action_record WHERE id = :a", a=aid)
+
+
+def test_rows_are_never_changed_deleted_or_truncated(w):
+    aid = insert(w, v=w.draft())
+    w.rejected("UPDATE action_record SET actor = 'Someone else' WHERE id = :a", "append-only", a=aid)
+    w.rejected("DELETE FROM action_record WHERE id = :a", "append-only", a=aid)
+    w.rejected("TRUNCATE action_record", "append-only")
+    assert w.val("SELECT actor FROM action_record WHERE id = :a", a=aid) == "Ada"
+
+
+@pytest.mark.parametrize("actor", [None, "", " Ada", "x" * 201])
+def test_an_action_on_the_website_names_its_person(w, actor):
+    with pytest.raises(IntegrityError, match="ck_action_record_(website_named|actor)"):
+        insert(w, actor=actor, v=w.draft())
+
+
+def test_the_command_line_may_give_no_name_and_code_gives_none(w):
+    vid = w.draft()
+    insert(w, channel="command line", actor=None, v=vid)
+    insert(w, channel="code", actor=None, v=vid)
+    with pytest.raises(IntegrityError, match="ck_action_record_code_unnamed"):
+        insert(w, channel="code", actor="Ada", v=vid)
+
+
+@pytest.mark.parametrize("action,channel", [("approve", "website"), ("create", "email")])
+def test_only_the_fixed_actions_and_channels(w, action, channel):
+    with pytest.raises(IntegrityError, match="ck_action_record_(action|channel)"):
+        insert(w, action=action, channel=channel, v=w.draft())
+
+
+def test_each_action_names_exactly_what_it_acts_on(w):
+    vid = w.dispatched()
+    rid = w.run(vid)
+    sv = w.version["mpea"]
+    targets = {"v": vid, "r": rid, "s": sv}
+    for action, kinds in models.ACTION_TARGETS.items():
+        insert(w, action=action, **{k: targets[k] for k in kinds})  # exactly its targets: accepted
+        missing = {k: targets[k] for k in kinds[1:]}  # without its first target
+        with pytest.raises(IntegrityError, match="ck_action_record_targets"):
+            insert(w, action=action, **missing)
+        extra = next(k for k in "vrs" if k not in kinds)  # with one it does not act on
+        with pytest.raises(IntegrityError, match="ck_action_record_targets"):
+            insert(w, action=action, **{k: targets[k] for k in kinds}, **{extra: targets[extra]})
diff --git a/tests/test_migrations_step9b.py b/tests/test_migrations_step9b.py
index 826c62c..eff1942 100644
--- a/tests/test_migrations_step9b.py
+++ b/tests/test_migrations_step9b.py
@@ -46,8 +46,9 @@ def release(w, cid, reason="finished"):
 
 # --- the migration ------------------------------------------------------------------------------------------
 
-def test_0008_is_the_head_and_follows_0007():
-    assert migrate.head_revision() == "0008" and m0008().down_revision == "0007"
+def test_0008_follows_0007():
+    # Step 10b, fix round 1: 0009 is now the head (tests/test_migrations_step10b.py).
+    assert m0008().down_revision == "0007"
 
 
 def test_0008_replaces_no_earlier_function():
@@ -86,7 +87,8 @@ def test_the_downgrade_refuses_while_a_claim_exists(db):
     before = snapshot(db)
     with pytest.raises(Exception, match="0008 is in use"):
         migrate.downgrade(db, "0007")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0008"
+    # Step 10b: the database stays at the head, now 0009 (0009's own downgrade is undone with the refused transaction).
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
 
 
 def test_the_release_reasons_are_the_codes():
diff --git a/tests/test_web_fix10b.py b/tests/test_web_fix10b.py
new file mode 100644
index 0000000..6fb7f4a
--- /dev/null
+++ b/tests/test_web_fix10b.py
@@ -0,0 +1,273 @@
+"""Step 10b, fix round 1 (ChatGPT's review of 2026-10-11, three findings accepted by the owner).
+
+1. Act only on the version shown: review, return, dispatch, dispatch again and edit forms send the displayed version's
+   id and a fingerprint of its content; the pipeline checks both under the version lock and refuses a stale submission
+   ("This query has changed since you opened it; reload the page"). Two-session tests.
+2. No formulas in exports: every text cell in the workbook is a string cell; in the CSV, text starting with =, +, -, @,
+   tab or carriage return is neutralised, and numbers stay numbers.
+3. Who did it: every write stores the signed-in name in `action_record` (migration 0009), in the same transaction;
+   confirm and cancel too (owner's addition).
+"""
+from __future__ import annotations
+
+import csv
+import io
+import re
+
+import pytest
+from openpyxl import load_workbook
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import confirmation, orchestrator, queries, workbook
+from stats_world import small_rows
+from test_web_runs import plain, signed_in, token
+
+STALE = "This query has changed since you opened it; reload the page"
+ALICE, BOB = "Alice Reviewer", "Bob Editor"
+CLAIM = to.FCC_CLAIM
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
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def shown(page: str) -> dict:
+    """The version id and fingerprint a page's form carries."""
+    return {"version_id": re.search(r'name="version_id" value="(\d+)"', page).group(1),
+            "version_fingerprint": re.search(r'name="version_fingerprint" value="([0-9a-f]{64})"', page).group(1)}
+
+
+def new_query(c, action="submit", claim=CLAIM, note=""):
+    r = c.post("/queries", data={"csrf_token": token(c), "claim": claim, "sources": ["mpea", "tamu_fcc"],
+                                 "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "note": note,
+                                 "action": action})
+    assert r.status_code == 303, plain(r.text)[:300]
+    return r.headers["location"].rsplit("/", 1)[1]
+
+
+def edit_form(claim=CLAIM, action="submit"):
+    return {"claim": claim, "sources": ["mpea", "tamu_fcc"], "domain": "grain_size_strengthening",
+            "sufficiency": "fixed_minimum", "note": "", "action": action}
+
+
+# --- finding 1: act only on the version shown ------------------------------------------------------------------------
+
+def test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2(own):
+    engine, url = own
+    alice, bob = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
+    number = new_query(bob)
+    seen_by_alice = shown(alice.get(f"/review/{number}").text)  # Alice opens version 1
+    assert bob.post(f"/review/{number}/return", data={"csrf_token": token(bob), "comment": "narrow it",
+                                                      **shown(bob.get(f"/review/{number}").text)}).status_code == 303
+    assert bob.post(f"/queries/{number}/edit", data={"csrf_token": token(bob), **edit_form(CLAIM + " in tension"),
+                                                     **shown(bob.get(f"/queries/{number}/edit").text)}).status_code == 303
+    r = alice.post(f"/review/{number}/dispatch", data={"csrf_token": token(alice), "domain": "grain_size_strengthening",
+                                                       **seen_by_alice})
+    assert r.status_code == 409 and STALE in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM run") == 0  # version 2 was not dispatched
+    r = alice.post(f"/review/{number}/return", data={"csrf_token": token(alice), "comment": "x", **seen_by_alice})
+    assert r.status_code == 409 and STALE in plain(r.text)
+
+
+def test_a_changed_version_is_refused_even_with_the_same_id(own):
+    """The fingerprint covers the content: a draft edited in another tab after this one opened is refused."""
+    engine, url = own
+    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
+    number = new_query(a, action="save")
+    tab_a, tab_b = shown(a.get(f"/queries/{number}/edit").text), shown(b.get(f"/queries/{number}/edit").text)
+    assert tab_a["version_id"] == tab_b["version_id"]
+    assert a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("first edit", "save"),
+                                                   **tab_a}).status_code == 303
+    r = b.post(f"/queries/{number}/edit", data={"csrf_token": token(b), **edit_form("second edit", "save"), **tab_b})
+    assert r.status_code == 409 and STALE in plain(r.text)
+    assert one(engine, "SELECT v.text FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
+                       "h.number = :n", n=number) == "first edit"  # never overwritten by the older form
+
+
+def test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version(own):
+    engine, url = own
+    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
+    number = new_query(a)
+    a.post(f"/review/{number}/return", data={"csrf_token": token(a), "comment": "edit", **shown(a.get(f"/review/{number}").text)})
+    tab_a, tab_b = shown(a.get(f"/queries/{number}/edit").text), shown(b.get(f"/queries/{number}/edit").text)
+    assert a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("v2 by Alice", "save"),
+                                                   **tab_a}).status_code == 303
+    r = b.post(f"/queries/{number}/edit", data={"csrf_token": token(b), **edit_form("v2 by Bob", "save"), **tab_b})
+    assert r.status_code == 409 and STALE in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
+                       "h.number = :n", n=number) == 2
+
+
+def test_a_form_without_the_version_it_showed_is_refused(own):
+    engine, url = own
+    c = signed_in(engine, url, ALICE)
+    number = new_query(c)
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
+    assert r.status_code == 409 and STALE in plain(r.text) and one(engine, "SELECT count(*) FROM run") == 0
+    draft = new_query(c, action="save")
+    r = c.post(f"/queries/{draft}/edit", data={"csrf_token": token(c), **edit_form("no version sent", "save")})
+    assert r.status_code == 409 and STALE in plain(r.text)
+    assert one(engine, "SELECT v.text FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id WHERE "
+                       "h.number = :n", n=draft) == CLAIM
+    r = c.post(f"/queries/{draft}/edit", data={"csrf_token": token(c), **edit_form("a forged id", "save"),
+                                               "version_id": "1", "version_fingerprint": "0" * 64})
+    assert r.status_code == 409 and STALE in plain(r.text)
+
+
+def test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock(own):
+    engine, _ = own
+    q = queries.create(engine, CLAIM, ["mpea"], by=ALICE)
+    queries.submit(engine, q.version_id, by=ALICE)
+    fp = queries.version_fingerprint(engine, q.version_id)
+    queries.return_for_edits(engine, q.version_id, by=BOB, comment="x", expected_fingerprint=fp)
+    with pytest.raises(queries.QueryRefused) as refused:
+        queries.dispatch(engine, q.version_id, by=ALICE, expected_fingerprint=fp)
+    assert refused.value.code == "stale" and refused.value.reason == STALE
+
+
+# --- finding 2: no formulas in exports -------------------------------------------------------------------------------
+
+FORMULA = "=1+1"
+
+
+def planted_run(engine, stub):
+    """A completed run whose stored text begins with formula signs: the hypothesis, a paper reference (MPEA title),
+    the note, the names, and the Analyst's text."""
+    starts = ("=", "+", "-", "@", "=", "+")
+    rows = [{**r, "REFERENCE: title": f"{starts[i]}1+1 title {i}"} for i, r in enumerate(small_rows(3, papers=3))]
+    pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
+    stub.respond(to.responder(analyst=lambda raw: "+Plain text {outcome_wording}."))
+    q = queries.create(engine, f"{FORMULA} yield strength rises as grain size falls", ["mpea"], note="@note", by="-Mallory")
+    queries.submit(engine, q.version_id, by="-Mallory")
+    queries.confirm_domain(engine, q.version_id, by="=Eve")
+    rid = queries.dispatch(engine, q.version_id, fixed_plan=True, by="=Eve")
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "completed"
+    return rid
+
+
+def test_every_text_cell_of_the_workbook_is_a_string_cell(migrated_database, stub):
+    engine = make_engine(migrated_database)
+    try:
+        rid = planted_run(engine, stub)
+        wb = load_workbook(io.BytesIO(workbook.build(engine, rid)))
+        texts = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
+        assert texts and all(c.data_type == "s" for c in texts), [c.coordinate for c in texts if c.data_type != "s"]
+        values = {c.value for c in texts}
+        assert f"{FORMULA} yield strength rises as grain size falls" in values  # kept as written, as a string
+        assert {"=1+1 title 0", "+1+1 title 1", "-1+1 title 2", "@1+1 title 3"} <= values and "@note" in values
+        assert any(v.startswith("=Eve, ") for v in values) and any(v.startswith("-Mallory, ") for v in values)  # names
+        assert any("+Plain text" in v for v in values)  # the Analyst's text
+        numbers = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row
+                   if isinstance(c.value, (int, float)) and not isinstance(c.value, bool)]
+        assert numbers and all(c.data_type == "n" for c in numbers)  # numbers stay numbers
+    finally:
+        engine.dispose()
+
+
+def test_the_csv_neutralises_formula_text_and_keeps_numbers(migrated_database, stub):
+    engine = make_engine(migrated_database)
+    try:
+        rid = planted_run(engine, stub)
+        rows = list(csv.reader(io.StringIO(workbook.records_csv(engine, rid))))
+        cells = [c for r in rows[1:] for c in r]
+        assert not [c for c in cells if c[:1] in ("=", "+", "-", "@", "\t", "\r")]
+        for i, start in enumerate(("=", "+", "-", "@")):
+            assert f"'{start}1+1 title {i}" in cells
+        header = rows[1]
+        assert re.fullmatch(r"-?\d+(\.\d+)?", rows[2][header.index("grain_size")])  # a number, unchanged
+    finally:
+        engine.dispose()
+
+
+# --- finding 3: who did it -------------------------------------------------------------------------------------------
+
+def actions(engine):
+    with engine.connect() as conn:
+        return [tuple(r) for r in conn.execute(text(
+            "SELECT action, actor, hypothesis_version_id IS NOT NULL, run_id IS NOT NULL, source_version_id IS NOT NULL "
+            "FROM action_record ORDER BY id")).all()]
+
+
+def test_every_website_write_stores_the_signed_in_name(own, stub):
+    engine, url = own
+    a, b = signed_in(engine, url, ALICE), signed_in(engine, url, BOB)
+    number = new_query(a, action="save")                                            # create
+    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("edited", "save"),
+                                            **shown(a.get(f"/queries/{number}/edit").text)})  # edit
+    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("edited", "submit"),
+                                            **shown(a.get(f"/queries/{number}/edit").text)})  # edit, submit
+    b.post(f"/review/{number}/return", data={"csrf_token": token(b), "comment": "x",
+                                             **shown(b.get(f"/review/{number}").text)})       # return
+    a.post(f"/queries/{number}/edit", data={"csrf_token": token(a), **edit_form("v2", "submit"),
+                                            **shown(a.get(f"/queries/{number}/edit").text)})  # new version, submit
+    r = b.post(f"/review/{number}/dispatch", data={"csrf_token": token(b), "domain": "grain_size_strengthening",
+                                                   **shown(b.get(f"/review/{number}").text)})  # confirm domain, dispatch
+    rid = int(r.headers["location"].rsplit("/", 1)[1])
+    b.post(f"/runs/{rid}/cancel", data={"csrf_token": token(b)})                      # cancel
+    b.post(f"/queries/{number}/again", data={"csrf_token": token(b), **shown(b.get(f"/queries/{number}").text)})
+    rows = actions(engine)
+    assert rows[:2] == [("register_source", None, False, False, True)] * 2  # the fixture's, at the command line, unnamed
+    got = [(x[0], x[1]) for x in rows[2:]]
+    assert got == [("create", ALICE), ("edit", ALICE), ("edit", ALICE), ("submit", ALICE), ("return", BOB),
+                   ("new_version", ALICE), ("submit", ALICE), ("confirm_domain", BOB), ("dispatch", BOB),
+                   ("cancel", BOB), ("dispatch_again", BOB)], got
+
+
+def test_registering_a_source_and_confirming_a_run_store_the_name(migrated_database, stub):
+    e = make_engine(migrated_database)
+    try:
+        pw.registered(e, ("mpea",))
+        c = signed_in(e, migrated_database, ALICE)
+        assert c.post("/sources/tamu_fcc/register", data={"csrf_token": token(c)}).status_code == 200
+        assert actions(e)[-1] == ("register_source", ALICE, False, False, True)
+        stub.respond(to.responder(to.planner_body()))
+        rid = to.dispatched(e)
+        assert orchestrator.run(e, rid, client_options=sp.client_options(stub)).status == "waiting"
+        page = c.get(f"/runs/{rid}/confirm").text
+        fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
+        assert c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp}).status_code == 303
+        assert actions(e)[-1] == ("confirm_rules", ALICE, False, True, False)
+        # The confirmation's own record is unchanged (owner): the name is in rules_confirmation as before.
+        assert one(e, "SELECT confirmed_by FROM rules_confirmation WHERE run_id = :r", r=rid) == ALICE
+    finally:
+        e.dispose()
+
+
+def test_action_records_are_append_only(own):
+    from sqlalchemy.exc import IntegrityError, InternalError
+    engine, _ = own
+    queries.create(engine, CLAIM, ["mpea"], by=ALICE)
+    for sql in ("UPDATE action_record SET actor = 'someone else'", "DELETE FROM action_record"):
+        with pytest.raises((IntegrityError, InternalError)):
+            with engine.begin() as conn:
+                conn.execute(text(sql))
+    assert actions(engine)[-1][:2] == ("create", ALICE)  # unchanged
+
+
+def test_every_formula_sign_is_neutralised_in_a_csv_cell_and_numbers_are_kept():
+    assert workbook.FORMULA_STARTS == ("=", "+", "-", "@", "\t", "\r")
+    for start in workbook.FORMULA_STARTS:
+        assert workbook.csv_cell(f"{start}1+1") == f"'{start}1+1"
+    for number in (-5.0, 12, 0.5, "-5", "+1e3", "-0.25"):
+        assert workbook.csv_cell(number) == number
+    assert workbook.csv_cell("plain text") == "plain text" and workbook.csv_cell(None) is None
diff --git a/tests/test_web_isolation.py b/tests/test_web_isolation.py
index 223aa76..4caa6f8 100644
--- a/tests/test_web_isolation.py
+++ b/tests/test_web_isolation.py
@@ -4,6 +4,10 @@ criterion 14.4: closing the browser or restarting the web service never affects
 A fresh process builds the app, signs in and opens every run page; afterwards no model library (dspy, litellm), and
 none of the queue, the worker, the orchestrator, recovery or the guarded runner is loaded in it. The source scan of
 tests/test_worker.py (direct imports in web/) still holds; this checks what a page actually loads.
+
+Step 10b, fix round 1 (ChatGPT's review; the owner): the same check for every page 10b added (queries, new query,
+query, edit, review, sources and the connection test, each agent page, help, the plot on the run page, the workbook
+and the CSV) and for every write the website makes (create, edit, return, dispatch, dispatch again, register).
 """
 from __future__ import annotations
 
@@ -73,3 +77,79 @@ def test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner(en
     loaded = set(result["loaded"])
     assert "hypocurate.web.app" in loaded and "hypocurate.pipeline.run_view" in loaded  # the probe did load the pages
     assert not [m for m in loaded if m in FORBIDDEN or m.split(".")[0] in ("dspy", "litellm")], loaded
+
+
+PROBE_10B = textwrap.dedent("""
+    import json, re, sys
+    from fastapi.testclient import TestClient
+    from hypocurate.config import Settings
+    from hypocurate.web.app import create_app
+    url, completed, draft, submitted, again = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
+    s = Settings(env="development", database_url=url, password="test-password-not-a-secret", session_secret="s" * 40,
+                 version="test")
+    c = TestClient(create_app(s), base_url="http://testserver", follow_redirects=False)
+    assert c.post("/login", data={"password": "test-password-not-a-secret", "name": "Probe"}).status_code == 303
+    import base64
+    payload = c.cookies["hypocurate_session"].split(".")[0]
+    token = json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4)))["csrf"]
+    def shown(page):
+        return {"version_id": re.search(r'name="version_id" value="(\\d+)"', page).group(1),
+                "version_fingerprint": re.search(r'name="version_fingerprint" value="([0-9a-f]{64})"', page).group(1)}
+    pages = ["/queries", "/queries/new", f"/queries/{draft}", f"/queries/{draft}/edit", "/review",
+             f"/review/{submitted}", "/sources", "/sources/mpea/test", "/agents/planner", "/agents/curator",
+             "/agents/critic", "/agents/analyst", "/agents/commentator", "/help", "/help?q=grain", f"/runs/{completed}",
+             f"/runs/{completed}/workbook", f"/runs/{completed}/records.csv", f"/queries/{again}"]
+    codes = {p: c.get(p).status_code for p in pages}
+    form = {"csrf_token": token, "claim": "Yield strength rises as grain size falls", "sources": ["mpea"],
+            "domain": "grain_size_strengthening", "sufficiency": "fixed_minimum", "note": ""}
+    writes = {
+        "create": c.post("/queries", data={**form, "action": "save"}).status_code,
+        "edit": c.post(f"/queries/{draft}/edit", data={**form, "action": "submit",
+                                                       **shown(c.get(f"/queries/{draft}/edit").text)}).status_code,
+        "return": c.post(f"/review/{draft}/return", data={"csrf_token": token, "comment": "narrow it",
+                                                          **shown(c.get(f"/review/{draft}").text)}).status_code,
+        "dispatch": c.post(f"/review/{submitted}/dispatch", data={"csrf_token": token,
+                                                                  "domain": "grain_size_strengthening",
+                                                                  **shown(c.get(f"/review/{submitted}").text)}
+                           ).status_code,
+        "again": c.post(f"/queries/{again}/again", data={"csrf_token": token,
+                                                         **shown(c.get(f"/queries/{again}").text)}).status_code,
+        "register": c.post("/sources/tamu_fcc/register", data={"csrf_token": token}).status_code,
+    }
+    print(json.dumps({"codes": codes, "writes": writes, "loaded": sorted(
+        m for m in sys.modules if m.startswith(("dspy", "litellm", "hypocurate")))}))
+""")
+
+
+def test_every_10b_page_and_write_loads_no_model_library_and_no_pipeline_runner(migrated_database, tmp_path):
+    from hypocurate.pipeline import queries
+    e = make_engine(migrated_database)
+    stub = sp.StubProvider()
+    try:
+        pw.registered(e, ("mpea",))
+        stub.respond(to.responder(to.planner_body()))
+        q = queries.create(e, to.FCC_CLAIM, ["mpea"])
+        queries.submit(e, q.version_id)
+        queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
+        done = queries.dispatch(e, q.version_id, fixed_plan=True)
+        assert to.run(e, done, stub).status == "completed"
+        draft = queries.create(e, to.FCC_CLAIM, ["mpea"]).number
+        submitted = queries.create(e, to.FCC_CLAIM, ["mpea"], submit=True).number
+    finally:
+        stub.close()
+        e.dispose()
+    probe = tmp_path / "probe.py"
+    probe.write_text(PROBE_10B, encoding="utf-8")
+    root = pathlib.Path(__file__).resolve().parents[1]
+    env = {**os.environ, "PYTHONPATH": str(root)}
+    out = subprocess.run([sys.executable, str(probe), migrated_database, str(done), draft, submitted, q.number],
+                         cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)
+    assert out.returncode == 0, out.stderr[-2000:]
+    result = json.loads(out.stdout.strip().splitlines()[-1])
+    assert set(result["codes"].values()) == {200}, result["codes"]
+    assert result["writes"] == {"create": 303, "edit": 303, "return": 303, "dispatch": 303, "again": 303,
+                                "register": 200}, result["writes"]
+    loaded = set(result["loaded"])
+    assert {"hypocurate.pipeline.plot", "hypocurate.pipeline.workbook", "hypocurate.pipeline.queries",
+            "hypocurate.sources.versions"} <= loaded  # the probe did load the 10b pages and writes
+    assert not [m for m in loaded if m in FORBIDDEN or m.split(".")[0] in ("dspy", "litellm")], loaded
diff --git a/tests/test_web_queries.py b/tests/test_web_queries.py
index 464439f..08a8cf0 100644
--- a/tests/test_web_queries.py
+++ b/tests/test_web_queries.py
@@ -26,6 +26,13 @@ CLAIM = to.FCC_CLAIM
 NAME = "Grace Reviewer"
 
 
+def shown(c, path: str) -> dict:
+    """The version a page's form shows (step 10b, fix round 1): its id and fingerprint, sent back with every write."""
+    page = c.get(path).text
+    return {"version_id": re.search(r'name="version_id" value="(\d+)"', page).group(1),
+            "version_fingerprint": re.search(r'name="version_fingerprint" value="([0-9a-f]{64})"', page).group(1)}
+
+
 @pytest.fixture
 def own(migrated_database):
     e = make_engine(migrated_database)
@@ -65,7 +72,8 @@ def test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_si
     v = latest(engine, number)
     assert (v.version_number, v.status, v.text, v.note) == (1, "draft", CLAIM, "please check the band")
     assert "Edit the draft" in plain(c.get(f"/queries/{number}").text)
-    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " (edited)",
+    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), **shown(c, f"/queries/{number}/edit"),
+                                                "claim": CLAIM + " (edited)",
                                                 "sources": ["mpea"], "domain": "grain_size_strengthening",
                                                 "sufficiency": "use_available", "note": "", "action": "submit"})
     assert r.status_code == 303
@@ -74,7 +82,7 @@ def test_a_query_goes_from_draft_through_review_to_a_dispatched_run_under_the_si
     page = plain(c.get(f"/review/{number}").text)
     assert f"{number} · version 1" in page and "Dispatching as Grace Reviewer" in page
     r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening",
-                                                  "ceiling": "0.40"})
+                                                  "ceiling": "0.40", **shown(c, f"/review/{number}")})
     assert r.status_code == 303 and r.headers["location"].startswith("/runs/")
     rid = int(r.headers["location"].rsplit("/", 1)[1])
     v = latest(engine, number)
@@ -90,13 +98,15 @@ def test_a_returned_query_is_edited_as_its_next_version_and_the_returned_one_is_
     engine, url = own
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit")
-    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "name the test type"})
+    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "name the test type",
+                                                  **shown(c, f"/review/{number}")})
     assert r.status_code == 303
     v = latest(engine, number)
     assert v.status == "returned" and v.review_comment == f"returned by {NAME}: name the test type"
     form = plain(c.get(f"/queries/{number}/edit").text)
     assert "Saving creates version 2; version 1 is kept unchanged" in form
-    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), "claim": CLAIM + " in tension",
+    r = c.post(f"/queries/{number}/edit", data={"csrf_token": token(c), **shown(c, f"/queries/{number}/edit"),
+                                                "claim": CLAIM + " in tension",
                                                 "sources": ["mpea", "tamu_fcc"], "domain": "grain_size_strengthening",
                                                 "sufficiency": "fixed_minimum", "note": "", "action": "save"})
     assert r.status_code == 303
@@ -113,7 +123,7 @@ def test_return_needs_a_comment(own):
     engine, url = own
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit")
-    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "  "})
+    r = c.post(f"/review/{number}/return", data={"csrf_token": token(c), "comment": "  ", **shown(c, f"/review/{number}")})
     assert r.status_code == 409 and "say what to change" in plain(r.text)
     assert latest(engine, number).status == "submitted"
 
@@ -122,14 +132,16 @@ def test_dispatch_again_makes_a_new_run_once_the_last_one_ended(own):
     engine, url = own
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit")
-    first = int(c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c),
+    first = int(c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), **shown(c, f"/review/{number}"),
                                                           "domain": "grain_size_strengthening"}).headers["location"]
                 .rsplit("/", 1)[1])
-    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
+    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=first)  # (no form while it is open)
+    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c), "version_id": str(vid),
+                                                 "version_fingerprint": queries.version_fingerprint(engine, vid)})
     assert r.status_code == 409 and queries.REASONS["already_open"] in plain(r.text)  # the first run is still open
     queries.cancel(engine, first, by=NAME)
     assert "Dispatch again" in plain(c.get(f"/queries/{number}").text)
-    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c)})
+    r = c.post(f"/queries/{number}/again", data={"csrf_token": token(c), **shown(c, f"/queries/{number}")})
     assert r.status_code == 303 and int(r.headers["location"].rsplit("/", 1)[1]) > first
 
 
@@ -140,7 +152,8 @@ def test_dispatch_at_the_monthly_cap_is_refused_with_the_owners_words(own):
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit")
     _spend_this_month(engine, spend.MONTH_CAP_USD)
-    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening",
+                                                  **shown(c, f"/review/{number}")})
     assert r.status_code == 409 and queries.REASONS["month_cap_reached"] in plain(r.text)
     assert latest(engine, number).status == "submitted"
 
@@ -150,7 +163,8 @@ def test_dispatch_of_constructed_test_data_is_refused_with_its_reason(own):
     pw.registered(engine, ("controlled_duplicates",))
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit", sources=("mpea", "controlled_duplicates"))
-    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening"})
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "grain_size_strengthening",
+                                                  **shown(c, f"/review/{number}")})
     assert r.status_code == 409
     assert queries.REASONS["constructed_source_unmarked"].format(source="controlled_duplicates") in plain(r.text)
 
@@ -159,7 +173,8 @@ def test_a_domain_not_yet_supported_cannot_be_dispatched_and_the_message_says_wh
     engine, url = own
     c = signed_in(engine, url, NAME)
     number = new_query(c, action="submit", domain="fatigue")
-    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "fatigue"})
+    r = c.post(f"/review/{number}/dispatch", data={"csrf_token": token(c), "domain": "fatigue",
+                                                  **shown(c, f"/review/{number}")})
     assert r.status_code == 409 and "the confirmed domain is not supported yet" in plain(r.text)
     assert one(engine, "SELECT count(*) FROM run") == 0
 
diff --git a/tests/test_worker_fix1.py b/tests/test_worker_fix1.py
index 0121db8..059b440 100644
--- a/tests/test_worker_fix1.py
+++ b/tests/test_worker_fix1.py
@@ -329,6 +329,11 @@ def test_the_monitoring_query_is_time_limited(engine, stub):
         assert time.monotonic() - started < queue.MONITOR_TIMEOUT_MS / 1000 + 13
 
 
+TEST_STALL_SECONDS = 20     # the test's stall allowance (production: queue.STALL_SECONDS, 900)
+TEST_DOWNTIME_SECONDS = 22  # longer than TEST_STALL_SECONDS
+FIRST_WRITE_HOLD_SECONDS = 6  # longer than the stall watch's first sample (min(5, TEST_STALL_SECONDS / 4) s)
+
+
 def test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance(engine, stub):
     """A run stopped after its lock, idle for longer than the allowance, then taken up: the new child gets the full
     allowance from its launch and completes."""
@@ -337,9 +342,26 @@ def test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance(e
     queries.start(engine, rid)
     with engine.connect() as conn:
         checkpoints.lock_rules(engine, rid, confirmation.plan_to_lock(conn, rid))
-    time.sleep(7)  # idle: longer than the allowance below
+    # Step 10b (owner's decision, 2026-10-11): the test's allowance is 20 s, not 6 s, so a slow machine's child start
+    # fits in it (the image's run once judged the child stalled at 6 s); the downtime stays longer than the allowance,
+    # so the test still checks that downtime before the attempt does not count. Production keeps STALL_SECONDS (900).
+    # The child's first write waits FIRST_WRITE_HOLD_SECONDS (a one-shot test trigger), so the stall watch samples
+    # (every min(5, allowance / 4) s) before any new write: if downtime counted, that sample would see a last write
+    # older than the allowance and stop the child (9b fix round 1, mutation f16). The hold plus the child's start still
+    # fits in the allowance.
+    with engine.begin() as conn:
+        conn.execute(text("CREATE TABLE hc_test_hold_once (x int)"))
+        conn.execute(text("INSERT INTO hc_test_hold_once VALUES (1)"))
+        conn.execute(text(f"CREATE FUNCTION hc_test_hold_once() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
+                          f"IF EXISTS (SELECT 1 FROM hc_test_hold_once) THEN DELETE FROM hc_test_hold_once; "
+                          f"PERFORM pg_sleep({FIRST_WRITE_HOLD_SECONDS}); END IF; RETURN NULL; END $$"))
+        # On the child's first write only (its records); the parent's recovery bookkeeping, before the launch, writes
+        # stage rows and must not use up the hold.
+        conn.execute(text("CREATE TRIGGER zz_hc_test_hold_once BEFORE INSERT ON record "
+                          "FOR EACH STATEMENT EXECUTE FUNCTION hc_test_hold_once()"))
+    time.sleep(TEST_DOWNTIME_SECONDS)  # idle: longer than the allowance below
     c = queue.claim(engine, rid, "test:f6")
-    out = worker.work(engine, c, stall_seconds=6, heartbeat_interval=0.5)
+    out = worker.work(engine, c, stall_seconds=TEST_STALL_SECONDS, heartbeat_interval=0.5)
     assert out["release"] == "finished" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
 
 

```

## 6. Test output

### The new tests against the reviewed package (`a4b29d9`, which has the reviewed code): failed before
```
=========================== short test summary info ============================
ERROR tests/test_migrations_step10b.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.35s

=========================== short test summary info ============================
FAILED tests/test_web_fix10b.py::test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2
FAILED tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id
FAILED tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version
FAILED tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
FAILED tests/test_web_fix10b.py::test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock
FAILED tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell
FAILED tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers
FAILED tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
FAILED tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name
FAILED tests/test_web_fix10b.py::test_action_records_are_append_only - TypeEr...
FAILED tests/test_web_fix10b.py::test_every_formula_sign_is_neutralised_in_a_csv_cell_and_numbers_are_kept
FAILED tests/test_web_isolation.py::test_every_10b_page_and_write_loads_no_model_library_and_no_pipeline_runner
12 failed in 40.01s
```
### Mutation checks
```
control: clean: 27 passed in 19.57s
f1_no_stale_check: caught: 4 failed, 7 passed in 14.31s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock
f2_website_may_send_no_version: caught: 1 failed, 10 passed in 14.76s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
f3_review_acts_on_latest: caught: 2 failed, 9 passed in 13.97s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
f4_edit_uses_latest: caught: 3 failed, 8 passed in 14.00s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
f5_fingerprint_without_content: caught: 9 failed, 2 passed in 10.50s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name
f6_workbook_formula_cells: caught: 1 failed, 10 passed in 14.49s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell
f7_csv_not_neutralised: caught: 2 failed, 9 passed in 14.25s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_formula_sign_is_neutralised_in_a_csv_cell_and_numbers_are_kept
f8_csv_only_equals: caught: 2 failed, 9 passed in 14.56s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_formula_sign_is_neutralised_in_a_csv_cell_and_numbers_are_kept
f9_no_action_rows: caught: 4 failed, 7 passed in 13.44s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_action_records_are_append_only
f10_web_create_unnamed: caught: 1 failed, 10 passed in 14.63s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
f11_confirm_no_row: caught: 1 failed, 10 passed in 14.86s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name
f12_register_no_row: caught: 2 failed, 9 passed in 13.60s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name
f13_dispatch_again_unnamed: caught: 1 failed, 10 passed in 14.57s
    ../../../../../../../workspaces/hypocurate/tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name
f14_db_time_not_forced: caught: 1 failed, 15 passed in 5.53s
    ../../../../../../../workspaces/hypocurate/tests/test_migrations_step10b.py::test_the_time_is_the_databases
f15_rows_mutable: caught: 1 failed, 15 passed in 5.52s
    ../../../../../../../workspaces/hypocurate/tests/test_migrations_step10b.py::test_rows_are_never_changed_deleted_or_truncated
f16_website_row_unnamed_allowed: caught: 1 failed, 15 passed in 5.62s
    ../../../../../../../workspaces/hypocurate/tests/test_migrations_step10b.py::test_an_action_on_the_website_names_its_person[None]

```
### The whole suite, locally
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2419 passed, 1 warning in 2426.18s (0:40:26)
elapsed 2432s
```
### The images
```
head:    410eaa7
repo:    dd482c0258a55efaa4309c87eb7997f43ff2a81b6c0f92c935a3c05c77e0370f  -
runtime: dd482c0258a55efaa4309c87eb7997f43ff2a81b6c0f92c935a3c05c77e0370f  -
test:    dd482c0258a55efaa4309c87eb7997f43ff2a81b6c0f92c935a3c05c77e0370f  -
tests/ in the test image vs the repository: identical
no tests/ or docs/ in the runtime image
guard checks in the runtime image: 1

suite in the test image:
2419 passed, 1 warning in 2663.35s (0:44:23)

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

## 7. Scratch scripts

### packet/packet.py
```python
"""Scratch: builds docs/reviews/step10b_fix_packet.md (fix round 1) from the files on disk."""
import pathlib
import subprocess

R = pathlib.Path("/workspaces/hypocurate")
W = pathlib.Path.home() / "hc-work/step10b/fix1"
REVIEWED = "a25caf0"


def sh(*a):
    return subprocess.run(a, cwd=R, capture_output=True, text=True, check=True).stdout


def tail(p, n=6):
    return "\n".join(pathlib.Path(p).read_text(encoding="utf-8").splitlines()[-n:])


summary = (R / "docs/reviews/step10b_summary.md").read_text(encoding="utf-8")
fix_section = summary[summary.index("## Fix round 1"):]
out = ["# Build step 10b — fix packet, round 1 (for a short re-check)", "",
       f"Branch `step-10b-screens`, head `{sh('git', 'rev-parse', '--short', 'HEAD').strip()}`. The reviewed head was "
       f"`{REVIEWED}`; this packet holds only what changed since. Generated from the files on disk by a script "
       "(quoted at the end).", "",
       "## 1. The review being answered (verbatim)", "",
       (R / "docs/reviews/step10b_review_chatgpt.md").read_text(encoding="utf-8"), "",
       "## 2. What was done (from the summary)", "", fix_section, "",
       "## 3. Commits since the reviewed head", "", "```", sh("git", "log", "--oneline", f"{REVIEWED}..HEAD"), "```", "",
       "## 4. Files changed", "", "```", sh("git", "diff", "--stat", f"{REVIEWED}..HEAD"), "```", "",
       "## 5. The diff (the summary and this packet left out)", "",
       "```diff", sh("git", "diff", f"{REVIEWED}..HEAD", "--", ".", ":(exclude)docs/reviews/step10b_summary.md",
                     ":(exclude)docs/reviews/step10b_fix_packet.md",
                     ":(exclude)docs/reviews/step10b_review_chatgpt.md"), "```", "",
       "## 6. Test output", "",
       "### The new tests against the reviewed package (`a4b29d9`, which has the reviewed code): failed before", "```",
       tail(W / "before/before.log", 4), "", tail(W / "before/before2.log", 14), "```",
       "### Mutation checks", "```", (W / "mut/mutations.log").read_text(encoding="utf-8"), "```",
       "### The whole suite, locally", "```", tail(W / "full.log", 3), "```",
       "### The images", "```", (W / "images.txt").read_text(encoding="utf-8"), "```",
       "### Reference dumps against main", "```", (W / "refdump_compare.txt").read_text(encoding="utf-8"), "```", "",
       "## 7. Scratch scripts", ""]
for name in ("packet/packet.py", "mut/mutate.py", "register_fix1.py"):
    out += [f"### {name}", "```python", (W / name).read_text(encoding="utf-8"), "```", ""]
(R / "docs/reviews/step10b_fix_packet.md").write_text("\n".join(out), encoding="utf-8")
print("written")

```

### mut/mutate.py
```python
"""Scratch: step 10b fix round 1 mutation checks. Each fault is applied to a fresh copy of the package (with data/
beside it), the named tests run with PYTHONPATH on the copy from a folder without a package, and the run must fail.
ERROR (the run could not complete) and HUNG are reported apart from caught."""
import os, pathlib, shutil, subprocess, sys
R = pathlib.Path("/workspaces/hypocurate"); W = pathlib.Path.home() / "hc-work/step10b/fix1/mut"
Q, APP, WB = "hypocurate/pipeline/queries.py", "hypocurate/web/app.py", "hypocurate/pipeline/workbook.py"
M9 = "hypocurate/db/migrations/versions/0009_action_record.py"
FIX = ["tests/test_web_fix10b.py"]
MIG = ["tests/test_migrations_step10b.py"]
FAULTS = {
 # finding 1
 "f1_no_stale_check": (Q, "    if expected_version is None and expected_fingerprint is None and via != VIA_WEBSITE:\n        return\n",
                       "    return\n", FIX),
 "f2_website_may_send_no_version": (Q, "    if expected_version is None and expected_fingerprint is None and via != VIA_WEBSITE:\n",
                                    "    if expected_version is None and expected_fingerprint is None:\n", FIX),
 "f3_review_acts_on_latest": (APP, '            if sent["version_id"] is None or sent["version_id"] != shown["latest"]["id"] or \\\n'
                                   '                    sent["version_fingerprint"] != queries_fingerprint(sent["version_id"]):\n'
                                   '                raise QueryRefused("stale", STALE)\n',
                              "", FIX, (APP, 'return act(form, name, sent["version_id"], sent["version_fingerprint"])',
                                        'return act(form, name, shown["latest"]["id"], shown["latest"]["fingerprint"])')),
 "f4_edit_uses_latest": (APP, 'expected_version=sent["version_id"],\n                   expected_fingerprint=sent["version_fingerprint"])',
                         'expected_version=shown["latest"]["id"],\n                   expected_fingerprint=shown["latest"]["fingerprint"])', FIX),
 "f5_fingerprint_without_content": (Q, '    content = dict(row._mapping)\n', '    content = {"id": row.id, "status": row.status}\n', FIX),
 # finding 2
 "f6_workbook_formula_cells": (WB, '            cell.data_type = "s"\n', '            pass\n', FIX),
 "f7_csv_not_neutralised": (WB, "        return CSV_TEXT_MARK + value\n", "        return value\n", FIX),
 "f8_csv_only_equals": (WB, 'FORMULA_STARTS = ("=", "+", "-", "@", "\\t", "\\r")', 'FORMULA_STARTS = ("=",)', FIX),
 # finding 3
 "f9_no_action_rows": ("hypocurate/db/actions.py", '    if action not in ACTIONS:\n        raise ValueError(f"unknown action {action!r}")\n',
                       "    return\n", FIX),
 "f10_web_create_unnamed": (APP, 'note=v["note"], by=name, via=queries.WEBSITE,', 'note=v["note"], by=None, via="command line",', FIX),
 "f11_confirm_no_row": ("hypocurate/pipeline/confirmation.py", '        actions.record(conn, "confirm_rules", name, via, run=run_id)\n',
                        "", FIX),
 "f12_register_no_row": ("hypocurate/sources/versions.py",
                         '            actions.record(conn, "register_source", by, via, source_version=done.version_id)\n',
                         "            pass\n", FIX),
 "f13_dispatch_again_unnamed": (Q, '        actions.record(conn, "dispatch_again", by, via, version=vid, run=rid)\n',
                                '        actions.record(conn, "dispatch_again", None, COMMAND_LINE, version=vid, run=rid)\n', FIX),
 "f14_db_time_not_forced": (M9, "        NEW.at := now();\n", "", MIG),
 "f15_rows_mutable": (M9, 'APPEND_ONLY = ["action_record"]', 'APPEND_ONLY = []', MIG),
 "f16_website_row_unnamed_allowed": (M9, "        sa.CheckConstraint(\"channel <> 'website' OR actor IS NOT NULL\", name=op.f('ck_action_record_website_named')),\n",
                                     "", MIG),
}
env = {**os.environ, "DATABASE_URL": [l.split("=", 1)[1].strip() for l in (R / ".env").read_text().splitlines() if l.startswith("DATABASE_URL=")][0]}
names = sys.argv[1:] or ["control", *FAULTS]
for name in names:
    copy = W / "copy"
    shutil.rmtree(copy, ignore_errors=True); copy.mkdir()
    shutil.copytree(R / "hypocurate", copy / "hypocurate", ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "data").symlink_to(R / "data")
    files = FIX + MIG
    if name != "control":
        path, old, new, files, *more = FAULTS[name]
        for p, o, n in [(path, old, new), *more]:
            f = copy / p; s = f.read_text(encoding="utf-8")
            assert s.count(o) == 1, (name, p, s.count(o)); f.write_text(s.replace(o, n), encoding="utf-8")
    run_dir = W / "run"; run_dir.mkdir(exist_ok=True)
    try:
        out = subprocess.run([str(R / ".venv/bin/pytest"), "-q", "-p", "no:cacheprovider", "--rootdir", str(R),
                              *[str(R / f) for f in files]], cwd=run_dir, capture_output=True, text=True,
                             env={**env, "PYTHONPATH": str(copy)}, timeout=1800)
        tail = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "NO OUTPUT"
        verdict = ("clean" if out.returncode == 0 else "ERROR") if name == "control" else (
            "caught" if out.returncode == 1 and "failed" in tail else "SURVIVED" if out.returncode == 0 else "ERROR")
        failed = [l.split(" ")[1] for l in out.stdout.splitlines() if l.startswith("FAILED ")]
    except subprocess.TimeoutExpired:
        tail, verdict, failed = "timeout", "HUNG", []
    (W / f"out_{name}.txt").write_text(out.stdout if verdict != "HUNG" else "timeout", encoding="utf-8")
    print(f"{name}: {verdict}: {tail}", flush=True)
    for f in failed:
        print(f"    {f}", flush=True)

```

### register_fix1.py
```python
"""Scratch: the register changes of step 10b, fix round 1 (drafts for the owner's review)."""
import json, pathlib
P = pathlib.Path("/workspaces/hypocurate/hypocurate/assumptions.json")
entries = json.loads(P.read_text(encoding="utf-8"))
by_key = {e["key"]: e for e in entries}
DECIDED = {"by": "owner (Khalid El-Awady)", "date": "2026-10-11"}
EVIDENCE = ["Step 10b, fix round 1: ChatGPT's review of 2026-10-11 (docs/reviews/step10b_review_chatgpt.md), its three "
            "findings accepted by the owner the same day, with the owner's answer on storage (quoted in "
            "docs/reviews/step10b_summary.md)."]
NOTE = "Wording drafted by Claude Code for the owner's review (2026-10-11, fix round 1)."


def entry(key, name, statement, value, affects, reason, settings, tests):
    return {"key": key, "name": name, "state": "in_force", "statement": statement,
            "value": {"text": value, "unit": None}, "category": "operational", "affects": affects, "reason": reason,
            "evidence": EVIDENCE, "decided": DECIDED,
            "expert_review": {"status": "not_reviewed", "name": None, "date": None}, "sensitivity": None,
            "applied": {"status": "yes", "settings": settings, "note": None}, "tests": tests, "history": [],
            "notes": [NOTE]}


new = [
    entry("action_record", "Who did what: the action record",
          "Every write a person makes records, in the same transaction, one row of action_record (migration 0009): "
          "the action (create, edit, new version, submit, return, domain confirmation, dispatch, dispatch again, "
          "cancel, confirmation of the question as tested, registering a source), where it was done (the website, the "
          "command line, or code), the name given, what it acted on, and the database's time. On the website the name "
          "is the signed-in name, and the database refuses a website row without one. At the command line it is --by "
          "where the command takes it; a command without --by is recorded with no name, as such. A narrower question "
          "code creates is recorded as code's, with no name. Rows are never changed or deleted. Confirmation and "
          "cancel keep their own records as before (rules_confirmation, the run's failure reason); their row here "
          "repeats the name so that who did what is in one place. Nothing proves who typed a name (see "
          "signed_in_name). It is a record, not a gate: no rule reads it.",
          "one row per action; append-only",
          "Every query, run and source-registration write.",
          "ChatGPT's review of 10b, finding 3 (create, submit, edit and dispatch again kept no name); the owner's "
          "answer: a new table action_record, migration 0009, with rows for confirm and cancel too.",
          [{"ref": "python:hypocurate.db.models:ACTIONS",
            "equals": ["create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch",
                       "dispatch_again", "cancel", "confirm_rules", "register_source"]},
           {"ref": "python:hypocurate.db.models:CHANNELS", "equals": ["website", "command line", "code"]},
           {"ref": "python:hypocurate.db.actions:ACTOR_MAX", "equals": 200}],
          ["tests/test_web_fix10b.py::test_every_website_write_stores_the_signed_in_name",
           "tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name",
           "tests/test_web_fix10b.py::test_action_records_are_append_only",
           "tests/test_migrations_step10b.py::test_an_action_on_the_website_names_its_person",
           "tests/test_migrations_step10b.py::test_each_action_names_exactly_what_it_acts_on",
           "tests/test_migrations_step10b.py::test_rows_are_never_changed_deleted_or_truncated"]),
    entry("act_on_version_shown", "A page acts only on the version it showed",
          "Every website form that writes to a query (edit, review's dispatch and return, dispatch again) sends the "
          "version it displayed and a fingerprint of that version's content (SHA-256 of its query, number, status, "
          "hypothesis, domains, option, note, sources and review comment). The pipeline compares both with the stored "
          "version under the version lock, in the write's own transaction, and refuses a difference with "
          "\"This query has changed since you opened it; reload the page\". A form that sends neither is refused the "
          "same way. So an old review tab never dispatches or returns a newer version, and an old edit form never "
          "overwrites a newer draft or makes a second new version. Saving and submitting from one form is one "
          "transaction. The command line names the version it acts on and is not checked this way.",
          "version id + content fingerprint, checked under the lock",
          "The query pages (PRD 9.2, 9.3).",
          "ChatGPT's review of 10b, finding 1 (a stale review page dispatched a version it never showed); the "
          "owner's fix, in the owner's words for the refusal.",
          [{"ref": "python:hypocurate.pipeline.queries:STALE",
            "equals": "This query has changed since you opened it; reload the page"}],
          ["tests/test_web_fix10b.py::test_a_review_tab_opened_on_version_1_cannot_dispatch_version_2",
           "tests/test_web_fix10b.py::test_a_changed_version_is_refused_even_with_the_same_id",
           "tests/test_web_fix10b.py::test_an_old_edit_form_of_a_returned_version_cannot_make_a_second_new_version",
           "tests/test_web_fix10b.py::test_a_form_without_the_version_it_showed_is_refused",
           "tests/test_web_fix10b.py::test_the_pipeline_refuses_a_stale_fingerprint_under_the_version_lock"]),
    entry("export_no_formulas", "No formulas in exports",
          "In the workbook every text cell is written as a string cell, whatever it begins with, so stored text (a "
          "hypothesis, a paper reference, a note, a name, the Analyst's text) is never a formula. In the records CSV a "
          "text beginning with =, +, -, @, a tab or a carriage return gets a leading apostrophe; a number, or a text "
          "that is exactly a number, is written as it is. The stored rows are unchanged.",
          "workbook: string cells; CSV: leading apostrophe",
          "The workbook and records CSV (PRD 11) and 'hypocurate export'.",
          "ChatGPT's review of 10b, finding 2 (a stored '=1+1' became a formula cell); the owner's fix.",
          [{"ref": "python:hypocurate.pipeline.workbook:FORMULA_STARTS", "equals": ["=", "+", "-", "@", "\t", "\r"]},
           {"ref": "python:hypocurate.pipeline.workbook:CSV_TEXT_MARK", "equals": "'"}],
          ["tests/test_web_fix10b.py::test_every_text_cell_of_the_workbook_is_a_string_cell",
           "tests/test_web_fix10b.py::test_the_csv_neutralises_formula_text_and_keeps_numbers"]),
]
for e in new:
    assert e["key"] not in by_key
# Revised 10b drafts (not yet approved; fix round 1).
q = by_key["query_versions_on_the_website"]
q["applied"]["settings"] = [s for s in q["applied"]["settings"] if s["ref"] != "python:hypocurate.pipeline.queries:WEBSITE"] + [
    {"ref": "python:hypocurate.pipeline.queries:WHERE_WORDS",
     "equals": {"command line": "at the command line", "website": "on the website"}}]
q["statement"] = q["statement"].replace(
    "Every write carries the session's CSRF token;",
    "Every write carries the session's CSRF token, acts only on the version the page showed (act_on_version_shown) "
    "and is recorded with the signed-in name (action_record);")
q["notes"] = [NOTE.replace("fix round 1", "revised in fix round 1")]
r = by_key["web_source_registration"]
r["statement"] = r["statement"].replace(
    "registering one calls sources.versions.register (as the command line's 'sources register'), under the signed-in "
    "name and with the session's CSRF token;",
    "registering one calls sources.versions.register (as the command line's 'sources register') with the session's "
    "CSRF token, and a version it seals is recorded with the signed-in name in action_record, in the same "
    "transaction;")
assert "action_record" in r["statement"]
r["tests"].append("tests/test_web_fix10b.py::test_registering_a_source_and_confirming_a_run_store_the_name")
r["notes"] = [NOTE.replace("fix round 1", "revised in fix round 1")]
assert "action_record" in q["statement"]
entries += new
P.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(entries))

```
