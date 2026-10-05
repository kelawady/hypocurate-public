# Build step 3 — review packet for the second model

Date: 2026-10-05. Branch: `step-03-data-model`. Code reviewed: commit `10f08c3` (this packet is added in the next commit and changes no code). GitHub Actions on that commit: success, https://github.com/kelawady/hypocurate/actions/runs/37247693364.

Generated from the files on disk by a script, so every file below is quoted exactly. The lock files are shown without their hash lines, which are long; the full files are in the repository.

## How to use this packet

You are reviewing build step 3 of HypoCurate (PRD Section 15): the data model. It includes:
- the tables of PRD Section 7, as SQLAlchemy models;
- one Alembic migration with CHECK constraints, triggers and views that enforce the rules in the database itself;
- the migration runner, applied by Render before every deploy;
- the schema revision on `/health`.

Not in this step: the access layer, agents, pipeline, statistics, screens, and loading sources.

Your review is advice; the test suite is the gate. Please return a dated findings file. Each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

Use the fixed checklist in section 2, answering each item yes, no or not applicable to this change, with a reason for every "no". For this step the most relevant items are:
- **Checkpoints**: can anything change after the lock or the freeze?
- **Stored is not analysed**;
- **Outcomes and wording**: the narrower question; the three kinds of "nothing found";
- **Cost**: is every model call recorded?
- **Data and tests**.

Beyond the checklist, please look at:
- the trigger functions in `0001_data_model.py`, for NULL handling and for any path that bypasses them;
- the migration's behaviour on failure and under concurrency;
- the "Questions for the reviewer" at the end of the summary.

## Contents

1. Step summary
2. Reviewer checklist
3. Application code: data model and migrations
4. Application code: health page
5. Tests
6. Containers, deployment and the image check
7. Dependencies
8. README
9. Test output

## Files added, modified or deleted since `main` (step 2 merge)

```
M	README.md
M	docker-compose.yml
M	hypocurate/db/engine.py
A	hypocurate/db/migrate.py
A	hypocurate/db/migrations/env.py
A	hypocurate/db/migrations/script.py.mako
A	hypocurate/db/migrations/versions/0001_data_model.py
A	hypocurate/db/models.py
M	hypocurate/web/app.py
M	hypocurate/web/templates/health.html
M	pyproject.toml
M	render.yaml
M	requirements-dev.lock
M	requirements.lock
M	scripts/check_runtime_image.py
M	tests/conftest.py
A	tests/model_builder.py
M	tests/test_check_runtime_image.py
A	tests/test_data_model.py
M	tests/test_health.py
A	tests/test_migrations.py
M	tests/test_skeleton.py
A	docs/reviews/step03_summary.md   (added with this packet)
A	docs/reviews/step03_review_packet.md   (this file)
```


## 1. Step summary

### `docs/reviews/step03_summary.md`

SHA-256 `aafd54f1927885dcb2f9f07516d4359759f02cf716ea30d2e1ab41f4e824089d`, 24016 bytes.

````markdown
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
````


## 2. Reviewer checklist

### `docs/reviews/checklist.md`

SHA-256 `93df5256230e9a3ed2089d0b0ed73c7af3d4bead77a4dbe084b72ffb91806ddb`, 6341 bytes.

```markdown
# Second-model review checklist

**Status: approved by the owner as a working draft, 2026-10-04.** Drafted from PRD Section 13.2 and the rules in `CLAUDE.md`. This is the fixed checklist given to the reviewer at every review. It may be amended after its first use in step 2; any amendment needs the owner's approval.

## When a review is required (PRD 13.2)
- At the end of each build step in PRD Section 15.
- Whenever a change touches a safeguard: the access rules, the plan lock, the inclusion and eligibility rules, or the statistics. Any change to a safeguard also needs the owner's approval, however small.

## What the reviewer is given
1. The changes since the last review: a review packet with the full text of every changed code, test and script file, and the test output.
2. The core rules:
   - the access contract (PRD 4);
   - the plan lock and dataset freeze (PRD 5.6);
   - "stored is not the same as analysed" (PRD 5.3);
   - "a narrower question is a separate record" (PRD 5.4).
3. This checklist.

## Minimum questions (PRD 13.2, verbatim)
1. Can any role reach outcome values it should not see?
2. Can anything change after the lock?
3. Are records ever dropped or overwritten in the store?
4. Do the eligibility rules match Section 5.3?
5. Are the statistics what the plan states?
6. Are there untested paths?
7. Are secrets or keys exposed?

## Rule-by-rule checks
Answer each with yes, no or not applicable to this change. Give a reason for every "no".

**Who decides**
- [ ] Code alone sets inclusion, flags, the choice of test, data sufficiency and the verdict. No language model output can set any of them. (CLAUDE.md rule 1)

**Access contract (PRD 4)**
- [ ] Every agent reads data only through the access layer, using a per-role, per-stage allow-list of fields. Is anything not on the list withheld?
- [ ] A disallowed call raises `AccessDenied` and writes an audit-log row.
- [ ] Outcome values cannot leak through any of these:
  - flag numbers;
  - values as originally reported;
  - nested fields;
  - text handed between stages.
- [ ] The tests cover a role's **complete** input: prompt, every tool response and handed-over text. Do they include the planted-value test for the Planner and the Critic?
- [ ] Pipeline code reads input files only from an explicit list of approved files. Are `tests/` and `docs/reviews/`, which hold expected answers, outside that list? Directory placement alone is a convention, not enforcement.
- [ ] The Curator is not told the direction of the claim.
- [ ] The Critic gets the kind of each flag, never the numbers.

**Checkpoints (PRD 5.6)**
- [ ] Rules lock before curation fixes all of these, with a fingerprint and a time:
  - the model;
  - scope;
  - exclusion rules;
  - eligibility rules;
  - the data-sufficiency option;
  - sensitivity analyses.
- [ ] Dataset freeze before analysis fixes the record sets, with a fingerprint and a time.
- [ ] After each checkpoint, nothing changes, by agent or by person. Is every attempt rejected and logged?
- [ ] A later removal appears only as a labelled sensitivity analysis and never changes the verdict.

**Stored is not analysed (PRD 5.3)**
- [ ] Every record found is kept. Nothing is deleted or overwritten in place.
- [ ] Eligibility is decided by code under the locked rules. Do the defaults match the PRD 5.3 table?
- [ ] Duplicates require all of these: the same original paper, alloy, grain size, value and test conditions. Is matching alloy and grain size alone kept from counting?
- [ ] The survivor of a duplicate pair follows the owner's rule:
  1. the record that comes directly from the original paper (detected by its DOI);
  2. then the fixed source order MPEA, Texas A&M, controlled extract;
  3. then the lowest row.
- [ ] Conflicting records are preserved, not automatically pooled.
- [ ] Physical checks never use the relationship under test.
- [ ] Model-recalled data are never pooled and never count toward a verdict.

**Statistics (PRD 5.7, 5.8, 5.10)**
- [ ] Only the one supported model is used:
  - OLS with alloy intercepts;
  - k × d^-1/2;
  - cluster-robust standard errors by paper, with the small-sample correction;
  - a one-sided test of k > 0 at 0.05, against t with (groups − 1) degrees of freedom;
  - only alloys with at least 2 distinct grain sizes.
- [ ] Both validity checks are applied to every analysis and can never be waived:
  1. Can a coefficient be fitted?
  2. Are there at least 1 residual degree of freedom and at least 2 groups?
  
  If check 2 fails, is only the coefficient reported?
- [ ] Data sufficiency is the option fixed at rules lock. Does "use what is available" waive only the threshold, and label the result exploratory?
- [ ] Calibration is a flag, not a gate. Is "calibration unavailable" shown with its reason when inference cannot run?
- [ ] Do the reference numbers still reproduce within the stated tolerances, with no tolerance widened?

**Outcomes and wording**
- [ ] A narrower question is a separate, linked record. Does the original get no verdict? (PRD 5.4)
- [ ] Are the three kinds of "nothing found" kept distinct: reported negative, missing evidence, failed search? (PRD 3.1)
- [ ] Are outcomes stated "in the sources searched"? Is it never claimed that data "do not exist"?

**Cost (PRD 8)**
- [ ] Is every model call recorded with tokens and actual cost (`model_call`)?
- [ ] Are the caps enforced: $2 per run, $50 per month?

**Data and tests**
- [ ] Do frozen files match their pinned fingerprints, with the manifest's own fingerprint and the list of required files pinned in the tests? (PRD 10, 15)
- [ ] Has no test been weakened, skipped or deleted, and no tolerance widened?
- [ ] Are new paths covered by tests?
- [ ] Has nothing been built ahead of the current step, and nothing from the backlog (PRD 18)?

**Secrets**
- [ ] Are there no keys, database URLs or passwords in code, tests, logs or committed files? Does `.env.example` hold names only?

## What comes back (PRD 13.2)
- A dated findings file in `docs/reviews/`.
- Each finding is either accepted, which means a fix plus a regression test, or rejected with a one-line reason in the same file.
- **Authority:** the reviewer advises; the test suite is the gate. A review cannot approve a change that fails the suite. A finding is acted on only after the owner accepts it.
```


## 3. Application code: data model and migrations

### `hypocurate/db/models.py`

SHA-256 `68480c62d94baac721890e589e811257ed22c202a0cdfbd01a81e395f9f2387e`, 36732 bytes.

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
`model_call`. The run-level kind of "nothing found" is not stored either; the view
`run_nothing_found` derives it from `run_source`.
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
    """A registered source (PRD 9.6). Settings such as on/off may change; it is never deleted."""
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
    """A snapshot of a source. Append-only."""
    __tablename__ = "source_version"
    id: Mapped[int] = pk()
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    label: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(Text)
    obtained_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("source_id", "fingerprint"),
        UniqueConstraint("id", "source_id"),
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
    )


