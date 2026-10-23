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

**Round 3 closure (ChatGPT round 2, `docs/reviews/sprint2_pilot_merge_review_round2_2026-10-23.md`; owner: no further review round).** A3 and A5 are resolved. The rest:

| Item | Done | Evidence |
|---|---|---|
| A1 the actual diffs | yes | Appendix A: the diffs of every safeguard file against main, each with its test changes |
| A2 an ordinary Planner request | yes | `tests/test_pilot_planner_request.py::test_an_ordinary_planner_request_is_byte_identical_to_mains`: the complete outbound body (instruction, inputs, DSPy's response schema) is byte-identical to the one captured under main at `eb78ec0` |
| A4 the verification call under the document cap | yes | `tests/test_pilot_spending.py::test_the_verification_call_is_refused_before_any_request_under_the_document_cap` |
| A4 the per-invocation cap | the owner's decision | register `pilot_document_cap` (owner, 2026-10-23); cumulative per-document enforcement on `docs/sprint2/post_pilot_list.md` item 7 |
| Defect 3 shown to fail without the fix | yes | section 13 |
| The runbook (worker resumed; validation writes) | yes | section 7a: the validation window, V1 to V5, the worker resumed at steps 5 and 9 |

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

**Deploy:** the live runbook in section 7a, steps 1 to 12. It is the only deploy sequence; the round-1 list it replaces is in the history of this file.

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

**The live runbook (round 2: the worker resumed explicitly; validation writes kept apart from ordinary use):**

- **The validation window** runs from step 1 to step 12.
  - In it, nobody uses the site for anything else: no queries, no runs, no curation.
  - The only writes are the owner's validation writes, numbered V1 to V5 below. Each is labelled as validation in its query text, e.g. "validation V1: MPEA reference before the bundle".
- **Restore cutoffs:** restoring backup B1 loses everything after step 2; restoring B2 loses V2 to V5. Every validation write can be redone, and no ordinary work is at risk because there is none in the window.

| Step | Who | What |
|---|---|---|
| 1 | owner | Suspend `hypocurate-worker` in Render. The window opens. |
| 2 | owner | **B1:** `pg_dump -Fc "$LIVE_URL" > ~/hc-work/live_backup_B1_<time>.dump` (cutoff 1) |
| 3 | Claude Code | Tag `pre-pilot-merge` on main; `git merge --no-ff`; tag `pilot-merge-1`; whole suite at the merge commit; push main |
| 4 | Render, then Claude Code | The GitHub check passes; Render deploys; pre-deploy applies 0010. Check that `/health` shows the merge commit with schema 0010 at head. |
| 5 | owner | **Resume the worker** (it runs the validation runs). Check the signed-in pages. |
| 6 | owner | **V1:** an MPEA-only fixed-plan run. Expected 76 / 13 / 19, k = 424.05 ± 62.2 |
| 7 | owner | Suspend the worker. **B2:** `pg_dump` to `live_backup_B2_<time>.dump` (cutoff 2) |
| 8 | owner | **V2:** `hypocurate documents load-bundle --file ~/hc-work/sprint2/bundle_v2_after_freeze.zip --by "K. El-Awady"` |
| 9 | owner | **Resume the worker.** |
| 10 | owner | **V3:** an MPEA-only fixed-plan run again; it must equal V1, and it is H1's 'MPEA only' run. **V4:** the extracted source only, under 'use what is available'. **V5:** MPEA + the extracted source, fixed minimum. |
| 11 | owner | Test-side check: `DATABASE_URL="$LIVE_URL" python tests/pilot_independent.py <augmented run id>` must report `"agree": true` |
| 12 | owner | Delete the PostgreSQL inbound IP rule "codespace pilot" (<codespace address>/32). The window closes and ordinary use resumes. |

**Model cost on live:** each run makes a Critic and an Analyst call, about $0.04, so about $0.16 for V1 and V3–V5.

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
| `pipeline/checkpoints.py` | the lock refuses a plan naming a pilot source the run did not choose (A2), reading the code list `vocabulary.PILOT_SOURCE_KEYS` (decision code never imports the profile: `test_eligibility.py::test_decision_code_does_not_import_the_domain_profile`) | section 10 |
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
| Extractor, verification call | per document invocation ($2) and monthly ($50) | `test_pilot_spending.py::test_the_verification_call_is_refused_before_any_request_under_the_document_cap`; `test_pilot_spending.py::test_the_verification_call_is_refused_before_any_request_under_the_monthly_cap` |
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
   - With the check removed, `tests/test_bundle.py::test_a_bundle_whose_freeze_names_a_non_accepted_record_is_refused_even_with_consistent_hashes` fails (`DID NOT RAISE BundleRefused`); restored, it passes. The removed check is exactly the pre-fix code.
4. **The A2 lock rule first imported the domain profile into `checkpoints.py`**, which Sprint 1 forbids for decision code. Found by the whole suite (`test_eligibility.py::test_decision_code_does_not_import_the_domain_profile[checkpoints]`). The lock now reads `access.vocabulary.PILOT_SOURCE_KEYS`; `test_pilot_plan_lock.py::test_the_locks_pilot_list_is_a_code_list_matching_the_profile` keeps the two lists equal.

## 14. Questions for the reviewer (first round)

1. Is enforcing the acceptance matrix at the freeze (rather than inside Sprint 1's inclusion) acceptable for the pilot,
   given that inclusion only ever sees accepted records through the sealed source?
2. Does any path let a Sprint 1 run (no pilot source chosen) reach `with_pilot_sources` with a non-empty result?
3. Is the downgrade's refusal list (0010 data, the document scope, pilot roles in four tables) complete?
4. Is any edit in section 5's test list a weakening?

## Appendix A. The safeguard files' diffs against main, with their test changes (merge review round 2, A1)

Generated with `git diff main -- <files>` at the packet's commit (regenerated after the final fix: the lock reads `vocabulary.PILOT_SOURCE_KEYS`, not the profile). New files (`pipeline/evidence.py`, `sources/pilot.py`, `documents/bundle.py`, migration 0010) are not diffs against main; sections 1, 4 and 12 describe them, and their tests are named there.

### Access layer

```diff
diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index 15b6c19..ba21657 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -41,7 +41,9 @@ from hypocurate.access.vocabulary import (CALIBRATION_METHODS, CATEGORY_FIELDS,
                                           SENSITIVITY_KEYS, SINGLE_PHASE, SOURCE_KEYS, TEMPERATURE_BANDS, TEST_TYPES,
                                           VALUE_STATUSES)
 
-ROLES = ("planner", "curator", "critic", "analyst", "commentator")
+# Sprint 2 pilot (owner, 2026-10-22, an approved safeguard change): the Extractor reads one parsed document in no
+# run; the Reconciler reads nothing until its lists are built and reviewed with R5.
+ROLES = ("planner", "curator", "critic", "analyst", "commentator", "extractor", "reconciler")
 # The code roles of PRD 4 (step 6, owner 2026-10-05): Inclusion and Checks are code, not
 # agents. They read through access objects too, bound by `dispatch.bind_code`, so their reads
 # are logged. No agent setting can bind as one of them. Step 7 (owner, 2026-10-05; a safeguard
@@ -58,8 +60,10 @@ ALL_ROLES = ROLES + CODE_ROLES
 # version, bound by a registration invocation (`dispatch.bind_invocation`), with no run.
 # narrowed (step 8b, owner 2026-10-07, A4): running, no plan, and code's narrowing decision of partly
 # sufficient stored; no plan can be locked from here (lock_rules needs before_lock; migration 0006).
+# document (Sprint 2 pilot, owner 2026-10-22): not a run stage; the Extractor reads one parsed document, bound by a
+# document invocation (`dispatch.bind_invocation`), with no run.
 STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze",
-          "registration", "narrowed")
+          "registration", "narrowed", "document")
 
 FIELDS = MappingProxyType({
     "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
@@ -76,6 +80,20 @@ FIELDS = MappingProxyType({
                             "No data file, no claim, no plan, no other version.",
     "curation_targets": "For the Curator at registration (step 8a): the fields it may propose a value for, "
                         "with each field's vocabulary or unit (vocabulary.CURATION_TARGETS).",
+    "parsed_document": "For the Extractor (Sprint 2 pilot): the one parsed document its invocation names, as stored "
+                       "(pages, text blocks and tables with their page, table and row indexes), checked against its "
+                       "hash. No DOI, no compilation record, no other document, no claim.",
+    "extraction_spec": "For the Extractor (Sprint 2 pilot; owner, 2026-10-22): the reading sections of the evidence "
+                       "specification its setting names (unit of observation, required measurements, required "
+                       "context, linkage evidence, ambiguity handling), with the specification's key, version and "
+                       "hash. Never the claim, the analysis, the exclusion rules or the re-report rule.",
+    "extraction_draft": "For the Extractor's verification call (Sprint 2 pilot; owner, 2026-10-23): the raw output "
+                        "of its own extraction call on the same parsed document, as stored with its hash.",
+    "s0_records": "For the Reconciler (Sprint 2 pilot; owner, 2026-10-23): the candidate observations of the newest S0 "
+                  "on the parsed document its invocation names, each with its values as written and their provenance.",
+    "compilation_records": "For the Reconciler (Sprint 2 pilot; owner, 2026-10-22: its list may include compilation "
+                           "records, so its outputs are S1, never S0): the compilation's (MPEA's) records for the same "
+                           "paper, each with its key, alloy, composition, grain size, yield strength and conditions.",
     "record_metadata": "Per stored record: id, source, item index, kind, alloy label and composition, DOI "
                        "(DOI syntax only), each field's status, and the non-outcome category values from "
                        "their vocabularies. No measured number of any field, no paper title, no origin key.",
@@ -160,6 +178,16 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
     # built and its lists are decided and reviewed. Its step 5 lists are kept in the register entry
     # 'access_allow_lists' as the starting point.
     "commentator": MappingProxyType({}),
+    # Sprint 2 pilot (owner, 2026-10-22): the Extractor reads one parsed document and the reading sections of its
+    # evidence specification; its verification call also reads its own draft. Nothing that holds the compilation.
+    "extractor": MappingProxyType({
+        "document": frozenset({"parsed_document", "extraction_spec", "extraction_draft"}),
+    }),
+    # R5 (owner, 2026-10-23: per document, before the runs): the Reconciler reads one parsed document, its newest S0
+    # and the compilation's records for that paper; its outputs are S1 events, never S0.
+    "reconciler": MappingProxyType({
+        "document": frozenset({"parsed_document", "s0_records", "compilation_records"}),
+    }),
 })
 
 
diff --git a/hypocurate/access/context.py b/hypocurate/access/context.py
index fe60f20..d289d2d 100644
--- a/hypocurate/access/context.py
+++ b/hypocurate/access/context.py
@@ -12,7 +12,8 @@ from dataclasses import dataclass
 @dataclass(frozen=True, slots=True)
 class AccessContext:
     """A run context (run_id set), or, from step 8a, a registration context: no run, the Curator,
-    stage 'registration', the sealed source version its invocation names."""
+    stage 'registration', the sealed source version its invocation names; or, from the Sprint 2 pilot, a document
+    context: no run, the Extractor, stage 'document', the parsed document its invocation names."""
     run_id: int | None
     role: str
     stage: str
@@ -20,3 +21,4 @@ class AccessContext:
     agent_setting_id: int | None = None
     source_version_id: int | None = None
     invocation_id: int | None = None
+    document_parse_id: int | None = None
diff --git a/hypocurate/access/dispatch.py b/hypocurate/access/dispatch.py
index 7a710c3..03a78f9 100644
--- a/hypocurate/access/dispatch.py
+++ b/hypocurate/access/dispatch.py
@@ -39,7 +39,8 @@ from hypocurate.access.allowlist import CODE_ROLES, allowed
 from hypocurate.access.context import AccessContext
 from hypocurate.access.errors import AccessDenied, AccessFailed
 from hypocurate.access.layer import (_AUDIT, _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, DENIALS, Access, _detail, _row,
-                                     bounded_source, keep_in_process_log, log_failure, registration_stage)
+                                     bounded_source, document_stage, keep_in_process_log, log_failure,
+                                     registration_stage)
 from hypocurate.access.stage import actual_stage
 from hypocurate.db.retry import run_transaction, sqlstate
 
@@ -97,9 +98,10 @@ def bind_invocation(engine: Engine, invocation_id: int, lock_timeout_ms: int = A
         raise TypeError("bind_invocation takes an integer invocation id")
     try:
         row = run_transaction(engine, lambda conn: conn.execute(text(
-            "SELECT i.scope, i.run_id, i.role, i.agent_setting_id, i.source_version_id, s.key AS source_key "
-            "FROM agent_invocation i LEFT JOIN source_version sv ON sv.id = i.source_version_id "
-            "LEFT JOIN source s ON s.id = sv.source_id WHERE i.id = :i"), dict(i=invocation_id)).one_or_none())
+            "SELECT i.scope, i.run_id, i.role, i.agent_setting_id, i.source_version_id, s.key AS source_key, "
+            "di.document_parse_id FROM agent_invocation i LEFT JOIN source_version sv ON sv.id = i.source_version_id "
+            "LEFT JOIN source s ON s.id = sv.source_id LEFT JOIN document_invocation di ON di.invocation_id = i.id "
+            "WHERE i.id = :i"), dict(i=invocation_id)).one_or_none())
     except DBAPIError as error:
         probe = AccessContext(None, UNBOUND, UNBOUND, invocation_id=invocation_id)
         keep_in_process_log(probe, "bind", "database_error", error)
@@ -116,12 +118,16 @@ def bind_invocation(engine: Engine, invocation_id: int, lock_timeout_ms: int = A
     if row.scope == "run":
         return bind(engine, row.run_id, row.agent_setting_id, lock_timeout_ms=lock_timeout_ms,
                     _invocation_id=invocation_id)
-    ctx = AccessContext(None, row.role, "registration", row.source_key, row.agent_setting_id,
-                        source_version_id=row.source_version_id, invocation_id=invocation_id)
+    if row.scope == "document":  # Sprint 2 pilot: the Extractor on one parsed document, no run
+        ctx = AccessContext(None, row.role, "document", None, row.agent_setting_id, invocation_id=invocation_id,
+                            document_parse_id=row.document_parse_id)
+    else:
+        ctx = AccessContext(None, row.role, "registration", row.source_key, row.agent_setting_id,
+                            source_version_id=row.source_version_id, invocation_id=invocation_id)
 
     def transaction(conn: Connection):
-        stage = registration_stage(conn, ctx)
-        code = None if stage == "registration" else "stage_mismatch"
+        stage = document_stage(conn, ctx) if row.scope == "document" else registration_stage(conn, ctx)
+        code = None if stage == ctx.stage else "stage_mismatch"
         conn.execute(_AUDIT, _row(ctx, None, "bind", code is None,
                                   _detail(ctx, "denied" if code else "allowed", code, stage,
                                           agent_setting=row.agent_setting_id)))
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 34dce18..bfa525a 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -250,6 +250,99 @@ def curation_targets(conn: Connection, ctx: Context) -> dict:
     return {field: dict(spec) for field, spec in vocab.CURATION_TARGETS.items()}
 
 
+# --- the Extractor (Sprint 2 pilot; owner, 2026-10-22) ---------------------------------------------------------------
+# Each reads the one parsed document its invocation names, or the specification its setting names. None of them reads
+# a source version, a record, a run or a claim: S0's reference-blindness is enforced here and only here.
+PARSED_KEYS = ("pages", "texts", "tables")
+
+
+def parsed_document(conn: Connection, ctx: Context) -> dict:
+    """The parsed document as stored, checked against its hash: pages, text blocks and tables (no DOI)."""
+    if ctx.document_parse_id is None:
+        raise Refused("no_document")
+    row = conn.execute(text("SELECT document_id, parsed, parsed_sha256 FROM document_parse WHERE id = :p "
+                            "AND status = 'parsed'"), dict(p=ctx.document_parse_id)).one_or_none()
+    if row is None or hashlib.sha256(row.parsed.encode("utf-8")).hexdigest() != row.parsed_sha256:
+        raise Refused("no_document")
+    content = json.loads(row.parsed)
+    return {"document_id": row.document_id, "parse_sha256": row.parsed_sha256,
+            **{k: content.get(k) for k in PARSED_KEYS}}
+
+
+def extraction_spec(conn: Connection, ctx: Context) -> dict:
+    """The reading sections of the evidence specification the Extractor's setting names (owner, 2026-10-22): never
+    the claim, the analysis, the exclusion rules or the re-report rule."""
+    from hypocurate.pipeline.extraction.interface import EvidenceSpec
+    name = conn.execute(text("SELECT settings->>'evidence_spec' FROM agent_setting WHERE id = :a"),
+                        dict(a=ctx.agent_setting_id)).scalar()
+    if not name:
+        raise Refused("spec_not_named")
+    spec = EvidenceSpec.load(name)
+    return {"key": spec.key, "version": spec.version, "sha256": spec.sha256,
+            "sections": {s: spec.content[s] for s in spec.content["extractor_sections"]}}
+
+
+def extraction_draft(conn: Connection, ctx: Context) -> dict:
+    """The raw output of the Extractor's own extraction call on the same parsed document (the newest), checked
+    against its hash, for the verification call (owner, 2026-10-23)."""
+    if ctx.document_parse_id is None:
+        raise Refused("no_document")
+    row = conn.execute(text(
+        "SELECT x.id, x.raw_output, x.raw_sha256 FROM extraction_output x "
+        "JOIN document_invocation di ON di.invocation_id = x.invocation_id "
+        "WHERE x.document_parse_id = :p AND di.document_parse_id = :p AND x.status = 'returned' "
+        "AND x.method->>'step' = 'extract' ORDER BY x.id DESC LIMIT 1"), dict(p=ctx.document_parse_id)).one_or_none()
+    if row is None or hashlib.sha256(row.raw_output.encode("utf-8")).hexdigest() != row.raw_sha256:
+        raise Refused("no_draft")
+    return {"output_id": row.id, "raw_sha256": row.raw_sha256, "raw_output": row.raw_output}
+
+
+def _document_of(conn: Connection, ctx: Context):
+    if ctx.document_parse_id is None:
+        raise Refused("no_document")
+    return conn.execute(text("SELECT d.id, d.doi_key FROM document_parse p JOIN document d ON d.id = p.document_id "
+                             "WHERE p.id = :p"), dict(p=ctx.document_parse_id)).one()
+
+
+def s0_records(conn: Connection, ctx: Context) -> dict:
+    """The newest S0 on the bound parsed document: its candidate observations with values and provenance."""
+    _document_of(conn, ctx)
+    out = conn.execute(text(
+        "SELECT x.id FROM extraction_output x JOIN evidence_snapshot s ON s.extraction_output_id = x.id "
+        "AND s.name = 'S0' WHERE x.document_parse_id = :p ORDER BY x.id DESC LIMIT 1"),
+        dict(p=ctx.document_parse_id)).scalar()
+    if out is None:
+        raise Refused("no_draft")
+    observations = []
+    for o in conn.execute(text("SELECT id, item_index, identity FROM candidate_observation WHERE extraction_output_id = :x "
+                               "ORDER BY item_index"), dict(x=out)).all():
+        values = [dict(field=v.field, text=v.value_text, unit=v.unit, definition=v.definition,
+                       provenance=v.provenance, ambiguity_note=v.ambiguity_note)
+                  for v in conn.execute(text("SELECT field, value_text, unit, definition, provenance, ambiguity_note "
+                                             "FROM candidate_value WHERE observation_id = :o ORDER BY id"),
+                                        dict(o=o.id)).all()]
+        observations.append({"item_index": o.item_index, "reported_from": o.identity.get("reported_from"),
+                             "values": values})
+    return {"extraction_output_id": out, "observations": observations}
+
+
+def compilation_records(conn: Connection, ctx: Context) -> list[dict]:
+    """MPEA's records for the bound document's paper (by Sprint 1's DOI key), from its newest sealed version."""
+    from hypocurate.sources.versions import latest_sealed_version_id
+    doc = _document_of(conn, ctx)
+    version = load_sealed_version(conn, latest_sealed_version_id(conn, "mpea"))
+    out = []
+    for r in adapters.read(version).records:
+        if not r.paper_doi or doi_group_key(r.paper_doi) != doc.doi_key:
+            continue
+        h = r.harmonized
+        out.append({"key": r.source_item_key, "alloy": r.alloy, "composition": h["composition"].value,
+                    "grain_size_um": h["grain_size"].value, "yield_strength_mpa": h["yield_strength"].value,
+                    "test_type": h["test_type"].value, "test_temperature_c": h["test_temperature"].value,
+                    "processing": h["processing_method"].value, "microstructure": h["microstructure"].value})
+    return out
+
+
 def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
     """No measured number of any field (owner, 2026-10-05): statuses, categories from their
     vocabularies, identity. No paper title and no origin key (step 5 review, finding 3)."""
@@ -629,4 +722,6 @@ READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions, "set_flags": set_flags,
     "frozen_analysis_data": frozen_analysis_data, "candidate_counts": candidate_counts,
     "analyst_facts": analyst_facts,
+    "parsed_document": parsed_document, "extraction_spec": extraction_spec, "extraction_draft": extraction_draft,
+    "s0_records": s0_records, "compilation_records": compilation_records,
 }
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index ab2b4b3..75d3508 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -77,7 +77,7 @@ LOG = logging.getLogger("hypocurate.access")
 
 # Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
 DENIALS = {
-    "unknown_role": "the role is not one of the five agent roles or the code roles",
+    "unknown_role": "the role is not one of the agent roles or the code roles",
     "not_a_code_role": "only the code roles (Inclusion, Checks, Statistics, gap facts, narrowing) are bound without "
                        "an agent setting",
     "unknown_stage": "the stage is not one of the access stages",
@@ -92,6 +92,9 @@ DENIALS = {
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
     "not_frozen": "no dataset is frozen for this run",
     "facts_missing": "the stored facts the Analyst's stage needs are not there (step 8b)",
+    "no_document": "the Extractor reads one named parsed document; none was bound",
+    "no_draft": "there is no extraction draft for this parsed document",
+    "spec_not_named": "the Extractor's setting names no evidence specification",
 }
 FAILURES = ("unknown_run", "unknown_invocation", "lock_timeout", "reader_error", "database_error", "file_guard")
 FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
@@ -125,6 +128,8 @@ def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | Non
         d["source_version"] = int(ctx.source_version_id)
     if ctx.invocation_id is not None:
         d["invocation"] = int(ctx.invocation_id)
+    if ctx.document_parse_id is not None:
+        d["document_parse"] = int(ctx.document_parse_id)
     for name, raw, valid in (("role", ctx.role, ALL_ROLES), ("stage", ctx.stage, STAGES)):
         if bounded(raw, valid) == "invalid" and raw != "invalid":
             d[f"given_{name}_length"] = len(raw) if isinstance(raw, str) else -1
@@ -177,10 +182,11 @@ class Access:
         if _trusted is not _TRUSTED:
             raise TypeError("an access object is created only by hypocurate.access.dispatch.bind")
         if not isinstance(context, AccessContext) or not (
-                isinstance(context.run_id, int) or context.run_id is None
-                and isinstance(context.source_version_id, int) and isinstance(context.invocation_id, int)):
+                isinstance(context.run_id, int) or context.run_id is None and isinstance(context.invocation_id, int)
+                and (isinstance(context.source_version_id, int) or isinstance(context.document_parse_id, int))):
             raise TypeError("an access object needs an AccessContext with an integer run id, or (registration) "
-                            "an integer source version and invocation")
+                            "an integer source version and invocation, or (document) an integer parsed document and "
+                            "invocation")
         object.__setattr__(self, "_engine", engine)
         object.__setattr__(self, "_context", context)
         object.__setattr__(self, "_lock_timeout_ms", int(lock_timeout_ms))
@@ -238,8 +244,8 @@ class Access:
 
     def _transaction(self, conn: Connection, ctx: AccessContext, function: str, fields: tuple) -> tuple:
         conn.execute(text(f"SET LOCAL lock_timeout = {self._lock_timeout_ms}"))
-        if ctx.run_id is None:  # a registration read (step 8a): no run, no lock; the invocation decides
-            actual = registration_stage(conn, ctx)
+        if ctx.run_id is None:  # a registration or document read: no run, no lock; the invocation decides
+            actual = document_stage(conn, ctx) if ctx.document_parse_id is not None else registration_stage(conn, ctx)
             if actual is None:
                 return ("unknown_invocation",)
         else:
@@ -291,6 +297,20 @@ def registration_stage(conn: Connection, ctx: AccessContext) -> str | None:
     return "registration" if ok else "none"
 
 
+def document_stage(conn: Connection, ctx: AccessContext) -> str | None:
+    """'document' when the context's invocation is a document invocation of its role on its parsed document and that
+    document is parsed (Sprint 2 pilot); 'none' otherwise; None when there is no such invocation."""
+    row = conn.execute(text("SELECT i.scope, i.role, di.document_parse_id, p.status FROM agent_invocation i "
+                            "LEFT JOIN document_invocation di ON di.invocation_id = i.id "
+                            "LEFT JOIN document_parse p ON p.id = di.document_parse_id WHERE i.id = :i"),
+                       dict(i=ctx.invocation_id)).one_or_none()
+    if row is None:
+        return None
+    ok = (row.scope == "document" and row.role == ctx.role and row.document_parse_id == ctx.document_parse_id
+          and row.status == "parsed")
+    return "document" if ok else "none"
+
+
 def _policy(ctx: AccessContext, field: str, actual: str) -> str | None:
     if ctx.role not in ALL_ROLES:
         return "unknown_role"
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index b342286..7ec1514 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -101,7 +101,10 @@ CRITIC_REASON_MAX = 300  # characters; shown to people only (A7)
 
 # Codes in the locked plan's rules (step 6): the registered sources, grouping units, value
 # statuses, domain profiles, and whether single phase is required.
-SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates"})
+SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates",
+                         "extracted_pilot"})  # Sprint 2 pilot (R9; register 'pilot_extracted_source')
+# The pilot's sources among them (merge review A2): the rules lock reads this code list, never the profile.
+PILOT_SOURCE_KEYS = frozenset({"extracted_pilot"})
 GROUPING_UNITS = frozenset({"paper", "dataset", "batch"})
 VALUE_STATUSES = frozenset({"converted", "assigned_from_source", "assigned_by_decision"})
 PROFILE_NAMES = frozenset({"grain_size_strengthening"})
```

**Test changes beside it:**

```diff
diff --git a/tests/access_testing.py b/tests/access_testing.py
index 47dabf9..4378fe0 100644
--- a/tests/access_testing.py
+++ b/tests/access_testing.py
@@ -21,3 +21,11 @@ def registration_access_for(engine, invocation_id, source_version_id, role="cura
     return Access(engine, AccessContext(None, role, stage, source_key, None, source_version_id=source_version_id,
                                         invocation_id=invocation_id), lock_timeout_ms=lock_timeout_ms,
                   _trusted=_TRUSTED)
+
+
+def document_access_for(engine, invocation_id, document_parse_id, role="extractor", stage="document",
+                        lock_timeout_ms=ACCESS_LOCK_TIMEOUT_MS):
+    """A document context (Sprint 2 pilot) the dispatcher would or would not produce."""
+    return Access(engine, AccessContext(None, role, stage, None, None, invocation_id=invocation_id,
+                                        document_parse_id=document_parse_id), lock_timeout_ms=lock_timeout_ms,
+                  _trusted=_TRUSTED)
diff --git a/tests/test_access_layer.py b/tests/test_access_layer.py
index e1431b2..68ec4c4 100644
--- a/tests/test_access_layer.py
+++ b/tests/test_access_layer.py
@@ -55,12 +55,14 @@ def audit(engine, run=None):
 
 def test_the_allow_list_matches_the_owners_table():
     """The table approved by the owner on 2026-10-05 (step 5 plan), field for field."""
-    assert ROLES == ("planner", "curator", "critic", "analyst", "commentator")
+    # Sprint 2 pilot (owner, 2026-10-22, an approved safeguard change): the Extractor and the Reconciler.
+    assert ROLES == ("planner", "curator", "critic", "analyst", "commentator", "extractor", "reconciler")
     assert set(ALLOWED) == set(ROLES)
     # Step 8b (owner, 2026-10-07): the Analyst also at 'narrowed' (A4); the Commentator reads nothing (A6).
     assert {r: set(s) for r, s in ALLOWED.items()} == {
         "planner": {"before_lock"}, "curator": {"registration"}, "critic": {"curation"},
-        "analyst": {"analysis", "closed_without_freeze", "narrowed"}, "commentator": set()}
+        "analyst": {"analysis", "closed_without_freeze", "narrowed"}, "commentator": set(),
+        "extractor": {"document"}, "reconciler": {"document"}}
     assert allowed("planner", "before_lock") == {"claim", "domain", "sources_meta", "tag_values", "record_counts"}
     # Owner, 2026-10-06 (step 8a, Q2): the Curator reads a source version's documentation at
     # registration, never in a run.
@@ -79,6 +81,15 @@ def test_the_allow_list_matches_the_owners_table():
         if stage != "before_lock":
             assert allowed("planner", stage) == frozenset()
     assert all(allowed(role, "none") == frozenset() for role in ROLES)
+    # Sprint 2 pilot: the Extractor reads one parsed document, its specification's reading sections and its own
+    # draft, at 'document' only; no other role reads anything there; the Reconciler reads nothing until R5.
+    assert allowed("extractor", "document") == {"parsed_document", "extraction_spec", "extraction_draft"}
+    assert all(allowed("extractor", stage) == frozenset() for stage in STAGES if stage != "document")
+    assert all(allowed(role, "document") == frozenset() for role in ROLES if role not in ("extractor", "reconciler"))
+    # R5 (owner, 2026-10-23): the Reconciler at 'document' only, with the compilation's records for that paper.
+    assert allowed("reconciler", "document") == {"parsed_document", "s0_records", "compilation_records"}
+    assert all(allowed("reconciler", stage) == frozenset() for stage in STAGES if stage != "document")
+    assert "compilation_records" not in allowed("extractor", "document")
 
 
 def test_every_listed_field_has_a_reader_and_a_description():
```

**New or unchanged covering tests:**

- `tests/test_extractor.py::test_the_extractors_complete_input_is_its_document_and_the_specs_reading_sections`
- `tests/test_extractor.py::test_no_planted_value_record_id_or_claim_reaches_the_outbound_requests`
- `tests/test_extractor.py::test_an_extractor_reads_only_its_own_document_and_a_reconciler_reads_nothing_there`
- `tests/test_extractor.py::test_a_setting_without_a_specification_reads_none`
- `tests/test_reconcile.py::test_the_reconcilers_input_is_the_document_its_s0_and_the_compilations_records_for_that_paper`
- `tests/test_pilot_blindness.py::test_a_re_extraction_after_review_sees_no_review_reconciler_or_compilation_text`
- `tests/test_pilot_planner_request.py::test_an_ordinary_planner_request_is_byte_identical_to_mains`

### Spending and the agent core

```diff
diff --git a/hypocurate/pipeline/agents/lm.py b/hypocurate/pipeline/agents/lm.py
index 043bc97..85a9e8c 100644
--- a/hypocurate/pipeline/agents/lm.py
+++ b/hypocurate/pipeline/agents/lm.py
@@ -58,6 +58,7 @@ FAILURES: Mapping[str, tuple[str, str]] = {
     "malformed": ("the answer could not be read in the requested form", "correct"),
     "spending_cap_run": ("the run's spending cap would be exceeded", "stop"),
     "spending_cap_curation": ("the curation's spending cap would be exceeded", "stop"),
+    "spending_cap_document": ("the document invocation's spending cap would be exceeded", "stop"),  # Sprint 2 pilot
     "spending_cap_month": ("the monthly spending cap would be exceeded", "stop"),
     "ceiling_reached": ("the ceiling set for this call would be exceeded", "stop"),
     "invocation_unknown": ("no such invocation", "stop"),
diff --git a/hypocurate/pipeline/agents/settings.py b/hypocurate/pipeline/agents/settings.py
index 5836a47..25544ac 100644
--- a/hypocurate/pipeline/agents/settings.py
+++ b/hypocurate/pipeline/agents/settings.py
@@ -24,6 +24,10 @@ MODELS = MappingProxyType({
     "curator": "claude-sonnet-5-5",
     "critic": "claude-haiku-4-5",
     "analyst": "claude-opus-5-5",
+    # Sprint 2 pilot (owner, 2026-10-22, register 'pilot_extractor_models'): Sonnet for the first pass; Opus as a
+    # second method on the annotated papers is a later setting, added only after S0 scoring works.
+    "extractor": "claude-sonnet-5-5",
+    "reconciler": "claude-sonnet-5-5",  # R5 (2026-10-23), register 'pilot_reconciler_placement'
 })
 
 RUN_ROLES = ("planner", "critic", "analyst")
@@ -103,13 +107,61 @@ SETTINGS = MappingProxyType({
 })
 
 
+# Sprint 2 pilot: the Extractor's settings (register 'pilot_extractor_settings'). Its instructions are the versioned
+# prompt files, never text in code (Design D17); each setting names its step, prompt version and evidence specification.
+EXTRACTOR_PROMPT_VERSION = "v4"  # v1 sent once, refused as malformed (no schema in the request); v2 used on 2026-10-23
+# for the nine open-access papers; v3 (owner, 2026-10-23 evening): context from the methods in every record, every
+# item verified; v4 (owner, 2026-10-23): every listed condition is a record. FROZEN for the pilot (register
+# 'pilot_prompt_frozen'): further defects are findings, not re-extractions.
+EXTRACTOR_PROMPT_FROZEN = "v4"
+EXTRACTOR_STEPS = ("extract", "verify")
+EXTRACTOR_LIMITS = MappingProxyType({
+    # max_tokens covers thinking and answer; max_output_chars bounds the answer text.
+    "extract": MappingProxyType({"max_tokens": 32000, "max_output_chars": 200000}),
+    "verify": MappingProxyType({"max_tokens": 16000, "max_output_chars": 100000}),
+})
+EXTRACTOR_EFFORT = "medium"
+
+
+def extractor_variant(step: str, spec: str, prompt_version: str = EXTRACTOR_PROMPT_VERSION) -> Mapping[str, Any]:
+    """The Extractor's settings for one step and one evidence specification."""
+    from pathlib import Path
+    if step not in EXTRACTOR_STEPS:
+        raise ValueError(f"unknown extractor step {step!r}")
+    prompts = Path(__file__).resolve().parents[1] / "extraction" / "prompts" / prompt_version
+    instruction = (prompts / f"{step}.md").read_text(encoding="utf-8").strip()
+    if step == "extract" and prompt_version != "v1":  # from v2: the output schema is part of the instruction
+        instruction += "\n\nOutput schema:\n" + (prompts / "output_schema.json").read_text(encoding="utf-8").strip()
+    return MappingProxyType({
+        "instruction": instruction, "model": MODELS["extractor"], "limits": EXTRACTOR_LIMITS[step],
+        "settings": MappingProxyType({"reasoning_effort": EXTRACTOR_EFFORT, "step": step,
+                                      "prompt_version": prompt_version, "evidence_spec": spec}),
+    })
+
+
+RECONCILER_PROMPT_VERSION = "v1"
+RECONCILER_LIMITS = MappingProxyType({"max_tokens": 16000, "max_output_chars": 100000})
+
+
+def reconciler_variant(prompt_version: str = RECONCILER_PROMPT_VERSION) -> Mapping[str, Any]:
+    """The Reconciler's settings: its instruction is the versioned prompt file (Design D17)."""
+    from pathlib import Path
+    path = Path(__file__).resolve().parents[1] / "extraction" / "prompts" / "reconcile" / prompt_version / "reconcile.md"
+    return MappingProxyType({
+        "instruction": path.read_text(encoding="utf-8").strip(), "model": MODELS["reconciler"],
+        "limits": RECONCILER_LIMITS,
+        "settings": MappingProxyType({"reasoning_effort": EXTRACTOR_EFFORT, "prompt_version": prompt_version}),
+    })
+
+
 def _plain(value):
     return json.loads(json.dumps(value, default=dict))
 
 
-def ensure_setting(engine: Engine, role: str) -> int:
-    """The id of the stored settings version equal to `SETTINGS[role]`, adding the next version if none is."""
-    s = SETTINGS[role]
+def ensure_setting(engine: Engine, role: str, variant: Mapping[str, Any] | None = None) -> int:
+    """The id of the stored settings version equal to `SETTINGS[role]` (or to `variant`, the Extractor's settings
+    for one step and specification), adding the next version if none is."""
+    s = SETTINGS[role] if variant is None else variant
     limits, extra = _plain(dict(s["limits"])), _plain(dict(s["settings"]))
 
     def transaction(conn):
diff --git a/hypocurate/pipeline/agents/spend.py b/hypocurate/pipeline/agents/spend.py
index b2aac38..1082503 100644
--- a/hypocurate/pipeline/agents/spend.py
+++ b/hypocurate/pipeline/agents/spend.py
@@ -9,6 +9,7 @@ on a stale total. (Before the step 8a review fix a registration call read its to
 while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
 - a run: at most `RUN_CAP_USD` over all its calls;
 - a registration invocation (the Curator): at most `CURATION_CAP_USD` over its calls;
+- a document invocation (the Extractor, Sprint 2 pilot): at most `DOCUMENT_CAP_USD` over its calls;
 - the calendar month (UTC, by the database's start time): at most `MONTH_CAP_USD` over every call
   recorded in this database;
 - optionally a lower ceiling the caller names (the live curation call: $0.50, owner 2026-10-06),
@@ -45,10 +46,12 @@ LOG = logging.getLogger("hypocurate.pipeline")
 RUN_CAP_USD = Decimal("2")         # CLAUDE.md rule 12; register 'spending_caps'
 MONTH_CAP_USD = Decimal("50")      # CLAUDE.md rule 12; register 'spending_caps'
 CURATION_CAP_USD = Decimal("2")    # step 8a (owner, 2026-10-06): one curation, like one run
+DOCUMENT_CAP_USD = Decimal("2")    # Sprint 2 pilot (owner, 2026-10-22): one Extractor invocation on one document
 MONTH_LOCK_KEY = 0x68636D6F6E7468  # pg_advisory_xact_lock key of the monthly cap ("hcmonth")
 CODES = {
     "spending_cap_run": "the run's model calls would exceed the per-run cap",
     "spending_cap_curation": "the curation's model calls would exceed the per-curation cap",
+    "spending_cap_document": "the document invocation's model calls would exceed the per-document cap",
     "spending_cap_month": "the month's model calls would exceed the monthly cap",
     "ceiling_reached": "the calls would exceed the ceiling set for this call",
     "invocation_unknown": "no such invocation",
@@ -101,7 +104,7 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
                 raise ClaimLost("the run's claim was closed or its work lock is gone")
             stage = actual_stage(conn, inv.run_id, status)
         else:
-            stage = "registration"
+            stage = "document" if inv.scope == "document" else "registration"
         conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
         limit = ceiling
         if inv.scope == "run":
@@ -113,7 +116,8 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
         else:
             spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                       "WHERE invocation_id = :i"), dict(i=invocation_id)).scalar_one()
-            cap, cap_code = CURATION_CAP_USD, "spending_cap_curation"
+            cap, cap_code = ((DOCUMENT_CAP_USD, "spending_cap_document") if inv.scope == "document"
+                             else (CURATION_CAP_USD, "spending_cap_curation"))
         month = conn.execute(text(_MONTH_TOTAL)).scalar_one()
         code = (cap_code if spent + max_cost > cap else
                 "ceiling_reached" if limit is not None and spent + max_cost > limit else
```

**New or unchanged covering tests:**

- `tests/test_extractor.py::test_a_document_invocation_is_reserved_under_the_per_document_cap`
- `tests/test_pilot_spending.py (7 tests: extraction, verification under the document and the monthly cap, retry, Reconciler, refusal codes, cap values)`
- `tests/test_extractor.py::test_the_extractor_settings_come_from_the_versioned_prompt_files`

### The rules lock and the fixed plan

```diff
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index b9ae161..6f61256 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -33,6 +33,7 @@ from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
 from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
+from hypocurate.access.vocabulary import PILOT_SOURCE_KEYS
 from hypocurate.pipeline.writes import (CONSTRUCTED_MARK, TEST_RUN_LABEL, Refused, code_stage, constructed_unmarked,
                                         decide_sets, marked,
                                         flag_index,
@@ -69,6 +70,11 @@ def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
             if chosen - covered:
                 raise Refused("lock_rules", "invalid_plan",
                               f"{name} leaves out chosen sources: {', '.join(sorted(chosen - covered))}")
+        # Sprint 2 pilot (merge review A2, 2026-10-23): a plan may name a pilot source only when the run chose it.
+        named = set(rules["survivor_source_order"]) | {g["source"] for g in rules["grouping"]}
+        if (named & PILOT_SOURCE_KEYS) - chosen:
+            raise Refused("lock_rules", "invalid_plan", "the plan names a pilot source the run did not choose: "
+                          + ", ".join(sorted((named & PILOT_SOURCE_KEYS) - chosen)))
         ids = []
         for kind, value in tags.items():
             tid = conn.execute(text("SELECT id FROM tag_value WHERE kind = :k AND value = :v AND status = 'approved'"),
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
index 73af0dd..00ce507 100644
--- a/hypocurate/pipeline/confirmation.py
+++ b/hypocurate/pipeline/confirmation.py
@@ -105,19 +105,27 @@ def _planner_plan(conn: Connection, run_id: int, row) -> dict:
                               row.sufficiency_option)
 
 
-def reference_plan(row) -> dict:
-    plan = plans.reference_plan(row.hypothesis_version_id)
+def reference_plan(row, chosen=()) -> dict:
+    """The fixed plan; `chosen`, the run's source keys: a pilot source among them is added (Sprint 2, R9)."""
+    plan = plans.with_pilot_sources(plans.reference_plan(row.hypothesis_version_id), chosen)
     plan["sufficiency"]["option"] = row.sufficiency_option
     return plan
 
 
+def _chosen(conn: Connection, run_id: int) -> list[str]:
+    """The sources the run chose: run_source also lists the registered sources it did not choose (no version), as the
+    lock reads them (merge rehearsal, 2026-10-23: without this filter a registered pilot source entered every plan)."""
+    return list(conn.execute(text("SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id "
+                                  "WHERE rs.run_id = :r AND rs.source_version_id IS NOT NULL"), dict(r=run_id)).scalars())
+
+
 def plan_to_lock(conn: Connection, run_id: int) -> dict:
     """The plan the run will lock, built from stored rows only, or NotLockable."""
     row = _run(conn, run_id)
     if row.narrower_of_run_id is not None:
         return _narrower_plan(conn, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
     if row.fixed_plan:
-        return reference_plan(row)
+        return reference_plan(row, _chosen(conn, run_id))
     return _planner_plan(conn, run_id, row)
 
 
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index 6f92fee..44ef82c 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -87,6 +87,18 @@ def default_plan(hypothesis_version_id: int) -> dict:
     }
 
 
+def with_pilot_sources(plan: dict, chosen) -> dict:
+    """The plan with each pilot source the run uses appended last to the survivor order and to the grouping
+    (Sprint 2 pilot, R9); a plan for a run without one is returned unchanged."""
+    extra = [s for s in p.PILOT_SOURCES if s in set(chosen or ())]
+    if extra and p.PILOT_REREPORT_SURVIVOR != "compilation":  # the only survivor rule the pilot supports (register)
+        raise PlanError(f"re-report survivor {p.PILOT_REREPORT_SURVIVOR!r} is not supported in the pilot")
+    for s in extra:
+        plan["rules"]["survivor_source_order"].append(s)
+        plan["rules"]["grouping"].append({"source": s, "unit": p.PILOT_SOURCES[s]})
+    return plan
+
+
 def reference_plan(hypothesis_version_id: int) -> dict:
     """The fixed reference plan of acceptance criterion 14.1a (the Planner bypassed): the
     default plan under the owner's step 6 decisions."""
diff --git a/hypocurate/pipeline/profile.py b/hypocurate/pipeline/profile.py
index 562935a..e07a7e5 100644
--- a/hypocurate/pipeline/profile.py
+++ b/hypocurate/pipeline/profile.py
@@ -56,6 +56,14 @@ ACCEPTED_VALUE_STATUSES = ("converted", "assigned_from_source", "assigned_by_dec
 # The grouping unit of each source for the grouped standard errors (register 'tamu_grouping_unit',
 # 'paper_grouping_by_doi').
 GROUPING = MappingProxyType({"mpea": "paper", "tamu_fcc": "dataset", "controlled_duplicates": "paper"})
+# Sprint 2 pilot (R9; register 'pilot_extracted_source'): the 'extracted (pilot)' source, grouped by paper and last in
+# the survivor order (a re-report is counted once as the compilation's record). It enters a plan only when the run
+# uses it (`plan.with_pilot_sources`), so every plan without it is unchanged.
+PILOT_SOURCES = MappingProxyType({"extracted_pilot": "paper"})
+# Which value survives when an accepted re-report is counted once (owner, 2026-10-23; register
+# 'pilot_rereport_survivor'): the compilation's record. Read by `plan.with_pilot_sources`, which puts the pilot sources
+# after the compilation in the survivor order. The only value the pilot supports.
+PILOT_REREPORT_SURVIVOR = "compilation"
 
 # --- Data sufficiency (PRD 5.8; register 'fixed_minimums', 'sufficiency_options') ---------
 SUFFICIENCY_OPTION = "fixed_minimum"
```

**New or unchanged covering tests:**

- `tests/test_pilot_plan_lock.py (3 tests, one parametrized x3)`
- `tests/test_pilot_source.py::test_a_plan_without_the_pilot_source_is_unchanged_and_with_it_the_source_comes_last`
- `tests/test_pilot_source.py::test_the_re_report_survivor_setting_is_the_compilation_and_no_other_value_is_accepted`
- `tests/test_pilot_source.py::test_a_sprint1_run_on_a_database_holding_the_pilot_source_locks_a_plan_without_it`
- `tests/test_checkpoints.py (unchanged, passes)`

### The register's step value

```diff
diff --git a/hypocurate/assumptions.py b/hypocurate/assumptions.py
index 520b87c..1ca511c 100644
--- a/hypocurate/assumptions.py
+++ b/hypocurate/assumptions.py
@@ -57,6 +57,14 @@ STATES = {"in_force": "In force", "open": "Open decision",
           "direction_approved": "Direction approved, pending technical review"}
 APPLIED = {"yes": "Yes", "partly": "Partly", "not_yet": "Not yet"}
 BUILD_STEPS = range(5, 13)  # PRD 15, steps still to come
+# Sprint 2's pilot (owner, 2026-10-22): its entries name the pilot as their step; BUILD_STEPS is unchanged, so no
+# Sprint 1 entry is read differently.
+PILOT_STEPS = ("pilot-2",)
+STEP_RULE = "a build step from 5 to 12, or the pilot step 'pilot-2'"
+
+
+def step_ok(step: Any) -> bool:
+    return (isinstance(step, int) and not isinstance(step, bool) and step in BUILD_STEPS) or step in PILOT_STEPS
 
 FIELDS = {"key", "name", "state", "statement", "value", "category", "affects", "reason", "evidence",
           "decided", "expert_review", "sensitivity", "applied", "tests", "history", "notes"}
@@ -138,8 +146,8 @@ def _validate_entry(where: str, e: Any) -> None:
     if state in PENDING_STATES:
         _keys(f"{where}.pending", e["pending"], {"by", "before_step"})
         _text(f"{where}.pending.by", e["pending"]["by"])
-        if e["pending"]["before_step"] not in BUILD_STEPS:
-            raise RegisterError(f"{where}.pending.before_step: a build step from 5 to 12")
+        if not step_ok(e["pending"]["before_step"]):
+            raise RegisterError(f"{where}.pending.before_step: {STEP_RULE}")
     if e["category"] not in CATEGORIES:
         raise RegisterError(f"{where}.category: one of {list(CATEGORIES)}")
     if not isinstance(e["evidence"], list) or not e["evidence"]:
@@ -215,8 +223,8 @@ def _validate_applied(where: str, applied: Any) -> None:
             _keys(where, applied, {"status", "settings", "done", "pending", "step", "note"})
             _text(f"{where}.done", applied["done"])
             _text(f"{where}.pending", applied["pending"])
-            if applied["step"] not in BUILD_STEPS:
-                raise RegisterError(f"{where}.step: a build step from 5 to 12")
+            if not step_ok(applied["step"]):
+                raise RegisterError(f"{where}.step: {STEP_RULE}")
         if not isinstance(applied["settings"], list) or not applied["settings"]:
             raise RegisterError(f"{where}.settings: applied in code needs at least one named setting")
         for j, s in enumerate(applied["settings"]):
@@ -224,8 +232,8 @@ def _validate_applied(where: str, applied: Any) -> None:
             _text(f"{where}.settings[{j}].ref", s["ref"])
     else:
         _keys(where, applied, {"status", "step", "note"})
-        if applied["step"] not in BUILD_STEPS:
-            raise RegisterError(f"{where}.step: a build step from 5 to 12")
+        if not step_ok(applied["step"]):
+            raise RegisterError(f"{where}.step: {STEP_RULE}")
     _text(f"{where}.note", applied["note"], optional=True)
```

**Test changes beside it:**

```diff
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index ea91098..9ecec2b 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -61,7 +61,7 @@ def test_every_category_has_entries_and_keys_are_unique():
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
 # Step 10a: question_as_tested fully applied (the website's Confirm button).
-PARTLY: set = set()  # step 10b: constructed_test_runs fully applied (its label on every screen); step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
+PARTLY: set = {"pilot_extractor_models"}  # Sprint 2 pilot (2026-10-23): the Opus second method pending; step 10b: constructed_test_runs fully applied (its label on every screen); step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -591,3 +591,19 @@ def test_the_service_does_not_start_with_an_invalid_register():
 
 def test_the_home_page_links_to_the_register():
     assert 'href="/assumptions"' in signed_in().get("/").text
+
+
+def test_the_pilot_step_is_accepted_beside_build_steps_5_to_12():
+    """Sprint 2 (owner, 2026-10-22): pilot entries name 'pilot-2' as their step; BUILD_STEPS stays 5 to 12, so no
+    Sprint 1 entry is read differently."""
+    from hypocurate import assumptions as reg
+    assert reg.BUILD_STEPS == range(5, 13) and reg.PILOT_STEPS == ("pilot-2",)
+    for step, ok in (("pilot-2", True), (5, True), (12, True), ("pilot-3", False), (13, False), (4, False),
+                     (True, False), ("5", False)):
+        e = copy.deepcopy(BY_KEY["session_length"])
+        e.update(applied={"status": "not_yet", "step": step, "note": None}, tests=[])
+        if ok:
+            reg.validate([e])
+        else:
+            with pytest.raises(reg.RegisterError, match="build step from 5 to 12, or the pilot step"):
+                reg.validate([e])
```

### Migration 0010's place in the existing migration tests

**Test changes beside it:**

```diff
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 9088724..8df7590 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -73,6 +73,9 @@ def expected_triggers() -> set[tuple[str, str]]:
     m9 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0009").module  # step 10b, fix round 1
     names |= {(t, f"hc_{t}_append_only") for t in m9.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m9.APPEND_ONLY}
     names |= {(t, trigger) for t, _, trigger, _ in m9.CHECKED}
+    m10 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0010").module  # Sprint 2 pilot (R1)
+    names |= {(t, f"hc_{t}_append_only") for t in m10.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m10.APPEND_ONLY}
+    names |= {(t, trigger) for t, _, trigger, _ in m10.CHECKED} | set(m10.CONSTRAINT_TRIGGERS)
     return names
 
 
diff --git a/tests/test_migrations_step10b.py b/tests/test_migrations_step10b.py
index 9f0e9b7..9436384 100644
--- a/tests/test_migrations_step10b.py
+++ b/tests/test_migrations_step10b.py
@@ -46,8 +46,9 @@ def insert(w, action="create", channel="website", actor="Ada", v=None, r=None, s
 
 # --- the migration ------------------------------------------------------------------------------------------
 
-def test_0009_is_the_head_and_follows_0008():
-    assert migrate.head_revision() == "0009" and m0009().down_revision == "0008"
+def test_0009_follows_0008():
+    # Sprint 2 (2026-10-22): 0010 follows 0009, so 0009 is no longer the head (tests/test_migrations_step0010.py).
+    assert m0009().down_revision == "0008" and SCRIPTS.get_revision("0010").down_revision == "0009"
 
 
 def test_0009_replaces_no_earlier_function():
@@ -86,7 +87,7 @@ def test_the_downgrade_refuses_while_an_action_is_recorded(db):
     before = snapshot(db)
     with pytest.raises(Exception, match="0009 is in use"):
         migrate.downgrade(db, "0008")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0009"
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
 
 
 def test_the_lists_are_the_codes():
@@ -183,5 +184,5 @@ def test_the_downgrade_waits_for_an_uncommitted_action_and_then_refuses(db):
         t.join(120)
     assert not t.is_alive()
     assert "0009 is in use" in outcome["result"], outcome
-    assert migrate.current_revision(db) == "0009"
+    assert migrate.current_revision(db) == migrate.head_revision()
     assert w.val("SELECT actor FROM action_record") == "Ada"
```

**New or unchanged covering tests:**

- `tests/test_migrations_step0010.py (33 test functions; new file)`

### The parse lock kept out of the image

**Test changes beside it:**

```diff
diff --git a/tests/test_skeleton.py b/tests/test_skeleton.py
index 4156e33..b766da2 100644
--- a/tests/test_skeleton.py
+++ b/tests/test_skeleton.py
@@ -131,6 +131,25 @@ def test_direct_dependencies_are_locked():
     assert direct_dependencies("dev") <= set(locked("requirements-dev.lock"))
 
 
+# Sprint 2 pilot (owner, 2026-10-22, register 'parser_choice'): the parsers live only in the parse environment.
+PARSE_PACKAGES = {"docling", "pymupdf", "torch", "torchvision"}
+
+
+def test_the_parse_lock_is_pinned_with_hashes_and_matches_its_input():
+    names = re.findall(r"^([A-Za-z0-9_.-]+)", read("requirements-parse.lock"), re.M)
+    pins = locked("requirements-parse.lock")
+    assert names and set(n.lower().replace("_", "-") for n in names) == set(pins)
+    wanted = dict(re.findall(r"^([A-Za-z0-9_.-]+)==(\S+)$", read("requirements-parse.in"), re.M))
+    assert set(wanted) == PARSE_PACKAGES and all(pins[k] == v for k, v in wanted.items())
+
+
+def test_the_parsers_are_in_no_project_lock_and_no_image():
+    for path in ["requirements.lock", "requirements-dev.lock"]:
+        assert not PARSE_PACKAGES & set(locked(path)), path
+    for path in ["Dockerfile", "docker-compose.yml", "render.yaml", ".github/workflows/tests.yml"]:
+        assert "requirements-parse" not in read(path) and "docling" not in read(path).lower(), path
+
+
 def test_runtime_and_dev_locks_agree():
     runtime, dev = locked("requirements.lock"), locked("requirements-dev.lock")
     assert {n: dev[n] for n in runtime} == runtime
```

