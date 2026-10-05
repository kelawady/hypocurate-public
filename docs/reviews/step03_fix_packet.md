# Build step 3 — fix packet for the second-model re-check

Date: 2026-10-05. Branch: `step-03-data-model`. The first review covered commit `4737b08` (see `docs/reviews/step03_review_packet.md`). The fixes are up to commit `e253950`. This packet is added in the next commit and changes no code. GitHub Actions on `e253950`: success, https://github.com/kelawady/hypocurate/actions/runs/37250072104.

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

The owner accepted all seven findings of your first review of step 3; your review text is filed verbatim as `docs/reviews/step03_review_chatgpt.md`. Migration 0001 has never run on the live database, so it was changed in place (owner's instruction); after the merge it is frozen.

Please check that each fix closes its finding, and look for anything the fixes broke or left untested. Use the same checklist (`docs/reviews/checklist.md`, unchanged). Return a dated findings file as before; your review is advice, and the test suite is the gate.

| # | Finding | Where the fix is |
|---|---|---|
| 1 | Concurrent transactions can defeat the freeze (and submission, dispatch) | `hc_lock_run` and `hc_lock_version`, called first by every run- and version-state trigger in `0001_data_model.py`; `tests/test_concurrency.py` |
| 2 | The primary set can omit eligible records | `hc_run_snapshot_insert`; the freeze-completeness tests in `tests/test_data_model.py` |
| 3 | Checkpoint ordering and finality incomplete | `hc_record_insert` (after the lock); the running-state checks in every curation, result and calibration trigger; `hc_run_update` (no open stage or call at the end); post-completion rules in the stage, model-call, commentary and artifact triggers; the lifecycle tests |
| 4 | A source version does not freeze its inputs | `source_version` columns and CHECKs; `hc_source_version_insert`, `hc_source_version_update`, `hc_files_fingerprint`, `hc_source_file_insert`, `hc_run_source_insert`, `hc_record_insert`; the source-version tests |
| 5 | The database overstates its validity checks | the count CHECKs in `models.py` and the migration; the distinct-alloy check in `hc_analysis_result_insert`; wording in `models.py`, the README and the summary; `test_stored_counts_must_be_consistent`; "Step 7 acceptance requirements" in the summary |
| 6 | "Reported negative" collapses mixed results; coverage reads the registry | view `run_search_coverage`; the inventory check in `hc_run_update`; `hc_source_update`; the coverage tests |
| 7 | Cost precision, bounds and times | `model_call` columns and CHECKs; `hc_model_call_insert` and `hc_model_call_update`; the cost tests; "Step 9 requirements" in the summary |

The summary (section 1) gives the locking protocol, what may be written to a run in each state (owner's addition), the details of each fix, what was shown with the locks removed, the limits of the up/down/up proof, the tests removed or replaced and why, and the open items.

## Contents

1. Step summary (updated)
2. Files changed since the first review
3. Changed files (full text)
4. Test output

## 1. Step summary (updated)

### `docs/reviews/step03_summary.md`

SHA-256 `063f339f1ab7e2ae6dc269fd3d6e86cbd440ce93bc0125846ade963e7323331d`, 34922 bytes.

````markdown
# Build step 3 — summary for review

Date: 2026-10-05. Branch: `step-03-data-model`. **Status: the seven findings of the second-model review are fixed and green on GitHub; awaiting the re-check and the owner's sign-off. Not merged, not deployed.** PRD Section 15, step 3: "Data model. Tables and migrations from Section 7."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`. It describes the state **after** the fixes for the first review. The findings and their fixes are listed below; the review text is in `docs/reviews/step03_review_chatgpt.md`. The plan was approved by the owner on 2026-10-04/05, with decisions on seven questions and four additions, and the fix plan on 2026-10-05, with two additions (the fingerprint computed at sealing; what may be written after a run ends).

Migration 0001 has never run on the live database, so it was changed in place (owner's instruction). After the merge it is frozen: any later change is a new migration.

Not built, as instructed: the access layer, any agent, any pipeline or statistics code, any screen, and loading the frozen sources into the tables.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/db/models.py` | SQLAlchemy 2 models, one class per table (list below), with every CHECK constraint. A naming convention fixes constraint names, so tests and errors can name them. |
| `hypocurate/db/migrations/versions/0001_data_model.py` | The one migration: tables, CHECKs, a sequence for query numbers, plpgsql trigger functions and triggers (40 functions), five views, and the three domain rows. The `CREATE TABLE` statements were **rendered by Alembic autogenerate from the models, then reviewed and edited by hand**. The functions, triggers, views and seed rows are hand-written. The migration does not import the models. |
| `hypocurate/db/migrations/env.py`, `script.py.mako` | Online mode only. One transaction for the whole upgrade. `pg_advisory_xact_lock` is taken before Alembic reads the current revision. |
| `hypocurate/db/migrate.py` | `python -m hypocurate.db.migrate upgrade \| current \| downgrade <rev> [--confirm-data-loss]`. The configuration is built in code (no `alembic.ini`), and the engine is passed as an object, never as a URL string. In production, `downgrade` exits 2 without `--confirm-data-loss`. `schema_status()` serves `/health`. |
| `render.yaml` | `preDeployCommand: python -m hypocurate.db.migrate upgrade` on **both** `hypocurate-web` and `hypocurate-worker`. |
| `docker-compose.yml` | A one-off `migrate` service; `web` and `worker` wait for it (`service_completed_successfully`). CI's Compose step therefore migrates in the runtime image. **No change to `.github/workflows/`.** |
| `/health` | Adds `schema: {"revision", "at_head"}`, informational only: it never changes the status code. |
| `scripts/check_runtime_image.py` | `REQUIRED` also lists the migration files. |
| `pyproject.toml`, locks | `alembic>=1.16`. The locks gained exactly `alembic==1.20.0` and `mako==1.4.3`, with hashes. |
| `README.md` | A "Database migrations" section: apply, failure, rollback, locking, post-run writes and limits. |

### Tables and views
Tables: `domain`, `tag_value`, `source`, `source_version`, `source_file`, `agent_setting`, `hypothesis`, `hypothesis_version`, `hypothesis_version_source`, `run`, `plan`, `run_tag`, `run_agent_setting`, `run_source`, `run_snapshot`, `stage_result`, `model_call`, `record`, `run_record`, `analysis_set`, `analysis_set_record`, `flag`, `flag_record`, `analysis_result`, `calibration_result`, `commentary`, `artifact`, `audit_log`.

Views: `run_search_coverage` (replaces `run_nothing_found`, finding 6), and `model_call_totals_by_stage`, `_by_run`, `_by_query`, `_by_month`.

## The deploy questions (owner's request)

1. **How migrations are applied on deploy.**
   - Render runs the pre-deploy command after the build and before the new version starts, on a separate instance (render.com/docs/deploys, checked 2026-10-04).
   - Both services run it. The advisory lock makes the second wait; it then finds the schema at head and does nothing.
   - Locally and in CI, the Compose `migrate` service does the same.
2. **If a migration fails mid-deploy.**
   - The upgrade is one PostgreSQL transaction, so a failure rolls back everything.
   - The command exits non-zero, Render fails the deploy, and the previous version keeps running.
   - Proven by `test_a_failed_upgrade_changes_nothing`, which plants a conflicting table so the upgrade fails late, and checks that the whole schema snapshot is unchanged.
3. **How a migration is rolled back** (README):
   - (a) Preferred: a new migration that undoes the change.
   - (b) Revert the merge on `main`. Every migration keeps working with the previous release's code; step 2's code uses no tables.
   - (c) The owner runs `downgrade <rev> --confirm-data-loss` in the Render Shell. It drops tables and their data. Point-in-time recovery reaches 3 days back on Hobby and restores into a *new* database, which costs money, so ask first.
4. **Up, down, up from empty** (`test_up_down_up_on_an_empty_database`):
   - On an empty scratch database, upgrade, then check:
     - Alembic `compare_metadata` against the models reports no differences;
     - the set of CHECK names equals the models';
     - every expected trigger and view exists;
     - the three domains are seeded;
     - the revision is head.
   - Downgrade to base; only Alembic's own empty `alembic_version` remains.
   - Upgrade again; a catalog snapshot equals the first one.

### Limits of the up/down/up proof (second-model review)
- **It tests reproducibility, not correctness.** A schema that is wrong in the same way twice still passes.
- **The CHECK comparison checks names, not what the conditions say.** Two CHECKs with the same name and different predicates would pass.
- **The expected trigger names come from the migration itself**, not from an independent list. What a trigger *does* is tested separately, by the behavioural tests in `tests/test_data_model.py` and `tests/test_concurrency.py`.
- **It is drift coverage, not independent proof of the rules.**
- **A successful migration is not undone if the application then fails to start.** Every migration must therefore keep working with the previous release's code.
- **Editing a migration in place breaks the downgrade of databases migrated with the old text.** I saw this on the local development database in this fix round (see "Deviations"). It is why 0001 is frozen after the merge.

## The locking protocol (review finding 1)

- **Run triggers.** Every trigger that checks or changes a run's state first calls `hc_lock_run(run_id)`. That function runs `SELECT status FROM run WHERE id = … FOR NO KEY UPDATE`, which locks the row and returns its latest committed status in one statement. Updates of the run row (start, completion, failure) take the same lock themselves.
- **Version triggers.** Triggers on chosen sources and on dispatch (run insert) call `hc_lock_version` first. Submission and dispatch are updates of the version row, so they take the same lock themselves.
- **Source files.** A `source_file` insert locks its version row; sealing is an update of that row.
- **Lock order:** version, then run. No trigger locks a version after a run.
- **Consequence:** a transaction that writes to a run makes every other writer to that run, including a worker's heartbeat update, wait until it commits. Step 9 should keep transactions on a run short (open item 2).

## What may be written to a run in each state (review finding 3; owner, 2026-10-05)

| Run state | What may be written |
|---|---|
| queued | `run_source` and `run_agent_setting` (dispatch). The run becomes running only when every source registered at dispatch has a `run_source` row. |
| running | The pipeline, in checkpoint order: plan and tags (rules lock) → records → eligibility → sets → freeze → results and calibration; search results, flags, stages, model calls and artifacts throughout. Records only after the rules lock. |
| completed | Only the commentary, the Commentator's stage and model calls, and artifacts (plot, workbook). They cannot change the outcome, verdict, analysis results or record sets: the run row is final, and results and sets are append-only and written only while running. **The Commentator's model calls count in the run's totals and toward its cap** (`model_call_totals_by_run`), like any other. |
| failed | Nothing, except `audit_log` rows (written in every state). |

A run can complete or fail only when none of its stages is `running` and none of its model calls is `started`. Step 9's recovery must therefore finish the open stage (`failed`) and calls (`interrupted`) before it marks the run failed.

## The owner's decisions, and the rules the database enforces

Every rejection by a trigger raises SQLSTATE 23514 with a message starting `hypocurate:`. "Append-only" means a trigger rejects UPDATE, DELETE and TRUNCATE.

1. **A narrower question is a separate query** (question 1).
   - It is a new `hypothesis` row with its own Q number and `narrower_of_run_id`, which may point only to a run that **completed with outcome `partly_sufficient`**. The link is fixed.
   - Its versions carry the original run's confirmed domain. It starts as a draft and goes through review and dispatch; nothing creates or runs it automatically.
   - **A run whose outcome is `partly_sufficient` has no verdict** (CHECK).
2. **Named analysis sets, limited to the locked plan** (question 2).
   - A set exists only for `primary` or a key of the run's locked plan.
   - `primary` holds only eligible records; model-recalled records are never in any set.
   - **At the freeze** (finding 2):
     - every record extracted in the run has a decision;
     - the `primary` set is **exactly** the records decided eligible;
     - `n_records` equals its size;
     - every named sensitivity set exists.
   - A duplicate's non-surviving copy carries its own decision (not eligible, "counted once"), which keeps it out of `primary`.
3. **Search coverage per source** (question 3; finding 6).
   - `run_source` has one row per run and source, written at dispatch, and decided once (`searched` or `failed`) while the run is running. `failed` ⇔ `failed_search`.
   - **No single run-level label exists.** `run_search_coverage` lists, per run:
     - `searched_sources` and `not_searched_sources`;
     - `not_selected_sources`;
     - `failed_search_sources`;
     - `records_found_sources`;
     - `missing_evidence_sources`;
     - `reported_negative_sources`.
     
     So a mixed result reads "missing evidence in source A; negative result reported in source B".
   - A failed source is listed as failed and not searched, never as missing evidence.
   - **Coverage comes only from the run's own dispatch-time rows**, never from the current source registry. A source's key never changes.
4. **Verdict and exploratory** (question 4; additions 2 and 3).
   - CHECK: `verdict IS NOT NULL` ⇔ (`completed` AND `sufficient`).
   - **Only when the outcome is `sufficient`**, a trigger requires:
     - exactly one pooled result that passed both validity checks;
     - under `fixed_minimum`, `minimums_met`;
     - `exploratory = (use_available AND NOT minimums_met)`.
   - Other endings need no pooled result.
5. **Model calls and totals** (question 5; finding 7).
   - The row is inserted **before** the request (`started`), with `max_cost` > 0 as the upper bound. It is finished exactly once: `succeeded` (all four usage values), `failed` (all four or none), or `interrupted` (none).
   - `cost` and `max_cost` are `numeric` without a fixed scale, so they are stored exactly and nothing rounds.
   - `started_at` and `finished_at` must equal the database's transaction time, so they cannot be backdated. A call counts in the UTC month of its `started_at`.
   - No table stores totals. The views give `reported_cost`, the token sums, `unconfirmed_calls`, `unconfirmed_cost_bound` (the sum of `max_cost` for calls without reported cost) and `cap_cost` = reported + bound.
6. **The reviewer's domain** (question 6). `confirmed_domain_id` and `domain_confirmed_at` are set together, only while `submitted`; dispatch requires them. Tags are written only in the rules-lock transaction. A proposed tag value is approved or rejected once.
7. **Per-run records with an origin** (question 7; findings 3 and 4).
   - The origin is `extraction_run_id`, `source_version_id`, `source_item_key` (NOT NULL, not empty) and `item_index`, with UNIQUE `uq_record_origin_per_run` and an index for matching across runs.
   - Records are inserted only **after the rules lock**, while running, and before the freeze.
   - A record must come from the version its run recorded, and has that version's kind of data.
8. **Power report** (addition 1). `plan.power_assumptions`, information only; power-based sufficiency is rejected.
9. **`analysis_result`** (addition 3; finding 5).
   - `scope` ∈ {`pooled`, `per_source`, `sensitivity`}, on the matching set, one result per run and scope. `n_records` equals the set's records, restricted to the source for `per_source`.
   - Written after the freeze, while running.
   - **The database checks necessary conditions on the stored counts only:**
     - `resid_df = n_records − n_alloys − 1`;
     - `n_records ≥ 2 × n_alloys`;
     - `n_groups ≤ n_records`;
     - a non-empty set has at least one group;
     - `n_alloys` ≤ the set's distinct alloys;
     - `check1_passed = (n_alloys ≥ 1)`;
     - `check2_passed = (check1 AND resid_df ≥ 1 AND n_groups ≥ 2)`;
     - an estimate iff check 1; a standard error and a p-value iff check 2.
   - **The full validity rules of PRD 5.7 are not enforced by the database:**
     - an alloy measured at two *distinct grain sizes*;
     - the exact alloy and group counts;
     - the agreement of the verdict with the pooled result.
     
     They are computed and tested in step 7 (see "Step 7 acceptance requirements").
10. **Files and source versions** (item 12; finding 4).
    - `source_file` and `artifact`: at most 5 MiB, and `sha256` must match the bytes. Source files must be `.csv` or `.xlsx`, so the 49 MB Zenodo archive cannot be stored.
    - A `source_version` **copies `source_type`, `data_kind` and `grouping_unit`** from its source at insert; a different caller-supplied value is rejected. Changing `source` afterwards affects only later versions. Operational settings stay mutable on `source`: enabled, adapter status, address, licence, properties.
    - Files are added, then the version is **sealed once**:
      - the database sets `sealed_at`;
      - at least one file is required;
      - the database requires `fingerprint` to equal the SHA-256 of the sorted file list, one line `<sha256>  <path>\n` per file, sorted bytewise by path (owner, 2026-10-05; step 4 computes the same).
      
      After sealing nothing changes; no file can be added.
    - **Only a sealed version can be used by a run.**

Other rules:
- The plan is inserted once, while running, with `locked_at` equal to the database's time. `run_snapshot` likewise has `frozen_at` equal to the database's time.
- `run_record` is append-only and only for the run's own records; a model-recalled record is never eligible.
- Run status moves forward only, and completed and failed runs are final. What a run records at dispatch cannot change. A run can be inserted only for a dispatched version whose confirmed domain is supported.
- Hypothesis versions move forward only. Chosen sources change only in draft. Versions and runs are never deleted.
- A flag is raised and classified (once) only while the run is running and before the freeze.
- Calibration:
  - `computed` exactly when the analysis passed check 2, and an `unavailable` reason must match the checks;
  - a run-level row is allowed only with `no_dataset_frozen`;
  - **such a row and a dataset freeze exclude each other**, in either order (finding 3).
- Commentary only after completion, from the commentator stage.

**Stated limitations.**
- The triggers stop the application and ordinary edits. The database owner can still drop or disable a trigger; that is not tamper-proof, and the fingerprints are the cross-check.
- A rejected attempt is not logged by the database: a log row written inside the failing transaction would be rolled back with it. Logging rejected attempts belongs to the access layer (steps 5 and 6).
- The `plan` and `run_snapshot` fingerprints are checked for format only; code computes them in step 6. The source-version fingerprint and the file and artifact hashes are checked against the content.

## Review findings and fixes (first review, ChatGPT, 2026-10-05)

The owner accepted all seven findings and approved the fix plan.

1. **High — concurrent transactions could defeat the freeze, submission and dispatch checks.**
   - **Fix:** the locking protocol above.
   - **Tests:** `tests/test_concurrency.py`, 14 tests. Each holds transaction A open, starts B in a thread, asserts that B is **waiting on a lock** (`pg_stat_activity`), commits A, and checks B's result. The races, each in both orders:
     - primary member vs freeze;
     - sensitivity member vs freeze;
     - flag vs freeze;
     - chosen source vs submission;
     - run agent setting vs start;
     - flag vs completion;
     - search result vs completion;
     - "no dataset frozen" vs freeze;
     - source file vs sealing.
   - **Shown:**
     - With the run lock removed from `hc_lock_run` in a temporary copy, all 10 run-level tests fail.
     - With the version and file locks removed, 3 of the remaining 4 fail. The fourth (a file insert first, then sealing) is serialized by PostgreSQL's own foreign-key lock even without ours: sealing writes `fingerprint`, which is part of a unique key, so it conflicts with the insert's foreign-key lock. Its outcome is correct either way.
2. **High — the primary set could omit eligible records; records could stay undecided.**
   - **Fix:** freeze completeness, as above.
   - **Tests:**
     - `test_the_freeze_rejects_a_primary_set_that_omits_eligible_records` (10 eligible, 3 in the set: rejected; all 10: accepted);
     - `test_the_freeze_rejects_an_undecided_record`.
   - The duplicate test now states that it shows storage only; duplicate handling is step 6.
3. **High — checkpoint ordering and finality were incomplete.**
   - **Fix:** records only after the rules lock; every curation, result and calibration write requires a running run; "no dataset frozen" and a freeze exclude each other; the post-completion and post-failure rules above (owner's addition).
   - **Tests:**
     - `test_records_and_eligibility_come_after_the_rules_lock`;
     - `test_no_curation_once_the_run_has_ended[completed|failed]` (records, decisions, set members, flags, classifications, flag records, search results, freeze, calibration);
     - `test_a_record_extracted_after_the_freeze_cannot_slip_in_after_the_run_ends`;
     - `test_no_dataset_frozen_and_a_freeze_exclude_each_other`;
     - `test_what_may_be_written_after_completion` (commentary, Commentator stage and call counted in the run's totals and cap, artifact; other stages and roles, verdict, results and sets rejected);
     - `test_nothing_but_the_audit_log_after_failure`;
     - `test_a_run_ends_only_with_no_stage_running_and_no_call_open[completed|failed]`.
4. **High — a source version did not freeze its inputs.**
   - **Fix:** copied interpretation settings; sealing with the database-computed fingerprint; only sealed versions in runs; a record's kind equals its version's.
   - **Tests:**
     - `test_files_cannot_be_added_after_sealing`;
     - `test_sealing_needs_files_and_the_fingerprint_of_the_file_list` (no files, wrong fingerprint, backdated `sealed_at`, sealing twice, delete);
     - `test_a_new_version_starts_unsealed`;
     - `test_only_a_sealed_version_can_be_used_by_a_run`;
     - `test_a_version_keeps_its_own_interpretation_settings`;
     - `test_a_record_has_its_versions_kind_of_data`.
5. **Medium — the database overstated what its validity checks establish.**
   - **Fix:** the count-consistency CHECKs and the distinct-alloy trigger. The constraints are renamed `check1_consistent` and `check2_consistent`. The comments, the README and this summary say "necessary conditions"; the full rules and verdict agreement are step 7 acceptance requirements.
   - **Tests:** `test_stored_counts_must_be_consistent` (4 cases: one record claiming a fitted coefficient; more groups than records; records without a group; more alloys than distinct alloys).
6. **Medium — "reported negative" collapsed mixed results; coverage read the current registry.**
   - **Fix:** `run_search_coverage`, as above. A run starts only with its full dispatch-time inventory, and a source's key is fixed.
   - **Tests:**
     - `test_mixed_results_are_reported_per_category`;
     - `test_a_failed_source_is_never_missing_evidence`;
     - `test_every_selected_source_failing_shows_no_source_searched`;
     - `test_records_found_is_its_own_category`;
     - `test_coverage_comes_from_the_runs_own_dispatch_rows`;
     - `test_a_run_starts_only_with_its_full_source_inventory`.
7. **Medium — cost precision, bounds and times.**
   - **Fix:** `numeric` without a fixed scale, `max_cost > 0`, and call times set by the database. The remaining items are step 9 requirements (below).
   - **Tests:** `test_small_costs_are_stored_exactly` (1e-12 and 3e-13 stored and summed exactly; `max_cost = 0` rejected); `test_call_times_are_set_by_the_database`.

The review's remark on migration safety and the limits of the up/down/up proof is recorded above under "Limits of the up/down/up proof".

### Step 7 acceptance requirements (from finding 5)
1. The full validity rules of PRD 5.7 are computed by code from the frozen dataset and tested against generated data with known answers:
   - check 1: at least one alloy measured at two *distinct grain sizes*;
   - check 2: at least 1 residual degree of freedom and at least 2 independent groups;
   - the exact alloy and group counts, by each version's grouping unit.
   
   The stored counts must equal what code computes.
2. The verdict agrees with the pooled result: `supported` exactly when the one-sided test of k > 0 rejects at the plan's threshold. Whether the rule is "p < threshold" or "p ≤ threshold" is decided then.

### Step 9 requirements (from finding 7)
1. The `model_call` reservation row commits **before** the external request, so a rollback cannot erase a charged call.
2. The caller supplies a genuine upper bound for `max_cost` (counted input tokens plus the output-token limit, priced from the price table). The database only requires it to be positive.
3. A call counts in the UTC month of its database-set `started_at`.
4. Reservation against the caps is atomic: lock, check that `cap_cost + max_cost` stays within the per-run and per-month caps, insert, commit. Then two callers cannot spend the same remaining budget. The views alone do not prevent that.
5. Recovery finishes open stages (`failed`) and calls (`interrupted`) before it marks a run failed (the rule above).

## PRD corrections and clarifications for the next PRD update
1. **PRD 7 vs 5.4:** the narrower-question link belongs on a new query (`hypothesis.narrower_of_run_id`), not on `hypothesis_version`.
2. **PRD 7:** `run_record`'s single "used only in a sensitivity analysis" flag is replaced by named sets (`analysis_set`, `analysis_set_record`). `run_record.eligible` means eligible for the primary analysis, and at the freeze the primary set equals the records decided eligible.
3. **PRD 7 and 3.1:** "kind of nothing found" per run is replaced by per-source search results in `run_source`, reported per category with their sources (`run_search_coverage`). Mixed results are never collapsed into one label, and coverage comes from the run's dispatch-time rows.
4. **PRD 7:** `run` needs `verdict` and `exploratory`.
5. **PRD 5.8 clarification:** "exploratory" means the "use what is available" option **and** data below the fixed minimums.
6. **PRD 7 and 8:** stored token and cost totals are replaced by views over `model_call`. A call is recorded before the request, and a call without reported cost counts at its `max_cost` bound. Call times are the database's. The Commentator's calls count in the run's totals and cap.
7. **PRD 7 and 8:** `run_snapshot` holds the dataset freeze only; dispatch-time agent settings and source versions are in `run_agent_setting` and `run_source`.
8. **PRD 9.3:** the reviewer's domain change is a review decision on the version, not a new version.
9. **PRD 5.5:** `tag_value` needs a status (proposed, approved, rejected) and a decision time.
10. **PRD 7:** a flag's records are a join table (`flag_record`).
11. **PRD 7:** records are extracted per run, after the rules lock, and carry an origin identifier.
12. **PRD 6, 7 and 10:**
    - files are `bytea`, at most 5 MiB each; source files are a separate table, and only data files are stored;
    - a source version copies the settings that change how records are read, and is sealed once with a fingerprint of its file list computed by the database;
    - only sealed versions are used.
13. **PRD 5.8 and 9.2:** power-based sufficiency is not an option in sprint 1. It is an "estimated power report (information only)"; as a gate it stays in the backlog.
14. **PRD 8 (new):** what may be written to a run in each state, as in the table above. After completion: commentary, the Commentator's stage and calls, and artifacts. After failure: only the audit log. A run ends only with no stage running and no call open.

## Tests (353, all passing; 165 for step 3; the 93 from step 1 and the login tests unchanged)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data tests/test_login.py tests/test_login_throttle.py` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_data_model.py` (new) | 134 | Every rule above, each with an allowed case and a rejected case, on a fresh migrated scratch database |
| `tests/test_concurrency.py` (new) | 14 | Two-connection races for the locking protocol (finding 1) |
| `tests/test_migrations.py` (new) | 11 | One head; downgrades; no statement escapes the transaction; migrations in the package; up, down, up; upgrade at head; failed upgrade; concurrent upgrades; command line; production downgrade refused; no password printed; `schema_status` |
| `tests/model_builder.py` (new) | — | Walks a run through the lifecycle in plain SQL, one transaction per step. Sources get one sealed version with one file. |
| `tests/conftest.py` | — | `empty_database`, a session `template_database` migrated once, `migrated_database` copied from it, and `db`. Tests never touch the database at `DATABASE_URL`. |
| `tests/test_health.py` | 8 (+1) | `schema` on `/health` |
| `tests/test_skeleton.py` | 33 (+2) | Compose `migrate` ordering; Render pre-deploy on both services |
| `tests/test_check_runtime_image.py` | 14 (+3) | A missing migration file fails the image check |

### Tests removed or replaced, and why (none weakened)
First round (before the review):
- `test_health_without_login_database_up` and `test_health_page_in_a_browser` now use scratch databases; the exact-equality assertion is kept, extended with `schema`. `test_health_reports_database_down_without_crashing` gains a `schema` assertion.
- `COMPOSE_ENV` in `tests/test_skeleton.py` gains the `migrate` service.

Fix round (finding 6, the single run-level label is removed):
- `test_a_reported_negative_result_is_kept_distinct` → `test_mixed_results_are_reported_per_category`. The old test asserted the collapsed label "reported_negative", which is the behaviour the review rejected; the new one asserts both categories with their sources.
- `test_no_source_searched_is_failed_search` → `test_every_selected_source_failing_shows_no_source_searched`. The same situation, asserted per category.
- `test_records_found_but_insufficient_is_missing_evidence` → `test_records_found_is_its_own_category`. The old test asserted that records found counted as "missing evidence" at run level; records found is now its own category.
- `test_nothing_found_applies_only_to_insufficient_runs` is removed: it tested when the run-level label appears, and no run-level label exists any more. Coverage is now covered by `test_coverage_comes_from_the_runs_own_dispatch_rows` and `test_a_run_starts_only_with_its_full_source_inventory`.
- `test_a_failed_source_is_never_missing_evidence` keeps its name; it now asserts the categories instead of a label.
- `test_run_has_no_stored_nothing_found_column` is renamed `test_no_table_stores_a_run_level_nothing_found`; the assertion is unchanged.

Fix round (finding 3, records only after the rules lock):
- `test_eligibility_is_decided_only_under_a_locked_plan` → `test_records_and_eligibility_come_after_the_rules_lock`. The old first step (deciding on a record extracted before the lock) can no longer be set up, because such a record is rejected; the new test asserts that rejection. The append-only assertions are unchanged.
- **Setup only; the assertions are unchanged.** These tests now lock the plan before extracting:
  - `test_records_are_never_updated_or_deleted`;
  - `test_a_record_comes_from_a_source_version_its_run_recorded`;
  - `test_every_record_names_its_origin`;
  - `test_a_run_decides_only_on_its_own_records`;
  - `test_a_flag_names_records_of_its_own_run`;
  - `test_a_model_recalled_record_is_stored_but_never_eligible`, which also registers a model-recall source, because a record's kind must match its version's.

Fix round (other setup changes; the assertions are unchanged unless stated):
- `test_a_run_source_starts_undecided`: the run is now running, because a queued run's rows cannot be updated at all. The "is final" assertion is unchanged.
- `test_the_source_version_of_a_run_cannot_change`: the other version is created and sealed through the new path.
- `test_commentary_comes_after_completion_and_lists_mismatches`: the stage created before completion is finished first, because a run ends only with no stage running. The commentary after completion uses a commentator stage created after completion.
- `test_source_files_are_data_files_up_to_5_mib`: uses an unsealed version, because files can be added only before sealing. The label-change assertions now expect the sealing messages instead of "append-only".
- `test_the_validity_checks_cannot_be_waived`: constraint name `check2_definition` → `check2_consistent`.
- `test_one_result_per_run_and_scope_on_the_right_set`: the per-source-without-source insert now has `n_groups = 1`, so that the source CHECK is the one tested; the new `records_have_a_group` CHECK would otherwise fire first.
- `test_migrations_stay_inside_the_one_transaction`: now matches whole words in code with comments removed, because a new comment says "committed". It still catches every statement it caught before.

### Suite results
```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, `docker compose up -d db`)
353 passed in 46.53s
$ docker compose run --rm test           (the test image)
353 passed in 48.24s
GitHub Actions, commit e253950 (last code change): success; "Run the suite in the test image": 353 passed.
https://github.com/kelawady/hypocurate/actions/runs/37250072104
```
The `ERROR: hypocurate: …` lines in the CI log's database output are the refusals the tests provoke on purpose.

Local checks beyond the suite:
- `docker compose up -d`: `migrate` exited 0 ("schema at 0001"), and `/health` reported `"schema":{"revision":"0001","at_head":true}`.
- The local database has `run_search_coverage` and 40 functions.

## Deviations from the approved plans
1. **`CREATE TABLE` statements rendered by autogenerate, then edited by hand** (first round). The drift and catalog-snapshot tests compare them with the models.
2. **More database rules than the first plan listed** (first round): run insertion needs a dispatched version with a supported domain; `run_record` is append-only; `hypothesis` is append-only; `locked_at` and `frozen_at` equal the database's time.
3. **NULL-safe trigger checks** (first round, commit `10f08c3`).
4. **Query numbers can skip.** A rejected insert leaves a gap in the `Q-` sequence; numbers stay unique and increasing.
5. **Fix-round commits grouped by area, not one per finding.** The plan said each finding would be its own commit with its tests. All seven fixes change the same migration file and test files, and splitting them would have needed interactive staging, which is not available here. The fixes are in commit `2fc0fe2`, whose message lists all seven; the race tests are in `0d009b0` and the README in `e253950`.
6. **The local development database was reset by hand.** The edited migration's downgrade could not run on a database migrated with the earlier text (it drops views by their new names). The local database held no rows (`hypothesis` and `run` both 0), so I ran `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` and migrated again. Production has never been migrated.
7. **Extra rules beyond the fix plan, each tested:**
   - a source's key and registration time cannot change, so coverage names stay stable;
   - a stage result starts as `running`;
   - the commentary must come from the commentator stage.

## Open items
1. **Live check after merge** (owner's go-ahead): Render's deploy log shows the pre-deploy command ran on both services, and live `/health` shows `"schema":{"revision":"0001","at_head":true}`. This is the first time a pre-deploy command runs with our Docker services. The merge also syncs the Blueprint.
2. **Lock contention (step 9).** A long transaction on a run holds its lock; a heartbeat update of the same run waits until it commits. Keep checkpoint transactions short, or move heartbeats to their own table if that proves a problem.
3. **Step 4** adopts the source-version fingerprint definition above, seals every version before use, and loads the two frozen sources.
4. **Step 6:** each run has a property, alloy-class and test-condition tag; duplicate handling (the duplicate test shows storage only).
5. **Step 7 and step 9 requirements** are listed above.
6. Storage estimate (about 4–6 MB per run, 120–200 runs in 1 GB), to be measured in step 8.
7. The test database user must be allowed to create databases. The tests never run against Render.
8. Source registration's "access key" (PRD 9.6) has no column; secrets stay in environment variables.
9. Carried from step 2, unchanged: the pooled p-value 7.4e-7 against "≈ 8e-7" (step 7); permitted test types and a non-MPEA survivor pair (step 6); the access layer must enforce the approved file list (step 5).
````

## 2. Files changed since the first review (`4737b08`)

```
M	README.md
A	docs/reviews/step03_review_chatgpt.md
M	docs/reviews/step03_summary.md
M	hypocurate/db/migrations/versions/0001_data_model.py
M	hypocurate/db/models.py
M	tests/model_builder.py
A	tests/test_concurrency.py
M	tests/test_data_model.py
M	tests/test_migrations.py
M	docs/reviews/step03_summary.md   (updated with this packet)
A	docs/reviews/step03_fix_packet.md   (this file)
```

## 3. Changed files (full text)

### `hypocurate/db/migrations/versions/0001_data_model.py`

SHA-256 `aca64882613242f914954f5e279d9bdfe5f1d93f97d0041b38e87c960e5d4e77`, 86689 bytes.

```python
"""Data model (build step 3): the tables of PRD Section 7 and the rules the database enforces.

Revision ID: 0001
Revises:
Create Date: 2026-10-05

The CREATE TABLE statements were rendered by Alembic autogenerate from
`hypocurate/db/models.py` and then reviewed and edited by hand (sequence and the
hypothesis -> run foreign key moved; long names shortened). The trigger
functions, triggers, views and the seed rows below are hand-written. The models
are not imported here, so this migration stays as it was when it was written.

Every trigger rejection raises SQLSTATE 23514 (check_violation) with a message
starting "hypocurate: ".

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('agent_setting',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('instruction', sa.Text(), nullable=False),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('limits', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_agent_setting_role')),
    sa.CheckConstraint('version >= 1', name=op.f('ck_agent_setting_version_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_agent_setting')),
    sa.UniqueConstraint('id', 'role', name=op.f('uq_agent_setting_id_role')),
    sa.UniqueConstraint('role', 'version', name=op.f('uq_agent_setting_role_version'))
    )
    op.create_table('domain',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('supported', sa.Boolean(), nullable=False),
    sa.Column('profile_name', sa.Text(), nullable=True),
    sa.CheckConstraint('NOT supported OR profile_name IS NOT NULL', name=op.f('ck_domain_supported_has_profile')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_domain')),
    sa.UniqueConstraint('key', name=op.f('uq_domain_key'))
    )
    op.execute("CREATE SEQUENCE hypothesis_number_seq")
    op.create_table('hypothesis',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('number', sa.Text(), server_default=sa.text("'Q-' || lpad(nextval('hypothesis_number_seq')::text, 4, '0')"), nullable=False),
    sa.Column('narrower_of_run_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hypothesis')),
    sa.UniqueConstraint('number', name=op.f('uq_hypothesis_number'))
    )
    op.create_table('source',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('source_type', sa.Text(), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('licence', sa.Text(), nullable=False),
    sa.Column('data_kind', sa.Text(), nullable=False),
    sa.Column('adapter_status', sa.Text(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('grouping_unit', sa.Text(), nullable=False),
    sa.Column('properties_covered', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("adapter_status IN ('adapter_needed', 'available')", name=op.f('ck_source_adapter_status')),
    sa.CheckConstraint("data_kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_source_data_kind')),
    sa.CheckConstraint("grouping_unit IN ('paper', 'dataset', 'batch')", name=op.f('ck_source_grouping_unit')),
    sa.CheckConstraint("key ~ '^[a-z0-9_]+$'", name=op.f('ck_source_key_format')),
    sa.CheckConstraint("source_type IN ('uploaded_table', 'web_interface', 'paper_search', 'model_recall')", name=op.f('ck_source_source_type')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source')),
    sa.UniqueConstraint('key', name=op.f('uq_source_key'))
    )
    op.create_table('hypothesis_version',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('hypothesis_id', sa.BigInteger(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('domain_id', sa.BigInteger(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default=sa.text("'draft'"), nullable=False),
    sa.Column('confirmed_domain_id', sa.BigInteger(), nullable=True),
    sa.Column('domain_confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status <> 'dispatched' OR (confirmed_domain_id IS NOT NULL AND dispatched_at IS NOT NULL)", name=op.f('ck_hypothesis_version_dispatch_needs_confirmed_domain')),
    sa.CheckConstraint("status <> 'returned' OR returned_at IS NOT NULL", name=op.f('ck_hypothesis_version_returned_time')),
    sa.CheckConstraint("status = 'draft' OR submitted_at IS NOT NULL", name=op.f('ck_hypothesis_version_submitted_time')),
    sa.CheckConstraint("status IN ('draft', 'submitted', 'returned', 'dispatched')", name=op.f('ck_hypothesis_version_status')),
    sa.CheckConstraint('(confirmed_domain_id IS NULL) = (domain_confirmed_at IS NULL)', name=op.f('ck_hypothesis_version_confirmed_domain_with_time')),
    sa.CheckConstraint('length(btrim(text)) > 0', name=op.f('ck_hypothesis_version_text_not_empty')),
    sa.CheckConstraint('version_number >= 1', name=op.f('ck_hypothesis_version_version_positive')),
    sa.ForeignKeyConstraint(['confirmed_domain_id'], ['domain.id'], name=op.f('fk_hypothesis_version_confirmed_domain_id')),
    sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], name=op.f('fk_hypothesis_version_domain_id')),
    sa.ForeignKeyConstraint(['hypothesis_id'], ['hypothesis.id'], name=op.f('fk_hypothesis_version_hypothesis_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hypothesis_version')),
    sa.UniqueConstraint('hypothesis_id', 'version_number', name=op.f('uq_hypothesis_version_hypothesis_id_version_number'))
    )
    op.create_table('source_version',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.Column('label', sa.Text(), nullable=False),
    sa.Column('obtained_on', sa.Date(), nullable=False),
    sa.Column('source_type', sa.Text(), nullable=False),
    sa.Column('data_kind', sa.Text(), nullable=False),
    sa.Column('grouping_unit', sa.Text(), nullable=False),
    sa.Column('sealed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('fingerprint', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_fingerprint_format')),
    sa.CheckConstraint('(sealed_at IS NULL) = (fingerprint IS NULL)', name=op.f('ck_source_version_sealed_with_fingerprint')),
    sa.CheckConstraint("source_type IN ('uploaded_table', 'web_interface', 'paper_search', 'model_recall')", name=op.f('ck_source_version_source_type')),
    sa.CheckConstraint("data_kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_source_version_data_kind')),
    sa.CheckConstraint("grouping_unit IN ('paper', 'dataset', 'batch')", name=op.f('ck_source_version_grouping_unit')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_source_version_source_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source_version')),
    sa.UniqueConstraint('id', 'source_id', name=op.f('uq_source_version_id_source_id')),
    sa.UniqueConstraint('source_id', 'fingerprint', name=op.f('uq_source_version_source_id_fingerprint'))
    )
    op.create_table('hypothesis_version_source',
    sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_hypothesis_version_source_hypothesis_version_id')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_hypothesis_version_source_source_id')),
    sa.PrimaryKeyConstraint('hypothesis_version_id', 'source_id', name=op.f('pk_hypothesis_version_source'))
    )
    op.create_table('run',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'queued'"), nullable=False),
    sa.Column('current_stage', sa.Text(), nullable=True),
    sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('outcome', sa.Text(), nullable=True),
    sa.Column('verdict', sa.Text(), nullable=True),
    sa.Column('exploratory', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('agent_mode', sa.Text(), server_default=sa.text("'four_roles'"), nullable=False),
    sa.Column('fixed_plan', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('experiment_flags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(outcome IS NOT NULL) = (status = 'completed')", name=op.f('ck_run_outcome_iff_completed')),
    sa.CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name=op.f('ck_run_failed_has_reason')),
    sa.CheckConstraint("(verdict IS NOT NULL) = (status = 'completed' AND outcome IS NOT DISTINCT FROM 'sufficient')", name=op.f('ck_run_verdict_iff_sufficient')),
    sa.CheckConstraint("agent_mode = 'four_roles'", name=op.f('ck_run_agent_mode')),
    sa.CheckConstraint("outcome IS NULL OR outcome IN ('sufficient', 'partly_sufficient', 'insufficient')", name=op.f('ck_run_outcome')),
    sa.CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name=op.f('ck_run_completed_time')),
    sa.CheckConstraint("status <> 'failed' OR failed_at IS NOT NULL", name=op.f('ck_run_failed_time')),
    sa.CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name=op.f('ck_run_started_time')),
    sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name=op.f('ck_run_status')),
    sa.CheckConstraint("verdict IS NULL OR verdict IN ('supported', 'not_supported')", name=op.f('ck_run_verdict')),
    sa.CheckConstraint('NOT exploratory OR verdict IS NOT NULL', name=op.f('ck_run_exploratory_needs_verdict')),
    sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_run_hypothesis_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_run'))
    )
    op.create_foreign_key(op.f('fk_hypothesis_narrower_of_run_id'), 'hypothesis', 'run', ['narrower_of_run_id'], ['id'])
    op.create_table('source_file',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=False),
    sa.Column('path', sa.Text(), nullable=False),
    sa.Column('sha256', sa.Text(), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=False),
    sa.CheckConstraint("path ~ '\\.(csv|xlsx)$'", name=op.f('ck_source_file_data_file_type')),
    sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=op.f('ck_source_file_sha256_matches_content')),
    sa.CheckConstraint('octet_length(content) <= 5242880', name=op.f('ck_source_file_max_size')),
    sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'], name=op.f('fk_source_file_source_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source_file')),
    sa.UniqueConstraint('source_version_id', 'path', name=op.f('uq_source_file_source_version_id_path'))
    )
    op.create_table('analysis_set',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.CheckConstraint("key ~ '^[a-z0-9_]+$'", name=op.f('ck_analysis_set_key_format')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_analysis_set_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_set')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_analysis_set_id_run_id')),
    sa.UniqueConstraint('run_id', 'key', name=op.f('uq_analysis_set_run_id_key'))
    )
    op.create_table('artifact',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('filename', sa.Text(), nullable=False),
    sa.Column('media_type', sa.Text(), nullable=False),
    sa.Column('sha256', sa.Text(), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('plot', 'workbook', 'csv')", name=op.f('ck_artifact_kind')),
    sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=op.f('ck_artifact_sha256_matches_content')),
    sa.CheckConstraint('octet_length(content) <= 5242880', name=op.f('ck_artifact_max_size')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_artifact_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_artifact'))
    )
    op.create_table('audit_log',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('stage', sa.Text(), nullable=False),
    sa.Column('function', sa.Text(), nullable=False),
    sa.Column('allowed', sa.Boolean(), nullable=False),
    sa.Column('detail', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_audit_log_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log'))
    )
    op.create_index('ix_audit_log_run_id', 'audit_log', ['run_id'], unique=False)
    op.create_table('flag',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('category', sa.Text(), nullable=False),
    sa.Column('compared_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('raised_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('critic_class', sa.Text(), nullable=True),
    sa.Column('critic_reason', sa.Text(), nullable=True),
    sa.Column('classified_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(critic_class IS NULL) = (classified_at IS NULL)', name=op.f('ck_flag_classified_time')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_flag_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_flag'))
    )
    op.create_table('plan',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('fingerprint', sa.Text(), nullable=False),
    sa.Column('locked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('sufficiency_option', sa.Text(), nullable=False),
    sa.Column('min_records', sa.Integer(), nullable=False),
    sa.Column('min_alloys', sa.Integer(), nullable=False),
    sa.Column('min_groups', sa.Integer(), nullable=False),
    sa.Column('min_resid_df', sa.Integer(), nullable=False),
    sa.Column('sensitivity_analysis_keys', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('power_assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.CheckConstraint("NOT ('primary' = ANY (sensitivity_analysis_keys))", name=op.f('ck_plan_primary_not_sensitivity')),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_plan_fingerprint_format')),
    sa.CheckConstraint("sufficiency_option IN ('fixed_minimum', 'use_available')", name=op.f('ck_plan_sufficiency_option')),
    sa.CheckConstraint('min_records >= 1 AND min_alloys >= 1 AND min_groups >= 1 AND min_resid_df >= 1', name=op.f('ck_plan_minimums_positive')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_plan_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plan')),
    sa.UniqueConstraint('run_id', name=op.f('uq_plan_run_id'))
    )
    op.create_table('record',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('extraction_run_id', sa.BigInteger(), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=False),
    sa.Column('source_item_key', sa.Text(), nullable=False),
    sa.Column('item_index', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('alloy', sa.Text(), nullable=True),
    sa.Column('harmonized', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reported', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('paper_reference', sa.Text(), nullable=True),
    sa.Column('paper_doi', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_record_kind')),
    sa.CheckConstraint('item_index >= 0', name=op.f('ck_record_item_index_not_negative')),
    sa.CheckConstraint('length(source_item_key) > 0', name=op.f('ck_record_item_key_not_empty')),
    sa.ForeignKeyConstraint(['extraction_run_id'], ['run.id'], name=op.f('fk_record_extraction_run_id')),
    sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'], name=op.f('fk_record_source_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_record')),
    sa.UniqueConstraint('extraction_run_id', 'source_version_id', 'source_item_key', 'item_index', name='uq_record_origin_per_run')
    )
    op.create_index('ix_record_source_version_id_source_item_key', 'record', ['source_version_id', 'source_item_key'], unique=False)
    op.create_table('run_agent_setting',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('agent_setting_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['agent_setting_id', 'role'], ['agent_setting.id', 'agent_setting.role'], name='fk_run_agent_setting_agent_setting'),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_agent_setting_run_id')),
    sa.PrimaryKeyConstraint('run_id', 'role', name=op.f('pk_run_agent_setting'))
    )
    op.create_table('run_snapshot',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('fingerprint', sa.Text(), nullable=False),
    sa.Column('frozen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('n_records', sa.Integer(), nullable=False),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_run_snapshot_fingerprint_format')),
    sa.CheckConstraint('n_records >= 1', name=op.f('ck_run_snapshot_not_empty')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_snapshot_run_id')),
    sa.PrimaryKeyConstraint('run_id', name=op.f('pk_run_snapshot'))
    )
    op.create_table('run_source',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=True),
    sa.Column('search_status', sa.Text(), nullable=False),
    sa.Column('nothing_found', sa.Text(), nullable=True),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(search_status = 'failed') = (nothing_found IS NOT DISTINCT FROM 'failed_search')", name=op.f('ck_run_source_failed_iff_failed_search')),
    sa.CheckConstraint("(search_status IN ('searched', 'failed')) = (decided_at IS NOT NULL)", name=op.f('ck_run_source_decided_time')),
    sa.CheckConstraint("nothing_found IS NULL OR nothing_found IN ('reported_negative', 'missing_evidence', 'failed_search')", name=op.f('ck_run_source_nothing_found')),
    sa.CheckConstraint("search_status <> 'failed' OR failure_reason IS NOT NULL", name=op.f('ck_run_source_failed_has_reason')),
    sa.CheckConstraint("search_status <> 'not_selected' OR source_version_id IS NULL", name=op.f('ck_run_source_not_selected_no_version')),
    sa.CheckConstraint("search_status <> 'searched' OR source_version_id IS NOT NULL", name=op.f('ck_run_source_searched_has_version')),
    sa.CheckConstraint("search_status IN ('not_selected', 'pending', 'searched', 'failed')", name=op.f('ck_run_source_search_status')),
    sa.CheckConstraint("search_status NOT IN ('not_selected', 'pending') OR nothing_found IS NULL", name=op.f('ck_run_source_undecided_has_no_kind')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_source_run_id')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_run_source_source_id')),
    sa.ForeignKeyConstraint(['source_version_id', 'source_id'], ['source_version.id', 'source_version.source_id'], name='fk_run_source_source_version'),
    sa.PrimaryKeyConstraint('run_id', 'source_id', name=op.f('pk_run_source'))
    )
    op.create_table('stage_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage', sa.Text(), nullable=False),
    sa.Column('attempt', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default=sa.text("'running'"), nullable=False),
    sa.Column('input', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('tool_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('agent_setting_id', sa.BigInteger(), nullable=True),
    sa.Column('model', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'running') = (finished_at IS NULL)", name=op.f('ck_stage_result_finished_time')),
    sa.CheckConstraint("role IS NULL OR role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_stage_result_role')),
    sa.CheckConstraint("stage ~ '^[a-z_]+$'", name=op.f('ck_stage_result_stage_format')),
    sa.CheckConstraint("status IN ('running', 'done', 'failed', 'skipped')", name=op.f('ck_stage_result_status')),
    sa.CheckConstraint('attempt >= 1', name=op.f('ck_stage_result_attempt_positive')),
    sa.ForeignKeyConstraint(['agent_setting_id'], ['agent_setting.id'], name=op.f('fk_stage_result_agent_setting_id')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_stage_result_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stage_result')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_stage_result_id_run_id')),
    sa.UniqueConstraint('run_id', 'stage', 'attempt', name=op.f('uq_stage_result_run_id_stage_attempt'))
    )
    op.create_table('tag_value',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('proposed_by_run_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'proposed') = (decided_at IS NULL)", name=op.f('ck_tag_value_decided_once')),
    sa.CheckConstraint("kind IN ('property', 'alloy_class', 'test_condition')", name=op.f('ck_tag_value_kind')),
    sa.CheckConstraint("status IN ('proposed', 'approved', 'rejected')", name=op.f('ck_tag_value_status')),
    sa.CheckConstraint('length(value) > 0', name=op.f('ck_tag_value_value_not_empty')),
    sa.ForeignKeyConstraint(['proposed_by_run_id'], ['run.id'], name=op.f('fk_tag_value_proposed_by_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tag_value')),
    sa.UniqueConstraint('kind', 'value', name=op.f('uq_tag_value_kind_value'))
    )
    op.create_table('analysis_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('scope', sa.Text(), nullable=False),
    sa.Column('analysis_set_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=True),
    sa.Column('n_records', sa.Integer(), nullable=False),
    sa.Column('n_alloys', sa.Integer(), nullable=False),
    sa.Column('n_groups', sa.Integer(), nullable=False),
    sa.Column('resid_df', sa.Integer(), nullable=False),
    sa.Column('check1_passed', sa.Boolean(), nullable=False),
    sa.Column('check2_passed', sa.Boolean(), nullable=False),
    sa.Column('minimums_met', sa.Boolean(), nullable=False),
    sa.Column('estimate', sa.Double(), nullable=True),
    sa.Column('std_error', sa.Double(), nullable=True),
    sa.Column('p_value', sa.Double(), nullable=True),
    sa.Column('estimated_power', sa.Double(), nullable=True),
    sa.Column('label', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("(scope = 'per_source') = (source_id IS NOT NULL)", name=op.f('ck_analysis_result_source_iff_per_source')),
    sa.CheckConstraint("label IS NULL OR label IN ('agrees', 'conflicts', 'not_enough_data')", name=op.f('ck_analysis_result_label')),
    sa.CheckConstraint("scope IN ('pooled', 'per_source', 'sensitivity')", name=op.f('ck_analysis_result_scope')),
    sa.CheckConstraint('check1_passed = (estimate IS NOT NULL)', name=op.f('ck_analysis_result_estimate_iff_check1')),
    sa.CheckConstraint('check1_passed = (n_alloys >= 1)', name=op.f('ck_analysis_result_check1_consistent')),
    sa.CheckConstraint('check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)', name=op.f('ck_analysis_result_check2_consistent')),
    sa.CheckConstraint('n_records >= 2 * n_alloys', name=op.f('ck_analysis_result_two_records_per_alloy')),
    sa.CheckConstraint('n_groups <= n_records', name=op.f('ck_analysis_result_groups_within_records')),
    sa.CheckConstraint('n_records = 0 OR n_groups >= 1', name=op.f('ck_analysis_result_records_have_a_group')),
    sa.CheckConstraint('check2_passed = (p_value IS NOT NULL)', name=op.f('ck_analysis_result_p_value_iff_check2')),
    sa.CheckConstraint('check2_passed = (std_error IS NOT NULL)', name=op.f('ck_analysis_result_std_error_iff_check2')),
    sa.CheckConstraint('estimated_power IS NULL OR estimated_power BETWEEN 0 AND 1', name=op.f('ck_analysis_result_power_range')),
    sa.CheckConstraint('n_records >= 0 AND n_alloys >= 0 AND n_groups >= 0', name=op.f('ck_analysis_result_counts_not_negative')),
    sa.CheckConstraint('p_value IS NULL OR p_value BETWEEN 0 AND 1', name=op.f('ck_analysis_result_p_value_range')),
    sa.CheckConstraint('resid_df = n_records - n_alloys - 1', name=op.f('ck_analysis_result_resid_df_definition')),
    sa.CheckConstraint('std_error IS NULL OR std_error >= 0', name=op.f('ck_analysis_result_std_error_not_negative')),
    sa.ForeignKeyConstraint(['analysis_set_id', 'run_id'], ['analysis_set.id', 'analysis_set.run_id'], name='fk_analysis_result_analysis_set'),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_analysis_result_source_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_result')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_analysis_result_id_run_id'))
    )
    op.create_index('uq_analysis_result_scope', 'analysis_result', ['run_id', 'scope', 'analysis_set_id', 'source_id'], unique=True, postgresql_nulls_not_distinct=True)
    op.create_table('analysis_set_record',
    sa.Column('analysis_set_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_set_id'], ['analysis_set.id'], name=op.f('fk_analysis_set_record_analysis_set_id')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_analysis_set_record_record_id')),
    sa.PrimaryKeyConstraint('analysis_set_id', 'record_id', name=op.f('pk_analysis_set_record'))
    )
    op.create_table('commentary',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage_result_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('number_check', sa.Text(), nullable=True),
    sa.Column('mismatches', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("(number_check IS NOT DISTINCT FROM 'mismatches') = (mismatches IS NOT NULL)", name=op.f('ck_commentary_mismatches_listed')),
    sa.CheckConstraint("(status = 'written') = (text IS NOT NULL AND number_check IS NOT NULL)", name=op.f('ck_commentary_written_has_text_and_check')),
    sa.CheckConstraint("number_check IS NULL OR number_check IN ('all_match', 'mismatches')", name=op.f('ck_commentary_number_check')),
    sa.CheckConstraint("status IN ('written', 'unavailable')", name=op.f('ck_commentary_status')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_commentary_run_id')),
    sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'], name='fk_commentary_stage_result'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_commentary')),
    sa.UniqueConstraint('run_id', name=op.f('uq_commentary_run_id'))
    )
    op.create_table('flag_record',
    sa.Column('flag_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['flag_id'], ['flag.id'], name=op.f('fk_flag_record_flag_id')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_flag_record_record_id')),
    sa.PrimaryKeyConstraint('flag_id', 'record_id', name=op.f('pk_flag_record'))
    )
    op.create_table('model_call',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage_result_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('price_table_version', sa.Text(), nullable=False),
    sa.Column('max_cost', sa.Numeric(), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'started'"), nullable=False),
    sa.Column('input_tokens', sa.BigInteger(), nullable=True),
    sa.Column('output_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cached_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cost', sa.Numeric(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_model_call_role')),
    sa.CheckConstraint("status <> 'failed' OR (finished_at IS NOT NULL AND ((input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL) OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL)))", name=op.f('ck_model_call_failed_usage_all_or_none')),
    sa.CheckConstraint("status <> 'interrupted' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_interrupted_has_no_usage')),
    sa.CheckConstraint("status <> 'started' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NULL)", name=op.f('ck_model_call_started_has_no_usage')),
    sa.CheckConstraint("status <> 'succeeded' OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_succeeded_has_usage')),
    sa.CheckConstraint("status IN ('started', 'succeeded', 'failed', 'interrupted')", name=op.f('ck_model_call_status')),
    sa.CheckConstraint('coalesce(input_tokens, 0) >= 0 AND coalesce(output_tokens, 0) >= 0 AND coalesce(cached_tokens, 0) >= 0 AND coalesce(cost, 0) >= 0', name=op.f('ck_model_call_usage_not_negative')),
    sa.CheckConstraint('length(model) > 0 AND length(price_table_version) > 0', name=op.f('ck_model_call_model_and_prices_named')),
    sa.CheckConstraint('max_cost > 0', name=op.f('ck_model_call_max_cost_positive')),
    sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'], name='fk_model_call_stage_result'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_call'))
    )
    op.create_index('ix_model_call_run_id', 'model_call', ['run_id'], unique=False)
    op.create_table('run_record',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.Column('eligible', sa.Boolean(), nullable=False),
    sa.Column('rule', sa.Text(), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(rule) > 0', name=op.f('ck_run_record_rule_named')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_run_record_record_id')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_record_run_id')),
    sa.PrimaryKeyConstraint('run_id', 'record_id', name=op.f('pk_run_record'))
    )
    op.create_table('run_tag',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_value_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_tag_run_id')),
    sa.ForeignKeyConstraint(['tag_value_id'], ['tag_value.id'], name=op.f('fk_run_tag_tag_value_id')),
    sa.PrimaryKeyConstraint('run_id', 'tag_value_id', name=op.f('pk_run_tag'))
    )
    op.create_table('calibration_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('analysis_result_id', sa.BigInteger(), nullable=True),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('n_simulations', sa.Integer(), nullable=True),
    sa.Column('seed', sa.BigInteger(), nullable=True),
    sa.Column('null_share', sa.Double(), nullable=True),
    sa.Column('null_ci_low', sa.Double(), nullable=True),
    sa.Column('null_ci_high', sa.Double(), nullable=True),
    sa.Column('effect_share', sa.Double(), nullable=True),
    sa.Column('effect_ci_low', sa.Double(), nullable=True),
    sa.Column('effect_ci_high', sa.Double(), nullable=True),
    sa.Column('confidence_flag', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("confidence_flag IS NULL OR confidence_flag IN ('none', 'over_confident', 'under_confident')", name=op.f('ck_calibration_result_confidence_flag')),
    sa.CheckConstraint("reason IS NULL OR reason IN ('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')", name=op.f('ck_calibration_result_reason')),
    sa.CheckConstraint("status <> 'computed' OR (reason IS NULL AND assumptions IS NOT NULL AND n_simulations IS NOT NULL AND seed IS NOT NULL AND null_share IS NOT NULL AND null_ci_low IS NOT NULL AND null_ci_high IS NOT NULL AND effect_share IS NOT NULL AND effect_ci_low IS NOT NULL AND effect_ci_high IS NOT NULL AND confidence_flag IS NOT NULL)", name=op.f('ck_calibration_result_computed_is_complete')),
    sa.CheckConstraint("status <> 'unavailable' OR (reason IS NOT NULL AND assumptions IS NULL AND n_simulations IS NULL AND seed IS NULL AND null_share IS NULL AND null_ci_low IS NULL AND null_ci_high IS NULL AND effect_share IS NULL AND effect_ci_low IS NULL AND effect_ci_high IS NULL AND confidence_flag IS NULL)", name=op.f('ck_calibration_result_unavailable_has_reason_only')),
    sa.CheckConstraint("status IN ('computed', 'unavailable')", name=op.f('ck_calibration_result_status')),
    sa.CheckConstraint('effect_share IS NULL OR (0 <= effect_ci_low AND effect_ci_low <= effect_share AND effect_share <= effect_ci_high AND effect_ci_high <= 1)', name=op.f('ck_calibration_result_effect_interval')),
    sa.CheckConstraint("(analysis_result_id IS NULL) = (reason IS NOT DISTINCT FROM 'no_dataset_frozen')", name=op.f('ck_calibration_result_run_level_only_without_freeze')),
    sa.CheckConstraint('n_simulations IS NULL OR n_simulations >= 1', name=op.f('ck_calibration_result_simulations_positive')),
    sa.CheckConstraint('null_share IS NULL OR (0 <= null_ci_low AND null_ci_low <= null_share AND null_share <= null_ci_high AND null_ci_high <= 1)', name=op.f('ck_calibration_result_null_interval')),
    sa.ForeignKeyConstraint(['analysis_result_id', 'run_id'], ['analysis_result.id', 'analysis_result.run_id'], name='fk_calibration_result_analysis_result'),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_calibration_result_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_calibration_result'))
    )
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id'], unique=True, postgresql_nulls_not_distinct=True)
    for statement in FUNCTIONS + TRIGGERS + VIEWS + SEED:
        op.execute(statement)


def downgrade() -> None:
    for view in reversed(VIEW_NAMES):
        op.execute(f"DROP VIEW {view}")
    op.drop_constraint(op.f('fk_hypothesis_narrower_of_run_id'), 'hypothesis', type_='foreignkey')
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.drop_table('calibration_result')
    op.drop_table('run_tag')
    op.drop_table('run_record')
    op.drop_index('ix_model_call_run_id', table_name='model_call')
    op.drop_table('model_call')
    op.drop_table('flag_record')
    op.drop_table('commentary')
    op.drop_table('analysis_set_record')
    op.drop_index('uq_analysis_result_scope', table_name='analysis_result', postgresql_nulls_not_distinct=True)
    op.drop_table('analysis_result')
    op.drop_table('tag_value')
    op.drop_table('stage_result')
    op.drop_table('run_source')
    op.drop_table('run_snapshot')
    op.drop_table('run_agent_setting')
    op.drop_index('ix_record_source_version_id_source_item_key', table_name='record')
    op.drop_table('record')
    op.drop_table('plan')
    op.drop_table('flag')
    op.drop_index('ix_audit_log_run_id', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_table('artifact')
    op.drop_table('analysis_set')
    op.drop_table('source_file')
    op.drop_table('run')
    op.drop_table('hypothesis_version_source')
    op.drop_table('source_version')
    op.drop_table('hypothesis_version')
    op.drop_table('source')
    op.drop_table('hypothesis')
    op.drop_table('domain')
    op.drop_table('agent_setting')
    op.execute("DROP SEQUENCE hypothesis_number_seq")
    for function in reversed(FUNCTION_NAMES):
        op.execute(f"DROP FUNCTION {function}")


# ---------------------------------------------------------------------------
# Hand-written: trigger functions, triggers, views, seed rows.
# No '%' anywhere: messages are built with ||.
#
# Locking protocol (review finding 1). Every trigger that checks or changes a run's
# state first locks that run's row with hc_lock_run (SELECT ... FOR NO KEY UPDATE),
# and reads the run's status from that same statement, so it sees the latest
# committed state. Updates of the run row itself take the same lock. Triggers on
# chosen sources and on dispatch lock the hypothesis version first (hc_lock_version);
# submission and dispatch are updates of that row. Lock order: version, then run.
# A transaction that holds a run's lock makes every other writer to that run wait.
#
# What may be written to a run in each state (review finding 3; owner, 2026-10-05):
#   queued:    run_source and run_agent_setting (dispatch); the run becomes running.
#   running:   everything of the pipeline, each in its checkpoint order:
#              plan (+ tags) -> records -> eligibility -> sets -> freeze -> results.
#   completed: only the commentary, the Commentator's stage and model calls, and
#              artifacts. None of them can change the outcome, verdict, analysis
#              results or record sets, which are all final.
#   failed:    nothing (audit_log is written in every state).
# A run can complete or fail only when none of its stages is running and none of its
# model calls is still started.
# ---------------------------------------------------------------------------

FUNCTION_NAMES = [
    "hc_reject(text)",
    "hc_append_only()",
    "hc_no_delete()",
    "hc_is_frozen(bigint)",
    "hc_lock_run(bigint)",
    "hc_lock_version(bigint)",
    "hc_files_fingerprint(bigint)",
    "hc_original_domain(bigint)",
    "hc_hypothesis_insert()",
    "hc_version_insert()",
    "hc_version_update()",
    "hc_version_source_change()",
    "hc_run_insert()",
    "hc_run_update()",
    "hc_plan_insert()",
    "hc_run_tag_insert()",
    "hc_tag_value_update()",
    "hc_source_update()",
    "hc_source_version_insert()",
    "hc_source_version_update()",
    "hc_source_file_insert()",
    "hc_run_agent_setting_insert()",
    "hc_run_source_insert()",
    "hc_run_source_update()",
    "hc_record_insert()",
    "hc_run_record_insert()",
    "hc_analysis_set_insert()",
    "hc_analysis_set_record_insert()",
    "hc_run_snapshot_insert()",
    "hc_flag_insert()",
    "hc_flag_update()",
    "hc_flag_record_insert()",
    "hc_analysis_result_insert()",
    "hc_calibration_insert()",
    "hc_commentary_insert()",
    "hc_artifact_insert()",
    "hc_stage_result_insert()",
    "hc_stage_result_update()",
    "hc_model_call_insert()",
    "hc_model_call_update()",
]

FUNCTIONS = [
    # Every rejection goes through here.
    """
    CREATE FUNCTION hc_reject(message text) RETURNS void LANGUAGE plpgsql AS $$
    BEGIN
        RAISE EXCEPTION USING MESSAGE = 'hypocurate: ' || message, ERRCODE = 'check_violation';
    END $$
    """,
    """
    CREATE FUNCTION hc_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM hc_reject(TG_TABLE_NAME || ' is append-only: ' || lower(TG_OP) || ' is not allowed');
        RETURN NULL;
    END $$
    """,
    """
    CREATE FUNCTION hc_no_delete() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM hc_reject(TG_TABLE_NAME || ' rows are never deleted: ' || lower(TG_OP) || ' is not allowed');
        RETURN NULL;
    END $$
    """,
    """
    CREATE FUNCTION hc_is_frozen(p_run bigint) RETURNS boolean LANGUAGE sql STABLE AS $$
        SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = p_run)
    $$
    """,
    # The locking protocol: lock the row and read its current status in one statement.
    """
    CREATE FUNCTION hc_lock_run(p_run bigint) RETURNS text LANGUAGE plpgsql AS $$
    DECLARE s text;
    BEGIN
        SELECT status INTO s FROM run WHERE id = p_run FOR NO KEY UPDATE;
        RETURN s;
    END $$
    """,
    """
    CREATE FUNCTION hc_lock_version(p_version bigint) RETURNS text LANGUAGE plpgsql AS $$
    DECLARE s text;
    BEGIN
        SELECT status INTO s FROM hypothesis_version WHERE id = p_version FOR NO KEY UPDATE;
        RETURN s;
    END $$
    """,
    # A source version's fingerprint (owner, 2026-10-05): SHA-256 of its file list,
    # one line "<sha256>  <path>\\n" per file (the sha256sum format), sorted by path
    # bytewise. Step 4 computes the same in Python.
    """
    CREATE FUNCTION hc_files_fingerprint(p_version bigint) RETURNS text LANGUAGE sql STABLE AS $$
        SELECT encode(sha256(convert_to(
                   string_agg(sha256 || '  ' || path || chr(10), '' ORDER BY path COLLATE "C"), 'UTF8')), 'hex')
        FROM source_file WHERE source_version_id = p_version
    $$
    """,
    # The confirmed domain of the original question, for a narrower query; NULL otherwise.
    """
    CREATE FUNCTION hc_original_domain(p_hypothesis bigint) RETURNS bigint LANGUAGE sql STABLE AS $$
        SELECT hv.confirmed_domain_id
        FROM hypothesis h
        JOIN run r ON r.id = h.narrower_of_run_id
        JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
        WHERE h.id = p_hypothesis
    $$
    """,
    # A narrower question links only to a run whose outcome is partly sufficient (owner, question 1).
    # A completed run never changes, so no lock is needed here.
    """
    CREATE FUNCTION hc_hypothesis_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.narrower_of_run_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM run WHERE id = NEW.narrower_of_run_id
              AND status = 'completed' AND outcome = 'partly_sufficient') THEN
            PERFORM hc_reject('a narrower question can link only to a run whose outcome is partly_sufficient');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original bigint := hc_original_domain(NEW.hypothesis_id);
    BEGIN
        IF NEW.status <> 'draft' OR NEW.confirmed_domain_id IS NOT NULL THEN
            PERFORM hc_reject('a new hypothesis version starts as an unreviewed draft');
        END IF;
        IF original IS NOT NULL AND NEW.domain_id <> original THEN
            PERFORM hc_reject('a narrower question has the domain of its original');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The UPDATE itself holds the version row's lock.
    """
    CREATE FUNCTION hc_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original bigint := hc_original_domain(NEW.hypothesis_id);
    BEGIN
        IF OLD.status IN ('returned', 'dispatched') THEN
            PERFORM hc_reject('a ' || OLD.status || ' hypothesis version cannot change; an edit is a new version');
        END IF;
        IF NEW.hypothesis_id <> OLD.hypothesis_id OR NEW.version_number <> OLD.version_number
           OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('the identity of a hypothesis version cannot change');
        END IF;
        IF OLD.status <> 'draft' AND (NEW.text IS DISTINCT FROM OLD.text OR NEW.domain_id IS DISTINCT FROM OLD.domain_id
                                      OR NEW.note IS DISTINCT FROM OLD.note) THEN
            PERFORM hc_reject('a submitted hypothesis version cannot be edited; an edit is a new version');
        END IF;
        IF NOT ((OLD.status, NEW.status) IN (('draft', 'draft'), ('draft', 'submitted'), ('submitted', 'submitted'),
                                             ('submitted', 'returned'), ('submitted', 'dispatched'))) THEN
            PERFORM hc_reject('hypothesis version status cannot go from ' || OLD.status || ' to ' || NEW.status);
        END IF;
        IF OLD.status <> 'submitted' AND (NEW.confirmed_domain_id IS DISTINCT FROM OLD.confirmed_domain_id
                                          OR NEW.domain_confirmed_at IS DISTINCT FROM OLD.domain_confirmed_at
                                          OR NEW.review_comment IS DISTINCT FROM OLD.review_comment) THEN
            PERFORM hc_reject('review fields can be set only while the version is submitted');
        END IF;
        IF original IS NOT NULL AND (NEW.domain_id <> original OR NEW.confirmed_domain_id <> original) THEN
            PERFORM hc_reject('a narrower question has the domain of its original');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_version_source_change() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE row_version bigint;
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            PERFORM hc_reject('hypothesis_version_source rows are added or removed, not updated');
        END IF;
        row_version := CASE WHEN TG_OP = 'INSERT' THEN NEW.hypothesis_version_id ELSE OLD.hypothesis_version_id END;
        IF hc_lock_version(row_version) IS DISTINCT FROM 'draft' THEN
            PERFORM hc_reject('the chosen sources can change only while the version is a draft');
        END IF;
        RETURN CASE WHEN TG_OP = 'INSERT' THEN NEW ELSE OLD END;
    END $$
    """,
    # Dispatch: the version is dispatched and its confirmed domain is supported (PRD 5.5).
    """
    CREATE FUNCTION hc_run_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.status <> 'queued' OR NEW.exploratory THEN
            PERFORM hc_reject('a run starts as queued');
        END IF;
        IF hc_lock_version(NEW.hypothesis_version_id) IS DISTINCT FROM 'dispatched' THEN
            PERFORM hc_reject('a run needs a dispatched hypothesis version');
        END IF;
        IF (SELECT d.supported FROM hypothesis_version hv JOIN domain d ON d.id = hv.confirmed_domain_id
            WHERE hv.id = NEW.hypothesis_version_id) IS NOT TRUE THEN
            PERFORM hc_reject('dispatch blocked: the confirmed domain is not supported yet');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The UPDATE itself holds the run row's lock, so writers to the run's children wait.
    # Start: the dispatch-time source inventory is complete (review finding 6).
    # Completion and failure: no stage running, no model call open.
    # Completion as sufficient (owner, question 4 and addition 2): exactly one pooled
    # result that passed both validity checks; exploratory = use_available AND minimums not met.
    """
    CREATE FUNCTION hc_run_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE p plan; pooled analysis_result; n_pooled int;
    BEGIN
        IF OLD.status IN ('completed', 'failed') THEN
            PERFORM hc_reject('a ' || OLD.status || ' run is final');
        END IF;
        IF NEW.hypothesis_version_id <> OLD.hypothesis_version_id OR NEW.agent_mode <> OLD.agent_mode
           OR NEW.fixed_plan <> OLD.fixed_plan OR NEW.experiment_flags <> OLD.experiment_flags
           OR NEW.queued_at <> OLD.queued_at THEN
            PERFORM hc_reject('what a run records at dispatch cannot change');
        END IF;
        IF NOT ((OLD.status, NEW.status) IN (('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))) THEN
            PERFORM hc_reject('run status cannot go from ' || OLD.status || ' to ' || NEW.status);
        END IF;
        IF OLD.status = 'queued' AND NEW.status = 'running' AND EXISTS (
            SELECT 1 FROM source s WHERE s.created_at <= NEW.queued_at
              AND NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.id AND rs.source_id = s.id)) THEN
            PERFORM hc_reject('a run starts only with a run_source row for every source registered at dispatch');
        END IF;
        IF NEW.status IN ('completed', 'failed') THEN
            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
                PERFORM hc_reject('a run ends only when no stage is running and no model call is open');
            END IF;
        END IF;
        IF NEW.status = 'completed' AND NEW.outcome = 'sufficient' THEN
            SELECT * INTO p FROM plan WHERE run_id = NEW.id;
            IF NOT FOUND THEN
                PERFORM hc_reject('a sufficient outcome needs a locked plan');
            END IF;
            SELECT count(*) INTO n_pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            IF n_pooled <> 1 OR pooled.check2_passed IS NOT TRUE THEN
                PERFORM hc_reject('a sufficient outcome needs exactly one pooled result that passed both validity checks');
            END IF;
            IF p.sufficiency_option = 'fixed_minimum' AND NOT pooled.minimums_met THEN
                PERFORM hc_reject('under fixed_minimum, a sufficient outcome needs the minimums met');
            END IF;
            IF NEW.exploratory <> (p.sufficiency_option = 'use_available' AND NOT pooled.minimums_met) THEN
                PERFORM hc_reject('exploratory must equal: use_available and the minimums not met');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """,
    # Rules lock (PRD 5.6): inserted once, during the run, with the database's own time.
    """
    CREATE FUNCTION hc_plan_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a plan is locked only while its run is running');
        END IF;
        IF NEW.locked_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('locked_at is set by the database at the lock');
        END IF;
        IF EXISTS (SELECT 1 FROM unnest(NEW.sensitivity_analysis_keys) k WHERE k IS NULL OR k !~ '^[a-z0-9_]+$') THEN
            PERFORM hc_reject('sensitivity analysis keys are lowercase names');
        END IF;
        IF cardinality(NEW.sensitivity_analysis_keys)
           <> (SELECT count(DISTINCT k) FROM unnest(NEW.sensitivity_analysis_keys) k) THEN
            PERFORM hc_reject('sensitivity analysis keys must be unique');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Tags are written in the transaction that locks the plan, and never after.
    """
    CREATE FUNCTION hc_run_tag_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('run tags are written only while the run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.run_id AND locked_at = now()) THEN
            PERFORM hc_reject('run tags are written in the rules-lock transaction only');
        END IF;
        IF (SELECT status FROM tag_value WHERE id = NEW.tag_value_id) IS NOT DISTINCT FROM 'rejected' THEN
            PERFORM hc_reject('a rejected tag value cannot be attached');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_tag_value_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF OLD.status <> 'proposed' OR NEW.status = 'proposed' THEN
            PERFORM hc_reject('a proposed tag value is approved or rejected once');
        END IF;
        IF NEW.kind <> OLD.kind OR NEW.value <> OLD.value OR NEW.created_at <> OLD.created_at
           OR NEW.proposed_by_run_id IS DISTINCT FROM OLD.proposed_by_run_id THEN
            PERFORM hc_reject('only the decision on a tag value can change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A source's key names it in every run's coverage, so it never changes (review finding 6).
    """
    CREATE FUNCTION hc_source_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.key <> OLD.key OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('a source''s key and registration time cannot change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A version copies the settings that change how records are read (review finding 4).
    """
    CREATE FUNCTION hc_source_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s source;
    BEGIN
        SELECT * INTO s FROM source WHERE id = NEW.source_id;
        IF NEW.sealed_at IS NOT NULL OR NEW.fingerprint IS NOT NULL THEN
            PERFORM hc_reject('a source version is sealed after its files are added');
        END IF;
        IF NEW.source_type IS DISTINCT FROM s.source_type AND NEW.source_type IS NOT NULL
           OR NEW.data_kind IS DISTINCT FROM s.data_kind AND NEW.data_kind IS NOT NULL
           OR NEW.grouping_unit IS DISTINCT FROM s.grouping_unit AND NEW.grouping_unit IS NOT NULL THEN
            PERFORM hc_reject('a source version copies its settings from the source');
        END IF;
        NEW.source_type := s.source_type;
        NEW.data_kind := s.data_kind;
        NEW.grouping_unit := s.grouping_unit;
        RETURN NEW;
    END $$
    """,
    # The only change to a version is sealing it, once (owner, 2026-10-05).
    """
    CREATE FUNCTION hc_source_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF OLD.sealed_at IS NOT NULL THEN
            PERFORM hc_reject('a sealed source version cannot change');
        END IF;
        IF NEW.sealed_at IS NULL OR NEW.source_id <> OLD.source_id OR NEW.label <> OLD.label
           OR NEW.obtained_on <> OLD.obtained_on OR NEW.source_type <> OLD.source_type
           OR NEW.data_kind <> OLD.data_kind OR NEW.grouping_unit <> OLD.grouping_unit
           OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('the only change to a source version is sealing it');
        END IF;
        IF NEW.sealed_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('sealed_at is set by the database at sealing');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM source_file WHERE source_version_id = NEW.id) THEN
            PERFORM hc_reject('a source version needs at least one file before sealing');
        END IF;
        IF NEW.fingerprint IS DISTINCT FROM hc_files_fingerprint(NEW.id) THEN
            PERFORM hc_reject('the fingerprint must be the SHA-256 of the sorted file list');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_source_file_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sealed timestamptz;
    BEGIN
        SELECT sealed_at INTO sealed FROM source_version WHERE id = NEW.source_version_id FOR NO KEY UPDATE;
        IF sealed IS NOT NULL THEN
            PERFORM hc_reject('files cannot be added to a sealed source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_agent_setting_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('agent settings versions are recorded at dispatch');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('run sources are recorded at dispatch');
        END IF;
        IF NEW.search_status NOT IN ('not_selected', 'pending') THEN
            PERFORM hc_reject('a run source starts as not_selected or pending');
        END IF;
        IF NEW.source_version_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM source_version WHERE id = NEW.source_version_id AND sealed_at IS NOT NULL) THEN
            PERFORM hc_reject('a run can use only a sealed source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(OLD.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a search result is recorded only while the run is running');
        END IF;
        IF OLD.search_status <> 'pending' THEN
            PERFORM hc_reject('a run source that is ' || OLD.search_status || ' is final');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.source_id <> OLD.source_id
           OR NEW.source_version_id IS DISTINCT FROM OLD.source_version_id THEN
            PERFORM hc_reject('the source and source version of a run cannot change');
        END IF;
        IF NEW.search_status = 'not_selected' THEN
            PERFORM hc_reject('a pending source becomes searched or failed');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Records: after the rules lock, while running, before the freeze, from a version the
    # run recorded, and of the kind that version holds (review findings 3 and 4).
    """
    CREATE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Stored is not analysed (PRD 5.3): eligibility is written once, after the lock, before the freeze.
    """
    CREATE FUNCTION hc_run_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE rec record;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('eligibility is decided only while the run is running');
        END IF;
        SELECT * INTO rec FROM record WHERE id = NEW.record_id;
        IF rec.extraction_run_id IS DISTINCT FROM NEW.run_id THEN
            PERFORM hc_reject('a run decides only on records extracted in that run');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.run_id) THEN
            PERFORM hc_reject('eligibility is decided only under a locked plan');
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('eligibility cannot change after the dataset freeze');
        END IF;
        IF NEW.eligible AND rec.kind = 'model_recalled' THEN
            PERFORM hc_reject('a model-recalled record is never eligible');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A set exists only for 'primary' or an analysis the locked plan names (owner, question 2).
    """
    CREATE FUNCTION hc_analysis_set_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE keys text[];
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis sets are written only while the run is running');
        END IF;
        SELECT sensitivity_analysis_keys INTO keys FROM plan WHERE run_id = NEW.run_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('an analysis set needs a locked plan');
        END IF;
        IF NEW.key <> 'primary' AND NOT (NEW.key = ANY (keys)) THEN
            PERFORM hc_reject('the locked plan names no analysis ' || NEW.key);
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis sets cannot change after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_analysis_set_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; rr run_record;
    BEGIN
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF hc_lock_run(s.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis sets are written only while the run is running');
        END IF;
        IF hc_is_frozen(s.run_id) THEN
            PERFORM hc_reject('analysis sets cannot change after the dataset freeze');
        END IF;
        SELECT * INTO rr FROM run_record WHERE run_id = s.run_id AND record_id = NEW.record_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('a set holds only records the run has decided on');
        END IF;
        IF (SELECT kind FROM record WHERE id = NEW.record_id) = 'model_recalled' THEN
            PERFORM hc_reject('a model-recalled record is never in an analysis set');
        END IF;
        IF s.key = 'primary' AND rr.eligible IS NOT TRUE THEN
            PERFORM hc_reject('the primary set holds only eligible records');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Dataset freeze (PRD 5.6; review findings 2 and 3): every record of the run has a
    # decision; the primary set is exactly the records decided eligible; every named
    # sensitivity set exists; no "no dataset frozen" calibration was recorded.
    """
    CREATE FUNCTION hc_run_snapshot_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE keys text[]; primary_id bigint; primary_count int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a dataset is frozen only while its run is running');
        END IF;
        IF NEW.frozen_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('frozen_at is set by the database at the freeze');
        END IF;
        SELECT sensitivity_analysis_keys INTO keys FROM plan WHERE run_id = NEW.run_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('a dataset freeze needs a locked plan');
        END IF;
        IF EXISTS (SELECT 1 FROM calibration_result WHERE run_id = NEW.run_id AND analysis_result_id IS NULL) THEN
            PERFORM hc_reject('this run already recorded that no dataset was frozen');
        END IF;
        IF EXISTS (SELECT 1 FROM record r WHERE r.extraction_run_id = NEW.run_id
                     AND NOT EXISTS (SELECT 1 FROM run_record rr WHERE rr.run_id = NEW.run_id AND rr.record_id = r.id)) THEN
            PERFORM hc_reject('every record of the run needs an eligibility decision before the freeze');
        END IF;
        SELECT id INTO primary_id FROM analysis_set WHERE run_id = NEW.run_id AND key = 'primary';
        SELECT count(*) INTO primary_count FROM analysis_set_record WHERE analysis_set_id = primary_id;
        IF primary_count = 0 THEN
            PERFORM hc_reject('no eligible records: no dataset is frozen');
        END IF;
        IF EXISTS (SELECT 1 FROM run_record rr WHERE rr.run_id = NEW.run_id AND rr.eligible
                     AND NOT EXISTS (SELECT 1 FROM analysis_set_record sr
                                     WHERE sr.analysis_set_id = primary_id AND sr.record_id = rr.record_id)) THEN
            PERFORM hc_reject('the primary set must hold every record decided eligible');
        END IF;
        IF NEW.n_records <> primary_count THEN
            PERFORM hc_reject('n_records must equal the size of the primary set');
        END IF;
        IF EXISTS (SELECT 1 FROM unnest(keys) k WHERE NOT EXISTS (
                     SELECT 1 FROM analysis_set WHERE run_id = NEW.run_id AND key = k)) THEN
            PERFORM hc_reject('every sensitivity analysis named by the plan needs its set before the freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are raised only while the run is running');
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('flags cannot be added after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(OLD.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are classified only while the run is running');
        END IF;
        IF OLD.critic_class IS NOT NULL THEN
            PERFORM hc_reject('a flag is classified once');
        END IF;
        IF hc_is_frozen(OLD.run_id) THEN
            PERFORM hc_reject('flags cannot change after the dataset freeze');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.kind <> OLD.kind OR NEW.category <> OLD.category
           OR NEW.compared_values IS DISTINCT FROM OLD.compared_values OR NEW.raised_at <> OLD.raised_at THEN
            PERFORM hc_reject('only the Critic''s classification of a flag can be added');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE flag_run bigint;
    BEGIN
        SELECT run_id INTO flag_run FROM flag WHERE id = NEW.flag_id;
        IF hc_lock_run(flag_run) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are raised only while the run is running');
        END IF;
        IF (SELECT extraction_run_id FROM record WHERE id = NEW.record_id) IS DISTINCT FROM flag_run THEN
            PERFORM hc_reject('a flag names only records of its own run');
        END IF;
        IF hc_is_frozen(flag_run) THEN
            PERFORM hc_reject('flags cannot change after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Results (owner, addition 3; review finding 5): after the freeze, while running, on
    # the right set, with counts consistent with it. These are necessary conditions only.
    """
    CREATE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Calibration (PRD 5.10): computed exactly when inference is valid; otherwise the reason
    # matches. A run-level "no dataset frozen" row and a freeze exclude each other (finding 3).
    """
    CREATE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF (NEW.status = 'computed') <> a.check2_passed THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid');
        END IF;
        IF NEW.reason = 'coefficient_not_fitted' AND a.check1_passed
           OR NEW.reason = 'insufficient_groups' AND NOT (a.check1_passed AND NOT a.check2_passed) THEN
            PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_commentary_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'completed' THEN
            PERFORM hc_reject('commentary is written after the run is completed');
        END IF;
        IF (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) IS DISTINCT FROM 'commentator' THEN
            PERFORM hc_reject('commentary comes from the commentator stage');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_artifact_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF coalesce(hc_lock_run(NEW.run_id), '') NOT IN ('running', 'completed') THEN
            PERFORM hc_reject('artifacts are stored only for a running or completed run');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Stages: while running; after completion only the Commentator's stage.
    """
    CREATE FUNCTION hc_stage_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND NEW.stage = 'commentator'
                                              AND NEW.role IS NOT DISTINCT FROM 'commentator') THEN
            PERFORM hc_reject('a stage runs while the run is running; after completion only the commentator');
        END IF;
        IF NEW.status <> 'running' THEN
            PERFORM hc_reject('a stage result starts as running');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_stage_result_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND OLD.stage = 'commentator') THEN
            PERFORM hc_reject('a stage result changes only while its run is running');
        END IF;
        IF OLD.status <> 'running' THEN
            PERFORM hc_reject('a finished stage result is final');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage <> OLD.stage OR NEW.attempt <> OLD.attempt
           OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('the identity of a stage result cannot change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Model calls (owner, question 5; review finding 7): written before the request with
    # the database's time, finished exactly once with the database's time. After
    # completion only the Commentator's calls, which count in the run's totals.
    """
    CREATE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
            PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
        END IF;
        IF NEW.status <> 'started' THEN
            PERFORM hc_reject('a model call is recorded before the request, as started');
        END IF;
        IF NEW.started_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('started_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND OLD.role = 'commentator') THEN
            PERFORM hc_reject('a model call is finished only while its run is running');
        END IF;
        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
            PERFORM hc_reject('a model call is finished exactly once');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('what was recorded before the request cannot change');
        END IF;
        IF NEW.finished_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('finished_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """,
]

APPEND_ONLY = [
    "domain", "agent_setting", "source_file", "hypothesis", "plan", "run_tag",
    "run_agent_setting", "run_snapshot", "record", "run_record", "analysis_set", "analysis_set_record",
    "flag_record", "analysis_result", "calibration_result", "commentary", "artifact", "audit_log",
]
NO_DELETE = [
    "hypothesis_version", "run", "tag_value", "source", "source_version", "run_source", "stage_result",
    "model_call", "flag",
]
# (table, event, function)
CHECKED = [
    ("hypothesis", "INSERT", "hc_hypothesis_insert"),
    ("hypothesis_version", "INSERT", "hc_version_insert"),
    ("hypothesis_version", "UPDATE", "hc_version_update"),
    ("hypothesis_version_source", "INSERT OR UPDATE OR DELETE", "hc_version_source_change"),
    ("run", "INSERT", "hc_run_insert"),
    ("run", "UPDATE", "hc_run_update"),
    ("plan", "INSERT", "hc_plan_insert"),
    ("run_tag", "INSERT", "hc_run_tag_insert"),
    ("tag_value", "UPDATE", "hc_tag_value_update"),
    ("source", "UPDATE", "hc_source_update"),
    ("source_version", "INSERT", "hc_source_version_insert"),
    ("source_version", "UPDATE", "hc_source_version_update"),
    ("source_file", "INSERT", "hc_source_file_insert"),
    ("run_agent_setting", "INSERT", "hc_run_agent_setting_insert"),
    ("run_source", "INSERT", "hc_run_source_insert"),
    ("run_source", "UPDATE", "hc_run_source_update"),
    ("record", "INSERT", "hc_record_insert"),
    ("run_record", "INSERT", "hc_run_record_insert"),
    ("analysis_set", "INSERT", "hc_analysis_set_insert"),
    ("analysis_set_record", "INSERT", "hc_analysis_set_record_insert"),
    ("run_snapshot", "INSERT", "hc_run_snapshot_insert"),
    ("flag", "INSERT", "hc_flag_insert"),
    ("flag", "UPDATE", "hc_flag_update"),
    ("flag_record", "INSERT", "hc_flag_record_insert"),
    ("analysis_result", "INSERT", "hc_analysis_result_insert"),
    ("calibration_result", "INSERT", "hc_calibration_insert"),
    ("commentary", "INSERT", "hc_commentary_insert"),
    ("artifact", "INSERT", "hc_artifact_insert"),
    ("stage_result", "INSERT", "hc_stage_result_insert"),
    ("stage_result", "UPDATE", "hc_stage_result_update"),
    ("model_call", "INSERT", "hc_model_call_insert"),
    ("model_call", "UPDATE", "hc_model_call_update"),
]

TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_delete BEFORE DELETE ON {t} "
       f"FOR EACH ROW EXECUTE FUNCTION hc_no_delete()" for t in NO_DELETE]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_no_delete()" for t in NO_DELETE + ["hypothesis_version_source"]]
    + [f"CREATE TRIGGER {f} BEFORE {event} ON {t} FOR EACH ROW EXECUTE FUNCTION {f}()"
       for t, event, f in CHECKED]
)

