# Build step 3 — summary for review

Date: 2026-10-05. Branch: `step-03-data-model`. **Status: built and green on GitHub; awaiting the second-model review and the owner's sign-off. Not merged, not deployed.** PRD Section 15, step 3: "Data model. Tables and migrations from Section 7."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`. The plan was approved by the owner on 2026-10-04/05, with decisions on seven questions and four additions (listed below).

Not built, as instructed: the access layer, any agent, any pipeline or statistics code, any screen, and loading the frozen sources into the tables.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/db/models.py` | SQLAlchemy 2 models, one class per table (list below), with every CHECK constraint. A naming convention fixes constraint names, so tests and errors can name them. |
| `hypocurate/db/migrations/versions/0001_data_model.py` | The one migration: tables, CHECKs, a sequence for query numbers, plpgsql trigger functions and triggers, five views, and the three domain rows. The `CREATE TABLE` statements were **rendered by Alembic autogenerate from the models, then reviewed and edited by hand**: the sequence was added, the hypothesis → run foreign key moved after `run`, and one name over 63 characters shortened. The functions, triggers, views and seed rows are hand-written. The migration does not import the models. |
| `hypocurate/db/migrations/env.py`, `script.py.mako` | Online mode only. One transaction for the whole upgrade (`transaction_per_migration=False`). It takes `pg_advisory_xact_lock` before Alembic reads the current revision. |
| `hypocurate/db/migrate.py` | `python -m hypocurate.db.migrate upgrade \| current \| downgrade <rev> [--confirm-data-loss]`. The Alembic configuration is built in code (no `alembic.ini`), so the deployed image's top level stays `hypocurate`, `data`, `requirements.lock`. The engine is passed as an object, never as a URL string. In production, `downgrade` exits 2 without `--confirm-data-loss`. `schema_status()` serves `/health`. |
| `render.yaml` | `preDeployCommand: python -m hypocurate.db.migrate upgrade` on **both** `hypocurate-web` and `hypocurate-worker`. |
| `docker-compose.yml` | A one-off `migrate` service (runtime image, the same command, only `HYPOCURATE_ENV` and `DATABASE_URL`). `web` and `worker` wait for it with `service_completed_successfully`. CI's existing Compose step therefore runs the migration in the runtime image. **No change to `.github/workflows/`.** |
| `/health` (`web/app.py`, `health.html`) | Adds `schema: {"revision", "at_head"}`. Informational: it never changes the status code. When the database is down it reports `{null, false}` without a second connection attempt. |
| `scripts/check_runtime_image.py` | `REQUIRED` also lists `migrate.py`, `migrations/env.py` and `versions/0001_data_model.py`. |
| `pyproject.toml`, locks | `alembic>=1.16` added. The locks gained exactly `alembic==1.20.0` and `mako==1.4.3`, with hashes; nothing else changed. |
| `README.md` | New "Database migrations" section (apply, failure, rollback, limits). |

### Tables
`domain`, `tag_value`, `source`, `source_version`, `source_file`, `agent_setting`, `hypothesis`, `hypothesis_version`, `hypothesis_version_source`, `run`, `plan`, `run_tag`, `run_agent_setting`, `run_source`, `run_snapshot`, `stage_result`, `model_call`, `record`, `run_record`, `analysis_set`, `analysis_set_record`, `flag`, `flag_record`, `analysis_result`, `calibration_result`, `commentary`, `artifact`, `audit_log`.

Views: `run_nothing_found`, `model_call_totals_by_stage`, `_by_run`, `_by_query`, `_by_month`.

## The deploy questions (owner's request)

1. **How migrations are applied on deploy.**
   - Render runs the pre-deploy command after the build and before the new version starts, on a separate instance (render.com/docs/deploys, checked 2026-10-04).
   - Both services run it for the same commit. The advisory lock makes the second wait; it then finds the schema at head and does nothing.
   - Locally and in CI, the Compose `migrate` service does the same.
2. **If a migration fails mid-deploy.**
   - The upgrade is one PostgreSQL transaction, so a failure rolls back everything: tables, functions, views, seed rows and `alembic_version`.
   - The command exits non-zero, Render fails the deploy, and the previous version keeps running (Render docs: "Your service continues running its most recent successful deploy").
   - Proven by `test_a_failed_upgrade_changes_nothing`, which plants a `commentary` table so the upgrade fails late, and checks that the whole schema snapshot is unchanged.
3. **How a migration is rolled back** (README):
   - (a) Preferred: a new migration that undoes the change.
   - (b) Revert the merge on `main`. The rule: every migration keeps working with the previous release's code. Step 2's code uses no tables, so reverting step 3 is safe.
   - (c) The owner runs `downgrade <rev> --confirm-data-loss` in the Render Shell. It drops tables and their data. Point-in-time recovery reaches 3 days back on Hobby and restores into a *new* database, which costs money, so ask first.
4. **Proof of up, down, up from empty** (`test_up_down_up_on_an_empty_database`):
   - On an empty scratch database, upgrade. Then check:
     - Alembic `compare_metadata` against the models reports no differences;
     - the set of CHECK names equals the models';
     - every expected trigger and view exists;
     - the three domains are seeded;
     - the revision is head.
   - Downgrade to base. Only Alembic's own empty `alembic_version` table may remain; there are no constraints, triggers, functions, views, sequences or types.
   - Upgrade again. A catalog snapshot (columns, constraint definitions, indexes, trigger definitions, function bodies, views, sequences) equals the first one.
   - I also checked by hand that `compare_metadata` reports a column added to a model only in memory. That check is not in the suite.

## The owner's decisions, and the rules the database enforces

Every rejection by a trigger raises SQLSTATE 23514 with a message starting `hypocurate:`. "Append-only" means a trigger rejects UPDATE, DELETE and TRUNCATE.

1. **A narrower question is a separate query** (question 1).
   - It is a new `hypothesis` row with its own Q number and `narrower_of_run_id`, which may point only to a run that **completed with outcome `partly_sufficient`**. The link is fixed (`hypothesis` is append-only).
   - Its versions must carry the original run's confirmed domain, both as submitted and as confirmed.
   - It starts as a draft and goes through review and dispatch. Nothing creates or runs it automatically.
   - **A run whose outcome is `partly_sufficient` has no verdict** (CHECK).
2. **Named analysis sets, limited to the locked plan** (question 2).
   - `plan.sensitivity_analysis_keys text[]`: `primary` is excluded (CHECK); the keys are unique and lowercase (trigger).
   - An `analysis_set` can be inserted only for `primary` or a key of the run's locked plan, and before the freeze.
   - `analysis_set_record`: only records the run has decided on; `primary` holds only eligible records; model-recalled records are never in any set.
   - The freeze requires a non-empty `primary` set, `n_records` equal to its size, and a set for every named sensitivity analysis.
   - A test shows a possible duplicate counted once in `primary` and twice in its sensitivity set.
3. **`run_source` and the derived kind of "nothing found"** (question 3).
   - One row per run and source, written at dispatch: `not_selected` or `pending`, then decided once as `searched` or `failed`.
   - CHECKs: `failed` ⇔ `failed_search`; `failed` needs a reason.
   - `run` has **no** stored nothing-found column. The view `run_nothing_found` derives it, only for `insufficient` runs:
     - if no selected source reached `searched` → `failed_search`;
     - else, over the searched sources only, `reported_negative` if any has it, else `missing_evidence`.
   - Every failed source is listed in `failed_sources` and `not_searched_sources`, and never counts as missing evidence.
   - The precedence of `reported_negative` over `missing_evidence` is my choice; the owner did not object.
4. **Verdict and exploratory** (question 4; additions 2 and 3).
   - CHECK `verdict IS NOT NULL` ⇔ (`completed` AND `sufficient`). An outcome exists exactly when the run is completed.
   - **Only when the outcome is `sufficient`**, a trigger requires:
     - exactly one pooled result that passed both validity checks;
     - under `fixed_minimum`, `minimums_met`;
     - `exploratory = (use_available AND NOT minimums_met)`.
   - Runs that end `insufficient`, `partly_sufficient` or `failed` need no pooled result. A coefficient-only pooled result (check 1 passes, check 2 fails) can complete only as non-sufficient, without a verdict.
   - `plan` stores `min_records`, `min_alloys`, `min_groups` and `min_resid_df` (NOT NULL, ≥ 1) **under both options**. `analysis_result.minimums_met` must equal the comparison of its stored counts with these.
   - `sufficiency_option` ∈ {`fixed_minimum`, `use_available`}.
5. **Model calls and totals** (question 5).
   - The row is inserted **before** the request, as `started`, with `max_cost` (the upper bound) NOT NULL.
   - It is finished exactly once:
     - `succeeded` with all four usage values;
     - `failed` with all four or none;
     - `interrupted` with none.
   - After that the row is frozen; it is never deleted.
   - No table stores token or cost totals (a test checks the columns). The views give `reported_cost`, the token sums, `unconfirmed_calls`, `unconfirmed_cost_bound` (the sum of `max_cost` for calls without reported cost) and `cap_cost` = reported + bound, per stage, run, query and month (UTC).
6. **The reviewer's domain** (question 6).
   - The submitter's `domain_id` is frozen after the draft.
   - `confirmed_domain_id` and `domain_confirmed_at` are set together, only while `submitted`. Dispatch requires them (CHECK); after dispatch the version cannot change.
   - Tags are set by the Planner at the lock (PRD 5.5), so no reviewer-changed tag exists. `run_tag` rows can be inserted only in the transaction that locked the plan (`plan.locked_at = now()`), and a `rejected` tag value cannot be attached.
   - A proposed `tag_value` is approved or rejected once, with `decided_at`.
7. **Per-run records with an origin** (question 7).
   - `record.extraction_run_id`, `source_version_id` and `source_item_key` are NOT NULL (the key may not be empty), plus `item_index`.
   - UNIQUE `uq_record_origin_per_run`, and an index on (`source_version_id`, `source_item_key`) for matching across runs.
   - The source version must be the one recorded for that run in `run_source`.
   - Records are added only while the run is running and before the freeze. They are append-only.
8. **Power report** (addition 1). `plan.power_assumptions jsonb NULL`, information only: no constraint or trigger reads it. Power-based sufficiency is rejected by the CHECK.
9. **`analysis_result`** (addition 3).
   - `scope` ∈ {`pooled`, `per_source`, `sensitivity`}, with `analysis_set_id` NOT NULL. `pooled` and `per_source` use `primary`; `sensitivity` uses a non-primary set; `source_id` is present iff `per_source`.
   - One result per run and scope (unique index, `NULLS NOT DISTINCT`).
   - `n_records` must equal the set's records, restricted to the source for `per_source`.
   - Results are inserted only after the freeze and are append-only.
   - The validity checks are written as CHECKs on the stored counts:
     - `resid_df = n_records − n_alloys − 1`;
     - `check1 = (n_alloys ≥ 1)`;
     - `check2 = (check1 AND resid_df ≥ 1 AND n_groups ≥ 2)`;
     - an estimate iff check 1;
     - a standard error and a p-value iff check 2.
10. **Files** (item 12).
    - `source_file` (the data files an adapter reads) and `artifact` each have CHECKs: `octet_length(content) ≤ 5 MiB`, and `sha256 = encode(sha256(content), 'hex')`.
    - `source_file.path` must end in `.csv` or `.xlsx`, so the 49 MB Zenodo archive cannot be stored (by size and by type).
    - Tests try 1 byte over the limit, a `.zip`, and a wrong hash.

Other rules in the migration (they follow from the plan's table; listed so the reviewer sees them):
- **The lock and the freeze.** The plan is inserted only while its run is `running`, with `locked_at` equal to the database's transaction time; it is append-only and unique per run. `run_snapshot` is append-only, with `frozen_at` equal to the database's time.
- **Eligibility.** A `run_record` is allowed only for the run's own records, after the lock and before the freeze. It is append-only, and a model-recalled record is never eligible.
- **Runs.**
  - Status moves queued→running→completed or failed, and queued→failed. Completed and failed runs are final.
  - What a run records at dispatch (version, agent mode, fixed-plan flag, experiment flags, queue time) cannot change.
  - A run can be inserted only as `queued`, for a `dispatched` version whose confirmed domain is supported. That is the database side of "dispatch blocked for an unsupported domain".
- **Hypothesis versions.** Status moves draft→submitted→returned or dispatched; returned and dispatched versions are frozen. Chosen sources change only in draft. Versions and runs are never deleted.
- **Flags.** Raised and classified (once) only before the freeze; only the Critic's fields can be added. `flag_record` holds only the flag's own run's records.
- **Calibration.**
  - `computed` exactly when the analysis passed check 2. An `unavailable` reason must match the checks.
  - A run-level row is allowed only with reason `no_dataset_frozen`, and only when no dataset was frozen.
  - The intervals must contain their share.
- **Other tables.**
  - `commentary` only after the run is completed. A written commentary needs its number check; `mismatches` are listed iff the check found some.
  - A finished `stage_result` is final.
  - `agent_setting`, `source_version`, `domain` and `audit_log` are append-only.

**Stated limitations.**
- The triggers stop the application and ordinary edits. The database owner, which is the only Render user, can still drop or disable a trigger; that is not tamper-proof, and the fingerprints are the cross-check.
- A rejected attempt is **not logged** by the database: a log row written in the failing transaction would be rolled back with it. Logging rejected attempts belongs to the access layer (steps 5 and 6).
- Fingerprints are checked for format only (`plan`, `run_snapshot`, `source_version`). What they fingerprint is computed by code in steps 4 and 6. The exception is `source_file`/`artifact`, where the database checks the hash against the bytes.

## PRD corrections and clarifications for the next PRD update
The owner asked that these be recorded. Section 7 is "the minimum… Names are suggestions".
1. **PRD 7 vs 5.4:** the narrower-question link belongs on a new query (`hypothesis.narrower_of_run_id`), not on `hypothesis_version`.
2. **PRD 7:** `run_record`'s single "used only in a sensitivity analysis" flag cannot express 5.3 and 5.6. It is replaced by named sets (`analysis_set`, `analysis_set_record`).
3. **PRD 7:** "kind of nothing found" per run is replaced by `run_source` per source, with the run-level kind derived (rule above).
4. **PRD 7:** `run` needs `verdict` and `exploratory`.
5. **PRD 5.8 clarification:** "exploratory" means the "use what is available" option **and** data below the fixed minimums. The 5.8 table currently labels every such result exploratory; 14.3 matches the owner's rule.
6. **PRD 7 and 8:** stored token and cost totals on `run`, `stage_result` and `commentary` are replaced by views over `model_call`. A call is recorded before the request, and a call without reported cost counts at its `max_cost` bound toward the caps.
7. **PRD 7 and 8:** `run_snapshot` holds the dataset freeze only. The dispatch-time agent settings and source versions are in `run_agent_setting` and `run_source`.
8. **PRD 9.3:** the reviewer's domain change is a review decision on the version (`confirmed_domain_id`, `domain_confirmed_at`), not a new version.
9. **PRD 5.5:** `tag_value` needs a status (proposed, approved, rejected) and a decision time.
10. **PRD 7:** a flag's records are a join table (`flag_record`).
11. **PRD 7:** records are extracted per run (`record.extraction_run_id`) and carry an origin identifier (`source_item_key`, `item_index`).
12. **PRD 6 and 7:** files are `bytea` with a 5 MiB limit per file. Source files are a separate table (`source_file`), so a version can have several; only data files are stored.
13. **PRD 5.8 and the New query screen (9.2):** power-based sufficiency is not an option in sprint 1. It becomes "estimated power report (information only)" (`plan.power_assumptions`); as a gate it stays in the backlog (PRD 18).

## Tests (316, all passing; 128 new; the 93 from step 1 and the login tests unchanged)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data tests/test_login.py tests/test_login_throttle.py` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_data_model.py` (new) | 111 | Every rule above, each with an allowed case and a rejected case, on a fresh migrated scratch database |
| `tests/test_migrations.py` (new) | 11 | One head; every revision has a downgrade; no statement escapes the transaction; migrations inside the package; up, down, up from empty; upgrade at head changes nothing; a failed upgrade changes nothing; two concurrent upgrades (subprocesses held on the lock, then released) both exit 0; the command line; production downgrade refused without the flag; no password printed; `schema_status` |
| `tests/model_builder.py` (new) | — | Walks a run through the lifecycle in plain SQL, one transaction per step |
| `tests/conftest.py` | — | `empty_database`, a session `template_database` migrated once, `migrated_database` copied from it (addition 4), and `db`. Tests never touch the database at `DATABASE_URL`; scratch databases are dropped with `WITH (FORCE)`. |
| `tests/test_health.py` | 8 (+1) | `schema` on `/health` |
| `tests/test_skeleton.py` | 33 (+2) | Compose `migrate` ordering; Render pre-deploy on both services |
| `tests/test_check_runtime_image.py` | 14 (+3) | A missing migration file fails the image check |

### Tests changed (none removed, none weakened)
- `test_health_without_login_database_up`: it now uses a migrated scratch database instead of the database at `DATABASE_URL`, whose schema is no longer predictable. The exact-equality assertion is kept, extended with `"schema": {"revision": "0001", "at_head": true}`.
- `test_health_page_in_a_browser`: a scratch database too; it now also checks the schema row.
- `test_health_reports_database_down_without_crashing`: adds an assertion on `schema`.
- `tests/test_skeleton.py`: `COMPOSE_ENV` gains `"migrate": {"HYPOCURATE_ENV", "DATABASE_URL"}`. The existing tests now also check that service's variables. The two module docstrings mention step 3.

### Suite results
```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, `docker compose up -d db`)
316 passed in 34.88s
$ docker compose run --rm test           (the test image)
316 passed in 36.48s
GitHub Actions, commit 10f08c3 (last code change): success; "Run the suite in the test image": 316 passed.
https://github.com/kelawady/hypocurate/actions/runs/37247693364
GitHub Actions, commit d276a46:          success; every step passed; the Compose step ran
                                         hypocurate-migrate-1 before web and worker.
