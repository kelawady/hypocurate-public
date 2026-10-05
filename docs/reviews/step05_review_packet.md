# Build step 5 — re-check packet for the second model

Date: 2026-10-05. Branch: `step-05-access`. Code reviewed: commit `2c639be` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success, 639 passed, runtime image OK, https://github.com/kelawady/hypocurate/actions/runs/37327512637.

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

**This packet is for the re-check after your first review** (`docs/reviews/step05_review_chatgpt.md`, section 11). The owner accepted all six findings and made a **threat-model decision** that scopes the fixes: the access layer and its tests guard against *our own code* leaking data to a model; agents are language models that return text only, never execute code and never receive SQL or file tools; only trusted, reviewed code runs; a trusted dispatcher binds each agent call to a run, role, stage and source. "Unreachable by construction" is withdrawn; the file guard is a tripwire, and the deployed image without `tests/` and `docs/` is the only construction-level guarantee. Agents that execute code go to the backlog, with operating-system isolation as a precondition.

The summary's sections "The threat model …", "Second-model review and fixes" and "Accepted disclosures" map each finding to its fix and list the claims withdrawn.

Your review is advice; the test suite is the gate. Please return a dated findings file: for each finding, closed, partly closed or open, and any new finding.

Please check in particular:
- **Within the threat model**, is each finding closed, and is every claim in the summary, the code docstrings, the README, CLAUDE.md and the register no stronger than the code supports?
- **The blinded views** (Planner, Critic, gap report, Commentator without a freeze): vocabularies, the recursive plan projection, provenance of `sources_meta`, codes instead of text. Is any stored outcome value still copied into a role's data? Are the accepted disclosures complete?
- **The dispatcher and the immutable context**: is the binding complete for steps 8 and 9?
- **Logging**: denial vs failure, the named exception (failure rows without the run lock), the process-log fallback, bounded strings. Is anything still unlogged?
- **Snapshot and checkpoints**: one transaction per role input under the run's lock (READ COMMITTED on purpose); the concurrent transition tests.

## Contents

1. Step summary
2. Reviewer checklist
3. CLAUDE.md
4. Core rules: PRD Sections 3, 4, 5.3, 5.4 and 5.6
5. The access layer: new package code (full text)
6. Other code changes (diffs)
7. The assumptions register: diff
8. Tests: new files (full text)
9. Tests: changes to `tests/test_assumptions.py` (diff)
10. README (diff)
11. The first review (`docs/reviews/step05_review_chatgpt.md`)

## Files added, modified or deleted since `main` (`2229df3`, the step 4b live record)

```
M	CLAUDE.md
M	README.md
A	docs/reviews/step05_review_chatgpt.md
A	docs/reviews/step05_review_packet.md
A	docs/reviews/step05_summary.md
M	hypocurate/access/__init__.py
A	hypocurate/access/allowlist.py
A	hypocurate/access/context.py
A	hypocurate/access/dispatch.py
A	hypocurate/access/errors.py
A	hypocurate/access/fields.py
A	hypocurate/access/file_guard.py
A	hypocurate/access/guard_probe.py
A	hypocurate/access/guarded.py
A	hypocurate/access/inputs.py
A	hypocurate/access/layer.py
A	hypocurate/access/stage.py
A	hypocurate/access/vocabulary.py
M	hypocurate/assumptions.json
M	hypocurate/sources/connection.py
M	hypocurate/sources/normalize.py
M	hypocurate/sources/versions.py
M	scripts/check_runtime_image.py
A	tests/access_testing.py
A	tests/access_world.py
A	tests/test_access_dispatch.py
A	tests/test_access_files.py
A	tests/test_access_layer.py
A	tests/test_access_projected.py
M	tests/test_assumptions.py
```
```
2c639be Step 5 review fixes: dispatcher, vocabularies, logging, tripwire
07e7067 Step 5 review: the second model's findings; the owner's threat model in CLAUDE.md
b70558b Step 5 summary and review packet: the owner's change before the review
81f5003 Step 5: the Commentator on a run with no dataset frozen (owner, 2026-10-05)
74054a4 Step 5 summary: the suite through Compose (615 passed)
abd07dc Step 5 summary and review packet
72355e6 README: step 5 status and the access layer
1a5a034 Step 5: the guard's write test uses unique names and always cleans up
0d803e8 Step 5: register entries for the access layer; image check
7d94aaa Step 5: the file guard for pipeline processes
432cb35 Step 5: the access layer (allow-lists, stages, audit log)
77c52bf Register: the owner decides the conflict pairing rule (2026-10-05)
```

## 1. Step summary

### `docs/reviews/step05_summary.md`

````markdown
# Build step 5 — summary for review

Date: 2026-10-05. Branch: `step-05-access`. **Status: first build reviewed by the second model (ChatGPT, 2026-10-05: "serious gaps"; six findings, all accepted by the owner with a threat-model decision); fixes built; awaiting the re-check. Not merged.** PRD Section 15, step 5: "Access layer. Role and stage objects, allowed-field lists, the audit log, and the tests for criterion 14.2 including the planted-value test. This is built before any agent."

The suite is the gate. This summary is for the second model's re-check (PRD 13.2), which uses `docs/reviews/checklist.md`. The review text is in `docs/reviews/step05_review_chatgpt.md`. It describes the state **after** the fixes; section "Second-model review and fixes" maps each finding to its fix.

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
| `hypocurate/access/stage.py`, `inputs.py`, `errors.py` | The stage from the database; `role_input` (one snapshot); `AccessDenied` and `AccessFailed`. |
| `hypocurate/access/file_guard.py`, `guarded.py`, `guard_probe.py` | The tripwire, its guarded process, and probes; refusals reported and logged. |
| `hypocurate/sources/connection.py` | "Test connection" reports unrecognized category counts per field. |
| `hypocurate/sources/normalize.py`, `versions.py` | `same_alloy_key`; registration refuses to run under the guard. |
| `CLAUDE.md` | Rule 14 and the threat model. |
| `README.md`, `scripts/check_runtime_image.py` | The access section, rewritten; the image must contain the access modules. |
| `tests/access_world.py`, `tests/access_testing.py` | Runs at every stage with planted values (now also inside every allowed field) and recorded agent settings; the tests' only way to build an access object outside the dispatcher. |
| `tests/test_access_layer.py`, `test_access_projected.py`, `test_access_dispatch.py`, `test_access_files.py` | 44, 13, 18 and 20 tests. |

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

`role_input` reads **every field of the role in this one transaction**: one snapshot, with every audit row in the same transaction (tested via `xmin`). Holding the run's lock, the stage and the rows cannot change until commit: writers to the run follow the same protocol and wait. Isolation is READ COMMITTED on purpose. A REPEATABLE READ snapshot would be taken *before* the lock wait, so it could miss a checkpoint committed meanwhile.

**Real concurrent checkpoint transitions** (review): a rules lock and a freeze are each committed by a transaction holding the run's lock, while a read waits on it. After commit, the waiting Planner and Critic are refused with `stage_mismatch`, and the Analyst's post-freeze read succeeds.

## Logging: denials and failures