class SourceFile(Base):
    """A data file an adapter reads (owner decision: only data files, at most 5 MiB). Append-only."""
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
    (owner decision, question 3). The run-level kind is derived (view run_nothing_found)."""
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
    reported cost counts at `max_cost` toward totals and caps."""
    __tablename__ = "model_call"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(BigInteger)
    stage_result_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    price_table_version: Mapped[str] = mapped_column(Text)
    max_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    status: Mapped[str] = mapped_column(Text, server_default=sql("'started'"))
    input_tokens: Mapped[int | None] = mapped_column(BigInteger)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cached_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
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
        CheckConstraint("max_cost >= 0", name="max_cost_not_negative"),
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
    that decided it (PRD 5.3). Written by code under the locked plan, before the freeze."""
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
    """One row per analysis and scope (owner's addition 3). The two validity checks
    (PRD 5.7) are recomputed from the stored counts by CHECK constraints."""
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
        CheckConstraint("resid_df = n_records - n_alloys - 1", name="resid_df_definition"),
        CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_definition"),
        CheckConstraint("check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)",
                        name="check2_definition"),
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
    """Plots and workbooks for a run (at most 5 MiB each). Append-only."""
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

### `hypocurate/db/migrations/versions/0001_data_model.py`

SHA-256 `3ece77994ebd7d010eddc45bea18df5a078bd6845e793e750a94f2337e407631`, 72199 bytes.

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
    sa.Column('fingerprint', sa.Text(), nullable=False),
    sa.Column('obtained_on', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_fingerprint_format')),
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
    sa.CheckConstraint('check1_passed = (n_alloys >= 1)', name=op.f('ck_analysis_result_check1_definition')),
    sa.CheckConstraint('check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)', name=op.f('ck_analysis_result_check2_definition')),
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
    sa.Column('max_cost', sa.Numeric(precision=12, scale=6), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'started'"), nullable=False),
    sa.Column('input_tokens', sa.BigInteger(), nullable=True),
    sa.Column('output_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cached_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cost', sa.Numeric(precision=12, scale=6), nullable=True),
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
    sa.CheckConstraint('max_cost >= 0', name=op.f('ck_model_call_max_cost_not_negative')),
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
# ---------------------------------------------------------------------------

FUNCTION_NAMES = [
    "hc_reject(text)",
    "hc_append_only()",
    "hc_no_delete()",
    "hc_is_frozen(bigint)",
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
        IF (SELECT status FROM hypothesis_version WHERE id = row_version) IS DISTINCT FROM 'draft' THEN
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
        IF (SELECT status FROM hypothesis_version WHERE id = NEW.hypothesis_version_id) IS DISTINCT FROM 'dispatched' THEN
            PERFORM hc_reject('a run needs a dispatched hypothesis version');
        END IF;
        IF (SELECT d.supported FROM hypothesis_version hv JOIN domain d ON d.id = hv.confirmed_domain_id
            WHERE hv.id = NEW.hypothesis_version_id) IS NOT TRUE THEN
            PERFORM hc_reject('dispatch blocked: the confirmed domain is not supported yet');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Completion (owner, question 4 and addition 2): only for an outcome of sufficient,
    # exactly one pooled result that passed both validity checks is required, and
    # exploratory = (use_available AND minimums not met).
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
        IF (SELECT status FROM run WHERE id = NEW.run_id) IS DISTINCT FROM 'running' THEN
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
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.run_id AND locked_at = now()) THEN
            PERFORM hc_reject('run tags are written in the rules-lock transaction only');
        END IF;
        IF (SELECT status FROM tag_value WHERE id = NEW.tag_value_id) = 'rejected' THEN
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
    """
    CREATE FUNCTION hc_run_agent_setting_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF (SELECT status FROM run WHERE id = NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('agent settings versions are recorded at dispatch');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF (SELECT status FROM run WHERE id = NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('run sources are recorded at dispatch');
        END IF;
        IF NEW.search_status NOT IN ('not_selected', 'pending') THEN
            PERFORM hc_reject('a run source starts as not_selected or pending');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
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
    # Records come from a source version the run recorded, while the run is running, before the freeze.
    """
    CREATE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF (SELECT status FROM run WHERE id = NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Stored is not analysed (PRD 5.3): eligibility is written once, after the lock, before the freeze.
    """
    CREATE FUNCTION hc_run_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE rec record;
    BEGIN
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
    # Dataset freeze (PRD 5.6): the primary set and every named sensitivity set exist.
    """
    CREATE FUNCTION hc_run_snapshot_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE keys text[]; primary_count int;
    BEGIN
        IF (SELECT status FROM run WHERE id = NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a dataset is frozen only while its run is running');
        END IF;
        IF NEW.frozen_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('frozen_at is set by the database at the freeze');
        END IF;
        SELECT sensitivity_analysis_keys INTO keys FROM plan WHERE run_id = NEW.run_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('a dataset freeze needs a locked plan');
        END IF;
        SELECT count(*) INTO primary_count FROM analysis_set s JOIN analysis_set_record sr ON sr.analysis_set_id = s.id
            WHERE s.run_id = NEW.run_id AND s.key = 'primary';
        IF primary_count = 0 THEN
            PERFORM hc_reject('no eligible records: no dataset is frozen');
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
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('flags cannot be added after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
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
        IF (SELECT extraction_run_id FROM record WHERE id = NEW.record_id) IS DISTINCT FROM flag_run THEN
            PERFORM hc_reject('a flag names only records of its own run');
        END IF;
        IF hc_is_frozen(flag_run) THEN
            PERFORM hc_reject('flags cannot change after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Results (owner, addition 3): after the freeze, on the right set, with counts that match it.
    """
    CREATE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int;
    BEGIN
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
        SELECT count(*) INTO set_count FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Calibration (PRD 5.10): computed exactly when inference is valid; otherwise the reason matches.
    """
    CREATE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result;
    BEGIN
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
        IF (SELECT status FROM run WHERE id = NEW.run_id) IS DISTINCT FROM 'completed' THEN
            PERFORM hc_reject('commentary is written after the run is completed');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_stage_result_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
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
    # Model calls (owner, question 5): written before the request, finished exactly once.
    """
    CREATE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.status <> 'started' THEN
            PERFORM hc_reject('a model call is recorded before the request, as started');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
            PERFORM hc_reject('a model call is finished exactly once');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('what was recorded before the request cannot change');
        END IF;
        RETURN NEW;
    END $$
    """,
]

APPEND_ONLY = [
    "domain", "agent_setting", "source_version", "source_file", "hypothesis", "plan", "run_tag",
    "run_agent_setting", "run_snapshot", "record", "run_record", "analysis_set", "analysis_set_record",
    "flag_record", "analysis_result", "calibration_result", "commentary", "artifact", "audit_log",
]
NO_DELETE = [
    "hypothesis_version", "run", "tag_value", "source", "run_source", "stage_result", "model_call", "flag",
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

VIEW_NAMES = [
    "run_nothing_found",
    "model_call_totals_by_stage",
    "model_call_totals_by_run",
    "model_call_totals_by_query",
    "model_call_totals_by_month",
]

VIEWS = [
    # Owner, question 3: the run-level kind of "nothing found" is derived, never stored.
    # A failed source is never "missing evidence": it is listed as failed and not searched.
    """
    CREATE VIEW run_nothing_found AS
    SELECT r.id AS run_id,
        CASE
            WHEN r.outcome IS DISTINCT FROM 'insufficient' THEN NULL
            WHEN NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = r.id AND rs.search_status = 'searched')
                THEN 'failed_search'
            WHEN EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = r.id AND rs.search_status = 'searched'
                           AND rs.nothing_found = 'reported_negative')
                THEN 'reported_negative'
            ELSE 'missing_evidence'
        END AS nothing_found,
        ARRAY(SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id
              WHERE rs.run_id = r.id AND rs.search_status = 'searched' ORDER BY s.key) AS searched_sources,
        ARRAY(SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id
              WHERE rs.run_id = r.id AND rs.search_status = 'failed' ORDER BY s.key) AS failed_sources,
        ARRAY(SELECT s.key FROM source s
              WHERE NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = r.id AND rs.source_id = s.id
                                  AND rs.search_status = 'searched')
              ORDER BY s.key) AS not_searched_sources
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

### `hypocurate/db/migrations/env.py`

SHA-256 `093331773fbe00c57a9cca39fd933e5cfaf1e9a96092b6bd583b3c6c7784b9dd`, 799 bytes.

```python
"""Alembic environment. Online mode only, with the engine passed in by
`hypocurate.db.migrate`. The whole run is one transaction, and the advisory
lock is taken inside it before Alembic reads the current revision."""
from alembic import context
from sqlalchemy import text

from hypocurate.db.migrate import ADVISORY_LOCK_KEY
from hypocurate.db.models import Base

engine = context.config.attributes["engine"]

with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        transaction_per_migration=False,  # one transaction for the whole upgrade
    )
    with context.begin_transaction():
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ADVISORY_LOCK_KEY})
        context.run_migrations()
```

### `hypocurate/db/migrations/script.py.mako`

SHA-256 `abd1a6742a8f1ad2ba20a2fe664d10051cf52c5ccf4834472795ccd0ff9734ac`, 686 bytes.

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

### `hypocurate/db/migrate.py`

SHA-256 `d81fb4ad367c8a399cae2260cefd4f88c2bc5640b25b36fb204d566d3f75aa73`, 4402 bytes.

