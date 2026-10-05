# Build step 6 — fix packet for the second model's re-check

Date: 2026-10-06. Branch: `step-06-eligibility`. Fixes for the first review (`docs/reviews/step06_review_chatgpt.md`), from `bb71e0c` (the reviewed packet's code plus the owner's decisions of 2026-10-06) to `3f2872e`. Generated from the files and commits on disk by a script. The full packet of the first build is `docs/reviews/step06_review_packet.md`.

## How to use this packet

The owner accepted all six findings and decided that the primary set's handling of conflicts, exact duplicates, invalid values and unresolved-identity groups is a fixed rule, not a plan default. Each fix is one commit with the tests that failed on the code before it (commit messages give the counts). Section 1 is the step summary, rewritten for the state after the fixes; its section "Second-model review and fixes" maps each finding to its fix and tests, and "Tests changed" lists every test changed and why. **No reference number changed** (section 4).

Please return a dated re-check: for each finding, closed, partly closed or open, and any new finding.

## Contents

1. Step summary (after the fixes)
2. The review
3. The fixes, commit by commit (message and full diff)
4. Reference numbers recomputed after the fixes
5. Mutation checks

## Commits

```
fe09cbe Step 6 fix: fixed rules for the primary set, not plan defaults
d52f771 Step 6: second-model review, saved verbatim
23c24b2 Step 6 fix: the extraction check requires present, string-typed fields
1821dcd Step 6 fix: survivors and groups never depend on database ids
e7d62ab Step 6 fix: the freeze fingerprint uses stable record identity
b78f01c Step 6 fix: ambiguous groups keep their conflicts
65f76f9 Step 6 fix: sensitivity sets recompute their matching flags
cbf99d1 Step 6 fix: Checks are bound to the exact records they covered
ac846a4 Step 6 fix: wording that the code supports
4babe82 Step 6 fix: answer-file rows 15-16 explanation for the tension-only plan
af536cc Step 6 fix: test that storage refuses after Checks
3f2872e Step 6 fix: test that no record is stored after Checks
```

## 1. Step summary

````markdown
# Build step 6 — summary for review

Date: 2026-10-06. Branch: `step-06-eligibility`. **Status: first build reviewed by the second model (ChatGPT, 2026-10-06: "serious correctness gaps", six findings, hold step 6); the owner accepted all six with a decision on the primary set; fixes built, each with tests that failed on the code before it; for the re-check.** PRD Section 15, step 6: "Plan, checkpoints, inclusion and checks. The plan model, the rules lock and the dataset freeze, the domain profile and tags, exclusion and eligibility rules, and the code checks that raise flags."

The suite is the gate. This summary is for the second model, which uses `docs/reviews/checklist.md`. The review is `docs/reviews/step06_review_chatgpt.md` (saved verbatim); the first packet is `docs/reviews/step06_review_packet.md`, the fix packet `docs/reviews/step06_fix_packet.md`. **It describes the state after the fixes**; section "Second-model review and fixes" maps each finding to its fix and tests.

**Not built, as instructed:** any agent or model call, the statistics module (step 7), screens, registering sources on the live database. Plans are fixed inputs; there is no Planner. **Two migrations**, approved by the owner with their reasons (section "Migrations"). No change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose or dependencies. No PRD document is changed; corrections are listed at the end.

## The owner's decisions in planning (2026-10-05)

The plan was approved after nine questions, a decision on conflicts (C), two changes and one clarification. They are folded in verbatim below and recorded in the register.