| `detail.result` | When | Code (`detail.code`) |
|---|---|---|
| `allowed` | a delivered read | — |
| `denied` (`AccessDenied`) | a policy refusal | `not_on_list`, `stage_mismatch`, `unknown_role`, `unknown_stage`, `no_source`, `source_not_recorded`, `source_not_for_role`, `setting_not_recorded`, `empty_list` |
| `failed` (`AccessFailed`) | the read could not be done | `unknown_run`, `lock_timeout`, `reader_error` (with the error's class name only), `database_error`, `file_guard` |

- **Only validated, bounded strings are logged.** A role, stage or field that is not one of ours is logged as `invalid`, with its length. Reasons are fixed texts per code, and error messages carry only validated strings.
- **Failure rows are a named exception to the locking protocol** (owner's answer to question 1; register `audit_failure_rows_without_run_lock`). They are written in their own transaction without `hc_write_lock`: there is no run to lock, or the lock is what failed. An `audit_log` insert takes only a key-share lock on the run, which never conflicts with the protocol's lock. For an unknown run, `run_id` is NULL and the requested id is in `detail`. The lock-timeout test checks that the failure row is written *while the other transaction still holds the lock*.
- **File-guard refusals** are written by the child as one bounded line each on standard error. `run_guarded(..., audit=(engine, run_id))` copies them into `audit_log` as failures (at most 100 per run, then a count), or to the process log when no run is given.
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

## Tests (639, all passing; 95 new in step 5; four register tests changed)

| File | Tests | What |
|---|---|---|
| `tests/test_access_layer.py` | 44 | The allow-list equals the owner's table; the full role × stage × field matrix at eight run states, with denial codes; queued and failed runs give nothing; a denied row survives the caller's rollback; outcome requests by the Planner and the Critic denied and logged; unknown roles, stages and fields are logged as `invalid`; both sides of each checkpoint; completion with and without a freeze; experiment flags relax nothing; field contents (named source fields, registry edits ignored, the Curator's own source and no direction of the claim, record metadata, flags, the projected plan, approved tags, counts with unrecognized counts, condition summaries, same-alloy key); the lock (timeout with a failure row, waiting, `run_transaction`, order of statements); no path-taking function; the guard installed in one place. |
| `tests/test_access_projected.py` | 13 | The **projected-data test**: planted values (in discarded fields and inside every allowed field) are absent from the projected input of the Planner, the Critic, the gap-report Analyst and the Commentator without a freeze, in the encodings listed in its docstring. Positive control. Source free text. Another run's value in no role's input at six stages. **Its docstring states what it does not cover.** |
| `tests/test_access_dispatch.py` | 18 | The dispatcher (role from settings, refusals, unknown run, no public constructor, immutability); logging (reader error, unknown run, database unavailable → process log, `role_input` never empty, bounded strings, file-guard refusals for a run or in the process log); one transaction per input; concurrent rules lock and freeze; vocabularies; the DOI disclosure; no unrecognized value in the frozen sources; unrecognized counts in coverage and test connection; codes, not failure text, in the gap report. |
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
639 passed in 125.99s
$ docker compose run --rm test                 (the test image, rebuilt)
639 passed in 131.23s
```

GitHub Actions, commit `2c639be` (the review fixes, last code change): success; "Run the suite in the test image": 639 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
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
   - **test the actual outbound model request**: instructions, message history, tool errors, retry prompts, attachments;
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
````

## 2. Reviewer checklist

### `docs/reviews/checklist.md`

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

## 3. CLAUDE.md

```markdown
# HypoCurate — instructions for Claude Code

Version: 2026-10-04 v1. Owner: Khalid El-Awady.

## What this is

HypoCurate takes a scientific hypothesis in words (first domain: grain-size strengthening in metal alloys), searches registered data sources, and ends in one of three outcomes stated for the sources searched: **sufficient** (a test and a verdict), **partly sufficient** (no verdict on the original question; a narrower question is a separate linked record), or **insufficient** (a gap report, never a forced verdict).

The full specification is `docs/PRD_sprint1.md`. Read the relevant section before you write code. If this file and the PRD disagree, stop and ask.

## How we work

1. **One build step at a time.** The build order is PRD Section 15. Do not start a step until the owner says so. Do not build ahead.
2. **Plan first.** For each step, propose a plan and wait for approval before changing files.
3. **Tests are the gate.** Every step adds tests to the regression suite. A step is finished only when the whole suite passes. Never weaken, skip or delete a test to make it pass; never widen a tolerance. If a test seems wrong, stop and ask.
4. **End of each step:** write a short summary in `docs/reviews/` (what was built, which tests were added, what is open) so a second model (ChatGPT) can review it. Its review is advice; the tests decide.
5. **Any change to a safeguard** (access layer, checkpoints, validity checks, eligibility rules) needs the owner's approval and a second-model review, even if small.
6. **Ask one question at a time**, in plain English, with options and a recommendation.
7. **Deferred ideas go in the backlog** (PRD Section 18). Do not build them.
8. Small commits with clear messages. Never commit to `main` anything that fails the suite.
9. **Any change to `.github/workflows/` needs the owner's explicit review**, even if the workflow tests pass. A workflow test cannot stop its own job from being skipped (for example by a job-level condition), and Render counts a skipped check as passed.
10. **A change to `render.yaml` takes effect at push, before the checks pass**, and redeploys the code already running (Render's Blueprint sync; seen on the step 3 merge, 2026-10-05). So any setting that depends on new code goes in a later merge than that code, and every `render.yaml` change needs the owner's explicit review, like workflow changes.

11. **Assumptions register.** Any new assumption or changed default is entered in `hypocurate/assumptions.json` in the same merge, with its reason, who decided it and when, and its earlier value in the history. The page /assumptions is generated from that file only.
12. **One named place per default.** Code reads a default from one named setting (a module constant, a source definition, a plan default or a database constraint), never from a literal scattered through the code. A register entry applied in code ("yes" or "partly") names that setting; `tests/test_assumptions.py` fails if it does not exist or holds a different value. That is a reference and value check only: it does not show that the entry's wording matches what the code does. Behaviour is covered by the regression tests the entry names, and the register test checks only that they exist.

## Rules the code must never break

1. **Code decides; agents advise.** Inclusion of records, flags, the choice of test, data sufficiency and the verdict are computed by code. No language model output may set them.
2. **Access contract (PRD Section 4).** Every agent reads data only through the access layer, which holds an allow-list of fields per role and stage. Anything else raises `AccessDenied` and is written to the audit log. Tests check a role's *complete* input, including a planted-value test.
   - Planner: fills template parameters; sees counts only, never outcome values.
   - Curator: extraction only; is not told the direction of the claim; has no say over inclusion.
   - Critic: classifies flags from sources and metadata; is told the kind of flag, not the numbers; never sees outcomes.
   - Analyst: explains results that code has already computed.
   - Commentator: outside the decision path; a different model; optional. Its numbers are checked against the run record; label: "numbers checked against the run record".
3. **Two checkpoints (PRD 5.6).** *Rules lock* before curation: the model, scope, exclusion rules and data-sufficiency option are fixed. *Dataset freeze* before analysis: the record set is fixed and fingerprinted. Nothing changes after its checkpoint, by agent or by person. Later removals are sensitivity analyses only and never change the verdict.
4. **Stored is not analysed (PRD 5.3).** Every record found is kept. Eligibility for the test is a separate decision by code under the locked rules. Conflicting records are preserved, not automatically pooled.
5. **Two validity checks that can never be waived (PRD 5.7).** (1) Can a coefficient be fitted? (2) Is inference valid (at least 1 residual degree of freedom and at least 2 independent groups)? If 1 passes and 2 fails: report the coefficient only, with no uncertainty, no p-value and no verdict.
6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction; one-sided test of k > 0 at 0.05 against a t distribution with (groups − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
7. **Data sufficiency is a query parameter fixed at rules lock (PRD 5.8).** Default: fixed minimum (30 records, 5 alloys with at least 2 grain sizes, 10 independent papers, 10 residual degrees of freedom). "Use what is available" waives the threshold only, never the validity checks, and labels the result exploratory.
8. **A narrower question is a separate record**, linked to the original. The original gets no verdict.
9. **Three kinds of "nothing found" stay distinct:** a reported negative result, missing evidence, and a failed search.
10. **Model-recalled data are never pooled** and never count toward a verdict.
11. **Per-run calibration (PRD 5.10) is a flag, not a gate.** When inference cannot run, show "calibration unavailable" with the reason. Software correctness (pass/fail against an independent reference) is separate from calibration (a reported finding).
12. **Every model call is recorded** with tokens and actual cost (`model_call`). Spending caps: $2 per run, $50 per month.
13. **Wording:** outcomes are always stated "in the sources searched". Never write that data "do not exist".
14. **Nothing a model controls ever receives SQL, a database connection or a file path.** Agents get data only as text built from an access object that the trusted dispatcher (`hypocurate.access.dispatch.bind`) bound to a run, role, stage and source. No code gives an agent a tool that runs SQL, opens files or executes code.

## Threat model (owner, 2026-10-05)

The access layer and its tests guard against **our own code** leaking data to a model. In sprint 1 agents are language models that return text only: they never execute code and never receive SQL or file tools. Only trusted, reviewed code runs, and a trusted dispatcher binds each agent call to a run, role, stage and source. The access layer is not a boundary against hostile code running in the same process, and the file guard is a tripwire against accidental file access, not a sandbox. The only construction-level guarantee about answer material is that the deployed image contains no `tests/` or `docs/`. Agents that execute code are in the backlog, with operating-system isolation as a precondition. Do not claim more than this anywhere.

## Environment

- Development happens in a GitHub Codespace. Nothing lives on the owner's laptop. The site runs on Render: pushing to `main` on GitHub deploys it.
- Stack: Python, FastAPI + Jinja + HTMX, one background worker (same code as the command line), PostgreSQL + Alembic, DSPy + litellm, statsmodels/scipy, Docker from day one (`Dockerfile`, `docker-compose.yml`, `render.yaml`).
- Repository layout: PRD Section 6.1.
- **Secrets** (API keys, database URL, login password) live in `.env` locally and in Render environment variables. Never commit them, print them, or put them in tests. Keep `.env.example` with names only.
- Do not create Render services or anything else that costs money without asking first.

## Reference material in `docs/`

- `PRD_sprint1.md` — the specification (PDF copy alongside).
- `HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf` — background and research questions.
- `glossary.json` — the 41 explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
- `mockup_screens/` — the nine target screens.
- `reference/worked_example.py`, `reference/calibration_example.py` — the scripts that produced the reference numbers. They contain file paths from another machine; treat them as a statement of method, not as code to import.

## Reference numbers (fixed-plan test, PRD 14.1a)

Pooled: 98 records, 22 alloys, 21 groups, 75 residual degrees of freedom, k = 428 ± 64, p ≈ 8e-7. First source alone (MPEA): 77 records, 20 papers, k = 427 ± 61, p ≈ 6e-7. Second source alone (Texas A&M): coefficient ≈ 1173, one group, no uncertainty, no verdict.
```

## 4. Core rules (from `docs/PRD_sprint1.md`)

```markdown
# 3. How a query flows

1.  **Draft and submit.** A person writes a hypothesis in words, picks its domain, chooses data sources and chooses how much data is enough (Section 5.8). Editing a hypothesis creates a new version; it never changes a run that has been made.

2.  **Review and dispatch.** A person reviews the submitted query, confirms or changes its domain, and dispatches it or returns it for edits. Dispatch creates a run and puts it in the queue.

3.  **Planner (agent).** Fills in the parameters of the supported model: variables, scope, exclusion rules from the allowed menu, and the tags. It sees record counts only.

4.  **Checkpoint 1: rules lock.** The plan and its rules are fixed and fingerprinted, before any curation.

5.  **Curator (agent) and inclusion (code).** The Curator maps each source to the fixed list of fields and extracts every matching record. Code then applies the locked rules to decide which records are eligible.

6.  **Checks (code) and Critic (agent).** Code compares values and raises flags. The Critic classifies each flag from sources and metadata; it is told the kind of flag, not the numbers.

7.  **Checkpoint 2: dataset freeze.** The analysis dataset is fixed and fingerprinted, before any analysis. Code decides from the predictor values whether the data are sufficient.

8.  **Statistics (code) and Analyst (agent).** Code runs the locked test on the pooled data and on each source, runs the sensitivity analyses, and determines the verdict. The Analyst explains the result and writes the report or the gap report.

9.  **Commentator (agent).** After the verdict is final, a separate model reads the query and the complete output and writes a commentary on the result and the limits of its statistical significance. It cannot change anything.

10. **Result.** The run viewer shows the outcome, the two checkpoints, the record of statistical significance, the plot, the per-source table, the commentary, each stage's input and output, and the records used and excluded. The data can be downloaded as a spreadsheet.

## 3.1 The three outcomes

| **Outcome** | **What the system returns** |
|---|---|
| Sufficient | A verdict from the pooled test, per-source results, sensitivity analyses and a curated dataset. |
| Partly sufficient | No verdict on the original question. A narrower question is stored as a separate, labelled record linked to the original, with its own locked plan and verdict. A gap report says what is missing for the original. |
| Insufficient in the sources searched | No verdict. A gap report listing missing fields, the shortfall against the required sample size, the sources searched and not searched, and the kind of "nothing found". |

Every result lists the sources searched and the sources not searched. A field missing from one dataset shows a gap in that dataset, not that the measurement was never made.

The three kinds of "nothing found" are: a **reported negative result** (the measurement was made and showed no effect), **missing evidence** (no one has reported the measurement in the sources searched), and a **failed search** (the system could not reach or read a source).
```

```markdown
# 4. Access contract

What each role can see is fixed in code, by role and by stage. There is no general unlock at either checkpoint. Roles that can add or remove records never see outcome values. Every read goes through the data-access layer and is written to an audit log.

| **Role** | **Can see** | **Cannot do or see** |
|---|---|---|
| Planner (agent) | The claim in words; record counts by field | Outcome values, at any stage |
| Curator, extraction (agent) | The source it is reading; the list of fields to extract | The direction of the claim; any say over which records are included |
| Inclusion (code) | The locked rules; record fields | Discretion: rules are applied exactly as written |
| Checks (code) | All values | Judgment: it only raises flags |
| Critic (agent) | Sources, metadata, and the kind of each flag raised by code | Outcome values, including the numbers behind a flag; choosing between conflicting values |
| Analyst (agent) | Results and outcome values, after the dataset freeze | Changing the plan, the records, or the verdict that code computed |
| Commentator (agent) | The query and the complete output, after the verdict is final | Changing anything; using numbers that are not in the run record |

**Allowed fields, not blocked fields.** Each role has a written list of the fields it may receive, kept in code next to the access layer. Anything not on the list is withheld. Removing the outcome column alone is not enough: outcome values can also leak through the numbers stored with a flag, through values as originally reported, through nested fields, and through explanatory text passed between stages.

**Implementation requirement.** Each agent role receives a data-access object built for that role and stage. A call that the role is not allowed to make raises an AccessDenied error and writes a row to the audit log. A flag passed to the Critic carries its kind, the record identifiers, the metadata and a category (for example "differ beyond tolerance" or "identical values"), never the numbers compared. The contract can be relaxed only by an explicit experiment flag on the run, which is recorded and shown in the run viewer.

**Testing requirement.** Access is tested on everything a role receives: the prompt text, every tool response and any text handed over from an earlier stage. The test data contain distinctive planted outcome values, and the tests fail if any of them appears anywhere in the input of the Planner or the Critic.
```

```markdown
## 5.3 Conflicting, duplicate and invalid records: stored is not the same as analysed

All observations are kept in the evidence store with their sources. Nothing is deleted or overwritten, and the Critic never chooses a preferred value. Keeping a record does not mean it is pooled into the analysis. Whether a flagged record enters the analysis is decided by eligibility rules that are part of the locked plan and applied by code. The defaults below apply unless the Planner sets a different rule before the lock; the rule used is stored with the run.

| **Class of flagged record** | **Kept in the store** | **Enters the primary analysis (default rule)** | **Sensitivity analysis** |
|---|---|---|---|
| Exact duplicate: the same measurement reported by two sources | Yes, both | Counted once. Code keeps the record from the original paper, or the first source in a fixed order if the origin is unknown. | None |
| Possible duplicate that cannot be resolved | Yes, both | Counted once, by the same fixed rule, so that one measurement is not counted twice. | Both counted separately |
| Comparable specimens and conditions; the values truly differ | Yes, both | Both enter, with records grouped by paper in the model. | None |
| Incompatible measurements: outside the plan's scope (test type, temperature, condition) | Yes | No. Listed as out of scope. | None |
| Difference explained by missing metadata: scope cannot be confirmed | Yes | No. Listed as "scope not confirmed". | Included |
| Invalid value: physically impossible (for example tensile strength below yield strength, or a negative grain size) | Yes, flagged | No. | None |
| Model-recalled value (from a language model's memory) | Kept apart, never in the evidence base | Never. | Shown beside the sources for comparison only |

**When two records are the same measurement.** Two records count as duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions. Matching alloy and grain size alone is not enough.

Physical checks must not involve the relationship under test. Agreement with the expected grain-size relationship can never be used to decide which records are credible.

## 5.4 A narrower question is a different question

When only part of a claim can be tested, the Planner may propose a narrower question (for example, one alloy class instead of all). The narrowing is decided on record counts, never on outcomes. The original question keeps the status "partly sufficient" and receives no verdict. The narrower question is stored as its own record, linked to the original, with its own locked plan and verdict, and is labelled as narrower wherever it appears.
```

```markdown
## 5.6 Two checkpoints: the rules lock and the dataset freeze

| **Checkpoint** | **When** | **What it fixes** |
|---|---|---|
| Rules lock | After the Planner, before curation | The plan: model parameters, scope, exclusion rules, eligibility rules, data-sufficiency option, sensitivity analyses. Stored with a fingerprint and a time. |
| Dataset freeze | After inclusion, checks and the Critic, before analysis | The analysis dataset: exactly which records enter the primary analysis and each sensitivity analysis. Stored with a fingerprint and a time. |

- Between the two checkpoints the set of records changes only by applying the locked rules. No agent and no person can add or remove a record by choice.

- After the dataset freeze nothing changes. Outcome values become visible to the statistics code and the Analyst only after it.

- A removal proposed after the rules lock, by an agent or a person, is recorded and appears only in a labelled sensitivity analysis.

- If no records are eligible, no dataset is frozen and no test is run; the run ends as insufficient.
```


## 5. The access layer: new package code (full text)

### `hypocurate/access/__init__.py`

```python
"""The data-access layer: role and stage objects, the audit log, AccessDenied (step 5).

- `allowlist`: the allowed fields per role and stage (the access contract, PRD 4), the
  threat model, the plan schema and the accepted disclosures;
- `vocabulary`: the controlled vocabularies of the blinded views;
- `dispatch.bind`: the only way to obtain an access object, for one agent call;
- `layer.Access`: the access object every agent read goes through; logs every read,
  denial and failure;
- `inputs.role_input`: a role's complete input at its stage, in one snapshot;
- `file_guard` and `guarded`: a tripwire against accidental file access by pipeline code
  (not a sandbox).
"""
from hypocurate.access.dispatch import bind
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.inputs import role_input
from hypocurate.access.layer import Access

__all__ = ["Access", "AccessDenied", "AccessFailed", "bind", "role_input"]
```

### `hypocurate/access/allowlist.py`

```python
"""The allowed fields per role and stage (PRD 4). The one named place for the access contract.

**Threat model** (owner, 2026-10-05; register entry 'threat_model'). The access layer and
its tests guard against *our own code* leaking data to a model. In sprint 1 agents are
language models that return text only: they never execute code and never receive SQL, a
database connection, a file path or any tool other than reads through an access object.
Only trusted, reviewed code runs, and a trusted dispatcher (`dispatch.bind`) binds each
agent call to a run, role, stage and source. The access layer is **not** a boundary
against hostile code running in the same process: such code could use the database
credentials directly. Agents that execute code are in the backlog, with operating-system
isolation as a precondition.

Allowed fields, not blocked fields: a role receives exactly the fields listed for it at
the run's stage, and nothing else. Each field is built from named keys only
(`hypocurate.access.fields`), never by copying a row and removing what is forbidden. Text
in the blinded views (the Planner, the Critic, the gap report and the Commentator without
a freeze) comes from fixed vocabularies (`vocabulary.py`) or is replaced by a marker; the
plan is projected recursively by `PLAN_SCHEMA`. What these views still disclose by design
is listed in `ACCEPTED_DISCLOSURES`; timing is not protected.

**Single-run scope** (owner, 2026-10-05). Every field reads only the rows of the access
object's own run, and the sealed source versions that run recorded at dispatch. No field
returns anything from another run: not from the run a narrower question came from (its
results, coefficient, stage outputs or commentary), and not from earlier runs of the same
hypothesis. Two fields are reference lists, not run data: `domain` (the run's confirmed
domain) and `tag_values` (the approved values of the fixed tag lists, without the run that
proposed them).

Stages are read from the database on every call (`hypocurate.access.stage`). A role that is
not listed for a stage receives nothing at that stage; a queued or failed run gives
nothing to anyone. There is no general unlock at a checkpoint, and no experiment flag
relaxes this contract (sprint 1; PRD 4's relaxation flag is in the backlog).
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from hypocurate.access.vocabulary import (CATEGORY_FIELDS, ELIGIBILITY_RULES, FLAG_KINDS, PHASE_CLASSES,
                                          PROCESSING_METHODS, SENSITIVITY_KEYS, TEMPERATURE_BANDS, TEST_TYPES)

ROLES = ("planner", "curator", "critic", "analyst", "commentator")

# none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
# frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
# closed_without_freeze: curation ended with no dataset frozen (insufficient), running.
# final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")

FIELDS = MappingProxyType({
    "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
    "domain": "The run's confirmed domain: key, name and profile.",
    "sources_meta": "The run's chosen sources, as fixed named plain fields (SOURCE_META_FIELDS): name, licence "
                    "and fields available from the code's source definitions; type, kind of data and grouping "
                    "unit from the sealed version the run recorded.",
    "tag_values": "The approved values of the fixed tag lists: kind and value.",
    "record_counts": "Per chosen source, computed by code from its sealed version: the number of records, "
                     "per field the count of each status, and per value of each non-outcome category field "
                     "the count of records.",
    "plan_fields_to_extract": "From the locked plan, the list of fields to extract, and nothing else.",
    "source_content": "The sealed files of the one source the Curator reads, as recorded for the run.",
    "record_metadata": "Per stored record: id, source, item index, kind, alloy label and composition, DOI "
                       "(DOI syntax only), each field's status, and the non-outcome category values from "
                       "their vocabularies. No measured number of any field, no paper title, no origin key.",
    "flags_kind": "Per flag: id, kind and category (from their vocabularies) and record ids. Never the numbers "
                  "compared.",
    "plan": "The locked plan, projected recursively by PLAN_SCHEMA; its fingerprint, lock time, "
            "data-sufficiency option and minimums, sensitivity analyses (vocabulary) and power assumptions "
            "(POWER_SCHEMA).",
    "records_full": "Per stored record: every stored field, including outcome values and values as reported.",
    "decisions": "Eligibility decisions (record, eligible, rule code) and the named analysis sets (keys from "
                 "the vocabulary).",
    "flags_full": "Per flag: kind, category, record ids, the numbers compared, the Critic's class and reason.",
    "results": "The run's status, outcome, verdict and exploratory label; the dataset freeze; analysis "
               "results; calibration results.",
    "coverage": "Per source: search status, kind of nothing found, and how many category values of each field "
                "were unrecognized in the run's records (counts only); the run's search coverage lists. "
                "No failure text.",
    "stage_outputs": "Every stage of the run: input, output, reasoning, tool calls and model.",
    "run_cost": "Tokens and cost of the run, in total and per stage.",
    "stored_record_counts": "Per source, computed by code from the run's stored records: the number of "
                            "records, per field the count of each status, and per value of each non-outcome "
                            "category field the count of records.",
    "condition_summaries": "Computed by code from the run's stored records, per alloy and overall: the "
                           "number of records; count, minimum and maximum of grain size and of test "
                           "temperature; counts by test type and by phase. Never a row-level value, an "
                           "outcome value or a statistic derived from outcomes.",
    "gap_report": "The Analyst's gap report: the output of each Analyst stage of the run.",
    "outcome": "The run's status, outcome, verdict and exploratory label.",
})

_ANALYSIS = frozenset({"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full",
                       "results", "coverage", "stage_outputs", "run_cost"})
_GAP_REPORT = frozenset({"claim", "domain", "sources_meta", "plan", "coverage", "stored_record_counts",
                         "decisions", "flags_kind", "condition_summaries"})

ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
    "planner": MappingProxyType({
        "before_lock": frozenset({"claim", "domain", "sources_meta", "tag_values", "record_counts"}),
    }),
    "curator": MappingProxyType({
        "curation": frozenset({"plan_fields_to_extract", "sources_meta", "source_content"}),
    }),
    "critic": MappingProxyType({
        "curation": frozenset({"sources_meta", "record_metadata", "flags_kind"}),
    }),
    "analyst": MappingProxyType({
        "analysis": _ANALYSIS,
        # Owner, 2026-10-05: the gap report gets everything except outcomes, plus condition summaries.
        "closed_without_freeze": _GAP_REPORT,
    }),
    "commentator": MappingProxyType({
        "final": _ANALYSIS,
        # Owner, 2026-10-05: with no dataset frozen, only what the Analyst received for the gap
        # report, plus the Analyst's gap report and the run's outcome. No outcome values, no
        # row-level records.
        "final_without_freeze": _GAP_REPORT | {"gap_report", "outcome"},
    }),
})


def allowed(role: str, stage: str) -> frozenset[str]:
    """The fields `role` may receive at `stage`; empty for any role or stage not listed."""
    return ALLOWED.get(role, {}).get(stage, frozenset())


# The fields that can be the outcome of a plan. The Planner does not know which one its
# plan will choose before the lock, so every one of them is treated as an outcome
# everywhere outcomes are withheld: their values never reach the Planner, the Critic or
# the gap report, and no count is ever broken down by their values.
OUTCOME_FIELDS = frozenset({"yield_strength", "yield_strength_sd", "ultimate_tensile_strength",
                            "hardness", "hardness_sd"})

# CATEGORY_FIELDS (from `vocabulary`): fields whose values are categories, shown to the Critic
# and counted for the Planner and the gap report, always through their vocabularies.

# The non-outcome measured conditions summarized for the gap report (owner, 2026-10-05).
CONDITION_RANGE_FIELDS = ("grain_size", "test_temperature")
CONDITION_COUNT_FIELDS = ("test_type", "phase_class")

# sources_meta: a fixed set of named plain fields (owner, 2026-10-05). Name, licence and
# fields available come from the code's definitions (`SOURCES`); interpretation settings
# from the run's sealed version. The source registry's text (address, labels, edits after
# dispatch) never reaches a role through this field.
SOURCE_META_FIELDS = ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                      "fields_available")

# The plan, projected recursively (owner, 2026-10-05: defined in step 5; step 6's plan model
# must follow it). A schema is a dict of named keys; a leaf is "number", "integer",
# "field" (a common field name), "unit", or a vocabulary (a frozenset); ("list", schema) is
# a list. Unknown keys are dropped; a leaf that does not fit becomes the marker (vocabulary,
# field, unit) or is dropped (number, integer). There is no free-text leaf. PRD 5.1's
# "claim in words" is not part of the projection: roles that may see it get the `claim`
# field.
ALLOY_CLASSES = frozenset({"multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy",
                           "titanium alloy", "nickel alloy", "copper alloy", "magnesium alloy", "other"})
EXCLUSION_RULES = frozenset({"grain_size_range", "temperature_range", "phase", "test_type"})
MODELS = frozenset({"hall_petch_alloy_intercepts"})
TRANSFORMATIONS = frozenset({"inverse_square_root"})
HYPOTHESES_NULL = frozenset({"k <= 0"})
HYPOTHESES_ALTERNATIVE = frozenset({"k > 0"})
VERDICT_STATEMENTS = frozenset({"pooled_test_gives_verdict"})
SUFFICIENCY_OPTIONS = frozenset({"fixed_minimum", "use_available"})
POWER_METHODS = frozenset({"information_only"})
CATEGORY_VALUES = TEST_TYPES | TEMPERATURE_BANDS | PHASE_CLASSES | PROCESSING_METHODS

PLAN_SCHEMA = MappingProxyType({
    "hypothesis_version": "integer",
    "variables": {"outcome": {"field": "field", "unit": "unit"},
                  "predictor": {"field": "field", "unit": "unit", "transformation": TRANSFORMATIONS}},
    "scope": {"alloy_class": ("list", ALLOY_CLASSES), "temperature_band": ("list", TEMPERATURE_BANDS),
              "test_type": ("list", TEST_TYPES), "phase_class": ("list", PHASE_CLASSES)},
    "model": {"name": MODELS, "null": HYPOTHESES_NULL, "alternative": HYPOTHESES_ALTERNATIVE, "alpha": "number"},
    "sufficiency": {"option": SUFFICIENCY_OPTIONS, "min_records": "integer", "min_alloys": "integer",
                    "min_groups": "integer", "min_resid_df": "integer"},
    "fields_to_extract": ("list", "field"),
    "exclusion_rules": ("list", {"rule": EXCLUSION_RULES, "min": "number", "max": "number",
                                 "values": ("list", CATEGORY_VALUES)}),
    "eligibility_rules": ("list", {"flag_kind": FLAG_KINDS, "rule": ELIGIBILITY_RULES}),
    "verdict_statement": VERDICT_STATEMENTS,
    "sensitivity_analyses": ("list", SENSITIVITY_KEYS),
})
POWER_SCHEMA = MappingProxyType({"method": POWER_METHODS, "within_paper_similarity": "number",
                                 "smallest_effect": "number", "scatter": "number"})

# What the blinded views still disclose, by design (owner, 2026-10-05; register entry
# 'accepted_disclosures'). The blinding claim is limited to: no outcome value is copied
# into these views from a stored outcome field, a value as reported, a flag's numbers, a
# stage's text, or text outside a vocabulary.
ACCEPTED_DISCLOSURES = (
    "counts by field status (for example how many yield strengths a source reports or cannot read)",
    "flag kinds and categories (for example that two values differ beyond the tolerance)",
    "condition summaries, which reveal an exact grain size or temperature when a group has one record",
    "compositions and alloy labels derived from them",
    "DOIs with DOI syntax, which may contain digits",
    "text written or approved by people: the claim, the approved tag values, source names and licences in code",
    "numbers in the locked plan (thresholds, minimums), written before any record exists",
    "the Analyst's gap report, passed to the Commentator on a run with no dataset frozen",
    "timing of calls and the existence of refusals",
)
```

### `hypocurate/access/vocabulary.py`

```python
"""Controlled vocabularies of the access layer (step 5 review, finding 3; owner, 2026-10-05).

Text that reaches a role through a blinded view (the Planner, the Critic, the gap report)
comes from a fixed vocabulary, or is replaced by the marker `UNRECOGNIZED`. The stored
value is never changed. Unrecognized values are counted per field (never shown), so that
a source with unfamiliar labels is noticed (owner's addition, 2026-10-05).

Adding a value to a vocabulary is a register change that needs the owner's approval
(entries 'category_vocabularies' and 'code_vocabularies').

This module imports nothing from the database or the sources, so any module may use it.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable, Mapping

UNRECOGNIZED = "unrecognized"

# The record fields whose values are categories.
CATEGORY_FIELDS = ("test_type", "test_temperature_band", "phase_class", "microstructure", "processing_method")

# --- Category values of records (built from the frozen sources' actual values) ----------

TEST_TYPES = frozenset({"tension", "compression"})
TEMPERATURE_BANDS = frozenset({"room temperature", "cryogenic", "elevated"})
PHASE_CLASSES = frozenset({"FCC", "BCC", "other"})
# A microstructure is one or more of these tokens joined by "+" (covers all 40 MPEA values).
MICROSTRUCTURE_TOKENS = frozenset({"FCC", "BCC", "B2", "HCP", "L12", "Laves", "Sec.", "Other"})
PROCESSING_METHODS = frozenset({"CAST", "WROUGHT", "ANNEAL", "POWDER", "OTHER"})

CATEGORY_VOCABULARIES: Mapping[str, frozenset[str]] = {
    "test_type": TEST_TYPES, "test_temperature_band": TEMPERATURE_BANDS, "phase_class": PHASE_CLASSES,
    "processing_method": PROCESSING_METHODS,
}


def category(field: str, value: Any) -> str:
    """A category value as a blinded view shows it: itself if it is in the field's
    vocabulary, otherwise `UNRECOGNIZED`."""
    if not isinstance(value, str):
        return UNRECOGNIZED
    if field == "microstructure":
        tokens = value.split("+")
        return value if tokens and all(t in MICROSTRUCTURE_TOKENS for t in tokens) else UNRECOGNIZED
    return value if value in CATEGORY_VOCABULARIES.get(field, frozenset()) else UNRECOGNIZED


def unrecognized_counts(values: Iterable[tuple[str, Any]]) -> dict[str, int]:
    """How many values of each field are unrecognized: counts only, never the values."""
    counts = Counter(f for f, v in values if category(f, v) == UNRECOGNIZED)
    return dict(sorted(counts.items()))


# --- Codes written by our own code (steps 6 and 7 must use these) ------------------------

FLAG_KINDS = frozenset({"exact_duplicate", "possible_duplicate", "values_disagree", "out_of_scope",
                        "scope_not_confirmed", "invalid_value", "model_recalled"})
FLAG_CATEGORIES = frozenset({"identical values", "differ beyond tolerance", "within tolerance",
                             "outside scope", "scope not confirmed", "physically impossible"})
ELIGIBILITY_RULES = frozenset({"in_scope", "out_of_scope", "scope_not_confirmed", "invalid_value",
                               "duplicate_counted_once", "model_recalled", "single_grain_size",
                               "excluded_by_rule"})
SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                              "source_only_assignments", "possible_duplicates_separate",
                              "scope_not_confirmed_included", "removal_after_lock"})
ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS


def code(value: Any, vocabulary: frozenset[str]) -> str:
    return value if isinstance(value, str) and value in vocabulary else UNRECOGNIZED


DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]{1,200}")


def doi(value: Any) -> str | None:
    """A DOI if it has DOI syntax (surrounding spaces ignored), None if absent, else the marker.
    A DOI may contain digits: an accepted disclosure (register 'accepted_disclosures')."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value.strip() if isinstance(value, str) and DOI.fullmatch(value.strip()) else UNRECOGNIZED
```

### `hypocurate/access/context.py`

```python
"""The access context: what one agent call may read, captured once (step 5 review, finding 2).

Immutable. Created only by the trusted dispatcher (`dispatch.bind`), which reads the role from
the run's recorded agent settings, the stage from the database, and checks a Curator's source
against the run's `run_source` rows. Every read of an access object uses this one context.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessContext:
    run_id: int
    role: str
    stage: str
    source_key: str | None = None
    agent_setting_id: int | None = None
```

### `hypocurate/access/dispatch.py`

```python
"""The trusted dispatcher: the only way to obtain an access object (step 5 review, finding 2).

`bind(engine, run_id, agent_setting_id, source_key=None)` is called by trusted orchestration
code (steps 8 and 9) for one agent call. It never takes a role, a stage or a run chosen by
anything a model controls:
- the **role** is read from the run's recorded agent settings (`run_agent_setting`): the
  setting being invoked must be recorded for this run, and its role is the one recorded;
- the **stage** is read from the database;
- a **source** is bound only for the Curator, and must be one of the run's `run_source` rows
  with a recorded version.
The result is an `Access` around an immutable `AccessContext`. The binding itself is
logged (function "bind"): allowed, denied with its code, or failed. Every later read checks
again that the run is still at the bound stage.

Nothing a model controls ever receives SQL, a database connection or a file path (CLAUDE.md):
agents get text built from `role_input` and from reads through this object only.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError

from hypocurate.access.context import AccessContext
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.layer import (_AUDIT, _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, DENIALS, Access, _detail, _row,
                                     bounded_source, log_failure)
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction, sqlstate

UNBOUND = "invalid"  # the role logged for a binding refused before a role is known


def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | None = None,
         lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
    """An access object for one agent call, or AccessDenied / AccessFailed (logged)."""
    if not isinstance(run_id, int) or isinstance(run_id, bool) or not isinstance(agent_setting_id, int):
        raise TypeError("bind takes an integer run id and an integer agent setting id")
    probe = AccessContext(run_id, UNBOUND, UNBOUND, source_key, agent_setting_id)

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=run_id)).scalar_one():
            return ("unknown_run", None)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        stage = actual_stage(conn, run_id, status)
        role = conn.execute(text("SELECT role FROM run_agent_setting WHERE run_id = :r AND agent_setting_id = :a"),
                            dict(r=run_id, a=agent_setting_id)).scalar_one_or_none()
        ctx = AccessContext(run_id, role or UNBOUND, stage, source_key, agent_setting_id)
        code = None
        if role is None:
            code = "setting_not_recorded"
        elif role != "curator" and source_key is not None:
            code = "source_not_for_role"
        elif role == "curator" and source_key is None:
            code = "no_source"
        elif role == "curator" and not conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM run_source rs JOIN source s ON s.id = rs.source_id "
                "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL)"),
                dict(r=run_id, k=source_key)).scalar_one():
            code = "source_not_recorded"
        extra = {"agent_setting": agent_setting_id}
        result = "denied" if code else "allowed"
        conn.execute(_AUDIT, _row(ctx, run_id, "bind", code is None, _detail(ctx, result, code, stage, **extra)))
        return (result, code, ctx)

    try:
        outcome = run_transaction(engine, transaction)
    except DBAPIError as error:
        code = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
        log_failure(engine, probe, "bind", code, agent_setting=agent_setting_id)
        raise AccessFailed(UNBOUND, UNBOUND, "bind", code) from error
    if outcome[0] == "unknown_run":
        log_failure(engine, probe, "bind", "unknown_run", run_known=False, agent_setting=agent_setting_id)
        raise AccessFailed(UNBOUND, UNBOUND, "bind", "unknown_run")
    result, code, ctx = outcome
    if result == "denied":
        raise AccessDenied(ctx.role, ctx.stage, "bind", code, DENIALS[code])
    return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)


__all__ = ["bind", "bounded_source"]
```

### `hypocurate/access/errors.py`

```python
"""The errors of the access layer (PRD 4).

`AccessDenied`: a policy refusal (the field is not on the role's list at the run's stage, the
stage has changed, the source is not the run's). `AccessFailed`: the read could not be done
(unknown run, lock timeout, a reader's error, the database unavailable). Both are logged
before they are raised (`layer.py`); their messages hold only validated, bounded strings.
"""
from __future__ import annotations


class AccessDenied(Exception):
    """A policy refusal, already in the audit log (or the process log) when raised."""

    def __init__(self, role: str, stage: str, field: str, code: str, reason: str):
        self.role, self.stage, self.field, self.code, self.reason = role, stage, field, code, reason
        super().__init__(f"access denied: {role} at {stage} asked for {field}: {reason}")


class AccessFailed(Exception):
    """An access failure, already in the audit log (or the process log) when raised."""

    def __init__(self, role: str, stage: str, field: str, code: str):
        self.role, self.stage, self.field, self.code = role, stage, field, code
        super().__init__(f"access failed: {role} at {stage} asking for {field}: {code}")
```

### `hypocurate/access/stage.py`

```python
"""A run's stage, read from the database (never taken from the caller).

Called inside the access layer's transaction, after `hc_write_lock` has locked the run, so
the stage cannot change between this check and the read that follows.
"""
from __future__ import annotations

from sqlalchemy import Connection, text


def actual_stage(conn: Connection, run_id: int, status: str) -> str:
    """The stage of run `run_id`, whose locked status is `status` (from `hc_write_lock`)."""
    if status == "completed":
        frozen = conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r)"),
                              dict(r=run_id)).scalar_one()
        return "final" if frozen else "final_without_freeze"
    if status != "running":  # queued, failed
        return "none"
    row = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM plan WHERE run_id = :r) AS locked, "
        "EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r) AS frozen, "
        "EXISTS (SELECT 1 FROM calibration_result WHERE run_id = :r AND analysis_result_id IS NULL "
        "AND reason = 'no_dataset_frozen') AS closed"), dict(r=run_id)).one()
    if not row.locked:
        return "before_lock"
    if row.frozen:
        return "analysis"
    if row.closed:
        return "closed_without_freeze"
    return "curation"
```

### `hypocurate/access/layer.py`

```python
"""The access object: what one agent call may read from one run (PRD 4).

Created only by the trusted dispatcher (`dispatch.bind`), around an immutable
`AccessContext` captured once. There is no public constructor that takes a caller-chosen
run, role, stage or source (tests use their own helper). Every read goes through `get`
(one field) or `read_all` (the role's complete input, used by `inputs.role_input`).

**One read is one transaction** (`run_transaction`, retried on 40P01 / 40001):
1. `SET LOCAL lock_timeout`; check that the run exists; `hc_write_lock(p_run => …)`: the
   locking protocol of step 3 (the audit rows are writes to the run). Holding the run's lock,
   the stage and the rows read cannot change until commit: writers to the run follow the
   same protocol and wait. So `read_all` is one snapshot of the role's whole input;
2. the run's actual stage (`stage.actual_stage`);
3. the policy checks per field: known role and stage, the context's stage equals the actual
   one, the field is on the role's list;
4. the reads (`fields.READERS`); a reader may refuse (a policy denial with its code);
5. the audit rows: one per field, `allowed` true for a delivered read, false for a denial;
6. commit, and only then return or raise `AccessDenied`. A refusal therefore survives any
   rollback by the caller.

**Denial and failure are logged apart.** `detail.result` is "allowed", "denied" (a policy
refusal; `AccessDenied`) or "failed" (an access failure; `AccessFailed`): an unknown run, a
lock timeout, a reader's error, the database unavailable, a file-guard refusal
(`guarded.run_guarded`). `detail.code` is a fixed code. Only validated, bounded strings are
logged: a role, stage or field that is not one of ours is logged as "invalid" with its
length; a run id must be an integer.

**Failure rows are a named exception to the locking protocol** (owner, 2026-10-05; register
entry 'audit_failure_rows_without_run_lock'): they are written in their own short
transaction *without* `hc_write_lock`, because there is no run to lock (unknown run) or the
lock is what failed (timeout). An `audit_log` insert takes only a key-share lock on the run,
which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an
unknown run, `run_id` is NULL and the requested id is in `detail`.

**Fallback.** If a failure row cannot be written (the database is unavailable), the event
goes to the process log (logger `hypocurate.access`, one bounded JSON line). Durable logging
in the database is therefore not unconditional.

**Never call the access layer while holding the same run's lock**: the call would wait for
it, and fails after the lock timeout (logged as a failure).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError

from hypocurate.access.allowlist import FIELDS, ROLES, STAGES, allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.errors import AccessDenied, AccessFailed
from hypocurate.access.fields import READERS, Refused
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import RETRYABLE_SQLSTATES, run_transaction, sqlstate

# How long an access call waits for a run's lock before failing (milliseconds).
ACCESS_LOCK_TIMEOUT_MS = 5000

LOG = logging.getLogger("hypocurate.access")

# Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
DENIALS = {
    "unknown_role": "the role is not one of the five roles",
    "unknown_stage": "the stage is not one of the access stages",
    "stage_mismatch": "the run is no longer at the stage this access was bound to",
    "not_on_list": "the field is not on the role's list at the run's stage",
    "no_source": "the Curator reads one named source; none was bound",
    "source_not_recorded": "the source is not recorded for this run",
    "source_not_for_role": "only the Curator is bound to a source",
    "setting_not_recorded": "the agent setting is not recorded for this run",
    "empty_list": "the role has no field at this stage",
}
FAILURES = ("unknown_run", "lock_timeout", "reader_error", "database_error", "file_guard")
FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
_SOURCE_KEY = re.compile(r"[a-z][a-z0-9_]{0,40}")

_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :field, :allowed, :detail)").bindparams(bindparam("detail", type_=JSONB))
_TRUSTED = object()  # held by dispatch.bind (and the tests' helper); not a public constructor


def bounded(value: Any, valid: Iterable[str]) -> str:
    """`value` if it is one of ours, else "invalid"."""
    return value if isinstance(value, str) and value in valid else "invalid"


def bounded_source(value: Any) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) and _SOURCE_KEY.fullmatch(value) else "invalid"


def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | None = None, **extra) -> dict:
    d: dict[str, Any] = {"result": result}
    if code is not None:
        d["code"] = code
    if actual is not None:
        d["actual_stage"] = actual
    if ctx.source_key is not None:
        d["source"] = bounded_source(ctx.source_key)
    for name, raw, valid in (("role", ctx.role, ROLES), ("stage", ctx.stage, STAGES)):
        if bounded(raw, valid) == "invalid" and raw != "invalid":
            d[f"given_{name}_length"] = len(raw) if isinstance(raw, str) else -1
    d.update(extra)
    return d


def _row(ctx: AccessContext, run_id: int | None, function: str, allowed_: bool, detail: dict) -> dict:
    return dict(r=run_id, role=bounded(ctx.role, ROLES), stage=bounded(ctx.stage, STAGES),
                field=bounded(function, FUNCTIONS), allowed=allowed_, detail=detail)


def log_failure(engine: Engine, ctx: AccessContext, function: str, code: str, run_known: bool = True,
                **extra) -> None:
    """One failure row, in its own transaction, without the run lock (the named exception);
    the process log if the database cannot take it."""
    run_id = ctx.run_id if run_known else None
    detail = _detail(ctx, "failed", code, **extra)
    if not run_known:
        detail["requested_run"] = int(ctx.run_id)
    try:
        run_transaction(engine, lambda conn: conn.execute(_AUDIT, _row(ctx, run_id, function, False, detail)))
    except Exception as error:  # the database is unavailable: the process log is the fallback
        LOG.error(json.dumps({"audit_fallback": _row(ctx, run_id, function, False, detail),
                              "error": type(error).__name__}, sort_keys=True))


class _ReaderError(Exception):
    def __init__(self, field: str, error: BaseException):
        self.field, self.error_class = field, type(error).__name__
        super().__init__(field)


class Access:
    """What one role may read from one run at one stage. Immutable; see the module docstring."""

    __slots__ = ("_engine", "_context", "_lock_timeout_ms")

    def __init__(self, engine: Engine, context: AccessContext, *, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS,
                 _trusted: object = None):
        if _trusted is not _TRUSTED:
            raise TypeError("an access object is created only by hypocurate.access.dispatch.bind")
        if not isinstance(context, AccessContext) or not isinstance(context.run_id, int):
            raise TypeError("an access object needs an AccessContext with an integer run id")
        object.__setattr__(self, "_engine", engine)
        object.__setattr__(self, "_context", context)
        object.__setattr__(self, "_lock_timeout_ms", int(lock_timeout_ms))

    def __setattr__(self, name, value):
        raise AttributeError("an access object is immutable")

    @property
    def context(self) -> AccessContext:
        return self._context

    def __repr__(self) -> str:
        c = self._context
        return f"Access(run={c.run_id}, role={bounded(c.role, ROLES)!r}, stage={bounded(c.stage, STAGES)!r})"

    def get(self, field: str) -> Any:
        """One field, or AccessDenied / AccessFailed (already logged)."""
        return self._read(field, (field,))[field]

    def read_all(self) -> dict[str, Any]:
        """Every field on the role's list at its stage, in one transaction (one snapshot).
        Never empty: a role with no field at its stage gets AccessDenied (logged)."""
        ctx = self._context
        return self._read("role_input", tuple(sorted(allowed(ctx.role, ctx.stage))))

    def _read(self, function: str, fields: tuple) -> dict[str, Any]:
        ctx, engine = self._context, self._engine
        name = bounded(function if fields != (function,) else fields[0], FUNCTIONS)
        try:
            outcome = run_transaction(engine, lambda conn: self._transaction(conn, ctx, function, fields))
        except _ReaderError as error:
            log_failure(engine, ctx, error.field, "reader_error", error_class=error.error_class)
            raise AccessFailed(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), bounded(error.field, FUNCTIONS),
                               "reader_error") from error.__cause__
        except DBAPIError as error:
            code = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
            log_failure(engine, ctx, name, code)
            raise AccessFailed(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), name, code) from error
        kind = outcome[0]
        if kind == "unknown_run":
            log_failure(engine, ctx, name, "unknown_run", run_known=False)
            raise AccessFailed(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), name, "unknown_run")
        if kind == "denied":
            field, code = outcome[1]
            raise AccessDenied(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), bounded(field, FUNCTIONS),
                               code, DENIALS[code])
        return outcome[1]

    def _transaction(self, conn: Connection, ctx: AccessContext, function: str, fields: tuple) -> tuple:
        conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=ctx.run_id)).scalar_one():
            return ("unknown_run",)
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=ctx.run_id)).scalar_one()
        actual = actual_stage(conn, ctx.run_id, status)
        if not fields:  # role_input with nothing on the list: never an empty input
            code = ("unknown_role" if ctx.role not in ROLES else "unknown_stage" if ctx.stage not in STAGES
                    else "empty_list")
            conn.execute(_AUDIT, _row(ctx, ctx.run_id, "role_input", False, _detail(ctx, "denied", code, actual)))
            return ("denied", ("role_input", code))
        values, denied = {}, []
        for field in fields:
            code = _policy(ctx, field, actual)
            if code is None:
                try:
                    values[field] = READERS[field](conn, ctx)
                except Refused as refused:
                    code = refused.code
                except DBAPIError as error:
                    if sqlstate(error) in RETRYABLE_SQLSTATES:
                        raise
                    raise _ReaderError(field, error) from error
                except Exception as error:
                    raise _ReaderError(field, error) from error
            if code is not None:
                denied.append((field, code))
        if denied:  # nothing is delivered; each refused field is logged
            for field, code in denied:
                conn.execute(_AUDIT, _row(ctx, ctx.run_id, field, False, _detail(ctx, "denied", code, actual)))
            return ("denied", denied[0])
        for field in fields:
            conn.execute(_AUDIT, _row(ctx, ctx.run_id, field, True, _detail(ctx, "allowed", None, actual)))
        return ("allowed", values)