```python
"""Database migrations (build step 3). Run as:

    python -m hypocurate.db.migrate upgrade              # to head; Render's pre-deploy command
    python -m hypocurate.db.migrate current
    python -m hypocurate.db.migrate downgrade <revision> [--confirm-data-loss]

How it behaves, and only this:
- The whole upgrade runs in one transaction (PostgreSQL has transactional DDL).
  If any statement fails, nothing is applied: no table and no change to
  `alembic_version`. The command exits non-zero, so Render fails the deploy and
  keeps the previous version running.
- `env.py` takes a transaction-level advisory lock before reading the current
  revision, so two upgrades started together (web and worker deploying the same
  commit) run one after the other; the second finds the database at head.
- A downgrade drops tables and their data. In production it refuses unless
  `--confirm-data-loss` is given.

The Alembic configuration is built here, not read from an `alembic.ini`, so the
deployed image holds only `hypocurate/`, `data/` and `requirements.lock`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine

from hypocurate.config import load_settings
from hypocurate.db.engine import make_engine

MIGRATIONS = Path(__file__).parent / "migrations"
# Any fixed number; shared by every process that migrates this database.
ADVISORY_LOCK_KEY = 0x48594343  # "HYCC"


def alembic_config(engine: Engine) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    # Passed as an object, never as a URL string: the URL holds the password, and
    # Alembic's config file syntax would also misread a '%' in it.
    cfg.attributes["engine"] = engine
    return cfg


def head_revision() -> str:
    heads = ScriptDirectory(str(MIGRATIONS)).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"expected exactly one migration head, found {len(heads)}")
    return heads[0]


def current_revision(engine: Engine) -> str | None:
    with engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def schema_status(engine: Engine) -> dict:
    """For /health: the database's revision and whether it is the code's head. Never raises."""
    try:
        revision = current_revision(engine)
    except Exception:
        return {"revision": None, "at_head": False}
    return {"revision": revision, "at_head": revision == head_revision()}


def upgrade(engine: Engine, revision: str = "head") -> None:
    command.upgrade(alembic_config(engine), revision)


def downgrade(engine: Engine, revision: str) -> None:
    command.downgrade(alembic_config(engine), revision)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m hypocurate.db.migrate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("upgrade", help="migrate to the latest revision (one transaction)")
    sub.add_parser("current", help="print the database's revision")
    down = sub.add_parser("downgrade", help="migrate down to a revision; drops tables and their data")
    down.add_argument("revision", help="target revision, or 'base' for an empty schema")
    down.add_argument("--confirm-data-loss", action="store_true",
                      help="required in production: the downgrade deletes data")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    engine = make_engine(settings.database_url)
    if args.command == "upgrade":
        upgrade(engine)
        print(f"schema at {current_revision(engine)}")
    elif args.command == "current":
        print(current_revision(engine) or "empty (no revision)")
    else:
        if settings.production and not args.confirm_data_loss:
            print("refused: a downgrade drops tables and their data. In production, add "
                  "--confirm-data-loss after taking a backup (README, 'Database migrations').",
                  file=sys.stderr)
            return 2
        downgrade(engine, args.revision)
        print(f"schema at {current_revision(engine) or 'empty (no revision)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### `hypocurate/db/engine.py`

SHA-256 `55bea49e03b2e841b54d0980030d28d7c4464ee3b5b3a2ddd8e23d2a22e019c9`, 945 bytes.

```python
"""The database engine. Login uses a signed cookie, not a table; the health page asks
whether the database answers. The tables (step 3) are in `models.py` and are created
only by the migrations (`migrate.py`)."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text


def make_engine(database_url: str) -> Engine:
    # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def database_reachable(engine: Engine) -> bool:
    """True if the database answers `SELECT 1`. Never raises."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```


## 4. Application code: health page

### `hypocurate/web/app.py`

SHA-256 `f8ee472da0ada035134cf13466c9d1fcd430c21d673f5fd38cffde4500a77e58`, 4376 bytes.

```python
"""The web service (PRD Section 6): login, health page, and a placeholder home page.

Every page needs the shared login except exactly /login and /health, and the
files under /static/. The session is a signed cookie (Starlette
SessionMiddleware, itsdangerous) holding only {"signed_in": true}; in
production it is sent over HTTPS only. There is no server-side session record:
rotating SESSION_SECRET ends every session (README, "Sessions").
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.db.migrate import schema_status
from hypocurate.web.login_throttle import Attempt, LoginThrottle

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
STATIC_PREFIX = "/static/"

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_throttle: LoginThrottle | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    throttle = login_throttle or LoginThrottle()

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        public = path in PUBLIC_PATHS or path.startswith(STATIC_PREFIX)
        if not public and not request.session.get("signed_in"):
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)

    # Added after require_login so that it runs first and the session is available.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=SESSION_COOKIE,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.production,
    )
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html", {})

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form("")) -> Response:
        result = throttle.attempt(password, settings.password)
        if result is Attempt.OK:
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        if result is Attempt.THROTTLED:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password."}, status_code=401
        )

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/health")
    def health(request: Request) -> Response:
        db_ok = database_reachable(engine)
        status = {"web": "ok", "database": "ok" if db_ok else "unreachable", "version": settings.version,
                  # Informational (step 3): confirms a deploy migrated; never changes the status code.
                  "schema": schema_status(engine) if db_ok else {"revision": None, "at_head": False}}
        code = 200 if db_ok else 503
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(request, "health.html", {"status": status}, status_code=code)
        return JSONResponse(status, status_code=code)

    return app
```

### `hypocurate/web/templates/health.html`

SHA-256 `92dfc7dd41a6be7c7934a2e9d629d8c4b671828ac25302a94503eafccb49f120`, 602 bytes.

```html
{% extends "base.html" %}
{% block title %}Health · HypoCurate{% endblock %}
{% block content %}
<h1>Health</h1>
<table>
  <tr><th>Web service</th><td>{{ status.web }}</td></tr>
  <tr><th>Database</th><td class="{{ 'ok' if status.database == 'ok' else 'error' }}">{{ status.database }}</td></tr>
  <tr><th>Version</th><td><code>{{ status.version }}</code></td></tr>
  <tr><th>Schema</th><td class="{{ 'ok' if status.schema.at_head else 'error' }}"><code>{{ status.schema.revision or 'none' }}</code>{{ ' (latest)' if status.schema.at_head else ' (not the latest)' }}</td></tr>
</table>
{% endblock %}
```


## 5. Tests

### `tests/conftest.py`

SHA-256 `286f8057517c9414c2c081d62e8eef480e813de8eb4e7c4654a694360e547acc`, 2858 bytes.

```python
"""Shared fixtures. Tests that need PostgreSQL fail, never skip, when it is not reachable.

Step 3: tests that need tables never touch the database at DATABASE_URL. Each gets
its own scratch database, dropped afterwards:
- `empty_database`: a new, empty database (the migration tests start here);
- `migrated_database`: a copy of a template database migrated once per session
  (owner's addition 4, for speed). The template itself is migrated from empty.
"""
import os
import uuid

import pytest
from sqlalchemy import make_url, text

from hypocurate.db import migrate
from hypocurate.db.engine import database_reachable, make_engine

HOW_TO = (
    "This test needs PostgreSQL. Run the suite with `docker compose run --rm test`, "
    "or start the database with `docker compose up -d db` and set DATABASE_URL "
    "(see README)."
)


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.fail("DATABASE_URL is not set. " + HOW_TO)
    if not database_reachable(make_engine(url)):
        pytest.fail("The database at DATABASE_URL does not answer. " + HOW_TO)
    return url


def url_for(database_url: str, name: str) -> str:
    return make_url(database_url).set(database=name).render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def admin(database_url):
    """Creates and drops scratch databases. Never used for anything else."""
    engine = make_engine(database_url).execution_options(isolation_level="AUTOCOMMIT")
    yield engine
    engine.dispose()


def _create(admin, prefix: str, template: str | None = None) -> str:
    name = f"{prefix}_{uuid.uuid4().hex[:12]}"
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"' + (f' TEMPLATE "{template}"' if template else "")))
    return name


def _drop(admin, name: str) -> None:
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


@pytest.fixture
def empty_database(admin, database_url):
    name = _create(admin, "hypocurate_t")
    yield url_for(database_url, name)
    _drop(admin, name)


@pytest.fixture(scope="session")
def template_database(admin, database_url):
    name = _create(admin, "hypocurate_tmpl")
    engine = make_engine(url_for(database_url, name))
    migrate.upgrade(engine)
    engine.dispose()  # a template must have no open connections
    yield name
    _drop(admin, name)


@pytest.fixture
def migrated_database(admin, database_url, template_database):
    name = _create(admin, "hypocurate_t", template=template_database)
    yield url_for(database_url, name)
    _drop(admin, name)


@pytest.fixture
def db(migrated_database):
    """An engine on a freshly migrated scratch database."""
    engine = make_engine(migrated_database)
    yield engine
    engine.dispose()
```

### `tests/model_builder.py`

SHA-256 `8cd6f488d64e1310ed5a9340db2e9f103cd916c07d464422706e016d7e749555`, 10354 bytes.

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


class World:
    def __init__(self, engine):
        self.e = engine
        self.domain = {k: v for k, v in self.rows("SELECT key, id FROM domain")}
        self.source = {}
        self.version = {}
        for key, unit, fp in (("mpea", "paper", "a" * 64), ("tamu_fcc", "dataset", "b" * 64)):
            self.source[key] = self.val(
                "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
                "VALUES (:k, :k, 'uploaded_table', 'test', 'measured', 'available', true, :u) RETURNING id",
                k=key, u=unit)
            self.version[key] = self.val(
                "INSERT INTO source_version (source_id, label, fingerprint, obtained_on) "
                "VALUES (:s, 'v1', :fp, '2026-10-04') RETURNING id", s=self.source[key], fp=fp)

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

    def record(self, rid, source="mpea", key="row-1", kind="measured", index=0):
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

    def stage(self, rid, stage="planner", role="planner"):
        return self.val("INSERT INTO stage_result (run_id, stage, role) VALUES (:r, :s, :o) RETURNING id",
                        r=rid, s=stage, o=role)

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

### `tests/test_data_model.py`

SHA-256 `e52987e24b77a3a38d82eac64f569a0ade58b4eda17a6084de83c0211e7ee086`, 48656 bytes.