1. **Possible duplicates.** Duplicates and conflicts are compared only between different sources; rows within one source are separate measurements. Same paper and every condition known: an exact duplicate (yield strengths within 2%) or a conflict (beyond 2%). The paper or a test condition missing on one side and the rest matching (alloy, grain size, value within 2%): a possible duplicate, counted once by the survivor rule, both in `possible_duplicates_separate`. **Owner's addition:** a record with a missing test condition is also "scope not confirmed"; state the order of the two rules and the record's single decision, and test it against the answer file. Order: Checks raises the `possible_duplicate` flag (kept regardless); Inclusion applies `scope_not_confirmed` (rule 5) before the duplicate rule (rule 7). Extract rows 13–14: the extract record is not eligible, `scope_not_confirmed`; its MPEA twin survives.
2. **One change per sensitivity set.** Each sensitivity set differs from the primary set in exactly one named respect, and every other rule (counted once included) applies unchanged. Tested for every set the reference plan names. The answer file's "included" for rows 13–14 is read this way: in `scope_not_confirmed_included` the scope no longer excludes the record, and the duplicate rule still counts the measurement once.
3. **`PLAN_SCHEMA` extended** with every setting that affects which records are eligible or how they are grouped, and the domain profile and version the defaults came from. A test fails if eligibility or grouping code reads such a value from anywhere other than the locked plan.
4. **Tag lists seeded by migration 0002** (data only; safe on a database that already has some values; works with the previous release's code; up/down/up tested; "down" leaves the rows). The live deploy is checked with the owner at the merge.
5. **Eight sensitivity sets** (the table below). The reference script's "discretionary removals" analysis is not carried over: those records were chosen after seeing outcomes, so it cannot be named in a plan locked before the data. Sensitivity results are descriptive, never change the verdict, and no adjustment is made for there being eight.
6. **Grain size within 2% to pair.** Grain size is a matching criterion, not something that can be in conflict: records whose grain sizes differ by more than 2% are separate measurements, so a grain-size disagreement between sources can never raise a conflict flag (known limit, recorded). **A tolerance is not exclusive:** if a record has more than one candidate in another source, nothing is paired automatically and all are flagged as possible duplicates.
7. **Code roles.** `dispatch.bind_code` for Inclusion and Checks; Inclusion is blind to outcomes. **Guaranteed:** Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. **Not claimed:** that outcomes play no part at all, since Checks compares values to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds. Tested: Checks uses no model, slope, residual or plan hypothesis.
8. **The test mark** `run.experiment_flags = {"constructed_test_data": true}`, set at dispatch. A marked run may freeze, be analysed and complete normally, verdict included, so that acceptance 14.1 ("Duplicates") and the 14.7 demonstration can be shown. Every place a marked run's outcome, verdict or numbers are stored or shown carries "test run: includes constructed data"; marked runs are excluded from every aggregate, count or list of real results; an unmarked run refuses constructed records at three points. **PRD 14 check: no criterion conflicts.** Notes: 14.7 needs the extract registered on the live database (the step 11 decision); PRD 4's experiment flag (the contract's relaxation) is unaffected, as the mark relaxes nothing.
9. **Vocabulary additions approved:** rule `missing_value`; sensitivity key `no_exclusions`; flag category "several candidates".
10. **The rest as recommended:** (a) flags only for duplicates, conflicts, possible duplicates and invalid values; (b) a refused change after either checkpoint is logged by our write path, in its own transaction (the named exception extended); (c) records stored by the adapters from the run's sealed versions, **on two conditions:** each record states how it was extracted (adapter, name and version), and the Curator's role for tabular sources is an **open owner decision for step 8**, not settled here; (d) the step 1 answer file, builder and README take the restored survivor wording, with the pinned fingerprint updated; the frozen extract is unchanged, and non-MPEA survivors are constructed test records; (e) CLAUDE.md's "Reference numbers" change only after the owner approves them.
11. **Migration 0003** for `record.extraction`: additive; 0001 and 0002 untouched; the replaced insert trigger keeps every 0001 check and adds only the new one (the packet shows old and new side by side). Both migrations are in the up/down/up and failure-rollback tests. The live deploy is checked with the owner at the merge.

**Decision C (conflicts).** Asked to quote PRD 5.3 and the answer file:
- PRD 5.3, "Comparable specimens and conditions; the values truly differ": "Both enter, with records grouped by paper in the model." Sensitivity: "None".
- truth.csv rows 7–8: primary "both enter", sensitivity "none".
- CLAUDE.md rule 4: "Conflicting records are preserved, not automatically pooled."

The owner decided: **neither enters the primary set**; a new eighth set `conflicts_survivor_value` counts the group once by the survivor rule. The same principle applies to ambiguous groups: none of their records enters the primary set (new rule `identity_unresolved`), and all enter `possible_duplicates_separate`. Its one change is "records of unresolved or possible duplicate groups are counted as separate measurements", which is a single change: both cases are an unresolved identity, while exact duplicates (identity resolved) stay counted once and conflicts (identity resolved, values not) stay out. PRD 5.3's row is corrected (it contradicted CLAUDE.md rule 4), and the answer file's rows 7–8 with it.

**Owner's changes at approval:**
- **Rule order:** duplicates are resolved before grain sizes are counted (rule 7 before rule 8). An alloy whose only two records are a cross-source duplicate pair at 1.79 and 1.8 µm is not eligible (tested).
- **Fixed minimums: where and when** (section "The dataset freeze").
- **Open owner decision for step 7:** what a run below the fixed minimums may show. The owner's starting position: the counts and which minimums were not met, and nothing derived from outcome values, not even a coefficient, so that the sufficiency option cannot be chosen after seeing an estimate. Not built.
- "Seven" became "eight" everywhere; the eight sets are listed in one place below.

## The owner's decisions after the first build (2026-10-06)

1. **The recomputed reference numbers are approved.** CLAUDE.md's "Reference numbers" now state them. A new register entry, `reference_numbers` (statistical; decided by the owner on 2026-10-06; partly applied), holds them, with the earlier values (98 / 77 records, k = 428 ± 64 and 427 ± 61) in its history. The statistics module in step 7 must reproduce them independently: the step 6 values come from a test-side script, not from package code. The record counts are regression tests already; the coefficients become tests in step 7.
2. **The answer file's rows 15–16** now describe the reference plan with its test-type rule. In both rows:
   - `prd_5_3_class` "Within scope under the reference plan: distinct measurements, not duplicates" → "Incompatible measurements: outside the plan's scope (test-type rule: tension only)";
   - `primary_analysis` "both enter under the reference plan (it sets no test-type rule)" → "not eligible: excluded by the test-type rule (tension only)".
   The pinned fingerprint is updated (`8ff53837…`), and the extract is unchanged. The rows' `explanation` cells were corrected after the review, in that round's one fingerprint update (section "Second-model review and fixes").
3. **The constructed-data guard stays in code.** A database rule goes to the backlog: a note in register entry `constructed_test_runs`, and PRD correction 16.

## Second-model review and fixes (ChatGPT, 2026-10-06)

The owner accepted all six findings, decided that the primary set's handling of conflicts, exact duplicates, invalid values and unresolved-identity groups is a fixed rule (not a plan default), approved the fix plan, and asked for each fix to come with a test that fails on the code before it. **Every new test below failed on the code before its fix** (counts in the commit messages and the table), except those marked as regressions.

| Finding | Fix | New tests (failed before the fix) |
|---|---|---|
| **Owner's decision** (review: "conflict policy is a default, not an invariant") | `eligibility.FLAG_RULE_CHOICES`: each flag kind's allowed rules. Exact duplicate: counted once. Conflict: neither (default) or the survivor's value once. Invalid value: never. Ambiguous group: never (counted separately only in `possible_duplicates_separate`). Possible duplicate: counted once (default) or both. `plan.validate` refuses anything else at the lock, and `eligibility.settings` refuses it again. Register `primary_set_invariants` lists the six things no plan can do, with a test for each, and is shown on the assumptions page. | `test_no_plan_can_put_these_records_in_the_primary_set` (5 cases); eight new cases in `test_invalid_plans_are_refused` (13 failed in all); `test_the_fixed_rules_hold_in_every_set_the_plan_names` and `test_the_plan_choices_that_remain` are regressions (passed before) |
| 1. Checks skipped or stale | Checks run only when no chosen source is pending; storage refuses after Checks; the Checks result records its **binding** (a hash of the record collection by stable identity, and of its flags); Inclusion and the freeze refuse (`checks_not_done`, `checks_not_current`) unless it matches. | `test_skipping_checks_is_refused_at_inclusion_and_the_freeze`, `test_checks_wait_until_every_chosen_source_is_stored`, `test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze` (real conflicting rows 7–8; all 3 failed); `test_no_record_is_stored_after_checks` (added after the mutation checks) |
| 2. Coarser alloy rule reuses primary flags | Checks computes, for each sensitivity set whose matching settings (same-alloy step, accepted value statuses, grouping) differ, its own duplicate, conflict and ambiguity flags, stored with its result as codes and ids. Inclusion reads them through a new field `set_flags`; each set applies its own flags, every other rule unchanged. | `test_the_coarser_same_alloy_rule_recomputes_the_duplicates` (the reviewer's example through the real pipeline; failed: 4 records where 2 are right); `test_every_other_set_keeps_the_primary_flags`; `test_the_one_change_rule_holds_with_recomputed_matching_flags` |
| 3. Survivor depends on insertion order | The lock refuses a survivor order or a grouping that leaves out a chosen source (validation refuses empty lists); the final tie-breaker is (source, origin key, item index), never a database id; `record_conditions` carries that identity. | `test_the_survivor_does_not_depend_on_database_ids_or_insertion_order` (failed with an incomplete order); `test_the_lock_refuses_settings_that_leave_out_a_chosen_source` (4 failed) |
| 4. Ambiguous groups hide a conflict | Checks adds a `values_disagree` flag for the conflicting pair inside an ambiguous group; Inclusion applies rule 7 in a fixed order (unresolved identity, conflict, counted once). | `test_an_ambiguous_group_keeps_its_conflict_in_every_set` (the reviewer's three-source example; checks the resulting sets; failed) |
| 5. Fingerprint depends on database ids | Records are identified in the fingerprint's sets and rules by (source-version fingerprint, origin key, item index) and their content hash. | `test_the_fingerprint_does_not_depend_on_database_ids` (two runs of one version in one database, unrelated records in between; failed) |
| 6. Extraction check accepts a missing method | 0003 changed in place (it has not run on the live database; the local development database is at 0001): every key a JSON string, the whole check coalesced to true or false. | `test_0003_refuses_a_missing_null_or_wrongly_typed_extraction_field` (13 cases: 6 failed; the others were already refused and stay as regressions) |
| Wording | "Pairwise comparisons feed whole-group classification"; "every setting from the plan" narrowed to plan settings, with the **fixed policies in code** listed (`eligibility.py`; register `fixed_policies_in_code`); "±" labelled one standard error, not a confidence interval (CLAUDE.md, register, this summary); unknown source definitions should fail closed (noted for a later step). | — |
| Answer file rows 15–16 | `explanation` describes the tension-only plan, in this round's one fingerprint update (`e6e859cd…`). | the test checks the new text |

**What the fixes do not do:**
- The constructed-data guard stays in code (owner, 2026-10-06).
- A source refused by that guard stays pending, so Checks cannot run on that run until the source is marked failed. The run's orchestration (step 9) must do that (register `checks_bound_to_records`).
- The plan names its hypothesis version by database id, so the freeze fingerprints of runs of different versions differ, by design.

**Reference numbers after the fixes:** recomputed with the same scripts; **none changed**. Records, alloys, groups, residual df, k, standard errors and p-values are identical for every set. The freeze fingerprint's value changed, because it is now computed from stable identities (`93c44b22…`, was `3440e972…`); it is not a reference number.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/pipeline/profile.py` | The domain profile: one named constant per default (scope, floor, tolerance, survivor order, minimums, statuses, grouping, sensitivity keys, tags), with its name and version. |
| `hypocurate/pipeline/plan.py` | The plan model: `default_plan`, `reference_plan`, `validate` (content must equal its own `PLAN_SCHEMA` projection and fit the template), canonical JSON and fingerprint, `tags_for`. |
| `hypocurate/pipeline/checkpoints.py` | `lock_rules` (plan, fingerprint, three tags, one transaction) and `freeze_dataset` (re-derives and verifies the sets, records the counts and the fingerprint, or "no dataset frozen"). |
| `hypocurate/pipeline/extract.py` | Record storage after the lock: each chosen source's sealed version read by its adapter, with `record.extraction`. |
| `hypocurate/pipeline/flags.py`, `checks.py` | Checks: the flag rules (pure) and the write path. |
| `hypocurate/pipeline/eligibility.py`, `inclusion.py` | Inclusion: one rule per record for the primary and the eight sensitivity sets (pure), the counts known at the freeze, and the write path. |
| `hypocurate/pipeline/writes.py` | The shared write path: lock protocol, re-checks, refusals logged. |
| `hypocurate/access/allowlist.py`, `vocabulary.py`, `fields.py`, `dispatch.py`, `layer.py` | Code roles and their lists, `record_conditions`, `bind_code`; `PLAN_SCHEMA` `rules` and `profile`, and a flag category in eligibility rules; the approved new codes. |
| `hypocurate/sources/record.py`, `adapters/*`, `normalize.py`, `versions.py`, `connection.py` | The two assigned statuses; Texas A&M band and microstructure by decision; adapter names and versions; `same_alloy_key(…, decimals)`; `identity_hash`; `constructed` on the source definition. |
| `hypocurate/db/migrations/versions/0002_tag_starting_lists.py`, `0003_record_extraction.py`, `models.py` | The two migrations and the model column. |
| `hypocurate/assumptions.json` | The register (section "Assumptions register"). |
| `tests/fixtures/controlled_duplicates/*` | The answer file, builder and README (restored survivor wording; decision C). |
| `README.md`, `scripts/check_runtime_image.py` | A pipeline section; the image must contain the new modules and migrations. |

## The plan

The plan's content follows `PLAN_SCHEMA` exactly: `validate` refuses content its projection would change (unknown key, free text, value outside a vocabulary, wrong type), content missing a part, and content outside the sprint-1 template (for example a band other than room temperature, a predictor other than grain size in µm, a range rule without bounds). New parts:

- `rules`: `same_alloy_decimals`, `duplicate_tolerance`, `survivor_source_order`, `min_grain_sizes`, `room_temperature_min/max`, `single_phase`, `accepted_value_statuses`, `grouping` (source → unit);
- `profile`: name and version of the domain profile the defaults came from;
- `eligibility_rules` entries may name a flag `category` (an ambiguous group is `possible_duplicate` / "several candidates"). This leaf was not listed at approval; it falls under "every setting that affects eligibility" and is reported here as a deviation.

Already present and used as the settings they are: permitted test types (`scope.test_type`), the minimum grain size (`exclusion_rules`), the four minimums (`sufficiency`).

**The reference plan** (criterion 14.1a) is the default plan under the owner's decisions: scope MPEA class / room temperature / tension / FCC (single phase); exclusion grain size ≥ 0.1 µm; fixed minimums 30, 5, 10, 10; the eligibility rules of PRD 5.3 as decided; the eight sensitivity sets.

**Plan settings come only from the locked plan** (owner, 2026-10-05; narrowed after the review): some policies are fixed in code for every plan and are listed in `eligibility.py` and register entry `fixed_policies_in_code`. The decision code (`eligibility.py`, `flags.py`, `checks.py`, `inclusion.py`, `checkpoints.py`) imports nothing from the profile (import scan), and two behavioural tests show it:
- for each setting, a plan whose value differs from the default changes the decision accordingly;
- with every profile constant replaced, the decisions under the same plan do not change.

**What the plan does not hold:** the change each sensitivity key applies (for example "1 at.%" for `same_alloy_1_at_pct`) is fixed by the key itself, in code (`eligibility.SENSITIVITY_CHANGES`), not by a number in the plan. The key names the change, and adding or changing one is a vocabulary change needing the owner's approval.

## The rules lock

`lock_rules(engine, run_id, content)`: validates the plan, then in one `run_transaction` takes `hc_write_lock(p_run)`, checks the run is before the lock and that the plan names the run's hypothesis version, looks up the three approved tag values (property, alloy class, test condition; one per kind), and inserts the plan (content, fingerprint, the database's time) and the three `run_tag` rows. The database already refuses a second plan, any change to a plan, and tags outside the lock's transaction (migration 0001). Our path refuses and logs a second lock or a changed plan, an invalid plan, and a plan for another version (PRD 14.2).

## Records, checks and inclusion

**Record storage** (`extract.store_records`): one transaction per source, under the run's lock. The adapter reads the sealed version the run recorded; every record is stored unchanged and in file order with `record.extraction` (`{"method": "adapter", "name": …, "version": …}`), and the source becomes `searched`. A file the adapter refuses makes the source `failed` / `failed_search`, with nothing stored. Storage reads the sealed version directly, not through an access object: it is code (adapters), approved under (c). The Curator's role for tabular sources is open for step 8.

**Checks** (`flags.py`, `checks.py`) read through their access object (`plan`, `records_full`) and raise:
- `invalid_value` / "physically impossible": tensile strength below yield strength, or a grain size of zero or less (one flag per record);
- duplicate groups, **between different sources only**. Two records are candidates when they have the same alloy (plan's same-alloy rule), grain sizes within the tolerance, and nothing known that differs (the same paper or one unknown; the same test type and temperature, or one unknown). Then:
  - same paper and every condition known: an **exact duplicate** if the yield strengths are within the tolerance, a **conflict** (`values_disagree`) if beyond it;
  - the paper or a condition unknown on one side: a **possible duplicate** if the yield strengths are within the tolerance, otherwise not a candidate.
  - Candidate links form groups. A group with two or more records from one source, **or one whose records are not all linked to each other**, is ambiguous ("several candidates"). The second condition is mine; it stops a chain A–B–C from pairing A and C when they are known to differ. Otherwise a group with a conflicting pair is a conflict, a group with a possible link is a possible duplicate, and the rest are exact duplicates.
- A source grouped by dataset (Texas A&M) cites itself, so its records never pair with a record citing another paper.
- The numbers compared are stored in `flag.compared_values` for audit only.

**Inclusion** (`eligibility.py`, `inclusion.py`) reads through its access object (`plan`, `record_conditions`, `flags_kind`). `record_conditions` carries no outcome value and no value as reported:
- statuses of every field;
- grain size and test temperature;
- category values through their vocabularies;
- the paper (from the DOI) and the Texas A&M batch as SHA-256 hashes;
- whether the record carries a DOI, the row number from the origin key, and a hash of the stored record.

### The eligibility rules (one per record, the first that applies; settings from the locked plan)

| # | Rule code | What it checks | Decision recorded |
|---|---|---|---|
| 1 | `model_recalled` | the record's kind is model-recalled | not eligible |
| 2 | `invalid_value` | a flag the plan maps to `invalid_value` | not eligible |
| 3 | `out_of_scope` | a known value outside scope: test type not permitted; reported temperature outside 20–25 °C, or band not room temperature; microstructure known and not exactly FCC | not eligible |
| 4 | `missing_value` | composition, grain size or outcome without an accepted value | not eligible |
| 5 | `scope_not_confirmed` | a scope value missing, or held with a status the plan does not accept | not eligible; in `scope_not_confirmed_included` |
| 6 | `excluded_by_rule` | a menu exclusion rule (grain size below 0.1 µm) | not eligible |
| 7 | `identity_unresolved` / `conflict_unresolved` / `duplicate_counted_once` | among records passing 1–6: an ambiguous group; a group with a conflict; not the survivor of an exact or possible duplicate group | not eligible |
| 8 | `single_grain_size` | the alloy has fewer than two distinct grain sizes among records passing 1–7 | not eligible |
| 9 | `in_scope` | none of the above | eligible: primary set |

Room temperature: a reported temperature decides; with none reported, the band decides if its status is accepted (Texas A&M: "room temperature", assigned by decision). Single phase: the microstructure exactly equals a scope phase class; the phase column is not used. Alloy class is not checked per record (records carry no alloy-class field): it is a scope label and a tag. The survivor rule: the record carrying the original paper reference (DOI); then the plan's source order (MPEA, Texas A&M, extract); then the lowest row. Rule 1 can only decide a possible duplicate, since paired records otherwise cite the same paper.

### The eight sensitivity sets (one named change each; every other rule unchanged)

| Key | Its one change from primary |
|---|---|
| `no_exclusions` | the menu exclusion rules are dropped (the grain-size floor); the scope is kept |
| `tension_and_compression` | permitted test types: tension and compression |
| `six_batches_as_groups` | Texas A&M grouped by its batches (the same records as primary) |
| `same_alloy_1_at_pct` | the same-alloy rule rounds to 1 at.% |
| `source_only_assignments` | accepted value statuses: converted and assigned from source only |
| `scope_not_confirmed_included` | records whose scope cannot be confirmed are treated as in scope |
| `possible_duplicates_separate` | records of unresolved or possible duplicate groups count as separate measurements |
| `conflicts_survivor_value` | conflict groups are counted once by the survivor rule |

Descriptive only; they never change the verdict; no adjustment for there being eight.

**Writes.** One transaction under the run's lock writes a decision for every record (`run_record`: eligible exactly when the rule is `in_scope`, with its rule), every set (`analysis_set`, `analysis_set_record`), and a code `stage_result` "inclusion" listing, per sensitivity set, the rules that differ from the primary set's, the totals and the named changes.

## The dataset freeze

`freeze_dataset` reads through Inclusion's access object, recomputes every set from the locked plan, the record conditions and the flags, then in one locked transaction:
1. refuses constructed records in an unmarked run;
2. re-checks the records and flags by id against what it read;
3. checks that the stored decisions and sets are exactly what the locked rules produce. These are read from the decision tables by SQL (ids and codes only, no record value), not through an access object;
4. writes a code `stage_result` "dataset_freeze" with the counts and the fingerprint;
5. writes `run_snapshot`, or, with no eligible record, the run-level "no dataset frozen" row.

**The fingerprint** is the SHA-256 of the canonical JSON of the plan's fingerprint, each set's records (id and a hash of the stored record) and rules, and the counts. Running the same steps on another database gives the same fingerprint, counts and decisions (tested).

**Fixed minimums: where and when** (owner's clarification):
- **Known at the freeze, computed by step 6 from structure and grain sizes only, no outcome value.** For the primary set, each source within it and each sensitivity set: records, alloys, alloys with at least two grain sizes, independent groups (the plan's grouping), residual degrees of freedom, the two validity-check inputs, and whether each minimum is met. These are recorded as information in the freeze's `stage_result`.
- **Step 6 decides no outcome and writes no `analysis_result`.** Step 7 writes `minimums_met` (the database checks it against the plan) and decides the outcome.
- **Zero eligible records:** no dataset is frozen; the "no dataset frozen" row is written; "insufficient" is set when the run completes (step 7 or 9).
- **Below the minimums with at least one eligible record:** the dataset is still frozen. What such a run may show is the owner's open decision for step 7.

## Writes, refusals and the guard

- **Every write** goes through `writes.write`: one `run_transaction` (retried on 40P01 / 40001), `SET LOCAL lock_timeout`, `hc_write_lock(p_run)` first, the run's stage from the database. A test watches every statement and checks that each INSERT or UPDATE of the five write paths comes after `hc_write_lock` in its transaction.
- **Reads and writes are apart.** Checks and Inclusion read through their access objects, never while holding the run's lock. The write then re-checks by id what was read; a record added in between is refused as `changed_since_read` (tested for Checks, Inclusion and the freeze).
- **Refusals are logged before they are raised**, in `audit_log` with `detail.result` "rejected", a fixed code and, for a database refusal, the database's own message. The row is written in its own transaction without the run lock (the step 5 named exception, extended with the owner's approval); the process log is the fallback.
- **Constructed data.** An unmarked run refuses constructed records at storage, inclusion and the freeze. **The guard is in code; the database itself does not refuse a constructed record.** That is consistent with the threat model (trusted code), but weaker than the triggers; a database rule would need a migration, which the owner may ask for.

## Migrations

| Revision | Why needed | Down | Previous release's code |
|---|---|---|---|
| 0002 | The fixed tag lists must exist as approved rows on every database before any run locks its tags (as 0001 seeds the domains). Data only. | No-op: tag values are never deleted and may be attached to runs. The rows stay; base removes them with the table (0001). | Unaffected: it only reads approved values. |
| 0003 | The record table had no column for how a record was extracted; the JSON columns hold harmonized values and values as reported. | Restores 0001's trigger and drops the column (its contents are lost). | Unaffected: it inserts no records outside tests. |

`ON CONFLICT (kind, value) DO NOTHING`: a value that already exists keeps its row and status (tested with proposed, rejected and approved values). The 0003 trigger is 0001's, unchanged and in the same order, plus `IF NEW.extraction IS NULL THEN … END IF` (tested textually and by behaviour). The failure-rollback test plants a column so 0003 fails after 0002 inserted its rows: nothing is left, and the revision stays 0001.

## Results on the controlled duplicate extract (marked run, MPEA and the extract)

Every row matches its answer-file row (`tests/test_controlled_duplicates_handling.py`, 50 tests). All 16 extract records are kept.

| Rows | Flag | Primary | Sensitivity |
|---|---|---|---|
| 1–4 | exact duplicate | MPEA survives (rule 2), extract counted once | — |
| 5–6 | possible duplicate | MPEA survives (rule 1) | both in `possible_duplicates_separate` |
| 7–8 | conflict | neither (`conflict_unresolved`) | MPEA counted once in `conflicts_survivor_value` |
| 9–10 | none (other paper) | both enter | — |
| 11–12 | none (other temperature) | extract out of scope | — |
| 13–14 | possible duplicate | extract `scope_not_confirmed`; MPEA in | extract counted once in `scope_not_confirmed_included` |
| 15–16 | none (other test type) | extract out of scope (tension only) | both in `tension_and_compression` |

Non-MPEA survivors (step 1 open item 3) are constructed records in `tests/test_eligibility.py`: the extract record wins by rule 1 when only it carries the DOI, and a Texas A&M record wins over an extract record by rule 2.

## Reference sets and numbers (test side only)

The reference run (reference plan, MPEA and Texas A&M, unmarked) through the freeze:
- **MPEA primary: 76 records** (the reference script's 77 without row 139, the compression test), 13 alloys, **19 papers**. Row 139's paper has no other record, so it drops out entirely.
- **Texas A&M: 21 eligible**, 72 `single_grain_size`, 1 `missing_value` (BBA09). They stay eligible through the band and the microstructure assigned by decision.
- **MPEA rules:** 1,242 out of scope, 207 missing value, 13 single grain size, 7 scope not confirmed (blank microstructure), 76 eligible.
- **No flag at all:** the two sources share no measurement and neither has an invalid value.

**Recomputed test-side**, with the method of `docs/reference/worked_example.py`: OLS with alloy intercepts; cluster-robust standard errors by group with the small-sample correction; one-sided p against t with groups − 1 df; statsmodels 0.15.0, scipy 1.18.1, in a scratchpad environment, not the project's. The sets come from the pipeline's freeze, the yield strengths from the stored records. The scripts are in the packet.

| Set | Records | Alloys | Groups | Resid. df | k (MPa·µm^½) | ± one standard error (not a confidence interval) | p |
|---|---|---|---|---|---|---|---|
| **MPEA alone** | 76 | 13 | 19 | 62 | 424.1 | ± 62.2 | 1.1e-6 |
| **Texas A&M alone** | 21 | 9 | 1 | 11 | 1173.3 | none (one group) | none |
| **Pooled (primary)** | 97 | 22 | 20 | 74 | 424.9 | ± 64.4 | 1.3e-6 |
| no_exclusions | 97 | 22 | 20 | 74 | 424.9 | ± 64.4 | 1.3e-6 |
| tension_and_compression | 98 | 22 | 21 | 75 | 428.0 | ± 63.5 | 7.4e-7 |
| six_batches_as_groups | 97 | 22 | 22 | 74 | 424.9 | ± 64.2 | 7.5e-7 |
| same_alloy_1_at_pct | 97 | 22 | 20 | 74 | 424.9 | ± 64.4 | 1.3e-6 |
| source_only_assignments | 76 | 13 | 19 | 62 | 424.1 | ± 62.2 | 1.1e-6 |
| scope_not_confirmed_included | 103 | 23 | 22 | 79 | 432.4 | ± 64.9 | 6.7e-7 |
| possible_duplicates_separate | 97 | 22 | 20 | 74 | 424.9 | ± 64.4 | 1.3e-6 |
| conflicts_survivor_value | 97 | 22 | 20 | 74 | 424.9 | ± 64.4 | 1.3e-6 |

Reading the table:
- **Cross-check.** `tension_and_compression` is the earlier reference selection and reproduces its numbers exactly (pooled 428.0 ± 63.5, p = 7.4e-7; MPEA alone in that set 77 records, 20 papers, 427.2 ± 61.4, p = 6.2e-7).
- **`no_exclusions` equals the primary set.** The one record below 0.1 µm in scope is a compression test (MPEA row 1471, CoCrFeMnNi, 0.03 µm, 1100 MPa), already out under tension only. That record alone made the reference script's "no exclusions" 233 ± 97: recomputed test-side, 232.9 ± 96.7 pooled (99 records) and 232.5 ± 93.4 for MPEA (78 records).
- **`six_batches_as_groups` has three Texas A&M groups, not six.** The 21 eligible records come from three batches (CBA, CBB, CBC, seven each), so the pooled groups are 19 + 3 = 22.
- **`same_alloy_1_at_pct`** groups the same 97 records into the same 22 alloys; it changes nothing here.
- **The two duplicate sets** equal the primary set on the real sources (they share no measurement).
- **The pooled p-value** is 1.3e-6, against "≈ 8e-7" in the PRD for the old set (recomputed 7.4e-7; step 1 open item 1).

The counts are regression tests now (`tests/test_reference_sets.py`). The coefficients, uncertainties and p-values become tests with the statistics module in step 7, which must reproduce them independently. **Approved by the owner on 2026-10-06**: CLAUDE.md and register entry `reference_numbers` state them.

## Assumptions register

99 entries: 96 in force, 2 open, 1 direction approved, after the owner's decisions and the review fixes of 2026-10-06. New on 2026-10-06: `primary_set_invariants`, `checks_bound_to_records`, `fixed_policies_in_code`, `reference_numbers`. Every entry decided in step 6 is by the owner on 2026-10-05, not reviewed by an expert.

**Applied in step 6, with named settings and tests:**
- **Moved to "yes":** `tamu_test_temperature`, `tamu_microstructure`, `permitted_test_types`, `same_alloy_rule`, `values_disagree_tolerance`, `conflict_pairing_rule`, `tag_starting_lists`, `room_temperature_scope`, `fcc_microstructure_scope`, `grain_size_floor`, `alloy_eligibility`, `physical_validity_checks`, `sufficiency_options`, `duplicate_identity`, `duplicate_survivor_rule`, `unresolved_duplicates`, `scope_not_confirmed`, `assigned_value_statuses`, `controlled_extract_disabled`, `observation_unit`, `quasistatic_tests`.
- **Still partly applied, completed in step 7:** `fixed_minimums`, `tamu_grouping_unit`, `grain_size_transformation_at_analysis`.

**Reworded**, with the earlier wording in history; each is now decided by the owner (2026-10-05):
- `values_disagree_tolerance`: a matching tolerance for grain size and a duplicate-or-conflict threshold for yield strength; known-limit note;
- `conflict_pairing_rule`: the possible-duplicate case and several candidates;
- `room_temperature_scope`: the band rule;
- `alloy_eligibility`: counted after duplicate resolution;
- `physical_validity_checks`: grain size "zero or less", where it read "negative" (my change, shown in the approved table);
- `duplicate_identity`: different sources and the tolerances;
- `unresolved_duplicates`: ambiguous groups;
- `plan_named_parts`: the schema extension;
- `audit_failure_rows_without_run_lock`: extended to the pipeline's refusals.

`code_vocabularies` lists the new codes, with the earlier lists in history.

**New entries:**
- `eligibility_rule_order`, `conflicts_not_pooled`, `sensitivity_one_change`, `code_role_access`, `record_extraction_provenance`, `freeze_counts`;
- `constructed_test_runs` (partly: the label and the exclusion are steps 7 and 10; a backlog note for a database rule, 2026-10-06);
- `reference_numbers` (2026-10-06; partly: the coefficients are reproduced by the statistics module in step 7; the earlier values in its history).

**Open owner decisions:**
- `below_minimum_display` (before step 7), with the owner's starting position;
- `curator_tabular_sources` (before step 8).

## Tests (860, all passing; 217 new in step 6; tests changed listed below)

| File | Tests | What |
|---|---|---|
| `tests/test_plan.py` | 33 | Default and reference plans valid and equal to their projection; the reference plan's values; each default from its named setting; 19 kinds of invalid plan refused; the fingerprint; three tags. |
| `tests/test_flags.py` | 18 | Invalid values; never within one source; tolerance boundaries (1.99% / 2.01%) on yield strength and grain size; known differences; unknown paper or condition; the same-alloy rule and the tolerance from the plan; 1:2, 2:2 and non-linked groups; conflict groups; a dataset cites itself; **flags unchanged when outcomes are replaced by arbitrary values that keep every pairwise and per-record relation, and with the plan's model and hypotheses removed**; import scan. |
| `tests/test_eligibility.py` | 45 | Each rule; the order; **duplicates before grain sizes (1.79/1.8 µm)**; Texas A&M by decision and the source-only set; survivors incl. **non-MPEA survivors**; conflicts and ambiguous groups; identity only among records that passed the earlier rules; **each setting read from the plan** (12 settings); grouping from the plan; decisions ignore the profile; no profile import; counts. |
| `tests/test_checkpoints.py` | 26 | The lock (plan, fingerprint, three tags in one transaction); second or changed lock, invalid plan, other version refused and logged; the lock waits for the run lock; **every write after `hc_write_lock`**; records stored after the lock with their extraction; **the guard at three points**; a marked run; changes between read and write refused (three steps); the freeze refuses decisions the rules do not produce; every write after the freeze refused and logged; counts and fingerprint; no dataset frozen; the same fingerprint on another database. |
| `tests/test_controlled_duplicates_handling.py` | 50 | Every extract row against the answer file: flag, primary handling, survivor, sensitivity handling; rows 15–16 under tension and compression. |
| `tests/test_reference_sets.py` | 6 | The primary set equals the reference selection without row 139; one decision per record (Texas A&M 21/72/1); no shared measurement; the freeze counts; **one change per sensitivity set**, on the reference run and on a marked run with duplicates and conflicts. |
| `tests/test_access_code_roles.py` | 12 | The code lists; binds only at curation (five other stages); only code roles; an agent setting cannot bind as one; **Inclusion receives no planted outcome value** (Checks as positive control); `record_conditions` contents and hashes. |
| `tests/test_migrations_step6.py` | 20 | Lists = register = profile; 0002 changes no schema; safe with existing values; up/down/up through each revision; failure rollback across both; 0003 keeps 0001's checks and adds one; a record states its extraction. |
| `tests/test_sensitivity_matching.py` | 3 | Review finding 2: the reviewer's example through the real pipeline (two compositions that merge at 1 at.%); every other set keeps the primary flags; the corrected one-change rule. |
| `tests/test_adapter_tamu.py`, `tests/test_assumptions.py` | +1, +3 | The decision citations quote the register; the step 6 decisions' wording; the approved reference numbers with the earlier values in their history (2026-10-06); `primary_set_invariants` in one entry, shown on the page. |

### Tests changed (none weakened)

- **The two assigned statuses** (the assertion follows the decided status; nothing removed):
  - `test_adapter_tamu.py`: `test_assigned_values_carry_their_passage` now also checks the band and the microstructure by decision; `test_assigned_and_reported_stay_distinguishable` checks both statuses; `test_temperature_is_not_reported` is renamed `test_temperature_is_not_reported_and_the_band_is_assigned_by_decision`, because the band is now assigned; the formula-cell test expects `assigned_from_source`.
  - `test_adapter_mpea.py::test_no_value_is_assigned`, `test_source_connection.py` (two tests, now also counting both statuses), `test_access_layer.py`, `test_access_dispatch.py`, `test_reference_counts_from_adapters.py`, and `test_assumptions.py::test_resolved_values_use_json_terms`: the status names.
- **Migration 0003:**
  - `model_builder.World.record` and `access_world` (helpers) insert records with an extraction;
  - `test_data_model.py::test_every_record_names_its_origin`: its two refused inserts carry an extraction, so they still reach the check they test (the new trigger would refuse them first).
- **Migration 0002:**
  - `test_migrations.py::test_exactly_one_head_and_every_revision_has_a_downgrade`: names 0002 as data-only and checks that its upgrade changes no schema and its downgrade is a no-op; it previously required "drop" in every downgrade. The behaviour is tested in `test_migrations_step6.py`.
  - `assert_schema_is_head` also checks the 19 seeded values (stronger).
  - `test_access_layer.py::test_tag_values_are_the_approved_lists_only`: expects the 19 seeded values, not the world's one; the planted proposed value is still absent.
  - `access_world` inserts its approved value with `ON CONFLICT DO NOTHING`.
- **The step 1 answer file** (owner's approval):
  - `test_controlled_duplicates.py`: the pinned fingerprint; the case renamed `conflict_value_differs`; `EXPECTED` for it (decision C); the survivor wording; the survivor test's conflict branch.
- **The register** (decisions moved from "not yet" to applied, the step 5 pattern):
  - `test_the_owners_eight_decisions_are_recorded_as_decided` expects each decision's applied status and step;
  - `PARTLY` follows the register;
  - `test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review` expects the two new open entries, the new statement, and the step 5 statement in its history;
  - `test_the_microstructure_decision_is_recorded` expects "yes";
  - the page tests expect the "Open decisions" section (2 open; 3 with the fixture).

- **The owner's decisions of 2026-10-06:**
  - `test_controlled_duplicates.py`: the pinned fingerprint; `test_other_test_type_rows_are_compression_copies_of_tension_records` and `EXPECTED` expect the corrected cells of rows 15–16;
  - `test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files` reads `primary_analysis` for every row, where it read the tension-only column for rows 15–16;
  - `test_assumptions.py`: `PARTLY` gains `reference_numbers`.

- **The review fixes (2026-10-06):**
  - `test_eligibility.py::test_each_setting_is_read_from_the_locked_plan`: the case that mapped a conflict to `in_scope` is **replaced** (owner's decision) by the allowed choice, the survivor's value counted once.
  - `test_flags.py::test_a_group_with_one_conflicting_pair_is_a_conflict` expects the extra conflict flag inside the ambiguous group (finding 4).
  - `test_flags.py::test_flags_use_only_pairwise_and_per_record_rules` is renamed `test_flags_come_from_pairwise_comparisons_and_group_classification` (wording); `test_checks_imports_no_statistics_…` allows the plan's sensitivity-set names (finding 2).
  - `test_reference_sets.py::_check_one_change` is **corrected** (finding 2): for a matching change it accepts identity changes that come from the set's own flags; it had assumed only grain-size counts can change.
  - `test_access_code_roles.py`: Inclusion's list and the audited fields include `set_flags`; `record_conditions` carries the stable identity.
  - `test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test` marks the bypassed source searched before Checks (Checks now wait for every source); `test_a_change_after_the_decisions_were_read_is_refused_at_the_freeze` expects `checks_not_current`, which the freeze now finds first.
  - `test_assumptions.py`: `conflicts_not_pooled` is decided on 2026-10-06; new tests for `primary_set_invariants` (shown on the page).
  - `test_controlled_duplicates.py`: the pinned fingerprint and the explanation of rows 15–16.

No test was removed.

### The safeguard tests fail when the safeguard is removed

Each change was made in a scratch copy of the package (the copy's import checked) and the named test files were run against it with `PYTHONPATH`:

| Removed or changed in the copy | Failing tests |
|---|---|
| Constructed-data guard off | 1 |
| `bind_code` accepts any role | 1 |
| Inclusion receives all values | 2 |
| `record_conditions` carries the outcome value | 3 |
| Checks does not re-check its read | 1 |
| Inclusion does not re-check its read | 1 |
| Grain sizes counted before duplicates | 1 |
| The scope rule removed (so the duplicate rule acts first) | 7 |
| Grain size compared exactly, not within the tolerance | 2 |
| Tolerance fixed in code, not from the plan | 1 |
| Minimum grain sizes from the profile, not the plan | 2 |
| Rows within one source compared | 2 |
| An ambiguous group paired anyway | 3 |
| A conflict enters with both records | 4 |
| Survivor rule 1 ignored | 1 |
| Write path without `hc_write_lock` | 1 |
| Refusals not logged | 9 |
| Freeze does not re-check its read | 1 |
| Freeze accepts decisions the rules do not produce | 2 |
| A second lock not refused by our path | 1 |
| 0003 trigger without the extraction requirement | 2 |
| Plan validation accepts free text | 5 |
| Texas A&M band not assigned | 6 |
| *After the review (2026-10-06):* plan validation skips the fixed rules | 13 |
| Checks run while a source is pending | 1 |
| Inclusion and the freeze ignore the Checks binding | 3 |
| Storage allowed after Checks | 1 (after the new test; see below) |
| Sensitivity sets reuse the primary flags | 2 |
| An ambiguous group drops its conflict | 2 |
| Survivor tie-break by database id | 1 |
| The lock accepts a setting that leaves out a source | 2 |
| The fingerprint keyed by database id | 1 |
| The extraction check without coalesce | 4 |

In the review round, **"storage allowed after Checks" first survived**: Checks now wait for every chosen source, so the normal sequence never reaches that refusal. `test_no_record_is_stored_after_checks` creates the state directly (a Checks result while a source is still pending) and fails without it. Its harness run was disturbed by a stale earlier run sharing the scratch copy, so this one was repeated by hand: the copy imported, 1 failed, 25 passed.

**Three mutations first survived**, and two tests were added:
- **"Write path without `hc_write_lock`":** the database triggers lock the run row too. The new statement-order test now fails without it.
- **"Freeze does not re-check its read":** its decision comparison caught the earlier scenario. The new tests change the run between each step's read and its write.
- **"`record_conditions` carries the outcome value":** the first mutation was neutralised by the reader's second filter. The stronger mutation (both removed) fails three tests.

### Suite results

```
$ pytest -q                                   (Codespace, Python 3.14.2, `docker compose up -d db`)
860 passed                                     (after the review fixes, 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
860 passed in 205.06s
```

Before the review: 816 passed locally and in the image.

GitHub Actions, commit `b11e7c8` (the owner's decisions of 2026-10-06, last change to code, tests or data): success; "Run the suite in the test image": 816 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37354762927
Earlier: commit `8ccfd36` (first build), 815 passed, https://github.com/kelawady/hypocurate/actions/runs/37352154249

## Deviations from the approved plan

1. **A flag `category` in `eligibility_rules`** (a schema leaf), so that the plan, not code, says what an ambiguous group means.
2. **A content hash in `record_conditions`**, so that the freeze fingerprint covers record content without Inclusion receiving values.
3. **Ambiguity also when a group's records are not all linked** (section "Records, checks and inclusion").
4. **The freeze reads the decision tables by SQL** (ids and codes) to check them, not through an access object.
5. **Record storage reads sealed versions directly** (code, approved under (c)), not through an access object.
6. **The variation of each sensitivity key is fixed by the key**, not by plan numbers.
7. **Sprint 1 plans accept only the room-temperature band**; any other band is refused by `validate`.
8. **The answer file's rows 15–16:** corrected by the owner's decision of 2026-10-06 (two cells per row).
9. **The register's reworded entries are recorded as decided by the owner on 2026-10-05** (the approval of this plan); their earlier deciders and dates are kept in their history.

## Things found unclear or contradictory while building

1. **PRD 5.3 vs CLAUDE.md rule 4** on conflicts: decided (C).
2. **The pairing rule vs possible duplicates** (rows 5–6, 13–14): decided (question 1).
3. **PRD 10 "no exclusions" (233 ± 97)** came from one compression record; under tension only it equals the primary set.
4. **"Six batches"** gives three groups among the eligible Texas A&M records.
5. **PRD 5.3's survivor rule 1** ("the record from the original paper") can only decide a possible duplicate under the pairing rule.
6. **A conflict and grain size:** the register said the tolerance "applies to yield strength and grain size"; decided (question 6).

## PRD corrections and clarifications for the next PRD update

1. **PRD 5.3 (conflicts):** "Comparable specimens and conditions; the values truly differ … Both enter" → two sources reporting the same measurement with values beyond the tolerance: both kept and flagged, **neither enters**; sensitivity "conflicts by the survivor value". It contradicted CLAUDE.md rule 4. Repeat specimens within one source are separate measurements and are never compared.
2. **PRD 5.3 (duplicates):** compared only between different sources; same alloy (0.1 at.%), grain size within 2% (matching), yield strength within 2% (duplicate) or beyond (conflict); a missing paper or test condition gives a possible duplicate; several candidates pair nothing, and none of them enters the primary set.
3. **PRD 5.3 (survivor):** "the record that carries the original paper reference (DOI); then the fixed source order MPEA, Texas A&M, controlled extract; then the lowest row".
4. **PRD 5.3 (rule order):** one rule per record in the stated order; duplicates are resolved before grain sizes are counted; a record with a missing condition is "scope not confirmed" before any duplicate rule.
5. **PRD 5.1 / 5.6 (plan):** the plan holds every setting that affects eligibility or grouping, and the domain profile and version; eight named sensitivity analyses, each one change from the primary set, descriptive, no multiplicity adjustment.
6. **PRD 10 and 5.7 (sensitivity figures):** remove "438 ± 67 with four records removed" (discretionary removals, chosen after seeing outcomes; not a plan analysis). "233 ± 97 with no exclusions" came from one compression record (0.03 µm); under the tension-only plan "no exclusions" equals the primary set.
7. **PRD 5.7, 5.8, 10, 13.1, 14.1a and CLAUDE.md (reference numbers; after the owner's approval):**
   - MPEA alone 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6;
   - pooled 97 records, 22 alloys, 20 groups, 74 residual df, k = 424.9 ± 64.4, p ≈ 1.3e-6;
   - Texas A&M alone unchanged: 21 records, 9 alloys, one group, k ≈ 1173, no uncertainty;
   - PRD 5.8 "MPEA alone (77, 13, 20)" → (76, 13, 19).
8. **PRD 10 (Texas A&M):**
   - test temperature (the room-temperature band) and single-phase FCC microstructure are **assigned by decision**, a status kept distinct from "assigned from source";
   - the 21 eligible records come from three of the six batches.
9. **PRD 5.2 (scope and exclusion):** test type, temperature band and single-phase FCC are the plan's scope (out of scope or scope not confirmed); the grain-size floor is the menu exclusion rule. "No exclusions" drops only the exclusion rules.
10. **PRD 5.5 (tags):** the starting lists are seeded by a migration; each run gets exactly one tag per kind at the lock.
11. **PRD 4 (table):** Inclusion and Checks read through access objects. Inclusion receives no outcome value; Checks sees all values.
12. **PRD 7 (data model):** `record` states how it was extracted (adapter or agent, name, version); code stages write `stage_result` rows (role empty).
13. **PRD 3 step 7 / 5.6:** the counts for the fixed minimums are computed at the freeze from structure and grain sizes; a dataset below the minimums is still frozen; the outcome is decided in step 7.
14. **PRD 14.2:** refused changes after a checkpoint are rejected and logged by the write paths as well as the database.
15. **PRD 2.1 / 10 (controlled extract):** runs that include constructed data are marked at dispatch, may complete, are labelled "test run: includes constructed data", and are excluded from aggregates and lists of real results.
16. **PRD 18 (backlog; owner, 2026-10-06):** a database rule that refuses a constructed source's records in a run not marked as a test. In sprint 1 the guard is in code only.
17. **PRD 5.3 (owner, 2026-10-06): fixed rules, not plan defaults.** "The defaults below apply unless the Planner sets a different rule before the lock" no longer holds for these: no plan, including one a model writes, can count an exact duplicate twice, admit both records of a conflict, a physically invalid value, an unresolved-identity group, a model-recalled record, or a constructed record in a run not marked as a test. A plan's only choices are: conflicts neither (default) or the survivor's value once; possible duplicates once (default) or both.
18. **PRD 3 / 5.6 (order of the steps; review finding 1):** extraction finishes before Checks; the completed Checks result is bound to the exact records it covered; Inclusion and the freeze verify that binding.
19. **PRD 5.7 / 5.8 / 14.1a (wording):** each "±" in the reference numbers is one standard error (cluster-robust, by group), not a confidence interval.

## Open items

1. **Owner:** the open decisions `below_minimum_display` (before step 7) and `curator_tabular_sources` (before step 8).
2. **Step 7:**
   - the statistics on the frozen sets; the coefficients above become tests;
   - the fixed-minimum check that decides the outcome;
   - the predictor transformation from the plan;
   - the per-source alloys rule (an alloy that qualifies only pooled);
   - the label "test run: includes constructed data" on stored results;
   - the open item from step 1 on the pooled p-value (1.3e-6 now);
   - the statistics module reproduces the approved reference numbers independently.
3. **Step 8:** the Curator and tabular sources; a Planner's plan must pass `validate` (including the fixed rules) and is locked through `lock_rules`.
4. **Step 9:** the orchestration marks a source refused by the constructed-data guard as failed, so Checks can run (register `checks_bound_to_records`).
5. **Step 10:** the label and the exclusion of marked runs on every screen and list.
6. **Later step:** an unknown source definition fails closed (register `constructed_test_runs`).
7. **At the merge:** migrations 0002 and 0003 run on Render's pre-deploy; check the live deploy with the owner (schema at 0003, 19 tag values).
8. **Carried, unchanged:** the step 5 open items for steps 7–9; live registration of sources (owner).

## Questions for the re-check

1. Is each of the six findings closed, and do the new tests exercise the scenarios you reproduced?
2. Does `primary_set_invariants` hold for every plan, including one a model writes (refused at the lock and again when the rules are applied)?
3. Is the Checks binding (record identities and flags) enough to stop a stale or skipped Checks result from reaching Inclusion or the freeze?
4. Are the per-set matching flags complete (which settings count as matching), and does Inclusion stay outcome-blind with `set_flags`?
5. Is any claim still stronger than the code supports?

## Questions for the first review (answered in its text)

1. Can any outcome value reach Inclusion (`record_conditions`, `flags_kind`, the projected plan)? Is the "guaranteed / not claimed" statement accurate?
2. Do the eligibility rules and their order match PRD 5.3 as the owner decided it, and is each sensitivity set exactly one change?
3. Is the duplicate grouping (candidate links, ambiguity when several candidates or not all linked, conflict precedence) sound, and is anything merged on a guess?
4. Can anything change after the rules lock or the freeze through these write paths, and is every refusal logged?
5. Are migrations 0002 and 0003 safe on the live database and with the previous release's code?
6. Is any claim in this summary, the code, the README or the register stronger than the code supports?
````

## 2. The review

````markdown
# Step 6 — second-model review (ChatGPT, 2026-10-06)

Review of `docs/reviews/step06_review_packet.md` (branch `step-06-eligibility`, code commit `b11e7c8`). Saved verbatim as the owner gave it. The owner accepted all six findings on 2026-10-06, with a decision on conflicts and exact duplicates (see `docs/reviews/step06_summary.md`).

---

There are serious correctness gaps. I would hold step 6. These are ordinary sequencing and data-handling mistakes within the agreed threat model—not hostile-code scenarios.
Findings, in seriousness order:
1. Checks can be skipped or become stale, and the freeze can still accept the result.
   decide_run() does not require a completed Checks stage covering the current records. freeze_dataset() recomputes decisions from the stored flags, without establishing that those flags cover every record.
   Two ordinary mistakes therefore matter:
   - Store records → skip Checks → decide → freeze.
   - Store source A → run Checks → store source B → decide → freeze.
   Both can produce internally consistent decisions based on missing flags. The second case also cannot simply rerun Checks because it is once-only. Comparing record IDs between each individual read and write does not close this gap.
   Fix: require extraction to finish before Checks, bind the completed Checks result to the exact record collection, and verify that binding before Inclusion and freeze. Test both sequences above with actual conflicting records.
2. The coarser-alloy sensitivity does not recompute duplicates under its changed alloy definition.
   same_alloy_1_at_pct changes Settings.decimals, but all_sets() reuses flags computed under the primary plan’s precision.
   I reproduced this with two compositions—Co50.06/Ni49.94 and Co50.04/Ni49.96—each represented at two grain sizes across two sources. The sensitivity retains all four records. Recomputing duplicate flags at its stated precision correctly counts only two.
   Fix: compute the relevant matching flags under each sensitivity’s effective settings, then apply the remaining rules unchanged. Inclusion can remain outcome-blind; Checks should supply those flags.
   The existing sensitivity test misses this and actually assumes that coarser grouping can change only single_grain_size versus in_scope.
3. An incomplete survivor order makes the selected record depend on database insertion order.
   Plan validation accepts an empty or incomplete survivor_source_order. Unlisted sources share the same priority; equal DOI status and row number then fall through to the database record ID.
   I reproduced a survivor switching from MPEA to the extract solely by swapping insertion IDs, with the same plan and source records.
   The validator likewise accepts empty/incomplete grouping, leaving some records without a group.
   Fix: at the rules lock, require the ordering and grouping settings to cover every selected source. Use stable source/origin identity for any final tie-breaker. Tests should vary insertion order and omit one selected source from each setting.
4. Ambiguous groups can hide a definite conflict from the sensitivity rules.
   Consider three sources:
   - A reports 400, with a DOI.
   - B reports 400, without a DOI.
   - C reports 440, with A’s DOI.
   A–C is a definite conflict; A–B is a possible duplicate; B–C does not link. The component becomes only possible_duplicate / several candidates. Its conflict information is absent from Inclusion’s input.
   The primary set correctly excludes the group. But possible_duplicates_separate then admits both conflicting values. I reproduced this with another grain size present.
   That contradicts the promise that this sensitivity changes unresolved-identity handling while leaving conflict handling unchanged. Preserve the conflict information when labelling a component ambiguous, and test the resulting sets—not just the flag label.
5. The freeze fingerprint is not reproducible independently of database IDs.
   The fingerprint includes record IDs in both sets and rules. Identical records and the same plan produce different fingerprints when the record sequence starts elsewhere. I confirmed this using the packet’s fingerprint calculation.
   The existing test creates two databases from the same template and follows identical insertion steps, reproducing the same IDs rather than testing independence from them.
   Fix: fingerprint stable record identities—source-version fingerprint, origin and item index—plus content and decisions. Keep database IDs separately for lookup. Test two identical runs after unrelated inserts or in the same database.
6. Migration 0003’s extraction constraint accepts a missing method.
   This passes the new shape check:
   {"name": "mpea_layout", "version": "1"}
   The missing method makes its comparison evaluate to SQL NULL; PostgreSQL accepts a CHECK yielding NULL. The trigger rejects only a NULL extraction column. Numeric/object name and version values can also pass because ->> converts them to text. PostgreSQL constraint semantics, JSON extraction semantics.
   Fix: require the necessary keys and JSON string types, and make the predicate explicitly true. Add missing-method, null-method and wrong-type tests.
   Otherwise, the replaced trigger preserves the earlier checks, and the migration transaction/rollback tests look appropriate. Migration 0002’s intentional no-op downgrade is accurately described.
On the remaining questions:
- Outcome blindness: I found no raw outcome value in Inclusion’s projected input or relationship-fitting logic in Checks. Outcome-derived flags and availability statuses deliberately influence eligibility. That qualification is accurate. “Only pairwise rules” is slightly imprecise: pairwise comparisons feed whole-component classification.
- Locked settings and sensitivity names: encoding a fixed change in a named sensitivity is acceptable; duplicating every constant into the plan is unnecessary. Its meaning must remain stable or be versioned. The broad “every setting comes only from the plan” claim needs narrowing because fixed policies such as flags.VALUE_STATUSES still live in code.
- Conflict policy: PRD 5.3 permits pre-lock overrides, and the implementation explicitly tests mapping conflicts to in_scope. Consequently, “neither conflict record enters primary” is currently a default, not an invariant. Clarify whether the owner’s later decision was intended to remove that override.
- Constructed-data guard: the three checks cover the registered constructed source under the agreed code-only approach. I found no additional blocker there; unknown source definitions should eventually fail closed.
- Reference numbers: the counts hang together: 76 + 21 = 97 records; 13 + 9 = 22 alloys; 19 + 1 = 20 groups; residual df = 97 − 22 − 1 = 74. The other table rows are similarly consistent. Three eligible Texas A&M batches explain 22 pooled sensitivity groups. The fitting script matches the specified OLS, clustered standard-error correction and one-sided t calculation. Label “±” explicitly as one standard error, not a confidence interval. statsmodels documentation
- Scope: the test-side statistical recomputation is appropriate verification, not problematic step-7 implementation creep.
I ran targeted extracted-code reproductions, not the reported 816-test PostgreSQL suite or the numerical fits. The sequencing, sensitivity and determinism gaps need fixing before sign-off.
````

## 3. The fixes, commit by commit

### `fe09cbe Step 6 fix: fixed rules for the primary set, not plan defaults`

````diff
fe09cbe8593510824e17957254e52f04fd78ce84

Step 6 fix: fixed rules for the primary set, not plan defaults

Owner, 2026-10-06 (review: conflict policy). No plan can count an exact
duplicate twice, admit both records of a conflict, an invalid value or an
unresolved-identity group: plan validation refuses it at the lock and
eligibility.settings refuses it again. Plan choices left: conflicts neither
(default) or the survivor's value once; possible duplicates once (default)
or both. The test that mapped a conflict to in_scope is replaced. Register:
new entry primary_set_invariants (all six things no plan can do, with
tests); conflict, duplicate and invalid-value entries reworded.
13 new tests failed on the code before this change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 1b0cf7f..00ba5b9 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -1252,7 +1252,7 @@
     "key": "physical_validity_checks",
     "name": "Physical validity checks",
     "state": "in_force",
-    "statement": "A physically impossible value (tensile strength below yield strength, or a grain size of zero or less) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
+    "statement": "A physically impossible value (tensile strength below yield strength, or a grain size of zero or less) is flagged and never enters the primary analysis, whatever the plan (a fixed rule). Agreement with the grain-size relationship under test is never used to judge a record.",
     "value": {
       "text": "UTS < YS or grain size <= 0: invalid",
       "unit": null
@@ -1265,7 +1265,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1288,11 +1288,20 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "Step 4b wording ('a negative grain size'); zero added in step 6, since the model needs a positive grain size."
+      },
+      {
+        "value": "A physically impossible value (tensile strength below yield strength, or a grain size of zero or less) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 6 wording; made a fixed rule by the owner on 2026-10-06."
       }
     ],
-    "notes": [],
+    "notes": [
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+    ],
     "tests": [
       "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_flags.py::test_flags_use_only_pairwise_and_per_record_rules",
       "tests/test_flags.py::test_physically_impossible_values_are_flagged_per_record"
     ]
@@ -2246,7 +2255,7 @@
     "key": "duplicate_survivor_rule",
     "name": "Which duplicate is kept in the primary analysis",
     "state": "in_force",
-    "statement": "1) Prefer the record that carries the original paper reference (DOI). 2) If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract. 3) Within one source, take the lowest row number.",
+    "statement": "1) Prefer the record that carries the original paper reference (DOI). 2) If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract. 3) Within one source, take the lowest row number. An exact duplicate is always counted once (a fixed rule).",
     "value": {
       "text": "the record carrying the original paper reference; then source order; then lowest row",
       "unit": null
@@ -2258,8 +2267,8 @@
       "PRD 5.3; step 1 summary, 'Survivor rule'."
     ],
     "decided": {
-      "by": "owner (Khalid El-Awady), step 1; wording restored 2026-10-05",
-      "date": "2026-10-05"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -2287,15 +2296,23 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "Wording of the step 1 re-check correction and of the first step 4b register; withdrawn after the step 4b review, finding 3."
+      },
+      {
+        "value": "1) Prefer the record that carries the original paper reference (DOI). 2) If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract. 3) Within one source, take the lowest row number.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 6 wording; 'always counted once' made a fixed rule by the owner on 2026-10-06."
       }
     ],
     "notes": [
       "A DOI identifies the cited paper, not where a record was extracted: a compilation and a copied extract can both carry it. Preferring records extracted directly from the original paper would need explicit extraction-origin metadata, which does not exist.",
       "The step 1 answer file, its builder and README carry this wording since step 6 (owner's approval, 2026-10-05).",
-      "Rule 1 can only decide a possible duplicate: paired records otherwise cite the same paper."
+      "Rule 1 can only decide a possible duplicate: paired records otherwise cite the same paper.",
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
     ],
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_eligibility.py::test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi",
       "tests/test_eligibility.py::test_survivor_rule_three_the_lowest_row_within_one_source",
       "tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order"
@@ -2305,7 +2322,7 @@
     "key": "unresolved_duplicates",
     "name": "Possible duplicates that cannot be resolved",
     "state": "in_force",
-    "statement": "A possible duplicate is kept and counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis. When identity cannot be resolved (several candidates), none of the group's records enters the primary analysis; all of them enter the same sensitivity analysis.",
+    "statement": "A possible duplicate is kept and counted once in the primary analysis by the survivor rule (the plan may instead count both records), and counted separately in a sensitivity analysis. When identity cannot be resolved (several candidates), none of the group's records ever enters the primary analysis (a fixed rule); all of them are counted separately only in 'possible_duplicates_separate'.",
     "value": {
       "text": "counted once",
       "unit": null
@@ -2318,7 +2335,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -2341,13 +2358,22 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "Step 4b wording; the ambiguous group added by the owner (2026-10-05, decision C)."
+      },
+      {
+        "value": "A possible duplicate is kept and counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis. When identity cannot be resolved (several candidates), none of the group's records enters the primary analysis; all of them enter the same sensitivity analysis.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 6 wording; the unresolved-identity rule made fixed by the owner on 2026-10-06."
       }
     ],
-    "notes": [],
+    "notes": [
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+    ],
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files",
       "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
-      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule"
+      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set"
     ]
   },
   {
@@ -4187,7 +4213,7 @@
     "key": "conflicts_not_pooled",
     "name": "Conflicting reports are not pooled",
     "state": "in_force",
-    "statement": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and neither enters the primary analysis: code does not choose between them. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
+    "statement": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and both never enter the primary analysis together: this is a fixed rule, not a plan default. By default neither enters the primary analysis; the only other choice a plan has is the survivor's value counted once. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
     "value": {
       "text": "neither in primary; survivor value in a sensitivity analysis",
       "unit": null
@@ -4200,7 +4226,7 @@
     ],
     "decided": {
       "by": "owner (Khalid El-Awady)",
-      "date": "2026-10-05"
+      "date": "2026-10-06"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -4217,12 +4243,22 @@
       ],
       "note": null
     },
-    "history": [],
-    "notes": [],
+    "history": [
+      {
+        "value": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and neither enters the primary analysis: code does not choose between them. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
+        "from": "2026-10-05",
+        "to": "2026-10-06",
+        "note": "Step 6 wording (decision C); made a fixed rule by the owner on 2026-10-06 (the override to 'both enter' removed)."
+      }
+    ],
+    "notes": [
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+    ],
     "tests": [
-      "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
       "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
-      "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files"
+      "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files",
+      "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set"
     ]
   },
   {
@@ -4578,5 +4614,65 @@
       "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139",
       "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
+  },
+  {
+    "key": "primary_set_invariants",
+    "name": "What no plan can ever do to the primary set",
+    "state": "in_force",
+    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted.",
+    "value": {
+      "text": "six things no plan can do",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "The primary set of every run, whoever writes its plan (the fixed reference plan now, the Planner from step 8).",
+    "reason": "Owner, 2026-10-06, after the step 6 review: the conflict rule was a plan default a plan could override; these are fixed rules, not defaults.",
+    "evidence": [
+      "docs/reviews/step06_review_chatgpt.md (finding on the conflict policy) and the owner's decision of 2026-10-06 in docs/reviews/step06_summary.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": "Only the named sensitivity analyses change (2) and (4): 'conflicts_survivor_value' and 'possible_duplicates_separate'.",
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:FLAG_RULE_CHOICES"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:fixed_rule_problems"
+        },
+        {
+          "ref": "sql:a model-recalled record is never eligible"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.writes:constructed_unmarked"
+        }
+      ],
+      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…]; (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused."
+    },
+    "history": [],
+    "notes": [
+      "Shown on the assumptions page like every entry."
+    ],
+    "tests": [
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
+      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
+      "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
+      "tests/test_eligibility.py::test_the_fixed_rules_hold_in_every_set_the_plan_names",
+      "tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible",
+      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
+      "tests/test_plan.py::test_invalid_plans_are_refused",
+      "tests/test_plan.py::test_the_plan_choices_that_remain"
+    ]
   }
 ]
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index a743b82..b25ad0c 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -39,6 +39,36 @@ from hypocurate.sources.normalize import same_alloy_key
 PRIMARY = "primary"
 FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_counted_once")
 
+# Fixed rules, not plan defaults (owner, 2026-10-06; register 'primary_set_invariants'): what each
+# flag means for the primary set. Every plan has exactly these eligibility-rule entries (flag kind,
+# category), with a rule from the allowed choices; validation refuses anything else, and so does
+# `settings` for a plan that bypassed validation. No plan, including one a model writes, can count
+# an exact duplicate twice, admit both records of a conflict, an invalid value or an unresolved-
+# identity group. The only plan choices: a conflict enters with neither record (the default) or
+# with the survivor's value counted once; a possible duplicate is counted once (the default) or
+# both records are counted.
+FLAG_RULE_CHOICES = {
+    ("invalid_value", None): ("invalid_value",),
+    ("exact_duplicate", None): ("duplicate_counted_once",),
+    ("values_disagree", None): ("conflict_unresolved", "duplicate_counted_once"),
+    ("possible_duplicate", "several candidates"): ("identity_unresolved",),
+    ("possible_duplicate", None): ("duplicate_counted_once", "in_scope"),
+}
+
+
+def fixed_rule_problems(eligibility_rules) -> list[str]:
+    """What breaks the fixed rules in a plan's eligibility rules (empty if nothing)."""
+    got = {(e.get("flag_kind"), e.get("category")): e.get("rule") for e in eligibility_rules}
+    problems = [f"{kind}{'/' + cat if cat else ''}: missing" for kind, cat in FLAG_RULE_CHOICES
+                if (kind, cat) not in got]
+    for key, rule in got.items():
+        allowed = FLAG_RULE_CHOICES.get(key)
+        if allowed is None:
+            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: not a flag the plan sets a rule for")
+        elif rule not in allowed:
+            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: {rule} (allowed: {', '.join(allowed)})")
+    return problems
+
 # The one change of each sensitivity set (owner, 2026-10-05).
 SENSITIVITY_CHANGES = {
     "no_exclusions": "the menu exclusion rules are dropped; the scope is kept",
@@ -77,6 +107,9 @@ class Settings:
 def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
     """The settings of set `key` under the locked plan's content."""
     r, s, v = plan["rules"], plan["scope"], plan["variables"]
+    problems = fixed_rule_problems(plan["eligibility_rules"])
+    if problems:
+        raise ValueError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
     flag_rules = tuple(sorted(((e["flag_kind"], e.get("category"), e["rule"]) for e in plan["eligibility_rules"]),
                               key=lambda t: t[1] is None))
     base = Settings(
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index 606c36b..ca72a7f 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -27,6 +27,7 @@ from hypocurate.access.allowlist import PLAN_SCHEMA
 from hypocurate.access.fields import project
 from hypocurate.access.vocabulary import SENSITIVITY_KEYS
 from hypocurate.pipeline import profile as p
+from hypocurate.pipeline.eligibility import fixed_rule_problems
 
 PARTS = ("hypothesis_version", "variables", "scope", "model", "sufficiency", "fields_to_extract", "exclusion_rules",
          "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules")
@@ -155,6 +156,9 @@ def _check_template(c: dict) -> None:
         if key in seen:
             raise PlanError("each flag kind (and category) has one eligibility rule")
         seen.add(key)
+    problems = fixed_rule_problems(c["eligibility_rules"])
+    if problems:
+        raise PlanError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
     keys = c["sensitivity_analyses"]
     if len(set(keys)) != len(keys) or not set(keys) <= SENSITIVITY_KEYS - {"removal_after_lock"}:
         raise PlanError("sensitivity analyses are named once each, from the vocabulary")
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 4ce2b66..221dc9c 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -234,7 +234,9 @@ def test_the_step_6_decisions_carry_the_owners_wording():
     for key in ("sensitivity_one_change", "code_role_access", "constructed_test_runs", "record_extraction_provenance",
                 "eligibility_rule_order", "conflicts_not_pooled", "freeze_counts"):
         e = BY_KEY[key]
-        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"} and e["expert_review"]["status"] == "not_reviewed"
+        # conflicts_not_pooled was made a fixed rule by the owner on 2026-10-06.
+        date = "2026-10-06" if key == "conflicts_not_pooled" else "2026-10-05"
+        assert e["decided"] == {"by": OWNER, "date": date} and e["expert_review"]["status"] == "not_reviewed"
 
 
 def test_the_approved_reference_numbers_keep_the_earlier_values_in_their_history():
@@ -248,6 +250,23 @@ def test_the_approved_reference_numbers_keep_the_earlier_values_in_their_history
     assert "database rule" in " ".join(BY_KEY["constructed_test_runs"]["notes"])
 
 
+def test_what_no_plan_can_do_to_the_primary_set_is_listed_in_one_entry():
+    """Owner, 2026-10-06: one entry, in plain words, with a test for each point; shown on the page."""
+    e = BY_KEY["primary_set_invariants"]
+    s = e["statement"]
+    for words in ("including any plan written by a model", "exact duplicate is never counted twice",
+                  "Both records of a conflict never enter", "physically invalid value never enters",
+                  "several candidates) never enters", "model-recalled record never enters",
+                  "constructed record (the controlled extract) never enters a run that is not marked as a test"):
+        assert words in s, words
+    assert e["decided"] == {"by": OWNER, "date": "2026-10-06"} and e["applied"]["status"] == "yes"
+    for point in ("(1)", "(2)", "(3)", "(4)", "(5)", "(6)"):
+        assert point in e["applied"]["note"], point
+    html = signed_in().get("/assumptions").text
+    assert 'id="primary_set_invariants"' in html and "What no plan can ever do to the primary set" in html
+    assert "made a fixed rule" in BY_KEY["conflicts_not_pooled"]["history"][-1]["note"]
+
+
 def open_entry():
     """An open decision built for the tests, independent of the register's own."""
     e = copy.deepcopy(BY_KEY["tamu_microstructure"])
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index b3c7fdb..f83a16d 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -216,7 +216,11 @@ def _changed(path, value):
     (("scope", "phase_class"), ["BCC"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
     (("exclusion_rules",), [{"rule": "grain_size_range", "min": 20.0}], pair(1, 10.0), [], 1, "in_scope",
      "excluded_by_rule"),
-    (("eligibility_rules",), [{"flag_kind": "values_disagree", "rule": "in_scope"}],
+    # Owner, 2026-10-06: for conflicts a plan may choose only between neither record (the default)
+    # and the survivor's value counted once. (Replaces the step 6 case that mapped a conflict to
+    # in_scope, which the owner removed.)
+    (("eligibility_rules",), [{**e, "rule": "duplicate_counted_once"} if e["flag_kind"] == "values_disagree" else e
+                              for e in PLAN["eligibility_rules"]],
      [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
      [flag("values_disagree", "differ beyond tolerance", 1, 3)], 1, "conflict_unresolved", "in_scope"),
     (("variables", "outcome", "field"), "hardness", pair(1, 10.0), [], 1, "in_scope", "missing_value"),
@@ -228,6 +232,37 @@ def test_each_setting_is_read_from_the_locked_plan(path, value, records, flags,
     assert decide(records, flags, _changed(path, value))[record] == after
 
 
+@pytest.mark.parametrize("kind, category, rule", [
+    ("exact_duplicate", None, "in_scope"),  # an exact duplicate counted twice
+    ("values_disagree", None, "in_scope"),  # both records of a conflict
+    ("invalid_value", None, "in_scope"),  # an invalid value
+    ("possible_duplicate", "several candidates", "in_scope"),  # an unresolved-identity group
+    ("possible_duplicate", "several candidates", "duplicate_counted_once"),
+])
+def test_no_plan_can_put_these_records_in_the_primary_set(kind, category, rule):
+    """Owner, 2026-10-06 (register 'primary_set_invariants'): fixed rules, not plan defaults. A
+    plan that bypassed validation is refused when its settings are built, too."""
+    plan = copy.deepcopy(PLAN)
+    for e in plan["eligibility_rules"]:
+        if e["flag_kind"] == kind and e.get("category") == category:
+            e["rule"] = rule
+    with pytest.raises(ValueError, match="fixed rule"):
+        el.settings(plan)
+
+
+def test_the_fixed_rules_hold_in_every_set_the_plan_names():
+    """Sensitivity sets change only what their key names: conflicts keep 'neither' or the survivor's
+    value; exact duplicates stay counted once; invalid values and ambiguous groups stay out except
+    that 'possible_duplicates_separate' counts ambiguous groups separately."""
+    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0),
+               cond(5, "tamu_fcc", doi=False), cond(6, "tamu_fcc", doi=False, gs=40.0)]
+    for flags, primary_out in (([flag("exact_duplicate", "identical values", 1, 3)], {3}),
+                               ([flag("invalid_value", "physically impossible", 1)], {1})):
+        for key in (el.PRIMARY, *PLAN["sensitivity_analyses"]):
+            got = decide(records, flags, key=key)
+            assert all(got[i] != "in_scope" for i in primary_out), (key, flags)
+
+
 def test_grouping_is_read_from_the_locked_plan():
     records = {r["id"]: r for r in [*pair(1, 10.0, paper="a"), *pair(3, 10.0, paper="b", comp={"Co": 40.0, "Ni": 60.0}),
                                     *pair(5, 10.0, source="tamu_fcc", doi=False, batch="x"),
diff --git a/tests/test_plan.py b/tests/test_plan.py
index fcfca2f..a348cdb 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -77,6 +77,21 @@ def test_each_default_comes_from_its_named_setting(monkeypatch):
         assert default_plan(1)["sufficiency"]["min_records"] == 3
 
 
+def _set_rule(content, kind, category, rule):
+    for e in content["eligibility_rules"]:
+        if e["flag_kind"] == kind and e.get("category") == category:
+            e["rule"] = rule
+
+
+def test_the_plan_choices_that_remain():
+    """Conflicts: neither (default) or the survivor's value counted once. Possible duplicates:
+    counted once (default) or counted separately."""
+    for kind, rule in (("values_disagree", "duplicate_counted_once"), ("possible_duplicate", "in_scope")):
+        content = default_plan(1)
+        _set_rule(content, kind, None, rule)
+        validate(content)
+
+
 @pytest.mark.parametrize("change, message", [
     (lambda c: c.update(extra=1), "outside PLAN_SCHEMA"),
     (lambda c: c["rules"].update(note="free text"), "outside PLAN_SCHEMA"),
@@ -93,6 +108,18 @@ def test_each_default_comes_from_its_named_setting(monkeypatch):
     (lambda c: c["sufficiency"].update(min_records=0), "at least 1"),
     (lambda c: c["exclusion_rules"].append({"rule": "grain_size_range"}), "minimum or a maximum"),
     (lambda c: c["eligibility_rules"].append({"flag_kind": "values_disagree", "rule": "in_scope"}), "one eligibility"),
+    # Owner, 2026-10-06: fixed rules a plan can never change (register 'primary_set_invariants').
+    (lambda c: _set_rule(c, "values_disagree", None, "in_scope"), "fixed rule"),
+    (lambda c: _set_rule(c, "exact_duplicate", None, "in_scope"), "fixed rule"),
+    (lambda c: _set_rule(c, "invalid_value", None, "in_scope"), "fixed rule"),
+    (lambda c: _set_rule(c, "possible_duplicate", "several candidates", "in_scope"), "fixed rule"),
+    (lambda c: _set_rule(c, "possible_duplicate", "several candidates", "duplicate_counted_once"), "fixed rule"),
+    (lambda c: c.update(eligibility_rules=[e for e in c["eligibility_rules"] if e["flag_kind"] != "values_disagree"]),
+     "fixed rule"),
+    (lambda c: c.update(eligibility_rules=[e for e in c["eligibility_rules"] if e["flag_kind"] != "invalid_value"]),
+     "fixed rule"),
+    (lambda c: c["eligibility_rules"].append({"flag_kind": "exact_duplicate", "category": "within tolerance",
+                                              "rule": "in_scope"}), "fixed rule"),
     (lambda c: c["eligibility_rules"].append({"flag_kind": "model_recalled", "rule": "out_of_scope"}),
      "flag rule codes"),
     (lambda c: c["sensitivity_analyses"].append("removal_after_lock"), "named once each"),
````

### `d52f771 Step 6: second-model review, saved verbatim`

````diff
d52f771eb44dcb485d71b63f7e4ea54887717cba

Step 6: second-model review, saved verbatim

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

### `23c24b2 Step 6 fix: the extraction check requires present, string-typed fields`

````diff
23c24b2dcc6854818b1fc45058da0c2a9030c476

Step 6 fix: the extraction check requires present, string-typed fields

Review finding 6: a missing or null method passed the CHECK as SQL NULL,
and numbers or objects passed as name and version. Migration 0003 (not yet
run on the live database) is changed in place: every key a JSON string and
the whole check coalesced to true or false. 6 of the 13 new cases failed on
the code before this change; the others were already refused.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 00ba5b9..4f8ae78 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4395,11 +4395,14 @@
       "note": "Migration 0003."
     },
     "history": [],
-    "notes": [],
+    "notes": [
+      "Step 6 review, finding 6 (2026-10-06): the check requires method, name and version as present JSON strings and is made explicitly true or false; migration 0003 was changed in place, before it ran on the live database."
+    ],
     "tests": [
+      "tests/test_checkpoints.py::test_records_are_stored_only_after_the_lock_with_how_they_were_extracted",
       "tests/test_migrations_step6.py::test_0003_a_new_record_states_its_extraction",
       "tests/test_migrations_step6.py::test_0003_keeps_every_check_of_0001_and_adds_one",
-      "tests/test_checkpoints.py::test_records_are_stored_only_after_the_lock_with_how_they_were_extracted"
+      "tests/test_migrations_step6.py::test_0003_refuses_a_missing_null_or_wrongly_typed_extraction_field"
     ]
   },
   {
diff --git a/hypocurate/db/migrations/versions/0003_record_extraction.py b/hypocurate/db/migrations/versions/0003_record_extraction.py
index 41221e1..51e4737 100644
--- a/hypocurate/db/migrations/versions/0003_record_extraction.py
+++ b/hypocurate/db/migrations/versions/0003_record_extraction.py
@@ -9,7 +9,8 @@ adapter's name and version) or, from step 8, by an agent, so that records extrac
 can always be told apart from records an agent extracts later (owner, 2026-10-05).
 
 - A new nullable column `record.extraction` (JSONB) with a CHECK on its shape: an object
-  whose `method` is 'adapter' or 'agent', with a non-empty `name` and `version`. Existing
+  whose `method`, `name` and `version` are present JSON strings, `method` 'adapter' or 'agent',
+  `name` and `version` non-empty; the check is made explicitly true or false. Existing
   rows keep NULL (the live database has none; every record before this step was a test row).
 - `hc_record_insert` is replaced: **every check of 0001 is kept unchanged, in the same
   order**, and one is added at the end: a new record must carry `extraction`.
@@ -31,10 +32,14 @@ down_revision = '0002'
 branch_labels = None
 depends_on = None
 
-SHAPE = ("extraction IS NULL OR (jsonb_typeof(extraction) = 'object' "
+# Every key present and a JSON string, and the whole condition true: a missing key or a JSON null
+# gives SQL NULL inside, which coalesce turns into false, so it cannot pass as an unknown result
+# (step 6 review, finding 6; changed in place before 0003 ran on the live database).
+SHAPE = ("extraction IS NULL OR coalesce(jsonb_typeof(extraction) = 'object' "
+         "AND jsonb_typeof(extraction->'method') = 'string' AND jsonb_typeof(extraction->'name') = 'string' "
+         "AND jsonb_typeof(extraction->'version') = 'string' "
          "AND (extraction->>'method') IN ('adapter', 'agent') "
-         "AND length(coalesce(extraction->>'name', '')) > 0 "
-         "AND length(coalesce(extraction->>'version', '')) > 0)")
+         "AND length(extraction->>'name') > 0 AND length(extraction->>'version') > 0, false)")
 
 # 0001's function, verbatim (restored by the downgrade).
 RECORD_INSERT_0001 = """
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 764f86d..67cd3d3 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -546,10 +546,13 @@ class Record(Base):
     extraction: Mapped[dict | None] = mapped_column(JSONB)
     created_at: Mapped[datetime] = created()
     __table_args__ = (
-        CheckConstraint("extraction IS NULL OR (jsonb_typeof(extraction) = 'object' "
+        CheckConstraint("extraction IS NULL OR coalesce(jsonb_typeof(extraction) = 'object' "
+                        "AND jsonb_typeof(extraction->'method') = 'string' "
+                        "AND jsonb_typeof(extraction->'name') = 'string' "
+                        "AND jsonb_typeof(extraction->'version') = 'string' "
                         "AND (extraction->>'method') IN ('adapter', 'agent') "
-                        "AND length(coalesce(extraction->>'name', '')) > 0 "
-                        "AND length(coalesce(extraction->>'version', '')) > 0)", name="extraction_shape"),
+                        "AND length(extraction->>'name') > 0 AND length(extraction->>'version') > 0, false)",
+                        name="extraction_shape"),
         UniqueConstraint("extraction_run_id", "source_version_id", "source_item_key", "item_index",
                          name="uq_record_origin_per_run"),
         Index("ix_record_source_version_id_source_item_key", "source_version_id", "source_item_key"),
diff --git a/tests/test_migrations_step6.py b/tests/test_migrations_step6.py
index e0c7627..0a233f8 100644
--- a/tests/test_migrations_step6.py
+++ b/tests/test_migrations_step6.py
@@ -160,6 +160,37 @@ def _record(conn, run, version, key, extraction):
                  dict(r=run, v=version, k=key, x=extraction))
 
 
+GOOD = {"method": "adapter", "name": "mpea_layout", "version": "1"}
+
+
+@pytest.mark.parametrize("extraction", [
+    {"name": "mpea_layout", "version": "1"},  # method missing (review finding 6)
+    {"method": None, "name": "mpea_layout", "version": "1"},
+    {"method": 1, "name": "mpea_layout", "version": "1"},
+    {"method": "adapter", "version": "1"},  # name missing
+    {"method": "adapter", "name": None, "version": "1"},
+    {"method": "adapter", "name": 5, "version": "1"},
+    {"method": "adapter", "name": {"a": 1}, "version": "1"},
+    {"method": "adapter", "name": "mpea_layout"},  # version missing
+    {"method": "adapter", "name": "mpea_layout", "version": None},
+    {"method": "adapter", "name": "mpea_layout", "version": 1},
+    {"method": "adapter", "name": "mpea_layout", "version": ["1"]},
+    {"method": "adapter", "name": "", "version": "1"},
+    "adapter",
+], ids=lambda x: json.dumps(x))
+def test_0003_refuses_a_missing_null_or_wrongly_typed_extraction_field(db, extraction):
+    """Review finding 6: every key present, a JSON string, and the whole check true (a missing
+    value must not pass as SQL NULL)."""
+    from model_builder import World
+    w = World(db)
+    rid = w.locked()
+    with pytest.raises(IntegrityError, match="ck_record_extraction_shape"):
+        with db.begin() as conn:
+            _record(conn, rid, w.version["mpea"], "row-x", json.dumps(extraction))
+    with db.begin() as conn:
+        _record(conn, rid, w.version["mpea"], "row-ok", json.dumps(GOOD))
+
+
 def test_0003_a_new_record_states_its_extraction(db):
     from model_builder import World
     w = World(db)
````

### `1821dcd Step 6 fix: survivors and groups never depend on database ids`

````diff
1821dcdce9a18d8dd2aaaaa98d31b0cb96270c27

Step 6 fix: survivors and groups never depend on database ids

Review finding 3: an incomplete survivor order let insertion order pick the
survivor, and an incomplete grouping left records without a group. The lock
now refuses either setting if it leaves out a chosen source (and validation
refuses empty lists); the final tie-breaker is (source, origin key, item
index). record_conditions carries that stable identity. 5 new tests failed
on the code before this change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index aa264b7..7d02a31 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -93,8 +93,8 @@ FIELDS = MappingProxyType({
                            "temperature; counts by test type and by phase. Never a row-level value, an "
                            "outcome value or a statistic derived from outcomes.",
     "gap_report": "The Analyst's gap report: the output of each Analyst stage of the run.",
-    "record_conditions": "Per stored record, for Inclusion (code): id, source, row number, kind, a hash of the "
-                         "stored record, whether it carries a DOI, identities as hashes (paper from the DOI, "
+    "record_conditions": "Per stored record, for Inclusion (code): id, source, row number, kind, its stable "
+                         "identity (source-version fingerprint, origin key, item index), a hash of the stored record, whether it carries a DOI, identities as hashes (paper from the DOI, "
                          "batch), composition, each "
                          "field's status, grain size and test temperature, and the category values from their "
                          "vocabularies. No outcome value, no value as reported, no free text.",
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index cff2979..6a175b6 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -297,6 +297,9 @@ def record_conditions(conn: Connection, ctx: Context) -> list[dict]:
                    "paper_reference": r.paper_reference, "paper_doi": r.paper_doi}
         out.append({
             "id": r.id, "source": r.source, "row": int(row.group(1)) if row else None, "kind": r.kind,
+            # Stable identity (step 6 review, findings 3 and 5): for tie-breaks and the freeze
+            # fingerprint, never a database id. The origin key carries no value.
+            "version_fingerprint": r.version_fingerprint, "origin": r.source_item_key, "item_index": r.item_index,
             # A hash of the stored record (for the freeze fingerprint): it carries no value.
             "fingerprint": hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"),
                                                      ensure_ascii=False).encode("utf-8")).hexdigest(),
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 4f8ae78..c06142c 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -167,6 +167,7 @@
     "tests": [
       "tests/test_adapter_tamu.py::test_one_group_the_dataset",
       "tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides",
+      "tests/test_checkpoints.py::test_the_lock_refuses_settings_that_leave_out_a_chosen_source",
       "tests/test_eligibility.py::test_grouping_is_read_from_the_locked_plan",
       "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
@@ -2308,14 +2309,17 @@
       "A DOI identifies the cited paper, not where a record was extracted: a compilation and a copied extract can both carry it. Preferring records extracted directly from the original paper would need explicit extraction-origin metadata, which does not exist.",
       "The step 1 answer file, its builder and README carry this wording since step 6 (owner's approval, 2026-10-05).",
       "Rule 1 can only decide a possible duplicate: paired records otherwise cite the same paper.",
-      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants').",
+      "Step 6 review, finding 3 (2026-10-06): the lock refuses a survivor order or a grouping that leaves out a chosen source, and the final tie-breaker is the record's stable identity (source, origin key, item index), never a database id."
     ],
     "tests": [
+      "tests/test_checkpoints.py::test_the_lock_refuses_settings_that_leave_out_a_chosen_source",
       "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
       "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_eligibility.py::test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi",
       "tests/test_eligibility.py::test_survivor_rule_three_the_lowest_row_within_one_source",
-      "tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order"
+      "tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order",
+      "tests/test_eligibility.py::test_the_survivor_does_not_depend_on_database_ids_or_insertion_order"
     ]
   },
   {
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index b18410c..b9920ca 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -52,6 +52,16 @@ def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
         version = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
         if plan["hypothesis_version"] != version:
             raise Refused("lock_rules", "invalid_plan", "the plan names another hypothesis version")
+        # Review finding 3: every chosen source has a survivor priority and a grouping unit.
+        chosen = set(conn.execute(text("SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id "
+                                       "WHERE rs.run_id = :r AND rs.source_version_id IS NOT NULL"),
+                                  dict(r=run_id)).scalars())
+        rules = plan["rules"]
+        for name, covered in (("survivor_source_order", set(rules["survivor_source_order"])),
+                              ("grouping", {g["source"] for g in rules["grouping"]})):
+            if chosen - covered:
+                raise Refused("lock_rules", "invalid_plan",
+                              f"{name} leaves out chosen sources: {', '.join(sorted(chosen - covered))}")
         ids = []
         for kind, value in tags.items():
             tid = conn.execute(text("SELECT id FROM tag_value WHERE kind = :k AND value = :v AND status = 'approved'"),
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index b25ad0c..5b52a71 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -220,9 +220,12 @@ def flag_rule(flag: Mapping, st: Settings) -> str | None:
 
 def survivor_key(rec: Mapping, st: Settings) -> tuple:
     """Register 'duplicate_survivor_rule': 1) the record that carries the original paper
-    reference (DOI); 2) the first source in the plan's order; 3) the lowest row."""
+    reference (DOI); 2) the first source in the plan's order; 3) the lowest row. The final
+    tie-breaker is the record's stable identity (source, origin key, item index), never a database
+    id (step 6 review, finding 3); the lock refuses a plan whose order leaves out a chosen source."""
     order = st.survivor_order.index(rec["source"]) if rec["source"] in st.survivor_order else len(st.survivor_order)
-    return (0 if rec["has_doi"] else 1, order, rec["row"] if rec["row"] is not None else math.inf, rec["id"])
+    return (0 if rec["has_doi"] else 1, order, rec["row"] if rec["row"] is not None else math.inf,
+            rec["source"], rec["origin"], rec["item_index"])
 
 
 # --- A whole set ---------------------------------------------------------------------------
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index ca72a7f..85cea40 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -132,6 +132,8 @@ def _check_template(c: dict) -> None:
         raise PlanError("a rule is out of range")
     order = r["survivor_source_order"]
     units = [g["source"] for g in r["grouping"]]
+    if not order or not units:
+        raise PlanError("the survivor order and the grouping name every chosen source")
     if len(set(order)) != len(order) or len(set(units)) != len(units) or any(set(g) != {"source", "unit"}
                                                                            for g in r["grouping"]):
         raise PlanError("the survivor order and the grouping name each source once")
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index 1c37626..2427f74 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -131,13 +131,14 @@ def test_record_conditions_carry_statuses_conditions_and_hashed_identities(engin
             dict(r=world.run))}
     assert [r["id"] for r in got] == sorted(stored)
     for r in got:
-        assert set(r) == {"id", "source", "row", "kind", "fingerprint", "has_doi", "paper", "batch", "composition",
-                          "status", "values", "categories"}
+        assert set(r) == {"id", "source", "row", "kind", "version_fingerprint", "origin", "item_index", "fingerprint",
+                          "has_doi", "paper", "batch", "composition", "status", "values", "categories"}
         assert len(r["fingerprint"]) == 64
         s = stored[r["id"]]
         assert set(r["status"]) == set(HARMONIZED_FIELDS)
         assert set(r["values"]) == {"grain_size", "test_temperature"} and not set(r["values"]) & OUTCOME_FIELDS
         assert r["row"] == int(s.source_item_key.rsplit(":", 1)[1])
+        assert (r["origin"], r["item_index"]) == (s.source_item_key, 0)
         doi = s.paper_doi if s.paper_doi and s.paper_doi.strip() else None
         assert r["has_doi"] == (doi is not None)
         assert r["paper"] == (identity_hash(doi_group_key(doi)) if doi else None)
diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index a64763d..2aea588 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -97,6 +97,25 @@ def test_an_invalid_plan_or_one_for_another_version_is_refused_and_logged(engine
     assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0
 
 
+@pytest.mark.parametrize("setting, value", [
+    ("survivor_source_order", ["mpea", "controlled_duplicates"]),  # tamu_fcc chosen but not ordered
+    ("survivor_source_order", []),
+    ("grouping", [{"source": "mpea", "unit": "paper"}]),  # tamu_fcc chosen but not grouped
+    ("grouping", []),
+])
+def test_the_lock_refuses_settings_that_leave_out_a_chosen_source(engine, setting, value):
+    """Review finding 3: the survivor order and the grouping must cover every chosen source, or a
+    survivor or a group would depend on something other than the plan."""
+    rid = pw.dispatched_run(engine, sources=("mpea", "tamu_fcc"))
+    content = reference_plan(pw.version_of(engine, rid))
+    content["rules"][setting] = value
+    with pytest.raises(Refused) as refused:
+        checkpoints.lock_rules(engine, rid, content)
+    assert refused.value.code == "invalid_plan"
+    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "invalid_plan")]
+    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0
+
+
 def test_the_lock_waits_for_the_run_lock(engine, monkeypatch):
     """The write path takes hc_write_lock first: while another transaction holds the run's lock
     the lock waits, then fails after the lock timeout, and nothing is written."""
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index f83a16d..9daf76a 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -35,7 +35,9 @@ def cond(i, source="mpea", comp=None, gs=10.0, temp=25.0, test_type="tension", m
                "microstructure": "converted" if micro else "not_reported",
                "phase_class": "converted" if phase else "not_reported"})
     st.update(status or {})
-    return {"id": i, "source": source, "row": i if row is None else row, "kind": kind, "fingerprint": "f" * 64,
+    row = i if row is None else row
+    return {"id": i, "source": source, "row": row, "origin": f"{source}.csv:row:{row}", "item_index": 0,
+            "version_fingerprint": "v" * 64, "kind": kind, "fingerprint": "f" * 64,
             "has_doi": doi, "paper": paper if doi else None, "batch": batch,
             "composition": comp if comp is not None else {"Co": 50.0, "Ni": 50.0}, "status": st,
             "values": {"grain_size": gs, "test_temperature": temp},
@@ -148,6 +150,25 @@ def test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order():
     assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)], reordered)[1] == "in_scope"
 
 
+@pytest.mark.parametrize("order", [["tamu_fcc"], ["mpea", "controlled_duplicates", "tamu_fcc"]])
+def test_the_survivor_does_not_depend_on_database_ids_or_insertion_order(order):
+    """Review finding 3: the same records with their database ids exchanged, and listed in another
+    order, keep the same survivor. The final tie-breaker is stable identity (source, origin key,
+    item index), never the database id; an incomplete source order is refused at the lock
+    (test_checkpoints)."""
+    plan = copy.deepcopy(PLAN)
+    plan["rules"]["survivor_source_order"] = order
+    survivors = set()
+    for a_id, b_id, reverse in ((1, 2, False), (2, 1, False), (1, 2, True), (2, 1, True)):
+        a = cond(a_id, "mpea", gs=10.0, row=7)
+        b = cond(b_id, "controlled_duplicates", gs=10.0, row=7)
+        records = [b, a] if reverse else [a, b]
+        got = decide(records + [cond(9, "mpea", gs=40.0, row=8)],
+                     [flag("exact_duplicate", "identical values", *sorted([a_id, b_id]))], plan)
+        survivors.add(next(r["source"] for r in (a, b) if got[r["id"]] == "in_scope"))
+    assert len(survivors) == 1
+
+
 def test_survivor_rule_three_the_lowest_row_within_one_source():
     st = el.settings(PLAN)
     a, b = cond(1, "mpea", row=900), cond(2, "mpea", row=12)
````

### `e7d62ab Step 6 fix: the freeze fingerprint uses stable record identity`

````diff
e7d62ab64bf278fd1f2d6c369fc490c8bdc77131

Step 6 fix: the freeze fingerprint uses stable record identity

Review finding 5: the fingerprint keyed records by database id, so identical
runs gave different fingerprints when ids differed. Records are now keyed by
(source-version fingerprint, origin key, item index) with their content hash.
The new test (two runs of one version in one database, unrelated records in
between) failed on the code before this change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index c06142c..5fde476 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4491,11 +4491,14 @@
       "note": null
     },
     "history": [],
-    "notes": [],
+    "notes": [
+      "Step 6 review, finding 5 (2026-10-06): the freeze fingerprint identifies each record by its stable identity (source-version fingerprint, origin key, item index) and content hash, never by database id. It does include the plan's fingerprint, and the plan names its hypothesis version by id, so runs of different versions differ by design."
+    ],
     "tests": [
-      "tests/test_eligibility.py::test_counts_known_at_the_freeze",
-      "tests/test_checkpoints.py::test_the_freeze_records_its_counts_and_fingerprint",
       "tests/test_checkpoints.py::test_no_eligible_record_means_no_dataset_is_frozen",
+      "tests/test_checkpoints.py::test_the_fingerprint_does_not_depend_on_database_ids",
+      "tests/test_checkpoints.py::test_the_freeze_records_its_counts_and_fingerprint",
+      "tests/test_eligibility.py::test_counts_known_at_the_freeze",
       "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
   },
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index b9920ca..c26cfec 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -15,7 +15,8 @@ transaction that re-checks the records, flags and decisions by id, it stores:
   minimums are met, as information (`stage_result` "dataset_freeze"); step 7 writes the
   analysis results and decides the outcome;
 - the fingerprint: SHA-256 of the canonical JSON of the plan's fingerprint, every set's records
-  (each with a hash of its stored content) and every set's rules, and the counts;
+  and rules, each record identified by its stable identity (source-version fingerprint, origin
+  key, item index) with a hash of its stored content, never by database id, and the counts;
 - `run_snapshot`, or, when no record is eligible, the run-level "no dataset frozen" row
   (PRD 5.6: no dataset is frozen and no test is run).
 """
@@ -105,10 +106,13 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
     counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
                                                             if by_id[i]["source"] == source])
                             for source in sorted({by_id[i]["source"] for i in members[el.PRIMARY]})}
+    # Review finding 5: records are identified by their stable identity (source-version
+    # fingerprint, origin key, item index) and their content hash, never by database id.
+    identity = {i: f"{r['version_fingerprint']}|{r['origin']}|{r['item_index']}" for i, r in by_id.items()}
     content = {
         "plan": data["plan"]["fingerprint"],
-        "sets": {key: [[i, by_id[i]["fingerprint"]] for i in ids] for key, ids in members.items()},
-        "rules": {key: {str(i): rule for i, rule in sorted(rules.items())} for key, rules in sets.items()},
+        "sets": {key: sorted([identity[i], by_id[i]["fingerprint"]] for i in ids) for key, ids in members.items()},
+        "rules": {key: dict(sorted((identity[i], rule) for i, rule in rules.items())) for key, rules in sets.items()},
         "counts": counts,
     }
     fp = hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index e0761fc..36d9428 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -47,6 +47,16 @@ def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
     _val(engine, "UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
          v=vid, d=domain)
     _val(engine, "UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)
+    return run_of_version(engine, vid, sources, marked)
+
+
+def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False) -> int:
+    """Another running run of an already dispatched hypothesis version."""
+    with engine.connect() as conn:
+        registry = dict(conn.execute(text(
+            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
+            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
+        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
     flags = json.dumps({"constructed_test_data": True} if marked else {})
     rid = _val(engine, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                        "VALUES (:v, true, CAST(:f AS jsonb)) RETURNING id", v=vid, f=flags)
diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 2aea588..7bf060a 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -367,6 +367,23 @@ def test_no_eligible_record_means_no_dataset_is_frozen(engine):
     assert stage(engine, rid) == "closed_without_freeze"
 
 
+def test_the_fingerprint_does_not_depend_on_database_ids(engine):
+    """Review finding 5: two identical runs in the same database, with an unrelated run's records
+    inserted between them (so every record id differs), give the same freeze fingerprint."""
+    first = pw.through_freeze(engine, sources=("mpea", "tamu_fcc"))
+    pw.through_freeze(engine, sources=("tamu_fcc",))  # unrelated inserts
+    second = pw.run_of_version(engine, pw.version_of(engine, first), sources=("mpea", "tamu_fcc"))
+    checkpoints.lock_rules(engine, second, reference_plan(pw.version_of(engine, first)))
+    extract.store_records(engine, second)
+    checks.run_checks(engine, second)
+    inclusion.decide_run(engine, second)
+    checkpoints.freeze_dataset(engine, second)
+    fp = {rid: q(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] for rid in (first, second)}
+    ids = {rid: q(engine, "SELECT min(id) FROM record WHERE extraction_run_id = :r", r=rid)[0][0] for rid in (first, second)}
+    assert ids[first] != ids[second]
+    assert fp[first] == fp[second]
+
+
 def test_the_same_steps_on_another_database_give_the_same_fingerprint(admin, database_url, template_database):
     """The freeze is deterministic: the same frozen sources, plan and steps give the same
     fingerprint, counts and decisions."""
````

### `b78f01c Step 6 fix: ambiguous groups keep their conflicts`

````diff
b78f01c10ecb11058983337ab30204f383c12b2a

Step 6 fix: ambiguous groups keep their conflicts

Review finding 4: an ambiguous group hid a definite conflict, so
possible_duplicates_separate admitted both conflicting values. Checks now
raises a conflict flag for the conflicting pair inside an ambiguous group,
and Inclusion applies identity, then conflict, then counted-once in a fixed
order. The reviewer's three-source example is tested by its resulting sets;
both new or changed tests failed on the code before this change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 5fde476..73804aa 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -398,6 +398,7 @@
     },
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_flag_is_the_answer_files",
+      "tests/test_eligibility.py::test_an_ambiguous_group_keeps_its_conflict_in_every_set",
       "tests/test_flags.py::test_a_dataset_source_is_its_own_paper",
       "tests/test_flags.py::test_a_group_whose_records_are_not_all_linked_is_ambiguous",
       "tests/test_flags.py::test_a_group_with_one_conflicting_pair_is_a_conflict",
@@ -425,7 +426,8 @@
       "Not reviewed by an expert.",
       "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance).",
       "A record with a missing test condition is also 'scope not confirmed': Checks still raises the possible-duplicate flag, and Inclusion applies the scope rule before the duplicate rule (owner, 2026-10-05).",
-      "A paper is identified by its DOI (derived key); a source grouped by dataset (Texas A&M) cites itself."
+      "A paper is identified by its DOI (derived key); a source grouped by dataset (Texas A&M) cites itself.",
+      "Step 6 review, finding 4 (2026-10-06): an ambiguous group that contains a definite conflict keeps it as its own conflict flag; the conflicting records stay out wherever conflicts are excluded, including 'possible_duplicates_separate'."
     ]
   },
   {
@@ -2371,11 +2373,13 @@
       }
     ],
     "notes": [
-      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants').",
+      "Step 6 review, finding 4 (2026-10-06): an ambiguous group that contains a definite conflict keeps it as its own conflict flag; the conflicting records stay out wherever conflicts are excluded, including 'possible_duplicates_separate'."
     ],
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files",
       "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
+      "tests/test_eligibility.py::test_an_ambiguous_group_keeps_its_conflict_in_every_set",
       "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
       "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set"
     ]
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 5b52a71..c9a885a 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -256,7 +256,10 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
             rules[r["id"]] = "scope_not_confirmed"
         elif _excluded(r, st):
             rules[r["id"]] = "excluded_by_rule"
-    for f in flags:  # 7
+    # 7, in a fixed order (review finding 4): unresolved identity, then conflicts, then counted once,
+    # so that a record in an ambiguous group and in a conflict gets the first that applies.
+    order = {"identity_unresolved": 0, "conflict_unresolved": 1, "duplicate_counted_once": 2}
+    for f in sorted(flags, key=lambda f: (order.get(flag_rule(f, st), 3), f["id"])):
         rule = flag_rule(f, st)
         members = [rid for rid in f["records"] if rid in records and rid not in rules]
         if rule in ("identity_unresolved", "conflict_unresolved"):
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 4bc1876..3dc71a8 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -21,9 +21,10 @@ Flags (owner, 2026-10-05):
     possible duplicate; beyond it → not a candidate (nothing says it is the same measurement).
   Candidate links form groups (connected components). A group with two or more records from
   one source, or one in which some pair is not linked, is ambiguous: `possible_duplicate`,
-  "several candidates" (nothing is paired on a guess). Otherwise a group with any conflicting
+  "several candidates" (nothing is paired on a guess); its definite conflicts, if any, get a
+  `values_disagree` flag of their own (review finding 4). Otherwise a group with any conflicting
   pair is a conflict, else a possible duplicate if any link is possible, else an exact
-  duplicate. One flag per group, naming all its records.
+  duplicate. One flag per group, naming all its records (plus that conflict flag).
 - Relative difference: |a − b| / min(|a|, |b|) (register 'values_disagree_tolerance').
 - The numbers compared are stored with the flag for audit (`compared_values`) and never
   returned to the Critic (step 5).
@@ -158,6 +159,12 @@ def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any]) -> list[Fl
         kinds = {kind for kind, _ in pairs.values()}
         if len(set(sources)) < len(sources) or len(pairs) < len(ids) * (len(ids) - 1) // 2:
             flags.append(Flag("possible_duplicate", "several candidates", ids, compared))
+            # Review finding 4: a definite conflict inside an ambiguous group is kept as its own
+            # flag, so that a set that counts the group separately still excludes it.
+            conflicting = sorted({i for (a, b), (kind, _) in pairs.items() if kind == "conflict" for i in (a, b)})
+            if conflicting:
+                flags.append(Flag("values_disagree", "differ beyond tolerance", conflicting,
+                                  {k: v for k, v in compared.items() if v["link"] == "conflict"}))
         elif "conflict" in kinds:
             flags.append(Flag("values_disagree", "differ beyond tolerance", ids, compared))
         else:
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index 9daf76a..433fd5c 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -198,6 +198,31 @@ def test_an_ambiguous_group_enters_with_none_of_its_records():
     assert decide(records, ambiguous, key="conflicts_survivor_value") == got
 
 
+def test_an_ambiguous_group_keeps_its_conflict_in_every_set():
+    """Review finding 4, the reviewer's example: A reports 400 with a DOI, B 400 without, C 440 with
+    A's DOI (three sources), and A's alloy has another grain size. A-C is a definite conflict, A-B a
+    possible duplicate, B-C no link: the group is ambiguous. The flags come from Checks' rules
+    (`flags.raise_flags`), and the resulting sets are checked, not only the labels."""
+    from test_flags import rec
+    plan = copy.deepcopy(PLAN)
+    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "controlled_duplicates", "unit": "paper"},
+                                 {"source": "tamu_fcc", "unit": "paper"}]
+    full = [rec(1, "mpea", ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
+            rec(3, "tamu_fcc", ys=440.0), rec(4, "mpea", gs=40.0, ys=300.0)]
+    from hypocurate.pipeline.flags import raise_flags
+    flags = [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
+             for n, f in enumerate(raise_flags(plan, full), start=1)]
+    records = [cond(1, "mpea"), cond(2, "controlled_duplicates", doi=False), cond(3, "tamu_fcc"),
+               cond(4, "mpea", gs=40.0)]
+    primary = decide(records, flags, plan)
+    assert {i: primary[i] for i in (1, 2, 3)} == {i: "identity_unresolved" for i in (1, 2, 3)}
+    separate = decide(records, flags, plan, "possible_duplicates_separate")
+    # The unresolved identity is lifted, the conflict is not: A and C stay out, B enters.
+    assert {i: separate[i] for i in (1, 2, 3)} == {1: "conflict_unresolved", 2: "in_scope", 3: "conflict_unresolved"}
+    survivor = decide(records, flags, plan, "conflicts_survivor_value")
+    assert {i: survivor[i] for i in (1, 2, 3)} == {i: "identity_unresolved" for i in (1, 2, 3)}
+
+
 def test_identity_applies_only_among_records_that_passed_the_earlier_rules():
     """Extract rows 13–14 (owner, 2026-10-05): the extract record is 'scope not confirmed'
     (rule 5 before rule 7); its MPEA twin survives. With scope not confirmed included, the
diff --git a/tests/test_flags.py b/tests/test_flags.py
index 2d8ccc5..58c8144 100644
--- a/tests/test_flags.py
+++ b/tests/test_flags.py
@@ -135,7 +135,9 @@ def test_a_group_with_one_conflicting_pair_is_a_conflict():
     # A possible link (paper unknown on 2) and a conflicting pair (1, 3) in one group: a conflict.
     got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
                  rec(3, "tamu_fcc", ys=440.0)], plan)
-    assert got[0][0] == "possible_duplicate" and got[0][1] == "several candidates"  # 2-3 not linked
+    # 2-3 not linked: ambiguous; the definite conflict 1-3 is kept as its own flag (review finding 4).
+    assert got == [("possible_duplicate", "several candidates", [1, 2, 3]),
+                   ("values_disagree", "differ beyond tolerance", [1, 3])]
 
 
 def test_a_dataset_source_is_its_own_paper():
````

### `65f76f9 Step 6 fix: sensitivity sets recompute their matching flags`

````diff
65f76f98569d3b342c21fd683890926e95ab12a6

Step 6 fix: sensitivity sets recompute their matching flags

Review finding 2: same_alloy_1_at_pct reused flags computed at the primary
precision. Checks now computes, for each sensitivity set whose matching
settings (same-alloy step, value statuses, grouping) differ, its own
duplicate, conflict and ambiguity flags and stores them (codes and ids)
with its result; Inclusion reads them through a new field, set_flags.
The reviewer's example (Co50.06/Ni49.94 vs Co50.04/Ni49.96) failed on the
code before this change (4 records where 2 are right). The one-change test
is corrected to accept identity changes from a set's own flags.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index 7d02a31..d812f41 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -93,6 +93,9 @@ FIELDS = MappingProxyType({
                            "temperature; counts by test type and by phase. Never a row-level value, an "
                            "outcome value or a statistic derived from outcomes.",
     "gap_report": "The Analyst's gap report: the output of each Analyst stage of the run.",
+    "set_flags": "From the completed Checks result, for Inclusion (code): per sensitivity set whose matching "
+                 "settings differ from the primary set's, its duplicate, conflict and ambiguity flags: kind and "
+                 "category (from their vocabularies) and record ids. Never the numbers compared.",
     "record_conditions": "Per stored record, for Inclusion (code): id, source, row number, kind, its stable "
                          "identity (source-version fingerprint, origin key, item index), a hash of the stored record, whether it carries a DOI, identities as hashes (paper from the DOI, "
                          "batch), composition, each "
@@ -136,7 +139,7 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
 # record's outcome directly or on its position relative to the tested relationship. It acts on
 # the flags Checks raised, by kind and category.
 CODE_ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
-    "inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind"})}),
+    "inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind", "set_flags"})}),
     "checks": MappingProxyType({"curation": frozenset({"plan", "records_full"})}),
 })
 
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 6a175b6..103a3ad 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -314,6 +314,21 @@ def record_conditions(conn: Connection, ctx: Context) -> list[dict]:
     return out
 
 
+def set_flags(conn: Connection, ctx: Context) -> dict:
+    """The per-set matching flags of the run's completed Checks result (step 6 review, finding 2):
+    codes and record ids only."""
+    output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'checks' "
+                               "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=ctx.run_id)).scalar_one_or_none()
+    stored = output.get("set_flags", {}) if isinstance(output, Mapping) else {}
+    out = {}
+    for key, flags in (stored.items() if isinstance(stored, Mapping) else ()):
+        out[vocab.code(key, vocab.SENSITIVITY_KEYS)] = [
+            {"kind": vocab.code(f.get("kind"), vocab.FLAG_KINDS), "category": vocab.code(f.get("category"), vocab.FLAG_CATEGORIES),
+             "records": [r for r in f.get("records", []) if isinstance(r, int) and not isinstance(r, bool)]}
+            for f in flags if isinstance(f, Mapping)]
+    return out
+
+
 def _flag_records(conn: Connection, ctx: Context) -> dict[int, list[int]]:
     out: dict[int, list[int]] = {}
     for flag_id, record_id in _rows(conn, "SELECT fr.flag_id, fr.record_id FROM flag_record fr "
@@ -477,5 +492,5 @@ READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
     "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
     "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
-    "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions,
+    "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions, "set_flags": set_flags,
 }
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 73804aa..980f3ed 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4309,12 +4309,15 @@
     "history": [],
     "notes": [
       "The reference script's 'discretionary removals' analysis (PRD 10: 438 ± 67 with four records removed) is not carried over: its records were chosen after seeing outcomes, so it cannot be named in a plan locked before the data (owner, 2026-10-05).",
-      "Related: 'no_multiplicity_adjustment'."
+      "Related: 'no_multiplicity_adjustment'.",
+      "Step 6 review, finding 2 (2026-10-06): a set that changes a matching setting (the same-alloy step, the accepted value statuses, the grouping) recomputes its duplicate, conflict and ambiguity flags under its own settings; Checks supplies them, so Inclusion stays outcome-blind. Its identity decisions can therefore change, not only the grain-size counts."
     ],
     "tests": [
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions",
       "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change",
       "tests/test_reference_sets.py::test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts",
-      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions"
+      "tests/test_sensitivity_matching.py::test_the_coarser_same_alloy_rule_recomputes_the_duplicates",
+      "tests/test_sensitivity_matching.py::test_the_one_change_rule_holds_with_recomputed_matching_flags"
     ]
   },
   {
@@ -4355,7 +4358,9 @@
       "note": null
     },
     "history": [],
-    "notes": [],
+    "notes": [
+      "Step 6 review, finding 2 (2026-10-06): Inclusion's list gains 'set_flags' (each sensitivity set's matching flags from the completed Checks result: codes and record ids, no numbers)."
+    ],
     "tests": [
       "tests/test_access_code_roles.py::test_the_code_lists_match_the_owners_decision",
       "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index c26cfec..2d7edc0 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -100,7 +100,7 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
     data = role_input(bind_code(engine, run_id, "inclusion"))
     plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
     by_id = {r["id"]: r for r in records}
-    sets = el.all_sets(plan, records, flags)
+    sets = el.all_sets(plan, records, flags, data["set_flags"])
     members = {key: el.members(rules) for key, rules in sets.items()}
     counts: dict[str, Any] = {key: el.counts(plan, by_id, ids, key) for key, ids in members.items()}
     counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
diff --git a/hypocurate/pipeline/checks.py b/hypocurate/pipeline/checks.py
index 6f82547..ac5256d 100644
--- a/hypocurate/pipeline/checks.py
+++ b/hypocurate/pipeline/checks.py
@@ -13,7 +13,7 @@ from sqlalchemy.dialects.postgresql import JSONB
 
 from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
-from hypocurate.pipeline.flags import Flag, raise_flags
+from hypocurate.pipeline.flags import Flag, raise_flags, set_flags
 from hypocurate.pipeline.writes import Refused, code_stage, flag_index, record_ids, write
 
 
@@ -21,6 +21,7 @@ def run_checks(engine: Engine, run_id: int) -> list[Flag]:
     data = role_input(bind_code(engine, run_id, "checks"))
     plan, records = data["plan"]["content"], data["records_full"]
     flags = raise_flags(plan, records)
+    per_set = set_flags(plan, records)
     read_ids = sorted(r["id"] for r in records)
 
     def body(conn: Connection, stage: str):
@@ -42,7 +43,11 @@ def run_checks(engine: Engine, run_id: int) -> list[Flag]:
         for f in flags:
             counts[f"{f.kind}/{f.category}"] = counts.get(f"{f.kind}/{f.category}", 0) + 1
         code_stage(conn, run_id, "checks", {"plan": data["plan"]["fingerprint"], "records": len(read_ids)},
-                   {"flags": dict(sorted(counts.items()))})
+                   {"flags": dict(sorted(counts.items())),
+                    # Step 6 review, finding 2: the matching flags of each sensitivity set whose matching
+                    # settings differ (kind, category, records; the numbers stay in Checks).
+                    "set_flags": {key: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
+                                  for key, fs in per_set.items()}})
         return flags
 
     return write(engine, run_id, "checks", "raise_flags", body)
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index c9a885a..4099330 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -281,9 +281,21 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
     return rules
 
 
-def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping]) -> dict[str, dict[int, str]]:
-    """The primary set and every sensitivity set the plan names."""
-    return {key: decide(plan, records, flags, key) for key in (PRIMARY, *plan["sensitivity_analyses"])}
+def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | None) -> list[Mapping]:
+    """The flags set `key` applies: its own matching flags from Checks where its matching settings
+    differ (step 6 review, finding 2), with the primary set's invalid-value flags; else the primary
+    set's flags."""
+    if not set_flags or key not in set_flags:
+        return flags
+    own = [{"id": 10 ** 12 + n, **f} for n, f in enumerate(set_flags[key])]
+    return [f for f in flags if f["kind"] == "invalid_value"] + own
+
+
+def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping],
+             set_flags: Mapping[str, list] | None = None) -> dict[str, dict[int, str]]:
+    """The primary set and every sensitivity set the plan names, each with its own flags."""
+    return {key: decide(plan, records, flags_for(key, flags, set_flags), key)
+            for key in (PRIMARY, *plan["sensitivity_analyses"])}
 
 
 def members(rules: Mapping[int, str]) -> list[int]:
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 3dc71a8..125a601 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -57,15 +57,15 @@ def relative_difference(a: float, b: float) -> float:
     return abs(a - b) / small if small > 0 else math.inf
 
 