def _policy(ctx: AccessContext, field: str, actual: str) -> str | None:
    if ctx.role not in ROLES:
        return "unknown_role"
    if ctx.stage not in STAGES:
        return "unknown_stage"
    if ctx.stage != actual:
        return "stage_mismatch"
    if field not in allowed(ctx.role, actual) or field not in READERS:
        return "not_on_list"
    return None
```

### `hypocurate/access/fields.py`

```python
"""One read function per field of the access contract (`hypocurate.access.allowlist`).

Every function reads only rows of the access object's own run (single-run scope), and
builds its output from named keys only. Nothing is copied whole and then trimmed: a key
or value that is not named here never reaches a role. The layer (`layer.py`) calls these
inside its transaction, after the run is locked and the role's field is checked.

Stored records carry their fields in the common record format of step 4
(`CommonRecord.to_json()`): `harmonized` maps a field name to {value, unit, status, ...}.

Blinded views (the fields listed for the Planner, the Critic, the gap report and the
Commentator without a freeze) carry text only from vocabularies (`vocabulary.py`) or the
marker "unrecognized"; the plan is projected recursively by `PLAN_SCHEMA`. The post-freeze
fields (`records_full`, `flags_full`, `results`, `stage_outputs`, `run_cost`) return the stored
rows of the run: after the freeze the Analyst and the Commentator may see outcomes.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping

from sqlalchemy import Connection, text

from hypocurate.access import vocabulary as vocab
from hypocurate.access.allowlist import (CATEGORY_FIELDS, CONDITION_COUNT_FIELDS, CONDITION_RANGE_FIELDS,
                                         PLAN_SCHEMA, POWER_SCHEMA, SOURCE_META_FIELDS)
from hypocurate.access.context import AccessContext as Context
from hypocurate.sources import adapters
from hypocurate.sources.normalize import alloy_label, same_alloy_key
from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, AdapterError
from hypocurate.sources.versions import SOURCES, UnsealedVersion, load_sealed_version

HAS_VALUE = ("converted", "assigned")
UNITS = frozenset(u for u in HARMONIZED_FIELDS.values() if u)


class Refused(Exception):
    """A field function refuses this read (for example a Curator asking for a source its
    run did not record). The layer logs it as a denial with this code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _plain(v: Any) -> Any:
    """A database value as plain JSON: times as ISO text, exact numbers as text."""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


def _rows(conn: Connection, sql: str, **params) -> list:
    return conn.execute(text(sql), dict(params)).all()


# --- Shared readers -----------------------------------------------------------------

def _chosen_sources(conn: Connection, ctx: Context) -> list:
    """The run's chosen sources (a version recorded at dispatch), in key order, with the
    interpretation settings of that sealed version (never the mutable source row's)."""
    return _rows(conn, "SELECT s.key, sv.source_type, sv.data_kind, sv.grouping_unit, rs.source_version_id "
                       "FROM run_source rs JOIN source s ON s.id = rs.source_id "
                       "JOIN source_version sv ON sv.id = rs.source_version_id "
                       "WHERE rs.run_id = :r AND rs.source_version_id IS NOT NULL ORDER BY s.key", r=ctx.run_id)


def _stored_records(conn: Connection, ctx: Context) -> list:
    return _rows(conn, "SELECT rec.id, s.key AS source, rec.source_item_key, rec.item_index, rec.kind, rec.alloy, "
                       "rec.harmonized, rec.reported, rec.paper_reference, rec.paper_doi, "
                       "sv.fingerprint AS version_fingerprint FROM record rec "
                       "JOIN source_version sv ON sv.id = rec.source_version_id "
                       "JOIN source s ON s.id = sv.source_id "
                       "WHERE rec.extraction_run_id = :r ORDER BY rec.id", r=ctx.run_id)


def _status(entry: Any) -> str | None:
    """A field's status, only if it is one of the known statuses."""
    if isinstance(entry, Mapping) and entry.get("status") in STATUSES:
        return entry["status"]
    return None


def _number(entry: Any) -> float | None:
    """A field's value, only if it has a value status and is a finite number."""
    if _status(entry) in HAS_VALUE:
        v = entry.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
            return float(v)
    return None


def _category(field: str, entry: Any) -> str | None:
    """A category field's value through its vocabulary (or the marker), only if it has a
    value status; None otherwise."""
    if _status(entry) in HAS_VALUE:
        return vocab.category(field, entry.get("value"))
    return None


def _unrecognized(harmonized_rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Per category field, how many values are unrecognized (counts only)."""
    return vocab.unrecognized_counts((f, h.get(f, {}).get("value")) for h in harmonized_rows
                                     for f in CATEGORY_FIELDS if _status(h.get(f)) in HAS_VALUE)


def _composition(entry: Any) -> dict[str, float] | None:
    """A composition (element -> atomic %), only if every amount is a finite number."""
    if _status(entry) not in HAS_VALUE or not isinstance(entry.get("value"), Mapping):
        return None
    out = {}
    for element, amount in entry["value"].items():
        if not (isinstance(element, str) and element.isalpha() and len(element) <= 2):
            return None
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount):
            return None
        out[element] = float(amount)
    return out


def _counts(harmonized_rows: Iterable[Mapping[str, Any]]) -> dict:
    """Counts by field status and by category value (through the vocabularies), and the
    unrecognized counts. Never a value of a non-category field."""
    harmonized_rows = list(harmonized_rows)
    n = 0
    by_status = {f: Counter() for f in HARMONIZED_FIELDS}
    by_category = {f: Counter() for f in CATEGORY_FIELDS}
    for h in harmonized_rows:
        n += 1
        for f in HARMONIZED_FIELDS:
            by_status[f][_status(h.get(f)) or "missing"] += 1
        for f in CATEGORY_FIELDS:
            value = _category(f, h.get(f))
            if value is not None:
                by_category[f][value] += 1
    return {"n_records": n,
            "by_status": {f: dict(sorted(c.items())) for f, c in by_status.items()},
            "by_category": {f: dict(sorted(c.items())) for f, c in by_category.items()},
            "unrecognized": _unrecognized(harmonized_rows)}


# --- The fields ---------------------------------------------------------------------

def claim(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT h.number, hv.version_number, hv.text, h.narrower_of_run_id IS NOT NULL AS narrower "
                      "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                      "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r", r=ctx.run_id)[0]
    return {"query": row.number, "version": row.version_number, "text": row.text, "narrower_question": row.narrower}


def domain(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT d.key, d.name, d.profile_name FROM run r "
                      "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                      "JOIN domain d ON d.id = hv.confirmed_domain_id WHERE r.id = :r", r=ctx.run_id)[0]
    return {"key": row.key, "name": row.name, "profile": row.profile_name}


def sources_meta(conn: Connection, ctx: Context) -> list[dict]:
    """Name, licence and fields available from the code's source definitions; interpretation
    settings from the sealed version the run recorded. The source registry's text never."""
    out = []
    for row in _chosen_sources(conn, ctx):
        if ctx.role == "curator" and row.key != ctx.source_key:
            continue
        d = SOURCES.get(row.key)
        values = {"key": row.key,
                  "name": d.name if d else vocab.UNRECOGNIZED,
                  "source_type": row.source_type, "data_kind": row.data_kind,
                  "licence": d.licence if d else vocab.UNRECOGNIZED,
                  "grouping_unit": row.grouping_unit,
                  "fields_available": [f for f in d.properties_covered if f in HARMONIZED_FIELDS] if d else []}
        out.append({k: values[k] for k in SOURCE_META_FIELDS})
    return out


def tag_values(conn: Connection, ctx: Context) -> list[dict]:
    return [{"kind": kind, "value": value} for kind, value in _rows(
        conn, "SELECT kind, value FROM tag_value WHERE status = 'approved' ORDER BY kind, value")]


def record_counts(conn: Connection, ctx: Context) -> list[dict]:
    """Computed by code from each chosen source's sealed version, through its adapter
    (records are stored only after the rules lock)."""
    out = []
    for row in _chosen_sources(conn, ctx):
        try:
            result = adapters.read(load_sealed_version(conn, row.source_version_id))
        except (AdapterError, UnsealedVersion):
            out.append({"source": row.key, "readable": False})
            continue
        counts = _counts({f: v.to_json() for f, v in r.harmonized.items()} for r in result.records)
        out.append({"source": row.key, "readable": True, **counts})
    return out


def project(value: Any, schema: Any) -> Any:
    """`value` projected by `schema` (allowlist.PLAN_SCHEMA): named keys only, recursively;
    vocabulary leaves give the value or the marker; number, integer, field and unit leaves
    give the value or nothing. Returns None for nothing."""
    if isinstance(schema, Mapping):
        if not isinstance(value, Mapping):
            return None
        out = {}
        for key, sub in schema.items():
            if key in value:
                p = project(value[key], sub)
                if p is not None:
                    out[key] = p
        return out
    if isinstance(schema, tuple) and schema[0] == "list":
        if not isinstance(value, list):
            return None
        return [p for p in (project(v, schema[1]) for v in value) if p is not None]
    if isinstance(schema, frozenset):
        return vocab.code(value, schema)
    if isinstance(value, bool):
        return None
    if schema == "number":
        return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None
    if schema == "integer":
        return value if isinstance(value, int) else None
    if schema == "field":
        return value if isinstance(value, str) and value in HARMONIZED_FIELDS else None
    if schema == "unit":
        return value if isinstance(value, str) and value in UNITS else None
    raise ValueError(f"unknown schema leaf {schema!r}")


def plan_fields_to_extract(conn: Connection, ctx: Context) -> list[str]:
    """Only names of the common fields, in order, without repeats."""
    content = _rows(conn, "SELECT content FROM plan WHERE run_id = :r", r=ctx.run_id)[0].content
    listed = project(content, PLAN_SCHEMA).get("fields_to_extract", []) if isinstance(content, Mapping) else []
    return list(dict.fromkeys(listed))


def source_content(conn: Connection, ctx: Context) -> dict:
    """The sealed files of the Curator's one source, from the version its run recorded."""
    if ctx.source_key is None:
        raise Refused("no_source")
    vid = conn.execute(text(
        "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
        "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL"),
        dict(r=ctx.run_id, k=ctx.source_key)).scalar_one_or_none()
    if vid is None:
        raise Refused("source_not_recorded")
    version = load_sealed_version(conn, vid)
    return {"source": ctx.source_key, "files": dict(version.files)}


def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
    """No measured number of any field (owner, 2026-10-05): statuses, categories from their
    vocabularies, identity. No paper title and no origin key (step 5 review, finding 3)."""
    out = []
    for r in _stored_records(conn, ctx):
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        composition = _composition(h.get("composition"))
        out.append({
            "id": r.id, "source": r.source, "item_index": r.item_index, "kind": r.kind,
            # The label is derived by code from the composition, never taken from the source.
            "alloy": alloy_label(composition) if composition else None,
            "composition": composition, "paper_doi": vocab.doi(r.paper_doi),
            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
            "categories": {f: _category(f, h.get(f)) for f in CATEGORY_FIELDS},
        })
    return out


def _flag_records(conn: Connection, ctx: Context) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for flag_id, record_id in _rows(conn, "SELECT fr.flag_id, fr.record_id FROM flag_record fr "
                                          "JOIN flag f ON f.id = fr.flag_id WHERE f.run_id = :r "
                                          "ORDER BY fr.flag_id, fr.record_id", r=ctx.run_id):
        out.setdefault(flag_id, []).append(record_id)
    return out


def flags_kind(conn: Connection, ctx: Context) -> list[dict]:
    """Kind, category and records only: never the numbers compared (PRD 4)."""
    records = _flag_records(conn, ctx)
    return [{"id": f.id, "kind": vocab.code(f.kind, vocab.FLAG_KINDS),
             "category": vocab.code(f.category, vocab.FLAG_CATEGORIES), "records": records.get(f.id, [])}
            for f in _rows(conn, "SELECT id, kind, category FROM flag WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def flags_full(conn: Connection, ctx: Context) -> list[dict]:
    records = _flag_records(conn, ctx)
    return [{"id": f.id, "kind": f.kind, "category": f.category, "records": records.get(f.id, []),
             "compared_values": f.compared_values, "critic_class": f.critic_class,
             "critic_reason": f.critic_reason, "raised_at": _plain(f.raised_at),
             "classified_at": _plain(f.classified_at)}
            for f in _rows(conn, "SELECT id, kind, category, compared_values, critic_class, critic_reason, "
                                 "raised_at, classified_at FROM flag WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def plan(conn: Connection, ctx: Context) -> dict:
    p = _rows(conn, "SELECT content, fingerprint, locked_at, sufficiency_option, min_records, min_alloys, "
                    "min_groups, min_resid_df, sensitivity_analysis_keys, power_assumptions "
                    "FROM plan WHERE run_id = :r", r=ctx.run_id)[0]
    return {"content": project(p.content, PLAN_SCHEMA) or {},
            "fingerprint": p.fingerprint, "locked_at": _plain(p.locked_at),
            "sufficiency_option": p.sufficiency_option,
            "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
                         "resid_df": p.min_resid_df},
            "sensitivity_analyses": [vocab.code(k, vocab.SENSITIVITY_KEYS) for k in p.sensitivity_analysis_keys],
            "power_assumptions": project(p.power_assumptions, POWER_SCHEMA)}


def records_full(conn: Connection, ctx: Context) -> list[dict]:
    return [{"id": r.id, "source": r.source, "origin": r.source_item_key, "item_index": r.item_index,
             "kind": r.kind, "alloy": r.alloy, "harmonized": r.harmonized, "reported": r.reported,
             "paper_reference": r.paper_reference, "paper_doi": r.paper_doi,
             "version_fingerprint": r.version_fingerprint}
            for r in _stored_records(conn, ctx)]


def decisions(conn: Connection, ctx: Context) -> dict:
    sets: dict[str, list[int]] = {}
    for key, record_id in _rows(conn, "SELECT a.key, asr.record_id FROM analysis_set a "
                                      "LEFT JOIN analysis_set_record asr ON asr.analysis_set_id = a.id "
                                      "WHERE a.run_id = :r ORDER BY a.key, asr.record_id", r=ctx.run_id):
        key = vocab.code(key, vocab.ANALYSIS_SET_KEYS)
        sets.setdefault(key, [])
        if record_id is not None:
            sets[key].append(record_id)
    return {"records": [{"record": rec, "eligible": eligible, "rule": vocab.code(rule, vocab.ELIGIBILITY_RULES)}
                        for rec, eligible, rule in _rows(
                conn, "SELECT record_id, eligible, rule FROM run_record WHERE run_id = :r ORDER BY record_id",
                r=ctx.run_id)],
            "sets": sets}


def results(conn: Connection, ctx: Context) -> dict:
    run = _rows(conn, "SELECT status, outcome, verdict, exploratory, fixed_plan, agent_mode, failure_reason "
                      "FROM run WHERE id = :r", r=ctx.run_id)[0]
    snap = _rows(conn, "SELECT fingerprint, n_records, frozen_at FROM run_snapshot WHERE run_id = :r", r=ctx.run_id)
    analyses = _rows(conn, "SELECT ar.id, ar.scope, a.key AS analysis_set, s.key AS source, ar.n_records, "
                           "ar.n_alloys, ar.n_groups, ar.resid_df, ar.check1_passed, ar.check2_passed, "
                           "ar.minimums_met, ar.estimate, ar.std_error, ar.p_value, ar.estimated_power, ar.label "
                           "FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
                           "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id",
                     r=ctx.run_id)
    calibration = _rows(conn, "SELECT analysis_result_id, status, reason, assumptions, n_simulations, seed, "
                              "null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, "
                              "confidence_flag FROM calibration_result WHERE run_id = :r ORDER BY id", r=ctx.run_id)
    return {"run": {k: _plain(v) for k, v in run._mapping.items()},
            "freeze": {k: _plain(v) for k, v in snap[0]._mapping.items()} if snap else None,
            "analyses": [{k: _plain(v) for k, v in a._mapping.items()} for a in analyses],
            "calibration": [{k: _plain(v) for k, v in c._mapping.items()} for c in calibration]}


def coverage(conn: Connection, ctx: Context) -> dict:
    """Codes and counts only: no failure text (step 5 review, finding 3). `unrecognized`: per
    source, how many category values of the run's records were unrecognized (owner, 2026-10-05)."""
    by_source: dict[str, list] = {}
    for r in _stored_records(conn, ctx):
        by_source.setdefault(r.source, []).append(r.harmonized if isinstance(r.harmonized, Mapping) else {})
    per_source = [{"source": key, "search_status": st, "nothing_found": nf,
                   "unrecognized": _unrecognized(by_source.get(key, []))}
                  for key, st, nf in _rows(
                      conn, "SELECT s.key, rs.search_status, rs.nothing_found FROM run_source rs "
                            "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r ORDER BY s.key", r=ctx.run_id)]
    view = _rows(conn, "SELECT * FROM run_search_coverage WHERE run_id = :r", r=ctx.run_id)[0]
    return {"sources": per_source,
            "lists": {k: list(v) if v is not None else [] for k, v in view._mapping.items() if k != "run_id"}}


def stage_outputs(conn: Connection, ctx: Context) -> list[dict]:
    return [{k: _plain(v) for k, v in s._mapping.items()} for s in _rows(
        conn, "SELECT id, stage, attempt, role, status, input, output, reasoning, tool_calls, model, "
              "started_at, finished_at FROM stage_result WHERE run_id = :r ORDER BY id", r=ctx.run_id)]


def run_cost(conn: Connection, ctx: Context) -> dict:
    total = _rows(conn, "SELECT * FROM model_call_totals_by_run WHERE run_id = :r", r=ctx.run_id)[0]
    stages = _rows(conn, "SELECT * FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage_result_id",
                   r=ctx.run_id)
    return {"total": {k: _plain(v) for k, v in total._mapping.items() if k != "run_id"},
            "stages": [{k: _plain(v) for k, v in s._mapping.items() if k != "run_id"} for s in stages]}


def stored_record_counts(conn: Connection, ctx: Context) -> list[dict]:
    by_source: dict[str, list] = {}
    for r in _stored_records(conn, ctx):
        by_source.setdefault(r.source, []).append(r.harmonized if isinstance(r.harmonized, Mapping) else {})
    return [{"source": key, **_counts(rows)} for key, rows in sorted(by_source.items())]


def _summary(harmonized_rows: list[Mapping[str, Any]]) -> dict:
    out: dict[str, Any] = {"n_records": len(harmonized_rows)}
    for f in CONDITION_RANGE_FIELDS:
        values = [v for v in (_number(h.get(f)) for h in harmonized_rows) if v is not None]
        out[f] = {"n": len(values), "min": min(values) if values else None, "max": max(values) if values else None}
    for f in CONDITION_COUNT_FIELDS:
        out[f] = dict(sorted(Counter(v for v in (_category(f, h.get(f)) for h in harmonized_rows)
                                     if v is not None).items()))
    return out


def condition_summaries(conn: Connection, ctx: Context) -> dict:
    """Owner, 2026-10-05: summaries of the non-outcome conditions the stored records cover,
    per alloy (grouped by the same-alloy rule) and overall. No row-level value, no outcome."""
    rows = [r.harmonized if isinstance(r.harmonized, Mapping) else {} for r in _stored_records(conn, ctx)]
    groups: dict[str, list] = {}
    for h in rows:
        composition = _composition(h.get("composition"))
        key = same_alloy_key(composition) if composition else "composition not available"
        groups.setdefault(key, []).append(h)
    return {"overall": _summary(rows),
            "per_alloy": [{"alloy": key, **_summary(g)} for key, g in sorted(groups.items())]}


def gap_report(conn: Connection, ctx: Context) -> list[dict]:
    """The output of each Analyst stage of the run, and nothing else of those stages."""
    return [{"stage": s.stage, "attempt": s.attempt, "status": s.status, "output": s.output} for s in _rows(
        conn, "SELECT stage, attempt, status, output FROM stage_result WHERE run_id = :r AND role = 'analyst' "
              "ORDER BY id", r=ctx.run_id)]


def outcome(conn: Connection, ctx: Context) -> dict:
    row = _rows(conn, "SELECT status, outcome, verdict, exploratory FROM run WHERE id = :r", r=ctx.run_id)[0]
    return {"status": row.status, "outcome": row.outcome, "verdict": row.verdict, "exploratory": row.exploratory}


READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
    "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
    "record_counts": record_counts, "plan_fields_to_extract": plan_fields_to_extract,
    "source_content": source_content, "record_metadata": record_metadata, "flags_kind": flags_kind,
    "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
    "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
    "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
    "gap_report": gap_report, "outcome": outcome,
}
```

### `hypocurate/access/inputs.py`

```python
"""A role's complete input at its stage, as data (PRD 4, testing requirement).

`role_input(access)` reads every field on the role's list in one transaction: one snapshot.
It never returns an empty input: a role with no field at its stage gets AccessDenied
(logged). The agents (step 8) build their prompts from this and answer their tool calls
through the same access object. This is the **projected data** a role receives; the actual
outbound model request (instructions, message history, tool errors, retry prompts) is a step 8
acceptance requirement to test.
"""
from __future__ import annotations

from typing import Any

from hypocurate.access.layer import Access


def role_input(access: Access) -> dict[str, Any]:
    return access.read_all()
```

### `hypocurate/access/file_guard.py`

```python
"""A tripwire against accidental file access by pipeline code (step 5; review finding 1).

**What it is.** In the process that runs one pipeline run (`guarded.run_guarded`), a Python
audit hook (`sys.addaudithook`) refuses, with `PermissionError`, what *trusted, reviewed*
pipeline code should never do by mistake:
- reading or listing anything outside the Python installation (standard library, installed
  packages, the certificate bundle) and the `hypocurate` package's code: so the repository
  root, `tests/`, `docs/` (including `docs/reviews/`) and `data/`;
- writing anywhere but the run's private scratch directory;
- relative paths;
- starting another program (`subprocess`, `os.system`, `exec`, `spawn`, `fork`) and loading a
  new native library through `ctypes`.
Each refusal is written as one bounded line to the process's standard error, and the parent
copies it into the audit log as a failure (code `file_guard`) when it knows the run.

**What it is not.** Python's own documentation warns that audit hooks are not suitable for
implementing a sandbox, because code in the same process can bypass them
(https://docs.python.org/3/library/sys.html#sys.addaudithook; PEP 578). In particular, as the
step 5 review showed:
- a file descriptor that is already open can still be read;
- the guard's own state can be changed from inside the process;
- `ctypes`, once imported (the database driver imports it before the guard is installed),
  can still read and write process memory directly (`from_address`; tested). Foreign calls
  raise an audit event the hook refuses (`string_at` was refused in our runs, though the
  review reports it working in its setup), but that is no barrier to code that tries;
- sockets, and so the database with the credentials the process has, are not restricted;
- the child inherits its environment, and startup hooks or modules imported before the guard
  run unguarded;
- checking a path and then opening it is not atomic.
So it catches accidents by our own code; it does not stop code that tries to get around it.
That is enough under the threat model (owner, 2026-10-05; CLAUDE.md, register 'threat_model'):
agents return text only and never execute code, and only trusted code runs. Agents that
execute code are in the backlog, with operating-system isolation as a precondition.

**The one construction-level guarantee** about answer material is the deployed image: it
contains no `tests/` and no `docs/` (Dockerfile; checked in CI by `scripts/check_runtime_image.py`).
In development the files exist on disk, and only this tripwire stands in the way of an
accidental read.

`install()` runs only in the process started by `python -m hypocurate.access.guarded`, once,
with a private scratch directory; it refuses to run in any other process, so the web service,
the migrations, the `sources` commands (registration reads `data/`) and the tests are never
guarded.
"""
from __future__ import annotations

import json
import os
import stat
import sys
import sysconfig
import tempfile
from pathlib import Path

GUARDED_MAIN = "hypocurate.access.guarded"
PACKAGE_DIR = os.path.realpath(Path(__file__).resolve().parent.parent)
# The system temporary directory, read when this module is imported (before the guarded
# process points TMPDIR at its scratch directory). Scratch directories live directly in it.
SYSTEM_TEMP = os.path.realpath(tempfile.gettempdir())
SCRATCH_PREFIX = "hc-run-"

# Events that start another program or load native code: always refused.
REFUSED_EVENTS = frozenset({
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty",
    "pty.spawn", "ctypes.dlopen", "ctypes.dlsym", "ctypes.call_function",
})
# Events that change the file system: allowed only inside the scratch directory.
WRITE_EVENTS = frozenset({
    "os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.chown", "os.utime", "os.truncate",
    "os.link", "os.symlink", "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree",
    "shutil.move", "shutil.rmtree", "shutil.chown", "shutil.make_archive", "shutil.unpack_archive",
})
LIST_EVENTS = frozenset({"os.listdir", "os.scandir"})
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND

_state: dict = {"installed": False, "scratch": None, "read_roots": ()}


def installed() -> bool:
    return _state["installed"]


def scratch_directory() -> str | None:
    return _state["scratch"]


def read_roots() -> tuple[str, ...]:
    """The directories the guarded process may read: the Python installation and the package."""
    paths = sysconfig.get_paths()
    roots = {os.path.realpath(paths[k]) for k in ("stdlib", "platstdlib", "purelib", "platlib")}
    roots.add(PACKAGE_DIR)
    return tuple(sorted(roots))


def _inside(path: str, roots) -> bool:
    return any(path == r or path.startswith(r + os.sep) for r in roots)


def _resolve(path) -> str | None:
    """The real absolute path, or None for a relative one (refused)."""
    path = os.fsdecode(path)
    if not os.path.isabs(path):
        return None
    return os.path.realpath(path)


REPORT_PREFIX = "HCGUARD "  # one line per refusal on standard error, read by guarded.run_guarded


def _printable(value: str, limit: int = 200) -> str:
    return "".join(c if c.isprintable() else "?" for c in value[:limit])


def _refuse(what: str, event: str = "open") -> None:
    message = f"file guard: {what} is outside the approved inputs of pipeline code"
    try:  # no audit event is raised by writing to an already-open stream
        sys.stderr.write(REPORT_PREFIX + json.dumps({"event": _printable(event, 40), "what": _printable(what)}) + "\n")
        sys.stderr.flush()
    except Exception:
        pass
    raise PermissionError(message)


def _check_path(path, writing: bool) -> None:
    if path is None or isinstance(path, int):  # an already-open descriptor (checked when opened)
        return
    real = _resolve(path)
    if real is None:
        _refuse(f"relative path {os.fsdecode(path)!r}", "relative_path")
    scratch = _state["scratch"]
    allowed = _inside(real, (scratch,)) if writing else _inside(real, _state["read_roots"] + (scratch,))
    if not allowed:
        _refuse(f"{'writing' if writing else 'reading'} {real}", "write" if writing else "read")


def _hook(event: str, args: tuple) -> None:
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool((flags or 0) & _WRITE_FLAGS)
        _check_path(path, writing)
    elif event in LIST_EVENTS:
        _check_path(args[0] if args and args[0] is not None else os.getcwd(), writing=False)
    elif event in WRITE_EVENTS:
        for a in args:
            if isinstance(a, (str, bytes, os.PathLike)):
                _check_path(a, writing=True)
    elif event in REFUSED_EVENTS:
        _refuse(f"{event}", event)


def check_scratch(scratch: str) -> None:
    """A scratch directory must be a fresh, empty, private `hc-run-*` directory directly in
    the system temporary directory, so that it can never open up anything else."""
    info = os.lstat(scratch)
    if (os.path.dirname(scratch) != SYSTEM_TEMP or not os.path.basename(scratch).startswith(SCRATCH_PREFIX)
            or not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_uid != os.getuid() or os.listdir(scratch)):
        raise RuntimeError(f"unsuitable scratch directory {scratch}")


def install(scratch: str) -> None:
    """Installs the guard for the rest of this process. Only `python -m hypocurate.access.guarded`
    may call it, once, with its private scratch directory."""
    main = sys.modules.get("__main__")
    spec = getattr(main, "__spec__", None)
    if spec is None or spec.name != GUARDED_MAIN:
        raise RuntimeError("the file guard is installed only in the process started by "
                           f"`python -m {GUARDED_MAIN}`")
    if _state["installed"]:
        raise RuntimeError("the file guard is already installed")
    scratch = os.path.realpath(scratch)
    check_scratch(scratch)
    sys.dont_write_bytecode = True  # no .pyc written next to the package
    _state.update(installed=True, scratch=scratch, read_roots=read_roots())
    sys.addaudithook(_hook)
```

### `hypocurate/access/guarded.py`

```python
"""Runs pipeline code in a fresh process under the file guard's tripwire (`file_guard`).

`run_guarded("hypocurate.module:function", payload, audit=(engine, run_id))` starts
`python -m hypocurate.access.guarded`, sends it the target and a JSON payload, and returns
the target's JSON result. The child:

1. receives a private scratch directory (mode 0700, created by the parent, which removes it
   when the child ends, however it ends) and points `TMPDIR`, `MPLCONFIGDIR` and
   `XDG_CACHE_HOME` at it, for libraries that need a cache or temporary files (the
   plotting library in step 7); its working directory is the scratch directory;
2. removes the repository root from its import path (the `hypocurate` package is already
   imported and keeps its own path), and imports the modules in `PRELOADED`;
3. installs the guard;
4. imports the target, which must be inside the `hypocurate` package, calls it with the
   payload, writes the result to its standard output and exits.

The guard's refusals come back on the child's standard error; the parent copies each into
the audit log as a failure (code `file_guard`) for the run given in `audit`, or to the
process log if no run is given or the database cannot take it.

This is a tripwire against *accidental* file access by trusted code, not a sandbox (see
`file_guard`). This is the only place that installs it. The pipeline's entry points (the
command line's run command, step 8; the worker's run of a claimed job, step 9) run each
pipeline run through `run_guarded`. The web service, the migrations, the `sources` commands
and the test process do not.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from hypocurate.access import file_guard

MODULE = "hypocurate.access.guarded"
SCRATCH_ENV = ("TMPDIR", "MPLCONFIGDIR", "XDG_CACHE_HOME")
# Imported before the guard is installed: the database driver imports `ctypes`, which loads
# the process's own symbols when it is first imported, and the guard refuses any ctypes
# load. Importing it first changes no refusal: after installation every ctypes load,
# symbol lookup and call is still refused, and reading the Python installation is allowed.
PRELOADED = ("psycopg",)


class GuardedRunError(Exception):
    """The guarded process failed; the message is its error."""


MAX_REPORTED = 100  # refusals copied into the audit log per run; the rest are counted


def _report_refusals(stderr: str, audit) -> None:
    """Copies the guard's refusal lines into the audit log (or the process log)."""
    from hypocurate.access.context import AccessContext
    from hypocurate.access.layer import LOG, log_failure
    reports = []
    for line in stderr.splitlines():
        if line.startswith(file_guard.REPORT_PREFIX):
            try:
                r = json.loads(line[len(file_guard.REPORT_PREFIX):])
                reports.append({"event": str(r.get("event", ""))[:40], "what": str(r.get("what", ""))[:200]})
            except ValueError:
                reports.append({"event": "unreadable", "what": ""})
    for i, r in enumerate(reports[:MAX_REPORTED]):
        extra = dict(r, **({"more": len(reports) - MAX_REPORTED} if i == MAX_REPORTED - 1
                           and len(reports) > MAX_REPORTED else {}))
        if audit is None:
            LOG.warning(json.dumps({"file_guard": extra}, sort_keys=True))
        else:
            engine, run_id = audit
            log_failure(engine, AccessContext(int(run_id), "invalid", "invalid"), "guarded_run", "file_guard",
                        **extra)


def run_guarded(target: str, payload: Any = None, env: dict[str, str] | None = None,
                timeout: float | None = None, audit=None) -> Any:
    """Runs `target(payload)` in a guarded child process and returns its JSON result.
    `audit`: (engine, run_id), where the guard's refusals are logged as failures."""
    if not target.startswith("hypocurate.") or ":" not in target:
        raise ValueError(f"target {target!r} must be 'hypocurate.<module>:<function>'")
    # mode 0700, in the system temporary directory; removed here, whatever the child does
    scratch = tempfile.mkdtemp(prefix=file_guard.SCRATCH_PREFIX, dir=file_guard.SYSTEM_TEMP)
    try:
        completed = subprocess.run([sys.executable, "-m", MODULE],
                                   input=json.dumps({"target": target, "payload": payload, "scratch": scratch}),
                                   capture_output=True, text=True, timeout=timeout,
                                   env=env if env is not None else dict(os.environ))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    _report_refusals(completed.stderr, audit)
    lines = completed.stdout.strip().splitlines()
    try:
        answer = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise GuardedRunError(f"the guarded process gave no answer (exit {completed.returncode}): "
                              f"{completed.stderr.strip()[-2000:]}") from None
    if not answer.get("ok"):
        raise GuardedRunError(answer.get("error", "unknown error"))
    return answer["result"]


def _main() -> int:
    request = json.loads(sys.stdin.read())
    scratch = request["scratch"]
    for name in SCRATCH_ENV:
        os.environ[name] = scratch
    tempfile.tempdir = scratch
    os.chdir(scratch)
    package_parent = os.path.dirname(file_guard.PACKAGE_DIR)
    sys.path[:] = [p for p in sys.path if p not in ("", ".") and os.path.realpath(p) != package_parent]
    sys.path_importer_cache.clear()
    for name in PRELOADED:
        importlib.import_module(name)
    file_guard.install(scratch)
    try:
        module_name, function = request["target"].split(":", 1)
        if not module_name.startswith("hypocurate."):
            raise ValueError(f"target {request['target']!r} is outside the package")
        result = getattr(importlib.import_module(module_name), function)(request["payload"])
        answer = {"ok": True, "result": result}
    except Exception as error:  # reported to the parent, which raises GuardedRunError
        answer = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    sys.stdout.write("\n" + json.dumps(answer) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
```

### `hypocurate/access/guard_probe.py`

```python
"""Checks of the file guard from inside a guarded process (`guarded.run_guarded`).

`probe(actions)` performs each action and reports "ok", or "refused: ..." when the guard
refused it. It is how the tests (and, later, a deploy-time self-check) show what the
tripwire catches. It reads nothing it reports beyond a byte count. It does not show that
the guard cannot be bypassed: it cannot be, by design (see `file_guard`).
"""
from __future__ import annotations

import io
import os
import pathlib
import ssl
import subprocess
import tempfile
from typing import Any, Callable


def _read(path: str, how: str) -> str:
    if how == "open":
        with open(path, "rb") as f:
            return f"ok {len(f.read())} bytes"
    if how == "io.open":
        with io.open(path, "rb") as f:
            return f"ok {len(f.read())} bytes"
    if how == "pathlib":
        return f"ok {len(pathlib.Path(path).read_bytes())} bytes"
    if how == "os.open":
        fd = os.open(path, os.O_RDONLY)
        os.close(fd)
        return "ok"
    raise ValueError(how)


def _list(path: str, how: str) -> str:
    if how == "listdir":
        return f"ok {len(os.listdir(path))} entries"
    if how == "scandir":
        with os.scandir(path) as it:
            return f"ok {sum(1 for _ in it)} entries"
    raise ValueError(how)


def _write(path: str) -> str:
    with open(path, "w") as f:
        f.write("x")
    return "ok"


def _write_scratch(_: Any) -> str:
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("cache")
        name = f.name
    with open(name) as f:
        assert f.read() == "cache"
    os.remove(name)
    cache = os.path.join(os.environ["MPLCONFIGDIR"], "cache.txt")
    with open(cache, "w") as f:
        f.write("x")
    return f"ok in {os.path.dirname(name) == os.environ['TMPDIR']}"


def _scratch(_: Any) -> str:
    """Where the scratch directory is, and its permissions (it is removed when the run ends)."""
    return f"ok {os.environ['TMPDIR']} {oct(os.stat(os.environ['TMPDIR']).st_mode & 0o777)} {os.getcwd()}"


def _render(_: Any) -> str:
    from hypocurate.web.app import templates
    html = templates.get_template("login.html").render(error=None)
    return f"ok {'<form' in html}"


def _database(_: Any) -> str:
    from sqlalchemy import text
    from hypocurate.db.engine import make_engine
    engine = make_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        value = conn.execute(text("SELECT now() IS NOT NULL AND 1 = 1")).scalar_one()
    engine.dispose()
    return f"ok {value}"


def _certificates(_: Any) -> str:
    import urllib.request
    context = ssl.create_default_context()
    urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    return f"ok {context.cert_store_stats()['x509_ca'] > 0}"


def _subprocess(_: Any) -> str:
    subprocess.run(["true"], check=True)
    return "ok"


def _system(_: Any) -> str:
    os.system("true")
    return "ok"


def _ctypes(_: Any) -> str:
    import ctypes
    ctypes.CDLL(None)
    return "ok"


def _ctypes_string_at(_: Any) -> str:
    """Calls through preloaded ctypes functions (string_at) raise the call event the guard refuses."""
    import ctypes
    return f"ok {ctypes.string_at(ctypes.c_char_p(b'x'), 1)!r}"


def _ctypes_from_address(_: Any) -> str:
    """A documented limit of the tripwire: ctypes, once imported before the guard (by the database
    driver), can still read process memory directly (`from_address`); only new library loads and
    foreign calls are refused."""
    import ctypes
    buffer = ctypes.create_string_buffer(b"x")
    return f"ok {ctypes.c_char.from_address(ctypes.addressof(buffer)).value!r}"


def _register(_: Any) -> str:
    from hypocurate.sources.versions import SOURCES, read_definition_files
    read_definition_files(SOURCES["mpea"])
    return "ok"


def _role_input(action: dict) -> str:
    """A role's complete input, built through the dispatcher and the access layer inside the
    guarded process."""
    import base64
    import json
    from hypocurate.access import bind, role_input
    from hypocurate.db.engine import make_engine
    engine = make_engine(os.environ["DATABASE_URL"])
    access = bind(engine, action["run"], action["agent_setting"], source_key=action.get("source"))
    out = json.dumps(role_input(access), sort_keys=True,
                     default=lambda b: base64.b64encode(b).decode() if isinstance(b, bytes) else str(b))
    engine.dispose()
    return out


ACTIONS: dict[str, Callable[[dict], str]] = {
    "read": lambda a: _read(a["path"], a.get("how", "open")),
    "list": lambda a: _list(a["path"], a.get("how", "listdir")),
    "write": lambda a: _write(a["path"]),
    "write_scratch": _write_scratch, "scratch": _scratch, "render": _render, "database": _database, "certificates": _certificates,
    "subprocess": _subprocess, "system": _system, "ctypes": _ctypes, "ctypes_string_at": _ctypes_string_at,
    "ctypes_from_address": _ctypes_from_address,
    "register": _register,
    "role_input": _role_input,
}


def probe(actions: list[dict]) -> list[str]:
    out = []
    for action in actions:
        try:
            out.append(ACTIONS[action["op"]](action))
        except PermissionError as error:
            out.append(f"refused: {error}")
        except Exception as error:
            out.append(f"error: {type(error).__name__}: {error}")
    return out
```


## 6. Other code changes (diffs)

### `hypocurate/sources/normalize.py`

```diff
diff --git a/hypocurate/sources/normalize.py b/hypocurate/sources/normalize.py
index 1ce6e3f..6aa586c 100644
--- a/hypocurate/sources/normalize.py
+++ b/hypocurate/sources/normalize.py
@@ -120,6 +120,21 @@ def alloy_label(composition: dict[str, float]) -> str:
     return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))
 
 
+# The same-alloy rule (register entry 'same_alloy_rule', owner 2026-10-05): each element's
+# atomic percent rounded to this many decimals; two compositions are the same alloy when
+# their rounded compositions are identical. Used by the gap report's condition summaries
+# (step 5); the plan setting that applies it to analysis comes in step 6.
+SAME_ALLOY_DECIMALS = 1
+
+
+def same_alloy_key(composition: dict[str, float]) -> str:
+    """The same-alloy rule's key for a full-precision composition: elements in
+    alphabetical order, each with its rounded atomic percent. Equal keys mean the same
+    alloy under the rule; unlike `alloy_label`, the key is the rule itself."""
+    return " ".join(f"{e} {round(v, SAME_ALLOY_DECIMALS):.{SAME_ALLOY_DECIMALS}f}"
+                    for e, v in sorted(composition.items()))
+
+
 _DOI_WRAPPER = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
 _ASCII_UPPER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
```

### `hypocurate/sources/versions.py`

```diff
diff --git a/hypocurate/sources/versions.py b/hypocurate/sources/versions.py
index 2b2b5a1..bfd0861 100644
--- a/hypocurate/sources/versions.py
+++ b/hypocurate/sources/versions.py
@@ -146,6 +146,10 @@ def read_definition_files(definition: SourceDefinition, data_dir: Path = DATA_DI
                           manifest: dict | None = None) -> tuple[dict[str, bytes], date]:
     """Reads a source's data files from disk, checks each against its manifest entry
     (SHA-256 and size) and returns {stored path: bytes} and the date obtained."""
+    from hypocurate.access import file_guard  # here, not at the top: the access layer imports this module
+    if file_guard.installed():
+        raise RegistrationError("source registration reads data/ and cannot run in a guarded pipeline "
+                                "process (step 5)")
     manifest = manifest if manifest is not None else load_manifest(data_dir / "manifest.json")
     listed, obtained = _manifest_files(definition, manifest)
     source_dir = safe_path_within(data_dir, definition.directory)
```

### `hypocurate/sources/connection.py`

```diff
diff --git a/hypocurate/sources/connection.py b/hypocurate/sources/connection.py
index 2742cf9..50571dc 100644
--- a/hypocurate/sources/connection.py
+++ b/hypocurate/sources/connection.py
@@ -2,7 +2,11 @@
 
 Loads the latest sealed version of a source, reads it with its adapter, and returns the
 first few records in the common record format, with counts. It only reads: the
-transaction is READ ONLY, so it cannot write to the database."""
+transaction is READ ONLY, so it cannot write to the database.
+
+It also reports, per category field, how many values are not in the access layer's
+vocabularies (counts only, never the values), so a source with unfamiliar labels is noticed
+(owner, 2026-10-05). Adding a value to a vocabulary is a register change."""
 from __future__ import annotations
 
 from collections import Counter
@@ -10,6 +14,7 @@ from dataclasses import dataclass
 
 from sqlalchemy import Engine, text
 
+from hypocurate.access import vocabulary
 from hypocurate.sources import adapters
 from hypocurate.sources.record import CommonRecord
 from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
@@ -25,12 +30,14 @@ class ConnectionReport:
     blank_rows: int
     status_counts: dict[str, int]  # harmonized values by status, over all records read
     sample: tuple[CommonRecord, ...]
+    unrecognized: dict[str, int]  # per category field, values outside its vocabulary (counts only)
 
     def to_json(self) -> dict:
         return {
             "source_key": self.source_key, "version_id": self.version_id, "version_label": self.version_label,
             "fingerprint": self.fingerprint, "records_read": self.records_read, "blank_rows": self.blank_rows,
-            "status_counts": self.status_counts, "sample": [r.to_json() for r in self.sample],
+            "status_counts": self.status_counts, "unrecognized": self.unrecognized,
+            "sample": [r.to_json() for r in self.sample],
         }
 
 
@@ -43,8 +50,11 @@ def test_connection(engine: Engine, key: str, n: int = 5) -> ConnectionReport:
         conn.rollback()
     result = adapters.read(version)
     counts = Counter(v.status for r in result.records for v in r.harmonized.values())
+    unrecognized = vocabulary.unrecognized_counts(
+        (f, r.harmonized[f].value) for r in result.records for f in vocabulary.CATEGORY_FIELDS
+        if r.harmonized[f].status in ("converted", "assigned"))
     return ConnectionReport(key, version.id, version.label, version.fingerprint, len(result.records),
-                            len(result.blank_rows), dict(sorted(counts.items())), result.records[:n])
+                            len(result.blank_rows), dict(sorted(counts.items())), result.records[:n], unrecognized)
 
 
 test_connection.__test__ = False  # a function, not a pytest test
```

### `scripts/check_runtime_image.py`

```diff
diff --git a/scripts/check_runtime_image.py b/scripts/check_runtime_image.py
index f4f02a5..6a5b4dd 100644
--- a/scripts/check_runtime_image.py
+++ b/scripts/check_runtime_image.py
@@ -28,7 +28,12 @@ REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.jso
             "data/controlled_duplicates/extract.csv",
             # Step 4b: the assumptions register and its page.
             "hypocurate/assumptions.json", "hypocurate/assumptions.py",
-            "hypocurate/web/templates/assumptions.html"]
+            "hypocurate/web/templates/assumptions.html",
+            # Step 5: the access layer and the guarded process that pipeline runs use.
+            "hypocurate/access/allowlist.py", "hypocurate/access/layer.py", "hypocurate/access/fields.py",
+            "hypocurate/access/stage.py", "hypocurate/access/inputs.py", "hypocurate/access/file_guard.py",
+            "hypocurate/access/guarded.py", "hypocurate/access/guard_probe.py", "hypocurate/access/vocabulary.py",
+            "hypocurate/access/context.py", "hypocurate/access/dispatch.py"]
 FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
 FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")