# Totals are derived from model_call, never stored (owner, question 5). A call without
# reported cost counts at its upper bound max_cost toward cap_cost.
_TOTALS = """
    count(mc.id) AS calls,
    coalesce(sum(mc.input_tokens), 0) AS input_tokens,
    coalesce(sum(mc.output_tokens), 0) AS output_tokens,
    coalesce(sum(mc.cached_tokens), 0) AS cached_tokens,
    coalesce(sum(mc.cost), 0) AS reported_cost,
    count(mc.id) FILTER (WHERE mc.cost IS NULL) AS unconfirmed_calls,
    coalesce(sum(mc.max_cost) FILTER (WHERE mc.cost IS NULL), 0) AS unconfirmed_cost_bound,
    coalesce(sum(coalesce(mc.cost, mc.max_cost)), 0) AS cap_cost
"""


def _sources(condition: str) -> str:
    return (f"ARRAY(SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id "
            f"WHERE rs.run_id = r.id AND {condition} ORDER BY s.key)")


VIEW_NAMES = [
    "run_search_coverage",
    "model_call_totals_by_stage",
    "model_call_totals_by_run",
    "model_call_totals_by_query",
    "model_call_totals_by_month",
]

VIEWS = [
    # Review finding 6: every category is reported with its sources, never collapsed into
    # one label; coverage comes only from the run's own dispatch-time run_source rows.
    # A failed source is listed as failed and not searched, never as missing evidence.
    f"""
    CREATE VIEW run_search_coverage AS
    SELECT r.id AS run_id,
        {_sources("rs.search_status = 'searched'")} AS searched_sources,
        {_sources("rs.search_status <> 'searched'")} AS not_searched_sources,
        {_sources("rs.search_status = 'not_selected'")} AS not_selected_sources,
        {_sources("rs.search_status = 'failed'")} AS failed_search_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found IS NULL")} AS records_found_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found = 'missing_evidence'")} AS missing_evidence_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found = 'reported_negative'")} AS reported_negative_sources
    FROM run r
    """,
    f"""
    CREATE VIEW model_call_totals_by_stage AS
    SELECT sr.id AS stage_result_id, sr.run_id, sr.stage, sr.attempt, {_TOTALS}
    FROM stage_result sr LEFT JOIN model_call mc ON mc.stage_result_id = sr.id
    GROUP BY sr.id
    """,
    f"""
    CREATE VIEW model_call_totals_by_run AS
    SELECT r.id AS run_id, {_TOTALS}
    FROM run r LEFT JOIN model_call mc ON mc.run_id = r.id
    GROUP BY r.id
    """,
    f"""
    CREATE VIEW model_call_totals_by_query AS
    SELECT h.id AS hypothesis_id, h.number, {_TOTALS}
    FROM hypothesis h
    LEFT JOIN hypothesis_version hv ON hv.hypothesis_id = h.id
    LEFT JOIN run r ON r.hypothesis_version_id = hv.id
    LEFT JOIN model_call mc ON mc.run_id = r.id
    GROUP BY h.id
    """,
    # A call counts in the UTC month of its started_at, which the database sets.
    f"""
    CREATE VIEW model_call_totals_by_month AS
    SELECT date_trunc('month', mc.started_at AT TIME ZONE 'UTC') AS month_utc, {_TOTALS}
    FROM model_call mc
    GROUP BY 1
    """,
]