-def _value(rec: Mapping, f: str) -> Any:
+def _value(rec: Mapping, f: str, statuses=VALUE_STATUSES) -> Any:
     entry = rec["harmonized"].get(f) if isinstance(rec.get("harmonized"), Mapping) else None
-    if isinstance(entry, Mapping) and entry.get("status") in VALUE_STATUSES:
+    if isinstance(entry, Mapping) and entry.get("status") in statuses:
         return entry.get("value")
     return None
 
 
-def _number(rec: Mapping, f: str) -> float | None:
-    v = _value(rec, f)
+def _number(rec: Mapping, f: str, statuses=VALUE_STATUSES) -> float | None:
+    v = _value(rec, f, statuses)
     return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None
 
 
@@ -92,11 +92,30 @@ def invalid_values(records: Iterable[Mapping], outcome: str) -> list[Flag]:
     return out
 
 
-def _condition(a: Mapping, b: Mapping) -> str:
+@dataclass(frozen=True)
+class Matching:
+    """The settings that decide which records are compared (step 6 review, finding 2): the
+    same-alloy step, the tolerance, the grouping (a dataset cites itself) and the value statuses
+    that count as known."""
+    decimals: int
+    tolerance: float
+    grouping: tuple
+    statuses: tuple
+
+
+def matching(plan: Mapping[str, Any], key: str = "primary") -> Matching:
+    """The matching settings of set `key` under the locked plan (its own change applied)."""
+    from hypocurate.pipeline.eligibility import settings
+    st = settings(plan, key)
+    return Matching(st.decimals, plan["rules"]["duplicate_tolerance"], tuple(sorted(st.grouping.items())),
+                    tuple(sorted(st.statuses)))
+
+
+def _condition(a: Mapping, b: Mapping, statuses=VALUE_STATUSES) -> str:
     """'same', 'unknown' (a condition missing on one side) or 'differs'."""
     state = "same"
     for f in ("test_type", "test_temperature"):