https://github.com/kelawady/hypocurate/actions/runs/37247347645
```
Local checks beyond the suite:
- `docker compose up -d`: `migrate` exited 0 ("schema at 0001"), and `/health` returned `{"web":"ok","database":"ok","version":"unknown","schema":{"revision":"0001","at_head":true}}`.
- The default image (built as Render builds it) passed `check_runtime_image.py` ("runtime image OK"), and `python -m hypocurate.db.migrate current` in it printed `0001`.

## Deviations from the approved plan
1. **`CREATE TABLE` statements rendered by autogenerate, then edited by hand.** The plan said "written by hand". The rendered code was reviewed line by line, and the drift and catalog-snapshot tests compare it with the models.
2. **More database rules than the plan's table listed.** They follow the same principles and each has a test:
   - run insert needs a dispatched version with a supported domain;
   - records only while running and before the freeze;
   - `run_record` fully append-only;
   - the validity-check definitions as CHECKs;
   - calibration consistent with the checks;
   - commentary only after completion;
   - `run_tag` limited to the lock transaction;
   - `hypothesis` append-only;
   - `locked_at` and `frozen_at` equal to the database's time.
3. **NULL-safe trigger checks (commit `10f08c3`).** While writing the reviewer's question 2, I found trigger conditions of the form `(SELECT …) <> 'x'` and `IF NOT (SELECT …)`. They would let a row through if the lookup returned NULL. A foreign key or CHECK caught every such case, so no test changed outcome. They now use `IS DISTINCT FROM` and `IS NOT TRUE`. The remaining `<>` comparisons are on NOT NULL columns of the row itself. Migration 0001 was edited in place because it has never been applied outside test and local databases. The local development database was downgraded to base and upgraded again.
4. **Query numbers can skip.** `Q-` numbers come from a PostgreSQL sequence, which does not roll back, so a rejected insert leaves a gap. Numbers stay unique and increasing.

## Open items
1. **Live check after merge** (owner's go-ahead): Render's deploy log shows the pre-deploy command ran on both services, and `https://hypocurate-web.onrender.com/health` shows `"schema":{"revision":"0001","at_head":true}`. Render documents `preDeployCommand` for web services and workers; this will be the first time it runs with our Docker services, so the live check is what confirms it. The merge also syncs the Blueprint, because `render.yaml` changed.
2. **Not enforced by the database; left to later steps' code and tests:**
   - that every registered source gets a `run_source` row at dispatch (step 9);
   - that each run has a property, alloy-class and test-condition tag (step 6);
   - that `verdict` agrees with the pooled p-value and the plan's threshold (step 7; whether "p < 0.05" or "≤" is a statistics decision);
   - the list of stage names (`stage_result.stage` is checked for format only; step 8).
3. **Storage estimate** (about 4–6 MB per run, 120–200 runs in 1 GB) is to be measured on the real acceptance run in step 8.
4. **The test database user must be allowed to create databases.** It is in the local and CI containers. The tests never run against Render.
5. **Source registration's "access key" (PRD 9.6) has no column.** Secrets stay in environment variables (CLAUDE.md); to decide when a source needs one.
6. The local development database (Compose volume) is now migrated to `0001`. This affects nothing in the suite.
7. Carried from step 2, unchanged: the pooled p-value 7.4e-7 against "≈ 8e-7" (before step 7); permitted test types and a non-MPEA survivor pair (step 6); the access layer must enforce the approved file list (step 5).

## Questions for the reviewer
1. Can any path change a locked plan, a frozen dataset or a stored record without a database error, other than dropping or disabling a trigger as the owner?
2. Is any trigger condition wrong when a value is NULL (a NULL comparison that lets a row through)?
3. Does the `run_nothing_found` derivation ever report a failed source as missing evidence?
4. Are the cost views right for every model-call status, especially `failed` with and without usage?