# PRD 5.5: the fixed list of domains. Tag lists are seeded in step 6 (PRD 17 #7 unconfirmed).
SEED = [
    """
    INSERT INTO domain (key, name, supported, profile_name) VALUES
        ('grain_size_strengthening', 'Grain-size strengthening', true, 'grain_size_strengthening'),
        ('fatigue', 'Fatigue', false, NULL),
        ('other', 'Other', false, NULL)
    """,
]
```

### `hypocurate/db/models.py`

SHA-256 `5181126940e217de284d1b373ac316c902777c3a420f53a5388e87307f54b5cc`, 39827 bytes.

```python
"""The tables of PRD Section 7 (build step 3), as decided with the owner on 2026-10-04/05.

The rules that protect the method are enforced in the database itself, by CHECK
constraints here and by triggers in the migration (`migrations/versions/0001_data_model.py`):
a locked plan cannot change; a frozen dataset cannot change; records are never
updated; stored is not analysed (`record` versus `run_record` and `analysis_set`);
a narrower question is a separate query linked to the run it narrows; every
model call has tokens and cost or counts at its upper bound.

Limitation, stated plainly: the triggers stop the application and ordinary edits.
The database owner can still drop a trigger; the fingerprints are the cross-check.

No table stores token or cost totals; the views `model_call_totals_by_*` sum
`model_call`. Search coverage and the kinds of "nothing found" are not stored per
run either; the view `run_search_coverage` reports them per source, from the run's
own dispatch-time `run_source` rows.

Locking protocol (review finding 1): every trigger that checks or changes a run's
state first locks that run's row (FOR NO KEY UPDATE); triggers on chosen sources and
on dispatch lock the hypothesis version first. Lock order: version, then run.

What the CHECKs on `analysis_result` establish (review finding 5): necessary
conditions on the stored counts only. The full validity rules of PRD 5.7 and the
agreement of the verdict with the pooled result are computed and tested in step 7.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Sequence,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy import text as sql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}

MAX_FILE_BYTES = 5 * 1024 * 1024  # owner decision, 2026-10-04: 5 MiB per stored file
ROLES = ("planner", "curator", "critic", "analyst", "commentator")
SHA256 = "~ '^[0-9a-f]{64}$'"


def one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def now():
    return sql("now()")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def pk() -> Mapped[int]:
    return mapped_column(BigInteger, Identity(), primary_key=True)


def created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=now())


# --- Fixed lists ---------------------------------------------------------------

class Domain(Base):
    """PRD 5.5. Seeded by the migration; append-only."""
    __tablename__ = "domain"
    id: Mapped[int] = pk()
    key: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    supported: Mapped[bool] = mapped_column(Boolean)
    profile_name: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("NOT supported OR profile_name IS NOT NULL", name="supported_has_profile"),
    )


TAG_KINDS = ("property", "alloy_class", "test_condition")
TAG_STATUSES = ("proposed", "approved", "rejected")


class TagValue(Base):
    """PRD 5.5: fixed lists. A value proposed by the Planner is approved or rejected once by a person."""
    __tablename__ = "tag_value"
    id: Mapped[int] = pk()
    kind: Mapped[str] = mapped_column(Text)
    value: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    proposed_by_run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
    created_at: Mapped[datetime] = created()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("kind", "value"),
        CheckConstraint(one_of("kind", TAG_KINDS), name="kind"),
        CheckConstraint(one_of("status", TAG_STATUSES), name="status"),
        CheckConstraint("length(value) > 0", name="value_not_empty"),
        CheckConstraint("(status = 'proposed') = (decided_at IS NULL)", name="decided_once"),
    )


# --- Sources -------------------------------------------------------------------

SOURCE_TYPES = ("uploaded_table", "web_interface", "paper_search", "model_recall")
DATA_KINDS = ("measured", "computed", "model_recalled")


class Source(Base):
    """A registered source (PRD 9.6). It is never deleted and its key never changes.
    `source_type`, `data_kind` and `grouping_unit` here are the settings for the next
    version: each version keeps its own copy (review finding 4). Operational settings
    (enabled, adapter status, address, licence, properties) may change."""
    __tablename__ = "source"
    id: Mapped[int] = pk()
    key: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    licence: Mapped[str] = mapped_column(Text)
    data_kind: Mapped[str] = mapped_column(Text)
    adapter_status: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean)
    # PRD 5.7: each source states its grouping unit (the paper, or the whole dataset).
    grouping_unit: Mapped[str] = mapped_column(Text)
    properties_covered: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=sql("'{}'"))
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        CheckConstraint("key ~ '^[a-z0-9_]+$'", name="key_format"),
        CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
        CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
        CheckConstraint(one_of("adapter_status", ("adapter_needed", "available")), name="adapter_status"),
        CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
    )


class SourceVersion(Base):
    """A snapshot of a source (review finding 4). It holds its own copy of the settings
    that change how records are read, copied from `source` at insert. Files are added,
    then the version is sealed once: the database sets `sealed_at` and checks that
    `fingerprint` is the SHA-256 of the sorted file list. Only a sealed version can be
    used by a run. Nothing changes after sealing; it is never deleted."""
    __tablename__ = "source_version"
    id: Mapped[int] = pk()
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    label: Mapped[str] = mapped_column(Text)
    obtained_on: Mapped[date] = mapped_column(Date)
    source_type: Mapped[str] = mapped_column(Text)
    data_kind: Mapped[str] = mapped_column(Text)
    grouping_unit: Mapped[str] = mapped_column(Text)
    sealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fingerprint: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("source_id", "fingerprint"),
        UniqueConstraint("id", "source_id"),
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint("(sealed_at IS NULL) = (fingerprint IS NULL)", name="sealed_with_fingerprint"),
        CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
        CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
        CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
    )


class SourceFile(Base):
    """A data file an adapter reads (owner decision: only data files, at most 5 MiB).
    Added only before its version is sealed. Append-only."""
    __tablename__ = "source_file"
    id: Mapped[int] = pk()
    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    __table_args__ = (
        UniqueConstraint("source_version_id", "path"),
        CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
        CheckConstraint(r"path ~ '\.(csv|xlsx)$'", name="data_file_type"),
        CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
    )


# --- Agent settings ------------------------------------------------------------

class AgentSetting(Base):
    """Versioned settings per role (PRD 9.5). Append-only: a change is a new version."""
    __tablename__ = "agent_setting"
    id: Mapped[int] = pk()
    role: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    limits: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    settings: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("role", "version"),
        UniqueConstraint("id", "role"),
        CheckConstraint(one_of("role", ROLES), name="role"),
        CheckConstraint("version >= 1", name="version_positive"),
    )


# --- Queries -------------------------------------------------------------------

HYPOTHESIS_NUMBER_SEQ = Sequence("hypothesis_number_seq", metadata=Base.metadata)


class Hypothesis(Base):
    """One row per query number. A narrower question is its own query, linked to the
    run whose outcome was partly sufficient (owner decision, question 1)."""
    __tablename__ = "hypothesis"
    id: Mapped[int] = pk()
    number: Mapped[str] = mapped_column(
        Text, unique=True,
        server_default=sql("'Q-' || lpad(nextval('hypothesis_number_seq')::text, 4, '0')"))
    narrower_of_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run.id", use_alter=True))
    created_at: Mapped[datetime] = created()


VERSION_STATUSES = ("draft", "submitted", "returned", "dispatched")


class HypothesisVersion(Base):
    """Each edit is a new version. Frozen once it leaves draft, except the review
    fields; everything is frozen once returned or dispatched."""
    __tablename__ = "hypothesis_version"
    id: Mapped[int] = pk()
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("hypothesis.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=sql("'draft'"))
    confirmed_domain_id: Mapped[int | None] = mapped_column(ForeignKey("domain.id"))
    domain_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("hypothesis_id", "version_number"),
        CheckConstraint(one_of("status", VERSION_STATUSES), name="status"),
        CheckConstraint("version_number >= 1", name="version_positive"),
        CheckConstraint("length(btrim(text)) > 0", name="text_not_empty"),
        CheckConstraint("(confirmed_domain_id IS NULL) = (domain_confirmed_at IS NULL)",
                        name="confirmed_domain_with_time"),
        CheckConstraint("status <> 'dispatched' OR (confirmed_domain_id IS NOT NULL AND dispatched_at IS NOT NULL)",
                        name="dispatch_needs_confirmed_domain"),
        CheckConstraint("status = 'draft' OR submitted_at IS NOT NULL", name="submitted_time"),
        CheckConstraint("status <> 'returned' OR returned_at IS NOT NULL", name="returned_time"),
    )


class HypothesisVersionSource(Base):
    """The sources chosen for a version. Changes only while the version is a draft."""
    __tablename__ = "hypothesis_version_source"
    hypothesis_version_id: Mapped[int] = mapped_column(ForeignKey("hypothesis_version.id"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), primary_key=True)


# --- Runs ----------------------------------------------------------------------

RUN_STATUSES = ("queued", "running", "completed", "failed")
OUTCOMES = ("sufficient", "partly_sufficient", "insufficient")
VERDICTS = ("supported", "not_supported")


class Run(Base):
    """One row per dispatch. Completed and failed are final.
    Verdict (owner decision, question 4): present if and only if the run completed as
    sufficient. Exploratory: only for a sufficient run under "use what is available"
    whose pooled data were below the plan's minimums (checked by trigger)."""
    __tablename__ = "run"
    id: Mapped[int] = pk()
    hypothesis_version_id: Mapped[int] = mapped_column(ForeignKey("hypothesis_version.id"))
    status: Mapped[str] = mapped_column(Text, server_default=sql("'queued'"))
    current_stage: Mapped[str | None] = mapped_column(Text)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str | None] = mapped_column(Text)
    exploratory: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
    fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
    experiment_flags: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint(one_of("status", RUN_STATUSES), name="status"),
        CheckConstraint(f"outcome IS NULL OR {one_of('outcome', OUTCOMES)}", name="outcome"),
        CheckConstraint(f"verdict IS NULL OR {one_of('verdict', VERDICTS)}", name="verdict"),
        CheckConstraint("agent_mode = 'four_roles'", name="agent_mode"),
        CheckConstraint("(outcome IS NOT NULL) = (status = 'completed')", name="outcome_iff_completed"),
        CheckConstraint(
            "(verdict IS NOT NULL) = (status = 'completed' AND outcome IS NOT DISTINCT FROM 'sufficient')",
            name="verdict_iff_sufficient"),
        CheckConstraint("NOT exploratory OR verdict IS NOT NULL", name="exploratory_needs_verdict"),
        CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
        CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
        CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
        CheckConstraint("status <> 'failed' OR failed_at IS NOT NULL", name="failed_time"),
    )