-        va, vb = _value(a, f), _value(b, f)
+        va, vb = _value(a, f, statuses), _value(b, f, statuses)
         if va is None or vb is None:
             state = "unknown"
         elif va != vb:
@@ -104,16 +123,17 @@ def _condition(a: Mapping, b: Mapping) -> str:
     return state
 
 
-def _link(a: Mapping, b: Mapping, plan: Mapping, grouping: Mapping) -> tuple[str, dict] | None:
+def _link(a: Mapping, b: Mapping, plan: Mapping, m: Matching) -> tuple[str, dict] | None:
     """The candidate link between two records of different sources, or None."""
-    tol, outcome = plan["rules"]["duplicate_tolerance"], plan["variables"]["outcome"]["field"]
-    ga, gb, ya, yb = (_number(a, "grain_size"), _number(b, "grain_size"), _number(a, outcome), _number(b, outcome))
+    tol, outcome, st, grouping = m.tolerance, plan["variables"]["outcome"]["field"], m.statuses, dict(m.grouping)
+    ga, gb, ya, yb = (_number(a, "grain_size", st), _number(b, "grain_size", st), _number(a, outcome, st),
+                      _number(b, outcome, st))
     if None in (ga, gb, ya, yb) or relative_difference(ga, gb) > tol:
         return None
     pa, pb = paper(a, grouping), paper(b, grouping)
     if pa is not None and pb is not None and pa != pb:
         return None
