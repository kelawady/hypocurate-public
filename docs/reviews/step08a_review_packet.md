# Build step 8a — review packet

Date: 2026-10-06. Branch: `step-08a-curator`, from `main` at `cd2b3be`. Head when generated: `ea1a295`. Generated from the files on disk by a script (`~/hc-work/step08a/packet.py`, quoted in section 11), so every diff and output below is quoted exactly. Left out: the frozen documentation files themselves (listed with their SHA-256 in section 5) and the full lock-file diffs (the added packages are listed in section 2).

## How to use this packet

Step 8a builds the agents' foundation and the Curator at source registration (the owner's decisions of 2026-10-06). It holds safeguard changes (migration 0005; the Curator's access; the spending caps; plan validation and eligibility rule 3; the guarded runner), so please review against `docs/reviews/checklist.md` and answer the questions at the end of the summary (section 1). Section 2 is the code diff; 3 the new test files; 4 the changed tests; 5 the register, manifest and frozen curation; 6 the reference comparison with `main`; 7 the live curation call; 8 the mutation checks; 9 the new tests on `main`'s code; 10 the suite; 11 the scripts.


## 1. The summary

# Build step 8a — summary for review

Date: 2026-10-06. Branch: `step-08a-curator` (from `main` at `cd2b3be`). **Status: built; the whole suite passes (1,342 locally and 1,342 in the rebuilt test image); pushed; not merged** (owner's instruction: "When 8a is built: full suite, summary, review packet, push, and stop. Do not merge."). Part 8b (Planner, partly sufficient, Critic, Analyst, orchestration, command-line runs) waits for the owner's separate approval after 8a is merged.

PRD Section 15, step 8 ("Agents"), split by the owner into 8a and 8b because it held six safeguard changes and a migration. **8a: the foundation and the Curator.** It contains these **safeguard changes, which need the second model's review before any merge** (CLAUDE.md, "How we work" item 5): migration 0005; the Curator's registration binding and fields, and the removal of its run-stage field; the spending caps; plan validation and eligibility rule 3 (temperature bands); the guarded runner's handling of missing import-path entries.

**Not changed:** `render.yaml`, `.github/workflows/`, the Dockerfile, Compose (checked with `git diff --name-only cd2b3be..HEAD`). Dependencies changed (below). No PRD document is changed; corrections are listed at the end.

## The owner's decisions (2026-10-06)

From the step 8 brief and planning (one question at a time):

- **Q1, documentation.** Each source's documentation is frozen into its source version: Texas A&M `paper/main.tex` and `paper/supplementary.tex` from the pinned Zenodo archive (MIT; archive MD5 matches the manifest), and the MPEA paper's full text from Europe PMC (PMC7722748, CC BY 4.0).
- **Q2, the Curator.** It runs when a source version is registered, never during a run; no run depends on live model output for any record value. A proposal takes effect only when a person accepts it (quote shown beside it); value, quote, acceptor and time are sealed into the source version. Two checks first: the quote exists in the sealed document, and it contains a listed term for the value. A rejected or unanswered proposal leaves the field unassigned. Values "assigned by decision" stay owner decisions.
- **Q3, compilations.** Only sources grouped by dataset are curated (Texas A&M). A source grouped by paper is refused before any model call.
- **Q4, temperature bands.** One band per plan (room temperature, elevated, cryogenic); another band than room temperature names the claim's temperature range in the plan's rules.
- **Q5–Q6, Q8, Q10** (partly sufficient, the Analyst's inputs, the Commentator deferred to step 12, the narrower question on the command line) apply to 8b.
- **Q7, models.** Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5.
- **Q9, live costs.** The live test set (8b) at most $2; the curation call at most $0.50; enforced in code on the reserved maximum.
- **Owner's additions** (named constant for a partly-sufficient original; the Critic's class read by no decision; no outcome-derived numbers in the Analyst's facts below the minimums; the price check before the first live call). The first three are 8b; the fourth was done (below).
- **During the build:** drop import-path entries that do not exist in the guarded process (rather than preload the libraries); narrow `test_test_tools_are_not_in_the_runtime_lock` so pyyaml may be in the runtime lock only as a dependency of litellm or huggingface-hub; the curation decisions (below).

## What was built (per milestone; each commit on the branch)

| Milestone | Commit | What |
|---|---|---|
| 1 | `b89f376` | dspy 3.4.0 and litellm 1.104.0 locked (53 new packages, no existing pin changed). `pipeline/agents/libraries.py`, the only module that imports them: `LITELLM_MODE=PRODUCTION` first (litellm otherwise reads a `.env` file at import; **the file guard caught it reading the repository's `.env`**), the local price map, litellm's retries off, DSPy's caches off. The guarded child drops missing import-path entries before installing the guard. Documentation frozen under `data/sources/*/documentation/` (not `docs/`: the runtime-image check forbids any docs directory), in a per-source `documentation` list in the manifest. |
| 2 | `8262bdb` | Migration 0005 (below). |
| 3 | `344ad4b` | The Curator's access at stage `registration` (no run): `source_documentation` and `curation_targets` only; nothing at any run stage. `dispatch.bind_invocation`: run or version, role, setting and source from one invocation record. Registration reads take no lock (a sealed version never changes) and check in their transaction that the invocation is a registration invocation of the role on that sealed version. |
| 4 | `a71ea84` | The agent core: `prices.py`, `spend.py`, `lm.py` (`RecordedEngine`, a DSPy engine on DSPy's supported interface), `interface.py` (`call_agent`, the common interface), `settings.py`, `quotes.py`. |
| 5 | `f5fdf61` | Registration with documentation (each file with its role); adapters read only data files; `sources/curated.py` (a sealed curation applied where the table gives no value); the Curator (`pipeline/agents/curator.py`) and the workflow (`sources/curation.py`); the `sources` commands. |
| 6 | `6877d9f` | Plans for other temperature bands. |
| 7 | `6598951` | The register (122 entries, none open); the price check; the reference comparison with `main`. |
| 8 | `dd613d1` | The live curation call, the owner's decisions, the frozen `curation.json`, Texas A&M adapter version 3, the comparison again. |

## Migration 0005

Additive; 0001–0004 untouched; the two replaced model-call functions keep every check of 0001 (tested textually and verbatim for the downgrade).

| Change | Why |
|---|---|
| `source_file.role` ('data' default, 'documentation', 'curation'), with the path rule by role under 0001's constraint name | Documentation and curation files in the sealed version; a path tells its role, so the files digest (sorted paths and hashes, unchanged) stays unambiguous. |
| `agent_invocation` ('run': its (run, role, setting) must be one recorded at dispatch, a running stage of the run with that role, the model-call run rule; 'registration': the Curator on a sealed version). Append-only. | One invocation record per agent call (step 5 re-check). |
| `model_call.invocation_id`, required by `ck_model_call_with_invocation` (named to sort after 0001's checks, so their refusals keep their messages); `run_id`/`stage_result_id` NULL exactly for a registration call; a run call must have its invocation's run, stage and role; a registration call can never be moved to a run. | Every call recorded, including the Curator's, which has no run. |
| `curator_proposal` ('proposed' only if the database itself finds the quote, whitespace collapsed, in the named documentation file of the invocation's version and the term in the quote; quote 30–1500 characters; 'refused' with a code; 'not_stated' empty) and `curator_decision` (one per proposal that passed, by a named person, at the database's time). Append-only. | Q2. |

Works with the previous release's code (it inserts source files without a role and writes nothing else 0005 adds). The downgrade refuses while anything 0005 added is in use, then restores 0001's functions and path rule exactly.

## The request path (every agent call)

1. **Reserve** (`spend.reserve`): one transaction (a run call takes the run's lock first, then one month-wide advisory lock) checks the caps ($2 per run, $2 per curation, $50 per calendar month UTC, and an optional lower ceiling) against every recorded call at its reported cost or, while none is known, its maximum; records the call as started with its maximum cost; commits. A refusal sends nothing and is logged.
2. **Send** once through DSPy's own litellm engine, **outside any database transaction** (tested with `pg_stat_activity` while the stub holds the request).
3. **Record** (`spend.finish`): reported usage and its cost from the price table, or failed with no usage and a fixed code. No provider, library or database text is kept or sent later; the original goes to the process log only.
4. **Failure policy** (at most two requests per agent call): unavailable provider (connection, timeout, 429, 5xx, a reply litellm cannot read) → the same request once more; unusable answer (empty, malformed, a tool call, truncated, over-long) → once more with a fixed corrective note naming only the code; refused credentials, other refused requests, refusals, unknown cost, failed recording, spending refusals → stop. DSPy's JSON fallback is off.

**The maximum cost** reserved: the request's UTF-8 JSON bytes (a token is never shorter than a byte) plus 1000 tokens of framing at the input price, and the output limit at the output price. **The price check** (owner's addition 4): the table matches Anthropic's published pricing (https://platform.claude.com/docs/en/about-claude/pricing, read 2026-10-06) for every price, including the cache prices first marked as assumed.

## The live curation call and the owner's decisions (2026-10-06)

On the local development database (migrated to 0005; not the live site), with the owner's key entered by the owner in `.env` and passed to the command without being read or printed: `hypocurate sources curate tamu_fcc --ceiling 0.50`.

- **One request, first attempt.** Claude Sonnet 5.5: 61,537 input tokens, 262 output tokens; **actual cost $0.125694** (maximum reserved $0.378166).
- **Proposals** (code's checks):

| # | Field | Value | Where (found by code) | Status | Owner |
|---|---|---|---|---|---|
| 5 | test type | tension | main.tex line 177: "Quasistatic tensile testing was used to determine 0.2\% offset YS, while Vickers indentation tests provided the HV." | proposed (term "tensile") | **accepted** |
| 2 | phase class | FCC | main.tex line 173: "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system." | proposed (term "FCC") | **accepted** |
| 1 | microstructure | FCC | main.tex line 173 (the same sentence) | proposed | **rejected** ("the sentence states the phase class, not a single-phase microstructure as a result"; the microstructure stays assigned by decision) |
| 3 | test temperature | — | — | not stated | — |
| 4 | temperature band | — | — | not stated | — |

The two accepted quotes are word for word the passages the adapter cited by hand before. `seal-curation` sealed version 2 (`2fad3ccb…`); `export-curation` wrote `curation.json`, now frozen as `data/sources/tamu_fcc/curation.json` (manifest list `curation`). **Registering the frozen source reproduces exactly that fingerprint** (tested), so every database gets the same curated version with no model call. **Texas A&M adapter version 3** no longer assigns test type or phase class; they come from the curation.

## Reference numbers

Compared with `main` (`cd2b3be`, a separate checkout), on the five runs of `test_reference_numbers.py`, after milestone 7 and again after milestone 8 (adapter version 3 with the curation):

- **Identical:** every count (records, alloys, groups, informative groups, residual df), label and reason, both validity checks, the minimums, the withheld state; every decision's outcome, verdict, exploratory label, evidence level and wording; every run row.
- **Checked structurally** by `compare_v3.py` (packet, sections 6 and 11): 784 comparisons of counts, checks, minimums, labels, reasons, degrees of freedom and significance across every analysis of the five runs, all identical. (A first version of this check, used at milestone 7, looked up the counts under the wrong keys and so compared nothing; the conclusion then rested on the leaf-by-leaf comparison alone, which showed no count among the differing values. Corrected before this packet.)
- **Pooled and per-source results: bit-identical.**
- **Four sensitivity sets** (tension and compression, six batches, scope not confirmed included, without the group with the largest share) differ in the last one or two digits: at most **8.7e-15 relative**. Records are ordered by stable identity, which begins with the source-version fingerprint; the versions now hold documentation (and the Texas A&M version its curation), so the summation order changed. **Every approved number is unchanged at its stated precision**; `test_reference_numbers.py` passes unchanged.
- **Calibration:** new random draws (the seed comes from the freeze fingerprint). No flag changed in any of the 12 analyses. The largest difference among the 22 computed shares is |z| = 2.84 (with 22 comparisons, about a one-in-ten chance by noise); the pooled no-effect shares are fixed 7.25% → 8.45% and estimated 8.85% → 7.75%.

## Tests

The whole suite passes: 1,342 locally and 1,342 in the rebuilt test image (packet, section 10). **New test files:** `test_agent_libraries.py` (5), `test_migrations_step8a.py` (25 functions, 49 cases), `test_access_curator.py` (7), `test_agent_core.py` (21 functions, 29 cases), `test_curator.py` (15 functions, 20 cases), `test_temperature_range.py` (9 functions, 27 cases); `tests/stub_provider.py`, a local stand-in for the provider's API that litellm really calls, so every request test checks the actual outbound bytes.

**Failed before the code:** each new test file was written before its code and failed on it (counts in each commit message), except named guards (the import scan; the room-temperature behaviour and the reference plan's fingerprint).

**Mutation checks** (scratch copy, `PYTHONPATH`, each run alone; all 39 re-run on the final tests and caught, control run clean; packet, section 8): g01–g03 (guard path filter, `LITELLM_MODE`), d01–d08 (0005's rules), a01–a05 (registration access), c01–c10 (agent core; **c02, the month lock, first survived** the race test, which can pass by timing; a deterministic lock test was added), u01–u07 (Curator; **u05, rejected values sealed, first survived**: the seal test had no rejected decision; one was added), t01–t06 (temperature range).

**Changed tests (none removed or weakened; each because a decision changed its premise):**
- Step 1 manifest: the pinned hash and the required files (documentation, curation); a new documentation-origin test and a curation test.
- `test_skeleton`: pyyaml allowed only as a runtime library's dependency (owner); `SECRET_NAMES` gains `ANTHROPIC_API_KEY`.
- Every model call now has an invocation: `model_builder` (agent settings at dispatch with `agents=True`; `call()` creates the invocation and defaults to the stage's role), ten model-call tests ask for `agents=True`, `test_model_call_usage_rules`' last assertion (the mismatch is refused by the invocation check before the foreign key), `test_migrations.expected_triggers` (0005's triggers), `test_migrations_step7` (0004 no longer the head).
- The Curator is no longer a run role: the allow-list test, the outcome-field list (`source_documentation`), the rules-lock and freeze tests, the run-stage Curator test replaced by `test_the_curator_has_nothing_in_any_run`, `test_access_dispatch`, `test_access_code_roles`, and `test_access_projected`'s Curator branch, which no longer ran (the registration input is covered by `test_access_curator.py`).
- Registration stores documentation and curation: `test_source_versions` (paths with roles; 7 files).
- Temperature bands: `test_plan` (the default plan's rules are the schema's less the optional range; a cryogenic band without a range is refused for the missing range).
- Adapter version 3: `test_adapter_tamu` (test type and phase class from the curation; a constructed workbook without curation leaves them not reported), `test_checkpoints` (adapter version "3"), `pipeline_world.registered_files` (a constructed Texas A&M version holds the frozen curation, like the real source), `test_curator` (`register_base`: the uncurated version a curation starts from; the seal test's "never over an existing value" now uses the microstructure, which the decision sets).
- The register's pinned states (`test_assumptions`): no open entry; `PARTLY` gains `agent_models`; the page without the open-decisions heading; the "Not yet" display on a fixture entry.

## Assumptions register

122 entries: 121 in force, 0 open, 1 direction approved; 120 applied "yes", 2 "partly" (`constructed_test_runs`, `agent_models`). New: `source_documentation`, `curator_quote_checks`, `curation_acceptance`, `agent_models`, `model_prices`, `request_failure_policy`, `model_call_libraries`, `temperature_bands`. Decided: `curator_tabular_sources` (open wording in history). Reworded (earlier wording in history): `access_allow_lists`, `access_context_dispatcher`, `access_logging`, `spending_caps`, `tamu_test_type`, `tamu_phase_class`. Notes: `plan_named_parts`, `room_temperature_scope`, `pipeline_file_guard`, `code_vocabularies`, `tamu_microstructure`, `model_prices` (the price check).

**For the owner's review** (drafted by Claude Code, not yet decided by the owner): the Curator's term list (`quotes.TERMS`) and the quote bounds (30–1500 characters); the Curator's instruction text and limits (8000 output tokens, 20000 characters, effort medium).

## What this step does not do or claim

- The checks show that a quote exists in the sealed documentation and contains a listed term; **they do not show that the sentence supports the value**. That is the person's decision, with the quote beside it.
- The monthly cap counts the calls recorded in one database; calls from another database (local, test) do not count toward the live site's month.
- The maximum-cost bound assumes a token is never shorter than a byte of UTF-8; it is an upper bound, not an estimate.
- Tests use a local stub of the provider; the one live call is the curation above. A real provider's behaviour beyond it is not tested here.
- No agent runs inside a run yet (8b). No source is registered on the live database.

## Open items

1. **The time-zone read under the file guard.** In the guarded curation, psycopg looks up the session's time zone (`ZoneInfo("Etc/UTC")`), which reads `/usr/share/zoneinfo/Etc/UTC`; the guard refuses it, psycopg warns and falls back to UTC (the same zone). Harmless, but every guarded process logs one refusal. Remedies are guard changes for the owner: load the zone before installing the guard, or allow reading the time-zone folder.
2. **8b** (separate approval): Planner, `narrowing` and the partly-sufficient path, Critic, Analyst, orchestration, `run`/`show`/`dispatch`, criteria 14.1 and 14.3 from the command line, the live test set (≤ $2), migration 0006, the per-agent table for the Planner, Critic and Analyst.
3. **Live registration** of sources stays the owner's decision; the curated Texas A&M version is reproducible there from the frozen files.

## PRD corrections and clarifications (for the next PRD update)

1. PRD 3 step 5 / PRD 4 (Curator): the Curator does not extract tabular records (adapters do); it runs at source registration on the source's documentation, for sources grouped by dataset; its proposals take effect only when a person accepts them, and only where the table gives no value.
2. PRD 4 (access): the Curator's stage is registration (no run); access objects come from one invocation record (`bind_invocation`).
3. PRD 6 (agents): agents are DSPy modules on DSPy's engine interface; one HTTP request is one recorded model call; at most two requests per agent call.
4. PRD 7 (data model): `agent_invocation`, `curator_proposal`, `curator_decision`; `source_file.role`; `model_call.invocation_id`.
5. PRD 8 (spending caps): also $2 per curation; checked before each request.
6. PRD 5.1 / 5.2 (plan): one band per plan; elevated and cryogenic plans name a temperature range.
7. PRD 10 (Texas A&M): test type and phase class come from the owner's accepted curation of the source's documentation.

## Questions for the reviewer

1. **Access.** Can the Curator receive anything beyond its version's documentation and the target fields (a data row, an outcome value, the claim, the plan, another version's files), through its access list, the request the code builds, a retry, or an error? Is `bind_invocation` complete (run, setting and source only from the one invocation record)?
2. **Agents decide nothing.** Can a model's output reach a record value, a flag, inclusion, the test, sufficiency, the verdict or the evidence level by any path other than a person's acceptance of a proposal that passed both checks? Is "applied only where the table gives no value" enforced for every field?
3. **Migration 0005.** Do the new rules (invocations, registration calls, proposals, decisions, file roles) hold against direct SQL, and does every check of 0001 still apply to run calls? Is the downgrade exact?
4. **Spending.** Can a request be sent without a recorded reservation, or two reservations both pass a cap? Is the maximum-cost bound a true upper bound? Is any call ever counted below its maximum while its cost is unknown?
5. **Failure handling.** Does every failure mode have the stated outcome, and can any provider, library or database text reach a stored row or a later request?
6. **Temperature bands.** Do validation and eligibility rule 3 do what the register states, leaving room-temperature plans (and the reference plan) unchanged?
7. **Reproducibility.** Is the frozen curation a faithful, deterministic record of the owner's decisions, and does registering it reproduce the sealed curated version in any database?
8. Is any claim in this summary, the code, the README or the register stronger than the code supports?


## 2. Code diff (`cd2b3be..HEAD`; package, README, pyproject, .env.example)

Runtime lock: 53 packages added, none removed or changed in version (`test_skeleton` checks the locks): aiohappyeyeballs, aiohttp, aiosignal, attrs, boto3, botocore, cachetools, certifi, charset-normalizer, cloudpickle, diskcache, distro, dspy, fastuuid, filelock, frozenlist, fsspec, gepa, h2, hf-xet, hpack, httpcore, httpx, huggingface-hub, hyperframe, importlib-metadata, jiter, jmespath, json-repair, jsonschema, jsonschema-specifications, litellm, multidict, openai, orjson, packaging, propcache, pydantic-settings, python-dotenv, pyyaml, referencing, regex, requests, rpds-py, s3transfer, sniffio, tenacity, tiktoken, tokenizers, tqdm, urllib3, yarl, zipp.

````diff
diff --git a/.env.example b/.env.example
index aefe62c..50a11fb 100644
--- a/.env.example
+++ b/.env.example
@@ -12,3 +12,5 @@ SESSION_SECRET=
 POSTGRES_PASSWORD=
 # Only for running outside Docker, e.g. postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate
 DATABASE_URL=
+# The model provider's key for the agents (step 8). Set it yourself; it is never printed or logged.
+ANTHROPIC_API_KEY=
diff --git a/README.md b/README.md
index 5324b1d..c9667d1 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,7 @@ HypoCurate takes a scientific hypothesis in words, searches registered data sour
 
 ## Status
 
-Build step 7 of 12 (PRD Section 15): the statistics, the validity checks, data sufficiency, the verdict and per-run calibration. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), the access layer with its audit log and the file guard for pipeline processes (step 5), plus the plan model, the rules lock, record storage, the code checks that raise flags, the eligibility decisions and the dataset freeze (step 6), plus the supported model, the two validity checks, the fixed-minimum check, the verdict, per-run calibration both ways, the record of statistical significance, the gap facts and the copy of the decision onto the run (step 7). The agents, the worker, the screens, the plot and the workbook come in later steps.
+Build step 8a of 12 (PRD Section 15; step 8 is built in two parts): the statistics, the validity checks, data sufficiency, the verdict and per-run calibration. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), the access layer with its audit log and the file guard for pipeline processes (step 5), plus the plan model, the rules lock, record storage, the code checks that raise flags, the eligibility decisions and the dataset freeze (step 6), plus the supported model, the two validity checks, the fixed-minimum check, the verdict, per-run calibration both ways, the record of statistical significance, the gap facts and the copy of the decision onto the run (step 7), plus, in step 8a, the agents' request path (every model call reserved, sent once and recorded, with spending caps), the Curator at source registration and plans for other temperature bands. The run-time agents (Planner, Critic, Analyst) and the command-line run come in step 8b; the worker, the screens, the plot and the workbook in later steps.
 
 ## Set up secrets (once)
 
@@ -14,7 +14,7 @@ Build step 7 of 12 (PRD Section 15): the statistics, the validity checks, data s
 cp .env.example .env     # then fill in every value; .env is never committed
 ```
 
-`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`.
+`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`. `ANTHROPIC_API_KEY` is the model provider's key (step 8a): the owner enters it; it is never printed or logged, and the suite never needs it (tests use a local stub of the provider).
 
 ## Start the system locally
 
@@ -110,7 +110,8 @@ python -m hypocurate.db.migrate downgrade <revision> # drops tables and their da
 |---|---|
 | `data/manifest.json` | Fingerprint (SHA-256), size, licence, origin and retrieval date of every frozen file |
 | `data/sources/mpea/` | MPEA dataset (Borg et al. 2020), Apache-2.0 |
-| `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT |
+| `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT; `curation.json`: the Curator's values the owner accepted (step 8a) |
+| `data/sources/*/documentation/` | Each source's own documentation, sealed with its data (step 8a): the Texas A&M paper (LaTeX, MIT), the MPEA paper (Europe PMC XML, CC BY 4.0) |
 | `data/controlled_duplicates/` | Constructed extract for testing duplicate detection; see its README |
 
 To check that the origins still serve the same bytes (needs network; never overwrites the frozen copies):
@@ -139,6 +140,20 @@ hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common re
 - The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
 - Not yet run on the live database: registering there is a later step and needs the owner.
 
+## The Curator and the agents' request path (step 8a)
+
+The Curator runs when a source version is registered, never in a run, and only for a source grouped by dataset. It reads that version's documentation and proposes, for the fields a table may lack, one value with the exact sentence it relied on. Code checks each proposal (the quote occurs in the sealed documentation, whitespace collapsed; it contains a listed term for the value); a person accepts or rejects it; the accepted values are sealed into a new source version and applied only where the table gives no value.
+
+```
+hypocurate sources curate tamu_fcc --ceiling 0.50   # one model call (costs money); needs ANTHROPIC_API_KEY
+hypocurate sources proposals tamu_fcc               # proposals with quote, document, line and checks
+hypocurate sources accept 5 --by "Name" [--note …]  # or: reject
+hypocurate sources seal-curation tamu_fcc           # a new sealed version with curation.json
+hypocurate sources export-curation tamu_fcc --out data/sources/tamu_fcc/curation.json
+```
+
+Every agent call (`hypocurate/pipeline/agents/`) goes through one path: the call's maximum cost is reserved in one transaction that checks the caps ($2 per run, $2 per curation, $50 per month, or a lower ceiling) and records the call as started; the request is sent once, outside any transaction; the reported usage and its cost (from `prices.py`) are recorded. At most two requests per call: the same request again if the provider is unavailable, a fixed corrective note if the answer cannot be used, otherwise stop. Only `libraries.py` imports DSPy and litellm (it sets `LITELLM_MODE=PRODUCTION` first, so litellm never reads a `.env` file).
+
 ## Plan, checkpoints, inclusion and checks
 
 Code in `hypocurate/pipeline/` (step 6; PRD 5). No agent and no model call: plans are fixed inputs.
diff --git a/hypocurate/access/__init__.py b/hypocurate/access/__init__.py
index 27ce36b..e5aa90d 100644
--- a/hypocurate/access/__init__.py
+++ b/hypocurate/access/__init__.py
@@ -11,9 +11,9 @@
 - `file_guard` and `guarded`: a tripwire against accidental file access by pipeline code
   (not a sandbox).
 """
-from hypocurate.access.dispatch import bind
+from hypocurate.access.dispatch import bind, bind_invocation
 from hypocurate.access.errors import AccessDenied, AccessFailed
 from hypocurate.access.inputs import role_input
 from hypocurate.access.layer import Access
 
-__all__ = ["Access", "AccessDenied", "AccessFailed", "bind", "role_input"]
+__all__ = ["Access", "AccessDenied", "AccessFailed", "bind", "bind_invocation", "role_input"]
diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index 5ae91e5..e8f4cd4 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -53,7 +53,10 @@ ALL_ROLES = ROLES + CODE_ROLES
 # frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
 # closed_without_freeze: curation ended with no dataset frozen (insufficient), running.
 # final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
-STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")
+# registration (step 8a, owner 2026-10-06): not a run stage; the Curator reads one sealed source
+# version, bound by a registration invocation (`dispatch.bind_invocation`), with no run.
+STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze",
+          "registration")
 
 FIELDS = MappingProxyType({
     "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
@@ -65,8 +68,11 @@ FIELDS = MappingProxyType({
     "record_counts": "Per chosen source, computed by code from its sealed version: the number of records, "
                      "per field the count of each status, and per value of each non-outcome category field "
                      "the count of records.",
-    "plan_fields_to_extract": "From the locked plan, the list of fields to extract, and nothing else.",
-    "source_content": "The sealed files of the one source the Curator reads, as recorded for the run.",
+    "source_documentation": "For the Curator at registration (step 8a): the documentation files of the one "
+                            "sealed source version its invocation names, as text, with the source's key. "
+                            "No data file, no claim, no plan, no other version.",
+    "curation_targets": "For the Curator at registration (step 8a): the fields it may propose a value for, "
+                        "with each field's vocabulary or unit (vocabulary.CURATION_TARGETS).",
     "record_metadata": "Per stored record: id, source, item index, kind, alloy label and composition, DOI "
                        "(DOI syntax only), each field's status, and the non-outcome category values from "
                        "their vocabularies. No measured number of any field, no paper title, no origin key.",
@@ -120,8 +126,10 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
     "planner": MappingProxyType({
         "before_lock": frozenset({"claim", "domain", "sources_meta", "tag_values", "record_counts"}),
     }),
+    # Owner, 2026-10-06 (step 8a, Q2): the Curator runs when a source version is registered, never in a
+    # run. It reads that version's documentation and the target fields, and nothing at any run stage.
     "curator": MappingProxyType({
-        "curation": frozenset({"plan_fields_to_extract", "sources_meta", "source_content"}),
+        "registration": frozenset({"source_documentation", "curation_targets"}),
     }),
     "critic": MappingProxyType({
         "curation": frozenset({"sources_meta", "record_metadata", "flags_kind"}),
@@ -232,7 +240,10 @@ PLAN_SCHEMA = MappingProxyType({
               "survivor_source_order": ("list", SOURCE_KEYS), "min_grain_sizes": "integer",
               "room_temperature_min": "number", "room_temperature_max": "number", "single_phase": SINGLE_PHASE,
               "accepted_value_statuses": ("list", VALUE_STATUSES),
-              "grouping": ("list", {"source": SOURCE_KEYS, "unit": GROUPING_UNITS})},
+              "grouping": ("list", {"source": SOURCE_KEYS, "unit": GROUPING_UNITS}),
+              # Step 8a (owner, 2026-10-06, Q4): the claim's temperature range, exactly when the plan's
+              # band is not room temperature.
+              "temperature_range": {"min": "number", "max": "number"}},
     # Step 7 (owner, 2026-10-05): the calibration is fixed at the rules lock, both methods.
     "calibration": {"methods": ("list", CALIBRATION_METHODS), "n_simulations": "integer", "scatter": "number",
                     "shift": "number", "estimation": ESTIMATION_METHODS, "smallest_effect": "number"},
diff --git a/hypocurate/access/context.py b/hypocurate/access/context.py
index 5bfb67e..fe60f20 100644
--- a/hypocurate/access/context.py
+++ b/hypocurate/access/context.py
@@ -11,8 +11,12 @@ from dataclasses import dataclass
 
 @dataclass(frozen=True, slots=True)
 class AccessContext:
-    run_id: int
+    """A run context (run_id set), or, from step 8a, a registration context: no run, the Curator,
+    stage 'registration', the sealed source version its invocation names."""
+    run_id: int | None
     role: str
     stage: str
     source_key: str | None = None
     agent_setting_id: int | None = None
+    source_version_id: int | None = None
+    invocation_id: int | None = None
diff --git a/hypocurate/access/dispatch.py b/hypocurate/access/dispatch.py
index 188550d..7a710c3 100644
--- a/hypocurate/access/dispatch.py
+++ b/hypocurate/access/dispatch.py
@@ -6,8 +6,8 @@ anything a model controls:
 - the **role** is read from the run's recorded agent settings (`run_agent_setting`): the
   setting being invoked must be recorded for this run, and its role is the one recorded;
 - the **stage** is read from the database;
-- a **source** is bound only for the Curator, and must be one of the run's `run_source` rows
-  with a recorded version.
+- no run role is bound to a source (step 8a, owner 2026-10-06: the Curator reads a source version
+  at registration, never in a run; `source_not_for_role`).
 The result is an `Access` around an immutable `AccessContext`. The binding itself is
 logged (function "bind"): allowed, denied with its code, or failed. Every later read checks
 again that the run is still at the bound stage.
@@ -15,6 +15,12 @@ again that the run is still at the bound stage.
 Nothing a model controls ever receives SQL, a database connection or a file path (CLAUDE.md):
 agents get text built from `role_input` and from reads through this object only.
 
+`bind_invocation(engine, invocation_id)` (step 8a) binds one agent call from its invocation record
+alone (step 5 re-check: run, setting and source come from one record, never assembled
+separately): a run invocation binds as `bind` does, for its run and setting; a registration
+invocation binds the Curator to the one sealed source version it names, with no run (stage
+'registration'). Every bind is logged; an unknown invocation is a logged failure.
+
 `bind_code(engine, run_id, role)` (step 6, owner 2026-10-05) binds the two **code roles** of
 PRD 4, Inclusion and Checks, which have no agent setting. It is called by trusted pipeline
 code (`hypocurate.pipeline`) only. It refuses any other role (`not_a_code_role`), reads the
@@ -33,7 +39,7 @@ from hypocurate.access.allowlist import CODE_ROLES, allowed
 from hypocurate.access.context import AccessContext
 from hypocurate.access.errors import AccessDenied, AccessFailed
 from hypocurate.access.layer import (_AUDIT, _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, DENIALS, Access, _detail, _row,
-                                     bounded_source, keep_in_process_log, log_failure)
+                                     bounded_source, keep_in_process_log, log_failure, registration_stage)
 from hypocurate.access.stage import actual_stage
 from hypocurate.db.retry import run_transaction, sqlstate
 
@@ -41,11 +47,11 @@ UNBOUND = "invalid"  # the role logged for a binding refused before a role is kn
 
 
 def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | None = None,
-         lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
+         lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS, _invocation_id: int | None = None) -> Access:
     """An access object for one agent call, or AccessDenied / AccessFailed (logged)."""
     if not isinstance(run_id, int) or isinstance(run_id, bool) or not isinstance(agent_setting_id, int):
         raise TypeError("bind takes an integer run id and an integer agent setting id")
-    probe = AccessContext(run_id, UNBOUND, UNBOUND, source_key, agent_setting_id)
+    probe = AccessContext(run_id, UNBOUND, UNBOUND, source_key, agent_setting_id, invocation_id=_invocation_id)
 
     def transaction(conn: Connection):
         conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
@@ -55,19 +61,12 @@ def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | N
         stage = actual_stage(conn, run_id, status)
         role = conn.execute(text("SELECT role FROM run_agent_setting WHERE run_id = :r AND agent_setting_id = :a"),
                             dict(r=run_id, a=agent_setting_id)).scalar_one_or_none()
-        ctx = AccessContext(run_id, role or UNBOUND, stage, source_key, agent_setting_id)
+        ctx = AccessContext(run_id, role or UNBOUND, stage, source_key, agent_setting_id, invocation_id=_invocation_id)
         code = None
         if role is None:
             code = "setting_not_recorded"
-        elif role != "curator" and source_key is not None:
+        elif source_key is not None:
             code = "source_not_for_role"
-        elif role == "curator" and source_key is None:
-            code = "no_source"
-        elif role == "curator" and not conn.execute(text(
-                "SELECT EXISTS (SELECT 1 FROM run_source rs JOIN source s ON s.id = rs.source_id "
-                "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL)"),
-                dict(r=run_id, k=source_key)).scalar_one():
-            code = "source_not_recorded"
         extra = {"agent_setting": agent_setting_id}
         result = "denied" if code else "allowed"
         conn.execute(_AUDIT, _row(ctx, run_id, "bind", code is None, _detail(ctx, result, code, stage, **extra)))
@@ -91,6 +90,49 @@ def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | N
     return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)
 
 
+def bind_invocation(engine: Engine, invocation_id: int, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
+    """An access object for the agent call recorded by `invocation_id`, or AccessDenied / AccessFailed
+    (logged). Run, role, setting and source all come from that one record."""
+    if not isinstance(invocation_id, int) or isinstance(invocation_id, bool):
+        raise TypeError("bind_invocation takes an integer invocation id")
+    try:
+        row = run_transaction(engine, lambda conn: conn.execute(text(
+            "SELECT i.scope, i.run_id, i.role, i.agent_setting_id, i.source_version_id, s.key AS source_key "
+            "FROM agent_invocation i LEFT JOIN source_version sv ON sv.id = i.source_version_id "
+            "LEFT JOIN source s ON s.id = sv.source_id WHERE i.id = :i"), dict(i=invocation_id)).one_or_none())
+    except DBAPIError as error:
+        probe = AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id)
+        keep_in_process_log(probe, "bind", "database_error", error)
+        failure = True
+    else:
+        failure = False
+    if failure:
+        log_failure(engine, AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id), "bind", "database_error")
+        raise AccessFailed(UNBOUND, UNBOUND, "bind", "database_error")
+    if row is None:
+        log_failure(engine, AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id), "bind",
+                    "unknown_invocation", run_known=False)
+        raise AccessFailed(UNBOUND, UNBOUND, "bind", "unknown_invocation")
+    if row.scope == "run":
+        return bind(engine, row.run_id, row.agent_setting_id, lock_timeout_ms=lock_timeout_ms,
+                    _invocation_id=invocation_id)
+    ctx = AccessContext(None, row.role, "registration", row.source_key, row.agent_setting_id,
+                        source_version_id=row.source_version_id, invocation_id=invocation_id)
+
+    def transaction(conn: Connection):
+        stage = registration_stage(conn, ctx)
+        code = None if stage == "registration" else "stage_mismatch"
+        conn.execute(_AUDIT, _row(ctx, None, "bind", code is None,
+                                  _detail(ctx, "denied" if code else "allowed", code, stage,
+                                          agent_setting=row.agent_setting_id)))
+        return code
+
+    code = run_transaction(engine, transaction)
+    if code is not None:
+        raise AccessDenied(ctx.role, ctx.stage, "bind", code, DENIALS[code])
+    return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)
+
+
 def bind_code(engine: Engine, run_id: int, role: str, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
     """An access object for a code role (Inclusion or Checks), or AccessDenied / AccessFailed
     (logged)."""
@@ -133,4 +175,4 @@ def bind_code(engine: Engine, run_id: int, role: str, lock_timeout_ms: int = ACC
     return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)
 
 
-__all__ = ["bind", "bind_code", "bounded_source"]
+__all__ = ["bind", "bind_code", "bind_invocation", "bounded_source"]
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 2866d6f..639f133 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -171,8 +171,6 @@ def sources_meta(conn: Connection, ctx: Context) -> list[dict]:
     settings from the sealed version the run recorded. The source registry's text never."""
     out = []
     for row in _chosen_sources(conn, ctx):
-        if ctx.role == "curator" and row.key != ctx.source_key:
-            continue
         d = SOURCES.get(row.key)
         values = {"key": row.key,
                   "name": d.name if d else vocab.UNRECOGNIZED,
@@ -237,25 +235,19 @@ def project(value: Any, schema: Any) -> Any:
     raise ValueError(f"unknown schema leaf {schema!r}")
 
 
-def plan_fields_to_extract(conn: Connection, ctx: Context) -> list[str]:
-    """Only names of the common fields, in order, without repeats."""
-    content = _rows(conn, "SELECT content FROM plan WHERE run_id = :r", r=ctx.run_id)[0].content
-    listed = project(content, PLAN_SCHEMA).get("fields_to_extract", []) if isinstance(content, Mapping) else []
-    return list(dict.fromkeys(listed))
+def source_documentation(conn: Connection, ctx: Context) -> dict:
+    """The documentation files of the one sealed version the Curator's invocation names, as text
+    (step 8a). Never a data file and never another version."""
+    if ctx.source_version_id is None:
+        raise Refused("no_source")
+    version = load_sealed_version(conn, ctx.source_version_id)
+    return {"source": version.source_key,
+            "documents": {path: content.decode("utf-8") for path, content in sorted(version.documentation.items())}}
 
 
-def source_content(conn: Connection, ctx: Context) -> dict:
-    """The sealed files of the Curator's one source, from the version its run recorded."""
-    if ctx.source_key is None:
-        raise Refused("no_source")
-    vid = conn.execute(text(
-        "SELECT rs.source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
-        "WHERE rs.run_id = :r AND s.key = :k AND rs.source_version_id IS NOT NULL"),
-        dict(r=ctx.run_id, k=ctx.source_key)).scalar_one_or_none()
-    if vid is None:
-        raise Refused("source_not_recorded")
-    version = load_sealed_version(conn, vid)
-    return {"source": ctx.source_key, "files": dict(version.files)}
+def curation_targets(conn: Connection, ctx: Context) -> dict:
+    """The fields the Curator may propose a value for, with their vocabularies (step 8a)."""
+    return {field: dict(spec) for field, spec in vocab.CURATION_TARGETS.items()}
 
 
 def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
@@ -543,8 +535,8 @@ def frozen_analysis_data(conn: Connection, ctx: Context) -> dict:
 
 READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
-    "record_counts": record_counts, "plan_fields_to_extract": plan_fields_to_extract,
-    "source_content": source_content, "record_metadata": record_metadata, "flags_kind": flags_kind,
+    "record_counts": record_counts, "source_documentation": source_documentation,
+    "curation_targets": curation_targets, "record_metadata": record_metadata, "flags_kind": flags_kind,
     "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
     "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
     "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
diff --git a/hypocurate/access/guard_probe.py b/hypocurate/access/guard_probe.py
index 33c2686..a5aa9ad 100644
--- a/hypocurate/access/guard_probe.py
+++ b/hypocurate/access/guard_probe.py
@@ -147,6 +147,20 @@ def _role_input(action: dict) -> str:
     return out
 
 
+def _agent_libraries(_: Any) -> str:
+    """Loads the model-call libraries the way the agents do (step 8a)."""
+    from hypocurate.pipeline.agents import libraries
+    libraries.load()
+    return "ok"
+
+
+def _dotenv(action: dict) -> str:
+    """A library reading a `.env` file (step 8a): what the tripwire must still catch."""
+    import dotenv
+    dotenv.load_dotenv(action["path"])
+    return "ok"
+
+
 ACTIONS: dict[str, Callable[[dict], str]] = {
     "read": lambda a: _read(a["path"], a.get("how", "open")),
     "list": lambda a: _list(a["path"], a.get("how", "listdir")),
@@ -156,6 +170,7 @@ ACTIONS: dict[str, Callable[[dict], str]] = {
     "ctypes_from_address": _ctypes_from_address,
     "register": _register,
     "role_input": _role_input, "sleep": _sleep,
+    "agent_libraries": _agent_libraries, "dotenv": _dotenv,
 }
 
 
diff --git a/hypocurate/access/guarded.py b/hypocurate/access/guarded.py
index 9cdeb59..ad369dc 100644
--- a/hypocurate/access/guarded.py
+++ b/hypocurate/access/guarded.py
@@ -9,7 +9,10 @@ the target's JSON result. The child:
    `XDG_CACHE_HOME` at it, for libraries that need a cache or temporary files (the
    plotting library in step 7); its working directory is the scratch directory;
 2. removes the repository root from its import path (the `hypocurate` package is already
-   imported and keeps its own path), and imports the modules in `PRELOADED`;
+   imported and keeps its own path) and every import-path entry that does not exist (owner,
+   2026-10-06: otherwise each later import probes them, for example the standard library's zip,
+   and the guard refuses those probes, which would fill the audit log with refusals that are not
+   mistakes), and imports the modules in `PRELOADED`;
 3. installs the guard;
 4. imports the target, which must be inside the `hypocurate` package, calls it with the
    payload, writes the result to its standard output and exits.
@@ -117,6 +120,11 @@ def run_guarded(target: str, payload: Any = None, env: dict[str, str] | None = N
     return answer["result"]
 
 
+def existing_path_entries(paths: list[str]) -> list[str]:
+    """The import-path entries that exist, in order (step 8a, owner 2026-10-06)."""
+    return [p for p in paths if os.path.exists(p)]
+
+
 def _main() -> int:
     request = json.loads(sys.stdin.read())
     scratch = request["scratch"]
@@ -126,6 +134,7 @@ def _main() -> int:
     os.chdir(scratch)
     package_parent = os.path.dirname(file_guard.PACKAGE_DIR)
     sys.path[:] = [p for p in sys.path if p not in ("", ".") and os.path.realpath(p) != package_parent]
+    sys.path[:] = existing_path_entries(sys.path)
     sys.path_importer_cache.clear()
     for name in PRELOADED:
         importlib.import_module(name)
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index f255781..ef48263 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -44,6 +44,13 @@ in the database is therefore not unconditional.
 
 **Never call the access layer while holding the same run's lock**: the call would wait for
 it, and fails after the lock timeout (logged as a failure).
+
+**Registration reads** (step 8a, owner 2026-10-06): the Curator reads one sealed source version,
+with no run. Its context has no run and names the version and the registration invocation
+(`dispatch.bind_invocation`). Each read checks in its transaction that the invocation exists, is
+a registration invocation of this role on this version, and that the version is sealed; then the
+stage is 'registration', otherwise 'none'. A sealed version never changes, so there is no lock to
+take. Audit rows have no run; their detail names the version and the invocation.
 """
 from __future__ import annotations
 
@@ -77,14 +84,14 @@ DENIALS = {
     "not_on_list": "the field is not on the role's list at the run's stage",
     "no_source": "the Curator reads one named source; none was bound",
     "source_not_recorded": "the source is not recorded for this run",
-    "source_not_for_role": "only the Curator is bound to a source",
+    "source_not_for_role": "no run role is bound to a source (the Curator reads a source version at registration)",
     "setting_not_recorded": "the agent setting is not recorded for this run",
     "empty_list": "the role has no field at this stage",
     "checks_not_done": "no completed Checks result for this run",
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
     "not_frozen": "no dataset is frozen for this run",
 }
-FAILURES = ("unknown_run", "lock_timeout", "reader_error", "database_error", "file_guard")
+FAILURES = ("unknown_run", "unknown_invocation", "lock_timeout", "reader_error", "database_error", "file_guard")
 FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
 _SOURCE_KEY = re.compile(r"[a-z][a-z0-9_]{0,40}")
 
@@ -112,6 +119,10 @@ def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | Non
         d["actual_stage"] = actual
     if ctx.source_key is not None:
         d["source"] = bounded_source(ctx.source_key)
+    if ctx.source_version_id is not None:
+        d["source_version"] = int(ctx.source_version_id)
+    if ctx.invocation_id is not None:
+        d["invocation"] = int(ctx.invocation_id)
     for name, raw, valid in (("role", ctx.role, ALL_ROLES), ("stage", ctx.stage, STAGES)):
         if bounded(raw, valid) == "invalid" and raw != "invalid":
             d[f"given_{name}_length"] = len(raw) if isinstance(raw, str) else -1
@@ -130,7 +141,7 @@ def log_failure(engine: Engine, ctx: AccessContext, function: str, code: str, ru
     the process log if the database cannot take it."""
     run_id = ctx.run_id if run_known else None
     detail = _detail(ctx, "failed", code, **extra)
-    if not run_known:
+    if not run_known and ctx.run_id is not None:
         detail["requested_run"] = int(ctx.run_id)
     try:
         run_transaction(engine, lambda conn: conn.execute(_AUDIT, _row(ctx, run_id, function, False, detail)))
@@ -163,8 +174,11 @@ class Access:
                  _trusted: object = None):
         if _trusted is not _TRUSTED:
             raise TypeError("an access object is created only by hypocurate.access.dispatch.bind")
-        if not isinstance(context, AccessContext) or not isinstance(context.run_id, int):
-            raise TypeError("an access object needs an AccessContext with an integer run id")
+        if not isinstance(context, AccessContext) or not (
+                isinstance(context.run_id, int) or context.run_id is None
+                and isinstance(context.source_version_id, int) and isinstance(context.invocation_id, int)):
+            raise TypeError("an access object needs an AccessContext with an integer run id, or (registration) "
+                            "an integer source version and invocation")
         object.__setattr__(self, "_engine", engine)
         object.__setattr__(self, "_context", context)
         object.__setattr__(self, "_lock_timeout_ms", int(lock_timeout_ms))
@@ -211,9 +225,9 @@ class Access:
             log_failure(engine, ctx, field, code, **extra)
             raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), field, code)
         kind = outcome[0]
-        if kind == "unknown_run":
-            log_failure(engine, ctx, name, "unknown_run", run_known=False)
-            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), name, "unknown_run")
+        if kind in ("unknown_run", "unknown_invocation"):
+            log_failure(engine, ctx, name, kind, run_known=False)
+            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), name, kind)
         if kind == "denied":
             field, code = outcome[1]
             raise AccessDenied(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), bounded(field, FUNCTIONS),
@@ -222,10 +236,16 @@ class Access:
 
     def _transaction(self, conn: Connection, ctx: AccessContext, function: str, fields: tuple) -> tuple:
         conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
-        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=ctx.run_id)).scalar_one():
-            return ("unknown_run",)
-        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=ctx.run_id)).scalar_one()
-        actual = actual_stage(conn, ctx.run_id, status)
+        if ctx.run_id is None:  # a registration read (step 8a): no run, no lock; the invocation decides
+            actual = registration_stage(conn, ctx)
+            if actual is None:
+                return ("unknown_invocation",)
+        else:
+            if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"),
+                                dict(r=ctx.run_id)).scalar_one():
+                return ("unknown_run",)
+            status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=ctx.run_id)).scalar_one()
+            actual = actual_stage(conn, ctx.run_id, status)
         if not fields:  # role_input with nothing on the list: never an empty input
             code = ("unknown_role" if ctx.role not in ALL_ROLES else "unknown_stage" if ctx.stage not in STAGES
                     else "empty_list")
@@ -256,6 +276,19 @@ class Access:
         return ("allowed", values)
 
 
+def registration_stage(conn: Connection, ctx: AccessContext) -> str | None:
+    """'registration' when the context's invocation is a registration invocation of its role on its
+    version and that version is sealed; 'none' otherwise; None when there is no such invocation."""
+    row = conn.execute(text("SELECT i.scope, i.role, i.source_version_id, sv.sealed_at IS NOT NULL AS sealed "
+                            "FROM agent_invocation i LEFT JOIN source_version sv ON sv.id = i.source_version_id "
+                            "WHERE i.id = :i"), dict(i=ctx.invocation_id)).one_or_none()
+    if row is None:
+        return None
+    ok = (row.scope == "registration" and row.role == ctx.role and row.source_version_id == ctx.source_version_id
+          and row.sealed)
+    return "registration" if ok else "none"
+
+
 def _policy(ctx: AccessContext, field: str, actual: str) -> str | None:
     if ctx.role not in ALL_ROLES:
         return "unknown_role"
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index 163852f..3b70c57 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -36,6 +36,20 @@ CATEGORY_VOCABULARIES: Mapping[str, frozenset[str]] = {
 }
 
 
+# --- What the Curator may propose (step 8a; owner, Q2) -------------------------------------
+# Per target field: its vocabulary (a value must be one of these) or, for the test temperature, a
+# number in °C. The fields a table may lack; the Curator proposes a source-wide value for them only
+# where the table gives none. The same list is the database's (models.CURATION_FIELDS).
+CURATION_TARGETS: Mapping[str, Mapping[str, Any]] = {
+    "test_type": {"vocabulary": sorted(TEST_TYPES)},
+    "phase_class": {"vocabulary": sorted(PHASE_CLASSES)},
+    "test_temperature": {"unit": "°C"},
+    "test_temperature_band": {"vocabulary": sorted(TEMPERATURE_BANDS)},
+    "microstructure": {"vocabulary": sorted(MICROSTRUCTURE_TOKENS),
+                       "form": "one or more of the vocabulary joined by '+'"},
+}
+
+
 def category(field: str, value: Any) -> str:
     """A category value as a blinded view shows it: itself if it is in the field's
     vocabulary, otherwise `UNRECOGNIZED`."""
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 1063d67..321a3f7 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -1,5 +1,6 @@
 """The command-line entry point (PRD Section 12). Step 2: `version` and `check-db`.
-Step 4: `sources register` and `sources test`."""
+Step 4: `sources register` and `sources test`. Step 8a: the curation workflow at registration
+(`sources curate | proposals | accept | reject | seal-curation | export-curation`)."""
 from __future__ import annotations
 
 import argparse
@@ -22,6 +23,21 @@ def main(argv: list[str] | None = None) -> int:
     test = sources_sub.add_parser("test", help="read a source and show sample records")
     test.add_argument("key")
     test.add_argument("-n", type=int, default=5, help="number of sample records (default 5)")
+    curate = sources_sub.add_parser("curate", help="ask the Curator for values the documentation states (costs money)")
+    curate.add_argument("key")
+    curate.add_argument("--ceiling", help="the most this curation may cost, in USD (refused above it)")
+    listing = sources_sub.add_parser("proposals", help="list the Curator's proposals and decisions")
+    listing.add_argument("key")
+    for name in ("accept", "reject"):
+        p = sources_sub.add_parser(name, help=f"{name} one proposal that passed the checks")
+        p.add_argument("proposal", type=int)
+        p.add_argument("--by", required=True, help="the name of the person deciding")
+        p.add_argument("--note")
+    seal = sources_sub.add_parser("seal-curation", help="seal the accepted values into a new source version")
+    seal.add_argument("key")
+    export = sources_sub.add_parser("export-curation", help="write the curated version's curation.json")
+    export.add_argument("key")
+    export.add_argument("--out", help="the file to write (default: print it)")
     args = parser.parse_args(argv)
 
     settings = load_settings(web=False)
@@ -41,6 +57,8 @@ def _sources(args, engine) -> int:
     from hypocurate.sources.record import AdapterError
     from hypocurate.sources.versions import SOURCES, RegistrationError, UnsealedVersion, register
 
+    if args.sources_command in ("curate", "proposals", "accept", "reject", "seal-curation", "export-curation"):
+        return _curation(args, engine)
     try:
         if args.sources_command == "register":
             for key in args.keys or list(SOURCES):
@@ -58,5 +76,43 @@ def _sources(args, engine) -> int:
         return 1
 
 
+def _curation(args, engine) -> int:
+    from hypocurate.access.guarded import GuardedRunError, run_guarded
+    from hypocurate.sources import curation
+    from hypocurate.sources.versions import UnsealedVersion
+
+    try:
+        if args.sources_command == "curate":
+            try:
+                out = run_guarded("hypocurate.sources.curation:curate_guarded",
+                                  {"key": args.key, "ceiling": args.ceiling}, timeout=900)
+            except GuardedRunError:
+                # The child's error text may hold anything; it stays out of the output.
+                print("error: the curation did not finish (see the process log)", file=sys.stderr)
+                return 1
+        elif args.sources_command == "proposals":
+            out = curation.proposals(engine, args.key)
+        elif args.sources_command in ("accept", "reject"):
+            out = curation.decide(engine, args.proposal, args.sources_command + "ed", args.by, args.note)
+        elif args.sources_command == "seal-curation":
+            r = curation.seal_curation(engine, args.key)
+            out = {"key": r.key, "version": r.version_id, "label": r.label, "fingerprint": r.fingerprint,
+                   "created": r.created}
+        else:
+            content = curation.curation_file(engine, args.key)
+            if args.out:
+                with open(args.out, "wb") as f:
+                    f.write(content)
+                out = {"written": args.out, "bytes": len(content)}
+            else:
+                sys.stdout.write(content.decode("utf-8"))
+                return 0
+    except (curation.CurationRefused, UnsealedVersion) as refused:
+        print(f"error: {refused}", file=sys.stderr)
+        return 1
+    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
+    return 0
+
+
 if __name__ == "__main__":
     sys.exit(main())
diff --git a/hypocurate/db/migrations/versions/0005_agents_and_documentation.py b/hypocurate/db/migrations/versions/0005_agents_and_documentation.py
new file mode 100644
index 0000000..12b9a3c
--- /dev/null
+++ b/hypocurate/db/migrations/versions/0005_agents_and_documentation.py
@@ -0,0 +1,404 @@
+"""The agents' records and the source documentation (build step 8a).
+
+Revision ID: 0005
+Revises: 0004
+Create Date: 2026-10-06
+
+Approved by the owner on 2026-10-06 (step 8a plan), subject to the second-model review before
+merging. Additive: 0001 to 0004 are untouched; the two trigger functions replaced here keep every
+check of 0001 unchanged and in the same order, and add new checks after them.
+
+source_file (owner, Q1: documentation frozen into the source version):
+- `role`: 'data' (default; what every earlier file is), 'documentation' or 'curation'. Each role
+  has its own path rule, so a path tells its role and the files digest (sorted paths and hashes,
+  unchanged) stays unambiguous: data `<name>.csv|.xlsx` (0001's rule), documentation
+  `docs/<name>.tex|.xml|.md|.txt`, curation exactly `curation.json`.
+
+agent_invocation (one invocation record per agent call; step 5 re-check):
+- `scope` 'run' or 'registration'. A run invocation names its run and stage result, and its
+  (run, role, agent setting) must be one recorded at dispatch (`run_agent_setting`). A
+  registration invocation names a sealed source version, its role is the Curator's, and its agent
+  setting is a Curator setting. The dispatcher (`bind_invocation`) reads run or version, role,
+  setting and source from this one row.
+
+model_call:
+- `invocation_id`: required on every new call (by the insert trigger; the live database has no
+  model call). `run_id` and `stage_result_id` may be NULL, exactly for a registration
+  invocation's calls. The run rules of 0001 are unchanged for run calls; a registration call is
+  recorded while its source version is sealed and finished exactly once, with the same
+  immutability rules. The month view already counts every call.
+
+curator_proposal, curator_decision (owner, Q2):
+- a proposal per field per invocation, either 'proposed' (it passed both checks: the quote occurs
+  in one of the version's documentation files, which the database verifies itself after
+  collapsing runs of whitespace, and the quote contains the listed term stored with it) or
+  'refused' with a code. Append-only.
+- one decision per proposal, 'accepted' or 'rejected', by a named person, at the database's time;
+  only a 'proposed' proposal can be decided. Append-only.
+
+Works with the previous release's code: that code inserts source files without a role (they are
+data files and get the default), writes no model call, invocation, proposal or decision.
+
+Downgrade refuses while any row uses what 0005 adds (a documentation or curation file, an
+invocation, a model call with an invocation, a proposal, a decision), then restores 0001's
+functions and constraints exactly.
+
+Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
+transaction; it keeps working with the previous release's code; and it has a downgrade.
+"""
+from alembic import op
+import sqlalchemy as sa
+from sqlalchemy.dialects import postgresql
+
+revision = '0005'
+down_revision = '0004'
+branch_labels = None
+depends_on = None
+
+ROLES = "('planner', 'curator', 'critic', 'analyst', 'commentator')"
+# The fields the Curator may propose values for (owner, Q2): the conditions a table may lack.
+CURATION_FIELDS = ('test_type', 'phase_class', 'test_temperature', 'test_temperature_band', 'microstructure')
+# A proposal's quote, after collapsing runs of whitespace (the same normalization as the code's).
+QUOTE_MIN, QUOTE_MAX = 30, 1500
+STORED_TEXT_MAX = 4000  # any status: what the model wrote is kept, bounded
+
+# 0001's path rule, and the rule by role that replaces it under the same name (so a path tells its
+# role, and the files digest stays unambiguous).
+PATH_RULE_0001 = "path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'"
+PATH_RULE_0005 = (
+    "(role = 'data' AND path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$' AND path !~ '^documentation/') "
+    "OR (role = 'documentation' AND path ~ '^documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)$') "
+    "OR (role = 'curation' AND path = 'curation.json')")
+
+# 0001's functions, verbatim (restored by the downgrade).
+MODEL_CALL_INSERT_0001 = """
+    CREATE OR REPLACE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
+    BEGIN
+        IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
+                AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
+            PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
+        END IF;
+        IF NEW.status <> 'started' THEN
+            PERFORM hc_reject('a model call is recorded before the request, as started');
+        END IF;
+        IF NEW.started_at IS DISTINCT FROM now() THEN
+            PERFORM hc_reject('started_at is set by the database');
+        END IF;
+        RETURN NEW;
+    END $$
+    """
+MODEL_CALL_UPDATE_0001 = """
+    CREATE OR REPLACE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
+    BEGIN
+        IF NOT (s = 'running' OR s = 'completed' AND OLD.role = 'commentator') THEN
+            PERFORM hc_reject('a model call is finished only while its run is running');
+        END IF;
+        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
+            PERFORM hc_reject('a model call is finished exactly once');
+        END IF;
+        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
+           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
+           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
+            PERFORM hc_reject('what was recorded before the request cannot change');
+        END IF;
+        IF NEW.finished_at IS DISTINCT FROM now() THEN
+            PERFORM hc_reject('finished_at is set by the database');
+        END IF;
+        RETURN NEW;
+    END $$
+    """
+
+# A registration call (no run) is checked first; a run call goes through 0001's checks unchanged and
+# then must agree with its invocation. That every call names an invocation is a CHECK
+# (`ck_model_call_with_invocation`), named to sort after 0001's checks.
+MODEL_CALL_INSERT_0005 = """
+    CREATE OR REPLACE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
+            inv agent_invocation;
+    BEGIN
+        IF NEW.invocation_id IS NOT NULL THEN
+            SELECT * INTO inv FROM agent_invocation WHERE id = NEW.invocation_id;
+        END IF;
+        IF inv.scope = 'registration' THEN
+            IF NEW.run_id IS NOT NULL OR NEW.stage_result_id IS NOT NULL OR NEW.role IS DISTINCT FROM inv.role THEN
+                PERFORM hc_reject('a call of a registration invocation belongs to no run and has the invocation''s role');
+            END IF;
+        ELSE
+            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
+                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
+                PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
+            END IF;
+            IF inv.id IS NOT NULL AND (NEW.run_id IS DISTINCT FROM inv.run_id
+                    OR NEW.stage_result_id IS DISTINCT FROM inv.stage_result_id OR NEW.role IS DISTINCT FROM inv.role) THEN
+                PERFORM hc_reject('a model call has its invocation''s run, stage and role');
+            END IF;
+        END IF;
+        IF NEW.status <> 'started' THEN
+            PERFORM hc_reject('a model call is recorded before the request, as started');
+        END IF;
+        IF NEW.started_at IS DISTINCT FROM now() THEN
+            PERFORM hc_reject('started_at is set by the database');
+        END IF;
+        RETURN NEW;
+    END $$
+    """
+MODEL_CALL_UPDATE_0005 = """
+    CREATE OR REPLACE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
+    BEGIN
+        IF OLD.run_id IS NOT NULL THEN
+            IF NOT (s = 'running' OR s = 'completed' AND OLD.role = 'commentator') THEN
+                PERFORM hc_reject('a model call is finished only while its run is running');
+            END IF;
+        END IF;
+        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
+            PERFORM hc_reject('a model call is finished exactly once');
+        END IF;
+        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
+           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
+           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
+            PERFORM hc_reject('what was recorded before the request cannot change');
+        END IF;
+        IF NEW.run_id IS DISTINCT FROM OLD.run_id OR NEW.stage_result_id IS DISTINCT FROM OLD.stage_result_id
+           OR NEW.invocation_id IS DISTINCT FROM OLD.invocation_id THEN
+            PERFORM hc_reject('what was recorded before the request cannot change');
+        END IF;
+        IF NEW.finished_at IS DISTINCT FROM now() THEN
+            PERFORM hc_reject('finished_at is set by the database');
+        END IF;
+        RETURN NEW;
+    END $$
+    """
+
+FUNCTIONS = [
+    # An invocation is recorded once, before its calls: a run invocation under the run rule of a model
+    # call, for a running stage of that run with the same role; a registration invocation for a sealed
+    # version.
+    """
+    CREATE FUNCTION hc_agent_invocation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
+    BEGIN
+        IF NEW.scope = 'run' THEN
+            -- The same rule as a model call (0001): while the run is running, and after completion
+            -- only the Commentator's, for its own stage.
+            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
+                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
+                PERFORM hc_reject('an agent is invoked only while the run is running; after completion only the commentator''s');
+            END IF;
+            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.stage_result_id AND run_id = NEW.run_id
+                             AND role = NEW.role AND status = 'running') THEN
+                PERFORM hc_reject('an invocation belongs to a running stage of its run with the same role');
+            END IF;
+        ELSIF NOT EXISTS (SELECT 1 FROM source_version WHERE id = NEW.source_version_id AND sealed_at IS NOT NULL) THEN
+            PERFORM hc_reject('a registration invocation reads a sealed source version');
+        END IF;
+        NEW.created_at := now();
+        RETURN NEW;
+    END $$
+    """,
+    # A proposal belongs to a registration invocation of the Curator and to that invocation's
+    # version. A proposal that passed the checks quotes a passage the database finds in one of the
+    # version's documentation files (runs of whitespace collapsed on both sides).
+    """
+    CREATE FUNCTION hc_curator_proposal_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE inv agent_invocation;
+    BEGIN
+        SELECT * INTO inv FROM agent_invocation WHERE id = NEW.invocation_id;
+        IF inv.scope IS DISTINCT FROM 'registration' OR inv.role IS DISTINCT FROM 'curator' THEN
+            PERFORM hc_reject('a proposal comes from a registration invocation of the curator');
+        END IF;
+        IF NEW.source_version_id IS DISTINCT FROM inv.source_version_id THEN
+            PERFORM hc_reject('a proposal is for its invocation''s source version');
+        END IF;
+        IF NEW.status = 'proposed' AND NOT EXISTS (
+                SELECT 1 FROM source_file f WHERE f.source_version_id = NEW.source_version_id
+                  AND f.role = 'documentation' AND f.path = NEW.document_path
+                  AND strpos(regexp_replace(convert_from(f.content, 'UTF8'), '\\s+', ' ', 'g'),
+                             btrim(regexp_replace(NEW.quote, '\\s+', ' ', 'g'))) > 0) THEN
+            PERFORM hc_reject('a proposal''s quote must occur in the documentation file it names');
+        END IF;
+        NEW.created_at := now();
+        RETURN NEW;
+    END $$
+    """,
+    # One decision per proposal (unique), by a named person, at the database's time; only a
+    # proposal that passed the checks can be decided.
+    """
+    CREATE FUNCTION hc_curator_decision_insert() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF (SELECT status FROM curator_proposal WHERE id = NEW.proposal_id) IS DISTINCT FROM 'proposed' THEN
+            PERFORM hc_reject('only a proposal that passed the checks can be accepted or rejected');
+        END IF;
+        NEW.decided_at := now();
+        RETURN NEW;
+    END $$
+    """,
+]
+FUNCTION_NAMES = ["hc_agent_invocation_insert()", "hc_curator_proposal_insert()", "hc_curator_decision_insert()"]
+
+APPEND_ONLY = ["agent_invocation", "curator_proposal", "curator_decision"]
+# (table, event, function)
+CHECKED = [
+    ("agent_invocation", "INSERT", "hc_agent_invocation_insert"),
+    ("curator_proposal", "INSERT", "hc_curator_proposal_insert"),
+    ("curator_decision", "INSERT", "hc_curator_decision_insert"),
+]
+TRIGGERS = (
+    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
+     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
+    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
+       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
+    + [f"CREATE TRIGGER {f} BEFORE {event} ON {t} FOR EACH ROW EXECUTE FUNCTION {f}()" for t, event, f in CHECKED]
+)
+
+
+def upgrade() -> None:
+    # source_file: a role per file, and the path rule by role (same name as 0001's rule).
+    op.add_column('source_file', sa.Column('role', sa.Text(), server_default=sa.text("'data'"), nullable=False))
+    op.drop_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', type_='check')
+    op.create_check_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', PATH_RULE_0005)
+
+    # The target of an invocation's (run, role, setting).
+    op.create_unique_constraint(op.f('uq_run_agent_setting_run_id_role_agent_setting_id'), 'run_agent_setting',
+                                ['run_id', 'role', 'agent_setting_id'])
+
+    op.create_table(
+        'agent_invocation',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('scope', sa.Text(), nullable=False),
+        sa.Column('run_id', sa.BigInteger(), nullable=True),
+        sa.Column('stage_result_id', sa.BigInteger(), nullable=True),
+        sa.Column('source_version_id', sa.BigInteger(), nullable=True),
+        sa.Column('role', sa.Text(), nullable=False),
+        sa.Column('agent_setting_id', sa.BigInteger(), nullable=False),
+        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.CheckConstraint("scope IN ('run', 'registration')", name=op.f('ck_agent_invocation_scope')),
+        sa.CheckConstraint(f"role IN {ROLES}", name=op.f('ck_agent_invocation_role')),
+        sa.CheckConstraint(
+            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL) "
+            "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
+            "AND source_version_id IS NOT NULL AND role = 'curator')", name=op.f('ck_agent_invocation_shape')),
+        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_agent_invocation_run_id')),
+        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
+                                name=op.f('fk_agent_invocation_source_version_id')),
+        sa.ForeignKeyConstraint(['agent_setting_id', 'role'], ['agent_setting.id', 'agent_setting.role'],
+                                name='fk_agent_invocation_agent_setting'),
+        sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'],
+                                name='fk_agent_invocation_stage_result'),
+        sa.ForeignKeyConstraint(['run_id', 'role', 'agent_setting_id'],
+                                ['run_agent_setting.run_id', 'run_agent_setting.role',
+                                 'run_agent_setting.agent_setting_id'],
+                                name='fk_agent_invocation_run_agent_setting'),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_agent_invocation')),
+    )
+    op.create_index('ix_agent_invocation_run_id', 'agent_invocation', ['run_id'], unique=False)
+
+    # model_call: owned by an invocation; run and stage only for a run invocation's calls.
+    op.add_column('model_call', sa.Column('invocation_id', sa.BigInteger(), nullable=True))
+    op.create_foreign_key(op.f('fk_model_call_invocation_id'), 'model_call', 'agent_invocation',
+                          ['invocation_id'], ['id'])
+    op.create_index('ix_model_call_invocation_id', 'model_call', ['invocation_id'], unique=False)
+    op.alter_column('model_call', 'run_id', existing_type=sa.BigInteger(), nullable=True)
+    op.alter_column('model_call', 'stage_result_id', existing_type=sa.BigInteger(), nullable=True)
+    op.create_check_constraint(op.f('ck_model_call_run_with_stage'), 'model_call',
+                               "(run_id IS NULL) = (stage_result_id IS NULL)")
+    op.create_check_constraint(op.f('ck_model_call_with_invocation'), 'model_call', "invocation_id IS NOT NULL")
+
+    op.create_table(
+        'curator_proposal',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('invocation_id', sa.BigInteger(), nullable=False),
+        sa.Column('source_version_id', sa.BigInteger(), nullable=False),
+        sa.Column('field', sa.Text(), nullable=False),
+        sa.Column('status', sa.Text(), nullable=False),
+        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
+        sa.Column('quote', sa.Text(), nullable=True),
+        sa.Column('document_path', sa.Text(), nullable=True),
+        sa.Column('line', sa.Integer(), nullable=True),
+        sa.Column('term', sa.Text(), nullable=True),
+        sa.Column('refusal_code', sa.Text(), nullable=True),
+        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.CheckConstraint("field IN (" + ", ".join(f"'{f}'" for f in CURATION_FIELDS) + ")",
+                           name=op.f('ck_curator_proposal_field')),
+        sa.CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name=op.f('ck_curator_proposal_status')),
+        sa.CheckConstraint(
+            f"status <> 'proposed' OR (value IS NOT NULL AND document_path IS NOT NULL AND line >= 1 "
+            f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
+            f"AND length(term) > 0 AND strpos(lower(quote), lower(term)) > 0)",
+            name=op.f('ck_curator_proposal_proposed_complete')),
+        sa.CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
+                           "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')",
+                           name=op.f('ck_curator_proposal_refusal_code')),
+        sa.CheckConstraint("status <> 'not_stated' OR (value IS NULL AND quote IS NULL AND document_path IS NULL "
+                           "AND line IS NULL AND term IS NULL)", name=op.f('ck_curator_proposal_not_stated_empty')),
+        sa.CheckConstraint(f"length(coalesce(quote, '')) <= {STORED_TEXT_MAX} "
+                           f"AND length(coalesce(value::text, '')) <= {STORED_TEXT_MAX}",
+                           name=op.f('ck_curator_proposal_bounded')),
+        sa.ForeignKeyConstraint(['invocation_id'], ['agent_invocation.id'],
+                                name=op.f('fk_curator_proposal_invocation_id')),
+        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
+                                name=op.f('fk_curator_proposal_source_version_id')),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_curator_proposal')),
+        sa.UniqueConstraint('invocation_id', 'field', name=op.f('uq_curator_proposal_invocation_id_field')),
+    )
+    op.create_table(
+        'curator_decision',
+        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
+        sa.Column('proposal_id', sa.BigInteger(), nullable=False),
+        sa.Column('decision', sa.Text(), nullable=False),
+        sa.Column('decided_by', sa.Text(), nullable=False),
+        sa.Column('note', sa.Text(), nullable=True),
+        sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
+        sa.CheckConstraint("decision IN ('accepted', 'rejected')", name=op.f('ck_curator_decision_decision')),
+        sa.CheckConstraint("length(btrim(decided_by)) BETWEEN 1 AND 200 AND length(coalesce(note, '')) <= 2000",
+                           name=op.f('ck_curator_decision_named_and_bounded')),
+        sa.ForeignKeyConstraint(['proposal_id'], ['curator_proposal.id'],
+                                name=op.f('fk_curator_decision_proposal_id')),
+        sa.PrimaryKeyConstraint('id', name=op.f('pk_curator_decision')),
+        sa.UniqueConstraint('proposal_id', name=op.f('uq_curator_decision_proposal_id')),
+    )
+
+    for f in FUNCTIONS:
+        op.execute(f)
+    for t in TRIGGERS:
+        op.execute(t)
+    op.execute(MODEL_CALL_INSERT_0005)
+    op.execute(MODEL_CALL_UPDATE_0005)
+
+
+# Anything 0005 added that holds data; the downgrade refuses while any exists.
+IN_USE = """
+    DO $$
+    BEGIN
+        IF EXISTS (SELECT 1 FROM source_file WHERE role <> 'data') OR EXISTS (SELECT 1 FROM agent_invocation)
+           OR EXISTS (SELECT 1 FROM model_call WHERE invocation_id IS NOT NULL)
+           OR EXISTS (SELECT 1 FROM curator_proposal) OR EXISTS (SELECT 1 FROM curator_decision) THEN
+            RAISE EXCEPTION 'hypocurate: migration 0005 is in use (documentation, invocations, proposals or decisions); not downgraded';
+        END IF;
+    END $$
+"""
+
+
+def downgrade() -> None:
+    op.execute(IN_USE)
+    op.execute(MODEL_CALL_INSERT_0001)
+    op.execute(MODEL_CALL_UPDATE_0001)
+    for t in ("curator_decision", "curator_proposal"):
+        op.drop_table(t)
+    op.drop_constraint(op.f('ck_model_call_with_invocation'), 'model_call', type_='check')
+    op.drop_constraint(op.f('ck_model_call_run_with_stage'), 'model_call', type_='check')
+    op.alter_column('model_call', 'stage_result_id', existing_type=sa.BigInteger(), nullable=False)
+    op.alter_column('model_call', 'run_id', existing_type=sa.BigInteger(), nullable=False)
+    op.drop_index('ix_model_call_invocation_id', table_name='model_call')
+    op.drop_constraint(op.f('fk_model_call_invocation_id'), 'model_call', type_='foreignkey')
+    op.drop_column('model_call', 'invocation_id')
+    op.drop_index('ix_agent_invocation_run_id', table_name='agent_invocation')
+    op.drop_table('agent_invocation')
+    for f in FUNCTION_NAMES:
+        op.execute(f"DROP FUNCTION {f}")
+    op.drop_constraint(op.f('uq_run_agent_setting_run_id_role_agent_setting_id'), 'run_agent_setting', type_='unique')
+    op.drop_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', type_='check')
+    op.create_check_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', PATH_RULE_0001)
+    op.drop_column('source_file', 'role')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index da5d45d..d2da17f 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -202,21 +202,31 @@ class SourceVersion(Base):
     )
 
 
+FILE_ROLES = ("data", "documentation", "curation")
+
+
 class SourceFile(Base):
-    """A data file an adapter reads (owner decision: only data files, at most 5 MiB).
-    Added only before its version is sealed. Append-only."""
+    """A file of a source version (at most 5 MiB), added only before its version is sealed.
+    Append-only. Step 8a (migration 0005; owner, 2026-10-06): its role is 'data' (what an adapter
+    reads; every file before 8a), 'documentation' (the source's own documentation, which the Curator
+    reads) or 'curation' (the accepted Curator values sealed into a curated version)."""
     __tablename__ = "source_file"
     id: Mapped[int] = pk()
     source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
     path: Mapped[str] = mapped_column(Text)
     sha256: Mapped[str] = mapped_column(Text)
     content: Mapped[bytes] = mapped_column(LargeBinary)
+    role: Mapped[str] = mapped_column(Text, server_default=sql("'data'"))
     __table_args__ = (
         UniqueConstraint("source_version_id", "path"),
         CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
         # Re-check item 2: a safe character set, anchored at both ends, so a path holds no
-        # line break and the sealed file list has one unambiguous line per file.
-        CheckConstraint("path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'", name="safe_data_file_path"),
+        # line break and the sealed file list has one unambiguous line per file. Step 8a: the rule
+        # by role (0001's name kept); a path tells its role, so the files digest stays unambiguous.
+        CheckConstraint(
+            "(role = 'data' AND path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$' AND path !~ '^documentation/') "
+            "OR (role = 'documentation' AND path ~ '^documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)$') "
+            "OR (role = 'curation' AND path = 'curation.json')", name="safe_data_file_path"),
         CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
     )
 
@@ -400,6 +410,8 @@ class RunAgentSetting(Base):
     __table_args__ = (
         ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
                              name="fk_run_agent_setting_agent_setting"),
+        # Step 8a (0005): the target of an invocation's (run, role, setting).
+        UniqueConstraint("run_id", "role", "agent_setting_id"),
     )
 
 
@@ -496,8 +508,10 @@ class ModelCall(Base):
     `finished_at` are the database's transaction times (review finding 7)."""
     __tablename__ = "model_call"
     id: Mapped[int] = pk()
-    run_id: Mapped[int] = mapped_column(BigInteger)
-    stage_result_id: Mapped[int] = mapped_column(BigInteger)
+    # Step 8a (0005): NULL exactly for the calls of a registration invocation (the Curator).
+    run_id: Mapped[int | None] = mapped_column(BigInteger)
+    stage_result_id: Mapped[int | None] = mapped_column(BigInteger)
+    invocation_id: Mapped[int | None] = mapped_column(ForeignKey("agent_invocation.id"))
     role: Mapped[str] = mapped_column(Text)
     model: Mapped[str] = mapped_column(Text)
     price_table_version: Mapped[str] = mapped_column(Text)
@@ -515,7 +529,11 @@ class ModelCall(Base):
         ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                              name="fk_model_call_stage_result"),
         Index("ix_model_call_run_id", "run_id"),
+        Index("ix_model_call_invocation_id", "invocation_id"),
         CheckConstraint(one_of("role", ROLES), name="role"),
+        CheckConstraint("(run_id IS NULL) = (stage_result_id IS NULL)", name="run_with_stage"),
+        # Named to sort after every check of 0001, so their refusals keep their own messages.
+        CheckConstraint("invocation_id IS NOT NULL", name="with_invocation"),
         CheckConstraint(one_of("status", CALL_STATUSES), name="status"),
         CheckConstraint("length(model) > 0 AND length(price_table_version) > 0", name="model_and_prices_named"),
         CheckConstraint("max_cost > 0", name="max_cost_positive"),
@@ -534,6 +552,95 @@ class ModelCall(Base):
     )
 
 
+# --- Agent invocations and the Curator's proposals (step 8a, migration 0005) --------------
+
+CURATION_FIELDS = ("test_type", "phase_class", "test_temperature", "test_temperature_band", "microstructure")
+QUOTE_MIN, QUOTE_MAX = 30, 1500  # a proposal's quote, whitespace collapsed (register 'curator_quote_checks')
+STORED_TEXT_MAX = 4000
+
+
+class AgentInvocation(Base):
+    """One record per agent call (step 5 re-check): the dispatcher reads run or version, role,
+    setting and source from it alone. A run invocation's (run, role, setting) is one recorded at
+    dispatch; a registration invocation is the Curator's, on a sealed source version. Append-only."""
+    __tablename__ = "agent_invocation"
+    id: Mapped[int] = pk()
+    scope: Mapped[str] = mapped_column(Text)
+    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
+    stage_result_id: Mapped[int | None] = mapped_column(BigInteger)
+    source_version_id: Mapped[int | None] = mapped_column(ForeignKey("source_version.id"))
+    role: Mapped[str] = mapped_column(Text)
+    agent_setting_id: Mapped[int] = mapped_column(BigInteger)
+    created_at: Mapped[datetime] = created()
+    __table_args__ = (
+        Index("ix_agent_invocation_run_id", "run_id"),
+        CheckConstraint("scope IN ('run', 'registration')", name="scope"),
+        CheckConstraint(one_of("role", ROLES), name="role"),
+        CheckConstraint(
+            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL) "
+            "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
+            "AND source_version_id IS NOT NULL AND role = 'curator')", name="shape"),
+        ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
+                             name="fk_agent_invocation_agent_setting"),
+        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
+                             name="fk_agent_invocation_stage_result"),
+        ForeignKeyConstraint(["run_id", "role", "agent_setting_id"],
+                             ["run_agent_setting.run_id", "run_agent_setting.role",
+                              "run_agent_setting.agent_setting_id"], name="fk_agent_invocation_run_agent_setting"),
+    )
+
+
+class CuratorProposal(Base):
+    """What the Curator proposed for one field, as stored by code after its two checks (owner, Q2):
+    'proposed' (passed: the quote occurs in the named documentation file, which the database checks
+    again, and contains the listed term), 'refused' (with a code) or 'not_stated'. Append-only."""
+    __tablename__ = "curator_proposal"
+    id: Mapped[int] = pk()
+    invocation_id: Mapped[int] = mapped_column(ForeignKey("agent_invocation.id"))
+    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
+    field: Mapped[str] = mapped_column(Text)
+    status: Mapped[str] = mapped_column(Text)
+    value: Mapped[dict | None] = mapped_column(JSONB)
+    quote: Mapped[str | None] = mapped_column(Text)
+    document_path: Mapped[str | None] = mapped_column(Text)
+    line: Mapped[int | None] = mapped_column(Integer)
+    term: Mapped[str | None] = mapped_column(Text)
+    refusal_code: Mapped[str | None] = mapped_column(Text)
+    created_at: Mapped[datetime] = created()
+    __table_args__ = (
+        UniqueConstraint("invocation_id", "field"),
+        CheckConstraint(one_of("field", CURATION_FIELDS), name="field"),
+        CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name="status"),
+        CheckConstraint(
+            f"status <> 'proposed' OR (value IS NOT NULL AND document_path IS NOT NULL AND line >= 1 "
+            f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
+            f"AND length(term) > 0 AND strpos(lower(quote), lower(term)) > 0)", name="proposed_complete"),
+        CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
+                        "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')", name="refusal_code"),
+        CheckConstraint("status <> 'not_stated' OR (value IS NULL AND quote IS NULL AND document_path IS NULL "
+                        "AND line IS NULL AND term IS NULL)", name="not_stated_empty"),
+        CheckConstraint(f"length(coalesce(quote, '')) <= {STORED_TEXT_MAX} "
+                        f"AND length(coalesce(value::text, '')) <= {STORED_TEXT_MAX}", name="bounded"),
+    )
+
+
+class CuratorDecision(Base):
+    """A person's decision on one proposal that passed the checks: accepted or rejected, by a
+    named person, at the database's time. One per proposal. Append-only."""
+    __tablename__ = "curator_decision"
+    id: Mapped[int] = pk()
+    proposal_id: Mapped[int] = mapped_column(ForeignKey("curator_proposal.id"), unique=True)
+    decision: Mapped[str] = mapped_column(Text)
+    decided_by: Mapped[str] = mapped_column(Text)
+    note: Mapped[str | None] = mapped_column(Text)
+    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
+    __table_args__ = (
+        CheckConstraint("decision IN ('accepted', 'rejected')", name="decision"),
+        CheckConstraint("length(btrim(decided_by)) BETWEEN 1 AND 200 AND length(coalesce(note, '')) <= 2000",
+                        name="named_and_bounded"),
+    )
+
+
 # --- Records: stored is not analysed ------------------------------------------------
 
 class Record(Base):
diff --git a/hypocurate/pipeline/agents/__init__.py b/hypocurate/pipeline/agents/__init__.py
new file mode 100644
index 0000000..abf28b5
--- /dev/null
+++ b/hypocurate/pipeline/agents/__init__.py
@@ -0,0 +1,9 @@
+"""The agents (PRD Sections 3, 4 and 6; build step 8).
+
+Agents are language models that return text only. They never execute code and never receive
+SQL, a database connection or a file path (CLAUDE.md rule 14): each call gets text built from an
+access object that the trusted dispatcher bound to one invocation. Code decides; agents advise.
+
+The model-call libraries (DSPy and litellm) are imported only through `libraries.load()`, which
+sets their environment first (litellm otherwise reads a `.env` file when it is imported).
+"""
diff --git a/hypocurate/pipeline/agents/curator.py b/hypocurate/pipeline/agents/curator.py
new file mode 100644
index 0000000..e6b0d3e
--- /dev/null
+++ b/hypocurate/pipeline/agents/curator.py
@@ -0,0 +1,138 @@
+"""The Curator (step 8a; owner, 2026-10-06, Q2 and Q3; register 'curator_registration').
+
+At registration of a source version grouped by dataset, the Curator reads that version's
+documentation and proposes, for each target field, one value that holds for all of the source's
+measurements, with the exact sentence it relied on, or says "not stated". It is not told any claim,
+plan or data row (its access list holds only the documentation and the targets).
+
+Code decides what a proposal is: `proposals_from` checks each entry (the field is a target, the
+value is allowed, the quote is found in the documentation and contains a listed term; `quotes`) and
+stores it as 'proposed', 'refused' with a code, or 'not_stated'. A proposal takes effect only when a
+person accepts it (`sources.curation`), and only where a table gives no value.
+
+The answer's form: one JSON object, one key per target field; each value is "not stated" or
+{"value": ..., "quote": ...}. A missing key means "not stated"; a key that is not a target is
+ignored and reported. An answer that is not such an object is malformed (corrected once, by the
+common interface).
+"""
+from __future__ import annotations
+
+import json
+import math
+import re
+from dataclasses import dataclass
+from typing import Any, Mapping
+
+from hypocurate.access.vocabulary import CURATION_TARGETS, MICROSTRUCTURE_TOKENS
+from hypocurate.pipeline.agents import libraries, quotes
+
+OUTPUT_DESCRIPTION = ('One JSON object with one key per target field. The value of each key is either the string '
+                      '"not stated" or an object {"value": <one of the allowed values, or a number in degrees '
+                      'Celsius for test_temperature>, "quote": "<the one sentence that states it, copied word for '
+                      'word>"}. Nothing else.')
+STORED_MAX = 4000  # the database's bound on stored text (migration 0005)
+_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)
+
+
+def signature(instruction: str):
+    _, dspy = libraries.load()
+
+    class CuratorSignature(dspy.Signature):
+        documentation: str = dspy.InputField(desc="The source's documentation files, each introduced by its path.")
+        targets: str = dspy.InputField(desc="The target fields, as JSON: each with its allowed values or unit.")
+        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
+        proposals: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)
+
+    return CuratorSignature.with_instructions(instruction)
+
+
+def render_inputs(curator_input: Mapping[str, Any]) -> dict[str, str]:
+    """The Curator's request inputs, built only from its complete access-layer input."""
+    documents = curator_input["source_documentation"]["documents"]
+    documentation = "\n".join(f"=== {path} ===\n{text}" for path, text in sorted(documents.items()))
+    return {"documentation": documentation,
+            "targets": json.dumps(curator_input["curation_targets"], sort_keys=True, ensure_ascii=False)}
+
+
+def parse(text: str) -> dict | None:
+    """The answer as a JSON object, or None. Surrounding whitespace and one ``` fence are allowed."""
+    body = text.strip()
+    fenced = _FENCE.match(body)
+    if fenced:
+        body = fenced.group(1)
+    try:
+        value = json.loads(body)
+    except ValueError:
+        return None
+    return value if isinstance(value, dict) else None
+
+
+def check(outputs: Mapping[str, str]) -> str | None:
+    """The common interface's check: None if the answer can be read, else "malformed"."""
+    return None if parse(outputs["proposals"]) is not None else "malformed"
+
+
+@dataclass(frozen=True)
+class Proposal:
+    field: str
+    status: str  # 'proposed', 'refused', 'not_stated'
+    value: Any = None
+    quote: str | None = None
+    document: str | None = None
+    line: int | None = None
+    term: str | None = None
+    refusal_code: str | None = None
+
+
+def _value_problem(field: str, value: Any) -> str | None:
+    if field == "test_temperature":
+        ok = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
+              and -273.15 <= value <= 3000)
+        return None if ok else "value_not_allowed"
+    if field == "microstructure":
+        ok = isinstance(value, str) and value != "" and all(t in MICROSTRUCTURE_TOKENS for t in value.split("+"))
+        return None if ok else "value_not_allowed"
+    return None if isinstance(value, str) and value in CURATION_TARGETS[field]["vocabulary"] else "value_not_allowed"
+
+
+def _stored(value: Any) -> Any:
+    """What a refused entry keeps of the model's value: JSON within the bound, else nothing."""
+    try:
+        text = json.dumps(value)
+    except (TypeError, ValueError):
+        return None
+    return value if len(text) <= STORED_MAX else None
+
+
+def _entry(field: str, entry: Any, documents: Mapping[str, str]) -> Proposal:
+    if isinstance(entry, str) and entry.strip().lower() == "not stated":
+        return Proposal(field, "not_stated")
+    if not (isinstance(entry, dict) and set(entry) == {"value", "quote"} and isinstance(entry["quote"], str)):
+        return Proposal(field, "refused", refusal_code="malformed_entry")
+    value, quote = entry["value"], entry["quote"]
+    kept = dict(value=_stored(value), quote=quote[:STORED_MAX])
+    code = _value_problem(field, value)
+    collapsed = quotes.collapse(quote)
+    if code is None and len(collapsed) < quotes.QUOTE_MIN_CHARS:
+        code = "quote_too_short"
+    if code is None and len(collapsed) > quotes.QUOTE_MAX_CHARS:
+        code = "quote_too_long"
+    located = quotes.locate(quote, documents) if code is None else None
+    if code is None and located is None:
+        code = "quote_not_found"
+    term = quotes.term_for(field, value, quote) if code is None else None
+    if code is None and term is None:
+        code = "term_missing"
+    if code is not None:
+        return Proposal(field, "refused", refusal_code=code, **kept)
+    return Proposal(field, "proposed", value=value, quote=quote, document=located.document, line=located.line,
+                    term=term)
+
+
+def proposals_from(text: str, documents: Mapping[str, str]) -> tuple[list[Proposal], list[str]]:
+    """One proposal per target field (in field order) and the keys that are not targets."""
+    data = parse(text)
+    if data is None:
+        raise ValueError("the answer is not a JSON object")  # the interface's check refuses it first
+    proposals = [_entry(field, data.get(field, "not stated"), documents) for field in sorted(CURATION_TARGETS)]
+    return proposals, sorted(k for k in data if k not in CURATION_TARGETS)
diff --git a/hypocurate/pipeline/agents/interface.py b/hypocurate/pipeline/agents/interface.py
new file mode 100644
index 0000000..ada7a49
--- /dev/null
+++ b/hypocurate/pipeline/agents/interface.py
@@ -0,0 +1,80 @@
+"""The common agent interface (PRD 6: the orchestrator calls every agent the same way; step 8a).
+
+`call_agent` runs one agent call, bound to one invocation record:
+- the input is the role's complete input from the access layer (`role_input` on the object
+  `bind_invocation` returns), rendered as text by the role's module; nothing else enters the request;
+- the request goes through a DSPy module (a `Signature` with declared inputs and outputs), with DSPy's
+  ChatAdapter and its JSON fallback off (a fallback would be a second, unplanned request), and a
+  `RecordedEngine` (every request reserved, sent, recorded);
+- failures follow `lm.FAILURES`: "retry" sends the same request once more, "correct" sends it once
+  more with the role's fixed corrective note naming the failure code (never the failed answer and
+  never any error text), "stop" ends the call. At most `MAX_ATTEMPTS` requests per agent call;
+- the result is the raw text of the parsed output fields, for the role's module to check. A role
+  never gets a result it can act on unless code has checked it.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass, field
+from decimal import Decimal
+from typing import Any, Mapping
+
+from hypocurate.pipeline.agents import libraries
+from hypocurate.pipeline.agents.lm import FAILURES, AgentFailure, RecordedEngine
+
+MAX_ATTEMPTS = 2  # register 'request_failure_policy'
+NO_NOTE = "none"
+
+
+def correction_note(code: str) -> str:
+    """The only text a retry adds: a fixed sentence naming the failure code."""
+    return (f"The previous answer could not be used ({code}: {FAILURES[code][0]}). "
+            "Answer again, in exactly the requested form, within the length limit.")
+
+
+@dataclass
+class AgentResult:
+    outputs: dict[str, str] | None
+    failure: str | None
+    attempts: list[str] = field(default_factory=list)  # one entry per request: "ok" or a failure code
+    calls: list[int] = field(default_factory=list)       # the recorded model calls
+
+
+def call_agent(db, invocation_id: int, signature, inputs: Mapping[str, str], *, model: str, max_tokens: int,
+               max_output_chars: int, ceiling: Decimal | None = None, lm_options: Mapping[str, Any] | None = None,
+               client_options: Mapping[str, Any] | None = None, check=None) -> AgentResult:
+    """One agent call (see the module docstring). `signature` has the role's input fields plus `note`.
+    `lm_options`: the role's request settings (for example its effort). `check(outputs)`: the role's
+    check that its answer can be read, returning None or "malformed" (then corrected like a DSPy parse
+    failure)."""
+    _, dspy = libraries.load()
+    engine = RecordedEngine(db, invocation_id, model, max_output_chars=max_output_chars, ceiling=ceiling,
+                            client_options=client_options)
+    lm = dspy.LM(f"anthropic/{model}", engine=engine, cache=False, num_retries=0, max_tokens=max_tokens,
+                 **dict(lm_options or {}))
+    adapter = dspy.ChatAdapter(use_json_adapter_fallback=False)
+    result = AgentResult(None, None)
+    note = NO_NOTE
+    try:
+        for _ in range(MAX_ATTEMPTS):
+            try:
+                with dspy.context(lm=lm, adapter=adapter):
+                    prediction = dspy.Predict(signature)(**inputs, note=note)
+            except Exception:  # noqa: BLE001 (classified by code; nothing of it is kept here)
+                code = engine.last_failure or "malformed"
+            else:
+                outputs = {name: str(getattr(prediction, name)) for name in signature.output_fields}
+                code = check(outputs) if check is not None else None
+                if code is None:
+                    result.attempts.append("ok")
+                    result.outputs, result.failure = outputs, None
+                    return result
+            result.attempts.append(code)
+            result.failure = code
+            action = FAILURES[code][1]
+            if action == "stop":
+                break
+            note = correction_note(code) if action == "correct" else note
+        return result
+    finally:
+        result.calls = list(engine.calls)
+        engine.close()
diff --git a/hypocurate/pipeline/agents/libraries.py b/hypocurate/pipeline/agents/libraries.py
new file mode 100644
index 0000000..58d6648
--- /dev/null
+++ b/hypocurate/pipeline/agents/libraries.py
@@ -0,0 +1,56 @@
+"""The one place that imports the model-call libraries, DSPy and litellm (step 8a).
+
+`load()` sets their environment before importing them, every time, overriding whatever the
+process had:
+- `LITELLM_MODE=PRODUCTION`: otherwise litellm reads a `.env` file when it is imported (the file
+  guard caught it reading the repository's `.env`, which holds the secrets);
+- `LITELLM_LOCAL_MODEL_COST_MAP=True`: litellm uses the price map shipped with it instead of
+  fetching one over the network. Our costs come from our own price table, never from litellm's.
+
+Then it turns off litellm's own retries (one HTTP request is one recorded model call; retries are
+ours, each reserved and recorded) and DSPy's caches (a cached answer would be a model output that
+no recorded call produced).
+"""
+from __future__ import annotations
+
+import os
+from types import MappingProxyType
+
+LIBRARY_ENVIRONMENT = MappingProxyType({
+    "LITELLM_MODE": "PRODUCTION",
+    "LITELLM_LOCAL_MODEL_COST_MAP": "True",
+})
+
+
+def load():
+    """Returns the modules (litellm, dspy), imported with their environment set."""
+    for name, value in LIBRARY_ENVIRONMENT.items():
+        os.environ[name] = value
+    import litellm
+    litellm.num_retries = 0
+    litellm.telemetry = False
+    litellm.suppress_debug_info = True
+    import dspy
+    dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)
+    return litellm, dspy
+
+
+def lm15():
+    """DSPy's provider-neutral request, response and error types (after `load`)."""
+    load()
+    from dspy import lm15 as module
+    return module
+
+
+def litellm_engine(**client_options):
+    """DSPy's one-attempt litellm engine (after `load`)."""
+    load()
+    from dspy.clients.engines.litellm_engine import LiteLLMEngine
+    return LiteLLMEngine(**client_options)
+
+
+def request_kwargs(request) -> dict:
+    """A DSPy request as the keyword arguments litellm receives (after `load`)."""
+    load()
+    from dspy.clients.lm15_boundary import request_kwargs as convert
+    return convert(request, "chat")
diff --git a/hypocurate/pipeline/agents/lm.py b/hypocurate/pipeline/agents/lm.py
new file mode 100644
index 0000000..00e0da1
--- /dev/null
+++ b/hypocurate/pipeline/agents/lm.py
@@ -0,0 +1,155 @@
+"""The request path of every agent call (step 8a): reserve, request, record (register
+'model_call_recording', 'request_failure_policy').
+
+`RecordedEngine` is a DSPy engine (`complete(Request) -> Response`, DSPy's supported interface). For
+each request it:
+1. reserves the call's maximum cost (`spend.reserve`, one transaction that checks the caps and
+   records the call as started); a refusal sends nothing;
+2. sends the request through DSPy's own litellm engine, outside any database transaction, one HTTP
+   attempt (litellm's retries are off, `libraries.load`);
+3. records the outcome (`spend.finish`): the reported usage and its cost (`prices.cost`), or a
+   failure with no usage and a fixed code;
+4. turns a reply that cannot be used into a fixed code after it is recorded: truncated (the output
+   limit was reached), refused, a tool call (no tools are offered), empty or over-long text.
+
+Every failure is an `AgentFailure` with a fixed code (`FAILURES`); its message is the code's fixed
+text. The original exception, with its traceback, goes to the process log only: nothing a provider,
+a library or the database wrote ever travels with the error or into a later request. The last
+failure is also kept on the engine (`last_failure`), because DSPy may wrap exceptions raised inside
+it.
+"""
+from __future__ import annotations
+
+import json
+import logging
+from decimal import Decimal
+from typing import Any, Mapping
+
+from hypocurate.pipeline.agents import libraries, prices, spend
+
+LOG = logging.getLogger("hypocurate.pipeline")
+DEFAULT_TIMEOUT_SECONDS = 300
+# code -> (fixed text, what the runner does: "retry" (the same request again), "correct" (again, with
+# the fixed corrective note), or "stop").
+FAILURES: Mapping[str, tuple[str, str]] = {
+    "provider_unavailable": ("the provider could not be reached or did not answer in time", "retry"),
+    "model_auth": ("the provider refused the credentials", "stop"),
+    "provider_rejected": ("the provider refused the request", "stop"),
+    "cost_unknown": ("the provider reported no usage, so the cost is unknown", "stop"),
+    "recording_failed": ("the call could not be recorded", "stop"),
+    "refused": ("the model declined to answer", "stop"),
+    "truncated": ("the answer reached the output limit", "correct"),
+    "tool_call": ("the answer asked for a tool; none is offered", "correct"),
+    "empty": ("the answer was empty", "correct"),
+    "over_long": ("the answer was longer than the role allows", "correct"),
+    "malformed": ("the answer could not be read in the requested form", "correct"),
+    "spending_cap_run": ("the run's spending cap would be exceeded", "stop"),
+    "spending_cap_curation": ("the curation's spending cap would be exceeded", "stop"),
+    "spending_cap_month": ("the monthly spending cap would be exceeded", "stop"),
+    "ceiling_reached": ("the ceiling set for this call would be exceeded", "stop"),
+    "invocation_unknown": ("no such invocation", "stop"),
+}
+
+
+class AgentFailure(Exception):
+    """A failed agent request, with a fixed code and only the code's fixed text."""
+
+    def __init__(self, code: str):
+        self.code = code
+        super().__init__(f"{code}: {FAILURES[code][0]}")
+
+
+def _classify(error: BaseException) -> str:
+    lm15 = libraries.lm15()
+    if isinstance(error, lm15.AuthError):
+        return "model_auth"
+    if isinstance(error, (lm15.RateLimitError, lm15.ServerError, lm15.TimeoutError, lm15.TransportError)):
+        return "provider_unavailable"
+    return "provider_rejected"
+
+
+def _keep(code: str, error: BaseException) -> None:
+    LOG.error(json.dumps({"agent_request_failure": code}), exc_info=(type(error), error, error.__traceback__))
+
+
+def request_bytes(request: Any) -> int:
+    """The UTF-8 length of the request's messages and settings as JSON: at least its token count."""
+    return len(json.dumps(libraries.request_kwargs(request), default=str, ensure_ascii=False).encode("utf-8"))
+
+
+class RecordedEngine:
+    def __init__(self, db, invocation_id: int, model: str, *, max_output_chars: int,
+                 ceiling: Decimal | None = None, client_options: Mapping[str, Any] | None = None):
+        prices.price(model)  # an unpriced model is refused before anything else
+        self._db, self._invocation, self._model = db, invocation_id, model
+        self._max_output_chars, self._ceiling = int(max_output_chars), ceiling
+        options = {"timeout": DEFAULT_TIMEOUT_SECONDS, **(client_options or {})}
+        self._inner = libraries.litellm_engine(**options)
+        self.last_failure: str | None = None
+        self.calls: list[int] = []
+
+    def _fail(self, code: str):
+        self.last_failure = code
+        return AgentFailure(code)
+
+    def complete(self, request):
+        self.last_failure = None
+        if not request.config.max_tokens:
+            raise ValueError("every agent request names its output limit")
+        bound = prices.max_cost(self._model, request_bytes(request), request.config.max_tokens)
+        try:
+            call = spend.reserve(self._db, self._invocation, self._model, bound, self._ceiling)
+        except spend.SpendingRefused as refused:
+            raise self._fail(refused.code) from None
+        self.calls.append(call)
+        failure = None
+        try:
+            response = self._inner.complete(request)
+        except Exception as error:  # noqa: BLE001 (classified; the original goes to the process log only)
+            failure = _classify(error)
+            _keep(failure, error)
+        if failure is not None:
+            spend.finish(self._db, call, "failed", code=failure)
+            raise self._fail(failure)
+        usage = response.usage
+        if usage is None or usage.input_tokens is None or usage.output_tokens is None:
+            spend.finish(self._db, call, "failed", code="cost_unknown")
+            raise self._fail("cost_unknown")
+        read, write = usage.cache_read_tokens or 0, usage.cache_write_tokens or 0
+        recorded = None
+        try:
+            spend.finish(self._db, call, "succeeded", input_tokens=usage.input_tokens,
+                         output_tokens=usage.output_tokens, cached_tokens=read,
+                         cost=prices.cost(self._model, usage.input_tokens, usage.output_tokens, read, write))
+            recorded = True
+        except Exception as error:  # noqa: BLE001
+            _keep("recording_failed", error)
+        if not recorded:
+            raise self._fail("recording_failed")
+        code = _unusable(response, self._max_output_chars)
+        if code:
+            raise self._fail(code)
+        return response
+
+    def stream(self, request):
+        raise NotImplementedError("the agents do not stream")
+
+    def close(self) -> None:
+        self._inner.close()
+
+
+def _unusable(response, max_output_chars: int) -> str | None:
+    """A recorded reply that cannot be used, as a code; None if it can."""
+    reason = response.finish_reason
+    if reason == "length":
+        return "truncated"
+    if reason in ("content_filter", "refusal"):
+        return "refused"
+    if response.tool_calls or reason == "tool_calls":
+        return "tool_call"
+    text = response.text or ""
+    if not text.strip():
+        return "empty"
+    if len(text) > max_output_chars:
+        return "over_long"
+    return None
diff --git a/hypocurate/pipeline/agents/prices.py b/hypocurate/pipeline/agents/prices.py
new file mode 100644
index 0000000..5a570fc
--- /dev/null
+++ b/hypocurate/pipeline/agents/prices.py
@@ -0,0 +1,70 @@
+"""The price table for model calls (step 8a; register entry 'model_prices').
+
+Cost is computed by code from the token usage the provider reports, times this table: the provider
+reports tokens, not money. Each model call stores the table's version (`PRICE_TABLE_VERSION`), so a
+cost can be recomputed if prices change. Prices are US dollars per million tokens, from Anthropic's
+published pricing as cached on 2026-09-25; before the first live call the table is checked against
+the published page, and work stops if it differs (owner, 2026-10-06).
+
+Cache writes cost 1.25 times the input price (the five-minute cache). The agents never ask for
+prompt caching, so cache reads and writes are expected to be zero; they are priced in case the
+provider reports any.
+
+The maximum cost reserved before a request (`max_cost`) is an upper bound: every token of the
+request is counted as at least one byte of its UTF-8 JSON (a token is never shorter than a byte),
+plus a fixed allowance for the provider's own framing, all at the input price, and the request's
+output limit at the output price (thinking tokens are output tokens and fall under the same limit).
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from decimal import Decimal
+from types import MappingProxyType
+
+PRICE_TABLE_VERSION = "anthropic-2026-09-25"
+PER_MILLION = Decimal(1_000_000)
+FRAMING_ALLOWANCE_TOKENS = 1000  # the provider's own tokens around a request (system framing)
+
+
+@dataclass(frozen=True)
+class Price:
+    input: Decimal
+    output: Decimal
+    cache_read: Decimal
+    cache_write: Decimal
+
+
+PRICES = MappingProxyType({
+    "claude-opus-5-5": Price(Decimal("4"), Decimal("20"), Decimal("0.20"), Decimal("5")),
+    "claude-sonnet-5-5": Price(Decimal("2"), Decimal("10"), Decimal("0.20"), Decimal("2.5")),
+    "claude-haiku-4-5": Price(Decimal("1"), Decimal("5"), Decimal("0.10"), Decimal("1.25")),
+})
+# How litellm names each model (provider prefix).
+PROVIDER_MODEL = MappingProxyType({m: f"anthropic/{m}" for m in PRICES})
+
+
+class UnknownModel(Exception):
+    """A model without a price cannot be called: its cost could not be computed or capped."""
+
+
+def price(model: str) -> Price:
+    if model not in PRICES:
+        raise UnknownModel(model)
+    return PRICES[model]
+
+
+def max_cost(model: str, request_bytes: int, max_output_tokens: int) -> Decimal:
+    """The most the request can cost (see the module docstring)."""
+    p = price(model)
+    return ((Decimal(request_bytes + FRAMING_ALLOWANCE_TOKENS) * p.input
+             + Decimal(max_output_tokens) * p.output) / PER_MILLION)
+
+
+def cost(model: str, input_tokens: int, output_tokens: int, cache_read_tokens: int, cache_write_tokens: int) -> Decimal:
+    """The cost of a reported usage. `input_tokens` includes the cached ones (as reported)."""
+    p = price(model)
+    uncached = input_tokens - cache_read_tokens - cache_write_tokens
+    if min(uncached, output_tokens, cache_read_tokens, cache_write_tokens) < 0:
+        raise ValueError("token counts do not add up")
+    return (Decimal(uncached) * p.input + Decimal(cache_read_tokens) * p.cache_read
+            + Decimal(cache_write_tokens) * p.cache_write + Decimal(output_tokens) * p.output) / PER_MILLION
diff --git a/hypocurate/pipeline/agents/quotes.py b/hypocurate/pipeline/agents/quotes.py
new file mode 100644
index 0000000..14e6bf7
--- /dev/null
+++ b/hypocurate/pipeline/agents/quotes.py
@@ -0,0 +1,93 @@
+"""The two checks on a Curator proposal (owner, 2026-10-06, Q2; register 'curator_quote_checks').
+
+1. **The quote occurs in the source's sealed documentation.** Runs of whitespace (spaces, tabs,
+   line breaks) are collapsed to one space on both sides, and the quote is trimmed; nothing else is
+   changed (no case folding, no punctuation or LaTeX normalization). Code finds the document and the
+   line where the quote begins; the model's own claim about where it found the quote is not used.
+   The database checks the same occurrence again when the proposal is stored (migration 0005).
+2. **The quote contains a listed term for the proposed value** (`TERMS`, case-insensitive), a first
+   filter against a quote unrelated to the value. A paraphrase without a listed term is refused,
+   which leaves the field unassigned: the safe direction. For the test temperature (a number), the
+   term is the number as written in the quote. A microstructure joined by '+' needs every part.
+
+Neither check shows that the sentence supports the value: that is for the person who accepts or
+rejects the proposal, with the quote shown beside it.
+"""
+from __future__ import annotations
+
+import re
+from dataclasses import dataclass
+from types import MappingProxyType
+from typing import Mapping
+
+QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 1500  # after collapsing whitespace; the database's bounds (0005)
+_SPACE = re.compile(r"\s+")
+
+# The listed terms per field and value (register 'curator_quote_checks'; changing it is a register change).
+TERMS: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType({
+    "test_type": MappingProxyType({"tension": ("tensile", "tension"), "compression": ("compressive", "compression")}),
+    "phase_class": MappingProxyType({"FCC": ("FCC", "face-centred cubic", "face-centered cubic"),
+                                     "BCC": ("BCC", "body-centred cubic", "body-centered cubic")}),
+    "test_temperature_band": MappingProxyType({
+        "room temperature": ("room temperature", "room-temperature", "ambient temperature"),
+        "elevated": ("elevated temperature", "high temperature", "high-temperature"),
+        "cryogenic": ("cryogenic", "liquid nitrogen", "77 K")}),
+    "microstructure": MappingProxyType({token: (token,) for token in ("FCC", "BCC", "B2", "HCP", "L12", "Laves")}),
+})
+
+
+def collapse(text: str) -> str:
+    return _SPACE.sub(" ", text).strip()
+
+
+@dataclass(frozen=True)
+class Located:
+    document: str
+    line: int  # 1-based, where the quote begins in the original document
+
+
+def locate(quote: str, documents: Mapping[str, str]) -> Located | None:
+    """Where the collapsed quote first occurs, searching documents in path order; None if nowhere."""
+    wanted = collapse(quote)
+    if not wanted:
+        return None
+    for path in sorted(documents):
+        original = documents[path]
+        collapsed, origin = [], []  # collapsed text, and for each of its characters the original index
+        in_space = False
+        for i, ch in enumerate(original):
+            if ch.isspace():
+                if not in_space and collapsed:
+                    collapsed.append(" ")
+                    origin.append(i)
+                in_space = True
+            else:
+                collapsed.append(ch)
+                origin.append(i)
+                in_space = False
+        at = "".join(collapsed).find(wanted)
+        if at >= 0:
+            return Located(path, original.count("\n", 0, origin[at]) + 1)
+    return None
+
+
+def term_for(field: str, value, quote: str) -> str | None:
+    """The listed term the quote contains for this value, or None (see the module docstring)."""
+    lowered = quote.lower()
+    if field == "test_temperature":
+        written = _number_text(value)
+        return written if written is not None and re.search(rf"(?<![\d.]){re.escape(written)}(?![\d])", quote) else None
+    if field == "microstructure" and isinstance(value, str):
+        parts = value.split("+")
+        terms = [next((t for t in TERMS["microstructure"].get(p, ()) if t.lower() in lowered), None) for p in parts]
+        return terms[0] if parts and all(terms) else None  # every part checked; the first stored (it occurs)
+    for term in TERMS.get(field, {}).get(value, ()):
+        if term.lower() in lowered:
+            return term
+    return None
+
+
+def _number_text(value) -> str | None:
+    if isinstance(value, bool) or not isinstance(value, (int, float)):
+        return None
+    return str(int(value)) if float(value).is_integer() else repr(float(value))
diff --git a/hypocurate/pipeline/agents/settings.py b/hypocurate/pipeline/agents/settings.py
new file mode 100644
index 0000000..08c064a
--- /dev/null
+++ b/hypocurate/pipeline/agents/settings.py
@@ -0,0 +1,69 @@
+"""The agents' settings: one named place per role (PRD 9.5; register 'agent_models', 'agent_settings').
+
+`MODELS` is the owner's choice for each role (2026-10-06, Q7). Each role's settings version (its
+instruction, model, limits and role-specific settings) is stored as an `agent_setting` row, append-only:
+`ensure_setting` returns the version whose stored values equal these, or adds the next version. A run
+records the versions it uses at dispatch; a registration invocation names the Curator's.
+
+The Curator's settings are here (step 8a); the other roles' instructions come with them in step 8b.
+"""
+from __future__ import annotations
+
+import json
+from types import MappingProxyType
+
+from sqlalchemy import Engine, text
+
+from hypocurate.db.retry import run_transaction
+
+MODELS = MappingProxyType({
+    "planner": "claude-opus-5-5",
+    "curator": "claude-sonnet-5-5",
+    "critic": "claude-haiku-4-5",
+    "analyst": "claude-opus-5-5",
+})
+
+CURATOR_INSTRUCTION = (
+    "You read the documentation of one scientific data source. For each field named in the targets, decide "
+    "whether the documentation explicitly states one value of that field that holds for all of the source's "
+    "measurements. If it does, give that value, using only the allowed values listed for the field (for the "
+    "test temperature, a number in degrees Celsius), and copy the one sentence that states it, word for word "
+    "as it appears in the documentation, including any markup. If the documentation does not state it "
+    "explicitly, answer \"not stated\" for that field. Do not infer, estimate or generalize, and do not use "
+    "anything you know from outside the documentation.")
+
+SETTINGS = MappingProxyType({
+    "curator": MappingProxyType({
+        "instruction": CURATOR_INSTRUCTION,
+        "model": MODELS["curator"],
+        # max_tokens covers thinking and answer; max_output_chars bounds the answer text.
+        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 20000}),
+        "settings": MappingProxyType({"reasoning_effort": "medium"}),
+    }),
+})
+
+
+def _plain(value):
+    return json.loads(json.dumps(value, default=dict))
+
+
+def ensure_setting(engine: Engine, role: str) -> int:
+    """The id of the stored settings version equal to `SETTINGS[role]`, adding the next version if none is."""
+    s = SETTINGS[role]
+    limits, extra = _plain(dict(s["limits"])), _plain(dict(s["settings"]))
+
+    def transaction(conn):
+        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('agent_setting:' || :r))"), dict(r=role))
+        found = conn.execute(text(
+            "SELECT id FROM agent_setting WHERE role = :r AND instruction = :i AND model = :m "
+            "AND limits = CAST(:l AS jsonb) AND settings = CAST(:s AS jsonb) ORDER BY version DESC LIMIT 1"),
+            dict(r=role, i=s["instruction"], m=s["model"], l=json.dumps(limits), s=json.dumps(extra))).scalar()
+        if found:
+            return found
+        return conn.execute(text(
+            "INSERT INTO agent_setting (role, version, instruction, model, limits, settings) VALUES (:r, "
+            "(SELECT coalesce(max(version), 0) + 1 FROM agent_setting WHERE role = :r), :i, :m, CAST(:l AS jsonb), "
+            "CAST(:s AS jsonb)) RETURNING id"),
+            dict(r=role, i=s["instruction"], m=s["model"], l=json.dumps(limits), s=json.dumps(extra))).scalar_one()
+
+    return run_transaction(engine, transaction)
diff --git a/hypocurate/pipeline/agents/spend.py b/hypocurate/pipeline/agents/spend.py
new file mode 100644
index 0000000..802fd80
--- /dev/null
+++ b/hypocurate/pipeline/agents/spend.py
@@ -0,0 +1,148 @@
+"""Reserving and recording model calls; the spending caps (step 8a; register 'spending_caps').
+
+**Before every request** (`reserve`): one transaction checks the caps and records the call as
+started with its maximum cost; it is finished before the request is sent, so no model call ever
+happens inside a database transaction. A run call takes the run's lock first (the locking protocol);
+every reservation then takes one month-wide advisory lock, so two reservations can never both pass
+the monthly cap. The caps count every recorded call at its reported cost, or at its maximum cost
+while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
+- a run: at most `RUN_CAP_USD` over all its calls;
+- a registration invocation (the Curator): at most `CURATION_CAP_USD` over its calls;
+- the calendar month (UTC, by the database's start time): at most `MONTH_CAP_USD` over every call
+  recorded in this database;
+- optionally a lower ceiling the caller names (the live curation call: $0.50, owner 2026-10-06),
+  over the same run or invocation.
+A refusal sends nothing, is logged in `audit_log` in its own transaction (function 'model_call',
+result 'rejected', a fixed code) and raises `SpendingRefused`.
+
+**After the request** (`finish`): one transaction (a run call takes the run's lock first) finishes
+the call exactly once, with the reported usage and its cost, or as failed with no usage (counted at
+its maximum cost) and a fixed code. Never any provider text.
+
+Limitation, stated plainly: the monthly cap counts the calls recorded in this database only; calls
+made from another database (a local or test database) are not counted toward the live site's month.
+"""
+from __future__ import annotations
+
+import json
+import logging
+from decimal import Decimal
+
+from sqlalchemy import Connection, Engine, bindparam, text
+from sqlalchemy.dialects.postgresql import JSONB
+
+from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
+from hypocurate.access.stage import actual_stage
+from hypocurate.db.retry import run_transaction
+from hypocurate.pipeline.agents.prices import PRICE_TABLE_VERSION
+
+LOG = logging.getLogger("hypocurate.pipeline")
+RUN_CAP_USD = Decimal("2")         # CLAUDE.md rule 12; register 'spending_caps'
+MONTH_CAP_USD = Decimal("50")      # CLAUDE.md rule 12; register 'spending_caps'
+CURATION_CAP_USD = Decimal("2")    # step 8a (owner, 2026-10-06): one curation, like one run
+MONTH_LOCK_KEY = 0x68636D6F6E7468  # pg_advisory_xact_lock key of the monthly cap ("hcmonth")
+CODES = {
+    "spending_cap_run": "the run's model calls would exceed the per-run cap",
+    "spending_cap_curation": "the curation's model calls would exceed the per-curation cap",
+    "spending_cap_month": "the month's model calls would exceed the monthly cap",
+    "ceiling_reached": "the calls would exceed the ceiling set for this call",
+    "invocation_unknown": "no such invocation",
+}
+FINISH_CODES = ("model_auth", "provider_rejected", "provider_unavailable", "cost_unknown")
+
+
+class SpendingRefused(Exception):
+    """No request was sent; the refusal is logged."""
+
+    def __init__(self, code: str):
+        self.code = code
+        super().__init__(f"model call refused: {CODES[code]}")
+
+
+_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
+              "VALUES (:r, :role, :stage, 'model_call', false, :d)").bindparams(bindparam("d", type_=JSONB))
+_MONTH_TOTAL = ("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
+                "WHERE date_trunc('month', started_at AT TIME ZONE 'UTC') = date_trunc('month', now() AT TIME ZONE 'UTC')")
+
+
+def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, ceiling: Decimal | None = None) -> int:
+    """The new call's id, recorded as started; or SpendingRefused (logged)."""
+    if not isinstance(max_cost, Decimal) or not max_cost > 0:
+        raise ValueError("max_cost must be a positive Decimal")
+
+    def transaction(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {int(ACCESS_LOCK_TIMEOUT_MS)}"))
+        inv = conn.execute(text("SELECT scope, run_id, stage_result_id, role FROM agent_invocation WHERE id = :i"),
+                           dict(i=invocation_id)).one_or_none()
+        if inv is None:
+            return ("refused", "invocation_unknown", None, None, None)
+        if inv.scope == "run":
+            status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=inv.run_id)).scalar_one()
+            stage = actual_stage(conn, inv.run_id, status)
+            spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
+                                      "WHERE run_id = :r"), dict(r=inv.run_id)).scalar_one()
+            cap, cap_code = RUN_CAP_USD, "spending_cap_run"
+        else:
+            stage = "registration"
+            spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
+                                      "WHERE invocation_id = :i"), dict(i=invocation_id)).scalar_one()
+            cap, cap_code = CURATION_CAP_USD, "spending_cap_curation"
+        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
+        month = conn.execute(text(_MONTH_TOTAL)).scalar_one()
+        code = (cap_code if spent + max_cost > cap else
+                "ceiling_reached" if ceiling is not None and spent + max_cost > ceiling else
+                "spending_cap_month" if month + max_cost > MONTH_CAP_USD else None)
+        if code:
+            return ("refused", code, inv, stage, {"spent": str(spent), "month": str(month)})
+        call = conn.execute(text(
+            "INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
+            "VALUES (:r, :s, :i, :o, :m, :p, :c) RETURNING id"),
+            dict(r=inv.run_id, s=inv.stage_result_id, i=invocation_id, o=inv.role, m=model, p=PRICE_TABLE_VERSION,
+                 c=max_cost)).scalar_one()
+        return ("reserved", call, None, None, None)
+
+    outcome = run_transaction(engine, transaction)
+    if outcome[0] == "reserved":
+        return outcome[1]
+    _, code, inv, stage, totals = outcome
+    _log_refusal(engine, invocation_id, inv, stage, code, max_cost, ceiling, totals)
+    raise SpendingRefused(code)
+
+
+def _log_refusal(engine, invocation_id, inv, stage, code, max_cost, ceiling, totals) -> None:
+    detail = {"result": "rejected", "code": code, "invocation": int(invocation_id), "max_cost": str(max_cost)}
+    if ceiling is not None:
+        detail["ceiling"] = str(ceiling)
+    detail.update(totals or {})
+    row = dict(r=inv.run_id if inv else None, role=inv.role if inv else "invalid", stage=stage or "none", d=detail)
+    try:
+        run_transaction(engine, lambda conn: conn.execute(_AUDIT, row))
+    except Exception as error:  # the process log is the fallback
+        LOG.error(json.dumps({"refusal_fallback": {**row, "function": "model_call"}, "error": type(error).__name__},
+                             sort_keys=True, default=str))
+
+
+def finish(engine: Engine, call_id: int, status: str, *, input_tokens: int | None = None,
+           output_tokens: int | None = None, cached_tokens: int | None = None, cost: Decimal | None = None,
+           code: str | None = None) -> None:
+    """Finishes the call once: 'succeeded' with its usage and cost, or 'failed' / 'interrupted' with
+    no usage and a fixed code."""
+    if status == "succeeded":
+        if None in (input_tokens, output_tokens, cached_tokens, cost):
+            raise ValueError("a succeeded call has its usage and cost")
+    elif status in ("failed", "interrupted"):
+        if code not in FINISH_CODES and status == "failed":
+            raise ValueError(f"unknown code {code!r}")
+    else:
+        raise ValueError(status)
+
+    def transaction(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {int(ACCESS_LOCK_TIMEOUT_MS)}"))
+        run_id = conn.execute(text("SELECT run_id FROM model_call WHERE id = :c"), dict(c=call_id)).scalar_one()
+        if run_id is not None:
+            conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
+        conn.execute(text("UPDATE model_call SET status = :st, input_tokens = :i, output_tokens = :o, "
+                          "cached_tokens = :c, cost = :cost, error = :e, finished_at = now() WHERE id = :id"),
+                     dict(st=status, i=input_tokens, o=output_tokens, c=cached_tokens, cost=cost, e=code, id=call_id))
+
+    run_transaction(engine, transaction)
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 075eebd..bda86c2 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -22,6 +22,9 @@ Each record gets one rule code, the first that applies (owner, 2026-10-05):
 2. `invalid_value`: a flag the plan maps to `invalid_value` (physically impossible).
 3. `out_of_scope`: a known value outside the scope (test type; reported temperature outside
    the room-temperature range, or a band outside the scope; microstructure, or phase class).
+   Step 8a (owner, 2026-10-06, Q4): under a plan for another band, its temperature range decides
+   a reported temperature; a band alone, with no number, is "scope not confirmed" (rule 6) when it
+   is the plan's band, out of scope otherwise.
 4. `missing_value`: composition, predictor or outcome without an accepted value.
 5. `group_unknown`: the record has no group under the set's grouping (a paper-grouped record
    without a DOI; a batch-grouped record without a batch). No group is invented (owner,
@@ -164,6 +167,7 @@ class Settings:
     survivor_order: tuple
     grouping: Mapping[str, str]
     scope_unconfirmed_ok: bool = False
+    temperature_range: tuple | None = None  # (min, max) exactly for a band other than room temperature
     conflict_survivor: bool = False  # only in 'conflicts_survivor_value' (`conflict_survivor_allowed`)
 
 
@@ -189,6 +193,8 @@ def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
         flag_rules=flag_rules, decimals=r["same_alloy_decimals"], min_grain_sizes=r["min_grain_sizes"],
         survivor_order=tuple(r["survivor_source_order"]),
         grouping={g["source"]: g["unit"] for g in r["grouping"]},
+        temperature_range=(r["temperature_range"]["min"], r["temperature_range"]["max"])
+        if "temperature_range" in r else None,
         conflict_survivor=conflict_survivor_allowed(key))
     if key == PRIMARY:
         return base
@@ -232,7 +238,15 @@ def scope(rec: Mapping, st: Settings) -> str:
         verdicts.append(None)
     # Temperature: a reported temperature decides; otherwise the band.
     t = rec["values"].get("test_temperature")
-    if _known(rec, "test_temperature", st) and t is not None:
+    if st.temperature_range is not None:  # a plan for another band (step 8a): its range decides
+        low, high = st.temperature_range
+        if _known(rec, "test_temperature", st) and t is not None:
+            verdicts.append(low <= t <= high)
+        elif _known(rec, "test_temperature_band", st):
+            verdicts.append(None if rec["categories"]["test_temperature_band"] in st.bands else False)
+        else:
+            verdicts.append(None)
+    elif _known(rec, "test_temperature", st) and t is not None:
         verdicts.append("room temperature" in st.bands and st.rt_min <= t <= st.rt_max)
     elif _known(rec, "test_temperature_band", st):
         verdicts.append(rec["categories"]["test_temperature_band"] in st.bands)
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index ebaa8b1..6f92fee 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -41,6 +41,8 @@ RULES = ("same_alloy_decimals", "duplicate_tolerance", "survivor_source_order",
 FLAG_RULE_CODES = frozenset({"invalid_value", "duplicate_counted_once", "identity_unresolved", "conflict_unresolved",
                              "in_scope"})
 MENU_RULES = frozenset({"grain_size_range", "temperature_range", "phase", "test_type"})
+ROOM_TEMPERATURE = "room temperature"
+RANGE_RULE = "temperature_range"  # a rules key, exactly for a band other than room temperature (step 8a)
 
 
 class PlanError(ValueError):
@@ -132,10 +134,26 @@ def _check_template(c: dict) -> None:
         raise PlanError("the model needs its name, hypotheses and a threshold between 0 and 1")
     if set(s) != {"alloy_class", "temperature_band", "test_type", "phase_class"} or not all(s.values()):
         raise PlanError("the scope names alloy classes, temperature bands, test types and phase classes")
-    if s["temperature_band"] != ["room temperature"]:
-        raise PlanError("sprint 1 supports the room-temperature band only")
-    if set(r) != set(RULES):
-        raise PlanError(f"the plan's rules are exactly: {', '.join(RULES)}")
+    # Step 8a (owner, 2026-10-06, Q4): one band per plan; another band than room temperature names the
+    # claim's temperature range, above (elevated) or below (cryogenic) the room-temperature rule.
+    if len(s["temperature_band"]) != 1:
+        raise PlanError("one band per plan")
+    band = s["temperature_band"][0]
+    if band not in p.SUPPORTED_BANDS:
+        raise PlanError(f"the band is one of {', '.join(p.SUPPORTED_BANDS)}")
+    expected = set(RULES) | ({RANGE_RULE} if band != ROOM_TEMPERATURE else set())
+    if set(r) != expected:
+        raise PlanError(f"the plan's rules are exactly: {', '.join(sorted(expected))} (a temperature range only "
+                        "for a band other than room temperature)")
+    if band != ROOM_TEMPERATURE:
+        tr = r[RANGE_RULE]
+        if set(tr) != {"min", "max"} or not (math.isfinite(tr["min"]) and math.isfinite(tr["max"])) \
+                or tr["min"] > tr["max"]:
+            raise PlanError("the temperature range needs a finite minimum and maximum, the minimum not above it")
+        if band == "elevated" and not tr["min"] > r["room_temperature_max"]:
+            raise PlanError("an elevated range lies above room temperature")
+        if band == "cryogenic" and not tr["max"] < r["room_temperature_min"]:
+            raise PlanError("a cryogenic range lies below room temperature")
     if not (0 <= r["same_alloy_decimals"] <= 3 and r["min_grain_sizes"] >= 2 and 0 <= r["duplicate_tolerance"] < 1
             and math.isfinite(r["room_temperature_min"]) and r["room_temperature_min"] <= r["room_temperature_max"]):
         raise PlanError("a rule is out of range")
diff --git a/hypocurate/pipeline/profile.py b/hypocurate/pipeline/profile.py
index b5e8c80..562935a 100644
--- a/hypocurate/pipeline/profile.py
+++ b/hypocurate/pipeline/profile.py
@@ -96,4 +96,11 @@ TAG_STARTING_LISTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
 PROPERTY_TAGS = MappingProxyType({"yield_strength": "yield strength",
                                   "ultimate_tensile_strength": "ultimate tensile strength", "hardness": "hardness"})
 TEST_CONDITION_TAGS = MappingProxyType({("room temperature", "tension"): "room-temperature tension",
-                                        ("room temperature", "compression"): "room-temperature compression"})
+                                        ("room temperature", "compression"): "room-temperature compression",
+                                        # Step 8a (owner, 2026-10-06, Q4): values seeded by migration 0002.
+                                        ("elevated", "tension"): "elevated temperature",
+                                        ("elevated", "compression"): "elevated temperature",
+                                        ("cryogenic", "tension"): "cryogenic",
+                                        ("cryogenic", "compression"): "cryogenic"})
+# The bands a plan may name, one per plan (step 8a, owner 2026-10-06, Q4).
+SUPPORTED_BANDS = ("room temperature", "elevated", "cryogenic")
diff --git a/hypocurate/sources/adapters/__init__.py b/hypocurate/sources/adapters/__init__.py
index 217b4f7..3f53ada 100644
--- a/hypocurate/sources/adapters/__init__.py
+++ b/hypocurate/sources/adapters/__init__.py
@@ -35,8 +35,10 @@ def extraction(source_key: str) -> dict:
 
 
 def read(version: SealedVersion) -> AdapterResult:
-    """Reads a sealed version with its source's adapter."""
+    """Reads a sealed version with its source's adapter, then applies the version's sealed curation,
+    if it has one, where the table gives no value (step 8a; `sources.curated`)."""
+    from hypocurate.sources.curated import apply_curation
     adapter = ADAPTERS.get(version.source_key)
     if adapter is None:
         raise AdapterError(f"no adapter for source {version.source_key!r}")
-    return adapter(version)
+    return apply_curation(adapter(version), version)
diff --git a/hypocurate/sources/adapters/mpea_layout.py b/hypocurate/sources/adapters/mpea_layout.py
index 28af199..e2dda23 100644
--- a/hypocurate/sources/adapters/mpea_layout.py
+++ b/hypocurate/sources/adapters/mpea_layout.py
@@ -105,9 +105,10 @@ def read(version: SealedVersion) -> AdapterResult:
     if version.grouping_unit != "paper":
         raise AdapterError(f"the MPEA-layout adapter groups by paper; version {version.id} "
                            f"has grouping unit {version.grouping_unit!r}")
-    if len(version.files) != 1:
-        raise AdapterError(f"expected one CSV file, found {sorted(version.files)}")
-    (path, content), = version.files.items()
+    # Step 8a: a version may also hold documentation and a curation file; the adapter reads its data.
+    if len(version.data_files) != 1:
+        raise AdapterError(f"expected one CSV file, found {sorted(version.data_files)}")
+    (path, content), = version.data_files.items()
     try:
         decoded = content.decode("utf-8")
     except UnicodeDecodeError as error:
diff --git a/hypocurate/sources/adapters/tamu_fcc.py b/hypocurate/sources/adapters/tamu_fcc.py
index 6b61db9..56240a9 100644
--- a/hypocurate/sources/adapters/tamu_fcc.py
+++ b/hypocurate/sources/adapters/tamu_fcc.py
@@ -18,8 +18,10 @@ spreadsheet, the source of record (step 1).
   the owner agrees they are independent enough. This adapter refuses any other unit.
 - Values not in the file are set with one of two statuses (register entry
   'assigned_value_statuses'), each with its citation:
-  - `assigned_from_source`, where the source's own documentation states them (owner,
-    2026-10-05, step 4 question 3): test type `tension`, phase class `FCC`;
+  - `assigned_from_source`, where the source's own documentation states them: from step 8a
+    (version 3) these come only from the version's sealed curation, the Curator's proposals the
+    owner accepted (`sources.curated`; test type `tension`, phase class `FCC`, both quoted from
+    paper/main.tex); this adapter leaves them not reported;
   - `assigned_by_decision`, where the source does not state them and the owner decided
     (register entries 'tamu_test_temperature' and 'tamu_microstructure', 2026-10-05):
     temperature band `room temperature`, microstructure `FCC` (single-phase).
@@ -41,7 +43,9 @@ from hypocurate.sources.versions import SealedVersion
 
 # The adapter's version, stored with every record it extracts (record.extraction; step 6).
 # Raise it whenever what the adapter returns for the same file changes.
-ADAPTER_VERSION = "2"  # 2: the two assigned statuses; band and microstructure by decision (step 6)
+# 2: the two assigned statuses; band and microstructure by decision (step 6). 3 (step 8a): test type and
+# phase class no longer assigned here; a curated version supplies them (owner, 2026-10-06).
+ADAPTER_VERSION = "3"
 
 SHEET = "GS_MasterTable_Iterations "  # verbatim: the sheet name ends with a space
 HEADER = (
@@ -63,13 +67,6 @@ DATASET_REFERENCE = ("Mulukutla, M. et al. (2026). Revisiting Hall-Petch strengt
                      "doi:10.5281/zenodo.22798856")
 
 _REPO = "ArroyaveLab/2026-mulukutla-hall-petch@11390ee516c1a17cacdde318b40d5d6889d4007f"
-TEST_TYPE_CITATION = Citation(
-    f"{_REPO} paper/main.tex", "line 177 (Dataset and descriptors, Alloy Synthesis and characterization)",
-    "Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
-    "tests provided the HV.")
-PHASE_CITATION = Citation(
-    f"{_REPO} paper/main.tex", "line 173 (Dataset and descriptors, Alloy Synthesis and characterization)",
-    "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.")
 COMPOSITION_UNIT_CITATION = Citation(
     f"{_REPO} paper/main.tex", "line 399 (Results, Family 3)",
     "Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider "
@@ -90,6 +87,8 @@ MICROSTRUCTURE_DECISION = Citation(
 TEMPERATURE_NOT_REPORTED = ("no per-record temperature; the source states no test temperature for its "
                             "own measurements (the room-temperature band is assigned by decision)")
 NO_COLUMN = "the source has no column for this field"
+CURATED = ("the spreadsheet has no column for this field; the source's documentation states it, and a curated "
+           "version supplies it (step 8a)")
 
 
 def reported_text(value) -> str:
@@ -143,8 +142,8 @@ def _harmonize(cells: dict) -> tuple[dict[str, Value], str | None]:
     h["cold_work"] = _number(cells["Cold Work (%Reduction)"], "% reduction")
     h["recrystallization_temperature"] = _number(cells["Recrystallization Temp(℃)"], "°C")
     h["holding_time"] = _number(cells["Holding time (h)"], "h")
-    h["test_type"] = Value("tension", None, "assigned_from_source", citation=TEST_TYPE_CITATION)
-    h["phase_class"] = Value("FCC", None, "assigned_from_source", citation=PHASE_CITATION)
+    h["test_type"] = Value(None, None, "not_reported", CURATED)
+    h["phase_class"] = Value(None, None, "not_reported", CURATED)
     h["test_temperature"] = Value(None, "°C", "not_reported", TEMPERATURE_NOT_REPORTED)
     h["test_temperature_band"] = Value("room temperature", None, "assigned_by_decision",
                                        citation=TEMPERATURE_DECISION)
@@ -162,9 +161,10 @@ def read(version: SealedVersion) -> AdapterResult:
     if version.grouping_unit != "dataset":
         raise AdapterError(f"the Texas A&M adapter supports the grouping unit 'dataset' only "
                            f"(PRD 17, decision 9); version {version.id} has {version.grouping_unit!r}")
-    if len(version.files) != 1:
-        raise AdapterError(f"expected one spreadsheet, found {sorted(version.files)}")
-    (path, content), = version.files.items()
+    # Step 8a: a version may also hold documentation and a curation file; the adapter reads its data.
+    if len(version.data_files) != 1:
+        raise AdapterError(f"expected one spreadsheet, found {sorted(version.data_files)}")
+    (path, content), = version.data_files.items()
     try:
         workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False)
     except (zipfile.BadZipFile, OSError, ValueError, KeyError) as error:
diff --git a/hypocurate/sources/curated.py b/hypocurate/sources/curated.py
new file mode 100644
index 0000000..7b69599
--- /dev/null
+++ b/hypocurate/sources/curated.py
@@ -0,0 +1,61 @@
+"""Applying a sealed curation to a source's records (step 8a; owner, 2026-10-06, Q2).
+
+A curated version holds `curation.json`: the Curator's proposals a person accepted, sealed with the
+source (`sources.curation.seal_curation`). Each value applies to every record of the version **only
+where the record's field is not reported** (the table gives no value and no owner decision assigned
+one); it never overrides a reported, converted or decided value. It is stored with the status
+'assigned_from_source' and a citation: the documentation file, the line, the exact quote, and the
+proposal, model and settings version, who accepted it and when.
+
+A curation file that cannot be read exactly as written (wrong format, another source, a field that is
+not a target) refuses the whole version, like any malformed file (register 'malformed_files_refused').
+"""
+from __future__ import annotations
+
+import dataclasses
+import json
+from typing import Mapping
+
+from hypocurate.access.vocabulary import CURATION_TARGETS
+from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation, Value
+from hypocurate.sources.versions import CURATION_PATH, SealedVersion
+
+CURATION_FORMAT = 1
+ENTRY_KEYS = {"value", "document", "line", "quote", "term", "proposal", "model", "agent_setting_version",
+              "accepted_by", "accepted_at", "note"}
+
+
+def curated_values(version: SealedVersion) -> dict[str, Value]:
+    raw = version.files.get(CURATION_PATH)
+    if raw is None:
+        return {}
+    try:
+        doc = json.loads(raw.decode("utf-8"))
+        if doc.get("format") != CURATION_FORMAT or doc.get("source") != version.source_key:
+            raise ValueError("format or source")
+        out = {}
+        for field, e in doc["values"].items():
+            if field not in CURATION_TARGETS or set(e) != ENTRY_KEYS:
+                raise ValueError(f"entry {field!r}")
+            where = (f"line {int(e['line'])}; Curator proposal {int(e['proposal'])} ({e['model']}, settings version "
+                     f"{int(e['agent_setting_version'])}), accepted by {e['accepted_by']} on {e['accepted_at'][:10]}")
+            out[field] = Value(e["value"], HARMONIZED_FIELDS[field], "assigned_from_source",
+                               citation=Citation(f"{version.source_key}: {e['document']} (sealed with the source)",
+                                                 where, e["quote"]))
+        return out
+    except (ValueError, KeyError, TypeError, AttributeError) as error:
+        raise AdapterError(f"{CURATION_PATH}: cannot be read as a curation file ({error})") from None
+
+
+def apply_curation(result: AdapterResult, version: SealedVersion) -> AdapterResult:
+    values: Mapping[str, Value] = curated_values(version)
+    if not values:
+        return result
+    records = []
+    for r in result.records:
+        h = dict(r.harmonized)
+        for field, value in values.items():
+            if h[field].status == "not_reported":
+                h[field] = value
+        records.append(dataclasses.replace(r, harmonized=h))
+    return AdapterResult(tuple(records), result.blank_rows)
diff --git a/hypocurate/sources/curation.py b/hypocurate/sources/curation.py
new file mode 100644
index 0000000..b321cae
--- /dev/null
+++ b/hypocurate/sources/curation.py
@@ -0,0 +1,217 @@
+"""The curation workflow at source registration (step 8a; owner, 2026-10-06, Q2 and Q3;
+register 'curator_registration', 'curation_acceptance').
+
+1. `curate(key)`: one Curator call on the source's newest sealed version, through one registration
+   invocation (`agent_invocation`) bound by the dispatcher; refused before any model call for a
+   source not grouped by dataset (a compilation of papers: a source-wide value would be a guess for
+   each paper), for a version without documentation, or for a version already curated. Every
+   proposal is stored (`curator_proposal`) as code decided it.
+2. `decide(proposal, accepted|rejected, by)`: a person's decision on a proposal that passed the
+   checks, written once with the database's time. The command line takes the name as given.
+3. `seal_curation(key)`: a new sealed version: the base version's files plus `curation.json`, the
+   accepted values only, each with its quote, document, line, proposal, model and settings version,
+   who accepted it and when. Unanswered and rejected proposals are left out (the field stays
+   unassigned). Sealed by the same registration code, so its fingerprint covers the curation.
+4. `curation_file(key)`: that file's bytes, to be frozen into `data/` (with the owner's approval):
+   registering the frozen source then gives the same curated version in any database, with no
+   model call.
+
+Adapters apply the curated values only where the table gives no value (`adapters.apply_curation`).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date
+from decimal import Decimal
+from typing import Any, Mapping
+
+from sqlalchemy import Engine, text
+from sqlalchemy.exc import IntegrityError
+
+from hypocurate.db.retry import run_transaction
+from hypocurate.sources.curated import CURATION_FORMAT
+from hypocurate.sources.versions import (CURATION_PATH, SOURCES, Registered, _register_in, latest_sealed_version_id,
+                                         load_sealed_version)
+
+CODES = {
+    "unknown_source": "no such source",
+    "compilation_source": "the source is grouped by paper (a compilation): a value for the whole source would be a "
+                          "guess for each paper, so it is not curated (owner, 2026-10-06)",
+    "no_documentation": "the source's newest version holds no documentation",
+    "already_curated": "the source's newest version is already a curated version",
+    "unknown_proposal": "no such proposal",
+    "not_decidable": "only a proposal that passed the checks can be accepted or rejected",
+    "already_decided": "this proposal has already been decided",
+    "nothing_curated": "the version has no curation invocation",
+    "conflicting_acceptances": "more than one proposal is accepted for the same field",
+}
+
+
+class CurationRefused(Exception):
+    def __init__(self, code: str):
+        self.code = code
+        super().__init__(f"{code}: {CODES[code]}")
+
+
+def _version(engine: Engine, key: str):
+    if key not in SOURCES:
+        raise CurationRefused("unknown_source")
+    with engine.connect() as conn:
+        return load_sealed_version(conn, latest_sealed_version_id(conn, key))
+
+
+def curate(engine: Engine, key: str, *, ceiling: Decimal | None = None,
+           client_options: Mapping[str, Any] | None = None) -> dict:
+    """One Curator call and its stored proposals; a summary for the command line."""
+    from hypocurate.access.dispatch import bind_invocation
+    from hypocurate.access.inputs import role_input
+    from hypocurate.pipeline.agents import curator
+    from hypocurate.pipeline.agents.interface import call_agent
+    from hypocurate.pipeline.agents.settings import SETTINGS, ensure_setting
+
+    version = _version(engine, key)
+    if version.grouping_unit != "dataset":
+        raise CurationRefused("compilation_source")
+    if CURATION_PATH in version.files:
+        raise CurationRefused("already_curated")
+    if not version.documentation:
+        raise CurationRefused("no_documentation")
+    setting = ensure_setting(engine, "curator")
+    invocation = run_transaction(engine, lambda conn: conn.execute(text(
+        "INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
+        "VALUES ('registration', :v, 'curator', :a) RETURNING id"), dict(v=version.id, a=setting)).scalar_one())
+    data = role_input(bind_invocation(engine, invocation))
+    s = SETTINGS["curator"]
+    result = call_agent(engine, invocation, curator.signature(s["instruction"]), curator.render_inputs(data),
+                        model=s["model"], max_tokens=s["limits"]["max_tokens"],
+                        max_output_chars=s["limits"]["max_output_chars"], ceiling=ceiling,
+                        lm_options=dict(s["settings"]), client_options=client_options, check=curator.check)
+    summary = {"source": key, "version": version.id, "invocation": invocation, "attempts": result.attempts,
+               "calls": result.calls}
+    if result.failure is not None:
+        return {**summary, "status": "failed", "code": result.failure, "proposals": [], "ignored_keys": []}
+    proposals, ignored = curator.proposals_from(result.outputs["proposals"], data["source_documentation"]["documents"])
+
+    def store(conn):
+        ids = []
+        for p in proposals:
+            ids.append(conn.execute(text(
+                "INSERT INTO curator_proposal (invocation_id, source_version_id, field, status, value, quote, "
+                "document_path, line, term, refusal_code) VALUES (:i, :v, :f, :st, CAST(:val AS jsonb), :q, :d, :l, "
+                ":t, :rc) RETURNING id"),
+                # No value is SQL NULL, never the JSON value null (the database's shape checks).
+                dict(i=invocation, v=version.id, f=p.field, st=p.status,
+                     val=None if p.value is None else json.dumps(p.value), q=p.quote, d=p.document,
+                     l=p.line, t=p.term, rc=p.refusal_code)).scalar_one())
+        return ids
+
+    ids = run_transaction(engine, store)
+    return {**summary, "status": "done", "ignored_keys": ignored,
+            "proposals": [{"id": i, **p.__dict__} for i, p in zip(ids, proposals)]}
+
+
+def proposals(engine: Engine, key: str) -> list[dict]:
+    """The proposals for the source's newest version, with any decision."""
+    version = _version(engine, key)
+    with engine.connect() as conn:
+        rows = conn.execute(text(
+            "SELECT p.id, p.invocation_id, p.field, p.status, p.value, p.quote, p.document_path, p.line, p.term, "
+            "p.refusal_code, d.decision, d.decided_by, d.decided_at FROM curator_proposal p "
+            "LEFT JOIN curator_decision d ON d.proposal_id = p.id WHERE p.source_version_id = :v ORDER BY p.id"),
+            dict(v=version.id)).mappings().all()
+    return [{**r, "decided_at": r["decided_at"].isoformat() if r["decided_at"] else None} for r in rows]
+
+
+def decide(engine: Engine, proposal_id: int, decision: str, by: str, note: str | None = None) -> dict:
+    if decision not in ("accepted", "rejected"):
+        raise ValueError(decision)
+
+    def transaction(conn):
+        status = conn.execute(text("SELECT status FROM curator_proposal WHERE id = :p"),
+                              dict(p=proposal_id)).scalar_one_or_none()
+        if status is None:
+            return "unknown_proposal"
+        if status != "proposed":
+            return "not_decidable"
+        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM curator_decision WHERE proposal_id = :p)"),
+                        dict(p=proposal_id)).scalar_one():
+            return "already_decided"
+        conn.execute(text("INSERT INTO curator_decision (proposal_id, decision, decided_by, note) "
+                          "VALUES (:p, :d, :b, :n)"), dict(p=proposal_id, d=decision, b=by, n=note))
+        return None
+
+    try:
+        code = run_transaction(engine, transaction)
+    except IntegrityError:  # a concurrent second decision (unique), or the database's own refusal
+        code = "already_decided"
+    if code:
+        raise CurationRefused(code)
+    return {"proposal": proposal_id, "decision": decision, "decided_by": by}
+
+
+def _accepted(conn, version_id: int) -> list:
+    return conn.execute(text(
+        "SELECT p.id, p.field, p.value, p.quote, p.document_path, p.line, p.term, s.model, s.version AS setting_version, "
+        "d.decided_by, d.decided_at, d.note FROM curator_proposal p "
+        "JOIN curator_decision d ON d.proposal_id = p.id AND d.decision = 'accepted' "
+        "JOIN agent_invocation i ON i.id = p.invocation_id JOIN agent_setting s ON s.id = i.agent_setting_id "
+        "WHERE p.source_version_id = :v ORDER BY p.field, p.id"), dict(v=version_id)).all()
+
+
+def curation_document(version, accepted) -> bytes:
+    """The curation file: accepted values only, deterministic bytes."""
+    values = {}
+    for r in accepted:
+        values[r.field] = {"value": r.value, "document": r.document_path, "line": r.line, "quote": r.quote,
+                           "term": r.term, "proposal": r.id, "model": r.model, "agent_setting_version": r.setting_version,
+                           "accepted_by": r.decided_by, "accepted_at": r.decided_at.isoformat(), "note": r.note}
+    body = {"format": CURATION_FORMAT, "source": version.source_key,
+            "base_version": {"label": version.label, "fingerprint": version.fingerprint}, "values": values}
+    return (json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
+
+
+def seal_curation(engine: Engine, key: str) -> Registered:
+    version = _version(engine, key)
+    if CURATION_PATH in version.files:
+        raise CurationRefused("already_curated")
+    definition = SOURCES[key]
+
+    def transaction(conn):
+        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM agent_invocation WHERE source_version_id = :v)"),
+                            dict(v=version.id)).scalar_one():
+            return ("refused", "nothing_curated")
+        accepted = _accepted(conn, version.id)
+        fields = [r.field for r in accepted]
+        if len(fields) != len(set(fields)):
+            return ("refused", "conflicting_acceptances")
+        files = {**dict(version.files), CURATION_PATH: curation_document(version, accepted)}
+        obtained = conn.execute(text("SELECT obtained_on FROM source_version WHERE id = :v"),
+                                dict(v=version.id)).scalar_one()
+        return ("ok", _register_in(conn, definition, files, obtained, label=f"{version.label} + curation"))
+
+    outcome = run_transaction(engine, transaction)
+    if outcome[0] == "refused":
+        raise CurationRefused(outcome[1])
+    return outcome[1]
+
+
+def curate_guarded(payload: dict) -> dict:
+    """The command line's `sources curate`, run in the guarded process (the tripwire watches the agent
+    code). Only JSON-safe values cross back; the parent never prints the child's error text."""
+    from hypocurate.config import load_settings
+    from hypocurate.db.engine import make_engine
+    engine = make_engine(load_settings(web=False).database_url)
+    try:
+        ceiling = Decimal(payload["ceiling"]) if payload.get("ceiling") is not None else None
+        return json.loads(json.dumps(curate(engine, payload["key"], ceiling=ceiling,
+                                            client_options=payload.get("client_options")), default=str))
+    finally:
+        engine.dispose()
+
+
+def curation_file(engine: Engine, key: str) -> bytes:
+    """The curation file of the source's newest (curated) version."""
+    version = _version(engine, key)
+    if CURATION_PATH not in version.files:
+        raise CurationRefused("nothing_curated")
+    return version.files[CURATION_PATH]
diff --git a/hypocurate/sources/manifest.py b/hypocurate/sources/manifest.py
index 3224d37..b8afa41 100644
--- a/hypocurate/sources/manifest.py
+++ b/hypocurate/sources/manifest.py
@@ -38,7 +38,9 @@ class FileEntry:
 def file_entries(manifest: dict) -> list[FileEntry]:
     entries = []
     for source_id, source in manifest["sources"].items():
-        for f in source["files"]:
+        # Step 8a (owner, 2026-10-06): a source's documentation is frozen too, in its own list
+        # (its origin is not always the data's commit), and checked like every other file.
+        for f in source["files"] + source.get("documentation", []) + source.get("curation", []):
             entries.append(FileEntry(f"sources/{source_id}", f["path"], f["sha256"], f["bytes"]))
     for f in manifest["controlled_duplicates"]["files"]:
         entries.append(FileEntry("controlled_duplicates", f["path"], f["sha256"], f["bytes"]))
diff --git a/hypocurate/sources/versions.py b/hypocurate/sources/versions.py
index 0a353d1..06b01af 100644
--- a/hypocurate/sources/versions.py
+++ b/hypocurate/sources/versions.py
@@ -32,7 +32,24 @@ from hypocurate.sources.manifest import REPO_ROOT, load_manifest
 DATA_DIR = REPO_ROOT / "data"
 MAX_FILE_BYTES = 5 * 1024 * 1024  # the source_file CHECK (owner decision, 2026-10-04)
 # The source_file path CHECK, in Python, so an unsafe path is refused before the database sees it.
+# A data file (0001's rule). Step 8a (migration 0005): the rule by role; a path tells its role.
 SAFE_STORED_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)")
+DOCUMENTATION_PATH = re.compile(r"documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)")
+CURATION_PATH = "curation.json"
+DOCUMENTATION_DIR = "documentation"
+
+
+def file_role(path: str) -> str:
+    """'data', 'documentation' or 'curation', from the path alone (the database's rule by role);
+    RegistrationError for a path no role allows."""
+    if isinstance(path, str):
+        if path == CURATION_PATH:
+            return "curation"
+        if DOCUMENTATION_PATH.fullmatch(path):
+            return "documentation"
+        if SAFE_STORED_PATH.fullmatch(path) and not path.startswith(DOCUMENTATION_DIR + "/"):
+            return "data"
+    raise RegistrationError(f"unsafe stored path {path!r}")
 
 
 class RegistrationError(Exception):
@@ -53,8 +70,7 @@ def files_digest(files: Mapping[str, bytes]) -> str:
     """SHA-256 of one line "<sha256>  <path>\\n" per file, sorted by path bytewise
     (the database sorts with COLLATE "C"). The same as `hc_files_digest`."""
     for path in files:
-        if not SAFE_STORED_PATH.fullmatch(path):
-            raise RegistrationError(f"unsafe stored path {path!r}")
+        file_role(path)
     listing = "".join(f"{sha256_hex(files[p])}  {p}\n" for p in sorted(files, key=lambda p: p.encode()))
     return sha256_hex(listing.encode("utf-8"))
 
@@ -101,6 +117,11 @@ class SourceDefinition:
     # Constructed test data (step 6): its records enter only a run marked as a test
     # (run.experiment_flags constructed_test_data; register 'constructed_test_runs').
     constructed: bool = False
+    # Step 8a (owner, 2026-10-06, Q1): the source's frozen documentation, stored with its data in the
+    # sealed version (paths inside `directory`, under documentation/), and, once the owner has
+    # accepted the Curator's proposals and the file is frozen, its curation file (curation.json).
+    documentation_files: tuple[str, ...] = ()
+    curation_file: str | None = None
 
 
 SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
@@ -110,6 +131,7 @@ SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
         address="https://github.com/CitrineInformatics/MPEA_dataset",
         properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
         enabled=True, directory="sources/mpea", data_files=("MPEA_dataset.csv",),
+        documentation_files=("documentation/Borg2020_PMC7722748.xml",),
         version_label="commit d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e",
         manifest_section=("sources", "mpea")),
     "tamu_fcc": SourceDefinition(
@@ -122,6 +144,9 @@ SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
         enabled=True, directory="sources/tamu_fcc",
         # The spreadsheet is the source of record (step 1); only files the adapter reads are stored.
         data_files=("Grain_Size_Summary_v3.xlsx",),
+        documentation_files=("documentation/main.tex", "documentation/supplementary.tex"),
+        # Step 8a: the owner's accepted Curator values (test type, phase class), frozen.
+        curation_file="curation.json",
         version_label="v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f",
         manifest_section=("sources", "tamu_fcc")),
     "controlled_duplicates": SourceDefinition(
@@ -142,13 +167,14 @@ def _manifest_files(definition: SourceDefinition, manifest: dict) -> tuple[dict,
     for part in definition.manifest_section:
         section = section[part]
     obtained = section.get("retrieved") or section.get("built")
-    return {f["path"]: f for f in section["files"]}, obtained
+    return {f["path"]: f for f in section["files"] + section.get("documentation", []) + section.get("curation", [])}, obtained
 
 
 def read_definition_files(definition: SourceDefinition, data_dir: Path = DATA_DIR,
                           manifest: dict | None = None) -> tuple[dict[str, bytes], date]:
-    """Reads a source's data files from disk, checks each against its manifest entry
-    (SHA-256 and size) and returns {stored path: bytes} and the date obtained."""
+    """Reads a source's files from disk (its data files, and from step 8a its documentation and any
+    curation file), checks each against its manifest entry (SHA-256 and size) and returns
+    {stored path: bytes} and the date obtained."""
     from hypocurate.access import file_guard  # here, not at the top: the access layer imports this module
     if file_guard.installed():
         raise RegistrationError("source registration reads data/ and cannot run in a guarded pipeline "
@@ -157,9 +183,13 @@ def read_definition_files(definition: SourceDefinition, data_dir: Path = DATA_DI
     listed, obtained = _manifest_files(definition, manifest)
     source_dir = safe_path_within(data_dir, definition.directory)
     files: dict[str, bytes] = {}
-    for name in definition.data_files:
-        if not SAFE_STORED_PATH.fullmatch(name):
-            raise RegistrationError(f"unsafe stored path {name!r}")
+    names = definition.data_files + definition.documentation_files + (
+        (definition.curation_file,) if definition.curation_file else ())
+    for name in names:
+        expected = ("data" if name in definition.data_files else
+                    "documentation" if name in definition.documentation_files else "curation")
+        if file_role(name) != expected:  # raises RegistrationError for a path no role allows
+            raise RegistrationError(f"{name!r} is not a {expected} file path")
         path = safe_path_within(source_dir, name)
         manifest_path = f"data/{definition.directory}/{name}"
         entry = listed.get(manifest_path)
@@ -190,7 +220,11 @@ class Registered:
 INTERPRETATION = ("source_type", "data_kind", "grouping_unit")
 
 
-def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes], obtained: date) -> Registered:
+def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes], obtained: date,
+                 label: str | None = None) -> Registered:
+    """Registers and seals a version of `d` holding `files` (or finds the identical sealed one).
+    `label`: the version's label (default: the definition's); a curated version names its own."""
+    label = label or d.version_label
     digest = files_digest(files)
     identity = version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)
     conn.execute(text(
@@ -218,17 +252,17 @@ def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes],
         return Registered(d.key, source_id, existing[0], existing[1], existing[2], identity, created=False)
     version_id = conn.execute(text(
         "INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, :l, :o) RETURNING id"),
-        dict(s=source_id, l=d.version_label, o=obtained)).scalar_one()
+        dict(s=source_id, l=label, o=obtained)).scalar_one()
     for path in sorted(files):
         conn.execute(text(
-            "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)"),
-            dict(v=version_id, p=path, h=sha256_hex(files[path]), c=files[path]))
+            "INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES (:v, :p, :h, :c, :r)"),
+            dict(v=version_id, p=path, h=sha256_hex(files[path]), c=files[path], r=file_role(path)))
     sealed = conn.execute(text(
         "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v "
         "RETURNING files_digest, fingerprint"), dict(v=version_id, fp=identity)).one()
     if sealed[0] != digest or sealed[1] != identity:
         raise RegistrationError("the database's files digest differs from the one computed here")
-    return Registered(d.key, source_id, version_id, d.version_label, digest, identity, created=True)
+    return Registered(d.key, source_id, version_id, label, digest, identity, created=True)
 
 
 def register(engine: Engine, key: str, data_dir: Path = DATA_DIR, manifest: dict | None = None) -> Registered:
@@ -260,6 +294,16 @@ class SealedVersion:
     def __post_init__(self):
         object.__setattr__(self, "files", MappingProxyType(dict(self.files)))
 
+    @property
+    def data_files(self) -> Mapping[str, bytes]:
+        """The files an adapter reads (step 8a: a version may also hold documentation and curation)."""
+        return MappingProxyType({p: c for p, c in self.files.items() if file_role(p) == "data"})
+
+    @property
+    def documentation(self) -> Mapping[str, bytes]:
+        """The source's own documentation, which the Curator reads (step 8a)."""
+        return MappingProxyType({p: c for p, c in self.files.items() if file_role(p) == "documentation"})
+
     def verify(self) -> None:
         """Raises UnsealedVersion unless the version is sealed and its bytes give exactly
         its stored files digest and identity. Every adapter calls this before parsing."""
diff --git a/pyproject.toml b/pyproject.toml
index 558ef77..119a215 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -23,6 +23,9 @@ dependencies = [
     # Step 7: the statistics module (numpy linear algebra, scipy t and binomial distributions).
     "numpy>=2.0",
     "scipy>=1.14",
+    # Step 8: the agents (DSPy modules; model calls through litellm).
+    "dspy>=3.4",
+    "litellm>=1.104",
 ]
 
 [project.optional-dependencies]
````

## 3. New test files

### `tests/stub_provider.py`

```python
"""A local stand-in for the model provider's HTTP API (step 8a), for tests only.

litellm sends its real HTTP request to it (`client_options(stub)` gives the address and a dummy key),
so the tests see the actual outbound request as bytes, exactly as the provider would, and replay
scripted replies in the provider's format: a text answer with usage, an error status, a timeout, a
missing usage, a refusal, a tool call, a truncated answer. Nothing leaves the machine.

`on_request(callback)` runs a callback while a request is being served (for example to check that the
caller holds no open database transaction at that moment).
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DUMMY_KEY = "stub-key-not-a-secret"


def reply(text, *, input_tokens=1200, output_tokens=150, cache_read=0, cache_write=0, stop="end_turn"):
    return {"kind": "json", "status": 200, "body": {
        "id": "msg_stub", "type": "message", "role": "assistant", "model": "stub",
        "content": [{"type": "text", "text": text}], "stop_reason": stop, "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                  "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write}}}


def error(status, kind, message="stub error"):
    return {"kind": "json", "status": status, "body": {"type": "error", "error": {"type": kind, "message": message}}}


def timeout(seconds):
    return {"kind": "sleep", "seconds": seconds}


def no_usage(text):
    r = reply(text)
    del r["body"]["usage"]
    return r


def refusal():
    r = reply("")
    r["body"]["content"] = []
    r["body"]["stop_reason"] = "refusal"
    return r


def tool_call():
    r = reply("")
    r["body"]["content"] = [{"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "/etc/x"}}]
    r["body"]["stop_reason"] = "tool_use"
    return r


def fields(**values) -> str:
    """An answer in DSPy's ChatAdapter form."""
    return "".join(f"[[ ## {k} ## ]]\n{v}\n\n" for k, v in values.items()) + "[[ ## completed ## ]]"


class StubProvider:
    def __init__(self):
        self.requests: list[dict] = []
        self.script: deque = deque()
        self._callback = None
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("content-length", 0)))
                stub.requests.append({"path": self.path, "headers": dict(self.headers), "raw": raw})
                if stub._callback:
                    stub._callback()
                step = stub.script.popleft() if stub.script else error(500, "api_error", "no scripted reply")
                if step["kind"] == "sleep":
                    time.sleep(step["seconds"])
                    step = reply("too late")
                body = json.dumps(step["body"]).encode()
                self.send_response(step["status"])
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.base_url = f"http://127.0.0.1:{self._server.server_address[1]}"

    def queue(self, *steps):
        self.script.extend(steps)
        return self

    def on_request(self, callback):
        self._callback = callback

    def bodies(self) -> list[dict]:
        return [json.loads(r["raw"]) for r in self.requests]

    def close(self):
        self._server.shutdown()
        self._server.server_close()


def client_options(stub: StubProvider, timeout_seconds: float = 30) -> dict:
    return {"api_base": stub.base_url, "api_key": DUMMY_KEY, "timeout": timeout_seconds}
```
### `tests/test_access_curator.py`

```python
"""Step 8a: the Curator's access at registration (owner, 2026-10-06, Q2; safeguard change).

The Curator runs when a source version is registered, never in a run. It is bound by
`dispatch.bind_invocation` from one registration invocation, and its complete input is the
documentation of that one sealed version and the target fields: no data file (which holds outcome
values), no claim (so not its direction), no plan, no other version. Every read is logged with no
run, naming the version and the invocation.

What these tests do not cover: the model request built from this input (the agent-core tests,
through the local stub provider), and anything the documentation itself says.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

from access_testing import registration_access_for
from hypocurate.access import AccessDenied, AccessFailed, bind, bind_invocation, role_input
from hypocurate.access.allowlist import FIELDS, allowed
from hypocurate.access.context import AccessContext
from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.db.models import CURATION_FIELDS
from model_builder import World

PLANTED_OUTCOME = 987.6543  # a yield strength in the data file
DATA = f"alloy,grain_size,yield_strength\nZQX1,4.0,{PLANTED_OUTCOME}\n".encode()
DOC = ("Quasistatic tensile testing was used to determine 0.2% offset YS.\n"
       "The dataset contains 94 FCC alloy conditions.\n")
OTHER_DOC = "A different version's documentation: ZQOTHERDOC.\n"


@pytest.fixture
def w(db):
    return World(db)


def sealed(w, key, label, doc):
    v = w.new_version(key, label)
    w.add_file(v, "table.csv", DATA + label.encode())
    w.add_file(v, "documentation/main.tex", doc.encode(), role="documentation")
    w.seal(v)
    return v


def registration(w, version):
    return w.val("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                 "VALUES ('registration', :v, 'curator', :a) RETURNING id", v=version, a=w.agent_setting("curator"))


def audit(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT run_id, role, stage, function, allowed, detail FROM audit_log ORDER BY id")).all()


def test_the_curator_is_listed_only_at_registration_with_two_fields():
    assert allowed("curator", "registration") == {"source_documentation", "curation_targets"}
    assert set(CURATION_TARGETS) == set(CURATION_FIELDS)
    assert "source_content" not in FIELDS and "plan_fields_to_extract" not in FIELDS


def test_bind_invocation_binds_the_curator_to_its_version_with_no_run(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    inv = registration(w, v)
    a = bind_invocation(db, inv)
    assert a.context == AccessContext(None, "curator", "registration", "tamu_fcc", w.agent_setting("curator"),
                                      source_version_id=v, invocation_id=inv)
    [row] = [r for r in audit(db) if r.function == "bind"]
    assert row.run_id is None and row.allowed and row.stage == "registration"
    assert row.detail["source_version"] == v and row.detail["invocation"] == inv


def test_the_curators_complete_input_is_its_versions_documentation_and_the_targets(w, db):
    """A run exists whose claim states the direction, and the version's data file holds a planted
    outcome value; another version has its own documentation. None of it reaches the Curator."""
    w.running()  # a run with the claim "Yield strength rises as grain size falls"
    v = sealed(w, "tamu_fcc", "docs", DOC)
    sealed(w, "tamu_fcc", "other", OTHER_DOC)
    got = role_input(bind_invocation(db, registration(w, v)))
    assert set(got) == {"source_documentation", "curation_targets"}
    assert got["source_documentation"] == {"source": "tamu_fcc", "documents": {"documentation/main.tex": DOC}}
    assert got["curation_targets"] == {f: dict(s) for f, s in CURATION_TARGETS.items()}
    encoded = json.dumps(got)
    for absent in (str(PLANTED_OUTCOME), "9876543", "ZQX1", "table.csv", "ZQOTHERDOC", "rises", "grain size falls"):
        assert absent not in encoded, absent
    reads = [r for r in audit(db) if r.function != "bind"]
    assert {(r.function, r.allowed) for r in reads} == {("source_documentation", True), ("curation_targets", True)}
    assert all(r.run_id is None and r.detail["source_version"] == v for r in reads)


def test_a_registration_access_reads_no_run_field(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    a = bind_invocation(db, registration(w, v))
    for field in ("claim", "records_full", "sources_meta", "plan", "record_counts", "flags_kind"):
        with pytest.raises(AccessDenied) as denied:
            a.get(field)
        assert denied.value.code == "not_on_list"


def test_a_context_naming_another_version_or_role_is_refused(w, db):
    v = sealed(w, "tamu_fcc", "docs", DOC)
    other = sealed(w, "tamu_fcc", "other", OTHER_DOC)
    inv = registration(w, v)
    for a in (registration_access_for(db, inv, other), registration_access_for(db, inv, v, role="planner")):
        with pytest.raises(AccessDenied):
            a.get("source_documentation")
    with pytest.raises(AccessDenied) as denied:
        registration_access_for(db, inv, other).get("source_documentation")
    assert denied.value.code == "stage_mismatch"


def test_an_unknown_invocation_is_a_logged_failure(w, db):
    with pytest.raises(AccessFailed) as failed:
        bind_invocation(db, 10 ** 9)
    assert failed.value.code == "unknown_invocation"
    [row] = audit(db)
    assert row.run_id is None and not row.allowed and row.detail == {"result": "failed", "code": "unknown_invocation",
                                                                      "invocation": 10 ** 9}
    with pytest.raises(AccessFailed) as failed:
        registration_access_for(db, 10 ** 9, 1).get("curation_targets")
    assert failed.value.code == "unknown_invocation"


def test_bind_invocation_for_a_run_takes_the_run_and_setting_from_the_record(w, db):
    """Two valid runs: the invocation of run B binds run B, whatever the caller holds."""
    a_run, b_run = w.running(agents=True), w.running(agents=True)
    inv_b = w.invocation(b_run, w.stage(b_run))
    got = bind_invocation(db, inv_b)
    setting = w.val("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = 'planner'", r=b_run)
    assert got.context == AccessContext(b_run, "planner", "before_lock", None, setting, invocation_id=inv_b)
    assert bind(db, a_run, setting).context.run_id == a_run  # bind itself takes what it is given
```
### `tests/test_agent_core.py`

```python
"""Step 8a: the request path every agent call takes (register 'model_call_recording',
'request_failure_policy', 'spending_caps', 'model_prices').

Each test drives real requests through DSPy and litellm to a local stub of the provider
(`stub_provider`), so what is checked is the actual outbound request, as bytes, and the rows the
database holds afterwards. One test per row of the failure table approved for step 8a, plus the
reservation before each request, the caps, the month-wide lock, and no open transaction while a
request is in flight.

What these tests do not cover: a real provider's behaviour (the live tests, run only with the
owner's go), and any role's own checks (the Curator's are in tests/test_curator.py).
"""
from __future__ import annotations

import json
import threading
from decimal import Decimal

import pytest
from sqlalchemy import text

import stub_provider as sp
from hypocurate.pipeline.agents import interface, lm, prices, spend
from hypocurate.pipeline.agents.interface import call_agent
from hypocurate.pipeline.agents.libraries import load
from model_builder import World

_, dspy = load()
MODEL = "claude-sonnet-5-5"
PLANTED = "ZQPLANTED-4711"


class Ask(dspy.Signature):
    """Answer the question in one short sentence."""
    question: str = dspy.InputField()
    note: str = dspy.InputField()
    answer: str = dspy.OutputField()


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def registration(w, label="docs"):
    v = w.new_version("tamu_fcc", label)
    w.add_file(v, "table.csv", f"a,{label}\n".encode())
    w.add_file(v, "documentation/main.tex", b"Quasistatic tensile testing was used throughout.\n", role="documentation")
    w.seal(v)
    return w.val("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                 "VALUES ('registration', :v, 'curator', :a) RETURNING id", v=v, a=w.agent_setting("curator"))


def ask(db, inv, stub, *, question="What is tested?", timeout_seconds=30, ceiling=None, max_output_chars=2000,
        check=None, lm_options=None):
    return call_agent(db, inv, Ask, {"question": question}, model=MODEL, max_tokens=500,
                      max_output_chars=max_output_chars, ceiling=ceiling, lm_options=lm_options,
                      client_options=sp.client_options(stub, timeout_seconds), check=check)


def calls(w, inv):
    return w.rows("SELECT status, input_tokens, output_tokens, cached_tokens, cost, max_cost, error, model, "
                  "price_table_version FROM model_call WHERE invocation_id = :i ORDER BY id", i=inv)


# --- a request that succeeds -------------------------------------------------------------------------

def test_a_request_is_reserved_sent_once_and_recorded_with_its_usage_and_cost(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="Tension."), input_tokens=1300, output_tokens=40, cache_read=100))
    result = ask(db, inv, stub, lm_options={"reasoning_effort": "medium"})
    assert result.failure is None and result.outputs == {"answer": "Tension."} and result.attempts == ["ok"]
    [row] = calls(w, inv)
    # The provider reports 1300 uncached input tokens and 100 read from its cache; the stored input is
    # their total (as DSPy reports it), with the cached part separately, each priced at its own rate.
    assert (row.status, row.input_tokens, row.output_tokens, row.cached_tokens) == ("succeeded", 1400, 40, 100)
    assert row.cost == prices.cost(MODEL, 1400, 40, 100, 0) == Decimal("0.00302")
    assert row.max_cost > row.cost and row.model == MODEL and row.price_table_version == prices.PRICE_TABLE_VERSION
    [request] = stub.requests
    assert request["path"] == "/v1/messages" and request["headers"]["x-api-key"] == sp.DUMMY_KEY
    body = json.loads(request["raw"])
    assert body["model"] == MODEL and body["max_tokens"] == 500
    assert body["output_config"] == {"effort": "medium"}
    assert "tools" not in body and "tool_choice" not in body  # no tool is ever offered


def test_the_whole_request_is_the_instruction_and_the_inputs(w, db, stub):
    """The complete outbound request: the signature's instruction and field descriptions, the
    question and the note 'none'; no history, no other content."""
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="Yes.")))
    ask(db, inv, stub, question="Is it tension?")
    body = stub.bodies()[0]
    assert set(body) <= {"model", "max_tokens", "system", "messages", "thinking", "output_config"}
    assert len(body["messages"]) == 1 and body["messages"][0]["role"] == "user"
    user = json.dumps(body["messages"][0]["content"])
    assert "Is it tension?" in user and "[[ ## note ## ]]\\nnone" in user
    assert "Answer the question in one short sentence." in json.dumps(body["system"])


# --- the failure table --------------------------------------------------------------------------------

def test_an_unavailable_provider_is_tried_once_more_with_the_same_request(w, db, stub):
    inv = registration(w)
    stub.queue(sp.error(500, "api_error"), sp.reply(sp.fields(answer="Fine.")))
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable", "ok"] and result.failure is None
    first, second = calls(w, inv)
    assert (first.status, first.input_tokens, first.cost, first.error) == ("failed", None, None, "provider_unavailable")
    assert second.status == "succeeded"
    assert stub.requests[0]["raw"] == stub.requests[1]["raw"]


@pytest.mark.parametrize("step", [sp.error(429, "rate_limit_error"), sp.error(503, "overloaded_error"),
                                  sp.error(500, "api_error")])
def test_two_unavailable_answers_end_the_call(w, db, stub, step):
    inv = registration(w)
    stub.queue(step, step)
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable"] * 2 and result.failure == "provider_unavailable"
    assert [r.status for r in calls(w, inv)] == ["failed", "failed"]


def test_a_timeout_is_an_unavailable_provider(w, db, stub):
    inv = registration(w)
    stub.queue(sp.timeout(3), sp.timeout(3))
    result = ask(db, inv, stub, timeout_seconds=1)
    assert result.failure == "provider_unavailable" and len(calls(w, inv)) == 2


@pytest.mark.parametrize("status, kind, code", [(401, "authentication_error", "model_auth"),
                                                (403, "permission_error", "model_auth"),
                                                (400, "invalid_request_error", "provider_rejected")])
def test_refused_credentials_or_requests_are_not_retried_and_no_provider_text_is_kept(w, db, stub, status, kind, code):
    inv = registration(w)
    stub.queue(sp.error(status, kind, f"provider says {PLANTED}"))
    result = ask(db, inv, stub)
    assert result.attempts == [code] and result.failure == code and len(stub.requests) == 1
    [row] = calls(w, inv)
    assert (row.status, row.error, row.cost) == ("failed", code, None)
    stored = json.dumps([list(r) for r in w.rows("SELECT * FROM model_call")] +
                        [list(r) for r in w.rows("SELECT * FROM audit_log")], default=str)
    assert PLANTED not in stored and PLANTED not in str(lm.AgentFailure(code))


@pytest.mark.parametrize("first, code", [
    (sp.reply(f"no fields at all {PLANTED}"), "malformed"),
    (sp.reply("   "), "empty"),
    (sp.reply(sp.fields(answer="cut"), stop="max_tokens"), "truncated"),
    (sp.tool_call(), "tool_call"),
    (sp.reply(sp.fields(answer="x" * 3000)), "over_long"),
])
def test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer(w, db, stub, first, code):
    inv = registration(w)
    stub.queue(first, sp.reply(sp.fields(answer="Better.")))
    result = ask(db, inv, stub)
    assert result.attempts == [code, "ok"] and result.outputs == {"answer": "Better."}
    assert [r.status for r in calls(w, inv)] == ["succeeded", "succeeded"]  # both recorded with their usage
    retry = json.dumps(stub.bodies()[1])
    assert interface.correction_note(code).replace('"', '\\"') in retry
    assert PLANTED not in retry and "x" * 100 not in retry and "/etc/x" not in retry
    assert retry.count("[[ ## note ## ]]") == stub.bodies()[0].__str__().count("[[ ## note ## ]]")


def test_a_second_unusable_answer_ends_the_call(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply("garbage"), sp.reply("garbage again"))
    result = ask(db, inv, stub)
    assert result.attempts == ["malformed", "malformed"] and result.failure == "malformed" and result.outputs is None


def test_a_refusal_is_not_retried(w, db, stub):
    inv = registration(w)
    stub.queue(sp.refusal())
    result = ask(db, inv, stub)
    assert result.attempts == ["refused"] and len(stub.requests) == 1
    assert calls(w, inv)[0].status == "succeeded"  # the provider charged for it: recorded with its usage


def test_a_role_check_that_fails_is_corrected_like_a_parse_failure(w, db, stub):
    inv = registration(w)
    stub.queue(sp.reply(sp.fields(answer="not json")), sp.reply(sp.fields(answer='{"ok": true}')))
    def check(outputs):
        try:
            json.loads(outputs["answer"])
        except ValueError:
            return "malformed"
        return None
    result = ask(db, inv, stub, check=check)
    assert result.attempts == ["malformed", "ok"] and result.outputs == {"answer": '{"ok": true}'}


def test_a_reply_without_usage_is_unreadable_failed_and_counted_at_its_maximum(w, db, stub):
    """litellm cannot read a reply with no usage block (it raises a connection error): the call is
    recorded as failed with no usage, counted at its maximum cost, and tried once more like an
    unavailable provider. Nothing is ever counted below its maximum when the cost is not known."""
    inv = registration(w)
    stub.queue(sp.no_usage(sp.fields(answer="Free?")), sp.no_usage(sp.fields(answer="Free?")))
    result = ask(db, inv, stub)
    assert result.attempts == ["provider_unavailable"] * 2 and result.outputs is None
    rows = calls(w, inv)
    assert [(r.status, r.cost) for r in rows] == [("failed", None), ("failed", None)]
    assert w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month") == sum(r.max_cost for r in rows)


def test_a_readable_reply_with_empty_usage_is_cost_unknown(w, db, stub):
    """The engine's own check, for a reply litellm can read but whose usage is empty."""
    class Inner:
        def complete(self, request):
            from types import SimpleNamespace
            return SimpleNamespace(usage=None, finish_reason="stop", text="[[ ## answer ## ]]\nx", tool_calls=())

        def close(self):
            pass

    inv = registration(w)
    engine = lm.RecordedEngine(db, inv, MODEL, max_output_chars=100)
    engine._inner = Inner()
    from dspy.lm15 import Request, Config
    from dspy._vendor.lm15.types import Message
    with pytest.raises(lm.AgentFailure) as failed:
        engine.complete(Request(model=MODEL, messages=(Message.user("q"),), config=Config(max_tokens=10)))
    assert failed.value.code == "cost_unknown" == engine.last_failure
    [row] = calls(w, inv)
    assert (row.status, row.cost, row.error) == ("failed", None, "cost_unknown")


def test_a_reply_whose_recording_fails_is_discarded_and_the_call_stays_open(w, db, stub, monkeypatch):
    inv = registration(w)
    real = spend.finish

    def broken(engine, call, status, **kw):
        if status == "succeeded":
            raise RuntimeError(f"database gone {PLANTED}")
        return real(engine, call, status, **kw)

    monkeypatch.setattr(spend, "finish", broken)
    stub.queue(sp.reply(sp.fields(answer="Kept?")))
    result = ask(db, inv, stub)
    assert result.attempts == ["recording_failed"] and result.outputs is None
    assert calls(w, inv)[0].status == "started"  # counted at its maximum cost; recovery is step 9


def test_an_unpriced_model_is_refused_before_anything_is_reserved(w, db, stub):
    inv = registration(w)
    with pytest.raises(prices.UnknownModel):
        call_agent(db, inv, Ask, {"question": "q"}, model="some-other-model", max_tokens=10, max_output_chars=10,
                   client_options=sp.client_options(stub))
    assert calls(w, inv) == [] and stub.requests == []


# --- reservation and caps ------------------------------------------------------------------------------

def spent(w, inv_or_run, amount, run=False):
    """A finished call of `amount` on a run's invocation or a registration invocation."""
    if run:
        inv = w.invocation(inv_or_run, w.stage(inv_or_run))
    else:
        inv = inv_or_run
    call = spend.reserve(w.e, inv, MODEL, Decimal(amount))
    spend.finish(w.e, call, "succeeded", input_tokens=1, output_tokens=1, cached_tokens=0, cost=Decimal(amount))
    return inv


def refusals(w):
    return [(r.function, r.allowed, r.detail["code"]) for r in
            w.rows("SELECT function, allowed, detail FROM audit_log WHERE function = 'model_call' ORDER BY id")]


def test_the_run_cap_refuses_a_request_before_it_is_sent(w, db, stub):
    rid = w.running(agents=True)
    inv = spent(w, rid, "1.999", run=True)
    stub.queue(sp.reply(sp.fields(answer="x")))
    result = ask(db, inv, stub)
    assert result.attempts == ["spending_cap_run"] and stub.requests == []
    assert refusals(w) == [("model_call", False, "spending_cap_run")]
    assert w.val("SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1


def test_the_curation_cap_and_a_ceiling_refuse_before_sending(w, db, stub):
    inv = spent(w, registration(w), "1.999")
    assert ask(db, inv, stub).attempts == ["spending_cap_curation"]
    fresh = registration(w, "other")
    assert ask(db, fresh, stub, ceiling=Decimal("0.0001")).attempts == ["ceiling_reached"]
    assert stub.requests == [] and [c for _, _, c in refusals(w)] == ["spending_cap_curation", "ceiling_reached"]


def test_the_month_cap_counts_every_call_including_unconfirmed_ones(w, db, stub):
    big = spent(w, registration(w, "a"), "1.99")
    for i in range(24):
        spent(w, registration(w, f"m{i}"), "1.99")      # 25 x 1.99 = 49.75 this month
    open_call = spend.reserve(db, registration(w, "open"), MODEL, Decimal("0.249"))  # started: counts at its max
    assert open_call and big
    result = ask(db, registration(w, "last"), stub)
    assert result.attempts == ["spending_cap_month"] and stub.requests == []


def test_two_reservations_cannot_both_pass_the_month_cap(w, db):
    for i in range(25):
        spent(w, registration(w, f"m{i}"), "1.99")      # 49.75
    a, b = registration(w, "a"), registration(w, "b")
    outcomes, barrier = [], threading.Barrier(2)

    def go(inv):
        barrier.wait()
        try:
            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal("0.2"))))
        except spend.SpendingRefused as refused:
            outcomes.append(("refused", refused.code))

    threads = [threading.Thread(target=go, args=(i,)) for i in (a, b)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(o[0] for o in outcomes) == ["ok", "refused"]
    assert [o[1] for o in outcomes if o[0] == "refused"] == ["spending_cap_month"]


def test_no_database_transaction_is_open_while_a_request_is_in_flight(w, db, stub):
    inv = registration(w)
    seen = []

    def watch():
        with db.connect() as conn:
            seen.append(conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                "AND pid <> pg_backend_pid() AND state LIKE 'idle in transaction%'")).scalar())

    stub.on_request(watch)
    stub.queue(sp.error(500, "api_error"), sp.reply(sp.fields(answer="ok")))
    ask(db, inv, stub)
    assert seen == [0, 0]


def test_the_price_table_names_the_owners_models():
    from hypocurate.pipeline.agents.settings import MODELS
    assert set(MODELS.values()) <= set(prices.PRICES)
    assert prices.PRICES["claude-opus-5-5"].input == 4 and prices.PRICES["claude-opus-5-5"].output == 20
    assert prices.PRICES["claude-sonnet-5-5"].input == 2 and prices.PRICES["claude-sonnet-5-5"].output == 10
    assert prices.PRICES["claude-haiku-4-5"].input == 1 and prices.PRICES["claude-haiku-4-5"].output == 5
    # The bound covers the request's bytes and its output limit at full price.
    assert prices.max_cost(MODEL, 1000, 100) == (Decimal(2000) * 2 + Decimal(100) * 10) / 1_000_000


def test_a_reservation_waits_for_the_month_wide_lock(w, db):
    """Deterministic: while another transaction holds the month-wide lock, a reservation waits, so two
    reservations never read the month's total at the same time. (The race test above may pass by
    timing alone; this one cannot.)"""
    inv = registration(w)
    done = threading.Event()
    with db.connect() as holder:
        holder.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=spend.MONTH_LOCK_KEY))
        thread = threading.Thread(target=lambda: (spend.reserve(db, inv, MODEL, Decimal("0.01")), done.set()))
        thread.start()
        assert not done.wait(1.5)  # still waiting for the lock
        holder.rollback()          # releases it
    assert done.wait(10)
    thread.join()
    assert len(calls(w, inv)) == 1
```
### `tests/test_agent_libraries.py`

```python
"""Step 8a: the model-call libraries (DSPy, litellm) and the file guard (owner, 2026-10-06).

litellm reads a `.env` file when it is imported unless `LITELLM_MODE` is `PRODUCTION`; the
tripwire caught it reading the repository's `.env` (which holds the secrets) in a guarded run.
`hypocurate.pipeline.agents.libraries` is the one place that imports them, and it sets that mode
first. Importing them under the guard also made Python probe a `sys.path` entry that does not
exist (the standard library's zip); the guarded process now drops such entries before the guard
is installed (owner's decision), so a clean agent import logs no refusal while the tripwire still
watches everything the libraries do (a planted `.env` read is still refused).

What these tests do not show: that the libraries make no other file access on code paths not
exercised here (a real model request is tested in the agent-core tests, through a local stub
provider).
"""
from __future__ import annotations

import ast
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from hypocurate.access import guarded
from hypocurate.access.guarded import run_guarded

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "hypocurate"
PROBE = "hypocurate.access.guard_probe:probe"


def _guard_lines(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if "file_guard" in r.getMessage()]


def test_the_agent_libraries_import_under_the_guard_with_no_refusal(caplog):
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    result = run_guarded(PROBE, [{"op": "agent_libraries"}], env=dict(os.environ), timeout=300)
    assert result == ["ok"]
    assert _guard_lines(caplog) == []


def test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard(tmp_path, caplog):
    caplog.set_level(logging.WARNING, logger="hypocurate.access")
    planted = tmp_path / ".env"
    planted.write_text("PLANTED_SECRET=do-not-read\n")
    result = run_guarded(PROBE, [{"op": "agent_libraries"}, {"op": "dotenv", "path": str(planted)}],
                         env=dict(os.environ), timeout=300)
    assert result[0] == "ok"
    assert result[1].startswith("refused: file guard: reading"), result
    assert any(str(planted) in line for line in _guard_lines(caplog))


def test_missing_path_entries_are_dropped_and_the_others_kept(tmp_path):
    present = tmp_path / "present"
    present.mkdir()
    entries = [str(present), str(tmp_path / "missing"), str(tmp_path / "missing.zip"), str(present)]
    assert guarded.existing_path_entries(entries) == [str(present), str(present)]


def test_the_libraries_never_read_a_dotenv_file_outside_the_guard(tmp_path):
    """A fresh interpreter in a directory holding a `.env`, with LITELLM_MODE set to DEV in its
    environment: loading the libraries through our module opens no `.env` file and leaves the
    planted variable unset."""
    (tmp_path / ".env").write_text("PLANTED_SECRET=do-not-read\n")
    script = (
        "import sys, json, os\n"
        "opened = []\n"
        "sys.addaudithook(lambda e, a: opened.append(str(a[0])) if e == 'open' and a and "
        "str(a[0]).endswith('.env') else None)\n"
        "from hypocurate.pipeline.agents import libraries\n"
        "libraries.load()\n"
        "print(json.dumps({'opened': opened, 'planted': os.environ.get('PLANTED_SECRET'),"
        " 'mode': os.environ.get('LITELLM_MODE')}))\n")
    env = {k: v for k, v in os.environ.items() if k != "PLANTED_SECRET"}
    env["LITELLM_MODE"] = "DEV"
    done = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env, capture_output=True,
                          text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-2000:]
    out = json.loads(done.stdout.strip().splitlines()[-1])
    assert out == {"opened": [], "planted": None, "mode": "PRODUCTION"}


def test_only_the_libraries_module_imports_dspy_or_litellm():
    """A tripwire for our own code: every other module goes through `libraries.load()`, which
    sets the environment first."""
    allowed = PACKAGE / "pipeline" / "agents" / "libraries.py"
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        if path == allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(n.split(".")[0] in ("dspy", "litellm") for n in names):
                offenders.append(str(path.relative_to(REPO)))
    assert offenders == []
```
### `tests/test_curator.py`

```python
"""Step 8a: the Curator and the curation workflow at registration (owner, 2026-10-06, Q2 and Q3).

Through the real path: the frozen sources registered with their documentation; `curate` binds one
registration invocation, reads the Curator's complete input through the access layer, sends the
request through DSPy and litellm to the local stub provider, and stores every proposal as code
decided it; a person accepts or rejects; `seal_curation` seals the accepted values into a new
version; the adapters apply them where the table gives no value.

What these tests do not cover: what a real model proposes (the one live curation call, run only
with the owner's go), and whether a sentence supports a value (that is the person's decision).
"""
from __future__ import annotations

import json
from decimal import Decimal

import pytest

import stub_provider as sp
from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.pipeline.agents import quotes
from hypocurate.pipeline.agents.settings import CURATOR_INSTRUCTION
from hypocurate.sources import adapters, curation
from hypocurate.sources.curation import CurationRefused
from hypocurate.sources.versions import (CURATION_PATH, files_digest, latest_sealed_version_id, load_sealed_version,
                                         register, version_identity)
from model_builder import World

TENSION_QUOTE = ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
                 "tests provided the HV.")
FCC_QUOTE = "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."
PLANTED = "ZQPLANT-31337"


def answer(**entries) -> str:
    body = {f: "not stated" for f in CURATION_TARGETS}
    body.update(entries)
    return sp.fields(proposals=json.dumps(body))


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def register_base(db):
    """The Texas A&M version a curation starts from: its data and documentation without the frozen
    curation (step 8a: registering the definition now gives the curated version)."""
    import dataclasses
    from hypocurate.db.retry import run_transaction
    from hypocurate.sources.versions import SOURCES, _register_in, read_definition_files
    d = dataclasses.replace(SOURCES["tamu_fcc"], curation_file=None)
    files, obtained = read_definition_files(d)
    return run_transaction(db, lambda conn: _register_in(conn, d, files, obtained))


def run_curate(db, key, stub, **kw):
    return curation.curate(db, key, client_options=sp.client_options(stub), **kw)


def version_of(db, key):
    with db.connect() as conn:
        return load_sealed_version(conn, latest_sealed_version_id(conn, key))


# --- refusals before any model call ------------------------------------------------------------------

def test_a_compilation_source_is_never_curated(db, stub):
    """Owner, Q3: a source grouped by paper is refused before any model call."""
    register(db, "mpea")
    with pytest.raises(CurationRefused) as refused:
        run_curate(db, "mpea", stub)
    assert refused.value.code == "compilation_source"
    with db.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM agent_invocation").scalar() == 0
    assert stub.requests == []


def test_a_version_without_documentation_is_not_curated(db, stub):
    w = World(db)  # the world's tamu_fcc version holds one data file and no documentation
    assert w
    with pytest.raises(CurationRefused) as refused:
        run_curate(db, "tamu_fcc", stub)
    assert refused.value.code == "no_documentation" and stub.requests == []


# --- the request and the proposals ------------------------------------------------------------------------

def test_the_curators_complete_request_is_the_instruction_the_documentation_and_the_targets(db, stub):
    register_base(db)
    version = version_of(db, "tamu_fcc")
    stub.queue(sp.reply(answer()))
    run_curate(db, "tamu_fcc", stub)
    [body] = stub.bodies()
    assert body["model"] == "claude-sonnet-5-5" and body["max_tokens"] == 8000
    assert body["output_config"] == {"effort": "medium"} and "tools" not in body
    system, user = json.dumps(body["system"]), body["messages"][0]["content"][0]["text"]
    assert len(body["messages"]) == 1
    assert json.dumps(CURATOR_INSTRUCTION)[1:-1] in system
    for path, content in version.documentation.items():
        assert f"=== {path} ===\n{content.decode()}" in user
    assert json.dumps({f: dict(s) for f, s in CURATION_TARGETS.items()}, sort_keys=True, ensure_ascii=False) in user
    assert "[[ ## note ## ]]\nnone" in user
    # No data row reaches the Curator: the spreadsheet's yield strengths and alloy names are absent.
    records = adapters.read(version).records
    documentation = "".join(c.decode() for c in version.documentation.values())
    checked = 0
    for r in records:
        for column in ("YS (MPa)", "Alloy Name", "Grain Size(µm)"):
            cell = r.reported.get(column)
            if cell is not None and len(cell.text) >= 4 and cell.text not in documentation:  # the paper names some
                assert cell.text not in user, (column, cell.text)
                checked += 1
    assert checked > 100


def test_no_planted_value_and_no_claim_reaches_the_curator(db, stub):
    """A constructed source version grouped by dataset: a planted outcome value in its data file, a
    run whose claim states a direction. Neither is in the request's bytes."""
    w = World(db)
    w.running()  # claim: "Yield strength rises as grain size falls"
    v = w.new_version("tamu_fcc", "planted")
    w.add_file(v, "table.csv", f"alloy,grain_size,yield_strength\nZQX1,4.0,{PLANTED}\n".encode())
    w.add_file(v, "documentation/notes.md", b"Every specimen was tested in tension at room temperature.\n",
               role="documentation")
    w.seal(v)
    stub.queue(sp.reply(answer()))
    run_curate(db, "tamu_fcc", stub)
    raw = stub.requests[0]["raw"].decode()
    assert "Every specimen was tested in tension" in raw
    for absent in (PLANTED, "ZQX1", "table.csv", "rises as grain size falls", "yield_strength\\n"):
        assert absent not in raw, absent


def test_each_proposal_is_stored_as_code_decided_it(db, stub):
    register_base(db)
    stub.queue(sp.reply(answer(
        test_type={"value": "tension", "quote": TENSION_QUOTE},
        phase_class={"value": "FCC", "quote": FCC_QUOTE},
        microstructure={"value": "FCC", "quote": "This sentence is not anywhere in the documentation, FCC."},
        test_temperature={"value": "warm", "quote": FCC_QUOTE},
        test_temperature_band={"value": "room temperature", "quote": FCC_QUOTE},
        made_up_field={"value": 1, "quote": "x"})))
    out = run_curate(db, "tamu_fcc", stub)
    assert out["status"] == "done" and out["ignored_keys"] == ["made_up_field"]
    got = {p["field"]: (p["status"], p["refusal_code"], p["document"], p["line"], p["term"]) for p in out["proposals"]}
    assert got == {
        "test_type": ("proposed", None, "documentation/main.tex", 177, "tensile"),
        "phase_class": ("proposed", None, "documentation/main.tex", 173, "FCC"),
        "microstructure": ("refused", "quote_not_found", None, None, None),
        "test_temperature": ("refused", "value_not_allowed", None, None, None),
        "test_temperature_band": ("refused", "term_missing", None, None, None),  # the quote names no temperature
    }
    assert {p["field"] for p in curation.proposals(db, "tamu_fcc")} == set(CURATION_TARGETS)


@pytest.mark.parametrize("entry, code", [
    ({"value": "tension", "quote": "tensile"}, "quote_too_short"),
    ({"value": "tension", "quote": "x" * 1600}, "quote_too_long"),
    ({"value": "shear", "quote": TENSION_QUOTE}, "value_not_allowed"),
    ({"value": "tension"}, "malformed_entry"),
    ("tension", "malformed_entry"),
    ({"value": "compression", "quote": TENSION_QUOTE}, "term_missing"),
])
def test_an_entry_that_fails_a_check_is_refused_with_its_code(db, stub, entry, code):
    register_base(db)
    stub.queue(sp.reply(answer(test_type=entry)))
    out = run_curate(db, "tamu_fcc", stub)
    [p] = [p for p in out["proposals"] if p["field"] == "test_type"]
    assert (p["status"], p["refusal_code"]) == ("refused", code)


def test_a_malformed_answer_is_corrected_once_and_then_nothing_is_stored(db, stub):
    register_base(db)
    stub.queue(sp.reply(sp.fields(proposals=f"I think tension {PLANTED}")),
               sp.reply(sp.fields(proposals="still not JSON")))
    out = run_curate(db, "tamu_fcc", stub)
    assert (out["status"], out["code"], out["attempts"]) == ("failed", "malformed", ["malformed", "malformed"])
    assert out["proposals"] == [] and curation.proposals(db, "tamu_fcc") == []
    retry = stub.requests[1]["raw"].decode()
    assert "(malformed:" in retry and PLANTED not in retry


def test_the_ceiling_refuses_the_call_before_it_is_sent(db, stub):
    register_base(db)
    out = run_curate(db, "tamu_fcc", stub, ceiling=Decimal("0.01"))
    assert (out["status"], out["code"]) == ("failed", "ceiling_reached") and stub.requests == []


# --- decisions, sealing and applying -------------------------------------------------------------------------

def proposed(db, stub, **entries):
    stub.queue(sp.reply(answer(**entries)))
    out = run_curate(db, "tamu_fcc", stub)
    return {p["field"]: p["id"] for p in out["proposals"]}


def test_a_person_decides_once_and_only_on_a_proposal_that_passed(db, stub):
    register_base(db)
    ids = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE},
                   phase_class={"value": "FCC", "quote": "not in the documentation at all, FCC here"})
    assert curation.decide(db, ids["test_type"], "accepted", "Khalid El-Awady")["decision"] == "accepted"
    for proposal, code in ((ids["test_type"], "already_decided"), (ids["phase_class"], "not_decidable"),
                           (10 ** 9, "unknown_proposal")):
        with pytest.raises(CurationRefused) as refused:
            curation.decide(db, proposal, "rejected", "Khalid El-Awady")
        assert refused.value.code == code


def tamu_with_notes(db, note: bytes):
    """A Texas A&M version holding the real spreadsheet and a test note as its documentation."""
    register_base(db)
    base = version_of(db, "tamu_fcc")
    w = World.__new__(World)
    w.e = db
    v = w.val("INSERT INTO source_version (source_id, label, obtained_on) SELECT source_id, 'notes', obtained_on "
              "FROM source_version WHERE id = :b RETURNING id", b=base.id)
    for path, content in base.data_files.items():
        w.add_file(v, path, content)
    w.add_file(v, "documentation/notes.md", note, role="documentation")
    w.seal(v, w.fingerprint(v) if hasattr(w, "fingerprint") else None)
    return v


def test_sealing_applies_accepted_values_only_where_the_table_gives_none(db, stub):
    note = ("All tensile tests in this dataset were carried out at 25 \u00b0C in laboratory air on single-phase "
            "FCC specimens.\n").encode()
    base = tamu_with_notes(db, note)
    quote = note.decode().strip()
    ids = proposed(db, stub, test_temperature={"value": 25, "quote": quote},
                   test_type={"value": "tension", "quote": quote},
                   phase_class={"value": "FCC", "quote": quote},
                   microstructure={"value": "FCC", "quote": quote},
                   test_temperature_band={"value": "room temperature", "quote": quote})
    assert {k for k, v in ids.items()} == set(CURATION_TARGETS)
    curation.decide(db, ids["test_temperature"], "accepted", "Khalid El-Awady", "states 25 °C")
    curation.decide(db, ids["test_type"], "accepted", "Khalid El-Awady")
    curation.decide(db, ids["phase_class"], "rejected", "Khalid El-Awady", "the phase check is not a result")
    curation.decide(db, ids["microstructure"], "accepted", "Khalid El-Awady")  # the decision's field: never replaced
    # Rejected (phase class), refused (the band: no listed term in the quote) and not stated: never sealed.
    sealed = curation.seal_curation(db, "tamu_fcc")
    assert sealed.created and sealed.label.endswith("+ curation")
    curated = version_of(db, "tamu_fcc")
    assert curated.id == sealed.version_id and set(curated.files) == {*load_sealed_version_files(db, base), CURATION_PATH}
    doc = json.loads(curated.files[CURATION_PATH])
    assert set(doc["values"]) == {"test_temperature", "test_type", "microstructure"} and doc["source"] == "tamu_fcc"
    assert doc["values"]["test_temperature"]["value"] == 25 and doc["values"]["test_temperature"]["line"] == 1
    records = adapters.read(curated).records
    t = records[0].harmonized["test_temperature"]
    assert (t.value, t.status) == (25, "assigned_from_source") and "accepted by Khalid El-Awady" in t.citation.location
    assert t.citation.quote == quote
    # Where the table gives none, the accepted value applies (test type: adapter version 3 assigns none).
    assert records[0].harmonized["test_type"].citation.document == "tamu_fcc: documentation/notes.md (sealed with the source)"
    # Never over a value the record already has: the band and the microstructure are assigned by decision,
    # so the accepted microstructure leaves them as they are.
    assert records[0].harmonized["test_temperature_band"].status == "assigned_by_decision"
    assert all(r.harmonized["microstructure"].status == "assigned_by_decision" for r in records)
    assert all(r.harmonized["test_temperature"].value == 25 for r in records)


def load_sealed_version_files(db, version_id):
    with db.connect() as conn:
        return set(load_sealed_version(conn, version_id).files)


def test_a_curated_version_is_reproducible_from_its_files_and_cannot_be_curated_again(db, stub):
    register_base(db)
    ids = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    curation.decide(db, ids["test_type"], "accepted", "K")
    sealed = curation.seal_curation(db, "tamu_fcc")
    curated = version_of(db, "tamu_fcc")
    assert curation.curation_file(db, "tamu_fcc") == curated.files[CURATION_PATH]
    assert version_identity(files_digest(curated.files), "uploaded_table", "measured", "dataset") == sealed.fingerprint
    for call in (lambda: run_curate(db, "tamu_fcc", stub), lambda: curation.seal_curation(db, "tamu_fcc")):
        with pytest.raises(CurationRefused) as refused:
            call()
        assert refused.value.code == "already_curated"


def test_two_accepted_proposals_for_one_field_are_not_sealed(db, stub):
    register_base(db)
    first = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    second = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    curation.decide(db, first["test_type"], "accepted", "K")
    curation.decide(db, second["test_type"], "accepted", "K")
    with pytest.raises(CurationRefused) as refused:
        curation.seal_curation(db, "tamu_fcc")
    assert refused.value.code == "conflicting_acceptances"


def test_a_curation_file_that_cannot_be_read_refuses_the_version(db):
    from hypocurate.sources.record import AdapterError
    register_base(db)
    base = version_of(db, "tamu_fcc")
    bad = {**dict(base.files), CURATION_PATH: b'{"format": 1, "source": "mpea", "values": {}}\n'}
    from hypocurate.sources.versions import SealedVersion
    digest = files_digest(bad)
    v = SealedVersion(base.id, base.source_key, base.label, base.source_type, base.data_kind, base.grouping_unit,
                      base.sealed_at, digest, version_identity(digest, base.source_type, base.data_kind,
                                                               base.grouping_unit), bad)
    with pytest.raises(AdapterError, match="curation.json"):
        adapters.read(v)


# --- the command line ------------------------------------------------------------------------------------------

def test_the_command_line_never_prints_the_guarded_childs_error_text(monkeypatch, capsys, migrated_database):
    from hypocurate import cli
    from hypocurate.access import guarded
    monkeypatch.setenv("DATABASE_URL", migrated_database)

    def failing(*a, **kw):
        raise guarded.GuardedRunError(f"RuntimeError: provider said {PLANTED}")

    monkeypatch.setattr(guarded, "run_guarded", failing)
    assert cli.main(["sources", "curate", "tamu_fcc"]) == 1
    captured = capsys.readouterr()
    assert PLANTED not in captured.out + captured.err and "did not finish" in captured.err


def test_the_quote_checks_collapse_whitespace_only():
    docs = {"documentation/a.tex": "line one\nThe  dataset\n  contains 94 FCC alloy conditions.\n"}
    assert quotes.locate("The dataset contains 94 FCC alloy conditions.", docs) == quotes.Located("documentation/a.tex", 2)
    assert quotes.locate("the dataset contains 94 FCC alloy conditions.", docs) is None  # no case folding
    assert quotes.term_for("microstructure", "FCC+BCC", "FCC and BCC phases") == "FCC"
    assert quotes.term_for("microstructure", "FCC+BCC", "FCC only") is None
    assert quotes.term_for("test_temperature", 25, "tested at 25 °C") == "25"
    assert quotes.term_for("test_temperature", 25, "tested at 250 °C") is None
```
### `tests/test_migrations_step8a.py`

```python
"""Step 8a: migration 0005 (approved by the owner on 2026-10-06, subject to the second-model review).

Additive; 0001 to 0004 untouched; the two replaced model-call functions keep every check of 0001;
up, down, up gives the same schema; the downgrade refuses while anything 0005 added is in use and
restores 0001's functions and path rule exactly; a failed upgrade changes nothing. Then the rules
0005 adds, each with an allowed and a refused case: source files by role, one invocation record per
agent call (run or registration), model calls owned by an invocation, the Curator's proposals and a
person's decisions."""
from __future__ import annotations

import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import World, sha
from test_migrations import assert_schema_is_empty, snapshot
from test_migrations_step6 import body

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0005 = SCRIPTS.get_revision("0005").module

DOC = ("Quasistatic tensile testing was used to determine 0.2% offset YS, while Vickers indentation\n"
       "tests provided the HV. The dataset contains 94 FCC alloy conditions in the system.\n").encode()
QUOTE = "Quasistatic tensile testing was used to determine 0.2% offset YS"


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


def function_source(engine, name) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = :n"), dict(n=name)).scalar_one()


def checks_of(function_sql: str) -> list[str]:
    return re.findall(r"IF .*? END IF;", body(function_sql))


# --- the migration -------------------------------------------------------------------------------

def test_0005_is_the_head_and_follows_0004():
    assert migrate.head_revision() == "0005" and M0005.down_revision == "0004"


@pytest.mark.parametrize("name, kept", [("hc_model_call_insert", "MODEL_CALL_INSERT_0001"),
                                        ("hc_model_call_update", "MODEL_CALL_UPDATE_0001")])
def test_the_downgrade_keeps_0001s_model_call_functions_verbatim(name, kept):
    original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
    assert body(getattr(M0005, kept)) == body(original)


@pytest.mark.parametrize("old, new", [("MODEL_CALL_INSERT_0001", "MODEL_CALL_INSERT_0005"),
                                      ("MODEL_CALL_UPDATE_0001", "MODEL_CALL_UPDATE_0005")])
def test_the_new_model_call_functions_keep_every_check_of_0001(old, new):
    new_body = body(getattr(M0005, new))
    for check in checks_of(getattr(M0005, old)):
        assert check in new_body, check


def test_up_down_up_restores_0001s_functions_and_path_rule(engine):
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0004")
    for name in ("hc_model_call_insert", "hc_model_call_update"):
        original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
        assert " ".join(function_source(engine, name).split()) == body(original)
    with engine.connect() as conn:
        rule = conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                                 "WHERE conname = 'ck_source_file_safe_data_file_path'")).scalar_one()
        nullable = conn.execute(text("SELECT is_nullable FROM information_schema.columns "
                                     "WHERE table_name = 'model_call' AND column_name = 'run_id'")).scalar_one()
        tables = set(conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).scalars())
    assert "csv|xlsx" in rule and "role" not in rule and nullable == "NO"
    assert not {"agent_invocation", "curator_proposal", "curator_decision"} & tables
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0004")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE curator_decision (id int)"))  # 0005 creates it last
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0004"


def test_the_downgrade_refuses_while_0005_is_in_use(db):
    w = World(db)
    v = w.new_version("mpea", "v2")
    w.add_file(v, "documentation/paper.tex", DOC, role="documentation")
    before = snapshot(db)
    with pytest.raises(Exception, match="0005 is in use"):
        migrate.downgrade(db, "0004")
    assert snapshot(db) == before and migrate.current_revision(db) == "0005"


# --- source files by role ------------------------------------------------------------------------

def test_a_file_without_a_role_is_a_data_file_as_before(w):
    """The previous release's code inserts files without a role."""
    v = w.new_version("mpea", "v2")
    w.add_file(v, "table.csv", b"a,b\n")
    assert w.val("SELECT role FROM source_file WHERE source_version_id = :v", v=v) == "data"


@pytest.mark.parametrize("path, role, ok", [
    ("documentation/main.tex", "documentation", True),
    ("documentation/paper.xml", "documentation", True),
    ("documentation/notes.md", "documentation", True),
    ("curation.json", "curation", True),
    ("table.xlsx", "data", True),
    ("documentation/main.tex", "data", False),        # a data file is a table
    ("documentation/table.csv", "data", False),       # the documentation folder holds documentation only
    ("main.tex", "documentation", False),             # documentation lives in its folder
    ("documentation/sub/main.tex", "documentation", False),
    ("documentation/main.pdf", "documentation", False),
    ("documentation/.hidden.tex", "documentation", False),
    ("other.json", "curation", False),
    ("curation.json", "data", False),
    ("table.csv", "curation", False),
    ("table.csv", "unknown", False),
])
def test_each_role_has_its_own_path_rule(w, path, role, ok):
    v = w.new_version("mpea", "v2")
    sql = ("INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES (:v, :p, :h, :c, :o)")
    params = dict(v=v, p=path, h=sha(b"x"), c=b"x", o=role)
    if ok:
        w.run_sql(sql, **params)
    else:
        w.rejected(sql, "ck_source_file_safe_data_file_path", **params)


def test_a_version_with_documentation_seals_over_all_its_files(w):
    v = w.new_version("mpea", "v2")
    w.add_file(v, "table.csv", b"a,b\n")
    w.add_file(v, "documentation/main.tex", DOC, role="documentation")
    w.seal(v)
    assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=v) == 2
    assert w.val("SELECT fingerprint FROM source_version WHERE id = :v", v=v) == w.fingerprint(v)


# --- invocations ---------------------------------------------------------------------------------

def run_invocation(w, rid, stage, role="planner", setting=None):
    setting = setting or w.val("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = :o",
                               r=rid, o=role)
    return ("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
            "VALUES ('run', :r, :s, :o, :a) RETURNING id", dict(r=rid, s=stage, o=role, a=setting))


def test_a_run_invocation_uses_the_setting_recorded_for_that_run(w):
    """Two valid runs whose recorded settings differ: an invocation of run A with run B's setting is
    refused, so a wrong but valid combination cannot be assembled."""
    a = w.running(agents=True)
    b_setting = w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 7, 'i', 'm') "
                      "RETURNING id")
    b = w.run()
    w.run_sql("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", r=b, s=b_setting)
    w.start(b)
    sa = w.stage(a)
    sql, params = run_invocation(w, a, sa)
    assert w.val(sql, **params)
    sql, params = run_invocation(w, a, sa, setting=b_setting)
    w.rejected(sql, "fk_agent_invocation_run_agent_setting", **params)


def test_a_run_invocation_names_a_running_stage_of_its_run_with_its_role(w):
    a, b = w.running(agents=True), w.running(agents=True)
    sa, sb = w.stage(a), w.stage(b)
    critic = w.stage(a, "critic", "critic")
    for sql, params in (run_invocation(w, a, sb),):                       # another run's stage
        w.rejected(sql, "running stage of its run with the same role", **params)
    sql, params = run_invocation(w, a, critic)                            # the stage is the critic's
    w.rejected(sql, "running stage of its run with the same role", **params)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=sa)
    sql, params = run_invocation(w, a, sa)                                # the stage is finished
    w.rejected(sql, "running stage of its run with the same role", **params)


def test_a_run_invocation_only_while_the_run_is_running(w):
    queued = w.run(agents=True)
    st = w.stage(w.running(agents=True))
    sql, params = run_invocation(w, queued, st)
    w.rejected(sql, "only while the run is running", **params)


def test_after_completion_only_the_commentator_is_invoked(w):
    rid, sets, _ = w.frozen(agents=True)
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    commentator = w.stage(rid, "commentator", "commentator")
    sql, params = run_invocation(w, rid, commentator, role="commentator")
    assert w.val(sql, **params)
    sql, params = run_invocation(w, rid, commentator, role="analyst")
    w.rejected(sql, "after completion only the commentator", **params)


def curator_setting(w):
    return w.agent_setting("curator")


def sealed_version_with_documentation(w, key="tamu_fcc", label="docs"):
    v = w.new_version(key, label)
    w.add_file(v, "table.csv", f"a,b,{label}\n".encode())  # each label its own files, so its own fingerprint
    w.add_file(v, "documentation/main.tex", DOC, role="documentation")
    w.seal(v)
    return v


REGISTRATION = ("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                "VALUES ('registration', :v, :o, :a) RETURNING id")


def test_a_registration_invocation_is_the_curators_on_a_sealed_version(w):
    v = sealed_version_with_documentation(w)
    assert w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    unsealed = w.new_version("tamu_fcc", "open")
    w.rejected(REGISTRATION, "reads a sealed source version", v=unsealed, o="curator", a=curator_setting(w))
    w.rejected(REGISTRATION, "ck_agent_invocation_shape", v=v, o="planner", a=w.agent_setting("planner"))
    w.rejected(REGISTRATION, "fk_agent_invocation_agent_setting", v=v, o="curator", a=w.agent_setting("planner"))
    rid = w.running(agents=True)
    w.rejected("INSERT INTO agent_invocation (scope, run_id, source_version_id, role, agent_setting_id) "
               "VALUES ('registration', :r, :v, 'curator', :a)", "ck_agent_invocation_shape",
               r=rid, v=v, a=curator_setting(w))


def test_invocations_are_append_only(w):
    v = sealed_version_with_documentation(w)
    w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    w.rejected("UPDATE agent_invocation SET source_version_id = source_version_id", "append-only")
    w.rejected("DELETE FROM agent_invocation", "append-only")


# --- model calls owned by an invocation -------------------------------------------------------------

CALL = ("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
        "VALUES (:r, :s, :i, :o, 'm', 'p', 0.5) RETURNING id")


def test_every_call_names_its_invocation(w):
    rid = w.running(agents=True)
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 0.5)", "ck_model_call_with_invocation", r=rid, s=st)
    assert w.call(rid, st)


def test_a_registration_call_belongs_to_no_run_and_is_finished_once(w):
    v = sealed_version_with_documentation(w)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    call = w.val(CALL, r=None, s=None, i=inv, o="curator")
    w.finish_call(call, "succeeded", (2000, 300, 0, 0.007))
    with pytest.raises(IntegrityError, match="finished exactly once"):
        w.finish_call(call, "failed", None)
    rid = w.running(agents=True)
    st = w.stage(rid, "curator", "curator")
    w.rejected(CALL, "belongs to no run", r=rid, s=st, i=inv, o="curator")            # a run on a registration call
    w.rejected(CALL, "belongs to no run", r=None, s=None, i=inv, o="planner")         # another role
    w.rejected(CALL, "ck_model_call_run_with_stage", r=rid, s=None, i=None, o="curator")
    month = w.val("SELECT sum(reported_cost) FROM model_call_totals_by_month")
    assert float(month) == 0.007  # the month counts registration calls; no run's total does
    assert float(w.val("SELECT sum(cap_cost) FROM model_call_totals_by_run")) == 0


def test_a_registration_call_cannot_be_moved_to_a_run(w):
    v = sealed_version_with_documentation(w)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    call = w.val(CALL, r=None, s=None, i=inv, o="curator")
    rid = w.running(agents=True)
    st = w.stage(rid, "curator", "curator")
    w.rejected("UPDATE model_call SET run_id = :r, stage_result_id = :s, status = 'interrupted', finished_at = now() "
               "WHERE id = :c", "cannot change", r=rid, s=st, c=call)
    other = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    w.rejected("UPDATE model_call SET invocation_id = :i, status = 'interrupted', finished_at = now() WHERE id = :c",
               "cannot change", i=other, c=call)


def test_a_run_call_has_its_invocations_run_stage_and_role(w):
    rid = w.running(agents=True)
    planner, critic = w.stage(rid), w.stage(rid, "critic", "critic")
    inv = w.invocation(rid, planner)
    w.rejected(CALL, "its invocation's run, stage and role", r=rid, s=critic, i=inv, o="critic")
    w.rejected(CALL, "its invocation's run, stage and role", r=rid, s=planner, i=inv, o="critic")
    assert w.val(CALL, r=rid, s=planner, i=inv, o="planner")


# --- the Curator's proposals and a person's decisions ----------------------------------------------

PROPOSAL = ("INSERT INTO curator_proposal (invocation_id, source_version_id, field, status, value, quote, "
            "document_path, line, term, refusal_code) VALUES (:i, :v, :f, :st, CAST(:val AS jsonb), :q, :d, :l, :t, :rc) "
            "RETURNING id")


def proposal(**kw):
    p = dict(f="test_type", st="proposed", val='"tension"', q=QUOTE, d="documentation/main.tex", l=1, t="tensile",
             rc=None)
    p.update(kw)
    return p


@pytest.fixture
def curation(w):
    v = sealed_version_with_documentation(w)
    return v, w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))


def test_a_proposal_that_passed_is_found_in_its_document_by_the_database(w, curation):
    v, inv = curation
    spaced = QUOTE.replace(" was ", "  was\n ")  # whitespace differs: runs are collapsed on both sides
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(q=spaced))


@pytest.mark.parametrize("change, match", [
    (dict(q="Quasistatic tensile testing was used to measure everything in the world"), "must occur"),
    (dict(d="table.csv"), "must occur"),                                   # not a documentation file
    (dict(d="documentation/other.tex"), "must occur"),
    (dict(t="compression"), "ck_curator_proposal_proposed_complete"),     # the term is not in the quote
    (dict(q="tensile testing", t="tensile"), "ck_curator_proposal_proposed_complete"),  # too short
    (dict(l=0), "ck_curator_proposal_proposed_complete"),
    (dict(val=None), "ck_curator_proposal_proposed_complete"),
    (dict(f="yield_strength"), "ck_curator_proposal_field"),
    (dict(rc="quote_not_found"), "ck_curator_proposal_refusal_code"),
])
def test_a_proposal_that_did_not_pass_cannot_be_stored_as_passed(w, curation, change, match):
    v, inv = curation
    w.rejected(PROPOSAL, match, i=inv, v=v, **proposal(**change))


def test_refused_and_not_stated_proposals_are_kept_with_their_shape(w, curation):
    v, inv = curation
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", val='"FCC"', q="made up",
                                                  t=None, rc="quote_not_found"))
    w.rejected(PROPOSAL, "ck_curator_proposal_refusal_code", i=inv, v=v,
               **proposal(f="microstructure", st="refused", rc=None))
    w.rejected(PROPOSAL, "ck_curator_proposal_not_stated_empty", i=inv, v=v,
               **proposal(f="test_temperature", st="not_stated"))
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="test_temperature", st="not_stated", val=None, q=None, d=None,
                                                  l=None, t=None))
    w.rejected(PROPOSAL, "ck_curator_proposal_bounded", i=inv, v=v,
               **proposal(f="test_temperature_band", st="refused", q="x" * 4001, t=None, rc="too_long"))


def test_one_proposal_per_field_per_invocation_for_its_own_version(w, curation):
    v, inv = curation
    w.val(PROPOSAL, i=inv, v=v, **proposal())
    w.rejected(PROPOSAL, "uq_curator_proposal_invocation_id_field", i=inv, v=v, **proposal())
    other = sealed_version_with_documentation(w, label="other")
    w.rejected(PROPOSAL, "its invocation's source version", i=inv, v=other, **proposal(f="phase_class"))
    rid = w.running(agents=True)
    run_inv = w.invocation(rid, w.stage(rid, "curator", "curator"), role="curator")
    w.rejected(PROPOSAL, "registration invocation of the curator", i=run_inv, v=v, **proposal(f="phase_class"))


DECISION = ("INSERT INTO curator_decision (proposal_id, decision, decided_by, note) VALUES (:p, :d, :b, :n) "
            "RETURNING id")


def test_a_person_decides_once_on_a_proposal_that_passed(w, curation):
    v, inv = curation
    passed = w.val(PROPOSAL, i=inv, v=v, **proposal())
    refused = w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", t=None, rc="term_missing"))
    w.rejected(DECISION, "only a proposal that passed", p=refused, d="accepted", b="Khalid El-Awady", n=None)
    w.rejected(DECISION, "ck_curator_decision_named_and_bounded", p=passed, d="accepted", b="  ", n=None)
    w.rejected(DECISION, "ck_curator_decision_decision", p=passed, d="maybe", b="Khalid El-Awady", n=None)
    assert w.val(DECISION, p=passed, d="accepted", b="Khalid El-Awady", n="quote checked")
    w.rejected(DECISION, "uq_curator_decision_proposal_id", p=passed, d="rejected", b="Khalid El-Awady", n=None)
    w.rejected("UPDATE curator_decision SET decision = 'rejected'", "append-only")
    w.rejected("UPDATE curator_proposal SET value = '\"compression\"'", "append-only")
    w.rejected("DELETE FROM curator_proposal", "append-only")


def test_the_database_sets_the_decision_time(w, curation):
    v, inv = curation
    passed = w.val(PROPOSAL, i=inv, v=v, **proposal())
    w.run_sql("INSERT INTO curator_decision (proposal_id, decision, decided_by, decided_at) "
              "VALUES (:p, 'accepted', 'K', now() - interval '3 days')", p=passed)
    assert w.val("SELECT decided_at > now() - interval '1 minute' FROM curator_decision WHERE proposal_id = :p",
                 p=passed)
```
### `tests/test_temperature_range.py`

```python
"""Step 8a: plans for other temperature bands (owner, 2026-10-06, Q4; a safeguard change: plan
validation and eligibility rule 3).

One band per plan: room temperature, elevated or cryogenic. A plan for elevated or cryogenic names
the claim's temperature range in its rules (`temperature_range`); a room-temperature plan does not
(its range is the room-temperature rule, unchanged). Rule 3 under a non-room-temperature plan: a
reported temperature inside the range is in scope, outside it out of scope; a band alone, with no
number, is "scope not confirmed" when it is the plan's band and out of scope otherwise. The
reference plan is unchanged, so its fingerprint and the reference numbers are too.
"""
from __future__ import annotations

import copy

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import plan as pl
from test_eligibility import cond

# The reference plan's fingerprint on main before step 8a (cd2b3be), for hypothesis version 1,
# computed from a checkout of that commit.
REFERENCE_FINGERPRINT_ON_MAIN = "830b5343d0bf6db763c6cb2292189a29a0de11170e78d4202cd18669a5aa2c91"


def plan_for(band: str, low=None, high=None, test_type="tension") -> dict:
    p = pl.default_plan(1)
    p["scope"]["temperature_band"] = [band]
    p["scope"]["test_type"] = [test_type]
    if low is not None or high is not None:
        p["rules"]["temperature_range"] = {k: v for k, v in (("min", low), ("max", high)) if v is not None}
    return p


def test_the_reference_plan_is_unchanged():
    ref = pl.reference_plan(1)
    assert "temperature_range" not in ref["rules"] and ref["scope"]["temperature_band"] == ["room temperature"]
    assert pl.validate(ref) == ref
    assert pl.fingerprint(ref) == REFERENCE_FINGERPRINT_ON_MAIN


@pytest.mark.parametrize("band, low, high", [("elevated", 950.0, 1050.0), ("cryogenic", -200.0, -150.0)])
def test_a_plan_for_another_band_names_its_range(band, low, high):
    p = plan_for(band, low, high)
    assert pl.validate(p)["rules"]["temperature_range"] == {"min": low, "max": high}
    with pytest.raises(pl.PlanError, match="temperature range"):
        pl.validate(plan_for(band))


@pytest.mark.parametrize("plan, match", [
    (lambda: plan_for("room temperature", 20.0, 25.0), "temperature range"),     # room temperature names none
    (lambda: plan_for("elevated", 20.0, 1050.0), "above room temperature"),      # overlaps room temperature
    (lambda: plan_for("cryogenic", -200.0, 21.0), "below room temperature"),
    (lambda: plan_for("elevated", 1050.0, 950.0), "temperature range"),           # min above max
    (lambda: plan_for("elevated", 950.0), "temperature range"),                   # one end only
    (lambda: plan_for("warm", 950.0, 1050.0), "outside PLAN_SCHEMA"),           # not a band of the vocabulary
])
def test_invalid_temperature_plans_are_refused(plan, match):
    with pytest.raises(pl.PlanError, match=match):
        pl.validate(plan())


def test_one_band_per_plan():
    p = plan_for("elevated", 950.0, 1050.0)
    p["scope"]["temperature_band"] = ["room temperature", "elevated"]
    with pytest.raises(pl.PlanError, match="one band"):
        pl.validate(p)


@pytest.mark.parametrize("band, test_type, tag", [("elevated", "tension", "elevated temperature"),
                                                  ("elevated", "compression", "elevated temperature"),
                                                  ("cryogenic", "tension", "cryogenic"),
                                                  ("cryogenic", "compression", "cryogenic")])
def test_the_test_condition_tag_of_another_band(band, test_type, tag):
    low, high = (950.0, 1050.0) if band == "elevated" else (-200.0, -150.0)
    assert pl.tags_for(pl.validate(plan_for(band, low, high, test_type)))["test_condition"] == tag


@pytest.mark.parametrize("record, verdict", [
    (cond(1, temp=1000.0), "in"),
    (cond(1, temp=1100.0), "in"),                       # the range includes its ends
    (cond(1, temp=800.0), "out"),
    (cond(1, temp=25.0), "out"),
    (cond(1, temp=None, band="elevated"), "unconfirmed"),  # a band alone does not confirm the range
    (cond(1, temp=None, band="room temperature"), "out"),
    (cond(1, temp=None), "unconfirmed"),
])
def test_rule_3_under_an_elevated_plan(record, verdict):
    st = el.settings(plan_for("elevated", 900.0, 1100.0))
    assert el.scope(record, st) == verdict


@pytest.mark.parametrize("record, verdict", [
    (cond(1, temp=22.0), "in"),
    (cond(1, temp=1000.0), "out"),
    (cond(1, temp=None, band="room temperature"), "in"),   # unchanged: the band decides when accepted
    (cond(1, temp=None, band="elevated"), "out"),
])
def test_rule_3_under_a_room_temperature_plan_is_unchanged(record, verdict):
    assert el.scope(record, el.settings(pl.default_plan(1))) == verdict


def test_the_range_comes_from_the_plan():
    narrow = el.settings(plan_for("elevated", 990.0, 1010.0))
    wide = el.settings(plan_for("elevated", 900.0, 1100.0))
    record = cond(1, temp=950.0)
    assert (el.scope(record, narrow), el.scope(record, wide)) == ("out", "in")


def test_every_sensitivity_set_keeps_the_range():
    p = plan_for("elevated", 900.0, 1100.0)
    for key in p["sensitivity_analyses"]:
        assert el.settings(p, key).temperature_range == (900.0, 1100.0)
    assert copy.deepcopy(p) == p
```

## 4. Changed tests and test helpers (diff)

```diff
diff --git a/tests/access_testing.py b/tests/access_testing.py
index d95d596..47dabf9 100644
--- a/tests/access_testing.py
+++ b/tests/access_testing.py
@@ -13,3 +13,11 @@ from hypocurate.access.layer import _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, Access
 def access_for(engine, run_id, role, stage, source_key=None, lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
     return Access(engine, AccessContext(run_id, role, stage, source_key), lock_timeout_ms=lock_timeout_ms,
                   _trusted=_TRUSTED)
+
+
+def registration_access_for(engine, invocation_id, source_version_id, role="curator", stage="registration",
+                            source_key=None, lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
+    """A registration context (step 8a) the dispatcher would or would not produce."""
+    return Access(engine, AccessContext(None, role, stage, source_key, None, source_version_id=source_version_id,
+                                        invocation_id=invocation_id), lock_timeout_ms=lock_timeout_ms,
+                  _trusted=_TRUSTED)
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 8517b37..3490fe1 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -56,9 +56,14 @@ class World:
         return self.val("INSERT INTO source_version (source_id, label, obtained_on) "
                         "VALUES (:s, :l, '2026-10-04') RETURNING id", s=self.source[key], l=label)
 
-    def add_file(self, version, path, content):
-        self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)",
-                     v=version, p=path, h=sha(content), c=content)
+    def add_file(self, version, path, content, role=None):
+        """A file of the version; `role` (step 8a, 0005) left out means the database's default, 'data'."""
+        if role is None:
+            self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)",
+                         v=version, p=path, h=sha(content), c=content)
+        else:
+            self.run_sql("INSERT INTO source_file (source_version_id, path, sha256, content, role) "
+                         "VALUES (:v, :p, :h, :c, :o)", v=version, p=path, h=sha(content), c=content, o=role)
 
     def files(self, version):
         return {p: bytes(c) for p, c in self.rows(
@@ -126,10 +131,15 @@ class World:
         return vid
 
     # --- runs -------------------------------------------------------------------------
-    def run(self, vid=None, sources=("mpea", "tamu_fcc")):
-        """Dispatch: a queued run with a run_source row for every registered source."""
+    def run(self, vid=None, sources=("mpea", "tamu_fcc"), agents=False):
+        """Dispatch: a queued run with a run_source row for every registered source; with `agents`,
+        the world's settings version of every role recorded too (needed for model calls, step 8a)."""
         vid = vid or self.dispatched()
         rid = self.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
+        if agents:
+            for role in ("planner", "curator", "critic", "analyst", "commentator"):
+                self.run_sql("INSERT INTO run_agent_setting VALUES (:r, :o, :s)", r=rid, o=role,
+                             s=self.agent_setting(role))
         for key in self.source:
             if key in sources:
                 self.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
@@ -192,11 +202,11 @@ class World:
         self.run_sql("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)",
                      r=rid, fp=FP, n=n)
 
-    def frozen(self, n=4, per_source=None, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1)):
+    def frozen(self, n=4, per_source=None, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1), agents=False):
         """A running run, locked and frozen, with n eligible records in its primary set.
         per_source: {"mpea": 3, "tamu_fcc": 1}; default: all from MPEA."""
         per_source = per_source or {"mpea": n}
-        rid = self.running()
+        rid = self.running(agents=agents)
         self.lock(rid, option=option, keys=keys, mins=mins)
         primary = self.analysis_set(rid)
         recs = []
@@ -260,11 +270,32 @@ class World:
         return self.val("INSERT INTO stage_result (run_id, stage, role, attempt) VALUES (:r, :s, :o, :a) RETURNING id",
                         r=rid, s=stage, o=role, a=attempt)
 
-    def call(self, rid, stage_id, max_cost=0.5, role="planner"):
+    AGENT_TEST_VERSION = 1000  # the world's own settings; tests that create settings use small versions
+
+    def agent_setting(self, role):
+        """The world's settings version for a role, created once (agent_setting is append-only)."""
+        found = self.val("SELECT id FROM agent_setting WHERE role = :o AND version = :v", o=role, v=self.AGENT_TEST_VERSION)
+        return found or self.val("INSERT INTO agent_setting (role, version, instruction, model) "
+                                 "VALUES (:o, :v, 'test', 'model-a') RETURNING id", o=role, v=self.AGENT_TEST_VERSION)
+
+    def invocation(self, rid, stage_id, role="planner"):
+        """Step 8a (0005): a run invocation for the stage, with the setting recorded for the run at
+        dispatch (a run made with `agents=True`)."""
+        setting = self.val("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = :o",
+                           r=rid, o=role)
+        assert setting is not None, "make the run with agents=True to record its agent settings at dispatch"
+        return self.val("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
+                        "VALUES ('run', :r, :s, :o, :a) RETURNING id", r=rid, s=stage_id, o=role, a=setting)
+
+    def call(self, rid, stage_id, max_cost=0.5, role=None):
+        """A model call, with its invocation (step 8a, 0005). The role defaults to the stage's; a
+        different role is refused by the invocation (0005), as a test may want to show."""
+        role = role or self.val("SELECT role FROM stage_result WHERE id = :s", s=stage_id)
+        inv = self.invocation(rid, stage_id, role)
         return self.val(
-            "INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
-            "VALUES (:r, :s, :o, 'model-a', 'prices-2026-10', :m) RETURNING id",
-            r=rid, s=stage_id, o=role, m=max_cost)
+            "INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, "
+            "max_cost) VALUES (:r, :s, :i, :o, 'model-a', 'prices-2026-10', :m) RETURNING id",
+            r=rid, s=stage_id, i=inv, o=role, m=max_cost)
 
     def finish_call(self, call_id, status="succeeded", usage=(1000, 200, 0, 0.01)):
         i, o, c, cost = usage if usage else (None, None, None, None)
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index 6813d4f..7d29053 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -25,8 +25,10 @@ def registered(engine, keys=SOURCE_KEYS) -> dict[str, int]:
 
 def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
     """Registers each source key with one sealed version holding the given file (MPEA layout for
-    'mpea' and 'controlled_duplicates'), with the settings of the code's source definition."""
-    from hypocurate.sources.versions import SOURCES, files_digest, version_identity
+    'mpea' and 'controlled_duplicates'), with the settings of the code's source definition. Step 8a:
+    a Texas A&M version also holds the frozen curation (the owner's accepted values: test type
+    tension, phase class FCC), as the real source does, since adapter version 3 no longer assigns them."""
+    from hypocurate.sources.versions import DATA_DIR, SOURCES, file_role, files_digest, version_identity
     out = {}
     for key, content in files.items():
         d = SOURCES[key]
@@ -39,9 +41,14 @@ def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
             vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) "
                                     "VALUES (:s, 'test file', '2026-10-06') RETURNING id"), dict(s=sid)).scalar()
             import hashlib
-            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)"),
-                         dict(v=vid, p=name, h=hashlib.sha256(content).hexdigest(), c=content))
-            digest = files_digest({name: content})
+            stored = {name: content}
+            if d.curation_file:
+                stored[d.curation_file] = (DATA_DIR / d.directory / d.curation_file).read_bytes()
+            for path, data in stored.items():
+                conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content, role) "
+                                  "VALUES (:v, :p, :h, :c, :r)"),
+                             dict(v=vid, p=path, h=hashlib.sha256(data).hexdigest(), c=data, r=file_role(path)))
+            digest = files_digest(stored)
             conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v"),
                          dict(v=vid, fp=version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)))
         out[key] = vid
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index f9b9eaa..904d56a 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -101,7 +101,7 @@ def test_an_agent_setting_cannot_bind_as_a_code_role(engine):
     """`bind` takes the role from run_agent_setting, whose roles are the five agent roles."""
     world = aw.build(engine, "curation")
     for role, setting in world.settings.items():
-        assert bind(engine, world.run, setting, source_key="mpea" if role == "curator" else None).context.role == role
+        assert bind(engine, world.run, setting).context.role == role
     with engine.connect() as conn:
         setting = conn.execute(text("SELECT id FROM agent_setting LIMIT 1")).scalar()
     for role in CODE_ROLES:
diff --git a/tests/test_access_dispatch.py b/tests/test_access_dispatch.py
index 9bb6499..bcf30c9 100644
--- a/tests/test_access_dispatch.py
+++ b/tests/test_access_dispatch.py
@@ -46,8 +46,9 @@ def test_bind_reads_the_role_from_the_runs_agent_settings_and_the_stage_from_the
     for role in ("critic", "analyst", "planner"):
         a = bind(engine, world.run, world.settings[role])
         assert a.context == AccessContext(world.run, role, "curation", None, world.settings[role])
-    curator = bind(engine, world.run, world.settings["curator"], source_key="mpea")
-    assert curator.context.role == "curator" and curator.context.source_key == "mpea"
+    # Step 8a: the Curator binds to a run with no source and then has nothing at a run stage.
+    curator = bind(engine, world.run, world.settings["curator"])
+    assert curator.context.role == "curator" and curator.context.source_key is None
     assert role_input(bind(engine, world.run, world.settings["critic"]))["flags_kind"]
     binds = [r for r in audit(engine, world.run) if r.function == "bind"]
     assert len(binds) == 5 and all(r.allowed and r.detail["result"] == "allowed" for r in binds)
@@ -57,10 +58,11 @@ def test_bind_refuses_a_setting_or_source_the_run_did_not_record(engine):
     world = aw.build(engine, "curation")
     stray = aw.val(world.w, "INSERT INTO agent_setting (role, version, instruction, model) "
                             "VALUES ('analyst', 2, 'x', 'model-a') RETURNING id")
+    # Step 8a: no run role is bound to a source, the Curator included (it reads at registration).
     cases = [(dict(agent_setting_id=stray), "setting_not_recorded"),
-             (dict(agent_setting_id=world.settings["curator"]), "no_source"),
+             (dict(agent_setting_id=world.settings["curator"], source_key="mpea"), "source_not_for_role"),
              (dict(agent_setting_id=world.settings["curator"], source_key="controlled_duplicates"),
-              "source_not_recorded"),
+              "source_not_for_role"),
              (dict(agent_setting_id=world.settings["critic"], source_key="mpea"), "source_not_for_role")]
     for kw, code in cases:
         with pytest.raises(AccessDenied) as denied:
diff --git a/tests/test_access_layer.py b/tests/test_access_layer.py
index d88be8c..a05eaa1 100644
--- a/tests/test_access_layer.py
+++ b/tests/test_access_layer.py
@@ -42,8 +42,6 @@ def engine(migrated_database):
 
 
 def access(engine, world, role, stage, **kw):
-    if role == "curator" and "source_key" not in kw:
-        kw["source_key"] = "mpea"
     return access_for(engine, world.run, role, stage, **kw)
 
 
@@ -60,10 +58,14 @@ def test_the_allow_list_matches_the_owners_table():
     assert ROLES == ("planner", "curator", "critic", "analyst", "commentator")
     assert set(ALLOWED) == set(ROLES)
     assert {r: set(s) for r, s in ALLOWED.items()} == {
-        "planner": {"before_lock"}, "curator": {"curation"}, "critic": {"curation"},
+        "planner": {"before_lock"}, "curator": {"registration"}, "critic": {"curation"},
         "analyst": {"analysis", "closed_without_freeze"}, "commentator": {"final", "final_without_freeze"}}
     assert allowed("planner", "before_lock") == {"claim", "domain", "sources_meta", "tag_values", "record_counts"}
-    assert allowed("curator", "curation") == {"plan_fields_to_extract", "sources_meta", "source_content"}
+    # Owner, 2026-10-06 (step 8a, Q2): the Curator reads a source version's documentation at
+    # registration, never in a run.
+    assert allowed("curator", "registration") == {"source_documentation", "curation_targets"}
+    assert all(allowed("curator", stage) == frozenset() for stage in STAGES if stage != "registration")
+    assert all(allowed(role, "registration") == frozenset() for role in ROLES if role != "curator")
     assert allowed("critic", "curation") == {"sources_meta", "record_metadata", "flags_kind"}
     analysis = {"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full", "results",
                 "coverage", "stage_outputs", "run_cost"}
@@ -87,7 +89,7 @@ def test_every_listed_field_has_a_reader_and_a_description():
 
 
 def test_no_outcome_reaching_field_is_listed_for_the_planner_the_critic_or_the_gap_report():
-    outcome_bearing = {"records_full", "flags_full", "results", "stage_outputs", "source_content", "plan"}
+    outcome_bearing = {"records_full", "flags_full", "results", "stage_outputs", "source_documentation", "plan"}
     for role, stage in (("planner", "before_lock"), ("critic", "curation")):
         assert not allowed(role, stage) & outcome_bearing, role
     assert not allowed("analyst", "closed_without_freeze") & (outcome_bearing - {"plan"})
@@ -161,12 +163,12 @@ def test_a_denied_row_survives_the_rejection_and_the_callers_rollback(engine):
 def test_the_planner_and_the_critic_asking_for_outcomes_are_denied_and_logged(engine, world_stage, role):
     """Criterion 14.2, first point."""
     world = aw.build(engine, world_stage)
-    for field in ("records_full", "flags_full", "results", "stage_outputs", "source_content"):
+    for field in ("records_full", "flags_full", "results", "stage_outputs", "source_documentation"):
         with pytest.raises(AccessDenied):
             access(engine, world, role, world_stage).get(field)
     denied = [r for r in audit(engine, world.run) if r.role == role and not r.allowed]
     assert {r.function for r in denied} == {"records_full", "flags_full", "results", "stage_outputs",
-                                            "source_content"}
+                                            "source_documentation"}
     assert not [r for r in audit(engine, world.run) if r.role == role and r.allowed]
 
 
@@ -209,23 +211,23 @@ def test_the_rules_lock_changes_what_each_role_may_see(engine):
     critic = access(engine, world, "critic", "curation")
     curator = access(engine, world, "curator", "curation")
     assert planner.get("claim")["text"] == aw.DIRECTION
-    for a, field in ((critic, "record_metadata"), (curator, "plan_fields_to_extract")):
-        with pytest.raises(AccessDenied):
-            a.get(field)
+    with pytest.raises(AccessDenied):
+        critic.get("record_metadata")
     aw.lock(world.w, world.run)
     with pytest.raises(AccessDenied, match="no longer at the stage"):
         planner.get("claim")
     assert critic.get("record_metadata") == []
-    assert curator.get("plan_fields_to_extract") == ["grain_size", "yield_strength", "composition"]
+    # Step 8a: the Curator has nothing at the curation stage (it reads at registration).
+    with pytest.raises(AccessDenied, match="not on the role's list"):
+        curator.get("sources_meta")
 
 
 def test_the_dataset_freeze_changes_what_each_role_may_see(engine):
     world = aw.build(engine, "curation")
     w = world.w
     critic = access(engine, world, "critic", "curation")
-    curator = access(engine, world, "curator", "curation")
     analyst = access(engine, world, "analyst", "analysis")
-    assert critic.get("flags_kind") and curator.get("sources_meta")
+    assert critic.get("flags_kind")
     with pytest.raises(AccessDenied):
         analyst.get("records_full")
     primary = w.analysis_set(world.run)
@@ -233,9 +235,8 @@ def test_the_dataset_freeze_changes_what_each_role_may_see(engine):
         w.decide(world.run, rec)
         w.add(primary, rec)
     w.freeze(world.run, len(world.records))
-    for a, field in ((critic, "flags_kind"), (curator, "sources_meta")):
-        with pytest.raises(AccessDenied, match="no longer at the stage"):
-            a.get(field)
+    with pytest.raises(AccessDenied, match="no longer at the stage"):
+        critic.get("flags_kind")
     assert len(analyst.get("records_full")) == len(world.records)
 
 
@@ -341,27 +342,24 @@ def test_sources_meta_comes_from_the_code_and_the_sealed_version_not_the_registr
                     "licence": d.licence, "grouping_unit": "paper", "fields_available": list(d.properties_covered)}
 
 
-def test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim(engine):
-    world = aw.build(engine, "curation")
-    got = role_input(access(engine, world, "curator", "curation"))
-    assert got["plan_fields_to_extract"] == ["grain_size", "yield_strength", "composition"]
-    assert [s["key"] for s in got["sources_meta"]] == ["mpea"]  # its own source only
-    assert list(got["source_content"]["files"]) == ["mpea_planted.csv"]
-    without_files = json.dumps({k: v for k, v in got.items() if k != "source_content"})
-    assert "ZQXDIR" not in without_files and "rises" not in without_files and "k > 0" not in without_files
-    assert b"ZQXDIR" not in got["source_content"]["files"]["mpea_planted.csv"]
-    other = access(engine, world, "curator", "curation", source_key="controlled_duplicates")
-    assert other.get("sources_meta") == []
-    with pytest.raises(AccessDenied, match="not recorded for this run"):
-        other.get("source_content")
-    with pytest.raises(AccessDenied, match="reads one named source"):
-        access(engine, world, "curator", "curation", source_key=None).get("source_content")
+@pytest.mark.parametrize("world_stage", ["before_lock", "curation", "analysis"])
+def test_the_curator_has_nothing_in_any_run(engine, world_stage):
+    """Step 8a (owner, 2026-10-06, Q2), replacing the run-stage Curator test of step 5: the Curator
+    reads a source version at registration (tests/test_access_curator.py), never a run's data."""
+    world = aw.build(engine, world_stage)
+    a = access(engine, world, "curator", WORLD_STAGES[world_stage])
+    with pytest.raises(AccessDenied, match="no field at this stage"):
+        role_input(a)
+    for field in ("sources_meta", "record_metadata", "claim", "source_documentation"):
+        with pytest.raises(AccessDenied):
+            a.get(field)
 
 
 def test_inclusion_is_not_the_curators(engine):
     """The Curator's list has no eligibility, set or flag field (criterion 14.2, fourth point);
     eligibility is code's (step 6)."""
-    assert not allowed("curator", "curation") & {"decisions", "flags_kind", "flags_full", "record_metadata"}
+    assert not allowed("curator", "registration") & {"decisions", "flags_kind", "flags_full", "record_metadata",
+                                                      "records_full", "claim", "plan"}
 
 
 def test_record_metadata_carries_no_number_but_identity_and_composition(engine):
diff --git a/tests/test_access_projected.py b/tests/test_access_projected.py
index 0571f79..af44030 100644
--- a/tests/test_access_projected.py
+++ b/tests/test_access_projected.py
@@ -101,7 +101,7 @@ def engine(migrated_database):
 def inputs_of(engine, world, role, stage=None):
     """The role's projected input, through the real dispatcher (role from the run's agent
     settings, stage from the database). `stage` is only checked."""
-    access = bind(engine, world.run, world.settings[role], source_key="mpea" if role == "curator" else None)
+    access = bind(engine, world.run, world.settings[role])
     assert stage is None or access.context.stage == stage
     return role_input(access)
 
@@ -216,12 +216,10 @@ def test_nothing_from_another_run_reaches_any_role(engine, world_stage):
     checked = 0
     for role in ROLES:
         if allowed(role, world_stage):
+            # Step 8a: the Curator has nothing at any run stage (its registration input is tested in
+            # tests/test_access_curator.py), so every role checked here is a run role.
             got = inputs_of(engine, world, role, world_stage)
-            if role != "curator":  # the Curator's input is its own source's bytes
-                assert leaks(got, [aw.OTHER]) == [], role
-            else:
-                assert str(aw.OTHER).encode() not in got["source_content"]["files"]["mpea_planted.csv"]
-                assert leaks({k: v for k, v in got.items() if k != "source_content"}, [aw.OTHER]) == []
+            assert leaks(got, [aw.OTHER]) == [], role
             checked += 1
     assert checked >= 1
     if world_stage == "before_lock":
diff --git a/tests/test_adapter_tamu.py b/tests/test_adapter_tamu.py
index d7c98e6..e6af168 100644
--- a/tests/test_adapter_tamu.py
+++ b/tests/test_adapter_tamu.py
@@ -97,13 +97,19 @@ def test_one_group_the_dataset(records):
 
 def test_assigned_values_carry_their_passage(records):
     """Step 6 (owner, 2026-10-05): two assigned statuses. Test type and phase class are
-    assigned from the source's own statements; the band and the microstructure by decision."""
+    assigned from the source's own statements; the band and the microstructure by decision.
+    Step 8a (owner, 2026-10-06): the first two come from the frozen curation (the Curator's proposals
+    the owner accepted), quoting the same passages the adapter cited by hand before (version 2)."""
     for r in records:
         t, p = r.harmonized["test_type"], r.harmonized["phase_class"]
-        assert (t.value, t.status, t.citation) == ("tension", "assigned_from_source", tamu_fcc.TEST_TYPE_CITATION)
-        assert (p.value, p.status, p.citation) == ("FCC", "assigned_from_source", tamu_fcc.PHASE_CITATION)
-        assert "Quasistatic tensile testing" in t.citation.quote and t.citation.location.startswith("line 177")
-        assert "94 FCC alloy conditions" in p.citation.quote
+        assert (t.value, t.status, p.value, p.status) == ("tension", "assigned_from_source", "FCC",
+                                                          "assigned_from_source")
+        assert t.citation.quote == ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while "
+                                    "Vickers indentation tests provided the HV.")
+        assert p.citation.quote == "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."
+        assert t.citation.location.startswith("line 177; Curator proposal 5") and "Khalid El-Awady" in t.citation.location
+        assert p.citation.location.startswith("line 173; Curator proposal 2")
+        assert t.citation.document == "tamu_fcc: documentation/main.tex (sealed with the source)"
         b, m = r.harmonized["test_temperature_band"], r.harmonized["microstructure"]
         assert (b.value, b.status, b.citation) == ("room temperature", "assigned_by_decision",
                                                    tamu_fcc.TEMPERATURE_DECISION)
@@ -232,8 +238,8 @@ def test_planted_values_are_kept_and_marked():
     assert {k: v for k, v in by_row[4].harmonized.items() if k != "grain_size_sd"} == \
         {k: v for k, v in by_row[0].harmonized.items() if k != "grain_size_sd"}
     assert (h(4, "grain_size").value, h(4, "yield_strength").value) == (23.0, 284.2)
-    assert (h(4, "test_type").status, h(4, "test_type").citation) == ("assigned_from_source",
-                                                                      tamu_fcc.TEST_TYPE_CITATION)
+    # Step 8a (adapter version 3): with no curation in this constructed version, no test type is assigned.
+    assert (h(4, "test_type").status, h(4, "test_type").reason) == ("not_reported", tamu_fcc.CURATED)
     assert h(4, "test_temperature").status == "not_reported"
     assert h(4, "test_temperature").reason == tamu_fcc.TEMPERATURE_NOT_REPORTED
     assert by_row[4].alloy == by_row[0].alloy
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 65287b5..b118294 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -60,7 +60,7 @@ def test_every_category_has_entries_and_keys_are_unique():
 # Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
-PARTLY = {"constructed_test_runs"}
+PARTLY = {"constructed_test_runs", "agent_models"}  # step 8a: the other roles' settings come in step 8b
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -128,10 +128,13 @@ def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review
     and added the possible-duplicate case and the rule for several candidates in step 6 planning.
     Step 6 recorded two new open decisions for the owner (steps 7 and 8). Step 7: the owner decided
     the first; a new one (records without a group) was open before step 8, and the owner decided it in
-    step 7b (2026-10-06)."""
-    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["curator_tabular_sources"]
-    assert {e["key"]: e["pending"]["before_step"] for e in REGISTER if e["state"] == "open"} == {
-        "curator_tabular_sources": 8}
+    step 7b (2026-10-06). Step 8a: the owner decided the last one, the Curator's role (2026-10-06)."""
+    assert [e["key"] for e in REGISTER if e["state"] == "open"] == []
+    curator = BY_KEY["curator_tabular_sources"]
+    assert curator["state"] == "in_force" and curator["decided"] == {"by": OWNER, "date": "2026-10-06"}
+    assert "pending" not in curator and curator["applied"]["status"] == "yes"
+    assert curator["history"][-1]["value"].startswith("Open: what the Curator agent does for tabular sources")
+    assert "never in a run" in curator["statement"] and "grouped by dataset" in curator["statement"]
     grouped = BY_KEY["records_without_group"]
     assert grouped["state"] == "in_force" and grouped["decided"] == {"by": OWNER, "date": "2026-10-06"}
     assert "pending" not in grouped and grouped["applied"]["status"] == "yes"
@@ -464,7 +467,8 @@ HEADINGS = ["Open decisions", "Direction approved, pending technical review",
 def test_the_page_shows_every_entry_grouped_with_pending_states_first():
     html = signed_in().get("/assumptions").text
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
-    assert headings == HEADINGS  # step 6 recorded two open decisions (steps 7 and 8)
+    # Step 8a: no decision is open, so the page leaves out the "Open decisions" heading (step 4b design).
+    assert headings == HEADINGS[1:]
     for e in REGISTER:
         assert f'id="{e["key"]}"' in html, e["key"]
     sections = re.split(r"<h2>", html)[1:]
@@ -479,10 +483,11 @@ def test_open_decisions_are_shown_first_when_there_are_any():
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
     assert headings == HEADINGS
     first = re.split(r"<h2>", html)[1]
-    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["curator_tabular_sources", "an_open_question"]
+    # Step 8a: the register's last open entry is decided; only the fixture's is open.
+    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["an_open_question"]
     assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
-    assert first.count("Not decided (owner, before step 8)") == 1  # records_without_group decided in step 7b
-    assert "2 open decisions</strong>" in html
+    assert first.count("Not decided (owner, before step 8)") == 0
+    assert "1 open decision</strong>" in html
     second = re.split(r"<h2>", html)[2]
     assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
     assert "pending: second-model technical review, before step 8" in second
@@ -493,9 +498,9 @@ def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
     summary = " ".join(re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1).split())
     count = {s: sum(e["state"] == s for e in REGISTER) for s in a.STATES}
     n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
-    assert count == {"in_force": len(REGISTER) - 2, "open": 1, "direction_approved": 1}
+    assert count == {"in_force": len(REGISTER) - 1, "open": 0, "direction_approved": 1}  # step 8a: none open
     assert f"{len(REGISTER)} entries: {count['in_force']} in force" in summary
-    assert "1 open decision</strong>" in summary
+    assert "0 open decisions</strong>" in summary
     assert "1 direction approved, pending technical review</strong>" in summary
     assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
     assert html.index('id="summary"') < html.index("<h2>")
@@ -532,7 +537,11 @@ def test_the_filter_shows_only_entries_not_reviewed_by_an_expert():
 
 
 def test_each_row_expands_to_reason_evidence_history_and_sensitivity():
-    html = signed_in().get("/assumptions").text
+    # Step 8a: no register entry is "not yet" applied any more (spending_caps is applied), so the
+    # "Not yet" display is shown on a fixture entry.
+    not_yet = copy.deepcopy(BY_KEY["spending_caps"])
+    not_yet.update(key="a_not_yet_entry", applied={"status": "not_yet", "step": 9, "note": None}, tests=[])
+    html = signed_in(REGISTER + [not_yet]).get("/assumptions").text
     body = re.search(r'<tbody id="values_disagree_tolerance"(.*?)</tbody>', html, re.S).group(1)
     e = BY_KEY["values_disagree_tolerance"]
     assert "<details>" in body
@@ -540,7 +549,7 @@ def test_each_row_expands_to_reason_evidence_history_and_sensitivity():
         assert str(escape(text)) in body, text
     applied = re.search(r'<tbody id="session_length"(.*?)</tbody>', html, re.S).group(1)
     assert "<code>python:hypocurate.web.app:SESSION_MAX_AGE</code>" in applied
-    assert "Not yet: step 9" in re.search(r'<tbody id="spending_caps"(.*?)</tbody>', html, re.S).group(1)
+    assert "Not yet: step 9" in re.search(r'<tbody id="a_not_yet_entry"(.*?)</tbody>', html, re.S).group(1)
     assert "<code>tests/test_login.py::test_session_expires_after_max_age</code>" in applied
     assert "Named settings (reference and value checks only)" in applied
 
diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 52e3a04..050ae14 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -311,7 +311,7 @@ def test_records_are_stored_only_after_the_lock_with_how_they_were_extracted(eng
                      "WHERE r.extraction_run_id = :r ORDER BY r.id", r=rid)
     assert {(r.key, json.dumps(r.extraction, sort_keys=True)) for r in rows} == {
         ("mpea", json.dumps({"method": "adapter", "name": "mpea_layout", "version": "1"}, sort_keys=True)),
-        ("tamu_fcc", json.dumps({"method": "adapter", "name": "tamu_fcc", "version": "2"}, sort_keys=True))}
+        ("tamu_fcc", json.dumps({"method": "adapter", "name": "tamu_fcc", "version": "3"}, sort_keys=True))}  # step 8a
     # Unchanged and in file order: the adapter's own output.
     expected = adapters.read(sealed_from_disk("tamu_fcc")).records
     tamu = [r for r in rows if r.key == "tamu_fcc"]
diff --git a/tests/test_concurrency.py b/tests/test_concurrency.py
index 4b668ab..c15dd9c 100644
--- a/tests/test_concurrency.py
+++ b/tests/test_concurrency.py
@@ -307,7 +307,7 @@ def test_following_the_protocol_does_not_deadlock(w):
 
 
 def test_following_the_protocol_on_model_calls_does_not_deadlock(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     call = w.call(rid, w.stage(rid))
     finish = ("UPDATE model_call SET status = 'interrupted', finished_at = now() WHERE id = :c "
               "AND status = 'started'")
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index db7527b..9ac1872 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -794,7 +794,7 @@ def test_no_dataset_frozen_and_a_freeze_exclude_each_other(w):
 def test_what_may_be_written_after_completion(w):
     """Owner, 2026-10-05: the commentary, the Commentator's stage and model calls, and
     artifacts. The Commentator's calls count in the run's totals and cap. Nothing else."""
-    rid, sets, _ = w.frozen()
+    rid, sets, _ = w.frozen(agents=True)
     w.result(rid, sets["primary"])
     w.complete(rid, "sufficient", "supported")
     commentator = w.stage(rid, "commentator", "commentator")
@@ -820,7 +820,7 @@ def test_what_may_be_written_after_completion(w):
 
 
 def test_nothing_but_the_audit_log_after_failure(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     st = w.stage(rid, "planner", "planner")
     w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE id = :s", s=st)
     w.fail(rid, "worker stopped")
@@ -837,7 +837,7 @@ def test_nothing_but_the_audit_log_after_failure(w):
 
 @pytest.mark.parametrize("ending", ["completed", "failed"])
 def test_a_run_ends_only_with_no_stage_running_and_no_call_open(w, ending):
-    rid = w.running()
+    rid = w.running(agents=True)
     st = w.stage(rid)
     end = (lambda: w.complete(rid, "insufficient")) if ending == "completed" else (lambda: w.fail(rid))
     with pytest.raises(IntegrityError, match="no stage is running and no model call is open"):
@@ -1037,7 +1037,7 @@ def test_calibration_intervals_contain_their_share(w):
 # --- model calls and totals (owner decision, question 5) ------------------------------------------------
 
 def test_a_model_call_is_recorded_before_the_request_and_finished_once(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     st = w.stage(rid)
     w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, status, "
                "input_tokens, output_tokens, cached_tokens, cost, finished_at) VALUES (:r, :s, 'planner', 'm', 'p', 1, "
@@ -1052,7 +1052,7 @@ def test_a_model_call_is_recorded_before_the_request_and_finished_once(w):
 
 
 def test_model_call_usage_rules(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     st = w.stage(rid)
     w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
                "VALUES (:r, :s, 'planner', 'm', '', 1)", "ck_model_call_model_and_prices_named", r=rid, s=st)
@@ -1065,13 +1065,18 @@ def test_model_call_usage_rules(w):
                "cost = 0, finished_at = now() WHERE id = :c", "ck_model_call_usage_not_negative", c=partial)
     w.rejected("UPDATE model_call SET status = 'failed', max_cost = 0, finished_at = now() WHERE id = :c",
                "before the request cannot change", c=partial)
+    # A call whose stage belongs to another run. Step 8a (0005): every call names its invocation, and
+    # the call must have the invocation's run, stage and role, which the insert trigger checks before
+    # the foreign key on (stage, run) is reached; the foreign key still holds for the invocation.
     other = w.running()
-    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
-               "VALUES (:r, :s, 'planner', 'm', 'p', 1)", "fk_model_call_stage_result", r=other, s=st)
+    inv = w.invocation(rid, st)
+    w.rejected("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, "
+               "max_cost) VALUES (:r, :s, :i, 'planner', 'm', 'p', 1)", "its invocation's run, stage and role",
+               r=other, s=st, i=inv)
 
 
 def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     planner, curator = w.stage(rid), w.stage(rid, "curator", "curator")
     ok = w.call(rid, planner, max_cost=0.50)
     w.finish_call(ok, "succeeded", (1000, 200, 100, 0.0123))
@@ -1099,7 +1104,7 @@ def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bou
 def test_small_costs_are_stored_exactly(w):
     """Review finding 7: numeric without a fixed scale; nothing rounds to zero."""
     from decimal import Decimal
-    rid = w.running()
+    rid = w.running(agents=True)
     call = w.call(rid, w.stage(rid), max_cost=Decimal("1E-12"))
     w.finish_call(call, "succeeded", (1, 1, 0, Decimal("3E-13")))
     w.call(rid, w.stage(rid, "curator", "curator"), max_cost=Decimal("2E-12"))
@@ -1127,7 +1132,7 @@ def test_max_cost_must_be_finite(w, value, match):
     ("-Infinity", "ck_model_call_usage_not_negative"),
 ])
 def test_reported_cost_must_be_finite(w, value, match):
-    rid = w.running()
+    rid = w.running(agents=True)
     call = w.call(rid, w.stage(rid))
     w.rejected("UPDATE model_call SET status = 'succeeded', input_tokens = 1, output_tokens = 1, cached_tokens = 0, "
                "cost = CAST(:v AS numeric), finished_at = now() WHERE id = :c", match, c=call, v=value)
@@ -1135,7 +1140,7 @@ def test_reported_cost_must_be_finite(w, value, match):
 
 
 def test_call_times_are_set_by_the_database(w):
-    rid = w.running()
+    rid = w.running(agents=True)
     st = w.stage(rid)
     w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, started_at) "
                "VALUES (:r, :s, 'planner', 'm', 'p', 1, now() - interval '40 days')", "started_at is set by the database",
diff --git a/tests/test_frozen_sources.py b/tests/test_frozen_sources.py
index acd56fc..a646f27 100644
--- a/tests/test_frozen_sources.py
+++ b/tests/test_frozen_sources.py
@@ -8,7 +8,7 @@ MANIFEST = load_manifest()
 MANIFEST_PATH = REPO_ROOT / "data/manifest.json"
 # Pinned here, outside data/, so the data and the manifest cannot be changed
 # together without changing a test (second-model review of step 1, finding 2).
-MANIFEST_SHA256 = "fa25ebee6a7c95d4d05dfe7eec2d388001fe37cd975e027d688b2de70b11f5b8"
+MANIFEST_SHA256 = "ea06df04819736e2608a508c63f9fff8177a2543d954cdbd1f6e2191f9c45d14"  # step 8a: documentation, curation
 # Every file the manifest must cover. Fixed here so that dropping an entry from
 # the manifest cannot silently remove its fingerprint check.
 REQUIRED_FILES = {
@@ -18,6 +18,12 @@ REQUIRED_FILES = {
     "data/sources/tamu_fcc/inputs.csv",
     "data/sources/tamu_fcc/LICENSE",
     "data/controlled_duplicates/extract.csv",
+    # Step 8a (owner, 2026-10-06): the sources' documentation, frozen into the source versions.
+    "data/sources/tamu_fcc/documentation/main.tex",
+    "data/sources/tamu_fcc/documentation/supplementary.tex",
+    "data/sources/mpea/documentation/Borg2020_PMC7722748.xml",
+    # Step 8a (owner, 2026-10-06): the Curator's proposals the owner accepted for Texas A&M.
+    "data/sources/tamu_fcc/curation.json",
 }
 MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
 TAMU_XLSX = REPO_ROOT / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
@@ -83,6 +89,40 @@ def test_manifest_records_origin_date_and_licence(source_id):
     assert s["licence_file"] in {f["path"] for f in s["files"]}, "licence text must be frozen too"
 
 
+def test_documentation_records_its_origin_and_licence():
+    """Step 8a (owner, 2026-10-06): each frozen document states where it came from and under
+    which licence; the Texas A&M documents come from the pinned commit's archive."""
+    tamu = MANIFEST["sources"]["tamu_fcc"]
+    assert [d["path"] for d in tamu["documentation"]] == ["data/sources/tamu_fcc/documentation/main.tex",
+                                                          "data/sources/tamu_fcc/documentation/supplementary.tex"]
+    for d in tamu["documentation"]:
+        assert d["origin_url"].startswith("https://") and tamu["commit"] in d["origin_url"]
+        assert d["archive_member"] == "paper/" + d["path"].rsplit("/", 1)[1]
+    mpea = MANIFEST["sources"]["mpea"]
+    [paper] = mpea["documentation"]
+    assert paper["path"] == "data/sources/mpea/documentation/Borg2020_PMC7722748.xml"
+    assert paper["origin_url"] == "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7722748/fullTextXML"
+    assert paper["licence"].startswith("CC-BY-4.0") and paper["retrieved"] == "2026-10-06"
+    text = (REPO_ROOT / paper["path"]).read_text(encoding="utf-8")
+    assert "Creative Commons Attribution 4.0 International License" in text
+    assert "10.1038/s41597-020-00768-9" in text
+
+
+def test_the_curation_file_records_the_owners_decisions():
+    """Step 8a: the frozen curation holds exactly the two values the owner accepted (proposals 5 and 2;
+    proposal 1, microstructure, rejected), each quoted from the frozen documentation."""
+    import json
+    [entry] = MANIFEST["sources"]["tamu_fcc"]["curation"]
+    assert entry["path"] == "data/sources/tamu_fcc/curation.json" and entry["built"] == "2026-10-06"
+    doc = json.loads((REPO_ROOT / entry["path"]).read_text(encoding="utf-8"))
+    assert doc["source"] == "tamu_fcc" and set(doc["values"]) == {"test_type", "phase_class"}
+    main = (REPO_ROOT / "data/sources/tamu_fcc/documentation/main.tex").read_text(encoding="utf-8").splitlines()
+    for field, value, line in (("test_type", "tension", 177), ("phase_class", "FCC", 173)):
+        v = doc["values"][field]
+        assert (v["value"], v["line"], v["accepted_by"]) == (value, line, "Khalid El-Awady")
+        assert v["quote"] in main[line - 1]
+
+
 def test_licence_texts_match_the_manifest():
     mpea = (REPO_ROOT / MANIFEST["sources"]["mpea"]["licence_file"]).read_text(encoding="utf-8")
     tamu = (REPO_ROOT / MANIFEST["sources"]["tamu_fcc"]["licence_file"]).read_text(encoding="utf-8")
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 30cc08e..587bec5 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -24,6 +24,8 @@ from hypocurate.db.models import Base
 
 REPO = Path(__file__).resolve().parents[1]
 MIGRATION = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0001").module
+# Step 8a: 0005 adds three append-only tables with their own checked inserts.
+MIGRATION_0005 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0005").module
 
 
 def snapshot(engine) -> dict:
@@ -57,6 +59,9 @@ def expected_triggers() -> set[tuple[str, str]]:
     names |= {(t, f"hc_{t}_no_truncate") for t in m.APPEND_ONLY + m.NO_DELETE + ["hypothesis_version_source"]}
     names |= {(t, f"hc_{t}_no_delete") for t in m.NO_DELETE}
     names |= {(t, f) for t, _, f in m.CHECKED}
+    m5 = MIGRATION_0005
+    names |= {(t, f"hc_{t}_append_only") for t in m5.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m5.APPEND_ONLY}
+    names |= {(t, f) for t, _, f in m5.CHECKED}
     return names
 
 
diff --git a/tests/test_migrations_step7.py b/tests/test_migrations_step7.py
index a27f395..bb5d556 100644
--- a/tests/test_migrations_step7.py
+++ b/tests/test_migrations_step7.py
@@ -41,8 +41,9 @@ def checks_of(function_sql: str) -> list[str]:
     return re.findall(r"IF .*? END IF;", body(function_sql))
 
 
-def test_0004_is_the_head_and_follows_0003():
-    assert migrate.head_revision() == "0004" and M0004.down_revision == "0003"
+def test_0004_follows_0003():
+    """Step 8a: 0004 is no longer the head (0005 follows it; tests/test_migrations_step8a.py)."""
+    assert M0004.down_revision == "0003"
 
 
 @pytest.mark.parametrize("name", ["hc_analysis_result_insert", "hc_calibration_insert"])
@@ -124,4 +125,6 @@ def test_the_downgrade_refuses_while_step_7_results_use_0004(db):
     before = snapshot(db)
     with pytest.raises(IntegrityError, match="0004 cannot be downgraded while step 7 results use it"):
         migrate.downgrade(db, "0003")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0004"
+    # Step 8a: the database stays at the head (0005, which holds nothing here, is not undone either:
+    # the whole downgrade is one transaction).
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
diff --git a/tests/test_plan.py b/tests/test_plan.py
index 000a1ba..2fcfdd7 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -19,7 +19,9 @@ def test_the_default_plan_is_valid_and_is_its_own_projection():
     assert validate(content) == content
     assert project(content, PLAN_SCHEMA) == content
     assert set(content) == set(PLAN_SCHEMA) == set(pl.PARTS)
-    assert set(content["rules"]) == set(PLAN_SCHEMA["rules"]) == set(pl.RULES)
+    # Step 8a (owner, 2026-10-06, Q4): the schema also allows the optional temperature range, which a
+    # room-temperature plan (the default) does not name.
+    assert set(content["rules"]) == set(pl.RULES) == set(PLAN_SCHEMA["rules"]) - {pl.RANGE_RULE}
 
 
 def test_the_reference_plan_is_the_default_plan_under_the_owners_decisions():
@@ -101,7 +103,8 @@ def test_the_plan_choices_that_remain():
     (lambda c: c["rules"].update(survivor_source_order=["mpea", "elsewhere"]), "outside PLAN_SCHEMA"),
     (lambda c: c.pop("rules"), "lacks rules"),
     (lambda c: c["rules"].pop("grouping"), "rules are exactly"),
-    (lambda c: c["scope"].update(temperature_band=["cryogenic"]), "room-temperature band only"),
+    # Step 8a (owner, 2026-10-06, Q4): another band is allowed with its temperature range; without it, refused.
+    (lambda c: c["scope"].update(temperature_band=["cryogenic"]), "temperature range"),
     (lambda c: c["rules"].update(min_grain_sizes=1), "out of range"),
     (lambda c: c["rules"].update(room_temperature_min=30.0), "out of range"),
     (lambda c: c["rules"].update(survivor_source_order=["mpea", "mpea"]), "each source once"),
diff --git a/tests/test_skeleton.py b/tests/test_skeleton.py
index d8ea58e..86e95fb 100644
--- a/tests/test_skeleton.py
+++ b/tests/test_skeleton.py
@@ -30,7 +30,8 @@ LAYOUT = [
     "requirements.lock",
     "requirements-dev.lock",
 ]
-SECRET_NAMES = {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD", "DATABASE_URL"}
+# Step 8a: the model provider's key (ANTHROPIC_API_KEY), entered by the owner only.
+SECRET_NAMES = {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD", "DATABASE_URL", "ANTHROPIC_API_KEY"}
 
 
 def read(path):
@@ -136,7 +137,22 @@ def test_runtime_and_dev_locks_agree():
 
 
 def test_test_tools_are_not_in_the_runtime_lock():
-    assert {"pytest", "httpx2", "pyyaml"}.isdisjoint(locked("requirements.lock"))
+    """pytest and httpx2 never reach the runtime image. pyyaml is a test tool too, but from step 8a
+    it is also a dependency of the runtime libraries (litellm, and huggingface-hub through it;
+    owner, 2026-10-06): it may be in the runtime lock only as theirs, never as our own runtime
+    dependency."""
+    runtime = locked("requirements.lock")
+    assert {"pytest", "httpx2"}.isdisjoint(runtime)
+    assert "pyyaml" not in direct_dependencies()
+    assert via("requirements.lock", "pyyaml") <= {"huggingface-hub", "litellm"}
+
+
+def via(path, package):
+    """The packages that pip-compile records as requiring `package` in a lock file."""
+    block = re.search(rf"^{re.escape(package)}==.*?\n((?:    .*\n)+)", read(path), re.M | re.I)
+    lines = [l.strip().lstrip("#").strip() for l in block.group(1).splitlines() if l.strip().startswith("#")]
+    names = [l.removeprefix("via").strip() for l in lines]
+    return {n.split(" ")[0].lower() for n in names if n}
 
 
 # --- Docker image ------------------------------------------------------------------
diff --git a/tests/test_source_versions.py b/tests/test_source_versions.py
index 6e8c378..40b35d1 100644
--- a/tests/test_source_versions.py
+++ b/tests/test_source_versions.py
@@ -98,8 +98,12 @@ def test_registering_seals_every_source(db):
         assert stored == files
         (enabled, status), = rows(db, "SELECT enabled, adapter_status FROM source WHERE key = :k", k=key)
         assert (enabled, status) == (d.enabled, "available")
-    stored_paths = {p for (p,) in rows(db, "SELECT path FROM source_file")}
-    assert stored_paths == {"MPEA_dataset.csv", "Grain_Size_Summary_v3.xlsx", "extract.csv"}
+    # Step 8a (owner, 2026-10-06, Q1): each source's documentation is stored with its data, by role.
+    stored = {(p, r) for p, r in rows(db, "SELECT path, role FROM source_file")}
+    assert stored == {("MPEA_dataset.csv", "data"), ("Grain_Size_Summary_v3.xlsx", "data"), ("extract.csv", "data"),
+                      ("documentation/Borg2020_PMC7722748.xml", "documentation"),
+                      ("documentation/main.tex", "documentation"), ("documentation/supplementary.tex", "documentation"),
+                      ("curation.json", "curation")}  # step 8a: the owner's accepted Curator values
     assert val(db, "SELECT enabled FROM source WHERE key = 'controlled_duplicates'") is False
 
 
@@ -107,7 +111,7 @@ def test_registering_again_adds_nothing(db):
     first = {k: register(db, k) for k in SOURCES}
     counts = [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")]
     again = {k: register(db, k) for k in SOURCES}
-    assert counts == [3, 3, 3]
+    assert counts == [3, 3, 7]  # step 8a: three data files, three documentation files, one curation file
     assert [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")] == counts
     assert all(not r.created and r.version_id == first[k].version_id and r.fingerprint == first[k].fingerprint
                for k, r in again.items())
@@ -274,3 +278,13 @@ def test_changed_settings_on_a_loaded_version_are_refused(db):
         version = load_sealed_version(conn, r.version_id)
     with pytest.raises(UnsealedVersion, match="sealed identity"):
         adapters.read(dataclasses.replace(version, grouping_unit="batch"))
+
+
+# The curated Texas A&M version sealed from the owner's decisions (step 8a, local development database,
+# 2026-10-06): registering the frozen files must give exactly this version, with no model call.
+CURATED_TAMU_FINGERPRINT = "2fad3ccb3dbc32c1ec51e6efcb70a9d17d755bfdfa606cb044f458bd2b37b982"
+
+
+def test_registering_the_frozen_curation_reproduces_the_sealed_curated_version(db):
+    r = register(db, "tamu_fcc")
+    assert r.fingerprint == CURATED_TAMU_FINGERPRINT
```

## 5. Register, manifest and frozen curation

8 new entries, 12 changed (of 122).

### New: `source_documentation`

```json
{
 "key": "source_documentation",
 "name": "Source documentation frozen into the source version",
 "state": "in_force",
 "statement": "Each source's own documentation is frozen with its data (sha256 in the manifest, in a 'documentation' list per source) and stored in the sealed source version as documentation files (paths documentation/<name>.tex|.xml|.md|.txt; source_file.role), so the version's fingerprint covers it. Texas A&M: paper/main.tex and paper/supplementary.tex from the pinned Zenodo archive (MIT); MPEA: the dataset paper's full text from Europe PMC (CC BY 4.0). Adapters read only data files.",
 "value": {
  "text": "documentation files of the sealed version",
  "unit": null
 },
 "category": "data_handling",
 "affects": "What the Curator reads; every source version's fingerprint (not any reference number).",
 "reason": "The Curator proposes values from the source's own documentation, which must be fixed and sealed like the data.",
 "evidence": [
  "Owner, step 8a plan, Q1 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.documentation_files",
    "equals": [
     "documentation/main.tex",
     "documentation/supplementary.tex"
    ]
   },
   {
    "ref": "python:hypocurate.sources.versions:SOURCES.mpea.documentation_files",
    "equals": [
     "documentation/Borg2020_PMC7722748.xml"
    ]
   },
   {
    "ref": "python:hypocurate.sources.versions:file_role"
   },
   {
    "ref": "sql:ck_source_file_safe_data_file_path"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [
  "The folder is 'documentation', not 'docs': the runtime-image check forbids any docs directory (the construction-level guarantee that docs/ never ships)."
 ],
 "tests": [
  "tests/test_frozen_sources.py::test_documentation_records_its_origin_and_licence",
  "tests/test_source_versions.py::test_registering_seals_every_source",
  "tests/test_migrations_step8a.py::test_each_role_has_its_own_path_rule"
 ]
}
```
### New: `curator_quote_checks`

```json
{
 "key": "curator_quote_checks",
 "name": "The two checks on a Curator proposal",
 "state": "in_force",
 "statement": "A Curator proposal passes only if (1) its quote occurs in one of the sealed version's documentation files after collapsing runs of whitespace to one space on both sides (nothing else is normalized: no case folding, no markup changes), code finding the document and the line where it begins, and the database checking the occurrence again when it is stored; the quote is 30 to 1500 characters after collapsing; and (2) the quote contains a listed term for the proposed value (TERMS, case-insensitive; for the test temperature the number as written; for a microstructure joined by '+', every part). Otherwise it is stored as refused with a code and leaves the field unassigned. Neither check shows that the sentence supports the value: a person decides that.",
 "value": {
  "text": "quote found + listed term; 30-1500 characters",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Which Curator proposals a person may accept.",
 "reason": "Owner's decision: a quote must exist in the sealed document and contain a listed term, a first filter; a refused paraphrase leaves the field unassigned, the safe direction.",
 "evidence": [
  "Owner, step 8a plan, Q2 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:QUOTE_MIN_CHARS",
    "equals": 30
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:QUOTE_MAX_CHARS",
    "equals": 1500
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:TERMS"
   },
   {
    "ref": "sql:ck_curator_proposal_proposed_complete"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [
  "The term list itself (TERMS) was drafted by Claude Code in step 8a; the owner approved the check, and the list is for the owner's review with step 8a. Changing it is a register change.",
  "The 30-1500 character bounds are Claude Code's defaults in step 8a, for the owner's review."
 ],
 "tests": [
  "tests/test_curator.py::test_each_proposal_is_stored_as_code_decided_it",
  "tests/test_curator.py::test_an_entry_that_fails_a_check_is_refused_with_its_code",
  "tests/test_curator.py::test_the_quote_checks_collapse_whitespace_only",
  "tests/test_migrations_step8a.py::test_a_proposal_that_did_not_pass_cannot_be_stored_as_passed"
 ]
}
```
### New: `curation_acceptance`

```json
{
 "key": "curation_acceptance",
 "name": "A Curator value takes effect only when a person accepts it",
 "state": "in_force",
 "statement": "A proposal that passed the checks takes effect only when a person accepts it (`hypocurate sources accept <proposal> --by <name>`; one decision per proposal, with the database's time; the command line takes the name as given and has no login). `seal-curation` seals the accepted values only, with quote, document, line, proposal, model and settings version, acceptor and time, as curation.json in a new sealed source version; rejected, refused, unanswered and not-stated proposals are left out (the field stays unassigned). Two accepted proposals for one field are not sealed. Adapters apply a curated value to every record of the version only where the record's field is not reported (never over a reported, converted or decided value), as 'assigned from source' with that citation. Runs use the newest sealed version; a run never calls the Curator. Values 'assigned by decision' stay owner decisions.",
 "value": {
  "text": "accepted by a person; sealed into the version; applied only to gaps",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Which values reach records from the Curator; record content and fingerprints of curated versions.",
 "reason": "Owner's decision: no run depends on live model output for any record value; a proposal is only a proposal until a person accepts it.",
 "evidence": [
  "Owner, step 8a plan, Q2 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.curation:seal_curation"
   },
   {
    "ref": "python:hypocurate.sources.curated:apply_curation"
   },
   {
    "ref": "sql:uq_curator_decision_proposal_id"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [],
 "tests": [
  "tests/test_curator.py::test_a_person_decides_once_and_only_on_a_proposal_that_passed",
  "tests/test_curator.py::test_sealing_applies_accepted_values_only_where_the_table_gives_none",
  "tests/test_curator.py::test_a_curated_version_is_reproducible_from_its_files_and_cannot_be_curated_again",
  "tests/test_curator.py::test_two_accepted_proposals_for_one_field_are_not_sealed",
  "tests/test_curator.py::test_a_curation_file_that_cannot_be_read_refuses_the_version"
 ]
}
```
### New: `agent_models`

```json
{
 "key": "agent_models",
 "name": "The model of each agent role",
 "state": "in_force",
 "statement": "Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5, each with its effort and limits set explicitly in its settings version (agent_setting, append-only). The Curator: at most 8000 output tokens (thinking included), at most 20000 characters of answer, effort medium.",
 "value": {
  "text": "Opus 5.5 / Sonnet 5.5 / Haiku 4.5 / Opus 5.5",
  "unit": null
 },
 "category": "operational",
 "affects": "Every model call's model, cost bound and quality.",
 "reason": "PRD 17, decision 2: a capable model for the Planner and the Analyst, a cheaper one for the Curator and the Critic.",
 "evidence": [
  "Owner, step 8a plan, Q7 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "partly",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.settings:MODELS",
    "equals": {
     "planner": "claude-opus-5-5",
     "curator": "claude-sonnet-5-5",
     "critic": "claude-haiku-4-5",
     "analyst": "claude-opus-5-5"
    }
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:SETTINGS.curator.limits",
    "equals": {
     "max_tokens": 8000,
     "max_output_chars": 20000
    }
   }
  ],
  "done": "The Curator's settings (step 8a).",
  "pending": "The Planner's, the Critic's and the Analyst's settings (step 8b).",
  "step": 8,
  "note": null
 },
 "history": [],
 "notes": [],
 "tests": [
  "tests/test_agent_core.py::test_the_price_table_names_the_owners_models",
  "tests/test_curator.py::test_the_curators_complete_request_is_the_instruction_the_documentation_and_the_targets"
 ]
}
```
### New: `model_prices`

```json
{
 "key": "model_prices",
 "name": "The price table for model calls",
 "state": "in_force",
 "statement": "Cost is computed by code from the token usage the provider reports times a versioned price table (US dollars per million tokens: Opus 5.5 4 input / 20 output, Sonnet 5.5 2 / 10, Haiku 4.5 1 / 5; cache reads 0.20, 0.20, 0.10; cache writes 1.25 times input), stored with each call's table version. The provider reports tokens, not money. Before a request, the call's maximum cost is reserved: the request's UTF-8 JSON bytes as an upper bound of its tokens (a token is never shorter than a byte) plus 1000 tokens for the provider's framing, at the input price, and the request's output limit at the output price. Before the first live call the table is checked against Anthropic's published pricing; work stops if it differs.",
 "value": {
  "text": "anthropic-2026-09-25",
  "unit": null
 },
 "category": "operational",
 "affects": "Every model call's recorded cost and every cap check.",
 "reason": "CLAUDE.md rule 12 and PRD 8: actual cost from the usage the provider reports, with the price table version stored.",
 "evidence": [
  "Prices from Anthropic's published pricing as cached on 2026-09-25 (step 8a planning); owner, step 8a plan (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.prices:PRICE_TABLE_VERSION",
    "equals": "anthropic-2026-09-25"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.prices:FRAMING_ALLOWANCE_TOKENS",
    "equals": 1000
   },
   {
    "ref": "python:hypocurate.pipeline.agents.prices:PRICES"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [
  "The cache prices for Haiku 4.5 (read 0.10) and every cache-write price are assumed from the usual ratios; the agents never request caching. They are checked with the rest of the table before the first live call.",
  "Checked on 2026-10-06 against Anthropic's published pricing (https://platform.claude.com/docs/en/about-claude/pricing), before the first live call: every price in the table matches (Opus 5.5 4 / 5 / 0.20 / 20, Sonnet 5.5 2 / 2.50 / 0.20 / 10, Haiku 4.5 1 / 1.25 / 0.10 / 5 per million tokens for input / 5-minute cache write / cache hit / output), including the cache prices marked as assumed. The page notes that newer models' tokenizer gives about 30% more tokens; the reservation bound counts bytes, never fewer than tokens."
 ],
 "tests": [
  "tests/test_agent_core.py::test_the_price_table_names_the_owners_models",
  "tests/test_agent_core.py::test_a_request_is_reserved_sent_once_and_recorded_with_its_usage_and_cost"
 ]
}
```
### New: `request_failure_policy`

```json
{
 "key": "request_failure_policy",
 "name": "What happens when an agent request fails",
 "state": "in_force",
 "statement": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a failed recording and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request: it goes to the process log only. DSPy's JSON fallback is off.",
 "value": {
  "text": "2 requests at most; retry / correct / stop by code",
  "unit": null
 },
 "category": "operational",
 "affects": "Every agent call's cost and outcome.",
 "reason": "The step 8a failure table (owner, 2026-10-06): every failure mode has a defined, tested outcome.",
 "evidence": [
  "Owner, step 8a plan: the request-path failure table (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.interface:MAX_ATTEMPTS",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:FAILURES"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [
  "litellm cannot read a reply with no usage block and raises a connection error, so such a reply is treated as an unavailable provider (failed, counted at its maximum, tried once more); the code 'cost_unknown' is for a readable reply whose usage is empty."
 ],
 "tests": [
  "tests/test_agent_core.py::test_an_unavailable_provider_is_tried_once_more_with_the_same_request",
  "tests/test_agent_core.py::test_refused_credentials_or_requests_are_not_retried_and_no_provider_text_is_kept",
  "tests/test_agent_core.py::test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer",
  "tests/test_agent_core.py::test_a_refusal_is_not_retried",
  "tests/test_agent_core.py::test_a_reply_without_usage_is_unreadable_failed_and_counted_at_its_maximum",
  "tests/test_agent_core.py::test_a_readable_reply_with_empty_usage_is_cost_unknown",
  "tests/test_agent_core.py::test_a_reply_whose_recording_fails_is_discarded_and_the_call_stays_open",
  "tests/test_agent_core.py::test_no_database_transaction_is_open_while_a_request_is_in_flight"
 ]
}
```
### New: `model_call_libraries`

```json
{
 "key": "model_call_libraries",
 "name": "How the model-call libraries are loaded",
 "state": "in_force",
 "statement": "DSPy and litellm are imported only through hypocurate.pipeline.agents.libraries, which first sets LITELLM_MODE=PRODUCTION (litellm otherwise reads a .env file at import: the file guard caught it reading the repository's .env) and LITELLM_LOCAL_MODEL_COST_MAP=True (no price map fetched over the network), then turns off litellm's retries and DSPy's caches. The guarded process drops import-path entries that do not exist before installing the file guard (owner, 2026-10-06), so importing the libraries logs no refusal while the tripwire still watches them.",
 "value": {
  "text": "LITELLM_MODE=PRODUCTION; no retries; no caches",
  "unit": null
 },
 "category": "operational",
 "affects": "What the agent libraries may read or fetch; the guarded process.",
 "reason": "The file guard caught litellm reading .env; the owner chose to keep the libraries under the tripwire (no PRELOADED change).",
 "evidence": [
  "Step 8a milestone 1 (2026-10-06); owner's decision on the guarded runner."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.libraries:LIBRARY_ENVIRONMENT",
    "equals": {
     "LITELLM_MODE": "PRODUCTION",
     "LITELLM_LOCAL_MODEL_COST_MAP": "True"
    }
   },
   {
    "ref": "python:hypocurate.access.guarded:existing_path_entries"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [],
 "tests": [
  "tests/test_agent_libraries.py::test_the_agent_libraries_import_under_the_guard_with_no_refusal",
  "tests/test_agent_libraries.py::test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard",
  "tests/test_agent_libraries.py::test_the_libraries_never_read_a_dotenv_file_outside_the_guard",
  "tests/test_agent_libraries.py::test_only_the_libraries_module_imports_dspy_or_litellm"
 ]
}
```
### New: `temperature_bands`

```json
{
 "key": "temperature_bands",
 "name": "Plans for other temperature bands",
 "state": "in_force",
 "statement": "One band per plan: room temperature, elevated or cryogenic. A plan for elevated or cryogenic names the claim's temperature range in its rules (temperature_range: min and max), above room temperature for elevated and below it for cryogenic; a room-temperature plan names none (the room-temperature rule is unchanged). Under such a plan, eligibility rule 3 lets the range decide a reported temperature (inside: in scope; outside: out of scope); a band alone, with no number, is 'scope not confirmed' when it is the plan's band and out of scope otherwise. Test-condition tags: 'elevated temperature' and 'cryogenic' (seeded by migration 0002).",
 "value": {
  "text": "room temperature, elevated, cryogenic; a range for the last two",
  "unit": null
 },
 "category": "scientific",
 "affects": "Which claims can be planned (criterion 14.3: BCC alloys at 1000 °C) and the scope of their records. The reference plan is unchanged.",
 "reason": "Criterion 14.3's claim at 1000 °C had no valid plan under the room-temperature-only template.",
 "evidence": [
  "Owner, step 8a plan, Q4 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.profile:SUPPORTED_BANDS",
    "equals": [
     "room temperature",
     "elevated",
     "cryogenic"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.plan:RANGE_RULE",
    "equals": "temperature_range"
   },
   {
    "ref": "python:hypocurate.pipeline.profile:TEST_CONDITION_TAGS"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [
  "Not reviewed by an expert: whether a band without a number should be 'scope not confirmed' is for Prof. El-Awady."
 ],
 "tests": [
  "tests/test_temperature_range.py::test_the_reference_plan_is_unchanged",
  "tests/test_temperature_range.py::test_a_plan_for_another_band_names_its_range",
  "tests/test_temperature_range.py::test_invalid_temperature_plans_are_refused",
  "tests/test_temperature_range.py::test_rule_3_under_an_elevated_plan",
  "tests/test_temperature_range.py::test_rule_3_under_a_room_temperature_plan_is_unchanged"
 ]
}
```
### Changed: `tamu_microstructure` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "tamu_microstructure",
 "name": "Texas A&M microstructure",
 "state": "in_force",
 "statement": "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source does not state it explicitly as a result.",
 "value": {
  "text": "single-phase FCC (assigned by decision)",
  "unit": null
 },
 "category": "scientific",
 "affects": "Whether the 94 Texas A&M records fall inside a single-phase FCC scope; with them, the pooled reference result (PRD 14.1a).",
 "reason": "The authors describe their measured compositions as single-phase FCC, the alloys were selected under an FCC phase-stability constraint, and their phase constitution was checked by X-ray diffraction.",
 "evidence": [
  "ArroyaveLab/2026-mulukutla-hall-petch@11390ee5 paper/main.tex line 138: \"The 81 compositions measured here carry all three, under one processing route and one characterization protocol. This is the largest such set reported for single-phase FCC multi-principal element alloys, and it lets composition, processing and grain size be separated without correcting across studies.\"",
  "paper/main.tex line 173: \"It explored composition under an FCC phase stability constraint while holding processing fixed.\" (BB campaign); paper/supplementary.tex line 61: \"It explored the Al--Co--Cr--Cu--Fe--Mn--Ni--V system under an FCC phase-stability constraint while holding processing fixed.\"",
  "paper/main.tex line 175: \"Candidate alloys were iteratively selected from an FCC-constrained, manufacturable design space with the models updated after each iteration using the newly acquired data.\" (CB campaign)",
  "paper/main.tex line 177: \"Energy-dispersive X-ray spectroscopy (EDS) and X-ray diffraction were used to check realized chemistry and phase constitution, while electron microscopy and EBSD documented the microstructure.\"; paper/supplementary.tex line 65: \"EDS and XRD checked realized chemistry and phase constitution; SEM and EBSD documented the microstructure;\"",
  "Step 4b summary, 'Texas A&M phase constitution'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-05"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": "The source-only analysis (reported values and values assigned from source only) shows the result without these records.",
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.adapters.tamu_fcc:MICROSTRUCTURE_DECISION.quote",
    "equals": "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source does not state it explicitly as a result."
   }
  ],
  "note": "Microstructure 'FCC' with status 'assigned_by_decision'."
 },
 "history": [
  {
   "value": "not reported: the source does not state the phases present per record (open decision)",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 4 adapter; open decision in the first step 4b register."
  }
 ],
 "notes": [
  "The paper says 81 compositions; the spreadsheet has 82 distinct compositions.",
  "No passage states the result of the XRD phase check.",
  "Not reviewed by an expert.",
  "Uses the status 'assigned by decision' (see entry 'assigned_value_statuses').",
  "Step 8a (2026-10-06): the Curator proposed 'FCC' as the microstructure from line 173 of paper/main.tex; the owner rejected it (proposal 1): the sentence states the phase class, not a single-phase microstructure as a result. The value stays assigned by decision."
 ],
 "tests": [
  "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
  "tests/test_adapter_tamu.py::test_decision_citations_quote_the_register",
  "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
 ]
}
```
### Changed: `room_temperature_scope` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "room_temperature_scope",
 "name": "Room temperature",
 "state": "in_force",
 "statement": "A room-temperature scope accepts a reported test temperature from 20 to 25 °C; a record with no reported temperature is accepted on the band 'room temperature' held with a status the plan accepts (the Texas A&M band is assigned by decision).",
 "value": {
  "text": "20 to 25",
  "unit": "°C"
 },
 "category": "scientific",
 "affects": "Which records are in scope for a room-temperature claim.",
 "reason": "The reference script's scope.",
 "evidence": [
  "docs/reference/worked_example.py: d['T'].between(20, 25)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-05"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.profile:ROOM_TEMPERATURE_C",
    "equals": [
     20.0,
     25.0
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A room-temperature scope accepts reported test temperatures from 20 to 25 °C.",
   "from": "2026-10-04",
   "to": "2026-10-05",
   "note": "Step 4b wording; the band rule added in step 6 (owner's requirement: the scope accepts the assigned band)."
  }
 ],
 "notes": [
  "How a record with an assigned room-temperature band (decision 'tamu_test_temperature') passes this scope is defined in step 6.",
  "Step 8a (owner, 2026-10-06, Q4): plans may name another band (elevated or cryogenic) with the claim's temperature range; this rule holds for room-temperature plans unchanged (entry 'temperature_bands')."
 ],
 "tests": [
  "tests/test_eligibility.py::test_each_rule_on_its_own",
  "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
  "tests/test_eligibility.py::test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them",
  "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139",
  "tests/test_temperature_range.py::test_rule_3_under_a_room_temperature_plan_is_unchanged"
 ]
}
```
### Changed: `tamu_test_type` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "tamu_test_type",
 "name": "Texas A&M test type",
 "state": "in_force",
 "statement": "The Texas A&M yield strengths are from tensile tests, assigned from source. From step 8a the value comes from the source version's sealed curation: the Curator proposed it with the sentence on line 177 of paper/main.tex, which the checks found, and the owner accepted it (proposal 5, 2026-10-06); the adapter no longer assigns it.",
 "value": {
  "text": "tension (assigned from source)",
  "unit": null
 },
 "category": "scientific",
 "affects": "Whether the Texas A&M records pass a tension-only rule.",
 "reason": "The paper states it explicitly.",
 "evidence": [
  "paper/main.tex line 177: \"Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.\"",
  "paper/supplementary.tex line 65."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.curation_file",
    "equals": "curation.json"
   },
   {
    "ref": "file:data/sources/tamu_fcc/curation.json:\"value\": \"tension\""
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "The Texas A&M yield strengths are from tensile tests, assigned from source.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Steps 4-7b: assigned by the adapter itself (version 2), citing the same sentence."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
  "tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable",
  "tests/test_frozen_sources.py::test_the_curation_file_records_the_owners_decisions",
  "tests/test_source_versions.py::test_registering_the_frozen_curation_reproduces_the_sealed_curated_version"
 ]
}
```
### Changed: `tamu_phase_class` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "tamu_phase_class",
 "name": "Texas A&M phase class",
 "state": "in_force",
 "statement": "The Texas A&M records are FCC, assigned from source. This is the phase class, not 'single-phase'. From step 8a the value comes from the source version's sealed curation: the Curator proposed it with the sentence on line 173 of paper/main.tex, which the checks found, and the owner accepted it (proposal 2, 2026-10-06); the adapter no longer assigns it. The Curator's proposal of the same sentence as a single-phase microstructure was rejected by the owner (proposal 1): the microstructure stays assigned by decision (entry 'tamu_microstructure').",
 "value": {
  "text": "FCC (assigned from source)",
  "unit": null
 },
 "category": "scientific",
 "affects": "The alloy-class description of the Texas A&M records.",
 "reason": "The paper states it explicitly.",
 "evidence": [
  "paper/main.tex line 173: \"The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.\""
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.curation_file",
    "equals": "curation.json"
   },
   {
    "ref": "file:data/sources/tamu_fcc/curation.json:\"value\": \"FCC\""
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "The Texas A&M records are FCC, assigned from source. This is the phase class, not 'single-phase'.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Steps 4-7b: assigned by the adapter itself (version 2), citing the same sentence."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
  "tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable",
  "tests/test_frozen_sources.py::test_the_curation_file_records_the_owners_decisions"
 ]
}
```
### Changed: `spending_caps` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction (the run's lock for a run call, then one month-wide advisory lock) that records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. The monthly cap counts the calls recorded in this database only.",
 "value": {
  "text": "$2 per run; $2 per curation; $50 per month",
  "unit": "USD"
 },
 "category": "operational",
 "affects": "Whether a run or a model call may proceed.",
 "reason": "CLAUDE.md, rule 12.",
 "evidence": [
  "CLAUDE.md, rule 12; step 3 summary, 'Step 9 requirements'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.spend:RUN_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:CURATION_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:MONTH_CAP_USD",
    "equals": 50
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Model calls may cost at most $2 per run and $50 per calendar month (UTC), counting calls without a reported cost at their upper bound.",
   "from": "2026-10-04",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): the per-curation cap and the enforcement before each request."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_agent_core.py::test_the_run_cap_refuses_a_request_before_it_is_sent",
  "tests/test_agent_core.py::test_the_curation_cap_and_a_ceiling_refuse_before_sending",
  "tests/test_agent_core.py::test_the_month_cap_counts_every_call_including_unconfirmed_ones",
  "tests/test_agent_core.py::test_two_reservations_cannot_both_pass_the_month_cap",
  "tests/test_agent_core.py::test_a_reservation_waits_for_the_month_wide_lock"
 ]
}
```
### Changed: `access_allow_lists` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "access_allow_lists",
 "name": "Allowed fields per role and stage",
 "state": "in_force",
 "statement": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Critic between the lock and the freeze; the Analyst after the freeze, or after a run ended without a freeze (gap report); the Commentator after completion. The Curator receives nothing at any run stage: it reads one sealed source version when that version is registered (stage 'registration', no run), and then only that version's documentation and the fields it may propose values for (step 8a). On a run completed with no dataset frozen, the Commentator receives only what the Analyst received for the gap report, plus the Analyst's gap report and the run's outcome: no outcome values and no row-level records. Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope), or for the Curator only its invocation's source version. Every read and every refusal is logged.",
 "value": {
  "text": "the table in hypocurate/access/allowlist.py (ALLOWED)",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Everything an agent can receive (PRD 4), from step 8 on.",
 "reason": "PRD 4 lists what each role can see in general terms; the fields the PRD does not assign (the plan for the Critic, tag lists, coverage, handovers, cost, eligibility decisions, the domain for the Curator) were assigned in the step 5 plan.",
 "evidence": [
  "PRD 4; step 5 plan approved by the owner, 2026-10-05, with additions A (single-run scope) and B (named source fields).",
  "Owner's change before the step 5 review, 2026-10-05: the Commentator on a run with no dataset frozen."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:ALLOWED"
   },
   {
    "ref": "python:hypocurate.access.allowlist:ROLES",
    "equals": [
     "planner",
     "curator",
     "critic",
     "analyst",
     "commentator"
    ]
   },
   {
    "ref": "python:hypocurate.access.allowlist:STAGES",
    "equals": [
     "none",
     "before_lock",
     "curation",
     "analysis",
     "closed_without_freeze",
     "final",
     "final_without_freeze",
     "registration"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "On a completed run, the Commentator received the Analyst's post-freeze fields (including every stored record with its outcome values) whether or not a dataset was frozen, plus the gap-report summaries.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 first build; changed by the owner before the review."
  },
  {
   "value": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Curator and the Critic between the lock and the freeze; the Analyst after the freeze, or after a run ended without a freeze (gap report); the Commentator after completion. On a run completed with no dataset frozen, the Commentator receives only what the Analyst received for the gap report, plus the Analyst's gap report and the run's outcome: no outcome values and no row-level records. Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope). Every read and every refusal is logged.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06, Q2): the Curator moved from the curation stage (its own source's data files and the fields to extract) to registration."
  }
 ],
 "notes": [
  "Two fields are reference lists, not run data: the confirmed domain and the approved tag values (without the run that proposed them)."
 ],
 "tests": [
  "tests/test_access_layer.py::test_the_allow_list_matches_the_owners_table",
  "tests/test_access_layer.py::test_each_role_gets_exactly_its_fields_and_every_refusal_is_logged",
  "tests/test_access_projected.py::test_nothing_from_another_run_reaches_any_role",
  "tests/test_access_layer.py::test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome",
  "tests/test_access_projected.py::test_no_projected_planted_value_in_the_commentators_input_without_a_freeze",
  "tests/test_access_layer.py::test_the_curator_has_nothing_in_any_run"
 ]
}
```
### Changed: `plan_named_parts` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "plan_named_parts",
 "name": "The plan's schema",
 "state": "in_force",
 "statement": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule. Step 7 adds the 'calibration' part (both methods, the number of simulations, the fixed scatter and shift, the estimation method and the smallest effect).",
 "value": {
  "text": "PLAN_SCHEMA (nested, named keys and vocabulary leaves)",
  "unit": null
 },
 "category": "data_handling",
 "affects": "What any role receives of a plan; the plan model (step 6) stores its content under these names.",
 "reason": "Allowed fields, not blocked fields (PRD 4).",
 "evidence": [
  "PRD 5.1; step 5 plan, point 9 (approved by the owner, 2026-10-05).",
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-05"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:PLAN_SCHEMA"
   },
   {
    "ref": "python:hypocurate.access.allowlist:POWER_SCHEMA"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A plan's content is read only under its named parts (PRD 5.1): claim, hypothesis version, variables, scope, model, sufficiency, fields to extract, exclusion rules, eligibility rules, verdict statement, sensitivity analyses. Any other key is withheld from every role. The list of fields to extract keeps only names of the common fields.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 first build; changed after the second-model review."
  },
  {
   "value": "A plan's content is read only through PLAN_SCHEMA, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped. Power assumptions likewise through POWER_SCHEMA, and the sensitivity keys through their vocabulary. Defined in step 5 (owner, 2026-10-05); the plan model of step 6 must follow it.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 wording; extended by the owner in step 6 planning (2026-10-05)."
  },
  {
   "value": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 7 (owner, 2026-10-05)."
  }
 ],
 "notes": [
  "Step 6 must store the plan's content in this schema; a change to the schema is a register change needing the owner's approval.",
  "Step 8a (2026-10-06): the step 5 Curator test named here was replaced (the Curator no longer reads the plan's fields to extract); the plan's projection is still covered by the other named tests."
 ],
 "tests": [
  "tests/test_access_layer.py::test_the_plan_is_projected_by_its_named_parts",
  "tests/test_eligibility.py::test_decisions_ignore_the_domain_profile",
  "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
  "tests/test_plan.py::test_invalid_plans_are_refused",
  "tests/test_plan.py::test_the_default_plan_is_valid_and_is_its_own_projection",
  "tests/test_statistics.py::test_an_invalid_calibration_part_is_refused_at_the_lock"
 ]
}
```
### Changed: `pipeline_file_guard` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "pipeline_file_guard",
 "name": "Approved input files of pipeline code",
 "state": "in_force",
 "statement": "A tripwire against accidental file access by trusted pipeline code, not a sandbox. Each pipeline run executes in a fresh process (python -m hypocurate.access.guarded) where a Python audit hook refuses reading or listing anything outside the Python installation and the package's code, writing outside a private scratch directory, relative paths, other programs and new native libraries; each refusal is logged (audit log as a failure, or the process log). It does not stop code that tries to get around it: Python warns that audit hooks are unsuitable for a sandbox, and open descriptors, the guard's own state, preloaded ctypes (direct memory access), sockets and the database are not restricted. The only construction-level guarantee is that the deployed image contains no tests/ or docs/.",
 "value": {
  "text": "tripwire: reads limited to the Python installation and package code; writes to a private scratch directory",
  "unit": null
 },
 "category": "operational",
 "affects": "Every pipeline run (the command line's run command, step 8; the worker, step 9).",
 "reason": "Answer material and review documents should not be reached by accident (step 1 open item 4). The owner's first instruction asked for 'unreachable by construction'; after the step 5 review the owner scoped this to a tripwire against our own mistakes, with the deployed image (no tests/, no docs/) as the only construction-level guarantee.",
 "evidence": [
  "Step 1 summary, open item 4; step 5 plan and owner's addition C, 2026-10-05.",
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-05"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.file_guard:GUARDED_MAIN",
    "equals": "hypocurate.access.guarded"
   },
   {
    "ref": "python:hypocurate.access.file_guard:SCRATCH_PREFIX",
    "equals": "hc-run-"
   },
   {
    "ref": "python:hypocurate.access.guarded:PRELOADED",
    "equals": [
     "psycopg"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A pipeline run executes in a fresh process (python -m hypocurate.access.guarded) under an irreversible guard: it may read only the Python installation and the package's code, and write only in a private scratch directory (an empty, 0700 hc-run-* directory in the system temporary directory, removed afterwards). tests/, docs/, data/ and the repository root cannot be read or listed; other programs and native code through ctypes are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. The database driver is imported before the guard is installed.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 first build; changed after the second-model review."
  }
 ],
 "notes": [
  "Python documentation, sys.addaudithook and PEP 578: audit hooks are not suitable for implementing a sandbox.",
  "Sufficient under the threat model (entry 'threat_model'): only trusted code runs; agents return text only.",
  "A library that imports ctypes after the guard is installed is refused; such a library (for example the plotting library, step 7) must be added to PRELOADED with the owner's approval.",
  "Step 8a (owner, 2026-10-06): the guarded process drops import-path entries that do not exist before installing the guard, so importing the agent libraries logs no refusal; a planted .env read by a library is still refused (entry 'model_call_libraries')."
 ],
 "tests": [
  "tests/test_access_files.py::test_answers_reviews_data_and_the_repository_root_cannot_be_read",
  "tests/test_access_files.py::test_writes_outside_the_scratch_directory_are_refused",
  "tests/test_access_files.py::test_templates_database_and_certificates_work_under_the_guard",
  "tests/test_access_files.py::test_source_registration_cannot_run_under_the_guard",
  "tests/test_access_files.py::test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else",
  "tests/test_access_layer.py::test_the_guard_is_installed_in_one_place",
  "tests/test_access_files.py::test_preloaded_ctypes_still_works_a_documented_limit",
  "tests/test_access_dispatch.py::test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log",
  "tests/test_check_runtime_image.py::test_clean_image_passes",
  "tests/test_access_dispatch.py::test_a_refusal_followed_by_a_timeout_is_still_logged",
  "tests/test_agent_libraries.py::test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard",
  "tests/test_agent_libraries.py::test_missing_path_entries_are_dropped_and_the_others_kept"
 ]
}
```
### Changed: `access_context_dispatcher` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "access_context_dispatcher",
 "name": "Access objects come only from the dispatcher",
 "state": "in_force",
 "statement": "An access object is created only by the trusted dispatcher, around an immutable context captured once: hypocurate.access.dispatch.bind(run, agent setting) reads the role from the run's recorded agent settings and the stage from the database, and binds no run role to a source; hypocurate.access.dispatch.bind_invocation(invocation) (step 8a) reads run or source version, role and agent setting from one invocation record (agent_invocation), so a call's run, setting and source are never assembled separately, and binds a registration invocation to the one sealed source version it names. There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
 "value": {
  "text": "dispatch.bind only",
  "unit": null
 },
 "category": "operational",
 "affects": "Every agent read (steps 8 and 9).",
 "reason": "Review finding 2: caller-chosen, mutable role, run, stage and source could be misused by our own code.",
 "evidence": [
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.dispatch:bind"
   },
   {
    "ref": "python:hypocurate.access.dispatch:bind_invocation"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "An access object is created only by hypocurate.access.dispatch.bind(run, agent setting, source), around an immutable context captured once: the role is read from the run's recorded agent settings, the stage from the database, and a Curator's source must be one of the run's run_source rows. There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): one invocation record per agent call (step 5 re-check); the Curator binds at registration, not to a run's source."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_access_dispatch.py::test_bind_refuses_a_setting_or_source_the_run_did_not_record",
  "tests/test_access_dispatch.py::test_an_access_object_has_no_public_constructor_and_cannot_be_changed"
 ]
}
```
### Changed: `access_logging` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "access_logging",
 "name": "What the audit log records, and its fallback",
 "state": "in_force",
 "statement": "Every read, policy denial and access failure is logged: detail.result is 'allowed', 'denied' (a policy refusal, with a fixed code) or 'failed' (unknown run, unknown invocation, lock timeout, reader error, database error, file-guard refusal). Only validated, bounded strings are logged; anything not one of ours is 'invalid' with its length. A role's whole input is read and logged in one transaction. If a failure cannot be written to the database, it goes to the process log (logger hypocurate.access); durable logging in the database is not unconditional. The original error of a failure (a reader's exception, the database's error) is kept, with its traceback, in the process log only; the error raised to the caller carries nothing of it (no cause, no context, no text). A file-guard refusal is still logged when the guarded process then times out. A registration read (step 8a) is logged with no run, naming the source version and the invocation.",
 "value": {
  "text": "allowed / denied / failed; process log as fallback",
  "unit": null
 },
 "category": "operational",
 "affects": "The audit log of every run (PRD 14.2).",
 "reason": "Review finding 5.",
 "evidence": [
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md.",
  "Step 5 re-check (ChatGPT, 2026-10-05): docs/reviews/step05_recheck_chatgpt.md, finding 5."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.layer:FAILURES",
    "equals": [
     "unknown_run",
     "unknown_invocation",
     "lock_timeout",
     "reader_error",
     "database_error",
     "file_guard"
    ]
   },
   {
    "ref": "python:hypocurate.access.layer:DENIALS"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Every read, policy denial and access failure is logged: detail.result is 'allowed', 'denied' (a policy refusal, with a fixed code) or 'failed' (unknown run, lock timeout, reader error, database error, file-guard refusal). Only validated, bounded strings are logged; anything not one of ours is 'invalid' with its length. A role's whole input is read and logged in one transaction. If a failure cannot be written to the database, it goes to the process log (logger hypocurate.access); durable logging in the database is not unconditional.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Before the step 5 re-check: the error raised was chained to the original."
  },
  {
   "value": "Every read, policy denial and access failure is logged: detail.result is 'allowed', 'denied' (a policy refusal, with a fixed code) or 'failed' (unknown run, lock timeout, reader error, database error, file-guard refusal). Only validated, bounded strings are logged; anything not one of ours is 'invalid' with its length. A role's whole input is read and logged in one transaction. If a failure cannot be written to the database, it goes to the process log (logger hypocurate.access); durable logging in the database is not unconditional. The original error of a failure (a reader's exception, the database's error) is kept, with its traceback, in the process log only; the error raised to the caller carries nothing of it (no cause, no context, no text). A file-guard refusal is still logged when the guarded process then times out.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): the failure 'unknown invocation' and registration reads."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_access_dispatch.py::test_a_readers_error_is_a_logged_failure",
  "tests/test_access_dispatch.py::test_an_unknown_run_is_a_logged_failure",
  "tests/test_access_dispatch.py::test_when_the_database_is_unavailable_the_process_log_is_the_fallback",
  "tests/test_access_dispatch.py::test_role_input_is_never_silently_empty",
  "tests/test_access_dispatch.py::test_only_validated_bounded_strings_are_logged",
  "tests/test_access_dispatch.py::test_a_roles_whole_input_is_read_in_one_transaction",
  "tests/test_access_dispatch.py::test_a_reader_failure_carries_nothing_of_the_original_error",
  "tests/test_access_dispatch.py::test_a_database_failure_carries_nothing_of_the_original_error",
  "tests/test_access_dispatch.py::test_a_refusal_followed_by_a_timeout_is_still_logged",
  "tests/test_access_dispatch.py::test_a_timeout_with_stderr_as_bytes_is_still_reported"
 ]
}
```
### Changed: `code_vocabularies` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "code_vocabularies",
 "name": "Vocabularies of codes our own code writes",
 "state": "in_force",
 "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase), and the calibration and estimation methods (step 7) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
 "value": {
  "text": "flag kinds, flag categories, eligibility rules, sensitivity keys, plan rule codes",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Flags (step 6), eligibility decisions (step 6), sensitivity analyses (step 7) as roles see them.",
 "reason": "Review finding 3: stored codes are text and could carry anything.",
 "evidence": [
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.vocabulary:FLAG_KINDS",
    "equals": [
     "exact_duplicate",
     "invalid_value",
     "model_recalled",
     "out_of_scope",
     "possible_duplicate",
     "scope_not_confirmed",
     "values_disagree"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:FLAG_CATEGORIES",
    "equals": [
     "differ beyond tolerance",
     "identical values",
     "outside scope",
     "physically impossible",
     "scope not confirmed",
     "several candidates",
     "within tolerance"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:ELIGIBILITY_RULES",
    "equals": [
     "conflict_unresolved",
     "duplicate_counted_once",
     "excluded_by_rule",
     "group_unknown",
     "identity_unresolved",
     "in_scope",
     "invalid_value",
     "missing_value",
     "model_recalled",
     "most_influential_paper",
     "out_of_scope",
     "scope_not_confirmed",
     "single_grain_size"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:SENSITIVITY_KEYS",
    "equals": [
     "conflicts_survivor_value",
     "no_exclusions",
     "possible_duplicates_separate",
     "removal_after_lock",
     "same_alloy_1_at_pct",
     "scope_not_confirmed_included",
     "six_batches_as_groups",
     "source_only_assignments",
     "tension_and_compression",
     "without_most_influential_paper"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:SOURCE_KEYS",
    "equals": [
     "controlled_duplicates",
     "mpea",
     "tamu_fcc"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:GROUPING_UNITS",
    "equals": [
     "batch",
     "dataset",
     "paper"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:VALUE_STATUSES",
    "equals": [
     "assigned_by_decision",
     "assigned_from_source",
     "converted"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:PROFILE_NAMES",
    "equals": [
     "grain_size_strengthening"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:SINGLE_PHASE",
    "equals": [
     "not_required",
     "required"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:CALIBRATION_METHODS",
    "equals": [
     "estimated",
     "fixed"
    ]
   },
   {
    "ref": "python:hypocurate.access.vocabulary:ESTIMATION_METHODS",
    "equals": [
     "henderson_iii"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "flag categories without 'several candidates'; eligibility rules without 'missing_value', 'identity_unresolved', 'conflict_unresolved'; sensitivity keys without 'no_exclusions', 'conflicts_survivor_value'; no plan rule codes",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5. Step 6 additions approved by the owner on 2026-10-05 (planning, questions 3, 5, 6, 9 and decision C)."
  },
  {
   "value": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 7 (owner, 2026-10-05)."
  },
  {
   "value": "eligibility rules without 'group_unknown' and 'most_influential_paper'; sensitivity keys without 'without_most_influential_paper'",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 7b additions approved by the owner on 2026-10-06."
  }
 ],
 "notes": [
  "Step 8a (owner, 2026-10-06): vocabulary.CURATION_TARGETS names the fields the Curator may propose values for, each with its vocabulary or unit (entry 'curator_tabular_sources'); the curation refusal codes are in sources/curation.py (CODES) and pipeline/agents/curator.py, the request failure codes in pipeline/agents/lm.py (FAILURES)."
 ],
 "tests": [
  "tests/test_access_layer.py::test_flags_kind_has_no_numbers",
  "tests/test_access_dispatch.py::test_the_gap_report_input_has_codes_not_failure_text"
 ]
}
```
### Changed: `curator_tabular_sources` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "curator_tabular_sources",
 "name": "The Curator's role for tabular sources",
 "state": "in_force",
 "statement": "The Curator does not extract tabular records: adapters (code) do. It runs when a source version is registered, never in a run, and only for a source grouped by dataset (a source grouped by paper, a compilation, is refused: a value for the whole source would be a guess for each paper). It reads that version's documentation and proposes, for the fields a table may lack (test type, phase class, test temperature or band, microstructure), one value that holds for all the source's measurements with the exact sentence it relied on, or 'not stated'. Code checks each proposal (entry 'curator_quote_checks'); a person accepts or rejects it (entry 'curation_acceptance'). It is not told any claim, plan or data row.",
 "value": {
  "text": "registration only; single-dataset sources; proposals accepted by a person",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Record extraction from step 8; which records count as extracted by an agent.",
 "reason": "Step 6 stores records by adapter code and does not settle the Curator's role.",
 "evidence": [
  "Owner, step 6 planning (2026-10-05)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-06"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.curation:curate"
   },
   {
    "ref": "python:hypocurate.access.allowlist:ALLOWED.curator.registration",
    "equals": [
     "curation_targets",
     "source_documentation"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Open: what the Curator agent does for tabular sources, whose records the adapters (code) extract in step 6.",
   "from": "2026-10-06",
   "to": "2026-10-06",
   "note": "Open until step 8a; decided by the owner in the step 8a plan (Q2, Q3)."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_curator.py::test_a_compilation_source_is_never_curated",
  "tests/test_access_curator.py::test_the_curators_complete_input_is_its_versions_documentation_and_the_targets",
  "tests/test_curator.py::test_no_planted_value_and_no_claim_reaches_the_curator"
 ]
}
```
### `data/manifest.json` (diff)

```diff
diff --git a/data/manifest.json b/data/manifest.json
index bd71df2..91091c1 100644
--- a/data/manifest.json
+++ b/data/manifest.json
@@ -27,6 +27,18 @@
           "sha256": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
           "bytes": 11357
         }
+      ],
+      "documentation": [
+        {
+          "path": "data/sources/mpea/documentation/Borg2020_PMC7722748.xml",
+          "role": "documentation: the dataset paper's full text (JATS XML, Europe PMC); frozen for later work, not curated in sprint 1 (a compilation grouped by paper)",
+          "origin_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7722748/fullTextXML",
+          "pmcid": "PMC7722748",
+          "licence": "CC-BY-4.0 (the article; stated in its <license> element)",
+          "retrieved": "2026-10-06",
+          "sha256": "ef21ae6085f5444b534ee2ef7137542f63e3b80fc3940219a3960b642f5a1550",
+          "bytes": 63254
+        }
       ]
     },
     "tamu_fcc": {
@@ -73,6 +85,34 @@
           "sha256": "917035f0704dbb979bd157a7f8d814f5e7c32d28aedba41986443298dea5b98b",
           "bytes": 1119
         }
+      ],
+      "documentation": [
+        {
+          "path": "data/sources/tamu_fcc/documentation/main.tex",
+          "role": "documentation: the paper's main text (LaTeX), read by the Curator (step 8a)",
+          "archive_member": "paper/main.tex",
+          "origin_url": "https://raw.githubusercontent.com/ArroyaveLab/2026-mulukutla-hall-petch/11390ee516c1a17cacdde318b40d5d6889d4007f/paper/main.tex",
+          "sha256": "81fb864c1463573adbfc2272c79287c2c71649e7a6e3024ca927bb221836038e",
+          "bytes": 76524
+        },
+        {
+          "path": "data/sources/tamu_fcc/documentation/supplementary.tex",
+          "role": "documentation: the paper's supplementary text (LaTeX), read by the Curator (step 8a)",
+          "archive_member": "paper/supplementary.tex",
+          "origin_url": "https://raw.githubusercontent.com/ArroyaveLab/2026-mulukutla-hall-petch/11390ee516c1a17cacdde318b40d5d6889d4007f/paper/supplementary.tex",
+          "sha256": "8dfe9731af618937c6686da5d63b8e0decc220c591e1831060cd10d447461317",
+          "bytes": 65359
+        }
+      ],
+      "curation": [
+        {
+          "path": "data/sources/tamu_fcc/curation.json",
+          "role": "curation: the Curator's proposals accepted by the owner (step 8a), exported by `hypocurate sources export-curation tamu_fcc` from the sealed curated version",
+          "origin": "curated version of base fingerprint c25b31743b28c5483e53a0a0569f6e78ac35873347cd83843eeffc5fb36ca050 (local development database, 2026-10-06); one Curator call (claude-sonnet-5-5, settings version 1); proposals 5 and 2 accepted, 1 rejected by Khalid El-Awady",
+          "built": "2026-10-06",
+          "sha256": "2a6cbf0124901df611d9f41760ad8e96d58acf20d343947f587d88f926dde69c",
+          "bytes": 1272
+        }
       ]
     }
   },
```
### Files added under `data/`

```
 data/manifest.json                                 |  40 +
 .../mpea/documentation/Borg2020_PMC7722748.xml     |   1 +
 data/sources/tamu_fcc/curation.json                |  36 +
 data/sources/tamu_fcc/documentation/main.tex       | 612 +++++++++++++++
 .../tamu_fcc/documentation/supplementary.tex       | 846 +++++++++++++++++++++
 5 files changed, 1535 insertions(+)
```
### `data/sources/tamu_fcc/curation.json`

```json
{
  "base_version": {
    "fingerprint": "c25b31743b28c5483e53a0a0569f6e78ac35873347cd83843eeffc5fb36ca050",
    "label": "v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f"
  },
  "format": 1,
  "source": "tamu_fcc",
  "values": {
    "phase_class": {
      "accepted_at": "2026-10-06T23:17:37.483039+00:00",
      "accepted_by": "Khalid El-Awady",
      "agent_setting_version": 1,
      "document": "documentation/main.tex",
      "line": 173,
      "model": "claude-sonnet-5-5",
      "note": "Owner's decision in the step 8a session, 2026-10-06",
      "proposal": 2,
      "quote": "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.",
      "term": "FCC",
      "value": "FCC"
    },
    "test_type": {
      "accepted_at": "2026-10-06T23:17:06.989007+00:00",
      "accepted_by": "Khalid El-Awady",
      "agent_setting_version": 1,
      "document": "documentation/main.tex",
      "line": 177,
      "model": "claude-sonnet-5-5",
      "note": "Owner's decision in the step 8a session, 2026-10-06",
      "proposal": 5,
      "quote": "Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.",
      "term": "tensile",
      "value": "tension"
    }
  }
}
```

## 6. Reference comparison with `main`

The five runs of `tests/test_reference_numbers.py` were dumped on `main` (a separate checkout of `cd2b3be`) and on this branch (after milestone 8: adapter version 3 with the frozen curation), then compared leaf by leaf. Scripts in section 11.

### Comparison output

```
differing leaves by name: {'ci_high': 99, 'ci_low': 99, 'share': 99, 'significant': 99, 'seed': 66, 'detection': 34, 'detection_ci': 68, 'false_positive': 65, 'false_positive_ci': 130, 'estimated_power_estimated_noise': 32, 'estimated_power': 2, 'freeze_fingerprint': 5, 'rss_full': 6, 'scatter': 10, 'scatter_squared': 6, 'shift': 16, 'shift_squared_untruncated': 9, 'trace': 4, 'estimate': 3, 'p_value': 4, 'std_error': 4, 't': 4, 'rss_reduced': 1, 'records_found': 189}
max relative difference of estimate, standard error, p, t: 8.685492656737593e-15
   .reference.analyses[4].estimate 428.02404949610104 -> 428.024049496101
   .reference.analyses[4].p_value 7.398407506070927e-07 -> 7.398407506070913e-07
   .reference.analyses[4].std_error 63.51112235023561 -> 63.511122350235595
   .reference.analyses[4].t 6.739355779854411 -> 6.739355779854412
   .reference.analyses[5].p_value 7.511240461762386e-07 -> 7.511240461762399e-07
   .reference.analyses[5].std_error 64.22883580113376 -> 64.22883580113377
   .reference.analyses[5].t 6.615080354343604 -> 6.615080354343602
   .reference.analyses[8].estimate 432.3502268594971 -> 432.35022685949724
   .reference.analyses[8].p_value 6.72368893771935e-07 -> 6.723688937719363e-07
   .reference.analyses[8].std_error 64.86124831533819 -> 64.86124831533822
   .reference.analyses[8].t 6.665770981735118 -> 6.665770981735117
   .reference.analyses[11].estimate 393.50438134761123 -> 393.50438134761134
   .reference.analyses[11].p_value 0.00019348509448671378 -> 0.00019348509448671546
   .reference.analyses[11].std_error 90.487111236234 -> 90.48711123623411
   .reference.analyses[11].t 4.348734045894032 -> 4.3487340458940285
mpea_fixed | run row identical: True | decision keys differing: ['freeze_fingerprint']
mpea_use | run row identical: True | decision keys differing: ['freeze_fingerprint']
reference | run row identical: True | decision keys differing: ['freeze_fingerprint']
tamu_fixed | run row identical: True | decision keys differing: ['freeze_fingerprint']
tamu_use | run row identical: True | decision keys differing: ['freeze_fingerprint']
structural comparisons made (counts, checks, minimums, labels, reasons, df, significance per analysis): 784
pooled on the branch: 97 22 20 74 424.9 64.4 1.3e-06
```
### Calibration, before and after

```
analysis                                     method     no-effect main       8a      z  detect main      8a
pooled                                       fixed              0.0725   0.0845   1.41       1.0000  1.0000
pooled                                       estimated          0.0885   0.0775  -1.26       0.9775  0.9665
per_source:mpea                              fixed              0.0995   0.0830  -1.81       1.0000  1.0000
per_source:mpea                              estimated          0.0800   0.0775  -0.29       0.9595  0.9620
sensitivity:without_most_influential_paper   fixed              0.0750   0.0740  -0.12       0.9995  1.0000
sensitivity:without_most_influential_paper   estimated          0.0790   0.0935   1.63       0.8740  0.8820
flags changed: 0 | max |z| over all computed calibrations: 2.84 of 22
```

## 7. The live curation call (local development database, 2026-10-06)

Command: `hypocurate sources curate tamu_fcc --ceiling 0.50`, run with the owner's key from `.env` (not read or printed). Its output (the command's JSON; no key in it):

```json
{
 "source": "tamu_fcc",
 "version": 1,
 "invocation": 1,
 "attempts": [
  "ok"
 ],
 "calls": [
  1
 ],
 "status": "done",
 "ignored_keys": [],
 "proposals": [
  {
   "id": 1,
   "field": "microstructure",
   "status": "proposed",
   "value": "FCC",
   "quote": "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.",
   "document": "documentation/main.tex",
   "line": 173,
   "term": "FCC",
   "refusal_code": null
  },
  {
   "id": 2,
   "field": "phase_class",
   "status": "proposed",
   "value": "FCC",
   "quote": "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.",
   "document": "documentation/main.tex",
   "line": 173,
   "term": "FCC",
   "refusal_code": null
  },
  {
   "id": 3,
   "field": "test_temperature",
   "status": "not_stated",
   "value": null,
   "quote": null,
   "document": null,
   "line": null,
   "term": null,
   "refusal_code": null
  },
  {
   "id": 4,
   "field": "test_temperature_band",
   "status": "not_stated",
   "value": null,
   "quote": null,
   "document": null,
   "line": null,
   "term": null,
   "refusal_code": null
  },
  {
   "id": 5,
   "field": "test_type",
   "status": "proposed",
   "value": "tension",
   "quote": "Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.",
   "document": "documentation/main.tex",
   "line": 177,
   "term": "tensile",
   "refusal_code": null
  }
 ]
}
```
The recorded call and the decisions:

```
agent_invocation: [{'id': 1, 'scope': 'registration', 'source_version_id': 1, 'role': 'curator', 'agent_setting_id': 1}]
model_call: [{'id': 1, 'invocation_id': 1, 'run_id': None, 'role': 'curator', 'model': 'claude-sonnet-5-5', 'price_table_version': 'anthropic-2026-09-25', 'max_cost': Decimal('0.378166'), 'status': 'succeeded', 'input_tokens': 61537, 'output_tokens': 262, 'cached_tokens': 0, 'cost': Decimal('0.125694'), 'error': None}]
curator_decision: [{'proposal_id': 1, 'decision': 'rejected', 'decided_by': 'Khalid El-Awady', 'note': "Owner's decision in the step 8a session, 2026-10-06: the sentence states the phase class, not a single-phase microstructure as a result; the microstructure stays assigned by decision (register 'tamu_microstructure')."}, {'proposal_id': 2, 'decision': 'accepted', 'decided_by': 'Khalid El-Awady', 'note': "Owner's decision in the step 8a session, 2026-10-06"}, {'proposal_id': 5, 'decision': 'accepted', 'decided_by': 'Khalid El-Awady', 'note': "Owner's decision in the step 8a session, 2026-10-06"}]
source versions: [{'id': 1, 'label': 'v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f', 'fingerprint': 'c25b31743b28c5483e53a0a0569f6e78ac35873347cd83843eeffc5fb36ca050'}, {'id': 2, 'label': 'v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f + curation', 'fingerprint': '2fad3ccb3dbc32c1ec51e6efcb70a9d17d755bfdfa606cb044f458bd2b37b982'}]
audit (bind and reads of the curation): [{'run_id': None, 'role': 'curator', 'stage': 'registration', 'function': 'bind', 'allowed': True, 'result': 'allowed'}, {'run_id': None, 'role': 'curator', 'stage': 'registration', 'function': 'curation_targets', 'allowed': True, 'result': 'allowed'}, {'run_id': None, 'role': 'curator', 'stage': 'registration', 'function': 'source_documentation', 'allowed': True, 'result': 'allowed'}]
```

## 8. Mutation checks (all re-run on the final tests)

Each mutation is applied to a scratch copy of the package (`data/` and `tests/` linked, `PYTHONPATH` to the copy, run from outside the repository, the import checked) and the named tests are run. The specs are in section 11.

```
control (no change): 112 passed, 1 warning in 44.57s
g01: 1 failed, 4 passed in 15.97s
g02: 3 failed, 2 passed in 6.65s
g03: 2 failed, 3 passed in 16.60s
d01: 3 failed, 199 passed in 50.95s
d02: 2 failed, 200 passed in 50.43s
d03: 2 failed, 200 passed in 50.95s
d04: 1 failed, 201 passed in 50.27s
d05: 1 failed, 201 passed in 50.50s
d06: 1 failed, 201 passed in 50.03s
d07: 1 failed, 201 passed in 50.32s
d08: 1 failed, 201 passed in 50.70s
a01: 1 failed, 74 passed in 52.94s
a02: 1 failed, 74 passed in 53.27s
a03: 4 failed, 71 passed in 52.25s
a04: 1 failed, 74 passed in 53.49s
a05: 2 failed, 73 passed in 52.94s
c01: 1 failed, 28 passed, 1 warning in 30.66s
c02: 1 failed, 28 passed, 1 warning in 28.73s
c03: 7 failed, 22 passed, 1 warning in 29.05s
c04: 2 failed, 27 passed, 1 warning in 30.51s
c05: 2 failed, 27 passed, 1 warning in 30.91s
c06: 1 failed, 28 passed, 1 warning in 30.48s
c07: 1 failed, 28 passed, 1 warning in 30.34s
c08: 1 failed, 28 passed, 1 warning in 30.19s
c09: 2 failed, 27 passed, 1 warning in 30.49s
c10: 2 failed, 27 passed, 1 warning in 30.41s
u01: 1 failed, 19 passed in 19.51s
u02: 2 failed, 18 passed in 19.26s
u03: 1 failed, 19 passed in 19.23s
u04: 1 failed, 19 passed in 19.07s
u05: 1 failed, 19 passed in 19.21s
u06: 1 failed, 19 passed in 19.13s
u07: 1 failed, 19 passed in 18.91s
t01: 1 failed, 62 passed in 1.82s
t02: 1 failed, 62 passed in 1.37s
t03: 1 failed, 62 passed in 1.29s
t04: 5 failed, 58 passed in 1.28s
t05: 5 failed, 58 passed in 1.24s
t06: 1 failed, 62 passed in 1.23s
```

## 9. The new tests on `main`'s code

The new test files run against `main`'s package (a checkout of `cd2b3be`), with this branch's tests and data:

```
test_agent_libraries: 4 failed, 1 passed in 1.96s
test_migrations_step8a: 1 error in 0.51s
test_access_curator: 1 error in 0.48s
test_agent_core: 1 error in 0.21s
test_curator: 1 error in 0.39s
test_temperature_range: 17 failed, 10 passed in 1.18s

Reading: the four files with "1 error" cannot be collected on main: the modules or tables they test (migration 0005,
bind_invocation and the registration stage, pipeline/agents, sources/curation) do not exist there, so every one of their
tests fails. test_agent_libraries: the one that passes is the import scan, a guard by design (nothing imports dspy or
litellm on main). test_temperature_range: the 10 that pass are the 9 guards that pin the room-temperature behaviour and the
test pinning the reference plan's fingerprint to main's value (it must pass on main).
```

## 10. Suite

### Locally

```
1342 passed, 1 warning in 409.36s (0:06:49)
```
### In the rebuilt test image

```
1342 passed, 1 warning in 448.96s (0:07:28)
```

## 11. Scripts

### `mutate2.sh`

```
#!/bin/bash
# usage: mutate2.sh <name> <spec.json> -- <pytest args>; spec: [[file, old, new], ...] (files relative to the package)
set -e
NAME=$1; SPEC=$2; shift 3
W=~/hc-work/step08a/mut/$NAME; rm -rf $W; mkdir -p $W
cp -r /workspaces/hypocurate/hypocurate $W/hypocurate
ln -s /workspaces/hypocurate/data $W/data; ln -s /workspaces/hypocurate/tests $W/tests
/workspaces/hypocurate/.venv/bin/python - "$W/hypocurate" "$SPEC" <<'PY'
import json, sys
root, spec = sys.argv[1], json.load(open(sys.argv[2]))
for f, old, new in spec:
    p = f"{root}/{f}"; s = open(p).read()
    assert s.count(old) == 1, (f, old[:50], s.count(old)); open(p, "w").write(s.replace(old, new))
PY
export DATABASE_URL="$(grep '^DATABASE_URL=' /workspaces/hypocurate/.env | cut -d= -f2-)"
cd $W && PYTHONPATH=$W /workspaces/hypocurate/.venv/bin/python -c "import hypocurate; assert hypocurate.__file__.startswith('$W')"
cd $W && PYTHONPATH=$W /workspaces/hypocurate/.venv/bin/pytest -q -p no:cacheprovider --rootdir=$W -c /dev/null "$@" 2>&1 | tail -1
```
### `rerun_mutations.sh`

```
#!/bin/bash
# Re-runs every step 8a mutation on the final tests; one line per mutation.
D=~/hc-work/step08a/mspec; M=~/hc-work/step08a/mutate2.sh; cd ~
T_G="tests/test_agent_libraries.py"
T_D="tests/test_migrations_step8a.py tests/test_data_model.py"
T_A="tests/test_access_curator.py tests/test_access_layer.py tests/test_access_dispatch.py"
T_C="tests/test_agent_core.py"
T_U="tests/test_curator.py"
T_T="tests/test_temperature_range.py tests/test_plan.py"
echo "control (no change): $(cp $D/c05.json /dev/null; ~/hc-work/step08a/mutate2.sh control <(echo '[]') -- $T_C $T_U $T_T)"
for m in g01 g02 g03; do echo "$m: $($M $m $D/$m.json -- $T_G)"; done
for m in d01 d02 d03 d04 d05 d06 d07 d08; do echo "$m: $($M $m $D/$m.json -- $T_D)"; done
for m in a01 a02 a03 a04 a05; do echo "$m: $($M $m $D/$m.json -- $T_A)"; done
for m in c01 c02 c03 c04 c05 c06 c07 c08 c09 c10; do echo "$m: $($M $m $D/$m.json -- $T_C)"; done
for m in u01 u02 u03 u04 u05 u06 u07; do echo "$m: $($M $m $D/$m.json -- $T_U)"; done
for m in t01 t02 t03 t04 t05 t06; do echo "$m: $($M $m $D/$m.json -- $T_T)"; done
```
### `refdump/test_zz_refdump.py`

```
"""Scratch (not committed): dumps the reference runs' full statistics output to REFDUMP_OUT."""
import json, os
from test_reference_numbers import runs  # noqa: F401 (the module fixture)


def test_dump(runs):
    out = {}
    for key, r in runs.items():
        records = [{"identity": [rec["stable_identity"] if "stable_identity" in rec else None], **{k: rec[k] for k in sorted(rec) if k not in ("id",)}}
                   for rec in r["data"]["records"]]
        out[key] = {"run": [str(x) for x in r["run"]], "decision": r["out"]["decision"],
                    "analyses": r["out"]["analyses"], "not_analysed": r["out"].get("not_analysed"),
                    "n_records": len(records)}
    with open(os.environ["REFDUMP_OUT"], "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
```
### `refdump/compare_v3.py`

```
"""Compares main.json with branch_v3.json leaf by leaf (the reference runs' full statistics output)."""
import collections, json
a = json.load(open("main.json")); b = json.load(open("branch_v3.json"))
out = []
def walk(x, y, p):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            walk(x.get(k, "<absent>"), y.get(k, "<absent>"), f"{p}.{k}")
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (u, v) in enumerate(zip(x, y)):
            walk(u, v, f"{p}[{i}]")
    elif x != y:
        out.append((p, x, y))
walk(a, b, "")
print("differing leaves by name:", dict(collections.Counter(p.split(".")[-1].split("[")[0] for p, _, _ in out)))
stat = [(p, x, y) for p, x, y in out if p.split(".")[-1] in ("estimate", "p_value", "std_error", "t")]
print("max relative difference of estimate, standard error, p, t:", max((abs(x - y) / abs(x) for _, x, y in stat), default=0))
for p, x, y in stat:
    print("  ", p, x, "->", y)
compared = 0
for key in a:
    print(key, "| run row identical:", a[key]["run"] == b[key]["run"],
          "| decision keys differing:", sorted(k for k in a[key]["decision"] if a[key]["decision"][k] != b[key]["decision"][k]))
    for x, y in zip(a[key]["analyses"], b[key]["analyses"]):
        assert x["analysis"] == y["analysis"]
        for k in ("counts", "checks", "minimums", "label", "label_reason", "inference_reason", "minimums_met",
                  "withheld", "df", "significant", "uninformative_groups", "scope", "set", "source"):
            compared += 1
            if x[k] != y[k]:
                print("  DIFFERENT", x["analysis"], k, x[k], y[k])
print("structural comparisons made (counts, checks, minimums, labels, reasons, df, significance per analysis):", compared)
c = b["reference"]["analyses"][0]
print("pooled on the branch:", c["counts"]["n_records"], c["counts"]["n_alloys"], c["counts"]["n_groups"],
      c["counts"]["resid_df"], round(c["estimate"], 1), round(c["std_error"], 1), f"{c['p_value']:.1e}")
```
### `packet.py`

````
"""Builds docs/reviews/step08a_review_packet.md from the files on disk (run from the repository root).
Every diff and output is quoted exactly. Frozen documentation is listed by fingerprint, not quoted."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step08a"
BASE = "cd2b3be"
OUT = Path("docs/reviews/step08a_review_packet.md")


def sh(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fence(text: str, lang: str = "") -> str:
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


def read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


head = sh("git", "rev-parse", "--short", "HEAD").strip()
parts = []
parts.append(f"""# Build step 8a — review packet

Date: 2026-10-06. Branch: `step-08a-curator`, from `main` at `{BASE}`. Head when generated: `{head}`. Generated from the files on disk by a script (`~/hc-work/step08a/packet.py`, quoted in section 11), so every diff and output below is quoted exactly. Left out: the frozen documentation files themselves (listed with their SHA-256 in section 5) and the full lock-file diffs (the added packages are listed in section 2).

## How to use this packet

Step 8a builds the agents' foundation and the Curator at source registration (the owner's decisions of 2026-10-06). It holds safeguard changes (migration 0005; the Curator's access; the spending caps; plan validation and eligibility rule 3; the guarded runner), so please review against `docs/reviews/checklist.md` and answer the questions at the end of the summary (section 1). Section 2 is the code diff; 3 the new test files; 4 the changed tests; 5 the register, manifest and frozen curation; 6 the reference comparison with `main`; 7 the live curation call; 8 the mutation checks; 9 the new tests on `main`'s code; 10 the suite; 11 the scripts.

""")
parts.append("## 1. The summary\n\n" + read("docs/reviews/step08a_summary.md") + "\n")

code_paths = ["hypocurate", "README.md", "pyproject.toml", ".env.example"]
diff = sh("git", "diff", f"{BASE}..HEAD", "--", *code_paths, ":(exclude)hypocurate/assumptions.json")
locks_old = set(l.split("==")[0] for l in sh("git", "show", f"{BASE}:requirements.lock").splitlines() if "==" in l and not l.startswith(" "))
locks_new = set(l.split("==")[0] for l in read("requirements.lock").splitlines() if "==" in l and not l.startswith(" "))
parts.append(f"## 2. Code diff (`{BASE}..HEAD`; package, README, pyproject, .env.example)\n\n"
             f"Runtime lock: {len(locks_new - locks_old)} packages added, none removed or changed in version "
             f"(`test_skeleton` checks the locks): {', '.join(sorted(locks_new - locks_old))}.\n\n" + fence(diff, "diff"))

new_tests = sh("git", "diff", "--name-only", "--diff-filter=A", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 3. New test files\n\n" + "".join(f"### `{p}`\n\n" + fence(read(p), "python") for p in new_tests))

changed = sh("git", "diff", "--name-only", "--diff-filter=M", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 4. Changed tests and test helpers (diff)\n\n" + fence(sh("git", "diff", f"{BASE}..HEAD", "--", *changed), "diff"))

reg_old = {e["key"]: e for e in json.loads(sh("git", "show", f"{BASE}:hypocurate/assumptions.json"))}
reg_new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
added = [k for k in reg_new if k not in reg_old]
modified = [k for k in reg_new if k in reg_old and reg_new[k] != reg_old[k]]
reg = "".join(f"### New: `{k}`\n\n" + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in added)
reg += "".join(f"### Changed: `{k}` (the entry as it now stands; earlier wording in its history)\n\n"
               + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in modified)
manifest = sh("git", "diff", f"{BASE}..HEAD", "--", "data/manifest.json")
docs = sh("git", "diff", "--stat", f"{BASE}..HEAD", "--", "data")
parts.append(f"## 5. Register, manifest and frozen curation\n\n{len(added)} new entries, {len(modified)} changed "
             f"(of {len(reg_new)}).\n\n" + reg + "### `data/manifest.json` (diff)\n\n" + fence(manifest, "diff")
             + "### Files added under `data/`\n\n" + fence(docs) + "### `data/sources/tamu_fcc/curation.json`\n\n"
             + fence(read("data/sources/tamu_fcc/curation.json"), "json"))

ref = (HOME / "refdump")
parts.append("## 6. Reference comparison with `main`\n\nThe five runs of `tests/test_reference_numbers.py` were dumped on "
             f"`main` (a separate checkout of `{BASE}`) and on this branch (after milestone 8: adapter version 3 with the "
             "frozen curation), then compared leaf by leaf. Scripts in section 11.\n\n"
             "### Comparison output\n\n" + fence(read(ref / "compare_v3_output.txt"))
             + "### Calibration, before and after\n\n" + fence(read(ref / "calibration_report_v3.txt")))

live = json.loads((HOME / "live_curation.json").read_text())
parts.append("## 7. The live curation call (local development database, 2026-10-06)\n\n"
             "Command: `hypocurate sources curate tamu_fcc --ceiling 0.50`, run with the owner's key from `.env` "
             "(not read or printed). Its output (the command's JSON; no key in it):\n\n"
             + fence(json.dumps(live, indent=1, ensure_ascii=False), "json")
             + "The recorded call and the decisions:\n\n" + fence(read(HOME / "live_rows.txt")))

parts.append("## 8. Mutation checks (all re-run on the final tests)\n\nEach mutation is applied to a scratch copy of the "
             "package (`data/` and `tests/` linked, `PYTHONPATH` to the copy, run from outside the repository, the "
             "import checked) and the named tests are run. The specs are in section 11.\n\n"
             + fence(read(HOME / "mutations_final.log")))

parts.append("## 9. The new tests on `main`'s code\n\nThe new test files run against `main`'s package (a checkout of "
             f"`{BASE}`), with this branch's tests and data:\n\n" + fence(read(HOME / "failed_before.log")))

parts.append("## 10. Suite\n\n### Locally\n\n" + fence(read(HOME / "suite_final.log").splitlines()[-1])
             + "### In the rebuilt test image\n\n" + fence(read(HOME / "image_final.log").splitlines()[-1]))

scripts = ["mutate2.sh", "rerun_mutations.sh", "refdump/test_zz_refdump.py", "refdump/compare_v3.py", "packet.py"]
specs = "".join(f"- `{p.stem}`: `{p.read_text().strip()}`\n" for p in sorted((HOME / "mspec").glob("*.json")))
parts.append("## 11. Scripts\n\n" + "".join(f"### `{s}`\n\n" + fence(read(HOME / s)) for s in scripts)
             + "### Mutation specs ([file, old, new] replacements)\n\n" + specs)

OUT.write_text("\n".join(parts), encoding="utf-8")
print(OUT, len(OUT.read_text()))
````
### Mutation specs ([file, old, new] replacements)

- `a01`: `[["access/layer.py", "    ok = (row.scope == \"registration\" and row.role == ctx.role and row.source_version_id == ctx.source_version_id", "    ok = (row.scope == \"registration\" and row.role == ctx.role"]]`
- `a02`: `[["access/fields.py", "path, content in sorted(version.documentation.items())", "path, content in sorted(version.files.items())"]]`
- `a03`: `[["access/allowlist.py", "        \"registration\": frozenset({\"source_documentation\", \"curation_targets\"}),", "        \"registration\": frozenset({\"source_documentation\", \"curation_targets\"}), \"curation\": frozenset({\"sources_meta\"}),"]]`
- `a04`: `[["access/dispatch.py", "        elif source_key is not None:\n            code = \"source_not_for_role\"", "        elif source_key is not None and role != \"curator\":\n            code = \"source_not_for_role\""]]`
- `a05`: `[["access/layer.py", "        d[\"source_version\"] = int(ctx.source_version_id)", "        pass"]]`
- `c01`: `[["pipeline/agents/interface.py", "            except Exception:  # noqa: BLE001 (classified by code; nothing of it is kept here)\n                code = engine.last_failure or \"malformed\"", "            except Exception as exc:  # noqa: BLE001\n                code = engine.last_failure or \"malformed\"\n                leaked = str(exc)"],
 ["pipeline/agents/interface.py", "            note = correction_note(code) if action == \"correct\" else note", "            note = (correction_note(code) + leaked) if action == \"correct\" else note"],
 ["pipeline/agents/interface.py", "    note = NO_NOTE\n", "    note = NO_NOTE\n    leaked = \"\"\n"]]`
- `c02`: `[["pipeline/agents/spend.py", "        conn.execute(text(\"SELECT pg_advisory_xact_lock(:k)\"), dict(k=MONTH_LOCK_KEY))\n", ""]]`
- `c03`: `[["pipeline/agents/lm.py", "    \"provider_unavailable\": (\"the provider could not be reached or did not answer in time\", \"retry\"),", "    \"provider_unavailable\": (\"the provider could not be reached or did not answer in time\", \"stop\"),"]]`
- `c04`: `[["pipeline/agents/lm.py", "    if isinstance(error, lm15.AuthError):\n        return \"model_auth\"\n", ""]]`
- `c05`: `[["pipeline/agents/spend.py", "        code = (cap_code if spent + max_cost > cap else", "        code = (None if spent + max_cost > cap else"]]`
- `c06`: `[["pipeline/agents/lm.py", "        if not recorded:\n            raise self._fail(\"recording_failed\")\n", ""]]`
- `c07`: `[["pipeline/agents/prices.py", "    return ((Decimal(request_bytes + FRAMING_ALLOWANCE_TOKENS) * p.input", "    return ((Decimal(FRAMING_ALLOWANCE_TOKENS) * p.input"]]`
- `c08`: `[["pipeline/agents/lm.py", "    if reason == \"length\":\n        return \"truncated\"\n", ""]]`
- `c09`: `[["pipeline/agents/spend.py", "                \"spending_cap_month\" if month + max_cost > MONTH_CAP_USD else None)", "                None)"]]`
- `c10`: `[["pipeline/agents/interface.py", "    adapter = dspy.ChatAdapter(use_json_adapter_fallback=False)", "    adapter = dspy.ChatAdapter(use_json_adapter_fallback=True)"]]`
- `d01`: `[["db/migrations/versions/0005_agents_and_documentation.py", "        IF NEW.status = 'proposed' AND NOT EXISTS (", "        IF false AND NOT EXISTS ("]]`
- `d02`: `[["db/migrations/versions/0005_agents_and_documentation.py", "    op.create_check_constraint(op.f('ck_model_call_with_invocation'), 'model_call', \"invocation_id IS NOT NULL\")", "    pass"]]`
- `d03`: `[["db/migrations/versions/0005_agents_and_documentation.py", "            IF inv.id IS NOT NULL AND (NEW.run_id IS DISTINCT FROM inv.run_id", "            IF false AND (NEW.run_id IS DISTINCT FROM inv.run_id"]]`
- `d04`: `[["db/migrations/versions/0005_agents_and_documentation.py", "                             AND role = NEW.role AND status = 'running') THEN", "                             ) THEN"]]`
- `d05`: `[["db/migrations/versions/0005_agents_and_documentation.py", "            IF NEW.run_id IS NOT NULL OR NEW.stage_result_id IS NOT NULL OR NEW.role IS DISTINCT FROM inv.role THEN", "            IF false THEN"]]`
- `d06`: `[["db/migrations/versions/0005_agents_and_documentation.py", "           OR NEW.invocation_id IS DISTINCT FROM OLD.invocation_id THEN", "           OR false THEN"]]`
- `d07`: `[["db/migrations/versions/0005_agents_and_documentation.py", "        IF (SELECT status FROM curator_proposal WHERE id = NEW.proposal_id) IS DISTINCT FROM 'proposed' THEN", "        IF false THEN"]]`
- `d08`: `[["db/migrations/versions/0005_agents_and_documentation.py", "        NEW.decided_at := now();", ""]]`
- `g01`: `[["access/guarded.py", "    sys.path[:] = existing_path_entries(sys.path)\n", ""]]`
- `g02`: `[["pipeline/agents/libraries.py", "\"LITELLM_MODE\": \"PRODUCTION\",", ""]]`
- `g03`: `[["access/guarded.py", "return [p for p in paths if os.path.exists(p)]", "return list(paths)"]]`
- `t01`: `[["pipeline/eligibility.py", "            verdicts.append(None if rec[\"categories\"][\"test_temperature_band\"] in st.bands else False)", "            verdicts.append(rec[\"categories\"][\"test_temperature_band\"] in st.bands)"]]`
- `t02`: `[["pipeline/eligibility.py", "            verdicts.append(low <= t <= high)", "            verdicts.append(low < t < high)"]]`
- `t03`: `[["pipeline/plan.py", "        if band == \"elevated\" and not tr[\"min\"] > r[\"room_temperature_max\"]:\n            raise PlanError(\"an elevated range lies above room temperature\")\n", ""]]`
- `t04`: `[["pipeline/plan.py", "    expected = set(RULES) | ({RANGE_RULE} if band != ROOM_TEMPERATURE else set())", "    expected = set(r)"]]`
- `t05`: `[["pipeline/eligibility.py", "        temperature_range=(r[\"temperature_range\"][\"min\"], r[\"temperature_range\"][\"max\"])\n        if \"temperature_range\" in r else None,", "        temperature_range=None,"]]`
- `t06`: `[["pipeline/plan.py", "    if len(s[\"temperature_band\"]) != 1:\n        raise PlanError(\"one band per plan\")\n", ""]]`
- `u01`: `[["pipeline/agents/curator.py", "    return None if isinstance(value, str) and value in CURATION_TARGETS[field][\"vocabulary\"] else \"value_not_allowed\"", "    return None"]]`
- `u02`: `[["pipeline/agents/curator.py", "    if code is None and located is None:\n        code = \"quote_not_found\"\n", "    if code is None and located is None:\n        located = quotes.Located(sorted(documents)[0], 1)\n"]]`
- `u03`: `[["sources/curated.py", "            if h[field].status == \"not_reported\":", "            if True:"]]`
- `u04`: `[["sources/curation.py", "    if version.grouping_unit != \"dataset\":\n        raise CurationRefused(\"compilation_source\")\n", ""]]`
- `u05`: `[["sources/curation.py", "        \"JOIN curator_decision d ON d.proposal_id = p.id AND d.decision = 'accepted' \"", "        \"JOIN curator_decision d ON d.proposal_id = p.id \""]]`
- `u06`: `[["cli.py", "                print(\"error: the curation did not finish (see the process log)\", file=sys.stderr)", "                print(f\"error: {sys.exc_info()[1]}\", file=sys.stderr)"]]`
- `u07`: `[["pipeline/agents/curator.py", "    documentation = \"\\n\".join(f\"=== {path} ===\\n{text}\" for path, text in sorted(documents.items()))", "    documentation = \"\\n\".join(f\"=== {path} ===\\n{text}\" for path, text in sorted(documents.items())[:1])"]]`