SUFFICIENCY_OPTIONS = ("fixed_minimum", "use_available")


class Plan(Base):
    """The locked plan (PRD 5.1, 5.6). Inserted at the rules lock, never changed.
    The columns the database checks against are explicit; the rest is `content`."""
    __tablename__ = "plan"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
    content: Mapped[dict] = mapped_column(JSONB)
    fingerprint: Mapped[str] = mapped_column(Text)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    sufficiency_option: Mapped[str] = mapped_column(Text)
    min_records: Mapped[int] = mapped_column(Integer)
    min_alloys: Mapped[int] = mapped_column(Integer)
    min_groups: Mapped[int] = mapped_column(Integer)
    min_resid_df: Mapped[int] = mapped_column(Integer)
    sensitivity_analysis_keys: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=sql("'{}'"))
    # Owner's addition 1: an information-only power report; never a gate, read by no constraint.
    power_assumptions: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint(one_of("sufficiency_option", SUFFICIENCY_OPTIONS), name="sufficiency_option"),
        CheckConstraint("min_records >= 1 AND min_alloys >= 1 AND min_groups >= 1 AND min_resid_df >= 1",
                        name="minimums_positive"),
        CheckConstraint("NOT ('primary' = ANY (sensitivity_analysis_keys))", name="primary_not_sensitivity"),
    )


class RunTag(Base):
    """Tags attached at the lock (PRD 5.5); written in the lock's transaction only."""
    __tablename__ = "run_tag"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    tag_value_id: Mapped[int] = mapped_column(ForeignKey("tag_value.id"), primary_key=True)


class RunAgentSetting(Base):
    """The agent settings version each role uses, recorded at dispatch (PRD 8)."""
    __tablename__ = "run_agent_setting"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    role: Mapped[str] = mapped_column(Text, primary_key=True)
    agent_setting_id: Mapped[int] = mapped_column(BigInteger)
    __table_args__ = (
        ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
                             name="fk_run_agent_setting_agent_setting"),
    )


SEARCH_STATUSES = ("not_selected", "pending", "searched", "failed")
NOTHING_FOUND = ("reported_negative", "missing_evidence", "failed_search")


class RunSource(Base):
    """Per run and source: what was searched, and the kind of "nothing found"
    (owner decision, question 3). Coverage and the kinds of "nothing found" are reported
    per source by the view run_search_coverage, from these dispatch-time rows only
    (review finding 6). A run starts only when every source registered at dispatch has a row."""
    __tablename__ = "run_source"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), primary_key=True)
    source_version_id: Mapped[int | None] = mapped_column(BigInteger)
    search_status: Mapped[str] = mapped_column(Text)
    nothing_found: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["source_version_id", "source_id"], ["source_version.id", "source_version.source_id"],
                             name="fk_run_source_source_version"),
        CheckConstraint(one_of("search_status", SEARCH_STATUSES), name="search_status"),
        CheckConstraint(f"nothing_found IS NULL OR {one_of('nothing_found', NOTHING_FOUND)}", name="nothing_found"),
        CheckConstraint("(search_status = 'failed') = (nothing_found IS NOT DISTINCT FROM 'failed_search')",
                        name="failed_iff_failed_search"),
        CheckConstraint("search_status NOT IN ('not_selected', 'pending') OR nothing_found IS NULL",
                        name="undecided_has_no_kind"),
        CheckConstraint("search_status <> 'failed' OR failure_reason IS NOT NULL", name="failed_has_reason"),
        CheckConstraint("search_status <> 'not_selected' OR source_version_id IS NULL", name="not_selected_no_version"),
        CheckConstraint("search_status <> 'searched' OR source_version_id IS NOT NULL", name="searched_has_version"),
        CheckConstraint("(search_status IN ('searched', 'failed')) = (decided_at IS NOT NULL)", name="decided_time"),
    )


class RunSnapshot(Base):
    """The dataset freeze (PRD 5.6): fingerprint and time. Append-only."""
    __tablename__ = "run_snapshot"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(Text)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    n_records: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint("n_records >= 1", name="not_empty"),
    )


STAGE_STATUSES = ("running", "done", "failed", "skipped")


class StageResult(Base):
    """Per stage and attempt: input, output, reasoning, tool calls, model, times.
    Token and cost totals come from the view model_call_totals_by_stage."""
    __tablename__ = "stage_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    stage: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, server_default=sql("1"))
    role: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=sql("'running'"))
    input: Mapped[dict | None] = mapped_column(JSONB)
    output: Mapped[dict | None] = mapped_column(JSONB)
    reasoning: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    agent_setting_id: Mapped[int | None] = mapped_column(ForeignKey("agent_setting.id"))
    model: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("run_id", "stage", "attempt"),
        UniqueConstraint("id", "run_id"),
        CheckConstraint("stage ~ '^[a-z_]+$'", name="stage_format"),
        CheckConstraint("attempt >= 1", name="attempt_positive"),
        CheckConstraint(f"role IS NULL OR {one_of('role', ROLES)}", name="role"),
        CheckConstraint(one_of("status", STAGE_STATUSES), name="status"),
        CheckConstraint("(status = 'running') = (finished_at IS NULL)", name="finished_time"),
    )


CALL_STATUSES = ("started", "succeeded", "failed", "interrupted")
USAGE = ("input_tokens", "output_tokens", "cached_tokens", "cost")


def _all(cond: str) -> str:
    return " AND ".join(f"{c} {cond}" for c in USAGE)


class ModelCall(Base):
    """One row per model call (owner decision, question 5), written BEFORE the request
    with its upper bound `max_cost`, then finished exactly once. A call without
    reported cost counts at `max_cost` toward totals and caps. `started_at` and
    `finished_at` are the database's transaction times (review finding 7)."""
    __tablename__ = "model_call"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(BigInteger)
    stage_result_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    price_table_version: Mapped[str] = mapped_column(Text)
    # numeric with no fixed scale: stored exactly, so no amount rounds (review finding 7)
    max_cost: Mapped[Decimal] = mapped_column(Numeric())
    status: Mapped[str] = mapped_column(Text, server_default=sql("'started'"))
    input_tokens: Mapped[int | None] = mapped_column(BigInteger)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cached_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cost: Mapped[Decimal | None] = mapped_column(Numeric())
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                             name="fk_model_call_stage_result"),
        Index("ix_model_call_run_id", "run_id"),
        CheckConstraint(one_of("role", ROLES), name="role"),
        CheckConstraint(one_of("status", CALL_STATUSES), name="status"),
        CheckConstraint("length(model) > 0 AND length(price_table_version) > 0", name="model_and_prices_named"),
        CheckConstraint("max_cost > 0", name="max_cost_positive"),
        CheckConstraint(" AND ".join(f"coalesce({c}, 0) >= 0" for c in USAGE), name="usage_not_negative"),
        CheckConstraint(f"status <> 'started' OR ({_all('IS NULL')} AND finished_at IS NULL)",
                        name="started_has_no_usage"),
        CheckConstraint(f"status <> 'succeeded' OR ({_all('IS NOT NULL')} AND finished_at IS NOT NULL)",
                        name="succeeded_has_usage"),
        CheckConstraint(f"status <> 'failed' OR (finished_at IS NOT NULL AND (({_all('IS NULL')}) "
                        f"OR ({_all('IS NOT NULL')})))", name="failed_usage_all_or_none"),
        CheckConstraint(f"status <> 'interrupted' OR ({_all('IS NULL')} AND finished_at IS NOT NULL)",
                        name="interrupted_has_no_usage"),
    )


# --- Records: stored is not analysed ------------------------------------------------

class Record(Base):
    """One observation, extracted in one run (owner decision, question 7). Append-only.
    `source_item_key` identifies the row or item of the source version it came from,
    so the same source row can be matched across runs."""
    __tablename__ = "record"
    id: Mapped[int] = pk()
    extraction_run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
    source_item_key: Mapped[str] = mapped_column(Text)
    item_index: Mapped[int] = mapped_column(Integer, server_default=sql("0"))
    kind: Mapped[str] = mapped_column(Text)
    alloy: Mapped[str | None] = mapped_column(Text)
    harmonized: Mapped[dict] = mapped_column(JSONB)
    reported: Mapped[dict] = mapped_column(JSONB)
    paper_reference: Mapped[str | None] = mapped_column(Text)
    paper_doi: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("extraction_run_id", "source_version_id", "source_item_key", "item_index",
                         name="uq_record_origin_per_run"),
        Index("ix_record_source_version_id_source_item_key", "source_version_id", "source_item_key"),
        CheckConstraint(one_of("kind", DATA_KINDS), name="kind"),
        CheckConstraint("length(source_item_key) > 0", name="item_key_not_empty"),
        CheckConstraint("item_index >= 0", name="item_index_not_negative"),
    )


class RunRecord(Base):
    """For each run and record: eligible for the primary analysis or not, and the rule
    that decided it (PRD 5.3). Written by code under the locked plan, before the freeze.
    At the freeze every record of the run must have a decision, and the primary set must
    be exactly the records decided eligible (review finding 2). A duplicate's
    non-surviving copy carries its own decision (eligible = false, "counted once")."""
    __tablename__ = "run_record"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)
    eligible: Mapped[bool] = mapped_column(Boolean)
    rule: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = created()
    __table_args__ = (CheckConstraint("length(rule) > 0", name="rule_named"),)


class AnalysisSet(Base):
    """A frozen record set: 'primary', or a sensitivity analysis named by the locked
    plan (owner decision, question 2)."""
    __tablename__ = "analysis_set"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    key: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("run_id", "key"),
        UniqueConstraint("id", "run_id"),
        CheckConstraint("key ~ '^[a-z0-9_]+$'", name="key_format"),
    )