-    cond = _condition(a, b)
+    cond = _condition(a, b, st)
     if cond == "differs":
         return None
     numbers = {"grain_size": [ga, gb], outcome: [ya, yb], "relative_difference": relative_difference(ya, yb)}
@@ -123,19 +143,18 @@ def _link(a: Mapping, b: Mapping, plan: Mapping, grouping: Mapping) -> tuple[str
     return ("possible", numbers) if within else None
 
 
-def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any]) -> list[Flag]:
-    rules = plan["rules"]
-    grouping = {g["source"]: g["unit"] for g in rules["grouping"]}
+def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any], m: Matching | None = None) -> list[Flag]:
+    m = m or matching(plan)
     by_alloy: dict[str, list[Mapping]] = defaultdict(list)
     for r in records:
-        comp = _value(r, "composition")
+        comp = _value(r, "composition", m.statuses)
         if isinstance(comp, Mapping) and comp:
-            by_alloy[same_alloy_key(dict(comp), rules["same_alloy_decimals"])].append(r)
+            by_alloy[same_alloy_key(dict(comp), m.decimals)].append(r)
     links: dict[tuple[int, int], tuple[str, dict]] = {}
     for group in by_alloy.values():
         for a, b in combinations(sorted(group, key=lambda r: r["id"]), 2):
             if a["source"] != b["source"]:
-                link = _link(a, b, plan, grouping)
+                link = _link(a, b, plan, m)
                 if link:
                     links[(a["id"], b["id"])] = link
     parent: dict[int, int] = {}
@@ -179,3 +198,16 @@ def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any]) -> list[Fl
 def raise_flags(plan: Mapping[str, Any], records: list[Mapping]) -> list[Flag]:
     """Every flag for the run's records under the locked plan, in a fixed order."""
     return invalid_values(records, plan["variables"]["outcome"]["field"]) + duplicate_groups(records, plan)
+
+
+def set_flags(plan: Mapping[str, Any], records: list[Mapping]) -> dict[str, list[Flag]]:
+    """For each sensitivity set whose matching settings differ from the primary set's, the
+    duplicate, conflict and ambiguity flags under its own settings (step 6 review, finding 2).
+    Invalid values do not depend on matching; the set uses the primary set's."""
+    primary = matching(plan)
+    out = {}
+    for key in plan["sensitivity_analyses"]:
+        m = matching(plan, key)
+        if m != primary:
+            out[key] = duplicate_groups(records, plan, m)
+    return out
diff --git a/hypocurate/pipeline/inclusion.py b/hypocurate/pipeline/inclusion.py
index 1786193..a53c9d2 100644
--- a/hypocurate/pipeline/inclusion.py
+++ b/hypocurate/pipeline/inclusion.py
@@ -27,7 +27,7 @@ from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarke
 def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
     data = role_input(bind_code(engine, run_id, "inclusion"))
     plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
-    sets = el.all_sets(plan, records, flags)
+    sets = el.all_sets(plan, records, flags, data["set_flags"])
     read_ids = sorted(r["id"] for r in records)
     read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
 
diff --git a/tests/pipeline_fixtures.py b/tests/pipeline_fixtures.py
index 5918979..45a96aa 100644
--- a/tests/pipeline_fixtures.py
+++ b/tests/pipeline_fixtures.py
@@ -36,6 +36,8 @@ def decisions(engine, run_id) -> dict:
             "WHERE r.extraction_run_id = :r"), dict(r=run_id)).all()
         stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
                              dict(r=run_id)).scalar_one()
+        checks = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'checks'"),
+                              dict(r=run_id)).scalar_one()
         sets = {}
         for key, rid in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a LEFT JOIN "
                                           "analysis_set_record asr ON asr.analysis_set_id = a.id WHERE a.run_id = :r"),
@@ -54,4 +56,5 @@ def decisions(engine, run_id) -> dict:
         rules[key] = {**primary, **{int(i): rule for i, rule in diff.items()}}
     return {"origin": {r.id: r.source_item_key for r in rows}, "source": {r.id: r.source for r in rows},
             "rules": rules, "sets": sets, "conditions": conditions,
-            "flags": [{"id": f.id, "kind": f.kind, "category": f.category, "records": list(f.records)} for f in flags]}
+            "flags": [{"id": f.id, "kind": f.kind, "category": f.category, "records": list(f.records)} for f in flags],
+            "set_flags": checks.get("set_flags", {})}
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index 36d9428..ca11e75 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -23,6 +23,50 @@ def registered(engine, keys=SOURCE_KEYS) -> dict[str, int]:
     return {k: register(engine, k).version_id for k in keys}
 
 
+def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
+    """Registers each source key with one sealed version holding the given file (MPEA layout for
+    'mpea' and 'controlled_duplicates'), with the settings of the code's source definition."""
+    from hypocurate.sources.versions import SOURCES, files_digest, version_identity
+    out = {}
+    for key, content in files.items():
+        d = SOURCES[key]
+        name = d.data_files[0]
+        with engine.begin() as conn:
+            sid = conn.execute(text(
+                "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
+                "VALUES (:k, :n, :t, :l, :d, 'available', true, :u) RETURNING id"),
+                dict(k=key, n=d.name, t=d.source_type, l=d.licence, d=d.data_kind, u=d.grouping_unit)).scalar()
+            vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) "
+                                    "VALUES (:s, 'test file', '2026-10-06') RETURNING id"), dict(s=sid)).scalar()
+            import hashlib
+            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:v, :p, :h, :c)"),
+                         dict(v=vid, p=name, h=hashlib.sha256(content).hexdigest(), c=content))
+            digest = files_digest({name: content})
+            conn.execute(text("UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v"),
+                         dict(v=vid, fp=version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)))
+        out[key] = vid
+    return out
+
+
+def mpea_csv(rows: list[dict]) -> bytes:
+    """An MPEA-layout file: the frozen header, then rows given as {column: value} (others blank)."""
+    import csv, io
+    from hypocurate.sources.adapters.mpea_layout import HEADER
+    out = io.StringIO()
+    w = csv.writer(out, lineterminator="\n")
+    w.writerow(HEADER)
+    for r in rows:
+        w.writerow([r.get(h, "") for h in HEADER])
+    return out.getvalue().encode("utf-8")
+
+
+def mpea_row(formula, gs, ys, doi="10.1016/j.test.2026.001", test="T", temperature="25.0"):
+    return {"FORMULA": formula, "PROPERTY: Microstructure": "FCC", "PROPERTY: BCC/FCC/other": "FCC",
+            "PROPERTY: grain size ($\\mu$m)": str(gs), "PROPERTY: Type of test": test,
+            "PROPERTY: Test temperature ($^\\circ$C)": temperature, "PROPERTY: YS (MPa)": str(ys),
+            "PROPERTY: UTS (MPa)": str(ys * 2), "REFERENCE: doi": doi}
+
+
 def _val(engine, sql, **params):
     with engine.begin() as conn:
         result = conn.execute(text(sql), params)
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index 2427f74..c12c77c 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -47,7 +47,8 @@ def test_the_code_lists_match_the_owners_decision():
     assert CODE_ROLES == ("inclusion", "checks") and ALL_ROLES == ROLES + CODE_ROLES
     assert not set(CODE_ROLES) & set(ALLOWED)  # the agent table is unchanged
     assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {"inclusion": {"curation"}, "checks": {"curation"}}
-    assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind"}
+    # set_flags: step 6 review, finding 2 (each sensitivity set's matching flags, codes and ids only).
+    assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind", "set_flags"}
     assert allowed("checks", "curation") == {"plan", "records_full"}
     for role in CODE_ROLES:
         for stage in ("none", "before_lock", "analysis", "closed_without_freeze", "final", "final_without_freeze"):
@@ -111,7 +112,7 @@ def test_inclusion_receives_no_outcome_value(engine):
     outcome values; Checks' input (all values, by design) is the positive control."""
     world = aw.build(engine, "curation")
     inclusion = role_input(bind_code(engine, world.run, "inclusion"))
-    assert set(inclusion) == {"plan", "record_conditions", "flags_kind"}
+    assert set(inclusion) == {"plan", "record_conditions", "flags_kind", "set_flags"}
     assert leaks(inclusion, aw.PLANTED.values()) == []
     assert aw.DIRECTION not in json.dumps(inclusion)
     checks = role_input(bind_code(engine, world.run, "checks"))
@@ -119,6 +120,7 @@ def test_inclusion_receives_no_outcome_value(engine):
     rows = [r for r in audit(engine, world.run) if r.role in CODE_ROLES and r.function != "bind"]
     assert {(r.role, r.function, r.allowed) for r in rows} == {
         ("inclusion", "plan", True), ("inclusion", "record_conditions", True), ("inclusion", "flags_kind", True),
+        ("inclusion", "set_flags", True),
         ("checks", "plan", True), ("checks", "records_full", True)}
 
 
diff --git a/tests/test_flags.py b/tests/test_flags.py
index 58c8144..c3c710c 100644
--- a/tests/test_flags.py
+++ b/tests/test_flags.py
@@ -206,4 +206,5 @@ def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_outcome_f
     assert "hypocurate.pipeline.profile" not in imported
     plan_keys = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                  and isinstance(n.value, ast.Name) and n.value.id == "plan" and isinstance(n.slice, ast.Constant)}
-    assert plan_keys == {"rules", "variables"}
+    # Step 6 review, finding 2: the names of the sensitivity sets, to compute each set's own flags.
+    assert plan_keys == {"rules", "variables", "sensitivity_analyses"}
diff --git a/tests/test_reference_sets.py b/tests/test_reference_sets.py
index e535b20..317e847 100644
--- a/tests/test_reference_sets.py
+++ b/tests/test_reference_sets.py
@@ -102,10 +102,22 @@ CASCADE = {"in_scope", "single_grain_size", "duplicate_counted_once"}
 SCOPE_FIELDS = ("test_type", "test_temperature", "test_temperature_band", "microstructure", "phase_class")
 
 
+def _regrouped(key, run):
+    """Records whose duplicate group differs under the set's own matching flags (step 6 review,
+    finding 2): a matching change can change identity decisions, not only grain-size counts."""
+    if key not in run["set_flags"]:
+        return set()
+    own = {frozenset(f["records"]) for f in run["set_flags"][key]}
+    primary = {frozenset(f["records"]) for f in run["flags"] if f["kind"] != "invalid_value"}
+    return set().union(*(own ^ primary)) if own ^ primary else set()
+
+
 def _direct(key, run, i):
     """Is record i one the set's named change applies to directly?"""
     c, primary = run["conditions"][i], run["rules"]["primary"][i]
     in_flag = lambda kind: any(i in f["records"] for f in run["flags"] if f["kind"] == kind)
+    if i in _regrouped(key, run):
+        return True
     return {
         "no_exclusions": primary == "excluded_by_rule",
         "tension_and_compression": c["categories"]["test_type"] == "compression",
@@ -137,7 +149,9 @@ def _check_one_change(run):
             assert key == "same_alloy_1_at_pct" or alloy(i) in touched_alloys or i in touched_groups, \
                 (key, run["origin"][i])
             if key == "same_alloy_1_at_pct":
-                assert {primary[i], other[i]} == {"in_scope", "single_grain_size"}
+                # Corrected after the review (finding 2): besides the grain-size count, identity
+                # decisions change for records regrouped by the set's own flags (direct, above).
+                assert {primary[i], other[i]} <= {"in_scope", "single_grain_size", "duplicate_counted_once"}
         assert run["sets"][key] == {i for i, r in other.items() if r == "in_scope"}
         differing_total[key] = len(differing)
     return differing_total
diff --git a/tests/test_sensitivity_matching.py b/tests/test_sensitivity_matching.py
new file mode 100644
index 0000000..f38ec5a
--- /dev/null
+++ b/tests/test_sensitivity_matching.py
@@ -0,0 +1,58 @@
+"""Step 6 review, finding 2: a sensitivity set that changes a matching setting recomputes the
+matching flags under its own settings. Checks supplies them (Inclusion stays blind); every other
+rule is unchanged.
+
+The reviewer's example, through the real pipeline: Co50.06/Ni49.94 in one source and
+Co50.04/Ni49.96 in another, each at two grain sizes, the same paper and values. At 0.1 at.% they
+are two alloys (four records enter); at 1 at.% they are one alloy and each grain size is the same
+measurement reported twice, so two records enter, not four."""
+from __future__ import annotations
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+
+
+@pytest.fixture
+def run(db):
+    pw.registered_files(db, {
+        "mpea": pw.mpea_csv([pw.mpea_row("Co50.06Ni49.94", 10.0, 300.0), pw.mpea_row("Co50.06Ni49.94", 40.0, 250.0)]),
+        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50.04Ni49.96", 10.0, 300.0),
+                                              pw.mpea_row("Co50.04Ni49.96", 40.0, 250.0)])})
+    rid = pw.through_freeze(db, sources=("mpea", "controlled_duplicates"), marked=True)
+    with db.connect() as conn:
+        sets = {}
+        for key, origin in conn.execute(text(
+                "SELECT a.key, r.source_item_key || '@' || s.key FROM analysis_set a "
+                "JOIN analysis_set_record asr ON asr.analysis_set_id = a.id JOIN record r ON r.id = asr.record_id "
+                "JOIN source_version sv ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
+                "WHERE a.run_id = :r"), dict(r=rid)):
+            sets.setdefault(key, set()).add(origin)
+        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
+                             dict(r=rid)).scalar_one()
+    from pipeline_fixtures import decisions
+    return sets, stage, decisions(db, rid)
+
+
+def test_the_coarser_same_alloy_rule_recomputes_the_duplicates(run):
+    sets, stage, _ = run
+    assert len(sets["primary"]) == 4  # two alloys at 0.1 at.%, each at two grain sizes
+    coarse = sets["same_alloy_1_at_pct"]
+    assert len(coarse) == 2
+    assert {o.split("@")[1] for o in coarse} == {"mpea"}  # the MPEA records survive (source order)
+    assert stage["rules"]["same_alloy_1_at_pct"]["duplicate_counted_once"] == 2
+
+
+def test_every_other_set_keeps_the_primary_flags(run):
+    sets, _, _ = run
+    for key in ("no_exclusions", "tension_and_compression", "scope_not_confirmed_included",
+                "possible_duplicates_separate", "conflicts_survivor_value"):
+        assert sets[key] == sets["primary"], key
+
+
+def test_the_one_change_rule_holds_with_recomputed_matching_flags(run):
+    """The corrected one-change test accepts identity changes that come from the set's own flags."""
+    from test_reference_sets import _check_one_change
+    differing = _check_one_change(run[2])
+    assert differing["same_alloy_1_at_pct"] == 2
````

### `cbf99d1 Step 6 fix: Checks are bound to the exact records they covered`

````diff
cbf99d1b00a4e577149c88b0c5e52c172f7d1e47

Step 6 fix: Checks are bound to the exact records they covered

Review finding 1: Checks could be skipped, or a source stored after them,
and Inclusion and the freeze still accepted the result. Checks now run only
when no chosen source is pending, storage refuses after Checks, and the
Checks result records its binding (record identities and flags); Inclusion
and the freeze refuse without it or when it does not match. The three new
tests (skipped Checks; Checks before the extract; a conflicting record
added after Checks) failed on the code before this change. Two existing
tests follow the new order (listed in the summary). Register entry
checks_bound_to_records.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 980f3ed..a8ea61d 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4693,5 +4693,52 @@
       "tests/test_plan.py::test_invalid_plans_are_refused",
       "tests/test_plan.py::test_the_plan_choices_that_remain"
     ]