```

### `CLAUDE.md`

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index d3fa37c..dc4b0ce 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -44,6 +44,11 @@ The full specification is `docs/PRD_sprint1.md`. Read the relevant section befor
 11. **Per-run calibration (PRD 5.10) is a flag, not a gate.** When inference cannot run, show "calibration unavailable" with the reason. Software correctness (pass/fail against an independent reference) is separate from calibration (a reported finding).
 12. **Every model call is recorded** with tokens and actual cost (`model_call`). Spending caps: $2 per run, $50 per month.
 13. **Wording:** outcomes are always stated "in the sources searched". Never write that data "do not exist".
+14. **Nothing a model controls ever receives SQL, a database connection or a file path.** Agents get data only as text built from an access object that the trusted dispatcher (`hypocurate.access.dispatch.bind`) bound to a run, role, stage and source. No code gives an agent a tool that runs SQL, opens files or executes code.
+
+## Threat model (owner, 2026-10-05)
+
+The access layer and its tests guard against **our own code** leaking data to a model. In sprint 1 agents are language models that return text only: they never execute code and never receive SQL or file tools. Only trusted, reviewed code runs, and a trusted dispatcher binds each agent call to a run, role, stage and source. The access layer is not a boundary against hostile code running in the same process, and the file guard is a tripwire against accidental file access, not a sandbox. The only construction-level guarantee about answer material is that the deployed image contains no `tests/` or `docs/`. Agents that execute code are in the backlog, with operating-system isolation as a precondition. Do not claim more than this anywhere.
 
 ## Environment
```


## 7. The assumptions register: diff of `hypocurate/assumptions.json`

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index ffd104d..49dcbc8 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -166,7 +166,15 @@
     },
     "sensitivity": "The same rule with a rounding step of 1 at.%.",
     "applied": {
-      "status": "not_yet",
+      "status": "partly",
+      "settings": [
+        {
+          "ref": "python:hypocurate.sources.normalize:SAME_ALLOY_DECIMALS",
+          "equals": 1
+        }
+      ],
+      "done": "The gap report's condition summaries group records by alloy under this rule (normalize.same_alloy_key, step 5).",
+      "pending": "The plan setting that applies it to the analysis, eligibility and duplicate matching.",
       "step": 6,
       "note": "The adapters give the full-precision composition; the display label (normalize.alloy_label) is not this rule."
     },
@@ -183,7 +191,10 @@
       "Ties follow the reference script's rounding (Python round on the computed percentage) unless step 6 states otherwise.",
       "Possible improvement for step 6, not a decision: a tolerance-based grouping, which would need a stated rule for chains and the owner's approval."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_access_layer.py::test_condition_summaries_are_ranges_and_counts_of_conditions_only",
