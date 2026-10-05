# Build step 5 — summary for review

Date: 2026-10-05. Branch: `step-05-access`. **Status: first build reviewed by the second model (ChatGPT, 2026-10-05: "serious gaps"; six findings, all accepted by the owner with a threat-model decision); fixes built; re-check (2026-10-05): threat model accepted, four findings closed, three narrow items left, "no further blocker under the agreed threat model". The three items were fixed and merged on their regression tests without a further review round, by the owner's decision (section "Re-check"). Merged into `main` (`81ce23c`, 2026-10-05) and live (see "Live deployment").** PRD Section 15, step 5: "Access layer. Role and stage objects, allowed-field lists, the audit log, and the tests for criterion 14.2 including the planted-value test. This is built before any agent."

The suite is the gate. This summary is for the second model's re-check (PRD 13.2), which uses `docs/reviews/checklist.md`. The review text is in `docs/reviews/step05_review_chatgpt.md`, the re-check in `docs/reviews/step05_recheck_chatgpt.md`. It describes the state **after** the fixes; section "Second-model review and fixes" maps each finding to its fix.

**Not built, as instructed:** any agent, any model call, eligibility or duplicate decisions, statistics, screens. **No migration** (`audit_log` exists since step 3). No change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose or dependencies.

## The threat model (owner, 2026-10-05), and what step 5 does and does not claim

The access layer and its tests guard against **our own code leaking data to a model**. In sprint 1 agents are language models that return text only: they never execute code and never receive SQL or file tools. Only trusted, reviewed code runs, and a trusted dispatcher binds each agent call to a run, role, stage and source. Agents that execute code go to the backlog, with operating-system isolation as a precondition. Recorded in CLAUDE.md (new rule 14 and a "Threat model" section) and in the register (`threat_model`).