+  },
+  {
+    "key": "checks_bound_to_records",
+    "name": "Checks cover exactly the records decided on",
+    "state": "in_force",
+    "statement": "Checks run only when every chosen source has been stored (or has failed), and no record is stored after them. The completed Checks result records exactly which records (by stable identity) and flags it covered; Inclusion and the dataset freeze refuse, and log the refusal, without a completed Checks result or when it does not cover exactly the run's records and flags.",
+    "value": {
+      "text": "extraction, then Checks, then Inclusion and the freeze, bound by the record collection",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Every eligibility decision and every freeze.",
+    "reason": "Step 6 review, finding 1: Checks could be skipped or become stale (a source stored after Checks) while Inclusion and the freeze still accepted the result.",
+    "evidence": [
+      "docs/reviews/step06_review_chatgpt.md, finding 1; accepted by the owner on 2026-10-06."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
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
+          "ref": "python:hypocurate.pipeline.writes:require_checks_cover"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.writes:binding"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "A source refused by the constructed-data guard stays pending, so Checks cannot run until it is marked failed: the run's orchestration (step 9) must do that."
+    ],
+    "tests": [
+      "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze",
+      "tests/test_checkpoints.py::test_checks_wait_until_every_chosen_source_is_stored",
+      "tests/test_checkpoints.py::test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze"
+    ]
   }
 ]
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index 2d7edc0..d18f274 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -34,7 +34,8 @@ from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
 from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
 from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, log_refusal,
-                                        record_ids, run_record_sources, write)
+                                        record_identity, record_ids, require_checks_cover, run_record_sources,
+                                        write)
 
 
 def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
@@ -118,6 +119,7 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
     fp = hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
     read_ids = sorted(by_id)
     read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
+    identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
 
     def body(conn: Connection, stage: str):
         if stage != "curation":
@@ -127,6 +129,7 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
             raise Refused("freeze_dataset", "constructed_data_unmarked")
         if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
             raise Refused("freeze_dataset", "changed_since_read")
+        require_checks_cover(conn, run_id, "freeze_dataset", identity_of, [(k, c, r) for _, k, c, r in read_flags])
         stored = dict(conn.execute(text("SELECT record_id, rule FROM run_record WHERE run_id = :r"),
                                    dict(r=run_id)).all())
         if stored != sets[el.PRIMARY] or _set_records(conn, run_id) != members:
diff --git a/hypocurate/pipeline/checks.py b/hypocurate/pipeline/checks.py
index ac5256d..030c073 100644
--- a/hypocurate/pipeline/checks.py
+++ b/hypocurate/pipeline/checks.py
@@ -1,7 +1,7 @@
 """Checks (code; PRD 4, 5.3; build step 6): raise the flags of a run's records.
 
 Reads through its own access object (`dispatch.bind_code(…, "checks")`: the locked plan and
-every stored value), computes the flags with `pipeline.flags` (per-record and pairwise rules
+every stored value) once every chosen source is stored, computes the flags with `pipeline.flags` (per-record and pairwise rules
 only), then writes them in one transaction under the run's lock that re-checks the records by
 id. Checks never decides eligibility. Flags are raised once per run, before the freeze; the
 numbers compared are stored for audit and never returned to the Critic.
@@ -14,7 +14,8 @@ from sqlalchemy.dialects.postgresql import JSONB
 from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline.flags import Flag, raise_flags, set_flags
-from hypocurate.pipeline.writes import Refused, code_stage, flag_index, record_ids, write
+from hypocurate.pipeline.writes import (Refused, binding, code_stage, flag_index, pending_sources, record_ids,
+                                        record_identity, write)
 
 
 def run_checks(engine: Engine, run_id: int) -> list[Flag]:
@@ -23,6 +24,8 @@ def run_checks(engine: Engine, run_id: int) -> list[Flag]:
     flags = raise_flags(plan, records)
     per_set = set_flags(plan, records)
     read_ids = sorted(r["id"] for r in records)
+    identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
+    covered = binding(identity_of.values(), [(f.kind, f.category, [identity_of[i] for i in f.records]) for f in flags])
 
     def body(conn: Connection, stage: str):
         if stage != "curation":
@@ -31,6 +34,8 @@ def run_checks(engine: Engine, run_id: int) -> list[Flag]:
                 "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'checks')"),
                 dict(r=run_id)).scalar_one():
             raise Refused("raise_flags", "already_done")
+        if pending_sources(conn, run_id):
+            raise Refused("raise_flags", "extraction_unfinished")
         if record_ids(conn, run_id) != read_ids:
             raise Refused("raise_flags", "changed_since_read")
         for f in flags:
@@ -43,7 +48,7 @@ def run_checks(engine: Engine, run_id: int) -> list[Flag]:
         for f in flags:
             counts[f"{f.kind}/{f.category}"] = counts.get(f"{f.kind}/{f.category}", 0) + 1
         code_stage(conn, run_id, "checks", {"plan": data["plan"]["fingerprint"], "records": len(read_ids)},
-                   {"flags": dict(sorted(counts.items())),
+                   {"flags": dict(sorted(counts.items())), "binding": covered,
                     # Step 6 review, finding 2: the matching flags of each sensitivity set whose matching
                     # settings differ (kind, category, records; the numbers stay in Checks).
                     "set_flags": {key: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
diff --git a/hypocurate/pipeline/extract.py b/hypocurate/pipeline/extract.py
index ec69724..4a7401c 100644
--- a/hypocurate/pipeline/extract.py
+++ b/hypocurate/pipeline/extract.py
@@ -52,6 +52,9 @@ def store_source(engine: Engine, run_id: int, source_key: str) -> int:
             raise Refused("store_records", "stage_mismatch", "the source is not chosen for this run")
         if row.search_status != "pending":
             raise Refused("store_records", "already_done")
+        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'checks')"),
+                        dict(r=run_id)).scalar_one():
+            raise Refused("store_records", "checks_done")
         if constructed_unmarked(conn, run_id, [source_key]):
             raise Refused("store_records", "constructed_data_unmarked")
         try:
diff --git a/hypocurate/pipeline/inclusion.py b/hypocurate/pipeline/inclusion.py
index a53c9d2..5ecf603 100644
--- a/hypocurate/pipeline/inclusion.py
+++ b/hypocurate/pipeline/inclusion.py
@@ -20,8 +20,8 @@ from sqlalchemy import Connection, Engine, text
 from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
-from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, record_ids,
-                                        run_record_sources, write)
+from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, record_identity,
+                                        record_ids, require_checks_cover, run_record_sources, write)
 
 
 def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
@@ -30,6 +30,7 @@ def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
     sets = el.all_sets(plan, records, flags, data["set_flags"])
     read_ids = sorted(r["id"] for r in records)
     read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
+    identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
 
     def body(conn: Connection, stage: str):
         if stage != "curation":
@@ -40,6 +41,7 @@ def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
             raise Refused("decide", "constructed_data_unmarked")
         if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
             raise Refused("decide", "changed_since_read")
+        require_checks_cover(conn, run_id, "decide", identity_of, [(k, c, r) for _, k, c, r in read_flags])
         primary = sets[el.PRIMARY]
         if primary:
             conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)"),
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index 1c38ca0..fc51e2e 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -10,6 +10,11 @@ layer while holding the run's lock. The write transaction that follows takes the
 and re-checks, by ids and codes only (never record values), that nothing it read has changed
 since: the stage, the records, the flags, the decisions.
 
+**Order of the steps** (step 6 review, finding 1): Checks runs only when every chosen source is
+stored or failed; nothing is stored after Checks; the completed Checks result records exactly
+which records (by stable identity) and flags it covered (`binding`), and Inclusion and the freeze
+refuse unless that binding matches the run's records and flags.
+
 **A refusal is logged, then raised** (PRD 14.2: changes after a checkpoint are rejected and
 logged). Our own refusals (the stage has moved on, something changed since it was read,
 constructed data in a run not marked as a test) and the database's (a trigger or a
@@ -22,6 +27,7 @@ the process log (`hypocurate.pipeline`) is the fallback.
 """
 from __future__ import annotations
 
+import hashlib
 import json
 import logging
 from typing import Any, Callable
