# Build step 3 — summary for review

Date: 2026-10-05. Branch: `step-03-data-model`. **Status: signed off by the second model's second re-check (2026-10-05): all findings closed, "Step 3 can be merged and its migration run on the live database". Merged into `main` (`427c1a3`, 2026-10-05) and **live on Render**: the pre-deploy migration ran on both services and live `/health` shows schema `0001` at head (see "Live deployment"). Migration 0001 is frozen from this merge on.** PRD Section 15, step 3: "Data model. Tables and migrations from Section 7."

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

## The locking protocol (review finding 1; corrected after the re-check)

**The lock order is version, then run, then the run's child rows. It is established for paths that follow the protocol below, not by the child-row triggers alone.** The first fix round said the triggers established it. The re-check showed they do not, and I tested its counter-example.

- **The protocol, for application code** (all write paths, from step 4 on):
  - Every transaction that will write to a run or any of its child rows first calls `SELECT hc_write_lock(p_run => <run id>)`.
  - Every transaction that will change a version's chosen sources, submit it or dispatch it first calls `SELECT hc_write_lock(p_version => <version id>)`.
  - `hc_write_lock` locks the version, then the run (`FOR NO KEY UPDATE`), and returns the status. It rejects an unknown run or version, and a run that does not belong to the given version.
- **The triggers.**
  - Every trigger that checks or changes a run's state calls `hc_lock_run(run_id)`, which locks the row and returns its latest committed status in one statement. Updates of the run row take the same lock themselves.
  - Triggers on chosen sources and on dispatch call `hc_lock_version`. A `source_file` insert locks its version row; sealing is an update of that row.
  - This makes every state check race-free (the checkpoint tests).
- **Why the triggers are not enough.** An UPDATE of a child row (a stage result, a model call, a run source, a flag) locks that row *before* its trigger asks for the run lock. So:
  1. A holds the run lock;
  2. B updates a child row and waits for the run;
  3. A updates the same child row.
  
  That is a deadlock. `test_skipping_the_protocol_can_deadlock` reproduces it: PostgreSQL aborts exactly one of the two transactions, and nothing of the aborted one is written. `test_following_the_protocol_does_not_deadlock` runs the same interleaving with B calling `hc_write_lock` first. B then waits before touching the child row, A writes and commits, and B writes after it, with no error. `test_following_the_protocol_on_model_calls_does_not_deadlock` does the same for finishing a model call.
- **Retries.** A path that skips the protocol, or any multi-row pattern not covered by it, may get SQLSTATE `40P01` (deadlock) or `40001` (serialization failure). The caller must retry the whole transaction.
- **Consequence:** a transaction holding a run's lock makes every other writer to that run, including a worker's heartbeat update, wait until it commits. Step 9 should keep transactions on a run short (open item 2).

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
   - The row is inserted **before** the request (`started`), with `max_cost` > 0 as the upper bound. `max_cost` and `cost` must be finite: NaN and ±Infinity are rejected (re-check item 3). It is finished exactly once: `succeeded` (all four usage values), `failed` (all four or none), or `interrupted` (none).
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
    - `source_file` and `artifact`: at most 5 MiB, and `sha256` must match the bytes.
    - A source file's path must match `^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$`: a safe character set, anchored at both ends, with no line break (re-check item 2). So the 49 MB Zenodo archive cannot be stored.
    - A `source_version` **copies `source_type`, `data_kind` and `grouping_unit`** from its source at insert; a different caller-supplied value is rejected. Changing `source` afterwards affects only later versions. Operational settings stay mutable on `source`: enabled, adapter status, address, licence, properties.
    - Files are added, then the version is **sealed once**:
      - the database sets `sealed_at`;
      - at least one file is required;
      - the database sets `files_digest` to the SHA-256 of the sorted file list, one line `<sha256>  <path>\n` per file, sorted bytewise by path (owner, 2026-10-05). Paths hold no line break, so the list is unambiguous;
      - the database requires `fingerprint`, the version's **identity** (unique per source), to equal the SHA-256 of four lines: `files <files_digest>`, `source_type <…>`, `data_kind <…>` and `grouping_unit <…>`, each ending in `\n` (re-check item 2). The same files under corrected settings therefore seal as a new version, while identical files and settings are rejected as a duplicate. Step 4 computes both values the same way.
      
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
- A stage result's run, stage name, attempt and **role** never change (re-check item 4), so a Commentator stage on a completed run cannot be relabelled.

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
    - a source version copies the settings that change how records are read, and is sealed once. The database computes its files digest and checks its identity: the digest plus the interpretation settings;
    - only sealed versions are used.
13. **PRD 5.8 and 9.2:** power-based sufficiency is not an option in sprint 1. It is an "estimated power report (information only)"; as a gate it stays in the backlog.
14. **PRD 8 (new):** what may be written to a run in each state, as in the table above. After completion: commentary, the Commentator's stage and calls, and artifacts. After failure: only the audit log. A run ends only with no stage running and no call open.

## Re-check (ChatGPT, 2026-10-05) and fixes

The re-check text is in `docs/reviews/step03_recheck_chatgpt.md`. Its verdict on each finding:

| Finding | Re-check status |
|---|---|
| 1. Locking protocol | partly closed: a parent/child deadlock path remained |
| 2. Exact primary set at freeze | closed |
| 3. Lifecycle and post-completion writes | partly closed: a Commentator stage's role could still change |
| 4. Source sealing and fingerprint | partly closed: ambiguous file-list encoding; interpretation-only revisions could not be sealed |
| 5. Validity-check wording | closed |
| 6. Search coverage | closed |
| 7. Costs | partly closed: NaN and Infinity were accepted |

The four remaining items, fixed in migration 0001 in place (owner's instruction), one commit each:
1. **Lock order** (`bd6f39a`).
   - **Fix:** `hc_write_lock(p_run, p_version)` and the protocol (section "The locking protocol"). The claim is corrected: the order holds for paths that follow the protocol, not by the child-row triggers alone. Retries on `40P01` and `40001` are documented, and all write paths from step 4 on must use the helper (open item 3).
   - **Tests:**
     - `test_skipping_the_protocol_can_deadlock` reproduces the review's interleaving; exactly one transaction is aborted;
     - `test_following_the_protocol_does_not_deadlock` and `test_following_the_protocol_on_model_calls_does_not_deadlock`: the same interleaving with the protocol completes without error;
     - `test_write_lock_locks_a_run_or_a_version`.
2. **Source fingerprints** (`c09176e`).
   - **Fix:** (a) safe, anchored file paths, so no line break is possible; (b) `files_digest` plus `fingerprint` as the version's identity, covering the digest and the interpretation settings.
   - **Tests:**
     - `test_unsafe_file_paths_are_rejected` (8 cases, including the review's line-break collision);
     - `test_the_same_files_under_revised_settings_seal_as_a_new_version`: the same files with a corrected grouping unit seal as a second version, and identical files and settings are rejected as a duplicate.
3. **Finite costs** (`1ea2850`).
   - **Fix:** CHECK `money_finite`.
   - **Tests:** `test_max_cost_must_be_finite` and `test_reported_cost_must_be_finite` (NaN, Infinity, -Infinity each).
4. **Stage role** (`f3e8f71`).
   - **Fix:** `hc_stage_result_update` freezes the role with the stage name.
   - **Tests:** `test_a_commentator_stage_cannot_be_relabelled` (with and without finishing the stage in the same update; to `planner` and to NULL); `test_a_running_stage_cannot_be_relabelled`.

## Second re-check (ChatGPT, 2026-10-05): sign-off

The text is in `docs/reviews/step03_recheck2_chatgpt.md`. All four re-check items are closed: lock order, source fingerprints, finite costs, frozen stage role. "No new result-corruption or live-database blocker found." Its two notes for later steps are open items 3 and 4 below.

## Tests (375, all passing; 187 for step 3; the 93 from step 1 and the login tests unchanged)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data tests/test_login.py tests/test_login_throttle.py` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_data_model.py` (new) | 153 | Every rule above, each with an allowed case and a rejected case, on a fresh migrated scratch database |
| `tests/test_concurrency.py` (new) | 17 | Two-connection races for the locking protocol (finding 1), and the deadlock interleaving with and without the protocol (re-check item 1) |
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

Re-check round (no test removed):
- `test_source_files_are_data_files_up_to_5_mib`: the `.zip` case now expects `ck_source_file_safe_data_file_path`, which replaces `ck_source_file_data_file_type` (the pattern is stricter).
- `test_sealing_needs_files_and_the_fingerprint_of_the_file_list`:
  - the wrong-fingerprint case expects the new message, which names the files digest and the settings;
  - it now also checks that the digest and the identity are both stored;
  - a new case rejects a wrong caller-supplied `files_digest`.
- `tests/test_concurrency.py`: the two sealing races compute the version's fingerprint with the new identity (`w.fingerprint`); their assertions are unchanged.

### Suite results
```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, `docker compose up -d db`)
375 passed in 52.72s
$ docker compose run --rm test           (the test image)
375 passed in 52.79s
GitHub Actions, commit f3e8f71 (last code change, re-check round): success; "Run the suite in the test image": 375 passed.
https://github.com/kelawady/hypocurate/actions/runs/37251807075
GitHub Actions, commit e253950 (first fix round): success; 353 passed.
https://github.com/kelawady/hypocurate/actions/runs/37250072104
```
The `ERROR: hypocurate: …` lines in the CI log's database output are the refusals the tests provoke on purpose.

Local checks beyond the suite:
- `docker compose up -d`: `migrate` exited 0 ("schema at 0001"), and `/health` reported `"schema":{"revision":"0001","at_head":true}`.
- The local database has `run_search_coverage` and 42 functions. It was reset again in the re-check round (no rows; production never migrated), because 0001 changed again.

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

## Live deployment (2026-10-05)

**Merge:** `step-03-data-model` into `main` with `--no-ff` (`427c1a3`), after the branch run was green (https://github.com/kelawady/hypocurate/actions/runs/37252572320, 375 passed). The suite also passed on `main` locally (375), and `main`'s run was green (https://github.com/kelawady/hypocurate/actions/runs/37252769426; started 01:46:49 UTC, passed 01:48:08 UTC). Times below are UTC; the owner's dashboard shows UTC−7.

| Check | How | Result |
|---|---|---|
| Live `/health` before the merge | `curl` | `version` `68ba1c4…`, no `schema` field (step 2 code) |
| Pre-deploy setting, web | Owner: `hypocurate-web` → Settings → Deploy | Pre-Deploy Command `python -m hypocurate.db.migrate upgrade`; Docker Command empty (the Dockerfile's default, uvicorn); Auto-Deploy "After CI Checks Pass" |
| Pre-deploy setting, worker | Owner: `hypocurate-worker` → Settings → Deploy | Pre-Deploy Command `python -m hypocurate.db.migrate upgrade`; Docker Command `python -m hypocurate.worker`; Auto-Deploy "After CI Checks Pass" |
| Pre-deploy ran, web | Owner: the web service's log (screenshot) | 01:48:42 `Starting pre-deploy: python -m hypocurate.db.migrate upgrade`; 01:48:49 `schema at 0001`; 01:48:53 `Pre-deploy complete!`; new instance started 01:49:02; `Your service is live` 01:49:05. The old instance answered `/health` throughout. |
| Pre-deploy ran, worker | Owner: the worker's log (screenshot) | 01:48:43 `Starting pre-deploy`; 01:48:50 `schema at 0001`; 01:48:53 `Pre-deploy complete!`; `Your service is live` 01:49:00; the new worker logs "database reachable". |
| Live `/health` after | `curl`, 01:49:35 | `{"web":"ok","database":"ok","version":"427c1a3…","schema":{"revision":"0001","at_head":true}}`; the HTML page shows "Schema `0001` (latest)" |
| Login still required | `curl` | `/` → 303 to `/login`; `/health/export` → 303 |

The two "schema at 0001" lines do not show which service applied the migration and which found it already at head; the advisory lock serialized them and both exited 0.

**A failed deploy before the successful one (worker; not changed or retried).** At 01:46:52, three seconds after the push and **before the GitHub check had passed**, the worker started a pre-deploy that failed:
- `/usr/local/bin/python: No module named hypocurate.db.migrate`
- `Pre-deploy has failed`
- `Exited with status 1`

The old worker kept running (it logged at 01:47:30 and 01:48:30), and nothing reached the database.

My reading: because `render.yaml` changed, Render's Blueprint sync applied the new `preDeployCommand` as soon as the push landed. It then redeployed the commit already running, `68ba1c4`, which has no `hypocurate.db.migrate`. Render documents that a Blueprint update redeploys affected services, and that a failed pre-deploy keeps the previous deploy running.

Two consequences, for later steps:
- **The `checksPass` gate does not cover Blueprint-sync redeploys of the commit already running.** A settings change can therefore run against old code before the check passes.
- **Next time,** deploy code that a new setting depends on in one merge, and add the setting in a later one.

The owner did not send the web service's events for 01:46, so whether web also had this failed redeploy was not checked; its log screenshot starts at 01:48:21.

## Open items
1. **Live check after merge: done** (see "Live deployment"). Follow-up for later steps: a `render.yaml` change is applied by the Blueprint sync before the `checksPass` gate, as a redeploy of the code already running. Put settings that depend on new code in a later merge than the code.
2. **Lock contention (step 9).** A long transaction on a run holds its lock; a heartbeat update of the same run waits until it commits. Keep checkpoint transactions short, or move heartbeats to their own table if that proves a problem.
3. **Step 4 onwards: every real write path follows the locking protocol** (second re-check, note 1). It calls `hc_write_lock` first and retries the whole transaction on `40P01` or `40001`; code review of each later step checks this.
   - The deadlock-free claim is scoped to **single-run transactions** that follow the protocol.
   - A transaction that writes to more than one run needs an additional ordering rule. My proposal for the step that first needs one: lock all versions first, then all runs, each in ascending id order, through `hc_write_lock`, before any child write. To be decided and tested then.
4. **Before any stored path is written to disk, check that it stays inside its target directory** (second re-check, note 2). The safe character pattern still allows `a/../../outside.csv`. Whichever step first writes source files or artifacts to disk must resolve each path and reject any that leaves the directory, with a test for that path.
5. **Step 4** computes the source-version files digest and identity as defined above, seals every version before use, and loads the two frozen sources. The source file paths stored must match the safe pattern.
6. **Step 6:** each run has a property, alloy-class and test-condition tag; duplicate handling (the duplicate test shows storage only).
7. **Step 7 and step 9 requirements** are listed above.
8. Storage estimate (about 4–6 MB per run, 120–200 runs in 1 GB), to be measured in step 8.
9. The test database user must be allowed to create databases. The tests never run against Render.
10. Source registration's "access key" (PRD 9.6) has no column; secrets stay in environment variables.
11. Carried from step 2, unchanged: the pooled p-value 7.4e-7 against "≈ 8e-7" (step 7); permitted test types and a non-MPEA survivor pair (step 6); the access layer must enforce the approved file list (step 5).
