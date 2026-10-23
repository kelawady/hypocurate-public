# Review packet: merging the Sprint 2 pilot branch to main (scoped)

Branch `pilot-evidence-assembly`, from main `eb78ec0`. Prepared 2026-10-23 for a second-model review (ChatGPT) and
the owner's review before the merge.

## 0. What this packet covers, and what it does not

**The owner's condition (a):** this packet is scoped to what touches Sprint 1 behaviour:
1. the freeze invariant;
2. the new source key;
3. the plan addition for pilot runs;
4. migration 0010 and its tested downgrade.

**Everything else on the branch is inert until a pilot run is started** (section 6 lists it).

**Round 2 (after ChatGPT's review of 2026-10-23, `docs/reviews/sprint2_pilot_merge_review_2026-10-23.md`):** the scope is extended to every safeguard file the 23 October report names (section 9). Added: the plan-schema refusal (10), a rehearsed rollback (7), the cost caps per call site (11), recovery and release checks (7a), answers to the C items (12) and the defects the round found (13). The B items are on the post-pilot list (`docs/sprint2/post_pilot_list.md`).

**Condition (d):** the full second-model review of the whole branch still happens in the review week. This packet does
not replace it.

**Why merge now:** PRD v1.2 R9 asks for the three H1 runs "on the live site from the pilot branch", and Render deploys
only `main`. The owner chose to merge after this review (option 1, 2026-10-23).

## 1. The freeze invariant (new; a checkpoint for extracted records)

`hypocurate/pipeline/evidence.py` holds `freeze()` and `check_invariant()`. Register: `pilot_freeze_invariant`.

- **What it does:** the freeze takes S2 (every state event of the standing outputs) and, in the same transaction,
  re-checks directly from those events that every record it accepts has `accepted` as the newest state of its
  observation, each of its links and each of its mappings.
- **Independence:** the check does not use the status computation, so a fault there cannot hide a failure here.
- **On failure:** any failure refuses the freeze, and no snapshot is stored.
- **Where it sits:**
  - The PRD says the matrix is "enforced at inclusion". In the pilot it is enforced where extracted records enter:
    the freeze, from which R9 builds the sealed source.
  - **Sprint 1's Checks, Inclusion, dataset freeze and statistics are not changed.**
- **Tests:**
  - `tests/test_evidence.py::test_the_freeze_takes_s1_and_s2_and_refuses_when_the_invariant_fails` plants a status
    function that claims a figure-only record is accepted. The freeze is refused, and no S1 or S2 is stored.
  - A mutation that drops the check (`problems = []`) is caught by that test.
- **Effect on Sprint 1:** none. Sprint 1 never calls it.

## 2. The new source key

`hypocurate/access/vocabulary.py` (access layer):

```diff
-SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates"})
+SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates",
+                         "extracted_pilot"})  # Sprint 2 pilot (R9; register 'pilot_extracted_source')
```

- **What the key does:**
  - `SOURCE_KEYS` bounds which sources a locked plan may name (`PLAN_SCHEMA`).
  - The key only matters for a run that chose the `extracted_pilot` source.
  - That source exists only after the owner loads the pilot bundle or takes a freeze locally.
- **Where the source is defined:**
  - Its definition (`hypocurate/sources/pilot.py`) is kept apart from Sprint 1's `SOURCES`, so `hypocurate sources
    register` and its tests are unchanged.
  - Its adapter is added to the adapter registry (`sources/adapters/__init__.py`, one entry in each of the two maps).
- **Register:** `code_vocabularies` updated (with history), `pilot_extracted_source`.

## 3. The plan addition for pilot runs

`hypocurate/pipeline/plan.py`, `hypocurate/pipeline/confirmation.py`, `hypocurate/pipeline/profile.py`:

```python
# profile.py
PILOT_SOURCES = MappingProxyType({"extracted_pilot": "paper"})
PILOT_REREPORT_SURVIVOR = "compilation"

# plan.py
def with_pilot_sources(plan: dict, chosen) -> dict:
    extra = [s for s in p.PILOT_SOURCES if s in set(chosen or ())]
    if extra and p.PILOT_REREPORT_SURVIVOR != "compilation":
        raise PlanError(...)
    for s in extra:
        plan["rules"]["survivor_source_order"].append(s)
        plan["rules"]["grouping"].append({"source": s, "unit": p.PILOT_SOURCES[s]})
    return plan

# confirmation.py: only the fixed plan the run locks passes the run's chosen source keys
def reference_plan(row, chosen=()) -> dict:
    plan = plans.with_pilot_sources(plans.reference_plan(row.hypothesis_version_id), chosen)
    ...
def plan_to_lock(conn, run_id):
    ...
    if row.fixed_plan:
        return reference_plan(row, _chosen(conn, run_id))
```

- **For a run without the pilot source, the plan is unchanged, byte for byte:**
  - `extra` is empty, so nothing is appended or checked.
  - The lock already refuses a plan whose survivor order or grouping leaves out a chosen source (`checkpoints.py`,
    review finding 3 of step 6). That is why a pilot run needs the addition.
- **Where it applies:** fixed-plan runs only. The Planner's path (`_planner_plan`) is unchanged, so a Planner run cannot
  lock a plan that names the pilot source, and the lock refuses it.
- **How re-reports are counted once:** in the augmented pool, a re-report is "duplicate counted once" with the MPEA
  record surviving. This comes from Sprint 1's own checks and inclusion, through the survivor order.
- **Tests (`tests/test_pilot_source.py`):**
  - `test_a_plan_without_the_pilot_source_is_unchanged_and_with_it_the_source_comes_last`
  - `test_the_re_report_survivor_setting_is_the_compilation_and_no_other_value_is_accepted`, which also asserts that
    a Sprint 1 plan is untouched
  - `test_the_augmented_pool_counts_a_re_report_once_with_the_mpea_record_surviving`, a whole run through the
    orchestrator with stubbed agents
  - `test_the_augmented_pool_agrees_with_the_independent_test_side_calculation`

## 4. Migration 0010 and its tested downgrade

`hypocurate/db/migrations/versions/0010_evidence_assembly.py`, with matching classes in `db/models.py`.

**Additive tables (18):**
- document, document_parse, search_log
- document_invocation
- extraction_output, candidate_observation, candidate_value, extraction_link
- reconciler_mapping
- evidence_state_event, evidence_snapshot
- run_stop_reason
- annotation_file, annotation_row
- review_file, owner_time_log
- auditor_finding, value_correction

Each table has its triggers (append-only; the database's clock; the ordering rules: S0 holds exactly its output's
events, no event before S0, and so on).

**Changes to existing objects** (the approved safeguard change of 2026-10-22):
- **Widened checks:** `agent_invocation.scope` gains `document`; the role lists of agent_invocation, model_call,
  stage_result and agent_setting gain `extractor` and `reconciler`.
- **Two replaced functions:** `hc_agent_invocation_insert` and `hc_model_call_insert` are replaced, each with one added
  branch for the document scope. 0005's text is kept for the downgrade.
- **No column is added to any existing table.**

**Downgrade:**
- It locks, then refuses while 0010 holds any data, or while any row uses the document scope or a pilot role. It then
  restores 0005's functions and checks and drops 0010's objects.

**Tests (`tests/test_migrations_step0010.py`, 33 test functions, some parametrized):**
- `test_up_down_up_restores_0009`
- `test_a_failed_upgrade_changes_nothing`
- `test_the_downgrade_refuses_while_0010_holds_data` (parametrized)
- `test_sprint1_combinations_are_unchanged`
- `test_no_column_is_added_to_an_existing_table`
- `test_0010_replaces_only_the_two_named_functions_and_keeps_0005s_text_for_the_downgrade`

## 5. Evidence that Sprint 1 behaviour is unchanged

- **The six reference dumps** (the reference run, the fixed plan, the Planner FCC and BCC runs, a partly-sufficient
  original and its narrower question): run on main and on this branch; every file is **byte-identical**.
  - They were run after each 0010 edit and again on 2026-10-23 at `235c0a1`, the packet's commit.
- **`tests/test_reference_numbers.py`** passes on the branch (pooled 97 / 22 / 20 / 74, 424.9 ± 64.4; MPEA alone
  424.1 ± 62.2).
- **A rehearsal on a copy of the development database:** the MPEA-only fixed-plan run gives 76 records, 13 alloys,
  19 groups, k = 424.05 ± 62.22, p ≈ 1.1e-6. An independent statsmodels calculation on its frozen records agrees
  (relative difference below 1e-12).
- **The whole suite:**
  - Locally: 2,579 passed (49.5 min) at `cccd8f5`.
  - GitHub run 39911273763: green, suite step 41 min 17 s. The job limit is 60 min.
  - The final run at the merge commit will be reported.
- **Edits to existing tests (each extends a check; none is weakened):**
  - `test_access_layer.py`: the role table gains the two pilot roles and their allow-lists, with asserts that no
    other role reads at `document`.
  - `test_assumptions.py`: the pilot step value; `PARTLY` gains `pilot_extractor_models`.
  - `test_migrations.py`: the m10 trigger block.
  - `test_migrations_step10b.py`: "0009 is the head" became "0009 follows 0008, 0010 follows 0009".
  - `test_skeleton.py`: parse-lock checks.
  - `access_testing.py`: a document-context helper.
- **Not changed:** `.github/workflows/`, `render.yaml`, `Dockerfile`, `requirements.lock`. The parse environment
  (Docling) has its own lock and is never in an image.

## 6. Inert until a pilot run is started

These are on the branch and are deployed by the merge. None of them runs, is read, or changes a Sprint 1 page or run
unless a person starts it:

- **Command-line steps:** the documents commands (selection, reach, fetch, parse, extract, rowsplit, reconcile,
  evidence, review sheet, freeze, costs, H2 inventory, export-bundle and load-bundle). The extraction and parsing ones
  run locally.
- **Agents:** the Extractor and the Reconciler (agents, prompts, settings, the per-document cap). The live site never
  calls them; extraction runs locally.
- **Rules and sources:** the R6 rules, the pilot source builder and its adapter.
- **Workbook:** five columns and a sheet that appear only when a run reads the pilot source. The test asserts that
  any other run's workbook is unchanged.
- **Page:** `/pilot/h2`, a new signed-in page that is not in the menu.
- **Access layer:** the pilot allow-lists (`extractor` and `reconciler` at stage `document`, approved 2026-10-22 and
  2026-10-23). They are tested so that no Sprint 1 role reads anything at `document`, and Sprint 1 roles' lists are
  unchanged (`test_the_allow_list_matches_the_owners_table`).
- **The register:** pilot entries under step `pilot-2`. `BUILD_STEPS` is unchanged.

## 7. The deploy and revert plan (conditions (b) and (c))

**Deploy:**
1. **Tag** the current main `pre-pilot-merge` (`eb78ec0`).
2. **Merge as a single merge commit** (`git merge --no-ff pilot-evidence-assembly`) and tag it `pilot-merge-1`. Run the
   whole suite locally at the merge commit, then push main. Render deploys after the GitHub check passes, and the
   pre-deploy command applies 0010.
3. **Before the push, the owner backs up the live database** (his access; Claude Code never sees it).
4. **After the deploy:**
   - `/health` shows the merge commit with schema 0010 at head.
   - The owner reproduces the Sprint 1 reference run on live: MPEA only, fixed plan. Expected: 76 / 13 / 19,
     k = 424.05 ± 62.2.
5. **Before loading the bundle, the owner takes a second backup.**
6. **Load the bundle:** the owner runs `hypocurate documents load-bundle --file … --by "K. El-Awady"` with the live
   database address he sets himself.
7. **The three H1 runs** go through the site.

**Revert (merge review A3; rehearsed 2026-10-23 on a scratch database):** the rehearsal used `hc_rollback`, restored from the 0009-era dump of the development database (40 tables, 46,772 rows).

1. **Pause writers.** Suspend `hypocurate-worker` in the Render dashboard, and do not use the site until the revert is done.
2. **Downgrade 0010 from an environment that still has migration 0010** (this branch's checkout, or the merge commit), against the live database:
   `DATABASE_URL=<live> python -m hypocurate.db.migrate downgrade 0009` → `schema at 0009`.
   - It succeeds only while 0010 holds no data and no row uses the document scope or a pilot role.
3. **Revert the code:** `git revert -m 1 <merge commit>` on main, run the whole suite, push. Render's pre-deploy (`python -m hypocurate.db.migrate upgrade`, `render.yaml` lines 23 and 49) then finds the database at 0009, main's head, and does nothing.
4. **Resume the worker.**

**What the rehearsal showed:**
- **The wrong order fails.** With the database still at 0010, main's pre-deploy stops with `Can't locate revision identified by '0010'` (exit 1). On Render a failed pre-deploy aborts that deploy, so the reverted code would never go live until step 2 is done.
- **The right order restores the state exactly.** After step 2 and main's pre-deploy (main checked out at `eb78ec0` in a separate worktree), the catalog matched the state before the upgrade in every part: tables, columns, constraints, indexes, triggers, functions with their source, views, sequences. The revision and the row counts of all 40 tables were identical too.

**After the bundle is loaded:**
- Step 2 refuses by design. Restore the second backup (0010, no pilot data), then follow steps 1 to 4.
- Or restore the first backup (0009).
- **Cutoff:** any write after the backup that is restored is lost. So between each backup and the end of its checks the worker stays suspended and the site is not used. The cutoff is the backup's time.

## 7a. Recovery and release checks (merge review A5)

**Restore rehearsal of the live backup: done, 2026-10-23** (daily report section 17).
- The owner's backup (1,064,714 bytes) restored into `hc_live_restore` with no errors: schema 0009, 13,147 rows, the three live reference runs at 424.88 ± 64.38.
- Its catalog matches main's fresh 0009 except two CHECKs printed with different parentheses.
- On the copy:
  - 0010 upgrade;
  - MPEA reference 424.05 ± 62.22;
  - bundle loaded, pilot fingerprint abe38724…, identical to the development freeze;
  - MPEA reference identical again;
  - extracted only: insufficient;
  - augmented: 419.73 ± 62.31;
  - the independent calculation agrees.

The procedure was:
1. The owner runs `pg_dump -Fc "$LIVE_URL" > ~/hc-work/live_backup_<date>.dump` in his own terminal. The address is never shown to Claude Code.
2. Claude Code restores the file into a scratch database (`hc_live_restore`) and checks that its revision is 0009, its row counts match `/health` and the owner's expectations, and its catalog is intact.
3. On that copy: the MPEA reference run; upgrade to 0010 with this branch; the reference run again; load the bundle; the reference run again.

**On the 0009-era stand-in, already rehearsed** (2026-10-23, `hc_rollback`, every model call to the stub):

| Step | Result |
|---|---|
| Upgraded to 0010; MPEA reference run | 76 / 13 / 19, k = 424.05 ± 62.22, p ≈ 1.1e-6 |
| Bundle loaded | 551 events, 40 snapshots with every hash re-checked, the freeze invariant re-checked, pilot version sealed |
| MPEA reference run again | identical: 76 / 13 / 19, 424.05 ± 62.22 |
| Extracted only | insufficient: 4 records scope not confirmed, 1 single grain size |
| Augmented pool | 77 / 13 / 20, k = 419.73 ± 62.31 |

- **That rehearsal found a defect, fixed before the merge** (`fa07602`). The fixed plan's chosen sources were read from `run_source` without the "chosen" filter. `run_source` also lists registered but unchosen sources, so after the bundle every MPEA-only fixed run named the pilot source, and the new lock rule (A2) refused it.
  - Test: `tests/test_pilot_source.py::test_a_sprint1_run_on_a_database_holding_the_pilot_source_locks_a_plan_without_it` (it fails without the fix).

**The production image** (built exactly as Render builds it: `docker build --file ./Dockerfile`, last stage):
- It runs as `app`, its command is uvicorn, and it holds no `tests/` or `docs/`.
- Run against `hc_rollback` (0010 with the bundle):
  - Pre-deploy: `schema at 0010`.
  - Web with `HYPOCURATE_ENV=production`: `/health` gives `{"web":"ok","database":"ok","schema":{"revision":"0010","at_head":true}}`.
  - Signed out: `/health` and `/login` give 200; `/`, `/runs`, `/assumptions`, `/help`, `/pilot/h2`, a run page and a workbook all give 303 to `/login`.
  - Worker: started, "nothing to claim; database reachable".
- Signed in, same image in development mode (the production cookie is HTTPS-only), with the local test password: 200 for `/`, `/runs`, `/queries`, `/sources`, `/assumptions`, `/help`.
  - The Sprint 1 run page shows 424.1.
  - The pilot run page shows 419.7.
  - The Sprint 1 run's workbook keeps its four sheets.
  - The pilot run's workbook adds "Extracted evidence by state".
  - The records CSV, `/pilot/h2` and its workbook all work.

**The live sequence:**
1. First backup, worker suspended.
2. Merge and push.
3. `/health` shows the merge commit at 0010.
4. Signed-in pages checked.
5. The MPEA reference run on live (424.05 ± 62.2).
6. Second backup.
7. Load the bundle.
8. The MPEA reference run on live again: it must be identical.
9. The three H1 runs.

## 9. The other safeguard files (merge review A1)

All of these changes were approved as safeguard changes on 2026-10-22 and 2026-10-23. Each adds the pilot's scope and roles without changing a Sprint 1 role's input.

| File | Change | Covering tests |
|---|---|---|
| `access/allowlist.py` | `ROLES` gains `extractor`, `reconciler`; `STAGES` gains `document`; five field descriptions; the two roles' lists at `document` only | `test_access_layer.py::test_the_allow_list_matches_the_owners_table` (complete table: no Sprint 1 role reads at `document`; pilot roles read nothing elsewhere; `compilation_records` never on the Extractor's list) |
| `access/context.py` | `AccessContext.document_parse_id` (optional); its validation accepts either a source version or a parsed document for a run-less context | `test_extractor.py::test_an_extractor_reads_only_its_own_document_and_a_reconciler_reads_nothing_there`; Sprint 1 context tests unchanged |
| `access/dispatch.py` | `bind_invocation` binds a document invocation to stage `document` with its parsed document; registration unchanged | `test_reconcile.py::test_the_reconcilers_input_is_the_document_its_s0_and_the_compilations_records_for_that_paper`; `test_extractor.py::test_the_extractors_complete_input_is_its_document_and_the_specs_reading_sections` |
| `access/layer.py` | `document_stage()`; three refusal codes (`no_document`, `no_draft`, `spec_not_named`); the audit row records the parsed document | `test_extractor.py::test_a_setting_without_a_specification_reads_none`; the access suite (`test_access_*`) unchanged |
| `access/fields.py` | five readers (`parsed_document`, `extraction_spec`, `extraction_draft`, `s0_records`, `compilation_records`) | `test_extractor.py::test_no_planted_value_record_id_or_claim_reaches_the_outbound_requests`; `test_pilot_blindness.py::test_a_re_extraction_after_review_sees_no_review_reconciler_or_compilation_text` |
| `access/vocabulary.py` | `SOURCE_KEYS` + `extracted_pilot` | section 2; `test_pilot_plan_lock.py` |
| `pipeline/agents/spend.py` | `DOCUMENT_CAP_USD` = $2 per document invocation; stage `document` in its audit rows | section 11 |
| `pipeline/agents/lm.py` | `FAILURES` + `spending_cap_document` (a defect found by A4's tests) | `test_pilot_spending.py::test_every_refusal_code_of_the_spending_module_is_a_known_failure_that_stops` |
| `pipeline/agents/settings.py` | `MODELS` + extractor, reconciler (Sonnet 5.5); `extractor_variant`, `reconciler_variant` read versioned prompt files | `test_extractor.py::test_the_extractor_settings_come_from_the_versioned_prompt_files`; `test_assumptions.py` settings checks |
| `pipeline/checkpoints.py` | the lock refuses a plan naming a pilot source the run did not choose (A2) | section 10 |
| `pipeline/confirmation.py` | `reference_plan(row, chosen)`; `_chosen` reads only chosen sources | section 3; `test_pilot_source.py::test_a_sprint1_run_on_a_database_holding_the_pilot_source_locks_a_plan_without_it` |

**Start-up:**
- The web service validates the register at start (`assumptions.load_register`). The pilot entries pass, and they use the step value `pilot-2` while `BUILD_STEPS` stays 5 to 12 (`test_assumptions.py::test_the_pilot_step_is_accepted_beside_build_steps_5_to_12`).
- The worker's start is unchanged.
- The release image starts web and worker (section 7a).

## 10. The plan schema (merge review A2)

`SOURCE_KEYS` now admits `extracted_pilot`, so `PLAN_SCHEMA` accepts a plan that names it. The rules lock (`checkpoints.lock_rules`) therefore refuses a plan that names a pilot source the run did not choose, in either the survivor order or the grouping.

Tests (`tests/test_pilot_plan_lock.py`):
- `test_an_ordinary_sprint1_plan_validates_unchanged_and_names_no_pilot_source`: the fixed plan and the Planner's template plan validate unchanged and lock.
- `test_a_plan_naming_the_pilot_source_on_a_run_without_it_is_refused` (survivor order, grouping, both).
- `test_a_pilot_plan_built_first_does_not_change_a_later_sprint1_plan` (C2).
- A mutation that removes the refusal fails 3 of these tests.

## 11. Cost caps per call site (merge review A4)

Every request is reserved before it is sent (`lm.complete` → `spend.reserve`), each attempt separately. A refusal sends nothing.

| Call site | Cap | Test |
|---|---|---|
| Extractor, extraction call | per document invocation ($2) | `test_pilot_spending.py::test_the_extraction_call_is_refused_before_any_request_under_the_document_cap`; `test_extractor.py::test_a_document_invocation_is_reserved_under_the_per_document_cap` |
| Extractor, verification call | monthly ($50) | `test_pilot_spending.py::test_the_verification_call_is_refused_before_any_request_under_the_monthly_cap` |
| A retry (after a malformed answer) | reserved again | `test_pilot_spending.py::test_a_retry_is_reserved_again_and_refused_when_the_cap_is_reached_between_attempts` |
| Reconciler | per document invocation and monthly | `test_pilot_spending.py::test_the_reconciler_call_is_refused_before_any_request_under_either_cap` |
| A repair's extraction | the extraction call above (same code path, new invocation) | as above |
| The monthly cap, shared by every call in the database | $50 | `test_agent_core.py::test_the_month_cap_counts_every_call_including_unconfirmed_ones`; `test_agent_core.py::test_two_reservations_cannot_both_pass_the_month_cap` |
| Every refusal code stops cleanly | — | `test_pilot_spending.py::test_every_refusal_code_of_the_spending_module_is_a_known_failure_that_stops` (found the missing entry) |

**Stated plainly:**
- The "per-document" cap is per document invocation. A paper extracted again (a repair, a prompt version) starts a new $2 budget. The monthly cap bounds the total across invocations and papers.
- The owner's $1-per-document stop rule is applied by the extraction command after each document (`mx.DOCUMENT_STOP_USD`), not by the database.

## 12. Answers to the C items

| C item | Claim | Test or record |
|---|---|---|
| C1 freeze invariant, exclusive entry | The pilot source is built only from a freeze (`documents freeze` → `evidence.freeze`, which runs the invariant → `pilot.register_frozen`); the bundle re-checks the invariant on the loaded events before it seals the version on live | `test_evidence.py::test_the_freeze_takes_s1_and_s2_and_refuses_when_the_invariant_fails`; `test_evidence.py::test_the_freeze_invariant_refuses_any_non_accepted_part_even_when_status_says_accepted` (link proposed, mapping disputed, observation disputed); `test_bundle.py::test_a_bundle_whose_freeze_names_a_non_accepted_record_is_refused_even_with_consistent_hashes` |
| C2 the plan helper mutates its argument | `plan.reference_plan` builds a new dict each call; a pilot plan built first leaves a later Sprint 1 plan unchanged; a Sprint 1 run on a database holding the pilot source locks the ordinary plan | `test_pilot_plan_lock.py::test_a_pilot_plan_built_first_does_not_change_a_later_sprint1_plan`; `test_pilot_source.py::test_a_sprint1_run_on_a_database_holding_the_pilot_source_locks_a_plan_without_it` |
| C3 0009 → 0010 → 0009 catalog | The catalog snapshot compared covers tables, columns, constraints (`pg_get_constraintdef`), indexes, triggers (`pg_get_triggerdef`), functions (`prosrc`), views, sequences, types | `test_migrations_step0010.py::test_up_down_up_restores_0009`; on real data, section 7 (catalog and row counts identical) |
| C4 blindness at the final boundary | The Extractor's complete input is its document, the specification's reading sections and its own new draft; planted compilation values, a record id, the claim, a Reconciler mapping, a person's decision, a finding and a correction never reach a re-extraction's requests | `test_access_layer.py::test_the_allow_list_matches_the_owners_table`; `test_extractor.py::test_the_extractors_complete_input_is_its_document_and_the_specs_reading_sections`; `test_extractor.py::test_no_planted_value_record_id_or_claim_reaches_the_outbound_requests`; `test_pilot_blindness.py::test_a_re_extraction_after_review_sees_no_review_reconciler_or_compilation_text` |
| C5 artifacts bound to the release commit | Supplied at the merge: the merge SHA, the whole suite there (local and GitHub), the six dumps there against main (raw files in `~/hc-work/sprint2/refdump/`), the MPEA run's source version fingerprint and plan fingerprint | recorded in the daily report at the merge |

## 13. Defects found by this round's rehearsals and tests (all fixed before the merge)

1. **`spending_cap_document` missing from the agent core's failure table** (A4). A document-cap refusal raised a KeyError after nothing was sent.
2. **The fixed plan's chosen sources included registered but unchosen sources** (A5 rehearsal). After the bundle, every Sprint 1 fixed run would have been refused by the A2 lock rule.
3. **The bundle sealed the pilot source without re-checking the freeze invariant** (C1). It now re-checks on the loaded events.

## 14. Questions for the reviewer (first round)

1. Is enforcing the acceptance matrix at the freeze (rather than inside Sprint 1's inclusion) acceptable for the pilot,
   given that inclusion only ever sees accepted records through the sealed source?
2. Does any path let a Sprint 1 run (no pilot source chosen) reach `with_pilot_sources` with a non-empty result?
3. Is the downgrade's refusal list (0010 data, the document scope, pilot roles in four tables) complete?
4. Is any edit in section 5's test list a weakening?