class AnalysisSetRecord(Base):
    __tablename__ = "analysis_set_record"
    analysis_set_id: Mapped[int] = mapped_column(ForeignKey("analysis_set.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)


class Flag(Base):
    """A flag raised by code. `compared_values` is kept for audit; the access layer
    (step 5) never returns it to the Critic. The Critic's class is set once, before the freeze."""
    __tablename__ = "flag"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    kind: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    compared_values: Mapped[dict | None] = mapped_column(JSONB)
    raised_at: Mapped[datetime] = created()
    critic_class: Mapped[str | None] = mapped_column(Text)
    critic_reason: Mapped[str | None] = mapped_column(Text)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("(critic_class IS NULL) = (classified_at IS NULL)", name="classified_time"),
    )


class FlagRecord(Base):
    __tablename__ = "flag_record"
    flag_id: Mapped[int] = mapped_column(ForeignKey("flag.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)


# --- Results -------------------------------------------------------------------

SCOPES = ("pooled", "per_source", "sensitivity")
LABELS = ("agrees", "conflicts", "not_enough_data")


class AnalysisResult(Base):
    """One row per analysis and scope (owner's addition 3).
    The CHECKs below are necessary conditions on the stored counts, not the full
    validity rules of PRD 5.7 (review finding 5): the database cannot see whether an
    alloy was measured at two distinct grain sizes, nor recount alloys and groups.
    Those, and the agreement of the verdict with the pooled result, are computed and
    tested in step 7."""
    __tablename__ = "analysis_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(BigInteger)
    scope: Mapped[str] = mapped_column(Text)
    analysis_set_id: Mapped[int] = mapped_column(BigInteger)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"))
    n_records: Mapped[int] = mapped_column(Integer)
    n_alloys: Mapped[int] = mapped_column(Integer)
    n_groups: Mapped[int] = mapped_column(Integer)
    resid_df: Mapped[int] = mapped_column(Integer)
    check1_passed: Mapped[bool] = mapped_column(Boolean)
    check2_passed: Mapped[bool] = mapped_column(Boolean)
    minimums_met: Mapped[bool] = mapped_column(Boolean)
    estimate: Mapped[float | None] = mapped_column(Double)
    std_error: Mapped[float | None] = mapped_column(Double)
    p_value: Mapped[float | None] = mapped_column(Double)
    estimated_power: Mapped[float | None] = mapped_column(Double)
    label: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        ForeignKeyConstraint(["analysis_set_id", "run_id"], ["analysis_set.id", "analysis_set.run_id"],
                             name="fk_analysis_result_analysis_set"),
        UniqueConstraint("id", "run_id"),
        Index("uq_analysis_result_scope", "run_id", "scope", "analysis_set_id", "source_id",
              unique=True, postgresql_nulls_not_distinct=True),
        CheckConstraint(one_of("scope", SCOPES), name="scope"),
        CheckConstraint("(scope = 'per_source') = (source_id IS NOT NULL)", name="source_iff_per_source"),
        CheckConstraint(f"label IS NULL OR {one_of('label', LABELS)}", name="label"),
        CheckConstraint("n_records >= 0 AND n_alloys >= 0 AND n_groups >= 0", name="counts_not_negative"),
        # Each counted alloy has records at two or more grain sizes, so at least two records.
        CheckConstraint("n_records >= 2 * n_alloys", name="two_records_per_alloy"),
        CheckConstraint("n_groups <= n_records", name="groups_within_records"),
        CheckConstraint("n_records = 0 OR n_groups >= 1", name="records_have_a_group"),
        CheckConstraint("resid_df = n_records - n_alloys - 1", name="resid_df_definition"),
        CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_consistent"),
        CheckConstraint("check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)",
                        name="check2_consistent"),
        CheckConstraint("check1_passed = (estimate IS NOT NULL)", name="estimate_iff_check1"),
        CheckConstraint("check2_passed = (std_error IS NOT NULL)", name="std_error_iff_check2"),
        CheckConstraint("check2_passed = (p_value IS NOT NULL)", name="p_value_iff_check2"),
        CheckConstraint("std_error IS NULL OR std_error >= 0", name="std_error_not_negative"),
        CheckConstraint("p_value IS NULL OR p_value BETWEEN 0 AND 1", name="p_value_range"),
        CheckConstraint("estimated_power IS NULL OR estimated_power BETWEEN 0 AND 1", name="power_range"),
    )


CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups")
CALIBRATION_NUMBERS = ("assumptions", "n_simulations", "seed", "null_share", "null_ci_low", "null_ci_high",
                       "effect_share", "effect_ci_low", "effect_ci_high", "confidence_flag")


class CalibrationResult(Base):
    """PRD 5.10, for a run (analysis_result_id NULL) and for each analysis. A flag, not a gate."""
    __tablename__ = "calibration_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    analysis_result_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict | None] = mapped_column(JSONB)
    n_simulations: Mapped[int | None] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(BigInteger)
    null_share: Mapped[float | None] = mapped_column(Double)
    null_ci_low: Mapped[float | None] = mapped_column(Double)
    null_ci_high: Mapped[float | None] = mapped_column(Double)
    effect_share: Mapped[float | None] = mapped_column(Double)
    effect_ci_low: Mapped[float | None] = mapped_column(Double)
    effect_ci_high: Mapped[float | None] = mapped_column(Double)
    confidence_flag: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        ForeignKeyConstraint(["analysis_result_id", "run_id"], ["analysis_result.id", "analysis_result.run_id"],
                             name="fk_calibration_result_analysis_result"),
        Index("uq_calibration_result_scope", "run_id", "analysis_result_id",
              unique=True, postgresql_nulls_not_distinct=True),
        CheckConstraint(one_of("status", ("computed", "unavailable")), name="status"),
        CheckConstraint(f"reason IS NULL OR {one_of('reason', CALIBRATION_REASONS)}", name="reason"),
        CheckConstraint("confidence_flag IS NULL OR "
                        + one_of("confidence_flag", ("none", "over_confident", "under_confident")),
                        name="confidence_flag"),
        CheckConstraint("status <> 'computed' OR (reason IS NULL AND "
                        + " AND ".join(f"{c} IS NOT NULL" for c in CALIBRATION_NUMBERS) + ")",
                        name="computed_is_complete"),
        CheckConstraint("status <> 'unavailable' OR (reason IS NOT NULL AND "
                        + " AND ".join(f"{c} IS NULL" for c in CALIBRATION_NUMBERS) + ")",
                        name="unavailable_has_reason_only"),
        # Calibration attaches to an analysis; a run-level row exists only when no dataset was frozen.
        CheckConstraint("(analysis_result_id IS NULL) = (reason IS NOT DISTINCT FROM 'no_dataset_frozen')",
                        name="run_level_only_without_freeze"),
        CheckConstraint("n_simulations IS NULL OR n_simulations >= 1", name="simulations_positive"),
        CheckConstraint("null_share IS NULL OR (0 <= null_ci_low AND null_ci_low <= null_share "
                        "AND null_share <= null_ci_high AND null_ci_high <= 1)", name="null_interval"),
        CheckConstraint("effect_share IS NULL OR (0 <= effect_ci_low AND effect_ci_low <= effect_share "
                        "AND effect_share <= effect_ci_high AND effect_ci_high <= 1)", name="effect_interval"),
    )


class Commentary(Base):
    """The Commentator's text (PRD 5.9). Tokens and cost come from its stage's model calls."""
    __tablename__ = "commentary"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
    stage_result_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    number_check: Mapped[str | None] = mapped_column(Text)
    mismatches: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                             name="fk_commentary_stage_result"),
        CheckConstraint(one_of("status", ("written", "unavailable")), name="status"),
        CheckConstraint("(status = 'written') = (text IS NOT NULL AND number_check IS NOT NULL)",
                        name="written_has_text_and_check"),
        CheckConstraint("number_check IS NULL OR " + one_of("number_check", ("all_match", "mismatches")),
                        name="number_check"),
        CheckConstraint("(number_check IS NOT DISTINCT FROM 'mismatches') = (mismatches IS NOT NULL)",
                        name="mismatches_listed"),
    )


class Artifact(Base):
    """Plots and workbooks for a run (at most 5 MiB each), written while the run is
    running or after it completed, never for a failed run. Append-only."""
    __tablename__ = "artifact"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    kind: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        CheckConstraint(one_of("kind", ("plot", "workbook", "csv")), name="kind"),
        CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
        CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
    )


class AuditLog(Base):
    """Every data read and every denied call (PRD 4). Append-only. Written by the
    access layer (step 5)."""
    __tablename__ = "audit_log"
    id: Mapped[int] = pk()
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
    role: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text)
    function: Mapped[str] = mapped_column(Text)
    allowed: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (Index("ix_audit_log_run_id", "run_id"),)
```

### `tests/model_builder.py`

SHA-256 `6f8ad547744ceef68eef9fc46381e539b3d33ee1a9f70424d6ca9d56df4451dc`, 12103 bytes.

```python
"""Builds rows through the real lifecycle, in plain SQL, one transaction per step,
so the step 3 tests exercise the database rules exactly as later code will meet them."""
from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

FP = "0" * 64  # a well-formed fingerprint


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_fingerprint(files: dict[str, bytes]) -> str:
    """A source version's fingerprint (owner, 2026-10-05): SHA-256 of one line
    "<sha256>  <path>\\n" per file, sorted by path (the sha256sum format)."""
    listing = "".join(f"{sha(files[path])}  {path}\n" for path in sorted(files))
    return sha(listing.encode())


class World:
    def __init__(self, engine):
        self.e = engine
        self.domain = {k: v for k, v in self.rows("SELECT key, id FROM domain")}
        self.source = {}
        self.version = {}
        for key, unit in (("mpea", "paper"), ("tamu_fcc", "dataset")):
            self.add_source(key, grouping_unit=unit)

    def add_source(self, key, data_kind="measured", source_type="uploaded_table", grouping_unit="paper"):
        """Registers a source with one sealed version holding one data file."""
        self.source[key] = self.val(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES (:k, :k, :t, 'test', :d, 'available', true, :u) RETURNING id",
            k=key, t=source_type, d=data_kind, u=grouping_unit)
        self.version[key] = self.new_version(key)
        self.add_file(self.version[key], f"{key}.csv", f"{key},data\n".encode())
        self.seal(self.version[key])
        return self.source[key]

    def new_version(self, key, label="v1"):
        return self.val("INSERT INTO source_version (source_id, label, obtained_on) "
                        "VALUES (:s, :l, '2026-10-04') RETURNING id", s=self.source[key], l=label)

    def add_file(self, version, path, content):
        self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)",
                     v=version, p=path, h=sha(content), c=content)

    def files(self, version):
        return {p: bytes(c) for p, c in self.rows(
            "SELECT path, content FROM source_file WHERE source_version_id = :v", v=version)}

    def seal(self, version, fingerprint=None):
        fingerprint = fingerprint or files_fingerprint(self.files(version))
        self.run_sql("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                     v=version, fp=fingerprint)

    # --- plumbing ---------------------------------------------------------------------
    def run_sql(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params)

    def val(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params).scalar()

    def rows(self, sql, **params):
        with self.e.begin() as conn:
            return conn.execute(text(sql), params).all()

    def rejected(self, sql, match, **params):
        """The statement is refused by the database with a message matching `match`."""
        with pytest.raises(IntegrityError, match=match):
            self.run_sql(sql, **params)

    # --- queries ----------------------------------------------------------------------
    def hypothesis(self, narrower_of=None):
        return self.val("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id", r=narrower_of)

    def draft(self, hypothesis=None, number=1, domain="grain_size_strengthening", sources=("mpea", "tamu_fcc")):
        hypothesis = hypothesis or self.hypothesis()
        vid = self.val(
            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
            "VALUES (:h, :n, 'Yield strength rises as grain size falls', :d) RETURNING id",
            h=hypothesis, n=number, d=self.domain[domain])
        for s in sources:
            self.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=self.source[s])
        return vid

    def submit(self, vid):
        self.run_sql("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)

    def confirm(self, vid, domain="grain_size_strengthening"):
        self.run_sql("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() "
                     "WHERE id = :v", v=vid, d=self.domain[domain])

    def dispatch_version(self, vid):
        self.run_sql("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)

    def dispatched(self, **kw):
        vid = self.draft(**kw)
        self.submit(vid)
        self.confirm(vid, kw.get("domain", "grain_size_strengthening"))
        self.dispatch_version(vid)
        return vid

    # --- runs -------------------------------------------------------------------------
    def run(self, vid=None, sources=("mpea", "tamu_fcc")):
        """Dispatch: a queued run with a run_source row for every registered source."""
        vid = vid or self.dispatched()
        rid = self.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
        for key in self.source:
            if key in sources:
                self.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                             "VALUES (:r, :s, :sv, 'pending')", r=rid, s=self.source[key], sv=self.version[key])
            else:
                self.run_sql("INSERT INTO run_source (run_id, source_id, search_status) "
                             "VALUES (:r, :s, 'not_selected')", r=rid, s=self.source[key])
        return rid

    def start(self, rid):
        self.run_sql("UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)

    def running(self, **kw):
        rid = self.run(**kw)
        self.start(rid)
        return rid

    def locked(self, **kw):
        """A running run whose rules are locked: records may now be extracted."""
        rid = self.running(**kw)
        self.lock(rid)
        return rid

    def lock(self, rid, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1), tags=()):
        """The rules lock, in one transaction with its tags."""
        with self.e.begin() as conn:
            pid = conn.execute(text(
                "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
                "min_groups, min_resid_df, sensitivity_analysis_keys) "
                "VALUES (:r, '{}', :fp, :o, :a, :b, :c, :d, :k) RETURNING id"),
                dict(r=rid, fp=FP, o=option, a=mins[0], b=mins[1], c=mins[2], d=mins[3], k=list(keys))).scalar()
            for tag in tags:
                conn.execute(text("INSERT INTO run_tag VALUES (:r, :t)"), dict(r=rid, t=tag))
        return pid

    def search(self, rid, source="mpea", status="searched", nothing_found=None, reason=None):
        self.run_sql("UPDATE run_source SET search_status = :st, nothing_found = :nf, failure_reason = :fr, "
                     "decided_at = now() WHERE run_id = :r AND source_id = :s",
                     st=status, nf=nothing_found, fr=reason, r=rid, s=self.source[source])

    def record(self, rid, source="mpea", key="row-1", kind=None, index=0):
        kind = kind or self.val("SELECT data_kind FROM source_version WHERE id = :v", v=self.version[source])
        return self.val(
            "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, "
            "alloy, harmonized, reported) VALUES (:r, :sv, :k, :i, :kind, 'CoCrNi', '{}', '{}') RETURNING id",
            r=rid, sv=self.version[source], k=key, i=index, kind=kind)

    def decide(self, rid, rec, eligible=True, rule="in_scope"):
        self.run_sql("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)",
                     r=rid, c=rec, e=eligible, u=rule)

    def analysis_set(self, rid, key="primary"):
        return self.val("INSERT INTO analysis_set (run_id, key) VALUES (:r, :k) RETURNING id", r=rid, k=key)

    def add(self, set_id, rec):
        self.run_sql("INSERT INTO analysis_set_record VALUES (:s, :c)", s=set_id, c=rec)

    def freeze(self, rid, n):
        self.run_sql("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)",
                     r=rid, fp=FP, n=n)

    def frozen(self, n=4, per_source=None, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1)):
        """A running run, locked and frozen, with n eligible records in its primary set.
        per_source: {"mpea": 3, "tamu_fcc": 1}; default: all from MPEA."""
        per_source = per_source or {"mpea": n}
        rid = self.running()
        self.lock(rid, option=option, keys=keys, mins=mins)
        primary = self.analysis_set(rid)
        recs = []
        for source, count in per_source.items():
            self.search(rid, source)
            for i in range(count):
                rec = self.record(rid, source=source, key=f"{source}-{i}")
                self.decide(rid, rec)
                self.add(primary, rec)
                recs.append(rec)
        sets = {"primary": primary}
        for k in keys:
            sets[k] = self.analysis_set(rid, k)
        self.freeze(rid, sum(per_source.values()))
        return rid, sets, recs

    def result(self, rid, set_id, scope="pooled", n=4, alloys=1, groups=2, source=None, minimums_met=None,
               mins=(4, 1, 2, 1)):
        """An analysis result whose fields follow the validity-check definitions."""
        resid = n - alloys - 1
        check1 = alloys >= 1
        check2 = check1 and resid >= 1 and groups >= 2
        if minimums_met is None:
            minimums_met = n >= mins[0] and alloys >= mins[1] and groups >= mins[2] and resid >= mins[3]
        return self.val(
            "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, "
            "resid_df, check1_passed, check2_passed, minimums_met, estimate, std_error, p_value) "
            "VALUES (:r, :sc, :s, :src, :n, :a, :g, :df, :c1, :c2, :mm, :est, :se, :p) RETURNING id",
            r=rid, sc=scope, s=set_id, src=self.source[source] if source else None, n=n, a=alloys, g=groups,
            df=resid, c1=check1, c2=check2, mm=minimums_met, est=428.0 if check1 else None,
            se=64.0 if check2 else None, p=1e-6 if check2 else None)

    def complete(self, rid, outcome, verdict=None, exploratory=False):
        self.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
                     "exploratory = :x WHERE id = :r", o=outcome, v=verdict, x=exploratory, r=rid)

    def fail(self, rid, reason="worker stopped"):
        self.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r",
                     f=reason, r=rid)

    def stage(self, rid, stage="planner", role="planner", attempt=1):
        return self.val("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :o, :a) RETURNING id",
                        r=rid, s=stage, o=role, a=attempt)

    def call(self, rid, stage_id, max_cost=0.5, role="planner"):
        return self.val(
            "INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
            "VALUES (:r, :s, :o, 'model-a', 'prices-2026-10', :m) RETURNING id",
            r=rid, s=stage_id, o=role, m=max_cost)

    def finish_call(self, call_id, status="succeeded", usage=(1000, 200, 0, 0.01)):
        i, o, c, cost = usage if usage else (None, None, None, None)
        self.run_sql("UPDATE model_call SET status = :st, input_tokens = :i, output_tokens = :o, "
                     "cached_tokens = :c, cost = :cost, finished_at = now() WHERE id = :id",
                     st=status, i=i, o=o, c=c, cost=cost, id=call_id)
```

### `tests/test_concurrency.py`

SHA-256 `93924a104a618b61becbfb5f97b34a395210cfe5b841e51b624e33b2f16c0acd`, 10168 bytes.

```python
"""Step 3 fix, review finding 1: the locking protocol, shown with two connections.

In each test, transaction A does its write and stays open. Transaction B starts in a
thread and must wait on A's lock (checked in pg_stat_activity). A then commits, and B
either sees A's committed write (serialized) or is rejected. Every race the review
describes is run in both orders."""
import threading
import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from model_builder import FP, World, files_fingerprint, sha


@pytest.fixture
def w(db):
    return World(db)


def waiting_on_a_lock(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
            "AND wait_event_type = 'Lock' AND state = 'active'")).scalar()


def race(engine, first: str, second: str, first_params=None, second_params=None):
    """Runs `first` in an open transaction A, then `second` in transaction B in a thread.
    Asserts that B waited on A's lock, commits A, and returns B's error (or None)."""
    outcome = {}

    def run_second():
        try:
            with engine.begin() as b:
                b.execute(text(second), second_params or {})
            outcome["error"] = None
        except Exception as error:  # reported to the test below
            outcome["error"] = error

    with engine.connect() as a:
        tx = a.begin()
        a.execute(text(first), first_params or {})
        thread = threading.Thread(target=run_second)
        thread.start()
        deadline = time.monotonic() + 10
        while waiting_on_a_lock(engine) == 0 and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert thread.is_alive() and waiting_on_a_lock(engine) == 1, "B should be waiting on A's lock"
        tx.commit()
    thread.join(30)
    assert not thread.is_alive()
    return outcome["error"]


def rejected(error, match):
    assert isinstance(error, IntegrityError), error
    assert match in str(error), str(error)


# --- primary-set member against the dataset freeze ---------------------------------------------------

def set_up_freeze(w):
    """A locked run with two eligible records: one already in primary, one not yet."""
    rid = w.locked()
    first, second = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, first)
    w.decide(rid, second)
    primary = w.analysis_set(rid)
    w.add(primary, first)
    return rid, primary, second


def test_member_first_then_freeze_counts_it(w):
    rid, primary, second = set_up_freeze(w)
    error = race(w.e, "INSERT INTO analysis_set_record VALUES (:s, :c)",
                 "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 2)",
                 dict(s=primary, c=second), dict(r=rid, fp=FP))
    assert error is None  # the freeze waited and saw both members
    assert w.val("SELECT n_records FROM run_snapshot WHERE run_id = :r", r=rid) == 2


def test_freeze_first_then_flag_is_rejected(w):
    rid = w.locked()
    first = w.record(rid, key="a")
    w.decide(rid, first)
    w.add(w.analysis_set(rid), first)
    late = w.record(rid, key="b")
    w.decide(rid, late, eligible=False, rule="out of scope")
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
                 dict(r=rid, fp=FP), dict(r=rid))
    rejected(error, "after the dataset freeze")


def test_freeze_first_then_sensitivity_member_is_rejected(w):
    rid = w.running()
    w.lock(rid, keys=["scope_not_confirmed"])
    first, other = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, first)
    w.decide(rid, other, eligible=False, rule="scope not confirmed")
    w.add(w.analysis_set(rid), first)
    sensitivity = w.analysis_set(rid, "scope_not_confirmed")
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 "INSERT INTO analysis_set_record VALUES (:s, :c)",
                 dict(r=rid, fp=FP), dict(s=sensitivity, c=other))
    rejected(error, "after the dataset freeze")
    assert w.val("SELECT count(*) FROM analysis_set_record WHERE analysis_set_id = :s", s=sensitivity) == 0


# --- chosen sources against submission ----------------------------------------------------------------

def test_source_first_then_submission_includes_it(w):
    vid = w.draft(sources=("mpea",))
    error = race(w.e, "INSERT INTO hypothesis_version_source VALUES (:v, :s)",
                 "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v",
                 dict(v=vid, s=w.source["tamu_fcc"]), dict(v=vid))
    assert error is None
    assert w.val("SELECT count(*) FROM hypothesis_version_source WHERE hypothesis_version_id = :v", v=vid) == 2


def test_submission_first_then_source_is_rejected(w):
    vid = w.draft(sources=("mpea",))
    error = race(w.e, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v",
                 "INSERT INTO hypothesis_version_source VALUES (:v, :s)",
                 dict(v=vid), dict(v=vid, s=w.source["tamu_fcc"]))
    rejected(error, "only while the version is a draft")
    assert w.val("SELECT count(*) FROM hypothesis_version_source WHERE hypothesis_version_id = :v", v=vid) == 1


# --- dispatch metadata against starting the run ---------------------------------------------------------

def agent_setting(w):
    return w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 1, 'i', 'm') "
                 "RETURNING id")


def test_dispatch_metadata_first_then_start_waits(w):
    setting, rid = agent_setting(w), w.run()
    error = race(w.e, "INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)",
                 "UPDATE run SET status = 'running', started_at = now() WHERE id = :r",
                 dict(r=rid, s=setting), dict(r=rid))
    assert error is None
    assert w.val("SELECT count(*) FROM run_agent_setting WHERE run_id = :r", r=rid) == 1


def test_start_first_then_dispatch_metadata_is_rejected(w):
    setting, rid = agent_setting(w), w.run()
    error = race(w.e, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r",
                 "INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)",
                 dict(r=rid), dict(r=rid, s=setting))
    rejected(error, "recorded at dispatch")


# --- a child write against completion ----------------------------------------------------------------------

COMPLETE = "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r"


def test_flag_first_then_completion_waits(w):
    rid = w.running()
    error = race(w.e, "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')", COMPLETE,
                 dict(r=rid), dict(r=rid))
    assert error is None
    assert w.val("SELECT count(*) FROM flag WHERE run_id = :r", r=rid) == 1


def test_completion_first_then_flag_is_rejected(w):
    rid = w.running()
    error = race(w.e, COMPLETE, "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
                 dict(r=rid), dict(r=rid))
    rejected(error, "only while the run is running")


def test_completion_first_then_search_result_is_rejected(w):
    rid = w.running()
    error = race(w.e, COMPLETE, "UPDATE run_source SET search_status = 'searched', decided_at = now() "
                                "WHERE run_id = :r AND source_id = :s",
                 dict(r=rid), dict(r=rid, s=w.source["mpea"]))
    rejected(error, "only while the run is running")
    assert w.val("SELECT search_status FROM run_source WHERE run_id = :r AND source_id = :s",
                 r=rid, s=w.source["mpea"]) == "pending"


# --- "no dataset frozen" against the freeze -------------------------------------------------------------------

NO_DATASET = ("INSERT INTO calibration_result (run_id, status, reason) "
              "VALUES (:r, 'unavailable', 'no_dataset_frozen')")


def ready_to_freeze(w):
    rid = w.locked()
    rec = w.record(rid)
    w.decide(rid, rec)
    w.add(w.analysis_set(rid), rec)
    return rid


def test_no_dataset_first_then_freeze_is_rejected(w):
    rid = ready_to_freeze(w)
    error = race(w.e, NO_DATASET, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
                 dict(r=rid), dict(r=rid, fp=FP))
    rejected(error, "already recorded that no dataset was frozen")


def test_freeze_first_then_no_dataset_is_rejected(w):
    rid = ready_to_freeze(w)
    error = race(w.e, "INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)", NO_DATASET,
                 dict(r=rid, fp=FP), dict(r=rid))
    rejected(error, "calibration is reported per analysis")


# --- a source file against sealing its version --------------------------------------------------------------------

def test_file_first_then_sealing_includes_it(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    both = files_fingerprint({"a.csv": b"a", "b.csv": b"b"})
    error = race(w.e, "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                 "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                 dict(v=sv, h=sha(b"b"), c=b"b"), dict(v=sv, fp=both))
    assert error is None  # the seal waited, then fingerprinted both files


def test_sealing_first_then_file_is_rejected(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    error = race(w.e, "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v",
                 "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, 'b.csv', :h, :c)",
                 dict(v=sv, fp=files_fingerprint({"a.csv": b"a"})), dict(v=sv, h=sha(b"b"), c=b"b"))
    rejected(error, "sealed source version")
    assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=sv) == 1
```

### `tests/test_data_model.py`

SHA-256 `8aea1082bc271d57b39aeb23e9cfc14355cc8fc9e42eae54a74167dd0a348359`, 64337 bytes.

```python
"""Step 3: the rules the database enforces (PRD 7, with the owner's decisions of
2026-10-04/05). Every rule has an allowed case and a rejected case, on a freshly
migrated scratch database. Rejections by a trigger read "hypocurate: ..."; rejections
by a CHECK name the constraint."""
import pytest
from sqlalchemy.exc import IntegrityError

from hypocurate.db.models import MAX_FILE_BYTES
from model_builder import FP, World, files_fingerprint, sha


@pytest.fixture
def w(db):
    return World(db)


# --- queries and versions ------------------------------------------------------------------

def test_query_numbers_come_from_a_sequence(w):
    numbers = [w.val("SELECT number FROM hypothesis WHERE id = :h", h=w.hypothesis()) for _ in range(2)]
    assert numbers == ["Q-0001", "Q-0002"]


def test_a_new_version_starts_as_an_unreviewed_draft(w):
    h = w.hypothesis()
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, status, submitted_at) "
               "VALUES (:h, 1, 'x', :d, 'submitted', now())", "starts as an unreviewed draft",
               h=h, d=w.domain["grain_size_strengthening"])
    assert w.draft(hypothesis=h)


def test_a_submitted_version_cannot_be_edited(w):
    vid = w.draft()
    w.run_sql("UPDATE hypothesis_version SET text = 'edited in draft' WHERE id = :v", v=vid)
    w.submit(vid)
    for column, value in (("text", "'changed'"), ("note", "'changed'"),
                          ("domain_id", str(w.domain["other"]))):
        w.rejected(f"UPDATE hypothesis_version SET {column} = {value} WHERE id = :v",
                   "an edit is a new version", v=vid)


def test_an_edit_is_a_new_version_of_the_same_query(w):
    h = w.hypothesis()
    v1 = w.dispatched(hypothesis=h)
    v2 = w.draft(hypothesis=h, number=2)
    assert v2 != v1
    w.rejected("UPDATE hypothesis_version SET text = 'x' WHERE id = :v", "cannot change", v=v1)
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 2, 'x', :d)", "uq_hypothesis_version_hypothesis_id_version_number",
               h=h, d=w.domain["other"])


@pytest.mark.parametrize("start, end", [("draft", "dispatched"), ("draft", "returned"),
                                        ("submitted", "draft"), ("returned", "submitted"),
                                        ("dispatched", "submitted")])
def test_version_status_moves_only_forward(w, start, end):
    vid = w.draft()
    if start != "draft":
        w.submit(vid)
    if start == "returned":
        w.run_sql("UPDATE hypothesis_version SET status = 'returned', returned_at = now() WHERE id = :v", v=vid)
    if start == "dispatched":
        w.confirm(vid)
        w.dispatch_version(vid)
    w.rejected(f"UPDATE hypothesis_version SET status = '{end}', submitted_at = now(), returned_at = now(), "
               "dispatched_at = now() WHERE id = :v", "cannot (go from|change)", v=vid)


def test_return_for_edits_with_a_comment(w):
    vid = w.draft()
    w.submit(vid)
    w.run_sql("UPDATE hypothesis_version SET status = 'returned', returned_at = now(), "
              "review_comment = 'narrow the scope' WHERE id = :v", v=vid)
    w.rejected("UPDATE hypothesis_version SET review_comment = 'other' WHERE id = :v", "returned", v=vid)


def test_chosen_sources_change_only_in_draft(w):
    vid = w.draft()
    w.run_sql("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v AND source_id = :s",
              v=vid, s=w.source["tamu_fcc"])
    w.submit(vid)
    w.rejected("INSERT INTO hypothesis_version_source VALUES (:v, :s)", "only while the version is a draft",
               v=vid, s=w.source["tamu_fcc"])
    w.rejected("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v", "only while", v=vid)
    w.rejected("UPDATE hypothesis_version_source SET source_id = :s", "not updated", s=w.source["tamu_fcc"])


def test_reviewer_confirms_the_domain_only_while_submitted(w):
    """Owner decision, question 6: the submitter's domain is kept; the reviewer's
    decision is a separate field with its time, fixed at dispatch."""
    vid = w.draft()
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "only while the version is submitted", v=vid, d=w.domain["other"])
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d WHERE id = :v",
               "ck_hypothesis_version_confirmed_domain_with_time", v=vid, d=w.domain["other"])
    w.rejected("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v",
               "ck_hypothesis_version_dispatch_needs_confirmed_domain", v=vid)
    w.confirm(vid, "other")
    w.confirm(vid, "grain_size_strengthening")  # may be changed again before dispatch
    w.dispatch_version(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "dispatched hypothesis version cannot change", v=vid, d=w.domain["other"])
    row = w.rows("SELECT domain_id, confirmed_domain_id, domain_confirmed_at IS NOT NULL "
                 "FROM hypothesis_version WHERE id = :v", v=vid)[0]
    assert row == (w.domain["grain_size_strengthening"], w.domain["grain_size_strengthening"], True)