```python
"""Step 3: the rules the database enforces (PRD 7, with the owner's decisions of
2026-10-04/05). Every rule has an allowed case and a rejected case, on a freshly
migrated scratch database. Rejections by a trigger read "hypocurate: ..."; rejections
by a CHECK name the constraint."""
import pytest
from sqlalchemy.exc import IntegrityError

from hypocurate.db.models import MAX_FILE_BYTES
from model_builder import FP, World, sha


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
    rid = w.run(sources=())
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
    other = w.val("INSERT INTO source_version (source_id, label, fingerprint, obtained_on) "
                  "VALUES (:s, 'v2', :fp, '2026-10-05') RETURNING id", s=w.source["mpea"], fp="c" * 64)
    w.rejected("UPDATE run_source SET source_version_id = :sv WHERE run_id = :r AND source_id = :s",
               "cannot change", sv=other, r=rid, s=w.source["mpea"])


def nothing_found(w, rid):
    return w.rows("SELECT nothing_found, searched_sources, failed_sources, not_searched_sources "
                  "FROM run_nothing_found WHERE run_id = :r", r=rid)[0]


def test_a_failed_source_is_never_missing_evidence(w):
    """One source failed, the other has missing evidence: the run is missing evidence
    in the sources searched, and the failed source is named as failed and not searched."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "missing_evidence")
    w.search(rid, "tamu_fcc", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("missing_evidence", ["mpea"], ["tamu_fcc"], ["tamu_fcc"])


def test_no_source_searched_is_failed_search(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("failed_search", [], ["mpea"], ["mpea", "tamu_fcc"])


def test_a_reported_negative_result_is_kept_distinct(w):
    rid = w.running()
    w.search(rid, "mpea", "searched", "reported_negative")
    w.search(rid, "tamu_fcc", "searched", "missing_evidence")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("reported_negative", ["mpea", "tamu_fcc"], [], [])


def test_records_found_but_insufficient_is_missing_evidence(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "searched")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("missing_evidence", ["mpea"], [], ["tamu_fcc"])


def test_nothing_found_applies_only_to_insufficient_runs(w):
    rid = w.running()
    w.search(rid, "mpea", "searched")
    assert nothing_found(w, rid)[0] is None
    w.complete(rid, "partly_sufficient")
    assert nothing_found(w, rid)[0] is None


def test_run_has_no_stored_nothing_found_column(w):
    assert w.val("SELECT count(*) FROM information_schema.columns WHERE table_name = 'run' "
                 "AND column_name LIKE '%nothing%'") == 0


# --- records: stored is not analysed ---------------------------------------------------------

def test_records_are_never_updated_or_deleted(w):
    rid = w.running()
    rec = w.record(rid)
    for sql in ("UPDATE record SET alloy = 'other' WHERE id = :c", "UPDATE record SET harmonized = '{}' WHERE id = :c",
                "DELETE FROM record WHERE id = :c"):
        w.rejected(sql, "record is append-only", c=rec)
    w.rejected("TRUNCATE record CASCADE", "append-only")


def test_a_record_comes_from_a_source_version_its_run_recorded(w):
    rid = w.running(sources=("mpea",))
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
    rid = w.running()
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported) "
               "VALUES (:r, :sv, '', 'measured', '{}', '{}')", "ck_record_item_key_not_empty",
               r=rid, sv=w.version["mpea"])
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported) "
               "VALUES (:r, :sv, 'measured', '{}', '{}')", "source_item_key", r=rid, sv=w.version["mpea"])
    w.record(rid, key="row-7")
    with pytest.raises(IntegrityError, match="uq_record_origin_per_run"):
        w.record(rid, key="row-7")
    w.record(rid, key="row-7", index=1)  # a second observation from the same row
    other_run = w.running()
    w.record(other_run, key="row-7")
    matched = w.rows("SELECT extraction_run_id FROM record WHERE source_version_id = :sv AND source_item_key = 'row-7' "
                     "AND item_index = 0 ORDER BY extraction_run_id", sv=w.version["mpea"])
    assert [r[0] for r in matched] == [rid, other_run]
    index = w.val("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_record_source_version_id_source_item_key'")
    assert index.endswith("(source_version_id, source_item_key)")


def test_eligibility_is_decided_only_under_a_locked_plan(w):
    rid = w.running()
    rec = w.record(rid)
    with pytest.raises(IntegrityError, match="under a locked plan"):
        w.decide(rid, rec)
    w.lock(rid)
    w.decide(rid, rec, eligible=False, rule="grain size below 0.1 um")
    w.rejected("UPDATE run_record SET eligible = true", "append-only")
    w.rejected("DELETE FROM run_record", "append-only")


def test_a_run_decides_only_on_its_own_records(w):
    other = w.running()
    rec = w.record(other)
    rid = w.running()
    w.lock(rid)
    with pytest.raises(IntegrityError, match="records extracted in that run"):
        w.decide(rid, rec)


def test_a_model_recalled_record_is_stored_but_never_eligible(w):
    rid = w.running()
    w.lock(rid)
    rec = w.record(rid, kind="model_recalled")
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
    """PRD 5.3, the reason for named sets: one survivor in primary, both in the sensitivity set."""
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
    rid, other = w.running(), w.running()
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
    ("check2_passed", "true", "ck_analysis_result_check2_definition"),  # 1 group
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
               "VALUES (:r, 'per_source', :s, 4, 0, 0, 3, false, false, false)",
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
    st = w.stage(rid, "commentator", "commentator")
    sql = ("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check, mismatches) "
           "VALUES (:r, :s, :st, :t, 'other-model', :nc, CAST(:mm AS jsonb))")
    w.rejected(sql, "after the run is completed", r=rid, s=st, st="written", t="x", nc="all_match", mm=None)
    w.complete(rid, "insufficient")
    w.rejected(sql, "ck_commentary_mismatches_listed", r=rid, s=st, st="written", t="x", nc="mismatches", mm=None)
    w.rejected(sql, "ck_commentary_written_has_text_and_check", r=rid, s=st, st="written", t=None, nc=None, mm=None)
    w.run_sql(sql, r=rid, s=st, st="written", t="k = 999", nc="mismatches", mm='["999"]')
    w.rejected("UPDATE commentary SET text = 'changed'", "append-only")


# --- files (owner decision: data files only, 5 MiB) ------------------------------------------------------

SOURCE_FILE = "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:sv, :p, :h, :c)"
ARTIFACT = ("INSERT INTO artifact (run_id, kind, filename, media_type, sha256, content) "
            "VALUES (:r, 'workbook', 'run.xlsx', 'application/octet-stream', :h, :c)")


def test_source_files_are_data_files_up_to_5_mib(w):
    sv = w.version["mpea"]
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(SOURCE_FILE, sv=sv, p="MPEA_dataset.csv", h=sha(at_limit), c=at_limit)
    w.rejected(SOURCE_FILE, "ck_source_file_max_size", sv=sv, p="big.csv", h=sha(over), c=over)
    w.rejected(SOURCE_FILE, "ck_source_file_data_file_type", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
    w.rejected(SOURCE_FILE, "ck_source_file_sha256_matches_content", sv=sv, p="other.csv", h=sha(b"a"), c=b"b")
    w.run_sql(SOURCE_FILE, sv=sv, p="Grain_Size_Summary_v3.xlsx", h=sha(b"x"), c=b"x")
    w.rejected("UPDATE source_file SET content = 'y'", "append-only")
    w.rejected("UPDATE source_version SET label = 'v9'", "append-only")


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

SHA-256 `f61426c2ac6c52b37352b661454ddae11b7410545b66ac1e820417b492d47220`, 11691 bytes.

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
        code = source.replace(docstring, "").upper()
        for forbidden in ("CONCURRENTLY", "AUTOCOMMIT_BLOCK(", "COMMIT", "VACUUM"):
            assert forbidden not in code, (path.name, forbidden)


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

### `tests/test_health.py`

SHA-256 `f87a125405fcb9885e6df3b80666bb352aed8b6973b64d23d09c68e29561c58a`, 3389 bytes.

```python
"""Step 2: the health page, the idle worker and the command line against a real PostgreSQL.
Step 3: /health also reports the schema revision (informational)."""
import logging

from fastapi.testclient import TestClient

from hypocurate import cli, worker
from hypocurate.config import Settings
from hypocurate.db.engine import make_engine
from hypocurate.db.migrate import head_revision
from hypocurate.web.app import create_app

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"


def client(database_url):
    s = Settings(env="development", database_url=database_url, password=PASSWORD,
                 session_secret=SECRET, version="abc123")
    return TestClient(create_app(s, engine=make_engine(database_url)), follow_redirects=False)


def test_health_without_login_database_up(migrated_database):
    r = client(migrated_database).get("/health")
    assert r.status_code == 200
    assert r.json() == {"web": "ok", "database": "ok", "version": "abc123",
                        "schema": {"revision": head_revision(), "at_head": True}}


def test_health_reports_an_unmigrated_database_without_failing(empty_database):
    """The schema field is informational: it never changes the status code."""
    r = client(empty_database).get("/health")
    assert r.status_code == 200
    assert r.json()["schema"] == {"revision": None, "at_head": False}


def test_health_page_in_a_browser(migrated_database):
    r = client(migrated_database).get("/health", headers={"accept": "text/html"})
    assert r.status_code == 200
    assert "Database" in r.text and ">ok<" in r.text
    assert f"<code>{head_revision()}</code> (latest)" in r.text


def test_health_reports_database_down_without_crashing():
    r = client(UNREACHABLE_DB).get("/health")
    assert r.status_code == 503
    assert r.json()["database"] == "unreachable"
    assert r.json()["schema"] == {"revision": None, "at_head": False}


def test_health_shows_no_secrets(database_url):
    c = client(database_url)
    for accept in ["application/json", "text/html"]:
        text = c.get("/health", headers={"accept": accept}).text
        assert PASSWORD not in text and SECRET not in text
        assert database_url not in text and "postgresql" not in text


def test_worker_idles_and_checks_the_database(database_url, monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", database_url)
    sleeps = []
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=2, sleep=sleeps.append)
    assert sleeps == [worker.IDLE_SECONDS] * 2
    assert caplog.text.count("no pipeline yet; database reachable") == 2


def test_worker_logs_an_unreachable_database(monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=1, sleep=lambda s: None)
    assert "database NOT reachable" in caplog.text
    assert "planted-pw-7319" not in caplog.text  # the URL's password is never logged