**Claims withdrawn.** The owner's earlier instruction "unreachable by construction" overreached, and the first build's summary and packet claimed too much from it. Corrected:
- "tests/, docs/reviews/ and answer material are unreachable by construction" → the **file guard is a tripwire** against accidental file access by trusted code, not a sandbox. **The only construction-level guarantee is that the deployed image contains no `tests/` or `docs/`** (Dockerfile; `scripts/check_runtime_image.py` in CI).
- "after installation every ctypes load, symbol lookup and foreign call is refused" → new library loads and foreign calls raise events the hook refuses, but preloaded `ctypes` still reads memory directly (`from_address`, tested). The review reports `string_at` working in its setup; in our runs it was refused (it raises the call event). Either way it is no barrier to code that tries.
- "a refusal is committed before the error is raised, so the row survives" → still true for policy refusals; failures are now logged too, and **durable logging in the database is not unconditional** (fallback: the process log).
- "the planted value appears in no role's complete input" → the **projected-data test** shows that the planted values are not copied into the *data* a blinded role is given; it does not test the model request, and the blinded views disclose some things by design (section "Accepted disclosures").
- "pipeline code reaches data only through the access layer" (a static import scan) → removed; it was vacuous. The guarantee is the dispatcher design plus CLAUDE.md rule 14, for trusted code.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/assumptions.json` | The owner's pairing-rule decision (first commit). Entries for this step's defaults and the review's decisions (section "Assumptions register"). |
| `hypocurate/access/allowlist.py` | The access contract in one place: threat model, roles, stages, field catalogue, `ALLOWED[role][stage]`, outcome fields, condition-summary fields, named source fields, **`PLAN_SCHEMA`** and `POWER_SCHEMA` (nested), **`ACCEPTED_DISCLOSURES`**. |
| `hypocurate/access/vocabulary.py` | **Controlled vocabularies** (category values; codes our own code writes), the marker `unrecognized`, unrecognized counts, DOI syntax. |
| `hypocurate/access/context.py` | **`AccessContext`**: immutable (frozen, slots): run, role, stage, source, agent setting. |
| `hypocurate/access/dispatch.py` | **`bind(engine, run_id, agent_setting_id, source_key=None)`**: the only way to obtain an access object. |
| `hypocurate/access/layer.py` | `Access` (no public constructor; immutable): `get(field)` and `read_all()`; the transaction, the audit rows, denial and failure codes, failure rows and the process-log fallback. |
| `hypocurate/access/fields.py` | One reader per field, built from named keys, vocabularies and the plan schema. |
| `hypocurate/access/stage.py`, `inputs.py`, `errors.py` | The stage from the database; `role_input` (one transaction under the run's lock); `AccessDenied` and `AccessFailed`. |
| `hypocurate/access/file_guard.py`, `guarded.py`, `guard_probe.py` | The tripwire, its guarded process, and probes; refusals reported and logged. |
| `hypocurate/sources/connection.py` | "Test connection" reports unrecognized category counts per field. |
| `hypocurate/sources/normalize.py`, `versions.py` | `same_alloy_key`; registration refuses to run under the guard. |
| `CLAUDE.md` | Rule 14 and the threat model. |
| `README.md`, `scripts/check_runtime_image.py` | The access section, rewritten; the image must contain the access modules. |
| `tests/access_world.py`, `tests/access_testing.py` | Runs at every stage with planted values (now also inside every allowed field) and recorded agent settings; the tests' only way to build an access object outside the dispatcher. |
| `tests/test_access_layer.py`, `test_access_projected.py`, `test_access_dispatch.py`, `test_access_files.py` | 44, 13, 22 and 20 tests. |

## Register update: the conflict pairing rule (owner, 2026-10-05)

`conflict_pairing_rule`: open → in force. "Duplicates and conflicts are looked for only between records from different sources that cite the same paper with the same alloy, grain size and test conditions. Rows within one source are always separate measurements (repeat specimens)." Known weakness, in the notes: a source that repeats its own row by mistake is not caught. Applied: not yet, step 6. Not reviewed by an expert. Its history keeps the open state. The notes of `values_disagree_tolerance` and `observation_unit` point to the decision. The register now has **no open decision**.

## The owner's change before the review (2026-10-05)

On a run that ended with no dataset frozen, the Commentator receives only what the Analyst received for the gap report (no outcome values, no row-level records), plus the Analyst's gap report and the run's outcome. In the first build it received every stored record, including outcome values never analysed (the first build's open item 5).

- **A new stage**, `final_without_freeze`: a completed run with no `run_snapshot`. A completed run with a freeze is `final`.
- **Two new fields**: `gap_report` (stage, attempt, status and output of each Analyst stage of the run; not their input, reasoning or tool calls) and `outcome` (status, outcome, verdict, exploratory).
- **The Commentator's lists**: `final` = the Analyst's `analysis` fields (the gap-report summaries, which the first build added there for the no-freeze case, are no longer needed); `final_without_freeze` = the gap-report fields + `gap_report` + `outcome`.
- **Register**: `access_allow_lists` states the rule, its stage list includes the new stage, and its history keeps the first build's rule; decided by the owner. `access_stage_from_database` states the two final stages. `gap_report_condition_summaries` notes that the Commentator receives the same input.
- **Tests**: the matrix now covers eight run states; the allow-list test checks both Commentator lists; the completion test is split into one without a freeze and one after a freeze; a new test checks the Commentator's exact input without a freeze; **the planted-value test now covers the Commentator's complete input without a freeze**; the other-run test covers the new stage.

## The owner's decisions in planning (2026-10-05)

1. **The Critic sees metadata, no numbers.** Source descriptions, never source content. Per record: id, source, origin key, alloy label and composition, paper reference and DOI, each field's status, and the category values (test type, temperature band, phase class, microstructure, processing method). No measured number of any field: not grain size, not temperature. Flags: kind, category and record ids; never the numbers compared.
2. **The gap report** (a run that ended with no dataset frozen): the Analyst gets everything except outcomes, **plus condition summaries computed by code**: per alloy and overall, the count and the minimum and maximum of grain size and of test temperature, and the counts by test type and by phase. Summaries only: no row-level value, no outcome value, no statistic derived from outcomes. Included in the planted-value test.
3. The other points raised in planning stand as recommended (next section).

**Additions at approval:**
- **A. Single-run scope**, stated in `allowlist.py` and tested with a value planted in other runs.
- **B. `sources_meta` is a fixed set of named plain fields**, tested with a value planted in the source's free text.
- **C. File guard scope**: which entry points install it; it cannot be installed in a process that later needs those paths; templates, the database driver and the certificate bundle work under it; one private scratch directory; writes elsewhere refused. (After the review: a tripwire, not a sandbox; see below.)
- **D. Audit-log volume** in the storage estimate (section "Audit-log volume").

## The allow-list (role × stage × fields)

Stages are read from the database on every call:
- `none`: queued or failed;
- `before_lock`: running, no plan;
- `curation`: plan locked, no freeze, no "no dataset frozen" record;
- `analysis`: dataset frozen, running;
- `closed_without_freeze`: the run-level calibration row with reason `no_dataset_frozen` exists, running;
- `final`: completed after a dataset freeze;
- `final_without_freeze`: completed with no dataset frozen.

| Role | Stage | Fields |
|---|---|---|
| Planner | before_lock | `claim`, `domain`, `sources_meta`, `tag_values`, `record_counts` |
| Curator | curation | `plan_fields_to_extract`, `sources_meta` (its own source), `source_content` (its own source's sealed files) |
| Critic | curation | `sources_meta`, `record_metadata`, `flags_kind` |
| Analyst | analysis | `claim`, `domain`, `sources_meta`, `plan`, `records_full`, `decisions`, `flags_full`, `results`, `coverage`, `stage_outputs`, `run_cost` |
| Analyst | closed_without_freeze | `claim`, `domain`, `sources_meta`, `plan`, `coverage`, `stored_record_counts`, `decisions`, `flags_kind`, `condition_summaries` |
| Commentator | final | the Analyst's `analysis` fields |
| Commentator | final_without_freeze | the Analyst's `closed_without_freeze` fields, plus `gap_report` and `outcome` |
| any | any other stage | nothing |

**The blinded views** are the Planner's, the Critic's, the gap report's and the Commentator's without a freeze. In them:
- **category values** (test type, temperature band, phase class, microstructure, processing method) come from fixed vocabularies, else `unrecognized`. The stored value is unchanged. Unrecognized values are counted per field and source (never shown) in "test connection" and in the run's `coverage`;
- **codes** (flag kinds and categories, eligibility rules, analysis-set and sensitivity keys) come from fixed vocabularies, else `unrecognized`;
- the **Critic's record view** has no paper title and no origin key. It has the DOI only if it has DOI syntax, and an alloy label derived by code from the composition;
- the **plan** is projected recursively by `PLAN_SCHEMA`: named keys at every level, vocabulary leaves (else the marker), numbers, integers, field names and units. There are no free-text leaves. `power_assumptions` goes through `POWER_SCHEMA`;
- **coverage** carries codes and counts only, with no failure text;
- **`sources_meta`**: name, licence and fields available come from the code's `SOURCES`; type, kind of data and grouping unit come from the sealed version the run recorded. Nothing comes from the mutable source registry.

**Outcome fields**, withheld wherever outcomes are withheld: yield strength and its spread, tensile strength, hardness and its spread.

**Single-run scope.** Every field reads only the run's own rows and the sealed source versions the run recorded. `domain` and `tag_values` (approved values only) are reference lists.

### Accepted disclosures (register `accepted_disclosures`; `ACCEPTED_DISCLOSURES`)

The blinding claim is limited to this: no outcome value is copied into a blinded view from a stored outcome field, a value as reported, a flag's numbers, a stage's text, or text outside a vocabulary. The blinded views still disclose, by design:
1. counts by field status (for example how many yield strengths a source reports or cannot read);
2. flag kinds and categories (for example that two values differ beyond the tolerance);
3. condition summaries, which reveal an exact grain size or temperature when a group has one record;
4. compositions and the alloy labels derived from them;
5. DOIs with DOI syntax, which may contain digits (tested);
6. text written or approved by people: the claim, approved tag values, and source names and licences in code;
7. numbers in the locked plan (thresholds, minimums), written before any record exists;
8. the Analyst's gap report, passed to the Commentator on a run with no dataset frozen;
9. timing of calls and the existence of refusals. **Timing is not protected.**

## Points in PRD 4 that were unclear or contradictory, and how they are resolved

1. **The Critic "sees sources" but never outcome values**, and the source files contain the outcome values: resolved by decision 1 (descriptions, never content).
2. **The Analyst writes the gap report** (PRD 3, step 8), but **sees data only "after the dataset freeze"** (PRD 4, 5.6), which an insufficient run never reaches: resolved by decision 2.
3. **Fields the PRD does not assign**: the plan for the Critic (not given); tag lists for the Planner (given: approved values); search coverage (Analyst; Commentator); text handed between stages (Analyst after the freeze, Commentator after a freeze; the Commentator without a freeze gets only the Analyst's gap report); tokens and cost (Analyst, Commentator after a freeze); eligibility decisions for the Critic (not given); the domain for the Curator (not given); the agent's instruction text (no field: it is configuration, not data; it is part of the model request that step 8 must test).
4. **The table lists Inclusion and Checks, which are code**: they get access objects in the steps that build them (6, 7), so their reads are logged too. Not built now.
5. **The experiment flag that may relax the contract** (PRD 4): not built. `test_experiment_flags_relax_nothing` shows that flags on a run change no list. **Backlog** (PRD 18).
6. **"Roles that can add or remove records never see outcome values"** sits awkwardly with the Curator, which reads source content and extracts records. It has no say over inclusion; whether its extraction is complete is a step 8 question (with step 4's note that adapters, which are code, extract tabular sources).
7. **The Planner's counts**: computed by code from the sealed sources (records are stored only after the lock); every property field is treated as an outcome.
8. **A possible self-wait**: the audit row is a write to the run, so an access call takes the run's lock. Code must never call the access layer while holding the same run's lock. A 5-second lock timeout turns that into an error instead of a hang.
9. **The plan's structure**: after the review, step 5 defines the plan's whole nested schema (`PLAN_SCHEMA`, owner 2026-10-05); step 6's plan model must follow it.

## How an access object is obtained and used

**The dispatcher** (`dispatch.bind`), called by trusted orchestration (steps 8, 9) for one agent call:
- it takes a run and the **agent setting** being invoked, never a role;
- the **role** is the one recorded for that setting in the run's `run_agent_setting` rows. A setting not recorded for the run is refused (`setting_not_recorded`);
- the **stage** is read from the database;
- a **source** is accepted only for the Curator, and only if the run has a `run_source` row with a version for it. Otherwise `no_source`, `source_not_recorded` or `source_not_for_role`;
- every bind is logged (function `bind`).

**The result** is an `Access` around an immutable `AccessContext`:
- `Access()` without the dispatcher's token raises `TypeError`;
- its attributes cannot be set;
- every read uses the captured context once (review: "concurrent mutation of run_id").

The tests build contexts the dispatcher would never produce (unknown roles, stale stages) with `tests/access_testing.py`, which no package code imports.

**One read is one transaction** (`run_transaction`):
1. `SET LOCAL lock_timeout`; check that the run exists; `hc_write_lock(p_run => …)`;
2. the actual stage;
3. the policy checks per field;
4. the reads;
5. one audit row per field;
6. commit; then return, or raise `AccessDenied`.

`role_input` reads **every field of the role in this one transaction**, with every audit row in the same transaction (tested via `xmin`, which shows one transaction; it does not by itself prove payload consistency). Holding the run's lock, the stage cannot change until commit, and neither can run data written by code that follows the same protocol (it waits). **The "one snapshot" claim is scoped to run data protected by the run-lock protocol.** Isolation is READ COMMITTED on purpose. A REPEATABLE READ snapshot would be taken *before* the lock wait, so it could miss a checkpoint committed meanwhile.

**Real concurrent checkpoint transitions** (review): a rules lock and a freeze are each committed by a transaction holding the run's lock, while a read waits on it. After commit, the waiting Planner and Critic are refused with `stage_mismatch`. The Analyst's read after the freeze succeeds; as the re-check notes, that read does not itself wait across the transition.

## Logging: denials and failures

| `detail.result` | When | Code (`detail.code`) |
|---|---|---|
| `allowed` | a delivered read | — |
| `denied` (`AccessDenied`) | a policy refusal | `not_on_list`, `stage_mismatch`, `unknown_role`, `unknown_stage`, `no_source`, `source_not_recorded`, `source_not_for_role`, `setting_not_recorded`, `empty_list` |
| `failed` (`AccessFailed`) | the read could not be done | `unknown_run`, `lock_timeout`, `reader_error` (with the error's class name only), `database_error`, `file_guard` |

- **Only validated, bounded strings are logged.** A role, stage or field that is not one of ours is logged as `invalid`, with its length. Reasons are fixed texts per code, and error messages carry only validated strings.
- **Failure rows are a named exception to the locking protocol** (owner's answer to question 1; register `audit_failure_rows_without_run_lock`). They are written in their own transaction without `hc_write_lock`: there is no run to lock, or the lock is what failed. An `audit_log` insert takes only a key-share lock on the run, which never conflicts with the protocol's lock. For an unknown run, `run_id` is NULL and the requested id is in `detail`. The lock-timeout test checks that the failure row is written *while the other transaction still holds the lock*.
- **File-guard refusals** are written by the child as one bounded line each on standard error. `run_guarded(..., audit=(engine, run_id))` copies them into `audit_log` as failures (at most 100 per run, then a count), or to the process log when no run is given.
- **The original error of a failure** (a reader's exception, the database's error) is written with its traceback to the process log only. `AccessFailed` is raised outside the handler: it has no cause, no context and no text of the original, so a formatter that forwards it (str, repr, formatted traceback) cannot forward the original (re-check; tested with a planted value).
- **A file-guard refusal is still logged when the guarded process then times out:** `run_guarded` reports the refusals from the captured standard error (text or bytes) before re-raising `TimeoutExpired` (re-check; tested).
- **Fallback:** a failure row the database cannot take goes to the process log (logger `hypocurate.access`, one JSON line). Durable database logging is therefore not unconditional.
- **`role_input` is never silently empty.** A role with no field at its stage gets `AccessDenied` (`empty_list`), logged.

## The file guard: a tripwire (review finding 1)

**What it does.** Each pipeline run executes in `python -m hypocurate.access.guarded` (`run_guarded`). There, an audit hook refuses, with `PermissionError`, what trusted code should never do by mistake:
- reading or listing outside the Python installation and the package's code (so the repository root, `tests/`, `docs/`, `data/`);
- writing outside the run's private scratch directory;
- relative paths;
- starting other programs;
- loading new native libraries.

Each refusal is logged (above). Templates, the database driver, the certificate bundle and the scratch directory work under it (tested). Registration refuses to run under it.

**What it does not do.** Python's documentation warns that audit hooks are not suitable for implementing a sandbox (`sys.addaudithook`; PEP 578). Code in the guarded process can get around it in several ways:
- an already-open descriptor can still be read;
- the guard's state can be edited;
- preloaded `ctypes` reads memory directly (tested as a documented limit);
- sockets and the database (with the process's credentials) are open;
- the child inherits its environment, and startup hooks run before the guard;
- checking a path and then opening it is not atomic.

So it catches our accidents, which is what the threat model needs. **The construction-level guarantee is the deployed image without `tests/` and `docs/`.**

Unchanged from the first build:
- the scratch directory: created and removed by the parent; `hc-run-*`, 0700, empty, directly in the system temporary directory;
- `install()` runs only in the guarded process, and only `guarded.py` calls it;
- the database driver is preloaded.

**Backlog:** agents that execute code, with operating-system isolation (a separate user, filesystem and network namespace, or a container) as a precondition.

## Second-model review and fixes (ChatGPT, 2026-10-05)

The owner accepted all six findings and decided the threat model; the fixes were planned, approved (with one question and an addition) and built.

| Finding | Fix | Tests |
|---|---|---|
| 1. The file guard is bypassable | Described everywhere as a tripwire, with Python's warning and the limits (code, README, register `pipeline_file_guard`, this summary). Block list not extended. The image guarantee stated. Refusals logged. | `test_preloaded_ctypes_still_works_a_documented_limit`; `test_no_other_program_and_no_new_native_library` (renamed: it tests new library loads); `test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log` |
| 2. Database access bypasses the contract; caller-chosen, mutable context | Threat model (only trusted code; nothing a model controls receives SQL, a connection or a path). The immutable `AccessContext`, created only by `dispatch.bind` from the run's agent settings and `run_source` rows. No public constructor. | `test_bind_reads_the_role_from_…`, `test_bind_refuses_a_setting_or_source_…`, `test_bind_logs_an_unknown_run_…`, `test_an_access_object_has_no_public_constructor_and_cannot_be_changed` |
| 3. Outcome-bearing text through approved fields | Vocabularies for category values and codes; no title or origin key for the Critic; DOI syntax; the plan projected recursively; no failure text in coverage; codes for eligibility rules. Accepted disclosures listed, and the blinding claim narrowed. **Values planted inside every allowed field.** | `test_access_projected.py` (13); `test_the_plan_is_projected_by_its_named_parts`; `test_record_metadata_…`; `test_flags_kind_has_no_numbers`; `test_the_gap_report_input_has_codes_not_failure_text`; `test_vocabularies_mark_what_they_do_not_know`; `test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure` |
| 4. `sources_meta` provenance | From the code's definitions and the run's sealed version. | `test_sources_meta_comes_from_the_code_and_the_sealed_version_not_the_registry` (name, licence, properties, grouping unit and kind of data edited after dispatch) |
| 5. Denials not always logged | Denied and failed logged apart, with codes; failure rows (named exception); process-log fallback; file-guard refusals; `role_input` never empty; bounded strings. | `test_a_readers_error_is_a_logged_failure`, `test_an_unknown_run_is_a_logged_failure`, `test_when_the_database_is_unavailable_the_process_log_is_the_fallback`, `test_role_input_is_never_silently_empty`, `test_only_validated_bounded_strings_are_logged`; the lock-timeout test now expects a failure row |
| 6. Not the complete model input | Renamed the **projected-data test**; its docstring states what it does not cover. **Step 8 acceptance requirement:** test the actual outbound model request, including instructions, message history, tool errors and retry prompts. | — |
| Checkpoints, snapshot, weak tests | Real concurrent rules-lock and freeze tests; `role_input` in one transaction; the static import scan removed. | `test_a_rules_lock_committed_while_a_read_waits_closes_the_planner`, `test_a_freeze_committed_while_reads_wait_closes_the_critic_and_opens_the_analyst`, `test_a_roles_whole_input_is_read_in_one_transaction` |

**The owner's addition (unrecognized counts).** Per run and per source, how many values of each category field were unrecognized (counts only) appears in "test connection" and in the run's `coverage`, so a source with unfamiliar labels is noticed. The frozen MPEA and Texas A&M sources have none (tested). Adding a value to a vocabulary is a register change needing the owner's approval.

## Re-check (ChatGPT, 2026-10-05) and fixes

The text is in `docs/reviews/step05_recheck_chatgpt.md`. **The threat model was accepted** ("reasonable for sprint 1; it does not require an operating-system sandbox, provided model responses cannot choose the access context or become executable instructions").

| Finding | Re-check status |
|---|---|
| 1. File guard as a tripwire | partly closed (documentation only): the `PRELOADED` comment in `guarded.py` still overclaimed |
| 2. Dispatcher-created context | closed for this layer; step 8 must derive run, setting and source from one invocation assignment |
| 3. Free text and disclosures | closed within the stated policy |
| 4. Source descriptions | closed |
| 5. Denial and failure logging | partly closed: refusals lost on a child timeout; the raised error chained to the original |
| 6. Projected-data test | closed for step 5; the outbound-request test is step 8's |

**The second model found no other blocker under the agreed threat model.** The failure-row exception to the locking protocol was judged sound.

The three items, fixed:
1. **Timeout** (`hypocurate/access/guarded.py`). `run_guarded` catches `TimeoutExpired`, reports the refusals in its captured standard error (bytes or text), and re-raises. Tests: `test_a_refusal_followed_by_a_timeout_is_still_logged` (a real child: a refused read, then a sleep past the timeout) and `test_a_timeout_with_stderr_as_bytes_is_still_reported`.
2. **Sanitized errors** (`layer.py`, `dispatch.py`). The original error and its traceback go to the process log only (`keep_in_process_log`). `AccessFailed` is raised outside the handler, so it has no `__cause__`, no `__context__` and no text of the original. Tests: `test_a_reader_failure_carries_nothing_of_the_original_error` (a planted value in a reader's error; checks str, repr, the formatted traceback, cause, context and args; the original is in the process log) and `test_a_database_failure_carries_nothing_of_the_original_error` (a lock timeout through `get` and through `bind`).
3. **Overclaims.**
   - The `PRELOADED` comment now says the guard refuses the ctypes audit events it intercepts (a new library load, a symbol lookup, a foreign call), and does not stop preloaded ctypes from reading memory directly.
   - A search of the branch for other overclaims found and fixed:
     - "one snapshot", now scoped to run data protected by the run-lock protocol (layer, inputs, package docstring, README, this summary);
     - a garbled sentence in `guard_probe.py` ("it cannot be, by design" → "code that tries can bypass it");
     - "the role's complete input" in `layer.py` → "every field on the role's list".
   - Register `access_logging` states the sanitized errors and names the four new tests; `pipeline_file_guard` names the timeout test.

**Each new test failed on the code before its fix.** All four were run with the fixes absent and only the probe's new `sleep` action present (test scaffolding the timeout test needs); all four failed. The two timeout tests failed because no refusal row was written. The two error tests failed on `__cause__`: the reader's `ValueError` with the planted value, and psycopg's `LockNotAvailable`. With the fixes, all pass.

**By the owner's decision, these fixes were merged on their regression tests without a further review round.**

## Live deployment (2026-10-05)

**Merge:** `step-05-access` into `main` with `--no-ff` (`81ce23c`), after the branch runs were green: last code commit `0034dc7` (https://github.com/kelawady/hypocurate/actions/runs/37330086644) and branch head `0b398cb` (https://github.com/kelawady/hypocurate/actions/runs/37330544938). Checked before merging (`git diff --name-only origin/main...step-05-access`): 31 files, all package code, tests, the image check, the README, CLAUDE.md and review documents; **no `render.yaml`, workflow, migration**, Dockerfile, Compose or dependency change. The suite passed on `main` locally (643), and `main`'s run was green (https://github.com/kelawady/hypocurate/actions/runs/37331298304; started 15:15:11 UTC, passed 15:18:02 UTC). Times are UTC.

| Check | How | Result |
|---|---|---|
| Live `/health` before the merge | `curl` | `version` `2229df3…`, `schema` `0001`, at head |
| Live `/health` after the deploy | `curl`, 15:19:09 UTC | `{"web":"ok","database":"ok","version":"81ce23c8f5a9b6b218861f0ca9ddda57990932db","schema":{"revision":"0001","at_head":true}}` |
| `/assumptions` signed out | `curl` | 303 to `/login` |
| `/assumptions?review=not_reviewed` signed out | `curl` | 303 to `/login` |
| `/` signed out | `curl` | 303 to `/login` |

That the service started on the new commit also shows that the deployed register (86 entries) passed validation at start-up. The signed-in page was not checked: that needs the production password, which only the owner uses. No migration ran (schema still `0001`), and no Blueprint sync was expected, because `render.yaml` did not change. The access layer has no caller on the live site yet (no agent, no worker job, no source registered).

## Requirements carried from earlier steps

| Requirement | How |
|---|---|
| Step 1 open item 4, step 2 deviation 5, step 4 open item 4: approved input files; `tests/` and `docs/reviews/` outside them | Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer (no path-taking function). A tripwire catches accidental file access in the guarded process. The construction-level guarantee is the deployed image without `tests/` and `docs/`. "By construction" in development is withdrawn (threat model). |
| Step 3 open item 3: `hc_write_lock` first, `run_transaction` | Every access transaction and every bind: `SET LOCAL lock_timeout`, run exists, `hc_write_lock(p_run => …)`, all in `run_transaction`. **Exception:** failure rows (named, owner-approved, in the register). |
| Step 3 stated limitation: rejected attempts logged by the access layer | Policy denials committed before the error; failures in their own transaction or the process log. |
| `flag.compared_values` never returned to the Critic | `flags_kind`; projected-data test. |

## Assumptions register

86 entries: 85 in force, 0 open, 1 direction approved; 22 scientific entries not reviewed by an expert.
- **New after the review** (decided by the owner, 2026-10-05):
  - `threat_model`;
  - `access_context_dispatcher`;
  - `access_logging`;
  - `audit_failure_rows_without_run_lock` (the named exception to the locking protocol);
  - `category_vocabularies`;
  - `code_vocabularies`;
  - `accepted_disclosures`.
- **Rewritten**, with the first build's wording kept in each entry's history:
  - `pipeline_file_guard` (a tripwire);
  - `critic_metadata_without_numbers`;
  - `source_meta_fields`;
  - `plan_named_parts` (now "The plan's schema", `PLAN_SCHEMA`; step 6 must follow it).
- **From the first build:**
  - `access_allow_lists`, `outcome_fields_withheld`, `gap_report_condition_summaries`, `access_stage_from_database`, `access_lock_timeout`, `no_experiment_relaxation`;
  - `same_alloy_rule` partly applied;
  - `conflict_pairing_rule` decided.
- The named regression tests follow the renamed test file (`test_access_projected.py`).

## Tests (643, all passing; 99 new in step 5; four register tests changed)

| File | Tests | What |
|---|---|---|
| `tests/test_access_layer.py` | 44 | The allow-list equals the owner's table; the full role × stage × field matrix at eight run states, with denial codes; queued and failed runs give nothing; a denied row survives the caller's rollback; outcome requests by the Planner and the Critic denied and logged; unknown roles, stages and fields are logged as `invalid`; both sides of each checkpoint; completion with and without a freeze; experiment flags relax nothing; field contents (named source fields, registry edits ignored, the Curator's own source and no direction of the claim, record metadata, flags, the projected plan, approved tags, counts with unrecognized counts, condition summaries, same-alloy key); the lock (timeout with a failure row, waiting, `run_transaction`, order of statements); no path-taking function; the guard installed in one place. |
| `tests/test_access_projected.py` | 13 | The **projected-data test**: planted values (in discarded fields and inside every allowed field) are absent from the projected input of the Planner, the Critic, the gap-report Analyst and the Commentator without a freeze, in the encodings listed in its docstring. Positive control. Source free text. Another run's value in no role's input at six stages. **Its docstring states what it does not cover.** |
| `tests/test_access_dispatch.py` | 22 | The dispatcher (role from settings, refusals, unknown run, no public constructor, immutability); logging (reader error, unknown run, database unavailable → process log, `role_input` never empty, bounded strings, file-guard refusals for a run or in the process log); one transaction per input; concurrent rules lock and freeze; vocabularies; the DOI disclosure; no unrecognized value in the frozen sources; unrecognized counts in coverage and test connection; codes, not failure text, in the gap report. Re-check: a refusal followed by a timeout is still logged (real child, and bytes); reader and database failures carry nothing of the original error in str, repr, cause, context or the formatted traceback. |
| `tests/test_access_files.py` | 20 | The tripwire in real guarded processes: reads, listings, relative paths, writes and programs refused; what is needed works; the documented `ctypes` limit; registration refused; a role's input identical inside and outside (through the dispatcher); scratch directories; the guard not installable elsewhere. Its docstring says what it does not show. |

### Tests changed (none weakened)

The owner's pairing-rule decision removed the register's only open entry. The same pattern as step 4b's microstructure decision:
- `test_the_pairing_rule_is_open_and_calibration_awaits_its_technical_review` is renamed `test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review`. It now asserts the decision: no open entry; in force; the owner and the date; not reviewed; not yet, step 6; the exact statement; the weakness and "not reviewed" in the notes; the open state in the history. The calibration assertions are unchanged.
- `test_open_decisions_are_shown_first_when_there_are_any`: with the fixture open entry added, the open section now lists only that entry, and the summary says "1 open decision" (it said 2). The direction-approved assertions are unchanged.
- `test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries`: the counts are now in force = all but 1, open 0, direction approved 1, and the summary says "0 open decisions".
- `test_the_page_shows_every_entry_grouped_with_pending_states_first`: the page leaves out the "Open decisions" heading when nothing is open (step 4b design), so the expected headings are `HEADINGS[1:]`. The section-by-section checks are unchanged.

`same_alloy_rule` is now partly applied:
- `PARTLY` in `tests/test_assumptions.py` gains it, so the partly-applied checks cover one more entry;
- `test_the_owners_eight_decisions_are_recorded_as_decided` now expects "partly" for it, through `PARTLY`, with its step unchanged (6).

**After the review** (none weakened):
- **Removed:** `test_pipeline_code_reaches_data_only_through_the_access_layer` (the static import scan), because the review found it vacuous. Nothing replaces it as a claim; the dispatcher tests cover the binding.
- **Renamed:**
  - `tests/test_access_planted.py` → `tests/test_access_projected.py`, and its leak tests `test_no_planted_value_in_…` → `test_no_projected_planted_value_in_…`;
  - `test_no_other_program_and_no_native_code` → `test_no_other_program_and_no_new_native_library`.
- **Changed by the new design, assertions kept or strengthened:**
  - the matrix and the unknown-input tests now assert the fixed codes and the `invalid` placeholders;
  - stage-mismatch tests match the fixed reason instead of the old message text;
  - the lock-timeout test expects `AccessFailed` and a failure row, where it used to expect no row;
  - the record-metadata, flags, plan, record-counts and `sources_meta` tests expect the new projections (two chosen sources in the world now);
  - the Curator's foreign source is now `controlled_duplicates`, because the world chooses `tamu_fcc`.

### The safeguard tests fail when the safeguard is removed

Each change was made in a scratch copy, and the named test files were run importing the copy (`PYTHONPATH`).

**Review fixes:**

| Removed or changed in the copy | Result |
|---|---|
| Vocabularies pass every value | 8 tests fail, including the projected-data tests of the Critic, the gap report and the Commentator |
| The paper title back in the Critic's view | 2 fail |
| The plan projected one level only | 3 fail |
| `sources_meta` name from the registry | 1 fails (the registry test) |
| `bind` reads the role from any agent setting, not the run's | 1 fails |
| Failure rows not written | 6 fail |
| One transaction per field instead of one per input | 1 fails |
| Coverage keeps the failure text | 4 fail |
| Eligibility rules passed raw | 3 fail |
| Flag kinds passed raw | 4 fail |

**First build** (run on the first build, before the review, and not repeated since): the allow-list check (16 fail), the stage taken from the caller (7), the refusal inside the transaction (11), `hc_write_lock` (3), the projections and run filters (2–5 each), the guard's hook (5), the scratch check (7), the preload (the guarded database and role-input tests).

### Suite results

```
$ pytest -q                                   (Codespace, Python 3.14.2, `docker compose up -d db`)
643 passed in 141.71s
$ docker compose run --rm test                 (the test image, rebuilt)
643 passed in 147.39s
```

GitHub Actions, commit `0034dc7` (the re-check fixes, last code change): success; "Run the suite in the test image": 643 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37330086644
GitHub Actions, commit `2c639be` (the review fixes): success; "Run the suite in the test image": 639 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37327512637
Earlier: first build `72355e6` (615 passed, https://github.com/kelawady/hypocurate/actions/runs/37319439565); the owner's change before the review `81f5003` (620 passed, https://github.com/kelawady/hypocurate/actions/runs/37321733673).

## Audit-log volume (addition D)

Measured on the first build: about **130 bytes of data a row**, about **200 bytes** with the header and two index entries. After the review there is also one `bind` row per agent call.

| Per run | Rows | Size |
|---|---|---|
| Each role reads its complete input once (5 + 3 × 2 + 3 + 11 + 11 field rows, plus about 6 binds) | about 42 | about 8 KB |
| With agent tool calls, refusals and failures (step 8), say | 500 | about 100 KB |

The step 3 estimate of **4–6 MB per run** is unchanged (the audit log adds at most about 2%); to be measured in step 8.

## Deviations from the approved plans

1. **The first build's own deviations stand:**
   - the parent owns the scratch directory;
   - the database driver is preloaded;
   - the scratch directory is validated;
   - `guard_probe.py` is in the package;
   - the first access commit (`432cb35`) does not pass alone.
2. **`string_at`.** The review's example of preloaded `ctypes` working (`string_at`) was refused in our runs, because it raises the call event the hook refuses. The documented-limit test uses direct memory access (`from_address`) instead, which does work.
3. **Isolation stays READ COMMITTED** for the one-transaction input. REPEATABLE READ would take the snapshot before the lock wait (above).
4. **Two chosen sources in the test world.** The world now chooses `tamu_fcc` too (with a placeholder file and a failed search carrying planted failure text), so that coverage text could be planted.
5. **The `git mv` rename of the test file** went into the review commit (staged before it), with its content unchanged; the edits are in the fix commit.
6. **The three re-check fixes are one commit.** They share `tests/test_access_dispatch.py`, and splitting them would have needed interactive staging, which is not available here; the commit message lists all three.

## PRD corrections and clarifications for the next PRD update

1. **PRD 4 (Critic):** "sources" means source descriptions, never source content. The Critic receives no measured number, no paper title and no origin key; categories come from vocabularies.
2. **PRD 3 step 8 and PRD 4 (Analyst):** on a run that ends with no dataset frozen, the Analyst writing the gap report gets everything except outcomes, plus code-computed condition summaries.
3. **PRD 4 (Commentator):** on a run completed with no dataset frozen, the Commentator receives only the gap-report input, the Analyst's gap report and the run's outcome.
4. **PRD 4 (table):** Inclusion and Checks are code; their reads go through access objects from steps 6 and 7.
5. **PRD 4 (relaxation flag):** not in sprint 1; to the backlog (PRD 18).
6. **PRD 4 (threat model, new):** the access contract guards against our own code leaking data to a text-only model. Blinding is limited as in "Accepted disclosures". Timing is not protected.
7. **PRD 4 (implementation):** access objects come only from a dispatcher that binds run, role (from the recorded agent settings), stage and source. Every read is one transaction that takes the run's lock. Denials and failures are logged apart, with the process log as fallback.
8. **PRD 4 (testing requirement):** the data test covers the projected input; the complete model request is tested in step 8.
9. **PRD 5.1 (plan):** the plan's content follows `PLAN_SCHEMA`.
10. **PRD 6 (worker):** each pipeline run executes in a guarded process (a tripwire against accidental file access).
11. **PRD 18 (backlog):** agents that execute code, with operating-system isolation as a precondition.

## Open items

1. **Step 6:**
   - the plan model stores its content in `PLAN_SCHEMA`;
   - flags, eligibility rules and sensitivity keys use the code vocabularies;
   - Inclusion and Checks read through access objects;
   - `same_alloy_rule` and the pairing rule applied.
2. **Step 7:** if the plotting library imports `ctypes`, adding it to `PRELOADED` needs the owner's approval and a second-model review.
3. **Step 8 acceptance requirements:**
   - **test the actual outbound model request**: instructions, message history, tool errors, retry prompts, attachments, **and formatted failures** (re-check);
   - **derive the run, the agent setting and the source of each agent call from one invocation record**, never assembled independently; `bind` checks authorization, not the caller's intention (re-check). **Test binding with two valid runs and two selected sources**, so that a wrong but valid combination would be caught;
   - **keep the "one snapshot" claim scoped** to run data protected by the run-lock protocol;
   - `GuardedRunError` carries the guarded child's error text (`"{type}: {message}"`), which could hold a value a role must not see. Step 8 must not forward it to a model, or must sanitize it as `AccessFailed` now is. Found in the overclaim search; not changed in step 5 (outside the three re-check items);
   - agents receive only text built from `role_input` and reads through an access object from `dispatch.bind`, and no tool that runs SQL, opens files or executes code;
   - the command line's run command calls `run_guarded(..., audit=…)`;
   - the Curator and tabular sources;
   - measure the audit volume.
4. **Step 9:** the worker binds through `dispatch.bind` and runs each run through `run_guarded`. It never calls the access layer while holding a run's lock.
5. **Category values and DOIs** reach the blinded views as the vocabularies and DOI syntax allow. New labels from a new source show as `unrecognized` until the owner adds them.
6. **Backlog:** the relaxation flag; agents that execute code (operating-system isolation first).
7. Carried, unchanged: the step 3 step 7 and step 9 requirements; live registration after the owner's decisions; the step 4b open items.

## Questions for the re-check

1. Is each finding closed within the owner's threat model, and is every claim in this summary, the code and the register now no stronger than the code supports?
2. Do the blinded views copy any stored outcome value into a role's data through a path the projected-data test would not catch?
3. Is the named exception for failure rows sound (no wait, no deadlock), and is anything still unlogged?
4. Is the dispatcher's binding complete for steps 8 and 9 (role from settings, stage from the database, source from `run_source`)?
5. Are the accepted disclosures complete?