def test_dispatch_is_blocked_for_an_unsupported_domain(w):
    vid = w.dispatched(domain="fatigue")
    w.rejected("INSERT INTO run (hypothesis_version_id) VALUES (:v)", "domain is not supported", v=vid)


def test_a_run_needs_a_dispatched_version(w):
    vid = w.draft()
    w.rejected("INSERT INTO run (hypothesis_version_id) VALUES (:v)", "needs a dispatched", v=vid)


@pytest.mark.parametrize("table", ["hypothesis", "hypothesis_version", "run"])
def test_queries_versions_and_runs_are_never_deleted(w, table):
    w.run()
    w.rejected(f"DELETE FROM {table}", "(append-only|never deleted)")
    w.rejected(f"TRUNCATE {table} CASCADE", "(append-only|never deleted)")


# --- a narrower question is a separate query (owner decision, question 1) --------------------------

def partly_sufficient_run(w):
    rid = w.running()
    w.complete(rid, "partly_sufficient")
    return rid


def test_narrower_question_links_only_to_a_partly_sufficient_run(w):
    running = w.running()
    w.rejected("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r)", "partly_sufficient", r=running)
    insufficient = w.running()
    w.complete(insufficient, "insufficient")
    w.rejected("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r)", "partly_sufficient", r=insufficient)
    original = partly_sufficient_run(w)
    narrower = w.hypothesis(narrower_of=original)
    original_query = w.val("SELECT h.number FROM run r JOIN hypothesis_version v ON v.id = r.hypothesis_version_id "
                           "JOIN hypothesis h ON h.id = v.hypothesis_id WHERE r.id = :r", r=original)
    narrower_query = w.val("SELECT number FROM hypothesis WHERE id = :h", h=narrower)
    assert narrower_query.startswith("Q-") and narrower_query != original_query  # its own query number
    w.rejected("UPDATE hypothesis SET narrower_of_run_id = NULL WHERE id = :h", "append-only", h=narrower)


def test_a_partly_sufficient_run_has_no_verdict(w):
    rid = w.running()
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "verdict = 'supported' WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)


def test_narrower_question_has_the_original_domain(w):
    narrower = w.hypothesis(narrower_of=partly_sufficient_run(w))
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 1, 'narrower', :d)", "domain of its original", h=narrower, d=w.domain["other"])
    vid = w.draft(hypothesis=narrower)
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "domain of its original", v=vid, d=w.domain["other"])


def test_narrower_question_goes_through_review_and_dispatch(w):
    """Nothing creates or runs it automatically: it starts as a draft like any query."""
    original = partly_sufficient_run(w)
    narrower = w.hypothesis(narrower_of=original)
    assert w.rows("SELECT count(*) FROM hypothesis_version WHERE hypothesis_id = :h", h=narrower)[0][0] == 0
    vid = w.draft(hypothesis=narrower)
    assert w.val("SELECT status FROM hypothesis_version WHERE id = :v", v=vid) == "draft"
    rid = w.run(vid=w.dispatched(hypothesis=narrower, number=2))
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "queued"
    assert w.val("SELECT outcome FROM run WHERE id = :r", r=original) == "partly_sufficient"
    assert w.val("SELECT verdict FROM run WHERE id = :r", r=original) is None


# --- runs ----------------------------------------------------------------------------------------

def test_a_run_starts_queued(w):
    vid = w.dispatched()
    w.rejected("INSERT INTO run (hypothesis_version_id, status, started_at) VALUES (:v, 'running', now())",
               "starts as queued", v=vid)


@pytest.mark.parametrize("sql", [
    "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r",
    "UPDATE run SET status = 'queued' WHERE id = :r",
])
def test_run_status_moves_only_forward(w, sql):
    rid = w.run()
    if "queued" in sql:
        w.start(rid)
    w.rejected(sql, "run status cannot go from", r=rid)


@pytest.mark.parametrize("end", ["completed", "failed"])
def test_completed_and_failed_runs_are_final(w, end):
    rid = w.running()
    w.complete(rid, "insufficient") if end == "completed" else w.fail(rid)
    w.rejected("UPDATE run SET heartbeat_at = now() WHERE id = :r", "run is final", r=rid)


def test_what_a_run_records_at_dispatch_cannot_change(w):
    rid = w.run()
    for change in ("experiment_flags = '{\"relaxed\": true}'", "fixed_plan = true", "queued_at = now() - interval '1 day'"):
        w.rejected(f"UPDATE run SET {change} WHERE id = :r", "at dispatch cannot change", r=rid)


def test_a_failed_run_states_its_reason(w):
    rid = w.running()
    w.rejected("UPDATE run SET status = 'failed', failed_at = now() WHERE id = :r", "ck_run_failed_has_reason", r=rid)
    w.fail(rid, "spending cap reached")


@pytest.mark.parametrize("outcome, verdict", [("sufficient", None), ("insufficient", "supported"),
                                              ("partly_sufficient", "not_supported")])
def test_verdict_if_and_only_if_sufficient(w, outcome, verdict):
    rid, sets, _ = w.frozen()
    w.result(rid, sets["primary"])  # a valid pooled result, so only the verdict rule can fail
    with pytest.raises(IntegrityError, match="ck_run_verdict_iff_sufficient"):
        w.complete(rid, outcome, verdict)


def test_a_running_run_has_no_outcome_or_verdict(w):
    rid = w.running()
    w.rejected("UPDATE run SET verdict = 'supported' WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)
    w.rejected("UPDATE run SET outcome = 'insufficient' WHERE id = :r", "ck_run_outcome_iff_completed", r=rid)


# --- completion (owner's addition 2): the pooled-result rule applies only to "sufficient" ----------

def test_sufficient_needs_a_pooled_result_that_passed_both_checks(w):
    rid, sets, _ = w.frozen()
    with pytest.raises(IntegrityError, match="exactly one pooled result"):
        w.complete(rid, "sufficient", "supported")
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")


def test_coefficient_only_completes_as_insufficient_without_a_verdict(w):
    """Check 1 passes, check 2 fails (2 records, 1 alloy: no residual degree of freedom)."""
    rid, sets, _ = w.frozen(n=2, mins=(1, 1, 1, 1))
    w.result(rid, sets["primary"], n=2, alloys=1, groups=2)
    assert w.rows("SELECT check1_passed, check2_passed, estimate IS NOT NULL, std_error, p_value "
                  "FROM analysis_result WHERE run_id = :r", r=rid) == [(True, False, True, None, None)]
    with pytest.raises(IntegrityError, match="passed both validity checks"):
        w.complete(rid, "sufficient", "supported")
    w.complete(rid, "insufficient")
    assert w.val("SELECT verdict FROM run WHERE id = :r", r=rid) is None


@pytest.mark.parametrize("outcome", ["insufficient", "partly_sufficient", "failed"])
def test_other_endings_need_no_pooled_result(w, outcome):
    rid = w.running()
    w.fail(rid) if outcome == "failed" else w.complete(rid, outcome)
    assert w.val("SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0


def test_fixed_minimum_sufficient_needs_the_minimums_met(w):
    rid, sets, _ = w.frozen(mins=(5, 1, 2, 1))  # 4 records < 5
    w.result(rid, sets["primary"], mins=(5, 1, 2, 1))
    with pytest.raises(IntegrityError, match="minimums met"):
        w.complete(rid, "sufficient", "supported")
    w.complete(rid, "insufficient")


@pytest.mark.parametrize("met, exploratory_ok", [(False, True), (True, False)])
def test_exploratory_means_use_available_and_minimums_not_met(w, met, exploratory_ok):
    """Owner decision, question 4: under "use what is available", data that meet the
    minimums are not exploratory."""
    mins = (4, 1, 2, 1) if met else (5, 1, 2, 1)
    rid, sets, _ = w.frozen(option="use_available", mins=mins)
    w.result(rid, sets["primary"], mins=mins)
    with pytest.raises(IntegrityError, match="exploratory must equal"):
        w.complete(rid, "sufficient", "supported", exploratory=not exploratory_ok)
    w.complete(rid, "sufficient", "supported", exploratory=exploratory_ok)


def test_exploratory_only_with_a_verdict(w):
    rid = w.running()
    with pytest.raises(IntegrityError, match="ck_run_exploratory_needs_verdict"):
        w.complete(rid, "insufficient", exploratory=True)


# --- the rules lock -------------------------------------------------------------------------

def test_a_locked_plan_cannot_change(w):
    rid = w.running()
    pid = w.lock(rid, keys=["no_exclusions"])
    for change in ("content = '{\"exclude\": []}'", "sufficiency_option = 'use_available'", "min_records = 1",
                   "sensitivity_analysis_keys = '{}'", "power_assumptions = '{}'", "fingerprint = repeat('1', 64)"):
        w.rejected(f"UPDATE plan SET {change} WHERE id = :p", "plan is append-only", p=pid)
    w.rejected("DELETE FROM plan WHERE id = :p", "plan is append-only", p=pid)
    w.rejected("TRUNCATE plan CASCADE", "plan is append-only")
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'fixed_minimum', 1, 1, 1, 1)",
               "uq_plan_run_id", r=rid, fp=FP)


def test_a_plan_is_locked_only_while_the_run_is_running(w):
    with pytest.raises(IntegrityError, match="only while its run is running"):
        w.lock(w.run())


def test_the_lock_time_is_the_database_time(w):
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df, locked_at) VALUES (:r, '{}', :fp, 'fixed_minimum', 1, 1, 1, 1, "
               "now() - interval '1 hour')", "set by the database", r=w.running(), fp=FP)


@pytest.mark.parametrize("keys, match", [(["primary"], "ck_plan_primary_not_sensitivity"),
                                         (["a", "a"], "must be unique"),
                                         (["Bad Key"], "lowercase names")])
def test_sensitivity_analysis_keys(w, keys, match):
    with pytest.raises(IntegrityError, match=match):
        w.lock(w.running(), keys=keys)


@pytest.mark.parametrize("option, mins, match", [
    ("power_based", (30, 5, 10, 10), "ck_plan_sufficiency_option"),
    ("fixed_minimum", (0, 5, 10, 10), "ck_plan_minimums_positive"),
    ("use_available", (30, 5, 10, 0), "ck_plan_minimums_positive"),
])
def test_sufficiency_option_and_minimums(w, option, mins, match):
    """Power-based is not a gate in sprint 1 (owner's addition 1); minimums are kept under both options."""
    with pytest.raises(IntegrityError, match=match):
        w.lock(w.running(), option=option, mins=mins)


def test_power_assumptions_are_an_information_field(w):
    rid = w.running()
    w.run_sql("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
              "min_groups, min_resid_df, power_assumptions) VALUES (:r, '{}', :fp, 'fixed_minimum', 30, 5, 10, 10, "
              "'{\"power\": 0.8}')", r=rid, fp=FP)


def test_plan_fingerprint_format(w):
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df) VALUES (:r, '{}', 'ABC', 'fixed_minimum', 1, 1, 1, 1)",
               "ck_plan_fingerprint_format", r=w.running())


# --- tags --------------------------------------------------------------------------------------

def tag(w, value="FCC", status="approved"):
    return w.val("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('alloy_class', :v, :s, "
                 "CASE WHEN :s = 'proposed' THEN NULL ELSE now() END) RETURNING id", v=value, s=status)


def test_tags_are_written_in_the_lock_transaction_only(w):
    fcc, bcc = tag(w, "FCC"), tag(w, "BCC")
    rid = w.running()
    w.lock(rid, tags=[fcc])
    w.rejected("INSERT INTO run_tag VALUES (:r, :t)", "rules-lock transaction only", r=rid, t=bcc)
    w.rejected("DELETE FROM run_tag", "append-only")
    w.rejected("INSERT INTO run_tag VALUES (:r, :t)", "rules-lock transaction only", r=w.running(), t=bcc)


def test_a_proposed_tag_value_is_decided_once(w):
    proposed = tag(w, "HEA", "proposed")
    rid = w.running()
    w.lock(rid, tags=[proposed])  # the lock does not wait for a person
    w.run_sql("UPDATE tag_value SET status = 'approved', decided_at = now() WHERE id = :t", t=proposed)
    w.rejected("UPDATE tag_value SET status = 'rejected' WHERE id = :t", "approved or rejected once", t=proposed)
    w.rejected("DELETE FROM tag_value", "never deleted")


def test_a_rejected_tag_value_cannot_be_attached(w):
    rejected = tag(w, "nonsense", "rejected")
    with pytest.raises(IntegrityError, match="rejected tag value"):
        w.lock(w.running(), tags=[rejected])


def test_tag_kinds_are_a_fixed_list(w):
    w.rejected("INSERT INTO tag_value (kind, value, status) VALUES ('colour', 'blue', 'proposed')",
               "ck_tag_value_kind")


# --- agent settings ---------------------------------------------------------------------------

def setting(w, role="planner", version=1):
    return w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES (:r, :v, 'i', 'm') "
                 "RETURNING id", r=role, v=version)


def test_agent_settings_are_versioned_and_append_only(w):
    s1 = setting(w)
    setting(w, version=2)
    w.rejected("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 1, 'i', 'm')",
               "uq_agent_setting_role_version")
    w.rejected("UPDATE agent_setting SET instruction = 'new' WHERE id = :s", "append-only", s=s1)


def test_agent_settings_versions_are_recorded_at_dispatch(w):
    planner = setting(w)
    rid = w.run()
    w.rejected("INSERT INTO run_agent_setting VALUES (:r, 'critic', :s)", "fk_run_agent_setting_agent_setting",
               r=rid, s=planner)
    w.run_sql("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", r=rid, s=planner)
    w.rejected("UPDATE run_agent_setting SET agent_setting_id = :s", "append-only", s=planner)
    running = w.running()
    w.rejected("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", "recorded at dispatch",
               r=running, s=planner)


# --- run sources and "nothing found" (owner decision, question 3) ----------------------------------------

def test_a_run_source_starts_undecided(w):
    rid = w.running(sources=())
    w.rejected("UPDATE run_source SET search_status = 'searched' WHERE run_id = :r", "is final", r=rid)
    vid = w.dispatched()
    rid2 = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.rejected("INSERT INTO run_source (run_id, source_id, source_version_id, search_status, decided_at) "
               "VALUES (:r, :s, :sv, 'searched', now())", "starts as not_selected or pending",
               r=rid2, s=w.source["mpea"], sv=w.version["mpea"])


@pytest.mark.parametrize("status, kind, reason, match", [
    ("failed", None, "timeout", "ck_run_source_failed_iff_failed_search"),
    ("failed", "missing_evidence", "timeout", "ck_run_source_failed_iff_failed_search"),
    ("searched", "failed_search", None, "ck_run_source_failed_iff_failed_search"),
    ("failed", "failed_search", None, "ck_run_source_failed_has_reason"),
])
def test_a_failed_source_is_always_failed_search(w, status, kind, reason, match):
    rid = w.running()
    with pytest.raises(IntegrityError, match=match):
        w.search(rid, status=status, nothing_found=kind, reason=reason)


def test_a_decided_run_source_is_final(w):
    rid = w.running()
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.rejected("UPDATE run_source SET search_status = 'searched', nothing_found = NULL, failure_reason = NULL "
               "WHERE run_id = :r AND source_id = :s", "is final", r=rid, s=w.source["mpea"])
    w.rejected("DELETE FROM run_source", "never deleted")


def test_the_source_version_of_a_run_cannot_change(w):
    rid = w.running()
    other = w.new_version("mpea", "v2")
    w.add_file(other, "mpea_v2.csv", b"v2")
    w.seal(other)
    w.rejected("UPDATE run_source SET source_version_id = :sv WHERE run_id = :r AND source_id = :s",
               "cannot change", sv=other, r=rid, s=w.source["mpea"])


COVERAGE = ("searched_sources, not_searched_sources, not_selected_sources, failed_search_sources, "
            "records_found_sources, missing_evidence_sources, reported_negative_sources")


def coverage(w, rid):
    names = [c.strip() for c in COVERAGE.split(",")]
    return dict(zip(names, w.rows(f"SELECT {COVERAGE} FROM run_search_coverage WHERE run_id = :r", r=rid)[0]))


def test_a_failed_source_is_never_missing_evidence(w):
    """One source failed, the other has missing evidence: each is reported in its own
    category; the failed source is named as failed and not searched."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "missing_evidence")
    w.search(rid, "tamu_fcc", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["missing_evidence_sources"] == ["mpea"] and c["failed_search_sources"] == ["tamu_fcc"]
    assert c["searched_sources"] == ["mpea"] and c["not_searched_sources"] == ["tamu_fcc"]


def test_mixed_results_are_reported_per_category(w):
    """Review finding 6: a negative report in one source and missing evidence in another
    are both reported, each with its source; nothing collapses them into one label."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "reported_negative")
    w.search(rid, "tamu_fcc", "searched", "missing_evidence")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["reported_negative_sources"] == ["mpea"] and c["missing_evidence_sources"] == ["tamu_fcc"]
    assert c["searched_sources"] == ["mpea", "tamu_fcc"] and c["not_searched_sources"] == []


def test_every_selected_source_failing_shows_no_source_searched(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["searched_sources"] == [] and c["failed_search_sources"] == ["mpea"]
    assert c["not_searched_sources"] == ["mpea", "tamu_fcc"] and c["not_selected_sources"] == ["tamu_fcc"]


def test_records_found_is_its_own_category(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "searched")
    c = coverage(w, rid)
    assert c["records_found_sources"] == ["mpea"] and c["missing_evidence_sources"] == []


def test_coverage_comes_from_the_runs_own_dispatch_rows(w):
    """Review finding 6: registering a source later does not change an earlier run's coverage."""
    rid = w.running()
    w.search(rid, "mpea", "searched")
    w.complete(rid, "insufficient")
    before = coverage(w, rid)
    w.add_source("later_source")
    assert coverage(w, rid) == before
    w.rejected("UPDATE source SET key = 'renamed' WHERE key = 'mpea'", "key and registration time cannot change")


def test_a_run_starts_only_with_its_full_source_inventory(w):
    """Every source registered at dispatch has a run_source row before the run starts."""
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
              "VALUES (:r, :s, :sv, 'pending')", r=rid, s=w.source["mpea"], sv=w.version["mpea"])
    with pytest.raises(IntegrityError, match="every source registered at dispatch"):
        w.start(rid)
    w.run_sql("INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
              r=rid, s=w.source["tamu_fcc"])
    w.start(rid)


def test_no_table_stores_a_run_level_nothing_found(w):
    assert w.val("SELECT count(*) FROM information_schema.columns WHERE table_name = 'run' "
                 "AND column_name LIKE '%nothing%'") == 0


# --- records: stored is not analysed ---------------------------------------------------------

def test_records_are_never_updated_or_deleted(w):
    rid = w.locked()
    rec = w.record(rid)
    for sql in ("UPDATE record SET alloy = 'other' WHERE id = :c", "UPDATE record SET harmonized = '{}' WHERE id = :c",
                "DELETE FROM record WHERE id = :c"):
        w.rejected(sql, "record is append-only", c=rec)
    w.rejected("TRUNCATE record CASCADE", "append-only")


def test_a_record_comes_from_a_source_version_its_run_recorded(w):
    rid = w.locked(sources=("mpea",))
    with pytest.raises(IntegrityError, match="source version recorded for its run"):
        w.record(rid, source="tamu_fcc")
    w.record(rid, source="mpea")


def test_records_are_extracted_while_running_and_before_the_freeze(w):
    with pytest.raises(IntegrityError, match="while their run is running"):
        w.record(w.run())
    rid, _, _ = w.frozen()
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.record(rid, key="late")


def test_every_record_names_its_origin(w):
    """Owner decision, question 7: source version plus the row it came from, so the
    same source row can be matched across runs."""
    rid = w.locked()
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported) "
               "VALUES (:r, :sv, '', 'measured', '{}', '{}')", "ck_record_item_key_not_empty",
               r=rid, sv=w.version["mpea"])
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported) "
               "VALUES (:r, :sv, 'measured', '{}', '{}')", "source_item_key", r=rid, sv=w.version["mpea"])
    w.record(rid, key="row-7")
    with pytest.raises(IntegrityError, match="uq_record_origin_per_run"):
        w.record(rid, key="row-7")
    w.record(rid, key="row-7", index=1)  # a second observation from the same row
    other_run = w.locked()
    w.record(other_run, key="row-7")
    matched = w.rows("SELECT extraction_run_id FROM record WHERE source_version_id = :sv AND source_item_key = 'row-7' "
                     "AND item_index = 0 ORDER BY extraction_run_id", sv=w.version["mpea"])
    assert [r[0] for r in matched] == [rid, other_run]
    index = w.val("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_record_source_version_id_source_item_key'")
    assert index.endswith("(source_version_id, source_item_key)")


def test_records_and_eligibility_come_after_the_rules_lock(w):
    """Review finding 3: no extraction before the rules lock, so no record can be
    decided on outside a locked plan."""
    rid = w.running()
    with pytest.raises(IntegrityError, match="only after the rules lock"):
        w.record(rid)
    w.lock(rid)
    rec = w.record(rid)
    w.decide(rid, rec, eligible=False, rule="grain size below 0.1 um")
    w.rejected("UPDATE run_record SET eligible = true", "append-only")
    w.rejected("DELETE FROM run_record", "append-only")


def test_a_run_decides_only_on_its_own_records(w):
    other = w.locked()
    rec = w.record(other)
    rid = w.running()
    w.lock(rid)
    with pytest.raises(IntegrityError, match="records extracted in that run"):
        w.decide(rid, rec)


def test_a_model_recalled_record_is_stored_but_never_eligible(w):
    w.add_source("recall", data_kind="model_recalled", source_type="model_recall")
    rid = w.locked(sources=("mpea", "recall"))
    rec = w.record(rid, source="recall")
    assert w.val("SELECT kind FROM record WHERE id = :c", c=rec) == "model_recalled"
    with pytest.raises(IntegrityError, match="never eligible"):
        w.decide(rid, rec, eligible=True)
    w.decide(rid, rec, eligible=False, rule="model-recalled: comparison only")
    sensitivity = w.analysis_set(rid, "primary")
    with pytest.raises(IntegrityError, match="never in an analysis set"):
        w.add(sensitivity, rec)


# --- analysis sets and the dataset freeze (owner decision, question 2) ---------------------------------

def test_a_set_exists_only_for_an_analysis_the_locked_plan_names(w):
    rid = w.running()
    with pytest.raises(IntegrityError, match="needs a locked plan"):
        w.analysis_set(rid)
    w.lock(rid, keys=["no_exclusions"])
    w.analysis_set(rid, "primary")
    w.analysis_set(rid, "no_exclusions")
    with pytest.raises(IntegrityError, match="names no analysis drop_four"):
        w.analysis_set(rid, "drop_four")


def test_primary_holds_only_eligible_records_and_sensitivity_sets_may_hold_others(w):
    rid = w.running()
    w.lock(rid, keys=["scope_not_confirmed"])
    eligible, excluded, undecided = w.record(rid, key="a"), w.record(rid, key="b"), w.record(rid, key="c")
    w.decide(rid, eligible)
    w.decide(rid, excluded, eligible=False, rule="scope not confirmed")
    primary, sensitivity = w.analysis_set(rid), w.analysis_set(rid, "scope_not_confirmed")
    with pytest.raises(IntegrityError, match="only eligible records"):
        w.add(primary, excluded)
    w.add(primary, eligible)
    w.add(sensitivity, eligible)
    w.add(sensitivity, excluded)
    with pytest.raises(IntegrityError, match="decided on"):
        w.add(sensitivity, undecided)


def test_a_possible_duplicate_counts_once_in_primary_and_twice_in_its_sensitivity_set(w):
    """PRD 5.3, the reason for named sets: one survivor in primary, both in the sensitivity set.
    This shows the storage can hold the result; it does not test duplicate handling,
    which is built in step 6 (second-model review of step 3). The non-surviving copy
    carries its own decision (not eligible), which keeps it out of the primary set."""
    rid = w.running()
    w.lock(rid, keys=["duplicates_separate"])
    survivor, twin = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, survivor)
    w.decide(rid, twin, eligible=False, rule="possible duplicate of a; counted once")
    primary, both = w.analysis_set(rid), w.analysis_set(rid, "duplicates_separate")
    w.add(primary, survivor)
    w.add(both, survivor)
    w.add(both, twin)
    w.freeze(rid, 1)
    counts = w.rows("SELECT s.key, count(*) FROM analysis_set s JOIN analysis_set_record r ON r.analysis_set_id = s.id "
                    "WHERE s.run_id = :r GROUP BY s.key ORDER BY s.key", r=rid)
    assert counts == [("duplicates_separate", 2), ("primary", 1)]


def test_nothing_changes_after_the_freeze(w):
    rid, sets, recs = w.frozen(keys=["no_exclusions"])
    late = recs[0]
    for sql, match in [
        ("INSERT INTO analysis_set (run_id, key) VALUES (:r, 'no_exclusions_2')", "names no analysis|after the dataset freeze"),
        ("DELETE FROM analysis_set_record WHERE analysis_set_id = :s", "append-only"),
        ("UPDATE analysis_set SET key = 'other' WHERE run_id = :r", "append-only"),
        ("UPDATE run_snapshot SET fingerprint = repeat('1', 64) WHERE run_id = :r", "append-only"),
        ("DELETE FROM run_snapshot WHERE run_id = :r", "append-only"),
    ]:
        w.rejected(sql, match, r=rid, s=sets["primary"])
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.add(sets["no_exclusions"], late)
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.decide(rid, late)


def eligible_records(w, rid, n):
    recs = [w.record(rid, key=f"row-{i}") for i in range(n)]
    for rec in recs:
        w.decide(rid, rec)
    return recs


def test_the_freeze_rejects_a_primary_set_that_omits_eligible_records(w):
    """Review finding 2: ten records decided eligible, three put in primary."""
    rid = w.locked()
    recs = eligible_records(w, rid, 10)
    primary = w.analysis_set(rid)
    for rec in recs[:3]:
        w.add(primary, rec)
    with pytest.raises(IntegrityError, match="must hold every record decided eligible"):
        w.freeze(rid, 3)
    for rec in recs[3:]:
        w.add(primary, rec)
    w.freeze(rid, 10)


def test_the_freeze_rejects_an_undecided_record(w):
    rid = w.locked()
    rec = eligible_records(w, rid, 1)[0]
    w.add(w.analysis_set(rid), rec)
    w.record(rid, key="undecided")
    with pytest.raises(IntegrityError, match="needs an eligibility decision"):
        w.freeze(rid, 1)


def test_no_eligible_records_means_no_freeze(w):
    rid = w.running()
    w.lock(rid)
    w.analysis_set(rid)
    with pytest.raises(IntegrityError, match="no dataset is frozen"):
        w.freeze(rid, 1)
    with pytest.raises(IntegrityError, match="no dataset is frozen"):
        w.freeze(rid, 0)


def test_the_freeze_matches_the_primary_set_and_needs_every_named_set(w):
    rid = w.running()
    w.lock(rid, keys=["no_exclusions"])
    rec = w.record(rid)
    w.decide(rid, rec)
    w.add(w.analysis_set(rid), rec)
    with pytest.raises(IntegrityError, match="every sensitivity analysis named by the plan"):
        w.freeze(rid, 1)
    w.analysis_set(rid, "no_exclusions")
    with pytest.raises(IntegrityError, match="size of the primary set"):
        w.freeze(rid, 2)
    w.rejected("INSERT INTO run_snapshot (run_id, fingerprint, n_records, frozen_at) "
               "VALUES (:r, :fp, 1, now() - interval '1 hour')", "set by the database", r=rid, fp=FP)
    w.freeze(rid, 1)


# --- lifecycle on both sides (review finding 3; owner, 2026-10-05) ---------------------------------

def curation_in_progress(w):
    """A locked run with a record, a decision, a primary set, a pending source and an
    unclassified flag: everything curation could still touch."""
    rid = w.locked()
    w.search(rid, "mpea", "searched")  # tamu_fcc stays pending
    rec = eligible_records(w, rid, 1)[0]
    w.record(rid, key="undecided")
    primary = w.analysis_set(rid)
    f = flag(w, rid)
    return rid, rec, primary, f


