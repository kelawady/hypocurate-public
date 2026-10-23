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

**Revert:**
- **Before the bundle is loaded:**
  1. `git revert -m 1 <merge commit>` on main, then push (Render redeploys the old code).
  2. Then `python -m hypocurate.db.migrate downgrade 0009` against the live database. It succeeds because 0010 holds
     no data and no row uses a pilot role.
  - Either order works: old code never reads 0010's tables, and the two replaced functions keep Sprint 1's behaviour.
    The downgrade is the step that returns the schema to 0009.
- **After the bundle is loaded:**
  - The downgrade refuses by design: 0010 never drops data.
  - The way back is the second backup, taken just before the load. Restoring it returns the database to 0010 with no
    pilot data, and then the steps above apply.
  - Restoring the first backup returns to 0009 directly. On Render, a restore goes into a new database and may be paid;
    the owner decides.

## 8. Questions for the reviewer

1. Is enforcing the acceptance matrix at the freeze (rather than inside Sprint 1's inclusion) acceptable for the pilot,
   given that inclusion only ever sees accepted records through the sealed source?
2. Does any path let a Sprint 1 run (no pilot source chosen) reach `with_pilot_sources` with a non-empty result?
3. Is the downgrade's refusal list (0010 data, the document scope, pilot roles in four tables) complete?
4. Is any edit in section 5's test list a weakening?
