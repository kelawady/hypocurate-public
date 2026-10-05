# Build step 5 — review packet for the second model

Date: 2026-10-05. Branch: `step-05-access`. Code reviewed: commit `81f5003` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success, 620 passed, runtime image OK, https://github.com/kelawady/hypocurate/actions/runs/37321733673.

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

You are reviewing **step 5 of HypoCurate (PRD Section 15): the access layer**, built before any agent. It has four parts:
- per-role, per-stage **allowed-field lists** (`hypocurate/access/allowlist.py`);
- an **access object** through which every agent read goes, which logs every read and every refusal in `audit_log`;
- the **tests for criterion 14.2**, including the planted-value test;
- a **file guard**: pipeline runs execute in a separate process that cannot read `tests/`, `docs/`, `data/` or the repository root.

The step starts with a register update: the owner decided the conflict pairing rule. Before this review the owner made one change: on a run completed with no dataset frozen, the Commentator receives only the gap-report input, the Analyst's gap report and the run's outcome (summary, "The owner's change before the review").

Not in this step: any agent, model call, eligibility or duplicate decision, statistics, screen or migration. No change to `render.yaml`, workflows, the Dockerfile, Compose or dependencies.

Your review is advice; the test suite is the gate. Please return a dated findings file. Each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

Use the fixed checklist in section 2, answering each item yes, no or not applicable, with a reason for every "no". For this step the most relevant questions are:
- **Can any role reach an outcome value it should not see?** In particular the Planner (before the rules lock), the Critic (between the lock and the freeze), the Analyst writing a gap report (a run that ended with no dataset frozen) and the Commentator on a run completed with no dataset frozen. Check every field on their lists (`fields.py`), including text that comes from the source (category values, paper references, source names).
- **Is the planted-value test strong enough?** Where the values are planted (`tests/access_world.py`), the encodings searched (`tests/test_access_planted.py`), and the positive control.
- **Stages and checkpoints**: the stage is read from the database on every call; is any boundary wrong, and is anything read before the stage is fixed?
- **The audit log**: is every refusal logged in a transaction that survives it, and does any audit row hold a value?
- **The file guard**: is the read set (the Python installation and the package) narrow enough? Can pipeline code reach answer material another way? Is preloading the database driver sound (summary, "The database driver is imported before the guard")? Are the stated limits complete?
- **Single-run scope** (owner's addition A): can anything from another run reach a role?
- The "Questions for the reviewer" at the end of the summary.

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

## Files added, modified or deleted since `main` (`2229df3`, the step 4b live record)

```
M	README.md
A	docs/reviews/step05_review_packet.md
A	docs/reviews/step05_summary.md
M	hypocurate/access/__init__.py
A	hypocurate/access/allowlist.py
A	hypocurate/access/errors.py
A	hypocurate/access/fields.py
A	hypocurate/access/file_guard.py
A	hypocurate/access/guard_probe.py
A	hypocurate/access/guarded.py
A	hypocurate/access/inputs.py
A	hypocurate/access/layer.py
A	hypocurate/access/stage.py
M	hypocurate/assumptions.json
M	hypocurate/sources/normalize.py
M	hypocurate/sources/versions.py
M	scripts/check_runtime_image.py
A	tests/access_world.py
A	tests/test_access_files.py
A	tests/test_access_layer.py
A	tests/test_access_planted.py
M	tests/test_assumptions.py
```
```
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

Date: 2026-10-05. Branch: `step-05-access`. **Status: built; awaiting the second-model review. Not merged.** PRD Section 15, step 5: "Access layer. Role and stage objects, allowed-field lists, the audit log, and the tests for criterion 14.2 including the planted-value test. This is built before any agent."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`.

**Not built, as instructed:** any agent, any model call, eligibility or duplicate decisions, statistics, screens. **No migration** (`audit_log` exists since step 3: append-only, writable in every run state). No change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose or dependencies.

The owner approved the plan on 2026-10-05 after two questions, with four additions (A–D below), and made one change before the review: the Commentator on a run with no dataset frozen (section "The owner's change before the review").

## What was built

| Path | What it is |
|---|---|
| `hypocurate/assumptions.json` | First commit, on its own: the owner's decision on `conflict_pairing_rule` (below). Later: ten entries for this step's defaults; `same_alloy_rule` partly applied. |
| `hypocurate/access/allowlist.py` | **The access contract, in one named place**: roles, stages, the field catalogue with a description of each field, `ALLOWED[role][stage]`, the outcome fields, the category fields, the condition-summary fields, the named source fields and the named plan parts. Its docstring states the single-run scope. |
| `hypocurate/access/stage.py` | `actual_stage`: the run's stage, read from the database inside the access transaction. |
| `hypocurate/access/fields.py` | One read function per field. Each builds its output from named keys only and reads only the run's own rows. |
| `hypocurate/access/layer.py` | `Access(engine, run_id, role, stage, source_key=None)` and its one method `get(field)`. The write protocol and the audit row (below). |
| `hypocurate/access/inputs.py` | `role_input(access)`: a role's complete input at its stage (every listed field, read through the access object). Step 8 builds prompts from this and answers tool calls through the same object. |
| `hypocurate/access/errors.py` | `AccessDenied` (role, stage, field, reason). |
| `hypocurate/access/file_guard.py`, `guarded.py` | The approved input files of pipeline code (below). |
| `hypocurate/access/guard_probe.py` | Probes run inside a guarded process (reads, lists, writes, templates, database, certificates, subprocess, ctypes, registration, a role's input). Used by the tests; available for a deploy-time self-check. |
| `hypocurate/sources/normalize.py` | `SAME_ALLOY_DECIMALS = 1` and `same_alloy_key`: the owner's same-alloy rule, used by the gap report's condition summaries. |
| `hypocurate/sources/versions.py` | `read_definition_files` refuses to run in a guarded process (registration reads `data/`). |
| `scripts/check_runtime_image.py` | `REQUIRED` gains the eight access modules. |
| `README.md` | Status line; an "Access layer" section. |
| `tests/access_world.py` | Builds runs at every stage with planted values (below). |
| `tests/test_access_layer.py`, `test_access_planted.py`, `test_access_files.py` | 41, 11 and 19 tests (below). |

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
- **C. File guard scope**: which entry points install it; it cannot be installed in a process that later needs those paths; templates, the database driver and the certificate bundle work under it; one private scratch directory; writes elsewhere refused.
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
| Commentator | final_without_freeze | the Analyst's `closed_without_freeze` fields, plus `gap_report` (the output of the run's Analyst stages) and `outcome` (status, outcome, verdict, exploratory). No outcome values, no row-level records. |
| any | any other stage | nothing |

What each field contains is in `FIELDS` (allowlist.py). In brief:
- `claim`: query number, version, text, and whether it is a narrower question (a yes/no only; nothing of the original run).
- `sources_meta`: key, name, source type, kind of data, licence, grouping unit, fields available. Name and licence are text, set from the code's source definitions (`SOURCES`), not from source content. The address and the version label are never included.
- `record_counts` (Planner): per chosen source, computed by code from its sealed version through its adapter (records are stored only after the rules lock): the number of records, per field the count of each status, and per value of each category field the count of records.
- **Outcome fields**, withheld wherever outcomes are withheld: yield strength and its spread, tensile strength, hardness and its spread. The Planner does not know before the lock which one its plan will choose, so all are treated as outcomes.
- `plan`: the plan's **named parts** (PRD 5.1) only; any other key is withheld. Its list of fields to extract keeps only names of the common fields, for every role.
- `tag_values` and `domain` are reference lists, not run data: approved tag values (never proposed ones, never the run that proposed them), and the run's confirmed domain.

**Single-run scope.** Every other field reads only the run's own rows and the sealed source versions the run recorded at dispatch. Nothing reaches a role from the original run of a narrower question (its records, results, coefficient, stage outputs, commentary) or from earlier runs of the same hypothesis.

## Points in PRD 4 that were unclear or contradictory, and how they are resolved

1. **The Critic "sees sources" but never outcome values**, and the source files contain the outcome values: resolved by decision 1 (descriptions, never content).
2. **The Analyst writes the gap report** (PRD 3, step 8), but **sees data only "after the dataset freeze"** (PRD 4, 5.6), which an insufficient run never reaches: resolved by decision 2.
3. **Fields the PRD does not assign**: the plan for the Critic (not given); tag lists for the Planner (given: approved values); search coverage (Analyst, Commentator); text handed between stages (Analyst, Commentator only); tokens and cost (Analyst, Commentator); eligibility decisions for the Critic (not given); the domain for the Curator (not given); the agent's instruction text (no field: it is configuration, not data).
4. **The table lists Inclusion and Checks, which are code**: they get access objects in the steps that build them (6, 7), so their reads are logged too. Not built now.
5. **The experiment flag that may relax the contract** (PRD 4): not built. `test_experiment_flags_relax_nothing` shows that flags on a run change no list. **Backlog** (PRD 18).
6. **"Roles that can add or remove records never see outcome values"** sits awkwardly with the Curator, which reads source content and extracts records. It has no say over inclusion; whether its extraction is complete is a step 8 question (with step 4's note that adapters, which are code, extract tabular sources).
7. **The Planner's counts**: computed by code from the sealed sources (records are stored only after the lock); every property field is treated as an outcome.
8. **A possible self-wait**: the audit row is a write to the run, so an access call takes the run's lock. Code must never call the access layer while holding the same run's lock. A 5-second lock timeout turns that into an error instead of a hang.
9. **The plan's structure is step 6's**: step 5 fixes the plan's top-level names from PRD 5.1 and reads only those.

## How the access layer works

Each `Access.get(field)` is one `run_transaction` (retried on `40P01` and `40001`):
1. `SET LOCAL lock_timeout = 5000`, then `SELECT hc_write_lock(p_run => …)`. This is the locking protocol of step 3, because the audit row is a write to the run. It also fixes the stage until commit.
2. The run's actual stage (`stage.actual_stage`).
3. The checks, in order: the role and the declared stage are known; the declared stage equals the actual one; the field is on the role's list at that stage.
4. The read, by the field's function. That function may itself refuse: the Curator asking for a source its run did not record, or giving none.
5. One `audit_log` row: role, declared stage, field, allowed or denied. Its `detail` holds the actual stage, the Curator's source and the reason, never a value.
6. Commit. A refusal raises `AccessDenied` only **after** the commit, so the denied row survives the rejection and any rollback by the caller. The object owns its engine and never takes the caller's connection.

An unknown run raises the database's error from `hc_write_lock`, and no audit row is written, because there is no run to log against.

## The approved input files of pipeline code (step 1 open item 4; addition C)

**Mechanism.** Three layers:
1. **No path in the access layer.** Pipeline code gets source data only as the sealed bytes of the source versions its run recorded: `source_content` for the Curator, and the adapters behind `record_counts`. These go through `load_sealed_version`, which re-checks every file against the seal. The access layer has no function that takes a path, and a static test checks this.
2. **A guarded process for every pipeline run.** `run_guarded("hypocurate.<module>:<function>", payload)` (`guarded.py`) runs the target in a fresh `python -m hypocurate.access.guarded` process. That process:
   - removes the repository root from its import path, imports the modules in `PRELOADED` and installs the guard (`file_guard.install`), which is an **irreversible** Python audit hook;
   - from then on may **read** only the Python installation (standard library, installed packages, including the certificate bundle) and the package's own code directory;
   - may **write** only in its private scratch directory;
   - is refused everything else with `PermissionError`: the repository root, `tests/`, `docs/` (so `docs/reviews/`) and `data/`, read or listed, by `open`, `io.open`, `pathlib`, `os.open`, `os.listdir` and `os.scandir`;
   - is refused relative paths, because the hook cannot see a `dir_fd`;
   - is refused starting another program (`subprocess`, `os.system`, `exec`, `spawn`, `fork`) and native code through `ctypes`.
3. **The deployed image** holds no `tests/` or `docs/` at all (step 2, checked in CI).

**The scratch directory.**
- The parent creates it (`hc-run-*`, mode 0700, in the system temporary directory) and removes it when the child ends, however the child ends.
- In the child, `TMPDIR`, `MPLCONFIGDIR` and `XDG_CACHE_HOME` point to it, and so does the working directory.
- `install()` accepts only a fresh, empty, private `hc-run-*` directory directly in the system temporary directory, so a bad scratch path cannot open up anything else (tested with `tests/`, `data/`, the repository root, a shared, a non-empty and a wrongly named directory).

**Which entry points install it.** Only `python -m hypocurate.access.guarded`, through `run_guarded`.
- `install()` refuses to run in any other process.
- A static test checks that `install(` is called only in `guarded.py` and `addaudithook` only in `file_guard.py`.
- The pipeline's entry points (the command line's run command in step 8, the worker's run of a claimed job in step 9) must call `run_guarded`.
- **Not guarded:** the web service, the migrations, the command line's `sources` commands (registration reads `data/`; it also refuses explicitly under the guard), and the test process.
- Because the guard lives only in a process created for one run, it can never be installed in a process that later needs those paths.

**The database driver is imported before the guard (my decision, for the owner's attention).**
- psycopg imports `ctypes`. Importing `ctypes` loads the process's own symbols (`dlopen(None)`), and the guard refuses that, so the database probe failed under the full guard.
- **No refusal was weakened.** The guarded process imports psycopg before installing the guard (`PRELOADED = ("psycopg",)`). After installation, every `ctypes` load, symbol lookup and foreign call is still refused (tested), and reading the Python installation is allowed anyway.
- No ctypes function is called while connecting (checked with an audit trace).
- **For step 7:** a library that imports `ctypes` after the guard is installed (the plotting library may) is refused. Adding it to `PRELOADED` needs the owner's approval; this is stated in the register entry.

**Limits.**
- An audit hook sees what Python code opens. Files that C libraries open themselves are not seen: libpq's configuration, OpenSSL's certificate store.
- Native code could bypass the hook entirely, which is why `ctypes` is refused.
- It is an in-process guard, not an operating-system sandbox.

## Requirements carried from earlier steps

| Requirement | How |
|---|---|
| Step 1 open item 4, step 2 deviation 5, step 4 open item 4: an explicit list of approved input files; `tests/` and `docs/reviews/` outside it | The section above. The approved inputs are the sealed source versions recorded for the run; everything else on disk is unreachable in the guarded process. |
| Step 3 open item 3: every write path calls `hc_write_lock` first and retries on `40P01` / `40001` | The access layer's only write is the audit row. Each call is one `run_transaction` whose first statements are `SET LOCAL lock_timeout` and `hc_write_lock(p_run => …)`. Tested by a held lock (timeout, and waiting then succeeding), a spy on `run_transaction`, and a source-order check. |
| Step 3 stated limitation: rejected attempts are logged by the access layer | Denied rows are committed before `AccessDenied` is raised; tested against the caller's rollback. |
| Step 3 note: `flag.compared_values` is never returned to the Critic | `flags_kind`; the planted test covers it. |

## Assumptions register

- **Ten new entries** (all in force, decided 2026-10-05, applied "yes", each with named settings and regression tests): `access_allow_lists`, `outcome_fields_withheld`, `critic_metadata_without_numbers`, `gap_report_condition_summaries`, `source_meta_fields`, `plan_named_parts`, `access_stage_from_database`, `access_lock_timeout`, `no_experiment_relaxation`, `pipeline_file_guard`.
- Decided by: the owner for the decisions and additions; otherwise "step 5 (owner's approval of the plan)".
- **`same_alloy_rule`: not yet → partly** (step 6). Done: the gap report's condition summaries group records by alloy under the rule (`same_alloy_key`, `SAME_ALLOY_DECIMALS = 1`). Pending: the plan setting that applies it to the analysis.
- 79 entries: 78 in force, 0 open, 1 direction approved (calibration noise levels); 22 scientific entries not reviewed by an expert.

## Tests (620, all passing; 76 new; four register tests changed)

| File | Tests | What |
|---|---|---|
| `tests/test_access_layer.py` | 44 | **The allow-list** equals the owner's table, field for field; every listed field has a reader; no outcome-bearing field is listed for the Planner, the Critic or the gap report. **The full matrix**: every role × every field at each of the eight run states (queued, failed and the six stages). An allowed field gives one allowed audit row; every other request raises `AccessDenied` and gives exactly one denied row with the reason. **Queued and failed runs** give nothing to anyone. **`role_input`** reads each listed field once, through the access object. **A denied row survives** the rejection and the caller's rollback (checked from a fresh connection). The Planner and the Critic asking for outcomes are denied and logged (criterion 14.2), and audit rows never hold a value. Unknown roles, stages and fields are denied and logged. **Both sides of each checkpoint**: the declared stage is checked against the database; the rules lock closes the Planner and opens the Curator and the Critic; the freeze closes the Curator and the Critic and opens the Analyst; ending without a freeze opens only the gap report input; completion, without a freeze or after one, closes the Analyst and opens the Commentator's list for that case; the Commentator without a freeze gets exactly the gap-report input, the Analyst's gap report and the outcome. Experiment flags relax nothing. **Field contents**: named source fields only (and only the chosen source); the Curator reads only its own source, and its input has no claim text, no hypotheses and no direction token; no inclusion field for the Curator; record metadata has no number; flags have no numbers; the plan by its named parts; approved tag values only; counts from the sealed source; condition summaries are ranges and counts of conditions only; the same-alloy key. **The write protocol**: a held run lock makes a call time out with nothing logged, or wait and then succeed; every call runs in `run_transaction`; `hc_write_lock` comes before anything else. **Static checks**: pipeline code imports no database, source or file API; the access layer has no path-taking function; the guard is installed in one place. |
| `tests/test_access_planted.py` | 13 | **Planted values** (yield strength 48213.579, tensile strength 57104.263, hardness 36912.847) are stored in the source file, the records (as harmonized values, as reported, inside a "not a number" reason), a flag's numbers, a Curator stage's input, output, reasoning and tool calls, a model instruction, a proposed tag value, the source's address and version label, and the plan (a non-allowed entry in its list of fields, and an unnamed key). They appear in **no encoding** (list in the file's docstring: rounded, separated, scientific, GPa/ksi/psi, IEEE bytes, base64, hex, URL; at least five characters) in the complete input of the **Planner**, the **Critic**, the **gap-report Analyst** or the **Commentator on a run with no dataset frozen** (whose input does hold the gap report and the outcome). **Positive control**: the detector finds them in the Analyst's input after the freeze. **Addition B**: the source's free text reaches neither the Planner nor the Critic. **Addition A**: a different value (59324.681), in the original run of the narrower question (records, coefficient, stage output, commentary) and in an earlier, failed run of the same hypothesis (records, stage output), appears in no role's complete input at any of the six stages. |
| `tests/test_access_files.py` | 19 | In real guarded processes: answer files, builder, review documents, frozen data, `CLAUDE.md` and `README.md` cannot be read in any of four ways. The repository root and the answer directories cannot be listed. Relative paths are refused. The Python installation and the package can be read. Writes outside the scratch directory are refused (package, site-packages, repository root, `tests/`, system temporary directory); the test uses unique names and removes anything created. A library can use the scratch directory (0700, the working directory), which is removed afterwards. No subprocess, `os.system` or `ctypes`. **Templates render, the database driver connects, and an HTTPS client loads its certificate bundle.** Registration refuses to run. A role's complete input is identical inside and outside the guard. The guard cannot be installed in the test process; `run_guarded` runs only package code; the test process is not guarded; six bad scratch directories are refused. |

### Tests changed (none weakened)

The owner's pairing-rule decision removed the register's only open entry. The same pattern as step 4b's microstructure decision:
- `test_the_pairing_rule_is_open_and_calibration_awaits_its_technical_review` is renamed `test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review`. It now asserts the decision: no open entry; in force; the owner and the date; not reviewed; not yet, step 6; the exact statement; the weakness and "not reviewed" in the notes; the open state in the history. The calibration assertions are unchanged.
- `test_open_decisions_are_shown_first_when_there_are_any`: with the fixture open entry added, the open section now lists only that entry, and the summary says "1 open decision" (it said 2). The direction-approved assertions are unchanged.
- `test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries`: the counts are now in force = all but 1, open 0, direction approved 1, and the summary says "0 open decisions".
- `test_the_page_shows_every_entry_grouped_with_pending_states_first`: the page leaves out the "Open decisions" heading when nothing is open (step 4b design), so the expected headings are `HEADINGS[1:]`. The section-by-section checks are unchanged.

`same_alloy_rule` is now partly applied:
- `PARTLY` in `tests/test_assumptions.py` gains it, so the partly-applied checks cover one more entry;
- `test_the_owners_eight_decisions_are_recorded_as_decided` now expects "partly" for it, through `PARTLY`, with its step unchanged (6).

### The safeguard tests fail when the safeguard is removed

Each change was made in a scratch copy of the branch (`git archive`), and only the named test files were run, importing the copy (`PYTHONPATH`). The copy was then discarded. These checks were run on the first build, before the owner's change; the change adds no new safeguard mechanism (one more stage and list, covered by the matrix and the planted test).

| Removed or changed in the copy | Result |
|---|---|
| The allow-list check | 16 tests fail (the matrix at all seven states, the survivor test, the audit-value test, the planted tests…) |
| The declared-stage check alone | 1 test fails (`test_a_declared_stage_is_checked_against_the_database`). The allow-list is still applied at the stage read from the database, so nothing more leaks. |
| The stage taken from the caller (both checks) | 7 tests fail: every checkpoint test, and queued and failed runs |
| The refusal raised inside the transaction (its row rolled back) | 11 tests fail, including the survivor test and the matrix |
| `hc_write_lock` replaced by a plain read | the 3 lock tests fail |
| The Critic's record metadata given the harmonized values | 2 fail, including the Critic's planted test |
| The Critic's flags given the numbers compared | 3 fail, including both planted tests |
| The plan's content passed whole | 2 fail, including the gap-report planted test |
| Yield strength added to the condition summaries | 2 fail, including the gap-report planted test |
| Records read without the run filter | 4 fail: the Critic's and the gap report's planted tests, other runs at analysis and final |
| Stage outputs read without the run filter | 2 fail (other runs at analysis and final) |
| The address added to `sources_meta` | 5 fail (named fields, and all four planted inputs) |
| The guard's hook not added | 5 file tests fail (reads, listing, relative paths, writes, programs) |
| The scratch directory not checked | 7 fail (six bad directories, and writes) |
| The database driver not preloaded | the database and role-input tests under the guard fail |

**Incident during these checks.** With the hook removed, the old write test really wrote a one-byte file into the shared virtual environment's `site-packages` and one into `/tmp`. I removed both. The test was then changed to use unique names and to remove anything created before asserting (commit "the guard's write test uses unique names and always cleans up"). Four leftover scratch directories from the first version of the runner, which cleaned up in the child, were also removed. No file of the repository was affected.

### Suite results

```
$ pytest -q                                   (Codespace, Python 3.14.2, `docker compose up -d db`)
620 passed in 110.42s
$ docker compose run --rm test                 (the test image, rebuilt)
620 passed in 117.77s
```

GitHub Actions, commit `81f5003` (the last code change: the owner's change before the review): success; "Run the suite in the test image": 620 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37321733673
First build, commit `72355e6`: success, 615 passed, runtime image OK. https://github.com/kelawady/hypocurate/actions/runs/37319439565
The `ERROR: hypocurate: …` lines in the CI log's database output are the refusals the tests provoke on purpose.

## Audit-log volume (addition D)

Measured: 7 rows (the Curator's and the Critic's complete inputs and one refusal) take 923 bytes of row data: about **130 bytes a row, at most about 190**. With the row header and the two index entries, about **200 bytes a row**.

| Reads per run | Rows | Size |
|---|---|---|
| Each role reads its complete input once (Planner 5, Curator 3 per source × 2, Critic 3, Analyst 11, Commentator 11) | 36 | about 7 KB |
| With agent tool calls and refusals (step 8), say | 500 | about 100 KB |

The step 3 estimate of **4–6 MB per run (120–200 runs in 1 GB)** is unchanged: the audit log adds at most about 2%. To be measured on real runs in step 8, with the rest of the estimate.

## Deviations from the approved plan

1. **The parent creates and removes the scratch directory**, not the child. In the child, `shutil.rmtree` works through relative paths against a directory handle, which the guard refuses by design. The parent's `finally` also cleans up after a crashed child.
2. **The database driver is preloaded** before the guard (above). No refusal changed.
3. **The scratch directory is validated** by `install()`. This is an addition: a bad path would have opened writes elsewhere.
4. **The plan's list of fields to extract is filtered for every role**, not only the Curator. The first planted run found the planted value in the gap report's `plan`, because I had planted it in that list.
5. **`guard_probe.py` is in the package**, not in `tests/`. A guarded process imports only package code, and `tests/` is unreachable under the guard by design.
6. **The first access commit (`432cb35`) does not pass the suite alone**: its static test expects `guarded.py`, which comes in the next commit. The branch head passes.

## PRD corrections and clarifications for the next PRD update

1. **PRD 4 (Critic):** "sources" means source descriptions (named fields), never source content. The Critic receives no measured number of any field.
2. **PRD 3 step 8 and PRD 4 (Analyst):** on a run that ends with no dataset frozen, the Analyst writing the gap report gets everything except outcomes, plus code-computed condition summaries.
3. **PRD 4 (Commentator):** on a run completed with no dataset frozen, the Commentator receives only the gap-report input, the Analyst's gap report and the run's outcome.
4. **PRD 4 (table):** Inclusion and Checks are code; their reads go through access objects from steps 6 and 7.
5. **PRD 4 (relaxation flag):** not in sprint 1; to the backlog (PRD 18).
6. **PRD 4 (stages):** the stages are read from the database: before the lock, curation, analysis, closed without freeze, final, final without freeze; queued and failed runs give nothing.
7. **PRD 4 (implementation):** every read is one transaction that takes the run's lock, and a refusal is committed before the error is raised.
8. **PRD 6 (worker):** each pipeline run executes in a guarded process (`run_guarded`) that can read only the Python installation and the package, and write only in its own scratch directory.

## Open items

1. **Step 6:**
   - the plan model stores its content under `PLAN_KEYS` and projects each part from named keys; today the named parts other than the field list are passed as written at the lock;
   - Inclusion and Checks read through access objects;
   - `same_alloy_rule` applied as a plan setting;
   - the pairing rule applied.
2. **Step 7:** if the plotting library imports `ctypes`, adding it to `PRELOADED` needs the owner's approval and a second-model review (a guard change). Inclusion of statistics reads in the access layer.
3. **Step 8:**
   - agents receive only `role_input` and the same access object;
   - the command line's run command calls `run_guarded`;
   - how the Curator relates to tabular sources (adapters extract them);
   - measure the audit volume.
4. **Step 9:** the worker runs each claimed run through `run_guarded`; never calls the access layer while holding a run's lock.
5. **The Commentator on an insufficient run**: closed by the owner's change before the review (above).
6. **Category values and paper references** reach the Critic as the source gives them (text from the source). They are metadata the owner approved, but they are source text.
7. **Backlog (PRD 18):** the experiment flag that relaxes the access contract.
8. Carried, unchanged: the step 3 step 7 and step 9 requirements; live registration after the owner's decisions; the step 4b open items.

## Questions for the reviewer

1. Can any role reach an outcome value through a field on its list, in a form the planted test would not catch?
2. Is the guarded process's read set (the Python installation and the package) narrow enough? Is preloading the database driver sound?
3. Is the order inside an access call (lock, stage, checks, read, audit row, commit, then raise) right, and is anything read before the stage is fixed?
4. Are the stage boundaries right, in particular `closed_without_freeze` read from the run-level calibration row?
5. Do the four changed register tests keep everything they checked before?
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

- `allowlist`: the allowed fields per role and stage (the access contract, PRD 4);
- `layer.Access`: the access object every agent read goes through; logs every read;
- `inputs.role_input`: a role's complete input at its stage;
- `file_guard` and `guarded`: the approved input files of pipeline code, enforced in the
  process that runs a pipeline.
"""
from hypocurate.access.errors import AccessDenied
from hypocurate.access.inputs import role_input
from hypocurate.access.layer import Access

__all__ = ["Access", "AccessDenied", "role_input"]
```

### `hypocurate/access/allowlist.py`

```python
"""The allowed fields per role and stage (PRD 4). The one named place for the access contract.

Allowed fields, not blocked fields: a role receives exactly the fields listed for it at
the run's stage, and nothing else. Each field is built from named keys only
(`hypocurate.access.fields`), never by copying a row and removing what is forbidden.

**Single-run scope** (owner, 2026-10-05). Every field reads only the rows of the access
object's own run, and the sealed source versions that run recorded at dispatch. No field
returns anything from another run: not from the run a narrower question came from (its
results, coefficient, stage outputs or commentary), and not from earlier runs of the same
hypothesis. Two fields are reference lists, not run data: `domain` (the run's confirmed
domain) and `tag_values` (the approved values of the fixed tag lists, without the run that
proposed them).

Stages are read from the database on every call (`hypocurate.access.stage`), never taken
from the caller. A role that is not listed for a stage receives nothing at that stage; a
queued or failed run gives nothing to anyone. There is no general unlock at a checkpoint,
and no experiment flag relaxes this contract (sprint 1; PRD 4's relaxation flag is in the
backlog).
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

ROLES = ("planner", "curator", "critic", "analyst", "commentator")

# none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
# frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
# closed_without_freeze: curation ended with no dataset frozen (insufficient), running.
# final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")

FIELDS = MappingProxyType({
    "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
    "domain": "The run's confirmed domain: key, name and profile.",
    "sources_meta": "The run's chosen sources, as fixed named plain fields only (SOURCE_META_FIELDS).",
    "tag_values": "The approved values of the fixed tag lists: kind and value.",
    "record_counts": "Per chosen source, computed by code from its sealed version: the number of records, "
                     "per field the count of each status, and per value of each non-outcome category field "
                     "the count of records.",
    "plan_fields_to_extract": "From the locked plan, the list of fields to extract, and nothing else.",
    "source_content": "The sealed files of the one source the Curator reads, as recorded for the run.",
    "record_metadata": "Per stored record: id, source, origin key, alloy label and composition, paper "
                       "reference and DOI, each field's status, and the non-outcome category values. "
                       "No measured number of any field.",
    "flags_kind": "Per flag: id, kind, category and record ids. Never the numbers compared.",
    "plan": "The locked plan: its named parts (PLAN_KEYS), fingerprint, lock time, data-sufficiency "
            "option and minimums, sensitivity analyses and power assumptions.",
    "records_full": "Per stored record: every stored field, including outcome values and values as reported.",
    "decisions": "Eligibility decisions (record, eligible, rule) and the named analysis sets.",
    "flags_full": "Per flag: kind, category, record ids, the numbers compared, the Critic's class and reason.",
    "results": "The run's status, outcome, verdict and exploratory label; the dataset freeze; analysis "
               "results; calibration results.",
    "coverage": "Per source: search status and kind of nothing found; the run's search coverage lists.",
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

# Fields whose values are categories (text from a fixed or source vocabulary), shown to the
# Critic and counted for the Planner and the gap report.
CATEGORY_FIELDS = ("test_type", "test_temperature_band", "phase_class", "microstructure", "processing_method")

# The non-outcome measured conditions summarized for the gap report (owner, 2026-10-05).
CONDITION_RANGE_FIELDS = ("grain_size", "test_temperature")
CONDITION_COUNT_FIELDS = ("test_type", "phase_class")

# sources_meta: a fixed set of named plain fields (owner, 2026-10-05). Free text such as
# the address or the version label never reaches a role through this field.
SOURCE_META_FIELDS = ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                      "fields_available")

# The named parts of a plan (PRD 5.1). The plan model (step 6) stores its content under
# these keys; any other key in a plan's content is withheld from every role.
PLAN_KEYS = ("claim", "hypothesis_version", "variables", "scope", "model", "sufficiency",
             "fields_to_extract", "exclusion_rules", "eligibility_rules", "verdict_statement",
             "sensitivity_analyses")
```

### `hypocurate/access/errors.py`

```python
"""The one error the access layer raises for a refused read (PRD 4)."""
from __future__ import annotations


class AccessDenied(Exception):
    """A role asked for a field it may not receive at the run's stage, or claimed a stage
    the run is not in. The refusal is already in the audit log when this is raised."""

    def __init__(self, role: str, stage: str, field: str, reason: str):
        self.role, self.stage, self.field, self.reason = role, stage, field, reason
        super().__init__(f"access denied: {role} at {stage} asked for {field!r}: {reason}")
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
"""The access object: one per role, stage and run (PRD 4).

Every read an agent's code path makes goes through `Access.get(field)`. Each call is one
transaction (`run_transaction`, retried on 40P01 / 40001), in this order:

1. `SET LOCAL lock_timeout`, then `hc_write_lock(p_run => run)`: the locking protocol of
   step 3 (the audit row is a write to the run), which also fixes the run's stage until
   commit;
2. the run's actual stage, read from the database (`stage.actual_stage`);
3. the checks: the declared stage equals the actual one, and the field is on the role's
   list for that stage (`allowlist.allowed`);
4. the read, by the field's function (`fields.READERS`), which may still refuse;
5. one `audit_log` row: role, declared stage, field, allowed or denied, and in `detail`
   the actual stage and the reason, never a value;
6. commit.

A refusal writes its denied row and commits, and only then raises `AccessDenied`, so the
row survives the rejection: it is never inside a transaction the caller could roll back.
The object owns its engine and never accepts the caller's connection.

**Never call the access layer while holding a run's lock** (a write transaction that has
called `hc_write_lock` for the same run): the access transaction would wait for it. The
lock timeout turns that wait into an error instead of a hang.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.allowlist import ROLES, STAGES, allowed
from hypocurate.access.errors import AccessDenied
from hypocurate.access.fields import READERS, Context, Refused
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction

# How long an access call waits for a run's lock before failing (milliseconds).
ACCESS_LOCK_TIMEOUT_MS = 5000

_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :field, :allowed, :detail)").bindparams(bindparam("detail", type_=JSONB))


class Access:
    """What one role may read from one run at one stage."""

    def __init__(self, engine: Engine, run_id: int, role: str, stage: str, source_key: str | None = None,
                 lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS):
        self._engine = engine
        self.run_id = int(run_id)
        self.role = role
        self.stage = stage
        self.source_key = source_key
        self._lock_timeout_ms = int(lock_timeout_ms)

    def __repr__(self) -> str:
        return f"Access(run={self.run_id}, role={self.role!r}, stage={self.stage!r})"

    def get(self, field: str) -> Any:
        """The field's content, or AccessDenied (already logged)."""
        outcome = run_transaction(self._engine, lambda conn: self._call(conn, field))
        if outcome[0] == "denied":
            raise AccessDenied(self.role, self.stage, field, outcome[1])
        return outcome[1]

    def _call(self, conn: Connection, field: str) -> tuple[str, Any]:
        conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=self.run_id)).scalar_one()
        actual = actual_stage(conn, self.run_id, status)
        reason = self._refusal(field, actual)
        if reason is None:
            try:
                value = READERS[field](conn, Context(self.run_id, self.role, self.source_key))
            except Refused as refused:
                reason = str(refused)
        detail: dict[str, Any] = {"actual_stage": actual}
        if self.source_key is not None:
            detail["source"] = self.source_key
        if reason is not None:
            detail["reason"] = reason
        conn.execute(_AUDIT, dict(r=self.run_id, role=self.role, stage=self.stage, field=field,
                                  allowed=reason is None, detail=detail))
        return ("denied", reason) if reason is not None else ("allowed", value)

    def _refusal(self, field: str, actual: str) -> str | None:
        if self.role not in ROLES:
            return f"unknown role {self.role!r}"
        if self.stage not in STAGES:
            return f"unknown stage {self.stage!r}"
        if self.stage != actual:
            return f"the run is at stage {actual!r}, not {self.stage!r}"
        if field not in allowed(self.role, actual):
            return f"{field!r} is not on the {self.role}'s list at stage {actual!r}"
        if field not in READERS:  # listed but not implemented: never silently empty
            return f"no reader for {field!r}"
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
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping

from sqlalchemy import Connection, text

from hypocurate.access.allowlist import (CATEGORY_FIELDS, CONDITION_COUNT_FIELDS, CONDITION_RANGE_FIELDS,
                                         PLAN_KEYS, SOURCE_META_FIELDS)
from hypocurate.sources import adapters
from hypocurate.sources.normalize import same_alloy_key
from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, AdapterError
from hypocurate.sources.versions import UnsealedVersion, load_sealed_version

HAS_VALUE = ("converted", "assigned")


class Refused(Exception):
    """A field function refuses this read (for example a Curator asking for a source its
    run did not record). The layer logs it as denied and raises AccessDenied."""


@dataclass(frozen=True)
class Context:
    run_id: int
    role: str
    source_key: str | None  # the Curator's one source


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
    """The run's chosen sources (a version recorded at dispatch), in key order."""
    return _rows(conn, "SELECT s.key, s.name, s.source_type, s.data_kind, s.licence, s.grouping_unit, "
                       "s.properties_covered, rs.source_version_id FROM run_source rs "
                       "JOIN source s ON s.id = rs.source_id "
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


def _category(entry: Any) -> str | None:
    """A category field's value, only if it has a value status and is text."""
    if _status(entry) in HAS_VALUE and isinstance(entry.get("value"), str):
        return entry["value"]
    return None


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
    """Counts by field status and by category value. Never a value of a non-category field."""
    n = 0
    by_status = {f: Counter() for f in HARMONIZED_FIELDS}
    by_category = {f: Counter() for f in CATEGORY_FIELDS}
    for h in harmonized_rows:
        n += 1
        for f in HARMONIZED_FIELDS:
            by_status[f][_status(h.get(f)) or "missing"] += 1
        for f in CATEGORY_FIELDS:
            value = _category(h.get(f))
            if value is not None:
                by_category[f][value] += 1
    return {"n_records": n,
            "by_status": {f: dict(sorted(c.items())) for f, c in by_status.items()},
            "by_category": {f: dict(sorted(c.items())) for f, c in by_category.items()}}


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
    out = []
    for row in _chosen_sources(conn, ctx):
        if ctx.role == "curator" and row.key != ctx.source_key:
            continue
        values = {"key": row.key, "name": row.name, "source_type": row.source_type, "data_kind": row.data_kind,
                  "licence": row.licence, "grouping_unit": row.grouping_unit,
                  "fields_available": [f for f in row.properties_covered if f in HARMONIZED_FIELDS]}
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


def _fields_to_extract(content: Any) -> list[str]:
    """The plan's list of fields to extract: only names of the common fields, in order;
    anything else in the list is withheld."""
    listed = content.get("fields_to_extract") if isinstance(content, Mapping) else None
    out: list[str] = []
    for f in listed if isinstance(listed, list) else []:
        if isinstance(f, str) and f in HARMONIZED_FIELDS and f not in out:
            out.append(f)
    return out


def plan_fields_to_extract(conn: Connection, ctx: Context) -> list[str]:
    return _fields_to_extract(_rows(conn, "SELECT content FROM plan WHERE run_id = :r", r=ctx.run_id)[0].content)


def source_content(conn: Connection, ctx: Context) -> dict:
    """The sealed files of the Curator's one source, from the version its run recorded."""
    if ctx.source_key is None:
        raise Refused("the Curator reads one named source; none was given")
    vid = conn.execute(text(
        "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
        "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL"),
        dict(r=ctx.run_id, k=ctx.source_key)).scalar_one_or_none()
    if vid is None:
        raise Refused(f"source {ctx.source_key!r} is not recorded for this run")
    version = load_sealed_version(conn, vid)
    return {"source": ctx.source_key, "files": dict(version.files)}


def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
    """No measured number of any field (owner, 2026-10-05): statuses, categories, identity."""
    out = []
    for r in _stored_records(conn, ctx):
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        out.append({
            "id": r.id, "source": r.source, "origin": r.source_item_key, "item_index": r.item_index,
            "kind": r.kind, "alloy": r.alloy, "composition": _composition(h.get("composition")),
            "paper_reference": r.paper_reference, "paper_doi": r.paper_doi,
            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
            "categories": {f: _category(h.get(f)) for f in CATEGORY_FIELDS},
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
    return [{"id": f.id, "kind": f.kind, "category": f.category, "records": records.get(f.id, [])}
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
    content = p.content if isinstance(p.content, Mapping) else {}
    # The named parts as written at the rules lock; the field list as the Curator gets it.
    # (The structure of the other parts is step 6's plan model, which projects each part.)
    named = {k: content[k] for k in PLAN_KEYS if k in content}
    if "fields_to_extract" in named:
        named["fields_to_extract"] = _fields_to_extract(content)
    return {"content": named,
            "fingerprint": p.fingerprint, "locked_at": _plain(p.locked_at),
            "sufficiency_option": p.sufficiency_option,
            "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
                         "resid_df": p.min_resid_df},
            "sensitivity_analyses": list(p.sensitivity_analysis_keys),
            "power_assumptions": p.power_assumptions}


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
        sets.setdefault(key, [])
        if record_id is not None:
            sets[key].append(record_id)
    return {"records": [{"record": rec, "eligible": eligible, "rule": rule} for rec, eligible, rule in _rows(
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
    per_source = [{"source": key, "search_status": st, "nothing_found": nf, "failure_reason": fr}
                  for key, st, nf, fr in _rows(
                      conn, "SELECT s.key, rs.search_status, rs.nothing_found, rs.failure_reason FROM run_source rs "
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
        out[f] = dict(sorted(Counter(v for v in (_category(h.get(f)) for h in harmonized_rows)
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
"""A role's complete input at its stage (PRD 4, testing requirement).

`role_input` reads every field on the role's list through the role's access object; it is
everything that role can receive at that stage. The agents (step 8) build their prompts
and answer their tool calls from this and from the same access object only, so the access
tests on this input cover what an agent sees. Fields take no parameters, so the complete
input is one read of each listed field.
"""
from __future__ import annotations

from typing import Any

from hypocurate.access.allowlist import allowed
from hypocurate.access.layer import Access


def role_input(access: Access) -> dict[str, Any]:
    """Every field `access.role` may receive at `access.stage`, read through `access`.
    Raises AccessDenied (logged) if the run is not at that stage."""
    return {field: access.get(field) for field in sorted(allowed(access.role, access.stage))}
```

### `hypocurate/access/file_guard.py`

```python
"""The approved input files of pipeline code (step 1 open item 4; step 5).

Pipeline code reads source data only as the sealed bytes of the source versions its run
recorded, through the access layer (`fields.source_content`, `fields.record_counts`); the
access layer has no function that takes a file path. This module makes everything else on
disk unreachable in the process that runs a pipeline, by construction:

- `install()` adds a Python audit hook, which cannot be removed once added. From then on
  the process may **read** only the Python installation (standard library and installed
  packages, including the certificate bundle) and the `hypocurate` package's own code
  directory, and may **write** only in its private scratch directory. Everything else is
  refused with `PermissionError`: in particular the repository root, `tests/`, `docs/`
  (and so `docs/reviews/`) and `data/`. Relative paths are refused (the hook cannot see a
  `dir_fd` they may be relative to). Starting another program (`subprocess`, `os.system`,
  `exec`, `spawn`, `fork`) and loading native code through `ctypes` are refused.
- It is installed only in a process started for one pipeline run, by
  `python -m hypocurate.access.guarded` (`guarded.run_guarded`), which exits when the run
  ends. `install()` refuses to run in any other process, so the guard can never be
  installed in a process that later needs those paths: the web service, the migrations,
  the command line's `sources` commands (registration reads `data/`) and the test process
  never install it.

Limit: an audit hook sees what Python code opens. Files that C libraries open themselves
(libpq's configuration, OpenSSL's certificate store) are not seen, and native code could
bypass the hook entirely, which is why loading native code through `ctypes` is refused.
It is an in-process guard, not an operating-system sandbox. The deployed image holds no
`tests/` or `docs/` at all (step 2, checked in CI).
"""
from __future__ import annotations

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


def _refuse(what: str) -> None:
    raise PermissionError(f"file guard: {what} is outside the approved inputs of pipeline code")


def _check_path(path, writing: bool) -> None:
    if path is None or isinstance(path, int):  # an already-open descriptor (checked when opened)
        return
    real = _resolve(path)
    if real is None:
        _refuse(f"relative path {os.fsdecode(path)!r}")
    scratch = _state["scratch"]
    allowed = _inside(real, (scratch,)) if writing else _inside(real, _state["read_roots"] + (scratch,))
    if not allowed:
        _refuse(f"{'writing' if writing else 'reading'} {real}")


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
        _refuse(f"{event}")


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
"""Runs pipeline code in a fresh process under the file guard (`file_guard`).

`run_guarded("hypocurate.module:function", payload)` starts
`python -m hypocurate.access.guarded`, sends it the target and a JSON payload, and returns
the target's JSON result. The child:

1. receives a private scratch directory (mode 0700, created by the parent, which removes it
   when the child ends, however it ends) and points `TMPDIR`, `MPLCONFIGDIR` and
   `XDG_CACHE_HOME` at it, for libraries that need a cache or temporary files (the
   plotting library in step 7); its working directory is the scratch directory;
2. removes the repository root from its import path (the `hypocurate` package is already
   imported and keeps its own path), and imports the modules in `PRELOADED`;
3. installs the guard, irreversibly;
4. imports the target, which must be inside the `hypocurate` package, calls it with the
   payload, writes the result to its standard output and exits.

This is the only place that installs the guard. The pipeline's entry points (the command
line's run command, step 8; the worker's run of a claimed job, step 9) run each pipeline
run through `run_guarded`. The web service, the migrations, the `sources` commands and
the test process do not.
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


def run_guarded(target: str, payload: Any = None, env: dict[str, str] | None = None,
                timeout: float | None = None) -> Any:
    """Runs `target(payload)` in a guarded child process and returns its JSON result."""
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
refused it. It is how the tests (and, later, a deploy-time self-check) show what pipeline
code can and cannot reach. It reads nothing it reports beyond a byte count.
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


def _register(_: Any) -> str:
    from hypocurate.sources.versions import SOURCES, read_definition_files
    read_definition_files(SOURCES["mpea"])
    return "ok"


def _role_input(action: dict) -> str:
    """A role's complete input, built through the access layer inside the guarded process."""
    import base64
    import json
    from hypocurate.access import Access, role_input
    from hypocurate.db.engine import make_engine
    engine = make_engine(os.environ["DATABASE_URL"])
    access = Access(engine, action["run"], action["role"], action["stage"], source_key=action.get("source"))
    out = json.dumps(role_input(access), sort_keys=True,
                     default=lambda b: base64.b64encode(b).decode() if isinstance(b, bytes) else str(b))
    engine.dispose()
    return out


ACTIONS: dict[str, Callable[[dict], str]] = {
    "read": lambda a: _read(a["path"], a.get("how", "open")),
    "list": lambda a: _list(a["path"], a.get("how", "listdir")),
    "write": lambda a: _write(a["path"]),
    "write_scratch": _write_scratch, "scratch": _scratch, "render": _render, "database": _database, "certificates": _certificates,
    "subprocess": _subprocess, "system": _system, "ctypes": _ctypes, "register": _register,
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

### `scripts/check_runtime_image.py`

```diff
diff --git a/scripts/check_runtime_image.py b/scripts/check_runtime_image.py
index f4f02a5..0d6d95c 100644
--- a/scripts/check_runtime_image.py
+++ b/scripts/check_runtime_image.py
@@ -28,7 +28,11 @@ REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.jso
             "data/controlled_duplicates/extract.csv",
             # Step 4b: the assumptions register and its page.
             "hypocurate/assumptions.json", "hypocurate/assumptions.py",
-            "hypocurate/web/templates/assumptions.html"]
+            "hypocurate/web/templates/assumptions.html",
+            # Step 5: the access layer and the guarded process that pipeline runs use.
+            "hypocurate/access/allowlist.py", "hypocurate/access/layer.py", "hypocurate/access/fields.py",
+            "hypocurate/access/stage.py", "hypocurate/access/inputs.py", "hypocurate/access/file_guard.py",
+            "hypocurate/access/guarded.py", "hypocurate/access/guard_probe.py"]
 FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
 FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")
```


## 7. The assumptions register: diff of `hypocurate/assumptions.json`

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index ffd104d..3825d1a 100644
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
@@ -2816,5 +2839,529 @@
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
+      "tests/test_access_planted.py::test_nothing_from_another_run_reaches_any_role",
+      "tests/test_access_layer.py::test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome",
+      "tests/test_access_planted.py::test_no_planted_value_in_the_commentators_input_without_a_freeze"
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
+      "tests/test_access_planted.py::test_no_planted_value_in_the_planners_complete_input"
+    ]
+  },
+  {
+    "key": "critic_metadata_without_numbers",
+    "name": "What the Critic sees about records",
+    "state": "in_force",
+    "statement": "The Critic sees source descriptions, never source content. Per record: id, source, origin key, alloy label and composition, paper reference and DOI, each field's status, and the category values (test type, temperature band, phase class, microstructure, processing method). No measured number of any field, not grain size and not temperature. Flags: kind, category and record ids, never the numbers compared.",
+    "value": {
+      "text": "metadata, statuses and categories; no measured numbers",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The Critic's classification of flags (step 8).",
+    "reason": "PRD 4: the Critic is told the kind of flag, never the numbers compared; and the source files contain the outcome values.",
+    "evidence": [
+      "Owner's answer to step 5 question 1, 2026-10-05."
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
+    "history": [],
+    "notes": [
+      "Category values and paper references are the source's text, shown as the source gives them."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_record_metadata_carries_no_number_but_identity_and_composition",
+      "tests/test_access_layer.py::test_flags_kind_has_no_numbers",
+      "tests/test_access_planted.py::test_no_planted_value_in_the_critics_complete_input"
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
+      "tests/test_access_planted.py::test_no_planted_value_in_the_gap_report_input",
+      "tests/test_access_layer.py::test_ending_without_a_freeze_opens_only_the_gap_report_input"
+    ]
+  },
+  {
+    "key": "source_meta_fields",
+    "name": "What a role sees about a source",
+    "state": "in_force",
+    "statement": "A source is described by a fixed set of named plain fields: key, name, type, kind of data, licence, grouping unit and fields available. Free text such as the address, the version label or notes never reaches the Planner or the Critic.",
+    "value": {
+      "text": "key, name, source_type, data_kind, licence, grouping_unit, fields_available",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The source descriptions every role receives.",
+    "reason": "Free text could carry anything, including an outcome value.",
+    "evidence": [
+      "Owner's addition B at the approval of the step 5 plan, 2026-10-05."
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
+    "history": [],
+    "notes": [
+      "Name and licence are text; they are set from the code's source definitions (SOURCES in hypocurate/sources/versions.py), not from source content."
+    ],
+    "tests": [
+      "tests/test_access_layer.py::test_sources_meta_is_exactly_the_named_plain_fields",
+      "tests/test_access_planted.py::test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic"
+    ]
+  },
+  {
+    "key": "plan_named_parts",
+    "name": "The named parts of a plan",
+    "state": "in_force",
+    "statement": "A plan's content is read only under its named parts (PRD 5.1): claim, hypothesis version, variables, scope, model, sufficiency, fields to extract, exclusion rules, eligibility rules, verdict statement, sensitivity analyses. Any other key is withheld from every role. The list of fields to extract keeps only names of the common fields.",
+    "value": {
+      "text": "the eleven named parts of PRD 5.1",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "What any role receives of a plan; the plan model (step 6) stores its content under these names.",
+    "reason": "Allowed fields, not blocked fields (PRD 4).",
+    "evidence": [
+      "PRD 5.1; step 5 plan, point 9 (approved by the owner, 2026-10-05)."
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
+          "ref": "python:hypocurate.access.allowlist:PLAN_KEYS",
+          "equals": [
+            "claim",
+            "hypothesis_version",
+            "variables",
+            "scope",
+            "model",
+            "sufficiency",
+            "fields_to_extract",
+            "exclusion_rules",
+            "eligibility_rules",
+            "verdict_statement",
+            "sensitivity_analyses"
+          ]
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "The parts other than the field list are passed as written at the rules lock; step 6 defines their structure and must project each part from named keys too."
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
+    "statement": "A pipeline run executes in a fresh process (python -m hypocurate.access.guarded) under an irreversible guard: it may read only the Python installation and the package's code, and write only in a private scratch directory (an empty, 0700 hc-run-* directory in the system temporary directory, removed afterwards). tests/, docs/, data/ and the repository root cannot be read or listed; other programs and native code through ctypes are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. The database driver is imported before the guard is installed.",
+    "value": {
+      "text": "read: Python installation and package code; write: private scratch directory only",
+      "unit": null
+    },
+    "category": "operational",
+    "affects": "Every pipeline run (the command line's run command, step 8; the worker, step 9).",
+    "reason": "Answer material and review documents must be unreachable by construction, not by convention (step 1 open item 4).",
+    "evidence": [
+      "Step 1 summary, open item 4; step 5 plan and owner's addition C, 2026-10-05."
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
+    "history": [],
+    "notes": [
+      "Limit: an audit hook sees what Python code opens; files that C libraries open themselves (libpq, OpenSSL) are not seen. It is an in-process guard, not an operating-system sandbox.",
+      "A library that imports ctypes after the guard is installed is refused; such a library (for example the plotting library, step 7) must be added to PRELOADED with the owner's approval."
+    ],
+    "tests": [
+      "tests/test_access_files.py::test_answers_reviews_data_and_the_repository_root_cannot_be_read",
+      "tests/test_access_files.py::test_writes_outside_the_scratch_directory_are_refused",
+      "tests/test_access_files.py::test_templates_database_and_certificates_work_under_the_guard",
+      "tests/test_access_files.py::test_source_registration_cannot_run_under_the_guard",
+      "tests/test_access_files.py::test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else",
+      "tests/test_access_layer.py::test_the_guard_is_installed_in_one_place"
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
    content = {"claim": DIRECTION, "model": {"alternative": f"k > 0 ({DIRECTION})"},
               "fields_to_extract": ["grain_size", "yield_strength", "composition", DIRECTION,
                                     repr(PLANTED["yield_strength"]), PLANTED["yield_strength"]],
               "scope": {"phase_class": "FCC"},
               "unnamed_key": {"planted": PLANTED["yield_strength"]}}
    sql(w, "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
           "min_groups, min_resid_df) VALUES (:r, :j_c, :fp, 'fixed_minimum', 4, 1, 2, 1)", r=run, j_c=content, fp=FP)


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
    sql(w, "INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 1, :i, 'model-a')",
        i=f"remember {PLANTED['yield_strength']}")
    sql(w, "INSERT INTO tag_value (kind, value, status, decided_at) "
           "VALUES ('property', 'yield strength', 'approved', now())")
    sql(w, "INSERT INTO tag_value (kind, value, status) VALUES ('property', :v, 'proposed')",
        v=f"strength {PLANTED['yield_strength']}")
    original = original_run(w)
    h = w.hypothesis(narrower_of=original)
    vid = val(w, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                 "VALUES (:h, 1, :t, :d) RETURNING id", h=h, t=DIRECTION, d=w.domain["grain_size_strengthening"])
    w.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=w.source["mpea"])
    w.submit(vid)
    w.confirm(vid)
    w.dispatch_version(vid)
    earlier = w.running(vid=vid, sources=("mpea",))
    w.lock(earlier)
    store_value_records(w, earlier, OTHER)
    stage(w, earlier, "curator", "curator", f"saw {OTHER}")
    w.fail(earlier)
    rid = w.run(vid=vid, sources=("mpea",))
    world = AccessWorld(w, rid, original, earlier)
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
    stage(w, rid, "curator", "curator", f"extracted yield strength {PLANTED['yield_strength']} MPa")
    if stage_name == "curation":
        return world
    for rec in world.records:
        w.decide(rid, rec)
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
from sqlalchemy.exc import OperationalError

import access_world as aw
from hypocurate.access import Access, AccessDenied, allowlist, layer, role_input
from hypocurate.access.allowlist import ALLOWED, FIELDS, PLAN_KEYS, ROLES, SOURCE_META_FIELDS, STAGES, allowed
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
    return Access(engine, world.run, role, stage, **kw)


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
                assert rows[0].detail == {"actual_stage": stage, **({"source": "mpea"} if role == "curator" else {})}
            else:
                with pytest.raises(AccessDenied):
                    a.get(field)
                rows = audit(engine, world.run)[before:]
                assert [(r.role, r.stage, r.function, r.allowed) for r in rows] == [(role, stage, field, False)]
                assert rows[0].detail["actual_stage"] == stage and "not on the" in rows[0].detail["reason"]


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
            Access(engine, world.run, role, stage).get(field)
    rows = [(r.role, r.stage, r.function, r.allowed) for r in audit(engine, world.run)]
    assert rows == [("judge", "before_lock", "claim", False), ("planner", "anytime", "claim", False),
                    ("planner", "before_lock", "everything", False)]


# --- Stages are read from the database; both sides of each checkpoint ------------------------

def test_a_declared_stage_is_checked_against_the_database(engine):
    world = aw.build(engine, "before_lock")
    with pytest.raises(AccessDenied, match="the run is at stage 'before_lock', not 'curation'"):
        access(engine, world, "critic", "curation").get("sources_meta")


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
    with pytest.raises(AccessDenied, match="at stage 'curation'"):
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
        with pytest.raises(AccessDenied, match="at stage 'analysis'"):
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
    with pytest.raises(AccessDenied, match="at stage 'final_without_freeze'"):
        gap.get("claim")
    assert commentator.get("outcome") == {"status": "completed", "outcome": "insufficient", "verdict": None,
                                          "exploratory": False}
    with pytest.raises(AccessDenied, match="at stage 'final_without_freeze', not 'final'"):
        access(engine, world, "commentator", "final").get("results")


def test_completion_after_a_freeze_moves_access_to_the_commentator_only(engine):
    world = aw.build(engine, "analysis")
    analyst = access(engine, world, "analyst", "analysis")
    commentator = access(engine, world, "commentator", "final")
    with pytest.raises(AccessDenied):
        commentator.get("results")
    assert analyst.get("results")
    world.w.complete(world.run, "partly_sufficient")
    with pytest.raises(AccessDenied, match="at stage 'final'"):
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
            Access(engine, flagged, "planner", "before_lock").get(field)


# --- What each field contains -----------------------------------------------------------

def test_sources_meta_is_exactly_the_named_plain_fields(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("sources_meta")
    assert SOURCE_META_FIELDS == ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                                  "fields_available")
    assert [list(s) for s in got] == [list(SOURCE_META_FIELDS)]
    assert got[0]["key"] == "mpea"  # the chosen source only: tamu_fcc was not selected for this run


def test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim(engine):
    world = aw.build(engine, "curation")
    got = role_input(access(engine, world, "curator", "curation"))
    assert got["plan_fields_to_extract"] == ["grain_size", "yield_strength", "composition"]
    assert [s["key"] for s in got["sources_meta"]] == ["mpea"]
    assert list(got["source_content"]["files"]) == ["mpea_planted.csv"]
    without_files = json.dumps({k: v for k, v in got.items() if k != "source_content"})
    assert "ZQXDIR" not in without_files and "rises" not in without_files and "k > 0" not in without_files
    assert b"ZQXDIR" not in got["source_content"]["files"]["mpea_planted.csv"]
    other = access(engine, world, "curator", "curation", source_key="tamu_fcc")
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
        assert set(r) == {"id", "source", "origin", "item_index", "kind", "alloy", "composition", "paper_reference",
                          "paper_doi", "status", "categories"}
        assert set(r["status"]) == set(HARMONIZED_FIELDS)
        assert set(r["status"].values()) <= {"converted", "not_reported", "not_convertible", "assigned", None}
        assert all(v is None or isinstance(v, str) for v in r["categories"].values())
    planted = [r for r in got if r["status"]["yield_strength"] == "not_convertible"]
    assert len(planted) == 1  # the unreadable cell: its reason (which quotes it) is withheld


def test_flags_kind_has_no_numbers(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("flags_kind")
    assert got == [{"id": world.flags[0], "kind": "values_disagree", "category": "differ beyond tolerance",
                    "records": got[0]["records"]}]
    assert len(got[0]["records"]) == 2


def test_the_plan_is_projected_by_its_named_parts(engine):
    world = aw.build(engine, "analysis")
    got = access(engine, world, "analyst", "analysis").get("plan")
    assert set(got["content"]) <= set(PLAN_KEYS) and "unnamed_key" not in got["content"]
    assert got["content"]["fields_to_extract"] == ["grain_size", "yield_strength", "composition"]
    assert got["minimums"] == {"records": 4, "alloys": 1, "groups": 2, "resid_df": 1}


def test_tag_values_are_the_approved_lists_only(engine):
    world = aw.build(engine, "before_lock")
    assert access(engine, world, "planner", "before_lock").get("tag_values") == [
        {"kind": "property", "value": "yield strength"}]


def test_record_counts_are_counts_from_the_sealed_source(engine):
    world = aw.build(engine, "before_lock")
    got = access(engine, world, "planner", "before_lock").get("record_counts")
    assert [c["source"] for c in got] == ["mpea"] and got[0]["readable"]
    c = got[0]
    assert c["n_records"] == 8  # four real rows and four planted ones
    assert c["by_status"]["yield_strength"] == {"converted": 7, "not_convertible": 1}
    assert c["by_category"]["test_type"]["tension"] >= 3
    assert set(c["by_category"]) == set(allowlist.CATEGORY_FIELDS)
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
        with pytest.raises(OperationalError, match="lock timeout"):
            Access(engine, world.run, "critic", "curation", lock_timeout_ms=300).get("flags_kind")
        tx.rollback()
    holder.dispose()
    assert len(audit(engine, world.run)) == before  # nothing was read, nothing logged
    assert Access(engine, world.run, "critic", "curation").get("flags_kind")
    assert layer.ACCESS_LOCK_TIMEOUT_MS == 5000


def test_an_access_call_waits_for_a_writer_holding_the_run_lock(engine):
    world = aw.build(engine, "curation")
    holder = make_engine(engine.test_url)
    result = {}
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        reader = threading.Thread(target=lambda: result.update(
            got=Access(engine, world.run, "critic", "curation").get("flags_kind")))
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
    a = Access(engine, world.run, "critic", "curation")
    a.get("flags_kind")
    with pytest.raises(AccessDenied):
        a.get("records_full")
    assert calls == [engine, engine]


def test_the_access_transaction_calls_hc_write_lock_before_anything_else():
    src = Path(layer.__file__).read_text()
    body = src[src.index("def _call"):src.index("def _refusal")]
    statements = [line.strip() for line in body.splitlines() if "conn.execute" in line or "actual_stage(" in line]
    assert "SET LOCAL lock_timeout" in statements[0]
    assert "hc_write_lock(p_run => :r)" in statements[1]
    assert "actual_stage(" in statements[2]


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


def test_pipeline_code_reaches_data_only_through_the_access_layer():
    """Agents and the pipeline (steps 6-8) import no database, source or file API."""
    forbidden = ("sqlalchemy", "psycopg", "hypocurate.db", "hypocurate.sources.versions",
                 "hypocurate.sources.adapters", "pathlib", "io", "shutil", "glob")
    for path in sorted((REPO / "hypocurate" / "pipeline").rglob("*.py")):
        tree = ast.parse(path.read_text())
        bad = {m for m in _imports(tree) if any(m == f or m.startswith(f + ".") for f in forbidden)}
        assert not bad, f"{path}: {bad}"
        assert "open" not in _calls(tree), path


def test_the_access_layer_has_no_function_that_takes_a_path():
    for name in ("allowlist", "errors", "fields", "inputs", "layer", "stage"):
        tree = ast.parse((REPO / "hypocurate" / "access" / f"{name}.py").read_text())
        assert not {"open", "read_bytes", "read_text", "Path", "listdir", "scandir"} & set(_calls(tree)), name
        assert not {"pathlib", "io", "glob", "shutil"} & _imports(tree), name
    assert list(Access.__init__.__code__.co_varnames[:7]) == [
        "self", "engine", "run_id", "role", "stage", "source_key", "lock_timeout_ms"]


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

### `tests/test_access_planted.py`

```python
"""Step 5: the planted-value test (PRD 4 testing requirement; criterion 14.2, second point).

Distinctive outcome values are planted everywhere the main run stores them
(`access_world`). None may appear, in any encoding we can reasonably anticipate, anywhere
in the complete input of the Planner (before the rules lock), the Critic (between the lock
and the freeze) or the Analyst writing a gap report (a run that ended with no dataset
frozen; owner, 2026-10-05). A positive control shows the detector finds the values where
they are allowed (the Analyst after the freeze).

Single-run scope (owner's addition A): a different value, planted in the original run of
the narrower question and in an earlier run of the same hypothesis, appears in no role's
complete input at any stage.

What "any encoding" covers: the value's decimal text at full precision and rounded to 2, 1
and 0 decimals; its integer part; thousands separators (comma, space, thin space) and a
decimal comma; scientific notation at several precisions; `g` formats; the value in GPa,
ksi and psi; `float.hex`; the IEEE-754 bytes (both byte orders) in hex and base64; the
decimal text in base64, hex and URL encoding. Only encodings of at least five characters
are searched, so that short fragments (for example "48.2") cannot match unrelated text by
chance. The input is searched as JSON (keys and values, with and without ASCII escapes),
as its Python repr, and case-insensitively.
"""
from __future__ import annotations

import base64
import json
import struct
import urllib.parse

import pytest
from sqlalchemy import text

import access_world as aw
from hypocurate.access import Access, role_input
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


def inputs_of(engine, world, role, stage):
    return role_input(Access(engine, world.run, role, stage, source_key="mpea" if role == "curator" else None))


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
    world = aw.build(engine, "curation")
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
        assert count("SELECT count(*) FROM stage_result WHERE output::text LIKE :v AND reasoning LIKE :v "
                     "AND tool_calls::text LIKE :v AND input::text LIKE :v") == 1
        assert count("SELECT count(*) FROM agent_setting WHERE instruction LIKE :v") == 1
        assert count("SELECT count(*) FROM tag_value WHERE value LIKE :v AND status = 'proposed'") == 1
        assert count("SELECT count(*) FROM source WHERE address LIKE :v") == 1
        assert count("SELECT count(*) FROM source_version WHERE label LIKE :v") == 1
        assert count("SELECT count(*) FROM plan WHERE content::text LIKE :v") == 1


def test_no_planted_value_in_the_planners_complete_input(engine):
    world = aw.build(engine, "before_lock")
    got = inputs_of(engine, world, "planner", "before_lock")
    assert set(got) == allowed("planner", "before_lock")
    assert got["record_counts"][0]["n_records"] == 8  # it did read the planted source
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_critics_complete_input(engine):
    world = aw.build(engine, "curation")
    got = inputs_of(engine, world, "critic", "curation")
    assert set(got) == allowed("critic", "curation")
    assert len(got["record_metadata"]) == 8 and got["flags_kind"]
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_gap_report_input(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = inputs_of(engine, world, "analyst", "closed_without_freeze")
    assert set(got) == allowed("analyst", "closed_without_freeze")
    assert got["condition_summaries"]["overall"]["n_records"] == 8
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_commentators_input_without_a_freeze(engine):
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
    meta = Access(engine, world.run, "planner", "before_lock").get("sources_meta")
    assert leaks(meta, aw.PLANTED.values()) == []
    assert "example.org" not in json.dumps(meta) and "label" not in json.dumps(meta)


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

### `tests/test_access_files.py`

```python
"""Step 5: the approved input files of pipeline code (`hypocurate.access.file_guard`).

Each test starts real guarded processes (`run_guarded`) and probes them from inside
(`hypocurate.access.guard_probe`). Under the guard: answer material (`tests/`), review
documents (`docs/reviews/`), the frozen files (`data/`) and the repository root cannot be
read or listed, by any of Python's ways of opening a file; writes outside the private
scratch directory are refused; no other program can be started and no native code loaded.
The things pipeline code needs still work: the web templates render, the database driver
connects, an HTTPS client loads its certificate bundle, a library can write its cache in
the scratch directory, and a role's complete input is built through the access layer.
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
from hypocurate.access import Access, file_guard, role_input
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


def test_no_other_program_and_no_native_code():
    results = probe([{"op": "subprocess"}, {"op": "system"}, {"op": "ctypes"}])
    assert results[0] == "refused: file guard: subprocess.Popen is outside the approved inputs of pipeline code"
    assert results[1] == "refused: file guard: os.system is outside the approved inputs of pipeline code"
    assert results[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code"


def test_templates_database_and_certificates_work_under_the_guard(migrated_database):
    """Owner's addition C: the guard is not bought by breaking what pipeline code needs."""
    results = probe([{"op": "render"}, {"op": "database"}, {"op": "certificates"}], migrated_database)
    assert results == ["ok True", "ok True", "ok True"]


def test_source_registration_cannot_run_under_the_guard():
    result, = probe([{"op": "register"}])
    assert result == ("error: RegistrationError: source registration reads data/ and cannot run in a guarded "
                      "pipeline process (step 5)")


def test_a_roles_complete_input_is_the_same_inside_the_guard(migrated_database):
    engine = make_engine(migrated_database)
    world = aw.build(engine, "before_lock")
    expected = role_input(Access(engine, world.run, "planner", "before_lock"))
    engine.dispose()
    got, = probe([{"op": "role_input", "run": world.run, "role": "planner", "stage": "before_lock"}],
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
index 107172c..abacef3 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,7 @@ HypoCurate takes a scientific hypothesis in words, searches registered data sour
 
 ## Status
 
-Build step 4 of 12 (PRD Section 15): sources and harmonization. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), plus the three sources registered as sealed versions, one adapter per source and "test connection" (step 4). The access layer, the pipeline and the screens come in later steps.
+Build step 5 of 12 (PRD Section 15): the access layer. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), plus the access layer with its audit log and the file guard for pipeline processes (step 5). The pipeline, the agents and the screens come in later steps.
 
 ## Set up secrets (once)
 
@@ -138,3 +138,19 @@ hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common re
 - "Test connection" runs in a read-only transaction.
 - The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
 - Not yet run on the live database: registering there is a later step and needs the owner.
+
+## Access layer
+
+Every agent reads data only through an access object built for its role, its stage and one run (`hypocurate/access/`; PRD 4). There is no agent yet (step 8).
+
+```python
+from hypocurate.access import Access, AccessDenied, role_input
+critic = Access(engine, run_id, "critic", "curation")
+critic.get("flags_kind")        # kind, category and record ids; never the numbers compared
+role_input(critic)              # everything the Critic may receive at this stage
+```
+
+- **Allowed fields, not blocked fields.** `hypocurate/access/allowlist.py` lists the fields each role may receive at each stage; anything else raises `AccessDenied`. Each field is built from named keys only (`fields.py`). Every field reads only the run's own rows.
+- **Stages come from the database**, on every call: before the rules lock, curation, analysis (after the freeze), closed without a freeze (gap report), final (completed after a freeze) and final without a freeze (completed with none; the Commentator then gets only the gap-report input, the Analyst's gap report and the run's outcome). Queued and failed runs give nothing.
+- **Every read and every refusal is logged** in `audit_log` (role, stage, field, allowed or denied, and the reason; never a value). Each call is one `run_transaction` that calls `hc_write_lock(p_run => …)` first. A refusal is committed before `AccessDenied` is raised, so the row survives it. Never call the access layer while holding the same run's lock: the call would wait, and fails after 5 seconds.
+- **Pipeline runs execute in a guarded process.** `run_guarded("hypocurate.<module>:<function>", payload)` starts `python -m hypocurate.access.guarded`, which installs an irreversible audit hook: it may read only the Python installation and the package's code, and write only in a private scratch directory (`TMPDIR`, `MPLCONFIGDIR` and `XDG_CACHE_HOME` point at it). `tests/`, `docs/`, `data/` and the repository root cannot be read or listed; other programs and `ctypes` are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. Source registration refuses to run in that process. The web service, the migrations, the `sources` commands and the tests are not guarded. The hook sees what Python code opens, not what C libraries open themselves; it is not an operating-system sandbox.
````