@pytest.mark.parametrize("ending", ["completed", "failed"])
def test_no_curation_once_the_run_has_ended(w, ending):
    rid, rec, primary, f = curation_in_progress(w)
    w.complete(rid, "insufficient") if ending == "completed" else w.fail(rid)
    with pytest.raises(IntegrityError, match="while their run is running"):
        w.record(rid, key="late")
    for sql in [
        "INSERT INTO run_record (run_id, record_id, eligible, rule) SELECT :r, id, true, 'x' FROM record "
        "WHERE extraction_run_id = :r AND source_item_key = 'undecided'",
        "INSERT INTO analysis_set_record VALUES (:s, :c)",
        "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
        "UPDATE flag SET critic_class = 'comparable', classified_at = now() WHERE id = :f",
        "INSERT INTO flag_record VALUES (:f, :c)",
        "UPDATE run_source SET search_status = 'searched', decided_at = now() WHERE run_id = :r AND search_status = 'pending'",
    ]:
        w.rejected(sql, "only while the run is running|while the run is running", r=rid, c=rec, s=primary, f=f)
    w.rejected("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
               "only while its run is running", r=rid, fp=FP)
    w.rejected(CALIBRATION.format(numbers=NONE), "only while the run is running",
               r=rid, a=None, st="unavailable", re="no_dataset_frozen")


def test_a_record_extracted_after_the_freeze_cannot_slip_in_after_the_run_ends(w):
    rid, sets, _ = w.frozen()
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    for sql in ["INSERT INTO analysis_set (run_id, key) VALUES (:r, 'extra')",
                "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
                "check1_passed, check2_passed, minimums_met) VALUES (:r, 'sensitivity', :s, 0, 0, 0, -1, false, false, false)"]:
        w.rejected(sql, "only while the run is running", r=rid, s=sets["primary"])


def test_no_dataset_frozen_and_a_freeze_exclude_each_other(w):
    """Review finding 3: whichever comes second is rejected (the other order is in the
    calibration tests below)."""
    rid = w.locked()
    rec = eligible_records(w, rid, 1)[0]
    w.add(w.analysis_set(rid), rec)
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=None, st="unavailable", re="no_dataset_frozen")
    with pytest.raises(IntegrityError, match="already recorded that no dataset was frozen"):
        w.freeze(rid, 1)


def test_what_may_be_written_after_completion(w):
    """Owner, 2026-10-05: the commentary, the Commentator's stage and model calls, and
    artifacts. The Commentator's calls count in the run's totals and cap. Nothing else."""
    rid, sets, _ = w.frozen()
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    commentator = w.stage(rid, "commentator", "commentator")
    call = w.call(rid, commentator, max_cost=0.25, role="commentator")
    assert float(w.val("SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)) == 0.25
    w.finish_call(call, "succeeded", (100, 50, 0, 0.002))
    assert float(w.val("SELECT reported_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)) == 0.002
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=commentator)
    w.run_sql("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
              "VALUES (:r, :s, 'written', 'k = 428', 'other-model', 'all_match')", r=rid, s=commentator)
    w.run_sql(ARTIFACT, r=rid, h=sha(b"plot"), c=b"plot")
    with pytest.raises(IntegrityError, match="after completion only the commentator"):
        w.stage(rid, "analyst", "analyst")
    with pytest.raises(IntegrityError, match="after completion only the commentator"):
        w.call(rid, commentator, role="analyst")
    for sql in ["UPDATE run SET verdict = 'not_supported' WHERE id = :r",
                "UPDATE run SET outcome = 'insufficient', verdict = NULL WHERE id = :r"]:
        w.rejected(sql, "run is final", r=rid)
    w.rejected("UPDATE analysis_result SET estimate = 1", "append-only")
    w.rejected("INSERT INTO analysis_set_record VALUES (:s, :c)", "only while the run is running",
               s=sets["primary"], c=w.val("SELECT min(id) FROM record"))
    assert w.rows("SELECT outcome, verdict FROM run WHERE id = :r", r=rid) == [("sufficient", "supported")]


def test_nothing_but_the_audit_log_after_failure(w):
    rid = w.running()
    st = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE id = :s", s=st)
    w.fail(rid, "worker stopped")
    with pytest.raises(IntegrityError, match="while the run is running"):
        w.stage(rid, "commentator", "commentator")
    with pytest.raises(IntegrityError, match="while the run is running"):
        w.call(rid, st)
    w.rejected("INSERT INTO commentary (run_id, stage_result_id, status, model) VALUES (:r, :s, 'unavailable', 'm')",
               "after the run is completed", r=rid, s=st)
    w.rejected(ARTIFACT, "running or completed run", r=rid, h=sha(b"x"), c=b"x")
    w.run_sql("INSERT INTO audit_log (run_id, role, stage, function, allowed) VALUES (:r, 'planner', 'plan', 'x', false)",
              r=rid)


@pytest.mark.parametrize("ending", ["completed", "failed"])
def test_a_run_ends_only_with_no_stage_running_and_no_call_open(w, ending):
    rid = w.running()
    st = w.stage(rid)
    end = (lambda: w.complete(rid, "insufficient")) if ending == "completed" else (lambda: w.fail(rid))
    with pytest.raises(IntegrityError, match="no stage is running and no model call is open"):
        end()
    call = w.call(rid, st)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=st)
    with pytest.raises(IntegrityError, match="no stage is running and no model call is open"):
        end()
    w.finish_call(call, "interrupted", None)
    end()


# --- flags ---------------------------------------------------------------------------------------

def flag(w, rid):
    return w.val("INSERT INTO flag (run_id, kind, category, compared_values) "
                 "VALUES (:r, 'values_differ', 'differ beyond tolerance', '{\"a\": 1.0}') RETURNING id", r=rid)


def test_a_flag_is_classified_once_before_the_freeze(w):
    rid = w.running()
    f = flag(w, rid)
    w.rejected("UPDATE flag SET compared_values = '{}' WHERE id = :f", "classification", f=f)
    w.run_sql("UPDATE flag SET critic_class = 'comparable', critic_reason = 'same test', classified_at = now() "
              "WHERE id = :f", f=f)
    w.rejected("UPDATE flag SET critic_class = 'other', classified_at = now() WHERE id = :f", "classified once", f=f)
    w.rejected("DELETE FROM flag", "never deleted")


def test_flags_stop_at_the_freeze(w):
    rid, _, recs = w.frozen()
    w.rejected("INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')", "after the dataset freeze", r=rid)


def test_a_flag_names_records_of_its_own_run(w):
    rid, other = w.locked(), w.locked()
    f = flag(w, rid)
    w.run_sql("INSERT INTO flag_record VALUES (:f, :c)", f=f, c=w.record(rid))
    w.rejected("INSERT INTO flag_record VALUES (:f, :c)", "its own run", f=f, c=w.record(other))


# --- analysis results (owner's addition 3) ------------------------------------------------------------

def test_results_come_after_the_freeze(w):
    rid = w.running()
    w.lock(rid)
    primary = w.analysis_set(rid)
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.result(rid, primary, n=0)


@pytest.mark.parametrize("column, value, match", [
    ("check2_passed", "true", "ck_analysis_result_check2_consistent"),  # 1 group
    ("std_error", "1.0", "ck_analysis_result_std_error_iff_check2"),
    ("p_value", "0.01", "ck_analysis_result_p_value_iff_check2"),
    ("resid_df", "5", "ck_analysis_result_resid_df_definition"),
])
def test_the_validity_checks_cannot_be_waived(w, column, value, match):
    """One group: check 2 fails, so no uncertainty and no p-value can be stored."""
    rid, sets, _ = w.frozen()
    rid_value = w.result(rid, sets["primary"], groups=1)
    assert w.rows("SELECT check2_passed, std_error, p_value FROM analysis_result WHERE id = :a", a=rid_value) == [
        (False, None, None)]
    rid2, sets2, _ = w.frozen()
    columns = {"run_id": rid2, "scope": "'pooled'", "analysis_set_id": sets2["primary"], "n_records": 4,
               "n_alloys": 1, "n_groups": 1, "resid_df": 2, "check1_passed": "true", "check2_passed": "false",
               "minimums_met": "false", "estimate": 1.0}
    columns[column] = value
    w.rejected(f"INSERT INTO analysis_result ({', '.join(columns)}) VALUES ({', '.join(map(str, columns.values()))})",
               match)


def test_check_one_failing_means_no_estimate(w):
    rid, sets, _ = w.frozen(n=1, mins=(1, 1, 1, 1))
    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
               "check1_passed, check2_passed, minimums_met, estimate) VALUES (:r, 'pooled', :s, 1, 0, 1, 0, false, "
               "false, false, 5.0)", "ck_analysis_result_estimate_iff_check1", r=rid, s=sets["primary"])
    w.result(rid, sets["primary"], n=1, alloys=0, groups=1, mins=(1, 1, 1, 1))


@pytest.mark.parametrize("n, alloys, groups, match", [
    (1, 1, 1, "ck_analysis_result_two_records_per_alloy"),  # one record cannot show two grain sizes
    (4, 1, 5, "ck_analysis_result_groups_within_records"),
    (4, 0, 0, "ck_analysis_result_records_have_a_group"),
    (4, 2, 2, "cannot exceed the distinct alloys"),         # the set has one alloy
])
def test_stored_counts_must_be_consistent(w, n, alloys, groups, match):
    """Review finding 5: necessary conditions on the stored counts. The full validity
    rules of PRD 5.7 are computed and tested in step 7."""
    rid, sets, _ = w.frozen(n=n, mins=(1, 1, 1, 1))
    with pytest.raises(IntegrityError, match=match):
        w.result(rid, sets["primary"], n=n, alloys=alloys, groups=groups, mins=(1, 1, 1, 1))


def test_one_result_per_run_and_scope_on_the_right_set(w):
    rid, sets, _ = w.frozen(n=4, per_source={"mpea": 3, "tamu_fcc": 1}, keys=["no_exclusions"])
    w.result(rid, sets["primary"])
    with pytest.raises(IntegrityError, match="uq_analysis_result_scope"):
        w.result(rid, sets["primary"])
    with pytest.raises(IntegrityError, match="use the primary set"):
        w.result(rid, sets["no_exclusions"], scope="pooled", n=0)
    with pytest.raises(IntegrityError, match="uses a sensitivity set"):
        w.result(rid, sets["primary"], scope="sensitivity")
    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
               "resid_df, check1_passed, check2_passed, minimums_met) "
               "VALUES (:r, 'per_source', :s, 4, 0, 1, 3, false, false, false)",
               "ck_analysis_result_source_iff_per_source", r=rid, s=sets["primary"])
    w.result(rid, sets["primary"], scope="per_source", source="mpea", n=3, alloys=1, groups=2)
    w.result(rid, sets["primary"], scope="per_source", source="tamu_fcc", n=1, alloys=0, groups=1)
    with pytest.raises(IntegrityError, match="uq_analysis_result_scope"):
        w.result(rid, sets["primary"], scope="per_source", source="mpea", n=3, alloys=1, groups=2)
    w.result(rid, sets["no_exclusions"], scope="sensitivity", n=0, alloys=0, groups=0)
    w.rejected("UPDATE analysis_result SET estimate = 1", "append-only")


def test_counts_must_match_the_set_used(w):
    rid, sets, _ = w.frozen(n=4, per_source={"mpea": 3, "tamu_fcc": 1})
    with pytest.raises(IntegrityError, match="n_records must equal"):
        w.result(rid, sets["primary"], n=5)
    with pytest.raises(IntegrityError, match="n_records must equal"):
        w.result(rid, sets["primary"], scope="per_source", source="mpea", n=4)  # restricted to MPEA: 3


def test_minimums_met_must_agree_with_the_plan(w):
    rid, sets, _ = w.frozen(mins=(4, 1, 2, 1))
    with pytest.raises(IntegrityError, match="minimums_met must agree"):
        w.result(rid, sets["primary"], minimums_met=False)


# --- calibration --------------------------------------------------------------------------------------

CALIBRATION = ("INSERT INTO calibration_result (run_id, analysis_result_id, status, reason, assumptions, "
               "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, "
               "effect_ci_high, confidence_flag) VALUES (:r, :a, :st, :re, {numbers})")
NUMBERS = "'{\"scatter\": 60}', 2000, 7, 0.072, 0.061, 0.084, 1.0, 0.998, 1.0, 'over_confident'"
NONE = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"


def test_calibration_is_computed_exactly_when_inference_is_valid(w):
    rid, sets, _ = w.frozen(keys=["one_group"])
    valid = w.result(rid, sets["primary"])
    w.run_sql(CALIBRATION.format(numbers=NUMBERS), r=rid, a=valid, st="computed", re=None)
    w.rejected(CALIBRATION.format(numbers=NONE), "computed exactly when", r=rid, a=valid, st="unavailable",
               re="insufficient_groups")
    w.rejected("DELETE FROM calibration_result", "append-only")


def test_calibration_unavailable_states_a_matching_reason(w):
    rid, sets, _ = w.frozen(n=2, per_source={"mpea": 1, "tamu_fcc": 1}, mins=(1, 1, 1, 1))
    one_group = w.result(rid, sets["primary"], scope="per_source", source="mpea", n=1, alloys=0, groups=1,
                         mins=(1, 1, 1, 1))
    w.rejected(CALIBRATION.format(numbers=NUMBERS), "computed exactly when", r=rid, a=one_group, st="computed",
               re=None)
    w.rejected(CALIBRATION.format(numbers=NONE), "must match the validity checks", r=rid, a=one_group,
               st="unavailable", re="insufficient_groups")
    w.rejected(CALIBRATION.format(numbers=NONE), "ck_calibration_result_unavailable_has_reason_only",
               r=rid, a=one_group, st="unavailable", re=None)
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=one_group, st="unavailable", re="coefficient_not_fitted")


def test_run_level_calibration_only_when_no_dataset_was_frozen(w):
    rid = w.running()
    w.rejected(CALIBRATION.format(numbers=NONE), "ck_calibration_result_run_level_only_without_freeze",
               r=rid, a=None, st="unavailable", re="insufficient_groups")
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=None, st="unavailable", re="no_dataset_frozen")
    frozen, _, _ = w.frozen()
    w.rejected(CALIBRATION.format(numbers=NONE), "calibration is reported per analysis",
               r=frozen, a=None, st="unavailable", re="no_dataset_frozen")


def test_calibration_intervals_contain_their_share(w):
    rid, sets, _ = w.frozen()
    valid = w.result(rid, sets["primary"])
    bad = NUMBERS.replace("0.072, 0.061, 0.084", "0.072, 0.080, 0.084")
    w.rejected(CALIBRATION.format(numbers=bad), "ck_calibration_result_null_interval",
               r=rid, a=valid, st="computed", re=None)


# --- model calls and totals (owner decision, question 5) ------------------------------------------------

def test_a_model_call_is_recorded_before_the_request_and_finished_once(w):
    rid = w.running()
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, status, "
               "input_tokens, output_tokens, cached_tokens, cost, finished_at) VALUES (:r, :s, 'planner', 'm', 'p', 1, "
               "'succeeded', 1, 1, 0, 0.1, now())", "before the request", r=rid, s=st)
    call = w.call(rid, st)
    with pytest.raises(IntegrityError, match="ck_model_call_succeeded_has_usage"):
        w.finish_call(call, "succeeded", usage=None)
    w.finish_call(call, "succeeded")
    with pytest.raises(IntegrityError, match="finished exactly once"):
        w.finish_call(call, "failed", usage=None)
    w.rejected("DELETE FROM model_call", "never deleted")


def test_model_call_usage_rules(w):
    rid = w.running()
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', '', 1)", "ck_model_call_model_and_prices_named", r=rid, s=st)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version) "
               "VALUES (:r, :s, 'planner', 'm', 'p')", "max_cost", r=rid, s=st)
    partial = w.call(rid, st)
    w.rejected("UPDATE model_call SET status = 'failed', input_tokens = 5, finished_at = now() WHERE id = :c",
               "ck_model_call_failed_usage_all_or_none", c=partial)
    w.rejected("UPDATE model_call SET status = 'succeeded', input_tokens = -1, output_tokens = 1, cached_tokens = 0, "
               "cost = 0, finished_at = now() WHERE id = :c", "ck_model_call_usage_not_negative", c=partial)
    w.rejected("UPDATE model_call SET status = 'failed', max_cost = 0, finished_at = now() WHERE id = :c",
               "before the request cannot change", c=partial)
    other = w.running()
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 1)", "fk_model_call_stage_result", r=other, s=st)


def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound(w):
    rid = w.running()
    planner, curator = w.stage(rid), w.stage(rid, "curator", "curator")
    ok = w.call(rid, planner, max_cost=0.50)
    w.finish_call(ok, "succeeded", (1000, 200, 100, 0.0123))
    charged = w.call(rid, planner, max_cost=0.40)
    w.finish_call(charged, "failed", (500, 0, 0, 0.0040))         # failed, but the provider reported usage
    lost = w.call(rid, curator, max_cost=0.30)
    w.finish_call(lost, "failed", None)                           # failed without usage: may still be charged
    w.call(rid, curator, max_cost=0.20)                           # still started (e.g. the worker died)
    columns = "calls, input_tokens, output_tokens, cached_tokens, reported_cost, unconfirmed_calls, " \
              "unconfirmed_cost_bound, cap_cost"
    run_total = w.rows(f"SELECT {columns} FROM model_call_totals_by_run WHERE run_id = :r", r=rid)[0]
    assert tuple(map(float, run_total)) == (4, 1500, 200, 100, 0.0163, 2, 0.50, 0.5163)
    by_stage = w.rows(f"SELECT stage, {columns} FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage",
                      r=rid)
    assert [(s, float(rep), float(cap)) for s, _, _, _, _, rep, _, _, cap in by_stage] == [
        ("curator", 0.0, 0.50), ("planner", 0.0163, 0.0163)]
    query = w.rows("SELECT h.id FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
                   "JOIN run r ON r.hypothesis_version_id = v.id WHERE r.id = :r", r=rid)[0][0]
    assert float(w.val("SELECT cap_cost FROM model_call_totals_by_query WHERE hypothesis_id = :h", h=query)) == 0.5163
    assert float(w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month")) == 0.5163
    direct = w.rows("SELECT sum(cost), sum(coalesce(cost, max_cost)) FROM model_call")[0]
    assert tuple(map(float, direct)) == (0.0163, 0.5163)


def test_small_costs_are_stored_exactly(w):
    """Review finding 7: numeric without a fixed scale; nothing rounds to zero."""
    from decimal import Decimal
    rid = w.running()
    call = w.call(rid, w.stage(rid), max_cost=Decimal("1E-12"))
    w.finish_call(call, "succeeded", (1, 1, 0, Decimal("3E-13")))
    w.call(rid, w.stage(rid, "curator", "curator"), max_cost=Decimal("2E-12"))
    row = w.rows("SELECT reported_cost, unconfirmed_cost_bound, cap_cost FROM model_call_totals_by_run "
                 "WHERE run_id = :r", r=rid)[0]
    assert row == (Decimal("3E-13"), Decimal("2E-12"), Decimal("2.3E-12"))
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 0)", "ck_model_call_max_cost_positive",
               r=rid, s=w.val("SELECT min(id) FROM stage_result"))


def test_call_times_are_set_by_the_database(w):
    rid = w.running()
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, started_at) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 1, now() - interval '40 days')", "started_at is set by the database",
               r=rid, s=st)
    call = w.call(rid, st)
    w.rejected("UPDATE model_call SET status = 'interrupted', finished_at = now() - interval '1 day' WHERE id = :c",
               "finished_at is set by the database", c=call)


def test_a_run_without_calls_totals_zero(w):
    rid = w.running()
    assert tuple(map(float, w.rows("SELECT calls, reported_cost, cap_cost FROM model_call_totals_by_run "
                                   "WHERE run_id = :r", r=rid)[0])) == (0, 0, 0)


def test_no_table_stores_token_or_cost_totals(w):
    columns = w.rows("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' "
                     "AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' "
                     "AND table_schema = 'public') AND (column_name LIKE '%token%' OR column_name LIKE '%cost%')")
    assert {t for t, _ in columns} == {"model_call"}


def test_a_finished_stage_result_is_final(w):
    rid = w.running()
    st = w.stage(rid)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=st)
    w.rejected("UPDATE stage_result SET output = '{\"changed\": true}' WHERE id = :s", "is final", s=st)
    w.rejected("DELETE FROM stage_result", "never deleted")


# --- commentary ---------------------------------------------------------------------------------------

def test_commentary_comes_after_completion_and_lists_mismatches(w):
    rid = w.running()
    early = w.stage(rid, "commentator", "commentator")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=early)
    sql = ("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check, mismatches) "
           "VALUES (:r, :s, :st, :t, 'other-model', :nc, CAST(:mm AS jsonb))")
    w.rejected(sql, "after the run is completed", r=rid, s=early, st="written", t="x", nc="all_match", mm=None)
    w.complete(rid, "insufficient")
    st = w.stage(rid, "commentator", "commentator", attempt=2)  # the Commentator's stage after completion
    w.rejected(sql, "ck_commentary_mismatches_listed", r=rid, s=st, st="written", t="x", nc="mismatches", mm=None)
    w.rejected(sql, "ck_commentary_written_has_text_and_check", r=rid, s=st, st="written", t=None, nc=None, mm=None)
    w.run_sql(sql, r=rid, s=st, st="written", t="k = 999", nc="mismatches", mm='["999"]')
    w.rejected("UPDATE commentary SET text = 'changed'", "append-only")


# --- files (owner decision: data files only, 5 MiB) ------------------------------------------------------

SOURCE_FILE = "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:sv, :p, :h, :c)"
ARTIFACT = ("INSERT INTO artifact (run_id, kind, filename, media_type, sha256, content) "
            "VALUES (:r, 'workbook', 'run.xlsx', 'application/octet-stream', :h, :c)")


def test_source_files_are_data_files_up_to_5_mib(w):
    sv = w.new_version("mpea", "v2")  # files are added before the version is sealed
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(SOURCE_FILE, sv=sv, p="MPEA_dataset.csv", h=sha(at_limit), c=at_limit)
    w.rejected(SOURCE_FILE, "ck_source_file_max_size", sv=sv, p="big.csv", h=sha(over), c=over)
    w.rejected(SOURCE_FILE, "ck_source_file_data_file_type", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
    w.rejected(SOURCE_FILE, "ck_source_file_sha256_matches_content", sv=sv, p="other.csv", h=sha(b"a"), c=b"b")
    w.run_sql(SOURCE_FILE, sv=sv, p="Grain_Size_Summary_v3.xlsx", h=sha(b"x"), c=b"x")
    w.rejected("UPDATE source_file SET content = 'y'", "append-only")
    w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "only change to a source version is sealing",
               v=sv)
    w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "sealed source version cannot change",
               v=w.version["mpea"])


# --- source versions: sealed files and their interpretation (review finding 4) ------------------------

def test_files_cannot_be_added_after_sealing(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    w.seal(sv)
    with pytest.raises(IntegrityError, match="sealed source version"):
        w.add_file(sv, "b.csv", b"b")


def test_sealing_needs_files_and_the_fingerprint_of_the_file_list(w):
    sv = w.new_version("mpea", "v2")
    with pytest.raises(IntegrityError, match="at least one file"):
        w.seal(sv, fingerprint="0" * 64)
    files = {"b.csv": b"second", "a.csv": b"first"}
    for path, content in files.items():
        w.add_file(sv, path, content)
    with pytest.raises(IntegrityError, match="SHA-256 of the sorted file list"):
        w.seal(sv, fingerprint="0" * 64)
    w.rejected("UPDATE source_version SET sealed_at = now() - interval '1 day', fingerprint = :fp WHERE id = :v",
               "set by the database", v=sv, fp=files_fingerprint(files))
    w.seal(sv)
    assert w.val("SELECT fingerprint FROM source_version WHERE id = :v", v=sv) == files_fingerprint(files)
    with pytest.raises(IntegrityError, match="sealed source version cannot change"):
        w.seal(sv)
    w.rejected("DELETE FROM source_version WHERE id = :v", "never deleted", v=sv)


def test_a_new_version_starts_unsealed(w):
    w.rejected("INSERT INTO source_version (source_id, label, obtained_on, sealed_at, fingerprint) "
               "VALUES (:s, 'v2', '2026-10-05', now(), :fp)", "sealed after its files are added",
               s=w.source["mpea"], fp=FP)


def test_only_a_sealed_version_can_be_used_by_a_run(w):
    unsealed = w.new_version("mpea", "v2")
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.rejected("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
               "VALUES (:r, :s, :sv, 'pending')", "only a sealed source version", r=rid, s=w.source["mpea"],
               sv=unsealed)


def test_a_version_keeps_its_own_interpretation_settings(w):
    """Changing the source's settings affects only versions made afterwards."""
    sv = w.version["mpea"]
    assert w.rows("SELECT source_type, data_kind, grouping_unit FROM source_version WHERE id = :v", v=sv) == [
        ("uploaded_table", "measured", "paper")]
    w.run_sql("UPDATE source SET grouping_unit = 'dataset', data_kind = 'computed', enabled = false WHERE key = 'mpea'")
    assert w.rows("SELECT data_kind, grouping_unit FROM source_version WHERE id = :v", v=sv) == [("measured", "paper")]
    later = w.new_version("mpea", "v2")
    assert w.rows("SELECT data_kind, grouping_unit FROM source_version WHERE id = :v", v=later) == [
        ("computed", "dataset")]
    w.rejected("INSERT INTO source_version (source_id, label, obtained_on, grouping_unit) "
               "VALUES (:s, 'v3', '2026-10-05', 'paper')", "copies its settings from the source", s=w.source["mpea"])
    w.rejected("UPDATE source_version SET grouping_unit = 'dataset' WHERE id = :v", "sealed source version", v=sv)


def test_a_record_has_its_versions_kind_of_data(w):
    rid = w.locked()
    with pytest.raises(IntegrityError, match="kind of data of its source version"):
        w.record(rid, kind="computed")


def test_artifacts_up_to_5_mib(w):
    rid = w.running()
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(ARTIFACT, r=rid, h=sha(at_limit), c=at_limit)
    w.rejected(ARTIFACT, "ck_artifact_max_size", r=rid, h=sha(over), c=over)
    w.rejected(ARTIFACT, "ck_artifact_sha256_matches_content", r=rid, h=sha(b"a"), c=b"b")
    w.rejected("DELETE FROM artifact", "append-only")


# --- fixed lists and the audit log ----------------------------------------------------------------------

def test_domains_are_seeded_and_fixed(w):
    rows = w.rows("SELECT key, supported, profile_name FROM domain ORDER BY id")
    assert rows == [("grain_size_strengthening", True, "grain_size_strengthening"),
                    ("fatigue", False, None), ("other", False, None)]
    w.rejected("UPDATE domain SET supported = true", "append-only")
    w.rejected("INSERT INTO domain (key, name, supported) VALUES ('x', 'X', true)", "ck_domain_supported_has_profile")


def test_the_audit_log_is_append_only(w):
    w.run_sql("INSERT INTO audit_log (role, stage, function, allowed) VALUES ('planner', 'plan', 'counts', true)")
    w.rejected("UPDATE audit_log SET allowed = false", "append-only")
    w.rejected("DELETE FROM audit_log", "append-only")
    w.rejected("TRUNCATE audit_log", "append-only")
```

### `tests/test_migrations.py`

SHA-256 `d45fe0e29a31b860c2ca06e3bc6c8aebbb794bd54a9b15ec3d9a9d94f85a177f`, 11845 bytes.

```python
"""Step 3: migrations. Up, down and up again on an empty database; a failed
upgrade changes nothing; concurrent upgrades are serialized; the command line.

Every test here starts from an empty scratch database, never from the template."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.schema import CreateTable

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.db.models import Base

REPO = Path(__file__).resolve().parents[1]
MIGRATION = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0001").module


def snapshot(engine) -> dict:
    """Everything the migrations create in the public schema, as text, for comparison."""
    queries = {
        "tables": "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public'",
        "columns": """SELECT table_name, column_name, data_type, is_nullable, column_default, is_identity
                      FROM information_schema.columns WHERE table_schema = 'public'""",
        "constraints": """SELECT conrelid::regclass::text, conname, pg_get_constraintdef(c.oid)
                          FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
                          WHERE n.nspname = 'public'""",
        "indexes": "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'",
        "triggers": """SELECT tgrelid::regclass::text, tgname, pg_get_triggerdef(t.oid) FROM pg_trigger t
                       JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
                       WHERE n.nspname = 'public' AND NOT t.tgisinternal""",
        "functions": """SELECT p.proname, pg_get_function_identity_arguments(p.oid), p.prosrc FROM pg_proc p
                        JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public'""",
        "views": "SELECT viewname, definition FROM pg_views WHERE schemaname = 'public'",
        "sequences": "SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'",
        "types": """SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE n.nspname = 'public' AND t.typtype IN ('e', 'd', 'c')
                      AND NOT EXISTS (SELECT 1 FROM pg_class c WHERE c.reltype = t.oid)""",
    }
    with engine.connect() as conn:
        return {k: sorted(tuple(map(str, row)) for row in conn.execute(text(q))) for k, q in queries.items()}


def expected_triggers() -> set[tuple[str, str]]:
    m = MIGRATION
    names = {(t, f"hc_{t}_append_only") for t in m.APPEND_ONLY}
    names |= {(t, f"hc_{t}_no_truncate") for t in m.APPEND_ONLY + m.NO_DELETE + ["hypothesis_version_source"]}
    names |= {(t, f"hc_{t}_no_delete") for t in m.NO_DELETE}
    names |= {(t, f) for t, _, f in m.CHECKED}
    return names


def model_check_names() -> set[str]:
    names = set()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        names |= set(re.findall(r"CONSTRAINT (ck_\w+) CHECK", ddl))
    return names


