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