def test_cli_check_db(database_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert cli.main(["check-db"]) == 0
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    assert cli.main(["check-db"]) == 1
    assert "planted-pw-7319" not in capsys.readouterr().out
```

### `tests/test_skeleton.py`

SHA-256 `392b9dd7f8dbd7407d26f4a438d0ac306477f0bd1c3b2213178c4db26aaa1d30`, 15688 bytes.

```python
"""Step 2: the skeleton's files: layout, locked dependencies, image, compose, Render and CI.
Step 3: the migration service in Compose and the pre-deploy command on Render."""
import os
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

# PRD 6.1
LAYOUT = [
    "hypocurate/pipeline/__init__.py",
    "hypocurate/access/__init__.py",
    "hypocurate/sources/__init__.py",
    "hypocurate/db/__init__.py",
    "hypocurate/web/__init__.py",
    "hypocurate/web/templates",
    "hypocurate/web/static",
    "hypocurate/worker.py",
    "hypocurate/cli.py",
    "tests",
    "Dockerfile",
    "docker-compose.yml",
    "render.yaml",
    "CLAUDE.md",
    "docs/reviews",
    ".github/workflows/tests.yml",
    ".env.example",
    "requirements.lock",
    "requirements-dev.lock",
]
SECRET_NAMES = {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD", "DATABASE_URL"}


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_layout_matches_prd_6_1():
    missing = [p for p in LAYOUT if not (REPO / p).exists()]
    assert missing == []


# --- secrets --------------------------------------------------------------------

def test_env_example_holds_names_only():
    names = set()
    for line in read(".env.example").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        assert sep and value == "", f"{name} has a value in .env.example"
        names.add(name)
    assert SECRET_NAMES | {"HYPOCURATE_ENV"} == names


def test_every_env_file_is_ignored_by_git_and_docker():
    """Review finding 5: .env.production, backups and the like too; only the template passes."""
    for ignore in (".gitignore", ".dockerignore"):
        lines = [l.strip() for l in read(ignore).splitlines()]
        assert ".env*" in lines and "!.env.example" in lines, ignore
        assert lines.index(".env*") < lines.index("!.env.example"), ignore


def text_files():
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "sources", "hypocurate.egg-info"}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            path = Path(root) / name
            if name == ".env" or path.suffix in {".pdf", ".png", ".xlsx"}:
                continue
            try:
                yield path, path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue


KEY_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{10,}",          # Anthropic
    r"sk-(proj-)?[A-Za-z0-9]{20,}",        # OpenAI
    r"gh[pousr]_[A-Za-z0-9]{20,}",         # GitHub
    r"AKIA[0-9A-Z]{16}",                   # AWS
    r"postgres(ql)?://[^:\s/]+:(?!planted-pw-7319@|\$\{|<)[^@\s]+@",  # URL with a password (planted test value allowed)
]


def test_no_keys_or_database_passwords_in_files():
    found = []
    for path, text in text_files():
        for pattern in KEY_PATTERNS:
            if re.search(pattern, text):
                found.append((str(path.relative_to(REPO)), pattern))
    assert found == []


def test_secret_values_from_the_environment_are_in_no_file():
    """When the suite runs with real secrets in its environment (Docker, CI), none appears in a file."""
    values = [os.environ.get(n, "") for n in SECRET_NAMES - {"DATABASE_URL"}]
    values = [v for v in values if len(v) >= 8]
    leaks = [str(p.relative_to(REPO)) for p, text in text_files() if any(v in text for v in values)]
    assert leaks == []


# --- locked dependencies -----------------------------------------------------------

def direct_dependencies(extra=None):
    import tomllib
    project = tomllib.loads(read("pyproject.toml"))["project"]
    deps = project["dependencies"] + (project["optional-dependencies"][extra] if extra else [])
    return {re.split(r"[\[<>=!~ ]", d, maxsplit=1)[0].lower().replace("_", "-") for d in deps}


def locked(path):
    pins = {}
    for m in re.finditer(r"^([A-Za-z0-9_.-]+)==(\S+) \\\n((?:\s+--hash=sha256:[0-9a-f]{64}(?: \\)?\n)+)", read(path), re.M):
        pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def test_every_lock_line_is_pinned_with_hashes():
    for path in ["requirements.lock", "requirements-dev.lock"]:
        names = re.findall(r"^([A-Za-z0-9_.-]+)", read(path), re.M)
        assert names and set(n.lower().replace("_", "-") for n in names) == set(locked(path)), path


def test_direct_dependencies_are_locked():
    assert direct_dependencies() <= set(locked("requirements.lock"))
    assert direct_dependencies("dev") <= set(locked("requirements-dev.lock"))


def test_runtime_and_dev_locks_agree():
    runtime, dev = locked("requirements.lock"), locked("requirements-dev.lock")
    assert {n: dev[n] for n in runtime} == runtime


def test_test_tools_are_not_in_the_runtime_lock():
    assert {"pytest", "httpx2", "pyyaml"}.isdisjoint(locked("requirements.lock"))


# --- Docker image ------------------------------------------------------------------

def dockerfile_stages(text=None):
    """The stages in order, as (name, parent, body)."""
    out = []
    for part in re.split(r"^FROM ", text or read("Dockerfile"), flags=re.M)[1:]:
        parent, name = re.match(r"(\S+) AS (\w+)", part.splitlines()[0]).groups()
        out.append((name, parent, part))
    return out


def stages():
    return {name: body for name, _, body in dockerfile_stages()}


def default_image(text=None):
    """What a plain `docker build .` (Render) produces: the LAST stage and every stage
    it is built FROM, with all the sources they COPY in, in build order."""
    found = dockerfile_stages(text)
    by_name = {name: (parent, body) for name, parent, body in found}
    chain, sources, name = [], [], found[-1][0]
    while name in by_name:
        parent, body = by_name[name]
        chain.append(name)
        stage_sources = []
        for args in re.findall(r"^COPY (.+)$", body, re.M):
            stage_sources += [a for a in args.split() if not a.startswith("--")][:-1]
        sources = stage_sources + sources
        name = parent
    return chain, sources


def default_image_problems(text=None):
    chain, sources = default_image(text)
    problems = []
    if chain[0] != "runtime":
        problems.append(f"the default (last) stage is {chain[0]!r}, not 'runtime'")
    if sources != ["requirements.lock", "hypocurate/", "data/"]:
        problems.append(f"the default image copies {sources}")
    return problems


def test_base_images_are_pinned_by_digest():
    froms = re.findall(r"^FROM (\S+)", read("Dockerfile"), re.M)
    assert froms[0].startswith("python:3.14-slim@sha256:")
    assert re.search(r"image: postgres:17@sha256:[0-9a-f]{64}", read("docker-compose.yml"))


def test_default_image_is_the_clean_runtime_stage():
    """Review finding 1: Render builds the last stage. It must be the runtime stage, and
    neither it nor any stage it is built from may copy tests/, docs/ or the whole repository."""
    assert default_image_problems() == []
    assert default_image()[0] == ["runtime", "base"]


def test_default_image_check_catches_the_old_layout():
    """The step 2 Dockerfile as first reviewed (test stage last) fails the check above."""
    old = """FROM python:3.14-slim AS runtime
COPY requirements.lock ./
COPY hypocurate/ hypocurate/
COPY data/ data/
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app"]
FROM runtime AS test
COPY requirements-dev.lock ./
COPY . .
CMD ["pytest", "-q"]
"""
    problems = default_image_problems(old)
    assert any("not 'runtime'" in p for p in problems)
    assert any("'.'" in p for p in problems)


def test_default_image_serves_the_web_by_default():
    final_name, _, final_body = dockerfile_stages()[-1]
    cmds = re.findall(r"^CMD (.+)$", final_body, re.M)
    assert final_name == "runtime" and len(cmds) == 1
    assert "uvicorn hypocurate.web.main:app" in cmds[0]


def test_installs_require_hashes():
    installs = re.findall(r"pip install (.*)", read("Dockerfile"))
    assert len(installs) == 2 and all("--require-hashes" in i for i in installs)


def test_image_runs_as_non_root():
    for name, body in stages().items():
        users = re.findall(r"^USER (\S+)", body, re.M)
        assert users and users[-1] == "app", name


def test_web_runs_one_process():
    """The login throttle is kept in memory, so it holds only with one web process."""
    assert "--workers 1" in stages()["runtime"]


# --- Docker Compose (review finding 5) ------------------------------------------------

COMPOSE_ENV = {
    "db": {"POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD"},
    "web": {"HYPOCURATE_ENV", "DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"},
    "worker": {"HYPOCURATE_ENV", "DATABASE_URL"},
    "migrate": {"HYPOCURATE_ENV", "DATABASE_URL"},
    "test": {"DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD"},
}


def compose():
    return yaml.safe_load(read("docker-compose.yml"))["services"]


def test_compose_has_web_worker_database_and_test():
    services = compose()
    assert set(services) == set(COMPOSE_ENV)
    assert services["worker"]["command"] == ["python", "-m", "hypocurate.worker"]
    assert services["web"]["build"]["target"] == services["worker"]["build"]["target"] == "runtime"
    assert services["test"]["build"]["target"] == "test"


def test_compose_migrates_before_web_and_worker_start():
    """Step 3: the same command as Render's pre-deploy, in the runtime image."""
    services = compose()
    assert services["migrate"]["command"] == ["python", "-m", "hypocurate.db.migrate", "upgrade"]
    assert services["migrate"]["build"]["target"] == "runtime"
    assert services["migrate"]["depends_on"] == {"db": {"condition": "service_healthy"}}
    for name in ("web", "worker"):
        assert services[name]["depends_on"] == {"db": {"condition": "service_healthy"},
                                                "migrate": {"condition": "service_completed_successfully"}}, name


def test_compose_gives_each_service_only_its_variables():
    for name, service in compose().items():
        assert "env_file" not in service, name
        assert set(service["environment"]) == COMPOSE_ENV[name], name


