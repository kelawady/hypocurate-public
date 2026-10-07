# Build step 8a — summary for review

> **After ChatGPT's review (2026-10-07):** six findings and the owner's term-check changes were fixed; see `step08a_review_chatgpt.md` and `step08a_fix_packet.md`. This summary is kept as it was reviewed, with two overclaims corrected in place (marked *Corrected*). Where it gives the quote bounds as 30–1500 characters, the database checks as occurrence and term only, or the Curator invocation as allowed in a run, the fix packet supersedes it.

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

0001–0004 untouched as files; the two replaced model-call functions keep every check of 0001 (tested textually and verbatim for the downgrade). *Corrected after ChatGPT's review (2026-10-07): not "additive" as first written: 0005 replaces two of 0001's functions, replaces source_file's path rule under the same name, and makes model_call.run_id and stage_result_id nullable (safe because the live database holds no model call). See step08a_fix_packet.md.*

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
3. **Record** (`spend.finish`): reported usage and its cost from the price table, or failed with no usage and a fixed code. No provider, library or database text is kept or sent later; the original goes to the process log only. *Corrected after ChatGPT's review (2026-10-07): the process log held the exception's full text and traceback; it now gets the code, the exception's types and where it was raised, never the text. A failed recording on the failure branches was not stopped (finding 4); now every branch stops. See step08a_fix_packet.md.*
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