@@ -46,6 +52,10 @@ CODES = {
     "rejected_by_database": "the database refused the write",
     "invalid_plan": "the plan is not valid for the supported template",
     "tag_not_available": "a tag value of the plan is not an approved value of the fixed lists",
+    "extraction_unfinished": "a chosen source is still waiting for its records",
+    "checks_done": "Checks have run: no record is stored after them",
+    "checks_not_done": "no completed Checks result for this run",
+    "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
 
@@ -135,6 +145,46 @@ def flag_index(conn: Connection, run_id: int) -> list[tuple[int, str, str, tuple
     return [(i, k, c, tuple(ids)) for i, k, c, ids in rows]
 
 
+# --- Checks bound to the records it covered (step 6 review, finding 1) -----------------------
+
+def record_identity(version_fingerprint: str, origin: str, item_index: int) -> str:
+    """A record's stable identity: never its database id."""
+    return f"{version_fingerprint}|{origin}|{item_index}"
+
+
+def binding(identities, flags) -> dict:
+    """What a completed Checks result covered: the exact record collection (by stable identity)
+    and the flags it raised (kind, category and the identities of their records)."""
+    ids = sorted(identities)
+    digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
+    flag_lines = sorted(f"{k}|{c}|{','.join(sorted(r))}" for k, c, r in flags)
+    return {"records": len(ids), "identities": digest,
+            "flags": hashlib.sha256("\n".join(flag_lines).encode("utf-8")).hexdigest()}
+
+
+def checks_binding(conn: Connection, run_id: int) -> dict | None:
+    """The binding of the run's completed Checks result, or None."""
+    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'checks' AND status = 'done' "
+                            "ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+    return out.get("binding") if isinstance(out, dict) else None
+
+
+def require_checks_cover(conn: Connection, run_id: int, function: str, identity_of: dict, flags) -> None:
+    """Refuses unless the completed Checks result covers exactly these records and flags."""
+    stored = checks_binding(conn, run_id)
+    if stored is None:
+        raise Refused(function, "checks_not_done")
+    flag_ids = [(kind, category, [identity_of[r] for r in records if r in identity_of])
+                for kind, category, records in flags]
+    if binding(identity_of.values(), flag_ids) != stored:
+        raise Refused(function, "checks_not_current")
+
+
+def pending_sources(conn: Connection, run_id: int) -> int:
+    return conn.execute(text("SELECT count(*) FROM run_source WHERE run_id = :r AND search_status = 'pending' "
+                             "AND source_version_id IS NOT NULL"), dict(r=run_id)).scalar_one()
+
+
 def code_stage(conn: Connection, run_id: int, stage: str, input_: dict, output: dict) -> int:
     """A finished stage result of a code step (role NULL): written running, then done."""
     sid = conn.execute(text(
diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 7bf060a..4735c47 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -207,6 +207,67 @@ def test_a_change_between_a_steps_read_and_its_write_is_refused(engine, monkeypa
     assert refusals(engine, rid)[-1][1:] == (function, "changed_since_read")
 
 
+# --- Checks bound to the records it covered (step 6 review, finding 1) ---------------------------
+
+def _conflict_ids(engine, rid):
+    """The MPEA and extract records of extract row 7 (MPEA row 1278): a real conflict (YS x 1.3)."""
+    rows = dict(q(engine, "SELECT source_item_key, id FROM record WHERE extraction_run_id = :r AND source_item_key "
+                          "IN ('MPEA_dataset.csv:row:1278', 'extract.csv:row:6')", r=rid))
+    return rows["MPEA_dataset.csv:row:1278"], rows["extract.csv:row:6"]
+
+
+def test_skipping_checks_is_refused_at_inclusion_and_the_freeze(engine):
+    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    extract.store_records(engine, rid)
+    for call, function in ((inclusion.decide_run, "decide"), (checkpoints.freeze_dataset, "freeze_dataset")):
+        with pytest.raises(Refused) as refused:
+            call(engine, rid)
+        assert refused.value.code == "checks_not_done"
+        assert refusals(engine, rid)[-1][1:] == (function, "checks_not_done")
+    assert q(engine, "SELECT count(*) FROM run_record WHERE run_id = :r", r=rid)[0][0] == 0
+
+
+def test_checks_wait_until_every_chosen_source_is_stored(engine):
+    """Store MPEA, then Checks while the extract is still pending: refused; after the extract is
+    stored, Checks covers both and the real conflict is flagged and kept out."""
+    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    extract.store_source(engine, rid, "mpea")
+    with pytest.raises(Refused) as refused:
+        checks.run_checks(engine, rid)
+    assert refused.value.code == "extraction_unfinished"
+    extract.store_source(engine, rid, "controlled_duplicates")
+    checks.run_checks(engine, rid)
+    with pytest.raises(Refused) as refused:  # nothing more is stored after Checks
+        extract.store_source(engine, rid, "controlled_duplicates")
+    sets = inclusion.decide_run(engine, rid)
+    mpea, copy = _conflict_ids(engine, rid)
+    assert (sets["primary"][mpea], sets["primary"][copy]) == ("conflict_unresolved", "conflict_unresolved")
+
+
+def test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze(engine):
+    """A conflicting copy added after Checks (by plain SQL: storage refuses it) is not covered by
+    the Checks result, so Inclusion and the freeze refuse."""
+    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    extract.store_records(engine, rid)
+    checks.run_checks(engine, rid)
+    mpea, _ = _conflict_ids(engine, rid)
+    with engine.begin() as conn:
+        conn.execute(text(
+            "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, alloy, "
+            "harmonized, reported, paper_reference, paper_doi, extraction) SELECT r.extraction_run_id, "
+            "(SELECT source_version_id FROM record WHERE source_item_key = 'extract.csv:row:6' AND extraction_run_id = :r), "
+            "'added-after-checks', 0, r.kind, r.alloy, jsonb_set(r.harmonized, '{yield_strength,value}', "
+            "to_jsonb((r.harmonized->'yield_strength'->>'value')::float * 1.5)), r.reported, r.paper_reference, "
+            "r.paper_doi, r.extraction FROM record r WHERE r.id = :m"), dict(r=rid, m=mpea))
+    with pytest.raises(Refused) as refused:
+        inclusion.decide_run(engine, rid)
+    assert refused.value.code == "checks_not_current"
+    with pytest.raises(Refused) as refused:
+        checkpoints.freeze_dataset(engine, rid)
+    assert refused.value.code in ("checks_not_current", "changed_since_read")
+    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0
+
+
 # --- records, flags and decisions between the checkpoints ------------------------------------
 
 def test_records_are_stored_only_after_the_lock_with_how_they_were_extracted(engine):
@@ -251,6 +312,9 @@ def test_constructed_data_never_enters_a_run_not_marked_as_a_test(engine):
         conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                           "reported, extraction) VALUES (:r, :v, 'extract.csv:row:0', 'measured', '{}', '{}', "
                           "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
+        # Checks wait until no chosen source is pending (review finding 1): the bypass marks it searched.
+        conn.execute(text("UPDATE run_source SET search_status = 'searched', decided_at = now() WHERE run_id = :r "
+                          "AND source_version_id = :v"), dict(r=rid, v=version))
     checks.run_checks(engine, rid)
     with pytest.raises(Refused) as refused:
         inclusion.decide_run(engine, rid)
@@ -287,8 +351,9 @@ def test_a_change_after_the_decisions_were_read_is_refused_at_the_freeze(engine)
                           "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
     with pytest.raises(Refused) as refused:
         checkpoints.freeze_dataset(engine, rid)
-    assert refused.value.code == "changed_since_read"
-    assert refusals(engine, rid)[-1] == ("checkpoint", "freeze_dataset", "changed_since_read")
+    # Since the review (finding 1) the freeze first finds that Checks did not cover the added record.
+    assert refused.value.code == "checks_not_current"
+    assert refusals(engine, rid)[-1] == ("checkpoint", "freeze_dataset", "checks_not_current")
     assert stage(engine, rid) == "curation"
````

### `ac846a4 Step 6 fix: wording that the code supports`

````diff
ac846a49b422d1940f3da39ce53f984e49def409

Step 6 fix: wording that the code supports

Review remarks: "pairwise comparisons feed whole-group classification",
not "only pairwise rules" (test renamed accordingly); "every setting comes
only from the plan" narrowed to plan settings, with the policies fixed in
code listed in eligibility.py and new register entry
fixed_policies_in_code; each "±" in the reference numbers labelled one
standard error, not a confidence interval; noted for a later step that an
unknown source definition should fail closed.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/CLAUDE.md b/CLAUDE.md
index 3e5a745..d933113 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -68,4 +68,4 @@ The access layer and its tests guard against **our own code** leaking data to a
 
 ## Reference numbers (fixed-plan test, PRD 14.1a)
 
-Under the owner's decisions of 2026-10-05 (tension only; Texas A&M room temperature and single-phase FCC assigned by decision); recomputed test-side in step 6 and approved by the owner on 2026-10-06 (register entry `reference_numbers`, which keeps the earlier values in its history). Pooled: 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6. First source alone (MPEA): 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6. Second source alone (Texas A&M): 21 records, 9 alloys, coefficient ≈ 1173, one group, no uncertainty, no verdict. The statistics module (step 7) must reproduce these independently; the step 6 values come from a test-side script, not from package code.
+Under the owner's decisions of 2026-10-05 (tension only; Texas A&M room temperature and single-phase FCC assigned by decision); recomputed test-side in step 6 and approved by the owner on 2026-10-06 (register entry `reference_numbers`, which keeps the earlier values in its history). Pooled: 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6. First source alone (MPEA): 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6. Each "±" is one standard error (cluster-robust, by group), not a confidence interval. Second source alone (Texas A&M): 21 records, 9 alloys, coefficient ≈ 1173, one group, no uncertainty, no verdict. The statistics module (step 7) must reproduce these independently; the step 6 values come from a test-side script, not from package code.
diff --git a/README.md b/README.md
index 0824dd1..a11e99c 100644
--- a/README.md
+++ b/README.md
@@ -153,7 +153,7 @@ inclusion.decide_run(engine, run_id)        # one rule per record; the primary a
 checkpoints.freeze_dataset(engine, run_id)  # counts and fingerprint; or "no dataset frozen"
 ```
 
-- **The plan** follows `PLAN_SCHEMA` exactly and holds every setting that affects eligibility or grouping. The default and reference plans take each value from the domain profile (`profile.py`); decision code reads settings only from the locked plan.
+- **The plan** follows `PLAN_SCHEMA` exactly and holds every plan setting that affects eligibility or grouping. The default and reference plans take each value from the domain profile (`profile.py`); decision code reads those settings only from the locked plan. Some policies are fixed in code for every plan (listed in `eligibility.py` and register entry `fixed_policies_in_code`), among them the rules no plan can change for the primary set (`primary_set_invariants`).
 - **Checks and Inclusion read through their own access objects** (`dispatch.bind_code`). Inclusion receives no outcome value.
 - **Every write** takes `hc_write_lock(p_run => …)` in `run_transaction`, re-checks by id what it read, and logs any refusal (`audit_log`, `detail.result` "rejected").
 - **Constructed test data** (the controlled extract) enter only a run marked `{"constructed_test_data": true}` in `experiment_flags` at dispatch.
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index a8ea61d..be47de1 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -1305,7 +1305,7 @@
     "tests": [
       "tests/test_eligibility.py::test_each_rule_on_its_own",
       "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
-      "tests/test_flags.py::test_flags_use_only_pairwise_and_per_record_rules",
+      "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification",
       "tests/test_flags.py::test_physically_impossible_values_are_flagged_per_record"
     ]
   },
@@ -4324,7 +4324,7 @@
     "key": "code_role_access",
     "name": "Inclusion and Checks read through access objects",
     "state": "in_force",
-    "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
+    "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
     "value": {
       "text": "Inclusion: plan, record conditions, flag kinds; Checks: plan, all values",
       "unit": null
@@ -4367,7 +4367,7 @@
       "tests/test_access_code_roles.py::test_only_code_roles_bind_without_an_agent_setting",
       "tests/test_access_code_roles.py::test_an_agent_setting_cannot_bind_as_a_code_role",
       "tests/test_access_code_roles.py::test_code_roles_do_not_bind_at_any_other_stage",
-      "tests/test_flags.py::test_flags_use_only_pairwise_and_per_record_rules"
+      "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification"
     ]
   },
   {
@@ -4458,7 +4458,8 @@
     },
     "history": [],
     "notes": [
-      "Backlog (owner, 2026-10-06; PRD 18 at the next PRD update): a database rule refusing a constructed source's records in a run not marked as a test. The guard stays in code in sprint 1."
+      "Backlog (owner, 2026-10-06; PRD 18 at the next PRD update): a database rule refusing a constructed source's records in a run not marked as a test. The guard stays in code in sprint 1.",
+      "Step 6 review (2026-10-06), for a later step: a source whose definition is unknown to the code should fail closed (be treated as constructed, or refused), not pass the guard."
     ],
     "tests": [
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
@@ -4581,9 +4582,9 @@
     "key": "reference_numbers",
     "name": "Reference numbers of the fixed-plan test",
     "state": "in_force",
-    "statement": "Under the reference plan (tension only; Texas A&M room temperature and single-phase FCC assigned by decision): pooled 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA alone 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6; Texas A&M alone 21 records, 9 alloys, one group, coefficient ≈ 1173 with no uncertainty and no verdict. The statistics module (step 7) must reproduce them independently.",
+    "statement": "Under the reference plan (tension only; Texas A&M room temperature and single-phase FCC assigned by decision): pooled 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA alone 76 records, 13 alloys, 19 papers, k = 424.1 ± 62.2, p ≈ 1.1e-6; Texas A&M alone 21 records, 9 alloys, one group, coefficient ≈ 1173 with no uncertainty and no verdict. Each ± is one standard error (cluster-robust, by group), not a confidence interval. The statistics module (step 7) must reproduce them independently.",
     "value": {
-      "text": "pooled 97 / 22 / 20 / 74, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA 76 / 13 / 19, k = 424.1 ± 62.2, p ≈ 1.1e-6; Texas A&M 21 / 9 / 1, k ≈ 1173",
+      "text": "pooled 97 / 22 / 20 / 74, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA 76 / 13 / 19, k = 424.1 ± 62.2, p ≈ 1.1e-6; Texas A&M 21 / 9 / 1, k ≈ 1173 (± one standard error)",
       "unit": "MPa·µm^½"
     },
     "category": "statistical",
@@ -4740,5 +4741,56 @@
       "tests/test_checkpoints.py::test_checks_wait_until_every_chosen_source_is_stored",
       "tests/test_checkpoints.py::test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze"
     ]
+  },
+  {
+    "key": "fixed_policies_in_code",
+    "name": "Policies fixed in code for every plan",
+    "state": "in_force",
+    "statement": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (the DOI's derived key; a source grouped by dataset cites itself); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
+    "value": {
+      "text": "eleven fixed policies",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "What a plan can and cannot set.",
+    "reason": "Step 6 review: the claim 'every setting comes only from the plan' was broader than the code; it is narrowed to plan settings, and the fixed policies are listed.",
+    "evidence": [
+      "docs/reviews/step06_review_chatgpt.md, 'Locked settings and sensitivity names'; accepted by the owner on 2026-10-06."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
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
+          "ref": "python:hypocurate.pipeline.flags:VALUE_STATUSES"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:FLAG_RULE_CHOICES"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:SENSITIVITY_CHANGES"
+        },
+        {
+          "ref": "python:hypocurate.access.allowlist:CODE_ALLOWED"
+        }
+      ],
+      "note": "The meaning of each sensitivity key must stay stable, or be versioned with the domain profile."
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_eligibility.py::test_decisions_ignore_the_domain_profile",
+      "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification"
+    ]
   }
 ]
diff --git a/hypocurate/pipeline/checks.py b/hypocurate/pipeline/checks.py
index 030c073..7d76b06 100644
--- a/hypocurate/pipeline/checks.py
+++ b/hypocurate/pipeline/checks.py
@@ -1,7 +1,8 @@
 """Checks (code; PRD 4, 5.3; build step 6): raise the flags of a run's records.
 
 Reads through its own access object (`dispatch.bind_code(…, "checks")`: the locked plan and
-every stored value) once every chosen source is stored, computes the flags with `pipeline.flags` (per-record and pairwise rules
+every stored value) once every chosen source is stored, computes the flags with `pipeline.flags` (per-record rules, and pairwise comparisons that feed a
+whole-group classification
 only), then writes them in one transaction under the run's lock that re-checks the records by
 id. Checks never decides eligibility. Flags are raised once per run, before the freeze; the
 numbers compared are stored for audit and never returned to the Critic.
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 4099330..3216972 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -1,8 +1,20 @@
 """Eligibility decisions under the locked plan (PRD 5.3; build step 6). Pure functions.
 
 Input: exactly what Inclusion's access object returns (`record_conditions`, `flags_kind`,
-the projected `plan`): no outcome value. **Every setting is read from the locked plan**
-(owner, 2026-10-05); this module imports nothing from the domain profile.
+the projected `plan`, each sensitivity set's own matching flags): no outcome value. This module
+imports nothing from the domain profile.
+
+**Settings and fixed policies** (step 6 review; owner, 2026-10-06). The plan's settings (scope,
+exclusion rules, eligibility rules within the fixed choices, `rules`, sufficiency) are read from
+the locked plan only, never from the domain profile. These are **fixed policies in code**, the
+same for every plan: which statuses carry a value; what counts as physically invalid (tensile
+strength below yield strength, grain size of zero or less); which test conditions are compared
+(test type and temperature); how a paper is identified (the DOI's derived key; a source grouped
+by dataset cites itself); the room-temperature band's name; the order of the rules; the
+ambiguity rule; the fixed rules for the primary set (register 'primary_set_invariants'); the
+structure of the survivor rule and its stable tie-breaker; the change each sensitivity key
+applies; and the code roles' field lists. Changing one is a code change with its register entry
+('fixed_policies_in_code').
 
 Each record gets one rule code, the first that applies (owner, 2026-10-05):
 
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 125a601..85f8dbe 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -2,9 +2,12 @@
 
 Input: exactly what Checks' access object returns (`records_full`, the projected `plan`).
 Checks sees every value (PRD 4) and only raises flags; Inclusion decides what a flag means
-under the locked plan. **Only per-record and pairwise rules are used**: no model, slope,
-residual or hypothesis of the plan, so agreement with the relationship under test can never
-decide which records are credible (PRD 5.3). Every setting is read from the locked plan.
+under the locked plan. **Per-record rules (invalid values) and pairwise comparisons that feed a
+whole-group classification** (duplicate, conflict, ambiguous group); no model, slope, residual or
+hypothesis of the plan, so agreement with the relationship under test can never decide which
+records are credible (PRD 5.3). The matching settings are read from the locked plan; the fixed
+policies listed in `eligibility.py` (which conditions are compared, how a paper is identified,
+the ambiguity rule) are code.
 
 Flags (owner, 2026-10-05):
 - `invalid_value` / "physically impossible": tensile strength below yield strength, or a
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index 85cea40..13dc593 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -6,7 +6,7 @@ no free text. `validate` refuses content that its own projection would change (a
 key, a value outside a vocabulary, a number where a code belongs), content missing a part,
 and content that the sprint-1 template does not support.
 
-Every setting that affects which records are eligible or how they are grouped is in the
+Every plan setting that affects which records are eligible or how they are grouped is in the
 plan (`rules`, `scope`, `exclusion_rules`, `eligibility_rules`, `sufficiency`), and the
 plan records the domain profile its defaults came from (`profile`). The default and the
 reference plans are built from the domain profile (`hypocurate.pipeline.profile`), its one
@@ -14,6 +14,8 @@ named place for each default. Plans are fixed inputs in step 6; the Planner (ste
 same template.
 
 The fingerprint is the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8).
+Some policies are fixed in code for every plan, not plan settings: see `eligibility.py`
+("Settings and fixed policies") and register entry 'fixed_policies_in_code'.
 """
 from __future__ import annotations
 
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index c12c77c..ca4d57a 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -8,7 +8,8 @@ position relative to the tested relationship.
 
 **Not claimed:** that outcomes play no part at all. Checks receives every value and compares
 them to classify duplicates, conflicts and physically invalid records, and Inclusion acts on
-those flag kinds (`tests/test_checks.py` shows that Checks uses only pairwise and per-record
+those flag kinds (`tests/test_flags.py` shows that Checks uses per-record rules and pairwise
+comparisons that feed a whole-group classification
 rules).
 """
 from __future__ import annotations
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index 433fd5c..844c22e 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -3,7 +3,7 @@
 Records here are in the `record_conditions` format Inclusion receives (no outcome value).
 Owner, 2026-10-05: one rule per record, the first that applies, in the order of the module
 docstring; duplicates are resolved before grain sizes are counted; a conflict and an ambiguous
-group enter the primary set with none of their records; every setting is read from the locked
+group enter the primary set with none of their records; every plan setting is read from the locked
 plan, never from the domain profile.
 """
 from __future__ import annotations
@@ -233,7 +233,7 @@ def test_identity_applies_only_among_records_that_passed_the_earlier_rules():
     assert decide(records, possible, key="scope_not_confirmed_included")[3] == "duplicate_counted_once"
 
 
-# --- every setting from the locked plan -----------------------------------------------------
+# --- every plan setting from the locked plan (fixed policies: eligibility.py) ------------------
 
 def _changed(path, value):
     plan = copy.deepcopy(PLAN)
diff --git a/tests/test_flags.py b/tests/test_flags.py
index c3c710c..a45b7a0 100644
--- a/tests/test_flags.py
+++ b/tests/test_flags.py
@@ -4,7 +4,8 @@ Records here are in the `records_full` format Checks receives through its access
 owner's rules (2026-10-05): duplicates and conflicts only between different sources; grain size
 within the tolerance to pair (a matching tolerance), yield strength within it for a duplicate
 and beyond it for a conflict; a group with several candidates from one source is ambiguous and
-nothing is paired on a guess. Checks uses only per-record and pairwise rules: no model, slope,
+nothing is paired on a guess. Checks uses per-record rules and pairwise comparisons that feed a
+whole-group classification: no model, slope,
 residual or plan hypothesis.
 """
 from __future__ import annotations
@@ -169,7 +170,7 @@ def _world(seed):
 
 
 @pytest.mark.parametrize("seed", range(5))
-def test_flags_use_only_pairwise_and_per_record_rules(seed):
+def test_flags_come_from_pairwise_comparisons_and_group_classification(seed):
     """Replacing every measurement's outcome by an arbitrary value (copies keep their ratio to it,
     tensile strength its ratio to yield strength) destroys any relation with grain size, but
     changes no pairwise or per-record relation: the flags are identical. So is removing the
diff --git a/tests/test_plan.py b/tests/test_plan.py
index a348cdb..7a520c6 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -1,4 +1,4 @@
-"""Step 6: the plan model (PRD 5.1). Plans follow PLAN_SCHEMA exactly; every setting that
+"""Step 6: the plan model (PRD 5.1). Plans follow PLAN_SCHEMA exactly; every plan setting that
 affects eligibility or grouping is a value of the plan; the default plan takes each value from
 the domain profile's named setting (owner, 2026-10-05)."""
 from __future__ import annotations
````

### `4babe82 Step 6 fix: answer-file rows 15-16 explanation for the tension-only plan`

````diff
4babe82e1ff3e9e59fd6b3c5e016701b41ad38f7

Step 6 fix: answer-file rows 15-16 explanation for the tension-only plan

Owner, 2026-10-06: the explanation text of rows 15-16 now describes the
reference plan's test-type rule, in this round's one fingerprint update.
The frozen extract is unchanged.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/tests/fixtures/controlled_duplicates/README.md b/tests/fixtures/controlled_duplicates/README.md
index 88d7b10..8ed91e0 100644
--- a/tests/fixtures/controlled_duplicates/README.md
+++ b/tests/fixtures/controlled_duplicates/README.md
@@ -49,7 +49,7 @@ No pair here lets a source other than MPEA survive. The step 6 tests add constru
 
 ## Permitted test types (decided)
 
-The owner decided on 2026-10-05 that the reference plan accepts tension tests only (register entry 'permitted_test_types'), which removes MPEA row 139 (a compression test) from its primary analysis. Since 2026-10-06 (owner's decision) the columns `prd_5_3_class` and `primary_analysis` of rows 15–16 describe this plan; the column `handling_under_tension_only_plan` agrees with them. The rows' `explanation` text still describes the step 1 plan without a test-type rule.
+The owner decided on 2026-10-05 that the reference plan accepts tension tests only (register entry 'permitted_test_types'), which removes MPEA row 139 (a compression test) from its primary analysis. Since 2026-10-06 (owner's decision) the columns `prd_5_3_class` and `primary_analysis` of rows 15–16 describe this plan; the column `handling_under_tension_only_plan` agrees with them. Their `explanation` text describes this plan too (owner, 2026-10-06, after the step 6 review).
 
 ## Rebuilding
 
diff --git a/tests/fixtures/controlled_duplicates/build.py b/tests/fixtures/controlled_duplicates/build.py
index 7a2a50d..6f950c7 100644
--- a/tests/fixtures/controlled_duplicates/build.py
+++ b/tests/fixtures/controlled_duplicates/build.py
@@ -152,7 +152,7 @@ CASES = {
         primary_analysis="not eligible: excluded by the test-type rule (tension only)",
         sensitivity_analysis="none",
         pair=None,
-        explanation="Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope.",
+        explanation="Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan accepts tension tests only, so this record is out of scope; with tension and compression together, both enter as distinct measurements.",
     ),
 }
 
diff --git a/tests/fixtures/controlled_duplicates/truth.csv b/tests/fixtures/controlled_duplicates/truth.csv
index 5b55fa5..47cccc7 100644
--- a/tests/fixtures/controlled_duplicates/truth.csv
+++ b/tests/fixtures/controlled_duplicates/truth.csv
@@ -13,5 +13,5 @@ extract_row,case,mpea_row,mpea_reference_id,mpea_doi,changed_columns,duplicate_s
 12,not_duplicate_other_temperature,1086,221,10.1016/j.msea.2018.12.077,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
 13,missing_test_condition,1036,211,10.1016/j.msea.2019.04.025,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 1036,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
 14,missing_test_condition,813,144,10.1016/j.ijplas.2018.10.005,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 813,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
-15,not_duplicate_other_test_type,1004,208,10.1016/j.actamat.2019.04.017,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope (test-type rule: tension only),yes,no,not eligible: excluded by the test-type rule (tension only),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
-16,not_duplicate_other_test_type,765,98,10.1016/j.actamat.2018.12.015,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope (test-type rule: tension only),yes,no,not eligible: excluded by the test-type rule (tension only),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
+15,not_duplicate_other_test_type,1004,208,10.1016/j.actamat.2019.04.017,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope (test-type rule: tension only),yes,no,not eligible: excluded by the test-type rule (tension only),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan accepts tension tests only, so this record is out of scope; with tension and compression together, both enter as distinct measurements."
+16,not_duplicate_other_test_type,765,98,10.1016/j.actamat.2018.12.015,PROPERTY: Type of test,not_duplicate,Incompatible measurements: outside the plan's scope (test-type rule: tension only),yes,no,not eligible: excluded by the test-type rule (tension only),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan accepts tension tests only, so this record is out of scope; with tension and compression together, both enter as distinct measurements."
diff --git a/tests/test_controlled_duplicates.py b/tests/test_controlled_duplicates.py
index d66f88b..b11a895 100644
--- a/tests/test_controlled_duplicates.py
+++ b/tests/test_controlled_duplicates.py
@@ -14,8 +14,9 @@ FIXTURES = REPO_ROOT / "tests/fixtures/controlled_duplicates"
 TRUTH = FIXTURES / "truth.csv"
 # Pinned here, outside data/, so the answer file cannot change without changing a test.
 # Step 6 (owner, 2026-10-05): the restored survivor wording and decision C (rows 7-8 are a conflict).
-# Owner, 2026-10-06: rows 15-16 describe the reference plan with its test-type rule (tension only).
-TRUTH_SHA256 = "8ff5383783726824faa03a724d3333e519ca2afa9b2ac33146f3c793e2b9a0f9"
+# Owner, 2026-10-06: rows 15-16 describe the reference plan with its test-type rule (tension only),
+# their explanation included (after the step 6 review).
+TRUTH_SHA256 = "e6e859cd127b26cad233fac11f68c09eeb29dc2e4457ea68cba530ef2355025b"
 # The frozen source files: fingerprint-pinned, and not written by us, so they
 # cannot hold our answers. Everything else under data/ is scanned.
 FROZEN_SOURCE_FILES = {
@@ -261,6 +262,8 @@ def test_other_test_type_rows_are_compression_copies_of_tension_records():
         # The reference plan accepts tension only (owner, 2026-10-05): the compression copy is out of scope.
         assert t["prd_5_3_class"] == "Incompatible measurements: outside the plan's scope (test-type rule: tension only)"
         assert t["primary_analysis"] == "not eligible: excluded by the test-type rule (tension only)"
+        assert "accepts tension tests only, so this record is out of scope" in t["explanation"]
+        assert "sets no test-type rule" not in t["explanation"]
         # Under a tension-only plan the compression record is out of scope.
         assert t["handling_under_tension_only_plan"] == (
             "excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements')")
````

### `af536cc Step 6 fix: test that storage refuses after Checks`

````diff
af536cc0ad4d851fabeec27fccf686893d8c2cea

Step 6 fix: test that storage refuses after Checks

Found by the mutation checks: removing the storage refusal after Checks
passed the earlier tests, which met the "already stored" refusal first.
The new test lets Checks run with a source pending (by patching that check
in the test) and shows the store is refused and logged.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index be47de1..38dd9b5 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4737,9 +4737,10 @@
       "A source refused by the constructed-data guard stays pending, so Checks cannot run until it is marked failed: the run's orchestration (step 9) must do that."
     ],
     "tests": [
-      "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze",
+      "tests/test_checkpoints.py::test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze",
       "tests/test_checkpoints.py::test_checks_wait_until_every_chosen_source_is_stored",
-      "tests/test_checkpoints.py::test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze"
+      "tests/test_checkpoints.py::test_no_record_is_stored_after_checks",
+      "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze"
     ]
   },
   {
diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 4735c47..426816a 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -244,6 +244,20 @@ def test_checks_wait_until_every_chosen_source_is_stored(engine):
     assert (sets["primary"][mpea], sets["primary"][copy]) == ("conflict_unresolved", "conflict_unresolved")
 
 
+def test_no_record_is_stored_after_checks(engine, monkeypatch):
+    """A second guard: storage refuses once Checks have run. Through the normal order this cannot
+    arise (Checks refuse while a source is pending, and a decided source is final), so the test
+    lets Checks run with the extract pending, then stores it."""
+    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    extract.store_source(engine, rid, "mpea")
+    monkeypatch.setattr(checks, "pending_sources", lambda conn, run_id: 0)
+    checks.run_checks(engine, rid)
+    with pytest.raises(Refused) as refused:
+        extract.store_source(engine, rid, "controlled_duplicates")
+    assert refused.value.code == "checks_done"
+    assert refusals(engine, rid)[-1][1:] == ("store_records", "checks_done")
+
+
 def test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze(engine):
     """A conflicting copy added after Checks (by plain SQL: storage refuses it) is not covered by
     the Checks result, so Inclusion and the freeze refuse."""
````

### `3f2872e Step 6 fix: test that no record is stored after Checks`

````diff
3f2872eeff44f4afd6c83d475107f256d1bc4265

Step 6 fix: test that no record is stored after Checks

Found by the mutation checks: removing the storage refusal after Checks
passed every test, because Checks already wait for every source. The new
test creates a Checks result while a source is still pending and expects
the refusal.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 426816a..70ee894 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -258,6 +258,20 @@ def test_no_record_is_stored_after_checks(engine, monkeypatch):
     assert refusals(engine, rid)[-1][1:] == ("store_records", "checks_done")
 
 
+def test_no_record_is_stored_after_checks(engine):
+    """Storage refuses once a Checks result exists, even for a source still pending (a state the
+    pipeline does not reach, since Checks wait for every source; created here directly)."""
+    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"), marked=True)
+    extract.store_source(engine, rid, "mpea")
+    with engine.begin() as conn:
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
+        writes.code_stage(conn, rid, "checks", {}, {"binding": {}})
+    with pytest.raises(Refused) as refused:
+        extract.store_source(engine, rid, "controlled_duplicates")
+    assert refused.value.code == "checks_done"
+    assert refusals(engine, rid)[-1][1:] == ("store_records", "checks_done")
+
+
 def test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze(engine):
     """A conflicting copy added after Checks (by plain SQL: storage refuses it) is not covered by
     the Checks result, so Inclusion and the freeze refuse."""
````

## 4. Reference numbers recomputed after the fixes

Same scripts as in the first packet (section 13 there), run on the fixed code. Before the fixes (normalized to the same label format) and after: **identical for every set** (`diff` empty). The freeze fingerprint's value changed (stable identities; finding 5); it is not a reference number.

````
fingerprint 93c44b227285b1c33157364d6f780e614dccfb7e6638dcf63b62803624320934
Each ± is one standard error (cluster-robust, by group), not a confidence interval.
| Set | Records | Alloys | Groups | Resid. df | Result |
|---|---|---|---|---|---|
| MPEA alone (primary) | 76 | 13 | 19 | 62 | k = 424.1 (SE 62.2), p = 1.1e-06 |
| Texas A&M alone (primary) | 21 | 9 | 1 | 11 | k = 1173.3 (no uncertainty, no p-value) |
| Pooled (primary) | 97 | 22 | 20 | 74 | k = 424.9 (SE 64.4), p = 1.3e-06 |
| conflicts_survivor_value | 97 | 22 | 20 | 74 | k = 424.9 (SE 64.4), p = 1.3e-06 |
| no_exclusions | 97 | 22 | 20 | 74 | k = 424.9 (SE 64.4), p = 1.3e-06 |
| possible_duplicates_separate | 97 | 22 | 20 | 74 | k = 424.9 (SE 64.4), p = 1.3e-06 |
| same_alloy_1_at_pct | 97 | 22 | 20 | 74 | k = 424.9 (SE 64.4), p = 1.3e-06 |
| scope_not_confirmed_included | 103 | 23 | 22 | 79 | k = 432.4 (SE 64.9), p = 6.7e-07 |
| six_batches_as_groups | 97 | 22 | 22 | 74 | k = 424.9 (SE 64.2), p = 7.5e-07 |
| source_only_assignments | 76 | 13 | 19 | 62 | k = 424.1 (SE 62.2), p = 1.1e-06 |
| tension_and_compression | 98 | 22 | 21 | 75 | k = 428.0 (SE 63.5), p = 7.4e-07 |
| tension_and_compression, MPEA alone | 77 | 13 | 20 | 63 | k = 427.2 (SE 61.4), p = 6.2e-07 |
````

## 5. Mutation checks

`mutate.py` (in the first packet, section 14) extended with this round's eleven mutations. Output of the last complete run; "storage allowed after Checks" was repeated by hand after its new test (see the summary).

````
constructed-data guard off: 1 failed, 24 passed in 44.78s  (imports the copy: True)
bind_code accepts any role: 1 failed, 11 passed in 7.23s  (imports the copy: True)
Inclusion receives all values: 2 failed, 10 passed in 7.08s  (imports the copy: True)
record_conditions carries the outcome value: 3 failed, 9 passed in 6.99s  (imports the copy: True)
checks does not re-check the records it read: 1 failed, 24 passed in 48.51s  (imports the copy: True)
inclusion does not re-check what it read: 1 failed, 24 passed in 45.70s  (imports the copy: True)
grain sizes counted before duplicates: 1 failed, 44 passed in 0.40s  (imports the copy: True)
scope rule after the duplicate rule (order 5/7): 7 failed, 88 passed in 5.07s  (imports the copy: True)
grain size compared exactly, not within the tolerance: 2 failed, 16 passed in 0.44s  (imports the copy: True)
tolerance fixed in code, not from the plan: 2 failed, 16 passed in 0.37s  (imports the copy: True)
minimum grain sizes from the profile, not the plan: 2 failed, 43 passed in 0.48s  (imports the copy: True)
rows within one source compared: 2 failed, 16 passed in 0.42s  (imports the copy: True)
an ambiguous group paired anyway: 3 failed, 15 passed in 0.37s  (imports the copy: True)
a conflict enters with both records: 5 failed, 90 passed in 4.92s  (imports the copy: True)
survivor rule 1 ignored: 1 failed, 44 passed in 0.39s  (imports the copy: True)
plan validation skips the fixed rules: 13 failed, 65 passed in 0.60s  (imports the copy: True)
Checks run while a source is pending: 1 failed, 24 passed in 44.72s  (imports the copy: True)
Inclusion and freeze ignore the Checks binding: 3 failed, 22 passed in 45.78s  (imports the copy: True)
storage allowed after Checks: 25 passed in 46.06s  (imports the copy: True)
sensitivity sets reuse the primary flags: 2 failed, 1 passed in 3.35s  (imports the copy: True)
an ambiguous group drops its conflict: 2 failed, 61 passed in 0.55s  (imports the copy: True)
survivor tie-break by database id: 1 failed, 44 passed in 0.41s  (imports the copy: True)
the lock accepts a setting that leaves out a source: 2 failed, 23 passed in 44.91s  (imports the copy: True)
the fingerprint keyed by database id: 1 failed, 24 passed in 45.60s  (imports the copy: True)
the extraction check without coalesce: 4 failed, 16 passed in 7.37s  (imports the copy: True)
write path without hc_write_lock: 1 failed, 24 passed in 63.29s (0:01:03)  (imports the copy: True)
refusals not logged: 14 failed, 11 passed in 76.04s (0:01:16)  (imports the copy: True)
freeze does not re-check the records it read: 1 failed, 24 passed in 101.76s (0:01:41)  (imports the copy: True)
freeze accepts decisions the rules do not produce: 1 failed, 25 passed in 89.19s (0:01:29)  (imports the copy: True)
a second lock not refused by our path: 1 failed, 25 passed in 73.25s (0:01:13)  (imports the copy: True)
0003 trigger without the extraction requirement: 2 failed, 18 passed in 13.00s  (imports the copy: True)
plan validation accepts free text: 5 failed, 28 passed in 0.88s  (imports the copy: True)
TAMU band not assigned (not reported): 6 failed, 16 passed in 16.46s  (imports the copy: True)
storage allowed after Checks, repeated by hand after test_no_record_is_stored_after_checks was added: 1 failed, 25 passed  (imports the copy: True)
````
