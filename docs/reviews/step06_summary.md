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

## The owner's decisions after the first build (2026-10-06)

1. **The recomputed reference numbers are approved.** CLAUDE.md's "Reference numbers" now state them. A new register entry, `reference_numbers` (statistical; decided by the owner on 2026-10-06; partly applied), holds them, with the earlier values (98 / 77 records, k = 428 ± 64 and 427 ± 61) in its history. The statistics module in step 7 must reproduce them independently: the step 6 values come from a test-side script, not from package code. The record counts are regression tests already; the coefficients become tests in step 7.
2. **The answer file's rows 15–16** now describe the reference plan with its test-type rule. In both rows:
   - `prd_5_3_class` "Within scope under the reference plan: distinct measurements, not duplicates" → "Incompatible measurements: outside the plan's scope (test-type rule: tension only)";
   - `primary_analysis` "both enter under the reference plan (it sets no test-type rule)" → "not eligible: excluded by the test-type rule (tension only)".
   The pinned fingerprint is updated (`8ff53837…`), and the extract is unchanged. The rows' `explanation` cells still describe the step 1 plan; they were not part of this decision (see "Open items").
3. **The constructed-data guard stays in code.** A database rule goes to the backlog: a note in register entry `constructed_test_runs`, and PRD correction 16.


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

The counts are regression tests now (`tests/test_reference_sets.py`). The coefficients, uncertainties and p-values become tests with the statistics module in step 7, which must reproduce them independently. **Approved by the owner on 2026-10-06**: CLAUDE.md and register entry `reference_numbers` state them.

## Assumptions register

96 entries: 93 in force, 2 open, 1 direction approved (after the owner's decisions of 2026-10-06). Every entry decided in step 6 is by the owner on 2026-10-05, not reviewed by an expert.

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

## Tests (816, all passing; 173 new; tests changed listed below)

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
| `tests/test_adapter_tamu.py`, `tests/test_assumptions.py` | +1, +2 | The decision citations quote the register; the step 6 decisions' wording; the approved reference numbers with the earlier values in their history (2026-10-06). |

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
816 passed in 179.58s    (after the owner's decisions of 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
816 passed in 182.96s
```

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

## Open items

1. **Owner:**
   - the open decisions `below_minimum_display` (before step 7) and `curator_tabular_sources` (before step 8);
   - the answer file's rows 15–16 `explanation` cells still say "The reference plan sets no test-type rule, so both enter"; correcting them was not part of the 2026-10-06 decision.
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