+      "tests/test_access_layer.py::test_condition_summaries_group_alloys_by_the_same_alloy_rule"
+    ]
   },
   {
     "key": "fixed_minimums",
@@ -275,28 +286,31 @@
       }
     ],
     "notes": [
-      "Which records are compared is the open decision 'conflict_pairing_rule' (step 6)."
+      "Which records are compared is decided by entry 'conflict_pairing_rule' (owner, 2026-10-05): different sources, same paper, alloy, grain size and test conditions."
     ],
     "tests": []
   },
   {
     "key": "conflict_pairing_rule",
     "name": "Which records are compared for a conflict",
-    "state": "open",
-    "statement": "Which pairs of records are compared for the 'values disagree' flag. Two records from the same paper with the same alloy, grain size and conditions in one source may be repeat specimens, which are separate measurements. A conflict is two records that claim to be the same measurement and disagree, which mainly arises between different sources reporting the same paper.",
-    "value": null,
+    "state": "in_force",
+    "statement": "Duplicates and conflicts are looked for only between records from different sources that cite the same paper with the same alloy, grain size and test conditions. Rows within one source are always separate measurements (repeat specimens).",
+    "value": {
+      "text": "different sources citing the same paper, with the same alloy, grain size and test conditions; rows within one source are separate measurements",
+      "unit": null
+    },
     "category": "data_handling",
     "affects": "Whether legitimate repeat specimens are flagged as conflicts; the conflict flags of every run.",
-    "reason": "The 2% tolerance (entry 'values_disagree_tolerance') needs a pairing rule, and the owner did not state one as final.",
+    "reason": "Repeat specimens reported by one source are legitimate separate measurements; a conflict or duplicate is two records that claim to be the same measurement, which arises when different sources report the same paper.",
     "evidence": [
       "Owner's answer on decision f, 2026-10-05 (step 4b summary).",
       "Step 1 summary: MPEA papers with the same alloy and grain size at different values, which duplicate detection must not merge.",
-      "Step 4b review, finding 4."
+      "Step 4b review, finding 4.",
+      "Owner's decision, 2026-10-05 (step 5 instructions)."
     ],
-    "decided": null,
-    "pending": {
-      "by": "owner",
-      "before_step": 6
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -310,9 +324,18 @@
       "note": null
     },
     "tests": [],
-    "history": [],
+    "history": [
+      {
+        "value": "open decision: which pairs of records are compared for the 'values disagree' flag (repeat specimens versus conflicting reports)",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Open entry added after the step 4b review, finding 4."
+      }
+    ],
     "notes": [
-      "Related: entry 'observation_unit' (what one source row represents)."
+      "Known weakness: a source that repeats its own row by mistake is not caught, because rows within one source are never compared.",
+      "Not reviewed by an expert.",
+      "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance)."
     ]
   },
   {
@@ -1967,7 +1990,7 @@
     "tests": [],
     "history": [],
     "notes": [
-      "Connects to the open decision 'conflict_pairing_rule'."
+      "Connects to entry 'conflict_pairing_rule' (decided 2026-10-05): rows within one source are always separate measurements."
     ]
   },
   {
@@ -2816,5 +2839,957 @@
     "history": [],
     "notes": [],
     "tests": []
+  },
+  {
+    "key": "access_allow_lists",
+    "name": "Allowed fields per role and stage",
+    "state": "in_force",
+    "statement": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Curator and the Critic between the lock and the freeze; the Analyst after the freeze, or after a run ended without a freeze (gap report); the Commentator after completion. On a run completed with no dataset frozen, the Commentator receives only what the Analyst received for the gap report, plus the Analyst's gap report and the run's outcome: no outcome values and no row-level records. Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope). Every read and every refusal is logged.",
+    "value": {
+      "text": "the table in hypocurate/access/allowlist.py (ALLOWED)",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Everything an agent can receive (PRD 4), from step 8 on.",
+    "reason": "PRD 4 lists what each role can see in general terms; the fields the PRD does not assign (the plan for the Critic, tag lists, coverage, handovers, cost, eligibility decisions, the domain for the Curator) were assigned in the step 5 plan.",
+    "evidence": [
+      "PRD 4; step 5 plan approved by the owner, 2026-10-05, with additions A (single-run scope) and B (named source fields).",
+      "Owner's change before the step 5 review, 2026-10-05: the Commentator on a run with no dataset frozen."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:ALLOWED"
+        },
+        {
+          "ref": "python:hypocurate.access.allowlist:ROLES",
+          "equals": [
+            "planner",
+            "curator",
+            "critic",
+            "analyst",
+            "commentator"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.allowlist:STAGES",
+          "equals": [
+            "none",
+            "before_lock",
+            "curation",
+            "analysis",
+            "closed_without_freeze",
+            "final",
+            "final_without_freeze"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [
+      {
+        "value": "On a completed run, the Commentator received the Analyst's post-freeze fields (including every stored record with its outcome values) whether or not a dataset was frozen, plus the gap-report summaries.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 first build; changed by the owner before the review."
+      }
+    ],
+    "notes": [
+      "Two fields are reference lists, not run data: the confirmed domain and the approved tag values (without the run that proposed them)."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_the_allow_list_matches_the_owners_table",
+      "tests/test_access_layer.py::test_each_role_gets_exactly_its_fields_and_every_refusal_is_logged",
+      "tests/test_access_projected.py::test_nothing_from_another_run_reaches_any_role",
+      "tests/test_access_layer.py::test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome",
+      "tests/test_access_projected.py::test_no_projected_planted_value_in_the_commentators_input_without_a_freeze"
+    ]
+  },
+  {
+    "key": "outcome_fields_withheld",
+    "name": "Which fields count as outcomes",
+    "state": "in_force",
+    "statement": "Yield strength, its spread, tensile strength, hardness and its spread are all treated as outcomes wherever outcomes are withheld: their values never reach the Planner, the Critic or the gap report, and no count is broken down by them. The Planner does not know before the lock which one its plan will choose.",
+    "value": {
+      "text": "yield_strength, yield_strength_sd, ultimate_tensile_strength, hardness, hardness_sd",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The Planner's record counts, the Critic's record metadata and the gap report's input.",
+    "reason": "Before the rules lock the outcome variable is not chosen yet, so every property that could be one is withheld.",
+    "evidence": [
+      "Step 5 plan, point 7 (approved by the owner, 2026-10-05)."
+    ],
+    "decided": {
+      "by": "step 5 (owner's approval of the plan)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:OUTCOME_FIELDS",
+          "equals": [
+            "hardness",
+            "hardness_sd",
+            "ultimate_tensile_strength",
+            "yield_strength",
+            "yield_strength_sd"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_layer.py::test_record_counts_are_counts_from_the_sealed_source",
+      "tests/test_access_projected.py::test_no_projected_planted_value_in_the_planners_complete_input"
+    ]
+  },
+  {
+    "key": "critic_metadata_without_numbers",
+    "name": "What the Critic sees about records",
+    "state": "in_force",
+    "statement": "The Critic sees source descriptions, never source content. Per record: id, source, item index, kind, alloy label (derived by code from the composition) and composition, DOI (DOI syntax only, else 'unrecognized'), each field's status, and the category values (test type, temperature band, phase class, microstructure, processing method) from their vocabularies, else 'unrecognized'. No measured number of any field, no paper title, no origin key. Flags: kind and category from their vocabularies, and record ids; never the numbers compared.",
+    "value": {
+      "text": "metadata, statuses and vocabulary categories; no measured numbers, no titles, no origin keys",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The Critic's classification of flags (step 8).",
+    "reason": "PRD 4: the Critic is told the kind of flag, never the numbers compared; and the source files contain the outcome values.",
+    "evidence": [
+      "Owner's answer to step 5 question 1, 2026-10-05.",
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:CATEGORY_FIELDS",
+          "equals": [
+            "test_type",
+            "test_temperature_band",
+            "phase_class",
+            "microstructure",
+            "processing_method"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [
+      {
+        "value": "The Critic sees source descriptions, never source content. Per record: id, source, origin key, alloy label and composition, paper reference and DOI, each field's status, and the category values (test type, temperature band, phase class, microstructure, processing method). No measured number of any field, not grain size and not temperature. Flags: kind, category and record ids, never the numbers compared.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 first build; changed after the second-model review."
+      }
+    ],
+    "notes": [
+      "Category values and paper references are the source's text, shown as the source gives them."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_record_metadata_carries_no_number_but_identity_and_composition",
+      "tests/test_access_layer.py::test_flags_kind_has_no_numbers",
+      "tests/test_access_projected.py::test_no_projected_planted_value_in_the_critics_complete_input",
+      "tests/test_access_dispatch.py::test_vocabularies_mark_what_they_do_not_know"
+    ]
+  },
+  {
+    "key": "gap_report_condition_summaries",
+    "name": "What the gap report's Analyst sees",
+    "state": "in_force",
+    "statement": "When a run ends with no dataset frozen, the Analyst gets everything except outcomes, plus summaries computed by code of the non-outcome conditions the stored records cover: per alloy (same-alloy rule) and overall, the count and the minimum and maximum of grain size and of test temperature, and the counts by test type and by phase. Never a row-level value, an outcome value or a statistic derived from outcomes.",
+    "value": {
+      "text": "counts and ranges of grain size and test temperature; counts by test type and phase",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The gap report of an insufficient run.",
+    "reason": "PRD 3 step 8 has the Analyst write the gap report, while PRD 4 and 5.6 show outcome values only after a freeze, which an insufficient run never has.",
+    "evidence": [
+      "Owner's answer to step 5 question 2, 2026-10-05."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:CONDITION_RANGE_FIELDS",
+          "equals": [
+            "grain_size",
+            "test_temperature"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.allowlist:CONDITION_COUNT_FIELDS",
+          "equals": [
+            "test_type",
+            "phase_class"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "On a completed run with no dataset frozen, the Commentator receives the same input (entry 'access_allow_lists')."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_condition_summaries_are_ranges_and_counts_of_conditions_only",
+      "tests/test_access_projected.py::test_no_projected_planted_value_in_the_gap_report_input",
+      "tests/test_access_layer.py::test_ending_without_a_freeze_opens_only_the_gap_report_input"
+    ]
+  },
+  {
+    "key": "source_meta_fields",
+    "name": "What a role sees about a source",
+    "state": "in_force",
+    "statement": "A source is described by a fixed set of named plain fields: key; name, licence and fields available from the code's source definitions (SOURCES); source type, kind of data and grouping unit from the sealed version the run recorded. Nothing from the mutable source registry (address, edited name, licence, properties or settings) reaches a role; editing the registry after dispatch changes nothing for that run.",
+    "value": {
+      "text": "key; name, licence, fields available (code); type, kind, grouping unit (sealed version)",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The source descriptions every role receives.",
+    "reason": "Free text could carry anything, including an outcome value.",
+    "evidence": [
+      "Owner's addition B at the approval of the step 5 plan, 2026-10-05.",
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:SOURCE_META_FIELDS",
+          "equals": [
+            "key",
+            "name",
+            "source_type",
+            "data_kind",
+            "licence",
+            "grouping_unit",
+            "fields_available"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [
+      {
+        "value": "A source is described by a fixed set of named plain fields: key, name, type, kind of data, licence, grouping unit and fields available. Free text such as the address, the version label or notes never reaches the Planner or the Critic.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 first build; changed after the second-model review."
+      }
+    ],
+    "notes": [
+      "Name and licence are text; they are set from the code's source definitions (SOURCES in hypocurate/sources/versions.py), not from source content."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_sources_meta_is_exactly_the_named_plain_fields",
+      "tests/test_access_projected.py::test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic",
+      "tests/test_access_layer.py::test_sources_meta_comes_from_the_code_and_the_sealed_version_not_the_registry"
+    ]
+  },
+  {
+    "key": "plan_named_parts",
+    "name": "The plan's schema",
+    "state": "in_force",
+    "statement": "A plan's content is read only through PLAN_SCHEMA, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped. Power assumptions likewise through POWER_SCHEMA, and the sensitivity keys through their vocabulary. Defined in step 5 (owner, 2026-10-05); the plan model of step 6 must follow it.",
+    "value": {
+      "text": "PLAN_SCHEMA (nested, named keys and vocabulary leaves)",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "What any role receives of a plan; the plan model (step 6) stores its content under these names.",
+    "reason": "Allowed fields, not blocked fields (PRD 4).",
+    "evidence": [
+      "PRD 5.1; step 5 plan, point 9 (approved by the owner, 2026-10-05).",
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:PLAN_SCHEMA"
+        },
+        {
+          "ref": "python:hypocurate.access.allowlist:POWER_SCHEMA"
+        }
+      ],
+      "note": null
+    },
+    "history": [
+      {
+        "value": "A plan's content is read only under its named parts (PRD 5.1): claim, hypothesis version, variables, scope, model, sufficiency, fields to extract, exclusion rules, eligibility rules, verdict statement, sensitivity analyses. Any other key is withheld from every role. The list of fields to extract keeps only names of the common fields.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 first build; changed after the second-model review."
+      }
+    ],
+    "notes": [
+      "Step 6 must store the plan's content in this schema; a change to the schema is a register change needing the owner's approval."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_the_plan_is_projected_by_its_named_parts",
+      "tests/test_access_layer.py::test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim"
+    ]
+  },
+  {
+    "key": "access_stage_from_database",
+    "name": "A role's stage is the run's, read from the database",
+    "state": "in_force",
+    "statement": "Every access call reads the run's stage from the database inside its own transaction, after locking the run, and refuses when the role's declared stage differs. An access object built for one stage stops working when the run passes a checkpoint. A completed run is at stage 'final' if a dataset was frozen, otherwise at 'final_without_freeze'.",
+    "value": {
+      "text": "read on every call",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "When each role's access opens and closes (rules lock, freeze, end without freeze, completion).",
+    "reason": "A stage taken from the caller could be wrong or stale.",
+    "evidence": [
+      "Step 5 plan (approved by the owner, 2026-10-05)."
+    ],
+    "decided": {
+      "by": "step 5 (owner's approval of the plan)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.stage:actual_stage"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_layer.py::test_a_declared_stage_is_checked_against_the_database",
+      "tests/test_access_layer.py::test_the_rules_lock_changes_what_each_role_may_see",
+      "tests/test_access_layer.py::test_the_dataset_freeze_changes_what_each_role_may_see",
+      "tests/test_access_layer.py::test_completion_without_a_freeze_moves_access_to_the_commentator_only",
+      "tests/test_access_layer.py::test_completion_after_a_freeze_moves_access_to_the_commentator_only"
+    ]
+  },
+  {
+    "key": "access_lock_timeout",
+    "name": "How long an access call waits for a run's lock",
+    "state": "in_force",
+    "statement": "An access call takes the run's lock first (hc_write_lock), and waits at most 5 seconds for it; then it fails with an error instead of hanging. Code must never call the access layer while holding the same run's lock.",
+    "value": {
+      "text": "5000",
+      "unit": "ms"
+    },
+    "category": "operational",
+    "affects": "Access calls while another transaction writes to the run.",
+    "reason": "The audit row is a write to the run, so the locking protocol applies; a caller that holds the run's lock and calls the access layer would otherwise wait on itself.",
+    "evidence": [
+      "Step 5 plan, point 8 (approved by the owner, 2026-10-05)."
+    ],
+    "decided": {
+      "by": "step 5 (owner's approval of the plan)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.layer:ACCESS_LOCK_TIMEOUT_MS",
+          "equals": 5000
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_layer.py::test_an_access_call_takes_the_run_lock_first_and_times_out_instead_of_hanging",
+      "tests/test_access_layer.py::test_an_access_call_waits_for_a_writer_holding_the_run_lock",
+      "tests/test_access_layer.py::test_every_access_call_runs_in_run_transaction"
+    ]
+  },
+  {
+    "key": "no_experiment_relaxation",
+    "name": "No relaxation of the access contract",
+    "state": "in_force",
+    "statement": "No experiment flag relaxes the access contract in sprint 1: the lists are the same whatever the run's experiment flags say.",
+    "value": {
+      "text": "none",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every run.",
+    "reason": "PRD 4 allows a recorded experiment flag to relax the contract; it is not needed in sprint 1, so it is not built (backlog).",
+    "evidence": [
+      "Step 5 plan, point 5 (approved by the owner, 2026-10-05); PRD 4."
+    ],
+    "decided": {
+      "by": "step 5 (owner's approval of the plan)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:ALLOWED"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_layer.py::test_experiment_flags_relax_nothing"
+    ]
+  },
+  {
+    "key": "pipeline_file_guard",
+    "name": "Approved input files of pipeline code",
+    "state": "in_force",
+    "statement": "A tripwire against accidental file access by trusted pipeline code, not a sandbox. Each pipeline run executes in a fresh process (python -m hypocurate.access.guarded) where a Python audit hook refuses reading or listing anything outside the Python installation and the package's code, writing outside a private scratch directory, relative paths, other programs and new native libraries; each refusal is logged (audit log as a failure, or the process log). It does not stop code that tries to get around it: Python warns that audit hooks are unsuitable for a sandbox, and open descriptors, the guard's own state, preloaded ctypes (direct memory access), sockets and the database are not restricted. The only construction-level guarantee is that the deployed image contains no tests/ or docs/.",
+    "value": {
+      "text": "tripwire: reads limited to the Python installation and package code; writes to a private scratch directory",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every pipeline run (the command line's run command, step 8; the worker, step 9).",
+    "reason": "Answer material and review documents should not be reached by accident (step 1 open item 4). The owner's first instruction asked for 'unreachable by construction'; after the step 5 review the owner scoped this to a tripwire against our own mistakes, with the deployed image (no tests/, no docs/) as the only construction-level guarantee.",
+    "evidence": [
+      "Step 1 summary, open item 4; step 5 plan and owner's addition C, 2026-10-05.",
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.file_guard:GUARDED_MAIN",
+          "equals": "hypocurate.access.guarded"
+        },
+        {
+          "ref": "python:hypocurate.access.file_guard:SCRATCH_PREFIX",
+          "equals": "hc-run-"
+        },
+        {
+          "ref": "python:hypocurate.access.guarded:PRELOADED",
+          "equals": [
+            "psycopg"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [
+      {
+        "value": "A pipeline run executes in a fresh process (python -m hypocurate.access.guarded) under an irreversible guard: it may read only the Python installation and the package's code, and write only in a private scratch directory (an empty, 0700 hc-run-* directory in the system temporary directory, removed afterwards). tests/, docs/, data/ and the repository root cannot be read or listed; other programs and native code through ctypes are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. The database driver is imported before the guard is installed.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 first build; changed after the second-model review."
+      }
+    ],
+    "notes": [
+      "Python documentation, sys.addaudithook and PEP 578: audit hooks are not suitable for implementing a sandbox.",
+      "Sufficient under the threat model (entry 'threat_model'): only trusted code runs; agents return text only.",
+      "A library that imports ctypes after the guard is installed is refused; such a library (for example the plotting library, step 7) must be added to PRELOADED with the owner's approval."
+    ],
+    "tests": [
+      "tests/test_access_files.py::test_answers_reviews_data_and_the_repository_root_cannot_be_read",
+      "tests/test_access_files.py::test_writes_outside_the_scratch_directory_are_refused",
+      "tests/test_access_files.py::test_templates_database_and_certificates_work_under_the_guard",
+      "tests/test_access_files.py::test_source_registration_cannot_run_under_the_guard",
+      "tests/test_access_files.py::test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else",
+      "tests/test_access_layer.py::test_the_guard_is_installed_in_one_place",
+      "tests/test_access_files.py::test_preloaded_ctypes_still_works_a_documented_limit",
+      "tests/test_access_dispatch.py::test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log",
+      "tests/test_check_runtime_image.py::test_clean_image_passes"
+    ]
+  },
+  {
+    "key": "threat_model",
+    "name": "Threat model of the access layer",
+    "state": "in_force",
+    "statement": "The access layer and its tests guard against our own code leaking data to a model. In sprint 1 agents are language models that return text only: they never execute code and never receive SQL, a database connection, a file path or other tools. Only trusted, reviewed code runs, and a trusted dispatcher binds each agent call to a run, role, stage and source. The access layer is not a boundary against hostile code in the same process. Agents that execute code are in the backlog, with operating-system isolation as a precondition.",
+    "value": {
+      "text": "own mistakes; text-only agents; trusted code",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "What the access layer and the file guard claim, and what step 8 may give an agent.",
+    "reason": "The step 5 review showed that an in-process guard cannot contain code that tries to get around it; the owner scoped the guarantees to our own mistakes.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "file:CLAUDE.md:Nothing a model controls ever receives SQL, a database connection or a file path"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "The owner's earlier instruction 'unreachable by construction' overreached; every claim that followed from it is corrected (step 5 summary)."
+    ],
+    "tests": [
+      "tests/test_access_dispatch.py::test_an_access_object_has_no_public_constructor_and_cannot_be_changed",
+      "tests/test_access_dispatch.py::test_bind_reads_the_role_from_the_runs_agent_settings_and_the_stage_from_the_database"
+    ]
+  },
+  {
+    "key": "access_context_dispatcher",
+    "name": "Access objects come only from the dispatcher",
+    "state": "in_force",
+    "statement": "An access object is created only by hypocurate.access.dispatch.bind(run, agent setting, source), around an immutable context captured once: the role is read from the run's recorded agent settings, the stage from the database, and a Curator's source must be one of the run's run_source rows. There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
+    "value": {
+      "text": "dispatch.bind only",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every agent read (steps 8 and 9).",
+    "reason": "Review finding 2: caller-chosen, mutable role, run, stage and source could be misused by our own code.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.dispatch:bind"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_dispatch.py::test_bind_refuses_a_setting_or_source_the_run_did_not_record",
+      "tests/test_access_dispatch.py::test_an_access_object_has_no_public_constructor_and_cannot_be_changed"
+    ]
+  },
+  {
+    "key": "access_logging",
+    "name": "What the audit log records, and its fallback",
+    "state": "in_force",
+    "statement": "Every read, policy denial and access failure is logged: detail.result is 'allowed', 'denied' (a policy refusal, with a fixed code) or 'failed' (unknown run, lock timeout, reader error, database error, file-guard refusal). Only validated, bounded strings are logged; anything not one of ours is 'invalid' with its length. A role's whole input is read and logged in one transaction. If a failure cannot be written to the database, it goes to the process log (logger hypocurate.access); durable logging in the database is not unconditional.",
+    "value": {
+      "text": "allowed / denied / failed; process log as fallback",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The audit log of every run (PRD 14.2).",
+    "reason": "Review finding 5.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.layer:FAILURES",
+          "equals": [
+            "unknown_run",
+            "lock_timeout",
+            "reader_error",
+            "database_error",
+            "file_guard"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.layer:DENIALS"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_dispatch.py::test_a_readers_error_is_a_logged_failure",
+      "tests/test_access_dispatch.py::test_an_unknown_run_is_a_logged_failure",
+      "tests/test_access_dispatch.py::test_when_the_database_is_unavailable_the_process_log_is_the_fallback",
+      "tests/test_access_dispatch.py::test_role_input_is_never_silently_empty",
+      "tests/test_access_dispatch.py::test_only_validated_bounded_strings_are_logged",
+      "tests/test_access_dispatch.py::test_a_roles_whole_input_is_read_in_one_transaction"
+    ]
+  },
+  {
+    "key": "audit_failure_rows_without_run_lock",
+    "name": "Failure rows: a named exception to the locking protocol",
+    "state": "in_force",
+    "statement": "Audit rows for access failures (unknown run, lock timeout, reader or database error, file-guard refusal) are written in their own short transaction without hc_write_lock: there is no run to lock, or the lock is what failed. An audit_log insert takes only a key-share lock on the run, which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an unknown run, run_id is NULL and the requested id is in the detail.",
+    "value": {
+      "text": "failure rows without hc_write_lock",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "The locking protocol of step 3 (every other write path still calls hc_write_lock first).",
+    "reason": "A failure must be logged even when the run's lock cannot be taken.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.layer:log_failure"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "Owner's answer to the fix-plan question 1, 2026-10-05: option (a)."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_an_access_call_takes_the_run_lock_first_and_times_out_instead_of_hanging",
+      "tests/test_access_dispatch.py::test_bind_logs_an_unknown_run_as_a_failure_with_no_run"
+    ]
+  },
+  {
+    "key": "category_vocabularies",
+    "name": "Vocabularies of category values in blinded views",
+    "state": "in_force",
+    "statement": "Category values shown to the Planner, the Critic and in gap reports come from fixed vocabularies; any other value is shown as 'unrecognized' (the stored value is unchanged). Test type: tension, compression. Temperature band: room temperature, cryogenic, elevated. Phase class: FCC, BCC, other. Microstructure: '+'-joined tokens from FCC, BCC, B2, HCP, L12, Laves, Sec., Other. Processing method: CAST, WROUGHT, ANNEAL, POWDER, OTHER. Unrecognized values are counted per field (never shown) in test connection and in the run's coverage. Adding a value is a register change needing the owner's approval.",
+    "value": {
+      "text": "five vocabularies; marker 'unrecognized'",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "What source text the Planner, the Critic and the gap report can receive.",
+    "reason": "Review finding 3: free text in category fields could carry outcome values. Built from the frozen sources' actual values (no value of either source is unrecognized).",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.vocabulary:TEST_TYPES",
+          "equals": [
+            "compression",
+            "tension"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:TEMPERATURE_BANDS",
+          "equals": [
+            "cryogenic",
+            "elevated",
+            "room temperature"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:PHASE_CLASSES",
+          "equals": [
+            "BCC",
+            "FCC",
+            "other"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:MICROSTRUCTURE_TOKENS",
+          "equals": [
+            "B2",
+            "BCC",
+            "FCC",
+            "HCP",
+            "L12",
+            "Laves",
+            "Other",
+            "Sec."
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:PROCESSING_METHODS",
+          "equals": [
+            "ANNEAL",
+            "CAST",
+            "OTHER",
+            "POWDER",
+            "WROUGHT"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:UNRECOGNIZED",
+          "equals": "unrecognized"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "Owner's approval of the vocabularies and of the unrecognized counts, 2026-10-05."
+    ],
+    "tests": [
+      "tests/test_access_dispatch.py::test_vocabularies_mark_what_they_do_not_know",
+      "tests/test_access_dispatch.py::test_the_frozen_sources_have_no_unrecognized_category_value",
+      "tests/test_access_dispatch.py::test_unrecognized_values_are_counted_in_coverage_and_test_connection"
+    ]
+  },
+  {
+    "key": "code_vocabularies",
+    "name": "Vocabularies of codes our own code writes",
+    "state": "in_force",
+    "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 must write these codes. Adding one is a register change needing the owner's approval.",
+    "value": {
+      "text": "flag kinds, flag categories, eligibility rules, sensitivity keys",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Flags (step 6), eligibility decisions (step 6), sensitivity analyses (step 7) as roles see them.",
+    "reason": "Review finding 3: stored codes are text and could carry anything.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.vocabulary:FLAG_KINDS",
+          "equals": [
+            "exact_duplicate",
+            "invalid_value",
+            "model_recalled",
+            "out_of_scope",
+            "possible_duplicate",
+            "scope_not_confirmed",
+            "values_disagree"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:FLAG_CATEGORIES",
+          "equals": [
+            "differ beyond tolerance",
+            "identical values",
+            "outside scope",
+            "physically impossible",
+            "scope not confirmed",
+            "within tolerance"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:ELIGIBILITY_RULES",
+          "equals": [
+            "duplicate_counted_once",
+            "excluded_by_rule",
+            "in_scope",
+            "invalid_value",
+            "model_recalled",
+            "out_of_scope",
+            "scope_not_confirmed",
+            "single_grain_size"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:SENSITIVITY_KEYS",
+          "equals": [
+            "possible_duplicates_separate",
+            "removal_after_lock",
+            "same_alloy_1_at_pct",
+            "scope_not_confirmed_included",
+            "six_batches_as_groups",
+            "source_only_assignments",
+            "tension_and_compression"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_layer.py::test_flags_kind_has_no_numbers",
+      "tests/test_access_dispatch.py::test_the_gap_report_input_has_codes_not_failure_text"
+    ]
+  },
+  {
+    "key": "accepted_disclosures",
+    "name": "What the blinded views disclose by design",
+    "state": "in_force",
+    "statement": "The blinding of the Planner, the Critic, the gap report and the Commentator without a freeze is limited to: no outcome value is copied into their views from a stored outcome field, a value as reported, a flag's numbers, a stage's text, or text outside a vocabulary. They still disclose, by design: counts by field status; flag kinds and categories; condition summaries, which reveal an exact grain size or temperature when a group has one record; compositions and alloy labels; DOIs with DOI syntax (which may contain digits); text written or approved by people (the claim, approved tag values, source names and licences in code); numbers in the locked plan; the Analyst's gap report passed to the Commentator; timing and the existence of refusals. Timing is not protected.",
+    "value": {
+      "text": "the nine disclosures in ACCEPTED_DISCLOSURES",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The claim made for blinding (PRD 4) in every document.",
+    "reason": "Review finding 3 and its note on counts and timing: these follow from the approved contract; 'no row-level value can be inferred' would be false.",
+    "evidence": [
+      "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
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
+          "ref": "python:hypocurate.access.allowlist:ACCEPTED_DISCLOSURES"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_projected.py::test_no_projected_planted_value_in_the_critics_complete_input",
+      "tests/test_access_dispatch.py::test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure"
+    ]
   }
 ]
```

## 8. Tests: new files (full text)

### `tests/access_world.py`

```python
"""Test data for the access layer (step 5): runs at every stage, with distinctive outcome
values planted everywhere they are stored, and a second planted value in other runs.

PLANTED: the main run's outcome values. They are in its sealed source file (yield
strength, tensile strength, hardness, and a cell the adapter cannot read, so the value
also sits in a 'not a number' reason), in its stored records (harmonized, as reported,
nested), in a flag's compared numbers, in a Curator stage's output, reasoning and tool
calls, in a model setting's instruction, in a proposed (not approved) tag value, in the
source's free-text address and version label, and in an unnamed key of the plan.

OTHER: a different value in other runs: the original run of the narrower question (its
records, coefficient, stage outputs and commentary) and an earlier, failed run of the same
hypothesis version (its records and stage outputs).

Inside allowed fields (step 5 review, finding 3), PLANTED is also in: category cells
(microstructure, processing method, phase class), the paper title, the DOI, every kind of
plan leaf and the power assumptions, an eligibility rule, a failed source's failure text, a
flag's kind and category, and the source registry's licence and properties edited after
dispatch.

GAP_REPORT: the text of the Analyst's gap report, on runs that end with no dataset frozen.

DIRECTION: a token in the claim and in the plan's hypotheses and field list, for the
Curator test (the Curator is not told the direction of the claim).
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.sources import adapters
from hypocurate.sources.versions import load_sealed_version
from model_builder import FP, World

REPO = Path(__file__).resolve().parent.parent
MPEA_CSV = REPO / "data" / "sources" / "mpea" / "MPEA_dataset.csv"

PLANTED = {"yield_strength": 48213.579, "ultimate_tensile_strength": 57104.263, "hardness": 36912.847}
OTHER = 59324.681
DIRECTION = "ZQXDIR rises as grain size falls"
GAP_REPORT = "Insufficient in the sources searched: grain size is missing for most alloys (GAPTOKEN)."

YS, UTS, HV = "PROPERTY: YS (MPa)", "PROPERTY: UTS (MPa)", "PROPERTY: HV"
GS, TT, TYPE = "PROPERTY: grain size ($\\mu$m)", "PROPERTY: Test temperature ($^\\circ$C)", "PROPERTY: Type of test"
MICRO, PROCESS, PHASE = "PROPERTY: Microstructure", "PROPERTY: Processing method", "PROPERTY: BCC/FCC/other"
TITLE, DOI = "REFERENCE: title", "REFERENCE: doi"
ROLES = ("planner", "curator", "critic", "analyst", "commentator")


def mpea_rows(n: int) -> tuple[list[str], list[dict]]:
    """The MPEA header and the first n real rows that have a grain size and a yield strength."""
    with MPEA_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r[GS].strip() and r[YS].strip()][:n]
        return list(reader.fieldnames), rows


def planted_csv(value_ys=PLANTED["yield_strength"], value_uts=PLANTED["ultimate_tensile_strength"],
                value_hv=PLANTED["hardness"]) -> bytes:
    """An MPEA-layout file: four real rows, then rows carrying the planted values."""
    header, rows = mpea_rows(4)
    planted = []
    for i, base in enumerate(rows[:3]):
        r = dict(base)
        r[YS], r[UTS], r[HV] = repr(value_ys), repr(value_uts), repr(value_hv)
        r[TYPE], r[TT] = "T", "25.0"
        r[GS] = f"{12.5 + i}"
        planted.append(r)
    # Planted inside fields the blinded views do show: category cells, the title, the DOI.
    planted[0][MICRO] = f"FCC; yield strength {value_ys} MPa"
    planted[0][PROCESS] = f"CAST {value_ys}"
    planted[0][PHASE] = f"FCC {value_ys}"
    planted[0][TITLE] = f"Yield strength of {value_ys} MPa in CoCrNi"
    planted[0][DOI] = f"doi {value_ys}"
    unreadable = dict(rows[0])
    unreadable[YS] = f"{value_ys} MPa"  # the adapter keeps it as 'not a number: ...'
    planted.append(unreadable)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=header, lineterminator="\n")
    w.writeheader()
    w.writerows(rows + planted)
    return out.getvalue().encode("utf-8")


def sql(world: World, statement: str, **params):
    """Runs one statement in its own transaction; parameters named j_* are JSON."""
    stmt = text(statement).bindparams(*[bindparam(k, type_=JSONB) for k in params if k.startswith("j_")])
    with world.e.begin() as conn:
        return conn.execute(stmt, params)


def val(world: World, statement: str, **params):
    return sql(world, statement, **params).scalar()


@dataclass
class AccessWorld:
    w: World
    run: int  # the main run (a narrower question)
    original_run: int  # the run the narrower question came from
    earlier_run: int  # an earlier run of the same hypothesis version
    records: list[int] = field(default_factory=list)
    flags: list[int] = field(default_factory=list)
    settings: dict = field(default_factory=dict)  # role -> agent setting id recorded for the run


def add_planted_version(w: World, key="mpea", content: bytes | None = None, label="v-planted") -> int:
    v = w.new_version(key, label=label)
    w.add_file(v, f"{key}_planted.csv", content or planted_csv())
    w.seal(v)
    w.version[key] = v
    return v


def store_records(w: World, run: int, key="mpea") -> list[int]:
    """The adapter's records of the run's version, stored as step 6 will store them."""
    with w.e.begin() as conn:
        version = load_sealed_version(conn, w.version[key])
    ids = []
    for r in adapters.read(version).records:
        j = r.to_json()
        ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                          "kind, alloy, harmonized, reported, paper_reference, paper_doi) "
                          "VALUES (:r, :sv, :k, :ix, :kind, :a, :j_h, :j_rep, :pr, :pd) RETURNING id",
                       r=run, sv=w.version[key], k=j["source_item_key"], ix=j["item_index"], kind=j["kind"],
                       a=j["alloy"], j_h=j["harmonized"], j_rep=j["reported"], pr=j["paper_reference"],
                       pd=j["paper_doi"]))
    return ids


def store_value_records(w: World, run: int, value: float, n=3, key="mpea") -> list[int]:
    """Records whose outcome value is `value` (for runs other than the main one)."""
    ids = []
    for i in range(n):
        h = {"yield_strength": {"value": value, "unit": "MPa", "status": "converted"},
             "grain_size": {"value": 10.0 + i, "unit": "µm", "status": "converted"},
             "composition": {"value": {"Co": 50.0, "Ni": 50.0}, "unit": "at.%", "status": "converted"}}
        rep = {YS: {"column": YS, "text": f"{value}", "unit": "MPa"}}
        ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                          "kind, alloy, harmonized, reported) VALUES (:r, :sv, :k, 0, 'measured', 'Co50Ni50', :j_h, :j_rep) "
                          "RETURNING id", r=run, sv=w.version[key], k=f"other-{run}-{i}", j_h=h, j_rep=rep))
    return ids


def stage(w: World, run: int, name: str, role: str, payload: str, attempt=1) -> int:
    sid = w.stage(run, stage=name, role=role, attempt=attempt)
    sql(w, "UPDATE stage_result SET status = 'done', finished_at = now(), input = :j_i, output = :j_o, "
           "reasoning = :rs, tool_calls = :j_t WHERE id = :s",
        j_i={"text": payload}, j_o={"note": payload, "nested": {"values": [payload]}}, rs=payload,
        j_t={"calls": [{"result": payload}]}, s=sid)
    return sid


def lock(w: World, run: int) -> None:
    ys = PLANTED["yield_strength"]
    # Planted in every kind of plan leaf; the projection keeps only named keys, vocabulary
    # values (else the marker), numbers and field names.
    content = {"claim": DIRECTION,
               "variables": {"outcome": {"field": "yield_strength", "unit": f"{ys} MPa", "note": f"{ys}"},
                             "predictor": {"field": "grain_size", "unit": "µm", "transformation": f"x^{ys}"}},
               "model": {"name": "hall_petch_alloy_intercepts", "null": "k <= 0",
                         "alternative": f"k > 0 ({DIRECTION}, {ys})", "alpha": 0.05, "comment": f"{ys}"},
               "scope": {"phase_class": ["FCC", f"FCC {ys}"], "alloy_class": [f"{ys}"], "free": f"{ys}"},
               "fields_to_extract": ["grain_size", "yield_strength", "composition", DIRECTION, repr(ys), ys],
               "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1, "note": f"{ys}"},
                                   {"rule": f"ys above {ys}", "values": ["tension", f"{ys}"]}],
               "eligibility_rules": [{"flag_kind": "values_disagree", "rule": f"keep {ys}"}],
               "verdict_statement": f"supported if {ys}",
               "sensitivity_analyses": ["tension_and_compression", f"drop {ys}"],
               "unnamed_key": {"planted": ys}}
    sql(w, "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
           "min_groups, min_resid_df, power_assumptions) VALUES (:r, :j_c, :fp, 'fixed_minimum', 4, 1, 2, 1, :j_p)",
        r=run, j_c=content, fp=FP, j_p={"method": "information_only", "scatter": 60.0, "note": f"{ys}",
                                         "smallest_effect": f"{ys}"})


def original_run(w: World) -> int:
    """A completed 'partly sufficient' run with OTHER in its records, coefficient, stage
    outputs and commentary: the run a narrower question comes from."""
    rid = w.running(sources=("mpea",))
    w.lock(rid)
    w.search(rid, "mpea")
    recs = store_value_records(w, rid, OTHER)
    primary = w.analysis_set(rid)
    for rec in recs:
        w.decide(rid, rec)
        w.add(primary, rec)
    w.freeze(rid, len(recs))
    sql(w, "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
           "check1_passed, check2_passed, minimums_met, estimate) "
           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, true, false, false, :e)", r=rid, s=primary, e=OTHER)
    stage(w, rid, "analyst", "analyst", f"k = {OTHER}")
    w.complete(rid, "partly_sufficient")
    cid = stage(w, rid, "commentator", "commentator", f"the coefficient {OTHER}")
    sql(w, "INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
           "VALUES (:r, :s, 'written', :t2, 'model-b', 'all_match')", r=rid, s=cid, t2=f"k was {OTHER}")
    return rid


def build(engine, stage_name: str) -> AccessWorld:
    """A main run at `stage_name` (one of the access stages, or 'queued' / 'failed')."""
    w = World(engine)
    # B: planted values in the source's free text: the version label and the address.
    add_planted_version(w, label=f"label {PLANTED['yield_strength']}")
    sql(w, "UPDATE source SET address = :a WHERE key = 'mpea'", a=f"https://example.org/{PLANTED['yield_strength']}")
    settings = {"planner": val(w, "INSERT INTO agent_setting (role, version, instruction, model) "
                                  "VALUES ('planner', 1, :i, 'model-a') RETURNING id",
                               i=f"remember {PLANTED['yield_strength']}")}
    sql(w, "INSERT INTO tag_value (kind, value, status, decided_at) "
           "VALUES ('property', 'yield strength', 'approved', now())")
    sql(w, "INSERT INTO tag_value (kind, value, status) VALUES ('property', :v, 'proposed')",
        v=f"strength {PLANTED['yield_strength']}")
    original = original_run(w)
    h = w.hypothesis(narrower_of=original)
    vid = val(w, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                 "VALUES (:h, 1, :t, :d) RETURNING id", h=h, t=DIRECTION, d=w.domain["grain_size_strengthening"])
    for key in ("mpea", "tamu_fcc"):
        w.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=w.source[key])
    w.submit(vid)
    w.confirm(vid)
    w.dispatch_version(vid)
    earlier = w.running(vid=vid, sources=("mpea", "tamu_fcc"))
    w.lock(earlier)
    store_value_records(w, earlier, OTHER)
    stage(w, earlier, "curator", "curator", f"saw {OTHER}")
    w.fail(earlier)
    rid = w.run(vid=vid, sources=("mpea", "tamu_fcc"))
    world = AccessWorld(w, rid, original, earlier)
    # Dispatch records the agent setting of each role (the dispatcher reads roles from here).
    for role in ROLES:
        sid = settings.get(role) or val(w, "INSERT INTO agent_setting (role, version, instruction, model) "
                                           "VALUES (:o, 1, 'instruction', 'model-a') RETURNING id", o=role)
        settings[role] = sid
        sql(w, "INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :a)",
            r=rid, o=role, a=sid)
    world.settings = settings
    # Edits to the source registry after dispatch must change nothing for this run.
    sql(w, "UPDATE source SET licence = :l, properties_covered = :p WHERE key = 'mpea'",
        l=f"licence {PLANTED['yield_strength']}", p=["yield_strength", f"{PLANTED['yield_strength']}"])
    if stage_name == "queued":
        return world
    w.start(rid)
    if stage_name == "failed":
        w.fail(rid)
        return world
    if stage_name == "before_lock":
        return world
    lock(w, rid)
    w.search(rid, "mpea")
    w.search(rid, "tamu_fcc", status="failed", nothing_found="failed_search",
             reason=f"timed out after reading {PLANTED['yield_strength']}")
    world.records = store_records(w, rid)
    planted = [r for r in world.records
               if val(w, "SELECT harmonized->'yield_strength'->>'value' FROM record WHERE id = :r", r=r)
               == repr(PLANTED["yield_strength"])]
    fid = val(w, "INSERT INTO flag (run_id, kind, category, compared_values) "
                 "VALUES (:r, 'values_disagree', 'differ beyond tolerance', :j_cv) RETURNING id",
              r=rid, j_cv={"yield_strength": [PLANTED["yield_strength"], 47000.25], "text": f"{PLANTED['yield_strength']}"})
    for rec in planted[:2]:
        sql(w, "INSERT INTO flag_record VALUES (:f, :r)", f=fid, r=rec)
    world.flags.append(fid)
    world.flags.append(val(w, "INSERT INTO flag (run_id, kind, category) VALUES (:r, :k, :c) RETURNING id", r=rid,
                           k=f"kind {PLANTED['yield_strength']}", c=f"differ by {PLANTED['yield_strength']}"))
    stage(w, rid, "curator", "curator", f"extracted yield strength {PLANTED['yield_strength']} MPa")
    if stage_name == "curation":
        return world
    for i, rec in enumerate(world.records):
        w.decide(rid, rec, rule=f"kept at {PLANTED['yield_strength']}" if i == 0 else "in_scope")
    if stage_name in ("closed_without_freeze", "final_without_freeze"):
        sql(w, "INSERT INTO calibration_result (run_id, status, reason) VALUES (:r, 'unavailable', 'no_dataset_frozen')",
            r=rid)
        # The Analyst's gap report (it never saw an outcome value, so it holds none).
        stage(w, rid, "analyst", "analyst", GAP_REPORT)
        if stage_name == "final_without_freeze":
            w.complete(rid, "insufficient")
        return world
    if stage_name in ("analysis", "final"):
        primary = w.analysis_set(rid)
        for rec in world.records:
            w.add(primary, rec)
        w.freeze(rid, len(world.records))
        if stage_name == "final":
            w.complete(rid, "partly_sufficient")
        return world
    raise ValueError(stage_name)
```

### `tests/access_testing.py`

```python
"""Test-only construction of access objects (step 5 review, finding 2).

Outside the tests, an access object comes only from the trusted dispatcher
(`hypocurate.access.dispatch.bind`), which reads the role from the run's recorded agent
settings and the stage from the database. The tests also need contexts the dispatcher would
never produce (an unknown role, a stale or wrong stage, a source the run did not record), to
show that every read still refuses them. They use this helper, which no package code imports.
"""
from hypocurate.access.context import AccessContext
from hypocurate.access.layer import _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, Access


def access_for(engine, run_id, role, stage, source_key=None, lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
    return Access(engine, AccessContext(run_id, role, stage, source_key), lock_timeout_ms=lock_timeout_ms,
                  _trusted=_TRUSTED)
```

### `tests/test_access_layer.py`

```python
"""Step 5: the access layer (PRD 4; criterion 14.2).

Every role at every stage gets exactly the fields on its list; every other request raises
AccessDenied and leaves a denied row in the audit log that survives the rejection; what a
role may see changes at the rules lock and at the dataset freeze, tested on both sides;
every access call follows the locking protocol and runs in `run_transaction`.
"""
from __future__ import annotations

import ast
import json
import threading
import time
from pathlib import Path

import pytest
from sqlalchemy import text
import access_world as aw
from access_testing import access_for
from hypocurate.access import Access, AccessDenied, AccessFailed, allowlist, bind, layer, role_input
from hypocurate.access import vocabulary
from hypocurate.access.allowlist import ALLOWED, FIELDS, ROLES, SOURCE_META_FIELDS, STAGES, allowed
from hypocurate.access.fields import READERS
from hypocurate.db.engine import make_engine
from hypocurate.sources.record import HARMONIZED_FIELDS

REPO = Path(__file__).resolve().parent.parent

# World stage -> the access stage it is at.
WORLD_STAGES = {"queued": "none", "failed": "none", "before_lock": "before_lock", "curation": "curation",
                "analysis": "analysis", "closed_without_freeze": "closed_without_freeze", "final": "final",
                "final_without_freeze": "final_without_freeze"}


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    yield e
    e.dispose()


def access(engine, world, role, stage, **kw):
    if role == "curator" and "source_key" not in kw:
        kw["source_key"] = "mpea"
    return access_for(engine, world.run, role, stage, **kw)


def audit(engine, run=None):
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log "
                                 + ("WHERE run_id = :r " if run else "") + "ORDER BY id"), dict(r=run)).all()


# --- The allow-list itself --------------------------------------------------------------

def test_the_allow_list_matches_the_owners_table():
    """The table approved by the owner on 2026-10-05 (step 5 plan), field for field."""
    assert ROLES == ("planner", "curator", "critic", "analyst", "commentator")
    assert set(ALLOWED) == set(ROLES)
    assert {r: set(s) for r, s in ALLOWED.items()} == {
        "planner": {"before_lock"}, "curator": {"curation"}, "critic": {"curation"},
        "analyst": {"analysis", "closed_without_freeze"}, "commentator": {"final", "final_without_freeze"}}
    assert allowed("planner", "before_lock") == {"claim", "domain", "sources_meta", "tag_values", "record_counts"}
    assert allowed("curator", "curation") == {"plan_fields_to_extract", "sources_meta", "source_content"}
    assert allowed("critic", "curation") == {"sources_meta", "record_metadata", "flags_kind"}
    analysis = {"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full", "results",
                "coverage", "stage_outputs", "run_cost"}
    assert allowed("analyst", "analysis") == analysis
    gap = {"claim", "domain", "sources_meta", "plan", "coverage", "stored_record_counts", "decisions", "flags_kind",
           "condition_summaries"}
    assert allowed("analyst", "closed_without_freeze") == gap
    assert allowed("commentator", "final") == analysis
    # Owner, 2026-10-05 (before the step 5 review): with no dataset frozen, the Commentator gets
    # only the gap-report input, the Analyst's gap report and the run's outcome.
    assert allowed("commentator", "final_without_freeze") == gap | {"gap_report", "outcome"}
    for stage in STAGES:
        if stage != "before_lock":
            assert allowed("planner", stage) == frozenset()
    assert all(allowed(role, "none") == frozenset() for role in ROLES)


def test_every_listed_field_has_a_reader_and_a_description():
    listed = set().union(*(fs for stages in ALLOWED.values() for fs in stages.values()))
    assert listed <= set(READERS) == set(FIELDS)


def test_no_outcome_reaching_field_is_listed_for_the_planner_the_critic_or_the_gap_report():
    outcome_bearing = {"records_full", "flags_full", "results", "stage_outputs", "source_content", "plan"}
    for role, stage in (("planner", "before_lock"), ("critic", "curation")):
        assert not allowed(role, stage) & outcome_bearing, role
    assert not allowed("analyst", "closed_without_freeze") & (outcome_bearing - {"plan"})
    assert not allowed("commentator", "final_without_freeze") & (outcome_bearing - {"plan"})


# --- Every role, every stage, every field ------------------------------------------------

@pytest.mark.parametrize("world_stage", list(WORLD_STAGES))
def test_each_role_gets_exactly_its_fields_and_every_refusal_is_logged(engine, world_stage):
    world = aw.build(engine, world_stage)
    stage = WORLD_STAGES[world_stage]
    for role in ROLES:
        for field in sorted(FIELDS):
            before = len(audit(engine, world.run))
            a = access(engine, world, role, stage)
            if field in allowed(role, stage):
                a.get(field)
                rows = audit(engine, world.run)[before:]
                assert [(r.role, r.stage, r.function, r.allowed) for r in rows] == [(role, stage, field, True)]
                assert rows[0].detail == {"result": "allowed", "actual_stage": stage,
                                          **({"source": "mpea"} if role == "curator" else {})}
            else:
                with pytest.raises(AccessDenied):
                    a.get(field)
                rows = audit(engine, world.run)[before:]
                assert [(r.role, r.stage, r.function, r.allowed) for r in rows] == [(role, stage, field, False)]
                assert rows[0].detail["actual_stage"] == stage
                assert rows[0].detail["result"] == "denied" and rows[0].detail["code"] == "not_on_list"


@pytest.mark.parametrize("world_stage", ["queued", "failed"])
def test_queued_and_failed_runs_give_nothing_to_anyone(engine, world_stage):
    world = aw.build(engine, world_stage)
    for role in ROLES:
        for stage in STAGES:
            with pytest.raises(AccessDenied):
                access(engine, world, role, stage).get("claim")


def test_role_input_reads_every_listed_field_once_through_the_access_object(engine):
    world = aw.build(engine, "curation")
    before = len(audit(engine, world.run))
    got = role_input(access(engine, world, "critic", "curation"))
    assert set(got) == allowed("critic", "curation")
    rows = audit(engine, world.run)[before:]
    assert sorted(r.function for r in rows) == sorted(allowed("critic", "curation"))
    assert all(r.allowed for r in rows)


# --- The refusal is logged and survives ----------------------------------------------------

def test_a_denied_row_survives_the_rejection_and_the_callers_rollback(engine):
    """The row is committed in the access layer's own transaction before AccessDenied is
    raised, so neither the exception nor a caller's rollback removes it."""
    world = aw.build(engine, "before_lock")
    with engine.connect() as caller:
        tx = caller.begin()
        caller.execute(text("SELECT 1"))
        with pytest.raises(AccessDenied) as denied:
            access(engine, world, "planner", "before_lock").get("records_full")
        tx.rollback()
    assert denied.value.field == "records_full" and denied.value.role == "planner"
    with make_engine(engine.test_url).connect() as fresh:
        rows = fresh.execute(text("SELECT role, function, allowed FROM audit_log WHERE run_id = :r"),
                             dict(r=world.run)).all()
    assert ("planner", "records_full", False) in [tuple(r) for r in rows]


@pytest.mark.parametrize("world_stage,role", [("before_lock", "planner"), ("curation", "critic")])
def test_the_planner_and_the_critic_asking_for_outcomes_are_denied_and_logged(engine, world_stage, role):
    """Criterion 14.2, first point."""
    world = aw.build(engine, world_stage)
    for field in ("records_full", "flags_full", "results", "stage_outputs", "source_content"):
        with pytest.raises(AccessDenied):
            access(engine, world, role, world_stage).get(field)
    denied = [r for r in audit(engine, world.run) if r.role == role and not r.allowed]
    assert {r.function for r in denied} == {"records_full", "flags_full", "results", "stage_outputs",
                                            "source_content"}
    assert not [r for r in audit(engine, world.run) if r.role == role and r.allowed]


def test_audit_rows_never_hold_a_value(engine):
    world = aw.build(engine, "curation")
    role_input(access(engine, world, "critic", "curation"))
    for field in ("records_full", "flags_full"):
        with pytest.raises(AccessDenied):
            access(engine, world, "critic", "curation").get(field)
    text_of_rows = json.dumps([list(r) for r in audit(engine, world.run)], default=str)
    for value in aw.PLANTED.values():
        assert repr(value) not in text_of_rows and str(int(value)) not in text_of_rows


def test_unknown_roles_stages_and_fields_are_denied_and_logged(engine):
    world = aw.build(engine, "before_lock")
    for role, stage, field in (("judge", "before_lock", "claim"), ("planner", "anytime", "claim"),
                               ("planner", "before_lock", "everything")):
        with pytest.raises(AccessDenied):
            access_for(engine, world.run, role, stage).get(field)
    rows = [(r.role, r.stage, r.function, r.allowed, r.detail["code"]) for r in audit(engine, world.run)]
    # Only validated strings are logged: anything not ours is "invalid" (with its length).
    assert rows == [("invalid", "before_lock", "claim", False, "unknown_role"),
                    ("planner", "invalid", "claim", False, "unknown_stage"),
                    ("planner", "before_lock", "invalid", False, "not_on_list")]


# --- Stages are read from the database; both sides of each checkpoint ------------------------

def test_a_declared_stage_is_checked_against_the_database(engine):
    world = aw.build(engine, "before_lock")
    with pytest.raises(AccessDenied) as denied:
        access(engine, world, "critic", "curation").get("sources_meta")
    assert denied.value.code == "stage_mismatch"


def test_the_rules_lock_changes_what_each_role_may_see(engine):
    world = aw.build(engine, "before_lock")
    planner = access(engine, world, "planner", "before_lock")
    critic = access(engine, world, "critic", "curation")
    curator = access(engine, world, "curator", "curation")
    assert planner.get("claim")["text"] == aw.DIRECTION
    for a, field in ((critic, "record_metadata"), (curator, "plan_fields_to_extract")):
        with pytest.raises(AccessDenied):
            a.get(field)
    aw.lock(world.w, world.run)
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        planner.get("claim")
    assert critic.get("record_metadata") == []
    assert curator.get("plan_fields_to_extract") == ["grain_size", "yield_strength", "composition"]


def test_the_dataset_freeze_changes_what_each_role_may_see(engine):
    world = aw.build(engine, "curation")
    w = world.w
    critic = access(engine, world, "critic", "curation")
    curator = access(engine, world, "curator", "curation")
    analyst = access(engine, world, "analyst", "analysis")
    assert critic.get("flags_kind") and curator.get("sources_meta")
    with pytest.raises(AccessDenied):
        analyst.get("records_full")
    primary = w.analysis_set(world.run)
    for rec in world.records:
        w.decide(world.run, rec)
        w.add(primary, rec)
    w.freeze(world.run, len(world.records))
    for a, field in ((critic, "flags_kind"), (curator, "sources_meta")):
        with pytest.raises(AccessDenied, match="no longer at the stage"):
            a.get(field)
    assert len(analyst.get("records_full")) == len(world.records)


def test_ending_without_a_freeze_opens_only_the_gap_report_input(engine):
    world = aw.build(engine, "curation")
    gap = access(engine, world, "analyst", "closed_without_freeze")
    with pytest.raises(AccessDenied):
        gap.get("condition_summaries")
    for rec in world.records:
        world.w.decide(world.run, rec)
    aw.sql(world.w, "INSERT INTO calibration_result (run_id, status, reason) "
                    "VALUES (:r, 'unavailable', 'no_dataset_frozen')", r=world.run)
    assert gap.get("condition_summaries")["overall"]["n_records"] == len(world.records)
    for field in ("records_full", "flags_full", "results", "stage_outputs"):
        with pytest.raises(AccessDenied):
            gap.get(field)
    with pytest.raises(AccessDenied):
        access(engine, world, "critic", "curation").get("flags_kind")


def test_completion_without_a_freeze_moves_access_to_the_commentator_only(engine):
    world = aw.build(engine, "closed_without_freeze")
    gap = access(engine, world, "analyst", "closed_without_freeze")
    commentator = access(engine, world, "commentator", "final_without_freeze")
    with pytest.raises(AccessDenied):
        commentator.get("outcome")
    assert gap.get("claim")
    world.w.complete(world.run, "insufficient")
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        gap.get("claim")
    assert commentator.get("outcome") == {"status": "completed", "outcome": "insufficient", "verdict": None,
                                          "exploratory": False}
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        access(engine, world, "commentator", "final").get("results")


def test_completion_after_a_freeze_moves_access_to_the_commentator_only(engine):
    world = aw.build(engine, "analysis")
    analyst = access(engine, world, "analyst", "analysis")
    commentator = access(engine, world, "commentator", "final")
    with pytest.raises(AccessDenied):
        commentator.get("results")
    assert analyst.get("results")
    world.w.complete(world.run, "partly_sufficient")
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        analyst.get("results")
    assert commentator.get("results")["run"]["outcome"] == "partly_sufficient"


def test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome(engine):
    """Owner, 2026-10-05: no outcome values and no row-level records."""
    world = aw.build(engine, "final_without_freeze")
    got = role_input(access(engine, world, "commentator", "final_without_freeze"))
    assert set(got) == allowed("analyst", "closed_without_freeze") | {"gap_report", "outcome"}
    assert got["gap_report"] == [{"stage": "analyst", "attempt": 1, "status": "done",
                                  "output": {"note": aw.GAP_REPORT, "nested": {"values": [aw.GAP_REPORT]}}}]
    assert got["outcome"]["outcome"] == "insufficient" and got["outcome"]["verdict"] is None
    for field in ("records_full", "flags_full", "results", "stage_outputs", "run_cost", "record_metadata"):
        with pytest.raises(AccessDenied):
            access(engine, world, "commentator", "final_without_freeze").get(field)


def test_experiment_flags_relax_nothing(engine):
    """PRD 4's relaxation flag is not built in sprint 1: flags on the run change no list."""
    world = aw.build(engine, "queued")
    w = world.w
    vid = w.val("SELECT hypothesis_version_id FROM run WHERE id = :r", r=world.run)
    flagged = aw.val(w, "INSERT INTO run (hypothesis_version_id, experiment_flags) VALUES (:v, :j_f) RETURNING id",
                     v=vid, j_f={"relax_access": True, "access": "all", "unlock": ["planner", "critic"]})
    w.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
              "VALUES (:r, :s, :sv, 'pending')", r=flagged, s=w.source["mpea"], sv=w.version["mpea"])
    w.run_sql("INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
              r=flagged, s=w.source["tamu_fcc"])
    w.start(flagged)
    assert w.val("SELECT experiment_flags->>'access' FROM run WHERE id = :r", r=flagged) == "all"
    for field in sorted(set(FIELDS) - allowed("planner", "before_lock")):
        with pytest.raises(AccessDenied):
            access_for(engine, flagged, "planner", "before_lock").get(field)


# --- What each field contains -----------------------------------------------------------

def test_sources_meta_is_exactly_the_named_plain_fields(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("sources_meta")
    assert SOURCE_META_FIELDS == ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                                  "fields_available")
    assert [list(s) for s in got] == [list(SOURCE_META_FIELDS)] * 2
    assert [s["key"] for s in got] == ["mpea", "tamu_fcc"]  # the chosen sources only


def test_sources_meta_comes_from_the_code_and_the_sealed_version_not_the_registry(engine):
    """Review finding 4: editing the source registry after dispatch changes nothing for the run
    (the world has already changed the licence and properties; here also the name and the
    interpretation settings)."""
    from hypocurate.sources.versions import SOURCES
    world = aw.build(engine, "curation")
    aw.sql(world.w, "UPDATE source SET name = 'renamed', grouping_unit = 'dataset', data_kind = 'computed' "
                    "WHERE key = 'mpea'")
    mpea = access(engine, world, "critic", "curation").get("sources_meta")[0]
    d = SOURCES["mpea"]
    assert mpea == {"key": "mpea", "name": d.name, "source_type": "uploaded_table", "data_kind": "measured",
                    "licence": d.licence, "grouping_unit": "paper", "fields_available": list(d.properties_covered)}


def test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim(engine):
    world = aw.build(engine, "curation")
    got = role_input(access(engine, world, "curator", "curation"))
    assert got["plan_fields_to_extract"] == ["grain_size", "yield_strength", "composition"]
    assert [s["key"] for s in got["sources_meta"]] == ["mpea"]  # its own source only
    assert list(got["source_content"]["files"]) == ["mpea_planted.csv"]
    without_files = json.dumps({k: v for k, v in got.items() if k != "source_content"})
    assert "ZQXDIR" not in without_files and "rises" not in without_files and "k > 0" not in without_files
    assert b"ZQXDIR" not in got["source_content"]["files"]["mpea_planted.csv"]
    other = access(engine, world, "curator", "curation", source_key="controlled_duplicates")
    assert other.get("sources_meta") == []
    with pytest.raises(AccessDenied, match="not recorded for this run"):
        other.get("source_content")
    with pytest.raises(AccessDenied, match="reads one named source"):
        access(engine, world, "curator", "curation", source_key=None).get("source_content")


def test_inclusion_is_not_the_curators(engine):
    """The Curator's list has no eligibility, set or flag field (criterion 14.2, fourth point);
    eligibility is code's (step 6)."""
    assert not allowed("curator", "curation") & {"decisions", "flags_kind", "flags_full", "record_metadata"}


def test_record_metadata_carries_no_number_but_identity_and_composition(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("record_metadata")
    assert len(got) == len(world.records)
    for r in got:
        assert set(r) == {"id", "source", "item_index", "kind", "alloy", "composition", "paper_doi", "status",
                          "categories"}  # no origin key, no paper title (review finding 3)
        assert set(r["status"]) == set(HARMONIZED_FIELDS)
        assert set(r["status"].values()) <= {"converted", "not_reported", "not_convertible", "assigned", None}
        for f, v in r["categories"].items():
            assert v is None or v == "unrecognized" or vocabulary.category(f, v) == v, (f, v)
    planted = [r for r in got if r["status"]["yield_strength"] == "not_convertible"]
    assert len(planted) == 1  # the unreadable cell: its reason (which quotes it) is withheld
    marked = [r for r in got if r["categories"]["microstructure"] == "unrecognized"]
    assert len(marked) == 1 and marked[0]["categories"]["processing_method"] == "unrecognized"
    assert marked[0]["categories"]["phase_class"] == "unrecognized" and marked[0]["paper_doi"] == "unrecognized"


def test_flags_kind_has_no_numbers(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("flags_kind")
    assert got == [{"id": world.flags[0], "kind": "values_disagree", "category": "differ beyond tolerance",
                    "records": got[0]["records"]},
                   {"id": world.flags[1], "kind": "unrecognized", "category": "unrecognized", "records": []}]
    assert len(got[0]["records"]) == 2


def test_the_plan_is_projected_by_its_named_parts(engine):
    world = aw.build(engine, "analysis")
    got = access(engine, world, "analyst", "analysis").get("plan")
    u = "unrecognized"
    assert got["content"] == {
        "variables": {"outcome": {"field": "yield_strength"},
                      "predictor": {"field": "grain_size", "unit": "µm", "transformation": u}},
        "model": {"name": "hall_petch_alloy_intercepts", "null": "k <= 0", "alternative": u, "alpha": 0.05},
        "scope": {"phase_class": ["FCC", u], "alloy_class": [u]},
        "fields_to_extract": ["grain_size", "yield_strength", "composition"],
        "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}, {"rule": u, "values": ["tension", u]}],
        "eligibility_rules": [{"flag_kind": "values_disagree", "rule": u}],
        "verdict_statement": u,
        "sensitivity_analyses": ["tension_and_compression", u]}
    assert got["minimums"] == {"records": 4, "alloys": 1, "groups": 2, "resid_df": 1}
    assert got["power_assumptions"] == {"method": "information_only", "scatter": 60.0}


def test_tag_values_are_the_approved_lists_only(engine):
    world = aw.build(engine, "before_lock")
    assert access(engine, world, "planner", "before_lock").get("tag_values") == [
        {"kind": "property", "value": "yield strength"}]


def test_record_counts_are_counts_from_the_sealed_source(engine):
    world = aw.build(engine, "before_lock")
    got = access(engine, world, "planner", "before_lock").get("record_counts")
    assert [c["source"] for c in got] == ["mpea", "tamu_fcc"] and got[0]["readable"]
    assert got[1] == {"source": "tamu_fcc", "readable": False}  # the world's placeholder file
    c = got[0]
    assert c["n_records"] == 8  # four real rows and four planted ones
    assert c["by_status"]["yield_strength"] == {"converted": 7, "not_convertible": 1}
    assert c["by_category"]["test_type"]["tension"] >= 3
    assert set(c["by_category"]) == set(allowlist.CATEGORY_FIELDS)
    assert c["unrecognized"] == {"microstructure": 1, "phase_class": 1, "processing_method": 1}
    assert c["by_category"]["microstructure"]["unrecognized"] == 1
    assert not set(c["by_category"]) & allowlist.OUTCOME_FIELDS


def test_condition_summaries_are_ranges_and_counts_of_conditions_only(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = access(engine, world, "analyst", "closed_without_freeze").get("condition_summaries")
    assert set(got) == {"overall", "per_alloy"}
    overall = got["overall"]
    assert set(overall) == {"n_records", "grain_size", "test_temperature", "test_type", "phase_class"}
    assert overall["n_records"] == 8
    assert overall["grain_size"]["n"] == 8
    assert overall["grain_size"]["min"] <= 12.5 and overall["grain_size"]["max"] >= 14.5
    assert overall["test_temperature"]["min"] <= 25.0 <= overall["test_temperature"]["max"]
    assert sum(overall["test_type"].values()) <= 8
    assert sum(g["n_records"] for g in got["per_alloy"]) == 8
    for g in got["per_alloy"]:
        assert set(g) == {"alloy", "n_records", "grain_size", "test_temperature", "test_type", "phase_class"}


# --- The write protocol: hc_write_lock first, inside run_transaction ----------------------

def test_an_access_call_takes_the_run_lock_first_and_times_out_instead_of_hanging(engine):
    world = aw.build(engine, "curation")
    before = len(audit(engine, world.run))
    holder = make_engine(engine.test_url)
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        with pytest.raises(AccessFailed) as failed:
            access_for(engine, world.run, "critic", "curation", lock_timeout_ms=300).get("flags_kind")
        # The failure row is written while the lock is still held (named exception: no run lock).
        rows = audit(engine, world.run)[before:]
        tx.rollback()
    holder.dispose()
    assert failed.value.code == "lock_timeout"
    assert [(r.function, r.allowed, r.detail["result"], r.detail["code"]) for r in rows] == [
        ("flags_kind", False, "failed", "lock_timeout")]
    assert access_for(engine, world.run, "critic", "curation").get("flags_kind")
    assert layer.ACCESS_LOCK_TIMEOUT_MS == 5000


def test_an_access_call_waits_for_a_writer_holding_the_run_lock(engine):
    world = aw.build(engine, "curation")
    holder = make_engine(engine.test_url)
    result = {}
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        reader = threading.Thread(target=lambda: result.update(
            got=access_for(engine, world.run, "critic", "curation").get("flags_kind")))
        reader.start()
        waiting = False
        for _ in range(100):
            with engine.connect() as probe:
                waiting = probe.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                    "AND wait_event_type = 'Lock' AND query LIKE '%hc_write_lock%'")).scalar() > 0
            if waiting:
                break
            time.sleep(0.05)
        assert waiting and "got" not in result
        tx.commit()
        reader.join(10)
    holder.dispose()
    assert result["got"][0]["kind"] == "values_disagree"


def test_every_access_call_runs_in_run_transaction(engine, monkeypatch):
    world = aw.build(engine, "curation")
    calls = []
    real = layer.run_transaction

    def spy(e, fn, *args, **kwargs):
        calls.append(e)
        return real(e, fn, *args, **kwargs)

    monkeypatch.setattr(layer, "run_transaction", spy)
    a = access_for(engine, world.run, "critic", "curation")
    a.get("flags_kind")
    with pytest.raises(AccessDenied):
        a.get("records_full")
    assert calls == [engine, engine]


def test_the_access_transaction_calls_hc_write_lock_before_anything_else():
    src = Path(layer.__file__).read_text()
    body = src[src.index("def _transaction"):src.index("def _policy")]
    statements = [line.strip() for line in body.splitlines() if "conn.execute" in line or "actual_stage(" in line]
    assert "SET LOCAL lock_timeout" in statements[0]
    assert "FROM run WHERE id = :r" in statements[1]  # does the run exist (else a failure row)
    assert "hc_write_lock(p_run => :r)" in statements[2]
    assert "actual_stage(" in statements[3]


# --- Static checks: one way in -------------------------------------------------------------

def _calls(tree: ast.AST) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            out.append(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return out


def _imports(tree: ast.AST) -> set[str]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_the_access_layer_has_no_function_that_takes_a_path():
    for name in ("allowlist", "context", "dispatch", "errors", "fields", "inputs", "layer", "stage", "vocabulary"):
        tree = ast.parse((REPO / "hypocurate" / "access" / f"{name}.py").read_text())
        assert not {"open", "read_bytes", "read_text", "Path", "listdir", "scandir"} & set(_calls(tree)), name
        assert not {"pathlib", "io", "glob", "shutil"} & _imports(tree), name
    assert list(Access.__init__.__code__.co_varnames[:5]) == ["self", "engine", "context", "lock_timeout_ms",
                                                              "_trusted"]


def test_the_guard_is_installed_in_one_place():
    installs, hooks = [], []
    for path in sorted((REPO / "hypocurate").rglob("*.py")):
        calls = _calls(ast.parse(path.read_text()))
        if "install" in calls:
            installs.append(path.relative_to(REPO).as_posix())
        if "addaudithook" in calls:
            hooks.append(path.relative_to(REPO).as_posix())
    assert installs == ["hypocurate/access/guarded.py"]
    assert hooks == ["hypocurate/access/file_guard.py"]


def test_condition_summaries_group_alloys_by_the_same_alloy_rule():
    """Register entry 'same_alloy_rule' (owner, 2026-10-05): rounded compositions identical."""
    from hypocurate.sources.normalize import SAME_ALLOY_DECIMALS, same_alloy_key
    assert SAME_ALLOY_DECIMALS == 1
    assert same_alloy_key({"Fe": 50.01, "Ni": 49.99}) == same_alloy_key({"Ni": 49.96, "Fe": 50.04}) == "Fe 50.0 Ni 50.0"
    assert same_alloy_key({"Fe": 50.06, "Ni": 49.94}) == "Fe 50.1 Ni 49.9"
```

### `tests/test_access_projected.py`

```python
"""Step 5: the projected-data test (PRD 4 testing requirement; criterion 14.2, second point).

Formerly "the planted-value test"; renamed after the step 5 review (finding 6), because it
tests the **data a role is given** (`role_input`, built through the real dispatcher), not the
complete model request.

Distinctive outcome values are planted everywhere the main run stores them
(`access_world`): in discarded fields (stored outcomes, values as reported, reasons, flag
numbers, stage text, model instructions, proposed tags, the source's address and label) and
**inside the fields the blinded views do show** (category cells, the paper title, the DOI,
every kind of plan leaf, power assumptions, eligibility rules, a failure text, flag kinds and
categories, the source registry's licence and properties edited after dispatch). None may
appear in the projected input of the Planner (before the rules lock), the Critic (between the
lock and the freeze), the Analyst writing a gap report, or the Commentator on a run that ended
with no dataset frozen. A positive control shows the detector finds the values where they are
allowed (the Analyst after the freeze).

Single-run scope (owner's addition A): a different value, planted in the original run of
the narrower question and in an earlier run of the same hypothesis, appears in no role's
projected input at any stage.

**What this test does not cover** (review finding 6):
- the actual outbound model request: agent instructions, message history, tool errors, retry
  prompts, attachments, anything step 8 adds (a **step 8 acceptance requirement**);
- values split across fields, spelled out in words, transformed arbitrarily or compressed;
- what counts, flag kinds and condition summaries reveal by design, and timing (register
  entry 'accepted_disclosures');
- human-written text the views pass on (the claim, approved tag values): a person who writes an
  outcome value there discloses it.
A longer list of encodings cannot prove the absence of leakage; it catches our own mistakes.

Encodings searched: the value's decimal text at full precision and rounded to 2, 1 and 0
decimals; its integer part; thousands separators (comma, space, thin space) and a decimal
comma; scientific notation at several precisions; `g` formats; GPa, ksi and psi; `float.hex`;
the IEEE-754 bytes (both byte orders) in hex and base64; the decimal text in base64, hex and
URL encoding. Only encodings of at least five characters are searched, so short fragments
cannot match unrelated text by chance. The input is searched as JSON (keys and values, with
and without ASCII escapes), as its Python repr, and case-insensitively.
"""
from __future__ import annotations

import base64
import json
import struct
import urllib.parse

import pytest
from sqlalchemy import text

import access_world as aw
from hypocurate.access import bind, role_input
from hypocurate.access.allowlist import ROLES, allowed
from hypocurate.db.engine import make_engine

MPA_PER_KSI = 6.894757293168361
PSI_PER_MPA = 145.03773773020923


def encodings(v: float) -> set[str]:
    s = repr(v)
    whole, _, frac = s.partition(".")
    out = {
        s, f"{v:.2f}", f"{v:.1f}", f"{v:.0f}", str(int(v)),
        f"{v:,}", f"{v:,.2f}", f"{v:,.1f}", f"{v:,.0f}",
        f"{v:,}".replace(",", " "), f"{v:,}".replace(",", " "), f"{v:,}".replace(",", " "),
        f"{whole},{frac}", f"{v:.2f}".replace(".", ","),
        f"{v:e}", f"{v:E}", f"{v:.3e}", f"{v:.4e}", f"{v:.2e}", f"{v:g}", f"{v:.8g}", f"{v:.10g}",
        repr(v / 1000), f"{v / 1000:.4f}", f"{v / 1000:.3f}",
        repr(v / MPA_PER_KSI), f"{v / MPA_PER_KSI:.2f}", f"{v / MPA_PER_KSI:.1f}",
        f"{v * PSI_PER_MPA:.0f}", f"{v * PSI_PER_MPA:.2e}",
        v.hex(),
        struct.pack("<d", v).hex(), struct.pack(">d", v).hex(),
        base64.b64encode(struct.pack("<d", v)).decode(), base64.b64encode(struct.pack(">d", v)).decode(),
        base64.b64encode(s.encode()).decode(), s.encode().hex(), urllib.parse.quote(f"{s} MPa"),
        json.dumps(s), json.dumps(v),
    }
    return {e for e in out if len(e) >= 5}


def leaks(payload, values) -> list[str]:
    """Every (value, encoding) found anywhere in the serialized input."""
    texts = [json.dumps(payload, sort_keys=True, default=str), json.dumps(payload, ensure_ascii=False, default=str),
             repr(payload)]
    haystack = "\n".join(texts)
    folded = haystack.lower()
    found = []
    for v in values:
        for e in sorted(encodings(v)):
            if e in haystack or e.lower() in folded:
                found.append(f"{v}: {e!r}")
    return found


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def inputs_of(engine, world, role, stage=None):
    """The role's projected input, through the real dispatcher (role from the run's agent
    settings, stage from the database). `stage` is only checked."""
    access = bind(engine, world.run, world.settings[role], source_key="mpea" if role == "curator" else None)
    assert stage is None or access.context.stage == stage
    return role_input(access)


def test_the_encodings_catch_the_value_where_it_is_allowed(engine):
    """Positive control: after the freeze the Analyst does receive the outcome values, and the
    detector finds them in its input."""
    world = aw.build(engine, "analysis")
    got = inputs_of(engine, world, "analyst", "analysis")
    found = leaks(got, aw.PLANTED.values())
    for v in aw.PLANTED.values():
        assert any(f.startswith(f"{v}:") for f in found), v
    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["flags_full"])
    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["stage_outputs"])


def test_the_planted_values_are_stored_everywhere_they_should_be(engine):
    """The test is not vacuous: the values are in the source file, the records (harmonized,
    as reported, in a reason), the flag's numbers, the stage outputs, a model instruction,
    a proposed tag value, and the source's free text."""
    world = aw.build(engine, "closed_without_freeze")
    ys = repr(aw.PLANTED["yield_strength"])
    with engine.connect() as conn:
        def count(sql):
            return conn.execute(text(sql), dict(v=f"%{ys}%")).scalar()
        assert count("SELECT count(*) FROM source_file WHERE convert_from(content, 'UTF8') LIKE :v") == 1
        assert count("SELECT count(*) FROM record WHERE harmonized->'yield_strength'->>'value' LIKE :v") == 3
        assert count("SELECT count(*) FROM record WHERE harmonized::text LIKE :v") == 4  # 3 values, 1 reason
        assert count("SELECT count(*) FROM record WHERE reported::text LIKE :v") == 4
        assert count("SELECT count(*) FROM record WHERE harmonized->'yield_strength'->>'reason' LIKE :v") == 1
        assert count("SELECT count(*) FROM flag WHERE compared_values::text LIKE :v") == 1
        assert count("SELECT count(*) FROM flag WHERE kind LIKE :v AND category LIKE :v") == 1
        assert count("SELECT count(*) FROM record WHERE paper_reference LIKE :v AND paper_doi LIKE :v") == 1
        assert count("SELECT count(*) FROM record WHERE harmonized->'microstructure'->>'value' LIKE :v "
                     "AND harmonized->'processing_method'->>'value' LIKE :v "
                     "AND harmonized->'phase_class'->>'value' LIKE :v") == 1
        assert count("SELECT count(*) FROM run_record WHERE rule LIKE :v") == 1
        assert count("SELECT count(*) FROM run_source WHERE failure_reason LIKE :v") == 1
        assert count("SELECT count(*) FROM plan WHERE power_assumptions::text LIKE :v") == 1
        assert count("SELECT count(*) FROM source WHERE licence LIKE :v") == 1
        assert count("SELECT count(*) FROM stage_result WHERE output::text LIKE :v AND reasoning LIKE :v "
                     "AND tool_calls::text LIKE :v AND input::text LIKE :v") == 1
        assert count("SELECT count(*) FROM agent_setting WHERE instruction LIKE :v") == 1
        assert count("SELECT count(*) FROM tag_value WHERE value LIKE :v AND status = 'proposed'") == 1
        assert count("SELECT count(*) FROM source WHERE address LIKE :v") == 1
        assert count("SELECT count(*) FROM source_version WHERE label LIKE :v") == 1
        assert count("SELECT count(*) FROM plan WHERE content::text LIKE :v") == 1


def test_no_projected_planted_value_in_the_planners_complete_input(engine):
    world = aw.build(engine, "before_lock")
    got = inputs_of(engine, world, "planner", "before_lock")
    assert set(got) == allowed("planner", "before_lock")
    assert got["record_counts"][0]["n_records"] == 8  # it did read the planted source
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_projected_planted_value_in_the_critics_complete_input(engine):
    world = aw.build(engine, "curation")
    got = inputs_of(engine, world, "critic", "curation")
    assert set(got) == allowed("critic", "curation")
    assert len(got["record_metadata"]) == 8 and got["flags_kind"]
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_projected_planted_value_in_the_gap_report_input(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = inputs_of(engine, world, "analyst", "closed_without_freeze")
    assert set(got) == allowed("analyst", "closed_without_freeze")
    assert got["condition_summaries"]["overall"]["n_records"] == 8
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_projected_planted_value_in_the_commentators_input_without_a_freeze(engine):
    """Owner, 2026-10-05: on a run that ended with no dataset frozen, the Commentator gets only the
    gap-report input, the Analyst's gap report and the run's outcome."""
    world = aw.build(engine, "final_without_freeze")
    got = inputs_of(engine, world, "commentator", "final_without_freeze")
    assert set(got) == allowed("commentator", "final_without_freeze")
    assert aw.GAP_REPORT in json.dumps(got["gap_report"]) and got["outcome"]["outcome"] == "insufficient"
    assert got["condition_summaries"]["overall"]["n_records"] == 8
    assert leaks(got, aw.PLANTED.values()) == []
    assert "extracted yield strength" not in json.dumps(got)  # the Curator's stage output stays out


def test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic(engine):
    """Owner's addition B: the address and version label hold the planted value; sources_meta
    is a fixed set of named plain fields."""
    world = aw.build(engine, "before_lock")
    meta = bind(engine, world.run, world.settings["planner"]).get("sources_meta")
    assert leaks(meta, aw.PLANTED.values()) == []
    assert "example.org" not in json.dumps(meta) and "label" not in json.dumps(meta)
    assert "licence 4" not in json.dumps(meta)  # the registry's licence, edited after dispatch


@pytest.mark.parametrize("world_stage", ["before_lock", "curation", "analysis", "closed_without_freeze", "final",
                                         "final_without_freeze"])
def test_nothing_from_another_run_reaches_any_role(engine, world_stage):
    """Owner's addition A: the original run of the narrower question and an earlier run of the
    same hypothesis hold OTHER in records, coefficient, stage outputs and commentary."""
    world = aw.build(engine, world_stage)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM analysis_result WHERE run_id = :r AND estimate = :v"),
                            dict(r=world.original_run, v=aw.OTHER)).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM commentary WHERE run_id = :r"),
                            dict(r=world.original_run)).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"),
                            dict(r=world.earlier_run)).scalar() == 3
        assert conn.execute(text("SELECT narrower_of_run_id FROM hypothesis h JOIN hypothesis_version hv "
                                 "ON hv.hypothesis_id = h.id JOIN run r ON r.hypothesis_version_id = hv.id "
                                 "WHERE r.id = :r"), dict(r=world.run)).scalar() == world.original_run
    checked = 0
    for role in ROLES:
        if allowed(role, world_stage):
            got = inputs_of(engine, world, role, world_stage)
            if role != "curator":  # the Curator's input is its own source's bytes
                assert leaks(got, [aw.OTHER]) == [], role
            else:
                assert str(aw.OTHER).encode() not in got["source_content"]["files"]["mpea_planted.csv"]
                assert leaks({k: v for k, v in got.items() if k != "source_content"}, [aw.OTHER]) == []
            checked += 1
    assert checked >= 1
    if world_stage == "before_lock":
        assert inputs_of(engine, world, "planner", "before_lock")["claim"]["narrower_question"] is True
```

### `tests/test_access_dispatch.py`

```python
"""Step 5 review fixes: the trusted dispatcher, the immutable context, logging of denials and
failures, one snapshot per input, real concurrent checkpoint transitions, and the
vocabularies with their unrecognized counts.
"""
from __future__ import annotations

import logging
import threading
import time

import pytest
from sqlalchemy import text

import access_world as aw
from access_testing import access_for
from hypocurate.access import Access, AccessDenied, AccessFailed, bind, layer, role_input, vocabulary
from hypocurate.access.allowlist import allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.guarded import run_guarded
from hypocurate.db.engine import make_engine
from hypocurate.sources import connection


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    yield e
    e.dispose()


def audit(engine, run=None, null_run=False):
    where = "WHERE run_id IS NULL " if null_run else ("WHERE run_id = :r " if run else "")
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log " + where
                                 + "ORDER BY id"), dict(r=run)).all()


# --- The dispatcher -------------------------------------------------------------------------

def test_bind_reads_the_role_from_the_runs_agent_settings_and_the_stage_from_the_database(engine):
    world = aw.build(engine, "curation")
    for role in ("critic", "analyst", "planner"):
        a = bind(engine, world.run, world.settings[role])
        assert a.context == AccessContext(world.run, role, "curation", None, world.settings[role])
    curator = bind(engine, world.run, world.settings["curator"], source_key="mpea")
    assert curator.context.role == "curator" and curator.context.source_key == "mpea"
    assert role_input(bind(engine, world.run, world.settings["critic"]))["flags_kind"]
    binds = [r for r in audit(engine, world.run) if r.function == "bind"]
    assert len(binds) == 5 and all(r.allowed and r.detail["result"] == "allowed" for r in binds)


def test_bind_refuses_a_setting_or_source_the_run_did_not_record(engine):
    world = aw.build(engine, "curation")
    stray = aw.val(world.w, "INSERT INTO agent_setting (role, version, instruction, model) "
                            "VALUES ('analyst', 2, 'x', 'model-a') RETURNING id")
    cases = [(dict(agent_setting_id=stray), "setting_not_recorded"),
             (dict(agent_setting_id=world.settings["curator"]), "no_source"),
             (dict(agent_setting_id=world.settings["curator"], source_key="controlled_duplicates"),
              "source_not_recorded"),
             (dict(agent_setting_id=world.settings["critic"], source_key="mpea"), "source_not_for_role")]
    for kw, code in cases:
        with pytest.raises(AccessDenied) as denied:
            bind(engine, world.run, **kw)
        assert denied.value.code == code
    rows = [(r.function, r.allowed, r.detail["result"], r.detail["code"]) for r in audit(engine, world.run)
            if r.function == "bind"]
    assert rows == [("bind", False, "denied", code) for _, code in cases]


def test_bind_logs_an_unknown_run_as_a_failure_with_no_run(engine):
    aw.build(engine, "before_lock")
    with pytest.raises(AccessFailed) as failed:
        bind(engine, 999999, 1)
    assert failed.value.code == "unknown_run"
    rows = audit(engine, null_run=True)
    assert [(r.function, r.detail["result"], r.detail["code"], r.detail["requested_run"]) for r in rows] == [
        ("bind", "failed", "unknown_run", 999999)]


def test_an_access_object_has_no_public_constructor_and_cannot_be_changed(engine):
    world = aw.build(engine, "before_lock")
    with pytest.raises(TypeError, match="only by hypocurate.access.dispatch.bind"):
        Access(engine, AccessContext(world.run, "analyst", "analysis"))
    a = bind(engine, world.run, world.settings["planner"])
    with pytest.raises(AttributeError):
        a._context = AccessContext(world.original_run, "analyst", "final")
    with pytest.raises(AttributeError):
        a.context.run_id = world.original_run
    with pytest.raises(TypeError):
        bind(engine, str(world.run), world.settings["planner"])


# --- Denials and failures are logged apart ---------------------------------------------------

def test_a_readers_error_is_a_logged_failure(engine, monkeypatch):
    world = aw.build(engine, "curation")

    def broken(conn, ctx):
        raise ValueError("something with 48213.579 inside")

    monkeypatch.setitem(layer.READERS, "flags_kind", broken)
    with pytest.raises(AccessFailed) as failed:
        access_for(engine, world.run, "critic", "curation").get("flags_kind")
    assert failed.value.code == "reader_error" and "48213" not in str(failed.value)
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail) == (
        "flags_kind", False, {"result": "failed", "code": "reader_error", "error_class": "ValueError"})


def test_an_unknown_run_is_a_logged_failure(engine):
    aw.build(engine, "before_lock")
    with pytest.raises(AccessFailed) as failed:
        access_for(engine, 424242, "planner", "before_lock").get("claim")
    assert failed.value.code == "unknown_run"
    assert audit(engine, null_run=True)[-1].detail == {"result": "failed", "code": "unknown_run",
                                                      "requested_run": 424242}


def test_when_the_database_is_unavailable_the_process_log_is_the_fallback(caplog):
    down = make_engine("postgresql://nobody@127.0.0.1:1/none")
    with caplog.at_level(logging.ERROR, logger="hypocurate.access"):
        with pytest.raises(AccessFailed) as failed:
            access_for(down, 7, "planner", "before_lock").get("claim")
    assert failed.value.code == "database_error"
    assert any('"audit_fallback"' in r.getMessage() and '"database_error"' in r.getMessage() for r in caplog.records)


def test_role_input_is_never_silently_empty(engine):
    world = aw.build(engine, "curation")
    with pytest.raises(AccessDenied) as denied:
        role_input(access_for(engine, world.run, "planner", "curation"))
    assert denied.value.code == "empty_list"
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail["code"]) == ("role_input", False, "empty_list")


def test_only_validated_bounded_strings_are_logged(engine):
    world = aw.build(engine, "before_lock")
    long_role = "planner-" + "48213.579" * 500
    for kw in (dict(role=long_role, stage="before_lock"), dict(role="planner", stage=long_role)):
        with pytest.raises(AccessDenied) as denied:
            access_for(engine, world.run, **kw).get("claim")
        assert "48213" not in str(denied.value)
    with pytest.raises(AccessDenied) as denied:
        access_for(engine, world.run, "planner", "before_lock").get("x" * 9000)
    assert "xxx" not in str(denied.value)
    rows = audit(engine, world.run)
    assert [(r.role, r.stage, r.function) for r in rows] == [("invalid", "before_lock", "claim"),
                                                            ("planner", "invalid", "claim"),
                                                            ("planner", "before_lock", "invalid")]
    assert rows[0].detail["given_role_length"] == len(long_role)
    assert all(len(str(r)) < 400 for r in rows)


def test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log(engine, caplog):
    world = aw.build(engine, "before_lock")
    target = str(aw.REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv")
    run_guarded("hypocurate.access.guard_probe:probe", [{"op": "read", "path": target}], timeout=60,
                audit=(engine, world.run))
    row = audit(engine, world.run)[-1]
    assert (row.function, row.allowed, row.detail["result"], row.detail["code"], row.detail["event"]) == (
        "guarded_run", False, "failed", "file_guard", "read")
    assert "truth.csv" in row.detail["what"]
    with caplog.at_level(logging.WARNING, logger="hypocurate.access"):
        run_guarded("hypocurate.access.guard_probe:probe", [{"op": "read", "path": target}], timeout=60)
    assert any('"file_guard"' in r.getMessage() for r in caplog.records)


# --- One snapshot; real concurrent checkpoint transitions -------------------------------------

def test_a_roles_whole_input_is_read_in_one_transaction(engine):
    world = aw.build(engine, "curation")
    role_input(bind(engine, world.run, world.settings["critic"]))
    with engine.connect() as conn:
        txns = conn.execute(text("SELECT DISTINCT xmin::text FROM audit_log WHERE run_id = :r AND function <> 'bind'"),
                            dict(r=world.run)).all()
    assert len(txns) == 1


def _waiting(engine) -> bool:
    with engine.connect() as probe:
        return probe.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                                  "AND wait_event_type = 'Lock' AND query LIKE '%hc_write_lock%'")).scalar() > 0


def _race(engine, url, read, transition):
    """`transition(conn)` runs in a transaction that holds the run's lock; `read()` starts in a
    thread and must wait; the transition commits; the read then sees the new stage."""
    holder = make_engine(url)
    out = {}
    with holder.connect() as conn:
        tx = conn.begin()
        transition(conn)
        t = threading.Thread(target=lambda: out.update(result=_outcome(read)))
        t.start()
        for _ in range(100):
            if _waiting(engine):
                break
            time.sleep(0.05)
        assert _waiting(engine) and "result" not in out
        tx.commit()
        t.join(10)
    holder.dispose()
    return out["result"]


def _outcome(read):
    try:
        return ("allowed", read())
    except AccessDenied as denied:
        return ("denied", denied.code)


def test_a_rules_lock_committed_while_a_read_waits_closes_the_planner(engine):
    world = aw.build(engine, "before_lock")
    planner = bind(engine, world.run, world.settings["planner"])

    def rules_lock(conn):
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        conn.execute(text("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, "
                          "min_alloys, min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'fixed_minimum', 4, 1, 2, 1)"),
                     dict(r=world.run, fp=aw.FP))

    assert _race(engine, engine.test_url, lambda: role_input(planner), rules_lock) == ("denied", "stage_mismatch")


def test_a_freeze_committed_while_reads_wait_closes_the_critic_and_opens_the_analyst(engine):
    world = aw.build(engine, "curation")
    w = world.w
    critic = bind(engine, world.run, world.settings["critic"])
    primary = w.analysis_set(world.run)
    for rec in world.records:
        w.decide(world.run, rec)
        w.add(primary, rec)

    def freeze(conn):
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
                     dict(r=world.run, fp=aw.FP, n=len(world.records)))

    assert _race(engine, engine.test_url, lambda: critic.get("flags_kind"), freeze) == ("denied", "stage_mismatch")
    analyst = access_for(engine, world.run, "analyst", "analysis")
    kind, got = _outcome(lambda: analyst.get("records_full"))
    assert kind == "allowed" and len(got) == len(world.records)


# --- Vocabularies and unrecognized counts -------------------------------------------------------

def test_vocabularies_mark_what_they_do_not_know():
    assert vocabulary.category("microstructure", "FCC+BCC+Sec.") == "FCC+BCC+Sec."
    assert vocabulary.category("microstructure", "FCC; yield strength 48213.579 MPa") == "unrecognized"
    assert vocabulary.category("phase_class", "fcc") == "unrecognized"
    assert vocabulary.category("test_type", None) == "unrecognized"
    assert vocabulary.code("primary", vocabulary.ANALYSIS_SET_KEYS) == "primary"
    assert vocabulary.code("drop 48213.579", vocabulary.SENSITIVITY_KEYS) == "unrecognized"
    assert vocabulary.unrecognized_counts([("phase_class", "FCC"), ("phase_class", "x"), ("microstructure", "y")]) \
        == {"microstructure": 1, "phase_class": 1}


def test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure():
    """Register 'accepted_disclosures': a syntactically valid DOI may contain digits."""
    assert vocabulary.doi(" 10.1038/ncomms10602") == "10.1038/ncomms10602"
    assert vocabulary.doi("10.1234/48213.579") == "10.1234/48213.579"
    assert vocabulary.doi("doi 48213.579") == "unrecognized"
    assert vocabulary.doi("") is None


def test_the_frozen_sources_have_no_unrecognized_category_value():
    from source_helpers import sealed_from_disk
    from hypocurate.sources import adapters
    for key in ("mpea", "tamu_fcc"):
        recs = adapters.read(sealed_from_disk(key)).records
        values = [(f, r.harmonized[f].value) for r in recs for f in vocabulary.CATEGORY_FIELDS
                  if r.harmonized[f].status in ("converted", "assigned")]
        assert vocabulary.unrecognized_counts(values) == {}, key


def test_unrecognized_values_are_counted_in_coverage_and_test_connection(engine):
    """Owner, 2026-10-05: counts only, per run and per source, never the values."""
    world = aw.build(engine, "analysis")
    cov = access_for(engine, world.run, "analyst", "analysis").get("coverage")
    assert cov["sources"][0] == {"source": "mpea", "search_status": "searched", "nothing_found": None,
                                 "unrecognized": {"microstructure": 1, "phase_class": 1, "processing_method": 1}}
    assert cov["sources"][1]["unrecognized"] == {} and "failure_reason" not in cov["sources"][1]
    report = connection.test_connection(engine, "mpea", n=1).to_json()  # the planted version is the latest
    assert report["unrecognized"] == {"microstructure": 1, "phase_class": 1, "processing_method": 1}
    assert "48213" not in str(report["unrecognized"])


def test_the_gap_report_input_has_codes_not_failure_text(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = role_input(bind(engine, world.run, world.settings["analyst"]))
    assert got["coverage"]["sources"][1]["search_status"] == "failed"
    assert set(got["coverage"]["sources"][1]) == {"source", "search_status", "nothing_found", "unrecognized"}
    rules = {d["rule"] for d in got["decisions"]["records"]}
    assert rules == {"in_scope", "unrecognized"}
    assert set(allowed("analyst", "closed_without_freeze")) == set(got)
```

### `tests/test_access_files.py`

```python
"""Step 5: the file guard, a tripwire against accidental file access by trusted pipeline code.

Each test starts real guarded processes (`run_guarded`) and probes them from inside
(`hypocurate.access.guard_probe`). The tests show what the tripwire catches when our own code
makes a mistake: reading or listing answer material (`tests/`), review documents
(`docs/reviews/`), the frozen files (`data/`) or the repository root, by any of Python's usual
ways of opening a file; writing outside the private scratch directory; starting another
program; loading a new native library. They also show that what pipeline code needs still
works (templates, the database driver, the certificate bundle, the scratch directory, a role's
input through the dispatcher).

They do **not** show that the guard cannot be bypassed: it can, by code that tries (an open
descriptor, the guard's own state, preloaded ctypes; see `file_guard` and Python's warning on
audit hooks). `test_preloaded_ctypes_still_works_a_documented_limit` records one such limit.
The construction-level guarantee is the deployed image without `tests/` and `docs/`
(`tests/test_check_runtime_image.py`).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import sqlalchemy

import pytest

import access_world as aw
from hypocurate.access import bind, file_guard, role_input
from hypocurate.access.guarded import GuardedRunError, run_guarded
from hypocurate.db.engine import make_engine

REPO = Path(__file__).resolve().parent.parent
PROBE = "hypocurate.access.guard_probe:probe"
HOWS = ("open", "io.open", "pathlib", "os.open")


def probe(actions, database_url=None):
    env = dict(os.environ)
    if database_url:
        env["DATABASE_URL"] = database_url
    return run_guarded(PROBE, actions, env=env, timeout=120)


def test_answers_reviews_data_and_the_repository_root_cannot_be_read():
    targets = [REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv",
               REPO / "tests" / "fixtures" / "controlled_duplicates" / "build.py",
               REPO / "docs" / "reviews" / "step01_summary.md", REPO / "docs" / "reviews" / "checklist.md",
               REPO / "data" / "sources" / "mpea" / "MPEA_dataset.csv", REPO / "data" / "manifest.json",
               REPO / "data" / "controlled_duplicates" / "extract.csv", REPO / "CLAUDE.md", REPO / "README.md"]
    for t in targets:
        assert t.is_file(), t  # they exist: the refusals are the guard's, not missing files
    actions = [{"op": "read", "path": str(t), "how": how} for t in targets for how in HOWS]
    results = probe(actions)
    for action, result in zip(actions, results):
        assert result.startswith("refused: file guard: reading"), (action, result)


def test_the_repository_root_and_the_answer_directories_cannot_be_listed():
    dirs = [REPO, REPO / "tests", REPO / "tests" / "fixtures", REPO / "docs" / "reviews", REPO / "data"]
    actions = [{"op": "list", "path": str(d), "how": how} for d in dirs for how in ("listdir", "scandir")]
    for action, result in zip(actions, probe(actions)):
        assert result.startswith("refused: file guard"), (action, result)


def test_relative_paths_are_refused():
    actions = [{"op": "read", "path": p} for p in ("tests/fixtures/controlled_duplicates/truth.csv",
                                                   "../tests/x", "data/manifest.json", "x.txt")]
    for result in probe(actions):
        assert result.startswith("refused: file guard: relative path"), result


def test_the_python_installation_and_the_package_code_can_be_read():
    targets = [REPO / "hypocurate" / "assumptions.json", Path(os.__file__), Path(sqlalchemy.__file__)]
    actions = [{"op": "read", "path": str(t)} for t in targets]
    actions.append({"op": "list", "path": str(REPO / "hypocurate"), "how": "scandir"})
    for action, result in zip(actions, probe(actions)):
        assert result.startswith("ok"), (action, result)


def test_writes_outside_the_scratch_directory_are_refused():
    name = f"hc-written-{uuid.uuid4().hex}.txt"  # unique, and removed below even if the guard fails
    site = Path(sqlalchemy.__file__).parent.parent
    targets = [REPO / "hypocurate" / name, site / name, REPO / name, REPO / "tests" / name,
               Path(tempfile.gettempdir()) / name]
    try:
        results = probe([{"op": "write", "path": str(t)} for t in targets])
        created = [t for t in targets if t.exists()]
    finally:
        for t in targets:
            t.unlink(missing_ok=True)
    assert created == []
    for t, result in zip(targets, results):
        assert result.startswith("refused: file guard: writing"), (t, result)


def test_a_library_can_use_the_private_scratch_directory_which_is_removed_afterwards():
    write, scratch = probe([{"op": "write_scratch"}, {"op": "scratch"}])
    assert write == "ok in True"
    _, path, mode, cwd = scratch.split()
    assert mode == "0o700" and cwd == path and Path(path).name.startswith("hc-run-")
    assert not Path(path).exists()


def test_no_other_program_and_no_new_native_library():
    results = probe([{"op": "subprocess"}, {"op": "system"}, {"op": "ctypes"}])
    assert results[0] == "refused: file guard: subprocess.Popen is outside the approved inputs of pipeline code"
    assert results[1] == "refused: file guard: os.system is outside the approved inputs of pipeline code"
    assert results[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code"


def test_templates_database_and_certificates_work_under_the_guard(migrated_database):
    """Owner's addition C: the guard is not bought by breaking what pipeline code needs."""
    results = probe([{"op": "render"}, {"op": "database"}, {"op": "certificates"}], migrated_database)
    assert results == ["ok True", "ok True", "ok True"]


def test_preloaded_ctypes_still_works_a_documented_limit():
    """Review finding 1: ctypes imported before the guard can still read process memory directly.
    (A foreign call such as string_at raises the call event, which the tripwire refuses here.)"""
    assert probe([{"op": "ctypes_from_address"}, {"op": "ctypes_string_at"}]) == [
        "ok b'x'", "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code"]


def test_source_registration_cannot_run_under_the_guard():
    result, = probe([{"op": "register"}])
    assert result == ("error: RegistrationError: source registration reads data/ and cannot run in a guarded "
                      "pipeline process (step 5)")


def test_a_roles_complete_input_is_the_same_inside_the_guard(migrated_database):
    engine = make_engine(migrated_database)
    world = aw.build(engine, "before_lock")
    expected = role_input(bind(engine, world.run, world.settings["planner"]))
    engine.dispose()
    got, = probe([{"op": "role_input", "run": world.run, "agent_setting": world.settings["planner"]}],
                 migrated_database)
    assert json.loads(got) == json.loads(json.dumps(expected, sort_keys=True))


def test_the_guard_cannot_be_installed_outside_the_guarded_process():
    with pytest.raises(RuntimeError, match="installed only in the process started by"):
        file_guard.install(tempfile.gettempdir())
    assert not file_guard.installed()


def test_run_guarded_runs_only_package_code():
    for target in ("tests.access_world:build", "os:system", "hypocurate.access.guard_probe"):
        with pytest.raises(ValueError):
            run_guarded(target, [])
    with pytest.raises(GuardedRunError, match="ModuleNotFoundError"):
        run_guarded("hypocurate.no_such_module:f", [], timeout=60)


def test_the_test_process_itself_is_not_guarded():
    assert not file_guard.installed()
    assert (REPO / "tests" / "fixtures" / "controlled_duplicates" / "truth.csv").read_bytes()
    assert sys.modules["__main__"].__spec__ is None or sys.modules["__main__"].__spec__.name != file_guard.GUARDED_MAIN


@pytest.mark.parametrize("scratch", ["tests", "data", "repo", "not_private", "not_empty", "wrong_name"])
def test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else(scratch):
    """The scratch directory is where writes are allowed; the child accepts only a fresh,
    empty, private hc-run-* directory directly in the system temporary directory."""
    made = None
    if scratch in ("tests", "data"):
        path = REPO / scratch
    elif scratch == "repo":
        path = REPO
    else:
        made = Path(tempfile.mkdtemp(prefix="hc-run-" if scratch != "wrong_name" else "other-",
                                     dir=file_guard.SYSTEM_TEMP))
        if scratch == "not_private":
            made.chmod(0o755)
        if scratch == "not_empty":
            (made / "x").write_text("x")
        path = made
    try:
        done = subprocess.run([sys.executable, "-m", "hypocurate.access.guarded"], capture_output=True, text=True,
                              input=json.dumps({"target": "hypocurate.access.guard_probe:probe", "payload": [],
                                                "scratch": str(path)}), timeout=60)
    finally:
        if made:
            for f in made.iterdir():
                f.unlink()
            made.rmdir()
    assert done.returncode != 0 and "unsuitable scratch directory" in done.stderr
```


## 9. Tests: changes to `tests/test_assumptions.py`

```diff
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 4b2f0cf..f8ffe4c 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -32,7 +32,7 @@ OWNER_DECISIONS = {
     "tamu_test_temperature": ("scientific", 6),
     "permitted_test_types": ("scientific", 6),
     "tamu_grouping_unit": ("statistical", 7),  # partly applied: the adapter's grouping unit
-    "same_alloy_rule": ("scientific", 6),
+    "same_alloy_rule": ("scientific", 6),  # partly applied from step 5: the gap report's summaries
     "fixed_minimums": ("statistical", 6),  # partly applied: the database's checks
     "values_disagree_tolerance": ("data_handling", 6),
     "calibration_noise_levels": ("statistical", 7),
@@ -54,7 +54,8 @@ def test_every_category_has_entries_and_keys_are_unique():
 
 
 PARTLY = {"tamu_grouping_unit", "papers_independent", "sufficiency_options", "controlled_extract_disabled",
-          "validity_checks", "fixed_minimums", "grain_size_transformation_at_analysis", "assigned_value_statuses"}
+          "validity_checks", "fixed_minimums", "grain_size_transformation_at_analysis", "assigned_value_statuses",
+          "same_alloy_rule"}  # step 5: the gap report's condition summaries group alloys under the rule
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -108,12 +109,22 @@ def test_the_survivor_rule_has_the_owners_step_1_wording():
     assert "detected by the original paper's DOI" in e["history"][0]["value"]  # the withdrawn wording
 
 
-def test_the_pairing_rule_is_open_and_calibration_awaits_its_technical_review():
-    """Finding 4."""
-    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["conflict_pairing_rule"]
+def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review():
+    """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)."""
+    assert [e["key"] for e in REGISTER if e["state"] == "open"] == []
     pairing = BY_KEY["conflict_pairing_rule"]
-    assert pairing["pending"] == {"by": "owner", "before_step": 6} and pairing["value"] is None
-    assert "repeat specimens" in pairing["statement"]
+    assert pairing["state"] == "in_force" and "pending" not in pairing
+    assert pairing["decided"] == {"by": OWNER, "date": "2026-10-05"}
+    assert pairing["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
+    assert pairing["applied"]["status"] == "not_yet" and pairing["applied"]["step"] == 6
+    assert pairing["statement"] == (
+        "Duplicates and conflicts are looked for only between records from different sources that cite the "
+        "same paper with the same alloy, grain size and test conditions. Rows within one source are always "
+        "separate measurements (repeat specimens).")
+    notes = " ".join(pairing["notes"])
+    assert "a source that repeats its own row by mistake is not caught" in notes
+    assert "Not reviewed by an expert." in notes
+    assert pairing["history"][0]["value"].startswith("open decision:")
     assert [e["key"] for e in REGISTER if e["state"] == "direction_approved"] == ["calibration_noise_levels"]
     assert BY_KEY["calibration_noise_levels"]["pending"] == {"by": "second-model technical review", "before_step": 7}
 
@@ -357,7 +368,7 @@ HEADINGS = ["Open decisions", "Direction approved, pending technical review",
 def test_the_page_shows_every_entry_grouped_with_pending_states_first():
     html = signed_in().get("/assumptions").text
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
-    assert headings == HEADINGS
+    assert headings == HEADINGS[1:]  # no open decision since the owner decided the pairing rule (step 5)
     for e in REGISTER:
         assert f'id="{e["key"]}"' in html, e["key"]
     sections = re.split(r"<h2>", html)[1:]
@@ -372,9 +383,9 @@ def test_open_decisions_are_shown_first_when_there_are_any():
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
     assert headings == HEADINGS
     first = re.split(r"<h2>", html)[1]
-    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["conflict_pairing_rule", "an_open_question"]
+    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["an_open_question"]
     assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
-    assert "2 open decisions</strong>" in html
+    assert "1 open decision</strong>" in html
     second = re.split(r"<h2>", html)[2]
     assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
     assert "pending: second-model technical review, before step 7" in second
@@ -385,9 +396,9 @@ def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
     summary = " ".join(re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1).split())
     count = {s: sum(e["state"] == s for e in REGISTER) for s in a.STATES}
     n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
-    assert count == {"in_force": len(REGISTER) - 2, "open": 1, "direction_approved": 1}
+    assert count == {"in_force": len(REGISTER) - 1, "open": 0, "direction_approved": 1}
     assert f"{len(REGISTER)} entries: {count['in_force']} in force" in summary
-    assert "1 open decision</strong>" in summary
+    assert "0 open decisions</strong>" in summary
     assert "1 direction approved, pending technical review</strong>" in summary
     assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
     assert html.index('id="summary"') < html.index("<h2>")
```

## 10. README

````diff
diff --git a/README.md b/README.md
index 107172c..25f56a0 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,7 @@ HypoCurate takes a scientific hypothesis in words, searches registered data sour
 
 ## Status
 
-Build step 4 of 12 (PRD Section 15): sources and harmonization. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), plus the three sources registered as sealed versions, one adapter per source and "test connection" (step 4). The access layer, the pipeline and the screens come in later steps.
+Build step 5 of 12 (PRD Section 15): the access layer. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), plus the access layer with its audit log and the file guard for pipeline processes (step 5). The pipeline, the agents and the screens come in later steps.
 
 ## Set up secrets (once)
 
@@ -138,3 +138,20 @@ hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common re
 - "Test connection" runs in a read-only transaction.
 - The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
 - Not yet run on the live database: registering there is a later step and needs the owner.
+
+## Access layer
+
+Every agent reads data only through an access object for one run, role and stage (`hypocurate/access/`; PRD 4). There is no agent yet (step 8).
+
+```python
+from hypocurate.access import bind, role_input
+critic = bind(engine, run_id, agent_setting_id)   # role from the run's recorded agent settings
+role_input(critic)                                 # everything the Critic may receive, in one snapshot
+```
+
+- **Threat model** (CLAUDE.md): the access layer guards against *our own code* leaking data to a model. Agents return text only and never receive SQL, a connection or a file path; only trusted code runs. It is not a boundary against hostile code in the same process.
+- **The dispatcher** (`dispatch.bind`) is the only way to get an access object. It reads the role from the run's agent settings and the stage from the database, and accepts a source only for the Curator and only if the run recorded it. The context is immutable.
+- **Allowed fields, not blocked fields.** `allowlist.py` lists the fields each role may receive at each stage. In the blinded views (Planner, Critic, gap report, Commentator without a freeze) text comes from fixed vocabularies (`vocabulary.py`) or shows as `unrecognized`, and the plan is projected recursively by `PLAN_SCHEMA`. What these views still disclose by design (counts, flag kinds, singleton condition summaries, DOIs, human-written text, timing) is listed in `ACCEPTED_DISCLOSURES` and the register. Unrecognized category values are counted per source in "test connection" and in a run's coverage.
+- **Stages come from the database**, on every call: before the rules lock, curation, analysis, closed without a freeze, final, final without a freeze. Queued and failed runs give nothing.
+- **Logging.** Every read, policy denial and access failure is logged in `audit_log` (`detail.result`: allowed, denied or failed, with a fixed code; only validated, bounded strings). A role's input is read in one transaction that calls `hc_write_lock(p_run => …)` first. Failure rows are written without the run lock (a named exception). If the database cannot take a failure row, it goes to the process log (`hypocurate.access`). Never call the access layer while holding the same run's lock: the call waits, then fails after 5 seconds.
+- **The file guard is a tripwire, not a sandbox.** Pipeline runs execute in `python -m hypocurate.access.guarded` (`run_guarded`), where an audit hook refuses accidental reads outside the Python installation and the package, writes outside a private scratch directory, other programs and new native libraries, and logs each refusal. Python warns that audit hooks cannot contain code that tries to get around them, and this one does not (open descriptors, its own state, preloaded `ctypes`, sockets and the database are not restricted). The only construction-level guarantee is that the deployed image contains no `tests/` or `docs/`.
````

## 11. The first review

### `docs/reviews/step05_review_chatgpt.md`

```markdown
# Step 5 — second-model review (ChatGPT, 2026-10-05)

Review of `docs/reviews/step05_review_packet.md` (branch `step-05-access`, code commit `81f5003`). Saved verbatim as the owner gave it. The owner accepted all six findings on 2026-10-05, with a threat-model decision that scopes the fixes (see `docs/reviews/step05_summary.md`).

---

There are serious gaps. I would not sign off step 5 as enforcing the isolation described in the packet. The database checkpoint checks are substantially better than the surrounding security boundary.
I reviewed the supplied code and ran isolated probes against the file guard. I did not rerun the reported 620-test suite.
1. The file guard is bypassable from the Python process it guards.
   I reproduced three behaviours using a temporary sentinel file:
   - Normal opening of the file was denied.
   - An already-open descriptor could still read it.
   - Changing file_guard._state["read_roots"] made the previously denied file readable.
   I also confirmed that preloaded ctypes.string_at still works after installation. The claim that every foreign call is refused is therefore incorrect. The test exercises CDLL(None)—a new library load—not the remaining capabilities of preloaded ctypes.
   An irreversible hook is not an immutable policy. Python explicitly warns that these hooks are unsuitable as a sandbox. Python documentation
   Other boundary limitations:
   - The child inherits the environment and starts without isolation flags. Startup hooks and unexpected import paths can execute before repository-path removal and guard installation.
   - Removing a path does not remove previously loaded modules or close their handles.
   - Sockets/network access are unrestricted.
   - Ordinary symlink targets are resolved, but path checking followed by opening is not an atomic containment guarantee.
   Required decision: either restrict execution to trusted application code and describe this as protection against accidental file access, or use an actual process/OS isolation boundary for untrusted Python. Extending the event blacklist will not establish the claimed guarantee.
2. Database access bypasses the entire role/run contract.
   The guarded process intentionally receives database credentials and can connect directly. The database probe demonstrates that. Nothing restricts its SQL to Access.get: it can read source_file, records from another run, outcomes or audit rows directly.
   Additionally, Access accepts caller-selected, mutable role, run_id, stage and source_key:
   - A caller can construct an Analyst access object for another frozen run.
   - A Curator can switch to another source selected for the run; there is no independent assignment check.
   - Concurrent mutation of run_id can make the locked run differ from the run passed to a field reader, because _call rereads mutable attributes.
   This is acceptable only when a trusted dispatcher exclusively controls these objects and credentials. That boundary is not implemented here. Bind role/run/source in trusted orchestration, capture an immutable context per request, and keep unrestricted SQL outside model-controlled tools or executable code.
3. The projectors allow outcome-bearing text through approved fields.
   Field names alone do not establish blinding. Concrete examples:
   - _category accepts any string. A microstructure value such as "FCC; yield strength 48213.579 MPa" reaches the Critic and becomes a dictionary key in the Planner’s category counts.
   - Paper titles, origin keys, alloy labels and flag categories pass through as text.
   - The no-freeze Analyst receives nested plan values, power_assumptions, eligibility-rule text and coverage failure messages without recursive projection.
   - The no-freeze Commentator receives arbitrary Analyst output through gap_report.
   The packet acknowledges that some source text is intentionally approved. That is a disclosure exception, not proof that outcome values cannot appear.
   Use controlled category values and structured reason codes where possible. For deliberately retained free text, explicitly narrow the blinding claim and test the accepted risk. Plant values inside these allowed locations—not just discarded fields.
4. sources_meta does not follow its stated provenance policy.
   The summary says name and licence come from code definitions. _chosen_sources actually reads them from the mutable source table. It also reads interpretation settings there rather than from the run’s sealed source version.
   Consequently, later source edits can change an old run’s metadata, and free text can enter supposedly controlled metadata fields.
   Use the sealed version’s interpretation settings and the intended trusted source-description fields. Test changing the source registry after dispatch.
5. Denied attempts are not always logged.
   The commit-before-AccessDenied design correctly preserves ordinary policy refusals despite a caller rollback. It does not cover:
   - File-guard refusals: no audit logging exists there.
   - Unknown runs and lock timeouts.
   - Reader exceptions other than Refused.
   - Invalid role/stage calls through role_input, which can return {} without calling get.
   The timeout test explicitly expects no audit row. Also, caller-supplied role, field and source strings are copied into messages/log details, so “never a value” is not enforced.
   Distinguish policy denial from access failure, log both through an appropriate bounded mechanism, and specify the fallback when the database itself is unavailable. Do not claim unconditional durable database logging.
6. The planted-value test does not yet cover complete model input.
   role_input is a bundle of field-reader outputs. It excludes agent instructions—even though the fixture plants a value there—plus future message history, tool errors, retry prompts, attachments and any extra content step 8 assembles.
   Test the actual outbound model request when that integration exists. Until then, call this a projected-data test.
   The encoding detector also misses split strings, spelled-out numbers, arbitrary transformations, compression and information conveyed through counts or timing. Expanding its encoding list cannot prove absence of leakage.
   Particularly weak tests are the static pipeline import scan, which can be vacuous before pipeline code exists and misses indirect/dynamic access, and the ctypes test discussed above.
Checkpoint enforcement: with a fixed access context and the established database locking protocol, locking the run before reading its stage correctly serializes rules-lock and dataset-freeze transitions. I found no ordinary SQL checkpoint bypass in that path. Add an actual concurrent checkpoint-transition test; the current concurrency test holds a lock without changing the stage. Separate get calls also do not constitute one atomic input snapshot.
Counts and timing: outcome-status counts and flag classifications intentionally reveal limited outcome-related information. Singleton condition summaries reveal exact grain size or temperature. Those are consequences of the approved contract, not new reasons to remove those fields—but “no row-level value can be inferred” would be false. Timing is not protected.
Scope: I found no substantial unnecessary later-step functionality. The issue is the opposite: nested projection and the trusted model-input boundary cannot remain future work while step 5 claims complete enforcement. Keep this implementation as an access API foundation, but close or accurately delimit these security guarantees before approval.
```
