# Build step 6 — review packet for the second model

Date: 2026-10-05. Branch: `step-06-eligibility`. Code reviewed: commit `8ccfd36` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success, 815 passed, runtime image OK, https://github.com/kelawady/hypocurate/actions/runs/37352154249.

Generated from the files on disk by a script, so every file below is quoted exactly. The frozen data and the test-image lock are left out.

## How to use this packet

This is the first review of build step 6 (PRD Section 15): the plan model, the rules lock and the dataset freeze, the domain profile and tags, the exclusion and eligibility rules, and the code checks that raise flags. There is no agent and no model call; plans are fixed inputs. The step touches safeguards (the access layer, the plan lock, the inclusion and eligibility rules) and adds two migrations.

The summary (section 1) states the owner's decisions in planning, what was built, the eligibility rules, the eight sensitivity sets, the reference numbers recomputed test-side, every test changed, and the mutation checks. Your review is advice; the test suite is the gate. Please return a dated findings file with each finding, its severity and the evidence.

Please check in particular:
- **Inclusion's input** (`record_conditions`, `flags_kind`, the projected plan): can any outcome value reach it? Is the "guaranteed / not claimed" statement accurate?
- **The eligibility rules** (`eligibility.py`): do they and their order match PRD 5.3 as the owner decided it (decision C on conflicts, ambiguous groups, duplicates before grain sizes)? Is each sensitivity set exactly one change?
- **The duplicate grouping** (`flags.py`): candidate links, ambiguity, conflict precedence. Is anything merged on a guess, or a measurement counted twice?
- **The checkpoints and write paths** (`checkpoints.py`, `writes.py`, `extract.py`, `checks.py`, `inclusion.py`): can anything change after the lock or the freeze? Is every refusal logged? Is the locking protocol followed?
- **Settings from the locked plan only**: does any decision code read a default from elsewhere?
- **Migrations 0002 and 0003**: safe on the live database and with the previous release's code? The old and new trigger are shown side by side in section 6.
- **Overclaims**: is any statement in the summary, the code, the README or the register stronger than the code supports?

## Contents

1. Step summary
2. Reviewer checklist
3. CLAUDE.md
4. Core rules: PRD Sections 3, 3.1, 4 and 5.1 to 5.8
5. New package code (full text)
6. Migration 0003: `hc_record_insert` before and after
7. Other code changes (diffs against `main`)
8. The assumptions register (diff)
9. Tests: new files (full text)
10. Tests: changed files (diffs)
11. The step 1 answer file, builder and README (diffs)
12. README (diff)
13. Test-side recomputation of the reference numbers (scripts and output)
14. Mutation checks (script and output)

## Files added, modified or deleted since `main` (`209febc`, the step 5 live record)

```
M	README.md
M	hypocurate/access/allowlist.py
M	hypocurate/access/dispatch.py
M	hypocurate/access/fields.py
M	hypocurate/access/layer.py
M	hypocurate/access/vocabulary.py
M	hypocurate/assumptions.json
M	hypocurate/cli.py
A	hypocurate/db/migrations/versions/0002_tag_starting_lists.py
A	hypocurate/db/migrations/versions/0003_record_extraction.py
M	hypocurate/db/models.py
A	hypocurate/pipeline/checkpoints.py
A	hypocurate/pipeline/checks.py
A	hypocurate/pipeline/eligibility.py
A	hypocurate/pipeline/extract.py
A	hypocurate/pipeline/flags.py
A	hypocurate/pipeline/inclusion.py
A	hypocurate/pipeline/plan.py
A	hypocurate/pipeline/profile.py
A	hypocurate/pipeline/writes.py
M	hypocurate/sources/adapters/__init__.py
M	hypocurate/sources/adapters/mpea_layout.py
M	hypocurate/sources/adapters/tamu_fcc.py
M	hypocurate/sources/connection.py
M	hypocurate/sources/normalize.py
M	hypocurate/sources/record.py
M	hypocurate/sources/versions.py
M	scripts/check_runtime_image.py
M	tests/access_world.py
M	tests/fixtures/controlled_duplicates/README.md
M	tests/fixtures/controlled_duplicates/build.py
M	tests/fixtures/controlled_duplicates/truth.csv
M	tests/model_builder.py
A	tests/pipeline_fixtures.py
A	tests/pipeline_world.py
A	tests/test_access_code_roles.py
M	tests/test_access_dispatch.py
M	tests/test_access_layer.py
M	tests/test_adapter_mpea.py
M	tests/test_adapter_tamu.py
M	tests/test_assumptions.py
A	tests/test_checkpoints.py
M	tests/test_controlled_duplicates.py
A	tests/test_controlled_duplicates_handling.py
M	tests/test_data_model.py
A	tests/test_eligibility.py
A	tests/test_flags.py
M	tests/test_migrations.py
A	tests/test_migrations_step6.py
A	tests/test_plan.py
M	tests/test_reference_counts_from_adapters.py
A	tests/test_reference_sets.py
M	tests/test_source_connection.py
A	docs/reviews/step06_review_packet.md   (this packet; next commit)
A	docs/reviews/step06_summary.md   (next commit)
```

## 1. Step summary

### `docs/reviews/step06_summary.md`

````markdown
# Build step 6 — summary for review

Date: 2026-10-05. Branch: `step-06-eligibility`. **Status: first build, for the second model's review (PRD 13.2).** PRD Section 15, step 6: "Plan, checkpoints, inclusion and checks. The plan model, the rules lock and the dataset freeze, the domain profile and tags, exclusion and eligibility rules, and the code checks that raise flags."

The suite is the gate. This summary is for the second model, which uses `docs/reviews/checklist.md`; the review packet is `docs/reviews/step06_review_packet.md`.

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

**Settings come only from the locked plan** (owner, 2026-10-05). The decision code (`eligibility.py`, `flags.py`, `checks.py`, `inclusion.py`, `checkpoints.py`) imports nothing from the profile (import scan), and two behavioural tests show it:
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

| Set | Records | Alloys | Groups | Resid. df | k (MPa·µm^½) | Uncertainty | p |
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

The counts are regression tests now (`tests/test_reference_sets.py`). The coefficients, uncertainties and p-values become tests with the statistics module in step 7. **CLAUDE.md's "Reference numbers" are not changed** until the owner approves these numbers.

## Assumptions register

95 entries: 92 in force, 2 open, 1 direction approved. Every entry decided in step 6 is by the owner on 2026-10-05, not reviewed by an expert.

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
- `constructed_test_runs` (partly: the label and the exclusion are steps 7 and 10).

**Open owner decisions:**
- `below_minimum_display` (before step 7), with the owner's starting position;
- `curator_tabular_sources` (before step 8).

## Tests (815, all passing; 172 new; tests changed listed below)

| File | Tests | What |
|---|---|---|
| `tests/test_plan.py` | 24 | Default and reference plans valid and equal to their projection; the reference plan's values; each default from its named setting; 19 kinds of invalid plan refused; the fingerprint; three tags. |
| `tests/test_flags.py` | 18 | Invalid values; never within one source; tolerance boundaries (1.99% / 2.01%) on yield strength and grain size; known differences; unknown paper or condition; the same-alloy rule and the tolerance from the plan; 1:2, 2:2 and non-linked groups; conflict groups; a dataset cites itself; **flags unchanged when outcomes are replaced by arbitrary values that keep every pairwise and per-record relation, and with the plan's model and hypotheses removed**; import scan. |
| `tests/test_eligibility.py` | 36 | Each rule; the order; **duplicates before grain sizes (1.79/1.8 µm)**; Texas A&M by decision and the source-only set; survivors incl. **non-MPEA survivors**; conflicts and ambiguous groups; identity only among records that passed the earlier rules; **each setting read from the plan** (12 settings); grouping from the plan; decisions ignore the profile; no profile import; counts. |
| `tests/test_checkpoints.py` | 17 | The lock (plan, fingerprint, three tags in one transaction); second or changed lock, invalid plan, other version refused and logged; the lock waits for the run lock; **every write after `hc_write_lock`**; records stored after the lock with their extraction; **the guard at three points**; a marked run; changes between read and write refused (three steps); the freeze refuses decisions the rules do not produce; every write after the freeze refused and logged; counts and fingerprint; no dataset frozen; the same fingerprint on another database. |
| `tests/test_controlled_duplicates_handling.py` | 50 | Every extract row against the answer file: flag, primary handling, survivor, sensitivity handling; rows 15–16 under tension and compression. |
| `tests/test_reference_sets.py` | 6 | The primary set equals the reference selection without row 139; one decision per record (Texas A&M 21/72/1); no shared measurement; the freeze counts; **one change per sensitivity set**, on the reference run and on a marked run with duplicates and conflicts. |
| `tests/test_access_code_roles.py` | 12 | The code lists; binds only at curation (five other stages); only code roles; an agent setting cannot bind as one; **Inclusion receives no planted outcome value** (Checks as positive control); `record_conditions` contents and hashes. |
| `tests/test_migrations_step6.py` | 7 | Lists = register = profile; 0002 changes no schema; safe with existing values; up/down/up through each revision; failure rollback across both; 0003 keeps 0001's checks and adds one; a record states its extraction. |
| `tests/test_adapter_tamu.py`, `tests/test_assumptions.py` | +1, +1 | The decision citations quote the register; the step 6 decisions' wording. |

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

**Three mutations first survived**, and two tests were added:
- **"Write path without `hc_write_lock`":** the database triggers lock the run row too. The new statement-order test now fails without it.
- **"Freeze does not re-check its read":** its decision comparison caught the earlier scenario. The new tests change the run between each step's read and its write.
- **"`record_conditions` carries the outcome value":** the first mutation was neutralised by the reader's second filter. The stronger mutation (both removed) fails three tests.

### Suite results

```
$ pytest -q                                   (Codespace, Python 3.14.2, `docker compose up -d db`)
815 passed in 178.83s
$ docker compose run --rm test                 (the test image, rebuilt)
815 passed in 194.83s
```

GitHub Actions, commit `8ccfd36` (the last code commit): success; "Run the suite in the test image": 815 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37352154249

## Deviations from the approved plan

1. **A flag `category` in `eligibility_rules`** (a schema leaf), so that the plan, not code, says what an ambiguous group means.
2. **A content hash in `record_conditions`**, so that the freeze fingerprint covers record content without Inclusion receiving values.
3. **Ambiguity also when a group's records are not all linked** (section "Records, checks and inclusion").
4. **The freeze reads the decision tables by SQL** (ids and codes) to check them, not through an access object.
5. **Record storage reads sealed versions directly** (code, approved under (c)), not through an access object.
6. **The variation of each sensitivity key is fixed by the key**, not by plan numbers.
7. **Sprint 1 plans accept only the room-temperature band**; any other band is refused by `validate`.
8. **The answer file's rows 15–16:** the columns `prd_5_3_class` and `primary_analysis` still describe the step 1 plan without a test-type rule ("both enter under the reference plan"). Under today's reference plan the column `handling_under_tension_only_plan` applies, and the test uses it. Aligning those two cells needs the owner's approval (open item).
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

## Open items

1. **Owner:**
   - approve the recomputed reference numbers before CLAUDE.md changes;
   - the open decisions `below_minimum_display` (before step 7) and `curator_tabular_sources` (before step 8);
   - whether to align the answer file's rows 15–16 cells with the tension-only plan;
   - whether the constructed-data guard should also be a database rule (a migration).
2. **Step 7:**
   - the statistics on the frozen sets; the coefficients above become tests;
   - the fixed-minimum check that decides the outcome;
   - the predictor transformation from the plan;
   - the per-source alloys rule (an alloy that qualifies only pooled);
   - the label "test run: includes constructed data" on stored results;
   - the open item from step 1 on the pooled p-value (1.3e-6 now).
3. **Step 8:** the Curator and tabular sources; a Planner's plan must pass `validate` and is locked through `lock_rules`.
4. **Step 10:** the label and the exclusion of marked runs on every screen and list.
5. **At the merge:** migrations 0002 and 0003 run on Render's pre-deploy; check the live deploy with the owner (schema at 0003, 19 tag values).
6. **Carried, unchanged:** the step 5 open items for steps 7–9; live registration of sources (owner).

## Questions for the reviewer

1. Can any outcome value reach Inclusion (`record_conditions`, `flags_kind`, the projected plan)? Is the "guaranteed / not claimed" statement accurate?
2. Do the eligibility rules and their order match PRD 5.3 as the owner decided it, and is each sensitivity set exactly one change?
3. Is the duplicate grouping (candidate links, ambiguity when several candidates or not all linked, conflict precedence) sound, and is anything merged on a guess?
4. Can anything change after the rules lock or the freeze through these write paths, and is every refusal logged?
5. Are migrations 0002 and 0003 safe on the live database and with the previous release's code?
6. Is any claim in this summary, the code, the README or the register stronger than the code supports?
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

### `CLAUDE.md`

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

````markdown
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

## 5.1 What the plan contains

- The claim in words, and the version of the hypothesis it belongs to.

- Variables with units, including the outcome variable and the predictor.

- Scope: alloy class, temperature range, test type, and any other condition.

- The parameters of the supported statistical model (Section 5.7): hypotheses and significance threshold.

- The data-sufficiency option and its values (Section 5.8).

- The list of fields the Curator must extract.

- Exclusion rules (Section 5.2) and analysis eligibility rules (Section 5.3).

- The statement that the pooled test gives the verdict and that per-source results are descriptive.

- The sensitivity analyses that will be run.

The rules lock stores the plan with a fingerprint and a timestamp. After it, no agent and no person can change the plan for that run. A change means a new hypothesis version and a new run. Section 5.6 describes the two checkpoints.

## 5.2 Exclusion rules

Removing records after seeing the outcome is a way to search for a result, so it is closed off. Exclusion rules are chosen by the Planner from an allowed menu before the rules lock and applied by code. The menu in sprint 1: a grain-size range, a temperature range, phase, and test type. Example for the sprint claim: exclude records with grain size below 0.1 µm.

Any removal proposed after the lock, by an agent or a person, goes into a separate, labelled sensitivity analysis. It is reported beside the verdict and never changes it.

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

## 5.5 Domain and tags

Every query carries a domain and three tags. They organize the testability-gap map, select the rules that apply, and let queries be filtered and reported by topic.

| **Field** | **Meaning and values** | **Who sets it** | **When** |
|---|---|---|---|
| Domain | The scientific topic. A fixed list, not free text: "Grain-size strengthening" (supported in sprint 1), "Fatigue" and "Other" (listed, not yet supported). | The submitter picks it; the reviewer confirms or changes it | Before dispatch |
| Property | The outcome variable of the plan, for example yield strength or hardness. | The Planner, from the plan | At the lock |
| Alloy class | For example FCC, BCC refractory, or conventional alloys. More than one value is allowed. | The Planner, from the plan | At the lock |
| Test condition | Temperature band and test type, for example room temperature, tension. | The Planner, from the plan | At the lock |

- **Domain profile.** Each domain has a profile in code: the fields to extract, the units, the physical checks, and the default exclusion and eligibility rules. Sprint 1 has one profile, for grain-size strengthening. Adding a domain later means adding a profile, not changing the pipeline.

- **Unsupported domains.** A query in a domain without a profile can be drafted and submitted, but dispatch is blocked with a clear message.

- **Mismatch.** If the Planner judges that the claim belongs to a different domain than the one chosen, the run stops before the lock with the status "failed: domain mismatch" and a note for the reviewer.

- **Tags are values from fixed lists** kept in the database, so that the same thing is always named the same way. The Planner chooses from the lists and may propose a new value, which a person must approve.

- **A narrower question** inherits the domain of its original and gets its own tags.

## 5.6 Two checkpoints: the rules lock and the dataset freeze

| **Checkpoint** | **When** | **What it fixes** |
|---|---|---|
| Rules lock | After the Planner, before curation | The plan: model parameters, scope, exclusion rules, eligibility rules, data-sufficiency option, sensitivity analyses. Stored with a fingerprint and a time. |
| Dataset freeze | After inclusion, checks and the Critic, before analysis | The analysis dataset: exactly which records enter the primary analysis and each sensitivity analysis. Stored with a fingerprint and a time. |

- Between the two checkpoints the set of records changes only by applying the locked rules. No agent and no person can add or remove a record by choice.

- After the dataset freeze nothing changes. Outcome values become visible to the statistics code and the Analyst only after it.

- A removal proposed after the rules lock, by an agent or a person, is recorded and appears only in a labelled sensitivity analysis.

- If no records are eligible, no dataset is frozen and no test is run; the run ends as insufficient.

## 5.7 The supported statistical model

Sprint 1 supports one model. The Planner fills in its parameters; it does not choose a test freely. The list of supported models is built so that more can be added later.

| **Element** | **Specification** |
|---|---|
| Formula | Yield strength = a baseline for each alloy + k × (grain size in µm)^-½. One baseline (intercept) per alloy; one shared coefficient k. |
| Fitting | Ordinary least squares. |
| Uncertainty | Standard error of k with records grouped by source paper (cluster-robust, with the small-sample correction). Each source states its grouping unit: the paper for literature data; for a single-laboratory dataset without per-record papers, the whole dataset is one group unless the adapter defines a unit such as a batch. |
| Hypotheses and reference distribution | Null: k ≤ 0. Alternative: k \> 0. One-sided test; threshold 0.05 unless the plan sets another. The statistic is judged against a t distribution with (number of groups − 1) degrees of freedom. |
| Validity check 1: can a coefficient be fitted? | At least one alloy measured at two distinct grain sizes. If not, nothing is fitted. |
| Validity check 2: is the inference valid? | Residual degrees of freedom (records − alloys − 1) of at least 1, and at least 2 independent groups; these are the hard floor below which no uncertainty can be computed. If check 1 passes and check 2 fails, the coefficient is reported alone: no uncertainty, no p-value, no verdict. |
| Which alloys can be used | Only alloys measured at two or more distinct grain sizes within the plan's scope. Others are kept in the store and marked not eligible. |
| Allowed exclusion rules | From the menu in Section 5.2 only. |
| Per-source results | The same model fitted on each source alone; descriptive. |
| Sensitivity analyses | The same model on the alternative record sets defined by the plan. |

- **The validity checks cannot be waived.** They are separate from data sufficiency (Section 5.8) and apply to the pooled test, to each per-source result and to each sensitivity analysis. One alloy at two grain sizes gives a slope but no way to estimate its uncertainty, and a source that is a single group has no computable grouped uncertainty.

- **Code decides; the Analyst explains.** Code determines whether the data are sufficient and what the statistical decision is. The Analyst never computes or changes a result.

- **Reference test.** The result k = 427 ± 61 is tested with a fixed plan and a fixed copy of the source, with numerical tolerances (for example ±1 on k and on its uncertainty). With 20 papers the p-value is about 6×10⁻⁷. The live Planner is tested separately; a statistics regression must not depend on a model producing the same plan again.

## 5.8 How much data is enough

This is a parameter of the query, chosen before dispatch and fixed at the rules lock. Changing it requires a new version of the query. It is applied after the two validity checks of Section 5.7, which no option can waive.

| **Option** | **What the user sets** | **How sufficiency is decided** |
|---|---|---|
| Fixed minimum (default in sprint 1) | Minimum records, alloys measured at two or more grain sizes, independent papers, and residual degrees of freedom. Starting values: 30, 5, 10 and 10. | Simple counts. All four must be met. |
| Power-based | Significance threshold, power wanted, smallest effect worth detecting, expected scatter, and an assumed similarity of records within a paper. | Code computes, from the grain sizes found, an estimated power under the stated assumptions. Not used as the gate in sprint 1 until the calculation has been specified and reviewed. |
| Use what is available | Nothing. | Any data that pass the validity checks are tested. The result is labelled "exploratory". |

- **Why fixed minimums are the default.** The power calculation needs an assumption about how alike the records within one paper are, as well as the grain-size spread and the expected scatter. Until that calculation is written down and reviewed, it should not decide whether a test runs.

- **Checked against the sprint data.** Pooled (98 records, 22 alloys, 21 groups, 75 residual degrees of freedom): met. MPEA alone (77, 13, 20): met. Texas A&M alone (21 records, 9 alloys, 1 group): not met, and it also fails validity check 2.

- **Estimated power.** The power figure may be computed and shown for information under any option. It is always labelled "estimated power under the stated assumptions", never "power achieved".

- The power check uses only the predictor (grain sizes), never the outcome, so it can be done at the dataset freeze, before any outcome is visible. The same calculation can tell the gap report roughly how much more data are needed.

- **Exploratory** waives the sufficiency threshold only. It does not waive either validity check.

- The starting values are to be confirmed with Prof. El-Awady.
````

## 5. New package code (full text)

### `hypocurate/pipeline/profile.py`

```python
"""The domain profile for grain-size strengthening (PRD 5.5; build step 6).

One named place for each default of the domain (CLAUDE.md, "How we work" item 12): the
fields to extract, the units, the scope, the exclusion and eligibility rules, the
data-sufficiency minimums, the sensitivity analyses and the tag lists. The register
(`hypocurate/assumptions.json`) names these settings.

**The defaults are copied into each plan at the rules lock** (owner, 2026-10-05): every
setting that affects which records are eligible or how they are grouped is a value of the
locked plan (`PLAN_SCHEMA`), and the code that decides eligibility and grouping reads it from
the plan only, never from here. A plan records the profile name and version its defaults came
from. Raise `PROFILE_VERSION` whenever a default here changes.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from hypocurate.sources.normalize import SAME_ALLOY_DECIMALS

PROFILE_NAME = "grain_size_strengthening"
PROFILE_VERSION = 1

# --- Variables and the supported model (PRD 5.7) ---------------------------------------
OUTCOME = ("yield_strength", "MPa")
PREDICTOR = ("grain_size", "µm")
TRANSFORMATION = "inverse_square_root"
MODEL = "hall_petch_alloy_intercepts"
ALPHA = 0.05  # one-sided test of k > 0 (register 'significance_threshold'; p < alpha)
FIELDS_TO_EXTRACT = ("composition", "grain_size", "yield_strength", "ultimate_tensile_strength", "test_type",
                     "test_temperature", "test_temperature_band", "phase_class", "microstructure")

# --- Scope -------------------------------------------------------------------------------
ALLOY_CLASSES = ("multi-principal-element (high-entropy) alloy",)
PERMITTED_TEST_TYPES = ("tension",)  # register 'permitted_test_types' (owner, 2026-10-05)
TEMPERATURE_BANDS = ("room temperature",)
ROOM_TEMPERATURE_C = (20.0, 25.0)  # register 'room_temperature_scope': reported 20 to 25 °C
PHASE_CLASSES = ("FCC",)
# Single phase (register 'fcc_microstructure_scope'): the microstructure is exactly the phase
# class ("FCC"), not the phase column.
SINGLE_PHASE = "required"

# --- Exclusion rule from the menu (PRD 5.2) ----------------------------------------------
GRAIN_SIZE_FLOOR_UM = 0.1  # register 'grain_size_floor': exclude below 0.1 µm

# --- Eligibility and duplicates (PRD 5.3) ------------------------------------------------
MIN_GRAIN_SIZES_PER_ALLOY = 2  # register 'alloy_eligibility'
SAME_ALLOY_DECIMALS_DEFAULT = SAME_ALLOY_DECIMALS  # register 'same_alloy_rule': 0.1 at.%
# Register 'values_disagree_tolerance': |a - b| / min(|a|, |b|). A matching tolerance for
# grain size, a duplicate-or-conflict threshold for yield strength.
DUPLICATE_TOLERANCE = 0.02
# Register 'duplicate_survivor_rule', rule 2: the fixed source order.
SURVIVOR_SOURCE_ORDER = ("mpea", "tamu_fcc", "controlled_duplicates")
# Register 'assigned_value_statuses': the statuses whose values the default plan accepts.
ACCEPTED_VALUE_STATUSES = ("converted", "assigned_from_source", "assigned_by_decision")
# The grouping unit of each source for the grouped standard errors (register 'tamu_grouping_unit',
# 'paper_grouping_by_doi').
GROUPING = MappingProxyType({"mpea": "paper", "tamu_fcc": "dataset", "controlled_duplicates": "paper"})

# --- Data sufficiency (PRD 5.8; register 'fixed_minimums', 'sufficiency_options') ---------
SUFFICIENCY_OPTION = "fixed_minimum"
FIXED_MINIMUMS = MappingProxyType({"min_records": 30, "min_alloys": 5, "min_groups": 10, "min_resid_df": 10})

# --- Sensitivity analyses (owner, 2026-10-05; register 'sensitivity_one_change') ---------
# Each differs from the primary set in exactly one named respect; descriptive only, never
# changes the verdict, no adjustment for there being eight.
SENSITIVITY_ANALYSES = ("no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                        "source_only_assignments", "scope_not_confirmed_included",
                        "possible_duplicates_separate", "conflicts_survivor_value")

# --- Tags (PRD 5.5; register 'tag_starting_lists'; seeded by migration 0002) -------------
TAG_STARTING_LISTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "property": ("yield strength", "ultimate tensile strength", "hardness", "elongation", "fatigue life"),
    "alloy_class": ("multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy", "titanium alloy",
                    "nickel alloy", "copper alloy", "magnesium alloy", "other"),
    "test_condition": ("room-temperature tension", "room-temperature compression", "elevated temperature",
                       "cryogenic", "hardness test", "fatigue"),
})
# How a plan maps to its three tags (one per kind).
PROPERTY_TAGS = MappingProxyType({"yield_strength": "yield strength",
                                  "ultimate_tensile_strength": "ultimate tensile strength", "hardness": "hardness"})
TEST_CONDITION_TAGS = MappingProxyType({("room temperature", "tension"): "room-temperature tension",
                                        ("room temperature", "compression"): "room-temperature compression"})
```

### `hypocurate/pipeline/plan.py`

```python
"""The plan model (PRD 5.1; build step 6).

A plan is plain JSON content that follows `PLAN_SCHEMA` exactly (owner, 2026-10-05): named
keys at every level, vocabulary values, numbers, integers, common field names and units, and
no free text. `validate` refuses content that its own projection would change (an unknown
key, a value outside a vocabulary, a number where a code belongs), content missing a part,
and content that the sprint-1 template does not support.

Every setting that affects which records are eligible or how they are grouped is in the
plan (`rules`, `scope`, `exclusion_rules`, `eligibility_rules`, `sufficiency`), and the
plan records the domain profile its defaults came from (`profile`). The default and the
reference plans are built from the domain profile (`hypocurate.pipeline.profile`), its one
named place for each default. Plans are fixed inputs in step 6; the Planner (step 8) fills the
same template.

The fingerprint is the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Mapping

from hypocurate.access.allowlist import PLAN_SCHEMA
from hypocurate.access.fields import project
from hypocurate.access.vocabulary import SENSITIVITY_KEYS
from hypocurate.pipeline import profile as p

PARTS = ("hypothesis_version", "variables", "scope", "model", "sufficiency", "fields_to_extract", "exclusion_rules",
         "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules")
RULES = ("same_alloy_decimals", "duplicate_tolerance", "survivor_source_order", "min_grain_sizes",
         "room_temperature_min", "room_temperature_max", "single_phase", "accepted_value_statuses", "grouping")
# What each eligibility-rule code does when the plan names it for a flag (PRD 5.3).
FLAG_RULE_CODES = frozenset({"invalid_value", "duplicate_counted_once", "identity_unresolved", "conflict_unresolved",
                             "in_scope"})
MENU_RULES = frozenset({"grain_size_range", "temperature_range", "phase", "test_type"})


class PlanError(ValueError):
    """The content is not a valid plan for the supported template."""


def default_plan(hypothesis_version_id: int) -> dict:
    """The default plan of the grain-size strengthening profile, every value from its named setting."""
    return {
        "hypothesis_version": hypothesis_version_id,
        "variables": {"outcome": {"field": p.OUTCOME[0], "unit": p.OUTCOME[1]},
                      "predictor": {"field": p.PREDICTOR[0], "unit": p.PREDICTOR[1],
                                    "transformation": p.TRANSFORMATION}},
        "scope": {"alloy_class": list(p.ALLOY_CLASSES), "temperature_band": list(p.TEMPERATURE_BANDS),
                  "test_type": list(p.PERMITTED_TEST_TYPES), "phase_class": list(p.PHASE_CLASSES)},
        "model": {"name": p.MODEL, "null": "k <= 0", "alternative": "k > 0", "alpha": float(p.ALPHA)},
        "sufficiency": {"option": p.SUFFICIENCY_OPTION, **dict(p.FIXED_MINIMUMS)},
        "fields_to_extract": list(p.FIELDS_TO_EXTRACT),
        "exclusion_rules": [{"rule": "grain_size_range", "min": float(p.GRAIN_SIZE_FLOOR_UM)}],
        "eligibility_rules": [
            {"flag_kind": "invalid_value", "rule": "invalid_value"},
            {"flag_kind": "exact_duplicate", "rule": "duplicate_counted_once"},
            {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "identity_unresolved"},
            {"flag_kind": "possible_duplicate", "rule": "duplicate_counted_once"},
            {"flag_kind": "values_disagree", "rule": "conflict_unresolved"},
        ],
        "verdict_statement": "pooled_test_gives_verdict",
        "sensitivity_analyses": list(p.SENSITIVITY_ANALYSES),
        "profile": {"name": p.PROFILE_NAME, "version": p.PROFILE_VERSION},
        "rules": {"same_alloy_decimals": p.SAME_ALLOY_DECIMALS_DEFAULT,
                  "duplicate_tolerance": float(p.DUPLICATE_TOLERANCE),
                  "survivor_source_order": list(p.SURVIVOR_SOURCE_ORDER),
                  "min_grain_sizes": p.MIN_GRAIN_SIZES_PER_ALLOY,
                  "room_temperature_min": float(p.ROOM_TEMPERATURE_C[0]),
                  "room_temperature_max": float(p.ROOM_TEMPERATURE_C[1]),
                  "single_phase": p.SINGLE_PHASE,
                  "accepted_value_statuses": list(p.ACCEPTED_VALUE_STATUSES),
                  "grouping": [{"source": s, "unit": u} for s, u in p.GROUPING.items()]},
    }


def reference_plan(hypothesis_version_id: int) -> dict:
    """The fixed reference plan of acceptance criterion 14.1a (the Planner bypassed): the
    default plan under the owner's step 6 decisions."""
    return default_plan(hypothesis_version_id)


def canonical(content: Mapping[str, Any]) -> str:
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(content: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()


def validate(content: Any) -> dict:
    """The content as a plan, or PlanError. Returns a deep copy."""
    if not isinstance(content, Mapping):
        raise PlanError("a plan is a JSON object")
    content = copy.deepcopy(dict(content))
    try:
        canonical(content)
    except (TypeError, ValueError) as error:
        raise PlanError(f"the plan is not plain JSON: {error}") from None
    missing = [k for k in PARTS if k not in content]
    if missing:
        raise PlanError(f"the plan lacks {', '.join(missing)}")
    if project(content, PLAN_SCHEMA) != content:
        raise PlanError("the plan has a key, value or type outside PLAN_SCHEMA (its projection would change it)")
    _check_template(content)
    return content


def _check_template(c: dict) -> None:
    v, s, m, r = c["variables"], c["scope"], c["model"], c["rules"]
    if set(v) != {"outcome", "predictor"} or set(v["outcome"]) != {"field", "unit"} or \
            set(v["predictor"]) != {"field", "unit", "transformation"}:
        raise PlanError("variables need an outcome (field, unit) and a predictor (field, unit, transformation)")
    if (v["predictor"]["field"], v["predictor"]["unit"]) != ("grain_size", "µm"):
        raise PlanError("the supported model's predictor is grain size in µm")
    if v["outcome"]["field"] == v["predictor"]["field"]:
        raise PlanError("the outcome and the predictor are different fields")
    if set(m) != {"name", "null", "alternative", "alpha"} or not 0 < m["alpha"] < 1:
        raise PlanError("the model needs its name, hypotheses and a threshold between 0 and 1")
    if set(s) != {"alloy_class", "temperature_band", "test_type", "phase_class"} or not all(s.values()):
        raise PlanError("the scope names alloy classes, temperature bands, test types and phase classes")
    if s["temperature_band"] != ["room temperature"]:
        raise PlanError("sprint 1 supports the room-temperature band only")
    if set(r) != set(RULES):
        raise PlanError(f"the plan's rules are exactly: {', '.join(RULES)}")
    if not (0 <= r["same_alloy_decimals"] <= 3 and r["min_grain_sizes"] >= 2 and 0 <= r["duplicate_tolerance"] < 1
            and math.isfinite(r["room_temperature_min"]) and r["room_temperature_min"] <= r["room_temperature_max"]):
        raise PlanError("a rule is out of range")
    order = r["survivor_source_order"]
    units = [g["source"] for g in r["grouping"]]
    if len(set(order)) != len(order) or len(set(units)) != len(units) or any(set(g) != {"source", "unit"}
                                                                           for g in r["grouping"]):
        raise PlanError("the survivor order and the grouping name each source once")
    if not r["accepted_value_statuses"] or "converted" not in r["accepted_value_statuses"]:
        raise PlanError("the accepted value statuses include 'converted'")
    suff = c["sufficiency"]
    if set(suff) != {"option", "min_records", "min_alloys", "min_groups", "min_resid_df"} or \
            min(suff[k] for k in suff if k != "option") < 1:
        raise PlanError("the sufficiency option needs its four minimums, each at least 1")
    for rule in c["exclusion_rules"]:
        if rule.get("rule") not in MENU_RULES:
            raise PlanError("an exclusion rule comes from the menu (PRD 5.2)")
        if rule["rule"] in ("grain_size_range", "temperature_range") and not ({"min", "max"} & set(rule)):
            raise PlanError("a range rule needs a minimum or a maximum")
        if rule["rule"] in ("phase", "test_type") and not rule.get("values"):
            raise PlanError("a phase or test-type rule needs its values")
    seen = set()
    for e in c["eligibility_rules"]:
        if "flag_kind" not in e or "rule" not in e or e["rule"] not in FLAG_RULE_CODES:
            raise PlanError("an eligibility rule names a flag kind and one of the flag rule codes")
        key = (e["flag_kind"], e.get("category"))
        if key in seen:
            raise PlanError("each flag kind (and category) has one eligibility rule")
        seen.add(key)
    keys = c["sensitivity_analyses"]
    if len(set(keys)) != len(keys) or not set(keys) <= SENSITIVITY_KEYS - {"removal_after_lock"}:
        raise PlanError("sensitivity analyses are named once each, from the vocabulary")


def tags_for(content: Mapping[str, Any]) -> dict[str, str]:
    """The run's three tags (PRD 5.5), one per kind, from the plan."""
    outcome = content["variables"]["outcome"]["field"]
    alloy_classes, types, bands = (content["scope"][k] for k in ("alloy_class", "test_type", "temperature_band"))
    if outcome not in p.PROPERTY_TAGS or len(alloy_classes) != 1 or len(types) != 1 or len(bands) != 1:
        raise PlanError("three tags per run: the plan needs one outcome, one alloy class, one test type and one band")
    condition = p.TEST_CONDITION_TAGS.get((bands[0], types[0]))
    if condition is None:
        raise PlanError("no test-condition tag for this band and test type")
    return {"property": p.PROPERTY_TAGS[outcome], "alloy_class": alloy_classes[0], "test_condition": condition}
```

### `hypocurate/pipeline/eligibility.py`

```python
"""Eligibility decisions under the locked plan (PRD 5.3; build step 6). Pure functions.

Input: exactly what Inclusion's access object returns (`record_conditions`, `flags_kind`,
the projected `plan`): no outcome value. **Every setting is read from the locked plan**
(owner, 2026-10-05); this module imports nothing from the domain profile.

Each record gets one rule code, the first that applies (owner, 2026-10-05):

1. `model_recalled`: the record is model-recalled.
2. `invalid_value`: a flag the plan maps to `invalid_value` (physically impossible).
3. `out_of_scope`: a known value outside the scope (test type; reported temperature outside
   the room-temperature range, or a band outside the scope; microstructure, or phase class).
4. `missing_value`: composition, predictor or outcome without an accepted value.
5. `scope_not_confirmed`: a scope value missing, or held with a status the plan does not accept.
6. `excluded_by_rule`: an exclusion rule from the menu (for example grain size below 0.1 µm).
7. Identity, among records that passed 1–6, per flag the plan maps:
   `identity_unresolved` (every record of an ambiguous group), `conflict_unresolved` (every
   record of a group whose values disagree), `duplicate_counted_once` (every record but the
   survivor of an exact or possible duplicate group).
8. `single_grain_size`: the alloy (same-alloy rule) has fewer than the plan's distinct grain
   sizes among records that passed 1–7, so duplicates are resolved before grain sizes are
   counted (owner, 2026-10-05).
9. `in_scope`: eligible.

**Sensitivity sets** (register 'sensitivity_one_change'): each differs from the primary set in
exactly one named respect; every other rule applies unchanged. `SENSITIVITY_CHANGES` lists
the change of each key. The variation each key applies is fixed by the key (its name in the
vocabulary), not by a number in the plan.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping

from hypocurate.sources.normalize import same_alloy_key

PRIMARY = "primary"
FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_counted_once")

# The one change of each sensitivity set (owner, 2026-10-05).
SENSITIVITY_CHANGES = {
    "no_exclusions": "the menu exclusion rules are dropped; the scope is kept",
    "tension_and_compression": "permitted test types: tension and compression",
    "six_batches_as_groups": "Texas A&M grouped by its six batches (the same records as primary)",
    "same_alloy_1_at_pct": "the same-alloy rule rounds to 1 at.%",
    "source_only_assignments": "accepted value statuses: converted and assigned from source only",
    "scope_not_confirmed_included": "records whose scope cannot be confirmed are treated as in scope",
    "possible_duplicates_separate": "records of unresolved or possible duplicate groups count as separate "
                                    "measurements",
    "conflicts_survivor_value": "conflict groups are counted once by the survivor rule",
}


@dataclass(frozen=True)
class Settings:
    """The plan's settings as one set applies them."""
    outcome: str
    predictor: str
    test_types: frozenset
    bands: frozenset
    phase_classes: frozenset
    single_phase: bool
    rt_min: float
    rt_max: float
    statuses: frozenset
    exclusions: tuple
    flag_rules: tuple  # ((kind, category or None, rule), ...), most specific first
    decimals: int
    min_grain_sizes: int
    survivor_order: tuple
    grouping: Mapping[str, str]
    scope_unconfirmed_ok: bool = False


def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
    """The settings of set `key` under the locked plan's content."""
    r, s, v = plan["rules"], plan["scope"], plan["variables"]
    flag_rules = tuple(sorted(((e["flag_kind"], e.get("category"), e["rule"]) for e in plan["eligibility_rules"]),
                              key=lambda t: t[1] is None))
    base = Settings(
        outcome=v["outcome"]["field"], predictor=v["predictor"]["field"], test_types=frozenset(s["test_type"]),
        bands=frozenset(s["temperature_band"]), phase_classes=frozenset(s["phase_class"]),
        single_phase=r["single_phase"] == "required", rt_min=r["room_temperature_min"],
        rt_max=r["room_temperature_max"], statuses=frozenset(r["accepted_value_statuses"]),
        exclusions=tuple(tuple(sorted(e.items(), key=lambda kv: kv[0])) for e in plan["exclusion_rules"]),
        flag_rules=flag_rules, decimals=r["same_alloy_decimals"], min_grain_sizes=r["min_grain_sizes"],
        survivor_order=tuple(r["survivor_source_order"]),
        grouping={g["source"]: g["unit"] for g in r["grouping"]})
    if key == PRIMARY:
        return base
    if key not in plan["sensitivity_analyses"]:
        raise KeyError(f"the locked plan names no analysis {key!r}")
    if key == "no_exclusions":
        return replace(base, exclusions=())
    if key == "tension_and_compression":
        return replace(base, test_types=frozenset({"tension", "compression"}))
    if key == "six_batches_as_groups":
        return replace(base, grouping={**base.grouping, "tamu_fcc": "batch"})
    if key == "same_alloy_1_at_pct":
        return replace(base, decimals=0)
    if key == "source_only_assignments":
        return replace(base, statuses=base.statuses - {"assigned_by_decision"})
    if key == "scope_not_confirmed_included":
        return replace(base, scope_unconfirmed_ok=True)
    if key == "possible_duplicates_separate":
        return replace(base, flag_rules=tuple((k, c, "in_scope" if k == "possible_duplicate" else rule)
                                              for k, c, rule in base.flag_rules))
    if key == "conflicts_survivor_value":
        return replace(base, flag_rules=tuple((k, c, "duplicate_counted_once" if rule == "conflict_unresolved"
                                               else rule) for k, c, rule in base.flag_rules))
    raise KeyError(f"no change is defined for the analysis {key!r}")


# --- One record --------------------------------------------------------------------------

def _known(rec: Mapping, field: str, st: Settings) -> bool:
    return rec["status"].get(field) in st.statuses


def scope(rec: Mapping, st: Settings) -> str:
    """'in', 'out' or 'unconfirmed' for one record's scope."""
    verdicts = []
    # Test type.
    if _known(rec, "test_type", st):
        verdicts.append(rec["categories"]["test_type"] in st.test_types)
    else:
        verdicts.append(None)
    # Temperature: a reported temperature decides; otherwise the band.
    t = rec["values"].get("test_temperature")
    if _known(rec, "test_temperature", st) and t is not None:
        verdicts.append("room temperature" in st.bands and st.rt_min <= t <= st.rt_max)
    elif _known(rec, "test_temperature_band", st):
        verdicts.append(rec["categories"]["test_temperature_band"] in st.bands)
    else:
        verdicts.append(None)
    # Single phase: the microstructure is exactly one of the scope's phase classes.
    field = "microstructure" if st.single_phase else "phase_class"
    if _known(rec, field, st):
        verdicts.append(rec["categories"][field] in st.phase_classes)
    else:
        verdicts.append(None)
    if any(v is False for v in verdicts):
        return "out"
    return "unconfirmed" if any(v is None for v in verdicts) else "in"


def _missing(rec: Mapping, st: Settings) -> bool:
    if rec["composition"] is None or not _known(rec, "composition", st):
        return True
    return not (_known(rec, st.predictor, st) and _known(rec, st.outcome, st)) or \
        rec["values"].get(st.predictor) is None


def _excluded(rec: Mapping, st: Settings) -> bool:
    for items in st.exclusions:
        e = dict(items)
        lo, hi = e.get("min", -math.inf), e.get("max", math.inf)
        if e["rule"] == "grain_size_range":
            g = rec["values"].get("grain_size")
            if g is not None and not lo <= g <= hi:
                return True
        elif e["rule"] == "temperature_range":
            t = rec["values"].get("test_temperature")
            if t is not None and _known(rec, "test_temperature", st) and not lo <= t <= hi:
                return True
        elif e["rule"] == "test_type":
            if _known(rec, "test_type", st) and rec["categories"]["test_type"] not in e["values"]:
                return True
        elif e["rule"] == "phase":
            if _known(rec, "phase_class", st) and rec["categories"]["phase_class"] not in e["values"]:
                return True
    return False


def alloy(rec: Mapping, decimals: int) -> str | None:
    return same_alloy_key(rec["composition"], decimals) if rec["composition"] else None


def flag_rule(flag: Mapping, st: Settings) -> str | None:
    for kind, category, rule in st.flag_rules:
        if kind == flag["kind"] and (category is None or category == flag["category"]):
            return rule
    return None


def survivor_key(rec: Mapping, st: Settings) -> tuple:
    """Register 'duplicate_survivor_rule': 1) the record that carries the original paper
    reference (DOI); 2) the first source in the plan's order; 3) the lowest row."""
    order = st.survivor_order.index(rec["source"]) if rec["source"] in st.survivor_order else len(st.survivor_order)
    return (0 if rec["has_doi"] else 1, order, rec["row"] if rec["row"] is not None else math.inf, rec["id"])


# --- A whole set ---------------------------------------------------------------------------

def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[Mapping],
           key: str = PRIMARY) -> dict[int, str]:
    """{record id: rule code} for every record, for set `key` (primary or a sensitivity set)."""
    st = settings(plan, key)
    records = {r["id"]: r for r in records}
    flags = list(flags)
    rules: dict[int, str] = {}
    for r in records.values():  # 1
        if r["kind"] == "model_recalled":
            rules[r["id"]] = "model_recalled"
    for f in flags:  # 2
        if flag_rule(f, st) == "invalid_value":
            for rid in f["records"]:
                rules.setdefault(rid, "invalid_value")
    for r in records.values():  # 3-6
        if r["id"] in rules:
            continue
        sc = scope(r, st)
        if sc == "out":
            rules[r["id"]] = "out_of_scope"
        elif _missing(r, st):
            rules[r["id"]] = "missing_value"
        elif sc == "unconfirmed" and not st.scope_unconfirmed_ok:
            rules[r["id"]] = "scope_not_confirmed"
        elif _excluded(r, st):
            rules[r["id"]] = "excluded_by_rule"
    for f in flags:  # 7
        rule = flag_rule(f, st)
        members = [rid for rid in f["records"] if rid in records and rid not in rules]
        if rule in ("identity_unresolved", "conflict_unresolved"):
            for rid in members:
                rules[rid] = rule
        elif rule == "duplicate_counted_once" and members:
            survivor = min(members, key=lambda rid: survivor_key(records[rid], st))
            for rid in members:
                if rid != survivor:
                    rules[rid] = "duplicate_counted_once"
    sizes: dict[str, set] = defaultdict(set)  # 8
    for r in records.values():
        if r["id"] not in rules:
            sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
    for r in records.values():
        if r["id"] not in rules:
            rules[r["id"]] = ("single_grain_size" if len(sizes[alloy(r, st.decimals)]) < st.min_grain_sizes
                              else "in_scope")
    return rules


def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping]) -> dict[str, dict[int, str]]:
    """The primary set and every sensitivity set the plan names."""
    return {key: decide(plan, records, flags, key) for key in (PRIMARY, *plan["sensitivity_analyses"])}


def members(rules: Mapping[int, str]) -> list[int]:
    return sorted(rid for rid, rule in rules.items() if rule == "in_scope")


# --- Counts known at the freeze (structure and predictor only, no outcome) ----------------

def group(rec: Mapping, st: Settings) -> str | None:
    """The record's independent group under the set's grouping (PRD 5.7)."""
    unit = st.grouping.get(rec["source"])
    if unit == "paper":
        return f"paper:{rec['paper']}" if rec["paper"] else None
    if unit == "dataset":
        return f"dataset:{rec['source']}"
    if unit == "batch":
        return f"batch:{rec['source']}:{rec['batch']}" if rec["batch"] else None
    return None


def counts(plan: Mapping[str, Any], records: Mapping[int, Mapping], ids: Iterable[int], key: str = PRIMARY) -> dict:
    """Counts of a record set for the fixed minimums and the two validity checks (PRD 5.7,
    5.8): records, alloys, alloys with at least the plan's distinct grain sizes, independent
    groups, residual degrees of freedom. Information at the freeze; step 7 decides."""
    st = settings(plan, key)
    chosen = [records[i] for i in ids]
    sizes: dict[str, set] = defaultdict(set)
    for r in chosen:
        sizes[alloy(r, st.decimals)].add(r["values"][st.predictor])
    groups = {group(r, st) for r in chosen}
    n, n_alloys = len(chosen), len(sizes)
    n_groups = len(groups - {None})
    resid = n - n_alloys - 1
    suff = plan["sufficiency"]
    out = {"n_records": n, "n_alloys": n_alloys,
           "n_alloys_two_grain_sizes": sum(len(v) >= st.min_grain_sizes for v in sizes.values()),
           "n_groups": n_groups, "n_records_without_group": sum(group(r, st) is None for r in chosen),
           "resid_df": resid}
    out["check1_inputs_met"] = out["n_alloys_two_grain_sizes"] >= 1
    out["check2_inputs_met"] = out["check1_inputs_met"] and resid >= 1 and n_groups >= 2
    out["minimums"] = {"records": n >= suff["min_records"],
                       "alloys": out["n_alloys_two_grain_sizes"] >= suff["min_alloys"],
                       "groups": n_groups >= suff["min_groups"], "resid_df": resid >= suff["min_resid_df"]}
    out["minimums_met"] = all(out["minimums"].values())
    return out
```

### `hypocurate/pipeline/flags.py`

```python
"""The code checks that raise flags (PRD 5.3; build step 6). Pure functions.

Input: exactly what Checks' access object returns (`records_full`, the projected `plan`).
Checks sees every value (PRD 4) and only raises flags; Inclusion decides what a flag means
under the locked plan. **Only per-record and pairwise rules are used**: no model, slope,
residual or hypothesis of the plan, so agreement with the relationship under test can never
decide which records are credible (PRD 5.3). Every setting is read from the locked plan.

Flags (owner, 2026-10-05):
- `invalid_value` / "physically impossible": tensile strength below yield strength, or a
  grain size of zero or less. One flag per record.
- Duplicates and conflicts, **only between records of different sources** (register
  'conflict_pairing_rule'); rows within one source are separate measurements. Two records
  are *candidates* when they have the same alloy (the plan's same-alloy rule), grain sizes
  within the plan's tolerance (a matching tolerance), and nothing known that differs: the
  same paper or a paper unknown on one side, and the same test conditions (test type,
  test temperature) or a condition unknown on one side.
  - same paper and every condition known: yield strengths within the tolerance → an exact
    duplicate; beyond it → a conflict (`values_disagree`, "differ beyond tolerance");
  - the paper or a condition unknown on one side: yield strengths within the tolerance → a
    possible duplicate; beyond it → not a candidate (nothing says it is the same measurement).
  Candidate links form groups (connected components). A group with two or more records from
  one source, or one in which some pair is not linked, is ambiguous: `possible_duplicate`,
  "several candidates" (nothing is paired on a guess). Otherwise a group with any conflicting
  pair is a conflict, else a possible duplicate if any link is possible, else an exact
  duplicate. One flag per group, naming all its records.
- Relative difference: |a − b| / min(|a|, |b|) (register 'values_disagree_tolerance').
- The numbers compared are stored with the flag for audit (`compared_values`) and never
  returned to the Critic (step 5).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Iterable, Mapping

from hypocurate.sources.normalize import doi_group_key, identity_hash, same_alloy_key

VALUE_STATUSES = ("converted", "assigned_from_source", "assigned_by_decision")


@dataclass
class Flag:
    kind: str
    category: str
    records: list[int]
    compared_values: dict = field(default_factory=dict)


def relative_difference(a: float, b: float) -> float:
    small = min(abs(a), abs(b))
    if a == b:
        return 0.0
    return abs(a - b) / small if small > 0 else math.inf


def _value(rec: Mapping, f: str) -> Any:
    entry = rec["harmonized"].get(f) if isinstance(rec.get("harmonized"), Mapping) else None
    if isinstance(entry, Mapping) and entry.get("status") in VALUE_STATUSES:
        return entry.get("value")
    return None


def _number(rec: Mapping, f: str) -> float | None:
    v = _value(rec, f)
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def paper(rec: Mapping, grouping: Mapping[str, str]) -> str | None:
    """The paper a record cites: from its DOI for a source grouped by paper; the dataset
    itself for a source that is its own paper (grouped by dataset)."""
    if grouping.get(rec["source"]) in ("dataset", "batch"):
        return f"dataset:{rec['source']}"
    doi = rec.get("paper_doi")
    return identity_hash(doi_group_key(doi)) if isinstance(doi, str) and doi.strip() else None


def invalid_values(records: Iterable[Mapping], outcome: str) -> list[Flag]:
    out = []
    for r in records:
        ys, uts, gs = _number(r, outcome), _number(r, "ultimate_tensile_strength"), _number(r, "grain_size")
        reasons = {}
        if outcome == "yield_strength" and ys is not None and uts is not None and uts < ys:
            reasons["ultimate_tensile_strength_below_yield_strength"] = [uts, ys]
        if gs is not None and gs <= 0:
            reasons["grain_size_not_positive"] = [gs]
        if reasons:
            out.append(Flag("invalid_value", "physically impossible", [r["id"]], reasons))
    return out


def _condition(a: Mapping, b: Mapping) -> str:
    """'same', 'unknown' (a condition missing on one side) or 'differs'."""
    state = "same"
    for f in ("test_type", "test_temperature"):
        va, vb = _value(a, f), _value(b, f)
        if va is None or vb is None:
            state = "unknown"
        elif va != vb:
            return "differs"
    return state


def _link(a: Mapping, b: Mapping, plan: Mapping, grouping: Mapping) -> tuple[str, dict] | None:
    """The candidate link between two records of different sources, or None."""
    tol, outcome = plan["rules"]["duplicate_tolerance"], plan["variables"]["outcome"]["field"]
    ga, gb, ya, yb = (_number(a, "grain_size"), _number(b, "grain_size"), _number(a, outcome), _number(b, outcome))
    if None in (ga, gb, ya, yb) or relative_difference(ga, gb) > tol:
        return None
    pa, pb = paper(a, grouping), paper(b, grouping)
    if pa is not None and pb is not None and pa != pb:
        return None
    cond = _condition(a, b)
    if cond == "differs":
        return None
    numbers = {"grain_size": [ga, gb], outcome: [ya, yb], "relative_difference": relative_difference(ya, yb)}
    within = numbers["relative_difference"] <= tol
    if pa is not None and pb is not None and cond == "same":
        return ("exact" if within else "conflict"), numbers
    return ("possible", numbers) if within else None


def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any]) -> list[Flag]:
    rules = plan["rules"]
    grouping = {g["source"]: g["unit"] for g in rules["grouping"]}
    by_alloy: dict[str, list[Mapping]] = defaultdict(list)
    for r in records:
        comp = _value(r, "composition")
        if isinstance(comp, Mapping) and comp:
            by_alloy[same_alloy_key(dict(comp), rules["same_alloy_decimals"])].append(r)
    links: dict[tuple[int, int], tuple[str, dict]] = {}
    for group in by_alloy.values():
        for a, b in combinations(sorted(group, key=lambda r: r["id"]), 2):
            if a["source"] != b["source"]:
                link = _link(a, b, plan, grouping)
                if link:
                    links[(a["id"], b["id"])] = link
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for a, b in links:
        parent[find(a)] = find(b)
    components: dict[int, list[int]] = defaultdict(list)
    for x in list(parent):
        components[find(x)].append(x)
    source = {r["id"]: r["source"] for r in records}
    flags = []
    for ids in sorted(sorted(c) for c in components.values()):
        pairs = {(a, b): links[(a, b)] for a, b in combinations(ids, 2) if (a, b) in links}
        compared = {f"{a}-{b}": {"link": kind, **numbers} for (a, b), (kind, numbers) in pairs.items()}
        sources = [source[i] for i in ids]
        kinds = {kind for kind, _ in pairs.values()}
        if len(set(sources)) < len(sources) or len(pairs) < len(ids) * (len(ids) - 1) // 2:
            flags.append(Flag("possible_duplicate", "several candidates", ids, compared))
        elif "conflict" in kinds:
            flags.append(Flag("values_disagree", "differ beyond tolerance", ids, compared))
        else:
            identical = all(n["relative_difference"] == 0 and n["grain_size"][0] == n["grain_size"][1]
                            for _, n in pairs.values())
            category = "identical values" if identical else "within tolerance"
            flags.append(Flag("possible_duplicate" if "possible" in kinds else "exact_duplicate", category, ids,
                              compared))
    return flags


def raise_flags(plan: Mapping[str, Any], records: list[Mapping]) -> list[Flag]:
    """Every flag for the run's records under the locked plan, in a fixed order."""
    return invalid_values(records, plan["variables"]["outcome"]["field"]) + duplicate_groups(records, plan)
```

### `hypocurate/pipeline/writes.py`

```python
"""Shared write path of the step 6 pipeline: the locking protocol, refusals and their log.

**Every write follows the protocol of step 3** (README, "Database migrations"): one
`run_transaction` (retried on 40P01 / 40001), `SET LOCAL lock_timeout`, then
`hc_write_lock(p_run => …)` before anything is written to the run or its child rows.

**Reads and writes are apart.** Inclusion and Checks read through their access objects
(`dispatch.bind_code`), each read one transaction under the run's lock; never call the access
layer while holding the run's lock. The write transaction that follows takes the lock again
and re-checks, by ids and codes only (never record values), that nothing it read has changed
since: the stage, the records, the flags, the decisions.

**A refusal is logged, then raised** (PRD 14.2: changes after a checkpoint are rejected and
logged). Our own refusals (the stage has moved on, something changed since it was read,
constructed data in a run not marked as a test) and the database's (a trigger or a
constraint) are written to `audit_log` in their own short transaction **without**
`hc_write_lock`: the named exception of step 5 (register entry
'audit_failure_rows_without_run_lock'), extended in step 6 to refusals of these write paths
(owner, 2026-10-05). The row holds the function, a fixed code and, for a database refusal,
the database's own message (our triggers' fixed texts). If the database cannot take the row,
the process log (`hypocurate.pipeline`) is the fallback.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError, IntegrityError

from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
from hypocurate.access.stage import actual_stage
from hypocurate.db.retry import run_transaction

LOG = logging.getLogger("hypocurate.pipeline")
LOCK_TIMEOUT_MS = ACCESS_LOCK_TIMEOUT_MS
# The roles under which the pipeline's own writes are logged.
WRITE_ROLES = ("extraction", "checks", "inclusion", "checkpoint")
CODES = {
    "stage_mismatch": "the run is not at the stage this step needs",
    "changed_since_read": "the run's records, flags or decisions changed after they were read",
    "already_done": "this step has already been done for the run",
    "constructed_data_unmarked": "constructed test data in a run not marked as a test",
    "rejected_by_database": "the database refused the write",
    "invalid_plan": "the plan is not valid for the supported template",
    "tag_not_available": "a tag value of the plan is not an approved value of the fixed lists",
}
CONSTRUCTED_MARK = "constructed_test_data"


class Refused(Exception):
    """A pipeline write refused; already logged in audit_log (or the process log)."""

    def __init__(self, function: str, code: str, message: str | None = None):
        self.function, self.code, self.message = function, code, message
        super().__init__(f"{function} refused: {CODES[code]}" + (f" ({message})" if message else ""))


_AUDIT = text("INSERT INTO audit_log (run_id, role, stage, function, allowed, detail) "
              "VALUES (:r, :role, :stage, :f, false, :d)").bindparams(bindparam("d", type_=JSONB))


def log_refusal(engine: Engine, run_id: int, role: str, function: str, code: str, message: str | None = None) -> None:
    """One refusal row in its own transaction, without the run lock (the named exception)."""
    detail: dict[str, Any] = {"result": "rejected", "code": code}
    if message:
        detail["message"] = message[:300]

    def write(conn: Connection):
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one_or_none()
        stage = actual_stage(conn, run_id, status) if status else "none"
        conn.execute(_AUDIT, dict(r=run_id if status else None, role=role, stage=stage, f=function, d=detail))

    try:
        run_transaction(engine, write)
    except Exception as error:  # the database is unavailable: the process log is the fallback
        LOG.error(json.dumps({"refusal_fallback": {"run": run_id, "role": role, "function": function, **detail},
                              "error": type(error).__name__}, sort_keys=True))


def database_message(error: DBAPIError) -> str:
    """The database's own refusal text: the first line, our triggers' fixed messages."""
    orig = getattr(error, "orig", None)
    diag = getattr(orig, "diag", None)
    primary = getattr(diag, "message_primary", None)
    return (primary or str(orig or error)).splitlines()[0][:300]


def write(engine: Engine, run_id: int, role: str, function: str, body: Callable[[Connection, str], Any]) -> Any:
    """Runs `body(conn, stage)` in one locked transaction; logs and raises any refusal."""

    def transaction(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {int(LOCK_TIMEOUT_MS)}"))
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        return body(conn, actual_stage(conn, run_id, status))

    try:
        return run_transaction(engine, transaction)
    except Refused as refused:
        log_refusal(engine, run_id, role, function, refused.code, refused.message)
        raise
    except IntegrityError as error:
        message = database_message(error)
        log_refusal(engine, run_id, role, function, "rejected_by_database", message)
        raise Refused(function, "rejected_by_database", message) from None


def constructed_unmarked(conn: Connection, run_id: int, source_keys: list[str]) -> bool:
    """True if any of `source_keys` is constructed test data and the run is not marked as a test."""
    from hypocurate.sources.versions import SOURCES
    if not any(SOURCES[k].constructed for k in source_keys if k in SOURCES):
        return False
    flags = conn.execute(text("SELECT experiment_flags FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
    return not (isinstance(flags, dict) and flags.get(CONSTRUCTED_MARK) is True)


def run_record_sources(conn: Connection, run_id: int) -> list[str]:
    return list(conn.execute(text(
        "SELECT DISTINCT s.key FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
        "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r"), dict(r=run_id)).scalars())


def record_ids(conn: Connection, run_id: int) -> list[int]:
    return list(conn.execute(text("SELECT id FROM record WHERE extraction_run_id = :r ORDER BY id"),
                             dict(r=run_id)).scalars())


def flag_index(conn: Connection, run_id: int) -> list[tuple[int, str, str, tuple[int, ...]]]:
    rows = conn.execute(text(
        "SELECT f.id, f.kind, f.category, coalesce(array_agg(fr.record_id ORDER BY fr.record_id) "
        "FILTER (WHERE fr.record_id IS NOT NULL), '{}') FROM flag f LEFT JOIN flag_record fr ON fr.flag_id = f.id "
        "WHERE f.run_id = :r GROUP BY f.id ORDER BY f.id"), dict(r=run_id)).all()
    return [(i, k, c, tuple(ids)) for i, k, c, ids in rows]


def code_stage(conn: Connection, run_id: int, stage: str, input_: dict, output: dict) -> int:
    """A finished stage result of a code step (role NULL): written running, then done."""
    sid = conn.execute(text(
        "INSERT INTO stage_result (run_id, stage, attempt, role, input) VALUES (:r, :s, "
        "(SELECT coalesce(max(attempt), 0) + 1 FROM stage_result WHERE run_id = :r AND stage = :s), NULL, :i) "
        "RETURNING id").bindparams(bindparam("i", type_=JSONB)), dict(r=run_id, s=stage, i=input_)).scalar_one()
    conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = :o WHERE id = :s")
                 .bindparams(bindparam("o", type_=JSONB)), dict(o=output, s=sid))
    return sid
```

### `hypocurate/pipeline/checkpoints.py`

```python
"""The two checkpoints (PRD 5.6; build step 6): the rules lock and the dataset freeze.

**Rules lock** (`lock_rules`): the plan, validated against the template, is stored with its
fingerprint and the database's time, with the run's three tags, in one transaction under the
run's lock. After it nothing in the plan can change: the database refuses any change to a
plan or a second plan (migration 0001), and this path refuses and logs a second lock.

**Dataset freeze** (`freeze_dataset`): Inclusion's access object reads the locked plan, the
record conditions and the flags; code recomputes every set from them and checks that the
stored decisions and sets are exactly what the locked rules produce. Then, in one locked
transaction that re-checks the records, flags and decisions by id, it stores:
- the counts of each set, known from structure and grain sizes only (no outcome value): records,
  alloys, alloys with enough grain sizes, independent groups and residual degrees of freedom,
  for the primary set, each source within it and each sensitivity set, with whether the plan's
  minimums are met, as information (`stage_result` "dataset_freeze"); step 7 writes the
  analysis results and decides the outcome;
- the fingerprint: SHA-256 of the canonical JSON of the plan's fingerprint, every set's records
  (each with a hash of its stored content) and every set's rules, and the counts;
- `run_snapshot`, or, when no record is eligible, the run-level "no dataset frozen" row
  (PRD 5.6: no dataset is frozen and no test is run).
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import bindparam, Text

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, log_refusal,
                                        record_ids, run_record_sources, write)


def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
    """Locks the run's rules with `content`; returns the plan's fingerprint."""
    try:
        plan = validate(content)
        tags = tags_for(plan)
    except PlanError as error:
        log_refusal(engine, run_id, "checkpoint", "lock_rules", "invalid_plan", str(error))
        raise Refused("lock_rules", "invalid_plan", str(error)) from None
    fp = fingerprint(plan)

    def body(conn: Connection, stage: str):
        if stage != "before_lock":
            raise Refused("lock_rules", "already_done" if stage != "none" else "stage_mismatch")
        version = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        if plan["hypothesis_version"] != version:
            raise Refused("lock_rules", "invalid_plan", "the plan names another hypothesis version")
        ids = []
        for kind, value in tags.items():
            tid = conn.execute(text("SELECT id FROM tag_value WHERE kind = :k AND value = :v AND status = 'approved'"),
                               dict(k=kind, v=value)).scalar_one_or_none()
            if tid is None:
                raise Refused("lock_rules", "tag_not_available", f"{kind}: {value}")
            ids.append(tid)
        s = plan["sufficiency"]
        conn.execute(text(
            "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
            "min_resid_df, sensitivity_analysis_keys) VALUES (:r, :c, :fp, :o, :a, :b, :g, :d, :k)").bindparams(
            bindparam("c", type_=JSONB), bindparam("k", type_=ARRAY(Text))),
            dict(r=run_id, c=plan, fp=fp, o=s["option"], a=s["min_records"], b=s["min_alloys"], g=s["min_groups"],
                 d=s["min_resid_df"], k=list(plan["sensitivity_analyses"])))
        for tid in ids:
            conn.execute(text("INSERT INTO run_tag (run_id, tag_value_id) VALUES (:r, :t)"), dict(r=run_id, t=tid))
        return fp

    return write(engine, run_id, "checkpoint", "lock_rules", body)


def _set_records(conn: Connection, run_id: int) -> dict[str, list[int]]:
    rows = conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a LEFT JOIN analysis_set_record asr "
                             "ON asr.analysis_set_id = a.id WHERE a.run_id = :r"), dict(r=run_id)).all()
    out: dict[str, list[int]] = {}
    for key, rid in rows:
        out.setdefault(key, [])
        if rid is not None:
            out[key].append(rid)
    return {k: sorted(v) for k, v in out.items()}


def freeze_dataset(engine: Engine, run_id: int) -> dict:
    """Freezes the analysis dataset (or records that none is frozen); returns the freeze record."""
    data = role_input(bind_code(engine, run_id, "inclusion"))
    plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
    by_id = {r["id"]: r for r in records}
    sets = el.all_sets(plan, records, flags)
    members = {key: el.members(rules) for key, rules in sets.items()}
    counts: dict[str, Any] = {key: el.counts(plan, by_id, ids, key) for key, ids in members.items()}
    counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
                                                            if by_id[i]["source"] == source])
                            for source in sorted({by_id[i]["source"] for i in members[el.PRIMARY]})}
    content = {
        "plan": data["plan"]["fingerprint"],
        "sets": {key: [[i, by_id[i]["fingerprint"]] for i in ids] for key, ids in members.items()},
        "rules": {key: {str(i): rule for i, rule in sorted(rules.items())} for key, rules in sets.items()},
        "counts": counts,
    }
    fp = hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
    read_ids = sorted(by_id)
    read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("freeze_dataset", "already_done" if stage in ("analysis", "closed_without_freeze")
                          else "stage_mismatch")
        if constructed_unmarked(conn, run_id, run_record_sources(conn, run_id)):
            raise Refused("freeze_dataset", "constructed_data_unmarked")
        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
            raise Refused("freeze_dataset", "changed_since_read")
        stored = dict(conn.execute(text("SELECT record_id, rule FROM run_record WHERE run_id = :r"),
                                   dict(r=run_id)).all())
        if stored != sets[el.PRIMARY] or _set_records(conn, run_id) != members:
            raise Refused("freeze_dataset", "changed_since_read",
                          "the stored decisions are not what the locked rules produce")
        record = {"fingerprint": fp, "counts": counts, "frozen": bool(members[el.PRIMARY])}
        code_stage(conn, run_id, "dataset_freeze", {"plan": data["plan"]["fingerprint"]}, record)
        if members[el.PRIMARY]:
            conn.execute(text("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, :n)"),
                         dict(r=run_id, fp=fp, n=len(members[el.PRIMARY])))
        else:
            conn.execute(text("INSERT INTO calibration_result (run_id, status, reason) "
                              "VALUES (:r, 'unavailable', 'no_dataset_frozen')"), dict(r=run_id))
        return record

    return write(engine, run_id, "checkpoint", "freeze_dataset", body)
```

### `hypocurate/pipeline/extract.py`

```python
"""Storing a run's records after the rules lock (PRD 5.6, 10; build step 6).

For tabular sources the adapters (code) extract the records: each chosen source's sealed
version, recorded for the run at dispatch, is read by its adapter, and every record it
returns is stored in the run, unchanged and in file order, with how it was extracted
(`record.extraction`: method "adapter", the adapter's name and version; owner, 2026-10-05).
Every record found is kept; eligibility is decided later by code (PRD 5.3). What the Curator
agent does for tabular sources is an open owner decision for step 8; this step does not
settle it.

One transaction per source, under the run's lock (`writes.write`). The source's search
status becomes `searched`; an adapter that refuses the file makes it `failed` with the kind of
nothing found `failed_search` (PRD 3.1), and nothing is stored from it. Records of a
constructed source (the controlled duplicate extract) are refused, and the refusal logged,
unless the run is marked as a test (register 'constructed_test_runs').
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.pipeline.writes import Refused, constructed_unmarked, write
from hypocurate.sources import adapters
from hypocurate.sources.record import AdapterError
from hypocurate.sources.versions import UnsealedVersion, load_sealed_version

_INSERT = text(
    "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, alloy, harmonized, "
    "reported, paper_reference, paper_doi, extraction) VALUES (:r, :v, :k, :i, :kind, :a, :h, :rep, :pr, :pd, :x)"
).bindparams(bindparam("h", type_=JSONB), bindparam("rep", type_=JSONB), bindparam("x", type_=JSONB))


def pending_sources(engine: Engine, run_id: int) -> list[str]:
    with engine.connect() as conn:
        return list(conn.execute(text(
            "SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r "
            "AND rs.search_status = 'pending' AND rs.source_version_id IS NOT NULL ORDER BY s.key"),
            dict(r=run_id)).scalars())


def store_source(engine: Engine, run_id: int, source_key: str) -> int:
    """Stores the records of one chosen source; returns how many were stored."""

    def body(conn: Connection, stage: str) -> int:
        if stage != "curation":
            raise Refused("store_records", "stage_mismatch")
        row = conn.execute(text(
            "SELECT rs.source_id, rs.source_version_id, rs.search_status FROM run_source rs "
            "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r AND s.key = :k"),
            dict(r=run_id, k=source_key)).one_or_none()
        if row is None or row.source_version_id is None:
            raise Refused("store_records", "stage_mismatch", "the source is not chosen for this run")
        if row.search_status != "pending":
            raise Refused("store_records", "already_done")
        if constructed_unmarked(conn, run_id, [source_key]):
            raise Refused("store_records", "constructed_data_unmarked")
        try:
            result = adapters.read(load_sealed_version(conn, row.source_version_id))
        except (AdapterError, UnsealedVersion) as error:
            conn.execute(text("UPDATE run_source SET search_status = 'failed', nothing_found = 'failed_search', "
                              "failure_reason = :f, decided_at = now() WHERE run_id = :r AND source_id = :s"),
                         dict(f=f"the adapter refused the source version ({type(error).__name__})", r=run_id,
                              s=row.source_id))
            return 0
        extraction = adapters.extraction(source_key)
        params = []
        for rec in result.records:
            j = rec.to_json()
            params.append(dict(r=run_id, v=row.source_version_id, k=j["source_item_key"], i=j["item_index"],
                               kind=j["kind"], a=j["alloy"], h=j["harmonized"], rep=j["reported"],
                               pr=j["paper_reference"], pd=j["paper_doi"], x=extraction))
        if params:
            conn.execute(_INSERT, params)
        conn.execute(text("UPDATE run_source SET search_status = 'searched', decided_at = now() "
                          "WHERE run_id = :r AND source_id = :s"), dict(r=run_id, s=row.source_id))
        return len(params)

    return write(engine, run_id, "extraction", "store_records", body)


def store_records(engine: Engine, run_id: int) -> dict[str, int]:
    """Stores the records of every chosen source still pending, one source per transaction."""
    return {key: store_source(engine, run_id, key) for key in pending_sources(engine, run_id)}
```

### `hypocurate/pipeline/checks.py`

```python
"""Checks (code; PRD 4, 5.3; build step 6): raise the flags of a run's records.

Reads through its own access object (`dispatch.bind_code(…, "checks")`: the locked plan and
every stored value), computes the flags with `pipeline.flags` (per-record and pairwise rules
only), then writes them in one transaction under the run's lock that re-checks the records by
id. Checks never decides eligibility. Flags are raised once per run, before the freeze; the
numbers compared are stored for audit and never returned to the Critic.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline.flags import Flag, raise_flags
from hypocurate.pipeline.writes import Refused, code_stage, flag_index, record_ids, write


def run_checks(engine: Engine, run_id: int) -> list[Flag]:
    data = role_input(bind_code(engine, run_id, "checks"))
    plan, records = data["plan"]["content"], data["records_full"]
    flags = raise_flags(plan, records)
    read_ids = sorted(r["id"] for r in records)

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("raise_flags", "stage_mismatch")
        if flag_index(conn, run_id) or conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'checks')"),
                dict(r=run_id)).scalar_one():
            raise Refused("raise_flags", "already_done")
        if record_ids(conn, run_id) != read_ids:
            raise Refused("raise_flags", "changed_since_read")
        for f in flags:
            fid = conn.execute(text("INSERT INTO flag (run_id, kind, category, compared_values) "
                                    "VALUES (:r, :k, :c, :v) RETURNING id").bindparams(bindparam("v", type_=JSONB)),
                               dict(r=run_id, k=f.kind, c=f.category, v=f.compared_values)).scalar_one()
            conn.execute(text("INSERT INTO flag_record (flag_id, record_id) VALUES (:f, :r)"),
                         [dict(f=fid, r=rid) for rid in f.records])
        counts: dict[str, int] = {}
        for f in flags:
            counts[f"{f.kind}/{f.category}"] = counts.get(f"{f.kind}/{f.category}", 0) + 1
        code_stage(conn, run_id, "checks", {"plan": data["plan"]["fingerprint"], "records": len(read_ids)},
                   {"flags": dict(sorted(counts.items()))})
        return flags

    return write(engine, run_id, "checks", "raise_flags", body)
```

### `hypocurate/pipeline/inclusion.py`

```python
"""Inclusion (code; PRD 4, 5.3; build step 6): every record's eligibility under the locked rules.

Reads through its own access object (`dispatch.bind_code(…, "inclusion")`): the locked plan,
the record conditions and the flags by kind and category. **It receives no outcome value**, so
no eligibility decision can depend on a record's outcome directly or on its position relative
to the tested relationship. It does act on the flags Checks raised, which compared values
(register 'code_role_access').

`pipeline.eligibility` decides one rule per record for the primary set and for every
sensitivity set the plan names. One transaction under the run's lock re-checks the records
and flags by id, then writes a decision for every record (`run_record`: eligible exactly when
the rule is `in_scope`, with the rule that decided it), each set (`analysis_set`,
`analysis_set_record`), and a code stage result "inclusion" listing each sensitivity set's
rules where they differ from the primary set's. Decisions are written once, before the freeze.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, text

from hypocurate.access.dispatch import bind_code
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, record_ids,
                                        run_record_sources, write)


def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
    data = role_input(bind_code(engine, run_id, "inclusion"))
    plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
    sets = el.all_sets(plan, records, flags)
    read_ids = sorted(r["id"] for r in records)
    read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("decide", "stage_mismatch")
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_record WHERE run_id = :r)"), dict(r=run_id)).scalar_one():
            raise Refused("decide", "already_done")
        if constructed_unmarked(conn, run_id, run_record_sources(conn, run_id)):
            raise Refused("decide", "constructed_data_unmarked")
        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
            raise Refused("decide", "changed_since_read")
        primary = sets[el.PRIMARY]
        if primary:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)"),
                         [dict(r=run_id, c=rid, e=rule == "in_scope", u=rule) for rid, rule in sorted(primary.items())])
        for key, rules in sets.items():
            sid = conn.execute(text("INSERT INTO analysis_set (run_id, key) VALUES (:r, :k) RETURNING id"),
                               dict(r=run_id, k=key)).scalar_one()
            ids = el.members(rules)
            if ids:
                conn.execute(text("INSERT INTO analysis_set_record (analysis_set_id, record_id) VALUES (:s, :c)"),
                             [dict(s=sid, c=rid) for rid in ids])
        differences = {key: {str(rid): rule for rid, rule in sorted(rules.items()) if rule != primary[rid]}
                       for key, rules in sets.items() if key != el.PRIMARY}
        totals = {key: {rule: sum(r == rule for r in rules.values()) for rule in sorted(set(rules.values()))}
                  for key, rules in sets.items()}
        code_stage(conn, run_id, "inclusion", {"plan": data["plan"]["fingerprint"], "records": len(read_ids),
                                               "flags": len(read_flags)},
                   {"rules": totals, "differences_from_primary": differences,
                    "changes": {k: el.SENSITIVITY_CHANGES[k] for k in sets if k != el.PRIMARY}})
        return sets

    return write(engine, run_id, "inclusion", "decide", body)
```

### `hypocurate/db/migrations/versions/0002_tag_starting_lists.py`

```python
"""Tag starting lists (build step 6; PRD 5.5; register entry 'tag_starting_lists').

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05

Data only: no schema change. Inserts the owner's starting values of the three fixed tag
lists as approved, so that every database has them before any run locks its three tags
(the same way 0001 seeds the domains).

- **Safe on a database that already has some of the values:** each row is inserted with
  `ON CONFLICT (kind, value) DO NOTHING`. A value that already exists keeps its row and its
  status (proposed, approved or rejected); it is not changed.
- **Works with the previous release's code:** step 5 code only reads approved tag values.
- **Downgrade does nothing** (owner, 2026-10-05): tag values can never be deleted (trigger
  `hc_tag_value_no_delete`), and a run may already have attached one. The rows stay; only
  the revision goes back to 0001. Going down to base removes them with the whole table
  (0001's downgrade).

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

# The owner's starting lists (register entry 'tag_starting_lists', 2026-10-05), written out
# here so that this migration stays as it was when it was written.
TAG_STARTING_LISTS = {
    "property": ("yield strength", "ultimate tensile strength", "hardness", "elongation", "fatigue life"),
    "alloy_class": ("multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy", "titanium alloy",
                    "nickel alloy", "copper alloy", "magnesium alloy", "other"),
    "test_condition": ("room-temperature tension", "room-temperature compression", "elevated temperature",
                       "cryogenic", "hardness test", "fatigue"),
}


def upgrade() -> None:
    insert = sa.text("INSERT INTO tag_value (kind, value, status, decided_at) "
                     "VALUES (:kind, :value, 'approved', now()) ON CONFLICT (kind, value) DO NOTHING")
    for kind, values in TAG_STARTING_LISTS.items():
        for value in values:
            op.execute(insert.bindparams(kind=kind, value=value))


def downgrade() -> None:
    """Data-only revision: the rows stay (see the module docstring)."""
```

### `hypocurate/db/migrations/versions/0003_record_extraction.py`

```python
"""How each record was extracted (build step 6; register entry 'record_extraction_provenance').

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-05

Additive. Each stored record states how it was extracted: by adapter code (with the
adapter's name and version) or, from step 8, by an agent, so that records extracted by code
can always be told apart from records an agent extracts later (owner, 2026-10-05).

- A new nullable column `record.extraction` (JSONB) with a CHECK on its shape: an object
  whose `method` is 'adapter' or 'agent', with a non-empty `name` and `version`. Existing
  rows keep NULL (the live database has none; every record before this step was a test row).
- `hc_record_insert` is replaced: **every check of 0001 is kept unchanged, in the same
  order**, and one is added at the end: a new record must carry `extraction`.
- 0001 and 0002 are untouched.
- **Works with the previous release's code:** that code inserts no records outside tests.
- **Downgrade** restores 0001's `hc_record_insert` exactly and drops the column; the
  extraction values stored in it are lost.

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

SHAPE = ("extraction IS NULL OR (jsonb_typeof(extraction) = 'object' "
         "AND (extraction->>'method') IN ('adapter', 'agent') "
         "AND length(coalesce(extraction->>'name', '')) > 0 "
         "AND length(coalesce(extraction->>'version', '')) > 0)")

# 0001's function, verbatim (restored by the downgrade).
RECORD_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        RETURN NEW;
    END $$
    """

# The same checks, then the new requirement.
RECORD_INSERT_0003 = """
    CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        IF NEW.extraction IS NULL THEN
            PERFORM hc_reject('a record states how it was extracted (adapter or agent, with name and version)');
        END IF;
        RETURN NEW;
    END $$
    """


def upgrade() -> None:
    op.add_column('record', sa.Column('extraction', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_check_constraint(op.f('ck_record_extraction_shape'), 'record', SHAPE)
    op.execute(RECORD_INSERT_0003)


def downgrade() -> None:
    op.execute(RECORD_INSERT_0001)
    op.drop_constraint(op.f('ck_record_extraction_shape'), 'record', type_='check')
    op.drop_column('record', 'extraction')
```

## 6. Migration 0003: `hc_record_insert` before and after

Left: 0001's function as 0003 restores it on downgrade (a test checks it equals 0001's text). Right: 0003's function.

```
    CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$                |     CREATE OR REPLACE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN                                                                                               |     BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN                           |         IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');                      |             PERFORM hc_reject('records are extracted while their run is running');
        END IF;                                                                                         |         END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN                    |         IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');                       |             PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;                                                                                         |         END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN                                                     |         IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');                      |             PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;                                                                                         |         END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id              |         IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN                         |                          AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');         |             PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;                                                                                         |         END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN|         IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');                   |             PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;                                                                                         |         END IF;
        RETURN NEW;                                                                                     |         IF NEW.extraction IS NULL THEN
    END $$                                                                                              |             PERFORM hc_reject('a record states how it was extracted (adapter or agent, with name and version)');
                                                                                                        |         END IF;
                                                                                                        |         RETURN NEW;
                                                                                                        |     END $$
                                                                                                        | 
```

Unified diff:

```diff
--- 0001 hc_record_insert (as restored by 0003's downgrade)
+++ 0003 hc_record_insert
@@ -17,6 +17,9 @@
         IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
             PERFORM hc_reject('a record has the kind of data of its source version');
         END IF;
+        IF NEW.extraction IS NULL THEN
+            PERFORM hc_reject('a record states how it was extracted (adapter or agent, with name and version)');
+        END IF;
         RETURN NEW;
     END $$
     
\ No newline at end of file
```

## 7. Other code changes (diffs against `main`)

```diff
diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index f996bb1..aa264b7 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -36,10 +36,17 @@ from __future__ import annotations
 from types import MappingProxyType
 from typing import Mapping
 
-from hypocurate.access.vocabulary import (CATEGORY_FIELDS, ELIGIBILITY_RULES, FLAG_KINDS, PHASE_CLASSES,
-                                          PROCESSING_METHODS, SENSITIVITY_KEYS, TEMPERATURE_BANDS, TEST_TYPES)
+from hypocurate.access.vocabulary import (CATEGORY_FIELDS, ELIGIBILITY_RULES, FLAG_CATEGORIES, FLAG_KINDS,
+                                          GROUPING_UNITS, PHASE_CLASSES, PROCESSING_METHODS, PROFILE_NAMES,
+                                          SENSITIVITY_KEYS, SINGLE_PHASE, SOURCE_KEYS, TEMPERATURE_BANDS, TEST_TYPES,
+                                          VALUE_STATUSES)
 
 ROLES = ("planner", "curator", "critic", "analyst", "commentator")
+# The code roles of PRD 4 (step 6, owner 2026-10-05): Inclusion and Checks are code, not
+# agents. They read through access objects too, bound by `dispatch.bind_code`, so their reads
+# are logged. No agent setting can bind as one of them.
+CODE_ROLES = ("inclusion", "checks")
+ALL_ROLES = ROLES + CODE_ROLES
 
 # none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
 # frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
@@ -86,6 +93,11 @@ FIELDS = MappingProxyType({
                            "temperature; counts by test type and by phase. Never a row-level value, an "
                            "outcome value or a statistic derived from outcomes.",
     "gap_report": "The Analyst's gap report: the output of each Analyst stage of the run.",
+    "record_conditions": "Per stored record, for Inclusion (code): id, source, row number, kind, a hash of the "
+                         "stored record, whether it carries a DOI, identities as hashes (paper from the DOI, "
+                         "batch), composition, each "
+                         "field's status, grain size and test temperature, and the category values from their "
+                         "vocabularies. No outcome value, no value as reported, no free text.",
     "outcome": "The run's status, outcome, verdict and exploratory label.",
 })
 
@@ -119,9 +131,20 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
 })
 
 
+# The code roles' lists (owner, 2026-10-05). Checks sees all values (PRD 4: it compares them);
+# Inclusion is blind: it receives no outcome value, so no eligibility decision can depend on a
+# record's outcome directly or on its position relative to the tested relationship. It acts on
+# the flags Checks raised, by kind and category.
+CODE_ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
+    "inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind"})}),
+    "checks": MappingProxyType({"curation": frozenset({"plan", "records_full"})}),
+})
+
+
 def allowed(role: str, stage: str) -> frozenset[str]:
     """The fields `role` may receive at `stage`; empty for any role or stage not listed."""
-    return ALLOWED.get(role, {}).get(stage, frozenset())
+    lists = ALLOWED.get(role) or CODE_ALLOWED.get(role) or {}
+    return lists.get(stage, frozenset())
 
 
 # The fields that can be the outcome of a plan. The Planner does not know which one its
@@ -145,6 +168,10 @@ CONDITION_COUNT_FIELDS = ("test_type", "phase_class")
 SOURCE_META_FIELDS = ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                       "fields_available")
 
+# record_conditions: the one column as reported that Inclusion receives, per source, as a hash:
+# the batch, for the sensitivity analysis that groups by batch (six batches for Texas A&M).
+BATCH_COLUMNS = MappingProxyType({"tamu_fcc": "Iteration"})
+
 # The plan, projected recursively (owner, 2026-10-05: defined in step 5; step 6's plan model
 # must follow it). A schema is a dict of named keys; a leaf is "number", "integer",
 # "field" (a common field name), "unit", or a vocabulary (a frozenset); ("list", schema) is
@@ -176,9 +203,19 @@ PLAN_SCHEMA = MappingProxyType({
     "fields_to_extract": ("list", "field"),
     "exclusion_rules": ("list", {"rule": EXCLUSION_RULES, "min": "number", "max": "number",
                                  "values": ("list", CATEGORY_VALUES)}),
-    "eligibility_rules": ("list", {"flag_kind": FLAG_KINDS, "rule": ELIGIBILITY_RULES}),
+    # A flag category narrows an entry (step 6): an ambiguous group is a possible duplicate
+    # with the category "several candidates".
+    "eligibility_rules": ("list", {"flag_kind": FLAG_KINDS, "category": FLAG_CATEGORIES, "rule": ELIGIBILITY_RULES}),
     "verdict_statement": VERDICT_STATEMENTS,
     "sensitivity_analyses": ("list", SENSITIVITY_KEYS),
+    # Step 6 (owner, 2026-10-05): every setting that affects which records are eligible or how
+    # they are grouped is a value of the locked plan, and the domain profile it came from.
+    "profile": {"name": PROFILE_NAMES, "version": "integer"},
+    "rules": {"same_alloy_decimals": "integer", "duplicate_tolerance": "number",
+              "survivor_source_order": ("list", SOURCE_KEYS), "min_grain_sizes": "integer",
+              "room_temperature_min": "number", "room_temperature_max": "number", "single_phase": SINGLE_PHASE,
+              "accepted_value_statuses": ("list", VALUE_STATUSES),
+              "grouping": ("list", {"source": SOURCE_KEYS, "unit": GROUPING_UNITS})},
 })
 POWER_SCHEMA = MappingProxyType({"method": POWER_METHODS, "within_paper_similarity": "number",
                                  "smallest_effect": "number", "scatter": "number"})
diff --git a/hypocurate/access/dispatch.py b/hypocurate/access/dispatch.py
index ef65cf0..188550d 100644
--- a/hypocurate/access/dispatch.py
+++ b/hypocurate/access/dispatch.py
@@ -14,6 +14,14 @@ again that the run is still at the bound stage.
 
 Nothing a model controls ever receives SQL, a database connection or a file path (CLAUDE.md):
 agents get text built from `role_input` and from reads through this object only.
+
+`bind_code(engine, run_id, role)` (step 6, owner 2026-10-05) binds the two **code roles** of
+PRD 4, Inclusion and Checks, which have no agent setting. It is called by trusted pipeline
+code (`hypocurate.pipeline`) only. It refuses any other role (`not_a_code_role`), reads the
+stage from the database, and binds only where the role has fields (the curation stage);
+elsewhere it is refused with `empty_list`. Every bind is logged like an agent's. An agent
+setting can never bind as a code role: `bind` reads the role from `run_agent_setting`, whose
+roles are the five agent roles (a database CHECK).
 """
 from __future__ import annotations
 
@@ -21,6 +29,7 @@ from sqlalchemy import Connection, Engine, bindparam, text
 from sqlalchemy.dialects.postgresql import JSONB
 from sqlalchemy.exc import DBAPIError
 
+from hypocurate.access.allowlist import CODE_ROLES, allowed
 from hypocurate.access.context import AccessContext
 from hypocurate.access.errors import AccessDenied, AccessFailed
 from hypocurate.access.layer import (_AUDIT, _TRUSTED, ACCESS_LOCK_TIMEOUT_MS, DENIALS, Access, _detail, _row,
@@ -82,4 +91,46 @@ def bind(engine: Engine, run_id: int, agent_setting_id: int, source_key: str | N
     return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)
 
 
-__all__ = ["bind", "bounded_source"]
+def bind_code(engine: Engine, run_id: int, role: str, lock_timeout_ms: int = ACCESS_LOCK_TIMEOUT_MS) -> Access:
+    """An access object for a code role (Inclusion or Checks), or AccessDenied / AccessFailed
+    (logged)."""
+    if not isinstance(run_id, int) or isinstance(run_id, bool):
+        raise TypeError("bind_code takes an integer run id")
+    named = role if isinstance(role, str) and role in CODE_ROLES else UNBOUND
+    probe = AccessContext(run_id, named, UNBOUND)
+
+    def transaction(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)}"))
+        if not conn.execute(text("SELECT EXISTS (SELECT 1 FROM run WHERE id = :r)"), dict(r=run_id)).scalar_one():
+            return ("unknown_run", None)
+        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
+        stage = actual_stage(conn, run_id, status)
+        ctx = AccessContext(run_id, named, stage)
+        code = None
+        if named == UNBOUND:
+            code = "not_a_code_role"
+        elif not allowed(named, stage):
+            code = "empty_list"
+        result = "denied" if code else "allowed"
+        conn.execute(_AUDIT, _row(ctx, run_id, "bind", code is None, _detail(ctx, result, code, stage, code_role=True)))
+        return (result, code, ctx)
+
+    failure = None
+    try:
+        outcome = run_transaction(engine, transaction)
+    except DBAPIError as error:
+        failure = "lock_timeout" if sqlstate(error) == "55P03" else "database_error"
+        keep_in_process_log(probe, "bind", failure, error)
+    if failure is not None:
+        log_failure(engine, probe, "bind", failure, code_role=True)
+        raise AccessFailed(named, UNBOUND, "bind", failure)
+    if outcome[0] == "unknown_run":
+        log_failure(engine, probe, "bind", "unknown_run", run_known=False, code_role=True)
+        raise AccessFailed(named, UNBOUND, "bind", "unknown_run")
+    result, code, ctx = outcome
+    if result == "denied":
+        raise AccessDenied(ctx.role, ctx.stage, "bind", code, DENIALS[code])
+    return Access(engine, ctx, lock_timeout_ms=lock_timeout_ms, _trusted=_TRUSTED)
+
+
+__all__ = ["bind", "bind_code", "bounded_source"]
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 325a67b..cff2979 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -16,7 +16,10 @@ rows of the run: after the freeze the Analyst and the Commentator may see outcom
 """
 from __future__ import annotations
 
+import hashlib
+import json
 import math
+import re
 from collections import Counter
 from dataclasses import dataclass
 from datetime import date, datetime
@@ -26,15 +29,16 @@ from typing import Any, Callable, Iterable, Mapping
 from sqlalchemy import Connection, text
 
 from hypocurate.access import vocabulary as vocab
-from hypocurate.access.allowlist import (CATEGORY_FIELDS, CONDITION_COUNT_FIELDS, CONDITION_RANGE_FIELDS,
-                                         PLAN_SCHEMA, POWER_SCHEMA, SOURCE_META_FIELDS)
+from hypocurate.access.allowlist import (BATCH_COLUMNS, CATEGORY_FIELDS, CONDITION_COUNT_FIELDS,
+                                         CONDITION_RANGE_FIELDS, OUTCOME_FIELDS, PLAN_SCHEMA, POWER_SCHEMA,
+                                         SOURCE_META_FIELDS)
 from hypocurate.access.context import AccessContext as Context
 from hypocurate.sources import adapters
-from hypocurate.sources.normalize import alloy_label, same_alloy_key
-from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, AdapterError
+from hypocurate.sources.normalize import alloy_label, doi_group_key, identity_hash, same_alloy_key
+from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, VALUE_STATUSES, AdapterError
 from hypocurate.sources.versions import SOURCES, UnsealedVersion, load_sealed_version
 
-HAS_VALUE = ("converted", "assigned")
+HAS_VALUE = VALUE_STATUSES
 UNITS = frozenset(u for u in HARMONIZED_FIELDS.values() if u)
 
 
@@ -271,6 +275,42 @@ def record_metadata(conn: Connection, ctx: Context) -> list[dict]:
     return out
 
 
+_ROW = re.compile(r":row:(\d+)$")
+# The non-outcome measured values Inclusion needs (scope and the grain-size rules).
+CONDITION_NUMBERS = ("grain_size", "test_temperature")
+
+
+def record_conditions(conn: Connection, ctx: Context) -> list[dict]:
+    """For Inclusion (code; step 6). No outcome value: outcome fields give their status only.
+    No value as reported and no free text: categories through their vocabularies, the paper
+    (from the DOI) and the batch as hashes, the row number from the origin key."""
+    out = []
+    for r in _stored_records(conn, ctx):
+        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
+        reported = r.reported if isinstance(r.reported, Mapping) else {}
+        row = _ROW.search(r.source_item_key or "")
+        batch_column = BATCH_COLUMNS.get(r.source)
+        batch = reported.get(batch_column, {}).get("text") if batch_column else None
+        doi = r.paper_doi if isinstance(r.paper_doi, str) and r.paper_doi.strip() else None
+        content = {"version_fingerprint": r.version_fingerprint, "origin": r.source_item_key,
+                   "item_index": r.item_index, "kind": r.kind, "harmonized": r.harmonized, "reported": r.reported,
+                   "paper_reference": r.paper_reference, "paper_doi": r.paper_doi}
+        out.append({
+            "id": r.id, "source": r.source, "row": int(row.group(1)) if row else None, "kind": r.kind,
+            # A hash of the stored record (for the freeze fingerprint): it carries no value.
+            "fingerprint": hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"),
+                                                     ensure_ascii=False).encode("utf-8")).hexdigest(),
+            "has_doi": doi is not None,
+            "paper": identity_hash(doi_group_key(doi)) if doi else None,
+            "batch": identity_hash(batch) if isinstance(batch, str) and batch.strip() else None,
+            "composition": _composition(h.get("composition")),
+            "status": {f: _status(h.get(f)) for f in HARMONIZED_FIELDS},
+            "values": {f: _number(h.get(f)) for f in CONDITION_NUMBERS if f not in OUTCOME_FIELDS},
+            "categories": {f: _category(f, h.get(f)) for f in CATEGORY_FIELDS},
+        })
+    return out
+
+
 def _flag_records(conn: Connection, ctx: Context) -> dict[int, list[int]]:
     out: dict[int, list[int]] = {}
     for flag_id, record_id in _rows(conn, "SELECT fr.flag_id, fr.record_id FROM flag_record fr "
@@ -434,5 +474,5 @@ READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "plan": plan, "records_full": records_full, "decisions": decisions, "flags_full": flags_full,
     "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
     "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
-    "gap_report": gap_report, "outcome": outcome,
+    "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions,
 }
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index 6667ddb..b43ac3c 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -56,7 +56,7 @@ from sqlalchemy import Connection, Engine, bindparam, text
 from sqlalchemy.dialects.postgresql import JSONB
 from sqlalchemy.exc import DBAPIError
 
-from hypocurate.access.allowlist import FIELDS, ROLES, STAGES, allowed
+from hypocurate.access.allowlist import ALL_ROLES, FIELDS, STAGES, allowed
 from hypocurate.access.context import AccessContext
 from hypocurate.access.errors import AccessDenied, AccessFailed
 from hypocurate.access.fields import READERS, Refused
@@ -70,7 +70,8 @@ LOG = logging.getLogger("hypocurate.access")
 
 # Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
 DENIALS = {
-    "unknown_role": "the role is not one of the five roles",
+    "unknown_role": "the role is not one of the five agent roles or the two code roles",
+    "not_a_code_role": "only the code roles Inclusion and Checks are bound without an agent setting",
     "unknown_stage": "the stage is not one of the access stages",
     "stage_mismatch": "the run is no longer at the stage this access was bound to",
     "not_on_list": "the field is not on the role's list at the run's stage",
@@ -108,7 +109,7 @@ def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | Non
         d["actual_stage"] = actual
     if ctx.source_key is not None:
         d["source"] = bounded_source(ctx.source_key)
-    for name, raw, valid in (("role", ctx.role, ROLES), ("stage", ctx.stage, STAGES)):
+    for name, raw, valid in (("role", ctx.role, ALL_ROLES), ("stage", ctx.stage, STAGES)):
         if bounded(raw, valid) == "invalid" and raw != "invalid":
             d[f"given_{name}_length"] = len(raw) if isinstance(raw, str) else -1
     d.update(extra)
@@ -116,7 +117,7 @@ def _detail(ctx: AccessContext, result: str, code: str | None, actual: str | Non
 
 
 def _row(ctx: AccessContext, run_id: int | None, function: str, allowed_: bool, detail: dict) -> dict:
-    return dict(r=run_id, role=bounded(ctx.role, ROLES), stage=bounded(ctx.stage, STAGES),
+    return dict(r=run_id, role=bounded(ctx.role, ALL_ROLES), stage=bounded(ctx.stage, STAGES),
                 field=bounded(function, FUNCTIONS), allowed=allowed_, detail=detail)
 
 
@@ -138,7 +139,7 @@ def log_failure(engine: Engine, ctx: AccessContext, function: str, code: str, ru
 def keep_in_process_log(ctx: AccessContext, function: str, code: str, original: BaseException | None) -> None:
     """The original error of an access failure, with its traceback, in the process log only.
     It may hold values a role must not see, so it never travels with the error raised."""
-    LOG.error(json.dumps({"access_failure": {"run": ctx.run_id, "role": bounded(ctx.role, ROLES),
+    LOG.error(json.dumps({"access_failure": {"run": ctx.run_id, "role": bounded(ctx.role, ALL_ROLES),
                                              "function": bounded(function, FUNCTIONS), "code": code}},
                          sort_keys=True),
               exc_info=(type(original), original, original.__traceback__) if original is not None else None)
@@ -174,7 +175,7 @@ class Access:
 
     def __repr__(self) -> str:
         c = self._context
-        return f"Access(run={c.run_id}, role={bounded(c.role, ROLES)!r}, stage={bounded(c.stage, STAGES)!r})"
+        return f"Access(run={c.run_id}, role={bounded(c.role, ALL_ROLES)!r}, stage={bounded(c.stage, STAGES)!r})"
 
     def get(self, field: str) -> Any:
         """One field, or AccessDenied / AccessFailed (already logged)."""
@@ -205,14 +206,14 @@ class Access:
             # the original, which stays in the process log only (re-check, finding 5).
             field, code, extra = failure
             log_failure(engine, ctx, field, code, **extra)
-            raise AccessFailed(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), field, code)
+            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), field, code)
         kind = outcome[0]
         if kind == "unknown_run":
             log_failure(engine, ctx, name, "unknown_run", run_known=False)
-            raise AccessFailed(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), name, "unknown_run")
+            raise AccessFailed(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), name, "unknown_run")
         if kind == "denied":
             field, code = outcome[1]
-            raise AccessDenied(bounded(ctx.role, ROLES), bounded(ctx.stage, STAGES), bounded(field, FUNCTIONS),
+            raise AccessDenied(bounded(ctx.role, ALL_ROLES), bounded(ctx.stage, STAGES), bounded(field, FUNCTIONS),
                                code, DENIALS[code])
         return outcome[1]
 
@@ -223,7 +224,7 @@ class Access:
         status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=ctx.run_id)).scalar_one()
         actual = actual_stage(conn, ctx.run_id, status)
         if not fields:  # role_input with nothing on the list: never an empty input
-            code = ("unknown_role" if ctx.role not in ROLES else "unknown_stage" if ctx.stage not in STAGES
+            code = ("unknown_role" if ctx.role not in ALL_ROLES else "unknown_stage" if ctx.stage not in STAGES
                     else "empty_list")
             conn.execute(_AUDIT, _row(ctx, ctx.run_id, "role_input", False, _detail(ctx, "denied", code, actual)))
             return ("denied", ("role_input", code))
@@ -253,7 +254,7 @@ class Access:
 
 
 def _policy(ctx: AccessContext, field: str, actual: str) -> str | None:
-    if ctx.role not in ROLES:
+    if ctx.role not in ALL_ROLES:
         return "unknown_role"
     if ctx.stage not in STAGES:
         return "unknown_stage"
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index f50af03..ffeb18e 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -57,17 +57,32 @@ def unrecognized_counts(values: Iterable[tuple[str, Any]]) -> dict[str, int]:
 
 FLAG_KINDS = frozenset({"exact_duplicate", "possible_duplicate", "values_disagree", "out_of_scope",
                         "scope_not_confirmed", "invalid_value", "model_recalled"})
+# Step 6 additions (owner, 2026-10-05): the category "several candidates" (an ambiguous match
+# group), the rules "missing_value", "identity_unresolved" and "conflict_unresolved", and the
+# sensitivity keys "no_exclusions" and "conflicts_survivor_value".
 FLAG_CATEGORIES = frozenset({"identical values", "differ beyond tolerance", "within tolerance",
-                             "outside scope", "scope not confirmed", "physically impossible"})
+                             "outside scope", "scope not confirmed", "physically impossible",
+                             "several candidates"})
 ELIGIBILITY_RULES = frozenset({"in_scope", "out_of_scope", "scope_not_confirmed", "invalid_value",
                                "duplicate_counted_once", "model_recalled", "single_grain_size",
-                               "excluded_by_rule"})
+                               "excluded_by_rule", "missing_value", "identity_unresolved",
+                               "conflict_unresolved"})
 SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                               "source_only_assignments", "possible_duplicates_separate",
-                              "scope_not_confirmed_included", "removal_after_lock"})
+                              "scope_not_confirmed_included", "removal_after_lock", "no_exclusions",
+                              "conflicts_survivor_value"})
 ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS
 
 
+# Codes in the locked plan's rules (step 6): the registered sources, grouping units, value
+# statuses, domain profiles, and whether single phase is required.
+SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates"})
+GROUPING_UNITS = frozenset({"paper", "dataset", "batch"})
+VALUE_STATUSES = frozenset({"converted", "assigned_from_source", "assigned_by_decision"})
+PROFILE_NAMES = frozenset({"grain_size_strengthening"})
+SINGLE_PHASE = frozenset({"required", "not_required"})
+
+
 def code(value: Any, vocabulary: frozenset[str]) -> str:
     return value if isinstance(value, str) and value in vocabulary else UNRECOGNIZED
 
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 436e205..1063d67 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -49,7 +49,8 @@ def _sources(args, engine) -> int:
                 print(f"{r.key}: {state}; version {r.version_id} ({r.label}); fingerprint {r.fingerprint}")
             return 0
         report = test_connection(engine, args.key, args.n)
-        # Assigned values carry status "assigned" and their citation in this output.
+        # Assigned values carry status "assigned_from_source" or "assigned_by_decision" and their
+        # citation in this output.
         print(json.dumps(report.to_json(), indent=2, ensure_ascii=False))
         return 0
     except (RegistrationError, UnsealedVersion, AdapterError) as error:
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 7a2e6e5..764f86d 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -541,8 +541,15 @@ class Record(Base):
     reported: Mapped[dict] = mapped_column(JSONB)
     paper_reference: Mapped[str | None] = mapped_column(Text)
     paper_doi: Mapped[str | None] = mapped_column(Text)
+    # How the record was extracted (migration 0003, step 6): {"method": "adapter" | "agent",
+    # "name", "version"}. Required for every new record by the insert trigger.
+    extraction: Mapped[dict | None] = mapped_column(JSONB)
     created_at: Mapped[datetime] = created()
     __table_args__ = (
+        CheckConstraint("extraction IS NULL OR (jsonb_typeof(extraction) = 'object' "
+                        "AND (extraction->>'method') IN ('adapter', 'agent') "
+                        "AND length(coalesce(extraction->>'name', '')) > 0 "
+                        "AND length(coalesce(extraction->>'version', '')) > 0)", name="extraction_shape"),
         UniqueConstraint("extraction_run_id", "source_version_id", "source_item_key", "item_index",
                          name="uq_record_origin_per_run"),
         Index("ix_record_source_version_id_source_item_key", "source_version_id", "source_item_key"),
diff --git a/hypocurate/sources/adapters/__init__.py b/hypocurate/sources/adapters/__init__.py
index 6fdcf3e..217b4f7 100644
--- a/hypocurate/sources/adapters/__init__.py
+++ b/hypocurate/sources/adapters/__init__.py
@@ -18,6 +18,22 @@ ADAPTERS: Mapping[str, Callable[[SealedVersion], AdapterResult]] = MappingProxyT
 })
 
 
+# How a record was extracted (stored in record.extraction, step 6): by adapter code, with the
+# adapter's name and version, so records extracted by code can always be told apart from
+# records an agent extracts later (owner, 2026-10-05).
+ADAPTER_IDENTITY: Mapping[str, tuple[str, str]] = MappingProxyType({
+    "mpea": ("mpea_layout", mpea_layout.ADAPTER_VERSION),
+    "controlled_duplicates": ("mpea_layout", mpea_layout.ADAPTER_VERSION),
+    "tamu_fcc": ("tamu_fcc", tamu_fcc.ADAPTER_VERSION),
+})
+
+
+def extraction(source_key: str) -> dict:
+    """The `record.extraction` value for a record this source's adapter extracted."""
+    name, version = ADAPTER_IDENTITY[source_key]
+    return {"method": "adapter", "name": name, "version": version}
+
+
 def read(version: SealedVersion) -> AdapterResult:
     """Reads a sealed version with its source's adapter."""
     adapter = ADAPTERS.get(version.source_key)
diff --git a/hypocurate/sources/adapters/mpea_layout.py b/hypocurate/sources/adapters/mpea_layout.py
index 7b4974a..28af199 100644
--- a/hypocurate/sources/adapters/mpea_layout.py
+++ b/hypocurate/sources/adapters/mpea_layout.py
@@ -51,6 +51,10 @@ UNITS = {
     "PROPERTY: C content (wppm)": "wppm",
 }
 
+# The adapter's version, stored with every record it extracts (record.extraction; step 6).
+# Raise it whenever what the adapter returns for the same file changes.
+ADAPTER_VERSION = "1"
+
 TEST_TYPE_CODES = {"T": "tension", "C": "compression"}
 
 NO_COLUMN = "the source has no column for this field"
diff --git a/hypocurate/sources/adapters/tamu_fcc.py b/hypocurate/sources/adapters/tamu_fcc.py
index 30b2f5b..6b61db9 100644
--- a/hypocurate/sources/adapters/tamu_fcc.py
+++ b/hypocurate/sources/adapters/tamu_fcc.py
@@ -16,11 +16,15 @@ spreadsheet, the source of record (step 1).
   batch (`Iteration`, six values) is kept as reported. **The grouping unit is an open
   decision for the owner (PRD 17, decision 9):** one group in sprint 1; batches only if
   the owner agrees they are independent enough. This adapter refuses any other unit.
-- Values not in the file are set only where the source's own documentation states them,
-  as `assigned` with the exact passage (owner, 2026-10-05, step 4 question 3):
-  test type `tension`, phase class `FCC`. **Test temperature is not assigned**: the
-  repository states no test temperature for these measurements (step 4 summary), so the
-  temperature and its band are `not_reported`, and the owner decides later.
+- Values not in the file are set with one of two statuses (register entry
+  'assigned_value_statuses'), each with its citation:
+  - `assigned_from_source`, where the source's own documentation states them (owner,
+    2026-10-05, step 4 question 3): test type `tension`, phase class `FCC`;
+  - `assigned_by_decision`, where the source does not state them and the owner decided
+    (register entries 'tamu_test_temperature' and 'tamu_microstructure', 2026-10-05):
+    temperature band `room temperature`, microstructure `FCC` (single-phase).
+  The numeric test temperature stays `not_reported`: neither the source nor the decision
+  gives a number.
 """
 from __future__ import annotations
 
@@ -35,6 +39,10 @@ from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterR
                                        CommonRecord, Group, Reported, Value)
 from hypocurate.sources.versions import SealedVersion
 
+# The adapter's version, stored with every record it extracts (record.extraction; step 6).
+# Raise it whenever what the adapter returns for the same file changes.
+ADAPTER_VERSION = "2"  # 2: the two assigned statuses; band and microstructure by decision (step 6)
+
 SHEET = "GS_MasterTable_Iterations "  # verbatim: the sheet name ends with a space
 HEADER = (
     "Iteration", "Alloy Name", "Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V", "Hardness, HV", "SD, HV",
@@ -67,8 +75,20 @@ COMPOSITION_UNIT_CITATION = Citation(
     "Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider "
     "interval.")
 
+# Decisions recorded in the assumptions register (status `assigned_by_decision`). The quote is
+# the entry's statement; tests check it against the register.
+REGISTER = "hypocurate/assumptions.json"
+TEMPERATURE_DECISION = Citation(
+    REGISTER, "entry 'tamu_test_temperature' (decided by the owner, Khalid El-Awady, 2026-10-05)",
+    "The Texas A&M records are treated as tested at room temperature. The value is 'assigned by decision': "
+    "the source does not report it and does not state it explicitly.")
+MICROSTRUCTURE_DECISION = Citation(
+    REGISTER, "entry 'tamu_microstructure' (decided by the owner, Khalid El-Awady, 2026-10-05)",
+    "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source "
+    "does not state it explicitly as a result.")
+
 TEMPERATURE_NOT_REPORTED = ("no per-record temperature; the source states no test temperature for its "
-                            "own measurements (owner decides; step 4 summary)")
+                            "own measurements (the room-temperature band is assigned by decision)")
 NO_COLUMN = "the source has no column for this field"
 
 
@@ -123,12 +143,12 @@ def _harmonize(cells: dict) -> tuple[dict[str, Value], str | None]:
     h["cold_work"] = _number(cells["Cold Work (%Reduction)"], "% reduction")
     h["recrystallization_temperature"] = _number(cells["Recrystallization Temp(℃)"], "°C")
     h["holding_time"] = _number(cells["Holding time (h)"], "h")
-    h["test_type"] = Value("tension", None, "assigned", citation=TEST_TYPE_CITATION)
-    h["phase_class"] = Value("FCC", None, "assigned", citation=PHASE_CITATION)
+    h["test_type"] = Value("tension", None, "assigned_from_source", citation=TEST_TYPE_CITATION)
+    h["phase_class"] = Value("FCC", None, "assigned_from_source", citation=PHASE_CITATION)
     h["test_temperature"] = Value(None, "°C", "not_reported", TEMPERATURE_NOT_REPORTED)
-    h["test_temperature_band"] = Value(None, None, "not_reported", TEMPERATURE_NOT_REPORTED)
-    h["microstructure"] = Value(None, None, "not_reported",
-                                "the source does not state the phases present per record")
+    h["test_temperature_band"] = Value("room temperature", None, "assigned_by_decision",
+                                       citation=TEMPERATURE_DECISION)
+    h["microstructure"] = Value("FCC", None, "assigned_by_decision", citation=MICROSTRUCTURE_DECISION)
     h["processing_method"] = Value(None, None, "not_reported",
                                    "the source gives processing parameters (cold work, recrystallization "
                                    "temperature, holding time), not a processing-method category")
diff --git a/hypocurate/sources/connection.py b/hypocurate/sources/connection.py
index 50571dc..32c46b2 100644
--- a/hypocurate/sources/connection.py
+++ b/hypocurate/sources/connection.py
@@ -16,7 +16,7 @@ from sqlalchemy import Engine, text
 
 from hypocurate.access import vocabulary
 from hypocurate.sources import adapters
-from hypocurate.sources.record import CommonRecord
+from hypocurate.sources.record import VALUE_STATUSES, CommonRecord
 from hypocurate.sources.versions import latest_sealed_version_id, load_sealed_version
 
 
@@ -52,7 +52,7 @@ def test_connection(engine: Engine, key: str, n: int = 5) -> ConnectionReport:
     counts = Counter(v.status for r in result.records for v in r.harmonized.values())
     unrecognized = vocabulary.unrecognized_counts(
         (f, r.harmonized[f].value) for r in result.records for f in vocabulary.CATEGORY_FIELDS
-        if r.harmonized[f].status in ("converted", "assigned"))
+        if r.harmonized[f].status in VALUE_STATUSES)
     return ConnectionReport(key, version.id, version.label, version.fingerprint, len(result.records),
                             len(result.blank_rows), dict(sorted(counts.items())), result.records[:n], unrecognized)
 
diff --git a/hypocurate/sources/normalize.py b/hypocurate/sources/normalize.py
index 6aa586c..9b5b9aa 100644
--- a/hypocurate/sources/normalize.py
+++ b/hypocurate/sources/normalize.py
@@ -8,6 +8,7 @@ the job of the code checks under the locked plan (step 6).
 """
 from __future__ import annotations
 
+import hashlib
 import math
 import re
 
@@ -122,17 +123,18 @@ def alloy_label(composition: dict[str, float]) -> str:
 
 # The same-alloy rule (register entry 'same_alloy_rule', owner 2026-10-05): each element's
 # atomic percent rounded to this many decimals; two compositions are the same alloy when
-# their rounded compositions are identical. Used by the gap report's condition summaries
-# (step 5); the plan setting that applies it to analysis comes in step 6.
+# their rounded compositions are identical. The default the domain profile copies into each
+# plan (step 6); eligibility and duplicate matching use the locked plan's value. The gap
+# report's condition summaries (step 5) use this default.
 SAME_ALLOY_DECIMALS = 1
 
 
-def same_alloy_key(composition: dict[str, float]) -> str:
+def same_alloy_key(composition: dict[str, float], decimals: int = SAME_ALLOY_DECIMALS) -> str:
     """The same-alloy rule's key for a full-precision composition: elements in
-    alphabetical order, each with its rounded atomic percent. Equal keys mean the same
-    alloy under the rule; unlike `alloy_label`, the key is the rule itself."""
-    return " ".join(f"{e} {round(v, SAME_ALLOY_DECIMALS):.{SAME_ALLOY_DECIMALS}f}"
-                    for e, v in sorted(composition.items()))
+    alphabetical order, each with its atomic percent rounded to `decimals` (Python's round,
+    as in the reference script). Equal keys mean the same alloy under the rule; unlike
+    `alloy_label`, the key is the rule itself."""
+    return " ".join(f"{e} {round(v, decimals):.{decimals}f}" for e, v in sorted(composition.items()))
 
 
 _DOI_WRAPPER = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
@@ -153,3 +155,12 @@ def doi_group_key(doi: str) -> str | None:
         key = key[match.end():]
     key = key.strip().translate(_ASCII_UPPER)
     return f"doi:{key}" if key else None
+
+
+def identity_hash(key: str | None) -> str | None:
+    """A paper or batch identity as an opaque hash (step 6): equal keys give equal hashes, and
+    the text of the key (a DOI, a batch label as reported) is not carried along. Used where
+    code compares identities without receiving the text (Inclusion's `record_conditions`)."""
+    if key is None:
+        return None
+    return hashlib.sha256(key.encode("utf-8")).hexdigest()
diff --git a/hypocurate/sources/record.py b/hypocurate/sources/record.py
index 1f81dbc..26f6291 100644
--- a/hypocurate/sources/record.py
+++ b/hypocurate/sources/record.py
@@ -15,9 +15,13 @@ flags, duplicates or survivors: those are decided by code under the locked plan
 - `not_reported`: blank in the source, or the source has no such column (the reason says which);
 - `not_convertible`: present in the source but could not be converted; the reason says why,
   and the text as reported is kept in `reported`;
-- `assigned`: not in the data file, set by the adapter from the source's own documentation.
-  It always carries a `Citation` (file, location and the exact passage), so an assigned
-  value can never be mistaken for a reported one.
+- `assigned_from_source`: not in the data file, set by the adapter from an explicit
+  statement in the source's own documentation, quoted with file and location;
+- `assigned_by_decision`: not in the data file and not stated by the source, set from a
+  recorded owner or expert decision (register `hypocurate/assumptions.json`), citing it.
+Both always carry a `Citation`, so an assigned value can never be mistaken for a reported
+one, and the two stay distinguishable wherever they are stored or shown (register entry
+'assigned_value_statuses', owner 2026-10-05; split in step 6).
 """
 from __future__ import annotations
 
@@ -25,7 +29,10 @@ from dataclasses import dataclass, field
 from types import MappingProxyType
 from typing import Any, Mapping
 
-STATUSES = ("converted", "not_reported", "not_convertible", "assigned")
+STATUSES = ("converted", "not_reported", "not_convertible", "assigned_from_source", "assigned_by_decision")
+ASSIGNED_STATUSES = ("assigned_from_source", "assigned_by_decision")
+# The statuses that carry a value.
+VALUE_STATUSES = ("converted",) + ASSIGNED_STATUSES
 
 # The harmonized fields, the same for every adapter, with their units (None: no unit).
 # A source without a column for a field reports it as `not_reported`.
@@ -54,7 +61,8 @@ TEST_TYPES = ("tension", "compression")
 
 @dataclass(frozen=True)
 class Citation:
-    """Where an assigned value (or a unit not stated in the data file) comes from."""
+    """Where an assigned value (or a unit not stated in the data file) comes from: a passage
+    of the source's documentation, or a decision recorded in the assumptions register."""
     document: str  # e.g. "ArroyaveLab/2026-mulukutla-hall-petch@11390ee paper/main.tex"
     location: str  # e.g. "line 177"
     quote: str  # the exact passage
@@ -80,16 +88,16 @@ class Value:
     def __post_init__(self):
         if self.status not in STATUSES:
             raise ValueError(f"unknown status {self.status!r}")
-        if self.status in ("converted", "assigned") and self.value is None:
+        if self.status in VALUE_STATUSES and self.value is None:
             raise ValueError(f"a {self.status} value needs a value")
         if self.status in ("not_reported", "not_convertible"):
             if self.value is not None:
                 raise ValueError(f"a {self.status} value has no value")
             if not self.reason:
                 raise ValueError(f"a {self.status} value needs a reason")
-        if self.status == "assigned" and self.citation is None:
+        if self.status in ASSIGNED_STATUSES and self.citation is None:
             raise ValueError("an assigned value needs a citation")
-        if self.citation is not None and self.status not in ("assigned", "converted"):
+        if self.citation is not None and self.status not in VALUE_STATUSES:
             raise ValueError("only an assigned value, or a converted value whose unit is documented "
                              "outside the data file, carries a citation")
         if isinstance(self.value, dict):
diff --git a/hypocurate/sources/versions.py b/hypocurate/sources/versions.py
index bfd0861..0a353d1 100644
--- a/hypocurate/sources/versions.py
+++ b/hypocurate/sources/versions.py
@@ -98,6 +98,9 @@ class SourceDefinition:
     data_files: tuple[str, ...]  # file names inside `directory`, as stored
     version_label: str
     manifest_section: tuple[str, ...]  # where its files are listed in data/manifest.json
+    # Constructed test data (step 6): its records enter only a run marked as a test
+    # (run.experiment_flags constructed_test_data; register 'constructed_test_runs').
+    constructed: bool = False
 
 
 SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
@@ -127,10 +130,10 @@ SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
         source_type="uploaded_table", data_kind="measured", grouping_unit="paper",
         licence="Apache-2.0 (derived from the MPEA dataset)", address=None,
         properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
-        # Off by default: constructed data. A real guard against choosing it is step 6's.
+        # Off by default: constructed data. Its records enter only a run marked as a test (step 6).
         enabled=False, directory="controlled_duplicates", data_files=("extract.csv",),
         version_label="built 2026-10-04 from the MPEA dataset",
-        manifest_section=("controlled_duplicates",)),
+        manifest_section=("controlled_duplicates",), constructed=True),
 })
 
 
diff --git a/scripts/check_runtime_image.py b/scripts/check_runtime_image.py
index 6a5b4dd..654730d 100644
--- a/scripts/check_runtime_image.py
+++ b/scripts/check_runtime_image.py
@@ -33,7 +33,13 @@ REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.jso
             "hypocurate/access/allowlist.py", "hypocurate/access/layer.py", "hypocurate/access/fields.py",
             "hypocurate/access/stage.py", "hypocurate/access/inputs.py", "hypocurate/access/file_guard.py",
             "hypocurate/access/guarded.py", "hypocurate/access/guard_probe.py", "hypocurate/access/vocabulary.py",
-            "hypocurate/access/context.py", "hypocurate/access/dispatch.py"]
+            "hypocurate/access/context.py", "hypocurate/access/dispatch.py",
+            # Step 6: the tag lists, record extraction, and the plan, checkpoints, checks and inclusion.
+            "hypocurate/db/migrations/versions/0002_tag_starting_lists.py",
+            "hypocurate/db/migrations/versions/0003_record_extraction.py",
+            "hypocurate/pipeline/profile.py", "hypocurate/pipeline/plan.py", "hypocurate/pipeline/checkpoints.py",
+            "hypocurate/pipeline/extract.py", "hypocurate/pipeline/flags.py", "hypocurate/pipeline/checks.py",
+            "hypocurate/pipeline/eligibility.py", "hypocurate/pipeline/inclusion.py", "hypocurate/pipeline/writes.py"]
 FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
 FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")
```

## 8. The assumptions register (diff)

```diff
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 48dacbb..8ba5be8 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -27,9 +27,14 @@
     },
     "sensitivity": "The source-only analysis (reported values and values assigned from source only) shows the effect of this and every other decision-based assignment.",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Today the adapter reports the temperature as not reported (tamu_fcc.TEMPERATURE_NOT_REPORTED)."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.sources.adapters.tamu_fcc:TEMPERATURE_DECISION.quote",
+          "equals": "The Texas A&M records are treated as tested at room temperature. The value is 'assigned by decision': the source does not report it and does not state it explicitly."
+        }
+      ],
+      "note": "The band 'room temperature' with status 'assigned_by_decision'; the numeric temperature stays not reported."
     },
     "history": [
       {
@@ -42,7 +47,13 @@
     "notes": [
       "Uses the status 'assigned by decision' (see entry 'assigned_value_statuses')."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
+      "tests/test_adapter_tamu.py::test_decision_citations_quote_the_register",
+      "tests/test_adapter_tamu.py::test_temperature_is_not_reported_and_the_band_is_assigned_by_decision",
+      "tests/test_eligibility.py::test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
+    ]
   },
   {
     "key": "permitted_test_types",
@@ -70,9 +81,16 @@
     },
     "sensitivity": "Tension and compression together.",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": null
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:PERMITTED_TEST_TYPES",
+          "equals": [
+            "tension"
+          ]
+        }
+      ],
+      "note": "The plan's scope.test_type; MPEA row 139 is out of scope in the primary set and enters 'tension_and_compression'."
     },
     "history": [
       {
@@ -85,7 +103,12 @@
     "notes": [
       "This removes MPEA_dataset.csv:row:139 (a compression test) from the primary analysis, so the reference numbers (77 / 98 records, k = 427 and 428) must be recomputed before step 7."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_controlled_duplicates_handling.py::test_rows_15_and_16_enter_together_when_compression_is_permitted",
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
+    ]
   },
   {
     "key": "tamu_grouping_unit",
@@ -118,10 +141,14 @@
         {
           "ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit",
           "equals": "dataset"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:GROUPING.tamu_fcc",
+          "equals": "dataset"
         }
       ],
-      "done": "The adapter gives every record one group (the dataset) and refuses any other grouping unit.",
-      "pending": "Using the groups in inference (step 7) and the six-batch sensitivity analysis.",
+      "done": "The adapter gives every record one group (the dataset) and refuses any other grouping unit; the plan states the grouping per source, and the sensitivity set 'six_batches_as_groups' groups the Texas A&M records by batch (step 6).",
+      "pending": "Using the groups in inference (step 7).",
       "step": 7,
       "note": null
     },
@@ -133,10 +160,14 @@
         "note": "PRD 17, decision 9."
       }
     ],
-    "notes": [],
+    "notes": [
+      "The 21 eligible records come from three of the six batches (CBA, CBB, CBC), so the six-batch analysis has three Texas A&M groups (step 6)."
+    ],
     "tests": [
       "tests/test_adapter_tamu.py::test_one_group_the_dataset",
-      "tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides"
+      "tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides",
+      "tests/test_eligibility.py::test_grouping_is_read_from_the_locked_plan",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
   },
   {
@@ -166,16 +197,17 @@
     },
     "sensitivity": "The same rule with a rounding step of 1 at.%.",
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.normalize:SAME_ALLOY_DECIMALS",
           "equals": 1
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:SAME_ALLOY_DECIMALS_DEFAULT",
+          "equals": 1
         }
       ],
-      "done": "The gap report's condition summaries group records by alloy under this rule (normalize.same_alloy_key, step 5).",
-      "pending": "The plan setting that applies it to the analysis, eligibility and duplicate matching.",
-      "step": 6,
       "note": "The adapters give the full-precision composition; the display label (normalize.alloy_label) is not this rule."
     },
     "history": [
@@ -189,11 +221,14 @@
     "notes": [
       "Known weakness: compositions closer than the step can fall into different bins at a boundary.",
       "Ties follow the reference script's rounding (Python round on the computed percentage) unless step 6 states otherwise.",
-      "Possible improvement for step 6, not a decision: a tolerance-based grouping, which would need a stated rule for chains and the owner's approval."
+      "Applied in step 6 from the locked plan (rules.same_alloy_decimals) to the grain-size rule, the counts and duplicate matching."
     ],
     "tests": [
       "tests/test_access_layer.py::test_condition_summaries_are_ranges_and_counts_of_conditions_only",
-      "tests/test_access_layer.py::test_condition_summaries_group_alloys_by_the_same_alloy_rule"
+      "tests/test_access_layer.py::test_condition_summaries_group_alloys_by_the_same_alloy_rule",
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_flags.py::test_the_same_alloy_rule_of_the_plan_decides_which_records_are_compared",
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change"
     ]
   },
   {
@@ -224,13 +259,22 @@
     "applied": {
       "status": "partly",
       "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:FIXED_MINIMUMS",
+          "equals": {
+            "min_records": 30,
+            "min_alloys": 5,
+            "min_groups": 10,
+            "min_resid_df": 10
+          }
+        },
         {
           "ref": "sql:hc_run_update"
         }
       ],
-      "done": "Each plan stores its four minimums, and the database checks that 'minimums met' agrees with them and that a sufficient outcome under the fixed minimum has them met.",
-      "pending": "These values as the plan's defaults (step 6) and the check computed by code (step 7).",
-      "step": 6,
+      "done": "The four minimums are each plan's default (step 6); the database checks that 'minimums met' agrees with them; the freeze records the counts and whether they are met, as information.",
+      "pending": "The fixed-minimum check that decides the outcome, computed by code (step 7).",
+      "step": 7,
       "note": null
     },
     "history": [
@@ -243,15 +287,18 @@
     ],
     "notes": [],
     "tests": [
+      "tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met",
       "tests/test_data_model.py::test_minimums_met_must_agree_with_the_plan",
-      "tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met"
+      "tests/test_eligibility.py::test_counts_known_at_the_freeze",
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
   },
   {
     "key": "values_disagree_tolerance",
     "name": "When values disagree",
     "state": "in_force",
-    "statement": "Two values that should be the same measurement raise a conflict flag when their relative difference |a - b| / min(|a|, |b|) is above 2%. Applies to yield strength and grain size.",
+    "statement": "Relative difference = |a - b| / min(|a|, |b|), with a tolerance of 2%. For grain size it is a matching tolerance: two records are compared only if their grain sizes are within it. For yield strength it is the duplicate-or-conflict threshold: within it two compared records are duplicates, beyond it a conflict flag is raised.",
     "value": {
       "text": "2% relative difference, relative to the smaller value",
       "unit": "%"
@@ -273,9 +320,14 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": null
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:DUPLICATE_TOLERANCE",
+          "equals": 0.02
+        }
+      ],
+      "note": "Read from the locked plan (rules.duplicate_tolerance)."
     },
     "history": [
       {
@@ -283,18 +335,29 @@
         "from": "2026-10-04",
         "to": "2026-10-05",
         "note": "PRD 17, decision 4."
+      },
+      {
+        "value": "Two values that should be the same measurement raise a conflict flag when their relative difference |a - b| / min(|a|, |b|) is above 2%. Applies to yield strength and grain size.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 4b wording; reworded at the owner's step 6 decision (2026-10-05)."
       }
     ],
     "notes": [
-      "Which records are compared is decided by entry 'conflict_pairing_rule' (owner, 2026-10-05): different sources, same paper, alloy, grain size and test conditions."
+      "Which records are compared is decided by entry 'conflict_pairing_rule' (owner, 2026-10-05): different sources, same paper, alloy, grain size and test conditions.",
+      "Known limit (owner, 2026-10-05): grain size is a matching criterion, not something that can be in conflict. Two records whose grain sizes differ by more than 2% are separate measurements, so a grain-size disagreement between sources can never raise a conflict flag."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_flags.py::test_exact_duplicate_and_the_tolerance_on_yield_strength",
+      "tests/test_flags.py::test_grain_size_is_a_matching_tolerance_never_a_conflict",
+      "tests/test_flags.py::test_the_tolerance_is_read_from_the_plan"
+    ]
   },
   {
     "key": "conflict_pairing_rule",
     "name": "Which records are compared for a conflict",
     "state": "in_force",
-    "statement": "Duplicates and conflicts are looked for only between records from different sources that cite the same paper with the same alloy, grain size and test conditions. Rows within one source are always separate measurements (repeat specimens).",
+    "statement": "Duplicates and conflicts are looked for only between records from different sources; rows within one source are always separate measurements (repeat specimens). Two records are compared when they have the same alloy, grain sizes within the tolerance, and nothing known that differs. Same paper and every test condition known: an exact duplicate (yield strengths within the tolerance) or a conflict (beyond it). The paper or a test condition missing on one side and the values within the tolerance: a possible duplicate. If a record has more than one candidate in another source, or the candidates are not all linked to each other, nothing is paired automatically and all of them are flagged as possible duplicates ('several candidates').",
     "value": {
       "text": "different sources citing the same paper, with the same alloy, grain size and test conditions; rows within one source are separate measurements",
       "unit": null
@@ -319,23 +382,48 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.flags:duplicate_groups"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:DUPLICATE_TOLERANCE",
+          "equals": 0.02
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_controlled_duplicates_handling.py::test_the_flag_is_the_answer_files",
+      "tests/test_flags.py::test_a_dataset_source_is_its_own_paper",
+      "tests/test_flags.py::test_a_group_whose_records_are_not_all_linked_is_ambiguous",
+      "tests/test_flags.py::test_a_group_with_one_conflicting_pair_is_a_conflict",
+      "tests/test_flags.py::test_a_known_difference_in_paper_or_conditions_means_no_pair",
+      "tests/test_flags.py::test_an_unknown_paper_or_condition_gives_a_possible_duplicate_only_if_the_values_match",
+      "tests/test_flags.py::test_rows_within_one_source_are_never_compared",
+      "tests/test_flags.py::test_several_candidates_from_one_source_pair_nothing"
+    ],
     "history": [
       {
         "value": "open decision: which pairs of records are compared for the 'values disagree' flag (repeat specimens versus conflicting reports)",
         "from": "2026-10-05",
         "to": "2026-10-05",
         "note": "Open entry added after the step 4b review, finding 4."
+      },
+      {
+        "value": "Duplicates and conflicts are looked for only between records from different sources that cite the same paper with the same alloy, grain size and test conditions. Rows within one source are always separate measurements (repeat specimens).",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 decision; the possible-duplicate case and the rule for several candidates added by the owner in step 6 planning (2026-10-05)."
       }
     ],
     "notes": [
       "Known weakness: a source that repeats its own row by mistake is not caught, because rows within one source are never compared.",
       "Not reviewed by an expert.",
-      "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance)."
+      "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance).",
+      "A record with a missing test condition is also 'scope not confirmed': Checks still raises the possible-duplicate flag, and Inclusion applies the scope rule before the duplicate rule (owner, 2026-10-05).",
+      "A paper is identified by its DOI (derived key); a source grouped by dataset (Texas A&M) cites itself."
     ]
   },
   {
@@ -413,9 +501,16 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": null
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:TAG_STARTING_LISTS"
+        },
+        {
+          "ref": "sql:TAG_STARTING_LISTS"
+        }
+      ],
+      "note": "Seeded as approved by migration 0002; each run gets one tag of each kind at the rules lock."
     },
     "history": [
       {
@@ -426,7 +521,13 @@
       }
     ],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_checkpoints.py::test_the_lock_stores_the_plan_its_fingerprint_and_three_tags_in_one_transaction",
+      "tests/test_migrations_step6.py::test_0002_changes_no_schema_and_seeds_19_approved_values",
+      "tests/test_migrations_step6.py::test_0002_is_safe_on_a_database_that_already_has_some_values",
+      "tests/test_migrations_step6.py::test_the_seeded_lists_are_the_registers_and_the_profiles",
+      "tests/test_plan.py::test_three_tags_one_per_kind_from_the_plan"
+    ]
   },
   {
     "key": "tamu_microstructure",
@@ -458,9 +559,14 @@
     },
     "sensitivity": "The source-only analysis (reported values and values assigned from source only) shows the result without these records.",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Today the adapter reports the microstructure as not reported and assigns phase class FCC from source."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.sources.adapters.tamu_fcc:MICROSTRUCTURE_DECISION.quote",
+          "equals": "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source does not state it explicitly as a result."
+        }
+      ],
+      "note": "Microstructure 'FCC' with status 'assigned_by_decision'."
     },
     "history": [
       {
@@ -476,7 +582,11 @@
       "Not reviewed by an expert.",
       "Uses the status 'assigned by decision' (see entry 'assigned_value_statuses')."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
+      "tests/test_adapter_tamu.py::test_decision_citations_quote_the_register",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
+    ]
   },
   {
     "key": "shared_coefficient",
@@ -836,13 +946,19 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "No code applies a rate rule; step 6 states the scope."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.access.allowlist:PLAN_SCHEMA.scope"
+        }
+      ],
+      "note": "The plan's scope has no loading-rate rule."
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions"
+    ]
   },
   {
     "key": "composition_as_reported",
@@ -892,7 +1008,7 @@
     "key": "room_temperature_scope",
     "name": "Room temperature",
     "state": "in_force",
-    "statement": "A room-temperature scope accepts reported test temperatures from 20 to 25 °C.",
+    "statement": "A room-temperature scope accepts a reported test temperature from 20 to 25 °C; a record with no reported temperature is accepted on the band 'room temperature' held with a status the plan accepts (the Texas A&M band is assigned by decision).",
     "value": {
       "text": "20 to 25",
       "unit": "°C"
@@ -904,8 +1020,8 @@
       "docs/reference/worked_example.py: d['T'].between(20, 25)."
     ],
     "decided": {
-      "by": "reference script and PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -914,15 +1030,35 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Used on the test side only (tests/test_reference_counts_from_adapters.py)."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:ROOM_TEMPERATURE_C",
+          "equals": [
+            20.0,
+            25.0
+          ]
+        }
+      ],
+      "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "A room-temperature scope accepts reported test temperatures from 20 to 25 °C.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 4b wording; the band rule added in step 6 (owner's requirement: the scope accepts the assigned band)."
+      }
+    ],
     "notes": [
       "How a record with an assigned room-temperature band (decision 'tamu_test_temperature') passes this scope is defined in step 6."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_eligibility.py::test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
+    ]
   },
   {
     "key": "fcc_microstructure_scope",
@@ -950,15 +1086,30 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Used on the test side only."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:SINGLE_PHASE",
+          "equals": "required"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:PHASE_CLASSES",
+          "equals": [
+            "FCC"
+          ]
+        }
+      ],
+      "note": "Single phase: the microstructure exactly equals the scope's phase class; the phase column is not used."
     },
     "history": [],
     "notes": [
       "The Texas A&M records meet it by decision (entry 'tamu_microstructure')."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_reference_sets.py::test_the_primary_set_is_the_reference_selection_without_row_139"
+    ]
   },
   {
     "key": "mpea_microstructure_label_trusted",
@@ -1029,19 +1180,28 @@
     },
     "sensitivity": "No exclusions (the reference script's sensitivity analysis).",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Used on the test side only."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:GRAIN_SIZE_FLOOR_UM",
+          "equals": 0.1
+        }
+      ],
+      "note": "An exclusion rule from the menu (grain_size_range, min 0.1) in the locked plan."
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_excluded_and_identity_come_before_the_grain_size_count",
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change"
+    ]
   },
   {
     "key": "alloy_eligibility",
     "name": "Alloys with two or more grain sizes",
     "state": "in_force",
-    "statement": "Only alloys measured at two or more distinct grain sizes within the plan's scope enter a test. Others are kept and marked not eligible.",
+    "statement": "Only alloys measured at two or more distinct grain sizes within the plan's scope enter a test. The grain sizes are counted among the records that survive duplicate resolution. Others are kept and marked not eligible.",
     "value": {
       "text": "at least 2 distinct grain sizes",
       "unit": null
@@ -1053,8 +1213,8 @@
       "PRD 5.7 ('Which alloys can be used'); CLAUDE.md, rule 6."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1063,21 +1223,37 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:MIN_GRAIN_SIZES_PER_ALLOY",
+          "equals": 2
+        }
+      ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Only alloys measured at two or more distinct grain sizes within the plan's scope enter a test. Others are kept and marked not eligible.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 4b wording; 'counted after duplicate resolution' added by the owner (2026-10-05)."
+      }
+    ],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_duplicates_are_resolved_before_grain_sizes_are_counted",
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule"
+    ]
   },
   {
     "key": "physical_validity_checks",
     "name": "Physical validity checks",
     "state": "in_force",
-    "statement": "A physically impossible value (for example tensile strength below yield strength, or a negative grain size) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
+    "statement": "A physically impossible value (tensile strength below yield strength, or a grain size of zero or less) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
     "value": {
-      "text": "UTS < YS or grain size < 0: invalid",
+      "text": "UTS < YS or grain size <= 0: invalid",
       "unit": null
     },
     "category": "scientific",
@@ -1087,8 +1263,8 @@
       "PRD 5.3."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -1097,13 +1273,28 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "The adapters convert such values unchanged; they do not judge them."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.flags:invalid_values"
+        }
+      ],
+      "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "UTS < YS or grain size < 0: invalid | A physically impossible value (for example tensile strength below yield strength, or a negative grain size) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 4b wording ('a negative grain size'); zero added in step 6, since the model needs a positive grain size."
+      }
+    ],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_flags.py::test_flags_use_only_pairwise_and_per_record_rules",
+      "tests/test_flags.py::test_physically_impossible_values_are_flagged_per_record"
+    ]
   },
   {
     "key": "tamu_test_type",
@@ -1590,7 +1781,7 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "sql:ck_plan_sufficiency_option"
@@ -1600,19 +1791,21 @@
         },
         {
           "ref": "sql:hc_run_update"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:SUFFICIENCY_OPTION",
+          "equals": "fixed_minimum"
         }
       ],
-      "done": "The database allows only the two options and enforces the 'exploratory' rule.",
-      "pending": "The fixed minimum as each plan's default.",
-      "step": 6,
       "note": null
     },
     "history": [],
     "notes": [],
     "tests": [
-      "tests/test_data_model.py::test_sufficiency_option_and_minimums",
       "tests/test_data_model.py::test_exploratory_means_use_available_and_minimums_not_met",
-      "tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met"
+      "tests/test_data_model.py::test_fixed_minimum_sufficient_needs_the_minimums_met",
+      "tests/test_data_model.py::test_sufficiency_option_and_minimums",
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions"
     ]
   },
   {
@@ -1983,11 +2176,17 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.extract:store_source"
+        }
+      ],
       "note": null
     },
-    "tests": [],
+    "tests": [
+      "tests/test_checkpoints.py::test_records_are_stored_only_after_the_lock_with_how_they_were_extracted"
+    ],
     "history": [],
     "notes": [
       "Connects to entry 'conflict_pairing_rule' (decided 2026-10-05): rows within one source are always separate measurements."
@@ -1997,7 +2196,7 @@
     "key": "duplicate_identity",
     "name": "When two records are the same measurement",
     "state": "in_force",
-    "statement": "Two records are duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions. Matching alloy and grain size alone is not enough.",
+    "statement": "Two records are duplicates only if they come from different sources, cite the same original paper and match on alloy (the same-alloy rule), grain size and yield strength (each within the tolerance) and test conditions. Matching alloy and grain size alone is not enough.",
     "value": {
       "text": "same paper, alloy, grain size, value and conditions",
       "unit": null
@@ -2009,8 +2208,8 @@
       "PRD 5.3."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -2019,13 +2218,28 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": "Alloy under the rule 'same_alloy_rule'; paper under 'paper_grouping_by_doi'."
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.flags:duplicate_groups"
+        }
+      ],
+      "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Two records are duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions. Matching alloy and grain size alone is not enough.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 4b wording; 'different sources' and the tolerances added in step 6 (owner, 2026-10-05)."
+      }
+    ],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_controlled_duplicates_handling.py::test_the_flag_is_the_answer_files",
+      "tests/test_flags.py::test_a_known_difference_in_paper_or_conditions_means_no_pair",
+      "tests/test_flags.py::test_exact_duplicate_and_the_tolerance_on_yield_strength"
+    ]
   },
   {
     "key": "duplicate_survivor_rule",
@@ -2053,9 +2267,18 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "not_yet",
-      "step": 6,
-      "note": null
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.profile:SURVIVOR_SOURCE_ORDER",
+          "equals": [
+            "mpea",
+            "tamu_fcc",
+            "controlled_duplicates"
+          ]
+        }
+      ],
+      "note": "Read from the locked plan (rules.survivor_source_order)."
     },
     "history": [
       {
@@ -2067,15 +2290,21 @@
     ],
     "notes": [
       "A DOI identifies the cited paper, not where a record was extracted: a compilation and a copied extract can both carry it. Preferring records extracted directly from the original paper would need explicit extraction-origin metadata, which does not exist.",
-      "The step 1 answer file and fixtures README still carry the withdrawn wording (their fingerprints are pinned); to be aligned with the owner's approval when step 6 builds duplicate handling."
+      "The step 1 answer file, its builder and README carry this wording since step 6 (owner's approval, 2026-10-05).",
+      "Rule 1 can only decide a possible duplicate: paired records otherwise cite the same paper."
     ],
-    "tests": []
+    "tests": [
+      "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
+      "tests/test_eligibility.py::test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi",
+      "tests/test_eligibility.py::test_survivor_rule_three_the_lowest_row_within_one_source",
+      "tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order"
+    ]
   },
   {
     "key": "unresolved_duplicates",
     "name": "Possible duplicates that cannot be resolved",
     "state": "in_force",
-    "statement": "A possible duplicate that cannot be resolved is kept, counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis.",
+    "statement": "A possible duplicate is kept and counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis. When identity cannot be resolved (several candidates), none of the group's records enters the primary analysis; all of them enter the same sensitivity analysis.",
     "value": {
       "text": "counted once",
       "unit": null
@@ -2087,8 +2316,8 @@
       "PRD 5.3."
     ],
     "decided": {
-      "by": "PRD v1.6 (owner)",
-      "date": "2026-10-04"
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-05"
     },
     "expert_review": {
       "status": "not_reviewed",
@@ -2097,13 +2326,28 @@
     },
     "sensitivity": "Both counted separately.",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:decide"
+        }
+      ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "A possible duplicate that cannot be resolved is kept, counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis.",
+        "from": "2026-10-04",
+        "to": "2026-10-05",
+        "note": "Step 4b wording; the ambiguous group added by the owner (2026-10-05, decision C)."
+      }
+    ],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files",
+      "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
+      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule"
+    ]
   },
   {
     "key": "scope_not_confirmed",
@@ -2131,13 +2375,21 @@
     },
     "sensitivity": "Included.",
     "applied": {
-      "status": "not_yet",
-      "step": 6,
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:scope"
+        }
+      ],
       "note": null
     },
     "history": [],
     "notes": [],
-    "tests": []
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_identity_applies_only_among_records_that_passed_the_earlier_rules",
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change"
+    ]
   },
   {
     "key": "assigned_value_statuses",
@@ -2165,7 +2417,7 @@
     },
     "sensitivity": "The reference plan names a sensitivity analysis that accepts only reported values and values assigned from source, so the effect of every decision-based assignment is visible.",
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.record:STATUSES",
@@ -2173,14 +2425,20 @@
             "converted",
             "not_reported",
             "not_convertible",
-            "assigned"
+            "assigned_from_source",
+            "assigned_by_decision"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.pipeline.profile:ACCEPTED_VALUE_STATUSES",
+          "equals": [
+            "converted",
+            "assigned_from_source",
+            "assigned_by_decision"
           ]
         }
       ],
-      "done": "One status 'assigned', which needs a citation and is used only for statements in the source (that is, 'assigned from source').",
-      "pending": "The two statuses 'assigned from source' and 'assigned by decision', and the source-only sensitivity analysis.",
-      "step": 6,
-      "note": null
+      "note": "The source-only sensitivity analysis ('source_only_assignments') accepts converted values and values assigned from source."
     },
     "history": [
       {
@@ -2192,8 +2450,10 @@
     ],
     "notes": [],
     "tests": [
+      "tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable",
       "tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage",
-      "tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable"
+      "tests/test_eligibility.py::test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
     ]
   },
   {
@@ -2230,7 +2490,8 @@
             "converted",
             "not_reported",
             "not_convertible",
-            "assigned"
+            "assigned_from_source",
+            "assigned_by_decision"
           ]
         }
       ],
@@ -2415,8 +2676,8 @@
         }
       ],
       "done": "Records carry grain size in µm only.",
-      "pending": "The transformation the locked plan names, applied when the analysis dataset is built.",
-      "step": 6,
+      "pending": "The transformation the locked plan names (variables.predictor.transformation), applied when the analysis data are built (step 7).",
+      "step": 7,
       "note": null
     },
     "history": [],
@@ -2451,21 +2712,24 @@
     },
     "sensitivity": null,
     "applied": {
-      "status": "partly",
+      "status": "yes",
       "settings": [
         {
           "ref": "python:hypocurate.sources.versions:SOURCES.controlled_duplicates.enabled",
           "equals": false
+        },
+        {
+          "ref": "python:hypocurate.sources.versions:SOURCES.controlled_duplicates.constructed",
+          "equals": true
         }
       ],
-      "done": "The extract is registered switched off (enabled = false).",
-      "pending": "A guard so that it cannot enter a real analysis; today no database rule prevents choosing a disabled source.",
-      "step": 6,
-      "note": null
+      "note": "The guard is in code at storage, inclusion and freeze; the database itself does not refuse it (see 'constructed_test_runs')."
     },
     "history": [],
     "notes": [],
     "tests": [
+      "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records",
+      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
       "tests/test_source_versions.py::test_registering_seals_every_source"
     ]
   },
@@ -3144,7 +3408,7 @@
     "key": "plan_named_parts",
     "name": "The plan's schema",
     "state": "in_force",
-    "statement": "A plan's content is read only through PLAN_SCHEMA, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped. Power assumptions likewise through POWER_SCHEMA, and the sensitivity keys through their vocabulary. Defined in step 5 (owner, 2026-10-05); the plan model of step 6 must follow it.",
+    "statement": "A plan's content follows PLAN_SCHEMA exactly and is read only through it, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped, and the plan model refuses content its projection would change. Since step 6 the schema holds every setting that affects which records are eligible or how they are grouped ('rules'), the domain profile and version the defaults came from ('profile'), and an optional flag category in each eligibility rule.",
     "value": {
       "text": "PLAN_SCHEMA (nested, named keys and vocabulary leaves)",
       "unit": null
@@ -3184,14 +3448,24 @@
         "from": "2026-10-05",
         "to": "2026-10-05",
         "note": "Step 5 first build; changed after the second-model review."
+      },
+      {
+        "value": "A plan's content is read only through PLAN_SCHEMA, recursively: named keys at every level, vocabulary values (else 'unrecognized'), numbers, integers, common field names and units; unknown keys, free text and values that do not fit are dropped. Power assumptions likewise through POWER_SCHEMA, and the sensitivity keys through their vocabulary. Defined in step 5 (owner, 2026-10-05); the plan model of step 6 must follow it.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5 wording; extended by the owner in step 6 planning (2026-10-05)."
       }
     ],
     "notes": [
       "Step 6 must store the plan's content in this schema; a change to the schema is a register change needing the owner's approval."
     ],
     "tests": [
+      "tests/test_access_layer.py::test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim",
       "tests/test_access_layer.py::test_the_plan_is_projected_by_its_named_parts",
-      "tests/test_access_layer.py::test_the_curator_reads_only_its_own_source_and_never_the_direction_of_the_claim"
+      "tests/test_eligibility.py::test_decisions_ignore_the_domain_profile",
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_plan.py::test_invalid_plans_are_refused",
+      "tests/test_plan.py::test_the_default_plan_is_valid_and_is_its_own_projection"
     ]
   },
   {
@@ -3548,7 +3822,7 @@
     "key": "audit_failure_rows_without_run_lock",
     "name": "Failure rows: a named exception to the locking protocol",
     "state": "in_force",
-    "statement": "Audit rows for access failures (unknown run, lock timeout, reader or database error, file-guard refusal) are written in their own short transaction without hc_write_lock: there is no run to lock, or the lock is what failed. An audit_log insert takes only a key-share lock on the run, which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an unknown run, run_id is NULL and the requested id is in the detail.",
+    "statement": "Audit rows for access failures (unknown run, lock timeout, reader or database error, file-guard refusal) are written in their own short transaction without hc_write_lock: there is no run to lock, or the lock is what failed. An audit_log insert takes only a key-share lock on the run, which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an unknown run, run_id is NULL and the requested id is in the detail. Since step 6 the same exception covers the refusals of the pipeline's write paths (rules lock, record storage, checks, inclusion, freeze): a refusal is logged in its own transaction before it is raised (owner, 2026-10-05).",
     "value": {
       "text": "failure rows without hc_write_lock",
       "unit": null
@@ -3578,13 +3852,22 @@
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Audit rows for access failures (unknown run, lock timeout, reader or database error, file-guard refusal) are written in their own short transaction without hc_write_lock: there is no run to lock, or the lock is what failed. An audit_log insert takes only a key-share lock on the run, which never conflicts with the protocol's lock, so it cannot wait on it or deadlock. For an unknown run, run_id is NULL and the requested id is in the detail.",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5."
+      }
+    ],
     "notes": [
       "Owner's answer to the fix-plan question 1, 2026-10-05: option (a)."
     ],
     "tests": [
+      "tests/test_access_dispatch.py::test_bind_logs_an_unknown_run_as_a_failure_with_no_run",
       "tests/test_access_layer.py::test_an_access_call_takes_the_run_lock_first_and_times_out_instead_of_hanging",
-      "tests/test_access_dispatch.py::test_bind_logs_an_unknown_run_as_a_failure_with_no_run"
+      "tests/test_checkpoints.py::test_a_second_lock_or_a_changed_plan_is_refused_and_logged",
+      "tests/test_checkpoints.py::test_after_the_freeze_every_write_is_refused_and_logged"
     ]
   },
   {
@@ -3682,9 +3965,9 @@
     "key": "code_vocabularies",
     "name": "Vocabularies of codes our own code writes",
     "state": "in_force",
-    "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 must write these codes. Adding one is a register change needing the owner's approval.",
+    "statement": "Flag kinds and categories, eligibility rule codes, analysis-set and sensitivity keys, and the codes in the locked plan's rules (source keys, grouping units, value statuses, profile names, single phase) reach blinded views only from fixed vocabularies, else 'unrecognized'. Steps 6 and 7 write these codes. Adding one is a register change needing the owner's approval.",
     "value": {
-      "text": "flag kinds, flag categories, eligibility rules, sensitivity keys",
+      "text": "flag kinds, flag categories, eligibility rules, sensitivity keys, plan rule codes",
       "unit": null
     },
     "category": "data_handling",
@@ -3726,16 +4009,20 @@
             "outside scope",
             "physically impossible",
             "scope not confirmed",
+            "several candidates",
             "within tolerance"
           ]
         },
         {
           "ref": "python:hypocurate.access.vocabulary:ELIGIBILITY_RULES",
           "equals": [
+            "conflict_unresolved",
             "duplicate_counted_once",
             "excluded_by_rule",
+            "identity_unresolved",
             "in_scope",
             "invalid_value",
+            "missing_value",
             "model_recalled",
             "out_of_scope",
             "scope_not_confirmed",
@@ -3745,6 +4032,8 @@
         {
           "ref": "python:hypocurate.access.vocabulary:SENSITIVITY_KEYS",
           "equals": [
+            "conflicts_survivor_value",
+            "no_exclusions",
             "possible_duplicates_separate",
             "removal_after_lock",
             "same_alloy_1_at_pct",
@@ -3753,11 +4042,55 @@
             "source_only_assignments",
             "tension_and_compression"
           ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:SOURCE_KEYS",
+          "equals": [
+            "controlled_duplicates",
+            "mpea",
+            "tamu_fcc"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:GROUPING_UNITS",
+          "equals": [
+            "batch",
+            "dataset",
+            "paper"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:VALUE_STATUSES",
+          "equals": [
+            "assigned_by_decision",
+            "assigned_from_source",
+            "converted"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:PROFILE_NAMES",
+          "equals": [
+            "grain_size_strengthening"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.access.vocabulary:SINGLE_PHASE",
+          "equals": [
+            "not_required",
+            "required"
+          ]
         }
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "flag categories without 'several candidates'; eligibility rules without 'missing_value', 'identity_unresolved', 'conflict_unresolved'; sensitivity keys without 'no_exclusions', 'conflicts_survivor_value'; no plan rule codes",
+        "from": "2026-10-05",
+        "to": "2026-10-05",
+        "note": "Step 5. Step 6 additions approved by the owner on 2026-10-05 (planning, questions 3, 5, 6, 9 and decision C)."
+      }
+    ],
     "notes": [],
     "tests": [
       "tests/test_access_layer.py::test_flags_kind_has_no_numbers",
@@ -3804,5 +4137,386 @@
       "tests/test_access_projected.py::test_no_projected_planted_value_in_the_critics_complete_input",
       "tests/test_access_dispatch.py::test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure"
     ]
+  },
+  {
+    "key": "eligibility_rule_order",
+    "name": "One eligibility rule per record, in a fixed order",
+    "state": "in_force",
+    "statement": "Every record gets one rule, the first that applies: model-recalled; invalid value; out of scope; missing value; scope not confirmed; excluded by a rule; identity (ambiguous group, conflict, or not the survivor of a duplicate group); fewer than two grain sizes for its alloy; otherwise eligible. Duplicates are resolved before grain sizes are counted.",
+    "value": {
+      "text": "model_recalled, invalid_value, out_of_scope, missing_value, scope_not_confirmed, excluded_by_rule, identity, single_grain_size, in_scope",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Every eligibility decision and the rule the run records for it.",
+    "reason": "PRD 5.3 needs one stated rule per record; the order makes the decision deterministic.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+          "ref": "python:hypocurate.pipeline.eligibility:decide"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_rule_order",
+      "tests/test_eligibility.py::test_excluded_and_identity_come_before_the_grain_size_count",
+      "tests/test_eligibility.py::test_duplicates_are_resolved_before_grain_sizes_are_counted",
+      "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule"
+    ]
+  },
+  {
+    "key": "conflicts_not_pooled",
+    "name": "Conflicting reports are not pooled",
+    "state": "in_force",
+    "statement": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and neither enters the primary analysis: code does not choose between them. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
+    "value": {
+      "text": "neither in primary; survivor value in a sensitivity analysis",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Conflicting records; the controlled extract's rows 7-8.",
+    "reason": "CLAUDE.md rule 4: conflicting records are preserved, not automatically pooled. PRD 5.3's 'both enter' contradicted it (correction for the next PRD update).",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md. Decision C."
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
+    "sensitivity": "Conflict groups counted once by the survivor rule ('conflicts_survivor_value').",
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:decide"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
+      "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
+      "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files"
+    ]
+  },
+  {
+    "key": "sensitivity_one_change",
+    "name": "Each sensitivity analysis changes one thing",
+    "state": "in_force",
+    "statement": "Each sensitivity set differs from the primary set in exactly one named respect, and every other rule applies unchanged. The reference and default plans name eight: no exclusions; tension and compression together; six batches for Texas A&M; the same-alloy rule at 1 at.%; source-only values; scope not confirmed included; possible duplicates separate; conflicts by the survivor value. Sensitivity results are descriptive, never change the verdict, and no adjustment is made for there being eight.",
+    "value": {
+      "text": "eight sets, one change each",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "The sensitivity sets frozen with the dataset (step 6) and their results (step 7).",
+    "reason": "A sensitivity analysis is interpretable only if it isolates one change.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+          "ref": "python:hypocurate.pipeline.profile:SENSITIVITY_ANALYSES"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:SENSITIVITY_CHANGES"
+        }
+      ],
+      "note": "What each key changes is fixed by the key itself, not by a number in the plan."
+    },
+    "history": [],
+    "notes": [
+      "The reference script's 'discretionary removals' analysis (PRD 10: 438 ± 67 with four records removed) is not carried over: its records were chosen after seeing outcomes, so it cannot be named in a plan locked before the data (owner, 2026-10-05).",
+      "Related: 'no_multiplicity_adjustment'."
+    ],
+    "tests": [
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_from_primary_only_by_its_named_change",
+      "tests/test_reference_sets.py::test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts",
+      "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions"
+    ]
+  },
+  {
+    "key": "code_role_access",
+    "name": "Inclusion and Checks read through access objects",
+    "state": "in_force",
+    "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
+    "value": {
+      "text": "Inclusion: plan, record conditions, flag kinds; Checks: plan, all values",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Eligibility decisions and flags.",
+    "reason": "PRD 4 lists Inclusion and Checks; their reads are logged like the agents'. Blinding Inclusion keeps outcomes out of eligibility by construction of its input.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+          "ref": "python:hypocurate.access.allowlist:CODE_ALLOWED"
+        },
+        {
+          "ref": "python:hypocurate.access.dispatch:bind_code"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_access_code_roles.py::test_the_code_lists_match_the_owners_decision",
+      "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
+      "tests/test_access_code_roles.py::test_only_code_roles_bind_without_an_agent_setting",
+      "tests/test_access_code_roles.py::test_an_agent_setting_cannot_bind_as_a_code_role",
+      "tests/test_access_code_roles.py::test_code_roles_do_not_bind_at_any_other_stage",
+      "tests/test_flags.py::test_flags_use_only_pairwise_and_per_record_rules"
+    ]
+  },
+  {
+    "key": "record_extraction_provenance",
+    "name": "Each record states how it was extracted",
+    "state": "in_force",
+    "statement": "Every stored record states how it was extracted: by adapter code, with the adapter's name and version, or (from step 8) by an agent. Records extracted by code can always be told apart from records extracted by an agent.",
+    "value": {
+      "text": "record.extraction: method, name, version",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Every stored record.",
+    "reason": "Owner's condition when approving record storage by the adapters in step 6.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+          "ref": "sql:ck_record_extraction_shape"
+        },
+        {
+          "ref": "python:hypocurate.sources.adapters:ADAPTER_IDENTITY"
+        }
+      ],
+      "note": "Migration 0003."
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_migrations_step6.py::test_0003_a_new_record_states_its_extraction",
+      "tests/test_migrations_step6.py::test_0003_keeps_every_check_of_0001_and_adds_one",
+      "tests/test_checkpoints.py::test_records_are_stored_only_after_the_lock_with_how_they_were_extracted"
+    ]
+  },
+  {
+    "key": "constructed_test_runs",
+    "name": "Runs with constructed test data",
+    "state": "in_force",
+    "statement": "Constructed test data (the controlled duplicate extract) enter only a run marked as a test (run.experiment_flags constructed_test_data, set at dispatch). An unmarked run refuses them, and logs the refusal, at record storage, inclusion and the freeze. A marked run may freeze, be analysed and complete normally with a verdict; every place its outcome, verdict or numbers are stored or shown carries 'test run: includes constructed data', and marked runs are excluded from every aggregate, count or list of real results.",
+    "value": {
+      "text": "marked at dispatch; refused otherwise",
+      "unit": null
+    },
+    "category": "data_handling",
+    "affects": "Acceptance 14.1 'Duplicates' and the 14.7 demonstration; every list of real results.",
+    "reason": "The extract must never enter a real analysis, yet the duplicate handling must be demonstrable end to end.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+      "status": "partly",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.writes:CONSTRUCTED_MARK",
+          "equals": "constructed_test_data"
+        }
+      ],
+      "done": "The mark and the refusals at storage, inclusion and freeze (step 6).",
+      "pending": "The label wherever a marked run's outcome, verdict or numbers are stored or shown, and the exclusion from aggregates and lists of real results (steps 7 and 10).",
+      "step": 10,
+      "note": "The guard is in code; the database itself does not refuse a constructed record."
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
+      "tests/test_checkpoints.py::test_a_marked_run_takes_the_constructed_records"
+    ]
+  },
+  {
+    "key": "freeze_counts",
+    "name": "Counts known at the dataset freeze",
+    "state": "in_force",
+    "statement": "At the dataset freeze, code computes from structure and grain sizes only (no outcome value), for the primary set, each source within it and each sensitivity set: records, alloys, alloys with enough grain sizes, independent groups and residual degrees of freedom, and whether the plan's minimums are met. They are recorded as information; step 7 writes the analysis results and decides the outcome. With no eligible record no dataset is frozen.",
+    "value": {
+      "text": "counts at the freeze; outcome in step 7",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "The freeze record and the data-sufficiency decision.",
+    "reason": "PRD 3 step 7: sufficiency is decided from the predictor values, before any outcome is visible.",
+    "evidence": [
+      "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
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
+          "ref": "python:hypocurate.pipeline.eligibility:counts"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_eligibility.py::test_counts_known_at_the_freeze",
+      "tests/test_checkpoints.py::test_the_freeze_records_its_counts_and_fingerprint",
+      "tests/test_checkpoints.py::test_no_eligible_record_means_no_dataset_is_frozen",
+      "tests/test_reference_sets.py::test_the_counts_known_at_the_freeze"
+    ]
+  },
+  {
+    "key": "below_minimum_display",
+    "name": "What a run below the fixed minimums shows",
+    "state": "open",
+    "statement": "Open: what a run below the fixed minimums may show besides 'insufficient'.",
+    "value": null,
+    "category": "statistical",
+    "affects": "The gap report and the run viewer for runs below the minimums.",
+    "reason": "The sufficiency option must not be choosable after seeing an estimate.",
+    "evidence": [
+      "Owner, step 6 approval (2026-10-05)."
+    ],
+    "decided": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "not_yet",
+      "step": 7,
+      "note": null
+    },
+    "history": [],
+    "notes": [
+      "Owner's starting position: the counts and which minimums were not met, and nothing derived from outcome values, not even a coefficient, so that the sufficiency option cannot be chosen after seeing an estimate."
+    ],
+    "tests": [],
+    "pending": {
+      "by": "owner",
+      "before_step": 7
+    }
+  },
+  {
+    "key": "curator_tabular_sources",
+    "name": "The Curator's role for tabular sources",
+    "state": "open",
+    "statement": "Open: what the Curator agent does for tabular sources, whose records the adapters (code) extract in step 6.",
+    "value": null,
+    "category": "data_handling",
+    "affects": "Record extraction from step 8; which records count as extracted by an agent.",
+    "reason": "Step 6 stores records by adapter code and does not settle the Curator's role.",
+    "evidence": [
+      "Owner, step 6 planning (2026-10-05)."
+    ],
+    "decided": null,
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "not_yet",
+      "step": 8,
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [],
+    "pending": {
+      "by": "owner",
+      "before_step": 8
+    }
   }
 ]
```

## 9. Tests: new files (full text)

### `tests/pipeline_world.py`

```python
"""Step 6 test helper: runs on the real frozen sources, through the real lifecycle.

`registered(engine)` registers the three sources from their frozen files (step 4 code).
`dispatched_run(...)` creates a query with the chosen sources, submits, confirms and dispatches
it, and starts the run (a run_source row for every registered source, as dispatch writes them).
`through_freeze(...)` locks the plan, stores the records, raises the flags, decides and freezes
(step 6 code), and returns the run's id.
"""
from __future__ import annotations

import json

from sqlalchemy import text

from hypocurate.pipeline import checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources.versions import register

SOURCE_KEYS = ("mpea", "tamu_fcc", "controlled_duplicates")


def registered(engine, keys=SOURCE_KEYS) -> dict[str, int]:
    return {k: register(engine, k).version_id for k in keys}


def _val(engine, sql, **params):
    with engine.begin() as conn:
        result = conn.execute(text(sql), params)
        return result.scalar() if result.returns_rows else None


def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
    """A running run of the reference claim that chose `sources`."""
    with engine.connect() as conn:
        registry = dict(conn.execute(text(
            "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
            "ORDER BY sv.id DESC LIMIT 1) FROM source s")).all())
        ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
        domain = conn.execute(text("SELECT id FROM domain WHERE key = 'grain_size_strengthening'")).scalar_one()
    h = _val(engine, "INSERT INTO hypothesis DEFAULT VALUES RETURNING id")
    vid = _val(engine, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) VALUES "
                       "(:h, 1, 'In FCC multi-principal-element alloys, yield strength rises as grain size falls', "
                       ":d) RETURNING id", h=h, d=domain)
    for key in sources:
        _val(engine, "INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=ids[key])
    _val(engine, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)
    _val(engine, "UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
         v=vid, d=domain)
    _val(engine, "UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)
    flags = json.dumps({"constructed_test_data": True} if marked else {})
    rid = _val(engine, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                       "VALUES (:v, true, CAST(:f AS jsonb)) RETURNING id", v=vid, f=flags)
    for key, version in registry.items():
        if key in sources:
            _val(engine, "INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                         "VALUES (:r, :s, :sv, 'pending')", r=rid, s=ids[key], sv=version)
        else:
            _val(engine, "INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
                 r=rid, s=ids[key])
    _val(engine, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)
    return rid


def version_of(engine, run_id) -> int:
    return _val(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=run_id)


def locked_run(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = dispatched_run(engine, sources, marked)
    checkpoints.lock_rules(engine, rid, plan or reference_plan(version_of(engine, rid)))
    return rid


def through_freeze(engine, sources=("mpea", "tamu_fcc"), marked=False, plan=None) -> int:
    rid = locked_run(engine, sources, marked, plan)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid
```

### `tests/pipeline_fixtures.py`

```python
"""Module-scoped scratch databases for the step 6 tests that run the pipeline once and
check its result in many ways."""
from __future__ import annotations

import contextlib

from sqlalchemy import text

import pipeline_world as pw
from conftest import _create, _drop, url_for
from hypocurate.access.context import AccessContext
from hypocurate.access.fields import record_conditions
from hypocurate.db.engine import make_engine


@contextlib.contextmanager
def frozen_run(admin, database_url, template_database, **kwargs):
    """A scratch database with the three sources registered and one run through the freeze."""
    name = _create(admin, "hypocurate_t", template=template_database)
    engine = make_engine(url_for(database_url, name))
    try:
        pw.registered(engine)
        yield engine, pw.through_freeze(engine, **kwargs)
    finally:
        engine.dispose()
        _drop(admin, name)


def decisions(engine, run_id) -> dict:
    """The stored decisions: per record its origin, source and rule in each set."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT r.id, r.source_item_key, s.key AS source, rr.rule FROM record r "
            "JOIN source_version sv ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
            "JOIN run_record rr ON rr.record_id = r.id AND rr.run_id = r.extraction_run_id "
            "WHERE r.extraction_run_id = :r"), dict(r=run_id)).all()
        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
                             dict(r=run_id)).scalar_one()
        sets = {}
        for key, rid in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a LEFT JOIN "
                                          "analysis_set_record asr ON asr.analysis_set_id = a.id WHERE a.run_id = :r"),
                                     dict(r=run_id)):
            sets.setdefault(key, set())
            if rid is not None:
                sets[key].add(rid)
        flags = conn.execute(text(
            "SELECT f.id, f.kind, f.category, array_agg(fr.record_id ORDER BY fr.record_id) AS records FROM flag f "
            "JOIN flag_record fr ON fr.flag_id = f.id WHERE f.run_id = :r GROUP BY f.id ORDER BY f.id"),
            dict(r=run_id)).all()
        conditions = {c["id"]: c for c in record_conditions(conn, AccessContext(run_id, "inclusion", "curation"))}
    primary = {r.id: r.rule for r in rows}
    rules = {"primary": primary}
    for key, diff in stage["differences_from_primary"].items():
        rules[key] = {**primary, **{int(i): rule for i, rule in diff.items()}}
    return {"origin": {r.id: r.source_item_key for r in rows}, "source": {r.id: r.source for r in rows},
            "rules": rules, "sets": sets, "conditions": conditions,
            "flags": [{"id": f.id, "kind": f.kind, "category": f.category, "records": list(f.records)} for f in flags]}
```

### `tests/test_plan.py`

```python
"""Step 6: the plan model (PRD 5.1). Plans follow PLAN_SCHEMA exactly; every setting that
affects eligibility or grouping is a value of the plan; the default plan takes each value from
the domain profile's named setting (owner, 2026-10-05)."""
from __future__ import annotations

import copy

import pytest

from hypocurate.access.allowlist import PLAN_SCHEMA
from hypocurate.access.fields import project
from hypocurate.pipeline import plan as pl
from hypocurate.pipeline import profile as p
from hypocurate.pipeline.plan import PlanError, default_plan, fingerprint, reference_plan, tags_for, validate


def test_the_default_plan_is_valid_and_is_its_own_projection():
    content = default_plan(7)
    assert validate(content) == content
    assert project(content, PLAN_SCHEMA) == content
    assert set(content) == set(PLAN_SCHEMA) == set(pl.PARTS)
    assert set(content["rules"]) == set(PLAN_SCHEMA["rules"]) == set(pl.RULES)


def test_the_reference_plan_is_the_default_plan_under_the_owners_decisions():
    ref = reference_plan(7)
    assert ref == default_plan(7)
    assert ref["scope"] == {"alloy_class": ["multi-principal-element (high-entropy) alloy"],
                            "temperature_band": ["room temperature"], "test_type": ["tension"], "phase_class": ["FCC"]}
    assert ref["exclusion_rules"] == [{"rule": "grain_size_range", "min": 0.1}]
    assert ref["sufficiency"] == {"option": "fixed_minimum", "min_records": 30, "min_alloys": 5, "min_groups": 10,
                                  "min_resid_df": 10}
    assert ref["rules"] == {
        "same_alloy_decimals": 1, "duplicate_tolerance": 0.02,
        "survivor_source_order": ["mpea", "tamu_fcc", "controlled_duplicates"], "min_grain_sizes": 2,
        "room_temperature_min": 20.0, "room_temperature_max": 25.0, "single_phase": "required",
        "accepted_value_statuses": ["converted", "assigned_from_source", "assigned_by_decision"],
        "grouping": [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "dataset"},
                     {"source": "controlled_duplicates", "unit": "paper"}]}
    assert ref["sensitivity_analyses"] == [
        "no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
        "source_only_assignments", "scope_not_confirmed_included", "possible_duplicates_separate",
        "conflicts_survivor_value"]
    assert ref["eligibility_rules"] == [
        {"flag_kind": "invalid_value", "rule": "invalid_value"},
        {"flag_kind": "exact_duplicate", "rule": "duplicate_counted_once"},
        {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "identity_unresolved"},
        {"flag_kind": "possible_duplicate", "rule": "duplicate_counted_once"},
        {"flag_kind": "values_disagree", "rule": "conflict_unresolved"}]
    assert ref["profile"] == {"name": "grain_size_strengthening", "version": p.PROFILE_VERSION}
    assert ref["model"] == {"name": "hall_petch_alloy_intercepts", "null": "k <= 0", "alternative": "k > 0",
                            "alpha": 0.05}
    assert ref["variables"]["predictor"] == {"field": "grain_size", "unit": "µm", "transformation": "inverse_square_root"}


def test_each_default_comes_from_its_named_setting(monkeypatch):
    """Changing a profile constant changes the default plan: the plan reads it from there."""
    for name, path, new in [("PERMITTED_TEST_TYPES", ("scope", "test_type"), ("compression",)),
                            ("GRAIN_SIZE_FLOOR_UM", ("exclusion_rules", 0, "min"), 0.5),
                            ("DUPLICATE_TOLERANCE", ("rules", "duplicate_tolerance"), 0.05),
                            ("MIN_GRAIN_SIZES_PER_ALLOY", ("rules", "min_grain_sizes"), 3),
                            ("SAME_ALLOY_DECIMALS_DEFAULT", ("rules", "same_alloy_decimals"), 0),
                            ("ROOM_TEMPERATURE_C", ("rules", "room_temperature_max"), (18.0, 27.0)),
                            ("SURVIVOR_SOURCE_ORDER", ("rules", "survivor_source_order"),
                             ("tamu_fcc", "mpea", "controlled_duplicates")),
                            ("ACCEPTED_VALUE_STATUSES", ("rules", "accepted_value_statuses"), ("converted",)),
                            ("PROFILE_VERSION", ("profile", "version"), 99)]:
        with monkeypatch.context() as m:
            m.setattr(p, name, new)
            value = default_plan(1)
            for k in path:
                value = value[k]
            expected = new[1] if name == "ROOM_TEMPERATURE_C" else list(new) if isinstance(new, tuple) else new
            assert value == expected, name
    with monkeypatch.context() as m:
        m.setattr(p, "FIXED_MINIMUMS", {"min_records": 3, "min_alloys": 2, "min_groups": 2, "min_resid_df": 1})
        assert default_plan(1)["sufficiency"]["min_records"] == 3


@pytest.mark.parametrize("change, message", [
    (lambda c: c.update(extra=1), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(note="free text"), "outside PLAN_SCHEMA"),
    (lambda c: c["scope"].update(test_type=["tension", "bending"]), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(same_alloy_decimals=1.5), "outside PLAN_SCHEMA"),
    (lambda c: c["rules"].update(survivor_source_order=["mpea", "elsewhere"]), "outside PLAN_SCHEMA"),
    (lambda c: c.pop("rules"), "lacks rules"),
    (lambda c: c["rules"].pop("grouping"), "rules are exactly"),
    (lambda c: c["scope"].update(temperature_band=["cryogenic"]), "room-temperature band only"),
    (lambda c: c["rules"].update(min_grain_sizes=1), "out of range"),
    (lambda c: c["rules"].update(room_temperature_min=30.0), "out of range"),
    (lambda c: c["rules"].update(survivor_source_order=["mpea", "mpea"]), "each source once"),
    (lambda c: c["rules"].update(accepted_value_statuses=["assigned_by_decision"]), "include 'converted'"),
    (lambda c: c["sufficiency"].update(min_records=0), "at least 1"),
    (lambda c: c["exclusion_rules"].append({"rule": "grain_size_range"}), "minimum or a maximum"),
    (lambda c: c["eligibility_rules"].append({"flag_kind": "values_disagree", "rule": "in_scope"}), "one eligibility"),
    (lambda c: c["eligibility_rules"].append({"flag_kind": "model_recalled", "rule": "out_of_scope"}),
     "flag rule codes"),
    (lambda c: c["sensitivity_analyses"].append("removal_after_lock"), "named once each"),
    (lambda c: c["model"].update(alpha=1.5), "threshold"),
    (lambda c: c["variables"]["predictor"].update(field="hardness"), "grain size"),
])
def test_invalid_plans_are_refused(change, message):
    content = default_plan(1)
    change(content)
    with pytest.raises(PlanError, match=message):
        validate(content)


def test_the_fingerprint_is_the_canonical_json_and_changes_with_any_value():
    a, b = default_plan(1), default_plan(1)
    b = dict(reversed(list(b.items())))  # key order does not matter
    assert fingerprint(a) == fingerprint(b) and len(fingerprint(a)) == 64
    c = copy.deepcopy(a)
    c["rules"]["duplicate_tolerance"] = 0.021
    assert fingerprint(c) != fingerprint(a)


def test_three_tags_one_per_kind_from_the_plan():
    assert tags_for(default_plan(1)) == {"property": "yield strength",
                                         "alloy_class": "multi-principal-element (high-entropy) alloy",
                                         "test_condition": "room-temperature tension"}
    for value in tags_for(default_plan(1)).values():
        assert any(value in values for values in p.TAG_STARTING_LISTS.values())
    two = default_plan(1)
    two["scope"]["test_type"] = ["tension", "compression"]
    with pytest.raises(PlanError, match="three tags"):
        tags_for(two)
```

### `tests/test_flags.py`

```python
"""Step 6: the code checks that raise flags (PRD 5.3; `hypocurate.pipeline.flags`).

Records here are in the `records_full` format Checks receives through its access object. The
owner's rules (2026-10-05): duplicates and conflicts only between different sources; grain size
within the tolerance to pair (a matching tolerance), yield strength within it for a duplicate
and beyond it for a conflict; a group with several candidates from one source is ambiguous and
nothing is paired on a guess. Checks uses only per-record and pairwise rules: no model, slope,
residual or plan hypothesis.
"""
from __future__ import annotations

import ast
import copy
import random
from pathlib import Path

import pytest

from hypocurate.pipeline import flags as fl
from hypocurate.pipeline.plan import default_plan

PLAN = default_plan(1)
DOI = "10.1016/j.test.2020.001"


def rec(i, source="mpea", comp=None, gs=10.0, ys=400.0, uts=None, doi=DOI, test_type="tension", temp=25.0):
    def v(value, unit=None):
        return {"value": value, "unit": unit, "status": "converted"} if value is not None else \
            {"value": None, "unit": unit, "status": "not_reported", "reason": "blank in the source"}
    return {"id": i, "source": source, "origin": f"{source}.csv:row:{i}", "item_index": 0, "kind": "measured",
            "alloy": "x", "paper_reference": None, "paper_doi": doi, "version_fingerprint": "f" * 64, "reported": {},
            "harmonized": {"composition": v(comp or {"Co": 50.0, "Ni": 50.0}, "at.%"), "grain_size": v(gs, "µm"),
                           "yield_strength": v(ys, "MPa"), "ultimate_tensile_strength": v(uts, "MPa"),
                           "test_type": v(test_type), "test_temperature": v(temp, "°C")}}


def kinds(records, plan=PLAN):
    return [(f.kind, f.category, f.records) for f in fl.raise_flags(plan, records)]


def test_physically_impossible_values_are_flagged_per_record():
    got = kinds([rec(1, uts=399.0), rec(2, uts=400.0), rec(3, gs=0.0, doi="10.1/a"), rec(4, gs=-1.0, doi="10.1/b"),
                 rec(5, gs=0.05, doi="10.1/c")])
    assert got == [("invalid_value", "physically impossible", [1]), ("invalid_value", "physically impossible", [3]),
                   ("invalid_value", "physically impossible", [4])]
    f = fl.raise_flags(PLAN, [rec(1, uts=399.0)])[0]
    assert f.compared_values == {"ultimate_tensile_strength_below_yield_strength": [399.0, 400.0]}


def test_rows_within_one_source_are_never_compared():
    assert kinds([rec(1), rec(2), rec(3, ys=600.0)]) == []


def test_exact_duplicate_and_the_tolerance_on_yield_strength():
    assert kinds([rec(1), rec(2, "controlled_duplicates")]) == [("exact_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=101.99)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]
    assert kinds([rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=102.01)]) == [
        ("values_disagree", "differ beyond tolerance", [1, 2])]
    # Relative to the smaller value, in either order.
    assert kinds([rec(1, ys=102.01), rec(2, "controlled_duplicates", ys=100.0)])[0][0] == "values_disagree"


def test_grain_size_is_a_matching_tolerance_never_a_conflict():
    assert kinds([rec(1, gs=100.0), rec(2, "controlled_duplicates", gs=101.99)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]
    assert kinds([rec(1, gs=100.0), rec(2, "controlled_duplicates", gs=102.01)]) == []  # separate measurements
    assert kinds([rec(1, gs=1.79), rec(2, "controlled_duplicates", gs=1.8)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]


def test_a_known_difference_in_paper_or_conditions_means_no_pair():
    other = "controlled_duplicates"
    assert kinds([rec(1), rec(2, other, doi="10.5555/other")]) == []
    assert kinds([rec(1), rec(2, other, test_type="compression")]) == []
    assert kinds([rec(1), rec(2, other, temp=-196.0)]) == []
    assert kinds([rec(1), rec(2, other, comp={"Co": 60.0, "Ni": 40.0})]) == []
    # DOI formatting does not split one paper (step 4's derived key).
    assert kinds([rec(1), rec(2, other, doi=f"https://doi.org/{DOI.upper()}")])[0][0] == "exact_duplicate"


def test_an_unknown_paper_or_condition_gives_a_possible_duplicate_only_if_the_values_match():
    other = "controlled_duplicates"
    assert kinds([rec(1), rec(2, other, doi=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, temp=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, test_type=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, doi=None, ys=500.0)]) == []


def test_the_same_alloy_rule_of_the_plan_decides_which_records_are_compared():
    other = "controlled_duplicates"
    a, b = {"Co": 50.04, "Ni": 49.96}, {"Co": 49.96, "Ni": 50.04}  # both 50.0 / 50.0 at 0.1 at.%
    assert kinds([rec(1, comp=a), rec(2, other, comp=b)])[0][0] == "exact_duplicate"
    c, d = {"Co": 50.06, "Ni": 49.94}, {"Co": 50.04, "Ni": 49.96}  # 50.1 vs 50.0: a known boundary weakness
    assert kinds([rec(1, comp=c), rec(2, other, comp=d)]) == []
    coarse = copy.deepcopy(PLAN)
    coarse["rules"]["same_alloy_decimals"] = 0
    assert kinds([rec(1, comp=c), rec(2, other, comp=d)], coarse)[0][0] == "exact_duplicate"


def test_the_tolerance_is_read_from_the_plan():
    loose = copy.deepcopy(PLAN)
    loose["rules"]["duplicate_tolerance"] = 0.05
    records = [rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=103.0)]
    assert kinds(records)[0][0] == "values_disagree"
    assert kinds(records, loose)[0][0] == "exact_duplicate"


def test_several_candidates_from_one_source_pair_nothing():
    """Owner, 2026-10-05: if a record has more than one candidate in another source, nothing is
    paired automatically and all of them are flagged as possible duplicates."""
    other = "controlled_duplicates"
    one_to_two = kinds([rec(1), rec(2, other), rec(3, other, gs=10.1)])
    assert one_to_two == [("possible_duplicate", "several candidates", [1, 2, 3])]
    two_to_two = kinds([rec(1), rec(2, gs=10.1), rec(3, other), rec(4, other, gs=10.05)])
    assert two_to_two == [("possible_duplicate", "several candidates", [1, 2, 3, 4])]


def test_a_group_whose_records_are_not_all_linked_is_ambiguous():
    """A–B and B–C are candidates, A–C are not (known different papers): nothing is paired."""
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    got = kinds([rec(1), rec(2, "controlled_duplicates", doi=None), rec(3, "tamu_fcc", doi="10.5555/other")], plan)
    assert got == [("possible_duplicate", "several candidates", [1, 2, 3])]


def test_a_group_with_one_conflicting_pair_is_a_conflict():
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    # 1 and 2 agree; 3 reports the same measurement 2.25% higher: the whole group is a conflict.
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0), rec(3, "tamu_fcc", ys=409.0)], plan)
    assert got == [("values_disagree", "differ beyond tolerance", [1, 2, 3])]
    # A possible link (paper unknown on 2) and a conflicting pair (1, 3) in one group: a conflict.
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
                 rec(3, "tamu_fcc", ys=440.0)], plan)
    assert got[0][0] == "possible_duplicate" and got[0][1] == "several candidates"  # 2-3 not linked


def test_a_dataset_source_is_its_own_paper():
    """Texas A&M (grouped by dataset) cites itself: never paired with a record citing another paper."""
    assert kinds([rec(1), rec(2, "tamu_fcc", doi=None)]) == []


def _world(seed):
    """Records with cross-source copies (exact, within tolerance, conflicting, possible) and
    invalid values, and a Hall-Petch-like trend in the outcomes."""
    rnd = random.Random(seed)
    records, measurement, i = [], {}, 0
    for alloy in range(6):
        comp = {"Co": 30.0 + alloy, "Ni": 70.0 - alloy}
        for size in (1.0, 4.0, 16.0, 64.0):
            m = len(measurement)
            ys = 200.0 + 400.0 / size ** 0.5 + rnd.uniform(-5, 5)
            measurement[m] = ys
            doi = f"10.1/p{alloy}"
            i += 1
            records.append((m, 1.0, rec(i, "mpea", comp, size, ys, uts=ys * rnd.choice([1.2, 0.9]), doi=doi)))
            for source, factor, d in (("controlled_duplicates", (1.0, 1.01, 1.3)[m % 3], doi),
                                      ("tamu_fcc", 1.0, None)):
                # A conflicting copy has no third record, so its group stays a plain conflict.
                if (m < 6 or rnd.random() < 0.6) and not (source == "tamu_fcc" and m % 3 == 2):
                    i += 1
                    records.append((m, factor, rec(i, source, comp, size, ys * factor, uts=ys * factor * 1.2, doi=d)))
    return records


@pytest.mark.parametrize("seed", range(5))
def test_flags_use_only_pairwise_and_per_record_rules(seed):
    """Replacing every measurement's outcome by an arbitrary value (copies keep their ratio to it,
    tensile strength its ratio to yield strength) destroys any relation with grain size, but
    changes no pairwise or per-record relation: the flags are identical. So is removing the
    plan's model, hypotheses and predictor transformation: Checks does not read them."""
    items = _world(seed)
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    before = kinds([r for _, _, r in items], plan)
    assert {k for k, _, _ in before} >= {"exact_duplicate", "values_disagree", "invalid_value", "possible_duplicate"}
    rnd = random.Random(1000 + seed)
    new = {m: rnd.uniform(50.0, 5000.0) for m in {m for m, _, _ in items}}
    changed = []
    for m, factor, r in items:
        r = copy.deepcopy(r)
        h = r["harmonized"]
        ratio = h["ultimate_tensile_strength"]["value"] / h["yield_strength"]["value"]
        h["yield_strength"]["value"] = new[m] * factor
        h["ultimate_tensile_strength"]["value"] = new[m] * factor * ratio
        changed.append(r)
    blind = copy.deepcopy(plan)
    for k in ("model", "verdict_statement"):
        del blind[k]
    del blind["variables"]["predictor"]["transformation"]
    assert kinds(changed, blind) == before


def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_outcome_field():
    source = Path(fl.__file__).read_text()
    tree = ast.parse(source)
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
        {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in imported if m and m.split(".")[0] in ("numpy", "scipy", "statsmodels", "pandas")}
    assert "hypocurate.pipeline.profile" not in imported
    plan_keys = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                 and isinstance(n.value, ast.Name) and n.value.id == "plan" and isinstance(n.slice, ast.Constant)}
    assert plan_keys == {"rules", "variables"}
```

### `tests/test_eligibility.py`

```python
"""Step 6: eligibility decisions under the locked plan (PRD 5.3; `hypocurate.pipeline.eligibility`).

Records here are in the `record_conditions` format Inclusion receives (no outcome value).
Owner, 2026-10-05: one rule per record, the first that applies, in the order of the module
docstring; duplicates are resolved before grain sizes are counted; a conflict and an ambiguous
group enter the primary set with none of their records; every setting is read from the locked
plan, never from the domain profile.
"""
from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import profile
from hypocurate.pipeline.plan import default_plan

PLAN = default_plan(1)
STATUS_FIELDS = ("composition", "grain_size", "yield_strength", "test_type", "test_temperature",
                 "test_temperature_band", "microstructure", "phase_class")


def cond(i, source="mpea", comp=None, gs=10.0, temp=25.0, test_type="tension", micro="FCC", phase="FCC", band=None,
         doi=True, row=None, kind="measured", ys=True, status=None, paper="p1", batch=None):
    """A record as Inclusion receives it."""
    st = {f: "not_reported" for f in STATUS_FIELDS}
    st.update({"composition": "converted", "grain_size": "converted" if gs is not None else "not_reported",
               "yield_strength": "converted" if ys else "not_reported",
               "test_type": "converted" if test_type else "not_reported",
               "test_temperature": "converted" if temp is not None else "not_reported",
               "test_temperature_band": "assigned_by_decision" if band else "not_reported",
               "microstructure": "converted" if micro else "not_reported",
               "phase_class": "converted" if phase else "not_reported"})
    st.update(status or {})
    return {"id": i, "source": source, "row": i if row is None else row, "kind": kind, "fingerprint": "f" * 64,
            "has_doi": doi, "paper": paper if doi else None, "batch": batch,
            "composition": comp if comp is not None else {"Co": 50.0, "Ni": 50.0}, "status": st,
            "values": {"grain_size": gs, "test_temperature": temp},
            "categories": {"test_type": test_type, "test_temperature_band": band, "microstructure": micro,
                           "phase_class": phase, "processing_method": None}}


def pair(i, gs, **kw):
    """Two grain sizes of one alloy, so that the alloy passes the grain-size rule."""
    return [cond(i, gs=gs, **kw), cond(i + 1, gs=gs * 4, **kw)]


def flag(kind, category, *records, fid=1):
    return {"id": fid, "kind": kind, "category": category, "records": list(records)}


def decide(records, flags=(), plan=PLAN, key=el.PRIMARY):
    return el.decide(plan, records, list(flags), key)


# --- one rule per record, the first that applies ---------------------------------------------

def test_each_rule_on_its_own():
    records = [*pair(1, 10.0),
               cond(10, kind="model_recalled"),
               cond(11, test_type="compression"), cond(12, temp=600.0), cond(13, micro="FCC+BCC"),
               cond(14, ys=False), cond(15, status={"grain_size": "not_convertible"}, gs=None),
               cond(16, temp=None), cond(17, micro=None), cond(18, test_type=None),
               cond(19, gs=0.05, comp={"Co": 40.0, "Ni": 60.0}), cond(20, gs=4.0, comp={"Co": 40.0, "Ni": 60.0}),
               cond(21, comp={"Co": 30.0, "Ni": 70.0})]
    got = decide(records, [flag("invalid_value", "physically impossible", 2)])
    assert got == {1: "single_grain_size", 2: "invalid_value", 10: "model_recalled", 11: "out_of_scope", 12: "out_of_scope",
                   13: "out_of_scope", 14: "missing_value", 15: "missing_value", 16: "scope_not_confirmed",
                   17: "scope_not_confirmed", 18: "scope_not_confirmed", 19: "excluded_by_rule",
                   20: "single_grain_size", 21: "single_grain_size"}
    # Record 1's partner is invalid, so its alloy is left with one grain size; without the flag
    # both enter.
    assert decide(records)[1] == decide(records)[2] == "in_scope"


@pytest.mark.parametrize("first, second, record", [
    ("model_recalled", "invalid_value", dict(kind="model_recalled")),
    ("invalid_value", "out_of_scope", dict(test_type="compression")),
    ("out_of_scope", "missing_value", dict(test_type="compression", ys=False)),
    ("missing_value", "scope_not_confirmed", dict(ys=False, temp=None)),
    ("scope_not_confirmed", "excluded_by_rule", dict(temp=None, gs=0.05)),
])
def test_rule_order(first, second, record):
    r = cond(5, **record)
    flags = [flag("invalid_value", "physically impossible", 5)] if "invalid_value" in (first, second) else []
    assert decide([r, *pair(1, 10.0)], flags)[5] == first


def test_excluded_and_identity_come_before_the_grain_size_count():
    """Rule 6 before rule 7 before rule 8: a record excluded by a rule, or not surviving its
    duplicate group, does not count as a grain size of its alloy."""
    records = [cond(1, gs=0.05), cond(2, gs=10.0)]
    assert decide(records) == {1: "excluded_by_rule", 2: "single_grain_size"}


def test_duplicates_are_resolved_before_grain_sizes_are_counted():
    """Owner, 2026-10-05: an alloy whose only two records are a cross-source duplicate pair at
    1.79 and 1.8 µm is not eligible: the pair is one grain size, its survivor's."""
    records = [cond(1, gs=1.79), cond(2, "controlled_duplicates", gs=1.8)]
    dup = flag("exact_duplicate", "within tolerance", 1, 2)
    assert decide(records, [dup]) == {1: "single_grain_size", 2: "duplicate_counted_once"}
    # Without the flag the two grain sizes would count as two and both enter.
    assert decide(records) == {1: "in_scope", 2: "in_scope"}


def test_texas_am_band_and_microstructure_by_decision_are_in_scope_unless_the_set_refuses_them():
    tamu = dict(source="tamu_fcc", temp=None, band="room temperature", doi=False,
                status={"microstructure": "assigned_by_decision", "test_type": "assigned_from_source",
                        "phase_class": "assigned_from_source"})
    records = pair(1, 10.0, **tamu)
    assert set(decide(records).values()) == {"in_scope"}
    assert set(decide(records, key="source_only_assignments").values()) == {"scope_not_confirmed"}
    assert set(decide(records, key="scope_not_confirmed_included").values()) == {"in_scope"}


# --- identity: survivors, conflicts, ambiguous groups ---------------------------------------

def test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule():
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=40.0,
                                                                              doi=False)]
    flags = [flag("exact_duplicate", "identical values", 1, 3, fid=1),
             flag("possible_duplicate", "identical values", 2, 4, fid=2)]
    assert decide(records, flags) == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once",
                                      4: "duplicate_counted_once"}
    sep = decide(records, flags, key="possible_duplicates_separate")
    assert sep == {1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once", 4: "in_scope"}


def test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi():
    """Step 1 open item 3: a non-MPEA survivor. The extract record carries the paper's DOI, the
    MPEA record does not: rule 1 keeps the extract record."""
    records = [cond(1, "mpea", gs=10.0, doi=False), cond(2, "controlled_duplicates", gs=10.0, doi=True),
               cond(3, "controlled_duplicates", gs=40.0)]
    got = decide(records, [flag("possible_duplicate", "identical values", 1, 2)])
    assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}


def test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order():
    records = [cond(1, "controlled_duplicates", gs=10.0, doi=False), cond(2, "tamu_fcc", gs=10.0, doi=False),
               cond(3, "tamu_fcc", gs=40.0, doi=False)]
    got = decide(records, [flag("exact_duplicate", "identical values", 1, 2)])
    assert got == {1: "duplicate_counted_once", 2: "in_scope", 3: "in_scope"}
    reordered = copy.deepcopy(PLAN)
    reordered["rules"]["survivor_source_order"] = ["controlled_duplicates", "mpea", "tamu_fcc"]
    assert decide(records, [flag("exact_duplicate", "identical values", 1, 2)], reordered)[1] == "in_scope"


def test_survivor_rule_three_the_lowest_row_within_one_source():
    st = el.settings(PLAN)
    a, b = cond(1, "mpea", row=900), cond(2, "mpea", row=12)
    assert min([a, b], key=lambda r: el.survivor_key(r, st))["id"] == 2


def test_a_conflict_enters_with_neither_record():
    """Decision C (owner, 2026-10-05): neither in primary; 'conflicts_survivor_value' counts the
    group once by the survivor rule."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=40.0)]
    conflict = [flag("values_disagree", "differ beyond tolerance", 1, 3)]
    assert decide(records, conflict) == {1: "conflict_unresolved", 2: "single_grain_size",
                                         3: "conflict_unresolved", 4: "single_grain_size"}
    assert decide(records, conflict, key="conflicts_survivor_value") == {
        1: "in_scope", 2: "in_scope", 3: "duplicate_counted_once", 4: "in_scope"}  # 4: the alloy has 10 and 40 µm
    assert decide(records, conflict, key="possible_duplicates_separate") == decide(records, conflict)


def test_an_ambiguous_group_enters_with_none_of_its_records():
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0), cond(4, "controlled_duplicates", gs=10.1),
               cond(5, "controlled_duplicates", gs=40.0)]
    ambiguous = [flag("possible_duplicate", "several candidates", 1, 3, 4)]
    got = decide(records, ambiguous)
    assert {i: got[i] for i in (1, 3, 4)} == {1: "identity_unresolved", 3: "identity_unresolved",
                                             4: "identity_unresolved"}
    assert decide(records, ambiguous, key="possible_duplicates_separate") == {i: "in_scope" for i in (1, 2, 3, 4, 5)}
    assert decide(records, ambiguous, key="conflicts_survivor_value") == got


def test_identity_applies_only_among_records_that_passed_the_earlier_rules():
    """Extract rows 13–14 (owner, 2026-10-05): the extract record is 'scope not confirmed'
    (rule 5 before rule 7); its MPEA twin survives. With scope not confirmed included, the
    duplicate rule still counts the measurement once."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates", gs=10.0, temp=None)]
    possible = [flag("possible_duplicate", "identical values", 1, 3)]
    assert decide(records, possible) == {1: "in_scope", 2: "in_scope", 3: "scope_not_confirmed"}
    assert decide(records, possible, key="scope_not_confirmed_included")[3] == "duplicate_counted_once"


# --- every setting from the locked plan -----------------------------------------------------

def _changed(path, value):
    plan = copy.deepcopy(PLAN)
    target = plan
    for k in path[:-1]:
        target = target[k]
    target[path[-1]] = value
    return plan


@pytest.mark.parametrize("path, value, records, flags, record, before, after", [
    (("rules", "same_alloy_decimals"), 0, [cond(1, comp={"Co": 50.4, "Ni": 49.6}),
                                           cond(2, comp={"Co": 50.2, "Ni": 49.8}, gs=40.0)], [], 1,
     "single_grain_size", "in_scope"),
    (("rules", "min_grain_sizes"), 3, pair(1, 10.0), [], 1, "in_scope", "single_grain_size"),
    (("rules", "room_temperature_min"), 23.0, [*pair(1, 10.0, temp=22.0)], [], 1, "in_scope", "out_of_scope"),
    (("rules", "room_temperature_max"), 21.0, [*pair(1, 10.0)], [], 1, "in_scope", "out_of_scope"),
    (("rules", "single_phase"), "not_required", [*pair(1, 10.0, micro="FCC+BCC")], [], 1, "out_of_scope",
     "in_scope"),
    (("rules", "accepted_value_statuses"), ["converted", "assigned_from_source"],
     [*pair(1, 10.0, temp=None, band="room temperature")], [], 1, "in_scope", "scope_not_confirmed"),
    (("rules", "survivor_source_order"), ["controlled_duplicates", "mpea", "tamu_fcc"],
     [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
     [flag("exact_duplicate", "identical values", 1, 3)], 1, "in_scope", "duplicate_counted_once"),
    (("scope", "test_type"), ["compression"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
    (("scope", "phase_class"), ["BCC"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
    (("exclusion_rules",), [{"rule": "grain_size_range", "min": 20.0}], pair(1, 10.0), [], 1, "in_scope",
     "excluded_by_rule"),
    (("eligibility_rules",), [{"flag_kind": "values_disagree", "rule": "in_scope"}],
     [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
     [flag("values_disagree", "differ beyond tolerance", 1, 3)], 1, "conflict_unresolved", "in_scope"),
    (("variables", "outcome", "field"), "hardness", pair(1, 10.0), [], 1, "in_scope", "missing_value"),
])
def test_each_setting_is_read_from_the_locked_plan(path, value, records, flags, record, before, after):
    """Owner, 2026-10-05: a plan whose value differs from the profile's default changes the
    decision accordingly; code that read the value from anywhere else would not."""
    assert decide(records, flags)[record] == before
    assert decide(records, flags, _changed(path, value))[record] == after


def test_grouping_is_read_from_the_locked_plan():
    records = {r["id"]: r for r in [*pair(1, 10.0, paper="a"), *pair(3, 10.0, paper="b", comp={"Co": 40.0, "Ni": 60.0}),
                                    *pair(5, 10.0, source="tamu_fcc", doi=False, batch="x"),
                                    cond(7, source="tamu_fcc", doi=False, batch="y", gs=20.0)]}
    assert el.counts(PLAN, records, records)["n_groups"] == 3  # two papers, one dataset
    assert el.counts(PLAN, records, records, "six_batches_as_groups")["n_groups"] == 4  # two papers, two batches
    one = _changed(("rules", "grouping"), [{"source": "mpea", "unit": "dataset"},
                                           {"source": "tamu_fcc", "unit": "dataset"}])
    assert el.counts(one, records, records)["n_groups"] == 2


def test_decisions_ignore_the_domain_profile(monkeypatch):
    """With every profile constant replaced by a different value, the decisions under the same
    locked plan do not change: the decision code reads none of them."""
    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0),
               cond(5, temp=None), cond(6, gs=0.05), *pair(7, 10.0, source="tamu_fcc", temp=None,
                                                          band="room temperature", doi=False)]
    flags = [flag("exact_duplicate", "identical values", 1, 3)]
    before = {k: decide(records, flags, key=k) for k in (el.PRIMARY, *PLAN["sensitivity_analyses"])}
    for name in dir(profile):
        if name.isupper():
            monkeypatch.setattr(profile, name, None)
    after = {k: decide(records, flags, key=k) for k in (el.PRIMARY, *PLAN["sensitivity_analyses"])}
    assert after == before


@pytest.mark.parametrize("module", ["eligibility", "flags", "inclusion", "checks", "checkpoints"])
def test_decision_code_does_not_import_the_domain_profile(module):
    tree = ast.parse((Path(el.__file__).parent / f"{module}.py").read_text())
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "hypocurate.pipeline.profile" not in imported and "profile" not in names


def test_counts_known_at_the_freeze():
    records = {r["id"]: r for r in [*pair(1, 10.0, paper="a"), *pair(3, 1.0, paper="b", comp={"Co": 40.0, "Ni": 60.0})]}
    got = el.counts(PLAN, records, records)
    assert {k: got[k] for k in ("n_records", "n_alloys", "n_alloys_two_grain_sizes", "n_groups", "resid_df")} == \
        {"n_records": 4, "n_alloys": 2, "n_alloys_two_grain_sizes": 2, "n_groups": 2, "resid_df": 1}
    assert got["check1_inputs_met"] and got["check2_inputs_met"] and not got["minimums_met"]
    assert got["minimums"] == {"records": False, "alloys": False, "groups": False, "resid_df": False}
```

### `tests/test_checkpoints.py`

```python
"""Step 6: the rules lock and the dataset freeze (PRD 5.6), the pipeline's write paths and their
refusals (PRD 14.2: changes after a checkpoint are rejected and logged), and the guard that keeps
constructed test data out of a run not marked as a test (register 'constructed_test_runs').

Real sources, registered from their frozen files, in scratch databases."""
from __future__ import annotations

import json
import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

import pipeline_world as pw
from conftest import _create, _drop, url_for
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import checkpoints, checks, extract, inclusion, writes
from hypocurate.pipeline.plan import default_plan, fingerprint, reference_plan
from hypocurate.pipeline.writes import Refused
from hypocurate.sources import adapters
from source_helpers import sealed_from_disk


@pytest.fixture
def engine(db):
    pw.registered(db)
    return db


def q(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def refusals(engine, run_id):
    return [(r.role, r.function, r.detail["code"]) for r in q(
        engine, "SELECT role, function, detail FROM audit_log WHERE run_id = :r AND detail->>'result' = 'rejected' "
                "ORDER BY id", r=run_id)]


def stage(engine, run_id):
    from hypocurate.access.stage import actual_stage
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        return actual_stage(conn, run_id, status)


# --- the rules lock ------------------------------------------------------------------------

def test_the_lock_stores_the_plan_its_fingerprint_and_three_tags_in_one_transaction(engine):
    rid = pw.dispatched_run(engine)
    content = reference_plan(pw.version_of(engine, rid))
    assert checkpoints.lock_rules(engine, rid, content) == fingerprint(content)
    (row,) = q(engine, "SELECT content, fingerprint, sufficiency_option, min_records, min_alloys, min_groups, "
                       "min_resid_df, sensitivity_analysis_keys, xmin::text AS tx FROM plan WHERE run_id = :r", r=rid)
    assert row.content == content and row.fingerprint == fingerprint(content)
    assert (row.sufficiency_option, row.min_records, row.min_alloys, row.min_groups, row.min_resid_df) == \
        ("fixed_minimum", 30, 5, 10, 10)
    assert row.sensitivity_analysis_keys == content["sensitivity_analyses"]
    tags = q(engine, "SELECT tv.kind, tv.value, rt.xmin::text AS tx FROM run_tag rt "
                     "JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r ORDER BY tv.kind", r=rid)
    assert [(t.kind, t.value) for t in tags] == [
        ("alloy_class", "multi-principal-element (high-entropy) alloy"), ("property", "yield strength"),
        ("test_condition", "room-temperature tension")]
    assert {t.tx for t in tags} == {row.tx}  # the lock's own transaction
    assert stage(engine, rid) == "curation"


def test_a_second_lock_or_a_changed_plan_is_refused_and_logged(engine):
    rid = pw.locked_run(engine)
    changed = reference_plan(pw.version_of(engine, rid))
    changed["rules"]["duplicate_tolerance"] = 0.5
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, changed)
    assert refused.value.code == "already_done"
    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "already_done")]
    # The database itself refuses any change to a locked plan, whoever tries.
    with pytest.raises(IntegrityError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(text("UPDATE plan SET content = '{}' WHERE run_id = :r"), dict(r=rid))
    assert q(engine, "SELECT content FROM plan WHERE run_id = :r", r=rid)[0].content == \
        reference_plan(pw.version_of(engine, rid))


def test_an_invalid_plan_or_one_for_another_version_is_refused_and_logged(engine):
    rid = pw.dispatched_run(engine)
    bad = default_plan(pw.version_of(engine, rid))
    bad["rules"]["note"] = "free text"
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, bad)
    assert refused.value.code == "invalid_plan"
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, rid, default_plan(pw.version_of(engine, rid) + 1000))
    assert refused.value.code == "invalid_plan" and "another hypothesis version" in refused.value.message
    assert refusals(engine, rid) == [("checkpoint", "lock_rules", "invalid_plan")] * 2
    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0


def test_the_lock_waits_for_the_run_lock(engine, monkeypatch):
    """The write path takes hc_write_lock first: while another transaction holds the run's lock
    the lock waits, then fails after the lock timeout, and nothing is written."""
    rid = pw.dispatched_run(engine)
    monkeypatch.setattr(writes, "LOCK_TIMEOUT_MS", 300)
    with engine.connect() as holder:
        holder.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
        started = time.monotonic()
        with pytest.raises(DBAPIError, match="lock timeout"):
            checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
        assert time.monotonic() - started >= 0.3
        holder.rollback()
    assert q(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid)[0][0] == 0


def test_every_write_path_takes_the_run_lock_before_it_writes(engine):
    """Locking protocol (step 3): in every transaction of the pipeline's write paths, each INSERT or
    UPDATE comes after `hc_write_lock(p_run => …)`. Refusal rows in audit_log are the named
    exception (written without the run lock)."""
    from sqlalchemy import event
    violations, state = [], {}

    def on_begin(conn):
        state[id(conn)] = False

    def on_execute(conn, cursor, statement, parameters, context, executemany):
        s = " ".join(statement.split()).upper()
        if "HC_WRITE_LOCK(" in s:
            state[id(conn)] = True
        elif s.startswith(("INSERT", "UPDATE")) and not s.startswith("INSERT INTO AUDIT_LOG") \
                and not state.get(id(conn), False):
            violations.append(s[:80])

    event.listen(engine, "begin", on_begin)
    event.listen(engine, "before_cursor_execute", on_execute)
    try:
        rid = pw.dispatched_run(engine, sources=("tamu_fcc",))
        violations.clear()  # the test's own dispatch is not a pipeline write path
        checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
        extract.store_records(engine, rid)
        checks.run_checks(engine, rid)
        inclusion.decide_run(engine, rid)
        checkpoints.freeze_dataset(engine, rid)
    finally:
        event.remove(engine, "begin", on_begin)
        event.remove(engine, "before_cursor_execute", on_execute)
    assert violations == []
    assert stage(engine, rid) == "analysis"


def _between_read_and_write(monkeypatch, module, engine, change):
    """Runs `change` after the step has read through its access object and before its write."""
    original = module.write

    def write(*args, **kwargs):
        change()
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "write", write)


def _add_record(engine, rid, key):
    version = q(engine, "SELECT source_version_id FROM run_source WHERE run_id = :r AND source_version_id IS NOT NULL",
                r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, :k, 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"),
                     dict(r=rid, v=version, k=key))


@pytest.mark.parametrize("step", ["checks", "inclusion", "freeze"])
def test_a_change_between_a_steps_read_and_its_write_is_refused(engine, monkeypatch, step):
    """Each step reads through its access object, then writes in a separate locked transaction
    that re-checks by id what it read. A record added in between is refused as a change."""
    rid = pw.locked_run(engine, sources=("tamu_fcc",))
    extract.store_records(engine, rid)
    if step != "checks":
        checks.run_checks(engine, rid)
    if step == "freeze":
        inclusion.decide_run(engine, rid)
    module, call, function = {"checks": (checks, checks.run_checks, "raise_flags"),
                              "inclusion": (inclusion, inclusion.decide_run, "decide"),
                              "freeze": (checkpoints, checkpoints.freeze_dataset, "freeze_dataset")}[step]
    _between_read_and_write(monkeypatch, module, engine, lambda: _add_record(engine, rid, f"added-{step}"))
    with pytest.raises(Refused) as refused:
        call(engine, rid)
    assert refused.value.code == "changed_since_read"
    assert refusals(engine, rid)[-1][1:] == (function, "changed_since_read")


# --- records, flags and decisions between the checkpoints ------------------------------------

def test_records_are_stored_only_after_the_lock_with_how_they_were_extracted(engine):
    rid = pw.dispatched_run(engine)
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "mpea")
    assert refused.value.code == "stage_mismatch"
    assert refusals(engine, rid) == [("extraction", "store_records", "stage_mismatch")]
    checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid)))
    assert extract.store_records(engine, rid) == {"mpea": 1545, "tamu_fcc": 94}
    rows = q(engine, "SELECT s.key, r.source_item_key, r.harmonized, r.extraction FROM record r JOIN source_version sv "
                     "ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id "
                     "WHERE r.extraction_run_id = :r ORDER BY r.id", r=rid)
    assert {(r.key, json.dumps(r.extraction, sort_keys=True)) for r in rows} == {
        ("mpea", json.dumps({"method": "adapter", "name": "mpea_layout", "version": "1"}, sort_keys=True)),
        ("tamu_fcc", json.dumps({"method": "adapter", "name": "tamu_fcc", "version": "2"}, sort_keys=True))}
    # Unchanged and in file order: the adapter's own output.
    expected = adapters.read(sealed_from_disk("tamu_fcc")).records
    tamu = [r for r in rows if r.key == "tamu_fcc"]
    assert [r.source_item_key for r in tamu] == [e.source_item_key for e in expected]
    assert [r.harmonized for r in tamu] == [e.to_json()["harmonized"] for e in expected]
    assert {r.search_status for r in q(engine, "SELECT search_status FROM run_source WHERE run_id = :r "
                                                "AND source_version_id IS NOT NULL", r=rid)} == {"searched"}
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "mpea")
    assert refused.value.code == "already_done"


def test_constructed_data_never_enters_a_run_not_marked_as_a_test(engine):
    """Register 'constructed_test_runs': refused and logged at storage, inclusion and freeze."""
    rid = pw.locked_run(engine, sources=("mpea", "controlled_duplicates"))
    assert extract.store_source(engine, rid, "mpea") == 1545
    with pytest.raises(Refused) as refused:
        extract.store_source(engine, rid, "controlled_duplicates")
    assert refused.value.code == "constructed_data_unmarked"
    assert q(engine, "SELECT search_status FROM run_source rs JOIN source s ON s.id = rs.source_id "
                     "WHERE rs.run_id = :r AND s.key = 'controlled_duplicates'", r=rid)[0][0] == "pending"
    # Code that bypassed storage (here: plain SQL) still meets the guard at inclusion and freeze.
    version = q(engine, "SELECT source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
                        "WHERE rs.run_id = :r AND s.key = 'controlled_duplicates'", r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, 'extract.csv:row:0', 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
    checks.run_checks(engine, rid)
    with pytest.raises(Refused) as refused:
        inclusion.decide_run(engine, rid)
    assert refused.value.code == "constructed_data_unmarked"
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code == "constructed_data_unmarked"
    assert refusals(engine, rid) == [("extraction", "store_records", "constructed_data_unmarked"),
                                     ("inclusion", "decide", "constructed_data_unmarked"),
                                     ("checkpoint", "freeze_dataset", "constructed_data_unmarked")]
    assert q(engine, "SELECT count(*) FROM run_record WHERE run_id = :r", r=rid)[0][0] == 0
    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0


def test_a_marked_run_takes_the_constructed_records(engine):
    rid = pw.through_freeze(engine, sources=("mpea", "controlled_duplicates"), marked=True)
    assert stage(engine, rid) == "analysis"
    assert q(engine, "SELECT count(*) FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
                     "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r "
                     "AND s.key = 'controlled_duplicates'", r=rid)[0][0] == 16


def test_a_change_after_the_decisions_were_read_is_refused_at_the_freeze(engine):
    rid = pw.locked_run(engine, sources=("mpea",))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    # A record added between inclusion and the freeze (the database allows it before the freeze).
    version = q(engine, "SELECT source_version_id FROM run_source WHERE run_id = :r AND source_version_id IS NOT NULL",
                r=rid)[0][0]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                          "reported, extraction) VALUES (:r, :v, 'added-by-hand', 'measured', '{}', '{}', "
                          "'{\"method\": \"adapter\", \"name\": \"x\", \"version\": \"1\"}')"), dict(r=rid, v=version))
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code == "changed_since_read"
    assert refusals(engine, rid)[-1] == ("checkpoint", "freeze_dataset", "changed_since_read")
    assert stage(engine, rid) == "curation"


def test_the_freeze_refuses_decisions_that_are_not_what_the_locked_rules_produce(engine):
    rid = pw.locked_run(engine, sources=("mpea",))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    with pytest.raises(Refused) as refused:  # no decisions at all
        checkpoints.freeze_dataset(engine, rid)
    assert refused.value.code == "changed_since_read"
    # Decisions written by hand, one of them by choice: the freeze refuses them.
    ids = [r[0] for r in q(engine, "SELECT id FROM record WHERE extraction_run_id = :r ORDER BY id", r=rid)]
    with engine.begin() as conn:
        for rid_ in ids:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)"),
                         dict(r=rid, c=rid_, e=rid_ == ids[0], u="in_scope" if rid_ == ids[0] else "out_of_scope"))
    with pytest.raises(Refused) as refused:
        checkpoints.freeze_dataset(engine, rid)
    assert "not what the locked rules produce" in refused.value.message


def test_after_the_freeze_every_write_is_refused_and_logged(engine):
    rid = pw.through_freeze(engine)
    before = q(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r", r=rid)[0][0]
    for call, role, function in [
            (lambda: checkpoints.lock_rules(engine, rid, reference_plan(pw.version_of(engine, rid))), "checkpoint",
             "lock_rules"),
            (lambda: checks.run_checks(engine, rid), "checks", "bind"),
            (lambda: inclusion.decide_run(engine, rid), "inclusion", "bind"),
            (lambda: checkpoints.freeze_dataset(engine, rid), "inclusion", "bind")]:
        with pytest.raises(Exception):
            call()
    rows = q(engine, "SELECT role, function, allowed FROM audit_log WHERE run_id = :r AND id > 0 ORDER BY id",
             r=rid)[before:]
    assert [(r.role, r.function, r.allowed) for r in rows] == [
        ("checkpoint", "lock_rules", False), ("checks", "bind", False), ("inclusion", "bind", False),
        ("inclusion", "bind", False)]
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO run_record (run_id, record_id, eligible, rule) SELECT :r, id, true, "
                              "'in_scope' FROM record WHERE extraction_run_id = :r LIMIT 1"), dict(r=rid))


# --- the dataset freeze ----------------------------------------------------------------------

def test_the_freeze_records_its_counts_and_fingerprint(engine):
    rid = pw.through_freeze(engine)
    (snap,) = q(engine, "SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r", r=rid)
    (out,) = q(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'dataset_freeze'", r=rid)
    record = out.output
    assert record["fingerprint"] == snap.fingerprint and record["frozen"] is True
    assert snap.n_records == record["counts"]["primary"]["n_records"]
    assert set(record["counts"]) == {"primary", "per_source", *reference_plan(1)["sensitivity_analyses"]}
    assert set(record["counts"]["per_source"]) == {"mpea", "tamu_fcc"}
    stages = [r.stage for r in q(engine, "SELECT stage FROM stage_result WHERE run_id = :r AND role IS NULL "
                                         "ORDER BY id", r=rid)]
    assert stages == ["checks", "inclusion", "dataset_freeze"]
    assert stage(engine, rid) == "analysis"


def test_no_eligible_record_means_no_dataset_is_frozen(engine):
    """PRD 5.6: no dataset is frozen and no test is run; the run is closed without a freeze."""
    rid = pw.dispatched_run(engine, sources=("tamu_fcc",))
    content = reference_plan(pw.version_of(engine, rid))
    content["scope"]["phase_class"] = ["BCC"]
    checkpoints.lock_rules(engine, rid, content)
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    sets = inclusion.decide_run(engine, rid)
    assert set(sets["primary"].values()) <= {"out_of_scope", "missing_value"}
    record = checkpoints.freeze_dataset(engine, rid)
    assert record["frozen"] is False and record["counts"]["primary"]["n_records"] == 0
    assert q(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid)[0][0] == 0
    assert q(engine, "SELECT status, reason FROM calibration_result WHERE run_id = :r", r=rid) == [
        ("unavailable", "no_dataset_frozen")]
    assert stage(engine, rid) == "closed_without_freeze"


def test_the_same_steps_on_another_database_give_the_same_fingerprint(admin, database_url, template_database):
    """The freeze is deterministic: the same frozen sources, plan and steps give the same
    fingerprint, counts and decisions."""
    results = []
    for _ in range(2):
        name = _create(admin, "hypocurate_t", template=template_database)
        engine = make_engine(url_for(database_url, name))
        try:
            pw.registered(engine)
            rid = pw.through_freeze(engine, sources=("mpea", "tamu_fcc", "controlled_duplicates"), marked=True)
            with engine.connect() as conn:
                results.append((conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                             dict(r=rid)).scalar_one(),
                                conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND "
                                                  "stage = 'dataset_freeze'"), dict(r=rid)).scalar_one(),
                                conn.execute(text("SELECT array_agg(rule ORDER BY record_id) FROM run_record "
                                                  "WHERE run_id = :r"), dict(r=rid)).scalar_one()))
        finally:
            engine.dispose()
            _drop(admin, name)
    assert results[0] == results[1]
```

### `tests/test_controlled_duplicates_handling.py`

```python
"""Step 6: duplicate, conflict and near-miss handling on the controlled duplicate extract,
checked against its answer file (PRD 5.3, 14.1 "Duplicates"; step 1).

One run, marked as a test (it holds constructed data), chooses the MPEA dataset and the extract,
and goes through the freeze under the reference plan. For each of the 16 extract rows the
answer file states the flag, the handling in the primary analysis, the survivor and the
sensitivity handling; every record is kept in the store.

The reference plan accepts tension tests only (owner, 2026-10-05), so for rows 15–16 the
answer file's column `handling_under_tension_only_plan` applies. For rows 13–14 the answer
file's "included" in the sensitivity analysis is read as decided by the owner (2026-10-05): in
`scope_not_confirmed_included` the scope no longer excludes the record, and the duplicate rule
still counts the measurement once.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline_fixtures import decisions, frozen_run

REPO = Path(__file__).resolve().parents[1]
TRUTH = list(csv.DictReader((REPO / "tests/fixtures/controlled_duplicates/truth.csv").open(encoding="utf-8")))
FLAG_OF = {"exact_duplicate": "exact_duplicate", "possible_duplicate": "possible_duplicate",
           "conflict": "values_disagree", "not_duplicate": None}


@pytest.fixture(scope="module")
def run(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "controlled_duplicates"),
                    marked=True) as (engine, rid):
        yield decisions(engine, rid)


def ids(run, t):
    """The extract record of answer row t and its MPEA source record."""
    by_origin = {o: i for i, o in run["origin"].items()}
    return (by_origin[f"extract.csv:row:{int(t['extract_row']) - 1}"],
            by_origin[f"MPEA_dataset.csv:row:{t['mpea_row']}"])


def test_every_extract_row_is_kept_in_the_store(run):
    assert sum(s == "controlled_duplicates" for s in run["source"].values()) == 16
    assert sum(s == "mpea" for s in run["source"].values()) == 1545
    assert all(t["kept_in_store"] == "yes" and t["removed_from_store"] == "no" for t in TRUTH)


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_flag_is_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    mine = [f for f in run["flags"] if extract_id in f["records"]]
    expected = FLAG_OF[t["duplicate_status"]]
    if expected is None:  # near misses: matching alloy and grain size alone is not enough
        assert mine == []
    else:
        assert [(f["kind"], f["records"]) for f in mine] == [(expected, sorted([extract_id, mpea_id]))]
        assert mine[0]["category"] != "several candidates"


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_primary_handling_and_the_survivor_are_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    rules = run["rules"]["primary"]
    primary = t["primary_analysis"] if t["handling_under_tension_only_plan"] == "same as under the reference plan" \
        else t["handling_under_tension_only_plan"]
    expected = {
        "counted once": ("in_scope", "duplicate_counted_once"),
        "neither enters: conflict unresolved": ("conflict_unresolved", "conflict_unresolved"),
        "both enter": ("in_scope", "in_scope"),
        "not eligible under a room-temperature plan": ("in_scope", "out_of_scope"),
        "not eligible: scope not confirmed": ("in_scope", "scope_not_confirmed"),
        "excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements')":
            ("in_scope", "out_of_scope"),
    }[primary]
    assert (rules[mpea_id], rules[extract_id]) == expected
    if t["survivor_in_primary"].startswith("MPEA row"):
        assert t["survivor_in_primary"] == f"MPEA row {t['mpea_row']}"
        assert mpea_id in run["sets"]["primary"]
    for record in (extract_id, mpea_id):
        assert (record in run["sets"]["primary"]) == (rules[record] == "in_scope")


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_sensitivity_handling_is_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    sensitivity = t["sensitivity_analysis"]
    if sensitivity == "both counted separately":
        rules = run["rules"]["possible_duplicates_separate"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "in_scope")
        assert {mpea_id, extract_id} <= run["sets"]["possible_duplicates_separate"]
    elif sensitivity == "counted once in conflicts_survivor_value":
        rules = run["rules"]["conflicts_survivor_value"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "duplicate_counted_once")
    elif sensitivity == "included":  # rows 13-14, as the owner decided (module docstring)
        rules = run["rules"]["scope_not_confirmed_included"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "duplicate_counted_once")
    else:
        assert sensitivity == "none"
        for key, rules in run["rules"].items():  # no set treats this pair differently from primary
            if key not in ("tension_and_compression", "source_only_assignments"):
                assert (rules[mpea_id], rules[extract_id]) == \
                    (run["rules"]["primary"][mpea_id], run["rules"]["primary"][extract_id]), key


def test_rows_15_and_16_enter_together_when_compression_is_permitted(run):
    """The compression copies are distinct measurements, not duplicates: with tension and
    compression together, both records of each pair enter."""
    for t in (t for t in TRUTH if t["case"] == "not_duplicate_other_test_type"):
        extract_id, mpea_id = ids(run, t)
        rules = run["rules"]["tension_and_compression"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "in_scope")
```

### `tests/test_reference_sets.py`

```python
"""Step 6: the reference run's record sets under the owner's decisions (PRD 14.1a), and the
rule that each sensitivity set differs from the primary set in exactly one named respect.

The reference run (fixed reference plan, MPEA and Texas A&M, not marked as a test) goes
through the freeze. Its primary set is the reference script's selection
(`docs/reference/worked_example.py`, reproduced test-side in
`test_reference_counts_from_adapters.py`) without MPEA row 139, the compression test the
tension-only decision removes; the 21 Texas A&M records stay eligible through their
room-temperature band and microstructure assigned by decision. The counts are those known at
the freeze (no outcome value); the coefficients are recomputed test-side and reported in the
step 6 summary, and become tests in step 7.
"""
from __future__ import annotations

from collections import Counter

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.plan import reference_plan
from hypocurate.sources import adapters
from pipeline_fixtures import decisions, frozen_run
from source_helpers import sealed_from_disk
from test_reference_counts_from_adapters import mpea_reference_set, tamu_reference_set

ROW_139 = "MPEA_dataset.csv:row:139"


@pytest.fixture(scope="module")
def reference(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc")) as (engine, rid):
        from sqlalchemy import text
        with engine.connect() as conn:
            freeze = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'dataset_freeze'"),
                                  dict(r=rid)).scalar_one()
            snapshot = conn.execute(text("SELECT n_records FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar_one()
        yield {**decisions(engine, rid), "freeze": freeze, "snapshot": snapshot}


@pytest.fixture(scope="module")
def with_extract(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "tamu_fcc", "controlled_duplicates"),
                    marked=True) as (engine, rid):
        yield decisions(engine, rid)


def origins(run, key="primary", source=None):
    return {run["origin"][i] for i in run["sets"][key] if source is None or run["source"][i] == source}


def test_the_primary_set_is_the_reference_selection_without_row_139(reference):
    mpea = {r.source_item_key for r in mpea_reference_set(adapters.read(sealed_from_disk("mpea")).records)}
    tamu = {r.source_item_key for r in tamu_reference_set(adapters.read(sealed_from_disk("tamu_fcc")).records)}
    assert len(mpea) == 77 and ROW_139 in mpea and len(tamu) == 21
    assert origins(reference, source="mpea") == mpea - {ROW_139}
    assert origins(reference, source="tamu_fcc") == tamu
    row_139 = next(i for i, o in reference["origin"].items() if o == ROW_139)
    assert reference["rules"]["primary"][row_139] == "out_of_scope"
    assert row_139 in reference["sets"]["tension_and_compression"]


def test_every_record_has_one_decision_with_its_rule(reference):
    assert len(reference["rules"]["primary"]) == 1545 + 94 == len(reference["origin"])
    assert reference["sets"]["primary"] == {i for i, r in reference["rules"]["primary"].items() if r == "in_scope"}
    by_source = {s: Counter(r for i, r in reference["rules"]["primary"].items() if reference["source"][i] == s)
                 for s in ("mpea", "tamu_fcc")}
    # Texas A&M: 21 eligible, 72 from alloys measured at one grain size, 1 without yield strength (PRD 10).
    assert by_source["tamu_fcc"] == {"in_scope": 21, "single_grain_size": 72, "missing_value": 1}
    assert by_source["mpea"]["in_scope"] == 76
    assert sum(by_source["mpea"].values()) == 1545


def test_the_two_sources_share_no_measurement(reference):
    assert [f for f in reference["flags"] if f["kind"] != "invalid_value"] == []


def test_the_counts_known_at_the_freeze(reference):
    c = reference["freeze"]["counts"]
    pick = lambda d: {k: d[k] for k in ("n_records", "n_alloys", "n_groups", "resid_df", "minimums_met")}
    assert reference["snapshot"] == 97
    assert pick(c["primary"]) == {"n_records": 97, "n_alloys": 22, "n_groups": 20, "resid_df": 74,
                                  "minimums_met": True}
    assert pick(c["per_source"]["mpea"]) == {"n_records": 76, "n_alloys": 13, "n_groups": 19, "resid_df": 62,
                                             "minimums_met": True}
    per_tamu = c["per_source"]["tamu_fcc"]
    assert pick(per_tamu) == {"n_records": 21, "n_alloys": 9, "n_groups": 1, "resid_df": 11, "minimums_met": False}
    assert per_tamu["check1_inputs_met"] and not per_tamu["check2_inputs_met"]  # one group: no grouped uncertainty
    # Tension and compression together is the earlier reference selection (98, 22 alloys, 21 groups).
    assert pick(c["tension_and_compression"]) == {"n_records": 98, "n_alloys": 22, "n_groups": 21, "resid_df": 75,
                                                  "minimums_met": True}
    # The 21 eligible Texas A&M records come from three of the six batches (counted test-side).
    tamu = tamu_reference_set(adapters.read(sealed_from_disk("tamu_fcc")).records)
    assert Counter(r.reported["Iteration"].text for r in tamu) == {"CBA": 7, "CBB": 7, "CBC": 7}
    assert pick(c["six_batches_as_groups"])["n_groups"] == 19 + 3
    assert pick(c["source_only_assignments"]) == {"n_records": 76, "n_alloys": 13, "n_groups": 19, "resid_df": 62,
                                                  "minimums_met": True}


# --- one named change per sensitivity set ---------------------------------------------------

CASCADE = {"in_scope", "single_grain_size", "duplicate_counted_once"}
SCOPE_FIELDS = ("test_type", "test_temperature", "test_temperature_band", "microstructure", "phase_class")


def _direct(key, run, i):
    """Is record i one the set's named change applies to directly?"""
    c, primary = run["conditions"][i], run["rules"]["primary"][i]
    in_flag = lambda kind: any(i in f["records"] for f in run["flags"] if f["kind"] == kind)
    return {
        "no_exclusions": primary == "excluded_by_rule",
        "tension_and_compression": c["categories"]["test_type"] == "compression",
        "six_batches_as_groups": False,
        "same_alloy_1_at_pct": False,
        "source_only_assignments": any(c["status"][f] == "assigned_by_decision" for f in SCOPE_FIELDS),
        "scope_not_confirmed_included": primary == "scope_not_confirmed",
        "possible_duplicates_separate": in_flag("possible_duplicate"),
        "conflicts_survivor_value": in_flag("values_disagree"),
    }[key]


def _check_one_change(run):
    plan = reference_plan(1)
    differing_total = {}
    for key in plan["sensitivity_analyses"]:
        primary, other = run["rules"]["primary"], run["rules"][key]
        differing = {i for i in primary if primary[i] != other[i]}
        direct = {i for i in differing if _direct(key, run, i)}
        decimals = 0 if key == "same_alloy_1_at_pct" else 1
        alloy = lambda i: el.alloy(run["conditions"][i], decimals)
        touched_alloys = {alloy(i) for i in run["conditions"] if _direct(key, run, i)}
        touched_groups = {i for f in run["flags"] if any(_direct(key, run, j) for j in f["records"])
                          for i in f["records"]}
        for i in differing - direct:
            # The rest changed only through the grain-size count (rule 8) or a survivor (rule 7) that
            # the change reached: never through any other rule.
            assert primary[i] in CASCADE and other[i] in CASCADE, (key, run["origin"][i], primary[i], other[i])
            assert key == "same_alloy_1_at_pct" or alloy(i) in touched_alloys or i in touched_groups, \
                (key, run["origin"][i])
            if key == "same_alloy_1_at_pct":
                assert {primary[i], other[i]} == {"in_scope", "single_grain_size"}
        assert run["sets"][key] == {i for i, r in other.items() if r == "in_scope"}
        differing_total[key] = len(differing)
    return differing_total


def test_each_sensitivity_set_differs_from_primary_only_by_its_named_change(reference):
    """Owner, 2026-10-05 (register 'sensitivity_one_change'), on the reference run."""
    differing = _check_one_change(reference)
    assert differing["six_batches_as_groups"] == 0
    assert reference["sets"]["six_batches_as_groups"] == reference["sets"]["primary"]
    for key in ("tension_and_compression", "source_only_assignments", "scope_not_confirmed_included"):
        assert differing[key] > 0, key


def test_each_sensitivity_set_differs_only_by_its_named_change_with_duplicates_and_conflicts(with_extract):
    """The same, on a marked run with the controlled extract, where possible duplicates and
    conflicts exist."""
    differing = _check_one_change(with_extract)
    for key in ("possible_duplicates_separate", "conflicts_survivor_value", "scope_not_confirmed_included"):
        assert differing[key] > 0, key
    assert set(el.SENSITIVITY_CHANGES) == set(reference_plan(1)["sensitivity_analyses"])
```

### `tests/test_access_code_roles.py`

```python
"""Step 6: the code roles Inclusion and Checks read through access objects (PRD 4; owner,
2026-10-05; register entry 'code_role_access').

**Guaranteed, and tested here:** Inclusion receives no outcome value (the projected-data
search of step 5 over its complete input, with values planted everywhere the world stores
them), so no eligibility decision can depend on a record's outcome directly or on its
position relative to the tested relationship.

**Not claimed:** that outcomes play no part at all. Checks receives every value and compares
them to classify duplicates, conflicts and physically invalid records, and Inclusion acts on
those flag kinds (`tests/test_checks.py` shows that Checks uses only pairwise and per-record
rules).
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import access_world as aw
from hypocurate.access import AccessDenied, AccessFailed, role_input
from hypocurate.access.allowlist import ALLOWED, ALL_ROLES, CODE_ALLOWED, CODE_ROLES, OUTCOME_FIELDS, ROLES, allowed
from hypocurate.access.dispatch import bind, bind_code
from hypocurate.db.engine import make_engine
from hypocurate.sources import adapters
from hypocurate.sources.normalize import doi_group_key, identity_hash
from hypocurate.sources.record import HARMONIZED_FIELDS
from test_access_projected import leaks


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def audit(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log WHERE run_id = :r "
                                 "ORDER BY id"), dict(r=run_id)).all()


def test_the_code_lists_match_the_owners_decision():
    assert CODE_ROLES == ("inclusion", "checks") and ALL_ROLES == ROLES + CODE_ROLES
    assert not set(CODE_ROLES) & set(ALLOWED)  # the agent table is unchanged
    assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {"inclusion": {"curation"}, "checks": {"curation"}}
    assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind"}
    assert allowed("checks", "curation") == {"plan", "records_full"}
    for role in CODE_ROLES:
        for stage in ("none", "before_lock", "analysis", "closed_without_freeze", "final", "final_without_freeze"):
            assert allowed(role, stage) == frozenset()


def test_code_roles_bind_at_curation_and_every_bind_is_logged(engine):
    world = aw.build(engine, "curation")
    for role in CODE_ROLES:
        access = bind_code(engine, world.run, role)
        assert (access.context.role, access.context.stage, access.context.agent_setting_id) == (role, "curation", None)
    rows = [r for r in audit(engine, world.run) if r.function == "bind" and r.role in CODE_ROLES]
    assert [(r.role, r.allowed, r.detail["result"]) for r in rows] == [("inclusion", True, "allowed"),
                                                                    ("checks", True, "allowed")]


@pytest.mark.parametrize("stage", ["queued", "before_lock", "analysis", "closed_without_freeze", "final"])
def test_code_roles_do_not_bind_at_any_other_stage(engine, stage):
    world = aw.build(engine, stage)
    for role in CODE_ROLES:
        with pytest.raises(AccessDenied) as denied:
            bind_code(engine, world.run, role)
        assert denied.value.code == "empty_list"
        row = [r for r in audit(engine, world.run) if r.function == "bind"][-1]
        assert (row.role, row.allowed, row.detail["code"], row.detail["code_role"]) == (role, False, "empty_list", True)


def test_only_code_roles_bind_without_an_agent_setting(engine):
    world = aw.build(engine, "curation")
    for role in ROLES + ("analysis", "", "Inclusion"):
        with pytest.raises(AccessDenied) as denied:
            bind_code(engine, world.run, role)
        assert denied.value.code == "not_a_code_role"
    rows = [r for r in audit(engine, world.run) if r.function == "bind"]
    assert {(r.role, r.allowed, r.detail["code"]) for r in rows} == {("invalid", False, "not_a_code_role")}
    with pytest.raises(AccessFailed) as failed:
        bind_code(engine, 10 ** 9, "checks")
    assert failed.value.code == "unknown_run"


def test_an_agent_setting_cannot_bind_as_a_code_role(engine):
    """`bind` takes the role from run_agent_setting, whose roles are the five agent roles."""
    world = aw.build(engine, "curation")
    for role, setting in world.settings.items():
        assert bind(engine, world.run, setting, source_key="mpea" if role == "curator" else None).context.role == role
    with engine.connect() as conn:
        setting = conn.execute(text("SELECT id FROM agent_setting LIMIT 1")).scalar()
    for role in CODE_ROLES:
        with pytest.raises(IntegrityError, match="ck_agent_setting_role"):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO agent_setting (role, version, instruction, model) "
                                  "VALUES (:o, 1, 'x', 'm')"), dict(o=role))
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) "
                                  "VALUES (:r, :o, :a)"), dict(r=world.run, o=role, a=setting))


def test_inclusion_receives_no_outcome_value(engine):
    """The projected-data search over Inclusion's complete input finds none of the planted
    outcome values; Checks' input (all values, by design) is the positive control."""
    world = aw.build(engine, "curation")
    inclusion = role_input(bind_code(engine, world.run, "inclusion"))
    assert set(inclusion) == {"plan", "record_conditions", "flags_kind"}
    assert leaks(inclusion, aw.PLANTED.values()) == []
    assert aw.DIRECTION not in json.dumps(inclusion)
    checks = role_input(bind_code(engine, world.run, "checks"))
    assert any(f.startswith(f"{aw.PLANTED['yield_strength']}:") for f in leaks(checks, aw.PLANTED.values()))
    rows = [r for r in audit(engine, world.run) if r.role in CODE_ROLES and r.function != "bind"]
    assert {(r.role, r.function, r.allowed) for r in rows} == {
        ("inclusion", "plan", True), ("inclusion", "record_conditions", True), ("inclusion", "flags_kind", True),
        ("checks", "plan", True), ("checks", "records_full", True)}


def test_record_conditions_carry_statuses_conditions_and_hashed_identities(engine):
    world = aw.build(engine, "curation")
    got = bind_code(engine, world.run, "inclusion").get("record_conditions")
    with engine.connect() as conn:
        stored = {r.id: r for r in conn.execute(text(
            "SELECT id, source_item_key, paper_doi, harmonized FROM record WHERE extraction_run_id = :r"),
            dict(r=world.run))}
    assert [r["id"] for r in got] == sorted(stored)
    for r in got:
        assert set(r) == {"id", "source", "row", "kind", "fingerprint", "has_doi", "paper", "batch", "composition",
                          "status", "values", "categories"}
        assert len(r["fingerprint"]) == 64
        s = stored[r["id"]]
        assert set(r["status"]) == set(HARMONIZED_FIELDS)
        assert set(r["values"]) == {"grain_size", "test_temperature"} and not set(r["values"]) & OUTCOME_FIELDS
        assert r["row"] == int(s.source_item_key.rsplit(":", 1)[1])
        doi = s.paper_doi if s.paper_doi and s.paper_doi.strip() else None
        assert r["has_doi"] == (doi is not None)
        assert r["paper"] == (identity_hash(doi_group_key(doi)) if doi else None)
        assert r["paper"] is None or (len(r["paper"]) == 64 and (doi or "") not in json.dumps(r))
        assert r["values"]["grain_size"] == s.harmonized["grain_size"].get("value")
    # The DOI planted with an outcome value reaches Inclusion only as a hash.
    assert all("doi " not in json.dumps(r) for r in got)


def test_record_conditions_hash_the_batch_for_texas_am(engine):
    world = aw.build(engine, "curation")
    w = world.w
    vid = w.version["tamu_fcc"]
    # The world's Texas A&M version is a placeholder; store two rows of the real one instead.
    from source_helpers import sealed_from_disk
    records = adapters.read(sealed_from_disk("tamu_fcc")).records[:2]
    with engine.begin() as conn:
        for r in records:
            j = r.to_json()
            conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                              "kind, alloy, harmonized, reported, paper_reference, paper_doi, extraction) VALUES "
                              "(:r, :v, :k, 0, 'measured', :a, CAST(:h AS jsonb), CAST(:rep AS jsonb), :pr, NULL, "
                              "CAST(:x AS jsonb))"),
                         dict(r=world.run, v=vid, k=j["source_item_key"], a=j["alloy"], h=json.dumps(j["harmonized"]),
                              rep=json.dumps(j["reported"]), pr=j["paper_reference"],
                              x=json.dumps(adapters.extraction("tamu_fcc"))))
    got = [r for r in bind_code(engine, world.run, "inclusion").get("record_conditions") if r["source"] == "tamu_fcc"]
    assert [r["batch"] for r in got] == [identity_hash(r.reported["Iteration"].text) for r in records]
    assert all(r["paper"] is None and r["has_doi"] is False for r in got)
    assert got[0]["status"]["microstructure"] == "assigned_by_decision"
    assert got[0]["categories"]["test_temperature_band"] == "room temperature"
    assert got[0]["status"]["yield_strength"] == "converted" and "yield_strength" not in got[0]["values"]
```

### `tests/test_migrations_step6.py`

```python
"""Step 6: migrations 0002 (tag starting lists, data only) and 0003 (record.extraction).

Owner, 2026-10-05: both are in the up, down, up test and the failure-rollback test; 0002 is
safe on a database that already has some values and its downgrade leaves the rows; 0003 is
additive and its replaced insert trigger keeps every check of 0001 and adds only the new
requirement. Every test starts from an empty scratch database."""
import json
import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import profile
from test_migrations import assert_schema_is_empty, assert_schema_is_head, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0002 = SCRIPTS.get_revision("0002").module
M0003 = SCRIPTS.get_revision("0003").module
REGISTER = json.loads((migrate.MIGRATIONS.parents[1] / "assumptions.json").read_text(encoding="utf-8"))


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


def tags(engine) -> dict:
    with engine.connect() as conn:
        return {(k, v): s for k, v, s in conn.execute(text("SELECT kind, value, status FROM tag_value"))}


def record_insert_source(engine) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = 'hc_record_insert'")).scalar_one()


def columns(engine, table) -> set:
    with engine.connect() as conn:
        return set(conn.execute(text("SELECT column_name FROM information_schema.columns "
                                     "WHERE table_schema = 'public' AND table_name = :t"), dict(t=table)).scalars())


def body(sql: str) -> str:
    """A function's body between the $$ quotes, with whitespace normalized."""
    return " ".join(sql.split("$$")[1].split())


# --- 0002 ------------------------------------------------------------------------------------

def test_the_seeded_lists_are_the_registers_and_the_profiles():
    """The migration's lists, the domain profile's and the register entry's statement agree."""
    assert {k: tuple(v) for k, v in M0002.TAG_STARTING_LISTS.items()} == \
        {k: tuple(v) for k, v in profile.TAG_STARTING_LISTS.items()}
    statement = next(e for e in REGISTER if e["key"] == "tag_starting_lists")["statement"]
    names = {"property": "Property", "alloy_class": "Alloy class", "test_condition": "Test condition"}
    assert statement == " ".join(f"{names[k]}: {', '.join(v)}." for k, v in M0002.TAG_STARTING_LISTS.items())
    assert sum(len(v) for v in M0002.TAG_STARTING_LISTS.values()) == 19


def test_0002_changes_no_schema_and_seeds_19_approved_values(engine):
    migrate.upgrade(engine, "0001")
    before = snapshot(engine)
    migrate.upgrade(engine, "0002")
    after = snapshot(engine)
    assert after == before  # no table, column, constraint, index, trigger, function or view changed
    seeded = tags(engine)
    assert len(seeded) == 19 and set(seeded.values()) == {"approved"}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM tag_value WHERE decided_at IS NULL "
                                 "OR proposed_by_run_id IS NOT NULL")).scalar() == 0


def test_0002_is_safe_on_a_database_that_already_has_some_values(engine):
    """An existing value keeps its row and its status; nothing is duplicated."""
    migrate.upgrade(engine, "0001")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO tag_value (kind, value, status) VALUES ('property', 'yield strength', "
                          "'proposed')"))
        conn.execute(text("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('alloy_class', "
                          "'steel', 'rejected', now())"))
        conn.execute(text("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('test_condition', "
                          "'cryogenic', 'approved', now())"))
        ids = dict(conn.execute(text("SELECT value, id FROM tag_value")).all())
    migrate.upgrade(engine)
    got = tags(engine)
    assert len(got) == 19
    assert got[("property", "yield strength")] == "proposed"
    assert got[("alloy_class", "steel")] == "rejected"
    assert got[("test_condition", "cryogenic")] == "approved"
    with engine.connect() as conn:
        assert dict(conn.execute(text("SELECT value, id FROM tag_value WHERE value IN "
                                      "('yield strength', 'steel', 'cryogenic')")).all()) == ids
    assert sum(s == "approved" for s in got.values()) == 17


def test_up_down_up_through_each_new_revision(engine):
    """Head, down to 0002 (0003 removed), down to 0001 (0002's downgrade leaves the rows),
    up again: the same schema as before, the rows once."""
    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    first = snapshot(engine)
    assert "extraction" in columns(engine, "record")

    migrate.downgrade(engine, "0002")
    assert migrate.current_revision(engine) == "0002"
    assert "extraction" not in columns(engine, "record")
    assert " ".join(record_insert_source(engine).split()) == body(M0003.RECORD_INSERT_0001)
    assert len(tags(engine)) == 19

    migrate.downgrade(engine, "0001")
    assert migrate.current_revision(engine) == "0001"
    assert len(tags(engine)) == 19  # rows stay: tag values are never deleted

    migrate.upgrade(engine)
    assert_schema_is_head(engine)
    assert snapshot(engine) == first
    assert len(tags(engine)) == 19

    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_through_the_new_revisions_changes_nothing(engine):
    """A column planted under the name 0003 adds makes the upgrade fail after 0002 has
    inserted its rows. The one transaction rolls both back: no tag value, no new revision."""
    migrate.upgrade(engine, "0001")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE record ADD COLUMN extraction int"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert tags(engine) == {}
    assert migrate.current_revision(engine) == "0001"


# --- 0003 ------------------------------------------------------------------------------------

def test_0003_keeps_every_check_of_0001_and_adds_one():
    """The replaced function is 0001's, unchanged and in the same order, plus one check at the end."""
    original = next(f for f in M0001.FUNCTIONS if "CREATE FUNCTION hc_record_insert()" in f)
    assert body(M0003.RECORD_INSERT_0001) == body(original)
    added = ("IF NEW.extraction IS NULL THEN PERFORM hc_reject('a record states how it was extracted "
             "(adapter or agent, with name and version)'); END IF;")
    old, new = body(M0003.RECORD_INSERT_0001), body(M0003.RECORD_INSERT_0003)
    assert new == old.replace("RETURN NEW; END", f"{added} RETURN NEW; END")
    assert len(re.findall(r"PERFORM hc_reject", new)) == len(re.findall(r"PERFORM hc_reject", old)) + 1


def _record(conn, run, version, key, extraction):
    conn.execute(text("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, "
                      "reported, extraction) VALUES (:r, :v, :k, 'measured', '{}', '{}', CAST(:x AS jsonb))"),
                 dict(r=run, v=version, k=key, x=extraction))


def test_0003_a_new_record_states_its_extraction(db):
    from model_builder import World
    w = World(db)
    rid = w.locked()
    good = json.dumps({"method": "adapter", "name": "mpea_layout", "version": "1"})
    with db.begin() as conn:
        _record(conn, rid, w.version["mpea"], "row-1", good)
    with pytest.raises(IntegrityError, match="states how it was extracted"):
        with db.begin() as conn:
            _record(conn, rid, w.version["mpea"], "row-2", None)
    for bad in ({"method": "guess", "name": "x", "version": "1"}, {"method": "agent", "name": "", "version": "1"},
                {"method": "adapter", "name": "x"}, ["adapter"]):
        with pytest.raises(IntegrityError, match="ck_record_extraction_shape"):
            with db.begin() as conn:
                _record(conn, rid, w.version["mpea"], "row-3", json.dumps(bad))
    # Every 0001 check still applies: for example no record before the rules lock.
    with pytest.raises(IntegrityError, match="only after the rules lock"):
        with db.begin() as conn:
            _record(conn, w.running(), w.version["mpea"], "row-4", good)
```

## 10. Tests: changed files (diffs)

```diff
diff --git a/tests/access_world.py b/tests/access_world.py
index 535d18d..0a781b1 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -126,11 +126,11 @@ def store_records(w: World, run: int, key="mpea") -> list[int]:
     for r in adapters.read(version).records:
         j = r.to_json()
         ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
-                          "kind, alloy, harmonized, reported, paper_reference, paper_doi) "
-                          "VALUES (:r, :sv, :k, :ix, :kind, :a, :j_h, :j_rep, :pr, :pd) RETURNING id",
+                          "kind, alloy, harmonized, reported, paper_reference, paper_doi, extraction) "
+                          "VALUES (:r, :sv, :k, :ix, :kind, :a, :j_h, :j_rep, :pr, :pd, :j_x) RETURNING id",
                        r=run, sv=w.version[key], k=j["source_item_key"], ix=j["item_index"], kind=j["kind"],
                        a=j["alloy"], j_h=j["harmonized"], j_rep=j["reported"], pr=j["paper_reference"],
-                       pd=j["paper_doi"]))
+                       pd=j["paper_doi"], j_x=adapters.extraction(key)))
     return ids
 
 
@@ -143,8 +143,10 @@ def store_value_records(w: World, run: int, value: float, n=3, key="mpea") -> li
              "composition": {"value": {"Co": 50.0, "Ni": 50.0}, "unit": "at.%", "status": "converted"}}
         rep = {YS: {"column": YS, "text": f"{value}", "unit": "MPa"}}
         ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
-                          "kind, alloy, harmonized, reported) VALUES (:r, :sv, :k, 0, 'measured', 'Co50Ni50', :j_h, :j_rep) "
-                          "RETURNING id", r=run, sv=w.version[key], k=f"other-{run}-{i}", j_h=h, j_rep=rep))
+                          "kind, alloy, harmonized, reported, extraction) "
+                          "VALUES (:r, :sv, :k, 0, 'measured', 'Co50Ni50', :j_h, :j_rep, :j_x) "
+                          "RETURNING id", r=run, sv=w.version[key], k=f"other-{run}-{i}", j_h=h, j_rep=rep,
+                       j_x=adapters.extraction(key)))
     return ids
 
 
@@ -213,7 +215,8 @@ def build(engine, stage_name: str) -> AccessWorld:
                                   "VALUES ('planner', 1, :i, 'model-a') RETURNING id",
                                i=f"remember {PLANTED['yield_strength']}")}
     sql(w, "INSERT INTO tag_value (kind, value, status, decided_at) "
-           "VALUES ('property', 'yield strength', 'approved', now())")
+           "VALUES ('property', 'yield strength', 'approved', now()) "
+           "ON CONFLICT (kind, value) DO NOTHING")  # seeded by migration 0002 (step 6)
     sql(w, "INSERT INTO tag_value (kind, value, status) VALUES ('property', :v, 'proposed')",
         v=f"strength {PLANTED['yield_strength']}")
     original = original_run(w)
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 4a9401b..5d1ba12 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -9,6 +9,8 @@ from sqlalchemy import text
 from sqlalchemy.exc import IntegrityError
 
 FP = "0" * 64  # a well-formed fingerprint
+# How a test record was extracted (record.extraction, required from migration 0003, step 6).
+EXTRACTION = '{"method": "adapter", "name": "test", "version": "1"}'
 
 
 def sha(data: bytes) -> str:
@@ -172,8 +174,9 @@ class World:
         kind = kind or self.val("SELECT data_kind FROM source_version WHERE id = :v", v=self.version[source])
         return self.val(
             "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, "
-            "alloy, harmonized, reported) VALUES (:r, :sv, :k, :i, :kind, 'CoCrNi', '{}', '{}') RETURNING id",
-            r=rid, sv=self.version[source], k=key, i=index, kind=kind)
+            "alloy, harmonized, reported, extraction) VALUES (:r, :sv, :k, :i, :kind, 'CoCrNi', '{}', '{}', "
+            "CAST(:x AS jsonb)) RETURNING id",
+            r=rid, sv=self.version[source], k=key, i=index, kind=kind, x=EXTRACTION)
 
     def decide(self, rid, rec, eligible=True, rule="in_scope"):
         self.run_sql("INSERT INTO run_record (run_id, record_id, eligible, rule) VALUES (:r, :c, :e, :u)",
diff --git a/tests/test_access_dispatch.py b/tests/test_access_dispatch.py
index e17f56c..9bb6499 100644
--- a/tests/test_access_dispatch.py
+++ b/tests/test_access_dispatch.py
@@ -275,7 +275,7 @@ def test_the_frozen_sources_have_no_unrecognized_category_value():
     for key in ("mpea", "tamu_fcc"):
         recs = adapters.read(sealed_from_disk(key)).records
         values = [(f, r.harmonized[f].value) for r in recs for f in vocabulary.CATEGORY_FIELDS
-                  if r.harmonized[f].status in ("converted", "assigned")]
+                  if r.harmonized[f].status in ("converted", "assigned_from_source", "assigned_by_decision")]
         assert vocabulary.unrecognized_counts(values) == {}, key
 
 
diff --git a/tests/test_access_layer.py b/tests/test_access_layer.py
index f0a5f62..d88be8c 100644
--- a/tests/test_access_layer.py
+++ b/tests/test_access_layer.py
@@ -22,6 +22,7 @@ from hypocurate.access import vocabulary
 from hypocurate.access.allowlist import ALLOWED, FIELDS, ROLES, SOURCE_META_FIELDS, STAGES, allowed
 from hypocurate.access.fields import READERS
 from hypocurate.db.engine import make_engine
+from hypocurate.pipeline.profile import TAG_STARTING_LISTS
 from hypocurate.sources.record import HARMONIZED_FIELDS
 
 REPO = Path(__file__).resolve().parent.parent
@@ -371,7 +372,8 @@ def test_record_metadata_carries_no_number_but_identity_and_composition(engine):
         assert set(r) == {"id", "source", "item_index", "kind", "alloy", "composition", "paper_doi", "status",
                           "categories"}  # no origin key, no paper title (review finding 3)
         assert set(r["status"]) == set(HARMONIZED_FIELDS)
-        assert set(r["status"].values()) <= {"converted", "not_reported", "not_convertible", "assigned", None}
+        assert set(r["status"].values()) <= {"converted", "not_reported", "not_convertible", "assigned_from_source",
+                                             "assigned_by_decision", None}
         for f, v in r["categories"].items():
             assert v is None or v == "unrecognized" or vocabulary.category(f, v) == v, (f, v)
     planted = [r for r in got if r["status"]["yield_strength"] == "not_convertible"]
@@ -409,9 +411,15 @@ def test_the_plan_is_projected_by_its_named_parts(engine):
 
 
 def test_tag_values_are_the_approved_lists_only(engine):
+    """The approved values only: since step 6, the 19 starting values seeded by migration 0002
+    (the world's own approved value is one of them). The planted proposed value never appears."""
     world = aw.build(engine, "before_lock")
-    assert access(engine, world, "planner", "before_lock").get("tag_values") == [
-        {"kind": "property", "value": "yield strength"}]
+    got = access(engine, world, "planner", "before_lock").get("tag_values")
+    seeded = sorted(({"kind": k, "value": v} for k, values in TAG_STARTING_LISTS.items() for v in values),
+                    key=lambda t: (t["kind"], t["value"]))
+    assert got == seeded
+    assert {"kind": "property", "value": "yield strength"} in got
+    assert str(aw.PLANTED["yield_strength"]) not in json.dumps(got)
 
 
 def test_record_counts_are_counts_from_the_sealed_source(engine):
diff --git a/tests/test_adapter_mpea.py b/tests/test_adapter_mpea.py
index 9147f78..420f2f6 100644
--- a/tests/test_adapter_mpea.py
+++ b/tests/test_adapter_mpea.py
@@ -94,7 +94,7 @@ def test_test_type_codes(result):
 
 def test_no_value_is_assigned(result):
     assert not [r for r in result.records for v in r.harmonized.values()
-                if v.status == "assigned" or v.citation is not None]
+                if v.status in ("assigned_from_source", "assigned_by_decision") or v.citation is not None]
 
 
 def _reference_norm(f):
diff --git a/tests/test_adapter_tamu.py b/tests/test_adapter_tamu.py
index e4e1436..d7c98e6 100644
--- a/tests/test_adapter_tamu.py
+++ b/tests/test_adapter_tamu.py
@@ -96,32 +96,53 @@ def test_one_group_the_dataset(records):
 
 
 def test_assigned_values_carry_their_passage(records):
+    """Step 6 (owner, 2026-10-05): two assigned statuses. Test type and phase class are
+    assigned from the source's own statements; the band and the microstructure by decision."""
     for r in records:
         t, p = r.harmonized["test_type"], r.harmonized["phase_class"]
-        assert (t.value, t.status, t.citation) == ("tension", "assigned", tamu_fcc.TEST_TYPE_CITATION)
-        assert (p.value, p.status, p.citation) == ("FCC", "assigned", tamu_fcc.PHASE_CITATION)
+        assert (t.value, t.status, t.citation) == ("tension", "assigned_from_source", tamu_fcc.TEST_TYPE_CITATION)
+        assert (p.value, p.status, p.citation) == ("FCC", "assigned_from_source", tamu_fcc.PHASE_CITATION)
         assert "Quasistatic tensile testing" in t.citation.quote and t.citation.location.startswith("line 177")
         assert "94 FCC alloy conditions" in p.citation.quote
+        b, m = r.harmonized["test_temperature_band"], r.harmonized["microstructure"]
+        assert (b.value, b.status, b.citation) == ("room temperature", "assigned_by_decision",
+                                                   tamu_fcc.TEMPERATURE_DECISION)
+        assert (m.value, m.status, m.citation) == ("FCC", "assigned_by_decision", tamu_fcc.MICROSTRUCTURE_DECISION)
         out = r.to_json()["harmonized"]
-        assert out["test_type"]["status"] == "assigned" and out["test_type"]["citation"]["quote"]
-    assigned = {k for r in records for k, v in r.harmonized.items() if v.status == "assigned"}
-    assert assigned == {"test_type", "phase_class"}
+        assert out["test_type"]["status"] == "assigned_from_source" and out["test_type"]["citation"]["quote"]
+        assert out["microstructure"]["status"] == "assigned_by_decision" and out["microstructure"]["citation"]["quote"]
+    by_status = lambda status: {k for r in records for k, v in r.harmonized.items() if v.status == status}
+    assert by_status("assigned_from_source") == {"test_type", "phase_class"}
+    assert by_status("assigned_by_decision") == {"test_temperature_band", "microstructure"}
+
+
+def test_decision_citations_quote_the_register():
+    """The citation of a value assigned by decision is the register entry's own statement."""
+    entries = {e["key"]: e for e in json.loads((REPO / "hypocurate" / "assumptions.json").read_text())}
+    for key, citation in (("tamu_test_temperature", tamu_fcc.TEMPERATURE_DECISION),
+                          ("tamu_microstructure", tamu_fcc.MICROSTRUCTURE_DECISION)):
+        e = entries[key]
+        assert citation.document == "hypocurate/assumptions.json"
+        assert citation.quote == e["statement"]
+        assert f"'{key}'" in citation.location and e["decided"]["date"] in citation.location
+        assert e["state"] == "in_force"
 
 
 def test_assigned_and_reported_stay_distinguishable(records):
     for r in records:
         for v in r.harmonized.values():
-            assert (v.status == "assigned") <= (v.citation is not None)
+            assert (v.status in ("assigned_from_source", "assigned_by_decision")) <= (v.citation is not None)
         assert all(isinstance(rep, Reported) and not hasattr(rep, "citation") for rep in r.reported.values())
         assert "tension" not in {rep.text for rep in r.reported.values()}
+        assert "room temperature" not in {rep.text for rep in r.reported.values()}
 
 
-def test_temperature_is_not_reported(records):
+def test_temperature_is_not_reported_and_the_band_is_assigned_by_decision(records):
     for r in records:
-        for name in ("test_temperature", "test_temperature_band"):
-            v = r.harmonized[name]
-            assert (v.status, v.value) == ("not_reported", None)
-            assert "states no test temperature" in v.reason
+        v = r.harmonized["test_temperature"]
+        assert (v.status, v.value) == ("not_reported", None)
+        assert "states no test temperature" in v.reason
+        assert r.harmonized["test_temperature_band"].status == "assigned_by_decision"
 
 
 def test_composition_in_atomic_percent(records):
@@ -211,7 +232,8 @@ def test_planted_values_are_kept_and_marked():
     assert {k: v for k, v in by_row[4].harmonized.items() if k != "grain_size_sd"} == \
         {k: v for k, v in by_row[0].harmonized.items() if k != "grain_size_sd"}
     assert (h(4, "grain_size").value, h(4, "yield_strength").value) == (23.0, 284.2)
-    assert (h(4, "test_type").status, h(4, "test_type").citation) == ("assigned", tamu_fcc.TEST_TYPE_CITATION)
+    assert (h(4, "test_type").status, h(4, "test_type").citation) == ("assigned_from_source",
+                                                                      tamu_fcc.TEST_TYPE_CITATION)
     assert h(4, "test_temperature").status == "not_reported"
     assert h(4, "test_temperature").reason == tamu_fcc.TEMPERATURE_NOT_REPORTED
     assert by_row[4].alloy == by_row[0].alloy
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index f8ffe4c..b8c6100 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -27,16 +27,18 @@ REGISTER = a.load_register()
 BY_KEY = {e["key"]: e for e in REGISTER}
 OWNER = "owner (Khalid El-Awady)"
 
-# The owner's eight decisions of 2026-10-05 (step 4b instructions, a to h).
+# The owner's eight decisions of 2026-10-05 (step 4b instructions, a to h), with how far each is
+# applied: (category, applied status, step that completes it). Step 6 applied a, b, d, f and h,
+# and the plan default of e.
 OWNER_DECISIONS = {
-    "tamu_test_temperature": ("scientific", 6),
-    "permitted_test_types": ("scientific", 6),
-    "tamu_grouping_unit": ("statistical", 7),  # partly applied: the adapter's grouping unit
-    "same_alloy_rule": ("scientific", 6),  # partly applied from step 5: the gap report's summaries
-    "fixed_minimums": ("statistical", 6),  # partly applied: the database's checks
-    "values_disagree_tolerance": ("data_handling", 6),
-    "calibration_noise_levels": ("statistical", 7),
-    "tag_starting_lists": ("data_handling", 6),
+    "tamu_test_temperature": ("scientific", "yes", None),
+    "permitted_test_types": ("scientific", "yes", None),
+    "tamu_grouping_unit": ("statistical", "partly", 7),  # the adapter's unit and the plan's grouping; inference
+    "same_alloy_rule": ("scientific", "yes", None),
+    "fixed_minimums": ("statistical", "partly", 7),  # plan default and freeze counts; the check deciding outcomes
+    "values_disagree_tolerance": ("data_handling", "yes", None),
+    "calibration_noise_levels": ("statistical", "not_yet", 7),
+    "tag_starting_lists": ("data_handling", "yes", None),
 }
 
 
@@ -53,13 +55,14 @@ def test_every_category_has_entries_and_keys_are_unique():
     assert len({e["key"] for e in REGISTER}) == len(REGISTER)
 
 
-PARTLY = {"tamu_grouping_unit", "papers_independent", "sufficiency_options", "controlled_extract_disabled",
-          "validity_checks", "fixed_minimums", "grain_size_transformation_at_analysis", "assigned_value_statuses",
-          "same_alloy_rule"}  # step 5: the gap report's condition summaries group alloys under the rule
+# Step 6 completed same_alloy_rule, sufficiency_options, controlled_extract_disabled and
+# assigned_value_statuses, and added constructed_test_runs (its label and exclusion: steps 7, 10).
+PARTLY = {"tamu_grouping_unit", "papers_independent", "validity_checks", "fixed_minimums",
+          "grain_size_transformation_at_analysis", "constructed_test_runs"}
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
-    for key, (category, step) in OWNER_DECISIONS.items():
+    for key, (category, status, step) in OWNER_DECISIONS.items():
         e = BY_KEY[key]
         # Review finding 4: the calibration direction is approved, its technical review pending.
         expected_state = "direction_approved" if key == "calibration_noise_levels" else "in_force"
@@ -67,8 +70,8 @@ def test_the_owners_eight_decisions_are_recorded_as_decided():
         assert e["category"] == category, key
         assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
         assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}, key
-        status = "partly" if key in PARTLY else "not_yet"
-        assert e["applied"]["status"] == status and e["applied"]["step"] == step, key
+        assert e["applied"]["status"] == status and e["applied"].get("step") == step, key
+        assert (status == "partly") == (key in PARTLY), key
 
 
 def test_decisions_carry_the_owners_wording():
@@ -110,21 +113,30 @@ def test_the_survivor_rule_has_the_owners_step_1_wording():
 
 
 def test_the_pairing_rule_is_decided_and_calibration_awaits_its_technical_review():
-    """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)."""
-    assert [e["key"] for e in REGISTER if e["state"] == "open"] == []
+    """Finding 4. The pairing rule was the open entry; the owner decided it on 2026-10-05 (step 5)
+    and added the possible-duplicate case and the rule for several candidates in step 6 planning.
+    Step 6 recorded two new open decisions for the owner (steps 7 and 8)."""
+    assert [e["key"] for e in REGISTER if e["state"] == "open"] == ["below_minimum_display", "curator_tabular_sources"]
+    assert {e["key"]: e["pending"]["before_step"] for e in REGISTER if e["state"] == "open"} == {
+        "below_minimum_display": 7, "curator_tabular_sources": 8}
+    assert "not even a coefficient" in " ".join(BY_KEY["below_minimum_display"]["notes"])
     pairing = BY_KEY["conflict_pairing_rule"]
     assert pairing["state"] == "in_force" and "pending" not in pairing
     assert pairing["decided"] == {"by": OWNER, "date": "2026-10-05"}
     assert pairing["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
-    assert pairing["applied"]["status"] == "not_yet" and pairing["applied"]["step"] == 6
-    assert pairing["statement"] == (
-        "Duplicates and conflicts are looked for only between records from different sources that cite the "
-        "same paper with the same alloy, grain size and test conditions. Rows within one source are always "
-        "separate measurements (repeat specimens).")
+    assert pairing["applied"]["status"] == "yes"
+    assert pairing["statement"].startswith(
+        "Duplicates and conflicts are looked for only between records from different sources; rows within one "
+        "source are always separate measurements (repeat specimens).")
+    assert "a possible duplicate" in pairing["statement"] and "nothing is paired automatically" in pairing["statement"]
     notes = " ".join(pairing["notes"])
     assert "a source that repeats its own row by mistake is not caught" in notes
     assert "Not reviewed by an expert." in notes
     assert pairing["history"][0]["value"].startswith("open decision:")
+    assert pairing["history"][-1]["value"] == (
+        "Duplicates and conflicts are looked for only between records from different sources that cite the "
+        "same paper with the same alloy, grain size and test conditions. Rows within one source are always "
+        "separate measurements (repeat specimens).")
     assert [e["key"] for e in REGISTER if e["state"] == "direction_approved"] == ["calibration_noise_levels"]
     assert BY_KEY["calibration_noise_levels"]["pending"] == {"by": "second-model technical review", "before_step": 7}
 
@@ -185,7 +197,7 @@ def test_the_microstructure_decision_is_recorded():
     assert e["value"]["text"] == "single-phase FCC (assigned by decision)"
     assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}
     assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
-    assert e["applied"]["status"] == "not_yet" and e["applied"]["step"] == 6
+    assert e["applied"]["status"] == "yes"  # step 6
     evidence = " ".join(e["evidence"])
     for cited in ("main.tex line 138", "main.tex line 173", "supplementary.tex line 61", "main.tex line 175",
                   "main.tex line 177", "supplementary.tex line 65"):
@@ -198,6 +210,32 @@ def test_the_microstructure_decision_is_recorded():
     assert e["history"][0]["value"].endswith("(open decision)")
 
 
+def test_the_step_6_decisions_carry_the_owners_wording():
+    """Owner, step 6 planning and approval (2026-10-05)."""
+    tol = BY_KEY["values_disagree_tolerance"]
+    assert "matching tolerance" in tol["statement"] and "duplicate-or-conflict threshold" in tol["statement"]
+    assert "can never raise a conflict flag" in " ".join(tol["notes"])
+    assert "survive duplicate resolution" in BY_KEY["alloy_eligibility"]["statement"]
+    conflicts = BY_KEY["conflicts_not_pooled"]
+    assert "neither enters the primary analysis" in conflicts["statement"]
+    assert "CLAUDE.md rule 4" in conflicts["reason"] and "PRD 5.3" in conflicts["reason"]
+    one = BY_KEY["sensitivity_one_change"]
+    assert "exactly one named respect" in one["statement"] and "never change the verdict" in one["statement"]
+    assert "no adjustment is made for there being eight" in one["statement"]
+    assert "discretionary removals" in " ".join(one["notes"])
+    access = BY_KEY["code_role_access"]["statement"]
+    assert "Inclusion receives no outcome value" in access and "Not claimed: that outcomes play no part at all" in access
+    assert "test run: includes constructed data" in BY_KEY["constructed_test_runs"]["statement"]
+    assert BY_KEY["constructed_test_runs"]["applied"]["step"] == 10
+    assert "adapter code, with the adapter's name and version" in BY_KEY["record_extraction_provenance"]["statement"]
+    assert "Duplicates are resolved before grain sizes are counted." in BY_KEY["eligibility_rule_order"]["statement"]
+    assert "step 1 answer file" in " ".join(BY_KEY["duplicate_survivor_rule"]["notes"])
+    for key in ("sensitivity_one_change", "code_role_access", "constructed_test_runs", "record_extraction_provenance",
+                "eligibility_rule_order", "conflicts_not_pooled", "freeze_counts"):
+        e = BY_KEY[key]
+        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"} and e["expert_review"]["status"] == "not_reviewed"
+
+
 def open_entry():
     """An open decision built for the tests, independent of the register's own."""
     e = copy.deepcopy(BY_KEY["tamu_microstructure"])
@@ -337,7 +375,7 @@ def test_a_wrong_value_or_a_missing_setting_is_reported():
 def test_resolved_values_use_json_terms():
     assert a.resolve_setting("python:hypocurate.db.retry:RETRYABLE_SQLSTATES") == ["40001", "40P01"]
     assert a.resolve_setting("python:hypocurate.sources.record:STATUSES") == [
-        "converted", "not_reported", "not_convertible", "assigned"]
+        "converted", "not_reported", "not_convertible", "assigned_from_source", "assigned_by_decision"]
 
 
 # --- The page ----------------------------------------------------------------------------
@@ -368,7 +406,7 @@ HEADINGS = ["Open decisions", "Direction approved, pending technical review",
 def test_the_page_shows_every_entry_grouped_with_pending_states_first():
     html = signed_in().get("/assumptions").text
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
-    assert headings == HEADINGS[1:]  # no open decision since the owner decided the pairing rule (step 5)
+    assert headings == HEADINGS  # step 6 recorded two open decisions (steps 7 and 8)
     for e in REGISTER:
         assert f'id="{e["key"]}"' in html, e["key"]
     sections = re.split(r"<h2>", html)[1:]
@@ -383,9 +421,11 @@ def test_open_decisions_are_shown_first_when_there_are_any():
     headings = re.findall(r"<h2>([^<]+)</h2>", html)
     assert headings == HEADINGS
     first = re.split(r"<h2>", html)[1]
-    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["an_open_question"]
+    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["below_minimum_display", "curator_tabular_sources",
+                                                             "an_open_question"]
     assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
-    assert "1 open decision</strong>" in html
+    assert "Not decided (owner, before step 7)" in first and "Not decided (owner, before step 8)" in first
+    assert "3 open decisions</strong>" in html
     second = re.split(r"<h2>", html)[2]
     assert re.findall(r'<tbody id="([a-z0-9_]+)"', second) == ["calibration_noise_levels"]
     assert "pending: second-model technical review, before step 7" in second
@@ -396,9 +436,9 @@ def test_the_summary_line_counts_each_state_and_unreviewed_scientific_entries():
     summary = " ".join(re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1).split())
     count = {s: sum(e["state"] == s for e in REGISTER) for s in a.STATES}
     n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
-    assert count == {"in_force": len(REGISTER) - 1, "open": 0, "direction_approved": 1}
+    assert count == {"in_force": len(REGISTER) - 3, "open": 2, "direction_approved": 1}
     assert f"{len(REGISTER)} entries: {count['in_force']} in force" in summary
-    assert "0 open decisions</strong>" in summary
+    assert "2 open decisions</strong>" in summary
     assert "1 direction approved, pending technical review</strong>" in summary
     assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
     assert html.index('id="summary"') < html.index("<h2>")
diff --git a/tests/test_controlled_duplicates.py b/tests/test_controlled_duplicates.py
index fb3f210..9bc0d98 100644
--- a/tests/test_controlled_duplicates.py
+++ b/tests/test_controlled_duplicates.py
@@ -13,7 +13,8 @@ EXTRACT = REPO_ROOT / "data/controlled_duplicates/extract.csv"
 FIXTURES = REPO_ROOT / "tests/fixtures/controlled_duplicates"
 TRUTH = FIXTURES / "truth.csv"
 # Pinned here, outside data/, so the answer file cannot change without changing a test.
-TRUTH_SHA256 = "e64b1035f0e1a69198ad690dedec73c8fdc1331b08148f8a19f8701c93861f2e"
+# Step 6 (owner, 2026-10-05): the restored survivor wording and decision C (rows 7-8 are a conflict).
+TRUTH_SHA256 = "8b293ddd4e760cc2c58e3515be5aefe6b0e9b5d3ed7d3425957fe82d1e113f7f"
 # The frozen source files: fingerprint-pinned, and not written by us, so they
 # cannot hold our answers. Everything else under data/ is scanned.
 FROZEN_SOURCE_FILES = {
@@ -162,7 +163,7 @@ def test_every_case_is_present_twice():
         "exact_duplicate_verbatim": 2,
         "exact_duplicate_renamed_alloy": 2,
         "possible_duplicate_unknown_paper": 2,
-        "not_duplicate_value_differs": 2,
+        "conflict_value_differs": 2,
         "not_duplicate_other_paper": 2,
         "not_duplicate_other_temperature": 2,
         "missing_test_condition": 2,
@@ -230,7 +231,7 @@ def test_changed_values_are_as_stated():
     ys, temp = COL["PROPERTY: YS (MPa)"], COL["PROPERTY: Test temperature ($^\\circ$C)"]
     for t in TRUTH_ROWS:
         src, row = MPEA_ROWS[int(t["mpea_row"])], EXTRACT_ROWS[int(t["extract_row"]) - 1]
-        if t["case"] == "not_duplicate_value_differs":
+        if t["case"] == "conflict_value_differs":
             assert float(row[ys]) == pytest.approx(1.3 * float(src[ys]), abs=0.05)
         if t["case"] == "not_duplicate_other_temperature":
             assert float(row[temp]) == -196.0
@@ -283,7 +284,9 @@ EXPECTED = {
     "exact_duplicate_verbatim": ("exact_duplicate", "counted once", "none"),
     "exact_duplicate_renamed_alloy": ("exact_duplicate", "counted once", "none"),
     "possible_duplicate_unknown_paper": ("possible_duplicate", "counted once", "both counted separately"),
-    "not_duplicate_value_differs": ("not_duplicate", "both enter", "none"),
+    # Decision C (owner, 2026-10-05; corrects PRD 5.3, which contradicted CLAUDE.md rule 4).
+    "conflict_value_differs": ("conflict", "neither enters: conflict unresolved",
+                               "counted once in conflicts_survivor_value"),
     "not_duplicate_other_paper": ("not_duplicate", "both enter", "none"),
     "not_duplicate_other_temperature": ("not_duplicate", "not eligible under a room-temperature plan", "none"),
     "missing_test_condition": ("possible_duplicate", "not eligible: scope not confirmed", "included"),
@@ -292,7 +295,7 @@ EXPECTED = {
 }
 
 SURVIVOR_RULE = (
-    "1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); "
+    "1) prefer the record that carries the original paper reference (DOI); "
     "2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; "
     "3) within one source, the lowest row number"
 )
@@ -330,5 +333,10 @@ def test_survivor_is_stated(t):
         else:
             assert row[doi] == src[doi]
             assert t["survivor_reason"].startswith("rule 2:")  # both carry it; MPEA is first in order
+    elif t["duplicate_status"] == "conflict":
+        # Decision C: neither enters the primary analysis; the sensitivity analysis counts the
+        # pair once by the survivor rule (both carry the paper's DOI; MPEA is first in order).
+        assert t["survivor_in_primary"] == "none: neither enters the primary analysis"
+        assert "conflicts_survivor_value" in t["survivor_reason"] and "rule 2:" in t["survivor_reason"]
     else:
         assert t["survivor_in_primary"] == "no pair: both kept"
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index 29cdb6f..61af868 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -6,7 +6,7 @@ import pytest
 from sqlalchemy.exc import IntegrityError
 
 from hypocurate.db.models import MAX_FILE_BYTES
-from model_builder import FP, World, files_digest, sha
+from model_builder import EXTRACTION, FP, World, files_digest, sha
 
 
 @pytest.fixture
@@ -553,11 +553,13 @@ def test_every_record_names_its_origin(w):
     """Owner decision, question 7: source version plus the row it came from, so the
     same source row can be matched across runs."""
     rid = w.locked()
-    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported) "
-               "VALUES (:r, :sv, '', 'measured', '{}', '{}')", "ck_record_item_key_not_empty",
-               r=rid, sv=w.version["mpea"])
-    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported) "
-               "VALUES (:r, :sv, 'measured', '{}', '{}')", "source_item_key", r=rid, sv=w.version["mpea"])
+    # Each insert states its extraction (step 6), so that it reaches the check it is about.
+    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported, "
+               "extraction) VALUES (:r, :sv, '', 'measured', '{}', '{}', CAST(:x AS jsonb))", "ck_record_item_key_not_empty",
+               r=rid, sv=w.version["mpea"], x=EXTRACTION)
+    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported, extraction) "
+               "VALUES (:r, :sv, 'measured', '{}', '{}', CAST(:x AS jsonb))", "source_item_key", r=rid, sv=w.version["mpea"],
+               x=EXTRACTION)
     w.record(rid, key="row-7")
     with pytest.raises(IntegrityError, match="uq_record_origin_per_run"):
         w.record(rid, key="row-7")
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index b5ee189..30cc08e 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -75,7 +75,9 @@ def assert_schema_is_head(engine):
             "SELECT conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
             "WHERE n.nspname = 'public' AND contype = 'c'"))}
         domains = conn.execute(text("SELECT key FROM domain ORDER BY key")).scalars().all()
+        approved_tags = conn.execute(text("SELECT count(*) FROM tag_value WHERE status = 'approved'")).scalar()
     assert db_checks == model_check_names()
+    assert approved_tags == 19  # migration 0002 (step 6)
     s = snapshot(engine)
     assert {(t, n) for t, n, _ in s["triggers"]} == expected_triggers()
     assert {v for v, _ in s["views"]} == set(MIGRATION.VIEW_NAMES)
@@ -95,13 +97,26 @@ def assert_schema_is_empty(engine):
 
 # --- revisions ------------------------------------------------------------------------
 
+# Revisions that only insert rows, whose downgrade leaves the rows (owner, 2026-10-05): tag
+# values can never be deleted. Their downgrade is tested by behaviour in test_migrations_step6.py.
+DATA_ONLY = {"0002"}
+
+
 def test_exactly_one_head_and_every_revision_has_a_downgrade():
     scripts = ScriptDirectory(str(migrate.MIGRATIONS))
     assert len(scripts.get_heads()) == 1
+    revisions = {rev.revision for rev in scripts.walk_revisions()}
+    assert DATA_ONLY <= revisions
     for rev in scripts.walk_revisions():
         source = Path(rev.path).read_text()
         body = source.split("def downgrade() -> None:", 1)[1]
-        assert "drop" in body.lower(), rev.revision
+        if rev.revision in DATA_ONLY:
+            # A data-only revision: its upgrade changes no schema, and its downgrade does nothing.
+            upgrade = source.split("def upgrade() -> None:", 1)[1].split("def downgrade", 1)[0]
+            assert not re.search(r"op\.(create|add|drop|alter)_", upgrade), rev.revision
+            assert "op." not in body and body.strip().startswith('"""'), rev.revision
+        else:
+            assert "drop" in body.lower(), rev.revision
 
 
 def test_migrations_stay_inside_the_one_transaction():
diff --git a/tests/test_reference_counts_from_adapters.py b/tests/test_reference_counts_from_adapters.py
index 88708f7..39f4ff7 100644
--- a/tests/test_reference_counts_from_adapters.py
+++ b/tests/test_reference_counts_from_adapters.py
@@ -27,7 +27,7 @@ REPO = Path(__file__).resolve().parents[1]
 
 def value(record, field):
     v = record.harmonized[field]
-    return v.value if v.status in ("converted", "assigned") else None
+    return v.value if v.status in ("converted", "assigned_from_source", "assigned_by_decision") else None
 
 
 def at_least_two_grain_sizes(records):
diff --git a/tests/test_source_connection.py b/tests/test_source_connection.py
index e623164..c8e6e40 100644
--- a/tests/test_source_connection.py
+++ b/tests/test_source_connection.py
@@ -41,8 +41,14 @@ def test_it_returns_sample_records_in_the_common_format(registered, key, total):
 def test_assigned_values_are_shown_with_their_citation(registered):
     report = connection.test_connection(registered, "tamu_fcc", n=1).to_json()
     test_type = report["sample"][0]["harmonized"]["test_type"]
-    assert test_type["status"] == "assigned" and "Quasistatic tensile testing" in test_type["citation"]["quote"]
-    assert report["status_counts"]["assigned"] == 94 * 2
+    assert test_type["status"] == "assigned_from_source"
+    assert "Quasistatic tensile testing" in test_type["citation"]["quote"]
+    band = report["sample"][0]["harmonized"]["test_temperature_band"]
+    assert band["status"] == "assigned_by_decision" and "'tamu_test_temperature'" in band["citation"]["location"]
+    # Two fields from the source and two by decision, for each of the 94 records (step 6).
+    assert report["status_counts"]["assigned_from_source"] == 94 * 2
+    assert report["status_counts"]["assigned_by_decision"] == 94 * 2
+    assert "assigned" not in report["status_counts"]
 
 
 def test_it_needs_a_sealed_version(db):
@@ -75,6 +81,6 @@ def test_the_command_line(db, migrated_database, monkeypatch, capsys):
     assert cli.main(["sources", "test", "tamu_fcc", "-n", "2"]) == 0
     shown = json.loads(capsys.readouterr().out)
     assert shown["records_read"] == 94 and len(shown["sample"]) == 2
-    assert shown["sample"][0]["harmonized"]["test_type"]["status"] == "assigned"
+    assert shown["sample"][0]["harmonized"]["test_type"]["status"] == "assigned_from_source"
     assert cli.main(["sources", "register", "nope"]) == 1
     assert "unknown source" in capsys.readouterr().err
```

## 11. The step 1 answer file, builder and README (diffs)

The frozen extract (`data/controlled_duplicates/extract.csv`) is unchanged.

```diff
diff --git a/tests/fixtures/controlled_duplicates/README.md b/tests/fixtures/controlled_duplicates/README.md
index 9909022..99af2e6 100644
--- a/tests/fixtures/controlled_duplicates/README.md
+++ b/tests/fixtures/controlled_duplicates/README.md
@@ -18,7 +18,7 @@ All 16 source rows are among the records eligible under the reference plan, from
 | 1–2 | `exact_duplicate_verbatim` | nothing (byte-for-byte copy) | yes | counted once | none |
 | 3–4 | `exact_duplicate_renamed_alloy` | formula written differently (`CoCrFeMnNi`, `Co4Cr1Ni4`); same atomic % | yes | counted once | none |
 | 5–6 | `possible_duplicate_unknown_paper` | reference ID, DOI, year, title blanked | possible: flagged, kept, not removed | counted once | both counted separately |
-| 7–8 | `not_duplicate_value_differs` | yield strength × 1.3 | no | both enter | none |
+| 7–8 | `conflict_value_differs` | yield strength × 1.3 | conflict: the same measurement reported with values beyond the tolerance | neither enters (decision C, owner 2026-10-05) | counted once by the survivor rule in `conflicts_survivor_value` |
 | 9–10 | `not_duplicate_other_paper` | DOI → constructed `10.5555/hypocurate-test-…` | no | both enter | none |
 | 11–12 | `not_duplicate_other_temperature` | 25 °C → −196 °C | no (conditions differ) | not eligible under a room-temperature plan | none |
 | 13–14 | `missing_test_condition` | test temperature blanked | possible (conditions cannot be confirmed); kept, not removed | not eligible: scope not confirmed | included |
@@ -32,8 +32,8 @@ Every row is kept in the store and none is removed.
 
 ## Which record survives in the primary analysis
 
-Owner's decision, 2026-10-04, refining PRD 5.3:
-1. Prefer the record that comes directly from the original paper. This is detected by the original paper's DOI on the record.
+Owner's decision, 2026-10-04, refining PRD 5.3 (rule 1 in the owner's wording, restored in step 6; register entry 'duplicate_survivor_rule'):
+1. Prefer the record that carries the original paper reference (DOI). A DOI identifies the cited paper, not where a record was extracted.
 2. If both or neither do, take the first source in the fixed order: MPEA, Texas A&M, controlled extract.
 3. Within one source, take the lowest row number.
 
@@ -41,13 +41,15 @@ For every duplicate and possible-duplicate row in this extract, the MPEA record
 - rows 1–4 and 13–14 by rule 2: both records carry the paper's DOI, and MPEA comes first in the fixed order (rows 13–14 are not eligible anyway);
 - rows 5–6 by rule 1: only the MPEA record carries the paper's DOI.
 
-No pair here lets a source other than MPEA survive. The behavioural tests in step 6 need one that does.
+Rows 7–8 are a conflict (decision C, owner 2026-10-05): neither enters the primary analysis; the sensitivity analysis `conflicts_survivor_value` counts each pair once, the MPEA record by rule 2.
+
+No pair here lets a source other than MPEA survive. The step 6 tests add constructed records in which one does (`tests/test_eligibility.py`): the extract record wins by rule 1, and a Texas A&M record wins over an extract record by rule 2.
 
 `truth.csv` gives the survivor and the reason for each row.
 
-## Open question (owner)
+## Permitted test types (decided)
 
-The reference plan's 77 MPEA records include one compression test (MPEA row 139). The reference plan does not yet state its permitted test types, and membership in that result set must not define the rule. The plan must state them explicitly before eligibility is implemented in step 6. This is pending the owner's decision. Rows 15–16 give the expected handling both ways: under the reference plan as it stands (no test-type rule), and under a tension-only plan.
+The owner decided on 2026-10-05 that the reference plan accepts tension tests only (register entry 'permitted_test_types'), which removes MPEA row 139 (a compression test) from its primary analysis. For rows 15–16 the column `handling_under_tension_only_plan` therefore gives the handling under today's reference plan; the columns `prd_5_3_class` and `primary_analysis` still describe the step 1 plan without a test-type rule. Aligning them is an open item for the owner (step 6 summary).
 
 ## Rebuilding
 
diff --git a/tests/fixtures/controlled_duplicates/build.py b/tests/fixtures/controlled_duplicates/build.py
index ceabdf9..eb44644 100644
--- a/tests/fixtures/controlled_duplicates/build.py
+++ b/tests/fixtures/controlled_duplicates/build.py
@@ -50,20 +50,28 @@ NOT_REMOVED = "no"
 
 # Owner's decision (2026-10-04): which record of a duplicate pair enters the
 # primary analysis. Refines PRD 5.3 "the record from the original paper, or the
-# first source in a fixed order if the origin is unknown". Whether a record comes
-# directly from the original paper is detected by the original paper's DOI on it.
+# first source in a fixed order if the origin is unknown". Rule 1 in the owner's own
+# wording, restored in step 6 (register 'duplicate_survivor_rule'): a DOI identifies the
+# cited paper, not where a record was extracted.
 SURVIVOR_RULE = (
-    "1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); "
+    "1) prefer the record that carries the original paper reference (DOI); "
     "2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; "
     "3) within one source, the lowest row number"
 )
 BOTH_CARRY_PAPER = (
-    "rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes "
-    "directly from it; MPEA comes first in the fixed source order"
+    "rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order"
 )
 ONLY_MPEA_CARRIES_PAPER = (
-    "rule 1: only the MPEA record carries the original paper's DOI, so it is detected as the one that "
-    "comes directly from the original paper"
+    "rule 1: only the MPEA record carries the original paper reference (DOI)"
+)
+# Owner's decision C (2026-10-05): conflicting reports of the same measurement are kept and
+# flagged; neither enters the primary analysis (code does not choose between them). The
+# sensitivity analysis 'conflicts_survivor_value' counts the pair once by the survivor rule.
+NEITHER = "none: neither enters the primary analysis"
+CONFLICT = (
+    "conflict: the values differ beyond the tolerance and code does not choose between them; in the "
+    "sensitivity analysis 'conflicts_survivor_value' the pair is counted once by the survivor rule: "
+    + BOTH_CARRY_PAPER
 )
 NO_PAIR = "no pair: both kept"
 SAME_AS_REFERENCE_PLAN = "same as under the reference plan"
@@ -111,13 +119,14 @@ CASES = {
         pair=BOTH_CARRY_PAPER + "; this record is not eligible in any case (scope not confirmed)",
         explanation="Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis.",
     ),
-    "not_duplicate_value_differs": dict(
-        duplicate_status="not_duplicate",
-        prd_class="Comparable specimens and conditions; the values truly differ",
-        primary_analysis="both enter",
-        sensitivity_analysis="none",
-        pair=None,
-        explanation="Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate.",
+    "conflict_value_differs": dict(
+        duplicate_status="conflict",
+        prd_class="Conflicting reports of the same measurement: the values differ beyond the tolerance",
+        primary_analysis="neither enters: conflict unresolved",
+        sensitivity_analysis="counted once in conflicts_survivor_value",
+        pair=CONFLICT,
+        survivor=NEITHER,
+        explanation="Same paper, alloy, grain size and conditions reported by two sources, but yield strength is 30% higher: conflicting reports of the same measurement. Both are kept and flagged, and neither enters the primary analysis (owner, 2026-10-05). Matching alloy and grain size alone would not make them the same measurement.",
     ),
     "not_duplicate_other_paper": dict(
         duplicate_status="not_duplicate",
@@ -159,8 +168,8 @@ SPEC: list[tuple[str, int, dict[int, str]]] = [
     ("exact_duplicate_renamed_alloy", 1007, {FORMULA: "Co4Cr1Ni4"}),
     ("possible_duplicate_unknown_paper", 998, {REF_ID: "", DOI: "", YEAR: "", TITLE: ""}),
     ("possible_duplicate_unknown_paper", 1085, {REF_ID: "", DOI: "", YEAR: "", TITLE: ""}),
-    ("not_duplicate_value_differs", 1278, {YS: "665.6"}),  # 512.0 x 1.3
-    ("not_duplicate_value_differs", 986, {YS: "282.1"}),  # 217.0 x 1.3
+    ("conflict_value_differs", 1278, {YS: "665.6"}),  # 512.0 x 1.3
+    ("conflict_value_differs", 986, {YS: "282.1"}),  # 217.0 x 1.3
     ("not_duplicate_other_paper", 1035, {REF_ID: "", DOI: TEST_DOI_PREFIX + "0001", TITLE: CONSTRUCTED_TITLE}),
     ("not_duplicate_other_paper", 764, {REF_ID: "", DOI: TEST_DOI_PREFIX + "0002", TITLE: CONSTRUCTED_TITLE}),
     ("not_duplicate_other_temperature", 1313, {TEMPERATURE: "-196.0"}),
@@ -178,7 +187,7 @@ TRUTH_COLUMNS = [
     "mpea_reference_id",
     "mpea_doi",
     "changed_columns",  # MPEA header names, separated by "; "
-    "duplicate_status",  # exact_duplicate | possible_duplicate | not_duplicate
+    "duplicate_status",  # exact_duplicate | possible_duplicate | conflict | not_duplicate
     "prd_5_3_class",
     "kept_in_store",
     "removed_from_store",
@@ -226,7 +235,7 @@ def build(mpea_path: Path = MPEA_PATH) -> tuple[str, str]:
         if c["pair"] is None:
             survivor, reason = NO_PAIR, NOT_SAME_MEASUREMENT
         else:
-            survivor, reason = f"MPEA row {row}", c["pair"]
+            survivor, reason = c.get("survivor", f"MPEA row {row}"), c["pair"]
         truth.append(_csv_line([
             str(n),
             case,
diff --git a/tests/fixtures/controlled_duplicates/truth.csv b/tests/fixtures/controlled_duplicates/truth.csv
index e73ad80..4991812 100644
--- a/tests/fixtures/controlled_duplicates/truth.csv
+++ b/tests/fixtures/controlled_duplicates/truth.csv
@@ -1,17 +1,17 @@
 extract_row,case,mpea_row,mpea_reference_id,mpea_doi,changed_columns,duplicate_status,prd_5_3_class,kept_in_store,removed_from_store,primary_analysis,sensitivity_analysis,handling_under_tension_only_plan,survivor_in_primary,survivor_reason,survivor_rule,explanation
-1,exact_duplicate_verbatim,1315,252,10.1007/s11661-019-05231-y,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1315,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
-2,exact_duplicate_verbatim,812,144,10.1016/j.ijplas.2018.10.005,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 812,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
-3,exact_duplicate_renamed_alloy,1316,252,10.1007/s11661-019-05231-y,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1316,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
-4,exact_duplicate_renamed_alloy,1007,208,10.1016/j.actamat.2019.04.017,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1007,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
-5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 998,"rule 1: only the MPEA record carries the original paper's DOI, so it is detected as the one that comes directly from the original paper","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
-6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 1085,"rule 1: only the MPEA record carries the original paper's DOI, so it is detected as the one that comes directly from the original paper","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
-7,not_duplicate_value_differs,1278,248,10.1016/j.msea.2019.138039,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
-8,not_duplicate_value_differs,986,204,10.1016/j.intermet.2019.106477,PROPERTY: YS (MPa),not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions, but yield strength is 30% higher. Matching alloy and grain size is not enough to be a duplicate."
-9,not_duplicate_other_paper,1035,211,10.1016/j.msea.2019.04.025,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
-10,not_duplicate_other_paper,764,98,10.1016/j.actamat.2018.12.015,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
-11,not_duplicate_other_temperature,1313,252,10.1007/s11661-019-05231-y,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
-12,not_duplicate_other_temperature,1086,221,10.1016/j.msea.2018.12.077,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
-13,missing_test_condition,1036,211,10.1016/j.msea.2019.04.025,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 1036,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed)","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
-14,missing_test_condition,813,144,10.1016/j.ijplas.2018.10.005,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 813,"rule 2: both records carry the original paper's DOI, so neither is detected as the one that comes directly from it; MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed)","1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
-15,not_duplicate_other_test_type,1004,208,10.1016/j.actamat.2019.04.017,PROPERTY: Type of test,not_duplicate,"Within scope under the reference plan: distinct measurements, not duplicates",yes,no,both enter under the reference plan (it sets no test-type rule),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
-16,not_duplicate_other_test_type,765,98,10.1016/j.actamat.2018.12.015,PROPERTY: Type of test,not_duplicate,"Within scope under the reference plan: distinct measurements, not duplicates",yes,no,both enter under the reference plan (it sets no test-type rule),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that comes directly from the original paper (detected by the original paper's DOI on the record); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
+1,exact_duplicate_verbatim,1315,252,10.1007/s11661-019-05231-y,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1315,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
+2,exact_duplicate_verbatim,812,144,10.1016/j.ijplas.2018.10.005,,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 812,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Byte-for-byte copy of the MPEA row: same paper, alloy, grain size, value and test conditions."
+3,exact_duplicate_renamed_alloy,1316,252,10.1007/s11661-019-05231-y,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1316,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
+4,exact_duplicate_renamed_alloy,1007,208,10.1016/j.actamat.2019.04.017,FORMULA,exact_duplicate,Exact duplicate: the same measurement reported by two sources,yes,no,counted once,none,same as under the reference plan,MPEA row 1007,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same measurement with the formula written in another notation; the composition in atomic percent is identical, so matching must use the normalized composition."
+5,possible_duplicate_unknown_paper,998,208,10.1016/j.actamat.2019.04.017,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 998,rule 1: only the MPEA record carries the original paper reference (DOI),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
+6,possible_duplicate_unknown_paper,1085,221,10.1016/j.msea.2018.12.077,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: year; REFERENCE: title,possible_duplicate,Possible duplicate that cannot be resolved,yes,no,counted once,both counted separately,same as under the reference plan,MPEA row 1085,rule 1: only the MPEA record carries the original paper reference (DOI),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and test conditions, but the paper reference is blank, so it cannot be confirmed as the same measurement. Flagged as a possible duplicate, kept, not removed."
+7,conflict_value_differs,1278,248,10.1016/j.msea.2019.138039,PROPERTY: YS (MPa),conflict,Conflicting reports of the same measurement: the values differ beyond the tolerance,yes,no,neither enters: conflict unresolved,counted once in conflicts_survivor_value,same as under the reference plan,none: neither enters the primary analysis,conflict: the values differ beyond the tolerance and code does not choose between them; in the sensitivity analysis 'conflicts_survivor_value' the pair is counted once by the survivor rule: rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions reported by two sources, but yield strength is 30% higher: conflicting reports of the same measurement. Both are kept and flagged, and neither enters the primary analysis (owner, 2026-10-05). Matching alloy and grain size alone would not make them the same measurement."
+8,conflict_value_differs,986,204,10.1016/j.intermet.2019.106477,PROPERTY: YS (MPa),conflict,Conflicting reports of the same measurement: the values differ beyond the tolerance,yes,no,neither enters: conflict unresolved,counted once in conflicts_survivor_value,same as under the reference plan,none: neither enters the primary analysis,conflict: the values differ beyond the tolerance and code does not choose between them; in the sensitivity analysis 'conflicts_survivor_value' the pair is counted once by the survivor rule: rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and conditions reported by two sources, but yield strength is 30% higher: conflicting reports of the same measurement. Both are kept and flagged, and neither enters the primary analysis (owner, 2026-10-05). Matching alloy and grain size alone would not make them the same measurement."
+9,not_duplicate_other_paper,1035,211,10.1016/j.msea.2019.04.025,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
+10,not_duplicate_other_paper,764,98,10.1016/j.actamat.2018.12.015,IDENTIFIER: Reference ID; REFERENCE: doi; REFERENCE: title,not_duplicate,Comparable specimens and conditions; the values truly differ,yes,no,both enter,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same alloy, grain size, value and conditions, but attributed to a different (constructed) paper. Duplicates must come from the same original paper."
+11,not_duplicate_other_temperature,1313,252,10.1007/s11661-019-05231-y,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
+12,not_duplicate_other_temperature,1086,221,10.1016/j.msea.2018.12.077,PROPERTY: Test temperature ($^\circ$C),not_duplicate,Incompatible measurements: outside the plan's scope,yes,no,not eligible under a room-temperature plan,none,same as under the reference plan,no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is -196 C instead of 25 C. Test conditions differ, so it is not a duplicate."
+13,missing_test_condition,1036,211,10.1016/j.msea.2019.04.025,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 1036,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
+14,missing_test_condition,813,144,10.1016/j.ijplas.2018.10.005,PROPERTY: Test temperature ($^\circ$C),possible_duplicate,Difference explained by missing metadata: scope cannot be confirmed,yes,no,not eligible: scope not confirmed,included,same as under the reference plan,MPEA row 813,rule 2: both records carry the original paper reference (DOI); MPEA comes first in the fixed source order; this record is not eligible in any case (scope not confirmed),"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size and value, but the test temperature is blank, so neither the scope (room temperature) nor the same measurement can be confirmed. Distinct from a missing paper: the paper is known, the test condition is not. Kept, not removed; not in the primary analysis; included in the sensitivity analysis."
+15,not_duplicate_other_test_type,1004,208,10.1016/j.actamat.2019.04.017,PROPERTY: Type of test,not_duplicate,"Within scope under the reference plan: distinct measurements, not duplicates",yes,no,both enter under the reference plan (it sets no test-type rule),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
+16,not_duplicate_other_test_type,765,98,10.1016/j.actamat.2018.12.015,PROPERTY: Type of test,not_duplicate,"Within scope under the reference plan: distinct measurements, not duplicates",yes,no,both enter under the reference plan (it sets no test-type rule),none,excluded by the test-type rule: outside the plan's scope (PRD 5.3 'Incompatible measurements'),no pair: both kept,not the same measurement,"1) prefer the record that carries the original paper reference (DOI); 2) if both or neither do, the first source in the fixed order MPEA, Texas A&M, controlled extract; 3) within one source, the lowest row number","Same paper, alloy, grain size, value and temperature, but a compression test instead of tension. The test conditions are known to differ, so it is not a duplicate and not a possible duplicate. The reference plan sets no test-type rule, so both enter; a plan restricted to tension would exclude this record as out of scope."
```

## 12. README (diff)

```diff
diff --git a/README.md b/README.md
index 072f7db..0824dd1 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,7 @@ HypoCurate takes a scientific hypothesis in words, searches registered data sour
 
 ## Status
 
-Build step 5 of 12 (PRD Section 15): the access layer. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), plus the access layer with its audit log and the file guard for pipeline processes (step 5). The pipeline, the agents and the screens come in later steps.
+Build step 6 of 12 (PRD Section 15): the plan, the two checkpoints, inclusion and checks. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), the access layer with its audit log and the file guard for pipeline processes (step 5), plus the plan model, the rules lock, record storage, the code checks that raise flags, the eligibility decisions and the dataset freeze (step 6). The statistics, the agents and the screens come in later steps.
 
 ## Set up secrets (once)
 
@@ -139,9 +139,28 @@ hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common re
 - The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
 - Not yet run on the live database: registering there is a later step and needs the owner.
 
+## Plan, checkpoints, inclusion and checks
+
+Code in `hypocurate/pipeline/` (step 6; PRD 5). No agent and no model call: plans are fixed inputs.
+
+```python
+from hypocurate.pipeline import checkpoints, checks, extract, inclusion
+from hypocurate.pipeline.plan import reference_plan
+checkpoints.lock_rules(engine, run_id, reference_plan(hypothesis_version_id))  # plan, fingerprint, three tags
+extract.store_records(engine, run_id)       # each chosen source's sealed version, by its adapter
+checks.run_checks(engine, run_id)           # flags: invalid values, duplicates, conflicts
+inclusion.decide_run(engine, run_id)        # one rule per record; the primary and sensitivity sets
+checkpoints.freeze_dataset(engine, run_id)  # counts and fingerprint; or "no dataset frozen"
+```
+
+- **The plan** follows `PLAN_SCHEMA` exactly and holds every setting that affects eligibility or grouping. The default and reference plans take each value from the domain profile (`profile.py`); decision code reads settings only from the locked plan.
+- **Checks and Inclusion read through their own access objects** (`dispatch.bind_code`). Inclusion receives no outcome value.
+- **Every write** takes `hc_write_lock(p_run => …)` in `run_transaction`, re-checks by id what it read, and logs any refusal (`audit_log`, `detail.result` "rejected").
+- **Constructed test data** (the controlled extract) enter only a run marked `{"constructed_test_data": true}` in `experiment_flags` at dispatch.
+
 ## Access layer
 
-Every agent reads data only through an access object for one run, role and stage (`hypocurate/access/`; PRD 4). There is no agent yet (step 8).
+Every agent reads data only through an access object for one run, role and stage (`hypocurate/access/`; PRD 4). There is no agent yet (step 8). The code roles Inclusion and Checks (step 6) read through access objects too, bound by `dispatch.bind_code` at the curation stage only.
 
 ```python
 from hypocurate.access import bind, role_input
```

## 13. Test-side recomputation of the reference numbers

Not package code. `dump_sets.py` runs the step 6 pipeline (project environment) on a scratch database and dumps each frozen set; `fit_sets.py` fits the specified model (statsmodels 0.15.0, scipy 1.18.1, pandas 3.0.6, in a separate scratchpad environment); `no_exclusions_check.py` shows the source of the reference script's "no exclusions" figure.

### `dump_sets.py`

```python
"""Scratchpad, test side: run the step 6 pipeline on a scratch database (reference plan, MPEA and
Texas A&M, unmarked) and dump each frozen set with the values the step 7 model needs."""
import json, os, sys, uuid
sys.path.insert(0, "/workspaces/hypocurate/tests")
from sqlalchemy import make_url, text
from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from hypocurate.access.context import AccessContext
from hypocurate.access.fields import record_conditions
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline.plan import reference_plan
import pipeline_world as pw

url = [l.split("=", 1)[1].strip() for l in open("/workspaces/hypocurate/.env") if l.startswith("DATABASE_URL=")][0]
admin = make_engine(url).execution_options(isolation_level="AUTOCOMMIT")
name = f"hypocurate_t_numbers_{uuid.uuid4().hex[:8]}"
with admin.connect() as c:
    c.execute(text(f'CREATE DATABASE "{name}"'))
try:
    engine = make_engine(make_url(url).set(database=name).render_as_string(hide_password=False))
    migrate.upgrade(engine)
    pw.registered(engine, ("mpea", "tamu_fcc"))
    rid = pw.through_freeze(engine, sources=("mpea", "tamu_fcc"))
    with engine.connect() as conn:
        plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=rid)).scalar_one()
        conds = {c["id"]: c for c in record_conditions(conn, AccessContext(rid, "inclusion", "curation"))}
        values = dict(conn.execute(text("SELECT id, (harmonized->'yield_strength'->>'value')::float FROM record "
                                        "WHERE extraction_run_id = :r"), dict(r=rid)).all())
        origin = dict(conn.execute(text("SELECT id, source_item_key FROM record WHERE extraction_run_id = :r"),
                                   dict(r=rid)).all())
        sets = {}
        for key, i in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr "
                                        "ON asr.analysis_set_id = a.id WHERE a.run_id = :r"), dict(r=rid)):
            sets.setdefault(key, []).append(i)
        freeze = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'dataset_freeze'"),
                              dict(r=rid)).scalar_one()
    out = {"fingerprint": freeze["fingerprint"], "counts": freeze["counts"], "sets": {}}
    for key, ids in sorted(sets.items()):
        st = el.settings(plan, key)
        out["sets"][key] = [{"id": i, "origin": origin[i], "source": conds[i]["source"],
                             "alloy": el.alloy(conds[i], st.decimals), "group": el.group(conds[i], st),
                             "gs": conds[i]["values"]["grain_size"], "ys": values[i]} for i in sorted(ids)]
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "sets.json"), "w"), indent=1)
    print({k: len(v) for k, v in out["sets"].items()})
finally:
    engine.dispose()
    with admin.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
```
### `fit_sets.py`

```python
"""Scratchpad, test side: the supported model (PRD 5.7) on each frozen set dumped by dump_sets.py.
YS = alloy intercept + k * d^-1/2, OLS; cluster-robust SE by group with the small-sample
correction (statsmodels' default); one-sided p for k > 0 against t with (groups - 1) df.
The method of docs/reference/worked_example.py. Not package code: the statistics module is step 7."""
import json, os
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import stats

data = json.load(open(os.path.join(os.path.dirname(__file__), "sets.json")))


def fit(rows):
    d = pd.DataFrame(rows)
    sizes = d.groupby("alloy").gs.nunique()
    n, alloys, groups = len(d), d.alloy.nunique(), d.group.nunique()
    resid = n - alloys - 1
    out = {"records": n, "alloys": alloys, "groups": groups, "resid_df": resid,
           "check1": bool((sizes >= 2).any()), "check2": bool((sizes >= 2).any() and resid >= 1 and groups >= 2)}
    if not out["check1"]:
        return out
    d["x"] = d.gs ** -0.5
    formula = "ys ~ x + C(alloy)" if alloys > 1 else "ys ~ x"
    if out["check2"]:
        m = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.group)[0]})
        k, se = m.params["x"], m.bse["x"]
        out.update(k=k, se=se, p=stats.t.sf(k / se, groups - 1))
    else:
        out.update(k=smf.ols(formula, d).fit().params["x"], se=None, p=None)
    return out


def show(label, r):
    k = f"k = {r['k']:.1f}" if "k" in r else "no coefficient"
    se = f" ± {r['se']:.1f}, p = {r['p']:.2g}" if r.get("se") is not None else (" (no uncertainty, no p-value)" if "k" in r else "")
    print(f"| {label} | {r['records']} | {r['alloys']} | {r['groups']} | {r['resid_df']} | {k}{se} |")


print("fingerprint", data["fingerprint"])
print("| Set | Records | Alloys | Groups | Resid. df | Result |\n|---|---|---|---|---|---|")
primary = data["sets"]["primary"]
show("MPEA alone (primary)", fit([r for r in primary if r["source"] == "mpea"]))
show("Texas A&M alone (primary)", fit([r for r in primary if r["source"] == "tamu_fcc"]))
show("Pooled (primary)", fit(primary))
for key, rows in data["sets"].items():
    if key != "primary":
        show(key, fit(rows))
# Cross-check: the earlier reference selection is 'tension_and_compression'.
tc = data["sets"]["tension_and_compression"]
show("tension_and_compression, MPEA alone", fit([r for r in tc if r["source"] == "mpea"]))
```
Output of `fit_sets.py`:

```
fingerprint 3440e972d511ad434a516bdadedae7d8ccd26638f74dc45985c39c531919079b
| Set | Records | Alloys | Groups | Resid. df | Result |
|---|---|---|---|---|---|
| MPEA alone (primary) | 76 | 13 | 19 | 62 | k = 424.1 ± 62.2, p = 1.1e-06 |
| Texas A&M alone (primary) | 21 | 9 | 1 | 11 | k = 1173.3 (no uncertainty, no p-value) |
| Pooled (primary) | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| conflicts_survivor_value | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| no_exclusions | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| possible_duplicates_separate | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| same_alloy_1_at_pct | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| scope_not_confirmed_included | 103 | 23 | 22 | 79 | k = 432.4 ± 64.9, p = 6.7e-07 |
| six_batches_as_groups | 97 | 22 | 22 | 74 | k = 424.9 ± 64.2, p = 7.5e-07 |
| source_only_assignments | 76 | 13 | 19 | 62 | k = 424.1 ± 62.2, p = 1.1e-06 |
| tension_and_compression | 98 | 22 | 21 | 75 | k = 428.0 ± 63.5, p = 7.4e-07 |
| tension_and_compression, MPEA alone | 77 | 13 | 20 | 63 | k = 427.2 ± 61.4, p = 6.2e-07 |
```

### `no_exclusions_check.py`

```python
"""Scratchpad: which record made the reference script's 'no exclusions' 233 ± 97?"""
import json, os, re
import pandas as pd, statsmodels.formula.api as smf
from scipy import stats
d = pd.read_csv("/workspaces/hypocurate/data/sources/mpea/MPEA_dataset.csv")
d.columns = ['ref','formula','micro','proc','phase','gs','rho_exp','rho_calc','HV','test','T','YS','UTS','el','elp',
             'E_exp','E_calc','O','N','Cwt','doi','year','title']
def norm(f):
    comp = {}
    for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f): comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
    s = sum(comp.values()); return ''.join(f"{e}{round(100*v/s,1):g}" for e, v in sorted(comp.items()))
d['comp'] = d.formula.map(norm)
s = d[(d.micro == 'FCC') & d['T'].between(20, 25) & d.gs.notna() & d.YS.notna()].copy()
g = s.groupby('comp').gs.nunique(); s = s[s.comp.isin(g[g >= 2].index)]
print("below 0.1 µm:", s[s.gs < 0.1][['comp', 'gs', 'YS', 'test', 'doi']].to_string())
tamu = [r for r in json.load(open(os.path.join(os.path.dirname(__file__), "sets.json")))["sets"]["primary"]
        if r["source"] == "tamu_fcc"]
t = pd.DataFrame({"comp": [r["alloy"] for r in tamu], "gs": [r["gs"] for r in tamu], "YS": [r["ys"] for r in tamu],
                  "doi": ["tamu"] * len(tamu)})
for label, m in (("MPEA no exclusions", s), ("pooled no exclusions", pd.concat([s[['comp', 'gs', 'YS', 'doi']], t]))):
    m = m.copy(); m['x'] = m.gs ** -0.5
    f = smf.ols('YS ~ x + C(comp)', m).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(m.doi)[0]})
    print(label, len(m), round(f.params['x'], 1), round(f.bse['x'], 1),
          stats.t.sf(f.params['x'] / f.bse['x'], m.doi.nunique() - 1))
```
Output:

```
below 0.1 µm:                       comp    gs      YS test                            doi
1471  Co20Cr20Fe20Mn20Ni20  0.03  1100.0    C  10.1080/00325899.2018.1554834
MPEA no exclusions 78 232.5 93.4 0.010860466948751531
pooled no exclusions 99 232.9 96.7 0.012676038869669691
```

## 14. Mutation checks

Each safeguard removed in a scratch copy of the package; the named tests run against it (`PYTHONPATH`; the last column confirms the copy was imported).

### `mutate.py`

```python
"""Scratchpad: remove each step 6 safeguard in a copy of the package and show its tests fail."""
import os, shutil, subprocess, sys
REPO = "/workspaces/hypocurate"
S = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ)
ENV["DATABASE_URL"] = [l.split("=", 1)[1].strip() for l in open(f"{REPO}/.env") if l.startswith("DATABASE_URL=")][0]

MUTATIONS = [
    ("constructed-data guard off", "hypocurate/pipeline/writes.py",
     "    if not any(SOURCES[k].constructed for k in source_keys if k in SOURCES):\n        return False",
     "    return False", ["tests/test_checkpoints.py"]),
    ("bind_code accepts any role", "hypocurate/access/dispatch.py",
     "named = role if isinstance(role, str) and role in CODE_ROLES else UNBOUND", "named = role",
     ["tests/test_access_code_roles.py"]),
    ("Inclusion receives all values", "hypocurate/access/allowlist.py",
     '"inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind"})}),',
     '"inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind", "records_full"})}),',
     ["tests/test_access_code_roles.py"]),
    ("record_conditions carries the outcome value", "hypocurate/access/fields.py",
     '"values": {f: _number(h.get(f)) for f in CONDITION_NUMBERS if f not in OUTCOME_FIELDS},',
     '"values": {f: _number(h.get(f)) for f in CONDITION_NUMBERS + ("yield_strength",)},',
     ["tests/test_access_code_roles.py"]),
    ("checks does not re-check the records it read", "hypocurate/pipeline/checks.py",
     "        if record_ids(conn, run_id) != read_ids:\n            raise Refused(\"raise_flags\", \"changed_since_read\")\n",
     "", ["tests/test_checkpoints.py"]),
    ("inclusion does not re-check what it read", "hypocurate/pipeline/inclusion.py",
     "        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:\n            raise Refused(\"decide\", \"changed_since_read\")\n",
     "", ["tests/test_checkpoints.py"]),
    ("grain sizes counted before duplicates", "hypocurate/pipeline/eligibility.py",
     "        if r[\"id\"] not in rules:\n            sizes[alloy(r, st.decimals)].add(r[\"values\"][st.predictor])",
     "        if r[\"id\"] not in rules or rules[r[\"id\"]] == \"duplicate_counted_once\":\n            sizes[alloy(r, st.decimals)].add(r[\"values\"][st.predictor])",
     ["tests/test_eligibility.py"]),
    ("scope rule after the duplicate rule (order 5/7)", "hypocurate/pipeline/eligibility.py",
     "        elif sc == \"unconfirmed\" and not st.scope_unconfirmed_ok:\n            rules[r[\"id\"]] = \"scope_not_confirmed\"\n",
     "", ["tests/test_eligibility.py", "tests/test_controlled_duplicates_handling.py"]),
    ("grain size compared exactly, not within the tolerance", "hypocurate/pipeline/flags.py",
     "if None in (ga, gb, ya, yb) or relative_difference(ga, gb) > tol:", "if None in (ga, gb, ya, yb) or ga != gb:",
     ["tests/test_flags.py"]),
    ("tolerance fixed in code, not from the plan", "hypocurate/pipeline/flags.py",
     'tol, outcome = plan["rules"]["duplicate_tolerance"], plan["variables"]["outcome"]["field"]',
     'tol, outcome = 0.02, plan["variables"]["outcome"]["field"]', ["tests/test_flags.py"]),
    ("minimum grain sizes from the profile, not the plan", "hypocurate/pipeline/eligibility.py",
     'min_grain_sizes=r["min_grain_sizes"],', 'min_grain_sizes=__import__("hypocurate.pipeline.profile", fromlist=["x"]).MIN_GRAIN_SIZES_PER_ALLOY,',
     ["tests/test_eligibility.py"]),
    ("rows within one source compared", "hypocurate/pipeline/flags.py",
     'if a["source"] != b["source"]:', 'if True:', ["tests/test_flags.py"]),
    ("an ambiguous group paired anyway", "hypocurate/pipeline/flags.py",
     "if len(set(sources)) < len(sources) or len(pairs) < len(ids) * (len(ids) - 1) // 2:", "if False:",
     ["tests/test_flags.py"]),
    ("a conflict enters with both records", "hypocurate/pipeline/eligibility.py",
     'if rule in ("identity_unresolved", "conflict_unresolved"):', 'if rule in ("identity_unresolved",):',
     ["tests/test_eligibility.py", "tests/test_controlled_duplicates_handling.py"]),
    ("survivor rule 1 ignored", "hypocurate/pipeline/eligibility.py",
     'return (0 if rec["has_doi"] else 1, order,', 'return (0, order,', ["tests/test_eligibility.py"]),
    ("write path without hc_write_lock", "hypocurate/pipeline/writes.py",
     'status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()',
     'status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()',
     ["tests/test_checkpoints.py"]),
    ("refusals not logged", "hypocurate/pipeline/writes.py",
     "    try:\n        run_transaction(engine, write)\n    except Exception as error:",
     "    try:\n        pass\n    except Exception as error:", ["tests/test_checkpoints.py"]),
    ("freeze does not re-check the records it read", "hypocurate/pipeline/checkpoints.py",
     "        if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:\n            raise Refused(\"freeze_dataset\", \"changed_since_read\")",
     "", ["tests/test_checkpoints.py"]),
    ("freeze accepts decisions the rules do not produce", "hypocurate/pipeline/checkpoints.py",
     "if stored != sets[el.PRIMARY] or _set_records(conn, run_id) != members:", "if False:",
     ["tests/test_checkpoints.py"]),
    ("a second lock not refused by our path", "hypocurate/pipeline/checkpoints.py",
     '            raise Refused("lock_rules", "already_done" if stage != "none" else "stage_mismatch")', "            pass",
     ["tests/test_checkpoints.py"]),
    ("0003 trigger without the extraction requirement", "hypocurate/db/migrations/versions/0003_record_extraction.py",
     "        IF NEW.extraction IS NULL THEN\n            PERFORM hc_reject('a record states how it was extracted (adapter or agent, with name and version)');\n        END IF;\n",
     "", ["tests/test_migrations_step6.py"]),
    ("plan validation accepts free text", "hypocurate/pipeline/plan.py",
     "    if project(content, PLAN_SCHEMA) != content:", "    if False:", ["tests/test_plan.py"]),
    ("TAMU band not assigned (not reported)", "hypocurate/sources/adapters/tamu_fcc.py",
     'h["test_temperature_band"] = Value("room temperature", None, "assigned_by_decision",\n                                       citation=TEMPERATURE_DECISION)',
     'h["test_temperature_band"] = Value(None, None, "not_reported", TEMPERATURE_NOT_REPORTED)',
     ["tests/test_reference_sets.py", "tests/test_adapter_tamu.py"]),
]

results = []
only = sys.argv[1:]
for name, path, old, new, tests in MUTATIONS:
    if only and not any(o in name for o in only):
        continue
    copy = os.path.join(S, "mut")
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(os.path.join(REPO, "hypocurate"), os.path.join(copy, "hypocurate"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.symlink(os.path.join(REPO, "data"), os.path.join(copy, "data"))
    target = os.path.join(copy, path)
    src = open(target).read()
    assert src.count(old) == 1, (name, src.count(old))
    open(target, "w").write(src.replace(old, new))
    env = dict(ENV, PYTHONPATH=copy)
    out = subprocess.run([f"{REPO}/.venv/bin/pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=REPO, env=env,
                         capture_output=True, text=True)
    last = [l for l in out.stdout.splitlines() if " passed" in l or " failed" in l or "error" in l.lower()][-1:]
    check = subprocess.run([f"{REPO}/.venv/bin/python", "-c", "import hypocurate,sys;print(hypocurate.__file__)"],
                           env=env, capture_output=True, text=True, cwd=S).stdout.strip()
    results.append((name, last[0] if last else out.stdout[-300:], check.startswith(copy)))
    print(f"{name}: {results[-1][1]}  (imports the copy: {results[-1][2]})", flush=True)
shutil.rmtree(os.path.join(S, "mut"), ignore_errors=True)
```
Output:

```
constructed-data guard off: 1 failed, 16 passed in 27.66s  (imports the copy: True)
bind_code accepts any role: 1 failed, 11 passed in 6.46s  (imports the copy: True)
Inclusion receives all values: 2 failed, 10 passed in 6.38s  (imports the copy: True)
record_conditions carries the outcome value: 3 failed, 9 passed in 6.40s  (imports the copy: True)
checks does not re-check the records it read: 1 failed, 16 passed in 28.33s  (imports the copy: True)
inclusion does not re-check what it read: 1 failed, 16 passed in 28.75s  (imports the copy: True)
grain sizes counted before duplicates: 1 failed, 35 passed in 0.49s  (imports the copy: True)
scope rule after the duplicate rule (order 5/7): 7 failed, 79 passed in 4.84s  (imports the copy: True)
grain size compared exactly, not within the tolerance: 2 failed, 16 passed in 0.33s  (imports the copy: True)
tolerance fixed in code, not from the plan: 1 failed, 17 passed in 0.33s  (imports the copy: True)
minimum grain sizes from the profile, not the plan: 2 failed, 34 passed in 0.36s  (imports the copy: True)
rows within one source compared: 2 failed, 16 passed in 0.42s  (imports the copy: True)
an ambiguous group paired anyway: 3 failed, 15 passed in 0.33s  (imports the copy: True)
a conflict enters with both records: 4 failed, 82 passed in 4.48s  (imports the copy: True)
survivor rule 1 ignored: 1 failed, 35 passed in 0.34s  (imports the copy: True)
write path without hc_write_lock: 1 failed, 16 passed in 28.61s  (imports the copy: True)
refusals not logged: 9 failed, 8 passed in 27.42s  (imports the copy: True)
freeze does not re-check the records it read: 1 failed, 16 passed in 28.62s  (imports the copy: True)
freeze accepts decisions the rules do not produce: 2 failed, 15 passed in 27.23s  (imports the copy: True)
a second lock not refused by our path: 1 failed, 16 passed in 28.28s  (imports the copy: True)
0003 trigger without the extraction requirement: 2 failed, 5 passed in 3.54s  (imports the copy: True)
plan validation accepts free text: 5 failed, 19 passed in 0.40s  (imports the copy: True)
TAMU band not assigned (not reported): 6 failed, 16 passed in 8.83s  (imports the copy: True)
```