def test_compose_takes_secret_values_from_env_only():
    for name, service in compose().items():
        env = service["environment"]
        for key in {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD"} & set(env):
            assert env[key].startswith("${" + key + ":?"), (name, key)
        if "DATABASE_URL" in env:
            assert "${POSTGRES_PASSWORD:?" in env["DATABASE_URL"], name


def test_compose_ports_are_bound_to_localhost():
    ports = [p for s in compose().values() for p in s.get("ports", [])]
    assert ports and all(p.startswith("127.0.0.1:") for p in ports)


# --- Render ---------------------------------------------------------------------------

def render():
    return yaml.safe_load(read("render.yaml"))


def test_render_describes_web_worker_and_database():
    r = render()
    kinds = {s["type"]: s for s in r["services"]}
    assert set(kinds) == {"web", "worker"}
    assert [d["name"] for d in r["databases"]] == ["hypocurate-db"]
    assert kinds["web"]["healthCheckPath"] == "/health"
    assert kinds["worker"]["dockerCommand"] == "python -m hypocurate.worker"


def test_render_plans_are_the_approved_ones():
    r = render()
    assert {s["type"]: s["plan"] for s in r["services"]} == {"web": "0.5c-512mb", "worker": "0.5c-512mb"}
    assert r["databases"][0]["plan"] == "0.1c-256mb"
    # 1 GB disk (owner decision, 2026-10-04); Render's default would be 15 GB, which cannot be reduced.
    assert r["databases"][0]["diskSizeGB"] == 1


def test_render_deploys_only_after_checks_pass():
    for s in render()["services"]:
        assert s["autoDeployTrigger"] == "checksPass", s["name"]
        assert "autoDeploy" not in s
        assert s["branch"] == "main"


def test_render_everything_in_one_region_and_database_private():
    r = render()
    regions = {s["region"] for s in r["services"]} | {r["databases"][0]["region"]}
    assert len(regions) == 1
    assert r["databases"][0]["ipAllowList"] == []


def test_render_holds_no_secret_values():
    env = {s["type"]: {v["key"]: v for v in s["envVars"]} for s in render()["services"]}
    web, wk = env["web"], env["worker"]
    assert web["HYPOCURATE_PASSWORD"] == {"key": "HYPOCURATE_PASSWORD", "sync": False}
    assert web["SESSION_SECRET"] == {"key": "SESSION_SECRET", "generateValue": True}
    for e in (web, wk):
        assert e["HYPOCURATE_ENV"]["value"] == "production"
        assert "value" not in e["DATABASE_URL"] and e["DATABASE_URL"]["fromDatabase"]["property"] == "connectionString"


def test_render_migrates_before_each_deploy():
    """Step 3: both services run the migration as the pre-deploy command, so neither
    starts new code on an older schema. A failed migration fails the deploy."""
    for s in render()["services"]:
        assert s["preDeployCommand"] == "python -m hypocurate.db.migrate upgrade", s["name"]


def test_render_worker_gets_no_login_secrets():
    worker = next(s for s in render()["services"] if s["type"] == "worker")
    assert {v["key"] for v in worker["envVars"]} == {"HYPOCURATE_ENV", "DATABASE_URL"}


# --- GitHub Actions (review finding 6) -------------------------------------------------
# Render counts a skipped or neutral check as passed, so nothing may be skippable.

REQUIRED_STEPS = {
    "Build the default image exactly as Render does": "docker build --file ./Dockerfile --tag hypocurate:default .",
    "Check the default image holds no tests, docs or answers": "python scripts/check_runtime_image.py /image",
    "Check no environment file reached an image": "hypocurate:default hypocurate:test",
    "Run the suite in the test image": "docker compose run --rm test",
    "Smoke-test the default image's default command": "hypocurate:default",
    "Start web, worker and database with Compose; check /health": "/health",
}


def workflow():
    return yaml.safe_load(read(".github/workflows/tests.yml"))


def test_ci_runs_on_every_push_and_pull_request_without_filters():
    triggers = workflow()[True]  # YAML 1.1 reads the key "on" as True
    assert triggers == {"push": None, "pull_request": None}


def test_ci_has_every_required_step():
    steps = {s.get("name"): s.get("run", "") for s in workflow()["jobs"]["tests"]["steps"]}
    for name, command in REQUIRED_STEPS.items():
        assert name in steps, name
        assert command in steps[name], name


def test_ci_nothing_can_be_skipped_or_allowed_to_fail():
    wf = workflow()
    assert "continue-on-error" not in read(".github/workflows/tests.yml")
    assert list(wf["jobs"]) == ["tests"]
    job = wf["jobs"]["tests"]
    assert "if" not in job and "strategy" not in job
    assert "defaults" not in wf and "defaults" not in job  # keep GitHub's `bash -eo pipefail`
    for step in job["steps"]:
        assert "shell" not in step, step.get("name")
        if "if" in step:
            assert (step["name"], step["if"]) == ("Logs", "always()")


def test_suite_command_runs_everything():
    """The test image runs plain pytest: no marker, -k or path filter can drop tests."""
    assert re.search(r'^CMD \["pytest", "-q"\]$', stages()["test"], re.M)
    assert "command" not in compose()["test"]  # `docker compose run --rm test` uses that CMD


def test_ci_actions_are_pinned_to_a_commit():
    uses = re.findall(r"uses: (\S+)", read(".github/workflows/tests.yml"))
    assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses)
```

### `tests/test_check_runtime_image.py`

SHA-256 `c1f84df3a9ea89f197471ddc0ea1b212854373c22ed9bdd5997c5e154707030c`, 2921 bytes.

```python
"""Step 2 fix (review finding 1): the deployed-image content check catches what it must."""
import importlib.util
import shutil

import pytest

from hypocurate.sources.manifest import REPO_ROOT