def assert_schema_is_head(engine):
    with engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []
        db_checks = {r[0] for r in conn.execute(text(
            "SELECT conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
            "WHERE n.nspname = 'public' AND contype = 'c'"))}
        domains = conn.execute(text("SELECT key FROM domain ORDER BY key")).scalars().all()
    assert db_checks == model_check_names()
    s = snapshot(engine)
    assert {(t, n) for t, n, _ in s["triggers"]} == expected_triggers()
    assert {v for v, _ in s["views"]} == set(MIGRATION.VIEW_NAMES)
    assert domains == ["fatigue", "grain_size_strengthening", "other"]
    assert migrate.current_revision(engine) == migrate.head_revision()


def assert_schema_is_empty(engine):
    s = snapshot(engine)
    # Alembic keeps its own bookkeeping table, empty; nothing else may remain.
    assert s["tables"] == [("alembic_version", "BASE TABLE")]
    assert [c for c in s["constraints"] if c[0] != "alembic_version"] == []
    for kind in ("triggers", "functions", "views", "sequences", "types"):
        assert s[kind] == [], kind
    assert migrate.current_revision(engine) is None


# --- revisions ------------------------------------------------------------------------

def test_exactly_one_head_and_every_revision_has_a_downgrade():
    scripts = ScriptDirectory(str(migrate.MIGRATIONS))
    assert len(scripts.get_heads()) == 1
    for rev in scripts.walk_revisions():
        source = Path(rev.path).read_text()
        body = source.split("def downgrade() -> None:", 1)[1]
        assert "drop" in body.lower(), rev.revision


def test_migrations_stay_inside_the_one_transaction():
    """No statement may escape the upgrade transaction (README, 'Database migrations')."""
    env = (migrate.MIGRATIONS / "env.py").read_text()
    assert "transaction_per_migration=False" in env
    assert env.index("pg_advisory_xact_lock") < env.index("context.run_migrations()")
    for path in list((migrate.MIGRATIONS / "versions").glob("*.py")) + [migrate.MIGRATIONS / "script.py.mako"]:
        source = path.read_text()
        docstring = source.split('"""')[1]  # the module docstring states these rules in words
        code = "\n".join(line for line in source.replace(docstring, "").splitlines()
                          if not line.lstrip().startswith("#")).upper()  # comments may say "committed"
        for forbidden in ("CONCURRENTLY", "AUTOCOMMIT_BLOCK", "COMMIT", "VACUUM"):
            assert not re.search(rf"\b{forbidden}\b", code), (path.name, forbidden)


def test_migrations_ship_inside_the_package():
    """The deployed image holds only hypocurate/, data/ and the lock; the migrations are in hypocurate/."""
    assert migrate.MIGRATIONS.is_relative_to(REPO / "hypocurate")
    assert not (REPO / "alembic.ini").exists()


# --- up, down, up -------------------------------------------------------------------------

def test_up_down_up_on_an_empty_database(empty_database):
    engine = make_engine(empty_database)
    try:
        assert snapshot(engine)["tables"] == []
        migrate.upgrade(engine)
        assert_schema_is_head(engine)
        first = snapshot(engine)

        migrate.downgrade(engine, "base")
        assert_schema_is_empty(engine)

        migrate.upgrade(engine)
        assert_schema_is_head(engine)
        assert snapshot(engine) == first
    finally:
        engine.dispose()


def test_upgrade_at_head_changes_nothing(empty_database):
    engine = make_engine(empty_database)
    try:
        migrate.upgrade(engine)
        first = snapshot(engine)
        migrate.upgrade(engine)
        assert snapshot(engine) == first
    finally:
        engine.dispose()


def test_a_failed_upgrade_changes_nothing(empty_database):
    """A table planted under a name the migration creates late makes the upgrade
    fail part-way. The one transaction rolls everything back: no new table,
    function, view or revision."""
    engine = make_engine(empty_database)
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE commentary (planted int)"))
        before = snapshot(engine)
        with pytest.raises(ProgrammingError, match="already exists"):
            migrate.upgrade(engine)
        assert snapshot(engine) == before
        assert migrate.current_revision(engine) is None
    finally:
        engine.dispose()


def test_concurrent_upgrades_run_one_after_the_other(empty_database):
    """Web and worker run the pre-deploy command for the same commit. Both wait on
    the advisory lock (held here first), then one migrates and the other finds the
    database at head. Both exit 0 and the seed rows exist once."""
    engine = make_engine(empty_database)
    env = {**os.environ, "DATABASE_URL": empty_database, "HYPOCURATE_ENV": "development"}
    cmd = [sys.executable, "-m", "hypocurate.db.migrate", "upgrade"]
    try:
        with engine.connect() as holder:
            holder.execute(text("SELECT pg_advisory_lock(:k)"), {"k": migrate.ADVISORY_LOCK_KEY})
            procs = [subprocess.Popen(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True) for _ in range(2)]
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                with engine.connect() as probe:
                    waiting = probe.execute(text(
                        "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")).scalar()
                if waiting == 2:
                    break
                time.sleep(0.2)
            assert waiting == 2, "both upgrades should be waiting on the lock"
            holder.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": migrate.ADVISORY_LOCK_KEY})
            holder.commit()
        results = [p.communicate(timeout=120) + (p.returncode,) for p in procs]
        assert [r[2] for r in results] == [0, 0], [r[1][-2000:] for r in results]
        assert_schema_is_head(engine)
    finally:
        engine.dispose()


# --- command line and status -------------------------------------------------------------------

def test_command_line_upgrade_current_downgrade(empty_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", empty_database)
    monkeypatch.setenv("HYPOCURATE_ENV", "development")
    assert migrate.main(["current"]) == 0
    assert "empty" in capsys.readouterr().out
    assert migrate.main(["upgrade"]) == 0
    assert migrate.main(["current"]) == 0
    assert capsys.readouterr().out.strip().endswith(migrate.head_revision())
    assert migrate.main(["downgrade", "base"]) == 0
    engine = make_engine(empty_database)
    try:
        assert_schema_is_empty(engine)
    finally:
        engine.dispose()


def test_production_downgrade_needs_confirmation(empty_database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", empty_database)
    monkeypatch.setenv("HYPOCURATE_ENV", "production")
    assert migrate.main(["upgrade"]) == 0
    assert migrate.main(["downgrade", "base"]) == 2
    assert "--confirm-data-loss" in capsys.readouterr().err
    engine = make_engine(empty_database)
    try:
        assert migrate.current_revision(engine) == migrate.head_revision()  # nothing was dropped
        assert migrate.main(["downgrade", "base", "--confirm-data-loss"]) == 0
        assert_schema_is_empty(engine)
    finally:
        engine.dispose()


def test_command_line_never_prints_the_database_password(empty_database, monkeypatch, capsys):
    password = make_engine(empty_database).url.password
    monkeypatch.setenv("DATABASE_URL", empty_database)
    migrate.main(["upgrade"])
    migrate.main(["current"])
    out = capsys.readouterr()
    assert password not in out.out and password not in out.err


def test_schema_status(empty_database):
    engine = make_engine(empty_database)
    try:
        assert migrate.schema_status(engine) == {"revision": None, "at_head": False}
        migrate.upgrade(engine)
        assert migrate.schema_status(engine) == {"revision": migrate.head_revision(), "at_head": True}
    finally:
        engine.dispose()
    unreachable = make_engine("postgresql://nobody:planted-pw-7319@127.0.0.1:1/none")
    assert migrate.schema_status(unreachable) == {"revision": None, "at_head": False}
```

### `README.md`

SHA-256 `ee9834b907d9e6a616859a5a27682307d7ee65d2cce8f52320867bbc8da482a7`, 9006 bytes.

````markdown
# hypocurate

[![tests](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml/badge.svg)](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml)

HypoCurate takes a scientific hypothesis in words, searches registered data sources, and reports whether the data in the sources searched are sufficient, partly sufficient or insufficient to test it. The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md); the rules for working on the code are in [CLAUDE.md](CLAUDE.md).

## Status

Build step 3 of 12 (PRD Section 15): the data model. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), plus the tables of PRD Section 7 with the rules the database enforces, and Alembic migrations applied before every deploy. The access layer, the pipeline and the screens come in later steps.

## Set up secrets (once)

```
cp .env.example .env     # then fill in every value; .env is never committed
```

`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`.

## Start the system locally

```
docker compose up --build         # database, web (http://localhost:8000) and worker
```

`/health` needs no login; every other page asks for the shared password. Compose publishes the web service on 127.0.0.1 only, because locally it is plain HTTP. Each service gets only the variables it needs; the worker never sees the login password or the session secret.

In this Codespace, Docker has a leftover firewall rule that blocks traffic between containers. After every Codespace restart, run once:

```
sudo iptables-legacy -I DOCKER-USER -j ACCEPT
```

## Sessions and the login

- A session is a signed cookie holding only `{"signed_in": true}`. It lasts 12 hours. There is no server-side session record.
- **To revoke access, rotate `SESSION_SECRET` together with the password.** Changing the password alone does not end existing sessions. On Render: set a new `HYPOCURATE_PASSWORD` and a new `SESSION_SECRET` on the web service, then redeploy. Every existing session ends.
- Logout clears the cookie in that browser only. A copied cookie keeps working until it expires or the secret is rotated. This is a known limitation of cookie-only sessions, stated in `tests/test_login.py`.
- Failed logins are counted. Every attempt is still checked against the password, and the correct password is never refused by the count, so nobody can lock the owner out. After 5 wrong attempts within 15 minutes, further wrong attempts receive 429 instead of 401 until the window passes. That is all the count does.
- The protection against guessing is a random password of at least 24 characters, generated as above. The configuration enforces the length, not the randomness.

## Run the test suite

The suite needs PostgreSQL; the database tests fail (they never skip) when it is not reachable.

In the same image as the deployed services (this is what GitHub runs at every push):

```
docker compose run --rm test
```

Or in the Codespace's virtual environment:

```
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-dev.lock
.venv/bin/pip install --no-deps -e .
docker compose up -d db
set -a; . ./.env; set +a
.venv/bin/pytest
```

## Dependencies

Direct dependencies are listed in `pyproject.toml`. The exact versions, with hashes, are in `requirements.lock` (runtime) and `requirements-dev.lock` (runtime plus test tools). To change a dependency: edit `pyproject.toml`, then regenerate both locks with pip-tools:

```
.venv/bin/pip install pip-tools
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe -o requirements.lock pyproject.toml
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe --extra dev -o requirements-dev.lock pyproject.toml
```

## Deployment

`render.yaml` describes the Render web service, worker and PostgreSQL database. Render deploys a commit on `main` only after its GitHub checks pass (`autoDeployTrigger: checksPass`).

## Database migrations

The tables are created and changed only by Alembic migrations in `hypocurate/db/migrations/`. The tables and the rules the database enforces are described in `hypocurate/db/models.py`.

```
python -m hypocurate.db.migrate upgrade              # to the latest revision
python -m hypocurate.db.migrate current              # the database's revision
python -m hypocurate.db.migrate downgrade <revision> # drops tables and their data
```

- **On deploy.** Both Render services run `python -m hypocurate.db.migrate upgrade` as their pre-deploy command. It runs after the image is built and before the new version starts. An advisory lock makes the second service wait, after which it finds the schema at the latest revision. `/health` shows the database's revision and whether it is the latest. Locally, `docker compose up` runs the same command in a one-off `migrate` service before web and worker start.
- **If a migration fails.** The whole upgrade is one transaction, so PostgreSQL undoes all of it: no table and no revision change. The command exits non-zero, Render fails the deploy, and the previous version keeps running. Every migration must therefore stay inside that transaction (no `CREATE INDEX CONCURRENTLY`, no `autocommit_block`); a test checks this.
- **Every migration keeps working with the previous release's code** (add first, remove in a later release). Reverting a merge on `main` then deploys the old code safely on the newer schema.
- **Rolling back:**
  1. Preferred: a new migration that undoes the change, deployed the normal way.
  2. Code only: revert the merge on `main`.
  3. Schema: the owner runs `python -m hypocurate.db.migrate downgrade <revision> --confirm-data-loss` in the Render Shell of a service. **This drops tables and their data**; in production it refuses without the flag. Before it, check the backups: Render's point-in-time recovery reaches back 3 days on the Hobby workspace and restores into a *new* database, which costs money.
- **What the database enforces, and its limits.**
  - Triggers and CHECK constraints refuse, among others: editing a locked plan; changing a frozen dataset; freezing a primary set that leaves out an eligible record; updating or deleting a record; extracting before the rules lock; any curation once a run has ended; adding files to a sealed source version; and a verdict on a run that is not sufficient. A refusal raises an error starting `hypocurate:`.
  - **Locking.** Every trigger that checks or changes a run's state first locks that run's row; triggers on chosen sources and on dispatch lock the hypothesis version first (lock order: version, then run). A transaction that writes to a run therefore makes every other writer to that run wait until it commits, so long transactions on a run should be avoided.
  - **After a run ends.** On a completed run only the commentary, the Commentator's stage and model calls, and artifacts may still be written; on a failed run only the audit log.
  - **Validity checks.** The CHECKs on `analysis_result` are necessary conditions on the stored counts, not the full validity rules of PRD 5.7. Those, and the agreement of the verdict with the pooled result, are computed and tested in step 7.
  - The triggers stop the application and ordinary edits. The database owner can still drop a trigger, so they are not tamper-proof; the fingerprints are the cross-check.
- **Tests never touch the database at `DATABASE_URL`.** They create scratch databases (`hypocurate_t_…`, from a template migrated once per session) and drop them afterwards. The database user must be allowed to create databases (the local and CI containers' user is).

## Data

| Path | What it is |
|---|---|
| `data/manifest.json` | Fingerprint (SHA-256), size, licence, origin and retrieval date of every frozen file |
| `data/sources/mpea/` | MPEA dataset (Borg et al. 2020), Apache-2.0 |
| `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT |
| `data/controlled_duplicates/` | Constructed extract for testing duplicate detection; see its README |

To check that the origins still serve the same bytes (needs network; never overwrites the frozen copies):

```
.venv/bin/python scripts/fetch_sources.py            # pinned GitHub files
.venv/bin/python scripts/fetch_sources.py --zenodo   # also the Zenodo archive (about 49 MB)
```
````

## 4. Test output

```
$ .venv/bin/pytest -v tests/test_concurrency.py tests/test_data_model.py tests/test_migrations.py
tests/test_concurrency.py::test_member_first_then_freeze_counts_it PASSED
tests/test_concurrency.py::test_freeze_first_then_flag_is_rejected PASSED
tests/test_concurrency.py::test_freeze_first_then_sensitivity_member_is_rejected PASSED
tests/test_concurrency.py::test_source_first_then_submission_includes_it PASSED
tests/test_concurrency.py::test_submission_first_then_source_is_rejected PASSED
tests/test_concurrency.py::test_dispatch_metadata_first_then_start_waits PASSED
tests/test_concurrency.py::test_start_first_then_dispatch_metadata_is_rejected PASSED
tests/test_concurrency.py::test_flag_first_then_completion_waits PASSED
tests/test_concurrency.py::test_completion_first_then_flag_is_rejected PASSED
tests/test_concurrency.py::test_completion_first_then_search_result_is_rejected PASSED
tests/test_concurrency.py::test_no_dataset_first_then_freeze_is_rejected PASSED
tests/test_concurrency.py::test_freeze_first_then_no_dataset_is_rejected PASSED
tests/test_concurrency.py::test_file_first_then_sealing_includes_it PASSED
tests/test_concurrency.py::test_sealing_first_then_file_is_rejected PASSED
tests/test_data_model.py::test_query_numbers_come_from_a_sequence PASSED
tests/test_data_model.py::test_a_new_version_starts_as_an_unreviewed_draft PASSED
tests/test_data_model.py::test_a_submitted_version_cannot_be_edited PASSED
tests/test_data_model.py::test_an_edit_is_a_new_version_of_the_same_query PASSED
tests/test_data_model.py::test_version_status_moves_only_forward[draft-dispatched] PASSED
tests/test_data_model.py::test_version_status_moves_only_forward[draft-returned] PASSED
tests/test_data_model.py::test_version_status_moves_only_forward[submitted-draft] PASSED
tests/test_data_model.py::test_version_status_moves_only_forward[returned-submitted] PASSED
tests/test_data_model.py::test_version_status_moves_only_forward[dispatched-submitted] PASSED
tests/test_data_model.py::test_return_for_edits_with_a_comment PASSED
tests/test_data_model.py::test_chosen_sources_change_only_in_draft PASSED
tests/test_data_model.py::test_reviewer_confirms_the_domain_only_while_submitted PASSED
tests/test_data_model.py::test_dispatch_is_blocked_for_an_unsupported_domain PASSED
tests/test_data_model.py::test_a_run_needs_a_dispatched_version PASSED
tests/test_data_model.py::test_queries_versions_and_runs_are_never_deleted[hypothesis] PASSED
tests/test_data_model.py::test_queries_versions_and_runs_are_never_deleted[hypothesis_version] PASSED
tests/test_data_model.py::test_queries_versions_and_runs_are_never_deleted[run] PASSED
tests/test_data_model.py::test_narrower_question_links_only_to_a_partly_sufficient_run PASSED
tests/test_data_model.py::test_a_partly_sufficient_run_has_no_verdict PASSED
tests/test_data_model.py::test_narrower_question_has_the_original_domain PASSED
tests/test_data_model.py::test_narrower_question_goes_through_review_and_dispatch PASSED
tests/test_data_model.py::test_a_run_starts_queued PASSED
tests/test_data_model.py::test_run_status_moves_only_forward[UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r] PASSED
tests/test_data_model.py::test_run_status_moves_only_forward[UPDATE run SET status = 'queued' WHERE id = :r] PASSED
tests/test_data_model.py::test_completed_and_failed_runs_are_final[completed] PASSED
tests/test_data_model.py::test_completed_and_failed_runs_are_final[failed] PASSED
tests/test_data_model.py::test_what_a_run_records_at_dispatch_cannot_change PASSED
tests/test_data_model.py::test_a_failed_run_states_its_reason PASSED
tests/test_data_model.py::test_verdict_if_and_only_if_sufficient[sufficient-None] PASSED
tests/test_data_model.py::test_verdict_if_and_only_if_sufficient[insufficient-supported] PASSED
tests/test_data_model.py::test_verdict_if_and_only_if_sufficient[partly_sufficient-not_supported] PASSED
tests/test_data_model.py::test_a_running_run_has_no_outcome_or_verdict PASSED
tests/test_data_model.py::test_sufficient_needs_a_pooled_result_that_passed_both_checks PASSED
tests/test_data_model.py::test_coefficient_only_completes_as_insufficient_without_a_verdict PASSED
tests/test_data_model.py::test_other_endings_need_no_pooled_result[insufficient] PASSED
tests/test_data_model.py::test_other_endings_need_no_pooled_result[partly_sufficient] PASSED
tests/test_data_model.py::test_other_endings_need_no_pooled_result[failed] PASSED
tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met PASSED
tests/test_data_model.py::test_exploratory_means_use_available_and_minimums_not_met[False-True] PASSED
tests/test_data_model.py::test_exploratory_means_use_available_and_minimums_not_met[True-False] PASSED
tests/test_data_model.py::test_exploratory_only_with_a_verdict PASSED
tests/test_data_model.py::test_a_locked_plan_cannot_change PASSED
tests/test_data_model.py::test_a_plan_is_locked_only_while_the_run_is_running PASSED
tests/test_data_model.py::test_the_lock_time_is_the_database_time PASSED
tests/test_data_model.py::test_sensitivity_analysis_keys[keys0-ck_plan_primary_not_sensitivity] PASSED
tests/test_data_model.py::test_sensitivity_analysis_keys[keys1-must be unique] PASSED
tests/test_data_model.py::test_sensitivity_analysis_keys[keys2-lowercase names] PASSED
tests/test_data_model.py::test_sufficiency_option_and_minimums[power_based-mins0-ck_plan_sufficiency_option] PASSED
tests/test_data_model.py::test_sufficiency_option_and_minimums[fixed_minimum-mins1-ck_plan_minimums_positive] PASSED
tests/test_data_model.py::test_sufficiency_option_and_minimums[use_available-mins2-ck_plan_minimums_positive] PASSED
tests/test_data_model.py::test_power_assumptions_are_an_information_field PASSED
tests/test_data_model.py::test_plan_fingerprint_format PASSED
tests/test_data_model.py::test_tags_are_written_in_the_lock_transaction_only PASSED
tests/test_data_model.py::test_a_proposed_tag_value_is_decided_once PASSED
tests/test_data_model.py::test_a_rejected_tag_value_cannot_be_attached PASSED
tests/test_data_model.py::test_tag_kinds_are_a_fixed_list PASSED
tests/test_data_model.py::test_agent_settings_are_versioned_and_append_only PASSED
tests/test_data_model.py::test_agent_settings_versions_are_recorded_at_dispatch PASSED
tests/test_data_model.py::test_a_run_source_starts_undecided PASSED
tests/test_data_model.py::test_a_failed_source_is_always_failed_search[failed-None-timeout-ck_run_source_failed_iff_failed_search] PASSED
tests/test_data_model.py::test_a_failed_source_is_always_failed_search[failed-missing_evidence-timeout-ck_run_source_failed_iff_failed_search] PASSED
tests/test_data_model.py::test_a_failed_source_is_always_failed_search[searched-failed_search-None-ck_run_source_failed_iff_failed_search] PASSED
tests/test_data_model.py::test_a_failed_source_is_always_failed_search[failed-failed_search-None-ck_run_source_failed_has_reason] PASSED
tests/test_data_model.py::test_a_decided_run_source_is_final PASSED
tests/test_data_model.py::test_the_source_version_of_a_run_cannot_change PASSED
tests/test_data_model.py::test_a_failed_source_is_never_missing_evidence PASSED
tests/test_data_model.py::test_mixed_results_are_reported_per_category PASSED
tests/test_data_model.py::test_every_selected_source_failing_shows_no_source_searched PASSED
tests/test_data_model.py::test_records_found_is_its_own_category PASSED
tests/test_data_model.py::test_coverage_comes_from_the_runs_own_dispatch_rows PASSED
tests/test_data_model.py::test_a_run_starts_only_with_its_full_source_inventory PASSED
tests/test_data_model.py::test_no_table_stores_a_run_level_nothing_found PASSED
tests/test_data_model.py::test_records_are_never_updated_or_deleted PASSED
tests/test_data_model.py::test_a_record_comes_from_a_source_version_its_run_recorded PASSED
tests/test_data_model.py::test_records_are_extracted_while_running_and_before_the_freeze PASSED
tests/test_data_model.py::test_every_record_names_its_origin PASSED
tests/test_data_model.py::test_records_and_eligibility_come_after_the_rules_lock PASSED
tests/test_data_model.py::test_a_run_decides_only_on_its_own_records PASSED
tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible PASSED
tests/test_data_model.py::test_a_set_exists_only_for_an_analysis_the_locked_plan_names PASSED
tests/test_data_model.py::test_primary_holds_only_eligible_records_and_sensitivity_sets_may_hold_others PASSED
tests/test_data_model.py::test_a_possible_duplicate_counts_once_in_primary_and_twice_in_its_sensitivity_set PASSED
tests/test_data_model.py::test_nothing_changes_after_the_freeze PASSED
tests/test_data_model.py::test_the_freeze_rejects_a_primary_set_that_omits_eligible_records PASSED
tests/test_data_model.py::test_the_freeze_rejects_an_undecided_record PASSED
tests/test_data_model.py::test_no_eligible_records_means_no_freeze PASSED
tests/test_data_model.py::test_the_freeze_matches_the_primary_set_and_needs_every_named_set PASSED
tests/test_data_model.py::test_no_curation_once_the_run_has_ended[completed] PASSED
tests/test_data_model.py::test_no_curation_once_the_run_has_ended[failed] PASSED
tests/test_data_model.py::test_a_record_extracted_after_the_freeze_cannot_slip_in_after_the_run_ends PASSED
tests/test_data_model.py::test_no_dataset_frozen_and_a_freeze_exclude_each_other PASSED
tests/test_data_model.py::test_what_may_be_written_after_completion PASSED
tests/test_data_model.py::test_nothing_but_the_audit_log_after_failure PASSED
tests/test_data_model.py::test_a_run_ends_only_with_no_stage_running_and_no_call_open[completed] PASSED
tests/test_data_model.py::test_a_run_ends_only_with_no_stage_running_and_no_call_open[failed] PASSED
tests/test_data_model.py::test_a_flag_is_classified_once_before_the_freeze PASSED
tests/test_data_model.py::test_flags_stop_at_the_freeze PASSED
tests/test_data_model.py::test_a_flag_names_records_of_its_own_run PASSED
tests/test_data_model.py::test_results_come_after_the_freeze PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[check2_passed-true-ck_analysis_result_check2_consistent] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[std_error-1.0-ck_analysis_result_std_error_iff_check2] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[p_value-0.01-ck_analysis_result_p_value_iff_check2] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[resid_df-5-ck_analysis_result_resid_df_definition] PASSED
tests/test_data_model.py::test_check_one_failing_means_no_estimate PASSED
tests/test_data_model.py::test_stored_counts_must_be_consistent[1-1-1-ck_analysis_result_two_records_per_alloy] PASSED
tests/test_data_model.py::test_stored_counts_must_be_consistent[4-1-5-ck_analysis_result_groups_within_records] PASSED
tests/test_data_model.py::test_stored_counts_must_be_consistent[4-0-0-ck_analysis_result_records_have_a_group] PASSED
tests/test_data_model.py::test_stored_counts_must_be_consistent[4-2-2-cannot exceed the distinct alloys] PASSED
tests/test_data_model.py::test_one_result_per_run_and_scope_on_the_right_set PASSED
tests/test_data_model.py::test_counts_must_match_the_set_used PASSED
tests/test_data_model.py::test_minimums_met_must_agree_with_the_plan PASSED
tests/test_data_model.py::test_calibration_is_computed_exactly_when_inference_is_valid PASSED
tests/test_data_model.py::test_calibration_unavailable_states_a_matching_reason PASSED
tests/test_data_model.py::test_run_level_calibration_only_when_no_dataset_was_frozen PASSED
tests/test_data_model.py::test_calibration_intervals_contain_their_share PASSED
tests/test_data_model.py::test_a_model_call_is_recorded_before_the_request_and_finished_once PASSED
tests/test_data_model.py::test_model_call_usage_rules PASSED
tests/test_data_model.py::test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound PASSED
tests/test_data_model.py::test_small_costs_are_stored_exactly PASSED
tests/test_data_model.py::test_call_times_are_set_by_the_database PASSED
tests/test_data_model.py::test_a_run_without_calls_totals_zero PASSED
tests/test_data_model.py::test_no_table_stores_token_or_cost_totals PASSED
tests/test_data_model.py::test_a_finished_stage_result_is_final PASSED
tests/test_data_model.py::test_commentary_comes_after_completion_and_lists_mismatches PASSED
tests/test_data_model.py::test_source_files_are_data_files_up_to_5_mib PASSED
tests/test_data_model.py::test_files_cannot_be_added_after_sealing PASSED
tests/test_data_model.py::test_sealing_needs_files_and_the_fingerprint_of_the_file_list PASSED
tests/test_data_model.py::test_a_new_version_starts_unsealed PASSED
tests/test_data_model.py::test_only_a_sealed_version_can_be_used_by_a_run PASSED
tests/test_data_model.py::test_a_version_keeps_its_own_interpretation_settings PASSED
tests/test_data_model.py::test_a_record_has_its_versions_kind_of_data PASSED
tests/test_data_model.py::test_artifacts_up_to_5_mib PASSED
tests/test_data_model.py::test_domains_are_seeded_and_fixed PASSED
tests/test_data_model.py::test_the_audit_log_is_append_only PASSED
tests/test_migrations.py::test_exactly_one_head_and_every_revision_has_a_downgrade PASSED
tests/test_migrations.py::test_migrations_stay_inside_the_one_transaction PASSED
tests/test_migrations.py::test_migrations_ship_inside_the_package PASSED
tests/test_migrations.py::test_up_down_up_on_an_empty_database PASSED
tests/test_migrations.py::test_upgrade_at_head_changes_nothing PASSED
tests/test_migrations.py::test_a_failed_upgrade_changes_nothing PASSED
tests/test_migrations.py::test_concurrent_upgrades_run_one_after_the_other PASSED
tests/test_migrations.py::test_command_line_upgrade_current_downgrade PASSED
tests/test_migrations.py::test_production_downgrade_needs_confirmation PASSED
tests/test_migrations.py::test_command_line_never_prints_the_database_password PASSED
tests/test_migrations.py::test_schema_status PASSED
============================= 159 passed in 43.40s =============================

$ .venv/bin/pytest -q   (whole suite)
353 passed in 46.96s

$ docker compose run --rm test
353 passed in 47.00s

With the run lock removed from hc_lock_run (temporary copy, restored): 10 failed, 4 passed (all 10 run-level races).
With the version and source-file locks removed (temporary copy, restored): 3 failed, 11 passed; test_file_first_then_sealing_includes_it
is serialized by the foreign-key lock (fingerprint is in a unique key), so its outcome is correct either way.
```