_spec = importlib.util.spec_from_file_location("check", REPO_ROOT / "scripts/check_runtime_image.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


@pytest.fixture
def image(tmp_path):
    """A copy of what the runtime stage puts in /app."""
    root = tmp_path / "app"
    root.mkdir()
    shutil.copytree(REPO_ROOT / "hypocurate", root / "hypocurate",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO_ROOT / "data", root / "data")
    shutil.copy(REPO_ROOT / "requirements.lock", root)
    return root


def test_clean_image_passes(image):
    assert check.problems(image) == []
    assert check.main(["check", str(image)]) == 0


@pytest.mark.parametrize("planted", [
    "tests/test_login.py",
    "docs/reviews/step02_summary.md",
    "data/controlled_duplicates/truth.csv",
    "hypocurate/fixtures/build.py",
    "scripts/check_runtime_image.py",
    "conftest.py",
])
def test_forbidden_paths_fail(image, planted):
    path = image / planted
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n")
    assert check.problems(image)
    assert check.main(["check", str(image)]) == 1


def test_whole_repository_copy_fails(image):
    """What the old default stage (`COPY . .`) produced."""
    shutil.copytree(REPO_ROOT / "tests", image / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO_ROOT / "docs" / "reviews", image / "docs" / "reviews")
    found = check.problems(image)
    assert any("tests" in f for f in found) and any("docs" in f for f in found)


def test_row_answer_in_package_fails(image):
    row, _, _ = check._answer_markers()
    marker = sorted(m for m in row if len(m) > 30)[0]
    (image / "hypocurate" / "leak.py").write_text(f'"""{marker}"""\n')
    assert any("answer material in hypocurate/leak.py" in f for f in check.problems(image))


def test_outcome_vocabulary_under_data_fails(image):
    (image / "data" / "notes.txt").write_text("these two records are exact_duplicate\n")
    assert any("answer material in data/notes.txt" in f for f in check.problems(image))


def test_missing_server_fails(image):
    (image / "hypocurate" / "web" / "main.py").unlink()
    assert "missing hypocurate/web/main.py" in check.problems(image)


@pytest.mark.parametrize("missing", ["hypocurate/db/migrate.py", "hypocurate/db/migrations/env.py",
                                     "hypocurate/db/migrations/versions/0001_data_model.py"])
def test_missing_migrations_fail(image, missing):
    """Step 3: Render's pre-deploy command runs the migrations from inside the deployed image."""
    (image / missing).unlink()
    assert f"missing {missing}" in check.problems(image)
```


## 6. Containers, deployment and the image check

### `render.yaml`

SHA-256 `de6c344addf50197f256f6241434d0b4388592bd175e9bdf3eec53a3d554e142`, 2421 bytes.

```yaml
# Render Blueprint (PRD Section 6, "Hosting"). This file only describes the
# services; nothing exists on Render until the owner connects it as a Blueprint.
# Checked against render.com/docs/blueprint-spec on 2026-10-04.
#
# Plans: the cheapest paid plans (owner decision, 2026-10-04).
# autoDeployTrigger checksPass: Render deploys a commit on main only after its
# GitHub checks pass, and never when a check fails or no check is found.
# Region: all three in one region, so the services reach the database over
# Render's private network. It cannot be changed after creation.
services:
  - type: web
    name: hypocurate-web
    runtime: docker
    region: oregon
    plan: 0.5c-512mb
    branch: main
    autoDeployTrigger: checksPass
    dockerfilePath: ./Dockerfile
    dockerContext: .
    # Step 3: migrate before the new version starts. If it fails, Render fails the
    # deploy and keeps the previous version running (README, "Database migrations").
    preDeployCommand: python -m hypocurate.db.migrate upgrade
    healthCheckPath: /health
    envVars:
      - key: HYPOCURATE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: hypocurate-db
          property: connectionString
      - key: HYPOCURATE_PASSWORD
        sync: false
      - key: SESSION_SECRET
        generateValue: true

  # The worker does not serve pages, so it gets no login secrets.
  - type: worker
    name: hypocurate-worker
    runtime: docker
    region: oregon
    plan: 0.5c-512mb
    branch: main
    autoDeployTrigger: checksPass
    dockerfilePath: ./Dockerfile
    dockerContext: .
    dockerCommand: python -m hypocurate.worker
    # Both services run it; an advisory lock makes the second wait and find the schema at head.
    preDeployCommand: python -m hypocurate.db.migrate upgrade
    envVars:
      - key: HYPOCURATE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: hypocurate-db
          property: connectionString

databases:
  - name: hypocurate-db
    region: oregon
    plan: 0.1c-256mb
    # Owner decision, 2026-10-04: 1 GB (about $0.30/month). Without this Render
    # gives a new database a 15 GB disk. A disk can be enlarged, never reduced.
    diskSizeGB: 1
    postgresMajorVersion: "17"
    databaseName: hypocurate
    user: hypocurate
    # No connections from outside Render's private network.
    ipAllowList: []
```

### `docker-compose.yml`

SHA-256 `640838be14e7c357f75dc2c9084a7a3051c2aaee6d6a43e6d7d4b05f8d715fa6`, 2673 bytes.

```yaml
# Local work: database, web service, worker; the suite with `docker compose run --rm test`.
# Values come from .env (see .env.example), never from this file. Compose reads
# .env only to fill in the ${...} below; each service gets only the variables it
# needs (second-model review of step 2, finding 5).
x-database-url: &database-url postgresql://hypocurate:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@db:5432/hypocurate

x-app: &app
  build:
    context: .
    target: runtime
  image: hypocurate:runtime
  depends_on:
    db:
      condition: service_healthy

services:
  db:
    image: postgres:17@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f
    environment:
      POSTGRES_USER: hypocurate
      POSTGRES_DB: hypocurate
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hypocurate -d hypocurate"]
      interval: 2s
      timeout: 3s
      retries: 30

  # Applies the migrations once, as Render's pre-deploy command does; web and
  # worker start only after it has succeeded.
  migrate:
    <<: *app
    command: ["python", "-m", "hypocurate.db.migrate", "upgrade"]
    environment:
      HYPOCURATE_ENV: ${HYPOCURATE_ENV:-development}
      DATABASE_URL: *database-url

  web:
    <<: *app
    depends_on: &after-migrate
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    environment:
      HYPOCURATE_ENV: ${HYPOCURATE_ENV:-development}
      DATABASE_URL: *database-url
      HYPOCURATE_PASSWORD: ${HYPOCURATE_PASSWORD:?set HYPOCURATE_PASSWORD in .env}
      SESSION_SECRET: ${SESSION_SECRET:?set SESSION_SECRET in .env}
    # Plain HTTP locally: reachable from this machine only.
    ports:
      - "127.0.0.1:8000:8000"

  worker:
    <<: *app
    depends_on: *after-migrate
    command: ["python", "-m", "hypocurate.worker"]
    environment:
      HYPOCURATE_ENV: ${HYPOCURATE_ENV:-development}
      DATABASE_URL: *database-url

  # The secrets are passed only so that the suite can check that none of their
  # values appears in any file (tests/test_skeleton.py).
  test:
    <<: *app
    build:
      context: .
      target: test
    image: hypocurate:test
    profiles: ["test"]
    environment:
      DATABASE_URL: *database-url
      HYPOCURATE_PASSWORD: ${HYPOCURATE_PASSWORD:?set HYPOCURATE_PASSWORD in .env}
      SESSION_SECRET: ${SESSION_SECRET:?set SESSION_SECRET in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}

volumes:
  pgdata:
```

### `scripts/check_runtime_image.py`

SHA-256 `68c9424780570e7536d6e7f564534ab0d83f2ffb7eb541c7da18903aeb73786f`, 3333 bytes.

```python
"""Check the contents of the deployed image (second-model review of step 2, finding 1).

Usage: python scripts/check_runtime_image.py <dir>
where <dir> is the image's /app copied out with `docker cp`. Run from the
repository (the test image in CI), because the answer markers come from the
step 1 tests, which are never in the deployed image.

The image must hold exactly the package, the frozen data and the runtime lock:
no tests/, no docs/, no answer file, no builder, no review document, and no
answer material in any file. Exit status 1 and one line per problem otherwise.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOP_LEVEL = {"hypocurate", "data", "requirements.lock"}
REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.json", "requirements.lock",
            # Step 3: Render's pre-deploy command migrates from inside the deployed image.
            "hypocurate/db/migrate.py", "hypocurate/db/migrations/env.py",
            "hypocurate/db/migrations/versions/0001_data_model.py"]
FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")


def _answer_markers():
    spec = importlib.util.spec_from_file_location("step1_tests", REPO / "tests/test_controlled_duplicates.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    row = {m.lower() for m in tests._row_specific_markers()}
    generic = {m.lower() for m in tests._generic_outcome_markers()}
    return row, generic, tests.FROZEN_SOURCE_FILES


def problems(root: Path) -> list[str]:
    root = Path(root)
    found = []
    top = {p.name for p in root.iterdir()}
    if top != TOP_LEVEL:
        found.append(f"top level is {sorted(top)}, expected {sorted(TOP_LEVEL)}")
    found += [f"missing {r}" for r in REQUIRED if not (root / r).is_file()]

    row, generic, frozen = _answer_markers()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        if FORBIDDEN_DIRS & set(parts if path.is_dir() else parts[:-1]):
            found.append(f"forbidden directory: {rel}")
            continue
        if not path.is_file():
            continue
        if FORBIDDEN_NAMES.match(path.name):
            found.append(f"forbidden file: {rel}")
        if rel in frozen:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        # Row-specific answers are forbidden everywhere; the outcome vocabulary only
        # under data/ (the package uses it from step 6), as in the step 1 tests.
        markers = row | generic if rel.startswith("data/") else row
        hits = sorted(m for m in markers if m in text)
        if hits:
            found.append(f"answer material in {rel}: {hits[:3]}")
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    found = problems(Path(argv[1]))
    for line in found:
        print(line)
    print("runtime image OK" if not found else f"{len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```


## 7. Dependencies

### `pyproject.toml`

SHA-256 `a2bebac12fa1294b92a0c4c397dcaaf9f0ceac9ada15619521cbc47900366539`, 910 bytes.

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "hypocurate"
version = "0.1.0"
description = "Tests a scientific hypothesis in words against registered data sources."
requires-python = ">=3.12"
# Direct dependencies. The exact versions installed, with hashes, are in
# requirements.lock and requirements-dev.lock (pip-compile --generate-hashes).
dependencies = [
    "pandas>=2.2",
    "openpyxl>=3.1",
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "jinja2>=3.1",
    "itsdangerous>=2.2",
    "python-multipart>=0.0.9",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.2",
    "alembic>=1.16",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx2>=2.13", "pyyaml>=6"]

[project.scripts]
hypocurate = "hypocurate.cli:main"

[tool.setuptools.packages.find]
include = ["hypocurate*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

### `requirements.lock`

SHA-256 `cabb3cd027a6564144c1ea56c2fe2054dab2aed283ee1f2ac4492b1797aa1e6e`, 50903 bytes. Hash lines left out.

```text
#
# This file is autogenerated by pip-compile with Python 3.14
# by the following command:
#
#    pip-compile --allow-unsafe --generate-hashes --no-index --output-file=requirements.lock --strip-extras pyproject.toml
#
alembic==1.20.0 \
    # via hypocurate (pyproject.toml)
annotated-doc==0.0.5 \
    # via fastapi
annotated-types==0.8.0 \
    # via pydantic
anyio==4.15.1 \
    # via starlette
click==8.5.0 \
    # via uvicorn
et-xmlfile==2.0.0 \
    # via openpyxl
fastapi==0.142.2 \
    # via hypocurate (pyproject.toml)
h11==0.16.0 \
    # via uvicorn
idna==3.20 \
    # via anyio
itsdangerous==2.2.0 \
    # via hypocurate (pyproject.toml)
jinja2==3.1.6 \
    # via hypocurate (pyproject.toml)
mako==1.4.3 \
    # via alembic
markupsafe==3.0.4 \
    # via
    #   jinja2
    #   mako
numpy==2.5.3 \
    # via pandas
openpyxl==3.1.5 \
    # via hypocurate (pyproject.toml)
opentelemetry-api==1.45.0 \
    # via fastapi
pandas==3.0.6 \
    # via hypocurate (pyproject.toml)
psycopg==3.3.6 \
    # via hypocurate (pyproject.toml)
psycopg-binary==3.3.6 \
    # via psycopg
pydantic==2.13.5 \
    # via fastapi
pydantic-core==2.46.5 \
    # via pydantic
python-dateutil==2.9.0.post0 \
    # via pandas
python-multipart==0.0.32 \
    # via hypocurate (pyproject.toml)
six==1.17.0 \
    # via python-dateutil
sqlalchemy==2.1.3 \
    # via
    #   alembic
    #   hypocurate (pyproject.toml)
starlette==1.7.0 \
    # via fastapi
typing-extensions==4.16.0 \
    # via
    #   alembic
    #   anyio
    #   fastapi
    #   opentelemetry-api
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   typing-inspection
typing-inspection==0.4.4 \
    # via
    #   fastapi
    #   pydantic
uvicorn==0.54.0 \
    # via hypocurate (pyproject.toml)
```

### `requirements-dev.lock`

SHA-256 `31fb561d0f0848eb067593cda30540c78006445e80f44b9b448f4be30b4b670c`, 58942 bytes. Hash lines left out.

```text
#
# This file is autogenerated by pip-compile with Python 3.14
# by the following command:
#
#    pip-compile --allow-unsafe --extra=dev --generate-hashes --no-index --output-file=requirements-dev.lock --strip-extras pyproject.toml
#
alembic==1.20.0 \
    # via hypocurate (pyproject.toml)
annotated-doc==0.0.5 \
    # via fastapi
annotated-types==0.8.0 \
    # via pydantic
anyio==4.15.1 \
    # via
    #   httpx2
    #   starlette
click==8.5.0 \
    # via uvicorn
et-xmlfile==2.0.0 \
    # via openpyxl
fastapi==0.142.2 \
    # via hypocurate (pyproject.toml)
h11==0.16.0 \
    # via
    #   httpcore2
    #   uvicorn
httpcore2==2.13.1 \
    # via httpx2
httpx2==2.13.1 \
    # via hypocurate (pyproject.toml)
idna==3.20 \
    # via
    #   anyio
    #   httpx2
iniconfig==2.3.0 \
    # via pytest
itsdangerous==2.2.0 \
    # via hypocurate (pyproject.toml)
jinja2==3.1.6 \
    # via hypocurate (pyproject.toml)
mako==1.4.3 \
    # via alembic
markupsafe==3.0.4 \
    # via
    #   jinja2
    #   mako
numpy==2.5.3 \
    # via pandas
openpyxl==3.1.5 \
    # via hypocurate (pyproject.toml)
opentelemetry-api==1.45.0 \
    # via fastapi
packaging==26.3 \
    # via pytest
pandas==3.0.6 \
    # via hypocurate (pyproject.toml)
pluggy==1.6.0 \
    # via pytest
psycopg==3.3.6 \
    # via hypocurate (pyproject.toml)
psycopg-binary==3.3.6 \
    # via psycopg
pydantic==2.13.5 \
    # via fastapi
pydantic-core==2.46.5 \
    # via pydantic
pygments==2.21.0 \
    # via pytest
pytest==9.1.1 \
    # via hypocurate (pyproject.toml)
python-dateutil==2.9.0.post0 \
    # via pandas
python-multipart==0.0.32 \
    # via hypocurate (pyproject.toml)
pyyaml==6.0.3 \
    # via hypocurate (pyproject.toml)
six==1.17.0 \
    # via python-dateutil
sqlalchemy==2.1.3 \
    # via
    #   alembic
    #   hypocurate (pyproject.toml)
starlette==1.7.0 \
    # via fastapi
truststore==0.10.4 \
    # via
    #   httpcore2
    #   httpx2
typing-extensions==4.16.0 \
    # via
    #   alembic
    #   anyio
    #   fastapi
    #   opentelemetry-api
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   typing-inspection
typing-inspection==0.4.4 \
    # via
    #   fastapi
    #   pydantic
uvicorn==0.54.0 \
    # via hypocurate (pyproject.toml)
```


## 8. README

### `README.md`

SHA-256 `0cae824ce52f3c4cf790cadc50f659730cd12c4fd5859a508fd7d828329128a1`, 8042 bytes.

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
- **What the database enforces, and its limit.** Triggers and CHECK constraints refuse, among others: editing a locked plan; changing a frozen dataset; updating or deleting a record; a verdict on a run that is not sufficient. A refusal raises an error starting `hypocurate:`. The triggers stop the application and ordinary edits; the database owner can still drop a trigger, so they are not tamper-proof. The fingerprints are the cross-check.
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


## 9. Test output

```
$ .venv/bin/pytest -v tests/test_migrations.py tests/test_data_model.py tests/test_health.py tests/test_skeleton.py tests/test_check_runtime_image.py
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
tests/test_data_model.py::test_no_source_searched_is_failed_search PASSED
tests/test_data_model.py::test_a_reported_negative_result_is_kept_distinct PASSED
tests/test_data_model.py::test_records_found_but_insufficient_is_missing_evidence PASSED
tests/test_data_model.py::test_nothing_found_applies_only_to_insufficient_runs PASSED
tests/test_data_model.py::test_run_has_no_stored_nothing_found_column PASSED
tests/test_data_model.py::test_records_are_never_updated_or_deleted PASSED
tests/test_data_model.py::test_a_record_comes_from_a_source_version_its_run_recorded PASSED
tests/test_data_model.py::test_records_are_extracted_while_running_and_before_the_freeze PASSED
tests/test_data_model.py::test_every_record_names_its_origin PASSED
tests/test_data_model.py::test_eligibility_is_decided_only_under_a_locked_plan PASSED
tests/test_data_model.py::test_a_run_decides_only_on_its_own_records PASSED
tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible PASSED
tests/test_data_model.py::test_a_set_exists_only_for_an_analysis_the_locked_plan_names PASSED
tests/test_data_model.py::test_primary_holds_only_eligible_records_and_sensitivity_sets_may_hold_others PASSED
tests/test_data_model.py::test_a_possible_duplicate_counts_once_in_primary_and_twice_in_its_sensitivity_set PASSED
tests/test_data_model.py::test_nothing_changes_after_the_freeze PASSED
tests/test_data_model.py::test_no_eligible_records_means_no_freeze PASSED
tests/test_data_model.py::test_the_freeze_matches_the_primary_set_and_needs_every_named_set PASSED
tests/test_data_model.py::test_a_flag_is_classified_once_before_the_freeze PASSED
tests/test_data_model.py::test_flags_stop_at_the_freeze PASSED
tests/test_data_model.py::test_a_flag_names_records_of_its_own_run PASSED
tests/test_data_model.py::test_results_come_after_the_freeze PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[check2_passed-true-ck_analysis_result_check2_definition] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[std_error-1.0-ck_analysis_result_std_error_iff_check2] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[p_value-0.01-ck_analysis_result_p_value_iff_check2] PASSED
tests/test_data_model.py::test_the_validity_checks_cannot_be_waived[resid_df-5-ck_analysis_result_resid_df_definition] PASSED
tests/test_data_model.py::test_check_one_failing_means_no_estimate PASSED
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
tests/test_data_model.py::test_a_run_without_calls_totals_zero PASSED
tests/test_data_model.py::test_no_table_stores_token_or_cost_totals PASSED
tests/test_data_model.py::test_a_finished_stage_result_is_final PASSED
tests/test_data_model.py::test_commentary_comes_after_completion_and_lists_mismatches PASSED
tests/test_data_model.py::test_source_files_are_data_files_up_to_5_mib PASSED
tests/test_data_model.py::test_artifacts_up_to_5_mib PASSED
tests/test_data_model.py::test_domains_are_seeded_and_fixed PASSED
tests/test_data_model.py::test_the_audit_log_is_append_only PASSED
tests/test_health.py::test_health_without_login_database_up PASSED
tests/test_health.py::test_health_reports_an_unmigrated_database_without_failing PASSED
tests/test_health.py::test_health_page_in_a_browser PASSED
tests/test_health.py::test_health_reports_database_down_without_crashing PASSED
tests/test_health.py::test_health_shows_no_secrets PASSED
tests/test_health.py::test_worker_idles_and_checks_the_database PASSED
tests/test_health.py::test_worker_logs_an_unreachable_database PASSED
tests/test_health.py::test_cli_check_db PASSED
tests/test_skeleton.py::test_layout_matches_prd_6_1 PASSED
tests/test_skeleton.py::test_env_example_holds_names_only PASSED
tests/test_skeleton.py::test_every_env_file_is_ignored_by_git_and_docker PASSED
tests/test_skeleton.py::test_no_keys_or_database_passwords_in_files PASSED
tests/test_skeleton.py::test_secret_values_from_the_environment_are_in_no_file PASSED
tests/test_skeleton.py::test_every_lock_line_is_pinned_with_hashes PASSED
tests/test_skeleton.py::test_direct_dependencies_are_locked PASSED
tests/test_skeleton.py::test_runtime_and_dev_locks_agree PASSED
tests/test_skeleton.py::test_test_tools_are_not_in_the_runtime_lock PASSED
tests/test_skeleton.py::test_base_images_are_pinned_by_digest PASSED
tests/test_skeleton.py::test_default_image_is_the_clean_runtime_stage PASSED
tests/test_skeleton.py::test_default_image_check_catches_the_old_layout PASSED
tests/test_skeleton.py::test_default_image_serves_the_web_by_default PASSED
tests/test_skeleton.py::test_installs_require_hashes PASSED
tests/test_skeleton.py::test_image_runs_as_non_root PASSED
tests/test_skeleton.py::test_web_runs_one_process PASSED
tests/test_skeleton.py::test_compose_has_web_worker_database_and_test PASSED
tests/test_skeleton.py::test_compose_migrates_before_web_and_worker_start PASSED
tests/test_skeleton.py::test_compose_gives_each_service_only_its_variables PASSED
tests/test_skeleton.py::test_compose_takes_secret_values_from_env_only PASSED
tests/test_skeleton.py::test_compose_ports_are_bound_to_localhost PASSED
tests/test_skeleton.py::test_render_describes_web_worker_and_database PASSED
tests/test_skeleton.py::test_render_plans_are_the_approved_ones PASSED
tests/test_skeleton.py::test_render_deploys_only_after_checks_pass PASSED
tests/test_skeleton.py::test_render_everything_in_one_region_and_database_private PASSED
tests/test_skeleton.py::test_render_holds_no_secret_values PASSED
tests/test_skeleton.py::test_render_migrates_before_each_deploy PASSED
tests/test_skeleton.py::test_render_worker_gets_no_login_secrets PASSED
tests/test_skeleton.py::test_ci_runs_on_every_push_and_pull_request_without_filters PASSED
tests/test_skeleton.py::test_ci_has_every_required_step PASSED
tests/test_skeleton.py::test_ci_nothing_can_be_skipped_or_allowed_to_fail PASSED
tests/test_skeleton.py::test_suite_command_runs_everything PASSED
tests/test_skeleton.py::test_ci_actions_are_pinned_to_a_commit PASSED
tests/test_check_runtime_image.py::test_clean_image_passes PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[tests/test_login.py] PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[docs/reviews/step02_summary.md] PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[data/controlled_duplicates/truth.csv] PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[hypocurate/fixtures/build.py] PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[scripts/check_runtime_image.py] PASSED
tests/test_check_runtime_image.py::test_forbidden_paths_fail[conftest.py] PASSED
tests/test_check_runtime_image.py::test_whole_repository_copy_fails PASSED
tests/test_check_runtime_image.py::test_row_answer_in_package_fails PASSED
tests/test_check_runtime_image.py::test_outcome_vocabulary_under_data_fails PASSED
tests/test_check_runtime_image.py::test_missing_server_fails PASSED
tests/test_check_runtime_image.py::test_missing_migrations_fail[hypocurate/db/migrate.py] PASSED
tests/test_check_runtime_image.py::test_missing_migrations_fail[hypocurate/db/migrations/env.py] PASSED
tests/test_check_runtime_image.py::test_missing_migrations_fail[hypocurate/db/migrations/versions/0001_data_model.py] PASSED
============================= 177 passed in 33.85s =============================

$ .venv/bin/pytest -q   (whole suite)
316 passed in 35.14s

$ docker compose run --rm test
316 passed in 35.97s
```
